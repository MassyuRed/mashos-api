"""Existing personal-evaluation assets read actual model prose, not its plan.

Fictional CPU candidates; no provider call or general Japanese quality claim.
Expected equivalents/changes are written independently of the source grammar.
"""
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from piece_v2_content_policy import _piece_model_read_block
from test_cmee_piece_finite_request_reuse import source
from test_piece_model_finite_scope import request, result
from test_cmee_piece_refined_sources import source as refined_source


EQUIVALENTS = (
    ('です', 'だ'), ('でした', 'だった'),
    ('ではありません', 'ではない'),
    ('ではありませんでした', 'ではなかった'),
    ('ではないです', 'ではない'),
    ('ではなかったです', 'ではなかった'),
    ('じゃありません', 'じゃない'),
    ('じゃありませんでした', 'じゃなかった'),
    ('かもしれません', 'かもしれない'),
    ('とは限りません', 'とは限らない'),
    ('だったかもしれません', 'だったかもしれない'),
    ('だったとは限りません', 'だったとは限らない'),
    ('ではないかもしれません', 'ではないかもしれない'),
    ('ではないとは限りません', 'ではないとは限らない'),
    ('ではなかったかもしれません', 'ではなかったかもしれない'),
    ('ではなかったとは限りません', 'ではなかったとは限らない'),
)


@pytest.mark.parametrize('base', ('大切', '大事', '重要', '必要', '好き', '苦手'))
@pytest.mark.parametrize('polite,plain', EQUIVALENTS)
def test_existing_evaluation_state_accepts_only_same_meaning_register(base, polite, plain):
    prefix = '私は' if base in ('好き', '苦手') else '私にとって'
    original = prefix + '一人で本を読む時間が' + base + polite + '。'
    visible = prefix + '一人で本を読む時間が' + base + plain + '。'
    req = request(source(original, field='memo'))
    out = result(req, (visible,))
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact.piece_text == visible
    assert out.source_meaning.saved_snapshot.saved_original_json == req.source.saved_original_json
    # Reuse changes availability of a real candidate; old S7 is not silently
    # changed to endorse a different evaluation predicate or a new author.
    with patch('piece_v2_content_policy._piece_model_evaluation', return_value=None):
        assert result(req, (visible,)).artifact is None


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('degree', ('', 'とても', 'かなり', '少し', 'あまり'))
def test_full_focal_evaluation_can_become_a_complete_same_viewpoint_sentence(speaker, degree):
    req = request(source(speaker + 'にとって' + degree + '大切なのは、一人で本を読む時間です。'))
    body = speaker + 'にとって、一人で本を読む時間が' + degree + '大切だ。'
    out = result(req, (body,))
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (body,)


@pytest.mark.parametrize('changed', (
    '私にとって一人で本を読む時間が大切だ。',
    '私にとって一人で本を読む時間が少し大切ではなかったかもしれない。',
    '私にとって一人で本を読む時間がとても大切だったかもしれない。',
    '私にとって一人で本を読む時間がとても大切ではないかもしれない。',
    '私にとって一人で本を読む時間がとても大切ではなかったとは限らない。',
    '私にとって友人と本を読む時間がとても大切ではなかったかもしれない。',
    '私にとって一人で本を読む時間がとても必要ではなかったかもしれない。',
    '私は一人で本を読む時間がとても大切ではなかったかもしれない。',
    '友人にとって一人で本を読む時間がとても大切ではなかったかもしれない。',
    '一人で本を読む時間がとても大切ではなかったかもしれない。',
    '私は一人で本を読む時間を大切にしたい。',
))
def test_target_owner_degree_negation_time_and_modal_changes_do_not_pass(changed):
    req = request(source('私にとって一人で本を読む時間がとても大切ではなかったかもしれません。'))
    assert result(req, ('私にとって一人で本を読む時間がとても大切ではなかったかもしれない。',)).artifact
    assert result(req, (changed,)).artifact is None


def test_whole_nominal_argument_is_retained_including_internal_comparison():
    req = request(source('私にとって仕事より休む時間が必要かもしれません。'))
    assert result(req, ('私にとって仕事より休む時間が必要かもしれない。',)).artifact
    assert result(req, ('私にとって休む時間が必要かもしれない。',)).artifact is None


