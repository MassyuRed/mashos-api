# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-5 surface signature audit for Product Read Feel family tuning.

P4-5 makes ``generic_reception_surface`` and
``repeated_surface_signature`` visible as body-free surface signatures.  It is
not a renderer and it does not rewrite ``comment_text``.  It only records which
family policy roles are missing, whether a visible surface collapsed to generic
reception / repeated closing / question-only shape, and which existing runtime
owner layer should later receive a family-specific correction.

The packet intentionally keeps no raw input, no rendered Emlis body, no history
raw text, no candidate body, no exact output, and no fixture-string route.  P4-5
also keeps P5 on hold: history-line surface strengthening must not hide current
input read-feel weakness.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
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
from emlis_ai_product_readfeel_p4_family_tuning_policy import (
    COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE,
    COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION,
    FAMILY_LIMITED_GROUNDING,
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610,
    build_product_readfeel_p4_family_tuning_policy_20260610,
)
from emlis_ai_product_readfeel_p4_material_audit import (
    assert_product_readfeel_p4_material_audit_meta_only_20260610,
)
from emlis_ai_product_readfeel_p4_target_case_selection import (
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only

PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.surface_signature_audit.20260610.v1"
)
PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_EVENT_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.surface_signature_audit_event.20260610.v1"
)
PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.surface_signature_audit_summary.20260610.v1"
)
PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610: Final = (
    "P4-5_Surface_Specificity"
)
PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SOURCE_20260610: Final = (
    "Cocolon_EmlisAI_P4_FamilyProductTuning_SurfaceSignatureAudit_20260610"
)
PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610: Final = (
    "p4_5_generic_reception_surface_repeated_signature_specificity_correction"
)

BLOCKER_GENERIC_RECEPTION_SURFACE: Final = "generic_reception_surface"
BLOCKER_REPEATED_SURFACE_SIGNATURE: Final = "repeated_surface_signature"
BLOCKER_FAMILY_TEMPERATURE_FLATTENED: Final = "family_temperature_flattened"
BLOCKER_QUESTION_ONLY_SURFACE: Final = "question_only_surface"
BLOCKER_QUESTION_BEFORE_RECEPTION: Final = "question_before_reception"
BLOCKER_REQUIRED_ANCHOR_MISSING: Final = "required_anchor_missing"
BLOCKER_RECEPTION_ANCHOR_MISSING: Final = "reception_anchor_missing"
BLOCKER_FORBIDDEN_SURFACE_CLASS_PRESENT: Final = "forbidden_surface_class_present"
BLOCKER_MIRROR_ONLY_SURFACE: Final = "mirror_only_surface"
BLOCKER_COMFORT_ONLY_SURFACE: Final = "comfort_only_surface"
BLOCKER_SOURCE_UNAVAILABLE_NORMAL_REBUILD_RISK: Final = "source_unavailable_normal_rebuild_risk"

VERDICT_PASS: Final = "PASS"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"

_CORRECTION_TARGET_LAYERS_BY_FAMILY_20260610: Final[dict[str, tuple[str, ...]]] = {
    FAMILY_DAILY_UNPLEASANT: (
        "reception_mode_resolver",
        "state_answer_ratio_policy",
        "two_stage_section_surface_plan",
        "complete_surface_realizer",
    ),
    FAMILY_STRUCTURE_QUESTION: (
        "reception_mode_resolver",
        "state_answer_ratio_policy",
        "two_stage_section_surface_plan",
        "complete_surface_realizer",
    ),
    FAMILY_SELF_DENIAL: (
        "state_answer_special_cases",
        "self_denial_safe_state_answer",
        "visible_surface_acceptance_gate",
        "state_answer_ratio_policy",
    ),
    FAMILY_DAILY_POSITIVE: (
        "state_answer_ratio_policy",
        "two_stage_section_surface_plan",
        "complete_surface_realizer",
    ),
    FAMILY_RELATIONSHIP_BOUNDARY: (
        "reception_mode_resolver",
        "state_answer_ratio_policy",
        "two_stage_section_surface_plan",
    ),
    FAMILY_LOW_INFORMATION_SHORT: (
        "public_surface_requirement",
        "low_information_observation_composer",
        "visible_surface_acceptance_gate",
    ),
    FAMILY_LIMITED_GROUNDING: (
        "public_surface_requirement",
        "limited_grounding_reception_surface",
        "visible_surface_acceptance_gate",
    ),
}

