"""Explicit source lifecycle; all responses here are independently synthetic."""
import asyncio
import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import ssl
import subprocess
import threading
from http.server import ThreadingHTTPServer
from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi import HTTPException
import httpx
import pytest

import analysis_cumulative_service as service
import analysis_model_source as model_sources
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_observed_roles import material
from test_analysis_model_quoted_parent_units import call
from test_analysis_saved_period import with_answer


def synthetic_response(prepared):
    fields = json.loads(prepared.messages()[1]['content'])['fields']
    packet = dict(fields=[dict(field=f['field'], units=[dict(quote=text,
        node_kind='ROLE' if 'の役割は' in text or '担当' in text else 'ACTION_OR_NONACTION',
        parent_quote=None, scope_role=None, qualifiers=[])
        for text in f['text'].rstrip('。').split('。')]) for f in fields])
    return call(prepared, packet).response


def run(awaitable):
    return asyncio.run(awaitable)


def provider_environment():
    return dict(COCOLON_ANALYSIS_MODEL_SOURCE='self_hosted.v1',
        COCOLON_ANALYSIS_MODEL_ENDPOINT='https://synthetic-analysis.invalid/v1/chat/completions',
        COCOLON_ANALYSIS_MODEL='synthetic-analysis-4b',
        COCOLON_ANALYSIS_MODEL_API_KEY='synthetic-analysis-private-key')


def provider_packet(raw, **changes):
    packet = dict(model='synthetic-analysis-4b', choices=[dict(finish_reason='stop',
        message=dict(role='assistant', content=raw))])
    packet.update(changes)
    return packet


def measured_batch_budget(prepared, *, tokens_per_record=250):
    """Deterministic unit-test counter plus the real existing JSON encoding."""
    messages = prepared.messages()
    records = json.loads(messages[1]['content'])['records']
    payload = dict(model='synthetic-analysis-4b', messages=messages, temperature=0,
        max_tokens=2048, stream=False, chat_template_kwargs={'enable_thinking': False})
    body = httpx.Request('POST', 'https://synthetic-analysis.invalid/v1/chat/completions',
        json=payload).content
    return service.AnalysisModelInputBudget(3000 + len(records)*tokens_per_record, len(body))


@pytest.mark.parametrize('profile', ['selected_material.v4', 'selected_material.v7'])
def test_offline_batch_plan_keeps_every_201_record_and_original_source_binding(profile):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import _model_fields_source
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import freeze_analysis_sources
    snap = source_snapshot(201)
    original = copy.deepcopy(snap)
    with patch.object(service, '_rpc', AsyncMock(side_effect=AssertionError('planner RPC'))):
        plan = service.prepare_cumulative_model_batches(OWNER, snap,
            prompt_version=profile, measure_budget=measured_batch_budget)
        service._rpc.assert_not_awaited()
    parent_frozen, parent_fields = _model_fields_source(plan.parent.request, allow_supplements=True)
    expected_refs = tuple(m.saved_record_ref for m in parent_frozen.members)
    assert len(plan.batches) > 1
    assert tuple(ref for group in plan.record_refs for ref in group) == expected_refs
    assert len(expected_refs) == len(set(expected_refs)) == 201
    assert snap == original
    parent_sources = {s.envelope.envelope_id:s for s in parent_frozen.sources}
    source_refs, field_refs = [], []
    for batch, budget, refs in zip(plan.batches, plan.budgets, plan.record_refs):
        assert batch.response is None and batch.source_guard == plan.parent.source_guard
        assert batch.prompt_version == profile
        assert batch.request.request_id == plan.parent.request.request_id
        assert batch.request.authenticated_owner_scope == OWNER
        assert batch.request.period_start == plan.parent.request.period_start
        assert batch.request.period_end == plan.parent.request.period_end
        assert tuple(m.saved_record_ref for m in batch.request.members) == refs
        assert budget.prompt_tokens + plan.reserved_new_tokens <= plan.context_tokens == 8192
        assert budget.request_body_bytes <= plan.max_request_bytes == 65536
        frozen, fields = _model_fields_source(batch.request, allow_supplements=True)
        assert frozen == freeze_analysis_sources(batch.request)
        assert all(parent_sources[s.envelope.envelope_id] == s for s in frozen.sources)
        source_refs.extend(s.envelope.envelope_id for s in frozen.sources)
        field_refs.extend(f['field_ref'] for f in fields)
        parent_by_field = {f['field_ref']:f for f in parent_fields}
        assert all(parent_by_field[f['field_ref']] == f for f in fields)
    assert source_refs == [s.envelope.envelope_id for s in parent_frozen.sources]
    assert field_refs == [f['field_ref'] for f in parent_fields]


@pytest.mark.parametrize('profile', ['selected_material.v4', 'selected_material.v7'])
def test_offline_batch_plan_returns_exact_parent_if_unsplit_and_does_not_change_legacy_bytes(profile):
    snap = source_snapshot(2)
    before = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=profile)
    messages = before.messages()
    plan = service.prepare_cumulative_model_batches(OWNER, snap,
        prompt_version=profile, measure_budget=measured_batch_budget)
    assert plan.batches == (plan.parent,) and plan.batches[0] is plan.parent
    assert plan.parent == before and plan.parent.messages() == messages
    assert service.prepare_cumulative_category_units(OWNER, snap, prompt_version=profile) == before


def test_offline_batch_plan_never_splits_original_fields_or_three_qualified_answers(monkeypatch):
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSupplement, commitment
    snap = source_snapshot(2)
    snap['members'][0]['original']['memo_action'] = '僕は費用を記録した。'
    parent_request = service._cumulative_model_request(OWNER, snap)
    first = parent_request.members[0]
    # The saved-source owner has its own round/answer tests. Here the planner
    # receives its already qualified immutable member with the maximum answers.
    texts = ('僕は資料を見た。', '僕は費用を記録した。', '僕は日程を決めなかった。')
    answers = tuple(AnalysisSupplement(str(UUID(int=700+i)), OWNER, first.saved_record_ref,
        first.saved_record_version, text, commitment(text)) for i,text in enumerate(texts))
    request = replace(parent_request, members=(replace(first, supplements=answers), parent_request.members[1]))
    monkeypatch.setattr(service, '_cumulative_model_request', lambda *_:request)
    plan = service.prepare_cumulative_model_batches(OWNER, snap,
        measure_budget=lambda p:measured_batch_budget(p, tokens_per_record=2000))
    assert len(plan.batches) == 2
    assert plan.batches[0].request.members == request.members[:1]
    assert plan.batches[0].request.members[0].supplements == answers
    body = json.loads(plan.batches[0].messages()[1]['content'])
    assert len(body['records']) == 1 and len(body['fields']) == 5
    assert [f['text'] for f in body['fields']] == [first_value for first_value in (
        json.loads(first.original_json)['memo'], '僕は費用を記録した。', *texts)]
    assert [f['source_role'] for f in body['fields']] == ['ORIGINAL_INPUT']*2 + ['SUPPLEMENTAL_ANSWER']*3
    assert [f['supplement'] for f in body['fields'][2:]] == [1,2,3]


def test_offline_batch_plan_preserves_unicode_categories_emotions_and_as_of():
    snap = source_snapshot(3)
    snap['members'][1]['original'].update(memo='僕は本を見た。🧭 café\u0301 雨のち晴れ。',
        memo_action='僕は費用を記録しなかった。', category=['生活', '家'],
        emotion_details=[dict(type='平穏', strength='medium')])
    parent = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v7')
    plan = service.prepare_cumulative_model_batches(OWNER, snap, prompt_version='selected_material.v7',
        measure_budget=lambda p:measured_batch_budget(p, tokens_per_record=2000))
    assert len(plan.batches) == 3
    full = json.loads(parent.messages()[1]['content'])
    for index, (batch, original_record) in enumerate(zip(plan.batches, parent.request.members)):
        assert batch.request.members == (original_record,)
        user = json.loads(batch.messages()[1]['content'])
        assert user['analysis_as_of'] == full['analysis_as_of']
        original = json.loads(original_record.original_json)
        assert [f['text'] for f in user['fields']] == [original[k] for k in ('memo','memo_action') if original[k]]
        assert user['records'][0]['selected_emotions'] == original['emotions']
        assert user['records'][0]['emotion_details'] == original['emotion_details']
        assert user['records'][0]['selected_categories'] == full['records'][index]['selected_categories']
        assert set(user['records'][0]['selected_categories']) == set(original['category'])
    before = plan.parent.messages()
    snap['members'][1]['original']['memo'] = 'changed after CPU preparation'
    assert plan.parent.messages() == before


def test_offline_batch_plan_enforces_body_budget_even_with_small_token_measurement():
    snap = source_snapshot(3)
    single = service.prepare_cumulative_category_units(OWNER, source_snapshot(1), prompt_version='selected_material.v4')
    body_limit = measured_batch_budget(single).request_body_bytes
    plan = service.prepare_cumulative_model_batches(OWNER, snap,
        measure_budget=lambda p:replace(measured_batch_budget(p), prompt_tokens=1),
        max_request_bytes=body_limit)
    assert len(plan.batches) == 3 and all(b.request_body_bytes <= body_limit for b in plan.budgets)


@pytest.mark.parametrize('budget', [service.AnalysisModelInputBudget(6144,65536),
    service.AnalysisModelInputBudget(6145,65536), service.AnalysisModelInputBudget(6144,65537)])
def test_offline_batch_plan_respects_exact_context_and_body_boundaries(budget):
    kwargs = dict(measure_budget=lambda _:budget)
    if budget.prompt_tokens == 6144 and budget.request_body_bytes == 65536:
        assert len(service.prepare_cumulative_model_batches(OWNER, source_snapshot(1), **kwargs).batches) == 1
    else:
        with pytest.raises(ValueError, match='analysis_model_batch_record_budget_exceeded'):
            service.prepare_cumulative_model_batches(OWNER, source_snapshot(1), **kwargs)


def test_offline_batch_plan_oversized_later_record_never_returns_a_partial_plan():
    snap = source_snapshot(4)
    last_id = snap['members'][-1]['original']['id']
    measured = []
    def budget(prepared):
        refs = tuple(m.saved_record_ref for m in prepared.request.members)
        measured.append(refs)
        return service.AnalysisModelInputBudget(7000 if last_id in refs else 3000+2000*len(refs), 1000)
    original = copy.deepcopy(snap)
    with pytest.raises(ValueError, match='analysis_model_batch_record_budget_exceeded'):
        service.prepare_cumulative_model_batches(OWNER, snap, measure_budget=budget)
    assert (last_id,) in measured and snap == original


