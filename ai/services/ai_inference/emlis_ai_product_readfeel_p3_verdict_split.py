# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-4 P2/P3 verdict split for EmlisAI Product Read Feel baseline.

P3-4 receives the body-free P3-2/P3-3 current-output material and assigns
explicit verdicts without retaining raw input or ``comment_text`` bodies.  The
purpose is to keep P2/contract/surface blockers separate from P3 read-feel
repairs so Product Read Feel work does not hide safety or public-contract
breakage behind a weak-but-visible response.

This module is measurement-only.  It does not change RN, API routes, DB schema,
public response keys, gates, renderer selection, or ``comment_text`` generation.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    FAILURE_CONTRACT_VIOLATION,
    FAILURE_DISPLAY_NOT_REACHED,
    FAILURE_READFEEL_GAP,
    FAILURE_STRUCTURE_INSIGHT_GAP,
    FAILURE_SURFACE_BREAKAGE,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
    VERDICT_NOT_EVALUATED,
    VERDICT_PASS,
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_YELLOW,
    assert_product_readfeel_current_output_inventory_meta_only,
    build_product_readfeel_current_output_inventory,
    normalize_product_readfeel_current_output_item,
)

PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.verdict_split.20260609.v1"
)
PRODUCT_READFEEL_P3_VERDICT_SPLIT_ROW_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.verdict_split_row.20260609.v1"
)
PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.verdict_split_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609: Final = (
    "P3-4_P2_P3_Verdict_Split"
)
PRODUCT_READFEEL_P3_VERDICT_SPLIT_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_P2P3VerdictSplit_20260609"
)
PRODUCT_READFEEL_P3_VERDICT_SPLIT_PROFILE_20260609: Final = (
    "local_product_readfeel_p3_verdict_split"
)

VERDICT_LAYER_P2_RED: Final = "P2_RED"
VERDICT_LAYER_P1_DISPLAY_REPAIR: Final = "P1_DISPLAY_REPAIR"
VERDICT_LAYER_P3_REPAIR_REQUIRED: Final = "P3_REPAIR_REQUIRED"
VERDICT_LAYER_P3_YELLOW: Final = "P3_YELLOW"
VERDICT_LAYER_P3_PASS: Final = "P3_PASS"
VERDICT_LAYER_NOT_EVALUATED: Final = "NOT_EVALUATED"

_ALLOWED_VERDICTS: Final[frozenset[str]] = frozenset(
    {VERDICT_RED, VERDICT_REPAIR_REQUIRED, VERDICT_YELLOW, VERDICT_PASS, VERDICT_NOT_EVALUATED}
)
_ALLOWED_VERDICT_LAYERS: Final[frozenset[str]] = frozenset(
    {
        VERDICT_LAYER_P2_RED,
        VERDICT_LAYER_P1_DISPLAY_REPAIR,
        VERDICT_LAYER_P3_REPAIR_REQUIRED,
        VERDICT_LAYER_P3_YELLOW,
        VERDICT_LAYER_P3_PASS,
        VERDICT_LAYER_NOT_EVALUATED,
    }
)

_FORBIDDEN_TEXT_KEYS: Final[frozenset[str]] = frozenset(
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
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "external_ai_used",
        "local_llm_used",
    }
)

_EXCLUDED_STATUS_VALUES: Final[frozenset[str]] = frozenset(
    {
        "safety_blocked",
        "safety_emergency",
        "infrastructure_error",
        "infra_error",
        "system_error",
    }
)
_EXCLUDED_REASON_MARKERS: Final[tuple[str, ...]] = (
    "safety",
    "self_harm",
    "policy_blocked",
    "infra",
    "infrastructure",
    "timeout",
    "server_error",
    "network_error",
    "system_error",
    "renderer_exception",
    "source_unavailable_true",
    "true_unavailable",
)
_P2_RED_REASON_MARKERS: Final[tuple[str, ...]] = (
    "contract",
    "public_response_key",
    "response_key",
    "api_route",
    "db_physical",
    "rn_visible",
    "rn_title",
    "gate_relaxed",
    "raw_text_public_leak",
    "raw_input_public_leak",
    "comment_text_public_leak",
    "candidate_body_public_leak",
    "sanitized_current_output_event_text_key_violation",
    "sanitized_current_output_event_forbidden_true_flag",
    "diagnosis",
    "diagnostic",
    "personality",
    "target_judgement_agreement",
    "other_person_intent_claim",
    "relationship_target_judgement_risk",
    "self_denial_identity_claim_risk",
    "cause_claim_without_evidence",
    "malformed",
    "bad_grammar",
    "koto_splice",
    "nominalization",
    "internal_role",
    "fixed_fallback",
    "fixed_template",
    "surface_breakage",
)
_P3_REPAIR_REASON_MARKERS: Final[tuple[str, ...]] = (
    "rich_input_low_information_overroute",
    "input_core_missing",
    "event_reaction_missing",
    "desire_fear_conflict_missing",
    "state_structure_missing",
    "mirror_only_or_self_report_only",
    "mirror_only",
    "self_report_only",
    "input_self_report_only",
    "history_line_masks_current_input_gap",
    "limited_grounding_collapsed_to_question",
    "structure_question_answered_as_comfort",
    "long_input_crushed",
    "too_short_for_long_input",
)
_P3_YELLOW_REASON_MARKERS: Final[tuple[str, ...]] = (
    "family_temperature_flattened",
    "generic_reception_surface",
    "repeated_surface_signature",
    "positive_overweighted",
    "positive_underreceived",
    "generic_comfort",
    "generic_follow",
    "follow_shallow",
    "weak_follow",
    "input_specificity_weak",
    "natural_but_generic",
    "readfeel_gap",
    "read_feeling",
)

