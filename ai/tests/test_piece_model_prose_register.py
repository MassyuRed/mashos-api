"""Bounded model prose register, with source-owned targets and reference edges.

All text is fictional. These fixed CPU candidates do not call a model or the
old author, and do not claim a general Japanese paraphrase comparison.
"""
from contextlib import ExitStack
import json
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PIECE_FIELD_SLOTS_FORMAT, PieceModelInputV1, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from piece_v2_content_policy import validate_source_meaning_preservation
from piece_v2_contract import PieceContractError
from test_cmee_piece_finite_request_reuse import source
from test_piece_model_finite_scope import request


WISH = '私は静かな場所で本を読む時間を大切にしたいです。私は自分の考えをノートに書くことを選びたい。まだ、毎日続けるかは決めていません。'
WISH_BODY = '私は静かな場所で本を読む時間を大切にしたい。私は自分の考えをノートに書くことを選びたい。まだ、毎日続けるかは決めていない。'
FOCAL = '私が大切にしたいのは、静かな部屋で本を読む時間です。私はその時間が好きです。まだ、毎日続けるかは決めていません。'
FOCAL_BODY = '私は、静かな部屋で本を読む時間を大切にしたい。その時間が好きだ。まだ、毎日続けるかは決めていない。'
NAMED = '私が選びたいのは、同僚の西さんと展示を見る時間です。私はその時間が好きです。まだ、参加する日は決めていません。'
NAMED_BODY = '私は、同僚と展示を見る時間を選びたい。私はその時間が好きだ。まだ、参加する日は決めていない。'
EVALUATION = '私にとってとても大切なのは、静かな場所で本を読む時間です。私は読書が好きです。私は料理が苦手だった。'
EVALUATION_TOPIC = '私にとって、静かな場所で本を読む時間はとても大切だ。私は読書が好きだ。私は料理が苦手だった。'


def evaluate(original, body, *, other=None):
    saved = source(original, field='memo', other=other)
    req = request(saved)
    prepared = prepare_piece_model_request(req)
    blocks = body if isinstance(body, list) else [body]
    keys = [item['field_path'] + '_' + str(i)
            for i, item in enumerate(prepared.payload()['control']['block_partition'])]
    raw = json.dumps({'field_blocks': dict(zip(keys, blocks, strict=True))},
                     ensure_ascii=False, separators=(',', ':'))
    receipt = receive_piece_model_candidate(prepared, raw_output=raw, finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT, provider='fixed-cpu', model='no-model-called')
    before = saved.saved_original_json, prepared.private_json
    with ExitStack() as stack:
        for owner in ('piece_v1c.realize_piece_artifact', 'piece_v1c._publicize_source_sentence',
                      'piece_v1c._evaluation_sentence', 'piece_refined.realize_refined_piece_artifact'):
            stack.enter_context(patch('cocolon_meaning_experience_engine.' + owner,
                                     side_effect=AssertionError('old author forbidden')))
        result = MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))
    assert (saved.saved_original_json, prepared.private_json) == before
    assert receipt.raw_output == raw
    if result.artifact:
        assert result.artifact.body_blocks == tuple(blocks)
        assert result.artifact.piece_text == '\n\n'.join(blocks)
    return result


@pytest.mark.parametrize('original,body', [(WISH, WISH_BODY), (FOCAL, FOCAL_BODY), (NAMED, NAMED_BODY)])
def test_source_bound_register_is_accepted_without_repair_or_author_replay(original, body):
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    # The native S7 contract remains strict; only the model review explicitly
    # opts into these source-bound register comparisons.
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


def test_written_target_topic_is_still_unassessed_instead_of_normalized_to_ga():
    assert evaluate(EVALUATION, EVALUATION_TOPIC).artifact is None


@pytest.mark.parametrize('changed', [
    WISH_BODY.replace('大切にしたい。', '大切にしたくない。'),
    WISH_BODY.replace('大切にしたい。', '大切にしたかった。'),
    WISH_BODY.replace('大切にしたい。', '大切にしたいかもしれない。'),
    WISH_BODY.replace('読む時間', '書く時間'),
    WISH_BODY.replace('私は静かな', '友人は静かな'),
    WISH_BODY.replace('私は静かな', '静かな'),
    WISH_BODY.replace('まだ、', ''),
    WISH_BODY.replace('毎日続けるかは', '参加する日は'),
    WISH_BODY.replace('毎日続けるかは', '毎日続けることは'),
    WISH_BODY.replace('決めていない。', '決めた。'),
    WISH_BODY.replace('決めていない。', '決めていなかった。'),
    WISH_BODY.replace('決めていない。', '決めていないかもしれない。'),
    WISH_BODY.replace('決めていない。', '決めていないと友人が言った。'),
    WISH_BODY + '私は毎日続けている。',
])
def test_wish_and_decision_preserve_entire_target_negation_time_and_question_prefix(changed):
    assert evaluate(WISH, changed).artifact is None


@pytest.mark.parametrize('changed', [
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間が苦手だ。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間がとても好きだ。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間が好きだった。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間が好きではない。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間が好きかもしれない。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'この時間が好きだ。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間は好きだ。'),
    FOCAL_BODY.replace('その時間が好きだ。', '友人はその時間が好きだ。'),
    FOCAL_BODY.replace('その時間が好きだ。', 'その時間が好きだと友人が言った。'),
    FOCAL_BODY.replace('その時間が好きだ。', ''),
    'その時間が好きだ。' + FOCAL_BODY.replace('その時間が好きだ。', ''),
])
def test_bound_reference_evaluation_never_loses_its_predicate_or_antecedent(changed):
    assert evaluate(FOCAL, changed).artifact is None


@pytest.mark.parametrize('changed', [
    NAMED_BODY.replace('同僚と', '友人と'),
    NAMED_BODY.replace('同僚と', '同僚の西さんと'),
    NAMED_BODY.replace('同僚と', '同僚の東さんと'),
    NAMED_BODY.replace('私はその時間', '同僚はその時間'),
    NAMED_BODY.replace('参加する日は', '参加するかは'),
])
def test_named_role_remains_exactly_the_public_alias_proved_by_source(changed):
    assert evaluate(NAMED, changed).artifact is None


@pytest.mark.parametrize('before,after', [
    ('好きです', '好きだ'), ('好きでした', '好きだった'),
    ('とても好きではありません', 'とても好きではない'),
    ('少し苦手ではありませんでした', '少し苦手ではなかった'),
    ('好きだったかもしれません', '好きだったかもしれない'),
    ('苦手ではなかったとは限りません', '苦手ではなかったとは限らない'),
])
def test_existing_bound_frame_owns_register_equivalence_and_all_operators(before, after):
    original = FOCAL.replace('好きです', before)
    body = FOCAL_BODY.replace('好きだ', after)
    assert evaluate(original, body).artifact is not None


def test_omission_never_borrows_self_or_reference_from_another_field():
    original = '私は自分の考えをノートに書くことを選びたい。'
    other = '私はその時間が好きです。まだ、毎日続けるかは決めていません。'
    assert evaluate(original, [original, 'その時間が好きだ。まだ、毎日続けるかは決めていない。'],
                    other=other).artifact is None
