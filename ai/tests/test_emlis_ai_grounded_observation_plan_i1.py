# -*- coding: utf-8 -*-
from __future__ import annotations

"""I1 guards for the non-public canonical GroundedObservationPlan.

These tests deliberately stop before SentencePlan/Surface integration. They
verify that the existing request-local Evidence Ledger and upstream semantic
objects can be adapted into one body-free plan without changing the public
reply path.
"""

from dataclasses import replace
import json
from pathlib import Path
import re
from typing import Callable

import pytest

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    EvidenceLedgerResolutionError,
    build_evidence_ledger,
    build_evidence_span_resolver,
    validate_evidence_ledger,
)
from emlis_ai_grounded_observation_plan import (
    GROUND_OBSERVATION_PLAN_GENERATION_PATH,
    GroundedObservationPlan,
    build_grounded_observation_plan_shadow,
    validate_grounded_observation_plan,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)
from emlis_ai_types import ObservationClaim, PerspectiveReport, RelationEdge

_CANONICAL_EVIDENCE_ID_RE = re.compile(r"^s[1-9]\d*$")
_AI_INFERENCE_ROOT = Path(__file__).resolve().parents[1] / "services" / "ai_inference"


def _case(case_id: str):
    return next(case for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES if case.case_id == case_id)


def _spans_and_resolver(current_input: dict[str, object]):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    return normalized, spans, resolver


def _nucleus_by_span(plan: GroundedObservationPlan) -> dict[str, object]:
    return {
        span_id: nucleus
        for nucleus in plan.nuclei
        for span_id in nucleus.source_span_ids
    }


def _span_id_containing(spans, text: str, *, source_field: str | None = None) -> str:
    for span in spans:
        if source_field is not None and span.source_field != source_field:
            continue
        if text in span.raw_text:
            return span.span_id
    raise AssertionError(f"span_not_found:{text}")


