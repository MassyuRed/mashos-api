# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase17 test-only diagnostics for EmlisAI two-stage product visibility.

This helper is intentionally scoped to tests.  It builds the same local
CompleteComposer path used by Phase16 tests, classifies where each of the five
existing fixtures stops, and returns a meta-only evaluation report.  It does not
add runtime reply text, does not copy accepted QA probes into production, and
does not add public response keys.
"""

import json
import re
from functools import lru_cache
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

from fixtures.emlis_ai_two_stage_reception_cases import (
    TWO_STAGE_LABEL_MARKERS,
    TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS,
    current_input_for_two_stage_reception_case,
    evaluate_forbidden_surface_fragments,
    split_two_stage_comment_text,
    two_stage_reception_case_by_id,
)
# Keep this helper cheap to import.  Phase17-10 runs many existing regression
# modules in one process; importing the full CompleteComposer / observer stack at
# collection time can exceed the constrained local test runner memory budget.
# Heavy runtime dependencies are imported lazily inside the functions that need
# them.

PHASE17_PRODUCT_VISIBLE_FIXTURE_EVALUATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis_two_stage.product_visible_fixture_evaluation.v1"
)
PHASE17_PRODUCT_VISIBLE_FIXTURE_SOURCE_PHASE: Final = (
    "Phase17_two_stage_product_visible_fixture_completion"
)
PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS: Final = (
    "daily_unpleasant_encounter_A",
    "self_confidence_uncertainty_B",
    "positive_change_after_work_streaming",
    "self_blame_to_gentle_self_observation",
    "independence_life_health_money_pace",
)
assert set(PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS) == set(TWO_STAGE_RECEPTION_REQUIRED_CASE_IDS)

CLASSIFICATION_PASSED: Final = "passed"
CLASSIFICATION_UNAVAILABLE_SURFACE: Final = "unavailable_surface"
CLASSIFICATION_UNAVAILABLE_GROUNDING: Final = "unavailable_grounding"
CLASSIFICATION_VISIBLE_GATE_REJECTED: Final = "visible_gate_rejected"
CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG: Final = "product_visible_surface_ng"
CLASSIFICATION_PUBLIC_META_LEAK: Final = "public_meta_leak"
PHASE17_PRODUCT_VISIBLE_CLASSIFICATIONS: Final = (
    CLASSIFICATION_PASSED,
    CLASSIFICATION_UNAVAILABLE_SURFACE,
    CLASSIFICATION_UNAVAILABLE_GROUNDING,
    CLASSIFICATION_VISIBLE_GATE_REJECTED,
    CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG,
    CLASSIFICATION_PUBLIC_META_LEAK,
)

PHASE17_INTERNAL_ROLE_LABEL_FRAGMENTS: Final = (
    "achievement",
    "positive state",
    "positive_state",
    "perfection fear",
    "perfection_fear",
    "pressure or limit",
    "role_",
)
PHASE17_RELATION_SKELETON_FRAGMENTS: Final = (
    "同じ流れ",
    "同じ場所",
    "別々の向き",
    "片方だけに寄らず",
    "片方だけに減らさず",
    "重なりを保っています",
    "一方向には決まりきっていません",
)
PHASE17_PRODUCT_VISIBLE_FORBIDDEN_FRAGMENTS: Final = (
    *PHASE17_INTERNAL_ROLE_LABEL_FRAGMENTS,
    *PHASE17_RELATION_SKELETON_FRAGMENTS,
)

PHASE17_SECTION_BUDGET_BY_CASE_ID: Final = {
    "daily_unpleasant_encounter_A": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 1,
        "reception_max": 2,
    },
    "self_confidence_uncertainty_B": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "positive_change_after_work_streaming": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "self_blame_to_gentle_self_observation": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
    "independence_life_health_money_pace": {
        "observation_min": 1,
        "observation_max": 1,
        "reception_min": 2,
        "reception_max": 2,
    },
}

# Feature families are intentionally broad alternatives, not exact output text.
PHASE17_FEATURE_FAMILY_ALTERNATIVES_BY_CASE_ID: Final = {
    "daily_unpleasant_encounter_A": (
        ("daily_unpleasant_observation", ("不快", "気持ち悪", "嫌")),
        ("fear_or_anger_seen", ("怖", "恐怖", "怒り", "イライラ")),
        ("reaction_received", ("自然", "受け取", "残る")),
    ),
    "self_confidence_uncertainty_B": (
        ("self_confidence_wish_seen", ("自信",)),
        ("uncertainty_seen", ("不安", "大丈夫", "これでいい")),
        ("attempt_or_challenge_seen", ("直したい", "挑戦", "頑張りたい", "試して")),
    ),
    "positive_change_after_work_streaming": (
        ("work_fatigue_seen", ("仕事", "疲れ", "くたくた")),
        ("conversation_wish_seen", ("話したい", "お話", "誰かと")),
        ("positive_change_seen", ("変化", "嬉", "動揺", "気持ちが動")),
    ),
    "self_blame_to_gentle_self_observation": (
        ("self_blame_flow_seen", ("責め", "否定", "追い込")),
        ("gentle_observation_direction_seen", ("優しく", "気持ちを見", "見てあげ", "向き合")),
        ("not_end_with_denial_received", ("終わらせず", "見直", "大事に")),
    ),
    "independence_life_health_money_pace": (
        ("independence_intention_seen", ("自立",)),
        ("life_health_money_context_seen", ("生活", "体調", "お金")),
        ("sustainable_pace_seen", ("ペース", "続け", "無理")),
    ),
}

_BODY_LEAK_TRUE_FLAG_KEYS: Final = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "observation_text_included",
    "reception_text_included",
    "section_body_included",
)
_PUBLIC_CONTRACT_TRUE_FLAG_KEYS: Final = (
    "public_response_key_added",
    "public_response_key_change",
    "response_shape_changed",
    "rn_visible_contract_changed",
    "api_route_changed",
    "db_physical_name_changed",
)
_GATE_RELAXED_TRUE_FLAG_KEYS: Final = (
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
)
_FORBIDDEN_IMPL_TRUE_FLAG_KEYS: Final = (
    "fixed_string_renderer_used",
    "fixed_sentence_template_used",
    "completed_reply_template_used",
    "input_specific_template_used",
    "external_ai_used",
    "local_llm_used",
)
_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?]+|[\r\n]+")
_SPACE_RE: Final = re.compile(r"\s+")


def build_phase17_two_stage_product_visible_payload(
    case_id: str,
    *,
    trace_prefix: str = "phase17-product-visible",
) -> dict[str, Any]:
    """Build the CompleteComposer payload used by the Phase17 fixture tests."""

    from emlis_ai_conversation_composer_service import build_conversation_composer_payload
    from emlis_ai_evidence_ledger_service import build_evidence_ledger
    from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
    from emlis_ai_observation_integrator_service import integrate_perspective_board
    from emlis_ai_observation_structure_material_service import build_observation_structure_material
    from emlis_ai_perspective_board import build_perspective_board
    from emlis_ai_perspective_observers import run_perspective_observers

    case = two_stage_reception_case_by_id(case_id)
    current_input = current_input_for_two_stage_reception_case(case)
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible", {
        "case_id": case_id,
        "scope_status": scope.scope_status,
    }
    material = build_observation_structure_material(
        current_input=current_input,
        evidence_ledger=evidence,
    )
    return build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id=f"{trace_prefix}-{case_id}",
        limited_observation_scope=scope,
        observation_structure_material=material,
    )



@lru_cache(maxsize=len(PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS))
def _generate_phase17_two_stage_product_visible_candidate_cached(case_id: str) -> dict[str, Any]:
    """Generate one minimized direct CompleteComposer candidate per fixture case.

    Phase17-10 regression runs ask the same expensive CompleteComposer fixtures
    from multiple assertion layers.  The cached value is minimized to the meta
    fields asserted by these tests, so the regression runner does not retain all
    full diagnostic graphs at once while preserving the production runtime path
    used to generate the candidate.
    """

    from emlis_ai_complete_composer_client import CocolonCompleteComposerClient

    payload = build_phase17_two_stage_product_visible_payload(case_id)
    candidate = CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True).generate(payload)
    return _phase17_10_minimize_candidate_for_regression(case_id=case_id, candidate=candidate)


def _phase17_10_minimize_candidate_for_regression(*, case_id: str, candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only test-asserted candidate fields for Phase17-10 regression."""

    source_meta = _as_mapping(candidate.get("composer_meta"))
    comment_text = str(candidate.get("comment_text") or "")
    current = current_input_for_two_stage_reception_case(two_stage_reception_case_by_id(case_id))
    raw_fragments = tuple(
        fragment
        for fragment in (
            str(current.get("memo") or ""),
            str(current.get("memo_action") or ""),
        )
        if len(_clean(fragment)) >= 12
    )
    public_contract_prescan = {
        "raw_input_body_found_in_meta": any(_contains_text_recursive(source_meta, fragment) for fragment in raw_fragments),
        "comment_text_body_found_in_meta": bool(
            comment_text and len(_clean(comment_text)) >= 12 and _contains_text_recursive(source_meta, comment_text)
        ),
        "body_flag_true": _any_true_recursive(source_meta, _BODY_LEAK_TRUE_FLAG_KEYS),
        "contract_flag_true": _any_true_recursive(source_meta, _PUBLIC_CONTRACT_TRUE_FLAG_KEYS),
        "display_gate_relaxed": _any_true_recursive(source_meta, ("display_gate_relaxed", "gate_relaxed")),
        "grounding_gate_relaxed": _any_true_recursive(source_meta, ("grounding_gate_relaxed",)),
    }
    keep_keys = (
        "composer_source",
        "composition_contract",
        "state_answer_surface_contract",
        "state_answer_special_cases",
        "state_answer_special_cases_payload",
        "special_handling",
        "state_answer_two_stage_display_required",
        "state_answer_two_stage_reception_surface_required",
        "state_answer_joined_comment_text_required",
        "state_answer_section_labels_required",
        "state_answer_expected_comment_text_shape",
        "state_answer_composer_role_plan",
        "shared_reception_evidence",
        "reception_shared_evidence",
        "reception_mode",
        "reception_mode_summary",
        "reception_section_material",
        "two_stage_surface_realization",
        "sentence_plan",
        "initial_grounding_report",
        "final_grounding_report",
        "grounding_input",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "external_ai_used",
        "local_llm_used",
        "fixed_string_renderer_used",
        "fixed_sentence_template_used",
        "completed_reply_template_used",
        "public_response_key_added",
        "rn_visible_contract_changed",
    )
    minimized_meta = {key: source_meta.get(key) for key in keep_keys if key in source_meta}
    minimized_meta["phase17_10_public_contract_prescan"] = public_contract_prescan
    minimized_candidate = {
        "status": candidate.get("status"),
        "composer_source": candidate.get("composer_source"),
        "comment_text": comment_text,
        "primary_reason": candidate.get("primary_reason"),
        "rejection_reasons": list(candidate.get("rejection_reasons") or ()),
        "fixed_string_renderer_used": candidate.get("fixed_string_renderer_used"),
        "external_ai_used": candidate.get("external_ai_used"),
        "local_llm_used": candidate.get("local_llm_used"),
        "public_response_key_added": candidate.get("public_response_key_added"),
        "composer_meta": minimized_meta,
    }
    del candidate, source_meta
    _phase17_10_release_memory()
    return minimized_candidate


