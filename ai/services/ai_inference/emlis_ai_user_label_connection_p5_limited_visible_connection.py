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
) -> dict[str, Any]:
    safe_phase8_meta = _safe_mapping(phase8_meta)
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
        "phase8_visible_surface_connection": user_label_connection_visible_surface_public_summary(safe_phase8_meta)
        if safe_phase8_meta
        else {},
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
        "existing_gate_reports_passed": meta.get("existing_gate_reports_passed") is True,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
        "release_allowed": False,
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
    if meta.get("release_allowed") is not False or meta.get("public_release_applied") is not False:
        raise ValueError("P5 limited visible connection must not convert QA pass to release")


__all__ = [
    "USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_STEP",
    "USER_LABEL_CONNECTION_P5_LIMITED_VISIBLE_CONNECTION_SOURCE",
    "UserLabelConnectionP5LimitedVisibleConnection",
    "build_user_label_connection_p5_limited_visible_connection",
    "user_label_connection_p5_limited_visible_connection_public_summary",
    "assert_user_label_connection_p5_limited_visible_connection_contract",
]
