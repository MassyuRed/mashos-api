# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_contracts import P7_INITIAL_HOLD_IDS, P7_INITIAL_RED_IDS
from emlis_ai_p7_event_bridge import (
    P7_SCORECARD_ROW_SCHEMA_VERSION,
    assert_p7_scorecard_row_contract,
    build_p7_scorecard_row,
)
from emlis_ai_p7_handoff_normalizer import build_p7_handoff_summary
from emlis_ai_product_quality_measurement_event import (
    PRODUCT_QUALITY_EVENT_SCHEMA_VERSION,
    normalize_product_quality_event,
)

SECRET_INPUT = "P7-4 secret raw input must never be serialized"
SECRET_COMMENT = "P7-4 secret comment_text body must never be serialized"


def _valid_surface_summary() -> dict[str, object]:
    return {
        "product_surface_valid": True,
        "public_reached": True,
        "rn_visible": True,
        "public_feedback_inclusion_contract_passed": True,
        "surface_requirement_family": "labelled_two_stage",
        "surface_requirement_satisfied": True,
        "blocker_code": "product_surface_valid",
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _event(*, family: str = "structure_question", row_id: str = "p7_row") -> dict[str, object]:
    return normalize_product_quality_event(
        run_id="p7_run",
        row_id=row_id,
        source_type="manual_internal_case",
        source_case_id=f"case_{row_id}",
        family=family,
        comment_text=SECRET_COMMENT,
        public_meta={"observation_status": "passed"},
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 1,
            "reason_covered_count": 1,
            "product_surface_validation": _valid_surface_summary(),
        },
    )


def _handoff() -> dict[str, object]:
    return build_p7_handoff_summary(
        p5_runtime_bridge_summary={
            "runtime_evaluated": True,
            "visible_applied": True,
            "product_quality_confirmed": True,
            "human_qa_completed": False,
            "release_allowed": False,
            "body_free": {
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
                "surface_body_included": False,
            },
        },
        p6_runtime_bridge_summary={
            "runtime_evaluated": True,
            "visible_applied": True,
            "visible_family": "structure_question",
            "product_quality_review_ratings_only": True,
            "release_allowed": False,
            "body_free": {
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
                "surface_body_included": False,
            },
        },
    )


def test_p7_4_event_bridge_keeps_product_quality_event_source_and_builds_body_free_scorecard_row() -> None:
    event = _event()
    row = build_p7_scorecard_row(product_quality_event=event, p7_handoff_summary=_handoff())
    assert_p7_scorecard_row_contract(row)

    assert event["schema_version"] == PRODUCT_QUALITY_EVENT_SCHEMA_VERSION
    assert row["schema_version"] == P7_SCORECARD_ROW_SCHEMA_VERSION
    assert row["source_event_schema_version"] == PRODUCT_QUALITY_EVENT_SCHEMA_VERSION
    assert row["release_allowed"] is False
    assert row["body_free"] is True
    assert all(value is False for value in row["public_contract"].values())
    assert all(value is False for value in row["body_free_markers"].values())

    assert row["display_contract"] == {
        "observation_status": "passed",
        "public_reached": True,
        "rn_visible": True,
        "product_surface_valid": True,
        "comment_text_present": True,
        "comment_text_length": len(SECRET_COMMENT),
    }
    assert set(P7_INITIAL_RED_IDS).issubset(set(row["red_refs"]))
    assert set(P7_INITIAL_HOLD_IDS).issubset(set(row["hold_refs"]))
    assert set(P7_INITIAL_RED_IDS).issubset(set(row["blocker_ids"]))

    dumped = json.dumps(row, ensure_ascii=False, sort_keys=True)
    assert SECRET_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_4_event_bridge_carries_p5_p6_flags_without_expanding_p6_visible_family() -> None:
    structure_row = build_p7_scorecard_row(product_quality_event=_event(family="structure_question"), p7_handoff_summary=_handoff())
    assert structure_row["p5"]["visible_applied"] is True
    assert structure_row["p5"]["status"] == "applied_hold"
    assert structure_row["p6"]["eligible"] is True
    assert structure_row["p6"]["visible_applied"] is True
    assert structure_row["p6"]["visible_family"] == "structure_question"

    daily_row = build_p7_scorecard_row(product_quality_event=_event(family="daily_positive"), p7_handoff_summary=_handoff())
    assert daily_row["family"] == "daily_positive"
    assert daily_row["p6"]["eligible"] is False
    assert daily_row["p6"]["visible_applied"] is False
    assert daily_row["p6"]["visible_family"] == "none"
    assert daily_row["p6"]["status"] == "meta_only"


def test_p7_4_event_bridge_keeps_ratings_required_instead_of_machine_filling_read_feeling() -> None:
    row = build_p7_scorecard_row(product_quality_event=_event(), p7_handoff_summary=_handoff())
    ratings = row["ratings"]

    assert ratings["blind_qa_required"] is True
    assert ratings["blind_qa_completed"] is False
    assert ratings["rating_required"] is True
    assert ratings["dimension_scores"] == {}
    assert "read_feeling" in ratings["missing_dimensions"]
    assert "history_connection_naturalness" in ratings["missing_dimensions"]
    assert "creepy_absence" in ratings["missing_dimensions"]


def test_p7_4_event_bridge_sequence_rows_can_mark_history_line_eligible_without_release() -> None:
    row = build_p7_scorecard_row(
        product_quality_event=_event(family="history_line_eligible"),
        p7_handoff_summary=_handoff(),
        sequence={"sequence_id": "sequence_3", "sequence_index": 2, "sequence_length": 3, "history_line_eligible": True},
    )

    assert row["sequence"]["sequence_id"] == "sequence_3"
    assert row["sequence"]["sequence_length"] == 3
    assert row["sequence"]["history_line_eligible"] is True
    assert row["sequence"]["row_kind"] == "sequence"
    assert row["release_allowed"] is False


def test_p7_4_event_bridge_contract_rejects_body_payload_public_contract_and_release_promotion() -> None:
    event = dict(_event())
    event["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        build_p7_scorecard_row(product_quality_event=event, p7_handoff_summary=_handoff())

    row = build_p7_scorecard_row(product_quality_event=_event(), p7_handoff_summary=_handoff())
    unsafe_release = dict(row)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_scorecard_row_contract(unsafe_release)

    unsafe_contract = dict(row)
    unsafe_contract["public_contract"] = dict(row["public_contract"])
    unsafe_contract["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_scorecard_row_contract(unsafe_contract)