def _assert_body_free_meta(plan: GroundedObservationPlan, forbidden_texts: tuple[str, ...]) -> None:
    meta = plan.as_body_free_meta()
    payload = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_included"] is False
    assert meta["surface_text_included"] is False
    assert meta["comment_text_generated"] is False
    assert meta["surface_connected"] is True
    assert meta["public_reply_path_connected"] is True
    assert meta["public_contract_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False
    for text in forbidden_texts:
        if text:
            assert text not in payload
    forbidden_keys = {"raw_text", "comment_text", "surface_text", "thought_text", "action_text"}

    def visit(value) -> None:
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(meta)


def test_i1_evidence_resolver_accepts_existing_sequential_ledger_and_emits_body_free_report() -> None:
    current_input = {
        "memo": "昨日は立ち止まっていた。でも今日は一歩動けた。",
        "memo_action": "変化を書き留めた。",
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    normalized, spans, resolver = _spans_and_resolver(current_input)
    report = validate_evidence_ledger(spans, current_input=normalized)

    assert report.valid is True
    assert report.issue_codes == ()
    assert report.canonical_span_ids == tuple(span.span_id for span in spans)
    assert resolver.span_ids == report.canonical_span_ids
    assert resolver.resolve("s1") == spans[0]
    assert resolver.resolve_many(("s1", "s2")) == spans[:2]
    assert resolver.unresolved_ids(("s1", "p5_visible", "p5_visible")) == ("p5_visible",)
    assert resolver.source_fields_for(("s1",)) == ("memo",)
    with pytest.raises(EvidenceLedgerResolutionError, match="unresolved_evidence_span_id"):
        resolver.resolve("p5_visible")

    report_meta = report.as_body_free_meta()
    assert report_meta["raw_user_text_included"] is False
    assert current_input["memo"] not in json.dumps(report_meta, ensure_ascii=False)


InvalidLedgerMutation = Callable[[tuple], tuple]


def _mutate_synthetic_id(spans: tuple) -> tuple:
    return (replace(spans[0], span_id="p5_visible"), *spans[1:])


def _mutate_nonsequential_ids(spans: tuple) -> tuple:
    return tuple(replace(span, span_id=f"s{index + 2}") for index, span in enumerate(spans))


def _mutate_duplicate_id(spans: tuple) -> tuple:
    return (spans[0], replace(spans[1], span_id=spans[0].span_id), *spans[2:])


def _mutate_source_slice(spans: tuple) -> tuple:
    return (replace(spans[0], raw_text="source mismatch"), *spans[1:])


@pytest.mark.parametrize(
    ("mutation", "expected_issue"),
    [
        (_mutate_synthetic_id, "noncanonical_span_id"),
        (_mutate_nonsequential_ids, "nonsequential_span_id"),
        (_mutate_duplicate_id, "duplicate_span_id"),
        (_mutate_source_slice, "source_slice_mismatch"),
    ],
)
def test_i1_evidence_resolver_rejects_noncanonical_or_unresolvable_ledgers(
    mutation: InvalidLedgerMutation,
    expected_issue: str,
) -> None:
    current_input = {
        "memo": "今は少し疲れている。でも今日はここまで進めた。",
        "memo_action": "短く記録した。",
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    invalid = mutation(spans)
    report = validate_evidence_ledger(invalid, current_input=normalized)

    assert report.valid is False
    assert expected_issue in report.issue_codes
    with pytest.raises(EvidenceLedgerResolutionError, match="invalid_evidence_ledger"):
        build_evidence_span_resolver(invalid, current_input=normalized)


def test_i1_adapter_preserves_existing_claim_and_relation_identity() -> None:
    current_input = {
        "memo": "昨日は立ち止まっていた。でも今日は一歩動けた。",
        "memo_action": "",
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    normalized, spans, resolver = _spans_and_resolver(current_input)
    text_spans = [
        span for span in spans
        if span.source_field == "memo" and span.detected_type != "relation_marker"
    ]
    assert len(text_spans) >= 2
    before_id, after_id = text_spans[0].span_id, text_spans[-1].span_id
    before_claim = ObservationClaim(
        claim_id="custom.c1",
        claim_type="state",
        subject="before",
        evidence_span_ids=[before_id],
        confidence=0.91,
    )
    after_claim = ObservationClaim(
        claim_id="custom.c2",
        claim_type="change",
        subject="after",
        evidence_span_ids=[after_id],
        confidence=0.92,
    )
    edge = RelationEdge(
        edge_id="custom.r1",
        from_claim_id=before_claim.claim_id,
        to_claim_id=after_claim.claim_id,
        relation_type="explicit_transition",
        evidence_span_ids=[before_id, after_id],
        confidence=0.88,
    )
    report = PerspectiveReport(
        observer_id="custom_observer",
        viewpoint="existing_upstream_identity",
        claims=[before_claim, after_claim],
        relations=[edge],
        evidence_span_ids=[span.span_id for span in spans],
        confidence=0.9,
    )

    plan = build_grounded_observation_plan_shadow(
        normalized,
        evidence_spans=spans,
        reports=[report],
    )
    by_span = _nucleus_by_span(plan)
    assert "custom.c1" in by_span[before_id].source_claim_ids
    assert "custom.c2" in by_span[after_id].source_claim_ids
    mapped = next(relation for relation in plan.relations if "custom.r1" in relation.source_relation_ids)
    assert mapped.type == "contrast"
    assert mapped.from_nucleus_id == by_span[before_id].nucleus_id
    assert mapped.to_nucleus_id == by_span[after_id].nucleus_id
    assert mapped.source_span_ids == (before_id, after_id)
    assert mapped.grounding_kind == "user_stated_relation"
    assert validate_grounded_observation_plan(plan, resolver) == ()


@pytest.mark.parametrize("case_id", ["A", "B", "C", "D"])
def test_i1_known_regression_inputs_build_valid_body_free_shadow_plans(case_id: str) -> None:
    case = _case(case_id)
    current_input = case.as_current_input()
    normalized, spans, resolver = _spans_and_resolver(current_input)
    plan = build_grounded_observation_plan_shadow(
        normalized,
        evidence_spans=spans,
    )

    assert plan.generation_path == GROUND_OBSERVATION_PLAN_GENERATION_PATH
    assert plan.generation_path == "grounded_observation_plan_canonical_v1"
    assert plan.input_profile.nucleus_count == len(plan.nuclei)
    assert plan.input_profile.relation_count == len(plan.relations)
    assert plan.evidence_ledger_validation.valid is True
    assert validate_grounded_observation_plan(plan, resolver) == ()
    assert plan.response_plan.question_policy.allowed is False
    assert plan.surface_policy.completed_semantic_template_allowed is False
    assert plan.surface_policy.example_cue_route_allowed is False
    assert plan.surface_policy.synthetic_evidence_id_allowed is False
    assert plan.referenced_evidence_span_ids
    assert set(plan.referenced_evidence_span_ids) <= set(resolver.span_ids)
    assert all(_CANONICAL_EVIDENCE_ID_RE.fullmatch(span_id) for span_id in plan.referenced_evidence_span_ids)
    assert all(
        _CANONICAL_EVIDENCE_ID_RE.fullmatch(span_id)
        for nucleus in plan.nuclei
        for span_id in nucleus.source_span_ids
    )
    assert all(
        resolver.source_fields_for(nucleus.source_span_ids) == nucleus.source_fields
        for nucleus in plan.nuclei
    )
    _assert_body_free_meta(
        plan,
        (
            case.thought_text,
            case.action_text,
            case.legacy_visible_body,
        ),
    )


def test_i1_long_input_keeps_shift_action_and_change_as_distinct_grounded_items() -> None:
    case = _case("B")
    current_input = case.as_current_input()
    normalized, spans, resolver = _spans_and_resolver(current_input)
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)
    by_span = _nucleus_by_span(plan)

    shift_span_id = _span_id_containing(spans, "疑問の対象が物", source_field="memo")
    shift_nucleus = by_span[shift_span_id]
    action_nuclei = [
        item for item in plan.nuclei
        if item.kind == "action" and "memo_action" in item.source_fields
    ]
    change_nuclei = [
        item for item in plan.nuclei
        if item.kind == "change" and "memo" in item.source_fields
    ]

    assert plan.input_profile.semantic_complexity == "long_arc"
    assert shift_nucleus.grounding_kind == "user_stated_relation"
    assert shift_nucleus.source_claim_ids
    assert action_nuclei
    assert change_nuclei
    assert len({shift_nucleus.nucleus_id, action_nuclei[0].nucleus_id, change_nuclei[0].nucleus_id}) == 3
    required_nuclei = {
        item.nucleus_id: item for item in plan.nuclei
        if item.nucleus_id in plan.response_plan.required_nucleus_ids
    }
    assert any("memo" in item.source_fields for item in required_nuclei.values())
    assert any("memo_action" in item.source_fields for item in required_nuclei.values())
    assert shift_nucleus.nucleus_id in required_nuclei
    # The shift clause contains both sides of its embedded marker in one
    # Evidence span.  R3 keeps that span required, but must not invent a
    # cross-span endpoint merely to materialize a Relation object.
    assert not any(
        f"evidence_relation_marker:{shift_span_id}" in relation.source_relation_ids
        for relation in plan.relations
    )
    assert any(
        "source_field_transition:memo_to_memo_action" in relation.source_relation_ids
        for relation in plan.relations
    )
    assert validate_grounded_observation_plan(plan, resolver) == ()


def test_i1_unseen_vocabulary_is_preserved_as_evidence_references_without_case_route() -> None:
    current_input = {
        "memo": "陶芸の釉薬が想定より濁った。でも焼成温度を記録したことで、次に比べられる材料は残せた。",
        "memo_action": "窯の温度と釉薬の厚みを別々に記録した。",
        "emotions": ["自己理解"],
        "category": ["創作"],
    }
    normalized, spans, resolver = _spans_and_resolver(current_input)
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)
    text_span_ids = {
        span.span_id for span in spans if span.source_field in {"memo", "memo_action"}
    }
    planned_text_span_ids = {
        span_id
        for nucleus in plan.nuclei
        for span_id in nucleus.source_span_ids
        if resolver.resolve(span_id).source_field in {"memo", "memo_action"}
    }

    assert text_span_ids == planned_text_span_ids
    assert plan.input_profile.text_presence == "text_present"
    assert plan.surface_policy.example_cue_route_allowed is False
    assert plan.surface_policy.completed_semantic_template_allowed is False
    assert any("memo_action" in nucleus.source_fields for nucleus in plan.nuclei)
    assert plan.relations
    assert validate_grounded_observation_plan(plan, resolver) == ()
    _assert_body_free_meta(
        plan,
        (current_input["memo"], current_input["memo_action"]),
    )


def test_i1_self_denial_uses_grounded_overlay_and_requires_fact_boundary() -> None:
    case = _case("D")
    normalized, spans, resolver = _spans_and_resolver(case.as_current_input())
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)
    required = {
        item.nucleus_id: item
        for item in plan.nuclei
        if item.nucleus_id in plan.response_plan.required_nucleus_ids
    }

    assert plan.input_profile.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert plan.response_plan.response_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert plan.surface_policy.content_source == "grounded_plan_only"
    assert plan.surface_policy.generic_observation_surface_allowed is True
    assert plan.safety_policy.grounded_plan_overlay_allowed is True
    assert plan.safety_policy.requires_separate_safety_surface is False
    assert plan.safety_policy.identity_claim_must_not_be_accepted_as_fact is True
    assert plan.coverage_requirements.fact_boundary_required is True
    assert plan.coverage_requirements.human_follow_required is True
    fact_boundary_ids = set(plan.response_plan.fact_boundary_nucleus_ids)
    follow_ids = set(plan.response_plan.human_follow_target_ids)
    required_ids = set(plan.response_plan.required_nucleus_ids)
    assert fact_boundary_ids
    assert fact_boundary_ids <= required_ids
    assert {required[item].kind for item in fact_boundary_ids} == {"self_evaluation"}
    assert follow_ids
    assert follow_ids <= required_ids
    assert {required[item].kind for item in follow_ids} & {"conclusion", "change", "value"}
    assert any(
        relation.type == "continuation_or_refusal"
        and relation.relation_id in plan.coverage_requirements.required_relation_ids
        for relation in plan.relations
    )
    assert {item.kind for item in required.values()} >= {"self_evaluation", "conclusion"}
    assert validate_grounded_observation_plan(plan, resolver) == ()


@pytest.mark.parametrize(
    (
        "current_input",
        "expected_kind",
        "expected_content_source",
        "generic_surface_allowed",
        "overlay_allowed",
        "human_follow_required",
        "fact_boundary_required",
    ),
    [
        (
            {"memo": "今日は少し落ち着いて、部屋を片付けた。", "emotions": ["平穏"]},
            TRIAGE_SAFE_OBSERVATION,
            "grounded_plan_only",
            True,
            True,
            True,
            False,
        ),
        (
            {"memo": "自分を責め続けても良いことはない。もうこの流れは続けたくない。", "emotions": ["悲しみ"]},
            TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
            "grounded_plan_only",
            True,
            True,
            True,
            True,
        ),
        (
            {"memo": "安全が保てない。助けが必要。", "emotions": ["不安"]},
            TRIAGE_SAFETY_SUPPORT_REQUIRED,
            "separate_safety_owner",
            False,
            False,
            False,
            True,
        ),
        (
            {"memo": "もう消えたい。今日で終わりにしたい。", "emotions": ["悲しみ"]},
            TRIAGE_SAFETY_BLOCKED_EMERGENCY,
            "separate_safety_owner",
            False,
            False,
            False,
            True,
        ),
    ],
)
def test_i1_safety_perimeter_keeps_four_routes_separate(
    current_input: dict[str, object],
    expected_kind: str,
    expected_content_source: str,
    generic_surface_allowed: bool,
    overlay_allowed: bool,
    human_follow_required: bool,
    fact_boundary_required: bool,
) -> None:
    normalized, spans, resolver = _spans_and_resolver(current_input)
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)

    assert plan.input_profile.safety_kind == expected_kind
    assert plan.safety_policy.safety_kind == expected_kind
    assert plan.surface_policy.content_source == expected_content_source
    assert plan.surface_policy.generic_observation_surface_allowed is generic_surface_allowed
    assert plan.safety_policy.grounded_plan_overlay_allowed is overlay_allowed
    assert plan.coverage_requirements.human_follow_required is human_follow_required
    assert plan.coverage_requirements.fact_boundary_required is fact_boundary_required
    if expected_kind in {TRIAGE_SAFETY_SUPPORT_REQUIRED, TRIAGE_SAFETY_BLOCKED_EMERGENCY}:
        assert plan.response_plan.surface_shape == "separate_safety_surface"
        assert plan.safety_policy.requires_separate_safety_surface is True
    else:
        assert plan.response_plan.surface_shape != "separate_safety_surface"
    assert plan.safety_policy.emergency_path_must_not_be_overridden is True
    assert validate_grounded_observation_plan(plan, resolver) == ()


