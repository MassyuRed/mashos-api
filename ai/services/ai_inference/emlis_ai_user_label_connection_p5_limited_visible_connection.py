# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-6 limited visible connection for User Label Connection.

This boundary is the narrow bridge from the P5 ratings-only / body-free review
chain into the existing limited visible surface connector.  It may append the
safe history-line support section to the already-passed ``comment_text``, but it
does not add public response keys, change RN/API/DB contracts, or place visible
body text inside metadata.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Any, Callable, Final

from emlis_ai_user_label_connection_p5_eligibility_matrix import (
    DECISION_CONNECTABLE as P5_ELIGIBILITY_DECISION_CONNECTABLE,
    assert_user_label_connection_p5_eligibility_matrix_contract,
)
from emlis_ai_user_label_connection_p5_product_quality_review import (
    assert_user_label_connection_p5_product_quality_review_contract,
)
from emlis_ai_user_label_connection_p5_safety_guard import (
    DECISION_ALLOW as P5_SAFETY_DECISION_ALLOW,
    assert_user_label_connection_p5_safety_guard_contract,
)
from emlis_ai_user_label_connection_p5_surface_role_plan import (
    SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
    assert_user_label_connection_p5_surface_role_plan_contract,
)
from emlis_ai_user_label_connection_p5_visibility_boundary import (
    DECISION_ALLOW_LIMITED_VISIBLE,
    assert_user_label_connection_p5_visibility_boundary_contract,
)
from emlis_ai_user_label_connection_surface import (
    build_user_label_connection_limited_visible_surface_connection,
    user_label_connection_visible_surface_public_summary,
)


USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_limited_visible_connection.v1"
)
USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP: Final = "P5-6_LimitedVisibleConnection"
USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_LimitedVisibleConnection_20260611"
)
USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE: Final = "p5_6_internal_boundary_only"
USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID: Final = "P5-HOLD-001"
USER_LABEL_CONNECTION_P5_HUMAN_QA_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_human_qa_boundary.v1"
)

REASON_EXISTING_COMMENT_TEXT_MISSING: Final = "existing_comment_text_missing"
REASON_OBSERVATION_STATUS_NOT_PASSED: Final = "observation_status_not_passed"
REASON_EXISTING_GATE_REPORT_MISSING: Final = "existing_gate_report_missing"
REASON_EXISTING_GATE_BLOCKED: Final = "existing_gate_blocked"
REASON_P5_VISIBILITY_BOUNDARY_NOT_ALLOWED: Final = "p5_visibility_boundary_not_allowed"
REASON_P5_ELIGIBILITY_NOT_CONNECTABLE: Final = "p5_eligibility_not_connectable"
REASON_P5_SURFACE_ROLE_PLAN_NOT_READY: Final = "p5_surface_role_plan_not_ready"
REASON_P5_SAFETY_GUARD_NOT_ALLOWED: Final = "p5_safety_guard_not_allowed"
REASON_P5_PRODUCT_QUALITY_REVIEW_MISSING: Final = "p5_product_quality_review_missing"
REASON_P5_PRODUCT_QUALITY_REVIEW_NOT_ALLOWED: Final = "p5_product_quality_review_not_allowed"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
REASON_UPSTREAM_CONTRACT_INVALID: Final = "upstream_contract_invalid"
REASON_PHASE8_VISIBLE_CONNECTION_NOT_APPLIED: Final = "phase8_visible_connection_not_applied"
REASON_P5_POST_CONNECTION_GATE_BLOCKED: Final = "p5_post_connection_gate_blocked"

_SOURCE_SCOPE_OWNED_HISTORY: Final = "current_input_with_owned_history"

_REQUIRED_EXISTING_GATE_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "display_gate": ("tone_guard", "display_gate", "reader_gate", "reader"),
    "grounding": ("grounding", "grounding_gate", "grounding_report"),
    "template_echo": ("template_echo", "template_gate", "template_echo_report"),
    "safety": ("safety", "safety_gate", "safety_report"),
    "runtime_surface_pre_return_gate": ("runtime_surface_pre_return_gate", "runtime_surface_gate"),
    "visible_surface_acceptance_gate": ("visible_surface_acceptance_gate", "visible_surface_gate"),
}
_PHASE8_GATE_NAMES: Final[tuple[str, ...]] = (
    "tone_guard",
    "grounding",
    "visible_surface_acceptance_gate",
    "runtime_surface_pre_return_gate",
)

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
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
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
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
        "observation_text",
        "reception_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_free_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "external_ai_used",
        "local_llm_used",
    }
)