_BLOCKER_TARGET_LAYERS: Final[dict[str, tuple[str, ...]]] = {
    "contract_violation": ("public_boundary_contract", "p0_p1_contract_freeze"),
    "surface_breakage": ("visible_surface_acceptance_gate", "surface_realizer", "p2_surface_safety"),
    "product_surface_invalid": ("product_surface_validation", "visible_surface_acceptance_gate"),
    "public_display_not_reached": ("emotion_submit_public_feedback_boundary", "display_contract"),
    "comment_text_missing": ("emotion_submit_public_feedback_boundary", "renderer_output_capture"),
    "rich_input_low_information_overroute": (
        "input_material_bundle",
        "public_surface_requirement",
        "gate_recovery_route",
    ),
    "input_core_missing": ("input_material_bundle", "surface_plan", "surface_realizer"),
    "event_reaction_missing": ("input_material_bundle", "surface_plan", "surface_realizer"),
    "desire_fear_conflict_missing": ("surface_plan", "reception_mode_resolver"),
    "state_structure_missing": ("state_answer_ratio_policy", "two_stage_section_surface_plan"),
    "limited_grounding_collapsed_to_question": (
        "limited_grounding_reception_surface",
        "low_information_observation_composer",
        "question_dominance_guard",
    ),
    "generic_reception_surface": (
        "phrase_unit_selection",
        "surface_realizer",
        "template_echo_guard",
    ),
    "repeated_surface_signature": (
        "surface_signature_detector",
        "phrase_variation",
        "closing_policy",
    ),
    "family_temperature_flattened": (
        "reception_mode_resolver",
        "state_answer_ratio_policy",
        "two_stage_section_surface_plan",
    ),
    "structure_insight_gap": (
        "mirror_only_surface_detector",
        "structure_insight_candidate_backlog",
    ),
    "history_line_masks_current_input_gap": (
        "user_label_connection_surface",
        "current_input_anchor_requirement",
    ),
    "p3_inventory_repair_required": ("product_readfeel_current_output_inventory",),
    "p3_readfeel_gap": ("surface_plan", "surface_realizer", "blind_qa_review"),
    "p3_yellow_readfeel_weakness": ("family_tuning_backlog", "blind_qa_review"),
    "not_evaluated_safety_or_infra": ("excluded_from_normal_observation_ledger",),
}
_BLOCKER_PRIORITY: Final[tuple[str, ...]] = (
    "contract_violation",
    "surface_breakage",
    "product_surface_invalid",
    "public_display_not_reached",
    "comment_text_missing",
    "rich_input_low_information_overroute",
    "input_core_missing",
    "event_reaction_missing",
    "desire_fear_conflict_missing",
    "state_structure_missing",
    "limited_grounding_collapsed_to_question",
    "history_line_masks_current_input_gap",
    "generic_reception_surface",
    "repeated_surface_signature",
    "family_temperature_flattened",
    "structure_insight_gap",
    "p3_inventory_repair_required",
    "p3_readfeel_gap",
    "p3_yellow_readfeel_weakness",
)


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
            if str(key) in _FORBIDDEN_TEXT_KEYS:
                return True
            if _contains_forbidden_key(child):
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


