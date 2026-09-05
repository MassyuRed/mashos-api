# -*- coding: utf-8 -*-
from __future__ import annotations

"""Case/dependency self-denial ownership and reception-act exact cover."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any, Mapping
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    classify_emlis_safety_triage_text,
    is_bounded_self_denial_text,
)
from cocolon_meaning_experience_engine.contracts import (
    CMEEStage1ContractError,
    GenerationRequest,
    LimitedMeaningOutcome,
    SubjectiveResponsibilityKind,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    _build_experience_plan,
    _build_graph,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine import emlis_stage1_composition as composition
from cocolon_meaning_experience_engine import emlis_stage1_response as response


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
_BATCH_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"
_TARGET_CASE_ID = "nls3s_b001_0066"
_SELECTED_AT = "2026-09-01T00:00:00Z"


def _request(
    *,
    record_id: str,
    thought_text: str,
    action_text: str,
    categories: tuple[str, ...] = ("生活",),
    emotions: tuple[Mapping[str, str], ...] = (
        {"type": "不安", "strength": "strong"},
    ),
) -> GenerationRequest:
    return GenerationRequest(
        request_id=f"req-cmee-self-denial-{record_id}",
        current_input_bundle=build_emlis_current_input_bundle(
            {
                "id": record_id,
                "created_at": _SELECTED_AT,
                "memo": thought_text,
                "memo_action": action_text,
                "category": list(categories),
                "emotion_details": list(emotions),
                "emotions": [str(item["type"]) for item in emotions],
                "is_secret": False,
            }
        ),
        expected_source_record_id=record_id,
    )


def _source_plan(request: GenerationRequest):
    source = freeze_text_source(request)
    plan = build_final_stage1_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    return source, plan


def _phase_a(request: GenerationRequest):
    source, plan = _source_plan(request)
    required_nuclei, required_relations, reception_targets = (
        _planned_visible_source_ids(plan)
    )
    graph = _build_graph(
        source,
        plan,
        _ordered((*required_nuclei, *reception_targets)),
        required_relations,
    )
    parent = _build_experience_plan(
        source,
        graph,
        plan,
        required_nuclei,
        required_relations,
        reception_targets,
    )
    phase = response.build_subjective_planning_inputs(
        source=source,
        grounded_plan=plan,
        grounded_graph=graph,
        parent_plan=parent,
    )
    return source, plan, phase


def _claim(
    claim_id: str,
    responsibility_refs: tuple[str, ...],
    act_refs: tuple[str, ...],
) -> composition.ProjectedSubjectiveClaim:
    return composition.ProjectedSubjectiveClaim(
        schema_version="focused-test",
        subjective_claim_id=claim_id,
        parent_duty_ref="parent-duty",
        speaker_owner="emlis",
        claim_domain="EMLIS_SUBJECTIVE_RESPONSE",
        subjective_responsibility_refs=responsibility_refs,
        selected_subjective_opportunity_key=f"opportunity:{claim_id}",
        asserted_subjective_proposition=None,
        basis_observation_contribution_refs=(),
        basis_semantic_refs=(),
        source_reception_act_refs=act_refs,
        value_principle_refs=(),
        user_fact_effect=0,
        forbidden_promotions=(),
    )


class CMEE0066SelfDenialDependencyAndExactCoverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows = tuple(
            json.loads(line)
            for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        manifest: dict[str, Any] = json.loads(
            _MANIFEST_PATH.read_text(encoding="utf-8")
        )
        if len(rows) != 100 or manifest["case_count"] != 100:
            raise AssertionError("canonical_batch001_exact100_required")
        cls.row = next(
            row for row in rows if str(row["case_id"]) == _TARGET_CASE_ID
        )
        input_row = cls.row["input"]
        cls.request = _request(
            record_id=_TARGET_CASE_ID,
            thought_text=str(input_row["thought_text"]),
            action_text=str(input_row["action_text"]),
            categories=tuple(str(value) for value in input_row["categories"]),
            emotions=tuple(input_row["emotions"]),
        )
        cls.source, cls.plan = _source_plan(cls.request)

    def test_01_accountability_returns_to_normal_two_move_plan(self) -> None:
        plan = self.plan
        action_nuclei = tuple(
            row for row in plan.nuclei if "memo_action" in row.source_fields
        )
        self.assertEqual(plan.input_profile.safety_kind, TRIAGE_SAFE_OBSERVATION)
        self.assertEqual(plan.response_plan.response_kind, "normal_observation")
        self.assertEqual(plan.response_plan.fact_boundary_nucleus_ids, ())
        self.assertEqual(len(action_nuclei), 1)
        self.assertEqual(
            (action_nuclei[0].kind, action_nuclei[0].semantic_frame.predicate_kind),
            ("action", "action"),
        )
        self.assertNotIn(
            "operator:self_evaluation",
            action_nuclei[0].semantic_frame.attribute_codes,
        )
        reception_plan = plan.response_plan.human_reception_plan
        self.assertIsNotNone(reception_plan)
        self.assertEqual(
            tuple(move.reception_act for move in reception_plan.moves),
            ("honor_concrete_effort", "recognize_lived_change"),
        )
        self.assertFalse(
            {"bounded_counter_self_denial", "stay_with_current_burden"}
            & {move.reception_act for move in reception_plan.moves}
        )

    def test_02_self_denial_requires_a_bounded_case_dependency(self) -> None:
        admitted = (
            "自分を傷つけている。",
            "自分のことを責め続けている。",
            "私自身を否定している。",
            "自分には価値がない。",
            "私は役に立たない。",
            "僕なんか何もできない。",
        )
        rejected = (
            "自分の言い方で相手を傷つけてしまい、謝った。",
            "自分の判断で相手を追い込んだことを認めた。",
            "自分が相手を傷つけた。",
            "自分の表現は最低だった。",
            "自分の予定では最低でも15分は取りたい。",
            "自分の考えを言葉にできない。",
            "彼は私を傷つけている。",
        )
        for text in admitted:
            with self.subTest(admitted=text):
                self.assertTrue(is_bounded_self_denial_text(text))
                self.assertEqual(
                    classify_emlis_safety_triage_text(text).safety_triage_kind,
                    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
                )
        for text in rejected:
            with self.subTest(rejected=text):
                self.assertFalse(is_bounded_self_denial_text(text))
                self.assertEqual(
                    classify_emlis_safety_triage_text(text).safety_triage_kind,
                    TRIAGE_SAFE_OBSERVATION,
                )

    def test_self_worth_particles_keep_the_same_identity_boundary(self) -> None:
        # Transform an existing public synthetic input; no corpus text is
        # copied into this grammatical boundary regression.
        source = "自分には価値がない。"
        for owner_link in ("には", "の"):
            for particle in ("が", "は", "も"):
                for negation in ("ない", "無い"):
                    text = source.replace("には", owner_link).replace(
                        "価値がない", f"価値{particle}{negation}",
                    )
                    with self.subTest(owner_link=owner_link, particle=particle,
                                      negation=negation):
                        self.assertTrue(is_bounded_self_denial_text(text))
                        decision = classify_emlis_safety_triage_text(text)
                        self.assertEqual(decision.safety_triage_kind,
                                         TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER)
                        self.assertTrue(decision.must_not_accept_identity_claim_as_fact)
                        self.assertFalse(decision.requires_separate_safety_surface)
        for owner_link in ("の表現には", "の予定には"):
            text = source.replace("には", owner_link).replace("価値が", "価値も")
            with self.subTest(non_identity_owner=owner_link):
                self.assertFalse(is_bounded_self_denial_text(text))
                self.assertEqual(classify_emlis_safety_triage_text(text).safety_triage_kind,
                                 TRIAGE_SAFE_OBSERVATION)

    def test_03_fact_boundary_cannot_launder_an_action_as_self_denial(self) -> None:
        action_id = next(
            row.nucleus_id
            for row in self.plan.nuclei
            if "memo_action" in row.source_fields
        )
        forged = replace(
            self.plan,
            safety_policy=replace(
                self.plan.safety_policy,
                safety_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
                identity_claim_must_not_be_accepted_as_fact=True,
            ),
            coverage_requirements=replace(
                self.plan.coverage_requirements,
                fact_boundary_required=True,
            ),
            response_plan=replace(
                self.plan.response_plan,
                fact_boundary_nucleus_ids=(action_id,),
            ),
        )
        resolver = build_evidence_span_resolver(
            self.source.evidence_spans,
            current_input=self.source.normalized_current_input,
        )
        self.assertIn(
            "self_denial_fact_boundary_target_kind_invalid",
            validate_grounded_observation_plan(forged, resolver),
        )

    def test_04_retained_responsibility_claim_cover_is_exact(self) -> None:
        responsibilities = (
            composition.SubjectiveResponsibilityRow(
                "responsibility:a",
                SubjectiveResponsibilityKind.MATERIAL_APPRAISAL,
                ("contribution:a",),
                ("act:a",),
            ),
            composition.SubjectiveResponsibilityRow(
                "responsibility:b",
                SubjectiveResponsibilityKind.AFFECTIVE_RESPONSE,
                ("contribution:b",),
                ("act:b",),
            ),
        )
        claims = (
            _claim("claim:a", ("responsibility:a",), ("act:a",)),
            _claim("claim:b", ("responsibility:b",), ("act:b",)),
        )
        composition._validate_retained_reception_act_exact_cover(
            retained_act_refs=("act:a", "act:b"),
            responsibilities=responsibilities,
            claims=claims,
        )

        laundering_mutations = (
            (responsibilities[:1], claims[:1]),
            (
                responsibilities,
                (
                    _claim("claim:a", ("responsibility:a",), ("act:b",)),
                    _claim("claim:b", ("responsibility:b",), ("act:a",)),
                ),
            ),
            (
                responsibilities,
                (
                    _claim("claim:a", ("responsibility:a",), ("act:a",)),
                    _claim("claim:b", ("responsibility:b",), ("act:a",)),
                ),
            ),
        )
        for test_responsibilities, test_claims in laundering_mutations:
            with self.subTest(
                responsibilities=len(test_responsibilities),
                claims=len(test_claims),
            ):
                with self.assertRaisesRegex(
                    composition.Stage1CompositionError,
                    "MEANING_PLAN_RECEPTION_ACT_EXACT_COVER_STOP",
                ):
                    composition._validate_retained_reception_act_exact_cover(
                        retained_act_refs=("act:a", "act:b"),
                        responsibilities=test_responsibilities,
                        claims=test_claims,
                    )

    def test_05_genuine_bounded_affirmative_mixed_counter_stops_in_im04(self) -> None:
        request = _request(
            record_id="focused-bounded-limited",
            thought_text="自分には価値がない。",
            action_text="相談先の番号は消さずに残した。",
        )
        _source, plan = _source_plan(request)
        self.assertEqual(
            plan.input_profile.safety_kind,
            TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
        ):
            _phase_a(request)

    def test_06_production_owners_contain_no_fixture_branch(self) -> None:
        input_row = self.row["input"]
        forbidden = (
            _TARGET_CASE_ID,
            str(input_row["thought_text"]),
            str(input_row["action_text"]),
        )
        owner_paths = (
            Path(is_bounded_self_denial_text.__code__.co_filename),
            _AI_ROOT / "services" / "ai_inference" / "emlis_ai_grounded_observation_plan.py",
            Path(composition.__file__),
        )
        for path in owner_paths:
            source = path.read_text(encoding="utf-8")
            with self.subTest(owner=path.name):
                for value in forbidden:
                    self.assertNotIn(value, source)


if __name__ == "__main__":
    unittest.main()
