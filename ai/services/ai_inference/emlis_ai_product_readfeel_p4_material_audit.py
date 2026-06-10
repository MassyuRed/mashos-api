# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-2 material audit for Product Read Feel family tuning.

P4-2 is a diagnostic layer.  It uses the P4-1 body-free target case refs and
local synthetic case material only long enough to rebuild structural material
metadata.  The returned audit packet keeps only case ids, family/slice ids,
visible material slots, material-quality families, public-surface requirement
shape ids, and blocker flags.

It does not render Emlis output, keep raw input, keep ``comment_text`` bodies,
change runtime gates, strengthen P5 visible surfaces, or alter RN/API/DB
contracts.  Route overrides are accepted only as local audit replay material so
that the P3-9 ``rich_input_low_information_overroute`` blocker can be
reproduced in a body-free way.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    VISIBLE_SLOT_ACTION,
    VISIBLE_SLOT_CHANGE,
    VISIBLE_SLOT_EMOTION_DIRECTION,
    VISIBLE_SLOT_EVENT,
    VISIBLE_SLOT_RELATIONSHIP,
    VISIBLE_SLOT_TARGET,
    VISIBLE_SLOT_TIME,
    VISIBLE_SLOT_UNRESOLVED_WEIGHT,
    VISIBLE_SLOT_VALUE,
    assert_emlis_input_material_bundle_meta,
    build_emlis_input_material_bundle_meta,
)
from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import FAMILY_STRUCTURE_QUESTION
from emlis_ai_product_readfeel_p4_target_case_selection import (
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610,
)
from emlis_ai_product_readfeel_rubric import assert_product_readfeel_rubric_meta_only
from emlis_ai_public_surface_requirement import (
    LOW_INFORMATION_SHAPE_KIND,
    PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    assert_public_surface_requirement_decision,
    assert_public_surface_requirement_decision_meta_only,
    resolve_public_surface_requirement,
)

PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.material_audit.20260610.v1"
)
PRODUCT_READFEEL_P4_MATERIAL_AUDIT_EVENT_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.material_audit_event.20260610.v1"
)
PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.material_audit_summary.20260610.v1"
)
PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610: Final = (
    "P4-2_Rich_Input_Material_Audit"
)
PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SOURCE_20260610: Final = (
    "Cocolon_EmlisAI_P4_FamilyProductTuning_MaterialAudit_20260610"
)
PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610: Final = (
    "p4_2_rich_input_low_information_overroute_reproduction"
)

BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE: Final = "rich_input_low_information_overroute"
BLOCKER_QUESTION_ONLY_SURFACE: Final = "question_only_surface"
BLOCKER_QUESTION_DOMINANT_SURFACE: Final = "question_dominant_surface"
BLOCKER_QUESTION_BEFORE_RECEPTION: Final = "question_before_reception"
BLOCKER_LIMITED_GROUNDING_COLLAPSED_TO_QUESTION: Final = "limited_grounding_collapsed_to_question"
BLOCKER_SOURCE_UNAVAILABLE_RECAST_AS_NORMAL_REBUILD: Final = "source_unavailable_recast_as_normal_rebuild"

COVERAGE_SLICE_LIMITED_GROUNDING: Final = "limited_grounding"
COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION: Final = "source_unavailable_high_information"

SLOT_GROUP_EVENTISH: Final = "eventish"
SLOT_GROUP_REACTIONISH: Final = "reactionish"
SLOT_GROUP_RELATIONSHIP_OR_TARGET: Final = "relationship_or_target"
SLOT_GROUP_CHANGE_OR_VALUE: Final = "change_or_value"
SLOT_GROUP_STRUCTURE_QUESTION: Final = "structure_question"

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
        "material_quality_forced_to_eligible",
        "low_information_globally_relaxed",
        "source_unavailable_recast_as_normal_rebuild",
        "normal_rebuild_used_for_source_unavailable",
        "public_meta_body_allowed",
    }
)


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
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set, frozenset)):
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
        text_value = _clean(value)
        if text_value and text_value not in out:
            out.append(text_value)
    return out


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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


