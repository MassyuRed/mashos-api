# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_response_contract import (
    EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY,
    build_emlis_internal_response_contract,
)

VISIBLE_COMMENT = "Phase20-7 public comment_text only. Generated wording is not exact-fixtured."
SECRET_RAW_INPUT = "Phase20-7 raw input must not leak"
SECRET_EVIDENCE = "Phase20-7 evidence text must not leak"
SECRET_INTERNAL_COMMENT = "Phase20-7 internal generated body must not leak"

FORBIDDEN_PUBLIC_BOUNDARY_KEYS = {
    "internal_response_contract",
    "internal_response_contract_schema_version",
    "response_kind",
    "public_input_feedback_allowed",
    "comment_text_required",
    "safety_triage_kind",
    "grounding_scope",
    "repair_attempts",
    "visible_material_slots",
    "unknown_slots",
    "material_quality",
    "generic_relation_material_ids",
    "reception_mode_id",
    "selected_reception_mode_id",
    "two_stage_reception_mode_id",
    "reception_mode_family",
    "mode_id",
    "mode",
    "mode_specific_rejection_reasons",
    "observation_text",
    "reception_text",
    "evidence_text",
}
FORBIDDEN_PUBLIC_BOUNDARY_FRAGMENTS = {
    "normal_observation",
    "limited_grounding_observation",
    "self_denial_safe_state_answer",
    "safety_support_required",
    "safety_blocked_emergency",
    "infrastructure_error",
    "self_understanding_learning_shift",
    "relationship_gratitude_recovery",
    "generic_sentence_plan_surface",
    SECRET_RAW_INPUT,
    SECRET_EVIDENCE,
    SECRET_INTERNAL_COMMENT,
}


def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_keys(child))
    return keys


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _response_body(comment_text: str, public_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {"comment_text": comment_text, "emlis_ai": dict(public_meta or {})}
    return {
        "status": "ok",
        "id": "phase20-7-emotion-log",
        "created_at": "2026-05-31T00:00:00.000000+00:00",
        "input_feedback": feedback,
    }


def _internal_meta_with_contract(response_kind: str, *, legacy_status: str = "rejected") -> dict[str, Any]:
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": legacy_status,
        "rejection_reasons": ["self_understanding_learning_shift"],
        EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY: build_emlis_internal_response_contract(
            response_kind,
            reason="phase20_7_public_boundary_contract_bridge",
        ),
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": "relationship_gratitude_recovery",
            "composer_status": "generated",
            "response_kind": response_kind,
            "comment_text": SECRET_INTERNAL_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
        },
        "two_stage_reception_gate": {
            "schema_version": "cocolon.emlis_ai_two_stage_reception.cross_gate.v1",
            "evaluated": True,
            "active": True,
            "connected": True,
            "passed": True,
            "blocked": False,
            "terminal_surface_block": False,
            "reception_mode_id": "relationship_gratitude_recovery",
            "reception_mode_family": "phase19_case_mode",
            "mode_specific_rejection_reasons": ["self_understanding_learning_shift"],
            "rejection_reasons": ["relationship_gratitude_recovery"],
            "comment_text": SECRET_INTERNAL_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
            "raw_text": SECRET_EVIDENCE,
            "observation_text": SECRET_INTERNAL_COMMENT,
            "reception_text": SECRET_INTERNAL_COMMENT,
        },
        "response_kind": response_kind,
        "safety_triage_kind": "safe_observation",
        "grounding_scope": "current_input_only",
        "visible_material_slots": ["event"],
        "unknown_slots": ["cause"],
        "material_quality": "eligible",
        "generic_relation_material_ids": ["phase20_relation_material"],
        "current_input": {"memo": SECRET_RAW_INPUT},
        "raw_input": SECRET_RAW_INPUT,
        "raw_text": SECRET_EVIDENCE,
        "comment_text": SECRET_INTERNAL_COMMENT,
        "observation_text": SECRET_INTERNAL_COMMENT,
        "reception_text": SECRET_INTERNAL_COMMENT,
        "evidence_text": SECRET_EVIDENCE,
    }


def _assert_public_boundary_no_internal_leaks(public_meta: Mapping[str, Any]) -> None:
    dumped = _dump(public_meta)
    assert FORBIDDEN_PUBLIC_BOUNDARY_KEYS.isdisjoint(_all_keys(public_meta))
    for fragment in FORBIDDEN_PUBLIC_BOUNDARY_FRAGMENTS:
        assert fragment not in dumped


@pytest.mark.parametrize(
    "response_kind",
    ["normal_observation", "low_information_observation", "limited_grounding_observation"],
)
def test_phase20_7_displayable_internal_contracts_bridge_to_public_passed_without_leaking_internal_meta(
    response_kind: str,
) -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _internal_meta_with_contract(response_kind),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback(VISIBLE_COMMENT, public_meta) is True
    assert set(body.keys()) == {"status", "id", "created_at", "input_feedback"}
    assert set(body["input_feedback"].keys()) == {"comment_text", "emlis_ai"}
    assert body["input_feedback"]["comment_text"] == VISIBLE_COMMENT
    _assert_public_boundary_no_internal_leaks(public_meta)
    _assert_public_boundary_no_internal_leaks(body)


@pytest.mark.parametrize(
    ("response_kind", "expected_public_status"),
    [
        ("safety_support_required", "safety_blocked"),
        ("safety_blocked_emergency", "safety_blocked"),
        ("infrastructure_error", "unavailable"),
    ],
)
def test_phase20_7_non_observation_contracts_do_not_fake_public_emlis_feedback(
    response_kind: str,
    expected_public_status: str,
) -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _internal_meta_with_contract(response_kind, legacy_status="passed"),
        comment_text_present=True,
        subscription_tier="free",
    )
    body = _response_body(VISIBLE_COMMENT, public_meta)

    assert public_meta["observation_status"] == expected_public_status
    assert should_include_public_input_feedback(VISIBLE_COMMENT, public_meta) is False
    assert body["input_feedback"] is None
    _assert_public_boundary_no_internal_leaks(public_meta)
    _assert_public_boundary_no_internal_leaks(body)


def test_phase20_7_comment_text_absent_still_blocks_passed_public_feedback() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        _internal_meta_with_contract("normal_observation", legacy_status="rejected"),
        comment_text_present=False,
        subscription_tier="free",
    )
    body = _response_body("", public_meta)

    assert public_meta["observation_status"] == "unavailable"
    assert public_meta["rejection_reasons"][0] == "public_feedback_comment_text_missing"
    assert should_include_public_input_feedback("", public_meta) is False
    assert body["input_feedback"] is None
    _assert_public_boundary_no_internal_leaks(public_meta)
