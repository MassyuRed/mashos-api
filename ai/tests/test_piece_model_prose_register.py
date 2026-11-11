"""Bounded model prose register, with source-owned targets and reference edges.

All text is fictional. These fixed CPU candidates do not call a model or the
old author, and do not claim a general Japanese paraphrase comparison.
"""
from contextlib import ExitStack
from dataclasses import replace
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
FOCAL_ORDER = '私が大切にしたいのは、静かな部屋で本を読む時間だ。その時間が好きだ。まだ、毎日続けるかは決めていない。'
EVALUATION_CONTINUED = '私にとって、静かな場所で本を読む時間がとても大切だ。読書が好きだ。料理が苦手だった。'
SCOPED_FOCAL = '疲れているなら、私が選びたいのは、音楽を聴く時間です。まだ、出かける日は決めていません。'
SCOPED_FOCAL_BODY = '疲れているなら、私が選びたいのは、音楽を聴く時間だ。まだ、出かける日は決めていない。'


def evaluate(original, body, *, other=None, emotions=None, details=None):
    saved = source(original, field='memo', other=other, emotions=emotions, details=details)
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


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば'])
@pytest.mark.parametrize('account', ['本を読みたい', '家で過ごしたい', '氷みたい'])
@pytest.mark.parametrize('polite_source', [False, True])
def test_canonical_self_fronted_literal_register_retains_existing_order_and_whole_account(
        speaker, marker, account, polite_source):
    original = f'疲れている{marker}、{speaker}は{account}' + ('です。' if polite_source else '。')
    native_body = f'{speaker}は、疲れている{marker}、{account}' + ('です。' if polite_source else '。')
    candidate = f'{speaker}は、疲れている{marker}、{account}' + ('。' if polite_source else 'です。')
    native = evaluate(original, native_body)
    assert native.artifact is not None, native.reason_codes
    validate_source_meaning_preservation(native.source_meaning, native.artifact_plan, native.artifact)
    out = evaluate(original, candidate)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.source_meaning == native.source_meaning
    assert out.artifact_plan == native.artifact_plan
    assert out.artifact.body_blocks == (candidate,)
    # A model-only register comparison never changes the native author contract.
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


CANONICAL_SELF_SOURCE = '疲れているなら、私は本を読みたいです。'
CANONICAL_SELF_BODY = '私は、疲れているなら、本を読みたい。'


@pytest.mark.parametrize('body', [
    CANONICAL_SELF_BODY.replace('私は', '僕は'),
    CANONICAL_SELF_BODY.replace('私は、', ''),
    CANONICAL_SELF_BODY.replace('疲れている', '疲れていない'),
    CANONICAL_SELF_BODY.replace('疲れている', '疲れていた'),
    CANONICAL_SELF_BODY.replace('なら', 'ので'),
    CANONICAL_SELF_BODY.replace('本を', '新聞を'),
    CANONICAL_SELF_BODY.replace('本を', '本が'),
    CANONICAL_SELF_BODY.replace('読みたい', '読みたくない'),
    CANONICAL_SELF_BODY.replace('読みたい', '読みたかった'),
    CANONICAL_SELF_BODY.replace('読みたい', '読んだ'),
    CANONICAL_SELF_BODY.replace('読みたい', '読みたいかもしれない'),
    CANONICAL_SELF_BODY.replace('読みたい', 'とても読みたい'),
    CANONICAL_SELF_BODY.replace('。', '！'),
    CANONICAL_SELF_BODY.replace('なら、', 'ならば、'),
    CANONICAL_SELF_BODY.replace('なら、', 'なら，'),
    CANONICAL_SELF_BODY.replace('なら、', 'なら、\n'),
    CANONICAL_SELF_BODY + '私は嬉しい。',
])
def test_canonical_self_fronted_register_rejects_changed_meaning_and_scope(body):
    assert evaluate(CANONICAL_SELF_SOURCE, body).artifact is None


@pytest.mark.parametrize('marker', ['けれど', 'けれども'])
@pytest.mark.parametrize('polite_body', [False, True])
def test_canonical_self_fronted_register_does_not_move_a_concession(marker, polite_body):
    original = f'疲れている{marker}、私は本を読みたいです。'
    fronted = f'私は、疲れている{marker}、本を読みたい' + ('です。' if polite_body else '。')
    assert evaluate(original, fronted).artifact is None
    assert evaluate(original, original.removesuffix('です。') + '。').artifact is not None


@pytest.mark.parametrize('stop', ['！', '!'])
def test_canonical_self_fronted_register_keeps_emphasized_literal_order(stop):
    original = '寒いので、私は氷みたいです' + stop
    assert evaluate(original, '私は、寒いので、氷みたい' + stop).artifact is None
    assert evaluate(original, original.removesuffix('です' + stop) + stop).artifact is not None


@pytest.mark.parametrize('separator', ['\n', '\r\n'])
def test_canonical_self_fronted_register_keeps_paragraph_and_author_boundaries(separator):
    original = CANONICAL_SELF_SOURCE + separator + '僕は読書が好きです。'
    blocks = [CANONICAL_SELF_BODY, '僕は読書が好きだ。']
    assert evaluate(original, blocks).artifact is not None
    assert evaluate(original, [blocks[0], '読書が好きだ。']).artifact is None


def test_canonical_self_fronted_register_keeps_saved_fields_and_refined_sources_separate():
    from test_cmee_piece_refined_sources import source as refined_source
    from test_piece_model_narrator_voice import evaluate as evaluate_saved
    answer = 'わたしは読書が好きです。'
    for saved in (source(CANONICAL_SELF_SOURCE, field='memo', other=answer),
                  refined_source(original=CANONICAL_SELF_SOURCE, answer=answer)):
        blocks = [CANONICAL_SELF_BODY, 'わたしは読書が好きだ。']
        assert evaluate_saved(saved, blocks).artifact is not None
        assert evaluate_saved(saved, [blocks[0], '読書が好きだ。']).artifact is None
        assert evaluate_saved(saved, [blocks[0], '私は読書が好きだ。']).artifact is None


def test_canonical_self_fronted_register_keeps_the_complete_quoted_premise():
    original = '友人が「私は休みたい」と言ったので、私は本を読みたいです。'
    body = '私は、友人が「私は休みたい」と言ったので、本を読みたい。'
    assert evaluate(original, body).artifact is not None
    assert evaluate(original, body.replace('「私は休みたい」', '「僕は休みたい」')).artifact is None
    assert evaluate(original, body.replace('「私は休みたい」', '「私は休んだ」')).artifact is None


def test_canonical_self_fronted_register_keeps_a_bound_reference_premise_in_native_order():
    original = '私にとって家で過ごす時間が大切です。その時間が取れるなら、私は旅に出る前の鳥みたいです。'
    body = '私にとって家で過ごす時間が大切だ。その時間が取れるなら、私は旅に出る前の鳥みたい。'
    assert evaluate(original, body).artifact is not None
    fronted = '私にとって家で過ごす時間が大切だ。私は、その時間が取れるなら、旅に出る前の鳥みたい。'
    assert evaluate(original, fronted).artifact is None


MODIFIED_TIME = '以前は、私は一人の食事が苦手でした。今は、私は一人の食事が好きです。'
MODIFIED_TIME_BODY = '以前は、私は一人の食事が苦手だった。今は、私は一人の食事が好きだ。'


