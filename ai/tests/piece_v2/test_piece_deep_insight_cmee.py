"""Use only synthetic records and synthetic model receipts."""

from dataclasses import replace
import json

import pytest

from cocolon_meaning_experience_engine.piece_deep_insight import (
    ANSWER_FIELD, DEEP_INSIGHT_ANSWER_ROLE, PieceDeepInsightSourceSnapshot,
    validate_deep_insight_piece_source,
)
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PIECE_FIELD_SLOTS_FORMAT, PieceModelInputV1, piece_model_source_plan,
    prepare_piece_model_request, receive_piece_model_candidate,
)
from cocolon_meaning_experience_engine.piece_v1c import MODEL_MEMO_SELECTION_PROFILE, PieceGenerationRequest
from cocolon_meaning_experience_engine.preparation_sources import piece_model_field_slots
from piece_model_source import build_piece_model_messages
from piece_v2_contract import PieceContractError, canonical_json_bytes
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


OWNER = '6134755b-de55-40a4-8e03-327d08d49f3e'
INPUT = '66d4ed52-968a-4096-aa0d-d79c6334380b'
QUESTION = '76adecb9-8df3-44a5-8759-2bfe6fbe3756'
STAMP = '2026-11-07T09:23:00+00:00'
MEMO = '私は、静かな時間を大切にしたいです。'
ACTION = '私は友人に旅程を相談しました。'
ANSWER = '私は、相手の話を大切にしたい。'


@pytest.fixture
def source():
    original = dict(id=INPUT, memo=MEMO, memo_action=ACTION, created_at=STAMP,
        category=['人間関係'], emotions=[], emotion_details=[])
    snapshot = PieceSourceSnapshot(OWNER, INPUT, 'emlis.current_input_bundle.v1',
        '\n\n'.join((MEMO, ACTION)), saved_original_json=canonical_json_bytes(original))
    return PieceDeepInsightSourceSnapshot(snapshot, QUESTION, ANSWER, STAMP, 'sha256:' + 'a' * 64)


def request_for(source, owner=OWNER):
    return PieceGenerationRequest('synthetic-piece-deep-insight', source, owner, INPUT,
        source.original.source_version)


def model_receipt(source, answer, *, memo=MEMO, action=ACTION):
    request = request_for(source)
    prepared = prepare_piece_model_request(request, realization_profile=MODEL_MEMO_SELECTION_PROFILE)
    receipt = receive_piece_model_candidate(prepared,
        raw_output=json.dumps({'field_blocks': {
            'memo_0': memo, 'memo_action_1': action, 'answer_text_private_2': answer,
        }}, ensure_ascii=False), finish_reason='stop',
        candidate_format=PIECE_FIELD_SLOTS_FORMAT, realization_profile=MODEL_MEMO_SELECTION_PROFILE)
    return PieceModelInputV1(prepared, receipt)


def test_owner_bound_answer_is_separate_model_evidence_with_exact_utf8(source):
    validate_deep_insight_piece_source(source)
    model = model_receipt(source, ANSWER)
    material = model.prepared.payload()
    assert [item['source_id'] for item in material['sources']] == [INPUT, QUESTION]
    assert [slot['literal'] for slot in piece_model_field_slots(material).values()] == [MEMO, ACTION, ANSWER]
    answer_source = material['sources'][1]
    assert answer_source['parent_record_id'] == INPUT
    assert answer_source['role'] == DEEP_INSIGHT_ANSWER_ROLE
    assert answer_source['text_fields'] == {ANSWER_FIELD: ANSWER}
    assert 'question_text' not in model.prepared.private_json

    meaning, plan = piece_model_source_plan(request_for(source))
    assert meaning.original.envelope.source_record_id == INPUT
    assert meaning.supplemental.envelope.source_record_id == QUESTION
    assert plan.source_roles == ('ORIGINAL_USER_INPUT', DEEP_INSIGHT_ANSWER_ROLE)
    evidence, = meaning.supplemental.evidence
    assert evidence.field_path == ANSWER_FIELD
    assert (evidence.scalar_start, evidence.scalar_end) == (0, len(ANSWER))
    assert meaning.supplemental.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == ANSWER

    messages = build_piece_model_messages(model.prepared, include_authoring_constraints=True,
        source_request=request_for(source), include_editorial_choices=True)
    message_material = json.loads(messages[1]['content'])
    assert message_material['control']['field_slots']['answer_text_private_2']['literal'] == ANSWER
    assert 'question_text' not in messages[1]['content']

    candidate = generate_piece_candidate(source, authenticated_owner_id=OWNER, model_candidate=model)
    assert candidate['content_payload']['body_blocks'] == [MEMO, ACTION, ANSWER]
    assert candidate['eligible_formats'] == ['short_essay']


def test_selected_owner_answer_can_be_edited_with_its_written_condition_intact(source):
    source = replace(source, answer_text='疲れているなら、私は本を読みたいです。')
    revised = '私は、疲れているなら、本を読みたい。'
    candidate = generate_piece_candidate(source, authenticated_owner_id=OWNER,
        model_candidate=model_receipt(source, revised))
    assert candidate['content_payload']['body_blocks'][-1] == revised
    with pytest.raises(PieceContractError, match='piece_model_meaning_unassessed_or_changed'):
        generate_piece_candidate(source, authenticated_owner_id=OWNER,
            model_candidate=model_receipt(source, '私は、本を読みたい。'))


@pytest.mark.parametrize('substitution', [
    '相手の話を大切にしたくない。',
    'そのときは、相手の話を大切にしたい。',
    'そうしたから、相手の話を大切にしたい。',
    MEMO,
])
def test_same_model_cannot_change_selected_answer_attribution_or_meaning(source, substitution):
    with pytest.raises(PieceContractError, match='piece_model_meaning_unassessed_or_changed'):
        generate_piece_candidate(source, authenticated_owner_id=OWNER,
            model_candidate=model_receipt(source, substitution))


def test_selected_answer_must_be_meaningful_without_generated_question(source):
    elliptical = replace(source, answer_text='相手が一人の時です。')
    with pytest.raises(PieceContractError, match='expression_meaning_not_admitted'):
        validate_deep_insight_piece_source(elliptical)


def test_model_receipt_is_bound_to_immutable_source(source):
    stale = model_receipt(source, ANSWER)
    changed = replace(source, source_commitment='sha256:' + 'b' * 64)
    with pytest.raises(PieceContractError, match='piece_model_input_rejected'):
        generate_piece_candidate(changed, authenticated_owner_id=OWNER, model_candidate=stale)
    with pytest.raises(PieceContractError, match='piece_model_input_rejected'):
        generate_piece_candidate(source, authenticated_owner_id=QUESTION, model_candidate=stale)
    with pytest.raises(PieceContractError, match='piece_deep_insight_model_required'):
        generate_piece_candidate(source, authenticated_owner_id=OWNER)
