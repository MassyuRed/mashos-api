"""A whole-map overview refers to all its nodes and distinguishes independent records."""
import json

import pytest

from analysis_plan_source_choices import WholeMapTitle
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_v16_source_title_endings import prepare
from test_analysis_v18_overview_source_coverage import relation


V19, V20 = core.SEMANTIC_MAP_OCCURRENCE_V19_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V20_PROFILE
NOTES = ('下書きを保存した。', '翌日、場所の予約を確認した。')


@pytest.mark.parametrize('version,refs,title,admitted', [
    (V19, ['n1'], '保存した下書き', True),
    (V20, ['n1'], '保存した下書き', False),
    (V20, ['n1', 'n2'], '保存した下書き', False),
    (V20, ['n1', 'n2'], '2件の記録を振り返って、保存した下書き', False),
    (V20, ['n2', 'n1'], '下書きの保存から翌日の予約確認まで', True),
    (V20, ['n1', 'n2'], '2件の記録を振り返って', True),
])
def test_distinct_days_under_a_whole_map_heading(version, refs, title, admitted):
    p, plan, nodes = prepare(NOTES, version)
    value, messages = relation(p, plan, nodes, refs, title)
    assert accepts(value, messages) is admitted
    if admitted:
        assert core.semantic_node_local_v4_relations(p, plan, nodes, value)['overview'] == value['overview']
    else:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.semantic_node_local_v4_relations(p, plan, nodes, value)


def test_identical_records_still_have_a_complete_heading_path_without_inventing_an_event():
    p, plan, nodes = prepare(('鍵を確認した。', '鍵を確認した。'), V20)
    value, messages = relation(p, plan, nodes, ['n1', 'n2'], '2件の記録を振り返って')
    assert accepts(value, messages)
    assert core.semantic_node_local_v4_relations(p, plan, nodes, value)['overview'] == value['overview']


def test_unselected_originals_and_corrections_cannot_supply_another_records_witness():
    original = lambda i, text: dict(field=i, record=i, source_role='ORIGINAL_INPUT', text=text)
    material = {'fields': [original(1, '下書きを保存した。'), original(2, '予約した。下書きを保存した。'),
        dict(field=3, record=1, source_role='USER_ANALYSIS_MAP_CORRECTION', text='曇りだった。')]}
    nodes = [dict(units=[dict(evidence=[dict(field=i, quote=quote)])]) for i, quote in
             enumerate(('下書きを保存した。', '予約した。', '曇りだった。'), 1)]
    scope = WholeMapTitle(material, nodes)
    assert scope.count == 2 and scope.accepts(scope.neutral)
    assert not scope.accepts('曇りの日の下書きと予約')


def test_late_unsupported_prefix_still_has_a_bounded_source_supported_continuation():
    p, plan, nodes = prepare(NOTES, V20)
    value, messages = relation(p, plan, nodes, ['n1', 'n2'], '2件の記録を振り返って')
    wire = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    prefix, rest = wire.split(value['overview']['title'])
    alphabet = ''.join(dict.fromkeys(wire + json.dumps(messages, ensure_ascii=False) + 'あ・'))
    state = advance(probe.semantic_json_parser(messages, alphabet), prefix)
    title = ''
    while 'あ' in state.get_allowed_characters():
        state = state.add_character('あ')
        title += 'あ'
    while '"' not in state.get_allowed_characters():
        char = state.get_allowed_characters()[0]
        title += char
        state = state.add_character(char)
    assert title and len(title) <= 80 and advance(state, rest).can_end()
    value['overview']['title'] = title
    assert core.semantic_node_local_v4_relations(p, plan, nodes, value)['overview']['title'] == title
