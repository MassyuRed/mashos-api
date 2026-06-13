# -*- coding: utf-8 -*-
"""P7-1 red ledger and blocker registry.

P7 starts by preserving known RED/HOLD/OUT_OF_SCOPE items.  The ledger is not a
release gate and it is not a mechanism for turning P5/P6 runtime connection into
product readiness.  Positive Recovery reds and Product Quality Connection timeout
remain open until separately classified and repaired.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_BLOCKER_REGISTRY_SCHEMA_VERSION,
    P7_DEFAULT_LOCAL_FILES,
    P7_GIT_CHECKED,
    P7_INITIAL_HOLD_IDS,
    P7_INITIAL_OUT_OF_SCOPE_IDS,
    P7_INITIAL_RED_IDS,
    P7_PHASE,
    P7_RED_LEDGER_SCHEMA_VERSION,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)

P7_RED_LEDGER_GENERATED_AT: Final = "2026-06-12T00:00:00+09:00"

_ALLOWED_STATUSES: Final[frozenset[str]] = frozenset({"RED", "HOLD", "OUT_OF_SCOPE", "CLOSED"})
_ALLOWED_SEVERITIES: Final[frozenset[str]] = frozenset(
    {"release_blocker", "runner_blocker", "quality_hold", "scope_boundary"}
)
_ALLOWED_SOURCE_KINDS: Final[frozenset[str]] = frozenset({"pytest", "doc", "local_review", "manual_ledger"})
_ALLOWED_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset(
    {"failed", "timeout", "hold", "out_of_scope", "unverified"}
)
_ALLOWED_RUNNER_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "ledger_only",
        "isolate_heavy_e2e",
        "route_to_blocker_matrix",
        "ratings_required",
        "exclude_from_p7",
    }
)
_ALLOWED_OWNER_LAYERS: Final[frozenset[str]] = frozenset(
    {
        "reader_relation_surface",
        "fail_closed_boundary",
        "product_quality_connection_e2e",
        "p5_human_qa",
        "p6_limited_surface",
        "release_decision_boundary",
        "unknown",
    }
)


def _entry(
    entry_id: str,
    *,
    status: str,
    severity: str,
    source_kind: str,
    source_path: str,
    evidence_kind: str,
    summary: str,
    release_blocker: bool,
    p7_runner_action: str,
    owner_layer: str,
    classification_required: bool,
) -> dict[str, Any]:
    return {
        "id": entry_id,
        "status": status,
        "severity": severity,
        "source": {
            "kind": source_kind,
            "path_or_doc": source_path,
            "evidence_kind": evidence_kind,
        },
        "summary": summary,
        "release_blocker": release_blocker,
        "p7_runner_action": p7_runner_action,
        "owner_layer": owner_layer,
        "classification_required": classification_required,
        "closed": False,
        "body_free": True,
    }


def _initial_red_entries() -> list[dict[str, Any]]:
    return [
        _entry(
            "P7-RED-001",
            status="RED",
            severity="release_blocker",
            source_kind="pytest",
            source_path="tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",
            evidence_kind="failed",
            summary="Positive Recovery relation signal mismatch remains open; recovery_load_bridge classification is still required.",
            release_blocker=True,
            p7_runner_action="route_to_blocker_matrix",
            owner_layer="reader_relation_surface",
            classification_required=True,
        ),
        _entry(
            "P7-RED-002",
            status="RED",
            severity="release_blocker",
            source_kind="pytest",
            source_path="tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",
            evidence_kind="failed",
            summary="Positive Recovery fail-closed boundary regression remains open; missing relation surface must not be passed.",
            release_blocker=True,
            p7_runner_action="route_to_blocker_matrix",
            owner_layer="fail_closed_boundary",
            classification_required=True,
        ),
        _entry(
            "P7-RED-003",
            status="RED",
            severity="runner_blocker",
            source_kind="pytest",
            source_path="tests/test_emlis_ai_complete_product_quality_connection_e2e.py",
            evidence_kind="timeout",
            summary="Product Quality Connection heavy E2E timeout remains open and must be isolated from the P7 core runner.",
            release_blocker=True,
            p7_runner_action="isolate_heavy_e2e",
            owner_layer="product_quality_connection_e2e",
            classification_required=True,
        ),
    ]


def _initial_hold_entries() -> list[dict[str, Any]]:
    return [
        _entry(
            "P7-HOLD-001",
            status="HOLD",
            severity="quality_hold",
            source_kind="doc",
            source_path="Cocolon_EmlisAI_P7_ProductQualityRunner_DetailedDesign_ImplementationOrder_20260612.md",
            evidence_kind="hold",
            summary="P5 human Blind QA is not complete; history-line quality dimensions remain review-required.",
            release_blocker=False,
            p7_runner_action="ratings_required",
            owner_layer="p5_human_qa",
            classification_required=False,
        ),
        _entry(
            "P7-HOLD-002",
            status="HOLD",
            severity="quality_hold",
            source_kind="doc",
            source_path="Cocolon_EmlisAI_P7_ProductQualityRunner_DetailedDesign_ImplementationOrder_20260612.md",
            evidence_kind="hold",
            summary="P6 visible expansion remains structure-question limited; long-arc and self-understanding families stay material-only.",
            release_blocker=False,
            p7_runner_action="ratings_required",
            owner_layer="p6_limited_surface",
            classification_required=False,
        ),
        _entry(
            "P7-HOLD-003",
            status="HOLD",
            severity="quality_hold",
            source_kind="manual_ledger",
            source_path="real_device_submit_and_mobile_modal_readfeel",
            evidence_kind="unverified",
            summary="Real-device submit and mobile modal read-feel are unverified and remain outside automated P7 core completion.",
            release_blocker=False,
            p7_runner_action="ledger_only",
            owner_layer="unknown",
            classification_required=False,
        ),
        _entry(
            "P7-HOLD-004",
            status="HOLD",
            severity="quality_hold",
            source_kind="manual_ledger",
            source_path="full_backend_suite",
            evidence_kind="unverified",
            summary="Full backend suite green is unverified; split subset results must not be promoted to full-suite green.",
            release_blocker=False,
            p7_runner_action="ledger_only",
            owner_layer="unknown",
            classification_required=False,
        ),
    ]


def _initial_out_of_scope_entries() -> list[dict[str, Any]]:
    rows = [
        ("P7-OUT-001", "RN UI change is outside P7-0/P7-1; visible modal contract is unchanged."),
        ("P7-OUT-002", "DB schema and write-path changes are outside P7-0/P7-1."),
        ("P7-OUT-003", "API route, request key, and public response top-level key changes are outside P7-0/P7-1."),
        ("P7-OUT-004", "release_allowed true is outside P7 and remains separated from P7 runner material."),
        ("P7-OUT-005", "P8 Derived User Model and Personal Continuity are outside the current step."),
        ("P7-OUT-006", "P9 external pilot and P10 release readiness are outside the current step."),
        ("P7-OUT-007", "P5 fixed visible examples are outside scope and must not be added."),
        ("P7-OUT-008", "P6 deep-insight family expansion is outside scope and remains blocked."),
    ]
    return [
        _entry(
            entry_id,
            status="OUT_OF_SCOPE",
            severity="scope_boundary",
            source_kind="doc",
            source_path="Cocolon_EmlisAI_P7_ProductQualityRunner_DetailedDesign_ImplementationOrder_20260612.md",
            evidence_kind="out_of_scope",
            summary=summary,
            release_blocker=False,
            p7_runner_action="exclude_from_p7",
            owner_layer="release_decision_boundary" if entry_id == "P7-OUT-004" else "unknown",
            classification_required=False,
        )
        for entry_id, summary in rows
    ]


def build_p7_red_ledger(
    *,
    generated_at: str = P7_RED_LEDGER_GENERATED_AT,
    local_files: Sequence[str] | None = None,
    include_out_of_scope: bool = True,
) -> dict[str, Any]:
    """Return the initial P7 red/HOLD/out-of-scope ledger as body-free material."""

    entries = _initial_red_entries() + _initial_hold_entries()
    if include_out_of_scope:
        entries.extend(_initial_out_of_scope_entries())
    ledger = {
        "schema_version": P7_RED_LEDGER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "generated_at": clean_identifier(generated_at, default=P7_RED_LEDGER_GENERATED_AT, max_length=64),
        "basis": {
            "source_mode": P7_SOURCE_MODE,
            "git_checked": P7_GIT_CHECKED,
            "local_files": dedupe_identifiers(local_files or P7_DEFAULT_LOCAL_FILES, limit=12, max_length=180),
        },
        "entries": entries,
        "public_contract": public_contract_flags(),
        "body_free": body_free_flags(include_history=False, include_reviewer=True),
        "release_allowed": False,
    }
    assert_p7_red_ledger_contract(ledger)
    return ledger


def _status_counts(entries: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(clean_identifier(entry.get("status"), default="UNKNOWN") for entry in entries)


def build_p7_blocker_registry_from_red_ledger(ledger: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Build a body-free adapter candidate from P7 red ledger to blocker matrix."""

    data = safe_mapping(ledger) if ledger is not None else build_p7_red_ledger()
    assert_p7_red_ledger_contract(data)
    entries = [safe_mapping(entry) for entry in data.get("entries", []) if isinstance(entry, Mapping)]
    counts = _status_counts(entries)
    release_blockers = [entry["id"] for entry in entries if entry.get("release_blocker") is True]
    hold_refs = [entry["id"] for entry in entries if entry.get("status") == "HOLD"]
    heavy_refs = [entry["id"] for entry in entries if entry.get("p7_runner_action") == "isolate_heavy_e2e"]
    route_to_matrix = [entry["id"] for entry in entries if entry.get("p7_runner_action") == "route_to_blocker_matrix"]

    registry = {
        "schema_version": P7_BLOCKER_REGISTRY_SCHEMA_VERSION,
        "source_red_ledger_schema_version": data.get("schema_version"),
        "phase": P7_PHASE,
        "release_allowed": False,
        "runner_can_start_with_open_reds": True,
        "initial_open_reds_are_expected": True,
        "red_count": counts.get("RED", 0),
        "hold_count": counts.get("HOLD", 0),
        "out_of_scope_count": counts.get("OUT_OF_SCOPE", 0),
        "release_blockers": release_blockers,
        "evaluation_hold_refs": hold_refs,
        "heavy_isolated_red_refs": heavy_refs,
        "blocker_matrix_candidate_refs": route_to_matrix,
        "public_contract": public_contract_flags(),
        "body_free": body_free_flags(include_history=False, include_reviewer=True),
    }
    assert_p7_blocker_registry_contract(registry)
    return registry


