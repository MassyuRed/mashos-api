"""Finite answer-owned THEN feelings retain their actual source and time.

These are private CPU inputs. Saved QUESTION/ADD eligibility and ordinary SQL
are exercised by the separate saved-pipeline tests, not fabricated here.
"""
import json

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PIECE_FIELD_SLOTS_FORMAT, PieceModelInputV1, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from piece_v2_contract import PieceContractError
from piece_v2_generation import generate_piece_candidate
from test_cmee_piece_refined_sources import source, request


def model_result(answer, visible=None):
    selected = source(answer=answer)
    req = request(selected)
    prepared = prepare_piece_model_request(req)
    raw = json.dumps({'field_blocks': {
        'memo_0': '私は、陶芸を選びたい。',
        'answer_text_private_1': answer if visible is None else visible,
    }}, ensure_ascii=False)
    receipt = receive_piece_model_candidate(prepared, raw_output=raw,
        finish_reason='stop', candidate_format=PIECE_FIELD_SLOTS_FORMAT)
    return selected, MeaningExperienceEngine().generate(req,
        semantic_input=PieceModelInputV1(prepared, receipt))


@pytest.mark.parametrize('answer', [
    'その時、私は寂しかった。',
    'その時は、私は嬉しくなかった。',
    'その時も、僕はとても悲しかったです。',
    'あの時は、わたしは少し嬉しかった。',
    '当時は、おれは全然楽しくなかった。',
    'その時は本当は、俺は寂しかった。',
])
def test_source_native_and_model_keep_the_complete_answer_time_and_envelope(answer):
    selected, out = model_result(answer)
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    assert out.artifact.body_blocks[1] == answer
    native = MeaningExperienceEngine().generate(request(selected))
    assert native.status == EngineStatus.GENERATED, native.reason_codes
    assert native.artifact.body_blocks[1] == answer
    meaning = out.source_meaning.supplemental
    assert meaning.graph.nodes[0].value == answer
    assert meaning.saved_snapshot is None and not meaning.selected_feelings
    evidence = meaning.evidence[0]
    assert evidence.field_path == 'answer_text_private'
    assert meaning.envelope.source_role == 'SUPPLEMENTAL_ANSWER'
    assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == answer
    assert not meaning.nominal_references


@pytest.mark.parametrize('visible', [
    '私は寂しかった。',
    '今は、私は寂しかった。',
    '当時は、私は寂しかった。',
    'その時も、私は寂しかった。',
    'その時、私は寂しい。',
    'その時、私は寂しくなかった。',
    'その時、私はとても寂しかった。',
    'その時、友人は寂しかった。',
    'その時、私は寂しかった。だから陶芸を選んだ。',
])
def test_model_cannot_drop_replace_or_invent_answer_time_subject_or_predicate(visible):
    _, out = model_result('その時、私は寂しかった。', visible)
    assert out.artifact is None


@pytest.mark.parametrize('answer', [
    'その時、寂しかった。',
    'その時、友人は寂しかった。',
    'その時間、私は寂しかった。',
    'その時の私は寂しかった。',
    'その時、私はそれが寂しかった。',
    'その時、私は寂しかったかもしれない。',
    'その時、私は寂しかったなら、',
    'その時、私は寂しかった。私はそれを大切にしたい。',
])
def test_unread_references_fragments_and_other_people_do_not_gain_answer_eligibility(answer):
    _, out = model_result(answer)
    assert out.artifact is None


def test_written_then_feeling_does_not_expand_original_saved_source_eligibility():
    selected = source(original='その時、私は寂しかった。')
    with pytest.raises(PieceContractError):
        generate_piece_candidate(selected.original,
            authenticated_owner_id=selected.original.owner_id)


def test_now_and_no_time_source_cannot_acquire_then_from_model():
    for answer in ('私は寂しかった。', '今は、私は寂しい。'):
        _, out = model_result(answer, 'その時、私は寂しかった。')
        assert out.artifact is None
