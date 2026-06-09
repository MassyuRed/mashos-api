# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-3 Sanitized Event / Inventory connection for Product Read Feel baseline.

P3-2 creates local review packets and body-free sanitized current-output events.
This module connects only the body-free events to the existing Product Read Feel
inventory and scorecard layers. It also projects the same body-free rows through
ProductQuality scorecard-row material so P3-3 touches the intended existing
measurement boundary without creating or retaining display bodies.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import assert_emlis_ai_product_quality_contract_freeze_meta_only
from emlis_ai_product_quality_measurement_event import (
    PRODUCT_QUALITY_SCORECARD_ROW_FROM_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION,
    product_quality_scorecard_row_from_sanitized_current_output_event_20260609,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    assert_product_readfeel_current_output_inventory_meta_only,
    build_product_readfeel_current_output_inventory,
    normalize_product_readfeel_current_output_inventory_to_scorecard_fields,
)
from emlis_ai_product_readfeel_scorecard import (
    assert_product_readfeel_scorecard_meta_only,
    build_product_readfeel_scorecard,
    normalize_product_readfeel_scorecard_to_scorecard_fields,
)
from fixtures.emlis_ai_product_readfeel_p3_local_output_capture_20260609 import (
    PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609,
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609,
    build_product_readfeel_p3_local_output_capture_20260609,
)

PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.inventory_connection.20260609.v1"
)
PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.inventory_connection_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_STEP_20260609: Final = "P3-3_Sanitized_Event_Inventory_Connection"
PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_SanitizedEventInventoryConnection_20260609"
)
PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_PROFILE_20260609: Final = "local_product_readfeel_p3_inventory_connection"

_FORBIDDEN_TEXT_KEYS: Final[frozenset[str]] = frozenset({
    "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
    "input", "input_text", "inputText", "user_input", "userInput",
    "current_input", "currentInput", "history_context", "historyContext",
    "memo", "memo_text", "memoText", "memo_action", "memoAction",
    "comment_text", "commentText", "comment_text_body", "commentTextBody",
    "candidate_body", "candidateBody", "reply_text", "replyText", "surface_text",
    "surfaceText", "display_text", "displayText", "body", "text",
})
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset({
    "api_route_changed", "request_key_changed", "response_shape_changed",
    "public_response_key_added", "public_response_key_change", "db_physical_name_changed",
    "rn_visible_contract_changed", "rn_visible_title_changed", "display_gate_relaxed",
    "grounding_gate_relaxed", "reader_gate_relaxed", "template_gate_relaxed", "gate_relaxed",
    "raw_input_included", "raw_text_included", "input_text_included", "comment_text_included",
    "comment_text_body_included", "candidate_body_included", "surface_body_included",
    "exact_comment_text_required", "exact_comment_text_locked", "case_specific_runtime_branch",
    "case_specific_runtime_branch_allowed", "case_specific_runtime_condition_allowed",
    "runtime_branching_uses_fixture_strings", "fixture_text_used_for_runtime_branching",
    "fixed_sentence_template_added", "fixed_sentence_template_used", "input_specific_template_added",
    "product_gate_ready", "product_gate_reached", "product_gate_public_release_applied",
    "public_release_applied", "product_quality_released", "machine_metrics_used_for_read_feeling",
    "read_feeling_auto_filled_from_machine_metrics", "read_feeling_auto_estimation_allowed",
    "external_ai_used", "local_llm_used",
})


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value)
    if not text:
        return default
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"
    clipped = text[:max_length]
    return clipped if all(ch in allowed for ch in clipped) else default


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        raw_values: list[Any] = []
    elif isinstance(values, (str, bytes, bytearray)):
        raw_values = [values]
    else:
        raw_values = list(values) if isinstance(values, Iterable) else [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_TEXT_KEYS or _contains_forbidden_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_TRUE_FLAGS and child is True:
                return child_path
            nested = _forbidden_true_flag_path(child, path=child_path)
            if nested:
                return nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def _extract_sanitized_events(source: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if source is None:
        capture = build_product_readfeel_p3_local_output_capture_20260609()
        events = capture.get("sanitized_current_output_events") or []
    elif isinstance(source, Mapping):
        events = source.get("sanitized_current_output_events") if "sanitized_current_output_events" in source else [source]
    else:
        events = list(source)
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)):
        raise ValueError("P3-3 sanitized events must be a sequence")
    for event in events:
        if not isinstance(event, Mapping):
            raise ValueError("P3-3 sanitized events must contain mappings")
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(
        events,
        source="product_readfeel_p3_inventory_connection.source_events",
    )
    return list(events)


