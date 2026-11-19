"""Keep every original fact while projecting overlapping complete, bound source sentences once."""
from copy import deepcopy

import pytest

from cocolon_meaning_experience_engine.cores.analysis.intent_compiler import _node_unique_fixed_facts
from test_analysis_v18_repeated_bound_facts import unit

A = '雨が降った。'
B = '外出はしなかった。'
C = '夕方にはやんだ。'


def test_whole_repeat_alone_or_paired_does_not_repeat_in_text():
    units = [unit((1, A), (1, B)), unit((1, A+B), (1, C))]
    original = deepcopy(units)
    parts = [(A, B), (A+B, C)]
    assert _node_unique_fixed_facts(units, parts, {1: 1}) == [A+B, A+B+C]
    assert _node_unique_fixed_facts(units, parts, {1: 1}, source_sentences={1: {A, B, C}}) == [A+B, C]
    assert units == original


@pytest.mark.parametrize('other_field,mode,extra,unique', [
    (1, 'RECORDED', B+C, {A, B, C}),
    (1, 'PERSON_WISH', A+B, {A, B}),
    (2, 'RECORDED', A+B, {A, B}),
    (1, 'RECORDED', A+B, {B}),  # A occurs more than once in the original.
])
def test_preserve_new_fact_other_mode_other_field_and_ambiguous_source(other_field, mode, extra, unique):
    units = [unit((1, A), (1, B)), unit((other_field, extra), mode=mode)]
    parts = [(A, B), (extra,)]
    assert _node_unique_fixed_facts(units, parts, {1: 1, 2: 1},
                                    source_sentences={1: unique, 2: unique}) == [A+B, extra]


def test_relative_fragments_are_not_removed_from_a_larger_sentence_or_quote():
    whole = '「'+A+B+'」と聞いた。'
    units = [unit((1, whole)), unit((1, A), (1, B))]
    assert _node_unique_fixed_facts(units, [(whole,), (A, B)], {1: 1},
                                    source_sentences={1: {whole}}) == [whole, A+B]


def test_selected_action_sentences_follow_source_positions_and_keep_other_field_slots():
    first = '家族が担当者に電話したと聞いた。'
    second = '返事を待って資料を見た。'
    third = '予約はまだしていない。'
    thought = '私はもう少し調べたいと思った。'
    units = [unit((2, third), (1, thought)), unit((2, first+second), (2, third))]
    original = deepcopy(units)
    parts = [(third, thought), (first+second, third)]
    original_fields = {1: {thought}, 2: {first, second, third}}
    ordered = {2: {first: 0, second: len(first), third: len(first+second)}}
    def project(order=None):
        return _node_unique_fixed_facts(units, parts, {1: 1, 2: 1},
            source_sentences=original_fields, separate_sentences=True, action_sentence_order=order)
    assert project() == [third, thought, first, second]
    assert project(ordered) == [first, thought, second, third]
    assert original == units


def test_unselected_action_sentences_never_enter_a_map_and_partial_quotes_do_not_move():
    units = [unit((1, C), (1, '降った')), unit((1, A))]
    result = _node_unique_fixed_facts(units, [(C, '降った'), (A,)], {1: 1},
        source_sentences={1: {A, B, C}}, separate_sentences=True, action_sentence_order={1: {A: 0, B: 5, C: 12}})
    assert result == [A, '降った', C]


def test_original_sentence_positions_are_scoped_to_a_single_record():
    units = [unit((1, C)), unit((2, B), (1, A))]
    result = _node_unique_fixed_facts(units, [(C,), (B, A)], {1: 1, 2: 2},
        source_sentences={1: {A, C}, 2: {B}}, separate_sentences=True, action_sentence_order={1: {A: 0, C: 4}})
    assert result == [C, B+A]


def test_later_action_used_as_heading_remains_at_its_position_in_new_full_text():
    from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import analysis_semantic_projection_text
    from analysis_cumulative_service import _saved_projection_text_matches
    projection = {'wire_kind': 'watashi.map.v3', 'overview': {'title': '全体', 'summary': ''}, 'edges': [],
        'nodes': [{'node_ref': 'n1', 'summary': B, 'title': C, 'explanation': '\n'.join([A, B, C]),
                   'context': [], 'unknowns': []}]}
    old = analysis_semantic_projection_text(projection, compact_source_captions=True)
    new = analysis_semantic_projection_text(projection, compact_source_captions=True, source_ordered_detail=True)
    assert old.splitlines() == ['全体', '', C, B, A]
    assert new.splitlines() == ['全体', '', C, A, B, C]
    assert _saved_projection_text_matches(projection, old) and _saved_projection_text_matches(projection, new)
    assert not _saved_projection_text_matches(projection, new + '未実施の発注を断定した。')
