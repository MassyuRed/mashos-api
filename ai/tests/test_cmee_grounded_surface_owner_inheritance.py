# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from dataclasses import replace
import inspect
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
)
import emlis_ai_grounded_observation_gate as gate_owner
import emlis_ai_grounded_sentence_surface as surface_owner
from emlis_ai_safety_triage import TRIAGE_SAFE_OBSERVATION
from cocolon_meaning_experience_engine.contracts import (
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    CMEEStage1ContractError,
    GenerationRequest,
    SubjectiveProjectionBranch,
    validate_stage1_projection,
    validate_stage1_sentence_unit,
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
import cocolon_meaning_experience_engine.emlis_v1a as v1a_module
from tools.cmee_v1a_i1sx_candidate_run import EXACT8


def _inputs(
    case_id: str,
    memo: str,
    category: str,
    emotion: str,
    strength: str,
):
    raw = {
        "id": f"cmee-grounded-owner-{case_id.lower()}",
        "created_at": "2026-09-01T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }
    request = GenerationRequest(
        request_id=f"req-grounded-owner-{case_id.lower()}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=str(raw["id"]),
    )
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
    return source, grounded_plan, graph, parent_plan


class CMEEGroundedSurfaceOwnerInheritanceTest(unittest.TestCase):
    def test_canonical_facade_has_no_independent_surface_call(self) -> None:
        facade_source = inspect.getsource(response.compile_stage1_response)
        facade_tree = ast.parse(facade_source)
        call_names = {
            (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            for node in ast.walk(facade_tree)
            if isinstance(node, ast.Call)
        }
        self.assertTrue(
            {
                "build_subjective_planning_inputs",
                "project_subjective_meaning_plan",
                "seal_stage1_projection",
                "build_grounded_sentence_plan",
                "build_reception_recovery_sentence_plan",
                "realize_source_grounded_human_reception",
                "realize_grounded_sentence_plan_with_human_reception",
                "evaluate_grounded_observation_gate",
                "evaluate_grounded_surface_body_inverse",
                "_adapt_grounded_surface_to_v2_realized_units",
            }
            <= call_names
        )
        self.assertTrue(
            {
                "build_surface_composition_inputs",
                "compose_stage1_from_projection",
            }.isdisjoint(call_names)
        )
        adapter_source = inspect.getsource(
            response._adapt_grounded_surface_to_v2_realized_units
        )
        self.assertNotIn("emlis_stage1_composition", adapter_source)
        self.assertFalse(
            hasattr(response, "_adapt_v2_composed_units_to_realized_units")
        )
        self.assertIn("compile_stage1_response", response.__all__)
        self.assertNotIn(
            "_compile_stage1_response_v1_legacy",
            response.__all__,
        )

        module_tree = ast.parse(
            Path(inspect.getsourcefile(response) or "").read_text(
                encoding="utf-8"
            )
        )
        legacy_node = next(
            row
            for row in module_tree.body
            if isinstance(row, ast.FunctionDef)
            and row.name == "_compile_stage1_response_v1_legacy"
        )
        self.assertEqual(
            sum(
                isinstance(row, ast.Call)
                and isinstance(row.func, ast.Name)
                and row.func.id == "_compile_stage1_response_v1_legacy"
                for row in ast.walk(module_tree)
            ),
            0,
        )
        self.assertTrue(legacy_node.name.startswith("_"))

    def test_exact8_use_canonical_recovery_candidates_and_trace_score(self) -> None:
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                source, grounded_plan, graph, parent_plan = _inputs(
                    case_id,
                    memo,
                    category,
                    emotion,
                    strength,
                )
                realized_surfaces = []
                selected_plans = []
                selected_reception_materials = []
                actual_realize = response.realize_grounded_sentence_plan_with_human_reception
                actual_author = response.realize_source_grounded_human_reception
                authored = []
                actual_reception_plan = v1a_module._cmee_semantic_reception_plan

                def track_realize(*args, **kwargs):
                    result = actual_realize(*args, **kwargs)
                    surface, placements = result
                    human = kwargs["human_reception_surface"]
                    self.assertIn(human, authored)
                    self.assertEqual(len(placements), len(human.visible_segment_bindings))
                    for placement, binding in zip(placements, human.visible_segment_bindings, strict=True):
                        self.assertEqual(placement.binding_ref, binding.binding_ref)
                        segment = human.text[binding.human_reception_local_scalar_start:binding.human_reception_local_scalar_end]
                        self.assertEqual(segment, surface.text[placement.body_scalar_start:placement.body_scalar_end])
                        self.assertEqual(hashlib.sha256(segment.encode("utf-8")).hexdigest(), binding.surface_span_sha256)
                    realized_surfaces.append(surface)
                    selected_plans.append(
                        kwargs.get("plan", args[1] if len(args) > 1 else None)
                    )
                    return result

                def track_author(*args, **kwargs):
                    result = actual_author(*args, **kwargs)
                    self.assertEqual(result.expression_refs, tuple(e.expression_ref for e in args[1]))
                    self.assertEqual(result.realized_move_ids, tuple(e.move_id for e in args[1]))
                    self.assertTrue(all(sum(e.expression_ref in binding.expression_refs for binding in result.visible_segment_bindings) == 1 for e in args[1]))
                    authored.append(result)
                    return result

                def track_reception_plan(*args, **kwargs):
                    if "material_quality" in kwargs:
                        selected_reception_materials.append(
                            kwargs["material_quality"]
                        )
                    return actual_reception_plan(*args, **kwargs)

                with (
                    patch.object(
                        response,
                        "realize_grounded_sentence_plan_with_human_reception",
                        side_effect=track_realize,
                    ) as grounded_realizer,
                    patch.object(response, "realize_source_grounded_human_reception", side_effect=track_author) as human_author,
                    patch.object(response, "realize_grounded_sentence_plan", side_effect=AssertionError("legacy final author reached")),
                    patch.object(
                        composition,
                        "compose_stage1_from_projection",
                        side_effect=AssertionError(
                            "independent final surface owner reached"
                        ),
                    ) as independent_composer,
                    patch.object(
                        v1a_module,
                        "_cmee_semantic_reception_plan",
                        side_effect=track_reception_plan,
                    ),
                ):
                    projection, units = response.compile_stage1_response(
                        source=source,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                        grounded_plan=grounded_plan,
                    )

                self.assertGreaterEqual(grounded_realizer.call_count, 2)
                self.assertEqual(human_author.call_count, grounded_realizer.call_count)
                self.assertEqual(independent_composer.call_count, 0)
                self.assertTrue(units)
                grounded_selected = bool(
                    projection.projection_branch
                    is SubjectiveProjectionBranch.NORMAL
                    and grounded_plan.input_profile.material_quality
                    == "grounded"
                    and grounded_plan.safety_policy.safety_kind
                    == TRIAGE_SAFE_OBSERVATION
                )
                expected_material_quality = (
                    "grounded" if grounded_selected else "limited_grounding"
                )
                expected_hedge_policy = (
                    "single_input_scope"
                    if grounded_selected
                    else "limited_single_input_scope"
                )
                self.assertTrue(selected_plans)
                self.assertTrue(
                    all(
                        plan.input_profile.material_quality
                        == expected_material_quality
                        for plan in selected_plans
                    )
                )
                self.assertTrue(
                    all(
                        plan.surface_policy.hedge_policy
                        == expected_hedge_policy
                        for plan in selected_plans
                    )
                )
                self.assertTrue(selected_reception_materials)
                self.assertTrue(
                    all(
                        material_quality == expected_material_quality
                        for material_quality in selected_reception_materials
                    )
                )
                self.assertNotIn(
                    "それ以上の出来事や理由は広げません。",
                    "\n".join(unit.text for unit in units),
                )
                selected_surface = next(
                    surface
                    for surface in realized_surfaces
                    if tuple(line.text for line in surface.lines)
                    == tuple(unit.text for unit in units)
                )
                if case_id in {"SX-06", "SX-07"}:
                    self.assertIs(
                        projection.projection_branch,
                        SubjectiveProjectionBranch.LIMITED,
                    )
                    observation_unit = next(
                        unit for unit in units if unit.layer == "LAYER_1"
                    )
                    relation_frames = tuple(
                        frame
                        for frame in observation_unit.clause_frames
                        if frame.discourse_relation.startswith("edge:")
                    )
                    self.assertEqual(
                        len(relation_frames),
                        len(
                            grounded_plan.coverage_requirements.required_relation_ids
                        ),
                    )
                    self.assertEqual(
                        len(
                            {
                                frame.discourse_relation
                                for frame in relation_frames
                            }
                        ),
                        len(relation_frames),
                    )
                    witness = surface_owner.parse_grounded_surface_body_bytes(
                        selected_surface.text.encode("utf-8")
                    )
                    observation_sentences = tuple(
                        sentence
                        for sentence in witness.sentences
                        if sentence.section == "observation"
                    )
                    self.assertGreaterEqual(
                        len(observation_sentences),
                        len(relation_frames),
                    )
                    edge_by_id = {edge.edge_id: edge for edge in graph.edges}
                    for sentence, frame in zip(
                        observation_sentences,
                        relation_frames,
                    ):
                        edge_id = frame.discourse_relation.removeprefix(
                            "edge:"
                        ).split("@", 1)[0]
                        self.assertIn(edge_id, edge_by_id)
                        relation_type = edge_by_id[edge_id].relation
                        allowed_markers = (
                            gate_owner._BODY_INVERSE_RELATION_MARKERS_BY_TYPE[
                                relation_type
                            ]
                        )
                        self.assertGreater(sentence.quote_count, 0)
                        self.assertTrue(
                            set(sentence.relation_marker_codes).intersection(
                                allowed_markers
                            )
                        )
                self.assertEqual(
                    tuple(unit.text for unit in units),
                    tuple(line.text for line in selected_surface.lines),
                )
                observation_anchors = tuple(
                    ref
                    for unit in units
                    if unit.layer == "LAYER_1"
                    for ref in unit.basis_anchor_refs
                )
                subjective_anchors = tuple(
                    ref
                    for unit in units
                    if unit.layer == "LAYER_2"
                    for ref in unit.basis_anchor_refs
                )
                self.assertEqual(
                    observation_anchors,
                    projection.ordered_observation_refs,
                )
                self.assertEqual(
                    subjective_anchors,
                    projection.ordered_subjective_refs,
                )
                prior_ids = []
                for unit in units:
                    validate_stage1_sentence_unit(
                        unit,
                        projection,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                        prior_unit_ids=tuple(prior_ids),
                    )
                    prior_ids.append(unit.unit_id)
                    seal = unit.v2_trace_seal
                    assert seal is not None
                    count_ref = next(
                        ref
                        for ref in seal.sentence_job_refs
                        if ref.startswith("hard-valid-candidate-count:")
                    )
                    score_ref = next(
                        ref
                        for ref in seal.sentence_job_refs
                        if ref.startswith("selection-score:")
                    )
                    self.assertGreaterEqual(int(count_ref.rsplit(":", 1)[1]), 2)
                    self.assertEqual(
                        len(score_ref.removeprefix("selection-score:").split(".")),
                        5,
                    )

    def test_reception_objects_are_derived_per_retained_act(self) -> None:
        case_id, memo, category, emotion, strength = next(
            row for row in EXACT8 if row[0] == "SX-08"
        )
        source, grounded_plan, graph, parent_plan = _inputs(
            case_id,
            memo,
            category,
            emotion,
            strength,
        )
        phase_a = response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        contributions = {
            row.contribution_id: row
            for row in phase_a.observation_contribution_rows
        }
        retained = {
            row.reception_act: row
            for row in phase_a.retained_reception_act_rows
        }
        receptions = phase_a.meaning_bound_reception_proposition_records
        self.assertEqual(
            tuple(row.reception_function for row in receptions),
            ("honor_concrete_effort", "recognize_lived_change"),
        )
        self.assertEqual(
            len({row.response_object_refs for row in receptions}),
            len(receptions),
        )
        self.assertEqual(
            len({row.responsibility_kind for row in receptions}),
            1,
        )
        for proposition in receptions:
            retained_row = retained[proposition.reception_function]
            expected_objects = _ordered(
                response_object_ref
                for contribution_ref in retained_row.basis_contribution_refs
                for response_object_ref in (
                    *contributions[contribution_ref].semantic_refs,
                    *contributions[contribution_ref].relation_basis_refs,
                )
            )
            self.assertEqual(
                proposition.response_object_refs,
                expected_objects,
            )

    def test_significance_protect_actual_keeps_relation_and_emlis_stance(
        self,
    ) -> None:
        source, grounded_plan, graph, parent_plan = _inputs(*EXACT8[6])
        _, units = response.compile_stage1_response(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        observation = next(
            unit.text for unit in units if unit.layer == "LAYER_1"
        )
        reception = next(
            unit.text for unit in units if unit.layer == "LAYER_2"
        )

        self.assertIn("異なる向き", observation)
        self.assertIn("だけで終わらない", observation)
        witness = surface_owner.parse_grounded_surface_body_bytes(
            (
                surface_owner.OBSERVATION_SECTION_LABEL + "\n" + observation
                + "\n\n" + surface_owner.RECEPTION_SECTION_LABEL + "\n" + reception
            ).encode("utf-8")
        )
        self.assertFalse(witness.structural_issues)
        codes = {marker.marker_code for marker in witness.markers if marker.section == "reception"}
        self.assertTrue({"protect", "receive", "target_intention"} <= codes)
        # The context is already an explicit relation endpoint. Require its
        # actual content once, rather than a duplicate background adjunct.
        context = next(n for n in grounded_plan.nuclei if n.kind == "reaction"
                       and n.nucleus_id in grounded_plan.coverage_requirements.required_nucleus_ids)
        context_text = next(str(span.raw_text).strip(" 、,。．.") for span in source.evidence_spans
                            if str(span.span_id) in context.source_span_ids)
        self.assertEqual(reception.count(context_text), 1)
        self.assertIn("違い", reception)
        self.assertEqual(reception.count("願い"), 1)

    def test_legacy_v1_compiler_is_schema_coherent_and_unreachable(self) -> None:
        source, grounded_plan, graph, parent_plan = _inputs(*EXACT8[0])
        projection, units = response._compile_stage1_response_v1_legacy(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        self.assertEqual(
            projection.schema_version,
            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
        )
        self.assertEqual(
            {
                row.schema_version
                for row in (
                    *projection.interpretation_candidates,
                    projection.meaning_field,
                    *projection.observation_contributions,
                    *projection.subjective_claims,
                )
            },
            {CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1},
        )
        validate_stage1_projection(
            projection,
            grounded_graph=graph,
            parent_plan=parent_plan,
        )
        self.assertTrue(units)
        self.assertNotIn(
            "_compile_stage1_response_v1_legacy",
            inspect.getsource(response.compile_stage1_response),
        )

    def test_body_inverse_failure_makes_every_candidate_hard_invalid(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[0]
        source, grounded_plan, graph, parent_plan = _inputs(
            case_id,
            memo,
            category,
            emotion,
            strength,
        )
        actual_inverse = response.evaluate_grounded_surface_body_inverse

        def reject_inverse(**kwargs):
            result = actual_inverse(**kwargs)
            return replace(
                result,
                passed=False,
                failure_codes=("test_forced_body_inverse_failure",),
            )

        with patch.object(
            response,
            "evaluate_grounded_surface_body_inverse",
            side_effect=reject_inverse,
        ):
            with self.assertRaisesRegex(
                CMEEStage1ContractError,
                "stage1_no_hard_valid_realization",
            ):
                response.compile_stage1_response(
                    source=source,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                    grounded_plan=grounded_plan,
                )


if __name__ == "__main__":
    unittest.main()
