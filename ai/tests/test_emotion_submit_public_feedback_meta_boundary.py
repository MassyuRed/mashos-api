from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from emlis_ai_public_feedback_meta import (
    PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES,
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)

VISIBLE_COMMENT = "これはpublic responseに表示してよいEmlis観測文です"
SECRET_RAW_INPUT = "これはpublic responseへ出してはいけない長文入力本文_STEP5"
SECRET_EVIDENCE = "これはpublic responseへ出してはいけない根拠全文_STEP5"
SECRET_INTERNAL_COMMENT = "これはpublic metaへ混ぜてはいけない内部comment_text_STEP5"


def _compact_json_bytes(value: Mapping[str, Any]) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _response_body(comment_text: str, public_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {"comment_text": comment_text, "emlis_ai": dict(public_meta or {})}
    return {
        "status": "ok",
        "id": "emotion-log-step5",
        "created_at": "2026-05-23T00:00:00+00:00",
        "input_feedback": feedback,
    }


def _huge_internal_meta(status: str) -> dict[str, Any]:
    raw_items = []
    for index in range(320):
        raw_items.append({
            "span_id": f"span-{index}",
            "raw_text": f"{SECRET_EVIDENCE}-{index}",
            "source_text": SECRET_RAW_INPUT,
            "current_input": {"memo": SECRET_RAW_INPUT},
        })

    gate_results = {
        "reader": {"passed": True, "primary_reason": "passed", "raw_text": SECRET_RAW_INPUT},
        "grounding": {"passed": True, "primary_reason": "passed", "evidence_spans": raw_items},
        "display": {"passed": status == "passed", "primary_reason": status},
    }

    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": status,
        "observation_trace_id": "emlisobs-step5-public-response-boundary",
        "trace_id": "trace-step5-public-response-boundary",
        "observation_reply_kind": "low_information_observation",
        "rejection_reasons": ["safe_public_reason"] * 80,
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": status,
            "coverage_group": "low_information",
            "composer_status": "generated",
            "composer_source": "ai_generated",
            "gate_results": gate_results,
            "complete_reply_service_diagnostics": {
                "used_phrase_unit_ids": ["phrase-unit-internal-only"],
                "relation_types": ["relation-internal-only"],
                "current_input": {"memo": SECRET_RAW_INPUT},
                "comment_text": SECRET_INTERNAL_COMMENT,
            },
        },
        "runtime_surface_pre_return_gate": {
            "passed": status == "passed",
            "action": "pass" if status == "passed" else "fail_closed",
            "rerender_attempted": False,
            "rejection_reasons": ["runtime_reason"] * 80,
            "candidate_comment_text": SECRET_INTERNAL_COMMENT,
            "diagnostics": {"raw_text": SECRET_RAW_INPUT},
        },
        "observation_reply_meta": {
            "observation_reply_kind": "low_information_observation",
            "eligible_for_full_observation": False,
            "question_required": True,
            "user_fact_may_promote_to_eligible": False,
            "comment_text": SECRET_INTERNAL_COMMENT,
        },
        "complete_reply_service_diagnostics": {
            "used_phrase_unit_ids": ["phrase-unit-internal-only"],
            "relation_types": ["relation-internal-only"],
            "current_input": {"memo": SECRET_RAW_INPUT},
            "comment_text": SECRET_INTERNAL_COMMENT,
        },
        "multi_perspective": {
            "evidence_spans": raw_items,
            "perspective_board": {"raw_text": SECRET_EVIDENCE},
            "observation_graph": {"nodes": [{"text": SECRET_EVIDENCE, "body": SECRET_RAW_INPUT}]},
        },
        "current_input": {"memo": SECRET_RAW_INPUT},
        "raw_text": SECRET_EVIDENCE,
        "raw_input": SECRET_RAW_INPUT,
        "comment_text": SECRET_INTERNAL_COMMENT,
        "evidence_spans": raw_items,
    }


def _assert_no_internal_payload(body: dict[str, Any]) -> None:
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)
    assert '"evidence_spans"' not in dumped
    assert '"current_input"' not in dumped
    assert '"raw_text"' not in dumped
    assert '"raw_input"' not in dumped
    assert '"complete_reply_service_diagnostics"' not in dumped
    assert '"multi_perspective"' not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert SECRET_INTERNAL_COMMENT not in dumped