@dataclass(frozen=True)
class UserLabelConnectionP5LimitedVisibleConnection:
    comment_text: str
    applied: bool
    meta: dict[str, Any]

    def as_meta(self) -> dict[str, Any]:
        return dict(self.meta)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return {str(key): item for key, item in meta.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _contract_invalid(
    name: str,
    value: Mapping[str, Any],
    checker: Callable[..., None],
) -> list[str]:
    if not value:
        return []
    try:
        checker(value, allow_partial=True)
    except (TypeError, ValueError):
        return [f"{REASON_UPSTREAM_CONTRACT_INVALID}:{name}"]
    return []


def _gate_passed(report: Any) -> bool:
    if isinstance(report, bool):
        return report is True
    meta = _safe_mapping(report)
    if not meta:
        return False
    if meta.get("blocked") is True or meta.get("passed") is False:
        return False
    if meta.get("passed") is True or meta.get("safe") is True:
        return True
    action = _clean(meta.get("action")).lower()
    classification = _clean(meta.get("classification")).lower()
    status = _clean(meta.get("status")).lower()
    if action in {"allow", "pass", "passed", "accept", "ok"}:
        return True
    if classification in {"green", "safe", "accepted", "passed", "pass", "ok"}:
        return True
    if status in {"passed", "pass", "ok", "accepted", "safe"}:
        return True
    return False


def _primary_reason(report: Any, fallback: str) -> str:
    meta = _safe_mapping(report)
    reason = _clean(meta.get("primary_reason") or meta.get("reason") or meta.get("blocker_reason"))
    if reason:
        return reason
    reasons = _dedupe(meta.get("rejection_reasons") or meta.get("blocker_reason_codes"))
    return reasons[0] if reasons else fallback


def _resolve_gate_report(reports: Mapping[str, Any], aliases: Sequence[str]) -> tuple[str, Any]:
    for alias in aliases:
        if alias in reports:
            return alias, reports[alias]
    return "", None


def _existing_gate_summary(existing_gate_reports: Mapping[str, Any] | None) -> tuple[bool, dict[str, dict[str, Any]], list[str]]:
    reports = _safe_mapping(existing_gate_reports)
    summary: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for gate_name, aliases in _REQUIRED_EXISTING_GATE_ALIASES.items():
        matched_name, report = _resolve_gate_report(reports, aliases)
        if not matched_name:
            summary[gate_name] = {"passed": False, "source_gate": "", "primary_reason": REASON_EXISTING_GATE_REPORT_MISSING}
            reasons.append(f"{REASON_EXISTING_GATE_REPORT_MISSING}:{gate_name}")
            continue
        passed = _gate_passed(report)
        primary = "" if passed else _primary_reason(report, f"{REASON_EXISTING_GATE_BLOCKED}:{gate_name}")
        summary[gate_name] = {
            "passed": passed,
            "source_gate": matched_name,
            "primary_reason": primary or None,
        }
        if not passed:
            reasons.append(primary or f"{REASON_EXISTING_GATE_BLOCKED}:{gate_name}")
    return not reasons, summary, _dedupe(reasons)


def _phase8_gate_reports(gate_summary: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        "tone_guard": dict(gate_summary.get("display_gate") or {"passed": False}),
        "grounding": dict(gate_summary.get("grounding") or {"passed": False}),
        "visible_surface_acceptance_gate": dict(gate_summary.get("visible_surface_acceptance_gate") or {"passed": False}),
        "runtime_surface_pre_return_gate": dict(gate_summary.get("runtime_surface_pre_return_gate") or {"passed": False}),
    }


def _p5_surface_plan_for_phase8(
    *,
    p5_surface_role_plan: Mapping[str, Any],
    p5_eligibility_matrix: Mapping[str, Any],
) -> dict[str, Any]:
    plan = _safe_mapping(p5_surface_role_plan)
    matrix = _safe_mapping(p5_eligibility_matrix)
    eligibility = _safe_mapping(matrix.get("eligibility"))
    role_plan_ready = plan.get("role_plan_ready") is True
    evidence_record_count = _int(eligibility.get("evidence_record_count"))
    history_record_count = _int(eligibility.get("history_record_count"))
    return {
        "schema_version": _clean(plan.get("schema_version")),
        "surface_plan_kind": _clean(plan.get("surface_plan_kind")),
        "connectable_family": _clean(plan.get("connectable_family")),
        "candidate_id": _clean(plan.get("candidate_id")),
        "history_connection_surface_plan_allowed": role_plan_ready,
        "limited_history_line_observation_ready": role_plan_ready,
        "must_include_roles": _dedupe(plan.get("must_include_roles")),
        "evidence_contract": {
            "evidence_record_count": evidence_record_count,
            "minimum_evidence_record_count": _int(eligibility.get("minimum_evidence_record_count"), 2) or 2,
            "current_record_included": eligibility.get("current_record_included") is True,
            "history_record_count": history_record_count,
            "source_scope": _clean(eligibility.get("source_scope")) or _SOURCE_SCOPE_OWNED_HISTORY,
        },
    }


def _product_quality_allowed(review: Mapping[str, Any]) -> bool:
    if not review:
        return False
    if review.get("ratings_only") is not True:
        return False
    blockers = _dedupe(review.get("blocker_reason_codes"))
    return review.get("p5_limited_visible_allowed") is True or not blockers


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "comment_text_body_in_meta_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
    }


