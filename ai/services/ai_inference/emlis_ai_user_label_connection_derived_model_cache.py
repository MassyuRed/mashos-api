# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 10 Derived User Model cache consideration for User Label Connection.

Phase 10 is intentionally a consideration / contract layer.  It does not add
persistent cache reads or writes, does not change the derived user model table,
does not add public response keys, and does not let cached label connections
become personality, diagnosis, or future-prediction claims.  The initial v1
path remains runtime-computed unless measured runtime cost and product-quality
QA both justify a future design review.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import json
from typing import Any, Final

try:  # Keep this module usable under the flat ai_inference import path.
    from emlis_ai_user_label_connection_product_quality_qa import (
        USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE,
        USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION,
    )
except Exception:  # pragma: no cover - defensive fallback for standalone linting.
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE = "Phase9_ProductQualityQA_BlindQA"
    USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION = (
        "cocolon.emlis.user_label_connection.product_quality_qa.v1"
    )

USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.derived_user_model_cache_consideration.v1"
)
USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_PREVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection_cache.v1"
)
USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_STEP: Final = (
    "UserLabelConnection_DerivedUserModelCacheConsideration_v1"
)
USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_PHASE: Final = (
    "Phase10_DerivedUserModelCacheConsideration"
)

CACHE_DECISION_KEEP_RUNTIME_COMPUTED: Final = "keep_runtime_computed_material_v1"
CACHE_DECISION_FUTURE_REVIEW_ONLY: Final = "future_cache_design_review_only"

RUNTIME_MATERIAL_P95_HEAVY_THRESHOLD_MS: Final = 750.0
RUNTIME_MATERIAL_AVG_HEAVY_THRESHOLD_MS: Final = 450.0
RUNTIME_MEASURED_EVENT_COUNT_MINIMUM: Final = 30
CACHE_STALE_AFTER_DAYS: Final = 14

BLOCKER_RUNTIME_MEASUREMENT_REQUIRED: Final = "runtime_measurement_required_before_cache"
BLOCKER_RUNTIME_NOT_MEASURED_HEAVY: Final = "runtime_computed_material_not_measured_heavy"
BLOCKER_PRODUCT_QUALITY_QA_REQUIRED: Final = "product_quality_qa_pass_required_before_cache"
BLOCKER_DB_PHYSICAL_SCHEMA_CHANGE_FORBIDDEN: Final = "db_physical_schema_change_forbidden_initial_v1"
BLOCKER_INITIAL_V1_CACHE_WRITE_FORBIDDEN: Final = "initial_v1_cache_write_forbidden"
BLOCKER_STALE_CACHE_STRONG_APPLICATION_BLOCKED: Final = "stale_cache_strong_application_blocked"
BLOCKER_CACHE_PERSONALITY_OR_DIAGNOSIS_CLAIM_BLOCKED: Final = (
    "cache_personality_or_diagnosis_claim_blocked"
)
BLOCKER_RAW_TEXT_PAYLOAD_DETECTED: Final = "derived_model_cache_raw_text_payload_detected"
BLOCKER_ACTUAL_CACHE_DATA_DETECTED: Final = "actual_label_connection_cache_data_detected_initial_v1"

_CACHE_EDGE_KEYS: Final = (
    "category_state_edges",
    "state_output_edges",
    "value_line_edges",
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
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
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
        "display_text",
        "displayText",
        "observation_text",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "db_physical_name_changed",
        "db_physical_schema_changed",
        "db_migration_required",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "cache_read_enabled",
        "cache_write_enabled",
        "cache_read_applied",
        "cache_write_applied",
        "cache_applied",
        "cache_persisted",
        "cache_persistence_attempted",
        "derived_user_model_write_attempted",
        "derived_user_model_cache_written",
        "label_connection_cache_written",
        "cache_strongly_applied_to_current_input",
        "stale_cache_strong_application_allowed",
        "cache_used_for_personality_claim",
        "cache_used_for_diagnosis",
        "cache_used_for_future_prediction",
        "cache_used_for_cause_claim",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "raw_fact_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "public_release_applied",
        "product_gate_ready",
        "external_ai_added",
        "local_llm_added",
        "user_model_schema_changed",
        "derived_user_model_schema_changed",
    }
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


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, bool):
            return default
        return float(value)
    except Exception:
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return default
        return int(value)
    except Exception:
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "passed", "pass", "green"}
    return bool(value)


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


