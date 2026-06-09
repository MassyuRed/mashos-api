# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-7 First Repair Design for EmlisAI Product Read Feel baseline.

P3-7 consumes the body-free P3-6 repair priority ledger and fixes the first
implementation design unit before any runtime repair is attempted.  It does not
change rendering, gates, API contracts, RN contracts, DB schema, or release
state.  The output is an implementation design packet made only of safe case
identifiers, blocker ids, target layers, candidate files, prohibited fix paths,
and regression subsets.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_p3_repair_priority_ledger import (
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609,
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_P1_DISPLAY_REPAIR,
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only

PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.first_repair_design.20260609.v1"
)
PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_ITEM_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.first_repair_design_item.20260609.v1"
)
PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.first_repair_design_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609: Final = (
    "P3-7_First_Repair_Design"
)
PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_FirstRepairDesign_20260609"
)
PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_PROFILE_20260609: Final = (
    "local_product_readfeel_p3_first_repair_design"
)

FORBIDDEN_BODY_KEYS_20260609: Final[frozenset[str]] = frozenset(
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
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "body",
        "text",
    }
)
FORBIDDEN_TRUE_FLAGS_20260609: Final[frozenset[str]] = frozenset(
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
        "external_ai_used",
        "local_llm_used",
    }
)

P2_BLOCKERS_20260609: Final[frozenset[str]] = frozenset(
    {
        "contract_violation",
        "surface_breakage",
        "product_surface_invalid",
        "self_denial_identity_claim_risk",
        "relationship_target_judgement_risk",
    }
)
P1_BLOCKERS_20260609: Final[frozenset[str]] = frozenset(
    {
        "public_display_not_reached",
        "comment_text_missing",
    }
)
REPAIR_A_BLOCKERS_20260609: Final[frozenset[str]] = frozenset(
    {
        "rich_input_low_information_overroute",
        "input_core_missing",
        "event_reaction_missing",
        "desire_fear_conflict_missing",
        "state_structure_missing",
        "limited_grounding_collapsed_to_question",
    }
)
REPAIR_B_BLOCKERS_20260609: Final[frozenset[str]] = frozenset(
    {
        "generic_reception_surface",
        "repeated_surface_signature",
        "family_temperature_flattened",
        "structure_question_answered_as_comfort",
        "positive_overweighted",
        "positive_underreceived",
        "p3_readfeel_gap",
        "p3_yellow_readfeel_weakness",
    }
)
BACKLOG_BLOCKERS_20260609: Final[frozenset[str]] = frozenset(
    {
        "history_line_masks_current_input_gap",
        "structure_insight_gap",
    }
)

REPAIR_A_FILE_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_current_input_bundle.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_input_material_bundle.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_public_surface_requirement.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_low_information_observation_composer.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_limited_grounding_reception_surface.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_gate_recovery_loop.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_reply_service.py",
)
REPAIR_B_FILE_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_ratio_policy.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_mirror_only_surface_detector.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_question_dominance_guard.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py",
)
P2_FILE_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_runtime_surface_pre_return_gate.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_product_quality_contract_freeze.py",
)
P1_FILE_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emotion_submit_service.py",
    "mashos-api/ai/services/ai_inference/api_emotion_submit.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
)
BACKLOG_FILE_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/services/ai_inference/emlis_ai_user_label_connection_surface.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_candidate.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_gate.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_surface.py",
)

