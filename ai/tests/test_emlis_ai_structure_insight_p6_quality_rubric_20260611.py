# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
from emlis_ai_structure_insight_p6_quality_rubric import (
    P6_QUALITY_RUBRIC_DIMENSION_TARGETS,
    P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS,
    STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP,
    STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION,
    VERDICT_PASS,
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_STRUCTURE_INSIGHT_READY,
    VERDICT_YELLOW,
    assert_structure_insight_p6_quality_rubric_contract,
    build_structure_insight_p6_quality_rubric,
    dump_structure_insight_p6_quality_rubric_public_summary,
    normalize_structure_insight_p6_quality_rubric_row,
)
from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy


FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "history_context",
    "historyContext",
    "history_records",
    "historyRecords",
    "history_raw_text",
    "historyRawText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "reply_text",
    "replyText",
    "display_text",
    "displayText",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_free_text",
    "raw_test_output",
    "test_output",
    "command_output",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _row(**overrides: Any) -> dict[str, Any]:
    row = {
        "row_id": "p6_quality_ready_row",
        "case_id": "p6_quality_ready_case",
        "family": "structure_question",
        "relation_family": "desire_blockage_conflict",
        "ratings": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
        "red_flags": [],
        "repair_flags": [],
    }
    row.update(overrides)
    return row


def _boundary() -> dict[str, Any]:
    return build_structure_insight_p6_family_boundary(
        family="structure_question",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        run_id="p6_quality_boundary_source",
    )


def _relation_policy() -> dict[str, Any]:
    return build_structure_insight_p6_relation_policy(
        relation_family="desire_blockage_conflict",
        p6_family_boundary=_boundary(),
        run_id="p6_quality_relation_policy_source",
    )


