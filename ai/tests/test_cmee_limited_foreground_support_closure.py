# -*- coding: utf-8 -*-
from __future__ import annotations

"""Pre-IM03 source-foreground coverage inherited by canonical Phase A."""

from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Mapping
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
)
from cocolon_meaning_experience_engine.contracts import (
    AppraisalDimension,
    AppraisalOperation,
    ArgumentRole,
    CMEEStage1ContractError,
    GenerationRequest,
    InterpretationKind,
    LimitedMeaningOutcome,
    RelationOperator,
    SemanticOperator,
    canonical_limited_retained_layer1_refs,
    resolve_limited_reception_aggregate,
    stage1_foreground_coverage_required_flags,
    stage1_source_explicit_target_topic_scope_refs,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    _build_experience_plan,
    _build_graph,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
import cocolon_meaning_experience_engine.emlis_stage1_composition as composition
import cocolon_meaning_experience_engine.emlis_stage1_response as response
from tools.emlis_nls_v3_batch_run import load_validated_batch


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
)
_BATCH_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"
_TARGET_CASE_ID = "nls3s_b001_0058"
_STRUCTURAL_UNFINISHED_CASE_ID = "nls3s_b001_0035"
_SELECTED_AT = "2026-09-01T00:00:00Z"
# The old full-projection population was 21.  These two already had exact-two
# Limited acts; pre-105 they stopped only because their causal trace had no
# foreground support.  Pre-IM03 promotion plus the canonical aggregate owner
# makes the complete current population exact24, including 0064's basis union.
_A_CAUSAL_FULL_PATH_DELTA_IDS = (
    "nls3s_b001_0059",
    "nls3s_b001_0061",
)
_CANONICAL_EXACT2_NON_COUNTER_FULL_PATH_IDS = (
    "nls3s_b001_0020",
    "nls3s_b001_0023",
    "nls3s_b001_0027",
    "nls3s_b001_0039",
    "nls3s_b001_0040",
    "nls3s_b001_0049",
    "nls3s_b001_0055",
    "nls3s_b001_0056",
    "nls3s_b001_0057",
    "nls3s_b001_0059",
    "nls3s_b001_0060",
    "nls3s_b001_0061",
    "nls3s_b001_0064",
    "nls3s_b001_0066",
    "nls3s_b001_0069",
    "nls3s_b001_0073",
    "nls3s_b001_0077",
    "nls3s_b001_0078",
    "nls3s_b001_0083",
    "nls3s_b001_0087",
    "nls3s_b001_0088",
    "nls3s_b001_0091",
    "nls3s_b001_0094",
    "nls3s_b001_0100",
)


def _request_from_canonical_row(row: Mapping[str, Any]) -> GenerationRequest:
    input_row = row["input"]
    emotions = input_row["emotions"]
    raw = {
        "id": str(row["case_id"]),
        "created_at": _SELECTED_AT,
        "memo": input_row["thought_text"],
        "memo_action": input_row["action_text"],
        "category": input_row["categories"],
        "emotion_details": emotions,
        "emotions": [str(item["type"]) for item in emotions],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-cmee-limited-support-{row['case_id']}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=str(row["case_id"]),
    )


def _grounded_inputs(row: Mapping[str, Any]):
    source = freeze_text_source(_request_from_canonical_row(row))
    grounded_plan = build_final_stage1_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    required_nuclei, required_relations, reception_targets = (
        _planned_visible_source_ids(grounded_plan)
    )
    graph = _build_graph(
        source,
        grounded_plan,
        _ordered((*required_nuclei, *reception_targets)),
        required_relations,
    )
    parent_plan = _build_experience_plan(
        source,
        graph,
        grounded_plan,
        required_nuclei,
        required_relations,
        reception_targets,
    )
    return source, grounded_plan, graph, parent_plan


def _semantic_cover(contribution) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *contribution.semantic_refs,
                *contribution.relation_basis_refs,
                *(
                    binding.semantic_ref
                    for binding in contribution.argument_bindings
                ),
            )
        )
    )


class CMEELimitedForegroundSupportClosureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, manifest = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        if len(rows) != 100 or manifest["case_count"] != 100:
            raise AssertionError("canonical_batch001_exact100_required")
        row = next(row for row in rows if row["case_id"] == _TARGET_CASE_ID)
        cls.inputs = _grounded_inputs(row)
        tracked_names = (
            "stage1_candidate_selection_indices",
            "derive_grounded_situation_view",
            "derive_foreground_scope_closed",
            "derive_input_specific_meaning_structure",
            "build_interpretation_candidate_pool",
            "build_emlis_meaning_field",
            "plan_layer1_observation",
        )
        originals = {name: getattr(response, name) for name in tracked_names}
        with ExitStack() as stack:
            spies = {
                name: stack.enter_context(
                    patch.object(response, name, wraps=originals[name])
                )
                for name in tracked_names
            }
            cls.phase = response.build_subjective_planning_inputs(
                source=cls.inputs[0],
                grounded_plan=cls.inputs[1],
                grounded_graph=cls.inputs[2],
                parent_plan=cls.inputs[3],
            )
            cls.call_counts = {
                name: spy.call_count for name, spy in spies.items()
            }
        row_by_id = {row["case_id"]: row for row in rows}
        cls.aggregate_phases = {}
        for case_id in _CANONICAL_EXACT2_NON_COUNTER_FULL_PATH_IDS:
            aggregate_inputs = _grounded_inputs(row_by_id[case_id])
            cls.aggregate_phases[case_id] = (
                response.build_subjective_planning_inputs(
                    source=aggregate_inputs[0],
                    grounded_plan=aggregate_inputs[1],
                    grounded_graph=aggregate_inputs[2],
                    parent_plan=aggregate_inputs[3],
                )
            )
        unfinished_inputs = _grounded_inputs(
            next(
                row
                for row in rows
                if row["case_id"] == _STRUCTURAL_UNFINISHED_CASE_ID
            )
        )
        cls.unfinished_phase = response.build_subjective_planning_inputs(
            source=unfinished_inputs[0],
            grounded_plan=unfinished_inputs[1],
            grounded_graph=unfinished_inputs[2],
            parent_plan=unfinished_inputs[3],
        )

    def test_graph_only_promotion_is_exact_bounded_and_fail_closed(self) -> None:
        node_a = "node:a@cocolon.cmee.v1a.grounded_graph.v1"
        node_b = "node:b@cocolon.cmee.v1a.grounded_graph.v1"
        edge = "edge:a-b@cocolon.cmee.v1a.grounded_graph.v1"
        self.assertEqual(
            stage1_foreground_coverage_required_flags(
                candidate_semantic_refs=((edge, node_a), (node_a,), (node_b,)),
                source_required_flags=(True, False, False),
                relation_flags=(True, False, False),
                foreground_object_refs=(node_a, node_b),
            ),
            (True, False, True),
        )
        self.assertEqual(
            stage1_foreground_coverage_required_flags(
                candidate_semantic_refs=((node_a,),),
                source_required_flags=(False,),
                relation_flags=(False,),
                foreground_object_refs=(),
            ),
            (False,),
        )
        invalid_rows = (
            (((edge, node_a),), (True,), (True,), (node_b,)),
            (((node_a,), (node_a,)), (False, False), (False, False), (node_a,)),
            (((node_a,), (node_b,)), (False, False), (False, False), (node_b, node_a)),
        )
        for semantic_rows, required, relations, foreground in invalid_rows:
            with self.subTest(foreground=foreground):
                with self.assertRaises(CMEEStage1ContractError):
                    stage1_foreground_coverage_required_flags(
                        candidate_semantic_refs=semantic_rows,
                        source_required_flags=required,
                        relation_flags=relations,
                        foreground_object_refs=foreground,
                    )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_required_observation_unrealizable",
        ):
            response._selected_contribution_candidates(
                tuple(SimpleNamespace(required=True) for _ in range(6))
            )

    def test_phase_a_inherits_premeaning_without_semantic_reselection(self) -> None:
        phase = self.phase
        premeaning = phase.premeaning_inputs
        outcome = phase.input_specific_meaning_structure.meaning_decision_outcome
        self.assertIs(type(outcome), LimitedMeaningOutcome)
        self.assertEqual(self.call_counts["stage1_candidate_selection_indices"], 1)
        self.assertEqual(self.call_counts["derive_grounded_situation_view"], 1)
        self.assertEqual(self.call_counts["derive_foreground_scope_closed"], 1)
        self.assertEqual(
            self.call_counts["derive_input_specific_meaning_structure"], 1
        )
        self.assertEqual(self.call_counts["build_interpretation_candidate_pool"], 0)
        self.assertEqual(self.call_counts["build_emlis_meaning_field"], 0)
        self.assertEqual(self.call_counts["plan_layer1_observation"], 0)
        self.assertFalse(
            hasattr(response, "_final_stage1_phase_a_semantic_closure")
        )

        self.assertEqual(phase.meaning_field, premeaning.meaning_field)
        self.assertEqual(
            phase.observation_contribution_rows,
            premeaning.observation_contribution_rows,
        )
        self.assertIs(
            phase.observation_depth_class,
            premeaning.observation_depth_class,
        )
        foreground_refs = stage1_source_explicit_target_topic_scope_refs(
            phase.grounded_graph
        )
        required_cover = {
            ref
            for contribution in premeaning.observation_contribution_rows
            if contribution.retention == "REQUIRED"
            for ref in _semantic_cover(contribution)
        }
        self.assertTrue(foreground_refs)
        self.assertTrue(set(foreground_refs).issubset(required_cover))
        self.assertLessEqual(
            len(premeaning.observation_contribution_rows),
            response.LAYER1_OBSERVATION_CONTRIBUTION_CAP,
        )

        premeaning_ids = {
            row.candidate_id for row in premeaning.interpretation_candidate_rows
        }
        phase_ids = {row.candidate_id for row in phase.interpretation_candidate_rows}
        self.assertTrue(premeaning_ids.issubset(phase_ids))
        endpoint_refs = {
            binding.semantic_ref
            for candidate in premeaning.interpretation_candidate_rows
            if candidate.candidate_id
            in set(premeaning.meaning_field.required_candidate_refs)
            and candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
            for binding in candidate.argument_bindings
        }
        support_tail = tuple(
            row
            for row in phase.interpretation_candidate_rows
            if row.candidate_id not in premeaning_ids
        )
        self.assertTrue(support_tail)
        self.assertTrue(
            all(
                row.relation_operator is RelationOperator.NO_RELATION_CLAIM
                and set(row.semantic_refs).issubset(endpoint_refs)
                for row in support_tail
            )
        )
        composition._validate_phase_A(phase)

    def test_limited_projection_keeps_bounded_trace_and_owner_lineage(self) -> None:
        plan = composition.project_subjective_meaning_plan(self.phase)
        bounded = self.phase.bounded_limited_reception_records[0]
        bounded_refs = set(bounded.bound_layer1_contribution_refs)
        self.assertEqual(len(plan.subjective_claim_rows), 1)
        self.assertEqual(len(plan.reception_visible_causal_trace_rows), 1)
        self.assertTrue(
            all(
                row.layer1_contribution_refs
                and set(row.layer1_contribution_refs).issubset(bounded_refs)
                for row in plan.meaning_visible_causal_trace_rows
            )
        )
        claim = plan.subjective_claim_rows[0]
        self.assertEqual(claim.user_fact_effect, 0)
        self.assertEqual(claim.source_reception_act_refs, plan.retained_reception_act_refs)

    def test_canonical_exact24_freezes_the_a_causal_full_path_delta(self) -> None:
        self.assertEqual(len(_CANONICAL_EXACT2_NON_COUNTER_FULL_PATH_IDS), 24)
        self.assertTrue(
            set(_A_CAUSAL_FULL_PATH_DELTA_IDS).issubset(
                _CANONICAL_EXACT2_NON_COUNTER_FULL_PATH_IDS
            )
        )
        for case_id, phase in self.aggregate_phases.items():
            with self.subTest(case_id=case_id):
                premeaning = phase.premeaning_inputs
                self.assertIs(
                    type(
                        phase.input_specific_meaning_structure
                        .meaning_decision_outcome
                    ),
                    LimitedMeaningOutcome,
                )
                self.assertEqual(len(phase.retained_reception_act_rows), 2)
                self.assertNotIn(
                    "bounded_counter_self_denial",
                    tuple(
                        row.reception_act
                        for row in phase.retained_reception_act_rows
                    ),
                )
                self.assertEqual(phase.meaning_field, premeaning.meaning_field)
                self.assertEqual(
                    phase.observation_contribution_rows,
                    premeaning.observation_contribution_rows,
                )
                self.assertIs(
                    phase.observation_depth_class,
                    premeaning.observation_depth_class,
                )
                expected_act_refs = (
                    phase.allowed_reception_opportunity_envelope
                    .allowed_reception_act_ids
                )
                canonical_retained_refs = (
                    canonical_limited_retained_layer1_refs(
                        phase.input_specific_meaning_structure
                        .meaning_decision_outcome.retained_layer1_refs,
                        phase.observation_contribution_rows,
                    )
                )
                (
                    _mode,
                    _operator,
                    act_refs,
                    licensed_basis_refs,
                    aggregate,
                ) = resolve_limited_reception_aggregate(
                    phase.retained_reception_act_rows,
                    expected_act_refs=expected_act_refs,
                    retained_layer1_refs=canonical_retained_refs,
                    observation_contribution_rows=(
                        phase.observation_contribution_rows
                    ),
                )
                self.assertTrue(aggregate)
                self.assertEqual(act_refs, expected_act_refs)
                self.assertEqual(
                    phase.bounded_limited_reception_records[0]
                    .bound_layer1_contribution_refs,
                    canonical_retained_refs,
                )
                self.assertEqual(
                    canonical_retained_refs,
                    tuple(
                        row.contribution_id
                        for row in phase.observation_contribution_rows
                        if row.contribution_id in set(canonical_retained_refs)
                    ),
                )
                if case_id == "nls3s_b001_0064":
                    self.assertEqual(len(licensed_basis_refs), 3)
                    protect_row = next(
                        row
                        for row in phase.retained_reception_act_rows
                        if row.reception_act
                        == "protect_retained_intention"
                    )
                    self.assertEqual(
                        len(protect_row.basis_contribution_refs),
                        2,
                    )
                    reduced_rows = tuple(
                        replace(
                            row,
                            basis_contribution_refs=(
                                row.basis_contribution_refs[0],
                            ),
                        )
                        if row is protect_row
                        else row
                        for row in phase.retained_reception_act_rows
                    )
                    reduced_records = (
                        response.build_stage1_post_selection_reception_records(
                            input_specific_meaning_structure=(
                                phase.input_specific_meaning_structure
                            ),
                            projection_preimage_ref=(
                                phase.projection_preimage_ref
                            ),
                            retained_reception_act_rows=reduced_rows,
                            observation_contribution_rows=(
                                phase.observation_contribution_rows
                            ),
                            interpretation_candidate_rows=(
                                phase.interpretation_candidate_rows
                            ),
                            contribution_to_candidate_ref_map=(
                                phase.contribution_to_candidate_ref_map
                            ),
                            qualifier_value_rows=(
                                phase.qualifier_value_by_candidate_scope_axis_key
                            ),
                            material_unknown_refs=(
                                phase.material_unknown_refs
                            ),
                            expected_act_refs=expected_act_refs,
                        )
                    )
                    forged_phase = replace(
                        phase,
                        retained_reception_act_rows=reduced_rows,
                        reading_consequence_records=reduced_records[0],
                        sealed_emlis_provisional_reading_records=(
                            reduced_records[1]
                        ),
                        meaning_bound_reception_proposition_records=(
                            reduced_records[2]
                        ),
                        meaning_bound_reception_set_records=(
                            reduced_records[3]
                        ),
                        bounded_limited_reception_records=(
                            reduced_records[4]
                        ),
                        bounded_limited_subjective_proposition_records=(
                            reduced_records[5]
                        ),
                        projection_seal_ref=reduced_records[6],
                    )
                    with self.assertRaisesRegex(
                        composition.Stage1CompositionError,
                        "STAGE1_RECEPTION_ACT_BASIS_CLOSURE_STOP",
                    ):
                        composition._validate_phase_A(forged_phase)
                if case_id == "nls3s_b001_0059":
                    self.assertEqual(
                        act_refs,
                        (
                            "recognize_lived_change",
                            "honor_concrete_effort",
                        ),
                    )
                plan = composition.project_subjective_meaning_plan(phase)
                self.assertEqual(len(plan.subjective_claim_rows), 1)
                self.assertTrue(
                    all(
                        row.layer1_contribution_refs
                        for row in plan.meaning_visible_causal_trace_rows
                    )
                )

    def test_final_surface_inherits_selected_foreground_coverage(self) -> None:
        actual_build_sentence_plan = response.build_grounded_sentence_plan
        actual_realize = response.realize_grounded_sentence_plan
        actual_inverse = response.evaluate_grounded_surface_body_inverse
        actual_gate = response.evaluate_grounded_observation_gate

        for case_id in (
            "nls3s_b001_0059",
            "nls3s_b001_0069",
            "nls3s_b001_0094",
        ):
            with self.subTest(case_id=case_id):
                phase = self.aggregate_phases[case_id]
                final_plans = []
                realized_surfaces = []
                inverse_by_body = {}
                gates_by_body = {}

                def track_build_sentence_plan(plan, resolver, **kwargs):
                    final_plans.append(plan)
                    return actual_build_sentence_plan(
                        plan,
                        resolver,
                        **kwargs,
                    )

                def track_realize(*args, **kwargs):
                    result = actual_realize(*args, **kwargs)
                    realized_surfaces.append(result)
                    return result

                def track_inverse(*args, **kwargs):
                    result = actual_inverse(*args, **kwargs)
                    body = kwargs.get("body", args[0] if args else None)
                    if type(body) is bytes:
                        inverse_by_body.setdefault(body, []).append(result)
                    return result

                def track_gate(*args, **kwargs):
                    result = actual_gate(*args, **kwargs)
                    surface = kwargs.get("surface_result")
                    if surface is not None:
                        gates_by_body.setdefault(
                            surface.text.encode("utf-8"),
                            [],
                        ).append(result)
                    return result

                with (
                    patch.object(
                        response,
                        "build_grounded_sentence_plan",
                        side_effect=track_build_sentence_plan,
                    ),
                    patch.object(
                        response,
                        "realize_grounded_sentence_plan",
                        side_effect=track_realize,
                    ),
                    patch.object(
                        response,
                        "evaluate_grounded_surface_body_inverse",
                        side_effect=track_inverse,
                    ),
                    patch.object(
                        response,
                        "evaluate_grounded_observation_gate",
                        side_effect=track_gate,
                    ),
                ):
                    projection, units = response.compile_stage1_response(
                        source=phase.admitted_source,
                        grounded_graph=phase.grounded_graph,
                        parent_plan=phase.parent_plan,
                        grounded_plan=phase.grounded_plan,
                    )

                self.assertEqual(len(final_plans), 1)
                final_plan = final_plans[0]
                binding = response._bind_grounded_plan(
                    phase.admitted_source,
                    phase.grounded_graph,
                    final_plan,
                )
                covered_graph_refs = {
                    *(
                        response._node_ref(
                            binding.nucleus_to_node[nucleus_id]
                        )
                        for nucleus_id in (
                            final_plan.coverage_requirements
                            .required_nucleus_ids
                        )
                    ),
                    *(
                        response._edge_ref(
                            binding.relation_to_edge[relation_id]
                        )
                        for relation_id in (
                            final_plan.coverage_requirements
                            .required_relation_ids
                        )
                    ),
                }
                selected_graph_refs = {
                    ref
                    for contribution in projection.observation_contributions
                    for ref in (
                        *contribution.semantic_refs,
                        *contribution.relation_basis_refs,
                    )
                }
                self.assertTrue(
                    selected_graph_refs.issubset(covered_graph_refs)
                )
                self.assertTrue(
                    set(
                        phase.grounded_plan.coverage_requirements
                        .required_nucleus_ids
                    ).issubset(
                        final_plan.coverage_requirements.required_nucleus_ids
                    )
                )
                self.assertTrue(
                    set(
                        phase.grounded_plan.coverage_requirements
                        .required_relation_ids
                    ).issubset(
                        final_plan.coverage_requirements.required_relation_ids
                    )
                )
                self.assertTrue(
                    set(final_plan.response_plan.required_nucleus_ids)
                    .isdisjoint(
                        final_plan.response_plan.optional_nucleus_ids
                    )
                )

                observation_anchors = tuple(
                    anchor
                    for unit in units
                    if unit.layer == "LAYER_1"
                    for anchor in unit.basis_anchor_refs
                )
                subjective_anchors = tuple(
                    anchor
                    for unit in units
                    if unit.layer == "LAYER_2"
                    for anchor in unit.basis_anchor_refs
                )
                self.assertEqual(
                    observation_anchors,
                    projection.ordered_observation_refs,
                )
                self.assertEqual(
                    subjective_anchors,
                    projection.ordered_subjective_refs,
                )
                selected_surface = next(
                    surface
                    for surface in realized_surfaces
                    if tuple(line.text for line in surface.lines)
                    == tuple(unit.text for unit in units)
                )
                selected_body = selected_surface.text.encode("utf-8")
                self.assertTrue(
                    any(
                        report.passed
                        for report in inverse_by_body[selected_body]
                    )
                )
                self.assertTrue(
                    any(
                        report.passed
                        for report in gates_by_body[selected_body]
                    )
                )

    def test_final_surface_projection_coverage_tamper_stops(self) -> None:
        phase = self.aggregate_phases["nls3s_b001_0069"]
        meaning_plan = composition.project_subjective_meaning_plan(phase)
        projection = response.seal_stage1_projection(phase, meaning_plan)
        first = projection.observation_contributions[0]
        invalid_rows = (
            replace(
                first,
                semantic_refs=(
                    "node:unmapped@cocolon.cmee.grounded_meaning_graph.v1alpha1",
                ),
            ),
            replace(
                first,
                relation_basis_refs=(first.semantic_refs[0],),
            ),
        )
        for invalid in invalid_rows:
            with self.subTest(invalid=invalid):
                forged = replace(
                    projection,
                    observation_contributions=(
                        invalid,
                        *projection.observation_contributions[1:],
                    ),
                )
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_v2_grounded_surface_projection_coverage_unmapped",
                ):
                    response._inherit_projection_observation_coverage(
                        source=phase.admitted_source,
                        grounded_graph=phase.grounded_graph,
                        grounded_plan=phase.grounded_plan,
                        projection=forged,
                    )
        missing_required = replace(
            projection,
            observation_contributions=(
                projection.observation_contributions[1:]
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_v2_grounded_surface_required_coverage_unselected",
        ):
            response._inherit_projection_observation_coverage(
                source=phase.admitted_source,
                grounded_graph=phase.grounded_graph,
                grounded_plan=phase.grounded_plan,
                projection=missing_required,
            )

    def test_structural_unfinished_appraisal_is_exact_and_tamper_closed(self) -> None:
        phase = self.unfinished_phase
        composition._validate_phase_A(phase)
        plan = composition.project_subjective_meaning_plan(phase)
        projection = response.seal_stage1_projection(phase, plan)
        response.build_surface_composition_inputs(phase, projection)

        self.assertEqual(
            len(phase.bounded_limited_subjective_proposition_records),
            1,
        )
        proposition = phase.bounded_limited_subjective_proposition_records[0]
        appraisal = proposition.appraisal_content
        self.assertIsNotNone(appraisal)
        assert appraisal is not None
        self.assertIs(appraisal.dimension, AppraisalDimension.UNFINISHED_OPENNESS)
        self.assertIs(appraisal.operation, AppraisalOperation.LEAVE_UNFINISHED)
        self.assertIsNone(appraisal.focal_relation_ref)
        self.assertIsNone(proposition.focal_relation_ref)
        self.assertEqual(appraisal.appraised_bindings, proposition.basis_binding_refs)
        self.assertEqual(
            appraisal.basis_contribution_refs,
            proposition.target_contribution_refs,
        )

        self.assertEqual(len(proposition.target_contribution_refs), 1)
        contribution_ref = proposition.target_contribution_refs[0]
        candidate_ref = dict(phase.contribution_to_candidate_ref_map)[
            contribution_ref
        ]
        candidate = next(
            row
            for row in phase.interpretation_candidate_rows
            if row.candidate_id == candidate_ref
        )
        self.assertIs(candidate.candidate_kind, InterpretationKind.BOUNDED_SOURCE_ORDER)
        self.assertIs(candidate.semantic_operator, SemanticOperator.PRESENT_UNFINISHED)
        self.assertIs(candidate.relation_operator, RelationOperator.NO_RELATION_CLAIM)
        self.assertEqual(len(candidate.relation_basis_refs), 1)
        self.assertEqual(
            tuple(binding.role for binding in candidate.argument_bindings),
            (ArgumentRole.BEFORE, ArgumentRole.AFTER),
        )
        self.assertEqual(
            tuple(binding.semantic_ref for binding in candidate.argument_bindings),
            candidate.semantic_refs,
        )

        candidate_index = phase.interpretation_candidate_rows.index(candidate)
        candidate_tampers = (
            replace(candidate, relation_basis_refs=()),
            replace(
                candidate,
                relation_basis_refs=(
                    *candidate.relation_basis_refs,
                    "edge:foreign",
                ),
            ),
            replace(
                candidate,
                argument_bindings=(
                    replace(candidate.argument_bindings[0], role=ArgumentRole.AFTER),
                    candidate.argument_bindings[1],
                ),
            ),
            replace(candidate, argument_bindings=tuple(reversed(candidate.argument_bindings))),
            replace(candidate, semantic_operator=SemanticOperator.PRESENT_STATE),
        )
        for index, tampered_candidate in enumerate(candidate_tampers):
            tampered_rows = list(phase.interpretation_candidate_rows)
            tampered_rows[candidate_index] = tampered_candidate
            with self.subTest(candidate_tamper=index):
                with self.assertRaises(composition.Stage1CompositionError):
                    composition._validate_phase_A(
                        replace(
                            phase,
                            interpretation_candidate_rows=tuple(tampered_rows),
                        )
                    )

        proposition_tampers = (
            replace(
                proposition,
                focal_relation_ref="edge:forged",
                appraisal_content=replace(
                    appraisal,
                    focal_relation_ref="edge:forged",
                ),
            ),
            replace(
                proposition,
                basis_binding_refs=("binding:foreign",),
                appraisal_content=replace(
                    appraisal,
                    appraised_bindings=("binding:foreign",),
                ),
            ),
        )
        for index, tampered_proposition in enumerate(proposition_tampers):
            with self.subTest(proposition_tamper=index):
                with self.assertRaises(composition.Stage1CompositionError):
                    composition._validate_phase_A(
                        replace(
                            phase,
                            bounded_limited_subjective_proposition_records=(
                                tampered_proposition,
                            ),
                        )
                    )

    def test_phase_a_rejects_order_duplicate_and_meaning_tamper(self) -> None:
        phase = self.phase
        premeaning = phase.premeaning_inputs
        tampers = (
            replace(
                phase,
                observation_contribution_rows=tuple(
                    reversed(phase.observation_contribution_rows)
                ),
            ),
            replace(
                phase,
                interpretation_candidate_rows=(
                    *phase.interpretation_candidate_rows,
                    phase.interpretation_candidate_rows[0],
                ),
            ),
            replace(
                phase,
                meaning_field=replace(
                    premeaning.meaning_field,
                    required_candidate_refs=tuple(
                        reversed(premeaning.meaning_field.required_candidate_refs)
                    ),
                ),
            ),
        )
        for index, tampered in enumerate(tampers):
            with self.subTest(tamper=index):
                with self.assertRaises(composition.Stage1CompositionError):
                    composition._validate_phase_A(tampered)


if __name__ == "__main__":
    unittest.main()