def test_offline_batch_plan_keeps_leading_middle_and_trailing_fieldless_records():
    snap = source_snapshot(5)
    for index in (0,2,4):
        snap['members'][index]['original'].update(memo='', memo_action='')
    plan = service.prepare_cumulative_model_batches(OWNER, snap,
        measure_budget=lambda p:measured_batch_budget(p, tokens_per_record=1000))
    assert [len(batch.request.members) for batch in plan.batches] == [2,3]
    expected = tuple(raw['original']['id'] for raw in snap['members'])
    assert tuple(ref for group in plan.record_refs for ref in group) == expected
    for batch in plan.batches:
        user = json.loads(batch.messages()[1]['content'])
        assert user['fields'] and len(user['records']) == len(batch.request.members)


def test_offline_batch_plan_uses_existing_canonical_record_order_without_changing_originals():
    snap = source_snapshot(4)
    snap['members'].reverse()
    original = copy.deepcopy(snap)
    plan = service.prepare_cumulative_model_batches(OWNER, snap,
        measure_budget=lambda p:measured_batch_budget(p, tokens_per_record=2000))
    expected = tuple(sorted((raw['original']['id'] for raw in snap['members'])))
    assert tuple(ref for group in plan.record_refs for ref in group) == expected
    assert snap == original


def test_offline_batch_fieldless_group_failure_does_not_claim_single_record_is_oversized():
    snap = source_snapshot(3)
    snap['members'][0]['original']['memo'] = ''
    with pytest.raises(ValueError, match='analysis_model_batch_group_budget_exceeded'):
        service.prepare_cumulative_model_batches(OWNER, snap,
            measure_budget=lambda p:measured_batch_budget(p, tokens_per_record=2000))


@pytest.mark.parametrize('scope', ['empty', 'all_fieldless', 'safety', 'foreign_answer', 'implicit_answer'])
def test_offline_batch_planner_checks_whole_source_before_any_budget_callback(scope):
    snap = source_snapshot(0 if scope == 'empty' else 2)
    if scope == 'all_fieldless':
        for member in snap['members']: member['original']['memo'] = ''
    if scope == 'safety': snap['members'][-1]['original']['memo'] = '死にたい。'
    if scope in {'foreign_answer', 'implicit_answer'}:
        # with_answer freezes a canonical Emlis parent; the plain cumulative
        # fixture deliberately has no strength-bearing emotion_details.
        snap['members'][-1]['original']['emotion_details'] = [dict(type='平穏', strength='medium')]
        snap['members'][-1] = with_answer(snap['members'][-1], '費用を記録した。' if scope=='implicit_answer' else '僕は費用を記録した。')
        if scope == 'foreign_answer': snap['members'][-1]['thread']['user_id'] = str(UUID(int=2))
    measured = []
    with pytest.raises(ValueError):
        service.prepare_cumulative_model_batches(OWNER, snap,
            measure_budget=lambda p:measured.append(p))
    assert measured == []


def test_offline_batch_planner_does_not_partition_away_a_foreign_member(monkeypatch):
    snap = source_snapshot(2)
    request = service._cumulative_model_request(OWNER, snap)
    foreign = replace(request.members[-1], owner_scope=str(UUID(int=2)))
    monkeypatch.setattr(service, '_cumulative_model_request',
        lambda *_:replace(request, members=(*request.members[:-1], foreign)))
    measured = []
    with pytest.raises(ValueError, match='analysis_owner_mismatch'):
        service.prepare_cumulative_model_batches(OWNER, snap, measure_budget=lambda p:measured.append(p))
    assert measured == []


def test_offline_batch_planner_accepts_conservative_limits_without_relaxing_provider_limits():
    plan = service.prepare_cumulative_model_batches(OWNER, source_snapshot(7),
        measure_budget=measured_batch_budget, context_tokens=7000,
        reserved_new_tokens=3000, max_request_bytes=50000)
    assert len(plan.batches) > 1
    assert all(b.prompt_tokens+3000 <= 7000 and b.request_body_bytes <= 50000 for b in plan.budgets)
    assert sum(map(len, plan.record_refs)) == 7


@pytest.mark.parametrize('bad', [True,False,0,-1,1.5,float('nan'),float('inf'),None,'100'])
@pytest.mark.parametrize('field', ['prompt_tokens','request_body_bytes'])
def test_offline_batch_planner_rejects_invalid_or_inexact_measurements(bad, field):
    values = dict(prompt_tokens=1, request_body_bytes=1)
    values[field] = bad
    with pytest.raises(ValueError, match='analysis_model_batch_budget_invalid'):
        service.prepare_cumulative_model_batches(OWNER, source_snapshot(1),
            measure_budget=lambda _:service.AnalysisModelInputBudget(**values))


@pytest.mark.parametrize('kwargs', [dict(context_tokens=True),dict(context_tokens=8193),dict(context_tokens=2048),
    dict(context_tokens=float('nan')),dict(reserved_new_tokens=True),dict(reserved_new_tokens=2047),
    dict(reserved_new_tokens=8192),dict(max_request_bytes=True),dict(max_request_bytes=65537),
    dict(max_request_bytes=0),dict(max_request_bytes=1.5)])
def test_offline_batch_planner_cannot_relax_existing_provider_budgets(kwargs):
    with pytest.raises(ValueError, match='analysis_model_batch_budget_invalid'):
        service.prepare_cumulative_model_batches(OWNER, source_snapshot(1),
            measure_budget=measured_batch_budget, **kwargs)


@pytest.mark.parametrize('callback', [None, lambda _:None, lambda _:{'prompt_tokens':1,'request_body_bytes':1}, AsyncMock()])
def test_offline_batch_planner_requires_an_explicit_synchronous_typed_counter(callback):
    with pytest.raises(ValueError, match='analysis_model_batch_budget_invalid'):
        service.prepare_cumulative_model_batches(OWNER, source_snapshot(1), measure_budget=callback)


def mock_provider(monkeypatch, handler):
    real_client = httpx.AsyncClient
    monkeypatch.setattr(model_sources.httpx, 'AsyncClient',
        lambda **kwargs: real_client(**{**kwargs, 'transport': httpx.MockTransport(handler)}))


def select_provider(monkeypatch):
    for name, value in provider_environment().items():
        monkeypatch.setenv(name, value)


@pytest.mark.parametrize('profile', ['selected_material.v4', 'selected_material.v7'])
def test_self_hosted_analysis_sends_exact_existing_material_and_retains_raw(profile):
    prepared = service.prepare_cumulative_category_units(OWNER, material('pair'), prompt_version=profile)
    raw = ' \n' + synthetic_response(prepared).raw + '\n '
    calls = []
    def handler(request):
        calls.append(request)
        assert request.headers['authorization'] == 'Bearer synthetic-analysis-private-key'
        assert json.loads(request.content) == dict(model='synthetic-analysis-4b', messages=prepared.messages(),
            temperature=0, max_tokens=2048, stream=False, chat_template_kwargs={'enable_thinking': False})
        return httpx.Response(200, json=provider_packet(raw))
    source = model_sources.SelfHostedAnalysisModelSource(
        endpoint=provider_environment()['COCOLON_ANALYSIS_MODEL_ENDPOINT'],
        model='synthetic-analysis-4b', api_key='synthetic-analysis-private-key', transport=httpx.MockTransport(handler), prompt_version=profile)
    response = run(source(prepared))
    assert len(calls) == 1 and response == replace(synthetic_response(prepared),
        raw=raw, raw_sha256=__import__('hashlib').sha256(raw.encode()).hexdigest())


