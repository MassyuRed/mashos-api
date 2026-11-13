"""Piece-only inflection knowledge and source-bound public literal composition.

New fictional CPU inputs exercise the existing Engine/receipt/S7 path, not a
new model, a source/candidate allowlist or a replacement source admission.
"""
import pytest

from piece_v2_content_policy import validate_source_meaning_preservation
from piece_v2_contract import PieceContractError
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source
from test_piece_model_narrator_voice import evaluate as evaluate_saved
from test_piece_model_prose_register import evaluate


CONTEXT = '私は図を描く時間を大切にしたいです。'
PAIRS = (
    ('私は、手紙に書かれた違いに気づきました。', '私は、手紙に書かれた違いに気づいた。'),
    ('私は、手紙に書かれた違いに気づきませんでした。', '私は、手紙に書かれた違いに気づかなかった。'),
    ('私は、来週の段取りを考えました。', '私は、来週の段取りを考えた。'),
    ('私は、来週の段取りを考えませんでした。', '私は、来週の段取りを考えなかった。'),
    ('私は、まだ十分な説明を言葉にできました。', '私は、まだ十分な説明を言葉にできた。'),
    ('私は、まだ十分な説明を言葉にできませんでした。', '私は、まだ十分な説明を言葉にできなかった。'),
    ('私は、受付係にはまだ集合場所を伝えていません。', '私は、受付係にはまだ集合場所を伝えていない。'),
    ('私は、受付係には今も集合場所を伝えています。', '私は、受付係には今も集合場所を伝えている。'),
    ('私は、話を終えたわけではありません。', '私は、話を終えたわけではない。'),
)


@pytest.mark.parametrize('before,after', PAIRS)
@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_complete_source_preserves_inflection_axes_and_written_narrator(before, after, speaker):
    before = before.replace('私は', speaker + 'は')
    after = after.replace('私は', speaker + 'は')
    out = evaluate(CONTEXT + before, CONTEXT + after)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.body_blocks == (CONTEXT + after,)
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)
    validate_source_meaning_preservation(out.source_meaning, out.artifact_plan,
                                        out.artifact, _model_register=True)


@pytest.mark.parametrize('index,old,new', (
    (0, '気づいた', '気づかなかった'), (0, '気づいた', '気づく'),
    (0, '気づいた', '気づいていた'), (0, '気づいた', '気づかれた'),
    (1, '気づかなかった', '気づいた'),
    (2, '考えた', '決めた'), (2, '来週', '今週'), (2, '段取りを', '段取りに'),
    (3, '考えなかった', '考えた'),
    (5, 'できなかった', 'しなかった'), (5, 'できなかった', 'できた'),
    (6, '伝えていない', '伝えた'), (6, '伝えていない', '伝えなかった'),
    (6, '伝えていない', '伝えない'), (6, '伝えていない', '伝えている'),
    (6, '伝えていない', '伝えていなかった'), (6, 'まだ', ''),
    (6, '受付係には', '受付係からは'),
    (7, '伝えている', '伝えた'),
    (8, '終えたわけではない', '終えなかった'),
    (8, '終えたわけではない', '終えた'),
    (8, '終えたわけではない', '終えたいわけではない'),
    (8, 'わけではない', 'わけではなかった'),
))
def test_changed_predicate_scope_case_aspect_or_time_is_refused(index, old, new):
    before, after = PAIRS[index]
    assert old in after
    assert evaluate(CONTEXT + before, CONTEXT + after.replace(old, new, 1)).artifact is None


def test_bound_name_alias_composes_with_impression_and_keeps_condition():
    before = '僕は、友人の坂さんとなら、急がずに話せる気がします。'
    after = '僕は、友人となら、急がずに話せる気がする。'
    out = evaluate(CONTEXT + before, CONTEXT + after)
    assert out.artifact is not None, out.reason_codes
    for damaged in (after.replace('友人', '同僚'), after.replace('友人', '坂さん'),
                    after.replace('となら', 'と'), after.replace('気がする', ''),
                    after.replace('僕は', '私は'), after.replace('気がする', '気がした')):
        assert evaluate(CONTEXT + before, CONTEXT + damaged).artifact is None


def test_alias_and_inflection_cannot_borrow_a_field_or_supplemental_author():
    memo = CONTEXT + 'おれは、同僚の土井さんとなら、落ち着いて話せる気がします。'
    answer_core = '僕は図を描く時間を大切にしたいです。'
    action = answer_core + '僕は、昨日の段取りを考えました。'
    blocks = [CONTEXT + 'おれは、同僚となら、落ち着いて話せる気がする。',
              answer_core + '僕は、昨日の段取りを考えた。']
    for saved in (source(memo, field='memo', other=action),
                  refined_source(original=memo, answer=action)):
        out = evaluate_saved(saved, blocks)
        assert out.artifact is not None, out.reason_codes
        for damaged in (blocks[::-1], [blocks[0], blocks[1].replace('僕は', 'おれは')],
                        [blocks[0].replace('同僚', '友人'), blocks[1]]):
            assert evaluate_saved(saved, damaged).artifact is None


@pytest.mark.parametrize('before,after', (
    ('私は、同僚の土井さんに資料を渡したことに気づきました。',
     '私は、同僚に資料を渡したことに気づいた。'),
    ('私は、同僚の土井さんにはまだ集合場所を伝えていません。',
     '私は、同僚にはまだ集合場所を伝えていない。'),
))
def test_public_alias_composes_in_the_same_finite_or_state_literal_leaf(before, after):
    out = evaluate(CONTEXT + before, CONTEXT + after)
    assert out.artifact is not None, out.reason_codes
    assert evaluate(CONTEXT + before, CONTEXT + after.replace('同僚', '友人')).artifact is None
    assert evaluate(CONTEXT + before, CONTEXT + after.replace('同僚', '土井さん')).artifact is None


@pytest.mark.parametrize('before,after', (
    ('私は、山を降りました。', '私は、山を降った。'),
    ('私は、手を動かしました。', '私は、手を動かした。'),
    ('私は、頼まれた内容に気づきました。', '私は、頼んだ内容に気づいた。'),
    ('私は、手紙に書かれた違いに気づきました。', '私は、手紙に書かれた違いに気づきた。'),
))
def test_unknown_class_malformed_inflection_and_changed_literal_stay_refused(before, after):
    assert evaluate(CONTEXT + before, CONTEXT + after).artifact is None


def test_new_inflection_does_not_qualify_an_unsupported_source():
    assert evaluate(PAIRS[0][0], PAIRS[0][1]).artifact is None
