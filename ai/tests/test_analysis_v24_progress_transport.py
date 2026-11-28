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


def successful_response(content, *, completion_tokens=20):
    return httpx.Response(200, json=dict(model='test-model', usage=dict(completion_tokens=completion_tokens),
        choices=[dict(finish_reason='stop', message=dict(role='assistant', content=content))]))


def test_progressing_phases_receive_fresh_clocks_and_keep_shared_tokens(monkeypatch, merge_exchange):
    stage, expected = merge_exchange
    phases = tuple(expected)

    async def scenario():
        loop = asyncio.get_running_loop()
        # Use an exact origin for the strict read-time bound below.
        base_time = 10_000.0
        elapsed = 0
        sent = []
        monkeypatch.setattr(loop, 'time', lambda: base_time + elapsed)

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
        base_time = loop.time()
        elapsed = 0
        monkeypatch.setattr(loop, 'time', lambda: base_time + elapsed)

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


@pytest.mark.parametrize('failure', [429, 503, 'heartbeat_429', 'cancel', 'late', 'invalid_content'])
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
        base_time = loop.time()
        elapsed = 0
        monkeypatch.setattr(loop, 'time', lambda: base_time + elapsed)

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
                if failure == 'heartbeat_429':
                    return httpx.Response(200, content=b' ' + json.dumps(dict(
                        error='analysis_bridge_rate_limited', status=429, retry_after='90')).encode())
                if failure != 'late':
                    return httpx.Response(failure, headers={'Retry-After': '90'})
                elapsed += 221
            else:
                elapsed += 180
            return successful_response(expected[phase][1])

        if failure == 'cancel':
            with pytest.raises(asyncio.CancelledError):
                await model_source(stage, handler)(stage, per_phase=True)
        elif failure in (429, 'heartbeat_429'):
            with pytest.raises(sources.AnalysisModelRateLimited, match='analysis_model_rate_limited') as captured:
                await model_source(stage, handler)(stage, per_phase=True)
            assert captured.value.retry_after == 90
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


@pytest.mark.parametrize('failure_stage', ['token_budget', 'prompt_build', 'prompt_bytes', 'request_bytes'])
@pytest.mark.parametrize('failed_phase', ['NODES', 'RELATIONS'])
def test_v24_distinguishes_pre_request_failures_without_model_data(
        monkeypatch, caplog, merge_exchange, failure_stage, failed_phase):
    stage, expected = merge_exchange
    phases = tuple(expected)
    sent = []
    prior_phase = phases[phases.index(failed_phase) - 1]

    if failure_stage in {'prompt_build', 'prompt_bytes'}:
        build = core.semantic_node_local_v4_wire_messages

        def fail_build(prepared, phase='PLAN', **kwargs):
            if phase != failed_phase:
                return build(prepared, phase, **kwargs)
            if failure_stage == 'prompt_build':
                raise ValueError('PRIVATE_CONTEXT')
            messages = build(prepared, phase, **kwargs)
            extra = dict(role='user', content='x' * (sources.SEMANTIC_MERGE_MAX_PROMPT_BYTES + 1))
            return [*messages, extra]

        monkeypatch.setattr(core, 'semantic_node_local_v4_wire_messages', fail_build)

    def handler(request):
        body = json.loads(request.content)
        phase = phases[len(sent)]
        sent.append(phase)
        completion_tokens = 20
        if phase == prior_phase:
            if failure_stage == 'token_budget':
                completion_tokens = body['max_tokens']
            elif failure_stage == 'request_bytes':
                monkeypatch.setattr(sources, 'SEMANTIC_MAX_REQUEST_BYTES', 1)
        return successful_response(expected[phase][1], completion_tokens=completion_tokens)

    async def scenario():
        with pytest.raises(RuntimeError, match='analysis_model_source_unavailable'):
            await model_source(stage, handler)(stage, per_phase=True)

    asyncio.run(scenario())
    assert sent == list(phases[:phases.index(failed_phase)])
    assert f'phase={failed_phase} stage={failure_stage} http_status=None' in caplog.text
    log = next(record for record in caplog.messages if 'analysis_model_acquisition_failed' in record)
    counts = dict(item.split('=', 1) for item in log.split()[5:])
    if failure_stage == 'token_budget':
        assert counts['remaining_tokens'] == '0' and counts['prompt_bytes'] == 'None'
    else:
        assert int(counts['remaining_tokens']) > 0
    if failure_stage == 'prompt_bytes':
        assert int(counts['prompt_bytes']) > int(counts['prompt_limit'])
    if failure_stage == 'request_bytes':
        assert int(counts['request_bytes']) > int(counts['request_limit'])
    assert 'PRIVATE_CONTEXT' not in caplog.text
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
        base_time = 10_000.0
        elapsed = 0
        monkeypatch.setattr(loop, 'time', lambda: base_time + elapsed)

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