@pytest.mark.parametrize('profile', ['selected_material.v4', 'selected_material.v7'])
def test_real_loopback_https_keeps_certificate_verification_and_exact_model_packet(tmp_path, profile):
    import importlib.util
    path = Path(__file__).parents[1] / 'tools/serve_emlis_natural_reply.py'
    spec = importlib.util.spec_from_file_location('analysis_https_probe', path)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    cert, key = tmp_path/'localhost.pem', tmp_path/'localhost.key'
    subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-sha256', '-days', '1', '-nodes',
        '-keyout', str(key), '-out', str(cert), '-subj', '/CN=localhost',
        '-addext', 'subjectAltName=DNS:localhost,IP:127.0.0.1'],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
    key.chmod(0o600)
    prepared = service.prepare_cumulative_category_units(OWNER, material('pair'), prompt_version=profile)
    raw = synthetic_response(prepared).raw
    calls = []
    def generate(messages, deadline):
        assert messages == prepared.messages()
        calls.append(messages)
        return raw, 'stop'
    import time
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='synthetic-private-key', model_name='synthetic-analysis-4b',
        deadline=time.monotonic()+20, max_requests=1))
    server_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server_context.load_cert_chain(cert, key)
    server.socket = server_context.wrap_socket(server.socket, server_side=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    endpoint = f'https://localhost:{server.server_port}/v1/chat/completions'
    try:
        untrusted = model_sources.SelfHostedAnalysisModelSource(endpoint=endpoint,
            model='synthetic-analysis-4b', api_key='synthetic-private-key', prompt_version=profile)
        with pytest.raises(RuntimeError, match='analysis_model_source_unavailable'):
            run(untrusted(prepared))
        assert calls == []
        async def trusted_call():
            context = ssl.create_default_context(cafile=str(cert))
            assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname
            source = model_sources.SelfHostedAnalysisModelSource(endpoint=endpoint,
                model='synthetic-analysis-4b', api_key='synthetic-private-key',
                transport=httpx.AsyncHTTPTransport(verify=context), prompt_version=profile)
            return await source(prepared)
        assert run(trusted_call()) == synthetic_response(prepared)
        assert len(calls) == 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


@pytest.mark.parametrize('defect', ['redirect', 'unauthorized', 'busy', 'unavailable', 'model', 'choices',
    'finish', 'role', 'tool', 'function', 'reasoning', 'content', 'json', 'oversize', 'timeout', 'connection'])
def test_provider_contract_failure_never_retries_redirects_or_exposes_body(defect):
    prepared = service.prepare_cumulative_category_units(OWNER, material('pair'), prompt_version='selected_material.v4')
    calls = []
    def handler(request):
        calls.append(request)
        if defect == 'timeout': raise httpx.ReadTimeout('private provider address')
        if defect == 'connection': raise httpx.ConnectError('private provider address')
        packet = provider_packet(synthetic_response(prepared).raw)
        if defect in {'redirect', 'unauthorized', 'busy', 'unavailable'}:
            return httpx.Response({'redirect':302,'unauthorized':401,'busy':429,'unavailable':503}[defect],
                content=b'private provider failure', headers={'Location':'https://other.invalid/'})
        if defect == 'model': packet['model'] = 'unselected-model'
        if defect == 'choices': packet['choices'] *= 2
        if defect == 'finish': packet['choices'][0]['finish_reason'] = 'length'
        if defect == 'role': packet['choices'][0]['message']['role'] = 'user'
        if defect == 'tool': packet['choices'][0]['message']['tool_calls'] = [{'private':'tool'}]
        if defect == 'function': packet['choices'][0]['message']['function_call'] = {'private':'tool'}
        if defect == 'reasoning': packet['choices'][0]['message']['reasoning_content'] = 'private reasoning'
        if defect == 'content': packet['choices'][0]['message']['content'] = None
        if defect == 'json': return httpx.Response(200, content=b'private malformed JSON')
        if defect == 'oversize': return httpx.Response(200, content=b'x' * (model_sources.MAX_RESPONSE_BYTES+1))
        return httpx.Response(200, json=packet)
    source = model_sources.SelfHostedAnalysisModelSource(endpoint=provider_environment()['COCOLON_ANALYSIS_MODEL_ENDPOINT'],
        model='synthetic-analysis-4b', api_key='synthetic-analysis-private-key', transport=httpx.MockTransport(handler))
    with pytest.raises(TimeoutError if defect == 'timeout' else RuntimeError) as error:
        run(source(prepared))
    assert str(error.value) == ('analysis_model_source_timeout' if defect == 'timeout' else 'analysis_model_source_unavailable')
    assert len(calls) == 1


@pytest.mark.parametrize('endpoint', ['http://synthetic.invalid/v1/chat/completions',
    'https://user:password@synthetic.invalid/v1/chat/completions',
    'https://synthetic.invalid/v1/chat/completions?key=private',
    'https://synthetic.invalid/v1/chat/completions#private', 'https://synthetic.invalid/other', None])
def test_analysis_provider_configuration_rejects_insecure_or_credential_urls(endpoint):
    with pytest.raises(ValueError, match='analysis_model_configuration_invalid'):
        model_sources.SelfHostedAnalysisModelSource(endpoint=endpoint, model='selected-4b', api_key='private-key')


@pytest.mark.parametrize('profile', ['selected_material.v6', 'selected_material.v8', '', None, 7])
def test_explicit_transport_rejects_undeclared_prompt_profiles(profile):
    with pytest.raises(ValueError, match='analysis_model_configuration_invalid'):
        model_sources.SelfHostedAnalysisModelSource(
            endpoint=provider_environment()['COCOLON_ANALYSIS_MODEL_ENDPOINT'],
            model='synthetic-analysis-4b', api_key='synthetic-key', prompt_version=profile)


@pytest.mark.parametrize('profile,other', [
    ('selected_material.v4', 'selected_material.v7'),
    ('selected_material.v7', 'selected_material.v4'),
])
def test_explicit_transport_rejects_mismatched_preparation_before_http(profile, other):
    prepared = service.prepare_cumulative_category_units(OWNER, material('pair'), prompt_version=other)
    def forbidden(_):
        raise AssertionError('mismatched prompt reached HTTP')
    source = model_sources.SelfHostedAnalysisModelSource(
        endpoint=provider_environment()['COCOLON_ANALYSIS_MODEL_ENDPOINT'],
        model='synthetic-analysis-4b', api_key='synthetic-key',
        transport=httpx.MockTransport(forbidden), prompt_version=profile)
    with pytest.raises(ValueError, match='analysis_quoted_parent_units_binding_invalid'):
        run(source(prepared))


def test_callback_attributes_cannot_select_the_transport_profile():
    callback = AsyncMock()
    callback.prompt_version = 'selected_material.v7'
    assert model_sources.analysis_model_prompt_version(callback) == 'selected_material.v4'
    assert model_sources.analysis_model_prompt_version(lambda _:None) == 'selected_material.v4'
    explicit = model_sources.SelfHostedAnalysisModelSource(
        endpoint=provider_environment()['COCOLON_ANALYSIS_MODEL_ENDPOINT'],
        model='synthetic-analysis-4b', api_key='synthetic-key', prompt_version='selected_material.v7')
    assert model_sources.analysis_model_prompt_version(explicit) == 'selected_material.v7'
    with pytest.raises(AttributeError):
        explicit.prompt_version = 'selected_material.v4'


def test_explicit_v7_transport_uses_normal_ensure_without_replacing_preparation(model_lifecycle, monkeypatch):
    received = []
    prepared = service.prepare_cumulative_category_units(OWNER, model_lifecycle['snapshot'],
        prompt_version='selected_material.v7')
    raw = ' \n' + synthetic_response(prepared).raw + '\n '
    def handler(request):
        received.append(json.loads(request.content))
        assert received[-1]['messages'] == prepared.messages()
        return httpx.Response(200, json=provider_packet(raw))
    source = model_sources.SelfHostedAnalysisModelSource(
        endpoint=provider_environment()['COCOLON_ANALYSIS_MODEL_ENDPOINT'],
        model='synthetic-analysis-4b', api_key='synthetic-key',
        transport=httpx.MockTransport(handler), prompt_version='selected_material.v7')
    original = service.prepare_cumulative_category_units
    versions = []
    def observe(owner, snapshot, *, prompt_version='selected_categories.v1'):
        versions.append(prompt_version)
        return original(owner, snapshot, prompt_version=prompt_version)
    monkeypatch.setattr(service, 'prepare_cumulative_category_units', observe)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['refreshed'] and len(received) == len(model_lifecycle['commits']) == 1
    assert versions and set(versions) == {'selected_material.v7'}
    # This isolated fixture has no SQL capture step; supply its already saved
    # monthly reference. The actual capture lifecycle has separate SQL coverage.
    from datetime import datetime, timezone, timedelta
    month = datetime.now(timezone(timedelta(hours=9))).date().replace(day=1).isoformat()
    model_lifecycle['row'].update(snapshot_month=month, captured_at=model_lifecycle['snapshot']['now'])
    with patch.object(model_sources, 'analysis_model_prompt_version', side_effect=AssertionError('saved profile lookup')), \
         patch.object(service, 'prepare_cumulative_category_units', side_effect=AssertionError('saved preparation')), \
         patch.object(model_sources.SelfHostedAnalysisModelSource, '__call__', side_effect=AssertionError('saved HTTP')):
        current = run(service.ensure_map(OWNER, model_source=source))
        monthly = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=source))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=source))
    for saved in (current, monthly, readonly):
        assert saved['report_id'] == first['report_id'] and saved['meta'] == first['meta']
        assert saved['content_text'] == first['content_text'] and not saved['refreshed']


@pytest.mark.parametrize('selector', ['', 'off'])
def test_factory_off_never_reuses_emlis_provider(monkeypatch, selector):
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_SOURCE', selector)
    monkeypatch.setenv('EMLIS_NATURAL_REPLY_ENDPOINT', 'https://emlis.invalid/v1/chat/completions')
    monkeypatch.setenv('EMLIS_NATURAL_REPLY_API_KEY', 'private-emlis-key')
    assert model_sources.application_analysis_model_source() is None


def test_implicit_application_updates_share_factory_identity_and_keep_saved_reads(model_lifecycle, monkeypatch):
    select_provider(monkeypatch)
    received = []
    async def handler(request):
        received.append(json.loads(request.content))
        await asyncio.sleep(0)
        prepared = service.prepare_cumulative_category_units(OWNER, model_lifecycle['snapshot'], prompt_version='selected_material.v4')
        return httpx.Response(200, json=provider_packet(synthetic_response(prepared).raw))
    mock_provider(monkeypatch, handler)
    source = model_sources.application_analysis_model_source()
    assert source is model_sources.application_analysis_model_source()
    async def scenario():
        results = await asyncio.gather(*(service.ensure_map(OWNER, force=True) for _ in range(3)))
        assert results[0] == results[1] == results[2]
        assert len(received) == len(model_lifecycle['commits']) == 1
        monkeypatch.delenv('COCOLON_ANALYSIS_MODEL_API_KEY')
        assert source is not model_sources.application_analysis_model_source()
        saved = await service.ensure_map(OWNER)
        assert saved['meta'] == results[0]['meta'] and saved['content_text'] == results[0]['content_text']
        with pytest.raises(HTTPException) as error:
            await service.ensure_map(OWNER, force=True)
        assert error.value.status_code == 503 and len(received) == 1 and len(model_lifecycle['commits']) == 1
    run(scenario())


@pytest.mark.parametrize('change', ['selector', 'key', 'model', 'after_build'])
def test_changed_application_configuration_rejects_pending_model_save(model_lifecycle, monkeypatch, change):
    select_provider(monkeypatch)
    def alter():
        monkeypatch.setenv({'selector':'COCOLON_ANALYSIS_MODEL_SOURCE','key':'COCOLON_ANALYSIS_MODEL_API_KEY',
            'model':'COCOLON_ANALYSIS_MODEL','after_build':'COCOLON_ANALYSIS_MODEL_SOURCE'}[change],
            'off' if change in {'selector','after_build'} else 'changed-private-value')
    def handler(request):
        prepared = service.prepare_cumulative_category_units(OWNER, model_lifecycle['snapshot'], prompt_version='selected_material.v4')
        if change != 'after_build': alter()
        return httpx.Response(200, json=provider_packet(synthetic_response(prepared).raw))
    mock_provider(monkeypatch, handler)
    if change == 'after_build':
        original_build = service.build_cumulative_map
        def build(*args, **kwargs):
            result = original_build(*args, **kwargs)
            alter()
            return result
        monkeypatch.setattr(service, 'build_cumulative_map', build)
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER))
    assert error.value.status_code == 503 and not model_lifecycle['commits']


@pytest.mark.parametrize('selector', ['unsupported.v1', 'self_hosted.v1'])
def test_bad_enabled_configuration_cannot_fall_back_to_finite_map(model_lifecycle, monkeypatch, selector):
    select_provider(monkeypatch)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_SOURCE', selector)
    if selector == 'self_hosted.v1':
        monkeypatch.delenv('COCOLON_ANALYSIS_MODEL_API_KEY')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER))
    assert error.value.status_code == 503 and not model_lifecycle['commits']
    # Explicit callback remains independent from the configured application source.
    source = AsyncMock(side_effect=lambda prepared: synthetic_response(prepared))
    assert run(service.ensure_map(OWNER, model_source=source))['refreshed']
    source.assert_awaited_once()


@pytest.mark.parametrize('defect', ['request', 'messages', 'raw', 'hash', 'finish',
    'missing', 'wrong_type', 'invalid_json', 'source_failure', 'stale_clock', 'foreign_owner'])
