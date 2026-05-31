# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Final

import pytest

import emotion_submit_service as submit_service
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e import (
    PHASE19_REAL_DEVICE_ABCD_CASES,
    Phase19RealDeviceCase,
    _assert_public_body_has_no_internal_leaks,
    _assert_public_response_shape_unchanged,
    _enable_complete_initial,
    _patch_real_reply_source_bundle,
    _patch_submit_persistence,
)


PHASE19_PUBLIC_FEEDBACK_BOUNDARY_ASSERTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase19.public_feedback_boundary_assertion.v1"
)
_PHASE19_PUBLIC_BOUNDARY_PHASE: Final = "Phase19-5_public_feedback_boundary_e2e"
_ALLOWED_PUBLIC_META_STATUSES: Final = {"passed", "rejected", "unavailable", "safety_blocked"}
_REQUIRED_BOUNDARY_ASSERTION_KEYS: Final = frozenset(
    {
        "schema_version",
        "source_phase",
        "case_id",
        "reply_comment_text_present",
        "public_meta_observation_status",
        "should_include_public_input_feedback",
        "response_has_input_feedback",
        "response_input_feedback_comment_text_present",
        "response_input_feedback_emlis_ai_status",
        "rn_modal_should_open",
    }
)
_FORBIDDEN_PUBLIC_RESPONSE_KEYS: Final = ("observation_text", "reception_text")
_FORBIDDEN_PUBLIC_RESPONSE_FRAGMENTS: Final = (
    '"current_input"',
    '"evidence_spans"',
    '"generated_candidate_text"',
    '"candidate_comment_text"',
    '"raw_input"',
    '"raw_text"',
    '"surface_policy"',
    "relationship_gratitude_recovery",
    "self_understanding_learning_shift",
)
_VISIBLE_COMMENT: Final = "Emlisの観測として表示する本文です。"
_SECRET_RAW_INPUT: Final = "Phase19-5 public responseへ出してはいけない入力本文"
_SECRET_INTERNAL_COMMENT: Final = "Phase19-5 public metaへ混ぜてはいけない内部本文"
_PHASE19_SAFE_INSERTED_IDS: Final = {
    "phase19_real_device_A_low_information_fatigue": "phase19-5-A",
    "phase19_real_device_B_safety_boundary_self_harm_adjacent": "phase19-5-B",
    "phase19_real_device_C_generic_self_understanding_regression": "phase19-5-C",
    "phase19_real_device_D_generic_relationship_boundary_regression": "phase19-5-D",
}


