# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 7 meta-only integration for User Label Connection Observation v1.

This module connects the Phase 2-6 User Label Connection layers to EmlisAI
runtime metadata without generating visible text.  It only exposes safe summary
identifiers, counts, and booleans.  It must not add public response keys, change
``/emotion/submit`` shape, connect RN-visible text, or carry raw memo/action /
comment/candidate/surface bodies.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_user_label_connection_candidate import (
    CANDIDATE_QUALITY_GATE_CANDIDATE,
    build_user_label_connection_candidate_metas,
)
from emlis_ai_user_label_connection_gate import (
    GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN,
    build_user_label_connection_gate_report,
    user_label_connection_gate_public_summary,
)
from emlis_ai_user_label_connection_material import build_user_label_connection_material
from emlis_ai_user_label_connection_surface import (
    SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION,
    build_user_label_connection_surface_plan,
    user_label_connection_surface_plan_public_summary,
    user_label_connection_visible_surface_public_summary,
)

USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.meta_only_integration.v1"
)
USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_STEP: Final = "UserLabelConnection_MetaOnlyIntegration_v1"
USER_LABEL_CONNECTION_META_ONLY_META_KEY: Final = "user_label_connection_meta_only"
USER_LABEL_CONNECTION_PUBLIC_META_KEY: Final = "user_label_connection"

_INTERNAL_SCOPE_PROBE_SURFACE: Final = (
    "この期間の記録では、今回と近い記録の範囲で、近い形に見えます。"
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "raw_user_text",
        "rawUserText",
        "source_text",
        "sourceText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo",
        "memo_action",
        "memo_text",
        "memoText",
        "memo_action_text",
        "memoActionText",
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
        "realized_text",
        "realizedText",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "comment_text_body_included",
        "comment_text_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "internal_question_body_included",
        "private_user_dictionary_text_included",
        "comment_text_generated",
        "comment_text_generated_by_this_layer",
        "comment_text_connected",
        "visible_text_generated",
        "visible_surface_connected",
        "history_line_surface_connected",
        "runtime_surface_connected",
        "public_response_key_added",
        "response_shape_changed",
        "request_key_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "fixed_sentence_template_added",
        "external_ai_added",
        "local_llm_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
    }
)

_SAFE_DEFAULT_FALSE_FLAGS: Final = (
    "api_route_changed",
    "request_key_changed",
    "response_shape_changed",
    "public_response_key_added",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "comment_text_generated",
    "comment_text_generated_by_this_layer",
    "comment_text_connected",
    "visible_text_generated",
    "visible_surface_connected",
    "history_line_surface_connected",
    "runtime_surface_connected",
    "history_connection_applied",
    "raw_input_included",
    "raw_text_included",
    "history_raw_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
    "surface_text_body_included",
    "internal_question_body_included",
    "private_user_dictionary_text_included",
    "fixed_sentence_template_added",
    "external_ai_added",
    "local_llm_added",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        try:
            meta = as_meta()
            if isinstance(meta, Mapping):
                return dict(meta)
        except Exception:
            return {}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Any, *, limit: int = 20) -> list[str]:
    out: list[str] = []
    for item in _listify(values):
        text = _clean(item)
        if text and text not in out:
            out.append(text[:96])
        if len(out) >= limit:
            break
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except Exception:
        return default


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            if _contains_text_payload_key(child):
                return True
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            if _flag_true(child, names):
                return True
    return False


def _edge_family_count(material_meta: Mapping[str, Any]) -> int:
    families: set[str] = set()
    for edge in _listify(material_meta.get("connection_edges")):
        if isinstance(edge, Mapping):
            family = _clean(edge.get("edge_family"))
            if family:
                families.add(family)
    return len(families)


def _max_edge_evidence_record_count(material_meta: Mapping[str, Any]) -> int:
    values: list[int] = []
    for edge in _listify(material_meta.get("connection_edges")):
        if isinstance(edge, Mapping):
            values.append(_int(edge.get("evidence_record_count")))
    return max(values) if values else 0