def test_bad_response_is_not_saved_or_replaced_with_finite_output(monkeypatch, defect):
    snap = material('pair')
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    response = synthetic_response(prepared)
    if defect == 'request': response = replace(response, request_ref='foreign')
    if defect == 'messages': response = replace(response, messages_sha256='0'*64)
    if defect == 'raw': response = replace(response, raw=response.raw+' ')
    if defect == 'hash': response = replace(response, raw_sha256='0'*64)
    if defect == 'finish': response = replace(response, finish_reason='length')
    if defect == 'missing': response = None
    if defect == 'wrong_type': response = prepared
    if defect == 'invalid_json': response = call(prepared, raw='{"fields":NaN}').response
    if defect == 'stale_clock': snap = dict(snap, now='2026-11-01T08:00:01+00:00', period_end='2026-11-01T08:00:01+00:00')
    if defect == 'foreign_owner':
        other = service.prepare_cumulative_category_units(str(UUID(int=2)), snap, prompt_version='selected_material.v4')
        response = synthetic_response(other)
    source = AsyncMock(side_effect=ValueError('unavailable')) if defect == 'source_failure' else AsyncMock(return_value=response)
    async def rpc(name, payload):
        if name == 'analysis_cumulative_read':
            return dict(items=[], subscription_tier='free', matched=True, history_limit=2)
        assert name == 'analysis_cumulative_source_snapshot', 'invalid response reached commit'
        return snap
    monkeypatch.setattr(service, '_rpc', rpc)
    monkeypatch.setattr(service, 'observed_mode', lambda:'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_awaited_once()


@pytest.mark.parametrize('scope', ['empty', 'safety'])
def test_unqualified_source_does_not_acquire_a_response(monkeypatch, scope):
    snap = source_snapshot(0 if scope == 'empty' else 1)
    if scope == 'safety': snap['members'][0]['original']['memo'] = '死にたい。'
    source = AsyncMock(side_effect=AssertionError('unqualified source acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items':[]}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda:'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def multi_material():
    snap = source_snapshot(7)
    bodies = [
        ('僕の役割は受付係だった。', ''),
        ('僕の役割は受付係だった。', '僕は費用を記録した。'),
        ('僕の役割は案内係だった。費用を記録した。', ''),
        ('僕の役割は案内係だった。僕は資料を調べた。', ''),
        ('私は会合の進行を担当した。その後、私は分担を決めた。', ''),
        ('僕は費用を記録しなかった。', ''),
        ('まだ言葉にはできません。', ''),
    ]
    for i, (member, (memo, action)) in enumerate(zip(snap['members'], bodies)):
        member['original'].update(memo=memo, memo_action=action,
            category=['仕事'] if i % 2 == 0 else ['生活'])
    return snap


def multi_proposal(snap):
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    return replace(prepared, response=synthetic_response(prepared))


def answer_material(original='私は資料を見た。', answer='私は費用を記録した。'):
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=original, memo_action='',
        emotion_details=[dict(type='平穏', strength='medium')])
    snap['members'][0] = with_answer(snap['members'][0], answer)
    return snap


@pytest.mark.parametrize('prompt', ['selected_material.v3', 'selected_material.v4'])
@pytest.mark.parametrize('original,answer,role,duplicate', [
    ('僕の役割は受付係だった。', '僕は費用を記録した。', True, False),
    ('私は資料を見た。', '私は費用を記録しなかった。', False, False),
    ('私は資料を見た。', '私は資料を見ました。', False, True),
])
def test_ordinary_answer_keeps_own_witness_and_one_record_occasion(prompt, original, answer, role, duplicate):
    snap = answer_material(original, answer)
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=prompt)
    artifact, counts = service.build_cumulative_map(OWNER, snap,
        model_input=replace(prepared, response=synthetic_response(prepared)))
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 1
    assert counts['unparsed_count'] == 0 and len(artifact.source_members) == 1
    assert len(artifact.graph.nodes) == (1 if duplicate else 2) and not artifact.graph.edges
    fields = json.loads(prepared.messages()[1]['content'])['fields']
    assert [f['source_role'] for f in fields] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
    assert fields[0]['record'] == fields[1]['record'] == 1
    envelopes = {e.source_envelope_id for n in artifact.graph.nodes for e in n.evidence_refs}
    assert len(envelopes) == 2 and envelopes == set(artifact.source_members[0].child_source_envelope_refs)
    assert all(n.record_refs == (snap['members'][0]['original']['id'],)
        and n.selected_categories == ('仕事',) for n in artifact.graph.nodes)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert all(n['evidence_badge_count'] == 1 for n in projection['nodes'])
    if role:
        assert artifact.graph.nodes[0].proposition.role_state == 'WRITTEN_PAST_ROLE'
        assert '受付係' in artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    else:
        finite, finite_counts = service.build_cumulative_map(OWNER, snap)
        assert artifact.graph == finite.graph and counts == finite_counts


def test_answer_and_independent_record_keep_categories_without_new_order_or_repetition():
    snap = answer_material(answer='私は資料を調べた。')
    other = source_snapshot(2)['members'][1]
    other['original'].update(memo='私は費用を記録した。', memo_action='', category=['生活'])
    snap['members'].append(other)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    assert counts['source_count'] == counts['mapped_count'] == 2 and counts['unparsed_count'] == 0
    assert len(artifact.graph.nodes) == 3 and not artifact.graph.edges
    assert [n.selected_categories for n in artifact.graph.nodes] == [('仕事',), ('仕事',), ('生活',)]


@pytest.mark.parametrize('defect', ['missing', 'kind', 'sibling_quote'])
def test_answer_requires_its_own_complete_model_proposal_without_finite_rescue(defect):
    snap = answer_material()
    value = multi_proposal(snap)
    packet = json.loads(value.response.raw)
    if defect == 'missing': packet['fields'].pop()
    if defect == 'kind': packet['fields'][1]['units'][0]['node_kind'] = 'ROLE'
    if defect == 'sibling_quote': packet['fields'][1]['units'][0]['quote'] = '私は資料を見た。'
    value = call(replace(value, response=None), packet)
    if defect == 'kind':
        artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
        assert artifact is None and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1
    else:
        with pytest.raises(ValueError):
            service.build_cumulative_map(OWNER, snap, model_input=value)


@pytest.mark.parametrize('defect', ['owner', 'parent', 'round', 'version', 'answer', 'guard'])
def test_answer_or_parent_binding_change_cannot_reuse_previous_whole_response(defect):
    snap = answer_material()
    value = multi_proposal(snap)
    changed = copy.deepcopy(snap)
    member = changed['members'][0]
    answer = next(e for e in member['events'] if e['kind'] == 'ANSWER')
    if defect == 'owner': member['thread']['user_id'] = str(UUID(int=2))
    if defect == 'parent': answer['payload']['source']['original_source_ref'] = 'foreign'
    if defect == 'round': answer['payload']['source']['round_index'] = 2
    if defect == 'version': member['original']['memo'] = '私は資料を調べた。'
    if defect == 'answer': answer['payload']['source']['answer_text_private'] = '私は資料を調べた。'
    if defect == 'guard': changed['guard'] = 'analysis-db-cumulative-v1:' + 'b' * 64
    with pytest.raises(ValueError):
        service.build_cumulative_map(OWNER, changed, model_input=value)


@pytest.mark.parametrize('answer', ['費用を記録した。', '彼は費用を記録した。',
    '私は資料を見なかった。', '「私は資料を見た」を撤回します。',
    '「私は資料を見た」ではなく「私は資料を調べた」です。',
    '私は費用を記録した。まだ言葉にできません。', '死にたい。'])
def test_ineligible_answer_does_not_acquire_a_response_or_inherit_parent_actor(monkeypatch, answer):
    snap = answer_material(answer=answer)
    source = AsyncMock(side_effect=AssertionError('ineligible answer acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items': []}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def test_original_edit_excludes_old_answer_without_a_second_record_or_old_answer_reuse():
    snap = answer_material()
    snap['members'][0]['original']['memo'] = '私は資料を調べた。'
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    assert counts['source_count'] == counts['mapped_count'] == counts['stale_supplement_count'] == 1
    assert counts['unparsed_count'] == 0 and len(artifact.graph.nodes) == 1
    assert len(artifact.source_members[0].child_source_envelope_refs) == 1
    assert artifact.graph.nodes[0].proposition.predicate_lemma == '調べる'


def test_supplement_parent_version_and_comparison_remain_unsupported():
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import prepare_analysis_model_quoted_parent_units
    prepared = service.prepare_cumulative_category_units(OWNER, answer_material(), prompt_version='selected_material.v4')
    member, = prepared.request.members
    supplement, = member.supplements
    bad_member = replace(member, supplements=(replace(supplement, parent_record_version='foreign'),))
    for request in (replace(prepared.request, members=(bad_member,)),
            replace(prepared.request, comparison_previous_request=prepared.request)):
        with pytest.raises(ValueError):
            prepare_analysis_model_quoted_parent_units(request, source_guard=prepared.source_guard,
                prompt_version='selected_material.v4')


def role_decision_answer(negative_role=False, negative_decision=False, marker='その後、'):
    return ('私は会合の進行を担当' + ('しなかった' if negative_role else 'した') + '。'
        + marker + '私は分担を' + ('決めなかった' if negative_decision else '決めた') + '。')


def role_answer_proposal(snap, *, style=None):
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v6')
    response = synthetic_response(prepared)
    if style is not None:
        from test_analysis_model_role_decision import response_for
        packet = json.loads(response.raw)
        styled = json.loads(response_for(prepared, style=style, qualifiers=True, reorder=True).raw)
        material = json.loads(prepared.messages()[1]['content'])['fields']
        for index, field in enumerate(material):
            if field['source_role'] == 'SUPPLEMENTAL_ANSWER':
                packet['fields'][index] = styled['fields'][index]
        response = call(prepared, packet).response
    return replace(prepared, response=response)


@pytest.mark.parametrize('role_negative', [False, True])
@pytest.mark.parametrize('decision_negative', [False, True])
@pytest.mark.parametrize('marker', ['', 'その後、'])
def test_complete_answer_responsibility_decision_preserves_own_polarity_and_only_own_order(role_negative, decision_negative, marker):
    snap = answer_material(answer=role_decision_answer(role_negative, decision_negative, marker))
    value = role_answer_proposal(snap)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact and len(artifact.graph.nodes) == 3
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 1
    assert counts['unparsed_count'] == 0 and len(artifact.graph.edges) == int(bool(marker))
    parent, role, decision = artifact.graph.nodes
    assert role.proposition.role_state == 'PAST_RESPONSIBILITY'
    assert role.polarity == ('negative' if role_negative else 'positive')
    assert decision.polarity == ('negative' if decision_negative else 'positive')
    assert role.evidence_refs[0].source_envelope_id == decision.evidence_refs[0].source_envelope_id
    assert role.evidence_refs[0].source_envelope_id != parent.evidence_refs[0].source_envelope_id
    assert all(n.record_refs == parent.record_refs and n.selected_categories == ('仕事',)
        and n.proposition.actor == 'SELF' for n in artifact.graph.nodes)
    if marker:
        edge, = artifact.graph.edges
        assert edge.edge_kind == 'OBSERVED_ORDER' and edge.endpoint_refs == (role.node_ref, decision.node_ref)
        assert edge.evidence_refs == role.evidence_refs + decision.evidence_refs
    assert all(n['evidence_badge_count'] == 1 for n in artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'])


@pytest.mark.parametrize('style', ['whole', 'without_marker', 'without_subject', 'predicate'])
def test_answer_uses_the_existing_complete_role_decision_unit_proof(style):
    snap = answer_material(answer=role_decision_answer(True, True))
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=role_answer_proposal(snap, style=style))
    assert artifact and len(artifact.graph.nodes) == 3 and len(artifact.graph.edges) == 1
    assert counts['unparsed_count'] == 0


@pytest.mark.parametrize('parent,expected_nodes,unread', [
    ('まだ言葉にできません。', 2, 1),
    ('僕の役割は受付係だった。', 3, 0),
    ('私は会合の進行を担当した。私は分担を決めた。', 2, 0),
])
def test_answer_graph_keeps_unread_parent_written_role_and_unordered_same_record_restatement(parent, expected_nodes, unread):
    snap = answer_material(parent, role_decision_answer(marker=''))
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=role_answer_proposal(snap))
    assert artifact and len(artifact.graph.nodes) == expected_nodes and not artifact.graph.edges
    assert counts['source_count'] == counts['mapped_count'] == 1 and counts['unparsed_count'] == unread
    assert any(g.missing_scope == 'SOURCE_SCOPE' for g in artifact.graph.unknown_gaps) == bool(unread)
    assert all(n['evidence_badge_count'] == 1 for n in artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'])
    if expected_nodes == 2 and not unread:
        assert all(len(n.evidence_refs) == 2 for n in artifact.graph.nodes)
        assert all(len({e.source_envelope_id for e in n.evidence_refs}) == 2 for n in artifact.graph.nodes)


def test_ordered_answer_occurrences_do_not_merge_with_unordered_parent_or_another_answer():
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSupplement, commitment
    snap = answer_material(role_decision_answer(marker=''), role_decision_answer())
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v6')
    member, = prepared.request.members
    second = AnalysisSupplement('another-owned-answer', OWNER, member.saved_record_ref,
        member.saved_record_version, role_decision_answer(), commitment(role_decision_answer()))
    member = replace(member, supplements=member.supplements + (second,))
    request = replace(prepared.request, members=(member,))
    prepared = admission.prepare_analysis_model_quoted_parent_units(request,
        source_guard=prepared.source_guard, prompt_version='selected_material.v6')
    artifact, mapped, unread = admission.generate_analysis_model_observed_actions(request,
        replace(prepared, response=synthetic_response(prepared)), with_record_counts=True)
    assert artifact and mapped == 1 and unread == 0
    assert len(artifact.graph.nodes) == 6 and len(artifact.graph.edges) == 2
    assert len({n.node_ref for n in artifact.graph.nodes}) == 6
    assert [e.edge_ref for e in artifact.graph.edges] == ['e1', 'e2']
    assert len({e.evidence_refs[0].source_envelope_id for e in artifact.graph.edges}) == 2
    for edge in artifact.graph.edges:
        nodes = [next(n for n in artifact.graph.nodes if n.node_ref == ref) for ref in edge.endpoint_refs]
        assert len({e.source_envelope_id for n in nodes for e in n.evidence_refs}) == 1
        assert edge.evidence_refs == nodes[0].evidence_refs + nodes[1].evidence_refs
    assert all(n['evidence_badge_count'] == 1 for n in artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'])


def test_answer_order_stays_with_its_record_among_other_owned_categories():
    snap = answer_material(answer=role_decision_answer())
    other = source_snapshot(2)['members'][1]
    other['original'].update(memo='僕は費用を記録しなかった。', memo_action='', category=['生活'])
    snap['members'].append(other)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=role_answer_proposal(snap))
    assert artifact and len(artifact.graph.nodes) == 4 and len(artifact.graph.edges) == 1
    assert counts['source_count'] == counts['mapped_count'] == 2 and counts['unparsed_count'] == 0
    assert [n.selected_categories for n in artifact.graph.nodes] == [('仕事',)] * 3 + [('生活',)]
    edge, = artifact.graph.edges
    endpoints = [next(n for n in artifact.graph.nodes if n.node_ref == ref) for ref in edge.endpoint_refs]
    assert all(n.record_refs == (snap['members'][0]['original']['id'],) for n in endpoints)
    assert len({e.source_envelope_id for e in edge.evidence_refs}) == 1


def test_role_clause_parent_with_answer_keeps_its_original_private_proof_boundary():
    snap = answer_material('僕の役割は受付係だった。費用を記録した。', role_decision_answer())
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=role_answer_proposal(snap))
    assert artifact is None and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1