@pytest.mark.parametrize('marker,relation', [
    ('ので', 'SOURCE_EXPLICIT_REASON'), ('なら', 'SOURCE_EXPLICIT_CONDITION'),
    ('ならば', 'SOURCE_EXPLICIT_CONDITION'), ('けれど', 'SOURCE_EXPLICIT_CONCESSION'),
    ('けれども', 'SOURCE_EXPLICIT_CONCESSION'),
])
@pytest.mark.parametrize('expression,body', [
    ('私は一人の食事が好きです。', '私は一人の食事が好きだ。'),
    ('ぼくは静かな朝食が苦手でした。', 'ぼくは静かな朝食が苦手だった。'),
    ('俺は読書が少し好きではありません。', '俺は読書が少し好きではない。'),
    ('わたしは料理が好きかもしれません。', 'わたしは料理が好きかもしれない。'),
    ('僕にとって古い資料を読む時間が大切です。', '僕にとって古い資料を読む時間が大切だ。'),
    ('私にとって休息がとても必要でした。', '私にとって休息がとても必要だった。'),
    ('おれにとって準備が大事とは限りません。', 'おれにとって準備が大事とは限らない。'),
    ('私にとって読書が重要だ。', '私にとって読書が重要です。'),
])
def test_scoped_evaluation_register_keeps_the_bound_relation_target_and_operators(marker, relation, expression, body):
    original = '時間に余裕がある' + marker + '、' + expression
    candidate = '時間に余裕がある' + marker + '、' + body
    out = evaluate(original, candidate)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    scope, = out.source_meaning.expression_scopes
    frame, = out.source_meaning.personal_evaluations
    assert scope.relation == relation and scope.node_id == frame.node_id
    assert out.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert out.artifact.body_blocks == (candidate,)


SCOPED_EVALUATION = '友人が「私は料理が苦手」と話してくれたので、私は静かな朝食が少し好きかもしれません。'
SCOPED_EVALUATION_BODY = SCOPED_EVALUATION.replace('かもしれません。', 'かもしれない。')


@pytest.mark.parametrize('body', [
    '私は静かな朝食が少し好きかもしれない。',
    SCOPED_EVALUATION_BODY.replace('ので', 'なら'),
    SCOPED_EVALUATION_BODY.replace('話してくれた', '話さなかった'),
    SCOPED_EVALUATION_BODY.replace('「私は', '「僕は'),
    SCOPED_EVALUATION_BODY.replace('料理が苦手', '料理が好き'),
    SCOPED_EVALUATION_BODY.replace('、私は', '、'),
    SCOPED_EVALUATION_BODY.replace('、私は', '、僕は'),
    SCOPED_EVALUATION_BODY.replace('静かな朝食', '朝食'),
    SCOPED_EVALUATION_BODY.replace('朝食が', '朝食は'),
    SCOPED_EVALUATION_BODY.replace('少し', 'とても'),
    SCOPED_EVALUATION_BODY.replace('少し', ''),
    SCOPED_EVALUATION_BODY.replace('好きかもしれない', '好きだ'),
    SCOPED_EVALUATION_BODY.replace('好きかもしれない', '好きではないかもしれない'),
    SCOPED_EVALUATION_BODY.replace('好きかもしれない', '好きだったかもしれない'),
    SCOPED_EVALUATION_BODY.replace('好き', '苦手'),
    SCOPED_EVALUATION_BODY.replace('。', '！'),
    SCOPED_EVALUATION_BODY + '私は嬉しい。',
])
def test_scoped_evaluation_register_never_borrows_or_changes_the_outer_or_inner_meaning(body):
    assert evaluate(SCOPED_EVALUATION, body).artifact is None


@pytest.mark.parametrize('separator', ['、 ', '，\t', ',\u3000'])
def test_scoped_evaluation_register_retains_the_full_outer_separator(separator):
    original = SCOPED_EVALUATION.replace('、', separator)
    body = SCOPED_EVALUATION_BODY.replace('、', separator)
    assert evaluate(original, body).artifact is not None
    assert evaluate(original, SCOPED_EVALUATION_BODY).artifact is None


def test_scoped_evaluation_register_keeps_existing_public_roles_and_native_matches():
    original = '友人の佐藤さんが忙しいので、私は読書が好きです。'
    native = MeaningExperienceEngine().generate(request(source(original, field='memo')))
    assert native.artifact.piece_text == '友人が忙しいので、私は、読書が好きです。'
    validate_source_meaning_preservation(native.source_meaning, native.artifact_plan, native.artifact)
    assert evaluate(original, native.artifact.piece_text).artifact == native.artifact
    body = '友人が忙しいので、私は読書が好きだ。'
    out = evaluate(original, body)
    assert out.artifact is not None
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)
    assert evaluate(original, body.replace('友人', '同僚')).artifact is None


def test_scoped_evaluation_register_uses_only_existing_author_continuity():
    original = '私は読書が好きです。雨が続いているので、私は静かな朝食が好きです。'
    body = '私は読書が好きだ。雨が続いているので、静かな朝食が好きだ。'
    assert evaluate(original, body).artifact is not None
    # A same-sentence self premise already proves this author in native too.
    original = '私は疲れているので、私は読書が好きです。'
    assert evaluate(original, '私は疲れているので、読書が好きです。').artifact is not None
    assert evaluate(original, '私は疲れているので、読書が好きだ。').artifact is not None
    value = '私は疲れているので、私にとって読書が大切です。'
    assert evaluate(value, '私は疲れているので、読書が大切だ。').artifact is None


@pytest.mark.parametrize('separator', ['\n', '\r\n'])
def test_scoped_evaluation_register_does_not_carry_the_author_across_paragraphs(separator):
    original = '私は読書が好きです。' + separator + '雨が続いているので、私は静かな朝食が好きです。'
    bodies = ['私は読書が好きだ。', '雨が続いているので、私は静かな朝食が好きだ。']
    assert evaluate(original, bodies).artifact is not None
    assert evaluate(original, [bodies[0], bodies[1].replace('私は', '')]).artifact is None


def test_scoped_evaluation_register_keeps_original_fields_and_supplemental_authors_separate():
    from test_piece_model_narrator_voice import evaluate as evaluate_saved
    from test_cmee_piece_refined_sources import source as refined_source
    other = '余裕があるなら、私は料理が好きです。'
    saved = source(SCOPED_EVALUATION, field='memo', other=other)
    bodies = [SCOPED_EVALUATION_BODY, other.replace('好きです', '好きだ')]
    assert evaluate_saved(saved, bodies).artifact is not None
    assert evaluate_saved(saved, [bodies[0], bodies[1].replace('私は', '')]).artifact is None
    saved = refined_source(original=SCOPED_EVALUATION, answer='わたしは読書が好きです。')
    bodies = [SCOPED_EVALUATION_BODY, 'わたしは読書が好きだ。']
    assert evaluate_saved(saved, bodies).artifact is not None
    assert evaluate_saved(saved, [bodies[0], bodies[1].replace('わたしは', '私は')]).artifact is None


def test_scoped_evaluation_register_does_not_add_a_focal_order_or_source_grammar():
    original = '雨が続いているので、私が好きなのは、読書の時間です。'
    assert evaluate(original, '雨が続いているので、私は読書の時間が好きだ。').artifact is not None
    assert evaluate(original, original.replace('です', 'だ')).artifact is None
    # A source without its own written viewpoint does not gain qualification.
    assert evaluate('雨が続いているので、静かな朝食が好きです。',
                    '雨が続いているので、私は静かな朝食が好きだ。').artifact is None


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('target', ['一人の食事', '静かな朝食'])
def test_modified_preference_time_register_keeps_each_whole_target_and_explicit_author(speaker, target):
    original = MODIFIED_TIME.replace('私', speaker).replace('一人の食事', target)
    body = MODIFIED_TIME_BODY.replace('私', speaker).replace('一人の食事', target)
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert len(out.source_meaning.expression_scopes) == 2
    assert all(s.relation == 'SOURCE_EXPLICIT_TIME_CONTEXT' for s in out.source_meaning.expression_scopes)
    frames = out.source_meaning.personal_evaluations
    assert [(f.temporal_scope, f.polarity) for f in frames] == [('PAST', 'AFFIRMATIVE'), ('NONPAST', 'AFFIRMATIVE')]
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('original,body', [
    ('俺は静かな朝食が好きです。', '俺は静かな朝食が好きだ。'),
    ('私は家族の朝食が苦手ではありませんでした。', '私は家族の朝食が苦手ではなかった。'),
    ('当時も、私は古い資料が少し苦手でした。', '当時も、私は古い資料が少し苦手だった。'),
    ('今は、僕は一人の食事が好きかもしれません。', '今は、僕は一人の食事が好きかもしれない。'),
    ('現在は、おれは静かな朝食が苦手ではありません。', '現在は、おれは静かな朝食が苦手ではない。'),
    ('以前は、私は読書が好きでした。', '以前は、私は読書が好きだった。'),
])
def test_modified_preference_reuses_existing_tense_degree_negation_and_modal_keys(original, body):
    assert evaluate(original, body).artifact is not None


