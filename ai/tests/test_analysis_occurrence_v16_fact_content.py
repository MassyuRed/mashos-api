"""Check authored body text, its original record, and literal alternatives through the native decoder and CMEE."""
import json
from copy import deepcopy

import pytest

import analysis_plan_source_choices as source
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_occurrence_v14_visible_closers import stages
from test_analysis_v13_separate_record_titles import wire

PROFILE = core.SEMANTIC_MAP_OCCURRENCE_V16_PROFILE
FIRST = '私は古い鍵を窓口に返した。'
SECOND = '新しい鍵を受け取れる日はまだ聞いていない。'


def example(note=FIRST+SECOND, profile=PROFILE):
    p, plan, nodes = stages(note, profile=profile)
    raw = wire(p, plan, nodes)
    parts = raw['nodes']['n1']['units']['u1']['fact_parts']
    return p, plan, raw, parts, core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)


@pytest.mark.parametrize('value,expected', [
    (',', None), ('、。', None), ('/></fact_parts', None), ('受付した。</fact_parts>', None),
    ('@9', None), ('@0', FIRST+SECOND), ('@1', FIRST), ('@2', SECOND),
    ('返却を済ませ、次の受取日はまだ知らない。', '返却を済ませ、次の受取日はまだ知らない。'),
])
def test_body_choices_are_root_scoped_and_ordinary_authorship_remains_available(value, expected):
    p, plan, raw, parts, msgs = example()
    key, = parts
    parts[key] = value
    saved_wire = deepcopy(raw)
    material = json.loads(msgs[1]['content'])
    assert material['evidence_parts_by_unit']['n1.u1']['e1']['sentence_choices'] == ['@0','@1','@2']
    assert accepts(raw, msgs) == (expected is not None)
    if expected is None:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
    else:
        result = core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
        assert result['nodes']['n1']['units']['u1']['fact_parts'][key] == expected
        lookup = probe._semantic_wire_fact_sources(msgs)
        assert lookup.get(('n1.u1', key, value), value) == expected
    assert raw == saved_wire


def test_identical_local_numbers_select_independent_sources_and_cannot_cross_roots():
    other = ('別の日に写真を撮った。', '棚の様子を確かめた。')
    p, plan, nodes = stages(FIRST+SECOND, ''.join(other), profile=PROFILE)
    raw = wire(p, plan, nodes)
    for n in raw['nodes'].values():
        parts = n['units']['u1']['fact_parts']
        parts[next(iter(parts))] = '@2'
    msgs = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    assert accepts(raw,msgs)
    result = core.admit_semantic_node_local_v4_nodes_response(p,plan,raw)
    assert [next(iter(n['units']['u1']['fact_parts'].values())) for n in result['nodes'].values()] == [SECOND,other[1]]


@pytest.mark.parametrize('value,good', [('○',True),('×',False),('3',True),('</test>',True),('別の言い方',True),('?></other',False),('@1',True)])
def test_source_symbols_markup_and_literal_handles_remain_available(value,good):
    p,plan,raw,parts,msgs=example('欄の○と @1 を確かめた。タグ </test> を読んだ。')
    parts[next(iter(parts))]=value
    assert accepts(raw,msgs)==good
    if good:
        admitted=core.admit_semantic_node_local_v4_nodes_response(p,plan,raw)
        assert next(iter(admitted['nodes']['n1']['units']['u1']['fact_parts'].values()))==value
    else:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(p,plan,raw)


def test_only_complete_selected_sentences_that_fit_can_be_chosen():
    all_source={FIRST, SECOND, '別の長い文を書き添えた。'}
    assert source.fact_sentence_choices(FIRST+SECOND, all_source,len(FIRST))=={'@1':FIRST}
    assert source.fact_sentence_choices(FIRST[1:]+SECOND,all_source,160)=={}
    assert source.fact_sentence_choices(FIRST+SECOND+'一部',all_source,160)=={}
    assert source.fact_sentence_choices(FIRST,all_source,160)=={}


def test_v15_ordinary_parse_preserves_real_punctuation_only_responses():
    p,plan,raw,parts,msgs=example(profile=core.SEMANTIC_MAP_OCCURRENCE_V15_PROFILE)
    parts[next(iter(parts))]=','
    assert accepts(raw,msgs)
    nodes=core.admit_semantic_node_local_v4_nodes_response(p,plan,raw)
    assert next(iter(nodes['nodes']['n1']['units']['u1']['fact_parts'].values()))==','


def fact_value_parser(note=FIRST+SECOND):
    p,plan,raw,parts,msgs=example(note)
    key,=parts
    marker=json.dumps(key,ensure_ascii=False)+':"'
    compact=json.dumps(raw,ensure_ascii=False,separators=(',',':'))
    alphabet=''.join(dict.fromkeys(compact+json.dumps(msgs,ensure_ascii=False)+',<>/x甲字123+'))
    parser=probe.semantic_json_parser(msgs,alphabet)
    start=advance(parser,compact[:compact.index(marker)+len(marker)])
    assert start is not None
    return start


@pytest.mark.parametrize('before',['/', '<x', '</x'])
def test_stop_unsourced_tag_at_its_first_irreversible_character(before):
    state=advance(fact_value_parser(),before)
    assert state is not None and '>' not in state.get_allowed_characters()
    escaped=advance(state,r'\u003')
    assert escaped is not None and not set('eE').intersection(escaped.get_allowed_characters())
    recovered=advance(state,' という表記')
    assert recovered is not None and '"' in recovered.get_allowed_characters()


def test_supporting_markup_at_source_can_close_and_finish():
    state=advance(fact_value_parser('文字列<x/>があった。別の欄は空だった。'),'記録の<x/')
    assert state is not None and '>' in state.get_allowed_characters()
    assert '"' in advance(state,r'\u003e').get_allowed_characters()


def test_last_scalar_reserves_content_in_both_direct_and_escaped_spellings():
    state=advance(fact_value_parser(),','*159)
    assert state is not None
    assert ',' not in state.get_allowed_characters() and '甲' in state.get_allowed_characters()
    # No code point in U+0020..U+002F adds licensed content in this source.
    esc=advance(state,r'\u00')
    assert esc is not None and '2' not in esc.get_allowed_characters()
    assert '"' in advance(state,r'\u7532').get_allowed_characters()
    # A supplementary CJK letter also occupies one scalar.
    assert '"' in advance(state,r'\ud840\udc00').get_allowed_characters()
