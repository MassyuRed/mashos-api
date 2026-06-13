# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_blind_qa_material import (
    apply_p7_blind_qa_review_to_scorecard_row,
    build_p7_blind_qa_candidate,
    build_p7_blind_qa_material,
)
from emlis_ai_p7_event_bridge import P7_RATING_REQUIRED_DIMENSIONS, build_p7_scorecard_row
from emlis_ai_p7_long_run_gate_handoff import (
    P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION,
    assert_p7_long_run_gate_handoff_contract,
    build_p7_long_run_gate_candidate_material,
    build_p7_long_run_gate_handoff,
)
from test_emlis_ai_p7_event_bridge_20260612 import _event, _handoff

SECRET_INPUT = "P7-7 raw input must never be serialized"
SECRET_COMMENT = "P7-7 comment_text body must never be serialized"
SECRET_REVIEW = "P7-7 reviewer free text must never be serialized"


def _row(
    *,
    row_id: str = "p7_long_row",
    family: str = "history_line_eligible",
    sequence_id: str = "sequence_7",
    sequence_index: int = 1,
    sequence_length: int = 7,
    history_line_eligible: bool = True,
) -> dict[str, object]:
    return build_p7_scorecard_row(
        product_quality_event=_event(row_id=row_id, family=family),
        p7_handoff_summary=_handoff(),
        sequence={
            "sequence_id": sequence_id,
            "sequence_index": sequence_index,
            "sequence_length": sequence_length,
            "history_line_eligible": history_line_eligible,
        },
    )


def _cleared(row: dict[str, object]) -> dict[str, object]:
    out = dict(row)
    out["red_refs"] = []
    out["hold_refs"] = []
    out["blocker_refs"] = []
    out["blocker_ids"] = []
    return out


def _review_for_row(row: dict[str, object], *, index: int = 1, score: float = 0.94) -> dict[str, object]:
    candidate_id = build_p7_blind_qa_candidate(row, candidate_index=index)["candidate_id"]
    return {
        "candidate_id": candidate_id,
        "reviewer_id_hash": f"reviewer_hash_{index}",
        "dimensions": {dimension: {"score": score, "reason_codes": ["observed"]} for dimension in P7_RATING_REQUIRED_DIMENSIONS},
        "reason_codes": ["ratings_only_review"],
    }


def _complete_reviews(rows: list[dict[str, object]], *, score: float = 0.94) -> list[dict[str, object]]:
    return [_review_for_row(row, index=index, score=score) for index, row in enumerate(rows, start=1)]


def _scored_history_rows() -> list[dict[str, object]]:
    specs = [
        ("score_seq_1", "history_line_eligible", "sequence_1", 1, 1, 0.80),
        ("score_seq_3", "long_meaning_arc", "sequence_3", 3, 3, 0.90),
        ("score_seq_7", "relationship_gratitude_recovery", "sequence_7", 7, 7, 0.94),
    ]
    rows: list[dict[str, object]] = []
    for row_id, family, sequence_id, sequence_index, sequence_length, score in specs:
        base = _cleared(
            _row(
                row_id=row_id,
                family=family,
                sequence_id=sequence_id,
                sequence_index=sequence_index,
                sequence_length=sequence_length,
                history_line_eligible=True,
            )
        )
        rows.append(apply_p7_blind_qa_review_to_scorecard_row(base, _review_for_row(base, score=score)))
    return rows


def test_p7_7_default_red_hold_rows_become_blocked_candidate_material_not_release() -> None:
    row = _row(sequence_id="sequence_1", sequence_index=1, sequence_length=1, history_line_eligible=False)
    handoff = build_p7_long_run_gate_handoff([row])
    assert_p7_long_run_gate_handoff_contract(handoff)

    assert handoff["schema_version"] == P7_LONG_RUN_GATE_HANDOFF_SCHEMA_VERSION
    assert handoff["candidate_status"] == "blocked"
    assert handoff["long_run_candidate_ready"] is False
    assert handoff["release_allowed"] is False
    assert handoff["product_gate_ready"] is False
    assert handoff["long_run_candidate_is_release_ready"] is False
    assert handoff["product_pass_is_release_ready"] is False
    assert "unresolved_red_refs_present" in handoff["candidate_blocked_or_review_required_reason_codes"]
    assert "unresolved_hold_refs_present" in handoff["candidate_blocked_or_review_required_reason_codes"]
    assert "blind_qa_review_missing" in handoff["candidate_blocked_or_review_required_reason_codes"]
    assert set(handoff["unresolved_red_refs"]) >= {"P7-RED-001", "P7-RED-002", "P7-RED-003"}


