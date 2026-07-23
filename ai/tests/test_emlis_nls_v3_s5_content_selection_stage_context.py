# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 5 Content Selection / Observation Stage Context acceptance tests."""

from copy import deepcopy
from dataclasses import replace
import inspect
import json
from pathlib import Path

import pytest

import emlis_ai_content_selection_v3 as content_module
from emlis_ai_content_selection_v3 import (
    ContentSelectionBuildError,
    build_content_selection_plan,
    derive_content_depth,
    validate_content_selection_policy,
)
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
    derive_content_id,
)
from emlis_ai_observation_stage_context_v3 import (
    ObservationStageContextBuildError,
    build_observation_stage_context,
)
from emlis_ai_refined_source_partition_v3 import (
    build_refined_source_partition,
    validate_refined_source_partition,
)
from emlis_ai_recovery_epoch001_source_baseline_manifest_v3 import (
    RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST,
    validate_recovery_epoch001_source_baseline_manifest,
    validate_recovery_epoch001_source_guard,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    SemanticObligationInventoryError,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
    validate_semantic_obligation_inventory,
)


_AI_ROOT = Path(__file__).resolve().parents[1]
_BATCH_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
)
_BUDGETS = {
    "minimal": {
        "observation_sentence_min": 1,
        "observation_sentence_max": 1,
        "reception_sentence_min": 1,
        "reception_sentence_max": 1,
        "total_sentence_max": 2,
    },
    "focused": {
        "observation_sentence_min": 1,
        "observation_sentence_max": 2,
        "reception_sentence_min": 1,
        "reception_sentence_max": 2,
        "total_sentence_max": 4,
    },
    "layered": {
        "observation_sentence_min": 2,
        "observation_sentence_max": 3,
        "reception_sentence_min": 1,
        "reception_sentence_max": 2,
        "total_sentence_max": 5,
    },
}
_CROSS_ROLE_DEPTH_SCHEMA = (
    "cocolon.emlis.nls_v3.cross_role_semantic_depth_equivalence.v1"
)
_CROSS_ROLE_EFFECT_SCOPE = "CONTENT_DEPTH_ONLY"
_CROSS_ROLE_DEPTH_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_DEPTH_NONINFLATION_NOT_PROVED"
)
_CROSS_ROLE_FULL_REPLAY_POSITIVE = (
    "INDEPENDENT_ROLE_LOCAL_FULL_TYPED_GRAPH_REPLAY"
)
_CROSS_ROLE_DEFAULT_GRAPH_NEGATIVE = (
    "EMPTY_WITNESS_FALSE_COLLAPSE_NEGATIVE"
)
_DEPTH_RANK = {
    "minimal": 0,
    "focused": 1,
    "layered": 2,
}


def _samples() -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def _sample(case_id: str) -> dict[str, object]:
    return next(row for row in _samples() if row["case_id"] == case_id)


def _known_input() -> dict[str, object]:
    return {
        "thought_text": "挑戦したい気持ちはあるけれど、不安も残っている。",
        "action_text": "今日は候補を一つ調べた。",
        "emotions": [{"type": "不安", "strength": "medium"}],
        "categories": ["仕事"],
    }


def _self_denial_boundary_input() -> dict[str, object]:
    return {
        "thought_text": "私は何をしてもだめだ。",
        "action_text": "それでも相談先を一つ調べた。",
        "emotions": [{"type": "悲しみ", "strength": "strong"}],
        "categories": ["人生"],
    }


def _normal_result(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    grounded = build_grounded_observation_plan(current_input, evidence_spans=spans)
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
    return stage, snapshot, build_semantic_obligation_inventory(snapshot)


def _pre_result(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    grounded = build_grounded_observation_plan(current_input, evidence_spans=spans)
    authority = TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256="a" * 64,
        permitted_stages=("pre_question_observation",),
        original_input_bundle_sha256=artifact_sha256(current_input),
        supplemental_answer_bundle_sha256=None,
    )
    stage = build_observation_stage_context(
        stage="pre_question_observation",
        original_input_bundle=current_input,
        trusted_future_authority=authority,
    )
    snapshot = build_grounded_source_snapshot(
        grounded,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=authority,
    )
    return stage, snapshot, build_semantic_obligation_inventory(snapshot)


def _legacy_reduced_supplemental(
    current_input: dict[str, object],
) -> dict[str, object]:
    """Return the connected non-isomorphic graph from the superseded positive."""

    return {
        "thought_text": current_input["thought_text"],
        "action_text": "",
        "emotions": [],
        "categories": [],
    }


def _independent_full_replay_supplemental(
    current_input: dict[str, object],
) -> dict[str, object]:
    """Create a distinct bundle whose complete role-local graph must replay."""

    supplemental = deepcopy(current_input)
    for field in ("thought_text", "action_text"):
        value = supplemental.get(field)
        if isinstance(value, str) and value:
            supplemental[field] = f" {value} "
    assert supplemental != current_input
    assert artifact_sha256(supplemental) != artifact_sha256(current_input)
    return supplemental


def _refined_result(
    current_input: dict[str, object] | None = None,
    supplemental: dict[str, object] | None = None,
):
    if current_input is None:
        current_input = _known_input()
    if supplemental is None:
        supplemental = _legacy_reduced_supplemental(current_input)
    original_spans = build_evidence_ledger(current_input)
    original_resolver = build_evidence_span_resolver(
        original_spans,
        current_input=current_input,
    )
    original_plan = build_grounded_observation_plan(
        current_input,
        evidence_spans=original_spans,
    )
    supplemental_spans = build_evidence_ledger(supplemental)
    supplemental_resolver = build_evidence_span_resolver(
        supplemental_spans,
        current_input=supplemental,
    )
    supplemental_plan = build_grounded_observation_plan(
        supplemental,
        evidence_spans=supplemental_spans,
    )
    authority = TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256="c" * 64,
        permitted_stages=("refined_observation",),
        original_input_bundle_sha256=artifact_sha256(current_input),
        supplemental_answer_bundle_sha256=artifact_sha256(supplemental),
    )
    stage = build_observation_stage_context(
        stage="refined_observation",
        original_input_bundle=current_input,
        trusted_future_authority=authority,
        supplemental_answer_bundle=supplemental,
    )
    partition = build_refined_source_partition(
        original_plan,
        original_resolver,
        supplemental_plan,
        supplemental_resolver,
        stage,
        current_input,
        supplemental,
        authority,
    )
    partition_issues = validate_refined_source_partition(
        partition,
        original_plan,
        original_resolver,
        supplemental_plan,
        supplemental_resolver,
        stage,
        current_input,
        supplemental,
        authority,
    )
    snapshot = build_grounded_source_snapshot(
        original_plan,
        original_resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=authority,
        supplemental_answer_bundle=supplemental,
        refined_source_partition=partition,
    )
    result = build_semantic_obligation_inventory(snapshot)
    plan = build_content_selection_plan(result)
    return (
        current_input,
        supplemental,
        partition,
        partition_issues,
        snapshot,
        result,
        plan,
    )

