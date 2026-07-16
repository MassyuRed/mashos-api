# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 6 Discourse Graph Planner acceptance and negative tests."""

from copy import deepcopy
from dataclasses import replace
import inspect
import json
from pathlib import Path

import emlis_ai_discourse_graph_planner_v3 as discourse_module
from emlis_ai_content_selection_v3 import build_content_selection_plan
from emlis_ai_discourse_graph_planner_v3 import (
    MAX_DISCOURSE_CANDIDATES,
    build_discourse_graph_plans,
    validate_discourse_graph_plan_set,
)
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_nls_v3_artifact_contract import validate_discourse_plan
from emlis_ai_observation_stage_context_v3 import build_observation_stage_context
from emlis_ai_semantic_obligation_inventory_v3 import (
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)


_AI_ROOT = Path(__file__).resolve().parents[1]
_BATCH_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
)


def _samples() -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _sample(case_id: str) -> dict[str, object]:
    return next(row for row in _samples() if row["case_id"] == case_id)


def _build(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    grounded = build_grounded_observation_plan(
        current_input, evidence_spans=spans
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=current_input,
    )
    snapshot = build_grounded_source_snapshot(
        grounded,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    inventory = build_semantic_obligation_inventory(snapshot)
    content = build_content_selection_plan(inventory)
    plans = build_discourse_graph_plans(inventory, content)
    return inventory, content, plans


def _section_groups(plan, role: str):
    return [
        row for row in plan["sentence_groups"]
        if row["section_role"] == role
    ]


def test_s6_batch001_all_100_are_strict_bounded_and_semantically_ordered() -> None:
    samples = _samples()
    assert len(samples) == 100
    for sample in samples:
        inventory, content, plan_set = _build(sample["input"])
        assert not validate_discourse_graph_plan_set(
            plan_set,
            inventory_result=inventory,
            content_plan=content,
        ), sample["case_id"]
        assert 1 <= len(plan_set.plans) <= MAX_DISCOURSE_CANDIDATES
        signatures = [row["structural_signature"] for row in plan_set.plans]
        assert len(signatures) == len(set(signatures))

        annotation = sample["coverage"]["structural_variation"]
        if annotation["merge_split_eligible"]:
            assert plan_set.capability.merge_split_variation, sample["case_id"]
        if annotation["minimal_single_structure_expected"]:
            assert len(plan_set.plans) == 1, sample["case_id"]
        if annotation["order_variation_eligible"]:
            assert (
                plan_set.capability.order_variation
                or "BOUND_RECEPTION_TARGET_ORDER_FIXED"
                in plan_set.capability.reason_codes
            ), sample["case_id"]
        if annotation["reception_position_variation_eligible"]:
            assert not plan_set.capability.reception_position_variation
            assert (
                "SINGLE_BOUND_RECEPTION_POSITION"
                in plan_set.capability.reason_codes
            )

        for plan in plan_set.plans:
            assert not validate_discourse_plan(
                plan,
                content_plan=content,
                obligation_ledger=inventory.ledger,
            ), sample["case_id"]
            observation_groups = _section_groups(plan, "observation")
            node_by_id = {row["node_id"]: row for row in plan["nodes"]}
            reception_targets = {
                target
                for row in plan["nodes"]
                if row["section_role"] == "reception"
                for target in row["antecedent_node_ids"]
            }
            assert reception_targets
            assert reception_targets <= set(
                observation_groups[-1]["node_ids"][-len(reception_targets) :]
            )
            group_index = {
                node_id: index
                for index, group in enumerate(observation_groups)
                for node_id in group["node_ids"]
            }
            for edge in plan["edges"]:
                if edge["type"] == "contrasts_with":
                    assert abs(
                        group_index[edge["from"]]
                        - group_index[edge["to"]]
                    ) <= 1
                if edge["type"] == "preserves_unknown_before":
                    assert node_by_id[edge["from"]]["clause_role"] == (
                        "unknown_boundary"
                    )
                    assert group_index[edge["from"]] <= group_index[edge["to"]]


def test_s6_input_swap_changes_content_derived_signatures() -> None:
    first = _build(_sample("nls3s_b001_0093")["input"])[2]
    second = _build(_sample("nls3s_b001_0098")["input"])[2]
    assert {
        row["structural_signature"] for row in first.plans
    } != {
        row["structural_signature"] for row in second.plans
    }


def test_s6_recomputes_candidate_set_and_rejects_coherent_mutation() -> None:
    inventory, content, plan_set = _build(
        _sample("nls3s_b001_0064")["input"]
    )
    mutated_plan = deepcopy(plan_set.plans[0])
    mutated_plan["nodes"][0]["merge_eligible"] = not mutated_plan["nodes"][0][
        "merge_eligible"
    ]
    forged = replace(
        plan_set,
        plans=(mutated_plan, *plan_set.plans[1:]),
    )
    assert "DISCOURSE_PLAN_SET_MISMATCH" in (
        validate_discourse_graph_plan_set(
            forged,
            inventory_result=inventory,
            content_plan=content,
        )
    )

    missing_receive = deepcopy(plan_set.plans[0])
    missing_receive["edges"] = [
        row for row in missing_receive["edges"] if row["type"] != "receives"
    ]
    assert validate_discourse_plan(
        missing_receive,
        content_plan=content,
        obligation_ledger=inventory.ledger,
    )


def test_s6_has_no_fixture_or_surface_generation_cues() -> None:
    source = inspect.getsource(discourse_module)
    for forbidden in (
        "case_id",
        "family_id",
        "batch_id",
        "expected_sentence",
        "final_text",
        "emlis_ai_grounded_reception_content_plan_v2",
    ):
        assert forbidden not in source
    assert "target_to_source" in source
    assert "DISCOURSE_RELATION_DIRECTION_UNSUPPORTED" in source
