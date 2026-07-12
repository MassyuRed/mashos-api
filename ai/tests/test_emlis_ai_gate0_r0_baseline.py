# -*- coding: utf-8 -*-
from __future__ import annotations

"""Integrity checks for the Gate 0 R0 local baseline freeze."""

import hashlib
import json
from pathlib import Path

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input


AI_TEST_ROOT = Path(__file__).resolve().parent
FREEZE_PATH = AI_TEST_ROOT / "fixtures" / "emlis_gate0_r0_freeze_20260711.json"
BODY_FULL_BASELINE_PATH = AI_TEST_ROOT / "local_only" / "emlis_gate0_r0_baseline_20260711.json"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assert_body_free_tree(value: object) -> None:
    forbidden_value_keys = {
        "raw_input",
        "raw_text",
        "source_text",
        "surface_text",
        "comment_text",
        "candidate_body",
        "returned_surface",
    }
    if isinstance(value, dict):
        assert not forbidden_value_keys.intersection(value)
        for nested in value.values():
            _assert_body_free_tree(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_body_free_tree(nested)


def test_gate0_r0_freeze_has_exact_16_case_source_and_unique_input_hashes() -> None:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    baseline = json.loads(BODY_FULL_BASELINE_PATH.read_text(encoding="utf-8"))
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    expected_ids = [case.case_id for case in cases]
    assert freeze["case_freeze"]["case_ids"] == expected_ids
    assert baseline["execution_contract"]["case_count"] == len(cases) == 16
    assert [item["case_id"] for item in baseline["cases"]] == expected_ids

    actual_hashes = []
    for case, frozen in zip(cases, baseline["cases"], strict=True):
        normalized = normalize_emlis_current_input(case.as_current_input())
        assert frozen["normalized_current_input"] == normalized
        assert frozen["normalized_current_input_sha256"] == _canonical_hash(normalized)
        actual_hashes.append(frozen["normalized_current_input_sha256"])
    assert len(set(actual_hashes)) == 16


def test_gate0_r0_body_free_debug_subtrees_do_not_retain_body_fields() -> None:
    baseline = json.loads(BODY_FULL_BASELINE_PATH.read_text(encoding="utf-8"))
    for case in baseline["cases"]:
        _assert_body_free_tree(case["current_body_free_grounded_meta"])
        _assert_body_free_tree(case["current_plan_body_free_debug"])
        _assert_body_free_tree(case["current_sentence_plan_body_free_debug"])
        _assert_body_free_tree(case["current_surface_body_free_debug"])


def test_gate0_r0_failure_freeze_has_no_unclassified_result() -> None:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    assert freeze["pre_r1_selected_suite"]["unclassified_failure_count"] == 0
    assert freeze["historical_phase20_10_suite"]["unclassified_failure_count"] == 0
    assert freeze["r1_red_suite"]["expected_status_at_r1"] == "intentional_red"
    assert freeze["r1_red_suite"]["production_code_changed"] is False
