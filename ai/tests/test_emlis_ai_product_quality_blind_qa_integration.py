# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

import pytest

from emlis_ai_product_quality_blind_qa_integration import (
    BLOCKER_BLIND_QA_REVIEW_REQUIRED,
    PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE,
    PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION,
    PRODUCT_QUALITY_BLIND_QA_REVIEW_SCHEMA_VERSION,
    RUNTIME_SURFACE_SCOPE,
    USER_LABEL_CONNECTION_SCOPE,
    assert_product_quality_blind_qa_integration_meta_only,
    build_product_quality_blind_qa_integration,
    dump_product_quality_blind_qa_integration,
    normalize_product_quality_blind_qa_review,
)
from emlis_ai_product_quality_measurement_runner import (
    dump_product_quality_measurement_run,
    run_product_quality_measurement,
)
from emlis_ai_types import ReplyEnvelope

SECRET_INPUT = "PHASE6_SECRET_RAW_INPUT_SHOULD_NOT_LEAK"
SECRET_COMMENT = "PHASE6_SECRET_COMMENT_TEXT_SHOULD_NOT_LEAK"
SECRET_SURFACE = "PHASE6_SECRET_SURFACE_TEXT_SHOULD_NOT_LEAK"

FORBIDDEN_BODY_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "input",
    "input_text",
    "inputText",
    "current_input",
    "currentInput",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
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


def _assert_no_secret_or_body_payload(value: Any) -> None:
    dumped = _dump(value)
    assert FORBIDDEN_BODY_KEYS.isdisjoint(_all_keys(value))
    for secret in (SECRET_INPUT, SECRET_COMMENT, SECRET_SURFACE):
        assert secret not in dumped


