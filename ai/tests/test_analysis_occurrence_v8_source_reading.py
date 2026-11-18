"""A field reference identifies a source. Meaning still requires comparing the whole output."""
import json

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_active_update_material import prepare, saved_update
from test_analysis_occurrence_v7_qualifications import packets, prepared


def material(p, phase='PLAN', **kwargs):
    wire = core.semantic_node_local_v4_messages(p, phase, **kwargs)
    return json.loads(wire[1]['content'])


def test_index_points_to_effective_original_ranges_without_reclassifying_the_correction():
    p = prepare(saved_update(), profile=core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE)
    source = json.loads(p.material_json)
    view = material(p)
    original = {f['field']: f for f in source['fields']}
    record = view['records'][0]
    refs = record['original_field_refs']
    assert len(refs['memo']) == 2
    assert [original[i]['text'] for i in refs['memo']] == ['私は考えをノートに書いた。', '私は資料を読んだ。']
    assert [original[i]['text'] for i in refs['memo_action']] == ['私は日程を決めた。']
    correction = next(f for f in source['fields'] if f['source_role'] == 'USER_INTERPRETATION_CORRECTION')
    assert correction['field'] not in refs['memo'] + refs['memo_action']
    assert correction in view['fields']

    selected = [dict(quote=original[refs['memo'][0]]['text'], field=refs['memo'][0]),
                dict(quote=correction['text'], field=correction['field'])]
    second_field = next(f for f in source['fields'] if f['record'] == 2)
    second = [dict(quote=second_field['text'], field=second_field['field'])]
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'),
                nodes=[dict(node_id='n1', units=[dict(evidence=selected)]),
                       dict(node_id='n2', units=[dict(evidence=second)])])
    parts = material(p, 'NODES', plan=plan)['evidence_parts_by_unit']['n1.u1']
    assert parts['e1'] == dict(field=selected[0]['field'], quote=selected[0]['quote'], original_record=1)
    assert parts['e2'] == dict(field=correction['field'], quote=correction['text'])


def test_absent_action_and_single_record_leaf_do_not_invent_or_borrow_a_field():
    parent = prepared(core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE)
    for member in parent.frozen.members:
        leaf = core.prepare_semantic_leaf(parent, (member.saved_record_ref,))
        view = material(leaf)
        assert len(view['records']) == len(view['fields']) == 1
        f, = view['fields']
        assert view['records'][0]['original_field_refs'] == {'memo': [f['field']]}
        assert 'memo_action' not in view['records'][0]['original_field_refs']


def test_v7_material_and_selected_fact_locations_remain_distinct_from_v8():
    legacy = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    candidate = prepared(core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE)
    plan, _, _ = packets(legacy)
    old_plan, new_plan = material(legacy), material(candidate)
    old_nodes = material(legacy, 'NODES', plan=plan)
    new_nodes = material(candidate, 'NODES', plan=plan)
    assert old_nodes['plan'] == new_nodes['plan'] == plan
    assert old_plan['fields'] == new_plan['fields']
    for row, new_row in zip(old_plan['records'], new_plan['records'], strict=True):
        assert 'original_field_refs' not in row
        refs = new_row['original_field_refs']['memo']
        assert refs == [f['field'] for f in old_plan['fields'] if f['record'] == row['record']]
    originals = {f['field']: f['record'] for f in old_plan['fields']}
    for unit, parts in new_nodes['evidence_parts_by_unit'].items():
        for ref, part in parts.items():
            previous = old_nodes['evidence_parts_by_unit'][unit][ref]
            assert part == dict(previous, original_record=originals[previous['field']])
