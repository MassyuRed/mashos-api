# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest

from helpers.emlis_ai_gate0_r9_r10_boundary import (
    GATE0_EXACT8_CASE_IDS,
    GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED,
    GATE0_REPAIR_RETURN_STOPPED,
    GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION,
    Gate0DevicePacketBlocked,
    Gate0ValidationEvidence,
    build_exact8_device_packet,
    build_gate0_local_decision,
)
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from helpers.emlis_ai_grounded_observation_i7_readfeel import (
    I7KarenLocalReview,
    assess_i7_local_surface,
    validate_i7_karen_local_reviews,
)
from emlis_ai_reply_service import render_emlis_ai_reply


_RECEIPT_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "emlis_gate0_r8_karen_local_review_receipt_20260711.json"
)
_CASES = (
    *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
    *GROUND_OBSERVATION_I6_BLIND_CASES,
)


def _load_receipt() -> tuple[dict[str, object], tuple[I7KarenLocalReview, ...]]:
    payload = json.loads(_RECEIPT_PATH.read_text(encoding="utf-8"))
    snapshot = str(payload["snapshot_fingerprint"])
    reviews = tuple(
        I7KarenLocalReview(
            snapshot_fingerprint=snapshot,
            **review,
        )
        for review in payload["reviews"]
    )
    return payload, reviews


def _automated_assessments():
    output = []
    for case in _CASES:
        reply = asyncio.run(
            render_emlis_ai_reply(
                user_id="gate0-r8-boundary-test",
                subscription_tier="free",
                current_input=case.as_current_input(),
            )
        )
        output.append(
            assess_i7_local_surface(
                case_id=case.case_id,
                surface_text=reply.comment_text,
                grounded_meta=reply.meta["grounded_observation"],
            )
        )
    return tuple(output)


def _passing_validation(snapshot_fingerprint: str) -> Gate0ValidationEvidence:
    return Gate0ValidationEvidence(
        schema_version=GATE0_VALIDATION_EVIDENCE_SCHEMA_VERSION,
        source_snapshot_fingerprint=snapshot_fingerprint,
        targeted_suites_green=True,
        targeted_result_ref="gate0_targeted_v2",
        safety_public_contract_green=True,
        safety_public_result_ref="gate0_safety_public_v2",
        rn_contract_green=True,
        rn_result_ref="gate0_rn_contract_v2",
        full_collect_success=True,
        full_collect_return_code=0,
        collected_test_count=1,
        collection_error_refs=(),
        full_backend_green=True,
        full_backend_return_code=0,
        full_backend_result_ref="gate0_full_backend_v2",
        unclassified_failure_refs=(),
    )


def test_actual_karen_receipt_is_body_free_complete_and_requires_repair() -> None:
    payload, reviews = _load_receipt()
    case_ids = tuple(case.case_id for case in _CASES)
    assert validate_i7_karen_local_reviews(reviews, expected_case_ids=case_ids) == ()
    assert payload["case_count"] == len(reviews) == 16
    assert payload["local_human_pass_count"] == 7
    assert payload["repair_required_count"] == 9
    assert payload["hard_fatal_count"] == 0
    assert payload["gate0_local_pass"] is False
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in ("current_input", "comment_text", "surface_text", "returned_surface"):
        assert f'"{forbidden}"' not in dumped


def test_gate0_binary_decision_blocks_exact8_for_actual_review_result() -> None:
    payload, reviews = _load_receipt()
    assessments = _automated_assessments()
    assert all(item.candidate_status == "candidate_pass" for item in assessments)
    decision = build_gate0_local_decision(
        local_assessments=assessments,
        actual_local_reviews=reviews,
        validation_evidence=_passing_validation(str(payload["snapshot_fingerprint"])),
        expected_source_snapshot_fingerprint=str(payload["snapshot_fingerprint"]),
    )
    assert decision["decision_code"] == GATE0_REPAIR_RETURN_STOPPED
    assert decision["gate0_local_pass"] is False
    assert decision["local_human_pass_count"] == 7
    assert decision["repair_required_count"] == 9
    assert decision["exact8_packet_generation_allowed"] is False
    with pytest.raises(Gate0DevicePacketBlocked, match="gate0_local_pass_required"):
        build_exact8_device_packet(
            gate0_decision=decision,
            cases=_CASES,
            local_comment_sha256_by_case={},
        )


def test_exact8_builder_uses_frozen_helpers_and_order_only_after_pass() -> None:
    payload, actual_reviews = _load_receipt()
    assessments = _automated_assessments()
    explicit_pass_reviews = tuple(
        replace(
            review,
            required_nucleus_retained="pass",
            required_relation_direction=(
                "not_applicable"
                if review.case_id in {"A", "I6-S01", "I6-S02", "I6-S03"}
                else "pass"
            ),
            lexical_fidelity="pass",
            whole_input_balance="pass",
            human_follow_fit="pass",
            natural_japanese="pass",
            non_template_readfeel="pass",
            safety_boundary=(
                "pass" if review.case_id in {"D", "I6-D01", "I6-D02", "I6-D03"}
                else "not_applicable"
            ),
            wants_more_input_candidate="pass",
            fatal_reason_refs=(),
            verdict="local_human_pass",
        )
        for review in actual_reviews
    )
    hypothetical_pass = build_gate0_local_decision(
        local_assessments=assessments,
        actual_local_reviews=explicit_pass_reviews,
        validation_evidence=_passing_validation(str(payload["snapshot_fingerprint"])),
        expected_source_snapshot_fingerprint=str(payload["snapshot_fingerprint"]),
    )
    assert hypothetical_pass["decision_code"] == GATE0_LOCAL_PASS_DEVICE_PACKET_READY_STOPPED
    hashes = {
        case.case_id: hashlib.sha256(case.case_id.encode("utf-8")).hexdigest()
        for case in _CASES
    }
    packet = build_exact8_device_packet(
        gate0_decision=hypothetical_pass,
        cases=_CASES,
        local_comment_sha256_by_case=hashes,
    )
    assert tuple(packet["case_order"]) == GATE0_EXACT8_CASE_IDS
    assert tuple(item["case_id"] for item in packet["cases"]) == GATE0_EXACT8_CASE_IDS
    assert packet["arbitrary_input_allowed"] is False
    assert packet["screenshot_local_only"] is True
    assert packet["p5_formal_24_started_here"] is False
    assert packet["p8_started_here"] is False


def test_actual_failed_gate_does_not_materialize_an_exact8_packet_fixture() -> None:
    packet_path = Path(__file__).parent / "fixtures" / "emlis_gate0_r10_exact8_device_packet_20260711.json"
    assert not packet_path.exists()
