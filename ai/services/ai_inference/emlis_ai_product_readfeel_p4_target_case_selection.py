# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-1 target case selection for EmlisAI Product Read Feel family tuning.

P4-1 freezes the first body-free case subset used by P4 family product tuning.
It consumes the P3-9 connection decision plus the P3-1 public-safe baseline
index and returns only case identifiers, family/slice coverage, blocker ids,
target layers, and contract flags.  It does not render Emlis output, keep raw
input, keep ``comment_text`` bodies, change runtime gates, strengthen P5 visible
surfaces, or alter RN/API/DB contracts.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_POSITIVE,
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_SELF_DENIAL,
    FAMILY_STRUCTURE_QUESTION,
)
from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P3_PASS,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only
from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)

PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.target_case_selection.20260610.v1"
)
PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_ITEM_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.target_case_selection_item.20260610.v1"
)
PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.target_case_selection_summary.20260610.v1"
)
PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610: Final = (
    "P4-1_Target_Case_Selection"
)
PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SOURCE_20260610: Final = (
    "Cocolon_EmlisAI_P4_FamilyProductTuning_TargetCaseSelection_20260610"
)
PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610: Final = (
    "p4_initial_daily_unpleasant_structure_question_self_denial"
)

P4_MAIN_TARGET_FAMILIES_20260610: Final[tuple[str, ...]] = (
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_STRUCTURE_QUESTION,
)
P4_YELLOW_REVIEW_FAMILIES_20260610: Final[tuple[str, ...]] = (FAMILY_SELF_DENIAL,)
P4_BOUNDARY_REGRESSION_FAMILIES_20260610: Final[tuple[str, ...]] = (
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_DAILY_POSITIVE,
    FAMILY_RELATIONSHIP_BOUNDARY,
)
P4_BOUNDARY_REGRESSION_SLICES_20260610: Final[tuple[str, ...]] = (
    "limited_grounding",
    "source_unavailable_high_information",
    "history_line_eligible",
)
P4_FIRST_BLOCKER_IDS_20260610: Final[tuple[str, ...]] = (
    "rich_input_low_information_overroute",
    "generic_reception_surface",
)
P4_FIRST_TARGET_LAYERS_20260610: Final[tuple[str, ...]] = (
    "input_material_bundle",
    "ratio_policy",
)
P4_FAMILY_SELECTION_MINIMUMS_20260610: Final[dict[str, int]] = {
    FAMILY_DAILY_UNPLEASANT: 5,
    FAMILY_STRUCTURE_QUESTION: 5,
    FAMILY_SELF_DENIAL: 3,
    FAMILY_LOW_INFORMATION_SHORT: 2,
    FAMILY_DAILY_POSITIVE: 2,
    FAMILY_RELATIONSHIP_BOUNDARY: 2,
}
P4_SLICE_SELECTION_MINIMUMS_20260610: Final[dict[str, int]] = {
    "limited_grounding": 2,
    "source_unavailable_high_information": 1,
    "history_line_eligible": 2,
}

_MAIN_TARGET_LAYERS: Final[tuple[str, ...]] = (
    "input_material_bundle",
    "public_surface_requirement",
    "ratio_policy",
)
_YELLOW_REVIEW_LAYERS: Final[tuple[str, ...]] = (
    "state_answer_ratio_policy",
    "visible_surface_acceptance_gate",
)
_BOUNDARY_FAMILY_LAYERS: Final[dict[str, tuple[str, ...]]] = {
    FAMILY_LOW_INFORMATION_SHORT: ("input_material_bundle", "public_surface_requirement"),
    FAMILY_DAILY_POSITIVE: ("ratio_policy", "two_stage_section_surface_plan"),
    FAMILY_RELATIONSHIP_BOUNDARY: ("ratio_policy", "reception_mode_resolver"),
}
_BOUNDARY_SLICE_LAYERS: Final[dict[str, tuple[str, ...]]] = {
    "limited_grounding": ("material_quality", "public_surface_requirement"),
    "source_unavailable_high_information": ("public_surface_requirement", "gate_recovery_route"),
    "history_line_eligible": ("ratio_policy", "user_label_connection_boundary_regression"),
}

