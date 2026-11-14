"""Fictional CPU packet and fake HTTP only; no live endpoint or model call."""
import copy
import json
from pathlib import Path

import httpx
import pytest

from ai.tools import cmee_current_4b_packet as tool


@pytest.fixture
def packet():
    return tool.build_packet(natural_model='FICTIONAL_EXISTING_NATURAL',
        analysis_model='FICTIONAL_EXISTING_ANALYSIS', include_map=True)


def test_frozen_fictional_packet_is_bound_to_current_builders():
    path = Path(__file__).parent / 'fixtures/cmee_current_4b_packet_20261114.json'
    frozen = tool.validate_packet(json.loads(path.read_bytes()))
    rebuilt = tool.build_packet(natural_model=frozen['natural_model'],
        analysis_model=frozen['analysis_model'], include_map=True)
    assert len(frozen['cases']) == len(rebuilt['cases']) == 6
    assert [case['wire_json'] for case in frozen['cases']] == [case['wire_json'] for case in rebuilt['cases']]
    for saved, fresh in zip(frozen['cases'], rebuilt['cases'], strict=True):
        assert saved['originals'] == fresh['originals']
    text = path.read_text()
    assert 'Bearer ' not in text and 'API_KEY' not in text


def test_current_builders_preserve_source_roles_updates_and_exact_wire(packet):
    assert len(packet['cases']) == 6
    for case in packet['cases']:
        assert case['request_ref']
        for original in case['originals']:
            assert set(original) == {'id', 'created_at', 'category', 'emotions',
                'emotion_details', 'memo', 'memo_action'}
        assert tool.sha(case['wire_json']) == case['wire_sha256']
        assert len(case['wire_json'].encode()) == case['wire_bytes']
        wire = json.loads(case['wire_json'])
        assert wire['stream'] is False and wire['temperature'] == 0
        assert wire['chat_template_kwargs'] == {'enable_thinking': False}
        assert wire['max_tokens'] == (2048 if case['auth_scope'] == 'natural' else 4096)
    correction, rejected = packet['cases'][:2]
    writer = json.loads(json.loads(correction['wire_json'])['messages'][1]['content'])
    record, = writer['records']
    active = '\n'.join(field['text'] for field in record['active_fields'])
    assert '私は仕事を続けたい' not in active
    assert all(text in active for text in ('私は家族を守りたい', '私は費用を記録した', '私は資料を調べた'))
    writer = json.loads(json.loads(rejected['wire_json'])['messages'][1]['content'])
    feedback, = writer['user_frame_feedback']
    assert feedback['status'] == 'REJECTED' and feedback['target_binding'] == 'BOUND'
    assert feedback['target_ai_interpretation']['received_meaning'] == '重かった'
    if_case = packet['cases'][-1]
    assert if_case['prepared']['request']['requested_candidate_count'] == 2
    assert json.loads(if_case['wire_json'])['messages'] == json.loads(if_case['prepared']['messages_json'])


@pytest.mark.asyncio
async def test_packet_serialized_payload_matches_all_current_production_transports(packet):
    from analysis_if_model_source import SelfHostedAnalysisIfModelSource
    from analysis_if_route_service import _restore_prepared
    from analysis_model_source import SelfHostedSemanticAnalysisModelSource
    from analysis_semantic_map import prepare_semantic_map
    from piece_model_source import Shared4BPieceModelSource
    from piece_v2_contract import canonical_json_bytes
    from piece_v2_generation import PieceSourceSnapshot
    from cocolon_meaning_experience_engine.natural_reply import NaturalReplyInput, SelfHostedNaturalReplySource
    from cocolon_meaning_experience_engine.preparation import PreparedRequest
    from cocolon_meaning_experience_engine.piece_v1c import MODEL_REALIZATION_PROFILE, PieceGenerationRequest

    calls = []
    for case in packet['cases']:
        expected = json.loads(case['wire_json'])

        def handler(request):
            calls.append(request)
            assert json.loads(request.content) == expected
            return httpx.Response(503, json={'synthetic': 'capture only, no model'})

        kwargs = dict(endpoint='https://fictional.invalid/v1/chat/completions',
            model=expected['model'], api_key='fictional-private-key-only-0001',
            transport=httpx.MockTransport(handler))
        if case['owner'] == 'emlis':
            source = SelfHostedNaturalReplySource(**kwargs)
            prepared = NaturalReplyInput(**case['prepared'])
        elif case['owner'] == 'piece':
            source = Shared4BPieceModelSource(**kwargs, use_editorial_choices=True,
                realization_profile=MODEL_REALIZATION_PROFILE)
            prepared = PreparedRequest(**case['prepared'])
        elif case['owner'] == 'map':
            source = SelfHostedSemanticAnalysisModelSource(**kwargs,
                semantic_prompt_version=case['prepared']['prompt_version'])
            prepared = prepare_semantic_map(tool.OWNER, case['source_snapshot'],
                prompt_version=case['prepared']['prompt_version'])
        else:
            source = SelfHostedAnalysisIfModelSource(**kwargs, max_tokens=4096)
            prepared = _restore_prepared(case['prepared'])
        try:
            if case['owner'] == 'piece':
                record, = case['originals']
                saved = PieceSourceSnapshot(tool.OWNER, record['id'], 'emlis.current_input_bundle.v1',
                    '\n\n'.join(record[k] for k in ('memo', 'memo_action') if record[k]),
                    saved_original_json=canonical_json_bytes(record))
                request = PieceGenerationRequest('fictional-current-4b-' +
                    case['case_id'].removeprefix('PIECE-'), saved, tool.OWNER,
                    saved.saved_input_id, saved.source_version)
                await source(prepared, source_request=request)
            else:
                await source(prepared)
        except (ValueError, RuntimeError):
            pass  # The 503 is deliberate. The assertion inside capture is not.
    assert len(calls) == 6