def _source_body_key_path(value: Any, *, path: str = "source") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_TEXT_KEYS:
                return child_path
            nested = _source_body_key_path(child, path=child_path)
            if nested:
                return nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            nested = _source_body_key_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y", "on", "passed", "pass", "valid", "allow"}:
        return True
    if text in {"false", "0", "no", "n", "off", "failed", "fail", "invalid", "block", "blocked"}:
        return False
    return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _has_marker(values: Iterable[str], markers: Sequence[str]) -> bool:
    normalized = [value.lower() for value in values]
    return any(marker in value for marker in markers for value in normalized)


def _reason_values(event: Mapping[str, Any], item: Mapping[str, Any]) -> list[str]:
    values: list[Any] = []
    for source in (event, item):
        for key in (
            "reason_codes",
            "rejection_reasons",
            "repair_reasons",
            "failure_reasons",
            "red_flags",
            "warnings",
            "failure_buckets",
            "top_reasons",
            "inventory_reasons",
            "mirror_only_reason_codes",
        ):
            values.extend(_dedupe(source.get(key)))
        for key in ("primary_reason", "reason_code", "unavailable_reason", "renderer_exception"):
            text = _clean(source.get(key))
            if text:
                values.append(text)
    return _dedupe(values)


def _failure_buckets(event: Mapping[str, Any], item: Mapping[str, Any]) -> list[str]:
    return _dedupe([*_dedupe(event.get("failure_buckets")), *_dedupe(item.get("failure_buckets"))])


