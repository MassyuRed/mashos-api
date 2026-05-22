# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step1 Runtime Surface Source Lock for EmlisAI.

The lock records which runtime/composer path produced the observation that is
eligible for display.  It is a meta-only diagnostic object.  It intentionally
stores only status, counts, version keys, and source IDs; it never stores raw
input text or the public ``comment_text`` body.
"""

import json
from dataclasses import asdict, is_dataclass
from collections.abc import Mapping, Sequence
from typing import Any

RUNTIME_SURFACE_SOURCE_LOCK_VERSION = "emlis.runtime_surface_source_lock.v1"
RUNTIME_SURFACE_SOURCE_LOCK_STEP = "Step1_Runtime_Surface_Source_Lock"
RUNTIME_COMPOSER_SOURCE_VALUES = (
    "complete_initial",
    "limited",
    "a1_equivalent",
    "unavailable",
    "unknown",
)

_COMPLETE_INITIAL_ALIASES = {
    "complete_initial",
    "complete_composer_initial",
    "complete-composer-initial",
    "complete",
    "complete_composer",
}
_LIMITED_ALIASES = {"limited", "limited_composer", "limited-composer"}
_A1_ALIASES = {"a1", "a1_equivalent", "a_plan_equivalent", "a-plan-equivalent"}
_UNAVAILABLE_ALIASES = {"unavailable", "none", "not_available", "not-generated", "not_generated"}

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
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
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "input_feedback_comment",
    "inputFeedbackComment",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
    "sentence",
    "sentences",
}


class RuntimeSurfaceSourceLockError(ValueError):
    """Raised when a runtime surface source lock violates meta-only contracts."""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _clean(value).lower()


def _to_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = _lower(value)
    if text in {"1", "true", "yes", "y", "passed", "displayed", "joined", "generated", "used"}:
        return True
    if text in {"0", "false", "no", "n", "none", "null", "", "not_used", "missing"}:
        return False
    return default


def _to_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _json_safe(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return None
    if is_dataclass(value):
        return _json_safe(asdict(value), depth=depth + 1)
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _clean(key)
            if not key_text or key_text in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                continue
            safe_item = _json_safe(item, depth=depth + 1)
            if safe_item is not None:
                out[key_text] = safe_item
        return out
    if isinstance(value, (list, tuple, set)):
        return [item for item in (_json_safe(item, depth=depth + 1) for item in value) if item is not None]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _safe_mapping(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        value = asdict(value)
    if not isinstance(value, Mapping):
        return {}
    safe = _json_safe(value)
    return safe if isinstance(safe, dict) else {}


def _safe_sequence(value: Any) -> list[Any]:
    if value is None or isinstance(value, (str, bytes)):
        return []
    if isinstance(value, Sequence):
        return list(value)
    return []


def _candidate_attr(candidate: Any, key: str, default: Any = None) -> Any:
    if isinstance(candidate, Mapping) and key in candidate:
        return candidate.get(key, default)
    return getattr(candidate, key, default)


def _candidate_meta(candidate: Any) -> dict[str, Any]:
    meta = _candidate_attr(candidate, "composer_meta", {})
    return _safe_mapping(meta)


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _first_bool(*values: Any, default: bool = False) -> bool:
    for value in values:
        if value is None:
            continue
        return _to_bool(value, default=default)
    return default


def _map_value(meta: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in meta and meta.get(key) not in (None, ""):
            return meta.get(key)
    return None


def _sub_mapping(meta: Mapping[str, Any], key: str) -> dict[str, Any]:
    return _safe_mapping(meta.get(key)) if isinstance(meta, Mapping) else {}


def _version_from_nested(meta: Mapping[str, Any], nested_key: str, *fallback_keys: str) -> str:
    nested = _sub_mapping(meta, nested_key)
    return _first_non_empty(
        nested.get("version"),
        nested.get("schema_version"),
        nested.get("service_version"),
        nested.get(f"{nested_key}_version"),
        *[meta.get(key) for key in fallback_keys],
    )


def _surface_signature_id(meta: Mapping[str, Any], explicit: Any = None) -> str:
    explicit_text = _clean(explicit)
    if explicit_text:
        return explicit_text
    for signature_key in ("surface_quality_signature", "step2_surface_quality_signature", "surface_signature_v1", "surface_signature"):
        signature = meta.get(signature_key)
        if isinstance(signature, Mapping):
            found = _first_non_empty(
                signature.get("surface_signature_id"),
                signature.get("signature_id"),
                signature.get("signature_hash"),
                signature.get("hash"),
            )
            if found:
                return found
        if isinstance(signature, (str, int, float)):
            found = _clean(signature)
            if found:
                return found
    return _first_non_empty(meta.get("surface_signature_id"), meta.get("signature_id"), meta.get("surface_signature_hash"))


def _merge_runtime_meta(*sources: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in sources:
        safe = _safe_mapping(source)
        if safe:
            merged.update(safe)
    return merged


def _has_token(value: Any, *tokens: str) -> bool:
    text = _lower(value)
    return any(token in text for token in tokens if token)


def _normalize_requested(value: Any) -> str:
    text = _lower(value).replace(" ", "_")
    if not text:
        return ""
    if text in _COMPLETE_INITIAL_ALIASES or _has_token(text, "complete_initial", "complete-composer-initial"):
        return "complete_initial"
    if text in _LIMITED_ALIASES or _has_token(text, "limited"):
        return "limited"
    if text in _A1_ALIASES or _has_token(text, "a_plan", "a1"):
        return "a1_equivalent"
    if text in _UNAVAILABLE_ALIASES:
        return "unavailable"
    return text


def _normalize_composer_source(value: Any) -> str:
    text = _normalize_requested(value)
    if text in RUNTIME_COMPOSER_SOURCE_VALUES:
        return text
    return "unknown"


def _comment_text_length(*, explicit_length: Any = None, comment_text: Any = None) -> int:
    if explicit_length is not None and _clean(explicit_length) != "":
        length = _to_int(explicit_length, default=-1)
        if length >= 0:
            return length
    if comment_text is None:
        return 0
    return len(_clean(comment_text))


def _backend_comment_text_present(explicit_present: Any, length: int) -> bool:
    if explicit_present is not None and _clean(explicit_present) != "":
        return _to_bool(explicit_present)
    return length > 0


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_source_lock_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_source_lock",
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise RuntimeSurfaceSourceLockError(
            f"{source} must stay meta-only and must not include text payload keys"
        )
    for flag in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "response_shape_changed",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "reader_gate_relaxed",
        "gate_relaxed",
        "public_release_applied",
        "product_gate_achieved",
    ):
        if value.get(flag) is True:
            raise RuntimeSurfaceSourceLockError(f"{source} violates fixed contract: {flag}=true")


def resolve_runtime_composer_source(
    *,
    composer_candidate: Any = None,
    resolution_meta: Mapping[str, Any] | None = None,
    runtime_meta: Mapping[str, Any] | None = None,
    diagnostic_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve the runtime composer path without relying on public text bodies."""

    resolution = _safe_mapping(resolution_meta)
    runtime = _merge_runtime_meta(_candidate_meta(composer_candidate), runtime_meta)
    diagnostic = _safe_mapping(diagnostic_meta)

    requested = _normalize_requested(
        _first_non_empty(
            resolution.get("requested_composer"),
            resolution.get("canonical_requested_composer"),
            resolution.get("requested"),
            diagnostic.get("composer_requested"),
            diagnostic.get("requested_composer"),
            runtime.get("composer_requested"),
            runtime.get("requested_composer"),
        )
    )
    model = _first_non_empty(
        _candidate_attr(composer_candidate, "composer_model", ""),
        runtime.get("composer_model"),
        resolution.get("composer_model"),
        diagnostic.get("composer_model"),
        diagnostic.get("runtime_composer_model"),
    )
    candidate_status = _first_non_empty(
        _candidate_attr(composer_candidate, "status", ""),
        runtime.get("composer_status"),
        diagnostic.get("composer_status"),
    )
    candidate_source = _first_non_empty(
        _candidate_attr(composer_candidate, "composer_source", ""),
        runtime.get("composer_source"),
        diagnostic.get("composer_source"),
    )
    resolution_source = _first_non_empty(
        resolution.get("resolution_source"),
        resolution.get("source"),
        resolution.get("registry_source"),
        runtime.get("resolution_source"),
        runtime.get("registry_source"),
        diagnostic.get("registry_source"),
    )
    generation_method = _first_non_empty(
        _candidate_attr(composer_candidate, "generation_method", ""),
        runtime.get("generation_method"),
        diagnostic.get("generation_method"),
    )
    complete_initial_client_used = _first_bool(
        resolution.get("complete_initial_client_used"),
        runtime.get("complete_initial_client_used"),
        runtime.get("complete_composer_client_added"),
        diagnostic.get("complete_initial_client_used"),
        diagnostic.get("runtime_surface_source_complete_initial_client_used"),
        default=False,
    )
    explicit_client_used = _first_bool(
        resolution.get("explicit_client_used"),
        runtime.get("explicit_client_used"),
        diagnostic.get("explicit_client_used"),
        default=False,
    )
    limited_reader_repair = runtime.get("limited_reader_repair")
    limited_reader_repair_applied = _first_bool(
        runtime.get("limited_reader_repair_applied"),
        diagnostic.get("limited_reader_repair_applied"),
        _safe_mapping(limited_reader_repair).get("applied"),
        default=False,
    )

    source_hint = _normalize_composer_source(
        _first_non_empty(
            diagnostic.get("runtime_composer_source"),
            runtime.get("runtime_composer_source"),
            resolution.get("runtime_composer_source"),
            runtime.get("composer_source"),
            resolution.get("composer_source"),
        )
    )
    if source_hint != "unknown":
        composer_source = source_hint
    else:
        connection_status = _lower(resolution.get("connection_status"))
        blocked_resolution = bool(
            connection_status.startswith("blocked_")
            or connection_status in {"not_resolved", "none"}
            or (requested == "complete_initial" and resolution.get("default_client_used") is False)
        )
        complete_initial_signal = bool(
            complete_initial_client_used
            or (not blocked_resolution and _has_token(resolution_source, "complete_initial", "complete_composer"))
            or _has_token(generation_method, "complete_initial", "binding_first_composer")
            or runtime.get("complete_composer_client_added") is True
            or (explicit_client_used and _has_token(model, "emlis_observation_composer", "complete"))
        )
        a1_signal = bool(
            requested == "a1_equivalent"
            or _has_token(resolution_source, "a_plan", "a1")
            or _has_token(model, "a1")
        )
        limited_signal = bool(
            requested == "limited"
            or _has_token(resolution_source, "limited")
            or _has_token(model, "limited")
            or _has_token(generation_method, "limited")
        )
        unavailable_signal = bool(
            requested == "unavailable"
            or (requested == "complete_initial" and blocked_resolution)
            or _lower(candidate_status) in _UNAVAILABLE_ALIASES
            or _lower(candidate_source) in _UNAVAILABLE_ALIASES
            or diagnostic.get("observation_status") == "unavailable"
        )
        if complete_initial_signal:
            composer_source = "complete_initial"
            complete_initial_client_used = True
        elif limited_signal:
            composer_source = "limited"
        elif a1_signal:
            composer_source = "a1_equivalent"
        elif unavailable_signal:
            composer_source = "unavailable"
        else:
            composer_source = "unknown"

    if not requested:
        requested = composer_source if composer_source != "unknown" else ""
    resolved = composer_source
    return {
        "composer_requested": requested,
        "composer_resolved": resolved,
        "composer_source": composer_source,
        "composer_model": model,
        "composer_status": candidate_status,
        "candidate_composer_source": candidate_source,
        "registry_source": resolution_source,
        "generation_method": generation_method,
        "complete_initial_client_used": bool(complete_initial_client_used),
        "explicit_client_used": bool(explicit_client_used),
        "limited_reader_repair_applied": bool(limited_reader_repair_applied),
    }


