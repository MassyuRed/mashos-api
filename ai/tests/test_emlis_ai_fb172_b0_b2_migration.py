# -*- coding: utf-8 -*-
from __future__ import annotations

"""Integrity checks for the FB172 B0-B2 ownership migration."""

import json
from pathlib import Path

import emlis_ai_reply_service


TEST_ROOT = Path(__file__).resolve().parent
FIXTURE_ROOT = TEST_ROOT / "fixtures"


def _load(name: str):
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def test_fb172_owner_ledger_covers_the_frozen_failure_set_once() -> None:
    ledger = _load("fb172_owner_ledger_20260712.json")
    validation = _load("gate0_rr8_validation_20260711.json")
    baseline = validation["steps"]["full_backend"]["failure_refs"]
    records = ledger["records"]
    refs = [record["baseline_failure_ref"] for record in records]

    assert ledger["record_count"] == len(records) == 172
    assert len(refs) == len(set(refs))
    assert refs == baseline
    assert ledger["unclassified_count"] == 0
    assert ledger["current_owner_missing_count"] == 0
    assert ledger["unresolved_stop_count"] == 0
    assert all(record["current_owner_refs"] for record in records)


def test_fb172_b0_b1_b2_counts_and_migration_guards_are_fixed() -> None:
    ledger = _load("fb172_owner_ledger_20260712.json")
    assert ledger["batch_counts"]["B0"] == 2
    assert ledger["batch_counts"]["B1"] == 35
    assert ledger["batch_counts"]["B2"] == 85

    migrated = [
        record
        for record in ledger["records"]
        if record["planned_repair_batch"] in {"B1", "B2"}
    ]
    assert len(migrated) == 120
    assert all(record["closure_state"] == "MIGRATED_CURRENT_OWNER" for record in migrated)
    assert all(record["old_owner_restored"] is False for record in migrated)
    assert all(record["skip_or_xfail_used"] is False for record in migrated)
    assert all(record["exact_body_assert_added"] is False for record in migrated)
    assert all(record["replacement_test_refs"] for record in migrated)


def test_fb172_environment_evidence_is_body_free_and_b0_is_test_owned() -> None:
    evidence = _load("fb172_environment_20260712.json")
    local = evidence["local_reproduction"]
    repair = evidence["b0_repair"]

    assert local["env_values_included"] is False
    assert set(local["env_var_name_refs"]) == {
        "PYTHONPATH",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "MYMODEL_APP_NAME",
    }
    assert repair["production_contract_changed"] is False
    assert repair["isolation_owner"] == "test subprocess"
    assert repair["shared_app_module_state_used"] is False


def test_fb172_removed_private_owners_and_old_meta_are_not_restored() -> None:
    assert emlis_ai_reply_service.__all__ == ["render_emlis_ai_reply"]
    for symbol in (
        "build_emlis_ai_source_bundle",
        "judge_listener_readability",
        "_expected_relation_types_for_reader",
        "recover_emlis_gate_failure",
        "_reply_service_gate_recovery_public_boundary_decision",
        "_build_visible_surface_acceptance_report_for_candidate",
        "_build_runtime_surface_pre_return_report_for_candidate",
    ):
        assert not hasattr(emlis_ai_reply_service, symbol)

