"""Whole admitted-source model review for retained spans and typed operators.

Fictional CPU candidates; no model, runtime, source admission or native author
is changed. End-to-end assertions use the actual Engine/receipt/S7 owners.
"""
from dataclasses import replace

import pytest

from cocolon_meaning_experience_engine.piece_semantic_admission import piece_model_source_plan
from piece_v2_content_policy import (_piece_model_operator_tree,
    validate_source_meaning_preservation)
from piece_v2_contract import PieceContractError
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_finite_scope import request
from test_piece_model_narrator_voice import evaluate


PAIRS = (
    ('私は受付係に発表会の開始時刻を確認しました。',
     '私は受付係に発表会の開始時刻を確認した。'),
    ('私は受付係に発表会の開始時刻を確認しませんでした。',
     '私は受付係に発表会の開始時刻を確認しなかった。'),
    ('私は、雨が降っているので、まだ完成していない看板の数を帳面に書きました。',
     '私は、雨が降っているので、まだ完成していない看板の数を帳面に書いた。'),
    ('私は、広場で使う椅子の数と、決まっていない配置を帳面に書きました。',
     '私は、広場で使う椅子の数と、決まっていない配置を帳面に書いた。'),
    ('急いで選ぶと、読めていない箇所を飛ばしてしまう気がします。',
     '急いで選ぶと、読めていない箇所を飛ばしてしまう気がする。'),
    ('私は、今回は参加をやめたいわけではありません。',
     '私は、今回は参加をやめたいわけではない。'),
    ('私は散歩が好きですが、今は遠出より近くの道をゆっくり歩きたいです。',
     '私は散歩が好きだが、今は遠出より近くの道をゆっくり歩きたい。'),
    ('私は、準備を任されることは嬉しいですが、自分で確かめる時間を大切にしたいです。',
     '私は、準備を任されることは嬉しいが、自分で確かめる時間を大切にしたい。'),
)

# Existing source admission needs a complete expressive core for these
# otherwise retained context sentences. This is explicitly part of each
# fictional input, not a generated addition or an expansion of admission.
CONTEXT = '私は図を描く時間を大切にしたいです。'


@pytest.mark.parametrize('before,after', PAIRS)
@pytest.mark.parametrize('field', ('memo', 'memo_action'))
def test_whole_admitted_source_reaches_exact_model_artifact(before, after, field):
    saved = source(CONTEXT + before, field=field)
    frozen = saved.saved_original_json
    out = evaluate(saved, [CONTEXT + after])
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (CONTEXT + after,)
    assert saved.saved_original_json == frozen
    meaning, plan = piece_model_source_plan(request(saved))
    # This expansion is opt-in model review only. Native KEEP stays literal.
    if all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in plan.duties):
        with pytest.raises(PieceContractError):
            validate_source_meaning_preservation(meaning, plan, out.artifact)
    validate_source_meaning_preservation(meaning, plan, out.artifact, _model_register=True)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_retained_narrator_cases_and_two_fields_never_borrow_each_other(speaker):
    memo = speaker + 'は受付係に集合時刻を確認しました。'
    action = CONTEXT + speaker + 'は、残っている係の名前を帳面に書きました。'
    good = [memo.replace('しました', 'した'), action.replace('書きました', '書いた')]
    saved = source(memo, field='memo', other=action)
    assert evaluate(saved, good).artifact is not None
    for blocks in (good[::-1], [good[0], good[1].replace(speaker + 'は', '', 1)],
                   [good[0].replace('受付係に', '受付係から'), good[1]]):
        assert evaluate(saved, blocks).artifact is None