def _role_component_ids_by_kind(
    snapshot,
    source_role: str,
) -> dict[str, tuple[str, ...]]:
    return {
        component_kind: tuple(
            sorted(
                row.source_id
                for row in getattr(snapshot, field)
                if row.source_role == source_role
            )
        )
        for component_kind, field in (
            ("nucleus", "nuclei"),
            ("relation", "relations"),
            ("unknown_boundary", "unknowns"),
        )
    }


def _assert_exact_cross_role_graph_bijection(snapshot) -> None:
    """Require an exact one-to-one and onto binding of both complete graphs."""

    equivalence = snapshot.cross_role_semantic_depth_equivalence
    assert equivalence is not None
    by_role = {
        role: _role_component_ids_by_kind(snapshot, role)
        for role in ("original_input", "supplemental_answer")
    }
    original_ids = {
        source_id
        for ids in by_role["original_input"].values()
        for source_id in ids
    }
    supplemental_ids = {
        source_id
        for ids in by_role["supplemental_answer"].values()
        for source_id in ids
    }
    bindings = equivalence.component_bindings
    assert original_ids
    assert supplemental_ids
    assert len(bindings) == len(original_ids) == len(supplemental_ids)
    assert {
        row.original_source_id for row in bindings
    } == original_ids
    assert {
        row.supplemental_source_id for row in bindings
    } == supplemental_ids
    original_to_supplemental = {
        row.original_source_id: row.supplemental_source_id
        for row in bindings
    }
    original_to_supplemental_topic: dict[str, str] = {}
    supplemental_to_original_topic: dict[str, str] = {}

    def assert_mapped_topic_scope(
        original_topic_ids: tuple[str, ...],
        supplemental_topic_ids: tuple[str, ...],
    ) -> None:
        assert len(original_topic_ids) == len(supplemental_topic_ids)
        for original_topic_id, supplemental_topic_id in zip(
            original_topic_ids,
            supplemental_topic_ids,
            strict=True,
        ):
            prior_supplemental = original_to_supplemental_topic.setdefault(
                original_topic_id,
                supplemental_topic_id,
            )
            prior_original = supplemental_to_original_topic.setdefault(
                supplemental_topic_id,
                original_topic_id,
            )
            assert prior_supplemental == supplemental_topic_id
            assert prior_original == original_topic_id

    rows_by_kind = {
        "nucleus": {
            row.source_id: row for row in snapshot.nuclei
        },
        "relation": {
            row.source_id: row for row in snapshot.relations
        },
        "unknown_boundary": {
            row.source_id: row for row in snapshot.unknowns
        },
    }
    for component_kind in ("nucleus", "relation", "unknown_boundary"):
        original_kind_ids = set(
            by_role["original_input"][component_kind]
        )
        supplemental_kind_ids = set(
            by_role["supplemental_answer"][component_kind]
        )
        kind_bindings = tuple(
            row for row in bindings if row.component_kind == component_kind
        )
        assert len(kind_bindings) == len(original_kind_ids)
        assert len(kind_bindings) == len(supplemental_kind_ids)
        assert {
            row.original_source_id for row in kind_bindings
        } == original_kind_ids
        assert {
            row.supplemental_source_id for row in kind_bindings
        } == supplemental_kind_ids
        assert all(
            row.original_source_kind == component_kind
            and row.supplemental_source_kind == component_kind
            and len(row.canonical_typed_component_sha256) == 64
            for row in kind_bindings
        )
        for binding in kind_bindings:
            original_row = rows_by_kind[component_kind][
                binding.original_source_id
            ]
            supplemental_row = rows_by_kind[component_kind][
                binding.supplemental_source_id
            ]
            assert_mapped_topic_scope(
                original_row.topic_scope_ids,
                supplemental_row.topic_scope_ids,
            )
            if component_kind == "nucleus":
                assert (
                    original_row.kind,
                    original_row.allowed_claim_scope,
                    original_row.grounding_kind,
                    original_row.source_actor,
                    original_row.source_predicate_kind,
                    original_row.source_modality,
                    original_row.source_time_scope,
                    original_row.source_degree,
                    original_row.source_attribute_codes,
                    original_row.polarity,
                    original_row.modality,
                    original_row.temporal_scope,
                    original_row.referent_scope,
                    original_row.retention,
                    original_row.required,
                    original_row.forbidden_claim_codes,
                    original_row.fact_boundary,
                ) == (
                    supplemental_row.kind,
                    supplemental_row.allowed_claim_scope,
                    supplemental_row.grounding_kind,
                    supplemental_row.source_actor,
                    supplemental_row.source_predicate_kind,
                    supplemental_row.source_modality,
                    supplemental_row.source_time_scope,
                    supplemental_row.source_degree,
                    supplemental_row.source_attribute_codes,
                    supplemental_row.polarity,
                    supplemental_row.modality,
                    supplemental_row.temporal_scope,
                    supplemental_row.referent_scope,
                    supplemental_row.retention,
                    supplemental_row.required,
                    supplemental_row.forbidden_claim_codes,
                    supplemental_row.fact_boundary,
                )
            elif component_kind == "relation":
                assert (
                    original_row.source_relation_kind,
                    original_row.grounding_kind,
                    original_row.endpoint_semantic_relation,
                    original_row.relation_type,
                    original_row.relation_direction,
                    original_row.polarity,
                    original_row.modality,
                    original_row.temporal_scope,
                    original_row.retention,
                    original_row.required,
                    original_row.forbidden_claim_codes,
                ) == (
                    supplemental_row.source_relation_kind,
                    supplemental_row.grounding_kind,
                    supplemental_row.endpoint_semantic_relation,
                    supplemental_row.relation_type,
                    supplemental_row.relation_direction,
                    supplemental_row.polarity,
                    supplemental_row.modality,
                    supplemental_row.temporal_scope,
                    supplemental_row.retention,
                    supplemental_row.required,
                    supplemental_row.forbidden_claim_codes,
                )
                assert original_to_supplemental[
                    original_row.from_nucleus_id
                ] == supplemental_row.from_nucleus_id
                assert original_to_supplemental[
                    original_row.to_nucleus_id
                ] == supplemental_row.to_nucleus_id
                assert tuple(
                    original_to_supplemental[source_id]
                    for source_id in (
                        original_row
                        .semantic_restatement_unit_nucleus_ids
                    )
                ) == (
                    supplemental_row
                    .semantic_restatement_unit_nucleus_ids
                )
            else:
                assert (
                    original_row.source_dimension,
                    original_row.dimension_code,
                    original_row.surface_policy,
                    original_row.required,
                ) == (
                    supplemental_row.source_dimension,
                    supplemental_row.dimension_code,
                    supplemental_row.surface_policy,
                    supplemental_row.required,
                )
                assert tuple(
                    original_to_supplemental[source_id]
                    for source_id in original_row.affected_nucleus_ids
                ) == supplemental_row.affected_nucleus_ids
    for source_role, all_ids in (
        ("original_input", original_ids),
        ("supplemental_answer", supplemental_ids),
    ):
        assert _incident_affected_closure_ids(
            snapshot,
            source_role=source_role,
            nucleus_ids=set(by_role[source_role]["nucleus"]),
        ) == all_ids


