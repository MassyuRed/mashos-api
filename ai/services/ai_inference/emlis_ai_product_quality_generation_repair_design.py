# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 5 Blocker-specific Generation Repair Design for EmlisAI.

This module turns Phase 4 Blocker Matrix rows into an internal, meta-only
repair design queue.  It does **not** change EmlisAI rendering behavior, does
not add fixed observation sentences, and does not relax public/RN/API/DB/Gate
contracts.  The output is a repair-design material used to decide which
existing generation / repair / surface modules should be adjusted next.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final, NamedTuple

from emlis_ai_product_quality_blocker_matrix import (
    PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION,
    assert_product_quality_blocker_matrix_meta_only,
)
from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_quality_measurement_event import normalize_product_quality_family

PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_VERSION: Final = (
    "cocolon.emlis.product_quality.generation_repair_design.v1"
)
PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_SCHEMA_VERSION: Final = (
    PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_VERSION
)
PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_VERSION: Final = (
    "cocolon.emlis.product_quality.generation_repair_design_row.v1"
)
PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_SCHEMA_VERSION: Final = (
    PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_VERSION
)
PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_PHASE: Final = (
    "Phase5_BlockerSpecificGenerationRepairDesign"
)
PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_TARGET_STEP: Final = (
    "BlockerSpecific_GenerationRepairDesign"
)

FAMILY_ALL: Final = "all"
FAMILY_UNKNOWN: Final = "unknown"

_CORE_PHASE5_TRACKS: Final[tuple[str, ...]] = (
    "display_reach_repair",
    "low_information_repair",
    "daily_mixed_state_answer",
    "binding_reason_grounding_repair",
    "self_denial_safe_state_answer",
    "surface_repetition_template_smell_repair",
    "long_meaning_arc_relationship_structure_repair",
    "user_label_connection_soft_connection_repair",
)

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
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "body",
        "text",
        "sentence",
        "sentences",
        "example",
        "example_text",
        "fixed_comment",
        "completed_sentence",
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
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "fixed_template_added",
        "input_specific_template_added",
        "runtime_fixture_branch_added",
        "runtime_fixture_branch_required",
        "external_ai_used",
        "local_llm_used",
    }
)
_ALLOWED_ROW_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "run_id",
        "design_id",
        "source_blocker_id",
        "source_blocker_group",
        "source_owner_area",
        "family",
        "priority_rank",
        "implementation_order",
        "repair_track",
        "repair_track_group",
        "phase5_applicable",
        "generation_logic_change_required",
        "precondition_or_followup",
        "target_owner_area",
        "candidate_modules",
        "target_metric",
        "target_metric_value",
        "failure_mode_ids",
        "repair_operation_ids",
        "forbidden_operation_ids",
        "acceptance_check_ids",
        "depends_on_tracks",
        "blocked_until_ids",
        "source_sample_row_ids",
        "observed_count",
        "release_blocking",
        "contract_change_allowed",
        "public_contract_change_allowed",
        "gate_relaxation_allowed",
        "fixed_template_allowed",
        "runtime_fixture_branch_allowed",
        "product_gate_ready",
        "public_release_applied",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
    }
)
_ALLOWED_DESIGN_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "version",
        "phase",
        "target_step",
        "run_id",
        "design_status",
        "source_blocker_matrix_schema_version",
        "source_blocker_matrix_row_count",
        "source_blocker_matrix_release_blocking_row_count",
        "contract_freeze",
        "contract_assertions",
        "core_phase5_tracks",
        "rows",
        "generation_repair_work_queue",
        "repair_design_queue",
        "repair_execution_order",
        "phase5_focus_tracks",
        "precondition_tracks",
        "followup_tracks",
        "track_counts",
        "family_counts",
        "target_owner_area_counts",
        "summary",
        "generation_logic_change_required",
        "contract_change_allowed",
        "public_contract_change_allowed",
        "gate_relaxation_allowed",
        "fixed_template_allowed",
        "runtime_fixture_branch_allowed",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "public_response_key_added",
        "response_shape_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
    }
)


class _Track(NamedTuple):
    repair_track: str
    repair_track_group: str
    priority_rank: int
    target_owner_area: str
    candidate_modules: tuple[str, ...]
    failure_mode_ids: tuple[str, ...]
    repair_operation_ids: tuple[str, ...]
    forbidden_operation_ids: tuple[str, ...]
    acceptance_check_ids: tuple[str, ...]
    phase5_applicable: bool = True
    generation_logic_change_required: bool = True
    precondition_or_followup: str = "phase5_generation_repair"
    depends_on_tracks: tuple[str, ...] = ()
    blocked_until_ids: tuple[str, ...] = ()