@pytest.mark.asyncio
async def test_one_batch_is_six_posts_two_health_and_output_cannot_be_reused(packet, monkeypatch, tmp_path):
    monkeypatch.setenv('FICTIONAL_NATURAL_KEY', 'natural-secret-not-output')
    monkeypatch.setenv('FICTIONAL_ANALYSIS_KEY', 'analysis-secret-not-output')
    calls = []

    def handler(request):
        calls.append(request)
        if request.method == 'GET':
            assert request.url.path == '/healthz'
            assert 'authorization' not in request.headers
            return httpx.Response(200, json={'status': 'ok'})
        case = packet['cases'][len([r for r in calls if r.method == 'POST']) - 1]
        assert request.content == case['wire_json'].encode()
        expected = 'natural' if case['auth_scope'] == 'natural' else 'analysis'
        assert request.headers['Authorization'] == 'Bearer ' + expected + '-secret-not-output'
        return httpx.Response(200, json={'model': 'synthetic-only'})

    output = tmp_path / 'responses.json'
    kwargs = dict(endpoint='https://fictional.invalid/v1/chat/completions',
        health_endpoint='https://fictional.invalid/healthz', output=output,
        auth_envs=dict(natural='FICTIONAL_NATURAL_KEY', analysis='FICTIONAL_ANALYSIS_KEY'),
        transport=httpx.MockTransport(handler))
    result = await tool.execute_packet(packet, **kwargs)
    assert [r.method for r in calls] == ['GET'] + ['POST'] * 6 + ['GET']
    assert len(result['responses']) == 6 and result['attempt_consumed'] is True
    assert '-secret-not-output' not in output.read_text()
    assert output.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        await tool.execute_packet(packet, **kwargs)
    assert len(calls) == 8


@pytest.mark.asyncio
async def test_timeout_or_unknown_ack_never_retries_or_advances(packet, monkeypatch, tmp_path):
    monkeypatch.setenv('FICTIONAL_NATURAL_KEY', 'fictional-key')
    monkeypatch.setenv('FICTIONAL_ANALYSIS_KEY', 'fictional-key')
    calls = []

    def handler(request):
        calls.append(request.method)
        if request.method == 'POST':
            raise httpx.ReadTimeout('synthetic ACK loss')
        return httpx.Response(200, json={'status': 'ok'})

    result = await tool.execute_packet(packet,
        endpoint='https://fictional.invalid/v1/chat/completions',
        health_endpoint='https://fictional.invalid/healthz',
        auth_envs=dict(natural='FICTIONAL_NATURAL_KEY', analysis='FICTIONAL_ANALYSIS_KEY'),
        output=tmp_path / 'unknown.json', transport=httpx.MockTransport(handler))
    assert calls == ['GET', 'POST', 'GET']
    assert result['responses'][0]['state'] == 'FAILED_OR_ACK_UNKNOWN'


