# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-4 family tuning policy for Product Read Feel family work.

P4-4 freezes family-level tuning as body-free policy material: ratios,
temperature profiles, section roles, required anchors, question limits, and
forbidden surface classes.  It deliberately does not render Emlis output, keep
raw input, keep ``comment_text`` bodies, add public response keys, relax gates,
create case-specific runtime branches, or strengthen P5 history-line surfaces.

This module is the P4 policy bridge.  It connects the P4-1 target case subset
and optional P4-2/P4-3 audit material to the runtime owner files by identifier
only.  Runtime wording and surface realization remain owned by the existing
resolver / ratio / section-plan / realizer modules and are not changed here.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import copy
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_POSITIVE,
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_SELF_DENIAL,
    FAMILY_STRUCTURE_QUESTION,
)
from emlis_ai_product_readfeel_p4_material_audit import (
    assert_product_readfeel_p4_material_audit_meta_only_20260610,
)
from emlis_ai_product_readfeel_p4_target_case_selection import (
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only

PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.family_tuning_policy.20260610.v1"
)
PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_ITEM_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.family_tuning_policy_item.20260610.v1"
)
PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.family_tuning_policy_summary.20260610.v1"
)
PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610: Final = (
    "P4-4_Family_Tuning_Policy"
)
PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SOURCE_20260610: Final = (
    "Cocolon_EmlisAI_P4_FamilyProductTuning_FamilyTuningPolicy_20260610"
)
PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610: Final = (
    "p4_4_family_ratio_temperature_section_role_policy"
)

FAMILY_LIMITED_GROUNDING: Final = "limited_grounding"
COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION: Final = "source_unavailable_high_information"
COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE: Final = "history_line_eligible"

ROLE_EVENT_ANCHOR: Final = "event_anchor"
ROLE_ACTION_ANCHOR: Final = "action_anchor"
ROLE_RELATIONSHIP_ANCHOR: Final = "relationship_anchor"
ROLE_EMOTION_DIRECTION_ANCHOR: Final = "emotion_direction_anchor"
ROLE_UNRESOLVED_WEIGHT_ANCHOR: Final = "unresolved_weight_anchor"
ROLE_STRUCTURE_QUESTION_ANCHOR: Final = "structure_question_anchor"
ROLE_CHANGE_ANCHOR: Final = "change_anchor"
ROLE_VALUE_ANCHOR: Final = "value_anchor"
ROLE_EMLIS_RECEPTION_ANCHOR: Final = "emlis_reception_anchor"
ROLE_SELF_DENIAL_STATE_NOT_FACT: Final = "self_denial_phrase_as_state_not_fact"
ROLE_VISIBLE_SCOPE_MARKER: Final = "visible_scope_marker"
ROLE_SOFT_INFERENCE_MARKER: Final = "soft_inference_marker"
ROLE_NO_TARGET_JUDGEMENT_MARKER: Final = "no_target_judgement_marker"
ROLE_NO_IDENTITY_CLAIM_MARKER: Final = "no_identity_claim_marker"
ROLE_LIMITED_GROUNDING_MARKER: Final = "limited_grounding_marker"
ROLE_SOURCE_UNAVAILABLE_MARKER: Final = "source_unavailable_marker"
ROLE_BOUNDARY_SIGNAL_ANCHOR: Final = "boundary_signal_anchor"
ROLE_UNKNOWN_SCOPE_MARKER: Final = "unknown_scope_marker"
ROLE_POSITIVE_CHANGE_ANCHOR: Final = "positive_change_anchor"

TEMP_WARM_RECEPTION_LIGHT_OBSERVATION: Final = "warm_reception_with_light_observation"
TEMP_CALM_OBSERVATION_SOFT_RECEPTION: Final = "calm_observation_with_soft_reception"
TEMP_CAREFUL_SUPPORT_NO_IDENTITY_CONFIRMATION: Final = "careful_support_without_identity_confirmation"
TEMP_POSITIVE_WARMTH_NO_OVERANALYSIS: Final = "positive_warmth_without_overanalysis"
TEMP_BOUNDARY_OBSERVATION_NO_TARGET_JUDGEMENT: Final = "boundary_observation_without_target_judgement"
TEMP_LIMITED_SCOPE_RECEPTION: Final = "limited_scope_reception"
TEMP_SOURCE_UNAVAILABLE_FAIL_CLOSED_BOUNDARY: Final = "source_unavailable_boundary_without_normal_rebuild"
TEMP_HISTORY_LINE_HOLD_CURRENT_INPUT_FIRST: Final = "history_line_hold_current_input_first"

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
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
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
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
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
        "schema_file_materialized",
        "material_quality_forced_to_eligible",
        "source_unavailable_recast_as_normal_rebuild",
        "history_line_masks_current_input_gap",
        "question_only_allowed",
        "comfort_only_allowed",
        "observation_zero_allowed",
        "human_follow_zero_allowed",
    }
)