def assert_product_readfeel_p4_material_audit_meta_only_20260610(
    payload: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    *,
    source: str = "p4_material_audit",
) -> None:
    """Reject body-bearing or runtime-mutating P4-2 material audit payloads."""

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


def _false_boundary_flags() -> dict[str, bool]:
    return {
        "body_free_case_references_only": True,
        "local_case_material_available": True,
        "local_case_material_retained_here": False,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
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
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "material_quality_forced_to_eligible": False,
        "low_information_globally_relaxed": False,
        "source_unavailable_recast_as_normal_rebuild": False,
        "normal_rebuild_used_for_source_unavailable": False,
        "public_meta_body_allowed": False,
    }


def _case_ref_id(case: Mapping[str, Any]) -> str:
    return _safe_identifier(case.get("case_ref_id") or case.get("case_id"), default="")


def _family(case: Mapping[str, Any]) -> str:
    return _clean(case.get("family") or case.get("product_readfeel_family"))


def _coverage_slices(case: Mapping[str, Any]) -> list[str]:
    return _dedupe(case.get("coverage_slices"))


def _current_case_map(local_cases: Sequence[Mapping[str, Any]] | None) -> dict[str, Mapping[str, Any]]:
    if not isinstance(local_cases, Sequence) or isinstance(local_cases, (str, bytes, bytearray)):
        raise ValueError("P4-2 material audit requires local synthetic baseline cases")
    out: dict[str, Mapping[str, Any]] = {}
    for case in local_cases:
        if not isinstance(case, Mapping):
            continue
        case_id = _case_ref_id(case)
        if case_id:
            out[case_id] = case
    if not out:
        raise ValueError("P4-2 material audit could not build a local case map")
    return out


def _visible_slot_groups(
    *,
    family: str,
    visible_slots: Sequence[str],
    relation_material_ids: Sequence[str],
) -> list[str]:
    visible = set(_dedupe(visible_slots))
    relation_ids = set(_dedupe(relation_material_ids))
    groups: list[str] = []
    if visible.intersection({VISIBLE_SLOT_EVENT, VISIBLE_SLOT_ACTION, VISIBLE_SLOT_TIME}):
        groups.append(SLOT_GROUP_EVENTISH)
    if visible.intersection({VISIBLE_SLOT_EMOTION_DIRECTION, VISIBLE_SLOT_UNRESOLVED_WEIGHT}):
        groups.append(SLOT_GROUP_REACTIONISH)
    if visible.intersection({VISIBLE_SLOT_RELATIONSHIP, VISIBLE_SLOT_TARGET}):
        groups.append(SLOT_GROUP_RELATIONSHIP_OR_TARGET)
    if visible.intersection({VISIBLE_SLOT_CHANGE, VISIBLE_SLOT_VALUE}) or relation_ids.intersection(
        {"value_preservation", "small_change_preservation", "future_intention", "gratitude_or_return_intent"}
    ):
        groups.append(SLOT_GROUP_CHANGE_OR_VALUE)
    if family == FAMILY_STRUCTURE_QUESTION or relation_ids.intersection(
        {"self_observation", "value_or_self_understanding_material", "self_understanding_learning"}
    ):
        groups.append(SLOT_GROUP_STRUCTURE_QUESTION)
    return _dedupe(groups)


def _rich_input_candidate(*, visible_slots: Sequence[str], visible_slot_groups: Sequence[str]) -> bool:
    visible = set(_dedupe(visible_slots))
    groups = set(_dedupe(visible_slot_groups))
    if not groups:
        return False
    has_eventish = SLOT_GROUP_EVENTISH in groups or bool(visible.intersection({VISIBLE_SLOT_EVENT, VISIBLE_SLOT_ACTION}))
    has_reactionish = SLOT_GROUP_REACTIONISH in groups
    has_structure = SLOT_GROUP_STRUCTURE_QUESTION in groups
    has_meaning = bool(groups.intersection({SLOT_GROUP_RELATIONSHIP_OR_TARGET, SLOT_GROUP_CHANGE_OR_VALUE}))
    if has_eventish and has_reactionish and len(visible) >= 3:
        return True
    if has_structure and has_reactionish and len(visible) >= 3:
        return True
    if has_reactionish and has_meaning and len(groups) >= 3 and len(visible) >= 4:
        return True
    return False