@pytest.mark.parametrize('changed', [
    MODIFIED_TIME_BODY.replace('一人の食事', '食事', 1),
    MODIFIED_TIME_BODY.replace('今は', '以前は'),
    MODIFIED_TIME_BODY.replace('以前は', '今は'),
    MODIFIED_TIME_BODY.replace('以前は', '以前も'),
    MODIFIED_TIME_BODY.replace('以前は、', ''),
    MODIFIED_TIME_BODY.replace('今は、', ''),
    MODIFIED_TIME_BODY.replace('苦手だった', '苦手だ'),
    MODIFIED_TIME_BODY.replace('苦手だった', '苦手ではなかった'),
    MODIFIED_TIME_BODY.replace('好きだ', '好きだった'),
    MODIFIED_TIME_BODY.replace('好きだ', '好きではない'),
    MODIFIED_TIME_BODY.replace('好きだ', '好きになった'),
    MODIFIED_TIME_BODY.replace('好きだ', '少し好きだ'),
    MODIFIED_TIME_BODY.replace('好きだ', '好きかもしれない'),
    MODIFIED_TIME_BODY.replace('今は、私は', '今は、僕は'),
    MODIFIED_TIME_BODY.replace('以前は、私は', '以前は、'),
    MODIFIED_TIME_BODY.replace('今は、', '以前苦手だったので、'),
    MODIFIED_TIME_BODY.replace('以前は、', '以前は，'),
    MODIFIED_TIME_BODY.replace('だった。', 'だった！'),
    '。'.join(reversed(MODIFIED_TIME_BODY.split('。')[:-1])) + '。',
    MODIFIED_TIME_BODY + 'だから私は成長した。',
])
def test_modified_preference_scope_never_licenses_target_time_author_or_operator_changes(changed):
    assert evaluate(MODIFIED_TIME, changed).artifact is None


def test_modified_preference_keeps_time_when_only_the_repeated_narrator_is_omitted():
    body = MODIFIED_TIME_BODY.replace('今は、私は', '今は、')
    assert evaluate(MODIFIED_TIME, body).artifact is not None


@pytest.mark.parametrize('changed', [
    '俺は朝食が好きだ。', '俺は静かな食事が好きだ。', '私は静かな朝食が好きだ。',
    '俺は静かな朝食が好きだった。', '俺は静かな朝食が苦手だ。',
    '俺は静かな朝食が好きかもしれない。',
])
def test_modified_preference_single_clause_preserves_attributive_and_narrator(changed):
    assert evaluate('俺は静かな朝食が好きです。', changed).artifact is None


REASON = '私は夕方に疲れやすいので、私は短い休息が大切です。'
REASON_BODY = '私は夕方に疲れやすいので、短い休息が大切だ。'
SEPARATE_ACTION = '私は家族に夕食の時刻を伝えました。'
SEPARATE_ACTION_BODY = '私は家族に夕食の時刻を伝えた。'


def evaluate_reason(original, body):
    # Ordinary emotion selection must match the original GeneralProse case.
    # SELF_INSIGHT has a different source-admission contract.
    return evaluate(original, body, other=SEPARATE_ACTION, emotions=['平穏'],
                    details=[dict(type='平穏', strength='weak')])


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('stop', ['。', '！', '!'])
def test_opaque_reason_value_keeps_complete_premise_target_and_same_written_author(speaker, stop):
    original = REASON.replace('私', speaker)[:-1] + stop
    body = REASON_BODY.replace('私', speaker)[:-1] + stop
    out = evaluate_reason(original, [body, SEPARATE_ACTION_BODY])
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact_plan.duties[0].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
    assert not out.source_meaning.personal_evaluations
    assert not out.source_meaning.expression_scopes
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('target,predicate', [
    ('早い帰宅', '大事'), ('静かな昼寝', 'とても重要'), ('長い準備', '少し必要'),
])
def test_opaque_reason_value_does_not_depend_on_one_target_or_one_evaluation_word(target, predicate):
    original = REASON.replace('短い休息', target).replace('大切', predicate)
    body = REASON_BODY.replace('短い休息', target).replace('大切', predicate)
    assert evaluate_reason(original, [body, SEPARATE_ACTION_BODY]).artifact
    assert evaluate_reason(original, [body.replace(predicate, '大切'), SEPARATE_ACTION_BODY]).artifact is None


@pytest.mark.parametrize('changed', [
    '短い休息が大切だ。',
    '夕方に疲れやすいので、短い休息が大切だ。',
    REASON_BODY.replace('疲れやすい', '疲れにくい'),
    REASON_BODY.replace('ので', 'なら'),
    REASON_BODY.replace('ので', 'けれど'),
    REASON_BODY.replace('短い休息', '長い休息'),
    REASON_BODY.replace('大切', '重要'),
    REASON_BODY.replace('大切', 'とても大切'),
    REASON_BODY.replace('大切だ', '大切ではない'),
    REASON_BODY.replace('大切だ', '大切だった'),
    REASON_BODY.replace('大切だ', '大切かもしれない'),
    REASON_BODY.replace('大切だ', '大切だと友人が言った'),
    REASON_BODY.replace('、短い', '、僕は短い'),
    REASON_BODY.replace('、短い', '、友人は短い'),
    REASON_BODY.replace('、短い', '、私が短い'),
    REASON_BODY.replace('休息が', '休息は'),
    REASON_BODY.replace('、', '，'),
    REASON_BODY.replace('。', '！'),
    REASON_BODY + '私は嬉しい。',
])
def test_opaque_reason_value_rejects_changed_context_viewpoint_operator_and_terminal(changed):
    assert evaluate_reason(REASON, [changed, SEPARATE_ACTION_BODY]).artifact is None


@pytest.mark.parametrize('original,body', [
    (REASON.replace('私は夕方', '友人は夕方'), REASON_BODY.replace('私は夕方', '友人は夕方')),
    (REASON.replace('私は夕方', '僕は夕方'), REASON_BODY.replace('私は夕方', '僕は夕方')),
    (REASON.replace('私は短い', '私は友人は短い'), REASON_BODY.replace('、短い', '、友人は短い')),
    (REASON.replace('私は短い', '私は私は短い'), REASON_BODY.replace('、短い', '、私は短い')),
    (REASON.replace('大切です', '大切ではないです'), REASON_BODY.replace('大切だ', '大切ではない')),
    (REASON.replace('大切です', '大切でした'), REASON_BODY.replace('大切だ', '大切だった')),
    (REASON.replace('大切です', '大切かもしれません'), REASON_BODY.replace('大切だ', '大切かもしれない')),
])
def test_opaque_reason_value_does_not_infer_scope_author_or_extend_past_negative_modal(original, body):
    assert evaluate_reason(original, [body, SEPARATE_ACTION_BODY]).artifact is None


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('ending,body_ending', [('たいです', 'たい'), ('たくないです', 'たくない')])
def test_complete_literal_self_ending_keeps_every_word_with_only_polite_desu_optional(speaker, ending, body_ending):
    original = speaker + 'は地域の活動に加わり' + ending + '。まだ、参加する日は決めていません。'
    body = speaker + 'は地域の活動に加わり' + body_ending + '。まだ、参加する日は決めていない。'
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('target', ['写真を飾る場所は', '参加する会場は', '集合する時刻は'])
def test_source_qualified_undecided_whole_nominal_head_keeps_exact_target(target):
    original = FOCAL.replace('毎日続けるかは', target)
    body = FOCAL_BODY.replace('毎日続けるかは', target)
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert evaluate(original, body.replace(target, '参加する日は')).artifact is None
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('changed', [
    '地域の活動に加わりたい。',
    '僕は地域の活動に加わりたい。',
    '私は会社の活動に加わりたい。',
    '私は地域の活動に加わりたくない。',
    '私は地域の活動に加わりたかった。',
    '私は地域の活動に加わった。',
    '私は地域の活動に加わりたいかもしれない。',
    '私は地域の活動に加わりたいと友人が言った。',
    '私は寂しいので地域の活動に加わりたい。',
    '私は地域の活動に加わりたい。私は嬉しい。',
])
def test_literal_self_register_never_changes_narrator_target_wish_time_or_adds_context(changed):
    original = '私は地域の活動に加わりたいです。まだ、参加する日は決めていません。'
    assert evaluate(original, changed + 'まだ、参加する日は決めていない。').artifact is None


