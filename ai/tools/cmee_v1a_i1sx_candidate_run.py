#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the disabled CMEE V1-A private Product-Read packet.

Stdout is body-free. Full synthetic input and generated text are written only
when ``--body-full-output`` is explicitly supplied; that file is private and
must not be committed.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping


AI_ROOT = Path(__file__).resolve().parents[1]
AI_INFERENCE = AI_ROOT / "services" / "ai_inference"
if str(AI_INFERENCE) not in sys.path:
    sys.path.insert(0, str(AI_INFERENCE))

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle  # noqa: E402
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine  # noqa: E402
from cocolon_meaning_experience_engine.contracts import (  # noqa: E402
    EpistemicState,
    RouteBDisposition,
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


def _structural_trace_valid(outcome: object) -> bool:
    artifact = getattr(outcome, "artifact", None)
    graph = getattr(outcome, "meaning_graph", None)
    if getattr(getattr(outcome, "status", None), "value", "") != "LIMITED":
        return False
    if artifact is None or graph is None or getattr(outcome, "automatic_progression", True):
        return False
    owner_ids = tuple(row.owner_id for row in graph.owner_dispositions)
    if owner_ids != graph.required_owner_refs + graph.active_optional_owner_refs:
        return False
    if len(owner_ids) != len(set(owner_ids)):
        return False
    roles = tuple(row.role for row in artifact.trace)
    if (
        len(roles) < 3
        or roles[-2:] != ("UNKNOWN", "RECEPTION")
        or any(role != "OBSERVATION" for role in roles[:-2])
        or roles.count("UNKNOWN") != 1
        or roles.count("RECEPTION") != 1
    ):
        return False
    if not roles[:-2] or not all(row.evidence_ids for row in artifact.trace):
        return False
    unknown = artifact.trace[-2]
    if (
        unknown.duty_id != "PRESERVE_EVIDENCE_BOUND_UNKNOWN"
        or unknown.operation != "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
        or unknown.meaning_node_ids
        or unknown.meaning_edge_ids
        or not unknown.constrained_by_owner_ids
    ):
        return False
    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    disposition = {row.owner_id: row for row in graph.owner_dispositions}
    if any(owner_id not in disposition for owner_id in unknown.constrained_by_owner_ids):
        return False
    for trace in artifact.trace:
        if trace.role in {"OBSERVATION", "RECEPTION"} and not trace.meaning_node_ids:
            return False
        for node_id in trace.meaning_node_ids:
            node = nodes.get(node_id)
            owner_disposition = disposition.get(node.owner_id) if node else None
            if (
                node is None
                or owner_disposition is None
                or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or owner_disposition.disposition
                is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                or node_id not in owner_disposition.visible_claim_refs
            ):
                return False
        for edge_id in trace.meaning_edge_ids:
            edge = edges.get(edge_id)
            owner_disposition = disposition.get(edge.owner_id) if edge else None
            if (
                edge is None
                or owner_disposition is None
                or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or owner_disposition.disposition
                is not RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                or edge_id not in owner_disposition.visible_claim_refs
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
            "structural_trace_valid_is_observation_only": True,
            "human_axes_required": list(PRODUCT_READ_AXES),
            "common_blocker_or_major_required": 0,
            "set_level_reread_required": True,
        },
    }
    body_free: dict[str, Any] = {
        "packet_id": full["packet_id"],
        "case_count": len(body_free_cases),
        "limited_count": sum(item["status"] == "LIMITED" for item in body_free_cases),
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
