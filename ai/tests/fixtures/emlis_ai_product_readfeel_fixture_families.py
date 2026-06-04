# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 3 fixture-family definitions for EmlisAI Product Read Feel.

These fixtures are not correct-answer public sentences.  They are a meta-only
family registry used by Product Read Feel QA to check family coverage, expected
internal modes, forbidden surface classes, section ratio policy, and v2 insight
opportunities.  The registry can project coverage events into the existing
scorecard path, but the events are explicitly forbidden from becoming runtime
branches, fixture-specific cues, or fixed reply templates.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Any, Final

from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_POSITIVE,
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_MIXED_EMOTION,
    FAMILY_POSITIVE_ONLY,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_SELF_DENIAL,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_UNCERTAINTY,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
)
from emlis_ai_product_readfeel_rubric import (
    DIMENSION_EVIDENCE_BOUNDARY,
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_INSIGHT_DELTA,
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_SOFT_INFERENCE_SURFACE,
    DIMENSION_STATE_STRUCTURE_RETENTION,
    DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS,
    PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS,
)

PRODUCT_READFEEL_FIXTURE_FAMILY_VERSION: Final = "cocolon.emlis.product_readfeel.fixture_family.v1"
PRODUCT_READFEEL_FIXTURE_FAMILY_REGISTRY_VERSION: Final = (
    "cocolon.emlis.product_readfeel.fixture_family_registry.v1"
)
PRODUCT_READFEEL_FIXTURE_FAMILY_COVERAGE_VERSION: Final = (
    "cocolon.emlis.product_readfeel.fixture_family_coverage.v1"
)
PRODUCT_READFEEL_FIXTURE_FAMILY_SCORECARD_EVENT_VERSION: Final = (
    "cocolon.emlis.product_readfeel.fixture_family_scorecard_event.v1"
)
PRODUCT_READFEEL_FIXTURE_FAMILY_SCORECARD_FIELDS_VERSION: Final = (
    "cocolon.emlis.product_readfeel.fixture_family_scorecard_fields.v1"
)
PRODUCT_READFEEL_FIXTURE_FAMILY_PHASE3_STEP: Final = "Phase3_Fixture_Family_Definition"
PRODUCT_READFEEL_FIXTURE_FAMILY_STEP: Final = PRODUCT_READFEEL_FIXTURE_FAMILY_PHASE3_STEP
PRODUCT_READFEEL_FIXTURE_FAMILY_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase3_FixtureFamily"

PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES: Final[tuple[str, ...]] = tuple(PRODUCT_READFEEL_REQUIRED_FAMILIES)

MODE_LOW_INFORMATION_OBSERVATION: Final = "low_information_observation"
MODE_DAILY_UNPLEASANT_RECEPTION: Final = "daily_unpleasant_reception"
MODE_DAILY_POSITIVE_RECEPTION: Final = "daily_positive_reception"
MODE_SELF_DENIAL_SUPPORT: Final = "self_denial_support"
MODE_UNCERTAINTY_SUPPORT: Final = "uncertainty_support"
MODE_STANDARD_STATE_ANSWER: Final = "standard_state_answer"
MODE_STRUCTURE_QUESTION_OBSERVATION: Final = "structure_question_observation"
MODE_LONG_MEANING_ARC: Final = "long_meaning_arc"
MODE_RELATIONSHIP_BOUNDARY_OBSERVATION: Final = "relationship_boundary_observation"
MODE_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
MODE_MIRROR_ONLY_FAILURE_DETECTION: Final = "input_self_report_only_failure_detection"

