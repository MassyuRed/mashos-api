# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_blind_qa_material import (
    P7_HUMAN_QA_DIMENSIONS,
    P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION,
    P7_HUMAN_QA_REVIEW_SUMMARY_SCHEMA_VERSION,
    assert_p7_human_qa_material_index_contract,
    assert_p7_human_qa_review_summary_contract,
    build_p7_blind_qa_material,
    build_p7_human_qa_material_index,
    build_p7_human_qa_review_summary,
)
from emlis_ai_p7_long_run_gate_handoff import build_p7_long_run_gate_handoff
from emlis_ai_p7_validation_matrix import build_p7_validation_regression_matrix
from test_emlis_ai_p7_event_bridge_20260612 import _event, _handoff
from emlis_ai_p7_event_bridge import build_p7_scorecard_row

SECRET_INPUT = "R8 secret raw input must never enter material"
SECRET_COMMENT = "R8 secret comment_text body must never enter material"
SECRET_REVIEWER_TEXT = "R8 reviewer free text must never enter material"


def _history_row() -> dict[str, object]:
    return build_p7_scorecard_row(
        product_quality_event=_event(family="history_line_eligible", row_id="r8_history"),
        p7_handoff_summary=_handoff(),
        sequence={"sequence_id": "sequence_7", "sequence_index": 7, "sequence_length": 7, "history_line_eligible": True},
    )


def test_r8_human_qa_material_index_keeps_p7_hold001_until_reviews_complete_and_stays_body_free() -> None:
    material = build_p7_blind_qa_material([_history_row()], material_id="r8_blind_qa")
    index = material["human_qa_material_index"]
    assert_p7_human_qa_material_index_contract(index)

    assert index["schema_version"] == P7_HUMAN_QA_MATERIAL_INDEX_SCHEMA_VERSION
    assert index["p5_human_qa_completed"] is False
    assert index["human_qa_review_status"] == "review_required"
    assert "P7-HOLD-001" in index["unresolved_hold_refs"]
    assert index["local_body_review_packet_exists"] is True
    assert index["local_body_review_packet_release_material"] is False
    assert index["scorecard_body_free"] is True
    assert index["release_material_body_free"] is True
    assert index["raw_input_included_in_scorecard"] is False
    assert index["comment_text_body_included_in_scorecard"] is False
    assert index["reviewer_free_text_included_in_scorecard"] is False
    assert set(index["dimensions_required"]) == set(P7_HUMAN_QA_DIMENSIONS)

    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_REVIEWER_TEXT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_r8_human_qa_review_summary_uses_ratings_only_and_maps_non_template_to_non_shallow_repeat() -> None:
    review = {
        "review_id": "r8_review_1",
        "candidate_id": "p7_blind_qa:r8:row:history_line_eligible:sequence_7:1",
        "reviewer_id_hash": "reviewer_hash",
        "dimension_scores": {
            "history_connection_naturalness": 0.93,
            "creepy_absence": 0.98,
            "wants_more_input_or_accumulation": 0.88,
            "overclaim_absence": 0.97,
            "self_blame_non_amplification": 1.0,
            "non_template": 0.91,
        },
        "reason_codes": ["history_line_natural", "no_creepy_overreach"],
    }

    unsafe_review = dict(review)
    unsafe_review["reviewer_free_text"] = SECRET_REVIEWER_TEXT
    with pytest.raises(ValueError):
        build_p7_human_qa_review_summary(unsafe_review)

    summary = build_p7_human_qa_review_summary(review)
    assert_p7_human_qa_review_summary_contract(summary)

    assert summary["schema_version"] == P7_HUMAN_QA_REVIEW_SUMMARY_SCHEMA_VERSION
    assert summary["review_status"] == "review_completed"
    assert summary["dimension_scores"]["non_shallow_repeat"] == 0.91
    assert summary["reviewer_free_text_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    assert summary["release_allowed"] is False
    assert SECRET_REVIEWER_TEXT not in json.dumps(summary, ensure_ascii=False, sort_keys=True)


def test_r8_long_run_and_validation_keep_human_qa_review_required_as_material_boundary() -> None:
    row = _history_row()
    material = build_p7_blind_qa_material([row], material_id="r8_blind_qa")
    index = build_p7_human_qa_material_index(blind_qa_material=material)
    long_run = build_p7_long_run_gate_handoff([row], blind_qa_material=material, human_qa_material_index=index)
    validation = build_p7_validation_regression_matrix(human_qa_material_index=index)

    assert "p5_human_qa_review_required" in long_run["candidate_blocked_or_review_required_reason_codes"]
    assert long_run["blind_qa_summary"]["p5_human_qa_completed"] is False
    assert long_run["blind_qa_summary"]["p5_human_qa_local_body_review_packet_release_material"] is False
    assert validation["summary"]["p5_human_qa_completed"] is False
    assert validation["summary"]["p5_human_qa_material_boundary_body_free"] is True
    assert validation["summary"]["p5_human_qa_hold_preserved"] is True
    assert "P7-HOLD-001" in validation["unresolved_hold_refs"]
    assert any(row["check_kind"] == "p5_human_qa_material_boundary" for row in validation["matrix_rows"])
