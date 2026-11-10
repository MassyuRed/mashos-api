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
