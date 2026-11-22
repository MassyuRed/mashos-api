"""Carry independent qualified source accounts from PLAN to the immutable fact slots."""
from copy import deepcopy

import pytest

import analysis_plan_source_choices as source
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_occurrence_v17_record_owners import packet, verify
from test_analysis_occurrence_v18_compact_originals import prepared


V23 = core.SEMANTIC_MAP_OCCURRENCE_V23_PROFILE
V24 = core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
EARLY = '担当者は会場の変更を望んでいたが、私は代理で手続きしたわけではない。'
LATE = '担当者が新しい申請を提出したかは聞いていない。'
PAIRS = [('席を確保した。担当者の分は申し込んでいない。', '自分の席を確保した。' + EARLY),
         ('本人宛の返事を開いた。担当者の申請は不明。', '自分の整理番号が届いた。' + LATE)]


@pytest.mark.parametrize('version,expected', [(V23, True), (V24, False)])
def test_self_only_selection_requires_both_accounts_in_the_new_profile(version, expected):
    p = prepared(PAIRS, version)
    self_only = [[[(1, '自分の席を確保した。')]], [[(3, '自分の整理番号が届いた。')]]]
    verify(p, packet(p, self_only), expected)
    if version == V24:
        for first, second in ((True, False), (False, True)):
            partial = deepcopy(self_only)
            if first:
                partial[0][0].append((1, EARLY))
            if second:
                partial[1][0].append((3, LATE))
            verify(p, packet(p, partial), False)


def test_separate_or_contiguous_source_choices_keep_both_clocks_and_full_statements():
    p = prepared(PAIRS, V24)
    other_node = [[[(1, '自分の席を確保した。')]], [[(3, '自分の整理番号が届いた。')]],
                  [[(1, EARLY), (3, LATE)]]]
    verify(p, packet(p, other_node), True)
    for separate in (False, True):
        roots = [[[(1, '自分の席を確保した。'), (1, EARLY)]],
                 [[(3, '自分の整理番号が届いた。'), (3, LATE)]]] if separate else [
                     [[(1, PAIRS[0][1])]], [[(3, PAIRS[1][1])]]]
        restored = verify(p, packet(p, roots), True)
        _, material, _, _ = view(p)
        fixed = core._semantic_node_fact_sources(restored, material, V24)
        assert any(EARLY in quote for _, quote in fixed.values())
        assert any(LATE in quote for _, quote in fixed.values())


@pytest.mark.parametrize('old,new', [
    ('担当者', 'Alex'), ('担当者', '調整係'), ('担当者', 'ミナさん'), ('担当者', '配送会社'),
])
def test_verbatim_topic_does_not_require_kinship_names_or_assigned_personhood(old, new):
    notes = [(a.replace(old, new), b.replace(old, new)) for a, b in PAIRS]
    shown, material, _, _ = view(prepared(notes, V24))
    selected = source.repeated_qualified_topics(material['fields'])
    assert selected == {1: EARLY.replace(old, new), 2: LATE.replace(old, new)}
    ranges = shown['whole_plan_source_ranges']
    assert len(ranges) == len(selected)
    for row in ranges:
        field = next(f for f in material['fields'] if f['field'] == row['field'])
        start, end = row['scalar_range']
        assert selected[field['record']] == field['text'][start:end]



@pytest.mark.parametrize('notes', [
    [PAIRS[0]],
    [(PAIRS[0][0], PAIRS[0][1] + '担当者はその日に鍵を渡していない。'), PAIRS[1]],
    [PAIRS[0], (PAIRS[1][0].replace('担当者', '代理人'), PAIRS[1][1])],
    [PAIRS[0], (PAIRS[1][0].replace('申請は不明', '申請は完了'), PAIRS[1][1])],
    [PAIRS[0], (PAIRS[1][0], '自分の整理番号が届いた。「' + LATE + '」と書かれていた。')],
    [(a.replace('担当者', '私'), b.replace('担当者', '私')) for a, b in PAIRS],
])
def test_no_role_inference_from_unmatched_names_one_record_quotes_or_first_person(notes):
    _, material, _, _ = view(prepared(notes, V24))
    assert not source.repeated_qualified_topics(material['fields'])


def test_excerpts_history_and_unresolved_updates_do_not_create_topic_requirements():
    _, material, _, _ = view(prepared(PAIRS, V24))
    owners = source.record_plan_owners(material)
    for flags in ({'history_stage': {'kind': 'LEAF'}}, {'map_corrections': [{}]},
                  {'emlis_source_materials': [{'unresolved_sources': ['open']}]}):
        assert not source.whole_plan_sources(dict(material, **flags), owners)
    incomplete = deepcopy(material)
    incomplete['fields'][0]['fragment_is_complete_field'] = False
    assert not source.whole_plan_sources(incomplete, owners)


def test_long_option_that_can_hide_one_witness_preserves_previous_choices_for_both_days():
    long_phrase = ('あ' * 153) + '。'
    notes = [(PAIRS[0][0], long_phrase + EARLY), PAIRS[1]]
    _, material, _, _ = view(prepared(notes, V24))
    assert not source.whole_plan_sources(material, source.record_plan_owners(material))


def test_only_map_generation_selects_the_new_profile(monkeypatch):
    import analysis_if_model_source as if_source
    import analysis_model_source as model_source
    from test_analysis_event_plan_model_alias import environment

    environment(monkeypatch, model=model_source.SEMANTIC_OCCURRENCE_V24_MODEL)
    assert model_source.analysis_model_prompt_version(model_source.application_analysis_model_source()) == V24
    assert if_source.application_analysis_if_model_source().model == model_source.SEMANTIC_EVENT_PLAN_BASE_MODEL
    environment(monkeypatch, model=model_source.SEMANTIC_OCCURRENCE_V23_MODEL)
    assert model_source.analysis_model_prompt_version(model_source.application_analysis_model_source()) == V23
