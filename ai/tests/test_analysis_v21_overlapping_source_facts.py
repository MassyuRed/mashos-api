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
