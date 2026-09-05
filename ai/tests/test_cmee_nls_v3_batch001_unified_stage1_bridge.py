# -*- coding: utf-8 -*-
from __future__ import annotations

"""Canonical NLS v3 batch 001 bridge into the active CMEE Stage 1 owner.

The validated JSONL/manifest pair is the only case inventory.  The bridge has
no copied case table and asserts structure rather than expected surface text.
"""

import ast
from dataclasses import FrozenInstanceError, asdict, fields
import inspect
from pathlib import Path
from typing import Any, Mapping
import unittest
from unittest.mock import patch

import emlis_ai_current_input_bundle as current_input_module
from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
import emlis_ai_evidence_ledger_service as evidence_module
import emlis_ai_grounded_human_reception as grounded_reception_module
import emlis_ai_grounded_observation_gate as grounded_gate_module
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
)
import emlis_ai_grounded_observation_plan as grounded_plan_module
import emlis_ai_grounded_sentence_surface as grounded_surface_module
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    CMEE_STAGE1_EMLIS_OWNER_REF_V2,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2,
    CMEE_TERMINAL_GENERATED_DISABLED,
    EngineStatus,
    GenerationRequest,
    LimitedMeaningVisibleCausalTraceRow,
    SubjectiveProjectionBranch,
    SubjectivePropositionV2,
    validate_stage1_sentence_unit,
    validate_stage1_trace_spine,
)
import cocolon_meaning_experience_engine.engine as engine_module
from cocolon_meaning_experience_engine.emlis_v1a import (
    _build_experience_plan,
    _build_graph,
    _ordered,
    _planned_visible_source_ids,
)
import cocolon_meaning_experience_engine.emlis_v1a as vertical_module
import cocolon_meaning_experience_engine.emlis_stage1_composition as composition
import cocolon_meaning_experience_engine.emlis_stage1_response as response
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
import cocolon_meaning_experience_engine.source_kernel as source_kernel_module
from tools.emlis_nls_v3_batch_run import load_validated_batch


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
_BATCH_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"
_ADAPTER_SELECTED_AT = "2026-09-01T00:00:00Z"

_RUNTIME_OWNER_MODULES = (
    engine_module,
    vertical_module,
    response,
    composition,
    source_kernel_module,
    current_input_module,
    evidence_module,
    grounded_plan_module,
    grounded_surface_module,
    grounded_reception_module,
    grounded_gate_module,
)

_EXTERNAL_AI_OR_NETWORK_ROOTS = {
    "aiohttp",
    "anthropic",
    "boto3",
    "cohere",
    "google",
    "grpc",
    "httpx",
    "openai",
    "random",
    "requests",
    "socket",
    "tensorflow",
    "torch",
    "transformers",
    "urllib",
}


def _request_from_canonical_row(row: Mapping[str, Any]) -> GenerationRequest:
    case_id = str(row["case_id"])
    input_row = row["input"]
    if not isinstance(input_row, Mapping):
        raise TypeError("batch001_input_mapping_required")
    emotions = input_row["emotions"]
    if not isinstance(emotions, list) or any(
        not isinstance(item, Mapping) for item in emotions
    ):
        raise TypeError("batch001_emotions_list_required")
    raw = {
        "id": case_id,
        "created_at": _ADAPTER_SELECTED_AT,
        "memo": input_row["thought_text"],
        "memo_action": input_row["action_text"],
        "category": input_row["categories"],
        "emotion_details": emotions,
        "emotions": [str(item["type"]) for item in emotions],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-cmee-nls3-{case_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=case_id,
    )


def _unified_stage1_inputs(row: Mapping[str, Any]):
    request = _request_from_canonical_row(row)
    source = freeze_text_source(request)
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
    return request, source, grounded_plan, graph, parent_plan


def _imported_roots(module: object) -> set[str]:
    path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        str(node.module).split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }


class CMEENLSV3Batch001UnifiedStage1BridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows, cls.manifest = load_validated_batch(
            _BATCH_PATH,
            _MANIFEST_PATH,
        )

    def test_batch001_loader_and_adapter_keep_one_canonical_input_source(
        self,
    ) -> None:
        self.assertEqual(len(self.rows), 100)
        self.assertEqual(self.manifest["case_count"], 100)
        self.assertEqual(
            tuple(row["case_id"] for row in self.rows),
            tuple(self.manifest["case_ids"]),
        )
        self.assertEqual(
            Path(self.manifest["corpus_file_ref"]).as_posix(),
            "ai/tests/fixtures/emlis_nls_v3/generated/batch_001.jsonl",
        )
        for row in self.rows:
            with self.subTest(case_id=row["case_id"]):
                request = _request_from_canonical_row(row)
                bundle = request.current_input_bundle
                input_row = row["input"]
                self.assertEqual(bundle.source_record_id, row["case_id"])
                self.assertEqual(bundle.thought_text, input_row["thought_text"])
                self.assertEqual(bundle.action_text, input_row["action_text"])
                self.assertEqual(bundle.categories, tuple(input_row["categories"]))
                self.assertEqual(
                    tuple(
                        {"type": item.type, "strength": item.strength}
                        for item in bundle.emotions
                    ),
                    tuple(input_row["emotions"]),
                )

    def test_all100_inherit_premeaning_and_reach_selected_final_surface_gate(
        self,
    ) -> None:
        actual_realize = (
            response.realize_grounded_sentence_plan_with_human_reception
        )
        actual_human_reception = (
            response.realize_source_grounded_human_reception
        )
        actual_inverse = response.evaluate_grounded_surface_body_inverse
        actual_gate = response.evaluate_grounded_observation_gate
        actual_premeaning = response.build_premeaning_grounded_inputs
        actual_phase_a = response.build_subjective_planning_inputs
        actual_project = composition.project_subjective_meaning_plan
        actual_seal = response.seal_stage1_projection
        actual_selected_input = response._build_selected_subjective_reception_input
        actual_replay = grounded_gate_module.replay_source_grounded_human_reception_from_plan
        self.assertEqual(
            tuple(inspect.signature(actual_inverse).parameters),
            ("body", "plan", "sentence_plan", "resolver", "selected_subjective_input"),
        )
        self.assertEqual(
            tuple(inspect.signature(actual_gate).parameters),
            (
                "plan",
                "sentence_plan",
                "surface_result",
                "resolver",
                "product_readfeel_status",
                "require_body_inverse",
                "selected_subjective_input",
            ),
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    grounded_surface_module.realize_grounded_sentence_plan
                ).parameters
            ),
            ("sentence_plan", "plan", "resolver"),
        )
        self.assertEqual(
            tuple(inspect.signature(actual_realize).parameters),
            (
                "sentence_plan",
                "plan",
                "resolver",
                "human_reception_surface",
                "selected_subjective_input",
            ),
        )
        self.assertEqual(
            tuple(inspect.signature(grounded_surface_module.parse_grounded_surface_body_bytes).parameters),
            ("body",),
        )
        request_local_inputs: list[object] = []
        limited_trace_count = 0
        grounded_normal_count = 0
        full_move_count = 0
        full_expression_count = 0
        shared_subject_zero_count = 0
        same_act_witnesses: list[
            tuple[tuple[str, ...], tuple[str, ...], str]
        ] = []

        for row in self.rows:
            with self.subTest(case_id=row["case_id"]):
                request, source, grounded_plan, graph, parent_plan = (
                    _unified_stage1_inputs(row)
                )
                input_row = row["input"]
                self.assertEqual(
                    source.envelope.source_record_id,
                    request.expected_source_record_id,
                )
                self.assertEqual(
                    source.normalized_current_input["memo"],
                    input_row["thought_text"],
                )
                self.assertEqual(
                    source.normalized_current_input["memo_action"],
                    input_row["action_text"],
                )
                self.assertEqual(
                    source.normalized_current_input["category"],
                    input_row["categories"],
                )

                realized_surfaces: list[object] = []
                arranged_candidates: list[tuple[object, ...]] = []
                human_reception_calls: list[tuple[object, ...]] = []
                selected_plans: list[object] = []
                inverse_by_body: dict[bytes, list[object]] = {}
                gates_by_body: dict[bytes, list[object]] = {}
                premeaning_outputs: list[object] = []
                phase_a_inputs: list[object] = []
                project_calls: list[tuple[object, object]] = []
                seal_calls: list[tuple[object, object, object]] = []
                selected_inputs: list[object] = []
                selected_input_snapshots: list[object] = []
                replay_inputs: list[object] = []

                def track_premeaning(*args, **kwargs):
                    result = actual_premeaning(*args, **kwargs)
                    premeaning_outputs.append(result)
                    return result

                def track_phase_a(*args, **kwargs):
                    result = actual_phase_a(*args, **kwargs)
                    phase_a_inputs.append(result)
                    return result

                def track_project(phase_a):
                    result = actual_project(phase_a)
                    project_calls.append((phase_a, result))
                    return result

                def track_seal(phase_a, meaning_plan):
                    result = actual_seal(phase_a, meaning_plan)
                    seal_calls.append((phase_a, meaning_plan, result))
                    return result

                def track_selected_input(*args, **kwargs):
                    # The trusted input is exposed once, after the existing
                    # projection seal and before any generated body exists.
                    self.assertEqual(len(seal_calls), 1)
                    self.assertFalse(selected_inputs)
                    self.assertFalse(human_reception_calls)
                    self.assertFalse(realized_surfaces)
                    self.assertFalse(inverse_by_body)
                    result = actual_selected_input(*args, **kwargs)
                    self.assertIs(result, kwargs["authority_input"])
                    self.assertIs(type(result), grounded_reception_module.SelectedSubjectiveReceptionInputV1)
                    self.assertEqual(tuple(field.name for field in fields(result)), (
                        "input_ref", "projection_preimage_ref", "projection_seal_ref", "grounding_ref",
                        "semantic_nucleus_pairs", "relation_pairs", "decisions",
                    ))
                    self.assertIs(type(result.decisions), tuple)
                    self.assertTrue(result.decisions)
                    for decision in result.decisions:
                        self.assertIs(type(decision), grounded_reception_module.SelectedSubjectiveReceptionDecisionV1)
                        self.assertIs(type(decision.subjective_proposition), SubjectivePropositionV2)
                    for target, attribute in (
                        (result, "input_ref"),
                        (result.decisions[0], "decision_ref"),
                        (result.decisions[0].subjective_proposition, "epistemic_scope"),
                    ):
                        with self.assertRaises(FrozenInstanceError):
                            setattr(target, attribute, "changed")
                    self.assertTrue(all(result is not prior for prior in request_local_inputs))
                    request_local_inputs.append(result)
                    selected_inputs.append(result)
                    selected_input_snapshots.append(asdict(result))
                    return result

                def assert_selected_input(kwargs):
                    self.assertEqual(len(selected_inputs), 1)
                    self.assertIs(kwargs["selected_subjective_input"], selected_inputs[0])

                def track_replay(*args, **kwargs):
                    assert_selected_input(kwargs)
                    self.assertEqual(set(kwargs), {
                        "plan", "recovery_stage", "clause_plans", "selected_subjective_input",
                    })
                    replay_inputs.append(kwargs["selected_subjective_input"])
                    return actual_replay(*args, **kwargs)

                def track_realize(*args, **kwargs):
                    assert_selected_input(kwargs)
                    result = actual_realize(*args, **kwargs)
                    surface, placements = result
                    realized_surfaces.append(surface)
                    selected_plans.append(
                        kwargs.get("plan", args[1] if len(args) > 1 else None)
                    )
                    arranged_candidates.append(
                        (
                            args[0],
                            args[1],
                            args[2],
                            kwargs["human_reception_surface"],
                            surface,
                            placements,
                        )
                    )
                    return result

                def track_human_reception(*args, **kwargs):
                    assert_selected_input(kwargs)
                    result = actual_human_reception(*args, **kwargs)
                    human_reception_calls.append(
                        (
                            args[0],
                            tuple(args[1]),
                            kwargs["recovery_stage"],
                            result,
                        )
                    )
                    return result

                def track_inverse(*args, **kwargs):
                    assert_selected_input(kwargs)
                    self.assertTrue(
                        {
                            "expressions",
                            "human_reception_surface",
                            "visible_segment_bindings",
                            "reception_placements",
                        }.isdisjoint(kwargs)
                    )
                    result = actual_inverse(*args, **kwargs)
                    body = kwargs.get("body", args[0] if args else None)
                    if type(body) is bytes:
                        inverse_by_body.setdefault(body, []).append(result)
                    return result

                def track_gate(*args, **kwargs):
                    assert_selected_input(kwargs)
                    self.assertTrue(
                        {
                            "expressions",
                            "human_reception_surface",
                            "visible_segment_bindings",
                            "reception_placements",
                        }.isdisjoint(kwargs)
                    )
                    result = actual_gate(*args, **kwargs)
                    surface = kwargs.get("surface_result")
                    if surface is not None:
                        gates_by_body.setdefault(
                            surface.text.encode("utf-8"), []
                        ).append(result)
                    return result

                with (
                    patch.object(
                        response,
                        "build_premeaning_grounded_inputs",
                        side_effect=track_premeaning,
                    ),
                    patch.object(
                        response,
                        "build_subjective_planning_inputs",
                        side_effect=track_phase_a,
                    ),
                    patch.object(
                        composition,
                        "project_subjective_meaning_plan",
                        side_effect=track_project,
                    ),
                    patch.object(
                        response,
                        "seal_stage1_projection",
                        side_effect=track_seal,
                    ),
                    patch.object(
                        response,
                        "_build_selected_subjective_reception_input",
                        side_effect=track_selected_input,
                    ),
                    patch.object(
                        grounded_gate_module,
                        "replay_source_grounded_human_reception_from_plan",
                        side_effect=track_replay,
                    ),
                    patch.object(
                        response,
                        "realize_grounded_sentence_plan",
                        wraps=grounded_surface_module.realize_grounded_sentence_plan,
                    ) as base_realizer,
                    patch.object(
                        response,
                        "realize_grounded_sentence_plan_with_human_reception",
                        side_effect=track_realize,
                    ),
                    patch.object(
                        response,
                        "realize_source_grounded_human_reception",
                        side_effect=track_human_reception,
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
                    patch.object(
                        composition,
                        "compose_stage1_from_projection",
                        side_effect=AssertionError(
                            "composition surface fallback reached"
                        ),
                    ) as composition_surface_fallback,
                    patch.object(
                        response,
                        "_compile_stage1_response_v2_candidate",
                        side_effect=AssertionError(
                            "compatibility compiler reached"
                        ),
                    ) as compatibility_compiler,
                    patch.object(
                        response,
                        "_compile_stage1_response_v1_legacy",
                        side_effect=AssertionError("legacy Stage1 fallback reached"),
                    ) as legacy_compiler,
                    patch.object(
                        response,
                        "build_stage1_realization_candidate_set",
                        side_effect=AssertionError("legacy surface builder reached"),
                    ) as legacy_surface_builder,
                    patch.object(
                        response,
                        "select_stage1_realization_candidate",
                        side_effect=AssertionError("legacy surface selector reached"),
                    ) as legacy_surface_selector,
                ):
                    projection, units = response.compile_stage1_response(
                        source=source,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                        grounded_plan=grounded_plan,
                    )

                self.assertEqual(
                    projection.schema_version,
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
                )
                self.assertTrue(units)
                grounded_selected = bool(
                    projection.projection_branch
                    is SubjectiveProjectionBranch.NORMAL
                    and grounded_plan.input_profile.material_quality
                    == "grounded"
                    and grounded_plan.safety_policy.safety_kind
                    == TRIAGE_SAFE_OBSERVATION
                )
                grounded_normal_count += int(grounded_selected)
                expected_material_quality = (
                    "grounded" if grounded_selected else "limited_grounding"
                )
                self.assertTrue(selected_plans)
                self.assertTrue(
                    all(
                        plan.input_profile.material_quality
                        == expected_material_quality
                        for plan in selected_plans
                    )
                )
                self.assertNotIn(
                    "それ以上の出来事や理由は広げません。",
                    "\n".join(unit.text for unit in units),
                )
                self.assertEqual(len(premeaning_outputs), 1)
                self.assertEqual(len(phase_a_inputs), 1)
                self.assertEqual(len(project_calls), 1)
                self.assertEqual(len(seal_calls), 1)
                self.assertEqual(base_realizer.call_count, 0)
                captured_premeaning = premeaning_outputs[0]
                phase_a = phase_a_inputs[0]
                projected_plan_input, projected_plan = project_calls[0]
                sealed_phase_a, sealed_plan, sealed_projection = seal_calls[0]
                self.assertIs(phase_a.premeaning_inputs, captured_premeaning)
                self.assertIs(projected_plan_input, phase_a)
                self.assertIs(sealed_phase_a, phase_a)
                self.assertIs(sealed_plan, projected_plan)
                self.assertIs(sealed_projection, projection)
                self.assertEqual(len(selected_inputs), 1)
                selected_input = selected_inputs[0]
                self.assertEqual(asdict(selected_input), selected_input_snapshots[0])
                self.assertEqual(selected_input.projection_preimage_ref, phase_a.projection_preimage_ref)
                self.assertEqual(selected_input.projection_seal_ref, projection.projection_seal_ref)
                self.assertTrue(replay_inputs)
                self.assertTrue(all(value is selected_input for value in replay_inputs))
                claims = {claim.subjective_claim_id: claim for claim in projection.subjective_claims}
                for decision in selected_input.decisions:
                    claim = claims[decision.projected_claim_ref]
                    self.assertEqual(decision.branch, projection.projection_branch.value)
                    self.assertEqual(decision.selected_opportunity_ref, claim.selected_subjective_opportunity_key)
                    self.assertIs(decision.subjective_proposition, claim.asserted_subjective_proposition)
                premeaning = captured_premeaning
                for dormant_owner in (
                    composition_surface_fallback,
                    compatibility_compiler,
                    legacy_compiler,
                    legacy_surface_builder,
                    legacy_surface_selector,
                ):
                    self.assertEqual(dormant_owner.call_count, 0)

                self.assertEqual(
                    projection.interpretation_candidates,
                    phase_a.interpretation_candidate_rows,
                )
                self.assertEqual(
                    phase_a.interpretation_candidate_rows[
                        : len(premeaning.interpretation_candidate_rows)
                    ],
                    premeaning.interpretation_candidate_rows,
                )
                self.assertEqual(projection.meaning_field, premeaning.meaning_field)
                self.assertEqual(
                    projection.observation_contributions,
                    premeaning.observation_contribution_rows,
                )
                self.assertEqual(
                    projection.ordered_observation_refs,
                    premeaning.ordered_observation_refs,
                )
                self.assertIs(
                    projection.observation_depth_class,
                    premeaning.observation_depth_class,
                )

                self.assertEqual(
                    len(human_reception_calls),
                    len(arranged_candidates),
                )
                full_calls = tuple(
                    call
                    for call in human_reception_calls
                    if call[2] == "full"
                )
                self.assertEqual(len(full_calls), 1)
                (
                    full_reception_plan,
                    full_expressions,
                    _full_stage,
                    full_human_surface,
                ) = full_calls[0]
                full_moves = grounded_reception_module.reception_active_moves(
                    full_reception_plan,
                    "full",
                )
                self.assertEqual(
                    tuple(expression.move_id for expression in full_expressions),
                    tuple(move.move_id for move in full_moves),
                )
                self.assertTrue(all(move.required for move in full_moves))
                full_move_count += len(full_moves)
                full_expression_count += len(full_expressions)
                for expression in full_expressions:
                    for argument in expression.arguments:
                        matching_primary = any(
                            peer.semantic_ref == argument.semantic_ref
                            and peer.semantic_role == "PRIMARY"
                            and peer.relation_endpoint_ref is None
                            for peer in expression.arguments
                        )
                        if (
                            argument.semantic_role == "EXPERIENCER"
                            and argument.relation_endpoint_ref is None
                            and matching_primary
                        ):
                            self.assertEqual(argument.realization, "ZERO")
                            self.assertEqual(
                                argument.zero_realization_condition_refs,
                                ("shared-subject:current-user",),
                            )
                            shared_subject_zero_count += 1
                        if argument.relation_endpoint_ref is not None:
                            self.assertEqual(argument.realization, "EXPLICIT")
                            self.assertFalse(
                                argument.zero_realization_condition_refs
                            )
                for (
                    candidate_reception_plan,
                    expressions,
                    recovery_stage,
                    human_surface,
                ) in human_reception_calls:
                    active_moves = grounded_reception_module.reception_active_moves(
                        candidate_reception_plan,
                        recovery_stage,
                    )
                    self.assertEqual(
                        tuple(expression.move_id for expression in expressions),
                        tuple(move.move_id for move in active_moves),
                    )
                    self.assertEqual(
                        human_surface.expression_refs,
                        tuple(
                            expression.expression_ref
                            for expression in expressions
                        ),
                    )
                    self.assertTrue(
                        all(
                            sum(
                                expression.expression_ref
                                in binding.expression_refs
                                for binding
                                in human_surface.visible_segment_bindings
                            )
                            == 1
                            for expression in expressions
                        )
                    )
                full_private_body_free_values = {
                    selected_input.input_ref,
                    *(decision.decision_ref for decision in selected_input.decisions),
                    *(
                        expression.expression_ref
                        for expression in full_expressions
                    ),
                    *(
                        expression.lexical_head
                        for expression in full_expressions
                    ),
                    *(
                        evidence_ref
                        for expression in full_expressions
                        for evidence_ref in expression.source_evidence_refs
                    ),
                    *(
                        argument.lexical_form
                        for expression in full_expressions
                        for argument in expression.arguments
                    ),
                    *(
                        binding.binding_ref
                        for binding
                        in full_human_surface.visible_segment_bindings
                    ),
                    *(
                        binding.surface_span_sha256
                        for binding
                        in full_human_surface.visible_segment_bindings
                    ),
                }
                full_arrangement = next(
                    candidate
                    for candidate in arranged_candidates
                    if candidate[3] is full_human_surface
                )
                body_free_material = repr(
                    (
                        full_arrangement[0].as_body_free_meta(),
                        full_arrangement[4].as_body_free_meta(),
                    )
                )
                self.assertTrue(
                    all(
                        private_ref not in body_free_material
                        for private_ref in full_private_body_free_values
                    )
                )
                same_act_witnesses.append(
                    (
                        tuple(move.reception_act for move in full_moves),
                        tuple(
                            expression.meaning_outcome_ref
                            for expression in full_expressions
                        ),
                        full_human_surface.text,
                    )
                )

                selected_texts = tuple(unit.text for unit in units)
                selected_surfaces = tuple(
                    surface
                    for surface in realized_surfaces
                    if tuple(line.text for line in surface.lines) == selected_texts
                )
                self.assertTrue(selected_surfaces)
                selected_body = selected_surfaces[0].text.encode("utf-8")
                self.assertTrue(
                    any(
                        report.passed
                        for report in inverse_by_body.get(selected_body, ())
                    )
                )
                self.assertTrue(
                    any(
                        report.passed
                        for report in gates_by_body.get(selected_body, ())
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

                prior_ids: list[str] = []
                for unit in units:
                    validate_stage1_sentence_unit(
                        unit,
                        projection,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                        prior_unit_ids=tuple(prior_ids),
                    )
                    prior_ids.append(unit.unit_id)
                    self.assertIsNotNone(unit.v2_trace_seal)

                contribution_order = tuple(
                    contribution.contribution_id
                    for contribution in premeaning.observation_contribution_rows
                )
                limited_traces = tuple(
                    trace
                    for trace in projection.meaning_visible_causal_trace_rows
                    if type(trace) is LimitedMeaningVisibleCausalTraceRow
                )
                limited_trace_count += len(limited_traces)
                for trace in limited_traces:
                    retained = set(trace.layer1_contribution_refs)
                    expected_subsequence = tuple(
                        contribution_ref
                        for contribution_ref in contribution_order
                        if contribution_ref in retained
                    )
                    self.assertTrue(trace.layer1_contribution_refs)
                    self.assertEqual(
                        trace.layer1_contribution_refs,
                        expected_subsequence,
                    )
        self.assertEqual(len(request_local_inputs), 100)
        self.assertGreater(limited_trace_count, 0)
        # Source-owned uncertain modality re-derives one existing reading;
        # the selected meaning, trace and all124 Move bindings above still
        # have to agree with their original owner chain.
        self.assertEqual(grounded_normal_count, 5)
        self.assertEqual(full_move_count, 124)
        self.assertEqual(full_expression_count, 124)
        self.assertGreater(shared_subject_zero_count, 0)
        self.assertTrue(
            any(
                left_acts == right_acts
                and left_meaning != right_meaning
                and left_text != right_text
                for index, (
                    left_acts,
                    left_meaning,
                    left_text,
                ) in enumerate(same_act_witnesses)
                for right_acts, right_meaning, right_text
                in same_act_witnesses[index + 1 :]
            )
        )

    def test_all100_outer_engine_is_disabled_or_fail_closed_with_v2_trace(
        self,
    ) -> None:
        actual_compile = vertical_module.compile_stage1_response
        actual_human_reception = (
            response.realize_source_grounded_human_reception
        )
        positive_count = 0
        unavailable_count = 0
        unavailable_reasons = {
            "current_experiencer_or_time_scope_unsupported",
            "reception_negative_meaning_promotion",
            "plan_bound_observation_realizer_unavailable",
        }
        for row in self.rows:
            with self.subTest(case_id=row["case_id"]):
                compiled: list[tuple[object, object]] = []
                full_expression_rebuilds: list[tuple[object, ...]] = []

                def track_compile(*args, **kwargs):
                    result = actual_compile(*args, **kwargs)
                    compiled.append(result)
                    return result

                def track_human_reception(*args, **kwargs):
                    result = actual_human_reception(*args, **kwargs)
                    if kwargs["recovery_stage"] == "full":
                        full_expression_rebuilds.append(tuple(args[1]))
                    return result

                with (
                    patch.object(
                        vertical_module,
                        "compile_stage1_response",
                        side_effect=track_compile,
                    ),
                    patch.object(
                        response,
                        "realize_source_grounded_human_reception",
                        side_effect=track_human_reception,
                    ),
                ):
                    outcome = MeaningExperienceEngine().generate(
                        _request_from_canonical_row(row)
                    )

                self.assertFalse(outcome.automatic_progression)
                body_free = outcome.as_body_free()
                self.assertEqual(body_free["production_effect"], 0)
                self.assertFalse(body_free["candidate_ready"])
                self.assertFalse(body_free["product_read_eligible"])
                self.assertFalse(body_free["automatic_progression"])

                if outcome.status is EngineStatus.UNAVAILABLE:
                    unavailable_count += 1
                    self.assertEqual(len(outcome.reason_codes), 1)
                    reason = outcome.reason_codes[0]
                    self.assertIn(reason, unavailable_reasons)
                    self.assertEqual(
                        outcome.terminal_state,
                        "CMEE_V1A_I1SX_TEXT_GROUNDED_REALIZATION_"
                        "UNAVAILABLE_STOP",
                    )
                    self.assertIsNotNone(outcome.source_envelope)
                    self.assertIsNone(outcome.meaning_graph)
                    self.assertIsNone(outcome.artifact)
                    self.assertEqual(
                        len(compiled),
                        0
                        if reason
                        == "current_experiencer_or_time_scope_unsupported"
                        else 1,
                    )
                    continue

                positive_count += 1
                self.assertIn(
                    outcome.status,
                    (EngineStatus.GENERATED, EngineStatus.LIMITED),
                    outcome.reason_codes,
                )
                self.assertEqual(
                    outcome.terminal_state,
                    CMEE_TERMINAL_GENERATED_DISABLED,
                )
                self.assertIsNotNone(outcome.meaning_graph)
                self.assertIsNotNone(outcome.artifact)
                self.assertEqual(len(compiled), 2)
                artifact = outcome.artifact
                graph = outcome.meaning_graph
                assert artifact is not None and graph is not None
                projection = compiled[0][0]
                self.assertTrue(
                    all(result[0] == projection for result in compiled)
                )
                self.assertEqual(len(full_expression_rebuilds), 2)
                self.assertEqual(
                    full_expression_rebuilds[0],
                    full_expression_rebuilds[1],
                )
                validate_stage1_trace_spine(
                    artifact.trace,
                    projection,
                    grounded_graph=graph,
                    parent_plan=artifact.plan,
                )

                positive_extensions = tuple(
                    trace.emlis_stage1_extension
                    for trace in artifact.trace
                    if trace.role in {"OBSERVATION", "RECEPTION"}
                )
                self.assertTrue(positive_extensions)
                self.assertTrue(
                    all(
                        extension is not None
                        and extension.schema_version
                        == CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2
                        and extension.owner_ref == CMEE_STAGE1_EMLIS_OWNER_REF_V2
                        and extension.user_fact_effect == 0
                        and extension.covered_duty_refs
                        and extension.composition_candidate_ref
                        and extension.composition_layout_ref
                        and extension.selected_stage1_artifact_ref
                        for extension in positive_extensions
                    )
                )
        # Mash's source-fidelity exception: five formerly unavailable bodies
        # now pass the unchanged strict check after unsupported meaning was
        # removed. The canonical inputs, axes and denominator are unchanged.
        self.assertEqual(positive_count, 73)
        self.assertEqual(unavailable_count, 27)

    def test_runtime_owners_have_no_external_ai_or_batch_case_routing(
        self,
    ) -> None:
        for module in _RUNTIME_OWNER_MODULES:
            with self.subTest(module=module.__name__):
                self.assertTrue(
                    _EXTERNAL_AI_OR_NETWORK_ROOTS.isdisjoint(
                        _imported_roots(module)
                    )
                )

        owner_sources = tuple(
            (module.__name__, inspect.getsource(module))
            for module in _RUNTIME_OWNER_MODULES
        )
        for row in self.rows:
            case_id = str(row["case_id"])
            for module_name, source_text in owner_sources:
                with self.subTest(case_id=case_id, module=module_name):
                    self.assertNotIn(case_id, source_text)

        facade_tree = ast.parse(inspect.getsource(response.compile_stage1_response))
        call_names = {
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
            for node in ast.walk(facade_tree)
            if isinstance(node, ast.Call)
        }
        self.assertIn("build_subjective_planning_inputs", call_names)
        self.assertIn(
            "realize_source_grounded_human_reception",
            call_names,
        )
        self.assertIn(
            "realize_grounded_sentence_plan_with_human_reception",
            call_names,
        )
        self.assertIn("evaluate_grounded_surface_body_inverse", call_names)
        self.assertIn("evaluate_grounded_observation_gate", call_names)
        self.assertTrue(
            {
                "compose_stage1_from_projection",
                "_compile_stage1_response_v2_candidate",
                "_compile_stage1_response_v1_legacy",
                "build_stage1_realization_candidate_set",
                "select_stage1_realization_candidate",
            }.isdisjoint(call_names)
        )


if __name__ == "__main__":
    unittest.main()