def generate_phase17_two_stage_product_visible_candidate(case_id: str) -> dict[str, Any]:
    """Generate one direct CompleteComposer candidate for a fixture case."""

    return _generate_phase17_two_stage_product_visible_candidate_cached(case_id)

def evaluate_phase17_two_stage_product_visible_candidate(
    *,
    case_id: str,
    candidate: Mapping[str, Any],
    current_input: Mapping[str, Any] | None = None,
    run_visible_gate: bool = True,
) -> dict[str, Any]:
    """Return a meta-only Phase17 product-visible evaluation report."""

    case = two_stage_reception_case_by_id(case_id)
    current = dict(current_input or case["current_input"])
    composer_meta = _as_mapping(candidate.get("composer_meta"))
    comment_text = str(candidate.get("comment_text") or "")
    shape = _comment_text_shape(comment_text)
    surface_quality = _surface_quality(case_id=case_id, case=case, comment_text=comment_text, shape=shape)
    public_contract = _public_contract(
        candidate=candidate,
        composer_meta=composer_meta,
        current_input=current,
        comment_text=comment_text,
    )
    grounding = _grounding_summary(composer_meta)
    gate = _gate_summary(
        comment_text=comment_text,
        current_input=current,
        composer_meta=composer_meta,
        run_visible_gate=run_visible_gate,
    )
    classification = _classify(
        candidate=candidate,
        public_contract=public_contract,
        surface_quality=surface_quality,
        gate=gate,
        grounding=grounding,
        shape=shape,
    )
    report = {
        "schema_version": PHASE17_PRODUCT_VISIBLE_FIXTURE_EVALUATION_SCHEMA_VERSION,
        "source_phase": PHASE17_PRODUCT_VISIBLE_FIXTURE_SOURCE_PHASE,
        "case_id": case_id,
        "candidate_status": _clean(candidate.get("status")),
        "composer_source": _clean(candidate.get("composer_source")),
        "classification": classification,
        "comment_text_shape": shape,
        "surface_quality": surface_quality,
        "gate": gate,
        "grounding": grounding,
        "public_contract": public_contract,
        "implementation_contract": _implementation_contract(candidate=candidate, composer_meta=composer_meta),
    }
    assert_phase17_product_visible_evaluation_meta_only(report)
    return report


