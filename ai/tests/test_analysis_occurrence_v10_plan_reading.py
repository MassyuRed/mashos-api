"""PLAN sees source-bound leads for a second object while choosing its evidence."""
import json

import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_active_update_material import prepare as prepare_correction, saved_update
from test_analysis_cumulative import OWNER, source_snapshot


def plan_material(prepared):
    return json.loads(prepared.messages()[1]['content'])


def test_independent_topic_action_is_available_during_plan_on_its_own_day():
    snapshot = source_snapshot(2)
    notes = [
        ('初日は観察日誌の構成を考えた。', '観察日誌の草案を手元に残した。受付にはまだ渡していない。'),
        ('翌日、受付から製本の日程を聞いた。', '観察日誌を受付に手渡した。別冊の目次を誰が校閲したかは聞いていない。'),
    ]
    for row, (memo, action) in zip(snapshot['members'], notes):
        row['original'].update(memo=memo, memo_action=action)
    current = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    old = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    source = plan_material(old)
    assert not any('unassessed_passage_cues' in f for f in source['fields'])
    view = plan_material(current)
    assert [field['record'] for field in view['fields']] == [field['record'] for field in source['fields']]
    assert view['source_duties'] == source['source_duties']
    for row in view['records']:
        fields = [f for f in view['fields'] if f['record'] == row['record']]
        assert [f['field_path'] for f in fields] == ['memo_action', 'memo']
        for f in fields:
            before = next(oldfield for oldfield in source['fields'] if oldfield['field'] == f['field'])
            assert {k:v for k,v in f.items() if k != 'unassessed_passage_cues'} == before
        assert 'unassessed_passage_cues' not in fields[1]
    current_action = view['fields'][2]
    assert ['別冊の目次を誰が校閲したかは聞いていない'] in current_action['unassessed_passage_cues']
    leaf = core.prepare_semantic_leaf(current, (current.frozen.members[-1].saved_record_ref,))
    assert plan_material(leaf)['fields'] == view['fields'][2:]


def test_plan_reading_does_not_reorder_corrections_or_use_withdrawn_originals():
    current = prepare_correction(saved_update(), profile=core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    old = prepare_correction(saved_update(), profile=core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    before, after = plan_material(old), plan_material(current)
    assert [f for f in enumerate(after['fields']) if f[1]['source_role'] != 'ORIGINAL_INPUT'] == [
        f for f in enumerate(before['fields']) if f[1]['source_role'] != 'ORIGINAL_INPUT']
    assert all('私は仕事を続けたい' not in str(f.get('unassessed_passage_cues', [])) for f in after['fields'])


def test_excerpt_cues_use_original_coordinates_and_omit_partly_hidden_ranges():
    material = dict(fields=[
        dict(record=1, field=2, source_role='ORIGINAL_INPUT', field_path='memo_action',
             text='仮置き。別紙は未提出。', fragment_scalar_range=[8,19]),
        dict(record=1, field=3, source_role='SIMULATION_SESSION_MATERIAL', field_path='memo_action', text='別人の例。')
    ], source_duties=dict(unassessed_source_ranges=[
        dict(field=2, ranges=[[0,4],[5,11],[12,18],[18,24]]),
        dict(field=3, ranges=[[0,4]])
    ]))
    fields = core._semantic_plan_reading_fields(material)
    assert fields[0]['unassessed_passage_cues'] == [['別紙は未提出']]
    assert fields[1] == material['fields'][1]
    assert 'unassessed_passage_cues' not in material['fields'][0]
