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
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response_module
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
    _sha256_text,
    build_text_grounded_limited_artifact,
    validate_positive_realization_trace as _runtime_validate_positive_realization_trace,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source
from tools.cmee_v1a_i1sx_candidate_run import (
    EXACT8,
    STAGE1_KAREN_DERIVED_MUTATION_SET_V1,
    _body_free_mutation_registry,
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
    captured: dict[str, object] = {}

    def capture_validation(
        validation_source,
        validation_graph,
        validation_artifact,
        safe_lines,
        **kwargs,
    ):
        captured["safe_lines"] = tuple(safe_lines)
        captured["projection"] = kwargs["projection"]
        captured["selected_units"] = kwargs["selected_units"]
        return _runtime_validate_positive_realization_trace(
            validation_source,
            validation_graph,
            validation_artifact,
            safe_lines,
            **kwargs,
        )

    with patch.object(
        emlis_v1a_module,
        "validate_positive_realization_trace",
        side_effect=capture_validation,
    ):
        graph, plan, artifact = build_text_grounded_limited_artifact(source)
    visible = captured["safe_lines"]
    _STAGE1_VALIDATION_CAPTURE[source.envelope.envelope_id] = (
        captured["projection"],
        captured["selected_units"],
    )
    return source, graph, plan, artifact, visible


_STAGE1_VALIDATION_CAPTURE: dict[str, tuple[object, object]] = {}


def validate_positive_realization_trace(source, graph, artifact, safe_lines):
    projection, selected_units = _STAGE1_VALIDATION_CAPTURE[
        source.envelope.envelope_id
    ]
    return _runtime_validate_positive_realization_trace(
        source,
        graph,
        artifact,
        safe_lines,
        projection=projection,
        selected_units=selected_units,
    )


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


_STEP6_MUTATION_CLASS_COUNTS = {
    "SEMANTIC_EQUIVALENCE_MUTATION": 3,
    "RELATION_CONTRAST_MUTATION": 3,
    "CLAIM_BOUNDARY_MUTATION": 4,
    "SUBJECTIVITY_MUTATION": 2,
}

_STEP6_WHOLE_STATE_NEGATION_VARIANTS = (
    ("noun", "plain", "none", "不安ではない。"),
    ("noun", "past", "none", "不安ではなかった。"),
    ("noun", "polite", "none", "不安ではありません。"),
    ("noun", "polite-past", "none", "不安ではありませんでした。"),
    ("noun", "plain", "も", "疲れもない。"),
    ("noun", "past", "も", "疲れもなかった。"),
    ("noun", "polite", "も", "疲れもありません。"),
    ("noun", "polite-past", "も", "疲れもありませんでした。"),
    ("adjective", "plain", "は", "つらくはない。"),
    ("adjective", "past", "は", "つらくはなかった。"),
    ("adjective", "polite", "は", "つらくはありません。"),
    ("adjective", "polite-past", "は", "つらくはありませんでした。"),
    ("verb", "plain", "none", "疲れていない。"),
    ("verb", "past", "none", "疲れていなかった。"),
    ("verb", "polite", "none", "疲れていません。"),
    ("verb", "polite-past", "none", "疲れていませんでした。"),
)


def _step6_mutation_requests(operator: str):
    """Return the exact bounded request pair for one public mutation opcode.

    Source bodies live only in this test-owned generator.  The public runner
    registry remains an ASCII identity/class/opcode table and never invokes
    this function.
    """

    request_pairs = {
        "REGISTER_INFLECTION": (
            {"memo": "今日は疲れている。"},
            {"memo": "今日は疲れています。"},
        ),
        "LEXICAL_PARAPHRASE": (
            {"memo": "体がだるい。"},
            {"memo": "体が重く感じる。"},
        ),
        "CLAUSE_ORDER": (
            {"memo": "体がだるい。少しつらい。"},
            {"memo": "少しつらい。体がだるい。"},
        ),
        "TEMPORAL_ORDER": (
            {
                "memo": "前は動いた。今は不安が残っている。",
                "category": "生活",
            },
            {
                "memo": "今は不安が残っている。前は動いた。",
                "category": "生活",
            },
        ),
        "COEXISTENCE_TENSION": (
            {
                "memo": "疲れている。同時に。歩きたい。",
                "category": "生活",
            },
            {
                "memo": "疲れている。でも。歩きたい。",
                "category": "生活",
            },
        ),
        "SEQUENCE_CAUSE": (
            {
                "memo": "記録を書いた。そのあと、不安が残っている。",
                "category": "生活",
            },
            {
                "memo": "記録を書いた。そのため、不安が残っている。",
                "category": "生活",
            },
        ),
        "NEGATION": (
            {"memo": "散歩したい。頼まれて歩いた。"},
            {"memo": "散歩したいわけではなく、頼まれたから歩いた。"},
        ),
        "MODALITY": (
            {"memo": "疲れている。"},
            {"memo": "疲れているかもしれない。"},
        ),
        "EXPERIENCER": (
            {"memo": "私は疲れている。"},
            {"memo": "友達は疲れている。"},
        ),
        "MATERIAL_UNRELATED": (
            {"memo": "体がだるい。", "category": "生活"},
            {"memo": "体がだるい。記録を書いた。", "category": "生活"},
        ),
        "SOURCE_STRENGTH": (
            {
                "memo": "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
                "category": "生活",
                "emotion": "平穏",
                "strength": "weak",
            },
            {
                "memo": "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
                "category": "生活",
                "emotion": "平穏",
                "strength": "strong",
            },
        ),
        "DISCOMFORT_PERSON_TARGET": (
            {"memo": "今日は疲れている。"},
            None,
        ),
    }
    before, after = request_pairs[operator]
    stem = operator.lower().replace("_", "-")
    return (
        _request(record_id=f"step6-{stem}-before", **before),
        (
            _request(record_id=f"step6-{stem}-after", **after)
            if after is not None
            else None
        ),
    )


def _step6_private_bodies() -> tuple[str, ...]:
    bodies: list[str] = []
    for _case_id, _mutation_class, operator in STAGE1_KAREN_DERIVED_MUTATION_SET_V1:
        before, after = _step6_mutation_requests(operator)
        for request in (before, after):
            if request is None:
                continue
            memo = str(
                request.current_input_bundle.raw_current_input.get("memo") or ""
            )
            if memo not in bodies:
                bodies.append(memo)
    return tuple(bodies)


def _run_step6_mutation_request(request: GenerationRequest) -> dict[str, object]:
    captured: dict[str, object] = {}
    original_compiler = emlis_v1a_module.compile_stage1_response
    original_common = emlis_v1a_module.compose_emlis_conversation_candidate
    legacy_names = (
        "_canonical_r4_observation_lines",
        "_canonical_r4_tail_lines",
        "_cmee_stage1_reception_text",
        "realize_grounded_human_reception",
    )

    def capture_compile(*args, **kwargs):
        captured.update(kwargs)
        projection, selected_units = original_compiler(*args, **kwargs)
        captured["projection"] = projection
        captured["selected_units"] = selected_units
        return projection, selected_units

    legacy_patchers = [
        patch.object(
            emlis_v1a_module,
            name,
            wraps=getattr(emlis_v1a_module, name),
        )
        for name in legacy_names
    ]
    with (
        patch.object(
            emlis_v1a_module,
            "compile_stage1_response",
            side_effect=capture_compile,
        ) as compiler,
        patch.object(
            emlis_v1a_module,
            "compose_emlis_conversation_candidate",
            wraps=original_common,
        ) as common_guard_path,
        legacy_patchers[0] as legacy_observation,
        legacy_patchers[1] as legacy_tail,
        legacy_patchers[2] as legacy_reception,
        legacy_patchers[3] as legacy_reception_realizer,
    ):
        outcome = MeaningExperienceEngine().generate(request)
    return {
        "request": request,
        "outcome": outcome,
        "captured": captured,
        "compiler_calls": compiler.call_count,
        "composer_calls": common_guard_path.call_count,
        "legacy_calls": (
            legacy_observation.call_count,
            legacy_tail.call_count,
            legacy_reception.call_count,
            legacy_reception_realizer.call_count,
        ),
    }


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)


def _step6_evidence_paths(captured: dict[str, object], evidence_ids) -> tuple:
    source = captured["source"]
    evidence_by_id = {row.evidence_id: row for row in source.evidence_refs}
    normalized_ids = tuple(
        (
            evidence_id.split(":", 1)[1].split("@", 1)[0]
            if evidence_id.startswith("evidence:")
            else evidence_id
        )
        for evidence_id in evidence_ids
    )
    return tuple(
        (
            evidence_by_id[evidence_id].field_path,
            evidence_by_id[evidence_id].element_index,
        )
        for evidence_id in normalized_ids
    )


def _step6_owner_shape(captured: dict[str, object], owner_id: str) -> tuple:
    graph = captured["grounded_graph"]
    row = next(
        disposition
        for disposition in graph.owner_dispositions
        if disposition.owner_id == owner_id
    )
    return (
        row.owner_class.value,
        row.provider_resolution.value,
        row.attachment_admission.value,
        row.visible_authority.value,
        row.disposition.value,
        _step6_evidence_paths(captured, row.evidence_ids),
        len(row.visible_claim_refs),
        row.target_unknown_ref is not None,
        row.reason_codes,
    )


def _step6_node_shape(captured: dict[str, object], node) -> tuple:
    return (
        node.node_kind,
        node.grounding_kind,
        node.epistemic_state.value,
        _step6_owner_shape(captured, node.owner_id),
        _step6_evidence_paths(captured, node.evidence_ids),
    )


def _step6_edge_shape(
    captured: dict[str, object],
    edge,
    relation_aliases: dict[str, str] | None = None,
) -> tuple:
    graph = captured["grounded_graph"]
    node_by_id = {row.node_id: row for row in graph.nodes}
    relation = (relation_aliases or {}).get(edge.relation, edge.relation)
    return (
        relation,
        _step6_node_shape(captured, node_by_id[edge.source_node_id]),
        _step6_node_shape(captured, node_by_id[edge.target_node_id]),
        edge.grounding_kind,
        edge.epistemic_state.value,
        _step6_owner_shape(captured, edge.owner_id),
        _step6_evidence_paths(captured, edge.evidence_ids),
    )


def _step6_ref_shape(
    captured: dict[str, object],
    semantic_ref: str,
    relation_aliases: dict[str, str] | None = None,
) -> tuple:
    graph = captured["grounded_graph"]
    ref_kind, payload = semantic_ref.split(":", 1)
    local_id = payload.split("@", 1)[0]
    if ref_kind == "node":
        node = next(row for row in graph.nodes if row.node_id == local_id)
        return ("node", _step6_node_shape(captured, node))
    if ref_kind == "edge":
        edge = next(row for row in graph.edges if row.edge_id == local_id)
        return (
            "edge",
            _step6_edge_shape(captured, edge, relation_aliases),
        )
    return (ref_kind, "EXTERNAL_REF")


def _step6_candidate_shape(
    captured: dict[str, object],
    candidate,
    relation_aliases: dict[str, str] | None = None,
) -> tuple:
    aliases = relation_aliases or {}
    relation_operator = aliases.get(
        candidate.relation_operator.value,
        candidate.relation_operator.value,
    )
    candidate_kind = aliases.get(
        candidate.candidate_kind.value,
        candidate.candidate_kind.value,
    )
    graph = captured["grounded_graph"]
    edge_by_id = {row.edge_id: row for row in graph.edges}
    relation_basis = tuple(
        _step6_edge_shape(
            captured,
            edge_by_id[ref.split(":", 1)[1].split("@", 1)[0]],
            aliases,
        )
        for ref in candidate.relation_basis_refs
    )
    return (
        candidate_kind,
        candidate.claim_domain,
        candidate.semantic_operator.value,
        tuple(
            (
                binding.role.value,
                _step6_ref_shape(captured, binding.semantic_ref, aliases),
            )
            for binding in candidate.argument_bindings
        ),
        relation_operator,
        relation_basis,
        aliases.get(candidate.derivation_rule_id, candidate.derivation_rule_id),
        tuple(
            _step6_ref_shape(captured, ref, aliases)
            for ref in candidate.semantic_refs
        ),
        _step6_evidence_paths(captured, candidate.evidence_refs),
        len(candidate.basis_candidate_refs),
        candidate.epistemic_state.value,
        candidate.required_qualifiers,
        candidate.forbidden_promotions,
    )


