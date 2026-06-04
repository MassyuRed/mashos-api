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

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_public_feedback_meta import should_include_public_input_feedback

PRODUCT_QUALITY_EVENT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.product_quality.measurement_event.v1"
)
PRODUCT_QUALITY_EVENT_PHASE: Final = "Phase2_ProductQualityEventV1_Normalizer"

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
    gate_results["bounded_repair_attempted"] = bool(bounded_repair)
    gate_results["post_final_gate_recovery_attempted"] = bool(post_final_recovery)
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
    "PRODUCT_QUALITY_EVENT_V1_SCHEMA",
    "assert_product_quality_measurement_event_meta_only",
    "build_product_quality_event_from_reply",
    "build_product_quality_event_schema_material",
    "dump_product_quality_measurement_event",
    "normalize_product_quality_event",
    "normalize_product_quality_family",
    "product_quality_event_to_scorecard_row",
]