_FORBIDDEN_BODY_KEYS_20260610: Final[frozenset[str]] = frozenset(
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
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "blind_qa_free_text",
        "stdout",
        "stderr",
        "raw_test_output",
        "test_output",
        "traceback_body",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS_20260610: Final[frozenset[str]] = frozenset(
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
        "history_raw_text_included",
        "raw_test_output_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "runtime_repair_applied",
        "implementation_change_applied",
        "p4_runtime_tuning_applied",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 128) -> str:
    text_value = _clean(value) or default
    chars: list[str] = []
    for ch in text_value[:max_length]:
        chars.append(ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-")
    return "".join(chars).strip("-") or default


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        raw_values: Iterable[Any] = [values]
    elif isinstance(values, Mapping):
        raw_values = values.keys()
    elif isinstance(values, Iterable):
        raw_values = values
    else:
        raw_values = [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        text_value = _clean(value)
        if text_value and text_value not in seen:
            seen.add(text_value)
            out.append(text_value)
    return out


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_BODY_KEYS_20260610:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            current_path = f"{path}.{key_text}"
            if key_text in _FORBIDDEN_TRUE_FLAGS_20260610 and child is True:
                return current_path
            nested = _forbidden_true_flag_path(child, path=current_path)
            if nested:
                return nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def assert_product_readfeel_p4_target_case_selection_meta_only_20260610(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "p4_target_case_selection",
) -> None:
    """Reject body-bearing or runtime-mutating P4-1 target selection payloads."""

    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain raw input, output, history, review, or log body keys")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {flag_path}")
    assert_product_readfeel_rubric_meta_only(payload, source=f"{source}.rubric")
    if isinstance(payload, Mapping):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for index, item in enumerate(payload):
            if isinstance(item, Mapping):
                assert_emlis_ai_product_quality_contract_freeze_meta_only(
                    item, source=f"{source}.contract_freeze[{index}]"
                )
            else:
                raise ValueError(f"{source}.contract_freeze[{index}] must be a mapping")


def _summary_from_p3_9(decision: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(decision, Mapping):
        raise ValueError("P4-1 target selection requires a body-free P3-9 connection decision")
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        decision, source="p4_1.source_p3_9_decision"
    )
    summary = decision.get("summary")
    if isinstance(summary, Mapping):
        return dict(summary)
    return dict(decision)


def _require_p4_initial_hold(summary: Mapping[str, Any]) -> None:
    if _clean(summary.get("next_phase_decision")) != DECISION_P4_NEXT_P5_HOLD:
        raise ValueError("P4-1 target selection is only valid for P3-9 P4-next / P5-hold decisions")
    if summary.get("p4_connection_allowed") is not True:
        raise ValueError("P4-1 target selection requires p4_connection_allowed=True")
    if summary.get("p5_connection_allowed") is not False:
        raise ValueError("P4-1 target selection must keep p5_connection_allowed=False")
    if summary.get("current_only_readfeel_minimum_met") is not False:
        raise ValueError("P4-1 must not run after current-only readfeel is already marked stable")
    if summary.get("main_family_readfeel_minimum_met") is not False:
        raise ValueError("P4-1 must not run after main-family readfeel is already marked stable")

    repair_required = set(_dedupe(summary.get("repair_required_families")))
    yellow = set(_dedupe(summary.get("yellow_families")))
    reason_codes = set(_dedupe(summary.get("classified_reason_codes")))
    first_layers = set(_dedupe(summary.get("first_repair_target_layers")))
    hold_codes = set(_dedupe(summary.get("p5_hold_reason_codes")))

    if not set(P4_MAIN_TARGET_FAMILIES_20260610).issubset(repair_required):
        raise ValueError("P4-1 requires daily_unpleasant and structure_question as repair-required families")
    if not set(P4_YELLOW_REVIEW_FAMILIES_20260610).issubset(yellow):
        raise ValueError("P4-1 requires self_denial as the yellow review family")
    if not set(P4_FIRST_BLOCKER_IDS_20260610).issubset(reason_codes):
        raise ValueError("P4-1 requires rich-input and generic-reception blocker ids from P3-9")
    if not set(P4_FIRST_TARGET_LAYERS_20260610).issubset(first_layers):
        raise ValueError("P4-1 requires input_material_bundle and ratio_policy as first repair layers")
    if "current_only_readfeel_below_minimum" not in hold_codes:
        raise ValueError("P4-1 requires P5 hold because current-only readfeel is below minimum")


def _case_id(case: Mapping[str, Any]) -> str:
    return _safe_identifier(case.get("case_id") or case.get("case_ref_id"), default="")


def _family(case: Mapping[str, Any]) -> str:
    return _clean(case.get("family") or case.get("product_readfeel_family"))


def _coverage_slices(case: Mapping[str, Any]) -> list[str]:
    return _dedupe(case.get("coverage_slices"))


def _make_boundary_flags() -> dict[str, bool]:
    return {
        "body_free_case_references_only": True,
        "local_case_material_retained_here": False,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
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


def _p3_verdict_for_group(selection_group: str) -> str:
    if selection_group == "main_target":
        return VERDICT_LAYER_P3_REPAIR_REQUIRED
    if selection_group == "yellow_review":
        return VERDICT_LAYER_P3_YELLOW
    return VERDICT_LAYER_P3_PASS


def _blockers_for_selection(*, selection_group: str, family: str, slice_id: str = "") -> list[str]:
    if selection_group == "main_target":
        return list(P4_FIRST_BLOCKER_IDS_20260610)
    if selection_group == "yellow_review":
        return ["p3_yellow_readfeel_weakness", "self_denial_yellow_safety_adjacent_review"]
    if family == FAMILY_LOW_INFORMATION_SHORT:
        return ["low_information_short_boundary_regression"]
    if family == FAMILY_DAILY_POSITIVE:
        return ["daily_positive_temperature_regression"]
    if family == FAMILY_RELATIONSHIP_BOUNDARY:
        return ["relationship_boundary_target_judgement_regression"]
    if slice_id == "limited_grounding":
        return ["limited_grounding_boundary_regression"]
    if slice_id == "source_unavailable_high_information":
        return ["source_unavailable_high_information_boundary_regression"]
    if slice_id == "history_line_eligible":
        return ["history_line_eligible_current_input_masking_regression"]
    return ["p4_boundary_regression"]


def _layers_for_selection(*, selection_group: str, family: str, slice_id: str = "") -> list[str]:
    if selection_group == "main_target":
        return list(_MAIN_TARGET_LAYERS)
    if selection_group == "yellow_review":
        return list(_YELLOW_REVIEW_LAYERS)
    if slice_id:
        return list(_BOUNDARY_SLICE_LAYERS.get(slice_id, ("public_surface_requirement",)))
    return list(_BOUNDARY_FAMILY_LAYERS.get(family, ("ratio_policy",)))


def _selected_reason(*, selection_group: str, family: str, slice_id: str = "") -> str:
    if selection_group == "main_target":
        return f"p3_9_repair_required_family_{family}"
    if selection_group == "yellow_review":
        return f"p3_9_yellow_family_{family}_safety_adjacent_review"
    if slice_id:
        return f"p4_boundary_regression_slice_{slice_id}"
    return f"p4_boundary_regression_family_{family}"


def _merge_selected_case(
    selected_by_id: dict[str, dict[str, Any]],
    case: Mapping[str, Any],
    *,
    selection_group: str,
    priority: int,
    run_id: str,
    source_decision: str,
    slice_id: str = "",
) -> None:
    case_ref_id = _case_id(case)
    if not case_ref_id:
        raise ValueError("P4-1 baseline public-safe index contains a case without a safe id")
    family = _family(case)
    coverage = _coverage_slices(case)
    if not family:
        raise ValueError(f"P4-1 baseline public-safe index contains a case without family: {case_ref_id}")
    if not coverage:
        raise ValueError(f"P4-1 baseline public-safe index contains a case without coverage_slices: {case_ref_id}")

    blockers = _blockers_for_selection(selection_group=selection_group, family=family, slice_id=slice_id)
    layers = _layers_for_selection(selection_group=selection_group, family=family, slice_id=slice_id)
    reason = _selected_reason(selection_group=selection_group, family=family, slice_id=slice_id)
    verdict = _p3_verdict_for_group(selection_group)

    if case_ref_id in selected_by_id:
        item = selected_by_id[case_ref_id]
        item["selection_groups"] = _dedupe([*item["selection_groups"], selection_group])
        item["coverage_slices"] = _dedupe([*item["coverage_slices"], *coverage])
        item["blocker_ids"] = _dedupe([*item["blocker_ids"], *blockers])
        item["target_layers"] = _dedupe([*item["target_layers"], *layers])
        item["selected_reason_codes"] = _dedupe([*item["selected_reason_codes"], reason])
        if priority < int(item["selection_priority"]):
            item["selection_priority"] = priority
            item["p3_verdict_layer"] = verdict
            item["selected_reason"] = reason
        return

    item = {
        "schema_version": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_ITEM_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_ITEM_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610,
        "run_id": run_id,
        "case_ref_id": case_ref_id,
        "family": family,
        "coverage_slices": coverage,
        "selection_groups": [selection_group],
        "selection_priority": priority,
        "p3_verdict_layer": verdict,
        "blocker_ids": blockers,
        "target_layers": layers,
        "selected_reason": reason,
        "selected_reason_codes": [reason],
        "source_p3_9_decision": source_decision,
        "main_target_case": selection_group == "main_target",
        "yellow_review_case": selection_group == "yellow_review",
        "boundary_regression_case": selection_group == "boundary_regression",
        "local_case_material_available": case.get("local_case_material_available") is True,
        "local_case_material_is_synthetic": case.get("local_case_material_is_synthetic") is True,
        **_make_boundary_flags(),
    }
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(item, source="p4_1.selected_case")
    selected_by_id[case_ref_id] = item


def _selected_family_counts(selected_cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counter = Counter(_family(case) for case in selected_cases)
    return {family: int(counter.get(family, 0)) for family in sorted(counter)}


def _selected_slice_counts(selected_cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in selected_cases:
        counter.update(_coverage_slices(case))
    return dict(sorted(counter.items()))


def _selected_group_counts(selected_cases: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for case in selected_cases:
        counter.update(_dedupe(case.get("selection_groups")))
    return dict(sorted(counter.items()))


def _add_family_cases(
    selected_by_id: dict[str, dict[str, Any]],
    baseline_cases: Sequence[Mapping[str, Any]],
    *,
    family: str,
    minimum: int,
    selection_group: str,
    priority: int,
    run_id: str,
    source_decision: str,
) -> None:
    added = 0
    for case in baseline_cases:
        if _family(case) != family:
            continue
        _merge_selected_case(
            selected_by_id,
            case,
            selection_group=selection_group,
            priority=priority,
            run_id=run_id,
            source_decision=source_decision,
        )
        added += 1
        if added >= minimum:
            break
    if added < minimum:
        raise ValueError(f"P4-1 could not select {minimum} cases for family {family}")


def _current_slice_count(selected_cases: Sequence[Mapping[str, Any]], slice_id: str) -> int:
    return sum(1 for case in selected_cases if slice_id in _coverage_slices(case))


def _current_boundary_slice_count(selected_cases: Sequence[Mapping[str, Any]], slice_id: str) -> int:
    return sum(
        1
        for case in selected_cases
        if slice_id in _coverage_slices(case) and "boundary_regression" in _dedupe(case.get("selection_groups"))
    )


def _add_slice_cases(
    selected_by_id: dict[str, dict[str, Any]],
    baseline_cases: Sequence[Mapping[str, Any]],
    *,
    slice_id: str,
    minimum: int,
    run_id: str,
    source_decision: str,
) -> None:
    for case in baseline_cases:
        if _current_boundary_slice_count(list(selected_by_id.values()), slice_id) >= minimum:
            return
        if slice_id not in _coverage_slices(case):
            continue
        _merge_selected_case(
            selected_by_id,
            case,
            selection_group="boundary_regression",
            priority=30,
            run_id=run_id,
            source_decision=source_decision,
            slice_id=slice_id,
        )
    if _current_boundary_slice_count(list(selected_by_id.values()), slice_id) < minimum:
        raise ValueError(f"P4-1 could not select {minimum} boundary cases for coverage slice {slice_id}")


def _case_sort_key(item: Mapping[str, Any]) -> tuple[int, str]:
    return (int(item.get("selection_priority", 99)), _clean(item.get("case_ref_id")))


def _build_summary(
    *,
    p3_summary: Mapping[str, Any],
    selected_cases: Sequence[Mapping[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    family_counts = _selected_family_counts(selected_cases)
    slice_counts = _selected_slice_counts(selected_cases)
    group_counts = _selected_group_counts(selected_cases)
    below_minimum_families = [
        family
        for family, minimum in P4_FAMILY_SELECTION_MINIMUMS_20260610.items()
        if int(family_counts.get(family, 0)) < minimum
    ]
    below_minimum_slices = [
        slice_id
        for slice_id, minimum in P4_SLICE_SELECTION_MINIMUMS_20260610.items()
        if int(slice_counts.get(slice_id, 0)) < minimum
    ]
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610,
        "run_id": run_id,
        "selection_profile": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610,
        "source_p3_9_decision": _clean(p3_summary.get("next_phase_decision")),
        "p4_connection_allowed": p3_summary.get("p4_connection_allowed") is True,
        "p5_connection_allowed": p3_summary.get("p5_connection_allowed") is True,
        "current_only_readfeel_minimum_met": p3_summary.get("current_only_readfeel_minimum_met") is True,
        "main_family_readfeel_minimum_met": p3_summary.get("main_family_readfeel_minimum_met") is True,
        "source_repair_required_families": _dedupe(p3_summary.get("repair_required_families")),
        "source_yellow_families": _dedupe(p3_summary.get("yellow_families")),
        "source_classified_reason_codes": _dedupe(p3_summary.get("classified_reason_codes")),
        "source_first_repair_target_layers": _dedupe(p3_summary.get("first_repair_target_layers")),
        "source_p5_hold_reason_codes": _dedupe(p3_summary.get("p5_hold_reason_codes")),
        "main_target_families": list(P4_MAIN_TARGET_FAMILIES_20260610),
        "yellow_review_families": list(P4_YELLOW_REVIEW_FAMILIES_20260610),
        "boundary_regression_families": list(P4_BOUNDARY_REGRESSION_FAMILIES_20260610),
        "boundary_regression_slices": list(P4_BOUNDARY_REGRESSION_SLICES_20260610),
        "selected_case_count": len(selected_cases),
        "selected_family_counts": family_counts,
        "selected_coverage_slice_counts": slice_counts,
        "selected_group_counts": group_counts,
        "family_selection_minimums": dict(P4_FAMILY_SELECTION_MINIMUMS_20260610),
        "slice_selection_minimums": dict(P4_SLICE_SELECTION_MINIMUMS_20260610),
        "below_minimum_families": below_minimum_families,
        "below_minimum_slices": below_minimum_slices,
        "p4_target_case_selection_fixed": not below_minimum_families and not below_minimum_slices,
        "p4_material_audit_ready": not below_minimum_families and not below_minimum_slices,
        "p5_hold_fixed": True,
        "p5_hold_until_current_only_readfeel_stable": True,
        **_make_boundary_flags(),
    }
    summary["p5_connection_allowed"] = False
    summary["current_only_readfeel_minimum_met"] = False
    summary["main_family_readfeel_minimum_met"] = False
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(summary, source="p4_1.summary")
    return summary


def build_product_readfeel_p4_target_case_selection_20260610(
    *,
    p3_connection_decision: Mapping[str, Any] | None,
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the P4-1 body-free target case selection packet."""

    p3_summary = _summary_from_p3_9(p3_connection_decision)
    _require_p4_initial_hold(p3_summary)
    if not isinstance(baseline_public_safe_index, Sequence) or isinstance(
        baseline_public_safe_index, (str, bytes, bytearray)
    ):
        raise ValueError("P4-1 requires the P3-1 public-safe baseline case index")
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(
        baseline_public_safe_index,
        source="p4_1.source_baseline_public_safe_index",
    )

    baseline_cases = [dict(case) for case in baseline_public_safe_index if isinstance(case, Mapping)]
    if len(baseline_cases) < 60:
        raise ValueError("P4-1 requires the full P3-1 body-free baseline index before selection")
    run_id_value = _safe_identifier(run_id or p3_summary.get("run_id"), default="p4_1_target_case_selection")
    source_decision = _clean(p3_summary.get("next_phase_decision"))

    selected_by_id: dict[str, dict[str, Any]] = {}
    for family in P4_MAIN_TARGET_FAMILIES_20260610:
        _add_family_cases(
            selected_by_id,
            baseline_cases,
            family=family,
            minimum=P4_FAMILY_SELECTION_MINIMUMS_20260610[family],
            selection_group="main_target",
            priority=10,
            run_id=run_id_value,
            source_decision=source_decision,
        )
    for family in P4_YELLOW_REVIEW_FAMILIES_20260610:
        _add_family_cases(
            selected_by_id,
            baseline_cases,
            family=family,
            minimum=P4_FAMILY_SELECTION_MINIMUMS_20260610[family],
            selection_group="yellow_review",
            priority=20,
            run_id=run_id_value,
            source_decision=source_decision,
        )
    for family in P4_BOUNDARY_REGRESSION_FAMILIES_20260610:
        _add_family_cases(
            selected_by_id,
            baseline_cases,
            family=family,
            minimum=P4_FAMILY_SELECTION_MINIMUMS_20260610[family],
            selection_group="boundary_regression",
            priority=30,
            run_id=run_id_value,
            source_decision=source_decision,
        )
    for slice_id, minimum in P4_SLICE_SELECTION_MINIMUMS_20260610.items():
        _add_slice_cases(
            selected_by_id,
            baseline_cases,
            slice_id=slice_id,
            minimum=minimum,
            run_id=run_id_value,
            source_decision=source_decision,
        )

    selected_cases = sorted(selected_by_id.values(), key=_case_sort_key)
    summary = _build_summary(p3_summary=p3_summary, selected_cases=selected_cases, run_id=run_id_value)
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610,
        "run_id": run_id_value,
        "selection_profile": PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610,
        "summary": summary,
        "selected_cases": selected_cases,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_fixed": True,
        "p5_hold_fixed": True,
        **_make_boundary_flags(),
    }
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(payload, source="p4_1.selection")
    return payload


def build_product_readfeel_p4_target_case_selection_public_summary_20260610(
    selection_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(selection_payload or {})
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(payload, source="p4_1.public_summary_source")
    summary = dict(payload.get("summary") or {})
    selected_cases = [case for case in payload.get("selected_cases") or [] if isinstance(case, Mapping)]
    public_summary = dict(summary)
    public_summary["schema_version"] = PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610
    public_summary["version"] = PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610
    public_summary["source"] = PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SOURCE_20260610
    public_summary["source_step"] = PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610
    public_summary["selected_case_refs"] = [
        {
            "case_ref_id": _clean(case.get("case_ref_id")),
            "family": _clean(case.get("family")),
            "coverage_slices": _dedupe(case.get("coverage_slices")),
            "selection_groups": _dedupe(case.get("selection_groups")),
            "blocker_ids": _dedupe(case.get("blocker_ids")),
            "target_layers": _dedupe(case.get("target_layers")),
        }
        for case in selected_cases
    ]
    public_summary.update(_make_boundary_flags())
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(public_summary, source="p4_1.public_summary")
    return public_summary


def dump_product_readfeel_p4_target_case_selection_public_summary_20260610(
    selection_payload: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p4_target_case_selection_public_summary_20260610(selection_payload)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_ITEM_VERSION_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610",
    "P4_MAIN_TARGET_FAMILIES_20260610",
    "P4_YELLOW_REVIEW_FAMILIES_20260610",
    "P4_BOUNDARY_REGRESSION_FAMILIES_20260610",
    "P4_BOUNDARY_REGRESSION_SLICES_20260610",
    "P4_FAMILY_SELECTION_MINIMUMS_20260610",
    "P4_SLICE_SELECTION_MINIMUMS_20260610",
    "assert_product_readfeel_p4_target_case_selection_meta_only_20260610",
    "build_product_readfeel_p4_target_case_selection_20260610",
    "build_product_readfeel_p4_target_case_selection_public_summary_20260610",
    "dump_product_readfeel_p4_target_case_selection_public_summary_20260610",
]