def _step6_contribution_shape(
    captured: dict[str, object],
    contribution,
    relation_aliases: dict[str, str] | None = None,
) -> tuple:
    aliases = relation_aliases or {}
    projection = captured["projection"]
    candidate_by_id = {
        row.candidate_id: row for row in projection.interpretation_candidates
    }
    graph = captured["grounded_graph"]
    edge_by_id = {row.edge_id: row for row in graph.edges}
    return (
        aliases.get(
            contribution.contribution_kind.value,
            contribution.contribution_kind.value,
        ),
        tuple(
            _step6_candidate_shape(captured, candidate_by_id[ref], aliases)
            for ref in contribution.interpretation_candidate_refs
        ),
        contribution.semantic_operator.value,
        tuple(
            (
                binding.role.value,
                _step6_ref_shape(captured, binding.semantic_ref, aliases),
            )
            for binding in contribution.argument_bindings
        ),
        aliases.get(
            contribution.relation_operator.value,
            contribution.relation_operator.value,
        ),
        tuple(
            _step6_edge_shape(
                captured,
                edge_by_id[ref.split(":", 1)[1].split("@", 1)[0]],
                aliases,
            )
            for ref in contribution.relation_basis_refs
        ),
        aliases.get(
            contribution.derivation_rule_id,
            contribution.derivation_rule_id,
        ),
        tuple(
            _step6_ref_shape(captured, ref, aliases)
            for ref in contribution.semantic_refs
        ),
        _step6_evidence_paths(captured, contribution.evidence_refs),
        contribution.retention,
        len(contribution.prerequisite_contribution_refs),
        contribution.forbidden_operations,
    )


def _step6_claim_shape(
    captured: dict[str, object],
    claim,
    *,
    include_targets: bool,
) -> tuple:
    projection = captured["projection"]
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    proposition = claim.asserted_subjective_proposition

    def contribution_shapes(refs) -> tuple:
        return tuple(
            _step6_contribution_shape(captured, contribution_by_id[ref])
            for ref in refs
        )

    response_shapes = ()
    if include_targets:
        response_shapes = tuple(
            (
                _step6_contribution_shape(captured, contribution_by_id[ref])
                if ref in contribution_by_id
                else _step6_ref_shape(captured, ref)
            )
            for ref in proposition.response_object_refs
        )
    return (
        claim.claim_domain,
        claim.subjective_mode.value,
        proposition.subjective_operator.value,
        contribution_shapes(proposition.target_contribution_refs)
        if include_targets
        else len(proposition.target_contribution_refs),
        response_shapes
        if include_targets
        else len(proposition.response_object_refs),
        _enum_value(proposition.affect_category),
        _enum_value(proposition.affect_intensity),
        _enum_value(proposition.stance_operator),
        proposition.counterposition_target_ref is not None,
        len(proposition.referenced_actor_refs),
        len(proposition.referenced_experiencer_refs),
        proposition.addressee_role,
        proposition.polarity,
        proposition.modality,
        contribution_shapes(claim.basis_observation_contribution_refs)
        if include_targets
        else len(claim.basis_observation_contribution_refs),
        len(claim.basis_semantic_refs),
        claim.source_reception_act_refs,
        claim.value_principle_refs,
        claim.user_fact_effect,
        claim.forbidden_promotions,
    )


def _step6_projection_shape(
    captured: dict[str, object],
    *,
    include_claim_targets: bool = True,
) -> tuple:
    graph = captured["grounded_graph"]
    projection = captured["projection"]
    return (
        tuple(
            sorted(
                _step6_owner_shape(captured, row.owner_id)
                for row in graph.owner_dispositions
            )
        ),
        tuple(sorted(_step6_node_shape(captured, row) for row in graph.nodes)),
        tuple(sorted(_step6_edge_shape(captured, row) for row in graph.edges)),
        tuple(
            sorted(
                _step6_candidate_shape(captured, row)
                for row in projection.interpretation_candidates
            )
        ),
        tuple(
            sorted(
                _step6_contribution_shape(captured, row)
                for row in projection.observation_contributions
            )
        ),
        tuple(
            sorted(
                _step6_claim_shape(
                    captured,
                    row,
                    include_targets=include_claim_targets,
                )
                for row in projection.subjective_claims
            )
        ),
        tuple(
            sorted(
                (
                    entry.slot.value,
                    len(entry.interpretation_candidate_refs),
                    len(entry.semantic_refs),
                    len(entry.evidence_refs),
                )
                for entry in projection.meaning_field.entries
            )
        ),
        len(projection.meaning_field.required_candidate_refs),
        len(projection.meaning_field.material_unknown_refs),
        projection.observation_depth_class.value,
        projection.subjective_depth_class.value,
        projection.temperature_class.value,
        projection.reception_style_policy_ref,
        len(projection.ordered_observation_refs),
        len(projection.ordered_subjective_refs),
    )