_RUNTIME_OWNER_REFERENCES_20260610: Final[tuple[dict[str, Any], ...]] = (
    {
        "owner_id": "reception_mode_resolver",
        "owner_file": "services/ai_inference/emlis_ai_reception_mode_resolver.py",
        "runtime_mutation_applied_by_p4_4": False,
        "policy_connection_kind": "mode_id_owner_reference_only",
    },
    {
        "owner_id": "state_answer_ratio_policy",
        "owner_file": "services/ai_inference/emlis_ai_state_answer_ratio_policy.py",
        "runtime_mutation_applied_by_p4_4": False,
        "policy_connection_kind": "ratio_owner_reference_only",
    },
    {
        "owner_id": "two_stage_section_surface_plan",
        "owner_file": "services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
        "runtime_mutation_applied_by_p4_4": False,
        "policy_connection_kind": "section_role_owner_reference_only",
    },
    {
        "owner_id": "complete_surface_realizer",
        "owner_file": "services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "runtime_mutation_applied_by_p4_4": False,
        "policy_connection_kind": "surface_realizer_owner_reference_only",
    },
)

# Policy rows are deliberately text-free.  They describe shape and constraints,
# not completed user-facing sentences.
_FAMILY_POLICY_REGISTRY_20260610: Final[dict[str, dict[str, Any]]] = {
    FAMILY_DAILY_UNPLEASANT: {
        "policy_id": "p4_4_daily_unpleasant_warm_reception_light_observation",
        "family": FAMILY_DAILY_UNPLEASANT,
        "policy_group": "main_target",
        "temperature_profile": TEMP_WARM_RECEPTION_LIGHT_OBSERVATION,
        "ratio_profile": {
            "observation_ratio_min": 0.20,
            "observation_ratio_max": 0.30,
            "reception_ratio_min": 0.70,
            "reception_ratio_max": 0.80,
            "ratio_intent": "light_observation_then_warm_reception",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "event_and_reaction_observation",
            "reception_section_role": "emlis_reaction_reception",
            "max_questions": 0,
            "requires_reception_section": True,
            "requires_visible_scope_marker": False,
            "question_only_forbidden": True,
            "question_position": "not_primary",
        },
        "required_anchor_roles": [
            ROLE_EVENT_ANCHOR,
            ROLE_EMOTION_DIRECTION_ANCHOR,
            ROLE_UNRESOLVED_WEIGHT_ANCHOR,
            ROLE_EMLIS_RECEPTION_ANCHOR,
            ROLE_NO_TARGET_JUDGEMENT_MARKER,
        ],
        "forbidden_surface_classes": [
            "target_judgement_agreement",
            "other_person_intent_claim",
            "heavy_analysis",
            "generic_comfort_template",
            "action_instruction",
            "p6_over_insight",
        ],
        "surface_requirement_preference": "labelled_two_stage_or_family_tuned_state_answer",
        "runtime_owner_mode_id": "daily_unpleasant_reception",
        "runtime_ratio_owner_reason_id": "daily_unpleasant_reception_light",
    },
    FAMILY_STRUCTURE_QUESTION: {
        "policy_id": "p4_4_structure_question_calm_observation_soft_reception",
        "family": FAMILY_STRUCTURE_QUESTION,
        "policy_group": "main_target",
        "temperature_profile": TEMP_CALM_OBSERVATION_SOFT_RECEPTION,
        "ratio_profile": {
            "observation_ratio_min": 0.60,
            "observation_ratio_max": 0.70,
            "reception_ratio_min": 0.30,
            "reception_ratio_max": 0.40,
            "ratio_intent": "structure_observation_then_soft_reception",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "structure_question_observation",
            "reception_section_role": "emlis_soft_reception",
            "max_questions": 1,
            "requires_reception_section": True,
            "requires_visible_scope_marker": True,
            "question_only_forbidden": True,
            "question_position": "after_reception_optional",
        },
        "required_anchor_roles": [
            ROLE_STRUCTURE_QUESTION_ANCHOR,
            ROLE_RELATIONSHIP_ANCHOR,
            ROLE_UNRESOLVED_WEIGHT_ANCHOR,
            ROLE_SOFT_INFERENCE_MARKER,
            ROLE_EMLIS_RECEPTION_ANCHOR,
        ],
        "forbidden_surface_classes": [
            "comfort_only",
            "advice_answer",
            "cause_claim_without_evidence",
            "personality_claim",
            "other_person_intent_claim",
            "p6_over_insight",
        ],
        "surface_requirement_preference": "labelled_two_stage_structure_entry",
        "runtime_owner_mode_id": "structure_question_observation",
        "runtime_ratio_owner_reason_id": "structure_question_observation_thickened",
    },
    FAMILY_SELF_DENIAL: {
        "policy_id": "p4_4_self_denial_careful_support_without_identity_confirmation",
        "family": FAMILY_SELF_DENIAL,
        "policy_group": "yellow_review",
        "temperature_profile": TEMP_CAREFUL_SUPPORT_NO_IDENTITY_CONFIRMATION,
        "ratio_profile": {
            "observation_ratio_min": 0.40,
            "observation_ratio_max": 0.50,
            "reception_ratio_min": 0.50,
            "reception_ratio_max": 0.60,
            "ratio_intent": "careful_observation_and_support_balance",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "self_denial_state_not_fact_observation",
            "reception_section_role": "safe_counter_reception",
            "max_questions": 0,
            "requires_reception_section": True,
            "requires_visible_scope_marker": True,
            "question_only_forbidden": True,
            "question_position": "not_primary",
        },
        "required_anchor_roles": [
            ROLE_SELF_DENIAL_STATE_NOT_FACT,
            ROLE_UNRESOLVED_WEIGHT_ANCHOR,
            ROLE_NO_IDENTITY_CLAIM_MARKER,
            ROLE_EMLIS_RECEPTION_ANCHOR,
        ],
        "forbidden_surface_classes": [
            "identity_claim_as_fact",
            "overpositive_template",
            "emergency_bypass",
            "cause_claim_without_evidence",
            "fixed_template_surface",
        ],
        "surface_requirement_preference": "self_denial_safe_state_answer_or_existing_safety_path",
        "runtime_owner_mode_id": "self_denial_support",
        "runtime_ratio_owner_reason_id": "self_denial_follow_thickened",
    },
    FAMILY_DAILY_POSITIVE: {
        "policy_id": "p4_4_daily_positive_positive_warmth_without_overanalysis",
        "family": FAMILY_DAILY_POSITIVE,
        "policy_group": "boundary_regression",
        "temperature_profile": TEMP_POSITIVE_WARMTH_NO_OVERANALYSIS,
        "ratio_profile": {
            "observation_ratio_min": 0.20,
            "observation_ratio_max": 0.25,
            "reception_ratio_min": 0.75,
            "reception_ratio_max": 0.80,
            "ratio_intent": "small_positive_change_preserved_without_heavy_analysis",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "positive_event_or_change_observation",
            "reception_section_role": "warm_positive_reception",
            "max_questions": 0,
            "requires_reception_section": True,
            "requires_visible_scope_marker": False,
            "question_only_forbidden": True,
            "question_position": "not_primary",
        },
        "required_anchor_roles": [
            ROLE_POSITIVE_CHANGE_ANCHOR,
            ROLE_EMOTION_DIRECTION_ANCHOR,
            ROLE_EMLIS_RECEPTION_ANCHOR,
        ],
        "forbidden_surface_classes": [
            "overanalysis",
            "cold_observation",
            "generic_applause_only",
            "fixed_template_surface",
        ],
        "surface_requirement_preference": "family_tuned_positive_reception",
        "runtime_owner_mode_id": "daily_positive_reception",
        "runtime_ratio_owner_reason_id": "daily_positive_reception_light",
    },
    FAMILY_RELATIONSHIP_BOUNDARY: {
        "policy_id": "p4_4_relationship_boundary_without_target_judgement",
        "family": FAMILY_RELATIONSHIP_BOUNDARY,
        "policy_group": "boundary_regression",
        "temperature_profile": TEMP_BOUNDARY_OBSERVATION_NO_TARGET_JUDGEMENT,
        "ratio_profile": {
            "observation_ratio_min": 0.45,
            "observation_ratio_max": 0.55,
            "reception_ratio_min": 0.45,
            "reception_ratio_max": 0.55,
            "ratio_intent": "boundary_signal_and_reception_balance",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "boundary_signal_observation",
            "reception_section_role": "distance_or_load_reception",
            "max_questions": 1,
            "requires_reception_section": True,
            "requires_visible_scope_marker": True,
            "question_only_forbidden": True,
            "question_position": "after_reception_optional",
        },
        "required_anchor_roles": [
            ROLE_BOUNDARY_SIGNAL_ANCHOR,
            ROLE_RELATIONSHIP_ANCHOR,
            ROLE_UNRESOLVED_WEIGHT_ANCHOR,
            ROLE_NO_TARGET_JUDGEMENT_MARKER,
            ROLE_EMLIS_RECEPTION_ANCHOR,
        ],
        "forbidden_surface_classes": [
            "other_person_intent_claim",
            "target_judgement_agreement",
            "attack_agreement",
            "cause_claim_without_evidence",
        ],
        "surface_requirement_preference": "labelled_two_stage_boundary_observation",
        "runtime_owner_mode_id": "standard_state_answer",
        "runtime_ratio_owner_reason_id": "anger_standard_with_inner_value_line",
    },
    FAMILY_LOW_INFORMATION_SHORT: {
        "policy_id": "p4_4_low_information_short_limited_scope_reception",
        "family": FAMILY_LOW_INFORMATION_SHORT,
        "policy_group": "boundary_regression",
        "temperature_profile": TEMP_LIMITED_SCOPE_RECEPTION,
        "ratio_profile": {
            "observation_ratio_min": 0.25,
            "observation_ratio_max": 0.35,
            "reception_ratio_min": 0.65,
            "reception_ratio_max": 0.75,
            "ratio_intent": "visible_scope_only_then_gentle_reception",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "visible_scope_only_observation",
            "reception_section_role": "gentle_reception_without_pressure",
            "max_questions": 1,
            "requires_reception_section": True,
            "requires_visible_scope_marker": True,
            "question_only_forbidden": True,
            "question_position": "after_reception_optional",
        },
        "required_anchor_roles": [
            ROLE_VISIBLE_SCOPE_MARKER,
            ROLE_UNKNOWN_SCOPE_MARKER,
            ROLE_EMLIS_RECEPTION_ANCHOR,
        ],
        "forbidden_surface_classes": [
            "deep_read",
            "history_supplementation",
            "question_pressure",
            "cause_claim_without_evidence",
        ],
        "surface_requirement_preference": "low_information_observation_or_reception_required",
        "runtime_owner_mode_id": "low_information_question",
        "runtime_ratio_owner_reason_id": "low_information_light_prompt",
    },
    FAMILY_LIMITED_GROUNDING: {
        "policy_id": "p4_4_limited_grounding_limited_scope_reception",
        "family": FAMILY_LIMITED_GROUNDING,
        "policy_group": "boundary_regression",
        "temperature_profile": TEMP_LIMITED_SCOPE_RECEPTION,
        "ratio_profile": {
            "observation_ratio_min": 0.35,
            "observation_ratio_max": 0.45,
            "reception_ratio_min": 0.55,
            "reception_ratio_max": 0.65,
            "ratio_intent": "limited_visible_scope_then_reception",
        },
        "section_policy": {
            "section_role_sequence": ["observation", "reception"],
            "observation_section_role": "limited_visible_scope_observation",
            "reception_section_role": "limited_grounding_reception",
            "max_questions": 1,
            "requires_reception_section": True,
            "requires_visible_scope_marker": True,
            "question_only_forbidden": True,
            "question_position": "after_reception_optional",
        },
        "required_anchor_roles": [
            ROLE_VISIBLE_SCOPE_MARKER,
            ROLE_LIMITED_GROUNDING_MARKER,
            ROLE_SOFT_INFERENCE_MARKER,
            ROLE_EMLIS_RECEPTION_ANCHOR,
        ],
        "forbidden_surface_classes": [
            "question_only",
            "material_quality_forced_to_eligible",
            "unsupported_claim",
            "source_unavailable_recast_as_normal_rebuild",
        ],
        "surface_requirement_preference": "labelled_two_stage_or_limited_grounding_reception",
        "runtime_owner_mode_id": "limited_grounding_reception",
        "runtime_ratio_owner_reason_id": "limited_grounding_limited_scope",
    },
}