def test_p7_7_can_mark_long_run_candidate_material_ready_without_release_when_red_hold_reviews_and_repetition_are_clear() -> None:
    rows = _scored_history_rows()
    blind = build_p7_blind_qa_material(rows)
    assert blind["review_missing_count"] == 0

    handoff = build_p7_long_run_gate_candidate_material(rows, blind_qa_material=blind)
    assert_p7_long_run_gate_handoff_contract(handoff)

    assert handoff["candidate_status"] == "candidate_material_ready"
    assert handoff["candidate"]["candidate_material_ready"] is True
    assert handoff["product_gate_candidate_material_ready"] is True
    assert handoff["long_run_candidate_ready"] is True
    assert handoff["release_decision_input_ready"] is True
    assert handoff["release_allowed"] is False
    assert handoff["product_gate_ready"] is False
    assert handoff["long_run_candidate_is_release_ready"] is False
    assert handoff["candidate_blocked_or_review_required_reason_codes"] == []
    assert handoff["sequence_coverage"]["sequence_7_present"] is True
    assert handoff["history_line_metrics"]["history_line_value_increase_observed"] is True
    assert handoff["risk_metrics"]["surface_signature_repetition_detected"] is False
    assert handoff["blind_qa_summary"]["review_missing_count"] == 0


def test_p7_7_returns_to_p5_when_sequence_value_does_not_increase() -> None:
    rows = []
    for index, sequence_length in enumerate((1, 3, 7), start=1):
        base = _cleared(
            _row(
                row_id=f"flat_history_{index}",
                family="history_line_eligible",
                sequence_id=f"sequence_{sequence_length}",
                sequence_index=sequence_length,
                sequence_length=sequence_length,
                history_line_eligible=True,
            )
        )
        # Same score across 1/3/7 means P5 history-line value is not increasing.
        rows.append(apply_p7_blind_qa_review_to_scorecard_row(base, _review_for_row(base, score=0.82)))
    blind = build_p7_blind_qa_material(rows)
    handoff = build_p7_long_run_gate_handoff(rows, blind_qa_material=blind)

    assert handoff["candidate_status"] == "review_required"
    assert handoff["long_run_candidate_ready"] is False
    assert "p5_history_line_sequence_value_not_increased" in handoff["candidate_blocked_or_review_required_reason_codes"]
    assert "P5_User_Label_Connection" in handoff["required_followup_targets"]
    assert handoff["release_allowed"] is False


def test_p7_7_material_is_body_free_and_does_not_serialize_review_or_surface_bodies() -> None:
    rows = _scored_history_rows()
    blind = build_p7_blind_qa_material(rows)
    handoff = build_p7_long_run_gate_handoff(rows, blind_qa_material=blind)
    dumped = json.dumps(handoff, ensure_ascii=False, sort_keys=True)

    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_REVIEW not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_7_contract_rejects_release_product_gate_promotion_and_body_payload() -> None:
    rows = _scored_history_rows()
    blind = build_p7_blind_qa_material(rows)
    handoff = build_p7_long_run_gate_handoff(rows, blind_qa_material=blind)

    unsafe_release = dict(handoff)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_long_run_gate_handoff_contract(unsafe_release)

    unsafe_gate = dict(handoff)
    unsafe_gate["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_p7_long_run_gate_handoff_contract(unsafe_gate)

    unsafe_promotion = dict(handoff)
    unsafe_promotion["product_pass_is_release_ready"] = True
    with pytest.raises(ValueError):
        assert_p7_long_run_gate_handoff_contract(unsafe_promotion)

    unsafe_body = dict(handoff)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_p7_long_run_gate_handoff_contract(unsafe_body)