def _surface_requirement_family(decision: Mapping[str, Any]) -> str:
    return _clean(decision.get("surface_requirement_family"))


def _shape_kind(decision: Mapping[str, Any]) -> str:
    shape = _as_mapping(decision.get("required_comment_text_shape"))
    return _clean(shape.get("kind"))


def _decision_sources(decision: Mapping[str, Any]) -> list[str]:
    return _dedupe(decision.get("decision_sources"))


def _low_information_route_selected(decision: Mapping[str, Any]) -> bool:
    return bool(
        _surface_requirement_family(decision) == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
        or _shape_kind(decision) == LOW_INFORMATION_SHAPE_KIND
        or _clean(decision.get("material_quality_family")) == MATERIAL_QUALITY_LOW_INFORMATION
        or "low_information_material" in _decision_sources(decision)
        or "low_information_reception_required" in _decision_sources(decision)
        or decision.get("low_information_allowed") is True
    )


def _limited_grounding_requested(decision: Mapping[str, Any]) -> bool:
    return bool(
        _surface_requirement_family(decision) == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
        and (
            _clean(decision.get("material_quality_family")) == MATERIAL_QUALITY_LIMITED_GROUNDING
            or "limited_grounding_reception_required" in _decision_sources(decision)
        )
    )


def _question_blocker(surface_observation: Mapping[str, Any]) -> str:
    values = {
        _clean(surface_observation.get("blocker_code")),
        _clean(surface_observation.get("question_dominance_blocker")),
        _clean(surface_observation.get("first_blocker_code")),
    }
    guard = _as_mapping(surface_observation.get("question_dominance_guard"))
    if guard:
        if guard.get("question_before_reception") is True:
            return BLOCKER_QUESTION_BEFORE_RECEPTION
        if guard.get("question_dominant") is True:
            return BLOCKER_QUESTION_DOMINANT_SURFACE
        if guard.get("reception_section_present") is False and guard.get("question_surface_present") is True:
            return BLOCKER_QUESTION_ONLY_SURFACE
    for value in values:
        lowered = value.lower()
        if "question_before_reception" in lowered:
            return BLOCKER_QUESTION_BEFORE_RECEPTION
        if "question_dominant" in lowered:
            return BLOCKER_QUESTION_DOMINANT_SURFACE
        if "question_only" in lowered or "question-only" in lowered:
            return BLOCKER_QUESTION_ONLY_SURFACE
    if surface_observation.get("question_only_surface_detected") is True:
        return BLOCKER_QUESTION_ONLY_SURFACE
    if surface_observation.get("question_dominant_surface_detected") is True:
        return BLOCKER_QUESTION_DOMINANT_SURFACE
    return ""


def _question_only_surface_detected(surface_observation: Mapping[str, Any]) -> bool:
    return bool(_question_blocker(surface_observation))


def _source_unavailable_boundary_kept(
    *,
    coverage_slices: Sequence[str],
    surface_observation: Mapping[str, Any],
) -> bool:
    if COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION not in set(_dedupe(coverage_slices)):
        return True
    source_kind = _clean(surface_observation.get("candidate_source_kind") or surface_observation.get("source_kind"))
    recovery_kind = _clean(surface_observation.get("recovery_route_kind") or surface_observation.get("recovery_kind"))
    if surface_observation.get("source_unavailable_recast_as_normal_rebuild") is True:
        return False
    if source_kind == "normal_observation_rebuild_candidate" or recovery_kind == "normal_observation_rebuild_candidate":
        return False
    return True