def assert_phase17_product_visible_evaluation_meta_only(report: Mapping[str, Any]) -> None:
    """Keep evaluation output JSON-safe and free of raw/comment bodies."""

    forbidden_body_keys = {
        "comment_text",
        "observation_text",
        "reception_text",
        "raw_input",
        "raw_text",
        "memo",
        "memo_action",
        "current_input",
        "surface_text",
        "realized_text",
        "body",
        "text",
        "sentence",
        "sentences",
        "evidence_text",
    }
    assert not _contains_any_key(report, forbidden_body_keys), report
    json.dumps(report, ensure_ascii=False, sort_keys=True, default=str)


def assert_phase17_product_visible_fixture_passed(evaluation: Mapping[str, Any]) -> None:
    """Assert the future Phase17 product-visible target for one fixture."""

    errors: list[str] = []
    if evaluation.get("classification") != CLASSIFICATION_PASSED:
        errors.append(f"classification={evaluation.get('classification')}")
    if evaluation.get("candidate_status") != "generated":
        errors.append(f"candidate_status={evaluation.get('candidate_status')}")
    if evaluation.get("composer_source") != "ai_generated":
        errors.append(f"composer_source={evaluation.get('composer_source')}")

    shape = _as_mapping(evaluation.get("comment_text_shape"))
    for key in (
        "labels_present",
        "label_order_valid",
        "observation_section_non_empty",
        "reception_section_non_empty",
    ):
        if shape.get(key) is not True:
            errors.append(f"shape.{key}={shape.get(key)}")

    surface_quality = _as_mapping(evaluation.get("surface_quality"))
    if surface_quality.get("forbidden_fragments_present"):
        errors.append(f"forbidden_fragments_present={surface_quality.get('forbidden_fragments_present')}")
    if surface_quality.get("internal_role_label_leak") is True:
        errors.append("internal_role_label_leak=True")
    if surface_quality.get("relation_skeleton_leak") is True:
        errors.append("relation_skeleton_leak=True")
    if surface_quality.get("section_budget_valid") is not True:
        errors.append(f"section_budget={surface_quality.get('section_budget')}")
    if surface_quality.get("missing_surface_feature_families"):
        errors.append(f"missing_surface_feature_families={surface_quality.get('missing_surface_feature_families')}")

    gate = _as_mapping(evaluation.get("gate"))
    if gate.get("visible_gate_passed") is not True:
        errors.append(f"visible_gate={gate}")
    if gate.get("two_stage_gate_passed") is False:
        errors.append(f"two_stage_gate={gate}")

    public_contract = _as_mapping(evaluation.get("public_contract"))
    for key in (
        "public_response_key_added",
        "rn_visible_contract_changed",
        "raw_input_included",
        "comment_text_body_included",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
    ):
        if public_contract.get(key) is True:
            errors.append(f"public_contract.{key}=True")

    implementation_contract = _as_mapping(evaluation.get("implementation_contract"))
    for key in ("fixed_string_renderer_used", "external_ai_used", "local_llm_used"):
        if implementation_contract.get(key) is True:
            errors.append(f"implementation_contract.{key}=True")

    if errors:
        raise AssertionError(_compact_failure_message(evaluation, errors))


