# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

import pytest

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_candidate import build_user_label_connection_candidate_meta
from emlis_ai_user_label_connection_gate import build_user_label_connection_gate_meta
from emlis_ai_user_label_connection_material import build_user_label_connection_material
from emlis_ai_user_label_connection_product_quality_qa import (
    BLOCKER_ACCUMULATION_MOTIVATION_NOT_CONFIRMED,
    BLOCKER_BLIND_QA_REVIEW_REQUIRED,
    BLOCKER_HISTORY_CONNECTION_CREEPY_RISK,
    BLOCKER_NO_REVIEWABLE_CANDIDATES,
    BLOCKER_OVERCLAIM_OR_DECIDING_RISK,
    BLOCKER_READ_FEELING_BELOW_TARGET,
    BLOCKER_SELF_BLAME_AMPLIFICATION_RISK,
    BLOCKER_SHALLOW_REPEAT_RISK,
    DIMENSION_CREEPY_ABSENCE,
    DIMENSION_HISTORY_CONNECTION_NATURALNESS,
    DIMENSION_NON_SHALLOW_REPEAT,
    DIMENSION_OVERCLAIM_ABSENCE,
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    DIMENSION_SELF_INFORMATION_ORGANIZED,
    DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_CANDIDATE_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REVIEW_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION,
    assert_user_label_connection_product_quality_qa_meta_only,
    build_user_label_connection_product_quality_qa_candidates,
    build_user_label_connection_product_quality_qa_summary,
    normalize_user_label_connection_product_quality_blind_qa_review,
)
from emlis_ai_user_label_connection_surface import (
    CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
    build_user_label_connection_limited_visible_surface_connection,
    build_user_label_connection_surface_plan,
)

SECRET_CURRENT_MEMO = "PHASE9_SECRET_CURRENT_MEMO_SHOULD_NOT_LEAK"
SECRET_HISTORY_MEMO = "PHASE9_SECRET_HISTORY_MEMO_SHOULD_NOT_LEAK"
SECRET_COMMENT_TEXT = "PHASE9_SECRET_COMMENT_TEXT_SHOULD_NOT_LEAK"
SECRET_SURFACE_TEXT = "PHASE9_SECRET_SURFACE_TEXT_SHOULD_NOT_LEAK"

FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "current_input",
    "currentInput",
    "history_input",
    "historyInput",
    "memo",
    "memo_action",
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
    "body",
    "text",
}


def _current_input() -> dict[str, object]:
    return {
        "id": "phase9-current-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "会議のあとに言葉が出なかった",
        "memo": "続けたい気持ちと動けなさが同時にある",
    }


def _history_rows() -> tuple[dict[str, object], dict[str, object]]:
    return (
        {
            "id": "phase9-history-001",
            "created_at": "2026-05-29T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": "職場で説明を求められた",
            "memo": "動きたいのに詰まっている感じがある",
        },
        {
            "id": "phase9-history-002",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "焦り", "strength": "medium"}],
            "memo_action": "連絡を返せなかった",
            "memo": "止まっていることが重く残っている",
        },
    )


def _source_bundle_with_history() -> SourceBundle:
    last, similar = _history_rows()
    return SourceBundle(
        user_id="phase9-user",
        display_name="Mash",
        current_input=_current_input(),
        last_input=last,
        same_day_recent_inputs=[],
        similar_inputs=[similar],
    )


def _surface_plan() -> dict[str, Any]:
    material = build_user_label_connection_material(
        _current_input(),
        source_bundle=_source_bundle_with_history(),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )
    candidate = build_user_label_connection_candidate_meta(material)
    gate = build_user_label_connection_gate_meta(
        candidate,
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        proposed_surface="この期間の記録では、今回と近い記録の範囲で、同じ線の上に出ているように見えます。",
    )
    return build_user_label_connection_surface_plan(
        gate,
        candidate=candidate,
        connectable_family=CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    )


def _gate_reports_passed() -> dict[str, dict[str, bool]]:
    return {
        "tone_guard": {"passed": True},
        "grounding": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
    }


def _phase8_visible_meta() -> dict[str, Any]:
    visible = build_user_label_connection_limited_visible_surface_connection(
        "今の入力は、かなり重さのある状態として受け取ります。",
        _surface_plan(),
        existing_gate_reports=_gate_reports_passed(),
    )
    assert visible.applied is True
    return visible.as_meta()