@pytest.mark.parametrize('defect', ['role_kind', 'missing_decision', 'false_negation'])
def test_answer_role_decision_requires_the_actual_model_role_and_complete_units(defect):
    snap = answer_material(answer=role_decision_answer())
    value = role_answer_proposal(snap)
    packet = json.loads(value.response.raw)
    units = packet['fields'][1]['units']
    if defect == 'role_kind': units[0]['node_kind'] = 'ACTION_OR_NONACTION'
    if defect == 'missing_decision': units.pop()
    if defect == 'false_negation': units[1]['qualifiers'] = [dict(kind='NEGATION', quote='決めた')]
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=call(replace(value, response=None), packet))
    assert artifact is None and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1


@pytest.mark.parametrize('defect', ['endpoint', 'edge_evidence', 'proposition', 'literal_hash'])
def test_answer_local_graph_cannot_borrow_cross_source_edges_or_changed_witnesses(defect):
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
    snap = answer_material(answer=role_decision_answer())
    value = role_answer_proposal(snap)
    frozen, fields, _ = admission._admit_quoted_parent_units(value.request, value)
    answer = next(s for s in frozen.sources if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
    graph = compiler.compile_observed_graph(frozen)
    parent, role, decision = graph.nodes
    edge, = graph.edges
    if defect == 'endpoint': graph = replace(graph, edges=(replace(edge, endpoint_refs=(parent.node_ref, decision.node_ref)),))
    if defect == 'edge_evidence': graph = replace(graph, edges=(replace(edge, evidence_refs=(parent.evidence_refs[0], decision.evidence_refs[0])),))
    if defect == 'proposition': graph = replace(graph, nodes=(parent, replace(role, proposition=replace(role.proposition, actor='OTHER')), decision))
    if defect == 'literal_hash': graph = replace(graph, nodes=(parent, replace(role,
        evidence_refs=(replace(role.evidence_refs[0], literal_sha256='0'*64),)), decision))
    with patch.object(compiler, 'compile_observed_graph', return_value=graph):
        assert compiler.compile_model_supplement_role_decision(frozen, fields, answer) is None


@pytest.mark.parametrize('answer', [
    '会合の進行を担当した。その後、私は分担を決めた。',
    '私は会合の進行を担当した。その後、分担を決めた。',
    '彼は会合の進行を担当した。その後、私は分担を決めた。',
    '私は会合の進行を担当した。その後、彼は分担を決めた。',
    '私は会合の進行を担当した。その後、私は分担を決めた。まだ言えない。',
])
def test_unproved_answer_actor_or_unread_remainder_does_not_acquire_a_response(monkeypatch, answer):
    snap = answer_material(answer=answer)
    source = AsyncMock(side_effect=AssertionError('unproved answer acquired'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items': []}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def test_complete_snapshot_keeps_each_witness_unknown_record_category_and_local_order():
    snap = multi_material()
    value = multi_proposal(snap)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert counts == dict(profile='cumulative.v1', source_count=7, processed_count=7,
        mapped_count=6, unparsed_count=2, excluded_count=0, exclusion_reasons={}, stale_supplement_count=0)
    assert len(artifact.source_members) == len(artifact.category_records) == 7
    assert {m.saved_record_ref for m in artifact.source_members} == {m['original']['id'] for m in snap['members']}
    nodes = artifact.graph.nodes
    assert len({n.node_ref for n in nodes}) == len(nodes) == 9
    assert [n.node_ref for n in nodes] == ['n' + str(i) for i in range(1, 10)]
    by_record = {m['original']['id']: [n for n in nodes if m['original']['id'] in n.record_refs]
        for m in snap['members']}
    assert [len(by_record[m['original']['id']]) for m in snap['members']] == [1, 2, 1, 2, 2, 1, 0]
    for member in snap['members']:
        ref = member['original']['id']
        for node in by_record[ref]:
            assert node.record_refs == (ref,)
            assert node.selected_categories == tuple(member['original']['category'])
            assert {e.source_envelope_id for e in node.evidence_refs} <= set(next(
                m.child_source_envelope_refs for m in artifact.source_members if m.saved_record_ref == ref))
    edge, = artifact.graph.edges
    assert edge.edge_kind == 'OBSERVED_ORDER'
    endpoints = [next(n for n in nodes if n.node_ref == r) for r in edge.endpoint_refs]
    assert endpoints[0].record_refs == endpoints[1].record_refs == (snap['members'][4]['original']['id'],)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '受付係' in text and '案内係' in text and '記録された担当' in text and '行わなかった' in text
    service._checked_projection(artifact.safe_projection(authenticated_owner_scope=OWNER), str(UUID(artifact.artifact_id[9:])))


@pytest.mark.parametrize('count', [2, 201])
def test_all_owned_records_remain_in_one_model_request_including_oldest(count):
    snap = source_snapshot(count)
    for member in snap['members']:
        member['original'].update(memo='僕の役割は受付係だった。', memo_action='')
    value = multi_proposal(snap)
    assert len(json.loads(value.messages()[1]['content'])['fields']) == count
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == count
    assert counts['unparsed_count'] == 0 and len(artifact.source_members) == count
    assert {r for n in artifact.graph.nodes for r in n.record_refs} == {m['original']['id'] for m in snap['members']}
    assert not artifact.graph.edges


@pytest.mark.parametrize('different_category', [False, True])
def test_finite_action_equivalence_and_record_badges_use_the_canonical_cumulative_signature(different_category):
    snap = source_snapshot(2)
    for member, memo in zip(snap['members'], ['僕は費用を記録した。', '僕は費用を記録しました。']):
        member['original'].update(memo=memo, memo_action='')
    if different_category: snap['members'][1]['original']['category'] = ['生活']
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    finite, finite_counts = service.build_cumulative_map(OWNER, snap)
    assert counts == finite_counts and artifact.graph == finite.graph
    assert len(artifact.graph.nodes) == (2 if different_category else 1)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert [n['evidence_badge_count'] for n in projection['nodes']] == ([1, 1] if different_category else [2])
    assert not artifact.graph.edges


@pytest.mark.parametrize('defect', ['memo', 'category', 'guard', 'owner'])
def test_later_record_or_full_snapshot_identity_cannot_reuse_an_old_response(defect):
    snap = multi_material()
    value = multi_proposal(snap)
    owner = OWNER
    if defect == 'memo': snap['members'][-1]['original']['memo'] += '変更。'
    if defect == 'category': snap['members'][-1]['original']['category'] = ['別場面']
    if defect == 'guard': snap['guard'] = 'analysis-db-cumulative-v1:' + 'b' * 64
    if defect == 'owner': owner = str(UUID(int=2))
    with pytest.raises(ValueError):
        service.build_cumulative_map(owner, snap, model_input=value)


def test_bad_later_record_kind_does_not_borrow_another_records_role_or_finite_fallback():
    snap = multi_material()
    value = multi_proposal(snap)
    packet = json.loads(value.response.raw)
    packet['fields'][4]['units'][0]['node_kind'] = 'ACTION_OR_NONACTION'
    value = call(replace(value, response=None), packet)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    rejected = snap['members'][3]['original']['id']
    assert all(rejected not in n.record_refs for n in artifact.graph.nodes)
    assert counts['source_count'] == 7 and counts['mapped_count'] == 5 and counts['unparsed_count'] == 3


def test_safety_in_a_later_record_is_rejected_before_acquisition(monkeypatch):
    snap = multi_material()
    snap['members'][-1]['original']['memo'] = '死にたい。'
    source = AsyncMock(side_effect=AssertionError('unsafe response acquisition'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items': []}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=snap))
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def test_clause_author_uses_its_own_action_witness_after_canonical_action_aggregation():
    snap = source_snapshot(3)
    for member, memo in zip(snap['members'], ['僕は費用を記録しました。',
            '僕の役割は受付係だった。僕は費用を記録した。', 'まだ言葉にできません。']):
        member['original'].update(memo=memo, memo_action='')
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    assert len(artifact.graph.nodes) == 2 and counts['mapped_count'] == 2 and counts['unparsed_count'] == 1
    action, role = artifact.graph.nodes
    assert len(action.record_refs) == len(action.evidence_refs) == 2
    assert role.proposition.role_state == 'WRITTEN_PAST_ROLE_CLAUSE'
    assert '受付係' in artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert any(g.missing_scope == 'SOURCE_SCOPE' for g in artifact.graph.unknown_gaps)


@pytest.mark.parametrize('defect', ['source_records', 'source_members', 'cross_edge', 'cross_gap'])
def test_multi_clause_author_does_not_accept_another_records_proof(defect):
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
    snap = multi_material()
    artifact, _ = service.build_cumulative_map(OWNER, snap, model_input=multi_proposal(snap))
    clause = next(n for n in artifact.graph.nodes if n.proposition.role_state == 'WRITTEN_PAST_ROLE_CLAUSE')
    other = next(n for n in artifact.graph.nodes if n.record_refs != clause.record_refs)
    if defect == 'source_records': artifact = replace(artifact, category_records=artifact.category_records[:-1])
    if defect == 'source_members': artifact = replace(artifact, source_members=artifact.source_members[:-1])
    if defect == 'cross_edge':
        artifact = replace(artifact, graph=replace(artifact.graph, edges=artifact.graph.edges + (
            compiler.ObservedEdge('e99', 'OBSERVED_ORDER', (clause.node_ref, other.node_ref), clause.evidence_refs + other.evidence_refs),)))
    if defect == 'cross_gap':
        artifact = replace(artifact, graph=replace(artifact.graph, unknown_gaps=artifact.graph.unknown_gaps + (
            compiler.UnknownGap('g99', (clause.node_ref, other.node_ref), 'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'),)))
    with pytest.raises(AnalysisSourceError):
        artifact.safe_projection(authenticated_owner_scope=OWNER)


@pytest.mark.parametrize('ensure,mode', [(False,'development'), (True,'read_only'), (True,'off')])
def test_read_only_routes_never_acquire_a_response(monkeypatch, ensure, mode):
    source = AsyncMock(side_effect=AssertionError('read generated'))
    monkeypatch.setattr(service, 'read_maps', AsyncMock(return_value={'items':[]}))
    monkeypatch.setattr(service, '_rpc', AsyncMock(side_effect=AssertionError('read wrote')))
    monkeypatch.setattr(service, 'observed_mode', lambda:mode)
    assert not run(service.ensure_map(OWNER, ensure=ensure, model_source=source))['has_visible_content']
    source.assert_not_awaited()


@pytest.fixture
def model_lifecycle(monkeypatch):
    """Real model admission/build with isolated commit/read state."""
    state = dict(snapshot=material('pair'), commits=[], row=None)
    async def read(owner, **kwargs):
        row = state['row']
        return dict(items=[copy.deepcopy(row)] if row else [])
    async def rpc(name, payload):
        if name == 'analysis_cumulative_source_snapshot':
            return copy.deepcopy(state['snapshot'])
        assert name == 'analysis_cumulative_commit'
        if payload['p_guard'] != state['snapshot']['guard']:
            raise HTTPException(409, 'analysis_source_changed')
        if 'p_existing_id' in payload:
            return payload['p_existing_id']
        state['commits'].append(copy.deepcopy(payload))
        rid = str(UUID(payload['p_artifact_id'][9:]))
        state['row'] = dict(id=rid, period_start=payload['p_start'], period_end=payload['p_end'],
            generated_at=payload['p_end'], title='わたしマップ', snapshot_month=None, captured_at=None,
            content_text=payload['p_text'], content_json=dict(watashiMap=payload['p_projection'],
                map_context=payload['p_private_evidence']['coverage']))
        return rid
    monkeypatch.setattr(service, 'read_maps', read)
    monkeypatch.setattr(service, '_rpc', rpc)
    monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
    yield state
    assert not service._model_map_flights


def test_overlapping_model_updates_share_one_snapshot_response_commit_and_independent_dtos(model_lifecycle):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        received = []
        async def source(prepared):
            received.append(prepared)
            entered.set()
            await release.wait()
            return synthetic_response(prepared)
        tasks = [asyncio.create_task(service.ensure_map(OWNER, force=True, model_source=source)) for _ in range(3)]
        await entered.wait()
        # Saved reads are independent and do not wait for this model request.
        readonly = await service.ensure_map(OWNER, ensure=False, model_source=source)
        assert not readonly['has_visible_content']
        release.set()
        values = await asyncio.gather(*tasks)
        assert len(received) == len(model_lifecycle['commits']) == 1
        assert values[0] == values[1] == values[2]
        values[0]['meta']['nodes'].clear()
        assert values[1]['meta']['nodes'] and model_lifecycle['row']['content_json']['watashiMap']['nodes']
        # An explicit later force update is fresh, not a retained result cache.
        later = await service.ensure_map(OWNER, force=True, model_source=source)
        assert len(received) == len(model_lifecycle['commits']) == 2
        assert later['report_id'] != values[1]['report_id']
    run(scenario())


@pytest.mark.parametrize('failure,code,detail', [
    (OSError('secret connection address'), 503, 'analysis_model_source_unavailable'),
    (RuntimeError('private provider diagnostics'), 503, 'analysis_model_source_unavailable'),
    (httpx.ConnectError('private provider URL'), 503, 'analysis_model_source_unavailable'),
    (TimeoutError('provider timeout'), 504, 'analysis_model_source_timeout'),
    (ValueError('malformed response'), 422, 'analysis_saved_source_unavailable'),
])
def test_model_failure_is_shared_sanitized_not_saved_and_can_be_retried(model_lifecycle, failure, code, detail):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []
        async def source(prepared):
            calls.append(prepared)
            entered.set()
            await release.wait()
            if len(calls) == 1:
                raise failure
            return synthetic_response(prepared)
        tasks = [asyncio.create_task(service.ensure_map(OWNER, model_source=source)) for _ in range(2)]
        await entered.wait()
        release.set()
        errors = await asyncio.gather(*tasks, return_exceptions=True)
        assert all(isinstance(e, HTTPException) and e.status_code == code and e.detail == detail for e in errors)
        assert len(calls) == 1 and not model_lifecycle['commits'] and not service._model_map_flights
        assert (await service.ensure_map(OWNER, model_source=source))['refreshed']
        assert len(calls) == 2 and len(model_lifecycle['commits']) == 1
    run(scenario())


@pytest.mark.parametrize('swallow', [False, True])
def test_model_deadline_cancels_provider_and_rejects_late_response(model_lifecycle, monkeypatch, swallow):
    monkeypatch.setattr(service, 'MODEL_SOURCE_TIMEOUT_SECONDS', 0.02)
    async def scenario():
        cancelled = asyncio.Event()
        async def source(prepared):
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                if swallow:
                    return synthetic_response(prepared)
                raise
        with pytest.raises(HTTPException) as error:
            await service.ensure_map(OWNER, model_source=source)
        assert error.value.status_code == 504 and error.value.detail == 'analysis_model_source_timeout'
        assert cancelled.is_set() and not model_lifecycle['commits'] and not service._model_map_flights
    run(scenario())


@pytest.mark.parametrize('all_waiters,swallow', [(False, False), (True, False), (True, True)])
def test_cancelled_waiters_do_not_cancel_other_readers_or_allow_abandoned_commit(model_lifecycle, all_waiters, swallow):
    async def scenario():
        entered, release, cancelled = asyncio.Event(), asyncio.Event(), asyncio.Event()
        calls = []
        async def source(prepared):
            calls.append(prepared)
            entered.set()
            try:
                await release.wait()
            except asyncio.CancelledError:
                cancelled.set()
                if not swallow:
                    raise
            return synthetic_response(prepared)
        tasks = [asyncio.create_task(service.ensure_map(OWNER, model_source=source)) for _ in range(2)]
        await entered.wait()
        flight, = service._model_map_flights.values()
        tasks[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[0]
        assert not cancelled.is_set()
        if all_waiters:
            tasks[1].cancel()
            with pytest.raises(asyncio.CancelledError):
                await tasks[1]
            with pytest.raises(asyncio.CancelledError):
                await flight.task
            assert cancelled.is_set() and not model_lifecycle['commits']
        else:
            release.set()
            assert (await tasks[1])['refreshed']
            assert len(model_lifecycle['commits']) == 1 and not cancelled.is_set()
        assert len(calls) == 1 and not service._model_map_flights
    run(scenario())


@pytest.mark.parametrize('mode', ['read_only', 'off'])
def test_switch_to_saved_reads_while_model_waits_prevents_generated_commit(model_lifecycle, monkeypatch, mode):
    async def source(prepared):
        response = synthetic_response(prepared)
        monkeypatch.setattr(service, 'observed_mode', lambda: mode)
        assert not (await service.ensure_map(OWNER, model_source=source))['has_visible_content']
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 503 and not model_lifecycle['commits']


@pytest.mark.parametrize('difference', ['owner', 'callable', 'force', 'monthly'])
def test_model_updates_do_not_share_different_owner_provider_or_view(monkeypatch, difference):
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []
        async def fake_ensure(owner, **kwargs):
            calls.append((owner, kwargs))
            if len(calls) == 2:
                entered.set()
            await release.wait()
            return {'owner': owner}
        monkeypatch.setattr(service, '_ensure_map', fake_ensure)
        monkeypatch.setattr(service, 'observed_mode', lambda: 'development')
        source, other = object(), object()
        first = asyncio.create_task(service.ensure_map(OWNER, model_source=source))
        kwargs = dict(model_source=other if difference == 'callable' else source,
            force=difference == 'force', monthly=difference == 'monthly')
        second = asyncio.create_task(service.ensure_map(str(UUID(int=2)) if difference == 'owner' else OWNER, **kwargs))
        await asyncio.wait_for(entered.wait(), 1)
        release.set()
        await asyncio.gather(first, second)
        assert len(calls) == 2 and not service._model_map_flights
    run(scenario())


@pytest.fixture
def sql_source(monkeypatch):
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('PostgreSQL WASM dependency is not configured')
    from test_emlis_q3_application import Q3Database
    db = Q3Database()
    try:
        db.migrate()
        for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                     '20261101080144_cumulative_watashi_map.sql'):
            db.proc.stdin.write(json.dumps({'script':True, 'sql':(Path(__file__).parents[2]/'supabase/migrations'/name).read_text()})+'\n')
            db.proc.stdin.flush()
            assert 'code' not in json.loads(db.proc.stdout.readline())
        async def rpc(name, payload):
            args = ','.join(f'{key} => ${i}' for i,key in enumerate(payload,1))
            params = [json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
            result = await asyncio.to_thread(db.query, f'select public.{name}({args}) as value', params, 'service_role')
            if 'code' in result: raise HTTPException(409, result['code'])
            return result['rows'][0]['value']
        monkeypatch.setattr(service, '_rpc', rpc)
        monkeypatch.setattr(service, 'observed_mode', lambda:'development')
        yield db, rpc
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)


def insert_material(db, mode):
    original = material('role' if mode == 'combined' else mode)['members'][0]['original']
    if mode == 'combined': original['memo'] += '僕は費用を記録した。'
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
    assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
        [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
         original['category'], original['emotions'], json.dumps(original['emotion_details'])])
    return original


@pytest.mark.parametrize('text,nodes,edges,actor_unknown',[
    ('資料を調べた。',1,0,True),
    ('僕は資料を調べた。僕は費用を記録した。',2,0,False),
    ('私は資料を見た。その後、私は分担を決めた。',2,1,False)])
def test_real_sql_model_actions_keep_source_scope_and_non_generating_rereads(sql_source,text,nodes,edges,actor_unknown):
    db,_=sql_source
    original=insert_material(db,'role')
    assert 'code' not in db.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
        [text,'',original['id']])
    calls=[]
    async def source(prepared):
        calls.append(prepared)
        return synthetic_response(prepared)
    first=run(service.ensure_map(OWNER,model_source=source))
    assert len(calls)==1 and first['refreshed'] and first['has_visible_content']
    assert len(first['meta']['nodes'])==nodes and len(first['meta']['edges'])==edges
    assert ('誰の行動かは未確定' in first['content_text'])==actor_unknown
    assert first['map_context']['mapped_count']==1 and first['map_context']['unparsed_count']==0
    forbidden=AsyncMock(side_effect=AssertionError('saved model acquisition'))
    with patch.object(service,'build_cumulative_map',side_effect=AssertionError('saved generation')):
        saved=[run(service.ensure_map(OWNER,model_source=forbidden)),
            run(service.ensure_map(OWNER,monthly=True,force=True,model_source=forbidden)),
            run(service.ensure_map(OWNER,ensure=False,model_source=forbidden))]
    forbidden.assert_not_awaited()
    for value in saved:
        assert value['report_id']==first['report_id'] and not value['refreshed']
        assert value['meta']==first['meta'] and value['content_text']==first['content_text']
        assert value['map_context']==first['map_context']


@pytest.mark.parametrize('mode', ['role', 'pair', 'clause', 'combined'])
def test_real_sql_fresh_source_normal_commit_and_immutable_month(sql_source, monkeypatch, mode):
    db, rpc = sql_source
    original = insert_material(db, mode)
    earlier = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id':OWNER}))
    stale = service.prepare_cumulative_category_units(OWNER, earlier, prompt_version='selected_material.v4')
    received = []
    async def source(prepared):
        assert prepared.response is None and prepared.prompt_version == 'selected_material.v4'
        assert prepared.source_guard == earlier['guard']
        assert prepared.request_ref != stale.request_ref
        received.append(prepared)
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['has_visible_content'] and first['refreshed'] and len(received) == 1
    assert '受付係' in first['content_text'] and '記録された役割' in first['content_text']
    assert len(first['meta']['nodes']) == (2 if mode in {'pair', 'combined'} else 1)
    assert first['map_context']['unparsed_count'] == int(mode == 'clause')
    if mode == 'clause': assert '費用を記録' not in first['content_text']
    raw = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1', [first['report_id']])['rows'][0]['private_evidence']
    assert raw['source_record_refs'] == [original['id']]
    assert raw['coverage'] == first['map_context']
    assert 'raw_sha256' not in json.dumps(raw)
    # Actual read validators and SQL run; only generation and source are forbidden.
    forbidden = AsyncMock(side_effect=AssertionError('saved read acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved read generated')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        monthly = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    forbidden.assert_not_awaited()
    for value in (current,monthly,readonly):
        assert value['meta'] == first['meta'] and value['content_text'] == first['content_text']
        assert value['report_id'] == first['report_id'] and not value['refreshed']
    assert detail['content_json']['watashiMap'] == first['meta']
    evidence = run(service.map_evidence(OWNER, first['report_id'], first['meta']['nodes'][0]['node_ref'], month=monthly['snapshot_month']))
    assert evidence['items'] and all(x['version_state'] == 'CURRENT' for x in evidence['items'])
    # A later valid rebuild updates current, but never rewrites this month's capture.
    db.query("update public.emotions set memo=replace(memo,'だった','ではなかった') where id=$1", [original['id']])
    async def updated(prepared): return synthetic_response(prepared)
    second = run(service.ensure_map(OWNER, force=True, model_source=updated))
    assert second['refreshed'] and second['report_id'] != first['report_id']
    assert second['content_text'] != first['content_text']
    history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
    assert history['meta'] == monthly['meta'] and history['content_text'] == monthly['content_text']
    assert history['captured_at'] == monthly['captured_at']
    forbidden.assert_not_awaited()


def test_real_sql_source_edit_during_response_rejects_commit(sql_source):
    db, _ = sql_source
    original = insert_material(db, 'pair')
    calls = []
    async def source(prepared):
        response = synthetic_response(prepared)
        calls.append(prepared.request_ref)
        db.query("update public.emotions set memo=memo || '変更。' where id=$1", [original['id']])
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001'
    assert len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0


def test_real_sql_overlapping_force_calls_share_one_save_and_month_snapshot(sql_source):
    db, _ = sql_source
    insert_material(db, 'pair')
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []
        async def source(prepared):
            calls.append(prepared.request_ref)
            entered.set()
            await release.wait()
            return synthetic_response(prepared)
        updates = [asyncio.create_task(service.ensure_map(OWNER, force=True, model_source=source)) for _ in range(3)]
        await entered.wait()
        release.set()
        values = await asyncio.gather(*updates)
        assert values[0] == values[1] == values[2] and len(calls) == 1
        assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 1
        assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 1
        forbidden = AsyncMock(side_effect=AssertionError('saved read acquired model response'))
        month = await service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden)
        assert month['report_id'] == values[0]['report_id'] and month['meta'] == values[0]['meta']
        forbidden.assert_not_awaited()
    run(scenario())


def test_real_sql_implicit_configured_http_source_uses_latest_bound_input(sql_source, monkeypatch):
    db, _ = sql_source
    insert_material(db, 'pair')
    select_provider(monkeypatch)
    original_prepare = service.prepare_cumulative_category_units
    prepared_inputs, received = [], []
    def prepare(*args, **kwargs):
        value = original_prepare(*args, **kwargs)
        prepared_inputs.append(value)
        return value
    monkeypatch.setattr(service, 'prepare_cumulative_category_units', prepare)
    async def handler(request):
        received.append(json.loads(request.content))
        prepared = prepared_inputs[0]
        assert received[0]['messages'] == prepared.messages()
        return httpx.Response(200, json=provider_packet(synthetic_response(prepared).raw))
    mock_provider(monkeypatch, handler)
    async def scenario():
        values = await asyncio.gather(*(service.ensure_map(OWNER, force=True) for _ in range(3)))
        assert values[0] == values[1] == values[2] and len(received) == 1
        assert values[0]['refreshed'] and values[0]['map_context']['mapped_count'] == 1
        assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 1
        assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 1
        monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', '')
        saved = await service.ensure_map(OWNER, monthly=True, force=True)
        assert saved['meta'] == values[0]['meta'] and saved['content_text'] == values[0]['content_text']
        assert len(received) == 1
    run(scenario())


def test_real_sql_timed_out_refresh_preserves_previous_current_and_month(sql_source, monkeypatch):
    db, _ = sql_source
    insert_material(db, 'pair')
    async def source(prepared):
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    month = run(service.ensure_map(OWNER, monthly=True))
    monkeypatch.setattr(service, 'MODEL_SOURCE_TIMEOUT_SECONDS', 0.02)
    async def blocked(prepared):
        await asyncio.Event().wait()
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, force=True, model_source=blocked))
    assert error.value.status_code == 504
    saved = run(service.ensure_map(OWNER, ensure=False))
    monthly = run(service.ensure_map(OWNER, monthly=True, force=True))
    assert saved['report_id'] == first['report_id'] and saved['meta'] == first['meta']
    assert saved['content_text'] == first['content_text']
    assert monthly['report_id'] == month['report_id'] and monthly['captured_at'] == month['captured_at']
    assert monthly['meta'] == month['meta'] and monthly['content_text'] == month['content_text']
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 1
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 1


def insert_additional_original(db, template, number, memo, category):
    original = dict(template, id=str(UUID(int=number)), memo=memo, memo_action='', category=[category])
    assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
        [original['id'], OWNER, original['created_at'], original['memo'], original['memo_action'],
         original['category'], original['emotions'], json.dumps(original['emotion_details'])])
    return original


