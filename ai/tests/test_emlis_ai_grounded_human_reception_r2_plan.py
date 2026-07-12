# -*- coding: utf-8 -*-
from __future__ import annotations

"""R2 unit and body-free contract tests for GroundedHumanReceptionPlan."""

from dataclasses import replace
import json
from pathlib import Path

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import (
    GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION,
    GroundedHumanReceptionPlan,
    build_grounded_observation_plan,
    map_grounded_human_follow_role_to_reception_act,
    validate_grounded_human_reception_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)


_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)


def _load_fixture():
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _plan_and_resolver(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    return plan, resolver


def _reception(current_input) -> GroundedHumanReceptionPlan:
    plan = _plan_and_resolver(current_input)[0]
    reception = plan.response_plan.human_reception_plan
    assert reception is not None
    return reception


def test_r2_role_to_act_mapping_is_complete_and_general() -> None:
    expected = {
        "integrated_current_state": "stay_with_current_burden",
        "burden_expression": "stay_with_current_burden",
        "concrete_effort": "honor_concrete_effort",
        "retained_intention": "protect_retained_intention",
        "valued_change": "recognize_lived_change",
        "help_seeking_preserved": "hold_help_seeking",
        "protective_counterdirection": "bounded_counter_self_denial",
    }
    assert {
        role: map_grounded_human_follow_role_to_reception_act(role)
        for role in expected
    } == expected


def test_r2_exact8_builds_expected_body_free_reception_acts_without_case_route() -> None:
    expected = {
        "A": ("stay_with_current_burden", None, "quiet_presence", "implicit_emlis"),
        "B": ("recognize_lived_change", None, "warm_recognition", "implicit_emlis"),
        "C": ("protect_retained_intention", None, "gentle_respect", "implicit_emlis"),
        "D": (
            "bounded_counter_self_denial",
            None,
            "bounded_disagreement",
            "explicit_emlis",
        ),
        "I6-S03": ("stay_with_current_burden", None, "quiet_presence", "implicit_emlis"),
        "I6-L03": ("honor_concrete_effort", None, "warm_recognition", "implicit_emlis"),
        "I6-C01": ("honor_concrete_effort", None, "warm_recognition", "implicit_emlis"),
        "I6-D02": (
            "hold_help_seeking",
            "bounded_counter_self_denial",
            "protective_presence",
            "explicit_emlis",
        ),
    }
    for case in _load_fixture()["cases"]:
        plan, resolver = _plan_and_resolver(case["exact_current_input"])
        reception = plan.response_plan.human_reception_plan
        assert reception is not None
        assert (
            reception.primary_reception_act,
            reception.secondary_reception_act,
            reception.stance,
            reception.speaker_presence,
        ) == expected[case["case_id"]]
        assert reception.schema_version == GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION
        assert reception.required is True
        assert reception.target_nucleus_ids == plan.response_plan.human_follow_target_ids
        assert set(reception.target_nucleus_ids) <= set(reception.observation_owned_nucleus_ids)
        assert reception.source_evidence_span_ids
        assert not resolver.unresolved_ids(reception.source_evidence_span_ids)
        assert reception.quote_policy.mode == "no_full_quote_replay"
        assert reception.quote_policy.max_anchor_count <= 1
        assert reception.quote_policy.max_anchor_visible_chars <= 20
        assert reception.sentence_policy.min_sentences == 1
        assert reception.sentence_policy.max_sentences <= 2
        assert validate_grounded_observation_plan(plan, resolver) == ()


def test_r2_short_state_and_self_denial_overrides_keep_safety_boundaries() -> None:
    cases = {case["case_id"]: case for case in _load_fixture()["cases"]}
    short = _reception(cases["I6-S03"]["exact_current_input"])
    assert short.primary_reception_act == "stay_with_current_burden"
    assert short.reference_mode == "anaphoric_first"
    assert short.sentence_policy.max_sentences == 1
    assert short.distinctness_policy.policy_explanation_allowed is False
    assert "internal_policy_explanation" in short.forbidden_surface_codes

    denial_plan = _plan_and_resolver(cases["D"]["exact_current_input"])[0]
    denial = denial_plan.response_plan.human_reception_plan
    assert denial is not None
    assert denial_plan.safety_policy.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert denial.primary_reception_act == "bounded_counter_self_denial"
    assert denial.reference_mode == "explicit_emlis_counterposition"
    assert {
        "felt_state_is_real",
        "identity_claim_is_not_accepted",
        "counterposition_requires_input_evidence",
    } <= set(denial.safety_modifier_codes)

    help_plan = _plan_and_resolver(cases["I6-D02"]["exact_current_input"])[0]
    help_reception = help_plan.response_plan.human_reception_plan
    assert help_reception is not None
    assert help_reception.primary_reception_act == "hold_help_seeking"
    assert help_reception.secondary_reception_act == "bounded_counter_self_denial"
    assert help_reception.speaker_presence == "explicit_emlis"


def test_r2_unseen_inputs_and_case_id_metamorphosis_do_not_change_plan() -> None:
    unseen_inputs = (
        {
            "memo": "肩の奥が重い感じがする。",
            "memo_action": "",
            "emotions": ["不安"],
            "category": ["健康"],
        },
        {
            "memo": (
                "前の案は説明が多すぎると感じた。ただ残したい図は一つある。"
                "まだ順番は決めきれていない。次は図から組み直したい。"
            ),
            "memo_action": "修正した箇所を一覧に残した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        },
        {
            "memo": "自分には何もできない。それでも、相談の予約は取り消していない。",
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        },
        {
            "memo": "まだ速くなったとは言えないが、前回より手順を一つ減らせそうだ。",
            "memo_action": "作業時間を表に記録した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        },
    )
    for current_input in unseen_inputs:
        original = build_grounded_observation_plan(current_input)
        renamed = build_grounded_observation_plan(
            {**current_input, "case_id": "fixture-name-must-not-be-semantic-input"}
        )
        reception = original.response_plan.human_reception_plan
        assert reception is not None
        assert reception.required is True
        assert original.as_body_free_meta() == renamed.as_body_free_meta()


def test_r2_reception_meta_contains_ids_enums_and_policies_but_no_body() -> None:
    for case in _load_fixture()["cases"]:
        plan = build_grounded_observation_plan(case["exact_current_input"])
        meta = plan.as_body_free_meta()
        serialized = json.dumps(meta, ensure_ascii=False, sort_keys=True)
        reception = meta["response_plan"]["human_reception_plan"]
        assert meta["human_reception_plan_included"] is True
        assert meta["human_reception_plan_required"] is True
        assert reception["schema_version"] == GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION
        assert reception["target_nucleus_ids"]
        assert reception["source_evidence_span_ids"]
        assert case["exact_current_input"]["memo"] not in serialized
        if case["exact_current_input"]["memo_action"]:
            assert case["exact_current_input"]["memo_action"] not in serialized
        assert case["local_comment_sha256"] not in serialized

        def visit(value) -> None:
            if isinstance(value, dict):
                assert not {
                    "raw_text",
                    "comment_text",
                    "surface_text",
                    "completed_sentence",
                    "case_id",
                    "expected_hash",
                }.intersection(value)
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(reception)


def test_r2_invalid_quote_distinctness_and_target_policies_are_rejected() -> None:
    current_input = _load_fixture()["cases"][2]["exact_current_input"]
    plan, resolver = _plan_and_resolver(current_input)
    reception = plan.response_plan.human_reception_plan
    assert reception is not None

    invalid_quote = replace(
        reception,
        quote_policy=replace(reception.quote_policy, max_anchor_count=2),
    )
    invalid_distinctness = replace(
        reception,
        distinctness_policy=replace(
            reception.distinctness_policy,
            relation_reexplanation_allowed=True,
        ),
    )
    other_nucleus_id = next(
        item.nucleus_id
        for item in plan.nuclei
        if item.nucleus_id not in reception.target_nucleus_ids
    )
    invalid_target = replace(reception, target_nucleus_ids=(other_nucleus_id,))
    invalid_stance = replace(reception, stance="quiet_presence")
    invalid_follow_profile = replace(
        reception,
        primary_follow_element="existence_respect",
    )

    for mutated_reception, expected_issue in (
        (invalid_quote, "human_reception_quote_anchor_count_invalid"),
        (invalid_distinctness, "human_reception_distinctness_policy_relaxed"),
        (invalid_target, "human_reception_target_mismatch"),
        (invalid_stance, "human_reception_stance_act_mismatch"),
        (invalid_follow_profile, "human_reception_follow_profile_act_mismatch"),
    ):
        mutated_plan = replace(
            plan,
            response_plan=replace(
                plan.response_plan,
                human_reception_plan=mutated_reception,
            ),
        )
        assert expected_issue in validate_grounded_observation_plan(mutated_plan, resolver)


def test_r2_ungrounded_self_denial_counterposition_is_rejected() -> None:
    case = next(case for case in _load_fixture()["cases"] if case["case_id"] == "D")
    plan, resolver = _plan_and_resolver(case["exact_current_input"])
    reception = plan.response_plan.human_reception_plan
    assert reception is not None
    target_id = reception.target_nucleus_ids[0]
    target = next(item for item in plan.nuclei if item.nucleus_id == target_id)
    stripped_codes = tuple(
        code
        for code in target.semantic_frame.attribute_codes
        if code
        not in {
            "operator:action",
            "operator:help_seeking",
            "operator:continuation",
            "operator:refusal",
            "semantic_role:protective_or_limiting_refusal",
        }
    )
    ungrounded_target = replace(
        target,
        kind="state",
        semantic_frame=replace(
            target.semantic_frame,
            modality="feeling",
            attribute_codes=stripped_codes,
        ),
    )
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    nucleus_index[target_id] = ungrounded_target
    ungrounded_reception = replace(
        reception,
        support_nucleus_ids=(),
        source_evidence_span_ids=ungrounded_target.source_span_ids,
    )
    issues = validate_grounded_human_reception_plan(
        ungrounded_reception,
        expected_target_ids=plan.response_plan.human_follow_target_ids,
        nucleus_index=nucleus_index,
        resolver=resolver,
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
    )
    assert "human_reception_ungrounded_self_denial_counterposition" in issues


def test_r2_empty_and_separate_safety_paths_do_not_create_normal_reception_plan() -> None:
    inputs_and_kinds = (
        ({}, "safe_observation"),
        (
            {"memo": "安全が保てない。助けが必要。", "emotions": ["不安"]},
            TRIAGE_SAFETY_SUPPORT_REQUIRED,
        ),
        (
            {"memo": "もう消えたい。今日で終わりにしたい。", "emotions": ["悲しみ"]},
            TRIAGE_SAFETY_BLOCKED_EMERGENCY,
        ),
    )
    for current_input, expected_safety_kind in inputs_and_kinds:
        plan, resolver = _plan_and_resolver(current_input)
        assert plan.safety_policy.safety_kind == expected_safety_kind
        assert plan.coverage_requirements.human_follow_required is False
        assert plan.response_plan.human_reception_plan is None
        assert validate_grounded_observation_plan(plan, resolver) == ()