def build_runtime_surface_source_lock(
    *,
    trace_id: Any = "",
    emotion_log_id: Any = "",
    observation_status: Any = "",
    backend_comment_text_present: Any = None,
    backend_comment_text_length: Any = None,
    comment_text: Any = None,
    display_confirmed: Any = None,
    display_confirmed_source: Any = "",
    coverage_group: Any = "",
    composer_candidate: Any = None,
    resolution_meta: Mapping[str, Any] | None = None,
    runtime_meta: Mapping[str, Any] | None = None,
    diagnostic_meta: Mapping[str, Any] | None = None,
    display_meta: Mapping[str, Any] | None = None,
    surface_signature_id: Any = "",
) -> dict[str, Any]:
    runtime = _merge_runtime_meta(_candidate_meta(composer_candidate), runtime_meta)
    diagnostic = _safe_mapping(diagnostic_meta)
    display = _safe_mapping(display_meta)
    resolved_source = resolve_runtime_composer_source(
        composer_candidate=composer_candidate,
        resolution_meta=resolution_meta,
        runtime_meta=runtime,
        diagnostic_meta=diagnostic,
    )
    status = _first_non_empty(
        observation_status,
        display.get("observation_status"),
        diagnostic.get("observation_status"),
        _candidate_attr(composer_candidate, "observation_status", ""),
        diagnostic.get("backend_observation_status"),
    )
    length = _comment_text_length(
        explicit_length=_first_non_empty(
            backend_comment_text_length,
            diagnostic.get("backend_comment_text_length"),
            diagnostic.get("backend_len"),
            diagnostic.get("rn_len"),
        ),
        comment_text=comment_text,
    )
    present = _backend_comment_text_present(
        backend_comment_text_present
        if backend_comment_text_present is not None
        else _first_non_empty(
            diagnostic.get("backend_comment_text_present"),
            diagnostic.get("comment_text_present"),
            display.get("backend_comment_text_present"),
        ),
        length,
    )
    if display_confirmed is None:
        display_confirmed_value = _to_bool(
            _first_non_empty(
                display.get("display_confirmed"),
                diagnostic.get("display_confirmed"),
                diagnostic.get("product_gate_display_counted"),
            ),
            default=bool(status == "passed" and present),
        )
    else:
        display_confirmed_value = _to_bool(display_confirmed)

    sentence_plan_version = _version_from_nested(
        runtime,
        "sentence_plan",
        "sentence_plan_version",
        "sentence_planner_version",
    )
    surface_realizer_version = _version_from_nested(
        runtime,
        "surface_realizer",
        "surface_realizer_version",
        "surface_realization_version",
    )
    tone_policy_version = _version_from_nested(
        runtime,
        "tone_policy",
        "tone_policy_version",
        "tone_engine_version",
        "product_quality_tone_engine_version",
    )
    self_repair_version = _version_from_nested(
        runtime,
        "self_repair",
        "self_repair_version",
        "self_repair_service_version",
    )

    lock = {
        "schema_version": RUNTIME_SURFACE_SOURCE_LOCK_VERSION,
        "version": RUNTIME_SURFACE_SOURCE_LOCK_VERSION,
        "source_step": RUNTIME_SURFACE_SOURCE_LOCK_STEP,
        "step": RUNTIME_SURFACE_SOURCE_LOCK_STEP,
        "source": "runtime_surface_source_lock",
        "lock_ready": True,
        "runtime_surface_source_lock_ready": True,
        "runtime_surface_source_locked": True,
        "trace_id": _first_non_empty(trace_id, diagnostic.get("trace_id"), display.get("trace_id")),
        "emotion_log_id": _first_non_empty(emotion_log_id, diagnostic.get("emotion_log_id"), display.get("emotion_log_id")),
        "observation_status": status,
        "backend_comment_text_present": bool(present),
        "backend_comment_text_length": int(max(0, length)),
        "display_confirmed": bool(display_confirmed_value),
        "display_confirmed_source": _first_non_empty(
            display_confirmed_source,
            display.get("display_confirmed_source"),
            diagnostic.get("display_confirmed_source"),
            "backend_passed_body_present" if status == "passed" and present else "not_confirmed",
        ),
        "coverage_group": _first_non_empty(
            coverage_group,
            runtime.get("coverage_group"),
            runtime.get("coverage_scope"),
            diagnostic.get("coverage_group"),
            diagnostic.get("coverage_scope"),
        ),
        "composer_requested": resolved_source["composer_requested"],
        "composer_resolved": resolved_source["composer_resolved"],
        "composer_source": resolved_source["composer_source"],
        "composer_model": resolved_source["composer_model"],
        "composer_status": resolved_source["composer_status"],
        "candidate_composer_source": resolved_source["candidate_composer_source"],
        "registry_source": resolved_source["registry_source"],
        "generation_method": resolved_source["generation_method"],
        "complete_initial_client_used": bool(resolved_source["complete_initial_client_used"]),
        "explicit_client_used": bool(resolved_source["explicit_client_used"]),
        "limited_reader_repair_applied": bool(resolved_source["limited_reader_repair_applied"]),
        "sentence_plan_version": sentence_plan_version,
        "surface_realizer_version": surface_realizer_version,
        "tone_policy_version": tone_policy_version,
        "self_repair_version": self_repair_version,
        "surface_signature_id": _surface_signature_id(runtime, explicit=surface_signature_id),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    assert_runtime_surface_source_lock_meta_only(lock)
    return lock


def dump_runtime_surface_source_lock(lock: Mapping[str, Any]) -> str:
    data = dict(lock or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_runtime_surface_source_lock_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "RUNTIME_COMPOSER_SOURCE_VALUES",
    "RUNTIME_SURFACE_SOURCE_LOCK_STEP",
    "RUNTIME_SURFACE_SOURCE_LOCK_VERSION",
    "RuntimeSurfaceSourceLockError",
    "assert_runtime_surface_source_lock_meta_only",
    "build_runtime_surface_source_lock",
    "dump_runtime_surface_source_lock",
    "resolve_runtime_composer_source",
]
