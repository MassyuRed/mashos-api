"""Separate source selections from summary text and keep serialization bound to its source."""
from copy import deepcopy
import json

import pytest

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_occurrence_v16_fact_content import FIRST, SECOND, example


V18, V19 = core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V19_PROFILE
LONG = ('記録表を開いたところ、' + '端の段に小さな傷があり、' * 14
        + '中央で測った値は3.5で、30分後にもう一度記録することにした。')
SUMMARY = '中央の値は3.5だった。30分後にもう一度記録する予定にした。'


def verify(source, text, expected, profile=V19):
    p, plan, raw, parts, messages = example(source, profile=profile)
    key, = parts
    if len(source) > 80:
        raw['nodes']['n1']['title'] = '記録表の確認'
    parts[key] = text
    original = deepcopy(raw)
    assert accepts(raw, messages) == (expected is not None)
    if expected is None:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
    else:
        closed = core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
        assert closed['nodes']['n1']['units']['u1']['fact_parts'][key] == expected
    assert original == raw


@pytest.mark.parametrize('selection,expected', [('@0', FIRST+SECOND), ('@1', FIRST), ('@2', SECOND),
    ('@8', None), (FIRST, None), ('返却は終わり、次回日は分からない。', None), (",'後の欄':2,", None)])
def test_complete_compact_root_has_only_local_source_choices(selection, expected):
    verify(FIRST+SECOND, selection, expected)


def test_v18_saved_authoring_contract_still_accepts_the_prior_free_summary():
    summary = '返却は終わり、次回日は分からない。'
    verify(FIRST+SECOND, summary, summary, profile=V18)


@pytest.mark.parametrize('raw', [",'room:/次の資料':2,", ",'next'/別の欄の説明", ",'next': '受付済み。','remaining': [",
    ',{17,18},', '次の値は{17,18}だった。', 'この表から、\'result\':4, と判断した。', '915'])
def test_a_long_root_cannot_use_unwitnessed_object_keys_or_numeric_notation(raw):
    verify(LONG, raw, None)


@pytest.mark.parametrize('text', [SUMMARY, '3.5', '確認は30分後。', '「中央の値」を記録した。'])
def test_an_unabridged_root_over_budget_keeps_independent_natural_authorship(text):
    verify(LONG, text, text)


@pytest.mark.parametrize('literal,display', [
    ("設定欄は{'panel':3}だった。", "設定欄を{'panel':3}と記録した。"),
    ('数学の記号は{17,18}だった。', '確認した集合は{17, 18}だった。'),
    ('測定比は3:2で、1/2を残した。', '3:2'), ('メモには「赤」と書いた。', '「赤」と記した。'),
    ("原文に ,'key'/ と書かれている。", ",'key'/")])
def test_numbers_punctuation_quotations_and_literal_data_keep_their_own_source(literal, display):
    # Keep the entire source one over-budget free-text root.
    note = LONG[:-1] + ' なお' + literal
    verify(note, display, display)


def test_prefix_cannot_complete_an_unsourced_member_in_either_json_spelling():
    p, plan, raw, parts, messages = example(LONG, profile=V19)
    key, = parts
    parts[key] = SUMMARY
    wire = json.dumps(raw, ensure_ascii=False, separators=(',', ':'))
    before, _ = wire.split(json.dumps(SUMMARY, ensure_ascii=False), 1)
    prefix = before + '",'
    alphabet = ''.join(dict.fromkeys(wire + " abcdefABCDEF0123456789/'{}[]:,\\u"))
    state = advance(probe.semantic_json_parser(messages, alphabet), prefix)
    assert "'" not in state.get_allowed_characters()
    assert '{' not in state.get_allowed_characters()
    assert '"' not in advance(state, '\\').get_allowed_characters()
    assert '7' not in advance(state, r'\u002').get_allowed_characters()
    # A leading comma can still be followed by ordinary words.
    assert 'a' in state.get_allowed_characters()


def parser_at_fact(source, alphabet=''):
    p, plan, raw, parts, messages = example(source, profile=V19)
    key, = parts
    raw['nodes']['n1']['title'] = '記録表の確認'
    parts[key] = SUMMARY
    wire = json.dumps(raw, ensure_ascii=False, separators=(',', ':'))
    before, after = wire.split(json.dumps(SUMMARY, ensure_ascii=False), 1)
    alphabet = ''.join(dict.fromkeys(wire + alphabet + "abc'/{}[]0123456789,.-: \\uABCDEF"))
    return advance(probe.semantic_json_parser(messages, alphabet), before + '"'), '"' + after


@pytest.mark.parametrize('opening,delimiter,escape,recovery', [
    ('記録は{17,18', '}', r'\u007', 'を見る条件だった。'),
    ('記録は[17,18', ']', r'\u005', 'を見る条件だった。'),
    ("記録は 'item'", ':', r'\u003', ' と書かれていた。')])
def test_free_field_has_a_complete_nodes_path_after_ambiguous_structural_prefix(opening, delimiter, escape, recovery):
    state, rest = parser_at_fact(LONG, opening + delimiter + recovery + 'abcdef')
    state = advance(state, opening)
    assert delimiter not in state.get_allowed_characters()
    pending = advance(state, escape)
    assert format(ord(delimiter), 'x')[-1] not in pending.get_allowed_characters()
    assert advance(state, recovery + rest).can_end()


def test_owned_notation_can_finish_even_at_its_last_literal_character():
    note = LONG[:-1] + "、記号は ,'one'/。"
    state, rest = parser_at_fact(note, ",'one'/。")
    state = advance(state, ",'one'/。")
    assert '\\' not in state.get_allowed_characters()
    assert advance(state, rest).can_end()


def test_source_numeric_and_at_literals_preserve_their_exact_bound_values():
    verify(LONG[:-1] + '、棚のラベルは@81だった。', '@81', '@81')
    verify(LONG[:-1] + '、棚のラベルは@81だった。', '@82', None)


def test_last_character_leaves_both_direct_and_unicode_paths_to_valid_prose():
    state, rest = parser_at_fact(LONG, '字')
    # A number on its own must be source-bound, but adding a letter can still
    # yield prose. The final character must be checked in each wire spelling.
    state = advance(state, '9' * 159)
    assert '"' not in state.get_allowed_characters() and '9' not in state.get_allowed_characters()
    assert '字' in state.get_allowed_characters()
    assert advance(state, r'\u5b57' + rest).can_end()