_BOUNDARY_SLICE_POLICY_REGISTRY_20260610: Final[dict[str, dict[str, Any]]] = {
    COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION: {
        "policy_id": "p4_4_source_unavailable_high_information_boundary",
        "coverage_slice": COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION,
        "temperature_profile": TEMP_SOURCE_UNAVAILABLE_FAIL_CLOSED_BOUNDARY,
        "boundary_policy": {
            "source_unavailable_boundary_kept": True,
            "normal_rebuild_forbidden": True,
            "readable_scope_only": True,
            "question_only_forbidden": True,
        },
        "required_anchor_roles": [ROLE_SOURCE_UNAVAILABLE_MARKER, ROLE_VISIBLE_SCOPE_MARKER],
        "forbidden_surface_classes": [
            "source_unavailable_recast_as_normal_rebuild",
            "unsupported_claim",
            "material_quality_forced_to_eligible",
        ],
    },
    COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE: {
        "policy_id": "p4_4_history_line_eligible_hold_current_input_first",
        "coverage_slice": COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE,
        "temperature_profile": TEMP_HISTORY_LINE_HOLD_CURRENT_INPUT_FIRST,
        "boundary_policy": {
            "p5_hold_until_current_only_readfeel_stable": True,
            "history_line_must_not_mask_current_input_gap": True,
            "owned_history_surface_strengthening_applied": False,
        },
        "required_anchor_roles": [ROLE_VISIBLE_SCOPE_MARKER, ROLE_SOFT_INFERENCE_MARKER],
        "forbidden_surface_classes": [
            "history_line_masks_current_input_gap",
            "creepy_history_overclaim",
            "self_blame_amplification",
        ],
    },
}


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 160) -> str:
    text_value = _clean(value) or default
    chars: list[str] = []
    for ch in text_value[:max_length]:
        chars.append(ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-")
    return "".join(chars).strip("-") or default


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)) or isinstance(value, Mapping):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
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
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_TRUE_FLAGS_20260610 and child is True:
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


def assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "p4_family_tuning_policy",
) -> None:
    """Reject body-bearing or runtime-mutating P4-4 policy payloads."""

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
            if not isinstance(item, Mapping):
                raise ValueError(f"{source}[{index}] must be a mapping")
            assert_emlis_ai_product_quality_contract_freeze_meta_only(
                item, source=f"{source}.contract_freeze[{index}]"
            )


def _false_contract_flags() -> dict[str, bool]:
    return {
        "body_free_policy_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
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
        "exact_comment_text_locked": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
        "input_specific_template_added": False,
        "case_specific_runtime_branch": False,
        "case_specific_runtime_condition_allowed": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "runtime_repair_applied": False,
        "implementation_change_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
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
        "external_ai_used": False,
        "local_llm_used": False,
        "schema_file_materialized": False,
        "material_quality_forced_to_eligible": False,
        "source_unavailable_recast_as_normal_rebuild": False,
        "history_line_masks_current_input_gap": False,
        "observation_zero_allowed": False,
        "human_follow_zero_allowed": False,
        "comfort_only_allowed": False,
    }


def _make_policy_item(policy: Mapping[str, Any]) -> dict[str, Any]:
    item = copy.deepcopy(dict(policy))
    ratio_profile = dict(item.get("ratio_profile") or {})
    obs_min = float(ratio_profile.get("observation_ratio_min", 0.0))
    obs_max = float(ratio_profile.get("observation_ratio_max", 0.0))
    rec_min = float(ratio_profile.get("reception_ratio_min", 0.0))
    rec_max = float(ratio_profile.get("reception_ratio_max", 0.0))
    section_policy = dict(item.get("section_policy") or {})
    item.update(
        {
            "schema_version": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_ITEM_VERSION_20260610,
            "source_phase": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
            "ratio_policy_kind": "range_not_exact_character_count",
            "ratio_total_min": round(obs_min + rec_min, 4),
            "ratio_total_max": round(obs_max + rec_max, 4),
            "observation_section_required": True,
            "reception_section_required": bool(section_policy.get("requires_reception_section", True)),
            "question_only_forbidden": bool(section_policy.get("question_only_forbidden", True)),
            "fixed_sentence_template_added": False,
            "case_specific_runtime_branch": False,
            "runtime_branching_uses_fixture_strings": False,
            "p4_runtime_tuning_applied": False,
            "p5_visible_surface_strengthened": False,
            **_false_contract_flags(),
        }
    )
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(item, source=f"p4_4.policy_item.{item.get('policy_id')}")
    return item


