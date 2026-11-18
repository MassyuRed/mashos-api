"""Opt-in authored facts and the two actual units supporting a relationship."""
import json

import pytest

import analysis_if_model_source as if_sources
import analysis_model_source as sources
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_event_plan_model_alias import environment
from test_analysis_node_local_native_profile import accepts
import test_analysis_node_local_v4_phases as phases
from test_emlis_natural_reply_probe_http import probe


def authored():
    snapshot = source_snapshot(2)
    first, second = (m['original'] for m in snapshot['members'])
    first.update(memo='初日は陶器の見本を持った。見本は買わなかった。', memo_action='')
    second.update(memo='翌週、別の鉢を注文した。追加で注文するつもりはない。', memo_action='')
    prepared = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE)
    def roots(*quotes):
        return dict(evidence=[dict(quote=quote, field=field) for field, quote in quotes])
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[
        dict(node_id='n1', units=[roots((1, '初日は陶器の見本を持った。'), (1, '見本は買わなかった。')),
            roots((2, '翌週、別の鉢を注文した。'))]),
        dict(node_id='n2', units=[roots((2, '追加で注文するつもりはない。'))])])
    def unit(ref, mode, *parts):
        return dict(evidence_ref=ref, source_mode=mode,
            fact_parts={f'e{i}': part for i, part in enumerate(parts, 1)}, unknowns=[])
    nodes = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256=core.semantic_map_hash(plan),
        nodes=dict(n1=dict(units=dict(u1=unit('n1.u1', 'RECORDED', '初日は陶器の見本を手に取り、', '購入しませんでした。'),
            u2=unit('n1.u2', 'RECORDED', '翌週、本人は別の鉢を注文しました。')),
            node_kind='CHOICE_OUTPUT', perspective='SELF', title='見本の試用と別の鉢の注文', meaning=''),
            n2=dict(units=dict(u1=unit('n2.u1', 'PERSON_WISH', '追加で注文するつもりはありません。')),
            node_kind='SELF_POSITION', perspective='SELF', title='追加注文をしない意向', meaning='')))
    registry = core._semantic_v4_join(plan, nodes)
    edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u2', 'to_unit': 'n2.u1',
        'label': '別の鉢は注文したが、追加注文の意向はない', 'relation_kind': 'CONTEXT_CONTRAST'}
    relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(registry),
        edges=[edge], overview=dict(node_refs=['n1', 'n2'], title='見本を買わず、別の鉢を注文。追加の意向はない'))
    return prepared, plan, nodes, relations


def test_actual_output_and_private_evidence_use_only_chosen_endpoint_units():
    p, plan, nodes, rel = authored()
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (plan, nodes, rel)):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=nodes)
        assert accepts(value, messages)
    assert json.loads(messages[1]['content'])['relation_units']['n1.u2'] == '翌週、本人は別の鉢を注文しました。'
    artifact = phases.artifact(p, (plan, nodes, rel))
    artifact['schema_version'] = core.SEMANTIC_MAP_OCCURRENCE_V6_SCHEMA
    result, coverage = app.build_semantic_map(p, phases.response(p, artifact))
    graph = result.safe_projection(authenticated_owner_scope=OWNER)
    assert coverage['mapped_count'] == 2
    assert graph['nodes'][0]['explanation'] == '初日は陶器の見本を手に取り、購入しませんでした。\n翌週、本人は別の鉢を注文しました。'
    assert graph['edges'][0]['explanation'] == '翌週、本人は別の鉢を注文しました。\n追加で注文するつもりはありません。'
    assert graph['edges'][0]['label'] == rel['edges'][0]['label']
    private = result.private_evidence()['graph']['meaning_review']['node_local_plan']
    assert private['edge_unit_closures'][0]['unit_refs'] == ['n1.u2', 'n2.u1']
    assert private['phase_artifact'] == artifact


@pytest.mark.parametrize('bad_parts', [{'e1': '一段だけ。'}, {'e2': '飛ばした。', 'e3': '多い。'},
    {'e1': '正しい。', 'e2': ''}, {'e1': '長' * 161, 'e2': '短い。'}])
