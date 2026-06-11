# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_product_quality_review import (
    QA_BUCKET_READY,
    QA_BUCKET_UNSAFE,
    QA_BUCKET_WEAK,
    STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP,
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_STRUCTURE_INSIGHT_READY,
    VERDICT_YELLOW,
    assert_structure_insight_p6_product_quality_review_contract,
    build_structure_insight_p6_product_quality_review,
    dump_structure_insight_p6_product_quality_review_public_summary,
    normalize_structure_insight_p6_product_quality_review_row,
)


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
    "candidate_comment_text",
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
    "observation_text",
    "reception_text",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_free_text",
    "blind_qa_free_text",
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


def _ready_row(case_id: str = "ready-structure-question") -> dict[str, Any]:
    return {
        "case_id": case_id,
        "family": "structure_question",
        "relation_family": "desire_blockage_conflict",
        "surface_role": "observation_insight_seed",
        "verdict": VERDICT_STRUCTURE_INSIGHT_READY,
        "ratings": {
            "read_feeling": 0.94,
            "safety": 1.0,
            "insight_delta": 0.91,
            "non_template": 0.93,
        },
        "safe_reason_codes": [],
    }


def test_p6_8_builds_ratings_only_summary_with_body_free_ready_count() -> None:
    report = build_structure_insight_p6_product_quality_review(
        review_rows=[_ready_row()],
        run_id="p6_product_qa_ready_summary",
    )
    summary = report["summary"]

    assert report["schema_version"] == STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION
    assert report["step"] == STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP
    assert report["ratings_only"] is True
    assert summary["review_count"] == 1
    assert summary["structure_insight_ready_candidate_count"] == 1
    assert summary["ready_candidate_count"] == 1
    assert summary["p7_long_run_field_candidate_count"] == 1
    assert summary["p7_long_run_field_candidates"][0]["case_id"] == "ready-structure-question"
    assert summary["release_allowed"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(report) is False
    assert_structure_insight_p6_product_quality_review_contract(report)


def test_p6_8_separates_unsafe_weak_and_ready_rows() -> None:
    report = build_structure_insight_p6_product_quality_review(
        review_rows=[
            _ready_row("ready-row"),
            {
                "case_id": "unsafe-row",
                "family": "self_understanding_follow",
                "relation_family": "self_denial_identity_split",
                "surface_role": "family_review",
                "verdict": VERDICT_RED,
                "ratings": {"safety": 0.0, "read_feeling": 0.4},
                "safe_reason_codes": ["self_denial_identity_fact_blocked"],
            },
            {
                "case_id": "weak-row",
                "family": "long_meaning_arc",
                "relation_family": "long_arc_multiple_core",
                "surface_role": "family_review",
                "verdict": VERDICT_YELLOW,
                "ratings": {"read_feeling": 0.82, "insight_delta": 0.8},
                "safe_reason_codes": ["long_meaning_arc_relation_flow_missing"],
            },
        ]
    )

    assert report["bucket_counts"][QA_BUCKET_READY] == 1
    assert report["bucket_counts"][QA_BUCKET_UNSAFE] == 1
    assert report["bucket_counts"][QA_BUCKET_WEAK] == 1
    assert report["verdict_counts"][VERDICT_STRUCTURE_INSIGHT_READY] == 1
    assert report["verdict_counts"][VERDICT_RED] == 1
    assert report["verdict_counts"][VERDICT_YELLOW] == 1
    assert "self_denial_identity_fact_blocked" in report["blocker_reason_codes"]


def test_p6_8_normalized_row_stays_ratings_only_and_has_no_release_flag() -> None:
    row = normalize_structure_insight_p6_product_quality_review_row(_ready_row())

    assert row["ratings_only"] is True
    assert row["qa_bucket"] == QA_BUCKET_READY
    assert row["p7_long_run_field_candidate"] is True
    assert row["release_allowed"] is False
    assert row["public_contract"]["public_response_key_added"] is False
    assert row["body_free"]["surface_body_included"] is False
    assert _contains_forbidden_raw_key(row) is False


def test_p6_8_detects_body_reviewer_free_text_public_contract_and_release_meta_without_returning_body() -> None:
    report = build_structure_insight_p6_product_quality_review(
        review_rows=[
            {
                **_ready_row("leaky-row"),
                "comment_text": "must not be retained",
                "reviewer_free_text": "must not be retained",
                "public_response_key_added": True,
                "release_allowed": True,
            }
        ]
    )
    row = report["rows"][0]

    assert row["qa_bucket"] == QA_BUCKET_UNSAFE
    assert "comment_text_body_detected" in row["safe_reason_codes"]
    assert "reviewer_free_text_detected" in row["safe_reason_codes"]
    assert "public_contract_mutation_detected" in row["safe_reason_codes"]
    assert "release_flag_detected" in row["safe_reason_codes"]
    assert report["summary"]["release_allowed"] is False
    assert "must not be retained" not in json.dumps(report, ensure_ascii=False)


def test_p6_8_can_build_material_from_quality_and_family_review_sources() -> None:
    quality = {
        "summary": {
            "verdict": VERDICT_STRUCTURE_INSIGHT_READY,
            "family": "structure_question",
            "relation_family": "desire_blockage_conflict",
            "dimension_averages": {"read_feeling": 0.93, "safety": 1.0},
            "decision_reason_codes": [],
        }
    }
    family_review = {
        "summary": {
            "family": "long_meaning_arc",
            "relation_family": "long_arc_multiple_core",
            "family_review_classification": "allow",
            "decision_reason_codes": [],
        }
    }
    report = build_structure_insight_p6_product_quality_review(
        p6_quality_rubric=quality,
        p6_family_review=family_review,
    )

    assert report["review_count"] == 2
    assert report["structure_insight_ready_candidate_count"] == 1
    assert report["p7_long_run_field_candidate_count"] == 1


def test_p6_8_missing_rows_are_weak_not_release_ready() -> None:
    report = build_structure_insight_p6_product_quality_review()

    assert report["review_count"] == 0
    assert report["structure_insight_ready_candidate_count"] == 0
    assert "ratings_only_review_rows_missing" in report["blocker_reason_codes"]
    assert report["release_allowed"] is False


def test_p6_8_public_summary_stays_body_free() -> None:
    report = build_structure_insight_p6_product_quality_review(review_rows=[_ready_row()])
    dumped = dump_structure_insight_p6_product_quality_review_public_summary(report)
    loaded = json.loads(dumped)

    assert loaded["ratings_only"] is True
    assert loaded["structure_insight_ready_candidate_count"] == 1
    assert loaded["release_allowed"] is False
    assert _contains_forbidden_raw_key(loaded) is False


def test_p6_8_contract_rejects_body_or_release_flags() -> None:
    report = build_structure_insight_p6_product_quality_review(review_rows=[_ready_row()])
    leaked = dict(report)
    leaked["surface_text"] = "leak"
    with pytest.raises(ValueError):
        assert_structure_insight_p6_product_quality_review_contract(leaked)

    released = dict(report)
    released["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_structure_insight_p6_product_quality_review_contract(released)