def _public_response_body(
    *,
    inserted_id: str,
    comment_text: str,
    public_meta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {"comment_text": str(comment_text or "").strip(), "emlis_ai": dict(public_meta or {})}
    return {
        "status": "ok",
        "id": inserted_id,
        "created_at": "2026-05-30T00:00:00.000000+00:00",
        "input_feedback": feedback,
    }


def _boundary_assertion(
    *,
    case_id: str,
    reply_comment_text_present: bool,
    comment_text_for_public_boundary: str,
    public_meta: Mapping[str, Any] | None,
    body: Mapping[str, Any],
) -> dict[str, Any]:
    feedback = body.get("input_feedback") if isinstance(body.get("input_feedback"), Mapping) else None
    feedback_meta = feedback.get("emlis_ai") if isinstance(feedback, Mapping) else None
    feedback_status = (
        str(feedback_meta.get("observation_status") or "").strip()
        if isinstance(feedback_meta, Mapping)
        else None
    )
    feedback_comment_present = bool(
        isinstance(feedback, Mapping) and str(feedback.get("comment_text") or "").strip()
    )
    public_status = (
        str(public_meta.get("observation_status") or "").strip()
        if isinstance(public_meta, Mapping)
        else None
    )
    assertion = {
        "schema_version": PHASE19_PUBLIC_FEEDBACK_BOUNDARY_ASSERTION_SCHEMA_VERSION,
        "source_phase": _PHASE19_PUBLIC_BOUNDARY_PHASE,
        "case_id": str(case_id),
        "reply_comment_text_present": bool(reply_comment_text_present),
        "public_meta_observation_status": public_status,
        "should_include_public_input_feedback": should_include_public_input_feedback(
            comment_text_for_public_boundary,
            public_meta,
        ),
        "response_has_input_feedback": feedback is not None,
        "response_input_feedback_comment_text_present": feedback_comment_present,
        "response_input_feedback_emlis_ai_status": feedback_status,
        "rn_modal_should_open": bool(
            feedback_comment_present
            and isinstance(feedback_meta, Mapping)
            and str(feedback_meta.get("observation_status") or "").strip() == "passed"
        ),
    }
    _validate_boundary_assertion(assertion)
    return assertion


def _validate_boundary_assertion(assertion: Mapping[str, Any]) -> None:
    assert set(assertion.keys()) == _REQUIRED_BOUNDARY_ASSERTION_KEYS
    assert assertion["schema_version"] == PHASE19_PUBLIC_FEEDBACK_BOUNDARY_ASSERTION_SCHEMA_VERSION
    assert assertion["source_phase"] == _PHASE19_PUBLIC_BOUNDARY_PHASE
    assert isinstance(assertion["case_id"], str) and assertion["case_id"].strip()
    assert isinstance(assertion["reply_comment_text_present"], bool)
    assert assertion["public_meta_observation_status"] in _ALLOWED_PUBLIC_META_STATUSES
    assert isinstance(assertion["should_include_public_input_feedback"], bool)
    assert isinstance(assertion["response_has_input_feedback"], bool)
    assert isinstance(assertion["response_input_feedback_comment_text_present"], bool)
    assert assertion["response_input_feedback_emlis_ai_status"] is None or isinstance(
        assertion["response_input_feedback_emlis_ai_status"],
        str,
    )
    assert isinstance(assertion["rn_modal_should_open"], bool)


def _minimal_internal_meta(status: str) -> dict[str, Any]:
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": status,
        "observation_trace_id": "phase19-5-public-boundary",
        "trace_id": "phase19-5-public-boundary-trace",
        "observation_reply_kind": "eligible_observation",
        "rejection_reasons": [] if status == "passed" else [f"phase19_5_{status}_reason"],
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": status,
            "composer_status": "generated" if status == "passed" else "not_generated",
            "current_input": {"memo": _SECRET_RAW_INPUT},
            "comment_text": _SECRET_INTERNAL_COMMENT,
        },
        "current_input": {"memo": _SECRET_RAW_INPUT},
        "raw_input": _SECRET_RAW_INPUT,
        "raw_text": _SECRET_RAW_INPUT,
        "comment_text": _SECRET_INTERNAL_COMMENT,
        "evidence_spans": [{"raw_text": _SECRET_RAW_INPUT}],
    }


def _assert_response_shape_has_not_changed(body: Mapping[str, Any]) -> None:
    assert set(body.keys()) == {"status", "id", "created_at", "input_feedback"}
    for key in _FORBIDDEN_PUBLIC_RESPONSE_KEYS:
        assert key not in body
    feedback = body.get("input_feedback")
    if feedback is not None:
        assert isinstance(feedback, Mapping)
        assert set(feedback.keys()) == {"comment_text", "emlis_ai"}
        for key in _FORBIDDEN_PUBLIC_RESPONSE_KEYS:
            assert key not in feedback


def _assert_no_internal_payload_leak(body: Mapping[str, Any]) -> None:
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)
    for fragment in _FORBIDDEN_PUBLIC_RESPONSE_FRAGMENTS:
        assert fragment not in dumped
    assert _SECRET_RAW_INPUT not in dumped
    assert _SECRET_INTERNAL_COMMENT not in dumped