def _with_failed_visible_surface_gate(meta: dict[str, Any]) -> dict[str, Any]:
    out = dict(meta)
    out["visible_surface_acceptance_gate"] = {
        "version": "emlis.visible_surface_acceptance_gate.v1",
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": ["emotion_focus_unbridged_secondary"],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "rn_visible_contract_changed": False,
        "public_response_key_change": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
    }
    return out


def test_emotion_submit_public_response_meta_stays_small_when_internal_meta_is_huge() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _huge_internal_meta("passed"),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert body["input_feedback"]["comment_text"] == VISIBLE_COMMENT
    meta = body["input_feedback"]["emlis_ai"]
    assert meta["schema_version"] == "emlis.public_input_feedback_meta.v1"
    assert meta["observation_status"] == "passed"
    assert meta["observation_trace_id"] == "emlisobs-step5-public-response-boundary"
    assert meta["public_feedback_meta_boundary"]["sanitized"] is True
    assert meta["public_feedback_meta_boundary"]["internal_meta_returned"] is False
    assert _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES
    assert _compact_json_bytes(body) <= 16 * 1024
    _assert_no_internal_payload(body)


def test_emotion_submit_public_response_omits_failed_visible_surface_gate_feedback() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _with_failed_visible_surface_gate(_huge_internal_meta("passed")),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": ["emotion_focus_unbridged_secondary"],
    }
    assert body["input_feedback"] is None
    assert _compact_json_bytes(public_meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES
    _assert_no_internal_payload(body)


def test_emotion_submit_public_response_omits_unavailable_empty_comment_feedback() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _huge_internal_meta("unavailable"),
        comment_text_present=False,
        subscription_tier="free",
    )
    body = _response_body("", public_meta)

    assert body["input_feedback"] is None
    assert _compact_json_bytes(body) <= 4 * 1024
    _assert_no_internal_payload(body)


def test_observation_diagnostic_lockdown_keeps_classification_summary_without_raw_payload() -> None:
    from emlis_ai_observation_diagnostic_lockdown import (
        build_observation_diagnostic_lockdown,
        dump_observation_diagnostic,
    )

    diagnostic = build_observation_diagnostic_lockdown(
        input_feedback_comment=VISIBLE_COMMENT,
        input_feedback_meta=_huge_internal_meta("passed"),
        emotion_log_id="emotion-log-step5",
        created_at="2026-05-23T00:00:00+00:00",
    )
    dumped = dump_observation_diagnostic(diagnostic)

    assert diagnostic["classification"] == "passed_displayed"
    assert diagnostic["trace_id"] == "emlisobs-step5-public-response-boundary"
    assert diagnostic["used_phrase_unit_ids"] == ["phrase-unit-internal-only"]
    assert diagnostic["relation_types"] == ["relation-internal-only"]
    assert diagnostic["raw_input_included"] is False
    assert diagnostic["comment_text_included"] is False
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert SECRET_INTERNAL_COMMENT not in dumped


def test_emotion_submit_public_response_omits_feedback_when_visible_surface_gate_blocks() -> None:
    internal_meta = _huge_internal_meta("passed")
    internal_meta["multi_perspective"]["gate_trace"] = {
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": False,
            "classification": "repair_required",
            "action": "rerender_surface",
            "rejection_reasons": ["emotion_focus_unbridged_secondary"],
            "comment_text": SECRET_INTERNAL_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
            "raw_text": SECRET_EVIDENCE,
        }
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": ["emotion_focus_unbridged_secondary"],
    }
    assert body["input_feedback"] is None
    assert _compact_json_bytes(public_meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES
    _assert_no_internal_payload(body)


def test_emotion_submit_public_response_keeps_visible_surface_gate_summary_when_allowed() -> None:
    internal_meta = _huge_internal_meta("passed")
    internal_meta["multi_perspective"]["gate_trace"] = {
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": True,
            "classification": "pass",
            "action": "allow",
            "rejection_reasons": [],
            "comment_text": SECRET_INTERNAL_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
            "raw_text": SECRET_EVIDENCE,
        }
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert body["input_feedback"]["comment_text"] == VISIBLE_COMMENT
    meta = body["input_feedback"]["emlis_ai"]
    assert meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": True,
        "classification": "pass",
        "action": "allow",
    }
    assert _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES
    _assert_no_internal_payload(body)
