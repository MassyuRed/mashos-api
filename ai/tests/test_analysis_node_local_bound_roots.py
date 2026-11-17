"""Forced original-root context is a producer constraint, never meaning proof."""
import asyncio
from copy import deepcopy
from io import BytesIO
import json
from types import SimpleNamespace
import time

import httpx
import pytest

import analysis_model_source as sources
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
import test_analysis_node_local_v4_phases as old
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_emlis_natural_reply_probe_http import probe

PROFILE = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_PROFILE
ALIAS = sources.SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL


def prepared():
    original = old.prepared()
    return app.prepare_semantic_map(OWNER, json.loads(original.source_snapshot_json), prompt_version=PROFILE)


def prefixed(values):
    plan, bodies, relations = deepcopy(values)
    for node in plan['nodes']:
        for index, roots in enumerate(node['units'], 1):
            units = bodies['nodes'][node['node_id']]['units']
            key = 'u' + str(index)
            units[key] = dict(assigned_evidence={
                'e' + str(i): dict(source_quote=e['quote'], source_field=e['field'])
                for i, e in enumerate(roots['evidence'], 1)}, **units[key])
    return plan, bodies, relations


def artifact(p, values=None):
    value = old.artifact(p, prefixed(old.phase_packets(p)) if values is None else values)
    value['schema_version'] = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_SCHEMA
    return value


def test_forced_root_prefix_precedes_prose_and_survives_private_raw_only():
    p = prepared()
    values = prefixed(old.phase_packets(p))
    plan, bodies, _ = values
    messages = [p.messages(), core.semantic_node_local_v4_messages(p, 'NODES', plan=plan),
        core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)]
    schema = probe.semantic_output_schema(messages[1])
    unit = schema['properties']['nodes']['properties']['n1']['properties']['units']['properties']['u1']
    assert list(unit['properties']) == ['assigned_evidence', 'source_mode', 'fact', 'unknowns']
    assert unit['properties']['assigned_evidence']['properties']['e1']['properties']['source_quote']['enum'] == [
        plan['nodes'][0]['units'][0]['evidence'][0]['quote']]
    for value, selected in zip(values, messages, strict=True):
        assert json.loads(selected[1]['content'])['author_profile'] == PROFILE
        assert accepts(value, selected)
    value = artifact(p, values)
    joined = core.assemble_semantic_node_local_v4(p, value)
    assert all(set(u) == {'evidence', 'source_mode', 'fact', 'unknowns'}
        for n in joined['nodes'] for u in n['units'])
    result, coverage = app.build_semantic_map(p, old.response(p, value))
    private = result.private_evidence()['graph']['meaning_review']['node_local_plan']
    assert private['phase_artifact'] == value
    assert private['meaning_status'] == 'UNASSESSED'
    assert coverage['mapped_count'] == 2
    public = result.safe_projection(authenticated_owner_scope=OWNER)
    assert public['wire_kind'] == 'watashi.map.v3'
    assert 'assigned_evidence' not in json.dumps(public)


@pytest.mark.parametrize('change', ['quote', 'field', 'boolean_field', 'extra', 'missing', 'swap'])
def test_wrong_or_missing_assigned_roots_rejected_by_native_and_existing_admission(change):
    p = prepared()
    plan, bodies, _ = prefixed(old.phase_packets(p))
    selected = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    unit = bodies['nodes']['n1']['units']['u1']
    if change == 'quote':
        unit['assigned_evidence']['e1']['source_quote'] = '書かれていない原文。'
    elif change == 'field':
        unit['assigned_evidence']['e1']['source_field'] = 2
    elif change == 'boolean_field':
        unit['assigned_evidence']['e1']['source_field'] = True
    elif change == 'extra':
        unit['assigned_evidence']['e2'] = deepcopy(unit['assigned_evidence']['e1'])
    elif change == 'missing':
        del unit['assigned_evidence']
    else:
        unit['assigned_evidence'] = deepcopy(bodies['nodes']['n2']['units']['u1']['assigned_evidence'])
    assert not accepts(bodies, selected)
    with pytest.raises(core.AnalysisSemanticMapError, match='nodes_invalid'):
        core.semantic_node_local_v4_nodes(p, plan, bodies)


def test_borrowed_fact_is_not_automatically_certified_or_repaired_by_prefix():
    p = prepared()
    values = list(prefixed(old.phase_packets(p)))
    # The prefix remains exact, while free prose is intentionally wrong.
    values[1]['nodes']['n1']['units']['u1']['fact'] = '妹は椅子を直しました。'
    values[2]['nodes_sha256'] = core.semantic_map_hash(core._semantic_v4_join(*values[:2]))
    value = artifact(p, values)
    result, _ = app.build_semantic_map(p, old.response(p, value))
    review = result.private_evidence()['graph']['meaning_review']['node_local_plan']
    assert review['meaning_status'] == 'UNASSESSED'
    assert review['full_source_semantic_coverage'] is False
    assert review['phase_artifact']['phases'][1]['raw'] == value['phases'][1]['raw']


def test_multiple_assigned_roots_are_forced_without_splitting_the_unit():
    p = prepared()
    values = list(deepcopy(old.phase_packets(p)))
    roots = values[0]['nodes'][0]['units'][0]['evidence']
    roots.append(dict(quote='まだ送っていない。', field=1))
    values[1]['plan_sha256'] = core.semantic_map_hash(values[0])
    values = list(prefixed(values))
    values[2]['nodes_sha256'] = core.semantic_map_hash(core._semantic_v4_join(*values[:2]))
    selected = core.semantic_node_local_v4_messages(p, 'NODES', plan=values[0])
    assert accepts(values[1], selected)
    assert core.semantic_node_local_v4_nodes(p, *values[:2]) is values[1]
    assert len(core._semantic_v4_join(*values[:2])[0]['units']) == 1
    changed = deepcopy(values[1])
    del changed['nodes']['n1']['units']['u1']['assigned_evidence']['e2']
    assert not accepts(changed, selected)