DO_NOT_TOUCH_FILES_20260609: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
    "Cocolon/tests/rn-screen-contracts.test.js",
    "mashos-api/ai/services/ai_inference/api_emotion_submit.py",
    "mashos-api/ai/services/ai_inference/emotion_submit_service.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
    "DB physical schema / write path",
    "public response top-level keys",
    "Free / Plus / Premium plan boundary",
)
FORBIDDEN_FIX_PATHS_20260609: Final[tuple[str, ...]] = (
    "gate_relaxation",
    "display_gate_relaxation",
    "grounding_gate_relaxation",
    "reader_gate_relaxation",
    "template_gate_relaxation",
    "fixed_comment_text_template",
    "exact_comment_text_lock",
    "case_specific_runtime_branch",
    "fixture_string_runtime_condition",
    "input_body_keyword_branching",
    "public_response_key_change",
    "api_route_change",
    "db_schema_change",
    "rn_display_contract_change",
    "history_line_masking_current_input_gap",
)
FIRST_REPAIR_TEST_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_first_repair_design_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_verdict_split_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_local_output_capture_20260609.py",
)
REGRESSION_SUBSET_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_contract_freeze_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_baseline_case_matrix_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_inventory_connection_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_verdict_split_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_first_repair_design_20260609.py",
)
REPAIR_A_ALLOWED_STEPS_20260609: Final[tuple[str, ...]] = (
    "inspect_visible_material_slot_transfer",
    "preserve_visible_material_slots_before_low_information_question_surface",
    "separate_material_quality_from_surface_shape_without_gate_relaxation",
    "bind_limited_grounding_reception_before_question_only_fallback",
    "verify_source_unavailable_is_not_recast_as_normal_rebuild",
)
REPAIR_B_ALLOWED_STEPS_20260609: Final[tuple[str, ...]] = (
    "inspect_phrase_role_and_section_plan",
    "preserve_family_temperature_before_generic_closing",
    "use_ratio_policy_without_case_specific_completed_sentence",
    "add_surface_signature_regression_without_fixed_templates",
    "verify_structure_question_does_not_fall_back_to_comfort_only",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value) or default
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"
    clipped = text[:max_length]
    return clipped if clipped and all(ch in allowed for ch in clipped) else default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        raw_values: list[Any] = []
    elif isinstance(values, (str, bytes, bytearray)):
        raw_values = [values]
    elif isinstance(values, Iterable):
        raw_values = list(values)
    else:
        raw_values = [values]
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
            if str(key) in FORBIDDEN_BODY_KEYS_20260609:
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
            if str(key) in FORBIDDEN_TRUE_FLAGS_20260609 and child is True:
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


def assert_product_readfeel_p3_first_repair_design_meta_only_20260609(
    payload: Any,
    *,
    source: str = "product_readfeel_p3_first_repair_design",
) -> None:
    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} contains a raw/display body key")
    flag_path = _forbidden_true_flag_path(payload, path=source)
    if flag_path:
        raise ValueError(f"{source} marks forbidden true flag at {flag_path}")
    if isinstance(payload, Mapping):
        if payload.get("product_gate_ready") is not False and "product_gate_ready" in payload:
            raise ValueError(f"{source} must keep product_gate_ready false")
        if payload.get("public_release_applied") is not False and "public_release_applied" in payload:
            raise ValueError(f"{source} must keep public_release_applied false")
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    assert_product_readfeel_rubric_meta_only(payload, source=f"{source}.rubric")