def test_p6_4_builds_ratings_only_structure_insight_ready_report_body_free() -> None:
    report = build_structure_insight_p6_quality_rubric(
        review_rows=[_row()],
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=_boundary(),
        run_id="p6_quality_ready_report",
    )
    summary = report["summary"]

    assert report["schema_version"] == STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION
    assert report["step"] == STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP
    assert summary["schema_version"] == STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION
    assert report["ratings_only"] is True
    assert summary["ratings_only"] is True
    assert summary["verdict"] == VERDICT_STRUCTURE_INSIGHT_READY
    assert summary["verdict_counts"][VERDICT_STRUCTURE_INSIGHT_READY] == 1
    assert summary["structure_insight_ready_candidate_count"] == 1
    assert summary["p7_long_run_candidate_count"] == 1
    assert summary["machine_metrics_do_not_fill_read_feeling"] is True
    assert summary["machine_metrics_do_not_fill_insight_delta"] is True
    assert summary["read_feeling_auto_filled_from_machine_metrics"] is False
    assert summary["insight_delta_auto_filled_from_machine_metrics"] is False
    assert summary["release_allowed"] is False
    assert summary["public_contract"]["public_response_key_added"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(report) is False
    assert_structure_insight_p6_quality_rubric_contract(report)


def test_p6_4_normalizes_single_row_without_public_or_body_leak() -> None:
    normalized = normalize_structure_insight_p6_quality_rubric_row(
        _row(),
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=_boundary(),
    )

    assert normalized["ratings_only"] is True
    assert normalized["verdict"] == VERDICT_STRUCTURE_INSIGHT_READY
    assert normalized["p7_long_run_candidate"] is True
    assert set(normalized["dimension_ratings"]) == set(P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS)
    assert normalized["machine_metrics_used_for_read_feeling"] is False
    assert normalized["read_feeling_auto_filled_from_machine_metrics"] is False
    assert normalized["public_response_key_added"] is False
    assert normalized["body_free"]["candidate_body_included"] is False
    assert _contains_forbidden_raw_key(normalized) is False


def test_p6_4_red_verdict_on_unsafe_claims_or_absence_dimension_failures() -> None:
    red = build_structure_insight_p6_quality_rubric(
        review_rows=[
            _row(
                row_id="p6_quality_red_row",
                ratings={**P6_QUALITY_RUBRIC_DIMENSION_TARGETS, "diagnosis_absence": 0.0},
            )
        ],
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=_boundary(),
    )
    assert red["summary"]["verdict"] == VERDICT_RED
    assert "dimension_below_target:diagnosis_absence" in red["summary"]["decision_reason_codes"]

    flagged = build_structure_insight_p6_quality_rubric(
        review_rows=[_row(row_id="p6_quality_unsafe_flag", red_flags=["target_judgement"])],
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=_boundary(),
    )
    assert flagged["summary"]["verdict"] == VERDICT_RED
    assert "unsafe_claim_or_red_flag" in flagged["summary"]["decision_reason_codes"]


def test_p6_4_repair_required_on_soft_marker_missing_insight_too_shallow_mirror_only_or_family_mismatch() -> None:
    for flag, reason in (
        ("soft_marker_missing", "soft_marker_missing"),
        ("insight_too_shallow", "insight_too_shallow"),
        ("mirror_only", "mirror_only_reduction_below_target"),
        ("family_mismatch", "family_mismatch"),
    ):
        report = build_structure_insight_p6_quality_rubric(
            review_rows=[_row(row_id=f"p6_quality_repair_{flag}", repair_flags=[flag])],
            p6_relation_policy=_relation_policy(),
            p6_family_boundary=_boundary(),
        )
        assert report["summary"]["verdict"] == VERDICT_REPAIR_REQUIRED
        assert reason in report["summary"]["decision_reason_codes"]


def test_p6_4_yellow_when_safe_but_insight_delta_or_naturalness_is_below_product_target() -> None:
    report = build_structure_insight_p6_quality_rubric(
        review_rows=[
            _row(
                row_id="p6_quality_yellow_row",
                ratings={
                    **P6_QUALITY_RUBRIC_DIMENSION_TARGETS,
                    "insight_delta": 0.80,
                    "naturalness": 0.88,
                },
            )
        ],
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=_boundary(),
    )
    summary = report["summary"]

    assert summary["verdict"] == VERDICT_YELLOW
    assert summary["verdict_policy"]["yellow_allowed_without_product_pass"] is True
    assert "dimension_below_target:insight_delta" in summary["decision_reason_codes"]
    assert "dimension_below_target:naturalness" in summary["decision_reason_codes"]


def test_p6_4_pass_when_targets_are_met_but_ready_policy_or_boundary_is_not_attached() -> None:
    report = build_structure_insight_p6_quality_rubric(review_rows=[_row(row_id="p6_quality_pass_row")])
    summary = report["summary"]

    assert summary["verdict"] == VERDICT_PASS
    assert summary["structure_insight_ready_candidate_count"] == 0
    assert "structure_ready_requires_policy_and_boundary" in summary["decision_reason_codes"]


def test_p6_4_relation_policy_or_family_boundary_can_prevent_structure_ready() -> None:
    review_policy = build_structure_insight_p6_relation_policy(relation_family="event_reaction_link")
    report = build_structure_insight_p6_quality_rubric(
        review_rows=[_row(row_id="p6_quality_relation_review")],
        p6_relation_policy=review_policy,
        p6_family_boundary=_boundary(),
    )
    assert report["summary"]["verdict"] == VERDICT_REPAIR_REQUIRED
    assert "relation_policy_review_required" in report["summary"]["decision_reason_codes"]

    no_connect = build_structure_insight_p6_family_boundary(
        family="low_information",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
    )
    report = build_structure_insight_p6_quality_rubric(
        review_rows=[_row(row_id="p6_quality_boundary_block")],
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=no_connect,
    )
    assert report["summary"]["verdict"] == VERDICT_REPAIR_REQUIRED
    assert "family_boundary_not_allowing_surface" in report["summary"]["decision_reason_codes"]


def test_p6_4_missing_rows_or_missing_dimensions_stays_repair_required() -> None:
    empty = build_structure_insight_p6_quality_rubric(review_rows=[])
    assert empty["summary"]["verdict"] == VERDICT_REPAIR_REQUIRED
    assert "ratings_only_review_rows_missing" in empty["summary"]["decision_reason_codes"]

    missing = build_structure_insight_p6_quality_rubric(
        review_rows=[_row(row_id="p6_quality_missing_dimension", ratings={"read_feeling": 1.0})]
    )
    assert missing["summary"]["verdict"] == VERDICT_REPAIR_REQUIRED
    assert "dimension_rating_missing:structure_insight_candidate_quality" in missing["summary"]["decision_reason_codes"]


def test_p6_4_rejects_raw_body_reviewer_free_text_and_machine_metric_autofill() -> None:
    with pytest.raises(ValueError):
        normalize_structure_insight_p6_quality_rubric_row({**_row(), "comment_text": "must not leak"})
    with pytest.raises(ValueError):
        normalize_structure_insight_p6_quality_rubric_row({**_row(), "reviewer_note": "free text is not retained"})
    with pytest.raises(ValueError):
        normalize_structure_insight_p6_quality_rubric_row(
            {**_row(), "machine_metrics_used_for_read_feeling": True}
        )


def test_p6_4_public_summary_is_body_free_and_excludes_review_rows() -> None:
    dumped = dump_structure_insight_p6_quality_rubric_public_summary(
        build_structure_insight_p6_quality_rubric(
            review_rows=[_row()],
            p6_relation_policy=_relation_policy(),
            p6_family_boundary=_boundary(),
        )
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION
    assert parsed["verdict"] == VERDICT_STRUCTURE_INSIGHT_READY
    assert parsed["public_response_key_added"] is False
    assert parsed["response_shape_changed"] is False
    assert parsed["raw_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["reviewer_free_text_included"] is False
    assert parsed["release_allowed"] is False
    assert '"review_rows"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"reviewer_note"' not in dumped
    assert _contains_forbidden_raw_key(parsed) is False
    assert_structure_insight_p6_quality_rubric_contract(parsed, allow_partial=True)


def test_p6_4_contract_rejects_raw_payload_keys_release_and_public_contract_mutation() -> None:
    with pytest.raises(ValueError):
        assert_structure_insight_p6_quality_rubric_contract({"comment_text": "must not leak"}, allow_partial=True)
    with pytest.raises(ValueError):
        assert_structure_insight_p6_quality_rubric_contract({"release_allowed": True}, allow_partial=True)

    clean = build_structure_insight_p6_quality_rubric(
        review_rows=[_row()],
        p6_relation_policy=_relation_policy(),
        p6_family_boundary=_boundary(),
    )
    contract = dict(clean)
    contract["summary"] = {
        **clean["summary"],
        "public_contract": dict(clean["summary"]["public_contract"], response_shape_changed=True),
    }
    with pytest.raises(ValueError):
        assert_structure_insight_p6_quality_rubric_contract(contract)
