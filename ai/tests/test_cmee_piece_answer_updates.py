"""Private active views keep one real answer update at its original sources.

The API tests separately obtain genuine issued QUESTION/ANSWER checkpoints.
This suite exercises the existing Piece author and S7 with fixed private views.
"""
from dataclasses import replace
import hashlib

import pytest

from piece_v2_contract import canonical_json_bytes, PieceContractError
from cocolon_meaning_experience_engine.piece_refined import (
    build_refined_meaning, _plans, generate_refined_piece,
    validate_active_original_meaning, validate_supplemental_meaning,
)
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    prepare_piece_model_request, receive_piece_model_candidate, generate_piece_model, PieceModelInputV1,
)
from cocolon_meaning_experience_engine.emlis_thread_source import freeze_supplemental_answer
from cocolon_meaning_experience_engine.contracts import EngineStatus
from test_cmee_piece_refined_sources import source, request


def update_source(operation='REVISE'):
    initial = source()
    record = dict(id=initial.original.saved_input_id, created_at='2026-11-09T01:00:00Z',
        memo='褒められたのに、嬉しくなかった。私は仕事を続けたい。',
        memo_action='私は資料を調べた。', category=['仕事'], emotions=['不安'],
        emotion_details=[dict(type='不安', strength='medium')])
    original = replace(initial.original, original_text=record['memo']+'\n\n'+record['memo_action'],
        saved_original_json=canonical_json_bytes(record))
    literal = ('「私は仕事を続けたい」ではなく「私は家族を守りたい」です。'
        if operation == 'REVISE' else '「私は仕事を続けたい」は取り消します。')
    answer = replace(initial.supplemental, answer_text_private=literal)
    return replace(initial, original=original, supplemental=answer,
        original_commitment='sha256:'+hashlib.sha256(original.saved_original_json).hexdigest(),
        supplemental_commitment='sha256:'+freeze_supplemental_answer(answer).envelope.raw_sha256,
        supplemental_update_operation=operation,
        original_active_ranges=(('memo',0,16),('memo_action',0,9)),
        supplemental_active_range=(16,25) if operation=='REVISE' else None)


@pytest.mark.parametrize('operation', ['REVISE','WITHDRAW'])
def test_update_uses_surviving_graph_and_existing_author_without_rewriting_sources(operation):
    selected = update_source(operation)
    original_raw = selected.original.saved_original_json
    answer_raw = selected.supplemental.answer_text_private
    result = generate_refined_piece(request(selected))
    assert result.status == EngineStatus.GENERATED, result.reason_codes
    artifact = result.artifact
    assert '私は仕事を続けたい' not in artifact.piece_text
    assert 'ではなく' not in artifact.piece_text and '取り消します' not in artifact.piece_text
    assert '褒められたのに、嬉しくなかった。' in artifact.piece_text
    assert '私は資料を調べた。' in artifact.piece_text
    assert ('私は家族を守りたい' in artifact.piece_text) == (operation=='REVISE')
    assert len(artifact.body_blocks) == (3 if operation=='REVISE' else 2)
    assert selected.original.saved_original_json == original_raw
    assert selected.supplemental.answer_text_private == answer_raw
    meaning = result.source_meaning
    assert meaning.original.saved_snapshot is selected.original
    for node, evidence in zip(meaning.original.graph.nodes, meaning.original.evidence, strict=True):
        assert meaning.original.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode()==node.value
    if operation=='REVISE':
        supplemental = meaning.supplemental
        evidence = supplemental.evidence[0]
        assert supplemental.graph.nodes[0].value == answer_raw[16:25] == '私は家族を守りたい'
        assert (evidence.scalar_start, evidence.scalar_end) == (16,25)
        assert supplemental.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == '私は家族を守りたい'
    else:
        assert meaning.supplemental is None and result.artifact_plan.supplemental_plan is None


@pytest.mark.parametrize('operation', ['REVISE','WITHDRAW'])
def test_same_model_body_preserved_but_revived_or_missing_claims_refused(operation):
    import json
    selected = update_source(operation)
    req = request(selected)
    prepared = prepare_piece_model_request(req)
    blocks = ['褒められたのに、嬉しくなかった。','私は資料を調べた。']
    if operation=='REVISE': blocks += ['私は家族を守りたい。']
    def run(values):
        receipt = receive_piece_model_candidate(prepared,
            raw_output=json.dumps(dict(body_blocks=values),ensure_ascii=False), finish_reason='stop')
        return generate_piece_model(req, PieceModelInputV1(prepared, receipt))
    actual = run(blocks)
    assert actual.status == EngineStatus.GENERATED, actual.reason_codes
    assert actual.artifact.body_blocks == tuple(blocks)
    revived = list(blocks); revived[0] += '私は仕事を続けたい。'
    assert run(revived).status != EngineStatus.GENERATED
    omitted = list(blocks); omitted[1] = '私は日程を決めた。'
    assert run(omitted).status != EngineStatus.GENERATED


@pytest.mark.parametrize('change', [
    dict(original_active_ranges=(('memo',0,15),('memo_action',0,9))),
    dict(original_active_ranges=(('memo_action',0,9),)),
    dict(original_active_ranges=(('memo_action',0,9),('memo',0,16))),
    dict(supplemental_active_range=(15,25)),
    dict(supplemental_active_range=(16,24)),
])
def test_partial_or_reordered_source_range_cannot_gain_update_admission(change):
    with pytest.raises(PieceContractError):
        meaning=build_refined_meaning(request(replace(update_source(),**change)))
        _plans(meaning)


def test_rehashed_wrong_absolute_evidence_or_source_view_is_not_accepted():
    meaning=build_refined_meaning(request(update_source()))
    original=meaning.original
    with pytest.raises(PieceContractError):
        validate_active_original_meaning(replace(original,
            evidence=(replace(original.evidence[0], scalar_end=15), *original.evidence[1:])))
    supplemental=meaning.supplemental
    with pytest.raises(PieceContractError):
        validate_supplemental_meaning(replace(supplemental,
            evidence=(replace(supplemental.evidence[0], utf8_start=0),)))
