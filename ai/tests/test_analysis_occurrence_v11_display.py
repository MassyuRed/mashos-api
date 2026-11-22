"""Independently bind compact MAP display choices to admitted source sentences."""

from copy import deepcopy
import json

import pytest

import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts
from test_emlis_natural_reply_probe_http import probe


def map_stages(*sentences):
    snapshot = source_snapshot(len(sentences))
    for member, sentence in zip(snapshot['members'], sentences, strict=True):
        member['original'].update(memo=sentence, memo_action='')
    p = maps.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V11_PROFILE)
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[])
    nodes = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256='', nodes={})
    for field in json.loads(p.material_json)['fields']:
        node_id = 'n' + str(len(plan['nodes']) + 1)
        number, quote = field['field'], field['text']
        roots = [dict(quote=quote, field=number)]
        plan['nodes'].append(dict(node_id=node_id, units=[dict(evidence=roots)]))
        unit = dict(evidence_ref=node_id + '.u1', source_mode='RECORDED',
            fact_parts={core._semantic_fact_part_key(roots, 0): quote},
            unknowns=[dict(source_quote=quote, source_field=number)])
        nodes['nodes'][node_id] = dict(units={'u1': unit}, node_kind='STATE_CONTEXT',
            perspective='SELF', title=quote, meaning='')
    nodes['plan_sha256'] = core.semantic_map_hash(plan)
    return p, plan, nodes


def test_display_preserves_outer_report_and_status_while_meaning_remains_authored():
    report = '担当者から「新しい箱を開けた」と連絡が来た。'
    p, plan, nodes = map_stages(report, 'そろえた部品をまだ取り付けていない。')
    nodes['nodes']['n1']['meaning'] = '本人が知ったのは、担当者から知らせがあった時点です。'
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    assert accepts(nodes, messages)
    assert core.semantic_node_local_v4_nodes(p, plan, nodes) == nodes
    for key in ['title', 'fact_parts']:
        wrong = deepcopy(nodes)
        if key == 'title':
            wrong['nodes']['n1']['title'] = '新しい箱を開けた。'
        else:
            parts = wrong['nodes']['n2']['units']['u1']['fact_parts']
            parts[next(iter(parts))] = 'そろえた部品は取り付けない。'
        assert not accepts(wrong, messages)
        with pytest.raises(core.AnalysisSemanticMapError):
            core.semantic_node_local_v4_nodes(p, plan, wrong)


def test_known_completed_action_and_unresolved_question_can_coexist_without_an_edge():
    p, plan, nodes = map_stages('私は会議を担当した。', '会場の鍵が誰に届いたかは聞いていない。')
    a, b = (n['units'][0]['evidence'][0] for n in plan['nodes'])
    joined = core._semantic_v4_join(plan, nodes)
    known, pending = core._semantic_qualification_candidates(joined, predicate_cues=True)
    assert known == 'q1/' + a['quote'][-8:] and pending == 'q2/' + b['quote'][-8:]
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'),
        nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan, nodes)),
        qualification_review={known: dict(status='STATED'), pending: dict(status='OPEN', source_quote=b['quote'])},
        edges=[], overview=dict(node_refs=['n1'], title='本人が会議を担当した'))
    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    material = json.loads(messages[1]['content'])
    assert list(material)[-1] == 'qualification_candidates'
    assert (a['field'], a['quote'][:-1]) in core._semantic_recorded_actions(material)
    assert accepts(rel, messages)
    joined = core.semantic_node_local_v4_relations(p, plan, nodes, rel)
    assert joined['nodes'][0]['units'][0]['unknowns'] == []
    assert joined['nodes'][1]['units'][0]['unknowns'] == [dict(source_quote=b['quote'], source_field=b['field'])]
    rel['qualification_review'][known] = dict(status='OPEN', source_quote=a['quote'])
    assert not accepts(rel, messages)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(p, plan, nodes, rel)


@pytest.mark.parametrize('field', [
    dict(field=1, text='中途で切った。', fragment_is_complete_field=False),
    dict(field=1, text='「中の文。'),
    dict(field=1, text='一度（別の語。小さな語）だけ聞いた。'),
    dict(field=1, text='同じ文。同じ文。'),
    dict(field=1, text='続きがまだある'),
])
def test_ambiguous_excerpt_preserves_authored_choices(field):
    material = dict(fields=[field])
    assert not core._semantic_display_sentences(material).get(1)
    assert core._semantic_display_sentences(material) == probe._semantic_display_sentences(material)