def test_real_sql_full_snapshot_single_acquisition_saved_reads_force_refresh_and_monthly_immutability(sql_source):
    db, rpc = sql_source
    original = insert_material(db, 'role')
    action = insert_additional_original(db, original, 5002, '僕は費用を記録した。', '生活')
    unknown = insert_additional_original(db, original, 5003, 'まだ言葉にできません。', '仕事')
    calls = []
    async def source(prepared):
        calls.append(prepared.request_ref)
        assert len(prepared.request.members) == 3
        assert len(json.loads(prepared.messages()[1]['content'])['fields']) == 3
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['refreshed'] and len(calls) == 1
    assert first['map_context']['source_count'] == first['map_context']['processed_count'] == 3
    assert first['map_context']['mapped_count'] == 2 and first['map_context']['unparsed_count'] == 1
    private = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1',
        [first['report_id']])['rows'][0]['private_evidence']
    assert set(private['source_record_refs']) == {original['id'], action['id'], unknown['id']}
    assert private['coverage'] == first['map_context'] and len(private['source_members']) == 3
    forbidden = AsyncMock(side_effect=AssertionError('saved multi-record read acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved multi-record generation')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        month = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    for saved in (current, month, readonly):
        assert saved['report_id'] == first['report_id'] and saved['meta'] == first['meta']
        assert saved['content_text'] == first['content_text'] and not saved['refreshed']
    assert detail['content_json']['map_context'] == first['map_context']
    forbidden.assert_not_awaited()
    assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1',
        [action['id'], '僕は費用を記録しなかった。'])
    second = run(service.ensure_map(OWNER, force=True, model_source=source))
    assert second['refreshed'] and second['report_id'] != first['report_id'] and len(calls) == 2
    assert calls[0] != calls[1] and second['content_text'] != first['content_text']
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved multi-record refresh generation')):
        history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        current = run(service.ensure_map(OWNER, ensure=False, model_source=forbidden))
    assert history['report_id'] == first['report_id'] and history['meta'] == month['meta']
    assert history['captured_at'] == month['captured_at'] and history['content_text'] == month['content_text']
    assert current['meta'] == second['meta'] and current['content_text'] == second['content_text']
    forbidden.assert_not_awaited()


