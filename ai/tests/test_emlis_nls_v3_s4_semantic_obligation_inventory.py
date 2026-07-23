# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 4 Semantic Obligation Inventory acceptance and RED tests."""

from copy import deepcopy
from dataclasses import asdict, fields, replace
import json
from pathlib import Path
import re

import pytest

import emlis_ai_semantic_obligation_inventory_v3 as inventory_module
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_nls_v3_artifact_contract import (
    TrustedFutureStageAuthority,
    artifact_sha256,
    derive_content_id,
    derive_obligation_id,
)
from emlis_ai_observation_stage_context_v3 import build_observation_stage_context
from emlis_ai_refined_source_partition_v3 import (
    build_refined_source_partition,
    validate_refined_source_partition,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    FROZEN_SOURCE_POLICY_SHA256,
    SemanticObligationInventoryError,
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
    obligation_inventory_upper_bound,
    validate_obligation_inventory_count,
    validate_semantic_obligation_inventory,
)


_AI_ROOT = Path(__file__).resolve().parents[1]
_BATCH_PATH = (
    _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated" / "batch_001.jsonl"
)
_MACHINE_SOURCE_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_REFINED_SOURCE_SNAPSHOT_SCHEMA = (
    "cocolon.emlis.nls_v3.refined_source_snapshot.v2"
)
_CROSS_ROLE_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_witness.v1"
)
_CROSS_ROLE_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_adapter.20260723.v1"
)
_CROSS_ROLE_DEPTH_SCHEMA = (
    "cocolon.emlis.nls_v3.cross_role_semantic_depth_equivalence.v1"
)
_CROSS_ROLE_EFFECT_SCOPE = "CONTENT_DEPTH_ONLY"
_CROSS_ROLE_SNAPSHOT_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_REFINED_SNAPSHOT_BINDING_NOT_PROVED"
)
_CROSS_ROLE_DEPTH_COMPONENT_FIELDS = (
    "component_kind",
    "original_source_role",
    "original_source_kind",
    "original_source_id",
    "supplemental_source_role",
    "supplemental_source_kind",
    "supplemental_source_id",
    "canonical_typed_component_sha256",
)
_CROSS_ROLE_DEPTH_EQUIVALENCE_FIELDS = (
    "schema_version",
    "source_witness_schema_version",
    "source_witness_adapter_version",
    "source_witness_sha256",
    "component_bindings",
    "effect_scope",
    "equivalence_sha256",
    "body_free",
)


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


