# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from dataclasses import replace
import inspect
import re
import unittest
from unittest.mock import patch

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine
import cocolon_meaning_experience_engine.emlis_v1a as emlis_v1a_module
import cocolon_meaning_experience_engine.contracts as cmee_contracts_module
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
from tools.cmee_v1a_i1sx_candidate_run import (
    EXACT8,
    _structural_trace_valid,
    run as run_exact8_candidate,
)


REPRESENTATIVE_MEMO = "仕事が続いて疲れていて、朝から何も手につかない。"
MATERIAL_UNKNOWN_MEMO = "疲れた。"


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


def _build_with_composer_candidate_mutation(mutator, request=None):
    source = freeze_text_source(request or _request())
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

        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
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
        self.assertEqual(roles.count("UNKNOWN"), 0)
        self.assertEqual(roles.count("RECEPTION"), 1)
        self.assertEqual(roles[-1], "RECEPTION")
        self.assertEqual(artifact.visible_unknowns, ())
        self.assertEqual(artifact.plan.visible_unknown_owner_ids, ())
        self.assertTrue(all(row.evidence_ids for row in artifact.trace))
        self.assertEqual(
            tuple(row.owner_id for row in graph.owner_dispositions),
            graph.required_owner_refs + graph.active_optional_owner_refs,
        )
        unresolved_optional_owner_ids = {
            row.owner_id
            for row in graph.owner_dispositions
            if row.owner_class is OwnerClass.ACTIVE_OPTIONAL
            and row.route_b_disposition
            not in {
                RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
                RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
            }
        }
        self.assertTrue(unresolved_optional_owner_ids)
        self.assertTrue(
            unresolved_optional_owner_ids.issubset(
                set(artifact.plan.unresolved_owner_ids)
            )
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
            surface_lines[0] = forged_text
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
            surface_lines[0] = forged_text
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

    def test_r4_binding_snapshots_reject_alias_core_and_evidence_tamper(self) -> None:
        request = _request(
            record_id="cmee-r4-binding-snapshots",
            memo="この職場でやっていけるか不安。でも、続けられる形は探したい。",
        )

        def alias_lists(meta):
            rows = [meta["sentence_bindings"]]
            for bundle_key in (
                "sentence_binding_bundle",
                "binding_bundle",
                "binding",
            ):
                bundle = meta[bundle_key]
                rows.extend(
                    bundle[key] for key in ("bindings", "sentence_bindings", "items")
                )
            diagnostic = meta["composer_diagnostic"]
            diagnostic_bundle = diagnostic["sentence_binding_bundle"]
            rows.extend(
                diagnostic_bundle[key]
                for key in ("bindings", "sentence_bindings", "items")
            )
            rows.append(diagnostic["sentence_bindings"])
            return rows

        def forge_relation_meta(rows):
            for binding_rows in rows:
                binding_rows[0]["meta"]["cmee_nucleus_ids"][0] = "nucleus:forged"
                binding_rows[0]["meta"]["cmee_relation_bindings"][0][
                    "from_nucleus_id"
                ] = "nucleus:forged"
                binding_rows[0]["meta"]["cmee_binding_digest"] = "0" * 64

        def outer_alias_only(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            detached = copy.deepcopy(
                composer_meta["sentence_binding_bundle"]["bindings"]
            )
            forge_relation_meta([detached])
            composer_meta["sentence_binding_bundle"]["bindings"] = detached
            return replace(candidate, composer_meta=composer_meta)

        def all_guarded_aliases(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            guarded_meta = composer_meta["core_text_generation"]["result"]["meta"][
                "candidate"
            ]["meta"]
            forge_relation_meta(alias_lists(guarded_meta))
            return replace(candidate, composer_meta=composer_meta)

        def core_projection_field(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["core_text_generation"]["sentence_bindings"][0][
                "coverage_scope"
            ] = "forged_scope"
            return replace(candidate, composer_meta=composer_meta)

        def core_bool_as_int(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            composer_meta["core_text_generation"]["sentence_bindings"][0][
                "must_include"
            ] = 1
            return replace(candidate, composer_meta=composer_meta)

        def grounding_extra_evidence(candidate):
            composer_meta = copy.deepcopy(candidate.composer_meta)
            result_meta = composer_meta["core_text_generation"]["result"]["meta"]
            result_meta["guard_results"][3]["meta"]["sentence_claims"][0][
                "evidence_span_ids"
            ].append("s6")
            result_meta["combined_guard_result"]["meta"]["guard_results"][3][
                "meta"
            ]["sentence_claims"][0]["evidence_span_ids"].append("s6")
            return replace(candidate, composer_meta=composer_meta)

        for name, mutate in {
            "outer_alias_only": outer_alias_only,
            "all_guarded_aliases": all_guarded_aliases,
            "core_projection_field": core_projection_field,
            "core_bool_as_int": core_bool_as_int,
            "grounding_extra_evidence": grounding_extra_evidence,
        }.items():
            with self.subTest(name=name):
                with self.assertRaises(CMEEVerticalError):
                    _build_with_composer_candidate_mutation(mutate, request=request)

    def test_common_guard_proof_mutations_reject_after_coordinated_rehash(self) -> None:
        material_request = _request(
            record_id="cmee-common-guard-material-unknown",
            memo=MATERIAL_UNKNOWN_MEMO,
        )
        source, graph, _plan, artifact, visible = _private_parts(material_request)
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
            _private_parts(
                _request(
                    record_id="cmee-common-guard-proof-foreign",
                    memo=MATERIAL_UNKNOWN_MEMO,
                )
            )
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

    def test_complete_route_b_rows_keep_nonmaterial_unknown_internal(self) -> None:
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
        self.assertEqual(unknown_trace, ())
        self.assertEqual(artifact.visible_unknowns, ())
        self.assertEqual(artifact.plan.visible_unknown_owner_ids, ())
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
        attachment_owner = next(
            row.meaning_owner_id
            for row in universe.obligations
            if row.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT"
        )
        self.assertIn(attachment_owner, artifact.plan.unresolved_owner_ids)
        self.assertEqual(
            obligations[attachment_owner].owner_class,
            OwnerClass.ACTIVE_OPTIONAL,
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

    def test_material_unknown_is_layer1_visible_and_cannot_be_hidden(self) -> None:
        request = _request(
            record_id="cmee-material-unknown",
            memo=MATERIAL_UNKNOWN_MEMO,
        )
        outcome = MeaningExperienceEngine().generate(request)
        self.assertEqual(outcome.status.value, "LIMITED", outcome.reason_codes)
        self.assertEqual(outcome.terminal_state, CMEE_TERMINAL_GENERATED_DISABLED)
        self.assertFalse(outcome.automatic_progression)
        self.assertIsNotNone(outcome.artifact)
        assert outcome.artifact is not None
        self.assertEqual(len(outcome.artifact.visible_unknowns), 1)
        self.assertEqual(
            sum(row.role == "UNKNOWN" for row in outcome.artifact.trace),
            1,
        )
        layer1, separator, layer2 = outcome.artifact.text.partition(
            "\n\nEmlisから：\n"
        )
        self.assertTrue(separator)
        unknown_text = outcome.artifact.visible_unknowns[0].text
        self.assertEqual(layer1.count(unknown_text), 1)
        self.assertNotIn(unknown_text, layer2)

        source, graph, _plan, artifact, visible = _private_parts(request)
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
        with self.assertRaisesRegex(CMEEVerticalError, "visible_line_source_semantic"):
            validate_positive_realization_trace(
                source,
                graph,
                hidden_artifact,
                visible_without_unknown,
            )

    def test_unknown_text_and_evidence_subset_tampering_are_rejected(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(
            _request(
                record_id="cmee-material-unknown-tamper",
                memo=MATERIAL_UNKNOWN_MEMO,
            )
        )
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
        with self.assertRaisesRegex(CMEEVerticalError, "visible_line_source_semantic"):
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
        with self.assertRaisesRegex(CMEEVerticalError, "visible_line_source_semantic"):
            validate_positive_realization_trace(
                source,
                graph,
                reduced_artifact,
                tuple(reduced_visible),
            )

    def test_unknown_without_current_source_evidence_is_unavailable(self) -> None:
        request = _request(
            record_id="cmee-material-unknown-without-evidence",
            memo=MATERIAL_UNKNOWN_MEMO,
        )
        source = freeze_text_source(request)
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
            outcome = MeaningExperienceEngine().generate(request)

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
                    "visible_line_source_semantic_mismatch",
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

        self.assertEqual(first.status.value, second.status.value, "GENERATED")
        self.assertEqual(first.meaning_graph, second.meaning_graph)
        self.assertEqual(first.artifact, second.artifact)
        self.assertEqual(changed.status.value, "GENERATED", changed.reason_codes)
        assert first.source_envelope and first.artifact and changed.source_envelope and changed.artifact
        self.assertNotEqual(first.source_envelope.envelope_id, changed.source_envelope.envelope_id)
        self.assertNotEqual(first.artifact.artifact_id, changed.artifact.artifact_id)
        self.assertNotEqual(first.artifact.observation, changed.artifact.observation)

    def test_positive_experience_receives_a_semantically_bound_positive_act(self) -> None:
        request = _request(
            record_id="cmee-positive",
            memo="友達と話せて嬉しかった。",
            category="人間関係",
            emotion="喜び",
        )
        outcome = MeaningExperienceEngine().generate(request)
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)
        artifact = outcome.artifact
        assert artifact is not None
        self.assertEqual(
            artifact.plan.allowed_reception_act_ids,
            ("recognize_lived_change",),
        )
        self.assertNotIn("苦しさ", artifact.reception)
        self.assertNotIn("負担", artifact.reception)

        source, graph, _plan, private_artifact, visible = _private_parts(request)
        reception_index = next(
            index
            for index, row in enumerate(visible)
            if row.binding.line_role == "human_follow"
        )
        burden_visible = list(visible)
        burden_visible[reception_index] = replace(
            burden_visible[reception_index],
            text="その苦しさを、ここで受け止めています。",
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "visible_line_source_semantic_mismatch",
        ):
            validate_positive_realization_trace(
                source,
                graph,
                private_artifact,
                tuple(burden_visible),
            )

        changed_plan = replace(
            private_artifact.plan,
            allowed_reception_act_ids=("stay_with_current_burden",),
            reception_plan_digest="forged-burden-plan",
        )
        changed_artifact = _rehash_artifact(
            source,
            graph,
            replace(private_artifact, plan=changed_plan),
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "experience_plan_source_semantic_mismatch",
        ):
            validate_positive_realization_trace(
                source,
                graph,
                changed_artifact,
                visible,
            )

    def test_relation_required_input_seals_exact_endpoints_direction_and_evidence(self) -> None:
        request = _request(
            record_id="cmee-relation",
            memo="この職場でやっていけるか不安。でも、続けられる形は探したい。",
        )
        source, graph, _plan, artifact, visible = _private_parts(request)
        observation_lines = tuple(
            line for line in visible if line.binding.line_role == "cmee_observation"
        )
        observation_traces = tuple(row for row in artifact.trace if row.role == "OBSERVATION")
        self.assertEqual(len(observation_lines), 2)
        self.assertEqual(len(observation_traces), 2)
        self.assertIn("cocolon.cmee.emlis.r4_realization_obligations.v1", artifact.plan.source_plan_version)
        changed_plan_artifact = _rehash_artifact(
            source,
            graph,
            replace(
                artifact,
                plan=replace(
                    artifact.plan,
                    source_plan_version=(
                        "cocolon.cmee.emlis.r4_realization_obligations.v1:forged"
                    ),
                ),
            ),
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "experience_plan_source_semantic_mismatch",
        ):
            validate_positive_realization_trace(
                source,
                graph,
                changed_plan_artifact,
                visible,
            )
        edge_index = {row.edge_id: row for row in graph.edges}
        self.assertEqual(
            tuple(edge_index[row.meaning_edge_ids[0]].relation for row in observation_traces),
            ("contrast", "wish_and_constraint"),
        )
        self.assertTrue(all("この順" not in line.text for line in observation_lines))
        self.assertIn("不安", observation_lines[0].text)
        self.assertIn("気持ち", observation_lines[1].text)
        for legacy in ("起点側", "到達側", "第一項", "第二項", "項A", "項B"):
            self.assertFalse(
                any(legacy in line.text for line in observation_lines),
                f"legacy structural label: {legacy}",
            )
        for line, trace in zip(observation_lines, observation_traces, strict=True):
            self.assertEqual(len(line.binding.relation_ids), 1)
            self.assertEqual(len(trace.meaning_edge_ids), 1)
            edge = edge_index[trace.meaning_edge_ids[0]]
            self.assertEqual(
                trace.meaning_node_ids,
                (edge.source_node_id, edge.target_node_id),
            )
            self.assertEqual(trace.evidence_ids, edge.evidence_ids)

        first, second = observation_lines
        mutation_cases = {
            "reverse_endpoints": replace(
                first,
                binding=replace(
                    first.binding,
                    nucleus_ids=tuple(reversed(first.binding.nucleus_ids)),
                ),
            ),
            "drop_relation": replace(
                first,
                binding=replace(first.binding, relation_ids=()),
            ),
            "duplicate_relation": replace(
                second,
                binding=replace(
                    second.binding,
                    relation_ids=first.binding.relation_ids,
                ),
            ),
            "wrong_evidence_subset": replace(
                first,
                binding=replace(
                    first.binding,
                    evidence_span_ids=first.binding.evidence_span_ids[:-1],
                ),
            ),
            "wrong_surface_direction": replace(first, text=second.text),
            "non_directional_direction_injection": replace(
                first,
                text=(
                    "入力では、前の記述から後の記述へ、"
                    "異なる向きの対比がこの順に示されています。"
                ),
            ),
        }
        for name, changed_line in mutation_cases.items():
            with self.subTest(name=name):
                changed_visible = list(visible)
                changed_visible[observation_lines.index(first if name != "duplicate_relation" else second)] = changed_line
                with self.assertRaisesRegex(
                    CMEEVerticalError,
                    "visible_line_source_semantic_mismatch",
                ):
                    validate_positive_realization_trace(
                        source,
                        graph,
                        artifact,
                        tuple(changed_visible),
                    )

        reordered = (
            observation_lines[1],
            observation_lines[0],
            *visible[len(observation_lines) :],
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "visible_line_source_semantic_mismatch",
        ):
            validate_positive_realization_trace(source, graph, artifact, reordered)

        directional_request = _request(
            record_id="cmee-directional-relation",
            memo="昨日は疲れていた。今日は少し落ち着いた。",
            category="生活",
            emotion="平穏",
        )
        (
            directional_source,
            directional_graph,
            _directional_plan,
            directional_artifact,
            directional_visible,
        ) = _private_parts(directional_request)
        directional_line = next(
            line
            for line in directional_visible
            if line.binding.line_role == "cmee_observation"
        )
        self.assertEqual(len(directional_line.binding.relation_ids), 1)
        self.assertIn("あと", directional_line.text)
        self.assertIn("順序", directional_line.text)
        self.assertFalse("起点側" in directional_line.text)
        self.assertFalse("到達側" in directional_line.text)
        reversed_directional = tuple(
            replace(
                line,
                binding=replace(
                    line.binding,
                    nucleus_ids=tuple(reversed(line.binding.nucleus_ids)),
                ),
            )
            if line is directional_line
            else line
            for line in directional_visible
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "visible_line_source_semantic_mismatch",
        ):
            validate_positive_realization_trace(
                directional_source,
                directional_graph,
                directional_artifact,
                reversed_directional,
            )

        forged_direction_text = (
            "入力では、後の記述から前の記述へ、"
            "変化の方向がこの順に示されています。"
        )
        coordinated_directional = tuple(
            replace(
                line,
                text=forged_direction_text,
                binding=replace(
                    line.binding,
                    nucleus_ids=tuple(reversed(line.binding.nucleus_ids)),
                ),
            )
            if line is directional_line
            else line
            for line in directional_visible
        )
        directional_trace = list(directional_artifact.trace)
        directional_trace_index = next(
            index for index, row in enumerate(directional_trace) if row.role == "OBSERVATION"
        )
        directional_trace[directional_trace_index] = replace(
            directional_trace[directional_trace_index],
            meaning_node_ids=tuple(
                reversed(directional_trace[directional_trace_index].meaning_node_ids)
            ),
            text_sha256=_sha256_text(forged_direction_text),
        )
        directional_units = list(
            directional_artifact.common_guard_proof.guarded_observation_units
        )
        directional_units[0] = (
            directional_units[0][0],
            _sha256_text(forged_direction_text),
        )
        coordinated_artifact = _rehash_common_guard_proof_artifact(
            directional_source,
            directional_graph,
            replace(
                directional_artifact,
                observation=forged_direction_text,
                trace=tuple(directional_trace),
            ),
            replace(
                directional_artifact.common_guard_proof,
                guarded_observation_units=tuple(directional_units),
            ),
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "visible_line_source_semantic_mismatch",
        ):
            validate_positive_realization_trace(
                directional_source,
                directional_graph,
                coordinated_artifact,
                coordinated_directional,
            )

        short_endpoint_request = _request(
            record_id="cmee-short-endpoint-labels",
            memo="不安。でも、続けたい。",
        )
        _short_source, _short_graph, _short_plan, short_artifact, _short_visible = (
            _private_parts(short_endpoint_request)
        )
        self.assertIn("不安", short_artifact.observation)
        self.assertIn("続けたい", short_artifact.observation)
        self.assertFalse("負荷を伴う反応" in short_artifact.observation)
        self.assertFalse("保ちたい方向" in short_artifact.observation)

        collision_request = _request(
            record_id="cmee-endpoint-anchor-collision",
            memo="この仕事が不安になる。でも、この仕事が不安でも続けたい。",
        )
        (
            _collision_source,
            _collision_graph,
            _collision_plan,
            collision_artifact,
            _collision_visible,
        ) = _private_parts(collision_request)
        self.assertIn("この仕事", collision_artifact.observation)
        self.assertIn("不安", collision_artifact.observation)
        self.assertIn("続けたい", collision_artifact.observation)
        self.assertFalse("負荷を伴う反応" in collision_artifact.observation)
        self.assertFalse("保ちたい方向" in collision_artifact.observation)
        self.assertNotIn("この順", collision_artifact.observation)

        same_label_contrast = _private_parts(
            _request(
                record_id="cmee-same-label-contrast",
                memo="この仕事がつらい。でも、この仕事が苦しい。",
            )
        )[3]
        self.assertIn("つらさ", same_label_contrast.observation)
        self.assertIn("苦しさ", same_label_contrast.observation)
        self.assertNotIn("この順", same_label_contrast.observation)

        same_label_directional = _private_parts(
            _request(
                record_id="cmee-same-label-directional",
                memo="昨日は不安だった。今日は不安だ。",
            )
        )[3]
        self.assertIn("あと", same_label_directional.observation)
        self.assertIn("順序", same_label_directional.observation)
        self.assertFalse("起点側" in same_label_directional.observation)
        self.assertFalse("到達側" in same_label_directional.observation)

    def test_stage1_realizer_does_not_embed_exact8_fixture_identity_or_body(self) -> None:
        implementation = (
            inspect.getsource(emlis_v1a_module)
            + inspect.getsource(cmee_contracts_module)
        )
        self.assertFalse("EXACT8" in implementation, "fixture registry referenced")
        self.assertFalse(
            "cmee_v1a_i1sx_candidate_run" in implementation,
            "candidate runner referenced by production code",
        )
        for case_id, memo, _category, _emotion, _strength in EXACT8:
            with self.subTest(case_id=case_id):
                self.assertFalse(case_id in implementation, "fixture id embedded")
                self.assertFalse(memo in implementation, "fixture body embedded")

    def test_exact8_stage1_surface_is_two_layer_natural_and_trace_bound(self) -> None:
        legacy_fragments = (
            "起点側",
            "到達側",
            "第一項",
            "第二項",
            "項A",
            "項B",
            "願いと制約の組",
            "並存する二項",
            "という記述",
            "が示されています",
            "前に進む際の制約",
            "負荷を伴う反応",
            "負荷を伴う状態",
            "保ちたい方向",
            "前向きな変化",
            "まだ分からないこと：",
        )
        observations: list[str] = []
        receptions: list[str] = []
        for case_id, memo, category, emotion, strength in EXACT8:
            with self.subTest(case_id=case_id):
                outcome = MeaningExperienceEngine().generate(
                    _request(
                        record_id=f"stage1-{case_id.lower()}",
                        memo=memo,
                        category=category,
                        emotion=emotion,
                        strength=strength,
                    )
                )
                self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
                self.assertEqual(
                    outcome.terminal_state,
                    CMEE_TERMINAL_GENERATED_DISABLED,
                )
                self.assertFalse(outcome.automatic_progression)
                artifact = outcome.artifact
                self.assertIsNotNone(artifact)
                graph = outcome.meaning_graph
                self.assertIsNotNone(graph)
                assert artifact is not None and graph is not None
                text = artifact.text
                delimiter = "\n\nEmlisから：\n"
                self.assertTrue(text.startswith("見えたこと：\n"), "Layer 1 missing")
                self.assertEqual(text.count(delimiter), 1)
                layer1, separator, layer2 = text.partition(delimiter)
                self.assertTrue(bool(separator), "Layer 2 delimiter missing")
                for fragment in legacy_fragments:
                    self.assertFalse(
                        fragment in text,
                        f"legacy surface fragment: {fragment}",
                    )
                self.assertEqual(artifact.visible_unknowns, ())
                self.assertEqual(artifact.plan.visible_unknown_owner_ids, ())
                self.assertEqual(
                    tuple(row for row in artifact.trace if row.role == "UNKNOWN"),
                    (),
                )
                unresolved_optional_owner_ids = {
                    row.owner_id
                    for row in graph.owner_dispositions
                    if row.owner_class is OwnerClass.ACTIVE_OPTIONAL
                    and row.route_b_disposition
                    not in {
                        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
                        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
                    }
                }
                self.assertTrue(unresolved_optional_owner_ids)
                self.assertTrue(
                    unresolved_optional_owner_ids.issubset(
                        set(artifact.plan.unresolved_owner_ids)
                    )
                )
                self.assertTrue(layer1.removeprefix("見えたこと：\n").strip())
                self.assertTrue(layer2.strip())
                observation_norm = re.sub(r"\s+", "", artifact.observation)
                reception_norm = re.sub(r"\s+", "", artifact.reception)
                self.assertFalse(
                    observation_norm == reception_norm
                    or observation_norm in reception_norm
                    or reception_norm in observation_norm,
                    "Reception repeats Observation",
                )
                observation_nodes = {
                    node_id
                    for row in artifact.trace
                    if row.role == "OBSERVATION"
                    for node_id in row.meaning_node_ids
                }
                reception_trace = next(
                    row for row in artifact.trace if row.role == "RECEPTION"
                )
                self.assertTrue(bool(reception_trace.meaning_node_ids))
                self.assertTrue(
                    set(reception_trace.meaning_node_ids).issubset(observation_nodes),
                    "Reception is not bound to an observed meaning",
                )
                observations.append(artifact.observation)
                receptions.append(artifact.reception)

        self.assertEqual(len(set(observations)), len(EXACT8))
        self.assertEqual(len(set(receptions)), len(EXACT8))

    def test_unseen_same_metadata_inputs_change_stage1_meaning_surface(self) -> None:
        memos = (
            "体が重いけれど、少し部屋を整えたい。",
            "今日は疲れたけど、少し休んだら落ち着いた。",
        )
        artifacts = []
        for index, memo in enumerate(memos, start=1):
            outcome = MeaningExperienceEngine().generate(
                _request(
                    record_id=f"stage1-unseen-{index}",
                    memo=memo,
                    category="生活",
                    emotion="不安",
                    strength="medium",
                )
            )
            self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
            self.assertIsNotNone(outcome.artifact)
            assert outcome.artifact is not None
            self.assertTrue(
                outcome.artifact.text.startswith("見えたこと：\n"),
                "unseen Layer 1 missing",
            )
            self.assertEqual(outcome.artifact.text.count("\n\nEmlisから：\n"), 1)
            artifacts.append(outcome.artifact)

        first, second = artifacts
        self.assertFalse(first.observation == second.observation, "Observation ignored meaning")
        self.assertFalse(first.reception == second.reception, "Reception ignored meaning")
        self.assertFalse(first.artifact_id == second.artifact_id, "identity ignored meaning")

    def test_unseen_inputs_do_not_inherit_fixture_specific_events_or_states(self) -> None:
        holiday = MeaningExperienceEngine().generate(
            _request(
                record_id="stage1-unseen-holiday",
                memo="休日の予定を受けたあと、納得したい気持ちと引っかかりが残っている。",
            )
        )
        positive = MeaningExperienceEngine().generate(
            _request(
                record_id="stage1-unseen-positive",
                memo="仕事で元気だったけど、帰ってから少し散歩したら落ち着いた。",
            )
        )
        short_actual_change = MeaningExperienceEngine().generate(
            _request(
                record_id="stage1-unseen-short-actual-change",
                memo="疲れていたけれど、散歩したら落ち着いた。",
            )
        )
        simile = MeaningExperienceEngine().generate(
            _request(
                record_id="stage1-unseen-simile",
                memo="雨みたいな空で、外に出るか迷っている。",
            )
        )
        for outcome in (holiday, positive, short_actual_change):
            self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
            self.assertIsNotNone(outcome.artifact)
        self.assertIn(simile.status.value, {"GENERATED", "UNAVAILABLE"})
        assert holiday.artifact and positive.artifact
        self.assertIn("引っかかり", holiday.artifact.observation)
        self.assertNotIn("仕事の話", holiday.artifact.text)
        self.assertIn("元気", positive.artifact.observation)
        self.assertIn("落ち着いた", positive.artifact.observation)
        self.assertNotIn("疲れ", positive.artifact.text)
        if simile.artifact is not None:
            self.assertNotIn("雨みたいという願い", simile.artifact.text)

        counterexamples = (
            (
                "negated-help-wish",
                "相談したいわけではない。相手に迷惑をかけたくないだけだ。",
                (
                    "相談したいという気持ち",
                    "相談したいという願い",
                    "助けを求める動き",
                ),
            ),
            (
                "negated-walk-wish",
                "散歩したいわけではなく、頼まれたから歩いた。",
                ("散歩したいという気持ち", "散歩したいという願い"),
            ),
            (
                "negated-help-wish-demo",
                "相談したいわけでもない。相手に伝えただけだ。",
                (
                    "相談したいという気持ち",
                    "相談したいという願い",
                    "助けを求める大切な動き",
                ),
            ),
            (
                "negated-help-wish-explanatory",
                "相談したいというわけではない。事実を伝えただけだ。",
                (
                    "相談したいという気持ち",
                    "相談したいという願い",
                    "助けを求める大切な動き",
                ),
            ),
            (
                "negated-help-wish-nominal",
                "相談したいのでもない。記録のために書いた。",
                (
                    "相談したいという気持ち",
                    "相談したいという願い",
                    "助けを求める大切な動き",
                ),
            ),
            (
                "negated-help-wish-polite",
                "相談したいわけでもありません。相手に伝えただけです。",
                (
                    "相談したいという気持ち",
                    "相談したいという願い",
                    "助けを求める大切な動き",
                ),
            ),
            (
                "negated-walk-wish-thought",
                "散歩したいとは思わない。頼まれたから歩いた。",
                ("散歩したいという気持ち", "散歩したいという願い"),
            ),
            (
                "negated-burden-polite",
                "つらくありません。もう大丈夫です。",
                ("いま感じているつらさ", "今もつら", "つらさが残"),
            ),
            (
                "negated-burden-nominal",
                "つらいわけではない。もう大丈夫だ。",
                ("いま感じているつらさ", "今もつら", "つらさが残"),
            ),
            (
                "resolved-anxiety",
                "不安はなく、友達と話したらほっとした。",
                ("今も不安", "まだ不安", "不安が残", "不安を抱え"),
            ),
        )
        for case_id, memo, false_surfaces in counterexamples:
            with self.subTest(counterexample=case_id):
                outcome = MeaningExperienceEngine().generate(
                    _request(record_id=f"stage1-{case_id}", memo=memo)
                )
                self.assertIn(
                    outcome.status.value,
                    {"GENERATED", "LIMITED", "UNAVAILABLE"},
                    outcome.reason_codes,
                )
                self.assertFalse(outcome.automatic_progression)
                if outcome.artifact is None:
                    self.assertEqual(outcome.status.value, "UNAVAILABLE")
                    continue
                self.assertEqual(
                    outcome.terminal_state,
                    CMEE_TERMINAL_GENERATED_DISABLED,
                )
                for false_surface in false_surfaces:
                    self.assertNotIn(false_surface, outcome.artifact.text)

    def test_stage1_fails_closed_when_current_experiencer_or_time_is_ambiguous(self) -> None:
        unsupported = (
            "友達が不安だと言った。私は話を聞いた。",
            "同僚は不安そうだった。私は話を聞いた。",
            "母がつらそうなので、手伝った。",
            "夫は不安そうだった。私は話を聞いた。",
            "妻がつらそうなので、手伝った。",
            "娘が不安そうだったので、そばにいた。",
            "佐藤さんは疲れているようだった。私は見守った。",
            "母は散歩したいと言っている。私は付き添う。",
            "その人は不安そうだった。私は話を聞いた。",
            "知人がつらそうなので、手伝った。",
            "患者は疲れているようだった。私は見守った。",
            "太郎は不安そうだった。私は話を聞いた。",
            "彼らは疲れているようだった。私は見守った。",
            "その人は散歩したいと言っている。私は付き添う。",
            "太郎は帰りたいと言った。私は見送った。",
            "太郎は不安だった。私は話を聞いた。",
            "その人は疲れている。私は休むよう勧めた。",
            "太郎は帰りたい。私は見送った。",
            "彼らは帰りたい。私は見送った。",
            "太郎は不安だった。",
            "その人は疲れている。",
            "太郎は不安だったので、話を聞いた。",
            "太郎は帰りたい。",
            "彼らは帰りたい。",
            "Johnは不安だった。",
            "Aliceは帰りたい。",
            "友達によると、不安らしい。",
            "友達によれば、つらいらしい。",
            "友達の話では、帰りたいらしい。",
            "友達の話だと、つらいらしい。",
            "友達曰く、不安だ。",
            "不安らしい。",
            "疲れているそうだ。",
            "つらいようだ。",
            "散歩したいらしい。",
            "昨日は疲れた。",
            "昨夜は不安だった。",
            "以前はつらかった。",
            "昔は帰りたいと思っていた。",
            "大前は不安だった。",
            "今井は疲れている。",
            "Johnも不安だった。",
            "太郎も不安だった。",
            "大形は不安だった。",
            "友達いわく、不安だ。",
            "友達から聞いたところ、不安だ。",
            "友達から、疲れたと聞いた。",
            "友達に、疲れたと言われた。",
            "太郎の不安を聞いた。",
            "不安みたいだ。",
            "疲れているみたい。",
            "不安だそうです。",
            "つらいようです。",
            "疲れているそう。",
            "不安だった。",
            "疲れていた。",
            "つらかった。",
            "帰りたかった。",
            "昨年、不安だった。",
            "数日前、疲れていた。",
            "おととい、つらかった。",
            "その頃、不安だった。",
            "友達によりますと、不安だ。",
            "友達の話を聞くと、不安だ。",
            "不安だと聞いた。",
            "疲れていると聞いている。",
            "散歩したいと聞いた。",
            "つらいという話を聞いた。",
            "不安だと言っていた。",
            "不安との話だ。",
            "不安っぽい。",
            "不安であった。",
            "疲れておりました。",
            "疲れてた。",
            "疲れました。",
            "不安がありました。",
            "不安を感じていた。",
            "不安を感じていました。",
            "帰りたいと思った。",
            "帰りたいと考えた。",
            "「不安」は友達の言葉だ。",
            "不安なのは友達だ。",
            "疲れているのは母だ。",
            "不安だと耳にした。",
            "不安だと伝え聞いた。",
            "不安との報告だ。",
            "不安だということだ。",
            "不安だって。",
            "散歩したいって。",
            "不安っぽかった。",
            "不安げだ。",
            "不安なのかもしれない。",
            "不安なのは太郎。",
            "不安を感じているのは太郎。",
            "不安は太郎のものだ。",
            "「不安だ」は太郎が言ったことだ。",
            "「不安」は友達が書いた。",
            "「不安」と友達が書いた。",
            "友達を不安にさせた。",
            "母を疲れさせた。",
            "友達に不安を与えた。",
            "友達こそ不安だ。",
            "不安だとの報告を受けた。",
            "帰りたいとの連絡があった。",
            "不安感があった。",
            "疲れ切っていた。",
            "不安を抱いていた。",
            "不安が残っていた。",
            "不安を覚えた。",
            "不安でございました。",
            "不安を感じた。",
            "不安を抱えた。",
            "しんどく感じた。",
            "帰りたいと思いました。",
            "帰りたいと考えました。",
            "帰りたい気持ちだった。",
            "帰りたい気持ちがあった。",
            "帰りたい気持ちでした。",
            "不安なんかない。",
            "不安などない。",
            "不安は少しもない。",
            "不安は解消した。今は平気だ。",
            "もし不安なら休む。",
            "仮に不安だとしても大丈夫。",
            "不安な場合は休む。",
            "不安かどうか分からない。",
            "自分が不安なのか分からない。",
            "散歩したいかどうか分からない。",
            "本当に不安なのだろうか。",
            "散歩したいのかな。",
            "疲れている気がする。",
            "不安な気がする。",
            "みんな不安だ。",
            "不安な人が多い。",
            "不安な友達を支えた。",
            "疲れた母を手伝った。",
            "不安と、友達は書いた。",
            "不安とは無縁だ。",
            "不安を感じずに済んだ。",
            "不安が和らいだ。",
            "疲れは癒えた。",
            "疲れから回復した。",
            "散歩したい気持ちは消えた。",
            "不安になる可能性がある。",
            "不安になる予定だ。",
            "不安とは言えない。",
            "散歩したいとは言えない。",
            "散歩したいとは限らない。",
            "散歩したいかと言えば違う。",
            "友達のメモ：不安だ。",
            "不安だ（友達の話）。",
            "\"不安\"と友達が書いた。",
            "【不安】は友達の言葉だ。",
            "不安だと決めつけられた。",
            "不安だと思われている。",
            "不安という評価を受けた。",
            "不安と診断された。",
            "不安というより、落ち着いている。",
            "不安かと思ったが、違った。",
            "不安だと思っていたが、勘違いだった。",
            "不安の記憶がある。",
            "不安（出典：友達）。",
            "疲れているときは休む。",
            "不安であれば休む。",
            "不安のときだけ休む。",
            "不安か否か分からない。",
            "不安かは分からない。",
            "散歩したいか自分でも分からない。",
            "疲れている気もする。",
            "不安な気はする。",
            "不安は治った。",
            "不安はおさまった。",
            "不安は感じていない。",
            "不安どころか落ち着いている。",
            "不安とは反対に落ち着いている。",
            "散歩したい気持ちは皆無だ。",
            "散歩したい気持ちはゼロだ。",
            "散歩したい気持ちは消滅した。",
            "不安の記録を読み返した。",
            "不安の体験を振り返った。",
            "不安という単語を書いた。",
            "「疲れ」という表現を使った。",
            "散歩したいという文を読んだ。",
            "例：不安だ。",
            "テスト用に「不安」と入力した。",
            "不安は自然な反応だ。",
            "疲れは休息で和らぐ。",
            "不安について説明してください。",
            "不安を感じてください。",
            "疲れたと書いてください。",
            "散歩したいと言ってください。",
            "不安？",
            "疲れている？",
            "不安なふりをした。",
            "散歩したいと嘘をついた。",
            "不安だと仮定する。",
            "散歩したいと思うべきだ。",
            "不安になる必要はない。",
            "散歩したい人はいない。",
            "不安定な天気だ。",
            "不安になりたくない。",
            "私は疲れやすい。",
            "時々不安になる。",
            "不安を感じている人を支えた。",
            "苦しんでいる人を助けた。",
            "帰りたいという人を見送った。",
            "不安を研究している。",
            "不安への対処法を教えた。",
            "苦しさを表す演技をした。",
            "散歩したいという設定にした。",
            "だいたい終わった。",
            "疲れていたけれど、散歩したら落ち着いたふりをした。",
            "疲れていたけれど、散歩したら落ち着いたことにした。",
            "疲れていたけれど、散歩したら落ち着いた夢を見た。",
            "疲れていたけれど、散歩したら落ち着いた？",
            "疲れていたけれど、散歩したら落ち着いたか覚えていない。",
            "疲れていたけれど、散歩したら落ち着いたかどうか覚えていない。",
            "疲れていたけれど、散歩したら落ち着いたと勘違いした。",
            "疲れていたけれど、散歩したら落ち着いたと思い込んだ。",
            "疲れていたけれど、散歩したら落ち着いたという話を書いた。",
            "疲れていたけれど、散歩したら落ち着いた場面を演じた。",
            "疲れていたけれど、散歩したら落ち着いた例を考えた。",
            "疲れていたけれど、散歩したら落ち着いたらと願った。",
            "私は不安そうに見えると言われた。でも自分では平気だ。",
            "明日は疲れるかもしれないが、今は元気だ。",
            "来週はつらくなりそう。今は平気だ。",
            "来月は仕事を辞めたいと思う。今は続けている。",
            "昨日は疲れたが、今日は元気だ。",
            "昨夜は不安だったけど、今は大丈夫だ。",
            "さっきは疲れていたが、今は元気だ。",
            "前はつらかった。でも今は落ち着いている。",
            "今朝は不安だったけど、今は大丈夫だ。",
            "先日は疲れていたが、今は元気だ。",
            "去年は戻りたいと思っていたが、今は戻らない。",
            "「疲れた」と同僚が言った。私はうなずいた。",
            "昨日は続けたいと思っていたが、今日はやめると決めた。",
            "昨日は続けたいと思っていた。今日はやめると決めた。",
            "先週は続けたいと思っていた。今はやめると決めた。",
            "かつては戻りたいと思っていた。今は戻らない。",
            "昨日は相談したいと思った。今日は必要ないと思う。",
        )
        for index, memo in enumerate(unsupported, start=1):
            with self.subTest(index=index):
                outcome = MeaningExperienceEngine().generate(
                    _request(record_id=f"stage1-scope-{index}", memo=memo)
                )
                self.assertEqual(outcome.status.value, "UNAVAILABLE")
                self.assertIsNone(outcome.artifact)
                self.assertEqual(
                    outcome.reason_codes,
                    ("current_experiencer_or_time_scope_unsupported",),
                )
                self.assertFalse(outcome.automatic_progression)

    def test_stage1_does_not_invert_explicitly_negated_desire(self) -> None:
        counterexamples = (
            "散歩したいとは思ってない。頼まれたから歩いた。",
            "散歩したいと思っているわけではない。頼まれたから歩いた。",
            "散歩したい気はない。頼まれたから歩いた。",
            "散歩したいとは全然思わない。頼まれたから歩いた。",
            "散歩したいなんて思わない。頼まれたから歩いた。",
            "散歩したい気は全くない。頼まれたから歩いた。",
            "散歩したい気分ではない。頼まれたから歩いた。",
            "散歩したいわけでもなかった。頼まれたから歩いた。",
            "散歩したいとはあまり思わない。頼まれたから歩いた。",
            "散歩したいとはそこまで思わない。頼まれたから歩いた。",
            "散歩したいとは一切思わない。頼まれたから歩いた。",
            "散歩したい気がない。頼まれたから歩いた。",
            "散歩したい気持ちではない。頼まれたから歩いた。",
            "散歩したいとは感じない。頼まれたから歩いた。",
        )
        for index, memo in enumerate(counterexamples, start=1):
            with self.subTest(index=index):
                outcome = MeaningExperienceEngine().generate(
                    _request(record_id=f"stage1-negated-desire-{index}", memo=memo)
                )
                if outcome.artifact is None:
                    self.assertEqual(outcome.status.value, "UNAVAILABLE")
                else:
                    self.assertNotIn("散歩したいという願い", outcome.artifact.text)
                    self.assertNotIn("散歩したいという気持ち", outcome.artifact.text)
                self.assertFalse(outcome.automatic_progression)

    def test_first_person_desire_is_not_rewritten_as_an_object(self) -> None:
        bare = MeaningExperienceEngine().generate(
            _request(
                record_id="stage1-first-person-desire-bare",
                memo="私は散歩したい。",
            )
        )
        self.assertEqual(bare.status.value, "GENERATED", bare.reason_codes)
        self.assertIsNotNone(bare.artifact)
        assert bare.artifact is not None
        self.assertIn("散歩したいという願い", bare.artifact.reception)
        self.assertNotIn("私を散歩したい", bare.artifact.text)

        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id="stage1-first-person-desire",
                memo="私は散歩したいと言っている。",
                emotion="自己理解",
            )
        )
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        assert outcome.artifact is not None
        self.assertIn("散歩したいという願い", outcome.artifact.reception)
        self.assertNotIn("私を散歩したい", outcome.artifact.reception)

    def test_stage1_retained_intention_support_is_semantic_canonical_and_sealed(self) -> None:
        memo = EXACT8[5][1]
        request = _request(
            record_id="stage1-retained-intention-contract",
            memo=memo,
            category=EXACT8[5][2],
            emotion=EXACT8[5][3],
            strength=EXACT8[5][4],
        )
        source = freeze_text_source(request)
        resolver = build_evidence_span_resolver(
            source.evidence_spans,
            current_input=source.normalized_current_input,
        )
        grounded_plan = build_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        reception_plan = emlis_v1a_module._cmee_semantic_reception_plan(
            grounded_plan,
            resolver,
        )
        nucleus_index = {row.nucleus_id: row for row in grounded_plan.nuclei}
        issues = emlis_v1a_module.validate_grounded_human_reception_plan(
            reception_plan,
            expected_target_ids=grounded_plan.response_plan.human_follow_target_ids,
            nucleus_index=nucleus_index,
            resolver=resolver,
            safety_kind=grounded_plan.safety_policy.safety_kind,
            material_quality=emlis_v1a_module.CMEE_RECEPTION_MATERIAL_MODE,
        )
        self.assertEqual(issues, ())
        self.assertEqual(len(reception_plan.target_nucleus_ids), 1)
        self.assertEqual(len(reception_plan.support_nucleus_ids), 1)
        expected_nucleus_ids = (
            *reception_plan.target_nucleus_ids,
            *reception_plan.support_nucleus_ids,
        )
        expected_span_set = {
            span_id
            for nucleus_id in expected_nucleus_ids
            for span_id in nucleus_index[nucleus_id].source_span_ids
        }
        expected_span_ids = tuple(
            span_id for span_id in resolver.span_ids if span_id in expected_span_set
        )
        self.assertEqual(reception_plan.source_evidence_span_ids, expected_span_ids)
        for opportunity in reception_plan.opportunities:
            if opportunity.reception_act == "protect_retained_intention":
                self.assertEqual(
                    opportunity.support_nucleus_ids,
                    reception_plan.support_nucleus_ids,
                )
                self.assertEqual(opportunity.source_evidence_span_ids, expected_span_ids)
        for move in reception_plan.moves:
            self.assertEqual(move.support_nucleus_ids, reception_plan.support_nucleus_ids)
            self.assertEqual(move.source_evidence_span_ids, expected_span_ids)

        original_digest = emlis_v1a_module._reception_plan_digest(reception_plan)
        first_opportunity = reception_plan.opportunities[0]
        mutated_opportunity = replace(
            first_opportunity,
            support_nucleus_ids=(),
            source_evidence_span_ids=tuple(
                span_id
                for nucleus_id in first_opportunity.target_nucleus_ids
                for span_id in nucleus_index[nucleus_id].source_span_ids
            ),
        )
        opportunity_mutation = replace(
            reception_plan,
            opportunities=(mutated_opportunity, *reception_plan.opportunities[1:]),
        )
        boundary_mutation = replace(
            reception_plan,
            target_nucleus_ids=(
                *reception_plan.target_nucleus_ids,
                *reception_plan.support_nucleus_ids,
            ),
            support_nucleus_ids=(),
        )
        self.assertNotEqual(
            emlis_v1a_module._reception_plan_digest(opportunity_mutation),
            original_digest,
        )
        self.assertNotEqual(
            emlis_v1a_module._reception_plan_digest(boundary_mutation),
            original_digest,
        )

        outcome = MeaningExperienceEngine().generate(request)
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        assert outcome.artifact is not None
        reception_trace = next(
            row for row in outcome.artifact.trace if row.role == "RECEPTION"
        )
        self.assertEqual(len(reception_trace.meaning_node_ids), 2)
        self.assertEqual(len(reception_trace.evidence_ids), 2)

        for index, unrelated in enumerate(
            (
                "仕事が忙しい。ずっとこのままなのが不安で、どうしたらいいのか考えている。",
                "疲れて動けない。ずっとこのままなのが不安で、どうしたらいいのか考えている。",
            ),
            start=1,
        ):
            unrelated_outcome = MeaningExperienceEngine().generate(
                _request(
                    record_id=f"stage1-unrelated-support-{index}",
                    memo=unrelated,
                )
            )
            self.assertEqual(unrelated_outcome.status.value, "UNAVAILABLE")
            self.assertEqual(
                unrelated_outcome.reason_codes,
                ("bound_human_reception_retained_intention_evidence_missing",),
            )
            self.assertIsNone(unrelated_outcome.artifact)

    def test_actual_stage1_reception_surface_must_pass_dedicated_validator(self) -> None:
        invalid_surfaces = (
            "今すぐ相談してください。",
            "この願いを大切にします。もう一文追加します。",
        )
        for invalid_surface in invalid_surfaces:
            with self.subTest(invalid_surface=invalid_surface):
                with patch.object(
                    emlis_v1a_module,
                    "_cmee_stage1_reception_text",
                    return_value=invalid_surface,
                ):
                    outcome = MeaningExperienceEngine().generate(_request())
                self.assertEqual(outcome.status.value, "UNAVAILABLE")
                self.assertIn(
                    "bound_human_reception_surface_rejected",
                    outcome.reason_codes,
                )

    def test_role_aware_exact8_comparator_and_mutations(self) -> None:
        request = _request(
            record_id="cmee-role-aware-material-unknown",
            memo=MATERIAL_UNKNOWN_MEMO,
        )
        outcome = MeaningExperienceEngine().generate(request)
        self.assertEqual(outcome.status.value, "LIMITED", outcome.reason_codes)
        self.assertTrue(_structural_trace_valid(outcome))
        artifact = outcome.artifact
        assert artifact is not None
        unknown_index = next(
            index for index, row in enumerate(artifact.trace) if row.role == "UNKNOWN"
        )
        reception_index = next(
            index for index, row in enumerate(artifact.trace) if row.role == "RECEPTION"
        )
        observation_index = next(
            index for index, row in enumerate(artifact.trace) if row.role == "OBSERVATION"
        )
        source_node_id = artifact.trace[observation_index].meaning_node_ids[0]
        graph = outcome.meaning_graph
        assert graph is not None
        nonvisible_node = next(
            row
            for row in graph.nodes
            if graph.owner_dispositions[
                tuple(item.owner_id for item in graph.owner_dispositions).index(row.owner_id)
            ].disposition
            is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
        )
        mutations = {
            "unknown_fake_node": replace(
                artifact.trace[unknown_index],
                meaning_node_ids=(source_node_id,),
            ),
            "unknown_fake_edge": replace(
                artifact.trace[unknown_index],
                meaning_edge_ids=("forged-edge",),
            ),
            "unknown_without_evidence": replace(
                artifact.trace[unknown_index],
                evidence_ids=(),
            ),
            "unknown_without_owner": replace(
                artifact.trace[unknown_index],
                constrained_by_owner_ids=(),
            ),
            "unknown_wrong_duty": replace(
                artifact.trace[unknown_index],
                duty_id="FORGED_UNKNOWN_DUTY",
            ),
            "unknown_wrong_operation": replace(
                artifact.trace[unknown_index],
                operation="FORGED_UNKNOWN_OPERATION",
            ),
            "observation_without_meaning": replace(
                artifact.trace[observation_index],
                meaning_node_ids=(),
                meaning_edge_ids=(),
            ),
            "observation_nonvisible_meaning": replace(
                artifact.trace[observation_index],
                meaning_node_ids=(nonvisible_node.node_id,),
                meaning_edge_ids=(),
            ),
            "reception_without_meaning": replace(
                artifact.trace[reception_index],
                meaning_node_ids=(),
            ),
        }
        for name, changed_trace in mutations.items():
            with self.subTest(name=name):
                trace = list(artifact.trace)
                index = (
                    unknown_index
                    if name.startswith("unknown_")
                    else (
                        observation_index
                        if name.startswith("observation_")
                        else reception_index
                    )
                )
                trace[index] = changed_trace
                self.assertFalse(
                    _structural_trace_valid(
                        replace(outcome, artifact=replace(artifact, trace=tuple(trace)))
                    )
                )

        sequence_mutations = {
            "missing_unknown": tuple(
                row for row in artifact.trace if row.role != "UNKNOWN"
            ),
            "duplicate_unknown": (
                *artifact.trace[:reception_index],
                artifact.trace[unknown_index],
                *artifact.trace[reception_index:],
            ),
            "unknown_after_reception": (
                *artifact.trace[:unknown_index],
                artifact.trace[reception_index],
                artifact.trace[unknown_index],
            ),
        }
        for name, trace in sequence_mutations.items():
            with self.subTest(name=name):
                self.assertFalse(
                    _structural_trace_valid(
                        replace(outcome, artifact=replace(artifact, trace=trace))
                    )
                )

        body_free, _full = run_exact8_candidate()
        self.assertEqual(len(EXACT8), 8)
        self.assertEqual(body_free["case_count"], 8)
        self.assertEqual(body_free["limited_count"], 0)
        self.assertEqual(body_free["artifact_count"], 8)
        self.assertEqual(body_free["structural_trace_valid_count"], 8)
        self.assertEqual(
            {row["status"] for row in body_free["cases"]},
            {"GENERATED"},
        )
        self.assertEqual(
            body_free["candidate_state"],
            "GENERATED_FOR_PRODUCT_READ_DISABLED",
        )
        self.assertFalse(body_free["product_read_eligible"])
        self.assertFalse(body_free["product_read_evaluated"])
        self.assertFalse(body_free["automatic_progression"])

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
        safety_inputs = (
            "自分には何もできない。それでも、明日の予約は取り消していない。",
            "「死にたい」と友達が言った。",
        )
        for index, memo in enumerate(safety_inputs, start=1):
            outcome = MeaningExperienceEngine().generate(
                _request(
                    record_id=f"cmee-safety-{index}",
                    memo=memo,
                    category="健康",
                )
            )
            self.assertEqual(outcome.status.value, "SEPARATE_SAFETY")
            self.assertEqual(outcome.reason_codes, ("separate_safety_owner_required",))
            self.assertIsNone(outcome.artifact)


if __name__ == "__main__":
    unittest.main()
