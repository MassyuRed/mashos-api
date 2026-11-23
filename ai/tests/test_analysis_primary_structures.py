"""Final authoring, admission and public read of grounded primary structures."""
import hashlib
import json
from uuid import UUID

import pytest

import analysis_cumulative_service as service
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_analysis_node_local_v4_phases import response
from test_analysis_occurrence_v11_display import map_stages
from test_analysis_occurrence_v17_record_owners import packet
from test_analysis_v13_separate_record_titles import wire

FIRST = '会議では、自分で選んだ仕事なので私から引き受けた。'
SECOND = '家では手伝うと決められてしまい、自分で決めたかったので断った。'


def scenario(*notes, self_report=False):
    old, plan, bodies = map_stages(*notes)
    snapshot = json.loads(old.source_snapshot_json)
    if self_report:
        snapshot['members'][0]['original'].update(emotions=['自己理解'])
    p = maps.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE, primary_structures=True)
    for node in bodies['nodes'].values():
        node['units']['u1'].update(unknowns=[], source_mode='PERSON_JUDGMENT')
    return p, plan, bodies


def reading(scope='across_records', anchors=('n1.u1.e1', 'n2.u1.e1')):
    return dict(anchors=list(anchors), scope=scope, heading='自分で選ぶ余地',
                reading='手を貸すかを決める場面では、ご自身で引き受けるかどうかを選べることを大切にしています。')


def test_final_native_receipt_and_saved_graph_show_conditional_conclusion_and_hide_private_anchors():
    p, plan, bodies = scenario(FIRST, SECOND)
    nodes = core._semantic_v4_join(plan, bodies)
    notes = [FIRST, SECOND]
    plan_wire = packet(p, [[[(i, note)]] for i, note in enumerate(notes, 1)])
    material = json.loads(p.material_json)
    from analysis_plan_source_choices import WholeMapTitle
    scope = WholeMapTitle(material, nodes).neutral
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
               qualification_review={}, edges=[], overview=dict(node_refs=['n1', 'n2'], title_proposal='', title=scope),
               primary_structures=[reading()])
    receipts = []
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES,
                            (plan_wire, wire(p, plan, bodies), rel), strict=True):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan if phase != 'PLAN' else None,
                                                       nodes=bodies if phase == 'RELATIONS' else None)
        if phase == 'RELATIONS':
            assert json.loads(messages[1]['content'])['primary_structure_reading'] == 'karen.v1'
            assert accepts(value, messages)
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        receipts.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(messages), raw=raw,
                             raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop', completion_tokens=100))
    received = dict(schema_version=core.semantic_node_local_v4_artifact_schema(p), phases=receipts)
    artifact, coverage = maps.build_semantic_map(p, response(p, received))
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert coverage['mapped_count'] == 2
    assert graph['overview']['primary_structures'] == [
        dict(scope='across_records', title=reading()['heading'], description=reading()['reading'], node_refs=['n1', 'n2'])]
    assert 'n1.u1.e1' not in json.dumps(graph) and reading()['reading'] in text
    assert service._checked_projection(graph, str(UUID(artifact.artifact_id[9:]))) == graph
    assert service._saved_projection_text_matches(graph, text)
    payload = dict(meta=graph, item=dict(content_json=dict(watashiMap=graph)), content_text=text)
    assert service.map_response_for_renderer(payload, 'semantic.v2')['meta'] == graph
    old = service.map_response_for_renderer(payload, 'semantic.v1')
    assert 'primary_structures' not in old['meta']['overview']
    assert 'primary_structures' not in old['item']['content_json']['watashiMap']['overview']
    assert 'primary_structures' in graph['overview']


@pytest.mark.parametrize('fault', ['one_record', 'copied_note', 'unknown_anchor', 'same_anchor', 'only_other_person',
                                   'four_claims', 'duplicated_axis', 'wish_only', 'claim_as_source'])
