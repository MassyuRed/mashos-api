# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from dataclasses import replace
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
)
from cocolon_meaning_experience_engine.contracts import (
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    CMEEStage1ContractError,
    GenerationRequest,
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
                "realize_grounded_sentence_plan",
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
                actual_realize = response.realize_grounded_sentence_plan

                def track_realize(*args, **kwargs):
                    result = actual_realize(*args, **kwargs)
                    realized_surfaces.append(result)
                    return result

                with (
                    patch.object(
                        response,
                        "realize_grounded_sentence_plan",
                        side_effect=track_realize,
                    ) as grounded_realizer,
                    patch.object(
                        composition,
                        "compose_stage1_from_projection",
                        side_effect=AssertionError(
                            "independent final surface owner reached"
                        ),
                    ) as independent_composer,
                ):
                    projection, units = response.compile_stage1_response(
                        source=source,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                        grounded_plan=grounded_plan,
                    )

                self.assertGreaterEqual(grounded_realizer.call_count, 2)
                self.assertEqual(independent_composer.call_count, 0)
                self.assertTrue(units)
                self.assertEqual(
                    tuple(unit.text for unit in units),
                    next(
                        tuple(line.text for line in surface.lines)
                        for surface in realized_surfaces
                        if tuple(line.text for line in surface.lines)
                        == tuple(unit.text for unit in units)
                    ),
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
