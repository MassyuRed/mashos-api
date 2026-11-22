"""Mixed original source records retain their own clocks without dating one corroborated fact."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, semantic_admission as core
from test_analysis_v13_separate_record_titles import stages


def fact(roots):
    return dict(evidence=roots, source_mode='RECORDED', fact=''.join(r['quote'] for r in roots), unknowns=[])


def test_same_unit_mixed_originals_are_readable_in_nodes_overview_and_edge_endpoints():
    quotes = ['前の日、作業場で紙を乾かした。', '今朝、運搬箱を閉じた。', '数日後、箱の数を記録した。']
    _, prepared, plan, bodies = stages(*quotes)
    material = json.loads(prepared.material_json)
    source = [n['units'][0]['evidence'][0] for n in plan['nodes']]
    nodes = core._semantic_v4_join(plan, bodies)
    nodes[0]['units'] = [fact(source[:2])]
    nodes.pop(1)
    for node in nodes:
        del node['node_id']
    edge = {'from':'n1', 'to':'n2', 'from_unit':'n1.u1', 'to_unit':'n2.u1',
            'label':'保管と数の確認', 'relation_kind':'CONTEXT_CONTRAST'}
    packet = dict(schema_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_SCHEMA, nodes=nodes, edges=[edge],
                  overview=dict(node_refs=['n1','n2'], title='保管と確認の記録'))
    original = deepcopy(packet)
    prepared = replace(prepared, prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE)
    render = intent_compiler._expand_analysis_semantic_node_local_v3
    previous = render(prepared, packet, fact_endpoints=True, mark_record_ownership=True)
    dated = render(prepared, packet, fact_endpoints=True, mark_record_ownership=True,
                   fixed_record_units={'n1.u1','n2.u1'})
    labels = choices.separate_record_labels(material, [fact([r]) for r in source[:2]])
    for label, quote in zip(labels, quotes, strict=False):
        assert label + '：' + quote in dated['nodes'][0]['summary']
        assert label + '：' + quote in dated['nodes'][0]['explanation']
        assert label in dated['overview']['summary']
    assert dated['edges'][0]['explanation'] != previous['edges'][0]['explanation']
    assert quotes[0] in dated['edges'][0]['explanation'] and quotes[2] in dated['edges'][0]['explanation']
    assert dated['edges'][0]['unit_evidence'] == previous['edges'][0]['unit_evidence']
    assert dated['nodes'][1] == previous['nodes'][1] and original == packet


@pytest.mark.parametrize('case', ['single','free','corroborating','same_quote','supplement','correction'])
def test_single_record_and_joint_authored_facts_never_receive_another_sources_clock(case):
    _, prepared, plan, _ = stages('私は箱を運んだ。', '昨日の運搬について書き足した。')
    m = json.loads(prepared.material_json)
    roots = [n['units'][0]['evidence'][0] for n in plan['nodes']]
    if case=='single':
        roots = roots[:1]
    elif case=='same_quote':
        roots[1]['quote'] = roots[0]['quote']
    elif case in ('correction','supplement'):
        field = next(f for f in m['fields'] if f['field']==roots[1]['field'])
        field['source_role'] = 'USER_ANALYSIS_MAP_CORRECTION' if case=='correction' else 'SUPPLEMENTAL_ANSWER'
    u = fact(roots)
    if case=='corroborating':
        u['fact'] = '箱を運んだという一つの出来事が、続く記録にも書かれている。'
    assert choices.mixed_record_facts(m, [u], [case!='free']) == ((), [])


def test_three_records_repeated_owner_preserves_order_and_uses_same_day_disambiguation():
    _, p, plan, _ = stages('見本を封筒に入れた。', '別の棚を調べた。', '受付に声を掛けた。')
    m = json.loads(p.material_json)
    for row, stamp in zip(m['records'], ('2026-01-01T00:00Z','2026-01-01T00:00Z','2027-02-01T00:00Z'),strict=True):
        row['recorded_at']=stamp
    a,b,c = [n['units'][0]['evidence'][0] for n in plan['nodes']]
    unit = fact([a,b,c,dict(a,quote='別の紙片も入れた。')])
    labels, shown = choices.mixed_record_facts(m,[unit],[True])
    assert labels == ('記録1（2026年1月1日 09:00）','記録2（2026年1月1日 09:00）','2027年2月1日の記録')
    assert shown == [label+'：'+r['quote'] for label,r in zip([*labels,labels[0]], unit['evidence'],strict=True)]


def test_normal_three_phase_map_and_text_restore_each_quoted_source_fragment():
    import hashlib
    import analysis_semantic_map as maps
    from test_analysis_cumulative import OWNER
    from test_analysis_node_local_v4_phases import response
    from test_analysis_v13_separate_record_titles import wire

    notes = ('昨日は照合を見送った。', '別の日に担当者から集計結果を聞いた。')
    _, previous, plan, bodies = stages(*notes)
    p = maps.prepare_semantic_map(OWNER, json.loads(previous.source_snapshot_json),
                                  prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V14_PROFILE)
    n1, n2 = plan['nodes']
    roots = n1['units'][0]['evidence']
    roots.extend(n2['units'][0]['evidence'])
    plan['nodes'].pop()
    del bodies['nodes']['n2']
    u = bodies['nodes']['n1']['units']['u1']
    u['unknowns'] = []
    u['fact_parts'] = {core._semantic_fact_part_key(roots, i): r['quote'] for i,r in enumerate(roots)}
    bodies['plan_sha256'] = core.semantic_map_hash(plan)
    wire_plan = deepcopy(plan)
    material = json.loads(p.messages()[1]['content'])
    _, table, _ = choices.restore_view(material)
    aliases = {(field, quote): cue for (field,cue),quote in table.items()}
    for r in wire_plan['nodes'][0]['units'][0]['evidence']:
        r['quote'] = aliases[r['field'], r['quote']]
    wire_plan['source_choices_sha256'] = material['source_choices_sha256']
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'),
               nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan,bodies)), qualification_review={},
               edges=[], overview=dict(node_refs=['n1'], title=bodies['nodes']['n1']['title']))
    rows=[]
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (wire_plan,wire(p,plan,bodies),rel), strict=True):
        source = core.semantic_node_local_v4_messages(p, phase, plan=plan if phase!='PLAN' else None,
                                                      nodes=bodies if phase=='RELATIONS' else None)
        raw = core.semantic_map_canonical(value)
        rows.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(source), raw=raw,
                         raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop',completion_tokens=100))
    retained = dict(schema_version=core.semantic_node_local_v4_artifact_schema(p), phases=rows)
    artifact, _ = maps.build_semantic_map(p, response(p,retained))
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    full = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert graph['nodes'][0]['evidence_badge_count'] == 2
    for label,q in zip(choices.separate_record_labels(json.loads(p.material_json), [fact([r]) for r in roots]),notes,strict=True):
        assert label+'：'+q in full and label+'：'+q in graph['nodes'][0]['explanation']
