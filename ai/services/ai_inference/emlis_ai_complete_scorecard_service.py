# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 12 scorecard / fixture expansion for EmlisAI Complete Composer.

This module aggregates the Step 11 Complete Composer scorecard event into a
coverage-group scorecard and exposes a sanitized fixture suite for internal QA.
It is intentionally meta-only: it does not write ``comment_text``, does not
change observation status, and does not alter DB/API/RN/public response shape.

The fixture suite stores coverage structure, target relations, and QA rubric
keys only.  It does not store raw user input or example texts, so improvements
can be made from diagnostics, binding, coverage, and Gate reasons.
"""

from dataclasses import dataclass, field as dataclass_field
from typing import Any, Iterable, Mapping, Sequence

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_reply_diagnostics_service import COMPLETE_SCORECARD_EVENT_VERSION
from emlis_ai_complete_tone_policy import (
    COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_STAGE,
    COMPLETE_TONE_ENGINE_VERSION,
)

COMPLETE_SCORECARD_SERVICE_VERSION = "emlis.complete_scorecard_service.v1"
COMPLETE_SCORECARD_FIXTURE_SUITE_VERSION = "emlis.complete_scorecard_fixture_suite.v1"
COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION = "emlis.complete_product_quality_coverage_suite.v1"
COMPLETE_SCORECARD_NORMALIZED_EVENT_VERSION = "emlis.complete_scorecard_normalized_event.v1"
COMPLETE_SCORECARD_EVENT_NORMALIZED_VERSION = COMPLETE_SCORECARD_NORMALIZED_EVENT_VERSION
COMPLETE_BLIND_QA_RUBRIC_VERSION = "emlis.complete_blind_qa_rubric.v1"
COMPLETE_SCORECARD_AGGREGATE_VERSION = "emlis.complete_scorecard_aggregate.v1"
COMPLETE_SCORECARD_HARNESS_VERSION = "emlis.complete_scorecard_harness.v1"
COMPLETE_SCORECARD_STEP = "Step12_Scorecard_fixture_extension"
COMPLETE_SCORECARD_STAGE = COMPLETE_SCORECARD_STEP
COMPLETE_SCORECARD_IMPLEMENTATION_UNIT = "Commit 12"

COMPLETE_INITIAL_DISPLAY_TARGET_MIN = 0.65
COMPLETE_INITIAL_DISPLAY_TARGET_MAX = 0.75
COMPLETE_PRODUCT_GATE_DISPLAY_TARGET = 0.90
COMPLETE_BINDING_TARGET_RATE = 0.98
COMPLETE_READ_FEELING_INITIAL_TARGET = 0.80
COMPLETE_READ_FEELING_PRODUCT_TARGET = 0.90
COMPLETE_SCORECARD_COVERAGE_GROUP_MISSING = "coverage_group_missing"

COMPLETE_COVERAGE_GROUP_ORDER: Sequence[str] = (
    "short_daily",
    "long_meaning_arc",
    "conflict",
    "recovery",
    "pressure",
    "desire_fear",
    "relationship",
)
COMPLETE_SCORECARD_COVERAGE_GROUPS = COMPLETE_COVERAGE_GROUP_ORDER
COMPLETE_SCORECARD_REQUIRED_COVERAGE_GROUPS = COMPLETE_COVERAGE_GROUP_ORDER
COMPLETE_FIXTURE_SUITE_VERSION = COMPLETE_SCORECARD_FIXTURE_SUITE_VERSION

_TEMPLATE_REASON_MARKERS = ("template", "fixed", "raw_echo", "over_echo", "same_ending", "surface_signature_repeat", "surface_connector_repetition", "signature_repeat", "emotion_label_only")
_SAFETY_REASON_MARKERS = ("safety", "diagnosis", "overclaim", "personality", "advice", "action_instruction", "medical", "unsafe")

_COVERAGE_GROUP_ALIASES = {
    "positive_recovery": "recovery",
    "energy_fatigue": "short_daily",
    "anxiety": "short_daily",
    "anger_hurt": "conflict",
    "limit_escape": "pressure",
    "value_wish": "short_daily",
    "wish_fear": "desire_fear",
    "desire_and_fear": "desire_fear",
    "desire-fear": "desire_fear",
    "approach_avoidance": "desire_fear",
    "scope_contract": "short_daily",
    "composer_material": "short_daily",
    "gate_quality": "short_daily",
    "safety_boundary": "pressure",
    "connection_rollout": "short_daily",
    "unclassified": "short_daily",
    "history_cross_core": "long_meaning_arc",
}

_RELATION_TO_COVERAGE_GROUP = {
    "recovery": "recovery",
    "pressure": "pressure",
    "contrast": "conflict",
    "coexistence": "conflict",
    "approach_avoidance": "desire_fear",
    "residue": "short_daily",
    "history_cross_core": "long_meaning_arc",
}

_COVERAGE_TAXONOMY: Mapping[str, Mapping[str, Any]] = {
    "short_daily": {
        "eligible_conditions": ("short_daily_emotion_or_residue", "no_overinterpretation"),
        "ng_conditions": ("diagnosis", "generic_comfort_only"),
        "expected_relations": ("residue", "coexistence"),
        "primary_gate_reasons": ("overclaim", "generic_comfort"),
    },
    "long_meaning_arc": {
        "eligible_conditions": ("multi_sentence_meaning_arc", "recurring_core_or_residue"),
        "ng_conditions": ("full_summary_only", "focus_drift"),
        "expected_relations": ("coexistence", "residue"),
        "primary_gate_reasons": ("too_long", "focus_drift"),
    },
    "conflict": {
        "eligible_conditions": ("two_or_more_inner_positions", "relation_traceable"),
        "ng_conditions": ("one_side_declared_true_self",),
        "expected_relations": ("contrast", "coexistence"),
        "primary_gate_reasons": ("relation_not_expressed",),
    },
    "recovery": {
        "eligible_conditions": ("recovery_signal", "prior_load_kept"),
        "ng_conditions": ("over_comfort", "already_ok_claim"),
        "expected_relations": ("recovery", "coexistence"),
        "primary_gate_reasons": ("over_comfort", "missing_prior_load"),
    },
    "pressure": {
        "eligible_conditions": ("internal_or_external_pressure", "no_causal_personality_claim"),
        "ng_conditions": ("diagnostic_tone", "cause_overclaim"),
        "expected_relations": ("pressure",),
        "primary_gate_reasons": ("diagnostic_tone", "cause_overclaim"),
    },
    "desire_fear": {
        "eligible_conditions": ("desire_and_fear_coexist", "approach_avoidance_relation"),
        "ng_conditions": ("advice_like", "action_instruction"),
        "expected_relations": ("approach_avoidance", "coexistence"),
        "primary_gate_reasons": ("advice_like", "relation_missing"),
    },
    "relationship": {
        "eligible_conditions": ("relationship_tension_on_user_side", "no_other_person_diagnosis"),
        "ng_conditions": ("personality_claim", "blame_overclaim"),
        "expected_relations": ("coexistence", "pressure"),
        "primary_gate_reasons": ("personality_claim", "blame_overclaim"),
    },
}

_TEXT_PAYLOAD_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
    "material_text",
    "surface_text",
    "realized_text",
    "comment_text",
    "text",
    "phrase",
    "sentence",
    "sentences",
    "line_text",
    "body",
    "reply_text",
    "summary_of_output",
}


@dataclass(frozen=True)
class CompleteScorecardFixtureCase:
    """Sanitized fixture definition for Complete Composer QA.

    ``scenario_key`` is a structural label, not a user input example.  No raw
    input text is stored in the fixture metadata.
    """

    fixture_id: str
    coverage_group: str
    scenario_key: str
    fixture_kind: str = "eligible_normal_input"
    target_relations: Iterable[str] = dataclass_field(default_factory=tuple)
    eligible_conditions: Iterable[str] = dataclass_field(default_factory=tuple)
    ng_conditions: Iterable[str] = dataclass_field(default_factory=tuple)
    expected_primary_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    expected_min_sentences: int = 2
    expected_max_sentences: int = 4
    binding_required: bool = True
    blind_qa_dimensions: Iterable[str] = dataclass_field(default_factory=lambda: (
        "input_specific_structure_reflected",
        "read_feeling",
        "no_diagnosis_or_personality_claim",
        "no_template_or_raw_echo",
    ))

    def as_meta(self) -> dict[str, Any]:
        taxonomy = _COVERAGE_TAXONOMY.get(self.coverage_group, {})
        return {
            "coverage_suite_version": COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION,
            "fixture_id": self.fixture_id,
            "coverage_group": self.coverage_group,
            "scenario_key": self.scenario_key,
            "fixture_kind": self.fixture_kind,
            "target_relations": _dedupe(self.target_relations),
            "eligible_conditions": _dedupe(self.eligible_conditions or taxonomy.get("eligible_conditions")),
            "ng_conditions": _dedupe(self.ng_conditions or taxonomy.get("ng_conditions")),
            "expected_primary_reasons": _dedupe(self.expected_primary_reasons or taxonomy.get("primary_gate_reasons")),
            "expected_min_sentences": int(self.expected_min_sentences),
            "expected_max_sentences": int(self.expected_max_sentences),
            "binding_required": bool(self.binding_required),
            "blind_qa_dimensions": _dedupe(self.blind_qa_dimensions),
            "raw_input_included": False,
            "raw_text_included": False,
        }


_DEFAULT_FIXTURE_CASES: Sequence[CompleteScorecardFixtureCase] = (
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_short_daily_01",
        coverage_group="short_daily",
        scenario_key="daily_small_residue",
        target_relations=("residue",),
        expected_min_sentences=2,
        expected_max_sentences=3,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_short_daily_02",
        coverage_group="short_daily",
        scenario_key="daily_small_wish_and_anxiety",
        target_relations=("coexistence", "residue"),
        expected_min_sentences=2,
        expected_max_sentences=3,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_long_meaning_arc_01",
        coverage_group="long_meaning_arc",
        scenario_key="multi_sentence_meaning_arc",
        target_relations=("coexistence", "residue"),
        expected_min_sentences=3,
        expected_max_sentences=5,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_conflict_01",
        coverage_group="conflict",
        scenario_key="two_positions_coexist_without_true_self_claim",
        target_relations=("contrast", "coexistence"),
        expected_min_sentences=2,
        expected_max_sentences=4,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_recovery_01",
        coverage_group="recovery",
        scenario_key="load_then_recovery_signal",
        target_relations=("recovery",),
        expected_min_sentences=2,
        expected_max_sentences=4,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_pressure_01",
        coverage_group="pressure",
        scenario_key="pressure_without_diagnosis",
        target_relations=("pressure",),
        expected_min_sentences=2,
        expected_max_sentences=4,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_desire_fear_01",
        coverage_group="desire_fear",
        scenario_key="approach_avoidance_desire_and_fear",
        target_relations=("approach_avoidance", "coexistence"),
        expected_min_sentences=2,
        expected_max_sentences=4,
    ),
    CompleteScorecardFixtureCase(
        fixture_id="complete_fixture_relationship_01",
        coverage_group="relationship",
        scenario_key="relationship_tension_kept_on_self_side",
        target_relations=("coexistence", "pressure"),
        expected_min_sentences=2,
        expected_max_sentences=4,
    ),
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _rate(numerator: int, denominator: int) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        source: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        source = values
    else:
        source = [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in source:
        item = _clean(value)
        if item and item not in seen:
            out.append(item)
            seen.add(item)
    return out


def _safe_json(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return None
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _clean(key)
            if not key_text or key_text in _TEXT_PAYLOAD_KEYS:
                continue
            safe_item = _safe_json(item, depth=depth + 1)
            if safe_item is not None:
                out[key_text] = safe_item
        return out
    if isinstance(value, (list, tuple, set)):
        return [item for item in (_safe_json(v, depth=depth + 1) for v in value) if item is not None]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    return {}


def _source_event(record: Any) -> dict[str, Any]:
    item = _mapping(record)
    for key in (
        "scorecard_event",
        "complete_scorecard_event",
        "complete_composer_scorecard_event",
        "complete_composer_initial_scorecard_event",
    ):
        nested = item.get(key)
        if isinstance(nested, Mapping):
            return dict(nested)
    return item


def _normalize_coverage_group(group: Any, relation_types: Sequence[str] | None = None) -> str:
    raw = _clean(group)
    raw_lower = raw.lower()
    relations = _dedupe(relation_types)
    if raw_lower in COMPLETE_COVERAGE_GROUP_ORDER:
        return raw_lower
    if raw_lower in {"", "unclassified", "unknown", "missing", "none", "null", COMPLETE_SCORECARD_COVERAGE_GROUP_MISSING}:
        for relation in relations:
            mapped = _RELATION_TO_COVERAGE_GROUP.get(str(relation).lower())
            if mapped:
                return mapped
        return COMPLETE_SCORECARD_COVERAGE_GROUP_MISSING
    if raw_lower in _COVERAGE_GROUP_ALIASES:
        return _COVERAGE_GROUP_ALIASES[raw_lower]
    for relation in relations:
        mapped = _RELATION_TO_COVERAGE_GROUP.get(str(relation).lower())
        if mapped:
            return mapped
    return raw_lower


def _event_relation_types(event: Mapping[str, Any]) -> list[str]:
    return _dedupe([
        *_dedupe(event.get("relation_types")),
        *_dedupe(event.get("used_relation_ids")),
    ])


def build_complete_scorecard_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_SCORECARD_SERVICE_VERSION,
        "target_step": COMPLETE_SCORECARD_STEP,
        "step": COMPLETE_SCORECARD_STEP,
        "implementation_unit": COMPLETE_SCORECARD_IMPLEMENTATION_UNIT,
        "stage": "complete_composer_initial",
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "scorecard_service_added": True,
        "fixture_suite_added": True,
        "fixture_extension_added": True,
        "product_quality_coverage_suite_version": COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION,
        "blind_qa_rubric_added": True,
        "tone_engine_added": True,
        "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
        "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "tone_engine_step": COMPLETE_TONE_ENGINE_STAGE,
        "tone_policy_scorecard_connected": True,
        "tone_guard_metrics_added": True,
        "tone_meaning_added_allowed": False,
        "coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "coverage_taxonomy": {key: {nested_key: _dedupe(nested_value) for nested_key, nested_value in value.items()} for key, value in _COVERAGE_TAXONOMY.items()},
        "coverage_groups_supported": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "coverage_group_missing_key": COMPLETE_SCORECARD_COVERAGE_GROUP_MISSING,
        "missing_group_falls_back_to_short_daily": False,
        "coverage_runtime_baseline_step": "Step4_Coverage_Runtime_Baseline",
        "initial_display_target_range": [COMPLETE_INITIAL_DISPLAY_TARGET_MIN, COMPLETE_INITIAL_DISPLAY_TARGET_MAX],
        "product_gate_display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
        "binding_target_rate": COMPLETE_BINDING_TARGET_RATE,
        "read_feeling_initial_target": COMPLETE_READ_FEELING_INITIAL_TARGET,
        "product_gate_evaluation": "not_evaluated_initial_version",
        "comment_text_contract": "passed_only",
        "comment_text_generated": False,
        "comment_text_written_by_step12": False,
        "comment_text_key_written": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "external_ai_allowed": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "raw_input_required_for_improvement": False,
    }


def build_complete_initial_fixture_suite(
    *,
    additional_cases: Sequence[CompleteScorecardFixtureCase | Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the Step 12 fixture suite without raw input examples."""

    cases: list[dict[str, Any]] = [case.as_meta() for case in _DEFAULT_FIXTURE_CASES]
    for item in list(additional_cases or ()):  # explicit internal QA extension point
        if isinstance(item, CompleteScorecardFixtureCase):
            cases.append(item.as_meta())
            continue
        if isinstance(item, Mapping):
            safe = _safe_json(item)
            if isinstance(safe, dict):
                safe["coverage_group"] = _normalize_coverage_group(safe.get("coverage_group"), _dedupe(safe.get("target_relations")))
                safe.setdefault("fixture_id", f"complete_fixture_extra_{len(cases) + 1:02d}")
                safe.setdefault("scenario_key", "additional_structural_fixture")
                safe.setdefault("fixture_kind", "eligible_normal_input")
                safe.setdefault("raw_input_included", False)
                safe.setdefault("raw_text_included", False)
                cases.append(safe)
    by_group: dict[str, list[dict[str, Any]]] = {group: [] for group in COMPLETE_COVERAGE_GROUP_ORDER}
    for case in cases:
        group = _normalize_coverage_group(case.get("coverage_group"), _dedupe(case.get("target_relations")))
        case["coverage_group"] = group
        by_group.setdefault(group, []).append(case)
    fixture_counts = {group: len(rows) for group, rows in by_group.items()}
    return {
        "version": COMPLETE_SCORECARD_FIXTURE_SUITE_VERSION,
        "target_step": COMPLETE_SCORECARD_STEP,
        "step": COMPLETE_SCORECARD_STEP,
        "fixture_suite_added": True,
        "product_quality_coverage_suite_version": COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION,
        "ready": True,
        "scorecard_fixture_suite_ready": True,
        "fixture_kind": "complete_composer_initial_structural_fixture_suite",
        "coverage_groups": list(COMPLETE_COVERAGE_GROUP_ORDER),
        "coverage_taxonomy": {key: {nested_key: _dedupe(nested_value) for nested_key, nested_value in value.items()} for key, value in _COVERAGE_TAXONOMY.items()},
        "fixture_count": len(cases),
        "fixture_counts_by_group": fixture_counts,
        "fixture_suite_ready": all(fixture_counts.get(group, 0) > 0 for group in COMPLETE_COVERAGE_GROUP_ORDER),
        "missing_coverage_groups": [group for group in COMPLETE_COVERAGE_GROUP_ORDER if fixture_counts.get(group, 0) <= 0],
        "fixtures": cases,
        "fixtures_by_group": by_group,
        "blind_qa_rubric": {
            "version": "emlis.complete_blind_qa_rubric.v1",
            "read_feeling_initial_target": COMPLETE_READ_FEELING_INITIAL_TARGET,
            "read_feeling_product_target": COMPLETE_READ_FEELING_PRODUCT_TARGET,
            "dimensions": {
                "input_specific_structure_reflected": {
                    "weight": 0.30,
                    "checks": ["input_specific_structure_reflected", "input_feels_read"],
                },
                "relation_kept": {
                    "weight": 0.18,
                    "checks": ["relation_type_present", "relation_surface_present"],
                },
                "tone_distance_stable": {
                    "weight": 0.12,
                    "checks": ["not_too_close", "not_cold", "no_over_empathy", "no_generic_comfort"],
                },
                "evidence_bound": {
                    "weight": 0.25,
                    "checks": ["sentence_binding_present", "evidence_span_ids_present"],
                },
                "natural_but_not_template": {
                    "weight": 0.15,
                    "checks": ["natural_japanese_surface", "no_fixed_output", "same_ending_not_repeated"],
                },
                "no_diagnosis_or_personality_claim": {
                    "weight": 0.10,
                    "checks": ["no_diagnosis_or_personality_claim", "no_action_instruction"],
                },
            },
            "raw_input_required_for_improvement": False,
        },
        "raw_input_included": False,
        "raw_text_included": False,
        "expected_comment_text_included": False,
        "fixed_output_text_contract": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
    }


