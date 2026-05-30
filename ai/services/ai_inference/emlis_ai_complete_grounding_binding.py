# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 8 Binding-aware Grounding bridge for Complete Composer initial version.

The bridge converts Complete SentencePlan v2 / Surface Realizer 2.0 internal
meta into the binding rows consumed by ``emlis_ai_grounding_judge``.  It is
additive only: it does not write public ``input_feedback.comment_text`` and does
not change DB physical names, API routes, response keys, or RN display rules.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_STAGE, CompleteSentencePlanV2
from emlis_ai_complete_sentence_planner import COMPLETE_SENTENCE_PLAN_STAGE, build_complete_sentence_binding_bundle_meta
from emlis_ai_complete_surface_realizer import COMPLETE_SURFACE_REALIZER_STAGE, CompleteSurfaceRealizationV2
from emlis_ai_grounding_judge import (
    _COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
    _COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
    _COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
    judge_grounding,
)
from emlis_ai_types import EvidenceSpan, GroundingReport, ObservationGraph

COMPLETE_BINDING_AWARE_GROUNDING_VERSION = _COMPLETE_BINDING_AWARE_GROUNDING_VERSION
COMPLETE_BINDING_AWARE_GROUNDING_SERVICE_VERSION = COMPLETE_BINDING_AWARE_GROUNDING_VERSION
COMPLETE_BINDING_AWARE_GROUNDING_STAGE = "Step8_Binding_aware_Grounding"
COMPLETE_BINDING_AWARE_GROUNDING_STEP = COMPLETE_BINDING_AWARE_GROUNDING_STAGE
COMPLETE_BINDING_AWARE_GROUNDING_TARGET_STEP = COMPLETE_BINDING_AWARE_GROUNDING_STAGE
COMPLETE_BINDING_AWARE_GROUNDING_IMPLEMENTATION_UNIT = "Commit 8"
COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION = _COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION
COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP = _COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP
GATE_BINDING_CONTRACT_VERSION = "emlis.gate_binding_contract.v2"

PHASE17_6_GROUNDING_RELATION_BINDING_SCHEMA_VERSION = "cocolon.emlis_two_stage.grounding_binding_patch.v1"
PHASE17_6_GROUNDING_RELATION_BINDING_SOURCE_PHASE = "Phase17_6_grounding_relation_binding"
PHASE17_6_EFFORT_PACE_CASE_FAMILY = "effort_pace_context"
PHASE17_6_EFFORT_PACE_TARGET_MODES: Tuple[str, ...] = ("standard_state_answer", "effort_support")
PHASE17_6_EFFORT_PACE_BINDING_ROLES: Tuple[str, ...] = (
    "independence_intention",
    "life_context",
    "health_pace",
    "money_context",
    "sustainable_pace",
    "effort_pace_observation_independence_life_health_money",
    "effort_pace_reception_sustainable_pace_received",
    "effort_pace_reception_not_overeffort_received",
)
PHASE17_6_ALLOWED_RELATION_MARKER_CODES: Tuple[str, ...] = (
    "coexistence_narabimasu",
    "coexistence_isshoni_nokoru",
    "context_mi_nagara",
    "sustainable_pace_shape",
)
PHASE17_6_FORBIDDEN_RELATION_MARKER_CODES: Tuple[str, ...] = (
    "future_guarantee_jiritsu_dekimasu",
    "cause_assertion_money",
    "overeffort_directive",
)

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


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


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
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        text_key = _clean(key)
        if not text_key or text_key in RAW_INPUT_META_KEYS:
            continue
        out[text_key] = _json_safe_value(item)
    return out


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, CompleteSurfaceRealizationV2):
        return value.as_grounding_input()
    if isinstance(value, CompleteSentencePlanV2):
        return value.as_meta()
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "as_grounding_input"):
        try:
            mapped = value.as_grounding_input()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        except Exception:
            return {}
    if hasattr(value, "as_meta"):
        try:
            mapped = value.as_meta()
            if isinstance(mapped, Mapping):
                return dict(mapped)
        except Exception:
            return {}
    return {}


