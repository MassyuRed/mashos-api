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
