"""Independent model-candidate mutations over the real Piece owners.

All raw candidates and inputs are fictional, fixed CPU material. No provider,
live source, database or native renderer runs here. A valid candidate is
required beside each mutation so an always-unavailable implementation cannot
satisfy these checks. This is finite preservation coverage, not general
Japanese semantic admission or independent human product acceptance.
"""
from dataclasses import replace
import json
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_contract import PieceContractError, canonical_json_bytes
from piece_v2_generation import generate_piece_candidate
from test_cmee_piece_finite_request_reuse import source as original_source
from test_cmee_piece_refined_sources import source as refined_source


def request(source, **changes):
    original = getattr(source, 'original', source)
    return PieceGenerationRequest(
        'independent-piece-model-candidate', source, original.owner_id,
        original.saved_input_id, original.source_version, **changes)


def model_input(req, blocks, *, raw=None, finish_reason='stop'):
    from cocolon_meaning_experience_engine.piece_semantic_admission import (
        PieceModelInputV1, prepare_piece_model_request, receive_piece_model_candidate,
    )
    prepared = prepare_piece_model_request(req)
    receipt = receive_piece_model_candidate(prepared, request_id=prepared.request_id,
        raw_output=json.dumps({'body_blocks': list(blocks)}, ensure_ascii=False) if raw is None else raw,
        finish_reason=finish_reason, provider='independent-fixed-cpu', model='no-model-called')
    return PieceModelInputV1(prepared, receipt)


def b8(req, candidate):
    return generate_piece_candidate(req.source, authenticated_owner_id=req.expected_owner_id,
        tier=req.tier, requested_format=req.requested_format, model_candidate=candidate)


