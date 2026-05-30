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


def test_phase5_emotion_submit_public_response_omits_failed_runtime_surface_gate_feedback() -> None:
    internal_meta = _huge_internal_meta("passed")
    internal_meta["runtime_surface_pre_return_gate"] = {
        "passed": False,
        "action": "block",
        "rerender_attempted": False,
        "rejection_reasons": ["environment_state_output_scope_marker_missing"],
        "candidate_comment_text": SECRET_INTERNAL_COMMENT,
        "diagnostics": {"raw_input": SECRET_RAW_INPUT, "raw_text": SECRET_EVIDENCE},
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["runtime_surface_pre_return_gate"] == {
        "passed": False,
        "action": "block",
        "rerender_attempted": False,
        "rejection_reasons": ["environment_state_output_scope_marker_missing"],
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


def _with_environment_state_output_runtime_gate(
    meta: dict[str, Any],
    *,
    runtime_passed: bool,
    marker_present: bool,
    terminal_block: bool = False,
    runtime_repair_applied: bool = False,
) -> dict[str, Any]:
    out = dict(meta)
    out["environment_state_output_surface_contract"] = {
        "connected": True,
        "single_record_only": True,
        "scope_marker_required": True,
        "required_scope_marker": "今回の入力では",
        "allowed_scope_markers": ["今回の入力では", "この入力では"],
        "forbidden_surface_claims": ["diagnosis", "period_tendency_from_single_record"],
        "output_theme_ids": [SECRET_RAW_INPUT],
        "raw_input": SECRET_RAW_INPUT,
        "comment_text": SECRET_INTERNAL_COMMENT,
    }
    out["environment_state_output_scope_marker_completion"] = {
        "schema_version": "cocolon.emlis.environment_state_output_surface_completion_result.v1",
        "evaluated": True,
        "applied": marker_present,
        "scope_marker": "今回の入力では",
        "target_line": "first_body_line",
        "target_line_index": 1,
        "before_marker_present": False,
        "after_marker_present": marker_present,
        "claim_rejection_reasons": [] if marker_present else ["environment_state_output_scope_marker_missing"],
        "action": "continue" if runtime_passed else "reject",
        "completed_text": SECRET_INTERNAL_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
    }
    out["runtime_surface_pre_return_gate"] = {
        "passed": runtime_passed,
        "action": "allow" if runtime_passed else "block",
        "rerender_attempted": False,
        "rejection_reasons": [] if runtime_passed else ["environment_state_output_scope_marker_missing"],
        "environment_state_output_frame_surface_limited_use": True,
        "environment_state_output_single_record_only": True,
        "environment_state_output_scope_marker_required": True,
        "environment_state_output_scope_marker_present": marker_present,
        "environment_state_output_runtime_marker_check_performed": True,
        "environment_state_output_runtime_double_check_active": True,
        "environment_state_output_runtime_gate_repair_applied": runtime_repair_applied,
        "environment_state_output_terminal_surface_block": terminal_block,
        "diagnosis_surface_blocked": terminal_block,
        "environment_state_output_output_theme_ids": [SECRET_RAW_INPUT],
        "comment_text": SECRET_INTERNAL_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
        "raw_text": SECRET_EVIDENCE,
    }
    return out


def test_phase5_public_meta_keeps_environment_state_completion_internal_only() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _with_environment_state_output_runtime_gate(
            _huge_internal_meta("passed"),
            runtime_passed=True,
            marker_present=True,
        ),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)

    assert body["input_feedback"]["comment_text"] == VISIBLE_COMMENT
    runtime_gate = body["input_feedback"]["emlis_ai"]["runtime_surface_pre_return_gate"]
    assert runtime_gate["passed"] is True
    assert runtime_gate["environment_state_output_frame_surface_limited_use"] is True
    assert runtime_gate["environment_state_output_scope_marker_required"] is True
    assert runtime_gate["environment_state_output_scope_marker_present"] is True
    assert runtime_gate["environment_state_output_runtime_marker_check_performed"] is True
    assert runtime_gate["environment_state_output_runtime_double_check_active"] is True
    assert runtime_gate["environment_state_output_runtime_gate_repair_applied"] is False
    assert runtime_gate["environment_state_output_terminal_surface_block"] is False
    assert "environment_state_output_scope_marker_completion" not in dumped
    assert "environment_state_output_surface_contract" not in dumped
    assert "environment_state_output_output_theme_ids" not in dumped
    _assert_no_internal_payload(body)


def test_phase5_public_response_omits_feedback_when_runtime_environment_state_gate_blocks() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _with_environment_state_output_runtime_gate(
            _huge_internal_meta("passed"),
            runtime_passed=False,
            marker_present=False,
            terminal_block=True,
        ),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["runtime_surface_pre_return_gate"]["passed"] is False
    assert public_meta["runtime_surface_pre_return_gate"]["action"] == "block"
    assert public_meta["runtime_surface_pre_return_gate"]["environment_state_output_scope_marker_present"] is False
    assert public_meta["runtime_surface_pre_return_gate"]["environment_state_output_terminal_surface_block"] is True
    assert body["input_feedback"] is None
    _assert_no_internal_payload(body)


def test_phase5_public_response_omits_feedback_when_runtime_environment_state_marker_check_fails_open_status() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _with_environment_state_output_runtime_gate(
            _huge_internal_meta("passed"),
            runtime_passed=True,
            marker_present=False,
        ),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["runtime_surface_pre_return_gate"]["passed"] is True
    assert public_meta["runtime_surface_pre_return_gate"]["environment_state_output_runtime_marker_check_performed"] is True
    assert public_meta["runtime_surface_pre_return_gate"]["environment_state_output_scope_marker_required"] is True
    assert public_meta["runtime_surface_pre_return_gate"]["environment_state_output_scope_marker_present"] is False
    assert body["input_feedback"] is None
    _assert_no_internal_payload(body)


def test_phase5_public_response_omits_non_passed_or_schema_invalid_status_even_with_comment_text() -> None:
    for internal_status in ("schema_invalid", "rejected", "unavailable"):
        public_meta = build_public_emlis_input_feedback_meta(
            _with_environment_state_output_runtime_gate(
                _huge_internal_meta(internal_status),
                runtime_passed=True,
                marker_present=True,
            ),
            comment_text_present=True,
            subscription_tier="free",
        )
        body = _response_body(VISIBLE_COMMENT, public_meta)

        assert body["input_feedback"] is None, internal_status
        assert public_meta["observation_status"] != "passed"
        _assert_no_internal_payload(body)


def test_phase10_emotion_submit_response_does_not_surface_state_answer_materials() -> None:
    internal_meta = _huge_internal_meta("passed")
    internal_meta.update(
        {
            "emlis_state_answer_surface_contract": {
                "schema_version": "cocolon.emlis_state_answer_surface_contract.v1",
                "material_id": "emlis_state_answer_surface_contract",
                "human_follow_layer": {
                    "primary_follow_key": "effort_receiving",
                    "comment_text": SECRET_INTERNAL_COMMENT,
                },
                "environment_state_output_frame": {
                    "memo": SECRET_RAW_INPUT,
                    "memo_action": SECRET_EVIDENCE,
                },
            },
            "state_answer_surface_contract": {
                "front_section_role": "state_answer_observation",
                "back_section_role": "human_follow",
                "raw_input": SECRET_RAW_INPUT,
                "comment_text": SECRET_INTERNAL_COMMENT,
            },
            "environment_state_output_frame": {
                "memo": SECRET_RAW_INPUT,
                "memo_action": SECRET_EVIDENCE,
            },
        }
    )
    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)

    assert set(body.keys()) == {"status", "id", "created_at", "input_feedback"}
    assert set(body["input_feedback"].keys()) == {"comment_text", "emlis_ai"}
    assert body["input_feedback"]["comment_text"] == VISIBLE_COMMENT
    assert body["input_feedback"]["emlis_ai"]["observation_status"] == "passed"

    for forbidden in (
        "emlis_state_answer_surface_contract",
        "state_answer_surface_contract",
        "environment_state_output_frame",
        "human_follow_layer",
        "primary_follow_key",
        "state_answer_observation",
        "human_follow",
    ):
        assert forbidden not in dumped

    _assert_no_internal_payload(body)


