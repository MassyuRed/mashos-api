"""A compact recorded action beside a long account remains available to the body author."""
from copy import deepcopy

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_node_local_native_profile import accepts, advance
from test_analysis_occurrence_v11_display import map_stages
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_occurrence_v17_record_owners import compact, packet, parser, verify
from test_analysis_v13_separate_record_titles import wire

V17, V18 = core.SEMANTIC_MAP_OCCURRENCE_V17_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE
ACTION = '水槽の温度を記録した。仕切り板を移した。三十分だけ水流を弱めた。'
DETAIL = '以前に書いた目盛りは隣の水槽で読んだ値だった。'
LONG = DETAIL + ''.join(f'棚の上の札に書かれていた第{i}回の数値を読み返した。' for i in range(8))


def prepared(pairs, profile=V18):
    snapshot = source_snapshot(len(pairs))
    for member, (action, thought) in zip(snapshot['members'], pairs, strict=True):
        member['original'].update(memo_action=action, memo=thought)
    return maps.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)


@pytest.mark.parametrize('profile,valid', [(V17, True), (V18, False)])
def test_one_short_passage_from_each_field_can_still_lose_what_was_done(profile, valid):
    p = prepared([(ACTION, LONG)], profile)
    _, original, _, _ = view(p)
    fields = {x['field_path']: x['field'] for x in original['fields']}
    verify(p, packet(p, [[[(fields['memo_action'], ACTION.split('。')[0]+'。'), (fields['memo'], DETAIL)]]]), valid)


@pytest.mark.parametrize('separate_units', [True, False])
def test_entire_action_retains_all_its_sentences_and_independent_record_account(separate_units):
    p = prepared([(ACTION, LONG)])
    shown, original, _, allowed = view(p)
    action, full, thought = choices.compact_action_pairs(original)[1]
    assert shown['records'][0]['paired_original_fields'] == [action, thought]
    assert full == ACTION and full in allowed[action]
    units = [[(action, full)], [(thought, DETAIL)]] if separate_units else [[(action, full), (thought, DETAIL)]]
    plan = verify(p, packet(p, [units]), True)
    assert [r['quote'] for u in plan['nodes'][0]['units'] for r in u['evidence']] == [ACTION, DETAIL]
    # This root survives native NODES reconstruction even when it contains more than two sentences.
    _, _, old = map_stages(DETAIL)
    author = old['nodes']['n1']
    author['title'], author['meaning'] = DETAIL, '水流を調整した時の記録。'
    author['units'] = {}
    for index, unit in enumerate(plan['nodes'][0]['units'], 1):
        parts = {}
        for ordinal, evidence in enumerate(unit['evidence']):
            parts[core._semantic_fact_part_key(unit['evidence'], ordinal)] = (
                '@3' if evidence['field'] == action else evidence['quote'])
        author['units'][f'u{index}'] = dict(evidence_ref=f'n1.u{index}', source_mode='RECORDED',
                                             fact_parts=parts, unknowns=[])
    old['plan_sha256'] = core.semantic_map_hash(plan)
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    raw = wire(p, plan, old)
    assert accepts(raw, messages)
    saved = core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
    assert '三十分だけ水流を弱めた。' in saved['nodes']['n1']['units']['u1']['fact_parts'].values()


def test_first_thought_can_witness_same_verbatim_action_but_not_a_paraphrase_or_other_record():
    action = '水位を読み取った。'
    paraphrase = '水面の高さを測定した。'
    p = prepared([(action, action + LONG), (action, paraphrase + LONG)])
    _, original, _, _ = view(p)
    a1, _, t1 = choices.compact_action_pairs(original)[1]
    a2, _, t2 = choices.compact_action_pairs(original)[2]
    own = [[[(t1, action)]], [[(a2, action), (t2, paraphrase)]]]
    verify(p, packet(p, own), True)
    for invalid in ([[[(t1, action)]], [[(t2, paraphrase)]]],
                    [[[(t1, action)]], [[(t1, action), (t2, paraphrase)]]],
                    [[[(a1, action), (t1, action)]], own[1]]):
        verify(p, packet(p, invalid), False)


