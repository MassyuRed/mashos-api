"""Opt-in refined composition keeps real source roles and the existing author."""
from dataclasses import replace
import hashlib
import json
from unittest.mock import patch

import pytest
from piece_v2_contract import canonical_json_bytes, PieceContractError
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_thread_source import freeze_supplemental_answer
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
import cocolon_meaning_experience_engine.piece_refined as refined


def source(original='私が選びたいのは、陶芸です。', answer='私は考える時間を大切にしたい。'):
    record = dict(id='refined-test-input', created_at='2026-11-09T01:00:00Z',
        memo=original, memo_action=None, category=['趣味', '価値観'],
        emotions=['平穏'], emotion_details=[dict(type='平穏',strength='weak')])
    saved = PieceSourceSnapshot('refined-test-owner', record['id'], 'emlis.current_input_bundle.v1',
        original, saved_original_json=canonical_json_bytes(record))
    supplemental = SupplementalAnswerSource('refined-test-answer', 'refined-test-thread',
        'refined-logical-question', 1, 'emlis-original-envelope', answer, '2026-11-09T01:02:00Z')
    return refined.PieceRefinedSourceSnapshot(saved, supplemental, saved.owner_id,
        'refined-question-event', 'refined-observation-event',
        'sha256:'+hashlib.sha256(saved.saved_original_json).hexdigest(),
        'sha256:'+freeze_supplemental_answer(supplemental).envelope.raw_sha256, True, 'ADD')


def request(s, **kw):
    return PieceGenerationRequest('refined-test-request', s, s.original.owner_id,
        s.original.saved_input_id, s.original.source_version, **kw)


def produce(s=None, **kw):
    return MeaningExperienceEngine().generate(request(s or source(), **kw))


@pytest.mark.parametrize('tier', ['free','plus','premium'])
def test_two_real_envelopes_reach_existing_author_and_private_reread(tier):
    s=source(); original_bytes=s.original.saved_original_json
    old=generate_piece_candidate(s.original, authenticated_owner_id=s.original.owner_id)
    result=produce(s,tier=tier)
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    assert result.artifact.piece_text == '私は、陶芸を選びたい。\n\n私は、考える時間を大切にしたい。'
    assert result.artifact.body_blocks[0] == old['piece_text']
    assert result.artifact.eligible_formats == ('short_essay',)
    assert result.source_meaning.original.envelope.source_role == 'ORIGINAL_USER_INPUT'
    m=result.source_meaning.supplemental
    frozen=freeze_supplemental_answer(s.supplemental)
    assert m.envelope == frozen.envelope and m.envelope.source_role == 'SUPPLEMENTAL_ANSWER'
    assert m.saved_snapshot is None and not m.selected_feelings
    assert result.source_meaning.original.saved_snapshot == s.original
    for sentence, ev in zip(m.sentences,m.evidence,strict=True):
        assert ev.source_envelope_id == frozen.envelope.envelope_id
        assert ev.field_path == 'answer_text_private'
        assert frozen.envelope.raw_utf8[ev.utf8_start:ev.utf8_end].decode() == s.supplemental.answer_text_private[sentence.source_start:sentence.source_end]
        assert ev.field_utf8_start > 0 and ev.scalar_start == sentence.source_start
    raw=refined.serialize_refined_piece(result); digest=hashlib.sha256(raw).hexdigest()
    forbidden=AssertionError('saved read must not generate or parse')
    with patch.object(MeaningExperienceEngine,'generate',side_effect=forbidden), \
         patch.object(refined,'build_refined_meaning',side_effect=forbidden), \
         patch.object(refined,'_plans',side_effect=forbidden), \
         patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=forbidden), \
         patch.object(refined,'validate_refined_preservation',side_effect=forbidden):
        assert refined.read_saved_refined_artifact(raw,expected_state_sha256=digest) == result.artifact
    assert s.original.saved_original_json == original_bytes
    state=json.loads(raw)
    assert state['sources']['supplemental']['source_role']=='SUPPLEMENTAL_ANSWER'
    assert state['sources']['original']['original_text']==s.original.original_text
    assert state['sources']['supplemental']['answer_text_private']==s.supplemental.answer_text_private
    assert state['plan']['source_roles']==['ORIGINAL_USER_INPUT','SUPPLEMENTAL_ANSWER']