def test_real_sql_nonfirst_record_change_during_multi_response_rejects_whole_commit(sql_source):
    db, _ = sql_source
    original = insert_material(db, 'role')
    action = insert_additional_original(db, original, 5002, '僕は費用を記録した。', '生活')
    calls = []
    async def source(prepared):
        assert len(prepared.request.members) == 2
        response = synthetic_response(prepared)
        calls.append(prepared.request_ref)
        assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1',
            [action['id'], '僕は費用を記録しなかった。'])
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001' and len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0


def test_real_sql_natural_role_decision_preserves_order_negative_refresh_and_month(sql_source):
    from test_analysis_model_role_decision import sample, response_for
    db, _ = sql_source
    original = insert_material(db, 'role')
    positive = sample()['members'][0]['original']
    assert 'code' not in db.query('update public.emotions set memo=$2,memo_action=$3,category=$4 where id=$1',
        [original['id'], positive['memo'], positive['memo_action'], ['生活']])
    calls = []
    async def source(prepared):
        calls.append(prepared.request_ref)
        return response_for(prepared, qualifiers=True, reorder=True)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['has_visible_content'] and first['refreshed'] and len(calls) == 1
    assert [n['node_kind'] for n in first['meta']['nodes']] == ['ROLE', 'ACTION_OR_NONACTION']
    role, decision = first['meta']['nodes']
    edge, = first['meta']['edges']
    assert edge['edge_kind'] == 'OBSERVED_ORDER'
    assert (edge['from_ref'], edge['to_ref']) == (role['node_ref'], decision['node_ref'])
    assert '会合の進行' in role['visible_label'] and '記録された担当' in role['visible_label']
    assert '分担を決める' in decision['visible_label'] and '実行済み' in decision['visible_label']
    assert '原因を示す線ではありません' in first['content_text']
    assert first['map_context']['source_count'] == first['map_context']['processed_count'] == first['map_context']['mapped_count'] == 1
    assert first['map_context']['unparsed_count'] == 0
    forbidden = AsyncMock(side_effect=AssertionError('saved natural role/decision acquired a response'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved natural role/decision generated')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        monthly = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, model_source=forbidden))
        detail = run(service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
    forbidden.assert_not_awaited()
    for saved in (current, monthly, readonly):
        assert not saved['refreshed'] and saved['report_id'] == first['report_id']
        assert saved['meta'] == first['meta'] and saved['content_text'] == first['content_text']
    assert detail['content_json']['watashiMap'] == first['meta']
    negative = sample(True, True)['members'][0]['original']
    assert 'code' not in db.query('update public.emotions set memo=$2 where id=$1',
        [original['id'], negative['memo']])
    second = run(service.ensure_map(OWNER, force=True, model_source=source))
    assert second['refreshed'] and second['report_id'] != first['report_id'] and len(calls) == 2
    assert calls[0] != calls[1]
    assert [n['node_kind'] for n in second['meta']['nodes']] == ['ROLE', 'ACTION_OR_NONACTION']
    assert '担当しなかった' in second['meta']['nodes'][0]['visible_label']
    assert '行わなかった' in second['meta']['nodes'][1]['visible_label']
    assert second['meta']['edges'] == first['meta']['edges'] and second['map_context']['unparsed_count'] == 0
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved natural role/decision generated')):
        history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        current = run(service.ensure_map(OWNER, ensure=False, model_source=forbidden))
    forbidden.assert_not_awaited()
    assert history['report_id'] == first['report_id'] and history['captured_at'] == monthly['captured_at']
    assert history['meta'] == first['meta'] and history['content_text'] == first['content_text']
    assert current['meta'] == second['meta'] and current['content_text'] == second['content_text']


def test_real_sql_saved_supplement_does_not_acquire_a_response(sql_source, monkeypatch):
    db, _ = sql_source
    original = insert_material(db, 'pair')
    import emlis_thread_store
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    from test_emlis_q3_application import answer
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    db.query("update public.emotions set memo=$2,memo_action='',created_at=(now()-interval '1 day') at time zone 'UTC',emotions=array['不安'],emotion_details=$3 where id=$1",
        [original['id'], '褒められたのに、嬉しくなかった。', json.dumps([dict(type='不安',strength='medium')])])
    emlis = EmlisThreadService(runtime_profile=Q3_PROFILE)
    dto = run(emlis.start(OWNER, original['id']))
    assert dto.get('pending_question') is not None
    run(answer(emlis, OWNER, dto, 'その時は重かった。', 'analysis-supplement'))
    source = AsyncMock(side_effect=AssertionError('supplement response acquired'))
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 422
    source.assert_not_awaited()


def insert_bound_answer(db, rpc, answer_text='僕は費用を記録した。'):
    """Use the existing saved-answer envelope shape in the real SQL snapshot."""
    original = insert_material(db, 'role')
    assert 'code' not in db.query('update public.emotions set emotion_details=$2 where id=$1',
        [original['id'], json.dumps([dict(type='平穏', strength='medium')])])
    snapshot = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id': OWNER}))
    member = with_answer(snapshot['members'][0], answer_text)
    thread = member['thread']
    assert 'code' not in db.query('''insert into public.emlis_input_threads
        (id,user_id,original_emotion_id,revision,state,issued_count,source_snapshot,data)
        values ($1,$2,$3,$4,'COMPLETED',$5,$6,$7)''',
        [thread['id'], OWNER, original['id'], thread['revision'], thread['issued_count'],
         json.dumps(thread['source_snapshot']), json.dumps(thread['data'])])
    for seq, event in enumerate(member['events'][:2], 1):
        assert 'code' not in db.query('''insert into public.emlis_thread_events
            (id,thread_id,seq,kind,round_index,question_id,payload) values ($1,$2,$3,$4,$5,$6,$7)''',
            [event['id'], thread['id'], seq, event['kind'], event['round_index'],
             event['question_id'], json.dumps(event['payload'])])
    return original, member['events'][1]['id']


def replace_bound_answer(db, answer_id, text):
    assert 'code' not in db.query('''update public.emlis_thread_events set
        payload=jsonb_set(payload,'{source,answer_text_private}',to_jsonb($2::text)) where id=$1''',
        [answer_id, text])


@pytest.mark.parametrize('answer_kind', ['plain', 'role_decision'])
def test_real_sql_ordinary_answer_normal_save_readonly_fresh_answer_and_immutable_month(sql_source, answer_kind):
    db, rpc = sql_source
    text = '僕は費用を記録した。' if answer_kind == 'plain' else role_decision_answer()
    original, answer_id = insert_bound_answer(db, rpc, text)
    calls = []
    async def source(prepared):
        calls.append(prepared)
        fields = json.loads(prepared.messages()[1]['content'])['fields']
        assert [f['source_role'] for f in fields] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
        return synthetic_response(prepared)
    first = run(service.ensure_map(OWNER, model_source=source))
    assert first['refreshed'] and len(calls) == 1
    assert len(first['meta']['nodes']) == (2 if answer_kind == 'plain' else 3)
    assert first['map_context']['source_count'] == first['map_context']['mapped_count'] == 1
    assert first['map_context']['unparsed_count'] == 0
    assert len(first['meta']['edges']) == int(answer_kind == 'role_decision')
    private = db.query('select private_evidence from public.analysis_observed_artifacts where id=$1',
        [first['report_id']])['rows'][0]['private_evidence']
    assert private['source_record_refs'] == [original['id']]
    assert len({e['source_envelope_id'] for n in private['graph']['nodes'] for e in n['evidence_refs']}) == 2
    forbidden = AsyncMock(side_effect=AssertionError('saved answer read generated'))
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved answer build')):
        current = run(service.ensure_map(OWNER, model_source=forbidden))
        month = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
        readonly = run(service.ensure_map(OWNER, ensure=False, force=True, model_source=forbidden))
    for saved in (current, month, readonly):
        assert saved['report_id'] == first['report_id'] and saved['meta'] == first['meta']
        assert saved['content_text'] == first['content_text'] and not saved['refreshed']
    changed = '僕は費用を記録しなかった。' if answer_kind == 'plain' else role_decision_answer(True, True)
    replace_bound_answer(db, answer_id, changed)
    stale = AsyncMock(return_value=synthetic_response(calls[0]))
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, force=True, model_source=stale))
    assert error.value.status_code == 422
    second = run(service.ensure_map(OWNER, force=True, model_source=source))
    assert second['refreshed'] and len(calls) == 2 and second['report_id'] != first['report_id']
    assert calls[1].source_guard != calls[0].source_guard and calls[1].request_ref != calls[0].request_ref
    assert '行わなかった' in second['content_text'] and second['map_context']['source_count'] == 1
    with patch.object(service, 'build_cumulative_map', side_effect=AssertionError('saved answer refresh build')):
        history = run(service.ensure_map(OWNER, monthly=True, force=True, model_source=forbidden))
    assert history['report_id'] == month['report_id'] and history['meta'] == month['meta']
    assert history['captured_at'] == month['captured_at'] and history['content_text'] == month['content_text']
    forbidden.assert_not_awaited()


@pytest.mark.parametrize('answer_kind', ['plain', 'role_decision'])
def test_real_sql_answer_edit_during_response_rejects_whole_commit(sql_source, answer_kind):
    db, rpc = sql_source
    text = '僕は費用を記録した。' if answer_kind == 'plain' else role_decision_answer()
    _, answer_id = insert_bound_answer(db, rpc, text)
    calls = []
    async def source(prepared):
        calls.append(prepared.request_ref)
        response = synthetic_response(prepared)
        changed = '僕は費用を記録しなかった。' if answer_kind == 'plain' else role_decision_answer(True, True)
        replace_bound_answer(db, answer_id, changed)
        return response
    with pytest.raises(HTTPException) as error:
        run(service.ensure_map(OWNER, model_source=source))
    assert error.value.status_code == 409 and error.value.detail == '40001' and len(calls) == 1
    assert db.query('select count(*) as n from public.analysis_observed_artifacts')['rows'][0]['n'] == 0
    assert db.query('select count(*) as n from public.analysis_cumulative_months')['rows'][0]['n'] == 0
