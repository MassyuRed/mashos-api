# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 10 limited-family Structure Insight surface connection.

This module is intentionally narrow.  It may provide one soft insight seed for
families where a structural answer is explicitly useful, while leaving daily
reception and low-information inputs on the Product Read Feel v1 surface.  It
uses the Phase 9 Structure Insight Gate before any visible sentence is returned
and keeps all evaluation metadata text-free.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Final

from emlis_ai_input_material_bundle import MATERIAL_QUALITY_ELIGIBLE
from emlis_ai_structure_insight_candidate import (
    FORBIDDEN_CLAIMS_BASE,
    GATE_REQUIRED_BASE,
    MUST_NOT_SURFACE_AS,
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_EFFORT_RESIDUE,
    RELATION_EVENT_REACTION_LINK,
    RELATION_LONG_ARC_MULTIPLE_CORE,
    RELATION_MIXED_EMOTION_COEXISTENCE,
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    RELATION_UNCERTAINTY_EFFORT_PAIR,
    RELATION_VALUE_LINE_CROSSED,
    STRUCTURE_INSIGHT_CANDIDATE_VERSION,
)
from emlis_ai_structure_insight_gate import (
    GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE,
    build_structure_insight_gate_report,
    assert_structure_insight_gate_meta_only,
)

STRUCTURE_INSIGHT_SURFACE_VERSION: Final = "cocolon.emlis.structure_insight_surface.v1"
STRUCTURE_INSIGHT_SURFACE_FIELDS_VERSION: Final = "cocolon.emlis.structure_insight_surface.scorecard_fields.v1"
STRUCTURE_INSIGHT_SURFACE_PHASE10_STEP: Final = "Phase10_Structure_Insight_Surface_Limited_Family_Connection"
STRUCTURE_INSIGHT_SURFACE_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase10_StructureInsightSurface"

SECTION_OBSERVATION: Final = "observation"
SECTION_RECEPTION: Final = "reception"
MODE_STRUCTURE_QUESTION: Final = "structure_question_observation"
MODE_SELF_UNDERSTANDING: Final = "self_understanding_follow"
MODE_DAILY_UNPLEASANT: Final = "daily_unpleasant_reception"
MODE_LOW_INFORMATION: Final = "low_information_question"
MODE_DAILY_POSITIVE: Final = "daily_positive_reception"
FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
FAMILY_DAILY_UNPLEASANT: Final = "daily_unpleasant"
FAMILY_LOW_INFORMATION_SHORT: Final = "low_information_short"

LIMITED_STRUCTURE_INSIGHT_SURFACE_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
)
LIMITED_STRUCTURE_INSIGHT_SURFACE_MODE_IDS: Final[tuple[str, ...]] = (
    MODE_STRUCTURE_QUESTION,
    MODE_SELF_UNDERSTANDING,
)
STRUCTURE_INSIGHT_SURFACE_SUPPRESSED_MODE_IDS: Final[tuple[str, ...]] = (
    MODE_DAILY_UNPLEASANT,
    MODE_LOW_INFORMATION,
    MODE_DAILY_POSITIVE,
)

