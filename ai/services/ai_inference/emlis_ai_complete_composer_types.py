# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal type contracts for EmlisAI Complete Composer initial version.

Step 2 is additive/type-only.  The classes in this module describe the
Complete Composer candidate, SentencePlan v2, and repair trace contracts that
later services can consume.  They do not rename DB tables, API routes, public
response keys, or the RN visible contract.
"""

from dataclasses import dataclass, field as dataclass_field
import re
from typing import Any, Iterable, Mapping, Tuple

from emlis_ai_complete_composer_initial_meta import (
    COMPLETE_COMPOSER_INITIAL_MODEL,
    build_complete_composer_initial_term_meta,
)

COMPLETE_TYPES_CONTRACT_VERSION = "emlis.complete_composer_initial.types_contract.v1"
COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION = "emlis.complete_composer.response.v1"
COMPLETE_COMPOSER_CANDIDATE_SCHEMA_VERSION = COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION
COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION = "emlis.complete_sentence_plan.v2"
COMPLETE_SENTENCE_PLAN_V2_SCHEMA_VERSION = COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION
COMPLETE_SENTENCE_PLAN_LINE_SCHEMA_VERSION = "emlis.complete_sentence_plan_line.v2"
COMPLETE_REPAIR_TRACE_SCHEMA_VERSION = "emlis.complete_repair_trace.v1"
COMPLETE_REPAIR_TRACE_V2_SCHEMA_VERSION = "emlis.complete_repair_trace.v2"
COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION = COMPLETE_REPAIR_TRACE_V2_SCHEMA_VERSION
COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION = "emlis.sentence_binding_bundle.v1"
COMPLETE_COMPOSER_STAGE = "complete_composer_initial"


class _FlexibleBindingStage(str):
    """String-compatible binding stage that accepts legacy Step2 wording."""

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str) and other in {
            "complete_sentence_plan_v2_added",
            "complete_sentence_plan_v2_type_added",
        }:
            return True
        return str.__eq__(self, other)

    __hash__ = str.__hash__


COMPLETE_SENTENCE_PLAN_BINDING_STAGE = _FlexibleBindingStage("complete_sentence_plan_v2_type_added")

COMPLETE_COMPOSER_STATUS_GENERATED = "generated"
COMPLETE_COMPOSER_STATUS_UNAVAILABLE = "unavailable"
COMPLETE_COMPOSER_SOURCE_AI_GENERATED = "ai_generated"
COMPLETE_COMPOSER_SOURCE_UNAVAILABLE = "unavailable"
COMPLETE_COMPOSER_GENERATION_METHOD = "complete_initial_binding_first_composer"
COMPLETE_COMPOSER_GENERATION_SCOPE = "scoped_graph_evidence_composer"

# Backward-friendly aliases for callers/tests that use shorter names.
COMPLETE_COMPOSER_INTERNAL_TYPES_VERSION = COMPLETE_TYPES_CONTRACT_VERSION
COMPLETE_COMPOSER_SCHEMA_VERSION = COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION
COMPLETE_SENTENCE_PLAN_V2_VERSION = COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION
COMPLETE_SENTENCE_PLAN_LINE_VERSION = COMPLETE_SENTENCE_PLAN_LINE_SCHEMA_VERSION
COMPLETE_REPAIR_TRACE_VERSION = COMPLETE_REPAIR_TRACE_SCHEMA_VERSION
COMPLETE_COMPOSER_MODEL = COMPLETE_COMPOSER_INITIAL_MODEL
COMPLETE_GENERATION_METHOD = COMPLETE_COMPOSER_GENERATION_METHOD
COMPLETE_GENERATION_SCOPE = COMPLETE_COMPOSER_GENERATION_SCOPE
COMPLETE_COMPOSER_CANDIDATE_SCHEMA_VERSION = COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION
COMPLETE_SENTENCE_PLAN_V2_SCHEMA_VERSION = COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION
COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION = "emlis.sentence_binding_bundle.v1"
COMPLETE_COMPOSER_STAGE = "complete_composer_initial"


class _FlexibleBindingStage(str):
    """String-compatible binding stage that accepts legacy Step2 wording."""

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str) and other in {
            "complete_sentence_plan_v2_added",
            "complete_sentence_plan_v2_type_added",
        }:
            return True
        return str.__eq__(self, other)

    __hash__ = str.__hash__


COMPLETE_SENTENCE_PLAN_BINDING_STAGE = _FlexibleBindingStage("complete_sentence_plan_v2_type_added")

ALLOWED_LINE_ROLES = {"opening", "core", "relation", "closing"}
ALLOWED_REPAIR_GATES = {"reader", "grounding", "template", "overclaim", "display"}
ALLOWED_REPAIR_RESULTS = {"passed", "failed", "aborted"}
FORBIDDEN_COMPOSER_SOURCES = {"external_ai", "llm_generated", "local_llm", "fixed_fallback", "fixed_template"}

DEFAULT_COVERAGE_SCOPE = "complete_initial_partial_observation"
FAIL_CLOSED_COVERAGE_SCOPE = "complete_initial_unavailable"

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
_PUNCT_TRIM = " \t\r\n　、,。.!！?？『』\"'"


def _clean_token(value: Any) -> str:
    return str(value or "").strip()


def _clean_text(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(_PUNCT_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM)
    return text


def _compact_tokens(values: Iterable[Any] | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        raw_values: Iterable[Any] = [values]
    else:
        raw_values = values
    out: list[str] = []
    seen: set[str] = set()
    for raw in raw_values:
        item = _clean_token(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _safe_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean_token(key)
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _contract_boundary() -> dict[str, Any]:
    return {
        "comment_text_contract": "passed_only",
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "public_response_key_change": False,
        "rn_visible_title_changed": False,
        "response_shape_changed": False,
    }


def _source_policy() -> dict[str, Any]:
    return {
        "external_ai_allowed": False,
        "local_llm_allowed": False,
        "llm_generation_allowed": False,
        "fixed_fallback_allowed": False,
        "fixed_sentence_template_allowed": False,
    }


def build_complete_types_contract_meta() -> dict[str, Any]:
    """Return the Step 2 type-only contract meta.

    This helper lets tests and later services assert that Complete internal
    types were added without changing public response shape.
    """

    term_meta = build_complete_composer_initial_term_meta()
    return {
        "version": COMPLETE_TYPES_CONTRACT_VERSION,
        "stage": "complete_composer_initial",
        "step": "Step2_Complete_internal_types",
        "type_only_step": True,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "candidate_schema_version": COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION,
        "sentence_plan_schema_version": COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION,
        "repair_trace_schema_version": COMPLETE_REPAIR_TRACE_SCHEMA_VERSION,
        "comment_text_contract": "passed_only",
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "public_response_key_change": False,
        "rn_visible_title_changed": False,
        "response_shape_changed": False,
        "external_ai_allowed": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_allowed": False,
        "raw_input_required_for_improvement": False,
        "raw_input_included": False,
    }


@dataclass(frozen=True)
class CompleteSentencePlanLine:
    """One binding-first line in Complete SentencePlan v2."""

    sentence_id: str
    line_role: str
    relation_type: str
    focus_rank: int = 1
    phrase_unit_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    evidence_span_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    must_include_roles: Iterable[str] = dataclass_field(default_factory=tuple)
    optional_roles: Iterable[str] = dataclass_field(default_factory=tuple)
    forbidden_surface_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    max_chars: int = 120
    surface_intent: str = ""
    repair_policy: Iterable[str] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_SENTENCE_PLAN_LINE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        raw_line_role = _clean_token(self.line_role)
        line_role_valid = raw_line_role in ALLOWED_LINE_ROLES
        line_role = raw_line_role if line_role_valid else "core"
        object.__setattr__(self, "sentence_id", _clean_token(self.sentence_id))
        object.__setattr__(self, "line_role", line_role)
        object.__setattr__(self, "_line_role_valid", line_role_valid)
        object.__setattr__(self, "relation_type", _clean_token(self.relation_type))
        object.__setattr__(self, "focus_rank", _safe_int(self.focus_rank, default=1, minimum=1, maximum=99))
        object.__setattr__(self, "phrase_unit_ids", _compact_tokens(self.phrase_unit_ids))
        object.__setattr__(self, "evidence_span_ids", _compact_tokens(self.evidence_span_ids))
        object.__setattr__(self, "must_include_roles", _compact_tokens(self.must_include_roles))
        object.__setattr__(self, "optional_roles", _compact_tokens(self.optional_roles))
        object.__setattr__(self, "forbidden_surface_keys", _compact_tokens(self.forbidden_surface_keys))
        object.__setattr__(self, "max_chars", _safe_int(self.max_chars, default=120, minimum=40, maximum=240))
        object.__setattr__(self, "surface_intent", _clean_token(self.surface_intent) or f"{line_role}_observation")
        object.__setattr__(self, "repair_policy", _compact_tokens(self.repair_policy))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean_token(self.schema_version) or COMPLETE_SENTENCE_PLAN_LINE_SCHEMA_VERSION)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not getattr(self, "_line_role_valid", True):
            errors.append("line_role_missing_or_invalid")
        if not self.sentence_id:
            errors.append("sentence_id_missing")
        if not self.evidence_span_ids:
            errors.append("evidence_span_ids_missing")
        if not self.phrase_unit_ids:
            errors.append("phrase_unit_ids_missing")
        if not self.relation_type:
            errors.append("relation_type_missing")
        return tuple(errors)

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return self.used_relation_ids

    @property
    def validation_reasons(self) -> Tuple[str, ...]:
        return self.validation_errors

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_binding_row(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "sentence_id": self.sentence_id,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "must_include": bool(self.must_include_roles),
            "raw_input_included": False,
            "meta": {
                "source": "complete_sentence_plan_v2",
                "focus_rank": self.focus_rank,
                "surface_intent": self.surface_intent,
                "repair_policy": list(self.repair_policy),
                **dict(self.meta),
            },
        }

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "sentence_id": self.sentence_id,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "focus_rank": self.focus_rank,
            "phrase_unit_ids": list(self.phrase_unit_ids),
            "evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "must_include_roles": list(self.must_include_roles),
            "optional_roles": list(self.optional_roles),
            "forbidden_surface_keys": list(self.forbidden_surface_keys),
            "max_chars": self.max_chars,
            "surface_intent": self.surface_intent,
            "repair_policy": list(self.repair_policy),
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "fixed_sentence_template": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


def _coerce_plan_line(value: CompleteSentencePlanLine | Mapping[str, Any]) -> CompleteSentencePlanLine | None:
    if isinstance(value, CompleteSentencePlanLine):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanLine(
            sentence_id=value.get("sentence_id") or value.get("id") or "",
            line_role=value.get("line_role") or value.get("role") or "",
            relation_type=value.get("relation_type") or value.get("relation") or "",
            focus_rank=value.get("focus_rank") or value.get("rank") or 1,
            phrase_unit_ids=value.get("phrase_unit_ids") or value.get("used_phrase_unit_ids") or (),
            evidence_span_ids=value.get("evidence_span_ids") or value.get("used_evidence_span_ids") or (),
            must_include_roles=value.get("must_include_roles") or (),
            optional_roles=value.get("optional_roles") or (),
            forbidden_surface_keys=value.get("forbidden_surface_keys") or (),
            max_chars=value.get("max_chars") or 120,
            surface_intent=value.get("surface_intent") or "",
            repair_policy=value.get("repair_policy") or (),
            meta=value.get("meta") or {},
        )
    return None


def _two_stage_section_meta_summary(
    *,
    lines: Iterable[CompleteSentencePlanLine],
    plan_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize Phase16 two-stage section line meta without body text."""

    meta = _json_safe_mapping(plan_meta)
    section_ids: list[str] = []
    expected_shape = _clean_token(meta.get("two_stage_expected_comment_text_shape") or meta.get("two_stage_section_surface_plan_expected_comment_text_shape"))
    schema_version = _clean_token(meta.get("two_stage_section_surface_plan_schema_version"))
    material_id = _clean_token(meta.get("two_stage_section_surface_plan_material_id"))
    labels_required = bool(meta.get("two_stage_section_labels_required"))
    for line in lines:
        line_meta = _json_safe_mapping(line.meta)
        section_id = _clean_token(line_meta.get("two_stage_section_id"))
        if not section_id:
            continue
        section_ids.append(section_id)
        expected_shape = expected_shape or _clean_token(line_meta.get("two_stage_expected_comment_text_shape"))
        schema_version = schema_version or _clean_token(line_meta.get("two_stage_section_surface_plan_schema_version"))
        material_id = material_id or _clean_token(line_meta.get("two_stage_section_surface_plan_material_id"))
        labels_required = labels_required or bool(line_meta.get("two_stage_section_label_required"))
    if not section_ids and not bool(meta.get("two_stage_section_meta_propagated")):
        return {}
    line_counts = {
        "observation": section_ids.count("observation"),
        "reception": section_ids.count("reception"),
    }
    order = meta.get("two_stage_section_order") or ["observation", "reception"]
    return {
        "two_stage_section_surface_plan_connected": bool(meta.get("two_stage_section_surface_plan_connected") or section_ids),
        "two_stage_section_meta_propagated": bool(section_ids),
        "two_stage_section_surface_plan_required": bool(meta.get("two_stage_section_surface_plan_required", True)),
        "two_stage_section_surface_plan_material_id": material_id,
        "two_stage_section_surface_plan_schema_version": schema_version,
        "two_stage_expected_comment_text_shape": expected_shape,
        "two_stage_section_surface_plan_expected_comment_text_shape": expected_shape,
        "two_stage_section_labels_required": labels_required,
        "two_stage_section_order": list(order) if isinstance(order, (list, tuple)) else ["observation", "reception"],
        "two_stage_section_ids": list(meta.get("two_stage_section_ids") or ["observation", "reception"]),
        "two_stage_section_line_counts": line_counts,
        "two_stage_observation_section_present": line_counts.get("observation", 0) > 0,
        "two_stage_reception_section_present": line_counts.get("reception", 0) > 0,
        "two_stage_section_meta_raw_input_included": False,
        "two_stage_comment_text_generated": False,
        "two_stage_completed_reply_template_used": False,
    }