def assert_p7_red_ledger_contract(ledger: Mapping[str, Any]) -> bool:
    data = safe_mapping(ledger)
    if data.get("schema_version") != P7_RED_LEDGER_SCHEMA_VERSION:
        raise ValueError("unexpected P7 red ledger schema_version")
    if data.get("phase") != P7_PHASE:
        raise ValueError("unexpected P7 red ledger phase")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 red ledger must not allow release")
    basis = safe_mapping(data.get("basis"))
    if basis.get("source_mode") != P7_SOURCE_MODE or basis.get("git_checked") is not False:
        raise ValueError("P7 red ledger must be based on local snapshot without GitHub check")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("P7 red ledger must contain entries")
    seen: set[str] = set()
    for raw_entry in entries:
        entry = safe_mapping(raw_entry)
        entry_id = clean_identifier(entry.get("id"))
        if not entry_id or entry_id in seen:
            raise ValueError("P7 red ledger entries must have unique ids")
        seen.add(entry_id)
        status = clean_identifier(entry.get("status"))
        severity = clean_identifier(entry.get("severity"))
        action = clean_identifier(entry.get("p7_runner_action"))
        owner_layer = clean_identifier(entry.get("owner_layer"))
        if status not in _ALLOWED_STATUSES:
            raise ValueError(f"P7 red ledger entry has invalid status: {entry_id}")
        if severity not in _ALLOWED_SEVERITIES:
            raise ValueError(f"P7 red ledger entry has invalid severity: {entry_id}")
        if action not in _ALLOWED_RUNNER_ACTIONS:
            raise ValueError(f"P7 red ledger entry has invalid runner action: {entry_id}")
        if owner_layer not in _ALLOWED_OWNER_LAYERS:
            raise ValueError(f"P7 red ledger entry has invalid owner layer: {entry_id}")
        if entry.get("closed") is not False:
            raise ValueError(f"P7 red ledger entry must remain open: {entry_id}")
        if entry.get("body_free") is not True:
            raise ValueError(f"P7 red ledger entry must be body-free: {entry_id}")
        source = safe_mapping(entry.get("source"))
        if clean_identifier(source.get("kind")) not in _ALLOWED_SOURCE_KINDS:
            raise ValueError(f"P7 red ledger entry has invalid source kind: {entry_id}")
        if clean_identifier(source.get("evidence_kind")) not in _ALLOWED_EVIDENCE_KINDS:
            raise ValueError(f"P7 red ledger entry has invalid evidence kind: {entry_id}")
    if not set(P7_INITIAL_RED_IDS).issubset(seen):
        raise ValueError("P7 red ledger must preserve initial RED ids")
    if not set(P7_INITIAL_HOLD_IDS).issubset(seen):
        raise ValueError("P7 red ledger must preserve initial HOLD ids")
    if set(P7_INITIAL_OUT_OF_SCOPE_IDS) & seen and not set(P7_INITIAL_OUT_OF_SCOPE_IDS).issubset(seen):
        raise ValueError("P7 red ledger out-of-scope ids must be complete when present")
    red_entries = [safe_mapping(entry) for entry in entries if safe_mapping(entry).get("status") == "RED"]
    if len(red_entries) < len(P7_INITIAL_RED_IDS):
        raise ValueError("P7 red ledger must start with open red entries; it is not pass-only")
    if any(entry.get("release_blocker") is not True for entry in red_entries):
        raise ValueError("P7 RED entries must remain release blockers")
    hold_entries = [safe_mapping(entry) for entry in entries if safe_mapping(entry).get("status") == "HOLD"]
    if any(entry.get("release_blocker") is True for entry in hold_entries):
        raise ValueError("P7 HOLD entries must be separated from RED release blockers")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_red_ledger.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free")), source="p7_red_ledger.body_free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_red_ledger")
    return True


