from __future__ import annotations

import importlib
import json
from collections.abc import Mapping
from typing import Any


SECRET_COMMENT = "これはpublic metaへ入れてはいけない観測本文です"
SECRET_RAW_INPUT = "これはpublic metaへ入れてはいけない入力本文です"
SECRET_EVIDENCE = "これはpublic metaへ入れてはいけない根拠全文です"

ENVIRONMENT_STATE_OUTPUT_INTERNAL_KEYS = {
    "environment_state_output_surface_contract",
    "environment_state_output_scope_marker_completion",
    "environment_state_output_scope_marker_completion_action",
    "environment_state_output_scope_marker_applied",
    "environment_state_output_allowed_scope_markers",
    "environment_state_output_forbidden_surface_claims",
    "environment_state_output_output_theme_ids",
    "environment_state_output_runtime_marker_check_performed",
    "environment_state_output_runtime_double_check_active",
    "environment_state_output_runtime_gate_repair_applied",
    "environment_state_output_terminal_surface_block",
}


FORBIDDEN_PUBLIC_KEYS = {
    "multi_perspective",
    "evidence_spans",
    "perspective_reports",
    "perspective_board",
    "observation_graph",
    "composer_candidate",
    "complete_scorecard_event",
    "complete_scorecard_harness",
    "complete_reply_diagnostics",
    "complete_reply_service_diagnostics",
    "complete_composer_reply_diagnostics",
    "complete_initial_fixture_qa_run",
    "fixture_qa_run",
    "product_quality_scorecard",
    "release_ladder_guard",
    "current_input",
    "memo",
    "memo_text",
    "raw_input",
    "raw_text",
    "source_text",
    "input_text",
    "comment_text",
    "commentText",
    "candidate_comment_text",
    "public_comment_text",
    "realized_text",
    "body",
    "text",
}


class ExplodingMapping(Mapping[str, Any]):
    """Mapping that lets the sanitizer prove fail-closed behavior."""

    def __getitem__(self, key: str) -> Any:  # pragma: no cover - invoked by implementation under test
        raise RuntimeError(f"unexpected read: {key}")

    def __iter__(self):  # pragma: no cover - invoked by implementation under test
        raise RuntimeError("unexpected iteration")

    def __len__(self) -> int:
        return 1

    def get(self, key: str, default: Any = None) -> Any:  # pragma: no cover - invoked by implementation under test
        raise RuntimeError(f"unexpected get: {key}")



def _public_meta_module():
    # Step 1 is test-first. Step 2 must add this module and make these
    # contract tests pass without loosening the RN display contract.
    return importlib.import_module("emlis_ai_public_feedback_meta")



def _compact_json_bytes(value: Mapping[str, Any]) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))



def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_all_keys(nested))
    elif isinstance(value, list):
        for nested in value:
            keys.update(_all_keys(nested))
    return keys



def _dump(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)



