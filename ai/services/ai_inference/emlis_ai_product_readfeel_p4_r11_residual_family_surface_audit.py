# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-R11 residual-family current-only surface audit helpers.

The R11 helpers freeze the R10 H/I/J future-direction repair position, preserve
the R55 return-to-R54 decision, fix the residual family / focus-slice matrix,
select body-free case refs, and normalize material-route / surface-path audit
metadata.  R11-4/R11-5 may read local synthetic case bodies only long enough to
produce structural ids and counts; returned payloads remain body-free.

This module does not generate visible Emlis output, does not create R54/P5
actual review rows, does not change runtime routes/gates, and does not alter
RN/API/DB/public response contracts.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    assert_emlis_input_material_bundle_meta,
    build_emlis_input_material_bundle_meta,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    SURFACE_REQUIREMENT_SAFETY_BLOCKED,
    SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
    assert_public_surface_requirement_decision,
    assert_public_surface_requirement_decision_meta_only,
    resolve_public_surface_requirement,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_POSITIVE,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_POSITIVE_ONLY,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_SELF_DENIAL,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_UNCERTAINTY,
)
from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)

PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.contract_freeze.r10_r55_position.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_SCOPE_MATRIX_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.residual_family_scope_matrix.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_SCOPE_GROUP_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.residual_family_scope_group.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_SCOPE_SUMMARY_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.residual_family_scope_summary.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_PUBLIC_SUMMARY_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.contract_scope_public_summary.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_RESIDUAL_SURFACE_AUDIT_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.residual_family_surface_audit.v1"
)
PRODUCT_READFEEL_P4_R11_AUDIT_ROW_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.audit_row.v1"
)
PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.case_ref_selection.coverage_audit.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_SUMMARY_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.case_ref_selection.coverage_summary.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.material_route_audit.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_SUMMARY_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.material_route_audit_summary.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.surface_path_audit.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_SUMMARY_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.surface_path_audit_summary.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624: Final = (
    "cocolon.emlis.product_readfeel.p4_r11.residual_surface_audit_public_summary.20260624.v1"
)
PRODUCT_READFEEL_P4_R11_SOURCE_20260624: Final = (
    "Cocolon_EmlisAI_P4_R11_ResidualFamilyCurrentOnlySurfaceAudit_20260624"
)
PRODUCT_READFEEL_P4_R11_PHASE_20260624: Final = (
    "P4-R11_ResidualFamilyCurrentOnlySurfaceAudit"
)
PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624: Final = (
    "p4_r11_residual_family_current_only_surface_specificity_triage"
)

P4_R11_R0_STEP_REF_20260624: Final = "R11-0_Contract_Freeze_R10_R55_Position_Fixed"
P4_R11_R1_STEP_REF_20260624: Final = "R11-1_Residual_Family_Scope_Matrix_Freeze"
P4_R11_R2_STEP_REF_20260624: Final = "R11-2_Body_Free_Audit_Row_Meta_Only_Guard"
P4_R11_R3_STEP_REF_20260624: Final = "R11-3_Case_Ref_Selection_Coverage_Audit"
P4_R11_R4_STEP_REF_20260624: Final = "R11-4_Material_Route_Audit"
P4_R11_R5_STEP_REF_20260624: Final = "R11-5_Surface_Path_Audit"
P4_R11_R6_STEP_REF_20260624: Final = "R11-6_Surface_Specificity_Role_Audit"
P4_R11_R7_STEP_REF_20260624: Final = "R11-7_Verdict_Repair_Candidate_Classification"
P4_R11_R8_STEP_REF_20260624: Final = "R11-8_Summary_Decision_Handoff"
P4_R11_R9_STEP_REF_20260624: Final = "R11-9_Targeted_Tests"
P4_R11_R10_STEP_REF_20260624: Final = "R11-10_P4_Existing_Regression"
P4_R11_R11_STEP_REF_20260624: Final = "R11-11_HIJ_Runtime_Backfill_Regression"
P4_R11_R12_STEP_REF_20260624: Final = "R11-12_P3_Product_Read_Feel_Regression"
P4_R11_R13_STEP_REF_20260624: Final = "R11-13_R54_R55_Hold_Boundary_Regression"
P4_R11_R14_STEP_REF_20260624: Final = "R11-14_RN_Contract_Compile_Collect_Only"
P4_R11_R15_STEP_REF_20260624: Final = "R11-15_Result_Memo_Handoff"

P4_R11_ALL_STEP_REFS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
    P4_R11_R1_STEP_REF_20260624,
    P4_R11_R2_STEP_REF_20260624,
    P4_R11_R3_STEP_REF_20260624,
    P4_R11_R4_STEP_REF_20260624,
    P4_R11_R5_STEP_REF_20260624,
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)
P4_R11_R0_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
)
P4_R11_R0_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R1_STEP_REF_20260624,
    P4_R11_R2_STEP_REF_20260624,
    P4_R11_R3_STEP_REF_20260624,
    P4_R11_R4_STEP_REF_20260624,
    P4_R11_R5_STEP_REF_20260624,
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)
P4_R11_R1_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
    P4_R11_R1_STEP_REF_20260624,
)
P4_R11_R1_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R2_STEP_REF_20260624,
    P4_R11_R3_STEP_REF_20260624,
    P4_R11_R4_STEP_REF_20260624,
    P4_R11_R5_STEP_REF_20260624,
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)
P4_R11_R2_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
    P4_R11_R1_STEP_REF_20260624,
    P4_R11_R2_STEP_REF_20260624,
)
P4_R11_R2_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R3_STEP_REF_20260624,
    P4_R11_R4_STEP_REF_20260624,
    P4_R11_R5_STEP_REF_20260624,
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)
P4_R11_R3_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
    P4_R11_R1_STEP_REF_20260624,
    P4_R11_R2_STEP_REF_20260624,
    P4_R11_R3_STEP_REF_20260624,
)
P4_R11_R3_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R4_STEP_REF_20260624,
    P4_R11_R5_STEP_REF_20260624,
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)
P4_R11_R4_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
    P4_R11_R1_STEP_REF_20260624,
    P4_R11_R2_STEP_REF_20260624,
    P4_R11_R3_STEP_REF_20260624,
    P4_R11_R4_STEP_REF_20260624,
)
P4_R11_R4_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R5_STEP_REF_20260624,
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)
P4_R11_R5_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R0_STEP_REF_20260624,
    P4_R11_R1_STEP_REF_20260624,
    P4_R11_R2_STEP_REF_20260624,
    P4_R11_R3_STEP_REF_20260624,
    P4_R11_R4_STEP_REF_20260624,
    P4_R11_R5_STEP_REF_20260624,
)
P4_R11_R5_NOT_YET_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    P4_R11_R6_STEP_REF_20260624,
    P4_R11_R7_STEP_REF_20260624,
    P4_R11_R8_STEP_REF_20260624,
    P4_R11_R9_STEP_REF_20260624,
    P4_R11_R10_STEP_REF_20260624,
    P4_R11_R11_STEP_REF_20260624,
    P4_R11_R12_STEP_REF_20260624,
    P4_R11_R13_STEP_REF_20260624,
    P4_R11_R14_STEP_REF_20260624,
    P4_R11_R15_STEP_REF_20260624,
)

P4_R11_R10_CLOSED_RED_REF_20260624: Final = "P4-HIJ-FUTURE-DIRECTION-SURFACE-001"
P4_R11_R10_CLOSED_BY_REFS_20260624: Final[tuple[str, ...]] = (
    "R2_R3_eligible_future_direction_semantic_focus",
    "labelled_two_stage_surface_specificity",
)
P4_R11_R10_PROTECTED_BY_REFS_20260624: Final[tuple[str, ...]] = (
    "R0_R1_body_free_red_ledger_lineage_audit",
    "R4_test_only_generic_surface_guard",
    "R5_HIJ_submit_E2E",
    "R6_P0_P4_surrounding_regression",
    "R7_P3_P4_product_readfeel_regression",
    "R8_RN_contract_regression",
    "R9_compile_collect_only",
    "R10_result_memo_handoff",
)
P4_R11_R10_BLOCKER_KIND_REFS_20260624: Final[tuple[str, ...]] = (
    "current_only_surface_specificity_red",
    "eligible_future_direction_surface_specificity_missing",
    "generic_reception_surface",
    "material_surface_drop_at_labelled_two_stage_lane",
)

P4_R11_R55_DECISION_REF_20260624: Final = "R55_R52_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED"
P4_R11_R55_EXISTING_DECISION_EQUIVALENT_REF_20260624: Final = (
    "R52_RETURN_TO_R51_ACTUAL_REVIEW_REQUIRED"
)
P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624: Final = (
    "R54_actual_local_only_human_review_operation_required_before_R52_reintake"
)
P4_R11_R55_ACTUAL_REVIEW_EVIDENCE_GAP_REF_20260624: Final = "ACTUAL_REVIEW_EVIDENCE_MISSING"
P4_R11_REQUIRED_ACTUAL_REVIEW_CASE_COUNT_20260624: Final = 24

SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION: Final = "change_future_intention_transition"
SCOPE_GROUP_DAILY_POSITIVE_RECOVERY: Final = "daily_positive_recovery"
SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY: Final = "relationship_gratitude_recovery"
SCOPE_GROUP_LONG_MEANING_ARC: Final = "long_meaning_arc"
SCOPE_GROUP_STRUCTURE_QUESTION: Final = "structure_question"
SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER: Final = "self_denial_yellow_remainder"

P4_R11_TARGET_SCOPE_GROUP_IDS_20260624: Final[tuple[str, ...]] = (
    SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION,
    SCOPE_GROUP_DAILY_POSITIVE_RECOVERY,
    SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY,
    SCOPE_GROUP_LONG_MEANING_ARC,
    SCOPE_GROUP_STRUCTURE_QUESTION,
    SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER,
)
P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624: Final = 4
P4_R11_TARGET_SCOPE_GROUP_COUNT_20260624: Final = len(P4_R11_TARGET_SCOPE_GROUP_IDS_20260624)
P4_R11_TARGET_ROW_COUNT_20260624: Final = (
    P4_R11_TARGET_SCOPE_GROUP_COUNT_20260624 * P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624
)

P4_R11_TARGET_FOCUS_SLICE_IDS_20260624: Final[tuple[str, ...]] = (
    "future_direction",
    "recovered_energy",
    "positive_small_change",
    "relationship_gratitude",
    "relationship_recovery",
    "long_arc_multi_core",
    "structure_question_state_answer",
    "self_denial_non_amplification",
)