@pytest.mark.parametrize(
    ("current_input", "expected_presence", "expected_quality", "expected_count_kind"),
    [
        (
            {"memo": "", "memo_action": "", "emotions": ["不安"], "category": ["生活"]},
            "labels_only",
            "labels_only_limited",
            "positive",
        ),
        ({}, "empty", "empty", "zero"),
    ],
)
def test_i1_labels_only_and_empty_inputs_remain_bounded_without_invented_text_nuclei(
    current_input: dict[str, object],
    expected_presence: str,
    expected_quality: str,
    expected_count_kind: str,
) -> None:
    normalized, spans, resolver = _spans_and_resolver(current_input)
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)

    assert plan.input_profile.text_presence == expected_presence
    assert plan.input_profile.material_quality == expected_quality
    assert not any(
        field in {"memo", "memo_action"}
        for nucleus in plan.nuclei
        for field in nucleus.source_fields
    )
    if expected_count_kind == "positive":
        assert plan.nuclei
        assert all(nucleus.allowed_claim_scope == "selected_label_only" for nucleus in plan.nuclei)
    else:
        assert plan.nuclei == ()
        assert plan.referenced_evidence_span_ids == ()
    assert plan.response_plan.question_policy.allowed is False
    assert validate_grounded_observation_plan(plan, resolver) == ()