def _incident_affected_closure_ids(
    snapshot,
    *,
    source_role: str,
    nucleus_ids: set[str],
) -> set[str]:
    """Close nucleus seeds over every incident edge and affected unknown."""

    closed = set(nucleus_ids)
    relations = tuple(
        row for row in snapshot.relations
        if row.source_role == source_role
    )
    unknowns = tuple(
        row for row in snapshot.unknowns
        if row.source_role == source_role
    )
    changed = True
    while changed:
        changed = False
        for relation in relations:
            endpoints = {
                relation.from_nucleus_id,
                relation.to_nucleus_id,
            }
            if endpoints & closed:
                expanded = endpoints | {relation.source_id}
                if not expanded <= closed:
                    closed.update(expanded)
                    changed = True
        for unknown in unknowns:
            affected = set(unknown.affected_nucleus_ids)
            if affected & closed:
                expanded = affected | {unknown.source_id}
                if not expanded <= closed:
                    closed.update(expanded)
                    changed = True
    return closed


def _codes(issues) -> set[str]:
    return {issue.code for issue in issues}


def _resign_content(value: dict[str, object]) -> None:
    value["content_plan_id"] = derive_content_id(
        "nls3cp_", value, "content_plan_id"
    )


def _resign_ledger(value: dict[str, object]) -> None:
    value["ledger_id"] = derive_content_id("nls3obl_", value, "ledger_id")


def _body_free_input_matching(predicate):
    for row in _samples():
        _stage, snapshot, result = _normal_result(row["input"])
        plan = build_content_selection_plan(result)
        if predicate(snapshot, result, plan):
            return deepcopy(row["input"])
    raise AssertionError("body_free_semantic_input_unavailable")


def _raises_build_code(call, expected: str) -> None:
    try:
        call()
    except ContentSelectionBuildError as exc:
        assert exc.code == expected, (expected, exc.code, str(exc))
    else:
        raise AssertionError(f"expected {expected}")


def test_s5_stage_context_is_explicit_body_free_and_future_authority_bound() -> None:
    current_input = _known_input()
    normal = build_observation_stage_context(
        stage="normal_observation", original_input_bundle=current_input
    )
    assert normal == {
        "schema_version": "cocolon.emlis.nls_v3.observation_stage_context.v1",
        "stage": "normal_observation",
        "original_input_bundle_sha256": artifact_sha256(current_input),
        "question_need_decision_sha256": None,
        "supplemental_answer_bundle_sha256": None,
        "allowed_source_roles": ["original_input"],
        "body_free": True,
    }
    assert current_input["thought_text"] not in str(normal)
    assert current_input["action_text"] not in str(normal)

    try:
        build_observation_stage_context(
            stage="pre_question_observation",
            original_input_bundle=current_input,
        )
    except ObservationStageContextBuildError as exc:
        assert exc.code == "NLS3_STAGE_CONTEXT_FUTURE_AUTHORITY_REQUIRED"
    else:
        raise AssertionError("future stage accepted without upstream authority")

    pre, snapshot, _result = _pre_result(current_input)
    assert pre["allowed_source_roles"] == [
        "original_input",
        "question_need_decision",
    ]
    assert snapshot.semantic_source_roles == ("original_input",)


def test_s5_refined_schema_is_bound_but_stops_without_partition_owner() -> None:
    current_input = _known_input()
    supplemental = {"answer": "不安は結果が読めない点についてです。"}
    authority = TrustedFutureStageAuthority(
        authority_owner="question_system_core",
        question_need_decision_sha256="b" * 64,
        permitted_stages=("refined_observation",),
        original_input_bundle_sha256=artifact_sha256(current_input),
        supplemental_answer_bundle_sha256=artifact_sha256(supplemental),
    )
    stage = build_observation_stage_context(
        stage="refined_observation",
        original_input_bundle=current_input,
        trusted_future_authority=authority,
        supplemental_answer_bundle=supplemental,
    )
    assert stage["allowed_source_roles"] == [
        "original_input",
        "question_need_decision",
        "supplemental_answer",
    ]
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    grounded = build_grounded_observation_plan(current_input, evidence_spans=spans)
    try:
        build_grounded_source_snapshot(
            grounded,
            resolver,
            observation_stage_context=stage,
            original_input_bundle=current_input,
            trusted_future_authority=authority,
            supplemental_answer_bundle=supplemental,
        )
    except SemanticObligationInventoryError as exc:
        assert exc.code == "REFINED_SOURCE_PARTITION_OWNER_UNAVAILABLE"
    else:
        raise AssertionError("refined sources were relabelled without an owner")


def test_s5_refined_partition_reaches_content_selection_body_free() -> None:
    (
        current_input,
        supplemental,
        partition,
        partition_issues,
        snapshot,
        result,
        plan,
    ) = _refined_result()
    assert partition_issues == ()
    assert validate_semantic_obligation_inventory(
        result.ledger,
        source_snapshot=snapshot,
    ) == ()
    assert validate_content_selection_policy(
        plan,
        inventory_result=result,
    ) == ()
    assert snapshot.semantic_source_roles == (
        "original_input",
        "supplemental_answer",
    )
    assert partition["semantic_source_roles"] == [
        "original_input",
        "supplemental_answer",
    ]
    assert partition["question_need_decision_is_semantic_source"] is False
    assert partition["control_plane_owner_role"] == "original_input"
    assert partition["original_source_commitment_sha256"] != partition[
        "supplemental_source_commitment_sha256"
    ]

    by_id = {
        row["obligation_id"]: row for row in result.ledger["obligations"]
    }
    selected_ids = {
        row["obligation_id"]
        for row in plan["decisions"]
        if row["status"] == "selected"
    }
    required_ids = set(result.ledger["required_obligation_ids"])
    assert required_ids <= selected_ids
    assert set(plan["required_coverage_obligation_ids"]) == required_ids
    active_nonstance_roles = {
        ref["source_role"]
        for obligation_id in selected_ids
        for row in (by_id[obligation_id],)
        if row["kind"] != "bound_emlis_reception"
        for ref in row["source_refs"]
    }
    assert active_nonstance_roles == {
        "original_input",
        "supplemental_answer",
    }
    assert any(
        row["kind"] == "bound_emlis_reception"
        and row["obligation_id"] in selected_ids
        and {
            ref["source_role"] for ref in row["source_refs"]
        } == {"original_input"}
        for row in result.ledger["obligations"]
    )
    assert plan["source_obligation_ledger_sha256"] == artifact_sha256(
        result.ledger
    )
    assert build_content_selection_plan(deepcopy(result)) == plan
    assert partition["body_free"] is True
    assert plan["body_free"] is True
    for source_body in (
        current_input["thought_text"],
        current_input["action_text"],
        supplemental["thought_text"],
    ):
        if source_body:
            assert source_body not in repr(partition)
            assert source_body not in str(plan)