def _normal_source(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    stage = build_observation_stage_context(
        stage="normal_observation", original_input_bundle=current_input
    )
    snapshot = build_grounded_source_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    return plan, resolver, stage, snapshot


def _pre_source(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
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
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=authority,
    )
    return plan, resolver, stage, authority, snapshot


def _plan_and_resolver(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    return build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    ), resolver


def _raises_code(call, expected: str) -> None:
    try:
        call()
    except SemanticObligationInventoryError as exc:
        assert exc.code == expected, (expected, exc.code, str(exc))
    else:
        raise AssertionError(f"expected {expected}")


def _resign_ledger(value: dict[str, object]) -> None:
    value["ledger_id"] = derive_content_id("nls3obl_", value, "ledger_id")


def test_s4_known_normal_builds_lossless_machine_safe_alias_inventory() -> None:
    _plan, _resolver, _stage, snapshot = _normal_source(_known_input())
    result = build_semantic_obligation_inventory(snapshot)
    ledger = result.ledger

    assert validate_semantic_obligation_inventory(
        ledger, source_snapshot=snapshot
    ) == ()
    assert ledger["response_eligibility"] == "normal_surface"
    assert ledger["body_free"] is True
    assert len(ledger["obligations"]) <= result.inventory_upper_bound

    bindings = snapshot.source_id_alias_bindings
    assert bindings
    assert len(
        {(item.source_kind, item.actual_source_id) for item in bindings}
    ) == len(bindings)
    assert len({item.alias_source_id for item in bindings}) == len(bindings)
    assert all(_MACHINE_SOURCE_ID_RE.fullmatch(item.alias_source_id) for item in bindings)
    assert any(":" in item.actual_source_id for item in bindings)
    encoded_ledger = str(ledger)
    assert all(
        item.actual_source_id not in encoded_ledger
        for item in bindings
        if ":" in item.actual_source_id
    )
    assert all(item.alias_source_id in str(snapshot) for item in bindings)

    stance_rows = [
        row for row in ledger["obligations"]
        if row["kind"] == "bound_emlis_reception"
    ]
    assert len(stance_rows) == len(snapshot.reception_opportunities)
    assert any(row["required"] is True for row in stance_rows)
    assert all(len(row["target_obligation_ids"]) == 1 for row in stance_rows)
    assert {
        item
        for row in stance_rows
        for item in row["reception_opportunity_ids"]
    } == {row.source_id for row in snapshot.reception_opportunities}


def test_s4_batch001_all_100_build_and_validate_without_surface_or_runtime() -> None:
    samples = _samples()
    assert len(samples) == 100
    for sample in samples:
        _plan, _resolver, _stage, snapshot = _normal_source(sample["input"])
        result = build_semantic_obligation_inventory(snapshot)
        assert validate_semantic_obligation_inventory(
            result.ledger, source_snapshot=snapshot
        ) == (), sample["case_id"]
        assert result.ledger["required_obligation_ids"], sample["case_id"]


def test_s4_is_deterministic_body_free_and_ignores_fixture_cues() -> None:
    current_input = _known_input()
    _plan, _resolver, _stage, snapshot = _normal_source(current_input)
    left = build_semantic_obligation_inventory(snapshot).ledger
    right = build_semantic_obligation_inventory(snapshot).ledger
    assert left == right
    assert artifact_sha256(left) == artifact_sha256(right)
    encoded = str((snapshot, left))
    assert not hasattr(snapshot, "_source_origin")
    assert current_input["thought_text"] not in str(vars(snapshot))
    assert current_input["action_text"] not in str(vars(snapshot))
    assert current_input["thought_text"] not in encoded
    assert current_input["action_text"] not in encoded
    for forbidden in (
        "case_id",
        "family_id",
        "batch_id",
        "expected_surface",
        "username",
        "question_need_decision_is_semantic_source': True",
    ):
        assert forbidden not in encoded


def test_s4_cross_input_plan_and_resolver_cannot_bind_to_another_input() -> None:
    first = _known_input()
    second = {
        **first,
        "thought_text": "今日は静かな時間を過ごせて、少し落ち着いた。",
    }
    spans = build_evidence_ledger(first)
    resolver = build_evidence_span_resolver(spans, current_input=first)
    plan = build_grounded_observation_plan(first, evidence_spans=spans)
    stage = build_observation_stage_context(
        stage="normal_observation", original_input_bundle=second
    )
    _raises_code(
        lambda: build_grounded_source_snapshot(
            plan,
            resolver,
            observation_stage_context=stage,
            original_input_bundle=second,
        ),
        "SOURCE_INPUT_BUNDLE_MISMATCH",
    )


def test_s4_same_shape_input_swap_changes_v3_source_commitments() -> None:
    first = {
        "thought_text": "鉢を明るい場所へ移した。",
        "action_text": "窓辺へ鉢を移した。",
        "emotions": [{"type": "平穏", "strength": "weak"}],
        "categories": ["趣味"],
    }
    second = {
        "thought_text": "本を机の上へ移した。",
        "action_text": "棚へ箱を移した。",
        "emotions": [{"type": "平穏", "strength": "weak"}],
        "categories": ["趣味"],
    }
    _plan, _resolver, _stage, first_snapshot = _normal_source(first)
    _plan, _resolver, _stage, second_snapshot = _normal_source(second)
    assert (
        first_snapshot.semantic_restatement_plan_binding_sha256
        != second_snapshot.semantic_restatement_plan_binding_sha256
    )
    assert (
        first_snapshot.source_semantic_restatement_witness_sha256
        != second_snapshot.source_semantic_restatement_witness_sha256
    )
    assert (
        first_snapshot.source_observation_plan_sha256
        != second_snapshot.source_observation_plan_sha256
    )


def test_s4_exact_source_replay_rejects_added_deleted_and_rebound_meaning() -> None:
    _plan, _resolver, _stage, snapshot = _normal_source(_known_input())
    source = build_semantic_obligation_inventory(snapshot).ledger
    relation = next(
        row for row in source["obligations"]
        if row["kind"] == "grounded_relation_preservation"
    )

    deleted = deepcopy(source)
    deleted["obligations"] = [
        row for row in deleted["obligations"]
        if row["obligation_id"] != relation["obligation_id"]
    ]
    deleted["required_obligation_ids"] = [
        item for item in deleted["required_obligation_ids"]
        if item != relation["obligation_id"]
    ]
    _resign_ledger(deleted)
    issues = validate_semantic_obligation_inventory(
        deleted, source_snapshot=snapshot
    )
    assert "OBLIGATION_IDENTITY_SET_MISMATCH" in issues
    assert "OBLIGATION_CONTENT_MISMATCH" in issues

    invented = deepcopy(source)
    forged = deepcopy(
        next(
            row for row in invented["obligations"]
            if row["kind"] == "grounded_nucleus_notice"
        )
    )
    forged.update(
        {
            "kind": "self_denial_boundary",
            "required": True,
            "allowed_response_acts": ["separate_self_denial"],
            "source_authority_codes": ["nucleus", "safety_policy"],
            "forbidden_claim_codes": ["IDENTITY_CLAIM_NOT_FACT"],
        }
    )
    forged["obligation_id"] = derive_obligation_id(forged)
    invented["obligations"].append(forged)
    invented["required_obligation_ids"].append(forged["obligation_id"])
    invented["required_obligation_ids"].sort()
    _resign_ledger(invented)
    issues = validate_semantic_obligation_inventory(
        invented, source_snapshot=snapshot
    )
    assert "OBLIGATION_IDENTITY_SET_MISMATCH" in issues
    assert "OBLIGATION_CONTENT_MISMATCH" in issues

    rebound = deepcopy(source)
    stance = next(
        row for row in rebound["obligations"]
        if row["kind"] == "bound_emlis_reception"
    )
    wrong_target = next(
        row["obligation_id"] for row in rebound["obligations"]
        if row["kind"] == "grounded_nucleus_notice"
        and row["obligation_id"] not in stance["target_obligation_ids"]
    )
    stance["target_obligation_ids"] = [wrong_target]
    stance["obligation_id"] = derive_obligation_id(stance)
    _resign_ledger(rebound)
    assert "OBLIGATION_CONTENT_MISMATCH" in validate_semantic_obligation_inventory(
        rebound, source_snapshot=snapshot
    )


def test_s4_alias_and_snapshot_authority_forgery_are_rejected() -> None:
    _plan, _resolver, _stage, snapshot = _normal_source(_known_input())
    result = build_semantic_obligation_inventory(snapshot)
    first = snapshot.source_id_alias_bindings[0]
    forged_binding = replace(first, alias_source_id="evidence_00000000000000000000")
    forged_snapshot = replace(
        snapshot,
        source_id_alias_bindings=(
            forged_binding,
            *snapshot.source_id_alias_bindings[1:],
        ),
    )
    issues = validate_semantic_obligation_inventory(
        result.ledger, source_snapshot=forged_snapshot
    )
    assert "SOURCE_ID_ALIAS_BINDING_INVALID" in issues
    try:
        build_semantic_obligation_inventory(forged_snapshot)
    except SemanticObligationInventoryError:
        pass
    else:
        raise AssertionError("forged source alias was accepted")

    shrunk = replace(snapshot, nuclei=snapshot.nuclei[:-1])
    issues = validate_semantic_obligation_inventory(
        result.ledger, source_snapshot=shrunk
    )
    assert {
        "SOURCE_ID_ALIAS_COVERAGE_MISMATCH",
        "SNAPSHOT_AUTHORITY_COMMITMENT_MISMATCH",
    } & set(issues)


def test_s4_coherently_resigned_snapshot_rebinds_to_original_source() -> None:
    _plan, _resolver, _stage, snapshot = _normal_source(_known_input())
    result = build_semantic_obligation_inventory(snapshot)
    source = snapshot.nuclei[0]
    assert source.required is True
    changed_source = replace(
        source,
        required=False,
        retention="optional",
    )
    changed_nuclei = (changed_source, *snapshot.nuclei[1:])
    changed = replace(snapshot, nuclei=changed_nuclei)

    # Re-sign every commitment that the former circular snapshot validator
    # derived from the snapshot itself.  The replacement object has no
    # module-owned request-local Grounded provenance capability, so the
    # coherent downgrade must still fail closed.
    eligibility = inventory_module._eligibility_authority_from_snapshot(changed)
    plan_artifact = inventory_module._plan_native_artifact(
        plan_schema_version=changed.plan_schema_version,
        plan_adapter_version=changed.plan_adapter_version,
        plan_generation_path=changed.plan_generation_path,
        semantic_restatement_witness_schema_version=(
            changed.semantic_restatement_witness_schema_version
        ),
        semantic_restatement_witness_adapter_version=(
            changed.semantic_restatement_witness_adapter_version
        ),
        semantic_restatement_plan_binding_sha256=(
            changed.semantic_restatement_plan_binding_sha256
        ),
        source_semantic_restatement_witness_sha256=(
            changed.source_semantic_restatement_witness_sha256
        ),
        bindings=changed.source_id_alias_bindings,
        evidence_ids=changed.evidence_ids,
        nuclei=changed.nuclei,
        relations=changed.relations,
        unknowns=changed.unknowns,
        safety_required_boundary_codes=(
            changed.safety_required_boundary_codes
        ),
        identity_claim_must_not_be_accepted_as_fact=(
            changed.identity_claim_must_not_be_accepted_as_fact
        ),
        eligibility=eligibility,
    )
    plan_hash = artifact_sha256(plan_artifact)
    reception_artifact = inventory_module._reception_native_artifact(
        changed.reception_opportunities,
        changed.source_id_alias_bindings,
    )
    reception_hash = (
        artifact_sha256(reception_artifact)
        if reception_artifact is not None
        else None
    )
    inventory_bound = obligation_inventory_upper_bound(
        dict(changed.resource_counts)
    )
    authority = inventory_module._ledger_authority(
        plan_hash=plan_hash,
        stage_hash=changed.source_observation_stage_context_sha256,
        reception_hash=reception_hash,
        eligibility=eligibility,
        evidence_ids=changed.evidence_ids,
        nuclei=changed.nuclei,
        relations=changed.relations,
        unknowns=changed.unknowns,
        opportunities=changed.reception_opportunities,
        role_bindings=changed.source_role_bindings,
        inventory_bound=inventory_bound,
    )
    resigned = replace(
        changed,
        source_observation_plan_sha256=plan_hash,
        source_reception_opportunity_plan_sha256=reception_hash,
        ledger_source_authority=authority,
    )

    class CallerDefinedOrigin:
        def rebuild(self):
            return resigned

    assert not hasattr(inventory_module, "_SOURCE_ORIGIN_REGISTRY")
    assert not hasattr(inventory_module, "_registered_source_origin")
    _raises_code(
        lambda: inventory_module._register_source_origin(
            resigned,
            CallerDefinedOrigin(),
        ),
        "SOURCE_ORIGIN_REGISTRATION_INVALID",
    )
    assert inventory_module._snapshot_authority_issues(resigned) == (
        "SOURCE_ORIGIN_AUTHORITY_REQUIRED",
    )
    assert "SOURCE_ORIGIN_AUTHORITY_REQUIRED" in (
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=resigned,
        )
    )
    _raises_code(
        lambda: build_semantic_obligation_inventory(resigned),
        "SOURCE_ORIGIN_AUTHORITY_REQUIRED",
    )


