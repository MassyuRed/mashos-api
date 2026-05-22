from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
)
from emlis_ai_observation_scorecard_blind_qa import (
    OBSERVATION_BLIND_QA_RUBRIC_VERSION,
    OBSERVATION_SCORECARD_BLIND_QA_VERSION,
    assert_observation_scorecard_blind_qa_contract,
    build_observation_blind_qa_rubric,
    build_observation_scorecard_blind_qa,
    dump_observation_scorecard_blind_qa,
    normalize_observation_blind_qa_review,
    normalize_observation_scorecard_event,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in ("raw_input", "raw_text", "input_text", "user_input", "comment_text", "reply_text", "body"):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        assert payload.get("machine_metrics_used_for_read_feeling") is not True
        assert payload.get("read_feeling_auto_filled_from_machine_metrics") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _event(
    event_id: str,
    *,
    kind: str,
    expected: str | None = None,
    status: str = "passed",
    plan: str = "free",
    skeleton: str = "skel-a",
    reasons: list[str] | None = None,
    user_fact_mode: str = USER_FACT_GROUNDING_MODE_DISABLED,
    facts_used: list[dict[str, str]] | None = None,
    max_depth: int = 1,
) -> dict[str, Any]:
    expected_kind = expected or kind
    eligibility_status = (
        OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
        else OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    )
    expected_eligibility = (
        OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        if expected_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
        else OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    )
    return {
        "row_id": event_id,
        "coverage_group": "short_daily",
        "observation_status": status,
        "comment_text_present": status == "passed",
        "passed_display_count": 1 if status == "passed" else 0,
        "display_confirmed": status == "passed",
        "observation_reply_meta": {
            "observation_reply_kind": kind,
            "eligibility_status": eligibility_status,
            "eligible_for_full_observation": kind == OBSERVATION_REPLY_KIND_ELIGIBLE,
            "question_required": kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "unknown_slots": ["event"] if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION else [],
            "user_fact_grounding_mode": user_fact_mode,
            "facts_used": facts_used or [],
        },
        "expected_observation_reply_kind": expected_kind,
        "expected_eligibility_status": expected_eligibility,
        "plan": plan,
        "user_fact_grounding_mode": user_fact_mode,
        "facts_used": facts_used or [],
        "max_inference_depth_used": max_depth,
        "surface_signature_family_key": skeleton,
        "top_rejection_reasons": reasons or [],
        "machine_metrics_used_for_read_feeling": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def _green_review(kind: str = OBSERVATION_REPLY_KIND_LOW_INFORMATION) -> dict[str, Any]:
    return {
        "review_id": "blind-qa-1",
        "coverage_group": "short_daily",
        "observation_reply_kind": kind,
        "ratings": {
            "read_feeling": "green",
            "input_arrangement": "green",
            "state_verbalization": "green",
            "low_info_question_quality": "green",
            "user_fact_boundary": "green",
            "non_template": "green",
            "overclaim_absence": "green",
        },
    }


def test_step12_blind_qa_rubric_is_observation_specific_and_meta_only() -> None:
    rubric = build_observation_blind_qa_rubric()

    assert rubric["version"] == OBSERVATION_BLIND_QA_RUBRIC_VERSION
    assert rubric["target_step"] == "Step12_Scorecard_Blind_QA"
    assert set(rubric["required_dimensions"]) == {
        "read_feeling",
        "input_arrangement",
        "state_verbalization",
        "low_info_question_quality",
        "user_fact_boundary",
        "non_template",
        "overclaim_absence",
    }
    assert rubric["machine_metrics_separated"] is True
    assert rubric["read_feeling_requires_blind_qa"] is True
    assert rubric["exact_comment_text_locked"] is False
    _assert_meta_only(rubric)


def test_step12_normalizes_blind_qa_review_without_raw_or_comment_text() -> None:
    review = normalize_observation_blind_qa_review(
        {
            **_green_review(),
            "raw_input": "should not leak",
            "comment_text": "should not leak",
            "ratings": {
                "input_specific_structure_reflected": "green",
                "arrangement": "green",
                "relation_verbalization": "green",
                "low_information_question": "green",
                "free_user_fact_boundary": "green",
                "natural_but_not_template": "green",
                "overclaim_absence": "green",
            },
        }
    )

    assert review["version"] == "emlis.observation_blind_qa_review.v1"
    assert review["read_feeling_score"] == 1.0
    assert review["passed"] is True
    assert review["machine_metrics_used_for_read_feeling"] is False
    _assert_meta_only(review)


def test_step12_scorecard_computes_observation_reply_metrics() -> None:
    scorecard = build_observation_scorecard_blind_qa(
        events=[
            _event("e1", kind=OBSERVATION_REPLY_KIND_ELIGIBLE, skeleton="skel-a", max_depth=3),
            _event("e2", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION, skeleton="skel-b"),
            _event("e3", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION, skeleton="skel-c"),
        ],
        blind_qa_reviews=[_green_review()],
    )

    assert scorecard["version"] == OBSERVATION_SCORECARD_BLIND_QA_VERSION
    assert scorecard["observation_scorecard_ready"] is True
    assert scorecard["always_display_rate"] == 1.0
    assert scorecard["eligible_observation_rate"] == 1.0
    assert scorecard["low_info_observation_rate"] == 1.0
    assert scorecard["false_eligible_rate"] == 0.0
    assert scorecard["free_user_fact_violation_count"] == 0
    assert scorecard["overclaim_count"] == 0
    assert scorecard["template_skeleton_repeat_rate"] == 0.0
    assert scorecard["read_feeling_score"] == 1.0
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert "observation_blind_qa_missing" not in scorecard["release_blockers"]
    _assert_meta_only(scorecard)


def test_step12_scorecard_detects_false_eligible_free_user_fact_overclaim_and_skeleton_repeat() -> None:
    scorecard = build_observation_scorecard_blind_qa(
        events=[
            _event(
                "bad-low-info-promoted",
                kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
                expected=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
                plan="free",
                user_fact_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
                facts_used=[{"fact_id": "fact-1"}],
                reasons=["overclaim", "personality_tendency"],
                skeleton="repeat-skel",
                max_depth=3,
            ),
            _event(
                "bad-repeat",
                kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
                expected=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
                skeleton="repeat-skel",
            ),
        ],
        blind_qa_reviews=[_green_review()],
    )

    assert scorecard["always_display_rate"] == 1.0
    assert scorecard["false_eligible_rate"] == 0.5
    assert scorecard["free_user_fact_violation_count"] == 1
    assert scorecard["overclaim_count"] == 1
    assert scorecard["template_skeleton_repeat_rate"] == 0.5
    blockers = set(scorecard["release_blockers"])
    assert "false_eligible_detected" in blockers
    assert "free_user_fact_violation_detected" in blockers
    assert "overclaim_detected" in blockers
    assert "template_skeleton_repeat_detected" in blockers
    _assert_meta_only(scorecard)


def test_step12_scorecard_excludes_safety_and_infra_from_always_display_denominator() -> None:
    scorecard = build_observation_scorecard_blind_qa(
        events=[
            _event("normal", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION),
            _event("safety", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION, status="safety_blocked", reasons=["safety_boundary"]),
            _event("timeout", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION, status="unavailable", reasons=["timeout"]),
        ],
        blind_qa_reviews=[_green_review()],
    )

    assert scorecard["event_count"] == 3
    assert scorecard["normal_input_count"] == 1
    assert scorecard["always_display_rate"] == 1.0
    _assert_meta_only(scorecard)


def test_step12_dump_and_meta_only_assert_reject_public_contract_relaxation() -> None:
    event = normalize_observation_scorecard_event(_event("strip", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION))
    dumped = dump_observation_scorecard_blind_qa(event)
    assert '"comment_text"' not in dumped

    stripped_event = normalize_observation_scorecard_event(
        {
            **_event("strip", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION),
            "raw_input": "must be stripped",
            "comment_text": "must be stripped",
        }
    )
    stripped_dump = dump_observation_scorecard_blind_qa(stripped_event)
    assert "must be stripped" not in stripped_dump
    assert '"comment_text"' not in stripped_dump

    with pytest.raises(ValueError):
        assert_observation_scorecard_blind_qa_contract({"display_gate_relaxed": True})


def test_step12_connects_observation_scorecard_to_product_quality_scorecard_without_release_claim() -> None:
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            _event("e1", kind=OBSERVATION_REPLY_KIND_ELIGIBLE, skeleton="skel-a", max_depth=3),
            _event("e2", kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION, skeleton="skel-b"),
        ],
        blind_qa_reviews=[_green_review()],
    )

    assert scorecard["observation_reply_scorecard_blind_qa_version"] == OBSERVATION_SCORECARD_BLIND_QA_VERSION
    assert scorecard["observation_scorecard_ready"] is True
    assert scorecard["observation_always_display_rate"] == 1.0
    assert scorecard["observation_eligible_observation_rate"] == 1.0
    assert scorecard["observation_low_info_observation_rate"] == 1.0
    assert scorecard["observation_free_user_fact_violation_count"] == 0
    assert scorecard["observation_machine_metrics_used_for_read_feeling"] is False
    assert scorecard["product_gate_ready"] is False
    assert scorecard["product_gate_reached"] is False
    assert scorecard["public_release_applied"] is False
    _assert_meta_only(scorecard)

    serialized = json.dumps(scorecard, ensure_ascii=False)
    assert '"comment_text"' not in serialized