def assert_phase17_visible_gate_blocks_forbidden_surface(
    *,
    surface: str,
    expected_reason_any: Sequence[str],
    case_id: str = "self_blame_to_gentle_self_observation",
) -> Mapping[str, Any]:
    """Assert a synthetic bad two-stage surface is blocked by the visible gate."""

    from fixtures.emlis_ai_two_stage_reception_display_quality_cases import (
        phase13_two_stage_display_qa_case_by_id,
    )
    from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report

    case = two_stage_reception_case_by_id(case_id)
    qa_case = phase13_two_stage_display_qa_case_by_id(case_id)
    report = build_visible_surface_acceptance_gate_report(
        comment_text=surface,
        current_input=dict(case["current_input"]),
        composer_meta=_required_two_stage_composer_meta(),
        reception_mode=str(qa_case.get("reception_mode") or ""),
        rerender_allowed=False,
    )
    reasons = set(str(item) for item in report.get("rejection_reasons") or ())
    assert report["passed"] is False, report
    assert report["classification"] == "red", report
    assert report["action"] == "block", report
    assert any(reason in reasons for reason in expected_reason_any), report
    assert report.get("comment_text_body_included") is False, report
    assert report.get("raw_input_included") is False, report
    assert report.get("display_gate_relaxed") is False, report
    return report