def test_i1_plan_validator_rejects_synthetic_reference_and_surface_policy_drift() -> None:
    current_input = {"memo": "今日は少し疲れた。", "emotions": ["悲しみ"]}
    normalized, spans, resolver = _spans_and_resolver(current_input)
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)
    bad_nucleus = replace(plan.nuclei[0], source_span_ids=("p5_visible",))
    bad_surface = replace(
        plan.surface_policy,
        completed_semantic_template_allowed=True,
        example_cue_route_allowed=True,
        synthetic_evidence_id_allowed=True,
    )
    bad_question = replace(plan.response_plan.question_policy, allowed=True)
    assert plan.unknown_boundaries
    bad_unknown = replace(plan.unknown_boundaries[0], dimension="何があったか")
    mutated = replace(
        plan,
        nuclei=(bad_nucleus, *plan.nuclei[1:]),
        unknown_boundaries=(bad_unknown, *plan.unknown_boundaries[1:]),
        response_plan=replace(plan.response_plan, question_policy=bad_question),
        surface_policy=bad_surface,
    )

    issues = validate_grounded_observation_plan(mutated, resolver)
    assert any("invalid_evidence_id:p5_visible" in issue for issue in issues)
    assert any("unresolved_evidence:p5_visible" in issue for issue in issues)
    assert "p7_question_policy_must_be_false" in issues
    assert "completed_semantic_template_must_be_false" in issues
    assert "example_cue_route_must_be_false" in issues
    assert "synthetic_evidence_id_must_be_false" in issues
    assert "referenced_evidence_span_ids_mismatch" in issues
    assert any("unknown_boundary:unknown:u1_non_body_free_code" == issue for issue in issues)


def test_i5_canonical_module_is_connected_once_without_owning_comment_text() -> None:
    reply_source = (_AI_INFERENCE_ROOT / "emlis_ai_reply_service.py").read_text(encoding="utf-8")
    plan_source = (_AI_INFERENCE_ROOT / "emlis_ai_grounded_observation_plan.py").read_text(encoding="utf-8")

    assert "from emlis_ai_grounded_observation_plan import" in reply_source
    assert "build_grounded_observation_plan(" in reply_source
    assert "build_grounded_observation_plan_shadow" not in reply_source
    assert "comment_text" not in {
        field_name
        for field_name in GroundedObservationPlan.__dataclass_fields__
    }
    assert "def build_grounded_observation_plan(" in plan_source
    assert "Generic Surface Realizer" not in plan_source
    assert "grounded_observation_plan_canonical_v1" in plan_source