def _extract_ledger_items(ledger_or_items: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if ledger_or_items is None:
        return []
    if isinstance(ledger_or_items, Mapping):
        if ledger_or_items.get("schema_version") == PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609:
            assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(ledger_or_items)
        raw_items = ledger_or_items.get("items") or ledger_or_items.get("first_repair_target_items") or []
    else:
        raw_items = ledger_or_items
    items: list[dict[str, Any]] = []
    for index, item in enumerate(raw_items or []):
        if not isinstance(item, Mapping):
            raise ValueError(f"P3-7 repair priority item[{index}] must be a mapping")
        assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(
            item,
            source=f"p3_7.repair_priority_item[{index}]",
        )
        items.append(dict(item))
    return items


def _item_blocker(item: Mapping[str, Any]) -> str:
    return _safe_identifier(item.get("blocker_id"), default="manual_review")


def _item_layer(item: Mapping[str, Any]) -> str:
    return _safe_identifier(item.get("verdict_layer"), default="")


def _profile_for_item(item: Mapping[str, Any], *, p2_red_present: bool) -> tuple[str, str, bool, tuple[str, ...], tuple[str, ...], str]:
    blocker = _item_blocker(item)
    layer = _item_layer(item)
    if p2_red_present or layer == VERDICT_LAYER_P2_RED or blocker in P2_BLOCKERS_20260609:
        return (
            "p2_surface_safety_or_contract_first",
            "return_to_p2_surface_safety_before_p3_first_repair",
            False,
            P2_FILE_CANDIDATES_20260609,
            FIRST_REPAIR_TEST_CANDIDATES_20260609,
            "p2_or_contract_repair_before_product_readfeel_changes",
        )
    if layer == VERDICT_LAYER_P1_DISPLAY_REPAIR or blocker in P1_BLOCKERS_20260609:
        return (
            "p1_display_reliability_first",
            "repair_display_reliability_before_p3_first_repair",
            False,
            P1_FILE_CANDIDATES_20260609,
            FIRST_REPAIR_TEST_CANDIDATES_20260609,
            "display_contract_repair_before_product_readfeel_changes",
        )
    if blocker in REPAIR_A_BLOCKERS_20260609:
        return (
            "repair_A_rich_input_low_information_overroute",
            "design_current_input_readfeel_repair_A",
            True,
            REPAIR_A_FILE_CANDIDATES_20260609,
            (
                *FIRST_REPAIR_TEST_CANDIDATES_20260609,
                "mashos-api/ai/tests/test_emlis_ai_public_surface_requirement_p1.py",
                "mashos-api/ai/tests/test_emlis_ai_limited_grounding_reception_surface_p4.py",
                "mashos-api/ai/tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py",
            ),
            "preserve_visible_material_slots_without_low_information_gate_relaxation",
        )
    if blocker in BACKLOG_BLOCKERS_20260609:
        return (
            "p5_p6_backlog_not_first_p3_repair",
            "defer_history_or_structure_backlog_until_current_input_readfeel_is_clear",
            False,
            BACKLOG_FILE_CANDIDATES_20260609,
            FIRST_REPAIR_TEST_CANDIDATES_20260609,
            "defer_to_p5_or_p6_backlog_after_p3_current_input_readfeel",
        )
    if blocker in REPAIR_B_BLOCKERS_20260609 or layer in {VERDICT_LAYER_P3_REPAIR_REQUIRED, VERDICT_LAYER_P3_YELLOW}:
        return (
            "repair_B_generic_repeated_or_family_temperature",
            "design_surface_specificity_repair_B",
            True,
            REPAIR_B_FILE_CANDIDATES_20260609,
            (
                *FIRST_REPAIR_TEST_CANDIDATES_20260609,
                "mashos-api/ai/tests/test_emlis_ai_product_readfeel_surface_v1_phase5.py",
                "mashos-api/ai/tests/test_emlis_ai_mirror_only_surface_detector.py",
                "mashos-api/ai/tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py",
            ),
            "preserve_input_core_and_family_temperature_without_fixed_templates",
        )
    return (
        "manual_review_before_first_repair",
        "manual_review_before_runtime_repair",
        False,
        tuple(_dedupe(item.get("target_file_candidates"))),
        FIRST_REPAIR_TEST_CANDIDATES_20260609,
        "manual_review_before_product_readfeel_changes",
    )


def _repair_steps_for_profile(profile_id: str) -> tuple[str, ...]:
    if profile_id == "repair_A_rich_input_low_information_overroute":
        return REPAIR_A_ALLOWED_STEPS_20260609
    if profile_id == "repair_B_generic_repeated_or_family_temperature":
        return REPAIR_B_ALLOWED_STEPS_20260609
    if profile_id == "p2_surface_safety_or_contract_first":
        return (
            "freeze_p3_repair_until_p2_red_is_zero",
            "inspect_contract_or_surface_safety_blocker",
            "rerun_p2_p3_verdict_split_before_p3_repair",
        )
    if profile_id == "p1_display_reliability_first":
        return (
            "freeze_p3_repair_until_public_display_contract_is_green",
            "inspect_public_reached_rn_visible_product_surface_valid_separately",
            "rerun_display_contract_before_p3_repair",
        )
    if profile_id == "p5_p6_backlog_not_first_p3_repair":
        return (
            "defer_history_or_structure_backlog",
            "collect_current_input_readfeel_blocker_before_p5_or_p6",
            "do_not_mask_current_input_gap_with_history_line",
        )
    return ("manual_review_before_runtime_repair",)


def _merge_file_candidates(primary: Sequence[Any], ledger_candidates: Sequence[Any] | Any | None) -> list[str]:
    return _dedupe([*list(primary or []), *_dedupe(ledger_candidates)])


def _design_item_from_ledger_item(
    item: Mapping[str, Any],
    *,
    p2_red_present: bool,
    priority: int,
    run_id: str,
) -> dict[str, Any]:
    profile_id, design_action, selected, primary_files, test_candidates, repair_policy = _profile_for_item(
        item,
        p2_red_present=p2_red_present,
    )
    target_file_candidates = _merge_file_candidates(primary_files, item.get("target_file_candidates"))
    first_test_candidates = _dedupe(test_candidates)
    design = {
        "schema_version": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_ITEM_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_ITEM_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609,
        "run_id": run_id,
        "priority": priority,
        "source_ledger_priority": _to_int(item.get("priority"), priority),
        "source_blocker_id": _item_blocker(item),
        "source_blocker_category": _clean(item.get("blocker_category")),
        "source_verdict_layer": _item_layer(item),
        "source_repair_action": _clean(item.get("repair_action")),
        "design_profile_id": profile_id,
        "design_action": design_action,
        "repair_policy": repair_policy,
        "selected_for_first_runtime_repair": selected,
        "p3_runtime_repair_allowed": selected and not p2_red_present,
        "implementation_stage": "design_only",
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "case_count": _to_int(item.get("case_count"), 0),
        "families": _dedupe(item.get("families")),
        "family_counts": dict(item.get("family_counts") or {}) if isinstance(item.get("family_counts"), Mapping) else {},
        "coverage_slices": _dedupe(item.get("coverage_slices")),
        "sample_case_ids": _dedupe(item.get("sample_case_ids"))[:5],
        "reason_codes": _dedupe(item.get("reason_codes")),
        "target_layers": _dedupe(item.get("target_layers")),
        "change_file_candidates": target_file_candidates,
        "target_file_candidates": target_file_candidates,
        "do_not_touch_files": list(DO_NOT_TOUCH_FILES_20260609),
        "forbidden_fix_paths": list(FORBIDDEN_FIX_PATHS_20260609),
        "repair_steps": list(_repair_steps_for_profile(profile_id)),
        "first_test_candidates": first_test_candidates,
        "regression_subset": list(REGRESSION_SUBSET_20260609),
        "baseline_subset_case_ids": _dedupe(item.get("sample_case_ids"))[:5],
        "max_first_targets_respected": True,
        "gate_relaxation_excluded_from_fix_plan": True,
        "fixed_template_fix_excluded": True,
        "case_specific_runtime_branch_excluded": True,
        "history_line_not_allowed_to_mask_current_input_gap": True,
        "material_quality_not_forced_to_eligible": profile_id == "repair_A_rich_input_low_information_overroute",
        "visible_material_slots_must_not_collapse_to_question_only": profile_id == "repair_A_rich_input_low_information_overroute",
        "source_unavailable_not_recast_as_normal_rebuild": profile_id == "repair_A_rich_input_low_information_overroute",
        "phrase_role_section_plan_must_preserve_input_core": profile_id == "repair_B_generic_repeated_or_family_temperature",
        "family_ratio_policy_used_without_fixed_sentence": profile_id == "repair_B_generic_repeated_or_family_temperature",
        "daily_positive_not_overanalyzed": profile_id == "repair_B_generic_repeated_or_family_temperature",
        "daily_unpleasant_emotion_not_erased": profile_id == "repair_B_generic_repeated_or_family_temperature",
        "self_denial_not_confirmed_as_identity": True,
        "structure_question_not_answered_as_comfort_only": profile_id == "repair_B_generic_repeated_or_family_temperature",
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
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
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(design, source="p3_7.design_item")
    return design


def _decision_from_design_items(
    *,
    p2_red_present: bool,
    p1_display_repair_present: bool,
    runtime_repair_count: int,
    backlog_count: int,
    source_decision: str,
) -> str:
    if p2_red_present:
        return "return_to_p2_surface_safety_before_first_repair_design"
    if p1_display_repair_present:
        return "repair_display_reliability_before_first_repair_design"
    if runtime_repair_count > 0:
        return "start_first_repair_implementation_design_with_max_two_targets"
    if backlog_count > 0:
        return "defer_p5_p6_backlog_and_collect_current_input_readfeel_evidence"
    if source_decision:
        return "manual_review_before_first_repair_implementation"
    return "wait_for_p3_6_repair_priority_ledger"


def _summary(
    *,
    ledger: Mapping[str, Any] | None,
    design_items: Sequence[Mapping[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    source_summary = dict((ledger or {}).get("summary") or (ledger or {}).get("public_summary") or {}) if isinstance(ledger, Mapping) else {}
    p2_red_present = bool(source_summary.get("p2_red_present")) or any(
        item.get("source_verdict_layer") == VERDICT_LAYER_P2_RED for item in design_items
    )
    p1_display_repair_present = bool(source_summary.get("p1_display_repair_required_count")) or any(
        item.get("source_verdict_layer") == VERDICT_LAYER_P1_DISPLAY_REPAIR for item in design_items
    )
    runtime_items = [item for item in design_items if item.get("selected_for_first_runtime_repair") is True]
    backlog_items = [item for item in design_items if item.get("design_profile_id") == "p5_p6_backlog_not_first_p3_repair"]
    families = _dedupe(family for item in design_items for family in item.get("families") or [])
    blockers = _dedupe(item.get("source_blocker_id") for item in design_items)
    decision = _decision_from_design_items(
        p2_red_present=p2_red_present,
        p1_display_repair_present=p1_display_repair_present,
        runtime_repair_count=len(runtime_items),
        backlog_count=len(backlog_items),
        source_decision=_clean(source_summary.get("decision")),
    )
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_PROFILE_20260609,
        "source_p3_6_decision": _clean(source_summary.get("decision")),
        "source_ledger_item_count": _to_int(source_summary.get("item_count"), len(design_items)),
        "design_item_count": len(design_items),
        "runtime_repair_design_count": len(runtime_items),
        "backlog_defer_count": len(backlog_items),
        "first_runtime_repair_design_ids": _dedupe(item.get("design_profile_id") for item in runtime_items),
        "first_runtime_repair_blocker_ids": _dedupe(item.get("source_blocker_id") for item in runtime_items),
        "source_blocker_ids": blockers,
        "families": families,
        "max_first_targets": 2,
        "first_repair_targets_limited_to_max_two": len(design_items) <= 2 and len(runtime_items) <= 2,
        "p2_red_present": p2_red_present,
        "p2_red_blocks_p3_repair": p2_red_present,
        "p1_display_repair_present": p1_display_repair_present,
        "p3_runtime_repair_can_start": (not p2_red_present) and (not p1_display_repair_present) and bool(runtime_items),
        "decision": decision,
        "change_file_candidates_visible": all(bool(item.get("change_file_candidates")) for item in design_items) if design_items else False,
        "do_not_touch_files_visible": True,
        "forbidden_fix_paths_visible": True,
        "repair_steps_visible": all(bool(item.get("repair_steps")) for item in design_items) if design_items else False,
        "first_test_candidates_visible": all(bool(item.get("first_test_candidates")) for item in design_items) if design_items else False,
        "regression_subset_visible": True,
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": bool(source_summary.get("p3_1_baseline_case_matrix_used")) or bool(source_summary.get("case_count")),
        "p3_2_local_output_capture_used": bool(source_summary.get("p3_2_local_output_capture_used")),
        "p3_3_inventory_connection_used": bool(source_summary.get("p3_3_inventory_connection_used")),
        "p3_4_verdict_split_used": bool(source_summary.get("p3_4_verdict_split_used")),
        "p3_5_blind_qa_ratings_only_review_used": bool(source_summary.get("p3_5_blind_qa_ratings_only_review_used")),
        "p3_6_repair_priority_ledger_used": bool(design_items) or bool(source_summary),
        "p3_7_first_repair_design_applied": True,
        "runtime_change_applied": False,
        "implementation_change_applied": False,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
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
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(summary, source="p3_7.summary")
    return summary


def _public_summary(design: Mapping[str, Any]) -> dict[str, Any]:
    summary = dict(design.get("summary") or {})
    public_summary = dict(summary)
    public_summary["schema_version"] = PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609
    public_summary["version"] = PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609
    public_summary["source"] = PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SOURCE_20260609
    public_summary["first_repair_design_items"] = [
        {
            "priority": _to_int(item.get("priority"), 0),
            "source_blocker_id": _clean(item.get("source_blocker_id")),
            "source_blocker_category": _clean(item.get("source_blocker_category")),
            "design_profile_id": _clean(item.get("design_profile_id")),
            "design_action": _clean(item.get("design_action")),
            "selected_for_first_runtime_repair": item.get("selected_for_first_runtime_repair") is True,
            "case_count": _to_int(item.get("case_count"), 0),
            "families": _dedupe(item.get("families")),
            "sample_case_ids": _dedupe(item.get("sample_case_ids")),
            "target_layers": _dedupe(item.get("target_layers")),
            "change_file_candidates": _dedupe(item.get("change_file_candidates")),
            "do_not_touch_files": list(DO_NOT_TOUCH_FILES_20260609),
            "forbidden_fix_paths": list(FORBIDDEN_FIX_PATHS_20260609),
            "repair_steps": _dedupe(item.get("repair_steps")),
            "first_test_candidates": _dedupe(item.get("first_test_candidates")),
            "comment_text_body_included": False,
            "raw_input_included": False,
            "candidate_body_included": False,
            "runtime_repair_applied": False,
            "implementation_change_applied": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        for item in design.get("design_items") or []
    ]
    public_summary["do_not_touch_files"] = list(DO_NOT_TOUCH_FILES_20260609)
    public_summary["forbidden_fix_paths"] = list(FORBIDDEN_FIX_PATHS_20260609)
    public_summary["regression_subset"] = list(REGRESSION_SUBSET_20260609)
    public_summary["product_gate_ready"] = False
    public_summary["public_release_applied"] = False
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(public_summary, source="p3_7.public_summary")
    return public_summary


def build_product_readfeel_p3_first_repair_design_20260609(
    *,
    repair_priority_ledger: Mapping[str, Any] | None = None,
    ledger: Mapping[str, Any] | None = None,
    repair_priority_items: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    max_design_items: int = 2,
) -> dict[str, Any]:
    source_ledger = repair_priority_ledger if repair_priority_ledger is not None else ledger
    if isinstance(source_ledger, Mapping):
        assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(source_ledger)
    source_summary = dict((source_ledger or {}).get("summary") or (source_ledger or {}).get("public_summary") or {}) if isinstance(source_ledger, Mapping) else {}
    p2_red_present = bool(source_summary.get("p2_red_present")) or bool(source_summary.get("p2_red_blocks_p3_repair"))
    raw_items = _extract_ledger_items(repair_priority_items if repair_priority_items is not None else source_ledger)
    max_items = max(1, min(2, int(max_design_items or 2)))
    run_id_value = _safe_identifier(
        run_id or source_summary.get("run_id") or (raw_items[0].get("run_id") if raw_items else None),
        default="p3_7_first_repair_design",
        max_length=96,
    )
    design_items = [
        _design_item_from_ledger_item(
            item,
            p2_red_present=p2_red_present,
            priority=index,
            run_id=run_id_value,
        )
        for index, item in enumerate(raw_items[:max_items], start=1)
    ]
    summary = _summary(ledger=source_ledger, design_items=design_items, run_id=run_id_value)
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_PROFILE_20260609,
        "summary": summary,
        "design_items": design_items,
        "design_item_count": len(design_items),
        "do_not_touch_files": list(DO_NOT_TOUCH_FILES_20260609),
        "forbidden_fix_paths": list(FORBIDDEN_FIX_PATHS_20260609),
        "first_test_candidates": list(FIRST_REPAIR_TEST_CANDIDATES_20260609),
        "regression_subset": list(REGRESSION_SUBSET_20260609),
        "public_summary": {},
        "p3_7_first_repair_design_applied": True,
        "implementation_stage": "design_only",
        "runtime_change_applied": False,
        "implementation_change_applied": False,
        "first_repair_targets_limited_to_max_two": len(design_items) <= 2,
        "body_free_case_references_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
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
    payload["public_summary"] = _public_summary(payload)
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(payload)
    return payload


def build_product_readfeel_p3_first_repair_design_public_summary_20260609(
    design_or_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(design_or_ledger, Mapping) and design_or_ledger.get("schema_version") == PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609:
        summary = dict(design_or_ledger.get("public_summary") or {})
    else:
        summary = build_product_readfeel_p3_first_repair_design_20260609(
            repair_priority_ledger=design_or_ledger,
        )["public_summary"]
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(summary)
    return summary


def dump_product_readfeel_p3_first_repair_design_public_summary_20260609(
    design_or_ledger: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p3_first_repair_design_public_summary_20260609(design_or_ledger)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609",
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_ITEM_VERSION_20260609",
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609",
    "assert_product_readfeel_p3_first_repair_design_meta_only_20260609",
    "build_product_readfeel_p3_first_repair_design_20260609",
    "build_product_readfeel_p3_first_repair_design_public_summary_20260609",
    "dump_product_readfeel_p3_first_repair_design_public_summary_20260609",
]