def _classify(
    *,
    candidate: Mapping[str, Any],
    public_contract: Mapping[str, Any],
    surface_quality: Mapping[str, Any],
    gate: Mapping[str, Any],
    grounding: Mapping[str, Any],
    shape: Mapping[str, Any],
) -> str:
    if public_contract.get("public_meta_leak") is True:
        return CLASSIFICATION_PUBLIC_META_LEAK
    status = _clean(candidate.get("status"))
    if status != "generated":
        reasons = _all_reasons(candidate, grounding)
        if any("grounding" in reason for reason in reasons) or grounding.get("passed") is False:
            return CLASSIFICATION_UNAVAILABLE_GROUNDING
        return CLASSIFICATION_UNAVAILABLE_SURFACE
    if gate.get("visible_gate_passed") is False:
        return CLASSIFICATION_VISIBLE_GATE_REJECTED
    if not _shape_is_valid(shape):
        return CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG
    if surface_quality.get("forbidden_fragments_present"):
        return CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG
    if surface_quality.get("internal_role_label_leak") is True:
        return CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG
    if surface_quality.get("relation_skeleton_leak") is True:
        return CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG
    if surface_quality.get("section_budget_valid") is not True:
        return CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG
    if surface_quality.get("missing_surface_feature_families"):
        return CLASSIFICATION_PRODUCT_VISIBLE_SURFACE_NG
    return CLASSIFICATION_PASSED


def _comment_text_shape(comment_text: str) -> dict[str, Any]:
    split = split_two_stage_comment_text(comment_text)
    observation_marker = TWO_STAGE_LABEL_MARKERS["observation"]
    reception_marker = TWO_STAGE_LABEL_MARKERS["reception"]
    observation_text = str(split.get("observation_text") or "")
    reception_text = str(split.get("reception_text") or "")
    return {
        "labels_present": bool(split.get("labels_present"))
        and comment_text.count(observation_marker) == 1
        and comment_text.count(reception_marker) == 1,
        "label_order_valid": bool(split.get("label_order_valid")),
        "observation_label_count": comment_text.count(observation_marker),
        "reception_label_count": comment_text.count(reception_marker),
        "observation_section_non_empty": bool(_clean(observation_text)),
        "reception_section_non_empty": bool(_clean(reception_text)),
        "observation_sentence_count": _count_sentences(observation_text),
        "reception_sentence_count": _count_sentences(reception_text),
        "starts_with_observation_label": comment_text.startswith("見えたこと：\n"),
        "contains_reception_label_boundary": "\n\nEmlisから：\n" in comment_text,
    }


def _surface_quality(
    *,
    case_id: str,
    case: Mapping[str, Any],
    comment_text: str,
    shape: Mapping[str, Any],
) -> dict[str, Any]:
    case_forbidden = tuple(str(item) for item in case.get("forbidden_surface_fragments") or ())
    forbidden_fragments = tuple(dict.fromkeys((*PHASE17_PRODUCT_VISIBLE_FORBIDDEN_FRAGMENTS, *case_forbidden)))
    forbidden_hits = tuple(fragment for fragment in forbidden_fragments if fragment and _contains_fragment(comment_text, fragment))
    internal_role_hits = tuple(
        fragment for fragment in PHASE17_INTERNAL_ROLE_LABEL_FRAGMENTS if fragment and _contains_fragment(comment_text, fragment)
    )
    relation_skeleton_hits = tuple(
        fragment for fragment in PHASE17_RELATION_SKELETON_FRAGMENTS if fragment and _contains_fragment(comment_text, fragment)
    )
    section_budget = _section_budget(case_id=case_id, shape=shape)
    missing_feature_families = _missing_feature_families(case_id=case_id, comment_text=comment_text)
    return {
        "forbidden_fragments_present": list(forbidden_hits),
        "internal_role_label_leak": bool(internal_role_hits),
        "internal_role_label_fragments": list(internal_role_hits),
        "relation_skeleton_leak": bool(relation_skeleton_hits),
        "relation_skeleton_fragments": list(relation_skeleton_hits),
        "section_budget": section_budget,
        "section_budget_valid": section_budget["valid"],
        "missing_surface_feature_families": list(missing_feature_families),
        "surface_feature_families_present": not bool(missing_feature_families),
    }


