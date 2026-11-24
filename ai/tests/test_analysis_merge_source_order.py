"""Versioned history presentation keeps the author's evidence, ordered within each original field."""
import analysis_plan_source_choices as choices


def original(number, path, text, record=1):
    return dict(field=number, field_path=path, source_role='ORIGINAL_INPUT', record=record, text=text,
                fragment_is_complete_field=True, fragment_scalar_range=[0, len(text)])


def unit(*roots):
    return dict(source_mode='RECORDED', evidence=[dict(field=f, quote=q) for f,q in roots])


def test_overlapping_roots_in_two_units_follow_separate_original_fields():
    first = '開場前、係員が受付を開けた。'
    middle = '入口が混んでいたので裏側に回った。'
    last = '閉場後にカメラをしまった。'
    arrived = '受付で入場を記録した。'
    left = '閉場後に会場を出た。'
    fields = [original(1, 'memo_action', arrived + left), original(2, 'memo', first + middle + last)]
    units = [unit((1,left),(2,last)), unit((2,first+middle),(1,arrived),(2,middle))]
    assert choices.ordered_record_sections(fields, units) == [
        ('memo',[first,middle,last]), ('memo_action',[arrived,left])]
    assert choices.record_opening_choices(fields, units) == [first, '記録にある場面']
    # The prior title menu may only contain a later standalone quotation.
    assert choices.source_node_titles(dict(fields=fields), units, [last]) == [last]


def test_incomplete_superseded_and_mixed_record_roots_keep_their_own_contract():
    before, after = '最初に鍵を返した。', '後で封筒を受け取った。'
    field = original(1,'memo',before+after)
    roots = [unit((1,before),(1,after))]
    for changed in [dict(field,fragment_is_complete_field=False),dict(field,supplement='answer')]:
        assert choices.ordered_record_sections([changed],roots) is None
    update=dict(field, field=3, source_role='USER_ANALYSIS_MAP_CORRECTION')
    assert choices.ordered_record_sections([field, update],roots) is None
    other=original(2,'memo',after,record=2)
    assert choices.ordered_record_sections([field,other],[unit((1,before),(2,after))]) is None
    assert choices.ordered_record_sections([field],roots,[['wrong source', after]]) is None


def test_long_selected_range_stays_with_bound_original_offset_and_keeps_its_cut_marks():
    quote = '朝に用意したお守りを机の上へ置いた。' + 'よく確かめながら少しずつ作業したので' * 15 + '終わるのに時間がかかった。'
    late = '帰宅してから控えを書いた。'
    field = original(1, 'memo', quote+late)
    roots = [unit((1,late),(1,quote))]
    chosen=list(choices.source_fact_ranges(quote).values())[-1]
    assert choices.ordered_record_sections([field],roots,[[late,chosen]]) == [('memo',[chosen,late])]
    assert choices.record_opening_choices([field],roots) == ['記録にある場面']


def test_comparison_detail_uses_the_two_chosen_sentences_and_keeps_the_complete_node():
    from dataclasses import replace
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, semantic_admission as core
    from test_analysis_v13_separate_record_titles import stages
    context = '帰宅して机の上を片付けた。'
    asked = '原稿の提出先を問い合わせた。'
    replied = '翌日、提出先の返事が来た。'
    after = '昼食は家で食べた。'
    _, prepared, plan, bodies = stages(context + asked, replied + after)
    nodes = core._semantic_v4_join(plan, bodies)
    for node in nodes:
        del node['node_id']
    left, right = [n['units'][0] for n in nodes]
    left_root, right_root = left['evidence'][0], right['evidence'][0]
    label = asked + '一方、' + replied
    edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u1', 'to_unit': 'n2.u1',
            'label': label, 'relation_kind': 'CONTEXT_CONTRAST'}
    packet = dict(schema_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_SCHEMA, nodes=nodes, edges=[edge],
                  overview=dict(node_refs=['n1', 'n2'], title='原稿の提出先について'))
    prepared = replace(prepared, prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE)
    render = intent_compiler._expand_analysis_semantic_node_local_v3
    options = dict(fact_endpoints=True, mark_record_ownership=True)
    old = render(prepared, packet, **options)
    source = {('n1.u1', 'n2.u1', label): ((left_root['field'], left_root['quote'], asked),
                                           (right_root['field'], right_root['quote'], replied))}
    actual = render(prepared, packet, comparison_sources=source, **options)
    assert actual['nodes'] == old['nodes'] and actual['overview'] == old['overview']
    assert actual['edges'][0]['label'] == old['edges'][0]['label']
    detail = actual['edges'][0]['explanation']
    assert asked in detail and replied in detail and context not in detail and after not in detail
    assert context in old['edges'][0]['explanation'] and after in old['edges'][0]['explanation']


def test_v24_merge_neutral_heading_counts_distinct_mapped_records():
    from dataclasses import replace
    import json

    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, semantic_admission as core
    from test_analysis_merge_transport import source_merge

    notes = ['朝に公園を散歩した。', '昼に図書館で本を借りた。', '夕方に机を片付けた。']
    merged = core._semantic_v4_view(source_merge(notes))
    prepared = replace(merged, prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE)

    def node(*indexes):
        roots = tuple((index, notes[index - 1]) for index in indexes)
        fact = ''.join(quote for _, quote in roots)
        return dict(node_kind='CHOICE_OUTPUT', perspective='SELF', title=fact, meaning='',
                    units=[dict(unit(*roots), fact=fact, unknowns=[])])

    nodes = [node(1, 2), node(2, 3), node(3)]
    material = json.loads(merged.material_json)
    neutral = choices.WholeMapTitle(material, nodes).neutral
    assert neutral == '1件の記録を振り返って'
    authored = '散歩と読書、机の片付け'
    overview = dict(node_refs=['n1', 'n2', 'n3'], title=neutral)
    packet = dict(schema_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_SCHEMA, nodes=nodes,
                  edges=[], overview=overview)
    render = intent_compiler._expand_analysis_semantic_node_local_v3
    assert render(prepared, packet)['overview']['title'] == '3件の記録を振り返って'
    assert packet['overview']['title'] == neutral
    assert render(prepared, dict(packet, overview=dict(overview, title=authored)))['overview']['title'] == authored
