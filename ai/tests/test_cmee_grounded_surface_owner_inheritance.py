# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from collections.abc import Mapping
from dataclasses import fields, replace
import hashlib
import inspect
from pathlib import Path
from typing import get_args, get_origin, get_type_hints
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
    validate_grounded_human_reception_plan,
)
import emlis_ai_grounded_observation_gate as gate_owner
import emlis_ai_grounded_human_reception as reception_owner
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
import cocolon_meaning_experience_engine.contracts as contracts_owner
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

        self.assertEqual(
            tuple(
                inspect.signature(
                    surface_owner.realize_grounded_sentence_plan
                ).parameters
            ),
            ("sentence_plan", "plan", "resolver"),
        )
        self.assertEqual(
            tuple(
                inspect.signature(
                    surface_owner.realize_grounded_sentence_plan_with_human_reception
                ).parameters
            ),
            (
                "sentence_plan",
                "plan",
                "resolver",
                "human_reception_surface",
            ),
        )
        self.assertTrue(
            {
                "_render_generic_final_reception_move",
                "_render_generic_final_stage1_human_follow",
                "_render_final_stage1_human_follow",
            }.isdisjoint(vars(surface_owner))
        )
        for verifier in (
            gate_owner.evaluate_grounded_observation_gate,
            gate_owner.evaluate_grounded_surface_body_inverse,
        ):
            self.assertTrue(
                {
                    "expressions",
                    "human_reception_surface",
                    "visible_segment_bindings",
                    "reception_placements",
                }.isdisjoint(inspect.signature(verifier).parameters)
            )

    def test_private_surface_carriers_hide_body_refs_and_locators_from_repr(
        self,
    ) -> None:
        private_body = "candidate-body-private-never-log"
        private_binding_ref = "binding-private-never-log"
        private_expression_ref = "expression-private-never-log"
        private_digest = "digest-private-never-log"
        binding = reception_owner.ReceptionVisibleSegmentBindingV1(
            binding_ref=private_binding_ref,
            expression_refs=(private_expression_ref,),
            move_ids=("move-private-never-log",),
            human_reception_local_scalar_start=0,
            human_reception_local_scalar_end=len(private_body),
            surface_span_sha256=private_digest,
            clause_frame_fields={"candidate": private_body},
            surface_derivation_refs=("derivation-private-never-log",),
        )
        human_surface = reception_owner.GroundedHumanReceptionSurface(
            text=private_body,
            terminal_predicate_kinds=("human_response_respect_words",),
            sentence_count=1,
            referent_kind="words_placed",
            realized_reception_acts=("respect_words_placed",),
            realized_move_ids=("move-private-never-log",),
            realized_move_roles=("felt_response",),
            move_predicate_families=("human_response_respect_words",),
            realized_clause_move_ids=(("move-private-never-log",),),
            grounded_nucleus_ids=("nucleus-private-never-log",),
            grounded_evidence_span_ids=("evidence-private-never-log",),
            source_anchor_count=0,
            source_anchor_max_visible_chars=0,
            recovery_stage="full",
            expression_refs=(private_expression_ref,),
            visible_segment_bindings=(binding,),
        )
        placement = surface_owner.SentenceSurfacePlacement(
            binding_ref=private_binding_ref,
            sentence_id="sentence-private-never-log",
            line_scalar_start=0,
            line_scalar_end=len(private_body),
            body_scalar_start=17,
            body_scalar_end=17 + len(private_body),
        )

        self.assertFalse(
            type(human_surface).__dataclass_params__.repr
        )
        self.assertFalse(type(placement).__dataclass_params__.repr)
        rendered = repr((human_surface, placement))
        for forbidden in (
            private_body,
            private_binding_ref,
            private_expression_ref,
            private_digest,
            "move-private-never-log",
            "nucleus-private-never-log",
            "evidence-private-never-log",
            "sentence-private-never-log",
            "human_reception_local_scalar_start=",
            "human_reception_local_scalar_end=",
            "line_scalar_start=",
            "line_scalar_end=",
            "body_scalar_start=",
            "body_scalar_end=",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_realizable_expression_v1_complete_identity_and_named_failures(
        self,
    ) -> None:
        self.assertEqual(
            reception_owner.SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION,
            "cocolon.emlis.human_reception.realizable_expression.v1",
        )
        self.assertEqual(
            get_args(
                get_type_hints(
                    reception_owner
                    .SourceGroundedRealizableReceptionExpressionV1
                )["schema_version"]
            ),
            ("cocolon.emlis.human_reception.realizable_expression.v1",),
        )
        self.assertEqual(
            tuple(
                field.name
                for field in fields(
                    reception_owner.RealizableReceptionArgumentV1
                )
            ),
            (
                "semantic_ref",
                "source_evidence_refs",
                "semantic_role",
                "lexical_form",
                "requirement",
                "omission_permission",
                "zero_realization_condition_refs",
                "omission_condition_refs",
                "case_marker",
                "direction_ref",
                "relation_endpoint_ref",
                "realization",
            ),
        )
        self.assertEqual(
            tuple(
                field.name
                for field in fields(
                    reception_owner.SourceGroundedRealizableReceptionExpressionV1
                )
            ),
            (
                "schema_version",
                "expression_ref",
                "meaning_outcome_ref",
                "reception_binding_ref",
                "move_id",
                "source_evidence_refs",
                "actor_refs",
                "subject_refs",
                "experiencer_refs",
                "predicate_kind",
                "lexical_head",
                "arguments",
                "polarity",
                "modality",
                "time_scope",
                "aspect",
                "degree",
                "quantity",
                "scope",
                "qualifier_refs",
                "relation_refs",
                "relation_endpoint_refs",
                "direction_refs",
                "reference_mode",
                "antecedent_refs",
                "antecedent_condition",
                "particle_plan",
                "inflection_plan",
                "nominalization_plan",
                "clause_link_plan",
                "provenance_refs",
            ),
        )
        self.assertEqual(
            tuple(
                field.name
                for field in fields(
                    reception_owner.ReceptionVisibleSegmentBindingV1
                )
            ),
            (
                "binding_ref",
                "expression_refs",
                "move_ids",
                "human_reception_local_scalar_start",
                "human_reception_local_scalar_end",
                "surface_span_sha256",
                "clause_frame_fields",
                "surface_derivation_refs",
            ),
        )
        self.assertIs(
            get_origin(
                get_type_hints(
                    reception_owner.ReceptionVisibleSegmentBindingV1
                )["clause_frame_fields"]
            ),
            Mapping,
        )

        semantic_ref = "node:reception-contract@cocolon.cmee.grounded_graph.v1"
        evidence_ref = "evidence:reception-contract"
        argument = reception_owner.RealizableReceptionArgumentV1(
            semantic_ref=semantic_ref,
            source_evidence_refs=(evidence_ref,),
            semantic_role="PRIMARY",
            lexical_form="少し休みたい",
            requirement="REQUIRED",
            omission_permission="FORBIDDEN",
            zero_realization_condition_refs=(),
            omission_condition_refs=(),
            case_marker="を",
            direction_ref=None,
            relation_endpoint_ref=None,
            realization="EXPLICIT",
        )
        outcome_ref = "selected-reading:reception-contract"
        reception_binding_ref = "meaning-bound-reception:reception-contract"
        draft = reception_owner.SourceGroundedRealizableReceptionExpressionV1(
            schema_version=(
                reception_owner
                .SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
            ),
            expression_ref="",
            meaning_outcome_ref=outcome_ref,
            reception_binding_ref=reception_binding_ref,
            move_id="rm1",
            source_evidence_refs=(evidence_ref,),
            actor_refs=(),
            subject_refs=(semantic_ref,),
            experiencer_refs=(),
            predicate_kind="present_state",
            lexical_head="少し休みたい",
            arguments=(argument,),
            polarity="affirmative",
            modality="wish",
            time_scope="current_input",
            aspect="source_bounded",
            degree="small",
            quantity="not_applicable",
            scope="source_bounded",
            qualifier_refs=("degree:small",),
            relation_refs=(),
            relation_endpoint_refs=(),
            direction_refs=(),
            reference_mode="EXPLICIT",
            antecedent_refs=(),
            antecedent_condition=None,
            particle_plan=("particle:PRIMARY:を",),
            inflection_plan=(
                "predicate:present_state",
                "polarity:affirmative",
                "modality:wish",
                "time:current_input",
                "aspect:source_bounded",
                "degree:small",
                "quantity:not_applicable",
                "scope:source_bounded",
                "focus-kind:wish",
                "head-class:source-grounded-proposition",
                "politeness:polite",
                "reception-form:full",
                "clause-form:FINITE",
            ),
            nominalization_plan=(
                "nominalization:source-grounded-reception-object",
            ),
            clause_link_plan=("clause-link:none",),
            provenance_refs=(outcome_ref, reception_binding_ref),
        )
        expression = (
            reception_owner.identify_source_grounded_reception_expression(
                draft
            )
        )
        reception_owner.validate_source_grounded_reception_expression(
            expression
        )
        self.assertNotIn("少し休みたい", repr(expression))

        for field in fields(type(expression)):
            if field.name == "expression_ref":
                continue
            value = getattr(expression, field.name)
            if field.name == "arguments":
                mutated_value = (
                    replace(argument, lexical_form="少し休みたくない"),
                )
            elif type(value) is tuple:
                mutated_value = (*value, "identity-tamper")
            elif value is None:
                mutated_value = "identity-tamper"
            else:
                mutated_value = f"{value}:identity-tamper"
            mutated = replace(
                expression,
                expression_ref="",
                **{field.name: mutated_value},
            )
            resealed = (
                reception_owner.identify_source_grounded_reception_expression(
                    mutated
                )
            )
            self.assertNotEqual(
                resealed.expression_ref,
                expression.expression_ref,
                field.name,
            )

        def reseal(**changes):
            return reception_owner.identify_source_grounded_reception_expression(
                replace(expression, expression_ref="", **changes)
            )

        shared_subject_zero = replace(
            argument,
            semantic_role="EXPERIENCER",
            case_marker="が",
            realization="ZERO",
            zero_realization_condition_refs=(
                "shared-subject:current-user",
            ),
        )
        shared_subject_expression = reseal(
            arguments=(argument, shared_subject_zero),
            experiencer_refs=(semantic_ref,),
            particle_plan=(
                "particle:PRIMARY:を",
                "particle:EXPERIENCER:が",
            ),
        )
        reception_owner.validate_source_grounded_reception_expression(
            shared_subject_expression
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "^MEANING_REALIZATION_CAUSAL_TRACE_GAP$",
        ):
            reception_owner._expression_source_grounded_move_realization(
                shared_subject_expression
            )
        self.assertEqual(
            tuple(
                (
                    row.semantic_role,
                    row.case_marker,
                    row.realization,
                )
                for row in shared_subject_expression.arguments
            ),
            (
                ("PRIMARY", "を", "EXPLICIT"),
                ("EXPERIENCER", "が", "ZERO"),
            ),
        )
        explicit_omission_alternative = replace(
            argument,
            requirement="OPTIONAL",
            omission_permission="PERMITTED",
            omission_condition_refs=("omission-duty:optional",),
        )
        reception_owner.validate_source_grounded_reception_expression(
            reseal(arguments=(explicit_omission_alternative,))
        )

        invalid_argument = replace(
            argument,
            realization="OMITTED",
        )
        named_failures = (
            (
                "MEANING_REALIZATION_CAPABILITY_GAP",
                reseal(lexical_head=""),
            ),
            (
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP",
                reseal(provenance_refs=(outcome_ref,)),
            ),
            (
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP",
                reseal(source_evidence_refs=()),
            ),
            (
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP",
                replace(expression, polarity="negative"),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP",
                reseal(arguments=(invalid_argument,)),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP",
                reseal(arguments=()),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP",
                reseal(
                    actor_refs=(),
                    subject_refs=(),
                    experiencer_refs=(),
                ),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP",
                reseal(clause_link_plan=()),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP",
                reseal(
                    inflection_plan=(
                        *expression.inflection_plan,
                        "inflection:foreign-extra-row",
                    )
                ),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP",
                reseal(
                    reference_mode="ANAPHORIC",
                    antecedent_refs=(),
                    antecedent_condition=None,
                ),
            ),
        )
        for failure, invalid in named_failures:
            with self.subTest(failure=failure):
                with self.assertRaisesRegex(
                    reception_owner.GroundedHumanReceptionSurfaceError,
                    f"^{failure}$",
                ):
                    reception_owner.validate_source_grounded_reception_expression(
                        invalid
                    )
        argument_gaps = (
            replace(
                argument,
                realization="ZERO",
                zero_realization_condition_refs=(),
            ),
            replace(
                argument,
                requirement="REQUIRED",
                omission_permission="PERMITTED",
                omission_condition_refs=("omission-duty:optional",),
            ),
            replace(
                argument,
                realization="ZERO",
                zero_realization_condition_refs=("foreign-condition:x",),
            ),
            replace(
                argument,
                realization="ZERO",
                zero_realization_condition_refs=(
                    "shared-subject:current-user",
                ),
            ),
            replace(
                argument,
                requirement="OPTIONAL",
                omission_permission="FORBIDDEN",
                omission_condition_refs=("omission-duty:optional",),
            ),
            replace(
                argument,
                requirement="OPTIONAL",
                omission_permission="PERMITTED",
                omission_condition_refs=(),
                realization="OMITTED",
            ),
            replace(
                argument,
                realization="ZERO",
                zero_realization_condition_refs=("omission-duty:optional",),
            ),
            replace(
                argument,
                realization="ZERO",
                zero_realization_condition_refs=(
                    "shared-subject:current-user",
                    "shared-subject:not-current-user",
                ),
            ),
            replace(
                argument,
                realization="ZERO",
                zero_realization_condition_refs=(
                    "shared-subject:current-user",
                    "shared-subject:current-user",
                ),
            ),
        )
        for invalid_argument_row in argument_gaps:
            with self.subTest(argument=invalid_argument_row):
                with self.assertRaisesRegex(
                    reception_owner.GroundedHumanReceptionSurfaceError,
                    "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
                ):
                    reception_owner.validate_source_grounded_reception_expression(
                        reseal(arguments=(invalid_argument_row,))
                    )

        additional_role_argument = replace(
            argument,
            semantic_role="EXPERIENCER",
            case_marker="が",
        )
        reception_owner.validate_source_grounded_reception_expression(
            reseal(
                arguments=(argument, additional_role_argument),
                experiencer_refs=(semantic_ref,),
                particle_plan=(
                    "particle:PRIMARY:を",
                    "particle:EXPERIENCER:が",
                ),
            )
        )
        conflicting_argument = replace(
            additional_role_argument,
            lexical_form="休息",
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
        ):
            reception_owner.validate_source_grounded_reception_expression(
                reseal(
                    arguments=(argument, conflicting_argument),
                    experiencer_refs=(semantic_ref,),
                    particle_plan=(
                        "particle:PRIMARY:を",
                        "particle:EXPERIENCER:が",
                    ),
                )
            )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
        ):
            reception_owner.validate_source_grounded_reception_expression(
                reseal(
                    arguments=(argument, argument),
                    particle_plan=(
                        "particle:PRIMARY:を",
                        "particle:PRIMARY:を",
                    ),
                )
            )

        malformed_rows = (
            (
                "MEANING_REALIZATION_CAPABILITY_GAP",
                reseal(lexical_head=None),
            ),
            (
                "MEANING_REALIZATION_CAPABILITY_GAP",
                reseal(actor_refs=(["not-hashable"],)),
            ),
            (
                "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP",
                reseal(
                    particle_plan=("particle:PRIMARY:を", 7),
                ),
            ),
        )
        for failure, malformed in malformed_rows:
            with self.subTest(malformed=failure):
                with self.assertRaisesRegex(
                    reception_owner.GroundedHumanReceptionSurfaceError,
                    f"^{failure}$",
                ):
                    reception_owner.validate_source_grounded_reception_expression(
                        malformed
                    )

    def test_resealed_foreign_expression_authority_fails_at_compiler_boundary(
        self,
    ) -> None:
        source, grounded_plan, graph, parent_plan = _inputs(
            *next(row for row in EXACT8 if row[0] == "SX-07")
        )
        actual_builder = response._build_source_grounded_reception_expressions

        def reseal(expression, **changes):
            return reception_owner.identify_source_grounded_reception_expression(
                replace(expression, expression_ref="", **changes)
            )

        def foreign_lineage(expressions):
            foreign_meaning_ref = "selected-meaning:foreign-unused"
            foreign_reception_ref = "reception-binding:foreign-unused"
            return tuple(
                reseal(
                    expression,
                    meaning_outcome_ref=foreign_meaning_ref,
                    reception_binding_ref=foreign_reception_ref,
                    provenance_refs=tuple(
                        foreign_meaning_ref
                        if ref == expression.meaning_outcome_ref
                        else foreign_reception_ref
                        if ref == expression.reception_binding_ref
                        else ref
                        for ref in expression.provenance_refs
                    ),
                )
                for expression in expressions
            )

        def foreign_evidence(expressions):
            tampered = []
            for expression in expressions:
                evidence_refs = _ordered(
                    ref
                    for argument in expression.arguments
                    for ref in argument.source_evidence_refs
                )
                foreign_by_ref = {
                    ref: f"evidence:foreign-unused-{index}"
                    for index, ref in enumerate(evidence_refs)
                }
                tampered_arguments = tuple(
                    replace(
                        argument,
                        source_evidence_refs=tuple(
                            foreign_by_ref[ref]
                            for ref in argument.source_evidence_refs
                        ),
                    )
                    for argument in expression.arguments
                )
                tampered.append(
                    reseal(
                        expression,
                        arguments=tampered_arguments,
                        source_evidence_refs=tuple(
                            foreign_by_ref[ref]
                            for ref in expression.source_evidence_refs
                        ),
                        provenance_refs=tuple(
                            foreign_by_ref.get(ref, ref)
                            for ref in expression.provenance_refs
                        ),
                    )
                )
            return tuple(tampered)

        def foreign_relations(expressions):
            tampered = []
            for expression in expressions:
                foreign_by_ref = {
                    ref: f"edge:foreign-unused-{index}"
                    for index, ref in enumerate(expression.relation_refs)
                }
                tampered_arguments = []
                for argument in expression.arguments:
                    if argument.relation_endpoint_ref is None:
                        tampered_arguments.append(argument)
                        continue
                    matching_refs = tuple(
                        relation_ref
                        for relation_ref in expression.relation_refs
                        if argument.relation_endpoint_ref
                        == reception_owner._source_grounded_relation_endpoint_ref(
                            relation_ref,
                            argument.semantic_ref,
                            argument.semantic_role,
                        )
                    )
                    self.assertEqual(len(matching_refs), 1)
                    relation_slot = expression.relation_refs.index(
                        matching_refs[0]
                    )
                    foreign_relation_ref = foreign_by_ref[
                        matching_refs[0]
                    ]
                    direction_side = reception_owner._source_grounded_direction_side(
                        expression.clause_link_plan[
                            relation_slot
                        ].removeprefix("relation-kind:"),
                        argument.semantic_role,
                    )
                    tampered_arguments.append(
                        replace(
                            argument,
                            relation_endpoint_ref=(
                                reception_owner
                                ._source_grounded_relation_endpoint_ref(
                                    foreign_relation_ref,
                                    argument.semantic_ref,
                                    argument.semantic_role,
                                )
                            ),
                            direction_ref=(
                                reception_owner._source_grounded_direction_ref(
                                    foreign_relation_ref,
                                    argument.semantic_ref,
                                    argument.semantic_role,
                                    direction_side,
                                )
                                if direction_side is not None
                                else None
                            ),
                        )
                    )
                argument_rows = tuple(tampered_arguments)
                tampered.append(
                    reseal(
                        expression,
                        arguments=argument_rows,
                        relation_refs=tuple(
                            foreign_by_ref[ref]
                            for ref in expression.relation_refs
                        ),
                        relation_endpoint_refs=_ordered(
                            argument.relation_endpoint_ref
                            for argument in argument_rows
                            if argument.relation_endpoint_ref is not None
                        ),
                        direction_refs=_ordered(
                            argument.direction_ref
                            for argument in argument_rows
                            if argument.direction_ref is not None
                        ),
                        provenance_refs=tuple(
                            foreign_by_ref.get(ref, ref)
                            for ref in expression.provenance_refs
                        ),
                    )
                )
            return tuple(tampered)

        def foreign_provenance(expressions):
            return tuple(
                reseal(
                    expression,
                    provenance_refs=(
                        *expression.provenance_refs,
                        f"provenance:foreign-unused-{index}",
                    ),
                )
                for index, expression in enumerate(expressions)
            )

        for mutation_name, mutate in (
            ("lineage", foreign_lineage),
            ("evidence", foreign_evidence),
            ("relations", foreign_relations),
            ("provenance", foreign_provenance),
        ):
            generic_validation_witnesses: list[bool] = []

            def build_with_foreign_authority(*args, **kwargs):
                expressions = actual_builder(*args, **kwargs)
                tampered_expressions = mutate(expressions)
                self.assertNotEqual(tampered_expressions, expressions)
                validated = (
                    reception_owner.validate_source_grounded_reception_expressions(
                        kwargs["reception_plan"],
                        tampered_expressions,
                        kwargs["recovery_stage"],
                    )
                )
                generic_validation_witnesses.append(
                    tuple(expression for _move, expression in validated)
                    == tampered_expressions
                )
                return tampered_expressions

            with self.subTest(mutation=mutation_name):
                with (
                    patch.object(
                        response,
                        "_build_source_grounded_reception_expressions",
                        side_effect=build_with_foreign_authority,
                    ),
                    self.assertRaisesRegex(
                        CMEEStage1ContractError,
                        "^MEANING_REALIZATION_CAUSAL_TRACE_GAP$",
                    ),
                ):
                    response.compile_stage1_response(
                        source=source,
                        grounded_graph=graph,
                        parent_plan=parent_plan,
                        grounded_plan=grounded_plan,
                    )
                self.assertEqual(generic_validation_witnesses, [True])

    def test_sx07_expression_ir_consumes_grammar_and_isolates_relation_evidence(
        self,
    ) -> None:
        source, grounded_plan, graph, parent_plan = _inputs(
            *next(row for row in EXACT8 if row[0] == "SX-07")
        )
        human_reception_calls = []
        actual_human_reception = (
            response.realize_source_grounded_human_reception
        )

        def track_human_reception(*args, **kwargs):
            result = actual_human_reception(*args, **kwargs)
            clause_plans = tuple(kwargs["clause_plans"])
            expected_clauses = (
                reception_owner._source_grounded_plan_clause_realizations(
                    args[0],
                    args[2],
                    args[3],
                    plan=kwargs["plan"],
                    recovery_stage=kwargs["recovery_stage"],
                    clause_plans=clause_plans,
                )
            )
            expected_by_move = {
                move_id: move_ir
                for clause_plan, clause_ir in zip(
                    clause_plans,
                    expected_clauses,
                    strict=True,
                )
                for move_id, move_ir in zip(
                    clause_plan.move_ids,
                    clause_ir.moves,
                    strict=True,
                )
            }
            human_reception_calls.append(
                (
                    kwargs["recovery_stage"],
                    tuple(args[1]),
                    expected_by_move,
                )
            )
            return result

        with patch.object(
            response,
            "realize_source_grounded_human_reception",
            side_effect=track_human_reception,
        ):
            response.compile_stage1_response(
                source=source,
                grounded_graph=graph,
                parent_plan=parent_plan,
                grounded_plan=grounded_plan,
            )

        expression, expected_move_ir = next(
            (expressions[0], expected_by_move[expressions[0].move_id])
            for recovery_stage, expressions, expected_by_move in human_reception_calls
            if recovery_stage == "integrated"
        )
        move_ir = reception_owner._expression_source_grounded_move_realization(
            expression,
            expected_relation_predicate_kinds=(
                expected_move_ir.relation_predicate_kinds
            ),
            expected_semantic_profiles=expected_move_ir.semantic_profiles,
            expected_target_slot_count=expected_move_ir.target_slot_count,
        )
        self.assertEqual(move_ir.reference_mode, "ANAPHORIC")
        self.assertEqual(len(move_ir.semantic_fragments), 2)
        self.assertEqual(len(move_ir.relations), 2)
        self.assertEqual(len(move_ir.arguments), 4)
        self.assertEqual(
            tuple(argument.semantic_slot for argument in move_ir.arguments),
            (0, 0, 1, 1),
        )
        self.assertEqual(
            {
                relation_slot: sum(
                    argument.relation_slot == relation_slot
                    for argument in move_ir.arguments
                )
                for relation_slot in range(len(move_ir.relations))
            },
            {0: 2, 1: 2},
        )
        argument_surface = reception_owner._source_grounded_argument_surface(
            move_ir
        )
        relation_morphemes = tuple(
            reception_owner._source_grounded_relation_predicate_morphemes(
                relation,
                predicate_kind=move_ir.predicate_kind,
            )
            for relation in move_ir.relations
        )
        relation_markers = tuple(
            finite for _continuative, finite in relation_morphemes
        )
        self.assertEqual(len(set(relation_markers)), 2)
        self.assertEqual(
            tuple(
                argument_surface.count(marker)
                for marker in relation_markers
            ),
            (1, 1),
        )
        self.assertLess(
            argument_surface.index(relation_markers[0]),
            argument_surface.index(relation_markers[1]),
        )

        node_by_ref = {
            response._node_ref(node.node_id): node for node in graph.nodes
        }
        edge_by_ref = {
            response._edge_ref(edge.edge_id): edge for edge in graph.edges
        }
        argument_relation_slots = []
        for argument in expression.arguments:
            relation_slots = tuple(
                relation_slot
                for relation_slot, relation_ref in enumerate(
                    expression.relation_refs
                )
                if argument.relation_endpoint_ref
                == reception_owner._source_grounded_relation_endpoint_ref(
                    relation_ref,
                    argument.semantic_ref,
                    argument.semantic_role,
                )
            )
            self.assertEqual(len(relation_slots), 1)
            relation_slot = relation_slots[0]
            argument_relation_slots.append(relation_slot)
            node_evidence_refs = tuple(
                response._evidence_ref(
                    evidence_id,
                    graph.source_version,
                )
                for evidence_id in node_by_ref[
                    argument.semantic_ref
                ].evidence_ids
            )
            relation_evidence_refs = tuple(
                response._evidence_ref(
                    evidence_id,
                    graph.source_version,
                )
                for evidence_id in edge_by_ref[
                    expression.relation_refs[relation_slot]
                ].evidence_ids
            )
            self.assertEqual(
                argument.source_evidence_refs,
                _ordered((*node_evidence_refs, *relation_evidence_refs)),
            )
        self.assertEqual(tuple(argument_relation_slots), (0, 1, 0, 1))
        relation_evidence_sets = tuple(
            {
                response._evidence_ref(
                    evidence_id,
                    graph.source_version,
                )
                for evidence_id in edge_by_ref[relation_ref].evidence_ids
            }
            for relation_ref in expression.relation_refs
        )
        first_relation_only = (
            relation_evidence_sets[0] - relation_evidence_sets[1]
        )
        self.assertTrue(first_relation_only)
        self.assertTrue(
            all(
                first_relation_only.isdisjoint(argument.source_evidence_refs)
                for argument, relation_slot in zip(
                    expression.arguments,
                    argument_relation_slots,
                    strict=True,
                )
                if relation_slot == 1
            )
        )
        self.assertEqual(
            expression.source_evidence_refs,
            _ordered(
                evidence_ref
                for argument in expression.arguments
                for evidence_ref in argument.source_evidence_refs
            ),
        )
        zero_endpoint_arguments = (
            replace(
                expression.arguments[0],
                realization="ZERO",
                zero_realization_condition_refs=(
                    "shared-subject:current-user",
                ),
            ),
            *expression.arguments[1:],
        )
        zero_endpoint_expression = (
            reception_owner.identify_source_grounded_reception_expression(
                replace(
                    expression,
                    expression_ref="",
                    arguments=zero_endpoint_arguments,
                )
            )
        )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
        ):
            reception_owner.validate_source_grounded_reception_expression(
                zero_endpoint_expression
            )

        arguments = move_ir.arguments
        argument_gap_mutations = (
            replace(
                move_ir,
                arguments=(arguments[1], arguments[0], *arguments[2:]),
            ),
            replace(
                move_ir,
                arguments=(
                    replace(arguments[0], case_marker="を"),
                    *arguments[1:],
                ),
            ),
            replace(
                move_ir,
                arguments=(
                    replace(arguments[0], relation_slot=1),
                    *arguments[1:],
                ),
            ),
            replace(
                move_ir,
                arguments=(
                    replace(arguments[0], direction_side="FROM"),
                    *arguments[1:],
                ),
            ),
            replace(
                move_ir,
                subject_slots=tuple(reversed(move_ir.subject_slots)),
            ),
        )
        for mutation in argument_gap_mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(
                    reception_owner.GroundedHumanReceptionSurfaceError,
                    "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
                ):
                    reception_owner._source_grounded_meaning_fragment(
                        mutation
                    )
        reference_gap_mutations = (
            replace(
                move_ir,
                antecedent_slots=tuple(
                    reversed(move_ir.antecedent_slots)
                ),
            ),
            replace(
                move_ir,
                antecedent_condition="FOREIGN_ANTECEDENT_CONDITION",
            ),
        )
        for mutation in reference_gap_mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(
                    reception_owner.GroundedHumanReceptionSurfaceError,
                    "^REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP$",
                ):
                    reception_owner._source_grounded_meaning_fragment(
                        mutation
                    )

    def test_explicit_user_stated_result_is_directional_and_gate_closed(
        self,
    ) -> None:
        source, grounded_plan, graph, parent_plan = _inputs(
            "USER-STATED-RESULT",
            "今日は仕事で疲れた。だから、早く休みたい。",
            "仕事",
            "不安",
            "medium",
        )
        result_relations = tuple(
            relation
            for relation in grounded_plan.relations
            if relation.type == "user_stated_result"
        )
        self.assertEqual(len(result_relations), 1)
        self.assertEqual(result_relations[0].retention, "required")
        self.assertIn(
            result_relations[0].relation_id,
            grounded_plan.coverage_requirements.required_relation_ids,
        )
        resolver = build_evidence_span_resolver(
            source.evidence_spans,
            current_input=source.normalized_current_input,
        )
        reception_plan = v1a_module._cmee_semantic_reception_plan(
            grounded_plan,
            resolver,
            material_quality=grounded_plan.input_profile.material_quality,
        )
        selected_plan = replace(
            grounded_plan,
            response_plan=replace(
                grounded_plan.response_plan,
                human_reception_plan=reception_plan,
            ),
        )
        active_moves = reception_owner.reception_active_moves(
            reception_plan,
            "integrated",
        )
        self.assertEqual(len(active_moves), 1)
        move = active_moves[0]
        target_id_set = set(move.target_nucleus_ids)
        applicable_relations = tuple(
            relation
            for relation in selected_plan.relations
            if relation.relation_id
            in selected_plan.coverage_requirements.required_relation_ids
            and target_id_set.intersection(
                (relation.from_nucleus_id, relation.to_nucleus_id)
            )
        )
        self.assertEqual(applicable_relations, result_relations)
        relation_context_ids = _ordered(
            nucleus_id
            for relation in applicable_relations
            for nucleus_id in (
                relation.from_nucleus_id,
                relation.to_nucleus_id,
            )
            if nucleus_id not in target_id_set
            and nucleus_id not in set(move.support_nucleus_ids)
        )
        semantic_nucleus_ids = _ordered(
            (
                *move.target_nucleus_ids,
                *move.support_nucleus_ids,
                *relation_context_ids,
            )
        )
        nucleus_index = {
            nucleus.nucleus_id: nucleus for nucleus in selected_plan.nuclei
        }
        owner_ir = (
            reception_owner._project_source_grounded_reception_move_realization(
                reception_plan,
                move,
                nucleus_index,
                resolver,
                plan=selected_plan,
                recovery_stage="integrated",
                clause_form="FINITE",
            )
        )
        self.assertEqual(len(owner_ir.relations), 1)
        self.assertEqual(
            owner_ir.relations[0].relation_kind,
            result_relations[0].type,
        )

        plan_binding = response._bind_grounded_plan(
            source,
            graph,
            selected_plan,
        )
        semantic_refs = tuple(
            response._node_ref(plan_binding.nucleus_to_node[nucleus_id])
            for nucleus_id in semantic_nucleus_ids
        )
        relation_ref = response._edge_ref(
            plan_binding.relation_to_edge[result_relations[0].relation_id]
        )
        node_by_id = {node.node_id: node for node in graph.nodes}
        relation_edge = next(
            edge
            for edge in graph.edges
            if edge.edge_id
            == plan_binding.relation_to_edge[result_relations[0].relation_id]
        )
        relation_evidence_refs = tuple(
            response._evidence_ref(evidence_id, graph.source_version)
            for evidence_id in relation_edge.evidence_ids
        )
        arguments = tuple(
            reception_owner.RealizableReceptionArgumentV1(
                semantic_ref=semantic_refs[argument.semantic_slot],
                source_evidence_refs=_ordered(
                    (
                        *(
                            response._evidence_ref(
                                evidence_id,
                                graph.source_version,
                            )
                            for evidence_id in node_by_id[
                                plan_binding.nucleus_to_node[
                                    semantic_nucleus_ids[
                                        argument.semantic_slot
                                    ]
                                ]
                            ].evidence_ids
                        ),
                        *(
                            relation_evidence_refs
                            if argument.relation_slot is not None
                            else ()
                        ),
                    )
                ),
                semantic_role=argument.semantic_role,
                lexical_form=argument.lexical_form,
                requirement="REQUIRED",
                omission_permission="FORBIDDEN",
                zero_realization_condition_refs=(
                    ("shared-subject:current-user",)
                    if argument.realization == "ZERO"
                    else ()
                ),
                omission_condition_refs=(),
                case_marker=argument.case_marker,
                direction_ref=(
                    reception_owner._source_grounded_direction_ref(
                        relation_ref,
                        semantic_refs[argument.semantic_slot],
                        argument.semantic_role,
                        argument.direction_side,
                    )
                    if argument.direction_side is not None
                    else None
                ),
                relation_endpoint_ref=(
                    reception_owner._source_grounded_relation_endpoint_ref(
                        relation_ref,
                        semantic_refs[argument.semantic_slot],
                        argument.semantic_role,
                    )
                    if argument.relation_slot is not None
                    else None
                ),
                realization=argument.realization,
            )
            for argument in owner_ir.arguments
        )
        meaning_outcome_ref = (
            "selected-grounded-relation:"
            f"{result_relations[0].relation_id}"
        )
        reception_binding_ref = (
            "selected-grounded-reception:"
            f"{move.move_id}:{result_relations[0].relation_id}"
        )
        expression = (
            reception_owner.identify_source_grounded_reception_expression(
                reception_owner.SourceGroundedRealizableReceptionExpressionV1(
                    schema_version=(
                        reception_owner
                        .SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
                    ),
                    expression_ref="",
                    meaning_outcome_ref=meaning_outcome_ref,
                    reception_binding_ref=reception_binding_ref,
                    move_id=move.move_id,
                    source_evidence_refs=_ordered(
                        evidence_ref
                        for argument in arguments
                        for evidence_ref in argument.source_evidence_refs
                    ),
                    actor_refs=tuple(
                        semantic_refs[index]
                        for index in owner_ir.actor_slots
                    ),
                    subject_refs=tuple(
                        semantic_refs[index]
                        for index in owner_ir.subject_slots
                    ),
                    experiencer_refs=tuple(
                        semantic_refs[index]
                        for index in owner_ir.experiencer_slots
                    ),
                    predicate_kind=owner_ir.predicate_kind,
                    lexical_head=owner_ir.predicate_head,
                    arguments=arguments,
                    polarity=owner_ir.polarity,
                    modality=owner_ir.modality,
                    time_scope=owner_ir.time_scope,
                    aspect=owner_ir.aspect,
                    degree=owner_ir.degree,
                    quantity=owner_ir.quantity,
                    scope=owner_ir.scope,
                    qualifier_refs=(),
                    relation_refs=(relation_ref,),
                    relation_endpoint_refs=_ordered(
                        argument.relation_endpoint_ref
                        for argument in arguments
                        if argument.relation_endpoint_ref is not None
                    ),
                    direction_refs=_ordered(
                        argument.direction_ref
                        for argument in arguments
                        if argument.direction_ref is not None
                    ),
                    reference_mode=owner_ir.reference_mode,
                    antecedent_refs=(
                        semantic_refs
                        if owner_ir.reference_mode == "ANAPHORIC"
                        else ()
                    ),
                    antecedent_condition=(
                        "PRIOR_LAYER1_EXACT_SEMANTIC_COVER"
                        if owner_ir.reference_mode == "ANAPHORIC"
                        else None
                    ),
                    particle_plan=tuple(
                        f"particle:{argument.semantic_role}:"
                        f"{argument.case_marker or 'ZERO'}"
                        for argument in arguments
                    ),
                    inflection_plan=(
                        f"predicate:{owner_ir.predicate_kind}",
                        f"polarity:{owner_ir.polarity}",
                        f"modality:{owner_ir.modality}",
                        f"time:{owner_ir.time_scope}",
                        f"aspect:{owner_ir.aspect}",
                        f"degree:{owner_ir.degree}",
                        f"quantity:{owner_ir.quantity}",
                        f"scope:{owner_ir.scope}",
                        "focus-kind:" + "+".join(owner_ir.focus_kinds),
                        "head-class:source-grounded-proposition",
                        "politeness:polite",
                        "reception-form:integrated",
                        "clause-form:FINITE",
                    ),
                    nominalization_plan=(
                        "nominalization:source-grounded-reception-object",
                    ),
                    clause_link_plan=(
                        f"relation-kind:{result_relations[0].type}",
                    ),
                    provenance_refs=(
                        meaning_outcome_ref,
                        reception_binding_ref,
                        relation_ref,
                    ),
                )
            )
        )
        reception_owner.validate_source_grounded_reception_expression(
            expression
        )
        self.assertEqual(expression.relation_refs, (relation_ref,))
        self.assertEqual(
            {argument.semantic_role for argument in expression.arguments},
            {"CAUSE", "EFFECT"},
        )
        self.assertEqual(len(expression.relation_endpoint_refs), 2)
        self.assertEqual(len(expression.direction_refs), 2)
        self.assertEqual(len(set(expression.direction_refs)), 2)
        for argument in expression.arguments:
            self.assertEqual(
                argument.case_marker,
                reception_owner.source_grounded_case_marker_for_role(
                    argument.semantic_role,
                    result_relations[0].type,
                ),
            )
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
            ):
                reception_owner.source_grounded_case_marker_for_role(
                    argument.semantic_role
                )

        move_ir = reception_owner._expression_source_grounded_move_realization(
            expression,
            expected_relation_predicate_kinds=(
                owner_ir.relation_predicate_kinds
            ),
            expected_semantic_profiles=owner_ir.semantic_profiles,
            expected_target_slot_count=owner_ir.target_slot_count,
        )
        self.assertEqual(move_ir, owner_ir)
        canonical_clause_plans = (
            reception_owner.build_grounded_reception_clause_plans(
                reception_plan,
                "integrated",
            )
        )
        canonical_clause_realizations = (
            reception_owner._source_grounded_plan_clause_realizations(
                reception_plan,
                nucleus_index,
                resolver,
                plan=selected_plan,
                recovery_stage="integrated",
                clause_plans=canonical_clause_plans,
            )
        )
        self.assertEqual(canonical_clause_realizations[0].moves, (owner_ir,))
        profile = owner_ir.semantic_profiles[0]
        tampered_profiles = (
            replace(
                profile,
                actor_kind=(
                    "OTHER" if profile.actor_kind != "OTHER" else "SELF"
                ),
            ),
            replace(
                profile,
                performed_action=False,
                future_action=not profile.future_action,
            ),
            replace(profile, quoted_boundary=not profile.quoted_boundary),
        )
        alternate_target_count = (
            2 if owner_ir.target_slot_count == 1 else 1
        )
        tampered_moves = tuple(
            replace(
                owner_ir,
                semantic_profiles=(
                    tampered_profile,
                    *owner_ir.semantic_profiles[1:],
                ),
            )
            for tampered_profile in tampered_profiles
        ) + (
            replace(owner_ir, target_slot_count=alternate_target_count),
            replace(
                owner_ir,
                time_scope=(
                    "past" if owner_ir.time_scope != "past" else "future"
                ),
            ),
            replace(
                owner_ir,
                aspect=(
                    "completed"
                    if owner_ir.aspect != "completed"
                    else "ongoing"
                ),
            ),
        )
        for tampered_move in tampered_moves:
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^MEANING_REALIZATION_CAUSAL_TRACE_GAP$",
            ):
                reception_owner._author_source_grounded_reception_clauses(
                    reception_plan,
                    canonical_clause_plans,
                    (
                        replace(
                            canonical_clause_realizations[0],
                            moves=(tampered_move,),
                        ),
                    ),
                    resolver,
                    plan=selected_plan,
                    nucleus_index=nucleus_index,
                    recovery_stage="integrated",
                )
        explicit_past = replace(
            owner_ir,
            reference_mode="EXPLICIT",
            time_scope="past",
            aspect="completed",
            semantic_heads=("確かめる", *owner_ir.semantic_heads[1:]),
            predicate_head="確かめる",
        )
        source_past = replace(
            explicit_past,
            semantic_heads=("確かめた", *explicit_past.semantic_heads[1:]),
            predicate_head="確かめた",
        )
        self.assertEqual(
            reception_owner._source_grounded_temporal_aspect_realization(
                source_past,
                "確かめた",
            ),
            ("SOURCE_CLAUSE", "SOURCE_CLAUSE", "", ""),
        )
        temporal_owner = (
            reception_owner._source_grounded_temporal_aspect_realization(
                explicit_past,
                "確かめる",
            )
        )
        self.assertEqual(temporal_owner[:2], ("ADJUNCT", "ADJUNCT"))
        temporal_adjunct, aspect_adjunct = temporal_owner[2:]
        axis_core = reception_owner._SourceGroundedClauseCoreV1(
            text=f"{temporal_adjunct}{aspect_adjunct}対象",
            target_referent="対象",
            semantic_slots=(0,),
            relation_count=0,
            target_owner_slot=0,
            temporal_realization="ADJUNCT",
            aspect_realization="ADJUNCT",
            temporal_adjunct=temporal_adjunct,
            aspect_adjunct=aspect_adjunct,
            voice="STATE",
        )
        reception_owner._validate_source_grounded_clause_core(
            axis_core,
            realization=explicit_past,
            target_owner_slot=0,
        )
        for invalid_text in (
            axis_core.text.replace(temporal_adjunct, "", 1),
            temporal_adjunct + axis_core.text,
        ):
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP$",
            ):
                reception_owner._validate_source_grounded_clause_core(
                    replace(axis_core, text=invalid_text),
                    realization=explicit_past,
                    target_owner_slot=0,
                )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "^REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP$",
        ):
            reception_owner._validate_source_grounded_clause_core(
                replace(
                    axis_core,
                    temporal_realization="SOURCE_CLAUSE",
                    temporal_adjunct="",
                ),
                realization=explicit_past,
                target_owner_slot=0,
            )
        with self.assertRaisesRegex(
            reception_owner.GroundedHumanReceptionSurfaceError,
            "^REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP$",
        ):
            reception_owner._validate_source_grounded_clause_core(
                replace(
                    axis_core,
                    text=f"任意に、{axis_core.text}",
                    temporal_adjunct="任意に、",
                ),
                realization=explicit_past,
                target_owner_slot=0,
            )
        source_core = replace(
            axis_core,
            text="確かめた対象",
            temporal_realization="SOURCE_CLAUSE",
            aspect_realization="SOURCE_CLAUSE",
            temporal_adjunct="",
            aspect_adjunct="",
        )
        reception_owner._validate_source_grounded_clause_core(
            source_core,
            realization=source_past,
            target_owner_slot=0,
        )
        anaphoric = replace(explicit_past, reference_mode="ANAPHORIC")
        anaphoric_core = replace(
            axis_core,
            text="対象",
            temporal_realization="ANTECEDENT",
            aspect_realization="ANTECEDENT",
            temporal_adjunct="",
            aspect_adjunct="",
        )
        reception_owner._validate_source_grounded_clause_core(
            anaphoric_core,
            realization=anaphoric,
            target_owner_slot=0,
        )
        self.assertEqual(
            reception_owner._source_grounded_temporal_aspect_realization(
                anaphoric,
                "確かめる",
            ),
            ("ANTECEDENT", "ANTECEDENT", "", ""),
        )
        profile_type = reception_owner._ReceptionSemanticProfileV1
        sole_content_profile = profile_type(
            "reaction",
            "SELF",
            "feeling",
            False,
            False,
            False,
        )
        self.assertEqual(
            reception_owner._source_grounded_target_owner_from_profiles(
                (sole_content_profile,),
                1,
                "lived_change",
            ),
            0,
        )
        for invalid_profiles, target_count, referent_kind in (
            (
                (sole_content_profile, sole_content_profile),
                2,
                "lived_change",
            ),
            ((sole_content_profile,), 1, "self_started_effort"),
            (
                (
                    profile_type(
                        "wish", "SELF", "wish", False, False, False
                    ),
                    sole_content_profile,
                ),
                1,
                "anchored_enacted_effort",
            ),
        ):
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP$",
            ):
                reception_owner._source_grounded_target_owner_from_profiles(
                    invalid_profiles,
                    target_count,
                    referent_kind,
                )
        valid_voice_rows = (
            (
                profile_type("action", "SELF", "action", False, True, False),
                "future_action_intention",
                "present_direction",
                "FUTURE_INTENTION",
            ),
            (
                profile_type("action", "SELF", "action", True, False, False),
                "self_started_effort",
                "present_actual_output",
                "SELF_PERFORMED",
            ),
            (
                profile_type("action", "OTHER", "action", True, False, False),
                "concrete_effort",
                "present_actual_output",
                "OTHER_PERFORMED",
            ),
            (
                profile_type("state", "OTHER", "state", False, False, False),
                "received_help",
                "present_state",
                "RECEIVED",
            ),
            (
                profile_type("constraint", "SELF", "constraint", False, False, False),
                "current_burden",
                "present_burden",
                "STATE",
            ),
        )
        for semantic_profile, referent_kind, predicate_kind, voice in valid_voice_rows:
            reception_owner._validate_source_grounded_predicate_voice(
                semantic_profile=semantic_profile,
                referent_kind=referent_kind,
                target_predicate_kind=predicate_kind,
                voice=voice,
            )
            invalid_voice = next(
                candidate
                for candidate in (
                    "STATE",
                    "SELF_PERFORMED",
                    "OTHER_PERFORMED",
                    "FUTURE_INTENTION",
                    "RECEIVED",
                )
                if candidate != voice
            )
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^MEANING_REALIZATION_CAPABILITY_GAP$",
            ):
                reception_owner._validate_source_grounded_predicate_voice(
                    semantic_profile=semantic_profile,
                    referent_kind=referent_kind,
                    target_predicate_kind=predicate_kind,
                    voice=invalid_voice,
                )
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^MEANING_REALIZATION_CAPABILITY_GAP$",
            ):
                reception_owner._validate_source_grounded_predicate_voice(
                    semantic_profile=semantic_profile,
                    referent_kind=referent_kind,
                    target_predicate_kind=(
                        "present_state"
                        if predicate_kind != "present_state"
                        else "present_direction"
                    ),
                    voice=voice,
                )
        self.assertEqual(
            tuple(
                (relation.relation_kind, relation.endpoint_roles)
                for relation in move_ir.relations
            ),
            (("user_stated_result", ("CAUSE", "EFFECT")),),
        )
        self.assertEqual(
            {argument.direction_side for argument in move_ir.arguments},
            {"FROM", "TO"},
        )
        from_index = next(
            index
            for index, argument in enumerate(expression.arguments)
            if argument.direction_ref
            == reception_owner._source_grounded_direction_ref(
                relation_ref,
                argument.semantic_ref,
                argument.semantic_role,
                "FROM",
            )
        )
        from_argument = expression.arguments[from_index]
        swapped_arguments = list(expression.arguments)
        swapped_arguments[from_index] = replace(
            from_argument,
            direction_ref=reception_owner._source_grounded_direction_ref(
                relation_ref,
                from_argument.semantic_ref,
                from_argument.semantic_role,
                "TO",
            ),
        )
        role_mismatch_arguments = list(expression.arguments)
        role_mismatch_arguments[from_index] = replace(
            from_argument,
            relation_endpoint_ref=(
                reception_owner._source_grounded_relation_endpoint_ref(
                    relation_ref,
                    from_argument.semantic_ref,
                    "EFFECT",
                )
            ),
        )
        wrong_case_arguments = list(expression.arguments)
        wrong_case_arguments[from_index] = replace(
            from_argument,
            case_marker=(
                reception_owner.source_grounded_case_marker_for_role(
                    from_argument.semantic_role,
                    "user_stated_cause",
                )
            ),
        )
        foreign_relation_ref = relation_ref.replace(
            "edge:",
            "edge:foreign-",
            1,
        )
        mutations = (
            replace(
                expression,
                expression_ref="",
                arguments=tuple(swapped_arguments),
                direction_refs=_ordered(
                    argument.direction_ref
                    for argument in swapped_arguments
                    if argument.direction_ref is not None
                ),
            ),
            replace(
                expression,
                expression_ref="",
                arguments=tuple(role_mismatch_arguments),
                relation_endpoint_refs=_ordered(
                    argument.relation_endpoint_ref
                    for argument in role_mismatch_arguments
                    if argument.relation_endpoint_ref is not None
                ),
            ),
            replace(
                expression,
                expression_ref="",
                relation_refs=(foreign_relation_ref,),
            ),
            replace(
                expression,
                expression_ref="",
                arguments=tuple(wrong_case_arguments),
                particle_plan=tuple(
                    f"particle:{argument.semantic_role}:"
                    f"{argument.case_marker or 'ZERO'}"
                    for argument in wrong_case_arguments
                ),
            ),
        )
        for mutation in mutations:
            resealed = (
                reception_owner.identify_source_grounded_reception_expression(
                    mutation
                )
            )
            self.assertNotEqual(resealed.expression_ref, expression.expression_ref)
            with self.assertRaisesRegex(
                reception_owner.GroundedHumanReceptionSurfaceError,
                "^REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP$",
            ):
                reception_owner._expression_source_grounded_move_realization(
                    resealed,
                    expected_relation_predicate_kinds=(
                        owner_ir.relation_predicate_kinds
                    ),
                    expected_semantic_profiles=owner_ir.semantic_profiles,
                    expected_target_slot_count=owner_ir.target_slot_count,
                )

    def test_exact8_use_canonical_recovery_candidates_and_trace_score(self) -> None:
        same_act_witnesses = []
        integrated_many_to_one_seed = None
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
                arranged_candidates = []
                human_reception_calls = []
                phase_a_outputs = []
                selected_plans = []
                selected_reception_materials = []
                actual_arrange = (
                    response.realize_grounded_sentence_plan_with_human_reception
                )
                actual_human_reception = (
                    response.realize_source_grounded_human_reception
                )
                actual_phase_a = response.build_subjective_planning_inputs
                actual_reception_plan = v1a_module._cmee_semantic_reception_plan

                def track_arrange(*args, **kwargs):
                    result = actual_arrange(*args, **kwargs)
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

                def track_phase_a(*args, **kwargs):
                    result = actual_phase_a(*args, **kwargs)
                    phase_a_outputs.append(result)
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
                        side_effect=track_arrange,
                    ) as grounded_arranger,
                    patch.object(
                        response,
                        "realize_source_grounded_human_reception",
                        side_effect=track_human_reception,
                    ) as human_reception_author,
                    patch.object(
                        response,
                        "build_subjective_planning_inputs",
                        side_effect=track_phase_a,
                    ),
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

                self.assertGreaterEqual(grounded_arranger.call_count, 2)
                self.assertEqual(
                    human_reception_author.call_count,
                    grounded_arranger.call_count,
                )
                self.assertEqual(len(phase_a_outputs), 1)
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
                (
                    selected_sentence_plan,
                    selected_grounded_plan,
                    selected_resolver,
                    selected_human_surface,
                    _selected_surface,
                    selected_placements,
                ) = next(
                    candidate
                    for candidate in arranged_candidates
                    if candidate[4] is selected_surface
                )
                (
                    selected_reception_plan,
                    selected_expressions,
                    selected_recovery_stage,
                    _selected_human_surface,
                ) = next(
                    call
                    for call in human_reception_calls
                    if call[3] is selected_human_surface
                )
                self.assertEqual(
                    selected_recovery_stage,
                    selected_sentence_plan.recovery_stage,
                )
                self.assertIs(
                    selected_grounded_plan.response_plan.human_reception_plan,
                    selected_reception_plan,
                )

                meaning_lineage_by_move: dict[
                    str,
                    set[tuple[str, str]],
                ] = {}
                source_span_by_evidence_ref = {
                    (
                        f"evidence:{evidence_ref.evidence_id}"
                        f"@{graph.source_version}"
                    ): evidence_ref.source_span_id
                    for evidence_ref in source.evidence_refs
                }
                for (
                    candidate_reception_plan,
                    expressions,
                    recovery_stage,
                    human_surface,
                ) in human_reception_calls:
                    active_moves = reception_owner.reception_active_moves(
                        candidate_reception_plan,
                        recovery_stage,
                    )
                    self.assertEqual(
                        tuple(expression.move_id for expression in expressions),
                        tuple(move.move_id for move in active_moves),
                    )
                    self.assertTrue(
                        {
                            move.move_id
                            for move in active_moves
                            if move.required
                        }.issubset(
                            expression.move_id for expression in expressions
                        )
                    )
                    self.assertEqual(
                        human_surface.expression_refs,
                        tuple(
                            expression.expression_ref
                            for expression in expressions
                        ),
                    )
                    for expression in expressions:
                        for argument in expression.arguments:
                            matching_primary = any(
                                other.semantic_ref == argument.semantic_ref
                                and other.semantic_role == "PRIMARY"
                                and other.relation_endpoint_ref is None
                                for other in expression.arguments
                            )
                            shared_subject_zero = bool(
                                argument.semantic_role == "EXPERIENCER"
                                and argument.relation_endpoint_ref is None
                                and matching_primary
                            )
                            if shared_subject_zero:
                                self.assertEqual(argument.realization, "ZERO")
                                self.assertEqual(
                                    argument.zero_realization_condition_refs,
                                    ("shared-subject:current-user",),
                                )
                            if argument.relation_endpoint_ref is not None:
                                self.assertEqual(
                                    argument.realization,
                                    "EXPLICIT",
                                )
                                self.assertFalse(
                                    argument.zero_realization_condition_refs
                                )
                        meaning_lineage_by_move.setdefault(
                            expression.move_id,
                            set(),
                        ).add(
                            (
                                expression.meaning_outcome_ref,
                                expression.reception_binding_ref,
                            )
                        )
                        self.assertEqual(
                            reception_owner
                            .identify_source_grounded_reception_expression(
                                replace(expression, expression_ref="")
                            )
                            .expression_ref,
                            expression.expression_ref,
                        )
                        self.assertEqual(
                            sum(
                                expression.expression_ref
                                in binding.expression_refs
                                for binding
                                in human_surface.visible_segment_bindings
                            ),
                            1,
                        )
                    if case_id == "SX-08" and recovery_stage == "integrated":
                        arranged_candidate = next(
                            candidate
                            for candidate in arranged_candidates
                            if candidate[3] is human_surface
                        )
                        integrated_many_to_one_seed = (
                            candidate_reception_plan,
                            tuple(expressions),
                            arranged_candidate[1],
                            arranged_candidate[2],
                        )
                    candidate_move_by_id = {
                        move.move_id: move for move in active_moves
                    }
                    for expression in expressions:
                        self.assertTrue(expression.source_evidence_refs)
                        self.assertTrue(
                            all(
                                evidence_ref in source_span_by_evidence_ref
                                for evidence_ref
                                in expression.source_evidence_refs
                            )
                        )
                        self.assertTrue(
                            set(
                                candidate_move_by_id[
                                    expression.move_id
                                ].source_evidence_span_ids
                            ).issubset(
                                source_span_by_evidence_ref[evidence_ref]
                                for evidence_ref
                                in expression.source_evidence_refs
                            )
                        )
                        self.assertTrue(
                            set(expression.source_evidence_refs).isdisjoint(
                                span.span_id for span in source.evidence_spans
                            )
                        )

                phase_a = phase_a_outputs[0]
                move_by_id = {
                    move.move_id: move
                    for move in selected_reception_plan.moves
                }
                normal_set_refs = tuple(
                    contracts_owner.meaning_bound_reception_set_id(
                        row,
                        proposition_records=(
                            phase_a.meaning_bound_reception_proposition_records
                        ),
                    )
                    for row in phase_a.meaning_bound_reception_set_records
                )
                limited_binding_refs = tuple(
                    contracts_owner.bounded_limited_reception_id(
                        bounded,
                        limited_outcome=(
                            phase_a.input_specific_meaning_structure
                            .meaning_decision_outcome
                        ),
                        subjective_proposition=subjective_proposition,
                    )
                    for bounded, subjective_proposition in zip(
                        phase_a.bounded_limited_reception_records,
                        phase_a.bounded_limited_subjective_proposition_records,
                        strict=True,
                    )
                )
                for expression in selected_expressions:
                    move = move_by_id[expression.move_id]
                    matching_traces = tuple(
                        trace
                        for trace
                        in projection.reception_visible_causal_trace_rows
                        if trace.meaning_outcome_ref
                        == expression.meaning_outcome_ref
                        and trace.reception_record_ref
                        == expression.reception_binding_ref
                        and trace.projected_claim_ref
                        in expression.provenance_refs
                    )
                    self.assertEqual(len(matching_traces), 1)
                    if projection.projection_branch is SubjectiveProjectionBranch.NORMAL:
                        matching_propositions = tuple(
                            proposition
                            for proposition
                            in phase_a.meaning_bound_reception_proposition_records
                            if proposition.reception_id
                            == expression.reception_binding_ref
                            and proposition.reception_function
                            == move.reception_act
                        )
                        self.assertEqual(len(matching_propositions), 1)
                        self.assertNotIn(
                            expression.reception_binding_ref,
                            normal_set_refs,
                        )
                        self.assertEqual(
                            sum(
                                set_ref in expression.provenance_refs
                                for set_ref in normal_set_refs
                            ),
                            1,
                        )
                        self.assertFalse(limited_binding_refs)
                    else:
                        self.assertIs(
                            projection.projection_branch,
                            SubjectiveProjectionBranch.LIMITED,
                        )
                        self.assertEqual(
                            limited_binding_refs,
                            (expression.reception_binding_ref,),
                        )
                        self.assertFalse(normal_set_refs)

                reception_unit = next(
                    unit for unit in units if unit.layer == "LAYER_2"
                )
                reception_line = next(
                    line
                    for line in selected_surface.lines
                    if line.binding.line_role == "human_follow"
                )
                self.assertEqual(
                    reception_unit.text,
                    selected_human_surface.text,
                )
                self.assertEqual(reception_line.text, reception_unit.text)
                self.assertEqual(
                    len(selected_human_surface.visible_segment_bindings),
                    len(selected_placements),
                )
                self.assertEqual(
                    len(reception_unit.clause_frames),
                    sum(
                        len(binding.expression_refs)
                        for binding
                        in selected_human_surface.visible_segment_bindings
                    ),
                )
                for binding, placement in zip(
                    selected_human_surface.visible_segment_bindings,
                    selected_placements,
                    strict=True,
                ):
                    local_segment = selected_human_surface.text[
                        binding.human_reception_local_scalar_start :
                        binding.human_reception_local_scalar_end
                    ]
                    line_segment = reception_unit.text[
                        placement.line_scalar_start : placement.line_scalar_end
                    ]
                    body_segment = selected_surface.text[
                        placement.body_scalar_start : placement.body_scalar_end
                    ]
                    self.assertEqual(
                        (local_segment, line_segment, body_segment),
                        (local_segment, local_segment, local_segment),
                    )
                    self.assertEqual(
                        hashlib.sha256(
                            local_segment.encode("utf-8")
                        ).hexdigest(),
                        binding.surface_span_sha256,
                    )
                    self.assertIsInstance(
                        binding.clause_frame_fields,
                        Mapping,
                    )
                    self.assertEqual(
                        tuple(binding.clause_frame_fields),
                        (
                            "semantic_refs",
                            "source_evidence_refs",
                            "predicate_operator",
                            "lexical_heads",
                            "topic_ref",
                            "object_ref",
                            "argument_bindings",
                            "qualifier_refs",
                            "relation_refs",
                            "relation_endpoint_refs",
                            "direction_refs",
                            "polarity",
                            "modality",
                            "time_scope",
                            "aspect",
                            "degree",
                            "quantity",
                            "scope",
                            "actor_refs",
                            "subject_refs",
                            "experiencer_refs",
                            "reference_modes",
                            "antecedent_refs",
                            "antecedent_conditions",
                            "particle_plans",
                            "inflection_plans",
                            "nominalization_plans",
                            "clause_link_plans",
                            "meaning_outcome_refs",
                            "reception_binding_refs",
                            "expression_frames",
                        ),
                    )
                    with self.assertRaises(TypeError):
                        binding.clause_frame_fields[
                            "meaning_outcome_refs"
                        ] = ()
                    self.assertEqual(placement.binding_ref, binding.binding_ref)
                    frames_for_binding = tuple(
                        frame
                        for frame in reception_unit.clause_frames
                        if binding.binding_ref in frame.qualifier_refs
                    )
                    self.assertEqual(
                        len(frames_for_binding),
                        len(binding.expression_refs),
                    )
                    self.assertTrue(
                        all(
                            binding.binding_ref in frame.qualifier_refs
                            and bool(
                                set(binding.expression_refs).intersection(
                                    frame.qualifier_refs
                                )
                            )
                            for frame in frames_for_binding
                        )
                    )
                    expression_by_ref = {
                        expression.expression_ref: expression
                        for expression in selected_expressions
                    }
                    for frame in frames_for_binding:
                        frame_expression_refs = tuple(
                            expression_ref
                            for expression_ref in binding.expression_refs
                            if expression_ref in frame.qualifier_refs
                        )
                        self.assertEqual(len(frame_expression_refs), 1)
                        frame_expression = expression_by_ref[
                            frame_expression_refs[0]
                        ]
                        self.assertEqual(
                            (
                                frame.predicate_operator,
                                frame.polarity,
                                frame.modality,
                                frame.time_scope,
                            ),
                            (
                                frame_expression.predicate_kind,
                                frame_expression.polarity,
                                frame_expression.modality,
                                frame_expression.time_scope,
                            ),
                        )
                        expression_semantic_refs = {
                            argument.semantic_ref
                            for argument in frame_expression.arguments
                        }
                        self.assertTrue(
                            {
                                argument.semantic_ref
                                for argument in frame.argument_bindings
                            }.issubset(expression_semantic_refs)
                        )
                        self.assertIn(
                            frame.topic_ref,
                            expression_semantic_refs,
                        )
                    self.assertEqual(
                        {
                            expression_ref
                            for frame in frames_for_binding
                            for expression_ref in binding.expression_refs
                            if expression_ref in frame.qualifier_refs
                        },
                        set(binding.expression_refs),
                    )
                    matching_public_bindings = tuple(
                        public_binding
                        for public_binding
                        in reception_unit.realized_semantic_bindings
                        if binding.binding_ref
                        in public_binding.clause_slot
                    )
                    self.assertTrue(matching_public_bindings)
                    self.assertTrue(
                        all(
                            (
                                public_binding.surface_scalar_start,
                                public_binding.surface_scalar_end,
                                public_binding.surface_span_sha256,
                            )
                            == (
                                placement.line_scalar_start,
                                placement.line_scalar_end,
                                binding.surface_span_sha256,
                            )
                            and all(
                                expression_ref
                                in public_binding.clause_slot
                                for expression_ref
                                in binding.expression_refs
                            )
                            for public_binding in matching_public_bindings
                        )
                    )
                if case_id == "SX-01":
                    first_binding = (
                        selected_human_surface.visible_segment_bindings[0]
                    )
                    tampered_human_surface = replace(
                        selected_human_surface,
                        visible_segment_bindings=(
                            replace(
                                first_binding,
                                surface_span_sha256="0" * 64,
                            ),
                            *selected_human_surface.visible_segment_bindings[1:],
                        ),
                    )
                    with self.assertRaisesRegex(
                        surface_owner.GroundedSentenceSurfaceError,
                        "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP",
                    ):
                        surface_owner.realize_grounded_sentence_plan_with_human_reception(
                            selected_sentence_plan,
                            selected_grounded_plan,
                            selected_resolver,
                            human_reception_surface=tampered_human_surface,
                        )
                same_act_witnesses.append(
                    (
                        tuple(
                            move.reception_act
                            for move in reception_owner.reception_active_moves(
                                selected_reception_plan,
                                selected_recovery_stage,
                            )
                        ),
                        tuple(
                            expression.meaning_outcome_ref
                            for expression in selected_expressions
                        ),
                        reception_unit.text,
                    )
                )
                self.assertTrue(
                    all(
                        len(lineages) == 1
                        for lineages in meaning_lineage_by_move.values()
                    ),
                    (case_id, meaning_lineage_by_move),
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

        self.assertIsNotNone(integrated_many_to_one_seed)
        assert integrated_many_to_one_seed is not None
        (
            base_reception_plan,
            base_expressions,
            base_grounded_plan,
            resolver,
        ) = integrated_many_to_one_seed
        self.assertEqual(len(base_expressions), 2)

        third_opportunity = replace(
            base_reception_plan.opportunities[1],
            opportunity_id="ro3",
            family="current_burden",
            reception_act="stay_with_current_burden",
        )
        third_move = replace(
            base_reception_plan.moves[1],
            move_id="rm3",
            reception_act="stay_with_current_burden",
            follow_elements=(
                "burden_understanding",
                "existence_respect",
            ),
            surface_strategy="quiet_referent_first",
            distinct_from_move_ids=("rm1", "rm2"),
        )
        integrated_reception_plan = replace(
            base_reception_plan,
            opportunities=(
                *base_reception_plan.opportunities,
                third_opportunity,
            ),
            depth_policy=replace(
                base_reception_plan.depth_policy,
                opportunity_count=3,
                selected_move_count=3,
                min_sentences=2,
                max_sentences=3,
                min_realized_moves=3,
                max_moves_per_sentence=2,
            ),
            moves=(*base_reception_plan.moves, third_move),
        )
        integrated_grounded_plan = replace(
            base_grounded_plan,
            response_plan=replace(
                base_grounded_plan.response_plan,
                human_reception_plan=integrated_reception_plan,
            ),
        )
        nucleus_index = {
            nucleus.nucleus_id: nucleus
            for nucleus in integrated_grounded_plan.nuclei
        }
        self.assertEqual(
            validate_grounded_human_reception_plan(
                integrated_reception_plan,
                expected_target_ids=(
                    integrated_reception_plan.target_nucleus_ids
                ),
                nucleus_index=nucleus_index,
                resolver=resolver,
                safety_kind=(
                    integrated_grounded_plan.safety_policy.safety_kind
                ),
                material_quality=(
                    integrated_grounded_plan.input_profile.material_quality
                ),
            ),
            (),
        )

        def with_clause_form(expression, clause_form):
            self.assertEqual(
                sum(
                    row.startswith("clause-form:")
                    for row in expression.inflection_plan
                ),
                1,
            )
            return (
                reception_owner.identify_source_grounded_reception_expression(
                    replace(
                        expression,
                        expression_ref="",
                        inflection_plan=tuple(
                            (
                                f"clause-form:{clause_form}"
                                if row.startswith("clause-form:")
                                else row
                            )
                            for row in expression.inflection_plan
                        ),
                    )
                )
            )

        first_expression = with_clause_form(
            base_expressions[0],
            "CONTINUATIVE",
        )
        second_expression = with_clause_form(
            base_expressions[1],
            "FINITE",
        )
        third_expression = (
            reception_owner.identify_source_grounded_reception_expression(
                replace(
                    second_expression,
                    expression_ref="",
                    move_id="rm3",
                )
            )
        )
        expressions = (
            first_expression,
            second_expression,
            third_expression,
        )
        clause_plans = reception_owner.build_grounded_reception_clause_plans(
            integrated_reception_plan,
            "integrated",
        )
        self.assertEqual(
            tuple(clause.move_ids for clause in clause_plans),
            (("rm1", "rm2"), ("rm3",)),
        )
        integrated_surface = (
            reception_owner.realize_source_grounded_human_reception(
                integrated_reception_plan,
                expressions,
                nucleus_index,
                resolver,
                plan=integrated_grounded_plan,
                recovery_stage="integrated",
                clause_plans=clause_plans,
            )
        )
        bindings = integrated_surface.visible_segment_bindings
        self.assertEqual(integrated_surface.sentence_count, 2)
        self.assertEqual(
            integrated_surface.realized_clause_move_ids,
            (("rm1", "rm2"), ("rm3",)),
        )
        self.assertEqual(len(bindings), 2)
        self.assertEqual(
            bindings[0].expression_refs,
            (first_expression.expression_ref, second_expression.expression_ref),
        )
        self.assertEqual(bindings[0].move_ids, ("rm1", "rm2"))
        self.assertEqual(
            bindings[1].expression_refs,
            (third_expression.expression_ref,),
        )
        self.assertEqual(bindings[1].move_ids, ("rm3",))
        self.assertEqual(
            tuple(
                expression_ref
                for binding in bindings
                for expression_ref in binding.expression_refs
            ),
            tuple(expression.expression_ref for expression in expressions),
        )
        self.assertEqual(
            (
                bindings[0].human_reception_local_scalar_start,
                bindings[0].human_reception_local_scalar_end,
                bindings[1].human_reception_local_scalar_start,
                bindings[1].human_reception_local_scalar_end,
            ),
            (
                0,
                bindings[1].human_reception_local_scalar_start,
                bindings[0].human_reception_local_scalar_end,
                len(integrated_surface.text),
            ),
        )
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
        body = (
            f"{surface_owner.OBSERVATION_SECTION_LABEL}\n{observation}\n\n"
            f"{surface_owner.RECEPTION_SECTION_LABEL}\n{reception}"
        ).encode("utf-8")
        body_witness = surface_owner.parse_grounded_surface_body_bytes(
            body
        )
        parsed_reception = next(
            row
            for row in body_witness.lines
            if row.section == "reception"
        )
        self.assertIn("coexistence", parsed_reception.relation_marker_codes)
        self.assertIn("target_intention", parsed_reception.reception_marker_codes)
        self.assertIn("protect", parsed_reception.reception_marker_codes)
        self.assertIn("receive", parsed_reception.reception_marker_codes)
        target_markers = tuple(
            marker
            for marker in body_witness.markers
            if marker.section == "reception"
            and marker.marker_kind == "reception"
            and marker.marker_code == "target_intention"
        )
        self.assertEqual(len(target_markers), 1)
        target_marker = target_markers[0]
        target_bytes = body[
            target_marker.utf8_byte_start : target_marker.utf8_byte_end
        ]
        self.assertTrue(target_bytes)
        self.assertEqual(body.count(target_bytes), 1)
        relation_marker = next(
            marker
            for marker in body_witness.markers
            if marker.section == "reception"
            and marker.marker_kind == "relation"
            and marker.marker_code == "coexistence"
        )
        protect_marker = min(
            (
                marker
                for marker in body_witness.markers
                if marker.section == "reception"
                and marker.marker_kind == "reception"
                and marker.marker_code == "protect"
                and marker.utf8_byte_start
                > max(
                    target_marker.utf8_byte_start,
                    relation_marker.utf8_byte_start,
                )
            ),
            key=lambda row: row.utf8_byte_start,
        )
        receive_marker = min(
            (
                marker
                for marker in body_witness.markers
                if marker.section == "reception"
                and marker.marker_kind == "reception"
                and marker.marker_code == "receive"
                and marker.utf8_byte_start > protect_marker.utf8_byte_start
            ),
            key=lambda row: row.utf8_byte_start,
        )
        self.assertLess(
            max(
                relation_marker.utf8_byte_start,
                target_marker.utf8_byte_start,
            ),
            protect_marker.utf8_byte_start,
        )
        self.assertLess(
            protect_marker.utf8_byte_start,
            receive_marker.utf8_byte_start,
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
