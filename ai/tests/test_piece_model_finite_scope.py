"""Extra finite-scope and receipt-byte checks for the explicit model arm.

Fictional CPU candidates only. These examples test bounded source/output
preservation and do not claim general Japanese understanding or human review.
"""
from dataclasses import replace
from hashlib import sha256
import json
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PieceModelInputV1, prepare_piece_model_request, receive_piece_model_candidate,
)
from piece_v2_contract import PieceContractError
from piece_v2_generation import generate_piece_candidate
from test_cmee_piece_finite_request_reuse import source
from test_cmee_piece_refined_sources import source as refined_source


def request(s):
    original = getattr(s, 'original', s)
    return PieceGenerationRequest('model-finite-scope', s, original.owner_id,
        original.saved_input_id, original.source_version)


def candidate(req, blocks):
    prepared = prepare_piece_model_request(req)
    receipt = receive_piece_model_candidate(prepared,
        raw_output=json.dumps({'body_blocks': list(blocks)}, ensure_ascii=False),
        finish_reason='stop', provider='fixed-test', model='no-model-called')
    return PieceModelInputV1(prepared, receipt)


def result(req, blocks):
    return MeaningExperienceEngine().generate(req, semantic_input=candidate(req, blocks))


def test_self_repetition_can_be_removed_only_after_explicit_self_in_the_same_block():
    req = request(source('私は同僚に資料の確認を頼みました。私は友人に旅程を相談しませんでした。'))
    body = '私は同僚に資料の確認を頼んだ。友人に旅程を相談しなかった。'
    out = result(req, (body,))
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact.piece_text == body
    assert body != req.source.original_text
    assert result(req, ('同僚に資料の確認を頼んだ。友人に旅程を相談しなかった。',)).artifact is None


@pytest.mark.parametrize('body', [
    '私は同僚から資料の確認を頼んだ。私は友人に旅程を相談しなかった。',
    '私は同僚に資料の確認を頼んだ。私は友人から旅程を相談しなかった。',
])
def test_written_counterpart_case_cannot_disappear_from_an_otherwise_equal_event_key(body):
    req = request(source('私は同僚に資料の確認を頼みました。私は友人に旅程を相談しませんでした。'))
    assert result(req, ('私は同僚に資料の確認を頼んだ。私は友人に旅程を相談しなかった。',)).artifact
    assert result(req, (body,)).artifact is None


@pytest.mark.parametrize('answer,body', [
    ('今は、私は嬉しいです。', '現在は、私は嬉しい。'),
    ('私はとても寂しかったです。', '私はとても寂しかった。'),
    ('私はあまり嬉しくなかったです。', '私はあまり嬉しくなかった。'),
])
def test_supplemental_feeling_register_keeps_its_own_time_negation_and_degree(answer, body):
    req = request(refined_source(original='私は同僚に資料の確認を頼みました。', answer=answer))
    out = result(req, ('私は同僚に資料の確認を頼んだ。', body))
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact.body_blocks[1] == body
    assert out.source_meaning.supplemental.saved_snapshot is None
    assert not out.source_meaning.supplemental.selected_feelings


@pytest.mark.parametrize('changed', [
    '今は、私は嬉しい。', '今も、私はとても嬉しい。',
    '今も、私は嬉しかった。', '私は嬉しい。',
])
def test_feeling_current_scope_continuation_particle_and_degree_cannot_be_dropped_or_added(changed):
    req = request(refined_source(original='私は同僚に資料の確認を頼みました。', answer='今も、私は嬉しいです。'))
    assert result(req, ('私は同僚に資料の確認を頼んだ。', '今も、私は嬉しい。')).artifact
    assert result(req, ('私は同僚に資料の確認を頼んだ。', changed)).artifact is None


def test_b8_rejects_a_different_but_semantically_equivalent_body_not_returned_by_the_bound_receipt():
    req = request(source('私は同僚に資料の確認を頼みました。'))
    selected = candidate(req, ('私は同僚に資料の確認を頼んだ。',))
    out = MeaningExperienceEngine().generate(req, semantic_input=selected)
    assert out.artifact is not None
    # This alternative is source-faithful, but it is not the actual raw model
    # candidate that this request acquired. A fresh hash cannot rebind it.
    body = '私は同僚に資料の確認を頼みました。'
    substituted = replace(out, artifact=replace(out.artifact, body_blocks=(body,),
        piece_text=body, piece_text_hash=sha256(body.encode()).hexdigest()))
    with patch.object(MeaningExperienceEngine, 'generate', return_value=substituted):
        with pytest.raises(PieceContractError) as error:
            generate_piece_candidate(req.source, authenticated_owner_id=req.expected_owner_id,
                                     model_candidate=selected)
    assert error.value.detail == 'piece_engine_artifact_binding'


def test_unknown_model_finish_never_calls_the_finite_author_as_a_backup():
    req = request(source('私は同僚に資料の確認を頼みました。'))
    selected = candidate(req, ('私は同僚に資料の確認を頼んだ。',))
    prepared = selected.prepared
    receipt = receive_piece_model_candidate(prepared, raw_output=selected.receipt.raw_output,
                                            finish_reason='length')
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
               side_effect=AssertionError('no finite backup on model failure')):
        out = MeaningExperienceEngine().generate(req, semantic_input=PieceModelInputV1(prepared, receipt))
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert out.reason_codes == ('piece_model_receipt_token_limit',)