def test_s5_refined_active_role_drop_is_independently_rejected() -> None:
    *_parents, result, plan = _refined_result()
    by_id = {
        row["obligation_id"]: row for row in result.ledger["obligations"]
    }
    mutation = deepcopy(plan)
    for decision in mutation["decisions"]:
        source_roles = {
            ref["source_role"]
            for ref in by_id[decision["obligation_id"]]["source_refs"]
        }
        if "supplemental_answer" in source_roles:
            decision["status"] = "deferred_by_budget"
            decision["reason_code"] = "OPTIONAL_DEFERRED_BY_BUDGET"
    _resign_content(mutation)
    codes = _codes(
        validate_content_selection_policy(
            mutation,
            inventory_result=result,
        )
    )
    assert "REFINED_SOURCE_ROLES_MUST_BOTH_REMAIN_ACTIVE" in codes
    assert "REQUIRED_COVERAGE_NOT_100_PERCENT" in codes


def test_s5_normal_plan_has_exact_required_coverage_and_no_unproven_status() -> None:
    _stage, _snapshot, result = _normal_result(_known_input())
    left = build_content_selection_plan(result)
    right = build_content_selection_plan(deepcopy(result))
    assert left == right
    assert validate_content_selection_policy(left, inventory_result=result) == ()
    assert left["section_budget"] == _BUDGETS[left["depth"]]

    decision_by_id = {
        row["obligation_id"]: row for row in left["decisions"]
    }
    assert set(result.ledger["required_obligation_ids"]) == set(
        left["required_coverage_obligation_ids"]
    )
    assert all(
        decision_by_id[obligation_id]["status"] == "selected"
        for obligation_id in result.ledger["required_obligation_ids"]
    )
    assert not {
        "integrated_into",
        "blocked_by_safety",
        "unrealizable",
    } & {row["status"] for row in left["decisions"]}
    assert any(row["status"] == "deferred_by_budget" for row in left["decisions"])


def test_s5_batch001_all_100_match_reviewed_depth_and_required_coverage() -> None:
    samples = _samples()
    assert len(samples) == 100
    depth_counts = {"minimal": 0, "focused": 0, "layered": 0}
    for sample in samples:
        _stage, _snapshot, result = _normal_result(sample["input"])
        plan = build_content_selection_plan(result)
        assert validate_content_selection_policy(
            plan, inventory_result=result
        ) == (), sample["case_id"]
        assert plan["depth"] in sample["semantic_contract"][
            "expected_depth_range"
        ], (sample["case_id"], plan["depth"])
        assert plan["section_budget"] == _BUDGETS[plan["depth"]]
        selected = {
            row["obligation_id"]
            for row in plan["decisions"]
            if row["status"] == "selected"
        }
        assert set(result.ledger["required_obligation_ids"]) <= selected
        for text in (
            sample["input"].get("thought_text", ""),
            sample["input"].get("action_text", ""),
        ):
            if text:
                assert text not in str(plan)
        depth_counts[plan["depth"]] += 1
    assert all(depth_counts.values()), depth_counts


def test_s5_depth_uses_typed_meaning_units_not_repetition_or_length() -> None:
    expected = {
        "nls3s_b001_0093": "minimal",
        "nls3s_b001_0098": "minimal",
        "nls3s_b001_0009": "focused",
        "nls3s_b001_0057": "layered",
    }
    for case_id, depth in expected.items():
        _stage, snapshot, result = _normal_result(_sample(case_id)["input"])
        plan = build_content_selection_plan(result)
        assert plan["depth"] == depth, case_id
        assert derive_content_depth(
            result,
            active_obligation_ids=[
                row["obligation_id"]
                for row in plan["decisions"]
                if row["status"] == "selected"
            ],
        ) == depth
        if case_id in {"nls3s_b001_0093", "nls3s_b001_0098"}:
            assert any(
                row.endpoint_semantic_relation == "semantic_restatement"
                and row.semantic_restatement_unit_nucleus_ids
                for row in snapshot.relations
            )

    _stage, _snapshot, distinct = _normal_result(
        _sample("nls3s_b001_0017")["input"]
    )
    assert build_content_selection_plan(distinct)["depth"] in {
        "focused",
        "layered",
    }

    _stage, _snapshot, distinct_topics = _normal_result(
        {
            "thought_text": "掃除は終わった。",
            "action_text": "宿題は完了した。",
        }
    )
    assert build_content_selection_plan(distinct_topics)["depth"] in {
        "focused",
        "layered",
    }


def test_s5_self_denial_and_concrete_action_require_layered_separation() -> None:
    current_input = _self_denial_boundary_input()
    _stage, _snapshot, result = _normal_result(current_input)
    plan = build_content_selection_plan(result)
    assert validate_content_selection_policy(plan, inventory_result=result) == ()
    assert plan["depth"] == "layered"
    assert plan["section_budget"] == _BUDGETS["layered"]
    by_id = {
        row["obligation_id"]: row for row in result.ledger["obligations"]
    }
    active_kinds = {
        by_id[row["obligation_id"]]["kind"]
        for row in plan["decisions"]
        if row["status"] == "selected"
    }
    assert {
        "self_denial_boundary",
        "intention_or_next_action",
        "bound_emlis_reception",
    } <= active_kinds


def test_s5_required_meaning_cannot_be_deferred_omitted_or_relabelled() -> None:
    _stage, _snapshot, result = _normal_result(_known_input())
    source = build_content_selection_plan(result)
    required_id = result.ledger["required_obligation_ids"][0]
    for status in (
        "deferred_by_budget",
        "omitted_redundant",
        "integrated_into",
        "blocked_by_safety",
        "unrealizable",
    ):
        mutation = deepcopy(source)
        decision = next(
            row for row in mutation["decisions"]
            if row["obligation_id"] == required_id
        )
        decision["status"] = status
        if status == "integrated_into":
            decision["integrated_into_obligation_id"] = next(
                row["obligation_id"]
                for row in mutation["decisions"]
                if row["obligation_id"] != required_id
            )
        _resign_content(mutation)
        codes = _codes(
            validate_content_selection_policy(mutation, inventory_result=result)
        )
        assert "CONTENT_SELECTION_STATUS_MISMATCH" in codes, (status, codes)
        assert "REQUIRED_COVERAGE_NOT_100_PERCENT" in codes, (status, codes)
        if status == "integrated_into":
            assert "INTEGRATION_WITNESS_AUTHORITY_REQUIRED" in codes
        if status == "blocked_by_safety":
            assert "UNAUTHORIZED_SAFETY_BLOCK" in codes


def test_s5_depth_budget_parent_hash_and_coverage_are_not_self_declared() -> None:
    _stage, _snapshot, result = _normal_result(
        _sample("nls3s_b001_0098")["input"]
    )
    source = build_content_selection_plan(result)
    assert source["depth"] == "minimal"

    padded = deepcopy(source)
    padded["depth"] = "layered"
    padded["section_budget"] = deepcopy(_BUDGETS["layered"])
    _resign_content(padded)
    assert "CONTENT_DEPTH_MISMATCH" in _codes(
        validate_content_selection_policy(padded, inventory_result=result)
    )

    budget = deepcopy(source)
    budget["section_budget"]["total_sentence_max"] += 1
    _resign_content(budget)
    assert "CONTENT_DEPTH_BUDGET_MISMATCH" in _codes(
        validate_content_selection_policy(budget, inventory_result=result)
    )

    wrong_parent = deepcopy(source)
    wrong_parent["source_obligation_ledger_sha256"] = "f" * 64
    _resign_content(wrong_parent)
    assert validate_content_selection_policy(
        wrong_parent, inventory_result=result
    )

    missing_coverage = deepcopy(source)
    missing_coverage["required_coverage_obligation_ids"] = missing_coverage[
        "required_coverage_obligation_ids"
    ][1:]
    _resign_content(missing_coverage)
    assert validate_content_selection_policy(
        missing_coverage, inventory_result=result
    )


