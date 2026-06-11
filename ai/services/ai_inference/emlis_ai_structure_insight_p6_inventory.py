# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-1 body-free inventory of existing Structure Insight assets.

The inventory separates existing Phase7/9/10 implementation assets from the
roadmap P6 work.  It records what can be reused, what must be extended later,
and which safety contracts are already confirmed without exposing text bodies
or changing public API/RN/DB contracts.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_inventory.v1"
)
STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_inventory_summary.v1"
)
STRUCTURE_INSIGHT_P6_INVENTORY_STEP: Final = "P6-1_ExistingStructureInsightInventory"
STRUCTURE_INSIGHT_P6_INVENTORY_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_ExistingInventory_20260611"
)

MODULE_STRUCTURE_INSIGHT_CANDIDATE: Final = "emlis_ai_structure_insight_candidate"
MODULE_STRUCTURE_INSIGHT_GATE: Final = "emlis_ai_structure_insight_gate"
MODULE_STRUCTURE_INSIGHT_SURFACE: Final = "emlis_ai_structure_insight_surface"
MODULE_COMPLETE_SURFACE_REALIZER: Final = "emlis_ai_complete_surface_realizer"
MODULE_TWO_STAGE_SECTION_SURFACE_PLAN: Final = "emlis_ai_two_stage_section_surface_plan"
MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE: Final = "emlis_ai_product_readfeel_long_run_product_gate"
MODULE_RUNTIME_SURFACE_BLIND_QA_LONG_RUN: Final = "emlis_ai_runtime_surface_blind_qa_long_run"
MODULE_MIRROR_ONLY_SURFACE_DETECTOR: Final = "emlis_ai_mirror_only_surface_detector"

P6_INVENTORY_TARGET_MODULE_IDS: Final[tuple[str, ...]] = (
    MODULE_STRUCTURE_INSIGHT_CANDIDATE,
    MODULE_STRUCTURE_INSIGHT_GATE,
    MODULE_STRUCTURE_INSIGHT_SURFACE,
    MODULE_COMPLETE_SURFACE_REALIZER,
    MODULE_TWO_STAGE_SECTION_SURFACE_PLAN,
    MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE,
    MODULE_RUNTIME_SURFACE_BLIND_QA_LONG_RUN,
    MODULE_MIRROR_ONLY_SURFACE_DETECTOR,
)
P6_INVENTORY_REQUIRED_MODULE_IDS: Final[frozenset[str]] = frozenset(P6_INVENTORY_TARGET_MODULE_IDS)

REASON_REQUIRED_MODULE_MISSING: Final = "required_structure_insight_module_missing"
REASON_CANDIDATE_MATERIAL_NOT_META_ONLY: Final = "candidate_material_not_meta_only"
REASON_GATE_HARDENING_NOT_CONFIRMED: Final = "gate_hardening_not_confirmed"
REASON_LIMITED_FAMILY_BOUNDARY_NOT_CONFIRMED: Final = "limited_family_boundary_not_confirmed"
REASON_DEEP_INSIGHT_SUPPRESSION_NOT_CONFIRMED: Final = "deep_insight_suppression_not_confirmed"
REASON_PUBLIC_OR_BODY_CONTRACT_RISK: Final = "public_or_body_contract_risk"
REASON_LONG_RUN_SPLIT_NOT_CONFIRMED: Final = "long_run_product_gate_split_not_confirmed"
REASON_MIRROR_ONLY_SIGNAL_NOT_CONFIRMED: Final = "mirror_only_detector_not_confirmed"
REASON_PHASE_ROADMAP_CONFUSION: Final = "existing_phase_marked_as_roadmap_p6_complete"

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
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
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_free_text",
        "raw_test_output",
        "test_output",
        "command_output",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
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
        "public_payload_changed",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "structure_insight_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
        "raw_test_output_included",
        "command_output_included",
        "terminal_output_included",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "target_judgement_agreement_allowed",
        "period_tendency_from_single_record_allowed",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "external_ai_used",
        "local_llm_used",
    }
)