_BODY_KEY_FRAGMENTS: Final[tuple[str, ...]] = (
    "raw_input",
    "raw_text",
    "input_text",
    "memo",
    "memo_action",
    "emotion_details",
    "comment_text",
    "surface_text",
    "visible_text",
    "candidate_body",
    "reply_text",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    else:
        try:
            iterable = values  # type: ignore[assignment]
            iter(iterable)
        except TypeError:
            iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _line_meta(line: Any) -> Mapping[str, Any]:
    return _as_mapping(getattr(line, "meta", {}) or {})


def _line_roles(line: Any) -> list[str]:
    roles: list[str] = []
    for key in ("must_include_roles", "phrase_unit_roles", "role_phrase_keys"):
        roles.extend(_dedupe(getattr(line, key, None) or _line_meta(line).get(key)))
    source_line = _as_mapping(getattr(line, "source_sentence_plan_line", {}) or {})
    for key in ("must_include_roles", "phrase_unit_roles", "role_phrase_keys"):
        roles.extend(_dedupe(source_line.get(key)))
    return _dedupe(roles)


def _canonical_relation(value: Any) -> str:
    relation = _clean(value).lower()
    if relation in {"approach_avoidance", "desire_stagnation", "action_blocked", "pressure_gap", "blockage"}:
        return "approach_avoidance"
    if relation in {"contrast", "coexistence", "balance", "thought_action_discrepancy", "emotion_nesting"}:
        return "coexistence"
    if relation in {"recovery", "repair", "return", "load_accumulation", "repetition"}:
        return "recovery"
    if relation in {"boundary", "value_line", "priority_pressure"}:
        return "boundary"
    return relation or "event_reaction"


def _mode_from_meta(two_stage_meta: Mapping[str, Any]) -> str:
    for key in (
        "two_stage_reception_mode_id",
        "reception_mode_id",
        "two_stage_mode_context_reception_mode_id",
        "mode_id",
    ):
        mode = _clean(two_stage_meta.get(key))
        if mode:
            return mode
    return ""


def _coverage_group_from_line(line: Any, two_stage_meta: Mapping[str, Any]) -> str:
    line_meta = _line_meta(line)
    for key in ("coverage_group", "two_stage_coverage_group", "fixture_family", "product_readfeel_fixture_family"):
        value = _clean(line_meta.get(key) or two_stage_meta.get(key))
        if value:
            return value
    source_line = _as_mapping(getattr(line, "source_sentence_plan_line", {}) or {})
    for key in ("coverage_group", "fixture_family"):
        value = _clean(source_line.get(key))
        if value:
            return value
    return ""


def _section_from_inputs(section_id: str, two_stage_meta: Mapping[str, Any]) -> str:
    return _clean(section_id or two_stage_meta.get("two_stage_section_id"))


def _connectable_family(*, line: Any, section_id: str, two_stage_meta: Mapping[str, Any]) -> str:
    mode = _mode_from_meta(two_stage_meta)
    coverage_group = _coverage_group_from_line(line, two_stage_meta)
    if mode in {MODE_DAILY_UNPLEASANT, MODE_LOW_INFORMATION, MODE_DAILY_POSITIVE}:
        return ""
    if coverage_group in {FAMILY_DAILY_UNPLEASANT, FAMILY_LOW_INFORMATION_SHORT, "low_information"}:
        return ""
    if coverage_group == FAMILY_LONG_MEANING_ARC:
        return FAMILY_LONG_MEANING_ARC
    if mode == MODE_STRUCTURE_QUESTION:
        return FAMILY_STRUCTURE_QUESTION
    if mode == MODE_SELF_UNDERSTANDING:
        return FAMILY_SELF_UNDERSTANDING_FOLLOW
    return ""


def _relation_family_for(*, family: str, relation_type: str, roles: Iterable[str]) -> str:
    role_set = set(_dedupe(roles))
    relation = _canonical_relation(relation_type)
    if family == FAMILY_LONG_MEANING_ARC:
        return RELATION_LONG_ARC_MULTIPLE_CORE
    if family == FAMILY_SELF_UNDERSTANDING_FOLLOW:
        if role_set.intersection({"self_denial", "self_blame", "felt_state", "identity_claim"}):
            return RELATION_SELF_DENIAL_IDENTITY_SPLIT
        return RELATION_UNCERTAINTY_EFFORT_PAIR
    if relation == "approach_avoidance":
        return RELATION_DESIRE_BLOCKAGE_CONFLICT
    if relation == "coexistence":
        return RELATION_MIXED_EMOTION_COEXISTENCE
    if relation == "recovery":
        return RELATION_EFFORT_RESIDUE
    if relation == "boundary":
        return RELATION_VALUE_LINE_CROSSED
    return RELATION_EVENT_REACTION_LINK


def _evidence_source_field_ids(line: Any) -> list[str]:
    ids = []
    if _dedupe(getattr(line, "evidence_span_ids", None)):
        ids.append("sentence_plan_evidence_span_ids")
    if _dedupe(getattr(line, "phrase_unit_ids", None)):
        ids.append("sentence_plan_phrase_unit_ids")
    if _clean(getattr(line, "relation_type", "")):
        ids.append("sentence_plan_relation_type")
    if _line_roles(line):
        ids.append("sentence_plan_material_roles")
    return ids or ["sentence_plan_relation_type", "sentence_plan_material_roles"]


def _candidate_material(*, line: Any, family: str, section_id: str, relation_family: str) -> dict[str, Any]:
    source_field_ids = _evidence_source_field_ids(line)
    candidate_id = f"phase10_{family}_{relation_family}_{section_id}_001"
    return {
        "schema_version": STRUCTURE_INSIGHT_CANDIDATE_VERSION,
        "version": STRUCTURE_INSIGHT_CANDIDATE_VERSION,
        "source_phase": STRUCTURE_INSIGHT_SURFACE_PHASE10_STEP,
        "source_scope": "current_input_only",
        "structure_insight_candidate_ready": True,
        "phase7_structure_insight_candidate_ready": True,
        "material_quality": MATERIAL_QUALITY_ELIGIBLE,
        "relation_candidate_families": [relation_family],
        "candidates": [
            {
                "candidate_id": candidate_id,
                "relation_family": relation_family,
                "source_scope": "current_input_only",
                "candidate_quality": "phase10_limited_family_surface_candidate",
                "evidence": {
                    "source_field_ids": source_field_ids,
                    "evidence_slot_count": max(2, len(source_field_ids)),
                    "requires_external_knowledge": False,
                    "requires_user_history": False,
                    "raw_text_included": False,
                },
                "inference_strength": "soft",
                "surface_permission": {
                    "may_surface": True,
                    "must_use_soft_expression": True,
                    "must_not_surface_as_fact": True,
                    "must_not_surface_as_personality": True,
                    "must_not_surface_as_diagnosis": True,
                },
                "suggested_surface_role": "observation_insight_seed",
                "forbidden_claims": list(FORBIDDEN_CLAIMS_BASE),
                "must_not_surface_as": list(MUST_NOT_SURFACE_AS),
                "gate_required": list(GATE_REQUIRED_BASE),
                "public_response_key_added": False,
                "raw_input_included": False,
                "comment_text_generated": False,
            }
        ],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_generated": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
    }


def _observation_surface(*, family: str, relation_family: str) -> tuple[str, str, list[str]]:
    if family == FAMILY_SELF_UNDERSTANDING_FOLLOW:
        return (
            "自分を責める流れだけではなく、気持ちを少し優しく見ようとする方向も、同じ入力の中に残っているように見えます。",
            "self_understanding_observation_insight_seed",
            ["self_understanding_motion_seen", "identity_fact_claim_avoided"],
        )
    if family == FAMILY_LONG_MEANING_ARC:
        return (
            "長く残された材料が、ひとつの気分ではなく、いくつかの核が重なった状態のように見えます。",
            "long_meaning_arc_observation_insight_seed",
            ["multiple_core_seen", "single_emotion_collapse_avoided"],
        )
    if relation_family == RELATION_DESIRE_BLOCKAGE_CONFLICT:
        return (
            "動きたい向きと止まる重さが、同じ入力の中でぶつかっているように見えます。",
            "structure_question_desire_blockage_insight_seed",
            ["desire_blockage_relation_seen", "soft_observation_used"],
        )
    if relation_family == RELATION_MIXED_EMOTION_COEXISTENCE:
        return (
            "ひとつの感情に寄り切らず、違う向きの反応が同じ入力の中で重なっているように見えます。",
            "structure_question_mixed_emotion_insight_seed",
            ["mixed_emotion_relation_seen", "soft_observation_used"],
        )
    return (
        "出来事と反応が、ただ並んでいるだけではなく、同じ入力の中で関係を持って残っているように見えます。",
        "structure_question_event_reaction_insight_seed",
        ["event_reaction_relation_seen", "soft_observation_used"],
    )


def _reception_surface(*, family: str) -> tuple[str, str, list[str]]:
    if family == FAMILY_SELF_UNDERSTANDING_FOLLOW:
        return (
            "否定だけで終わらせずに見直そうとしている動きがあるように見えますし、その温度も一緒に受け取れます。",
            "self_understanding_reception_temperature_support",
            ["temperature_support", "conclusion_not_forced"],
        )
    if family == FAMILY_LONG_MEANING_ARC:
        return (
            "短く片づけないほうが自然な厚みのように見えますし、いくつかの核が残る重さごと受け取れます。",
            "long_meaning_arc_reception_temperature_support",
            ["temperature_support", "multiple_core_not_flattened"],
        )
    return (
        "断定せずに扱うほうが自然な関係のように見えますし、いま見えている重さごと受け取れます。",
        "structure_question_reception_temperature_support",
        ["temperature_support", "overclaim_avoided"],
    )


def _assert_surface_meta_only(meta: Mapping[str, Any]) -> None:
    for key in meta.keys():
        lowered = str(key).lower()
        if any(fragment in lowered for fragment in _BODY_KEY_FRAGMENTS):
            if lowered.endswith("_included") or lowered.endswith("_generated") or lowered.endswith("_added") or lowered.endswith("_blocked"):
                continue
            if lowered in {"structure_insight_surface_key", "structure_insight_surface_ending_key"}:
                continue
            raise ValueError(f"Phase10 surface meta contains body-like key: {key}")


def build_structure_insight_surface_for_line(
    line: Any,
    *,
    section_id: str,
    two_stage_meta: Mapping[str, Any] | None = None,
    proposed_surface_override: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return a gated visible sentence and text-free meta for one eligible line."""

    meta_source = _as_mapping(two_stage_meta)
    section = _section_from_inputs(section_id, meta_source)
    family = _connectable_family(line=line, section_id=section, two_stage_meta=meta_source)
    mode = _mode_from_meta(meta_source)
    coverage_group = _coverage_group_from_line(line, meta_source)
    if not family or section not in {SECTION_OBSERVATION, SECTION_RECEPTION}:
        return "", {}
    roles = _line_roles(line)
    relation_type = _clean(getattr(line, "relation_type", "")) or _clean(_line_meta(line).get("relation_type"))
    relation_family = _relation_family_for(family=family, relation_type=relation_type, roles=roles)
    if section == SECTION_OBSERVATION:
        surface, surface_key, feature_families = _observation_surface(family=family, relation_family=relation_family)
        surface_role = "observation_insight_seed"
        insight_seed_added = True
    else:
        surface, surface_key, feature_families = _reception_surface(family=family)
        surface_role = "reception_temperature_support"
        insight_seed_added = False
    proposed_surface = _clean(proposed_surface_override) or surface
    candidate_material = _candidate_material(
        line=line,
        family=family,
        section_id=section,
        relation_family=relation_family,
    )
    gate_report = build_structure_insight_gate_report(
        candidate_material,
        proposed_surface=proposed_surface,
    )
    assert_structure_insight_gate_meta_only(gate_report)
    gate_results = gate_report.get("candidate_gate_results") if isinstance(gate_report, Mapping) else []
    gate_result = gate_results[0] if isinstance(gate_results, list) and gate_results else {}
    gate_action = _clean(gate_report.get("action")) if isinstance(gate_report, Mapping) else ""
    gate_passed = bool(gate_report.get("passed")) if isinstance(gate_report, Mapping) else gate_action == GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE
    rejection_reasons = list(_as_mapping(gate_result).get("rejection_reasons") or gate_report.get("rejection_reasons") or [])
    phase10_meta = {
        "structure_insight_surface_schema_version": STRUCTURE_INSIGHT_SURFACE_VERSION,
        "structure_insight_surface_fields_version": STRUCTURE_INSIGHT_SURFACE_FIELDS_VERSION,
        "structure_insight_surface_source_phase": STRUCTURE_INSIGHT_SURFACE_PHASE10_STEP,
        "structure_insight_surface_source": STRUCTURE_INSIGHT_SURFACE_SOURCE,
        "phase10_structure_insight_surface_connected": gate_passed,
        "phase10_limited_family_connection": True,
        "structure_insight_surface_applied": gate_passed,
        "structure_insight_surface_limited_family_eligible": True,
        "structure_insight_surface_family": family,
        "structure_insight_surface_mode_id": mode,
        "structure_insight_surface_coverage_group": coverage_group,
        "structure_insight_surface_section_id": section,
        "structure_insight_surface_role": surface_role,
        "structure_insight_surface_key": surface_key,
        "structure_insight_surface_ending_key": surface_key,
        "structure_insight_surface_feature_families": list(feature_families),
        "structure_insight_surface_relation_family": relation_family,
        "structure_insight_surface_candidate_count": 1,
        "structure_insight_surface_gate_passed": gate_passed,
        "structure_insight_surface_gate_action": gate_action,
        "structure_insight_surface_gate_rejection_reasons": rejection_reasons,
        "structure_insight_surface_soft_expression_required": True,
        "structure_insight_surface_soft_expression_enforced": gate_passed,
        "structure_insight_surface_insight_seed_added": insight_seed_added and gate_passed,
        "structure_insight_surface_temperature_support_added": (not insight_seed_added) and gate_passed,
        "structure_insight_surface_public_response_key_added": False,
        "structure_insight_surface_comment_text_body_included": False,
        "structure_insight_surface_raw_input_included": False,
        "structure_insight_surface_candidate_body_included": False,
        "structure_insight_surface_overclaim_blocked": True,
        "structure_insight_surface_diagnosis_blocked": True,
        "structure_insight_surface_personality_claim_blocked": True,
        "structure_insight_surface_daily_unpleasant_deep_insight_suppressed": True,
        "structure_insight_surface_low_information_deep_insight_suppressed": True,
        "structure_insight_surface_mirror_only_reduction_supported": gate_passed,
        "structure_insight_surface_insight_delta_blind_qa_floor_candidate": "YELLOW" if gate_passed else "BLOCKED",
        "structure_insight_surface_gate_relaxed": False,
        "structure_insight_surface_surface_text_body_included": False,
    }
    _assert_surface_meta_only(phase10_meta)
    if not gate_passed:
        return "", phase10_meta
    return surface, phase10_meta


def normalize_structure_insight_surface_to_scorecard_fields(surface_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _as_mapping(surface_meta)
    return {
        "structure_insight_surface_fields_version": STRUCTURE_INSIGHT_SURFACE_FIELDS_VERSION,
        "phase10_structure_insight_surface_connected": bool(meta.get("applied") or meta.get("structure_insight_surface_applied")),
        "structure_insight_surface_applied": bool(meta.get("applied") or meta.get("structure_insight_surface_applied")),
        "structure_insight_surface_insight_seed_count": int(meta.get("observation_insight_seed_count") or meta.get("structure_insight_surface_insight_seed_count") or 0),
        "structure_insight_surface_insight_delta_blind_qa_floor_candidate": _clean(meta.get("insight_delta_blind_qa_floor_candidate") or meta.get("structure_insight_surface_insight_delta_blind_qa_floor_candidate")),
        "structure_insight_surface_overclaim_count": int(meta.get("overclaim_count") or 0),
        "structure_insight_surface_diagnosis_count": int(meta.get("diagnosis_count") or 0),
        "structure_insight_surface_personality_claim_count": int(meta.get("personality_claim_count") or 0),
        "structure_insight_surface_public_response_key_added": False,
        "structure_insight_surface_comment_text_body_included": False,
        "structure_insight_surface_raw_input_included": False,
        "structure_insight_surface_gate_relaxed": False,
    }
