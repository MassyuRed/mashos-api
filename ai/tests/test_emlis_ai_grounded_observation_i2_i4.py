# -*- coding: utf-8 -*-
from __future__ import annotations

"""Structural acceptance tests for GroundedObservation I2-I4.

These tests inspect the non-public canonical plan, SentencePlan, isolated
Surface, low-info/limited/self-denial policy integration, and plan-preserving
Recovery.  They intentionally do not assert one exact public reply body.
"""

import json
from pathlib import Path
import re
from typing import Any

import pytest

from emlis_ai_complete_focus_selector import build_complete_coverage_plan
from emlis_ai_complete_material_service import CompleteMaterialBundle, CompleteMaterialUnit
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    EvidenceSpanResolver,
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    build_grounded_observation_plan_shadow,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    GroundedSentencePlan,
    GroundedSurfaceResult,
    build_grounded_sentence_plan,
    build_grounded_surface_result,
    build_plan_preserving_recovery_sequence,
    validate_grounded_sentence_plan,
    validate_grounded_surface_result,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)

AI_ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROOT = AI_ROOT / "services" / "ai_inference"
_EVIDENCE_ID_RE = re.compile(r"^s[1-9][0-9]*$")
_RELATION_REALIZING_FUNCTIONS = {
    "observe_nuclei_with_relations",
    "observe_relation",
    "render_limited_scope",
    "render_limited_opposition",
}


def _case(case_id: str):
    return next(
        case
        for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES
        if case.case_id == case_id
    )


def _build(
    current_input: dict[str, Any],
) -> tuple[dict[str, Any], tuple[Any, ...], EvidenceSpanResolver, GroundedObservationPlan]:
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan_shadow(normalized, evidence_spans=spans)
    return normalized, spans, resolver, plan


def _surface(
    current_input: dict[str, Any],
    *,
    recovery_stage: str = "full",
) -> tuple[GroundedObservationPlan, EvidenceSpanResolver, GroundedSentencePlan, GroundedSurfaceResult]:
    _, _, resolver, plan = _build(current_input)
    sentence_plan = build_grounded_sentence_plan(
        plan,
        resolver,
        recovery_stage=recovery_stage,
    )
    result = build_grounded_surface_result(
        plan,
        resolver,
        recovery_stage=recovery_stage,
    )
    return plan, resolver, sentence_plan, result


def _text_nuclei(plan: GroundedObservationPlan):
    return tuple(
        nucleus
        for nucleus in plan.nuclei
        if set(nucleus.source_fields) & {"memo", "memo_action"}
        and nucleus.kind != "other_explicit"
    )


def _binding_evidence_ids(sentence_plan: GroundedSentencePlan) -> set[str]:
    return {
        span_id
        for line in sentence_plan.lines
        for span_id in line.binding.evidence_span_ids
    }


