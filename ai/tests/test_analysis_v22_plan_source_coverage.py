"""Protect bounded source evidence while preserving the author's freedom to place it."""
from copy import deepcopy

import pytest

import analysis_plan_source_choices as source
from test_analysis_node_local_native_profile import advance
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_occurrence_v17_record_owners import compact, packet, parser, verify
from test_analysis_occurrence_v18_compact_originals import prepared
from test_analysis_v21_recorded_schedule import V21


V22 = 'semantic_map.node_local.v4.occurrence.v22'
EARLY = '公園では四十分歩けたが、夜の道では同じとは限らない。'
LATER = '川沿いで二十分歩けた。'
PAIRS = [('公園を歩いた。', '切符を買った。' + EARLY),
         ('二十分小道を歩いた。', '地図を開いた。' + LATER)]


def requirements(pairs=PAIRS, profile=V22):
    p = prepared(pairs, profile)
    shown, original, _, _ = view(p)
    return shown, source.whole_plan_sources(original, source.record_plan_owners(original))


@pytest.mark.parametrize('early,action,later,later_action', [
    (EARLY, '公園を歩いた。', LATER, '二十分の待ち時間の後に道を歩いた。'),
    (EARLY, '公園を歩いた。', LATER, '二十分休んでから小道を歩いた。'),
    (EARLY, '公園を歩いた。', LATER, '二十分読んだ。小道を歩いた。'),
    (EARLY, '公園を歩かなかった。', LATER, '二十分歩いた。'),
    ('母は四十分歩けた。', '母は公園を歩いた。', '弟は二十分歩けた。', '弟は二十分歩いた。'),
    (EARLY, '父が公園を歩いた。', LATER, '二十分歩いた。'),
    ('もし朝なら四十分歩けた。', '公園を歩いた。', LATER, '二十分歩いた。'),
    ('「四十分歩けた」と聞いた。', '公園を歩いた。', LATER, '二十分歩いた。'),
    ('四十分歩ける予定だった。', '公園を歩いた。', LATER, '二十分歩いた。'),
    ('四十分歩かなかった。', '公園を歩いた。', '二十分歩かなかった。', '二十分歩いた。'),
    ('四十分歩きたかった。', '公園を歩いた。', '二十分歩きたかった。', '二十分歩いた。'),
    ('五時三十分歩けた。', '公園を歩いた。', LATER, '二十分歩いた。'),
    ('二千円を支払った。', '代金を支払った。', LATER, '二十分歩いた。'),
    ('二日だけ歩く予定だ。', '公園を歩いた。', LATER, '二十分歩いた。'),
    ('道を十分歩けた。', '公園を歩いた。', LATER, '二十分歩いた。'),
    (EARLY + '帰りにも三十分歩けた。', '公園を歩いた。', LATER, '二十分歩いた。'),
])
def test_other_actor_time_goal_or_unrelated_duration_never_claims_a_slot(early, action, later, later_action):
    shown, required = requirements([(action, early), (later_action, later)])
    assert not required and 'whole_plan_source_ranges' not in shown


@pytest.mark.parametrize('early,later,actions', [
    ('風の弱い日には四十分走れたが、雨の日には試していない。', '午後に十五分走れた。',
     ('道を走った。', '十五分走った。')),
    ('窯の中で二時間焼いた。', '昨日に六十分焼いた。',
     ('鉢を焼いた。', '六十分鉢を焼いた。')),
])
def test_other_actions_retain_exact_sentence_and_record(early, later, actions):
    shown, required = requirements([(actions[0], early), (actions[1], later)])
    assert list(required.values()) == [early, later]
    assert len(shown['whole_plan_source_ranges']) == 2


def test_scope_bounds_and_presented_offsets_round_trip():
    shown, wanted = requirements()
    material, _, _ = source.restore_view(shown)
    assert wanted == {1: EARLY, 3: LATER}
    for row in shown['whole_plan_source_ranges']:
        field = next(f for f in material['fields'] if f['field'] == row['field'])
        start, end = row['scalar_range']
        assert field['text'][start:end] == wanted[row['field']]
    broken = deepcopy(shown)
    broken['whole_plan_source_ranges'][0]['scalar_range'][0] += 1
    with pytest.raises(ValueError):
        source.restore_view(broken)
    assert requirements(PAIRS, V21)[1] == {}
    limited = [(PAIRS[0][0], '青' * 135 + '。' + EARLY), PAIRS[1]]
    # One legal two-sentence PLAN root exceeds the per-root display limit.
    # It must remain an ordinary, freely excerptable source, not a guaranteed witness.
    assert not requirements(limited)[1]
    for foreign in [dict(history_stage={'kind':'MERGE'}), dict(map_corrections=[1]),
                    dict(emlis_source_materials=[dict(conflicts=[True])])]:
        changed = dict(material, **foreign)
        assert not source.whole_plan_sources(changed, source.record_plan_owners(changed))
    assert not source.whole_plan_sources(material, ())
    material['fields'][0]['fragment_is_complete_field'] = False
    assert not source.whole_plan_sources(material, source.record_plan_owners(material))