def test_s5_revalidates_step4_against_shrink_reid_relabel_and_downgrade() -> None:
    _stage, snapshot, result = _normal_result(_known_input())
    source = build_content_selection_plan(result)

    shrunk = deepcopy(result)
    optional = next(
        row for row in shrunk.ledger["obligations"] if row["required"] is False
    )
    shrunk.ledger["obligations"] = [
        row for row in shrunk.ledger["obligations"]
        if row["obligation_id"] != optional["obligation_id"]
    ]
    _resign_ledger(shrunk.ledger)
    assert "SEMANTIC_INVENTORY_REVALIDATION_FAILED" in _codes(
        validate_content_selection_policy(source, inventory_result=shrunk)
    )
    _raises_build_code(
        lambda: build_content_selection_plan(shrunk),
        "NLS3_CONTENT_SELECTION_PARENT_INVALID",
    )

    reidentified = deepcopy(result)
    optional = next(
        row for row in reidentified.ledger["obligations"]
        if row["required"] is False
    )
    optional["obligation_id"] = "obl_0000000000000000"
    _resign_ledger(reidentified.ledger)
    _raises_build_code(
        lambda: build_content_selection_plan(reidentified),
        "NLS3_CONTENT_SELECTION_PARENT_INVALID",
    )

    relabelled_snapshot = replace(
        snapshot, observation_stage="pre_question_observation"
    )
    _raises_build_code(
        lambda: build_content_selection_plan(
            replace(result, source_snapshot=relabelled_snapshot)
        ),
        "NLS3_CONTENT_SELECTION_PARENT_INVALID",
    )

    downgraded_snapshot = replace(
        snapshot, response_eligibility="source_unavailable"
    )
    _raises_build_code(
        lambda: build_content_selection_plan(
            replace(result, source_snapshot=downgraded_snapshot)
        ),
        "NLS3_CONTENT_SELECTION_PARENT_INVALID",
    )


def test_s5_pre_question_preserves_every_unknown_and_observation() -> None:
    _stage, snapshot, result = _pre_result(_known_input())
    plan = build_content_selection_plan(result)
    assert validate_content_selection_policy(plan, inventory_result=result) == ()
    by_id = {
        row["obligation_id"]: row for row in result.ledger["obligations"]
    }
    selected_ids = {
        row["obligation_id"]
        for row in plan["decisions"]
        if row["status"] == "selected"
    }
    active_unknowns = {
        unknown_id
        for obligation_id in selected_ids
        for unknown_id in by_id[obligation_id]["unknown_boundary_ids"]
    }
    assert snapshot.preserved_unknown_boundary_ids <= active_unknowns
    assert any(
        by_id[obligation_id]["kind"] not in {
            "unknown_boundary_preservation",
            "bound_emlis_reception",
        }
        for obligation_id in selected_ids
    )

    mutation = deepcopy(plan)
    unknown_id = next(
        row["obligation_id"]
        for row in result.ledger["obligations"]
        if row["kind"] == "unknown_boundary_preservation"
    )
    decision = next(
        row for row in mutation["decisions"]
        if row["obligation_id"] == unknown_id
    )
    decision["status"] = "deferred_by_budget"
    _resign_content(mutation)
    codes = _codes(
        validate_content_selection_policy(mutation, inventory_result=result)
    )
    assert "PRESERVED_UNKNOWN_NOT_ACTIVE" in codes
    assert "REQUIRED_COVERAGE_NOT_100_PERCENT" in codes


def test_s5_source_unavailable_is_limited_to_labels_or_explicit_unknown() -> None:
    labels_only = {
        "thought_text": "",
        "action_text": "",
        "emotions": [{"type": "不安", "strength": "medium"}],
        "categories": ["仕事"],
    }
    _stage, label_snapshot, label_result = _normal_result(labels_only)
    assert label_snapshot.response_eligibility == "source_unavailable"
    label_plan = build_content_selection_plan(label_result)
    assert validate_content_selection_policy(
        label_plan, inventory_result=label_result
    ) == ()
    assert label_plan["depth"] == "minimal"
    assert all(
        source.allowed_claim_scope == "selected_label_only"
        for source in label_snapshot.nuclei
    )

    explicit_unknown = {
        "thought_text": "わからない",
        "action_text": "",
        "emotions": [{"type": "不安", "strength": "medium"}],
        "categories": ["生活"],
    }
    _stage, unknown_snapshot, unknown_result = _normal_result(explicit_unknown)
    assert unknown_snapshot.response_eligibility == "source_unavailable"
    assert any(
        source.source_modality == "uncertain"
        and "operator:uncertainty" in source.source_attribute_codes
        for source in unknown_snapshot.nuclei
    )
    unknown_plan = build_content_selection_plan(unknown_result)
    assert validate_content_selection_policy(
        unknown_plan, inventory_result=unknown_result
    ) == ()

    try:
        _normal_result({})
    except SemanticObligationInventoryError as exc:
        assert exc.code == "OBLIGATION_SOURCE_UNAVAILABLE"
    else:
        raise AssertionError("empty source became a visible v3 success")


def test_s5_new_modules_are_runtime_disconnected_and_do_not_read_fixture_cues() -> None:
    generation_source = inspect.getsource(
        __import__("emlis_ai_content_selection_v3")
    )
    for forbidden in (
        "case_id",
        "family_id",
        "batch_id",
        "expected_depth_range",
        "expected_surface",
        "raw_text",
        "thought_text",
        "action_text",
    ):
        assert forbidden not in generation_source
    assert "emlis_ai_nls_v2" not in generation_source
    assert "def artifact_sha256" not in generation_source

    assert validate_recovery_epoch001_source_baseline_manifest() == ()
    files = RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST["files"]
    assert {
        "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
        "ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py",
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py",
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py",
    } <= set(files)
    for relative_path in files:
        path = _AI_ROOT.parent / relative_path
        assert path.is_file()
        assert validate_recovery_epoch001_source_guard(
            relative_path,
            path.read_bytes(),
            RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST,
        ) == ()
    assert files["ai/services/ai_inference/emlis_ai_reply_service.py"][
        "runtime_connected"
    ] is True
    assert files[
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py"
    ]["runtime_connected"] is False


