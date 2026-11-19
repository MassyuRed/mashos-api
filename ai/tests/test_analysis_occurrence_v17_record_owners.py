"""Bound ordinary PLAN nodes to independent original records before optional synthesis."""
import json
from copy import deepcopy

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_saved_period import with_answer
from test_analysis_semantic_history_core import correction_snapshot

V16, V17 = core.SEMANTIC_MAP_OCCURRENCE_V16_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V17_PROFILE


def prepared(notes, version=V17):
    snap = source_snapshot(len(notes))
    for member, note in zip(snap['members'], notes, strict=True):
        member['original'].update(memo=note, memo_action='')
    return maps.prepare_semantic_map(OWNER, snap, prompt_version=version)


def packet(p, nodes):
    material, _, table, _ = view(p)
    cues = {(field, quote): cue for (field, cue), quote in table.items()}
    return dict(schema_version=core._semantic_v4_schema('PLAN'),
        source_choices_sha256=material['source_choices_sha256'],
        nodes=[dict(node_id=f'n{i}', units=[
            dict(evidence=[dict(quote=cues.get((field, quote), quote), field=field) for field, quote in unit])
            for unit in units]) for i, units in enumerate(nodes, 1)])


def verify(p, raw, expected):
    assert accepts(raw, p.messages()) == expected
    if expected:
        return core.admit_semantic_node_local_v4_plan_response(p, raw)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.admit_semantic_node_local_v4_plan_response(p, raw)


def compact(data):
    return json.dumps(data, ensure_ascii=False, separators=(',', ':'))


def parser(p, raw):
    return probe.semantic_json_parser(p.messages(), ''.join(dict.fromkeys(compact(raw) + compact(p.messages()))))


@pytest.mark.parametrize('profile,expected', [(V16, True), (V17, False)])
def test_similar_subjects_with_distinct_people_cannot_take_each_others_original_slots(profile, expected):
    notes = ['友人に変更の相談をした。', '妹に予定表を渡した。']
    p = prepared(notes, profile)
    mixed = [[[(1, notes[0]), (2, notes[1])]]]
    verify(p, packet(p, mixed), expected)
    verify(p, packet(p, [[[(2, notes[1])]], [[(1, notes[0])]]]), expected)
    separated = [[[(i, note)]] for i, note in enumerate(notes, 1)]
    verify(p, packet(p, separated), True)


def test_record_head_and_genuine_later_corroboration_can_coexist():
    first, extra = '私は弦を張った。', '袋から古い弦を出した。'
    later, third = '翌日、その張り替えを写した写真が届いた。', '隣の楽器の鍵を預かった。'
    p = prepared([first + extra, later, third])
    nodes = [[[(1, first)]], [[(2, later)]], [[(3, third)]]]
    # The optional node has its own distinct lead and can cite both sources.
    nodes.append([[(1, extra), (2, later), (1, first)]])
    closed = verify(p, packet(p, nodes), True)
    assert [r['field'] for r in closed['nodes'][-1]['units'][0]['evidence']] == [1, 2, 1]