def _make_surface_requirement(
    *,
    current_case_material: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    selected_case: Mapping[str, Any],
    audit_route_override: Mapping[str, Any] | None,
) -> dict[str, Any]:
    route_meta = dict(material_meta)
    if audit_route_override:
        assert_product_readfeel_p4_material_audit_meta_only_20260610(
            audit_route_override,
            source="p4_2.audit_route_override",
        )
        route_meta.update(dict(audit_route_override))
    decision = resolve_public_surface_requirement(
        current_input=_as_mapping(current_case_material.get("current_input")),
        material_route=route_meta,
        composer_meta={},
        diagnostic_summary={},
        fixture_family_meta={
            "family": _family(selected_case),
            "coverage_slices": _coverage_slices(selected_case),
            "blocker_ids": _dedupe(selected_case.get("blocker_ids")),
        },
        comment_text_present=False,
        # P4-2 keeps the old overroute reproducible as a local replay.  P4-3
        # enables the correction for normal boundary decisions and verifies it
        # in its own tests, without erasing this diagnostic fixture.
        p4_3_boundary_correction_enabled=not bool(audit_route_override),
    )
    assert_public_surface_requirement_decision(decision)
    assert_public_surface_requirement_decision_meta_only(decision)
    return decision


def build_product_readfeel_p4_material_audit_event_20260610(
    *,
    selected_case: Mapping[str, Any],
    local_case_material: Mapping[str, Any],
    run_id: str | None = None,
    audit_route_override: Mapping[str, Any] | None = None,
    surface_observation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one body-free P4-2 material audit event from local case material."""

    if not isinstance(selected_case, Mapping):
        raise ValueError("P4-2 selected_case must be a mapping")
    if not isinstance(local_case_material, Mapping):
        raise ValueError("P4-2 local_case_material must be a mapping")
    surface_meta = dict(surface_observation or {})
    if surface_meta:
        assert_product_readfeel_p4_material_audit_meta_only_20260610(
            surface_meta,
            source="p4_2.surface_observation",
        )

    case_ref_id = _case_ref_id(selected_case) or _case_ref_id(local_case_material)
    if not case_ref_id:
        raise ValueError("P4-2 material audit requires a body-free case_ref_id")
    if _case_ref_id(local_case_material) and _case_ref_id(local_case_material) != case_ref_id:
        raise ValueError(f"P4-2 local material case id mismatch for {case_ref_id}")

    current_case_material = _as_mapping(local_case_material)
    current_material = _as_mapping(current_case_material.get("current_input"))
    if not current_material:
        raise ValueError(f"P4-2 local material missing current input for {case_ref_id}")
    material_meta = build_emlis_input_material_bundle_meta(current_material)
    assert_emlis_input_material_bundle_meta(material_meta)
    public_requirement = _make_surface_requirement(
        current_case_material=current_case_material,
        material_meta=material_meta,
        selected_case=selected_case,
        audit_route_override=audit_route_override,
    )

    family = _family(selected_case) or _family(local_case_material)
    coverage_slices = _dedupe(_coverage_slices(selected_case) or _coverage_slices(local_case_material))
    visible_slots = _dedupe(material_meta.get("visible_material_slots"))
    unknown_slots = _dedupe(material_meta.get("unknown_slots"))
    relation_ids = _dedupe(material_meta.get("relation_material_ids") or material_meta.get("generic_relation_material_ids"))
    slot_groups = _visible_slot_groups(
        family=family,
        visible_slots=visible_slots,
        relation_material_ids=relation_ids,
    )
    rich_candidate = _rich_input_candidate(visible_slots=visible_slots, visible_slot_groups=slot_groups)
    low_info_route = _low_information_route_selected(public_requirement)
    limited_grounding = _limited_grounding_requested(public_requirement)
    question_only = _question_only_surface_detected(surface_meta)
    question_blocker = _question_blocker(surface_meta)
    source_boundary_kept = _source_unavailable_boundary_kept(
        coverage_slices=coverage_slices,
        surface_observation=surface_meta,
    )
    detected_blockers: list[str] = []
    if rich_candidate and (low_info_route or question_only):
        detected_blockers.append(BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE)
    if limited_grounding and question_only:
        detected_blockers.append(BLOCKER_LIMITED_GROUNDING_COLLAPSED_TO_QUESTION)
    if question_blocker:
        detected_blockers.append(question_blocker)
    if not source_boundary_kept:
        detected_blockers.append(BLOCKER_SOURCE_UNAVAILABLE_RECAST_AS_NORMAL_REBUILD)

    route_material_quality = _clean(public_requirement.get("material_quality_family"))
    event = {
        "schema_version": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_EVENT_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_EVENT_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610,
        "run_id": _safe_identifier(run_id, default="p4_2_material_audit_event"),
        "case_ref_id": case_ref_id,
        "family": family,
        "coverage_slices": coverage_slices,
        "selection_groups": _dedupe(selected_case.get("selection_groups")),
        "p3_target_blocker_ids": _dedupe(selected_case.get("blocker_ids")),
        "p3_target_layers": _dedupe(selected_case.get("target_layers")),
        "p3_reported_rich_input_low_information_overroute": BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE
        in set(_dedupe(selected_case.get("blocker_ids"))),
        "visible_material_slots": visible_slots,
        "visible_material_slot_count": len(visible_slots),
        "visible_slot_groups_present": slot_groups,
        "visible_slot_group_count": len(slot_groups),
        "unknown_slots": unknown_slots,
        "unknown_slot_count": len(unknown_slots),
        "relation_material_ids": relation_ids,
        "relation_material_count": len(relation_ids),
        "material_quality": _clean(material_meta.get("material_quality")),
        "route_material_quality_family": route_material_quality,
        "public_surface_requirement": {
            "schema_version": PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
            "surface_requirement_family": _surface_requirement_family(public_requirement),
            "required_comment_text_shape_kind": _shape_kind(public_requirement),
            "two_stage_required": bool(public_requirement.get("two_stage_required")),
            "plain_state_answer_allowed": bool(public_requirement.get("plain_state_answer_allowed")),
            "low_information_allowed": bool(public_requirement.get("low_information_allowed")),
            "decision_sources": _decision_sources(public_requirement),
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "required_comment_text_shape_kind": _shape_kind(public_requirement),
        "low_information_route_selected": low_info_route,
        "limited_grounding_requested": limited_grounding,
        "source_unavailable_boundary_kept": source_boundary_kept,
        "question_only_surface_detected": question_only,
        "question_dominance_blocker": question_blocker or "none",
        "rich_input_candidate": rich_candidate,
        "rich_input_low_information_overroute_detected": bool(
            BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE in detected_blockers
        ),
        "detected_blockers": _dedupe(detected_blockers),
        "audit_replay_route_override_used": bool(audit_route_override),
        "audit_replay_only": bool(audit_route_override),
        "p4_2_material_audit_event_ready": True,
        "p4_3_surface_requirement_boundary_review_candidate": bool(
            BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE in detected_blockers
            or selected_case.get("main_target_case") is True
            or limited_grounding
            or COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION in set(coverage_slices)
        ),
        **_false_boundary_flags(),
    }
    assert_product_readfeel_p4_material_audit_meta_only_20260610(event, source="p4_2.event")
    return event


def _selected_cases_from_payload(selection_payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(
        selection_payload,
        source="p4_2.source_p4_1_target_selection",
    )
    selected = selection_payload.get("selected_cases")
    if not isinstance(selected, Sequence) or isinstance(selected, (str, bytes, bytearray)):
        raise ValueError("P4-2 material audit requires P4-1 selected_cases")
    return [case for case in selected if isinstance(case, Mapping)]


def _make_summary(*, events: Sequence[Mapping[str, Any]], run_id: str) -> dict[str, Any]:
    family_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    surface_counts: Counter[str] = Counter()
    coverage_counts: Counter[str] = Counter()
    group_counts: Counter[str] = Counter()
    for event in events:
        family_counts[_clean(event.get("family"))] += 1
        blocker_counts.update(_dedupe(event.get("detected_blockers")))
        surface = _as_mapping(event.get("public_surface_requirement"))
        surface_counts[_clean(surface.get("surface_requirement_family"))] += 1
        coverage_counts.update(_dedupe(event.get("coverage_slices")))
        group_counts.update(_dedupe(event.get("visible_slot_groups_present")))

    p3_reported_refs = [
        _clean(event.get("case_ref_id"))
        for event in events
        if event.get("p3_reported_rich_input_low_information_overroute") is True
    ]
    detected_refs = [
        _clean(event.get("case_ref_id"))
        for event in events
        if event.get("rich_input_low_information_overroute_detected") is True
    ]
    p4_3_refs = [
        _clean(event.get("case_ref_id"))
        for event in events
        if event.get("p4_3_surface_requirement_boundary_review_candidate") is True
    ]
    summary = {
        "schema_version": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610,
        "run_id": run_id,
        "audit_profile": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": True,
        "p4_2_material_audit_ready": True,
        "p5_hold_fixed": True,
        "p5_connection_allowed": False,
        "selected_case_count": len(events),
        "audited_case_count": len(events),
        "family_counts": dict(sorted(family_counts.items())),
        "coverage_slice_counts": dict(sorted(coverage_counts.items())),
        "visible_slot_group_counts": dict(sorted(group_counts.items())),
        "surface_requirement_family_counts": dict(sorted(surface_counts.items())),
        "detected_blocker_counts": dict(sorted(blocker_counts.items())),
        "rich_input_candidate_count": sum(1 for event in events if event.get("rich_input_candidate") is True),
        "low_information_route_selected_count": sum(
            1 for event in events if event.get("low_information_route_selected") is True
        ),
        "limited_grounding_requested_count": sum(
            1 for event in events if event.get("limited_grounding_requested") is True
        ),
        "source_unavailable_boundary_case_count": sum(
            1
            for event in events
            if COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION in set(_dedupe(event.get("coverage_slices")))
        ),
        "source_unavailable_boundary_kept_count": sum(
            1
            for event in events
            if COVERAGE_SLICE_SOURCE_UNAVAILABLE_HIGH_INFORMATION in set(_dedupe(event.get("coverage_slices")))
            and event.get("source_unavailable_boundary_kept") is True
        ),
        "question_only_surface_detected_count": sum(
            1 for event in events if event.get("question_only_surface_detected") is True
        ),
        "p3_reported_rich_input_low_information_overroute_count": len(p3_reported_refs),
        "rich_input_low_information_overroute_detected_count": len(detected_refs),
        "p3_reported_rich_input_low_information_overroute_case_refs": p3_reported_refs,
        "rich_input_low_information_overroute_detected_case_refs": detected_refs,
        "p4_3_surface_requirement_boundary_candidate_case_refs": _dedupe(p4_3_refs),
        "p4_3_surface_requirement_boundary_review_ready": True,
        **_false_boundary_flags(),
    }
    assert_product_readfeel_p4_material_audit_meta_only_20260610(summary, source="p4_2.summary")
    return summary


def build_product_readfeel_p4_material_audit_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None,
    local_baseline_cases: Sequence[Mapping[str, Any]] | None,
    run_id: str | None = None,
    audit_route_overrides_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    surface_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the P4-2 body-free material audit packet."""

    if not isinstance(target_case_selection_payload, Mapping):
        raise ValueError("P4-2 material audit requires the P4-1 target case selection payload")
    selected_cases = _selected_cases_from_payload(target_case_selection_payload)
    if not selected_cases:
        raise ValueError("P4-2 material audit cannot run without selected cases")
    local_by_id = _current_case_map(local_baseline_cases)
    run_id_value = _safe_identifier(run_id or target_case_selection_payload.get("run_id"), default="p4_2_material_audit")
    overrides = dict(audit_route_overrides_by_case_ref_id or {})
    surface_observations = dict(surface_observations_by_case_ref_id or {})
    if overrides:
        assert_product_readfeel_p4_material_audit_meta_only_20260610(
            overrides,
            source="p4_2.audit_route_overrides_by_case_ref_id",
        )
    if surface_observations:
        assert_product_readfeel_p4_material_audit_meta_only_20260610(
            surface_observations,
            source="p4_2.surface_observations_by_case_ref_id",
        )

    events: list[dict[str, Any]] = []
    for selected_case in selected_cases:
        case_ref_id = _case_ref_id(selected_case)
        if case_ref_id not in local_by_id:
            raise ValueError(f"P4-2 local case material not found for {case_ref_id}")
        event = build_product_readfeel_p4_material_audit_event_20260610(
            selected_case=selected_case,
            local_case_material=local_by_id[case_ref_id],
            run_id=run_id_value,
            audit_route_override=overrides.get(case_ref_id),
            surface_observation=surface_observations.get(case_ref_id),
        )
        events.append(event)

    summary = _make_summary(events=events, run_id=run_id_value)
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610,
        "run_id": run_id_value,
        "audit_profile": PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610,
        "summary": summary,
        "material_audit_events": events,
        "p4_0_connection_freeze_respected": True,
        "p4_1_target_case_selection_used": True,
        "p4_2_material_audit_ready": True,
        "p5_hold_fixed": True,
        "p5_connection_allowed": False,
        **_false_boundary_flags(),
    }
    assert_product_readfeel_p4_material_audit_meta_only_20260610(payload, source="p4_2.audit")
    return payload