def _surface_rows_from_input(grounding_input: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(list(grounding_input.get("surface_lines") or grounding_input.get("lines") or ()), start=1):
        row = _as_mapping(item)
        if not row:
            continue
        surface_text = _clean(row.get("surface_text") or row.get("text") or row.get("sentence"))
        sentence_id = _clean(row.get("sentence_id") or row.get("id") or f"complete-s{index}")
        source_sentence_plan_line = _json_safe_mapping(row.get("source_sentence_plan_line") or {})
        role_values = _dedupe(
            row.get("phrase_unit_roles")
            or row.get("role_phrase_keys")
            or row.get("must_include_roles")
            or source_sentence_plan_line.get("must_include_roles")
            or source_sentence_plan_line.get("phrase_unit_roles")
            or row.get("role_phrase_key")
        )
        polarity_values = _dedupe(
            row.get("phrase_unit_polarities")
            or row.get("polarities")
            or row.get("polarity")
            or source_sentence_plan_line.get("phrase_unit_polarities")
        )
        rows.append(
            {
                "version": row.get("version") or row.get("schema_version") or "emlis.complete_surface_line.v2",
                "sentence_id": sentence_id,
                "text": surface_text,
                "surface_text": surface_text,
                "line_role": _clean(row.get("line_role") or row.get("role") or "core"),
                "relation_type": _clean(row.get("relation_type") or row.get("relation") or row.get("declared_relation_type")),
                "used_evidence_span_ids": list(_dedupe(row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or row.get("declared_evidence_span_ids"))),
                "used_phrase_unit_ids": list(_dedupe(row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or row.get("declared_phrase_unit_ids"))),
                "role_phrase_key": _clean(row.get("role_phrase_key")),
                "role_phrase_keys": list(_dedupe(row.get("role_phrase_keys") or role_values)),
                "phrase_unit_roles": list(role_values),
                "phrase_unit_polarities": list(polarity_values),
                "source_sentence_plan_line": source_sentence_plan_line,
                "relation_expression_required": bool(row.get("relation_expression_required")) or _clean(row.get("line_role") or row.get("role")) == "relation",
                "surface_signature": _json_safe_mapping(row.get("surface_signature") or {}),
                "source_step": row.get("source_step") or COMPLETE_SURFACE_REALIZER_STAGE,
                "target_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
                "raw_input_included": False,
            }
        )
    return rows


def _plan_rows_from_sentence_plan(sentence_plan: Any) -> list[dict[str, Any]]:
    if not sentence_plan:
        return []
    if isinstance(sentence_plan, CompleteSentencePlanV2):
        bundle = sentence_plan.as_sentence_binding_bundle_meta()
    elif isinstance(sentence_plan, Mapping):
        if sentence_plan.get("bindings") or sentence_plan.get("sentence_bindings"):
            bundle = sentence_plan
        else:
            bundle = build_complete_sentence_binding_bundle_meta(sentence_plan)
    else:
        return []
    rows = []
    for item in list(bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items") or ()):  # type: ignore[union-attr]
        row = _as_mapping(item)
        if row:
            phrase_roles = _dedupe(row.get("must_include_roles") or row.get("phrase_unit_roles") or row.get("role_phrase_keys"))
            phrase_polarities = _dedupe(row.get("phrase_unit_polarities") or row.get("polarities") or row.get("polarity"))
            rows.append(
                {
                    "sentence_id": _clean(row.get("sentence_id") or row.get("id")),
                    "line_role": _clean(row.get("line_role") or row.get("role") or "core"),
                    "relation_type": _clean(row.get("relation_type") or row.get("relation") or row.get("declared_relation_type")),
                    "used_evidence_span_ids": list(_dedupe(row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or row.get("declared_evidence_span_ids"))),
                    "used_phrase_unit_ids": list(_dedupe(row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or row.get("declared_phrase_unit_ids"))),
                    "role_phrase_key": _clean(row.get("role_phrase_key")),
                    "role_phrase_keys": list(_dedupe(row.get("role_phrase_keys") or phrase_roles)),
                    "phrase_unit_roles": list(phrase_roles),
                    "phrase_unit_polarities": list(phrase_polarities),
                    "source_sentence_plan_line": _json_safe_mapping(row),
                    "relation_expression_required": _clean(row.get("line_role") or row.get("role")) == "relation",
                    "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
                    "target_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
                    "raw_input_included": False,
                }
            )
    return rows


def _merge_rows(surface_rows: Sequence[Mapping[str, Any]], plan_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in list(plan_rows) + list(surface_rows):
        sentence_id = _clean(row.get("sentence_id") or row.get("id")) or f"complete-s{len(by_id) + 1}"
        current = dict(by_id.get(sentence_id) or {"sentence_id": sentence_id})
        for key, value in row.items():
            if value not in (None, "", [], (), {}):
                current[key] = _json_safe_value(value)
        current.setdefault("target_step", COMPLETE_BINDING_AWARE_GROUNDING_STAGE)
        current.setdefault("raw_input_included", False)
        by_id[sentence_id] = current
    return list(by_id.values())


def _joined_text(rows: Sequence[Mapping[str, Any]]) -> str:
    return "".join(_clean(row.get("surface_text") or row.get("text") or row.get("sentence")) for row in rows)


def _row_relation_type(row: Mapping[str, Any]) -> str:
    return _clean(row.get("relation_type") or row.get("relation") or row.get("declared_relation_type")).lower()


def _phase17_6_row_tokens(row: Mapping[str, Any]) -> Tuple[str, ...]:
    source_line = _json_safe_mapping(row.get("source_sentence_plan_line") or {})
    source_meta = _json_safe_mapping(source_line.get("meta") or {})
    return _dedupe(
        list(_as_list(row.get("role_phrase_keys")))
        + list(_as_list(row.get("phrase_unit_roles")))
        + list(_as_list(row.get("must_include_roles")))
        + list(_as_list(source_line.get("role_phrase_keys")))
        + list(_as_list(source_line.get("phrase_unit_roles")))
        + list(_as_list(source_line.get("must_include_roles")))
        + list(_as_list(source_meta.get("two_stage_mode_specific_surface_feature_families")))
        + list(_as_list(source_meta.get("two_stage_mode_specific_surface_key")))
    )


def _phase17_6_row_mode_id(row: Mapping[str, Any]) -> str:
    source_line = _json_safe_mapping(row.get("source_sentence_plan_line") or {})
    source_meta = _json_safe_mapping(source_line.get("meta") or {})
    return _clean(
        row.get("two_stage_reception_mode_id")
        or row.get("reception_mode_id")
        or source_line.get("two_stage_reception_mode_id")
        or source_meta.get("two_stage_reception_mode_id")
        or source_meta.get("two_stage_mode_specific_surface_mode_id")
    )


def _phase17_6_is_effort_pace_row(row: Mapping[str, Any]) -> bool:
    relation = _row_relation_type(row)
    if relation and relation not in {"coexistence", "context", "recovery"}:
        return False
    mode_id = _phase17_6_row_mode_id(row)
    if mode_id in PHASE17_6_EFFORT_PACE_TARGET_MODES:
        return True
    tokens = set(_phase17_6_row_tokens(row))
    if tokens.intersection(PHASE17_6_EFFORT_PACE_BINDING_ROLES):
        return True
    return any(token.startswith("effort_pace_") for token in tokens)


def _annotate_phase17_6_grounding_relation_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    for row in rows:
        next_row = dict(row)
        if _phase17_6_is_effort_pace_row(next_row):
            next_row.update(
                {
                    "phase17_6_grounding_relation_binding_applied": True,
                    "phase17_6_grounding_relation_binding_schema_version": PHASE17_6_GROUNDING_RELATION_BINDING_SCHEMA_VERSION,
                    "phase17_6_grounding_relation_binding_source_phase": PHASE17_6_GROUNDING_RELATION_BINDING_SOURCE_PHASE,
                    "phase17_6_grounding_relation_binding_case_family": PHASE17_6_EFFORT_PACE_CASE_FAMILY,
                    "phase17_6_grounding_relation_binding_target_modes": list(PHASE17_6_EFFORT_PACE_TARGET_MODES),
                    "phase17_6_grounding_relation_binding_roles": list(PHASE17_6_EFFORT_PACE_BINDING_ROLES),
                    "phase17_6_allowed_relation_marker_codes": list(PHASE17_6_ALLOWED_RELATION_MARKER_CODES),
                    "phase17_6_forbidden_relation_marker_codes": list(PHASE17_6_FORBIDDEN_RELATION_MARKER_CODES),
                    "relation_expression_required": True,
                    "unsupported_sentence_allowed": False,
                    "relation_not_expressed_allowed": False,
                    "grounding_gate_relaxed": False,
                    "display_gate_relaxed": False,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                }
            )
        annotated.append(next_row)
    return annotated


def _phase17_6_grounding_relation_binding_summary(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    applied_rows = [dict(row) for row in rows if bool(row.get("phase17_6_grounding_relation_binding_applied"))]
    sentence_ids = _dedupe(row.get("sentence_id") or row.get("id") for row in applied_rows)
    relation_types = _dedupe(row.get("relation_type") or row.get("declared_relation_type") for row in applied_rows)
    return {
        "schema_version": PHASE17_6_GROUNDING_RELATION_BINDING_SCHEMA_VERSION,
        "source_phase": PHASE17_6_GROUNDING_RELATION_BINDING_SOURCE_PHASE,
        "applied": bool(applied_rows),
        "case_family": PHASE17_6_EFFORT_PACE_CASE_FAMILY if applied_rows else "",
        "target_modes": list(PHASE17_6_EFFORT_PACE_TARGET_MODES),
        "binding_roles": list(PHASE17_6_EFFORT_PACE_BINDING_ROLES),
        "allowed_relation_marker_codes": list(PHASE17_6_ALLOWED_RELATION_MARKER_CODES),
        "forbidden_relation_marker_codes": list(PHASE17_6_FORBIDDEN_RELATION_MARKER_CODES),
        "row_count": len(applied_rows),
        "sentence_ids": list(sentence_ids),
        "relation_expression_required_sentence_ids": list(sentence_ids),
        "relation_types": list(relation_types),
        "unsupported_sentence_allowed": False,
        "relation_not_expressed_allowed": False,
        "grounding_gate_relaxed": False,
        "display_gate_relaxed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }


def build_complete_grounding_binding_bundle(
    *,
    grounding_input: Mapping[str, Any] | CompleteSurfaceRealizationV2 | None = None,
    surface_realization: Mapping[str, Any] | CompleteSurfaceRealizationV2 | None = None,
    sentence_plan: Mapping[str, Any] | CompleteSentencePlanV2 | None = None,
    comment_text: str | None = None,
    coverage_group: str | None = None,
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    grounding = _as_mapping(surface_realization or grounding_input)
    if isinstance(grounding_input, Mapping) and not grounding:
        grounding = dict(grounding_input)
    source_plan = sentence_plan or grounding.get("source_sentence_binding_bundle") or grounding.get("sentence_plan")
    surface_rows = _surface_rows_from_input(grounding)
    plan_rows = _plan_rows_from_sentence_plan(source_plan)
    rows = _annotate_phase17_6_grounding_relation_rows(_merge_rows(surface_rows, plan_rows))
    phase17_6_relation_binding = _phase17_6_grounding_relation_binding_summary(rows)
    text = _clean(comment_text) or _clean(grounding.get("realized_text")) or _joined_text(rows)
    used_evidence = _dedupe(item for row in rows for item in (row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or ()))
    used_phrase = _dedupe(item for row in rows for item in (row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or ()))
    relation_types = _dedupe(row.get("relation_type") or row.get("declared_relation_type") for row in rows)
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
        "service_version": COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
        "product_quality_grounding_version": COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
        "product_quality_grounding_step": COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
        "grounding_report_contract_version": COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
        "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
        "target_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
        "step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_BINDING_AWARE_GROUNDING_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "complete_binding_aware_grounding": True,
        "product_quality_grounding": True,
        "grounding_relation_binding_v2": True,
        "phase17_6_grounding_relation_binding": phase17_6_relation_binding,
        "phase17_6_grounding_relation_binding_applied": bool(phase17_6_relation_binding.get("applied")),
        "phase17_6_grounding_relation_binding_schema_version": PHASE17_6_GROUNDING_RELATION_BINDING_SCHEMA_VERSION,
        "phase17_6_grounding_relation_binding_source_phase": PHASE17_6_GROUNDING_RELATION_BINDING_SOURCE_PHASE,
        "step8_binding_aware_grounding": True,
        "complete_binding_required": True,
        "binding_required": True,
        "require_sentence_id": True,
        "require_evidence_span_ids": True,
        "require_phrase_unit_ids": True,
        "require_relation_type": True,
        "relation_expression_checker": True,
        "relation_expression_checked": True,
        "phrase_unit_quality_checked": True,
        "binding_support_source_required": True,
        "binding_count": len(rows),
        "sentence_binding_count": len(rows),
        "expected_binding_count": len(rows),
        "binding_present": bool(rows),
        "binding_missing": not bool(rows),
        "coverage_group": _clean(coverage_group) or _clean(grounding.get("coverage_group")) or "unknown",
        "plan_id": _clean(grounding.get("plan_id")) or _clean(getattr(sentence_plan, "plan_id", "")) or "complete_grounding_plan",
        "realized_text": text,
        "comment_text_present": bool(text),
        "comment_text_publicly_assigned": False,
        "comment_text_key_written": False,
        "comment_text_contract": "passed_only",
        "used_evidence_span_ids": list(used_evidence),
        "used_phrase_unit_ids": list(used_phrase),
        "relation_types": list(relation_types),
        "bindings": rows,
        "sentence_bindings": rows,
        "items": rows,
        "surface_lines": rows,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
        "grounding_gate_relaxed": False,
        "display_gate_relaxed": False,
        "phase17_6_grounding_gate_relaxed": False,
        "phase17_6_relation_not_expressed_allowed": False,
        "phase17_6_unsupported_sentence_allowed": False,
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_debug": False,
        "meta": _json_safe_mapping(meta),
    }


def judge_complete_binding_aware_grounding(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    comment_text: str | None = None,
    grounding_input: Mapping[str, Any] | CompleteSurfaceRealizationV2 | None = None,
    surface_realization: Mapping[str, Any] | CompleteSurfaceRealizationV2 | None = None,
    sentence_plan: Mapping[str, Any] | CompleteSentencePlanV2 | None = None,
    allowed_evidence_span_ids: Sequence[str] | None = None,
    coverage_group: str | None = None,
    meta: Mapping[str, Any] | None = None,
) -> GroundingReport:
    bundle = build_complete_grounding_binding_bundle(
        grounding_input=grounding_input,
        surface_realization=surface_realization,
        sentence_plan=sentence_plan,
        comment_text=comment_text,
        coverage_group=coverage_group,
        meta=meta,
    )
    text = _clean(comment_text) or _clean(bundle.get("realized_text"))
    return judge_grounding(
        comment_text=text,
        graph=graph,
        evidence_spans=evidence_spans,
        allowed_evidence_span_ids=allowed_evidence_span_ids,
        grounding_scope="complete_initial_binding_aware",
        binding_meta=bundle,
    )


def build_complete_binding_aware_grounding_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
        "service_version": COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
        "product_quality_grounding_version": COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
        "product_quality_grounding_step": COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP,
        "grounding_report_contract_version": COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION,
        "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
        "target_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
        "step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
        "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_BINDING_AWARE_GROUNDING_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "accepts_complete_sentence_plan_v2": True,
        "accepts_complete_surface_realizer_v2_grounding_input": True,
        "sentence_id_required": True,
        "used_evidence_span_ids_required": True,
        "used_phrase_unit_ids_required": True,
        "relation_type_required": True,
        "relation_expression_checker": True,
        "relation_expression_checked": True,
        "binding_support_source_required": True,
        "unsupported_sentence_ids_reported": True,
        "relation_not_expressed_sentence_ids_reported": True,
        "phase17_6_grounding_relation_binding_schema_version": PHASE17_6_GROUNDING_RELATION_BINDING_SCHEMA_VERSION,
        "phase17_6_grounding_relation_binding_source_phase": PHASE17_6_GROUNDING_RELATION_BINDING_SOURCE_PHASE,
        "phase17_6_effort_pace_relation_binding_supported": True,
        "phase17_6_effort_pace_target_modes": list(PHASE17_6_EFFORT_PACE_TARGET_MODES),
        "phase17_6_effort_pace_binding_roles": list(PHASE17_6_EFFORT_PACE_BINDING_ROLES),
        "phase17_6_allowed_relation_marker_codes": list(PHASE17_6_ALLOWED_RELATION_MARKER_CODES),
        "phase17_6_forbidden_relation_marker_codes": list(PHASE17_6_FORBIDDEN_RELATION_MARKER_CODES),
        "phase17_6_unsupported_sentence_allowed": False,
        "phase17_6_relation_not_expressed_allowed": False,
        "phrase_unit_quality_checked": True,
        "weak_material_reason_enabled": True,
        "binding_pass_rate_measurable": True,
        "unsupported_sentence_release_blocker": True,
        "relation_not_expressed_repair_target": True,
        "over_echo_repair_target": True,
        "overclaim_reject_preferred": True,
        "comment_text_contract": "passed_only",
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
        "grounding_gate_relaxed": False,
        "display_gate_relaxed": False,
        "raw_input_included": False,
    }


build_complete_grounding_binding_meta = build_complete_grounding_binding_bundle
build_complete_binding_aware_grounding_meta = build_complete_grounding_binding_bundle
judge_complete_grounding_binding = judge_complete_binding_aware_grounding

__all__ = [
    "COMPLETE_BINDING_AWARE_GROUNDING_VERSION",
    "COMPLETE_BINDING_AWARE_GROUNDING_SERVICE_VERSION",
    "COMPLETE_BINDING_AWARE_GROUNDING_STAGE",
    "COMPLETE_BINDING_AWARE_GROUNDING_STEP",
    "COMPLETE_BINDING_AWARE_GROUNDING_TARGET_STEP",
    "COMPLETE_BINDING_AWARE_GROUNDING_IMPLEMENTATION_UNIT",
    "COMPLETE_PRODUCT_QUALITY_GROUNDING_VERSION",
    "COMPLETE_PRODUCT_QUALITY_GROUNDING_STEP",
    "GATE_BINDING_CONTRACT_VERSION",
    "PHASE17_6_GROUNDING_RELATION_BINDING_SCHEMA_VERSION",
    "PHASE17_6_GROUNDING_RELATION_BINDING_SOURCE_PHASE",
    "PHASE17_6_EFFORT_PACE_CASE_FAMILY",
    "PHASE17_6_EFFORT_PACE_TARGET_MODES",
    "PHASE17_6_EFFORT_PACE_BINDING_ROLES",
    "PHASE17_6_ALLOWED_RELATION_MARKER_CODES",
    "PHASE17_6_FORBIDDEN_RELATION_MARKER_CODES",
    "build_complete_grounding_binding_bundle",
    "build_complete_grounding_binding_meta",
    "build_complete_binding_aware_grounding_meta",
    "build_complete_binding_aware_grounding_contract_meta",
    "judge_complete_binding_aware_grounding",
    "judge_complete_grounding_binding",
]