@pytest.mark.parametrize('changed', [
    'まだ、写真を飾る日は決めていない。',
    'まだ、写真を飾る場所も決めていない。',
    '写真を飾る場所は決めていない。',
    'まだ、写真を飾る場所は決めた。',
    'まだ、写真を飾る場所は決めていなかった。',
    'まだ、写真を飾る場所は決めていないかもしれない。',
    'まだ、写真を飾る場所は決めていないと聞いた。',
])
def test_nominal_decision_target_stays_undecided_and_whole(changed):
    original = FOCAL.replace('毎日続けるかは', '写真を飾る場所は')
    body = FOCAL_BODY.rsplit('まだ、', 1)[0] + changed
    assert evaluate(original, body).artifact is None


@pytest.mark.parametrize('stop', ['。', '！', '!'])
def test_literal_register_retains_topic_internal_reason_and_exact_emphasis(stop):
    original = '私は疲れているので、私は地域の活動に加わりたいです' + stop
    body = '私は疲れているので、私は地域の活動に加わりたい' + stop
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    changed_stop = '。' if stop != '。' else '！'
    assert evaluate(original, body[:-1] + changed_stop).artifact is None


def test_literal_register_never_bypasses_a_source_scope_operation_binding():
    original = '疲れているなら、私は本を読みたい。'
    out = evaluate(original, '私は、疲れているなら、本を読みたい。')
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.source_meaning.expression_scopes
    forged_plan = replace(out.artifact_plan, duties=tuple(
        replace(duty, operation='SOURCE_FIRST_PERSON_TOPIC')
        for duty in out.artifact_plan.duties))
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, forged_plan,
                                           out.artifact, _model_register=True)


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば', 'けれど', 'けれども'])
def test_scoped_self_wish_register_keeps_its_complete_written_outer_prefix(speaker, marker):
    original = '雨が続いている' + marker + '、' + speaker + 'は家で過ごしたいです。'
    body = original.removesuffix('です。') + '。'
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert len(out.source_meaning.expression_scopes) == 1
    assert out.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert not out.artifact_plan.declaration_eligible
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('text', [
    '余裕がないので、私は地域の活動に加わりたくない',
    '予定が合うなら、僕は海辺を歩きたい',
    'まだ時間はあるけれど、わたしは急ぎたくない',
    '友人が「私は待っているよ」と言ってくれたので、私は家で過ごしたい',
])
@pytest.mark.parametrize('polite_source', [False, True])
@pytest.mark.parametrize('stop', ['。', '！', '!'])
def test_scoped_self_wish_register_works_both_ways_without_changing_quote_polarity_or_emphasis(
        text, polite_source, stop):
    original = text + ('です' if polite_source else '') + stop
    body = text + ('' if polite_source else 'です') + stop
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact.body_blocks == (body,)


SCOPED_SELF_WISH = '雨が続いているので、私は家で過ごしたいです。'
SCOPED_SELF_WISH_BODY = '雨が続いているので、私は家で過ごしたい。'


@pytest.mark.parametrize('body', [
    '私は家で過ごしたい。',
    '雨が続いているなら、私は家で過ごしたい。',
    '雨が続いているけれど、私は家で過ごしたい。',
    '雪が続いているので、私は家で過ごしたい。',
    '雨が続いていないので、私は家で過ごしたい。',
    '雨が続いていたので、私は家で過ごしたい。',
    '雨が続いているので、家で過ごしたい。',
    '雨が続いているので、僕は家で過ごしたい。',
    '雨が続いているので、私は外で過ごしたい。',
    '雨が続いているので、私は家で過ごしたくない。',
    '雨が続いているので、私は家で過ごしたかった。',
    '雨が続いているので、私は家で過ごした。',
    '雨が続いているので、私は家で過ごしたいかもしれない。',
    '雨が続いているので、私は家で過ごしたいと友人が言った。',
    '雨が続いているので、私は家で過ごしたい！',
    '雨が続いているので、私は家で過ごしたい。私は嬉しい。',
    '雨が続いているので私は家で過ごしたい。',
    '雨が続いているので，私は家で過ごしたい。',
    '雨が続いているので、\n私は家で過ごしたい。',
])
def test_scoped_self_wish_register_never_changes_reason_narrator_or_complete_wish(body):
    assert evaluate(SCOPED_SELF_WISH, body).artifact is None


def test_scoped_self_wish_register_retains_every_quoted_word_and_outer_self():
    original = '友人が「私は待っているよ」と言ってくれたので、私は家で過ごしたいです。'
    body = original.removesuffix('です。') + '。'
    assert evaluate(original, body).artifact is not None
    assert evaluate(original, body.replace('私は待っているよ', '僕は待っているよ')).artifact is None
    assert evaluate(original, body.replace('私は家で', '家で')).artifact is None


@pytest.mark.parametrize('separator', ['、 ', '，\t', ',\u3000'])
def test_scoped_self_wish_register_keeps_the_source_separator_and_horizontal_pause(separator):
    original = SCOPED_SELF_WISH.replace('、', separator)
    body = SCOPED_SELF_WISH_BODY.replace('、', separator)
    assert evaluate(original, body).artifact is not None
    assert evaluate(original, SCOPED_SELF_WISH_BODY).artifact is None


def test_scoped_self_wish_register_cannot_borrow_a_narrator_from_another_saved_field():
    from test_piece_model_narrator_voice import evaluate as evaluate_saved
    other = '余裕がないので、私は地域の活動に加わりたくないです。'
    saved = source(SCOPED_SELF_WISH, field='memo', other=other)
    body = [SCOPED_SELF_WISH_BODY, other.removesuffix('です。') + '。']
    assert evaluate_saved(saved, body).artifact is not None
    assert evaluate_saved(saved, [body[0], body[1].replace('私は', '')]).artifact is None


def test_scoped_self_wish_register_keeps_original_and_supplemental_source_authors_separate():
    from test_cmee_piece_refined_sources import source as refined_source
    from test_piece_model_narrator_voice import evaluate as evaluate_saved
    answer = 'わたしは読書が好きです。'
    saved = refined_source(original=SCOPED_SELF_WISH, answer=answer)
    body = [SCOPED_SELF_WISH_BODY, 'わたしは読書が好きだ。']
    assert evaluate_saved(saved, body).artifact is not None
    assert evaluate_saved(saved, [body[0], body[1].replace('わたしは', '私は')]).artifact is None
    assert evaluate_saved(saved, [body[0], body[1].replace('わたしは', '')]).artifact is None