def test_native_and_consumer_require_one_bounded_contribution_per_plan_quote(bad_parts):
    p, plan, nodes, _ = authored()
    nodes['nodes']['n1']['units']['u1']['fact_parts'] = bad_parts
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    assert not accepts(nodes, messages)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_nodes(p, plan, nodes)


@pytest.mark.parametrize('change', [{'from_unit':'n1.u3'}, {'to_unit':'n1.u1'},
    {'from_unit':'n1.u2', 'label':'見本の試用と別の鉢の注文'}, {'label':'追加注文をしない意向'}])
def test_native_and_consumer_bind_both_units_and_exclude_endpoint_title_only(change):
    p, plan, nodes, rel = authored()
    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    rel['edges'][0].update(change)
    assert not accepts(rel, messages)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(p, plan, nodes, rel)


def test_independent_units_may_remain_unconnected_and_shared_title_prefix_is_valid():
    p, plan, nodes, rel = authored()
    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    rel['edges'][0]['label'] = nodes['nodes']['n2']['title'] + 'と、先に済ませた別の鉢の注文'
    assert accepts(rel, messages)
    assert core.semantic_node_local_v4_relations(p, plan, nodes, rel)['edges'] == rel['edges']
    rel['edges'] = []
    assert accepts(rel, messages)
    assert core.semantic_node_local_v4_relations(p, plan, nodes, rel)['edges'] == []


def test_opt_in_map_keeps_previous_if_model(monkeypatch):
    environment(monkeypatch, model=sources.SEMANTIC_OCCURRENCE_V6_MODEL)
    assert sources.application_analysis_model_source().prompt_version == core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE
    assert if_sources.application_analysis_if_model_source().model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL


@pytest.mark.parametrize('long_length', [115, 228])
def test_four_sources_preserve_room_for_long_qualified_statement(long_length):
    snapshot = source_snapshot(1)
    quotes = ['行った。', '見た。', '読んだ。', '甲' * (long_length - 1) + '。']
    snapshot['members'][0]['original'].update(memo=''.join(quotes), memo_action='')
    p = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE)
    evidence = [dict(quote=q, field=1) for q in quotes]
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'),
        nodes=[dict(node_id='n1', units=[dict(evidence=evidence)])])
    limits = core._semantic_fact_part_limits(evidence)
    assert sum(limits) == 160 and limits[-1] >= min(long_length, 145)
    if sum(map(len, quotes)) <= 160:
        assert all(len(q) <= limit for q, limit in zip(quotes, limits))
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    unit_schema = probe.semantic_output_schema(messages)['properties']['nodes']['properties']['n1']
    size = unit_schema['properties']['units']['properties']['u1']['properties']['fact_parts']['properties']
    assert [size[f'e{i}']['maxLength'] for i in range(1, 5)] == limits


@pytest.mark.parametrize('leaf', [False, True])
def test_fictional_demonstration_uses_real_protocol_for_its_own_sources(leaf):
    def sample(phase):
        lesson = core._semantic_occurrence_v6_example(phase, leaf=leaf)
        inputs, output = lesson.split('例入力=', 1)[1].split('\n例出力=')
        return json.loads(inputs), json.loads(output.split('\n例はここまで。')[0])
    context, plan = sample('PLAN')
    snapshot = source_snapshot(len(context['fields']))
    for member, field_text in zip(snapshot['members'], context['fields'].values()):
        member['original'].update(memo=field_text, memo_action='')
    p = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE)
    node_input, nodes = sample('NODES')
    relation_input, relations = sample('RELATIONS')
    assert node_input['plan'] == plan
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (plan, nodes, relations)):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=nodes)
        assert accepts(value, messages)
    assert relation_input['relation_units'] == json.loads(messages[1]['content'])['relation_units']
    assert bool(relations['edges']) != leaf
    assert core.semantic_node_local_v4_relations(p, plan, nodes, relations)['edges'] == relations['edges']