def assert_p7_blocker_registry_contract(registry: Mapping[str, Any]) -> bool:
    data = safe_mapping(registry)
    if data.get("schema_version") != P7_BLOCKER_REGISTRY_SCHEMA_VERSION:
        raise ValueError("unexpected P7 blocker registry schema_version")
    if data.get("release_allowed") is not False:
        raise ValueError("P7 blocker registry must not allow release")
    if data.get("runner_can_start_with_open_reds") is not True:
        raise ValueError("P7 runner registry must allow starting with ledgered open reds")
    if data.get("red_count", 0) < len(P7_INITIAL_RED_IDS):
        raise ValueError("P7 blocker registry must preserve initial red count")
    if not set(P7_INITIAL_RED_IDS).issubset(set(dedupe_identifiers(data.get("release_blockers")))):
        raise ValueError("P7 blocker registry must expose initial red release blockers")
    if "P7-RED-003" not in dedupe_identifiers(data.get("heavy_isolated_red_refs")):
        raise ValueError("P7 blocker registry must isolate the heavy timeout red")
    assert_false_markers(safe_mapping(data.get("public_contract")), source="p7_blocker_registry.public_contract")
    assert_false_markers(safe_mapping(data.get("body_free")), source="p7_blocker_registry.body_free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_blocker_registry")
    return True