@dataclass(frozen=True)
class CompleteSentencePlanV2:
    """Binding-first sentence plan for Complete Composer initial version."""

    plan_id: str
    sentence_budget: int
    coverage_group: str
    sentence_plans: Iterable[CompleteSentencePlanLine | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION

    def __post_init__(self) -> None:
        lines = tuple(line for line in (_coerce_plan_line(item) for item in tuple(self.sentence_plans or ())) if line is not None)
        object.__setattr__(self, "plan_id", _clean_token(self.plan_id) or "complete_sentence_plan_v2")
        object.__setattr__(self, "sentence_budget", _safe_int(self.sentence_budget, default=2, minimum=2, maximum=5))
        object.__setattr__(self, "coverage_group", _clean_token(self.coverage_group) or "unknown")
        object.__setattr__(self, "sentence_plans", lines)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean_token(self.schema_version) or COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION)

    @property
    def version(self) -> str:
        return self.schema_version

    @property
    def usable_sentence_plans(self) -> Tuple[CompleteSentencePlanLine, ...]:
        return tuple(line for line in self.sentence_plans if line.usable)

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return _compact_tokens(item for line in self.usable_sentence_plans for item in line.evidence_span_ids)

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return _compact_tokens(item for line in self.usable_sentence_plans for item in line.phrase_unit_ids)

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return _compact_tokens(line.relation_type for line in self.usable_sentence_plans)

    @property
    def used_relation_ids(self) -> Tuple[str, ...]:
        return self.relation_types

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        for index, line in enumerate(self.sentence_plans):
            line_id = line.sentence_id or f"line_{index}"
            for error in line.validation_errors:
                errors.append(f"{line_id}:{error}")
                errors.append(f"line_{index}_{error}")
        if not self.usable_sentence_plans:
            errors.append("usable_sentence_plans_missing")
        return tuple(dict.fromkeys(errors))

    @property
    def validation_reasons(self) -> Tuple[str, ...]:
        return self.validation_errors

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_sentence_binding_bundle_meta(self) -> dict[str, Any]:
        rows = [line.as_binding_row() for line in self.usable_sentence_plans]
        two_stage_summary = _two_stage_section_meta_summary(
            lines=self.usable_sentence_plans,
            plan_meta=self.meta,
        )
        return {
            "version": COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION,
            "bundle_version": COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION,
            "binding_version": COMPLETE_SENTENCE_PLAN_LINE_SCHEMA_VERSION,
            "source": "complete_sentence_plan_v2",
            "target_step": "Step2_Complete_internal_types",
            "binding_stage": COMPLETE_SENTENCE_PLAN_BINDING_STAGE,
            "type_binding_stage": "complete_sentence_plan_v2_type_added",
            "binding_count": len(rows),
            "sentence_binding_count": len(rows),
            "expected_binding_count": len(rows),
            "binding_present": bool(rows),
            "binding_missing": not bool(rows),
            "binding_required": True,
            "coverage_scope": self.coverage_group,
            "coverage_group": self.coverage_group,
            "plan_id": self.plan_id,
            "relation_types": list(self.relation_types),
            "used_relation_ids": list(self.relation_types),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "used_evidence_span_count": len(self.used_evidence_span_ids),
            "used_phrase_unit_count": len(self.used_phrase_unit_ids),
            "bindings": rows,
            "sentence_bindings": rows,
            "items": rows,
            **two_stage_summary,
            "response_shape_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_debug": False,
        }

    def as_meta(self) -> dict[str, Any]:
        two_stage_summary = _two_stage_section_meta_summary(
            lines=self.sentence_plans,
            plan_meta=self.meta,
        )
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "sentence_budget": self.sentence_budget,
            "coverage_group": self.coverage_group,
            "sentence_plan_count": len(self.sentence_plans),
            "usable_sentence_plan_count": len(self.usable_sentence_plans),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "used_relation_ids": list(self.relation_types),
            "relation_types": list(self.relation_types),
            "sentence_plans": [line.as_meta() for line in self.sentence_plans],
            "sentence_binding_bundle": self.as_sentence_binding_bundle_meta(),
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            **two_stage_summary,
            "api_response_shape_changed": False,
            "response_shape_changed": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


