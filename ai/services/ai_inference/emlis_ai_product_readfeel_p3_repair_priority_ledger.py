# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-6 Repair Priority Ledger for EmlisAI Product Read Feel baseline.

P3-6 consumes body-free P3-4 verdict rows and P3-5 ratings-only review rows,
then fixes the first repair targets without changing runtime behaviour.  The
ledger is intentionally meta-only: it records safe identifiers, counts,
blockers, target layers, candidate files, and forbidden fix paths, but it never
keeps raw input, rendered ``comment_text`` bodies, or candidate display bodies.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from emlis_ai_product_readfeel_p3_blind_qa_ratings_review import (
    PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609,
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609,
    VERDICT_LAYER_NOT_EVALUATED,
    VERDICT_LAYER_P1_DISPLAY_REPAIR,
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_PASS,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
    assert_product_readfeel_p3_verdict_split_meta_only_20260609,
)
from emlis_ai_product_readfeel_rubric import (
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_READ_FEELING,
    PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
    assert_product_readfeel_rubric_meta_only,
)

PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.repair_priority_ledger.20260609.v1"
)
PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_ITEM_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.repair_priority_ledger_item.20260609.v1"
)
PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609: Final = (
    "cocolon.emlis.product_readfeel.p3.repair_priority_ledger_summary.20260609.v1"
)
PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609: Final = (
    "P3-6_Repair_Priority_Ledger"
)
PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SOURCE_20260609: Final = (
    "Cocolon_EmlisAI_P3_ProductReadFeel_RepairPriorityLedger_20260609"
)
PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_PROFILE_20260609: Final = (
    "local_product_readfeel_p3_repair_priority_ledger"
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
        "external_ai_used",
        "local_llm_used",
    }
)