def _p5_human_qa_boundary(
    *,
    applied: bool,
    p5_product_quality_review: Mapping[str, Any] | None,
) -> dict[str, Any]:
    review = _safe_mapping(p5_product_quality_review)
    review_count = _int(review.get("review_count"))
    blocker_reason_codes = _dedupe(review.get("blocker_reason_codes"))
    review_rows_present = review_count > 0
    ratings_only = review.get("ratings_only") is True
    confirmed = bool(
        review_rows_present
        and ratings_only
        and review.get("p5_limited_visible_allowed") is True
        and not blocker_reason_codes
    )
    if confirmed:
        qa_status = "confirmed_by_human_blind_qa"
    elif review_rows_present:
        qa_status = "reviewed_but_not_confirmed"
    else:
        qa_status = "not_started_or_missing"

    hold_reason_codes: list[str] = []
    if not confirmed:
        hold_reason_codes.append("p5_human_qa_not_confirmed")
        if not review_rows_present:
            hold_reason_codes.append("p5_human_qa_review_rows_missing")
        hold_reason_codes.extend(blocker_reason_codes)
    hold_reason_codes = _dedupe(hold_reason_codes)

    return {
        "schema_version": USER_LABEL_CONNECTION_P5_HUMAN_QA_BOUNDARY_SCHEMA_VERSION,
        "hold_id": USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID,
        "human_qa_required": True,
        "human_qa_status": qa_status,
        "human_qa_review_rows_present": review_rows_present,
        "human_qa_review_count": review_count,
        "human_qa_complete": confirmed,
        "human_qa_confirmed": confirmed,
        "human_blind_qa_confirmed": confirmed,
        "human_qa_not_substituted_by_runtime": True,
        "human_qa_not_substituted_by_visible_connection": True,
        "runtime_evaluated": True,
        "visible_applied": bool(applied),
        "product_quality_confirmed": confirmed,
        "product_quality_confirmed_by": "human_blind_qa_ratings" if confirmed else "not_confirmed",
        "product_quality_complete_claim_allowed": False,
        "p5_completion_claim_allowed": False,
        "live_runtime_review_rows_synthesized": False,
        "machine_metrics_used_as_human_qa": False,
        "reviewer_free_text_included": False,
        "public_meta_summary_only": True,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
        "hold_reason_codes": hold_reason_codes,
    }


def _p5_public_meta_boundary(*, applied: bool, product_quality_confirmed: bool) -> dict[str, Any]:
    return {
        "safe_summary_only": True,
        "input_feedback_comment_text_only_visible_body": True,
        "public_response_top_level_key_added": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_schema_changed": False,
        "runtime_evaluated": True,
        "visible_applied": bool(applied),
        "product_quality_confirmed": bool(product_quality_confirmed),
        "human_qa_required_for_product_quality": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "history_raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "actual_appended_line_included": False,
        "release_allowed": False,
    }


def _p5_completion_layers(*, applied: bool, human_qa_boundary: Mapping[str, Any]) -> dict[str, Any]:
    product_quality_confirmed = human_qa_boundary.get("product_quality_confirmed") is True
    return {
        "runtime_evaluated": {
            "status": "evaluated",
            "complete": True,
            "body_free": True,
        },
        "visible_applied": {
            "status": "applied" if applied else "not_applied",
            "complete": bool(applied),
            "comment_text_owner": "input_feedback.comment_text",
        },
        "human_qa_product_quality": {
            "status": str(human_qa_boundary.get("human_qa_status") or "not_started_or_missing"),
            "complete": product_quality_confirmed,
            "hold_id": USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID,
            "not_substituted_by_runtime": True,
            "not_substituted_by_visible_connection": True,
        },
    }


