"""Explicit selection, current-state reread and existing DB lineage projection."""
import asyncio
from dataclasses import replace
import json

import pytest

from piece_v2_contract import PieceContractError, canonical_json_bytes
from piece_v2_source_adapter import PieceSavedSourceAdapter, project_saved_refined_lineage
from test_b05a_piece_refined_source_handoff import (
    ANSWER, AUTH, INPUT, OWNER, Store, auth, resolve, snapshot,
)


def test_refined_reference_has_only_seven_body_free_fields_and_rereads():
    store = Store(snapshot())
    result = asyncio.run(PieceSavedSourceAdapter(store=store).resolve_refined_source_ref(
        AUTH, INPUT, supplemental_answer_identity=ANSWER, opted_in=True))
    assert set(result) == {
        'source_input_id', 'source_input_version', 'source_input_bundle_commitment',
        'emlis_observation_stage', 'emlis_observation_result_identity',
        'question_need_decision_identity', 'supplemental_answer_identity',
    }
    assert result['emlis_observation_stage'] == 'refined_observation'
    assert result['supplemental_answer_identity'] == ANSWER
    assert store.calls == [(OWNER, INPUT), (OWNER, INPUT)]
    assert 'PRIVATE' not in json.dumps(result)


@pytest.mark.parametrize('change', ['opt_out', 'wrong_answer', 'raced_revision', 'raced_answer'])
def test_selection_and_current_state_cannot_be_replaced(change):
    class RacingStore(Store):
        async def read(self, *args, **kwargs):
            if self.calls and change == 'raced_revision':
                self.value['thread']['revision'] += 1
            if self.calls and change == 'raced_answer':
                self.value['events'][4]['payload']['source']['answer_text_private'] += ' '
            return await super().read(*args, **kwargs)
    adapter = PieceSavedSourceAdapter(store=RacingStore(snapshot()))
    with pytest.raises(PieceContractError):
        asyncio.run(adapter.resolve_refined_source_ref(
            AUTH, INPUT, supplemental_answer_identity=INPUT if change == 'wrong_answer' else ANSWER,
            opted_in=change != 'opt_out'))


def test_canonical_db_lineage_preserves_separate_supplement_commitment():
    saved = resolve(snapshot())
    private = saved.lineage_payload()
    line = project_saved_refined_lineage(saved, opted_in=True)
    assert len(line) == 8 and len(line['source_input']) == 5 and len(line['observation']) == 7
    assert line['semantic_source_roles'] == ['original_input', 'supplemental_answer']
    assert line['observation']['supplemental_answer_bundle_commitment'] == private['observation']['supplemental_answer_bundle_commitment']
    assert saved.lineage_payload() == private
    line['observation']['supplemental_answer_identity'] = INPUT
    assert saved.lineage_payload() == private
    with pytest.raises(PieceContractError):
        project_saved_refined_lineage(saved, opted_in=False)
    private['refined_result_source_binding']['supplemental_answer_bundle_commitment'] = saved.original.record_commitment
    with pytest.raises(PieceContractError):
        project_saved_refined_lineage(replace(saved, _lineage_json=canonical_json_bytes(private)), opted_in=True)
