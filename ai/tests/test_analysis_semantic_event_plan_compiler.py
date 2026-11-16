"""Source/contract tests for an unadopted reference author, not model quality."""
from copy import deepcopy
import json

import pytest

import analysis_semantic_map as application
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_semantic_map import OWNER, candidate, response, sample

PROFILE = 'semantic_map.event_plan.v1'
SCHEMA = 'cocolon.analysis.semantic_map.event_plan.model.v1'


def prepared():
    return application.prepare_semantic_map(OWNER, sample(), prompt_version=PROFILE)


def plan():
    return dict(schema_version=SCHEMA,
        events=[dict(evidence=[dict(quote='自分が納得して選びたい', field=1)],
            event_id='e1', fact='自分が納得して選びたい。', unknowns=[]),
            dict(evidence=[dict(quote='私は意見を言わなかった', field=3)],
            event_id='e2', fact='私は意見を言わなかった。', unknowns=['発言しなかった理由'])],
        readings=[dict(reading_id='r1', event_refs=['e1', 'e2'],
            meaning='本人の希望と、その場の発言とを見比べています。')],
        nodes=[dict(node_id='n1', node_kind='SELF_POSITION', perspective='SELF',
            title='選びたいという希望', event_refs=['e1'], reading_refs=[]),
            dict(node_id='n2', node_kind='CHOICE_OUTPUT', perspective='SELF',
            title='意見を言わなかった場面', event_refs=['e2'], reading_refs=[])],
        edges=[dict(**{'from':'n1', 'to':'n2'}, relation_kind='SELF_OUTSIDE_GAP',
            label='希望と発言', event_refs=['e1', 'e2'], reading_refs=['r1'])],
        overview=dict(title='希望と発言した範囲', event_refs=['e2', 'e1'], reading_refs=['r1']))


def compile_plan(value=None, material=None):
    return compiler.compile_analysis_semantic_map(prepared() if material is None else material,
        plan() if value is None else value, response_sha256='a' * 64)


def test_reference_realization_uses_authored_facts_in_selected_order_and_keeps_original_plan():
    authored = plan()
    original = deepcopy(authored)
    graph = compile_plan(authored)
    nodes, edges = json.loads(graph.nodes_json), json.loads(graph.edges_json)
    assert nodes[0]['summary'] == nodes[0]['explanation'] == authored['events'][0]['fact']
    assert nodes[1]['summary'] == nodes[1]['explanation'] == authored['events'][1]['fact']
    assert nodes[1]['unknowns'] == authored['events'][1]['unknowns']
    assert edges[0]['explanation'] == '\n'.join([authored['events'][0]['fact'],
        authored['events'][1]['fact'], authored['readings'][0]['meaning']])
    assert json.loads(graph.overview_json)['summary'] == '\n'.join([
        authored['events'][1]['fact'], authored['events'][0]['fact'], authored['readings'][0]['meaning']])
    assert graph.response_sha256 == 'a' * 64
    private = json.loads(graph.meaning_review_json)['event_plan']
    assert private['plan'] == original and private['meaning_status'] == 'UNASSESSED'
    assert authored == original
    authored['events'][0]['fact'] = 'mutated after compilation'
    assert json.loads(graph.meaning_review_json)['event_plan']['plan'] == original


def test_same_legacy_packet_produces_exactly_the_unchanged_legacy_graph():
    material = application.prepare_semantic_map(OWNER, sample())
    packet = candidate()
    direct = compiler._compile_analysis_semantic_map_v2(material, packet, response_sha256='b' * 64)
    wrapped = compiler.compile_analysis_semantic_map(material, packet, response_sha256='b' * 64)
    assert wrapped == direct
    assert compiler.expand_analysis_semantic_event_plan(material, packet) is packet


@pytest.mark.parametrize('new_profile', [False, True])
def test_new_private_contract_and_profile_cannot_be_silently_cross_admitted(new_profile):
    material = prepared() if new_profile else application.prepare_semantic_map(OWNER, sample())
    value = candidate() if new_profile else plan()
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_event_plan_profile_unbound'):
        compile_plan(value, material)


@pytest.mark.parametrize('mutate', [
    lambda p: p['nodes'][0].update(event_refs=['e9']),
    lambda p: p['nodes'][0].update(reading_refs=['r9']),
    lambda p: p['nodes'][0].update(event_refs=['e1', 'e1']),
    lambda p: p['nodes'][0].update(reading_refs=['r1']),
    lambda p: p['edges'][0].update(event_refs=['e1'], reading_refs=['r1']),
    lambda p: p['events'][0]['evidence'][0].update(field=3),
    lambda p: p['events'][0]['evidence'][0].update(quote='原文にない引用'),
    lambda p: p['overview'].update(event_refs=['e9']),
])
def test_dangling_duplicate_cross_scope_and_cross_field_references_are_rejected(mutate):
    value = plan()
    mutate(value)
    with pytest.raises(core.AnalysisSemanticMapError):
        compile_plan(value)