def _large_internal_meta() -> dict[str, Any]:
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "internal-tier-must-not-override-explicit-subscription",
        "observation_status": "passed",
        "observation_trace_id": "emlisobs-public-boundary",
        "trace_id": "trace-public-boundary",
        "observation_reply_kind": "low_information_observation",
        "rejection_reasons": [f"reason_{idx}_" + ("x" * 160) for idx in range(32)],
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": "passed",
            "secondary_reasons": ["must_not_be_copied"],
            "coverage_group": "low_information",
            "coverage_scope": "current_input_core",
            "composer_status": "generated",
            "composer_source": "ai_generated",
            "gate_results": {
                "reader": {
                    "passed": True,
                    "primary_reason": "passed",
                    "raw_text": SECRET_RAW_INPUT,
                    "rejection_reasons": ["must_not_be_copied"],
                },
                "grounding": {
                    "passed": True,
                    "primary_reason": "passed",
                    "debug_payload": {"raw_text": SECRET_EVIDENCE},
                },
                "display": {
                    "passed": True,
                    "primary_reason": "passed",
                    "comment_text": SECRET_COMMENT,
                },
            },
            "complete_reply_service_diagnostics": {
                "current_input": {"memo": SECRET_RAW_INPUT},
                "comment_text": SECRET_COMMENT,
                "complete_candidate_generated": True,
            },
        },
        "runtime_surface_pre_return_gate": {
            "passed": True,
            "action": "pass",
            "rerender_attempted": False,
            "rejection_reasons": ["safe_reason"],
            "candidate_comment_text": SECRET_COMMENT,
            "diagnostics": {"raw_text": SECRET_RAW_INPUT},
        },
        "observation_reply_meta": {
            "observation_reply_kind": "low_information_observation",
            "eligible_for_full_observation": False,
            "question_required": True,
            "user_fact_may_promote_to_eligible": False,
            "comment_text": SECRET_COMMENT,
        },
        "step10_observation_display_repair_integration": {
            "applied": True,
            "final_observation_status": "passed",
            "observation_reply_kind": "low_information_observation",
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "rn_visible_contract_changed": False,
            "response_shape_changed": False,
            "display_gate_relaxed": False,
            "fixed_fallback_used": False,
            "external_ai_used": False,
            "comment_text": SECRET_COMMENT,
        },
        "multi_perspective": {
            "evidence_spans": [
                {
                    "span_id": "span-1",
                    "raw_text": SECRET_EVIDENCE,
                    "source_text": SECRET_RAW_INPUT,
                }
            ],
            "perspective_reports": [
                {
                    "observer": "reader",
                    "claims": [{"object": SECRET_RAW_INPUT}],
                }
            ],
            "perspective_board": {"raw_text": SECRET_EVIDENCE},
            "observation_graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "text": SECRET_EVIDENCE,
                        "body": SECRET_RAW_INPUT,
                    }
                ]
            },
            "composer_candidate": {
                "comment_text": SECRET_COMMENT,
                "current_input": {"memo": SECRET_RAW_INPUT},
            },
        },
        "complete_scorecard_event": {"raw_text": SECRET_EVIDENCE},
        "complete_scorecard_harness": {"raw_text": SECRET_EVIDENCE},
        "complete_reply_diagnostics": {"current_input": {"memo": SECRET_RAW_INPUT}},
        "complete_composer_reply_diagnostics": {"comment_text": SECRET_COMMENT},
        "complete_initial_fixture_qa_run": {"input_text": SECRET_RAW_INPUT},
        "fixture_qa_run": {"source_text": SECRET_EVIDENCE},
        "product_quality_scorecard": {"body": SECRET_EVIDENCE},
        "release_ladder_guard": {"text": SECRET_EVIDENCE},
        "current_input": {"memo": SECRET_RAW_INPUT},
        "memo": SECRET_RAW_INPUT,
        "memo_text": SECRET_RAW_INPUT,
        "raw_input": SECRET_RAW_INPUT,
        "raw_text": SECRET_EVIDENCE,
        "source_text": SECRET_EVIDENCE,
        "input_text": SECRET_RAW_INPUT,
        "comment_text": SECRET_COMMENT,
        "commentText": SECRET_COMMENT,
        "candidate_comment_text": SECRET_COMMENT,
        "public_comment_text": SECRET_COMMENT,
        "realized_text": SECRET_COMMENT,
        "body": SECRET_RAW_INPUT,
        "text": SECRET_RAW_INPUT,
    }



def _build_public_meta(internal_meta: Mapping[str, Any] | None, **kwargs: Any) -> dict[str, Any]:
    module = _public_meta_module()
    return module.build_public_emlis_input_feedback_meta(internal_meta, **kwargs)



def _visible_surface_gate_failed_payload() -> dict[str, Any]:
    return {
        "version": "emlis.visible_surface_acceptance_gate.v1",
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": [
            "emotion_focus_unbridged_secondary",
            SECRET_RAW_INPUT,
            "x" * 180,
        ],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "rn_visible_contract_changed": False,
        "public_response_key_change": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
    }