def _build_product_quality_rows(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = [product_quality_scorecard_row_from_sanitized_current_output_event_20260609(event) for event in events]
    for row in rows:
        assert_emlis_ai_product_quality_contract_freeze_meta_only(
            row,
            source="product_readfeel_p3_inventory_connection.product_quality_scorecard_row",
        )
    return rows


def assert_product_readfeel_p3_inventory_connection_meta_only_20260609(
    payload: Mapping[str, Any] | Sequence[Any] | None,
    *,
    source: str = "product_readfeel_p3_inventory_connection",
) -> None:
    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} contains raw input or comment_text body key")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} marks forbidden true flag at {flag_path}")
    if isinstance(payload, Mapping):
        if payload.get("comment_text_body_included") is not False:
            raise ValueError(f"{source} must keep comment_text_body_included false")
        if payload.get("raw_input_included") is not False:
            raise ValueError(f"{source} must keep raw_input_included false")
        if payload.get("product_gate_ready") is not False:
            raise ValueError(f"{source} must keep product_gate_ready false")
        if payload.get("public_release_applied") is not False:
            raise ValueError(f"{source} must keep public_release_applied false")
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for index, item in enumerate(payload):
            if isinstance(item, Mapping):
                assert_product_readfeel_p3_inventory_connection_meta_only_20260609(item, source=f"{source}[{index}]")


def _summary_from_connection(connection: Mapping[str, Any]) -> dict[str, Any]:
    events = list(connection.get("sanitized_current_output_events") or [])
    inventory = dict(connection.get("current_output_inventory") or {})
    scorecard = dict(connection.get("product_readfeel_scorecard") or {})
    product_quality_rows = list(connection.get("product_quality_scorecard_rows") or [])
    family_counts = Counter(str(event.get("family") or event.get("product_readfeel_family") or "") for event in events)
    coverage_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    path_counts: Counter[str] = Counter()
    for event in events:
        coverage_counts.update(_dedupe(event.get("coverage_slices")))
        reason_counts.update(_dedupe(event.get("reason_codes")))
        path_counts.update([_safe_identifier(event.get("path"), default="render_default_path", max_length=80)])
    missing_families = list(inventory.get("missing_families") or [])
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_STEP_20260609,
        "run_id": _safe_identifier(connection.get("run_id"), default="", max_length=96),
        "run_profile": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_PROFILE_20260609,
        "source_event_schema_version": PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609,
        "product_quality_scorecard_row_schema_version": PRODUCT_QUALITY_SCORECARD_ROW_FROM_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION,
        "sanitized_current_output_event_count": len(events),
        "sanitized_event_count": len(events),
        "product_quality_scorecard_row_count": len(product_quality_rows),
        "inventory_item_count": int(inventory.get("item_count") or 0),
        "scorecard_family_result_count": len(scorecard.get("family_results") or []),
        "required_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "family_counts": dict(family_counts),
        "observed_families": list(inventory.get("observed_families") or []),
        "missing_families": missing_families,
        "all_required_families_observed": missing_families == [],
        "coverage_slice_counts": dict(coverage_counts),
        "path_counts": dict(path_counts),
        "reason_code_counts": dict(reason_counts),
        "family_verdicts": dict(inventory.get("family_verdicts") or {}),
        "scorecard_family_verdicts": dict(scorecard.get("family_verdicts") or {}),
        "scorecard_aggregate_verdict": _safe_identifier(scorecard.get("aggregate_verdict"), default="", max_length=40),
        "scorecard_next_action": _safe_identifier(scorecard.get("next_action"), default="", max_length=96),
        "failure_bucket_counts": dict(inventory.get("failure_bucket_counts") or {}),
        "v1_fix_families": list(inventory.get("v1_fix_families") or []),
        "v2_structure_insight_backlog_families": list(inventory.get("v2_structure_insight_backlog_families") or []),
        "current_output_inventory_connected": True,
        "product_quality_scorecard_rows_created": True,
        "product_readfeel_scorecard_connected": True,
        "p3_3_inventory_connected": True,
        "p3_3_scorecard_connected": True,
        "p3_4_verdict_split_applied": False,
        "blind_qa_ratings_applied": False,
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": True,
        "p3_2_sanitized_current_output_event_used": True,
        "p3_3_inventory_connection_completed": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "local_review_packet_retained_in_summary": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_requires_blind_qa": True,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609(summary, source="product_readfeel_p3_inventory_connection_summary")
    return summary


