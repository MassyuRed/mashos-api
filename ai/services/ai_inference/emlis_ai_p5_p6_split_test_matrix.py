# -*- coding: utf-8 -*-
"""P5/P6 split test matrix and body-free handoff lock.

R9 does not claim the full backend suite is green.  It fixes the smaller
P5/P6 confirmation matrix and exports a compact, body-free handoff summary for
later P7 design work.  The handoff is an internal diagnostic contract only; it
must not change RN, DB, routes, request keys, public response top-level keys, or
release decisions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

P5_P6_SPLIT_TEST_MATRIX_SCHEMA_VERSION: Final = "cocolon.emlis.p5_p6.split_test_matrix.v1"
P5_P6_HANDOFF_LOCK_SCHEMA_VERSION: Final = "cocolon.emlis.p5_p6.split_test_matrix_handoff.v1"
P5_P6_R9_REPAIR_STEP: Final = "R9_P5P6SplitTestMatrixHandoff_20260612"

_P5_FOCUSED_TESTS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_p5_readiness_freeze_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_visibility_boundary_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_eligibility_matrix_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_surface_role_plan_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_safety_guard_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_product_quality_review_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_limited_visible_connection_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_regression_handoff_20260611.py",
    "tests/test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612.py",
    "tests/test_emlis_ai_user_label_connection_p5_visible_connection_r3_boundary_20260612.py",
    "tests/test_emlis_ai_user_label_connection_p5_public_meta_human_qa_boundary_r4_20260612.py",
    "tests/test_emlis_ai_user_label_connection_p5_body_free_public_meta_boundary_r4_20260612.py",
)

_P6_FOCUSED_TESTS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_structure_insight_p6_entry_freeze_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_inventory_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_family_boundary_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_relation_policy_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_quality_rubric_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_gate_hardening_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_surface_role_plan_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_family_review_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_product_quality_review_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_regression_handoff_20260611.py",
    "tests/test_emlis_ai_structure_insight_p6_runtime_bridge_20260612.py",
    "tests/test_emlis_ai_structure_insight_p6_limited_surface_r7_20260612.py",
    "tests/test_emlis_ai_structure_insight_p6_no_connect_regression_r8_20260612.py",
)

_RUNTIME_PUBLIC_REGRESSION_TESTS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_material.py",
    "tests/test_emlis_ai_user_label_connection_candidate.py",
    "tests/test_emlis_ai_user_label_connection_gate.py",
    "tests/test_emlis_ai_user_label_connection_surface.py",
    "tests/test_emlis_ai_user_label_connection_public_boundary.py",
    "tests/test_emlis_ai_user_label_connection_e2e_contract.py",
    "tests/test_emlis_ai_public_observation_recovery_acceptance_p0.py",
    "tests/test_emlis_ai_public_surface_requirement_p1.py",
    "tests/test_emlis_ai_product_surface_validation_p3.py",
    "tests/test_emotion_submit_public_feedback_inclusion_summary_p7.py",
    "tests/test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e.py",
)

_NO_CONNECT_SAFETY_TESTS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_free_tier_boundary.py",
    "tests/test_emlis_ai_user_label_connection_low_information_boundary.py",
    "tests/test_emlis_ai_user_label_connection_no_raw_text_meta.py",
    "tests/test_emlis_ai_d_source_unavailable_normal_observation_recovery.py",
    "tests/test_emlis_ai_limited_grounding_reception_surface_p4.py",
)

_R0_R8_TARGETED_TESTS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612.py",
    "tests/test_emlis_ai_user_label_connection_p5_visible_connection_r3_boundary_20260612.py",
    "tests/test_emlis_ai_user_label_connection_p5_public_meta_human_qa_boundary_r4_20260612.py",
    "tests/test_emlis_ai_user_label_connection_p5_body_free_public_meta_boundary_r4_20260612.py",
    "tests/test_emlis_ai_structure_insight_p6_runtime_bridge_20260612.py",
    "tests/test_emlis_ai_structure_insight_p6_limited_surface_r7_20260612.py",
    "tests/test_emlis_ai_structure_insight_p6_no_connect_regression_r8_20260612.py",
)

_FORBIDDEN_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
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
        "reviewer_free_text",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body",
        "text",
    }
)


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _safe_bool(value: Any) -> bool:
    return value is True


def _safe_identifier(value: Any, *, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _reason_codes(value: Any, *, limit: int = 12) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    reasons: list[str] = []
    for item in value:
        text = _safe_identifier(item)
        if text and text not in reasons:
            reasons.append(text[:120])
        if len(reasons) >= limit:
            break
    return reasons


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if str(raw_key) in _FORBIDDEN_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


def _test_group(group_id: str, files: Sequence[str], *, repository: str = "mashos-api/ai") -> dict[str, Any]:
    return {
        "group_id": group_id,
        "repository": repository,
        "command_kind": "pytest" if repository == "mashos-api/ai" else "npm",
        "working_directory": repository,
        "environment": {"PYTHONPATH": "services/ai_inference"} if repository == "mashos-api/ai" else {},
        "command": "PYTHONPATH=services/ai_inference pytest -q " + " ".join(files)
        if repository == "mashos-api/ai"
        else "npm run test:rn-screens --silent",
        "test_files": list(files),
        "green_claim_scope": "split_group_only",
        "full_backend_suite_green_claim_allowed": False,
        "timeout_hang_is_green": False,
        "body_free": True,
    }


def build_p5_p6_split_test_matrix() -> dict[str, Any]:
    """Return the R9 split matrix without executing tests or claiming full-suite green."""

    groups = [
        _test_group("r0_r8_targeted_runtime_repair", _R0_R8_TARGETED_TESTS),
        _test_group("p5_focused_runtime_and_boundary", _P5_FOCUSED_TESTS),
        _test_group("p6_focused_runtime_limited_surface_and_regression", _P6_FOCUSED_TESTS),
        _test_group("existing_runtime_public_regression", _RUNTIME_PUBLIC_REGRESSION_TESTS),
        _test_group("no_connect_safety_low_info_regression", _NO_CONNECT_SAFETY_TESTS),
        _test_group("rn_contract_external", (), repository="Cocolon"),
    ]
    return {
        "schema_version": P5_P6_SPLIT_TEST_MATRIX_SCHEMA_VERSION,
        "step": P5_P6_R9_REPAIR_STEP,
        "scope": "P5_P6_runtime_repair_only",
        "p7_out_of_scope": True,
        "split_matrix_fixed": True,
        "full_backend_suite_green_claim_allowed": False,
        "full_backend_timeout_hang_must_be_ledgered": True,
        "combined_pytest_timeout_is_not_green": True,
        "release_allowed": False,
        "groups": groups,
        "required_group_ids": [group["group_id"] for group in groups],
        "public_contract": {
            "public_response_key_added": False,
            "rn_visible_contract_changed": False,
            "api_route_changed": False,
            "db_schema_changed": False,
            "release_allowed": False,
        },
        "body_free": {
            "raw_input_included": False,
            "raw_text_included": False,
            "history_raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "reviewer_free_text_included": False,
            "terminal_output_included": False,
        },
    }


def build_p5_p6_handoff_lock(
    *,
    p5_runtime_bridge_summary: Mapping[str, Any] | None = None,
    p6_runtime_bridge_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the compact R9 handoff lock from P5/P6 runtime summaries."""

    p5 = _safe_mapping(p5_runtime_bridge_summary)
    p6 = _safe_mapping(p6_runtime_bridge_summary)
    p5_visible_applied = _safe_bool(p5.get("visible_applied")) or _safe_bool(p5.get("p5_visible_applied"))
    p5_product_quality_confirmed = _safe_bool(p5.get("product_quality_confirmed")) or _safe_bool(
        p5.get("p5_product_quality_confirmed")
    )
    p6_visible_applied = _safe_bool(p6.get("visible_applied")) or _safe_bool(p6.get("p6_visible_applied"))
    p6_visible_family = _safe_identifier(p6.get("visible_family"), default="none")
    if p6_visible_family not in {"structure_question", "none"}:
        p6_visible_family = "none"

    p5_visible_not_applied_reason_codes = _reason_codes(p5.get("blocked_reason_codes"))
    if not p5_visible_applied and not p5_visible_not_applied_reason_codes:
        p5_visible_not_applied_reason_codes = ["p5_visible_not_applied"]

    p6_visible_not_applied_reason_codes = _reason_codes(
        p6.get("p6_visible_not_applied_reason_codes") or p6.get("blocked_reason_codes")
    )
    if not p6_visible_applied and not p6_visible_not_applied_reason_codes:
        p6_visible_not_applied_reason_codes = ["p6_visible_not_applied"]

    no_connect_family_regression_green = bool(
        p6.get("r8_no_connect_regression") is True
        and p6.get("no_connect_family_visible_applied") is not True
        and p6.get("no_connect_family_preserved") is not False
    )
    matrix = build_p5_p6_split_test_matrix()
    summary = {
        "schema_version": P5_P6_HANDOFF_LOCK_SCHEMA_VERSION,
        "step": P5_P6_R9_REPAIR_STEP,
        "scope": "P5_P6_runtime_repair_only",
        "p7_out_of_scope": True,
        "p7_ready": False,
        "p7_ready_default_false": True,
        "release_allowed": False,
        "release_allowed_source": "never_from_p5_p6_r9_handoff",
        "split_test_matrix_id": P5_P6_SPLIT_TEST_MATRIX_SCHEMA_VERSION,
        "split_matrix_required": True,
        "required_split_group_ids": matrix["required_group_ids"],
        "full_backend_suite_green_claim_allowed": False,
        "full_backend_timeout_hang_must_be_ledgered": True,
        "combined_pytest_timeout_is_not_green": True,
        "p5_handoff": {
            "runtime_evaluated": _safe_bool(p5.get("runtime_evaluated")) or _safe_bool(p5.get("p5_runtime_evaluated")),
            "visible_applied": p5_visible_applied,
            "visible_not_applied_reason_codes": [] if p5_visible_applied else p5_visible_not_applied_reason_codes,
            "product_quality_confirmed": p5_product_quality_confirmed,
            "product_quality_unconfirmed_blocks_release": not p5_product_quality_confirmed,
            "human_qa_completed": _safe_bool(p5.get("human_qa_completed")),
            "release_allowed": False,
        },
        "p6_handoff": {
            "runtime_evaluated": _safe_bool(p6.get("runtime_evaluated")) or _safe_bool(p6.get("p6_runtime_evaluated")),
            "visible_applied": p6_visible_applied,
            "visible_family": p6_visible_family,
            "visible_only_for_structure_question": p6_visible_family in {"structure_question", "none"},
            "visible_not_applied_reason_codes": [] if p6_visible_applied else p6_visible_not_applied_reason_codes,
            "no_connect_family_regression_green": no_connect_family_regression_green,
            "product_quality_review_ratings_only": p6.get("p6_product_quality_review_ratings_only") is not False,
            "p7_ready": False,
            "release_allowed": False,
        },
        "public_contract": {
            "public_response_key_added": False,
            "rn_visible_contract_changed": False,
            "api_route_changed": False,
            "db_schema_changed": False,
            "release_allowed": False,
            "public_release_applied": False,
        },
        "body_free": {
            "raw_input_included": False,
            "raw_text_included": False,
            "history_raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "reviewer_free_text_included": False,
            "terminal_output_included": False,
        },
    }
    assert_p5_p6_handoff_lock_contract(summary)
    return summary