P4_R11_SCOPE_GROUP_DEFINITIONS_20260624: Final[tuple[dict[str, Any], ...]] = (
    {
        "scope_group_id": SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION,
        "priority_band": "P0_highest",
        "existing_runtime_family_ids": (
            FAMILY_DAILY_POSITIVE,
            FAMILY_UNCERTAINTY,
            FAMILY_SELF_UNDERSTANDING_FOLLOW,
        ),
        "residual_focus_slice_ids": ("future_direction", "recovered_energy", "transition"),
        "candidate_coverage_slice_ids": (),
        "required_surface_role_ids": (
            "current_change_nucleus_visible",
            "future_direction_visible",
            "recovered_energy_or_transition_visible",
            "self_possibility_without_prediction_visible",
            "value_preservation_without_advice_visible",
        ),
        "scope_reason_refs": (
            "hij_future_direction_red_adjacent_residual_slice",
            "current_change_material_can_collapse_to_generic_surface",
        ),
        "residual_focus_slice_only": True,
    },
    {
        "scope_group_id": SCOPE_GROUP_DAILY_POSITIVE_RECOVERY,
        "priority_band": "P1_high",
        "existing_runtime_family_ids": (FAMILY_DAILY_POSITIVE, FAMILY_POSITIVE_ONLY),
        "residual_focus_slice_ids": ("positive_small_change", "recovered_energy"),
        "candidate_coverage_slice_ids": (),
        "required_surface_role_ids": (
            "positive_event_or_small_change_visible",
            "positive_temperature_kept",
            "observation_not_overweighted",
            "reception_warmth_present",
            "no_generic_praise_only",
        ),
        "scope_reason_refs": (
            "positive_or_recovery_temperature_can_cool",
            "generic_praise_only_must_not_replace_current_nucleus",
        ),
        "residual_focus_slice_only": False,
    },
    {
        "scope_group_id": SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY,
        "priority_band": "P1_high",
        "existing_runtime_family_ids": (
            FAMILY_RELATIONSHIP_BOUNDARY,
            FAMILY_DAILY_POSITIVE,
            FAMILY_POSITIVE_ONLY,
        ),
        "residual_focus_slice_ids": ("relationship_gratitude", "relationship_recovery"),
        "candidate_coverage_slice_ids": (),
        "required_surface_role_ids": (
            "relationship_or_gratitude_nucleus_visible",
            "user_side_wish_or_reaction_visible",
            "no_other_person_intent_claim",
            "no_relationship_permanence_claim",
            "recovery_or_thanks_temperature_kept",
        ),
        "scope_reason_refs": (
            "relationship_gratitude_must_not_become_target_judgement",
            "recovery_temperature_must_not_flatten_to_generic_comfort",
        ),
        "residual_focus_slice_only": False,
    },
    {
        "scope_group_id": SCOPE_GROUP_LONG_MEANING_ARC,
        "priority_band": "P2_medium",
        "existing_runtime_family_ids": (FAMILY_LONG_MEANING_ARC,),
        "residual_focus_slice_ids": ("long_arc_multi_core",),
        "candidate_coverage_slice_ids": (),
        "required_surface_role_ids": (
            "multiple_current_nuclei_visible",
            "relation_between_nuclei_visible",
            "not_summary_only",
            "observation_section_has_structure",
            "reception_does_not_crush_complexity",
        ),
        "scope_reason_refs": (
            "long_input_must_not_crush_to_short_summary",
            "history_line_must_not_mask_current_arc",
        ),
        "residual_focus_slice_only": False,
    },
    {
        "scope_group_id": SCOPE_GROUP_STRUCTURE_QUESTION,
        "priority_band": "P2_medium",
        "existing_runtime_family_ids": (FAMILY_STRUCTURE_QUESTION,),
        "residual_focus_slice_ids": ("structure_question_state_answer",),
        "candidate_coverage_slice_ids": (),
        "required_surface_role_ids": (
            "question_context_visible",
            "state_answer_attempt_visible",
            "comfort_not_primary",
            "observation_ratio_high_enough",
            "no_question_escape",
        ),
        "scope_reason_refs": (
            "structure_question_must_not_escape_to_comfort",
            "question_context_should_be_answered_as_state_observation",
        ),
        "residual_focus_slice_only": False,
    },
    {
        "scope_group_id": SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER,
        "priority_band": "P2_medium",
        "existing_runtime_family_ids": (FAMILY_SELF_DENIAL,),
        "residual_focus_slice_ids": ("self_denial_non_amplification",),
        "candidate_coverage_slice_ids": (),
        "required_surface_role_ids": (
            "self_denial_not_accepted_as_fact",
            "load_or_pain_behind_denial_visible",
            "no_personality_claim",
            "no_absolute_personality_praise",
            "safety_boundary_if_needed",
        ),
        "scope_reason_refs": (
            "self_denial_yellow_remainder_requires_non_amplification_audit",
            "identity_echo_must_not_be_treated_as_readfeel_pass",
        ),
        "residual_focus_slice_only": False,
    },
)


P4_R11_CASE_ORIGIN_P3_BASELINE_20260624: Final = "p3_baseline_public_safe_index"
P4_R11_CASE_ORIGIN_P4_TARGET_SELECTION_20260624: Final = "p4_target_selection"
P4_R11_CASE_ORIGIN_P4_HIJ_HANDOFF_20260624: Final = "p4_runtime_backfill_hij_handoff"
P4_R11_CASE_ORIGIN_LOCAL_SYNTHETIC_REF_20260624: Final = "local_only_synthetic_case_ref"
P4_R11_CASE_ORIGIN_UNKNOWN_20260624: Final = "unknown"
P4_R11_ALLOWED_CASE_ORIGINS_20260624: Final[frozenset[str]] = frozenset(
    {
        P4_R11_CASE_ORIGIN_P3_BASELINE_20260624,
        P4_R11_CASE_ORIGIN_P4_TARGET_SELECTION_20260624,
        P4_R11_CASE_ORIGIN_P4_HIJ_HANDOFF_20260624,
        P4_R11_CASE_ORIGIN_LOCAL_SYNTHETIC_REF_20260624,
        P4_R11_CASE_ORIGIN_UNKNOWN_20260624,
    }
)
P4_R11_MATERIAL_QUALITY_SOURCE_UNAVAILABLE_20260624: Final = "source_unavailable"
P4_R11_MATERIAL_QUALITY_UNKNOWN_20260624: Final = "unknown"
P4_R11_ALLOWED_MATERIAL_QUALITIES_20260624: Final[tuple[str, ...]] = (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    P4_R11_MATERIAL_QUALITY_SOURCE_UNAVAILABLE_20260624,
    P4_R11_MATERIAL_QUALITY_UNKNOWN_20260624,
)
P4_R11_SURFACE_ROUTE_KINDS_20260624: Final[tuple[str, ...]] = (
    "complete_initial_surface_recomposition",
    "labelled_two_stage_surface_recomposition",
    "limited_grounding_reception_surface",
    "low_information_observation",
    "normal_observation_rebuild",
    "history_line_candidate",
    "unknown",
)
P4_R11_PRIORITY_BANDS_20260624: Final[tuple[str, ...]] = (
    "P0_highest",
    "P1_high",
    "P2_medium",
    "P3_boundary",
)
P4_R11_ALLOWED_PRIORITY_BANDS_20260624: Final[frozenset[str]] = frozenset(P4_R11_PRIORITY_BANDS_20260624)
P4_R11_CASE_SELECTION_PREFERRED_FAMILY_ORDER_20260624: Final[dict[str, tuple[str, ...]]] = {
    SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION: (
        FAMILY_UNCERTAINTY,
        FAMILY_SELF_UNDERSTANDING_FOLLOW,
        FAMILY_DAILY_POSITIVE,
    ),
    SCOPE_GROUP_DAILY_POSITIVE_RECOVERY: (FAMILY_DAILY_POSITIVE, FAMILY_POSITIVE_ONLY),
    SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY: (
        FAMILY_RELATIONSHIP_BOUNDARY,
        FAMILY_DAILY_POSITIVE,
        FAMILY_POSITIVE_ONLY,
    ),
    SCOPE_GROUP_LONG_MEANING_ARC: (FAMILY_LONG_MEANING_ARC,),
    SCOPE_GROUP_STRUCTURE_QUESTION: (FAMILY_STRUCTURE_QUESTION,),
    SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER: (FAMILY_SELF_DENIAL,),
}

_FORBIDDEN_BODY_KEYS_20260624: Final[frozenset[str]] = frozenset(
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
        "visible_text",
        "visibleText",
        "realized_text",
        "realizedText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "question_text",
        "draft_question_text",
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "blind_qa_free_text",
        "stdout",
        "stderr",
        "raw_test_output",
        "test_output",
        "traceback",
        "traceback_body",
        "command_output",
        "terminal_output",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS_20260624: Final[frozenset[str]] = frozenset(
    {
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "public_release_applied",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "product_quality_released",
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
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "runtime_changed_here",
        "runtime_repair_applied",
        "implementation_change_applied",
        "p4_runtime_tuning_applied",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "schema_file_materialized",
        "json_schema_file_materialized",
        "api_db_rn_response_key_changed_here",
        "question_implementation_started_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_trigger_logic_implemented",
        "question_storage_schema_implemented",
        "question_answer_persistence_implemented",
        "question_plan_guard_implemented",
        "p8_question_implementation_spec_finalized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_run_here",
        "disposal_receipt_materialized_here",
        "actual_review_evidence_complete",
        "actual_review_evidence_claimed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_included",
        "reviewer_free_text_included",
        "question_text_included",
        "history_raw_text_included",
        "raw_test_output_included",
        "command_output_included",
        "terminal_output_included",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "external_ai_used",
        "local_llm_used",
        "runtime_family_rename_applied",
        "new_runtime_family_constant_added",
        "case_ref_selection_performed_here",
        "actual_audit_rows_created_here",
    }
)
_AUDIT_FORBIDDEN_TRUE_FLAGS_20260624: Final[frozenset[str]] = frozenset(
    flag for flag in _FORBIDDEN_TRUE_FLAGS_20260624 if flag != "case_ref_selection_performed_here"
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 160) -> str:
    text = _clean(value) or default
    chars = [ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-" for ch in text[:max_length]]
    return "".join(chars).strip("-") or default


def _listify(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.keys())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_BODY_KEYS_20260624:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_key(child) for child in value)
    return False


def _forbidden_true_flag_path(
    value: Any,
    *,
    path: str = "payload",
    forbidden_flags: frozenset[str] = _FORBIDDEN_TRUE_FLAGS_20260624,
) -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden_flags and child is True:
                return child_path
            nested = _forbidden_true_flag_path(child, path=child_path, forbidden_flags=forbidden_flags)
            if nested:
                return nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(
                child,
                path=f"{path}[{index}]",
                forbidden_flags=forbidden_flags,
            )
            if nested:
                return nested
    return None


def assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "p4_r11_contract_scope",
) -> None:
    """Reject body-bearing or contract-mutating R11-0/R11-1 materials."""

    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain raw input, output, history, question, review, or log body keys")
    flag_path = _forbidden_true_flag_path(payload)
    if flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {flag_path}")
    if isinstance(payload, Mapping):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for index, item in enumerate(payload):
            if not isinstance(item, Mapping):
                raise ValueError(f"{source}[{index}] must be a mapping")
            assert_emlis_ai_product_quality_contract_freeze_meta_only(
                item, source=f"{source}.contract_freeze[{index}]"
            )


def _public_contract_flags() -> dict[str, bool]:
    return {
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "gate_relaxed": False,
        "api_db_rn_response_key_changed_here": False,
    }


def _runtime_no_touch_flags() -> dict[str, bool]:
    return {
        "runtime_changed_here": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "schema_file_materialized": False,
        "json_schema_file_materialized": False,
        "runtime_family_rename_applied": False,
        "new_runtime_family_constant_added": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
        "input_specific_template_added": False,
        "exact_comment_text_required": False,
        "exact_comment_text_locked": False,
    }


def _p5_p6_p8_release_hold_flags() -> dict[str, bool]:
    return {
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "product_quality_released": False,
    }


def _question_no_touch_flags() -> dict[str, bool]:
    return {
        "question_implementation_started_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_trigger_logic_implemented": False,
        "question_storage_schema_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_plan_guard_implemented": False,
        "p8_question_implementation_spec_finalized_here": False,
    }