def build_product_readfeel_p3_inventory_connection_20260609(
    *,
    sanitized_current_output_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    sanitized_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    capture: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if capture is None and sanitized_current_output_events is None and sanitized_events is None and renderer is not None:
        capture = build_product_readfeel_p3_local_output_capture_20260609(renderer=renderer, run_id=run_id)
    source = capture if capture is not None else (sanitized_current_output_events if sanitized_current_output_events is not None else sanitized_events)
    events = _extract_sanitized_events(source)
    run_id_value = _safe_identifier(run_id, default="", max_length=96) or _safe_identifier(
        events[0].get("run_id") if events else "",
        default="p3_3_inventory_connection",
        max_length=96,
    )
    product_quality_rows = _build_product_quality_rows(events)
    inventory = build_product_readfeel_current_output_inventory(events=events, run_id=run_id_value)
    inventory_from_product_quality_rows = build_product_readfeel_current_output_inventory(events=product_quality_rows, run_id=run_id_value)
    inventory_fields = normalize_product_readfeel_current_output_inventory_to_scorecard_fields(inventory)
    scorecard = build_product_readfeel_scorecard(current_output_inventory=inventory, run_id=run_id_value)
    scorecard_fields = normalize_product_readfeel_scorecard_to_scorecard_fields(scorecard)
    connection = {
        "schema_version": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_PROFILE_20260609,
        "sanitized_current_output_events": list(events),
        "product_quality_scorecard_rows": product_quality_rows,
        "current_output_inventory": inventory,
        "current_output_inventory_fields": inventory_fields,
        "current_output_inventory_from_product_quality_rows": inventory_from_product_quality_rows,
        "product_readfeel_scorecard": scorecard,
        "product_readfeel_scorecard_fields": scorecard_fields,
        "current_output_inventory_connected": True,
        "product_quality_scorecard_rows_created": True,
        "product_readfeel_scorecard_connected": True,
        "p3_3_inventory_connection_completed": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
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
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    connection["public_summary"] = _summary_from_connection(connection)
    connection["summary"] = connection["public_summary"]
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609(connection)
    assert_product_readfeel_current_output_inventory_meta_only(inventory)
    assert_product_readfeel_current_output_inventory_meta_only(inventory_from_product_quality_rows)
    assert_product_readfeel_scorecard_meta_only(scorecard)
    return connection


def build_product_readfeel_p3_inventory_connection_public_summary_20260609(
    connection_or_events: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if isinstance(connection_or_events, Mapping) and connection_or_events.get("schema_version") == PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609:
        summary = dict(connection_or_events.get("public_summary") or _summary_from_connection(connection_or_events))
    else:
        summary = build_product_readfeel_p3_inventory_connection_20260609(
            sanitized_current_output_events=connection_or_events,
        )["public_summary"]
    assert_product_readfeel_p3_inventory_connection_meta_only_20260609(summary)
    return summary


def dump_product_readfeel_p3_inventory_connection_public_summary_20260609(
    connection_or_events: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> str:
    summary = build_product_readfeel_p3_inventory_connection_public_summary_20260609(connection_or_events)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def dump_product_readfeel_p3_inventory_connection_summary_20260609(
    connection_or_events: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> str:
    return dump_product_readfeel_p3_inventory_connection_public_summary_20260609(connection_or_events)


__all__ = [
    "PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_VERSION_20260609",
    "PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_INVENTORY_CONNECTION_STEP_20260609",
    "assert_product_readfeel_p3_inventory_connection_meta_only_20260609",
    "build_product_readfeel_p3_inventory_connection_20260609",
    "build_product_readfeel_p3_inventory_connection_public_summary_20260609",
    "dump_product_readfeel_p3_inventory_connection_public_summary_20260609",
    "dump_product_readfeel_p3_inventory_connection_summary_20260609",
]