def _phase11_blocked_two_stage_gate_payload() -> dict[str, Any]:
    return {
        "schema_version": "cocolon.emlis_ai_two_stage_reception.cross_gate.v1",
        "material_id": "emlis_ai_two_stage_reception_cross_gate",
        "evaluated": True,
        "active": True,
        "connected": True,
        "two_stage_required": True,
        "passed": False,
        "blocked": True,
        "terminal_surface_block": True,
        "labels_present": True,
        "label_order_valid": True,
        "observation_section_non_empty": True,
        "reception_section_non_empty": True,
        "reception_mode_id": "daily_unpleasant_reception",
        "reception_mode_family": "daily_reception",
        "daily_reception_question_escape_blocked": True,
        "rejection_reasons": ["daily_reception_question_escape_when_event_fact_present"],
        "surface_blocker_reasons": ["daily_reception_question_escape_when_event_fact_present"],
        "comment_text": SECRET_INTERNAL_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
        "raw_text": SECRET_EVIDENCE,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def test_phase11_emotion_submit_public_response_omits_two_stage_gate_blocked_feedback() -> None:
    internal_meta = _huge_internal_meta("passed")
    internal_meta["two_stage_reception_gate"] = _phase11_blocked_two_stage_gate_payload()

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)

    assert public_meta["observation_status"] == "rejected"
    assert public_meta["rejection_reasons"][0] == "public_feedback_two_stage_reception_gate_blocked"
    assert public_meta["two_stage_reception_gate"]["passed"] is False
    assert body["input_feedback"] is None
    assert SECRET_INTERNAL_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    _assert_no_internal_payload(body)


def test_phase11_emotion_submit_inclusion_summary_marks_two_stage_gate_without_body() -> None:
    from emotion_submit_service import (
        _build_public_feedback_inclusion_summary,
        _public_input_feedback_comment,
    )

    internal_meta = _huge_internal_meta("passed")
    internal_meta["two_stage_reception_gate"] = {
        "evaluated": True,
        "passed": False,
        "blocked": True,
        "terminal_surface_block": True,
        "rejection_reasons": ["two_stage_bad_grammar_or_koto_splice_surface"],
        "comment_text": SECRET_INTERNAL_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
    }
    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=VISIBLE_COMMENT,
        internal_input_feedback_meta=internal_meta,
        public_input_feedback_meta=public_meta,
    )

    assert _public_input_feedback_comment(VISIBLE_COMMENT, public_meta) == ""
    assert summary["public_feedback_included"] is False
    assert summary["public_feedback_not_included_two_stage_reception_gate"] is True
    assert summary["candidate_fail_closed_display_absent"] is True
    assert summary["reason_family"] == "two_stage_reception_gate"
    assert "two_stage_bad_grammar_or_koto_splice_surface" in summary["reason_codes"]
    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert SECRET_INTERNAL_COMMENT not in dumped
