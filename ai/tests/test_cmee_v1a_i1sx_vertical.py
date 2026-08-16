# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from dataclasses import replace
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine
import cocolon_meaning_experience_engine.emlis_v1a as emlis_v1a_module
from cocolon_meaning_experience_engine.contracts import (
    AttachmentAdmission,
    CMEE_COMMON_GUARD_PROOF_VERSION,
    CMEE_TERMINAL_GENERATED_DISABLED,
    CommonGuardResultProof,
    EpistemicState,
    OwnerClass,
    ProviderResolution,
    RouteBDisposition,
    VisibleAuthority,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    CMEEVerticalError,
    EXPECTED_COMMON_GUARD_IDS,
    _artifact_id,
    _build_experience_plan,
    _graph_id,
    _common_guard_proof_id,
    _plan_id,
    _planned_visible_source_ids,
    _realize_cmee_experience,
    _sha256_text,
    build_text_grounded_limited_artifact,
    validate_positive_realization_trace,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source


REPRESENTATIVE_MEMO = "仕事が続いて疲れていて、朝から何も手につかない。"


def _request(
    *,
    record_id: str = "cmee-vertical-1",
    memo: str = REPRESENTATIVE_MEMO,
    action: str = "",
    category: str = "仕事",
    emotion: str = "不安",
    strength: str = "medium",
) -> GenerationRequest:
    raw = {
        "id": record_id,
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }
    return GenerationRequest(
        request_id=f"req-{record_id}",
        current_input_bundle=build_emlis_current_input_bundle(raw),
        expected_source_record_id=record_id,
    )


def _private_parts(request: GenerationRequest):
    source = freeze_text_source(request)
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    grounded_plan = build_grounded_observation_plan(
        source.normalized_current_input,
        evidence_spans=source.evidence_spans,
    )
    graph, plan, artifact = build_text_grounded_limited_artifact(source)
    visible, _guard_material = _realize_cmee_experience(
        source,
        graph,
        plan,
        grounded_plan,
    )
    return source, graph, plan, artifact, visible


def _rehash_graph(graph):
    return replace(
        graph,
        graph_id=_graph_id(
            graph.source_envelope_id,
            graph.owner_universe_digest,
            graph.nodes,
            graph.edges,
            graph.owner_dispositions,
        ),
    )


def _rehash_artifact(source, graph, artifact):
    plan = replace(
        artifact.plan,
        plan_id=_plan_id(
            source.envelope.envelope_id,
            graph.graph_id,
            artifact.plan,
            artifact.plan.visible_line_ids,
        ),
    )
    proof = replace(
        artifact.common_guard_proof,
        source_envelope_id=source.envelope.envelope_id,
        graph_id=graph.graph_id,
        plan_id=plan.plan_id,
    )
    proof = replace(
        proof,
        proof_id=_common_guard_proof_id(
            source_envelope_id=proof.source_envelope_id,
            graph_id=proof.graph_id,
            plan_id=proof.plan_id,
            guarded_observation_units=proof.guarded_observation_units,
            guard_results=proof.guard_results,
            stabilization_report_name=proof.stabilization_report_name,
            stabilization_phase=proof.stabilization_phase,
            stabilization_core_id=proof.stabilization_core_id,
            stabilization_passed=proof.stabilization_passed,
            common_shapes_ready=proof.common_shapes_ready,
            stabilization_guard_names=proof.stabilization_guard_names,
            issue_codes=proof.issue_codes,
        ),
    )
    trace = tuple(
        replace(row, artifact_common_guard_proof_ref=proof.proof_id)
        for row in artifact.trace
    )
    return replace(
        artifact,
        plan=plan,
        common_guard_proof=proof,
        trace=trace,
        artifact_id=_artifact_id(
            source.envelope.envelope_id,
            graph.graph_id,
            plan.plan_id,
            proof.proof_id,
            artifact.observation,
            tuple(row.text for row in artifact.visible_unknowns),
            artifact.reception,
        ),
    )


def _rehash_common_guard_proof_artifact(source, graph, artifact, proof):
    proof = replace(
        proof,
        proof_id=_common_guard_proof_id(
            source_envelope_id=proof.source_envelope_id,
            graph_id=proof.graph_id,
            plan_id=proof.plan_id,
            guarded_observation_units=proof.guarded_observation_units,
            guard_results=proof.guard_results,
            stabilization_report_name=proof.stabilization_report_name,
            stabilization_phase=proof.stabilization_phase,
            stabilization_core_id=proof.stabilization_core_id,
            stabilization_passed=proof.stabilization_passed,
            common_shapes_ready=proof.common_shapes_ready,
            stabilization_guard_names=proof.stabilization_guard_names,
            issue_codes=proof.issue_codes,
        ),
    )
    trace = tuple(
        replace(row, artifact_common_guard_proof_ref=proof.proof_id)
        for row in artifact.trace
    )
    return replace(
        artifact,
        common_guard_proof=proof,
        trace=trace,
        artifact_id=_artifact_id(
            source.envelope.envelope_id,
            graph.graph_id,
            artifact.plan.plan_id,
            proof.proof_id,
            artifact.observation,
            tuple(row.text for row in artifact.visible_unknowns),
            artifact.reception,
        ),
    )


def _build_with_common_core_mutation(mutator):
    source = freeze_text_source(_request())
    original = emlis_v1a_module.compose_emlis_conversation_candidate

    def mutate_result(*args, **kwargs):
        candidate = original(*args, **kwargs)
        composer_meta = copy.deepcopy(candidate.composer_meta)
        core_meta = composer_meta["core_text_generation"]
        mutator(core_meta)
        return replace(candidate, composer_meta=composer_meta)

    with patch.object(
        emlis_v1a_module,
        "compose_emlis_conversation_candidate",
        side_effect=mutate_result,
    ):
        return build_text_grounded_limited_artifact(source)


def _build_with_composer_candidate_mutation(mutator):
    source = freeze_text_source(_request())
    original = emlis_v1a_module.compose_emlis_conversation_candidate

    def mutate_result(*args, **kwargs):
        candidate = original(*args, **kwargs)
        return mutator(candidate)

    with patch.object(
        emlis_v1a_module,
        "compose_emlis_conversation_candidate",
        side_effect=mutate_result,
    ):
        return build_text_grounded_limited_artifact(source)


class CMEEV1AI1SXVerticalTest(unittest.TestCase):
    def test_real_text_input_reaches_graph_plan_artifact_and_exact_positive_trace(self) -> None:
        outcome = MeaningExperienceEngine().generate(_request())

        self.assertEqual(outcome.status.value, "LIMITED", outcome.reason_codes)
        self.assertIsNotNone(outcome.source_envelope)
        self.assertIsNotNone(outcome.meaning_graph)
        self.assertIsNotNone(outcome.artifact)
        graph = outcome.meaning_graph
        artifact = outcome.artifact
        assert graph is not None and artifact is not None
        self.assertTrue(artifact.observation)
        self.assertTrue(artifact.reception)
        roles = tuple(row.role for row in artifact.trace)
        self.assertGreaterEqual(roles.count("OBSERVATION"), 1)
        self.assertEqual(roles.count("UNKNOWN"), 1)
        self.assertEqual(roles.count("RECEPTION"), 1)
        self.assertEqual(roles[-1], "RECEPTION")
        self.assertTrue(all(row.evidence_ids for row in artifact.trace))
        self.assertEqual(
            tuple(row.owner_id for row in graph.owner_dispositions),
            graph.required_owner_refs + graph.active_optional_owner_refs,
        )
        source = freeze_text_source(_request())
        self.assertEqual(
            graph.owner_universe_digest,
            source.owner_universe.owner_universe_digest,
        )
        binding = (
            graph.source_envelope_id,
            graph.source_version,
            graph.obligation_version,
            graph.owner_universe_digest,
        )
        self.assertEqual(
            (
                artifact.plan.source_envelope_id,
                artifact.plan.source_version,
                artifact.plan.obligation_version,
                artifact.plan.owner_universe_digest,
            ),
            binding,
        )
        self.assertTrue(
            all(
                (
                    row.source_envelope_id,
                    row.source_version,
                    row.obligation_version,
                    row.owner_universe_digest,
                )
                == binding
                for row in artifact.trace
            )
        )
        self.assertEqual(outcome.terminal_state, CMEE_TERMINAL_GENERATED_DISABLED)
        self.assertNotIn("CANDIDATE_READY", outcome.terminal_state)
        self.assertFalse(outcome.automatic_progression)

    def test_common_guard_proof_seals_exact5_and_binds_artifact_trace(self) -> None:
        outcome = MeaningExperienceEngine().generate(_request())
        assert outcome.meaning_graph is not None and outcome.artifact is not None
        graph = outcome.meaning_graph
        artifact = outcome.artifact
        proof = artifact.common_guard_proof

        self.assertEqual(proof.schema_version, CMEE_COMMON_GUARD_PROOF_VERSION)
        self.assertEqual(proof.source_envelope_id, graph.source_envelope_id)
        self.assertEqual(proof.graph_id, graph.graph_id)
        self.assertEqual(proof.plan_id, artifact.plan.plan_id)
        self.assertEqual(
            tuple(row.guard_id for row in proof.guard_results),
            EXPECTED_COMMON_GUARD_IDS,
        )
        self.assertTrue(
            all(type(row.passed) is bool and row.passed is True for row in proof.guard_results)
        )
        self.assertIs(proof.stabilization_passed, True)
        self.assertIs(proof.common_shapes_ready, True)
        self.assertEqual(proof.stabilization_guard_names, EXPECTED_COMMON_GUARD_IDS)
        self.assertEqual(proof.issue_codes, ())
        self.assertEqual(
            proof.guarded_observation_units,
            tuple(
                (row.source_sentence_id, row.text_sha256)
                for row in artifact.trace
                if row.role == "OBSERVATION"
            ),
        )
        self.assertTrue(proof.guarded_observation_units)
        self.assertTrue(
            all(
                row.artifact_common_guard_proof_ref == proof.proof_id
                for row in artifact.trace
            )
        )
        self.assertTrue(
            all(
                sentence_id.startswith("cmee:observation:")
                for sentence_id, _text_sha256 in proof.guarded_observation_units
            )
        )
        self.assertNotIn(REPRESENTATIVE_MEMO, repr(proof))

    def test_actual_common_guard_rows_require_exact_order_identity_and_true_bool(self) -> None:
        def guard_rows(core_meta):
            return core_meta["result"]["meta"]["guard_results"]

        def passed_false(core_meta):
            guard_rows(core_meta)[0]["passed"] = False

        def passed_truthy_int(core_meta):
            guard_rows(core_meta)[0]["passed"] = 1

        def passed_with_rejection_reason(core_meta):
            guard_rows(core_meta)[0]["rejection_reasons"] = ["ACTUAL_FAILURE"]

        def wrong_identity(core_meta):
            guard_rows(core_meta)[0]["guard_name"] = "forged.guard.v1"

        def missing_row(core_meta):
            guard_rows(core_meta).pop()

        def extra_row(core_meta):
            guard_rows(core_meta).append(copy.deepcopy(guard_rows(core_meta)[-1]))

        def duplicate_row(core_meta):
            guard_rows(core_meta)[1] = copy.deepcopy(guard_rows(core_meta)[0])

        def reordered_rows(core_meta):
            rows = guard_rows(core_meta)
            rows[0], rows[1] = rows[1], rows[0]

        mutations = {
            "passed_false": passed_false,
            "passed_truthy_int": passed_truthy_int,
            "passed_with_rejection_reason": passed_with_rejection_reason,
            "wrong_identity": wrong_identity,
            "missing_row": missing_row,
            "extra_row": extra_row,
            "duplicate_row": duplicate_row,
            "reordered_rows": reordered_rows,
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                with self.assertRaises(CMEEVerticalError):
                    _build_with_common_core_mutation(mutate)

    def test_common_guard_proof_rejects_outer_binding_text_swap(self) -> None:
        forged_text = "あなたは絶対に病気だと確定しました。"

        def outer_text_only(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["sentence_bindings"][0]["text"] = forged_text
            return replace(candidate, composer_meta=composer_meta)

        def guarded_snapshot_text_only(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            guarded_bindings = composer_meta["core_text_generation"]["result"]["meta"][
                "candidate"
            ]["meta"]["sentence_bindings"]
            guarded_bindings[0]["text"] = "これはguard済みではありません。"
            return replace(candidate, composer_meta=composer_meta)

        def coordinated_outer_and_snapshot_text(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["sentence_bindings"][0]["text"] = forged_text
            guarded_bindings = composer_meta["core_text_generation"]["result"]["meta"][
                "candidate"
            ]["meta"]["sentence_bindings"]
            guarded_bindings[0]["text"] = forged_text
            return replace(candidate, composer_meta=composer_meta)

        def coordinated_bindings_and_claim_text(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["sentence_bindings"][0]["text"] = forged_text
            result_meta = composer_meta["core_text_generation"]["result"]["meta"]
            result_meta["candidate"]["meta"]["sentence_bindings"][0]["text"] = (
                forged_text
            )
            result_meta["guard_results"][3]["meta"]["sentence_claims"][0][
                "sentence"
            ] = forged_text.rstrip("。")
            return replace(candidate, composer_meta=composer_meta)

        def coordinated_bindings_claim_and_surface_text(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["sentence_bindings"][0]["text"] = forged_text
            result_meta = composer_meta["core_text_generation"]["result"]["meta"]
            result_meta["candidate"]["meta"]["sentence_bindings"][0]["text"] = (
                forged_text
            )
            result_meta["guard_results"][3]["meta"]["sentence_claims"][0][
                "sentence"
            ] = forged_text.rstrip("。")
            surface_lines = candidate.comment_text.splitlines()
            surface_lines[1] = f"今回の入力では、{forged_text}"
            return replace(
                candidate,
                comment_text="\n".join(surface_lines),
                composer_meta=composer_meta,
            )

        def coordinated_all_primary_guard_snapshots(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["sentence_bindings"][0]["text"] = forged_text
            result_meta = composer_meta["core_text_generation"]["result"]["meta"]
            result_meta["candidate"]["meta"]["sentence_bindings"][0]["text"] = (
                forged_text
            )
            result_meta["guard_results"][3]["meta"]["sentence_claims"][0][
                "sentence"
            ] = forged_text.rstrip("。")
            result_meta["combined_guard_result"]["meta"]["guard_results"][3][
                "meta"
            ]["sentence_claims"][0]["sentence"] = forged_text.rstrip("。")
            surface_lines = candidate.comment_text.splitlines()
            surface_lines[1] = f"今回の入力では、{forged_text}"
            return replace(
                candidate,
                comment_text="\n".join(surface_lines),
                composer_meta=composer_meta,
            )

        def guarded_binding_alias_text_only(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            candidate_meta = composer_meta["core_text_generation"]["result"]["meta"][
                "candidate"
            ]["meta"]
            candidate_meta["sentence_binding_bundle"]["bindings"][0]["text"] = (
                forged_text
            )
            return replace(candidate, composer_meta=composer_meta)

        def grounding_claim_text_only(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            claims = composer_meta["core_text_generation"]["result"]["meta"][
                "guard_results"
            ][3]["meta"]["sentence_claims"]
            claims[0]["sentence"] = "これはguard済みではありません"
            return replace(candidate, composer_meta=composer_meta)

        def coordinated_exact6_key_missing(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            core_meta = composer_meta["core_text_generation"]
            core_meta["sentence_bindings"][0].pop("used_phrase_unit_ids")
            composer_meta["sentence_bindings"][0].pop("used_phrase_unit_ids")
            core_meta["result"]["meta"]["candidate"]["meta"]["sentence_bindings"][
                0
            ].pop("used_phrase_unit_ids")
            return replace(candidate, composer_meta=composer_meta)

        for name, mutate in {
            "outer_text_only": outer_text_only,
            "guarded_snapshot_text_only": guarded_snapshot_text_only,
            "coordinated_outer_and_snapshot_text": coordinated_outer_and_snapshot_text,
            "coordinated_bindings_and_claim_text": coordinated_bindings_and_claim_text,
            "coordinated_bindings_claim_and_surface_text": (
                coordinated_bindings_claim_and_surface_text
            ),
            "coordinated_all_primary_guard_snapshots": (
                coordinated_all_primary_guard_snapshots
            ),
            "guarded_binding_alias_text_only": guarded_binding_alias_text_only,
            "grounding_claim_text_only": grounding_claim_text_only,
            "coordinated_exact6_key_missing": coordinated_exact6_key_missing,
        }.items():
            with self.subTest(name=name):
                with self.assertRaises(CMEEVerticalError):
                    _build_with_composer_candidate_mutation(mutate)

    def test_actual_common_guard_stabilization_requires_exact_success(self) -> None:
        def stabilization(core_meta):
            return core_meta["step15_common_core_stabilization"]

        def combined_false(core_meta):
            core_meta["result"]["meta"]["combined_guard_result"]["passed"] = False

        def combined_truthy_int(core_meta):
            core_meta["result"]["meta"]["combined_guard_result"]["passed"] = 1

        def combined_nested_row_tampered(core_meta):
            combined_rows = core_meta["result"]["meta"]["combined_guard_result"][
                "meta"
            ]["guard_results"]
            combined_rows[0]["passed"] = False

        def report_identity(core_meta):
            stabilization(core_meta)["report_name"] = "forged.stabilization.v1"

        def stabilization_false(core_meta):
            stabilization(core_meta)["passed"] = False

        def stabilization_truthy_int(core_meta):
            stabilization(core_meta)["passed"] = 1

        def shapes_false(core_meta):
            stabilization(core_meta)["common_shapes_ready"] = False

        def shapes_truthy_int(core_meta):
            stabilization(core_meta)["common_shapes_ready"] = 1

        def issue_added(core_meta):
            stabilization(core_meta)["issue_codes"] = ["FORGED"]

        def guard_names_reordered(core_meta):
            names = stabilization(core_meta)["guard_names"]
            names[0], names[1] = names[1], names[0]

        def shape_part_false(core_meta):
            stabilization(core_meta)["shared_quality_parts"]["GuardResult"] = False

        def shape_part_truthy_int(core_meta):
            stabilization(core_meta)["shared_quality_parts"]["GuardResult"] = 1

        mutations = {
            "combined_false": combined_false,
            "combined_truthy_int": combined_truthy_int,
            "combined_nested_row_tampered": combined_nested_row_tampered,
            "report_identity": report_identity,
            "stabilization_false": stabilization_false,
            "stabilization_truthy_int": stabilization_truthy_int,
            "shapes_false": shapes_false,
            "shapes_truthy_int": shapes_truthy_int,
            "issue_added": issue_added,
            "guard_names_reordered": guard_names_reordered,
            "shape_part_false": shape_part_false,
            "shape_part_truthy_int": shape_part_truthy_int,
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                with self.assertRaises(CMEEVerticalError):
                    _build_with_common_core_mutation(mutate)

    def test_common_guard_proof_mutations_reject_after_coordinated_rehash(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        proof = artifact.common_guard_proof

        changed_rows = list(proof.guard_results)
        changed_rows[0] = replace(changed_rows[0], passed=False)
        passed_false = replace(proof, guard_results=tuple(changed_rows))
        changed_rows = list(proof.guard_results)
        changed_rows[0] = replace(changed_rows[0], passed=1)
        passed_truthy_int = replace(proof, guard_results=tuple(changed_rows))
        changed_rows = list(proof.guard_results)
        changed_rows[0] = replace(changed_rows[0], guard_id="forged.guard.v1")
        wrong_identity = replace(proof, guard_results=tuple(changed_rows))
        changed_rows = list(proof.guard_results)
        changed_rows[0], changed_rows[1] = changed_rows[1], changed_rows[0]
        reordered = replace(proof, guard_results=tuple(changed_rows))
        unknown_trace = next(row for row in artifact.trace if row.role == "UNKNOWN")
        mutations = {
            "schema": replace(proof, schema_version="forged.proof.v1"),
            "passed_false": passed_false,
            "passed_truthy_int": passed_truthy_int,
            "wrong_identity": wrong_identity,
            "missing_row": replace(proof, guard_results=proof.guard_results[:-1]),
            "extra_row": replace(
                proof,
                guard_results=(
                    *proof.guard_results,
                    CommonGuardResultProof(guard_id="forged.extra.v1", passed=True),
                ),
            ),
            "reordered": reordered,
            "stabilization_false": replace(proof, stabilization_passed=False),
            "stabilization_truthy_int": replace(proof, stabilization_passed=1),
            "shapes_false": replace(proof, common_shapes_ready=False),
            "issue_added": replace(proof, issue_codes=("FORGED",)),
            "guard_names_reordered": replace(
                proof,
                stabilization_guard_names=(
                    proof.stabilization_guard_names[1],
                    proof.stabilization_guard_names[0],
                    *proof.stabilization_guard_names[2:],
                ),
            ),
            "unknown_inserted_into_guarded_units": replace(
                proof,
                guarded_observation_units=(
                    *proof.guarded_observation_units,
                    (unknown_trace.source_sentence_id, unknown_trace.text_sha256),
                ),
            ),
            "source_binding": replace(proof, source_envelope_id="source:foreign"),
            "graph_binding": replace(proof, graph_id="graph:foreign"),
            "plan_binding": replace(proof, plan_id="plan:foreign"),
        }
        for name, changed_proof in mutations.items():
            with self.subTest(name=name):
                changed_artifact = _rehash_common_guard_proof_artifact(
                    source,
                    graph,
                    artifact,
                    changed_proof,
                )
                with self.assertRaises(CMEEVerticalError):
                    validate_positive_realization_trace(
                        source,
                        graph,
                        changed_artifact,
                        visible,
                    )

        other_source, _other_graph, _other_plan, other_artifact, _other_visible = (
            _private_parts(_request(record_id="cmee-common-guard-proof-foreign"))
        )
        self.assertNotEqual(
            other_source.envelope.envelope_id,
            source.envelope.envelope_id,
        )
        copied = _rehash_common_guard_proof_artifact(
            source,
            graph,
            artifact,
            other_artifact.common_guard_proof,
        )
        with self.assertRaisesRegex(CMEEVerticalError, "proof_artifact_binding"):
            validate_positive_realization_trace(source, graph, copied, visible)

        missing_proof = replace(artifact, common_guard_proof=None)
        with self.assertRaisesRegex(CMEEVerticalError, "proof_type"):
            validate_positive_realization_trace(source, graph, missing_proof, visible)

        bad_trace = (
            replace(
                artifact.trace[0],
                artifact_common_guard_proof_ref="common-guard-proof-foreign",
            ),
            *artifact.trace[1:],
        )
        with self.assertRaisesRegex(CMEEVerticalError, "proof_trace_binding"):
            validate_positive_realization_trace(
                source,
                graph,
                replace(artifact, trace=bad_trace),
                visible,
            )

    def test_every_required_meaning_owner_is_realized_without_provisional_promotion(self) -> None:
        outcome = MeaningExperienceEngine().generate(_request())
        assert outcome.meaning_graph is not None and outcome.artifact is not None
        graph = outcome.meaning_graph
        visible_edges = {
            edge_id
            for trace in outcome.artifact.trace
            for edge_id in trace.meaning_edge_ids
        }
        disposition = {row.owner_id: row.disposition for row in graph.owner_dispositions}

        realized_owner_ids = {
            *(
                graph_node.owner_id
                for trace in outcome.artifact.trace
                if trace.role == "OBSERVATION"
                for graph_node in graph.nodes
                if graph_node.node_id in trace.meaning_node_ids
            ),
            *(
                graph_edge.owner_id
                for trace in outcome.artifact.trace
                if trace.role == "OBSERVATION"
                for graph_edge in graph.edges
                if graph_edge.edge_id in trace.meaning_edge_ids
            ),
        }
        self.assertEqual(realized_owner_ids, set(outcome.artifact.plan.required_observation_owner_ids))
        for edge in graph.edges:
            if edge.grounding_kind == "bounded_structural_inference":
                self.assertEqual(edge.epistemic_state, EpistemicState.UNKNOWN)
                self.assertNotIn(edge.edge_id, visible_edges)
                self.assertEqual(
                    disposition[edge.owner_id],
                    RouteBDisposition.UNKNOWN_PRESERVED_LIMITED,
                )
            if edge.edge_id in visible_edges:
                self.assertEqual(edge.grounding_kind, "user_stated_relation")
                self.assertEqual(edge.epistemic_state, EpistemicState.SOURCE_EXPLICIT)
        strength_node = next(
            row for row in graph.nodes if row.node_kind == "STRUCTURED_EMOTION_STRENGTH"
        )
        self.assertEqual(strength_node.epistemic_state, EpistemicState.SOURCE_EXPLICIT)
        self.assertEqual(
            disposition[strength_node.owner_id],
            RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
        )

    def test_complete_route_b_rows_and_evidence_bound_unknown_are_exact(self) -> None:
        source, graph, _plan, artifact, _visible = _private_parts(_request())
        universe = source.owner_universe
        obligations = {
            row.meaning_owner_id: row for row in universe.obligations
        }
        self.assertEqual(
            tuple(row.meaning_owner_id for row in graph.owner_dispositions),
            universe.required_owner_refs + universe.active_optional_owner_refs,
        )
        self.assertEqual(
            len(graph.owner_dispositions),
            len({row.meaning_owner_id for row in graph.owner_dispositions}),
        )
        for row in graph.owner_dispositions:
            obligation = obligations[row.meaning_owner_id]
            self.assertEqual(row.owner_class, obligation.owner_class)
            self.assertEqual(row.evidence_refs, obligation.evidence_refs)
            if obligation.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT":
                self.assertEqual(
                    row.provider_resolution,
                    ProviderResolution.MISSING_OR_INVALID,
                )
                self.assertEqual(row.attachment_admission, AttachmentAdmission.UNAVAILABLE)
                self.assertEqual(
                    row.route_b_disposition,
                    RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
                )
                self.assertEqual(row.visible_authority, VisibleAuthority.NONE)
                self.assertEqual(row.visible_claim_refs, ())
                self.assertIsNone(row.target_unknown_ref)
                self.assertEqual(row.reason_codes, ("ATTACHMENT_UNRESOLVED",))
            elif row.route_b_disposition is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE:
                self.assertEqual(
                    row.provider_resolution,
                    ProviderResolution.MISSING_OR_INVALID,
                )
                self.assertEqual(row.attachment_admission, AttachmentAdmission.UNAVAILABLE)
                self.assertEqual(row.visible_authority, VisibleAuthority.SOURCE_EXPLICIT)
                self.assertTrue(row.visible_claim_refs)
                self.assertIsNone(row.target_unknown_ref)
                self.assertEqual(row.reason_codes, ())
            else:
                self.assertEqual(
                    row.provider_resolution,
                    ProviderResolution.MISSING_OR_INVALID,
                )
                self.assertEqual(row.attachment_admission, AttachmentAdmission.UNAVAILABLE)
                self.assertEqual(row.route_b_disposition, RouteBDisposition.NOT_VISIBLE_UNRESOLVED)
                self.assertEqual(row.visible_authority, VisibleAuthority.NONE)
                self.assertEqual(row.visible_claim_refs, ())
                self.assertEqual(row.reason_codes, ("ATTACHMENT_UNRESOLVED",))

        unknown_trace = tuple(row for row in artifact.trace if row.role == "UNKNOWN")
        self.assertEqual(len(unknown_trace), 1)
        self.assertEqual(len(artifact.visible_unknowns), 1)
        self.assertEqual(
            unknown_trace[0].constrained_by_owner_ids,
            artifact.plan.visible_unknown_owner_ids,
        )
        self.assertTrue(unknown_trace[0].evidence_ids)
        self.assertEqual(unknown_trace[0].meaning_node_ids, ())
        self.assertEqual(unknown_trace[0].meaning_edge_ids, ())
        self.assertEqual(unknown_trace[0].duty_id, artifact.plan.unknown_duty_id)
        self.assertEqual(
            {
                row.meaning_owner_id
                for row in graph.owner_dispositions
                if row.owner_class is OwnerClass.REQUIRED
                and row.route_b_disposition
                not in {
                    RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
                    RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
                }
            },
            set(artifact.plan.required_unknown_owner_ids),
        )
        self.assertEqual(artifact.plan.required_unknown_owner_ids, ())
        self.assertTrue(
            all(
                next(
                    ref
                    for ref in source.evidence_refs
                    if ref.evidence_id == evidence_id
                ).source_envelope_id
                == source.envelope.envelope_id
                for evidence_id in unknown_trace[0].evidence_ids
            )
        )

    def test_route_b_owner_and_disposition_mutations_are_rejected(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        positive_index = next(
            index
            for index, row in enumerate(graph.owner_dispositions)
            if row.route_b_disposition is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
        )
        positive = graph.owner_dispositions[positive_index]
        other_source = freeze_text_source(_request(record_id="cmee-foreign"))
        foreign_evidence = other_source.evidence_refs[0].evidence_id
        field_mutations = {
            "owner_class": replace(positive, owner_class=OwnerClass.ACTIVE_OPTIONAL),
            "provider_resolution": replace(
                positive,
                provider_resolution=ProviderResolution.UNRESOLVED,
            ),
            "attachment_admission": replace(
                positive,
                attachment_admission=AttachmentAdmission.UNRESOLVED,
            ),
            "visible_authority": replace(
                positive,
                visible_authority=VisibleAuthority.NONE,
            ),
            "route_b_disposition": replace(
                positive,
                route_b_disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
            ),
            "visible_claim_refs": replace(positive, visible_claim_refs=()),
            "evidence_refs": replace(positive, evidence_refs=(foreign_evidence,)),
            "target_unknown_ref": replace(positive, target_unknown_ref="unknown:foreign"),
            "reason_codes": replace(positive, reason_codes=("tampered",)),
        }
        for field_name, changed_row in field_mutations.items():
            with self.subTest(field_name=field_name):
                changed_rows = list(graph.owner_dispositions)
                changed_rows[positive_index] = changed_row
                changed_graph = _rehash_graph(
                    replace(graph, owner_dispositions=tuple(changed_rows))
                )
                changed_artifact = _rehash_artifact(source, changed_graph, artifact)
                with self.assertRaises(CMEEVerticalError):
                    validate_positive_realization_trace(
                        source,
                        changed_graph,
                        changed_artifact,
                        visible,
                    )

        omitted_graph = _rehash_graph(
            replace(graph, owner_dispositions=graph.owner_dispositions[:-1])
        )
        with self.assertRaisesRegex(CMEEVerticalError, "owner_denominator"):
            validate_positive_realization_trace(source, omitted_graph, artifact, visible)

        duplicate_graph = _rehash_graph(
            replace(
                graph,
                owner_dispositions=(
                    *graph.owner_dispositions,
                    graph.owner_dispositions[-1],
                ),
            )
        )
        with self.assertRaisesRegex(CMEEVerticalError, "owner_denominator"):
            validate_positive_realization_trace(source, duplicate_graph, artifact, visible)

        shrunk_graph = _rehash_graph(
            replace(
                graph,
                owner_dispositions=graph.owner_dispositions[:-1],
                active_optional_owner_refs=graph.active_optional_owner_refs[:-1],
                owner_universe_digest="f" * 64,
            )
        )
        with self.assertRaises(CMEEVerticalError):
            validate_positive_realization_trace(source, shrunk_graph, artifact, visible)

    def test_universe_swap_and_binding_mutations_are_rejected(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        other_source = freeze_text_source(_request(record_id="cmee-same-shape-other"))
        swapped_digest = other_source.owner_universe.owner_universe_digest
        swapped_graph = _rehash_graph(
            replace(graph, owner_universe_digest=swapped_digest)
        )
        swapped_plan = replace(
            artifact.plan,
            owner_universe_digest=swapped_digest,
        )
        swapped_plan = replace(
            swapped_plan,
            plan_id=_plan_id(
                source.envelope.envelope_id,
                swapped_graph.graph_id,
                swapped_plan,
                swapped_plan.visible_line_ids,
            ),
        )
        swapped_trace = tuple(
            replace(row, owner_universe_digest=swapped_digest)
            for row in artifact.trace
        )
        swapped_unknowns = tuple(
            replace(row, owner_universe_digest=swapped_digest)
            for row in artifact.visible_unknowns
        )
        swapped_artifact = replace(
            artifact,
            plan=swapped_plan,
            trace=swapped_trace,
            visible_unknowns=swapped_unknowns,
            artifact_id=_artifact_id(
                source.envelope.envelope_id,
                swapped_graph.graph_id,
                swapped_plan.plan_id,
                artifact.common_guard_proof.proof_id,
                artifact.observation,
                tuple(row.text for row in swapped_unknowns),
                artifact.reception,
            ),
        )
        with self.assertRaisesRegex(CMEEVerticalError, "owner_universe_binding"):
            validate_positive_realization_trace(
                source,
                swapped_graph,
                swapped_artifact,
                visible,
            )

        bad_plan = replace(artifact.plan, obligation_version="tampered")
        bad_plan = replace(
            bad_plan,
            plan_id=_plan_id(
                source.envelope.envelope_id,
                graph.graph_id,
                bad_plan,
                bad_plan.visible_line_ids,
            ),
        )
        bad_plan_artifact = replace(artifact, plan=bad_plan)
        with self.assertRaises(CMEEVerticalError):
            validate_positive_realization_trace(
                source,
                graph,
                bad_plan_artifact,
                visible,
            )

        bad_trace = (
            replace(artifact.trace[0], source_version="cross-source-version"),
            *artifact.trace[1:],
        )
        with self.assertRaisesRegex(CMEEVerticalError, "trace_universe_binding"):
            validate_positive_realization_trace(
                source,
                graph,
                replace(artifact, trace=bad_trace),
                visible,
            )

    def test_hidden_unknown_is_rejected_after_coordinated_rehash(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        visible_without_unknown = tuple(
            row for row in visible if row.binding.line_role != "cmee_unknown"
        )
        trace_without_unknown = tuple(
            replace(row, visible_unit_id=f"visible:{ordinal}")
            for ordinal, row in enumerate(
                (row for row in artifact.trace if row.role != "UNKNOWN"),
                start=1,
            )
        )
        hidden_plan = replace(
            artifact.plan,
            visible_line_ids=tuple(row.sentence_id for row in visible_without_unknown),
        )
        hidden_plan = replace(
            hidden_plan,
            plan_id=_plan_id(
                source.envelope.envelope_id,
                graph.graph_id,
                hidden_plan,
                hidden_plan.visible_line_ids,
            ),
        )
        hidden_artifact = _rehash_artifact(
            source,
            graph,
            replace(
                artifact,
                plan=hidden_plan,
                trace=trace_without_unknown,
                visible_unknowns=(),
            ),
        )
        with self.assertRaisesRegex(CMEEVerticalError, "visible_line_role_cardinality"):
            validate_positive_realization_trace(
                source,
                graph,
                hidden_artifact,
                visible_without_unknown,
            )

    def test_unknown_text_and_evidence_subset_tampering_are_rejected(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        unknown_index = next(
            index
            for index, row in enumerate(visible)
            if row.binding.line_role == "cmee_unknown"
        )
        unknown_line = visible[unknown_index]
        unknown_trace = artifact.trace[unknown_index]

        causal_text = "仕事が原因だと分かります。"
        causal_visible = list(visible)
        causal_visible[unknown_index] = replace(unknown_line, text=causal_text)
        causal_trace = list(artifact.trace)
        causal_trace[unknown_index] = replace(
            unknown_trace,
            text_sha256=_sha256_text(causal_text),
        )
        causal_unknowns = (
            replace(artifact.visible_unknowns[0], text=causal_text),
        )
        causal_artifact = replace(
            artifact,
            trace=tuple(causal_trace),
            visible_unknowns=causal_unknowns,
            artifact_id=_artifact_id(
                source.envelope.envelope_id,
                graph.graph_id,
                artifact.plan.plan_id,
                artifact.common_guard_proof.proof_id,
                artifact.observation,
                (causal_text,),
                artifact.reception,
            ),
        )
        with self.assertRaisesRegex(CMEEVerticalError, "unknown_canonical_binding"):
            validate_positive_realization_trace(
                source,
                graph,
                causal_artifact,
                tuple(causal_visible),
            )

        reduced_span_ids = unknown_line.binding.evidence_span_ids[:1]
        reduced_evidence_ids = (
            source.evidence_ref(reduced_span_ids[0]).evidence_id,
        )
        reduced_visible = list(visible)
        reduced_visible[unknown_index] = replace(
            unknown_line,
            binding=replace(
                unknown_line.binding,
                evidence_span_ids=reduced_span_ids,
            ),
        )
        reduced_trace = list(artifact.trace)
        reduced_trace[unknown_index] = replace(
            unknown_trace,
            evidence_ids=reduced_evidence_ids,
        )
        reduced_unknowns = (
            replace(
                artifact.visible_unknowns[0],
                evidence_ids=reduced_evidence_ids,
            ),
        )
        reduced_artifact = replace(
            artifact,
            trace=tuple(reduced_trace),
            visible_unknowns=reduced_unknowns,
        )
        with self.assertRaisesRegex(CMEEVerticalError, "unknown_canonical_binding"):
            validate_positive_realization_trace(
                source,
                graph,
                reduced_artifact,
                tuple(reduced_visible),
            )

    def test_unknown_without_current_source_evidence_is_unavailable(self) -> None:
        source = freeze_text_source(_request())
        obligations = list(source.owner_universe.obligations)
        unknown_index = next(
            index
            for index, row in enumerate(obligations)
            if row.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        obligations[unknown_index] = replace(
            obligations[unknown_index],
            source_span_ids=(),
            evidence_refs=(),
        )
        damaged_source = replace(
            source,
            owner_universe=replace(
                source.owner_universe,
                obligations=tuple(obligations),
            ),
        )
        with patch(
            "cocolon_meaning_experience_engine.engine.freeze_text_source",
            return_value=damaged_source,
        ):
            outcome = MeaningExperienceEngine().generate(_request())

        self.assertEqual(outcome.status.value, "UNAVAILABLE")
        self.assertIsNone(outcome.artifact)
        self.assertEqual(outcome.reason_codes, ("source_owner_universe_mismatch",))

    def test_unresolved_required_owner_without_visible_unknown_fails_closed(self) -> None:
        source, graph, _plan, _artifact, _visible = _private_parts(_request())
        grounded_plan = build_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(grounded_plan)
        )
        rows = list(graph.owner_dispositions)
        required_visible_index = next(
            index
            for index, row in enumerate(rows)
            if row.owner_class is OwnerClass.REQUIRED
            and row.route_b_disposition is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
        )
        rows[required_visible_index] = replace(
            rows[required_visible_index],
            visible_authority=VisibleAuthority.NONE,
            route_b_disposition=RouteBDisposition.NOT_VISIBLE_UNRESOLVED,
            visible_claim_refs=(),
            target_unknown_ref=None,
            reason_codes=("ATTACHMENT_UNRESOLVED",),
        )
        changed_graph = replace(graph, owner_dispositions=tuple(rows))

        with self.assertRaisesRegex(CMEEVerticalError, "required_unknown_not_safely_visible"):
            _build_experience_plan(
                source,
                changed_graph,
                grounded_plan,
                required_nuclei,
                required_relations,
                reception_targets,
            )

    def test_trace_tamper_is_rejected(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        first = artifact.trace[0]
        tampered_trace = (replace(first, evidence_ids=("foreign-evidence",)),) + artifact.trace[1:]
        tampered = replace(artifact, trace=tampered_trace)

        with self.assertRaisesRegex(CMEEVerticalError, "visible_trace_exact_binding_mismatch"):
            validate_positive_realization_trace(source, graph, tampered, visible)

    def test_positive_roles_reject_a_source_explicit_but_nonvisible_owner(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        strength_node = next(
            row for row in graph.nodes if row.node_kind == "STRUCTURED_EMOTION_STRENGTH"
        )
        strength_ref = source.evidence_ref("structured:emotion_strength")
        for role in ("OBSERVATION", "RECEPTION"):
            with self.subTest(role=role):
                trace_index = next(
                    index for index, row in enumerate(artifact.trace) if row.role == role
                )
                changed_visible = list(visible)
                changed_visible[trace_index] = replace(
                    changed_visible[trace_index],
                    binding=replace(
                        changed_visible[trace_index].binding,
                        nucleus_ids=(strength_node.owner_id,),
                        relation_ids=(),
                        evidence_span_ids=(strength_ref.source_span_id,),
                    ),
                )
                changed_trace = list(artifact.trace)
                changed_trace[trace_index] = replace(
                    changed_trace[trace_index],
                    meaning_node_ids=(strength_node.node_id,),
                    meaning_edge_ids=(),
                    evidence_ids=(strength_ref.evidence_id,),
                )
                with self.assertRaisesRegex(
                    CMEEVerticalError,
                    "visible_trace_node_authority_mismatch",
                ):
                    validate_positive_realization_trace(
                        source,
                        graph,
                        replace(artifact, trace=tuple(changed_trace)),
                        tuple(changed_visible),
                    )

    def test_same_source_is_deterministic_and_semantic_mutation_changes_identity(self) -> None:
        request = _request()
        first = MeaningExperienceEngine().generate(request)
        second = MeaningExperienceEngine().generate(request)
        changed = MeaningExperienceEngine().generate(
            _request(
                record_id="cmee-vertical-2",
                memo="続けたい気持ちはあるけれど、疲れて動けない。",
                category="生活",
                emotion="不安",
            )
        )

        self.assertEqual(first.status.value, second.status.value, "LIMITED")
        self.assertEqual(first.meaning_graph, second.meaning_graph)
        self.assertEqual(first.artifact, second.artifact)
        self.assertEqual(changed.status.value, "LIMITED", changed.reason_codes)
        assert first.source_envelope and first.artifact and changed.source_envelope and changed.artifact
        self.assertNotEqual(first.source_envelope.envelope_id, changed.source_envelope.envelope_id)
        self.assertNotEqual(first.artifact.artifact_id, changed.artifact.artifact_id)
        self.assertNotEqual(first.artifact.observation, changed.artifact.observation)

    def test_positive_experience_is_unavailable_instead_of_acquiring_burden(self) -> None:
        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id="cmee-positive",
                memo="友達と話せて嬉しかった。",
                category="人間関係",
                emotion="喜び",
            )
        )
        self.assertEqual(outcome.status.value, "UNAVAILABLE", outcome.reason_codes)
        self.assertIn(
            outcome.reason_codes[0],
            {
                "plan_bound_observation_realizer_unavailable",
                "bound_human_reception_positive_burden_promotion",
            },
        )
        self.assertIsNone(outcome.artifact)

    def test_relation_required_input_is_unavailable_without_endpoint_binding(self) -> None:
        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id="cmee-relation",
                memo="この職場でやっていけるか不安。でも、続けられる形は探したい。",
            )
        )
        self.assertEqual(outcome.status.value, "UNAVAILABLE")
        self.assertEqual(outcome.reason_codes, ("relation_endpoint_binding_not_supported",))
        self.assertIsNone(outcome.artifact)

    def test_coordinated_rehash_cannot_replace_source_semantics(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        changed_node = replace(graph.nodes[0], value="unrelated meaning")
        changed_nodes = (changed_node,) + graph.nodes[1:]
        changed_graph = replace(
            graph,
            nodes=changed_nodes,
            graph_id=_graph_id(
                graph.source_envelope_id,
                graph.owner_universe_digest,
                changed_nodes,
                graph.edges,
                graph.owner_dispositions,
            ),
        )
        changed_plan = replace(
            artifact.plan,
            plan_id=_plan_id(
                source.envelope.envelope_id,
                changed_graph.graph_id,
                artifact.plan,
                artifact.plan.visible_line_ids,
            ),
        )
        changed_artifact = replace(
            artifact,
            plan=changed_plan,
            artifact_id=_artifact_id(
                source.envelope.envelope_id,
                changed_graph.graph_id,
                changed_plan.plan_id,
                artifact.common_guard_proof.proof_id,
                artifact.observation,
                tuple(row.text for row in artifact.visible_unknowns),
                artifact.reception,
            ),
        )

        with self.assertRaisesRegex(CMEEVerticalError, "source_semantic_mismatch"):
            validate_positive_realization_trace(
                source,
                changed_graph,
                changed_artifact,
                visible,
            )

    def test_safety_routed_input_never_emits_a_limited_artifact(self) -> None:
        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id="cmee-safety",
                memo="自分には何もできない。それでも、明日の予約は取り消していない。",
                category="健康",
            )
        )
        self.assertEqual(outcome.status.value, "SEPARATE_SAFETY")
        self.assertEqual(outcome.reason_codes, ("separate_safety_owner_required",))
        self.assertIsNone(outcome.artifact)


if __name__ == "__main__":
    unittest.main()