def build_product_readfeel_p4_family_policy_registry_20260610() -> list[dict[str, Any]]:
    """Return all P4-4 family policies as body-free rows."""

    rows = [_make_policy_item(policy) for policy in _FAMILY_POLICY_REGISTRY_20260610.values()]
    rows.sort(key=lambda row: (str(row.get("policy_group")), str(row.get("family"))))
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(rows, source="p4_4.family_policy_registry")
    return rows


def get_product_readfeel_p4_family_policy_20260610(family: str) -> dict[str, Any]:
    family_id = _clean(family)
    if family_id not in _FAMILY_POLICY_REGISTRY_20260610:
        raise KeyError(f"unknown P4-4 family policy: {family_id}")
    return _make_policy_item(_FAMILY_POLICY_REGISTRY_20260610[family_id])


def build_product_readfeel_p4_boundary_slice_policy_registry_20260610() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for policy in _BOUNDARY_SLICE_POLICY_REGISTRY_20260610.values():
        row = copy.deepcopy(dict(policy))
        row.update(
            {
                "schema_version": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_ITEM_VERSION_20260610,
                "source_phase": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
                "policy_group": "boundary_slice_regression",
                "fixed_sentence_template_added": False,
                "case_specific_runtime_branch": False,
                "runtime_branching_uses_fixture_strings": False,
                "p4_runtime_tuning_applied": False,
                "p5_visible_surface_strengthened": False,
                **_false_contract_flags(),
            }
        )
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(row, source=f"p4_4.boundary_slice_policy.{row.get('policy_id')}")
        rows.append(row)
    rows.sort(key=lambda row: str(row.get("coverage_slice")))
    return rows