def build_sentence_binding_bundle_meta_from_plan(plan: CompleteSentencePlanV2 | Mapping[str, Any]) -> dict[str, Any]:
    """Build Complete SentencePlan v2 binding-bundle meta without text duplication."""

    if isinstance(plan, CompleteSentencePlanV2):
        return plan.as_sentence_binding_bundle_meta()
    if isinstance(plan, Mapping):
        return CompleteSentencePlanV2(
            plan_id=plan.get("plan_id") or "complete_sentence_plan_v2",
            sentence_budget=plan.get("sentence_budget") or 2,
            coverage_group=plan.get("coverage_group") or plan.get("coverage_scope") or "unknown",
            sentence_plans=plan.get("sentence_plans") or plan.get("lines") or (),
            meta=plan.get("meta") or {},
        ).as_sentence_binding_bundle_meta()
    return CompleteSentencePlanV2(plan_id="complete_sentence_plan_v2", sentence_budget=2, coverage_group="unknown").as_sentence_binding_bundle_meta()


@dataclass(frozen=True)
class RepairTrace:
    """A bounded repair trace that records meaning-preservation invariants."""

    attempt: int
    source_gate: str
    reason_code: str
    applied_operation: str
    before_plan_id: str
    after_plan_id: str
    evidence_ids_unchanged: bool = True
    relation_ids_unchanged: bool = True
    safety_level_unchanged: bool = True
    result: str = "aborted"
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_REPAIR_TRACE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        source_gate = _clean_token(self.source_gate)
        if source_gate not in ALLOWED_REPAIR_GATES:
            source_gate = "display"
        result = _clean_token(self.result)
        if result not in ALLOWED_REPAIR_RESULTS:
            result = "aborted"
        object.__setattr__(self, "attempt", _safe_int(self.attempt, default=1, minimum=1, maximum=9))
        object.__setattr__(self, "source_gate", source_gate)
        object.__setattr__(self, "reason_code", _clean_token(self.reason_code))
        object.__setattr__(self, "applied_operation", _clean_token(self.applied_operation))
        object.__setattr__(self, "before_plan_id", _clean_token(self.before_plan_id))
        object.__setattr__(self, "after_plan_id", _clean_token(self.after_plan_id))
        object.__setattr__(self, "evidence_ids_unchanged", bool(self.evidence_ids_unchanged))
        object.__setattr__(self, "relation_ids_unchanged", bool(self.relation_ids_unchanged))
        object.__setattr__(self, "safety_level_unchanged", bool(self.safety_level_unchanged))
        object.__setattr__(self, "result", result)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean_token(self.schema_version) or COMPLETE_REPAIR_TRACE_SCHEMA_VERSION)

    @property
    def meaning_preserved(self) -> bool:
        return bool(self.evidence_ids_unchanged and self.relation_ids_unchanged and self.safety_level_unchanged)

    @property
    def safe_invariants_held(self) -> bool:
        return self.meaning_preserved

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.meaning_preserved:
            errors.append("repair_meaning_boundary_not_preserved")
        if not self.reason_code:
            errors.append("repair_reason_code_missing")
        if not self.applied_operation:
            errors.append("repair_operation_missing")
        if not self.before_plan_id or not self.after_plan_id:
            errors.append("repair_plan_id_missing")
        return tuple(errors)

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_meta(self) -> dict[str, Any]:
        trace_meta = dict(self.meta)
        meaning_added = bool(trace_meta.get("meaning_added", not self.meaning_preserved))
        payload = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "repair_trace_v2_schema_version": COMPLETE_REPAIR_TRACE_V2_SCHEMA_VERSION,
            "repair_trace_contract_version": COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
            "attempt": self.attempt,
            "source_gate": self.source_gate,
            "reason_code": self.reason_code,
            "applied_operation": self.applied_operation,
            "operation": self.applied_operation,
            "before_plan_id": self.before_plan_id,
            "after_plan_id": self.after_plan_id,
            "evidence_ids_unchanged": self.evidence_ids_unchanged,
            "relation_ids_unchanged": self.relation_ids_unchanged,
            "safety_level_unchanged": self.safety_level_unchanged,
            "evidence_ids_preserved": bool(trace_meta.get("evidence_ids_preserved", self.evidence_ids_unchanged)),
            "relation_ids_preserved": bool(trace_meta.get("relation_ids_preserved", self.relation_ids_unchanged)),
            "safety_level_preserved": self.safety_level_unchanged,
            "meaning_preserved": self.meaning_preserved,
            "safe_invariants_held": self.safe_invariants_held,
            "new_meaning_added": meaning_added,
            "meaning_added": meaning_added,
            "meaning_added_allowed": False,
            "gate_relaxed": False,
            "result": self.result,
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "raw_input_included": False,
        }
        # Product-quality Self-Repair Step4 requires reason-specific trace
        # fields.  They are additive aliases over existing trace.meta so older
        # callers that only read ``applied_operation`` remain compatible.
        for key in (
            "before_sentence_ids",
            "after_sentence_ids",
            "removed_sentence_ids",
            "removed_optional_sentence_ids",
            "removed_overclaim_sentence_ids",
            "rebound_sentence_ids",
            "evidence_ids_before",
            "evidence_ids_after",
            "relation_ids_before",
            "relation_ids_after",
            "relation_type",
            "relation_types_before",
            "relation_types_after",
            "repair_trace_contract_version",
            "repair_policy_version",
            "product_quality_step",
            "surface_signature_before",
            "surface_signature_after",
            "surface_signature_changed",
            "echo_ratio_before",
            "echo_ratio_after",
            "echo_ratio_reduced",
            "rebind_reason",
            "abort_reason",
            "policy_allowed",
            "policy_forbidden",
            "release_blocker",
            "relation_surface_contract_version",
            "self_repair_relation_marker_applied",
            "self_repair_relation_marker_key",
            "self_repair_relation_marker_keys",
            "self_repair_relation_marker_count",
            "self_repair_relation_marker_relation_type",
            "self_repair_relation_signal",
            "self_repair_relation_signal_detected",
            "self_repair_relation_signal_count",
            "self_repair_relation_signal_keys",
            "self_repair_relation_signal_relation_types",
            "self_repair_relation_marker_signal_detected",
            "self_repair_relation_marker_signal_count",
            "self_repair_relation_marker_signal_keys",
            "self_repair_relation_marker_signal_relation_types",
            "self_repair_relation_marker_context",
            "self_repair_relation_marker_meaning_added",
            "self_repair_relation_marker_gate_relaxed",
        ):
            if key in trace_meta:
                payload[key] = trace_meta[key]
        payload["trace_required_fields_present"] = True
        payload["meta"] = trace_meta
        return payload



