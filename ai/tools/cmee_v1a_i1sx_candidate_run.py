#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the disabled CMEE V1-A private Product-Read packet.

Stdout is body-free. Full synthetic input and generated text are written only
when ``--body-full-output`` is explicitly supplied; that file is private and
must not be committed.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Mapping


AI_ROOT = Path(__file__).resolve().parents[1]
AI_INFERENCE = AI_ROOT / "services" / "ai_inference"
if str(AI_INFERENCE) not in sys.path:
    sys.path.insert(0, str(AI_INFERENCE))

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle  # noqa: E402
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine  # noqa: E402
from cocolon_meaning_experience_engine.contracts import (  # noqa: E402
    CMEE_COMMON_GUARD_PROOF_VERSION,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
    CMEE_TERMINAL_GENERATED_DISABLED,
    CommonGuardProof,
    CommonGuardResultProof,
    EmlisStage1PositiveTraceExtension,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationArtifactBundle,
    GroundedMeaningGraph,
    OwnerClass,
    RouteBDisposition,
    VisibleUnitTrace,
    VisibleUnknownUnit,
)
from cocolon_meaning_experience_engine.emlis_v1a import (  # noqa: E402
    COMMON_GUARD_STABILIZATION_CORE_ID,
    COMMON_GUARD_STABILIZATION_PHASE,
    COMMON_GUARD_STABILIZATION_REPORT_NAME,
    EXPECTED_COMMON_GUARD_IDS,
    REALIZER_CONTRACT_IDS,
    TRUST_POLICY_IDS,
    _common_guard_proof_id,
)


EXACT8: tuple[tuple[str, str, str, str, str], ...] = (
    ("SX-01", "疲れているけれど、少し整えたい気持ちもある。", "生活", "自己理解", "medium"),
    ("SX-02", "続けたいのに限界が近い感じがある。", "仕事", "不安", "medium"),
    (
        "SX-03",
        "今日は仕事の話を受けたあと、納得したい気持ちと引っかかりが残っている。",
        "仕事",
        "自己理解",
        "medium",
    ),
    (
        "SX-04",
        "だるいし何もしたくない。相談したいけど迷惑かもしれない。",
        "健康",
        "不安",
        "strong",
    ),
    ("SX-05", "環境を変えたいけど変えられなくて疲れた。", "生活", "不安", "medium"),
    (
        "SX-06",
        "変えたいのに動けなくて疲れた。ずっとこのままなのが不安で、どうしたらいいのか考えている。",
        "生活",
        "不安",
        "strong",
    ),
    (
        "SX-07",
        "この職場でやっていけるか不安。でも、続けられる形は探したい。",
        "仕事",
        "不安",
        "medium",
    ),
    (
        "SX-08",
        "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
        "生活",
        "平穏",
        "medium",
    ),
)

PRODUCT_READ_AXES = (
    "PRIMARY_MEANING_RETAINED",
    "RELATION_DIRECTION_CORRECT",
    "NO_CAUSE_PERSONALITY_DIAGNOSIS_PROMOTION",
    "UNKNOWN_BOUNDARY_PRESERVED",
    "SELF_DENIAL_NOT_ADOPTED_OR_AMPLIFIED",
    "BOUND_EMLIS_RECEPTION",
    "SECTION_SEMANTIC_DISTINCTNESS",
    "NATURAL_NON_REPETITIVE_SURFACE",
    "DISTRIBUTION_NOT_OVERCONCENTRATED",
    "DEPTH_PROPORTIONAL",
    "NO_FALSE_UNDERSTANDING_COMPLETION",
    "IMMEDIATE_OBSERVATION_FEELS_READ",
)
PRIVATE_OUTPUT_ROOT = Path(
    os.environ.get("CMEE_PRIVATE_OUTPUT_ROOT", "/tmp/cocolon-cmee-v1a-private")
).resolve()


def _raw(case_id: str, memo: str, category: str, emotion: str, strength: str) -> dict[str, Any]:
    return {
        "id": f"cmee-i1sx-{case_id.lower()}",
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }


def _valid_ref_tuple(value: object, *, allow_empty: bool = False) -> bool:
    return (
        type(value) is tuple
        and (allow_empty or bool(value))
        and all(type(ref) is str and bool(ref) for ref in value)
        and len(value) == len(set(value))
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _structural_trace_valid(outcome: object) -> bool:
    artifact = getattr(outcome, "artifact", None)
    graph = getattr(outcome, "meaning_graph", None)
    status = getattr(getattr(outcome, "status", None), "value", "")
    if status not in {"GENERATED", "LIMITED"}:
        return False
    if (
        type(artifact) is not GenerationArtifactBundle
        or type(graph) is not GroundedMeaningGraph
        or type(artifact.plan) is not ExperiencePlan
        or type(artifact.trace) is not tuple
        or any(type(row) is not VisibleUnitTrace for row in artifact.trace)
        or type(artifact.visible_unknowns) is not tuple
        or any(
            type(row) is not VisibleUnknownUnit for row in artifact.visible_unknowns
        )
        or getattr(outcome, "terminal_state", "")
        != CMEE_TERMINAL_GENERATED_DISABLED
        or getattr(outcome, "automatic_progression", True)
    ):
        return False
    expected_lineage = (
        graph.source_envelope_id,
        graph.source_version,
        graph.obligation_version,
        graph.owner_universe_digest,
    )
    if (
        type(artifact.observation) is not str
        or not artifact.observation
        or type(artifact.reception) is not str
        or not artifact.reception
        or type(artifact.artifact_id) is not str
        or re.fullmatch(r"artifact-[0-9a-f]{24}", artifact.artifact_id) is None
        or artifact.realizer_contract_ids != REALIZER_CONTRACT_IDS
        or artifact.trust_policy_ids != TRUST_POLICY_IDS
        or (
            artifact.plan.source_envelope_id,
            artifact.plan.source_version,
            artifact.plan.obligation_version,
            artifact.plan.owner_universe_digest,
        )
        != expected_lineage
        or any(
            (
                row.source_envelope_id,
                row.source_version,
                row.obligation_version,
                row.owner_universe_digest,
            )
            != expected_lineage
            for row in artifact.trace
        )
    ):
        return False
    owner_ids = tuple(row.owner_id for row in graph.owner_dispositions)
    if owner_ids != graph.required_owner_refs + graph.active_optional_owner_refs:
        return False
    if len(owner_ids) != len(set(owner_ids)):
        return False
    roles = tuple(row.role for row in artifact.trace)
    observation_count = roles.count("OBSERVATION")
    unknown_traces = tuple(row for row in artifact.trace if row.role == "UNKNOWN")
    reception_traces = tuple(
        row for row in artifact.trace if row.role == "RECEPTION"
    )
    visible_unknowns = tuple(getattr(artifact, "visible_unknowns", ()))
    expected_status = "LIMITED" if unknown_traces else "GENERATED"
    if (
        status != expected_status
        or not 1 <= observation_count <= 5
        or not 0 <= len(unknown_traces) <= 1
        or not 1 <= len(reception_traces) <= 4
        or roles
        != (
            *("OBSERVATION" for _ in range(observation_count)),
            *("UNKNOWN" for _ in range(len(unknown_traces))),
            *("RECEPTION" for _ in range(len(reception_traces))),
        )
    ):
        return False
    visible_unit_ids = tuple(row.visible_unit_id for row in artifact.trace)
    source_sentence_ids = tuple(row.source_sentence_id for row in artifact.trace)
    if (
        visible_unit_ids != tuple(
            f"visible:{index}" for index in range(1, len(artifact.trace) + 1)
        )
        or len(visible_unit_ids) != len(set(visible_unit_ids))
        or len(source_sentence_ids) != len(set(source_sentence_ids))
    ):
        return False
    expected_source_sentence_ids = (
        *(f"cmee:observation:{index}" for index in range(1, observation_count + 1)),
        *(f"cmee:unknown:{index}" for index in range(1, len(unknown_traces) + 1)),
        *(f"cmee:reception:{index}" for index in range(1, len(reception_traces) + 1)),
    )
    if source_sentence_ids != expected_source_sentence_ids:
        return False
    if len(visible_unknowns) != len(unknown_traces):
        return False
    if (
        tuple(
            owner_id
            for trace in unknown_traces
            for owner_id in trace.constrained_by_owner_ids
        )
        != artifact.plan.visible_unknown_owner_ids
        or not set(artifact.plan.required_unknown_owner_ids).issubset(
            artifact.plan.visible_unknown_owner_ids
        )
    ):
        return False
    if any(
        unknown_trace.visible_unit_id != visible_unknown.unknown_unit_id
        or unknown_trace.source_sentence_id != visible_unknown.source_sentence_id
        or unknown_trace.source_envelope_id != visible_unknown.source_envelope_id
        or unknown_trace.source_version != visible_unknown.source_version
        or unknown_trace.obligation_version != visible_unknown.obligation_version
        or unknown_trace.owner_universe_digest
        != visible_unknown.owner_universe_digest
        or unknown_trace.duty_id != visible_unknown.duty_id
        or unknown_trace.constrained_by_owner_ids != visible_unknown.owner_ids
        or unknown_trace.evidence_ids != visible_unknown.evidence_ids
        for unknown_trace, visible_unknown in zip(
            unknown_traces, visible_unknowns, strict=True
        )
    ):
        return False
    if not all(
        _valid_ref_tuple(row.evidence_ids)
        and _valid_ref_tuple(row.meaning_node_ids, allow_empty=True)
        and _valid_ref_tuple(row.meaning_edge_ids, allow_empty=True)
        and _valid_ref_tuple(row.constrained_by_owner_ids, allow_empty=True)
        for row in artifact.trace
    ):
        return False
    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    disposition = {row.owner_id: row for row in graph.owner_dispositions}
    disposition_evidence_ids = {
        evidence_id
        for row in graph.owner_dispositions
        for evidence_id in row.evidence_ids
    }
    positive_dispositions = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for unknown in unknown_traces:
        constrained_evidence_ids = {
            evidence_id
            for owner_id in unknown.constrained_by_owner_ids
            if owner_id in disposition
            for evidence_id in disposition[owner_id].evidence_ids
        }
        allowed_unknown_evidence_owner_ids = set(
            unknown.constrained_by_owner_ids
        ) | set(artifact.plan.required_observation_owner_ids)
        allowed_unknown_evidence_ids = {
            evidence_id
            for owner_id in allowed_unknown_evidence_owner_ids
            if owner_id in disposition
            for evidence_id in disposition[owner_id].evidence_ids
        }
        if (
            unknown.duty_id != "PRESERVE_EVIDENCE_BOUND_UNKNOWN"
            or unknown.operation != "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            or unknown.meaning_node_ids
            or unknown.meaning_edge_ids
            or not unknown.constrained_by_owner_ids
            or unknown.emlis_stage1_extension is not None
            or any(
                owner_id not in disposition
                for owner_id in unknown.constrained_by_owner_ids
            )
            or any(
                disposition[owner_id].disposition
                is not RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
                and (
                    disposition[owner_id].owner_class is not OwnerClass.REQUIRED
                    or disposition[owner_id].disposition in positive_dispositions
                )
                for owner_id in unknown.constrained_by_owner_ids
            )
            or not constrained_evidence_ids.issubset(unknown.evidence_ids)
            or not set(unknown.evidence_ids).issubset(
                allowed_unknown_evidence_ids & disposition_evidence_ids
            )
        ):
            return False
    trace_position = {
        row.visible_unit_id: index for index, row in enumerate(artifact.trace)
    }
    observation_trace_ids = {
        row.visible_unit_id for row in artifact.trace if row.role == "OBSERVATION"
    }
    observation_contributions_by_trace: dict[str, tuple[str, ...]] = {}
    positive_variants: set[str] = set()
    observation_contribution_refs: list[str] = []
    reception_claim_refs: list[str] = []
    for trace in artifact.trace:
        extension = trace.emlis_stage1_extension
        semantic_evidence_ids: set[str] = set()
        if trace.role in {"OBSERVATION", "RECEPTION"}:
            if (
                type(extension) is not EmlisStage1PositiveTraceExtension
                or not (trace.meaning_node_ids or trace.meaning_edge_ids)
                or trace.constrained_by_owner_ids
            ):
                return False
            if (
                extension.schema_version
                != CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION
                or type(extension.owner_ref) is not str
                or extension.owner_ref
                != "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v1"
                or type(extension.user_fact_effect) is not int
                or extension.user_fact_effect != 0
                or type(extension.composition_variant_id) is not str
                or not extension.composition_variant_id
                or not _valid_ref_tuple(extension.contribution_refs, allow_empty=True)
                or not _valid_ref_tuple(extension.basis_trace_refs, allow_empty=True)
                or not _valid_ref_tuple(
                    extension.interpretation_candidate_refs, allow_empty=True
                )
                or not _valid_ref_tuple(
                    extension.basis_observation_contribution_refs,
                    allow_empty=True,
                )
                or not _valid_ref_tuple(extension.value_principle_refs, allow_empty=True)
            ):
                return False
            positive_variants.add(extension.composition_variant_id)
            if trace.role == "OBSERVATION":
                if (
                    trace.duty_id != artifact.plan.observation_duty_id
                    or trace.operation != "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
                    or extension.claim_domain
                    is not EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION
                    or len(extension.contribution_refs) != 1
                    or not extension.interpretation_candidate_refs
                    or extension.subjective_claim_ref is not None
                    or extension.basis_trace_refs
                    or extension.basis_observation_contribution_refs
                    or extension.value_principle_refs
                    or extension.speaker_owner is not None
                ):
                    return False
                observation_contributions_by_trace[trace.visible_unit_id] = (
                    extension.contribution_refs
                )
                observation_contribution_refs.extend(extension.contribution_refs)
            elif (
                trace.duty_id != artifact.plan.reception_duty_id
                or trace.operation != "BOUND_HUMAN_RECEPTION"
                or extension.claim_domain
                is not EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE
                or extension.contribution_refs
                or extension.interpretation_candidate_refs
                or type(extension.subjective_claim_ref) is not str
                or not extension.subjective_claim_ref
                or not extension.basis_observation_contribution_refs
                or not extension.basis_trace_refs
                or extension.speaker_owner != "EMLIS"
                or any(
                    basis_ref not in observation_trace_ids
                    or trace_position[basis_ref] >= trace_position[trace.visible_unit_id]
                    for basis_ref in extension.basis_trace_refs
                )
            ):
                return False
            else:
                reception_claim_refs.append(extension.subjective_claim_ref)
                reachable_basis_contributions = tuple(
                    contribution_ref
                    for basis_ref in extension.basis_trace_refs
                    for contribution_ref in observation_contributions_by_trace.get(
                        basis_ref, ()
                    )
                )
                if (
                    extension.basis_observation_contribution_refs
                    != reachable_basis_contributions
                ):
                    return False
        for node_id in trace.meaning_node_ids:
            node = nodes.get(node_id)
            owner_disposition = disposition.get(node.owner_id) if node else None
            if (
                node is None
                or owner_disposition is None
                or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or node.grounding_kind not in {"explicit", "user_stated_relation"}
                or not node.evidence_ids
            ):
                return False
            semantic_evidence_ids.update(node.evidence_ids)
        for edge_id in trace.meaning_edge_ids:
            edge = edges.get(edge_id)
            owner_disposition = disposition.get(edge.owner_id) if edge else None
            if (
                edge is None
                or owner_disposition is None
                or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or edge.grounding_kind != "user_stated_relation"
                or not edge.evidence_ids
            ):
                return False
            semantic_evidence_ids.update(edge.evidence_ids)
        if trace.role in {"OBSERVATION", "RECEPTION"} and set(
            trace.evidence_ids
        ) != semantic_evidence_ids:
            return False
    if len(positive_variants) != 1:
        return False
    if (
        len(observation_contribution_refs)
        != len(set(observation_contribution_refs))
        or len(reception_claim_refs) != len(set(reception_claim_refs))
    ):
        return False
    guarded_ids = tuple(
        row.source_sentence_id
        for row in artifact.trace
        if row.role == "OBSERVATION"
    )
    proof = artifact.common_guard_proof
    if (
        type(proof) is not CommonGuardProof
        or type(proof.guarded_observation_units) is not tuple
        or any(
            type(row) is not tuple
            or len(row) != 2
            or any(type(value) is not str or not value for value in row)
            for row in proof.guarded_observation_units
        )
    ):
        return False
    if tuple(
        row[0] for row in proof.guarded_observation_units
    ) != guarded_ids:
        return False
    if "\r" in artifact.observation or "\r" in artifact.reception:
        return False
    observation_lines = tuple(artifact.observation.split("\n"))
    reception_lines = tuple(artifact.reception.split("\n"))
    if (
        any(not line for line in (*observation_lines, *reception_lines))
        or artifact.observation != "\n".join(observation_lines)
        or artifact.reception != "\n".join(reception_lines)
        or len(observation_lines) != observation_count
        or len(reception_lines) != len(reception_traces)
    ):
        return False
    visible_text = (
        *observation_lines,
        *(row.text for row in visible_unknowns),
        *reception_lines,
    )
    if any(
        trace.text_sha256 != _sha256_text(text)
        for trace, text in zip(artifact.trace, visible_text, strict=True)
    ):
        return False
    expected_guarded_observation_units = tuple(
        (source_sentence_id, _sha256_text(text))
        for source_sentence_id, text in zip(
            guarded_ids,
            observation_lines,
            strict=True,
        )
    )
    if (
        proof.schema_version != CMEE_COMMON_GUARD_PROOF_VERSION
        or type(proof.proof_id) is not str
        or not proof.proof_id
        or proof.source_envelope_id != graph.source_envelope_id
        or proof.graph_id != graph.graph_id
        or proof.plan_id != artifact.plan.plan_id
        or any(
            row.artifact_common_guard_proof_ref != proof.proof_id
            for row in artifact.trace
        )
        or type(proof.guarded_observation_units) is not tuple
        or proof.guarded_observation_units != expected_guarded_observation_units
        or type(proof.guard_results) is not tuple
        or len(proof.guard_results) != len(EXPECTED_COMMON_GUARD_IDS)
        or any(
            type(row) is not CommonGuardResultProof
            or row.guard_id != expected_guard_id
            or type(row.passed) is not bool
            or row.passed is not True
            for expected_guard_id, row in zip(
                EXPECTED_COMMON_GUARD_IDS,
                proof.guard_results,
                strict=True,
            )
        )
        or proof.stabilization_report_name
        != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or proof.stabilization_phase != COMMON_GUARD_STABILIZATION_PHASE
        or proof.stabilization_core_id != COMMON_GUARD_STABILIZATION_CORE_ID
        or type(proof.stabilization_passed) is not bool
        or proof.stabilization_passed is not True
        or type(proof.common_shapes_ready) is not bool
        or proof.common_shapes_ready is not True
        or type(proof.stabilization_guard_names) is not tuple
        or proof.stabilization_guard_names != EXPECTED_COMMON_GUARD_IDS
        or type(proof.issue_codes) is not tuple
        or proof.issue_codes != ()
    ):
        return False
    if proof.proof_id != _common_guard_proof_id(
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
    ):
        return False
    return True


def run() -> tuple[dict[str, Any], dict[str, Any]]:
    engine = MeaningExperienceEngine()
    private_cases: list[dict[str, Any]] = []
    body_free_cases: list[dict[str, Any]] = []
    for case_id, memo, category, emotion, strength in EXACT8:
        raw = _raw(case_id, memo, category, emotion, strength)
        outcome = engine.generate(
            GenerationRequest(
                request_id=f"req-{case_id}",
                current_input_bundle=build_emlis_current_input_bundle(raw),
                expected_source_record_id=str(raw["id"]),
            )
        )
        structural_valid = _structural_trace_valid(outcome)
        private_cases.append(
            {
                "case_id": case_id,
                "synthetic_input_private": raw,
                "candidate_private": outcome.artifact.text if outcome.artifact else "",
                "structural_trace_valid": structural_valid,
                "review_axes": list(PRODUCT_READ_AXES),
                "human_product_read": {
                    "axis_results": None,
                    "common_severity": None,
                    "accepted": None,
                },
            }
        )
        body_free_cases.append(
            {
                "case_id": case_id,
                "status": outcome.status.value,
                "reason_codes": list(outcome.reason_codes),
                "structural_trace_valid": structural_valid,
                "artifact_present": outcome.artifact is not None,
                "visible_unit_trace_count": len(outcome.artifact.trace) if outcome.artifact else 0,
            }
        )

    artifact_count = sum(item["artifact_present"] for item in body_free_cases)
    structural_count = sum(item["structural_trace_valid"] for item in body_free_cases)
    candidate_state = (
        "GENERATED_FOR_PRODUCT_READ_DISABLED"
        if structural_count == len(EXACT8)
        else "EXACT8_GENERATION_INCOMPLETE_DISABLED"
    )
    full = {
        "packet_id": "CMEE_V1A_I1SX_TEXT_GROUNDED_PRIVATE_PRODUCT_READ_EXACT8",
        "private_body_full": True,
        "candidate_state": candidate_state,
        "cases": private_cases,
        "candidate_evaluation_not_yet_accepted": {
            "structural_trace_valid_is_observation_only": False,
            "human_axes_required": list(PRODUCT_READ_AXES),
            "common_blocker_or_major_required": 0,
            "set_level_reread_required": True,
        },
    }
    body_free: dict[str, Any] = {
        "packet_id": full["packet_id"],
        "case_count": len(body_free_cases),
        "generated_count": sum(item["status"] == "GENERATED" for item in body_free_cases),
        "limited_count": sum(item["status"] == "LIMITED" for item in body_free_cases),
        "material_unknown_case_count": sum(
            item["status"] == "LIMITED" for item in body_free_cases
        ),
        "structural_trace_valid_count": sum(item["structural_trace_valid"] for item in body_free_cases),
        "artifact_count": artifact_count,
        "observation_plus_bound_reception_trace_count": sum(
            item["structural_trace_valid"] for item in body_free_cases
        ),
        "cases": body_free_cases,
        "candidate_state": candidate_state,
        "implementation_state": "DRAFT_WIP_DISABLED",
        "route_b_contract_complete": False,
        "candidate_ready": False,
        "product_read_eligible": False,
        "exact8_acceptance_complete": False,
        "product_read_evaluated": False,
        "private_text_published": False,
        "p0_credit": 0,
        "l3i_credit": 0,
        "full_i1_credit": 0,
        "cycle001_credit": 0,
        "production_effect": 0,
        "automatic_progression": False,
    }
    return body_free, full


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body-full-output", type=Path)
    args = parser.parse_args()
    body_free, full = run()
    if args.body_full_output is not None:
        target = args.body_full_output.resolve()
        if target == PRIVATE_OUTPUT_ROOT or PRIVATE_OUTPUT_ROOT not in target.parents:
            parser.error(f"--body-full-output must be below {PRIVATE_OUTPUT_ROOT}")
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(target.parent, 0o700)
        with target.open("x", encoding="utf-8") as handle:
            os.chmod(target, 0o600)
            handle.write(json.dumps(full, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(body_free, ensure_ascii=False, sort_keys=True))
    # Candidate generation gaps are reported, not hidden by fixture tuning.
    # A complete packet is not the same thing as a successful candidate run.
    return 0 if body_free["structural_trace_valid_count"] == len(EXACT8) else 1


if __name__ == "__main__":
    raise SystemExit(main())