_DEFAULT_MODULE_RECORDS: Final[tuple[dict[str, Any], ...]] = (
    {
        "module_id": MODULE_STRUCTURE_INSIGHT_CANDIDATE,
        "file_name": "emlis_ai_structure_insight_candidate.py",
        "existing_phase_label": "Phase7",
        "roadmap_p6_role": "internal_relation_candidate_material",
        "reuse_decision": "reuse_as_p6_candidate_material_base",
        "extension_decision": "extend_later_with_p6_relation_policy_and_quality_rubric",
        "candidate_material_meta_only": True,
        "gate_hardening_confirmed": False,
        "limited_family_boundary_confirmed": False,
        "deep_insight_suppression_confirmed": False,
        "long_run_product_gate_split_confirmed": False,
        "mirror_only_detector_confirmed": False,
    },
    {
        "module_id": MODULE_STRUCTURE_INSIGHT_GATE,
        "file_name": "emlis_ai_structure_insight_gate.py",
        "existing_phase_label": "Phase9",
        "roadmap_p6_role": "unsafe_insight_surface_gate",
        "reuse_decision": "reuse_as_p6_gate_base",
        "extension_decision": "extend_later_with_p6_gate_hardening_cases",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": True,
        "limited_family_boundary_confirmed": False,
        "deep_insight_suppression_confirmed": False,
        "long_run_product_gate_split_confirmed": False,
        "mirror_only_detector_confirmed": False,
    },
    {
        "module_id": MODULE_STRUCTURE_INSIGHT_SURFACE,
        "file_name": "emlis_ai_structure_insight_surface.py",
        "existing_phase_label": "Phase10",
        "roadmap_p6_role": "limited_family_surface_connection",
        "reuse_decision": "reuse_as_limited_surface_reference",
        "extension_decision": "extend_later_with_p6_surface_role_plan",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": True,
        "limited_family_boundary_confirmed": True,
        "deep_insight_suppression_confirmed": True,
        "long_run_product_gate_split_confirmed": False,
        "mirror_only_detector_confirmed": False,
    },
    {
        "module_id": MODULE_COMPLETE_SURFACE_REALIZER,
        "file_name": "emlis_ai_complete_surface_realizer.py",
        "existing_phase_label": "Phase10 integration",
        "roadmap_p6_role": "existing_comment_text_integration_point",
        "reuse_decision": "reuse_existing_two_stage_comment_text_path",
        "extension_decision": "avoid_public_response_shape_change",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": True,
        "limited_family_boundary_confirmed": True,
        "deep_insight_suppression_confirmed": True,
        "long_run_product_gate_split_confirmed": False,
        "mirror_only_detector_confirmed": True,
    },
    {
        "module_id": MODULE_TWO_STAGE_SECTION_SURFACE_PLAN,
        "file_name": "emlis_ai_two_stage_section_surface_plan.py",
        "existing_phase_label": "Phase10 support",
        "roadmap_p6_role": "section_role_plan_boundary",
        "reuse_decision": "reuse_as_surface_role_planning_reference",
        "extension_decision": "extend_later_with_p6_role_plan_scorecard",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": False,
        "limited_family_boundary_confirmed": True,
        "deep_insight_suppression_confirmed": True,
        "long_run_product_gate_split_confirmed": False,
        "mirror_only_detector_confirmed": False,
    },
    {
        "module_id": MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE,
        "file_name": "emlis_ai_product_readfeel_long_run_product_gate.py",
        "existing_phase_label": "long-run QA",
        "roadmap_p6_role": "separate_v1_product_pass_from_v2_structure_ready",
        "reuse_decision": "reuse_as_product_gate_split_reference",
        "extension_decision": "extend_later_with_p6_ratings_only_review",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": True,
        "limited_family_boundary_confirmed": True,
        "deep_insight_suppression_confirmed": True,
        "long_run_product_gate_split_confirmed": True,
        "mirror_only_detector_confirmed": True,
    },
    {
        "module_id": MODULE_RUNTIME_SURFACE_BLIND_QA_LONG_RUN,
        "file_name": "emlis_ai_runtime_surface_blind_qa_long_run.py",
        "existing_phase_label": "long-run QA",
        "roadmap_p6_role": "ratings_only_long_run_guardrail",
        "reuse_decision": "reuse_as_body_free_long_run_qa_reference",
        "extension_decision": "extend_later_with_p6_insight_delta_rubric",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": True,
        "limited_family_boundary_confirmed": False,
        "deep_insight_suppression_confirmed": False,
        "long_run_product_gate_split_confirmed": True,
        "mirror_only_detector_confirmed": False,
    },
    {
        "module_id": MODULE_MIRROR_ONLY_SURFACE_DETECTOR,
        "file_name": "emlis_ai_mirror_only_surface_detector.py",
        "existing_phase_label": "mirror-only detection",
        "roadmap_p6_role": "detect_repetition_only_surface_gap",
        "reuse_decision": "reuse_as_p6_value_delta_signal",
        "extension_decision": "extend_later_with_p6_inventory_to_quality_rubric_bridge",
        "candidate_material_meta_only": False,
        "gate_hardening_confirmed": False,
        "limited_family_boundary_confirmed": False,
        "deep_insight_suppression_confirmed": False,
        "long_run_product_gate_split_confirmed": False,
        "mirror_only_detector_confirmed": True,
    },
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _default_record_by_id() -> dict[str, Mapping[str, Any]]:
    return {record["module_id"]: record for record in _DEFAULT_MODULE_RECORDS}


def _normalize_record(record: Mapping[str, Any], *, index: int = 0) -> dict[str, Any]:
    source = _safe_mapping(record)
    module_id = _clean(source.get("module_id") or source.get("id")) or f"structure_insight_module_{index:03d}"
    defaults = _default_record_by_id().get(module_id, {})
    merged = {**defaults, **source}
    found = _bool(merged.get("found"), default=True)
    public_contract = _public_contract()
    public_contract.update({key: False for key in public_contract})
    body_free = _body_free_contract()
    body_free.update({key: False for key in body_free})
    normalized = {
        "module_id": module_id,
        "file_name": _clean(merged.get("file_name")) or f"{module_id}.py",
        "existing_phase_label": _clean(merged.get("existing_phase_label")) or "existing",
        "roadmap_p6_role": _clean(merged.get("roadmap_p6_role")) or "p6_inventory_candidate",
        "reuse_decision": _clean(merged.get("reuse_decision")) or "review_before_reuse",
        "extension_decision": _clean(merged.get("extension_decision")) or "extension_scope_not_yet_fixed",
        "found": found,
        "required_for_p6_inventory": module_id in P6_INVENTORY_REQUIRED_MODULE_IDS,
        "existing_phase_is_roadmap_p6_complete": merged.get("existing_phase_is_roadmap_p6_complete") is True,
        "candidate_material_meta_only": _bool(merged.get("candidate_material_meta_only")),
        "gate_hardening_confirmed": _bool(merged.get("gate_hardening_confirmed")),
        "limited_family_boundary_confirmed": _bool(merged.get("limited_family_boundary_confirmed")),
        "deep_insight_suppression_confirmed": _bool(merged.get("deep_insight_suppression_confirmed")),
        "long_run_product_gate_split_confirmed": _bool(merged.get("long_run_product_gate_split_confirmed")),
        "mirror_only_detector_confirmed": _bool(merged.get("mirror_only_detector_confirmed")),
        "body_free_inventory_record_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "public_release_applied": False,
        "release_allowed": False,
        "public_contract": public_contract,
        "body_free": body_free,
    }
    assert_structure_insight_p6_inventory_contract(normalized, allow_partial=True)
    return normalized


def _records_from_source(module_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    records = list(module_records or _DEFAULT_MODULE_RECORDS)
    normalized = [
        _normalize_record(item, index=index)
        for index, item in enumerate(records, start=1)
        if isinstance(item, Mapping)
    ]
    seen = {_clean(item.get("module_id")) for item in normalized}
    for module_id in P6_INVENTORY_TARGET_MODULE_IDS:
        if module_id not in seen:
            normalized.append(
                _normalize_record(
                    {
                        "module_id": module_id,
                        "found": False,
                        "reuse_decision": "cannot_reuse_until_found",
                        "extension_decision": "restore_or_confirm_before_p6",
                    },
                    index=len(normalized) + 1,
                )
            )
    return normalized


def _inventory_blockers(records: Sequence[Mapping[str, Any]]) -> list[str]:
    blockers: list[str] = []
    by_id = {_clean(item.get("module_id")): item for item in records}
    for module_id in P6_INVENTORY_REQUIRED_MODULE_IDS:
        item = by_id.get(module_id)
        if not item or item.get("found") is not True:
            blockers.append(f"{REASON_REQUIRED_MODULE_MISSING}:{module_id}")
    if by_id.get(MODULE_STRUCTURE_INSIGHT_CANDIDATE, {}).get("candidate_material_meta_only") is not True:
        blockers.append(REASON_CANDIDATE_MATERIAL_NOT_META_ONLY)
    if by_id.get(MODULE_STRUCTURE_INSIGHT_GATE, {}).get("gate_hardening_confirmed") is not True:
        blockers.append(REASON_GATE_HARDENING_NOT_CONFIRMED)
    if by_id.get(MODULE_STRUCTURE_INSIGHT_SURFACE, {}).get("limited_family_boundary_confirmed") is not True:
        blockers.append(REASON_LIMITED_FAMILY_BOUNDARY_NOT_CONFIRMED)
    if by_id.get(MODULE_STRUCTURE_INSIGHT_SURFACE, {}).get("deep_insight_suppression_confirmed") is not True:
        blockers.append(REASON_DEEP_INSIGHT_SUPPRESSION_NOT_CONFIRMED)
    if by_id.get(MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE, {}).get("long_run_product_gate_split_confirmed") is not True:
        blockers.append(REASON_LONG_RUN_SPLIT_NOT_CONFIRMED)
    if by_id.get(MODULE_MIRROR_ONLY_SURFACE_DETECTOR, {}).get("mirror_only_detector_confirmed") is not True:
        blockers.append(REASON_MIRROR_ONLY_SIGNAL_NOT_CONFIRMED)
    if any(item.get("existing_phase_is_roadmap_p6_complete") is True for item in records):
        blockers.append(REASON_PHASE_ROADMAP_CONFUSION)
    if any(_contains_text_payload_key(item) or _flag_true(item) for item in records):
        blockers.append(REASON_PUBLIC_OR_BODY_CONTRACT_RISK)
    return _dedupe(blockers)


def build_structure_insight_p6_inventory(
    *,
    module_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the body-free P6 inventory over existing Structure Insight assets."""

    run = _clean(run_id) or "p6_structure_insight_inventory"
    records = _records_from_source(module_records)
    blockers = _inventory_blockers(records)
    by_id = {_clean(item.get("module_id")): item for item in records}
    ready = not blockers
    reuse_ready_modules = [
        item["module_id"]
        for item in records
        if item.get("found") is True and _clean(item.get("reuse_decision")).startswith("reuse")
    ]
    extension_needed_modules = [
        item["module_id"]
        for item in records
        if item.get("found") is True and _clean(item.get("extension_decision")).startswith("extend")
    ]
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_INVENTORY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_INVENTORY_STEP,
        "run_id": run,
        "p6_inventory_created": True,
        "p6_inventory_only": True,
        "p6_inventory_ready": ready,
        "structure_insight_inventory_confirmed": ready,
        "ready_for_p6_entry_freeze": ready,
        "existing_phase_to_roadmap_p6_mixed_up": False,
        "target_module_ids": list(P6_INVENTORY_TARGET_MODULE_IDS),
        "required_module_ids": sorted(P6_INVENTORY_REQUIRED_MODULE_IDS),
        "module_count": len(records),
        "found_module_count": sum(1 for item in records if item.get("found") is True),
        "reuse_ready_module_ids": reuse_ready_modules,
        "reuse_ready_module_count": len(reuse_ready_modules),
        "extension_needed_module_ids": extension_needed_modules,
        "extension_needed_module_count": len(extension_needed_modules),
        "missing_required_module_ids": [
            module_id
            for module_id in sorted(P6_INVENTORY_REQUIRED_MODULE_IDS)
            if by_id.get(module_id, {}).get("found") is not True
        ],
        "inventory_blockers": blockers,
        "candidate_layer_seen": by_id.get(MODULE_STRUCTURE_INSIGHT_CANDIDATE, {}).get("found") is True,
        "candidate_material_meta_only_confirmed": by_id.get(MODULE_STRUCTURE_INSIGHT_CANDIDATE, {}).get(
            "candidate_material_meta_only"
        )
        is True,
        "gate_layer_seen": by_id.get(MODULE_STRUCTURE_INSIGHT_GATE, {}).get("found") is True,
        "gate_hardening_confirmed": by_id.get(MODULE_STRUCTURE_INSIGHT_GATE, {}).get("gate_hardening_confirmed")
        is True,
        "limited_surface_layer_seen": by_id.get(MODULE_STRUCTURE_INSIGHT_SURFACE, {}).get("found") is True,
        "limited_family_boundary_confirmed": by_id.get(MODULE_STRUCTURE_INSIGHT_SURFACE, {}).get(
            "limited_family_boundary_confirmed"
        )
        is True,
        "deep_insight_suppression_confirmed": by_id.get(MODULE_STRUCTURE_INSIGHT_SURFACE, {}).get(
            "deep_insight_suppression_confirmed"
        )
        is True,
        "long_run_layer_seen": by_id.get(MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE, {}).get("found") is True,
        "long_run_product_gate_split_confirmed": by_id.get(
            MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE, {}
        ).get("long_run_product_gate_split_confirmed")
        is True,
        "mirror_only_layer_seen": by_id.get(MODULE_MIRROR_ONLY_SURFACE_DETECTOR, {}).get("found") is True,
        "mirror_only_detector_confirmed": by_id.get(MODULE_MIRROR_ONLY_SURFACE_DETECTOR, {}).get(
            "mirror_only_detector_confirmed"
        )
        is True,
        "complete_realizer_public_key_change_blocked": True,
        "two_stage_role_plan_reuse_confirmed": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_inventory_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload = {
        "schema_version": STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_INVENTORY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_INVENTORY_STEP,
        "run_id": run,
        "summary": summary,
        "module_records": records,
        "public_summary": {},
        "p6_inventory_created": True,
        "p6_inventory_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_inventory_status_only": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload["public_summary"] = structure_insight_p6_inventory_public_summary(payload)
    assert_structure_insight_p6_inventory_contract(payload)
    return payload


def structure_insight_p6_inventory_public_summary(
    inventory_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _safe_mapping(inventory_payload_or_summary)
    source = _safe_mapping(payload.get("summary")) or payload
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_INVENTORY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_INVENTORY_STEP,
        "run_id": _clean(source.get("run_id")),
        "p6_inventory_created": source.get("p6_inventory_created") is True,
        "p6_inventory_ready": source.get("p6_inventory_ready") is True,
        "structure_insight_inventory_confirmed": source.get("structure_insight_inventory_confirmed") is True,
        "ready_for_p6_entry_freeze": source.get("ready_for_p6_entry_freeze") is True,
        "existing_phase_to_roadmap_p6_mixed_up": source.get("existing_phase_to_roadmap_p6_mixed_up") is True,
        "target_module_ids": _dedupe(source.get("target_module_ids")),
        "required_module_ids": _dedupe(source.get("required_module_ids")),
        "module_count": int(source.get("module_count") or 0),
        "found_module_count": int(source.get("found_module_count") or 0),
        "reuse_ready_module_ids": _dedupe(source.get("reuse_ready_module_ids")),
        "reuse_ready_module_count": int(source.get("reuse_ready_module_count") or 0),
        "extension_needed_module_ids": _dedupe(source.get("extension_needed_module_ids")),
        "extension_needed_module_count": int(source.get("extension_needed_module_count") or 0),
        "missing_required_module_ids": _dedupe(source.get("missing_required_module_ids")),
        "inventory_blockers": _dedupe(source.get("inventory_blockers")),
        "candidate_layer_seen": source.get("candidate_layer_seen") is True,
        "candidate_material_meta_only_confirmed": source.get("candidate_material_meta_only_confirmed") is True,
        "gate_layer_seen": source.get("gate_layer_seen") is True,
        "gate_hardening_confirmed": source.get("gate_hardening_confirmed") is True,
        "limited_surface_layer_seen": source.get("limited_surface_layer_seen") is True,
        "limited_family_boundary_confirmed": source.get("limited_family_boundary_confirmed") is True,
        "deep_insight_suppression_confirmed": source.get("deep_insight_suppression_confirmed") is True,
        "long_run_layer_seen": source.get("long_run_layer_seen") is True,
        "long_run_product_gate_split_confirmed": source.get("long_run_product_gate_split_confirmed") is True,
        "mirror_only_layer_seen": source.get("mirror_only_layer_seen") is True,
        "mirror_only_detector_confirmed": source.get("mirror_only_detector_confirmed") is True,
        "complete_realizer_public_key_change_blocked": source.get("complete_realizer_public_key_change_blocked")
        is True,
        "two_stage_role_plan_reuse_confirmed": source.get("two_stage_role_plan_reuse_confirmed") is True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "body_free_inventory_status_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
    }
    assert_structure_insight_p6_inventory_contract(summary, allow_partial=True)
    return summary


def dump_structure_insight_p6_inventory_public_summary(
    inventory_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = structure_insight_p6_inventory_public_summary(inventory_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_structure_insight_p6_inventory_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if not meta:
        raise ValueError("P6 Structure Insight inventory must be a mapping")
    if _contains_text_payload_key(meta):
        raise ValueError("P6 Structure Insight inventory must not include raw/comment/history/test body keys")
    if _flag_true(meta):
        raise ValueError("P6 Structure Insight inventory contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if meta.get("schema_version") != STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight inventory schema_version")
    if meta.get("step") != STRUCTURE_INSIGHT_P6_INVENTORY_STEP:
        raise ValueError("unexpected P6 Structure Insight inventory step")
    summary = _safe_mapping(meta.get("summary"))
    if summary.get("schema_version") != STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight inventory summary schema_version")
    if summary.get("release_allowed") is not False or meta.get("release_allowed") is not False:
        raise ValueError("P6 Structure Insight inventory must not allow release")
    for source_name, source in (("payload", meta), ("summary", summary)):
        public_contract = _safe_mapping(source.get("public_contract"))
        body_free = _safe_mapping(source.get("body_free"))
        for key in (
            "rn_visible_contract_changed",
            "rn_visible_title_changed",
            "public_response_key_added",
            "response_shape_changed",
            "api_route_changed",
            "request_key_changed",
            "db_schema_changed",
            "fixed_sentence_template_added",
            "release_allowed",
            "public_release_applied",
            "product_quality_released",
        ):
            if public_contract.get(key) is not False:
                raise ValueError(f"P6 inventory {source_name}.public_contract.{key} must be false")
        for key in (
            "raw_input_included",
            "raw_text_included",
            "input_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
        ):
            if body_free.get(key) is not False:
                raise ValueError(f"P6 inventory {source_name}.body_free.{key} must be false")


__all__ = [
    "STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_INVENTORY_STEP",
    "P6_INVENTORY_TARGET_MODULE_IDS",
    "P6_INVENTORY_REQUIRED_MODULE_IDS",
    "MODULE_STRUCTURE_INSIGHT_CANDIDATE",
    "MODULE_STRUCTURE_INSIGHT_GATE",
    "MODULE_STRUCTURE_INSIGHT_SURFACE",
    "MODULE_COMPLETE_SURFACE_REALIZER",
    "MODULE_TWO_STAGE_SECTION_SURFACE_PLAN",
    "MODULE_PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE",
    "MODULE_RUNTIME_SURFACE_BLIND_QA_LONG_RUN",
    "MODULE_MIRROR_ONLY_SURFACE_DETECTOR",
    "assert_structure_insight_p6_inventory_contract",
    "build_structure_insight_p6_inventory",
    "structure_insight_p6_inventory_public_summary",
    "dump_structure_insight_p6_inventory_public_summary",
]