VERDICT_PRIORITY_ORDER_20260609: Final[tuple[str, ...]] = (
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P1_DISPLAY_REPAIR,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
    VERDICT_LAYER_P3_PASS,
    VERDICT_LAYER_NOT_EVALUATED,
)
BLOCKER_PRIORITY_ORDER_20260609: Final[tuple[str, ...]] = (
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
    "self_denial_identity_claim_risk",
    "relationship_target_judgement_risk",
    "structure_question_answered_as_comfort",
    "positive_overweighted",
    "positive_underreceived",
    "structure_insight_gap",
    "p3_inventory_repair_required",
    "p3_readfeel_gap",
    "p3_yellow_readfeel_weakness",
    "manual_review",
)
BLOCKER_CATEGORY_BY_ID_20260609: Final[dict[str, str]] = {
    "contract_violation": "p2_contract_or_surface_safety",
    "surface_breakage": "p2_contract_or_surface_safety",
    "product_surface_invalid": "p2_contract_or_surface_safety",
    "public_display_not_reached": "p1_display_repair",
    "comment_text_missing": "p1_display_repair",
    "rich_input_low_information_overroute": "p3_current_input_core_retention",
    "input_core_missing": "p3_current_input_core_retention",
    "event_reaction_missing": "p3_current_input_core_retention",
    "desire_fear_conflict_missing": "p3_current_input_core_retention",
    "state_structure_missing": "p3_current_input_core_retention",
    "limited_grounding_collapsed_to_question": "p3_limited_grounding_reception",
    "generic_reception_surface": "p3_generic_or_repeated_surface",
    "repeated_surface_signature": "p3_generic_or_repeated_surface",
    "family_temperature_flattened": "p3_family_temperature",
    "self_denial_identity_claim_risk": "p2_contract_or_surface_safety",
    "relationship_target_judgement_risk": "p2_contract_or_surface_safety",
    "structure_question_answered_as_comfort": "p3_family_temperature",
    "positive_overweighted": "p3_family_temperature",
    "positive_underreceived": "p3_family_temperature",
    "structure_insight_gap": "p6_structure_insight_backlog",
    "history_line_masks_current_input_gap": "p5_history_line_backlog",
    "p3_inventory_repair_required": "p3_current_input_core_retention",
    "p3_readfeel_gap": "p3_generic_or_repeated_surface",
    "p3_yellow_readfeel_weakness": "p3_generic_or_repeated_surface",
    "manual_review": "manual_review",
}
TARGET_LAYERS_BY_BLOCKER_20260609: Final[dict[str, tuple[str, ...]]] = {
    "contract_violation": ("public_boundary_contract", "p0_p1_contract_freeze"),
    "surface_breakage": ("visible_surface_acceptance_gate", "surface_realizer", "p2_surface_safety"),
    "product_surface_invalid": ("product_surface_validation", "visible_surface_acceptance_gate"),
    "public_display_not_reached": ("emotion_submit_public_feedback_boundary", "display_contract"),
    "comment_text_missing": ("emotion_submit_public_feedback_boundary", "renderer_output_capture"),
    "rich_input_low_information_overroute": (
        "input_material_bundle",
        "material_quality",
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
    "generic_reception_surface": ("phrase_unit_selection", "surface_realizer", "template_echo_guard"),
    "repeated_surface_signature": ("surface_signature_detector", "phrase_variation", "closing_policy"),
    "family_temperature_flattened": (
        "reception_mode_resolver",
        "state_answer_ratio_policy",
        "two_stage_section_surface_plan",
    ),
    "self_denial_identity_claim_risk": (
        "self_denial_special_cases",
        "state_answer_gate",
        "safety_adjacent_boundary",
    ),
    "relationship_target_judgement_risk": (
        "relationship_boundary_surface",
        "target_judgement_guard",
        "evidence_boundary",
    ),
    "structure_question_answered_as_comfort": (
        "structure_question_observation_mode",
        "structure_insight_candidate_backlog",
    ),
    "positive_overweighted": ("daily_positive_ratio_policy", "family_temperature"),
    "positive_underreceived": ("daily_positive_ratio_policy", "family_temperature"),
    "structure_insight_gap": ("mirror_only_surface_detector", "structure_insight_candidate_backlog"),
    "history_line_masks_current_input_gap": (
        "user_label_connection_visible_surface_binding",
        "current_input_anchor_requirement",
    ),
    "p3_inventory_repair_required": ("product_readfeel_current_output_inventory",),
    "p3_readfeel_gap": ("surface_plan", "surface_realizer", "blind_qa_review"),
    "p3_yellow_readfeel_weakness": ("family_tuning_backlog", "blind_qa_review"),
    "manual_review": ("manual_review",),
}
TARGET_FILE_CANDIDATES_BY_LAYER_20260609: Final[dict[str, tuple[str, ...]]] = {
    "input_material_bundle": (
        "mashos-api/ai/services/ai_inference/emlis_ai_current_input_bundle.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_input_material_bundle.py",
    ),
    "material_quality": ("mashos-api/ai/services/ai_inference/emlis_ai_input_material_bundle.py",),
    "public_surface_requirement": (
        "mashos-api/ai/services/ai_inference/emlis_ai_public_surface_requirement.py",
    ),
    "gate_recovery_route": (
        "mashos-api/ai/services/ai_inference/emlis_ai_gate_recovery_loop.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py",
    ),
    "limited_grounding_reception_surface": (
        "mashos-api/ai/services/ai_inference/emlis_ai_limited_grounding_reception_surface.py",
    ),
    "low_information_observation_composer": (
        "mashos-api/ai/services/ai_inference/emlis_ai_low_information_observation_composer.py",
    ),
    "question_dominance_guard": (
        "mashos-api/ai/services/ai_inference/emlis_ai_question_dominance_guard.py",
    ),
    "surface_plan": (
        "mashos-api/ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
    ),
    "surface_realizer": (
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_labelled_two_stage_surface_recomposition.py",
    ),
    "phrase_unit_selection": (
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
    ),
    "template_echo_guard": (
        "mashos-api/ai/services/ai_inference/emlis_ai_template_echo_guard.py",
    ),
    "surface_signature_detector": (
        "mashos-api/ai/services/ai_inference/emlis_ai_mirror_only_surface_detector.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_template_echo_guard.py",
    ),
    "phrase_variation": (
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
    ),
    "closing_policy": (
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
    ),
    "reception_mode_resolver": (
        "mashos-api/ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
    ),
    "state_answer_ratio_policy": (
        "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_ratio_policy.py",
    ),
    "two_stage_section_surface_plan": (
        "mashos-api/ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
    ),
    "self_denial_special_cases": (
        "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_special_cases.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_self_denial_safe_state_answer.py",
    ),
    "state_answer_gate": (
        "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_gate_boundary.py",
    ),
    "safety_adjacent_boundary": (
        "mashos-api/ai/services/ai_inference/emlis_ai_safety_boundary_service.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_safety_triage.py",
    ),
    "relationship_boundary_surface": (
        "mashos-api/ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
    ),
    "target_judgement_guard": (
        "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py",
    ),
    "evidence_boundary": (
        "mashos-api/ai/services/ai_inference/emlis_ai_user_fact_grounding_boundary.py",
    ),
    "structure_question_observation_mode": (
        "mashos-api/ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_two_stage_section_surface_plan.py",
    ),
    "structure_insight_candidate_backlog": (
        "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_candidate.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_gate.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_structure_insight_surface.py",
    ),
    "daily_positive_ratio_policy": (
        "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_ratio_policy.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
    ),
    "family_temperature": (
        "mashos-api/ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_ratio_policy.py",
    ),
    "mirror_only_surface_detector": (
        "mashos-api/ai/services/ai_inference/emlis_ai_mirror_only_surface_detector.py",
    ),
    "user_label_connection_visible_surface_binding": (
        "mashos-api/ai/services/ai_inference/emlis_ai_user_label_connection_surface.py",
    ),
    "current_input_anchor_requirement": (
        "mashos-api/ai/services/ai_inference/emlis_ai_user_label_connection_candidate.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_user_label_connection_gate.py",
    ),
    "product_readfeel_current_output_inventory": (
        "mashos-api/ai/services/ai_inference/emlis_ai_product_readfeel_current_output_inventory.py",
    ),
    "product_surface_validation": (
        "mashos-api/ai/services/ai_inference/emlis_ai_product_surface_validation.py",
    ),
    "visible_surface_acceptance_gate": (
        "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py",
    ),
    "emotion_submit_public_feedback_boundary": (
        "mashos-api/ai/services/ai_inference/emotion_submit_service.py",
        "mashos-api/ai/services/ai_inference/api_emotion_submit.py",
    ),
    "display_contract": (
        "mashos-api/ai/tests/test_emlis_ai_display_contract.py",
        "mashos-api/ai/tests/test_emotion_submit_two_stage_reception_e2e.py",
    ),
    "public_boundary_contract": (
        "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
    ),
    "p0_p1_contract_freeze": (
        "mashos-api/ai/services/ai_inference/emlis_ai_product_quality_contract_freeze.py",
    ),
    "p2_surface_safety": (
        "mashos-api/ai/services/ai_inference/emlis_ai_visible_surface_acceptance_gate.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_runtime_surface_pre_return_gate.py",
    ),
    "renderer_output_capture": (
        "mashos-api/ai/tests/fixtures/emlis_ai_product_readfeel_p3_local_output_capture_20260609.py",
    ),
    "blind_qa_review": (
        "mashos-api/ai/services/ai_inference/emlis_ai_product_readfeel_p3_blind_qa_ratings_review.py",
    ),
    "family_tuning_backlog": (
        "mashos-api/ai/services/ai_inference/emlis_ai_reception_mode_resolver.py",
        "mashos-api/ai/services/ai_inference/emlis_ai_state_answer_ratio_policy.py",
    ),
    "manual_review": (
        "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609.py",
    ),
}
DO_NOT_TOUCH_FILES_20260609: Final[tuple[str, ...]] = (
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/useInputFeedbackModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
    "Cocolon/tests/rn-screen-contracts.test.js",
    "mashos-api/ai/services/ai_inference/api_emotion_submit.py",
    "mashos-api/ai/services/ai_inference/emotion_submit_service.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_product_release_decision.py",
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
    "public_response_key_change",
    "api_route_change",
    "db_schema_change",
    "rn_display_contract_change",
    "history_line_masking_current_input_gap",
)
FIRST_TEST_CANDIDATES_20260609: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_contract_freeze_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_baseline_case_matrix_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_local_output_capture_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_inventory_connection_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_verdict_split_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609.py",
    "mashos-api/ai/tests/test_emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609.py",
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


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        number = float(value)
        if number != number:
            return None
        return max(0.0, min(1.0, number))
    except (TypeError, ValueError):
        return None


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


def assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(
    payload: Any,
    *,
    source: str = "product_readfeel_p3_repair_priority_ledger",
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


def _verdict_layer_rank(layer: str) -> int:
    try:
        return VERDICT_PRIORITY_ORDER_20260609.index(layer)
    except ValueError:
        return len(VERDICT_PRIORITY_ORDER_20260609)


def _blocker_priority(blocker_id: str) -> int:
    try:
        return BLOCKER_PRIORITY_ORDER_20260609.index(blocker_id)
    except ValueError:
        return len(BLOCKER_PRIORITY_ORDER_20260609)


def _extract_verdict_rows(verdict_split_or_rows: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if verdict_split_or_rows is None:
        return []
    if isinstance(verdict_split_or_rows, Mapping):
        if verdict_split_or_rows.get("schema_version") == PRODUCT_READFEEL_P3_VERDICT_SPLIT_VERSION_20260609:
            assert_product_readfeel_p3_verdict_split_meta_only_20260609(verdict_split_or_rows)
        rows = verdict_split_or_rows.get("verdict_rows") or verdict_split_or_rows.get("rows") or []
    else:
        rows = verdict_split_or_rows
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows or []):
        if not isinstance(row, Mapping):
            raise ValueError(f"P3-6 verdict row[{index}] must be a mapping")
        assert_product_readfeel_p3_verdict_split_meta_only_20260609(row, source=f"p3_6.verdict_rows[{index}]")
        normalized.append(dict(row))
    return normalized


def _extract_review_rows(blind_qa_material_or_rows: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    if blind_qa_material_or_rows is None:
        return []
    if isinstance(blind_qa_material_or_rows, Mapping):
        if blind_qa_material_or_rows.get("schema_version") == PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609:
            assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(blind_qa_material_or_rows)
        rows = blind_qa_material_or_rows.get("review_rows") or blind_qa_material_or_rows.get("rows") or []
    else:
        rows = blind_qa_material_or_rows
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows or []):
        if not isinstance(row, Mapping):
            raise ValueError(f"P3-6 review row[{index}] must be a mapping")
        assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(row, source=f"p3_6.review_rows[{index}]")
        normalized.append(dict(row))
    return normalized


def _case_key(row: Mapping[str, Any]) -> str:
    for key in ("case_id", "fixture_id", "candidate_id", "row_id", "review_id"):
        value = _safe_identifier(row.get(key), default="")
        if value:
            return value
    return ""


def _review_by_case(review_rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    lookup: dict[str, Mapping[str, Any]] = {}
    for row in review_rows:
        key = _case_key(row)
        if key and key not in lookup:
            lookup[key] = row
    return lookup


def _row_layer(row: Mapping[str, Any]) -> str:
    return _clean(row.get("verdict_layer") or row.get("source_verdict_layer") or "")


def _row_verdict(row: Mapping[str, Any]) -> str:
    return _clean(row.get("verdict") or row.get("source_verdict") or "")


def _row_blockers(row: Mapping[str, Any]) -> list[str]:
    blockers = _dedupe(row.get("blocker_ids"))
    blockers.extend(_dedupe(row.get("source_blocker_ids")))
    if not blockers and _row_layer(row) == VERDICT_LAYER_P2_RED:
        blockers.append("contract_violation")
    if not blockers and _row_layer(row) == VERDICT_LAYER_P3_REPAIR_REQUIRED:
        blockers.append("p3_inventory_repair_required")
    if not blockers and _row_layer(row) == VERDICT_LAYER_P3_YELLOW:
        blockers.append("p3_yellow_readfeel_weakness")
    return _dedupe(blockers)


def _row_reason_codes(row: Mapping[str, Any]) -> list[str]:
    return _dedupe([
        *_dedupe(row.get("reason_codes")),
        *_dedupe(row.get("source_reason_codes")),
        *_dedupe(row.get("repair_reasons")),
        *_dedupe(row.get("yellow_reasons")),
        *_dedupe(row.get("red_reasons")),
        *_dedupe(row.get("red_flags")),
        *_dedupe(row.get("source_failure_buckets")),
        *_dedupe(row.get("failure_buckets")),
    ])


def _target_layers_for_blocker(blocker_id: str) -> list[str]:
    return _dedupe(TARGET_LAYERS_BY_BLOCKER_20260609.get(blocker_id, ("manual_review",)))


def _target_files_for_layers(layers: Sequence[str]) -> list[str]:
    files: list[str] = []
    for layer in layers:
        files.extend(TARGET_FILE_CANDIDATES_BY_LAYER_20260609.get(layer, ()))
    return _dedupe(files)


def _first_test_candidates_for_blocker(blocker_id: str) -> list[str]:
    tests = list(FIRST_TEST_CANDIDATES_20260609)
    if blocker_id in {"limited_grounding_collapsed_to_question", "rich_input_low_information_overroute"}:
        tests.append("mashos-api/ai/tests/test_emlis_ai_limited_grounding_reception_surface_p4.py")
        tests.append("mashos-api/ai/tests/test_emlis_ai_public_surface_requirement_p1.py")
    if blocker_id in {"generic_reception_surface", "repeated_surface_signature", "p3_readfeel_gap"}:
        tests.append("mashos-api/ai/tests/test_emlis_ai_mirror_only_surface_detector.py")
        tests.append("mashos-api/ai/tests/test_emlis_ai_product_surface_question_dominance_guard_p6.py")
    if blocker_id in {"family_temperature_flattened", "structure_question_answered_as_comfort"}:
        tests.append("mashos-api/ai/tests/test_emlis_ai_product_readfeel_surface_v1_phase5.py")
    if blocker_id in {"self_denial_identity_claim_risk", "relationship_target_judgement_risk", "surface_breakage"}:
        tests.append("mashos-api/ai/tests/test_emlis_ai_visible_surface_acceptance_gate.py")
        tests.append("mashos-api/ai/tests/test_emlis_ai_quality_gate_pre_return.py")
    return _dedupe(tests)


def _repair_action(blocker_id: str) -> str:
    category = BLOCKER_CATEGORY_BY_ID_20260609.get(blocker_id, "manual_review")
    if category == "p2_contract_or_surface_safety":
        return "return_to_p2_or_contract_repair_before_product_readfeel_changes"
    if category == "p1_display_repair":
        return "repair_display_arrival_before_readfeel_tuning"
    if category == "p3_current_input_core_retention":
        return "inspect_material_bundle_and_surface_requirement_without_gate_relaxation"
    if category == "p3_limited_grounding_reception":
        return "repair_limited_grounding_reception_without_turning_it_into_question_only"
    if category == "p3_generic_or_repeated_surface":
        return "repair_surface_plan_and_realizer_to_restore_input_specificity"
    if category == "p3_family_temperature":
        return "repair_family_temperature_ratio_and_observation_mode"
    if category == "p5_history_line_backlog":
        return "defer_p5_until_current_input_anchor_is_strong"
    if category == "p6_structure_insight_backlog":
        return "defer_to_p6_structure_insight_backlog_after_p3_readfeel"
    return "manual_review_before_runtime_changes"


def _effective_source_rows(
    *,
    verdict_rows: Sequence[Mapping[str, Any]],
    review_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    review_lookup = _review_by_case(review_rows)
    rows: list[dict[str, Any]] = []
    for verdict in verdict_rows:
        key = _case_key(verdict)
        merged = dict(verdict)
        review = review_lookup.get(key)
        if review:
            merged["review_read_feeling_score"] = review.get("read_feeling_score")
            merged["review_naturalness_score"] = (review.get("dimension_scores") or {}).get(DIMENSION_NATURALNESS)
            merged["review_non_template_score"] = (review.get("dimension_scores") or {}).get(DIMENSION_NON_TEMPLATE)
            merged["review_v1_score"] = review.get("v1_score")
            merged["review_repair_reasons"] = list(review.get("repair_reasons") or [])
            merged["review_red_flags"] = list(review.get("red_flags") or [])
        rows.append(merged)
    if rows:
        return rows
    for review in review_rows:
        rows.append(
            {
                "case_id": _safe_identifier(review.get("case_id"), default=""),
                "fixture_id": _safe_identifier(review.get("fixture_id") or review.get("case_id"), default=""),
                "row_id": _safe_identifier(review.get("candidate_id") or review.get("review_id"), default=""),
                "family": _clean(review.get("family") or review.get("product_readfeel_family")),
                "product_readfeel_family": _clean(review.get("product_readfeel_family") or review.get("family")),
                "coverage_slices": _dedupe(review.get("coverage_slices")),
                "verdict": _clean(review.get("source_verdict")),
                "verdict_layer": _clean(review.get("source_verdict_layer")),
                "blocker_ids": _dedupe(review.get("source_blocker_ids")),
                "reason_codes": _dedupe([*_dedupe(review.get("source_reason_codes")), *_dedupe(review.get("repair_reasons")), *_dedupe(review.get("red_flags"))]),
                "review_read_feeling_score": review.get("read_feeling_score"),
                "review_naturalness_score": (review.get("dimension_scores") or {}).get(DIMENSION_NATURALNESS),
                "review_non_template_score": (review.get("dimension_scores") or {}).get(DIMENSION_NON_TEMPLATE),
                "review_v1_score": review.get("v1_score"),
            }
        )
    return rows


def _target_candidate_rows(rows: Sequence[Mapping[str, Any]], *, p2_red_present: bool) -> list[Mapping[str, Any]]:
    if p2_red_present:
        return [row for row in rows if _row_layer(row) == VERDICT_LAYER_P2_RED]
    display_rows = [row for row in rows if _row_layer(row) == VERDICT_LAYER_P1_DISPLAY_REPAIR]
    if display_rows:
        return display_rows
    repair_rows = [row for row in rows if _row_layer(row) == VERDICT_LAYER_P3_REPAIR_REQUIRED]
    yellow_rows = [row for row in rows if _row_layer(row) == VERDICT_LAYER_P3_YELLOW]
    # P3-6 fixes priority by blocker class, not only by verdict strength.
    # This keeps P6/P5 backlog-like repair rows from outranking current-input
    # read-feel blockers such as rich-input overroute or generic surfaces.
    if repair_rows or yellow_rows:
        return [*repair_rows, *yellow_rows]
    weak_review_rows = [
        row
        for row in rows
        if (_safe_float(row.get("review_read_feeling_score")) is not None)
        and float(row.get("review_read_feeling_score")) < PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET
        and _row_layer(row) not in {VERDICT_LAYER_NOT_EVALUATED, VERDICT_LAYER_P2_RED}
    ]
    return weak_review_rows


def _item_from_blocker_rows(
    *,
    blocker_id: str,
    blocker_rows: Sequence[Mapping[str, Any]],
    priority: int,
    p2_red_present: bool,
    run_id: str,
) -> dict[str, Any]:
    families = Counter(_clean(row.get("family") or row.get("product_readfeel_family") or "unclassified") for row in blocker_rows)
    verdict_layers = Counter(_row_layer(row) for row in blocker_rows)
    verdicts = Counter(_row_verdict(row) for row in blocker_rows)
    coverage = Counter(slice_id for row in blocker_rows for slice_id in _dedupe(row.get("coverage_slices")))
    reasons = Counter(reason for row in blocker_rows for reason in _row_reason_codes(row))
    read_scores = [_safe_float(row.get("review_read_feeling_score")) for row in blocker_rows]
    naturalness_scores = [_safe_float(row.get("review_naturalness_score")) for row in blocker_rows]
    non_template_scores = [_safe_float(row.get("review_non_template_score")) for row in blocker_rows]
    read_scores = [score for score in read_scores if score is not None]
    naturalness_scores = [score for score in naturalness_scores if score is not None]
    non_template_scores = [score for score in non_template_scores if score is not None]
    target_layers = _target_layers_for_blocker(blocker_id)
    item = {
        "schema_version": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_ITEM_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_ITEM_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609,
        "run_id": run_id,
        "priority": priority,
        "blocker_id": blocker_id,
        "blocker_category": BLOCKER_CATEGORY_BY_ID_20260609.get(blocker_id, "manual_review"),
        "verdict_level": max((key for key in verdicts if key), key=lambda value: verdicts[value], default=""),
        "verdict_layer": min((key for key in verdict_layers if key), key=_verdict_layer_rank, default=""),
        "case_count": len(blocker_rows),
        "families": [family for family, _count in families.most_common()],
        "family_counts": dict(families),
        "coverage_slices": [slice_id for slice_id, _count in coverage.most_common()],
        "sample_case_ids": [_case_key(row) for row in blocker_rows if _case_key(row)][:5],
        "reason_codes": [reason for reason, _count in reasons.most_common()],
        "target_layers": target_layers,
        "target_file_candidates": _target_files_for_layers(target_layers),
        "first_test_candidates": _first_test_candidates_for_blocker(blocker_id),
        "forbidden_fix_paths": list(FORBIDDEN_FIX_PATHS_20260609),
        "repair_action": _repair_action(blocker_id),
        "p2_red_present": p2_red_present,
        "p3_repair_allowed_before_p2_clear": not p2_red_present,
        "repair_priority_fixed": True,
        "selected_as_first_repair_target": priority <= 2,
        "review_read_feeling_min": min(read_scores) if read_scores else None,
        "review_read_feeling_average": round(sum(read_scores) / len(read_scores), 4) if read_scores else None,
        "review_naturalness_min": min(naturalness_scores) if naturalness_scores else None,
        "review_non_template_min": min(non_template_scores) if non_template_scores else None,
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
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(item, source="p3_6.ledger_item")
    return item


def _build_items(rows: Sequence[Mapping[str, Any]], *, max_first_targets: int, p2_red_present: bool, run_id: str) -> list[dict[str, Any]]:
    candidate_rows = _target_candidate_rows(rows, p2_red_present=p2_red_present)
    by_blocker: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in candidate_rows:
        blockers = _row_blockers(row) or ["manual_review"]
        for blocker_id in blockers:
            by_blocker[blocker_id].append(row)
    ordered = sorted(by_blocker.items(), key=lambda item: (_blocker_priority(item[0]), -len(item[1]), item[0]))
    items: list[dict[str, Any]] = []
    max_items = max(1, min(2, int(max_first_targets or 2)))
    for priority, (blocker_id, blocker_rows) in enumerate(ordered[:max_items], start=1):
        items.append(
            _item_from_blocker_rows(
                blocker_id=blocker_id,
                blocker_rows=blocker_rows,
                priority=priority,
                p2_red_present=p2_red_present,
                run_id=run_id,
            )
        )
    return items


def _summary(
    *,
    rows: Sequence[Mapping[str, Any]],
    review_rows: Sequence[Mapping[str, Any]],
    items: Sequence[Mapping[str, Any]],
    run_id: str,
    source_summary: Mapping[str, Any],
) -> dict[str, Any]:
    layer_counts = Counter(_row_layer(row) for row in rows)
    verdict_counts = Counter(_row_verdict(row) for row in rows)
    family_counts = Counter(_clean(row.get("family") or row.get("product_readfeel_family") or "unclassified") for row in rows)
    blocker_counts = Counter(blocker for row in rows for blocker in _row_blockers(row))
    required_observed = [family for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if family_counts.get(family, 0) > 0]
    missing_required = [family for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if family not in required_observed]
    p2_red_count = int(layer_counts.get(VERDICT_LAYER_P2_RED, 0))
    p1_display_count = int(layer_counts.get(VERDICT_LAYER_P1_DISPLAY_REPAIR, 0))
    p3_repair_count = int(layer_counts.get(VERDICT_LAYER_P3_REPAIR_REQUIRED, 0))
    p3_yellow_count = int(layer_counts.get(VERDICT_LAYER_P3_YELLOW, 0))
    pass_count = int(layer_counts.get(VERDICT_LAYER_P3_PASS, 0) or verdict_counts.get("PASS", 0))
    not_evaluated_count = int(layer_counts.get(VERDICT_LAYER_NOT_EVALUATED, 0))
    review_read_scores = [_safe_float(row.get("read_feeling_score")) for row in review_rows]
    review_read_scores = [score for score in review_read_scores if score is not None]
    first_target = _clean(items[0].get("blocker_id")) if items else ""
    if p2_red_count > 0:
        decision = "return_to_p2_surface_safety_before_p3_repair"
    elif p1_display_count > 0:
        decision = "repair_display_reliability_before_p3_readfeel"
    elif items:
        decision = "start_p3_repair_with_max_two_targets"
    elif review_read_scores and min(review_read_scores) >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET:
        decision = "advance_to_p4_family_tuning_candidate"
    elif not review_rows:
        decision = "wait_for_p3_5_ratings_before_repair_priority"
    else:
        decision = "manual_review_before_p4_or_p5"
    summary = {
        "schema_version": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_PROFILE_20260609,
        "case_count": len(rows) or _to_int(source_summary.get("expected_review_count"), 0),
        "review_count": len(review_rows),
        "item_count": len(items),
        "first_repair_target": first_target,
        "first_repair_target_count": len(items),
        "first_repair_target_blocker_ids": [_clean(item.get("blocker_id")) for item in items],
        "first_repair_targets_limited_to_max_two": len(items) <= 2,
        "verdict_layer_counts": {key: int(value) for key, value in layer_counts.items() if key},
        "verdict_counts": {key: int(value) for key, value in verdict_counts.items() if key},
        "family_counts": dict(family_counts),
        "blocker_counts": dict(blocker_counts),
        "required_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "observed_required_families": required_observed,
        "missing_required_families": missing_required,
        "all_required_families_present": missing_required == [] and bool(required_observed),
        "p2_red_count": p2_red_count,
        "p1_display_repair_required_count": p1_display_count,
        "p3_repair_required_count": p3_repair_count,
        "p3_yellow_count": p3_yellow_count,
        "pass_count": pass_count,
        "not_evaluated_count": not_evaluated_count,
        "red_count": p2_red_count,
        "repair_required_count": p3_repair_count + p1_display_count,
        "yellow_count": p3_yellow_count,
        "p2_red_present": p2_red_count > 0,
        "p2_red_blocks_p3_repair": p2_red_count > 0,
        "p3_repair_can_start": p2_red_count == 0 and bool(items),
        "read_feeling_score_min": min(review_read_scores) if review_read_scores else None,
        "read_feeling_score_average": round(sum(review_read_scores) / len(review_read_scores), 4) if review_read_scores else None,
        "read_feeling_product_target": PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
        "ratings_only_review_connected": bool(review_rows),
        "ratings_do_not_override_p2_red": True,
        "target_file_candidates_visible": all(bool(item.get("target_file_candidates")) for item in items) if items else False,
        "do_not_touch_files_visible": True,
        "forbidden_fix_paths_visible": True,
        "gate_relaxation_excluded_from_fix_plan": True,
        "fixed_template_fix_excluded": True,
        "case_specific_runtime_branch_excluded": True,
        "p5_history_line_not_used_to_mask_current_input_gap": True,
        "decision": decision,
        "source_p3_5_decision": _clean(source_summary.get("decision")),
        "p3_0_contract_freeze_respected": True,
        "p3_1_baseline_case_matrix_used": len(rows) >= 60 or _to_int(source_summary.get("expected_review_count"), 0) >= 60,
        "p3_2_local_output_capture_used": True,
        "p3_3_inventory_connection_used": True,
        "p3_4_verdict_split_used": bool(rows),
        "p3_5_blind_qa_ratings_only_review_used": bool(review_rows),
        "p3_6_repair_priority_ledger_applied": True,
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
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(summary, source="p3_6.summary")
    return summary


def _public_summary(ledger: Mapping[str, Any]) -> dict[str, Any]:
    summary = dict(ledger.get("summary") or {})
    public_summary = {
        key: value
        for key, value in summary.items()
        if key not in {"verdict_rows", "review_rows", "items", "source_rows", "source_review_rows"}
    }
    public_summary["schema_version"] = PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609
    public_summary["version"] = PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609
    public_summary["source"] = PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SOURCE_20260609
    public_summary["first_repair_target_items"] = [
        {
            "priority": int(item.get("priority") or 0),
            "blocker_id": _clean(item.get("blocker_id")),
            "blocker_category": _clean(item.get("blocker_category")),
            "case_count": _to_int(item.get("case_count"), 0),
            "families": list(item.get("families") or []),
            "sample_case_ids": list(item.get("sample_case_ids") or []),
            "target_layers": list(item.get("target_layers") or []),
            "target_file_candidates": list(item.get("target_file_candidates") or []),
            "forbidden_fix_paths": list(item.get("forbidden_fix_paths") or []),
            "repair_action": _clean(item.get("repair_action")),
            "comment_text_body_included": False,
            "raw_input_included": False,
            "candidate_body_included": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        for item in ledger.get("items") or []
    ]
    public_summary["do_not_touch_files"] = list(DO_NOT_TOUCH_FILES_20260609)
    public_summary["forbidden_fix_paths"] = list(FORBIDDEN_FIX_PATHS_20260609)
    public_summary["product_gate_ready"] = False
    public_summary["public_release_applied"] = False
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(public_summary, source="p3_6.public_summary")
    return public_summary


def build_product_readfeel_p3_repair_priority_ledger_20260609(
    *,
    blind_qa_material: Mapping[str, Any] | None = None,
    ratings_material: Mapping[str, Any] | None = None,
    review_rows: Sequence[Mapping[str, Any]] | None = None,
    verdict_split: Mapping[str, Any] | None = None,
    verdict_rows: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    max_first_targets: int = 2,
) -> dict[str, Any]:
    material = blind_qa_material if blind_qa_material is not None else ratings_material
    if isinstance(material, Mapping):
        assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(material)
    if isinstance(verdict_split, Mapping):
        assert_product_readfeel_p3_verdict_split_meta_only_20260609(verdict_split)

    extracted_review_rows = _extract_review_rows(review_rows if review_rows is not None else material)
    extracted_verdict_rows = _extract_verdict_rows(verdict_rows if verdict_rows is not None else verdict_split)
    source_rows_from_reviews_only = False
    if not extracted_verdict_rows and isinstance(material, Mapping):
        # P3-5 intentionally does not retain source verdict rows in the public summary.
        # In that case the ledger can still fix priority from ratings-only review rows,
        # while keeping source_verdict_row_count at zero.
        source_rows_from_reviews_only = True
    source_summary = {}
    if isinstance(material, Mapping):
        source_summary = dict(material.get("summary") or material.get("public_summary") or {})
    elif isinstance(verdict_split, Mapping):
        source_summary = dict(verdict_split.get("summary") or verdict_split.get("public_summary") or {})
    run_id_value = _safe_identifier(
        run_id
        or source_summary.get("run_id")
        or (extracted_verdict_rows[0].get("run_id") if extracted_verdict_rows else None)
        or (extracted_review_rows[0].get("run_id") if extracted_review_rows else None),
        default="p3_6_repair_priority_ledger",
        max_length=96,
    )
    source_rows = _effective_source_rows(
        verdict_rows=[] if source_rows_from_reviews_only else extracted_verdict_rows,
        review_rows=extracted_review_rows,
    )
    p2_red_present = any(_row_layer(row) == VERDICT_LAYER_P2_RED for row in source_rows)
    items = _build_items(
        source_rows,
        max_first_targets=max_first_targets,
        p2_red_present=p2_red_present,
        run_id=run_id_value,
    )
    summary = _summary(
        rows=source_rows,
        review_rows=extracted_review_rows,
        items=items,
        run_id=run_id_value,
        source_summary=source_summary,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609,
        "version": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609,
        "source": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SOURCE_20260609,
        "source_step": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_PROFILE_20260609,
        "summary": summary,
        "items": items,
        "item_count": len(items),
        "do_not_touch_files": list(DO_NOT_TOUCH_FILES_20260609),
        "forbidden_fix_paths": list(FORBIDDEN_FIX_PATHS_20260609),
        "first_test_candidates": list(FIRST_TEST_CANDIDATES_20260609),
        "source_verdict_row_count": len(extracted_verdict_rows),
        "source_review_row_count": len(extracted_review_rows),
        "source_case_count": len(source_rows),
        "public_summary": {},
        "p3_6_repair_priority_ledger_applied": True,
        "repair_priority_fixed": True,
        "first_repair_targets_limited_to_max_two": len(items) <= 2,
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
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(payload)
    return payload


def build_product_readfeel_p3_repair_priority_ledger_public_summary_20260609(
    ledger_or_material: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if isinstance(ledger_or_material, Mapping) and ledger_or_material.get("schema_version") == PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609:
        summary = dict(ledger_or_material.get("public_summary") or {})
    else:
        summary = build_product_readfeel_p3_repair_priority_ledger_20260609(
            blind_qa_material=ledger_or_material,
        )["public_summary"]
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(summary)
    return summary


def dump_product_readfeel_p3_repair_priority_ledger_public_summary_20260609(
    ledger_or_material: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p3_repair_priority_ledger_public_summary_20260609(ledger_or_material)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_ITEM_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609",
    "assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609",
    "build_product_readfeel_p3_repair_priority_ledger_20260609",
    "build_product_readfeel_p3_repair_priority_ledger_public_summary_20260609",
    "dump_product_readfeel_p3_repair_priority_ledger_public_summary_20260609",
]