def _runtime_candidate(candidate_id: str = "runtime-row-001") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "row_id": candidate_id,
        "coverage_group": "short_daily",
        "review_scope": RUNTIME_SURFACE_SCOPE,
        "reviewable_for_blind_qa": True,
        "blind_qa_review_required": True,
        "ratings_required": ["read_feeling", "evidence_retention", "distance", "naturalness", "non_template"],
        "public_passed": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def _user_label_candidate(candidate_id: str = "ulc-row-001") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "row_id": candidate_id,
        "connectable_family": "self_understanding_follow",
        "review_scope": USER_LABEL_CONNECTION_SCOPE,
        "reviewable_for_blind_qa": True,
        "blind_qa_required": True,
        "limited_visible_surface_connection_applied": True,
        "history_connection_applied": True,
        "existing_surface_gates_passed": True,
        "evidence_record_count": 2,
        "ratings_required": [
            "read_feeling",
            "self_information_organized",
            "history_connection_naturalness",
            "creepy_absence",
            "overclaim_absence",
            "self_blame_non_amplification",
            "wants_more_input_or_accumulation",
            "non_shallow_repeat",
        ],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def _runtime_review(candidate_id: str = "runtime-row-001", value: object = "green") -> dict[str, object]:
    return {
        "review_id": f"review-{candidate_id}",
        "candidate_id": candidate_id,
        "review_scope": RUNTIME_SURFACE_SCOPE,
        "ratings": {
            "read_feeling": value,
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def _user_label_review(candidate_id: str = "ulc-row-001", value: object = "green") -> dict[str, object]:
    return {
        "review_id": f"review-{candidate_id}",
        "candidate_id": candidate_id,
        "review_scope": USER_LABEL_CONNECTION_SCOPE,
        "ratings": {
            "read_feeling": value,
            "self_information_organized": "green",
            "history_connection_naturalness": "green",
            "creepy_absence": "green",
            "overclaim_absence": "green",
            "self_blame_non_amplification": "green",
            "wants_more_input_or_accumulation": "green",
            "non_shallow_repeat": "green",
        },
    }


def test_phase6_normalizes_ratings_only_review_and_strips_text_payload() -> None:
    review = _runtime_review()
    review.update({"raw_input": SECRET_INPUT, "comment_text": SECRET_COMMENT, "surface_text": SECRET_SURFACE})

    normalized = normalize_product_quality_blind_qa_review(review, review_scope=RUNTIME_SURFACE_SCOPE)

    assert normalized["schema_version"] == PRODUCT_QUALITY_BLIND_QA_REVIEW_SCHEMA_VERSION
    assert normalized["review_scope"] == RUNTIME_SURFACE_SCOPE
    assert normalized["candidate_id"] == "runtime-row-001"
    assert normalized["ratings_only_payload"] is True
    assert normalized["read_feeling_score"] == 1.0
    assert normalized["machine_metrics_used_for_read_feeling"] is False
    assert normalized["read_feeling_auto_filled_from_machine_metrics"] is False
    assert normalized["source_text_payload_stripped"] is True
    assert normalized["product_gate_ready"] is False
    assert normalized["public_release_applied"] is False
    _assert_no_secret_or_body_payload(normalized)


def test_phase6_blocks_when_review_is_missing_and_does_not_turn_release_flags_on() -> None:
    integration = build_product_quality_blind_qa_integration(
        run_id="pq_phase6_missing_review",
        runtime_surface_candidates=[_runtime_candidate()],
        runtime_surface_reviews=[],
        user_label_connection_candidates=[_user_label_candidate()],
        user_label_connection_reviews=[],
    )

    assert integration["schema_version"] == PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION
    assert integration["phase"] == PRODUCT_QUALITY_BLIND_QA_INTEGRATION_PHASE
    assert integration["blind_qa_required"] is True
    assert integration["blind_qa_integration_ready"] is False
    assert integration["runtime_surface"]["blind_qa_review_coverage_rate"] == 0.0
    assert integration["user_label_connection"]["blind_qa_review_coverage_rate"] == 0.0
    assert BLOCKER_BLIND_QA_REVIEW_REQUIRED in integration["release_blockers"]
    assert integration["product_gate_ready"] is False
    assert integration["public_release_applied"] is False
    assert integration["machine_metrics_used_for_read_feeling"] is False
    assert integration["read_feeling_auto_filled_from_machine_metrics"] is False
    _assert_no_secret_or_body_payload(integration)


def test_phase6_integration_passes_only_when_runtime_and_user_label_reviews_cover_all_candidates() -> None:
    integration = build_product_quality_blind_qa_integration(
        run_id="pq_phase6_green",
        runtime_surface_candidates=[_runtime_candidate()],
        runtime_surface_reviews=[_runtime_review()],
        user_label_connection_candidates=[_user_label_candidate()],
        user_label_connection_reviews=[_user_label_review()],
    )

    assert integration["blind_qa_integration_ready"] is True
    assert integration["runtime_surface"]["ready"] is True
    assert integration["user_label_connection"]["ready"] is True
    assert integration["runtime_surface"]["read_feeling_score"] == 1.0
    assert integration["user_label_connection"]["read_feeling_score"] == 1.0
    assert integration["release_blockers"] == []
    assert integration["blind_qa_review_queue_count"] == 2
    assert all(row["reviewed"] is True for row in integration["blind_qa_review_queue"])
    assert_product_quality_blind_qa_integration_meta_only(integration)
    dumped = dump_product_quality_blind_qa_integration(integration)
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped


def test_phase6_integration_assertion_rejects_body_payload_or_release_flag() -> None:
    with pytest.raises(ValueError):
        assert_product_quality_blind_qa_integration_meta_only({"comment_text": SECRET_COMMENT})
    with pytest.raises(ValueError):
        assert_product_quality_blind_qa_integration_meta_only({"product_gate_ready": True})
    with pytest.raises(ValueError):
        assert_product_quality_blind_qa_integration_meta_only({"machine_metrics_used_for_read_feeling": True})


def test_phase6_measurement_runner_connects_blind_qa_integration_without_serializing_bodies() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text=SECRET_COMMENT,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
                "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
                "state_answer_gate_boundary": {"passed": True},
                "diagnostic_summary": {
                    "binding_required_count": 1,
                    "binding_supported_count": 1,
                    "surface_signature_key": "phase6_runner_signature",
                },
            },
        )

    run = run_product_quality_measurement(
        input_cases=[
            {
                "case_id": "phase6_runner",
                "family": "daily_unpleasant",
                "current_input": {"memo": SECRET_INPUT},
            }
        ],
        renderer=renderer,
        run_id="pq_phase6_runner",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    assert run["blind_qa_integration"]["schema_version"] == PRODUCT_QUALITY_BLIND_QA_INTEGRATION_SCHEMA_VERSION
    assert run["phase6_blind_qa_review_required"] is True
    assert run["blind_qa_integration_ready"] is False
    assert BLOCKER_BLIND_QA_REVIEW_REQUIRED in run["blind_qa_release_blockers"]
    assert run["blind_qa_review_queue_count"] == len(run["blind_qa_review_queue"])
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False
    dumped = dump_product_quality_measurement_run(run)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