def test_public_feedback_meta_keeps_public_rn_contract_keys_and_boundary_marker() -> None:
    module = _public_meta_module()

    public_meta = module.build_public_emlis_input_feedback_meta(
        _large_internal_meta(),
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["schema_version"] == "emlis.public_input_feedback_meta.v1"
    assert public_meta["version"] == "emlis_ai_v3"
    assert public_meta["kernel_version"] == "multi_perspective_observation.v1"
    assert public_meta["tier"] == "free"
    assert public_meta["observation_status"] == "passed"
    assert public_meta["observation_trace_id"] == "emlisobs-public-boundary"
    assert public_meta["trace_id"] == "trace-public-boundary"
    assert public_meta["observation_reply_kind"] == "low_information_observation"

    boundary = public_meta["public_feedback_meta_boundary"]
    assert boundary == {
        "version": "emlis.public_feedback_meta_boundary.v1",
        "sanitized": True,
        "max_bytes": module.PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES,
        "trimmed": False,
        "internal_meta_returned": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }



def test_public_feedback_meta_drops_internal_text_and_diagnostic_payloads() -> None:
    public_meta = _build_public_meta(
        _large_internal_meta(),
        comment_text_present=True,
        subscription_tier="free",
    )

    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))



def test_phase5_public_feedback_meta_drops_environment_state_output_internal_completion_meta() -> None:
    internal_meta = _large_internal_meta()
    internal_meta.update({
        "environment_state_output_surface_contract": {
            "connected": True,
            "scope_marker_required": True,
            "required_scope_marker": "今回の入力では",
            "allowed_scope_markers": ["今回の入力では"],
            "comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
        },
        "environment_state_output_scope_marker_completion": {
            "schema_version": "cocolon.emlis.environment_state_output_surface_completion_result.v1",
            "evaluated": True,
            "connected": True,
            "applied": True,
            "scope_marker": "今回の入力では",
            "target_line": "first_body_line",
            "before_marker_present": False,
            "after_marker_present": True,
            "claim_rejection_reasons": [],
            "action": "continue",
            "display_gate_relaxed": False,
            "raw_input_included": False,
            "comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
        },
        "environment_state_output_scope_marker_completion_action": "continue",
        "environment_state_output_scope_marker_applied": True,
        "environment_state_output_allowed_scope_markers": ["今回の入力では", "この入力では"],
        "environment_state_output_forbidden_surface_claims": ["diagnosis"],
        "environment_state_output_output_theme_ids": ["output-theme-internal-only"],
        "environment_state_output_runtime_marker_check_performed": True,
        "environment_state_output_runtime_double_check_active": True,
        "environment_state_output_runtime_gate_repair_applied": False,
        "environment_state_output_terminal_surface_block": False,
    })

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert ENVIRONMENT_STATE_OUTPUT_INTERNAL_KEYS.isdisjoint(_all_keys(public_meta))
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert "output-theme-internal-only" not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


def test_public_feedback_meta_reduces_diagnostic_summary_to_safe_gate_summary() -> None:
    public_meta = _build_public_meta(
        _large_internal_meta(),
        comment_text_present=True,
        subscription_tier="free",
    )

    diagnostic_summary = public_meta["diagnostic_summary"]
    assert diagnostic_summary == {
        "stage": "display",
        "primary_reason": "passed",
        "coverage_group": "low_information",
        "composer_status": "generated",
        "composer_source": "ai_generated",
        "gate_results": {
            "reader": {"passed": True, "primary_reason": "passed"},
            "grounding": {"passed": True, "primary_reason": "passed"},
            "display": {"passed": True, "primary_reason": "passed"},
        },
    }
    for gate_summary in diagnostic_summary["gate_results"].values():
        assert set(gate_summary) <= {"passed", "primary_reason"}