FORBIDDEN_SURFACE_CLASSES: Final[tuple[str, ...]] = (
    "diagnosis",
    "diagnostic_tone",
    "personality_claim",
    "cause_claim_without_evidence",
    "target_judgement_agreement",
    "other_person_intent_claim",
    "action_instruction",
    "generic_advice",
    "generic_comfort_template",
    "identity_claim_as_fact",
    "anger_target_attack_agreement",
    "category_as_cause",
    "fixed_template_surface",
    "malformed_nominalization",
    "internal_role_label",
    "relation_skeleton_surface",
    "raw_text_public_leak",
    "comment_text_public_leak",
    "case_specific_runtime_branch",
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
        "emotion_details",
        "comment_text",
        "commentText",
        "expected_comment_text",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "realized_text",
        "accepted_surface_probe",
        "blocked_surface_probe",
        "candidate_body",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "expected_comment_text_locked",
    "exact_comment_text_locked",
    "exact_comment_text_required",
    "case_specific_runtime_branch",
    "case_specific_runtime_condition_allowed",
    "runtime_branching_uses_fixture_strings",
    "fixture_text_used_for_runtime_branching",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "comment_text_generated",
    "comment_text_key_written",
    "comment_text_written_by_scorecard",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "public_status_extended",
    "observation_status_enum_extended",
    "response_shape_changed",
    "public_response_key_change",
    "public_response_key_added",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
    "external_ai_used",
    "local_llm_used",
)

_FAMILY_ALIASES: Final[dict[str, str]] = {
    "low_information": FAMILY_LOW_INFORMATION_SHORT,
    "low_information_short": FAMILY_LOW_INFORMATION_SHORT,
    "short_low_information": FAMILY_LOW_INFORMATION_SHORT,
    "low_info": FAMILY_LOW_INFORMATION_SHORT,
    "daily_unpleasant": FAMILY_DAILY_UNPLEASANT,
    "daily_unpleasant_reception": FAMILY_DAILY_UNPLEASANT,
    "daily_positive": FAMILY_DAILY_POSITIVE,
    "daily_positive_reception": FAMILY_DAILY_POSITIVE,
    "self_denial": FAMILY_SELF_DENIAL,
    "self_denial_support": FAMILY_SELF_DENIAL,
    "uncertainty": FAMILY_UNCERTAINTY,
    "uncertainty_support": FAMILY_UNCERTAINTY,
    "mixed_emotion": FAMILY_MIXED_EMOTION,
    "long_meaning_arc": FAMILY_LONG_MEANING_ARC,
    "relationship": FAMILY_RELATIONSHIP_BOUNDARY,
    "relationship_boundary": FAMILY_RELATIONSHIP_BOUNDARY,
    "structure_question": FAMILY_STRUCTURE_QUESTION,
    "structure_question_observation": FAMILY_STRUCTURE_QUESTION,
    "positive_only": FAMILY_POSITIVE_ONLY,
    "self_understanding": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "self_understanding_follow": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "input_self_report_only_failure": FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    "self_report_only_failure": FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
}


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _clean_key(value: Any) -> str:
    return _clean(value).lower().replace("-", "_")


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)


def normalize_product_readfeel_fixture_family(value: Any) -> str:
    text = _clean_key(value)
    return _FAMILY_ALIASES.get(text, text if text in PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES else "")


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def assert_product_readfeel_fixture_family_meta_only(
    payload: Mapping[str, Any] | None,
    *,
    source: str = "product_readfeel_fixture_family",
) -> None:
    data = dict(payload or {})
    if _contains_text_payload_key(data):
        raise ValueError(f"{source} must not include raw input or comment_text payload keys")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"{source} violates Phase3 fixture family boundary: {flag}=true")
    if data.get("examples_are_runtime_templates") is True:
        raise ValueError(f"{source} must not make examples runtime templates")


def _ratio_policy(
    *,
    ratio_family: str,
    observation_min_weight: int,
    observation_max_weight: int,
    reception_min_weight: int,
    reception_max_weight: int,
) -> dict[str, Any]:
    return {
        "ratio_policy_family": ratio_family,
        "observation_min_weight": observation_min_weight,
        "observation_max_weight": observation_max_weight,
        "reception_min_weight": reception_min_weight,
        "reception_max_weight": reception_max_weight,
        "fixed_ratio_forbidden": True,
        "observation_zero_allowed": False,
        "reception_zero_allowed": False,
        "measured_as_exact_character_ratio": False,
        "measured_by_section_role": True,
        "measured_by_sentence_plan_unit": True,
        "measured_by_follow_key_count": True,
    }