def test_scoped_self_wish_register_does_not_change_the_existing_literal_order_contract():
    original = '疲れているなら、私は本を読みたい。'
    canonical = evaluate(original, '私は、疲れているなら、本を読みたい。')
    assert canonical.artifact is not None
    validate_source_meaning_preservation(canonical.source_meaning, canonical.artifact_plan,
                                        canonical.artifact)
    retained = evaluate(original, original)
    assert retained.artifact is not None
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(retained.source_meaning, retained.artifact_plan,
                                            retained.artifact)


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('marker', ['ので', 'なら', 'ならば', 'けれど', 'けれども'])
@pytest.mark.parametrize('account', ['休みたい', '本を読みたい'])
def test_scoped_literal_register_retains_the_full_self_account_in_source_order(speaker, marker, account):
    original = f'疲れている{marker}、{speaker}は{account}です。'
    body = original.removesuffix('です。') + '。'
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact.body_blocks == (body,)
    assert len(out.source_meaning.expression_scopes) == 1
    assert out.artifact_plan.duties[0].operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
    assert not out.artifact_plan.declaration_eligible
    # Model register retention does not expand the native author contract.
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('account', ['休みたい', '本を読みたい', '氷みたい'])
@pytest.mark.parametrize('polite_source', [False, True])
@pytest.mark.parametrize('stop', ['。', '！', '!'])
def test_scoped_literal_register_keeps_non_wish_classification_and_terminal(account, polite_source, stop):
    from piece_v2_expression import _WISH_END
    from cocolon_meaning_experience_engine.piece_source import _scoped_self_topic
    text = f'寒いので、私は{account}'
    original = text + ('です' if polite_source else '') + stop
    body = text + ('' if polite_source else 'です') + stop
    out = evaluate(original, body)
    assert out.artifact is not None
    scope = out.source_meaning.expression_scopes[0]
    expression = original[slice(*scope.expression_scalar_span)]
    assert not _WISH_END.search(_scoped_self_topic(expression)['body'])
    assert not out.artifact_plan.declaration_eligible
    changed_stop = '。' if stop != '。' else '！'
    assert evaluate(original, body[:-1] + changed_stop).artifact is None


SCOPED_LITERAL = '疲れているので、私は本を読みたいです。'
SCOPED_LITERAL_BODY = '疲れているので、私は本を読みたい。'


@pytest.mark.parametrize('body', [
    '私は本を読みたい。',
    '疲れていないので、私は本を読みたい。',
    '疲れていたので、私は本を読みたい。',
    '疲れているなら、私は本を読みたい。',
    '疲れているけれど、私は本を読みたい。',
    '疲れているので、本を読みたい。',
    '疲れているので、僕は本を読みたい。',
    '疲れているので、私は新聞を読みたい。',
    '疲れているので、私は本を読みたくない。',
    '疲れているので、私は本を読みたかった。',
    '疲れているので、私は本を読んだ。',
    '疲れているので、私は本を読みたいかもしれない。',
    '疲れているので、私は本を読みたいと友人が言った。',
    '疲れているので、私は本を読みたい。私は嬉しい。',
    '疲れているので私は本を読みたい。',
    '疲れているので，私は本を読みたい。',
    '疲れているので、\n私は本を読みたい。',
])
def test_scoped_literal_register_does_not_change_context_self_or_complete_predicate(body):
    assert evaluate(SCOPED_LITERAL, body).artifact is None


@pytest.mark.parametrize('separator', ['、 ', '，\t', ',\u3000'])
def test_scoped_literal_register_retains_the_original_separator_and_pause(separator):
    original = SCOPED_LITERAL.replace('、', separator)
    body = SCOPED_LITERAL_BODY.replace('、', separator)
    assert evaluate(original, original).artifact is not None
    assert evaluate(original, body).artifact is not None
    assert evaluate(original, SCOPED_LITERAL_BODY).artifact is None


def test_scoped_literal_register_keeps_the_quote_inside_its_source_owned_outer_context():
    original = '友人が「私は先に休みたい」と言ったので、私は本を読みたいです。'
    body = original.removesuffix('です。') + '。'
    assert evaluate(original, body).artifact is not None
    for before, after in [
        ('私は先に休みたい', '僕は先に休みたい'),
        ('先に休みたい', '先に休んだ'),
        ('と言ったので', 'と言ったなら'),
        ('私は本を', '本を'),
        ('本を読みたい。', '本を読みたかった。'),
    ]:
        assert evaluate(original, body.replace(before, after)).artifact is None


def test_scoped_literal_register_does_not_extend_emphasized_literal_narrator_continuity():
    original = '疲れているので、私は休みたいです！私は読書が好きです。'
    body = '疲れているので、私は休みたい！私は読書が好きだ。'
    assert evaluate(original, body).artifact is not None
    assert evaluate(original, body.replace('私は読書が', '読書が')).artifact is None


def test_scoped_literal_register_keeps_separate_saved_fields_and_supplemental_authors():
    from test_cmee_piece_refined_sources import source as refined_source
    from test_piece_model_narrator_voice import evaluate as evaluate_saved
    other = '寒いなら、僕は休みたいです。'
    saved = source(SCOPED_LITERAL, field='memo', other=other)
    body = [SCOPED_LITERAL_BODY, '寒いなら、僕は休みたい。']
    assert evaluate_saved(saved, body).artifact is not None
    assert evaluate_saved(saved, [body[0], body[1].replace('僕は', '')]).artifact is None
    assert evaluate_saved(saved, [body[0], body[1].replace('僕は', '私は')]).artifact is None
    saved = refined_source(original=SCOPED_LITERAL, answer='わたしは読書が好きです。')
    body = [SCOPED_LITERAL_BODY, 'わたしは読書が好きだ。']
    assert evaluate_saved(saved, body).artifact is not None
    assert evaluate_saved(saved, [body[0], body[1].replace('わたしは', '私は')]).artifact is None
    assert evaluate_saved(saved, [body[0], body[1].replace('わたしは', '')]).artifact is None


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


@pytest.mark.parametrize('original,body', [
    (FOCAL, FOCAL_ORDER),
    (SCOPED_FOCAL, SCOPED_FOCAL_BODY),
    ('私が選びたいのは、工房で木を削る時間です。私はその時間があまり好きではありませんでした。',
     '私が選びたいのは、工房で木を削る時間だ。私はその時間があまり好きではなかった。'),
    (NAMED, '私が選びたいのは、同僚と展示を見る時間だ。その時間が好きだ。まだ、参加する日は決めていない。'),
    (EVALUATION, EVALUATION_CONTINUED),
    ('私は読書が好きです。私は料理が苦手でした。', '私は読書が好きだ。料理が苦手だった。'),
])
def test_model_register_reuses_source_focal_order_and_native_same_author_continuity(original, body):
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    # Native S7 keeps its prior literal register contract.
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('changed', [
    FOCAL_ORDER.replace('私が', '僕が'),
    FOCAL_ORDER.replace('大切にしたいのは', '大切にしたくないのは'),
    FOCAL_ORDER.replace('大切にしたいのは', '大切にしたかったのは'),
    FOCAL_ORDER.replace('大切にしたいのは', '大切にしたいかもしれないのは'),
    FOCAL_ORDER.replace('読む時間だ', '書く時間だ'),
    FOCAL_ORDER.replace('読む時間だ', '読む時間だった'),
    FOCAL_ORDER.replace('読む時間だ。', '読む時間だ！'),
    FOCAL_ORDER.replace('その時間が好きだ。', 'その時間が少し好きだ。'),
    FOCAL_ORDER.replace('その時間が好きだ。', 'その時間が好きではない。'),
    FOCAL_ORDER.replace('その時間が好きだ。', 'その時間が好きだった。'),
    FOCAL_ORDER.replace('その時間が好きだ。', 'その時間が好きかもしれない。'),
    FOCAL_ORDER.replace('その時間が', 'この時間が'),
    FOCAL_ORDER.replace('その時間が', 'その時間は'),
    'その時間が好きだ。' + FOCAL_ORDER.replace('その時間が好きだ。', ''),
    FOCAL_ORDER + '私は毎日読んでいる。',
])
def test_original_focal_order_retains_every_source_argument_operator_and_reference(changed):
    assert evaluate(FOCAL, changed).artifact is None