def test_public_feedback_meta_retains_runtime_and_reply_optional_summaries_only() -> None:
    public_meta = _build_public_meta(
        _large_internal_meta(),
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["runtime_surface_pre_return_gate"] == {
        "passed": True,
        "action": "pass",
        "rerender_attempted": False,
        "rejection_reasons": ["safe_reason"],
    }
    assert public_meta["observation_reply_meta"] == {
        "observation_reply_kind": "low_information_observation",
        "eligible_for_full_observation": False,
        "question_required": True,
        "user_fact_may_promote_to_eligible": False,
    }
    assert public_meta["step10_observation_display_repair_integration"] == {
        "applied": True,
        "final_observation_status": "passed",
        "observation_reply_kind": "low_information_observation",
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "display_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
    }


def test_public_feedback_meta_retains_visible_surface_gate_summary_only() -> None:
    internal_meta = _large_internal_meta()
    internal_meta["multi_perspective"]["gate_trace"] = {
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": False,
            "classification": "repair_required",
            "action": "rerender_surface",
            "rejection_reasons": [
                "emotion_focus_unbridged_secondary",
                "visible_surface_reason_with_" + ("x" * 160),
                SECRET_RAW_INPUT,
            ],
            "comment_text": SECRET_COMMENT,
            "candidate_comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
            "raw_text": SECRET_EVIDENCE,
            "selected_emotion_count": 2,
            "malformed_nominalization_codes": ["malformed_nominalization_tari_fragment"],
        }
    }

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": [
            "emotion_focus_unbridged_secondary",
            "visible_surface_reason_with_" + ("x" * 68),
        ],
    }
    assert set(public_meta["visible_surface_acceptance_gate"]) <= {
        "evaluated",
        "passed",
        "classification",
        "action",
        "rejection_reasons",
    }
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))



def test_public_feedback_meta_exposes_visible_surface_acceptance_gate_summary_only() -> None:
    internal_meta = dict(_large_internal_meta())
    internal_meta["visible_surface_acceptance_gate"] = _visible_surface_gate_failed_payload()

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": [
            "emotion_focus_unbridged_secondary",
            "x" * 96,
        ],
    }
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