def _assert_body_free(payload: dict[str, Any], raw_values: tuple[str, ...]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for value in raw_values:
        text = str(value or "").strip()
        if text:
            assert text not in serialized


@pytest.mark.parametrize("case_id", ["A", "B", "C", "D"])
def test_i2_i4_known_inputs_build_valid_canonical_plan_and_bound_surface(case_id: str) -> None:
    case = _case(case_id)
    normalized, _, resolver, plan = _build(case.as_current_input())
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    result = build_grounded_surface_result(plan, resolver)

    assert validate_grounded_observation_plan(plan, resolver) == ()
    assert validate_grounded_sentence_plan(sentence_plan, plan, resolver) == ()
    assert validate_grounded_surface_result(result, sentence_plan, plan, resolver) == ()
    assert plan.response_plan.question_policy.allowed is False
    assert plan.surface_policy.content_source == "grounded_plan_only"
    assert plan.surface_policy.completed_semantic_template_allowed is False
    assert plan.surface_policy.example_cue_route_allowed is False
    assert plan.surface_policy.synthetic_evidence_id_allowed is False
    assert set(plan.coverage_requirements.required_nucleus_ids) <= {
        item.nucleus_id for item in plan.nuclei
    }
    assert set(plan.coverage_requirements.required_relation_ids) <= {
        item.relation_id for item in plan.relations
    }
    assert result.status == "generated"
    assert result.required_coverage_preserved is True
    assert "?" not in result.text and "？" not in result.text
    assert all(_EVIDENCE_ID_RE.fullmatch(item) for item in plan.referenced_evidence_span_ids)
    assert all(_EVIDENCE_ID_RE.fullmatch(item) for item in _binding_evidence_ids(sentence_plan))
    assert not resolver.unresolved_ids(_binding_evidence_ids(sentence_plan))
    _assert_body_free(
        plan.as_body_free_meta(),
        (str(normalized.get("memo") or ""), str(normalized.get("memo_action") or "")),
    )
    _assert_body_free(
        sentence_plan.as_body_free_meta(),
        (str(normalized.get("memo") or ""), str(normalized.get("memo_action") or "")),
    )
    _assert_body_free(
        result.as_body_free_meta(),
        (str(normalized.get("memo") or ""), str(normalized.get("memo_action") or "")),
    )


def test_i2_event_noun_replacement_preserves_structure_family() -> None:
    left = {
        "memo": "以前は植物の色を見ていた。でも今は建物の形も見るようになった。",
        "emotions": ["自己理解"],
    }
    right = {
        "memo": "以前は商品の傷を見ていた。でも今は道路の模様も見るようになった。",
        "emotions": ["自己理解"],
    }
    _, _, _, left_plan = _build(left)
    _, _, _, right_plan = _build(right)

    assert left_plan.input_profile.material_quality == right_plan.input_profile.material_quality
    assert [item.kind for item in _text_nuclei(left_plan)] == [
        item.kind for item in _text_nuclei(right_plan)
    ]
    assert [item.semantic_frame.time_scope for item in _text_nuclei(left_plan)] == [
        item.semantic_frame.time_scope for item in _text_nuclei(right_plan)
    ]
    assert [item.type for item in left_plan.relations] == [
        item.type for item in right_plan.relations
    ]
    assert [item.retention for item in left_plan.relations] == [
        item.retention for item in right_plan.relations
    ]


def test_i2_negation_changes_polarity_without_changing_source_contract() -> None:
    positive = {"memo": "今日は散歩できた。", "emotions": ["達成感"]}
    negative = {"memo": "今日は散歩できなかった。", "emotions": ["悲しみ"]}
    _, _, _, positive_plan = _build(positive)
    _, _, _, negative_plan = _build(negative)

    positive_nucleus = _text_nuclei(positive_plan)[0]
    negative_nucleus = _text_nuclei(negative_plan)[0]
    assert positive_nucleus.semantic_frame.polarity == "positive"
    assert negative_nucleus.semantic_frame.polarity == "negative"
    assert positive_nucleus.source_fields == negative_nucleus.source_fields == ("memo",)
    assert positive_nucleus.allowed_claim_scope == negative_nucleus.allowed_claim_scope
    assert "operator:negation" not in positive_nucleus.semantic_frame.attribute_codes
    assert "operator:negation" in negative_nucleus.semantic_frame.attribute_codes


def test_i2_label_changes_do_not_remove_or_replace_text_nuclei() -> None:
    memo = "今までは急いで決めていた。でも今日は一度立ち止まって考えられた。"
    _, _, left_resolver, left_plan = _build(
        {"memo": memo, "emotions": ["安心"], "category": ["生活"]}
    )
    _, _, right_resolver, right_plan = _build(
        {"memo": memo, "emotions": ["不安"], "category": ["仕事"]}
    )

    def text_signature(plan: GroundedObservationPlan, resolver: EvidenceSpanResolver):
        return tuple(
            (
                resolver.resolve(nucleus.source_span_ids[0]).raw_text,
                nucleus.kind,
                nucleus.semantic_frame.polarity,
                nucleus.retention,
            )
            for nucleus in _text_nuclei(plan)
        )

    assert text_signature(left_plan, left_resolver) == text_signature(right_plan, right_resolver)
    assert text_signature(left_plan, left_resolver)


def test_i3_every_required_relation_has_visible_semantic_binding() -> None:
    case = _case("B")
    plan, resolver, sentence_plan, result = _surface(case.as_current_input())
    relation_index = {item.relation_id: item for item in plan.relations}
    bound_lines = {
        relation_id: line
        for line in sentence_plan.lines
        for relation_id in line.binding.relation_ids
    }

    for relation_id in plan.coverage_requirements.required_relation_ids:
        relation = relation_index[relation_id]
        line = bound_lines[relation_id]
        assert line.surface_function in _RELATION_REALIZING_FUNCTIONS
        assert {relation.from_nucleus_id, relation.to_nucleus_id} <= set(
            line.binding.nucleus_ids
        )
        assert set(relation.source_span_ids) <= set(line.binding.evidence_span_ids)
    assert set(plan.coverage_requirements.required_relation_ids) == set(
        sentence_plan.covered_required_relation_ids
    )
    assert result.required_coverage_preserved is True


def test_i3_different_inputs_keep_different_source_bound_surface_content() -> None:
    first = {"memo": "今日は肩が重くて、何も始めたくない。", "emotions": ["疲労"]}
    second = {"memo": "今日は少し落ち着いて、本を開けた。", "emotions": ["安心"]}
    _, _, _, first_result = _surface(first)
    _, _, _, second_result = _surface(second)

    assert first_result.text != second_result.text
    assert "肩が重くて" in first_result.text
    assert "本を開けた" in second_result.text
    assert "肩が重くて" not in second_result.text
    assert "本を開けた" not in first_result.text


def test_i4_short_state_is_observation_first_and_never_event_question_escape() -> None:
    case = _case("A")
    plan, _, sentence_plan, result = _surface(case.as_current_input())
    roles = [line.binding.line_role for line in sentence_plan.lines]

    assert plan.input_profile.material_quality == "short_state_sufficient"
    assert plan.response_plan.response_kind == "short_state_observation"
    assert roles[0] == "primary_observation"
    assert "limited_scope" not in roles
    assert not any(line.binding.contains_question for line in sentence_plan.lines)
    assert "?" not in result.text and "？" not in result.text
    assert "何があった" not in result.text
    assert result.required_coverage_preserved is True


def test_i4_truly_limited_text_uses_same_plan_with_claim_scope_restriction() -> None:
    current_input = {
        "memo": "わからない",
        "emotions": ["不安"],
        "category": ["生活"],
    }
    plan, _, sentence_plan, result = _surface(current_input)

    assert plan.input_profile.material_quality == "limited_grounding"
    assert plan.response_plan.response_kind == "limited_grounding_observation"
    assert sentence_plan.lines[0].binding.line_role == "limited_scope"
    assert sentence_plan.lines[0].binding.claim_scope == "limited_grounding_no_event_completion"
    assert "no_event_completion" in sentence_plan.lines[0].binding.functional_atom_ids
    assert "no_reason_completion" in sentence_plan.lines[0].binding.functional_atom_ids
    assert "?" not in result.text and "？" not in result.text
    assert "何があった" not in result.text
    assert result.required_coverage_preserved is True


def test_i4_labels_only_is_allowed_only_without_text_nucleus() -> None:
    plan, _, sentence_plan, result = _surface(
        {"memo": "", "memo_action": "", "emotions": ["不安"], "category": ["生活"]}
    )

    assert plan.input_profile.text_presence == "labels_only"
    assert plan.input_profile.material_quality == "labels_only_limited"
    assert not _text_nuclei(plan)
    assert sentence_plan.lines[0].binding.claim_scope == "selected_labels_only"
    assert all(
        set(plan_nucleus.source_fields) <= {"emotion_details", "emotions", "category"}
        for plan_nucleus in plan.nuclei
    )
    assert result.required_coverage_preserved is True


def test_i4_self_denial_has_fact_boundary_grounded_opposition_and_human_follow() -> None:
    case = _case("D")
    plan, resolver, sentence_plan, result = _surface(case.as_current_input())
    roles = [line.binding.line_role for line in sentence_plan.lines]
    relation_index = {item.relation_id: item for item in plan.relations}
    opposition_line = next(
        line for line in sentence_plan.lines if line.binding.line_role == "limited_opposition"
    )
    follow_line = next(
        line
        for line in sentence_plan.lines
        if "human_follow:protective_counterdirection"
        in line.binding.functional_atom_ids
    )

    assert plan.input_profile.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert plan.safety_policy.identity_claim_must_not_be_accepted_as_fact is True
    assert plan.coverage_requirements.fact_boundary_required is True
    assert roles[:2] == ["fact_boundary", "limited_opposition"]
    assert roles == ["fact_boundary", "limited_opposition", "human_follow"]
    assert opposition_line.binding.relation_ids
    assert all(
        relation_index[item].retention == "required"
        and relation_index[item].grounding_kind == "user_stated_relation"
        for item in opposition_line.binding.relation_ids
    )
    assert "identity_claim_not_fact" in sentence_plan.lines[0].binding.functional_atom_ids
    assert "input_grounded_opposition" in opposition_line.binding.functional_atom_ids
    assert "evidence_bound_human_follow" in follow_line.binding.functional_atom_ids
    assert follow_line.binding.line_role == "human_follow"
    assert "human_follow_delivery:separate" in follow_line.binding.functional_atom_ids
    assert not resolver.unresolved_ids(opposition_line.binding.evidence_span_ids)
    assert not resolver.unresolved_ids(follow_line.binding.evidence_span_ids)
    assert sentence_plan.fact_boundary_covered is True
    assert sentence_plan.limited_opposition_covered is True
    assert sentence_plan.human_follow_covered is True
    assert result.required_coverage_preserved is True
    assert "あなた自身について確定した事実ではありません" in result.text
    assert "見えたこと：" in result.text
    assert "Emlisから：" in result.text
    assert "あなたは悪くない" not in result.text
    assert "あなたには価値がある" not in result.text


@pytest.mark.parametrize(
    "memo",
    [
        "自分は何をしても駄目だと思う。でもこの考え方をやめたい。",
        "私は役に立たないと思う。でも今日は助けを求められた。",
        "私は役に立たないと思ってしまう。ただ、今日は誰かに相談できた。",
    ],
)
def test_i4_self_denial_paraphrases_use_one_overlay_without_fixed_body(memo: str) -> None:
    plan, _, sentence_plan, result = _surface({"memo": memo, "emotions": ["悲しみ"]})
    roles = {line.binding.line_role for line in sentence_plan.lines}

    assert plan.input_profile.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert {"fact_boundary", "limited_opposition"} <= roles
    assert any(
        any(
            atom.startswith("human_follow:")
            for atom in line.binding.functional_atom_ids
        )
        for line in sentence_plan.lines
    )
    assert sentence_plan.limited_opposition_covered is True
    assert result.required_coverage_preserved is True
    assert memo not in sentence_plan.as_body_free_meta().values()


def test_i4_expression_difficulty_is_not_self_denial_false_positive() -> None:
    plan, _, sentence_plan, result = _surface(
        {"memo": "自分の気持ちをうまく言葉にできない。", "emotions": ["不安"]}
    )

    assert plan.input_profile.safety_kind == TRIAGE_SAFE_OBSERVATION
    assert plan.response_plan.response_kind == "short_state_observation"
    assert "fact_boundary" not in {line.binding.line_role for line in sentence_plan.lines}
    assert result.required_coverage_preserved is True


def test_i4_expression_difficulty_with_lower_bound_adverb_is_not_self_denial() -> None:
    plan, _, sentence_plan, result = _surface(
        {
            "memo": "自分の予定では最低でも15分は取りたいけれど、まだうまく表現できない。",
            "emotions": ["自己理解"],
        }
    )

    assert plan.input_profile.safety_kind == TRIAGE_SAFE_OBSERVATION
    assert "fact_boundary" not in {line.binding.line_role for line in sentence_plan.lines}
    assert result.required_coverage_preserved is True


def test_i4_damage_word_with_self_reference_is_not_self_denial() -> None:
    plan, _, sentence_plan, result = _surface(
        {
            "memo": (
                "自分のことを優先して整えられるのは嬉しい。"
                "ただ、現実と向き合うときのダメージが大きく、たまに逃げ出したくなる。"
            ),
            "emotions": ["喜び", "不安"],
        }
    )

    assert plan.input_profile.safety_kind == TRIAGE_SAFE_OBSERVATION
    assert "fact_boundary" not in {line.binding.line_role for line in sentence_plan.lines}
    assert result.required_coverage_preserved is True


def test_i4_recovery_stages_preserve_depth_and_required_meaning() -> None:
    case = _case("B")
    _, _, resolver, plan = _build(case.as_current_input())
    sequence = build_plan_preserving_recovery_sequence(plan, resolver)

    assert tuple(item.recovery_stage for item in sequence) == tuple(
        stage for stage in GROUND_RECOVERY_STAGES if stage != "minimal_grounded"
    )
    assert all(item.status == "generated" for item in sequence)
    assert all(item.required_coverage_preserved for item in sequence)
    assert all(item.required_nucleus_ids == sequence[0].required_nucleus_ids for item in sequence)
    assert all(item.required_relation_ids == sequence[0].required_relation_ids for item in sequence)
    assert all(not item.unresolved_evidence_span_ids for item in sequence)
    assert all(item.synthetic_evidence_id_used is False for item in sequence)
    assert [len(item.lines) for item in sequence] == sorted(
        (len(item.lines) for item in sequence),
        reverse=True,
    )

    full_plan = build_grounded_sentence_plan(plan, resolver, recovery_stage="full")
    optional_removed_plan = build_grounded_sentence_plan(
        plan,
        resolver,
        recovery_stage="optional_removed",
    )
    non_required_ids = {
        item.nucleus_id for item in plan.nuclei if item.retention != "required"
    }
    full_bound_ids = {
        nucleus_id
        for line in full_plan.lines
        for nucleus_id in line.binding.nucleus_ids
    }
    optional_removed_bound_ids = {
        nucleus_id
        for line in optional_removed_plan.lines
        for nucleus_id in line.binding.nucleus_ids
    }
    assert not non_required_ids & optional_removed_bound_ids
    # A large required set already fills the visible two-stage budget.  Full
    # recovery must not force a non-required item into that body merely to make
    # the next recovery stage look different; that recreates ledger-style
    # enumeration and overlong output.
    assert len(plan.coverage_requirements.required_nucleus_ids) > 5
    assert not non_required_ids & full_bound_ids

    for stage_result in sequence:
        stage_plan = build_grounded_sentence_plan(
            plan,
            resolver,
            recovery_stage=stage_result.recovery_stage,
        )
        evidence_ids = _binding_evidence_ids(stage_plan)
        assert evidence_ids
        assert all(_EVIDENCE_ID_RE.fullmatch(item) for item in evidence_ids)
        assert not resolver.unresolved_ids(evidence_ids)


def test_i4_source_question_marks_do_not_turn_observation_into_question() -> None:
    case = _case("B")
    _, _, sentence_plan, result = _surface(case.as_current_input())

    assert "？" in case.thought_text
    assert "?" not in result.text and "？" not in result.text
    assert not any(line.binding.contains_question for line in sentence_plan.lines)


@pytest.mark.parametrize(
    ("current_input", "expected_safety_kind"),
    [
        (
            {"memo": "安全が保てない。助けが必要。", "emotions": ["不安"]},
            TRIAGE_SAFETY_SUPPORT_REQUIRED,
        ),
        (
            {"memo": "もう消えたい。今日で終わりにしたい。", "emotions": ["悲しみ"]},
            TRIAGE_SAFETY_BLOCKED_EMERGENCY,
        ),
    ],
)
def test_i4_support_and_emergency_keep_separate_safety_surface_owner(
    current_input: dict[str, Any],
    expected_safety_kind: str,
) -> None:
    plan, _, sentence_plan, result = _surface(current_input)

    assert plan.input_profile.safety_kind == expected_safety_kind
    assert plan.safety_policy.requires_separate_safety_surface is True
    assert plan.safety_policy.grounded_plan_overlay_allowed is False
    assert plan.surface_policy.content_source == "separate_safety_owner"
    assert plan.surface_policy.generic_observation_surface_allowed is False
    assert sentence_plan.status == "separate_safety_owner"
    assert sentence_plan.coverage_delegated_to_separate_safety_owner is True
    assert sentence_plan.lines == ()
    assert result.status == "separate_safety_owner"
    assert result.lines == ()
    assert result.text == ""


def test_i5_canonical_modules_are_connected_without_importing_legacy_body_paths() -> None:
    plan_source = (SERVICE_ROOT / "emlis_ai_grounded_observation_plan.py").read_text(encoding="utf-8")
    surface_source = (SERVICE_ROOT / "emlis_ai_grounded_sentence_surface.py").read_text(encoding="utf-8")
    reply_source = (SERVICE_ROOT / "emlis_ai_reply_service.py").read_text(encoding="utf-8")
    combined = plan_source + "\n" + surface_source

    assert "from emlis_ai_grounded_observation_plan import" in reply_source
    assert "from emlis_ai_grounded_sentence_surface import" in reply_source
    for forbidden_module in (
        "emlis_ai_complete_initial_surface_recomposition",
        "emlis_ai_limited_grounding_reception_surface",
        "emlis_ai_low_information_observation_composer",
        "emlis_ai_self_denial_safe_state_answer",
        "emlis_reception_assistance_dictionary",
    ):
        assert f"import {forbidden_module}" not in combined
        assert f"from {forbidden_module} import" not in combined

    for fixture_body in (
        _case("A").thought_text,
        _case("C").thought_text,
        _case("D").thought_text,
        _case("A").legacy_visible_body,
        _case("B").legacy_visible_body,
        _case("C").legacy_visible_body,
        _case("D").legacy_visible_body,
    ):
        assert fixture_body not in combined


def test_i1_5_complete_material_to_focus_preserves_canonical_source_refs() -> None:
    material = CompleteMaterialUnit(
        material_id="cm1",
        phrase_unit_id="cpu1",
        evidence_span_id="s1",
        material_text="入力にある状態",
        role="state_awareness",
        relation_type="coexistence",
        canonical_nucleus_ids=("nucleus:1", "nucleus:2"),
        canonical_relation_ids=("relation:1",),
        source_evidence_span_ids=("s1", "s2"),
        source_anchor={"source_anchor_present": True, "source_field": "memo"},
    )
    bundle = CompleteMaterialBundle(materials=(material,), coverage_group="short_daily")
    plan = build_complete_coverage_plan(material_bundle=bundle)
    focus = plan.focus_items[0]
    seed = plan.as_sentence_plan_seed()

    assert focus.canonical_nucleus_ids == ("nucleus:1", "nucleus:2")
    assert focus.canonical_relation_ids == ("relation:1",)
    assert focus.source_evidence_span_ids == ("s1", "s2")
    assert plan.canonical_nucleus_ids == ("nucleus:1", "nucleus:2")
    assert plan.canonical_relation_ids == ("relation:1",)
    assert plan.source_evidence_span_ids == ("s1", "s2")
    assert seed["canonical_nucleus_ids"] == ["nucleus:1", "nucleus:2"]
    assert seed["canonical_relation_ids"] == ["relation:1"]
    assert seed["source_evidence_span_ids"] == ["s1", "s2"]


def test_i2_static_withdrawal_removes_fixture_semantic_owners() -> None:
    material_source = (SERVICE_ROOT / "emlis_ai_input_material_bundle.py").read_text(encoding="utf-8")
    meaning_source = (SERVICE_ROOT / "emlis_ai_input_meaning_block_service.py").read_text(encoding="utf-8")
    safety_source = (SERVICE_ROOT / "emlis_ai_safety_triage.py").read_text(encoding="utf-8")

    assert "_SEMANTIC_MATERIAL_PATTERNS" not in material_source
    assert "_GENERIC_RELATION_MATERIAL_PATTERNS" not in material_source
    assert "SEMANTIC_RELATION_MATERIAL_GENERATION_DISABLED" in material_source
    assert "_ROLE_DEFINITIONS" not in meaning_source
    assert "self_and_others_happiness_toward_unreachable_wish" not in meaning_source
    assert "_SELF_DENIAL_HARD_MARKER_RE" not in safety_source
    assert "自分を傷つけてるのは私" not in safety_source
    assert "いい事なんて絶対にない" not in safety_source