@pytest.mark.asyncio
async def test_batch_deadline_stops_new_posts_and_health(packet, monkeypatch, tmp_path):
    monkeypatch.setenv('FICTIONAL_NATURAL_KEY', 'fictional-key')
    monkeypatch.setenv('FICTIONAL_ANALYSIS_KEY', 'fictional-key')
    elapsed = [0.0]
    calls = []

    def handler(request):
        calls.append(request.method)
        if request.method == 'POST':
            elapsed[0] = 300.0
        return httpx.Response(200, json={'status': 'synthetic-only'})

    result = await tool.execute_packet(packet,
        endpoint='https://fictional.invalid/v1/chat/completions',
        health_endpoint='https://fictional.invalid/healthz',
        auth_envs=dict(natural='FICTIONAL_NATURAL_KEY', analysis='FICTIONAL_ANALYSIS_KEY'),
        output=tmp_path / 'deadline.json', transport=httpx.MockTransport(handler), clock=lambda: elapsed[0])
    assert calls == ['GET', 'POST'] and len(result['responses']) == 1
    assert result['failure'] == 'batch_deadline_reached'
    assert result['health_after'] is None and result['elapsed_seconds'] == 300.0


def test_unchanged_raw_returns_to_existing_cpu_owners(packet):
    from analysis_if_route_service import _restore_prepared
    from test_analysis_if_routes import packet as if_packet
    from analysis_semantic_map import MODEL_SCHEMA
    recorded = json.loads((Path(__file__).parent / 'fixtures/piece_cmee_realization_recorded.json').read_text())
    piece_raw = {'PIECE-' + row['case_id']: row['raw_output'] for row in recorded['rows']}
    rows = []
    for case in packet['cases']:
        wire = json.loads(case['wire_json'])
        if case['owner'] == 'emlis':
            raw = '書いてくださった内容を受け取りました。'
        elif case['owner'] == 'piece':
            raw = piece_raw[case['case_id']]
        elif case['owner'] == 'if':
            raw = json.dumps(if_packet(_restore_prepared(case['prepared'])), ensure_ascii=False)
        else:
            material = json.loads(wire['messages'][1]['content'])
            field = material['fields'][0]
            raw = json.dumps(dict(schema_version=MODEL_SCHEMA,
                overview=dict(title='記録にあること', summary='記録した内容を分けて読みます。'),
                nodes=[dict(node_id='n1', node_kind='STATE_CONTEXT', title='ノートに書いたこと',
                    summary='記録した内容です。', explanation='本人の記録から読みます。',
                    perspective='SELF', unknowns=[],
                    evidence=[dict(field=field['field'], quote=field['text'])])], edges=[]), ensure_ascii=False)
        response = dict(model=wire['model'], choices=[dict(finish_reason='stop',
            message=dict(role='assistant', content=raw))])
        if case['owner'] == 'piece':
            response['candidate_format'] = 'piece.field_slots.v1'
        rows.append(dict(case_id=case['case_id'], attempt=1, state='RECEIVED',
            status_code=200, body=json.dumps(response, ensure_ascii=False)))
    results = dict(packet_sha256=tool.sha(tool.canonical(packet)), responses=rows)
    before = copy.deepcopy(results)
    admitted = tool.admit_results(packet, results)
    assert results == before
    assert admitted['model_calls'] == admitted['database_writes'] == 0
    assert [row['status'] for row in admitted['results']] == [
        'FORMAT_ADMITTED', 'FORMAT_ADMITTED', 'GENERATED', 'GENERATED', 'GENERATED', 'GENERATED']
    for received, checked in zip(rows, admitted['results'], strict=True):
        raw = json.loads(received['body'])['choices'][0]['message']['content']
        assert checked['raw_sha256'] == tool.sha(raw)
    results['packet_sha256'] = 'wrong'
    with pytest.raises(ValueError, match='response_packet_binding_invalid'):
        tool.admit_results(packet, results)


def _if_parser_accepts(messages, raw):
    from ai.tools.serve_emlis_natural_reply import semantic_json_parser
    # Use the same pinned parser and initial Unicode alphabet as serving.
    raw_bytes = raw.encode('utf-8')
    decoded = raw_bytes.decode('utf-8')
    assert decoded.encode('utf-8') == raw_bytes
    parser = semantic_json_parser(messages, ''.join(dict.fromkeys(decoded)))
    for character in decoded:
        if character not in parser.get_allowed_characters():
            return False
        parser = parser.add_character(character)
    return parser.can_end()