def _actual_review_no_touch_flags() -> dict[str, bool]:
    return {
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_run_here": False,
        "disposal_receipt_materialized_here": False,
        "actual_review_evidence_complete": False,
        "actual_review_evidence_claimed": False,
    }


def _body_boundary() -> dict[str, bool]:
    return {
        "body_free": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "surface_text_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _all_boundary_flags() -> dict[str, Any]:
    return {
        "public_contract_flags": _public_contract_flags(),
        "runtime_no_touch_flags": _runtime_no_touch_flags(),
        "p5_p6_p8_release_hold_flags": _p5_p6_p8_release_hold_flags(),
        "question_no_touch_flags": _question_no_touch_flags(),
        "actual_review_no_touch_flags": _actual_review_no_touch_flags(),
        "body_boundary": _body_boundary(),
        **_public_contract_flags(),
        **_runtime_no_touch_flags(),
        **_p5_p6_p8_release_hold_flags(),
        **_question_no_touch_flags(),
        **_actual_review_no_touch_flags(),
        **_body_boundary(),
    }


def _extract_r55_summary(r55_final_summary: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(r55_final_summary, Mapping):
        return {
            "r55_decision_ref": P4_R11_R55_DECISION_REF_20260624,
            "r52_existing_decision_equivalent": P4_R11_R55_EXISTING_DECISION_EQUIVALENT_REF_20260624,
            "next_required_step": P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624,
            "actual_review_evidence_complete": False,
            "actual_review_evidence_gap_status_ref": P4_R11_R55_ACTUAL_REVIEW_EVIDENCE_GAP_REF_20260624,
            "required_case_count": P4_R11_REQUIRED_ACTUAL_REVIEW_CASE_COUNT_20260624,
            "rating_row_count": 0,
            "question_observation_row_count": 0,
            "disposal_verified": False,
            "p6_hold": True,
            "p8_hold": True,
            "release_hold": True,
            "p6_limited_human_readfeel_start_allowed": False,
            "p8_start_allowed": False,
            "p7_complete": False,
            "release_allowed": False,
        }

    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(
        r55_final_summary,
        source="p4_r11.r55_final_summary_source",
    )
    summary = {
        "r55_decision_ref": _clean(r55_final_summary.get("r55_decision_ref")),
        "r52_existing_decision_equivalent": _clean(r55_final_summary.get("r52_existing_decision_equivalent")),
        "next_required_step": _clean(r55_final_summary.get("next_required_step")),
        "actual_review_evidence_complete": r55_final_summary.get("actual_review_evidence_complete") is True,
        "actual_review_evidence_gap_status_ref": _clean(
            r55_final_summary.get("actual_review_evidence_gap_status_ref")
        ),
        "required_case_count": int(r55_final_summary.get("required_case_count") or 0),
        "rating_row_count": int(r55_final_summary.get("rating_row_count") or 0),
        "question_observation_row_count": int(r55_final_summary.get("question_observation_row_count") or 0),
        "disposal_verified": r55_final_summary.get("disposal_verified") is True,
        "p6_hold": r55_final_summary.get("p6_hold") is True,
        "p8_hold": r55_final_summary.get("p8_hold") is True,
        "release_hold": r55_final_summary.get("release_hold") is True,
        "p6_limited_human_readfeel_start_allowed": r55_final_summary.get(
            "p6_limited_human_readfeel_start_allowed"
        ) is True,
        "p8_start_allowed": r55_final_summary.get("p8_start_allowed") is True,
        "p7_complete": r55_final_summary.get("p7_complete") is True,
        "release_allowed": r55_final_summary.get("release_allowed") is True,
    }
    _assert_r55_position(summary)
    return summary


def _assert_r55_position(summary: Mapping[str, Any]) -> None:
    if summary.get("r55_decision_ref") != P4_R11_R55_DECISION_REF_20260624:
        raise ValueError("P4-R11 R11-0 requires the R55 return-to-R54 decision to stay fixed")
    if summary.get("r52_existing_decision_equivalent") not in {
        "",
        P4_R11_R55_EXISTING_DECISION_EQUIVALENT_REF_20260624,
    }:
        raise ValueError("P4-R11 R11-0 must not rewrite the R52 equivalent decision")
    if summary.get("next_required_step") != P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624:
        raise ValueError("P4-R11 R11-0 must keep the next required step at R54 actual review")
    if summary.get("actual_review_evidence_complete") is not False:
        raise ValueError("P4-R11 R11-0 must not claim actual review evidence complete")
    if int(summary.get("rating_row_count") or 0) != 0:
        raise ValueError("P4-R11 R11-0 must not create R54 rating rows")
    if int(summary.get("question_observation_row_count") or 0) != 0:
        raise ValueError("P4-R11 R11-0 must not create question observation rows")
    if summary.get("disposal_verified") is not False:
        raise ValueError("P4-R11 R11-0 must not claim disposal verified")
    for key in (
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if summary.get(key) is not False:
            raise ValueError(f"P4-R11 R11-0 must keep {key}=False")


def _family_from_index_case(case: Mapping[str, Any]) -> str:
    return _clean(case.get("family") or case.get("product_readfeel_family"))


def _coverage_slices_from_index_case(case: Mapping[str, Any]) -> list[str]:
    return _dedupe(case.get("coverage_slices"))


def _case_ref_from_index_case(case: Mapping[str, Any]) -> str:
    return _safe_identifier(case.get("case_id") or case.get("case_ref_id"), default="")


def _potential_case_ref_counts(
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None,
) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
    if not isinstance(baseline_public_safe_index, Sequence) or isinstance(
        baseline_public_safe_index, (str, bytes, bytearray)
    ):
        return {}, {}, {}
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(
        baseline_public_safe_index,
        source="p4_r11.source_baseline_public_safe_index",
    )
    family_counts: Counter[str] = Counter()
    slice_counts: Counter[str] = Counter()
    group_counts: dict[str, int] = {}
    seen_by_group: dict[str, set[str]] = {group_id: set() for group_id in P4_R11_TARGET_SCOPE_GROUP_IDS_20260624}
    definitions_by_id = {
        str(definition["scope_group_id"]): definition for definition in P4_R11_SCOPE_GROUP_DEFINITIONS_20260624
    }
    for item in baseline_public_safe_index:
        if not isinstance(item, Mapping):
            continue
        case_ref = _case_ref_from_index_case(item)
        if not case_ref:
            continue
        family = _family_from_index_case(item)
        slices = _coverage_slices_from_index_case(item)
        if family:
            family_counts[family] += 1
        slice_counts.update(slices)
        for group_id, definition in definitions_by_id.items():
            # R11-1 freezes the residual scope matrix; it must not perform the
            # later R11-3 case-ref selection by broad coverage-slice matching.
            # Candidate coverage slices are recorded as hints, but minimum
            # availability is counted from existing runtime-family refs only so
            # a long_arc/structure group cannot be accidentally satisfied by
            # unrelated standard_state_answer cases.
            existing_families = set(definition.get("existing_runtime_family_ids") or ())
            if family in existing_families:
                seen_by_group[group_id].add(case_ref)
    for group_id in P4_R11_TARGET_SCOPE_GROUP_IDS_20260624:
        group_counts[group_id] = len(seen_by_group[group_id])
    return dict(family_counts), dict(slice_counts), group_counts


def build_product_readfeel_p4_r11_contract_freeze_20260624(
    *,
    r55_final_summary: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build R11-0 contract material without promoting P5/P6/P8/release."""

    run_id_value = _safe_identifier(run_id or "p4_r11_r0_contract_freeze", default="p4_r11_r0_contract_freeze")
    r55_summary = _extract_r55_summary(r55_final_summary)
    material = {
        "schema_version": PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R0_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "contract_freeze_fixed": True,
        "p4_r11_contract_freeze_fixed": True,
        "p4_r11_current_only_audit_position_fixed": True,
        "p4_r11_runtime_no_touch_step": True,
        "r10_position_status_ref": "R10_CLOSED_REPAIR_PRESERVED_AS_CURRENT_INPUT_SURFACE_PRECEDENT",
        "r10_closed_red_ref": P4_R11_R10_CLOSED_RED_REF_20260624,
        "r10_closed_red_reopened_here": False,
        "r10_closed_by_refs": list(P4_R11_R10_CLOSED_BY_REFS_20260624),
        "r10_protected_by_refs": list(P4_R11_R10_PROTECTED_BY_REFS_20260624),
        "r10_blocker_kind_refs": list(P4_R11_R10_BLOCKER_KIND_REFS_20260624),
        "r55_decision_ref": r55_summary["r55_decision_ref"],
        "r52_existing_decision_equivalent": r55_summary["r52_existing_decision_equivalent"]
        or P4_R11_R55_EXISTING_DECISION_EQUIVALENT_REF_20260624,
        "r55_next_required_step": r55_summary["next_required_step"],
        "next_required_step": r55_summary["next_required_step"],
        "r55_decision_preserved": True,
        "r55_position_preserved": True,
        "r55_not_replaced_by_p4_r11": True,
        "actual_review_evidence_complete": False,
        "actual_review_evidence_gap_status_ref": r55_summary.get("actual_review_evidence_gap_status_ref")
        or P4_R11_R55_ACTUAL_REVIEW_EVIDENCE_GAP_REF_20260624,
        "required_case_count": P4_R11_REQUIRED_ACTUAL_REVIEW_CASE_COUNT_20260624,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "p6_hold": True,
        "p8_hold": True,
        "release_hold": True,
        "implemented_steps": list(P4_R11_R0_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R0_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R1_STEP_REF_20260624,
        "scope_matrix_fixed_here": False,
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(material, source="p4_r11.r0_contract_freeze")
    return material


def _scope_group_row(
    definition: Mapping[str, Any],
    *,
    candidate_case_ref_count: int,
    run_id: str,
) -> dict[str, Any]:
    scope_group_id = _clean(definition.get("scope_group_id"))
    below_minimum = candidate_case_ref_count < P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624
    row = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SCOPE_GROUP_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SCOPE_GROUP_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R1_STEP_REF_20260624,
        "run_id": run_id,
        "scope_group_id": scope_group_id,
        "priority_band": _clean(definition.get("priority_band")),
        "existing_runtime_family_ids": _dedupe(definition.get("existing_runtime_family_ids")),
        "residual_focus_slice_ids": _dedupe(definition.get("residual_focus_slice_ids")),
        "candidate_coverage_slice_ids": _dedupe(definition.get("candidate_coverage_slice_ids")),
        "required_surface_role_ids": _dedupe(definition.get("required_surface_role_ids")),
        "scope_reason_refs": _dedupe(definition.get("scope_reason_refs")),
        "minimum_case_ref_count": P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624,
        "candidate_case_ref_count": int(candidate_case_ref_count),
        "coverage_status": "insufficient_public_safe_case_refs" if below_minimum else "candidate_refs_available",
        "coverage_below_minimum": below_minimum,
        "residual_focus_slice_only": definition.get("residual_focus_slice_only") is True,
        "runtime_family_rename_applied": False,
        "new_runtime_family_constant_added": False,
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        **_runtime_no_touch_flags(),
        **_body_boundary(),
    }
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(row, source=f"p4_r11.scope_group.{scope_group_id}")
    return row


def _build_scope_summary(
    *,
    scope_groups: Sequence[Mapping[str, Any]],
    family_counts: Mapping[str, int],
    coverage_slice_counts: Mapping[str, int],
    run_id: str,
    contract_freeze: Mapping[str, Any],
) -> dict[str, Any]:
    insufficient_group_ids = [
        _clean(group.get("scope_group_id"))
        for group in scope_groups
        if group.get("coverage_below_minimum") is True
    ]
    coverage_status = "complete" if not insufficient_group_ids else "insufficient_public_safe_case_refs"
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SCOPE_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SCOPE_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R1_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id,
        "r10_closed_red_ref": P4_R11_R10_CLOSED_RED_REF_20260624,
        "r10_closed_red_reopened_here": False,
        "r55_decision_ref": contract_freeze.get("r55_decision_ref") or P4_R11_R55_DECISION_REF_20260624,
        "r55_next_required_step": contract_freeze.get("r55_next_required_step")
        or P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624,
        "r55_decision_preserved": True,
        "target_scope_group_ids": list(P4_R11_TARGET_SCOPE_GROUP_IDS_20260624),
        "target_scope_group_count": P4_R11_TARGET_SCOPE_GROUP_COUNT_20260624,
        "minimum_case_refs_per_scope_group": P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624,
        "target_row_count": P4_R11_TARGET_ROW_COUNT_20260624,
        "target_focus_slice_ids": list(P4_R11_TARGET_FOCUS_SLICE_IDS_20260624),
        "coverage_status": coverage_status,
        "insufficient_scope_group_ids": insufficient_group_ids,
        "insufficient_scope_group_count": len(insufficient_group_ids),
        "candidate_family_counts": dict(sorted(family_counts.items())),
        "candidate_coverage_slice_counts": dict(sorted(coverage_slice_counts.items())),
        "p4_r11_scope_matrix_fixed": True,
        "case_coverage_ready_for_r11_3": coverage_status == "complete",
        "scope_matrix_only": True,
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        "p4_r11_does_not_replace_r54_actual_review": True,
        "p4_r11_audit_rows_not_r54_rating_rows": True,
        "p4_r11_audit_rows_not_question_observation_rows": True,
        "change_future_intention_transition_is_runtime_family": False,
        "runtime_family_rename_applied": False,
        "new_runtime_family_constant_added": False,
        "implemented_steps": list(P4_R11_R1_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R1_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R2_STEP_REF_20260624,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(summary, source="p4_r11.r1_scope_summary")
    return summary


def build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
    *,
    contract_freeze: Mapping[str, Any] | None = None,
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the R11-1 residual family / focus-slice scope matrix.

    Passing the P3 public-safe baseline index lets this helper record whether
    there are enough candidate refs for the later R11-3 selection step.  It does
    not select or retain actual cases here.
    """

    run_id_value = _safe_identifier(run_id or "p4_r11_r1_scope_matrix", default="p4_r11_r1_scope_matrix")
    freeze = dict(contract_freeze or build_product_readfeel_p4_r11_contract_freeze_20260624(run_id=run_id_value))
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(freeze, source="p4_r11.r1_contract_source")
    if freeze.get("r55_decision_ref") != P4_R11_R55_DECISION_REF_20260624:
        raise ValueError("P4-R11 R11-1 requires the R11-0 R55 decision freeze")
    if freeze.get("r10_closed_red_ref") != P4_R11_R10_CLOSED_RED_REF_20260624:
        raise ValueError("P4-R11 R11-1 requires the R10 H/I/J red closure freeze")
    for key in ("p8_start_allowed", "release_allowed", "runtime_changed_here"):
        if freeze.get(key) is not False:
            raise ValueError(f"P4-R11 R11-1 requires {key}=False from R11-0")

    family_counts, coverage_slice_counts, group_counts = _potential_case_ref_counts(baseline_public_safe_index)
    scope_groups = [
        _scope_group_row(
            definition,
            candidate_case_ref_count=int(group_counts.get(_clean(definition.get("scope_group_id")), 0)),
            run_id=run_id_value,
        )
        for definition in P4_R11_SCOPE_GROUP_DEFINITIONS_20260624
    ]
    summary = _build_scope_summary(
        scope_groups=scope_groups,
        family_counts=family_counts,
        coverage_slice_counts=coverage_slice_counts,
        run_id=run_id_value,
        contract_freeze=freeze,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SCOPE_MATRIX_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SCOPE_MATRIX_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R1_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "contract_freeze_schema_version": PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624,
        "contract_freeze_ref": _safe_identifier(freeze.get("run_id"), default="p4_r11_r0_contract_freeze"),
        "summary": summary,
        "scope_groups": scope_groups,
        "scope_matrix_fixed_here": True,
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        "implemented_steps": list(P4_R11_R1_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R1_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R2_STEP_REF_20260624,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(payload, source="p4_r11.r1_scope_matrix")
    return payload


def assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "p4_r11_residual_surface_audit",
) -> None:
    """Reject body-bearing or contract-mutating R11-2/R11-3 materials."""

    if payload is None:
        raise ValueError(f"{source} must not be None")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain raw input, output, history, question, review, or log body keys")
    flag_path = _forbidden_true_flag_path(payload, forbidden_flags=_AUDIT_FORBIDDEN_TRUE_FLAGS_20260624)
    if flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {flag_path}")
    if isinstance(payload, Mapping):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")
    elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        for index, item in enumerate(payload):
            if not isinstance(item, Mapping):
                raise ValueError(f"{source}[{index}] must be a mapping")
            assert_emlis_ai_product_quality_contract_freeze_meta_only(
                item, source=f"{source}.contract_freeze[{index}]"
            )


def _pending_audit_status_flags() -> dict[str, Any]:
    return {
        "material_route_audit_status": "not_run_r11_4",
        "surface_path_audit_status": "not_run_r11_5",
        "surface_specificity_role_audit_status": "not_run_r11_6",
        "verdict_classification_status": "not_run_r11_7",
        "decision_handoff_status": "not_run_r11_8",
        "material_route_audit_performed_here": False,
        "surface_path_audit_performed_here": False,
        "surface_specificity_role_audit_performed_here": False,
        "verdict_classification_performed_here": False,
        "decision_handoff_performed_here": False,
    }


def _p5_p8_escape_boundary_pending() -> dict[str, Any]:
    return {
        "p5_masking_forbidden": True,
        "p8_question_escape_forbidden": True,
        "current_only_repair_required_before_history_or_question": False,
        "p5_p8_escape_boundary_status": "scope_boundary_only_not_r11_7_verdict",
    }




def _r11_4_pending_after_material_flags() -> dict[str, Any]:
    return {
        "material_route_audit_status": "audited_r11_4",
        "surface_path_audit_status": "not_run_r11_5",
        "surface_specificity_role_audit_status": "not_run_r11_6",
        "verdict_classification_status": "not_run_r11_7",
        "decision_handoff_status": "not_run_r11_8",
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": False,
        "surface_specificity_role_audit_performed_here": False,
        "verdict_classification_performed_here": False,
        "decision_handoff_performed_here": False,
    }


def _r11_5_pending_after_surface_path_flags() -> dict[str, Any]:
    return {
        "material_route_audit_status": "audited_r11_4",
        "surface_path_audit_status": "audited_r11_5",
        "surface_specificity_role_audit_status": "not_run_r11_6",
        "verdict_classification_status": "not_run_r11_7",
        "decision_handoff_status": "not_run_r11_8",
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": True,
        "surface_specificity_role_audit_performed_here": False,
        "verdict_classification_performed_here": False,
        "decision_handoff_performed_here": False,
    }


def _case_ref_from_local_case(local_case: Mapping[str, Any]) -> str:
    return _safe_identifier(local_case.get("case_ref_id") or local_case.get("case_id"), default="")


def _local_case_map_for_r11_material_audit(
    local_baseline_cases: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Mapping[str, Any]]:
    """Map local body-bearing cases by id without returning any body material."""

    if not isinstance(local_baseline_cases, Sequence) or isinstance(local_baseline_cases, (str, bytes, bytearray)):
        return {}
    mapped: dict[str, Mapping[str, Any]] = {}
    for local_case in local_baseline_cases:
        if not isinstance(local_case, Mapping):
            continue
        case_ref = _case_ref_from_local_case(local_case)
        if case_ref:
            mapped[case_ref] = local_case
    return mapped


def _current_input_from_local_case(local_case: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(local_case, Mapping):
        return {}
    current = local_case.get("current_input")
    return current if isinstance(current, Mapping) else {}


def _semantic_focus_ids_from_material(
    *,
    residual_family_id: str,
    residual_focus_slice_ids: Iterable[Any] | Any | None,
    semantic_material_ids: Iterable[Any] | Any | None,
    selected_coverage_slice_ids: Iterable[Any] | Any | None = None,
) -> list[str]:
    material_ids = set(_dedupe(semantic_material_ids))
    selected_slices = set(_dedupe(selected_coverage_slice_ids))
    explicit_focus = _dedupe(residual_focus_slice_ids)
    focus: list[str] = []

    def add(value: str) -> None:
        if value and value not in focus:
            focus.append(value)

    for material_id in material_ids:
        if material_id == "recovered_energy":
            add("recovered_energy")
        elif material_id == "future_intention":
            add("future_direction")
        elif material_id in {"small_change_preservation", "comparison_baseline_shift"}:
            add("positive_small_change")
        elif material_id in {"gratitude_or_return_intent", "support_from_other", "support_received_material"}:
            add("relationship_gratitude")
        elif material_id in {"relationship_end", "relationship_material", "relationship_category_direction", "boundary_or_transition"}:
            add("relationship_recovery")
        elif material_id in {"self_observation", "self_understanding_learning", "value_or_self_understanding_material"}:
            add("structure_question_state_answer")
        elif material_id == "value_preservation":
            add("future_direction")

    if residual_family_id == SCOPE_GROUP_LONG_MEANING_ARC:
        add("long_arc_multi_core")
    if residual_family_id == SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER:
        add("self_denial_non_amplification")
    if "standard_state_answer" in selected_slices and residual_family_id == SCOPE_GROUP_STRUCTURE_QUESTION:
        add("structure_question_state_answer")
    if not focus:
        for item in explicit_focus:
            add(item)
    return [item for item in focus if not explicit_focus or item in set(explicit_focus)] or explicit_focus


def _body_free_material_audit_from_meta(
    *,
    row: Mapping[str, Any],
    material_meta: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(material_meta, Mapping):
        audit = {
            "material_quality": P4_R11_MATERIAL_QUALITY_SOURCE_UNAVAILABLE_20260624,
            "visible_material_slot_ids": [],
            "visible_material_slots": [],
            "semantic_material_ids": [],
            "semantic_focus_ids": _dedupe(row.get("residual_focus_slice_ids")),
            "semantic_material_count": 0,
            "unknown_slot_ids": [],
            "unknown_slot_count": 0,
            "current_only_material_available": False,
            "material_source_available": False,
            "material_route_audit_status": "source_unavailable_r11_4",
            "material_route_audit_performed_here": True,
            "material_quality_forced_to_eligible": False,
            "low_information_or_limited_grounding_upgraded_here": False,
            "raw_memo_or_action_retained_here": False,
            "body_free": True,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
        }
        return audit

    assert_emlis_input_material_bundle_meta(material_meta)
    material_quality = _clean(material_meta.get("material_quality")) or P4_R11_MATERIAL_QUALITY_UNKNOWN_20260624
    visible_slots = _dedupe(material_meta.get("visible_material_slots"))
    unknown_slots = _dedupe(material_meta.get("unknown_slots"))
    semantic_material_ids = _dedupe(
        material_meta.get("relation_material_ids") or material_meta.get("generic_relation_material_ids")
    )
    semantic_focus_ids = _semantic_focus_ids_from_material(
        residual_family_id=_clean(row.get("residual_family_id")),
        residual_focus_slice_ids=row.get("residual_focus_slice_ids"),
        semantic_material_ids=semantic_material_ids,
        selected_coverage_slice_ids=row.get("selected_coverage_slice_ids"),
    )
    current_only_available = bool(
        material_quality in {MATERIAL_QUALITY_ELIGIBLE, MATERIAL_QUALITY_LIMITED_GROUNDING, MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED}
        or visible_slots
        or semantic_material_ids
    ) and material_quality != MATERIAL_QUALITY_LOW_INFORMATION
    audit = {
        "material_quality": material_quality,
        "visible_material_slot_ids": visible_slots,
        "visible_material_slots": visible_slots,
        "semantic_material_ids": semantic_material_ids,
        "relation_material_ids": semantic_material_ids,
        "generic_relation_material_ids": semantic_material_ids,
        "semantic_focus_ids": semantic_focus_ids,
        "semantic_material_count": len(semantic_material_ids),
        "unknown_slot_ids": unknown_slots,
        "unknown_slot_count": len(unknown_slots),
        "source_field_ids": _dedupe(material_meta.get("source_field_ids")),
        "current_only_material_available": current_only_available,
        "material_source_available": True,
        "material_route_audit_status": "audited_r11_4",
        "material_route_audit_performed_here": True,
        "material_quality_forced_to_eligible": False,
        "low_information_or_limited_grounding_upgraded_here": False,
        "raw_memo_or_action_retained_here": False,
        "input_material_bundle_meta_ref": _clean(material_meta.get("schema_version")),
        "body_free": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
    }
    return audit


def _surface_requirement_from_material_row(
    *,
    row: Mapping[str, Any],
    local_case: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    current_input = _current_input_from_local_case(local_case)
    material_audit = row.get("material_audit") if isinstance(row.get("material_audit"), Mapping) else {}
    material_route = dict(material_audit or {})
    material_route.setdefault("material_quality", _clean(material_audit.get("material_quality")))
    material_route.setdefault("visible_material_slots", _dedupe(material_audit.get("visible_material_slot_ids")))
    material_route.setdefault("relation_material_ids", _dedupe(material_audit.get("semantic_material_ids")))
    decision = resolve_public_surface_requirement(
        current_input=current_input,
        material_route=material_route,
        fixture_family_meta={
            "family": _clean(row.get("selected_existing_runtime_family_id") or row.get("family_id")),
            "coverage_slices": _dedupe(row.get("selected_coverage_slice_ids")),
            "path_targets": _dedupe(row.get("path_target_ids")),
        },
        comment_text_present=False,
    )
    assert_public_surface_requirement_decision(decision)
    assert_public_surface_requirement_decision_meta_only(decision)
    return decision


def _surface_path_from_requirement(
    *,
    row: Mapping[str, Any],
    surface_requirement: Mapping[str, Any],
) -> dict[str, Any]:
    surface_family = _clean(surface_requirement.get("surface_requirement_family")) or SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    material_audit = row.get("material_audit") if isinstance(row.get("material_audit"), Mapping) else {}
    material_quality = _clean(material_audit.get("material_quality"))
    path_targets = set(_dedupe(row.get("path_target_ids")))
    decision_sources = _dedupe(surface_requirement.get("decision_sources"))
    labelled_used = surface_family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    limited_used = labelled_used and material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    complete_initial_used = False
    selected_route = "unknown"
    candidate_source = "unknown"
    if labelled_used and limited_used:
        selected_route = "limited_grounding_reception_surface"
        candidate_source = "limited_grounding_reception_surface_candidate"
    elif labelled_used:
        selected_route = "labelled_two_stage_surface_recomposition"
        candidate_source = "labelled_two_stage_surface_recomposition_candidate"
    elif surface_family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
        selected_route = "low_information_observation"
        candidate_source = "low_information_observation_candidate"
    elif "complete_initial_path" in path_targets:
        selected_route = "complete_initial_surface_recomposition"
        candidate_source = "complete_initial_surface_recomposition_candidate"
        complete_initial_used = True
    elif surface_family in {SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER, SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER}:
        selected_route = "normal_observation_rebuild"
        candidate_source = "normal_observation_rebuild_candidate"
    elif surface_family in {SURFACE_REQUIREMENT_SAFETY_BLOCKED, SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED}:
        selected_route = "normal_observation_rebuild"
        candidate_source = f"{surface_family}_current_only_boundary_candidate"
    audit = {
        "surface_requirement_family": surface_family,
        "selected_surface_route_kind": selected_route,
        "selected_public_candidate_source_kind": candidate_source,
        "surface_requirement_decision_sources": decision_sources,
        "labelled_two_stage_surface_recomposition_used": labelled_used and not limited_used,
        "complete_initial_surface_recomposition_used": complete_initial_used,
        "limited_grounding_reception_surface_used": limited_used,
        "history_line_surface_used": False,
        "history_line_surface_candidate_seen_but_not_used": "history_line_candidate_path" in path_targets,
        "current_only_audit_valid": True,
        "p5_history_line_mixed_into_current_only_audit": False,
        "surface_path_audit_status": "audited_r11_5",
        "surface_path_audit_performed_here": True,
        "runtime_candidate_body_retained_here": False,
        "candidate_source_kind_only_retained_here": True,
        "body_free": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_text_included": False,
    }
    return audit

def _scope_groups_from_payload(scope_matrix: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    groups = scope_matrix.get("scope_groups") if isinstance(scope_matrix, Mapping) else None
    if not isinstance(groups, Sequence) or isinstance(groups, (str, bytes, bytearray)):
        return []
    return [group for group in groups if isinstance(group, Mapping)]


def _scope_definition_by_group_id() -> dict[str, Mapping[str, Any]]:
    return {
        _clean(definition.get("scope_group_id")): definition
        for definition in P4_R11_SCOPE_GROUP_DEFINITIONS_20260624
    }


def build_product_readfeel_p4_r11_audit_row_20260624(
    *,
    case_ref_id: str,
    residual_family_id: str,
    run_id: str | None = None,
    source_step: str = P4_R11_R2_STEP_REF_20260624,
    case_origin: str = P4_R11_CASE_ORIGIN_UNKNOWN_20260624,
    residual_focus_slice_ids: Iterable[Any] | Any | None = None,
    priority_band: str = "P2_medium",
    required_surface_role_ids: Iterable[Any] | Any | None = None,
    selected_existing_runtime_family_id: str | None = None,
    selected_coverage_slice_ids: Iterable[Any] | Any | None = None,
    path_target_ids: Iterable[Any] | Any | None = None,
    selection_reason_refs: Iterable[Any] | Any | None = None,
    p4_target_selection_groups: Iterable[Any] | Any | None = None,
    p4_target_blocker_ids: Iterable[Any] | Any | None = None,
    p4_target_layer_ids: Iterable[Any] | Any | None = None,
    selected_priority_index: int | None = None,
) -> dict[str, Any]:
    """Build a body-free audit row shell; actual R11-4+ audit work stays not-run."""

    case_ref = _safe_identifier(case_ref_id, default="")
    if not case_ref:
        raise ValueError("P4-R11 audit row requires case_ref_id")
    group_id = _safe_identifier(residual_family_id, default="")
    if group_id not in set(P4_R11_TARGET_SCOPE_GROUP_IDS_20260624):
        raise ValueError(f"P4-R11 audit row has unknown residual_family_id: {group_id}")
    if source_step not in {P4_R11_R2_STEP_REF_20260624, P4_R11_R3_STEP_REF_20260624}:
        raise ValueError("P4-R11 audit row shell can only be created by R11-2 or R11-3")
    origin = _clean(case_origin) or P4_R11_CASE_ORIGIN_UNKNOWN_20260624
    if origin not in P4_R11_ALLOWED_CASE_ORIGINS_20260624:
        raise ValueError(f"P4-R11 audit row has unknown case_origin: {origin}")
    band = _clean(priority_band) or "P2_medium"
    if band not in P4_R11_ALLOWED_PRIORITY_BANDS_20260624:
        raise ValueError(f"P4-R11 audit row has unknown priority_band: {band}")
    run_id_value = _safe_identifier(run_id or "p4_r11_audit_row_shell", default="p4_r11_audit_row_shell")
    r11_3_selection = source_step == P4_R11_R3_STEP_REF_20260624
    status_flags = _pending_audit_status_flags()
    required_roles = _dedupe(required_surface_role_ids)
    row = {
        "schema_version": PRODUCT_READFEEL_P4_R11_AUDIT_ROW_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_AUDIT_ROW_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": source_step,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "case_ref_id": case_ref,
        "case_origin": origin,
        "residual_family_id": group_id,
        "family_id": group_id,
        "residual_focus_slice_ids": _dedupe(residual_focus_slice_ids),
        "priority_band": band,
        "selected_existing_runtime_family_id": _safe_identifier(selected_existing_runtime_family_id, default=""),
        "selected_coverage_slice_ids": _dedupe(selected_coverage_slice_ids),
        "path_target_ids": _dedupe(path_target_ids),
        "selection_reason_refs": _dedupe(selection_reason_refs),
        "selected_priority_index": int(selected_priority_index or 0),
        "p4_target_selection_groups": _dedupe(p4_target_selection_groups),
        "p4_target_blocker_ids": _dedupe(p4_target_blocker_ids),
        "p4_target_layer_ids": _dedupe(p4_target_layer_ids),
        "required_surface_role_ids": required_roles,
        "history_line_surface_used": False,
        "observed_surface_role_ids": [],
        "missing_surface_role_ids": [],
        "generic_surface_signature_ids": [],
        "temperature_mismatch_ids": [],
        "repair_candidate_layer_ids": [],
        "material_audit": {
            "material_quality": "unknown",
            "visible_material_slot_ids": [],
            "semantic_material_ids": [],
            "semantic_focus_ids": [],
            "semantic_material_count": 0,
            "unknown_slot_count": 0,
            "current_only_material_available": None,
            "material_route_audit_status": status_flags["material_route_audit_status"],
        },
        "surface_path_audit": {
            "surface_requirement_family": "not_run_r11_5",
            "selected_surface_route_kind": "unknown",
            "selected_public_candidate_source_kind": "not_run_r11_5",
            "labelled_two_stage_surface_recomposition_used": False,
            "complete_initial_surface_recomposition_used": False,
            "limited_grounding_reception_surface_used": False,
            "history_line_surface_used": False,
            "surface_path_audit_status": status_flags["surface_path_audit_status"],
        },
        "surface_specificity_audit": {
            "current_only_specificity_required": True,
            "specificity_met": None,
            "required_surface_role_ids": required_roles,
            "observed_surface_role_ids": [],
            "missing_surface_role_ids": [],
            "generic_surface_signature_ids": [],
            "temperature_mismatch_ids": [],
            "question_escape_detected": False,
            "mirror_only_detected": False,
            "surface_specificity_role_audit_status": status_flags["surface_specificity_role_audit_status"],
        },
        "risk_flags": {
            "p5_masking_risk": False,
            "p8_question_escape_risk": False,
            "self_blame_amplification_risk": False,
            "overclaim_risk": False,
            "positive_cooling_risk": False,
            "long_arc_crush_risk": False,
            "structure_question_comfort_escape_risk": False,
            "risk_flag_status": "not_run_r11_7",
        },
        "verdict": None,
        "verdict_status": status_flags["verdict_classification_status"],
        "next_action": "not_run_r11_7",
        "p5_p8_escape_boundary": _p5_p8_escape_boundary_pending(),
        "body_free_audit_row_shell_created_here": True,
        "case_ref_selection_performed_here": r11_3_selection,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "local_case_material_retained_here": False,
        "local_synthetic_body_retained_here": False,
        "p4_r11_audit_row_shell_not_r54_actual_review_row": True,
        "p4_r11_audit_row_shell_not_rating_row": True,
        "p4_r11_audit_row_shell_not_question_observation_row": True,
        **status_flags,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(row, source=f"p4_r11.audit_row.{case_ref}")
    return row


def _p4_target_selection_index(
    p4_target_case_selection: Mapping[str, Any] | None,
) -> dict[str, dict[str, list[str]]]:
    if not isinstance(p4_target_case_selection, Mapping):
        return {}
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        p4_target_case_selection,
        source="p4_r11.r3_p4_target_case_selection_source",
    )
    selected_cases = p4_target_case_selection.get("selected_cases") or p4_target_case_selection.get("selected_case_refs") or []
    if not isinstance(selected_cases, Sequence) or isinstance(selected_cases, (str, bytes, bytearray)):
        return {}
    index: dict[str, dict[str, list[str]]] = {}
    for item in selected_cases:
        if not isinstance(item, Mapping):
            continue
        case_ref = _safe_identifier(item.get("case_ref_id") or item.get("case_id"), default="")
        if not case_ref:
            continue
        index[case_ref] = {
            "p4_target_selection_groups": _dedupe(item.get("selection_groups")),
            "p4_target_blocker_ids": _dedupe(item.get("blocker_ids")),
            "p4_target_layer_ids": _dedupe(item.get("target_layers")),
        }
    return index


def _candidate_index_by_scope_group(
    *,
    scope_groups: Sequence[Mapping[str, Any]],
    baseline_public_safe_index: Sequence[Mapping[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        baseline_public_safe_index,
        source="p4_r11.r3_baseline_public_safe_index_source",
    )
    candidate_index: dict[str, list[dict[str, Any]]] = {_clean(group.get("scope_group_id")): [] for group in scope_groups}
    families_by_group = {
        _clean(group.get("scope_group_id")): set(_dedupe(group.get("existing_runtime_family_ids")))
        for group in scope_groups
    }
    for item in baseline_public_safe_index:
        if not isinstance(item, Mapping):
            continue
        case_ref = _case_ref_from_index_case(item)
        family = _family_from_index_case(item)
        if not case_ref or not family:
            continue
        for group in scope_groups:
            group_id = _clean(group.get("scope_group_id"))
            if family not in families_by_group.get(group_id, set()):
                continue
            candidate_index[group_id].append(
                {
                    "case_ref_id": case_ref,
                    "case_origin": P4_R11_CASE_ORIGIN_P3_BASELINE_20260624,
                    "selected_existing_runtime_family_id": family,
                    "selected_coverage_slice_ids": _coverage_slices_from_index_case(item),
                    "path_target_ids": _dedupe(item.get("path_targets")),
                    "selection_reason_refs": [f"p4_r11_r3_existing_runtime_family_{family}"],
                }
            )
    for group in scope_groups:
        group_id = _clean(group.get("scope_group_id"))
        preferred = list(P4_R11_CASE_SELECTION_PREFERRED_FAMILY_ORDER_20260624.get(group_id, ()))
        preferred_index = {family: idx for idx, family in enumerate(preferred)}
        candidate_index[group_id].sort(
            key=lambda row: (
                preferred_index.get(_clean(row.get("selected_existing_runtime_family_id")), 99),
                _clean(row.get("case_ref_id")),
            )
        )
    return candidate_index


def _select_cases_for_scope_group(
    candidates: Sequence[Mapping[str, Any]],
    *,
    used_case_refs: set[str],
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        case_ref = _safe_identifier(candidate.get("case_ref_id"), default="")
        if not case_ref or case_ref in used_case_refs:
            continue
        selected.append(dict(candidate))
        used_case_refs.add(case_ref)
        if len(selected) >= P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624:
            break
    return selected


def _build_r11_2_summary(*, run_id: str, audit_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R2_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id,
        "target_row_count": P4_R11_TARGET_ROW_COUNT_20260624,
        "audit_row_shell_count": len(audit_rows),
        "audited_row_count": 0,
        "coverage_status": "not_run_r11_3" if not audit_rows else "row_shells_supplied_without_r11_3_coverage_decision",
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "json_schema_file_materialized": False,
        "p4_r11_audit_rows_not_r54_rating_rows": True,
        "p4_r11_audit_rows_not_question_observation_rows": True,
        "implemented_steps": list(P4_R11_R2_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R2_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R3_STEP_REF_20260624,
        **_pending_audit_status_flags(),
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(summary, source="p4_r11.r2_summary")
    return summary


def build_product_readfeel_p4_r11_residual_surface_audit_20260624(
    *,
    audit_rows: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the R11-2 audit-root shell without actual case selection or surface audit."""

    run_id_value = _safe_identifier(run_id or "p4_r11_r2_body_free_audit_guard", default="p4_r11_r2_body_free_audit_guard")
    rows = [dict(row) for row in (audit_rows or []) if isinstance(row, Mapping)]
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(rows, source="p4_r11.r2_audit_rows")
    summary = _build_r11_2_summary(run_id=run_id_value, audit_rows=rows)
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_RESIDUAL_SURFACE_AUDIT_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_RESIDUAL_SURFACE_AUDIT_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R2_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "summary": summary,
        "audit_rows": rows,
        "body_free_audit_row_guard_fixed_here": True,
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R2_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R2_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R3_STEP_REF_20260624,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload, source="p4_r11.r2_audit_root")
    return payload


def build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
    *,
    scope_matrix: Mapping[str, Any] | None,
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None,
    p4_target_case_selection: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Select R11-3 body-free case refs without carrying local input bodies."""

    if not isinstance(scope_matrix, Mapping):
        raise ValueError("P4-R11 R11-3 requires the R11-1 scope matrix")
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(scope_matrix, source="p4_r11.r3_scope_matrix_source")
    if scope_matrix.get("schema_version") != PRODUCT_READFEEL_P4_R11_SCOPE_MATRIX_VERSION_20260624:
        raise ValueError("P4-R11 R11-3 requires the R11-1 scope matrix schema")
    if not isinstance(baseline_public_safe_index, Sequence) or isinstance(
        baseline_public_safe_index, (str, bytes, bytearray)
    ):
        raise ValueError("P4-R11 R11-3 requires the P3 baseline public-safe index")
    run_id_value = _safe_identifier(run_id or "p4_r11_r3_case_ref_selection", default="p4_r11_r3_case_ref_selection")
    scope_groups = _scope_groups_from_payload(scope_matrix)
    if len(scope_groups) != P4_R11_TARGET_SCOPE_GROUP_COUNT_20260624:
        raise ValueError("P4-R11 R11-3 requires all six R11-1 scope groups")
    candidate_index = _candidate_index_by_scope_group(
        scope_groups=scope_groups,
        baseline_public_safe_index=baseline_public_safe_index,
    )
    p4_index = _p4_target_selection_index(p4_target_case_selection)
    definitions = _scope_definition_by_group_id()
    used_case_refs: set[str] = set()
    selected_case_ref_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    selected_counts_by_group: dict[str, int] = {}
    candidate_counts_by_group: dict[str, int] = {}
    insufficient_group_ids: list[str] = []

    for group in scope_groups:
        group_id = _clean(group.get("scope_group_id"))
        definition = definitions.get(group_id) or group
        candidates = candidate_index.get(group_id, [])
        candidate_counts_by_group[group_id] = len(candidates)
        selected = _select_cases_for_scope_group(candidates, used_case_refs=used_case_refs)
        selected_counts_by_group[group_id] = len(selected)
        if len(selected) < P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624:
            insufficient_group_ids.append(group_id)
        for index, candidate in enumerate(selected, start=1):
            case_ref = _safe_identifier(candidate.get("case_ref_id"), default="")
            p4_meta = p4_index.get(case_ref, {})
            row = build_product_readfeel_p4_r11_audit_row_20260624(
                case_ref_id=case_ref,
                residual_family_id=group_id,
                run_id=run_id_value,
                source_step=P4_R11_R3_STEP_REF_20260624,
                case_origin=P4_R11_CASE_ORIGIN_P3_BASELINE_20260624,
                residual_focus_slice_ids=group.get("residual_focus_slice_ids") or definition.get("residual_focus_slice_ids"),
                priority_band=_clean(group.get("priority_band") or definition.get("priority_band")) or "P2_medium",
                required_surface_role_ids=group.get("required_surface_role_ids") or definition.get("required_surface_role_ids"),
                selected_existing_runtime_family_id=_clean(candidate.get("selected_existing_runtime_family_id")),
                selected_coverage_slice_ids=candidate.get("selected_coverage_slice_ids"),
                path_target_ids=candidate.get("path_target_ids"),
                selection_reason_refs=candidate.get("selection_reason_refs"),
                p4_target_selection_groups=p4_meta.get("p4_target_selection_groups"),
                p4_target_blocker_ids=p4_meta.get("p4_target_blocker_ids"),
                p4_target_layer_ids=p4_meta.get("p4_target_layer_ids"),
                selected_priority_index=index,
            )
            audit_rows.append(row)
            selected_case_ref_rows.append(
                {
                    "case_ref_id": case_ref,
                    "case_origin": row["case_origin"],
                    "residual_family_id": group_id,
                    "family_id": group_id,
                    "selected_existing_runtime_family_id": row["selected_existing_runtime_family_id"],
                    "residual_focus_slice_ids": row["residual_focus_slice_ids"],
                    "selected_coverage_slice_ids": row["selected_coverage_slice_ids"],
                    "path_target_ids": row["path_target_ids"],
                    "priority_band": row["priority_band"],
                    "required_surface_role_ids": row["required_surface_role_ids"],
                    "p4_target_selection_groups": row["p4_target_selection_groups"],
                    "p4_target_blocker_ids": row["p4_target_blocker_ids"],
                    "p4_target_layer_ids": row["p4_target_layer_ids"],
                    "case_ref_selection_performed_here": True,
                    "actual_audit_rows_created_here": False,
                    "local_case_material_retained_here": False,
                    "local_synthetic_body_retained_here": False,
                    **_body_boundary(),
                }
            )

    coverage_status = "complete" if not insufficient_group_ids else "insufficient_public_safe_case_refs"
    family_counts = Counter(row["selected_existing_runtime_family_id"] for row in selected_case_ref_rows)
    selection_summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R3_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "target_scope_group_ids": list(P4_R11_TARGET_SCOPE_GROUP_IDS_20260624),
        "target_scope_group_count": P4_R11_TARGET_SCOPE_GROUP_COUNT_20260624,
        "target_row_count": P4_R11_TARGET_ROW_COUNT_20260624,
        "minimum_case_refs_per_scope_group": P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624,
        "source_baseline_public_safe_index_case_count": len(baseline_public_safe_index),
        "candidate_counts_by_scope_group": dict(sorted(candidate_counts_by_group.items())),
        "selected_counts_by_scope_group": dict(sorted(selected_counts_by_group.items())),
        "selected_ref_row_count": len(selected_case_ref_rows),
        "selected_unique_case_ref_count": len({row["case_ref_id"] for row in selected_case_ref_rows}),
        "selected_existing_runtime_family_counts": dict(sorted(family_counts.items())),
        "coverage_status": coverage_status,
        "insufficient_scope_group_ids": insufficient_group_ids,
        "insufficient_scope_group_count": len(insufficient_group_ids),
        "case_ref_selection_performed_here": True,
        "case_ref_supplemented_by_fabrication": False,
        "raw_input_or_local_synthetic_body_brought_into_summary": False,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p4_r11_audit_rows_not_r54_rating_rows": True,
        "p4_r11_audit_rows_not_question_observation_rows": True,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R3_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R3_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R4_STEP_REF_20260624,
        **_pending_audit_status_flags(),
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        selected_case_ref_rows,
        source="p4_r11.r3_selected_case_ref_rows",
    )
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        selection_summary,
        source="p4_r11.r3_selection_summary",
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R3_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "scope_matrix_ref": _safe_identifier(scope_matrix.get("run_id"), default="p4_r11_r1_scope_matrix"),
        "summary": selection_summary,
        "selected_case_ref_rows": selected_case_ref_rows,
        "audit_rows": audit_rows,
        "case_ref_selection_performed_here": True,
        "case_ref_supplemented_by_fabrication": False,
        "actual_audit_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R3_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R3_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R4_STEP_REF_20260624,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload, source="p4_r11.r3_selection_payload")
    return payload




def _audit_rows_from_payload(payload: Mapping[str, Any], *, source: str) -> list[dict[str, Any]]:
    rows_source = payload.get("audit_rows") or []
    if not isinstance(rows_source, Sequence) or isinstance(rows_source, (str, bytes, bytearray)):
        raise ValueError(f"{source} requires audit_rows")
    rows = [dict(row) for row in rows_source if isinstance(row, Mapping)]
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(rows, source=f"{source}.audit_rows")
    return rows


def _material_audit_summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    run_id: str,
    source_selection: Mapping[str, Any],
) -> dict[str, Any]:
    quality_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    route_status_counts: Counter[str] = Counter()
    focus_counts: Counter[str] = Counter()
    current_material_count = 0
    material_absence_count = 0
    for row in rows:
        audit = row.get("material_audit") if isinstance(row.get("material_audit"), Mapping) else {}
        quality = _clean(audit.get("material_quality")) or P4_R11_MATERIAL_QUALITY_UNKNOWN_20260624
        quality_counts[quality] += 1
        group_counts[_clean(row.get("residual_family_id"))] += 1
        route_status_counts[_clean(audit.get("material_route_audit_status"))] += 1
        focus_counts.update(_dedupe(audit.get("semantic_focus_ids")))
        if audit.get("current_only_material_available") is True:
            current_material_count += 1
        else:
            material_absence_count += 1
    selection_summary = source_selection.get("summary") if isinstance(source_selection.get("summary"), Mapping) else {}
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R4_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id,
        "target_row_count": P4_R11_TARGET_ROW_COUNT_20260624,
        "audited_row_count": len(rows),
        "coverage_status": _clean(selection_summary.get("coverage_status")) or "unknown",
        "selected_ref_row_count": int(selection_summary.get("selected_ref_row_count") or len(rows)),
        "selected_unique_case_ref_count": int(selection_summary.get("selected_unique_case_ref_count") or len({row.get("case_ref_id") for row in rows})),
        "material_quality_counts": dict(sorted(quality_counts.items())),
        "material_route_status_counts": dict(sorted(route_status_counts.items())),
        "audited_counts_by_scope_group": dict(sorted(group_counts.items())),
        "semantic_focus_counts": dict(sorted(focus_counts.items())),
        "current_only_material_available_row_count": current_material_count,
        "material_absence_or_low_information_row_count": material_absence_count,
        "source_unavailable_row_count": int(quality_counts.get(P4_R11_MATERIAL_QUALITY_SOURCE_UNAVAILABLE_20260624, 0)),
        "low_information_row_count": int(quality_counts.get(MATERIAL_QUALITY_LOW_INFORMATION, 0)),
        "limited_grounding_row_count": int(quality_counts.get(MATERIAL_QUALITY_LIMITED_GROUNDING, 0)),
        "eligible_row_count": int(quality_counts.get(MATERIAL_QUALITY_ELIGIBLE, 0)),
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": False,
        "material_quality_forced_to_eligible": False,
        "low_information_or_limited_grounding_upgraded_here": False,
        "raw_memo_or_action_retained_here": False,
        "case_ref_selection_performed_here": True,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p4_r11_audit_rows_not_r54_rating_rows": True,
        "p4_r11_audit_rows_not_question_observation_rows": True,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R4_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R4_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R5_STEP_REF_20260624,
        **_r11_4_pending_after_material_flags(),
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(summary, source="p4_r11.r4_material_summary")
    return summary


def build_product_readfeel_p4_r11_material_route_audit_20260624(
    *,
    case_ref_selection_payload: Mapping[str, Any] | None,
    local_baseline_cases: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run R11-4 body-free material route audit for selected case refs.

    ``local_baseline_cases`` may contain synthetic body material.  It is used
    only long enough to build ``emlis_input_material_bundle`` meta; returned
    rows keep ids/counts/booleans only.
    """

    if not isinstance(case_ref_selection_payload, Mapping):
        raise ValueError("P4-R11 R11-4 requires the R11-3 case ref selection payload")
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        case_ref_selection_payload,
        source="p4_r11.r4_case_ref_selection_source",
    )
    if case_ref_selection_payload.get("schema_version") != PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_VERSION_20260624:
        raise ValueError("P4-R11 R11-4 requires the R11-3 case ref selection schema")
    rows = _audit_rows_from_payload(case_ref_selection_payload, source="p4_r11.r4_selection_source")
    run_id_value = _safe_identifier(run_id or "p4_r11_r4_material_route_audit", default="p4_r11_r4_material_route_audit")
    local_cases = _local_case_map_for_r11_material_audit(local_baseline_cases)
    audited_rows: list[dict[str, Any]] = []
    for source_row in rows:
        row = dict(source_row)
        case_ref = _safe_identifier(row.get("case_ref_id"), default="")
        local_case = local_cases.get(case_ref)
        current_input = _current_input_from_local_case(local_case)
        material_meta = build_emlis_input_material_bundle_meta(current_input) if current_input else None
        material_audit = _body_free_material_audit_from_meta(row=row, material_meta=material_meta)
        status_flags = _r11_4_pending_after_material_flags()
        row.update(
            {
                "source_step": P4_R11_R4_STEP_REF_20260624,
                "run_id": run_id_value,
                "material_audit": material_audit,
                "visible_material_slot_ids": material_audit["visible_material_slot_ids"],
                "semantic_material_ids": material_audit["semantic_material_ids"],
                "semantic_focus_ids": material_audit["semantic_focus_ids"],
                "semantic_material_count": material_audit["semantic_material_count"],
                "unknown_slot_count": material_audit["unknown_slot_count"],
                "material_quality": material_audit["material_quality"],
                "current_only_material_available": material_audit["current_only_material_available"],
                "implemented_steps": list(P4_R11_R4_IMPLEMENTED_STEPS_20260624),
                "not_yet_implemented_steps": list(P4_R11_R4_NOT_YET_IMPLEMENTED_STEPS_20260624),
                "next_implementation_step": P4_R11_R5_STEP_REF_20260624,
                "actual_audit_rows_created_here": False,
                "actual_rating_rows_materialized_here": False,
                "actual_question_need_observation_rows_materialized_here": False,
                "local_case_material_available": bool(local_case),
                "local_case_material_retained_here": False,
                "local_synthetic_body_retained_here": False,
                "raw_memo_or_action_retained_here": False,
                "material_quality_forced_to_eligible": False,
                "low_information_or_limited_grounding_upgraded_here": False,
                **status_flags,
            }
        )
        assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
            row,
            source=f"p4_r11.r4_row.{case_ref}",
        )
        audited_rows.append(row)
    summary = _material_audit_summary(
        rows=audited_rows,
        run_id=run_id_value,
        source_selection=case_ref_selection_payload,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R4_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "case_ref_selection_ref": _safe_identifier(case_ref_selection_payload.get("run_id"), default="p4_r11_r3_case_ref_selection"),
        "summary": summary,
        "audit_rows": audited_rows,
        "case_ref_selection_performed_here": True,
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": False,
        "actual_audit_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R4_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R4_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R5_STEP_REF_20260624,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload, source="p4_r11.r4_material_payload")
    return payload


def _surface_path_summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    run_id: str,
    source_material_payload: Mapping[str, Any],
) -> dict[str, Any]:
    route_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    history_candidate_count = 0
    for row in rows:
        audit = row.get("surface_path_audit") if isinstance(row.get("surface_path_audit"), Mapping) else {}
        route_counts[_clean(audit.get("selected_surface_route_kind"))] += 1
        family_counts[_clean(audit.get("surface_requirement_family"))] += 1
        source_counts[_clean(audit.get("selected_public_candidate_source_kind"))] += 1
        if audit.get("history_line_surface_candidate_seen_but_not_used") is True:
            history_candidate_count += 1
    source_summary = source_material_payload.get("summary") if isinstance(source_material_payload.get("summary"), Mapping) else {}
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R5_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id,
        "target_row_count": P4_R11_TARGET_ROW_COUNT_20260624,
        "audited_row_count": len(rows),
        "coverage_status": _clean(source_summary.get("coverage_status")) or "unknown",
        "selected_surface_route_kind_counts": dict(sorted(route_counts.items())),
        "surface_requirement_family_counts": dict(sorted(family_counts.items())),
        "selected_public_candidate_source_kind_counts": dict(sorted(source_counts.items())),
        "history_line_candidate_seen_but_not_used_count": history_candidate_count,
        "history_line_surface_used_count": 0,
        "labelled_two_stage_surface_recomposition_used_count": int(route_counts.get("labelled_two_stage_surface_recomposition", 0)),
        "complete_initial_surface_recomposition_used_count": int(route_counts.get("complete_initial_surface_recomposition", 0)),
        "limited_grounding_reception_surface_used_count": int(route_counts.get("limited_grounding_reception_surface", 0)),
        "low_information_observation_route_count": int(route_counts.get("low_information_observation", 0)),
        "normal_observation_rebuild_route_count": int(route_counts.get("normal_observation_rebuild", 0)),
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": True,
        "surface_specificity_role_audit_performed_here": False,
        "runtime_candidate_body_retained_here": False,
        "candidate_source_kind_only_retained_here": True,
        "p5_history_line_mixed_into_current_only_audit": False,
        "case_ref_selection_performed_here": True,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p4_r11_audit_rows_not_r54_rating_rows": True,
        "p4_r11_audit_rows_not_question_observation_rows": True,
        "p5_human_review_evidence_created_here": False,
        "question_observation_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R5_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R5_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R6_STEP_REF_20260624,
        **_r11_5_pending_after_surface_path_flags(),
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(summary, source="p4_r11.r5_surface_summary")
    return summary


def build_product_readfeel_p4_r11_surface_path_audit_20260624(
    *,
    material_route_audit_payload: Mapping[str, Any] | None,
    local_baseline_cases: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Run R11-5 body-free surface path audit from R11-4 material rows."""

    if not isinstance(material_route_audit_payload, Mapping):
        raise ValueError("P4-R11 R11-5 requires the R11-4 material route audit payload")
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        material_route_audit_payload,
        source="p4_r11.r5_material_audit_source",
    )
    if material_route_audit_payload.get("schema_version") != PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_VERSION_20260624:
        raise ValueError("P4-R11 R11-5 requires the R11-4 material route audit schema")
    rows = _audit_rows_from_payload(material_route_audit_payload, source="p4_r11.r5_material_source")
    run_id_value = _safe_identifier(run_id or "p4_r11_r5_surface_path_audit", default="p4_r11_r5_surface_path_audit")
    local_cases = _local_case_map_for_r11_material_audit(local_baseline_cases)
    audited_rows: list[dict[str, Any]] = []
    for source_row in rows:
        row = dict(source_row)
        case_ref = _safe_identifier(row.get("case_ref_id"), default="")
        if row.get("material_route_audit_performed_here") is not True:
            raise ValueError(f"P4-R11 R11-5 requires R11-4 material audit before surface path audit: {case_ref}")
        local_case = local_cases.get(case_ref)
        surface_requirement = _surface_requirement_from_material_row(row=row, local_case=local_case)
        surface_path_audit = _surface_path_from_requirement(row=row, surface_requirement=surface_requirement)
        status_flags = _r11_5_pending_after_surface_path_flags()
        row.update(
            {
                "source_step": P4_R11_R5_STEP_REF_20260624,
                "run_id": run_id_value,
                "surface_path_audit": surface_path_audit,
                "surface_requirement_family": surface_path_audit["surface_requirement_family"],
                "selected_surface_route_kind": surface_path_audit["selected_surface_route_kind"],
                "selected_public_candidate_source_kind": surface_path_audit["selected_public_candidate_source_kind"],
                "labelled_two_stage_surface_recomposition_used": surface_path_audit[
                    "labelled_two_stage_surface_recomposition_used"
                ],
                "complete_initial_surface_recomposition_used": surface_path_audit[
                    "complete_initial_surface_recomposition_used"
                ],
                "limited_grounding_reception_surface_used": surface_path_audit[
                    "limited_grounding_reception_surface_used"
                ],
                "history_line_surface_used": False,
                "surface_requirement_decision": surface_requirement,
                "implemented_steps": list(P4_R11_R5_IMPLEMENTED_STEPS_20260624),
                "not_yet_implemented_steps": list(P4_R11_R5_NOT_YET_IMPLEMENTED_STEPS_20260624),
                "next_implementation_step": P4_R11_R6_STEP_REF_20260624,
                "runtime_candidate_body_retained_here": False,
                "candidate_source_kind_only_retained_here": True,
                "actual_audit_rows_created_here": False,
                "actual_rating_rows_materialized_here": False,
                "actual_question_need_observation_rows_materialized_here": False,
                "local_case_material_retained_here": False,
                "local_synthetic_body_retained_here": False,
                **status_flags,
            }
        )
        assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
            row,
            source=f"p4_r11.r5_row.{case_ref}",
        )
        audited_rows.append(row)
    summary = _surface_path_summary(rows=audited_rows, run_id=run_id_value, source_material_payload=material_route_audit_payload)
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R5_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": run_id_value,
        "material_route_audit_ref": _safe_identifier(material_route_audit_payload.get("run_id"), default="p4_r11_r4_material_route_audit"),
        "summary": summary,
        "audit_rows": audited_rows,
        "case_ref_selection_performed_here": True,
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": True,
        "actual_audit_rows_created_here": False,
        "json_schema_file_materialized": False,
        "implemented_steps": list(P4_R11_R5_IMPLEMENTED_STEPS_20260624),
        "not_yet_implemented_steps": list(P4_R11_R5_NOT_YET_IMPLEMENTED_STEPS_20260624),
        "next_implementation_step": P4_R11_R6_STEP_REF_20260624,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(payload, source="p4_r11.r5_surface_payload")
    return payload

def build_product_readfeel_p4_r11_public_summary_20260624(
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_payload = dict(payload or build_product_readfeel_p4_r11_residual_surface_audit_20260624())
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        source_payload,
        source="p4_r11.audit_public_summary_source",
    )
    summary = dict(source_payload.get("summary") or {})
    rows_source = source_payload.get("selected_case_ref_rows") or source_payload.get("audit_rows") or []
    rows = [row for row in rows_source if isinstance(row, Mapping)] if isinstance(rows_source, Sequence) else []
    public_rows = []
    for row in rows:
        material_audit = row.get("material_audit") if isinstance(row.get("material_audit"), Mapping) else {}
        surface_path_audit = row.get("surface_path_audit") if isinstance(row.get("surface_path_audit"), Mapping) else {}
        public_rows.append(
            {
                "case_ref_id": _safe_identifier(row.get("case_ref_id"), default=""),
                "case_origin": _clean(row.get("case_origin")),
                "residual_family_id": _clean(row.get("residual_family_id")),
                "family_id": _clean(row.get("family_id") or row.get("residual_family_id")),
                "selected_existing_runtime_family_id": _clean(row.get("selected_existing_runtime_family_id")),
                "residual_focus_slice_ids": _dedupe(row.get("residual_focus_slice_ids")),
                "selected_coverage_slice_ids": _dedupe(row.get("selected_coverage_slice_ids")),
                "priority_band": _clean(row.get("priority_band")),
                "required_surface_role_ids": _dedupe(row.get("required_surface_role_ids")),
                "material_quality": _clean(material_audit.get("material_quality")),
                "visible_material_slot_ids": _dedupe(material_audit.get("visible_material_slot_ids")),
                "semantic_material_ids": _dedupe(material_audit.get("semantic_material_ids")),
                "semantic_focus_ids": _dedupe(material_audit.get("semantic_focus_ids")),
                "current_only_material_available": material_audit.get("current_only_material_available") is True,
                "material_route_audit_status": _clean(material_audit.get("material_route_audit_status")),
                "surface_requirement_family": _clean(surface_path_audit.get("surface_requirement_family")),
                "selected_surface_route_kind": _clean(surface_path_audit.get("selected_surface_route_kind")),
                "selected_public_candidate_source_kind": _clean(surface_path_audit.get("selected_public_candidate_source_kind")),
                "surface_path_audit_status": _clean(surface_path_audit.get("surface_path_audit_status")),
                "history_line_surface_used": False,
                "case_ref_selection_performed_here": row.get("case_ref_selection_performed_here") is True,
                "actual_audit_rows_created_here": False,
            }
        )
    public_summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": _clean(source_payload.get("source_step")) or P4_R11_R2_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": _safe_identifier(source_payload.get("run_id"), default="p4_r11_audit_public_summary"),
        "summary": summary,
        "selected_case_ref_rows": public_rows,
        "selected_ref_row_count": len(public_rows),
        "case_ref_selection_performed_here": source_payload.get("case_ref_selection_performed_here") is True,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "json_schema_file_materialized": False,
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        public_summary,
        source="p4_r11.audit_public_summary",
    )
    return public_summary


def dump_product_readfeel_p4_r11_public_summary_20260624(
    payload: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p4_r11_public_summary_20260624(payload)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def build_product_readfeel_p4_r11_contract_scope_public_summary_20260624(
    scope_matrix: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = dict(scope_matrix or build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624())
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(
        payload,
        source="p4_r11.public_summary_source",
    )
    summary = dict(payload.get("summary") or {})
    scope_groups = [group for group in payload.get("scope_groups") or [] if isinstance(group, Mapping)]
    public_summary = {
        "schema_version": PRODUCT_READFEEL_P4_R11_PUBLIC_SUMMARY_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_PUBLIC_SUMMARY_VERSION_20260624,
        "source": PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": P4_R11_R1_STEP_REF_20260624,
        "audit_profile": PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "run_id": _safe_identifier(payload.get("run_id"), default="p4_r11_r1_scope_matrix"),
        "summary": summary,
        "case_ref_selection_performed_here": False,
        "actual_audit_rows_created_here": False,
        "scope_group_refs": [
            {
                "scope_group_id": _clean(group.get("scope_group_id")),
                "priority_band": _clean(group.get("priority_band")),
                "existing_runtime_family_ids": _dedupe(group.get("existing_runtime_family_ids")),
                "residual_focus_slice_ids": _dedupe(group.get("residual_focus_slice_ids")),
                "minimum_case_ref_count": int(group.get("minimum_case_ref_count") or 0),
                "candidate_case_ref_count": int(group.get("candidate_case_ref_count") or 0),
                "coverage_status": _clean(group.get("coverage_status")),
                "runtime_family_rename_applied": False,
            }
            for group in scope_groups
        ],
        **_all_boundary_flags(),
    }
    assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624(
        public_summary,
        source="p4_r11.public_summary",
    )
    return public_summary


def dump_product_readfeel_p4_r11_contract_scope_public_summary_20260624(
    scope_matrix: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p4_r11_contract_scope_public_summary_20260624(scope_matrix)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_R11_CONTRACT_FREEZE_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_SCOPE_MATRIX_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_SCOPE_GROUP_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_SCOPE_SUMMARY_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_PUBLIC_SUMMARY_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_RESIDUAL_SURFACE_AUDIT_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_AUDIT_ROW_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_CASE_REF_SELECTION_SUMMARY_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_MATERIAL_ROUTE_AUDIT_SUMMARY_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_SUMMARY_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_AUDIT_PUBLIC_SUMMARY_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_SOURCE_20260624",
    "PRODUCT_READFEEL_P4_R11_PHASE_20260624",
    "PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624",
    "P4_R11_R0_STEP_REF_20260624",
    "P4_R11_R1_STEP_REF_20260624",
    "P4_R11_R2_STEP_REF_20260624",
    "P4_R11_R3_STEP_REF_20260624",
    "P4_R11_R4_STEP_REF_20260624",
    "P4_R11_R5_STEP_REF_20260624",
    "P4_R11_R0_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R0_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R1_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R1_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R2_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R2_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R3_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R3_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R4_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R4_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R5_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R5_NOT_YET_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R10_CLOSED_RED_REF_20260624",
    "P4_R11_R55_DECISION_REF_20260624",
    "P4_R11_R55_NEXT_REQUIRED_STEP_REF_20260624",
    "P4_R11_TARGET_SCOPE_GROUP_IDS_20260624",
    "P4_R11_TARGET_FOCUS_SLICE_IDS_20260624",
    "P4_R11_SCOPE_GROUP_MINIMUM_CASE_REFS_20260624",
    "P4_R11_TARGET_ROW_COUNT_20260624",
    "SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION",
    "SCOPE_GROUP_DAILY_POSITIVE_RECOVERY",
    "SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY",
    "SCOPE_GROUP_LONG_MEANING_ARC",
    "SCOPE_GROUP_STRUCTURE_QUESTION",
    "SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER",
    "assert_product_readfeel_p4_r11_contract_scope_meta_only_20260624",
    "assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624",
    "build_product_readfeel_p4_r11_contract_freeze_20260624",
    "build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624",
    "build_product_readfeel_p4_r11_audit_row_20260624",
    "build_product_readfeel_p4_r11_residual_surface_audit_20260624",
    "build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624",
    "build_product_readfeel_p4_r11_material_route_audit_20260624",
    "build_product_readfeel_p4_r11_surface_path_audit_20260624",
    "build_product_readfeel_p4_r11_public_summary_20260624",
    "dump_product_readfeel_p4_r11_public_summary_20260624",
    "build_product_readfeel_p4_r11_contract_scope_public_summary_20260624",
    "dump_product_readfeel_p4_r11_contract_scope_public_summary_20260624",
]
