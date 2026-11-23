"""Exercise the split-history clocks against synthetic responses over HTTPX MockTransport."""
import asyncio
from dataclasses import replace
import json

import httpx
import pytest

import analysis_job_progress as progress
import analysis_merge_wire as wire
import analysis_model_source as sources
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_response_parser import exchange, planned
from test_analysis_occurrence_v17_record_owners import packet, prepared


# Integral seconds keep the strict per-phase upper bounds exact on every runner.
CLOCK_ORIGIN = 10_000.0


@pytest.fixture(scope='module')
def merge_exchange():
    stage, plan_packet = planned()
    material = json.loads(stage.material_json)
    material['history_stage']['profile'] = core.SEMANTIC_HISTORY_MERGE_PROFILE
    stage = replace(stage, material_json=core.semantic_map_canonical(material))
    plan_packet['source_choices_sha256'] = json.loads(stage.messages()[1]['content'])['source_choices_sha256']
    plan = core.admit_semantic_node_local_v4_plan_response(stage, plan_packet,
        merge_anchors=True, merge_action_sources=True)
    _, node_packet, _, _ = exchange('NODES')
    node_packet['plan_sha256'] = core.semantic_map_hash(['analysis.node-facts.v1', 'NODES', stage.request_ref, plan])
    nodes = core.admit_semantic_node_local_v4_nodes_response(stage, plan, node_packet)
    logical = core.semantic_node_local_v4_messages(stage, 'RELATIONS', plan=plan, nodes=nodes)
    registry = json.loads(logical[1]['content'])['candidate_nodes']
    relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(registry),
        qualification_review={}, edges=[], overview=dict(node_refs=['n1'], title='図面の問い合わせ'))
    expected = {}
    for phase, packet, options in [('PLAN', plan_packet, {}), ('NODES', node_packet, {'plan': plan}),
            ('RELATIONS', relations, {'plan': plan, 'nodes': nodes})]:
        messages = core.semantic_node_local_v4_wire_messages(stage, phase, **options)
        codec = wire.response_codec(messages)
        expected[phase] = (messages, wire.compact_json(codec.encode(packet) if codec else packet))
    return stage, expected


def model_source(stage, handler):
    return sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://test.invalid/chat/completions',
        model='test-model', api_key='synthetic-test', semantic_prompt_version=stage.prompt_version,
        transport=httpx.MockTransport(handler))


def successful_response(content):
    return httpx.Response(200, json=dict(model='test-model', usage=dict(completion_tokens=20),
        choices=[dict(finish_reason='stop', message=dict(role='assistant', content=content))]))


def test_progressing_phases_receive_fresh_clocks_and_keep_shared_tokens(monkeypatch, merge_exchange):
    stage, expected = merge_exchange
    phases = tuple(expected)

    async def scenario():
        loop = asyncio.get_running_loop()
        elapsed = 0
        sent = []
        monkeypatch.setattr(loop, 'time', lambda: CLOCK_ORIGIN + elapsed)

        async def handler(request):
            nonlocal elapsed
            phase = phases[len(sent) % 3]
            body = json.loads(request.content)
            messages, reply = expected[phase]
            assert body['messages'] == messages
            assert body['max_tokens'] == 4096 - (len(sent) % 3) * 20
            assert body['generation_seconds'] == 210
            assert 219 < request.extensions['timeout']['read'] <= 220
            assert request.extensions['timeout']['connect'] == 15
            sent.append(phase)
            elapsed += 180
            return successful_response(reply)

        source = model_source(stage, handler)
        for _ in range(2):
            result = await source(stage, per_phase=True)
            assert [row['phase'] for row in json.loads(result.raw)['phases']] == list(phases)
        assert sent == list(phases) * 2
        assert elapsed == 1080

    asyncio.run(scenario())