def _selected_cases(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    selected = payload.get("selected_cases") or []
    if isinstance(selected, Sequence) and not isinstance(selected, (str, bytes, bytearray)):
        return [item for item in selected if isinstance(item, Mapping)]
    return []


def _material_audit_events(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    events = payload.get("material_audit_events") or []
    if isinstance(events, Sequence) and not isinstance(events, (str, bytes, bytearray)):
        return [item for item in events if isinstance(item, Mapping)]
    return []


def _family_case_links(
    *,
    target_case_selection_payload: Mapping[str, Any] | None,
    family_policies_by_family: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for case in _selected_cases(target_case_selection_payload):
        case_ref_id = _safe_identifier(case.get("case_ref_id") or case.get("case_id"), default="case-ref")
        family = _clean(case.get("family"))
        policy = family_policies_by_family.get(family)
        if not policy:
            continue
        links.append(
            {
                "case_ref_id": case_ref_id,
                "family": family,
                "policy_id": _clean(policy.get("policy_id")),
                "policy_group": _clean(policy.get("policy_group")),
                "coverage_slices": _dedupe(case.get("coverage_slices") or []),
                "blocker_ids": _dedupe(case.get("blocker_ids") or []),
                "target_layers": _dedupe(case.get("target_layers") or []),
                "raw_input_included": False,
                "comment_text_body_included": False,
                "case_specific_runtime_branch": False,
            }
        )
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(links, source="p4_4.family_case_links")
    return links


def _slice_policy_links(
    *,
    target_case_selection_payload: Mapping[str, Any] | None,
    boundary_policies_by_slice: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for case in _selected_cases(target_case_selection_payload):
        case_ref_id = _safe_identifier(case.get("case_ref_id") or case.get("case_id"), default="case-ref")
        for coverage_slice in _dedupe(case.get("coverage_slices") or []):
            policy = boundary_policies_by_slice.get(coverage_slice)
            if not policy:
                continue
            links.append(
                {
                    "case_ref_id": case_ref_id,
                    "coverage_slice": coverage_slice,
                    "policy_id": _clean(policy.get("policy_id")),
                    "policy_group": "boundary_slice_regression",
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                    "case_specific_runtime_branch": False,
                }
            )
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(links, source="p4_4.slice_policy_links")
    return links


def _summary(
    *,
    family_policies: Sequence[Mapping[str, Any]],
    boundary_slice_policies: Sequence[Mapping[str, Any]],
    family_case_links: Sequence[Mapping[str, Any]],
    slice_policy_links: Sequence[Mapping[str, Any]],
    material_audit_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    policy_groups = Counter(_clean(policy.get("policy_group")) for policy in family_policies)
    linked_families = _dedupe(link.get("family") for link in family_case_links)
    audit_events = _material_audit_events(material_audit_payload)
    rich_input_candidate_count = sum(1 for event in audit_events if event.get("rich_input_candidate") is True)
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610,
        "source_phase": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
        "family_policy_count": len(family_policies),
        "boundary_slice_policy_count": len(boundary_slice_policies),
        "family_policy_groups": dict(policy_groups),
        "main_target_family_ids": [FAMILY_DAILY_UNPLEASANT, FAMILY_STRUCTURE_QUESTION],
        "yellow_review_family_ids": [FAMILY_SELF_DENIAL],
        "boundary_regression_family_ids": [
            FAMILY_LOW_INFORMATION_SHORT,
            FAMILY_DAILY_POSITIVE,
            FAMILY_RELATIONSHIP_BOUNDARY,
            FAMILY_LIMITED_GROUNDING,
        ],
        "boundary_regression_slice_ids": [
            COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION,
            COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE,
        ],
        "linked_family_ids": linked_families,
        "family_case_link_count": len(family_case_links),
        "slice_policy_link_count": len(slice_policy_links),
        "material_audit_connected": bool(audit_events),
        "rich_input_candidate_count_from_material_audit": rich_input_candidate_count,
        "family_temperature_flattened_detection_ready": True,
        "generic_reception_surface_policy_boundary_ready": True,
        "daily_unpleasant_policy_ready": FAMILY_DAILY_UNPLEASANT in [p.get("family") for p in family_policies],
        "structure_question_policy_ready": FAMILY_STRUCTURE_QUESTION in [p.get("family") for p in family_policies],
        "self_denial_yellow_review_policy_ready": FAMILY_SELF_DENIAL in [p.get("family") for p in family_policies],
        "limited_grounding_boundary_policy_ready": FAMILY_LIMITED_GROUNDING in [p.get("family") for p in family_policies],
        "source_unavailable_boundary_policy_ready": bool(
            any(policy.get("coverage_slice") == COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION for policy in boundary_slice_policies)
        ),
        "history_line_current_input_first_hold_ready": bool(
            any(policy.get("coverage_slice") == COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE for policy in boundary_slice_policies)
        ),
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": bool(family_case_links or slice_policy_links),
        "p4_2_material_audit_used_for_context": bool(audit_events),
        "p4_3_surface_requirement_boundary_respected": True,
        "p4_4_family_tuning_policy_ready": True,
        "p5_connection_allowed": False,
        "p5_visible_surface_strengthened": False,
        "p4_runtime_tuning_applied": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(summary, source="p4_4.summary")
    return summary


def build_product_readfeel_p4_family_tuning_policy_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the P4-4 body-free family tuning policy packet."""

    if target_case_selection_payload is not None:
        assert_product_readfeel_p4_target_case_selection_meta_only_20260610(
            target_case_selection_payload, source="p4_4.source_p4_1_target_selection"
        )
    if material_audit_payload is not None:
        assert_product_readfeel_p4_material_audit_meta_only_20260610(
            material_audit_payload, source="p4_4.source_p4_2_material_audit"
        )

    family_policies = build_product_readfeel_p4_family_policy_registry_20260610()
    boundary_slice_policies = build_product_readfeel_p4_boundary_slice_policy_registry_20260610()
    family_policies_by_family = {str(policy.get("family")): policy for policy in family_policies}
    boundary_policies_by_slice = {str(policy.get("coverage_slice")): policy for policy in boundary_slice_policies}
    case_links = _family_case_links(
        target_case_selection_payload=target_case_selection_payload,
        family_policies_by_family=family_policies_by_family,
    )
    slice_links = _slice_policy_links(
        target_case_selection_payload=target_case_selection_payload,
        boundary_policies_by_slice=boundary_policies_by_slice,
    )
    summary = _summary(
        family_policies=family_policies,
        boundary_slice_policies=boundary_slice_policies,
        family_case_links=case_links,
        slice_policy_links=slice_links,
        material_audit_payload=material_audit_payload,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610,
        "run_id": _safe_identifier(run_id, default="p4_4_family_tuning_policy"),
        "source_step": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
        "source_phase": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
        "source": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SOURCE_20260610,
        "policy_profile": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610,
        "family_policies": family_policies,
        "boundary_slice_policies": boundary_slice_policies,
        "family_case_policy_links": case_links,
        "boundary_slice_policy_links": slice_links,
        "runtime_owner_references": copy.deepcopy(list(_RUNTIME_OWNER_REFERENCES_20260610)),
        "runtime_owner_reference_only": True,
        "runtime_policy_connection_applied": False,
        "runtime_mutation_applied_by_p4_4": False,
        "summary": summary,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": bool(target_case_selection_payload),
        "p4_2_material_audit_used_for_context": bool(material_audit_payload),
        "p4_3_surface_requirement_boundary_respected": True,
        "p4_4_family_tuning_policy_ready": True,
        "p5_connection_allowed": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(payload, source="p4_4.policy")
    return payload


def build_product_readfeel_p4_family_tuning_policy_public_summary_20260610(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
        payload, source="p4_4.public_summary_source"
    )
    summary = dict(payload.get("summary") or {})
    public_summary = {
        "schema_version": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610,
        "source_phase": PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
        "run_id": _safe_identifier(payload.get("run_id"), default="p4_4_family_tuning_policy"),
        "policy_profile": _clean(payload.get("policy_profile")),
        "family_policy_count": int(summary.get("family_policy_count") or 0),
        "boundary_slice_policy_count": int(summary.get("boundary_slice_policy_count") or 0),
        "main_target_family_ids": _dedupe(summary.get("main_target_family_ids") or []),
        "yellow_review_family_ids": _dedupe(summary.get("yellow_review_family_ids") or []),
        "boundary_regression_family_ids": _dedupe(summary.get("boundary_regression_family_ids") or []),
        "boundary_regression_slice_ids": _dedupe(summary.get("boundary_regression_slice_ids") or []),
        "family_temperature_flattened_detection_ready": bool(
            summary.get("family_temperature_flattened_detection_ready")
        ),
        "generic_reception_surface_policy_boundary_ready": bool(
            summary.get("generic_reception_surface_policy_boundary_ready")
        ),
        "p4_4_family_tuning_policy_ready": bool(summary.get("p4_4_family_tuning_policy_ready")),
        "p5_connection_allowed": False,
        "p5_visible_surface_strengthened": False,
        "p4_runtime_tuning_applied": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(public_summary, source="p4_4.public_summary")
    return public_summary


def dump_product_readfeel_p4_family_tuning_policy_public_summary_20260610(
    payload: Mapping[str, Any],
) -> str:
    public_summary = build_product_readfeel_p4_family_tuning_policy_public_summary_20260610(payload)
    return json.dumps(public_summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "FAMILY_LIMITED_GROUNDING",
    "COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE",
    "COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_ITEM_VERSION_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610",
    "assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610",
    "build_product_readfeel_p4_boundary_slice_policy_registry_20260610",
    "build_product_readfeel_p4_family_policy_registry_20260610",
    "build_product_readfeel_p4_family_tuning_policy_20260610",
    "build_product_readfeel_p4_family_tuning_policy_public_summary_20260610",
    "dump_product_readfeel_p4_family_tuning_policy_public_summary_20260610",
    "get_product_readfeel_p4_family_policy_20260610",
]
