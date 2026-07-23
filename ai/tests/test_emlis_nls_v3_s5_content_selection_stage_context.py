# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 5 Content Selection / Observation Stage Context acceptance tests."""

from copy import deepcopy
from dataclasses import replace
import inspect
import json
from pathlib import Path

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


def _refined_result(current_input: dict[str, object] | None = None):
    if current_input is None:
        current_input = _known_input()
    supplemental = {
        "thought_text": current_input["thought_text"],
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
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


def _codes(issues) -> set[str]:
    return {issue.code for issue in issues}


def _resign_content(value: dict[str, object]) -> None:
    value["content_plan_id"] = derive_content_id(
        "nls3cp_", value, "content_plan_id"
    )


def _resign_ledger(value: dict[str, object]) -> None:
    value["ledger_id"] = derive_content_id("nls3obl_", value, "ledger_id")


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
    current_input = {
        "thought_text": "私は何をしてもだめだ。",
        "action_text": "それでも相談先を一つ調べた。",
        "emotions": [{"type": "悲しみ", "strength": "strong"}],
        "categories": ["人生"],
    }
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