def test_s4_restatement_relation_is_typed_and_cannot_inflate_depth() -> None:
    current_input = _sample("nls3s_b001_0098")["input"]
    _plan, _resolver, _stage, snapshot = _normal_source(current_input)
    relation = next(
        row for row in snapshot.relations
        if row.endpoint_semantic_relation == "semantic_restatement"
    )
    assert relation.grounding_kind == "bounded_structural_inference"
    assert relation.relation_direction == "source_to_target"
    assert "NO_BOUNDED_INFERENCE_UPGRADE" in relation.forbidden_claim_codes
    assert "NO_SEMANTIC_RESTATEMENT_DEPTH_INFLATION" in relation.forbidden_claim_codes
    ledger = build_semantic_obligation_inventory(snapshot).ledger
    row = next(
        item for item in ledger["obligations"]
        if relation.source_id in item["relation_ids"]
    )
    assert "NO_SEMANTIC_RESTATEMENT_DEPTH_INFLATION" in row["forbidden_claim_codes"]

    distinct_input = _sample("nls3s_b001_0017")["input"]
    _plan, _resolver, _stage, distinct = _normal_source(distinct_input)
    assert all(
        row.endpoint_semantic_relation == "distinct_meanings"
        for row in distinct.relations
    )


def test_s4_restatement_unit_is_losslessly_bound_and_forgery_is_rejected() -> None:
    current_input = _sample("nls3s_b001_0093")["input"]
    plan, resolver, stage, snapshot = _normal_source(current_input)
    relation = next(
        row
        for row in snapshot.relations
        if row.endpoint_semantic_relation == "semantic_restatement"
    )
    actual_nucleus_id_by_alias = {
        row.alias_source_id: row.actual_source_id
        for row in snapshot.source_id_alias_bindings
        if row.source_kind == "nucleus"
    }
    assert tuple(
        actual_nucleus_id_by_alias[item]
        for item in relation.semantic_restatement_unit_nucleus_ids
    ) == ("nucleus:s1", "nucleus:s2", "nucleus:s3")

    ledger = build_semantic_obligation_inventory(snapshot).ledger
    obligation = next(
        row
        for row in ledger["obligations"]
        if relation.source_id in row["relation_ids"]
    )
    assert set(obligation["nucleus_ids"]) == set(
        relation.semantic_restatement_unit_nucleus_ids
    )

    forged_relation = replace(
        relation,
        semantic_restatement_unit_nucleus_ids=(
            relation.semantic_restatement_unit_nucleus_ids[:-1]
        ),
    )
    forged_snapshot = replace(
        snapshot,
        relations=tuple(
            forged_relation if row.source_id == relation.source_id else row
            for row in snapshot.relations
        ),
    )
    issues = validate_semantic_obligation_inventory(
        ledger, source_snapshot=forged_snapshot
    )
    assert "SOURCE_OBSERVATION_PLAN_COMMITMENT_MISMATCH" in issues
    assert "OBLIGATION_CONTENT_MISMATCH" in issues

    forged_witness_commitment = replace(
        snapshot,
        source_semantic_restatement_witness_sha256="f" * 64,
    )
    assert "SOURCE_OBSERVATION_PLAN_COMMITMENT_MISMATCH" in (
        validate_semantic_obligation_inventory(
            ledger,
            source_snapshot=forged_witness_commitment,
        )
    )

    forged_adapter_version = replace(
        snapshot,
        semantic_restatement_witness_adapter_version=(
            "cocolon.emlis.nls_v3.grounded_semantic_restatement_adapter.forged"
        ),
    )
    assert "SEMANTIC_RESTATEMENT_WITNESS_COMMITMENT_INVALID" in (
        validate_semantic_obligation_inventory(
            ledger,
            source_snapshot=forged_adapter_version,
        )
    )

    trusted_builder = inventory_module.build_grounded_semantic_restatement_witness
    trusted_witness = trusted_builder(plan, resolver)
    forged_witness_relation = replace(
        next(
            row
            for row in trusted_witness.relations
            if row.endpoint_semantic_relation == "semantic_restatement"
        ),
        endpoint_semantic_relation="distinct_meanings",
        semantic_restatement_unit_nucleus_ids=(),
    )
    forged_witness = replace(
        trusted_witness,
        relations=tuple(
            forged_witness_relation
            if row.relation_id == forged_witness_relation.relation_id
            else row
            for row in trusted_witness.relations
        ),
    )
    inventory_module.build_grounded_semantic_restatement_witness = (
        lambda _plan, _resolver: forged_witness
    )
    try:
        _raises_code(
            lambda: build_grounded_source_snapshot(
                plan,
                resolver,
                observation_stage_context=stage,
                original_input_bundle=current_input,
            ),
            "SEMANTIC_RESTATEMENT_WITNESS_INVALID",
        )
    finally:
        inventory_module.build_grounded_semantic_restatement_witness = trusted_builder

    two_nucleus_input = _sample("nls3s_b001_0098")["input"]
    _plan, _resolver, _stage, two_nucleus_snapshot = _normal_source(
        two_nucleus_input
    )
    two_nucleus_relation = next(
        row
        for row in two_nucleus_snapshot.relations
        if row.endpoint_semantic_relation == "semantic_restatement"
    )
    assert len(two_nucleus_relation.semantic_restatement_unit_nucleus_ids) == 2

    distinct_input = _sample("nls3s_b001_0017")["input"]
    _plan, _resolver, _stage, distinct_snapshot = _normal_source(distinct_input)
    assert all(
        not row.semantic_restatement_unit_nucleus_ids
        for row in distinct_snapshot.relations
    )