def test_if_dispatcher_real_grammar_raw_and_existing_meaning_owner(packet):
    from ai.tools.serve_emlis_natural_reply import semantic_output_schema, IF_CANDIDATE_SCHEMA
    from analysis_if_route_service import _restore_prepared
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelQuotedParentUnitsResponse, digest)
    from test_analysis_if_routes import packet as if_packet
    case = packet['cases'][-1]
    prepared = _restore_prepared(case['prepared'])
    messages = prepared.messages()
    schema = semantic_output_schema(messages)
    assert schema['properties']['schema_version']['enum'] == [IF_CANDIDATE_SCHEMA]

    def admit(value):
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        assert _if_parser_accepts(messages, raw)
        response = AnalysisModelQuotedParentUnitsResponse(prepared.request_ref,
            digest(messages), tool.sha(raw), 'stop', raw)
        return MeaningExperienceEngine().generate(prepared.request, semantic_input=response)

    value = if_packet(prepared)
    valid = admit(value)
    assert valid.status.value == 'GENERATED' and valid.artifact is not None
    assert valid.artifact.to_storage()['model_receipt']['raw'] == json.dumps(
        value, ensure_ascii=False, separators=(',', ':'))
    # Well-formed JSON with an invented person choice still fails the owner.
    changed = copy.deepcopy(value)
    chosen = changed['scenarios'][0]['nodes'][1]
    chosen.update(origin='USER_CHOICE', text='本人が選んだと勝手に決めた別の案。')
    assert admit(changed).status.value == 'REJECTED'
    pending = admit(dict(schema_version=IF_CANDIDATE_SCHEMA, scenarios=[],
        clarification=dict(reason_code='CONSTRAINT_UNCLEAR', prompt='大切な条件を教えてください。')))
    assert pending.status.value == 'QUESTION_PENDING' and pending.artifact is None
    invalid = copy.deepcopy(value)
    invalid['scenarios'][0]['extra'] = 'unexpected'
    assert not _if_parser_accepts(messages, json.dumps(invalid, ensure_ascii=False))


def test_if_real_serving_closure_selects_mask_and_returns_exact_raw_to_owner(packet, monkeypatch):
    import time
    from analysis_if_route_service import _restore_prepared
    from test_analysis_if_routes import packet as if_packet
    from test_piece_model_server_constraints import synthetic_generator
    from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
        AnalysisModelQuotedParentUnitsResponse, digest)
    prepared = _restore_prepared(packet['cases'][-1]['prepared'])
    raw = json.dumps(if_packet(prepared), ensure_ascii=False, separators=(',', ':'))
    generate, captured, expected, eos = synthetic_generator(monkeypatch,
        constrained=True, raw_output=raw)
    returned, finish = generate(prepared.messages(), time.monotonic() + 10)
    assert (returned, finish) == (expected, 'stop')
    assert returned.encode('utf-8') == raw.encode('utf-8')
    assert len(captured['generate']) == 1
    options = captured['generate'][0]
    assert options['max_new_tokens'] == 4096 and options['eos_token_id'] == eos
    assert callable(options['prefix_allowed_tokens_fn'])
    outcome = MeaningExperienceEngine().generate(prepared.request,
        semantic_input=AnalysisModelQuotedParentUnitsResponse(prepared.request_ref,
            digest(prepared.messages()), tool.sha(returned), finish, returned))
    assert outcome.status.value == 'GENERATED'


@pytest.mark.parametrize('change', [
    lambda value: value.update(extra='unexpected'),
    lambda value: value.update(base_map_kind='PERSON_ORIGINAL'),
    lambda value: value.update(requested_candidate_count=True),
    lambda value: value['fields'][0].update(source_role='ORIGINAL_INPUT'),
    lambda value: value['fields'][0].update(extra='unexpected'),
])
def test_if_marker_requires_exact_prepared_shape(packet, change):
    from ai.tools.serve_emlis_natural_reply import semantic_output_schema
    messages = json.loads(packet['cases'][-1]['wire_json'])['messages']
    material = json.loads(messages[1]['content'])
    change(material)
    messages[1]['content'] = json.dumps(material, ensure_ascii=False)
    with pytest.raises(ValueError, match='if_material_invalid'):
        semantic_output_schema(messages)


def test_if_dispatch_leaves_legacy_map_schema_exact_bytes_and_unmarked_fields_unchanged():
    from ai.tools.serve_emlis_natural_reply import semantic_output_schema
    messages = [dict(role='system', content='synthetic'), dict(role='user', content=json.dumps(
        dict(fields=[dict(field=1, text='部屋を整えた。')]), ensure_ascii=False))]
    schema = semantic_output_schema(messages)
    assert len(tool.canonical(schema).encode()) == 2276
    assert tool.sha(tool.canonical(schema)) == '0234036789f0cf9c879e03c68a153cd5ea0cea338a8d040927651ceff1198075'
    material = json.loads(messages[1]['content'])
    material['model_schema'] = 'different.owner.v1'
    messages[1]['content'] = json.dumps(material, ensure_ascii=False)
    assert semantic_output_schema(messages) == schema