def _material_summary(material_meta: Mapping[str, Any]) -> dict[str, Any]:
    if _contains_text_payload_key(material_meta) or _flag_true(material_meta):
        return _unsafe_summary("user_label_connection_material_meta_unsafe")
    history_summary = _safe_mapping(material_meta.get("owned_history_points_summary"))
    edge_count = _int(material_meta.get("connection_edge_count"), len(_listify(material_meta.get("connection_edges"))))
    material_quality = _clean(material_meta.get("material_quality"))
    record_scope = _clean(material_meta.get("record_scope"))
    history_read_allowed = bool(material_meta.get("history_read_allowed") is True)
    return {
        "material_schema_version": _clean(material_meta.get("schema_version")),
        "source_scope": _clean(material_meta.get("source_scope")),
        "record_scope": record_scope,
        "capability_tier": _clean(material_meta.get("capability_tier")),
        "material_quality": material_quality,
        "history_read_allowed": history_read_allowed,
        "current_point_present": bool(material_meta.get("current_point_present") is True),
        "owned_history_point_count": _int(history_summary.get("point_count")),
        "same_day_count": _int(history_summary.get("same_day_count")),
        "similar_count": _int(history_summary.get("similar_count")),
        "last_input_present": bool(history_summary.get("last_input_present") is True),
        "history_connection_edge_count": edge_count,
        "history_connection_edge_family_count": _edge_family_count(material_meta),
        "history_connection_evidence_record_count": _max_edge_evidence_record_count(material_meta),
        "history_connection_candidate_present": bool(edge_count > 0),
        "history_connection_blocked": bool(
            not history_read_allowed
            or record_scope.startswith("blocked_")
            or material_quality in {"history_connection_blocked", "low_information_protected", "safety_triage_required"}
        ),
        "low_information_protected": bool(material_meta.get("low_information_protected") is True),
        "user_fact_grounding_boundary_passed": bool(material_meta.get("user_fact_grounding_boundary_passed") is True),
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }


def _candidate_summary(candidate_metas: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if any(_contains_text_payload_key(candidate) or _flag_true(candidate) for candidate in candidate_metas):
        return _unsafe_summary("user_label_connection_candidate_meta_unsafe")
    evidence_counts: list[int] = []
    history_counts: list[int] = []
    current_included = False
    gate_candidate_count = 0
    for candidate in candidate_metas:
        evidence = _safe_mapping(candidate.get("evidence"))
        evidence_counts.append(_int(evidence.get("evidence_record_count")))
        history_counts.append(_int(evidence.get("history_record_count")))
        current_included = current_included or bool(evidence.get("current_record_included") is True)
        if _clean(candidate.get("candidate_quality")) == CANDIDATE_QUALITY_GATE_CANDIDATE:
            gate_candidate_count += 1
    return {
        "candidate_count": len(candidate_metas),
        "gate_candidate_count": gate_candidate_count,
        "blocked_candidate_count": max(0, len(candidate_metas) - gate_candidate_count),
        "history_connection_candidate_present": bool(gate_candidate_count > 0),
        "candidate_evidence_record_count": max(evidence_counts) if evidence_counts else 0,
        "candidate_history_record_count": max(history_counts) if history_counts else 0,
        "candidate_current_record_included": current_included,
        "candidate_body_included": False,
        "comment_text_body_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
    }


def _unsafe_summary(reason: str) -> dict[str, Any]:
    return {
        "evaluated": True,
        "blocked": True,
        "history_connection_blocked": True,
        "rejection_reasons": [_clean(reason) or "user_label_connection_public_meta_unsafe"],
        "public_meta_summary_only": True,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }


def _collect_rejection_reasons(*sources: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        reasons.extend(_dedupe(source.get("rejection_reasons") or source.get("surface_plan_rejection_reasons") or []))
    return _dedupe(reasons)


def _base_contract_flags() -> dict[str, bool]:
    return {key: False for key in _SAFE_DEFAULT_FALSE_FLAGS}


def _observation_meta_from_runtime(
    *,
    observation_reply_meta: Mapping[str, Any] | None,
    material_quality: Any = None,
    safety_triage_kind: Any = None,
) -> dict[str, Any]:
    meta = dict(observation_reply_meta or {}) if isinstance(observation_reply_meta, Mapping) else {}
    if material_quality is not None and "material_quality" not in meta:
        meta["material_quality"] = _clean(material_quality)
    if safety_triage_kind is not None and "safety_triage_kind" not in meta:
        meta["safety_triage_kind"] = _clean(safety_triage_kind)
    return meta


def build_user_label_connection_meta_only_integration(
    current_input: Any,
    *,
    source_bundle: Any = None,
    capability: Any = None,
    subscription_tier: Any = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    material_quality: Any = None,
    safety_triage_kind: Any = None,
    connectable_family: Any = None,
    max_candidates: int = 4,
    reply_flow_meta_only_connected: bool = False,
) -> dict[str, Any]:
    """Build the Phase 7 safe summary without generating visible text."""

    runtime_observation_meta = _observation_meta_from_runtime(
        observation_reply_meta=observation_reply_meta,
        material_quality=material_quality,
        safety_triage_kind=safety_triage_kind,
    )
    material = build_user_label_connection_material(
        current_input,
        source_bundle=source_bundle,
        capability=capability,
        subscription_tier=subscription_tier,
        observation_reply_meta=runtime_observation_meta,
        material_quality=material_quality,
    )
    material_meta = material.as_meta()
    candidate_metas = build_user_label_connection_candidate_metas(material, max_candidates=max_candidates)
    gate_report = build_user_label_connection_gate_report(
        candidate_metas,
        material=material,
        capability=capability,
        subscription_tier=subscription_tier,
        observation_reply_meta=runtime_observation_meta,
        proposed_surface=_INTERNAL_SCOPE_PROBE_SURFACE,
        max_candidates=max_candidates,
    )
    first_candidate = candidate_metas[0] if candidate_metas else {}
    surface_plan = build_user_label_connection_surface_plan(
        gate_report,
        candidate=first_candidate,
        observation_reply_meta=runtime_observation_meta,
        connectable_family=connectable_family,
    )

    material_safe = _material_summary(material_meta)
    candidate_safe = _candidate_summary(candidate_metas)
    gate_safe = user_label_connection_gate_public_summary(gate_report)
    surface_safe = user_label_connection_surface_plan_public_summary(surface_plan)
    rejection_reasons = _collect_rejection_reasons(gate_report, surface_plan, material_safe)
    gate_passed = bool(gate_report.get("passed") is True and gate_report.get("action") == GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN)
    limited_plan_ready = bool(surface_plan.get("surface_plan_kind") == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION)
    history_connection_candidate_present = bool(
        material_safe.get("history_connection_candidate_present")
        or candidate_safe.get("history_connection_candidate_present")
        or limited_plan_ready
    )
    history_connection_blocked = bool(
        material_safe.get("history_connection_blocked")
        or gate_report.get("blocked") is True
        or surface_plan.get("surface_plan_kind") != SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    )

    meta: dict[str, Any] = {
        "schema_version": USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_STEP,
        "phase": "Phase7_MetaOnlyIntegration",
        "evaluated": True,
        "meta_only_connected": True,
        "reply_flow_meta_only_connected": bool(reply_flow_meta_only_connected),
        "surface_connection_deferred_to_phase8": True,
        "visible_surface_connection_deferred": True,
        "comment_text_connection_deferred": True,
        "public_meta_summary_only": True,
        "source_scope": _clean(material_safe.get("source_scope")),
        "record_scope": _clean(material_safe.get("record_scope")),
        "capability_tier": _clean(material_safe.get("capability_tier") or getattr(capability, "tier", "") or subscription_tier),
        "history_read_allowed": bool(material_safe.get("history_read_allowed") is True),
        "history_connection_candidate_present": history_connection_candidate_present,
        "history_connection_blocked": history_connection_blocked,
        "history_connection_applied": False,
        "history_connection_edge_family_count": _int(material_safe.get("history_connection_edge_family_count")),
        "history_connection_evidence_record_count": max(
            _int(material_safe.get("history_connection_evidence_record_count")),
            _int(candidate_safe.get("candidate_evidence_record_count")),
        ),
        "scope_marker_required": True,
        "soft_marker_required": True,
        "gate_passed": gate_passed,
        "gate_action": _clean(gate_report.get("action")),
        "surface_plan_kind": _clean(surface_plan.get("surface_plan_kind")),
        "connectable_family": _clean(surface_plan.get("connectable_family")),
        "limited_history_line_observation_ready": limited_plan_ready,
        "material_summary": material_safe,
        "candidate_summary": candidate_safe,
        "gate_summary": gate_safe,
        "surface_plan_summary": surface_safe,
        "surface_plan_meta": surface_plan,
        "rejection_reasons": rejection_reasons,
        **_base_contract_flags(),
    }
    assert_user_label_connection_meta_only_integration_contract(meta)
    return {key: value for key, value in meta.items() if value not in ("", None)}


def _visible_surface_meta_from(source: Mapping[str, Any]) -> dict[str, Any]:
    if _clean(source.get("phase")) == USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE:
        return dict(source)
    if _clean(source.get("schema_version")) == USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION:
        return dict(source)
    for key in (
        USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY,
        "phase8_limited_visible_surface_connection",
        "limited_visible_surface_connection",
    ):
        nested = _safe_mapping(source.get(key))
        if nested:
            return nested
    return {}


def _without_visible_surface_meta(source: Mapping[str, Any]) -> dict[str, Any]:
    hidden_keys = {
        USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY,
        "phase8_limited_visible_surface_connection",
        "limited_visible_surface_connection",
    }
    return {str(key): value for key, value in source.items() if str(key) not in hidden_keys}


def user_label_connection_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _safe_mapping(value)
    if not source:
        return {}

    visible_source = _visible_surface_meta_from(source)
    visible_summary = user_label_connection_visible_surface_public_summary(visible_source) if visible_source else {}

    if _clean(source.get("phase")) == USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE:
        return visible_summary
    if _clean(source.get("schema_version")) == USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION:
        return visible_summary

    meta_only_source = _without_visible_surface_meta(source)
    if _contains_text_payload_key(meta_only_source) or _flag_true(meta_only_source):
        return _unsafe_summary("user_label_connection_meta_only_public_meta_unsafe")

    visible_applied = bool(visible_summary.get("history_connection_applied") is True)
    summary = {
        "public_meta_summary_only": True,
        "schema_version": _clean(source.get("schema_version")),
        "phase": USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE if visible_applied else _clean(source.get("phase")),
        "evaluated": bool(source.get("evaluated") is True),
        "meta_only_connected": bool(source.get("meta_only_connected") is True),
        "reply_flow_meta_only_connected": bool(source.get("reply_flow_meta_only_connected") is True),
        "history_connection_candidate_present": bool(source.get("history_connection_candidate_present") is True),
        "history_connection_blocked": bool(source.get("history_connection_blocked") is True and not visible_applied),
        "history_connection_applied": visible_applied,
        "limited_visible_surface_connection_applied": bool(visible_summary.get("limited_visible_surface_connection_applied") is True),
        "history_line_surface_connected": bool(visible_summary.get("history_line_surface_connected") is True),
        "history_connection_edge_family_count": _int(source.get("history_connection_edge_family_count")),
        "history_connection_evidence_record_count": max(
            _int(source.get("history_connection_evidence_record_count")),
            _int(visible_summary.get("history_connection_evidence_record_count")),
        ),
        "scope_marker_required": bool(source.get("scope_marker_required") is True or visible_summary.get("scope_marker_required") is True),
        "soft_marker_required": bool(source.get("soft_marker_required") is True or visible_summary.get("soft_marker_required") is True),
        "scope_marker_present": bool(visible_summary.get("scope_marker_present") is True),
        "soft_marker_present": bool(visible_summary.get("soft_marker_present") is True),
        "gate_passed": bool(source.get("gate_passed") is True),
        "gate_action": _clean(source.get("gate_action")),
        "surface_plan_kind": _clean(source.get("surface_plan_kind") or visible_summary.get("surface_plan_kind")),
        "limited_history_line_observation_ready": bool(source.get("limited_history_line_observation_ready") is True),
        "visible_surface_connected": bool(visible_summary.get("visible_surface_connected") is True),
        "runtime_surface_connected": bool(visible_summary.get("runtime_surface_connected") is True),
        "comment_text_connected": bool(visible_summary.get("comment_text_connected") is True),
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }
    reasons = _dedupe(source.get("rejection_reasons") or [])
    reasons.extend(_dedupe(visible_summary.get("rejection_reasons") or []))
    reasons = _dedupe(reasons)
    if reasons:
        summary["rejection_reasons"] = reasons
    json.dumps(summary, ensure_ascii=False, sort_keys=True)
    return {key: value for key, value in summary.items() if value not in ("", None)}


def attach_user_label_connection_meta_only_integration(
    meta: Mapping[str, Any] | None,
    *,
    current_input: Any,
    source_bundle: Any = None,
    capability: Any = None,
    subscription_tier: Any = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    material_quality: Any = None,
    safety_triage_kind: Any = None,
    connectable_family: Any = None,
) -> dict[str, Any]:
    """Attach Phase 7 summary to internal reply meta only."""

    out = dict(meta or {}) if isinstance(meta, Mapping) else {}
    integration = build_user_label_connection_meta_only_integration(
        current_input,
        source_bundle=source_bundle,
        capability=capability,
        subscription_tier=subscription_tier,
        observation_reply_meta=observation_reply_meta,
        material_quality=material_quality,
        safety_triage_kind=safety_triage_kind,
        connectable_family=connectable_family,
        reply_flow_meta_only_connected=True,
    )
    out[USER_LABEL_CONNECTION_META_ONLY_META_KEY] = integration
    summary = user_label_connection_public_summary(integration)
    if isinstance(out.get("diagnostic_summary"), dict):
        out["diagnostic_summary"][USER_LABEL_CONNECTION_META_ONLY_META_KEY] = summary
        out["diagnostic_summary"][USER_LABEL_CONNECTION_PUBLIC_META_KEY] = summary
    if isinstance(out.get("phase_gate"), dict):
        out["phase_gate"].update(
            {
                "phase7_user_label_connection_meta_only_ready": True,
                "phase7_user_label_connection_reply_flow_meta_only_connected": True,
                "phase7_user_label_connection_comment_text_connected": False,
                "phase7_user_label_connection_visible_surface_connected": False,
                "phase7_user_label_connection_public_response_key_added": False,
                "phase7_user_label_connection_raw_text_included": False,
                "phase7_user_label_connection_comment_text_body_included": False,
            }
        )
    assert_user_label_connection_meta_only_integration_contract(out[USER_LABEL_CONNECTION_META_ONLY_META_KEY])
    return out


def assert_user_label_connection_meta_only_integration_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("User Label Connection meta-only integration must not include raw/comment/candidate/surface body keys")
    if _flag_true(value):
        raise ValueError("User Label Connection meta-only integration contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("User Label Connection meta-only integration must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION:
        raise ValueError("unexpected User Label Connection meta-only schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_STEP:
        raise ValueError("unexpected User Label Connection meta-only step")
    if value.get("meta_only_connected") is not True:
        raise ValueError("Phase 7 requires meta_only_connected=true")
    if value.get("comment_text_connected") is not False:
        raise ValueError("Phase 7 must not connect comment_text")
    if value.get("visible_surface_connected") is not False:
        raise ValueError("Phase 7 must not connect visible surface")
    if value.get("history_connection_applied") is not False:
        raise ValueError("Phase 7 must not apply history connection to visible output")
    for key in _SAFE_DEFAULT_FALSE_FLAGS:
        if value.get(key) is not False:
            raise ValueError(f"Phase 7 contract requires {key}=false")


__all__ = [
    "USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_META_ONLY_INTEGRATION_STEP",
    "USER_LABEL_CONNECTION_META_ONLY_META_KEY",
    "USER_LABEL_CONNECTION_PUBLIC_META_KEY",
    "USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY",
    "attach_user_label_connection_meta_only_integration",
    "assert_user_label_connection_meta_only_integration_contract",
    "build_user_label_connection_meta_only_integration",
    "user_label_connection_public_summary",
]