def _event(row_id: str = "phase9-row-001") -> dict[str, Any]:
    return {
        "row_id": row_id,
        "coverage_group": "self_understanding_follow",
        "user_label_connection_visible_surface": _phase8_visible_meta(),
        "comment_text": SECRET_COMMENT_TEXT,
        "surface_text": SECRET_SURFACE_TEXT,
        "raw_input": SECRET_CURRENT_MEMO,
    }


def _ratings(value: object = "green") -> dict[str, object]:
    return {dimension: value for dimension in USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS}


def _review(candidate_id: str = "phase9-row-001", **rating_overrides: object) -> dict[str, object]:
    ratings = _ratings("green")
    ratings.update(rating_overrides)
    return {
        "review_id": f"review-{candidate_id}",
        "candidate_id": candidate_id,
        "ratings": ratings,
        "raw_input": SECRET_CURRENT_MEMO,
        "comment_text": SECRET_COMMENT_TEXT,
        "surface_text": SECRET_SURFACE_TEXT,
        "memo": SECRET_HISTORY_MEMO,
    }


def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_keys(child))
    return keys


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_secret_or_raw_payload(value: Any) -> None:
    dumped = _dump(value)
    assert FORBIDDEN_RAW_KEYS.isdisjoint(_all_keys(value))
    for secret in (SECRET_CURRENT_MEMO, SECRET_HISTORY_MEMO, SECRET_COMMENT_TEXT, SECRET_SURFACE_TEXT):
        assert secret not in dumped


def test_phase9_builds_blind_qa_candidates_from_phase8_meta_only() -> None:
    candidates = build_user_label_connection_product_quality_qa_candidates([_event()])

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["schema_version"] == USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_CANDIDATE_SCHEMA_VERSION
    assert candidate["phase"] == USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE
    assert candidate["source_phase"] == USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE
    assert candidate["candidate_id"] == "phase9-row-001"
    assert candidate["reviewable_for_blind_qa"] is True
    assert candidate["limited_visible_surface_connection_applied"] is True
    assert candidate["history_connection_applied"] is True
    assert candidate["existing_surface_gates_passed"] is True
    assert candidate["evidence_record_count"] >= 2
    assert candidate["ratings_required"] == list(USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REQUIRED_DIMENSIONS)
    assert candidate["pytest_green_only_is_not_product_result"] is True
    assert candidate["blind_qa_required"] is True
    assert candidate["machine_metrics_used_for_read_feeling"] is False
    assert candidate["comment_text_body_included"] is False
    assert candidate["public_response_key_added"] is False
    assert candidate["candidate_blockers"] == []
    assert "product_quality_qa_text_payload_detected" in candidate["candidate_warnings"]
    _assert_no_secret_or_raw_payload(candidate)


def test_phase9_normalizes_ratings_only_blind_qa_review_and_strips_text_payload() -> None:
    review = normalize_user_label_connection_product_quality_blind_qa_review(_review())

    assert review["schema_version"] == USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_REVIEW_SCHEMA_VERSION
    assert review["candidate_id"] == "phase9-row-001"
    assert review["ratings_only_payload"] is True
    assert review["read_feeling_score"] == 1.0
    assert review["self_information_organized_score"] == 1.0
    assert review["history_connection_naturalness_score"] == 1.0
    assert review["creepy_absence_score"] == 1.0
    assert review["overclaim_absence_score"] == 1.0
    assert review["self_blame_non_amplification_score"] == 1.0
    assert review["wants_more_input_or_accumulation_score"] == 1.0
    assert review["non_shallow_repeat_score"] == 1.0
    assert review["passed"] is True
    assert review["machine_metrics_used_for_read_feeling"] is False
    assert review["comment_text_body_included"] is False
    _assert_no_secret_or_raw_payload(review)