def test_public_feedback_meta_exposes_step7_surface_codes_and_display_absence_summary_only() -> None:
    internal_meta = dict(_large_internal_meta())
    internal_meta["runtime_surface_pre_return_gate"] = {
        "passed": False,
        "action": "rerender_shallow_v2",
        "rerender_attempted": True,
        "rejection_reasons": [
            "malformed_phrase_unit",
            SECRET_RAW_INPUT,
        ],
        "malformed_phrase_unit_count": 3,
        "koto_splice_detected": True,
        "koto_splice_codes": [
            "malformed_nominalization_conditional_fragment",
            SECRET_RAW_INPUT,
        ],
        "surface_malformed_nominalization_codes": [
            "residual_koto_splice_fragment",
            "long_clause_koto_attachment_risk",
        ],
        "comment_text": SECRET_COMMENT,
    }
    internal_meta["visible_surface_acceptance_gate"] = {
        "evaluated": True,
        "passed": False,
        "classification": "red",
        "action": "rerender_surface",
        "rejection_reasons": ["malformed_phrase_unit", "surface_relation_skeleton_major"],
        "koto_splice_detected": True,
        "koto_splice_codes": ["malformed_nominalization_conditional_fragment"],
        "relation_skeleton_marker_count": 2,
        "relation_skeleton_marker_codes": ["surface_relation_skeleton_major"],
        "relation_skeleton_major": True,
        "analytic_register_leak_count": 1,
        "analytic_register_leak_codes": ["analytic_register_leak"],
        "analytic_register_leak": True,
        "surface_repair_requested": True,
        "repair_reason_family": "koto_splice",
        "comment_text": SECRET_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
    }
    internal_meta["diagnostic_summary"] = {
        "stage": "display",
        "primary_reason": "visible_surface_gate_failed",
        "display_absence_summary": {
            "candidate_blocked_surface_grammar": True,
            "candidate_blocked_koto_splice": True,
            "candidate_blocked_relation_skeleton": True,
            "candidate_repair_attempted": True,
            "candidate_repair_succeeded": False,
            "candidate_repair_failed": True,
            "candidate_fail_closed_display_absent": True,
            "public_feedback_not_included_non_passed": True,
            "public_feedback_not_included_empty_comment_text": False,
            "rn_payload_absent": True,
            "reason_family": "koto_splice",
            "reason_codes": ["residual_koto_splice_fragment", SECRET_RAW_INPUT],
            "raw_text": SECRET_RAW_INPUT,
            "comment_text": SECRET_COMMENT,
        },
    }

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["runtime_surface_pre_return_gate"] == {
        "passed": False,
        "action": "rerender_shallow_v2",
        "rerender_attempted": True,
        "rejection_reasons": ["malformed_phrase_unit"],
        "koto_splice_detected": True,
        "malformed_phrase_unit_count": 3,
        "koto_splice_codes": ["malformed_nominalization_conditional_fragment"],
        "surface_malformed_nominalization_codes": [
            "residual_koto_splice_fragment",
            "long_clause_koto_attachment_risk",
        ],
    }
    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": False,
        "classification": "red",
        "action": "rerender_surface",
        "rejection_reasons": ["malformed_phrase_unit", "surface_relation_skeleton_major"],
        "koto_splice_detected": True,
        "relation_skeleton_major": True,
        "analytic_register_leak": True,
        "surface_repair_requested": True,
        "relation_skeleton_marker_count": 2,
        "analytic_register_leak_count": 1,
        "koto_splice_codes": ["malformed_nominalization_conditional_fragment"],
        "relation_skeleton_marker_codes": ["surface_relation_skeleton_major"],
        "analytic_register_leak_codes": ["analytic_register_leak"],
        "repair_reason_family": "koto_splice",
    }
    assert public_meta["diagnostic_summary"]["display_absence_summary"] == {
        "candidate_blocked_surface_grammar": True,
        "candidate_blocked_koto_splice": True,
        "candidate_blocked_relation_skeleton": True,
        "candidate_repair_attempted": True,
        "candidate_repair_succeeded": False,
        "candidate_repair_failed": True,
        "candidate_fail_closed_display_absent": True,
        "public_feedback_not_included_non_passed": True,
        "public_feedback_not_included_empty_comment_text": False,
        "rn_payload_absent": True,
        "reason_family": "koto_splice",
        "reason_codes": ["residual_koto_splice_fragment"],
    }
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


def test_public_feedback_meta_reads_visible_surface_gate_from_phase_gate_trace() -> None:
    internal_meta = dict(_large_internal_meta())
    internal_meta["phase_gate"] = {
        "gate_trace": {
            "visible_surface_acceptance_gate": _visible_surface_gate_failed_payload(),
        },
        "visible_surface_acceptance_gate_comment_text_body_included": False,
        "visible_surface_acceptance_gate_raw_input_included": False,
    }

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["visible_surface_acceptance_gate"]["passed"] is False
    assert public_meta["visible_surface_acceptance_gate"]["classification"] == "repair_required"
    assert public_meta["visible_surface_acceptance_gate"]["action"] == "rerender_surface"
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped


def test_public_feedback_meta_fails_visible_surface_summary_closed_when_gate_contract_is_unsafe() -> None:
    internal_meta = dict(_large_internal_meta())
    unsafe_gate = _visible_surface_gate_failed_payload()
    unsafe_gate["comment_text_body_included"] = True
    unsafe_gate["comment_text"] = SECRET_COMMENT
    internal_meta["visible_surface_acceptance_gate"] = unsafe_gate

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["visible_surface_acceptance_gate"] == {
        "passed": False,
        "classification": "red",
        "action": "fail_closed",
        "rejection_reasons": ["visible_surface_acceptance_gate_public_meta_unsafe"],
    }
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped


def test_phase5_public_feedback_meta_downgrades_passed_status_when_comment_text_is_absent() -> None:
    public_meta = _build_public_meta(
        _large_internal_meta(),
        comment_text_present=False,
        subscription_tier="free",
    )

    assert public_meta["observation_status"] == "unavailable"
    assert public_meta["rejection_reasons"][0] == "public_feedback_comment_text_missing"
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False
    assert SECRET_COMMENT not in _dump(public_meta)