def test_s4_pre_question_preserves_all_unknowns_and_hash_boundaries() -> None:
    current_input = _known_input()
    _normal_plan, _normal_resolver, _normal_stage, normal = _normal_source(current_input)
    _plan, _resolver, _stage, _authority, pre = _pre_source(current_input)

    assert normal.source_observation_plan_sha256 == pre.source_observation_plan_sha256
    assert normal.source_policy_sha256 == pre.source_policy_sha256
    assert normal.source_policy_sha256 == FROZEN_SOURCE_POLICY_SHA256
    assert (
        normal.source_observation_stage_context_sha256
        != pre.source_observation_stage_context_sha256
    )
    assert pre.preserved_unknown_boundary_ids == {
        row.source_id for row in pre.unknowns
    }
    assert pre.answered_unknown_boundary_ids == frozenset()
    ledger = build_semantic_obligation_inventory(pre).ledger
    required_unknowns = {
        unknown_id
        for row in ledger["obligations"]
        if row["kind"] == "unknown_boundary_preservation"
        and row["required"] is True
        for unknown_id in row["unknown_boundary_ids"]
    }
    assert required_unknowns == pre.preserved_unknown_boundary_ids
    assert any(
        row["required"] is True
        and row["kind"] != "unknown_boundary_preservation"
        for row in ledger["obligations"]
    )

    relabelled = replace(pre, observation_stage="normal_observation")
    issues = validate_semantic_obligation_inventory(
        ledger, source_snapshot=relabelled
    )
    assert "OBSERVATION_STAGE_CONTEXT_COMMITMENT_MISMATCH" in issues


