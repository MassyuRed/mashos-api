# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed withdrawal and replacement packet after the actual-device failure.

The historical GA7/GA8 technical artifacts remain inspectable, but none of
those artifacts may authorize progression after the visible two-stage and
mechanical-restatement failure was observed on the device.
"""

import hashlib
import json
from pathlib import Path


_TEST_ROOT = Path(__file__).resolve().parent
_FIXTURE_ROOT = _TEST_ROOT / "fixtures"
_WITHDRAWAL = _FIXTURE_ROOT / "gatea_ga7_ga8_actual_device_withdrawal_20260712.json"
_RECHECK = _FIXTURE_ROOT / "gatea_mandatory_two_stage_exact8_recheck_20260712.json"
_HISTORICAL_REVIEW = _FIXTURE_ROOT / "gate0_rr_gatea_ga7_karen_review_20260712.json"
_HISTORICAL_DECISION = _FIXTURE_ROOT / "gate0_rr_gatea_ga8_decision_20260712.json"
_HISTORICAL_PACKET = _FIXTURE_ROOT / "gate0_rr_gatea_ga8_exact8_20260712.json"
_HISTORICAL_LINK = _FIXTURE_ROOT / "gate0_rr_gatea_ga8_final_link_20260712.json"
_HISTORICAL_VALIDATION = _FIXTURE_ROOT / "gate0_rr_gatea_ga8_validation_20260712.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_json(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def test_actual_device_failure_withdraws_every_downstream_ga7_ga8_authority() -> None:
    withdrawal = _load(_WITHDRAWAL)
    review = _load(_HISTORICAL_REVIEW)
    decision = _load(_HISTORICAL_DECISION)
    packet = _load(_HISTORICAL_PACKET)
    final_link = _load(_HISTORICAL_LINK)
    validation = _load(_HISTORICAL_VALIDATION)

    assert withdrawal["withdrawal_effective"] is True
    assert withdrawal["progression"] == {
        "gate0_local_pass": False,
        "next_action_ref": "mandatory_two_stage_current_input_surface_repair_then_exact8_device_recheck",
        "old_exact8_packet_valid": False,
        "p5_formal_24_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
    }

    assert review["valid_for_progression"] is False
    assert review["gatea_local_pass"] is False
    assert review["valid_local_review_count"] == 0
    assert "reviews" not in review
    assert len(review["historical_reviews"]) == 16

    assert decision["valid_for_progression"] is False
    assert decision["gate0_local_pass"] is False
    assert decision["product_readfeel_valid"] is False
    assert decision["decision_code"] == "GATE0_LOCAL_PASS_WITHDRAWN_ACTUAL_DEVICE_FAILURE"

    assert packet["valid_for_progression"] is False
    assert packet["packet_status"] == "withdrawn_after_actual_device_failure"
    assert final_link["valid_for_progression"] is False
    assert final_link["final_link_status"] == "withdrawn_after_actual_device_failure"
    assert validation["technical_validation_all_pass"] is True
    assert validation["product_validation_pass"] is False
    assert validation["validation_all_pass"] is False
    assert validation["valid_for_progression"] is False


def test_withdrawal_preserves_pre_withdrawal_hashes_without_body_leak() -> None:
    withdrawal = _load(_WITHDRAWAL)
    expected = {
        "gate0_rr_gatea_ga7_karen_review_20260712.json": "77257163782bc3edb899a75b27dc80216c46ed88f48576e8f0ba088ea28c3548",
        "gate0_rr_gatea_ga8_decision_20260712.json": "ba861e8f68a990908b0904576070eb1f19b5a47c3fa2d18bc85c1cf551f69680",
        "gate0_rr_gatea_ga8_exact8_20260712.json": "43a402f6d4c802400ac7fb5065c899c51ac1ffa85e1d787331f87900a507ba8c",
        "gate0_rr_gatea_ga8_final_link_20260712.json": "a44f92e02effd7898c7aab4761fec4ce86695e257fe732410b0119f3bd0f73e6",
        "gate0_rr_gatea_ga8_validation_20260712.json": "e17a57fef4a6d8cf17b56fb97563ff716b6b8d3379d8d3f2e38bacc6aee2ba3f",
    }
    actual = {
        row["file_ref"]: row["pre_withdrawal_sha256"]
        for row in withdrawal["superseded_artifacts"]
    }
    assert actual == expected
    assert withdrawal["raw_input_included"] is False
    assert withdrawal["returned_surface_included"] is False
    assert withdrawal["comment_text_included"] is False


def test_replacement_exact8_is_evidence_request_not_progression_authority() -> None:
    packet = _load(_RECHECK)
    assert packet["packet_status"] == "ready_waiting_for_actual_device_visible_surface_evidence"
    assert packet["valid_for_progression"] is False
    assert packet["local_status"] == {
        "actual_device_evidence_status": "not_started",
        "p5_formal_24_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "product_readfeel_status": "not_evaluated",
        "structural_candidate_ready": True,
    }
    assert len(packet["case_order"]) == len(set(packet["case_order"])) == 8
    assert packet["required_device_evidence_fields"] == [
        "generation_path",
        "composer_source",
        "semantic_quality_gate",
        "public_reply_path_connected",
        "two_stage_contract_gate",
        "mechanical_restatement_gate",
        "runtime_visible_contract_guard",
        "visible_surface_sha256",
        "expected_local_surface_sha256",
    ]


def test_replacement_exact8_hashes_remain_immutable_historical_failure_evidence() -> None:
    packet = _load(_RECHECK)
    assert hashlib.sha256(_RECHECK.read_bytes()).hexdigest() == (
        "8de881fb66577efe1c30556754ca178c211737f8e1218f0a5825bba9a4831e6e"
    )
    assert packet["valid_for_progression"] is False
    assert packet["progression_authority"] == (
        "none_until_device_evidence_matches_local_visible_surface"
    )
    for case in packet["cases"]:
        assert _sha256_json(case["exact_current_input"]) == case["current_input_sha256"]
        assert len(case["local_comment_sha256"]) == 64
        assert case["local_comment_character_count"] > 0
        assert case["local_comment_nonempty_line_count"] >= 2
