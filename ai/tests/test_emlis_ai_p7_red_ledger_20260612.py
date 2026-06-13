# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_contracts import (
    P7_BLOCKER_REGISTRY_SCHEMA_VERSION,
    P7_INITIAL_HOLD_IDS,
    P7_INITIAL_OUT_OF_SCOPE_IDS,
    P7_INITIAL_RED_IDS,
    P7_RED_LEDGER_SCHEMA_VERSION,
)
from emlis_ai_p7_red_ledger import (
    assert_p7_blocker_registry_contract,
    assert_p7_red_ledger_contract,
    build_p7_blocker_registry_from_red_ledger,
    build_p7_red_ledger,
)

SECRET_INPUT = "P7-1 secret raw input must never be serialized"
SECRET_COMMENT = "P7-1 secret comment_text body must never be serialized"


def _by_id(ledger: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(entry["id"]): entry for entry in ledger["entries"]}  # type: ignore[index]


def test_p7_1_red_ledger_preserves_initial_red_hold_and_out_of_scope_without_release() -> None:
    ledger = build_p7_red_ledger()
    assert_p7_red_ledger_contract(ledger)

    assert ledger["schema_version"] == P7_RED_LEDGER_SCHEMA_VERSION
    assert ledger["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert ledger["basis"] == {
        "source_mode": "local_snapshot",
        "git_checked": False,
        "local_files": [
            "Cocolon_前提資料(205).zip",
            "EmlisAIの実装済み資料(56).zip",
            "Cocolon_EmlisAI_P7_ProductQualityRunner_DetailedDesign_ImplementationOrder_20260612(1).md",
            "Cocolon(227).zip",
            "mashos-api(140).zip",
        ],
    }
    assert ledger["release_allowed"] is False
    assert all(value is False for value in ledger["public_contract"].values())
    assert all(value is False for value in ledger["body_free"].values())

    entries = _by_id(ledger)
    assert set(P7_INITIAL_RED_IDS).issubset(entries)
    assert set(P7_INITIAL_HOLD_IDS).issubset(entries)
    assert set(P7_INITIAL_OUT_OF_SCOPE_IDS).issubset(entries)

    for red_id in P7_INITIAL_RED_IDS:
        entry = entries[red_id]
        assert entry["status"] == "RED"
        assert entry["release_blocker"] is True
        assert entry["closed"] is False
        assert entry["body_free"] is True
        assert entry["classification_required"] is True

    assert entries["P7-RED-001"]["owner_layer"] == "reader_relation_surface"
    assert entries["P7-RED-001"]["p7_runner_action"] == "route_to_blocker_matrix"
    assert entries["P7-RED-002"]["owner_layer"] == "fail_closed_boundary"
    assert entries["P7-RED-003"]["source"]["evidence_kind"] == "timeout"  # type: ignore[index]
    assert entries["P7-RED-003"]["p7_runner_action"] == "isolate_heavy_e2e"

    for hold_id in P7_INITIAL_HOLD_IDS:
        entry = entries[hold_id]
        assert entry["status"] == "HOLD"
        assert entry["release_blocker"] is False
        assert entry["closed"] is False

    dumped = json.dumps(ledger, ensure_ascii=False, sort_keys=True)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped


def test_p7_1_blocker_registry_starts_with_open_reds_instead_of_pass_only_design() -> None:
    ledger = build_p7_red_ledger()
    registry = build_p7_blocker_registry_from_red_ledger(ledger)
    assert_p7_blocker_registry_contract(registry)

    assert registry["schema_version"] == P7_BLOCKER_REGISTRY_SCHEMA_VERSION
    assert registry["source_red_ledger_schema_version"] == P7_RED_LEDGER_SCHEMA_VERSION
    assert registry["release_allowed"] is False
    assert registry["runner_can_start_with_open_reds"] is True
    assert registry["initial_open_reds_are_expected"] is True
    assert registry["red_count"] == 3
    assert registry["hold_count"] == 4
    assert registry["out_of_scope_count"] == 8
    assert registry["release_blockers"] == ["P7-RED-001", "P7-RED-002", "P7-RED-003"]
    assert registry["evaluation_hold_refs"] == list(P7_INITIAL_HOLD_IDS)
    assert registry["heavy_isolated_red_refs"] == ["P7-RED-003"]
    assert registry["blocker_matrix_candidate_refs"] == ["P7-RED-001", "P7-RED-002"]
    assert all(value is False for value in registry["public_contract"].values())
    assert all(value is False for value in registry["body_free"].values())


def test_p7_1_red_ledger_does_not_close_positive_recovery_or_timeout_as_stale_environment() -> None:
    entries = _by_id(build_p7_red_ledger())

    positive_recovery_1 = entries["P7-RED-001"]
    positive_recovery_2 = entries["P7-RED-002"]
    timeout_red = entries["P7-RED-003"]

    assert positive_recovery_1["closed"] is False
    assert positive_recovery_1["classification_required"] is True
    assert positive_recovery_1["source"]["evidence_kind"] == "failed"  # type: ignore[index]
    assert "old" not in str(positive_recovery_1["summary"]).lower()
    assert "stale" not in str(positive_recovery_1["summary"]).lower()

    assert positive_recovery_2["closed"] is False
    assert positive_recovery_2["classification_required"] is True
    assert positive_recovery_2["source"]["evidence_kind"] == "failed"  # type: ignore[index]

    assert timeout_red["closed"] is False
    assert timeout_red["classification_required"] is True
    assert timeout_red["source"]["evidence_kind"] == "timeout"  # type: ignore[index]
    assert timeout_red["p7_runner_action"] == "isolate_heavy_e2e"
    assert "environment" not in str(timeout_red["summary"]).lower()


def test_p7_1_red_ledger_contract_rejects_body_payload_release_or_closed_red() -> None:
    ledger = build_p7_red_ledger()

    unsafe_body = dict(ledger)
    unsafe_body["entries"] = list(ledger["entries"])
    unsafe_entry = dict(unsafe_body["entries"][0])
    unsafe_entry["comment_text"] = SECRET_COMMENT
    unsafe_body["entries"][0] = unsafe_entry
    with pytest.raises(ValueError):
        assert_p7_red_ledger_contract(unsafe_body)

    unsafe_release = dict(ledger)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_red_ledger_contract(unsafe_release)

    unsafe_contract = dict(ledger)
    unsafe_contract["public_contract"] = dict(ledger["public_contract"])
    unsafe_contract["public_contract"]["api_response_key_added"] = True
    with pytest.raises(ValueError):
        assert_p7_red_ledger_contract(unsafe_contract)

    unsafe_closed = dict(ledger)
    unsafe_closed["entries"] = list(ledger["entries"])
    closed_red = dict(unsafe_closed["entries"][0])
    closed_red["closed"] = True
    unsafe_closed["entries"][0] = closed_red
    with pytest.raises(ValueError):
        assert_p7_red_ledger_contract(unsafe_closed)


def test_p7_1_red_ledger_can_omit_out_of_scope_only_when_explicitly_requested() -> None:
    ledger = build_p7_red_ledger(include_out_of_scope=False)
    assert_p7_red_ledger_contract(ledger)
    entries = _by_id(ledger)

    assert set(P7_INITIAL_RED_IDS).issubset(entries)
    assert set(P7_INITIAL_HOLD_IDS).issubset(entries)
    assert set(P7_INITIAL_OUT_OF_SCOPE_IDS).isdisjoint(entries)
    assert ledger["release_allowed"] is False
