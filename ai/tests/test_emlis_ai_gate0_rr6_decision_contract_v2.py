# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
import inspect

import pytest

from helpers.emlis_ai_gate0_r9_r10_boundary import (
    GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED,
    GATE0_REPAIR_RETURN_STOPPED,
    GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED,
    GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION,
    Gate0DevicePacketBlocked,
    Gate0ValidationEvidence,
    build_exact8_device_packet,
    build_gate0_local_decision,
)
from helpers.emlis_ai_grounded_observation_i7_readfeel import (
    I7KarenLocalReview,
    I7LocalReadFeelAssessment,
)


_SNAPSHOT = "a" * 64
_CASE_IDS = tuple(f"case-{index:02d}" for index in range(1, 17))


def _assessments() -> tuple[I7LocalReadFeelAssessment, ...]:
    return tuple(
        I7LocalReadFeelAssessment(
            case_id=case_id,
            review_kind="local_product_read_candidate",
            axis_refs=(),
            fatal_reason_refs=(),
            character_count=1,
            line_count=1,
            candidate_status="candidate_pass",
        )
        for case_id in _CASE_IDS
    )


def _reviews(*, repair: bool = False) -> tuple[I7KarenLocalReview, ...]:
    return tuple(
        I7KarenLocalReview(
            case_id=case_id,
            snapshot_fingerprint=_SNAPSHOT,
            required_nucleus_retained="pass",
            required_relation_direction="pass",
            lexical_fidelity="pass",
            whole_input_balance="pass",
            human_follow_fit="fail" if repair and index == 1 else "pass",
            natural_japanese="pass",
            non_template_readfeel="pass",
            safety_boundary="not_applicable",
            wants_more_input_candidate="fail" if repair and index == 1 else "pass",
            fatal_reason_refs=("human_follow_role_surface_mismatch",)
            if repair and index == 1
            else (),
            verdict="repair_required" if repair and index == 1 else "local_human_pass",
        )
        for index, case_id in enumerate(_CASE_IDS, start=1)
    )


def _evidence() -> Gate0ValidationEvidence:
    return Gate0ValidationEvidence(
        schema_version=GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION,
        source_snapshot_fingerprint=_SNAPSHOT,
        targeted_suites_green=True,
        targeted_result_ref="gate0_targeted_v2",
        safety_public_contract_green=True,
        safety_public_result_ref="gate0_safety_public_v2",
        rn_contract_green=True,
        rn_result_ref="gate0_rn_v2",
        full_collect_success=True,
        full_collect_return_code=0,
        collected_test_count=100,
        collection_error_refs=(),
        full_backend_green=True,
        full_backend_return_code=0,
        full_backend_result_ref="gate0_full_backend_v2",
        unclassified_failure_refs=(),
    )


def _decision(
    evidence: Gate0ValidationEvidence,
    *,
    repair: bool = False,
    expected_snapshot: str = _SNAPSHOT,
):
    return build_gate0_local_decision(
        local_assessments=_assessments(),
        actual_local_reviews=_reviews(repair=repair),
        validation_evidence=evidence,
        expected_source_snapshot_fingerprint=expected_snapshot,
    )


def test_rr6_signature_requires_validation_object_and_expected_snapshot() -> None:
    parameters = inspect.signature(build_gate0_local_decision).parameters
    assert "validation_evidence" in parameters
    assert "expected_source_snapshot_fingerprint" in parameters
    assert "affected_suites_green" not in parameters
    assert "unclassified_failure_count" not in parameters
    with pytest.raises(TypeError):
        build_gate0_local_decision(  # type: ignore[call-arg]
            local_assessments=_assessments(),
            actual_local_reviews=_reviews(),
        )


def test_rr6_all_validation_and_review_inputs_are_required_for_pass() -> None:
    decision = _decision(_evidence())
    assert decision["decision_code"] == GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED
    assert decision["gate0_local_pass"] is True
    assert decision["blocker_refs"] == []
    assert decision["validation"]["full_collect_success"] is True
    assert decision["validation"]["collection_error_count"] == 0
    assert decision["validation"]["full_backend_green"] is True


def test_rr6_collection_error_blocks_pass_even_if_collect_boolean_is_true() -> None:
    evidence = replace(
        _evidence(),
        collection_error_refs=("collection_error:obsolete_private_import",),
    )
    decision = _decision(evidence)
    assert decision["decision_code"] == GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED
    assert decision["gate0_local_pass"] is False
    assert "full_collect_evidence_inconsistent" in decision["blocker_refs"]
    assert "collection_error:obsolete_private_import" in decision["blocker_refs"]


def test_rr6_full_backend_not_run_blocks_pass() -> None:
    evidence = replace(
        _evidence(),
        full_backend_green=False,
        full_backend_return_code=-1,
    )
    decision = _decision(evidence)
    assert decision["decision_code"] == GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED
    assert "full_backend_not_green" in decision["blocker_refs"]


def test_rr6_snapshot_mismatch_blocks_decision_and_exact8() -> None:
    decision = _decision(_evidence(), expected_snapshot="b" * 64)
    assert decision["decision_code"] == GATE0_TEST_OR_CONTRACT_BLOCKED_STOPPED
    assert "validation_source_snapshot_mismatch" in decision["blocker_refs"]
    assert "review_validation_source_snapshot_mismatch" in decision["blocker_refs"]
    with pytest.raises(Gate0DevicePacketBlocked):
        build_exact8_device_packet(
            gate0_decision=decision,
            cases=(),
            local_comment_sha256_by_case={},
        )


def test_rr6_repair_decision_keeps_validation_blockers_separate() -> None:
    evidence = replace(
        _evidence(),
        full_collect_success=False,
        full_collect_return_code=1,
        collected_test_count=0,
        collection_error_refs=("collection_error:bounded_repair_step7",),
        full_backend_green=False,
        full_backend_return_code=1,
    )
    decision = _decision(evidence, repair=True)
    assert decision["decision_code"] == GATE0_REPAIR_RETURN_STOPPED
    assert decision["repair_required_count"] == 1
    assert "collection_error:bounded_repair_step7" in decision["blocker_refs"]
    assert "full_backend_not_green" in decision["blocker_refs"]