_FAMILY_MIN_REQUIRED_ANCHOR_COUNT_20260610: Final[dict[str, int]] = {
    FAMILY_DAILY_UNPLEASANT: 2,
    FAMILY_STRUCTURE_QUESTION: 3,
    FAMILY_SELF_DENIAL: 2,
    FAMILY_DAILY_POSITIVE: 2,
    FAMILY_RELATIONSHIP_BOUNDARY: 3,
    FAMILY_LOW_INFORMATION_SHORT: 2,
    FAMILY_LIMITED_GROUNDING: 3,
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
        "visible_text",
        "visibleText",
        "realized_text",
        "realizedText",
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
        "comfort_only_allowed",
        "question_only_allowed",
        "observation_zero_allowed",
        "human_follow_zero_allowed",
        "public_meta_body_allowed",
        "comment_text_written_by_detector",
        "comment_text_generated",
        "comment_text_key_written",
        "runtime_surface_rewritten",
        "surface_rewritten_by_audit",
    }
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 160) -> str:
    text_value = _clean(value) or default
    text_value = "_".join(text_value.split())
    if len(text_value) > max_length:
        text_value = text_value[:max_length].rstrip("_-.:/")
    return text_value or default


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in _listify(values):
        cleaned = _safe_identifier(item)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


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


def assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "p4_surface_signature_audit",
) -> None:
    """Reject body-bearing or runtime-mutating P4-5 audit payloads."""

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
        "body_free_signature_only": True,
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
        "question_only_allowed": False,
        "comfort_only_allowed": False,
        "observation_zero_allowed": False,
        "human_follow_zero_allowed": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "runtime_surface_rewritten": False,
        "surface_rewritten_by_audit": False,
    }


def _as_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    return bool(value)