def _material_flags(
    *,
    low_information: bool = False,
    long_input: bool = False,
    structure_question_requested: bool = False,
    self_denial_present: bool = False,
    mixed_emotion_present: bool = False,
    relationship_target_present: bool = False,
    positive_only: bool = False,
    sufficient_material_for_insight: bool = True,
) -> dict[str, Any]:
    return {
        "memo_present": not low_information,
        "memo_action_present": not low_information,
        "selected_emotions_present": True,
        "emotion_details_present": not low_information,
        "category_present": True,
        "long_input": long_input,
        "structure_question_requested": structure_question_requested,
        "self_denial_present": self_denial_present,
        "mixed_emotion_present": mixed_emotion_present,
        "relationship_target_present": relationship_target_present,
        "positive_only": positive_only,
        "safety_path_required": False,
        "sufficient_material_for_insight": sufficient_material_for_insight,
        "raw_text_included": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
    }


@dataclass(frozen=True)
class ProductReadFeelFixtureFamily:
    family_id: str
    focus_summary: str
    v1_expectation: str
    v2_insight_summary: str
    expected_internal_modes: tuple[str, ...]
    expected_ratio_policy: Mapping[str, Any]
    input_material_flags: Mapping[str, Any]
    required_dimensions: tuple[str, ...] = PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS
    optional_v2_dimensions: tuple[str, ...] = PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS
    forbidden_surface_classes: tuple[str, ...] = FORBIDDEN_SURFACE_CLASSES
    v2_relation_candidates: tuple[str, ...] = ()
    v2_insight_opportunity: str = "optional_seed"
    expected_v1_verdict_floor: str = "YELLOW"
    expected_v2_backlog_if_missing: bool = True

    def as_registry_item(self) -> dict[str, Any]:
        item = {
            "version": PRODUCT_READFEEL_FIXTURE_FAMILY_VERSION,
            "schema_version": PRODUCT_READFEEL_FIXTURE_FAMILY_VERSION,
            "source": PRODUCT_READFEEL_FIXTURE_FAMILY_SOURCE,
            "source_step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
            "step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
            "fixture_family": self.family_id,
            "product_readfeel_family": self.family_id,
            "coverage_group": self.family_id,
            "focus_summary": self.focus_summary,
            "v1_expectation": self.v1_expectation,
            "v2_insight_summary": self.v2_insight_summary,
            "expected_internal_modes": list(self.expected_internal_modes),
            "expected_ratio_policy": dict(self.expected_ratio_policy),
            "input_material_flags": dict(self.input_material_flags),
            "required_dimensions": list(self.required_dimensions),
            "optional_v2_dimensions": list(self.optional_v2_dimensions),
            "forbidden_surface_classes": list(self.forbidden_surface_classes),
            "hard_fail_conditions": list(self.forbidden_surface_classes),
            "v2_relation_candidates": list(self.v2_relation_candidates),
            "v2_insight_opportunity": self.v2_insight_opportunity,
            "expected_v1_verdict_floor": self.expected_v1_verdict_floor,
            "expected_v2_backlog_if_missing": self.expected_v2_backlog_if_missing,
            "exact_comment_text_required": False,
            "exact_comment_text_locked": False,
            "examples_are_not_runtime_templates": True,
            "case_specific_runtime_condition_allowed": False,
            "case_specific_runtime_branch": False,
            "runtime_branching_uses_fixture_strings": False,
            "fixture_text_used_for_runtime_branching": False,
            "use_as_runtime_branch_condition": False,
            "scorecard_event_projection_available": True,
            "raw_input_included": False,
            "raw_text_included": False,
            "input_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "comment_text_written_by_scorecard": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "template_gate_relaxed": False,
            "gate_relaxed": False,
            "product_gate_ready": False,
            "product_gate_reached": False,
            "product_gate_public_release_applied": False,
            "public_release_applied": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_product_readfeel_fixture_family_meta_only(item, source=f"fixture_family:{self.family_id}")
        return item


PRODUCT_READFEEL_FIXTURE_FAMILIES: Final[tuple[ProductReadFeelFixtureFamily, ...]] = (
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_LOW_INFORMATION_SHORT,
        focus_summary="very short low-information fatigue or refusal markers",
        v1_expectation="observe only the visible scope and invite details lightly without forcing input",
        v2_insight_summary="treat only an unspecified weight before details become clear",
        expected_internal_modes=(MODE_LOW_INFORMATION_OBSERVATION,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="light_observation_with_prompt",
            observation_min_weight=1,
            observation_max_weight=2,
            reception_min_weight=8,
            reception_max_weight=9,
        ),
        input_material_flags=_material_flags(low_information=True, sufficient_material_for_insight=False),
        v2_relation_candidates=("low_information_unspecified_weight",),
        v2_insight_opportunity="do_not_force_deep_insight",
        expected_v2_backlog_if_missing=False,
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_DAILY_UNPLEASANT,
        focus_summary="ordinary unpleasant event, fear, anger, or discomfort",
        v1_expectation="keep observation small, preserve event and reaction, and deepen human follow",
        v2_insight_summary="surface only a soft user-side line or residue when evidence exists",
        expected_internal_modes=(MODE_DAILY_UNPLEASANT_RECEPTION,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="daily_unpleasant_reception",
            observation_min_weight=1,
            observation_max_weight=2,
            reception_min_weight=8,
            reception_max_weight=9,
        ),
        input_material_flags=_material_flags(relationship_target_present=True),
        v2_relation_candidates=("value_line_crossed", "event_reaction_link"),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_DAILY_POSITIVE,
        focus_summary="joy, relief, or a small positive change after a daily event",
        v1_expectation="observe the material and naturally share the positive temperature",
        v2_insight_summary="keep the structure of change, recovery, relief, or surprise light",
        expected_internal_modes=(MODE_DAILY_POSITIVE_RECEPTION,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="daily_positive_reception",
            observation_min_weight=2,
            observation_max_weight=2,
            reception_min_weight=8,
            reception_max_weight=8,
        ),
        input_material_flags=_material_flags(positive_only=True),
        v2_relation_candidates=("positive_change_recovery",),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_SELF_DENIAL,
        focus_summary="self-denial wording with a felt state that must not become identity fact",
        v1_expectation="receive the felt state while separating it from identity claim",
        v2_insight_summary="show the contradiction between self-denial words and remaining effort",
        expected_internal_modes=(MODE_SELF_DENIAL_SUPPORT,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="self_denial_support",
            observation_min_weight=3,
            observation_max_weight=4,
            reception_min_weight=6,
            reception_max_weight=7,
        ),
        input_material_flags=_material_flags(self_denial_present=True),
        v2_relation_candidates=("self_denial_identity_split",),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_UNCERTAINTY,
        focus_summary="uncertainty, worry, or question about whether the current way is okay",
        v1_expectation="receive both anxiety and effort without collapsing either side",
        v2_insight_summary="show relation between wish, fear, and trial when supported",
        expected_internal_modes=(MODE_UNCERTAINTY_SUPPORT,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="uncertainty_support",
            observation_min_weight=3,
            observation_max_weight=4,
            reception_min_weight=6,
            reception_max_weight=7,
        ),
        input_material_flags=_material_flags(),
        v2_relation_candidates=("uncertainty_effort_pair", "desire_blockage_conflict"),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_MIXED_EMOTION,
        focus_summary="coexisting positive and fearful or blocked reactions",
        v1_expectation="do not flatten the state into a single emotion",
        v2_insight_summary="show why both sides can appear at the same time",
        expected_internal_modes=(MODE_STANDARD_STATE_ANSWER, "mixed_emotion_observation"),
        expected_ratio_policy=_ratio_policy(
            ratio_family="mixed_emotion_balance",
            observation_min_weight=5,
            observation_max_weight=6,
            reception_min_weight=4,
            reception_max_weight=5,
        ),
        input_material_flags=_material_flags(mixed_emotion_present=True),
        v2_relation_candidates=("mixed_emotion_coexistence",),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_LONG_MEANING_ARC,
        focus_summary="long input with multiple cores across event, emotion, wish, blockage, or realization",
        v1_expectation="do not crush long material into one mood; rearrange it as state structure",
        v2_insight_summary="show relations among multiple cores such as wish and blockage or effort and fatigue",
        expected_internal_modes=(MODE_STANDARD_STATE_ANSWER, MODE_LONG_MEANING_ARC),
        expected_ratio_policy=_ratio_policy(
            ratio_family="long_arc_variable",
            observation_min_weight=5,
            observation_max_weight=7,
            reception_min_weight=3,
            reception_max_weight=5,
        ),
        input_material_flags=_material_flags(long_input=True),
        v2_relation_candidates=("long_arc_multiple_core", "desire_blockage_conflict"),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_RELATIONSHIP_BOUNDARY,
        focus_summary="another person is involved, but the reply must stay on the user-side boundary",
        v1_expectation="do not agree with target judgement or infer the other person intent",
        v2_insight_summary="show user-side boundary, expectation, hurt, or distance without overclaim",
        expected_internal_modes=(MODE_STANDARD_STATE_ANSWER, MODE_RELATIONSHIP_BOUNDARY_OBSERVATION),
        expected_ratio_policy=_ratio_policy(
            ratio_family="relationship_boundary_soft",
            observation_min_weight=4,
            observation_max_weight=6,
            reception_min_weight=4,
            reception_max_weight=6,
        ),
        input_material_flags=_material_flags(relationship_target_present=True),
        v2_relation_candidates=("value_line_crossed", "relationship_boundary_user_side"),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_STRUCTURE_QUESTION,
        focus_summary="explicit request to understand why or what kind of state is present",
        v1_expectation="make observation thicker and do not escape into comfort only",
        v2_insight_summary="return a safe structural insight candidate itself",
        expected_internal_modes=(MODE_STRUCTURE_QUESTION_OBSERVATION,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="structure_question_observation",
            observation_min_weight=6,
            observation_max_weight=7,
            reception_min_weight=3,
            reception_max_weight=4,
        ),
        input_material_flags=_material_flags(structure_question_requested=True),
        v2_relation_candidates=("structure_question_direct_insight", "event_reaction_link"),
        v2_insight_opportunity="initial_structure_insight_connection_candidate",
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_POSITIVE_ONLY,
        focus_summary="bright input that should not be pulled into unnecessary heaviness",
        v1_expectation="keep joy and relief warm without over-analysis",
        v2_insight_summary="show the structure of joy without cooling it down",
        expected_internal_modes=(MODE_DAILY_POSITIVE_RECEPTION,),
        expected_ratio_policy=_ratio_policy(
            ratio_family="positive_only_light",
            observation_min_weight=2,
            observation_max_weight=3,
            reception_min_weight=7,
            reception_max_weight=8,
        ),
        input_material_flags=_material_flags(positive_only=True),
        v2_relation_candidates=("positive_change_recovery",),
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_SELF_UNDERSTANDING_FOLLOW,
        focus_summary="the user is trying to look at themself rather than only report an event",
        v1_expectation="receive the movement of facing oneself",
        v2_insight_summary="surface the entrance of self-understanding softly",
        expected_internal_modes=(MODE_STANDARD_STATE_ANSWER, MODE_SELF_UNDERSTANDING_FOLLOW),
        expected_ratio_policy=_ratio_policy(
            ratio_family="self_understanding_follow",
            observation_min_weight=5,
            observation_max_weight=6,
            reception_min_weight=4,
            reception_max_weight=5,
        ),
        input_material_flags=_material_flags(),
        v2_relation_candidates=("self_understanding_entry", "effort_residue"),
        v2_insight_opportunity="initial_structure_insight_connection_candidate",
    ),
    ProductReadFeelFixtureFamily(
        family_id=FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        focus_summary="case that only repeats self-report material and exposes insight_delta gap",
        v1_expectation="classify as YELLOW or REPAIR_REQUIRED instead of treating repetition as product pass",
        v2_insight_summary="detect missing relation insight when enough material exists",
        expected_internal_modes=(MODE_STANDARD_STATE_ANSWER, MODE_MIRROR_ONLY_FAILURE_DETECTION),
        expected_ratio_policy=_ratio_policy(
            ratio_family="mirror_only_failure_detection",
            observation_min_weight=5,
            observation_max_weight=7,
            reception_min_weight=3,
            reception_max_weight=5,
        ),
        input_material_flags=_material_flags(long_input=True, structure_question_requested=True),
        v2_relation_candidates=("input_material_relation_missing", "insight_delta_missing"),
        v2_insight_opportunity="required_gap_detection",
        expected_v1_verdict_floor="REPAIR_REQUIRED",
        expected_v2_backlog_if_missing=True,
    ),
)