def test_s5_cross_role_depth_noninflation_floor_and_effect_scope_red() -> None:
    assert _CROSS_ROLE_FULL_REPLAY_POSITIVE.endswith(
        "FULL_TYPED_GRAPH_REPLAY"
    )
    assert _CROSS_ROLE_DEFAULT_GRAPH_NEGATIVE.startswith("EMPTY_WITNESS_")
    original = deepcopy(_known_input())
    full_replay_supplemental = (
        _independent_full_replay_supplemental(original)
    )
    _normal_stage, normal_snapshot, normal_result = _normal_result(original)
    normal_plan = build_content_selection_plan(normal_result)
    (
        current_input,
        supplemental,
        partition,
        partition_issues,
        snapshot,
        result,
        plan,
    ) = _refined_result(original, full_replay_supplemental)
    assert current_input is original
    assert supplemental != original
    assert supplemental is not original
    assert artifact_sha256(supplemental) != artifact_sha256(original)
    assert all(
        str(supplemental[field]).strip() == str(original[field]).strip()
        and supplemental[field] != original[field]
        for field in ("thought_text", "action_text")
    )
    assert supplemental["emotions"] is not original["emotions"]
    assert supplemental["categories"] is not original["categories"]

    required_snapshot_fields = (
        "refined_source_snapshot_schema_version",
        "cross_role_semantic_restatement_witness_sha256",
        "cross_role_semantic_depth_equivalence",
    )
    missing = tuple(
        name for name in required_snapshot_fields if not hasattr(snapshot, name)
    )
    if missing:
        pytest.fail(
            f"{_CROSS_ROLE_DEPTH_RED}:{','.join(missing)}",
            pytrace=False,
        )
    equivalence = snapshot.cross_role_semantic_depth_equivalence
    if equivalence is None:
        pytest.fail(
            f"{_CROSS_ROLE_DEPTH_RED}:empty_depth_equivalence",
            pytrace=False,
        )

    assert partition_issues == ()
    assert partition["cross_source_bindings"] == []
    assert partition["question_need_decision_is_semantic_source"] is False
    assert partition["control_plane_owner_role"] == "original_input"
    assert equivalence.schema_version == _CROSS_ROLE_DEPTH_SCHEMA
    assert equivalence.effect_scope == _CROSS_ROLE_EFFECT_SCOPE
    assert equivalence.source_witness_sha256 == (
        snapshot.cross_role_semantic_restatement_witness_sha256
    )
    _assert_exact_cross_role_graph_bijection(snapshot)
    assert normal_snapshot.semantic_source_roles == ("original_input",)
    assert snapshot.semantic_source_roles == (
        "original_input",
        "supplemental_answer",
    )

    assert validate_semantic_obligation_inventory(
        result.ledger,
        source_snapshot=snapshot,
    ) == ()
    assert validate_content_selection_policy(
        plan,
        inventory_result=result,
    ) == ()
    assert plan["depth"] == normal_plan["depth"]
    assert _DEPTH_RANK[plan["depth"]] >= _DEPTH_RANK[normal_plan["depth"]]
    assert plan["source_obligation_ledger_sha256"] == artifact_sha256(
        result.ledger
    )
    assert build_content_selection_plan(deepcopy(result)) == plan

    def assert_binding_preservation(
        current_snapshot,
        current_result,
        current_plan,
    ) -> None:
        current_equivalence = (
            current_snapshot.cross_role_semantic_depth_equivalence
        )
        assert current_equivalence is not None
        obligation_by_id = {
            row["obligation_id"]
            for row in current_result.ledger["obligations"]
        }
        row_by_id = {
            row["obligation_id"]: row
            for row in current_result.ledger["obligations"]
        }
        selected = {
            row["obligation_id"]
            for row in current_plan["decisions"]
            if row["status"] == "selected"
        }
        required = set(
            current_result.ledger["required_obligation_ids"]
        )
        bound_obligation_ids_by_role = {
            "original_input": set(),
            "supplemental_answer": set(),
        }
        ref_field = {
            "nucleus": "nucleus_ids",
            "relation": "relation_ids",
            "unknown_boundary": "unknown_boundary_ids",
        }
        for binding in current_equivalence.component_bindings:
            field = ref_field[binding.component_kind]
            for source_role, source_id in (
                (
                    binding.original_source_role,
                    binding.original_source_id,
                ),
                (
                    binding.supplemental_source_role,
                    binding.supplemental_source_id,
                ),
            ):
                bound_rows = [
                    row
                    for row in current_result.ledger["obligations"]
                    if row["kind"] != "bound_emlis_reception"
                    and any(
                        ref["source_role"] == source_role
                        and source_id in ref[field]
                        for ref in row["source_refs"]
                    )
                ]
                assert bound_rows
                assert all(
                    {
                        ref["source_role"]
                        for ref in row["source_refs"]
                    } == {source_role}
                    for row in bound_rows
                )
                bound_obligation_ids = {
                    row["obligation_id"] for row in bound_rows
                }
                assert bound_obligation_ids
                assert bound_obligation_ids & required <= selected
                bound_obligation_ids_by_role[source_role].update(
                    bound_obligation_ids
                )
        assert (
            bound_obligation_ids_by_role["original_input"]
            .isdisjoint(
                bound_obligation_ids_by_role["supplemental_answer"]
            )
        )
        assert all(
            bound_ids & selected
            for bound_ids in bound_obligation_ids_by_role.values()
        )

        reception_rows = [
            row
            for row in current_result.ledger["obligations"]
            if row["kind"] == "bound_emlis_reception"
        ]
        assert reception_rows
        for reception in reception_rows:
            assert {
                ref["source_role"] for ref in reception["source_refs"]
            } == {"original_input"}
            assert len(reception["target_obligation_ids"]) == 1
            target_id = reception["target_obligation_ids"][0]
            assert target_id in obligation_by_id
            assert {
                ref["source_role"]
                for ref in row_by_id[target_id]["source_refs"]
            } == {"original_input"}

    assert_binding_preservation(snapshot, result, plan)

    legacy_original = deepcopy(_known_input())
    legacy_supplemental = _legacy_reduced_supplemental(legacy_original)
    (
        _legacy_current,
        _legacy_answer,
        legacy_partition,
        legacy_partition_issues,
        legacy_snapshot,
        legacy_result,
        legacy_plan,
    ) = _refined_result(
        legacy_original,
        legacy_supplemental,
    )
    assert legacy_partition_issues == ()
    assert legacy_partition["cross_source_bindings"] == []
    assert (
        legacy_partition["question_need_decision_is_semantic_source"]
        is False
    )
    assert legacy_snapshot.cross_role_semantic_depth_equivalence is None
    assert legacy_snapshot.semantic_source_roles == (
        "original_input",
        "supplemental_answer",
    )
    assert validate_semantic_obligation_inventory(
        legacy_result.ledger,
        source_snapshot=legacy_snapshot,
    ) == ()
    assert validate_content_selection_policy(
        legacy_plan,
        inventory_result=legacy_result,
    ) == ()
    legacy_required = set(
        legacy_result.ledger["required_obligation_ids"]
    )
    legacy_selected = {
        row["obligation_id"]
        for row in legacy_plan["decisions"]
        if row["status"] == "selected"
    }
    assert legacy_required <= legacy_selected
    assert set(
        legacy_plan["required_coverage_obligation_ids"]
    ) == legacy_required
    assert {
        ref["source_role"]
        for row in legacy_result.ledger["obligations"]
        if row["kind"] != "bound_emlis_reception"
        for ref in row["source_refs"]
    } == {"original_input", "supplemental_answer"}
    assert all(
        {
            ref["source_role"] for ref in row["source_refs"]
        } == {"original_input"}
        for row in legacy_result.ledger["obligations"]
        if row["kind"] == "bound_emlis_reception"
    )
    assert _DEPTH_RANK[legacy_plan["depth"]] >= _DEPTH_RANK[
        normal_plan["depth"]
    ]

    layered_input = _body_free_input_matching(
        lambda candidate_snapshot, _candidate_result, candidate_plan: (
            candidate_plan["depth"] == "layered"
            and bool(candidate_snapshot.relations)
            and bool(candidate_snapshot.unknowns)
        )
    )
    (
        _layered_stage,
        _layered_snapshot,
        layered_normal_result,
    ) = _normal_result(layered_input)
    layered_normal_plan = build_content_selection_plan(layered_normal_result)
    *_layered_parents, layered_refined_result, layered_refined_plan = (
        _refined_result(
            layered_input,
            _independent_full_replay_supplemental(layered_input),
        )
    )
    assert layered_normal_plan["depth"] == "layered"
    assert layered_refined_plan["depth"] == "layered"
    assert _DEPTH_RANK[layered_refined_plan["depth"]] >= _DEPTH_RANK[
        layered_normal_plan["depth"]
    ]
    assert validate_content_selection_policy(
        layered_refined_plan,
        inventory_result=layered_refined_result,
    ) == ()

    safety_input = _self_denial_boundary_input()
    (
        _safety_normal_stage,
        safety_normal_snapshot,
        safety_normal_result,
    ) = _normal_result(safety_input)
    safety_normal_plan = build_content_selection_plan(safety_normal_result)
    (
        _safety_current,
        _safety_supplemental,
        _safety_partition,
        safety_partition_issues,
        safety_refined_snapshot,
        safety_refined_result,
        safety_refined_plan,
    ) = _refined_result(
        safety_input,
        _independent_full_replay_supplemental(safety_input),
    )
    assert safety_partition_issues == ()
    assert safety_normal_plan["depth"] == "layered"
    assert safety_refined_plan["depth"] == "layered"
    assert safety_normal_snapshot.safety_required_boundary_codes
    assert safety_refined_snapshot.safety_required_boundary_codes == (
        safety_normal_snapshot.safety_required_boundary_codes
    )
    assert (
        safety_refined_snapshot.cross_role_semantic_depth_equivalence
        is not None
    )
    assert (
        safety_refined_snapshot
        .cross_role_semantic_depth_equivalence
        .component_bindings
    )
    safety_selected_ids = {
        row["obligation_id"]
        for row in safety_refined_plan["decisions"]
        if row["status"] == "selected"
    }
    assert set(
        safety_refined_result.ledger["required_obligation_ids"]
    ) <= safety_selected_ids
    assert validate_content_selection_policy(
        safety_refined_plan,
        inventory_result=safety_refined_result,
    ) == ()
    assert_binding_preservation(
        safety_refined_snapshot,
        safety_refined_result,
        safety_refined_plan,
    )
    safety_obligation_rows = [
        row
        for row in safety_refined_result.ledger["obligations"]
        if row["kind"] in {
            "self_denial_boundary",
            "bounded_counterposition",
        }
    ]
    assert safety_obligation_rows
    safety_obligation_by_id = {
        row["obligation_id"]: row for row in safety_obligation_rows
    }
    for safety_row in safety_obligation_rows:
        assert len(safety_row["must_not_merge_with"]) == 1
        separated_id = safety_row["must_not_merge_with"][0]
        assert separated_id in safety_obligation_by_id
        assert safety_row["obligation_id"] in (
            safety_obligation_by_id[separated_id]["must_not_merge_with"]
        )
    safety_pair_ids = set(safety_obligation_by_id)
    assert safety_pair_ids <= {
        row["obligation_id"]
        for row in safety_refined_plan["decisions"]
    }
    assert (
        safety_pair_ids
        & set(safety_refined_result.ledger["required_obligation_ids"])
    ) <= safety_selected_ids

    unsafe_nucleus_ids_by_role = {
        role: {
            nucleus_id
            for row in safety_obligation_rows
            if row["kind"] == "self_denial_boundary"
            for ref in row["source_refs"]
            if ref["source_role"] == role
            for nucleus_id in ref["nucleus_ids"]
        }
        for role in ("original_input", "supplemental_answer")
    }
    assert all(unsafe_nucleus_ids_by_role.values())
    safety_bindings = (
        safety_refined_snapshot
        .cross_role_semantic_depth_equivalence
        .component_bindings
    )
    for role, binding_field in (
        ("original_input", "original_source_id"),
        ("supplemental_answer", "supplemental_source_id"),
    ):
        unsafe_closed_ids = _incident_affected_closure_ids(
            safety_refined_snapshot,
            source_role=role,
            nucleus_ids=unsafe_nucleus_ids_by_role[role],
        )
        assert unsafe_closed_ids
        assert unsafe_closed_ids.isdisjoint(
            {
                getattr(binding, binding_field)
                for binding in safety_bindings
            }
        )

    (
        _unmatched_current,
        _unmatched_supplemental,
        _unmatched_partition,
        unmatched_partition_issues,
        unmatched_snapshot,
        unmatched_result,
        unmatched_plan,
    ) = _refined_result(_known_input(), layered_input)
    assert unmatched_partition_issues == ()
    unmatched_equivalence = (
        unmatched_snapshot.cross_role_semantic_depth_equivalence
    )
    assert unmatched_equivalence is not None
    assert unmatched_equivalence.component_bindings
    bound_ids_by_role = {
        "original_input": {
            row.original_source_id
            for row in unmatched_equivalence.component_bindings
        },
        "supplemental_answer": {
            row.supplemental_source_id
            for row in unmatched_equivalence.component_bindings
        },
    }
    bound_nucleus_ids_by_role = {
        "original_input": {
            row.original_source_id
            for row in unmatched_equivalence.component_bindings
            if row.component_kind == "nucleus"
        },
        "supplemental_answer": {
            row.supplemental_source_id
            for row in unmatched_equivalence.component_bindings
            if row.component_kind == "nucleus"
        },
    }
    unmatched_ids_by_role: dict[str, set[str]] = {}
    for source_role in ("original_input", "supplemental_answer"):
        all_role_ids = {
            row.source_id
            for row in (
                *unmatched_snapshot.nuclei,
                *unmatched_snapshot.relations,
                *unmatched_snapshot.unknowns,
            )
            if row.source_role == source_role
        }
        assert bound_nucleus_ids_by_role[source_role]
        bound_closure = _incident_affected_closure_ids(
            unmatched_snapshot,
            source_role=source_role,
            nucleus_ids=bound_nucleus_ids_by_role[source_role],
        )
        assert bound_closure == bound_ids_by_role[source_role]
        unmatched_ids_by_role[source_role] = (
            all_role_ids - bound_ids_by_role[source_role]
        )
        assert unmatched_ids_by_role[source_role]
        assert unmatched_ids_by_role[source_role].isdisjoint(
            bound_closure
        )
    bound_supplemental_ids = {
        row.supplemental_source_id
        for row in unmatched_equivalence.component_bindings
    }
    unmatched_relation_ids = {
        row.source_id
        for row in unmatched_snapshot.relations
        if row.source_role == "supplemental_answer"
        and row.source_id not in bound_supplemental_ids
    }
    unmatched_unknown_ids = {
        row.source_id
        for row in unmatched_snapshot.unknowns
        if row.source_role == "supplemental_answer"
        and row.source_id not in bound_supplemental_ids
    }
    unmatched_nucleus_ids = {
        row.source_id
        for row in unmatched_snapshot.nuclei
        if row.source_role == "supplemental_answer"
        and row.source_id not in bound_supplemental_ids
    }
    assert unmatched_nucleus_ids
    assert unmatched_relation_ids
    assert unmatched_unknown_ids
    unmatched_source_ids = (
        unmatched_nucleus_ids
        | unmatched_relation_ids
        | unmatched_unknown_ids
    )
    assert unmatched_source_ids == unmatched_ids_by_role[
        "supplemental_answer"
    ]
    referenced_unmatched_ids_by_role = {
        role: set()
        for role in ("original_input", "supplemental_answer")
    }
    unmatched_obligation_ids_by_role = {
        role: set()
        for role in ("original_input", "supplemental_answer")
    }
    for obligation in unmatched_result.ledger["obligations"]:
        obligation_ref_roles = {
            ref["source_role"] for ref in obligation["source_refs"]
        }
        for role in ("original_input", "supplemental_answer"):
            matched_ids = {
                source_id
                for ref in obligation["source_refs"]
                if ref["source_role"] == role
                for source_id in (
                    *ref["nucleus_ids"],
                    *ref["relation_ids"],
                    *ref["unknown_boundary_ids"],
                )
                if source_id in unmatched_ids_by_role[role]
            }
            if matched_ids:
                assert obligation_ref_roles == {role}
                referenced_unmatched_ids_by_role[role].update(matched_ids)
                unmatched_obligation_ids_by_role[role].add(
                    obligation["obligation_id"]
                )
    for role in ("original_input", "supplemental_answer"):
        assert referenced_unmatched_ids_by_role[role] == (
            unmatched_ids_by_role[role]
        )
        assert unmatched_obligation_ids_by_role[role]
    unmatched_obligation_ids = set().union(
        *unmatched_obligation_ids_by_role.values()
    )
    unmatched_selected_ids = {
        row["obligation_id"]
        for row in unmatched_plan["decisions"]
        if row["status"] == "selected"
    }
    unmatched_required_ids = set(
        unmatched_result.ledger["required_obligation_ids"]
    )
    assert unmatched_obligation_ids <= unmatched_selected_ids
    assert all(
        (
            unmatched_obligation_ids_by_role[role]
            & unmatched_required_ids
        )
        <= set(unmatched_plan["required_coverage_obligation_ids"])
        for role in ("original_input", "supplemental_answer")
    )
    assert unmatched_required_ids <= unmatched_selected_ids
    assert set(
        unmatched_plan["required_coverage_obligation_ids"]
    ) == unmatched_required_ids
    assert all(
        {
            ref["source_role"] for ref in row["source_refs"]
        } == {"original_input"}
        for row in unmatched_result.ledger["obligations"]
        if row["kind"] == "bound_emlis_reception"
    )
    assert unmatched_plan["depth"] == "layered"
    assert validate_semantic_obligation_inventory(
        unmatched_result.ledger,
        source_snapshot=unmatched_snapshot,
    ) == ()
    assert validate_content_selection_policy(
        unmatched_plan,
        inventory_result=unmatched_result,
    ) == ()

    by_id = {
        row["obligation_id"]: row for row in result.ledger["obligations"]
    }
    selected_ids = {
        row["obligation_id"]
        for row in plan["decisions"]
        if row["status"] == "selected"
    }
    required_ids = set(result.ledger["required_obligation_ids"])
    assert required_ids <= selected_ids
    assert set(plan["required_coverage_obligation_ids"]) == required_ids
    supplemental_ids = {
        row["obligation_id"]
        for row in result.ledger["obligations"]
        if row["kind"] != "bound_emlis_reception"
        and {
            ref["source_role"] for ref in row["source_refs"]
        } == {"supplemental_answer"}
    }
    assert supplemental_ids
    required_supplemental_ids = supplemental_ids & required_ids
    assert required_supplemental_ids
    assert required_supplemental_ids <= selected_ids
    assert {
        row["obligation_id"] for row in plan["decisions"]
    } == set(by_id)
    assert all(
        decision["status"] == "selected"
        for decision in plan["decisions"]
        if decision["obligation_id"] in required_ids
    )
    assert {
        ref["source_role"]
        for obligation_id in selected_ids
        for row in (by_id[obligation_id],)
        if row["kind"] != "bound_emlis_reception"
        for ref in row["source_refs"]
    } == {"original_input", "supplemental_answer"}
    assert all(
        {
            ref["source_role"] for ref in row["source_refs"]
        } == {"original_input"}
        for row in result.ledger["obligations"]
        if row["kind"] == "bound_emlis_reception"
    )

    target_id = sorted(required_supplemental_ids)[0]
    other_id = next(
        row["obligation_id"]
        for row in plan["decisions"]
        if row["obligation_id"] != target_id
    )
    for status in (
        "deferred_by_budget",
        "omitted_redundant",
        "integrated_into",
    ):
        mutation = deepcopy(plan)
        decision = next(
            row for row in mutation["decisions"]
            if row["obligation_id"] == target_id
        )
        decision["status"] = status
        if status == "integrated_into":
            decision["integrated_into_obligation_id"] = other_id
        _resign_content(mutation)
        mutation_codes = _codes(
            validate_content_selection_policy(
                mutation,
                inventory_result=result,
            )
        )
        assert "CONTENT_SELECTION_STATUS_MISMATCH" in mutation_codes
        assert "REQUIRED_COVERAGE_NOT_100_PERCENT" in mutation_codes
        if status == "integrated_into":
            assert "INTEGRATION_WITNESS_AUTHORITY_REQUIRED" in mutation_codes

    wrong_effect_snapshot = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            effect_scope="OBLIGATION_SELECTION",
        ),
    )
    wrong_effect_result = replace(
        result,
        source_snapshot=wrong_effect_snapshot,
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=wrong_effect_snapshot,
        )
    )
    assert "SEMANTIC_INVENTORY_REVALIDATION_FAILED" in _codes(
        validate_content_selection_policy(
            plan,
            inventory_result=wrong_effect_result,
        )
    )
    _raises_build_code(
        lambda: build_content_selection_plan(wrong_effect_result),
        "NLS3_CONTENT_SELECTION_PARENT_INVALID",
    )

    source_text = inspect.getsource(content_module)
    assert "cross_role_semantic_depth_equivalence" in source_text
    assert "CONTENT_DEPTH_ONLY" in source_text
    for forbidden in (
        "thought_text",
        "action_text",
        "normalized_text",
        "synonym",
        "case_id",
        "family_id",
        "fixture_id",
    ):
        assert forbidden not in source_text
