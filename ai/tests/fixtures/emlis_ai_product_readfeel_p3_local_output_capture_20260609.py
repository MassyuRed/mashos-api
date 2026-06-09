# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-2 local current-output capture for Product Read Feel baseline cases.

This module is deliberately local-QA oriented.  It creates two separated
materials from the P3-1 synthetic baseline matrix:

* Local Review Packet: contains synthetic ``current_input`` and rendered
  ``comment_text`` so a reviewer can judge Product Read Feel.
* Sanitized Current Output Events: body-free rows that can be passed to
  inventory / scorecard layers without leaking raw input or comment bodies.

The module does not change RN, API, DB, public response shape, gates, composer
selection, or runtime behavior.  It only calls the existing renderer and records
what came back under the P3-2 boundary.
"""

import asyncio
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import inspect
import json
from typing import Any, Final
from uuid import uuid4

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    assert_product_readfeel_current_output_inventory_meta_only,
)
from emlis_ai_product_surface_validation import PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    PATH_RENDER_DEFAULT,
    PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609,
    SLICE_HISTORY_LINE_ELIGIBLE,
    assert_product_readfeel_baseline_case_matrix_contract_20260609,
    assert_product_readfeel_baseline_public_safe_meta_only_20260609,
    build_product_readfeel_baseline_cases_20260609,
)

PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_RUN_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.local_output_capture_run.20260609.v1"
)
PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.local_review_packet.20260609.v1"
)
PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_ITEM_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.local_review_packet_item.20260609.v1"
)
PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.current_output_event.20260609.v1"
)
PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.local_output_capture_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609: Final = (
    "P3-2_Local_Output_Capture"
)
PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_LocalOutputCapture_20260609"
)
PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_PROFILE_20260609: Final = "local_product_readfeel_p3_qa"
PRODUCT_READFEEL_P3_LOCAL_REVIEW_VISIBILITY_20260609: Final = "local_qa_only"
PRODUCT_READFEEL_P3_LOCAL_REVIEW_COMMIT_POLICY_20260609: Final = (
    "do_not_commit_if_contains_real_user_text"
)
PRODUCT_READFEEL_P3_DEFAULT_USER_ID_20260609: Final = "local_product_readfeel_p3_user"
PRODUCT_READFEEL_P3_DEFAULT_TIMEZONE_20260609: Final = "Asia/Tokyo"

VERDICT_NOT_EVALUATED: Final = "NOT_EVALUATED"

_SANITIZED_FORBIDDEN_TEXT_KEYS_20260609: Final[frozenset[str]] = frozenset(
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
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS_20260609: Final[frozenset[str]] = frozenset(
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
        "exact_comment_text_required",
        "exact_comment_text_locked",
        "case_specific_runtime_branch",
        "case_specific_runtime_branch_allowed",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "product_gate_ready",
        "product_gate_reached",
        "public_release_applied",
        "product_quality_released",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


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
        text_value = _clean(value)
        if text_value and text_value not in seen:
            seen.add(text_value)
            out.append(text_value)
    return out


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text_value = _clean(value)
    if not text_value:
        return default
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"
    clipped = text_value[:max_length]
    return clipped if all(ch in allowed for ch in clipped) else default


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _default_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"p3local_{stamp}_{uuid4().hex[:8]}"


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text_value = str(value).strip().lower()
    if text_value in {"true", "1", "yes", "y", "on", "passed", "pass", "valid", "allow"}:
        return True
    if text_value in {"false", "0", "no", "n", "off", "failed", "fail", "invalid", "block", "blocked"}:
        return False
    return default


def _get_path(source: Mapping[str, Any], path: str) -> Any:
    current: Any = source
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current.get(part)
    return current


def _first_path(*sources: Mapping[str, Any], paths: Sequence[str], default: Any = "") -> Any:
    for path in paths:
        for source in sources:
            value = _get_path(source, path)
            if value not in (None, "", [], {}):
                return value
    return default


def _contains_forbidden_key(value: Any, forbidden_keys: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in forbidden_keys:
                return True
            if _contains_forbidden_key(child, forbidden_keys):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child, forbidden_keys) for child in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_TRUE_FLAGS_20260609 and child is True:
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


def _default_renderer() -> Callable[..., Any]:
    from emlis_ai_reply_service import render_emlis_ai_reply

    return render_emlis_ai_reply


async def _call_renderer(renderer: Callable[..., Any], **kwargs: Any) -> Any:
    rendered = renderer(**kwargs)
    if inspect.isawaitable(rendered):
        return await rendered
    return rendered


def _extract_reply_comment_text(reply: Any) -> str:
    if isinstance(reply, Mapping):
        return _clean(reply.get("comment_text") or reply.get("commentText"))
    return _clean(getattr(reply, "comment_text", ""))


def _extract_reply_meta(reply: Any) -> dict[str, Any]:
    if isinstance(reply, Mapping):
        meta = reply.get("meta") or reply.get("emlis_ai") or {}
        return dict(meta) if isinstance(meta, Mapping) else {}
    meta = getattr(reply, "meta", None)
    return dict(meta) if isinstance(meta, Mapping) else {}


def _primary_capture_path(case: Mapping[str, Any]) -> str:
    path_targets = _dedupe(case.get("path_targets"))
    if PATH_RENDER_DEFAULT in path_targets:
        return PATH_RENDER_DEFAULT
    return _safe_identifier(path_targets[0] if path_targets else PATH_RENDER_DEFAULT, default=PATH_RENDER_DEFAULT)


def _fingerprint(value: str) -> str:
    if not value:
        return ""
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _public_observation_status(public_meta: Mapping[str, Any], internal_meta: Mapping[str, Any]) -> str:
    return _safe_identifier(
        public_meta.get("observation_status")
        or internal_meta.get("observation_status")
        or internal_meta.get("public_observation_status")
        or "unavailable",
        default="unavailable",
        max_length=40,
    )


def _visible_surface_acceptance(public_meta: Mapping[str, Any], internal_meta: Mapping[str, Any]) -> dict[str, Any]:
    gate = _safe_mapping(public_meta.get("visible_surface_acceptance_gate"))
    if not gate:
        gate = _safe_mapping(internal_meta.get("visible_surface_acceptance_gate"))
    classification = _safe_identifier(
        gate.get("classification") or gate.get("visible_surface_acceptance_classification"),
        default="",
        max_length=80,
    )
    action = _safe_identifier(gate.get("action") or gate.get("visible_surface_acceptance_action"), default="", max_length=80)
    passed = gate.get("passed")
    if passed is None:
        passed = gate.get("gate_passed")
    return {
        "classification": classification,
        "action": action,
        "passed": _to_bool(passed, default=False),
    }


def _product_surface_valid(public_meta: Mapping[str, Any], *, public_reached: bool) -> bool:
    surface = _safe_mapping(public_meta.get(PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY))
    if not surface:
        return public_reached
    for key in ("product_surface_valid", "public_surface_valid", "surface_valid", "valid", "passed"):
        if key in surface:
            return _to_bool(surface.get(key), default=public_reached)
    return public_reached


def _reply_summary(public_meta: Mapping[str, Any], internal_meta: Mapping[str, Any]) -> dict[str, Any]:
    visible = _visible_surface_acceptance(public_meta, internal_meta)
    return {
        "observation_reply_kind": _safe_identifier(
            _first_path(
                public_meta,
                internal_meta,
                paths=(
                    "observation_reply_kind",
                    "observation_reply_meta.response_kind",
                    "internal_response_contract.response_kind",
                    "step10_observation_display_repair_integration.response_kind",
                ),
                default="",
            ),
            default="",
            max_length=96,
        ),
        "material_quality": _safe_identifier(
            _first_path(
                public_meta,
                internal_meta,
                paths=(
                    "diagnostic_summary.material_quality",
                    "observation_quality.material_quality",
                    "material_quality",
                    "phase20_13_observation_quality.material_quality",
                ),
                default="",
            ),
            default="",
            max_length=96,
        ),
        "candidate_source_kind": _safe_identifier(
            _first_path(
                public_meta,
                internal_meta,
                paths=(
                    "public_surface_lineage.candidate_source_kind",
                    "surface_origin.candidate_source_kind",
                    "candidate_source_kind",
                    "diagnostic_summary.candidate_source_kind",
                ),
                default="",
            ),
            default="",
            max_length=96,
        ),
        "composer_model": _safe_identifier(
            _first_path(
                public_meta,
                internal_meta,
                paths=(
                    "complete_initial_surface_recomposition.composer_model",
                    "labelled_two_stage_surface_recomposition.composer_model",
                    "composer_model",
                    "composer_resolution.composer_model",
                ),
                default="",
            ),
            default="",
            max_length=96,
        ),
        "visible_surface_acceptance": visible,
        "rejection_reasons": _dedupe(
            _first_path(
                public_meta,
                internal_meta,
                paths=("rejection_reasons", "diagnostic_summary.rejection_reasons"),
                default=[],
            )
        ),
        "repair_reasons": _dedupe(
            _first_path(
                public_meta,
                internal_meta,
                paths=(
                    "repair_reasons",
                    "step10_observation_display_repair_integration.repair_reasons",
                    "diagnostic_summary.repair_reasons",
                ),
                default=[],
            )
        ),
        "fallback_reason_family": _safe_identifier(
            _first_path(
                public_meta,
                internal_meta,
                paths=("fallback_reason_family", "diagnostic_summary.fallback_reason_family"),
                default="",
            ),
            default="",
            max_length=96,
        ),
    }


def _local_review_item(
    *,
    run_id: str,
    row_id: str,
    case: Mapping[str, Any],
    path: str,
    target_paths_not_captured: Sequence[str],
    comment_text: str,
    public_meta: Mapping[str, Any],
    internal_meta: Mapping[str, Any],
    renderer_exception: str = "",
) -> dict[str, Any]:
    current_input = deepcopy(case.get("current_input") or {})
    history_context = deepcopy(case.get("history_context") or {})
    summary = _reply_summary(public_meta, internal_meta)
    observation_status = _public_observation_status(public_meta, internal_meta)
    comment_text_present = bool(comment_text.strip())
    public_reached = observation_status == "passed" and comment_text_present
    expected = _safe_mapping(case.get("expected_contract"))
    product_surface_valid = _product_surface_valid(public_meta, public_reached=public_reached)
    visible = _safe_mapping(summary.get("visible_surface_acceptance"))
    item = {
        "schema_version": PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_ITEM_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_ITEM_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609,
        "visibility": PRODUCT_READFEEL_P3_LOCAL_REVIEW_VISIBILITY_20260609,
        "run_id": run_id,
        "row_id": row_id,
        "case_id": str(case.get("case_id") or row_id),
        "family": str(case.get("family") or case.get("product_readfeel_family") or ""),
        "product_readfeel_family": str(case.get("product_readfeel_family") or case.get("family") or ""),
        "coverage_slices": _dedupe(case.get("coverage_slices")),
        "path": path,
        "path_targets": _dedupe(case.get("path_targets")),
        "target_paths_not_captured": _dedupe(target_paths_not_captured),
        "subscription_tier": _safe_identifier(case.get("subscription_tier"), default="free", max_length=32),
        "current_input": current_input,
        "history_context": history_context,
        "comment_text": comment_text,
        "observation_status": observation_status,
        "observation_reply_kind": summary["observation_reply_kind"],
        "comment_text_present": comment_text_present,
        "comment_text_length": len(comment_text),
        "public_reached": public_reached,
        "rn_visible_expected": bool(expected.get("rn_visible_expected", True)),
        "rn_visible_actual": public_reached,
        "product_surface_valid": product_surface_valid,
        "visible_surface_acceptance_classification": visible.get("classification", ""),
        "visible_surface_acceptance_action": visible.get("action", ""),
        "visible_surface_acceptance_passed": bool(visible.get("passed")),
        "material_quality": summary["material_quality"],
        "candidate_source_kind": summary["candidate_source_kind"],
        "composer_model": summary["composer_model"],
        "rejection_reasons": summary["rejection_reasons"],
        "repair_reasons": summary["repair_reasons"],
        "fallback_reason_family": summary["fallback_reason_family"],
        "renderer_exception": renderer_exception,
        "reply_meta_local_summary": summary,
        "local_qa_only": True,
        "synthetic_case_material": bool(current_input.get("synthetic_case_material") is True),
        "contains_raw_input": True,
        "contains_comment_text_body": True,
        "public_meta_body_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    return item


def _sanitized_event_from_local_item(item: Mapping[str, Any]) -> dict[str, Any]:
    comment_text = _clean(item.get("comment_text"))
    comment_text_present = bool(item.get("comment_text_present"))
    family = str(item.get("family") or item.get("product_readfeel_family") or "")
    history_context = _safe_mapping(item.get("history_context"))
    target_paths_not_captured = _dedupe(item.get("target_paths_not_captured"))
    reason_codes = _dedupe(
        [
            *_dedupe(item.get("rejection_reasons")),
            *_dedupe(item.get("repair_reasons")),
            *( ["renderer_exception"] if item.get("renderer_exception") else [] ),
            *( ["target_path_pending_capture"] if target_paths_not_captured else [] ),
        ]
    )
    public_reached = bool(item.get("public_reached"))
    event = {
        "schema_version": PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609,
        "run_id": _safe_identifier(item.get("run_id"), default="", max_length=96),
        "row_id": _safe_identifier(item.get("row_id"), default="", max_length=96),
        "case_id": _safe_identifier(item.get("case_id"), default="", max_length=96),
        "fixture_id": _safe_identifier(item.get("case_id"), default="", max_length=96),
        "family": family,
        "product_readfeel_family": family,
        "fixture_family": family,
        "coverage_group": family,
        "coverage_slices": _dedupe(item.get("coverage_slices")),
        "path": _safe_identifier(item.get("path"), default=PATH_RENDER_DEFAULT, max_length=80),
        "path_targets": _dedupe(item.get("path_targets")),
        "target_paths_not_captured": target_paths_not_captured,
        "target_path_pending_capture": bool(target_paths_not_captured),
        "subscription_tier": _safe_identifier(item.get("subscription_tier"), default="free", max_length=32),
        "history_context_enabled": bool(history_context.get("enabled")),
        "history_owned_record_count": int(history_context.get("owned_record_count") or 0),
        "history_evidence_record_count": int(history_context.get("evidence_record_count") or 0),
        "public_reached": public_reached,
        "public_passed": public_reached,
        "backend_public_passed": public_reached,
        "display_confirmed": public_reached,
        "rn_visible": bool(item.get("rn_visible_actual")),
        "rn_visible_expected": bool(item.get("rn_visible_expected")),
        "expected_display": True,
        "eligible_count": 1,
        "passed_display_count": 1 if public_reached else 0,
        "product_surface_valid": bool(item.get("product_surface_valid")),
        "observation_status": _safe_identifier(item.get("observation_status"), default="unavailable", max_length=40),
        "backend_observation_status": _safe_identifier(item.get("observation_status"), default="unavailable", max_length=40),
        "observation_reply_kind": _safe_identifier(item.get("observation_reply_kind"), default="", max_length=96),
        "comment_text_present": comment_text_present,
        "backend_comment_text_present": comment_text_present,
        "comment_text_length": len(comment_text),
        "comment_text_fingerprint": _fingerprint(comment_text),
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "source_display_body_retained": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "exact_comment_text_required": False,
        "exact_comment_text_locked": False,
        "case_specific_runtime_branch": False,
        "case_specific_runtime_branch_allowed": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "material_quality": _safe_identifier(item.get("material_quality"), default="", max_length=96),
        "candidate_source_kind": _safe_identifier(item.get("candidate_source_kind"), default="", max_length=96),
        "composer_model": _safe_identifier(item.get("composer_model"), default="", max_length=96),
        "visible_surface_acceptance": {
            "classification": _safe_identifier(item.get("visible_surface_acceptance_classification"), default="", max_length=80),
            "action": _safe_identifier(item.get("visible_surface_acceptance_action"), default="", max_length=80),
            "passed": bool(item.get("visible_surface_acceptance_passed")),
        },
        "visible_surface_acceptance_classification": _safe_identifier(item.get("visible_surface_acceptance_classification"), default="", max_length=80),
        "visible_surface_acceptance_action": _safe_identifier(item.get("visible_surface_acceptance_action"), default="", max_length=80),
        "visible_surface_acceptance_passed": bool(item.get("visible_surface_acceptance_passed")),
        "rejection_reasons": _dedupe(item.get("rejection_reasons")),
        "repair_reasons": _dedupe(item.get("repair_reasons")),
        "fallback_reason_family": _safe_identifier(item.get("fallback_reason_family"), default="", max_length=96),
        "renderer_exception": _safe_identifier(item.get("renderer_exception"), default="", max_length=96),
        "verdict": VERDICT_NOT_EVALUATED,
        "failure_buckets": [],
        "reason_codes": reason_codes,
        "p3_2_output_capture_completed": True,
        "p3_2_sanitized_current_output_event_created": True,
        "scorecard_event_created": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(
        [event],
        source="product_readfeel_p3_sanitized_current_output_event",
    )
    return event


def assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(
    events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None,
    *,
    source: str = "product_readfeel_p3_sanitized_current_output_events_20260609",
) -> None:
    if events is None:
        raise ValueError(f"{source} must not be None")
    payload: Any = events
    if isinstance(events, Mapping):
        payload = [events]
    if not isinstance(payload, Sequence) or isinstance(payload, (str, bytes, bytearray)):
        raise ValueError(f"{source} must be a mapping or sequence of mappings")
    if _contains_forbidden_key(payload, _SANITIZED_FORBIDDEN_TEXT_KEYS_20260609):
        raise ValueError(f"{source} contains raw input or comment_text body key")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} marks forbidden true flag at {flag_path}")
    for event in payload:
        if not isinstance(event, Mapping):
            raise ValueError(f"{source} must contain mappings")
        if event.get("comment_text_body_included") is not False:
            raise ValueError(f"{source} must keep comment_text_body_included false")
        if event.get("raw_input_included") is not False:
            raise ValueError(f"{source} must keep raw_input_included false")
        if event.get("product_gate_ready") is not False:
            raise ValueError(f"{source} must keep product_gate_ready false")
        if event.get("public_release_applied") is not False:
            raise ValueError(f"{source} must keep public_release_applied false")
        assert_product_readfeel_current_output_inventory_meta_only(
            event,
            source=f"{source}.inventory_compat",
        )
        assert_emlis_ai_product_quality_contract_freeze_meta_only(
            event,
            source=f"{source}.contract_freeze",
        )


def assert_product_readfeel_p3_local_review_packet_local_only_20260609(
    packet: Mapping[str, Any] | None,
    *,
    source: str = "product_readfeel_p3_local_review_packet_20260609",
) -> None:
    if not isinstance(packet, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if packet.get("schema_version") != PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609:
        raise ValueError(f"{source} has invalid schema_version")
    if packet.get("visibility") != PRODUCT_READFEEL_P3_LOCAL_REVIEW_VISIBILITY_20260609:
        raise ValueError(f"{source} must stay local_qa_only")
    if packet.get("contains_raw_input") is not True:
        raise ValueError(f"{source} must mark raw input as local-only material")
    if packet.get("contains_comment_text_body") is not True:
        raise ValueError(f"{source} must mark comment_text body as local-only material")
    if packet.get("product_gate_ready") is not False:
        raise ValueError(f"{source} must keep product_gate_ready false")
    if packet.get("public_release_applied") is not False:
        raise ValueError(f"{source} must keep public_release_applied false")
    items = packet.get("items")
    if not isinstance(items, Sequence) or isinstance(items, (str, bytes, bytearray)):
        raise ValueError(f"{source}.items must be a sequence")
    if int(packet.get("item_count") or -1) != len(items):
        raise ValueError(f"{source}.item_count mismatch")
    for item in items:
        if not isinstance(item, Mapping):
            raise ValueError(f"{source}.items must contain mappings")
        if item.get("visibility") != PRODUCT_READFEEL_P3_LOCAL_REVIEW_VISIBILITY_20260609:
            raise ValueError(f"{source}.item visibility must stay local_qa_only")
        if not isinstance(item.get("current_input"), Mapping):
            raise ValueError(f"{source}.item must keep synthetic current_input for local QA")
        if "comment_text" not in item:
            raise ValueError(f"{source}.item must keep comment_text for local QA")
        current_input = _safe_mapping(item.get("current_input"))
        if current_input.get("synthetic_case_material") is not True:
            raise ValueError(f"{source}.item must be synthetic local QA material")
        if item.get("product_gate_ready") is not False:
            raise ValueError(f"{source}.item product_gate_ready must stay false")
        if item.get("public_release_applied") is not False:
            raise ValueError(f"{source}.item public_release_applied must stay false")


def build_product_readfeel_p3_local_output_capture_public_summary_20260609(
    capture: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(capture, Mapping):
        raise ValueError("P3-2 capture must be a mapping")
    events = list(capture.get("sanitized_current_output_events") or [])
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(events)
    family_counts = Counter(str(event.get("family") or "") for event in events)
    coverage_counts: Counter[str] = Counter()
    path_counts: Counter[str] = Counter()
    observation_status_counts: Counter[str] = Counter()
    target_path_pending_counts: Counter[str] = Counter()
    for event in events:
        coverage_counts.update(_dedupe(event.get("coverage_slices")))
        path_counts.update([_safe_identifier(event.get("path"), default=PATH_RENDER_DEFAULT, max_length=80)])
        observation_status_counts.update([_safe_identifier(event.get("observation_status"), default="unavailable", max_length=40)])
        target_path_pending_counts.update(_dedupe(event.get("target_paths_not_captured")))
    missing_families = [
        family
        for family in PRODUCT_READFEEL_BASELINE_REQUIRED_FAMILIES_20260609
        if int(family_counts.get(family, 0)) <= 0
    ]
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609,
        "run_id": _safe_identifier(capture.get("run_id"), default="", max_length=96),
        "run_profile": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_PROFILE_20260609,
        "case_count": len(events),
        "output_row_count": len(events),
        "sanitized_current_output_event_count": len(events),
        "local_review_packet_created": bool(capture.get("local_review_packet")),
        "local_review_packet_visibility": PRODUCT_READFEEL_P3_LOCAL_REVIEW_VISIBILITY_20260609,
        "local_review_packet_contains_synthetic_bodies": True,
        "local_review_packet_retained_in_public_summary": False,
        "required_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "family_counts": dict(family_counts),
        "missing_families": missing_families,
        "coverage_slice_counts": dict(coverage_counts),
        "path_counts": dict(path_counts),
        "observation_status_counts": dict(observation_status_counts),
        "target_path_pending_counts": dict(target_path_pending_counts),
        "all_cases_have_output_rows": len(events) == len(capture.get("local_review_packet", {}).get("items", [])),
        "public_reached_count": sum(1 for event in events if event.get("public_reached") is True),
        "rn_visible_count": sum(1 for event in events if event.get("rn_visible") is True),
        "comment_text_present_count": sum(1 for event in events if event.get("comment_text_present") is True),
        "product_surface_valid_count": sum(1 for event in events if event.get("product_surface_valid") is True),
        "renderer_exception_count": sum(1 for event in events if _clean(event.get("renderer_exception"))),
        "capture_path_scope": "primary_render_default_path_for_p3_2",
        "target_path_pending_capture_allowed_in_p3_2": True,
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": True,
        "p3_2_local_output_capture_completed": True,
        "output_capture_completed": True,
        "sanitized_current_output_event_created": True,
        "scorecard_event_created": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "candidate_body_included": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(
        [summary],
        source="product_readfeel_p3_local_output_capture_public_summary_20260609",
    )
    assert_product_readfeel_baseline_public_safe_meta_only_20260609(
        summary,
        source="product_readfeel_p3_local_output_capture_public_summary_20260609",
    )
    return summary


async def build_product_readfeel_p3_local_output_capture_async_20260609(
    *,
    input_cases: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    renderer: Callable[..., Any] | None = None,
    run_id: str | None = None,
    created_at: str | None = None,
    user_id: str = PRODUCT_READFEEL_P3_DEFAULT_USER_ID_20260609,
    display_name: str | None = None,
    timezone_name: str | None = PRODUCT_READFEEL_P3_DEFAULT_TIMEZONE_20260609,
    composer_client: Any = None,
) -> dict[str, Any]:
    cases = list(input_cases) if input_cases is not None else build_product_readfeel_baseline_cases_20260609()
    assert_product_readfeel_baseline_case_matrix_contract_20260609(cases)
    run_id_value = _safe_identifier(run_id, default="", max_length=96) or _default_run_id()
    created_at_value = _clean(created_at) or _now_iso()
    active_renderer = renderer or _default_renderer()

    local_items: list[dict[str, Any]] = []
    sanitized_events: list[dict[str, Any]] = []
    warnings: list[str] = []

    for index, raw_case in enumerate(cases, start=1):
        case = dict(raw_case or {})
        case_id = _safe_identifier(case.get("case_id"), default=f"case_{index:03d}", max_length=96)
        row_id = f"p3_2_{index:03d}_{case_id}"
        path = _primary_capture_path(case)
        target_paths = _dedupe(case.get("path_targets"))
        target_paths_not_captured = [target for target in target_paths if target != path]
        current_input = deepcopy(case.get("current_input") or {})
        subscription_tier = _safe_identifier(case.get("subscription_tier"), default="free", max_length=32)
        renderer_exception = ""
        try:
            reply = await _call_renderer(
                active_renderer,
                user_id=user_id,
                subscription_tier=subscription_tier,
                current_input=current_input,
                display_name=case.get("display_name", display_name),
                timezone_name=case.get("timezone_name", timezone_name),
                composer_client=case.get("composer_client", composer_client),
            )
            comment_text = _extract_reply_comment_text(reply)
            internal_meta = _extract_reply_meta(reply)
        except Exception as exc:  # noqa: BLE001 - local QA must keep one output row per case.
            renderer_exception = type(exc).__name__
            warnings.append(f"renderer_exception:{renderer_exception}")
            comment_text = ""
            internal_meta = {
                "observation_status": "unavailable",
                "observation_reply_kind": "renderer_exception",
                "rejection_reasons": ["renderer_exception", f"renderer_exception_{renderer_exception}"],
            }
        public_meta = build_public_emlis_input_feedback_meta(
            internal_meta,
            comment_text_present=bool(comment_text.strip()),
            subscription_tier=subscription_tier,
        )
        local_item = _local_review_item(
            run_id=run_id_value,
            row_id=row_id,
            case=case,
            path=path,
            target_paths_not_captured=target_paths_not_captured,
            comment_text=comment_text,
            public_meta=public_meta,
            internal_meta=internal_meta,
            renderer_exception=renderer_exception,
        )
        local_items.append(local_item)
        sanitized_events.append(_sanitized_event_from_local_item(local_item))

    local_review_packet = {
        "schema_version": PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609,
        "visibility": PRODUCT_READFEEL_P3_LOCAL_REVIEW_VISIBILITY_20260609,
        "commit_policy": PRODUCT_READFEEL_P3_LOCAL_REVIEW_COMMIT_POLICY_20260609,
        "run_id": run_id_value,
        "created_at": created_at_value,
        "item_count": len(local_items),
        "contains_raw_input": True,
        "contains_comment_text_body": True,
        "contains_synthetic_case_material_only": True,
        "public_meta_body_allowed": False,
        "items": local_items,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_p3_local_review_packet_local_only_20260609(local_review_packet)
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(sanitized_events)
    capture = {
        "schema_version": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_RUN_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_RUN_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_PROFILE_20260609,
        "created_at": created_at_value,
        "local_review_packet": local_review_packet,
        "sanitized_current_output_events": sanitized_events,
        "warnings": _dedupe(warnings),
        "output_capture_completed": True,
        "sanitized_current_output_event_created": True,
        "scorecard_event_created": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    capture["public_summary"] = build_product_readfeel_p3_local_output_capture_public_summary_20260609(capture)
    return capture


def build_product_readfeel_p3_local_output_capture_20260609(**kwargs: Any) -> dict[str, Any]:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(build_product_readfeel_p3_local_output_capture_async_20260609(**kwargs))
    raise RuntimeError(
        "build_product_readfeel_p3_local_output_capture_async_20260609 must be awaited inside an active event loop"
    )


def dump_product_readfeel_p3_local_output_capture_public_summary_20260609(
    summary_or_capture: Mapping[str, Any] | None = None,
) -> str:
    if summary_or_capture is None:
        summary = build_product_readfeel_p3_local_output_capture_public_summary_20260609(
            build_product_readfeel_p3_local_output_capture_20260609()
        )
    elif summary_or_capture.get("schema_version") == PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609:
        summary = dict(summary_or_capture)
    else:
        summary = build_product_readfeel_p3_local_output_capture_public_summary_20260609(summary_or_capture)
    assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609(
        [summary],
        source="product_readfeel_p3_local_output_capture_public_summary_dump_20260609",
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_RUN_VERSION_20260609",
    "PRODUCT_READFEEL_P3_LOCAL_REVIEW_PACKET_VERSION_20260609",
    "PRODUCT_READFEEL_P3_SANITIZED_CURRENT_OUTPUT_EVENT_VERSION_20260609",
    "PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_LOCAL_OUTPUT_CAPTURE_STEP_20260609",
    "assert_product_readfeel_p3_local_review_packet_local_only_20260609",
    "assert_product_readfeel_p3_sanitized_current_output_events_meta_only_20260609",
    "build_product_readfeel_p3_local_output_capture_20260609",
    "build_product_readfeel_p3_local_output_capture_async_20260609",
    "build_product_readfeel_p3_local_output_capture_public_summary_20260609",
    "dump_product_readfeel_p3_local_output_capture_public_summary_20260609",
]