def test_phase5_public_feedback_meta_hides_environment_state_output_completion_internal_result() -> None:
    internal_meta = dict(_large_internal_meta())
    internal_meta["environment_state_output_scope_marker_completion"] = {
        "schema_version": "cocolon.emlis.environment_state_output_surface_contract_completion.v1",
        "evaluated": True,
        "applied": True,
        "scope_marker": "今回の入力では",
        "target_line": "first_body_line",
        "candidate_comment_text": SECRET_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
        "internal_completion_result": {"comment_text": SECRET_COMMENT},
    }
    internal_meta["composer_meta"] = {
        "environment_state_output_scope_marker_completion": internal_meta["environment_state_output_scope_marker_completion"],
    }

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    dumped = _dump(public_meta)
    assert "environment_state_output_scope_marker_completion" not in dumped
    assert "internal_completion_result" not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


def test_public_feedback_meta_caps_reason_count_string_lengths_and_total_bytes() -> None:
    module = _public_meta_module()

    public_meta = module.build_public_emlis_input_feedback_meta(
        _large_internal_meta(),
        comment_text_present=True,
        subscription_tier="free",
    )

    assert len(public_meta["rejection_reasons"]) == module.PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS
    assert all(
        len(reason) <= module.PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH
        for reason in public_meta["rejection_reasons"]
    )
    assert _compact_json_bytes(public_meta) <= module.PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES



def test_public_feedback_meta_returns_minimal_unavailable_when_sanitizer_cannot_read_meta() -> None:
    module = _public_meta_module()

    public_meta = module.build_public_emlis_input_feedback_meta(
        ExplodingMapping(),
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta == {
        "schema_version": "emlis.public_input_feedback_meta.v1",
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "unavailable",
        "rejection_reasons": ["public_feedback_meta_sanitizer_failed"],
        "public_feedback_meta_boundary": {
            "version": "emlis.public_feedback_meta_boundary.v1",
            "sanitized": True,
            "max_bytes": module.PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES,
            "trimmed": True,
            "internal_meta_returned": False,
            "raw_input_included": False,
            "comment_text_included": False,
        },
    }
    assert _compact_json_bytes(public_meta) <= module.PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES


def test_should_include_public_input_feedback_requires_comment_and_passed_public_meta() -> None:
    module = _public_meta_module()

    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {"observation_status": "passed"},
    ) is True
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {
            "observation_status": "passed",
            "visible_surface_acceptance_gate": {
                "passed": True,
                "classification": "yellow",
                "action": "warn",
            },
        },
    ) is True
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {
            "observation_status": "passed",
            "visible_surface_acceptance_gate": {
                "passed": False,
                "classification": "repair_required",
                "action": "rerender_surface",
            },
        },
    ) is False
    assert module.should_include_public_input_feedback(
        "",
        {"observation_status": "passed"},
    ) is False
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {"observation_status": "unavailable"},
    ) is False
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {"version": "legacy_meta_without_public_status"},
    ) is False
    assert module.should_include_public_input_feedback("Emlisの観測本文です。", None) is False
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {
            "observation_status": "passed",
            "runtime_surface_pre_return_gate": {
                "passed": False,
                "action": "block",
                "rejection_reasons": ["environment_state_output_scope_marker_missing"],
            },
        },
    ) is False
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {
            "observation_status": "passed",
            "runtime_surface_pre_return_gate": {
                "passed": True,
                "action": "allow",
                "rejection_reasons": ["environment_state_output_scope_marker_missing"],
            },
        },
    ) is False
    assert module.should_include_public_input_feedback(
        "Emlisの観測本文です。",
        {
            "observation_status": "passed",
            "runtime_surface_pre_return_gate": {
                "passed": True,
                "action": "pass",
            },
            "visible_surface_acceptance_gate": {
                "passed": True,
                "classification": "pass",
                "action": "allow",
            },
        },
    ) is True