def _missing_feature_families(*, case_id: str, comment_text: str) -> tuple[str, ...]:
    missing: list[str] = []
    for family_id, alternatives in PHASE17_FEATURE_FAMILY_ALTERNATIVES_BY_CASE_ID[case_id]:
        if not any(fragment and _contains_fragment(comment_text, fragment) for fragment in alternatives):
            missing.append(family_id)
    return tuple(missing)


def _section_budget(*, case_id: str, shape: Mapping[str, Any]) -> dict[str, Any]:
    expected = PHASE17_SECTION_BUDGET_BY_CASE_ID[case_id]
    observation_count = int(shape.get("observation_sentence_count") or 0)
    reception_count = int(shape.get("reception_sentence_count") or 0)
    valid = (
        bool(shape.get("labels_present"))
        and bool(shape.get("label_order_valid"))
        and expected["observation_min"] <= observation_count <= expected["observation_max"]
        and expected["reception_min"] <= reception_count <= expected["reception_max"]
    )
    return {
        "valid": valid,
        "observation_sentence_count": observation_count,
        "reception_sentence_count": reception_count,
        "expected": dict(expected),
    }


def _gate_summary(
    *,
    comment_text: str,
    current_input: Mapping[str, Any],
    composer_meta: Mapping[str, Any],
    run_visible_gate: bool,
) -> dict[str, Any]:
    if not run_visible_gate or not comment_text:
        return {
            "visible_gate_evaluated": False,
            "visible_gate_passed": None,
            "two_stage_gate_passed": None,
            "rejection_reasons": [],
            "two_stage_rejection_reasons": [],
        }
    from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report

    report = build_visible_surface_acceptance_gate_report(
        comment_text=comment_text,
        current_input=current_input,
        composer_meta=composer_meta,
        rerender_allowed=False,
    )
    two_stage = _as_mapping(report.get("two_stage_reception_gate"))
    return {
        "visible_gate_evaluated": True,
        "visible_gate_passed": report.get("passed"),
        "visible_gate_classification": report.get("classification"),
        "visible_gate_action": report.get("action"),
        "two_stage_gate_passed": two_stage.get("passed"),
        "two_stage_gate_required": report.get("two_stage_reception_gate_required")
        if "two_stage_reception_gate_required" in report
        else two_stage.get("two_stage_required"),
        "two_stage_gate_terminal_surface_block": report.get("two_stage_reception_gate_terminal_surface_block"),
        "rejection_reasons": list(report.get("rejection_reasons") or ()),
        "two_stage_rejection_reasons": list(two_stage.get("rejection_reasons") or ()),
    }


def _grounding_summary(meta: Mapping[str, Any]) -> dict[str, Any]:
    candidates = [
        _as_mapping(meta.get("final_grounding_report")),
        _as_mapping(meta.get("final_grounding")),
        _as_mapping(meta.get("initial_grounding_report")),
        _as_mapping(meta.get("initial_grounding")),
        _as_mapping(meta.get("complete_grounding_binding")),
    ]
    report = next((item for item in candidates if item.get("passed") is False), None)
    if report is None:
        report = next((item for item in candidates if item), {})
    rejection_reasons = _dedupe_strings(
        report.get("rejection_reasons")
        or report.get("fail_reasons")
        or report.get("product_quality_rejection_reasons")
        or ()
    )
    return {
        "passed": report.get("passed") if report else meta.get("grounding_passed"),
        "rejection_reasons": rejection_reasons,
        "unsupported_sentence_ids": _dedupe_strings(report.get("unsupported_sentence_ids") or ()),
        "relation_not_expressed_sentence_ids": _dedupe_strings(report.get("relation_not_expressed_sentence_ids") or ()),
        "binding_present": report.get("binding_present"),
        "binding_used": report.get("binding_used"),
        "binding_missing": report.get("binding_missing"),
        "binding_count": report.get("binding_count"),
        "expected_binding_count": report.get("expected_binding_count"),
        "binding_supported_sentence_count": report.get("binding_supported_sentence_count"),
        "binding_pass_rate": report.get("binding_pass_rate"),
        "binding_support_source": _clean(report.get("binding_support_source")),
        "release_blocker": report.get("release_blocker"),
        "grounding_gate_relaxed": bool(_any_true_recursive(report, ("grounding_gate_relaxed",))),
        "display_gate_relaxed": bool(_any_true_recursive(report, ("display_gate_relaxed",))),
        "raw_input_included": bool(_any_true_recursive(report, ("raw_input_included", "raw_text_included", "input_text_included"))),
    }


