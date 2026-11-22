"""Source attribution in the ordinary diagram, full-text projection and decoder."""
import json
from copy import deepcopy

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v11_display import map_stages


def stages(*notes):
    old, plan, bodies = map_stages(*notes)
    prepared = maps.prepare_semantic_map(OWNER, json.loads(old.source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V13_PROFILE)
    return old, prepared, plan, bodies


def combined(plan, bodies):
    first, second = plan['nodes'][:2]
    first['units'].extend(second['units'])
    plan['nodes'].remove(second)
    merged = bodies['nodes'].pop('n2')['units']['u1']
    merged['evidence_ref'] = 'n1.u2'
    bodies['nodes']['n1']['units']['u2'] = merged
    bodies['plan_sha256'] = core.semantic_map_hash(plan)


def wire(prepared, plan, canonical):
    compact = deepcopy(canonical)
    compact['plan_sha256'] = core.semantic_map_hash(['analysis.node-facts.v1', 'NODES', prepared.request_ref, plan])
    for (node, unit, key), (ordinal, quote) in core._semantic_node_fact_sources(plan, json.loads(prepared.material_json)).items():
        assert compact['nodes'][node]['units'][unit]['fact_parts'][key] == quote
        compact['nodes'][node]['units'][unit]['fact_parts'][key] = ordinal
    return compact


def test_natural_title_keeps_both_records_separate_without_requiring_source_concatenation():
    notes = ('私はまだ申し込んでいない。', '翌日の窓口で受付が済んだ。')
    old, prepared, plan, bodies = stages(*notes)
    combined(plan, bodies)
    node = bodies['nodes']['n1']
    messages = core.semantic_node_local_v4_messages(prepared, 'NODES', plan=plan)
    for one_day in (notes[1], notes[1][:-1]):
        node['title'] = one_day
        raw = wire(prepared, plan, bodies)
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw)
        assert not accepts(raw, messages)
    node['title'] = notes[1]
    assert accepts(bodies, core.semantic_node_local_v4_messages(old, 'NODES', plan=plan))
    node['title'] = '申し込みを保留してから窓口で受け付けるまで'
    raw = wire(prepared, plan, bodies)
    assert accepts(raw, messages)
    assert core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw) == bodies


def test_corroboration_and_supplement_do_not_change_a_facts_source_clock():
    _, prepared, plan, _ = stages('私は窓を開けた。', 'あとで窓を開けた時のことを説明した。')
    first, second = [n['units'][0] for n in plan['nodes']]
    mixed = dict(evidence=first['evidence'] + second['evidence'])
    material = json.loads(prepared.material_json)
    assert choices.separate_record_labels(material, [first, mixed]) == ()
    assert choices.one_sided_source_titles(material, [first, mixed]) is None
    # A corroborated third fact does not turn two unrelated, single-owner facts into one.
    assert second['evidence'][0]['quote'] in choices.one_sided_source_titles(material, [first, second, mixed])
    material['fields'][0]['source_role'] = 'USER_ANALYSIS_MAP_CORRECTION'
    assert choices.separate_record_labels(material, [first, second]) == ()
    assert choices.one_sided_source_titles(material, [first, second]) is None


@pytest.mark.parametrize('second,expected', [
    ('2026-11-14T15:10:00Z', ('11月14日の記録', '11月15日の記録')),
    ('2026-11-14T01:10:00Z', ('11月14日 09:01の記録', '11月14日 10:10の記録')),
    ('2026-11-14T09:01:00+09:00', ('記録1（11月14日 09:01）', '記録2（11月14日 09:01）')),
    ('2026-11-14T00:01:54Z', ('記録1（11月14日 09:01）', '記録2（11月14日 09:01）')),
    ('2027-11-13T15:01:00Z', ('2026年11月14日の記録', '2027年11月14日の記録')),
])
def test_labels_identify_physical_records_and_jst_dates(second, expected):
    _, prepared, plan, _ = stages('前日の出来事を記録した。', '来週行うことを書き留めた。')
    material = json.loads(prepared.material_json)
    material['records'][0]['recorded_at'] = '2026-11-14T00:01:00'
    material['records'][1]['recorded_at'] = second
    units = [n['units'][0] for n in plan['nodes']]
    assert choices.separate_record_labels(material, units) == expected
    assert choices.separate_record_labels(material, units[::-1]) == expected[::-1]