def assert_admitted(req, blocks):
    candidate = model_input(req, blocks)
    forbidden = AssertionError('model admission must not replay a Piece text author')
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', side_effect=forbidden), \
         patch('cocolon_meaning_experience_engine.piece_refined.realize_refined_piece_artifact', side_effect=forbidden):
        outcome = MeaningExperienceEngine().generate(req, semantic_input=candidate)
        assert outcome.status == EngineStatus.GENERATED, outcome.reason_codes
        assert outcome.artifact is not None
        assert outcome.artifact.body_blocks == tuple(blocks)
        projected = b8(req, candidate)
    assert projected['content_payload']['body_blocks'] == list(blocks)
    assert projected['piece_text'] == '\n\n'.join(blocks)
    assert projected['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert projected['record_effect'] == projected['quota_effect'] == 0
    return candidate


def assert_refused(req, blocks):
    candidate = model_input(req, blocks)
    forbidden = AssertionError('an invalid model body must not trigger another author')
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', side_effect=forbidden), \
         patch('cocolon_meaning_experience_engine.piece_refined.realize_refined_piece_artifact', side_effect=forbidden):
        outcome = MeaningExperienceEngine().generate(req, semantic_input=candidate)
        assert outcome.artifact is None
        with pytest.raises(PieceContractError):
            b8(req, candidate)


@pytest.mark.parametrize('before,after', [
    ('私は同僚に資料の確認を頼みました。', '私は同僚に資料の確認を頼んだ。'),
    ('私は司書に展示の設営を相談しませんでした。', '私は司書に展示の設営を相談しなかった。'),
])
def test_valid_model_body_can_differ_from_the_existing_canonical_author(before, after):
    req = request(original_source(before))
    legacy = generate_piece_candidate(req.source, authenticated_owner_id=req.expected_owner_id)
    assert legacy['piece_text'] != after
    assert_admitted(req, (after,))


@pytest.mark.parametrize('body', [
    '同僚は私に資料の確認を頼んだ。',
    '私は司書に資料の確認を頼んだ。',
    '私は同僚に日程の変更を頼んだ。',
    '私は同僚に資料の確認を頼まれた。',
    '私は同僚に資料の確認を頼まなかった。',
    '私は同僚に資料の確認を頼む。',
    '私は同僚に資料の確認を頼みたい。',
    'あなたは同僚に資料の確認を頼んだ。',
    'Emlisは同僚に資料の確認を頼んだ。',
    '私は同僚に資料の確認を頼んだ。私は承諾した。',
    '私は同僚に資料の確認を頼んだ。だから安心した。',
    '私は同僚に資料の確認を頼んだ。見知らぬ新しい意味です。',
])
def test_roles_voice_negation_time_modality_and_extra_claims_are_not_lexical_matches(body):
    req = request(original_source('私は同僚に資料の確認を頼みました。'))
    assert_admitted(req, ('私は同僚に資料の確認を頼んだ。',))
    assert_refused(req, (body,))


@pytest.mark.parametrize('changed', [
    '今日、私は同僚に資料の確認を頼みました。',
    '私は同僚に資料の確認を頼みました。',
])
def test_written_day_is_not_dropped_or_reassigned(changed):
    req = request(original_source('昨日、私は同僚に資料の確認を頼んだ。'))
    assert_admitted(req, ('昨日、私は同僚に資料の確認を頼みました。',))
    assert_refused(req, (changed,))


@pytest.mark.parametrize('changed', [
    '私は同僚に資料の確認を頼んだ。',
    '私は同僚に資料の確認を頼んだ。もう決めました。',
    '私は同僚に資料の確認を頼んだ。きっとそうだ。',
])
def test_unread_reservation_is_not_silently_discarded_by_a_recognized_first_clause(changed):
    text = '私は同僚に資料の確認を頼んだ。かもしれない。'
    req = request(original_source(text))
    assert_admitted(req, (text,))
    assert_refused(req, (changed,))


@pytest.mark.parametrize('blocks', [
    ('私は同僚に資料の確認を頼んだ。',),
    ('私は司書に展示の設営を相談した。',),
    ('私は同僚に資料の確認を頼んだ。', '私は同僚に資料の確認を頼んだ。'),
    ('私は司書に展示の設営を相談した。', '私は同僚に資料の確認を頼んだ。'),
    ('私は同僚に資料の確認を頼んだ。私は司書に展示の設営を相談した。',),
])
def test_both_written_fields_keep_their_complete_partition_and_multiplicity(blocks):
    req = request(original_source('私は司書に展示の設営を相談した。',
        other='私は同僚に資料の確認を頼んだ。'))
    assert_admitted(req, ('私は同僚に資料の確認を頼みました。', '私は司書に展示の設営を相談しました。'))
    assert_refused(req, blocks)


@pytest.mark.parametrize('blocks', [
    ('私は陶芸を選びたい。',),
    ('今は、私は嬉しい。',),
    ('今は、私は嬉しい。', '私は陶芸を選びたい。'),
    ('私は陶芸を選びたい。', '今は、友人は嬉しい。'),
    ('私は陶芸を選びたい。', '今は、あなたは嬉しい。'),
    ('私は陶芸を選びたい。', '以前は、私は嬉しい。'),
    ('私は陶芸を選びたい。', '私は嬉しい。'),
    ('私は陶芸を選びたい。', '今は、私は嬉しくない。'),
    ('私は陶芸を選びたい。', '今は、私は嬉しい。だから陶芸を選んだ。'),
])
def test_refined_candidate_cannot_move_erase_or_reinterpret_the_selected_answer(blocks):
    req = request(refined_source(answer='今は、私は嬉しい。'))
    assert_admitted(req, ('私は陶芸を選びたい。', '今は、私は嬉しい。'))
    assert_refused(req, blocks)


@pytest.mark.parametrize('body', [
    '私は友人のAliceさんに資料の確認を頼んだ。',
    '私はAliceさんに資料の確認を頼んだ。',
])
def test_model_cannot_keep_a_name_when_existing_public_role_abstraction_is_required(body):
    saved = original_source('私は友人のAliceさんに資料の確認を頼んだ。',
        emotions=['平穏'], details=[dict(type='平穏', strength='weak')])
    req = request(saved)
    assert_admitted(req, ('私は友人に資料の確認を頼んだ。',))
    assert_refused(req, (body,))


def test_nonself_clauses_cannot_be_reordered_by_a_role_blind_multiset():
    saved = original_source('同僚は私に資料の確認を頼んだ。司書は私に展示の設営を相談した。',
        emotions=['平穏'], details=[dict(type='平穏', strength='weak')])
    req = request(saved)
    assert_admitted(req, ('同僚は私に資料の確認を頼みました。司書は私に展示の設営を相談しました。',))
    assert_refused(req, ('司書は私に展示の設営を相談しました。同僚は私に資料の確認を頼みました。',))


def test_receipt_of_another_original_or_selected_answer_is_not_a_capability():
    first = request(original_source('私は同僚に資料の確認を頼みました。'))
    old = assert_admitted(first, ('私は同僚に資料の確認を頼んだ。',))
    second = request(original_source('私は司書に資料の確認を頼みました。'))
    assert MeaningExperienceEngine().generate(second, semantic_input=old).artifact is None
    with pytest.raises(PieceContractError):
        b8(second, old)
    refined = request(refined_source(answer='今は、私は嬉しい。'))
    answer_input = assert_admitted(refined, ('私は陶芸を選びたい。', '今は、私は嬉しい。'))
    changed = request(refined_source(answer='今は、私は悲しい。'))
    assert MeaningExperienceEngine().generate(changed, semantic_input=answer_input).artifact is None
    with pytest.raises(PieceContractError):
        b8(changed, answer_input)


def test_same_words_do_not_allow_receipt_reuse_after_metadata_or_answer_time_changes():
    from cocolon_meaning_experience_engine.emlis_thread_source import freeze_supplemental_answer
    first = request(original_source('私は同僚に資料の確認を頼みました。'))
    old = assert_admitted(first, ('私は同僚に資料の確認を頼んだ。',))
    record = json.loads(first.source.saved_original_json)
    record['category'] = ['仕事']
    changed = replace(first, source=replace(first.source, saved_original_json=canonical_json_bytes(record)))
    assert MeaningExperienceEngine().generate(changed, semantic_input=old).artifact is None
    with pytest.raises(PieceContractError):
        b8(changed, old)
    refined = request(refined_source(answer='今は、私は嬉しい。'))
    original_answer = assert_admitted(refined, ('私は陶芸を選びたい。', '今は、私は嬉しい。'))
    later = replace(refined.source.supplemental, recorded_at='2026-11-09T01:03:00Z')
    changed = replace(refined, source=replace(refined.source, supplemental=later,
        supplemental_commitment='sha256:' + freeze_supplemental_answer(later).envelope.raw_sha256))
    assert MeaningExperienceEngine().generate(changed, semantic_input=original_answer).artifact is None
    with pytest.raises(PieceContractError):
        b8(changed, original_answer)


@pytest.mark.parametrize('raw,finish', [
    ('{"body_blocks":["私は同僚に資料の確認を頼んだ。"],"claims":["trusted"]}', 'stop'),
    ('{"body_blocks":["私は同僚に資料の確認を頼んだ。"],"body_blocks":["別の本文。"]}', 'stop'),
    ('{"body_blocks":["私は同僚に資料の確認を頼んだ。"]}', 'length'),
])
def test_unapproved_model_envelope_duplicate_keys_and_truncation_do_not_admit(raw, finish):
    req = request(original_source('私は同僚に資料の確認を頼みました。'))
    assert_admitted(req, ('私は同僚に資料の確認を頼んだ。',))
    candidate = model_input(req, (), raw=raw, finish_reason=finish)
    assert MeaningExperienceEngine().generate(req, semantic_input=candidate).artifact is None
    with pytest.raises(PieceContractError):
        b8(req, candidate)


def test_prior_p4_semantic_profile_still_uses_its_own_bounded_admission():
    from test_cmee_piece_semantic_snapshot import context
    req, old_input = context()
    result = MeaningExperienceEngine().generate(req, semantic_input=old_input)
    assert result.status == EngineStatus.GENERATED
    assert result.artifact.piece_text == req.source.original_text
    assert result.snapshot.semantic_profile == 'piece_candidate_snapshot.v1'
