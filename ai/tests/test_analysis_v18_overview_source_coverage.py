"""Native decoding and semantic publication retain the selected records of a literal overview."""
import json

import pytest

import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts
from test_analysis_v16_source_title_endings import prepare


def relation(prepared, plan, nodes, refs, title):
    joined = core._semantic_v4_join(plan, nodes)
    value = dict(schema_version=core._semantic_v4_schema('RELATIONS'),
        nodes_sha256=core.semantic_map_hash(joined), qualification_review={},
        edges=[], overview=dict(node_refs=refs, title=title))
    messages = core.semantic_node_local_v4_messages(prepared, 'RELATIONS', plan=plan, nodes=nodes)
    return value, messages


def check(prepared, plan, nodes, refs, title, expected):
    value, messages = relation(prepared, plan, nodes, refs, title)
    assert accepts(value, messages) is expected
    if expected:
        assert core.semantic_node_local_v4_relations(prepared, plan, nodes, value)['overview'] == value['overview']
    else:
        with pytest.raises(core.AnalysisSemanticMapError, match='relations_invalid'):
            core.semantic_node_local_v4_relations(prepared, plan, nodes, value)


@pytest.mark.parametrize('version,refs,title,expected', [
    (17, ['n1', 'n2'], '部屋を確認した。、案内を送った。', True),
    (18, ['n1', 'n2'], '部屋を確認した。、案内を送った。', False),
    (18, ['n2', 'n1'], '案内を送った／部屋を確認した', False),
    (18, ['n1', 'n2'], '部屋を確認した案内を送った', False),
    (18, ['n2'], '部屋を確認した。、案内を送った。', True),
    (18, ['n1', 'n2'], '下書きを保存した。部屋を確認した。', True),
    (18, ['n2', 'n1'], '下書きを保存した。翌日、確認した部屋で参加者に案内した。', True),
    (18, ['n1', 'n2'], '準備から場所の確認と案内まで', True),
])
def test_heading_can_join_both_records_or_use_its_own_words(version, refs, title, expected):
    profile = getattr(core, f'SEMANTIC_MAP_OCCURRENCE_V{version}_PROFILE')
    prepared, plan, nodes = prepare(('下書きを保存した。', '部屋を確認した。案内を送った。'), profile)
    check(prepared, plan, nodes, refs, title, expected)


def test_three_way_overview_distinguishes_omitted_and_shared_records():
    notes = ('荷物を預けた。控えをしまった。', '到着を確かめた。受領を確認した。', '受領を確認した。宛名を確かめた。')
    p, plan, nodes = prepare(notes, core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE)
    check(p, plan, nodes, ['n1', 'n2', 'n3'], '控えをしまった。到着を確かめた。', False)
    check(p, plan, nodes, ['n1', 'n2', 'n3'], '控えをしまった。受領を確認した。', True)
    check(p, plan, nodes, ['n2', 'n3'], '受領を確認した。', True)


def test_supplement_does_not_invent_one_original_owner_or_match_inside_a_report():
    p, plan, _ = prepare(('室温は12.5度だった。', '受付に着いた。', '店員は「到着した。確認した」と言った。'),
        core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE)
    material = json.loads(p.material_json)
    units = [node['units'][0] for node in plan['nodes']]
    material['fields'][2]['source_role'] = 'USER_ANALYSIS_MAP_SUPPLEMENT'
    sources = choices.OverviewSourcePhrases(material, units)
    assert sources.omits_record('室温は12.5度だった。／室温は12.5度だった。')
    assert not sources.omits_record('室温は125度だった／室温は125度だった')
    assert not sources.omits_record('室温は12.5度だった。店員は「到着した。確認した」と言った。')
    assert not sources.omits_record('到着した。室温は12.5度だった。')


def test_native_keeps_valid_continuation_at_title_length_limit():
    word = '棚を確かめた'
    p, plan, nodes = prepare(('別の部品を用意した。', word + '。'), core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE)
    prefix = (word + '。') * 10 + word
    prefix += '、' * (79 - len(prefix))
    assert len(prefix) == 79
    check(p, plan, nodes, ['n1', 'n2'], prefix + '。', False)
    check(p, plan, nodes, ['n1', 'n2'], prefix + '後', True)