def build_complete_blind_qa_rubric() -> dict[str, Any]:
    return {
        "version": "emlis.complete_blind_qa_rubric.v1",
        "target_step": COMPLETE_SCORECARD_STEP,
        "purpose": "blind_qa_read_feeling_without_exact_sentence_lock",
        "read_feeling_initial_target": COMPLETE_READ_FEELING_INITIAL_TARGET,
        "read_feeling_product_target": COMPLETE_READ_FEELING_PRODUCT_TARGET,
        "dimensions": {
            "input_specific_structure_reflected": {
                "checks": ["input_specific_structure_reflected", "coverage_group_core_visible", "not_generic_summary"],
            },
            "relation_kept": {
                "checks": ["relation_type_traceable", "relation_visible_without_overclaim", "relation_kept"],
            },
            "evidence_bound": {
                "checks": ["sentence_binding_present", "phrase_or_evidence_ids_present", "evidence_bound"],
            },
            "natural_but_not_template": {
                "checks": ["surface_is_readable", "same_ending_not_major", "no_fixed_output"],
            },
            "no_diagnosis_or_personality_claim": {
                "checks": ["no_diagnosis", "no_other_person_judgment", "no_command"],
            },
        },
        "exact_comment_text_locked": False,
        "machine_test_only": False,
        "raw_input_required_for_improvement": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }

def _count_reason_markers(reasons: Iterable[str], markers: Sequence[str]) -> int:
    count = 0
    for reason in _dedupe(reasons):
        lowered = reason.lower()
        if any(marker in lowered for marker in markers):
            count += 1
    return count


def normalize_complete_scorecard_event(scorecard_event: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize a Step 11 event for Step 12 aggregation."""

    event = _source_event(scorecard_event or {})
    relation_types = _event_relation_types(event)
    coverage_group = _normalize_coverage_group(event.get("coverage_group") or event.get("coverage_scope"), relation_types)
    eligible_count = _safe_int(event.get("eligible_count"), 0)
    if eligible_count <= 0 and bool(event.get("complete_candidate_seen")):
        eligible_count = 1
    candidate_generated_count = _safe_int(event.get("candidate_generated_count"), 0)
    if candidate_generated_count <= 0 and bool(event.get("complete_candidate_generated")):
        candidate_generated_count = 1
    passed_display_count = _safe_int(event.get("passed_display_count"), 0)
    if passed_display_count <= 0 and bool(event.get("complete_candidate_displayed") or event.get("display_passed")):
        passed_display_count = 1
    observation_status = _clean(event.get("observation_status")) or ("passed" if passed_display_count else "unavailable")
    binding_pass = bool(event.get("binding_pass"))
    binding_count = _safe_int(event.get("binding_count"), 0)
    # Step2 prefers sentence-level binding counts.  Older Step9/Step12 events
    # only expose binding_pass/binding_count, so do not treat their binding_count
    # as an expected sentence denominator unless sentence-level fields are present.
    binding_supported_sentence_count = _safe_int(event.get("binding_supported_sentence_count"), 0)
    expected_binding_count = _safe_int(event.get("expected_binding_count"), 0)
    has_sentence_binding_counts = bool(expected_binding_count > 0 or binding_supported_sentence_count > 0)
    if has_sentence_binding_counts and expected_binding_count <= 0:
        expected_binding_count = binding_count
    sentence_binding_pass_rate = _rate(binding_supported_sentence_count, expected_binding_count)
    if expected_binding_count:
        binding_pass = bool(binding_pass or sentence_binding_pass_rate >= COMPLETE_BINDING_TARGET_RATE)
    read_feeling_score = _safe_float(event.get("read_feeling_score"))
    reason_markers = _dedupe([
        *_dedupe(event.get("top_rejection_reasons") or event.get("gate_rejection_reasons")),
        event.get("primary_reason"),
        event.get("gate_primary_reason"),
    ])
    surface_same_ending_major_count = _safe_int(event.get("surface_same_ending_major_count"), 0)
    surface_signature_repeat_count = _safe_int(event.get("surface_signature_repeat_count"), 0)
    surface_connector_repetition_count = _safe_int(event.get("surface_connector_repetition_count"), 0)
    surface_variation_major_count = _safe_int(event.get("surface_variation_major_count"), 0)
    if surface_variation_major_count <= 0:
        surface_variation_major_count = surface_same_ending_major_count + surface_signature_repeat_count + surface_connector_repetition_count
    tone_guard_major_count = _safe_int(event.get("tone_guard_major_count"), 0)
    tone_over_empathy_count = _safe_int(event.get("tone_over_empathy_count"), _safe_int(event.get("over_empathy_count"), 0))
    tone_diagnostic_count = _safe_int(event.get("tone_diagnostic_count"), _safe_int(event.get("diagnostic_tone_count"), 0))
    tone_advice_count = _safe_int(event.get("tone_advice_count"), _safe_int(event.get("advice_like_count"), 0))
    tone_generic_count = _safe_int(event.get("tone_generic_count"), _safe_int(event.get("generic_comfort_count"), 0))
    tone_guard_report = event.get("tone_guard_report") if isinstance(event.get("tone_guard_report"), Mapping) else {}
    if tone_guard_report:
        tone_guard_major_count = max(tone_guard_major_count, _safe_int(tone_guard_report.get("tone_guard_major_count"), 0))
        tone_over_empathy_count = max(tone_over_empathy_count, _safe_int(tone_guard_report.get("over_empathy_count"), 0))
        tone_diagnostic_count = max(tone_diagnostic_count, _safe_int(tone_guard_report.get("diagnostic_tone_count"), 0))
        tone_advice_count = max(tone_advice_count, _safe_int(tone_guard_report.get("advice_like_count"), 0))
        tone_generic_count = max(tone_generic_count, _safe_int(tone_guard_report.get("generic_comfort_count"), 0))
    tone_guard_reasons = _dedupe([
        *_dedupe(event.get("tone_guard_reasons")),
        *_dedupe(tone_guard_report.get("tone_guard_reasons") if isinstance(tone_guard_report, Mapping) else None),
        *_dedupe(tone_guard_report.get("blocker_reasons") if isinstance(tone_guard_report, Mapping) else None),
    ])
    tone_meaning_added = bool(event.get("tone_meaning_added") or event.get("meaning_added_by_tone_policy") or (tone_guard_report.get("meaning_added_by_tone_policy") if isinstance(tone_guard_report, Mapping) else False))
    reason_markers = _dedupe([*reason_markers, *tone_guard_reasons])
    template_major_count = _safe_int(event.get("template_major_count"), 0) + _count_reason_markers(reason_markers, _TEMPLATE_REASON_MARKERS)
    if template_major_count <= 0 and surface_variation_major_count > 0:
        template_major_count = surface_variation_major_count
    safety_major_count = _safe_int(event.get("safety_major_count"), 0) + _count_reason_markers(reason_markers, _SAFETY_REASON_MARKERS)
    if safety_major_count < tone_guard_major_count:
        safety_major_count = tone_guard_major_count
    if observation_status == "safety_blocked" and safety_major_count <= 0:
        safety_major_count = 1
    repair_trace_v2_count = _safe_int(event.get("repair_trace_v2_count"), _safe_int(event.get("repair_trace_count"), 0))
    repair_passed_count = _safe_int(event.get("repair_passed_count"), 0)
    repair_failed_count = _safe_int(event.get("repair_failed_count"), 0)
    repair_aborted_count = _safe_int(event.get("repair_aborted_count"), 0)
    repair_meaning_added_count = _safe_int(event.get("repair_meaning_added_count"), 0)
    repair_policy_violation_count = _safe_int(event.get("repair_policy_violation_count"), 0)
    repair_attempted = bool(event.get("repair_attempted")) or repair_trace_v2_count > 0 or _safe_int(event.get("repair_trace_count"), 0) > 0
    repair_success = bool(event.get("repair_success")) and repair_meaning_added_count == 0 and repair_policy_violation_count == 0
    repair_operation_counts = event.get("repair_operation_counts") if isinstance(event.get("repair_operation_counts"), Mapping) else {}
    repair_reason_counts = event.get("repair_reason_counts") if isinstance(event.get("repair_reason_counts"), Mapping) else {}
    normalized = {
        "version": COMPLETE_SCORECARD_NORMALIZED_EVENT_VERSION,
        "source_event_version": _clean(event.get("version")) or COMPLETE_SCORECARD_EVENT_VERSION,
        "target_step": COMPLETE_SCORECARD_STEP,
        "source_step": _clean(event.get("source_step")),
        "event_kind": _clean(event.get("event_kind")) or "complete_composer_initial_reply_attempt",
        "coverage_group": coverage_group,
        "coverage_scope": _clean(event.get("coverage_scope")),
        "observation_status": observation_status,
        "eligible_count": eligible_count,
        "candidate_generated_count": candidate_generated_count,
        "passed_display_count": passed_display_count,
        "rejected_count": 1 if eligible_count and observation_status == "rejected" else 0,
        "unavailable_count": 1 if eligible_count and observation_status == "unavailable" else 0,
        "safety_blocked_count": 1 if observation_status == "safety_blocked" else 0,
        "binding_pass": binding_pass,
        "binding_pass_count": 1 if binding_pass else 0,
        "binding_count": binding_count,
        "binding_supported_sentence_count": binding_supported_sentence_count,
        "expected_binding_count": expected_binding_count,
        "sentence_binding_pass_rate": sentence_binding_pass_rate,
        "unsupported_sentence_ids": list(_dedupe(event.get("unsupported_sentence_ids"))),
        "relation_not_expressed_sentence_ids": list(_dedupe(event.get("relation_not_expressed_sentence_ids"))),
        "phrase_unit_missing_sentence_ids": list(_dedupe(event.get("phrase_unit_missing_sentence_ids"))),
        "weak_material_sentence_ids": list(_dedupe(event.get("weak_material_sentence_ids"))),
        "binding_support_source": _clean(event.get("binding_support_source")),
        "binding_present": bool(event.get("binding_present") or binding_count > 0),
        "used_evidence_span_count": _safe_int(event.get("used_evidence_span_count"), 0),
        "used_phrase_unit_count": _safe_int(event.get("used_phrase_unit_count"), 0),
        "used_relation_count": _safe_int(event.get("used_relation_count"), 0),
        "relation_types": relation_types,
        "repair_attempted": repair_attempted,
        "repair_attempt_count": 1 if repair_attempted else 0,
        "repair_success": repair_success,
        "repair_success_count": 1 if repair_success else 0,
        "repair_trace_contract_version": _clean(event.get("repair_trace_contract_version")),
        "repair_trace_v2_count": repair_trace_v2_count,
        "repair_passed_count": repair_passed_count,
        "repair_failed_count": repair_failed_count,
        "repair_aborted_count": repair_aborted_count,
        "repair_meaning_added_count": repair_meaning_added_count,
        "repair_policy_violation_count": repair_policy_violation_count,
        "repair_operation_counts": {str(key): _safe_int(value, 0) for key, value in repair_operation_counts.items()},
        "repair_reason_counts": {str(key): _safe_int(value, 0) for key, value in repair_reason_counts.items()},
        "template_major_count": template_major_count,
        "surface_same_ending_major_count": surface_same_ending_major_count,
        "surface_signature_repeat_count": surface_signature_repeat_count,
        "surface_connector_repetition_count": surface_connector_repetition_count,
        "surface_variation_major_count": surface_variation_major_count,
        "surface_variation_passed": bool(event.get("surface_variation_passed", surface_variation_major_count == 0)),
        "tone_engine_version": _clean(event.get("tone_engine_version")) or COMPLETE_TONE_ENGINE_VERSION,
        "product_quality_tone_engine_version": _clean(event.get("product_quality_tone_engine_version")) or COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "tone_policy_applied": bool(event.get("tone_policy_applied", True)),
        "tone_guard_report": _safe_json(tone_guard_report) if tone_guard_report else {},
        "tone_guard_major_count": tone_guard_major_count,
        "tone_guard_passed": bool(event.get("tone_guard_passed", tone_guard_major_count == 0)) and tone_guard_major_count == 0,
        "tone_guard_reasons": tone_guard_reasons,
        "tone_over_empathy_count": tone_over_empathy_count,
        "tone_diagnostic_count": tone_diagnostic_count,
        "tone_advice_count": tone_advice_count,
        "tone_generic_count": tone_generic_count,
        "tone_meaning_added": tone_meaning_added,
        "tone_meaning_added_count": 1 if tone_meaning_added else 0,
        "safety_major_count": safety_major_count,
        "read_feeling_score": read_feeling_score,
        "read_feeling_evaluated_count": 1 if read_feeling_score is not None else 0,
        "read_feeling_pass_count": 1 if (read_feeling_score is not None and read_feeling_score >= COMPLETE_READ_FEELING_INITIAL_TARGET) else 0,
        "top_rejection_reasons": reason_markers[:8],
        "gate_primary_reason": _clean(event.get("gate_primary_reason") or event.get("primary_reason")),
        "complete_initial_client_used": bool(event.get("complete_initial_client_used")),
        "explicit_client_used": bool(event.get("explicit_client_used")),
        "product_gate_evaluation": "not_evaluated_initial_version",
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    return normalized


def _empty_bucket(group: str, fixture_suite: Mapping[str, Any]) -> dict[str, Any]:
    fixture_counts = fixture_suite.get("fixture_counts_by_group") if isinstance(fixture_suite, Mapping) else {}
    return {
        "coverage_group": group,
        "fixture_count": _safe_int((fixture_counts or {}).get(group), 0) if isinstance(fixture_counts, Mapping) else 0,
        "event_count": 0,
        "eligible_count": 0,
        "candidate_generated_count": 0,
        "passed_display_count": 0,
        "rejected_count": 0,
        "unavailable_count": 0,
        "safety_blocked_count": 0,
        "binding_pass_count": 0,
        "binding_count_total": 0,
        "binding_supported_sentence_count_total": 0,
        "expected_binding_count_total": 0,
        "repair_attempt_count": 0,
        "repair_success_count": 0,
        "repair_trace_v2_count": 0,
        "repair_passed_count": 0,
        "repair_failed_count": 0,
        "repair_aborted_count": 0,
        "repair_meaning_added_count": 0,
        "repair_policy_violation_count": 0,
        "template_major_count": 0,
        "surface_same_ending_major_count": 0,
        "surface_signature_repeat_count": 0,
        "surface_connector_repetition_count": 0,
        "surface_variation_major_count": 0,
        "tone_guard_major_count": 0,
        "tone_over_empathy_count": 0,
        "tone_diagnostic_count": 0,
        "tone_advice_count": 0,
        "tone_generic_count": 0,
        "tone_meaning_added_count": 0,
        "safety_major_count": 0,
        "read_feeling_evaluated_count": 0,
        "read_feeling_pass_count": 0,
        "relation_type_counts": {},
        "repair_operation_counts": {},
        "repair_reason_counts": {},
        "reason_counts": {},
        "display_reach_rate": 0.0,
        "candidate_generation_rate": 0.0,
        "binding_pass_rate": 0.0,
        "repair_success_rate": 0.0,
        "read_feeling_pass_rate": 0.0,
        "non_template_major_clear": True,
        "safety_major_clear": True,
    }


def _inc_count_map(bucket: dict[str, Any], field: str, key: Any, count: int = 1) -> None:
    key_text = _clean(key)
    if not key_text:
        return
    values = dict(bucket.get(field) or {})
    values[key_text] = _safe_int(values.get(key_text), 0) + int(count)
    bucket[field] = values


def _merge_event(bucket: dict[str, Any], event: Mapping[str, Any]) -> None:
    bucket["event_count"] += 1
    for key in (
        "eligible_count",
        "candidate_generated_count",
        "passed_display_count",
        "rejected_count",
        "unavailable_count",
        "safety_blocked_count",
        "binding_pass_count",
        "repair_attempt_count",
        "repair_success_count",
        "repair_trace_v2_count",
        "repair_passed_count",
        "repair_failed_count",
        "repair_aborted_count",
        "repair_meaning_added_count",
        "repair_policy_violation_count",
        "template_major_count",
        "surface_same_ending_major_count",
        "surface_signature_repeat_count",
        "surface_connector_repetition_count",
        "surface_variation_major_count",
        "tone_guard_major_count",
        "tone_over_empathy_count",
        "tone_diagnostic_count",
        "tone_advice_count",
        "tone_generic_count",
        "tone_meaning_added_count",
        "safety_major_count",
        "read_feeling_evaluated_count",
        "read_feeling_pass_count",
    ):
        bucket[key] = _safe_int(bucket.get(key), 0) + _safe_int(event.get(key), 0)
    bucket["binding_count_total"] = _safe_int(bucket.get("binding_count_total"), 0) + _safe_int(event.get("binding_count"), 0)
    bucket["binding_supported_sentence_count_total"] = _safe_int(bucket.get("binding_supported_sentence_count_total"), 0) + _safe_int(event.get("binding_supported_sentence_count"), 0)
    bucket["expected_binding_count_total"] = _safe_int(bucket.get("expected_binding_count_total"), 0) + _safe_int(event.get("expected_binding_count"), 0)
    for relation in _dedupe(event.get("relation_types")):
        _inc_count_map(bucket, "relation_type_counts", relation)
    repair_operation_counts = event.get("repair_operation_counts")
    if isinstance(repair_operation_counts, Mapping):
        for operation, count in repair_operation_counts.items():
            _inc_count_map(bucket, "repair_operation_counts", operation, _safe_int(count, 0))
    repair_reason_counts = event.get("repair_reason_counts")
    if isinstance(repair_reason_counts, Mapping):
        for reason, count in repair_reason_counts.items():
            _inc_count_map(bucket, "repair_reason_counts", reason, _safe_int(count, 0))
            _inc_count_map(bucket, "reason_counts", reason, _safe_int(count, 0))
    for reason in _dedupe(event.get("top_rejection_reasons")):
        _inc_count_map(bucket, "reason_counts", reason)
    for reason in _dedupe(event.get("tone_guard_reasons")):
        _inc_count_map(bucket, "reason_counts", f"tone_guard:{reason}")
    primary_reason = _clean(event.get("gate_primary_reason"))
    if primary_reason:
        _inc_count_map(bucket, "reason_counts", primary_reason)
    eligible = _safe_int(bucket.get("eligible_count"), 0)
    repair_attempts = _safe_int(bucket.get("repair_attempt_count"), 0)
    read_eval = _safe_int(bucket.get("read_feeling_evaluated_count"), 0)
    bucket["display_reach_rate"] = _rate(_safe_int(bucket.get("passed_display_count"), 0), eligible)
    bucket["candidate_generation_rate"] = _rate(_safe_int(bucket.get("candidate_generated_count"), 0), eligible)
    expected_bindings = _safe_int(bucket.get("expected_binding_count_total"), 0)
    if expected_bindings:
        bucket["binding_pass_rate"] = _rate(_safe_int(bucket.get("binding_supported_sentence_count_total"), 0), expected_bindings)
    else:
        bucket["binding_pass_rate"] = _rate(_safe_int(bucket.get("binding_pass_count"), 0), eligible)
    bucket["repair_success_rate"] = _rate(_safe_int(bucket.get("repair_success_count"), 0), repair_attempts)
    bucket["read_feeling_pass_rate"] = _rate(_safe_int(bucket.get("read_feeling_pass_count"), 0), read_eval)
    bucket["non_template_major_clear"] = _safe_int(bucket.get("template_major_count"), 0) == 0
    bucket["safety_major_clear"] = _safe_int(bucket.get("safety_major_count"), 0) == 0


def aggregate_complete_scorecard_events(
    events: Sequence[Any] | Iterable[Any] | None = None,
    *,
    fixture_suite: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    suite = dict(fixture_suite or build_complete_initial_fixture_suite())
    normalized = [normalize_complete_scorecard_event(_source_event(item)) for item in list(events or [])]
    totals = _empty_bucket("all", suite)
    by_group: dict[str, dict[str, Any]] = {group: _empty_bucket(group, suite) for group in COMPLETE_COVERAGE_GROUP_ORDER}
    for event in normalized:
        group = _normalize_coverage_group(event.get("coverage_group"), _dedupe(event.get("relation_types")))
        _merge_event(totals, event)
        bucket = by_group.setdefault(group, _empty_bucket(group, suite))
        _merge_event(bucket, event)
    groups_with_events = [group for group, row in by_group.items() if _safe_int(row.get("event_count"), 0) > 0]
    required_groups = list(COMPLETE_COVERAGE_GROUP_ORDER)
    missing_fixture_groups = [group for group in required_groups if group not in groups_with_events]
    fixture_coverage_rate = _rate(len(groups_with_events), len(required_groups))
    release_blockers: list[str] = []
    if _safe_int(totals.get("safety_major_count"), 0) > 0:
        release_blockers.append("safety_major_detected")
    if _safe_int(totals.get("tone_guard_major_count"), 0) > 0:
        release_blockers.append("tone_guard_major_detected")
    if _safe_int(totals.get("tone_meaning_added_count"), 0) > 0:
        release_blockers.append("tone_meaning_added_detected")
    if _safe_int(totals.get("template_major_count"), 0) > 0:
        release_blockers.append("template_major_detected")
    if _safe_int(totals.get("repair_meaning_added_count"), 0) > 0:
        release_blockers.append("repair_meaning_added_detected")
    if _safe_int(totals.get("repair_policy_violation_count"), 0) > 0:
        release_blockers.append("repair_policy_violation_detected")
    if _safe_int(totals.get("eligible_count", 0), 0) and float(totals.get("binding_pass_rate") or 0.0) < COMPLETE_BINDING_TARGET_RATE:
        release_blockers.append("binding_target_not_met")
    if missing_fixture_groups:
        release_blockers.append("fixture_coverage_incomplete")
    rows = [by_group[group] for group in sorted(by_group, key=lambda key: (COMPLETE_COVERAGE_GROUP_ORDER.index(key) if key in COMPLETE_COVERAGE_GROUP_ORDER else 99, key))]
    groups_needing_attention = [
        str(row.get("coverage_group"))
        for row in rows
        if _safe_int(row.get("rejected_count"), 0)
        or _safe_int(row.get("unavailable_count"), 0)
        or _safe_int(row.get("safety_blocked_count"), 0)
        or _safe_int(row.get("safety_major_count"), 0)
        or _safe_int(row.get("tone_guard_major_count"), 0)
        or _safe_int(row.get("tone_meaning_added_count"), 0)
        or _safe_int(row.get("template_major_count"), 0)
        or _safe_int(row.get("repair_meaning_added_count"), 0)
        or _safe_int(row.get("repair_policy_violation_count"), 0)
        or (_safe_int(row.get("eligible_count"), 0) and float(row.get("binding_pass_rate") or 0.0) < COMPLETE_BINDING_TARGET_RATE)
    ]
    return {
        "version": COMPLETE_SCORECARD_AGGREGATE_VERSION,
        "target_step": COMPLETE_SCORECARD_STEP,
        "step": COMPLETE_SCORECARD_STEP,
        "implementation_unit": COMPLETE_SCORECARD_IMPLEMENTATION_UNIT,
        "phase": "complete_composer_initial",
        "purpose": "aggregate_complete_initial_fixture_display_binding_read_feeling_safety_template_metrics",
        "ready": bool(normalized),
        "scorecard_ready": bool(normalized),
        "event_count": len(normalized),
        "record_count": len(normalized),
        "fixture_suite_version": _clean(suite.get("version")),
        "fixture_count": _safe_int(suite.get("fixture_count"), 0),
        "required_coverage_groups": required_groups,
        "groups_with_events": groups_with_events,
        "missing_fixture_groups": missing_fixture_groups,
        "fixture_coverage_rate": fixture_coverage_rate,
        "totals": totals,
        "coverage_group_rows": rows,
        "by_coverage_group": {str(row.get("coverage_group")): dict(row) for row in rows},
        "display_reach_rate": float(totals.get("display_reach_rate") or 0.0),
        "candidate_generation_rate": float(totals.get("candidate_generation_rate") or 0.0),
        "binding_pass_rate": float(totals.get("binding_pass_rate") or 0.0),
        "read_feeling_pass_rate": float(totals.get("read_feeling_pass_rate") or 0.0),
        "safety_major_count": _safe_int(totals.get("safety_major_count"), 0),
        "template_major_count": _safe_int(totals.get("template_major_count"), 0),
        "tone_guard_major_count": _safe_int(totals.get("tone_guard_major_count"), 0),
        "tone_over_empathy_count": _safe_int(totals.get("tone_over_empathy_count"), 0),
        "tone_diagnostic_count": _safe_int(totals.get("tone_diagnostic_count"), 0),
        "tone_advice_count": _safe_int(totals.get("tone_advice_count"), 0),
        "tone_generic_count": _safe_int(totals.get("tone_generic_count"), 0),
        "tone_meaning_added_count": _safe_int(totals.get("tone_meaning_added_count"), 0),
        "read_feeling_evaluated_count": _safe_int(totals.get("read_feeling_evaluated_count"), 0),
        "groups_needing_attention": groups_needing_attention,
        "non_template_major_clear": bool(totals.get("non_template_major_clear")),
        "safety_major_clear": bool(totals.get("safety_major_clear")),
        "initial_display_target_range": [COMPLETE_INITIAL_DISPLAY_TARGET_MIN, COMPLETE_INITIAL_DISPLAY_TARGET_MAX],
        "product_gate_display_target": COMPLETE_PRODUCT_GATE_DISPLAY_TARGET,
        "binding_target_rate": COMPLETE_BINDING_TARGET_RATE,
        "read_feeling_initial_target": COMPLETE_READ_FEELING_INITIAL_TARGET,
        "product_gate_evaluation": "not_evaluated_initial_version",
        "product_gate_reached": False,
        "release_blockers": release_blockers,
        "next_step": "Step13_RN_contract_regression",
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


def build_complete_scorecard_harness(
    *,
    scorecard_event: Mapping[str, Any] | None = None,
    scorecard_events: Sequence[Any] | Iterable[Any] | None = None,
    records: Sequence[Any] | Iterable[Any] | None = None,
    fixture_suite: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    suite = dict(fixture_suite or build_complete_initial_fixture_suite())
    if not scorecard_event and isinstance(diagnostic_summary, Mapping):
        scorecard_event = _source_event(diagnostic_summary)
    normalized_event = normalize_complete_scorecard_event(scorecard_event or {})
    all_records: list[Any] = []
    if scorecard_event:
        all_records.append(normalized_event)
    all_records.extend(list(scorecard_events or []))
    all_records.extend(list(records or []))
    aggregate = aggregate_complete_scorecard_events(all_records, fixture_suite=suite)
    group = str(normalized_event.get("coverage_group") or "short_daily")
    group_scorecard = dict((aggregate.get("by_coverage_group") or {}).get(group) or {})
    contract = build_complete_scorecard_contract_meta()
    blind_qa_rubric = build_complete_blind_qa_rubric()
    return {
        **contract,
        "version": COMPLETE_SCORECARD_HARNESS_VERSION,
        "target_step": COMPLETE_SCORECARD_STEP,
        "step": COMPLETE_SCORECARD_STEP,
        "scorecard_harness_added": True,
        "scorecard_ready": bool(aggregate.get("scorecard_ready")),
        "ready": bool(aggregate.get("ready")),
        "event": normalized_event,
        "normalized_event": normalized_event,
        "source_event_version": normalized_event.get("source_event_version"),
        "fixture_suite": suite,
        "blind_qa_rubric": blind_qa_rubric,
        "read_feeling_requires_blind_qa": True,
        "aggregate": aggregate,
        "scorecard_aggregate": aggregate,
        "coverage_group": group,
        "coverage_group_scorecard": group_scorecard,
        "coverage_group_rows": list(aggregate.get("coverage_group_rows") or []),
        "by_coverage_group": dict(aggregate.get("by_coverage_group") or {}),
        "display_reach_rate": float(aggregate.get("display_reach_rate") or 0.0),
        "candidate_generation_rate": float(aggregate.get("candidate_generation_rate") or 0.0),
        "binding_pass_rate": float(aggregate.get("binding_pass_rate") or 0.0),
        "read_feeling_pass_rate": float(aggregate.get("read_feeling_pass_rate") or 0.0),
        "non_template_major_clear": bool(aggregate.get("non_template_major_clear")),
        "safety_major_clear": bool(aggregate.get("safety_major_clear")),
        "tone_guard_major_count": _safe_int(aggregate.get("tone_guard_major_count"), 0),
        "tone_guard_clear": _safe_int(aggregate.get("tone_guard_major_count"), 0) == 0,
        "tone_meaning_added_count": _safe_int(aggregate.get("tone_meaning_added_count"), 0),
        "missing_fixture_groups": list(aggregate.get("missing_fixture_groups") or []),
        "fixture_coverage_rate": float(aggregate.get("fixture_coverage_rate") or 0.0),
        "release_blockers": list(aggregate.get("release_blockers") or []),
        "ready_for_step13_rn_contract_regression": bool(aggregate.get("scorecard_ready")),
        "product_gate_evaluation": "not_product_gate_initial_version",
        "read_feeling_requires_blind_qa": True,
        "machine_test_only": False,
        "comment_text_contract": "passed_only",
        "comment_text_generated": False,
        "comment_text_written_by_step12": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "input_specific_template_added": False,
        "fixed_completed_sentence_template_added": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


# Compatibility aliases for shorter call sites.
def build_complete_scorecard_fixture_suite(
    fixtures: Sequence[CompleteScorecardFixtureCase | Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return build_complete_initial_fixture_suite(additional_cases=fixtures)


def build_complete_fixture_suite(
    fixtures: Sequence[CompleteScorecardFixtureCase | Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return build_complete_scorecard_fixture_suite(fixtures)


def build_complete_scorecard_event(*, scorecard_event: Mapping[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_complete_scorecard_event(scorecard_event or {})
    read_score = normalized.get("read_feeling_score")
    if read_score is None:
        read_verdict = "not_evaluated"
    else:
        read_verdict = "green" if float(read_score) >= COMPLETE_READ_FEELING_INITIAL_TARGET else "red"
    return {
        **normalized,
        "version": COMPLETE_SCORECARD_EVENT_VERSION,
        "normalized_event_version": normalized.get("version"),
        "scorecard_event_normalized_by_step12": True,
        "read_feeling_verdict": read_verdict,
        "safety_pass": _safe_int(normalized.get("safety_major_count"), 0) == 0,
        "non_template_pass": _safe_int(normalized.get("template_major_count"), 0) == 0,
        "comment_text_included": False,
        "raw_input_included": False,
        "response_shape_changed": False,
    }


build_complete_scorecard_report = build_complete_scorecard_harness
aggregate_complete_scorecard = aggregate_complete_scorecard_events


__all__ = [
    "COMPLETE_COVERAGE_GROUP_ORDER",
    "COMPLETE_SCORECARD_COVERAGE_GROUP_MISSING",
    "COMPLETE_SCORECARD_COVERAGE_GROUPS",
    "COMPLETE_SCORECARD_REQUIRED_COVERAGE_GROUPS",
    "COMPLETE_FIXTURE_SUITE_VERSION",
    "COMPLETE_SCORECARD_AGGREGATE_VERSION",
    "COMPLETE_SCORECARD_FIXTURE_SUITE_VERSION",
    "COMPLETE_PRODUCT_QUALITY_COVERAGE_SUITE_VERSION",
    "COMPLETE_SCORECARD_HARNESS_VERSION",
    "COMPLETE_SCORECARD_IMPLEMENTATION_UNIT",
    "COMPLETE_SCORECARD_STAGE",
    "COMPLETE_SCORECARD_NORMALIZED_EVENT_VERSION",
    "COMPLETE_SCORECARD_EVENT_NORMALIZED_VERSION",
    "COMPLETE_BLIND_QA_RUBRIC_VERSION",
    "COMPLETE_SCORECARD_SERVICE_VERSION",
    "COMPLETE_SCORECARD_STEP",
    "CompleteScorecardFixtureCase",
    "aggregate_complete_scorecard",
    "aggregate_complete_scorecard_events",
    "build_complete_fixture_suite",
    "build_complete_initial_fixture_suite",
    "build_complete_blind_qa_rubric",
    "build_complete_scorecard_event",
    "build_complete_scorecard_fixture_suite",
    "build_complete_scorecard_contract_meta",
    "build_complete_scorecard_harness",
    "build_complete_scorecard_report",
    "normalize_complete_scorecard_event",
]