@pytest.mark.parametrize('alias,bound_marker,status', [
    (ALIAS, PROFILE, 200), (ALIAS, None, 400),
    (sources.SEMANTIC_NODE_LOCAL_V4_MODEL, PROFILE, 400),
    (ALIAS, 'unknown-profile', 400),
])
def test_native_exact_alias_marker_pair_and_actual_phase_usage(alias, bound_marker, status):
    p = prepared() if bound_marker is not None else old.prepared()
    selected = deepcopy(p.messages())
    material = json.loads(selected[1]['content'])
    if bound_marker is not None:
        material['author_profile'] = bound_marker
    selected[1]['content'] = json.dumps(material, ensure_ascii=False)
    calls = []
    def generate(messages, end, *, profile=None, output_tokens=None):
        assert 120 < end - time.monotonic() <= 123
        calls.append((profile, output_tokens))
        return json.dumps(old.phase_packets(p)[0]), 'stop', dict(completion_tokens=99)
    handler_type = probe.make_handler(generate, api_key='synthetic-local-key',
        model_name=sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, event_plan_model=alias,
        deadline=time.monotonic() + 200, request_seconds=210, max_requests=1, max_new_tokens=4096)
    body = dict(model=alias, messages=selected, temperature=0, max_tokens=4000,
        generation_seconds=123, stream=False, chat_template_kwargs={'enable_thinking':False})
    raw = json.dumps(body).encode()
    handler = handler_type.__new__(handler_type)
    handler.path = '/v1/chat/completions'
    handler.headers = {'Authorization':'Bearer synthetic-local-key', 'Content-Length':str(len(raw))}
    handler.rfile = BytesIO(raw)
    handler.connection = SimpleNamespace(settimeout=lambda n: None)
    replies = []
    handler.reply = lambda code, value: replies.append((code, value))
    handler.do_POST()
    assert replies[0][0] == status
    if status == 200:
        assert calls == [('event_plan', 4000)]
        assert replies[0][1]['usage']['completion_tokens'] == 99
    else:
        assert calls == []


def test_profile_and_outer_schema_prevent_old_raw_rebinding():
    new, prior = prepared(), old.prepared()
    assert new.request_ref != prior.request_ref
    assert new.fields == prior.fields and new.frozen == prior.frozen
    assert new.source_guard == prior.source_guard
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(new, old.artifact(prior))
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(prior, artifact(new))


@pytest.mark.parametrize('failure', [None, 'length', 'HTTP503', 'wrong_model', 'missing_usage'])
def test_bound_transport_keeps_three_calls_shared_budget_and_failure_stop(failure):
    p, calls = prepared(), []
    values = prefixed(old.phase_packets(p))
    def handler(request):
        body = json.loads(request.content)
        index = len(calls)
        calls.append(body)
        assert body['model'] == ALIAS and body['max_tokens'] == 4096 - 100 * index
        assert 0 < body['generation_seconds'] <= 210
        assert json.loads(body['messages'][1]['content'])['author_profile'] == PROFILE
        failed = failure is not None and index == 1
        return httpx.Response(503 if failed and failure == 'HTTP503' else 200, json=dict(
            model='wrong' if failed and failure == 'wrong_model' else ALIAS,
            usage={} if failed and failure == 'missing_usage' else dict(completion_tokens=100),
            choices=[dict(finish_reason='length' if failed and failure == 'length' else 'stop',
                message=dict(role='assistant', content=json.dumps(values[index], ensure_ascii=False)))]))
    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint=old.ENDPOINT, model=ALIAS,
        api_key='synthetic-local-key', transport=httpx.MockTransport(handler), semantic_prompt_version=PROFILE)
    if failure:
        with pytest.raises(RuntimeError):
            asyncio.run(source(p))
        assert len(calls) == 2
    else:
        response = asyncio.run(source(p))
        assert len(calls) == 3 and json.loads(response.raw)['schema_version'] == core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_SCHEMA
        assert core.assemble_semantic_node_local_v4(p, json.loads(response.raw))


def test_existing_deadline_cancellation_and_usage_guards_apply_to_bound_profile(monkeypatch):
    monkeypatch.setattr(old, 'PROFILE', PROFILE)
    monkeypatch.setattr(old, 'ALIAS', ALIAS)
    monkeypatch.setattr(old, 'phase_packets', lambda p: prefixed(original_packets(p)))
    old.test_absolute_deadline_cancels_slow_continuous_stream(monkeypatch)
    old.test_cancellation_propagates_without_next_phase_or_retry()
    old.test_exhausted_total_token_budget_never_starts_second_generation()
    for usage in (None, 0, -1, True, 4097):
        old.test_invalid_phase_token_usage_stops_before_next_phase(usage)


original_packets = old.phase_packets
original_generated = old.generated_phase_values


def test_correction_cohort_full_explanation_and_stage_lineage(monkeypatch):
    monkeypatch.setattr(old, 'PROFILE', PROFILE)
    monkeypatch.setattr(old, 'generated_phase_values', lambda p: prefixed(original_generated(p)))
    original_artifact = old.artifact
    def bound_artifact(p, values=None):
        packet = original_artifact(p, values)
        packet['schema_version'] = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_SCHEMA
        return packet
    monkeypatch.setattr(old, 'artifact', bound_artifact)
    old.test_correction_cohort_full_explanation_and_leaf_merge_lineage_are_preserved(monkeypatch)
