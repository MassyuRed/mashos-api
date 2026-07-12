# -*- coding: utf-8 -*-
from __future__ import annotations

"""Integrity checks for the FB172 B3-B7 current-owner migration."""

import inspect
import json
from pathlib import Path

import emlis_ai_reply_service
from emlis_ai_reply_service import render_emlis_ai_reply
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    evaluate_ground_observation_i0_negative_reachability,
)


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
BACKEND_ROOT = FIXTURE_ROOT.parents[2]


def _ledger():
    return json.loads(
        (FIXTURE_ROOT / "fb172_owner_ledger_20260712.json").read_text(
            encoding="utf-8"
        )
    )


def test_fb172_b3_through_b7_counts_and_closure_states_are_fixed() -> None:
    ledger = _ledger()
    assert ledger["batch_counts"]["B3"] == 11
    assert ledger["batch_counts"]["B4"] == 19
    assert ledger["batch_counts"]["B5"] == 7
    assert ledger["batch_counts"]["B6"] == 9
    assert ledger["batch_counts"]["B7"] == 4
    assert ledger["implemented_batches"] == [
        "B0",
        "B1",
        "B2",
        "B3",
        "B4",
        "B5",
        "B6",
        "B7",
    ]
    assert ledger["pending_batches"] == []

    migrated = [
        record
        for record in ledger["records"]
        if record["planned_repair_batch"] in {"B3", "B4", "B5", "B6", "B7"}
    ]
    assert len(migrated) == 50
    assert all(record["closure_state"] == "MIGRATED_CURRENT_OWNER" for record in migrated)
    assert all(record["replacement_test_refs"] for record in migrated)
    assert all(record["old_owner_restored"] is False for record in migrated)
    assert all(record["skip_or_xfail_used"] is False for record in migrated)
    assert all(record["exact_body_assert_added"] is False for record in migrated)


def test_fb172_b3_keeps_semantic_obligations_without_exact_body_contract() -> None:
    ledger = _ledger()
    records = [
        record for record in ledger["records"]
        if record["planned_repair_batch"] == "B3"
    ]
    assert records
    assert all(record["primary_classification"] == "EXACT_SURFACE_EXPECTATION" for record in records)
    assert all(
        set(record["valid_protected_obligations"])
        == {"bounded_observation", "source_lexeme_retention", "question_policy_false"}
        for record in records
    )


def test_fb172_b4_keeps_p5_p6_on_hold_without_runtime_bridge_restore() -> None:
    source = inspect.getsource(emlis_ai_reply_service)
    function_source = inspect.getsource(render_emlis_ai_reply)
    for retired_runtime_owner in (
        "build_p5_p6_handoff_lock",
        "build_user_label_connection_p5_readiness",
        "build_user_label_connection_p5_limited_visible_connection",
        "build_structure_insight_p6_entry_freeze",
        "build_structure_insight_p6_limited_surface_connection",
        "p5_runtime_bridge",
        "p6_runtime_bridge",
    ):
        assert retired_runtime_owner not in source
        assert retired_runtime_owner not in function_source


def test_fb172_b5_keeps_external_contract_owner_without_production_change_permission() -> None:
    ledger = _ledger()
    records = [
        record for record in ledger["records"]
        if record["planned_repair_batch"] == "B5"
    ]
    assert records
    assert all(record["production_change_allowed"] is False for record in records)
    assert all(
        set(record["valid_protected_obligations"])
        == {"passed_only_visibility", "public_meta_body_free", "safety_boundary"}
        for record in records
    )


def test_fb172_b6_allows_only_the_proven_relation_direction_production_repair() -> None:
    records = [
        record
        for record in _ledger()["records"]
        if record["planned_repair_batch"] == "B6"
    ]
    changed = [record for record in records if record["production_change_allowed"]]
    assert len(records) == 9
    assert len(changed) == 1
    assert changed[0]["production_change_applied"] is True
    assert "required_relation_direction" in changed[0]["valid_protected_obligations"]
    assert all(
        record["primary_classification"] == "STALE_OWNER_EXPECTATION"
        for record in records
        if record is not changed[0]
    )


def test_fb172_b7_uses_scoped_negative_reachability_without_production_change() -> None:
    records = [
        record
        for record in _ledger()["records"]
        if record["planned_repair_batch"] == "B7"
    ]
    assert len(records) == 4
    assert all(record["production_change_allowed"] is False for record in records)
    assert all(
        record["primary_classification"] == "STALE_OWNER_EXPECTATION"
        for record in records
    )
    assert evaluate_ground_observation_i0_negative_reachability(BACKEND_ROOT) == ()