@pytest.mark.asyncio
@pytest.mark.parametrize("case", PHASE19_REAL_DEVICE_ABCD_CASES, ids=lambda case: case.case_id)
async def test_phase19_5_real_device_abcd_reaches_final_public_feedback_boundary(
    monkeypatch: pytest.MonkeyPatch,
    case: Phase19RealDeviceCase,
) -> None:
    _enable_complete_initial(monkeypatch)
    _patch_submit_persistence(monkeypatch, inserted_id=_PHASE19_SAFE_INSERTED_IDS[case.case_id])
    captured: dict[str, Any] = {}
    _patch_real_reply_source_bundle(monkeypatch, captured)

    result = await submit_service.persist_emotion_submission(
        user_id=f"phase19-5-user-{case.case_id}",
        emotions=list(case.emotions),
        memo=case.memo,
        memo_action=case.memo_action,
        category=list(case.categories),
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else {}
    comment_text = str(result.get("input_feedback_comment") or "").strip()
    inserted = result.get("inserted") if isinstance(result.get("inserted"), Mapping) else {}
    body = _public_response_body(
        inserted_id=str(inserted.get("id") or ""),
        comment_text=comment_text,
        public_meta=public_meta,
    )

    _assert_public_response_shape_unchanged(body)
    _assert_public_body_has_no_internal_leaks(body, case)

    boundary = _boundary_assertion(
        case_id=case.case_id,
        reply_comment_text_present=bool(captured.get("reply_comment_text_present")),
        comment_text_for_public_boundary=comment_text,
        public_meta=public_meta,
        body=body,
    )
    failure_context = json.dumps(boundary, ensure_ascii=False, indent=2, sort_keys=True)

    if case.expected_observation_status == "non_passed":
        assert boundary["public_meta_observation_status"] in {
            "rejected",
            "unavailable",
            "safety_blocked",
        }, failure_context
    else:
        assert boundary["public_meta_observation_status"] == case.expected_observation_status, failure_context
    assert (
        boundary["response_has_input_feedback"] is case.expected_public_input_feedback_included
    ), failure_context
    assert (
        boundary["response_input_feedback_comment_text_present"]
        is case.expected_public_input_feedback_included
    ), failure_context
    assert boundary["rn_modal_should_open"] is bool(case.expected_rn_modal_opened), failure_context

    if case.expected_public_input_feedback_included:
        assert boundary["reply_comment_text_present"] is True, failure_context
        assert boundary["should_include_public_input_feedback"] is True, failure_context
        assert boundary["response_input_feedback_emlis_ai_status"] == "passed", failure_context
        assert body["input_feedback"]["comment_text"] == comment_text
    else:
        assert boundary["should_include_public_input_feedback"] is False, failure_context
        assert boundary["response_input_feedback_emlis_ai_status"] is None, failure_context
        assert body["input_feedback"] is None


def test_phase19_5_passed_public_meta_without_comment_is_downgraded_to_unavailable() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _minimal_internal_meta("passed"),
        comment_text_present=False,
        subscription_tier="free",
    )
    body = _public_response_body(
        inserted_id="phase19-5-empty-comment",
        comment_text="",
        public_meta=public_meta,
    )
    boundary = _boundary_assertion(
        case_id="phase19_5_passed_meta_empty_comment",
        reply_comment_text_present=False,
        comment_text_for_public_boundary="",
        public_meta=public_meta,
        body=body,
    )

    assert public_meta["observation_status"] == "unavailable"
    assert public_meta["rejection_reasons"][0] == "public_feedback_comment_text_missing"
    assert boundary["should_include_public_input_feedback"] is False
    assert boundary["response_has_input_feedback"] is False
    assert boundary["rn_modal_should_open"] is False
    _assert_response_shape_has_not_changed(body)
    _assert_no_internal_payload_leak(body)


@pytest.mark.parametrize("status", ["rejected", "unavailable", "safety_blocked"])
def test_phase19_5_non_passed_public_meta_is_not_included_even_when_comment_exists(status: str) -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _minimal_internal_meta(status),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _public_response_body(
        inserted_id=f"phase19-5-{status}",
        comment_text=_VISIBLE_COMMENT,
        public_meta=public_meta,
    )
    boundary = _boundary_assertion(
        case_id=f"phase19_5_{status}_with_comment",
        reply_comment_text_present=True,
        comment_text_for_public_boundary=_VISIBLE_COMMENT,
        public_meta=public_meta,
        body=body,
    )

    assert public_meta["observation_status"] == status
    assert boundary["should_include_public_input_feedback"] is False
    assert boundary["response_has_input_feedback"] is False
    assert boundary["response_input_feedback_comment_text_present"] is False
    assert boundary["response_input_feedback_emlis_ai_status"] is None
    assert boundary["rn_modal_should_open"] is False
    _assert_response_shape_has_not_changed(body)
    _assert_no_internal_payload_leak(body)


def test_phase19_5_passed_comment_text_is_included_with_unchanged_public_shape() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _minimal_internal_meta("passed"),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _public_response_body(
        inserted_id="phase19-5-passed-comment",
        comment_text=_VISIBLE_COMMENT,
        public_meta=public_meta,
    )
    boundary = _boundary_assertion(
        case_id="phase19_5_passed_comment",
        reply_comment_text_present=True,
        comment_text_for_public_boundary=_VISIBLE_COMMENT,
        public_meta=public_meta,
        body=body,
    )

    assert public_meta["observation_status"] == "passed"
    assert boundary["should_include_public_input_feedback"] is True
    assert boundary["response_has_input_feedback"] is True
    assert boundary["response_input_feedback_comment_text_present"] is True
    assert boundary["response_input_feedback_emlis_ai_status"] == "passed"
    assert boundary["rn_modal_should_open"] is True
    assert body["input_feedback"]["comment_text"] == _VISIBLE_COMMENT
    assert set(body["input_feedback"].keys()) == {"comment_text", "emlis_ai"}
    _assert_response_shape_has_not_changed(body)
    _assert_no_internal_payload_leak(body)
