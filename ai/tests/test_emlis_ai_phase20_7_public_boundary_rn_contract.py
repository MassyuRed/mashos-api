# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_response_contract import (
    ResponseKind,
    build_emlis_internal_response_contract,
)


PUBLIC_RESPONSE_KEYS = {"status", "id", "created_at", "input_feedback"}
INPUT_FEEDBACK_KEYS = {"comment_text", "emlis_ai"}
DISPLAYABLE_KINDS = (
    ResponseKind.NORMAL_OBSERVATION,
    ResponseKind.LOW_INFORMATION_OBSERVATION,
    ResponseKind.LIMITED_GROUNDING_OBSERVATION,
)
NON_DISPLAYABLE_KINDS = (
    ResponseKind.SAFETY_SUPPORT_REQUIRED,
    ResponseKind.SAFETY_BLOCKED_EMERGENCY,
    ResponseKind.INFRASTRUCTURE_ERROR,
)
FORBIDDEN_PUBLIC_FRAGMENTS = (
    "internal_response_contract",
    "internal_response_contract_schema_version",
    '"response_kind"',
    '"safety_triage_kind"',
    '"grounding_scope"',
    '"repair_attempts"',
    "self_understanding_learning_shift",
    "relationship_gratitude_recovery",
    "normal_observation",
    "low_information_observation",
    "limited_grounding_observation",
    "self_denial_safe_state_answer",
    "safety_support_required",
    "safety_blocked_emergency",
    "infrastructure_error",
    "phase20_7_secret_raw_input",
    "phase20_7_secret_evidence_text",
    "phase20_7_secret_internal_comment",
    "observation_text_should_not_be_public",
    "reception_text_should_not_be_public",
)


def _internal_meta_for_response_kind(
    response_kind: ResponseKind,
    *,
    legacy_status: str,
    rejection_reasons: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        # Phase20-7 must prefer the internal response_kind contract over this
        # legacy field when the contract exists.
        "observation_status": legacy_status,
        "observation_trace_id": "phase20-7-public-boundary",
        "trace_id": "phase20-7-public-boundary-trace",
        "rejection_reasons": list(rejection_reasons or []),
        "internal_response_contract": build_emlis_internal_response_contract(
            response_kind,
            reason="phase20_7_public_boundary_contract_test",
        ),
        "internal_response_contract_schema_version": "cocolon.emlis.internal_response_contract.v1",
        # These payloads are intentionally unsafe.  The public boundary may keep
        # short, sanitized diagnostic summaries, but it must not expose these
        # internal keys or values and RN must never use them as display sources.
        "response_kind": response_kind.value,
        "safety_triage_kind": "safe_observation",
        "grounding_scope": "current_input_only",
        "internal_mode": "self_understanding_learning_shift",
        "mode": "relationship_gratitude_recovery",
        "current_input": {"memo": "phase20_7_secret_raw_input"},
        "raw_input": "phase20_7_secret_raw_input",
        "raw_text": "phase20_7_secret_evidence_text",
        "comment_text": "phase20_7_secret_internal_comment",
        "candidate_comment_text": "phase20_7_secret_internal_comment",
        "observation_text": "observation_text_should_not_be_public",
        "reception_text": "reception_text_should_not_be_public",
        "evidence_spans": [{"raw_text": "phase20_7_secret_evidence_text"}],
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": "phase20_7_public_boundary",
            "coverage_group": "phase20_7",
            "composer_status": "generated",
            "mode": "relationship_gratitude_recovery",
            "response_kind": response_kind.value,
            "comment_text": "phase20_7_secret_internal_comment",
            "current_input": {"memo": "phase20_7_secret_raw_input"},
            "evidence_spans": [{"raw_text": "phase20_7_secret_evidence_text"}],
        },
    }


