"""Same qualified Q2 ADD across a database close/reopen and Piece save.

Auth and the Piece response are fixed CPU material. The actual Q2 commits,
saved source qualification, CMEE, preview/save RPCs and owner readers run in
isolated PGlite. This is not a model call, live Auth/DB or native image proof.
"""
import asyncio
import json
import os
from unittest.mock import patch

import pytest

from test_cmee_piece_request_saved_pipeline import saved_piece_db
from test_emlis_q3_application import Q3Database
from test_b05_refined_preview_saved_pipeline import (
    refined_pipeline_db, _prepare_refined_pipeline, _finish_refined_pipeline,
)


def _checkpoint_material(db, monkeypatch, state):
    """Use the same existing source and preparation owners before/after IO."""
    import api_account_visibility
    import emlis_thread_store
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from piece_v2_preview_service import _resolve_handoff, _prepare_model_inputs
    from piece_model_source import build_piece_model_messages

    async def verify(token):
        assert token == state['token']
        return state['owner']

    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    handoff = asyncio.run(_resolve_handoff(PieceSavedSourceAdapter(),
        'Bearer ' + state['token'], state['source_ref']))
    request, prepared = _prepare_model_inputs(handoff, state['request'])
    messages = build_piece_model_messages(prepared,
        include_authoring_constraints=True, source_request=request)
    return prepared, messages


@pytest.mark.skipif(not os.environ.get('Q2_PGLITE_MODULE'), reason='PGlite dependency not configured')
def test_qualified_refined_checkpoint_keeps_answer_lineage_and_exact_model_material(tmp_path):
    from emlis_thread_service import EmlisThreadService
    from cocolon_meaning_experience_engine.piece_semantic_admission import receive_piece_model_candidate

    fixture = saved_piece_db.__wrapped__()
    original_db = next(fixture)
    restored = None
    try:
        refined_pipeline_db.__wrapped__(original_db)
        with pytest.MonkeyPatch.context() as setup:
            state = _prepare_refined_pipeline(original_db, setup,
                'その時、私は寂しかった。', 'qualified-checkpoint-refined')
            # State is serialized without creating a second source or answer.
            state = json.loads(json.dumps(state, ensure_ascii=False))
            prepared, messages = _checkpoint_material(original_db, setup, state)
        path = tmp_path / 'qualified-refined.tar.gz'
        original_db.dump_checkpoint(path)
        original_db.proc.stdin.close()
        original_db.proc.wait(timeout=10)

        restored = Q3Database(checkpoint_path=path)
        with pytest.MonkeyPatch.context() as resumed:
            current, current_messages = _checkpoint_material(restored, resumed, state)
            assert current.request_id == prepared.request_id
            assert current.private_json == prepared.private_json
            assert current_messages == messages
            material = json.loads(current_messages[1]['content'])
            assert [source['role'] for source in material['sources']] == [
                'ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
            assert material['sources'][1]['source_id'] == state['snapshot_before']['thread']['latest_answer_event_id']
            slots = material['control']['field_slots']
            raw = json.dumps({'field_blocks': {key: slot['literal'] for key, slot in slots.items()}},
                             ensure_ascii=False)
            calls = []

            async def fixed_cpu_source(value):
                assert value == prepared
                calls.append(value.request_id)
                return receive_piece_model_candidate(value, raw_output=raw, finish_reason='stop',
                    provider='checkpoint.cpu.fixed', model=None,
                    candidate_format='piece.field_slots.v1')

            resumed.setattr('piece_model_source.application_piece_model_source', lambda: fixed_cpu_source)
            with patch.object(EmlisThreadService, 'start', side_effect=AssertionError('no new Emlis start')), \
                 patch.object(EmlisThreadService, 'answer', side_effect=AssertionError('no new answer')):
                result = _finish_refined_pipeline(restored, resumed, state)
            assert calls == [prepared.request_id]
            assert result['source_ref'] == state['source_ref']
            assert result['snapshot_before'] == state['snapshot_before']
            assert result['snapshot_after']['original'] == state['original']
            assert result['snapshot_after']['thread'] == state['snapshot_before']['thread']
            assert result['snapshot_after']['events'] == state['snapshot_before']['events']
            assert result['quota_consumptions'] == 1
            for key in ('piece_text', 'content_payload', 'visual_recipe', 'piece_text_hash',
                        'content_payload_hash', 'visual_recipe_hash', 'renderer_version'):
                assert result['preview'][key] == result['detail'][key] == result['persisted_row'][key]
    finally:
        if restored is not None:
            restored.proc.stdin.close()
            restored.proc.wait(timeout=10)
        fixture.close()