@pytest.mark.parametrize('kind', ['event', 'reading'])
def test_orphan_plan_content_is_rejected_instead_of_hidden(kind):
    value = plan()
    if kind == 'event':
        value['events'].append(dict(evidence=[dict(field=2, quote='自分で選びたい')],
            event_id='e3', fact='自分で選びたい。', unknowns=[]))
    else:
        value['readings'].append(dict(reading_id='r2', event_refs=['e1'], meaning='別の読みです。'))
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_event_plan_orphan'):
        compile_plan(value)


def test_edge_cannot_borrow_an_event_outside_both_endpoint_scopes():
    value = plan()
    value['events'].append(dict(evidence=[dict(field=2, quote='自分で選びたい')],
        event_id='e3', fact='自分で選びたい。', unknowns=[]))
    value['nodes'].append(dict(node_id='n3', node_kind='SELF_POSITION', perspective='SELF',
        title='別の記述', event_refs=['e3'], reading_refs=[]))
    value['edges'][0]['event_refs'] = ['e1', 'e2', 'e3']
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_event_plan_invalid'):
        compile_plan(value)


@pytest.mark.parametrize('bound', ['summary', 'unknowns', 'overview'])
def test_expanded_public_bounds_reject_instead_of_truncating(bound):
    value = plan()
    if bound == 'summary':
        value['events'].append(dict(evidence=[dict(field=2, quote='自分で選びたい')],
            event_id='e3', fact='う' * 160, unknowns=[]))
        value['events'][0]['fact'] = 'あ' * 160
        value['events'][1]['fact'] = 'い' * 160
        value['nodes'][0]['event_refs'] = ['e1', 'e2', 'e3']
    elif bound == 'unknowns':
        value['events'][0]['unknowns'] = ['一', '二', '三']
        value['events'][1]['unknowns'] = ['四', '五', '六']
        value['nodes'][0]['event_refs'] = ['e1', 'e2']
    else:
        for i in range(3, 15):
            value['events'].append(dict(evidence=[dict(field=2, quote='自分で選びたい')],
                event_id='e' + str(i), fact=str(i) + 'あ' * 158, unknowns=[]))
            value['nodes'].append(dict(node_id='n' + str(i), node_kind='STATE_CONTEXT',
                perspective='SELF', title='場面' + str(i), event_refs=['e' + str(i)], reading_refs=[]))
        value['events'][0]['fact'] = 'あ' * 160
        value['events'][1]['fact'] = 'い' * 160
        value['overview']['event_refs'] = ['e' + str(i) for i in range(1, 15)]
    original = deepcopy(value)
    with pytest.raises(core.AnalysisSemanticMapError):
        compile_plan(value)
    assert value == original


def test_bound_response_retains_original_raw_hash_and_exposes_only_existing_public_map():
    material, authored = prepared(), plan()
    receipt = response(material, authored)
    artifact, coverage = application.build_semantic_map(material, receipt)
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projection['wire_kind'] == 'watashi.map.v3'
    assert 'events' not in projection and 'readings' not in projection
    private = artifact.private_evidence()
    assert private['response_sha256'] == receipt.raw_sha256
    assert private['messages_sha256'] == receipt.messages_sha256
    assert private['graph']['meaning_review']['event_plan']['plan'] == authored
    assert coverage['mapped_count'] == 2


def leaf_plan(field=1, quote='自分が納得して選びたい'):
    value = plan()
    value['events'] = [dict(evidence=[dict(field=field, quote=quote)],
        event_id='e1', fact='この記録に書かれた内容です。', unknowns=[])]
    value['readings'] = []
    value['nodes'] = [value['nodes'][0]]
    value['edges'] = []
    value['overview'].update(event_refs=['e1'], reading_refs=[])
    return value


def test_history_stage_expands_before_enforcing_shown_source_and_keeps_plan_once():
    material = prepared()
    stage = core.prepare_semantic_leaf(material, (material.frozen.members[0].saved_record_ref,))
    authored = leaf_plan()
    receipt = response(stage, authored)
    graph = core.build_semantic_stage(stage, receipt)
    review = json.loads(graph.meaning_review_json)
    assert review['event_plan']['plan'] == authored
    assert review['history_synthesis']['kind'] == 'LEAF'
    assert graph.response_sha256 == receipt.raw_sha256
    assert json.loads(graph.coverage_json)['mapped_count'] == 1
    packet, repeated = core._semantic_history_leaf_packet(stage, receipt)
    assert packet['schema_version'] == core.SEMANTIC_MAP_MODEL_SCHEMA
    assert packet['nodes'][0]['evidence'] == authored['events'][0]['evidence']
    assert repeated == graph
    hidden = leaf_plan(field=3, quote='私は意見を言わなかった')
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_history_evidence_not_shown'):
        core.build_semantic_stage(stage, response(stage, hidden))