def _actual_cache_edge_data_detected(value: Any) -> bool:
    """Detect non-empty future-cache edge arrays in public/contract meta.

    Phase 10 may preview the *shape* of a future cache, but initial v1 must not
    serialize actual label-connection edge arrays into derived user model cache
    material.  Counts and booleans are allowed; edge payload arrays are not.
    """

    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _CACHE_EDGE_KEYS:
                if isinstance(child, Mapping):
                    return True
                if isinstance(child, (list, tuple, set)) and len(child) > 0:
                    return True
            if _actual_cache_edge_data_detected(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            if _actual_cache_edge_data_detected(child):
                return True
    return False




def _contains_personality_or_diagnosis_claim(value: Any) -> bool:
    claim_keys = {
        "personality",
        "personality_claim",
        "personalityClaim",
        "personality_type",
        "personalityType",
        "diagnosis",
        "diagnostic",
        "diagnostic_label",
        "diagnosticLabel",
        "future_prediction",
        "futurePrediction",
        "cause_claim",
        "causeClaim",
        "always_claim",
        "alwaysClaim",
        "should_statement",
        "shouldStatement",
        "trait",
        "tendency_fact",
        "tendencyFact",
    }
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_s = str(key)
            if key_s in claim_keys:
                return True
            if key_s in {"line_is_fact", "cache_line_is_fact", "personality_fact"} and child is True:
                return True
            if _contains_personality_or_diagnosis_claim(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            if _contains_personality_or_diagnosis_claim(child):
                return True
    return False

def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
    except Exception:
        return None


def _parse_dt(value: Any) -> datetime | None:
    text = _clean(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _now(now_iso: str | None = None) -> datetime:
    parsed = _parse_dt(now_iso)
    if parsed is not None:
        return parsed
    return datetime.now(timezone.utc)


def _days_old(updated_at: Any, *, now_iso: str | None = None) -> int | None:
    updated = _parse_dt(updated_at)
    if updated is None:
        return None
    delta = _now(now_iso) - updated
    return max(0, int(delta.total_seconds() // 86400))


def build_user_label_connection_future_cache_schema_preview(*, updated_at: str | None = None) -> dict[str, Any]:
    """Return the safe future-shape preview from the design, without data.

    The preview has empty edge arrays only.  It is not a schema file, not a DB
    migration, and not a write payload for the derived user model store.
    """

    return {
        "interpretive_frame": {
            "label_connection_map": {
                "schema_version": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_PREVIEW_SCHEMA_VERSION,
                "category_state_edges": [],
                "state_output_edges": [],
                "value_line_edges": [],
                "updated_at": _clean(updated_at) or None,
            }
        }
    }


def _runtime_measurement(runtime_metrics: Mapping[str, Any] | None) -> dict[str, Any]:
    metrics = _safe_mapping(runtime_metrics)
    event_count = max(
        _int(metrics.get("measured_event_count")),
        _int(metrics.get("event_count")),
        _int(metrics.get("sample_count")),
    )
    material_avg_ms = max(
        _float(metrics.get("material_avg_ms")),
        _float(metrics.get("material_builder_avg_ms")),
        _float(metrics.get("avg_material_ms")),
        _float(metrics.get("material_builder_ms")),
    )
    material_p95_ms = max(
        _float(metrics.get("material_p95_ms")),
        _float(metrics.get("material_builder_p95_ms")),
        _float(metrics.get("p95_material_ms")),
        _float(metrics.get("p95_material_builder_ms")),
    )
    total_avg_ms = max(
        _float(metrics.get("total_avg_ms")),
        _float(metrics.get("total_runtime_avg_ms")),
        _float(metrics.get("avg_total_ms")),
    )
    measured = event_count >= RUNTIME_MEASURED_EVENT_COUNT_MINIMUM and (
        material_avg_ms > 0.0 or material_p95_ms > 0.0 or total_avg_ms > 0.0
    )
    measured_heavy = measured and (
        material_p95_ms >= RUNTIME_MATERIAL_P95_HEAVY_THRESHOLD_MS
        or material_avg_ms >= RUNTIME_MATERIAL_AVG_HEAVY_THRESHOLD_MS
    )
    return {
        "measured": measured,
        "measured_event_count": event_count,
        "minimum_measured_event_count": RUNTIME_MEASURED_EVENT_COUNT_MINIMUM,
        "material_avg_ms": round(material_avg_ms, 3),
        "material_p95_ms": round(material_p95_ms, 3),
        "total_avg_ms": round(total_avg_ms, 3),
        "runtime_material_avg_heavy_threshold_ms": RUNTIME_MATERIAL_AVG_HEAVY_THRESHOLD_MS,
        "runtime_material_p95_heavy_threshold_ms": RUNTIME_MATERIAL_P95_HEAVY_THRESHOLD_MS,
        "runtime_computed_material_measured_heavy": measured_heavy,
    }


def _product_quality_passed(product_quality_summary: Mapping[str, Any] | None) -> bool:
    summary = _safe_mapping(product_quality_summary)
    return bool(
        summary.get("phase9_product_quality_qa_passed") is True
        and summary.get("product_value_connected_by_qa") is True
        and summary.get("public_release_applied") is not True
    )


def _label_connection_map_from_model(existing_derived_user_model: Any) -> dict[str, Any]:
    model = _safe_mapping(existing_derived_user_model)
    interpretive_frame = _safe_mapping(model.get("interpretive_frame"))
    label_connection_map = _safe_mapping(interpretive_frame.get("label_connection_map"))
    if label_connection_map:
        return label_connection_map

    # Some tests / callers may pass a DerivedUserModel-like object.
    frame = getattr(existing_derived_user_model, "interpretive_frame", None)
    raw_frame = _safe_mapping(frame)
    if raw_frame:
        return _safe_mapping(raw_frame.get("label_connection_map"))
    raw_attr = getattr(frame, "label_connection_map", None)
    return _safe_mapping(raw_attr)


def _existing_cache_summary(existing_derived_user_model: Any, *, now_iso: str | None = None) -> dict[str, Any]:
    label_connection_map = _label_connection_map_from_model(existing_derived_user_model)
    if not label_connection_map:
        return {
            "existing_cache_detected": False,
            "existing_cache_schema_version": None,
            "existing_cache_updated_at_present": False,
            "existing_cache_days_old": None,
            "existing_cache_may_be_stale": False,
            "existing_cache_edge_family_counts": {key: 0 for key in _CACHE_EDGE_KEYS},
            "existing_cache_raw_text_included": False,
            "existing_cache_actual_edge_data_detected": False,
            "existing_cache_personality_or_diagnosis_claim_detected": False,
        }

    edge_counts: dict[str, int] = {}
    for key in _CACHE_EDGE_KEYS:
        edge_counts[key] = len(_listify(label_connection_map.get(key)))
    days = _days_old(label_connection_map.get("updated_at"), now_iso=now_iso)
    stale = days is None or days > CACHE_STALE_AFTER_DAYS
    return {
        "existing_cache_detected": True,
        "existing_cache_schema_version": _clean(label_connection_map.get("schema_version")) or None,
        "existing_cache_updated_at_present": bool(_clean(label_connection_map.get("updated_at"))),
        "existing_cache_days_old": days,
        "existing_cache_may_be_stale": stale,
        "existing_cache_edge_family_counts": edge_counts,
        "existing_cache_raw_text_included": _contains_text_payload_key(label_connection_map),
        "existing_cache_actual_edge_data_detected": _actual_cache_edge_data_detected(label_connection_map),
        "existing_cache_personality_or_diagnosis_claim_detected": _contains_personality_or_diagnosis_claim(label_connection_map),
    }


def _material_runtime_summary(runtime_material_meta: Any) -> dict[str, Any]:
    meta = _safe_mapping(runtime_material_meta)
    edges = [edge for edge in _listify(meta.get("connection_edges")) if isinstance(edge, Mapping)]
    owned_history = _safe_mapping(meta.get("owned_history_points_summary"))
    return {
        "runtime_computed_material_available": bool(meta),
        "runtime_computed_material_schema_version": _clean(meta.get("schema_version")) or None,
        "runtime_computed_material_quality": _clean(meta.get("material_quality")) or None,
        "runtime_computed_edge_count": len(edges),
        "runtime_computed_owned_history_point_count": _int(owned_history.get("point_count")),
        "runtime_computed_raw_text_included": bool(meta.get("raw_text_included") is True),
        "runtime_computed_comment_text_body_included": bool(meta.get("comment_text_body_included") is True),
    }


def build_user_label_connection_derived_model_cache_consideration(
    *,
    runtime_material_meta: Any | None = None,
    product_quality_summary: Mapping[str, Any] | None = None,
    runtime_metrics: Mapping[str, Any] | None = None,
    existing_derived_user_model: Any | None = None,
    now_iso: str | None = None,
) -> dict[str, Any]:
    """Build Phase 10 cache consideration meta without implementing a cache."""

    material_summary = _material_runtime_summary(runtime_material_meta)
    runtime = _runtime_measurement(runtime_metrics)
    product_qa_passed = _product_quality_passed(product_quality_summary)
    existing_cache = _existing_cache_summary(existing_derived_user_model, now_iso=now_iso)

    future_blockers: list[str] = []
    if not runtime["measured"]:
        future_blockers.append(BLOCKER_RUNTIME_MEASUREMENT_REQUIRED)
    elif not runtime["runtime_computed_material_measured_heavy"]:
        future_blockers.append(BLOCKER_RUNTIME_NOT_MEASURED_HEAVY)
    if not product_qa_passed:
        future_blockers.append(BLOCKER_PRODUCT_QUALITY_QA_REQUIRED)

    if existing_cache["existing_cache_may_be_stale"]:
        future_blockers.append(BLOCKER_STALE_CACHE_STRONG_APPLICATION_BLOCKED)
    if existing_cache["existing_cache_raw_text_included"]:
        future_blockers.append(BLOCKER_RAW_TEXT_PAYLOAD_DETECTED)
    if existing_cache.get("existing_cache_actual_edge_data_detected"):
        future_blockers.append(BLOCKER_ACTUAL_CACHE_DATA_DETECTED)
    if existing_cache.get("existing_cache_personality_or_diagnosis_claim_detected"):
        future_blockers.append(BLOCKER_CACHE_PERSONALITY_OR_DIAGNOSIS_CLAIM_BLOCKED)

    eligible_for_future_design_review = not future_blockers and runtime["runtime_computed_material_measured_heavy"]
    decision = CACHE_DECISION_FUTURE_REVIEW_ONLY if eligible_for_future_design_review else CACHE_DECISION_KEEP_RUNTIME_COMPUTED

    meta = {
        "schema_version": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_SCHEMA_VERSION,
        "phase": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_PHASE,
        "step": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_STEP,
        "source_phase": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_PHASE,
        "decision": decision,
        "initial_v1_cache_implemented": False,
        "cache_implementation_deferred": True,
        "runtime_computed_material_kept": True,
        "runtime_computed_material_is_source_of_truth_v1": True,
        "derived_user_model_cache_is_future_candidate_only": True,
        "cache_read_enabled": False,
        "cache_write_enabled": False,
        "cache_read_applied": False,
        "cache_write_applied": False,
        "cache_applied": False,
        "cache_persisted": False,
        "cache_persistence_attempted": False,
        "derived_user_model_write_attempted": False,
        "db_physical_schema_changed": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "comment_text_generated": False,
        "visible_surface_connected_by_this_layer": False,
        "history_connection_applied_by_cache": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "history_raw_text_included": False,
        "raw_fact_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "runtime_material_summary": material_summary,
        "runtime_measurement": runtime,
        "product_quality_dependency": {
            "schema_version": USER_LABEL_CONNECTION_PRODUCT_QUALITY_QA_SCHEMA_VERSION,
            "phase9_product_quality_qa_passed": product_qa_passed,
            "pytest_green_only_is_not_cache_result": True,
            "blind_qa_required_before_cache": True,
        },
        "existing_derived_user_model_cache_summary": existing_cache,
        "future_cache_candidate": {
            "considered": True,
            "eligible_for_future_design_review": eligible_for_future_design_review,
            "blockers": future_blockers,
            "schema_preview": build_user_label_connection_future_cache_schema_preview(updated_at=None),
            "schema_preview_only": True,
            "schema_file_added": False,
            "db_migration_required": False,
            "write_payload": False,
        },
        "stale_cache_safety_contract": {
            "cache_stale_after_days": CACHE_STALE_AFTER_DAYS,
            "stale_cache_strong_application_allowed": False,
            "stale_cache_current_input_strong_apply_blocked": bool(
                existing_cache["existing_cache_detected"] and existing_cache["existing_cache_may_be_stale"]
            ),
            "cache_current_input_strong_application_allowed": False,
        },
        "claim_contract": {
            "cache_used_for_personality_claim": False,
            "cache_used_for_diagnosis": False,
            "cache_used_for_future_prediction": False,
            "cache_used_for_cause_claim": False,
            "diagnosis_allowed": False,
            "personality_claim_allowed": False,
            "cause_claim_allowed": False,
            "advice_allowed": False,
            "future_prediction_allowed": False,
            "always_claim_allowed": False,
            "should_statement_allowed": False,
        },
    }
    assert_user_label_connection_derived_model_cache_contract(meta)
    return meta


def assert_user_label_connection_derived_model_cache_contract(meta: Mapping[str, Any]) -> None:
    """Assert Phase 10 stayed a cache consideration, not a cache implementation."""

    if _contains_text_payload_key(meta):
        raise ValueError("Phase 10 cache consideration must not include raw text/comment payload keys")
    if _flag_true(meta):
        raise ValueError("Phase 10 cache consideration must not turn on cache writes, DB/API/RN changes, or claims")
    if _actual_cache_edge_data_detected(meta):
        raise ValueError("Phase 10 initial v1 must not serialize actual label-connection cache edge arrays")
    return None


def user_label_connection_derived_model_cache_public_summary(meta: Mapping[str, Any]) -> dict[str, Any]:
    """Return a safe boolean/count summary if a caller wants to log Phase 10."""

    safe = _safe_mapping(meta)
    assert_user_label_connection_derived_model_cache_contract(safe)
    future = _safe_mapping(safe.get("future_cache_candidate"))
    runtime = _safe_mapping(safe.get("runtime_measurement"))
    existing_cache = _safe_mapping(safe.get("existing_derived_user_model_cache_summary"))
    return {
        "schema_version": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_SCHEMA_VERSION,
        "phase": USER_LABEL_CONNECTION_DERIVED_MODEL_CACHE_CONSIDERATION_PHASE,
        "decision": _clean(safe.get("decision")) or CACHE_DECISION_KEEP_RUNTIME_COMPUTED,
        "runtime_computed_material_kept": True,
        "initial_v1_cache_implemented": False,
        "cache_implementation_deferred": True,
        "cache_read_enabled": False,
        "cache_write_enabled": False,
        "derived_user_model_write_attempted": False,
        "db_physical_schema_changed": False,
        "public_response_key_added": False,
        "runtime_measured": bool(runtime.get("measured") is True),
        "runtime_computed_material_measured_heavy": bool(
            runtime.get("runtime_computed_material_measured_heavy") is True
        ),
        "future_cache_design_review_candidate": bool(
            future.get("eligible_for_future_design_review") is True
        ),
        "future_cache_blocker_count": len(_listify(future.get("blockers"))),
        "existing_cache_detected": bool(existing_cache.get("existing_cache_detected") is True),
        "existing_cache_may_be_stale": bool(existing_cache.get("existing_cache_may_be_stale") is True),
        "raw_text_included": False,
        "comment_text_body_included": False,
    }