assert tuple(f.family_id for f in PRODUCT_READFEEL_FIXTURE_FAMILIES) == PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES


def iter_product_readfeel_fixture_families(
    *,
    families: Sequence[str] | Iterable[str] | None = None,
) -> tuple[ProductReadFeelFixtureFamily, ...]:
    allowed = {normalize_product_readfeel_fixture_family(family) for family in _listify(families)} if families else None
    return tuple(
        fixture
        for fixture in PRODUCT_READFEEL_FIXTURE_FAMILIES
        if not allowed or fixture.family_id in allowed
    )


def product_readfeel_fixture_family_by_id(family: str) -> ProductReadFeelFixtureFamily:
    normalized = normalize_product_readfeel_fixture_family(family)
    for fixture in PRODUCT_READFEEL_FIXTURE_FAMILIES:
        if fixture.family_id == normalized:
            return fixture
    raise KeyError(f"unknown product readfeel fixture family: {family}")


def build_product_readfeel_fixture_family_definitions() -> list[dict[str, Any]]:
    definitions = [fixture.as_registry_item() for fixture in PRODUCT_READFEEL_FIXTURE_FAMILIES]
    for item in definitions:
        assert_product_readfeel_fixture_family_meta_only(item, source="product_readfeel_fixture_family_definition")
    return definitions


