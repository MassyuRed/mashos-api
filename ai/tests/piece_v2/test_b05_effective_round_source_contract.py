"""Genuine Q3 source chains, mocked model preservation and exact old ADD bytes.

The existing fixtures issue real questions and persist real answer/checkpoint
events in isolated SQL. Natural replies and model candidates are synthetic.
These checks make no assertion about live 4B quality or a person's device.
"""
from dataclasses import fields
import json
import os
from pathlib import Path
import subprocess
import sys
import types

import pytest

from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_refined_source
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from cocolon_meaning_experience_engine import piece_refined as refined
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PieceModelInputV1, generate_piece_model, prepare_piece_model_request,
    receive_piece_model_candidate,
)
from piece_model_source import build_piece_model_messages
from test_b05_piece_answer_update_saved_pipeline import (
    ACTION, ANSWERS, answer_update_db, natural_refined_db, refined_pipeline_db,
    saved_piece_db, prepare_later_update, run,
)
from test_b05_refined_preview_saved_pipeline import _finish_refined_pipeline


def _source_case(db, monkeypatch, texts, *, action=''):
    state, _, calls = prepare_later_update(db, monkeypatch, len(texts), 'ADD', 'free',
        answer_texts=texts, action_text=action)
    handoff = run(PieceSavedSourceAdapter().resolve_refined_handoff(
        'Bearer ' + state['token'], state['source_id'],
        supplemental_answer_identity=state['snapshot_before']['thread']['latest_answer_event_id'],
        opted_in=True))
    source = project_saved_refined_source(handoff, opted_in=True)
    request = PieceGenerationRequest('effective-round-contract', source, state['owner'],
        state['source_id'], source.original.source_version)
    return state, calls, handoff, request


@pytest.mark.parametrize('texts,retained,absent,prior_rounds', [
    ([ANSWERS['REVISE'], '「私は家族を守りたい」ではなく「私は資料を読みたい」です。',
      ANSWERS['ADD']], ['資料を読みたい', ANSWERS['ADD']],
     ['仕事を続けたい', '家族を守りたい'], [2]),
    ([ANSWERS['REVISE'], ANSWERS['ADD'], '「私は家族を守りたい」は取り消します。'],
     [], ['仕事を続けたい', '家族を守りたい', ANSWERS['ADD']], []),
])
def test_three_round_chain_keeps_only_active_replacement_and_selected_latest(
        answer_update_db, monkeypatch, texts, retained, absent, prior_rounds):
    state, calls, _, request = _source_case(answer_update_db, monkeypatch, texts)
    assert request.source.effective_round_sources
    assert [answer.round_index for answer, _ in request.source.prior_revisions] == prior_rounds
    outcome = refined.generate_refined_piece(request)
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    for value in retained:
        assert value in outcome.artifact.piece_text
    for value in absent:
        assert value not in outcome.artifact.piece_text
    for part in outcome.source_meaning.prior_revisions:
        for evidence in part.evidence:
            assert part.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == (
                part.frozen_answer.source.answer_text_private[evidence.scalar_start:evidence.scalar_end])
    monkeypatch.setenv('PIECE_MODEL_SOURCE', 'off')
    result = _finish_refined_pipeline(answer_update_db, monkeypatch, state,
        expected_blocks=list(outcome.artifact.body_blocks))
    assert len(calls) == 4
    assert result['detail']['piece_text'] == outcome.artifact.piece_text
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1


def test_four_required_blocks_are_rejected_without_dropping_a_source_or_acquiring_model(
        answer_update_db, monkeypatch):
    _, calls, _, request = _source_case(answer_update_db, monkeypatch,
        [ANSWERS['REVISE'], ANSWERS['ADD']], action=ACTION)
    before = (request.source.original.saved_original_json,
              request.source.supplemental.answer_text_private,
              request.source.prior_revisions)
    meaning = refined.build_refined_meaning(request)
    plan = refined._plans(meaning)
    assert sum(len(child.block_node_ids) for _, child in refined.refined_meaning_parts(meaning, plan)) == 4
    with pytest.raises(ValueError, match='piece_model_block_partition'):
        prepare_piece_model_request(request)
    assert refined.generate_refined_piece(request).status is not EngineStatus.GENERATED
    assert before == (request.source.original.saved_original_json,
                      request.source.supplemental.answer_text_private,
                      request.source.prior_revisions)
    assert len(calls) == 3  # Emlis only; no Piece model source was installed.


