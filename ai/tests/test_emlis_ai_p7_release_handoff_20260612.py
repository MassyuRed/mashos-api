# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_blind_qa_material import apply_p7_blind_qa_review_to_scorecard_row, build_p7_blind_qa_material, build_p7_blind_qa_candidate
from emlis_ai_p7_event_bridge import P7_RATING_REQUIRED_DIMENSIONS, build_p7_scorecard_row
from emlis_ai_p7_long_run_gate_handoff import build_p7_long_run_gate_handoff
from emlis_ai_p7_release_handoff import (
    P7_RELEASE_HANDOFF_SCHEMA_VERSION,
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_product_release_decision import PRODUCT_RELEASE_DECISION_SCHEMA_VERSION
from test_emlis_ai_p7_event_bridge_20260612 import _event, _handoff

SECRET_INPUT = "P7-8 raw input must never be serialized"
SECRET_COMMENT = "P7-8 comment_text body must never be serialized"
SECRET_BODY = "P7-8 candidate body must never be serialized"


def _row(
    *,
    row_id: str,
    family: str,
    sequence_id: str,
    sequence_index: int,
    sequence_length: int,
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


def _ready_long_run_handoff() -> dict[str, object]:
    specs = [
        ("ready_seq_1", "history_line_eligible", "sequence_1", 1, 1, 0.80),
        ("ready_seq_3", "long_meaning_arc", "sequence_3", 3, 3, 0.90),
        ("ready_seq_7", "relationship_gratitude_recovery", "sequence_7", 7, 7, 0.94),
    ]
    rows: list[dict[str, object]] = []
    for index, (row_id, family, sequence_id, sequence_index, sequence_length, score) in enumerate(specs, start=1):
        base = _cleared(
            _row(
                row_id=row_id,
                family=family,
                sequence_id=sequence_id,
                sequence_index=sequence_index,
                sequence_length=sequence_length,
            )
        )
        rows.append(apply_p7_blind_qa_review_to_scorecard_row(base, _review_for_row(base, index=index, score=score)))
    blind = build_p7_blind_qa_material(rows)
    return build_p7_long_run_gate_handoff(rows, blind_qa_material=blind)


def test_p7_8_default_handoff_consumes_r13_red003_closure_but_keeps_holds_and_never_allows_release() -> None:
    handoff = build_p7_release_decision_handoff()
    assert_p7_release_decision_handoff_contract(handoff)

    assert handoff["schema_version"] == P7_RELEASE_HANDOFF_SCHEMA_VERSION
    assert handoff["handoff_target_schema_version"] == PRODUCT_RELEASE_DECISION_SCHEMA_VERSION
    assert handoff["release_decision_input_ready"] is False
    assert handoff["release_allowed"] is False
    assert handoff["release_input_status"] == "review_required"
    assert handoff["product_pass_is_release_ready"] is False
    assert handoff["product_pass_promoted_to_release_ready"] is False
    assert set(handoff["closed_red_refs"]) >= {"P7-RED-001", "P7-RED-002", "P7-RED-003"}
    assert handoff["unresolved_red_refs"] == []
    assert handoff["unresolved_timeout_refs"] == []
    assert set(handoff["unresolved_hold_refs"]) >= {"P7-HOLD-001", "P7-HOLD-002"}
    assert "full_backend_suite_green_unconfirmed" in handoff["required_followup_fixes"]


def test_p7_8_clean_long_run_candidate_still_waits_on_holds_after_r13_red003_closure_not_release() -> None:
    long_run = _ready_long_run_handoff()
    assert long_run["release_decision_input_ready"] is True
    assert long_run["long_run_candidate_ready"] is True

    handoff = build_p7_release_decision_handoff(
        long_run_gate_handoff=long_run,
        p7_runner_result={
            "runner_result_id": "p7_runner_clear_material",
            "release_decision_input_ready": True,
            "full_backend_suite_green_confirmed": True,
        },
    )
    assert_p7_release_decision_handoff_contract(handoff)

    assert handoff["source_material_status"]["release_decision_input_ready_from_long_run"] is True
    assert handoff["release_decision_input_ready"] is False
    assert handoff["release_input_status"] == "review_required"
    assert handoff["release_allowed"] is False
    assert handoff["release_decision_applied"] is False
    assert handoff["public_release_applied"] is False
    assert handoff["product_gate_ready"] is False
    assert handoff["product_pass_is_release_ready"] is False
    assert handoff["long_run_candidate_is_release_ready"] is False
    assert set(handoff["closed_red_refs"]) >= {"P7-RED-001", "P7-RED-002", "P7-RED-003"}
    assert handoff["unresolved_red_refs"] == []
    assert set(handoff["unresolved_hold_refs"]) >= {"P7-HOLD-001", "P7-HOLD-002", "P7-HOLD-003", "P7-HOLD-004"}
    assert handoff["unresolved_timeout_refs"] == []
    assert handoff["release_boundary"]["release_allowed_true_requires_p10_release_readiness"] is True


def test_p7_8_review_missing_keeps_handoff_review_required_not_ready() -> None:
    row = _cleared(
        _row(
            row_id="missing_review_seq_7",
            family="history_line_eligible",
            sequence_id="sequence_7",
            sequence_index=7,
            sequence_length=7,
        )
    )
    long_run = build_p7_long_run_gate_handoff([row])
    handoff = build_p7_release_decision_handoff(
        long_run_gate_handoff=long_run,
        p7_runner_result={"runner_result_id": "p7_runner_missing_review", "full_backend_suite_green_confirmed": True},
    )

    assert handoff["release_decision_input_ready"] is False
    assert handoff["release_input_status"] == "review_required"
    assert "blind_qa_review_missing" in handoff["unreviewed_refs"]
    assert "blind_qa_review_missing" in handoff["release_blockers"]
    assert handoff["unresolved_timeout_refs"] == []
    assert "P7_Red_Ledger" not in handoff["required_followup_targets"]
    assert "P7_RatingsOnly_Blind_QA" in handoff["required_followup_targets"]
    assert handoff["release_allowed"] is False


def test_p7_8_material_is_body_free_and_does_not_serialize_source_bodies() -> None:
    long_run = _ready_long_run_handoff()
    handoff = build_p7_release_decision_handoff(
        long_run_gate_handoff=long_run,
        p7_runner_result={"runner_result_id": "p7_runner_body_free", "full_backend_suite_green_confirmed": True},
    )
    dumped = json.dumps(handoff, ensure_ascii=False, sort_keys=True)

    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_BODY not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_8_contract_rejects_release_promotion_and_body_payload() -> None:
    handoff = build_p7_release_decision_handoff()

    unsafe_release = dict(handoff)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(unsafe_release)

    unsafe_ready = dict(handoff)
    unsafe_ready["product_pass_is_release_ready"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(unsafe_ready)

    unsafe_boundary = dict(handoff)
    unsafe_boundary["release_boundary"] = dict(handoff["release_boundary"])
    unsafe_boundary["release_boundary"]["p7_makes_release_decision"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(unsafe_boundary)

    unsafe_body = dict(handoff)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(unsafe_body)

    with pytest.raises(ValueError):
        build_p7_release_decision_handoff(p7_runner_result={"raw_input": SECRET_INPUT})