_COMMON_FORBIDDEN: Final[tuple[str, ...]] = (
    "gate_relaxation",
    "public_response_key_addition",
    "rn_display_contract_relaxation",
    "db_schema_change",
    "fixed_sentence_template",
    "case_specific_runtime_branch",
    "a_c_d_exact_fixture_branch",
    "raw_or_comment_body_in_release_material",
    "machine_metric_read_feeling_autofill",
)
_COMMON_ACCEPTANCE: Final[tuple[str, ...]] = (
    "public_contract_unchanged",
    "rn_contract_unchanged",
    "db_schema_unchanged",
    "gate_thresholds_unchanged",
    "raw_or_comment_body_absent_from_material",
)

_TRACKS: Final[dict[str, _Track]] = {
    "contract_boundary_repair": _Track(
        "contract_boundary_repair",
        "contract_boundary",
        0,
        "public_contract_boundary_and_meta_sanitizer",
        (
            "emlis_ai_product_quality_contract_freeze.py",
            "emlis_ai_product_quality_measurement_event.py",
            "emlis_ai_public_feedback_meta.py",
            "api_emotion_submit.py",
        ),
        ("contract_or_release_flag_leak", "body_payload_key_leak", "schema_boundary_invalid"),
        ("remove_body_payload_keys", "force_release_flags_false", "restore_meta_only_material"),
        _COMMON_FORBIDDEN,
        _COMMON_ACCEPTANCE + ("contract_violation_count_zero",),
        phase5_applicable=False,
        generation_logic_change_required=False,
        precondition_or_followup="precondition_contract_repair",
    ),
    "composer_bootstrap_precondition": _Track(
        "composer_bootstrap_precondition",
        "pre_generation_boundary",
        5,
        "local_product_qa_composer_bootstrap",
        (
            "emlis_ai_composer_client_registry.py",
            "emlis_ai_limited_release_service.py",
            "emlis_ai_product_quality_measurement_runner.py",
        ),
        ("composer_path_closed", "composer_feature_flag_disabled", "rollout_stage_not_internal"),
        ("record_composer_disabled_blocker", "open_local_product_qa_profile_only", "keep_all_rollout_disallowed"),
        _COMMON_FORBIDDEN + ("production_rollout_flag_change", "complete_initial_default_before_ap0_green"),
        _COMMON_ACCEPTANCE + ("composer_generation_path_open_for_local_qa",),
        phase5_applicable=False,
        generation_logic_change_required=False,
        precondition_or_followup="precondition_composer_bootstrap",
    ),
    "display_reach_repair": _Track(
        "display_reach_repair",
        "display_reach",
        10,
        "display_repair_and_gate_recovery",
        (
            "emlis_ai_observation_display_repair_integration.py",
            "emlis_ai_gate_recovery_loop.py",
            "emlis_ai_reply_service.py",
        ),
        ("comment_missing", "public_display_not_reached", "post_final_empty_exit"),
        ("bounded_repair_before_empty_exit", "post_final_gate_recovery", "assertion_softening", "surface_shortening"),
        _COMMON_FORBIDDEN + ("passed_status_without_displayable_material", "meta_only_display_bypass"),
        _COMMON_ACCEPTANCE + ("display_reach_rate_at_or_above_target", "comment_contract_non_empty_when_passed"),
    ),
    "low_information_repair": _Track(
        "low_information_repair",
        "low_information",
        20,
        "display_repair_low_information",
        (
            "emlis_ai_low_information_observation_composer.py",
            "emlis_ai_observation_display_repair_integration.py",
            "emlis_ai_gate_recovery_loop.py",
            "emlis_ai_reply_service.py",
        ),
        ("low_information_empty_exit", "unsupported_event_inference", "generic_comfort_only", "question_only_exit"),
        ("scope_known_observation", "unknown_slots_acknowledgement", "burden_or_unformed_state_surface", "question_not_required_for_display"),
        _COMMON_FORBIDDEN + ("cause_inference", "personality_inference", "future_prediction", "question_only_repair"),
        _COMMON_ACCEPTANCE + ("low_information_display_reach_stable", "unsupported_binding_count_zero", "family_cross_repetition_absent"),
    ),
    "daily_mixed_state_answer": _Track(
        "daily_mixed_state_answer",
        "daily_mixed_state_answer",
        30,
        "state_answer_surface_planner",
        (
            "emlis_ai_state_answer_ratio_policy.py",
            "emlis_ai_two_stage_section_surface_plan.py",
            "emlis_ai_complete_surface_realizer.py",
            "emlis_ai_runtime_surface_tone_engine_2_1.py",
        ),
        ("mirror_only", "generic_comfort_only", "advice_surface", "personality_claim"),
        ("state_answer_ratio_apply", "environment_state_output_binding", "human_follow_as_observation_temperature", "advice_suppression"),
        _COMMON_FORBIDDEN + ("diagnosis", "personality_claim", "action_advice_default", "emotion_label_echo_only"),
        _COMMON_ACCEPTANCE + ("mirror_only_absent", "generic_comfort_absent", "input_condition_binding_present"),
    ),
    "binding_reason_grounding_repair": _Track(
        "binding_reason_grounding_repair",
        "grounding_and_reasoning",
        40,
        "evidence_ledger_relation_reason_planner",
        (
            "emlis_ai_evidence_ledger_service.py",
            "emlis_ai_shared_reception_evidence.py",
            "emlis_ai_complete_sentence_planner.py",
            "emlis_ai_complete_relation_graph_service.py",
            "emlis_ai_grounding_judge.py",
        ),
        ("unsupported_binding", "reason_gap", "relation_without_evidence", "overwide_assertion"),
        ("sentence_binding_narrowing", "reason_clause_from_input_relation", "unsupported_assertion_drop", "grounding_scope_reduce"),
        _COMMON_FORBIDDEN + ("reason_fabrication", "personality_tendency_from_single_input", "history_fact_as_current_event"),
        _COMMON_ACCEPTANCE + ("binding_pass_rate_at_or_above_target", "reason_coverage_complete", "unsupported_binding_count_zero"),
    ),
    "self_denial_safe_state_answer": _Track(
        "self_denial_safe_state_answer",
        "self_denial_safety",
        50,
        "self_denial_safe_state_answer_and_safety_triage",
        (
            "emlis_ai_safety_triage.py",
            "emlis_ai_self_denial_safe_state_answer.py",
            "emlis_ai_state_answer_special_cases.py",
            "emlis_ai_state_answer_gate_boundary.py",
            "emlis_ai_gate_recovery_loop.py",
        ),
        ("self_denial_fact_acceptance", "over_safety_blocking", "emergency_miss", "generic_encouragement"),
        ("self_denial_not_fact_surface", "self_denial_as_felt_state_not_fact", "emergency_boundary_split", "safe_state_answer_route", "non_emergency_display_repair"),
        _COMMON_FORBIDDEN + ("identity_claim_validation", "self_denial_identity_confirmation", "emergency_to_normal_pass_conversion", "blanket_safety_block"),
        _COMMON_ACCEPTANCE + ("self_denial_not_fact_confirmed", "emergency_boundary_preserved", "non_emergency_display_not_empty"),
    ),
    "surface_repetition_template_smell_repair": _Track(
        "surface_repetition_template_smell_repair",
        "surface_repetition_template",
        60,
        "surface_realizer_anti_template",
        (
            "emlis_ai_complete_surface_realizer_anti_template.py",
            "emlis_ai_complete_surface_quality_signature.py",
            "emlis_ai_runtime_surface_tone_engine_2_1.py",
            "emlis_ai_mirror_only_surface_detector.py",
            "emlis_ai_complete_sentence_planner.py",
        ),
        ("family_cross_same_skeleton", "generic_opening_repeat", "mirror_only", "fixed_fallback_smell"),
        ("component_signature_diversification", "family_specific_relation_axis", "state_word_specificity", "anti_template_pre_return_check"),
        _COMMON_FORBIDDEN + ("opening_only_variation", "completed_sentence_bank", "fixture_phrase_trigger"),
        _COMMON_ACCEPTANCE + ("surface_signature_repetition_zero", "fixed_template_absent", "blind_qa_non_template_at_target"),
    ),
    "long_meaning_arc_relationship_structure_repair": _Track(
        "long_meaning_arc_relationship_structure_repair",
        "long_meaning_structure",
        70,
        "structure_insight_gate_and_surface",
        (
            "emlis_ai_structure_insight_candidate.py",
            "emlis_ai_structure_insight_gate.py",
            "emlis_ai_structure_insight_surface.py",
            "emlis_ai_complete_surface_quality_signature.py",
            "emlis_ai_complete_sentence_planner.py",
        ),
        ("long_input_summary_only", "abstract_deep_sounding", "relation_overclaim", "forced_structure_insight"),
        ("relation_state_output_axis_select", "allowed_family_insight_only", "soft_expression_enforce", "summary_to_structure_shift"),
        _COMMON_FORBIDDEN + ("relationship_decision_claim", "diagnosis", "single_record_tendency", "daily_short_deep_insight"),
        _COMMON_ACCEPTANCE + ("overclaim_absent", "unsafe_insight_absent", "required_insight_family_only"),
    ),
    "user_label_connection_soft_connection_repair": _Track(
        "user_label_connection_soft_connection_repair",
        "user_label_connection",
        80,
        "user_label_connection_material_gate_surface_qa",
        (
            "emlis_ai_user_label_connection_material.py",
            "emlis_ai_user_label_connection_gate.py",
            "emlis_ai_user_label_connection_surface.py",
            "emlis_ai_user_label_connection_product_quality_qa.py",
        ),
        ("creepy_history_connection", "overclaim_or_deciding", "self_blame_amplification", "shallow_history_repeat"),
        ("current_input_first_connection", "limited_visible_connection_only", "history_softening", "creepy_overclaim_gate_enforce"),
        _COMMON_FORBIDDEN + ("identity_label_claim", "history_decides_current_user", "raw_history_exposure"),
        _COMMON_ACCEPTANCE + ("creepy_absence_at_target", "overclaim_absence_at_target", "self_blame_non_amplification_at_target"),
    ),
    "blind_qa_followup_required": _Track(
        "blind_qa_followup_required",
        "blind_qa_followup",
        90,
        "runtime_surface_blind_qa_review_flow",
        (
            "emlis_ai_runtime_surface_blind_qa_long_run.py",
            "emlis_ai_product_readfeel_scorecard.py",
            "emlis_ai_user_label_connection_product_quality_qa.py",
        ),
        ("blind_qa_missing", "read_feeling_unreviewed", "non_template_unreviewed"),
        ("create_reviewable_candidate_set", "ratings_only_review_ingest", "block_release_until_coverage_complete"),
        _COMMON_FORBIDDEN + ("machine_read_feeling_substitution", "review_comment_body_import_to_release_material"),
        _COMMON_ACCEPTANCE + ("blind_qa_coverage_complete", "runtime_read_feeling_at_target", "red_review_count_zero"),
        phase5_applicable=False,
        generation_logic_change_required=False,
        precondition_or_followup="followup_blind_qa_required",
    ),
    "long_run_stability_followup": _Track(
        "long_run_stability_followup",
        "phase11_long_run_followup",
        100,
        "long_run_product_gate_material_and_input_set",
        (
            "emlis_ai_product_readfeel_long_run_product_gate.py",
            "emlis_ai_runtime_surface_blind_qa_long_run.py",
            "emlis_ai_product_quality_measurement_runner.py",
        ),
        ("phase11_not_green", "required_family_incomplete", "consecutive_pass_not_observed"),
        ("rerun_after_generation_repairs", "required_family_input_coverage", "long_run_repetition_monitor"),
        _COMMON_FORBIDDEN + ("phase11_product_gate_ready_direct_set", "release_flag_inside_phase11"),
        _COMMON_ACCEPTANCE + ("five_consecutive_product_pass", "ten_consecutive_product_pass", "family_cross_repetition_absent"),
        phase5_applicable=False,
        generation_logic_change_required=False,
        precondition_or_followup="followup_long_run_stability",
    ),
    "manual_triage_mapping_required": _Track(
        "manual_triage_mapping_required",
        "unmapped_product_quality_blocker",
        120,
        "product_quality_measurement_triage",
        (
            "emlis_ai_product_quality_blocker_matrix.py",
            "emlis_ai_product_quality_generation_repair_design.py",
        ),
        ("unmapped_blocker", "owner_area_unknown", "repair_policy_unknown"),
        ("classify_unknown_blocker", "classify_blocker_before_generation_change", "add_owner_area_mapping", "add_acceptance_checks"),
        _COMMON_FORBIDDEN + ("fixture_specific_patch", "guess_generation_owner", "gate_relaxation_as_shortcut"),
        _COMMON_ACCEPTANCE + ("blocker_has_owner_area", "blocker_has_repair_policy"),
        phase5_applicable=False,
        generation_logic_change_required=False,
        precondition_or_followup="precondition_manual_triage",
    ),
}


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _listify(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _safe_identifier(value: Any, *, max_length: int = 128, default: str = "") -> str:
    text = _clean(value)
    if not text:
        return default
    text = text[:max_length]
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"
    if any(ch not in allowed for ch in text):
        return default
    return text


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_family(value: Any) -> str:
    if value in {FAMILY_ALL, FAMILY_UNKNOWN}:
        return str(value)
    return normalize_product_quality_family(value) or FAMILY_UNKNOWN


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(child) for child in value)
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