def _meta(
    *,
    run_id: str,
    applied: bool,
    base_text_present: bool,
    observation_status: str,
    gate_summary: Mapping[str, Mapping[str, Any]],
    gate_reports_passed: bool,
    p5_visibility_allowed: bool,
    p5_eligibility_connectable: bool,
    p5_surface_role_plan_ready: bool,
    p5_safety_guard_allowed: bool,
    p5_product_quality_allowed: bool,
    rejection_reasons: Sequence[Any],
    phase8_meta: Mapping[str, Any] | None = None,
    p5_product_quality_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    safe_phase8_meta = _safe_mapping(phase8_meta)
    human_qa_boundary = _p5_human_qa_boundary(
        applied=applied,
        p5_product_quality_review=p5_product_quality_review,
    )
    product_quality_confirmed = human_qa_boundary.get("product_quality_confirmed") is True
    meta = {
        "schema_version": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP,
        "source": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SOURCE,
        "run_id": run_id,
        "evaluated": True,
        "applied": bool(applied),
        "limited_visible_connection_applied": bool(applied),
        "p5_limited_visible_allowed": bool(applied),
        "history_connection_applied": bool(applied),
        "history_line_surface_connected": bool(applied),
        "visible_surface_connected": bool(applied),
        "runtime_surface_connected": bool(applied),
        "comment_text_connected": bool(applied),
        "existing_comment_text_present": bool(base_text_present),
        "observation_status": observation_status,
        "observation_status_passed": observation_status == "passed",
        "existing_gate_reports_passed": bool(gate_reports_passed),
        "existing_gate_reports": {key: dict(value) for key, value in gate_summary.items()},
        "p5_visibility_boundary_allowed": bool(p5_visibility_allowed),
        "p5_eligibility_connectable": bool(p5_eligibility_connectable),
        "p5_surface_role_plan_ready": bool(p5_surface_role_plan_ready),
        "p5_safety_guard_allowed": bool(p5_safety_guard_allowed),
        "p5_product_quality_allowed": bool(p5_product_quality_allowed),
        "p5_runtime_evaluated": True,
        "runtime_evaluated": True,
        "p5_visible_applied": bool(applied),
        "visible_applied": bool(applied),
        "p5_product_quality_confirmed": product_quality_confirmed,
        "product_quality_confirmed": product_quality_confirmed,
        "p5_human_blind_qa_confirmed": product_quality_confirmed,
        "human_blind_qa_confirmed": product_quality_confirmed,
        "p5_human_qa_status": str(human_qa_boundary.get("human_qa_status") or "not_started_or_missing"),
        "human_qa_status": str(human_qa_boundary.get("human_qa_status") or "not_started_or_missing"),
        "p5_human_qa_boundary": human_qa_boundary,
        "human_qa_boundary": human_qa_boundary,
        "p5_public_meta_boundary": _p5_public_meta_boundary(
            applied=applied,
            product_quality_confirmed=product_quality_confirmed,
        ),
        "p5_completion_layers": _p5_completion_layers(
            applied=applied,
            human_qa_boundary=human_qa_boundary,
        ),
        "product_quality_complete_claim_allowed": False,
        "p5_completion_claim_allowed": False,
        "human_qa_not_substituted_by_runtime": True,
        "human_qa_not_substituted_by_visible_connection": True,
        "visible_connection_route": "p5_6_boundary_internal_phase8_connector",
        "p5_6_boundary_enforced": True,
        "phase8_connector_scope": USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE,
        "phase8_connector_used_as_internal_detail": bool(safe_phase8_meta),
        "phase8_direct_reply_service_call_allowed": False,
        "phase8_direct_visible_connection_from_reply_service": False,
        "old_phase8_direct_visible_connection_replaced_by_p5_6_boundary": True,
        "legacy_phase8_direct_call_used": False,
        "phase8_connector_called_inside_p5_6_boundary": bool(safe_phase8_meta),
        "post_connection_regate_required": True,
        "post_connection_gate_passed": bool(applied),
        "p5_red_002_closed_by_route": True,
        "phase8_visible_surface_connection": user_label_connection_visible_surface_public_summary(safe_phase8_meta)
        if safe_phase8_meta
        else {},
        "visible_connection_owner": "p5_6_limited_visible_connection_boundary",
        "legacy_phase8_connector_scope": "p5_6_internal_boundary_only",
        "reply_service_direct_phase8_call_allowed": False,
        "phase8_connector_internal_to_p5_6_boundary": True,
        "connection_shape": {
            "existing_comment_text_primary": True,
            "history_line_support_section": bool(applied),
            "current_input_not_masked_by_history": True,
            "input_feedback_comment_text_only_visible_body": True,
            "user_label_connection_meta_safe_summary_only": True,
        },
        "comment_text_visible_body_owner": "input_feedback.comment_text",
        "input_feedback_user_label_connection_meta_kind": "safe_summary_only",
        "public_meta_summary_only": True,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "rejection_reasons": _dedupe(rejection_reasons),
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_user_label_connection_p5_limited_visible_connection_contract(meta)
    return meta


def _blocked_result(
    *,
    existing_comment_text: str,
    run_id: str,
    base_text_present: bool,
    observation_status: str,
    gate_summary: Mapping[str, Mapping[str, Any]],
    gate_reports_passed: bool,
    p5_visibility_allowed: bool,
    p5_eligibility_connectable: bool,
    p5_surface_role_plan_ready: bool,
    p5_safety_guard_allowed: bool,
    p5_product_quality_allowed: bool,
    rejection_reasons: Sequence[Any],
    phase8_meta: Mapping[str, Any] | None = None,
    p5_product_quality_review: Mapping[str, Any] | None = None,
) -> UserLabelConnectionP5LimitedVisibleConnection:
    meta = _meta(
        run_id=run_id,
        applied=False,
        base_text_present=base_text_present,
        observation_status=observation_status,
        gate_summary=gate_summary,
        gate_reports_passed=gate_reports_passed,
        p5_visibility_allowed=p5_visibility_allowed,
        p5_eligibility_connectable=p5_eligibility_connectable,
        p5_surface_role_plan_ready=p5_surface_role_plan_ready,
        p5_safety_guard_allowed=p5_safety_guard_allowed,
        p5_product_quality_allowed=p5_product_quality_allowed,
        rejection_reasons=rejection_reasons,
        phase8_meta=phase8_meta,
        p5_product_quality_review=p5_product_quality_review,
    )
    return UserLabelConnectionP5LimitedVisibleConnection(comment_text=existing_comment_text, applied=False, meta=meta)


def build_user_label_connection_p5_limited_visible_connection(
    existing_comment_text: Any,
    *,
    observation_status: Any = "",
    p5_visibility_boundary: Mapping[str, Any] | None = None,
    p5_eligibility_matrix: Mapping[str, Any] | None = None,
    p5_surface_role_plan: Mapping[str, Any] | None = None,
    p5_safety_guard: Mapping[str, Any] | None = None,
    p5_product_quality_review: Mapping[str, Any] | None = None,
    existing_gate_reports: Mapping[str, Any] | None = None,
    safety_context: Any = "",
    run_id: str | None = None,
) -> UserLabelConnectionP5LimitedVisibleConnection:
    """Apply P5 limited visible connection only after P5-1 through P5-5 pass."""

    base_text = _clean(existing_comment_text)
    status = _clean(observation_status).lower()
    visibility = _safe_mapping(p5_visibility_boundary)
    eligibility = _safe_mapping(p5_eligibility_matrix)
    role_plan = _safe_mapping(p5_surface_role_plan)
    guard = _safe_mapping(p5_safety_guard)
    review = _safe_mapping(p5_product_quality_review)
    sources = [visibility, eligibility, role_plan, guard, review, _safe_mapping(existing_gate_reports)]

    gate_reports_passed, gate_summary, gate_reasons = _existing_gate_summary(existing_gate_reports)
    p5_visibility_allowed = visibility.get("decision") == DECISION_ALLOW_LIMITED_VISIBLE and visibility.get("allow_limited_visible") is True
    p5_eligibility_connectable = eligibility.get("decision") == P5_ELIGIBILITY_DECISION_CONNECTABLE and eligibility.get("connectable") is True
    p5_surface_role_plan_ready = (
        role_plan.get("role_plan_ready") is True
        and role_plan.get("surface_plan_kind") == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    )
    p5_safety_guard_allowed = (
        guard.get("decision") == P5_SAFETY_DECISION_ALLOW and guard.get("allow_limited_visible_candidate") is True
    )
    p5_product_quality_allowed = _product_quality_allowed(review)

    reasons: list[str] = []
    if any(_contains_text_payload_key(source) for source in sources):
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if any(_flag_true(source) for source in sources):
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    reasons.extend(_contract_invalid("p5_visibility_boundary", visibility, assert_user_label_connection_p5_visibility_boundary_contract))
    reasons.extend(_contract_invalid("p5_eligibility_matrix", eligibility, assert_user_label_connection_p5_eligibility_matrix_contract))
    reasons.extend(_contract_invalid("p5_surface_role_plan", role_plan, assert_user_label_connection_p5_surface_role_plan_contract))
    reasons.extend(_contract_invalid("p5_safety_guard", guard, assert_user_label_connection_p5_safety_guard_contract))
    reasons.extend(_contract_invalid("p5_product_quality_review", review, assert_user_label_connection_p5_product_quality_review_contract))

    if not base_text:
        reasons.append(REASON_EXISTING_COMMENT_TEXT_MISSING)
    if status != "passed":
        reasons.append(REASON_OBSERVATION_STATUS_NOT_PASSED)
    if not gate_reports_passed:
        reasons.extend(gate_reasons)
    if not p5_visibility_allowed:
        reasons.append(REASON_P5_VISIBILITY_BOUNDARY_NOT_ALLOWED)
        reasons.extend(f"p5_visibility:{reason}" for reason in _dedupe(visibility.get("rejection_reasons")))
    if not p5_eligibility_connectable:
        reasons.append(REASON_P5_ELIGIBILITY_NOT_CONNECTABLE)
        reasons.extend(f"p5_eligibility:{reason}" for reason in _dedupe(eligibility.get("rejection_reasons")))
    if not p5_surface_role_plan_ready:
        reasons.append(REASON_P5_SURFACE_ROLE_PLAN_NOT_READY)
        reasons.extend(f"p5_surface_role_plan:{reason}" for reason in _dedupe(role_plan.get("rejection_reasons")))
    if not p5_safety_guard_allowed:
        reasons.append(REASON_P5_SAFETY_GUARD_NOT_ALLOWED)
        reasons.extend(f"p5_safety_guard:{reason}" for reason in _dedupe(guard.get("rejection_reasons")))
    if not review:
        reasons.append(REASON_P5_PRODUCT_QUALITY_REVIEW_MISSING)
    elif not p5_product_quality_allowed:
        reasons.append(REASON_P5_PRODUCT_QUALITY_REVIEW_NOT_ALLOWED)
        reasons.extend(f"p5_product_quality:{reason}" for reason in _dedupe(review.get("blocker_reason_codes")))
    reasons = _dedupe(reasons)

    run = run_id or "p5_limited_visible_connection"
    if reasons:
        return _blocked_result(
            existing_comment_text=base_text,
            run_id=run,
            base_text_present=bool(base_text),
            observation_status=status,
            gate_summary=gate_summary,
            gate_reports_passed=gate_reports_passed,
            p5_visibility_allowed=p5_visibility_allowed,
            p5_eligibility_connectable=p5_eligibility_connectable,
            p5_surface_role_plan_ready=p5_surface_role_plan_ready,
            p5_safety_guard_allowed=p5_safety_guard_allowed,
            p5_product_quality_allowed=p5_product_quality_allowed,
            rejection_reasons=reasons,
            p5_product_quality_review=review,
        )

    phase8_plan = _p5_surface_plan_for_phase8(
        p5_surface_role_plan=role_plan,
        p5_eligibility_matrix=eligibility,
    )
    phase8_result = build_user_label_connection_limited_visible_surface_connection(
        base_text,
        phase8_plan,
        existing_gate_reports=_phase8_gate_reports(gate_summary),
        safety_context=safety_context,
    )
    phase8_meta = phase8_result.as_meta()
    if not phase8_result.applied:
        return _blocked_result(
            existing_comment_text=base_text,
            run_id=run,
            base_text_present=True,
            observation_status=status,
            gate_summary=gate_summary,
            gate_reports_passed=gate_reports_passed,
            p5_visibility_allowed=p5_visibility_allowed,
            p5_eligibility_connectable=p5_eligibility_connectable,
            p5_surface_role_plan_ready=p5_surface_role_plan_ready,
            p5_safety_guard_allowed=p5_safety_guard_allowed,
            p5_product_quality_allowed=p5_product_quality_allowed,
            rejection_reasons=[REASON_PHASE8_VISIBLE_CONNECTION_NOT_APPLIED, *phase8_meta.get("rejection_reasons", [])],
            phase8_meta=phase8_meta,
            p5_product_quality_review=review,
        )

    meta = _meta(
        run_id=run,
        applied=True,
        base_text_present=True,
        observation_status=status,
        gate_summary=gate_summary,
        gate_reports_passed=gate_reports_passed,
        p5_visibility_allowed=p5_visibility_allowed,
        p5_eligibility_connectable=p5_eligibility_connectable,
        p5_surface_role_plan_ready=p5_surface_role_plan_ready,
        p5_safety_guard_allowed=p5_safety_guard_allowed,
        p5_product_quality_allowed=p5_product_quality_allowed,
        rejection_reasons=[],
        phase8_meta=phase8_meta,
        p5_product_quality_review=review,
    )
    return UserLabelConnectionP5LimitedVisibleConnection(
        comment_text=phase8_result.comment_text,
        applied=True,
        meta=meta,
    )


def user_label_connection_p5_limited_visible_connection_public_summary(
    value: Mapping[str, Any] | UserLabelConnectionP5LimitedVisibleConnection | None,
) -> dict[str, Any]:
    meta = _safe_mapping(value)
    if not meta:
        return {}
    if _contains_text_payload_key(meta) or _flag_true(meta):
        return {
            "schema_version": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION,
            "step": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP,
            "evaluated": True,
            "applied": False,
            "limited_visible_connection_applied": False,
            "rejection_reasons": ["p5_limited_visible_connection_public_meta_unsafe"],
            "public_meta_summary_only": True,
            "public_response_key_added": False,
            "response_shape_changed": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "history_raw_text_included": False,
            "p5_runtime_evaluated": True,
            "runtime_evaluated": True,
            "p5_visible_applied": False,
            "visible_applied": False,
            "p5_product_quality_confirmed": False,
            "product_quality_confirmed": False,
            "p5_human_blind_qa_confirmed": False,
            "human_blind_qa_confirmed": False,
            "human_qa_status": "not_started_or_missing",
            "product_quality_complete_claim_allowed": False,
            "p5_completion_claim_allowed": False,
            "release_allowed": False,
        }
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP,
        "evaluated": meta.get("evaluated") is True,
        "applied": meta.get("applied") is True,
        "limited_visible_connection_applied": meta.get("limited_visible_connection_applied") is True,
        "history_connection_applied": meta.get("history_connection_applied") is True,
        "history_line_surface_connected": meta.get("history_line_surface_connected") is True,
        "visible_surface_connected": meta.get("visible_surface_connected") is True,
        "runtime_surface_connected": meta.get("runtime_surface_connected") is True,
        "comment_text_connected": meta.get("comment_text_connected") is True,
        "p5_visibility_boundary_allowed": meta.get("p5_visibility_boundary_allowed") is True,
        "p5_eligibility_connectable": meta.get("p5_eligibility_connectable") is True,
        "p5_surface_role_plan_ready": meta.get("p5_surface_role_plan_ready") is True,
        "p5_safety_guard_allowed": meta.get("p5_safety_guard_allowed") is True,
        "p5_product_quality_allowed": meta.get("p5_product_quality_allowed") is True,
        "p5_runtime_evaluated": meta.get("runtime_evaluated") is True or meta.get("p5_runtime_evaluated") is True,
        "runtime_evaluated": meta.get("runtime_evaluated") is True or meta.get("p5_runtime_evaluated") is True,
        "p5_visible_applied": meta.get("visible_applied") is True or meta.get("p5_visible_applied") is True,
        "visible_applied": meta.get("visible_applied") is True or meta.get("p5_visible_applied") is True,
        "p5_product_quality_confirmed": meta.get("product_quality_confirmed") is True or meta.get("p5_product_quality_confirmed") is True,
        "product_quality_confirmed": meta.get("product_quality_confirmed") is True or meta.get("p5_product_quality_confirmed") is True,
        "p5_human_blind_qa_confirmed": meta.get("human_blind_qa_confirmed") is True or meta.get("p5_human_blind_qa_confirmed") is True,
        "human_blind_qa_confirmed": meta.get("human_blind_qa_confirmed") is True or meta.get("p5_human_blind_qa_confirmed") is True,
        "p5_human_qa_status": _clean(meta.get("p5_human_qa_status") or meta.get("human_qa_status")),
        "human_qa_status": _clean(meta.get("p5_human_qa_status") or meta.get("human_qa_status")),
        "p5_human_qa_boundary": dict(_safe_mapping(meta.get("p5_human_qa_boundary") or meta.get("human_qa_boundary"))),
        "human_qa_boundary": dict(_safe_mapping(meta.get("p5_human_qa_boundary") or meta.get("human_qa_boundary"))),
        "p5_public_meta_boundary": dict(_safe_mapping(meta.get("p5_public_meta_boundary"))),
        "p5_completion_layers": dict(_safe_mapping(meta.get("p5_completion_layers"))),
        "product_quality_complete_claim_allowed": False,
        "p5_completion_claim_allowed": False,
        "human_qa_not_substituted_by_runtime": meta.get("human_qa_not_substituted_by_runtime") is True,
        "human_qa_not_substituted_by_visible_connection": meta.get("human_qa_not_substituted_by_visible_connection") is True,
        "p5_6_boundary_enforced": meta.get("p5_6_boundary_enforced") is True,
        "phase8_connector_scope": _clean(meta.get("phase8_connector_scope")),
        "phase8_connector_used_as_internal_detail": meta.get("phase8_connector_used_as_internal_detail") is True,
        "phase8_direct_reply_service_call_allowed": False,
        "phase8_direct_visible_connection_from_reply_service": False,
        "old_phase8_direct_visible_connection_replaced_by_p5_6_boundary": meta.get("old_phase8_direct_visible_connection_replaced_by_p5_6_boundary") is True,
        "existing_gate_reports_passed": meta.get("existing_gate_reports_passed") is True,
        "visible_connection_owner": _clean(meta.get("visible_connection_owner")),
        "legacy_phase8_connector_scope": _clean(meta.get("legacy_phase8_connector_scope")) or "p5_6_internal_boundary_only",
        "reply_service_direct_phase8_call_allowed": False,
        "phase8_connector_internal_to_p5_6_boundary": meta.get("phase8_connector_internal_to_p5_6_boundary") is True,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
        "release_allowed": False,
        "visible_connection_route": _clean(meta.get("visible_connection_route"))
        or "p5_6_boundary_internal_phase8_connector",
        "phase8_connector_scope": _clean(meta.get("phase8_connector_scope")) or USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE,
        "legacy_phase8_direct_call_used": False,
        "phase8_connector_called_inside_p5_6_boundary": meta.get("phase8_connector_called_inside_p5_6_boundary") is True,
        "post_connection_regate_required": True,
        "post_connection_gate_passed": meta.get("post_connection_gate_passed") is True,
        "p5_red_002_closed_by_route": True,
    }
    assert_user_label_connection_p5_limited_visible_connection_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_limited_visible_connection_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if _contains_text_payload_key(meta):
        raise ValueError("P5 limited visible connection meta must not include raw/comment/surface body keys")
    if _flag_true(meta):
        raise ValueError("P5 limited visible connection meta contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not meta:
        raise ValueError("P5 limited visible connection meta must be a mapping")
    if meta.get("schema_version") != USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION:
        raise ValueError("unexpected P5 limited visible connection schema_version")
    if meta.get("step") != USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP:
        raise ValueError("unexpected P5 limited visible connection step")
    public_contract = _safe_mapping(meta.get("public_contract"))
    body_free = _safe_mapping(meta.get("body_free"))
    for key in (
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "public_response_key_added",
        "response_shape_changed",
        "api_route_changed",
        "request_key_changed",
        "db_schema_changed",
        "fixed_sentence_template_added",
        "release_allowed",
        "public_release_applied",
        "product_quality_released",
    ):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 limited visible public_contract.{key} must be false")
    for key in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "comment_text_body_in_meta_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
    ):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 limited visible body_free.{key} must be false")
    if meta.get("p5_6_boundary_enforced") is not True:
        raise ValueError("P5 limited visible connection requires p5_6_boundary_enforced=true")
    if meta.get("phase8_connector_scope") != USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE:
        raise ValueError("P5 limited visible connection requires phase8 connector to be internal to P5-6")
    if meta.get("phase8_direct_reply_service_call_allowed") is not False:
        raise ValueError("P5 limited visible connection must not allow Phase8 direct reply_service calls")
    if meta.get("phase8_direct_visible_connection_from_reply_service") is not False:
        raise ValueError("P5 limited visible connection must prove no Phase8 direct visible reply_service connection")
    applied = meta.get("applied") is True
    for key in (
        "limited_visible_connection_applied",
        "history_connection_applied",
        "history_line_surface_connected",
        "visible_surface_connected",
        "runtime_surface_connected",
        "comment_text_connected",
    ):
        if meta.get(key) is not applied:
            raise ValueError(f"P5 limited visible meta requires {key}=applied")
    if applied:
        for key in (
            "existing_comment_text_present",
            "observation_status_passed",
            "existing_gate_reports_passed",
            "p5_visibility_boundary_allowed",
            "p5_eligibility_connectable",
            "p5_surface_role_plan_ready",
            "p5_safety_guard_allowed",
            "p5_product_quality_allowed",
        ):
            if meta.get(key) is not True:
                raise ValueError(f"P5 limited visible applied meta requires {key}=true")
        if _dedupe(meta.get("rejection_reasons")):
            raise ValueError("P5 limited visible applied meta must not have rejection reasons")
    human_qa = _safe_mapping(meta.get("p5_human_qa_boundary") or meta.get("human_qa_boundary"))
    if human_qa:
        if human_qa.get("hold_id") != USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID:
            raise ValueError("P5 human QA boundary must keep P5-HOLD-001 as separate hold evidence")
        if human_qa.get("human_qa_required") is not True:
            raise ValueError("P5 human QA boundary must mark human_qa_required=true")
        if human_qa.get("human_qa_not_substituted_by_runtime") is not True:
            raise ValueError("P5 human QA must not be substituted by runtime evaluation")
        if human_qa.get("human_qa_not_substituted_by_visible_connection") is not True:
            raise ValueError("P5 human QA must not be substituted by visible connection")
        if human_qa.get("product_quality_confirmed") is True and human_qa.get("human_qa_complete") is not True:
            raise ValueError("P5 product quality confirmation requires completed human QA")
        if human_qa.get("product_quality_complete_claim_allowed") is not False:
            raise ValueError("P5 human QA boundary must not claim product quality complete from runtime meta")
        if human_qa.get("p5_completion_claim_allowed") is not False:
            raise ValueError("P5 human QA boundary must not claim P5 completion from runtime meta")
    public_meta_boundary = _safe_mapping(meta.get("p5_public_meta_boundary"))
    if public_meta_boundary:
        if public_meta_boundary.get("safe_summary_only") is not True:
            raise ValueError("P5 public meta boundary must be safe summary only")
        for key in (
            "public_response_top_level_key_added",
            "public_response_key_added",
            "rn_visible_contract_changed",
            "api_route_changed",
            "request_key_changed",
            "db_schema_changed",
            "raw_input_included",
            "raw_text_included",
            "history_raw_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "reviewer_free_text_included",
            "actual_appended_line_included",
            "release_allowed",
        ):
            if public_meta_boundary.get(key) is not False:
                raise ValueError(f"P5 public meta boundary requires {key}=false")
    if meta.get("product_quality_complete_claim_allowed") is not False:
        raise ValueError("P5 limited visible connection must not claim product-quality completion")
    if meta.get("p5_completion_claim_allowed") is not False:
        raise ValueError("P5 limited visible connection must not claim P5 completion")
    if meta.get("release_allowed") is not False or meta.get("public_release_applied") is not False:
        raise ValueError("P5 limited visible connection must not convert QA pass to release")
    if not allow_partial:
        if meta.get("visible_connection_route") != "p5_6_boundary_internal_phase8_connector":
            raise ValueError("P5 visible connection must be routed through the P5-6 boundary")
        if meta.get("phase8_connector_scope") != USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE:
            raise ValueError("Phase8 connector must be scoped to the P5-6 internal boundary")
        if meta.get("legacy_phase8_direct_call_used") is not False:
            raise ValueError("P5 limited visible connection must not mark legacy Phase8 direct call usage")
        if meta.get("post_connection_regate_required") is not True:
            raise ValueError("P5 limited visible connection must require post-connection regate")


__all__ = [
    "USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP",
    "USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SOURCE",
    "USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE",
    "USER_LABEL_CONNECTION_P5_HUMAN_QA_HOLD_ID",
    "USER_LABEL_CONNECTION_P5_HUMAN_QA_BOUNDARY_SCHEMA_VERSION",
    "REASON_P5_POST_CONNECTION_GATE_BLOCKED",
    "UserLabelConnectionP5LimitedVisibleConnection",
    "build_user_label_connection_p5_limited_visible_connection",
    "user_label_connection_p5_limited_visible_connection_public_summary",
    "assert_user_label_connection_p5_limited_visible_connection_contract",
]