@pytest.mark.parametrize('changed', [
    SCOPED_FOCAL_BODY.replace('疲れているなら、', ''),
    SCOPED_FOCAL_BODY.replace('疲れているなら', '疲れているので'),
    SCOPED_FOCAL_BODY.replace('疲れているなら', '疲れていないなら'),
    SCOPED_FOCAL_BODY.replace('疲れているなら、私が', '私が疲れているなら、'),
    SCOPED_FOCAL_BODY.replace('聴く時間だ', '聴く時間だった'),
    SCOPED_FOCAL_BODY.replace('私が選びたい', '僕が選びたい'),
])
def test_original_focal_order_requires_entire_premise_in_its_source_order(changed):
    assert evaluate(SCOPED_FOCAL, changed).artifact is None


@pytest.mark.parametrize('changed', [
    '私が選びたいのは、同僚の西さんと展示を見る時間だ。その時間が好きだ。まだ、参加する日は決めていない。',
    '私が選びたいのは、同僚の東さんと展示を見る時間だ。その時間が好きだ。まだ、参加する日は決めていない。',
    '私が選びたいのは、友人と展示を見る時間だ。その時間が好きだ。まだ、参加する日は決めていない。',
])
def test_original_focal_order_still_requires_exact_public_role_abstraction(changed):
    assert evaluate(NAMED, changed).artifact is None


@pytest.mark.parametrize('changed', [
    EVALUATION_CONTINUED.replace('私にとって、', ''),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '僕は読書が好きだ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書が苦手だ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書がとても好きだ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書が好きではない。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書が好きだった。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書が好きかもしれない。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '映画が好きだ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書は好きだ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書も好きだ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '疲れているなら、読書が好きだ。'),
    EVALUATION_CONTINUED.replace('読書が好きだ。', '読書が好きだと友人が言った。'),
    EVALUATION_CONTINUED.replace('とても大切だ。', 'とても大切だった。'),
])
def test_same_author_register_ellipsis_preserves_all_evaluation_features(changed):
    assert evaluate(EVALUATION, changed).artifact is None


def test_first_evaluation_and_explicit_value_viewpoint_cannot_be_elided():
    assert evaluate('私は読書が好きです。', '読書が好きだ。').artifact is None
    original = '私は読書が好きです。私にとって料理が大切です。'
    assert evaluate(original, '私は読書が好きだ。私にとって料理が大切だ。').artifact is not None
    assert evaluate(original, '私は読書が好きだ。料理が大切だ。').artifact is None


@pytest.mark.parametrize('original,explicit,omitted', [
    ('私は読書が好きです。友人は先に帰った。私は料理が苦手です。',
     '私は読書が好きだ。友人は先に帰った。私は料理が苦手だ。',
     '私は読書が好きだ。友人は先に帰った。料理が苦手だ。'),
    ('私は読書が好きです。まだ、参加する日は決めていません。私は料理が苦手です。',
     '私は読書が好きだ。まだ、参加する日は決めていない。私は料理が苦手だ。',
     '私は読書が好きだ。まだ、参加する日は決めていない。料理が苦手だ。'),
    ('私は読書が好きです。僕は料理が苦手です。',
     '私は読書が好きだ。僕は料理が苦手だ。', '私は読書が好きだ。料理が苦手だ。'),
])
def test_register_ellipsis_stops_at_context_or_literal_speaker_change(original, explicit, omitted):
    assert evaluate(original, explicit).artifact is not None
    assert evaluate(original, omitted).artifact is None


def test_same_author_evaluation_register_ellipsis_cannot_cross_field_or_newline():
    first, second = '私は読書が好きです。', '私は料理が苦手です。'
    assert evaluate(first, ['私は読書が好きだ。', '私は料理が苦手だ。'], other=second).artifact is not None
    assert evaluate(first, ['私は読書が好きだ。', '料理が苦手だ。'], other=second).artifact is None
    assert evaluate(first + '\n' + second, ['私は読書が好きだ。', '料理が苦手だ。']).artifact is None


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
@pytest.mark.parametrize('pause', ['', '、', '，', ','])
def test_qualified_focal_wish_keeps_explicit_ga_and_adjacent_reference(speaker, pause):
    original = f'{speaker}が選びたいのは、木版画を彫る時間です。{speaker}はその時間が好きです。'
    body = f'{speaker}が{pause}木版画を彫る時間を選びたい。その時間が好きだ。'
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    with pytest.raises(PieceContractError):
        validate_source_meaning_preservation(out.source_meaning, out.artifact_plan, out.artifact)


@pytest.mark.parametrize('predicate', ['選びたい', '選びたくない', '大切にしたい', '大切にしたくない'])
@pytest.mark.parametrize('register', ['', 'です'])
def test_direct_ga_wish_retains_source_polarity_and_existing_register_pair(predicate, register):
    original = f'僕が{predicate}のは、静かな庭で過ごす時間です。'
    body = f'僕が静かな庭で過ごす時間を{predicate}{register}。'
    out = evaluate(original, body)
    assert out.status == EngineStatus.GENERATED, out.reason_codes


GA_BODY = FOCAL_BODY.replace('私は、', '私が、', 1)


@pytest.mark.parametrize('changed', [
    GA_BODY.replace('私が、', '僕が、'),
    GA_BODY.replace('私が、', '友人が、'),
    GA_BODY.replace('私が、', ''),
    GA_BODY.replace('私が、', '私が、、'),
    GA_BODY.replace('読む時間', '書く時間'),
    GA_BODY.replace('時間を大切', '時間が大切'),
    GA_BODY.replace('大切にしたい。', '大切にしたくない。'),
    GA_BODY.replace('大切にしたい。', '大切にしたかった。'),
    GA_BODY.replace('大切にしたい。', '大切にしたいかもしれない。'),
    GA_BODY.replace('大切にしたい。', '大切にしている。'),
    GA_BODY.replace('大切にしたい。', '大切にしたい！'),
    GA_BODY.replace('その時間', 'この時間'),
    GA_BODY.replace('その時間が好きだ。', 'その時間が苦手だ。'),
    GA_BODY.replace('その時間が好きだ。', 'その時間が好きだった。'),
    GA_BODY.replace('その時間が好きだ。', ''),
    'その時間が好きだ。' + GA_BODY.replace('その時間が好きだ。', ''),
    GA_BODY.replace('まだ、', ''),
    GA_BODY.replace('決めていない。', '決めた。'),
    GA_BODY + '私は毎日続けている。',
])
def test_direct_ga_never_loosens_source_wish_reference_or_reservation(changed):
    assert evaluate(FOCAL, changed).artifact is None


@pytest.mark.parametrize('predicate', ['選びたかった', '選びたいかもしれない', '大切にしている'])
def test_direct_ga_does_not_expand_to_past_modal_or_state_focal_predicates(predicate):
    original = f'私が{predicate}のは、静かな庭で過ごす時間です。'
    body = f'私が静かな庭で過ごす時間を{predicate}。'
    assert evaluate(original, body).artifact is None


def test_direct_ga_stays_inside_qualified_focal_source_and_field():
    assert evaluate('私は静かな庭で過ごす時間を選びたい。',
                    '私が静かな庭で過ごす時間を選びたい。').artifact is None
    scoped = '疲れているなら、私が選びたいのは、静かな庭で過ごす時間です。'
    assert evaluate(scoped, '疲れているなら、私が静かな庭で過ごす時間を選びたい。').artifact is None
    first, second = '私が選びたいのは、静かな庭で過ごす時間です。', '私は読書が好きです。'
    body = '私が静かな庭で過ごす時間を選びたい。'
    assert evaluate(first, [body, '私は読書が好きだ。'], other=second).artifact is not None
    assert evaluate(first, [body, '読書が好きだ。'], other=second).artifact is None
    assert evaluate('私が静かな庭で過ごす時間を選びたい。', body).artifact is None