def _track_id_for_matrix_row(row: Mapping[str, Any]) -> str:
    family = _normalize_family(row.get("family"))
    group = _safe_identifier(row.get("blocker_group"), max_length=96, default="")
    blocker = _safe_identifier(row.get("blocker_id"), max_length=128, default="")
    owner = _safe_identifier(row.get("likely_owner_area"), max_length=128, default="")
    low_families = {"low_information_short", "positive_only"}
    daily_families = {"daily_unpleasant", "daily_positive", "uncertainty", "mixed_emotion"}
    long_structure_families = {
        "long_meaning_arc",
        "relationship_boundary",
        "structure_question",
        "self_understanding_follow",
    }
    family_generation_groups = {"display_reach", "binding", "reason_coverage", "low_information", "structure_insight"}

    # Contract/precondition/follow-up blockers must not be swallowed by a
    # family-level generation repair.  For example, a Blind QA row can be
    # attached to self_denial family, but it still belongs to the review-flow
    # follow-up track rather than a self-denial generation rewrite.
    if group == "contract_leakage" or "contract" in blocker or "forbidden" in blocker or "schema" in blocker:
        return "contract_boundary_repair"
    if group == "composer_bootstrap" or "composer" in blocker or "composer" in owner:
        return "composer_bootstrap_precondition"
    if group == "blind_qa" or "blind_qa" in blocker or "read_feeling" in blocker:
        return "blind_qa_followup_required"
    if group == "phase11_long_run" or "phase11" in blocker or "consecutive" in blocker or "family_coverage" in blocker:
        return "long_run_stability_followup"
    if group == "user_label_connection" or "user_label" in blocker or "history_connection" in blocker or "overclaim" in blocker or "creepy" in blocker:
        return "user_label_connection_soft_connection_repair"
    if group == "structure_insight" or "structure_insight" in blocker or "forced_insight" in blocker:
        return "long_meaning_arc_relationship_structure_repair"

    if family == "self_denial" or group == "self_denial_safety" or "self_denial" in blocker or "safety" in blocker:
        return "self_denial_safe_state_answer"
    if group == "surface_repetition_template" or "template" in blocker or "repeat" in blocker or "mirror" in blocker or "shallow" in blocker:
        return "surface_repetition_template_smell_repair"
    if group == "low_information" or family in low_families:
        return "low_information_repair"
    if family in daily_families and (
        group in family_generation_groups
        or "display" in blocker
        or "comment" in blocker
        or "binding" in blocker
        or "reason" in blocker
    ):
        return "daily_mixed_state_answer"
    if family in long_structure_families:
        return "long_meaning_arc_relationship_structure_repair"
    if group in {"binding", "reason_coverage"} or "binding" in blocker or "reason" in blocker or "grounding" in blocker:
        return "binding_reason_grounding_repair"
    if group == "display_reach" or "display" in blocker or "comment" in blocker or "observation_status" in blocker:
        return "display_reach_repair"
    return "manual_triage_mapping_required"

