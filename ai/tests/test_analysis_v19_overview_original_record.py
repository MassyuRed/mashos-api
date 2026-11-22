"""A shared overview may cite more than one record even when the PLAN chose other roots."""
import json
import pytest
import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_v16_source_title_endings import prepare
from test_analysis_v18_overview_source_coverage import check


def selected(version, full, excerpts):
    p, plan, nodes = prepare(full, getattr(core, f'SEMANTIC_MAP_OCCURRENCE_V{version}_PROFILE'))
    for item, quote in zip(plan['nodes'], excerpts, strict=True):
        roots = item['units'][0]['evidence']
        roots[0]['quote'] = quote
        node = nodes['nodes'][item['node_id']]
        node['units']['u1']['fact_parts'] = {core._semantic_fact_part_key(roots, 0): quote}
        node['title'] = quote
    nodes['plan_sha256'] = core.semantic_map_hash(plan)
    return p, plan, nodes


@pytest.mark.parametrize('version,expected', [(18, True), (19, False)])
def test_borrowing_an_unselected_original_sentence_or_node_title(version, expected):
    original = '椅子を受け取った。'
    day_one = '預かり票を書いた。順番を待った。'
    day_two = '受付票をしまった。控えを返した。'
    p, plan, nodes = selected(version, (day_one, original + day_two), (day_one, day_two))
    refs = ['n1', 'n2']
    for node_title in (original, '受取の控え'):
        nodes['nodes']['n2']['title'] = node_title
        check(p, plan, nodes, refs, original, expected)
        check(p, plan, nodes, refs, day_two + '、' + original, expected)
    check(p, plan, nodes, ['n2'], original, True)
    check(p, plan, nodes, refs[::-1], '預かり票を書いた。' + original, True)
    check(p, plan, nodes, refs, '預け入れから受領まで', True)
    # An authored overview can share a generic heading with a single node.
    nodes['nodes']['n1']['title'] = '受け渡しの記録'
    check(p, plan, nodes, refs, '受け渡しの記録', True)


@pytest.mark.parametrize('version,expected', [(18, False), (19, True)])
def test_a_plan_literal_can_be_shared_by_another_records_unselected_original(version, expected):
    shared = '同じ表示を確かめた。'
    other = '担当者から控えをもらった。'
    p, plan, nodes = selected(version, (shared, other + shared + shared), (shared, other))
    check(p, plan, nodes, ['n2', 'n1'], shared, expected)


@pytest.mark.parametrize('role,fragment', [('SUPPLEMENTAL_ANSWER', True), ('USER_ANALYSIS_MAP_CORRECTION', True),
                                           ('ORIGINAL_INPUT', False)])
def test_partial_or_unassigned_fields_never_lift_original_record_restrictions(role, fragment):
    shared = '登録した。'
    p, plan, _ = selected(19, (shared, '用紙を送った。'), (shared, '用紙を送った。'))
    material = json.loads(p.material_json)
    material['fields'].append(dict(field=9, record=2, text=shared, source_role=role, fragment_is_complete_field=fragment))
    units = [n['units'][0] for n in plan['nodes']]
    blocked = choices.one_sided_source_titles(material, units, compare_end_marks=True)
    phrases = choices.OverviewSourcePhrases(material, units, restricted_titles=blocked, include_original_fields=True)
    assert choices.source_title_key(shared) in phrases.restricted_titles
    assert phrases.omits_record(shared)


def test_originals_of_unselected_nodes_and_embedded_quotations_are_not_assigned():
    secret = '返答を受けた。'
    texts = ('配布した。係員から「' + secret + '」と伝えられた。', '封筒を持ち帰った。', '鍵を受け取った。（別件。追記。）' + '外に出た。' + secret)
    p, plan, nodes = selected(19, texts, ('配布した。', '封筒を持ち帰った。', '鍵を受け取った。'))
    check(p, plan, nodes, ['n1', 'n2'], secret, True)
    check(p, plan, nodes, ['n1', 'n2', 'n3'], secret, False)