def test_direct_ga_still_requires_source_proved_public_role():
    body = NAMED_BODY.replace('私は、', '私が、', 1)
    assert evaluate(NAMED, body).artifact is not None
    assert evaluate(NAMED, body.replace('同僚と', '友人と')).artifact is None
    assert evaluate(NAMED, body.replace('同僚と', '同僚の西さんと')).artifact is None


QUOTED_CONTEXT = '友人が「ゆっくりでいいよ」と言ってくれた。私は急がなくても一緒に過ごせることが嬉しかった。'
QUOTE_FEELING = dict(emotions=['喜び'], details=[dict(type='喜び', strength='strong')])


@pytest.mark.parametrize('speaker', ['私', 'わたし', '僕', 'ぼく', '俺', 'おれ'])
def test_one_literal_quote_retains_speaker_condition_possibility_and_past_feeling(speaker):
    original = QUOTED_CONTEXT.replace('私', speaker)
    out = evaluate(original, original, **QUOTE_FEELING)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in out.artifact_plan.duties)
    assert not out.source_meaning.personal_evaluations and not out.source_meaning.expression_scopes
    assert not out.artifact_plan.declaration_eligible
    assert out.artifact.eligible_formats == ('short_essay',)
    meaning = out.source_meaning
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert meaning.envelope.raw_utf8[slice(evidence.utf8_start, evidence.utf8_end)].decode() == node.value
        assert original[slice(evidence.scalar_start, evidence.scalar_end)] == node.value


@pytest.mark.parametrize('quoted', ['ゆっくりでいいよ', '急がず、待っていていいよ', 'また会いたい',
                                   '私は本を読む時間を選びたい', '一緒に帰ろう😊'])
def test_one_quote_is_retained_as_context_without_promoting_its_own_words_to_a_self_intent(quoted):
    original = QUOTED_CONTEXT.replace('ゆっくりでいいよ', quoted)
    out = evaluate(original, original, **QUOTE_FEELING)
    assert out.artifact is not None
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in out.artifact_plan.duties)


def test_literal_quote_uses_native_keep_and_original_paragraph_partition():
    original = QUOTED_CONTEXT.replace('。私', '。\n私')
    out = evaluate(original, original.split('\n'), **QUOTE_FEELING)
    assert out.artifact.body_blocks == tuple(original.split('\n'))
    saved = source(original, field='memo', **QUOTE_FEELING)
    native = MeaningExperienceEngine().generate(request(saved))
    assert native.artifact and native.artifact.body_blocks == out.artifact.body_blocks
    assert native.source_meaning.envelope.raw_utf8.decode() == original


@pytest.mark.parametrize('changed', [
    QUOTED_CONTEXT.replace('友人が', '私が'),
    QUOTED_CONTEXT.replace('言ってくれた', '言ってあげた'),
    QUOTED_CONTEXT.replace('ゆっくりでいいよ', '急いだほうがいいよ'),
    QUOTED_CONTEXT.replace('「', '').replace('」', ''),
    QUOTED_CONTEXT.replace('「', '『').replace('」', '』'),
    QUOTED_CONTEXT.replace('急がなくても', '急いだので'),
    QUOTED_CONTEXT.replace('過ごせる', '過ごせた'),
    QUOTED_CONTEXT.replace('嬉しかった', '嬉しい'),
    QUOTED_CONTEXT.replace('嬉しかった', '嬉しくなかった'),
    QUOTED_CONTEXT.replace('私は', '僕は'),
    QUOTED_CONTEXT.split('。')[1] + '。',
    QUOTED_CONTEXT + 'だから私は友人を信頼している。',
])
def test_quoted_keep_does_not_justify_a_rewritten_quote_speaker_time_or_causal_story(changed):
    assert evaluate(QUOTED_CONTEXT, changed, **QUOTE_FEELING).artifact is None


@pytest.mark.parametrize('quoted', [
    '「ゆっくりでいいよ', 'ゆっくりでいいよ」', '「」', '「 \t　」',
    '「ゆっくりでいいよ」「待っているよ」', '「外「内」外」', '「外『内』外」',
    '『ゆっくりでいいよ』', '“ゆっくりでいいよ”', '"ゆっくりでいいよ"',
    '「ゆっくり\nでいいよ」', '「ゆっくり\rでいいよ」', '「ゆっくり\r\nでいいよ」',
])
def test_quote_admission_retains_refusal_for_unread_boundaries(quoted):
    from piece_v2_generation import _sentences
    original = QUOTED_CONTEXT.replace('「ゆっくりでいいよ」', quoted)
    with pytest.raises(PieceContractError) as exc:
        _sentences(original)
    assert exc.value.detail == 'quoted_discourse_not_yet_supported'
    assert evaluate(original, original.splitlines(), **QUOTE_FEELING).artifact is None


@pytest.mark.parametrize('original', [
    '同僚が「私の友人の佐藤さんも来る」と言ってくれた。佐藤さんが資料を届けた。',
    '私の友人の佐藤さんが来た。同僚が「佐藤さんも来る」と言ってくれた。',
    '同僚が「私の友人の佐藤さんも来る」と言ってくれた。',
    '同僚が「佐藤さんも来る」と言ってくれた。',
])
def test_quote_names_do_not_borrow_a_global_role_alias_across_speakers(original):
    from cocolon_meaning_experience_engine.piece_source import _role_bindings
    with pytest.raises(PieceContractError) as exc:
        _role_bindings(original)
    assert exc.value.detail == 'public_identity_is_material'
    assert evaluate(original, original, **QUOTE_FEELING).artifact is None


def test_name_outside_quote_keeps_existing_public_role_binding():
    original = QUOTED_CONTEXT.replace('友人が', '友人の佐藤さんが')
    assert evaluate(original, QUOTED_CONTEXT, **QUOTE_FEELING).artifact is not None
    assert evaluate(original, original, **QUOTE_FEELING).artifact is None


def test_a_later_reported_quote_keeps_the_other_speakers_promise_in_its_own_field():
    thought = '余裕があるなら、私が選びたいのは、陶芸です。'
    report = '「続けます」と友人が言った。'
    out = evaluate(thought, [thought, report], other=report)
    assert out.artifact and out.artifact.body_blocks == (thought, report)
    assert out.artifact_plan.duties[-1].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'


def test_quote_cannot_cross_saved_field_boundaries_or_supply_a_hidden_input_mode():
    assert evaluate('友人が「ゆっくりでいいよ',
                    ['友人が「ゆっくりでいいよ', '」と言ってくれた。'],
                    other='」と言ってくれた。', **QUOTE_FEELING).artifact is None
    assert evaluate(QUOTED_CONTEXT, QUOTED_CONTEXT, emotions=[], details=[]).artifact is None
    assert evaluate(QUOTED_CONTEXT, QUOTED_CONTEXT).artifact is None


@pytest.mark.parametrize('quoted', ['連絡先はuser@example.com', 'api_key: fictional-only', 'ゆっくり\u200bでいいよ'])
def test_literal_quote_never_hides_existing_contact_credential_or_control_detectors(quoted):
    original = QUOTED_CONTEXT.replace('ゆっくりでいいよ', quoted)
    assert evaluate(original, original, **QUOTE_FEELING).artifact is None