def _selected_cases(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    selected = payload.get("selected_cases") or []
    if isinstance(selected, Sequence) and not isinstance(selected, (str, bytes, bytearray)):
        return [item for item in selected if isinstance(item, Mapping)]
    return []


def _family_policies(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("family_policies") or []
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
        return [item for item in rows if isinstance(item, Mapping)]
    return []


def _boundary_slice_policies(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    rows = payload.get("boundary_slice_policies") or []
    if isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
        return [item for item in rows if isinstance(item, Mapping)]
    return []


def _policy_for_case(
    *,
    selected_case: Mapping[str, Any],
    family_policies_by_family: Mapping[str, Mapping[str, Any]],
    boundary_policies_by_slice: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    family = _clean(selected_case.get("family"))
    if family in family_policies_by_family:
        return family_policies_by_family[family]
    for coverage_slice in _dedupe(selected_case.get("coverage_slices") or []):
        policy = boundary_policies_by_slice.get(coverage_slice)
        if policy:
            return policy
    return None


def _policy_id(policy: Mapping[str, Any] | None) -> str:
    if not policy:
        return "unmapped_policy"
    return _safe_identifier(policy.get("policy_id"), default="unmapped_policy")


def _policy_family(policy: Mapping[str, Any] | None, fallback_family: str) -> str:
    if not policy:
        return fallback_family
    return _safe_identifier(policy.get("family") or fallback_family, default=fallback_family)


def _policy_section(policy: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not policy:
        return {}
    section = policy.get("section_policy")
    if isinstance(section, Mapping):
        return section
    return {}


def _expected_section_sequence(policy: Mapping[str, Any] | None) -> list[str]:
    section = _policy_section(policy)
    return _dedupe(section.get("section_role_sequence") or ["observation", "reception"])


def _expected_anchor_roles(policy: Mapping[str, Any] | None) -> list[str]:
    if not policy:
        return []
    return _dedupe(policy.get("required_anchor_roles") or [])


def _forbidden_surface_classes(policy: Mapping[str, Any] | None) -> list[str]:
    if not policy:
        return []
    return _dedupe(policy.get("forbidden_surface_classes") or [])


def _expected_temperature_profile(policy: Mapping[str, Any] | None) -> str:
    if not policy:
        return "unmapped_temperature_profile"
    return _safe_identifier(policy.get("temperature_profile"), default="unmapped_temperature_profile")


def _min_required_anchor_count(family: str, expected_anchor_roles: Sequence[str]) -> int:
    return min(
        len(expected_anchor_roles),
        int(_FAMILY_MIN_REQUIRED_ANCHOR_COUNT_20260610.get(family, 2)),
    )


def _default_signature_observation(
    *,
    selected_case: Mapping[str, Any],
    policy: Mapping[str, Any] | None,
) -> dict[str, Any]:
    family = _policy_family(policy, _safe_identifier(selected_case.get("family"), default="unclassified"))
    expected_anchors = _expected_anchor_roles(policy)
    min_count = _min_required_anchor_count(family, expected_anchors)
    expected_sequence = _expected_section_sequence(policy)
    return {
        "section_role_sequence": expected_sequence,
        "opening_shape_family": f"{family}_opening",
        "closing_shape_family": f"{family}_closing",
        "observed_temperature_profile": _expected_temperature_profile(policy),
        "observed_anchor_roles": expected_anchors[: max(min_count, 1)],
        "observation_anchor_count": max(min_count, 1),
        "reception_anchor_count": 1,
        "generic_empathy_marker_count": 0,
        "question_count": 0,
        "question_position": "none",
        "same_closing_family_repetition_count": 1,
        "same_section_role_sequence_repetition_count": 1,
        "observed_signature_cluster_size": 1,
        "mirror_only_detected": False,
        "comfort_only_surface_detected": False,
        "forbidden_surface_classes_present": [],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "gate_relaxed": False,
    }


def _normalize_signature_observation(
    *,
    selected_case: Mapping[str, Any],
    policy: Mapping[str, Any] | None,
    provided: Mapping[str, Any] | None,
) -> dict[str, Any]:
    base = _default_signature_observation(selected_case=selected_case, policy=policy)
    if provided:
        assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
            provided, source="p4_5.surface_signature_observation"
        )
        for key, value in provided.items():
            base[str(key)] = value
    base["section_role_sequence"] = _dedupe(base.get("section_role_sequence") or [])
    base["observed_anchor_roles"] = _dedupe(base.get("observed_anchor_roles") or [])
    base["opening_shape_family"] = _safe_identifier(base.get("opening_shape_family"), default="unknown_opening")
    base["closing_shape_family"] = _safe_identifier(base.get("closing_shape_family"), default="unknown_closing")
    base["observed_temperature_profile"] = _safe_identifier(
        base.get("observed_temperature_profile"), default="unknown_temperature_profile"
    )
    base["question_position"] = _safe_identifier(base.get("question_position"), default="none")
    base["forbidden_surface_classes_present"] = _dedupe(base.get("forbidden_surface_classes_present") or [])
    return base


def _missing_anchor_roles(expected_anchor_roles: Sequence[str], observed_anchor_roles: Sequence[str]) -> list[str]:
    observed = set(_dedupe(observed_anchor_roles))
    return [role for role in _dedupe(expected_anchor_roles) if role not in observed]


def _surface_signature_key(
    *,
    family: str,
    observed: Mapping[str, Any],
) -> str:
    section = "+".join(_dedupe(observed.get("section_role_sequence") or [])) or "no_section"
    opening = _safe_identifier(observed.get("opening_shape_family"), default="opening")
    closing = _safe_identifier(observed.get("closing_shape_family"), default="closing")
    temp = _safe_identifier(observed.get("observed_temperature_profile"), default="temperature")
    return f"{family}:{section}:{opening}:{closing}:{temp}"


def _detected_blockers(
    *,
    family: str,
    coverage_slices: Sequence[str],
    policy: Mapping[str, Any] | None,
    observed: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    expected_anchor_roles = _expected_anchor_roles(policy)
    observed_anchor_roles = _dedupe(observed.get("observed_anchor_roles") or [])
    missing_anchor_roles = _missing_anchor_roles(expected_anchor_roles, observed_anchor_roles)
    observation_anchor_count = _as_int(observed.get("observation_anchor_count"))
    reception_anchor_count = _as_int(observed.get("reception_anchor_count"))
    generic_count = _as_int(observed.get("generic_empathy_marker_count"))
    question_count = _as_int(observed.get("question_count"))
    question_position = _safe_identifier(observed.get("question_position"), default="none")
    same_closing = _as_int(observed.get("same_closing_family_repetition_count"), default=1)
    same_sequence = _as_int(observed.get("same_section_role_sequence_repetition_count"), default=1)
    cluster_size = _as_int(observed.get("observed_signature_cluster_size"), default=1)
    forbidden_present = _dedupe(observed.get("forbidden_surface_classes_present") or [])
    min_anchor_count = _min_required_anchor_count(family, expected_anchor_roles)

    if missing_anchor_roles and observation_anchor_count < min_anchor_count:
        blockers.append(BLOCKER_REQUIRED_ANCHOR_MISSING)
    if reception_anchor_count <= 0:
        blockers.append(BLOCKER_RECEPTION_ANCHOR_MISSING)
    if generic_count > 0 and (observation_anchor_count < min_anchor_count or reception_anchor_count <= 0):
        blockers.append(BLOCKER_GENERIC_RECEPTION_SURFACE)
    if _as_bool(observed.get("comfort_only_surface_detected")) or (
        generic_count > 0 and observation_anchor_count <= 0 and reception_anchor_count > 0
    ):
        blockers.append(BLOCKER_COMFORT_ONLY_SURFACE)
    if question_count > 0 and observation_anchor_count <= 0 and reception_anchor_count <= 0:
        blockers.append(BLOCKER_QUESTION_ONLY_SURFACE)
    if question_count > 0 and question_position in {"before_reception", "primary", "opening"}:
        blockers.append(BLOCKER_QUESTION_BEFORE_RECEPTION)
    if same_closing >= 3 or same_sequence >= 3 or cluster_size >= 3:
        blockers.append(BLOCKER_REPEATED_SURFACE_SIGNATURE)
    if _as_bool(observed.get("mirror_only_detected")):
        blockers.append(BLOCKER_MIRROR_ONLY_SURFACE)
    if forbidden_present:
        blockers.append(BLOCKER_FORBIDDEN_SURFACE_CLASS_PRESENT)
    if _safe_identifier(observed.get("observed_temperature_profile")) == "generic_reception_flattened":
        blockers.append(BLOCKER_FAMILY_TEMPERATURE_FLATTENED)
    if COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION in coverage_slices and (
        _as_bool(observed.get("normal_rebuild_risk")) or "source_unavailable_recast_as_normal_rebuild" in forbidden_present
    ):
        blockers.append(BLOCKER_SOURCE_UNAVAILABLE_NORMAL_REBUILD_RISK)
    return _dedupe(blockers)


def _verdict(blockers: Sequence[str], *, family: str) -> str:
    blocker_set = set(blockers)
    repair_blockers = {
        BLOCKER_GENERIC_RECEPTION_SURFACE,
        BLOCKER_REPEATED_SURFACE_SIGNATURE,
        BLOCKER_QUESTION_ONLY_SURFACE,
        BLOCKER_QUESTION_BEFORE_RECEPTION,
        BLOCKER_RECEPTION_ANCHOR_MISSING,
        BLOCKER_FORBIDDEN_SURFACE_CLASS_PRESENT,
        BLOCKER_SOURCE_UNAVAILABLE_NORMAL_REBUILD_RISK,
    }
    if blocker_set & repair_blockers:
        return VERDICT_REPAIR_REQUIRED
    if BLOCKER_REQUIRED_ANCHOR_MISSING in blocker_set or BLOCKER_MIRROR_ONLY_SURFACE in blocker_set:
        return VERDICT_YELLOW
    if family == FAMILY_SELF_DENIAL and blocker_set:
        return VERDICT_YELLOW
    return VERDICT_PASS


def _correction_requirements(
    *,
    family: str,
    policy: Mapping[str, Any] | None,
    detected_blockers: Sequence[str],
    missing_anchor_roles: Sequence[str],
) -> dict[str, Any]:
    correction_required = bool(detected_blockers)
    section_policy = _policy_section(policy)
    correction = {
        "correction_required": correction_required,
        "correction_kind": "surface_signature_role_specificity" if correction_required else "none",
        "target_layers": _dedupe(_CORRECTION_TARGET_LAYERS_BY_FAMILY_20260610.get(family, ())),
        "restore_missing_anchor_roles": _dedupe(missing_anchor_roles),
        "preserve_expected_section_role_sequence": _expected_section_sequence(policy),
        "required_reception_section": bool(section_policy.get("requires_reception_section", True)),
        "question_only_forbidden": True,
        "generic_comfort_template_forbidden": True,
        "same_closing_family_repetition_limit": 2,
        "same_section_role_sequence_repetition_limit": 2,
        "closing_only_variation_not_sufficient": True,
        "fixed_sentence_template_allowed": False,
        "exact_output_allowed": False,
        "case_specific_runtime_branch_allowed": False,
        "runtime_branching_uses_fixture_strings": False,
        "apply_to_runtime_now": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
    }
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        correction, source="p4_5.correction_requirements"
    )
    return correction


def build_product_readfeel_p4_surface_signature_audit_event_20260610(
    *,
    selected_case: Mapping[str, Any],
    family_policy: Mapping[str, Any] | None = None,
    boundary_slice_policy: Mapping[str, Any] | None = None,
    surface_signature_observation: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build one body-free P4-5 surface signature event."""

    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        selected_case, source="p4_5.selected_case"
    )
    if family_policy is not None:
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
            family_policy, source="p4_5.family_policy"
        )
    if boundary_slice_policy is not None:
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
            boundary_slice_policy, source="p4_5.boundary_slice_policy"
        )

    policy = family_policy or boundary_slice_policy
    case_ref_id = _safe_identifier(selected_case.get("case_ref_id") or selected_case.get("case_id"), default="case-ref")
    selected_family = _safe_identifier(selected_case.get("family"), default="unclassified")
    family = _policy_family(policy, selected_family)
    coverage_slices = _dedupe(selected_case.get("coverage_slices") or [])
    blocker_ids = _dedupe(selected_case.get("blocker_ids") or [])
    observation = _normalize_signature_observation(
        selected_case=selected_case,
        policy=policy,
        provided=surface_signature_observation,
    )
    expected_anchor_roles = _expected_anchor_roles(policy)
    observed_anchor_roles = _dedupe(observation.get("observed_anchor_roles") or [])
    missing_anchor_roles = _missing_anchor_roles(expected_anchor_roles, observed_anchor_roles)
    blockers = _detected_blockers(
        family=family,
        coverage_slices=coverage_slices,
        policy=policy,
        observed=observation,
    )
    p3_reported_generic = BLOCKER_GENERIC_RECEPTION_SURFACE in blocker_ids
    p3_reported_repeated = BLOCKER_REPEATED_SURFACE_SIGNATURE in blocker_ids
    signature_key = _surface_signature_key(family=family, observed=observation)
    verdict = _verdict(blockers, family=family)
    correction = _correction_requirements(
        family=family,
        policy=policy,
        detected_blockers=blockers,
        missing_anchor_roles=missing_anchor_roles,
    )

    event = {
        "schema_version": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_EVENT_VERSION_20260610,
        "source_phase": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
        "run_id": _safe_identifier(run_id, default="p4_5_surface_signature_event"),
        "case_ref_id": case_ref_id,
        "family": family,
        "selected_family": selected_family,
        "policy_id": _policy_id(policy),
        "coverage_slices": coverage_slices,
        "selection_groups": _dedupe(selected_case.get("selection_groups") or []),
        "p3_reported_blocker_ids": blocker_ids,
        "p3_reported_generic_reception_surface": p3_reported_generic,
        "p3_reported_repeated_surface_signature": p3_reported_repeated,
        "expected_temperature_profile": _expected_temperature_profile(policy),
        "observed_temperature_profile": _safe_identifier(
            observation.get("observed_temperature_profile"), default="unknown_temperature_profile"
        ),
        "expected_section_role_sequence": _expected_section_sequence(policy),
        "section_role_sequence": _dedupe(observation.get("section_role_sequence") or []),
        "section_role_sequence_matches_policy": _dedupe(observation.get("section_role_sequence") or [])
        == _expected_section_sequence(policy),
        "opening_shape_family": _safe_identifier(observation.get("opening_shape_family"), default="unknown_opening"),
        "closing_shape_family": _safe_identifier(observation.get("closing_shape_family"), default="unknown_closing"),
        "surface_signature_key": signature_key,
        "expected_anchor_roles": expected_anchor_roles,
        "observed_anchor_roles": observed_anchor_roles,
        "missing_anchor_roles": missing_anchor_roles,
        "required_anchor_role_minimum": _min_required_anchor_count(family, expected_anchor_roles),
        "observation_anchor_count": _as_int(observation.get("observation_anchor_count")),
        "reception_anchor_count": _as_int(observation.get("reception_anchor_count")),
        "generic_empathy_marker_count": _as_int(observation.get("generic_empathy_marker_count")),
        "question_count": _as_int(observation.get("question_count")),
        "question_position": _safe_identifier(observation.get("question_position"), default="none"),
        "same_closing_family_repetition_count": _as_int(
            observation.get("same_closing_family_repetition_count"), default=1
        ),
        "same_section_role_sequence_repetition_count": _as_int(
            observation.get("same_section_role_sequence_repetition_count"), default=1
        ),
        "observed_signature_cluster_size": _as_int(observation.get("observed_signature_cluster_size"), default=1),
        "mirror_only_detected": _as_bool(observation.get("mirror_only_detected")),
        "comfort_only_surface_detected": _as_bool(observation.get("comfort_only_surface_detected")),
        "forbidden_surface_classes_expected": _forbidden_surface_classes(policy),
        "forbidden_surface_classes_present": _dedupe(observation.get("forbidden_surface_classes_present") or []),
        "generic_reception_surface_detected": BLOCKER_GENERIC_RECEPTION_SURFACE in blockers,
        "repeated_surface_signature_detected": BLOCKER_REPEATED_SURFACE_SIGNATURE in blockers,
        "family_temperature_flattened_detected": BLOCKER_FAMILY_TEMPERATURE_FLATTENED in blockers,
        "question_only_surface_detected": BLOCKER_QUESTION_ONLY_SURFACE in blockers,
        "question_before_reception_detected": BLOCKER_QUESTION_BEFORE_RECEPTION in blockers,
        "required_anchor_missing_detected": BLOCKER_REQUIRED_ANCHOR_MISSING in blockers,
        "reception_anchor_missing_detected": BLOCKER_RECEPTION_ANCHOR_MISSING in blockers,
        "source_unavailable_boundary_kept": not (
            BLOCKER_SOURCE_UNAVAILABLE_NORMAL_REBUILD_RISK in blockers
        ),
        "detected_blockers": blockers,
        "verdict": verdict,
        "surface_specificity_correction_required": bool(blockers),
        "surface_specificity_correction_requirements": correction,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": True,
        "p4_2_material_audit_used_for_context": False,
        "p4_3_surface_requirement_boundary_respected": True,
        "p4_4_family_tuning_policy_used": bool(policy),
        "p4_5_surface_specificity_audit_ready": True,
        "p5_connection_allowed": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        event, source=f"p4_5.event.{case_ref_id}"
    )
    return event


def _make_summary(*, events: Sequence[Mapping[str, Any]], run_id: str) -> dict[str, Any]:
    families = Counter(_clean(event.get("family")) for event in events)
    blockers = Counter(
        blocker
        for event in events
        for blocker in _dedupe(event.get("detected_blockers") or [])
    )
    verdicts = Counter(_clean(event.get("verdict")) for event in events)
    signature_keys = Counter(_clean(event.get("surface_signature_key")) for event in events)
    repeated_case_refs = [
        _safe_identifier(event.get("case_ref_id"))
        for event in events
        if event.get("repeated_surface_signature_detected") is True
    ]
    generic_case_refs = [
        _safe_identifier(event.get("case_ref_id"))
        for event in events
        if event.get("generic_reception_surface_detected") is True
    ]
    repair_case_refs = [
        _safe_identifier(event.get("case_ref_id"))
        for event in events
        if event.get("verdict") == VERDICT_REPAIR_REQUIRED
    ]
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610,
        "source_phase": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
        "run_id": _safe_identifier(run_id, default="p4_5_surface_signature_audit"),
        "audit_profile": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610,
        "audited_case_count": len(events),
        "family_counts": dict(families),
        "verdict_counts": dict(verdicts),
        "detected_blocker_counts": dict(blockers),
        "unique_surface_signature_count": len(signature_keys),
        "generic_reception_surface_detected_count": int(blockers.get(BLOCKER_GENERIC_RECEPTION_SURFACE, 0)),
        "repeated_surface_signature_detected_count": int(blockers.get(BLOCKER_REPEATED_SURFACE_SIGNATURE, 0)),
        "family_temperature_flattened_detected_count": int(blockers.get(BLOCKER_FAMILY_TEMPERATURE_FLATTENED, 0)),
        "question_only_surface_detected_count": int(blockers.get(BLOCKER_QUESTION_ONLY_SURFACE, 0)),
        "generic_reception_surface_detected_case_refs": generic_case_refs,
        "repeated_surface_signature_detected_case_refs": repeated_case_refs,
        "repair_required_case_refs": repair_case_refs,
        "main_target_family_ids": [FAMILY_DAILY_UNPLEASANT, FAMILY_STRUCTURE_QUESTION],
        "yellow_review_family_ids": [FAMILY_SELF_DENIAL],
        "boundary_regression_family_ids": [
            FAMILY_LOW_INFORMATION_SHORT,
            FAMILY_DAILY_POSITIVE,
            FAMILY_RELATIONSHIP_BOUNDARY,
            FAMILY_LIMITED_GROUNDING,
        ],
        "boundary_regression_slice_ids": [
            "limited_grounding",
            COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION,
            COVERAGE_SLICE_HISTORY_LINE_ELIGIBLE,
        ],
        "daily_unpleasant_signature_review_ready": families.get(FAMILY_DAILY_UNPLEASANT, 0) > 0,
        "structure_question_signature_review_ready": families.get(FAMILY_STRUCTURE_QUESTION, 0) > 0,
        "self_denial_yellow_signature_review_ready": families.get(FAMILY_SELF_DENIAL, 0) > 0,
        "surface_specificity_correction_plan_ready": True,
        "closing_only_variation_not_sufficient": True,
        "exact_comment_text_locked": False,
        "fixed_sentence_template_added": False,
        "case_specific_runtime_branch": False,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": True,
        "p4_2_material_audit_used_for_context": True,
        "p4_3_surface_requirement_boundary_respected": True,
        "p4_4_family_tuning_policy_used": True,
        "p4_5_surface_specificity_audit_ready": True,
        "p5_connection_allowed": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        summary, source="p4_5.summary"
    )
    return summary


def build_product_readfeel_p4_surface_signature_audit_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    family_tuning_policy_payload: Mapping[str, Any] | None = None,
    surface_signature_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the P4-5 body-free surface signature audit packet."""

    run = _safe_identifier(run_id, default="p4_5_surface_signature_audit")
    if target_case_selection_payload is not None:
        assert_product_readfeel_p4_target_case_selection_meta_only_20260610(
            target_case_selection_payload, source="p4_5.source_p4_1_target_selection"
        )
    if material_audit_payload is not None:
        assert_product_readfeel_p4_material_audit_meta_only_20260610(
            material_audit_payload, source="p4_5.source_p4_2_material_audit"
        )
    if family_tuning_policy_payload is not None:
        assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
            family_tuning_policy_payload, source="p4_5.source_p4_4_family_policy"
        )
    policy_payload = family_tuning_policy_payload or build_product_readfeel_p4_family_tuning_policy_20260610(
        target_case_selection_payload=target_case_selection_payload,
        material_audit_payload=material_audit_payload,
        run_id=f"{run}_source_p4_4_family_policy",
    )
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(
        policy_payload, source="p4_5.policy_payload"
    )
    selected_cases = _selected_cases(target_case_selection_payload)
    if not selected_cases:
        # The policy packet may have been built from P4-1; use its body-free case links as a fallback.
        linked = policy_payload.get("family_case_policy_links") or []
        if isinstance(linked, Sequence) and not isinstance(linked, (str, bytes, bytearray)):
            selected_cases = [item for item in linked if isinstance(item, Mapping)]
    observations_by_id = surface_signature_observations_by_case_ref_id or {}
    if observations_by_id:
        assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
            observations_by_id, source="p4_5.surface_signature_observations_by_case_ref_id"
        )
    family_policies_by_family = {
        _safe_identifier(policy.get("family")): policy for policy in _family_policies(policy_payload)
    }
    boundary_policies_by_slice = {
        _safe_identifier(policy.get("coverage_slice")): policy
        for policy in _boundary_slice_policies(policy_payload)
    }
    events: list[dict[str, Any]] = []
    for selected_case in selected_cases:
        case_ref_id = _safe_identifier(selected_case.get("case_ref_id") or selected_case.get("case_id"), default="case-ref")
        policy = _policy_for_case(
            selected_case=selected_case,
            family_policies_by_family=family_policies_by_family,
            boundary_policies_by_slice=boundary_policies_by_slice,
        )
        event = build_product_readfeel_p4_surface_signature_audit_event_20260610(
            selected_case=selected_case,
            family_policy=policy if policy and policy.get("family") else None,
            boundary_slice_policy=policy if policy and policy.get("coverage_slice") else None,
            surface_signature_observation=observations_by_id.get(case_ref_id),
            run_id=f"{run}_{case_ref_id}",
        )
        events.append(event)
    summary = _make_summary(events=events, run_id=run)
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610,
        "run_id": run,
        "source_step": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
        "source_phase": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
        "source": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SOURCE_20260610,
        "audit_profile": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610,
        "surface_signature_events": events,
        "summary": summary,
        "runtime_owner_reference_only": True,
        "runtime_policy_connection_applied": False,
        "runtime_mutation_applied_by_p4_5": False,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": bool(target_case_selection_payload),
        "p4_2_material_audit_used_for_context": bool(material_audit_payload),
        "p4_3_surface_requirement_boundary_respected": True,
        "p4_4_family_tuning_policy_used": True,
        "p4_5_surface_specificity_audit_ready": True,
        "p5_connection_allowed": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        payload, source="p4_5.audit"
    )
    return payload


def build_product_readfeel_p4_surface_signature_audit_public_summary_20260610(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        payload, source="p4_5.public_summary_source"
    )
    summary = dict(payload.get("summary") or {})
    public_summary = {
        "schema_version": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610,
        "source_phase": PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610,
        "run_id": _safe_identifier(payload.get("run_id"), default="p4_5_surface_signature_audit"),
        "audit_profile": _clean(payload.get("audit_profile")),
        "audited_case_count": int(summary.get("audited_case_count") or 0),
        "family_counts": dict(summary.get("family_counts") or {}),
        "verdict_counts": dict(summary.get("verdict_counts") or {}),
        "detected_blocker_counts": dict(summary.get("detected_blocker_counts") or {}),
        "unique_surface_signature_count": int(summary.get("unique_surface_signature_count") or 0),
        "generic_reception_surface_detected_count": int(
            summary.get("generic_reception_surface_detected_count") or 0
        ),
        "repeated_surface_signature_detected_count": int(
            summary.get("repeated_surface_signature_detected_count") or 0
        ),
        "generic_reception_surface_detected_case_refs": _dedupe(
            summary.get("generic_reception_surface_detected_case_refs") or []
        ),
        "repeated_surface_signature_detected_case_refs": _dedupe(
            summary.get("repeated_surface_signature_detected_case_refs") or []
        ),
        "repair_required_case_refs": _dedupe(summary.get("repair_required_case_refs") or []),
        "surface_specificity_correction_plan_ready": bool(
            summary.get("surface_specificity_correction_plan_ready")
        ),
        "closing_only_variation_not_sufficient": bool(summary.get("closing_only_variation_not_sufficient")),
        "p4_5_surface_specificity_audit_ready": bool(summary.get("p4_5_surface_specificity_audit_ready")),
        "p5_connection_allowed": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610(
        public_summary, source="p4_5.public_summary"
    )
    return public_summary


def dump_product_readfeel_p4_surface_signature_audit_public_summary_20260610(
    payload: Mapping[str, Any],
) -> str:
    public_summary = build_product_readfeel_p4_surface_signature_audit_public_summary_20260610(payload)
    return json.dumps(public_summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "BLOCKER_COMFORT_ONLY_SURFACE",
    "BLOCKER_FAMILY_TEMPERATURE_FLATTENED",
    "BLOCKER_FORBIDDEN_SURFACE_CLASS_PRESENT",
    "BLOCKER_GENERIC_RECEPTION_SURFACE",
    "BLOCKER_MIRROR_ONLY_SURFACE",
    "BLOCKER_QUESTION_BEFORE_RECEPTION",
    "BLOCKER_QUESTION_ONLY_SURFACE",
    "BLOCKER_RECEPTION_ANCHOR_MISSING",
    "BLOCKER_REPEATED_SURFACE_SIGNATURE",
    "BLOCKER_REQUIRED_ANCHOR_MISSING",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_EVENT_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_PROFILE_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_STEP_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SURFACE_SIGNATURE_AUDIT_VERSION_20260610",
    "VERDICT_PASS",
    "VERDICT_REPAIR_REQUIRED",
    "VERDICT_YELLOW",
    "assert_product_readfeel_p4_surface_signature_audit_meta_only_20260610",
    "build_product_readfeel_p4_surface_signature_audit_20260610",
    "build_product_readfeel_p4_surface_signature_audit_event_20260610",
    "build_product_readfeel_p4_surface_signature_audit_public_summary_20260610",
    "dump_product_readfeel_p4_surface_signature_audit_public_summary_20260610",
]