def test_s4_frozen_source_policy_rejects_in_process_artifact_drift() -> None:
    _plan, _resolver, _stage, snapshot = _normal_source(_known_input())
    ledger = build_semantic_obligation_inventory(snapshot).ledger
    original = inventory_module.SOURCE_POLICY_ARTIFACT["body_free"]
    inventory_module.SOURCE_POLICY_ARTIFACT["body_free"] = False
    try:
        assert "SOURCE_POLICY_MISMATCH" in validate_semantic_obligation_inventory(
            ledger, source_snapshot=snapshot
        )
        _raises_code(
            lambda: build_semantic_obligation_inventory(snapshot),
            "SOURCE_POLICY_MISMATCH",
        )
    finally:
        inventory_module.SOURCE_POLICY_ARTIFACT["body_free"] = original


def test_s4_refined_context_requires_and_consumes_the_partition_owner() -> None:
    current_input = _sample("nls3s_b001_0031")["input"]
    supplemental = {"thought_text": "結果が読めない点が不安。"}
    plan, resolver = _plan_and_resolver(current_input)
    supplemental_plan, supplemental_resolver = _plan_and_resolver(supplemental)
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
    assert stage["supplemental_answer_bundle_sha256"] == artifact_sha256(supplemental)
    _raises_code(
        lambda: build_grounded_source_snapshot(
            plan,
            resolver,
            observation_stage_context=stage,
            original_input_bundle=current_input,
            trusted_future_authority=authority,
            supplemental_answer_bundle=supplemental,
        ),
        "REFINED_SOURCE_PARTITION_OWNER_UNAVAILABLE",
    )

    partition = build_refined_source_partition(
        plan,
        resolver,
        supplemental_plan,
        supplemental_resolver,
        stage,
        current_input,
        supplemental,
        authority,
    )
    assert validate_refined_source_partition(
        partition,
        plan,
        resolver,
        supplemental_plan,
        supplemental_resolver,
        stage,
        current_input,
        supplemental,
        authority,
    ) == ()
    snapshot = build_grounded_source_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
        trusted_future_authority=authority,
        supplemental_answer_bundle=supplemental,
        refined_source_partition=partition,
    )
    assert snapshot.semantic_source_roles == (
        "original_input",
        "supplemental_answer",
    )
    assert partition["question_need_decision_is_semantic_source"] is False
    assert partition["control_plane_owner_role"] == "original_input"
    assert {
        role for _source_id, role in snapshot.source_role_bindings
    } == {"original_input", "supplemental_answer"}
    assert all(
        role == "original_input"
        for source_id, role in snapshot.source_role_bindings
        if source_id
        in {row.source_id for row in snapshot.reception_opportunities}
    )
    result = build_semantic_obligation_inventory(snapshot)
    assert validate_semantic_obligation_inventory(
        result.ledger, source_snapshot=snapshot
    ) == ()
    assert current_input["thought_text"] not in repr(partition)
    assert supplemental["thought_text"] not in repr(partition)


def test_s4_source_unavailable_is_label_bounded_and_empty_fails_closed() -> None:
    labels_only = {
        "thought_text": "",
        "action_text": "",
        "emotions": [{"type": "不安", "strength": "medium"}],
        "categories": ["仕事"],
    }
    _plan, _resolver, _stage, snapshot = _normal_source(labels_only)
    assert snapshot.response_eligibility == "source_unavailable"
    assert all(
        row.allowed_claim_scope == "selected_label_only"
        and set(row.source_fields) <= {"emotion_details", "emotions", "category"}
        and "NO_LABEL_TO_EVENT_INFERENCE" in row.forbidden_claim_codes
        for row in snapshot.nuclei
    )
    result = build_semantic_obligation_inventory(snapshot)
    assert validate_semantic_obligation_inventory(
        result.ledger, source_snapshot=snapshot
    ) == ()

    _plan, _resolver, _stage, empty = _normal_source({})
    assert empty.response_eligibility == "source_unavailable"
    _raises_code(
        lambda: build_semantic_obligation_inventory(empty),
        "OBLIGATION_SOURCE_UNAVAILABLE",
    )