def _public_contract(
    *,
    candidate: Mapping[str, Any],
    composer_meta: Mapping[str, Any],
    current_input: Mapping[str, Any],
    comment_text: str,
) -> dict[str, Any]:
    raw_fragments = tuple(
        fragment
        for fragment in (
            str(current_input.get("memo") or ""),
            str(current_input.get("memo_action") or ""),
        )
        if len(_clean(fragment)) >= 12
    )
    prescan = _as_mapping(composer_meta.get("phase17_10_public_contract_prescan"))
    if prescan:
        raw_input_body_found = bool(prescan.get("raw_input_body_found_in_meta"))
        comment_body_found = bool(prescan.get("comment_text_body_found_in_meta"))
        body_flag_true = bool(prescan.get("body_flag_true"))
        contract_flag_true = bool(prescan.get("contract_flag_true"))
        gate_relaxed_true = bool(prescan.get("display_gate_relaxed") or prescan.get("grounding_gate_relaxed"))
    else:
        raw_input_body_found = any(_contains_text_recursive(composer_meta, fragment) for fragment in raw_fragments)
        comment_body_found = bool(
            comment_text and len(_clean(comment_text)) >= 12 and _contains_text_recursive(composer_meta, comment_text)
        )
        body_flag_true = _any_true_recursive(composer_meta, _BODY_LEAK_TRUE_FLAG_KEYS)
        contract_flag_true = _any_true_recursive(composer_meta, _PUBLIC_CONTRACT_TRUE_FLAG_KEYS)
        gate_relaxed_true = _any_true_recursive(composer_meta, _GATE_RELAXED_TRUE_FLAG_KEYS)
    return {
        "public_meta_leak": bool(raw_input_body_found or comment_body_found or body_flag_true),
        "raw_input_included": bool(
            raw_input_body_found
            or _any_true_recursive(composer_meta, ("raw_input_included", "raw_text_included", "input_text_included"))
        ),
        "comment_text_body_included": bool(
            comment_body_found
            or _any_true_recursive(composer_meta, ("comment_text_included", "comment_text_body_included", "surface_text_body_included"))
        ),
        "public_response_key_added": bool(
            contract_flag_true
            or candidate.get("public_response_key_added") is True
            or composer_meta.get("public_response_key_added") is True
        ),
        "rn_visible_contract_changed": bool(_any_true_recursive(composer_meta, ("rn_visible_contract_changed",))),
        "display_gate_relaxed": bool(gate_relaxed_true and _any_true_recursive(composer_meta, ("display_gate_relaxed", "gate_relaxed"))),
        "grounding_gate_relaxed": bool(_any_true_recursive(composer_meta, ("grounding_gate_relaxed",))),
        "raw_input_body_found_in_meta": raw_input_body_found,
        "comment_text_body_found_in_meta": comment_body_found,
    }


def _implementation_contract(*, candidate: Mapping[str, Any], composer_meta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "fixed_string_renderer_used": bool(
            candidate.get("fixed_string_renderer_used") is True
            or _any_true_recursive(composer_meta, ("fixed_string_renderer_used",))
        ),
        "fixed_sentence_template_used": bool(
            _any_true_recursive(composer_meta, ("fixed_sentence_template_used", "completed_reply_template_used"))
        ),
        "external_ai_used": bool(
            candidate.get("external_ai_used") is True or _any_true_recursive(composer_meta, ("external_ai_used",))
        ),
        "local_llm_used": bool(
            candidate.get("local_llm_used") is True or _any_true_recursive(composer_meta, ("local_llm_used",))
        ),
        "forbidden_impl_flag_true": bool(_any_true_recursive(composer_meta, _FORBIDDEN_IMPL_TRUE_FLAG_KEYS)),
    }


def _shape_is_valid(shape: Mapping[str, Any]) -> bool:
    return all(
        shape.get(key) is True
        for key in (
            "labels_present",
            "label_order_valid",
            "observation_section_non_empty",
            "reception_section_non_empty",
        )
    )