def _track_for_matrix_row(row: Mapping[str, Any]) -> _Track:
    return _TRACKS[_track_id_for_matrix_row(row)]


def _target_metric(row: Mapping[str, Any], track: _Track) -> tuple[str, float | int]:
    metric = _safe_identifier(row.get("target_metric"), max_length=96, default="")
    value = row.get("target_metric_value")
    if metric:
        if isinstance(value, int):
            return metric, value
        if isinstance(value, float):
            return metric, value
        try:
            return metric, float(value)
        except (TypeError, ValueError):
            pass
    if track.repair_track == "display_reach_repair":
        return "display_reach_rate", 0.9
    if track.repair_track == "low_information_repair":
        return "low_information_display_reach_rate", 0.9
    if track.repair_track == "binding_reason_grounding_repair":
        return "binding_and_reason_quality", 1.0
    if track.repair_track == "surface_repetition_template_smell_repair":
        return "surface_repetition_count", 0
    if track.repair_track == "self_denial_safe_state_answer":
        return "self_denial_safety_violation_count", 0
    if track.repair_track == "blind_qa_followup_required":
        return "blind_qa_review_coverage_rate", 1.0
    if track.repair_track == "long_run_stability_followup":
        return "long_run_product_pass", 1.0
    return "repair_track_acceptance", 1.0


