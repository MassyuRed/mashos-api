# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-0 guard: Phase19 diffs are classified before production changes.

This test does not change runtime behavior.  It keeps the current Phase19
symbols auditable so the later Phase20 delete/quarantine/generalize work can be
applied without treating A/C/D exact fixture success as the EmlisAI goal.
"""

from pathlib import Path

from helpers.emlis_ai_phase20_phase19_diff_inventory import (
    DECISION_DELETE,
    DECISION_QUARANTINE,
    DECISION_GENERALIZE,
    DECISION_RETAIN,
    PHASE20_ALLOWED_DECISIONS,
    PHASE20_PHASE19_DIFF_REVIEW_ENTRIES,
    PHASE20_PHASE19_DIFF_REVIEW_SCHEMA_VERSION,
    PHASE20_PHASE19_DIFF_REVIEW_SOURCE_PHASE,
    phase20_phase19_diff_review_schema_payloads,
    phase20_phase19_exact_fixture_entries,
    phase20_phase19_runtime_mainline_entries,
    validate_phase20_phase19_diff_review_inventory,
)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _read_backend_source(relative_path: str) -> str:
    path = _BACKEND_ROOT / relative_path
    assert path.exists(), f"source file missing from backend snapshot: {relative_path}"
    return path.read_text(encoding="utf-8")


def test_phase20_0_phase19_diff_inventory_schema_is_complete() -> None:
    assert PHASE20_PHASE19_DIFF_REVIEW_SCHEMA_VERSION == "cocolon.emlis.phase20.phase19_diff_review.v1"
    assert PHASE20_PHASE19_DIFF_REVIEW_SOURCE_PHASE == "Phase20-0_current_inventory_phase19_diff_classification"
    validate_phase20_phase19_diff_review_inventory()

    schema_payloads = phase20_phase19_diff_review_schema_payloads()
    assert len(schema_payloads) == len(PHASE20_PHASE19_DIFF_REVIEW_ENTRIES)
    assert {payload["current_decision"] for payload in schema_payloads} == PHASE20_ALLOWED_DECISIONS
    for payload in schema_payloads:
        assert set(payload.keys()) == {
            "file_path",
            "symbol_name",
            "introduced_for_phase19_case",
            "current_decision",
            "reason",
            "replacement_design",
            "requires_test_update",
        }


def test_phase20_0_runtime_mainline_acd_routes_are_not_retained_as_success_path() -> None:
    runtime_entries = phase20_phase19_runtime_mainline_entries()
    assert runtime_entries

    phase19_case_runtime_entries = [
        entry
        for entry in runtime_entries
        if entry.introduced_for_phase19_case in {"A", "C", "D"}
    ]
    assert phase19_case_runtime_entries
    assert {entry.current_decision for entry in phase19_case_runtime_entries}.issubset(
        {DECISION_DELETE, DECISION_GENERALIZE}
    )

    delete_symbols = {entry.symbol_name for entry in runtime_entries if entry.current_decision == DECISION_DELETE}
    assert "MODE_SELF_UNDERSTANDING_LEARNING_SHIFT" in delete_symbols
    assert "MODE_RELATIONSHIP_GRATITUDE_RECOVERY" in delete_symbols
    assert "_learning_shift_surface_text_for_line" in delete_symbols
    assert "_relationship_gratitude_surface_text_for_line" in delete_symbols

    generalized_symbols = {entry.symbol_name for entry in runtime_entries if entry.current_decision == DECISION_GENERALIZE}
    assert "_phase19_complete_initial_low_information_repair_ownership_meta" in generalized_symbols
    assert "_complete_initial_low_information_repair_context_allowed" in generalized_symbols


def test_phase20_0_inventory_tokens_are_retained_or_withdrawn_by_phase20_9() -> None:
    # Cocolon/RN lives outside the backend repo in local snapshots, so this
    # source-token check intentionally covers backend runtime/test files only.
    # Phase20-9 actually removes or generalizes the Phase19 production symbols,
    # so delete/generalize entries are no longer required to exist verbatim in
    # runtime code. Retain/quarantine entries must remain auditable.
    for entry in PHASE20_PHASE19_DIFF_REVIEW_ENTRIES:
        if entry.file_path.startswith("Cocolon/"):
            continue
        source = _read_backend_source(entry.file_path)
        if entry.current_decision in {DECISION_RETAIN, DECISION_QUARANTINE}:
            for token in entry.source_tokens:
                assert token in source, f"{entry.file_path} lost retained/quarantined token {token!r} for {entry.symbol_name}"
        else:
            assert entry.current_decision in {DECISION_DELETE, DECISION_GENERALIZE}
            assert entry.source_tokens, f"historical inventory token missing for {entry.symbol_name}"


def test_phase20_0_exact_abcd_fixtures_are_regression_guards_not_generated_text_goals() -> None:
    exact_entries = phase20_phase19_exact_fixture_entries()
    assert exact_entries
    assert {entry.current_decision for entry in exact_entries} == {DECISION_RETAIN}
    for entry in exact_entries:
        assert entry.runtime_mainline is False
        assert entry.requires_test_update is True
        joined = " ".join([entry.reason, entry.replacement_design or ""])
        assert "回帰" in joined or "shape" in joined or "behavior" in joined

    real_device_fixture_entry = next(
        entry for entry in exact_entries if entry.symbol_name == "PHASE19_REAL_DEVICE_ABCD_CASES"
    )
    assert "exact comment_text" in (real_device_fixture_entry.replacement_design or "")
