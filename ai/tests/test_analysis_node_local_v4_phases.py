"""Three synthetic author phases prove contracts, never real model quality."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import time

import httpx
import pytest

import analysis_model_source as sources
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts
from test_emlis_natural_reply_probe_http import probe

PROFILE = core.SEMANTIC_MAP_NODE_LOCAL_V4_PROFILE
SCHEMA = core.SEMANTIC_MAP_NODE_LOCAL_V4_SCHEMA
ALIAS = sources.SEMANTIC_NODE_LOCAL_V4_MODEL
ENDPOINT = 'https://synthetic-analysis.invalid/v1/chat/completions'


def prepared():
    snap = source_snapshot(2)
    snap['members'][0]['original'].update(
        memo='私は図面を保存した。まだ送っていない。', memo_action='')
    snap['members'][1]['original'].update(
        memo='妹は椅子を直した。妹が机を直すかはわからない。', memo_action='')
    return app.prepare_semantic_map(OWNER, snap, prompt_version=PROFILE)


def phase_packets(p):
    fields = json.loads(p.material_json)['fields']
    first, second = fields[0]['field'], fields[1]['field']
    quote = '妹は椅子を直した。妹が机を直すかはわからない。'
    plan = dict(schema_version=SCHEMA + '.plan', nodes=[
        dict(node_id='n1', units=[dict(evidence=[dict(quote='私は図面を保存した。', field=first)])]),
        dict(node_id='n2', units=[dict(evidence=[dict(quote=quote, field=second)])])])
    def node(fact, title, unknowns=()):
        return dict(units={'u1': dict(source_mode='RECORDED', fact=fact, unknowns=list(unknowns))},
            node_kind='CHOICE_OUTPUT', perspective='SELF', title=title, meaning='')
    bodies = dict(schema_version=SCHEMA + '.nodes', plan_sha256=core.semantic_map_hash(plan), nodes={
        'n1': node('本人は図面を保存しました。', '保存した図面'),
        'n2': node('妹は椅子を直しましたが、机を直すかはわかりません。', '妹の修理と未確認の範囲',
            [dict(source_quote='妹が机を直すかはわからない。', source_field=second)])})
    bodies['nodes']['n2']['perspective'] = 'OBSERVED_INTERACTION'
    registry = core._semantic_v4_join(plan, bodies)
    relations = dict(schema_version=SCHEMA + '.relations',
        nodes_sha256=core.semantic_map_hash(registry), edges=[],
        overview=dict(title='保存と修理の記録', node_refs=['n1', 'n2']))
    return plan, bodies, relations


def artifact(p, values=None):
    values = phase_packets(p) if values is None else values
    plan = bodies = None
    rows = []
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, values, strict=True):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=bodies)
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        rows.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(messages),
            raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
            finish_reason='stop', completion_tokens=100))
        if phase == 'PLAN':
            plan = value
        elif phase == 'NODES':
            bodies = value
    return dict(schema_version=SCHEMA, phases=rows)


def response(p, value):
    raw = core.semantic_map_canonical(value)
    return core.AnalysisModelQuotedParentUnitsResponse(p.request_ref,
        core.semantic_map_hash(p.messages()), hashlib.sha256(raw.encode()).hexdigest(), 'stop', raw)


def source(handler):
    return sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT, model=ALIAS,
        api_key='synthetic-local-key', transport=httpx.MockTransport(handler),
        semantic_prompt_version=PROFILE)


def test_all_three_native_shapes_and_same_public_graph_with_exact_private_lineage():
    p = prepared()
    plan, bodies, relations = phase_packets(p)
    messages = [p.messages(),
        core.semantic_node_local_v4_messages(p, 'NODES', plan=plan),
        core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)]
    for value, selected in zip((plan, bodies, relations), messages, strict=True):
        assert accepts(value, selected)
    value = artifact(p)
    joined = core.assemble_semantic_node_local_v4(p, value)
    assert joined['nodes'][0]['node_id'] == 'n1'
    assert joined['nodes'][1]['units'][0]['evidence'] == plan['nodes'][1]['units'][0]['evidence']
    result, coverage = app.build_semantic_map(p, response(p, value))
    projection = result.safe_projection(authenticated_owner_scope=OWNER)
    assert projection and coverage['mapped_count'] == 2
    private = result.private_evidence()
    assert private['graph']['meaning_review']['node_local_plan']['phase_artifact'] == value


def test_real_three_transport_requests_keep_original_raw_and_freeze_actual_registry():
    p, calls = prepared(), []
    values = phase_packets(p)
    def handler(request):
        body = json.loads(request.content)
        phase = json.loads(body['messages'][1]['content'])['author_phase']
        index = len(calls)
        assert phase == core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES[index]
        assert body['max_tokens'] == 4096 - index * 100
        assert 0 < body['generation_seconds'] <= 210
        calls.append(body)
        return httpx.Response(200, json=dict(model=ALIAS, usage=dict(completion_tokens=100), choices=[dict(finish_reason='stop',
            message=dict(role='assistant', content=json.dumps(values[index], ensure_ascii=False)))]))
    result = asyncio.run(source(handler)(p))
    assert len(calls) == 3
    saved = json.loads(result.raw)
    assert sum(row['completion_tokens'] for row in saved['phases']) == 300
    assert core.assemble_semantic_node_local_v4(p, saved)['edges'] == []
    registry = json.loads(calls[2]['messages'][1]['content'])['candidate_nodes']
    assert registry == core._semantic_v4_join(values[0], values[1])
    assert saved['phases'][1]['raw'] == json.dumps(values[1], ensure_ascii=False)


@pytest.mark.parametrize('bad_phase', [0, 1, 2])
@pytest.mark.parametrize('failure', ['length', 'HTTP503', 'wrong_model'])
def test_incomplete_or_wrong_phase_never_starts_later_acquisition(bad_phase, failure):
    p, calls = prepared(), []
    values = phase_packets(p)
    def handler(request):
        index = len(calls)
        calls.append(json.loads(request.content))
        return httpx.Response(503 if index == bad_phase and failure == 'HTTP503' else 200,
            json=dict(model='wrong' if index == bad_phase and failure == 'wrong_model' else ALIAS,
                usage=dict(completion_tokens=100),
                choices=[dict(finish_reason='length' if index == bad_phase and failure == 'length' else 'stop',
                    message=dict(role='assistant', content=json.dumps(values[index], ensure_ascii=False)))]))
    with pytest.raises(RuntimeError, match='analysis_model_source_unavailable'):
        asyncio.run(source(handler)(p))
    assert len(calls) == bad_phase + 1


def test_cancellation_propagates_without_next_phase_or_retry():
    p, calls = prepared(), []
    async def handler(request):
        calls.append(request)
        raise asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(source(handler)(p))
    assert len(calls) == 1


def test_absolute_deadline_cancels_slow_continuous_stream(monkeypatch):
    p, calls = prepared(), []
    monkeypatch.setattr(sources, 'SEMANTIC_HTTP_TIMEOUT_SECONDS', .08)
    monkeypatch.setattr(sources, 'SEMANTIC_V4_RESPONSE_RESERVE_SECONDS', .005)
    class Stream(httpx.AsyncByteStream):
        async def __aiter__(self):
            for _ in range(100):
                await asyncio.sleep(.01)
                yield b' '
    def handler(request):
        calls.append(request)
        return httpx.Response(200, stream=Stream())
    start = time.monotonic()
    with pytest.raises(TimeoutError, match='analysis_model_source_timeout'):
        asyncio.run(source(handler)(p))
    assert time.monotonic() - start < .8 and len(calls) == 1


@pytest.mark.parametrize('mutation', ['raw_hash', 'messages_hash', 'finish', 'phase', 'inner_json'])
def test_phase_lineage_mutation_is_typed_rejection(mutation):
    p = prepared()
    value = artifact(p)
    row = value['phases'][1]
    if mutation == 'raw_hash':
        row['raw_sha256'] = 'f' * 64
    elif mutation == 'messages_hash':
        row['messages_sha256'] = 'f' * 64
    elif mutation == 'finish':
        row['finish_reason'] = 'length'
    elif mutation == 'phase':
        row['phase'] = 'PLAN'
    else:
        row['raw'] = '{"broken":'
        row['raw_sha256'] = hashlib.sha256(row['raw'].encode()).hexdigest()
    with pytest.raises(core.AnalysisSemanticMapError):
        core.assemble_semantic_node_local_v4(p, value)
    outcome = core.generate_analysis_semantic_map(p.request, replace(p, response=response(p, value)))
    assert outcome.status.value == 'REJECTED'


def test_fixed_plan_unknown_scope_and_registry_cannot_be_changed():
    p = prepared()
    plan, bodies, _ = phase_packets(p)
    bad = deepcopy(bodies)
    bad['nodes']['n1']['units']['u1']['unknowns'] = deepcopy(bodies['nodes']['n2']['units']['u1']['unknowns'])
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_nodes(p, plan, bad)
    selected = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)
    material = json.loads(selected[1]['content'])
    material['candidate_nodes'][0]['units'][0]['evidence'] = plan['nodes'][1]['units'][0]['evidence']
    selected[1]['content'] = json.dumps(material, ensure_ascii=False)
    with pytest.raises(ValueError):
        probe.semantic_output_schema(selected)


def test_existing_dictionary_source_boundaries_and_label_before_kind():
    p = prepared()
    plan, bodies, _ = phase_packets(p)
    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)
    assert '参照辞書（本人の事実ではない）' in messages[0]['content']
    assert 'source_duties' in json.loads(messages[1]['content'])
    schema = probe.semantic_output_schema(messages)
    assert list(schema['properties']['edges']['items']['properties']) == ['from', 'to', 'label', 'relation_kind']
    assert sources._configured_semantic_prompt_version(ALIAS) == PROFILE
    assert sources._configured_semantic_prompt_version(ALIAS + '-unknown') == core.SEMANTIC_MAP_PROFILE


def test_cross_record_corroboration_and_twentyfour_record_allocation_are_not_banned():
    p = prepared()
    plan, _, _ = phase_packets(p)
    plan['nodes'][0]['units'][0]['evidence'] += plan['nodes'][1]['units'][0]['evidence']
    plan['nodes'] = plan['nodes'][:1]
    assert core.semantic_node_local_v4_plan(p, plan) is plan
    snap = source_snapshot(24)
    many = app.prepare_semantic_map(OWNER, snap, prompt_version=PROFILE)
    fields = json.loads(many.material_json)['fields']
    plan = dict(schema_version=SCHEMA + '.plan', nodes=[dict(node_id='n' + str(i + 1),
        units=[dict(evidence=[dict(field=f['field'], quote='私は考えをノートに書いた。')])
            for f in fields[i * 2:i * 2 + 2]]) for i in range(12)])
    assert core.semantic_node_local_v4_plan(many, plan) is plan


def generated_phase_values(p):
    """Synthetic complete sources, not a model teacher or semantic acceptance."""
    fields = json.loads(p.material_json)['fields']
    by_record, corrections = {}, []
    for field in fields:
        if field['record'] is None:
            corrections.append(field)
        else:
            by_record.setdefault(field['record'], []).append(field)
    groups = [[items[0]] for items in by_record.values()]
    for field in corrections:
        # Keep the whole explanation attached to an existing represented
        # cohort node; this never replaces an original-record citation.
        index = next(i for i, group in enumerate(groups) if group[0]['record'] in field['record_refs'])
        groups[index].append(field)
    plan = dict(schema_version=SCHEMA + '.plan', nodes=[])
    bodies = dict(schema_version=SCHEMA + '.nodes', nodes={})
    for i, group in enumerate(groups, 1):
        ref = 'n' + str(i)
        plan['nodes'].append(dict(node_id=ref, units=[dict(evidence=[
            dict(quote=f['text'], field=f['field']) for f in group])]))
        bodies['nodes'][ref] = dict(units={'u1': dict(source_mode='RECORDED',
            fact=group[0]['text'], unknowns=[])}, node_kind='STATE_CONTEXT',
            perspective='SELF', title='記録' + str(i), meaning='')
    bodies['plan_sha256'] = core.semantic_map_hash(plan)
    relations = dict(schema_version=SCHEMA + '.relations',
        nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan, bodies)),
        edges=[], overview=dict(title='記録の範囲', node_refs=list(bodies['nodes'])[:8]))
    return plan, bodies, relations


def test_correction_cohort_full_explanation_and_leaf_merge_lineage_are_preserved(monkeypatch):
    from test_analysis_semantic_history_core import correction_snapshot
    from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer
    realized = []
    realize = observed_route_realizer.realize_analysis_semantic_map
    def observed(graph):
        realized.append(graph)
        return realize(graph)
    monkeypatch.setattr(observed_route_realizer, 'realize_analysis_semantic_map', observed)
    p = app.prepare_semantic_map(OWNER, correction_snapshot(), prompt_version=PROFILE)
    refs = tuple(m.saved_record_ref for m in p.frozen.members)
    with pytest.raises(core.AnalysisSemanticMapError, match='cohort_split'):
        core.prepare_semantic_leaf(p, refs[:1])
    leaves = []
    for records in (refs[:2], refs[2:]):
        leaf = core.prepare_semantic_leaf(p, records)
        values = generated_phase_values(leaf)
        value = artifact(leaf, values)
        receipt = response(leaf, value)
        partial = core.build_semantic_stage(leaf, receipt)
        assert json.loads(partial.coverage_json)['mapped_count'] == len(records)
        if len(records) == 2:
            correction = next(f for f in json.loads(leaf.material_json)['fields'] if f['record'] is None)
            assert any(e['field'] == correction['field'] and e['quote'] == correction['text']
                for n in values[0]['nodes'] for u in n['units'] for e in u['evidence'])
            bad = deepcopy(values[0])
            root = next(e for n in bad['nodes'] for u in n['units'] for e in u['evidence']
                if e['field'] == correction['field'])
            root['quote'] = root['quote'][1:]
            with pytest.raises(core.AnalysisSemanticMapError, match='evidence_incomplete'):
                core.semantic_node_local_v4_plan(leaf, bad)
        leaves.append((leaf, receipt))
    assert realized == []
    merge = core.prepare_semantic_merge(p, tuple(leaves))
    final = core.build_semantic_stage(merge, response(merge, artifact(merge, generated_phase_values(merge))))
    assert final.coverage['mapped_count'] == 3
    assert len(realized) == 1
    assert final.artifact.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'
    private = final.artifact.private_evidence()
    assert private['graph']['meaning_review']['node_local_plan']['phase_count'] == 3
    assert [r['raw'] for r in private['graph']['meaning_review']['history_synthesis']['leaf_candidates']] == [
        r.raw for _, r in leaves]


def test_all_existing_prompt_profiles_keep_exact_parent_wire_bytes():
    from test_analysis_semantic_map import sample
    # Independently captured from immutable d610facb, before v4 extraction
    # of the shared conditional source instructions.
    expected = {
        'semantic_map.v1': '8423602adb9d1b6f3ecfc81818a8c98d8cd52eb9c07a4f2ac29a32c99351b28a',
        'semantic_map.source_duties.v2': 'ff0716425bc802cbb1ef055cec155fe0d2c1f5373fa82748a57b0ea44d5066bf',
        'semantic_map.event_plan.v1': '5ffc60099f7daac312c67fe5d99ed92357132e488fa8e81de3bc182547745a6c',
        'semantic_map.event_plan.v2': 'f635e267b6a8aa0346c6ee4a7d80dee8d64cdedea82822ac061d9c0152a9d251',
        'semantic_map.node_local.v3': '5158e34fd77050b641fb8419aa497c9e8b612823d584fb874c314c822f6ddc88',
    }
    for profile, digest in expected.items():
        assert core.semantic_map_hash(app.prepare_semantic_map(OWNER, sample(),
            prompt_version=profile).messages()) == digest


def test_unknown_must_also_be_unique_in_original_full_field():
    snap = source_snapshot(2)
    snap['members'][0]['original']['memo'] = '未確認です。私は次に調べた。未確認です。'
    snap['members'][1]['original']['memo'] = '妹は椅子を直した。妹が机を直すかはわからない。'
    p = app.prepare_semantic_map(OWNER, snap, prompt_version=PROFILE)
    plan, bodies, _ = phase_packets(p)
    plan['nodes'][0]['units'][0]['evidence'][0]['quote'] = '私は次に調べた。未確認です。'
    bodies['plan_sha256'] = core.semantic_map_hash(plan)
    bodies['nodes']['n1']['units']['u1']['unknowns'] = [dict(source_quote='未確認です。', source_field=1)]
    with pytest.raises(core.AnalysisSemanticMapError, match='unknown_unbound'):
        core.semantic_node_local_v4_nodes(p, plan, bodies)


@pytest.mark.parametrize('usage', [None, 0, -1, True, 4097])
def test_invalid_phase_token_usage_stops_before_next_phase(usage):
    p, calls = prepared(), []
    plan = phase_packets(p)[0]
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=dict(model=ALIAS, usage=dict(completion_tokens=usage),
            choices=[dict(finish_reason='stop', message=dict(role='assistant', content=json.dumps(plan)))]))
    with pytest.raises(RuntimeError):
        asyncio.run(source(handler)(p))
    assert len(calls) == 1


def test_exhausted_total_token_budget_never_starts_second_generation():
    p, calls = prepared(), []
    plan = phase_packets(p)[0]
    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=dict(model=ALIAS, usage=dict(completion_tokens=4096),
            choices=[dict(finish_reason='stop', message=dict(role='assistant', content=json.dumps(plan)))]))
    with pytest.raises(RuntimeError):
        asyncio.run(source(handler)(p))
    assert len(calls) == 1


def test_native_v4_budget_and_usage_are_explicit_without_changing_default_identity():
    from http.server import ThreadingHTTPServer
    import threading
    p, calls = prepared(), []
    def generate(messages, end, *, profile=None, output_tokens=None):
        calls.append((profile, output_tokens, end - time.monotonic()))
        return 'synthetic-phase-raw', 'stop', dict(completion_tokens=17, prompt_tokens=20, total_tokens=37)
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name='original120u', event_plan_model=ALIAS,
        deadline=float('inf'), max_requests=1, max_new_tokens=4096, request_seconds=210))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        body = dict(model=ALIAS, messages=p.messages(), max_tokens=3072, generation_seconds=13,
            temperature=0, stream=False, chat_template_kwargs={'enable_thinking': False})
        with httpx.Client(trust_env=False) as client:
            url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
            def post(value):
                return client.post(url, headers={'Authorization': 'Bearer analysis-test-key'}, json=value)
            assert post(dict(body, max_tokens=4097)).status_code == 400
            assert post(dict(body, generation_seconds=211)).status_code == 400
            assert post(dict(body, model='original120u')).status_code == 400
            assert calls == []
            result = post(body)
            assert result.status_code == 200 and result.json()['usage']['completion_tokens'] == 17
            assert len(calls) == 1 and calls[0][:2] == ('event_plan', 3072) and 0 < calls[0][2] <= 13
    finally:
        server.shutdown()
        server.server_close()
        worker.join(3)