MUTATIONS = (
    (0, '受付係に', '先生に'), (0, '受付係に', '受付係から'),
    (0, '確認した', '確認しなかった'), (0, '確認した', '確認できた'),
    (0, '確認した', '確認された'), (0, '確認した', '確認していた'),
    (0, '確認した', '確認したい'), (0, '確認した', '確認する'),
    (0, '私は', '僕は'), (0, '開始時刻', '終了時刻'),
    (2, '降っている', '降った'), (2, '完成していない', '完成した'),
    (2, 'ので', 'のに'), (2, '書いた', '書かなかった'),
    (2, '書いた', '書きたい'), (2, '書いた', '書かれた'),
    (2, '書いた', '書いていた'), (2, '帳面に', '帳面から'),
    (3, '決まっていない', '決まった'), (3, '椅子の数', '机の数'),
    (4, '読めていない', '読めた'), (4, '気がする', '気がした'),
    (4, '気がする', ''), (4, '急いで選ぶと', '急いで選ぶので'),
    (5, 'やめたいわけではない', 'やめたくない'),
    (5, 'やめたいわけではない', 'やめたい'),
    (5, 'わけではない', 'わけではなかった'),
    (6, '好きだが', '好きなので'), (6, '好きだが', '苦手だが'),
    (6, '好きだが', '好きが'),
    (6, '散歩が', '読書が'), (6, '遠出より', '遠出も'),
    (7, '任される', '任せる'), (7, 'ことは', 'ことが'),
    (7, '嬉しいが', '嬉しくないが'), (7, '嬉しいが', '嬉しかったが'),
    (7, '嬉しいが', '嬉しいので'), (7, '大切にしたい', '大切にしたくない'),
)


@pytest.mark.parametrize('index,old,new', MUTATIONS)
def test_changed_meaning_inside_any_retained_or_typed_span_is_refused(index, old, new):
    before, after = PAIRS[index]
    assert old in after
    damaged = after.replace(old, new, 1)
    saved = source(CONTEXT + before, field='memo')
    assert evaluate(saved, [CONTEXT + after]).artifact is not None
    assert evaluate(saved, [CONTEXT + damaged]).artifact is None


def test_original_and_opted_in_answer_keep_distinct_source_roles():
    original, visible_original = PAIRS[3]
    answer = PAIRS[7][0] + PAIRS[5][0]
    visible_answer = PAIRS[7][1] + PAIRS[5][1]
    saved = refined_source(original=original, answer=answer)
    out = evaluate(saved, [visible_original, visible_answer])
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (visible_original, visible_answer)
    for blocks in ([visible_answer, visible_original],
                   [visible_original + visible_answer, '私は読書が好きだ。']):
        assert evaluate(saved, blocks).artifact is None
    with pytest.raises(ValueError, match='piece_model_refined_binding'):
        evaluate(replace(saved, opted_in=False), [visible_original, visible_answer])


@pytest.mark.parametrize('before,after', PAIRS[2:6])
def test_existing_standalone_source_qualification_is_not_expanded(before, after):
    out = evaluate(source(before, field='memo'), [after])
    assert out.artifact is None
    assert out.reason_codes == ('expression_meaning_not_admitted',)


@pytest.mark.parametrize('before,after', (
    ('私は「時刻を確認しました」と紙に書きました。', '私は「時刻を確認した」と紙に書いた。'),
    ('私は（時刻を確認しました）と紙に書きました。', '私は（時刻を確認した）と紙に書いた。'),
    ('湿気がします。', '湿気がする。'),
    ('私は手を動かしました。', '私は手を動かした。'),
))
def test_unproved_quote_nominal_boundary_and_new_kana_verb_stay_unassessed(before, after):
    left, right = _piece_model_operator_tree(before), _piece_model_operator_tree(after)
    assert left is None or right is None or left != right


def test_new_tree_does_not_erase_clause_order_or_invent_an_extra_sentence():
    before, after = PAIRS[6]
    for damaged in ('今は遠出より近くの道をゆっくり歩きたい。私は散歩が好きだ。',
                    after + '私は毎日歩く。', after.replace('が、', 'が。')):
        assert evaluate(source(before, field='memo'), [damaged]).artifact is None