@pytest.mark.parametrize('quoted', [
    'ゆっくりでいいよ。待つよ', 'ゆっくりでいいよ！', 'ゆっくりでいいよ!',
    'どうする？', 'どうする?', 'ゆっくりでいいよ!!', 'どうする！？',
    '急がずに来て。私は待っているよ😊',
    '私は本を読む時間を選びたい。まだ決めていない',
])
def test_quote_internal_stops_remain_in_one_literal_proposition(quoted):
    from piece_v2_generation import _sentences
    original = QUOTED_CONTEXT.replace('ゆっくりでいいよ', quoted)
    first, second = original.rsplit('。私', 1)
    expected = [first + '。', '私' + second]
    assert _sentences(original) == expected
    out = evaluate(original, original, **QUOTE_FEELING)
    assert out.artifact, out.reason_codes
    assert [node.value for node in out.source_meaning.graph.nodes] == expected
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT' for d in out.artifact_plan.duties)
    assert not out.source_meaning.personal_evaluations
    assert not out.source_meaning.expression_scopes
    assert not out.artifact_plan.declaration_eligible
    for node, evidence in zip(out.source_meaning.graph.nodes, out.source_meaning.evidence, strict=True):
        assert original[evidence.scalar_start:evidence.scalar_end] == node.value
        assert out.source_meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end] == node.value.encode()
    saved = source(original, field='memo', **QUOTE_FEELING)
    native = MeaningExperienceEngine().generate(request(saved))
    assert native.artifact and native.artifact.body_blocks == (original,)


QUOTED_STOPS = QUOTED_CONTEXT.replace('ゆっくりでいいよ', 'ゆっくりでいいよ。待つよ！')


@pytest.mark.parametrize('changed', [
    QUOTED_STOPS.replace('。待つよ！', '！'),
    QUOTED_STOPS.replace('ゆっくりでいいよ。待つよ！', '待つよ！ゆっくりでいいよ。'),
    QUOTED_STOPS.replace('ゆっくりでいいよ。', 'ゆっくりでいいよ！'),
    QUOTED_STOPS.replace('待つよ！', '待たないよ！'),
    QUOTED_STOPS.replace('友人が', '私が'),
    QUOTED_STOPS.replace('言ってくれた', '言ってあげた'),
    QUOTED_STOPS.replace('「', '').replace('」', ''),
    QUOTED_STOPS.replace('急がなくても', '急いだので'),
    QUOTED_STOPS.replace('過ごせる', '過ごせた'),
    QUOTED_STOPS.replace('嬉しかった', '嬉しい'),
    QUOTED_STOPS.replace('嬉しかった', '嬉しくなかった'),
    QUOTED_STOPS.replace('私は', '僕は'),
    QUOTED_STOPS.split('」')[0] + '」と言ってくれた。',
    QUOTED_STOPS + 'だから私は友人を信頼している。',
])
def test_internal_quote_stops_do_not_license_omission_reordering_or_changed_meaning(changed):
    assert evaluate(QUOTED_STOPS, changed, **QUOTE_FEELING).artifact is None


@pytest.mark.parametrize('separator', [' ', '\t', '　', '\n', '\r\n', '\r'])
def test_quote_stop_spans_preserve_written_gaps_and_paragraph_boundaries(separator):
    from piece_v2_generation import _sentences
    first, second = QUOTED_STOPS.rsplit('。私', 1)
    original = first + '。' + separator + '私' + second
    expected = [first + '。', '私' + second]
    assert _sentences(original) == expected
    blocks = expected if '\n' in separator or '\r' in separator else [''.join(expected)]
    out = evaluate(original, blocks, **QUOTE_FEELING)
    assert out.artifact, out.reason_codes
    for node, evidence in zip(out.source_meaning.graph.nodes, out.source_meaning.evidence, strict=True):
        assert original[evidence.scalar_start:evidence.scalar_end] == node.value
    if len(blocks) == 2:
        assert evaluate(original, [''.join(expected), ''], **QUOTE_FEELING).artifact is None


@pytest.mark.parametrize('quoted_source', [QUOTED_CONTEXT, QUOTED_STOPS])
@pytest.mark.parametrize('separator', ['\u00a0', '\u2002', '\u2003'])
def test_quote_spans_keep_the_existing_unicode_separator_bytes(quoted_source, separator):
    from piece_v2_generation import _sentences
    first, second = quoted_source.rsplit('。私', 1)
    original = first + '。' + separator + '私' + second
    assert _sentences(original) == [first + '。', separator + '私' + second]
    out = evaluate(original, original, **QUOTE_FEELING)
    assert out.artifact, out.reason_codes
    assert out.artifact.body_blocks == (original,)
    for node, evidence in zip(out.source_meaning.graph.nodes, out.source_meaning.evidence, strict=True):
        assert original[evidence.scalar_start:evidence.scalar_end] == node.value
        assert out.source_meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end] == node.value.encode()
    native = MeaningExperienceEngine().generate(request(source(original, field='memo', **QUOTE_FEELING)))
    assert native.artifact and native.artifact.body_blocks == (original,)
    assert evaluate(original, quoted_source, **QUOTE_FEELING).artifact is None


@pytest.mark.parametrize('outside', ['と言ってくれた！！', 'と言ってくれた!?', 'と言ってくれた。！'])
def test_quote_internal_runs_do_not_expand_outer_sentence_punctuation(outside):
    from piece_v2_generation import _sentences
    original = QUOTED_STOPS.replace('と言ってくれた。', outside)
    with pytest.raises(PieceContractError):
        _sentences(original)
    assert evaluate(original, original, **QUOTE_FEELING).artifact is None


def test_quote_internal_stops_do_not_increase_the_existing_raw_stop_budget():
    original = QUOTED_CONTEXT.replace('ゆっくりでいいよ', '大丈夫！！！！待つよ！')
    out = evaluate(original, original, **QUOTE_FEELING)
    assert out.artifact is None
    assert out.reason_codes == ('content_envelope',)


@pytest.mark.parametrize('quoted', [
    '私の友人の佐藤さんも来る。待つよ！',
    '佐藤さんも来る。待つよ！',
    '連絡先はuser@example.com。待つよ！',
    'api_key: fictional-only。待つよ！',
    'ゆっくり\u200bでいいよ。待つよ！',
])
def test_quote_internal_stops_cannot_hide_names_contacts_credentials_or_controls(quoted):
    original = QUOTED_CONTEXT.replace('ゆっくりでいいよ', quoted)
    assert evaluate(original, original, **QUOTE_FEELING).artifact is None


def test_internal_quote_stops_cannot_bridge_saved_fields_or_supply_an_input_selection():
    first, second = QUOTED_STOPS.rsplit('。私', 1)
    assert evaluate(first + '。', [first + '。', '私' + second],
                    other='私' + second, **QUOTE_FEELING).artifact is not None
    assert evaluate('友人が「ゆっくりでいいよ。',
                    ['友人が「ゆっくりでいいよ。', '待つよ！」と言ってくれた。'],
                    other='待つよ！」と言ってくれた。', **QUOTE_FEELING).artifact is None
    assert evaluate(QUOTED_STOPS, QUOTED_STOPS, emotions=[], details=[]).artifact is None
    assert evaluate(QUOTED_STOPS, QUOTED_STOPS).artifact is None


def test_internal_quote_stops_preserve_the_existing_outside_public_role():
    original = QUOTED_STOPS.replace('友人が', '友人の佐藤さんが')
    assert evaluate(original, QUOTED_STOPS, **QUOTE_FEELING).artifact is not None
    assert evaluate(original, QUOTED_STOPS.replace('友人が', '同僚が'), **QUOTE_FEELING).artifact is None
    assert evaluate(original, original, **QUOTE_FEELING).artifact is None


def test_literal_quote_stops_do_not_move_an_external_conditional_wish_inside_the_quote():
    report = QUOTED_STOPS.rsplit('。私', 1)[0] + '。'
    original, body = report + SCOPED_FOCAL, report + SCOPED_FOCAL_BODY
    out = evaluate(original, body)
    assert out.artifact, out.reason_codes
    assert [d.operation for d in out.artifact_plan.duties] == [
        'KEEP_COMPLETE_SOURCE_CONTEXT', 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON',
        'KEEP_COMPLETE_SOURCE_CONTEXT']
    assert len(out.source_meaning.expression_scopes) == 1
    assert evaluate(original, body.replace('疲れているなら、', '')).artifact is None
    assert evaluate(original, body.replace('選びたい', '選ぶ')).artifact is None