def test_step7_public_feedback_meta_keeps_surface_reason_summary_code_only() -> None:
    internal_meta = dict(_large_internal_meta())
    gate = _visible_surface_gate_failed_payload()
    gate.update({
        "koto_splice_detected": True,
        "koto_splice_codes": [
            "malformed_nominalization_conditional_fragment",
            "residual_koto_splice_fragment",
            SECRET_COMMENT,
        ],
        "relation_skeleton_major": True,
        "relation_skeleton_marker_count": 3,
        "relation_skeleton_marker_codes": ["surface_relation_skeleton_major"],
        "analytic_register_leak": True,
        "analytic_register_leak_count": 2,
        "analytic_register_leak_codes": ["analytic_register_leak"],
        "surface_repair_requested": True,
        "repair_reason_family": "koto_splice",
        "comment_text": SECRET_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
    })
    internal_meta["visible_surface_acceptance_gate"] = gate
    internal_meta["diagnostic_summary"]["step7_public_feedback_diagnostic_summary"] = {
        "candidate_blocked_surface_grammar": True,
        "candidate_blocked_koto_splice": True,
        "candidate_blocked_relation_skeleton": True,
        "candidate_repair_attempted": True,
        "candidate_repair_succeeded": False,
        "candidate_repair_failed": True,
        "candidate_fail_closed_display_absent": True,
        "public_feedback_not_included_non_passed": False,
        "public_feedback_not_included_empty_comment_text": False,
        "public_feedback_not_included_visible_surface_gate": True,
        "rn_payload_absent": True,
        "reason_family": "koto_splice",
        "reason_codes": ["malformed_nominalization_conditional_fragment", SECRET_RAW_INPUT],
        "comment_text": SECRET_COMMENT,
    }

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": False,
        "classification": "repair_required",
        "action": "rerender_surface",
        "rejection_reasons": [
            "emotion_focus_unbridged_secondary",
            "x" * 96,
        ],
        "koto_splice_detected": True,
        "relation_skeleton_major": True,
        "analytic_register_leak": True,
        "surface_repair_requested": True,
        "relation_skeleton_marker_count": 3,
        "analytic_register_leak_count": 2,
        "koto_splice_codes": [
            "malformed_nominalization_conditional_fragment",
            "residual_koto_splice_fragment",
        ],
        "relation_skeleton_marker_codes": ["surface_relation_skeleton_major"],
        "analytic_register_leak_codes": ["analytic_register_leak"],
        "repair_reason_family": "koto_splice",
    }
    assert public_meta["diagnostic_summary"]["display_absence_summary"] == {
        "candidate_blocked_surface_grammar": True,
        "candidate_blocked_koto_splice": True,
        "candidate_blocked_relation_skeleton": True,
        "candidate_repair_attempted": True,
        "candidate_repair_succeeded": False,
        "candidate_repair_failed": True,
        "candidate_fail_closed_display_absent": True,
        "public_feedback_not_included_non_passed": False,
        "public_feedback_not_included_empty_comment_text": False,
        "public_feedback_not_included_visible_surface_gate": True,
        "rn_payload_absent": True,
        "reason_family": "koto_splice",
        "reason_codes": ["malformed_nominalization_conditional_fragment"],
    }
    dumped = _dump(public_meta)
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