def test_default_transport_still_enforces_one_stage_clock(monkeypatch, merge_exchange):
    stage, expected = merge_exchange
    seen = []

    async def scenario():
        loop = asyncio.get_running_loop()
        elapsed = 0
        monkeypatch.setattr(loop, 'time', lambda: CLOCK_ORIGIN + elapsed)

        async def handler(request):
            nonlocal elapsed
            phase = tuple(expected)[len(seen)]
            seen.append(json.loads(request.content)['generation_seconds'])
            elapsed += 180
            return successful_response(expected[phase][1])

        with pytest.raises(TimeoutError, match='analysis_model_source_timeout'):
            await model_source(stage, handler)(stage)

    asyncio.run(scenario())
    assert len(seen) == 2 and seen[0] == 210 and 30 < seen[1] <= 35


@pytest.mark.parametrize('failure', [429, 503, 'cancel', 'late', 'invalid_content'])
@pytest.mark.parametrize('failed_phase', ['PLAN', 'NODES', 'RELATIONS'])
def test_failed_phase_never_posts_again(monkeypatch, merge_exchange, failed_phase, failure):
    stage, expected = merge_exchange
    phases = tuple(expected)
    sent = []
    checkpointed = []

    async def mark_checkpoint():
        checkpointed.append(sent[-1])

    monkeypatch.setattr(progress, 'checkpoint_v24_phase', mark_checkpoint)

    async def scenario():
        loop = asyncio.get_running_loop()
        elapsed = 0
        monkeypatch.setattr(loop, 'time', lambda: CLOCK_ORIGIN + elapsed)

        async def handler(request):
            nonlocal elapsed
            phase = phases[len(sent)]
            assert json.loads(request.content)['messages'] == expected[phase][0]
            sent.append(phase)
            if phase == failed_phase:
                if failure == 'cancel':
                    raise asyncio.CancelledError
                if failure == 'invalid_content':
                    return successful_response('{}')
                if failure != 'late':
                    return httpx.Response(failure)
                elapsed += 221
            else:
                elapsed += 180
            return successful_response(expected[phase][1])

        if failure == 'cancel':
            with pytest.raises(asyncio.CancelledError):
                await model_source(stage, handler)(stage, per_phase=True)
        else:
            error, code = ((TimeoutError, 'analysis_model_source_timeout') if failure == 'late'
                else (RuntimeError, 'analysis_model_source_unavailable'))
            with pytest.raises(error, match=code):
                await model_source(stage, handler)(stage, per_phase=True)

    asyncio.run(scenario())
    assert sent == list(phases[:phases.index(failed_phase) + 1])
    assert checkpointed == sent[:-1]


@pytest.mark.parametrize('claim_error', [progress.MapJobClaimChanged, progress.MapJobClaimUnavailable])
def test_worker_losing_checkpoint_stops_before_next_post(merge_exchange, claim_error):
    stage, expected = merge_exchange
    actions = []

    async def checkpoint():
        actions.append('checkpoint')
        raise claim_error('synthetic claim failure')

    async def unexpected_persistence_check():
        pytest.fail('transport attempted to persist an artifact')

    async def handler(request):
        phase = json.loads(json.loads(request.content)['messages'][1]['content'])['author_phase']
        actions.append(phase)
        return successful_response(expected[phase][1])

    async def scenario():
        with progress.map_job_progress(checkpoint, unexpected_persistence_check):
            with pytest.raises(claim_error):
                await model_source(stage, handler)(stage, per_phase=True)

    asyncio.run(scenario())
    assert actions == ['PLAN', 'checkpoint']


def test_v24_logs_invalid_plan_wire_without_model_data(caplog, merge_exchange):
    stage, _ = merge_exchange
    calls = []

    def handler(request):
        calls.append(request)
        return successful_response('{"private":"PRIVATE_REPLY"}')

    async def scenario():
        with pytest.raises(RuntimeError, match='analysis_model_source_unavailable'):
            await model_source(stage, handler)(stage, per_phase=True)

    asyncio.run(scenario())
    assert len(calls) == 1
    assert 'analysis_model_acquisition_failed phase=PLAN stage=phase_wire http_status=200' in caplog.text
    assert 'PRIVATE_REPLY' not in caplog.text
    assert 'test.invalid' not in caplog.text