def _all_reasons(candidate: Mapping[str, Any], grounding: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(
        _dedupe_strings(
            [
                candidate.get("primary_reason"),
                *list(candidate.get("rejection_reasons") or ()),
                *list(grounding.get("rejection_reasons") or ()),
            ]
        )
    )


def _compact_failure_message(evaluation: Mapping[str, Any], errors: Iterable[str]) -> str:
    compact = {
        "case_id": evaluation.get("case_id"),
        "candidate_status": evaluation.get("candidate_status"),
        "composer_source": evaluation.get("composer_source"),
        "classification": evaluation.get("classification"),
        "errors": list(errors),
        "shape": evaluation.get("comment_text_shape"),
        "surface_quality": evaluation.get("surface_quality"),
        "gate": evaluation.get("gate"),
        "grounding": evaluation.get("grounding"),
        "public_contract": evaluation.get("public_contract"),
        "implementation_contract": evaluation.get("implementation_contract"),
    }
    return json.dumps(compact, ensure_ascii=False, sort_keys=True, default=str)


def _required_two_stage_composer_meta() -> dict[str, Any]:
    return {
        "composer_source": "ai_generated",
        "state_answer_composer_role_plan_connected": True,
        "state_answer_two_stage_display_required": True,
        "state_answer_section_labels_required": True,
        "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
        "composition_contract": {
            "two_stage_reception_surface_required": True,
            "section_labels_required": True,
            "expected_comment_text_shape": "labelled_two_stage_text",
        },
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
    }


def _count_sentences(text: str) -> int:
    cleaned = _clean(text)
    if not cleaned:
        return 0
    return len([chunk for chunk in (_clean(part) for part in _SENTENCE_SPLIT_RE.split(text)) if chunk])


def _contains_fragment(text: str, fragment: str) -> bool:
    if not text or not fragment:
        return False
    if _asciiish(fragment):
        return fragment.lower() in text.lower()
    return fragment in text


def _asciiish(value: str) -> bool:
    return all(ord(ch) < 128 for ch in value)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _dedupe_strings(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = _clean(value)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _safe_json_dump(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
    except Exception:
        return ""




def _phase17_10_release_memory() -> None:
    """Best-effort release for large test-only CompleteComposer graphs."""

    import gc

    gc.collect()
    try:
        import ctypes

        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


def _contains_text_recursive(value: Any, needle: str, *, _seen: set[int] | None = None) -> bool:
    """Return whether a body fragment is present in nested meta.

    This is test-only leak detection for public/meta boundaries.  It avoids
    serializing the whole composer meta into one large string, which keeps
    Phase17-10 regression runs under the local memory ceiling.
    """

    cleaned_needle = _clean(needle)
    if not cleaned_needle:
        return False
    seen = _seen if _seen is not None else set()
    value_id = id(value)
    if value_id in seen:
        return False
    if isinstance(value, (Mapping, list, tuple, set)):
        seen.add(value_id)
    if isinstance(value, Mapping):
        for item in value.values():
            if _contains_text_recursive(item, cleaned_needle, _seen=seen):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_recursive(item, cleaned_needle, _seen=seen) for item in value)
    if isinstance(value, str):
        return cleaned_needle in _clean(value)
    return False


def _any_true_recursive(value: Any, keys: Iterable[str]) -> bool:
    key_set = set(keys)
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in key_set and item is True:
                return True
            if isinstance(item, (Mapping, list, tuple)) and _any_true_recursive(item, key_set):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_any_true_recursive(item, key_set) for item in value)
    return False


def _contains_any_key(value: Any, keys: set[str]) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in keys:
                return True
            if isinstance(item, (Mapping, list, tuple)) and _contains_any_key(item, keys):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_contains_any_key(item, keys) for item in value)
    return False


# Backward-compatible aliases for earlier Phase17 test names.
build_phase17_complete_candidate_for_case = generate_phase17_two_stage_product_visible_candidate
evaluate_phase17_product_visible_fixture_candidate = lambda case_id, candidate: evaluate_phase17_two_stage_product_visible_candidate(case_id=case_id, candidate=candidate)
assert_phase17_product_visible_fixture_candidate = lambda case_id, candidate: assert_phase17_product_visible_fixture_passed(
    evaluate_phase17_two_stage_product_visible_candidate(case_id=case_id, candidate=candidate)
)

__all__ = [
    "CLASSIFICATION_PASSED",
    "PHASE17_PRODUCT_VISIBLE_CLASSIFICATIONS",
    "PHASE17_PRODUCT_VISIBLE_FIXTURE_EVALUATION_SCHEMA_VERSION",
    "PHASE17_PRODUCT_VISIBLE_FIXTURE_SOURCE_PHASE",
    "PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS",
    "assert_phase17_product_visible_evaluation_meta_only",
    "assert_phase17_product_visible_fixture_candidate",
    "assert_phase17_product_visible_fixture_passed",
    "assert_phase17_visible_gate_blocks_forbidden_surface",
    "build_phase17_complete_candidate_for_case",
    "build_phase17_two_stage_product_visible_payload",
    "evaluate_phase17_product_visible_fixture_candidate",
    "evaluate_phase17_two_stage_product_visible_candidate",
    "generate_phase17_two_stage_product_visible_candidate",
]