def _step6_trace_spine(run: dict[str, object]) -> tuple:
    captured = run["captured"]
    outcome = run["outcome"]
    graph = captured["grounded_graph"]
    node_by_id = {row.node_id: row for row in graph.nodes}
    edge_by_id = {row.edge_id: row for row in graph.edges}
    artifact = outcome.artifact
    assert artifact is not None
    rows = []
    for trace in artifact.trace:
        extension = trace.emlis_stage1_extension
        rows.append(
            (
                trace.role,
                trace.duty_id,
                trace.operation,
                tuple(node_by_id[ref].node_kind for ref in trace.meaning_node_ids),
                tuple(edge_by_id[ref].relation for ref in trace.meaning_edge_ids),
                _step6_evidence_paths(captured, trace.evidence_ids),
                len(trace.constrained_by_owner_ids),
                (
                    None
                    if extension is None
                    else (
                        extension.claim_domain.value,
                        len(extension.contribution_refs),
                        len(extension.basis_trace_refs),
                        len(extension.interpretation_candidate_refs),
                        extension.subjective_claim_ref is not None,
                        len(extension.basis_observation_contribution_refs),
                        extension.value_principle_refs,
                        extension.speaker_owner,
                        extension.user_fact_effect,
                        extension.composition_variant_id,
                    )
                ),
            )
        )
    return tuple(rows)


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
        self.assertGreaterEqual(roles.count("RECEPTION"), 1)
        self.assertLessEqual(roles.count("RECEPTION"), 4)
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
        self.assertTrue(
            set(outcome.artifact.plan.required_observation_owner_ids).issubset(
                realized_owner_ids
            )
        )
        self.assertTrue(
            realized_owner_ids.issubset(
                set(graph.required_owner_refs + graph.active_optional_owner_refs)
            )
        )
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

        with self.assertRaisesRegex(
            CMEEVerticalError,
            "stage1_positive_trace_extension_invalid",
        ):
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
        memo = "この職場でやっていけるか不安。でも、続けられる形は探したい。"
        request = _request(
            record_id="cmee-relation",
            memo=memo,
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
        projection, selected_units = _STAGE1_VALIDATION_CAPTURE[
            source.envelope.envelope_id
        ]
        relation_contributions = tuple(
            row
            for row in projection.observation_contributions
            if row.relation_operator.value in {"TENSION_WITH", "COEXISTS_WITH"}
        )
        self.assertEqual(
            tuple(row.relation_operator.value for row in relation_contributions),
            ("TENSION_WITH", "COEXISTS_WITH"),
        )
        unit_by_move = {
            row.move_ref: row for row in selected_units if row.layer == "LAYER_1"
        }
        first_relation_unit, second_relation_unit = tuple(
            unit_by_move[
                stage1_response_module._move_ref(row.contribution_id)
            ]
            for row in relation_contributions
        )
        first_endpoints = {
            row.semantic_ref
            for row in relation_contributions[0].argument_bindings
        }
        second_endpoints = {
            row.semantic_ref
            for row in relation_contributions[1].argument_bindings
        }
        self.assertEqual(first_endpoints, second_endpoints)
        node_by_ref = {
            (
                f"node:{row.node_id}@"
                f"{cmee_contracts_module.CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
            ): row
            for row in graph.nodes
        }
        self.assertEqual(first_endpoints, set(node_by_ref) & first_endpoints)
        direction_ref = next(
            ref for ref in first_endpoints if node_by_ref[ref].node_kind == "wish"
        )
        burden_ref = next(ref for ref in first_endpoints if ref != direction_ref)

        # The first shared TENSION owns every bounded source anchor exactly
        # once and reaches both relation endpoints without anaphora.
        first_source_anchors = tuple(
            row
            for row in first_relation_unit.realized_semantic_bindings
            if row.semantic_ref in first_endpoints
            and row.clause_slot.endswith((":anchor", ":affect"))
        )
        self.assertEqual(
            {row.semantic_ref for row in first_source_anchors},
            first_endpoints,
        )
        self.assertFalse(
            any(
                row.clause_slot.endswith(":argument_anaphora")
                for row in first_relation_unit.realized_semantic_bindings
            )
        )
        for binding in first_source_anchors:
            span = first_relation_unit.text[
                binding.surface_scalar_start : binding.surface_scalar_end
            ]
            self.assertIn(span, node_by_ref[binding.semantic_ref].value)
            self.assertIn(span, memo)
            self.assertEqual(first_relation_unit.text.count(span), 1)

        first_quote_openings = tuple(
            row
            for row in first_relation_unit.realized_semantic_bindings
            if row.clause_slot.endswith(":quote_open")
        )
        first_quote_closings = tuple(
            row
            for row in first_relation_unit.realized_semantic_bindings
            if row.clause_slot.endswith(":quote_close")
        )
        self.assertEqual(len(first_quote_openings), 2)
        self.assertEqual(len(first_quote_closings), 2)
        self.assertEqual(first_relation_unit.text.count("「"), 2)
        self.assertEqual(first_relation_unit.text.count("」"), 2)
        quoted_span_by_ref: dict[str, str] = {}
        for opening, closing in zip(
            first_quote_openings,
            first_quote_closings,
            strict=True,
        ):
            self.assertEqual(opening.semantic_ref, closing.semantic_ref)
            quoted_span_by_ref[opening.semantic_ref] = first_relation_unit.text[
                opening.surface_scalar_end : closing.surface_scalar_start
            ]
        self.assertEqual(set(quoted_span_by_ref), first_endpoints)

        burden_match = (
            stage1_response_module._CONTEXT_DE_EPISTEMIC_BURDEN_RE.fullmatch(
                node_by_ref[burden_ref].value
            )
        )
        self.assertIsNotNone(burden_match)
        assert burden_match is not None
        burden_context = burden_match.group("context")
        burden_question = burden_match.group("question")
        burden_affect = burden_match.group("affect")
        burden_question_span = f"{burden_context}で{burden_question}"
        self.assertEqual(quoted_span_by_ref[burden_ref], burden_question_span)
        self.assertEqual(
            burden_question_span + burden_affect,
            node_by_ref[burden_ref].value,
        )
        burden_affect_bindings = tuple(
            row
            for row in first_relation_unit.realized_semantic_bindings
            if row.semantic_ref == burden_ref
            and row.clause_slot.endswith(":affect")
        )
        self.assertEqual(len(burden_affect_bindings), 1)
        self.assertEqual(
            first_relation_unit.text[
                burden_affect_bindings[0].surface_scalar_start :
                burden_affect_bindings[0].surface_scalar_end
            ],
            burden_affect,
        )
        self.assertEqual(quoted_span_by_ref[direction_ref], node_by_ref[direction_ref].value)
        self.assertEqual(memo.count(node_by_ref[burden_ref].value), 1)
        self.assertEqual(memo.count(node_by_ref[direction_ref].value), 1)

        # The second shared COEXISTS replays no exact anchor.  Each endpoint
        # is resolved by one prior-bound typed anaphor.
        second_source_anchors = tuple(
            row
            for row in second_relation_unit.realized_semantic_bindings
            if row.semantic_ref in second_endpoints
            and row.clause_slot.endswith((":anchor", ":affect"))
        )
        self.assertEqual(second_source_anchors, ())
        self.assertNotRegex(second_relation_unit.text, r"[「」]")
        second_anaphors = tuple(
            row
            for row in second_relation_unit.realized_semantic_bindings
            if row.clause_slot.endswith(":argument_anaphora")
        )
        self.assertEqual(len(second_anaphors), 2)
        self.assertEqual(
            {row.semantic_ref for row in second_anaphors},
            second_endpoints,
        )
        self.assertEqual(
            {
                row.semantic_ref
                for row in second_anaphors
                if row.semantic_ref
                not in {anchor.semantic_ref for anchor in first_source_anchors}
            },
            set(),
        )
        for binding in second_anaphors:
            span = second_relation_unit.text[
                binding.surface_scalar_start : binding.surface_scalar_end
            ]
            self.assertEqual(second_relation_unit.text.count(span), 1)

        first_direction_anchors = tuple(
            row
            for row in first_source_anchors
            if row.semantic_ref == direction_ref
            and row.clause_slot.endswith(":anchor")
        )
        second_direction_anaphors = tuple(
            row for row in second_anaphors if row.semantic_ref == direction_ref
        )
        self.assertEqual(len(first_direction_anchors), 1)
        self.assertEqual(len(second_direction_anaphors), 1)
        direction_anaphor = second_relation_unit.text[
            second_direction_anaphors[0].surface_scalar_start :
            second_direction_anaphors[0].surface_scalar_end
        ]
        self.assertEqual(direction_anaphor, "その願い")
        self.assertNotIn(
            "その方向",
            "\n".join(row.text for row in observation_lines),
        )
        self.assertNotRegex(
            "\n".join(row.text for row in observation_lines),
            r"(?:この|次の)(?:方向|願い)",
        )

        # The continuing qualifier belongs to the shared direction endpoint
        # and is surfaced once across the relation pair, not once per edge.
        direction_time_spans = tuple(
            unit.text[binding.surface_scalar_start : binding.surface_scalar_end]
            for unit in (first_relation_unit, second_relation_unit)
            for binding in unit.realized_semantic_bindings
            if binding.semantic_ref == direction_ref
            and binding.clause_slot.endswith(":time")
        )
        self.assertEqual(direction_time_spans, ("今も",))
        self.assertEqual(
            sum(
                unit.text.count("今も")
                for unit in (first_relation_unit, second_relation_unit)
            ),
            1,
        )

        # The direction coordinate particle is followed by its qualifier,
        # never by a separator token.
        second_bindings = second_relation_unit.realized_semantic_bindings
        coordinate_indexes = tuple(
            index
            for index, binding in enumerate(second_bindings)
            if binding.semantic_ref == direction_ref
            and binding.clause_slot.endswith(":case_suffix")
            and second_relation_unit.text[
                binding.surface_scalar_start : binding.surface_scalar_end
            ]
            == "は"
        )
        self.assertEqual(len(coordinate_indexes), 1)
        coordinate_index = coordinate_indexes[0]
        self.assertLess(coordinate_index + 1, len(second_bindings))
        self.assertFalse(
            second_bindings[coordinate_index + 1].clause_slot.endswith(
                ":separator"
            )
        )
        self.assertNotIn("は、", second_relation_unit.text)

        # A non-fixture input with the same typed relation shape must satisfy
        # the same quote/anaphora/qualifier/particle contract.
        synthetic_memo = (
            "この職場で続けていけるか不安。"
            "でも、続けられる形は探したい。"
        )
        self.assertNotIn(synthetic_memo, {row[1] for row in EXACT8})
        (
            synthetic_source,
            synthetic_graph,
            _synthetic_plan,
            _synthetic_artifact,
            _synthetic_visible,
        ) = _private_parts(
            _request(
                record_id="cmee-relation-synthetic-same-shape",
                memo=synthetic_memo,
            )
        )
        synthetic_projection, synthetic_units = _STAGE1_VALIDATION_CAPTURE[
            synthetic_source.envelope.envelope_id
        ]
        synthetic_relations = tuple(
            row
            for row in synthetic_projection.observation_contributions
            if row.relation_operator.value in {"TENSION_WITH", "COEXISTS_WITH"}
        )
        self.assertEqual(
            tuple(row.relation_operator.value for row in synthetic_relations),
            ("TENSION_WITH", "COEXISTS_WITH"),
        )
        synthetic_unit_by_move = {
            row.move_ref: row for row in synthetic_units if row.layer == "LAYER_1"
        }
        synthetic_first, synthetic_second = tuple(
            synthetic_unit_by_move[
                stage1_response_module._move_ref(row.contribution_id)
            ]
            for row in synthetic_relations
        )
        synthetic_endpoints = {
            row.semantic_ref for row in synthetic_relations[0].argument_bindings
        }
        self.assertEqual(
            synthetic_endpoints,
            {
                row.semantic_ref
                for row in synthetic_relations[1].argument_bindings
            },
        )
        self.assertEqual(synthetic_first.text.count("「"), 2)
        self.assertEqual(synthetic_first.text.count("」"), 2)
        self.assertEqual(synthetic_second.text.count("「"), 0)
        self.assertEqual(synthetic_second.text.count("」"), 0)
        synthetic_first_anchor_refs = {
            row.semantic_ref
            for row in synthetic_first.realized_semantic_bindings
            if row.clause_slot.endswith((":anchor", ":affect"))
        }
        synthetic_second_anaphors = tuple(
            row
            for row in synthetic_second.realized_semantic_bindings
            if row.clause_slot.endswith(":argument_anaphora")
        )
        self.assertEqual(synthetic_first_anchor_refs, synthetic_endpoints)
        self.assertEqual(len(synthetic_second_anaphors), 2)
        self.assertEqual(
            {row.semantic_ref for row in synthetic_second_anaphors},
            synthetic_endpoints,
        )
        self.assertTrue(
            all(
                row.semantic_ref in synthetic_first_anchor_refs
                for row in synthetic_second_anaphors
            )
        )
        synthetic_node_by_ref = {
            (
                f"node:{row.node_id}@"
                f"{cmee_contracts_module.CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
            ): row
            for row in synthetic_graph.nodes
        }
        synthetic_direction_ref = next(
            ref
            for ref in synthetic_endpoints
            if synthetic_node_by_ref[ref].node_kind == "wish"
        )
        synthetic_burden_ref = next(
            ref for ref in synthetic_endpoints if ref != synthetic_direction_ref
        )
        synthetic_burden_parts = (
            stage1_response_module._source_context_de_epistemic_burden_parts(
                synthetic_node_by_ref[synthetic_burden_ref].value
            )
        )
        self.assertIsNotNone(synthetic_burden_parts)
        assert synthetic_burden_parts is not None
        self.assertEqual(
            "".join(synthetic_burden_parts),
            synthetic_node_by_ref[synthetic_burden_ref].value,
        )
        self.assertIn(
            synthetic_node_by_ref[synthetic_burden_ref].value,
            synthetic_memo,
        )
        synthetic_time_spans = tuple(
            unit.text[binding.surface_scalar_start : binding.surface_scalar_end]
            for unit in (synthetic_first, synthetic_second)
            for binding in unit.realized_semantic_bindings
            if binding.semantic_ref == synthetic_direction_ref
            and binding.clause_slot.endswith(":time")
        )
        self.assertEqual(synthetic_time_spans, ("今も",))
        synthetic_coordinate_indexes = tuple(
            index
            for index, binding in enumerate(
                synthetic_second.realized_semantic_bindings
            )
            if binding.semantic_ref == synthetic_direction_ref
            and binding.clause_slot.endswith(":case_suffix")
            and synthetic_second.text[
                binding.surface_scalar_start : binding.surface_scalar_end
            ]
            == "は"
        )
        self.assertEqual(len(synthetic_coordinate_indexes), 1)
        synthetic_coordinate_index = synthetic_coordinate_indexes[0]
        self.assertFalse(
            synthetic_second.realized_semantic_bindings[
                synthetic_coordinate_index + 1
            ].clause_slot.endswith(":separator")
        )
        self.assertNotIn("は、", synthetic_second.text)

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
                set(trace.meaning_node_ids),
                {edge.source_node_id, edge.target_node_id},
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
            memo="昨日は記録を書いた。今は不安が残っている。",
            category="生活",
            emotion="不安",
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
        self.assertFalse("起点側" in directional_line.text)
        self.assertFalse("到達側" in directional_line.text)
        directional_projection, _selected = _STAGE1_VALIDATION_CAPTURE[
            directional_source.envelope.envelope_id
        ]
        temporal_candidates = tuple(
            candidate
            for candidate in directional_projection.interpretation_candidates
            if candidate.relation_operator.value == "TEMPORALLY_PRECEDES"
        )
        self.assertEqual(len(temporal_candidates), 1)
        self.assertEqual(
            tuple(binding.role.value for binding in temporal_candidates[0].argument_bindings),
            ("BEFORE", "AFTER"),
        )
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
        self.assertIn("つらい", same_label_contrast.observation)
        self.assertIn("苦しい", same_label_contrast.observation)
        self.assertNotIn("この順", same_label_contrast.observation)

        same_label_directional = _private_parts(
            _request(
                record_id="cmee-same-label-directional",
                memo="昨日は記録を書いた。今は不安が残っている。",
            )
        )[3]
        self.assertIn("あと", same_label_directional.observation)
        self.assertIn("記録", same_label_directional.observation)
        self.assertIn("不安", same_label_directional.observation)
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
            "がという",
            "にという",
            "をという",
            "についてという",
            "という願いあります",
            "という方向がという",
            "またEmlis",
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
                first_reception_sentence = layer2.splitlines()[0]
                self.assertTrue(first_reception_sentence.startswith("Emlisは、"))
                self.assertEqual(first_reception_sentence.count("「"), 0)
                self.assertEqual(first_reception_sentence.count("」"), 0)
                self.assertTrue(
                    any(
                        token in first_reception_sentence
                        for token in stage1_response_module._LAYER2_ANAPHORIC_SURFACES.values()
                    ),
                    "first Reception sentence must use a typed anaphor",
                )
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
        self.assertIn("「散歩したい」という気持ち", bare.artifact.observation)
        self.assertIn("その願い", bare.artifact.reception)
        self.assertNotIn("散歩したい", bare.artifact.reception)
        self.assertNotIn("「", bare.artifact.reception)
        self.assertNotIn("」", bare.artifact.reception)
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
        self.assertIn(
            "「散歩したい」という気持ち",
            outcome.artifact.observation,
        )
        self.assertIn("その願い", outcome.artifact.reception)
        self.assertNotIn("散歩したい", outcome.artifact.reception)
        self.assertNotIn("「", outcome.artifact.reception)
        self.assertNotIn("」", outcome.artifact.reception)
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

    def test_legacy_reception_surface_validator_is_not_active_after_step5(self) -> None:
        invalid_surfaces = (
            "今すぐ相談してください。",
            "この願いを大切にします。もう一文追加します。",
        )
        for invalid_surface in invalid_surfaces:
            with self.subTest(invalid_surface=invalid_surface):
                with (
                    patch.object(
                        emlis_v1a_module,
                        "_cmee_stage1_reception_text",
                        return_value=invalid_surface,
                    ) as legacy_surface,
                    patch.object(
                        emlis_v1a_module,
                        "validate_grounded_human_reception_surface",
                        side_effect=AssertionError("legacy validator called"),
                    ) as legacy_validator,
                ):
                    outcome = MeaningExperienceEngine().generate(_request())
                self.assertEqual(outcome.status.value, "GENERATED")
                self.assertEqual(legacy_surface.call_count, 0)
                self.assertEqual(legacy_validator.call_count, 0)

    def test_step5_atomic_cutover_uses_one_compiler_and_no_legacy_surface(self) -> None:
        case_id, memo, category, emotion, strength = EXACT8[5]
        request = _request(
            record_id=f"step5-{case_id.lower()}",
            memo=memo,
            category=category,
            emotion=emotion,
            strength=strength,
        )
        captured: dict[str, object] = {}
        original_compiler = emlis_v1a_module.compile_stage1_response
        original_common = emlis_v1a_module.compose_emlis_conversation_candidate
        original_validation = emlis_v1a_module.validate_positive_realization_trace

        def compile_once(**kwargs):
            projection, units = original_compiler(**kwargs)
            captured["projection"] = projection
            captured["units"] = units
            return projection, units

        def validate_once(
            validation_source,
            validation_graph,
            validation_artifact,
            safe_lines,
            **kwargs,
        ):
            captured["source"] = validation_source
            captured["safe_lines"] = tuple(safe_lines)
            captured["validation_kwargs"] = kwargs
            return original_validation(
                validation_source,
                validation_graph,
                validation_artifact,
                safe_lines,
                **kwargs,
            )

        with (
            patch.object(
                emlis_v1a_module,
                "compile_stage1_response",
                side_effect=compile_once,
            ) as compiler,
            patch.object(
                emlis_v1a_module,
                "compose_emlis_conversation_candidate",
                wraps=original_common,
            ) as common_guard_path,
            patch.object(
                emlis_v1a_module,
                "validate_positive_realization_trace",
                side_effect=validate_once,
            ) as disabled_validator,
            patch.object(
                emlis_v1a_module,
                "_canonical_r4_observation_lines",
                side_effect=AssertionError("legacy observation called"),
            ) as legacy_observation,
            patch.object(
                emlis_v1a_module,
                "_canonical_r4_tail_lines",
                side_effect=AssertionError("legacy tail called"),
            ) as legacy_tail,
            patch.object(
                emlis_v1a_module,
                "_cmee_nucleus_observation_text",
                side_effect=AssertionError("legacy nucleus surface called"),
            ) as legacy_nucleus,
            patch.object(
                emlis_v1a_module,
                "_cmee_relation_observation_text",
                side_effect=AssertionError("legacy relation surface called"),
            ) as legacy_relation,
            patch.object(
                emlis_v1a_module,
                "_cmee_stage1_reception_text",
                side_effect=AssertionError("legacy reception surface called"),
            ) as legacy_reception,
            patch.object(
                emlis_v1a_module,
                "realize_grounded_human_reception",
                side_effect=AssertionError("legacy reception realizer called"),
            ) as legacy_reception_realizer,
            patch.object(
                emlis_v1a_module,
                "validate_grounded_human_reception_surface",
                side_effect=AssertionError("legacy reception validator called"),
            ) as legacy_reception_validator,
        ):
            outcome = MeaningExperienceEngine().generate(request)

        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        self.assertEqual(compiler.call_count, 1)
        self.assertEqual(common_guard_path.call_count, 1)
        self.assertEqual(disabled_validator.call_count, 1)
        for legacy in (
            legacy_observation,
            legacy_tail,
            legacy_nucleus,
            legacy_relation,
            legacy_reception,
            legacy_reception_realizer,
            legacy_reception_validator,
        ):
            self.assertEqual(legacy.call_count, 0)

        graph = outcome.meaning_graph
        artifact = outcome.artifact
        projection = captured["projection"]
        units = captured["units"]
        assert graph is not None and artifact is not None
        roles = tuple(row.role for row in artifact.trace)
        self.assertEqual(roles, ("OBSERVATION", "OBSERVATION", "RECEPTION", "RECEPTION", "RECEPTION"))
        self.assertEqual(len(artifact.observation.splitlines()), 2)
        self.assertEqual(len(artifact.reception.splitlines()), 3)
        self.assertEqual(
            tuple(row[0] for row in artifact.common_guard_proof.guarded_observation_units),
            tuple(
                row.source_sentence_id
                for row in artifact.trace
                if row.role == "OBSERVATION"
            ),
        )
        self.assertTrue(
            all(
                row.source_sentence_id.startswith("cmee:reception:")
                for row in artifact.trace
                if row.role == "RECEPTION"
            )
        )
        variants = {
            row.emlis_stage1_extension.composition_variant_id
            for row in artifact.trace
            if row.role in {"OBSERVATION", "RECEPTION"}
            and row.emlis_stage1_extension is not None
        }
        self.assertEqual(len(variants), 1)
        for row in artifact.trace:
            extension = row.emlis_stage1_extension
            if row.role == "OBSERVATION":
                assert extension is not None
                self.assertTrue(extension.contribution_refs)
                self.assertTrue(extension.interpretation_candidate_refs)
                self.assertIsNone(extension.subjective_claim_ref)
                self.assertIsNone(extension.speaker_owner)
            elif row.role == "RECEPTION":
                assert extension is not None
                self.assertTrue(extension.subjective_claim_ref)
                self.assertTrue(extension.basis_observation_contribution_refs)
                self.assertTrue(extension.basis_trace_refs)
                self.assertEqual(extension.speaker_owner, "EMLIS")
                self.assertEqual(extension.user_fact_effect, 0)

        cmee_contracts_module.validate_stage1_trace_spine(
            artifact.trace,
            projection,
            grounded_graph=graph,
            parent_plan=artifact.plan,
        )
        projection_ref = cmee_contracts_module.stage1_projection_artifact_ref(
            projection
        )
        identity_args = (
            graph.source_envelope_id,
            graph.graph_id,
            artifact.plan.plan_id,
            artifact.common_guard_proof.proof_id,
            artifact.observation,
            tuple(row.text for row in artifact.visible_unknowns),
            artifact.reception,
        )
        self.assertEqual(
            artifact.artifact_id,
            _artifact_id(
                *identity_args,
                emlis_stage1_projection_ref=projection_ref,
            ),
        )
        self.assertNotEqual(artifact.artifact_id, _artifact_id(*identity_args))
        self.assertEqual(
            tuple(artifact.__dataclass_fields__),
            (
                "artifact_id",
                "realizer_contract_ids",
                "trust_policy_ids",
                "common_guard_proof",
                "observation",
                "reception",
                "plan",
                "trace",
                "visible_unknowns",
            ),
        )
        self.assertEqual(len(units), len(artifact.trace))
        self.assertTrue(_structural_trace_valid(outcome))

        first_reception = roles.index("RECEPTION")
        reception_row = artifact.trace[first_reception]
        assert reception_row.emlis_stage1_extension is not None
        invalid_extension = replace(
            reception_row.emlis_stage1_extension,
            user_fact_effect=1,
        )
        invalid_trace = list(artifact.trace)
        invalid_trace[first_reception] = replace(
            reception_row,
            emlis_stage1_extension=invalid_extension,
        )
        with self.assertRaisesRegex(
            cmee_contracts_module.CMEEStage1ContractError,
            "user_fact_effect_invalid",
        ):
            cmee_contracts_module.validate_stage1_trace_spine(
                tuple(invalid_trace),
                projection,
                grounded_graph=graph,
                parent_plan=artifact.plan,
            )
        self.assertFalse(
            _structural_trace_valid(
                replace(
                    outcome,
                    artifact=replace(artifact, trace=tuple(invalid_trace)),
                )
            )
        )
        reordered = (
            artifact.trace[0],
            artifact.trace[first_reception],
            artifact.trace[1],
            *artifact.trace[first_reception + 1 :],
        )
        with self.assertRaisesRegex(
            cmee_contracts_module.CMEEStage1ContractError,
            "role_order_invalid",
        ):
            cmee_contracts_module.validate_stage1_trace_spine(
                reordered,
                projection,
                grounded_graph=graph,
                parent_plan=artifact.plan,
            )
        self.assertFalse(
            _structural_trace_valid(
                replace(outcome, artifact=replace(artifact, trace=reordered))
            )
        )

        reception_indexes = tuple(
            index
            for index, row in enumerate(artifact.trace)
            if row.role == "RECEPTION"
        )
        claim_swapped_trace = list(artifact.trace)
        left_index, right_index = reception_indexes[:2]
        left_extension = artifact.trace[left_index].emlis_stage1_extension
        right_extension = artifact.trace[right_index].emlis_stage1_extension
        assert left_extension is not None and right_extension is not None
        claim_swapped_trace[left_index] = replace(
            artifact.trace[left_index],
            emlis_stage1_extension=right_extension,
        )
        claim_swapped_trace[right_index] = replace(
            artifact.trace[right_index],
            emlis_stage1_extension=left_extension,
        )
        claim_swapped_artifact = replace(
            artifact,
            trace=tuple(claim_swapped_trace),
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "stage1_positive_trace_extension_invalid",
        ):
            original_validation(
                captured["source"],
                graph,
                claim_swapped_artifact,
                captured["safe_lines"],
                **captured["validation_kwargs"],
            )

        lineage_swapped_trace = list(artifact.trace)
        lineage_swapped_trace[0] = replace(
            artifact.trace[0],
            meaning_node_ids=artifact.trace[1].meaning_node_ids,
            meaning_edge_ids=artifact.trace[1].meaning_edge_ids,
            evidence_ids=artifact.trace[1].evidence_ids,
        )
        with self.assertRaisesRegex(
            CMEEVerticalError,
            "stage1_positive_trace_extension_invalid",
        ):
            original_validation(
                captured["source"],
                graph,
                replace(artifact, trace=tuple(lineage_swapped_trace)),
                captured["safe_lines"],
                **captured["validation_kwargs"],
            )

    def test_step5_compiler_failure_is_terminal_without_legacy_fallback(self) -> None:
        with (
            patch.object(
                emlis_v1a_module,
                "compile_stage1_response",
                side_effect=cmee_contracts_module.CMEEStage1ContractError(
                    "stage1_no_hard_valid_realization"
                ),
            ) as compiler,
            patch.object(
                emlis_v1a_module,
                "_canonical_r4_observation_lines",
                side_effect=AssertionError("legacy observation called"),
            ) as legacy_observation,
            patch.object(
                emlis_v1a_module,
                "_canonical_r4_tail_lines",
                side_effect=AssertionError("legacy tail called"),
            ) as legacy_tail,
            patch.object(
                emlis_v1a_module,
                "_cmee_stage1_reception_text",
                side_effect=AssertionError("legacy reception called"),
            ) as legacy_reception,
        ):
            outcome = MeaningExperienceEngine().generate(_request())
        self.assertEqual(outcome.status.value, "UNAVAILABLE")
        self.assertEqual(
            outcome.reason_codes,
            ("stage1_no_hard_valid_realization",),
        )
        self.assertIsNone(outcome.artifact)
        self.assertEqual(compiler.call_count, 1)
        self.assertEqual(legacy_observation.call_count, 0)
        self.assertEqual(legacy_tail.call_count, 0)
        self.assertEqual(legacy_reception.call_count, 0)

    def test_step5_common_guard_failure_is_terminal_without_legacy_fallback(
        self,
    ) -> None:
        case_id, memo, category, emotion, strength = EXACT8[1]
        original_compiler = emlis_v1a_module.compile_stage1_response
        original_common = emlis_v1a_module.compose_emlis_conversation_candidate

        def rejected_common_guard(*args, **kwargs):
            candidate = original_common(*args, **kwargs)
            return replace(
                candidate,
                comment_text="",
                composer_source="unavailable",
                status="unavailable",
                ai_generated=False,
                rejection_reasons=["forced_common_guard_rejection"],
            )

        with (
            patch.object(
                emlis_v1a_module,
                "compile_stage1_response",
                wraps=original_compiler,
            ) as compiler,
            patch.object(
                emlis_v1a_module,
                "compose_emlis_conversation_candidate",
                side_effect=rejected_common_guard,
            ) as common_guard_path,
            patch.object(
                emlis_v1a_module,
                "_canonical_r4_observation_lines",
                side_effect=AssertionError("legacy observation called"),
            ) as legacy_observation,
            patch.object(
                emlis_v1a_module,
                "_canonical_r4_tail_lines",
                side_effect=AssertionError("legacy tail called"),
            ) as legacy_tail,
            patch.object(
                emlis_v1a_module,
                "_cmee_stage1_reception_text",
                side_effect=AssertionError("legacy reception called"),
            ) as legacy_reception,
            patch.object(
                emlis_v1a_module,
                "realize_grounded_human_reception",
                side_effect=AssertionError("legacy reception realizer called"),
            ) as legacy_reception_realizer,
        ):
            outcome = MeaningExperienceEngine().generate(
                _request(
                    record_id=f"step5-no-fallback-{case_id.lower()}",
                    memo=memo,
                    category=category,
                    emotion=emotion,
                    strength=strength,
                )
            )
        self.assertEqual(outcome.status.value, "UNAVAILABLE")
        self.assertEqual(
            outcome.reason_codes,
            ("plan_bound_observation_realizer_unavailable",),
        )
        self.assertIsNone(outcome.artifact)
        self.assertEqual(compiler.call_count, 1)
        self.assertEqual(common_guard_path.call_count, 1)
        for legacy in (
            legacy_observation,
            legacy_tail,
            legacy_reception,
            legacy_reception_realizer,
        ):
            self.assertEqual(legacy.call_count, 0)

    def test_role_aware_exact8_comparator_and_mutations(self) -> None:
        material_unknown = MeaningExperienceEngine().generate(
            _request(
                record_id="cmee-role-aware-material-unknown",
                memo=MATERIAL_UNKNOWN_MEMO,
            )
        )
        self.assertEqual(material_unknown.status.value, "LIMITED")
        self.assertEqual(
            material_unknown.reason_codes,
            ("text_grounded_source_explicit_limited",),
        )
        self.assertIsNotNone(material_unknown.artifact)
        self.assertTrue(_structural_trace_valid(material_unknown))
        assert material_unknown.artifact is not None
        self.assertEqual(len(material_unknown.artifact.visible_unknowns), 1)
        self.assertEqual(
            tuple(row.role for row in material_unknown.artifact.trace),
            ("OBSERVATION", "UNKNOWN", "RECEPTION", "RECEPTION"),
        )

        case_id, memo, category, emotion, strength = EXACT8[5]
        outcome = MeaningExperienceEngine().generate(
            _request(
                record_id=f"role-aware-{case_id.lower()}",
                memo=memo,
                category=category,
                emotion=emotion,
                strength=strength,
            )
        )
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        artifact = outcome.artifact
        assert artifact is not None
        self.assertTrue(_structural_trace_valid(outcome))
        self.assertEqual(
            tuple(row.role for row in artifact.trace),
            ("OBSERVATION", "OBSERVATION", "RECEPTION", "RECEPTION", "RECEPTION"),
        )
        reception_index = next(
            index for index, row in enumerate(artifact.trace) if row.role == "RECEPTION"
        )
        observation_index = next(
            index for index, row in enumerate(artifact.trace) if row.role == "OBSERVATION"
        )
        reception_extension = artifact.trace[reception_index].emlis_stage1_extension
        assert reception_extension is not None
        mutations = {
            "observation_without_meaning": replace(
                artifact.trace[observation_index],
                meaning_node_ids=(),
                meaning_edge_ids=(),
            ),
            "reception_without_meaning": replace(
                artifact.trace[reception_index],
                meaning_node_ids=(),
                meaning_edge_ids=(),
            ),
            "reception_wrong_speaker": replace(
                artifact.trace[reception_index],
                emlis_stage1_extension=replace(
                    reception_extension,
                    speaker_owner=None,
                ),
            ),
            "reception_bool_user_fact": replace(
                artifact.trace[reception_index],
                emlis_stage1_extension=replace(
                    reception_extension,
                    user_fact_effect=False,
                ),
            ),
            "reception_wrong_schema": replace(
                artifact.trace[reception_index],
                emlis_stage1_extension=replace(
                    reception_extension,
                    schema_version="cocolon.cmee.invalid.v1",
                ),
            ),
            "reception_raw_string_domain": replace(
                artifact.trace[reception_index],
                emlis_stage1_extension=replace(
                    reception_extension,
                    claim_domain="EMLIS_SUBJECTIVE_RESPONSE",
                ),
            ),
            "reception_unreachable_basis": replace(
                artifact.trace[reception_index],
                emlis_stage1_extension=replace(
                    reception_extension,
                    basis_observation_contribution_refs=("contribution:foreign",),
                ),
            ),
            "reception_positive_constraint": replace(
                artifact.trace[reception_index],
                constrained_by_owner_ids=("owner:forged",),
            ),
            "reception_basis_order_mismatch": replace(
                artifact.trace[reception_index],
                emlis_stage1_extension=replace(
                    reception_extension,
                    basis_trace_refs=tuple(
                        reversed(reception_extension.basis_trace_refs)
                    ),
                ),
            ),
        }
        for name, changed_trace in mutations.items():
            with self.subTest(name=name):
                trace = list(artifact.trace)
                index = (
                    observation_index
                    if name.startswith("observation_")
                    else reception_index
                )
                trace[index] = changed_trace
                self.assertFalse(
                    _structural_trace_valid(
                        replace(outcome, artifact=replace(artifact, trace=tuple(trace)))
                    )
                )

        sequence_mutations = {
            "observation_after_reception": (
                artifact.trace[0],
                artifact.trace[reception_index],
                artifact.trace[1],
                *artifact.trace[reception_index + 1 :],
            ),
            "duplicate_reception": (*artifact.trace, artifact.trace[-1]),
        }
        for name, trace in sequence_mutations.items():
            with self.subTest(name=name):
                self.assertFalse(
                    _structural_trace_valid(
                        replace(outcome, artifact=replace(artifact, trace=trace))
                    )
                )
        self.assertFalse(
            _structural_trace_valid(
                replace(
                    outcome,
                    artifact=replace(
                        artifact,
                        reception=f"{artifact.reception}\nforged extra line",
                    ),
                )
            )
        )
        self.assertFalse(
            _structural_trace_valid(
                replace(
                    outcome,
                    artifact=replace(
                        artifact,
                        reception=f"{artifact.reception}\n",
                    ),
                )
            )
        )
        self.assertFalse(
            _structural_trace_valid(
                replace(
                    outcome,
                    artifact=replace(
                        artifact,
                        realizer_contract_ids=("cocolon.cmee.forged.v1",),
                    ),
                )
            )
        )
        forged_guard_results = (
            replace(
                artifact.common_guard_proof.guard_results[0],
                passed=False,
            ),
            *artifact.common_guard_proof.guard_results[1:],
        )
        self.assertFalse(
            _structural_trace_valid(
                replace(
                    outcome,
                    artifact=replace(
                        artifact,
                        common_guard_proof=replace(
                            artifact.common_guard_proof,
                            guard_results=forged_guard_results,
                        ),
                    ),
                )
            )
        )

        body_free, _full = run_exact8_candidate()
        self.assertEqual(len(EXACT8), 8)
        self.assertEqual(body_free["case_count"], 8)
        self.assertEqual(body_free["limited_count"], 0)
        self.assertEqual(body_free["artifact_count"], 8)
        self.assertEqual(body_free["generated_count"], 8)
        self.assertEqual(body_free["structural_trace_valid_count"], 8)
        self.assertEqual(
            tuple(
                row["case_id"]
                for row in body_free["cases"]
                if row["structural_trace_valid"]
            ),
            tuple(row[0] for row in EXACT8),
        )
        self.assertEqual(
            body_free["candidate_state"],
            "GENERATED_FOR_PRODUCT_READ_DISABLED",
        )
        self.assertFalse(body_free["product_read_eligible"])
        self.assertFalse(body_free["product_read_evaluated"])
        self.assertFalse(body_free["automatic_progression"])

    def _assert_step6_generated(self, run: dict[str, object]) -> None:
        outcome = run["outcome"]
        captured = run["captured"]
        self.assertEqual(outcome.status.value, "GENERATED", outcome.reason_codes)
        self.assertIsNotNone(outcome.artifact)
        self.assertIsNotNone(outcome.meaning_graph)
        self.assertFalse(outcome.automatic_progression)
        self.assertEqual(run["compiler_calls"], 1)
        self.assertEqual(run["composer_calls"], 1)
        self.assertEqual(run["legacy_calls"], (0, 0, 0, 0))
        self.assertIn("projection", captured)
        self.assertIn("selected_units", captured)
        self.assertTrue(_structural_trace_valid(outcome))
        cmee_contracts_module.validate_stage1_projection(
            captured["projection"],
            grounded_graph=captured["grounded_graph"],
            parent_plan=captured["parent_plan"],
        )
        cmee_contracts_module.validate_stage1_trace_spine(
            outcome.artifact.trace,
            captured["projection"],
            grounded_graph=captured["grounded_graph"],
            parent_plan=outcome.artifact.plan,
        )

    def _assert_step6_unavailable(
        self,
        run: dict[str, object],
        reason_code: str,
        *,
        compiler_calls: int,
    ) -> None:
        outcome = run["outcome"]
        self.assertEqual(outcome.status.value, "UNAVAILABLE")
        self.assertEqual(outcome.reason_codes, (reason_code,))
        self.assertIsNone(outcome.artifact)
        self.assertFalse(outcome.automatic_progression)
        self.assertEqual(run["compiler_calls"], compiler_calls)
        self.assertEqual(run["composer_calls"], 0)
        self.assertEqual(run["legacy_calls"], (0, 0, 0, 0))

    def test_step6_exact12_registry_is_body_free_ascii_and_test_executed(self) -> None:
        with patch.object(
            MeaningExperienceEngine,
            "generate",
            side_effect=AssertionError("body-free registry executed engine"),
        ) as engine_path:
            registry = _body_free_mutation_registry()
        self.assertEqual(engine_path.call_count, 0)
        self.assertEqual(registry["case_count"], 12)
        self.assertFalse(registry["body_payload_present"])
        self.assertFalse(registry["runner_executes_source_bodies"])
        self.assertEqual(registry["execution_owner"], "current_and_new_tests")
        self.assertEqual(registry["class_counts"], _STEP6_MUTATION_CLASS_COUNTS)
        self.assertEqual(len(STAGE1_KAREN_DERIVED_MUTATION_SET_V1), 12)
        self.assertEqual(
            tuple(
                (
                    row["case_id"],
                    row["mutation_class"],
                    row["mutation_operator"],
                )
                for row in registry["cases"]
            ),
            STAGE1_KAREN_DERIVED_MUTATION_SET_V1,
        )
        self.assertEqual(
            len({row[0] for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1}),
            12,
        )
        self.assertEqual(
            len({row[2] for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1}),
            12,
        )
        for case_id, mutation_class, operator in STAGE1_KAREN_DERIVED_MUTATION_SET_V1:
            with self.subTest(case_id=case_id):
                self.assertTrue(
                    all(ord(character) < 128 for character in case_id + mutation_class + operator)
                )
                self.assertRegex(case_id, r"^KDM-(?:SE|RC|CB|SU)-\d{2}$")
        self.assertEqual(
            {
                mutation_class: sum(
                    row[1] == mutation_class
                    for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
                )
                for mutation_class in _STEP6_MUTATION_CLASS_COUNTS
            },
            _STEP6_MUTATION_CLASS_COUNTS,
        )

        registry_source = inspect.getsource(_body_free_mutation_registry)
        self.assertNotIn("engine.generate", registry_source)
        self.assertNotIn("MeaningExperienceEngine", registry_source)
        for body in _step6_private_bodies():
            self.assertNotIn(body, registry_source)
        production_source = "\n".join(
            (
                inspect.getsource(emlis_v1a_module),
                inspect.getsource(stage1_response_module),
                inspect.getsource(cmee_contracts_module),
            )
        )
        for case_id, _mutation_class, _operator in STAGE1_KAREN_DERIVED_MUTATION_SET_V1:
            self.assertNotIn(case_id, production_source)
        for body in _step6_private_bodies():
            self.assertNotIn(body, production_source)

    def test_step6_semantic_equivalence_mutations_preserve_structured_invariants(
        self,
    ) -> None:
        operators = tuple(
            row[2]
            for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
            if row[1] == "SEMANTIC_EQUIVALENCE_MUTATION"
        )
        self.assertEqual(
            operators,
            ("REGISTER_INFLECTION", "LEXICAL_PARAPHRASE", "CLAUSE_ORDER"),
        )
        for operator in operators:
            with self.subTest(operator=operator):
                before_request, after_request = _step6_mutation_requests(operator)
                assert after_request is not None
                before = _run_step6_mutation_request(before_request)
                after = _run_step6_mutation_request(after_request)
                self._assert_step6_generated(before)
                self._assert_step6_generated(after)
                self.assertEqual(
                    _step6_projection_shape(
                        before["captured"],
                        include_claim_targets=True,
                    ),
                    _step6_projection_shape(
                        after["captured"],
                        include_claim_targets=True,
                    ),
                )
                self.assertEqual(
                    _step6_trace_spine(before),
                    _step6_trace_spine(after),
                )
                for run in (before, after):
                    projection = run["captured"]["projection"]
                    semantic_keys = tuple(
                        row.canonical_semantic_key
                        for row in projection.observation_contributions
                    )
                    self.assertEqual(len(semantic_keys), len(set(semantic_keys)))

        clause_before, clause_after = _step6_mutation_requests("CLAUSE_ORDER")
        assert clause_after is not None
        before_sentences = tuple(
            row
            for row in clause_before.current_input_bundle.thought_text.split("。")
            if row
        )
        after_sentences = tuple(
            row
            for row in clause_after.current_input_bundle.thought_text.split("。")
            if row
        )
        self.assertEqual(after_sentences, tuple(reversed(before_sentences)))

    def test_step6_whole_state_negation_table_fails_closed_before_compilation(
        self,
    ) -> None:
        expected_tenses = {"plain", "past", "polite", "polite-past"}
        self.assertEqual(
            {
                tense
                for morphology, tense, _particle, _memo
                in _STEP6_WHOLE_STATE_NEGATION_VARIANTS
                if morphology == "noun"
            },
            expected_tenses,
        )
        self.assertEqual(
            {
                tense
                for morphology, tense, _particle, _memo
                in _STEP6_WHOLE_STATE_NEGATION_VARIANTS
                if morphology == "verb"
            },
            expected_tenses,
        )
        expected_groups = {
            ("noun", "none"),
            ("noun", "も"),
            ("adjective", "は"),
            ("verb", "none"),
        }
        self.assertEqual(
            {
                (morphology, particle)
                for morphology, _tense, particle, _memo
                in _STEP6_WHOLE_STATE_NEGATION_VARIANTS
            },
            expected_groups,
        )
        for group in expected_groups:
            self.assertEqual(
                {
                    tense
                    for morphology, tense, particle, _memo
                    in _STEP6_WHOLE_STATE_NEGATION_VARIANTS
                    if (morphology, particle) == group
                },
                expected_tenses,
            )
        self.assertEqual(
            len(
                {
                    (morphology, tense, particle, memo)
                    for morphology, tense, particle, memo
                    in _STEP6_WHOLE_STATE_NEGATION_VARIANTS
                }
            ),
            len(_STEP6_WHOLE_STATE_NEGATION_VARIANTS),
        )
        for index, (morphology, tense, particle, memo) in enumerate(
            _STEP6_WHOLE_STATE_NEGATION_VARIANTS,
            start=1,
        ):
            with self.subTest(
                morphology=morphology,
                tense=tense,
                particle=particle,
            ):
                run = _run_step6_mutation_request(
                    _request(record_id=f"step6-whole-negation-{index}", memo=memo)
                )
                self._assert_step6_unavailable(
                    run,
                    "lexical_role_negation_unrepresentable",
                    compiler_calls=0,
                )

    def test_step6_relation_contrast_mutations_preserve_typed_direction_and_bounds(
        self,
    ) -> None:
        operators = tuple(
            row[2]
            for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
            if row[1] == "RELATION_CONTRAST_MUTATION"
        )
        self.assertEqual(
            operators,
            ("TEMPORAL_ORDER", "COEXISTENCE_TENSION", "SEQUENCE_CAUSE"),
        )

        temporal_request, reversed_temporal_request = _step6_mutation_requests(
            "TEMPORAL_ORDER"
        )
        assert reversed_temporal_request is not None
        temporal = _run_step6_mutation_request(temporal_request)
        reversed_temporal = _run_step6_mutation_request(reversed_temporal_request)
        self._assert_step6_generated(temporal)
        self._assert_step6_unavailable(
            reversed_temporal,
            "stage1_projection_unavailable",
            compiler_calls=1,
        )
        temporal_capture = temporal["captured"]
        temporal_projection = temporal_capture["projection"]
        temporal_graph = temporal_capture["grounded_graph"]
        temporal_candidates = tuple(
            row
            for row in temporal_projection.interpretation_candidates
            if row.relation_operator.value == "TEMPORALLY_PRECEDES"
        )
        self.assertEqual(len(temporal_candidates), 1)
        temporal_candidate = temporal_candidates[0]
        self.assertEqual(temporal_candidate.candidate_kind.value, "RESIDUE_AFTER_EVENT")
        self.assertEqual(temporal_candidate.semantic_operator.value, "PRESENT_RESIDUE")
        self.assertEqual(
            tuple(row.role.value for row in temporal_candidate.argument_bindings),
            ("BEFORE", "AFTER"),
        )
        temporal_edges = tuple(
            row for row in temporal_graph.edges if row.relation == "shift_from_to"
        )
        self.assertEqual(len(temporal_edges), 1)
        temporal_edge = temporal_edges[0]
        self.assertEqual(temporal_edge.grounding_kind, "user_stated_relation")
        self.assertEqual(temporal_edge.epistemic_state.value, "SOURCE_EXPLICIT")

        def local_ref(semantic_ref: str) -> str:
            return semantic_ref.split(":", 1)[1].split("@", 1)[0]

        self.assertEqual(
            tuple(local_ref(row.semantic_ref) for row in temporal_candidate.argument_bindings),
            (temporal_edge.source_node_id, temporal_edge.target_node_id),
        )
        temporal_node_by_id = {row.node_id: row for row in temporal_graph.nodes}
        self.assertEqual(
            (
                temporal_node_by_id[temporal_edge.source_node_id].node_kind,
                temporal_node_by_id[temporal_edge.target_node_id].node_kind,
            ),
            ("event", "reaction"),
        )
        self.assertIn("before_time_scope:past", temporal_candidate.required_qualifiers)
        self.assertIn("after_time_scope:present", temporal_candidate.required_qualifiers)
        temporal_relation_traces = tuple(
            row
            for row in temporal["outcome"].artifact.trace
            if row.meaning_edge_ids
        )
        temporal_observation_relation_traces = tuple(
            row for row in temporal_relation_traces if row.role == "OBSERVATION"
        )
        self.assertEqual(len(temporal_observation_relation_traces), 1)
        self.assertTrue(
            all(
                row.meaning_edge_ids == (temporal_edge.edge_id,)
                and set(row.meaning_node_ids)
                == {temporal_edge.source_node_id, temporal_edge.target_node_id}
                and row.evidence_ids == temporal_edge.evidence_ids
                for row in temporal_relation_traces
            )
        )
        self.assertFalse(
            any(
                row.relation_operator.value == "SOURCE_EXPLICIT_CAUSE"
                for row in temporal_projection.interpretation_candidates
            )
        )

        coexist_request, tension_request = _step6_mutation_requests(
            "COEXISTENCE_TENSION"
        )
        assert tension_request is not None
        coexist = _run_step6_mutation_request(coexist_request)
        tension = _run_step6_mutation_request(tension_request)
        self._assert_step6_generated(coexist)
        self._assert_step6_generated(tension)
        coexist_capture = coexist["captured"]
        tension_capture = tension["captured"]
        coexist_projection = coexist_capture["projection"]
        tension_projection = tension_capture["projection"]
        coexist_relation_candidates = tuple(
            row
            for row in coexist_projection.interpretation_candidates
            if row.relation_operator.value != "NO_RELATION_CLAIM"
        )
        tension_relation_candidates = tuple(
            row
            for row in tension_projection.interpretation_candidates
            if row.relation_operator.value != "NO_RELATION_CLAIM"
        )
        self.assertEqual(len(coexist_relation_candidates), 1)
        self.assertEqual(len(tension_relation_candidates), 1)
        self.assertEqual(
            (
                coexist_relation_candidates[0].candidate_kind.value,
                coexist_relation_candidates[0].semantic_operator.value,
                coexist_relation_candidates[0].relation_operator.value,
            ),
            ("COEXISTENCE", "SYNTHESIZE_RELATION", "COEXISTS_WITH"),
        )
        self.assertEqual(
            (
                tension_relation_candidates[0].candidate_kind.value,
                tension_relation_candidates[0].semantic_operator.value,
                tension_relation_candidates[0].relation_operator.value,
            ),
            ("TENSION", "SYNTHESIZE_RELATION", "TENSION_WITH"),
        )
        relation_aliases = {
            "COEXISTENCE": "RELATION_KIND",
            "TENSION": "RELATION_KIND",
            "COEXISTS_WITH": "RELATION_OPERATOR",
            "TENSION_WITH": "RELATION_OPERATOR",
            "OBSERVE_COEXISTENCE": "RELATION_CONTRIBUTION",
            "OBSERVE_TENSION": "RELATION_CONTRIBUTION",
            "coexistence": "relation-edge",
            "contrast": "relation-edge",
            "cocolon.cmee.v1a.stage1.relation.coexistence.v1": "RELATION_RULE",
            "cocolon.cmee.v1a.stage1.relation.contrast.v1": "RELATION_RULE",
            "cocolon.cmee.v1a.stage1.layer1.observe_coexistence.v1": "CONTRIBUTION_RULE",
            "cocolon.cmee.v1a.stage1.layer1.observe_tension.v1": "CONTRIBUTION_RULE",
        }
        self.assertEqual(
            _step6_candidate_shape(
                coexist_capture,
                coexist_relation_candidates[0],
                relation_aliases,
            ),
            _step6_candidate_shape(
                tension_capture,
                tension_relation_candidates[0],
                relation_aliases,
            ),
        )
        coexist_relation_contributions = tuple(
            row
            for row in coexist_projection.observation_contributions
            if row.relation_operator.value != "NO_RELATION_CLAIM"
        )
        tension_relation_contributions = tuple(
            row
            for row in tension_projection.observation_contributions
            if row.relation_operator.value != "NO_RELATION_CLAIM"
        )
        self.assertEqual(len(coexist_relation_contributions), 1)
        self.assertEqual(len(tension_relation_contributions), 1)
        self.assertEqual(
            _step6_contribution_shape(
                coexist_capture,
                coexist_relation_contributions[0],
                relation_aliases,
            ),
            _step6_contribution_shape(
                tension_capture,
                tension_relation_contributions[0],
                relation_aliases,
            ),
        )
        coexist_edges = coexist_capture["grounded_graph"].edges
        tension_edges = tension_capture["grounded_graph"].edges
        self.assertEqual(tuple(row.relation for row in coexist_edges), ("coexistence",))
        self.assertEqual(tuple(row.relation for row in tension_edges), ("contrast",))
        self.assertEqual(
            _step6_edge_shape(coexist_capture, coexist_edges[0], relation_aliases),
            _step6_edge_shape(tension_capture, tension_edges[0], relation_aliases),
        )
        self.assertEqual(
            tuple(
                sorted(
                    _step6_candidate_shape(coexist_capture, row)
                    for row in coexist_projection.interpretation_candidates
                    if row.relation_operator.value == "NO_RELATION_CLAIM"
                )
            ),
            tuple(
                sorted(
                    _step6_candidate_shape(tension_capture, row)
                    for row in tension_projection.interpretation_candidates
                    if row.relation_operator.value == "NO_RELATION_CLAIM"
                )
            ),
        )
        self.assertEqual(
            (
                coexist_projection.observation_depth_class,
                coexist_projection.subjective_depth_class,
                coexist_projection.temperature_class,
            ),
            (
                tension_projection.observation_depth_class,
                tension_projection.subjective_depth_class,
                tension_projection.temperature_class,
            ),
        )

        def relation_neutral_trace_spine(run: dict[str, object]) -> tuple:
            return tuple(
                (
                    *row[:4],
                    tuple("relation-edge" for _relation in row[4]),
                    *row[5:],
                )
                for row in _step6_trace_spine(run)
            )

        self.assertEqual(
            relation_neutral_trace_spine(coexist),
            relation_neutral_trace_spine(tension),
        )
        self.assertFalse(
            any(
                row.relation == "user_stated_cause"
                for row in (*coexist_edges, *tension_edges)
            )
        )

        sequence_request, cause_request = _step6_mutation_requests("SEQUENCE_CAUSE")
        assert cause_request is not None
        sequence = _run_step6_mutation_request(sequence_request)
        cause = _run_step6_mutation_request(cause_request)
        self._assert_step6_generated(sequence)
        self._assert_step6_generated(cause)
        sequence_capture = sequence["captured"]
        cause_capture = cause["captured"]
        sequence_projection = sequence_capture["projection"]
        cause_projection = cause_capture["projection"]
        self.assertEqual(sequence_capture["grounded_graph"].edges, ())
        self.assertFalse(
            any(
                row.relation_operator.value != "NO_RELATION_CLAIM"
                for row in sequence_projection.interpretation_candidates
            )
        )
        cause_edges = cause_capture["grounded_graph"].edges
        self.assertEqual(len(cause_edges), 1)
        self.assertEqual(
            (
                cause_edges[0].relation,
                cause_edges[0].grounding_kind,
                cause_edges[0].epistemic_state.value,
            ),
            ("user_stated_cause", "user_stated_relation", "SOURCE_EXPLICIT"),
        )
        cause_candidates = tuple(
            row
            for row in cause_projection.interpretation_candidates
            if row.relation_operator.value == "SOURCE_EXPLICIT_CAUSE"
        )
        self.assertEqual(len(cause_candidates), 1)
        self.assertEqual(cause_candidates[0].candidate_kind.value, "SOURCE_STATED_CAUSE")
        self.assertEqual(
            tuple(row.role.value for row in cause_candidates[0].argument_bindings),
            ("CAUSE", "EFFECT"),
        )
        cause_contributions = tuple(
            row
            for row in cause_projection.observation_contributions
            if row.relation_operator.value == "SOURCE_EXPLICIT_CAUSE"
        )
        self.assertEqual(len(cause_contributions), 1)
        self.assertEqual(cause_contributions[0].contribution_kind.value, "OBSERVE_TIME_RELATION")

        def without_visible_claim_cardinality(value):
            if isinstance(value, tuple):
                if (
                    len(value) == 9
                    and value[0] in {"REQUIRED", "ACTIVE_OPTIONAL"}
                    and value[1] in {"RESOLVED", "UNRESOLVED", "MISSING_OR_INVALID"}
                ):
                    value = (*value[:6], *value[7:])
                return tuple(without_visible_claim_cardinality(row) for row in value)
            return value

        self.assertEqual(
            tuple(
                sorted(
                    without_visible_claim_cardinality(
                        _step6_node_shape(sequence_capture, row)
                    )
                    for row in sequence_capture["grounded_graph"].nodes
                )
            ),
            tuple(
                sorted(
                    without_visible_claim_cardinality(
                        _step6_node_shape(cause_capture, row)
                    )
                    for row in cause_capture["grounded_graph"].nodes
                )
            ),
        )
        self.assertEqual(
            sum(
                len(row.visible_claim_refs)
                for row in cause_capture["grounded_graph"].owner_dispositions
            ),
            sum(
                len(row.visible_claim_refs)
                for row in sequence_capture["grounded_graph"].owner_dispositions
            )
            + 1,
        )
        self.assertEqual(
            tuple(
                sorted(
                    without_visible_claim_cardinality(
                        _step6_candidate_shape(sequence_capture, row)
                    )
                    for row in sequence_projection.interpretation_candidates
                )
            ),
            tuple(
                sorted(
                    without_visible_claim_cardinality(
                        _step6_candidate_shape(cause_capture, row)
                    )
                    for row in cause_projection.interpretation_candidates
                    if row.relation_operator.value == "NO_RELATION_CLAIM"
                )
            ),
        )
        self.assertEqual(
            (
                sequence_projection.observation_depth_class,
                sequence_projection.subjective_depth_class,
                sequence_projection.temperature_class,
            ),
            (
                cause_projection.observation_depth_class,
                cause_projection.subjective_depth_class,
                cause_projection.temperature_class,
            ),
        )
        sequence_relation_traces = tuple(
            row
            for row in sequence["outcome"].artifact.trace
            if row.meaning_edge_ids
        )
        cause_relation_traces = tuple(
            row for row in cause["outcome"].artifact.trace if row.meaning_edge_ids
        )
        self.assertEqual(sequence_relation_traces, ())
        self.assertEqual(
            len(tuple(row for row in cause_relation_traces if row.role == "OBSERVATION")),
            1,
        )
        self.assertTrue(
            all(
                row.meaning_edge_ids == (cause_edges[0].edge_id,)
                and set(row.meaning_node_ids)
                == {cause_edges[0].source_node_id, cause_edges[0].target_node_id}
                and row.evidence_ids == cause_edges[0].evidence_ids
                for row in cause_relation_traces
            )
        )

    def test_step6_claim_boundary_mutations_reject_or_preserve_exact_scope(
        self,
    ) -> None:
        operators = tuple(
            row[2]
            for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
            if row[1] == "CLAIM_BOUNDARY_MUTATION"
        )
        self.assertEqual(
            operators,
            ("NEGATION", "MODALITY", "EXPERIENCER", "MATERIAL_UNRELATED"),
        )

        positive_request, negated_request = _step6_mutation_requests("NEGATION")
        assert negated_request is not None
        positive = _run_step6_mutation_request(positive_request)
        negated = _run_step6_mutation_request(negated_request)
        self._assert_step6_generated(positive)
        self._assert_step6_unavailable(
            negated,
            "lexical_role_negated_desire_conflict",
            compiler_calls=0,
        )
        positive_projection = positive["captured"]["projection"]
        direction_candidates = tuple(
            row
            for row in positive_projection.interpretation_candidates
            if row.semantic_operator.value == "PRESENT_DIRECTION"
        )
        self.assertEqual(len(direction_candidates), 1)
        self.assertIn("polarity:positive", direction_candidates[0].required_qualifiers)
        self.assertIn("modality:wish", direction_candidates[0].required_qualifiers)
        self.assertEqual(
            len(
                tuple(
                    row
                    for row in positive_projection.observation_contributions
                    if row.semantic_operator.value == "PRESENT_DIRECTION"
                    and row.retention == "REQUIRED"
                )
            ),
            1,
        )
        self.assertIsNone(negated["outcome"].meaning_graph)

        fact_request, uncertain_request = _step6_mutation_requests("MODALITY")
        assert uncertain_request is not None
        fact = _run_step6_mutation_request(fact_request)
        uncertain = _run_step6_mutation_request(uncertain_request)
        self._assert_step6_generated(fact)
        self._assert_step6_generated(uncertain)
        fact_capture = fact["captured"]
        uncertain_capture = uncertain["captured"]
        fact_projection = fact_capture["projection"]
        uncertain_projection = uncertain_capture["projection"]

        def required_memo_burden_candidate(captured: dict[str, object]):
            projection = captured["projection"]
            rows = tuple(
                row
                for row in projection.interpretation_candidates
                if row.semantic_operator.value == "PRESENT_BURDEN"
                and _step6_evidence_paths(captured, row.evidence_refs)
                == (("memo", -1),)
            )
            self.assertEqual(len(rows), 1)
            return rows[0]

        fact_burden = required_memo_burden_candidate(fact_capture)
        uncertain_burden = required_memo_burden_candidate(uncertain_capture)
        self.assertEqual(fact_burden.candidate_kind, uncertain_burden.candidate_kind)
        self.assertEqual(fact_burden.semantic_operator, uncertain_burden.semantic_operator)
        self.assertEqual(fact_burden.relation_operator, uncertain_burden.relation_operator)
        self.assertEqual(
            set(fact_burden.required_qualifiers)
            - set(uncertain_burden.required_qualifiers),
            {"modality:fact"},
        )
        self.assertEqual(
            set(uncertain_burden.required_qualifiers)
            - set(fact_burden.required_qualifiers),
            {"modality:uncertain"},
        )

        self.assertEqual(
            _step6_ref_shape(fact_capture, fact_burden.argument_bindings[0].semantic_ref),
            _step6_ref_shape(
                uncertain_capture,
                uncertain_burden.argument_bindings[0].semantic_ref,
            ),
        )
        self.assertEqual(fact_burden.argument_bindings[0].role.value, "PRIMARY")
        self.assertEqual(uncertain_burden.argument_bindings[0].role.value, "PRIMARY")
        self.assertEqual(
            tuple(
                sorted(
                    _step6_owner_shape(fact_capture, row.owner_id)
                    for row in fact_capture["grounded_graph"].owner_dispositions
                )
            ),
            tuple(
                sorted(
                    _step6_owner_shape(uncertain_capture, row.owner_id)
                    for row in uncertain_capture["grounded_graph"].owner_dispositions
                )
            ),
        )
        self.assertEqual(
            tuple(
                sorted(
                    _step6_node_shape(fact_capture, row)
                    for row in fact_capture["grounded_graph"].nodes
                )
            ),
            tuple(
                sorted(
                    _step6_node_shape(uncertain_capture, row)
                    for row in uncertain_capture["grounded_graph"].nodes
                )
            ),
        )
        self.assertEqual(
            tuple(
                sorted(
                    _step6_candidate_shape(fact_capture, row)
                    for row in fact_projection.interpretation_candidates
                    if row is not fact_burden
                )
            ),
            tuple(
                sorted(
                    _step6_candidate_shape(uncertain_capture, row)
                    for row in uncertain_projection.interpretation_candidates
                    if row is not uncertain_burden
                )
            ),
        )
        self.assertEqual(
            tuple(
                sorted(
                    _step6_claim_shape(
                        fact_capture,
                        row,
                        include_targets=False,
                    )
                    for row in fact_projection.subjective_claims
                )
            ),
            tuple(
                sorted(
                    _step6_claim_shape(
                        uncertain_capture,
                        row,
                        include_targets=False,
                    )
                    for row in uncertain_projection.subjective_claims
                )
            ),
        )
        self.assertEqual(
            (
                fact_projection.observation_depth_class,
                fact_projection.subjective_depth_class,
                fact_projection.temperature_class,
                len(fact_projection.meaning_field.entries),
                len(fact_projection.ordered_observation_refs),
                len(fact_projection.ordered_subjective_refs),
            ),
            (
                uncertain_projection.observation_depth_class,
                uncertain_projection.subjective_depth_class,
                uncertain_projection.temperature_class,
                len(uncertain_projection.meaning_field.entries),
                len(uncertain_projection.ordered_observation_refs),
                len(uncertain_projection.ordered_subjective_refs),
            ),
        )
        self.assertEqual(_step6_trace_spine(fact), _step6_trace_spine(uncertain))
        fact_nuclei = tuple(
            row
            for row in fact_capture["grounded_plan"].nuclei
            if row.retention == "required" and row.source_fields == ("memo",)
        )
        uncertain_nuclei = tuple(
            row
            for row in uncertain_capture["grounded_plan"].nuclei
            if row.retention == "required" and row.source_fields == ("memo",)
        )
        self.assertEqual(len(fact_nuclei), 1)
        self.assertEqual(len(uncertain_nuclei), 1)
        fact_frame = fact_nuclei[0].semantic_frame
        uncertain_frame = uncertain_nuclei[0].semantic_frame
        self.assertEqual((fact_frame.modality, uncertain_frame.modality), ("fact", "uncertain"))
        self.assertEqual(
            set(uncertain_frame.attribute_codes) - set(fact_frame.attribute_codes),
            {"operator:uncertainty", "semantic_role:limiting_unknown"},
        )
        self.assertEqual(
            set(fact_frame.attribute_codes) - set(uncertain_frame.attribute_codes),
            set(),
        )
        self.assertEqual(
            replace(
                uncertain_frame,
                modality=fact_frame.modality,
                attribute_codes=fact_frame.attribute_codes,
            ),
            fact_frame,
        )
        self.assertFalse(fact["outcome"].artifact.visible_unknowns)
        self.assertFalse(uncertain["outcome"].artifact.visible_unknowns)
        self.assertFalse(
            any(
                "future" in qualifier.lower()
                for projection in (fact_projection, uncertain_projection)
                for row in projection.interpretation_candidates
                for qualifier in row.required_qualifiers
            )
        )

        self_request, other_request = _step6_mutation_requests("EXPERIENCER")
        assert other_request is not None
        self_owned = _run_step6_mutation_request(self_request)
        other_owned = _run_step6_mutation_request(other_request)
        self._assert_step6_generated(self_owned)
        self._assert_step6_unavailable(
            other_owned,
            "current_experiencer_or_time_scope_unsupported",
            compiler_calls=0,
        )
        self.assertTrue(
            all(
                "actor:current_user" in row.required_qualifiers
                for row in self_owned["captured"]["projection"].interpretation_candidates
            )
        )
        self.assertIsNone(other_owned["outcome"].meaning_graph)
        self.assertIsNone(other_owned["outcome"].artifact)

        material_request, appended_request = _step6_mutation_requests(
            "MATERIAL_UNRELATED"
        )
        assert appended_request is not None
        material = _run_step6_mutation_request(material_request)
        appended = _run_step6_mutation_request(appended_request)
        self._assert_step6_generated(material)
        self._assert_step6_generated(appended)
        material_capture = material["captured"]
        appended_capture = appended["captured"]

        def finite_multiset_addition(before_rows, after_rows) -> tuple:
            remaining = list(after_rows)
            for row in before_rows:
                self.assertIn(row, remaining)
                remaining.remove(row)
            return tuple(remaining)

        def normalize_memo_owner_growth(value):
            if isinstance(value, tuple):
                if (
                    len(value) == 9
                    and value[0] == "REQUIRED"
                    and value[5]
                    and set(value[5]) == {("memo", -1)}
                ):
                    value = (*value[:5], (("memo", -1),), "MEMO_CLAIMS", *value[7:])
                return tuple(normalize_memo_owner_growth(row) for row in value)
            return value

        material_memo_owners = tuple(
            row
            for row in material_capture["grounded_graph"].owner_dispositions
            if set(_step6_evidence_paths(material_capture, row.evidence_ids))
            == {("memo", -1)}
            and row.owner_class.value == "REQUIRED"
        )
        appended_memo_owners = tuple(
            row
            for row in appended_capture["grounded_graph"].owner_dispositions
            if set(_step6_evidence_paths(appended_capture, row.evidence_ids))
            == {("memo", -1)}
            and row.owner_class.value == "REQUIRED"
        )
        self.assertEqual(len(material_memo_owners), 1)
        self.assertEqual(len(appended_memo_owners), 1)
        self.assertEqual(
            (
                len(material_memo_owners[0].evidence_ids),
                len(material_memo_owners[0].visible_claim_refs),
            ),
            (1, 1),
        )
        self.assertEqual(
            (
                len(appended_memo_owners[0].evidence_ids),
                len(appended_memo_owners[0].visible_claim_refs),
            ),
            (2, 2),
        )

        material_memo_nodes = tuple(
            normalize_memo_owner_growth(_step6_node_shape(material_capture, row))
            for row in material_capture["grounded_graph"].nodes
            if _step6_evidence_paths(material_capture, row.evidence_ids)
            == (("memo", -1),)
        )
        appended_memo_nodes = tuple(
            normalize_memo_owner_growth(_step6_node_shape(appended_capture, row))
            for row in appended_capture["grounded_graph"].nodes
            if _step6_evidence_paths(appended_capture, row.evidence_ids)
            == (("memo", -1),)
        )
        added_nodes = finite_multiset_addition(
            material_memo_nodes,
            appended_memo_nodes,
        )
        self.assertEqual(len(added_nodes), 1)
        self.assertEqual(added_nodes[0][0], "action")
        material_memo_contributions = tuple(
            normalize_memo_owner_growth(
                _step6_contribution_shape(material_capture, row)
            )
            for row in material_capture["projection"].observation_contributions
            if _step6_evidence_paths(material_capture, row.evidence_refs)
            == (("memo", -1),)
        )
        appended_memo_contributions = tuple(
            normalize_memo_owner_growth(
                _step6_contribution_shape(appended_capture, row)
            )
            for row in appended_capture["projection"].observation_contributions
            if _step6_evidence_paths(appended_capture, row.evidence_refs)
            == (("memo", -1),)
        )
        added_contributions = finite_multiset_addition(
            material_memo_contributions,
            appended_memo_contributions,
        )
        self.assertEqual(len(added_contributions), 1)
        added_contribution = next(
            row
            for row in appended_capture["projection"].observation_contributions
            if row.semantic_operator.value == "PRESENT_ACTUAL_OUTPUT"
        )
        self.assertEqual(
            (
                added_contribution.contribution_kind.value,
                added_contribution.semantic_operator.value,
                added_contribution.relation_operator.value,
                added_contribution.retention,
            ),
            (
                "OBSERVE_ACTUAL_OUTPUT",
                "PRESENT_ACTUAL_OUTPUT",
                "NO_RELATION_CLAIM",
                "REQUIRED",
            ),
        )
        material_memo_trace = tuple(
            row
            for row in _step6_trace_spine(material)
            if row[0] == "OBSERVATION" and row[5] == (("memo", -1),)
        )
        appended_memo_trace = tuple(
            row
            for row in _step6_trace_spine(appended)
            if row[0] == "OBSERVATION" and row[5] == (("memo", -1),)
        )
        added_trace = finite_multiset_addition(
            material_memo_trace,
            appended_memo_trace,
        )
        self.assertEqual(len(added_trace), 1)
        self.assertEqual(added_trace[0][3], ("action",))
        for run in (material, appended):
            projection = run["captured"]["projection"]
            graph = run["captured"]["grounded_graph"]
            self.assertEqual(graph.edges, ())
            self.assertTrue(
                all(
                    row.relation_operator.value == "NO_RELATION_CLAIM"
                    for row in projection.interpretation_candidates
                )
            )
            self.assertFalse(
                any(
                    row.node_kind.lower()
                    in {"personality", "diagnosis", "hidden_intent", "future"}
                    for row in graph.nodes
                )
            )

    def test_step6_subjectivity_mutations_preserve_strength_and_reject_person_target(
        self,
    ) -> None:
        operators = tuple(
            row[2]
            for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
            if row[1] == "SUBJECTIVITY_MUTATION"
        )
        self.assertEqual(
            operators,
            ("SOURCE_STRENGTH", "DISCOMFORT_PERSON_TARGET"),
        )

        weak_request, strong_request = _step6_mutation_requests("SOURCE_STRENGTH")
        assert strong_request is not None
        weak = _run_step6_mutation_request(weak_request)
        strong = _run_step6_mutation_request(strong_request)
        self._assert_step6_generated(weak)
        self._assert_step6_generated(strong)
        weak_capture = weak["captured"]
        strong_capture = strong["captured"]
        weak_projection = weak_capture["projection"]
        strong_projection = strong_capture["projection"]
        self.assertEqual(
            _step6_projection_shape(weak_capture),
            _step6_projection_shape(strong_capture),
        )
        self.assertEqual(_step6_trace_spine(weak), _step6_trace_spine(strong))
        self.assertEqual(
            (
                weak["outcome"].artifact.observation,
                weak["outcome"].artifact.reception,
                tuple(row.text for row in weak["outcome"].artifact.visible_unknowns),
            ),
            (
                strong["outcome"].artifact.observation,
                strong["outcome"].artifact.reception,
                tuple(row.text for row in strong["outcome"].artifact.visible_unknowns),
            ),
        )
        self.assertNotEqual(
            weak_capture["source"].envelope.envelope_id,
            strong_capture["source"].envelope.envelope_id,
        )
        self.assertNotEqual(
            weak_capture["grounded_graph"].graph_id,
            strong_capture["grounded_graph"].graph_id,
        )
        self.assertNotEqual(weak_projection.projection_id, strong_projection.projection_id)
        self.assertNotEqual(
            weak["outcome"].artifact.artifact_id,
            strong["outcome"].artifact.artifact_id,
        )
        weak_raw = copy.deepcopy(weak_request.current_input_bundle.raw_current_input)
        strong_raw = copy.deepcopy(strong_request.current_input_bundle.raw_current_input)
        weak_raw["id"] = "REQUEST_ID"
        strong_raw["id"] = "REQUEST_ID"
        weak_raw["emotion_details"][0]["strength"] = "MUTATED_STRENGTH"
        strong_raw["emotion_details"][0]["strength"] = "MUTATED_STRENGTH"
        self.assertEqual(weak_raw, strong_raw)

        def literal_hashes(captured: dict[str, object]) -> dict[tuple[str, int], str]:
            return {
                (row.field_path, row.element_index): row.literal_sha256
                for row in captured["source"].evidence_refs
            }

        weak_hashes = literal_hashes(weak_capture)
        strong_hashes = literal_hashes(strong_capture)
        self.assertEqual(set(weak_hashes), set(strong_hashes))
        self.assertEqual(
            {
                field
                for field in weak_hashes
                if weak_hashes[field] != strong_hashes[field]
            },
            {("emotion_details.0.strength", 0)},
        )
        self.assertEqual(
            tuple(
                (
                    row.asserted_subjective_proposition.affect_category,
                    row.asserted_subjective_proposition.affect_intensity,
                    row.subjective_mode,
                    row.user_fact_effect,
                )
                for row in weak_projection.subjective_claims
            ),
            tuple(
                (
                    row.asserted_subjective_proposition.affect_category,
                    row.asserted_subjective_proposition.affect_intensity,
                    row.subjective_mode,
                    row.user_fact_effect,
                )
                for row in strong_projection.subjective_claims
            ),
        )

        valid_request, no_second_request = _step6_mutation_requests(
            "DISCOMFORT_PERSON_TARGET"
        )
        self.assertIsNone(no_second_request)
        valid = _run_step6_mutation_request(valid_request)
        self._assert_step6_generated(valid)
        valid_capture = valid["captured"]
        projection = valid_capture["projection"]
        graph = valid_capture["grounded_graph"]
        parent_plan = valid_capture["parent_plan"]
        cmee_contracts_module.validate_stage1_projection(
            projection,
            grounded_graph=graph,
            parent_plan=parent_plan,
        )
        affective_claims = tuple(
            row
            for row in projection.subjective_claims
            if row.subjective_mode.value == "AFFECTIVE_RESPONSE"
        )
        self.assertEqual(len(affective_claims), 1)
        original_claim = affective_claims[0]
        original_proposition = original_claim.asserted_subjective_proposition
        self.assertIsNotNone(original_proposition.affect_category)
        self.assertNotEqual(
            original_proposition.affect_category.value,
            "DISCOMFORT",
        )
        self.assertTrue(original_proposition.response_object_refs)
        node_by_id = {row.node_id: row for row in graph.nodes}

        def response_node(ref: str):
            ref_kind, payload = ref.split(":", 1)
            self.assertEqual(ref_kind, "node")
            return node_by_id[payload.split("@", 1)[0]]

        response_nodes = tuple(
            response_node(ref) for ref in original_proposition.response_object_refs
        )
        self.assertTrue(
            all(row.node_kind not in {"event", "action", "change"} for row in response_nodes)
        )
        tampered_proposition = replace(
            original_proposition,
            affect_category=cmee_contracts_module.AffectCategory.DISCOMFORT,
        )
        tampered_claim = replace(
            original_claim,
            subjective_claim_id="",
            asserted_subjective_proposition=tampered_proposition,
        )
        tampered_claim = replace(
            tampered_claim,
            subjective_claim_id=cmee_contracts_module.recompute_stage1_identity(
                tampered_claim
            ),
        )
        self.assertNotEqual(
            tampered_claim.subjective_claim_id,
            original_claim.subjective_claim_id,
        )
        self.assertEqual(
            replace(
                tampered_claim,
                subjective_claim_id=original_claim.subjective_claim_id,
                asserted_subjective_proposition=replace(
                    tampered_proposition,
                    affect_category=original_proposition.affect_category,
                ),
            ),
            original_claim,
        )
        tampered_claims = tuple(
            tampered_claim if row is original_claim else row
            for row in projection.subjective_claims
        )
        tampered_order = tuple(
            tampered_claim.subjective_claim_id
            if ref == original_claim.subjective_claim_id
            else ref
            for ref in projection.ordered_subjective_refs
        )
        tampered_projection = replace(
            projection,
            projection_id="",
            subjective_claims=tampered_claims,
            ordered_subjective_refs=tampered_order,
        )
        tampered_projection = replace(
            tampered_projection,
            projection_id=cmee_contracts_module.recompute_stage1_identity(
                tampered_projection
            ),
        )
        self.assertNotEqual(tampered_projection.projection_id, projection.projection_id)
        cmee_contracts_module.validate_stage1_identity(tampered_claim)
        cmee_contracts_module.validate_stage1_identity(tampered_projection)
        with (
            patch.object(
                emlis_v1a_module,
                "compile_stage1_response",
                side_effect=AssertionError("tamper validation compiled"),
            ) as compiler,
            patch.object(
                emlis_v1a_module,
                "compose_emlis_conversation_candidate",
                side_effect=AssertionError("tamper validation composed"),
            ) as composer,
            patch.object(
                stage1_response_module,
                "build_stage1_realization_candidate_set",
                side_effect=AssertionError("tamper validation realized"),
            ) as realizer,
            patch.object(
                stage1_response_module,
                "select_stage1_realization_candidate",
                side_effect=AssertionError("tamper validation selected"),
            ) as selector,
        ):
            with self.assertRaisesRegex(
                cmee_contracts_module.CMEEStage1ContractError,
                "^stage1_subjective_discomfort_target_invalid$",
            ):
                cmee_contracts_module.validate_stage1_projection(
                    tampered_projection,
                    grounded_graph=graph,
                    parent_plan=parent_plan,
                )
        self.assertEqual(compiler.call_count, 0)
        self.assertEqual(composer.call_count, 0)
        self.assertEqual(realizer.call_count, 0)
        self.assertEqual(selector.call_count, 0)
        self.assertFalse(
            any(
                row.emlis_stage1_extension is not None
                and row.emlis_stage1_extension.subjective_claim_ref
                == tampered_claim.subjective_claim_id
                for row in valid["outcome"].artifact.trace
            )
        )

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