def _public_body(*, comment_text: str, public_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {
            "comment_text": str(comment_text or "").strip(),
            "emlis_ai": dict(public_meta or {}),
        }
    return {
        "status": "ok",
        "id": "phase20-7-emotion-log",
        "created_at": "2026-05-31T00:00:00.000000+00:00",
        "input_feedback": feedback,
    }


def _assert_public_response_shape(body: Mapping[str, Any]) -> None:
    assert set(body.keys()) == PUBLIC_RESPONSE_KEYS
    feedback = body.get("input_feedback")
    if feedback is not None:
        assert isinstance(feedback, Mapping)
        assert set(feedback.keys()) == INPUT_FEEDBACK_KEYS
        assert isinstance(feedback.get("comment_text"), str)
        assert isinstance(feedback.get("emlis_ai"), Mapping)


def _assert_no_internal_boundary_leak(value: Mapping[str, Any]) -> None:
    dumped = json.dumps(value, ensure_ascii=False, sort_keys=True)
    for fragment in FORBIDDEN_PUBLIC_FRAGMENTS:
        assert fragment not in dumped


@pytest.mark.parametrize("response_kind", DISPLAYABLE_KINDS, ids=lambda kind: kind.value)
def test_phase20_7_displayable_response_kinds_connect_to_public_passed_comment_text(
    response_kind: ResponseKind,
) -> None:
    internal_meta = _internal_meta_for_response_kind(
        response_kind,
        legacy_status="rejected",
        rejection_reasons=[
            response_kind.value,
            "self_understanding_learning_shift",
            "relationship_gratitude_recovery",
            "phase20_7_public_safe_reason",
        ],
    )
    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    comment_text = "Phase20-7 public comment_text sample for displayable observation."
    body = _public_body(comment_text=comment_text, public_meta=public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta.get("rejection_reasons") == ["phase20_7_public_safe_reason"]
    assert should_include_public_input_feedback(comment_text, public_meta) is True
    assert body["input_feedback"] is not None
    assert body["input_feedback"]["comment_text"] == comment_text
    assert body["input_feedback"]["emlis_ai"]["observation_status"] == "passed"
    _assert_public_response_shape(body)
    _assert_no_internal_boundary_leak(body)


@pytest.mark.parametrize("response_kind", NON_DISPLAYABLE_KINDS, ids=lambda kind: kind.value)
def test_phase20_7_non_displayable_response_kinds_do_not_fake_emlis_observation(
    response_kind: ResponseKind,
) -> None:
    internal_meta = _internal_meta_for_response_kind(
        response_kind,
        legacy_status="passed",
        rejection_reasons=["phase20_7_non_displayable_contract"],
    )
    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _public_body(
        comment_text="This body must not be exposed as Emlis observation.",
        public_meta=public_meta,
    )

    expected_status = "unavailable" if response_kind is ResponseKind.INFRASTRUCTURE_ERROR else "safety_blocked"
    assert public_meta["observation_status"] == expected_status
    assert should_include_public_input_feedback("This body must not be exposed as Emlis observation.", public_meta) is False
    assert body["input_feedback"] is None
    _assert_public_response_shape(body)
    _assert_no_internal_boundary_leak(body)


def test_phase20_7_displayable_contract_still_requires_non_empty_comment_text() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _internal_meta_for_response_kind(ResponseKind.NORMAL_OBSERVATION, legacy_status="passed"),
        comment_text_present=False,
        subscription_tier="free",
    )
    body = _public_body(comment_text="   ", public_meta=public_meta)

    assert public_meta["observation_status"] == "unavailable"
    assert "public_feedback_comment_text_missing" in public_meta.get("rejection_reasons", [])
    assert should_include_public_input_feedback("   ", public_meta) is False
    assert body["input_feedback"] is None
    _assert_public_response_shape(body)


def test_phase20_7_legacy_meta_without_internal_contract_keeps_existing_public_status_boundary() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "free",
            "observation_status": "rejected",
            "rejection_reasons": ["legacy_rejected_without_phase20_contract"],
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["observation_status"] == "rejected"
    assert should_include_public_input_feedback("legacy comment", public_meta) is False