def test_phase9_summary_passes_only_when_product_value_blind_qa_passes() -> None:
    summary = build_user_label_connection_product_quality_qa_summary(
        events=[_event()],
        blind_qa_reviews=[_review()],
        run_id="phase9-run-pass",
    )

    assert summary["schema_version"] == USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION
    assert summary["phase"] == USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE
    assert summary["candidate_count"] == 1
    assert summary["reviewable_candidate_count"] == 1
    assert summary["reviewed_candidate_count"] == 1
    assert summary["blind_qa_review_coverage_rate"] == 1.0
    assert summary["phase9_product_quality_qa_passed"] is True
    assert summary["product_quality_qa_ready"] is True
    assert summary["product_value_connected_by_qa"] is True
    assert summary["pytest_green_only_is_not_product_result"] is True
    assert summary["release_blockers"] == []
    assert summary["read_feeling_score"] == 1.0
    assert summary["self_information_organized_score"] == 1.0
    assert summary["history_connection_naturalness_score"] == 1.0
    assert summary["creepy_absence_score"] == 1.0
    assert summary["wants_more_input_or_accumulation_score"] == 1.0
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False
    assert summary["public_response_key_added"] is False
    _assert_no_secret_or_raw_payload(summary)


@pytest.mark.parametrize(
    ("dimension", "expected_blocker"),
    [
        (DIMENSION_READ_FEELING, BLOCKER_READ_FEELING_BELOW_TARGET),
        (DIMENSION_CREEPY_ABSENCE, BLOCKER_HISTORY_CONNECTION_CREEPY_RISK),
        (DIMENSION_OVERCLAIM_ABSENCE, BLOCKER_OVERCLAIM_OR_DECIDING_RISK),
        (DIMENSION_SELF_BLAME_NON_AMPLIFICATION, BLOCKER_SELF_BLAME_AMPLIFICATION_RISK),
        (DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION, BLOCKER_ACCUMULATION_MOTIVATION_NOT_CONFIRMED),
        (DIMENSION_NON_SHALLOW_REPEAT, BLOCKER_SHALLOW_REPEAT_RISK),
        (DIMENSION_HISTORY_CONNECTION_NATURALNESS, "history_connection_naturalness_below_target"),
        (DIMENSION_SELF_INFORMATION_ORGANIZED, "self_information_organization_below_target"),
    ],
)
def test_phase9_summary_blocks_creepy_overclaim_self_blame_and_shallow_repeat_risks(
    dimension: str,
    expected_blocker: str,
) -> None:
    summary = build_user_label_connection_product_quality_qa_summary(
        events=[_event()],
        blind_qa_reviews=[_review(**{dimension: "yellow"})],
    )

    assert summary["phase9_product_quality_qa_passed"] is False
    assert expected_blocker in summary["release_blockers"]
    assert summary["product_value_connected_by_qa"] is False
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False


def test_phase9_does_not_treat_pytest_green_or_visible_connection_as_product_success_without_blind_qa() -> None:
    summary = build_user_label_connection_product_quality_qa_summary(
        events=[_event()],
        blind_qa_reviews=[],
    )

    assert summary["reviewable_candidate_count"] == 1
    assert summary["blind_qa_review_count"] == 0
    assert summary["pytest_green_only_is_not_product_result"] is True
    assert summary["blind_qa_required"] is True
    assert summary["phase9_product_quality_qa_passed"] is False
    assert BLOCKER_BLIND_QA_REVIEW_REQUIRED in summary["release_blockers"]
    assert summary["product_value_connected_by_qa"] is False
    assert summary["product_gate_ready"] is False
    assert summary["public_release_applied"] is False


def test_phase9_blocks_when_no_reviewable_limited_visible_connection_exists() -> None:
    summary = build_user_label_connection_product_quality_qa_summary(
        events=[{"row_id": "non-reviewable", "coverage_group": "daily_positive"}],
        blind_qa_reviews=[_review("non-reviewable")],
    )

    assert summary["reviewable_candidate_count"] == 0
    assert summary["phase9_product_quality_qa_passed"] is False
    assert BLOCKER_NO_REVIEWABLE_CANDIDATES in summary["release_blockers"]
    assert summary["product_value_connected_by_qa"] is False
    assert summary["product_gate_ready"] is False


def test_phase9_meta_only_assert_rejects_text_keys_and_release_flags() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_product_quality_qa_meta_only({"comment_text": SECRET_COMMENT_TEXT})
    with pytest.raises(ValueError):
        assert_user_label_connection_product_quality_qa_meta_only({"product_gate_ready": True})
    with pytest.raises(ValueError):
        assert_user_label_connection_product_quality_qa_meta_only({"public_response_key_added": True})