def _is_excluded_from_normal_observation(event: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    status = _clean(event.get("observation_status") or event.get("backend_observation_status") or event.get("status")).lower()
    if status in _EXCLUDED_STATUS_VALUES:
        return True
    if _clean(event.get("renderer_exception")):
        return True
    if "renderer_exception" in {reason.lower() for reason in reasons}:
        return True
    if status in {"unavailable", "rejected", ""} and _has_marker(reasons, _EXCLUDED_REASON_MARKERS):
        return True
    return False


def _public_reached(event: Mapping[str, Any], item: Mapping[str, Any]) -> bool:
    status = _clean(event.get("observation_status") or item.get("observation_status")).lower()
    return bool(
        event.get("public_reached") is True
        or event.get("public_passed") is True
        or event.get("backend_public_passed") is True
        or event.get("display_confirmed") is True
        or item.get("display_returned") is True
        or (status == "passed" and event.get("comment_text_present") is True)
    )


def _comment_text_present(event: Mapping[str, Any], item: Mapping[str, Any]) -> bool:
    return bool(
        event.get("comment_text_present") is True
        or event.get("backend_comment_text_present") is True
        or item.get("comment_text_present") is True
    )


def _product_surface_valid(event: Mapping[str, Any]) -> bool:
    if "product_surface_valid" not in event:
        return True
    return event.get("product_surface_valid") is True


def _visible_surface_blocked(event: Mapping[str, Any]) -> bool:
    action = _clean(event.get("visible_surface_acceptance_action")).lower()
    classification = _clean(event.get("visible_surface_acceptance_classification")).lower()
    if _to_bool(event.get("visible_surface_acceptance_passed"), default=True) is False:
        return True
    return any(marker in action for marker in ("block", "reject")) or any(
        marker in classification for marker in ("block", "reject", "invalid")
    )


def _blocker_from_known_reason(reason: str) -> str:
    lower = reason.lower()
    known = [
        "rich_input_low_information_overroute",
        "input_core_missing",
        "event_reaction_missing",
        "desire_fear_conflict_missing",
        "state_structure_missing",
        "limited_grounding_collapsed_to_question",
        "history_line_masks_current_input_gap",
        "generic_reception_surface",
        "repeated_surface_signature",
        "family_temperature_flattened",
        "structure_question_answered_as_comfort",
    ]
    for candidate in known:
        if candidate in lower:
            return candidate
    if "mirror_only" in lower or "self_report_only" in lower or "structure_insight" in lower:
        return "structure_insight_gap"
    if "readfeel" in lower or "read_feeling" in lower:
        return "p3_readfeel_gap"
    if any(marker in lower for marker in _P2_RED_REASON_MARKERS):
        if "contract" in lower or "key" in lower or "route" in lower or "gate_relaxed" in lower:
            return "contract_violation"
        return "surface_breakage"
    return ""


def _priority_index(blocker_id: str) -> int:
    try:
        return _BLOCKER_PRIORITY.index(blocker_id)
    except ValueError:
        return len(_BLOCKER_PRIORITY) + 1


def _target_layers(blocker_ids: Sequence[str]) -> list[str]:
    layers: list[str] = []
    for blocker_id in blocker_ids:
        layers.extend(_BLOCKER_TARGET_LAYERS.get(blocker_id, ("manual_review",)))
    return _dedupe(layers)


def _lookup_key(record: Mapping[str, Any]) -> str:
    for key in ("case_id", "fixture_id", "row_id", "item_id", "candidate_id", "review_id"):
        value = _safe_identifier(record.get(key), max_length=96, default="")
        if value:
            return value
    return ""


def _inventory_items_by_key(inventory: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    mapping: dict[str, Mapping[str, Any]] = {}
    for item in list(inventory.get("items") or []):
        if not isinstance(item, Mapping):
            continue
        for key in ("case_id", "fixture_id", "row_id", "item_id", "candidate_id", "review_id"):
            value = _safe_identifier(item.get(key), max_length=96, default="")
            if value and value not in mapping:
                mapping[value] = item
    return mapping


def _extract_events(source: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> list[Mapping[str, Any]]:
    if source is None:
        return []
    if isinstance(source, Mapping):
        if "sanitized_current_output_events" in source:
            events = source.get("sanitized_current_output_events") or []
        elif "events" in source:
            events = source.get("events") or []
        elif "verdict_rows" in source:
            events = source.get("verdict_rows") or []
        else:
            events = [source]
    else:
        events = list(source)
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)):
        raise ValueError("P3-4 verdict split source events must be a sequence")
    out: list[Mapping[str, Any]] = []
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise ValueError(f"P3-4 verdict split source event[{index}] must be a mapping")
        body_path = _source_body_key_path(event, path=f"source_events[{index}]")
        if body_path:
            raise ValueError(f"P3-4 verdict split source event contains forbidden body key at {body_path}")
        out.append(event)
    return out


def _classify_event(
    event: Mapping[str, Any],
    *,
    inventory_item: Mapping[str, Any] | None = None,
    run_id: str,
    index: int,
) -> dict[str, Any]:
    item = dict(inventory_item or normalize_product_readfeel_current_output_item(event))
    reasons = _reason_values(event, item)
    buckets = _failure_buckets(event, item)
    source_inventory_verdict = _clean(item.get("verdict")) or VERDICT_NOT_EVALUATED
    public_reached = _public_reached(event, item)
    comment_text_present = _comment_text_present(event, item)
    product_surface_valid = _product_surface_valid(event)
    visible_surface_blocked = _visible_surface_blocked(event)
    excluded = _is_excluded_from_normal_observation(event, reasons)

    blocker_ids: list[str] = []
    red_reasons: list[str] = []
    repair_reasons: list[str] = []
    yellow_reasons: list[str] = []
    not_evaluated_reasons: list[str] = []

    if excluded:
        verdict = VERDICT_NOT_EVALUATED
        verdict_layer = VERDICT_LAYER_NOT_EVALUATED
        blocker_ids.append("not_evaluated_safety_or_infra")
        not_evaluated_reasons.extend(reasons or ["safety_or_infra_or_true_unavailable"])
    else:
        if FAILURE_CONTRACT_VIOLATION in buckets:
            blocker_ids.append("contract_violation")
            red_reasons.append(FAILURE_CONTRACT_VIOLATION)
        if FAILURE_SURFACE_BREAKAGE in buckets:
            blocker_ids.append("surface_breakage")
            red_reasons.append(FAILURE_SURFACE_BREAKAGE)
        if not product_surface_valid or visible_surface_blocked:
            blocker_ids.append("product_surface_invalid")
            red_reasons.append("product_surface_invalid")
        if _has_marker(reasons, _P2_RED_REASON_MARKERS):
            for reason in reasons:
                blocker = _blocker_from_known_reason(reason)
                if blocker in {"contract_violation", "surface_breakage"}:
                    blocker_ids.append(blocker)
                    red_reasons.append(reason)
        if source_inventory_verdict == VERDICT_RED:
            blocker_ids.append("surface_breakage" if FAILURE_SURFACE_BREAKAGE in buckets else "contract_violation")
            red_reasons.append("inventory_red_verdict")

        if red_reasons:
            verdict = VERDICT_RED
            verdict_layer = VERDICT_LAYER_P2_RED
        else:
            if FAILURE_DISPLAY_NOT_REACHED in buckets or not public_reached or not comment_text_present:
                if not public_reached:
                    blocker_ids.append("public_display_not_reached")
                    repair_reasons.append("public_display_not_reached")
                if not comment_text_present:
                    blocker_ids.append("comment_text_missing")
                    repair_reasons.append("comment_text_missing")
                verdict = VERDICT_REPAIR_REQUIRED
                verdict_layer = VERDICT_LAYER_P1_DISPLAY_REPAIR
            elif source_inventory_verdict == VERDICT_REPAIR_REQUIRED or _has_marker(reasons, _P3_REPAIR_REASON_MARKERS):
                for reason in reasons:
                    blocker = _blocker_from_known_reason(reason)
                    if blocker:
                        blocker_ids.append(blocker)
                        repair_reasons.append(reason)
                if FAILURE_STRUCTURE_INSIGHT_GAP in buckets:
                    blocker_ids.append("structure_insight_gap")
                    repair_reasons.append(FAILURE_STRUCTURE_INSIGHT_GAP)
                if FAILURE_READFEEL_GAP in buckets:
                    blocker_ids.append("p3_readfeel_gap")
                    repair_reasons.append(FAILURE_READFEEL_GAP)
                if not repair_reasons:
                    blocker_ids.append("p3_inventory_repair_required")
                    repair_reasons.append("inventory_repair_required")
                verdict = VERDICT_REPAIR_REQUIRED
                verdict_layer = VERDICT_LAYER_P3_REPAIR_REQUIRED
            elif source_inventory_verdict == VERDICT_YELLOW or FAILURE_READFEEL_GAP in buckets or FAILURE_STRUCTURE_INSIGHT_GAP in buckets or _has_marker(reasons, _P3_YELLOW_REASON_MARKERS):
                for reason in reasons:
                    blocker = _blocker_from_known_reason(reason)
                    if blocker:
                        blocker_ids.append(blocker)
                        yellow_reasons.append(reason)
                if FAILURE_READFEEL_GAP in buckets:
                    blocker_ids.append("p3_readfeel_gap")
                    yellow_reasons.append(FAILURE_READFEEL_GAP)
                if FAILURE_STRUCTURE_INSIGHT_GAP in buckets:
                    blocker_ids.append("structure_insight_gap")
                    yellow_reasons.append(FAILURE_STRUCTURE_INSIGHT_GAP)
                if not yellow_reasons:
                    blocker_ids.append("p3_yellow_readfeel_weakness")
                    yellow_reasons.append("inventory_yellow_verdict")
                verdict = VERDICT_YELLOW
                verdict_layer = VERDICT_LAYER_P3_YELLOW
            else:
                verdict = VERDICT_PASS
                verdict_layer = VERDICT_LAYER_P3_PASS

    blocker_ids = sorted(_dedupe(blocker_ids), key=_priority_index)
    target_layers = _target_layers(blocker_ids)
    family = _safe_identifier(
        event.get("family")
        or event.get("product_readfeel_family")
        or item.get("family")
        or item.get("product_readfeel_family"),
        default="unclassified",
        max_length=96,
    )
    row = {
        "schema_version": PRODUCT_READFEEL_P3_VERDICT_SPLIT_ROW_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_VERDICT_SPLIT_ROW_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_VERDICT_SPLIT_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609,
        "run_id": _safe_identifier(run_id, default="p3_4_verdict_split", max_length=96),
        "row_id": _safe_identifier(event.get("row_id"), default=f"p3_4_row_{index:03d}", max_length=96),
        "case_id": _safe_identifier(event.get("case_id") or item.get("case_id"), default="", max_length=96),
        "fixture_id": _safe_identifier(event.get("fixture_id") or item.get("fixture_id") or event.get("case_id"), default="", max_length=96),
        "family": family,
        "product_readfeel_family": family,
        "coverage_slices": _dedupe(event.get("coverage_slices")),
        "path": _safe_identifier(event.get("path"), default="render_default_path", max_length=96),
        "subscription_tier": _safe_identifier(event.get("subscription_tier"), default="", max_length=32),
        "observation_status": _safe_identifier(event.get("observation_status"), default="", max_length=40),
        "public_reached": public_reached,
        "rn_visible": _to_bool(event.get("rn_visible"), default=False),
        "rn_visible_expected": _to_bool(event.get("rn_visible_expected"), default=True),
        "product_surface_valid": product_surface_valid,
        "comment_text_present": comment_text_present,
        "source_inventory_verdict": source_inventory_verdict,
        "verdict": verdict,
        "verdict_layer": verdict_layer,
        "p2_red": verdict_layer == VERDICT_LAYER_P2_RED,
        "p1_display_repair": verdict_layer == VERDICT_LAYER_P1_DISPLAY_REPAIR,
        "p3_repair_required": verdict_layer == VERDICT_LAYER_P3_REPAIR_REQUIRED,
        "p3_yellow": verdict_layer == VERDICT_LAYER_P3_YELLOW,
        "p3_pass": verdict_layer == VERDICT_LAYER_P3_PASS,
        "not_evaluated": verdict_layer == VERDICT_LAYER_NOT_EVALUATED,
        "excluded_from_p3_readfeel_repair": verdict_layer in {VERDICT_LAYER_P2_RED, VERDICT_LAYER_NOT_EVALUATED},
        "excluded_reason_kind": "safety_or_infra_or_true_unavailable" if verdict_layer == VERDICT_LAYER_NOT_EVALUATED else "",
        "failure_buckets": buckets,
        "reason_codes": reasons,
        "blocker_ids": blocker_ids,
        "target_layers": target_layers,
        "red_reasons": _dedupe(red_reasons),
        "repair_reasons": _dedupe(repair_reasons),
        "yellow_reasons": _dedupe(yellow_reasons),
        "not_evaluated_reasons": _dedupe(not_evaluated_reasons),
        "verdict_priority": 1 if verdict == VERDICT_RED else 2 if verdict == VERDICT_REPAIR_REQUIRED else 3 if verdict == VERDICT_YELLOW else 4 if verdict == VERDICT_PASS else 9,
        "p3_4_verdict_split_applied": True,
        "blind_qa_ratings_applied": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
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
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    if row["verdict"] not in _ALLOWED_VERDICTS:
        raise ValueError("P3-4 verdict row has unsupported verdict")
    if row["verdict_layer"] not in _ALLOWED_VERDICT_LAYERS:
        raise ValueError("P3-4 verdict row has unsupported verdict layer")
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(row, source="product_readfeel_p3_verdict_split_row")
    return row


def _repair_target_rows(rows: Sequence[Mapping[str, Any]], *, p2_red_present: bool) -> list[Mapping[str, Any]]:
    if p2_red_present:
        return [row for row in rows if row.get("verdict_layer") == VERDICT_LAYER_P2_RED]
    p3_repair = [row for row in rows if row.get("verdict_layer") == VERDICT_LAYER_P3_REPAIR_REQUIRED]
    if p3_repair:
        return p3_repair
    return [row for row in rows if row.get("verdict_layer") == VERDICT_LAYER_P3_YELLOW]


def _first_repair_targets(rows: Sequence[Mapping[str, Any]], *, p2_red_present: bool) -> list[dict[str, Any]]:
    target_rows = _repair_target_rows(rows, p2_red_present=p2_red_present)
    by_blocker: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in target_rows:
        for blocker_id in _dedupe(row.get("blocker_ids")) or ["manual_review"]:
            by_blocker[blocker_id].append(row)
    ordered = sorted(
        by_blocker.items(),
        key=lambda item: (_priority_index(item[0]), -len(item[1]), item[0]),
    )
    targets: list[dict[str, Any]] = []
    for priority, (blocker_id, blocker_rows) in enumerate(ordered[:2], start=1):
        family_counter = Counter(_safe_identifier(row.get("family"), default="unclassified", max_length=96) for row in blocker_rows)
        case_ids = [_safe_identifier(row.get("case_id"), default="", max_length=96) for row in blocker_rows]
        target = {
            "priority": priority,
            "blocker_id": blocker_id,
            "verdict_level": VERDICT_RED if p2_red_present else _clean(blocker_rows[0].get("verdict")),
            "verdict_layer": _clean(blocker_rows[0].get("verdict_layer")),
            "case_count": len(blocker_rows),
            "families": [family for family, _count in family_counter.most_common()],
            "sample_case_ids": [case_id for case_id in case_ids if case_id][:5],
            "target_layers": _target_layers([blocker_id]),
            "forbidden_fix_paths": [
                "gate_relaxation",
                "fixed_comment_text_template",
                "case_specific_runtime_branch",
                "public_response_key_change",
            ],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        assert_product_readfeel_p3_verdict_split_meta_only_20260609(target, source="product_readfeel_p3_first_repair_target")
        targets.append(target)
    return targets


def _summary_from_rows(
    *,
    rows: Sequence[Mapping[str, Any]],
    inventory: Mapping[str, Any],
    run_id: str,
) -> dict[str, Any]:
    verdict_counts = Counter(_clean(row.get("verdict")) for row in rows)
    layer_counts = Counter(_clean(row.get("verdict_layer")) for row in rows)
    family_counts = Counter(_safe_identifier(row.get("family"), default="unclassified", max_length=96) for row in rows)
    blocker_counter: Counter[str] = Counter()
    p3_blocker_counter: Counter[str] = Counter()
    p2_blocker_counter: Counter[str] = Counter()
    coverage_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()
    family_verdicts: dict[str, str] = {}
    family_layer_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        family = _safe_identifier(row.get("family"), default="unclassified", max_length=96)
        family_layer_counts[family].update([_clean(row.get("verdict"))])
        for blocker_id in _dedupe(row.get("blocker_ids")):
            blocker_counter.update([blocker_id])
            if row.get("verdict_layer") == VERDICT_LAYER_P2_RED:
                p2_blocker_counter.update([blocker_id])
            elif row.get("verdict_layer") in {VERDICT_LAYER_P3_REPAIR_REQUIRED, VERDICT_LAYER_P3_YELLOW}:
                p3_blocker_counter.update([blocker_id])
        coverage_counter.update(_dedupe(row.get("coverage_slices")))
        reason_counter.update(_dedupe(row.get("reason_codes")))
    verdict_rank = {VERDICT_PASS: 0, VERDICT_NOT_EVALUATED: 1, VERDICT_YELLOW: 2, VERDICT_REPAIR_REQUIRED: 3, VERDICT_RED: 4}
    for family, counter in family_layer_counts.items():
        family_verdicts[family] = max(counter, key=lambda verdict: verdict_rank.get(verdict, 0))

    required = list(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    observed_required = [family for family in required if family_counts.get(family, 0) > 0]
    missing_required = [family for family in required if family not in observed_required]
    p2_red_count = int(layer_counts.get(VERDICT_LAYER_P2_RED, 0))
    p3_repair_count = int(layer_counts.get(VERDICT_LAYER_P3_REPAIR_REQUIRED, 0))
    p3_yellow_count = int(layer_counts.get(VERDICT_LAYER_P3_YELLOW, 0))
    p1_display_repair_count = int(layer_counts.get(VERDICT_LAYER_P1_DISPLAY_REPAIR, 0))
    not_evaluated_count = int(layer_counts.get(VERDICT_LAYER_NOT_EVALUATED, 0))
    pass_count = int(verdict_counts.get(VERDICT_PASS, 0))
    all_rows_have_verdict = len(rows) > 0 and sum(verdict_counts.values()) == len(rows)
    first_repair_targets = _first_repair_targets(rows, p2_red_present=p2_red_count > 0)
    decision = (
        "return_to_p2_surface_safety"
        if p2_red_count > 0
        else "continue_p3_repair"
        if p3_repair_count > 0 or p3_yellow_count > 0 or p1_display_repair_count > 0
        else "advance_to_p4_family_tuning_candidate"
    )
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_VERDICT_SPLIT_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609,
        "run_id": _safe_identifier(run_id, default="p3_4_verdict_split", max_length=96),
        "run_profile": PRODUCT_READFEEL_P3_VERDICT_SPLIT_PROFILE_20260609,
        "required_families": required,
        "observed_required_families": observed_required,
        "missing_required_families": missing_required,
        "all_required_families_have_verdict": missing_required == [],
        "source_inventory_item_count": _to_int(inventory.get("item_count"), 0),
        "sanitized_event_count": len(rows),
        "verdict_row_count": len(rows),
        "all_rows_have_verdict": all_rows_have_verdict,
        "verdict_counts": dict(verdict_counts),
        "verdict_layer_counts": dict(layer_counts),
        "family_counts": dict(family_counts),
        "family_verdicts": family_verdicts,
        "p2_red_count": p2_red_count,
        "p1_display_repair_required_count": p1_display_repair_count,
        "repair_required_count": int(verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0)),
        "p3_repair_required_count": p3_repair_count,
        "p3_yellow_count": p3_yellow_count,
        "pass_count": pass_count,
        "not_evaluated_count": not_evaluated_count,
        "p2_red_present": p2_red_count > 0,
        "red_and_repair_required_separated": True,
        "p3_repair_should_not_start_until_p2_red_cleared": p2_red_count > 0,
        "can_continue_p3_repair": p2_red_count == 0,
        "decision": decision,
        "blocker_counts": dict(blocker_counter),
        "p2_red_blocker_counts": dict(p2_blocker_counter),
        "p3_repair_blocker_counts": dict(p3_blocker_counter),
        "coverage_slice_counts": dict(coverage_counter),
        "reason_code_counts": dict(reason_counter),
        "first_repair_targets": first_repair_targets,
        "first_repair_target_count": len(first_repair_targets),
        "first_repair_target_blocker_ids": [target["blocker_id"] for target in first_repair_targets],
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": True,
        "p3_2_sanitized_current_output_event_used": True,
        "p3_3_inventory_connection_used": True,
        "p3_4_verdict_split_applied": True,
        "blind_qa_ratings_applied": False,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
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
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(summary, source="product_readfeel_p3_verdict_split_summary")
    return summary


def assert_product_readfeel_p3_verdict_split_meta_only_20260609(
    payload: Mapping[str, Any] | Sequence[Any] | None,
    *,
    source: str = "product_readfeel_p3_verdict_split",
) -> None:
    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} contains raw input or comment_text body key")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} marks forbidden true flag at {flag_path}")
    if isinstance(payload, Mapping):
        if payload.get("comment_text_body_included") is not False and "comment_text_body_included" in payload:
            raise ValueError(f"{source} must keep comment_text_body_included false")
        if payload.get("raw_input_included") is not False and "raw_input_included" in payload:
            raise ValueError(f"{source} must keep raw_input_included false")
        if payload.get("product_gate_ready") is not False and "product_gate_ready" in payload:
            raise ValueError(f"{source} must keep product_gate_ready false")
        if payload.get("public_release_applied") is not False and "public_release_applied" in payload:
            raise ValueError(f"{source} must keep public_release_applied false")
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for index, item in enumerate(payload):
            if isinstance(item, Mapping):
                assert_product_readfeel_p3_verdict_split_meta_only_20260609(item, source=f"{source}[{index}]")


def build_product_readfeel_p3_verdict_split_20260609(
    *,
    sanitized_current_output_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    sanitized_events: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    source: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    current_output_inventory: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    event_source = source if source is not None else (sanitized_current_output_events if sanitized_current_output_events is not None else sanitized_events)
    events = _extract_events(event_source)
    run_id_value = _safe_identifier(run_id, default="", max_length=96)
    if not run_id_value and events:
        run_id_value = _safe_identifier(events[0].get("run_id"), default="", max_length=96)
    if not run_id_value:
        run_id_value = "p3_4_verdict_split"

    inventory = dict(current_output_inventory or {})
    if not inventory and isinstance(event_source, Mapping):
        inventory = dict(event_source.get("current_output_inventory") or {})
    if not inventory:
        inventory = build_product_readfeel_current_output_inventory(events=events, run_id=run_id_value)
    assert_product_readfeel_current_output_inventory_meta_only(inventory)
    item_by_key = _inventory_items_by_key(inventory)
    verdict_rows: list[dict[str, Any]] = []
    for index, event in enumerate(events):
        key = _lookup_key(event)
        inventory_item = item_by_key.get(key)
        verdict_rows.append(
            _classify_event(
                event,
                inventory_item=inventory_item,
                run_id=run_id_value,
                index=index,
            )
        )
    split_inventory = build_product_readfeel_current_output_inventory(events=verdict_rows, run_id=run_id_value)
    summary = _summary_from_rows(rows=verdict_rows, inventory=inventory, run_id=run_id_value)
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_VERDICT_SPLIT_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_VERDICT_SPLIT_PROFILE_20260609,
        "verdict_rows": verdict_rows,
        "verdict_row_count": len(verdict_rows),
        "source_current_output_inventory": inventory,
        "current_output_inventory_after_verdict_split": split_inventory,
        "public_summary": summary,
        "summary": summary,
        "p3_4_verdict_split_applied": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
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
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(payload)
    assert_product_readfeel_current_output_inventory_meta_only(split_inventory)
    return payload


def build_product_readfeel_p3_verdict_split_public_summary_20260609(
    split_or_events: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if isinstance(split_or_events, Mapping) and split_or_events.get("schema_version") == PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609:
        summary = dict(split_or_events.get("public_summary") or split_or_events.get("summary") or {})
    else:
        summary = build_product_readfeel_p3_verdict_split_20260609(source=split_or_events)["public_summary"]
    assert_product_readfeel_p3_verdict_split_meta_only_20260609(summary)
    return summary


def dump_product_readfeel_p3_verdict_split_public_summary_20260609(
    split_or_events: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
) -> str:
    summary = build_product_readfeel_p3_verdict_split_public_summary_20260609(split_or_events)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609",
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_ROW_VERSION_20260609",
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_VERDICT_SPLIT_STEP_20260609",
    "VERDICT_LAYER_P2_RED",
    "VERDICT_LAYER_P1_DISPLAY_REPAIR",
    "VERDICT_LAYER_P3_REPAIR_REQUIRED",
    "VERDICT_LAYER_P3_YELLOW",
    "VERDICT_LAYER_P3_PASS",
    "VERDICT_LAYER_NOT_EVALUATED",
    "assert_product_readfeel_p3_verdict_split_meta_only_20260609",
    "build_product_readfeel_p3_verdict_split_20260609",
    "build_product_readfeel_p3_verdict_split_public_summary_20260609",
    "dump_product_readfeel_p3_verdict_split_public_summary_20260609",
]