def test_first_or_later_node_and_extended_source_are_equivalent():
    p = prepared(PAIRS, V22)
    heads = [[[(1, '切符を買った。')]], [[(3, LATER)]]]
    verify(p, packet(p, heads), False)
    verify(p, packet(p, [[[(1, '切符を買った。' + EARLY)]], heads[1]]), True)
    verify(p, packet(p, heads + [[[(1, EARLY)]]]), True)
    before = prepared(PAIRS, V21)
    verify(before, packet(before, heads), True)


def test_last_node_preserves_any_lead_and_reserves_only_actually_needed_evidence_slots():
    extras = [f'第{i}号の札を置いた。' for i in range(1, 13)]
    pairs = [(PAIRS[0][0], ''.join(extras) + EARLY), PAIRS[1]]
    p = prepared(pairs, V22)
    # The ten optional nodes can choose any still-distinct lead. Give the last
    # one an unrelated lead too, and leave the two missing ranges to its final unit.
    heads = [[[(1, extras[0]), (1, extras[5]), (1, extras[10])]], [[(3, '地図を開いた。')]]]
    earlier = heads + [[[(1, quote)]] for quote in extras[1:10]]
    last = [[(1, extras[11])], [(1, extras[0]), (1, extras[1]), (1, EARLY), (3, LATER)]]
    value = packet(p, earlier + [last])
    verify(p, value, True)
    before_unit = compact(value).rpartition('},{"evidence":[')[0] + '}'
    state = advance(parser(p, value), before_unit)
    assert ']' not in state.get_allowed_characters() and ',' in state.get_allowed_characters()
    raw = compact(value)
    last_two_start = raw.index(compact(value['nodes'][-1]['units'][1]['evidence'][2]))
    state = advance(parser(p, value), raw[:last_two_start])
    distractor = value['nodes'][0]['units'][0]['evidence'][2]
    with pytest.raises(ValueError):
        advance(state, compact(distractor))
    advance(state, compact(value['nodes'][-1]['units'][1]['evidence'][2]))


def test_twelve_record_owners_keep_room_for_their_own_source_without_forbidding_overlapping_quotes():
    extras = [f'第{i}号の札を置いた。' for i in range(1, 13)]
    # Action fields are kept short and the first thought has several existing
    # regions. The other ten owners reserve their whole original nodes.
    pairs = [(PAIRS[0][0], ''.join(extras) + EARLY), PAIRS[1]]
    pairs.extend([(f'箱を第{i}室に置いた。', f'紙を第{i}室に届けた。') for i in range(3, 13)])
    p = prepared(pairs, V22)
    _, material, _, _ = view(p)
    fields = [row['original_field_refs']['memo'][0] for row in material['records']]
    assert len(source.record_plan_owners(material)) == len(fields) == 12
    first, second = fields[:2]
    remaining = [[[(f, note)]] for f, (_, note) in zip(fields[2:], pairs[2:], strict=True)]
    heads = [[(first, extras[0]), (first, extras[5]), (first, extras[10])]]
    nodes = [heads, [[(second, '地図を開いた。' + LATER), (second, LATER)]], *remaining]
    verify(p, packet(p, nodes), False)
    last = [(first, extras[1]), (first, extras[2]), (first, extras[3]), (first, EARLY)]
    nodes[0] = [heads[0], last]
    value = packet(p, nodes)
    verify(p, value, True)
    text = compact(value)
    slot = compact(value['nodes'][0]['units'][1]['evidence'][-1])
    state = advance(parser(p, value), text[:text.index(slot)])
    with pytest.raises(ValueError):
        advance(state, compact(value['nodes'][0]['units'][0]['evidence'][-1]))
    advance(state, slot)
