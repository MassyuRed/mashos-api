"""Phase messages retain the recording clock of each original without redating corrections."""
import json

import analysis_model_source as source
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_active_update_material import prepare, saved_update
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v7_qualifications import BROTHER, prepared, reply
from test_analysis_occurrence_v9_source_cues import example


def node_material(p, plan):
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    return json.loads(messages[1]['content'])


def test_selected_parts_use_their_own_original_clock_across_records():
    legacy, plan, _, _ = example(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    candidate = prepared(core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    assert source._configured_semantic_prompt_version(source.SEMANTIC_OCCURRENCE_V10_MODEL) == candidate.prompt_version
    view = node_material(candidate, plan)
    old = node_material(legacy, plan)
    original = {f['field']: f for f in view['fields']}
    assert len({f['original_recorded_at'] for f in original.values()}) == 2
    for unit, parts in view['evidence_parts_by_unit'].items():
        for key, evidence in parts.items():
            field = original[evidence['field']]
            assert evidence == {**old['evidence_parts_by_unit'][unit][key],
                                'original_recorded_at': field['original_recorded_at']}
    assert view['plan'] == old['plan'] == plan


def test_corrected_originals_keep_their_clock_supplemental_corrections_do_not_borrow_it():
    p = prepare(saved_update(), profile=core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    fields = json.loads(p.material_json)['fields']
    original = [f for f in fields if f['source_role'] == 'ORIGINAL_INPUT']
    corrections = [f for f in fields if f['source_role'] != 'ORIGINAL_INPUT']
    assert corrections
    selected = [original[0], next(f for f in original if f['record'] != original[0]['record']), *corrections]
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[
        dict(node_id='n'+str(i), units=[dict(evidence=[dict(field=f['field'], quote=f['text'])])])
        for i, f in enumerate(selected, 1)])
    view = node_material(p, plan)
    for i, field in enumerate(selected, 1):
        part = view['evidence_parts_by_unit'][f'n{i}.u1']['e1']
        assert ('original_recorded_at' in part) == (field['source_role'] == 'ORIGINAL_INPUT')


def test_single_record_leaf_uses_its_own_sources_without_multi_record_copy():
    parent = prepared(core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    member = parent.frozen.members[0]
    leaf = core.prepare_semantic_leaf(parent, (member.saved_record_ref,))
    row = json.loads(leaf.material_json)['fields'][0]
    quote = row['text'].split('。')[0] + '。'
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=[
        dict(node_id='n1', units=[dict(evidence=[dict(field=row['field'], quote=quote)])])])
    view = node_material(leaf, plan)
    assert 'original_recorded_at' not in view['evidence_parts_by_unit']['n1.u1']['e1']


def test_authored_past_context_and_separate_open_condition_survive_public_projection():
    legacy, plan, nodes, relations = example(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    candidate = prepared(core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    assert core.semantic_node_local_v4_artifact_schema(legacy) != core.semantic_node_local_v4_artifact_schema(candidate)
    for phase, packet in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (plan, nodes, relations), strict=True):
        messages = core.semantic_node_local_v4_messages(candidate, phase, plan=plan, nodes=nodes)
        assert accepts(packet, messages)
    # These fixture phrases were written before projection. The artifact must
    # retain them as authored and must never turn the recording date into an event.
    new_response = reply(candidate, (plan, nodes, relations))
    previous_response = reply(legacy, (plan, nodes, relations))
    current, _ = app.build_semantic_map(candidate, new_response)
    previous, _ = app.build_semantic_map(legacy, previous_response)
    projection = current.safe_projection(authenticated_owner_scope=OWNER)
    old_projection = previous.safe_projection(authenticated_owner_scope=OWNER)
    assert all(projection[k] == old_projection[k] for k in ('overview','nodes','edges'))
    assert [node['unknowns'] for node in projection['nodes']] == [[], [BROTHER]]
    assert BROTHER in current.safe_text_projection(authenticated_owner_scope=OWNER)['text']