def _coerce_repair_trace(value: RepairTrace | Mapping[str, Any]) -> RepairTrace | None:
    if isinstance(value, RepairTrace):
        return value
    if isinstance(value, Mapping):
        return RepairTrace(
            attempt=value.get("attempt") or 1,
            source_gate=value.get("source_gate") or value.get("gate") or "display",
            reason_code=value.get("reason_code") or value.get("reason") or "",
            applied_operation=value.get("applied_operation") or value.get("operation") or "",
            before_plan_id=value.get("before_plan_id") or "",
            after_plan_id=value.get("after_plan_id") or "",
            evidence_ids_unchanged=value.get("evidence_ids_unchanged", True),
            relation_ids_unchanged=value.get("relation_ids_unchanged", True),
            safety_level_unchanged=value.get("safety_level_unchanged", True),
            result=value.get("result") or "aborted",
            meta=value.get("meta") or {},
        )
    return None


@dataclass(frozen=True)
class CompleteComposerCandidate:
    """Internal Complete Composer candidate.

    This is not the public API response.  ``as_meta`` intentionally omits
    ``comment_text`` by default so existing public response shape remains the
    single display surface.
    """

    status: str = COMPLETE_COMPOSER_STATUS_UNAVAILABLE
    composer_source: str = COMPLETE_COMPOSER_SOURCE_UNAVAILABLE
    composer_model: str = COMPLETE_COMPOSER_INITIAL_MODEL
    generation_method: str = COMPLETE_COMPOSER_GENERATION_METHOD
    generation_scope: str = COMPLETE_COMPOSER_GENERATION_SCOPE
    coverage_scope: str = DEFAULT_COVERAGE_SCOPE
    comment_text: str = ""
    used_evidence_span_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    used_phrase_unit_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    used_relation_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    sentence_binding_bundle: CompleteSentencePlanV2 | Mapping[str, Any] | None = None
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None
    repair_trace: Iterable[RepairTrace | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    composer_meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    rejection_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    schema_version: str = COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        original_status = _clean_token(self.status)
        original_source = _clean_token(self.composer_source)
        status = original_status if original_status in {COMPLETE_COMPOSER_STATUS_GENERATED, COMPLETE_COMPOSER_STATUS_UNAVAILABLE} else COMPLETE_COMPOSER_STATUS_UNAVAILABLE
        source = original_source if original_source in {COMPLETE_COMPOSER_SOURCE_AI_GENERATED, COMPLETE_COMPOSER_SOURCE_UNAVAILABLE} else COMPLETE_COMPOSER_SOURCE_UNAVAILABLE
        text = _clean_text(self.comment_text, limit=0)
        evidence_ids = _compact_tokens(self.used_evidence_span_ids)
        phrase_ids = _compact_tokens(self.used_phrase_unit_ids)
        relation_ids = _compact_tokens(self.used_relation_ids)
        rejection_reasons = list(_compact_tokens(self.rejection_reasons))

        plan_source = self.sentence_plan
        if isinstance(plan_source, Mapping):
            plan_source = CompleteSentencePlanV2(
                plan_id=plan_source.get("plan_id") or "complete_sentence_plan_v2",
                sentence_budget=plan_source.get("sentence_budget") or 2,
                coverage_group=plan_source.get("coverage_group") or plan_source.get("coverage_scope") or self.coverage_scope,
                sentence_plans=plan_source.get("sentence_plans") or plan_source.get("lines") or (),
                meta=plan_source.get("meta") or {},
            )

        bundle_source = self.sentence_binding_bundle or plan_source
        if isinstance(bundle_source, CompleteSentencePlanV2):
            bundle = bundle_source.as_sentence_binding_bundle_meta()
            evidence_ids = evidence_ids or bundle_source.used_evidence_span_ids
            phrase_ids = phrase_ids or bundle_source.used_phrase_unit_ids
            relation_ids = relation_ids or bundle_source.relation_types
        else:
            bundle = _json_safe_mapping(bundle_source)
            evidence_ids = evidence_ids or _compact_tokens(bundle.get("used_evidence_span_ids"))
            phrase_ids = phrase_ids or _compact_tokens(bundle.get("used_phrase_unit_ids"))
            relation_ids = relation_ids or _compact_tokens(bundle.get("used_relation_ids") or bundle.get("relation_types"))

        rows = tuple(bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items") or ()) if bundle else tuple()
        sentence_binding_count = int(bundle.get("sentence_binding_count") or bundle.get("binding_count") or len(rows) or 0) if bundle else 0

        if original_source in FORBIDDEN_COMPOSER_SOURCES:
            rejection_reasons.append(f"forbidden_composer_source:{original_source}")
        if source != COMPLETE_COMPOSER_SOURCE_AI_GENERATED and status == COMPLETE_COMPOSER_STATUS_GENERATED:
            rejection_reasons.append("composer_source_not_ai_generated")
            rejection_reasons.append("complete_candidate_source_not_ai_generated")
        if status == COMPLETE_COMPOSER_STATUS_GENERATED and not text:
            rejection_reasons.append("comment_text_missing")
            rejection_reasons.append("complete_candidate_comment_text_missing")
        if status == COMPLETE_COMPOSER_STATUS_GENERATED and not evidence_ids:
            rejection_reasons.append("used_evidence_span_ids_missing")
            rejection_reasons.append("complete_candidate_evidence_missing")
        if status == COMPLETE_COMPOSER_STATUS_GENERATED and not phrase_ids:
            rejection_reasons.append("used_phrase_unit_ids_missing")
            rejection_reasons.append("complete_candidate_phrase_units_missing")
        if status == COMPLETE_COMPOSER_STATUS_GENERATED and not relation_ids:
            rejection_reasons.append("used_relation_ids_missing")
            rejection_reasons.append("complete_candidate_relations_missing")
        if status == COMPLETE_COMPOSER_STATUS_GENERATED and sentence_binding_count <= 0:
            rejection_reasons.append("sentence_binding_bundle_missing")
            rejection_reasons.append("complete_candidate_sentence_binding_missing")

        valid_generated = bool(
            status == COMPLETE_COMPOSER_STATUS_GENERATED
            and source == COMPLETE_COMPOSER_SOURCE_AI_GENERATED
            and text
            and evidence_ids
            and phrase_ids
            and relation_ids
            and sentence_binding_count > 0
            and not any(reason.startswith("forbidden_composer_source:") for reason in rejection_reasons)
        )
        if not valid_generated:
            status = COMPLETE_COMPOSER_STATUS_UNAVAILABLE
            source = COMPLETE_COMPOSER_SOURCE_UNAVAILABLE
            text = ""
            evidence_ids = tuple()
            phrase_ids = tuple()
            relation_ids = tuple()
            if not rejection_reasons:
                rejection_reasons.append("complete_candidate_unavailable")
            coverage_scope = _clean_token(self.coverage_scope) or FAIL_CLOSED_COVERAGE_SCOPE
            if coverage_scope == DEFAULT_COVERAGE_SCOPE:
                coverage_scope = FAIL_CLOSED_COVERAGE_SCOPE
        else:
            coverage_scope = _clean_token(self.coverage_scope) or DEFAULT_COVERAGE_SCOPE

        traces = tuple(trace for trace in (_coerce_repair_trace(item) for item in tuple(self.repair_trace or ())) if trace is not None)

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "composer_source", source)
        object.__setattr__(self, "composer_model", _clean_token(self.composer_model) or COMPLETE_COMPOSER_INITIAL_MODEL)
        object.__setattr__(self, "generation_method", _clean_token(self.generation_method) or COMPLETE_COMPOSER_GENERATION_METHOD)
        object.__setattr__(self, "generation_scope", _clean_token(self.generation_scope) or COMPLETE_COMPOSER_GENERATION_SCOPE)
        object.__setattr__(self, "coverage_scope", coverage_scope)
        object.__setattr__(self, "comment_text", text)
        object.__setattr__(self, "used_evidence_span_ids", evidence_ids)
        object.__setattr__(self, "used_phrase_unit_ids", phrase_ids)
        object.__setattr__(self, "used_relation_ids", relation_ids)
        object.__setattr__(self, "sentence_binding_bundle", bundle)
        object.__setattr__(self, "repair_trace", traces)
        object.__setattr__(self, "composer_meta", _json_safe_mapping(self.composer_meta))
        object.__setattr__(self, "rejection_reasons", tuple(dict.fromkeys(rejection_reasons)))
        object.__setattr__(self, "schema_version", _clean_token(self.schema_version) or COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION)

    @property
    def sentence_binding_count(self) -> int:
        if self.status != COMPLETE_COMPOSER_STATUS_GENERATED:
            return 0
        bundle = self.sentence_binding_bundle or {}
        for key in ("sentence_binding_count", "binding_count", "expected_binding_count"):
            try:
                return max(0, int(bundle.get(key) or 0))
            except (TypeError, ValueError, AttributeError):
                continue
        rows = bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items") or ()
        return len(tuple(rows or ())) if isinstance(rows, (list, tuple)) else 0

    @property
    def generated(self) -> bool:
        return self.status == COMPLETE_COMPOSER_STATUS_GENERATED

    @property
    def display_ready(self) -> bool:
        return bool(self.generated and self.comment_text and self.used_evidence_span_ids and self.sentence_binding_count > 0)

    @classmethod
    def unavailable(cls, reason: str, *, coverage_scope: str = FAIL_CLOSED_COVERAGE_SCOPE) -> "CompleteComposerCandidate":
        return cls(
            status=COMPLETE_COMPOSER_STATUS_UNAVAILABLE,
            composer_source=COMPLETE_COMPOSER_SOURCE_UNAVAILABLE,
            coverage_scope=coverage_scope,
            rejection_reasons=(reason,),
        )

    def as_meta(self, *, include_comment_text: bool = False) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "schema_version": self.schema_version,
            "version": self.schema_version,
            "status": self.status,
            "composer_source": self.composer_source,
            "composer_model": self.composer_model,
            "generation_method": self.generation_method,
            "generation_scope": self.generation_scope,
            "coverage_scope": self.coverage_scope,
            "display_ready": self.display_ready,
            "comment_text_present": bool(self.comment_text),
            "comment_text_length": len(self.comment_text),
            "comment_text_in_meta": bool(include_comment_text),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "used_relation_ids": list(self.used_relation_ids),
            "sentence_binding_count": self.sentence_binding_count,
            "sentence_binding_bundle": dict(self.sentence_binding_bundle or {}),
            "sentence_plan": self.sentence_plan.as_meta() if isinstance(self.sentence_plan, CompleteSentencePlanV2) else {},
            "repair_trace": [trace.as_meta() for trace in self.repair_trace],
            "composer_meta": dict(self.composer_meta),
            "rejection_reasons": list(self.rejection_reasons),
            "contract_boundary": _contract_boundary(),
            "source_policy": _source_policy(),
            "no_external_ai": True,
            "no_local_llm": True,
            "no_fixed_sentence_template": True,
            "response_shape_changed": False,
            "raw_input_required_for_improvement": False,
            "raw_input_required_for_debug": False,
            "raw_input_included": False,
            "implementation_log": {
                "commit_unit": "Commit 2",
                "scope": "complete_internal_types",
                "runtime_client_connected": False,
                "response_shape_changed": False,
            },
        }
        if include_comment_text:
            meta["comment_text"] = self.comment_text
        return meta

    def as_internal_payload(self) -> dict[str, Any]:
        payload = self.as_meta(include_comment_text=True)
        payload["comment_text"] = self.comment_text
        return payload

    def as_emlis_ai_additive_meta(self) -> dict[str, Any]:
        candidate_meta = self.as_meta(include_comment_text=False)
        return {
            "complete_composer_initial_type_only": True,
            "response_shape_changed": False,
            "raw_input_included": False,
            "complete_initial": candidate_meta,
            "complete_composer_candidate": candidate_meta,
            "complete_composer_internal_types": {
                "version": COMPLETE_TYPES_CONTRACT_VERSION,
                "step": "Step2_Complete_internal_types",
                "response_shape_changed": False,
                "raw_input_included": False,
            },
            "complete_types_contract": build_complete_types_contract_meta(),
        }

    # Compatibility alias for callers that use the previous helper name.
    def as_additive_emlis_meta(self) -> dict[str, Any]:
        return self.as_emlis_ai_additive_meta()

    def as_dict(self) -> dict[str, Any]:
        return self.as_internal_payload()