def assert_p5_p6_split_test_matrix_contract(matrix: Mapping[str, Any]) -> bool:
    data = _safe_mapping(matrix)
    if data.get("schema_version") != P5_P6_SPLIT_TEST_MATRIX_SCHEMA_VERSION:
        raise ValueError("unexpected P5/P6 split test matrix schema_version")
    if data.get("step") != P5_P6_R9_REPAIR_STEP:
        raise ValueError("unexpected P5/P6 split test matrix step")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("R9 matrix must not allow full backend suite green claims")
    if data.get("combined_pytest_timeout_is_not_green") is not True:
        raise ValueError("R9 matrix must ledger timeout/hang instead of treating it as green")
    groups = data.get("groups")
    if not isinstance(groups, list) or len(groups) < 5:
        raise ValueError("R9 matrix must define split groups")
    group_ids = {str(group.get("group_id") or "") for group in groups if isinstance(group, Mapping)}
    required = set(data.get("required_group_ids") or [])
    if not required or not required.issubset(group_ids):
        raise ValueError("R9 matrix required groups are missing")
    if data.get("release_allowed") is not False:
        raise ValueError("R9 matrix must not become release_allowed")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R9 matrix must not include body payload keys")
    return True


def assert_p5_p6_handoff_lock_contract(summary: Mapping[str, Any]) -> bool:
    data = _safe_mapping(summary)
    if data.get("schema_version") != P5_P6_HANDOFF_LOCK_SCHEMA_VERSION:
        raise ValueError("unexpected P5/P6 handoff lock schema_version")
    if data.get("step") != P5_P6_R9_REPAIR_STEP:
        raise ValueError("unexpected P5/P6 handoff lock step")
    if data.get("release_allowed") is not False or data.get("p7_ready") is not False:
        raise ValueError("R9 handoff must not allow release or mark P7 ready")
    if data.get("full_backend_suite_green_claim_allowed") is not False:
        raise ValueError("R9 handoff must not allow full backend suite green claims")
    if data.get("combined_pytest_timeout_is_not_green") is not True:
        raise ValueError("R9 handoff must ledger timeout/hang")
    p5 = _safe_mapping(data.get("p5_handoff"))
    p6 = _safe_mapping(data.get("p6_handoff"))
    if not p5 or not p6:
        raise ValueError("R9 handoff must contain P5 and P6 handoff summaries")
    if p5.get("release_allowed") is not False or p6.get("release_allowed") is not False:
        raise ValueError("P5/P6 handoff must not allow release")
    if p6.get("visible_family") not in {"structure_question", "none"}:
        raise ValueError("P6 visible handoff must remain structure_question-only or none")
    if _contains_forbidden_payload_key(data):
        raise ValueError("R9 handoff must not include body payload keys")
    body_free = _safe_mapping(data.get("body_free"))
    if any(value is True for value in body_free.values()):
        raise ValueError("R9 handoff body_free flags must remain false")
    return True
