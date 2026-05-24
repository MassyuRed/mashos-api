# -*- coding: utf-8 -*-
"""Public EmlisAI input-feedback meta boundary.

This module keeps the internal EmlisAI reply meta out of the public
``/emotion/submit`` response.  It exposes only a small additive metadata subset
needed by RN display/debug contracts and never returns raw input, evidence text,
comment text, graph payloads, scorecards, or complete diagnostics.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from enum import Enum
from typing import Any, Dict, Iterable, Optional


PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION = "emlis.public_input_feedback_meta.v1"
PUBLIC_EMLIS_FEEDBACK_META_BOUNDARY_VERSION = "emlis.public_feedback_meta_boundary.v1"
PUBLIC_EMLIS_FEEDBACK_META_TARGET_BYTES = 8 * 1024
PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES = 12 * 1024
PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS = 20
PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH = 96
PUBLIC_EMLIS_FEEDBACK_META_MAX_GATE_RESULTS = 20

_DEFAULT_VERSION = "emlis_ai_v3"
_DEFAULT_KERNEL_VERSION = "multi_perspective_observation.v1"
_DEFAULT_TIER = "free"
_ALLOWED_OBSERVATION_STATUSES = {"passed", "rejected", "unavailable", "safety_blocked"}
_ALLOWED_OBSERVATION_REPLY_KINDS = {
    "eligible_observation",
    "low_information_observation",
}
_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


def _compact_json_bytes(value: Mapping[str, Any]) -> int:
    return len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _boundary_marker(*, trimmed: bool) -> Dict[str, Any]:
    return {
        "version": PUBLIC_EMLIS_FEEDBACK_META_BOUNDARY_VERSION,
        "sanitized": True,
        "max_bytes": PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES,
        "trimmed": bool(trimmed),
        "internal_meta_returned": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _minimal_unavailable_meta(
    *,
    subscription_tier: Any = None,
    reason: str = "public_feedback_meta_sanitizer_failed",
) -> Dict[str, Any]:
    return {
        "schema_version": PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION,
        "version": _DEFAULT_VERSION,
        "kernel_version": _DEFAULT_KERNEL_VERSION,
        "tier": _coerce_tier(subscription_tier),
        "observation_status": "unavailable",
        "rejection_reasons": [_safe_reason(reason) or "public_feedback_meta_sanitizer_failed"],
        "public_feedback_meta_boundary": _boundary_marker(trimmed=True),
    }


def _coerce_tier(value: Any) -> str:
    if isinstance(value, Enum):
        raw = value.value
    else:
        raw = getattr(value, "value", value)
    text = str(raw or "").strip() or _DEFAULT_TIER
    return _safe_identifier(text, max_length=40, default=_DEFAULT_TIER)


def _safe_identifier(value: Any, *, max_length: int, default: Optional[str] = None) -> Optional[str]:
    text = str(value or "").strip()
    if not text:
        return default
    text = text[:max_length]
    if not _IDENTIFIER_RE.match(text):
        return default
    return text


def _safe_trace(value: Any) -> Optional[str]:
    return _safe_identifier(value, max_length=120, default=None)


def _safe_status(value: Any) -> Optional[str]:
    text = _safe_identifier(value, max_length=40, default=None)
    if text in _ALLOWED_OBSERVATION_STATUSES:
        return text
    return None


def _safe_reply_kind(value: Any) -> Optional[str]:
    text = _safe_identifier(value, max_length=80, default=None)
    if text in _ALLOWED_OBSERVATION_REPLY_KINDS:
        return text
    return None


def _safe_reason(value: Any) -> Optional[str]:
    return _safe_identifier(
        value,
        max_length=PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH,
        default=None,
    )


def _safe_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    return None


def _safe_mapping(value: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return value
    return None


def _safe_get(meta: Mapping[str, Any], key: str, default: Any = None) -> Any:
    return meta.get(key, default)


def _safe_rejection_reasons(values: Any) -> list[str]:
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes, bytearray)):
        return []
    reasons: list[str] = []
    for raw in values:
        reason = _safe_reason(raw)
        if not reason:
            continue
        reasons.append(reason)
        if len(reasons) >= PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS:
            break
    return reasons


def _pick_diagnostic_summary(internal_meta: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    summary = _safe_mapping(_safe_get(internal_meta, "diagnostic_summary"))
    if summary is not None:
        return summary

    multi_perspective = _safe_mapping(_safe_get(internal_meta, "multi_perspective"))
    if multi_perspective is None:
        return None
    return _safe_mapping(_safe_get(multi_perspective, "diagnostic_summary"))


def _build_gate_results(raw_gate_results: Any) -> Dict[str, Dict[str, Any]]:
    gate_results = _safe_mapping(raw_gate_results)
    if gate_results is None:
        return {}

    public_gate_results: Dict[str, Dict[str, Any]] = {}
    for raw_gate_name, raw_gate_payload in gate_results.items():
        if len(public_gate_results) >= PUBLIC_EMLIS_FEEDBACK_META_MAX_GATE_RESULTS:
            break
        gate_name = _safe_identifier(raw_gate_name, max_length=80, default=None)
        gate_payload = _safe_mapping(raw_gate_payload)
        if not gate_name or gate_payload is None:
            continue

        gate_summary: Dict[str, Any] = {}
        passed = _safe_bool(_safe_get(gate_payload, "passed"))
        if passed is not None:
            gate_summary["passed"] = passed
        primary_reason = _safe_reason(_safe_get(gate_payload, "primary_reason"))
        if primary_reason:
            gate_summary["primary_reason"] = primary_reason
        if gate_summary:
            public_gate_results[gate_name] = gate_summary
    return public_gate_results


def _build_diagnostic_summary(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _pick_diagnostic_summary(internal_meta)
    if source is None:
        return {}

    public_summary: Dict[str, Any] = {}
    for key, max_length in (
        ("stage", 80),
        ("primary_reason", 120),
        ("coverage_group", 80),
        ("composer_status", 80),
        ("composer_source", 80),
    ):
        value = _safe_identifier(_safe_get(source, key), max_length=max_length, default=None)
        if value:
            public_summary[key] = value

    gate_results = _build_gate_results(_safe_get(source, "gate_results"))
    if gate_results:
        public_summary["gate_results"] = gate_results

    return public_summary


def _build_runtime_surface_gate(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _safe_mapping(_safe_get(internal_meta, "runtime_surface_pre_return_gate"))
    if source is None:
        return {}

    public_gate: Dict[str, Any] = {}
    passed = _safe_bool(_safe_get(source, "passed"))
    if passed is not None:
        public_gate["passed"] = passed

    action = _safe_identifier(_safe_get(source, "action"), max_length=80, default=None)
    if action:
        public_gate["action"] = action

    rerender_attempted = _safe_bool(_safe_get(source, "rerender_attempted"))
    if rerender_attempted is not None:
        public_gate["rerender_attempted"] = rerender_attempted

    reasons = _safe_rejection_reasons(_safe_get(source, "rejection_reasons"))
    if reasons:
        public_gate["rejection_reasons"] = reasons

    return public_gate


def _build_observation_reply_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _safe_mapping(_safe_get(internal_meta, "observation_reply_meta"))
    if source is None:
        return {}

    public_meta: Dict[str, Any] = {}
    reply_kind = _safe_reply_kind(_safe_get(source, "observation_reply_kind"))
    if reply_kind:
        public_meta["observation_reply_kind"] = reply_kind

    for key in (
        "eligible_for_full_observation",
        "question_required",
        "user_fact_may_promote_to_eligible",
    ):
        value = _safe_bool(_safe_get(source, key))
        if value is not None:
            public_meta[key] = value

    return public_meta


def _build_step10_repair_meta(internal_meta: Mapping[str, Any]) -> Dict[str, Any]:
    source = _safe_mapping(_safe_get(internal_meta, "step10_observation_display_repair_integration"))
    if source is None:
        return {}

    public_meta: Dict[str, Any] = {}
    applied = _safe_bool(_safe_get(source, "applied"))
    if applied is not None:
        public_meta["applied"] = applied

    final_status = _safe_status(_safe_get(source, "final_observation_status"))
    if final_status:
        public_meta["final_observation_status"] = final_status

    reply_kind = _safe_reply_kind(_safe_get(source, "observation_reply_kind"))
    if reply_kind:
        public_meta["observation_reply_kind"] = reply_kind

    for key in (
        "public_status_extended",
        "observation_status_enum_extended",
        "rn_visible_contract_changed",
        "response_shape_changed",
        "display_gate_relaxed",
        "fixed_fallback_used",
        "external_ai_used",
    ):
        value = _safe_bool(_safe_get(source, key))
        if value is not None:
            public_meta[key] = value

    return public_meta


def _mark_trimmed(meta: Dict[str, Any]) -> Dict[str, Any]:
    boundary = meta.get("public_feedback_meta_boundary")
    if isinstance(boundary, dict):
        boundary["trimmed"] = True
    return meta


def _fit_hard_byte_limit(meta: Dict[str, Any], *, subscription_tier: Any = None) -> Dict[str, Any]:
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    _mark_trimmed(meta)

    runtime_gate = meta.get("runtime_surface_pre_return_gate")
    if isinstance(runtime_gate, dict):
        runtime_gate.pop("rejection_reasons", None)
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    diagnostic_summary = meta.get("diagnostic_summary")
    if isinstance(diagnostic_summary, dict):
        diagnostic_summary.pop("gate_results", None)
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    meta.pop("diagnostic_summary", None)
    meta.pop("runtime_surface_pre_return_gate", None)
    meta.pop("observation_reply_meta", None)
    meta.pop("step10_observation_display_repair_integration", None)
    meta["rejection_reasons"] = meta.get("rejection_reasons", [])[:5]
    if _compact_json_bytes(meta) <= PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES:
        return meta

    return _minimal_unavailable_meta(
        subscription_tier=subscription_tier,
        reason="public_feedback_meta_hard_limit_exceeded",
    )


def build_public_emlis_input_feedback_meta(
    internal_meta: Mapping[str, Any] | None,
    *,
    comment_text_present: bool,
    subscription_tier: Any = None,
) -> Dict[str, Any]:
    """Build the public-safe ``input_feedback.emlis_ai`` metadata subset.

    ``comment_text_present`` is intentionally accepted at this boundary so
    callers can keep the public display contract close to the sanitizer.  The
    sanitizer never copies the actual comment text; response inclusion remains
    controlled by the caller in the next integration step.
    """
    del comment_text_present  # The body is never copied into public meta.

    try:
        if not isinstance(internal_meta, Mapping):
            return _minimal_unavailable_meta(subscription_tier=subscription_tier)

        version = _safe_identifier(
            _safe_get(internal_meta, "version"),
            max_length=80,
            default=_DEFAULT_VERSION,
        )
        kernel_version = _safe_identifier(
            _safe_get(internal_meta, "kernel_version"),
            max_length=120,
            default=_DEFAULT_KERNEL_VERSION,
        )
        tier_source = subscription_tier
        if tier_source is None:
            tier_source = _safe_get(internal_meta, "tier", _DEFAULT_TIER)

        step10_meta = _safe_mapping(
            _safe_get(internal_meta, "step10_observation_display_repair_integration")
        )
        observation_status = _safe_status(_safe_get(internal_meta, "observation_status"))
        if observation_status is None and step10_meta is not None:
            observation_status = _safe_status(_safe_get(step10_meta, "final_observation_status"))
        observation_status = observation_status or "unavailable"

        public_meta: Dict[str, Any] = {
            "schema_version": PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION,
            "version": version or _DEFAULT_VERSION,
            "kernel_version": kernel_version or _DEFAULT_KERNEL_VERSION,
            "tier": _coerce_tier(tier_source),
            "observation_status": observation_status,
        }

        observation_trace_id = _safe_trace(_safe_get(internal_meta, "observation_trace_id"))
        if observation_trace_id:
            public_meta["observation_trace_id"] = observation_trace_id

        trace_id = _safe_trace(_safe_get(internal_meta, "trace_id"))
        if trace_id:
            public_meta["trace_id"] = trace_id

        reply_kind = _safe_reply_kind(_safe_get(internal_meta, "observation_reply_kind"))
        if reply_kind:
            public_meta["observation_reply_kind"] = reply_kind

        rejection_reasons = _safe_rejection_reasons(_safe_get(internal_meta, "rejection_reasons"))
        if rejection_reasons:
            public_meta["rejection_reasons"] = rejection_reasons

        diagnostic_summary = _build_diagnostic_summary(internal_meta)
        if diagnostic_summary:
            public_meta["diagnostic_summary"] = diagnostic_summary

        runtime_gate = _build_runtime_surface_gate(internal_meta)
        if runtime_gate:
            public_meta["runtime_surface_pre_return_gate"] = runtime_gate

        observation_reply_meta = _build_observation_reply_meta(internal_meta)
        if observation_reply_meta:
            public_meta["observation_reply_meta"] = observation_reply_meta

        step10_public_meta = _build_step10_repair_meta(internal_meta)
        if step10_public_meta:
            public_meta["step10_observation_display_repair_integration"] = step10_public_meta

        public_meta["public_feedback_meta_boundary"] = _boundary_marker(trimmed=False)
        return _fit_hard_byte_limit(public_meta, subscription_tier=tier_source)
    except Exception:
        return _minimal_unavailable_meta(subscription_tier=subscription_tier)


def should_include_public_input_feedback(
    comment_text: Any,
    public_meta: Mapping[str, Any] | None,
) -> bool:
    """Return whether ``input_feedback`` should be present in a public response.

    RN shows Emlis observations only for ``passed`` public meta plus a non-empty
    ``comment_text``.  Keeping this condition in the public meta boundary avoids
    returning meta-only unavailable/rejected payloads that cannot be displayed and
    can bloat ``/emotion/submit`` responses.
    """
    if not str(comment_text or "").strip():
        return False
    if not isinstance(public_meta, Mapping):
        return False
    return str(public_meta.get("observation_status") or "").strip() == "passed"


__all__ = [
    "PUBLIC_EMLIS_FEEDBACK_META_BOUNDARY_VERSION",
    "PUBLIC_EMLIS_FEEDBACK_META_HARD_BYTES",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_GATE_RESULTS",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_REASON_LENGTH",
    "PUBLIC_EMLIS_FEEDBACK_META_MAX_REJECTION_REASONS",
    "PUBLIC_EMLIS_FEEDBACK_META_SCHEMA_VERSION",
    "PUBLIC_EMLIS_FEEDBACK_META_TARGET_BYTES",
    "build_public_emlis_input_feedback_meta",
    "should_include_public_input_feedback",
]