def test_one_record_or_identical_statement_in_both_records_remains_admissible():
    quote = '同じ条件で測定した。'
    _, prepared, plan, bodies = stages(quote, quote)
    messages = core.semantic_node_local_v4_messages(prepared, 'NODES', plan=plan)
    assert accepts(wire(prepared, plan, bodies), messages)
    combined(plan, bodies)
    assert choices.one_sided_source_titles(json.loads(prepared.material_json), plan['nodes'][0]['units']) == []
    assert core.admit_semantic_node_local_v4_nodes_response(prepared, plan, wire(prepared, plan, bodies)) == bodies


def test_overview_uses_only_its_selected_nodes():
    notes = ('私は配布用の用紙を持ち帰った。', '後日、記入した用紙を受付に提出した。')
    _, prepared, plan, bodies = stages(*notes)
    for node in bodies['nodes'].values():
        node['units']['u1']['unknowns'] = []
    joined = core._semantic_v4_join(plan, bodies)
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(joined),
               qualification_review={}, edges=[], overview=dict(node_refs=['n2'], title=notes[1]))
    messages = core.semantic_node_local_v4_messages(prepared, 'RELATIONS', plan=plan, nodes=bodies)
    assert accepts(rel, messages)
    assert core.semantic_node_local_v4_relations(prepared, plan, bodies, rel)['overview'] == rel['overview']
    rel['overview']['node_refs'] = ['n2', 'n1']
    assert not accepts(rel, messages)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(prepared, plan, bodies, rel)
    rel['overview']['title'] = '用紙の持ち帰りと後日の提出'
    assert accepts(rel, messages)
    assert core.semantic_node_local_v4_relations(prepared, plan, bodies, rel)['overview'] == rel['overview']


def test_graph_summary_explanation_and_edge_keep_each_selected_facts_own_record():
    from dataclasses import replace
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler

    notes = ('昨日提出する予定だった資料を確かめた。', '来週提出するための準備をした。', '以前提出した資料を読み返した。')
    _, prepared, plan, bodies = stages(*notes)
    nodes = core._semantic_v4_join(plan, bodies)
    nodes[0]['units'].extend(nodes.pop(1)['units'])
    for n in nodes:
        del n['node_id']
    nodes[0]['title'] = '資料の確認と次回提出の準備'
    nodes[0]['meaning'] = '今後の提出に向けて準備したことが分かります。'
    material = json.loads(prepared.material_json)
    labels = choices.separate_record_labels(material, nodes[0]['units'])
    endpoints = [nodes[0]['units'][1], nodes[1]['units'][0]]
    edge_labels = choices.separate_record_labels(material, endpoints)
    assert len(labels) == len(edge_labels) == 2
    edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u2', 'to_unit': 'n2.u1',
            'relation_kind': 'CONTEXT_CONTRAST', 'label': '資料の準備と読み返し'}
    packet = dict(schema_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_SCHEMA, nodes=nodes, edges=[edge],
                  overview=dict(node_refs=['n1', 'n2'], title='資料の準備から確認まで'))
    render = intent_compiler._expand_analysis_semantic_node_local_v3
    prepared = replace(prepared, prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE)
    ordinary = render(prepared, packet, fact_endpoints=True)
    dated = render(prepared, packet, fact_endpoints=True, mark_record_ownership=True)
    for label, fact in zip(labels, notes[:2], strict=True):
        assert label + '：' + fact in dated['nodes'][0]['summary']
        assert label + '：' + fact in dated['nodes'][0]['explanation']
        assert label in dated['overview']['summary']
    assert dated['nodes'][1] == ordinary['nodes'][1]
    assert dated['edges'][0]['unit_evidence'] == ordinary['edges'][0]['unit_evidence']
    assert dated['edges'][0]['explanation'] == '\n'.join(
        label + '：' + unit['fact'] for label, unit in zip(edge_labels, endpoints, strict=True))