def test_supplement_can_follow_its_own_original_and_correction_keeps_its_own_cohort():
    snap = correction_snapshot()
    snap['members'][0]['original']['emotion_details'] = [dict(type='平穏', strength='medium')]
    snap['members'][0] = with_answer(snap['members'][0], '私は日程を決めなかった。')
    p = maps.prepare_semantic_map(OWNER, snap, prompt_version=V17)
    _, original, _, _ = view(p)
    fields = original['fields']
    heads = [[[(f['field'], f['text'].split('。')[0] + '。')]] for f in fields if f['source_role'] == 'ORIGINAL_INPUT']
    supplement, = [(f['field'], f['text']) for f in fields if f['source_role'] == 'SUPPLEMENTAL_ANSWER']
    correction, = [f for f in fields if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION']
    assert correction['record'] is None and correction['record_refs'] == [1, 2]
    heads[0][0].append(supplement)
    full = heads + [[[(correction['field'], correction['text'])]]]
    verify(p, packet(p, full), True)
    verify(p, packet(p, heads), False)
    for wrong in ('other_supplement', 'supplement_first', 'cohort_as_owner'):
        candidate = deepcopy(full)
        if wrong == 'other_supplement':
            candidate[1][0].append(supplement)
        elif wrong == 'supplement_first':
            candidate[0][0].reverse()
        else:
            candidate[1][0].append(candidate.pop()[0][0])
        verify(p, packet(p, candidate), False)


def test_native_keeps_a_completion_path_on_last_local_choice_and_next_record():
    notes = ['水位を読んだ。', '別の井戸に蓋をした。']
    p = prepared(notes)
    raw = packet(p, [[[(i, note)]] for i, note in enumerate(notes, 1)])
    encoded = compact(raw)
    first_node = raw['nodes'][0]
    first_root = compact(first_node['units'][0]['evidence'][0])
    state = advance(parser(p, raw), encoded[:encoded.index(first_root) + len(first_root)])
    assert ',' not in state.get_allowed_characters() and ']' in state.get_allowed_characters()
    state = advance(state, ']}]}')
    assert ']' not in state.get_allowed_characters() and ',' in state.get_allowed_characters()
    second = compact(raw['nodes'][1]['units'][0]['evidence'][0])
    state = advance(state, ',{"node_id":"n2","units":[{"evidence":[')
    with pytest.raises(ValueError):
        advance(state, first_root)
    assert advance(state, second + ']}]}]}').can_end()


@pytest.mark.parametrize('count', [12, 13, 24, 25])
def test_at_capacity_and_beyond_existing_flexible_coverage_is_preserved(count):
    notes = [f'標本{i}を調べた。' for i in range(1, count + 1)]
    p = prepared(notes)
    candidates = [(i, note) for i, note in enumerate(notes, 1)]
    grouped = [[candidates[i:i+4]] for i in range(0, count, 4)] if count <= 24 else [[candidates[:1]]]
    verify(p, packet(p, grouped), count > 12)
    if count == 12:
        verify(p, packet(p, [[[pair]] for pair in candidates]), True)


def test_ownership_requires_an_admissible_original_and_fits_independent_corrections():
    material = dict(author_profile=V17, records=[dict(record=n) for n in [5, 2]], fields=[
        dict(record=2, field=1, source_role='ORIGINAL_INPUT', text='棚の扉を閉めた。'),
        dict(record=5, field=4, source_role='ORIGINAL_INPUT', text='紙を折った。')])
    assert choices.record_plan_owners(material) == (({4}, {4}), ({1}, {1}))
    assert not choices.record_plan_owners(material, {1})
    for stage in ['LEAF', 'MERGE']:
        assert not choices.record_plan_owners(dict(material, history_stage=dict(kind=stage)))
    unowned = dict(field=7, record=None, record_refs=[2, 5], source_role='USER_ANALYSIS_MAP_CORRECTION', text='その時だけです。')
    capacity = dict(material, records=[dict(record=r) for r in range(1, 13)],
        fields=[dict(record=r, field=r, source_role='ORIGINAL_INPUT', text='原文。') for r in range(1, 13)]
        + [dict(unowned, field=13)])
    assert not choices.record_plan_owners(capacity)


def test_last_free_node_reserves_its_last_root_for_an_unowned_correction():
    snap = correction_snapshot()
    for index, record in enumerate(snap['members'], 1):
        record['original']['memo'] = ''.join(f'第{index}室の標本{j}を見た。' for j in range(6))
    p = maps.prepare_semantic_map(OWNER, snap, prompt_version=V17)
    _, original, _, _ = view(p)
    sources = [f for f in original['fields'] if f['source_role'] == 'ORIGINAL_INPUT']
    correction, = [f for f in original['fields'] if f['source_role'] == 'USER_ANALYSIS_MAP_CORRECTION']
    def root(f, j):
        return f['field'], f['text'].split('。')[j] + '。'
    distinct = [root(f, j) for j in range(6) for f in sources]
    correction_root = correction['field'], correction['text']
    # The three mandatory nodes come first. Eight optional nodes then consume
    # distinct lead positions before the only remaining node opens its last unit.
    allocation = [[[r]] for r in distinct[:11]]
    last = [[distinct[11]], [*distinct[12:15], correction_root]]
    raw = packet(p, allocation + [last])
    verify(p, raw, True)
    target = compact(raw['nodes'][-1]['units'][-1]['evidence'][-1])
    prefix = compact(raw).rsplit(',' + target, 1)[0]
    state = advance(parser(p, raw), prefix)
    assert ']' not in state.get_allowed_characters() and ',' in state.get_allowed_characters()
    state = advance(state, ',')
    with pytest.raises(ValueError):
        advance(state, compact(raw['nodes'][0]['units'][0]['evidence'][0]))
    assert advance(state, target + ']}]}]}').can_end()


def test_at_twelve_nodes_separate_records_still_support_one_event_in_relations_and_overview():
    from test_analysis_occurrence_v14_visible_closers import stages

    first = '私は青い額を展示室に掛けた。'
    later = 'その青い額を掛けている私を写した写真が届いた。'
    independent = [f'標本{i}の番号を読んだ。' for i in range(10)]
    notes = [first, *independent, later]
    p, plan, nodes = stages(*notes, profile=V17)
    assert verify(p, packet(p, [[[(i, note)]] for i, note in enumerate(notes, 1)]), True) == plan
    edge = {'from':'n1', 'to':'n12', 'from_unit':'n1.u1', 'to_unit':'n12.u1',
        'from_source':core._semantic_source_cues(first)[0], 'to_source':core._semantic_source_cues(later)[0],
        'label':'青い額を掛けた場面を、後日届いた写真でも確認した', 'relation_kind':'SHARED_MEANING'}
    overview = dict(node_refs=['n1', 'n12'], title='青い額を展示する作業と、後から届いたその写真')
    joined = core._semantic_v4_join(plan, nodes)
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(joined),
        qualification_review={}, edges=[edge], overview=overview)
    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    assert accepts(rel, messages)
    projected = core.semantic_node_local_v4_relations(p, plan, nodes, rel)
    assert len(projected['nodes']) == 12 and projected['edges'][0]['label'] == edge['label']
    assert projected['overview'] == overview
