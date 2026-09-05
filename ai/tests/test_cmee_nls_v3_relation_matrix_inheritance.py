# -*- coding: utf-8 -*-
from __future__ import annotations

"""Truthful relation normalization and typed action-sequence inheritance."""

from dataclasses import replace
import hashlib
from pathlib import Path
from typing import Any, Mapping
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
import emlis_ai_grounded_observation_plan as observation_plan_owner
from emlis_ai_grounded_observation_plan import (
    build_final_stage1_grounded_observation_plan,
)
from emlis_ai_safety_triage import (
    EmlisSafetyTriageDecision,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)
from cocolon_meaning_experience_engine.contracts import (
    ArgumentRole,
    CMEEStage1ContractError,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    EpistemicState,
    GenerationRequest,
    InterpretationKind,
    RelationOperator,
    SemanticOperator,
)
from cocolon_meaning_experience_engine import contracts as contract_owner
from cocolon_meaning_experience_engine.emlis_v1a import (
    _build_experience_plan,
    _build_graph,
    _graph_id,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from cocolon_meaning_experience_engine import emlis_stage1_response as response
from cocolon_meaning_experience_engine import emlis_stage1_composition as composition
from tools.emlis_nls_v3_batch_run import load_validated_batch
from tools.cmee_v1a_i1sx_candidate_run import EXACT8


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
_BATCH_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"
_SELECTED_AT = "2026-09-01T00:00:00Z"


def _request(row: Mapping[str, Any]) -> GenerationRequest:
    case_id = str(row["case_id"])
    input_row = row["input"]
    if not isinstance(input_row, Mapping):
        raise TypeError("canonical_input_mapping_required")
    emotions = input_row["emotions"]
    if not isinstance(emotions, list) or any(
        not isinstance(item, Mapping) for item in emotions
    ):
        raise TypeError("canonical_emotions_list_required")
    raw = {
        "id": case_id,
        "created_at": _SELECTED_AT,
        "memo": input_row["thought_text"],
        "memo_action": input_row["action_text"],
        "category": input_row["categories"],
        "emotion_details": emotions,
        "emotions": [str(item["type"]) for item in emotions],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-cmee-relation-matrix-{case_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=case_id,
    )


class CMEENLSV3RelationMatrixInheritanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rows, manifest = load_validated_batch(_BATCH_PATH, _MANIFEST_PATH)
        if len(rows) != 100 or manifest["case_count"] != 100:
            raise AssertionError("canonical_batch001_exact100_required")
        cls.rows = {str(row["case_id"]): row for row in rows}

    def _source_plan(self, case_id: str):
        source = freeze_text_source(_request(self.rows[case_id]))
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        return source, plan

    def _exact8_source_plan(self, case_id: str):
        _case_id, memo, category, emotion, strength = next(
            row for row in EXACT8 if row[0] == case_id
        )
        raw = {
            "id": f"cmee-relation-matrix-{case_id.lower()}",
            "created_at": _SELECTED_AT,
            "memo": memo,
            "memo_action": "",
            "category": [category],
            "emotion_details": [
                {"type": emotion, "strength": strength}
            ],
            "emotions": [emotion],
            "is_secret": False,
        }
        source = freeze_text_source(
            GenerationRequest(
                request_id=f"req-cmee-relation-matrix-{case_id.lower()}",
                current_input_bundle=build_emlis_current_input_bundle(raw),
                expected_source_record_id=str(raw["id"]),
            )
        )
        plan = build_final_stage1_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        return source, plan

    def _candidate_inputs(self, case_id: str):
        source, plan = self._source_plan(case_id)
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
        return source, plan, graph, parent

    def _exact8_candidate_inputs(self, case_id: str):
        source, plan = self._exact8_source_plan(case_id)
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
        return source, plan, graph, parent

    def test_required14_preserve_type_endpoints_retention_and_lineage(self) -> None:
        expected = {
            "nls3s_b001_0035": (
                ("relation:r1", "uncertain_connection", "nucleus:s1", "nucleus:s2", ("whole_input_source_order",), ("whole_input:source_order",), ("s1", "s2")),
            ),
            "nls3s_b001_0062": (
                ("relation:r4", "continuation_or_refusal", "nucleus:s4", "nucleus:s5", ("whole_input_source_order",), ("whole_input:source_order",), ("s4", "s5")),
            ),
            "nls3s_b001_0064": (
                ("relation:r1", "wish_and_constraint", "nucleus:s5", "nucleus:s2", ("conflict.e1",), (), ("s2", "s5")),
                ("relation:r2", "preserves_despite", "nucleus:s3", "nucleus:s5", ("evidence_relation_marker:s4", "whole_input_source_order"), ("whole_input:source_order",), ("s3", "s4", "s5")),
            ),
            "nls3s_b001_0068": (
                ("relation:r1", "wish_and_constraint", "nucleus:s3", "nucleus:s1", ("conflict.e1",), (), ("s1", "s3")),
                ("relation:r2", "preserves_despite", "nucleus:s1", "nucleus:s3", ("evidence_relation_marker:s2", "whole_input_source_order"), ("whole_input:source_order",), ("s1", "s2", "s3")),
            ),
            "nls3s_b001_0070": (
                ("relation:r1", "wish_and_constraint", "nucleus:s2", "nucleus:s1", ("conflict.e1",), (), ("s1", "s2")),
                ("relation:r2", "uncertain_connection", "nucleus:s1", "nucleus:s2", ("whole_input_source_order",), ("whole_input:source_order",), ("s1", "s2")),
            ),
            "nls3s_b001_0077": (
                ("relation:r1", "wish_and_constraint", "nucleus:s1", "nucleus:s2", ("conflict.e1", "whole_input_source_order"), ("whole_input:source_order",), ("s1", "s2")),
            ),
            "nls3s_b001_0079": (
                ("relation:r1", "wish_and_constraint", "nucleus:s1", "nucleus:s2", ("conflict.e1", "whole_input_source_order"), ("whole_input:source_order",), ("s1", "s2")),
            ),
            "nls3s_b001_0083": (
                ("relation:r1", "wish_and_constraint", "nucleus:s2", "nucleus:s3", ("conflict.e1", "whole_input_source_order"), ("whole_input:source_order",), ("s2", "s3")),
            ),
            "nls3s_b001_0091": (
                ("relation:r1", "attempt_and_block", "nucleus:s2", "nucleus:s1", ("conflict.e1",), (), ("s1", "s2")),
            ),
            "nls3s_b001_0100": (
                ("relation:r1", "wish_and_constraint", "nucleus:s1", "nucleus:s2", ("whole_input_source_order",), ("whole_input:source_order",), ("s1", "s2")),
                ("relation:r2", "shift_from_to", "nucleus:s2", "nucleus:s3", ("whole_input_source_order",), ("whole_input:source_order",), ("s2", "s3")),
            ),
        }
        self.assertEqual(sum(map(len, expected.values())), 14)
        for case_id, expected_rows in expected.items():
            with self.subTest(case_id=case_id):
                _source, plan = self._source_plan(case_id)
                required_ids = set(
                    plan.coverage_requirements.required_relation_ids
                )
                actual = tuple(
                    (
                        row.relation_id,
                        row.type,
                        row.from_nucleus_id,
                        row.to_nucleus_id,
                        row.source_relation_ids,
                        row.source_meaning_arc_keys,
                        row.source_span_ids,
                    )
                    for row in plan.relations
                    if row.relation_id in {value[0] for value in expected_rows}
                )
                self.assertEqual(actual, expected_rows)
                self.assertTrue({row[0] for row in expected_rows} <= required_ids)
                for row in plan.relations:
                    if row.relation_id in {value[0] for value in expected_rows}:
                        self.assertEqual(row.grounding_kind, "user_stated_relation")
                        self.assertEqual(row.retention, "required")

    def test_0068_reverse_relations_keep_independent_lineage_and_marker_span(
        self,
    ) -> None:
        _source, plan = self._source_plan("nls3s_b001_0068")
        required_ids = set(plan.coverage_requirements.required_relation_ids)
        required = tuple(
            row for row in plan.relations if row.relation_id in required_ids
        )
        self.assertEqual(tuple(row.relation_id for row in required), ("relation:r1", "relation:r2"))
        first, second = required
        self.assertEqual(
            (first.type, first.from_nucleus_id, first.to_nucleus_id),
            ("wish_and_constraint", "nucleus:s3", "nucleus:s1"),
        )
        self.assertEqual(first.source_relation_ids, ("conflict.e1",))
        self.assertEqual(first.source_meaning_arc_keys, ())
        self.assertEqual(first.source_span_ids, ("s1", "s3"))
        self.assertEqual(
            (second.type, second.from_nucleus_id, second.to_nucleus_id),
            ("preserves_despite", "nucleus:s1", "nucleus:s3"),
        )
        self.assertEqual(
            second.source_relation_ids,
            ("evidence_relation_marker:s2", "whole_input_source_order"),
        )
        self.assertEqual(
            second.source_meaning_arc_keys,
            ("whole_input:source_order",),
        )
        self.assertEqual(second.source_span_ids, ("s1", "s2", "s3"))
        self.assertNotEqual(first.source_relation_ids, second.source_relation_ids)

    def test_required_relation_families_have_finite_v2_shapes(self) -> None:
        expected = {
            ("nls3s_b001_0035", "relation:r1"): (
                InterpretationKind.BOUNDED_SOURCE_ORDER,
                RelationOperator.NO_RELATION_CLAIM,
            ),
            ("nls3s_b001_0062", "relation:r4"): (
                InterpretationKind.DIRECTION_UNDER_BURDEN,
                RelationOperator.TENSION_WITH,
            ),
            ("nls3s_b001_0064", "relation:r1"): (
                InterpretationKind.COEXISTENCE,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0064", "relation:r2"): (
                InterpretationKind.TENSION,
                RelationOperator.TENSION_WITH,
            ),
            ("nls3s_b001_0068", "relation:r1"): (
                InterpretationKind.COEXISTENCE,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0068", "relation:r2"): (
                InterpretationKind.TENSION,
                RelationOperator.TENSION_WITH,
            ),
            ("nls3s_b001_0070", "relation:r1"): (
                InterpretationKind.COEXISTENCE,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0070", "relation:r2"): (
                InterpretationKind.BOUNDED_SOURCE_ORDER,
                RelationOperator.NO_RELATION_CLAIM,
            ),
            ("nls3s_b001_0077", "relation:r1"): (
                InterpretationKind.DIRECTION_UNDER_BURDEN,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0079", "relation:r1"): (
                InterpretationKind.DIRECTION_UNDER_BURDEN,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0083", "relation:r1"): (
                InterpretationKind.COEXISTENCE,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0091", "relation:r1"): (
                InterpretationKind.TENSION,
                RelationOperator.TENSION_WITH,
            ),
            ("nls3s_b001_0100", "relation:r1"): (
                InterpretationKind.DIRECTION_UNDER_BURDEN,
                RelationOperator.COEXISTS_WITH,
            ),
            ("nls3s_b001_0100", "relation:r2"): (
                InterpretationKind.SOURCE_STATED_TRANSITION,
                RelationOperator.TEMPORALLY_PRECEDES,
            ),
        }
        self.assertEqual(len(expected), 14)
        cached = {}
        for (case_id, relation_id), expected_shape in expected.items():
            with self.subTest(case_id=case_id, relation_id=relation_id):
                if case_id not in cached:
                    source, plan, graph, parent = self._candidate_inputs(case_id)
                    binding = response._bind_grounded_plan(source, graph, plan)
                    candidates = response.build_interpretation_candidate_pool(
                        graph,
                        parent,
                        source=source,
                        grounded_plan=plan,
                    )
                    cached[case_id] = (binding, candidates)
                binding, candidates = cached[case_id]
                edge_id = binding.relation_to_edge[relation_id]
                relation_ref = response._edge_ref(edge_id)
                rows = tuple(
                    row
                    for row in candidates
                    if row.relation_basis_refs == (relation_ref,)
                )
                self.assertEqual(len(rows), 1)
                self.assertEqual(
                    (rows[0].candidate_kind, rows[0].relation_operator),
                    expected_shape,
                )

    def test_0062_direction_under_burden_seal_replays_exact_endpoints(
        self,
    ) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0062"
        )
        raw_candidates = response.build_interpretation_candidate_pool(
            graph,
            parent,
            source=source,
            grounded_plan=plan,
        )
        raw_relation_candidate = next(
            row
            for row in raw_candidates
            if row.candidate_kind
            is InterpretationKind.DIRECTION_UNDER_BURDEN
            and row.relation_operator is RelationOperator.TENSION_WITH
        )
        phase_a = response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent,
            grounded_plan=plan,
        )
        candidates = phase_a.interpretation_candidate_rows
        relation_candidate = next(
            row
            for row in candidates
            if row.candidate_id == raw_relation_candidate.candidate_id
        )
        endpoint_seal = tuple(
            value
            for value in relation_candidate.required_qualifiers
            if "_qualifier:semantic_role:direction_under_burden_" in value
        )
        self.assertEqual(
            endpoint_seal,
            (
                "left_qualifier:semantic_role:direction_under_burden_direction",
                "right_qualifier:semantic_role:direction_under_burden_burden",
            ),
        )
        left_ref, right_ref = tuple(
            row.semantic_ref for row in relation_candidate.argument_bindings
        )
        direct_shapes: dict[
            str,
            set[tuple[InterpretationKind, SemanticOperator]],
        ] = {}
        direct_contracts: dict[str, tuple[str, ...]] = {}
        for row in candidates:
            if row.relation_basis_refs:
                continue
            semantic_ref = row.semantic_refs[0]
            direct_shapes.setdefault(semantic_ref, set()).add(
                (row.candidate_kind, row.semantic_operator)
            )
            direct_contracts[semantic_ref] = tuple(
                value
                for value in row.required_qualifiers
                if value.startswith("qualifier:")
            )
        self.assertEqual(
            direct_contracts[left_ref],
            (
                "qualifier:semantic_role:"
                "direction_under_burden_direction",
            ),
        )
        self.assertEqual(
            direct_contracts[right_ref],
            (
                "qualifier:semantic_role:"
                "direction_under_burden_burden",
            ),
        )
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_relation_source_contract_seal_invalid",
        ):
            contract_owner.project_stage1_relation_required_qualifiers(
                candidate_kind=(
                    InterpretationKind.DIRECTION_UNDER_BURDEN
                ),
                role_qualified_values=(
                    "epistemic:provisional_interpretation",
                    "left_qualifier:semantic_role:"
                    "direction_under_burden_foreign",
                ),
                source_attribute_codes=(
                    "semantic_role:direction_under_burden_direction",
                ),
                target_attribute_codes=(
                    "semantic_role:direction_under_burden_burden",
                ),
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            )
        node_by_id = {row.node_id: row for row in graph.nodes}
        edge_by_id = {row.edge_id: row for row in graph.edges}
        frozen_direct_shapes = {
            ref: frozenset(values) for ref, values in direct_shapes.items()
        }
        node_source_order = {
            row.node_id: index for index, row in enumerate(graph.nodes)
        }

        def validate_relation(
            candidate,
            *,
            edges=edge_by_id,
            contracts=direct_contracts,
        ) -> None:
            contract_owner._validate_stage1_relation_binding(
                candidate,
                edge_by_id=edges,
                node_by_id=node_by_id,
                node_source_order=node_source_order,
                direct_shapes_by_node_ref=frozen_direct_shapes,
                direct_source_contract_qualifiers_by_node_ref=contracts,
            )

        validate_relation(relation_candidate)
        left_seal, right_seal = endpoint_seal
        reversed_endpoint_candidate = replace(
            relation_candidate,
            required_qualifiers=(
                *(
                    value
                    for value in relation_candidate.required_qualifiers
                    if value not in endpoint_seal
                ),
                right_seal,
                left_seal,
            ),
        )
        forged_candidates = (
            replace(
                relation_candidate,
                required_qualifiers=tuple(
                    value
                    for value in relation_candidate.required_qualifiers
                    if value != left_seal
                ),
            ),
            replace(
                relation_candidate,
                required_qualifiers=tuple(
                    "right_qualifier:semantic_role:"
                    "direction_under_burden_direction"
                    if value == left_seal
                    else (
                        "left_qualifier:semantic_role:"
                        "direction_under_burden_burden"
                        if value == right_seal
                        else value
                    )
                    for value in relation_candidate.required_qualifiers
                ),
            ),
            replace(
                relation_candidate,
                required_qualifiers=tuple(
                    right_seal if value == left_seal else value
                    for value in relation_candidate.required_qualifiers
                ),
            ),
            reversed_endpoint_candidate,
            replace(
                relation_candidate,
                required_qualifiers=(
                    *relation_candidate.required_qualifiers,
                    "left_qualifier:semantic_role:"
                    "direction_under_burden_foreign",
                ),
            ),
            replace(
                relation_candidate,
                argument_bindings=tuple(
                    replace(
                        value,
                        semantic_ref=(
                            right_ref
                            if value.semantic_ref == left_ref
                            else left_ref
                        ),
                    )
                    for value in relation_candidate.argument_bindings
                ),
            ),
        )
        for forged in forged_candidates:
            with self.subTest(forged=forged):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_candidate_relation_binding_invalid",
                ):
                    validate_relation(forged)

        relation_edge_id = response._local_ref(
            relation_candidate.relation_basis_refs[0]
        )
        relation_edge = edge_by_id[relation_edge_id]
        reversed_edges = {
            **edge_by_id,
            relation_edge_id: replace(
                relation_edge,
                source_node_id=relation_edge.target_node_id,
                target_node_id=relation_edge.source_node_id,
            ),
        }
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_relation_binding_invalid",
        ):
            validate_relation(relation_candidate, edges=reversed_edges)
        # Edge order is transport lineage, while LEFT/RIGHT retain the finite
        # semantic roles.  A distinct reversed-edge source is therefore valid
        # only when its ordered source-contract seal reverses as one unit; the
        # unchanged seal above remains a directional tamper and fails closed.
        validate_relation(
            reversed_endpoint_candidate,
            edges=reversed_edges,
        )
        for forged_contracts in (
            {**direct_contracts, left_ref: ()},
            {
                **direct_contracts,
                left_ref: direct_contracts[right_ref],
            },
            {
                **direct_contracts,
                left_ref: (
                    "qualifier:semantic_role:"
                    "direction_under_burden_foreign",
                ),
            },
        ):
            with self.subTest(forged_contracts=forged_contracts):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_candidate_relation_binding_invalid",
                ):
                    validate_relation(
                        relation_candidate,
                        contracts=forged_contracts,
                    )

        projection = response.seal_stage1_projection(
            phase_a,
            composition.project_subjective_meaning_plan(phase_a),
        )
        self.assertIn(
            relation_candidate,
            projection.interpretation_candidates,
        )

    def test_direction_under_burden_raw_namespace_stops_before_set_normalization(
        self,
    ) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0062"
        )
        binding = response._bind_grounded_plan(source, graph, plan)
        edge_id = binding.relation_to_edge["relation:r4"]
        edge = next(row for row in graph.edges if row.edge_id == edge_id)
        source_nucleus = binding.node_meta[edge.source_node_id]
        target_nucleus = binding.node_meta[edge.target_node_id]
        direction_code = (
            "semantic_role:direction_under_burden_direction"
        )
        burden_code = "semantic_role:direction_under_burden_burden"
        namespace = "semantic_role:direction_under_burden_"

        def replace_codes(nucleus, codes):
            retained = tuple(
                value
                for value in nucleus.semantic_frame.attribute_codes
                if not value.startswith(namespace)
            )
            return replace(
                nucleus,
                semantic_frame=replace(
                    nucleus.semantic_frame,
                    attribute_codes=(*retained, *codes),
                ),
            )

        malformed_pairs = (
            ((direction_code, direction_code), (burden_code,)),
            ((f"{namespace}foreign",), (burden_code,)),
            ((direction_code, burden_code), (burden_code,)),
            ((direction_code,), ()),
            ((), (burden_code,)),
            ((direction_code,), (direction_code,)),
        )
        for source_codes, target_codes in malformed_pairs:
            with self.subTest(
                source_codes=source_codes,
                target_codes=target_codes,
            ):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_direction_under_burden_source_contract_invalid",
                ):
                    contract_owner.project_stage1_relation_required_qualifiers(
                        candidate_kind=(
                            InterpretationKind.DIRECTION_UNDER_BURDEN
                        ),
                        role_qualified_values=(
                            "epistemic:provisional_interpretation",
                        ),
                        source_attribute_codes=source_codes,
                        target_attribute_codes=target_codes,
                        stage1_response_schema_version=(
                            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                        ),
                    )

                changed_source = replace_codes(
                    source_nucleus,
                    source_codes,
                )
                changed_target = replace_codes(
                    target_nucleus,
                    target_codes,
                )
                changed_by_id = {
                    changed_source.nucleus_id: changed_source,
                    changed_target.nucleus_id: changed_target,
                }
                tampered_plan = replace(
                    plan,
                    nuclei=tuple(
                        changed_by_id.get(row.nucleus_id, row)
                        for row in plan.nuclei
                    ),
                )
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_direction_under_burden_source_contract_invalid",
                ):
                    source_qualifiers = (
                        contract_owner
                        ._foreground_source_qualifiers_by_node_ref(
                            source=source,
                            grounded_plan=tampered_plan,
                            grounded_graph=graph,
                            parent_plan=parent,
                            stage1_response_schema_version=(
                                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                            ),
                        )
                    )
                    contract_owner._foreground_expected_layer1(
                        source=source,
                        grounded_plan=tampered_plan,
                        grounded_graph=graph,
                        parent_plan=parent,
                        source_qualifiers_by_node_ref=source_qualifiers,
                        stage1_response_schema_version=(
                            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                        ),
                    )

        self.assertEqual(
            contract_owner.project_stage1_relation_source_contract_qualifiers(
                candidate_kind=(
                    InterpretationKind.DIRECTION_UNDER_BURDEN
                ),
                source_attribute_codes=(),
                target_attribute_codes=(),
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            ),
            (),
        )

    def test_0062_full_rehash_rejects_coordinated_endpoint_role_laundering(
        self,
    ) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0062"
        )
        phase_a = response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent,
            grounded_plan=plan,
        )
        projection = response.seal_stage1_projection(
            phase_a,
            composition.project_subjective_meaning_plan(phase_a),
        )
        relation_candidate = next(
            row
            for row in projection.interpretation_candidates
            if row.candidate_kind
            is InterpretationKind.DIRECTION_UNDER_BURDEN
            and row.relation_operator is RelationOperator.TENSION_WITH
        )
        left_ref, right_ref = tuple(
            row.semantic_ref for row in relation_candidate.argument_bindings
        )
        direction_marker = (
            "qualifier:semantic_role:direction_under_burden_direction"
        )
        burden_marker = (
            "qualifier:semantic_role:direction_under_burden_burden"
        )
        direct_by_ref = {
            row.semantic_refs[0]: row
            for row in projection.interpretation_candidates
            if not row.relation_basis_refs
            and row.semantic_refs[0] in {left_ref, right_ref}
            and set(row.required_qualifiers)
            & {direction_marker, burden_marker}
        }
        self.assertEqual(set(direct_by_ref), {left_ref, right_ref})

        relation_edge_id = response._local_ref(
            relation_candidate.relation_basis_refs[0]
        )
        relation_edge = next(
            row for row in graph.edges if row.edge_id == relation_edge_id
        )
        reversed_edges = tuple(
            replace(
                row,
                source_node_id=row.target_node_id,
                target_node_id=row.source_node_id,
            )
            if row.edge_id == relation_edge_id
            else row
            for row in graph.edges
        )
        forged_graph = replace(
            graph,
            graph_id=_graph_id(
                graph.source_envelope_id,
                graph.owner_universe_digest,
                graph.nodes,
                reversed_edges,
                graph.owner_dispositions,
            ),
            edges=reversed_edges,
        )

        def identify_candidate(row):
            blank = replace(row, candidate_id="")
            return replace(
                blank,
                candidate_id=contract_owner.recompute_stage1_identity(blank),
            )

        def rehash_support_shape(direct, **changes):
            changed_direct = identify_candidate(
                replace(direct, **changes)
            )
            changed_candidates = tuple(
                changed_direct
                if row.candidate_id == direct.candidate_id
                else row
                for row in projection.interpretation_candidates
            )
            changed_preimage = (
                contract_owner.project_stage1_projection_preimage_ref(
                    grounded_graph_ref=projection.grounded_graph_ref,
                    parent_observation_duty_ref=(
                        projection.parent_observation_duty_ref
                    ),
                    parent_reception_duty_ref=(
                        projection.parent_reception_duty_ref
                    ),
                    interpretation_candidate_ids=tuple(
                        row.candidate_id for row in changed_candidates
                    ),
                    meaning_field_id=(
                        projection.meaning_field.meaning_field_id
                    ),
                    observation_contribution_ids=tuple(
                        row.contribution_id
                        for row in projection.observation_contributions
                    ),
                    retained_reception_act_ids=(
                        projection.retained_reception_act_ids
                    ),
                    observation_depth_class=(
                        projection.observation_depth_class
                    ),
                    temperature_class=projection.temperature_class,
                    reception_style_policy_ref=(
                        projection.reception_style_policy_ref
                    ),
                    emlis_value_policy_ref=projection.emlis_value_policy_ref,
                )
            )
            changed_projection_blank = replace(
                projection,
                projection_id="",
                interpretation_candidates=changed_candidates,
                projection_preimage_ref=changed_preimage,
            )
            changed_projection = replace(
                changed_projection_blank,
                projection_id=contract_owner.recompute_stage1_identity(
                    changed_projection_blank
                ),
            )
            contract_owner.validate_stage1_identity(changed_direct)
            contract_owner.validate_stage1_identity(changed_projection)
            return changed_projection

        direction_direct = next(
            row
            for row in direct_by_ref.values()
            if direction_marker in row.required_qualifiers
        )
        burden_direct = next(
            row
            for row in direct_by_ref.values()
            if burden_marker in row.required_qualifiers
        )
        self.assertEqual(
            (
                direction_direct.candidate_kind,
                direction_direct.semantic_operator,
            ),
            (
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_STATE,
            ),
        )
        self.assertEqual(
            (
                burden_direct.candidate_kind,
                burden_direct.semantic_operator,
            ),
            (
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_BURDEN,
            ),
        )
        support_shape_tampers = (
            (
                direction_direct,
                {"candidate_kind": InterpretationKind.DIRECT_DIRECTION},
            ),
            (
                direction_direct,
                {"semantic_operator": SemanticOperator.PRESENT_DIRECTION},
            ),
            (
                burden_direct,
                {"candidate_kind": InterpretationKind.DIRECT_DIRECTION},
            ),
            (
                burden_direct,
                {"semantic_operator": SemanticOperator.PRESENT_STATE},
            ),
        )
        for direct, changes in support_shape_tampers:
            with self.subTest(
                source_contract=tuple(
                    value
                    for value in direct.required_qualifiers
                    if value in {direction_marker, burden_marker}
                ),
                changes=changes,
            ):
                fully_rehashed = rehash_support_shape(direct, **changes)
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_projection_v2_support_candidate_invalid",
                ):
                    contract_owner.validate_stage1_projection(
                        fully_rehashed,
                        grounded_graph=graph,
                        parent_plan=parent,
                    )

        endpoint_seal = (
            "left_qualifier:semantic_role:direction_under_burden_direction",
            "right_qualifier:semantic_role:direction_under_burden_burden",
        )
        forged_relation = identify_candidate(
            replace(
                relation_candidate,
                required_qualifiers=tuple(
                    endpoint_seal[1]
                    if value == endpoint_seal[0]
                    else (
                        endpoint_seal[0]
                        if value == endpoint_seal[1]
                        else value
                    )
                    for value in relation_candidate.required_qualifiers
                ),
            )
        )

        forged_direct_rows = {}
        for semantic_ref, direct in direct_by_ref.items():
            forged_direct_rows[semantic_ref] = identify_candidate(
                replace(
                    direct,
                    required_qualifiers=tuple(
                        burden_marker
                        if value == direction_marker
                        else (
                            direction_marker
                            if value == burden_marker
                            else value
                        )
                        for value in direct.required_qualifiers
                    ),
                )
            )
        replacement_by_id = {
            relation_candidate.candidate_id: forged_relation,
            **{
                direct_by_ref[semantic_ref].candidate_id: forged
                for semantic_ref, forged in forged_direct_rows.items()
            },
        }
        candidate_id_map = {
            old_id: row.candidate_id
            for old_id, row in replacement_by_id.items()
        }
        forged_candidates = tuple(
            replacement_by_id.get(row.candidate_id, row)
            for row in projection.interpretation_candidates
        )
        forged_meaning_field_blank = replace(
            projection.meaning_field,
            meaning_field_id="",
            grounded_graph_ref=response._graph_ref(forged_graph),
            center_candidate_ref=candidate_id_map.get(
                projection.meaning_field.center_candidate_ref,
                projection.meaning_field.center_candidate_ref,
            ),
            entries=tuple(
                replace(
                    entry,
                    interpretation_candidate_refs=tuple(
                        candidate_id_map.get(ref, ref)
                        for ref in entry.interpretation_candidate_refs
                    ),
                )
                for entry in projection.meaning_field.entries
            ),
            required_candidate_refs=tuple(
                candidate_id_map.get(ref, ref)
                for ref in projection.meaning_field.required_candidate_refs
            ),
        )
        forged_meaning_field = replace(
            forged_meaning_field_blank,
            meaning_field_id=contract_owner.recompute_stage1_identity(
                forged_meaning_field_blank
            ),
        )

        contribution_id_map = {}
        forged_contributions = []
        forged_candidate_by_id = {
            row.candidate_id: row for row in forged_candidates
        }
        for contribution in projection.observation_contributions:
            candidate_refs = tuple(
                candidate_id_map.get(ref, ref)
                for ref in contribution.interpretation_candidate_refs
            )
            if candidate_refs == contribution.interpretation_candidate_refs:
                forged_contributions.append(contribution)
                continue
            self.assertEqual(len(candidate_refs), 1)
            contribution_blank = replace(
                contribution,
                contribution_id="",
                interpretation_candidate_refs=candidate_refs,
                canonical_semantic_key=(
                    contract_owner._stage2_observation_semantic_key(
                        forged_candidate_by_id[candidate_refs[0]]
                    )
                ),
            )
            forged_contribution = replace(
                contribution_blank,
                contribution_id=contract_owner.recompute_stage1_identity(
                    contribution_blank
                ),
            )
            contribution_id_map[contribution.contribution_id] = (
                forged_contribution.contribution_id
            )
            forged_contributions.append(forged_contribution)

        forged_projection_blank = replace(
            projection,
            projection_id="",
            grounded_graph_ref=response._graph_ref(forged_graph),
            interpretation_candidates=forged_candidates,
            meaning_field=forged_meaning_field,
            observation_contributions=tuple(forged_contributions),
            ordered_observation_refs=tuple(
                contribution_id_map.get(ref, ref)
                for ref in projection.ordered_observation_refs
            ),
        )
        forged_projection = replace(
            forged_projection_blank,
            projection_id=contract_owner.recompute_stage1_identity(
                forged_projection_blank
            ),
        )
        for row in (
            *replacement_by_id.values(),
            forged_meaning_field,
            *(
                row
                for row in forged_contributions
                if row.contribution_id in set(contribution_id_map.values())
            ),
            forged_projection,
        ):
            contract_owner.validate_stage1_identity(row)

        # Reversing a symmetric edge can be an equivalent transport source
        # only while LEFT=direction and RIGHT=burden remain node-owned.  This
        # coordinated rewrite swaps both direct endpoint commitments, so the
        # support partition now stops before relation-shape replay.
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_projection_v2_support_candidate_invalid",
        ):
            contract_owner.validate_stage1_projection(
                forged_projection,
                grounded_graph=forged_graph,
                parent_plan=parent,
            )

        def rehash_relation_seal(
            required_qualifiers,
        ):
            changed_relation = identify_candidate(
                replace(
                    relation_candidate,
                    required_qualifiers=required_qualifiers,
                )
            )
            changed_candidates = tuple(
                changed_relation
                if row.candidate_id == relation_candidate.candidate_id
                else row
                for row in projection.interpretation_candidates
            )
            changed_meaning_blank = replace(
                projection.meaning_field,
                meaning_field_id="",
                center_candidate_ref=(
                    changed_relation.candidate_id
                    if projection.meaning_field.center_candidate_ref
                    == relation_candidate.candidate_id
                    else projection.meaning_field.center_candidate_ref
                ),
                entries=tuple(
                    replace(
                        entry,
                        interpretation_candidate_refs=tuple(
                            changed_relation.candidate_id
                            if ref == relation_candidate.candidate_id
                            else ref
                            for ref in entry.interpretation_candidate_refs
                        ),
                    )
                    for entry in projection.meaning_field.entries
                ),
                required_candidate_refs=tuple(
                    changed_relation.candidate_id
                    if ref == relation_candidate.candidate_id
                    else ref
                    for ref in projection.meaning_field.required_candidate_refs
                ),
            )
            changed_meaning = replace(
                changed_meaning_blank,
                meaning_field_id=contract_owner.recompute_stage1_identity(
                    changed_meaning_blank
                ),
            )
            contribution_map = {}
            changed_contributions = []
            for contribution in projection.observation_contributions:
                if (
                    relation_candidate.candidate_id
                    not in contribution.interpretation_candidate_refs
                ):
                    changed_contributions.append(contribution)
                    continue
                changed_contribution_blank = replace(
                    contribution,
                    contribution_id="",
                    interpretation_candidate_refs=(
                        changed_relation.candidate_id,
                    ),
                    canonical_semantic_key=(
                        contract_owner._stage2_observation_semantic_key(
                            changed_relation
                        )
                    ),
                )
                changed_contribution = replace(
                    changed_contribution_blank,
                    contribution_id=contract_owner.recompute_stage1_identity(
                        changed_contribution_blank
                    ),
                )
                contribution_map[contribution.contribution_id] = (
                    changed_contribution.contribution_id
                )
                changed_contributions.append(changed_contribution)
            changed_projection_blank = replace(
                projection,
                projection_id="",
                interpretation_candidates=changed_candidates,
                meaning_field=changed_meaning,
                observation_contributions=tuple(changed_contributions),
                ordered_observation_refs=tuple(
                    contribution_map.get(ref, ref)
                    for ref in projection.ordered_observation_refs
                ),
            )
            changed_projection = replace(
                changed_projection_blank,
                projection_id=contract_owner.recompute_stage1_identity(
                    changed_projection_blank
                ),
            )
            for row in (
                changed_relation,
                changed_meaning,
                *(
                    row
                    for row in changed_contributions
                    if row.contribution_id in set(contribution_map.values())
                ),
                changed_projection,
            ):
                contract_owner.validate_stage1_identity(row)
            return changed_projection

        left_seal, _right_seal = endpoint_seal
        non_equivalent_seals = (
            tuple(
                "left_qualifier:semantic_role:"
                "direction_under_burden_foreign"
                if value == left_seal
                else value
                for value in relation_candidate.required_qualifiers
            ),
            tuple(
                value
                for value in relation_candidate.required_qualifiers
                if value != left_seal
            ),
        )
        for changed_seal in non_equivalent_seals:
            with self.subTest(changed_seal=changed_seal):
                fully_rehashed = rehash_relation_seal(changed_seal)
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_candidate_relation_binding_invalid",
                ):
                    contract_owner.validate_stage1_projection(
                        fully_rehashed,
                        grounded_graph=graph,
                        parent_plan=parent,
                    )

    def test_existing_direct_meaning_keeps_role_seal_in_support_closure(
        self,
    ) -> None:
        source, plan, graph, parent = self._exact8_candidate_inputs("SX-07")
        phase_a = response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent,
            grounded_plan=plan,
        )
        meaning_candidate_refs = {
            ref
            for entry in phase_a.meaning_field.entries
            for ref in entry.interpretation_candidate_refs
        }
        direction_marker = (
            "qualifier:semantic_role:direction_under_burden_direction"
        )
        burden_marker = (
            "qualifier:semantic_role:direction_under_burden_burden"
        )
        role_markers = {direction_marker, burden_marker}
        relation = next(
            row
            for row in phase_a.interpretation_candidate_rows
            if row.candidate_kind
            is InterpretationKind.DIRECTION_UNDER_BURDEN
            and row.relation_operator is RelationOperator.TENSION_WITH
        )
        endpoint_refs = {
            binding.semantic_ref for binding in relation.argument_bindings
        }
        meaning_direct = {
            row.semantic_refs[0]: row
            for row in phase_a.interpretation_candidate_rows
            if row.candidate_id in meaning_candidate_refs
            and not row.relation_basis_refs
            and row.semantic_refs[0] in endpoint_refs
        }
        support_direct = {
            row.semantic_refs[0]: row
            for row in phase_a.interpretation_candidate_rows
            if row.candidate_id not in meaning_candidate_refs
            and not row.relation_basis_refs
            and row.semantic_refs[0] in endpoint_refs
        }
        self.assertEqual(set(meaning_direct), endpoint_refs)
        self.assertEqual(set(support_direct), endpoint_refs)
        self.assertTrue(
            all(
                not role_markers.intersection(row.required_qualifiers)
                for row in meaning_direct.values()
            )
        )
        self.assertEqual(
            {
                marker
                for row in support_direct.values()
                for marker in row.required_qualifiers
                if marker in role_markers
            },
            role_markers,
        )
        for argument in relation.argument_bindings:
            endpoint_row = next(
                row
                for row in (
                    phase_a
                    .relation_endpoint_grounded_candidate_ref_by_binding_key
                )
                if row.relation_candidate_ref == relation.candidate_id
                and row.source_argument_role is argument.role
                and row.source_semantic_ref == argument.semantic_ref
            )
            self.assertEqual(
                endpoint_row.endpoint_grounded_candidate_ref,
                support_direct[argument.semantic_ref].candidate_id,
            )
        markerless_relation = next(
            row
            for row in phase_a.interpretation_candidate_rows
            if row.candidate_id != relation.candidate_id
            and row.relation_basis_refs
            and set(row.semantic_refs) == endpoint_refs
            and not any(
                "_qualifier:semantic_role:direction_under_burden_" in value
                for value in row.required_qualifiers
            )
        )
        for argument in markerless_relation.argument_bindings:
            endpoint_row = next(
                row
                for row in (
                    phase_a
                    .relation_endpoint_grounded_candidate_ref_by_binding_key
                )
                if row.relation_candidate_ref
                == markerless_relation.candidate_id
                and row.source_argument_role is argument.role
                and row.source_semantic_ref == argument.semantic_ref
            )
            self.assertEqual(
                endpoint_row.endpoint_grounded_candidate_ref,
                meaning_direct[argument.semantic_ref].candidate_id,
            )
        projection = response.seal_stage1_projection(
            phase_a,
            composition.project_subjective_meaning_plan(phase_a),
        )
        self.assertEqual(
            projection.interpretation_candidates,
            phase_a.interpretation_candidate_rows,
        )

        def identify_candidate(row):
            blank = replace(row, candidate_id="")
            return replace(
                blank,
                candidate_id=contract_owner.recompute_stage1_identity(blank),
            )

        # A support row is an exact source-contract twin, never a second
        # direct-shape owner.  A fully rehashed operator change still stops.
        support = next(iter(support_direct.values()))
        reshaped_support = identify_candidate(
            replace(
                support,
                semantic_operator=SemanticOperator.PRESENT_STATE,
            )
        )
        reshaped_projection_blank = replace(
            projection,
            projection_id="",
            interpretation_candidates=tuple(
                reshaped_support
                if row.candidate_id == support.candidate_id
                else row
                for row in projection.interpretation_candidates
            ),
        )
        reshaped_projection = replace(
            reshaped_projection_blank,
            projection_id=contract_owner.recompute_stage1_identity(
                reshaped_projection_blank
            ),
        )
        contract_owner.validate_stage1_identity(reshaped_support)
        contract_owner.validate_stage1_identity(reshaped_projection)
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_projection_v2_support_candidate_invalid",
        ):
            contract_owner.validate_stage1_projection(
                reshaped_projection,
                grounded_graph=graph,
                parent_plan=parent,
            )

        # Promoting a DUB-qualified support twin into the MeaningField cannot
        # launder the relation-role marker into a meaning owner.
        meaning = meaning_direct[support.semantic_refs[0]]
        candidate_ref_map = {meaning.candidate_id: support.candidate_id}
        promoted_meaning_blank = replace(
            projection.meaning_field,
            meaning_field_id="",
            center_candidate_ref=candidate_ref_map.get(
                projection.meaning_field.center_candidate_ref,
                projection.meaning_field.center_candidate_ref,
            ),
            entries=tuple(
                replace(
                    entry,
                    interpretation_candidate_refs=tuple(
                        candidate_ref_map.get(ref, ref)
                        for ref in entry.interpretation_candidate_refs
                    ),
                )
                for entry in projection.meaning_field.entries
            ),
            required_candidate_refs=tuple(
                candidate_ref_map.get(ref, ref)
                for ref in projection.meaning_field.required_candidate_refs
            ),
        )
        promoted_meaning = replace(
            promoted_meaning_blank,
            meaning_field_id=contract_owner.recompute_stage1_identity(
                promoted_meaning_blank
            ),
        )
        contribution_ref_map = {}
        promoted_contributions = []
        for contribution in projection.observation_contributions:
            candidate_refs = tuple(
                candidate_ref_map.get(ref, ref)
                for ref in contribution.interpretation_candidate_refs
            )
            if candidate_refs == contribution.interpretation_candidate_refs:
                promoted_contributions.append(contribution)
                continue
            promoted_blank = replace(
                contribution,
                contribution_id="",
                interpretation_candidate_refs=candidate_refs,
                canonical_semantic_key=(
                    contract_owner._stage2_observation_semantic_key(support)
                ),
            )
            promoted = replace(
                promoted_blank,
                contribution_id=contract_owner.recompute_stage1_identity(
                    promoted_blank
                ),
            )
            contribution_ref_map[contribution.contribution_id] = (
                promoted.contribution_id
            )
            promoted_contributions.append(promoted)
        promoted_projection_blank = replace(
            projection,
            projection_id="",
            meaning_field=promoted_meaning,
            observation_contributions=tuple(promoted_contributions),
            ordered_observation_refs=tuple(
                contribution_ref_map.get(ref, ref)
                for ref in projection.ordered_observation_refs
            ),
        )
        promoted_projection = replace(
            promoted_projection_blank,
            projection_id=contract_owner.recompute_stage1_identity(
                promoted_projection_blank
            ),
        )
        for row in (
            promoted_meaning,
            *(
                contribution
                for contribution in promoted_contributions
                if contribution.contribution_id
                in set(contribution_ref_map.values())
            ),
            promoted_projection,
        ):
            contract_owner.validate_stage1_identity(row)
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_direct_source_contract_invalid",
        ):
            contract_owner.validate_stage1_projection(
                promoted_projection,
                grounded_graph=graph,
                parent_plan=parent,
            )

    def test_role_incompatible_fallback_requires_exact_source_edge(self) -> None:
        source, plan, graph, _parent = self._candidate_inputs(
            "nls3s_b001_0068"
        )
        binding = response._bind_grounded_plan(source, graph, plan)
        node_by_id = {row.node_id: row for row in graph.nodes}
        edge_id = binding.relation_to_edge["relation:r1"]
        edge = next(row for row in graph.edges if row.edge_id == edge_id)

        def shape(test_edge):
            return response._relation_shape(
                test_edge,
                node_by_id,
                binding,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            )

        self.assertEqual(shape(edge)[0], InterpretationKind.COEXISTENCE)
        for unsealed_edge in (
            replace(edge, grounding_kind="bounded_structural_inference"),
            replace(edge, epistemic_state=EpistemicState.UNKNOWN),
            replace(edge, evidence_ids=()),
        ):
            with self.subTest(unsealed_edge=unsealed_edge):
                self.assertIsNone(shape(unsealed_edge))

    def test_past_action_to_present_action_has_one_registered_shape(self) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0090"
        )
        candidates = response.build_interpretation_candidate_pool(
            graph,
            parent,
            source=source,
            grounded_plan=plan,
        )
        rows = tuple(
            row
            for row in candidates
            if row.candidate_kind is InterpretationKind.ACTION_BEFORE_AFTER
        )
        self.assertEqual(len(rows), 1)
        candidate = rows[0]
        self.assertEqual(
            (
                candidate.semantic_operator,
                candidate.relation_operator,
                tuple(binding.role for binding in candidate.argument_bindings),
            ),
            (
                SemanticOperator.PRESENT_ACTUAL_OUTPUT,
                RelationOperator.TEMPORALLY_PRECEDES,
                (ArgumentRole.BEFORE, ArgumentRole.AFTER),
            ),
        )
        self.assertIn("before_time_scope:past", candidate.required_qualifiers)
        self.assertIn("after_time_scope:present", candidate.required_qualifiers)
        self.assertEqual(
            tuple(
                value
                for value in candidate.required_qualifiers
                if "_qualifier:" in value
            ),
            (
                "before_qualifier:operator:shift",
                "after_qualifier:operator:shift",
            ),
        )
        self.assertEqual(len(candidate.relation_basis_refs), 1)
        phase_a = response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent,
            grounded_plan=plan,
        )
        projection = response.seal_stage1_projection(
            phase_a,
            composition.project_subjective_meaning_plan(phase_a),
        )
        self.assertEqual(
            projection.schema_version,
            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
        )
        self.assertIn(candidate, projection.interpretation_candidates)
        contribution = next(
            row
            for row in projection.observation_contributions
            if candidate.candidate_id in row.interpretation_candidate_refs
        )
        self.assertEqual(contribution.semantic_operator, candidate.semantic_operator)
        self.assertEqual(contribution.relation_operator, candidate.relation_operator)

    def test_shift_qualifier_seals_bind_direct_profiles_and_fail_closed(
        self,
    ) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0090"
        )
        candidates = response.build_interpretation_candidate_pool(
            graph,
            parent,
            source=source,
            grounded_plan=plan,
            stage1_response_schema_version=(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            ),
        )
        relation_candidate = next(
            row
            for row in candidates
            if row.candidate_kind
            is InterpretationKind.ACTION_BEFORE_AFTER
        )
        node_by_id = {row.node_id: row for row in graph.nodes}
        edge_by_id = {row.edge_id: row for row in graph.edges}
        direct_shapes: dict[
            str,
            set[tuple[InterpretationKind, SemanticOperator]],
        ] = {}
        direct_contracts: dict[str, tuple[str, ...]] = {}
        for row in candidates:
            if row.relation_basis_refs:
                continue
            semantic_ref = row.semantic_refs[0]
            direct_shapes.setdefault(semantic_ref, set()).add(
                (row.candidate_kind, row.semantic_operator)
            )
            direct_contracts[semantic_ref] = tuple(
                value
                for value in row.required_qualifiers
                if value.startswith("qualifier:")
            )
        frozen_direct_shapes = {
            ref: frozenset(values) for ref, values in direct_shapes.items()
        }

        def validate_relation(
            candidate,
            *,
            contracts=direct_contracts,
        ) -> None:
            contract_owner._validate_stage1_relation_binding(
                candidate,
                edge_by_id=edge_by_id,
                node_by_id=node_by_id,
                node_source_order={
                    row.node_id: index
                    for index, row in enumerate(graph.nodes)
                },
                direct_shapes_by_node_ref=frozen_direct_shapes,
                direct_source_contract_qualifiers_by_node_ref=contracts,
            )

        validate_relation(relation_candidate)
        for forged in (
            replace(
                relation_candidate,
                required_qualifiers=tuple(
                    value
                    for value in relation_candidate.required_qualifiers
                    if value != "before_qualifier:operator:shift"
                ),
            ),
            replace(
                relation_candidate,
                required_qualifiers=(
                    *relation_candidate.required_qualifiers,
                    "before_qualifier:operator:change",
                ),
            ),
        ):
            with self.subTest(forged=forged.required_qualifiers):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "stage1_candidate_relation_binding_invalid",
                ):
                    validate_relation(forged)

        before_ref = relation_candidate.argument_bindings[0].semantic_ref
        forged_direct_contracts = {
            **direct_contracts,
            before_ref: (),
        }
        with self.assertRaisesRegex(
            CMEEStage1ContractError,
            "stage1_candidate_relation_binding_invalid",
        ):
            validate_relation(
                relation_candidate,
                contracts=forged_direct_contracts,
            )

        source_qualifiers = (
            contract_owner._foreground_source_qualifiers_by_node_ref(
                source=source,
                grounded_plan=plan,
                grounded_graph=graph,
                parent_plan=parent,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            )
        )
        direct_candidate = next(
            row
            for row in candidates
            if not row.relation_basis_refs
            and row.semantic_refs == (before_ref,)
        )
        self.assertEqual(
            direct_contracts[before_ref],
            ("qualifier:operator:shift",),
        )
        for forged_qualifiers in (
            tuple(
                value
                for value in direct_candidate.required_qualifiers
                if value != "qualifier:operator:shift"
            ),
            (
                *direct_candidate.required_qualifiers,
                "qualifier:operator:change",
            ),
        ):
            forged_rows = tuple(
                replace(row, required_qualifiers=forged_qualifiers)
                if row is direct_candidate
                else row
                for row in candidates
            )
            with self.subTest(forged_direct=forged_qualifiers):
                with self.assertRaisesRegex(
                    CMEEStage1ContractError,
                    "foreground_scope_projection_qualifier_source_mismatch",
                ):
                    contract_owner._validate_premeaning_source_qualifiers(
                        interpretation_candidate_rows=forged_rows,
                        source_qualifiers_by_node_ref=source_qualifiers,
                        source_relation_by_ref={
                            response._edge_ref(value.edge_id): value
                            for value in graph.edges
                        },
                    )

        self.assertEqual(
            contract_owner.project_stage1_source_contract_qualifiers(
                source_attribute_codes=("operator:change", "operator:shifted"),
                source_explicit_shift_relation_endpoint=True,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            ),
            (),
        )
        self.assertEqual(
            contract_owner.project_stage1_source_contract_qualifiers(
                source_attribute_codes=("operator:shift",),
                source_explicit_shift_relation_endpoint=False,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            ),
            (),
        )
        self.assertEqual(
            contract_owner.project_stage1_source_contract_qualifiers(
                source_attribute_codes=("operator:shift",),
                source_explicit_shift_relation_endpoint=True,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            ),
            ("qualifier:operator:shift",),
        )

        sx_source, sx_plan = self._exact8_source_plan("SX-08")
        sx_required_nuclei, sx_required_relations, sx_targets = (
            _planned_visible_source_ids(sx_plan)
        )
        sx_graph = _build_graph(
            sx_source,
            sx_plan,
            _ordered((*sx_required_nuclei, *sx_targets)),
            sx_required_relations,
        )
        sx_binding = response._bind_grounded_plan(
            sx_source,
            sx_graph,
            sx_plan,
        )
        nonshift_shift_meta = tuple(
            (
                node_id,
                meta,
            )
            for node_id, meta in sx_binding.node_meta.items()
            if "operator:shift" in tuple(meta.semantic_frame.attribute_codes)
        )
        self.assertTrue(nonshift_shift_meta)
        shift_endpoint_ids = (
            contract_owner.project_stage1_source_explicit_shift_endpoint_node_ids(
                sx_graph
            )
        )
        self.assertFalse(shift_endpoint_ids)
        for node_id, meta in nonshift_shift_meta:
            self.assertNotIn(
                node_id,
                shift_endpoint_ids,
            )
            self.assertNotIn(
                "qualifier:operator:shift",
                response._qualifiers(
                    meta,
                    source_explicit_shift_relation_endpoint=False,
                    stage1_response_schema_version=(
                        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                    ),
                ),
            )
        nonshift_action_meta = next(
            meta
            for node_id, meta in sx_binding.node_meta.items()
            if next(
                row for row in sx_graph.nodes if row.node_id == node_id
            ).node_kind
            == "action"
        )
        forged_shift_action_meta = replace(
            nonshift_action_meta,
            semantic_frame=replace(
                nonshift_action_meta.semantic_frame,
                attribute_codes=(
                    *nonshift_action_meta.semantic_frame.attribute_codes,
                    "operator:shift",
                ),
            ),
        )
        self.assertNotIn(
            "qualifier:operator:shift",
            response._qualifiers(
                forged_shift_action_meta,
                source_explicit_shift_relation_endpoint=False,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            ),
        )

    def test_v1_shift_shapes_and_qualifier_identity_remain_frozen(self) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0090"
        )
        binding = response._bind_grounded_plan(source, graph, plan)
        relation = next(
            row for row in plan.relations if row.type == "shift_from_to"
        )
        edge_id = binding.relation_to_edge[relation.relation_id]
        edge = next(row for row in graph.edges if row.edge_id == edge_id)
        node_by_id = {row.node_id: row for row in graph.nodes}
        endpoint_direct = tuple(
            response._candidate_from_direct(
                graph,
                node_by_id[node_id],
                binding.node_meta[node_id],
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                ),
            )
            for node_id in (edge.source_node_id, edge.target_node_id)
        )
        expected_qualifiers = (
            (
                "epistemic:provisional_interpretation",
                "actor:current_user",
                "polarity:neutral",
                "modality:intention",
                "time_scope:past",
            ),
            (
                "epistemic:provisional_interpretation",
                "actor:current_user",
                "polarity:neutral",
                "modality:fact",
                "time_scope:present",
            ),
        )
        self.assertEqual(
            tuple(row.required_qualifiers for row in endpoint_direct),
            expected_qualifiers,
        )
        self.assertEqual(
            tuple(
                hashlib.sha256(
                    contract_owner.stage1_canonical_json_bytes(values)
                ).hexdigest()
                for values in expected_qualifiers
            ),
            (
                "fdc02e7f62eadbbb9d38d58267861eede373616629342d7ed21bfb8eae02c42d",
                "118bfc381d2002d28f6667f2418bf9cafb9e7f9820139a0876ed5ba74537fd5e",
            ),
        )
        self.assertTrue(
            all(
                "qualifier:operator:shift" not in row.required_qualifiers
                for row in endpoint_direct
            )
        )

        v1_shift = contract_owner.project_stage1_relation_shape(
            relation_kind="shift_from_to",
            source_ref="node:event@1.0",
            target_ref="node:residue@1.0",
            source_node_kind="event",
            target_node_kind="reaction",
            source_direct_shape=(
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_STATE,
            ),
            target_direct_shape=(
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_STATE,
            ),
            source_time_scope="past",
            target_time_scope="present",
            source_attribute_codes=(),
            target_attribute_codes=(),
            source_order=0,
            target_order=1,
            edge_grounding_kind="user_stated_relation",
            edge_epistemic_state=EpistemicState.SOURCE_EXPLICIT,
            edge_evidence_ids=("evidence",),
            stage1_response_schema_version=(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
            ),
        )
        self.assertEqual(
            v1_shift,
            (
                InterpretationKind.RESIDUE_AFTER_EVENT,
                SemanticOperator.PRESENT_RESIDUE,
                RelationOperator.TEMPORALLY_PRECEDES,
                (
                    contract_owner.ArgumentBinding(
                        ArgumentRole.BEFORE,
                        "node:event@1.0",
                    ),
                    contract_owner.ArgumentBinding(
                        ArgumentRole.AFTER,
                        "node:residue@1.0",
                    ),
                ),
            ),
        )
        self.assertIsNone(
            contract_owner.project_stage1_relation_shape(
                relation_kind="wish_and_constraint",
                source_ref="node:left@1.0",
                target_ref="node:right@1.0",
                source_node_kind="state",
                target_node_kind="state",
                source_direct_shape=(
                    InterpretationKind.DIRECT_STATE,
                    SemanticOperator.PRESENT_STATE,
                ),
                target_direct_shape=(
                    InterpretationKind.DIRECT_STATE,
                    SemanticOperator.PRESENT_STATE,
                ),
                source_time_scope="present",
                target_time_scope="present",
                source_attribute_codes=(),
                target_attribute_codes=(),
                source_order=0,
                target_order=1,
                edge_grounding_kind="user_stated_relation",
                edge_epistemic_state=EpistemicState.SOURCE_EXPLICIT,
                edge_evidence_ids=("evidence",),
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                ),
            )
        )

    def test_contracts_owns_frozen_exact13_and_v2_exact16(self) -> None:
        self.assertIs(
            response.INTERPRETATION_MATRIX_EXACT13,
            contract_owner.INTERPRETATION_MATRIX_EXACT13,
        )
        self.assertIs(
            response.INTERPRETATION_MATRIX_EXACT16,
            contract_owner.INTERPRETATION_MATRIX_EXACT16,
        )
        self.assertIs(
            response.project_stage1_relation_shape,
            contract_owner.project_stage1_relation_shape,
        )
        self.assertEqual(len(contract_owner.INTERPRETATION_MATRIX_EXACT13), 13)
        self.assertEqual(len(contract_owner.INTERPRETATION_MATRIX_EXACT16), 16)
        self.assertEqual(
            contract_owner.INTERPRETATION_MATRIX_EXACT16[:13],
            contract_owner.INTERPRETATION_MATRIX_EXACT13,
        )
        self.assertEqual(
            contract_owner.INTERPRETATION_MATRIX_EXACT16[13:],
            (
                (
                    InterpretationKind.ACTION_BEFORE_AFTER,
                    SemanticOperator.PRESENT_ACTUAL_OUTPUT,
                    RelationOperator.TEMPORALLY_PRECEDES,
                    (ArgumentRole.BEFORE, ArgumentRole.AFTER),
                ),
                (
                    InterpretationKind.BOUNDED_SOURCE_ORDER,
                    SemanticOperator.PRESENT_UNFINISHED,
                    RelationOperator.NO_RELATION_CLAIM,
                    (ArgumentRole.BEFORE, ArgumentRole.AFTER),
                ),
                (
                    InterpretationKind.SOURCE_STATED_TRANSITION,
                    SemanticOperator.PRESENT_CHANGE,
                    RelationOperator.TEMPORALLY_PRECEDES,
                    (ArgumentRole.BEFORE, ArgumentRole.AFTER),
                ),
            ),
        )
        self.assertEqual(
            hashlib.sha256(
                contract_owner.stage1_canonical_json_bytes(
                    contract_owner.INTERPRETATION_MATRIX_EXACT13
                )
            ).hexdigest(),
            "10d9292029a2aea2588c7a559bc47a2d518df921106e78ba49cc60d48b1951a5",
        )
        self.assertEqual(
            response.CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256,
            "dc4e1e5ef8026d5577698f375e305db7886f57096c69e6e6a0b99bfe1f26de8a",
        )
        self.assertEqual(
            len(
                dict(response.CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)[
                    "observation_operator_rows"
                ]
            ),
            12,
        )
        self.assertEqual(len(response._OBSERVATION_PREDICATE_ROWS), 12)

    def test_action_before_after_rejects_non_temporal_or_unsealed_pairs(
        self,
    ) -> None:
        source, plan, graph, _parent = self._candidate_inputs(
            "nls3s_b001_0090"
        )
        binding = response._bind_grounded_plan(source, graph, plan)
        node_by_id = {row.node_id: row for row in graph.nodes}
        edge = next(
            row
            for row in graph.edges
            if row.edge_id in binding.required_edge_ids
        )

        def shape(test_edge, test_binding):
            return response._relation_shape(
                test_edge,
                node_by_id,
                test_binding,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            )

        self.assertIsNotNone(shape(edge, binding))
        self.assertIsNone(
            response._relation_shape(
                edge,
                node_by_id,
                binding,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
                ),
            )
        )
        self.assertIsNone(
            shape(
                replace(
                    edge,
                    source_node_id=edge.target_node_id,
                    target_node_id=edge.source_node_id,
                ),
                binding,
            )
        )

        source_meta = binding.node_meta[edge.source_node_id]
        target_meta = binding.node_meta[edge.target_node_id]
        same_time_meta = replace(
            source_meta,
            semantic_frame=replace(
                source_meta.semantic_frame,
                time_scope="present",
            ),
        )
        self.assertIsNone(
            shape(
                edge,
                replace(
                    binding,
                    node_meta={
                        **binding.node_meta,
                        edge.source_node_id: same_time_meta,
                    },
                ),
            )
        )

        source_no_shift_meta = replace(
            source_meta,
            semantic_frame=replace(
                source_meta.semantic_frame,
                attribute_codes=tuple(
                    code
                    for code in source_meta.semantic_frame.attribute_codes
                    if code != "operator:shift"
                ),
            ),
        )
        self.assertIsNone(
            shape(
                edge,
                replace(
                    binding,
                    node_meta={
                        **binding.node_meta,
                        edge.source_node_id: source_no_shift_meta,
                    },
                ),
            )
        )

        target_no_shift_meta = replace(
            target_meta,
            semantic_frame=replace(
                target_meta.semantic_frame,
                attribute_codes=tuple(
                    code
                    for code in target_meta.semantic_frame.attribute_codes
                    if code != "operator:shift"
                ),
            ),
        )
        self.assertIsNone(
            shape(
                edge,
                replace(
                    binding,
                    node_meta={
                        **binding.node_meta,
                        edge.target_node_id: target_no_shift_meta,
                    },
                ),
            )
        )

        future_target_meta = replace(
            target_meta,
            semantic_frame=replace(
                target_meta.semantic_frame,
                time_scope="future",
            ),
        )
        self.assertIsNone(
            shape(
                edge,
                replace(
                    binding,
                    node_meta={
                        **binding.node_meta,
                        edge.target_node_id: future_target_meta,
                    },
                ),
            )
        )
        for unsealed_edge in (
            replace(edge, grounding_kind="bounded_structural_inference"),
            replace(edge, epistemic_state=EpistemicState.UNKNOWN),
            replace(edge, evidence_ids=()),
        ):
            with self.subTest(unsealed_edge=unsealed_edge):
                self.assertIsNone(shape(unsealed_edge, binding))

    def test_generic_source_stated_transition_is_strict_and_non_action(
        self,
    ) -> None:
        source, plan, graph, _parent = self._candidate_inputs(
            "nls3s_b001_0100"
        )
        binding = response._bind_grounded_plan(source, graph, plan)
        node_by_id = {row.node_id: row for row in graph.nodes}
        relation_id = next(
            row.relation_id
            for row in plan.relations
            if row.type == "shift_from_to"
        )
        edge_id = binding.relation_to_edge[relation_id]
        edge = next(row for row in graph.edges if row.edge_id == edge_id)

        def shape(test_edge, test_binding):
            return response._relation_shape(
                test_edge,
                node_by_id,
                test_binding,
                stage1_response_schema_version=(
                    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
                ),
            )

        actual = shape(edge, binding)
        self.assertIsNotNone(actual)
        self.assertEqual(actual[0], InterpretationKind.SOURCE_STATED_TRANSITION)
        source_meta = binding.node_meta[edge.source_node_id]
        no_shift = replace(
            source_meta,
            semantic_frame=replace(
                source_meta.semantic_frame,
                attribute_codes=tuple(
                    code
                    for code in source_meta.semantic_frame.attribute_codes
                    if code != "operator:shift"
                ),
            ),
        )
        self.assertIsNone(
            shape(
                edge,
                replace(
                    binding,
                    node_meta={
                        **binding.node_meta,
                        edge.source_node_id: no_shift,
                    },
                ),
            )
        )
        self.assertIsNone(
            shape(
                replace(
                    edge,
                    source_node_id=edge.target_node_id,
                    target_node_id=edge.source_node_id,
                ),
                binding,
            )
        )

    def test_action_before_after_is_visible_to_surface_inverse(self) -> None:
        source, plan, graph, parent = self._candidate_inputs(
            "nls3s_b001_0090"
        )
        relation = next(
            row
            for row in plan.relations
            if row.type == "shift_from_to"
        )
        self.assertEqual(
            plan.response_plan.human_follow_target_ids,
            (relation.to_nucleus_id,),
        )
        reception_plan = plan.response_plan.human_reception_plan
        self.assertIsNotNone(reception_plan)
        self.assertEqual(len(reception_plan.moves), 1)
        self.assertEqual(
            reception_plan.moves[0].target_nucleus_ids,
            (relation.to_nucleus_id,),
        )
        self.assertEqual(
            reception_plan.moves[0].support_nucleus_ids,
            (relation.from_nucleus_id,),
        )
        nucleus_by_id = {row.nucleus_id: row for row in plan.nuclei}
        span_by_id = {
            span.span_id: span
            for span in source.evidence_spans
        }
        before_text = "".join(
            span_by_id[span_id].raw_text
            for span_id in nucleus_by_id[
                relation.from_nucleus_id
            ].source_span_ids
        )
        after_text = "".join(
            span_by_id[span_id].raw_text
            for span_id in nucleus_by_id[
                relation.to_nucleus_id
            ].source_span_ids
        )
        realized_surfaces = []
        inverse_by_body: dict[bytes, list[object]] = {}
        gate_by_body: dict[bytes, list[object]] = {}
        actual_realize = response.realize_grounded_sentence_plan
        actual_inverse = response.evaluate_grounded_surface_body_inverse
        actual_gate = response.evaluate_grounded_observation_gate

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
            surface = kwargs.get(
                "surface_result",
                args[2] if len(args) > 2 else None,
            )
            if surface is not None:
                gate_by_body.setdefault(
                    surface.text.encode("utf-8"),
                    [],
                ).append(result)
            return result

        with (
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
                source=source,
                grounded_graph=graph,
                parent_plan=parent,
                grounded_plan=plan,
            )
        self.assertTrue(units)
        self.assertTrue(
            any(
                row.candidate_kind is InterpretationKind.ACTION_BEFORE_AFTER
                for row in projection.interpretation_candidates
            )
        )

        selected_surfaces = tuple(
            surface
            for surface in realized_surfaces
            if tuple(line.text for line in surface.lines)
            == tuple(unit.text for unit in units)
        )
        self.assertTrue(selected_surfaces)
        selected_surface = selected_surfaces[0]

        visible = tuple(
            line
            for line in selected_surface.lines
            if relation.relation_id in line.binding.relation_ids
            and before_text in line.text
            and after_text in line.text
            and "前から後" in line.text
        )
        self.assertTrue(visible)
        line = visible[0]
        self.assertLess(line.text.index(before_text), line.text.index(after_text))
        selected_body = selected_surface.text.encode("utf-8")
        inverse_rows = inverse_by_body.get(selected_body, [])
        gate_rows = gate_by_body.get(selected_body, [])
        self.assertTrue(inverse_rows)
        self.assertTrue(gate_rows)
        self.assertTrue(any(report.passed for report in inverse_rows))
        self.assertTrue(any(report.passed for report in gate_rows))
        self.assertTrue(
            any(
                report.source_anchor_count >= 2
                and report.relation_marker_count >= 1
                and not any(
                    "relation" in code or "order" in code
                    for code in report.failure_codes
                )
                for report in inverse_rows
            )
        )

    def test_directional_follow_rank_does_not_override_self_denial_safety(
        self,
    ) -> None:
        _source, plan = self._source_plan("nls3s_b001_0066")
        directional = replace(
            next(
                row
                for row in plan.relations
                if row.type == "action_supports_change"
            ),
            retention="required",
            from_nucleus_id="nucleus:s3",
            to_nucleus_id="nucleus:s2",
        )
        safety = EmlisSafetyTriageDecision(
            safety_triage_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
            response_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
            normal_observation_allowed=False,
            safe_state_answer_allowed=True,
            must_not_accept_identity_claim_as_fact=True,
            evidence_span_ids=["s3"],
        )
        response_plan, _coverage, _surface, _safety = (
            observation_plan_owner._build_response_and_policies(
                nuclei=plan.nuclei,
                relations=(*plan.relations, directional),
                safety_decision=safety,
                complexity=plan.input_profile.semantic_complexity,
                material_quality=plan.input_profile.material_quality,
                include_reception_relation_support=True,
            )
        )
        self.assertEqual(
            response_plan.human_follow_target_ids,
            plan.response_plan.human_follow_target_ids,
        )
        self.assertEqual(
            response_plan.human_follow_target_ids,
            ("nucleus:s3",),
        )

    def test_directional_follow_rank_requires_distinct_endpoint_evidence(
        self,
    ) -> None:
        _source, plan = self._exact8_source_plan("SX-03")
        temporal = next(
            row
            for row in plan.relations
            if row.type == "temporal_before_after"
        )
        nucleus_by_id = {row.nucleus_id: row for row in plan.nuclei}
        self.assertFalse(
            set(
                nucleus_by_id[
                    temporal.from_nucleus_id
                ].source_span_ids
            ).isdisjoint(
                nucleus_by_id[
                    temporal.to_nucleus_id
                ].source_span_ids
            )
        )
        self.assertNotEqual(
            plan.response_plan.human_follow_target_ids,
            (temporal.to_nucleus_id,),
        )
        self.assertEqual(
            plan.response_plan.human_follow_target_ids,
            ("nucleus:s1:wish",),
        )


if __name__ == "__main__":
    unittest.main()