def test_derived_fields_are_verified_against_exact_originals():
    p = prepared([(ACTION, LONG)])
    shown, _, _, _ = view(p)
    for changed in ([1, 1], [], None):
        wrong = deepcopy(shown)
        if changed is None:
            del wrong['records'][0]['paired_original_fields']
        else:
            wrong['records'][0]['paired_original_fields'] = changed
        with pytest.raises(ValueError, match='unbound'):
            choices.restore_view(wrong)


@pytest.mark.parametrize('action,thought', [
    (ACTION, ''), ('', LONG), ('水の量を測った。', '水量を記録した。'),
    (ACTION, ACTION), ('水面' * 81 + '。', LONG), ('水面を見た', LONG),
    ('一。二。三。四。五。', LONG), (ACTION, '長' * 160 + 'い。'),
    ('記録した。記録した。', LONG), ('水温を測った。\n蓋を閉じた。', LONG)])
def test_short_equivalent_missing_or_unrepresentable_pairs_keep_free_local_evidence(action, thought):
    p = prepared([(action, thought)])
    shown, orig, _, allowed = view(p)
    assert not choices.compact_action_pairs(orig)
    assert 'paired_original_fields' not in shown['records'][0]
    field = next(f['field'] for f in orig['fields'] if allowed[f['field']])
    verify(p, packet(p, [[[(field, sorted(allowed[field])[0])]]]), True)


def test_history_explicit_updates_and_unrepresentable_owner_keep_existing_allocation():
    p = prepared([(ACTION, LONG)])
    _, orig, _, _ = view(p)
    assert choices.compact_action_pairs(orig)
    for stage in ['LEAF', 'MERGE']:
        assert not choices.compact_action_pairs(dict(orig, history_stage=dict(kind=stage)))
    for key in ['conflicts', 'source_updates', 'unresolved_sources']:
        assert not choices.compact_action_pairs(dict(orig, emlis_source_materials=[dict(record=1, **{key:['記録への補足']})]))
    for extra in [dict(record=1, field=3, source_role='SUPPLEMENTAL_ANSWER', text='量だけを測った。'),
                  dict(record=None, field=3, source_role='USER_ANALYSIS_MAP_CORRECTION', text='今は確認した。')]:
        assert not choices.compact_action_pairs(dict(orig, fields=[*orig['fields'], extra]))
    assert not choices.compact_action_pairs(dict(orig, records=orig['records']+[dict(record=2)]))
    split = deepcopy(orig)
    split['fields'][0]['fragment_is_complete_field'] = False
    assert not choices.compact_action_pairs(split)


def test_native_cannot_close_after_only_action_and_both_unit_layouts_remain_reachable():
    p = prepared([(ACTION, LONG)])
    _, orig, _, _ = view(p)
    a, text, t = choices.compact_action_pairs(orig)[1]
    raw = packet(p, [[[(a, text)], [(t, DETAIL)]]])
    r1, r2 = [compact(u['evidence'][0]) for u in raw['nodes'][0]['units']]
    word = compact(raw)
    state = advance(parser(p, raw), word[:word.index(r1) + len(r1)])
    assert advance(state, ',' + r2 + ']}]}]}').can_end()
    end_unit = advance(state, ']}')
    assert ']' not in end_unit.get_allowed_characters() and ',' in end_unit.get_allowed_characters()
    second = advance(end_unit, ',{"evidence":[')
    with pytest.raises(ValueError):
        advance(second, r1)
    assert advance(second, r2 + ']}]}]}').can_end()


def test_expensive_action_literals_cannot_consume_the_shared_three_reply_budget():
    # Rare Unicode characters can each take several tokens. The old source
    # remains available; only the extra mandatory transcription falls back.
    expensive = ''.join(chr(0x20010 + j) for j in range(150))
    p = prepared([(f'第{i}号の表記{expensive}。', LONG) for i in range(12)])
    shown, original, _, _ = view(p)
    assert not choices.compact_action_pairs(original)
    assert all('paired_original_fields' not in row for row in shown['records'])
    minimal = [[[(f['field'], DETAIL)]] for f in original['fields'] if f['field_path'] == 'memo']
    verify(p, packet(p, minimal), True)