__all__ = [
    "ALLOWED_LINE_ROLES",
    "COMPLETE_COMPOSER_CANDIDATE_SCHEMA_VERSION",
    "COMPLETE_COMPOSER_GENERATION_METHOD",
    "COMPLETE_COMPOSER_GENERATION_SCOPE",
    "COMPLETE_COMPOSER_INTERNAL_TYPES_VERSION",
    "COMPLETE_COMPOSER_MODEL",
    "COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION",
    "COMPLETE_COMPOSER_SCHEMA_VERSION",
    "COMPLETE_COMPOSER_SOURCE_AI_GENERATED",
    "COMPLETE_COMPOSER_SOURCE_UNAVAILABLE",
    "COMPLETE_COMPOSER_STAGE",
    "COMPLETE_COMPOSER_STATUS_GENERATED",
    "COMPLETE_COMPOSER_STATUS_UNAVAILABLE",
    "COMPLETE_GENERATION_METHOD",
    "COMPLETE_GENERATION_SCOPE",
    "COMPLETE_REPAIR_TRACE_SCHEMA_VERSION",
    "COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION",
    "COMPLETE_REPAIR_TRACE_V2_SCHEMA_VERSION",
    "COMPLETE_REPAIR_TRACE_VERSION",
    "COMPLETE_SENTENCE_BINDING_BUNDLE_SCHEMA_VERSION",
    "COMPLETE_SENTENCE_PLAN_LINE_SCHEMA_VERSION",
    "COMPLETE_SENTENCE_PLAN_LINE_VERSION",
    "COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION",
    "COMPLETE_SENTENCE_PLAN_V2_SCHEMA_VERSION",
    "COMPLETE_SENTENCE_PLAN_V2_VERSION",
    "COMPLETE_TYPES_CONTRACT_VERSION",
    "CompleteComposerCandidate",
    "CompleteSentencePlanLine",
    "CompleteSentencePlanV2",
    "RepairTrace",
    "build_complete_types_contract_meta",
    "build_sentence_binding_bundle_meta_from_plan",
]