def build_product_readfeel_fixture_family_registry() -> dict[str, Any]:
    families = build_product_readfeel_fixture_family_definitions()
    covered_families = _dedupe(item.get("product_readfeel_family") for item in families)
    missing_families = [family for family in PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES if family not in covered_families]
    registry = {
        "version": PRODUCT_READFEEL_FIXTURE_FAMILY_REGISTRY_VERSION,
        "schema_version": PRODUCT_READFEEL_FIXTURE_FAMILY_REGISTRY_VERSION,
        "source": PRODUCT_READFEEL_FIXTURE_FAMILY_SOURCE,
        "source_step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "registry_type": "product_readfeel_fixture_family_meta_only",
        "phase3_fixture_family_definition_ready": not missing_families,
        "product_readfeel_phase3_ready": not missing_families,
        "required_families": list(PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES),
        "covered_families": covered_families,
        "missing_families": missing_families,
        "fixture_family_count": len(families),
        "families": families,
        "required_dimensions": list(PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS),
        "optional_v2_dimensions": list(PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS),
        "exact_comment_text_required": False,
        "exact_comment_text_locked": False,
        "case_specific_runtime_condition_allowed": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "examples_are_not_runtime_templates": True,
        "scorecard_event_projection_available": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_product_readfeel_fixture_family_meta_only(registry, source="product_readfeel_fixture_family_registry")
    return registry


def build_product_readfeel_fixture_family_scorecard_event(
    family: str | ProductReadFeelFixtureFamily,
    *,
    event_id: str = "",
    display_confirmed: bool = True,
) -> dict[str, Any]:
    fixture = family if isinstance(family, ProductReadFeelFixtureFamily) else product_readfeel_fixture_family_by_id(family)
    registry_item = fixture.as_registry_item()
    is_mirror_failure = fixture.family_id == FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE
    ratings = {
        DIMENSION_READ_FEELING: "yellow" if is_mirror_failure else "green",
        DIMENSION_SELF_REPORT_RETENTION: "green",
        DIMENSION_STATE_STRUCTURE_RETENTION: "yellow" if is_mirror_failure else "green",
        DIMENSION_EMOTION_TEMPERATURE_RETENTION: "green",
        DIMENSION_FOLLOW_DEPTH: "yellow" if is_mirror_failure else "green",
        DIMENSION_EVIDENCE_BOUNDARY: "green",
        DIMENSION_SOFT_INFERENCE_SURFACE: "green",
        DIMENSION_NATURALNESS: "green",
        DIMENSION_NON_TEMPLATE: "green",
        DIMENSION_INSIGHT_DELTA: "red" if is_mirror_failure else "green",
        DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY: "yellow" if is_mirror_failure else "green",
    }
    reason_codes = ["mirror_only", "insight_delta_missing"] if is_mirror_failure else []
    event = {
        "version": PRODUCT_READFEEL_FIXTURE_FAMILY_SCORECARD_EVENT_VERSION,
        "schema_version": PRODUCT_READFEEL_FIXTURE_FAMILY_SCORECARD_EVENT_VERSION,
        "source": PRODUCT_READFEEL_FIXTURE_FAMILY_SOURCE,
        "source_step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "fixture_id": event_id or f"phase3_product_readfeel_family_{fixture.family_id}",
        "row_id": event_id or f"phase3_product_readfeel_family_{fixture.family_id}",
        "fixture_family": fixture.family_id,
        "product_readfeel_family": fixture.family_id,
        "coverage_group": fixture.family_id,
        "expected_internal_modes": list(fixture.expected_internal_modes),
        "expected_ratio_policy": dict(fixture.expected_ratio_policy),
        "input_material_flags": dict(fixture.input_material_flags),
        "required_dimensions": list(fixture.required_dimensions),
        "optional_v2_dimensions": list(fixture.optional_v2_dimensions),
        "v2_relation_candidates": list(fixture.v2_relation_candidates),
        "v2_insight_opportunity": fixture.v2_insight_opportunity,
        "ratings": ratings,
        "reason_codes": reason_codes,
        "mirror_only_detected": is_mirror_failure,
        "self_report_only_detected": is_mirror_failure,
        "material_slot_count": 1 if fixture.family_id == FAMILY_LOW_INFORMATION_SHORT else 5,
        "evidence_slot_count": 1 if fixture.family_id == FAMILY_LOW_INFORMATION_SHORT else 5,
        "source_field_ids": [] if fixture.family_id == FAMILY_LOW_INFORMATION_SHORT else ["memo", "memo_action", "selected_emotions"],
        "observation_status": "passed" if display_confirmed else "unavailable",
        "display_confirmed": bool(display_confirmed),
        "comment_text_present": bool(display_confirmed),
        "public_passed": bool(display_confirmed),
        "eligible_count": 1,
        "passed_display_count": 1 if display_confirmed else 0,
        "binding_supported_sentence_count": 2 if display_confirmed else 0,
        "expected_binding_count": 2,
        "surface_signature_family_key": f"phase3:{fixture.family_id}",
        "fixture_registry_item_present": True,
        "exact_comment_text_required": False,
        "exact_comment_text_locked": False,
        "case_specific_runtime_condition_allowed": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "examples_are_not_runtime_templates": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    # Keep the registry item local to construction only.  The scorecard event is
    # intentionally a compact projection, not a copy of the whole definition.
    assert registry_item["product_readfeel_family"] == event["product_readfeel_family"]
    assert_product_readfeel_fixture_family_meta_only(event, source=f"fixture_family_scorecard_event:{fixture.family_id}")
    return event


def build_product_readfeel_fixture_family_scorecard_events(
    *,
    families: Sequence[str] | Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    events = [build_product_readfeel_fixture_family_scorecard_event(fixture) for fixture in iter_product_readfeel_fixture_families(families=families)]
    for event in events:
        assert_product_readfeel_fixture_family_meta_only(event, source="product_readfeel_fixture_family_scorecard_event")
    return events


def build_product_readfeel_fixture_family_coverage(
    scorecard_events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    raw_events = list(scorecard_events or build_product_readfeel_fixture_family_scorecard_events())
    observed_families = _dedupe(
        normalize_product_readfeel_fixture_family(
            (event or {}).get("product_readfeel_family")
            or (event or {}).get("fixture_family")
            or (event or {}).get("coverage_group")
        )
        for event in raw_events
        if isinstance(event, Mapping)
    )
    observed_families = [family for family in observed_families if family]
    missing_families = [family for family in PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES if family not in observed_families]
    unsupported_families = [family for family in observed_families if family not in PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES]
    coverage = {
        "version": PRODUCT_READFEEL_FIXTURE_FAMILY_COVERAGE_VERSION,
        "schema_version": PRODUCT_READFEEL_FIXTURE_FAMILY_COVERAGE_VERSION,
        "source": PRODUCT_READFEEL_FIXTURE_FAMILY_SOURCE,
        "source_step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "step": PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "phase3_fixture_family_coverage_ready": bool(raw_events and not missing_families and not unsupported_families),
        "product_readfeel_phase3_ready": bool(raw_events and not missing_families and not unsupported_families),
        "required_families": list(PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES),
        "observed_families": observed_families,
        "covered_families": observed_families,
        "missing_families": missing_families,
        "unsupported_families": unsupported_families,
        "scorecard_event_count": len(raw_events),
        "required_family_count": len(PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES),
        "observed_required_family_count": len([family for family in observed_families if family in PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES]),
        "fixture_family_coverage_rate": _rate(
            len([family for family in PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES if family in observed_families]),
            len(PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES),
        ),
        "scorecard_event_projection_available": True,
        "exact_comment_text_required": False,
        "case_specific_runtime_condition_allowed": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_product_readfeel_fixture_family_meta_only(coverage, source="product_readfeel_fixture_family_coverage")
    return coverage


def normalize_product_readfeel_fixture_family_coverage_to_scorecard_fields(
    coverage: Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = dict(coverage or build_product_readfeel_fixture_family_coverage())
    assert_product_readfeel_fixture_family_meta_only(data, source="product_readfeel_fixture_family_scorecard_fields_source")
    fields = {
        "product_readfeel_fixture_family_coverage_version": _clean(data.get("version"))
        or PRODUCT_READFEEL_FIXTURE_FAMILY_COVERAGE_VERSION,
        "product_readfeel_fixture_family_coverage_step": _clean(data.get("step"))
        or PRODUCT_READFEEL_FIXTURE_FAMILY_STEP,
        "phase3_fixture_family_coverage_ready": bool(data.get("phase3_fixture_family_coverage_ready")),
        "product_readfeel_phase3_ready": bool(data.get("product_readfeel_phase3_ready")),
        "product_readfeel_required_fixture_families": list(data.get("required_families") or []),
        "product_readfeel_observed_fixture_families": list(data.get("observed_families") or []),
        "product_readfeel_missing_fixture_families": list(data.get("missing_families") or []),
        "product_readfeel_fixture_family_coverage_rate": data.get("fixture_family_coverage_rate", 0.0),
        "product_readfeel_fixture_family_scorecard_event_count": data.get("scorecard_event_count", 0),
        "scorecard_event_projection_available": True,
        "exact_comment_text_required": False,
        "case_specific_runtime_condition_allowed": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_fixture_family_meta_only(fields, source="product_readfeel_fixture_family_scorecard_fields")
    return fields


def dump_product_readfeel_fixture_family_registry(payload: Mapping[str, Any] | None = None) -> str:
    data = dict(payload or build_product_readfeel_fixture_family_registry())
    assert_product_readfeel_fixture_family_meta_only(data, source="product_readfeel_fixture_family_registry_dump")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_FIXTURE_FAMILY_VERSION",
    "PRODUCT_READFEEL_FIXTURE_FAMILY_REGISTRY_VERSION",
    "PRODUCT_READFEEL_FIXTURE_FAMILY_COVERAGE_VERSION",
    "PRODUCT_READFEEL_FIXTURE_FAMILY_SCORECARD_EVENT_VERSION",
    "PRODUCT_READFEEL_FIXTURE_FAMILY_SCORECARD_FIELDS_VERSION",
    "PRODUCT_READFEEL_FIXTURE_FAMILY_PHASE3_STEP",
    "PRODUCT_READFEEL_FIXTURE_FAMILY_STEP",
    "PRODUCT_READFEEL_PHASE3_REQUIRED_FAMILIES",
    "FORBIDDEN_SURFACE_CLASSES",
    "ProductReadFeelFixtureFamily",
    "assert_product_readfeel_fixture_family_meta_only",
    "normalize_product_readfeel_fixture_family",
    "iter_product_readfeel_fixture_families",
    "product_readfeel_fixture_family_by_id",
    "build_product_readfeel_fixture_family_definitions",
    "build_product_readfeel_fixture_family_registry",
    "build_product_readfeel_fixture_family_scorecard_event",
    "build_product_readfeel_fixture_family_scorecard_events",
    "build_product_readfeel_fixture_family_coverage",
    "normalize_product_readfeel_fixture_family_coverage_to_scorecard_fields",
    "dump_product_readfeel_fixture_family_registry",
]