def test_evaluation_keeps_its_own_explicit_self_even_after_another_evaluation():
    req = request(source('私は読書が好きです。私は料理が苦手でした。'))
    assert result(req, ('私は読書が好きだ。私は料理が苦手だった。',)).artifact
    assert result(req, ('私は読書が好きだ。料理が苦手だった。',)).artifact is None
    assert result(req, ('読書が好きだ。料理が苦手だった。',)).artifact is None
    assert result(req, ('私は読書が好きだ。料理が好きだった。',)).artifact is None


def test_explicit_value_viewpoint_cannot_be_omitted_after_other_self_sentence():
    req = request(source('私は読書が好きです。私にとって休む時間が大切です。'))
    assert result(req, ('私は読書が好きだ。私にとって休む時間が大切だ。',)).artifact
    assert result(req, ('私は読書が好きだ。休む時間が大切だ。',)).artifact is None


@pytest.mark.parametrize('unread', (
    '友人は読書が好きだ。', '読書が好きだ。',
    '私はその時間が好きだ。', '私にとって読書が大切だから休む。',
    '私は読書が好きだと友人が言った。', '「私は読書が好きだ」。',
    '私にとって休む時間は必要だ。', '私にとって休む時間も必要だ。',
))
def test_finite_reading_does_not_claim_unknown_scopes(unread):
    assert _piece_model_read_block(unread) is None


def test_existing_bound_reference_keeps_its_order_and_surface_owner():
    req = request(source('私にとって読書の時間が大切です。私はその時間が好きです。'))
    # No new scope for an unbound "その時間", even though both evaluations
    # individually have plausible inflections. Existing S7 still owns them.
    assert result(req, ('私はその時間が好きだ。私にとって読書の時間が大切だ。',)).artifact is None


def test_missing_extra_or_repeated_evaluation_is_not_a_register_change():
    req = request(source('私は読書が好きです。私は料理が苦手です。'))
    for body in ('私は読書が好きだ。',
                 '私は読書が好きだ。私は料理が苦手だ。私は散歩が好きだ。',
                 '私は読書が好きだ。私は読書が好きだ。'):
        assert result(req, (body,)).artifact is None


def test_source_fields_never_share_a_self_subject_completion():
    req = request(source('私は読書が好きです。', field='memo', other='私は料理が苦手です。'))
    assert result(req, ('私は読書が好きだ。', '私は料理が苦手だ。')).artifact
    assert result(req, ('私は読書が好きだ。', '料理が苦手だ。')).artifact is None


@pytest.mark.parametrize('marker', ('ので', 'なら', 'ならば', 'けれど', 'けれども'))
def test_output_only_condition_cause_or_concession_cannot_hide_in_an_inner_evaluation(marker):
    req = request(source('私は休む時間が好きです。'))
    body = '私は疲れている' + marker + '、私は休む時間が好きだ。'
    assert _piece_model_read_block(body) is None
    assert result(req, (body,)).artifact is None


@pytest.mark.parametrize('scope', ('今は', '今も', '以前は', '当時は', '現在も', 'これからは'))
def test_output_only_temporal_scope_cannot_be_discarded_by_the_inner_reader(scope):
    req = request(source('私にとって休む時間が必要です。'))
    body = scope + '、私にとって休む時間が必要だ。'
    assert _piece_model_read_block(body) is None
    assert result(req, (body,)).artifact is None


@pytest.mark.parametrize('answer,visible', (
    ('私にとって休む時間が大切ではありませんでした。', '私にとって休む時間が大切ではなかった。'),
    ('私は読書が好きかもしれません。', '私は読書が好きかもしれない。'),
))
def test_supplemental_evaluation_uses_its_own_source_and_viewpoint(answer, visible):
    req = request(refined_source(original='私は同僚に資料の確認を頼みました。', answer=answer))
    out = result(req, ('私は同僚に資料の確認を頼んだ。', visible))
    assert out.artifact is not None, out.reason_codes
    assert out.source_meaning.supplemental.envelope.source_role == 'SUPPLEMENTAL_ANSWER'
    assert out.source_meaning.supplemental.saved_snapshot is None
    assert result(req, (visible, '私は同僚に資料の確認を頼んだ。')).artifact is None
    assert result(req, ('私は同僚に資料の確認を頼んだ。', visible.removeprefix('私は').removeprefix('私にとって'))).artifact is None