def overview_with_opposite_events(profile, title, selected, *, history_leaf=False):
    statements = ('私は資料を調べなかった。', '私は資料を調べた。')
    snapshot = source_snapshot(2)
    for member, text in zip(snapshot['members'], statements):
        member['original'].update(memo=text, memo_action='')
    prepared = app.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)
    if history_leaf:
        refs = tuple(member.saved_record_ref for member in prepared.frozen.members)
        prepared = core.prepare_semantic_leaf(prepared, refs)
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[])
    node_map = {}
    for number, text in enumerate(statements, 1):
        ref = f'n{number}'
        plan['nodes'].append(dict(node_id=ref, units=[dict(evidence=[dict(field=number, quote=text)])]))
        unit = dict(evidence_ref=ref + '.u1', source_mode='RECORDED', unknowns=[])
        if profile == core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE:
            unit['fact_parts'] = dict(e1=text)
        else:
            unit['fact'] = text
        node_map[ref] = dict(units=dict(u1=unit), node_kind='CHOICE_OUTPUT',
            perspective='SELF', title=text, meaning='')
    nodes = dict(schema_version=core._semantic_v4_schema('NODES'),
        plan_sha256=core.semantic_map_hash(plan), nodes=node_map)
    relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'), edges=[],
        nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan, nodes)),
        overview=dict(node_refs=selected, title=title))
    packet = phases.artifact(prepared, (plan, nodes, relations))
    packet['schema_version'] = core.semantic_node_local_v4_artifact_schema(prepared)
    reply = phases.response(prepared, packet)
    if history_leaf:
        graph = core.build_semantic_stage(prepared, reply)
        return json.loads(graph.meaning_review_json)['overview']['fields']
    artifact, _ = app.build_semantic_map(prepared, reply)
    return artifact.private_evidence()['graph']['meaning_review']['overview']['fields']


@pytest.mark.parametrize('history_leaf', [False, True])
def test_overview_cannot_borrow_opposite_event_from_unselected_node(history_leaf):
    profile = core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE
    with pytest.raises((core.AnalysisSemanticMapError, app.SemanticMapError), match='analysis_semantic_meaning_conflict'):
        overview_with_opposite_events(profile, '私は資料を調べた。', ['n1'], history_leaf=history_leaf)
    fields = overview_with_opposite_events(profile, '私は資料を調べた。', ['n2'], history_leaf=history_leaf)
    assert all(row['source_claims'] == ['c2'] and row['verdict'] == 'NO_CONFLICT_IN_CHECKED_SCOPE' for row in fields)


@pytest.mark.parametrize('profile,selected,title,claims', [
    (core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE, ['n1', 'n2'], '私は資料を調べた。', ['c1', 'c2']),
    (core.SEMANTIC_MAP_OCCURRENCE_V6_PROFILE, ['n1'], 'このときは資料の確認を見送った', []),
    (core.SEMANTIC_MAP_OCCURRENCE_V5_PROFILE, ['n1'], '私は資料を調べた。', ['c1', 'c2']),
])
def test_ambiguous_sources_unparsed_paraphrases_and_prior_profile_keep_existing_verdict(profile, selected, title, claims):
    fields = overview_with_opposite_events(profile, title, selected)
    row = next(field for field in fields if field['field'] == 'title')
    assert row['verdict'] == 'UNASSESSED' and row['source_claims'] == claims


def test_expanded_v6_material_alone_has_no_overview_selection():
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler
    prepared, plan, nodes, relations = authored()
    packet = phases.artifact(prepared, (plan, nodes, relations))
    packet['schema_version'] = core.SEMANTIC_MAP_OCCURRENCE_V6_SCHEMA
    expanded = intent_compiler.expand_analysis_semantic_event_plan(prepared, packet)
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_node_local_v4_lineage_invalid'):
        intent_compiler._compile_analysis_semantic_map_v2(prepared, expanded, response_sha256='a' * 64)