@pytest.mark.parametrize('change', [
    dict(opted_in=False), dict(opted_in=1), dict(supplemental_owner_id='other-owner'),
    dict(original_commitment='sha256:'+'0'*64), dict(supplemental_commitment='sha256:'+'0'*64),
    dict(question_need_decision_identity=''), dict(refined_result_identity=''),
    dict(supplemental_update_operation='REVISE'), dict(supplemental_update_operation='WITHDRAW')])
def test_ineligible_private_source_is_not_composed(change):
    result=produce(replace(source(),**change))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


@pytest.mark.parametrize('answer',[
    'それを大切にしたい。', '訂正します。私は陶芸を選びたくない。',
    '私は陶芸ではなく絵画を選びたい。', '考える時間です。',
    '私は何を選びたいですか。', '私は考えるなら、',
    '私は連絡先test@example.comを残したい。'])
def test_fragments_questions_corrections_and_unsafe_answers_not_appended(answer):
    result=produce(source(answer=answer))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


@pytest.mark.parametrize('change',[dict(round_index=2),dict(source_role='ORIGINAL_USER_INPUT'),
    dict(answer_id='refined-test-input'),dict(question_id=''),dict(source_version='unknown')])
def test_answer_qualification_is_not_an_original_alias(change):
    s=source(); a=replace(s.supplemental,**change)
    # Keep source commitment when malformed; do not claim rehash authenticates identity.
    result=produce(replace(s,supplemental=a))
    assert result.status == EngineStatus.UNAVAILABLE and result.artifact is None


@pytest.mark.parametrize('wrong',[
    '私は、陶芸を選びたくない。\n\n私は、考える時間を大切にしたい。',
    '私は、陶芸を選びたい。\n\n友人は、考える時間を大切にしたい。',
    '私は、陶芸を選びたい。\n\n私は、考える時間を大切にしたい。だから安心した。',
    '私は、考える時間を大切にしたい。\n\n私は、陶芸を選びたい。',
    '私は、陶芸を選びたい。'])
def test_rehashed_wrong_completed_body_is_rejected_without_author_replay(wrong):
    result=produce(); blocks=tuple(wrong.split('\n\n'))
    artifact=replace(result.artifact, body_blocks=blocks,piece_text=wrong,
                     piece_text_hash=hashlib.sha256(wrong.encode()).hexdigest())
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',side_effect=AssertionError('author')):
        with pytest.raises(PieceContractError):
            refined.validate_refined_preservation(result.source_meaning,result.artifact_plan,artifact)


def test_swapped_child_meaning_cannot_certify_another_source():
    first=produce(); other=produce(source(answer='私は庭で休む時間を大切にしたい。'))
    forged=replace(first.source_meaning, supplemental=other.source_meaning.supplemental)
    with pytest.raises(PieceContractError):
        refined.validate_refined_preservation(forged,other.artifact_plan,other.artifact)


def test_rehashed_wrong_answer_envelope_offsets_rejected():
    result=produce(); m=result.source_meaning.supplemental
    bad=replace(m,evidence=(replace(m.evidence[0],utf8_start=0),))
    with pytest.raises(PieceContractError):
        refined.validate_supplemental_meaning(bad)


def test_saved_state_uses_expected_store_digest_not_mutable_embedded_hash():
    result=produce();raw=refined.serialize_refined_piece(result);digest=hashlib.sha256(raw).hexdigest()
    row=json.loads(raw);row['artifact']['piece_text']='別の本文。'
    row['artifact']['body_blocks']=['別の本文。']
    row['artifact']['piece_text_hash']=hashlib.sha256('別の本文。'.encode()).hexdigest()
    with pytest.raises(PieceContractError):
        refined.read_saved_refined_artifact(canonical_json_bytes(row),expected_state_sha256=digest)


@pytest.mark.parametrize('fmt',['quote','declaration'])
def test_refined_slice_does_not_infer_a_declaration_or_detach_a_quote(fmt):
    assert produce(tier='premium',requested_format=fmt).artifact is None