@pytest.mark.parametrize('mutation', ['revive_prior', 'drop_active_prior'])
def test_model_candidate_cannot_revive_or_drop_a_prior_replacement(
        answer_update_db, monkeypatch, mutation):
    _, _, _, request = _source_case(answer_update_db, monkeypatch,
        [ANSWERS['REVISE'], '「私は家族を守りたい」ではなく「私は資料を読みたい」です。',
         ANSWERS['ADD']])
    native = refined.generate_refined_piece(request)
    assert native.status is EngineStatus.GENERATED, native.reason_codes
    blocks = list(native.artifact.body_blocks)
    prepared = prepare_piece_model_request(request)

    def admit(values):
        receipt = receive_piece_model_candidate(prepared,
            raw_output=json.dumps({'body_blocks': values}, ensure_ascii=False), finish_reason='stop')
        return generate_piece_model(request, PieceModelInputV1(prepared, receipt))

    assert admit(blocks).status is EngineStatus.GENERATED
    index = next(i for i, block in enumerate(blocks) if '資料を読みたい' in block)
    if mutation == 'revive_prior':
        blocks[index] = blocks[index].replace('資料を読みたい', '家族を守りたい')
    else:
        blocks.pop(index)
    assert admit(blocks).status is not EngineStatus.GENERATED


# These exact blobs were independently fetched at API 7f51a64e6cb58668ad5d418480b7de4499bfe6fa.
# They are also present in the local object database. The test never networks,
# checks out another tree, or changes the running product files.
_BASE_7F51_BLOBS = (
    ('cocolon_meaning_experience_engine.piece_refined', '37e4be3c327077668d573f0b61cb992e5eaaf47a'),
    ('cocolon_meaning_experience_engine.preparation_sources', 'cb6681f9b12f37002c6ffa93599291f177a39105'),
    ('piece_model_source', '79e9fc3a6fcd54e87db7e7131e28415ad3317b0e'),
    ('piece_v2_source_adapter', '424eaddda5a2ebb1b05e4ba79004d00720a003b7'),
)


def test_independent_add_chain_keeps_exact_7f51_prepared_messages_and_private_saved_bytes(
        answer_update_db, monkeypatch):
    state, _, handoff, request = _source_case(answer_update_db, monkeypatch,
        [ANSWERS['ADD'], '今は、私は怖い。'], action=ACTION)
    assert not request.source.effective_round_sources
    actual_outcome = refined.generate_refined_piece(request)
    assert actual_outcome.status is EngineStatus.GENERATED, actual_outcome.reason_codes
    actual_prepared = prepare_piece_model_request(request)
    actual = (actual_prepared.private_json,
              build_piece_model_messages(actual_prepared, include_authoring_constraints=True,
                                         source_request=request),
              refined.serialize_refined_piece(actual_outcome))
    root = Path(__file__).resolve().parents[3]
    baseline_repo = Path(os.environ.get('PIECE_ADD_COMPAT_BASE_REPOSITORY', root))
    with monkeypatch.context() as baseline:
        modules = {}
        for name, blob in _BASE_7F51_BLOBS:
            raw = subprocess.check_output(['git', 'cat-file', 'blob', blob], cwd=baseline_repo)
            assert subprocess.check_output(['git', 'hash-object', '--stdin'], input=raw,
                                           cwd=root).decode().strip() == blob
            module = types.ModuleType(name)
            module.__package__ = name.rpartition('.')[0]
            module.__file__ = str(root / '7f51-reference' / (name.replace('.', '/') + '.py'))
            baseline.setitem(sys.modules, name, module)
            exec(compile(raw, module.__file__, 'exec'), module.__dict__)
            modules[name] = module
        old_adapter = modules['piece_v2_source_adapter']
        old_original = old_adapter.PieceSavedOriginal(**{
            field.name: getattr(handoff.original, field.name)
            for field in fields(old_adapter.PieceSavedOriginal)})
        old_handoff = old_adapter._natural_later_add_handoff(old_original,
            state['snapshot_before'], handoff.supplemental.answer_id)
        old_source = old_adapter.project_saved_refined_source(old_handoff, opted_in=True)
        old_request = PieceGenerationRequest(request.request_id, old_source,
            state['owner'], state['source_id'], old_source.original.source_version)
        old_refined = modules['cocolon_meaning_experience_engine.piece_refined']
        old_outcome = old_refined.generate_refined_piece(old_request)
        assert old_outcome.status is EngineStatus.GENERATED, old_outcome.reason_codes
        old_prepared = prepare_piece_model_request(old_request)
        expected = (old_prepared.private_json,
                    modules['piece_model_source'].build_piece_model_messages(old_prepared,
                        include_authoring_constraints=True, source_request=old_request),
                    old_refined.serialize_refined_piece(old_outcome))
        assert expected == actual
