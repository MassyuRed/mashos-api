# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
import hashlib
import unittest

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import (
    CMEE_TERMINAL_GENERATED_DISABLED,
    EpistemicState,
    RouteBDisposition,
)
from cocolon_meaning_experience_engine.emlis_v1a import (
    CMEEVerticalError,
    _artifact_id,
    _graph_id,
    _plan_id,
    _realize_cmee_experience,
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
    visible = _realize_cmee_experience(source, graph, plan, grounded_plan)
    return source, graph, plan, artifact, visible


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
        self.assertEqual(roles.count("RECEPTION"), 1)
        self.assertEqual(roles[-1], "RECEPTION")
        self.assertTrue(all(row.evidence_ids for row in artifact.trace))
        self.assertEqual(
            tuple(row.owner_id for row in graph.owner_dispositions),
            graph.required_owner_refs + graph.active_optional_owner_refs,
        )
        expected_digest = hashlib.sha256(
            "|".join(
                (graph.source_version, graph.obligation_version, *graph.required_owner_refs)
            ).encode("utf-8")
        ).hexdigest()
        self.assertEqual(graph.owner_universe_digest, expected_digest)
        self.assertEqual(outcome.terminal_state, CMEE_TERMINAL_GENERATED_DISABLED)
        self.assertNotIn("CANDIDATE_READY", outcome.terminal_state)
        self.assertFalse(outcome.automatic_progression)

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

    def test_trace_tamper_is_rejected(self) -> None:
        source, graph, _plan, artifact, visible = _private_parts(_request())
        first = artifact.trace[0]
        tampered_trace = (replace(first, evidence_ids=("foreign-evidence",)),) + artifact.trace[1:]
        tampered = replace(artifact, trace=tampered_trace)

        with self.assertRaisesRegex(CMEEVerticalError, "visible_trace_exact_binding_mismatch"):
            validate_positive_realization_trace(source, graph, tampered, visible)

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
                artifact.observation,
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