def _build_design_row(*, run_id: str, row: Mapping[str, Any], index: int) -> dict[str, Any]:
    track = _track_for_matrix_row(row)
    metric, metric_value = _target_metric(row, track)
    source_blocker_id = _safe_identifier(row.get("blocker_id"), max_length=128, default="unknown_blocker")
    family = _normalize_family(row.get("family"))
    candidate_modules = _dedupe(tuple(row.get("candidate_modules") or ()) + tuple(track.candidate_modules))
    repair_row = {
        "schema_version": PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_VERSION,
        "run_id": _safe_identifier(run_id, max_length=96, default="product_quality_run"),
        "design_id": f"phase5_{index:03d}_{track.repair_track}",
        "source_blocker_id": source_blocker_id,
        "source_blocker_group": _safe_identifier(row.get("blocker_group"), max_length=96, default="unmapped_product_quality_blocker"),
        "source_owner_area": _safe_identifier(row.get("likely_owner_area"), max_length=128, default="product_quality_measurement_triage"),
        "family": family,
        "priority_rank": int(track.priority_rank),
        "implementation_order": int(index),
        "repair_track": track.repair_track,
        "repair_track_group": track.repair_track_group,
        "phase5_applicable": bool(track.phase5_applicable),
        "generation_logic_change_required": bool(track.generation_logic_change_required),
        "precondition_or_followup": track.precondition_or_followup,
        "target_owner_area": track.target_owner_area,
        "candidate_modules": candidate_modules,
        "target_metric": metric,
        "target_metric_value": metric_value,
        "failure_mode_ids": list(track.failure_mode_ids),
        "repair_operation_ids": list(track.repair_operation_ids),
        "forbidden_operation_ids": list(track.forbidden_operation_ids),
        "acceptance_check_ids": list(track.acceptance_check_ids),
        "depends_on_tracks": list(track.depends_on_tracks),
        "blocked_until_ids": list(track.blocked_until_ids),
        "source_sample_row_ids": _dedupe(row.get("sample_row_ids"))[:8],
        "observed_count": max(0, _to_int(row.get("observed_count"))),
        "release_blocking": row.get("release_blocking") is not False,
        "contract_change_allowed": False,
        "public_contract_change_allowed": False,
        "gate_relaxation_allowed": False,
        "fixed_template_allowed": False,
        "runtime_fixture_branch_allowed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert_product_quality_generation_repair_design_row_meta_only(repair_row)
    return repair_row


def _extract_matrix_rows(
    *,
    blocker_matrix: Mapping[str, Any] | None = None,
    blocker_matrix_rows: Sequence[Mapping[str, Any]] | None = None,
    repair_work_queue: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if isinstance(blocker_matrix, Mapping):
        assert_product_quality_blocker_matrix_meta_only(blocker_matrix)
        rows = blocker_matrix.get("repair_work_queue") or blocker_matrix.get("rows") or []
    elif repair_work_queue is not None:
        rows = repair_work_queue
    else:
        rows = blocker_matrix_rows or []
    return [dict(row) for row in rows if isinstance(row, Mapping)]


def build_product_quality_generation_repair_design(
    *,
    run_id: Any = "",
    blocker_matrix: Mapping[str, Any] | None = None,
    blocker_matrix_rows: Sequence[Mapping[str, Any]] | None = None,
    repair_work_queue: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build Phase 5 repair design material from Phase 4 blocker rows.

    The returned material is safe to persist as internal QA metadata.  It is not
    a renderer patch and it intentionally carries operation identifiers rather
    than completed user-visible wording.
    """

    source_rows = _extract_matrix_rows(
        blocker_matrix=blocker_matrix,
        blocker_matrix_rows=blocker_matrix_rows,
        repair_work_queue=repair_work_queue,
    )
    run_id_value = _safe_identifier(
        run_id or (blocker_matrix or {}).get("run_id") if isinstance(blocker_matrix, Mapping) else run_id,
        max_length=96,
        default="product_quality_run",
    )
    design_rows = [_build_design_row(run_id=run_id_value, row=row, index=index) for index, row in enumerate(source_rows, start=1)]
    design_rows.sort(key=lambda item: (int(item["priority_rank"]), str(item["repair_track"]), str(item["source_blocker_id"]), str(item["family"])))
    for index, row in enumerate(design_rows, start=1):
        row["implementation_order"] = index
        assert_product_quality_generation_repair_design_row_meta_only(row)

    track_counts = Counter(str(row["repair_track"]) for row in design_rows)
    family_counts = Counter(str(row["family"]) for row in design_rows)
    owner_counts = Counter(str(row["target_owner_area"]) for row in design_rows)
    execution_order = _dedupe(row.get("repair_track") for row in design_rows)
    phase5_focus_tracks = [track for track in execution_order if track in _CORE_PHASE5_TRACKS]
    precondition_tracks = [track for track in execution_order if track not in _CORE_PHASE5_TRACKS and _TRACKS.get(track, _TRACKS["manual_triage_mapping_required"]).precondition_or_followup.startswith("precondition")]
    followup_tracks = [track for track in execution_order if track not in _CORE_PHASE5_TRACKS and track not in precondition_tracks]
    generation_rows = [row for row in design_rows if row.get("generation_logic_change_required") is True]
    source_schema = ""
    source_row_count = len(source_rows)
    source_release_blocking_count = sum(1 for row in source_rows if row.get("release_blocking") is not False)
    if isinstance(blocker_matrix, Mapping):
        source_schema = _safe_identifier(blocker_matrix.get("schema_version"), max_length=128, default="")
        source_row_count = _to_int(blocker_matrix.get("row_count"), default=source_row_count)
        source_release_blocking_count = _to_int(blocker_matrix.get("release_blocking_row_count"), default=source_release_blocking_count)

    summary = {
        "row_count": len(design_rows),
        "generation_repair_row_count": len(generation_rows),
        "phase5_focus_track_count": len(phase5_focus_tracks),
        "precondition_track_count": len(precondition_tracks),
        "followup_track_count": len(followup_tracks),
        "track_counts": dict(sorted(track_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "target_owner_area_counts": dict(sorted(owner_counts.items())),
        "contract_change_required": False,
        "gate_relaxation_required": False,
        "fixed_template_required": False,
        "runtime_fixture_branch_required": False,
    }

    design = {
        "schema_version": PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_VERSION,
        "version": PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_VERSION,
        "phase": PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_PHASE,
        "target_step": PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_TARGET_STEP,
        "run_id": run_id_value,
        "design_status": "ready" if design_rows else "no_blocker_matrix_rows",
        "source_blocker_matrix_schema_version": source_schema or PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION,
        "source_blocker_matrix_row_count": int(source_row_count),
        "source_blocker_matrix_release_blocking_row_count": int(source_release_blocking_count),
        "contract_freeze": build_emlis_ai_product_quality_contract_freeze(),
        "contract_assertions": {
            "api_route_changed": False,
            "response_shape_changed": False,
            "public_response_key_added": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
        },
        "core_phase5_tracks": list(_CORE_PHASE5_TRACKS),
        "rows": design_rows,
        "generation_repair_work_queue": design_rows,
        "repair_design_queue": design_rows,
        "repair_execution_order": execution_order,
        "phase5_focus_tracks": phase5_focus_tracks,
        "precondition_tracks": precondition_tracks,
        "followup_tracks": followup_tracks,
        "track_counts": dict(sorted(track_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "target_owner_area_counts": dict(sorted(owner_counts.items())),
        "summary": summary,
        "generation_logic_change_required": bool(generation_rows),
        "contract_change_allowed": False,
        "public_contract_change_allowed": False,
        "gate_relaxation_allowed": False,
        "fixed_template_allowed": False,
        "runtime_fixture_branch_allowed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }
    assert_product_quality_generation_repair_design_meta_only(design)
    return design


def build_product_quality_generation_repair_design_from_measurement_run(run: Mapping[str, Any]) -> dict[str, Any]:
    blocker_matrix = run.get("blocker_matrix") if isinstance(run, Mapping) and isinstance(run.get("blocker_matrix"), Mapping) else {}
    return build_product_quality_generation_repair_design(
        run_id=run.get("run_id") if isinstance(run, Mapping) else "",
        blocker_matrix=blocker_matrix,
    )


def assert_product_quality_generation_repair_design_row_meta_only(row: Mapping[str, Any]) -> None:
    if not isinstance(row, Mapping):
        raise ValueError("generation repair design row must be a mapping")
    extra = set(row.keys()) - set(_ALLOWED_ROW_KEYS)
    if extra:
        raise ValueError(f"generation repair design row contains unsupported keys: {sorted(extra)}")
    if row.get("schema_version") != PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_VERSION:
        raise ValueError("generation repair design row has invalid schema_version")
    if not _safe_identifier(row.get("design_id"), max_length=128, default=""):
        raise ValueError("generation repair design row requires design_id")
    if not _safe_identifier(row.get("repair_track"), max_length=128, default=""):
        raise ValueError("generation repair design row requires repair_track")
    if not _safe_identifier(row.get("target_owner_area"), max_length=128, default=""):
        raise ValueError("generation repair design row requires target_owner_area")
    for key in (
        "contract_change_allowed",
        "public_contract_change_allowed",
        "gate_relaxation_allowed",
        "fixed_template_allowed",
        "runtime_fixture_branch_allowed",
        "product_gate_ready",
        "public_release_applied",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
    ):
        if row.get(key) is not False:
            raise ValueError(f"generation repair design row {key} must be false")
    if _contains_text_payload_key(row):
        raise ValueError("generation repair design row contains a forbidden text payload key")
    flag_path = _forbidden_true_flag_path(row, path="generation_repair_design_row")
    if flag_path:
        raise ValueError(f"generation repair design row marks forbidden flag true at {flag_path}")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(row, source="emlis_ai_product_quality_generation_repair_design_row")


def assert_product_quality_generation_repair_design_meta_only(design: Mapping[str, Any]) -> None:
    if not isinstance(design, Mapping):
        raise ValueError("generation repair design must be a mapping")
    extra = set(design.keys()) - set(_ALLOWED_DESIGN_KEYS)
    if extra:
        raise ValueError(f"generation repair design contains unsupported keys: {sorted(extra)}")
    if design.get("schema_version") != PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_VERSION:
        raise ValueError("generation repair design has invalid schema_version")
    if design.get("product_gate_ready") is not False:
        raise ValueError("generation repair design must keep product_gate_ready false")
    if design.get("public_release_applied") is not False:
        raise ValueError("generation repair design must keep public_release_applied false")
    if design.get("generation_repair_work_queue") != design.get("rows"):
        raise ValueError("generation_repair_work_queue must mirror rows")
    if design.get("repair_design_queue") != design.get("rows"):
        raise ValueError("repair_design_queue must mirror rows")
    for key in (
        "contract_change_allowed",
        "public_contract_change_allowed",
        "gate_relaxation_allowed",
        "fixed_template_allowed",
        "runtime_fixture_branch_allowed",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "public_response_key_added",
        "response_shape_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
    ):
        if design.get(key) is not False:
            raise ValueError(f"generation repair design {key} must be false")
    for row in design.get("rows") or []:
        assert_product_quality_generation_repair_design_row_meta_only(row)
    if _contains_text_payload_key(design):
        raise ValueError("generation repair design contains a forbidden text payload key")
    flag_path = _forbidden_true_flag_path(design, path="generation_repair_design")
    if flag_path:
        raise ValueError(f"generation repair design marks forbidden flag true at {flag_path}")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(design, source="emlis_ai_product_quality_generation_repair_design")


def dump_product_quality_generation_repair_design(design: Mapping[str, Any]) -> str:
    assert_product_quality_generation_repair_design_meta_only(design)
    return json.dumps(design, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_PHASE",
    "PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_SCHEMA_VERSION",
    "PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_VERSION",
    "PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_SCHEMA_VERSION",
    "PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_TARGET_STEP",
    "PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_VERSION",
    "assert_product_quality_generation_repair_design_meta_only",
    "assert_product_quality_generation_repair_design_row_meta_only",
    "build_product_quality_generation_repair_design",
    "build_product_quality_generation_repair_design_from_measurement_run",
    "dump_product_quality_generation_repair_design",
]
