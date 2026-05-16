# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 9 Self-Repair Loop for EmlisAI Complete Composer initial version.

Self-Repair receives Gate / Grounding reasons and applies only bounded,
meaning-preserving adjustments to the Complete Composer internal plan/surface.
It never relaxes gates, never creates new user-facing ``comment_text`` keys,
and never invents evidence, relation, diagnosis, advice, or fixed fallback
sentences.  Public API response shape and RN display contracts stay unchanged.
"""

from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
from typing import Any, Iterable, Mapping, Sequence, Tuple
import re

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_STAGE,
    CompleteSentencePlanLine,
    CompleteSentencePlanV2,
    RepairTrace,
)
from emlis_ai_complete_grounding_binding import COMPLETE_BINDING_AWARE_GROUNDING_STAGE
from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_REALIZER_STAGE,
    COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
    COMPLETE_SURFACE_STATUS_READY,
    COMPLETE_SURFACE_STATUS_UNAVAILABLE,
    CompleteSurfaceLineV2,
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
    build_complete_surface_signature,
)

COMPLETE_SELF_REPAIR_VERSION = "emlis.complete_self_repair.v1"
COMPLETE_SELF_REPAIR_SERVICE_VERSION = COMPLETE_SELF_REPAIR_VERSION
COMPLETE_SELF_REPAIR_STAGE = "Step9_Self_Repair_Loop"
COMPLETE_SELF_REPAIR_STEP = COMPLETE_SELF_REPAIR_STAGE
COMPLETE_SELF_REPAIR_TARGET_STEP = COMPLETE_SELF_REPAIR_STAGE
COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT = "Commit 9"

COMPLETE_SELF_REPAIR_STATUS_REPAIRED = "repaired"
COMPLETE_SELF_REPAIR_STATUS_UNCHANGED = "unchanged"
COMPLETE_SELF_REPAIR_STATUS_ABORTED = "aborted"
COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE = "unavailable"

MAX_SELF_REPAIR_ATTEMPTS = 2

REPAIR_REASON_UNSUPPORTED_SENTENCE = "unsupported_sentence"
REPAIR_REASON_RELATION_NOT_EXPRESSED = "relation_not_expressed"
REPAIR_REASON_TEMPLATE_LIKE = "template_like"
REPAIR_REASON_RAW_ECHO = "raw_echo"
REPAIR_REASON_OVER_ECHO = "over_echo"
REPAIR_REASON_TOO_LONG = "too_long"
REPAIR_REASON_OVERCLAIM = "overclaim"
REPAIR_REASON_UNSUPPORTED_OVERCLAIM = "unsupported_overclaim"

ALLOWED_REPAIR_REASONS = {
    REPAIR_REASON_UNSUPPORTED_SENTENCE,
    REPAIR_REASON_RELATION_NOT_EXPRESSED,
    REPAIR_REASON_TEMPLATE_LIKE,
    REPAIR_REASON_RAW_ECHO,
    REPAIR_REASON_OVER_ECHO,
    REPAIR_REASON_TOO_LONG,
    REPAIR_REASON_OVERCLAIM,
    REPAIR_REASON_UNSUPPORTED_OVERCLAIM,
}

REJECT_PREFERRED_REASONS = {REPAIR_REASON_OVERCLAIM, REPAIR_REASON_UNSUPPORTED_OVERCLAIM}
ECHO_REASONS = {REPAIR_REASON_RAW_ECHO, REPAIR_REASON_OVER_ECHO}

RAW_INPUT_META_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
}

_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[^0-9a-zA-Z_\-.]+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"

RELATION_MARKER_PHRASES = {
    "contrast": "別々の向きが並んでいることも残しています。",
    "coexistence": "同じ時間の中に重なっていることも残しています。",
    "pressure": "圧力として前面に出ていることも残しています。",
    "approach_avoidance": "近づく動きと止まる動きの両方が残っています。",
    "recovery": "戻ってくる動きと前段の負荷の関係も残しています。",
    "residue": "あとに残る余韻として置かれています。",
}

RELATION_ROLE_PHRASES = {
    "contrast": "別々の向き",
    "coexistence": "同じ時間の重なり",
    "pressure": "圧力",
    "approach_avoidance": "近づく動きと止まる動き",
    "recovery": "戻ってくる動き",
    "residue": "あとに残る余韻",
    "limit": "限界に近い圧力",
    "context": "根拠のある背景",
    "center": "中心にある感覚",
}

RELATION_CONNECTOR_KEYS = {
    "contrast": "repair_relation_contrast",
    "coexistence": "repair_relation_coexistence",
    "pressure": "repair_relation_pressure",
    "approach_avoidance": "repair_relation_approach_avoidance",
    "recovery": "repair_relation_recovery",
    "residue": "repair_relation_residue",
}

FORBIDDEN_REPAIR_OPERATIONS = {
    "add_rootless_material",
    "invent_relation",
    "swap_to_fixed_completed_sentence",
    "expand_meaning",
    "delete_must_include",
    "weaken_overclaim_only",
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _clean_token(value: Any) -> str:
    return _TOKEN_RE.sub("_", str(value or "").strip().lower()).strip("_")


def _dedupe(values: Iterable[Any] | Any | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        raw: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        raw = values
    else:
        raw = [values]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return tuple(out)


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    if is_dataclass(value):
        return _json_safe_mapping(asdict(value))
    if hasattr(value, "as_meta"):
        try:
            mapped = value.as_meta()
            if isinstance(mapped, Mapping):
                return _json_safe_mapping(mapped)
        except Exception:
            pass
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key or "").strip()
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "as_meta"):
        try:
            meta = value.as_meta()
            if isinstance(meta, Mapping):
                return dict(meta)
        except Exception:
            return {}
    return {}


def _coerce_surface_realization(value: Any, **surface_kwargs: Any) -> CompleteSurfaceRealizationV2:
    if isinstance(value, CompleteSurfaceRealizationV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSurfaceRealizationV2(
            plan_id=value.get("plan_id") or "complete_surface_realization_v2",
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "unknown",
            surface_lines=value.get("surface_lines") or value.get("lines") or (),
            source_sentence_plan=value.get("source_sentence_plan") or value.get("sentence_plan") or None,
            meta=value.get("meta") or {},
            status=value.get("status") or COMPLETE_SURFACE_STATUS_READY,
        )
    return build_complete_surface_realization_v2(**surface_kwargs)


def _coerce_plan(value: Any) -> CompleteSentencePlanV2 | None:
    if isinstance(value, CompleteSentencePlanV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanV2(
            plan_id=value.get("plan_id") or "complete_sentence_plan_v2",
            sentence_budget=value.get("sentence_budget") or len(value.get("sentence_plans") or value.get("lines") or ()) or 2,
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "unknown",
            sentence_plans=value.get("sentence_plans") or value.get("lines") or (),
            meta=value.get("meta") or {},
        )
    return None


def _plan_line_from_surface_line(line: CompleteSurfaceLineV2) -> CompleteSentencePlanLine:
    source = _json_safe_mapping(line.source_sentence_plan_line)
    return CompleteSentencePlanLine(
        sentence_id=source.get("sentence_id") or line.sentence_id,
        line_role=source.get("line_role") or line.line_role,
        relation_type=source.get("relation_type") or line.relation_type,
        focus_rank=source.get("focus_rank") or 1,
        phrase_unit_ids=source.get("phrase_unit_ids") or source.get("used_phrase_unit_ids") or line.phrase_unit_ids,
        evidence_span_ids=source.get("evidence_span_ids") or source.get("used_evidence_span_ids") or line.evidence_span_ids,
        must_include_roles=source.get("must_include_roles") or (),
        optional_roles=source.get("optional_roles") or (),
        forbidden_surface_keys=source.get("forbidden_surface_keys") or line.forbidden_surface_keys,
        max_chars=source.get("max_chars") or 120,
        surface_intent=source.get("surface_intent") or f"{line.line_role}_observation",
        repair_policy=source.get("repair_policy") or ("self_repair_allowed",),
        meta={
            **_json_safe_mapping(source.get("meta") or {}),
            "source_step": COMPLETE_SELF_REPAIR_STAGE,
            "derived_from_surface_line": True,
            "raw_input_included": False,
        },
    )


def _source_plan_for(realization: CompleteSurfaceRealizationV2) -> CompleteSentencePlanV2:
    plan = _coerce_plan(realization.source_sentence_plan)
    if plan is not None:
        return plan
    lines = [_plan_line_from_surface_line(line) for line in realization.surface_lines]
    return CompleteSentencePlanV2(
        plan_id=f"{realization.plan_id}_source_plan",
        sentence_budget=max(2, min(5, len(lines) or 2)),
        coverage_group=realization.coverage_group,
        sentence_plans=lines,
        meta={"source_step": COMPLETE_SELF_REPAIR_STAGE, "raw_input_included": False},
    )


def _line_plan_map(plan: CompleteSentencePlanV2) -> dict[str, CompleteSentencePlanLine]:
    return {line.sentence_id: line for line in plan.sentence_plans}


def _is_must_include(plan_line: CompleteSentencePlanLine | None, surface_line: CompleteSurfaceLineV2 | None = None) -> bool:
    if plan_line is not None and plan_line.must_include_roles:
        return True
    if surface_line is not None:
        source = surface_line.source_sentence_plan_line
        if isinstance(source, Mapping) and source.get("must_include_roles"):
            return True
    return False


def _is_optional(plan_line: CompleteSentencePlanLine | None, surface_line: CompleteSurfaceLineV2) -> bool:
    if surface_line.line_role == "closing":
        return True
    if plan_line is not None and plan_line.optional_roles:
        return True
    return not _is_must_include(plan_line, surface_line)


def _line_has_binding(line: CompleteSurfaceLineV2) -> bool:
    return bool(line.evidence_span_ids and line.phrase_unit_ids and line.relation_type)


def _evidence_ids_from(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, Mapping):
        return _dedupe(value.get("allowed_evidence_span_ids") or value.get("used_evidence_span_ids") or value.get("evidence_span_ids"))
    if hasattr(value, "allowed_evidence_span_ids"):
        return _dedupe(getattr(value, "allowed_evidence_span_ids", None))
    if hasattr(value, "span_id"):
        return _dedupe([getattr(value, "span_id", "")])
    return _dedupe(value)


def _allowed_rebind_ids(*sources: Any) -> Tuple[str, ...]:
    ids: list[str] = []
    for source in sources:
        if source is None:
            continue
        if isinstance(source, Sequence) and not isinstance(source, (str, bytes, Mapping)):
            for item in source:
                ids.extend(_evidence_ids_from(item))
        else:
            ids.extend(_evidence_ids_from(source))
    return _dedupe(ids)


def _normalize_reason(value: Any) -> str:
    reason = _clean_token(value)
    aliases = {
        "complete_relation_not_expressed": REPAIR_REASON_RELATION_NOT_EXPRESSED,
        "complete_over_echo": REPAIR_REASON_OVER_ECHO,
        "over_echo": REPAIR_REASON_OVER_ECHO,
        "raw_copy": REPAIR_REASON_RAW_ECHO,
        "raw_quote": REPAIR_REASON_RAW_ECHO,
        "too_long_comment": REPAIR_REASON_TOO_LONG,
        "surface_too_long": REPAIR_REASON_TOO_LONG,
        "same_ending_major_detected": REPAIR_REASON_TEMPLATE_LIKE,
        "fixed_template_like": REPAIR_REASON_TEMPLATE_LIKE,
        "unsupported_overclaim": REPAIR_REASON_UNSUPPORTED_OVERCLAIM,
    }
    return aliases.get(reason, reason)


def _reasons_from_gate_input(gate_reasons: Any = None, grounding_report: Any = None, gate_results: Any = None, meta: Mapping[str, Any] | None = None) -> Tuple[str, ...]:
    reasons: list[str] = []
    for raw in _dedupe(gate_reasons):
        reasons.append(_normalize_reason(raw))
    if grounding_report is not None:
        reasons.extend(_normalize_reason(raw) for raw in _dedupe(getattr(grounding_report, "rejection_reasons", None)))
        reasons.extend(_normalize_reason(raw) for raw in _dedupe(getattr(grounding_report, "binding_rejection_reasons", None)))
        diagnostics = getattr(grounding_report, "binding_diagnostics", None)
        if isinstance(diagnostics, Mapping):
            reasons.extend(_normalize_reason(raw) for raw in _dedupe(diagnostics.get("repair_targets")))
            if diagnostics.get("over_echo_count"):
                reasons.append(REPAIR_REASON_OVER_ECHO)
            if diagnostics.get("relation_not_expressed_count"):
                reasons.append(REPAIR_REASON_RELATION_NOT_EXPRESSED)
    if isinstance(gate_results, Mapping):
        for key in ("rejection_reasons", "reasons", "repair_targets", "failed_reasons"):
            reasons.extend(_normalize_reason(raw) for raw in _dedupe(gate_results.get(key)))
        if gate_results.get("template_like") or gate_results.get("same_ending_major_detected"):
            reasons.append(REPAIR_REASON_TEMPLATE_LIKE)
        if gate_results.get("raw_echo") or gate_results.get("over_echo"):
            reasons.append(REPAIR_REASON_RAW_ECHO)
        if gate_results.get("too_long"):
            reasons.append(REPAIR_REASON_TOO_LONG)
    if isinstance(meta, Mapping):
        for key in ("gate_reasons", "repair_targets", "rejection_reasons"):
            reasons.extend(_normalize_reason(raw) for raw in _dedupe(meta.get(key)))
    return tuple(reason for reason in _dedupe(reasons) if reason)


def _operation_for(reason: str) -> str:
    return {
        REPAIR_REASON_UNSUPPORTED_SENTENCE: "remove_optional_or_rebind_evidence",
        REPAIR_REASON_RELATION_NOT_EXPRESSED: "make_declared_relation_surface_explicit",
        REPAIR_REASON_TEMPLATE_LIKE: "vary_surface_signature_tail_connector_order",
        REPAIR_REASON_RAW_ECHO: "reduce_raw_echo_by_role_phrase_rephrase",
        REPAIR_REASON_OVER_ECHO: "reduce_raw_echo_by_role_phrase_rephrase",
        REPAIR_REASON_TOO_LONG: "remove_optional_or_shorten_closing",
        REPAIR_REASON_OVERCLAIM: "reject_or_remove_overclaim_optional_line",
        REPAIR_REASON_UNSUPPORTED_OVERCLAIM: "reject_or_remove_overclaim_optional_line",
    }.get(reason, "aborted_unknown_repair_reason")


def _contract_boundary() -> dict[str, Any]:
    return {
        "comment_text_contract": "passed_only",
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


def _source_policy() -> dict[str, Any]:
    return {
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "llm_generation_used": False,
        "fixed_sentence_template_used": False,
        "fixed_sentence_template_allowed": False,
        "fixed_fallback_used": False,
        "fixed_fallback_allowed": False,
        "completion_sentence_template_used": False,
        "input_specific_template_used": False,
    }


def build_complete_self_repair_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_SELF_REPAIR_VERSION,
        "service_version": COMPLETE_SELF_REPAIR_VERSION,
        "target_step": COMPLETE_SELF_REPAIR_STAGE,
        "step": COMPLETE_SELF_REPAIR_STAGE,
        "source_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "self_repair_loop_added": True,
        "self_repair_enabled": True,
        "max_repair_attempts": MAX_SELF_REPAIR_ATTEMPTS,
        "gate_relaxation_allowed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "display_gate_relaxed": False,
        "new_meaning_addition_allowed": False,
        "meaning_addition_allowed": False,
        "new_meaning_added": False,
        "must_include_deletion_allowed": False,
        "allowed_repair_reasons": sorted(ALLOWED_REPAIR_REASONS),
        "reject_preferred_reasons": sorted(REJECT_PREFERRED_REASONS),
        "allowed_operations": {
            REPAIR_REASON_UNSUPPORTED_SENTENCE: ["remove_optional_line", "rebind_to_existing_evidence"],
            REPAIR_REASON_RELATION_NOT_EXPRESSED: ["make_relation_explicit", "replace_connector"],
            REPAIR_REASON_TEMPLATE_LIKE: ["vary_tail", "vary_connector", "vary_surface_signature"],
            REPAIR_REASON_RAW_ECHO: ["reduce_quote_density", "role_phrase_rephrase"],
            REPAIR_REASON_OVER_ECHO: ["reduce_quote_density", "role_phrase_rephrase"],
            REPAIR_REASON_TOO_LONG: ["remove_optional_line", "shorten_closing"],
            REPAIR_REASON_OVERCLAIM: ["reject", "remove_optional_overclaim_line"],
            REPAIR_REASON_UNSUPPORTED_OVERCLAIM: ["reject", "remove_optional_overclaim_line"],
        },
        "forbidden_operations": sorted(FORBIDDEN_REPAIR_OPERATIONS),
        "repair_trace_required": True,
        "repair_trace_records_before_after_plan_id": True,
        "evidence_ids_must_remain_bound": True,
        "relation_ids_must_remain_bound": True,
        **_contract_boundary(),
        **_source_policy(),
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
    }


def _surface_signature_for_line(
    line: CompleteSurfaceLineV2,
    *,
    operation: str,
    attempt: int,
    connector_key: str | None = None,
    ending_key: str | None = None,
    variation_key: str | None = None,
) -> dict[str, Any]:
    signature = dict(line.surface_signature or {})
    new_connector = connector_key or line.connector_key
    new_ending = ending_key or line.ending_key or f"repair_tail_{attempt}"
    new_variation = variation_key or f"repair_v{attempt}"
    signature.update(
        {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SELF_REPAIR_STAGE,
            "sentence_id": line.sentence_id,
            "line_role": line.line_role,
            "relation_type": line.relation_type,
            "role_phrase_key": line.role_phrase_key,
            "connector_key": new_connector,
            "predicate_key": line.predicate_key,
            "ending_key": new_ending,
            "variation_key": new_variation,
            "repair_operation": operation,
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }
    )
    signature["signature"] = "|".join(
        _clean_token(signature.get(key))
        for key in ("line_role", "relation_type", "role_phrase_key", "connector_key", "predicate_key", "ending_key", "variation_key")
    )
    return signature


def _clone_line(
    line: CompleteSurfaceLineV2,
    *,
    surface_text: str | None = None,
    connector_key: str | None = None,
    ending_key: str | None = None,
    variation_key: str | None = None,
    evidence_span_ids: Iterable[str] | None = None,
    phrase_unit_ids: Iterable[str] | None = None,
    relation_type: str | None = None,
    operation: str = "self_repair_adjustment",
    attempt: int = 1,
) -> CompleteSurfaceLineV2:
    new_connector = connector_key or line.connector_key
    new_ending = ending_key or line.ending_key
    new_variation = variation_key or line.variation_key
    new_relation = relation_type or line.relation_type
    return CompleteSurfaceLineV2(
        sentence_id=line.sentence_id,
        line_role=line.line_role,
        relation_type=new_relation,
        surface_text=_clean(surface_text if surface_text is not None else line.surface_text),
        phrase_unit_ids=phrase_unit_ids if phrase_unit_ids is not None else line.phrase_unit_ids,
        evidence_span_ids=evidence_span_ids if evidence_span_ids is not None else line.evidence_span_ids,
        role_phrase_key=line.role_phrase_key,
        role_phrase_keys=line.role_phrase_keys,
        subject_policy_key=line.subject_policy_key,
        connector_key=new_connector,
        particle_key=line.particle_key,
        predicate_key=line.predicate_key,
        ending_key=new_ending,
        distance_policy_key=line.distance_policy_key,
        variation_key=new_variation,
        surface_signature=_surface_signature_for_line(
            line,
            operation=operation,
            attempt=attempt,
            connector_key=new_connector,
            ending_key=new_ending,
            variation_key=new_variation,
        ),
        forbidden_surface_keys=line.forbidden_surface_keys,
        source_sentence_plan_line=line.source_sentence_plan_line,
        meta={
            **_json_safe_mapping(line.meta),
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "self_repair_applied": True,
            "repair_operation": operation,
            "repair_attempt": attempt,
            "meaning_added": False,
            "raw_input_included": False,
        },
    )


def _rebuild_plan(original_plan: CompleteSentencePlanV2, surface_lines: Sequence[CompleteSurfaceLineV2], *, attempt: int, operation: str) -> CompleteSentencePlanV2:
    original_lines = _line_plan_map(original_plan)
    plan_lines: list[CompleteSentencePlanLine] = []
    for surface_line in surface_lines:
        source_line = original_lines.get(surface_line.sentence_id) or _plan_line_from_surface_line(surface_line)
        plan_lines.append(
            CompleteSentencePlanLine(
                sentence_id=source_line.sentence_id,
                line_role=source_line.line_role,
                relation_type=surface_line.relation_type or source_line.relation_type,
                focus_rank=source_line.focus_rank,
                phrase_unit_ids=surface_line.phrase_unit_ids or source_line.phrase_unit_ids,
                evidence_span_ids=surface_line.evidence_span_ids or source_line.evidence_span_ids,
                must_include_roles=source_line.must_include_roles,
                optional_roles=source_line.optional_roles,
                forbidden_surface_keys=source_line.forbidden_surface_keys,
                max_chars=source_line.max_chars,
                surface_intent=source_line.surface_intent,
                repair_policy=(*tuple(source_line.repair_policy), operation),
                meta={
                    **_json_safe_mapping(source_line.meta),
                    "source_step": COMPLETE_SELF_REPAIR_STAGE,
                    "repaired_from_plan_id": original_plan.plan_id,
                    "repair_attempt": attempt,
                    "repair_operation": operation,
                    "raw_input_included": False,
                },
            )
        )
    return CompleteSentencePlanV2(
        plan_id=f"{original_plan.plan_id}_repair{attempt}",
        sentence_budget=max(2, min(5, len(plan_lines) or 2)),
        coverage_group=original_plan.coverage_group,
        sentence_plans=plan_lines,
        meta={
            **_json_safe_mapping(original_plan.meta),
            "source_step": COMPLETE_SELF_REPAIR_STAGE,
            "repaired_from_plan_id": original_plan.plan_id,
            "repair_attempt": attempt,
            "repair_operation": operation,
            "new_meaning_added": False,
            "raw_input_included": False,
        },
    )


def _rebuild_realization(
    original: CompleteSurfaceRealizationV2,
    original_plan: CompleteSentencePlanV2,
    surface_lines: Sequence[CompleteSurfaceLineV2],
    *,
    attempt: int,
    operation: str,
) -> CompleteSurfaceRealizationV2:
    plan = _rebuild_plan(original_plan, surface_lines, attempt=attempt, operation=operation)
    status = COMPLETE_SURFACE_STATUS_READY if surface_lines else COMPLETE_SURFACE_STATUS_UNAVAILABLE
    return CompleteSurfaceRealizationV2(
        plan_id=plan.plan_id,
        coverage_group=original.coverage_group,
        surface_lines=tuple(surface_lines),
        source_sentence_plan=plan,
        status=status,
        meta={
            **_json_safe_mapping(original.meta),
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "self_repair_applied": True,
            "repair_attempt": attempt,
            "repair_operation": operation,
            "before_plan_id": original.plan_id,
            "after_plan_id": plan.plan_id,
            "comment_text_key_written": False,
            "response_shape_changed": False,
            "new_meaning_added": False,
            "raw_input_included": False,
        },
    )


def _remove_optional_lines(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
    reason: str,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    original_lines = list(realization.surface_lines)
    plan_map = _line_plan_map(plan)
    # Prefer dropping invalid optional rows first, then optional closing rows.
    removable: list[CompleteSurfaceLineV2] = []
    for line in original_lines:
        plan_line = plan_map.get(line.sentence_id)
        if _is_optional(plan_line, line) and (not _line_has_binding(line) or line.line_role == "closing" or reason == REPAIR_REASON_TOO_LONG):
            removable.append(line)
    for remove_line in removable:
        kept = [line for line in original_lines if line.sentence_id != remove_line.sentence_id]
        if len(kept) < 2:
            continue
        op = "remove_optional_line" if reason != REPAIR_REASON_TOO_LONG else "remove_optional_line_for_length"
        return _rebuild_realization(realization, plan, kept, attempt=attempt, operation=op), op, True
    return None, "remove_optional_line_unavailable", False


def _rebind_missing_evidence(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    rebind_ids: Sequence[str],
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    if not rebind_ids:
        return None, "rebind_evidence_unavailable", False
    changed = False
    rebuilt: list[CompleteSurfaceLineV2] = []
    plan_map = _line_plan_map(plan)
    for line in realization.surface_lines:
        plan_line = plan_map.get(line.sentence_id)
        if _is_must_include(plan_line, line) and not line.evidence_span_ids:
            rebuilt.append(_clone_line(line, evidence_span_ids=[rebind_ids[0]], operation="rebind_to_existing_evidence", attempt=attempt))
            changed = True
        else:
            rebuilt.append(line)
    if not changed:
        return None, "rebind_evidence_not_needed", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="rebind_to_existing_evidence"), "rebind_to_existing_evidence", True


def _make_relation_explicit(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    changed = False
    # Prefer relation line; otherwise use the first non-center line already bound to a declared relation.
    candidate_id = ""
    for line in realization.surface_lines:
        if line.line_role == "relation" and line.relation_type not in {"center", "context", "unknown", "neutral"}:
            candidate_id = line.sentence_id
            break
    if not candidate_id:
        for line in realization.surface_lines:
            if line.relation_type not in {"center", "context", "unknown", "neutral"}:
                candidate_id = line.sentence_id
                break
    for line in realization.surface_lines:
        if line.sentence_id != candidate_id:
            rebuilt.append(line)
            continue
        relation = _clean_token(line.relation_type) or "center"
        marker = RELATION_MARKER_PHRASES.get(relation) or "関係として同じ場所に置かれています。"
        text = _clean(line.surface_text)
        if marker.rstrip("。") in text:
            rebuilt.append(line)
            continue
        # Keep this a relation clarification, not a new claim: use the line's declared relation only.
        new_text = f"{text.rstrip('。')}。{marker}" if text else marker
        rebuilt.append(
            _clone_line(
                line,
                surface_text=new_text,
                connector_key=RELATION_CONNECTOR_KEYS.get(relation, "repair_relation_connector"),
                operation="make_declared_relation_surface_explicit",
                attempt=attempt,
            )
        )
        changed = True
    if not changed:
        return None, "relation_line_unavailable", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="make_declared_relation_surface_explicit"), "make_declared_relation_surface_explicit", True


def _vary_surface_signature(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    seen_tail: dict[str, int] = {}
    for index, line in enumerate(realization.surface_lines, start=1):
        base_tail = line.ending_key or "tail"
        seen_tail[base_tail] = seen_tail.get(base_tail, 0) + 1
        new_tail = f"repair_tail_{attempt}_{index}"
        new_variation = f"repair_v{attempt}_{index}"
        connector = line.connector_key
        if index > 1 and connector == "none":
            connector = f"repair_connector_{attempt}_{index}"
        rebuilt.append(
            _clone_line(
                line,
                connector_key=connector,
                ending_key=new_tail,
                variation_key=new_variation,
                operation="vary_surface_signature_tail_connector_order",
                attempt=attempt,
            )
        )
    if not rebuilt:
        return None, "surface_signature_rows_missing", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="vary_surface_signature_tail_connector_order"), "vary_surface_signature_tail_connector_order", True


def _role_phrase_for_line(line: CompleteSurfaceLineV2) -> str:
    relation = _clean_token(line.relation_type)
    if line.role_phrase_key and line.role_phrase_key not in {"unknown", "none"}:
        return line.role_phrase_key.replace("_", " ")
    return RELATION_ROLE_PHRASES.get(relation) or "根拠のある材料"


def _reduce_echo(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    for index, line in enumerate(realization.surface_lines, start=1):
        role_phrase = _role_phrase_for_line(line)
        relation = _clean_token(line.relation_type)
        if relation in RELATION_ROLE_PHRASES:
            text = f"{RELATION_ROLE_PHRASES[relation]}が、根拠のある範囲で置かれています。"
        else:
            text = f"{role_phrase}が、根拠のある範囲で置かれています。"
        rebuilt.append(
            _clone_line(
                line,
                surface_text=text,
                ending_key=f"repair_echo_tail_{attempt}_{index}",
                variation_key=f"repair_echo_v{attempt}_{index}",
                operation="reduce_raw_echo_by_role_phrase_rephrase",
                attempt=attempt,
            )
        )
    if not rebuilt:
        return None, "echo_repair_lines_missing", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="reduce_raw_echo_by_role_phrase_rephrase"), "reduce_raw_echo_by_role_phrase_rephrase", True


def _shorten_closing(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    changed = False
    for line in realization.surface_lines:
        if line.line_role == "closing":
            relation_phrase = RELATION_ROLE_PHRASES.get(_clean_token(line.relation_type), "根拠のある範囲")
            text = f"{relation_phrase}だけを、短く残しています。"
            rebuilt.append(_clone_line(line, surface_text=text, operation="shorten_closing", attempt=attempt))
            changed = True
        else:
            rebuilt.append(line)
    if not changed:
        return None, "closing_line_unavailable", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="shorten_closing"), "shorten_closing", True


def _remove_optional_overclaim_line(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    plan_map = _line_plan_map(plan)
    overclaim_re = re.compile(r"本当は|本当の願い|愛されたい|前向き|強い人|性格|診断|病気|治療|医療|弱さではなく")
    for line in realization.surface_lines:
        if overclaim_re.search(line.surface_text) and _is_optional(plan_map.get(line.sentence_id), line):
            kept = [item for item in realization.surface_lines if item.sentence_id != line.sentence_id]
            if len(kept) >= 2:
                return _rebuild_realization(realization, plan, kept, attempt=attempt, operation="remove_optional_overclaim_line"), "remove_optional_overclaim_line", True
    return None, "overclaim_reject_preferred", False


def _apply_one_repair(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    reason: str,
    attempt: int,
    rebind_ids: Sequence[str] = (),
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool, bool]:
    """Return (new_realization, operation, changed, reject_preferred)."""
    if reason == REPAIR_REASON_UNSUPPORTED_SENTENCE:
        repaired, op, changed = _remove_optional_lines(realization, plan, attempt=attempt, reason=reason)
        if changed:
            return repaired, op, True, False
        repaired, op, changed = _rebind_missing_evidence(realization, plan, rebind_ids=rebind_ids, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_RELATION_NOT_EXPRESSED:
        repaired, op, changed = _make_relation_explicit(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_TEMPLATE_LIKE:
        repaired, op, changed = _vary_surface_signature(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason in ECHO_REASONS:
        repaired, op, changed = _reduce_echo(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_TOO_LONG:
        repaired, op, changed = _remove_optional_lines(realization, plan, attempt=attempt, reason=reason)
        if changed:
            return repaired, op, True, False
        repaired, op, changed = _shorten_closing(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason in REJECT_PREFERRED_REASONS:
        repaired, op, changed = _remove_optional_overclaim_line(realization, plan, attempt=attempt)
        return repaired, op, changed, not changed
    return None, "unsupported_repair_reason", False, False


def _trace(
    *,
    attempt: int,
    reason: str,
    operation: str,
    before_plan_id: str,
    after_plan_id: str,
    result: str,
    source_gate: str = "grounding",
    meta: Mapping[str, Any] | None = None,
) -> RepairTrace:
    return RepairTrace(
        attempt=attempt,
        source_gate=source_gate,
        reason_code=reason,
        applied_operation=operation,
        before_plan_id=before_plan_id,
        after_plan_id=after_plan_id,
        evidence_ids_unchanged=True,
        relation_ids_unchanged=True,
        safety_level_unchanged=True,
        result=result,
        meta={
            "source_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "new_meaning_added": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            **_json_safe_mapping(meta),
        },
    )


@dataclass(frozen=True)
class CompleteSelfRepairResult:
    """Result object for the bounded Complete self-repair loop."""

    original_surface_realization: CompleteSurfaceRealizationV2
    repaired_surface_realization: CompleteSurfaceRealizationV2
    repair_trace: Iterable[RepairTrace] = dataclass_field(default_factory=tuple)
    gate_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    status: str = COMPLETE_SELF_REPAIR_STATUS_UNCHANGED
    rejection_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_SELF_REPAIR_VERSION

    def __post_init__(self) -> None:
        status = _clean_token(self.status) or COMPLETE_SELF_REPAIR_STATUS_UNCHANGED
        if status not in {
            COMPLETE_SELF_REPAIR_STATUS_REPAIRED,
            COMPLETE_SELF_REPAIR_STATUS_UNCHANGED,
            COMPLETE_SELF_REPAIR_STATUS_ABORTED,
            COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE,
        }:
            status = COMPLETE_SELF_REPAIR_STATUS_ABORTED
        traces = tuple(item if isinstance(item, RepairTrace) else _trace(attempt=1, reason="unknown", operation="unknown", before_plan_id="", after_plan_id="", result="aborted") for item in tuple(self.repair_trace or ()))
        object.__setattr__(self, "repair_trace", traces)
        object.__setattr__(self, "gate_reasons", _dedupe(self.gate_reasons))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "rejection_reasons", _dedupe(self.rejection_reasons))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_SELF_REPAIR_VERSION)

    @property
    def repaired(self) -> bool:
        return self.status == COMPLETE_SELF_REPAIR_STATUS_REPAIRED

    @property
    def aborted(self) -> bool:
        return self.status == COMPLETE_SELF_REPAIR_STATUS_ABORTED

    @property
    def ready(self) -> bool:
        return self.repaired_surface_realization.ready

    @property
    def comment_text(self) -> str:
        # Internal candidate text only. Step 11/Display Gate controls public key.
        return self.repaired_surface_realization.comment_text

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return self.repaired_surface_realization.used_evidence_span_ids

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return self.repaired_surface_realization.used_phrase_unit_ids

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return self.repaired_surface_realization.relation_types

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors = list(self.repaired_surface_realization.validation_errors)
        for trace in self.repair_trace:
            errors.extend(trace.validation_errors)
        return tuple(dict.fromkeys(errors))

    def as_grounding_input(self) -> dict[str, Any]:
        payload = self.repaired_surface_realization.as_grounding_input()
        payload.update(
            {
                "source_step": COMPLETE_SELF_REPAIR_STAGE,
                "target_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
                "repair_trace": [trace.as_meta() for trace in self.repair_trace],
                "self_repair_applied": self.repaired,
                "comment_text_key_written": False,
                "response_shape_changed": False,
                "raw_input_included": False,
            }
        )
        return payload

    def as_meta(self, *, include_realized_text: bool = True) -> dict[str, Any]:
        term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
        repaired_meta = self.repaired_surface_realization.as_meta(include_realized_text=include_realized_text)
        surface_signature = build_complete_surface_signature(self.repaired_surface_realization)
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "service_version": COMPLETE_SELF_REPAIR_VERSION,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "step": COMPLETE_SELF_REPAIR_STAGE,
            "source_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
            "stage": COMPLETE_COMPOSER_STAGE,
            "implementation_unit": COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT,
            "target_composer_term": term_meta["target_composer_term"],
            "target_composer_family_term": term_meta["target_composer_family_term"],
            "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
            "status": self.status,
            "repaired": self.repaired,
            "ready": self.ready,
            "aborted": self.aborted,
            "attempt_count": len(self.repair_trace),
            "max_repair_attempts": MAX_SELF_REPAIR_ATTEMPTS,
            "gate_reasons": list(self.gate_reasons),
            "rejection_reasons": list(self.rejection_reasons),
            "before_plan_id": self.original_surface_realization.plan_id,
            "after_plan_id": self.repaired_surface_realization.plan_id,
            "before_surface_line_count": len(self.original_surface_realization.surface_lines),
            "after_surface_line_count": len(self.repaired_surface_realization.surface_lines),
            "repair_trace": [trace.as_meta() for trace in self.repair_trace],
            "repaired_surface_meta": repaired_meta,
            "surface_signature": surface_signature,
            "surface_signature_changed": build_complete_surface_signature(self.original_surface_realization).get("surface_signatures") != surface_signature.get("surface_signatures"),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "new_meaning_added": False,
            "meaning_addition_allowed": False,
            "gate_relaxation_allowed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "display_gate_relaxed": False,
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "comment_text_publicly_assigned": False,
            "comment_text_contract": "passed_only",
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "fixed_sentence_template_used": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_improvement": False,
            "validation_errors": list(self.validation_errors),
            "meta": dict(self.meta),
        }


def run_complete_self_repair_loop(
    *,
    surface_realization: CompleteSurfaceRealizationV2 | Mapping[str, Any] | None = None,
    grounding_report: Any = None,
    gate_reasons: Iterable[str] | str | None = None,
    gate_results: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    allowed_evidence_span_ids: Sequence[str] | None = None,
    max_attempts: int = MAX_SELF_REPAIR_ATTEMPTS,
    meta: Mapping[str, Any] | None = None,
    **surface_kwargs: Any,
) -> CompleteSelfRepairResult:
    original = _coerce_surface_realization(surface_realization, **surface_kwargs)
    if not original.surface_lines:
        reason_tuple = _reasons_from_gate_input(gate_reasons, grounding_report, gate_results, meta)
        return CompleteSelfRepairResult(
            original_surface_realization=original,
            repaired_surface_realization=original,
            repair_trace=(),
            gate_reasons=reason_tuple,
            status=COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE,
            rejection_reasons=("surface_lines_missing",),
            meta={**build_complete_self_repair_contract_meta(), **_json_safe_mapping(meta)},
        )

    plan = _source_plan_for(original)
    reasons = _reasons_from_gate_input(gate_reasons, grounding_report, gate_results, meta)
    if not reasons:
        return CompleteSelfRepairResult(
            original_surface_realization=original,
            repaired_surface_realization=original,
            repair_trace=(),
            gate_reasons=(),
            status=COMPLETE_SELF_REPAIR_STATUS_UNCHANGED,
            rejection_reasons=(),
            meta={**build_complete_self_repair_contract_meta(), **_json_safe_mapping(meta), "reason": "no_repair_target"},
        )

    attempts_allowed = max(0, min(MAX_SELF_REPAIR_ATTEMPTS, int(max_attempts or MAX_SELF_REPAIR_ATTEMPTS)))
    current = original
    current_plan = plan
    traces: list[RepairTrace] = []
    blocked: list[str] = []
    rebind_ids = _allowed_rebind_ids(allowed_evidence_span_ids, getattr(grounding_report, "allowed_evidence_span_ids", None), evidence_spans)

    for reason in reasons:
        if len(traces) >= attempts_allowed:
            blocked.append("max_repair_attempts_reached")
            break
        if reason not in ALLOWED_REPAIR_REASONS:
            blocked.append(f"repair_reason_not_allowed:{reason}")
            continue
        before_plan_id = current.plan_id
        repaired, operation, changed, reject_preferred = _apply_one_repair(
            current,
            current_plan,
            reason=reason,
            attempt=len(traces) + 1,
            rebind_ids=rebind_ids,
        )
        if reject_preferred:
            traces.append(
                _trace(
                    attempt=len(traces) + 1,
                    reason=reason,
                    operation=operation,
                    before_plan_id=before_plan_id,
                    after_plan_id=before_plan_id,
                    result="aborted",
                    source_gate="overclaim",
                    meta={"reject_preferred": True},
                )
            )
            blocked.append(operation)
            break
        if not changed or repaired is None:
            traces.append(
                _trace(
                    attempt=len(traces) + 1,
                    reason=reason,
                    operation=operation,
                    before_plan_id=before_plan_id,
                    after_plan_id=before_plan_id,
                    result="aborted",
                    meta={"repair_unavailable": True},
                )
            )
            blocked.append(operation)
            continue
        current = repaired
        current_plan = _source_plan_for(current)
        traces.append(
            _trace(
                attempt=len(traces) + 1,
                reason=reason,
                operation=operation,
                before_plan_id=before_plan_id,
                after_plan_id=current.plan_id,
                result="passed" if current.ready else "failed",
            )
        )

    if any(trace.result == "passed" for trace in traces):
        status = COMPLETE_SELF_REPAIR_STATUS_REPAIRED
    elif any(reason in REJECT_PREFERRED_REASONS for reason in reasons) or blocked:
        status = COMPLETE_SELF_REPAIR_STATUS_ABORTED
    else:
        status = COMPLETE_SELF_REPAIR_STATUS_UNCHANGED

    return CompleteSelfRepairResult(
        original_surface_realization=original,
        repaired_surface_realization=current,
        repair_trace=tuple(traces),
        gate_reasons=reasons,
        status=status,
        rejection_reasons=tuple(blocked),
        meta={
            **build_complete_self_repair_contract_meta(),
            **_json_safe_mapping(meta),
            "allowed_rebind_evidence_span_ids": list(rebind_ids),
            "blocked_reasons": list(blocked),
        },
    )


def build_complete_self_repair_result(**kwargs: Any) -> CompleteSelfRepairResult:
    return run_complete_self_repair_loop(**kwargs)


def build_complete_self_repair_loop(**kwargs: Any) -> CompleteSelfRepairResult:
    return run_complete_self_repair_loop(**kwargs)


def build_complete_self_repair_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return run_complete_self_repair_loop(**kwargs).as_meta(include_realized_text=include_realized_text)


def build_complete_self_repair_loop_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return build_complete_self_repair_meta(include_realized_text=include_realized_text, **kwargs)


def build_complete_repair_trace_meta(**kwargs: Any) -> list[dict[str, Any]]:
    return [trace.as_meta() for trace in run_complete_self_repair_loop(**kwargs).repair_trace]


CompleteSelfRepairLoopResult = CompleteSelfRepairResult
CompleteSelfRepairControllerResult = CompleteSelfRepairResult

__all__ = [
    "COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT",
    "COMPLETE_SELF_REPAIR_SERVICE_VERSION",
    "COMPLETE_SELF_REPAIR_STAGE",
    "COMPLETE_SELF_REPAIR_STATUS_ABORTED",
    "COMPLETE_SELF_REPAIR_STATUS_REPAIRED",
    "COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE",
    "COMPLETE_SELF_REPAIR_STATUS_UNCHANGED",
    "COMPLETE_SELF_REPAIR_STEP",
    "COMPLETE_SELF_REPAIR_TARGET_STEP",
    "COMPLETE_SELF_REPAIR_VERSION",
    "CompleteSelfRepairControllerResult",
    "CompleteSelfRepairLoopResult",
    "CompleteSelfRepairResult",
    "build_complete_repair_trace_meta",
    "build_complete_self_repair_contract_meta",
    "build_complete_self_repair_loop",
    "build_complete_self_repair_loop_meta",
    "build_complete_self_repair_meta",
    "build_complete_self_repair_result",
    "run_complete_self_repair_loop",
]