@pytest.mark.parametrize('expected_stage,invalid_reply', [
    ('bridge_unavailable', {'error': 'analysis_bridge_unavailable', 'status': 503}),
    ('response_model', {'model': 'PRIVATE_WRONG_MODEL'}),
    ('response_choices', {'choices': []}),
    ('response_message', {'choices': [{'finish_reason': 'stop', 'message': {
        'role': 'assistant', 'content': 'PRIVATE_REPLY', 'reasoning_content': 'PRIVATE_REASONING'}}]}),
    ('response_content', {'choices': [{'finish_reason': 'stop', 'message': {
        'role': 'assistant', 'content': '  '}}]}),
])
def test_v24_logs_rejected_nodes_envelope_without_model_data(caplog, merge_exchange, expected_stage, invalid_reply):
    stage, expected = merge_exchange
    sent = []

    def handler(request):
        phase = json.loads(json.loads(request.content)['messages'][1]['content'])['author_phase']
        sent.append(phase)
        if phase == 'PLAN':
            return successful_response(expected[phase][1])
        if expected_stage == 'bridge_unavailable':
            return httpx.Response(200, content=b'   ' + json.dumps(invalid_reply).encode())
        return httpx.Response(200, json={'model': 'test-model', **invalid_reply})

    async def scenario():
        with pytest.raises(RuntimeError, match='analysis_model_source_unavailable'):
            await model_source(stage, handler)(stage, per_phase=True)

    asyncio.run(scenario())
    assert sent == ['PLAN', 'NODES']
    assert f'phase=NODES stage={expected_stage} http_status=200' in caplog.text
    assert 'PRIVATE_' not in caplog.text


def test_split_v24_leaf_renews_clock_after_accepted_plan(monkeypatch):
    note = '祖母は図面を保存した。'
    parent = prepared([note], core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    leaf = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))
    plan = packet(leaf, [[[(1, note)]]])
    posted = []

    async def scenario():
        loop = asyncio.get_running_loop()
        elapsed = 0
        monkeypatch.setattr(loop, 'time', lambda: CLOCK_ORIGIN + elapsed)

        async def handler(request):
            nonlocal elapsed
            body = json.loads(request.content)
            phase = json.loads(body['messages'][1]['content'])['author_phase']
            posted.append(phase)
            assert body['generation_seconds'] == 210
            assert 219 < request.extensions['timeout']['read'] <= 220
            if phase == 'PLAN':
                elapsed += 200
                return successful_response(wire.compact_json(plan))
            raise asyncio.CancelledError

        with pytest.raises(asyncio.CancelledError):
            await model_source(leaf, handler)(leaf, per_phase=True)

    asyncio.run(scenario())
    assert posted == ['PLAN', 'NODES']


@pytest.mark.parametrize('out_of_scope', ['old_profile', 'v23_leaf', 'v24_whole', 'shared_deadline'])
def test_per_phase_scope_is_checked_before_any_post(merge_exchange, out_of_scope):
    stage, _ = merge_exchange
    options = {'per_phase': True}
    if out_of_scope == 'shared_deadline':
        options['pipeline_deadline'] = 1
    elif out_of_scope == 'v24_whole':
        stage = stage.parent
    else:
        profile = core.SEMANTIC_MAP_PROFILE if out_of_scope == 'old_profile' else core.SEMANTIC_MAP_OCCURRENCE_V23_PROFILE
        parent = replace(stage.parent, prompt_version=profile)
        stage = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))

    def forbidden_request(request):
        pytest.fail('out of scope request reached the transport')

    with pytest.raises(core.AnalysisSemanticError, match='analysis_semantic_phase_scope_invalid'):
        asyncio.run(model_source(stage, forbidden_request)(stage, **options))