def test_reject_unbound_repeated_or_overgeneralised_readings(fault):
    p, plan, bodies = scenario(FIRST, FIRST if fault == 'copied_note' else SECOND)
    nodes = core._semantic_v4_join(plan, bodies)
    axes = [reading()]
    if fault == 'one_record':
        axes = [reading(anchors=['n1.u1.e1'])]
    if fault == 'unknown_anchor':
        axes = [reading(anchors=['n1.u99.e1'])]
    if fault == 'same_anchor':
        axes = [reading(anchors=['n1.u1.e1'] * 2)]
    if fault == 'only_other_person':
        for node in nodes:
            node['perspective'] = 'OBSERVED_INTERACTION'
    if fault in ('four_claims', 'duplicated_axis'):
        axes *= 4 if fault == 'four_claims' else 2
    if fault == 'wish_only':
        for node in nodes:
            node['units'][0]['source_mode'] = 'PERSON_WISH'
    if fault == 'claim_as_source':
        axes[0]['reading'] = FIRST
    with pytest.raises(core.AnalysisSemanticMapError):
        core._read_primary_structures(p, json.loads(p.material_json), nodes, axes)


def test_single_self_interpretation_and_one_off_event_have_different_scope():
    p, plan, bodies = scenario('人と過ごした後は一人で本を読む時間も大切だと思った。', self_report=True)
    material = json.loads(p.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    axes = [reading('self_report', ['n1.u1.e1'])]
    assert core._read_primary_structures(p, material, nodes, axes)[0]['scope'] == 'self_report'
    material['records'][0]['selected_emotions'] = ['喜び']
    with pytest.raises(core.AnalysisSemanticMapError):
        core._read_primary_structures(p, material, nodes, axes)
    assert core._read_primary_structures(p, material, nodes, [reading('in_this_record', ['n1.u1.e1'])])
    assert core._read_primary_structures(p, material, nodes, []) == []
    material['fields'][0]['field_path'] = 'memo_action'
    with pytest.raises(core.AnalysisSemanticMapError):
        core._read_primary_structures(p, material, nodes, [reading('in_this_record', ['n1.u1.e1'])])


def test_history_merge_native_parser_preserves_structure_and_leaf_never_authors_one():
    from dataclasses import replace

    import analysis_merge_wire as merge
    from test_analysis_merge_transport import source_merge
    from test_analysis_node_local_native_profile import advance
    from test_emlis_natural_reply_probe_http import probe
    from analysis_plan_source_choices import WholeMapTitle

    p, plan, bodies = scenario(FIRST, SECOND)
    stage = source_merge([FIRST, SECOND])
    material = json.loads(stage.material_json)
    material['primary_structure_reading'] = 'karen.v1'
    stage = replace(stage, parent=p, material_json=core.semantic_map_canonical(material))
    messages = core.semantic_node_local_v4_wire_messages(stage, 'RELATIONS', plan=plan, nodes=bodies)
    codec = merge.response_codec(messages)
    overview = dict(node_refs=['n1', 'n2'], title_proposal='', title=WholeMapTitle(
        material, core._semantic_v4_join(plan, bodies)).neutral)
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=codec.binding,
               qualification_review={}, edges=[], overview=overview, primary_structures=[reading()])
    physical = codec.encode(rel)
    raw = merge.compact_json(physical)
    alphabet = ''.join(dict.fromkeys(merge.compact_json(messages) + raw))
    completed = advance(probe.semantic_json_parser(messages, alphabet), raw)
    assert completed.can_end() and json.loads(completed.projected_prefix()) == rel
    joined = core.semantic_node_local_v4_relations(stage, plan, bodies, codec.decode(physical))
    assert joined['overview']['primary_structures'][0]['node_refs'] == ['n1', 'n2']
    refs = tuple(m.saved_record_ref for m in p.frozen.members)
    leaf = core.prepare_semantic_leaf(p, refs)
    leaf_messages = core.semantic_node_local_v4_messages(leaf, 'RELATIONS', plan=plan, nodes=bodies)
    assert 'primary_structures' not in probe.semantic_output_schema(leaf_messages)['properties']