def test_s4_self_denial_keeps_identity_boundary_and_concrete_action_distinct() -> None:
    current_input = {
        "thought_text": "私は何をしてもだめだ。",
        "action_text": "それでも相談先を一つ調べた。",
        "emotions": [{"type": "悲しみ", "strength": "strong"}],
        "categories": ["人生"],
    }
    _plan, _resolver, _stage, snapshot = _normal_source(current_input)
    result = build_semantic_obligation_inventory(snapshot)
    assert validate_semantic_obligation_inventory(
        result.ledger, source_snapshot=snapshot
    ) == ()
    required = [
        row for row in result.ledger["obligations"]
        if row["required"] is True
    ]
    assert {
        "intention_or_next_action",
        "self_denial_boundary",
        "bounded_counterposition",
        "bound_emlis_reception",
    } <= {row["kind"] for row in required}
    self_denial = next(
        row for row in required if row["kind"] == "self_denial_boundary"
    )
    assert "IDENTITY_CLAIM_NOT_FACT" in self_denial["forbidden_claim_codes"]
    assert "safety_policy" in self_denial["source_authority_codes"]


def test_s4_separate_safety_owner_is_delegated() -> None:
    current_input = {
        "thought_text": "今すぐ死にたい。方法も考えている。",
        "action_text": "",
        "emotions": [{"type": "悲しみ", "strength": "strong"}],
        "categories": ["人生"],
    }
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    stage = build_observation_stage_context(
        stage="normal_observation", original_input_bundle=current_input
    )
    _raises_code(
        lambda: build_grounded_source_snapshot(
            plan,
            resolver,
            observation_stage_context=stage,
            original_input_bundle=current_input,
        ),
        "SEPARATE_SAFETY_OWNER",
    )


def test_s4_inventory_bound_is_exact_step1_formula_and_components_are_strict() -> None:
    counts = {
        "evidence_span_count": 1,
        "text_evidence_span_count": 1,
        "nucleus_count": 1,
        "relation_count": 0,
        "unknown_boundary_count": 0,
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": 0,
        "reception_opportunity_count": 0,
    }
    bound = obligation_inventory_upper_bound(counts)
    assert bound == (4 * 1 + 0 + 0) * (1 + 0 + 1) * (0 + 2) == 16
    assert bound != 12
    assert validate_obligation_inventory_count(counts, bound - 1) == ()
    assert validate_obligation_inventory_count(counts, bound) == ()
    assert validate_obligation_inventory_count(counts, bound + 1) == (
        "OBLIGATION_INVENTORY_OVERFLOW",
    )
    for field, invalid_value in (
        ("text_evidence_span_count", 2),
        ("nucleus_count", 2),
        ("relation_count", 1),
        ("unknown_boundary_count", 12),
        ("safety_policy_count", 0),
        ("safety_required_boundary_code_count", 10),
        ("reception_opportunity_count", 5),
    ):
        mutation = {**counts, field: invalid_value}
        _raises_code(
            lambda mutation=mutation: obligation_inventory_upper_bound(mutation),
            "SOURCE_RESOURCE_COUNTS_INVALID",
        )


def _cross_role_snapshot_api_or_red():
    required = (
        "REFINED_SOURCE_SNAPSHOT_SCHEMA",
        "CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA",
        "CrossRoleSemanticDepthComponentBinding",
        "CrossRoleSemanticDepthEquivalence",
    )
    missing = tuple(
        name for name in required if not hasattr(inventory_module, name)
    )
    snapshot_fields = {
        row.name for row in fields(inventory_module.GroundedSourceSnapshot)
    }
    required_snapshot_fields = {
        "refined_source_snapshot_schema_version",
        "cross_role_semantic_restatement_witness_sha256",
        "cross_role_semantic_depth_equivalence",
    }
    missing_snapshot_fields = tuple(
        sorted(required_snapshot_fields - snapshot_fields)
    )
    if missing or missing_snapshot_fields:
        details = (
            *(f"attribute:{name}" for name in missing),
            *(f"snapshot_field:{name}" for name in missing_snapshot_fields),
        )
        pytest.fail(
            f"{_CROSS_ROLE_SNAPSHOT_RED}:{','.join(details)}",
            pytrace=False,
        )
    return (
        inventory_module.CrossRoleSemanticDepthComponentBinding,
        inventory_module.CrossRoleSemanticDepthEquivalence,
    )