def test_phase10_public_feedback_meta_strips_state_answer_surface_contract_body() -> None:
    from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract

    current_input = {
        "id": "phase10-public-meta-state-answer-001",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": SECRET_RAW_INPUT,
        "memo_action": SECRET_EVIDENCE,
        "emotion_details": [{"type": "自己否定", "strength": "strong"}],
        "category": ["自己理解"],
    }
    state_answer_contract = build_emlis_state_answer_surface_contract(current_input)
    internal_meta = dict(_large_internal_meta())
    internal_meta.update(
        {
            "observation_status": "passed",
            "emlis_state_answer_surface_contract": state_answer_contract.as_meta(),
            "state_answer_surface_contract": state_answer_contract.composer_payload(),
            "state_answer_composer_role_plan": {
                "front_section_role": "state_answer_observation",
                "back_section_role": "human_follow",
                "raw_input": SECRET_RAW_INPUT,
                "comment_text": SECRET_COMMENT,
            },
            "environment_state_output_frame": state_answer_contract.as_meta().get("environment_state_output_frame"),
            "comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
            "raw_text": SECRET_EVIDENCE,
        }
    )

    public_meta = _build_public_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    dumped = _dump(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["public_feedback_meta_boundary"]["internal_meta_returned"] is False
    assert public_meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False

    for forbidden in (
        "emlis_state_answer_surface_contract",
        "state_answer_surface_contract",
        "state_answer_composer_role_plan",
        "environment_state_output_frame",
        "human_follow_layer",
        "primary_follow_key",
        "secondary_follow_keys",
        "afterglow_follow_key",
        "ratio_policy",
        "observation_layer",
        "special_handling",
        "metaphor_policy",
        "surface_policy",
        "state_answer_observation",
        "human_follow",
    ):
        assert forbidden not in dumped

    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


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
        "two_stage_labels_present": True,
        "observation_label_present": True,
        "reception_label_present": True,
        "label_order_valid": True,
        "observation_section_non_empty": True,
        "reception_section_non_empty": True,
        "reception_mode_id": "daily_unpleasant_reception",
        "reception_mode_family": "daily_reception",
        "daily_reception_question_escape_blocked": True,
        "rejection_reasons": [
            "daily_reception_question_escape_when_event_fact_present",
            SECRET_RAW_INPUT,
            "x" * 180,
        ],
        "surface_blocker_reasons": ["daily_reception_question_escape_when_event_fact_present"],
        "comment_text": SECRET_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
        "raw_text": SECRET_EVIDENCE,
        "observation_text": SECRET_COMMENT,
        "reception_text": SECRET_COMMENT,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
    }


def test_phase11_public_feedback_meta_downgrades_passed_when_two_stage_gate_blocks() -> None:
    module = _public_meta_module()
    internal_meta = dict(_large_internal_meta())
    internal_meta["two_stage_reception_gate"] = _phase11_blocked_two_stage_gate_payload()

    public_meta = module.build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    dumped = _dump(public_meta)

    assert public_meta["observation_status"] == "rejected"
    assert public_meta["rejection_reasons"][0] == "public_feedback_two_stage_reception_gate_blocked"
    assert public_meta["two_stage_reception_gate"]["passed"] is False
    assert public_meta["two_stage_reception_gate"]["blocked"] is True
    assert public_meta["two_stage_reception_gate"]["terminal_surface_block"] is True
    assert public_meta["two_stage_reception_gate"]["daily_reception_question_escape_blocked"] is True
    assert len(public_meta["two_stage_reception_gate"]["rejection_reasons"][0]) <= module.PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH
    assert module.should_include_public_input_feedback("見えたこと：\n...", public_meta) is False
    assert SECRET_COMMENT not in dumped
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert FORBIDDEN_PUBLIC_KEYS.isdisjoint(_all_keys(public_meta))


def test_phase11_should_include_public_input_feedback_rejects_direct_two_stage_gate_block() -> None:
    module = _public_meta_module()

    comment_text = "見えたこと：\n入力内の出来事が見えます。\n\nEmlisから：\n受け取り文です。"

    assert module.should_include_public_input_feedback(
        comment_text,
        {
            "observation_status": "passed",
            "two_stage_reception_gate": {
                "evaluated": True,
                "passed": False,
                "blocked": True,
                "terminal_surface_block": True,
                "rejection_reasons": ["two_stage_section_order_invalid"],
            },
        },
    ) is False

    assert module.should_include_public_input_feedback(
        comment_text,
        {
            "observation_status": "passed",
            "two_stage_reception_gate": {
                "evaluated": True,
                "passed": True,
                "blocked": False,
                "terminal_surface_block": False,
            },
        },
    ) is True