def build_product_readfeel_p4_material_audit_public_summary_20260610(
    audit_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(audit_payload or {})
    assert_product_readfeel_p4_material_audit_meta_only_20260610(payload, source="p4_2.public_summary_source")
    summary = dict(payload.get("summary") or {})
    events = [event for event in payload.get("material_audit_events") or [] if isinstance(event, Mapping)]
    public_summary = dict(summary)
    public_summary["schema_version"] = PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610
    public_summary["version"] = PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610
    public_summary["source"] = PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SOURCE_20260610
    public_summary["source_step"] = PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610
    public_summary["audited_case_refs"] = [
        {
            "case_ref_id": _clean(event.get("case_ref_id")),
            "family": _clean(event.get("family")),
            "coverage_slices": _dedupe(event.get("coverage_slices")),
            "visible_material_slots": _dedupe(event.get("visible_material_slots")),
            "visible_slot_groups_present": _dedupe(event.get("visible_slot_groups_present")),
            "material_quality": _clean(event.get("material_quality")),
            "route_material_quality_family": _clean(event.get("route_material_quality_family")),
            "surface_requirement_family": _clean(
                _as_mapping(event.get("public_surface_requirement")).get("surface_requirement_family")
            ),
            "rich_input_candidate": bool(event.get("rich_input_candidate")),
            "low_information_route_selected": bool(event.get("low_information_route_selected")),
            "rich_input_low_information_overroute_detected": bool(
                event.get("rich_input_low_information_overroute_detected")
            ),
            "detected_blockers": _dedupe(event.get("detected_blockers")),
        }
        for event in events
    ]
    public_summary.update(_false_boundary_flags())
    assert_product_readfeel_p4_material_audit_meta_only_20260610(public_summary, source="p4_2.public_summary")
    return public_summary


def dump_product_readfeel_p4_material_audit_public_summary_20260610(
    audit_payload: Mapping[str, Any] | None,
) -> str:
    summary = build_product_readfeel_p4_material_audit_public_summary_20260610(audit_payload)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "BLOCKER_LIMITED_GROUNDING_COLLAPSED_TO_QUESTION",
    "BLOCKER_QUESTION_BEFORE_RECEPTION",
    "BLOCKER_QUESTION_DOMINANT_SURFACE",
    "BLOCKER_QUESTION_ONLY_SURFACE",
    "BLOCKER_RICH_INPUT_LOW_INFORMATION_OVERROUTE",
    "BLOCKER_SOURCE_UNAVAILABLE_RECAST_AS_NORMAL_REBUILD",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_EVENT_VERSION_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SOURCE_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610",
    "SLOT_GROUP_CHANGE_OR_VALUE",
    "SLOT_GROUP_EVENTISH",
    "SLOT_GROUP_REACTIONISH",
    "SLOT_GROUP_RELATIONSHIP_OR_TARGET",
    "SLOT_GROUP_STRUCTURE_QUESTION",
    "assert_product_readfeel_p4_material_audit_meta_only_20260610",
    "build_product_readfeel_p4_material_audit_20260610",
    "build_product_readfeel_p4_material_audit_event_20260610",
    "build_product_readfeel_p4_material_audit_public_summary_20260610",
    "dump_product_readfeel_p4_material_audit_public_summary_20260610",
]