def test_s4_cross_role_refined_snapshot_lineage_alias_and_tamper_red() -> None:
    component_type, equivalence_type = _cross_role_snapshot_api_or_red()
    assert (
        inventory_module.REFINED_SOURCE_SNAPSHOT_SCHEMA
        == _REFINED_SOURCE_SNAPSHOT_SCHEMA
    )
    assert (
        inventory_module.CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA
        == _CROSS_ROLE_DEPTH_SCHEMA
    )
    assert tuple(row.name for row in fields(component_type)) == (
        _CROSS_ROLE_DEPTH_COMPONENT_FIELDS
    )
    assert tuple(row.name for row in fields(equivalence_type)) == (
        _CROSS_ROLE_DEPTH_EQUIVALENCE_FIELDS
    )

    policy = inventory_module.SOURCE_POLICY_ARTIFACT
    assert policy["cross_role_semantic_restatement_witness_schema"] == (
        _CROSS_ROLE_WITNESS_SCHEMA
    )
    assert policy["cross_role_semantic_restatement_adapter_version"] == (
        _CROSS_ROLE_ADAPTER_VERSION
    )
    assert policy["cross_role_semantic_restatement_effect_scope"] == (
        _CROSS_ROLE_EFFECT_SCOPE
    )
    assert policy["cross_role_semantic_depth_equivalence_schema"] == (
        _CROSS_ROLE_DEPTH_SCHEMA
    )
    assert policy["refined_source_snapshot_schema"] == (
        _REFINED_SOURCE_SNAPSHOT_SCHEMA
    )
    refined_commitment = inventory_module._refined_plan_commitment_material(
        partition_sha256="1" * 64,
        original_plan_sha256="2" * 64,
        supplemental_plan_sha256="3" * 64,
        role_bindings=(
            ("source:original", "original_input"),
            ("source:supplemental", "supplemental_answer"),
        ),
        cross_role_semantic_restatement_witness_sha256="4" * 64,
    )
    assert refined_commitment == {
        "schema_version": _REFINED_SOURCE_SNAPSHOT_SCHEMA,
        "refined_source_partition_sha256": "1" * 64,
        "original_source_observation_plan_sha256": "2" * 64,
        "supplemental_source_observation_plan_sha256": "3" * 64,
        "source_role_bindings": [
            ["source:original", "original_input"],
            ["source:supplemental", "supplemental_answer"],
        ],
        "cross_role_semantic_restatement_witness_sha256": "4" * 64,
        "body_free": True,
    }

    from test_emlis_nls_v3_s5_content_selection_stage_context import (
        _known_input as _s5_known_input,
        _normal_result,
        _pre_result,
        _refined_result,
    )

    _normal_stage, normal_snapshot, normal_result = _normal_result(
        _s5_known_input()
    )
    _pre_stage, pre_snapshot, pre_result = _pre_result(_s5_known_input())
    assert normal_snapshot.refined_source_snapshot_schema_version is None
    assert normal_snapshot.cross_role_semantic_depth_equivalence is None
    assert normal_snapshot.cross_role_semantic_restatement_witness_sha256 is None
    assert pre_snapshot.refined_source_snapshot_schema_version is None
    assert pre_snapshot.cross_role_semantic_depth_equivalence is None
    assert pre_snapshot.cross_role_semantic_restatement_witness_sha256 is None

    (
        _current_input,
        _supplemental,
        partition,
        partition_issues,
        snapshot,
        result,
        _content_plan,
    ) = _refined_result()
    assert partition_issues == ()
    assert partition["cross_source_bindings"] == []
    assert partition["question_need_decision_is_semantic_source"] is False
    assert partition["control_plane_owner_role"] == "original_input"
    assert snapshot.refined_source_snapshot_schema_version == (
        _REFINED_SOURCE_SNAPSHOT_SCHEMA
    )
    equivalence = snapshot.cross_role_semantic_depth_equivalence
    assert type(equivalence) is equivalence_type
    assert equivalence.schema_version == _CROSS_ROLE_DEPTH_SCHEMA
    assert equivalence.source_witness_schema_version == (
        _CROSS_ROLE_WITNESS_SCHEMA
    )
    assert equivalence.source_witness_adapter_version == (
        _CROSS_ROLE_ADAPTER_VERSION
    )
    assert equivalence.source_witness_sha256 == (
        snapshot.cross_role_semantic_restatement_witness_sha256
    )
    assert equivalence.effect_scope == _CROSS_ROLE_EFFECT_SCOPE
    assert equivalence.body_free is True
    assert len(equivalence.component_bindings) >= 2
    assert equivalence.equivalence_sha256 == artifact_sha256(
        {
            "schema_version": equivalence.schema_version,
            "source_witness_schema_version": (
                equivalence.source_witness_schema_version
            ),
            "source_witness_adapter_version": (
                equivalence.source_witness_adapter_version
            ),
            "source_witness_sha256": equivalence.source_witness_sha256,
            "component_bindings": [
                asdict(row) for row in equivalence.component_bindings
            ],
            "effect_scope": equivalence.effect_scope,
            "body_free": equivalence.body_free,
        }
    )

    role_by_id = dict(snapshot.source_role_bindings)
    assert all(
        type(row) is component_type
        and row.component_kind in {"nucleus", "relation", "unknown_boundary"}
        and row.original_source_role == "original_input"
        and row.original_source_kind == row.component_kind
        and row.supplemental_source_role == "supplemental_answer"
        and row.supplemental_source_kind == row.component_kind
        and role_by_id[row.original_source_id] == "original_input"
        and role_by_id[row.supplemental_source_id] == "supplemental_answer"
        and len(row.canonical_typed_component_sha256) == 64
        for row in equivalence.component_bindings
    )
    assert snapshot.semantic_source_roles == (
        "original_input",
        "supplemental_answer",
    )
    assert validate_semantic_obligation_inventory(
        result.ledger,
        source_snapshot=snapshot,
    ) == ()

    parent_drift_snapshots = (
        replace(snapshot, refined_source_partition_sha256="0" * 64),
        replace(
            snapshot,
            refined_original_source_observation_plan_sha256="0" * 64,
        ),
        replace(
            snapshot,
            refined_supplemental_source_observation_plan_sha256="0" * 64,
        ),
    )
    for drifted in parent_drift_snapshots:
        drift_issues = set(
            validate_semantic_obligation_inventory(
                result.ledger,
                source_snapshot=drifted,
            )
        )
        assert "SOURCE_ORIGIN_AUTHORITY_REQUIRED" in drift_issues
        assert (
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH"
            in drift_issues
        )

    stage_binding = snapshot.observation_stage_source_binding
    for drifted_binding in (
        replace(stage_binding, original_input_bundle_sha256="0" * 64),
        replace(stage_binding, supplemental_answer_bundle_sha256="0" * 64),
    ):
        stage_drift = replace(
            snapshot,
            observation_stage_source_binding=drifted_binding,
        )
        stage_issues = set(
            validate_semantic_obligation_inventory(
                result.ledger,
                source_snapshot=stage_drift,
            )
        )
        assert "SOURCE_ORIGIN_AUTHORITY_REQUIRED" in stage_issues
        assert "OBSERVATION_STAGE_CONTEXT_COMMITMENT_MISMATCH" in stage_issues

    stage_hash_drift = replace(
        snapshot,
        source_observation_stage_context_sha256="0" * 64,
    )
    stage_hash_issues = set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=stage_hash_drift,
        )
    )
    assert "SOURCE_ORIGIN_AUTHORITY_REQUIRED" in stage_hash_issues
    assert "OBSERVATION_STAGE_CONTEXT_COMMITMENT_MISMATCH" in stage_hash_issues

    active_nonstance_roles = {
        ref["source_role"]
        for row in result.ledger["obligations"]
        if row["kind"] != "bound_emlis_reception"
        for ref in row["source_refs"]
    }
    assert active_nonstance_roles == {
        "original_input",
        "supplemental_answer",
    }
    assert all(
        {
            ref["source_role"] for ref in row["source_refs"]
        } == {"original_input"}
        for row in result.ledger["obligations"]
        if row["kind"] == "bound_emlis_reception"
    )

    missing = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=None,
    )
    missing_issues = set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=missing,
        )
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID" in (
        missing_issues
    )
    assert "SOURCE_ORIGIN_AUTHORITY_REQUIRED" in set(
        inventory_module._snapshot_authority_issues(missing)
    )

    injected = replace(
        normal_snapshot,
        refined_source_snapshot_schema_version=(
            _REFINED_SOURCE_SNAPSHOT_SCHEMA
        ),
        cross_role_semantic_restatement_witness_sha256=(
            equivalence.source_witness_sha256
        ),
        cross_role_semantic_depth_equivalence=equivalence,
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID" in set(
        validate_semantic_obligation_inventory(
            normal_result.ledger,
            source_snapshot=injected,
        )
    )

    wrong_effect = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            effect_scope="OBLIGATION_SELECTION",
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=wrong_effect,
        )
    )

    equivalence_tamper_cases = (
        (
            {"schema_version": "forged"},
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID",
        ),
        (
            {"source_witness_schema_version": "forged"},
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH",
        ),
        (
            {"source_witness_adapter_version": "forged"},
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH",
        ),
        (
            {"source_witness_sha256": "0" * 64},
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH",
        ),
        (
            {"body_free": False},
            "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED",
        ),
    )
    for mutation, expected_code in equivalence_tamper_cases:
        tampered = replace(
            snapshot,
            cross_role_semantic_depth_equivalence=replace(
                equivalence,
                **mutation,
            ),
        )
        assert expected_code in set(
            validate_semantic_obligation_inventory(
                result.ledger,
                source_snapshot=tampered,
            )
        )

    first = equivalence.component_bindings[0]
    removed_binding = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            component_bindings=equivalence.component_bindings[:-1],
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=removed_binding,
        )
    )

    duplicated_binding = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            component_bindings=(
                *equivalence.component_bindings,
                first,
            ),
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=duplicated_binding,
        )
    )

    reordered_binding = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            component_bindings=tuple(
                reversed(equivalence.component_bindings)
            ),
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=reordered_binding,
        )
    )

    wrong_equivalence_hash = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            equivalence_sha256="0" * 64,
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=wrong_equivalence_hash,
        )
    )

    wrong_snapshot_witness_hash = replace(
        snapshot,
        cross_role_semantic_restatement_witness_sha256="0" * 64,
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=wrong_snapshot_witness_hash,
        )
    )

    wrong_alias = replace(
        snapshot,
        cross_role_semantic_depth_equivalence=replace(
            equivalence,
            component_bindings=(
                replace(
                    first,
                    supplemental_source_id=first.original_source_id,
                ),
                *equivalence.component_bindings[1:],
            ),
        ),
    )
    assert "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH" in set(
        validate_semantic_obligation_inventory(
            result.ledger,
            source_snapshot=wrong_alias,
        )
    )
    assert validate_semantic_obligation_inventory(
        pre_result.ledger,
        source_snapshot=pre_snapshot,
    ) == ()
