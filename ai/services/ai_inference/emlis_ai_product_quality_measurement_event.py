# -*- coding: utf-8 -*-
from __future__ import annotations

"""ProductQualityEventV1 schema and normalizer for EmlisAI QA.

Phase 2 introduces a text-free internal event used by Product Quality
measurement.  The event records only metadata needed for QA/blocker routing and
uses the same public display condition as ``/emotion/submit``.  It never stores
raw input, comment_text body, candidate body, surface body, public response key
changes, release flags, or machine-filled read-feeling ratings.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LIMITED_COMPOSER,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    CANDIDATE_SOURCE_KIND_NONE,
    CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHODS,
    GATE_RECOVERY_MATERIAL_SURFACE_MODELS,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_complete_initial_surface_recomposition import (
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
)
from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_surface_validation import (
    PRODUCT_SURFACE_BLOCKER_NONE,
    build_product_surface_validation_summary,
    product_surface_validation_public_summary,
    resolve_product_surface_requirement_from_sources,
)
from emlis_ai_public_feedback_meta import should_include_public_input_feedback

PRODUCT_QUALITY_EVENT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.measurement_event.v1"
)
PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.surface_origin.v1"
)
PRODUCT_QUALITY_EVENT_PHASE: Final = "Phase2_ProductQualityEventV1_Normalizer"
NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL: Final = "normal_observation_rebuild_candidate_v1"
NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD: Final = (
    "normal_observation_rebuild_after_surface_gate_failure"
)

PRODUCT_QUALITY_SCORECARD_ROW_FROM_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION: Final = (
    "cocolon.emlis.product_quality.scorecard_row_from_sanitized_current_output_event.20260609.v1"
)
PRODUCT_QUALITY_SANITIZED_CURRENT_OUTPUT_EVENT_CONNECTION_STEP_20260609: Final = (
    "P3-3_Sanitized_Event_Inventory_Connection"
)

_ALLOWED_SOURCE_TYPES: Final[frozenset[str]] = frozenset(
    {
        "fixture_family",
        "local_jsonl",
        "manual_internal_case",
        "regression_fixture",
    }
)
_ALLOWED_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "low_information_short",
        "daily_unpleasant",
        "daily_positive",
        "self_denial",
        "uncertainty",
        "mixed_emotion",
        "long_meaning_arc",
        "relationship_boundary",
        "structure_question",
        "positive_only",
        "self_understanding_follow",
        "input_self_report_only_failure",
        "unknown",
    }
)
_ALLOWED_OBSERVATION_STATUSES: Final[frozenset[str]] = frozenset(
    {"passed", "rejected", "unavailable", "safety_blocked"}
)
_ALLOWED_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "phase",
        "run_id",
        "row_id",
        "source",
        "family",
        "observation_status",
        "public_display_reached",
        "comment_text_present",
        "comment_text_length",
        "public_contract",
        "gate_results",
        "binding",
        "reason_coverage",
        "surface_quality",
        "safety",
        "composer_resolution",
        "surface_origin",
        "user_label_connection",
        "blockers",
        "warnings",
        "product_gate_ready",
        "public_release_applied",
    }
)
_PUBLIC_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "response_shape_changed",
    "public_response_key_added",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "raw_input_included",
    "comment_text_body_included",
    "candidate_body_included",
)
_FORBIDDEN_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "reply_text",
        "replyText",
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
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
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "external_ai_used",
        "local_llm_used",
    }
)
_IDENTIFIER_CHARS: Final[str] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"

PRODUCT_QUALITY_EVENT_V1_SCHEMA: Final[dict[str, Any]] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "ProductQualityEventV1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "run_id",
        "row_id",
        "source",
        "family",
        "observation_status",
        "public_display_reached",
        "comment_text_present",
        "comment_text_length",
        "public_contract",
        "gate_results",
        "binding",
        "reason_coverage",
        "surface_quality",
        "safety",
        "composer_resolution",
        "surface_origin",
        "blockers",
    ],
    "properties": {
        "schema_version": {"const": PRODUCT_QUALITY_EVENT_SCHEMA_VERSION},
        "phase": {"const": PRODUCT_QUALITY_EVENT_PHASE},
        "run_id": {"type": "string", "maxLength": 96},
        "row_id": {"type": "string", "maxLength": 96},
        "source": {
            "type": "object",
            "additionalProperties": False,
            "required": ["source_type", "source_case_id"],
            "properties": {
                "source_type": {"type": "string", "enum": sorted(_ALLOWED_SOURCE_TYPES)},
                "source_case_id": {"type": "string", "maxLength": 96},
                "source_revision": {"type": "string", "maxLength": 96},
            },
        },
        "family": {"type": "string", "enum": sorted(_ALLOWED_FAMILIES)},
        "observation_status": {
            "type": "string",
            "enum": sorted(_ALLOWED_OBSERVATION_STATUSES),
        },
        "public_display_reached": {"type": "boolean"},
        "comment_text_present": {"type": "boolean"},
        "comment_text_length": {"type": "integer", "minimum": 0, "maximum": 800},
        "public_contract": {
            "type": "object",
            "additionalProperties": False,
            "required": list(_PUBLIC_CONTRACT_KEYS),
            "properties": {key: {"const": False} for key in _PUBLIC_CONTRACT_KEYS},
        },
        "gate_results": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "display_gate_passed": {"type": "boolean"},
                "runtime_surface_gate_passed": {"type": "boolean"},
                "visible_surface_acceptance_passed": {"type": "boolean"},
                "two_stage_reception_gate_passed": {"type": "boolean"},
                "state_answer_gate_passed": {"type": "boolean"},
                "public_feedback_boundary_included": {"type": "boolean"},
                "bounded_repair_attempted": {"type": "boolean"},
                "post_final_gate_recovery_attempted": {"type": "boolean"},
                "normal_observation_rebuild_attempted": {"type": "boolean"},
                "normal_observation_rebuild_applied": {"type": "boolean"},
                "final_empty_exit": {"type": "boolean"},
            },
        },
        "binding": {
            "type": "object",
            "additionalProperties": False,
            "required": ["binding_required_count", "binding_supported_count", "binding_passed"],
            "properties": {
                "binding_required_count": {"type": "integer", "minimum": 0},
                "binding_supported_count": {"type": "integer", "minimum": 0},
                "unsupported_binding_count": {"type": "integer", "minimum": 0},
                "binding_passed": {"type": "boolean"},
            },
        },
        "reason_coverage": {
            "type": "object",
            "additionalProperties": False,
            "required": ["reason_required_count", "reason_covered_count", "reason_coverage_passed"],
            "properties": {
                "reason_required_count": {"type": "integer", "minimum": 0},
                "reason_covered_count": {"type": "integer", "minimum": 0},
                "reason_coverage_passed": {"type": "boolean"},
            },
        },
        "surface_quality": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "surface_signature_key": {"type": "string", "maxLength": 128},
                "template_major_count": {"type": "integer", "minimum": 0},
                "generic_comfort_detected": {"type": "boolean"},
                "mirror_only_detected": {"type": "boolean"},
                "structure_insight_family": {"type": "string", "maxLength": 96},
                "unsafe_insight_surface_detected": {"type": "boolean"},
            },
        },
        "safety": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "safety_major_count": {"type": "integer", "minimum": 0},
                "self_denial_safe_state_answer_used": {"type": "boolean"},
                "emergency_empty_exit": {"type": "boolean"},
            },
        },
        "composer_resolution": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "default_limited_enabled": {"type": "boolean"},
                "resolution_source": {"type": "string"},
                "composer_model": {"type": "string"},
                "requested_composer": {"type": "string"},
                "default_client_used": {"type": "boolean"},
                "complete_initial_client_used": {"type": "boolean"},
                "rejection_reasons": {"type": "array", "items": {"type": "string"}},
                "qa_profile": {"type": "string"},
            },
        },
        "surface_origin": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "schema_version",
                "candidate_source_kind",
                "composer_model",
                "generation_method",
                "public_surface_role",
                "public_display_allowed_by_boundary",
                "gate_recovery_material_surface_detected",
                "post_final_gate_recovery_material_surface_detected",
                "internal_policy_sentence_leak_risk",
                "template_meta_false_negative_risk",
                "normal_observation_rebuild_attempted",
                "normal_observation_rebuild_applied",
                "complete_initial_surface_recomposition_used",
                "labelled_two_stage_surface_recomposition_used",
                "raw_input_included",
                "comment_text_body_included",
            ],
            "properties": {
                "schema_version": {"const": PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION},
                "candidate_source_kind": {"type": "string", "maxLength": 128},
                "composer_model": {"type": "string", "maxLength": 128},
                "generation_method": {"type": "string", "maxLength": 128},
                "public_surface_role": {"type": "string", "maxLength": 128},
                "public_display_allowed_by_boundary": {"type": "boolean"},
                "gate_recovery_material_surface_detected": {"type": "boolean"},
                "post_final_gate_recovery_material_surface_detected": {"type": "boolean"},
                "internal_policy_sentence_leak_risk": {"type": "boolean"},
                "template_meta_false_negative_risk": {"type": "boolean"},
                "normal_observation_rebuild_attempted": {"type": "boolean"},
                "normal_observation_rebuild_applied": {"type": "boolean"},
                "complete_initial_surface_recomposition_used": {"type": "boolean"},
                "labelled_two_stage_surface_recomposition_used": {"type": "boolean"},
                "raw_input_included": {"const": False},
                "comment_text_body_included": {"const": False},
            },
        },
        "user_label_connection": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "limited_visible_surface_connection_applied": {"type": "boolean"},
                "history_connection_applied": {"type": "boolean"},
                "connectable_family": {"type": "string"},
                "evidence_record_count": {"type": "integer", "minimum": 0},
                "existing_surface_gates_passed": {"type": "boolean"},
            },
        },
        "blockers": {"type": "array", "items": {"type": "string"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "product_gate_ready": {"const": False},
        "public_release_applied": {"const": False},
    },
}


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_id(value: Any, *, max_length: int = 96, default: str = "") -> str:
    text = _clean(value)
    if not text:
        return default
    text = text[:max_length]
    if any(ch not in _IDENTIFIER_CHARS for ch in text):
        return default
    return text


def _safe_text_token(value: Any, *, max_length: int = 128, default: str = "") -> str:
    text = _clean(value)
    if not text:
        return default
    # This is used only for identifiers/signatures, never for body text.  If a
    # value looks like prose or contains whitespace, drop it rather than risk
    # carrying a surface body into the event.
    if any(ch.isspace() for ch in text):
        return default
    return text[:max_length]


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Sequence):
        return value
    if isinstance(value, set):
        return list(value)
    return [value]


def _dedupe(values: Sequence[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _as_sequence(values):
        text = _safe_id(item, max_length=160, default="")
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _to_bool(value: Any, default: bool | None = None) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on", "passed", "pass", "allow", "green"}:
        return True
    if text in {"false", "0", "no", "n", "off", "failed", "fail", "blocked", "red"}:
        return False
    return default


def _to_int(value: Any, default: int = 0, *, minimum: int = 0, maximum: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number < minimum:
        return minimum
    if maximum is not None and number > maximum:
        return maximum
    return number


def _get_path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _first(paths: Sequence[str], *sources: Mapping[str, Any]) -> Any:
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        for path in paths:
            value = _get_path(source, path)
            if value is not None and value != "":
                return value
    return None


def _first_int(paths: Sequence[str], *sources: Mapping[str, Any], default: int = 0) -> int:
    value = _first(paths, *sources)
    return _to_int(value, default)


def _first_bool(paths: Sequence[str], *sources: Mapping[str, Any], default: bool | None = None) -> bool | None:
    value = _first(paths, *sources)
    return _to_bool(value, default)


def _flag_is_true(value: Any) -> bool:
    return _to_bool(value, False) is True


def _find_forbidden_text_key_paths(value: Any, *, path: str = "payload", limit: int = 32) -> list[str]:
    found: list[str] = []
    if limit <= 0:
        return found
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                found.append(child_path)
                if len(found) >= limit:
                    return found
            for nested in _find_forbidden_text_key_paths(child, path=child_path, limit=limit - len(found)):
                found.append(nested)
                if len(found) >= limit:
                    return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for idx, child in enumerate(value):
            for nested in _find_forbidden_text_key_paths(child, path=f"{path}[{idx}]", limit=limit - len(found)):
                found.append(nested)
                if len(found) >= limit:
                    return found
    return found


def _find_forbidden_true_flag_paths(value: Any, *, path: str = "payload", limit: int = 32) -> list[str]:
    found: list[str] = []
    if limit <= 0:
        return found
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in _FORBIDDEN_TRUE_FLAGS and _flag_is_true(child):
                found.append(child_path)
                if len(found) >= limit:
                    return found
            for nested in _find_forbidden_true_flag_paths(child, path=child_path, limit=limit - len(found)):
                found.append(nested)
                if len(found) >= limit:
                    return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for idx, child in enumerate(value):
            for nested in _find_forbidden_true_flag_paths(child, path=f"{path}[{idx}]", limit=limit - len(found)):
                found.append(nested)
                if len(found) >= limit:
                    return found
    return found


def normalize_product_quality_family(value: Any) -> str:
    text = _clean(value).lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "low_information": "low_information_short",
        "low_info": "low_information_short",
        "low_info_short": "low_information_short",
        "daily_negative": "daily_unpleasant",
        "daily_unpleasantness": "daily_unpleasant",
        "unpleasant_daily": "daily_unpleasant",
        "daily_good": "daily_positive",
        "positive_daily": "daily_positive",
        "self_deny": "self_denial",
        "self_denial_safe": "self_denial",
        "mixed": "mixed_emotion",
        "meaning_arc": "long_meaning_arc",
        "long_arc": "long_meaning_arc",
        "relationship": "relationship_boundary",
        "relationship_boundary_issue": "relationship_boundary",
        "structure": "structure_question",
        "structure_insight": "structure_question",
        "positive": "positive_only",
        "self_understanding": "self_understanding_follow",
        "self_report_only_failure": "input_self_report_only_failure",
    }
    normalized = aliases.get(text, text)
    return normalized if normalized in _ALLOWED_FAMILIES else "unknown"


def _normalize_source_type(value: Any) -> str:
    text = _safe_id(value, max_length=64, default="manual_internal_case")
    return text if text in _ALLOWED_SOURCE_TYPES else "manual_internal_case"


def _normalize_status(value: Any) -> str:
    text = _safe_id(value, max_length=40, default="")
    return text if text in _ALLOWED_OBSERVATION_STATUSES else "unavailable"


def _public_contract() -> dict[str, bool]:
    return {key: False for key in _PUBLIC_CONTRACT_KEYS}


def _gate_passed_from(value: Any) -> bool | None:
    gate = _as_mapping(value)
    if not gate:
        return None
    direct = _to_bool(gate.get("passed"), None)
    if direct is not None:
        return direct
    status = _clean(gate.get("status") or gate.get("result") or gate.get("classification")).lower()
    if status in {"passed", "pass", "green", "ok", "allow", "yellow"}:
        return True
    if status in {"failed", "fail", "red", "repair_required", "blocked", "block"}:
        return False
    action = _clean(gate.get("action")).lower()
    if action in {"allow", "warn", "pass"}:
        return True
    if action in {"rerender_surface", "reroute_low_information", "block", "fail_closed"}:
        return False
    blocked = _to_bool(gate.get("blocked") or gate.get("terminal_surface_block"), None)
    if blocked is True:
        return False
    return None


def _extract_gate_results(
    *,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    public_display_reached: bool,
    comment_text_present: bool,
) -> dict[str, Any]:
    runtime_gate = _first(
        ("runtime_surface_pre_return_gate", "runtime_surface_gate", "multi_perspective.runtime_surface_pre_return_gate"),
        public_meta,
        internal_meta,
    )
    visible_gate = _first(
        ("visible_surface_acceptance_gate", "visible_surface_acceptance", "multi_perspective.visible_surface_acceptance_gate"),
        public_meta,
        internal_meta,
    )
    two_stage_gate = _first(
        ("two_stage_reception_gate", "two_stage_reception_cross_gate", "state_answer_gate_boundary.two_stage_reception_gate"),
        public_meta,
        internal_meta,
    )
    state_gate = _first(("state_answer_gate_boundary", "state_answer_gate"), public_meta, internal_meta)

    gate_results: dict[str, Any] = {
        "display_gate_passed": bool(public_display_reached),
        "public_feedback_boundary_included": bool(public_display_reached),
        "final_empty_exit": not comment_text_present,
    }
    runtime_passed = _gate_passed_from(runtime_gate)
    visible_passed = _gate_passed_from(visible_gate)
    two_stage_passed = _gate_passed_from(two_stage_gate)
    state_passed = _gate_passed_from(state_gate)
    if runtime_passed is not None:
        gate_results["runtime_surface_gate_passed"] = runtime_passed
    if visible_passed is not None:
        gate_results["visible_surface_acceptance_passed"] = visible_passed
    if two_stage_passed is not None:
        gate_results["two_stage_reception_gate_passed"] = two_stage_passed
    if state_passed is not None:
        gate_results["state_answer_gate_passed"] = state_passed

    bounded_repair = _first_bool(
        (
            "bounded_repair_attempted",
            "bounded_repair.attempted",
            "multi_perspective.bounded_repair_attempted",
            "display_repair.bounded_repair_attempted",
        ),
        public_meta,
        internal_meta,
        default=False,
    )
    post_final_recovery = _first_bool(
        (
            "post_final_gate_recovery_attempted",
            "post_final_gate_recovery.attempted",
            "multi_perspective.post_final_gate_recovery_attempted",
            "gate_recovery.post_final_gate_recovery_attempted",
        ),
        public_meta,
        internal_meta,
        default=False,
    )
    normal_rebuild_attempted = _first_bool(
        (
            "normal_observation_rebuild_attempted",
            "normal_observation_rebuild.attempted",
            "diagnostic_summary.normal_observation_rebuild.attempted",
            "reply_service_public_boundary.normal_observation_rebuild_attempted",
            "phase20_13_post_final_gate_recovery.normal_observation_rebuild_attempted",
            "phase20_5_gate_recovery_public_boundary.normal_observation_rebuild_attempted",
        ),
        public_meta,
        internal_meta,
        default=False,
    )
    normal_rebuild_applied = _first_bool(
        (
            "normal_observation_rebuild_applied",
            "normal_observation_rebuild.applied",
            "diagnostic_summary.normal_observation_rebuild.applied",
            "reply_service_public_boundary.normal_observation_rebuild_applied",
            "phase20_13_post_final_gate_recovery.normal_observation_rebuild_applied",
            "phase20_5_gate_recovery_public_boundary.normal_observation_rebuild_applied",
        ),
        public_meta,
        internal_meta,
        default=False,
    )
    gate_results["bounded_repair_attempted"] = bool(bounded_repair)
    gate_results["post_final_gate_recovery_attempted"] = bool(post_final_recovery)
    gate_results["normal_observation_rebuild_attempted"] = bool(normal_rebuild_attempted)
    gate_results["normal_observation_rebuild_applied"] = bool(normal_rebuild_applied)
    return gate_results


def _extract_binding(*sources: Mapping[str, Any]) -> dict[str, Any]:
    required = _first_int(
        (
            "binding.binding_required_count",
            "binding_required_count",
            "expected_binding_count",
            "expected_binding_sentence_count",
            "sentence_count",
            "diagnostic_summary.expected_binding_count",
            "diagnostic_summary.sentence_count",
        ),
        *sources,
        default=0,
    )
    supported = _first_int(
        (
            "binding.binding_supported_count",
            "binding_supported_count",
            "binding_supported_sentence_count",
            "binding_pass_count",
            "binding_count",
            "diagnostic_summary.binding_count",
            "diagnostic_summary.binding_supported_sentence_count",
        ),
        *sources,
        default=0,
    )
    unsupported = _first_int(
        (
            "binding.unsupported_binding_count",
            "unsupported_binding_count",
            "binding_missing_count",
            "diagnostic_summary.binding_missing_count",
        ),
        *sources,
        default=max(required - supported, 0),
    )
    explicit = _first_bool(
        ("binding.binding_passed", "binding_passed", "binding_pass", "grounding_passed"),
        *sources,
        default=None,
    )
    passed = bool(explicit) if explicit is not None else bool(unsupported == 0 and supported >= required)
    return {
        "binding_required_count": required,
        "binding_supported_count": supported,
        "unsupported_binding_count": unsupported,
        "binding_passed": passed,
    }


def _extract_reason_coverage(*sources: Mapping[str, Any]) -> dict[str, Any]:
    required = _first_int(
        (
            "reason_coverage.reason_required_count",
            "reason_required_count",
            "non_pass_reason_required_count",
            "diagnostic_summary.reason_required_count",
        ),
        *sources,
        default=0,
    )
    covered = _first_int(
        (
            "reason_coverage.reason_covered_count",
            "reason_covered_count",
            "non_pass_reason_covered_count",
            "diagnostic_summary.reason_covered_count",
        ),
        *sources,
        default=required,
    )
    explicit = _first_bool(
        ("reason_coverage.reason_coverage_passed", "reason_coverage_passed", "reason_coverage_pass"),
        *sources,
        default=None,
    )
    passed = bool(explicit) if explicit is not None else bool(covered >= required)
    return {
        "reason_required_count": required,
        "reason_covered_count": covered,
        "reason_coverage_passed": passed,
    }


def _extract_surface_quality(*sources: Mapping[str, Any]) -> dict[str, Any]:
    signature = _safe_text_token(
        _first(
            (
                "surface_quality.surface_signature_key",
                "surface_signature_key",
                "surface_quality_signature.surface_signature_key",
                "surface_quality_signature.signature_key",
                "diagnostic_summary.surface_signature_key",
            ),
            *sources,
        ),
        max_length=128,
        default="",
    )
    structure_family = normalize_product_quality_family(
        _first(("surface_quality.structure_insight_family", "structure_insight_family"), *sources)
    )
    if structure_family == "unknown":
        structure_family = _safe_id(
            _first(("surface_quality.structure_insight_family", "structure_insight_family"), *sources),
            max_length=96,
            default="",
        )
    template_major_count = _first_int(
        (
            "surface_quality.template_major_count",
            "template_major_count",
            "surface_template_major_count",
            "anti_template_major_count",
            "diagnostic_summary.template_major_count",
        ),
        *sources,
        default=0,
    )
    return {
        "surface_signature_key": signature,
        "template_major_count": template_major_count,
        "generic_comfort_detected": bool(
            _first_bool(("surface_quality.generic_comfort_detected", "generic_comfort_detected"), *sources, default=False)
        ),
        "mirror_only_detected": bool(
            _first_bool(("surface_quality.mirror_only_detected", "mirror_only_detected"), *sources, default=False)
        ),
        "structure_insight_family": structure_family,
        "unsafe_insight_surface_detected": bool(
            _first_bool(
                (
                    "surface_quality.unsafe_insight_surface_detected",
                    "unsafe_insight_surface_detected",
                    "unsafe_surface_detected",
                ),
                *sources,
                default=False,
            )
        ),
    }


def _extract_safety(*sources: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "safety_major_count": _first_int(
            ("safety.safety_major_count", "safety_major_count", "diagnostic_summary.safety_major_count"),
            *sources,
            default=0,
        ),
        "self_denial_safe_state_answer_used": bool(
            _first_bool(
                (
                    "safety.self_denial_safe_state_answer_used",
                    "self_denial_safe_state_answer_used",
                    "state_answer_gate_boundary.self_denial_safe_state_answer_used",
                ),
                *sources,
                default=False,
            )
        ),
        "emergency_empty_exit": bool(
            _first_bool(("safety.emergency_empty_exit", "emergency_empty_exit"), *sources, default=False)
        ),
    }


def _extract_composer_resolution(*sources: Mapping[str, Any]) -> dict[str, Any]:
    composer = _as_mapping(
        _first(
            (
                "composer_resolution",
                "multi_perspective.composer_client_resolution",
                "default_composer_resolution",
            ),
            *sources,
        )
    )
    if not composer:
        for source in sources:
            candidate = _as_mapping(source)
            if any(
                key in candidate
                for key in (
                    "default_limited_enabled",
                    "resolution_source",
                    "source",
                    "composer_model",
                    "requested_composer",
                    "default_client_used",
                )
            ):
                composer = candidate
                break
    return {
        "default_limited_enabled": bool(_to_bool(composer.get("default_limited_enabled"), False)),
        "resolution_source": _safe_id(
            composer.get("resolution_source") or composer.get("source"), max_length=96, default=""
        ),
        "composer_model": _safe_id(composer.get("composer_model"), max_length=96, default=""),
        "requested_composer": _safe_id(composer.get("requested_composer"), max_length=64, default=""),
        "default_client_used": bool(_to_bool(composer.get("default_client_used"), False)),
        "complete_initial_client_used": bool(_to_bool(composer.get("complete_initial_client_used"), False)),
        "rejection_reasons": _dedupe(composer.get("rejection_reasons")),
        "qa_profile": _safe_id(composer.get("qa_profile"), max_length=64, default=""),
    }


def _extract_boundary_decision(*sources: Mapping[str, Any]) -> Mapping[str, Any]:
    value = _first(
        (
            "surface_origin.gate_recovery_public_boundary_decision",
            "gate_recovery_public_boundary_decision",
            "phase20_5_gate_recovery_public_boundary.gate_recovery_public_boundary_decision",
            "phase20_5_gate_recovery_public_candidate_builder.gate_recovery_public_boundary_decision",
            "phase20_13_post_final_gate_recovery.gate_recovery_public_boundary_decision",
            "phase20_13_post_final_gate_recovery.reply_service_public_boundary.gate_recovery_public_boundary_decision",
            "reply_service_public_boundary.gate_recovery_public_boundary_decision",
            "gate_recovery_public_boundary.gate_recovery_public_boundary_decision",
        ),
        *sources,
    )
    return _as_mapping(value)


def _infer_surface_origin_candidate_source_kind(
    *,
    explicit_source_kind: str,
    composer_model: str,
    generation_method: str,
    public_surface_role: str,
    requested_composer: str,
    default_client_used: bool,
    complete_initial_client_used: bool,
) -> str:
    if explicit_source_kind:
        return explicit_source_kind
    model_lower = composer_model.lower()
    generation_lower = generation_method.lower()
    if composer_model in GATE_RECOVERY_MATERIAL_SURFACE_MODELS or generation_method in GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHODS:
        return CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    if public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY:
        return CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE
    if "bounded_repaired_original" in model_lower or generation_method == "bounded_repair_after_gate_recovery":
        return CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    if "low_information_observation_composer" in model_lower or "low_information_observation" in generation_lower:
        return CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    if "self_denial_safe_state_answer" in model_lower or "self_denial_safe_state_answer" in generation_lower:
        return CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER
    if (
        composer_model == COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL
        or generation_method == COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD
        or "complete_initial_surface_recomposition" in model_lower
        or "complete_initial_surface_recomposition" in generation_lower
    ):
        return CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    if (
        composer_model == LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL
        or generation_method == LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD
        or "labelled_two_stage_surface_recomposition" in model_lower
        or "labelled_two_stage_surface_recomposition" in generation_lower
    ):
        return CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    if (
        composer_model == NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
        or generation_method == NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD
        or "normal_observation_rebuild" in model_lower
        or "normal_observation_rebuild" in generation_lower
    ):
        return CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    if "complete_self_repair" in model_lower or "complete_self_repair" in generation_lower:
        return CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE
    if complete_initial_client_used or requested_composer == "complete_initial" or "complete_initial" in model_lower:
        return CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER
    if default_client_used or requested_composer == "limited" or "limited" in model_lower:
        return CANDIDATE_SOURCE_KIND_LIMITED_COMPOSER
    return CANDIDATE_SOURCE_KIND_NONE


def _infer_surface_origin_public_role(*, explicit_role: str, candidate_source_kind: str) -> str:
    if explicit_role:
        return explicit_role
    if candidate_source_kind in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS:
        return PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    if candidate_source_kind in {
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    }:
        return PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    return ""


def _surface_origin_template_false_negative_risk(
    *,
    recovery_surface_detected: bool,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    composer_resolution: Mapping[str, Any],
    machine_metrics: Mapping[str, Any],
) -> bool:
    if not recovery_surface_detected:
        return False
    sources = (public_meta, internal_meta, composer_resolution, machine_metrics)
    for path in (
        "surface_origin.template_meta_false_negative_risk",
        "template_meta_false_negative_risk",
    ):
        explicit = _first_bool((path,), *sources, default=None)
        if explicit is not None:
            return bool(explicit)
    for path in (
        "surface_quality_signature.surface_template_major",
        "surface_quality_signature.template_major",
        "phase20_15_gate_recovery_surface_binding.surface_quality_signature.surface_template_major",
        "phase20_15_gate_recovery_surface_binding.surface_quality_signature.template_major",
        "surface_origin.surface_template_major",
        "surface_origin.template_major",
        "surface_template_major",
        "template_major",
    ):
        flag = _first_bool((path,), *sources, default=None)
        if flag is False:
            return True
    return False


def _extract_surface_origin(
    *,
    public_display_reached: bool,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    composer_resolution: Mapping[str, Any],
    machine_metrics: Mapping[str, Any],
) -> dict[str, Any]:
    """Return P8 meta-only surface origin for ProductQualityEventV1.

    The extraction is lineage-only.  It never copies public body text, raw input,
    or candidate bodies into QA material.
    """

    sources = (public_meta, internal_meta, composer_resolution, machine_metrics)
    boundary_decision = _extract_boundary_decision(*sources)
    composer_model = _safe_id(
        _first(
            (
                "surface_origin.composer_model",
                "public_surface_lineage.composer_model",
                "complete_initial_surface_recomposition_summary.composer_model",
                "labelled_two_stage_surface_recomposition_summary.composer_model",
                "composer_model",
                "composer_resolution.composer_model",
                "candidate.composer_model",
                "phase20_5_gate_recovery_public_boundary.gate_recovery_public_boundary_decision.composer_model",
                "phase20_5_gate_recovery_public_candidate_builder.gate_recovery_public_boundary_decision.composer_model",
                "phase20_13_post_final_gate_recovery.gate_recovery_public_boundary_decision.composer_model",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.gate_recovery_public_boundary_decision.composer_model",
                "reply_service_public_boundary.composer_model",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.composer_model",
            ),
            *sources,
            boundary_decision,
        ),
        max_length=128,
        default="",
    )
    generation_method = _safe_id(
        _first(
            (
                "surface_origin.generation_method",
                "public_surface_lineage.generation_method",
                "complete_initial_surface_recomposition_summary.generation_method",
                "labelled_two_stage_surface_recomposition_summary.generation_method",
                "generation_method",
                "composer_resolution.generation_method",
                "candidate.generation_method",
                "phase20_5_gate_recovery_public_boundary.gate_recovery_public_boundary_decision.generation_method",
                "phase20_5_gate_recovery_public_candidate_builder.gate_recovery_public_boundary_decision.generation_method",
                "phase20_13_post_final_gate_recovery.gate_recovery_public_boundary_decision.generation_method",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.gate_recovery_public_boundary_decision.generation_method",
                "reply_service_public_boundary.generation_method",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.generation_method",
            ),
            *sources,
            boundary_decision,
        ),
        max_length=128,
        default="",
    )
    explicit_source_kind = _safe_id(
        _first(
            (
                "surface_origin.candidate_source_kind",
                "public_surface_lineage.candidate_source_kind",
                "complete_initial_surface_recomposition_summary.candidate_source_kind",
                "labelled_two_stage_surface_recomposition_summary.candidate_source_kind",
                "candidate_source_kind",
                "composer_resolution.candidate_source_kind",
                "candidate.candidate_source_kind",
                "phase20_5_gate_recovery_public_candidate_builder.source_kind",
                "phase20_5_gate_recovery_public_candidate_builder.gate_recovery_public_boundary_decision.candidate_source_kind",
                "phase20_5_gate_recovery_public_boundary.gate_recovery_public_boundary_decision.candidate_source_kind",
                "phase20_13_post_final_gate_recovery.gate_recovery_public_boundary_decision.candidate_source_kind",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.gate_recovery_public_boundary_decision.candidate_source_kind",
                "public_candidate_source_kind",
                "adopted_candidate_source_kind",
                "final_surface_origin_candidate_source_kind",
                "normal_observation_rebuild_source_kind",
                "reply_service_public_boundary.candidate_source_kind",
                "reply_service_public_boundary.public_candidate_source_kind",
                "reply_service_public_boundary.adopted_candidate_source_kind",
                "reply_service_public_boundary.final_surface_origin_candidate_source_kind",
                "reply_service_public_boundary.normal_observation_rebuild_source_kind",
                "phase20_13_post_final_gate_recovery.public_candidate_source_kind",
                "phase20_13_post_final_gate_recovery.adopted_candidate_source_kind",
                "phase20_13_post_final_gate_recovery.final_surface_origin_candidate_source_kind",
                "phase20_13_post_final_gate_recovery.normal_observation_rebuild_source_kind",
                "diagnostic_summary.normal_observation_rebuild.source_kind",
                "diagnostic_summary.normal_observation_rebuild.candidate_source_kind",
            ),
            *sources,
            boundary_decision,
        ),
        max_length=128,
        default="",
    )
    explicit_role = _safe_id(
        _first(
            (
                "surface_origin.public_surface_role",
                "public_surface_lineage.public_surface_role",
                "complete_initial_surface_recomposition_summary.public_surface_role",
                "labelled_two_stage_surface_recomposition_summary.public_surface_role",
                "public_surface_role",
                "candidate.public_surface_role",
                "phase20_5_gate_recovery_public_boundary.gate_recovery_public_boundary_decision.public_surface_role",
                "phase20_5_gate_recovery_public_candidate_builder.gate_recovery_public_boundary_decision.public_surface_role",
                "phase20_13_post_final_gate_recovery.gate_recovery_public_boundary_decision.public_surface_role",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.gate_recovery_public_boundary_decision.public_surface_role",
                "reply_service_public_boundary.public_surface_role",
                "phase20_13_post_final_gate_recovery.reply_service_public_boundary.public_surface_role",
                "diagnostic_summary.normal_observation_rebuild.public_surface_role",
            ),
            *sources,
            boundary_decision,
        ),
        max_length=128,
        default="",
    )
    requested_composer = _safe_id(
        _first(("requested_composer", "composer_resolution.requested_composer"), composer_resolution, internal_meta, public_meta),
        max_length=64,
        default="",
    )
    candidate_source_kind = _infer_surface_origin_candidate_source_kind(
        explicit_source_kind=explicit_source_kind,
        composer_model=composer_model,
        generation_method=generation_method,
        public_surface_role=explicit_role,
        requested_composer=requested_composer,
        default_client_used=bool(_to_bool(_first(("default_client_used", "composer_resolution.default_client_used"), composer_resolution, internal_meta, public_meta), False)),
        complete_initial_client_used=bool(_to_bool(_first(("complete_initial_client_used", "composer_resolution.complete_initial_client_used"), composer_resolution, internal_meta, public_meta), False)),
    )
    public_surface_role = _infer_surface_origin_public_role(
        explicit_role=explicit_role,
        candidate_source_kind=candidate_source_kind,
    )
    gate_recovery_surface_detected = bool(
        composer_model in GATE_RECOVERY_MATERIAL_SURFACE_MODELS
        or generation_method in GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHODS
        or candidate_source_kind
        in {CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE, CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE}
        or public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    )
    post_final_surface_detected = bool(
        gate_recovery_surface_detected
        and (
            composer_model == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
            or generation_method == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
            or _first_bool(
                (
                    "surface_origin.post_final_gate_recovery_material_surface_detected",
                    "post_final_gate_recovery_material_surface_detected",
                ),
                *sources,
                default=False,
            )
            is True
        )
    )
    boundary_allowed = _first_bool(
        (
            "surface_origin.public_display_allowed_by_boundary",
            "surface_origin.public_display_allowed",
            "public_surface_lineage.public_display_allowed_by_boundary",
            "public_surface_lineage.public_display_allowed",
            "complete_initial_surface_recomposition_summary.public_display_allowed_by_boundary",
            "labelled_two_stage_surface_recomposition_summary.public_display_allowed_by_boundary",
            "public_display_allowed_by_boundary",
            "public_display_allowed",
            "phase20_5_gate_recovery_public_boundary.public_display_allowed",
            "phase20_5_gate_recovery_public_candidate_builder.gate_recovery_public_boundary_decision.public_display_allowed",
            "phase20_13_post_final_gate_recovery.public_display_allowed_by_boundary",
            "phase20_13_post_final_gate_recovery.reply_service_public_boundary.public_display_allowed",
            "reply_service_public_boundary.public_display_allowed",
            "diagnostic_summary.normal_observation_rebuild.public_boundary.public_display_allowed",
        ),
        *sources,
        boundary_decision,
        default=None,
    )
    if boundary_allowed is None:
        boundary_allowed = bool(
            public_surface_role == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
            and candidate_source_kind in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
            and not gate_recovery_surface_detected
        )
    template_false_negative_risk = _surface_origin_template_false_negative_risk(
        recovery_surface_detected=gate_recovery_surface_detected,
        public_meta=public_meta,
        internal_meta=internal_meta,
        composer_resolution=composer_resolution,
        machine_metrics=machine_metrics,
    )
    internal_policy_sentence_leak_risk = bool(
        gate_recovery_surface_detected
        and (
            public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
            or bool(public_display_reached)
        )
    )
    normal_rebuild_attempted = bool(
        candidate_source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        or _first_bool(
            (
                "normal_observation_rebuild_attempted",
                "normal_observation_rebuild.attempted",
                "surface_origin.normal_observation_rebuild_attempted",
                "reply_service_public_boundary.normal_observation_rebuild_attempted",
                "phase20_13_post_final_gate_recovery.normal_observation_rebuild_attempted",
                "phase20_5_gate_recovery_public_boundary.normal_observation_rebuild_attempted",
                "diagnostic_summary.normal_observation_rebuild.attempted",
            ),
            *sources,
            boundary_decision,
            default=False,
        )
    )
    explicit_normal_rebuild_applied = _first_bool(
        (
            "normal_observation_rebuild_applied",
            "normal_observation_rebuild.applied",
            "surface_origin.normal_observation_rebuild_applied",
            "reply_service_public_boundary.normal_observation_rebuild_applied",
            "phase20_13_post_final_gate_recovery.normal_observation_rebuild_applied",
            "phase20_5_gate_recovery_public_boundary.normal_observation_rebuild_applied",
            "diagnostic_summary.normal_observation_rebuild.applied",
        ),
        *sources,
        boundary_decision,
        default=None,
    )
    normal_rebuild_applied = bool(
        explicit_normal_rebuild_applied
        if explicit_normal_rebuild_applied is not None
        else (
            normal_rebuild_attempted
            and candidate_source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
            and bool(boundary_allowed)
            and bool(public_display_reached)
        )
    )
    complete_initial_recomposition_used = bool(
        candidate_source_kind == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
        or _first_bool(
            (
                "complete_initial_surface_recomposition_used",
                "complete_initial_surface_recomposition_applied",
                "surface_origin.complete_initial_surface_recomposition_used",
                "public_surface_lineage.complete_initial_surface_recomposition_used",
                "complete_initial_surface_recomposition_summary.source_unavailable_recovered",
                "complete_initial_surface_recomposition_summary.public_display_allowed_by_boundary",
            ),
            *sources,
            boundary_decision,
            default=False,
        )
    )
    labelled_two_stage_recomposition_used = bool(
        candidate_source_kind == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
        or _first_bool(
            (
                "labelled_two_stage_recomposition_used",
                "labelled_two_stage_surface_recomposition_used",
                "labelled_two_stage_surface_recomposition_applied",
                "surface_origin.labelled_two_stage_surface_recomposition_used",
                "public_surface_lineage.labelled_two_stage_surface_recomposition_used",
                "labelled_two_stage_surface_recomposition_summary.two_stage_required",
                "labelled_two_stage_surface_recomposition_summary.public_display_allowed_by_boundary",
            ),
            *sources,
            boundary_decision,
            default=False,
        )
    )
    return {
        "schema_version": PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION,
        "candidate_source_kind": candidate_source_kind,
        "composer_model": composer_model,
        "generation_method": generation_method,
        "public_surface_role": public_surface_role,
        "public_display_allowed_by_boundary": bool(boundary_allowed),
        "gate_recovery_material_surface_detected": bool(gate_recovery_surface_detected),
        "post_final_gate_recovery_material_surface_detected": bool(post_final_surface_detected),
        "internal_policy_sentence_leak_risk": bool(internal_policy_sentence_leak_risk),
        "template_meta_false_negative_risk": bool(template_false_negative_risk),
        "normal_observation_rebuild_attempted": bool(normal_rebuild_attempted),
        "normal_observation_rebuild_applied": bool(normal_rebuild_applied),
        "complete_initial_surface_recomposition_used": bool(complete_initial_recomposition_used),
        "labelled_two_stage_surface_recomposition_used": bool(labelled_two_stage_recomposition_used),
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _extract_product_surface_validation(
    *,
    comment_text: Any,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    composer_resolution: Mapping[str, Any],
    machine_metrics: Mapping[str, Any],
    surface_origin: Mapping[str, Any],
    public_display_reached: bool,
) -> dict[str, Any]:
    existing = product_surface_validation_public_summary(
        _first(
            (
                "product_surface_validation",
                "surface_quality.product_surface_validation",
                "diagnostic_summary.product_surface_validation",
            ),
            public_meta,
            internal_meta,
            machine_metrics,
        )
    )
    if existing:
        return existing

    surface_requirement = resolve_product_surface_requirement_from_sources(
        public_meta,
        internal_meta,
        machine_metrics,
        composer_resolution,
    )
    candidate_generation = dict(_as_mapping(surface_origin))
    candidate_generation.update(
        {
            "composer_source": _first(
                (
                    "composer_source",
                    "composer_resolution.composer_source",
                    "candidate.composer_source",
                ),
                public_meta,
                internal_meta,
                composer_resolution,
                machine_metrics,
            ),
            "candidate_status": _first(
                (
                    "candidate_status",
                    "status",
                    "composer_resolution.candidate_status",
                    "candidate.status",
                ),
                public_meta,
                internal_meta,
                composer_resolution,
                machine_metrics,
            ),
        }
    )
    return build_product_surface_validation_summary(
        input_feedback_included=bool(public_display_reached),
        comment_text=comment_text,
        emlis_ai_public_meta=public_meta,
        surface_requirement=surface_requirement,
        candidate_generation_summary=candidate_generation,
    )


def _extract_user_label_connection(*sources: Mapping[str, Any]) -> dict[str, Any]:
    user_label = _as_mapping(
        _first(
            (
                "user_label_connection",
                "emlis_ai_user_label_connection",
                "multi_perspective.user_label_connection",
            ),
            *sources,
        )
    )
    return {
        "limited_visible_surface_connection_applied": bool(
            _to_bool(user_label.get("limited_visible_surface_connection_applied"), False)
        ),
        "history_connection_applied": bool(_to_bool(user_label.get("history_connection_applied"), False)),
        "connectable_family": _safe_id(user_label.get("connectable_family"), max_length=96, default=""),
        "evidence_record_count": _to_int(user_label.get("evidence_record_count"), 0),
        "existing_surface_gates_passed": bool(_to_bool(user_label.get("existing_surface_gates_passed"), False)),
    }


def _detect_gate_recovery_public_leak_blockers(
    *,
    public_display_reached: bool,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    composer_resolution: Mapping[str, Any],
    machine_metrics: Mapping[str, Any],
    surface_origin: Mapping[str, Any] | None = None,
) -> list[str]:
    """Return meta-only blockers when a diagnostic recovery surface reached public display.

    This P0/P1 detector does not add new event keys and does not inspect body
    text.  It only looks at candidate lineage/source-kind metadata that P1 makes
    explicit.  P2/P3 still have to block the runtime promotion itself.
    """

    origin = _as_mapping(surface_origin) or _extract_surface_origin(
        public_display_reached=public_display_reached,
        public_meta=public_meta,
        internal_meta=internal_meta,
        composer_resolution=composer_resolution,
        machine_metrics=machine_metrics,
    )
    sources = (public_meta, internal_meta, composer_resolution, machine_metrics, origin)
    composer_model = _safe_id(origin.get("composer_model"), max_length=128, default="")
    generation_method = _safe_id(origin.get("generation_method"), max_length=128, default="")
    candidate_source_kind = _safe_id(origin.get("candidate_source_kind"), max_length=128, default="")
    public_surface_role = _safe_id(origin.get("public_surface_role"), max_length=128, default="")
    rejection_reasons = _dedupe(
        _first(("rejection_reasons", "composer_resolution.rejection_reasons"), *sources)
    )

    recovery_surface_detected = bool(origin.get("gate_recovery_material_surface_detected"))
    if not recovery_surface_detected:
        return []

    blockers: list[str] = []
    if bool(public_display_reached):
        if (
            composer_model == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
            or generation_method == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
        ):
            blockers.append(BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK)
        else:
            blockers.append(BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK)
        if public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY:
            blockers.append(BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC)
        if "default_limited_composer_feature_disabled" in rejection_reasons:
            blockers.append(BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION)
    if bool(origin.get("template_meta_false_negative_risk")):
        blockers.append(BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE)
    return _dedupe(blockers)


def _forbidden_source_findings(
    *,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    composer_resolution: Mapping[str, Any],
    machine_metrics: Mapping[str, Any],
) -> tuple[list[str], list[str]]:
    text_paths: list[str] = []
    flag_paths: list[str] = []
    sources = {
        "public_meta": public_meta,
        "internal_meta": internal_meta,
        "composer_resolution": composer_resolution,
        "machine_metrics": machine_metrics,
    }
    for name, source in sources.items():
        if not source:
            continue
        text_paths.extend(_find_forbidden_text_key_paths(source, path=name, limit=16))
        flag_paths.extend(_find_forbidden_true_flag_paths(source, path=name, limit=16))
    return _dedupe(text_paths), _dedupe(flag_paths)


def normalize_product_quality_event(
    *,
    run_id: Any,
    row_id: Any,
    source_type: Any = "manual_internal_case",
    source_case_id: Any = "manual_case",
    family: Any = "unknown",
    reply: Any = None,
    comment_text: Any = None,
    public_meta: Mapping[str, Any] | None = None,
    internal_meta: Mapping[str, Any] | None = None,
    composer_resolution: Mapping[str, Any] | None = None,
    machine_metrics: Mapping[str, Any] | None = None,
    source_revision: Any = "",
    blockers: Sequence[Any] | None = None,
    warnings: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Build a ProductQualityEventV1 without carrying body text.

    ``comment_text`` is used only to compute presence/length and the public
    display contract.  The returned event never contains the text itself.
    """

    reply_meta = _as_mapping(getattr(reply, "meta", None))
    reply_comment = getattr(reply, "comment_text", None)
    if comment_text is None:
        comment_text = reply_comment

    public_meta_map = _as_mapping(public_meta)
    internal_meta_map = dict(reply_meta)
    if isinstance(internal_meta, Mapping):
        # Explicit internal meta can supplement or replace ReplyEnvelope.meta.
        internal_meta_map.update(dict(internal_meta))
    machine_metrics_map = _as_mapping(machine_metrics)
    composer_map = _as_mapping(composer_resolution)

    observation_status = _normalize_status(
        public_meta_map.get("observation_status")
        or internal_meta_map.get("observation_status")
        or machine_metrics_map.get("observation_status")
    )
    comment_stripped = str(comment_text or "").strip()
    comment_present = bool(comment_stripped)
    comment_length = min(len(comment_stripped), 800)
    public_display_reached = should_include_public_input_feedback(comment_stripped, public_meta_map)

    source: dict[str, Any] = {
        "source_type": _normalize_source_type(source_type),
        "source_case_id": _safe_id(source_case_id, max_length=96, default="manual_case"),
    }
    revision = _safe_id(source_revision, max_length=96, default="")
    if revision:
        source["source_revision"] = revision

    text_paths, flag_paths = _forbidden_source_findings(
        public_meta=public_meta_map,
        internal_meta=internal_meta_map,
        composer_resolution=composer_map,
        machine_metrics=machine_metrics_map,
    )

    event_blockers = _dedupe(blockers)
    event_warnings = _dedupe(warnings)
    if text_paths:
        event_blockers.append("forbidden_text_payload_key_detected_in_source")
        event_warnings.extend(f"stripped_forbidden_text_key:{path}" for path in text_paths[:8])
    if flag_paths:
        event_blockers.append("forbidden_contract_or_release_flag_true_in_source")
        event_warnings.extend(f"blocked_forbidden_true_flag:{path}" for path in flag_paths[:8])
    if not public_display_reached:
        event_blockers.append("public_display_not_reached")
    if not comment_present:
        event_blockers.append("comment_text_missing")
    if observation_status != "passed":
        event_blockers.append("observation_status_not_passed")

    sources_for_metrics = (machine_metrics_map, public_meta_map, internal_meta_map)
    binding = _extract_binding(*sources_for_metrics)
    reason_coverage = _extract_reason_coverage(*sources_for_metrics)
    surface_quality = _extract_surface_quality(*sources_for_metrics)
    safety = _extract_safety(*sources_for_metrics)
    extracted_composer = _extract_composer_resolution(composer_map, internal_meta_map, public_meta_map)
    surface_origin = _extract_surface_origin(
        public_display_reached=bool(public_display_reached),
        public_meta=public_meta_map,
        internal_meta=internal_meta_map,
        composer_resolution=composer_map,
        machine_metrics=machine_metrics_map,
    )
    product_surface_validation = _extract_product_surface_validation(
        comment_text=comment_stripped,
        public_meta=public_meta_map,
        internal_meta=internal_meta_map,
        composer_resolution=composer_map,
        machine_metrics=machine_metrics_map,
        surface_origin=surface_origin,
        public_display_reached=bool(public_display_reached),
    )
    surface_quality = dict(surface_quality)
    surface_quality["product_surface_validation"] = product_surface_validation
    surface_quality["product_surface_valid"] = bool(product_surface_validation.get("product_surface_valid"))
    surface_quality["product_surface_requirement_family"] = _safe_id(
        product_surface_validation.get("surface_requirement_family"), max_length=96, default=""
    )
    surface_quality["product_surface_two_stage_required"] = bool(product_surface_validation.get("two_stage_required"))
    surface_quality["product_surface_blocker_code"] = _safe_id(
        product_surface_validation.get("blocker_code"), max_length=160, default=""
    )
    if (
        public_display_reached
        and product_surface_validation.get("blocker_code")
        and product_surface_validation.get("blocker_code") != PRODUCT_SURFACE_BLOCKER_NONE
    ):
        event_blockers.append(str(product_surface_validation.get("blocker_code")))
    event_blockers.extend(
        _detect_gate_recovery_public_leak_blockers(
            public_display_reached=bool(public_display_reached),
            public_meta=public_meta_map,
            internal_meta=internal_meta_map,
            composer_resolution=composer_map,
            machine_metrics=machine_metrics_map,
            surface_origin=surface_origin,
        )
    )
    user_label_connection = _extract_user_label_connection(public_meta_map, internal_meta_map, machine_metrics_map)

    if not binding["binding_passed"]:
        event_blockers.append("binding_not_passed")
    if not reason_coverage["reason_coverage_passed"]:
        event_blockers.append("reason_coverage_not_passed")
    if surface_quality["template_major_count"] > 0:
        event_blockers.append("template_major_detected")
    if surface_quality["unsafe_insight_surface_detected"]:
        event_blockers.append("unsafe_insight_surface_detected")
    if safety["safety_major_count"] > 0:
        event_blockers.append("safety_major_detected")

    event: dict[str, Any] = {
        "schema_version": PRODUCT_QUALITY_EVENT_SCHEMA_VERSION,
        "phase": PRODUCT_QUALITY_EVENT_PHASE,
        "run_id": _safe_id(run_id, max_length=96, default="product_quality_run"),
        "row_id": _safe_id(row_id, max_length=96, default="row"),
        "source": source,
        "family": normalize_product_quality_family(family),
        "observation_status": observation_status,
        "public_display_reached": bool(public_display_reached),
        "comment_text_present": bool(comment_present),
        "comment_text_length": comment_length,
        "public_contract": _public_contract(),
        "gate_results": _extract_gate_results(
            public_meta=public_meta_map,
            internal_meta=internal_meta_map,
            public_display_reached=bool(public_display_reached),
            comment_text_present=bool(comment_present),
        ),
        "binding": binding,
        "reason_coverage": reason_coverage,
        "surface_quality": surface_quality,
        "safety": safety,
        "composer_resolution": extracted_composer,
        "surface_origin": surface_origin,
        "user_label_connection": user_label_connection,
        "blockers": _dedupe(event_blockers),
        "warnings": _dedupe(event_warnings),
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_quality_measurement_event_meta_only(event)
    return event


def build_product_quality_event_from_reply(**kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for callers that use ReplyEnvelope terminology."""

    return normalize_product_quality_event(**kwargs)



def product_quality_event_to_scorecard_row(event: Mapping[str, Any]) -> dict[str, Any]:
    """Flatten ProductQualityEventV1 into text-free scorecard material."""

    assert_product_quality_measurement_event_meta_only(event)
    binding = _as_mapping(event.get("binding"))
    reason = _as_mapping(event.get("reason_coverage"))
    surface = _as_mapping(event.get("surface_quality"))
    safety = _as_mapping(event.get("safety"))
    gate = _as_mapping(event.get("gate_results"))
    surface_origin = _as_mapping(event.get("surface_origin"))
    product_surface_validation = _as_mapping(surface.get("product_surface_validation"))
    row = {
        "schema_version": "cocolon.emlis.product_quality.scorecard_event_from_measurement_event.v1",
        "source_schema_version": event.get("schema_version"),
        "run_id": _safe_id(event.get("run_id"), max_length=96, default=""),
        "row_id": _safe_id(event.get("row_id"), max_length=96, default=""),
        "family": normalize_product_quality_family(event.get("family")),
        "observation_status": _normalize_status(event.get("observation_status")),
        "public_display_reached": bool(event.get("public_display_reached")),
        "comment_text_present": bool(event.get("comment_text_present")),
        "comment_text_length": _to_int(event.get("comment_text_length"), 0, maximum=800),
        "display_gate_passed": bool(gate.get("display_gate_passed")),
        "binding_required_count": _to_int(binding.get("binding_required_count"), 0),
        "binding_supported_sentence_count": _to_int(binding.get("binding_supported_count"), 0),
        "unsupported_binding_count": _to_int(binding.get("unsupported_binding_count"), 0),
        "binding_passed": bool(binding.get("binding_passed")),
        "reason_required_count": _to_int(reason.get("reason_required_count"), 0),
        "reason_covered_count": _to_int(reason.get("reason_covered_count"), 0),
        "reason_coverage_passed": bool(reason.get("reason_coverage_passed")),
        "template_major_count": _to_int(surface.get("template_major_count"), 0),
        "surface_signature_key": _safe_text_token(surface.get("surface_signature_key"), max_length=128),
        "unsafe_insight_surface_detected": bool(surface.get("unsafe_insight_surface_detected")),
        "surface_origin_candidate_source_kind": _safe_id(
            surface_origin.get("candidate_source_kind"), max_length=128, default=""
        ),
        "surface_origin_composer_model": _safe_id(surface_origin.get("composer_model"), max_length=128, default=""),
        "surface_origin_generation_method": _safe_id(surface_origin.get("generation_method"), max_length=128, default=""),
        "surface_origin_public_surface_role": _safe_id(
            surface_origin.get("public_surface_role"), max_length=128, default=""
        ),
        "surface_origin_public_display_allowed_by_boundary": bool(
            surface_origin.get("public_display_allowed_by_boundary")
        ),
        "product_surface_valid": bool(product_surface_validation.get("product_surface_valid")),
        "product_surface_requirement_family": _safe_id(
            product_surface_validation.get("surface_requirement_family"), max_length=96, default=""
        ),
        "product_surface_two_stage_required": bool(product_surface_validation.get("two_stage_required")),
        "product_surface_blocker_code": _safe_id(
            product_surface_validation.get("blocker_code"), max_length=160, default=""
        ),
        "surface_origin_normal_observation_rebuild_attempted": bool(
            surface_origin.get("normal_observation_rebuild_attempted")
        ),
        "surface_origin_normal_observation_rebuild_applied": bool(
            surface_origin.get("normal_observation_rebuild_applied")
        ),
        "surface_origin_complete_initial_surface_recomposition_used": bool(
            surface_origin.get("complete_initial_surface_recomposition_used")
        ),
        "surface_origin_labelled_two_stage_surface_recomposition_used": bool(
            surface_origin.get("labelled_two_stage_surface_recomposition_used")
        ),
        "gate_recovery_material_surface_detected": bool(
            surface_origin.get("gate_recovery_material_surface_detected")
        ),
        "post_final_gate_recovery_material_surface_detected": bool(
            surface_origin.get("post_final_gate_recovery_material_surface_detected")
        ),
        "gate_recovery_template_meta_false_negative_risk": bool(
            surface_origin.get("template_meta_false_negative_risk")
        ),
        "safety_major_count": _to_int(safety.get("safety_major_count"), 0),
        "blockers": _dedupe(event.get("blockers")),
        "product_gate_ready": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert_emlis_ai_product_quality_contract_freeze_meta_only(row, source="product_quality_event_to_scorecard_row")
    return row



def product_quality_scorecard_row_from_sanitized_current_output_event_20260609(
    event: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Project a P3-2 sanitized current-output event into ProductQuality scorecard material.

    The source event is already body-free; this adapter keeps that boundary and
    only reshapes identifiers, display booleans, safe counts, reason codes, and
    surface-origin hints so the existing Product Read Feel inventory/scorecard
    path can consume the row during P3-3.
    """

    source = _as_mapping(event)
    text_paths = _find_forbidden_text_key_paths(source, path="sanitized_current_output_event", limit=8)
    flag_paths = _find_forbidden_true_flag_paths(source, path="sanitized_current_output_event", limit=8)
    family = normalize_product_quality_family(
        source.get("family")
        or source.get("product_readfeel_family")
        or source.get("fixture_family")
        or source.get("coverage_group")
    )
    if family == "unknown":
        # Product Read Feel inventory uses ``unclassified`` for unknown families,
        # but ProductQuality measurement keeps the stricter ``unknown`` boundary.
        product_readfeel_family = "unclassified"
    else:
        product_readfeel_family = family

    observation_status = _normalize_status(
        source.get("observation_status") or source.get("backend_observation_status") or "unavailable"
    )
    public_display_reached = bool(
        source.get("public_reached") is True
        or source.get("public_passed") is True
        or source.get("backend_public_passed") is True
        or source.get("display_confirmed") is True
        or (observation_status == "passed" and source.get("comment_text_present") is True)
    )
    comment_text_present = bool(
        source.get("comment_text_present") is True or source.get("backend_comment_text_present") is True
    )
    reason_codes = _dedupe(
        [
            *_dedupe(source.get("reason_codes")),
            *_dedupe(source.get("rejection_reasons")),
            *_dedupe(source.get("repair_reasons")),
            *_dedupe(source.get("failure_buckets")),
        ]
    )
    warnings: list[str] = []
    if text_paths:
        reason_codes.append("sanitized_current_output_event_text_key_violation")
        warnings.extend(f"forbidden_text_key:{path}" for path in text_paths)
    if flag_paths:
        reason_codes.append("sanitized_current_output_event_forbidden_true_flag")
        warnings.extend(f"forbidden_true_flag:{path}" for path in flag_paths)
    if not public_display_reached and source.get("rn_visible_expected") is True:
        reason_codes.append("public_display_not_reached")
    if not comment_text_present:
        reason_codes.append("comment_text_missing")
    if observation_status != "passed":
        reason_codes.append("observation_status_not_passed")

    row = {
        "schema_version": PRODUCT_QUALITY_SCORECARD_ROW_FROM_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION,
        "source_schema_version": _safe_id(source.get("schema_version"), max_length=128, default=""),
        "source_step": PRODUCT_QUALITY_SANITIZED_CURRENT_OUTPUT_EVENT_CONNECTION_STEP_20260609,
        "run_id": _safe_id(source.get("run_id"), max_length=96, default=""),
        "row_id": _safe_id(source.get("row_id"), max_length=96, default=""),
        "case_id": _safe_id(source.get("case_id"), max_length=96, default=""),
        "fixture_id": _safe_id(source.get("fixture_id") or source.get("case_id"), max_length=96, default=""),
        "family": family,
        "product_readfeel_family": product_readfeel_family,
        "fixture_family": product_readfeel_family,
        "coverage_group": product_readfeel_family,
        "coverage_slices": _dedupe(source.get("coverage_slices")),
        "path": _safe_id(source.get("path"), max_length=96, default=""),
        "path_targets": _dedupe(source.get("path_targets")),
        "target_paths_not_captured": _dedupe(source.get("target_paths_not_captured")),
        "target_path_pending_capture": bool(source.get("target_path_pending_capture") is True),
        "subscription_tier": _safe_id(source.get("subscription_tier"), max_length=32, default=""),
        "observation_status": observation_status,
        "backend_observation_status": observation_status,
        "public_display_reached": public_display_reached,
        "display_confirmed": public_display_reached,
        "public_passed": public_display_reached,
        "backend_public_passed": public_display_reached,
        "rn_visible": bool(source.get("rn_visible") is True),
        "rn_visible_expected": bool(source.get("rn_visible_expected") is True),
        "expected_display": bool(source.get("rn_visible_expected") is not False),
        "eligible_count": 1,
        "passed_display_count": 1 if public_display_reached else 0,
        "comment_text_present": comment_text_present,
        "backend_comment_text_present": comment_text_present,
        "comment_text_length": _to_int(source.get("comment_text_length"), 0, maximum=800),
        "comment_text_fingerprint_present": bool(_safe_id(source.get("comment_text_fingerprint"), max_length=96, default="")),
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "source_display_body_retained": False,
        "product_surface_valid": bool(source.get("product_surface_valid") is True),
        "visible_surface_acceptance_classification": _safe_id(
            source.get("visible_surface_acceptance_classification")
            or _as_mapping(source.get("visible_surface_acceptance")).get("classification"),
            max_length=96,
            default="",
        ),
        "visible_surface_acceptance_action": _safe_id(
            source.get("visible_surface_acceptance_action")
            or _as_mapping(source.get("visible_surface_acceptance")).get("action"),
            max_length=96,
            default="",
        ),
        "visible_surface_acceptance_passed": bool(
            source.get("visible_surface_acceptance_passed") is True
            or _as_mapping(source.get("visible_surface_acceptance")).get("passed") is True
        ),
        "candidate_source_kind": _safe_id(source.get("candidate_source_kind"), max_length=128, default=""),
        "surface_origin_candidate_source_kind": _safe_id(source.get("candidate_source_kind"), max_length=128, default=""),
        "surface_origin_composer_model": _safe_id(source.get("composer_model"), max_length=128, default=""),
        "surface_origin_public_display_allowed_by_boundary": public_display_reached,
        "material_quality": _safe_id(source.get("material_quality"), max_length=128, default=""),
        "renderer_exception": _safe_id(source.get("renderer_exception"), max_length=96, default=""),
        "reason_codes": _dedupe(reason_codes),
        "rejection_reasons": _dedupe(source.get("rejection_reasons")),
        "repair_reasons": _dedupe(source.get("repair_reasons")),
        "warnings": _dedupe(warnings),
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
    }
    assert_emlis_ai_product_quality_contract_freeze_meta_only(
        row,
        source="product_quality_scorecard_row_from_sanitized_current_output_event_20260609",
    )
    return row


def assert_product_quality_measurement_event_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "emlis_ai_product_quality_measurement_event",
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    extra_keys = set(value.keys()) - set(_ALLOWED_TOP_LEVEL_KEYS)
    if extra_keys:
        raise ValueError(f"{source} contains unsupported top-level keys: {sorted(extra_keys)}")
    missing = set(PRODUCT_QUALITY_EVENT_V1_SCHEMA["required"]) - set(value.keys())
    if missing:
        raise ValueError(f"{source} is missing required keys: {sorted(missing)}")
    if value.get("schema_version") != PRODUCT_QUALITY_EVENT_SCHEMA_VERSION:
        raise ValueError(f"{source} has invalid schema_version")
    if value.get("product_gate_ready") is not False:
        raise ValueError(f"{source} must keep product_gate_ready false")
    if value.get("public_release_applied") is not False:
        raise ValueError(f"{source} must keep public_release_applied false")
    if value.get("family") not in _ALLOWED_FAMILIES:
        raise ValueError(f"{source} has unsupported family")
    if value.get("observation_status") not in _ALLOWED_OBSERVATION_STATUSES:
        raise ValueError(f"{source} has unsupported observation_status")

    surface_origin = _as_mapping(value.get("surface_origin"))
    required_surface_origin_keys = {
        "schema_version",
        "candidate_source_kind",
        "composer_model",
        "generation_method",
        "public_surface_role",
        "public_display_allowed_by_boundary",
        "gate_recovery_material_surface_detected",
        "post_final_gate_recovery_material_surface_detected",
        "internal_policy_sentence_leak_risk",
        "template_meta_false_negative_risk",
        "normal_observation_rebuild_attempted",
        "normal_observation_rebuild_applied",
        "complete_initial_surface_recomposition_used",
        "labelled_two_stage_surface_recomposition_used",
        "raw_input_included",
        "comment_text_body_included",
    }
    if set(surface_origin.keys()) != required_surface_origin_keys:
        raise ValueError(f"{source} surface_origin key set changed")
    if surface_origin.get("schema_version") != PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION:
        raise ValueError(f"{source} has invalid surface_origin schema_version")
    for key in (
        "public_display_allowed_by_boundary",
        "gate_recovery_material_surface_detected",
        "post_final_gate_recovery_material_surface_detected",
        "internal_policy_sentence_leak_risk",
        "template_meta_false_negative_risk",
        "normal_observation_rebuild_attempted",
        "normal_observation_rebuild_applied",
        "complete_initial_surface_recomposition_used",
        "labelled_two_stage_surface_recomposition_used",
    ):
        if not isinstance(surface_origin.get(key), bool):
            raise ValueError(f"{source} surface_origin.{key} must be boolean")
    if surface_origin.get("raw_input_included") is not False:
        raise ValueError(f"{source} surface_origin.raw_input_included must be false")
    if surface_origin.get("comment_text_body_included") is not False:
        raise ValueError(f"{source} surface_origin.comment_text_body_included must be false")

    src = _as_mapping(value.get("source"))
    if src.get("source_type") not in _ALLOWED_SOURCE_TYPES:
        raise ValueError(f"{source} has unsupported source.source_type")
    if not _safe_id(src.get("source_case_id"), max_length=96, default=""):
        raise ValueError(f"{source} requires source.source_case_id")

    contract = _as_mapping(value.get("public_contract"))
    for key in _PUBLIC_CONTRACT_KEYS:
        if contract.get(key) is not False:
            raise ValueError(f"{source} public_contract.{key} must be false")
    if set(contract.keys()) != set(_PUBLIC_CONTRACT_KEYS):
        raise ValueError(f"{source} public_contract key set changed")

    if _find_forbidden_text_key_paths(value, path="event", limit=1):
        raise ValueError(f"{source} contains a forbidden text payload key")
    if _find_forbidden_true_flag_paths(value, path="event", limit=1):
        raise ValueError(f"{source} marks a forbidden contract/release flag true")

    # Reuse the Phase 0 contract freeze assertion so new event material cannot
    # quietly diverge from the frozen public/RN/DB boundary.
    assert_emlis_ai_product_quality_contract_freeze_meta_only(value, source=source)


def dump_product_quality_measurement_event(event: Mapping[str, Any]) -> str:
    assert_product_quality_measurement_event_meta_only(event)
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_product_quality_event_schema_material() -> dict[str, Any]:
    """Return schema material plus Phase 0 freeze reference, without body text."""

    material = {
        "schema_version": "cocolon.emlis.product_quality.measurement_event_schema_material.v1",
        "event_schema_version": PRODUCT_QUALITY_EVENT_SCHEMA_VERSION,
        "phase": PRODUCT_QUALITY_EVENT_PHASE,
        "json_schema": PRODUCT_QUALITY_EVENT_V1_SCHEMA,
        "contract_freeze": build_emlis_ai_product_quality_contract_freeze(),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_emlis_ai_product_quality_contract_freeze_meta_only(
        material,
        source="emlis_ai_product_quality_measurement_event_schema_material",
    )
    return material


__all__ = [
    "PRODUCT_QUALITY_EVENT_PHASE",
    "PRODUCT_QUALITY_EVENT_SCHEMA_VERSION",
    "PRODUCT_QUALITY_SCORECARD_ROW_FROM_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION",
    "PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION",
    "PRODUCT_QUALITY_EVENT_V1_SCHEMA",
    "NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL",
    "NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD",
    "BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION",
    "BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC",
    "BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK",
    "BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK",
    "CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE",
    "PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY",
    "assert_product_quality_measurement_event_meta_only",
    "build_product_quality_event_from_reply",
    "build_product_quality_event_schema_material",
    "dump_product_quality_measurement_event",
    "normalize_product_quality_event",
    "normalize_product_quality_family",
    "product_quality_event_to_scorecard_row",
    "product_quality_scorecard_row_from_sanitized_current_output_event_20260609",
]
