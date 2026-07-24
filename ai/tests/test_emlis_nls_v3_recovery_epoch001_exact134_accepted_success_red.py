# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for exact134 accepted-success and one-shot run history.

This file freezes only the future contract.  It does not run exact134, select
or consume a formal P1 token, issue a receipt, publish an event, or authorize
P2.  All probes are body-free and use the current committed proof registry.
"""

from copy import deepcopy
import ast
import hashlib
import importlib.util
import inspect
from pathlib import Path
import platform
import subprocess
import sys
from types import ModuleType
from typing import Any, Mapping

import pytest

import emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3 as accepted_owner
import emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 as registry_owner
from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_nls_v3_artifact_contract import canonical_json_bytes
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    fresh_recovery_epoch001_canonical_current_closure,
)


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_EXACT134_"
    "SUCCESS_AND_SEQUENCE_EVENT1_EVENT2_SHAREABLE_LEDGER_ATOMIC_PUBLICATION_"
    "CONTRACT_RECONCILIATION_RED_FREEZE_ONLY"
)
_KAREN_DIARY_PIN = "700f749f5149cac1f8bd4bab8a364d524a56985b"
_COCOLON_PIN = "fee21e9a92450d4171536f280e859d95e344804e"
_SOURCE_PIN = "78276950d0d7650968fe938bc63a6e13455a8d6c"
_SOURCE_TREE = "e13b8bcfce4d56ab1b25d0a4309326b8cc36eca2"
_DESIGN_BLOB = "7e7d454d888141cbdb872244bf6df93c046e0b6c"
_DESIGN_SHA256 = (
    "8bb377d49f04a33d6d21323a40bcd5ddc0d30eee8d4d2a2700ad7f074e32bb64"
)
_DETAILED_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
_CANDIDATE = "nls_v3_rc_0034"
_LOGICAL_CYCLE = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH = "NLS_V3_CYCLE001_RECOVERY_EPOCH_001"
_EVENT1_BASE_COMMIT = "a" * 40
_EVENT1_COMMIT = "b" * 40
_RESERVATION_COMMIT = "c" * 40

_ATTEMPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.formal_test_run_attempt.v2"
)
_RESERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.formal_test_run_reservation.v1"
)
_ACCEPTED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.accepted_test_run_receipt.v2"
)
_SEQUENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch001.sequence_event.v2"
)
_ALL11_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.all11_completion_chain.v2"
)
_RUN_PROTOCOL = "RECOVERY_EPOCH001_PYTEST_EXACT134_BODY_FREE_V1"

_ACCEPTED_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3.py"
)
_STEP_RECEIPT_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_step_completion_receipt_v3.py"
)
_SEQUENCE_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_sequence_ledger_v3.py"
)
_RUNNER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
)
_ALL11_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_all11_receipt_issue.py"
)
_PUBLISHER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_atomic_publication_bundle_v3.py"
)
_VERIFIER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
)
_CURRENT_CLOSURE_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
)
_PROVED_RECEIPT_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_proved_receipt_contract_red.py"
)
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_exact134_accepted_success_red.py"
)
_SEQUENCE_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_sequence_ledger_publication_red.py"
)

_FUTURE_SOURCE_SURFACE = frozenset(
    {
        _ACCEPTED_PATH,
        _STEP_RECEIPT_PATH,
        _SEQUENCE_OWNER_PATH,
        _RUNNER_PATH,
        _ALL11_PATH,
        _PUBLISHER_PATH,
        _VERIFIER_PATH,
    }
)
_RED_TEST_SURFACE = frozenset(
    {
        _CURRENT_CLOSURE_RED_PATH,
        _PROVED_RECEIPT_RED_PATH,
        _THIS_PATH,
        _SEQUENCE_RED_PATH,
    }
)
_PROTECTED_SHA256 = {
    "ai/services/ai_inference/api_emotion_submit.py": (
        "0705dc5cd7d4a78a4b8f6de1721b80b1ea6ae70b1d48a064acff9a8277af1822"
    ),
    "ai/services/ai_inference/emlis_ai_reply_service.py": (
        "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a"
    ),
    "ai/services/ai_inference/emlis_ai_step11_cycle_evidence_v3.py": (
        "e9f77f7411b581e96a7035d05aa3a50eb4628cbba37a02b0786a0d35b818d43d"
    ),
}

_ATTEMPT_KEYS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "authority_token",
        "challenge_id",
        "authority_challenge_id",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "run_reservation",
        "source_closure",
        "formal_node_registry_sha256",
        "collection_node_ids",
        "collection_sha256",
        "executed_node_ids",
        "executed_node_sha256",
        "runner_environment",
        "run_start",
        "run_end",
        "run_started_at_utc",
        "run_finished_at_utc",
        "outcomes",
        "counts",
        "exit_code",
        "timed_out",
        "outcome_state",
        "stop_code",
        "body_free",
        "formal_test_run_attempt_sha256",
    }
)
_RESERVATION_KEYS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "authority_challenge_id",
        "authority_token",
        "challenge_id",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "source_closure",
        "formal_node_registry_sha256",
        "reserved_at_utc",
        "reservation_state",
        "automatic_progression",
        "body_free",
        "formal_test_run_reservation_sha256",
    }
)
_RESERVATION_IDENTITY_KEYS = frozenset(
    {
        "artifact_role",
        "schema_version",
        "repository_full_name",
        "path",
        "git_blob_sha1",
        "raw_sha256",
        "logical_artifact_sha256",
        "publication_commit_sha1",
        "body_free",
        "identity_sha256",
    }
)
_ACCEPTED_KEYS = frozenset(
    {
        "schema_version",
        "formal_test_run_attempt",
        "formal_test_run_attempt_sha256",
        "step_view_sha256_by_step",
        "proof_sources",
        "proof_source_closure_sha256",
        "accepted",
        "body_free",
        "accepted_test_run_receipt_sha256",
    }
)
_SOURCE_CLOSURE_KEYS = frozenset(
    {
        "repository_full_name",
        "source_ref",
        "source_commit_sha1",
        "source_tree_sha1",
        "worktree_clean",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "requirement_registry_sha256",
        "formal_node_registry_sha256",
        "detailed_design_sha256",
    }
)
_PUBLISHED_EVENT_IDENTITY_KEYS = frozenset(
    {
        "identity_kind",
        "ledger_id",
        "recovery_epoch_id",
        "event_id",
        "event_name",
        "event_ordinal",
        "state",
        "timestamp_utc",
        "event_path",
        "event_git_blob_sha1",
        "event_raw_sha256",
        "event_sha256",
        "publication_commit_sha1",
        "identity_sha256",
    }
)
_RUNNER_ENVIRONMENT_KEYS = frozenset(
    {
        "protocol",
        "python_version",
        "pytest_version",
        "plugin_autoload_disabled",
        "runner_path",
        "runner_git_blob_sha1",
        "runner_sha256",
        "worker_isolated",
        "source_materialization",
        "pytest_addopts_ignored",
        "pytest_plugins_ignored",
        "timeout_seconds",
        "worker_argv_sha256",
        "environment_profile_material",
        "environment_profile_sha256",
    }
)
_ENVIRONMENT_PROFILE_KEYS = frozenset(
    {"fixed", "removed", "inherited_path_sha256", "lang", "lc_all"}
)
_OUTCOME_KEYS = frozenset(
    {
        "test_node_id",
        "source_path",
        "source_blob_sha1",
        "source_sha256",
        "result",
        "expected_closed_code",
        "actual_closed_code",
        "evidence_sha256",
    }
)
_COUNT_KEYS = frozenset(
    {
        "collected",
        "executed",
        "passed",
        "failed",
        "skipped",
        "xfailed",
        "xpassed",
        "deselected",
        "collection_errors",
        "timeouts",
    }
)
_ATTEMPT_ID_PREIMAGE_KEYS = frozenset(
    {
        "authority_token",
        "challenge_id",
        "source_baseline_event.event_sha256",
        "source_closure.source_commit_sha1",
        "formal_node_registry_sha256",
    }
)
_SUCCESS_COUNTS = {
    "collected": 134,
    "executed": 134,
    "passed": 134,
    "failed": 0,
    "skipped": 0,
    "xfailed": 0,
    "xpassed": 0,
    "deselected": 0,
    "collection_errors": 0,
    "timeouts": 0,
}
_ENVIRONMENT_FIXED = {
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
}
_ENVIRONMENT_REMOVED = [
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
]

_ATTACK_EXPECTATIONS = {
    "A01": "RUN_PARTIAL",
    "A02": "RUN_PARTIAL",
    "A03": "RUN_PARTIAL",
    "A04": "RUN_PARTIAL",
    "A05": "RUN_PARTIAL",
    "A06": "RUN_PARTIAL",
    "A07": "RUN_TIMED_OUT",
    "A08": "RUN_COLLECTION_ERROR",
    "A09": "RUN_PARTIAL",
    "A10": "RUN_PROVENANCE_INVALID",
    "A11": "RUN_PROVENANCE_INVALID",
    "A11a": "RUN_PROVENANCE_INVALID",
    "A11b": "RUN_PROVENANCE_INVALID",
    "A11c": "RUN_PROVENANCE_INVALID",
    "A12": "RUN_PROVENANCE_INVALID",
    "A13": "RUN_PROVENANCE_INVALID",
    "A14": "SOURCE_OR_ROOT_DRIFT",
    "A15": "RUN_PROVENANCE_INVALID",
    "A16": "RUN_PROVENANCE_INVALID",
    "A17": "BODY_FREE_VIOLATION",
    "A18": "ACCEPTED_RECEIPT_NOT_ISSUABLE",
    "A19": "ACCEPTED_RECEIPT_NOT_ISSUABLE",
    "A20": "RUN_PROVENANCE_INVALID",
    "A21": "RUN_PROVENANCE_INVALID",
    "R01": "RUN_ATTEMPT_REPLAY",
    "R02": "RUN_ATTEMPT_REPLAY",
    "R03": "RUN_RESERVATION_INVALID",
    "R04": "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
    "R05": "RUN_ATTEMPT_REPLAY",
    "S05": "ACCEPTED_RECEIPT_NOT_ISSUABLE",
}
_ATTEMPT_NEGATIVE_CODES = frozenset(
    {
        "RUN_PARTIAL",
        "RUN_TIMED_OUT",
        "RUN_COLLECTION_ERROR",
        "RUN_INFRA_ERROR",
        "RUN_PROVENANCE_INVALID",
        "BODY_FREE_VIOLATION",
        "SOURCE_OR_ROOT_DRIFT",
    }
)
_ACCEPTED_ISSUANCE_NEGATIVE_CODES = frozenset(
    {"ACCEPTED_RECEIPT_NOT_ISSUABLE"}
)
_RESERVATION_HISTORY_NEGATIVE_CODES = frozenset(
    {
        "RUN_ATTEMPT_REPLAY",
        "RUN_RESERVATION_INVALID",
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
    }
)

_OWNER_RED = "RECOVERY_EPOCH001_EXACT134_ACCEPTED_OWNER_V2_NOT_PROVED"
_FAIL_OPEN_RED = "RECOVERY_EPOCH001_EXACT134_REHASHED_PARTIAL_ACCEPTED"
_BOOLEAN_ZERO_RED = "RECOVERY_EPOCH001_EXACT134_BOOLEAN_ZERO_ACCEPTED"
_ATTEMPT_RED = "RECOVERY_EPOCH001_EXACT134_ATTEMPT_CONTRACT_NOT_PROVED"
_RESERVATION_RED = "RECOVERY_EPOCH001_EXACT134_RESERVATION_CONTRACT_NOT_PROVED"
_RUNNER_RED = "RECOVERY_EPOCH001_EXACT134_RUNNER_ATTEMPT_V2_NOT_PROVED"
_VERIFIER_RED = "RECOVERY_EPOCH001_EXACT134_INDEPENDENT_VERIFIER_NOT_PROVED"
_DOWNSTREAM_RED = "RECOVERY_EPOCH001_EXACT134_ACCEPTED_V2_GATE_NOT_PROVED"
_CLOSURE_RED = "RECOVERY_EPOCH001_EXACT134_PROOF_CLOSURE_NOT_PROVED"

_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tool_module_or_red(path: str, module_name: str, red_code: str) -> ModuleType:
    absolute = _REPO_ROOT / path
    if not absolute.is_file():
        pytest.fail(red_code, pytrace=False)
    spec = importlib.util.spec_from_file_location(module_name, absolute)
    if spec is None or spec.loader is None:
        pytest.fail(red_code, pytrace=False)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _issue_codes(value: Any) -> frozenset[str]:
    if not isinstance(value, (tuple, list, set, frozenset)):
        return frozenset()
    return frozenset(
        row if type(row) is str else str(getattr(row, "code", ""))
        for row in value
    )


def _material(value: Mapping[str, Any], hash_key: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != hash_key}


def _rehash_identity(value: dict[str, Any]) -> None:
    value["identity_sha256"] = artifact_sha256(
        _material(value, "identity_sha256")
    )


def _formal_nodes_and_context() -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[str],
    dict[str, str | None],
    dict[str, dict[str, Any]],
]:
    registry = (
        registry_owner.fresh_recovery_epoch001_current_step_requirement_registry()
    )
    closure = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT
    )
    nodes = [
        node
        for row in registry["steps"]
        for node in row["formal_completion_node_ids"]
    ]
    expected_codes: dict[str, str | None] = {node: None for node in nodes}
    for row in registry["steps"]:
        negative = row["independent_negative_proof"]
        expected_codes[negative["test_node_id"]] = negative[
            "expected_closed_code"
        ]
    files = {row["path"]: row for row in closure["files"]}
    return registry, closure, nodes, expected_codes, files


def _source_closure(
    *,
    registry: Mapping[str, Any],
    closure: Mapping[str, Any],
) -> dict[str, Any]:
    source_commit, source_tree = _git_head_tree()
    return {
        "repository_full_name": "MassyuRed/mashos-api",
        "source_ref": "refs/heads/main",
        "source_commit_sha1": source_commit,
        "source_tree_sha1": source_tree,
        "worktree_clean": True,
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "requirement_registry_sha256": registry["registry_sha256"],
        "formal_node_registry_sha256": (
            registry_owner.RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "detailed_design_sha256": _DETAILED_DESIGN_SHA256,
    }


def _git_head_tree() -> tuple[str, str]:
    values: list[str] = []
    for revision in ("HEAD", "HEAD^{tree}"):
        result = subprocess.run(
            ["git", "rev-parse", revision],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        values.append(result.stdout.strip())
    return values[0], values[1]


def _published_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _git_blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(prefix + raw).hexdigest()


def _p0_anchor() -> dict[str, Any]:
    value: dict[str, Any] = {
        "identity_kind": "LEGACY_IMMUTABLE_P0_ANCHOR",
        "event_name": "PARENT_ADDENDUM_FROZEN",
        "event_ordinal": 0,
        "state": "DEFINED_NOT_STARTED",
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "original_authority": (
            "NLS_V3_STEP11_CYCLE001_PROCESS_NONCONFORMANCE_CANONICAL_"
            "RECOVERY_EPOCH_PARENT_DESIGN_ADDENDUM_READ_ONLY"
        ),
        "timestamp_utc": "2026-07-22T22:37:07Z",
        "document_path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_ProcessNonconformance_"
            "CanonicalRecoveryEpoch001_ParentDesignAddendum_"
            "ReadOnly_20260723.md"
        ),
        "document_publication_commit_sha1": (
            "90a2c009b8a463110e01b907224e52ea50912bd8"
        ),
        "document_git_blob_sha1": (
            "3333ae29ec0f4e9dde614bc9cd520448f61d2386"
        ),
        "document_raw_sha256": (
            "46333ede4b86a9ced0a5223e8df8dea35287548c676ce15c7787602b9a62b45c"
        ),
        "receipt_path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_ProcessNonconformance_"
            "CanonicalRecoveryEpoch001_ParentDesignAddendum_"
            "ReadOnly_BodyFree_Receipt_20260723.json"
        ),
        "receipt_publication_commit_sha1": (
            "f20165e3eda11dc0262373d5f82f63377df76f10"
        ),
        "receipt_git_blob_sha1": (
            "bdfbd559535db06ae4af35fe1bb58716d6566126"
        ),
        "receipt_raw_sha256": (
            "70563fa0732f97e9c54d3e8371741253e834440a618936e448a31b4d1cf5c30e"
        ),
        "anchor_publication_commit_sha1": (
            "f20165e3eda11dc0262373d5f82f63377df76f10"
        ),
    }
    _rehash_identity(value)
    return value


def _event1_fixture(source_closure: Mapping[str, Any]) -> dict[str, Any]:
    lock_authority = (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "SOURCE_BASELINE_LOCK_TEST_OWNED_FIXTURE_ONLY"
    )
    lock_challenge = "d" * 64
    prior = _p0_anchor()
    baseline_id = artifact_sha256(
        {
            "logical_cycle_id": _LOGICAL_CYCLE,
            "recovery_epoch_id": _RECOVERY_EPOCH,
            "candidate_version_id": _CANDIDATE,
            "source_closure": source_closure,
            "prior_anchor.identity_sha256": prior["identity_sha256"],
        }
    )
    receipt: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch001."
            "source_baseline_closure_receipt.v2"
        ),
        "baseline_id": baseline_id,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "lock_authority_token": lock_authority,
        "lock_challenge_id": lock_challenge,
        "source_closure": deepcopy(source_closure),
        "prior_anchor": deepcopy(prior),
        "automatic_progression": False,
        "body_free": True,
        "source_baseline_closure_receipt_sha256": "",
    }
    receipt["source_baseline_closure_receipt_sha256"] = artifact_sha256(
        _material(
            receipt,
            "source_baseline_closure_receipt_sha256",
        )
    )
    receipt_raw = _published_bytes(receipt)
    receipt_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch001_"
        "SourceBaselineClosure_BodyFree_Receipt_20260724.json"
    )
    receipt_identity = {
        "artifact_role": "SOURCE_BASELINE_CLOSURE_RECEIPT",
        "schema_version": receipt["schema_version"],
        "repository_full_name": "MassyuRed/Cocolon",
        "path": receipt_path,
        "git_blob_sha1": _git_blob_sha1(receipt_raw),
        "raw_sha256": hashlib.sha256(receipt_raw).hexdigest(),
        "logical_artifact_sha256": (
            receipt["source_baseline_closure_receipt_sha256"]
        ),
        "body_free": True,
    }
    event_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch001_SequenceEvent01_"
        "SourceBaselineLocked_BodyFree_Event_20260724.json"
    )
    event_base_commit = "a" * 40
    event_publication_commit = "b" * 40
    event: dict[str, Any] = {
        "schema_version": _SEQUENCE_SCHEMA,
        "ledger_id": (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_SEQUENCE_LEDGER"
        ),
        "event_id": (
            "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_001_"
            "SOURCE_BASELINE_LOCKED"
        ),
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "event_name": "SOURCE_BASELINE_LOCKED",
        "event_ordinal": 1,
        "state": "SOURCE_BASELINE_LOCKED",
        "timestamp_utc": "2026-07-24T00:00:00Z",
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": lock_authority,
            "publication_authority_token": lock_authority,
        },
        "challenge_id": lock_challenge,
        "source_closure": deepcopy(source_closure),
        "prior_event": deepcopy(prior),
        "primary_evidence_artifact": deepcopy(receipt_identity),
        "publication": {
            "repository_full_name": "MassyuRed/Cocolon",
            "branch": "main",
            "base_commit_sha1": event_base_commit,
            "event_path": event_path,
            "supporting_artifact_count": 1,
            "supporting_artifacts": [deepcopy(receipt_identity)],
            "supporting_artifact_set_sha256": artifact_sha256(
                [receipt_identity]
            ),
            "expected_changed_path_count": 2,
            "ref_update_mode": (
                "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
            ),
            "publication_state": "PUBLISHED_ATOMIC",
        },
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
    }
    event["event_sha256"] = artifact_sha256(
        _material(event, "event_sha256")
    )
    event_raw = _published_bytes(event)
    identity: dict[str, Any] = {
        "identity_kind": "PUBLISHED_SEQUENCE_EVENT",
        "ledger_id": event["ledger_id"],
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "event_id": event["event_id"],
        "event_name": "SOURCE_BASELINE_LOCKED",
        "event_ordinal": 1,
        "state": "SOURCE_BASELINE_LOCKED",
        "timestamp_utc": "2026-07-24T00:00:00Z",
        "event_path": event_path,
        "event_git_blob_sha1": _git_blob_sha1(event_raw),
        "event_raw_sha256": hashlib.sha256(event_raw).hexdigest(),
        "event_sha256": event["event_sha256"],
        "publication_commit_sha1": event_publication_commit,
    }
    _rehash_identity(identity)
    return {
        "artifact": event,
        "identity": identity,
        "raw_bytes": event_raw,
        "source_receipt_artifact": receipt,
        "source_receipt_identity": receipt_identity,
        "source_receipt_raw_bytes": receipt_raw,
        "publication": {
            "base_commit_sha1": event_base_commit,
            "publication_commit_sha1": event_publication_commit,
            "parent_commit_sha1s": [event_base_commit],
            "changed_paths": sorted({receipt_path, event_path}),
            "expected_old_sha_lease_used": True,
            "postverified": True,
        },
        "repository_snapshot": {
            "parents_by_commit": {
                event_base_commit: [
                    prior["anchor_publication_commit_sha1"]
                ],
                event_publication_commit: [event_base_commit],
            },
            "path_blob_by_commit": {
                event_publication_commit: {
                    receipt_path: receipt_identity["git_blob_sha1"],
                    event_path: identity["event_git_blob_sha1"],
                }
            },
        },
    }


def _attempt_id(
    *,
    authority_token: str,
    challenge_id: str,
    event_sha256: str,
    source_commit_sha1: str,
    formal_node_registry_sha256: str,
) -> str:
    """Resolve the design's dotted §3.4 notation as literal preimage keys."""

    preimage = {
        "authority_token": authority_token,
        "challenge_id": challenge_id,
        "source_baseline_event.event_sha256": event_sha256,
        "source_closure.source_commit_sha1": source_commit_sha1,
        "formal_node_registry_sha256": formal_node_registry_sha256,
    }
    assert set(preimage) == _ATTEMPT_ID_PREIMAGE_KEYS
    return artifact_sha256(preimage)


def _reservation_fixture(
    *,
    authority_token: str,
    challenge_id: str,
    authority_challenge_id: str,
    attempt_id: str,
    source_baseline_event: Mapping[str, Any],
    source_closure: Mapping[str, Any],
    formal_node_registry_sha256: str,
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "schema_version": _RESERVATION_SCHEMA,
        "attempt_id": attempt_id,
        "authority_challenge_id": authority_challenge_id,
        "authority_token": authority_token,
        "challenge_id": challenge_id,
        "candidate_version_id": _CANDIDATE,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "source_baseline_event": deepcopy(source_baseline_event),
        "source_closure": deepcopy(source_closure),
        "formal_node_registry_sha256": formal_node_registry_sha256,
        "reserved_at_utc": "2026-07-24T00:00:01Z",
        "reservation_state": "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN",
        "automatic_progression": False,
        "body_free": True,
        "formal_test_run_reservation_sha256": "",
    }
    artifact["formal_test_run_reservation_sha256"] = artifact_sha256(
        _material(artifact, "formal_test_run_reservation_sha256")
    )
    raw = _published_bytes(artifact)
    path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch001_Attempt_"
        f"{attempt_id}_FormalTestRunReservation_BodyFree_"
        "Receipt_20260724.json"
    )
    identity: dict[str, Any] = {
        "artifact_role": "FORMAL_TEST_RUN_RESERVATION",
        "schema_version": _RESERVATION_SCHEMA,
        "repository_full_name": "MassyuRed/Cocolon",
        "path": path,
        "git_blob_sha1": _git_blob_sha1(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "logical_artifact_sha256": (
            artifact["formal_test_run_reservation_sha256"]
        ),
        "publication_commit_sha1": "c" * 40,
        "body_free": True,
    }
    _rehash_identity(identity)
    return {
        "artifact": artifact,
        "identity": identity,
        "raw_bytes": raw,
        "publication": {
            "base_commit_sha1": "b" * 40,
            "publication_commit_sha1": "c" * 40,
            "parent_commit_sha1s": ["b" * 40],
            "changed_paths": [path],
            "expected_old_sha_lease_used": True,
            "postverified": True,
        },
    }


def _rehash_attempt(
    attempt: dict[str, Any],
    *,
    rehash_outcomes: bool = True,
    rehash_environment: bool = True,
) -> dict[str, Any]:
    if rehash_outcomes and type(attempt.get("outcomes")) is list:
        for row in attempt["outcomes"]:
            if type(row) is dict:
                row["evidence_sha256"] = artifact_sha256(
                    _material(row, "evidence_sha256")
                )
    environment = attempt.get("runner_environment")
    if rehash_environment and type(environment) is dict:
        profile = environment.get("environment_profile_material")
        if type(profile) is dict:
            environment["environment_profile_sha256"] = artifact_sha256(
                profile
            )
    attempt["collection_sha256"] = artifact_sha256(
        {"node_ids": attempt.get("collection_node_ids")}
    )
    attempt["executed_node_sha256"] = artifact_sha256(
        {"node_ids": attempt.get("executed_node_ids")}
    )
    attempt["formal_test_run_attempt_sha256"] = artifact_sha256(
        _material(attempt, "formal_test_run_attempt_sha256")
    )
    return attempt


def _valid_v2_attempt_and_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    registry, closure, nodes, expected_codes, files = (
        _formal_nodes_and_context()
    )
    source_closure = _source_closure(registry=registry, closure=closure)
    event_fixture = _event1_fixture(source_closure)
    event = event_fixture["identity"]
    authority = (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "FORMAL_TEST_RUN_TEST_OWNED_FIXTURE_ONLY"
    )
    challenge = "a" * 64
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": authority,
            "challenge_id": challenge,
        }
    )
    attempt_id = _attempt_id(
        authority_token=authority,
        challenge_id=challenge,
        event_sha256=event["event_sha256"],
        source_commit_sha1=source_closure["source_commit_sha1"],
        formal_node_registry_sha256=(
            source_closure["formal_node_registry_sha256"]
        ),
    )
    reservation_fixture = _reservation_fixture(
        authority_token=authority,
        challenge_id=challenge,
        authority_challenge_id=authority_challenge_id,
        attempt_id=attempt_id,
        source_baseline_event=event,
        source_closure=source_closure,
        formal_node_registry_sha256=(
            source_closure["formal_node_registry_sha256"]
        ),
    )
    reservation = reservation_fixture["identity"]
    outcomes: list[dict[str, Any]] = []
    for node_id in nodes:
        source_path = node_id.partition("::")[0]
        source = files[source_path]
        row: dict[str, Any] = {
            "test_node_id": node_id,
            "source_path": source_path,
            "source_blob_sha1": source["git_blob_sha1"],
            "source_sha256": source["sha256"],
            "result": "PASSED",
            "expected_closed_code": expected_codes[node_id],
            "actual_closed_code": expected_codes[node_id],
        }
        row["evidence_sha256"] = artifact_sha256(row)
        outcomes.append(row)
    profile = {
        "fixed": dict(_ENVIRONMENT_FIXED),
        "removed": list(_ENVIRONMENT_REMOVED),
        "inherited_path_sha256": "b" * 64,
        "lang": "C.UTF-8",
        "lc_all": "C.UTF-8",
    }
    runner = files[_RUNNER_PATH]
    attempt: dict[str, Any] = {
        "schema_version": _ATTEMPT_SCHEMA,
        "attempt_id": attempt_id,
        "authority_token": authority,
        "challenge_id": challenge,
        "authority_challenge_id": authority_challenge_id,
        "candidate_version_id": _CANDIDATE,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "source_baseline_event": event,
        "run_reservation": reservation,
        "source_closure": deepcopy(source_closure),
        "formal_node_registry_sha256": (
            source_closure["formal_node_registry_sha256"]
        ),
        "collection_node_ids": list(nodes),
        "collection_sha256": "",
        "executed_node_ids": list(nodes),
        "executed_node_sha256": "",
        "runner_environment": {
            "protocol": _RUN_PROTOCOL,
            "python_version": platform.python_version(),
            "pytest_version": pytest.__version__,
            "plugin_autoload_disabled": True,
            "runner_path": _RUNNER_PATH,
            "runner_git_blob_sha1": runner["git_blob_sha1"],
            "runner_sha256": runner["sha256"],
            "worker_isolated": True,
            "source_materialization": "DETACHED_PINNED_GIT_WORKTREE",
            "pytest_addopts_ignored": True,
            "pytest_plugins_ignored": True,
            "timeout_seconds": (
                accepted_owner.RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS
            ),
            "worker_argv_sha256": (
                artifact_sha256(
                    {
                        "python_flags": ["-I", "-B"],
                        "runner_path": _RUNNER_PATH,
                        "worker_mode": "--internal-exact134-child",
                        "node_ids": nodes,
                        "pytest_options": [
                            "-q",
                            "--disable-warnings",
                            "-p",
                            "no:cacheprovider",
                        ],
                    }
                )
            ),
            "environment_profile_material": profile,
            "environment_profile_sha256": "",
        },
        "run_start": deepcopy(source_closure),
        "run_end": deepcopy(source_closure),
        "run_started_at_utc": "2026-07-24T00:00:01Z",
        "run_finished_at_utc": "2026-07-24T00:00:02Z",
        "outcomes": outcomes,
        "counts": dict(_SUCCESS_COUNTS),
        "exit_code": 0,
        "timed_out": False,
        "outcome_state": "SUCCEEDED",
        "stop_code": None,
        "body_free": True,
        "formal_test_run_attempt_sha256": "",
    }
    evidence = {
        "source_baseline_event": event_fixture,
        "formal_test_run_reservation": reservation_fixture,
        "repository_snapshot": {
            **event_fixture["repository_snapshot"],
            "parents_by_commit": {
                **event_fixture["repository_snapshot"][
                    "parents_by_commit"
                ],
                "c" * 40: ["b" * 40],
            },
            "path_blob_by_commit": {
                **event_fixture["repository_snapshot"][
                    "path_blob_by_commit"
                ],
                "c" * 40: {
                    reservation["path"]: reservation["git_blob_sha1"]
                },
            },
        },
        "event_publication_is_ancestor_of_reservation": True,
        "reservation_publication_is_ancestor_of_run": True,
    }
    return _rehash_attempt(attempt), evidence


def _valid_v2_attempt() -> dict[str, Any]:
    return _valid_v2_attempt_and_evidence()[0]


def _valid_publication_evidence() -> dict[str, Any]:
    return _valid_v2_attempt_and_evidence()[1]


def _failure_attempt(attack: str) -> dict[str, Any]:
    attempt = _valid_v2_attempt()
    first = attempt["outcomes"][0]
    if attack == "A01":
        first["result"] = "FAILED"
        first["actual_closed_code"] = None
        attempt["counts"].update(passed=133, failed=1)
        attempt["exit_code"] = 1
        stop_code = "RUN_PARTIAL"
    elif attack == "A02":
        first["result"] = "SKIPPED"
        first["actual_closed_code"] = None
        attempt["counts"].update(passed=133, skipped=1)
        stop_code = "RUN_PARTIAL"
    elif attack == "A03":
        first["result"] = "XFAILED"
        first["actual_closed_code"] = None
        attempt["counts"].update(passed=133, xfailed=1)
        stop_code = "RUN_PARTIAL"
    elif attack == "A04":
        first["result"] = "XPASSED"
        first["actual_closed_code"] = None
        attempt["counts"].update(passed=133, xpassed=1)
        stop_code = "RUN_PARTIAL"
    elif attack == "A05":
        first["result"] = "NOT_EXECUTED"
        first["actual_closed_code"] = None
        attempt["executed_node_ids"] = attempt["executed_node_ids"][1:]
        attempt["counts"].update(executed=133, passed=133, failed=1)
        attempt["exit_code"] = 1
        stop_code = "RUN_PARTIAL"
    elif attack == "A06":
        attempt["exit_code"] = 1
        stop_code = "RUN_PARTIAL"
    elif attack == "A07":
        for row in attempt["outcomes"]:
            row["result"] = "NOT_EXECUTED"
            row["actual_closed_code"] = None
        attempt["executed_node_ids"] = []
        attempt["counts"].update(
            executed=0,
            passed=0,
            failed=134,
            timeouts=1,
        )
        attempt["exit_code"] = 124
        attempt["timed_out"] = True
        attempt["outcome_state"] = "TIMED_OUT"
        stop_code = "RUN_TIMED_OUT"
    elif attack == "A08":
        for row in attempt["outcomes"]:
            row["result"] = "NOT_EXECUTED"
            row["actual_closed_code"] = None
        attempt["collection_node_ids"] = []
        attempt["executed_node_ids"] = []
        attempt["counts"].update(
            collected=0,
            executed=0,
            passed=0,
            failed=134,
            collection_errors=1,
        )
        attempt["exit_code"] = 4
        stop_code = "RUN_COLLECTION_ERROR"
    elif attack == "A09":
        first["result"] = "NOT_EXECUTED"
        first["actual_closed_code"] = None
        attempt["executed_node_ids"] = attempt["executed_node_ids"][1:]
        attempt["counts"].update(
            executed=133,
            passed=133,
            failed=1,
            deselected=1,
        )
        stop_code = "RUN_PARTIAL"
    elif attack == "INFRA":
        for row in attempt["outcomes"]:
            row["result"] = "NOT_EXECUTED"
            row["actual_closed_code"] = None
        attempt["executed_node_ids"] = []
        attempt["counts"].update(executed=0, passed=0, failed=134)
        attempt["exit_code"] = 125
        attempt["outcome_state"] = "INFRA_ERROR"
        stop_code = "RUN_INFRA_ERROR"
    else:
        raise AssertionError(f"unknown failure fixture: {attack}")
    if attack not in {"A07", "INFRA"}:
        attempt["outcome_state"] = "FAILED"
    attempt["stop_code"] = stop_code
    return _rehash_attempt(attempt)


def _invalid_attempt_cases(
    valid: Mapping[str, Any],
) -> list[tuple[str, dict[str, Any]]]:
    cases: list[tuple[str, dict[str, Any]]] = []

    for field in ("collection_node_ids", "executed_node_ids"):
        candidate = deepcopy(valid)
        candidate[field] = candidate[field][1:]
        cases.append(("A10", _rehash_attempt(candidate)))

        candidate = deepcopy(valid)
        candidate[field][1] = candidate[field][0]
        cases.append(("A10", _rehash_attempt(candidate)))

        candidate = deepcopy(valid)
        candidate[field][0], candidate[field][1] = (
            candidate[field][1],
            candidate[field][0],
        )
        cases.append(("A10", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["counts"]["failed"] = False
    cases.append(("A11", _rehash_attempt(candidate)))

    for value in (True, False):
        candidate = deepcopy(valid)
        candidate["exit_code"] = value
        cases.append(("A11a", _rehash_attempt(candidate)))

    for value in (0, 1):
        candidate = deepcopy(valid)
        candidate["timed_out"] = value
        cases.append(("A11b", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["source_baseline_event"]["event_ordinal"] = True
    _rehash_identity(candidate["source_baseline_event"])
    cases.append(("A11c", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["outcomes"] = candidate["outcomes"][1:]
    cases.append(("A12", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["outcomes"][1] = deepcopy(candidate["outcomes"][0])
    cases.append(("A12", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["outcomes"][0], candidate["outcomes"][1] = (
        candidate["outcomes"][1],
        candidate["outcomes"][0],
    )
    cases.append(("A12", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["counts"].update(passed=133, failed=1)
    cases.append(("A12", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    dedicated = next(
        row
        for row in candidate["outcomes"]
        if row["expected_closed_code"] is not None
    )
    dedicated["actual_closed_code"] = "WRONG_CLOSED_CODE"
    cases.append(("A13", _rehash_attempt(candidate)))

    for owner, field, value in (
        ("source_closure", "source_tree_sha1", "e" * 40),
        ("run_start", "source_commit_sha1", "e" * 40),
        ("run_end", "source_tree_sha1", "f" * 40),
    ):
        candidate = deepcopy(valid)
        candidate[owner][field] = value
        cases.append(("A14", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["formal_node_registry_sha256"] = "e" * 64
    cases.append(("A14", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["source_baseline_event"]["event_sha256"] = "e" * 64
    _rehash_identity(candidate["source_baseline_event"])
    cases.append(("A14", _rehash_attempt(candidate)))

    for field, value in (
        ("python_version", "0.invalid"),
        ("pytest_version", "0.invalid"),
        ("runner_git_blob_sha1", "e" * 40),
        ("runner_sha256", "e" * 64),
        ("worker_argv_sha256", "e" * 64),
    ):
        candidate = deepcopy(valid)
        candidate["runner_environment"][field] = value
        cases.append(("A15", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["runner_environment"]["environment_profile_material"][
        "lang"
    ] = "en_US.UTF-8"
    cases.append(("A15", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["outcomes"][0]["evidence_sha256"] = "0" * 64
    cases.append(
        ("A16", _rehash_attempt(candidate, rehash_outcomes=False))
    )

    candidate = deepcopy(valid)
    candidate["runner_environment"]["environment_profile_sha256"] = "0" * 64
    cases.append(
        ("A16", _rehash_attempt(candidate, rehash_environment=False))
    )

    candidate = deepcopy(valid)
    candidate["formal_test_run_attempt_sha256"] = "0" * 64
    cases.append(("A16", candidate))

    candidate = deepcopy(valid)
    candidate["raw_body"] = "forbidden"
    cases.append(("A17", _rehash_attempt(candidate)))

    for started, finished in (
        ("2026-07-24 00:00:01", "2026-07-24T00:00:02Z"),
        ("2026-07-24T09:00:01+09:00", "2026-07-24T00:00:02Z"),
        ("2026-07-24T00:00:03Z", "2026-07-24T00:00:02Z"),
    ):
        candidate = deepcopy(valid)
        candidate["run_started_at_utc"] = started
        candidate["run_finished_at_utc"] = finished
        cases.append(("A20", _rehash_attempt(candidate)))

    candidate = deepcopy(valid)
    candidate["outcome_state"] = "FAILED"
    candidate["stop_code"] = "RUN_PARTIAL"
    cases.append(("A21", _rehash_attempt(candidate)))

    candidate = _failure_attempt("A01")
    candidate["outcome_state"] = "SUCCEEDED"
    candidate["stop_code"] = None
    cases.append(("A21", _rehash_attempt(candidate)))
    return cases


def _valid_accepted_v2_receipt(
    attempt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    value = _valid_v2_attempt() if attempt is None else deepcopy(attempt)
    _registry, closure, _nodes, _codes, _files = (
        _formal_nodes_and_context()
    )
    proof_by_path: dict[str, dict[str, Any]] = {}
    for outcome in value["outcomes"]:
        proof_by_path[outcome["source_path"]] = {
            "path": outcome["source_path"],
            "git_blob_sha1": outcome["source_blob_sha1"],
            "sha256": outcome["source_sha256"],
        }
    proof_sources = [
        proof_by_path[path] for path in sorted(proof_by_path)
    ]
    receipt: dict[str, Any] = {
        "schema_version": _ACCEPTED_SCHEMA,
        "formal_test_run_attempt": deepcopy(value),
        "formal_test_run_attempt_sha256": (
            value["formal_test_run_attempt_sha256"]
        ),
        "step_view_sha256_by_step": {
            str(step): artifact_sha256(
                closure["step_views"][f"step_{step}"]
            )
            for step in range(11)
        },
        "proof_sources": proof_sources,
        "proof_source_closure_sha256": artifact_sha256(proof_sources),
        "accepted": True,
        "body_free": True,
        "accepted_test_run_receipt_sha256": "",
    }
    receipt["accepted_test_run_receipt_sha256"] = artifact_sha256(
        _material(receipt, "accepted_test_run_receipt_sha256")
    )
    return receipt


def _rehash_accepted_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    receipt["accepted_test_run_receipt_sha256"] = artifact_sha256(
        _material(receipt, "accepted_test_run_receipt_sha256")
    )
    return receipt


def _valid_reservation() -> dict[str, Any]:
    return deepcopy(
        _valid_publication_evidence()["formal_test_run_reservation"][
            "artifact"
        ]
    )


def _valid_reservation_record() -> dict[str, Any]:
    return deepcopy(
        _valid_publication_evidence()["formal_test_run_reservation"]
    )


def _rebuild_reservation_record(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    result = deepcopy(record)
    artifact = result["artifact"]
    artifact["formal_test_run_reservation_sha256"] = artifact_sha256(
        _material(
            artifact,
            "formal_test_run_reservation_sha256",
        )
    )
    raw = _published_bytes(artifact)
    result["raw_bytes"] = raw
    identity = result["identity"]
    identity["git_blob_sha1"] = _git_blob_sha1(raw)
    identity["raw_sha256"] = hashlib.sha256(raw).hexdigest()
    identity["logical_artifact_sha256"] = artifact[
        "formal_test_run_reservation_sha256"
    ]
    _rehash_identity(identity)
    return result


def _publication_evidence_with_reservation(
    record: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = _valid_publication_evidence()
    old = evidence["formal_test_run_reservation"]["identity"]
    new = record["identity"]
    paths = evidence["repository_snapshot"]["path_blob_by_commit"][
        _RESERVATION_COMMIT
    ]
    paths.pop(old["path"], None)
    paths[new["path"]] = new["git_blob_sha1"]
    evidence["formal_test_run_reservation"] = deepcopy(record)
    return evidence


def _attempt_bound_to_reservation(
    attempt: Mapping[str, Any],
    record: Mapping[str, Any],
) -> dict[str, Any]:
    result = deepcopy(attempt)
    reservation = record["artifact"]
    result["attempt_id"] = reservation["attempt_id"]
    result["authority_token"] = reservation["authority_token"]
    result["challenge_id"] = reservation["challenge_id"]
    result["authority_challenge_id"] = reservation[
        "authority_challenge_id"
    ]
    result["run_reservation"] = deepcopy(record["identity"])
    return _rehash_attempt(result)


def _assert_issue_contains(
    validator: Any,
    value: Mapping[str, Any],
    expected_code: str,
) -> None:
    issues = _issue_codes(validator(value))
    assert expected_code in issues, (expected_code, sorted(issues))


def _current_v1_receipt(
    monkeypatch: pytest.MonkeyPatch,
    *,
    attack: str,
) -> dict[str, Any]:
    """Build a current rehashed exploit receipt without executing pytest."""

    authority = (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_BODY_FREE_RED_PROBE_ONLY"
    )
    challenge = "1" * 64
    registry = registry_owner.fresh_recovery_epoch001_current_step_requirement_registry()
    closure = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT
    )
    monkeypatch.setattr(
        accepted_owner,
        "RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN",
        authority,
    )
    monkeypatch.setattr(
        accepted_owner,
        "_git_identity",
        lambda _root: (_SOURCE_PIN, _SOURCE_TREE, True),
    )
    event = accepted_owner.build_recovery_epoch001_source_baseline_event(
        formal_p1_authority=authority,
        challenge_id=challenge,
        requirement_registry=registry,
        repo_root=_REPO_ROOT,
    )
    nodes = [
        node
        for row in registry["steps"]
        for node in row["formal_completion_node_ids"]
    ]
    negative_codes = {
        row["independent_negative_proof"]["test_node_id"]: (
            row["independent_negative_proof"]["expected_closed_code"]
        )
        for row in registry["steps"]
    }
    files = {row["path"]: row for row in closure["files"]}
    outcomes: list[dict[str, Any]] = []
    for node_id in nodes:
        source_path = node_id.partition("::")[0]
        expected_code = negative_codes.get(node_id)
        row: dict[str, Any] = {
            "test_node_id": node_id,
            "source_path": source_path,
            "source_blob_sha1": files[source_path]["git_blob_sha1"],
            "source_sha256": files[source_path]["sha256"],
            "result": "PASSED",
            "expected_closed_code": expected_code,
            "actual_closed_code": expected_code,
        }
        row["evidence_sha256"] = artifact_sha256(row)
        outcomes.append(row)
    if attack == "partial":
        outcomes[0]["result"] = "FAILED"
        outcomes[0]["actual_closed_code"] = None
        outcomes[0]["evidence_sha256"] = artifact_sha256(
            {
                key: value
                for key, value in outcomes[0].items()
                if key != "evidence_sha256"
            }
        )
        counts: dict[str, int | bool] = {
            **_SUCCESS_COUNTS,
            "passed": 133,
            "failed": 1,
        }
        exit_code = 1
    elif attack == "boolean_zero":
        counts = {
            **_SUCCESS_COUNTS,
            "failed": False,
            "skipped": False,
            "xfailed": False,
            "xpassed": False,
            "deselected": False,
            "timeouts": False,
        }
        exit_code = 0
    else:
        raise AssertionError(f"unknown body-free attack: {attack}")
    binding = {
        "source_commit": _SOURCE_PIN,
        "source_tree": _SOURCE_TREE,
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "registry_sha256": registry["registry_sha256"],
        "worktree_clean": True,
    }
    runner_row = files[_RUNNER_PATH]
    proof_run: dict[str, Any] = {
        "protocol": (
            accepted_owner.RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL
        ),
        "candidate_version_id": _CANDIDATE,
        "recovery_epoch": 1,
        "source_baseline_event_sha256": event["event_sha256"],
        "source_commit": _SOURCE_PIN,
        "source_tree": _SOURCE_TREE,
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "registry_sha256": registry["registry_sha256"],
        "formal_node_registry_sha256": (
            registry_owner.RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "collection_node_ids": list(nodes),
        "executed_node_ids": list(nodes),
        "runner_environment": {
            "protocol": (
                accepted_owner.RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL
            ),
            "python_version": platform.python_version(),
            "pytest_version": pytest.__version__,
            "plugin_autoload_disabled": True,
            "runner_path": _RUNNER_PATH,
            "runner_git_blob_sha1": runner_row["git_blob_sha1"],
            "runner_sha256": runner_row["sha256"],
            "worker_isolated": True,
            "source_materialization": "DETACHED_PINNED_GIT_WORKTREE",
            "pytest_addopts_ignored": True,
            "pytest_plugins_ignored": True,
            "timeout_seconds": (
                accepted_owner.RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS
            ),
            "worker_argv_sha256": (
                accepted_owner._expected_worker_argv_sha256(nodes)
            ),
            "environment_profile_sha256": "2" * 64,
        },
        "run_start": dict(binding),
        "run_end": dict(binding),
        "outcomes": outcomes,
        "counts": counts,
        "exit_code": exit_code,
        "timed_out": False,
        "body_free": True,
    }
    proof_run["proof_run_sha256"] = artifact_sha256(proof_run)
    return accepted_owner.build_recovery_epoch001_accepted_test_run_receipt(
        proof_run=proof_run,
        requirement_registry=registry,
        source_baseline_event=event,
        repo_root=_REPO_ROOT,
    )


def test_exact134_red_authority_surface_and_protected_boundaries_are_exact() -> None:
    assert _AUTHORITY.endswith("RED_FREEZE_ONLY")
    assert _KAREN_DIARY_PIN == "700f749f5149cac1f8bd4bab8a364d524a56985b"
    assert _COCOLON_PIN == "fee21e9a92450d4171536f280e859d95e344804e"
    assert _SOURCE_PIN == "78276950d0d7650968fe938bc63a6e13455a8d6c"
    assert _SOURCE_TREE == "e13b8bcfce4d56ab1b25d0a4309326b8cc36eca2"
    assert _DESIGN_BLOB == "7e7d454d888141cbdb872244bf6df93c046e0b6c"
    assert _DESIGN_SHA256 == (
        "8bb377d49f04a33d6d21323a40bcd5ddc0d30eee8d4d2a2700ad7f074e32bb64"
    )
    assert _DETAILED_DESIGN_SHA256 == (
        "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
    )
    assert _CANDIDATE == "nls_v3_rc_0034"
    assert len(_FUTURE_SOURCE_SURFACE) == 7
    assert len(_RED_TEST_SURFACE) == 4
    assert not (_FUTURE_SOURCE_SURFACE & _RED_TEST_SURFACE)
    assert not (_FUTURE_SOURCE_SURFACE & set(_PROTECTED_SHA256))
    assert all((_REPO_ROOT / path).is_file() for path in _RED_TEST_SURFACE)
    for path, expected_sha256 in _PROTECTED_SHA256.items():
        assert _sha256(_REPO_ROOT / path) == expected_sha256, path
    assert (
        accepted_owner.RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN
        is None
    )
    assert accepted_owner.RECOVERY_EPOCH001_P2_AUTOMATIC_AUTHORIZATION is False


def test_exact134_literal_schemas_keysets_and_attack_matrix_are_exact() -> None:
    assert _ATTEMPT_SCHEMA.endswith("formal_test_run_attempt.v2")
    assert _RESERVATION_SCHEMA.endswith("formal_test_run_reservation.v1")
    assert _ACCEPTED_SCHEMA.endswith("accepted_test_run_receipt.v2")
    assert _SEQUENCE_SCHEMA.endswith("sequence_event.v2")
    assert _ALL11_SCHEMA.endswith("all11_completion_chain.v2")
    assert len(_ATTEMPT_KEYS) == 29
    assert len(_RESERVATION_KEYS) == 16
    assert len(_RESERVATION_IDENTITY_KEYS) == 10
    assert len(_ACCEPTED_KEYS) == 9
    assert len(_SOURCE_CLOSURE_KEYS) == 10
    assert len(_PUBLISHED_EVENT_IDENTITY_KEYS) == 14
    assert len(_RUNNER_ENVIRONMENT_KEYS) == 15
    assert len(_ENVIRONMENT_PROFILE_KEYS) == 5
    assert len(_OUTCOME_KEYS) == 8
    assert len(_COUNT_KEYS) == 10
    assert len(_ATTEMPT_ID_PREIMAGE_KEYS) == 5
    assert len(_ATTACK_EXPECTATIONS) == 30
    assert set(_ATTACK_EXPECTATIONS) == {
        *(f"A{number:02d}" for number in range(1, 22)),
        "A11a",
        "A11b",
        "A11c",
        *(f"R{number:02d}" for number in range(1, 6)),
        "S05",
    }
    assert (
        _ATTEMPT_NEGATIVE_CODES
        | _ACCEPTED_ISSUANCE_NEGATIVE_CODES
        | _RESERVATION_HISTORY_NEGATIVE_CODES
    ) == {
        "RUN_PARTIAL",
        "RUN_TIMED_OUT",
        "RUN_COLLECTION_ERROR",
        "RUN_PROVENANCE_INVALID",
        "SOURCE_OR_ROOT_DRIFT",
        "BODY_FREE_VIOLATION",
        "ACCEPTED_RECEIPT_NOT_ISSUABLE",
        "RUN_ATTEMPT_REPLAY",
        "RUN_RESERVATION_INVALID",
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "RUN_INFRA_ERROR",
    }
    assert set(_SUCCESS_COUNTS) == _COUNT_KEYS
    assert all(type(value) is int for value in _SUCCESS_COUNTS.values())
    assert _ENVIRONMENT_FIXED == {
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
    }
    assert _ENVIRONMENT_REMOVED == [
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
    ]


def test_exact134_current_v1_rehashed_partial_is_causally_red(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if (
        accepted_owner.RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA
        == _ACCEPTED_SCHEMA
    ):
        return
    partial = _current_v1_receipt(monkeypatch, attack="partial")
    boolean_zero = _current_v1_receipt(
        monkeypatch,
        attack="boolean_zero",
    )
    if (
        partial.get("accepted") is True
        and boolean_zero.get("accepted") is True
    ):
        pytest.fail(_FAIL_OPEN_RED, pytrace=False)
    if boolean_zero.get("accepted") is True:
        pytest.fail(_BOOLEAN_ZERO_RED, pytrace=False)
    pytest.fail(_OWNER_RED, pytrace=False)


def test_exact134_attempt_and_accepted_v2_owner_surface_is_proved_or_red() -> None:
    required = {
        "RECOVERY_EPOCH001_FORMAL_TEST_RUN_ATTEMPT_SCHEMA",
        "RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA",
        "RECOVERY_EPOCH001_FORMAL_TEST_RUN_ATTEMPT_NEGATIVE_CODES",
        "RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_NEGATIVE_CODES",
        "validate_recovery_epoch001_formal_test_run_attempt_shape",
        "validate_recovery_epoch001_accepted_test_run_attempt_for_issuance",
        "build_recovery_epoch001_accepted_test_run_receipt",
        "validate_recovery_epoch001_accepted_test_run_receipt_shape",
    }
    if (
        accepted_owner.RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA
        != _ACCEPTED_SCHEMA
        or getattr(
            accepted_owner,
            "RECOVERY_EPOCH001_FORMAL_TEST_RUN_ATTEMPT_SCHEMA",
            None,
        )
        != _ATTEMPT_SCHEMA
        or any(not hasattr(accepted_owner, name) for name in required)
    ):
        pytest.fail(_OWNER_RED, pytrace=False)
    codes = frozenset(
        accepted_owner.RECOVERY_EPOCH001_FORMAL_TEST_RUN_ATTEMPT_NEGATIVE_CODES
    )
    if not _ATTEMPT_NEGATIVE_CODES <= codes:
        pytest.fail(_OWNER_RED, pytrace=False)
    receipt_codes = frozenset(
        accepted_owner
        .RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_NEGATIVE_CODES
    )
    if not _ACCEPTED_ISSUANCE_NEGATIVE_CODES <= receipt_codes:
        pytest.fail(_OWNER_RED, pytrace=False)
    parameters = tuple(
        inspect.signature(
            accepted_owner.build_recovery_epoch001_accepted_test_run_receipt
        ).parameters
    )
    assert parameters == (
        "formal_test_run_attempt",
        "requirement_registry",
        "source_baseline_event",
        "publication_evidence",
        "repo_root",
    )


def test_exact134_attempt_success_partial_type_hash_and_body_contract_or_red() -> None:
    validate_shape = getattr(
        accepted_owner,
        "validate_recovery_epoch001_formal_test_run_attempt_shape",
        None,
    )
    validate_issuance = getattr(
        accepted_owner,
        "validate_recovery_epoch001_accepted_test_run_attempt_for_issuance",
        None,
    )
    if not callable(validate_shape) or not callable(validate_issuance):
        pytest.fail(_ATTEMPT_RED, pytrace=False)
    valid, publication_evidence = _valid_v2_attempt_and_evidence()
    registry = (
        registry_owner.fresh_recovery_epoch001_current_step_requirement_registry()
    )
    source_event = publication_evidence["source_baseline_event"]["artifact"]
    build_receipt = (
        accepted_owner.build_recovery_epoch001_accepted_test_run_receipt
    )
    assert set(valid) == _ATTEMPT_KEYS
    assert set(valid["source_closure"]) == _SOURCE_CLOSURE_KEYS
    assert set(valid["source_baseline_event"]) == (
        _PUBLISHED_EVENT_IDENTITY_KEYS
    )
    assert set(valid["run_reservation"]) == _RESERVATION_IDENTITY_KEYS
    assert set(valid["runner_environment"]) == _RUNNER_ENVIRONMENT_KEYS
    assert set(
        valid["runner_environment"]["environment_profile_material"]
    ) == _ENVIRONMENT_PROFILE_KEYS
    assert all(set(row) == _OUTCOME_KEYS for row in valid["outcomes"])
    assert set(valid["counts"]) == _COUNT_KEYS
    assert _issue_codes(validate_shape(valid)) == frozenset()
    assert _issue_codes(
        validate_issuance(
            valid,
            publication_evidence=publication_evidence,
        )
    ) == frozenset()

    for attack in (
        "A01",
        "A02",
        "A03",
        "A04",
        "A05",
        "A06",
        "A07",
        "A08",
        "A09",
    ):
        failed = _failure_attempt(attack)
        assert _issue_codes(validate_shape(failed)) == frozenset(), attack
        assert failed["stop_code"] == _ATTACK_EXPECTATIONS[attack]
        issuance = _issue_codes(
            validate_issuance(
                failed,
                publication_evidence=publication_evidence,
            )
        )
        assert issuance == _ACCEPTED_ISSUANCE_NEGATIVE_CODES, (
            attack,
            sorted(issuance),
        )
        with pytest.raises(
            ValueError,
            match="^ACCEPTED_RECEIPT_NOT_ISSUABLE$",
        ):
            build_receipt(
                formal_test_run_attempt=failed,
                requirement_registry=registry,
                source_baseline_event=source_event,
                publication_evidence=publication_evidence,
                repo_root=_REPO_ROOT,
            )

    infra = _failure_attempt("INFRA")
    assert _issue_codes(validate_shape(infra)) == frozenset()
    assert infra["stop_code"] == "RUN_INFRA_ERROR"
    assert _issue_codes(
        validate_issuance(
            infra,
            publication_evidence=publication_evidence,
        )
    ) == _ACCEPTED_ISSUANCE_NEGATIVE_CODES
    with pytest.raises(
        ValueError,
        match="^ACCEPTED_RECEIPT_NOT_ISSUABLE$",
    ):
        build_receipt(
            formal_test_run_attempt=infra,
            requirement_registry=registry,
            source_baseline_event=source_event,
            publication_evidence=publication_evidence,
            repo_root=_REPO_ROOT,
        )

    for attack, candidate in _invalid_attempt_cases(valid):
        _assert_issue_contains(
            validate_shape,
            candidate,
            _ATTACK_EXPECTATIONS[attack],
        )
        with pytest.raises(
            ValueError,
            match="^ACCEPTED_RECEIPT_NOT_ISSUABLE$",
        ):
            build_receipt(
                formal_test_run_attempt=candidate,
                requirement_registry=registry,
                source_baseline_event=source_event,
                publication_evidence=publication_evidence,
                repo_root=_REPO_ROOT,
            )

    temporal_or_challenge_cases: list[
        tuple[dict[str, Any], dict[str, Any]]
    ] = []
    for reserved_at in (
        "2026-07-23T23:59:59Z",
        "2026-07-24T00:00:02Z",
    ):
        record = deepcopy(
            publication_evidence["formal_test_run_reservation"]
        )
        record["artifact"]["reserved_at_utc"] = reserved_at
        record = _rebuild_reservation_record(record)
        evidence = _publication_evidence_with_reservation(record)
        temporal_or_challenge_cases.append(
            (_attempt_bound_to_reservation(valid, record), evidence)
        )

    lock_challenge = source_event["challenge_id"]
    authority = valid["authority_token"]
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": authority,
            "challenge_id": lock_challenge,
        }
    )
    attempt_id = _attempt_id(
        authority_token=authority,
        challenge_id=lock_challenge,
        event_sha256=valid["source_baseline_event"]["event_sha256"],
        source_commit_sha1=valid["source_closure"]["source_commit_sha1"],
        formal_node_registry_sha256=valid[
            "formal_node_registry_sha256"
        ],
    )
    same_challenge_record = _reservation_fixture(
        authority_token=authority,
        challenge_id=lock_challenge,
        authority_challenge_id=authority_challenge_id,
        attempt_id=attempt_id,
        source_baseline_event=valid["source_baseline_event"],
        source_closure=valid["source_closure"],
        formal_node_registry_sha256=valid[
            "formal_node_registry_sha256"
        ],
    )
    temporal_or_challenge_cases.append(
        (
            _attempt_bound_to_reservation(
                valid,
                same_challenge_record,
            ),
            _publication_evidence_with_reservation(
                same_challenge_record
            ),
        )
    )
    for candidate, evidence in temporal_or_challenge_cases:
        assert _issue_codes(
            validate_issuance(
                candidate,
                publication_evidence=evidence,
            )
        ) == _ACCEPTED_ISSUANCE_NEGATIVE_CODES
        with pytest.raises(
            ValueError,
            match="^ACCEPTED_RECEIPT_NOT_ISSUABLE$",
        ):
            build_receipt(
                formal_test_run_attempt=candidate,
                requirement_registry=registry,
                source_baseline_event=source_event,
                publication_evidence=evidence,
                repo_root=_REPO_ROOT,
            )

    validate_receipt = (
        accepted_owner.validate_recovery_epoch001_accepted_test_run_receipt_shape
    )
    accepted = _valid_accepted_v2_receipt(valid)
    assert build_receipt(
        formal_test_run_attempt=valid,
        requirement_registry=registry,
        source_baseline_event=source_event,
        publication_evidence=publication_evidence,
        repo_root=_REPO_ROOT,
    ) == accepted
    assert set(accepted) == _ACCEPTED_KEYS
    assert _issue_codes(
        validate_receipt(
            accepted,
            requirement_registry=registry,
            source_baseline_event=source_event,
            publication_evidence=publication_evidence,
            repo_root=_REPO_ROOT,
        )
    ) == frozenset()
    receipt_attacks: list[dict[str, Any]] = []

    candidate_receipt = deepcopy(accepted)
    candidate_receipt["accepted"] = False
    receipt_attacks.append(_rehash_accepted_receipt(candidate_receipt))

    candidate_receipt = deepcopy(accepted)
    failed = _failure_attempt("A01")
    candidate_receipt["formal_test_run_attempt"] = failed
    candidate_receipt["formal_test_run_attempt_sha256"] = failed[
        "formal_test_run_attempt_sha256"
    ]
    receipt_attacks.append(_rehash_accepted_receipt(candidate_receipt))

    candidate_receipt = deepcopy(accepted)
    candidate_receipt["accepted_test_run_receipt_sha256"] = "0" * 64
    receipt_attacks.append(candidate_receipt)

    for attacked_receipt in receipt_attacks:
        issues = _issue_codes(
            validate_receipt(
                attacked_receipt,
                requirement_registry=registry,
                source_baseline_event=source_event,
                publication_evidence=publication_evidence,
                repo_root=_REPO_ROOT,
            )
        )
        assert "ACCEPTED_RECEIPT_NOT_ISSUABLE" in issues


def test_exact134_one_shot_reservation_replay_and_unknown_result_or_red() -> None:
    sequence_owner = _tool_module_or_red(
        _SEQUENCE_OWNER_PATH,
        "emlis_ai_recovery_epoch001_sequence_ledger_v3",
        _RESERVATION_RED,
    )
    required = {
        "RECOVERY_EPOCH001_FORMAL_TEST_RUN_RESERVATION_SCHEMA",
        "build_recovery_epoch001_formal_test_run_reservation",
        "validate_recovery_epoch001_formal_test_run_reservation_shape",
        "validate_recovery_epoch001_formal_test_run_reservation_admission",
    }
    if (
        getattr(
            sequence_owner,
            "RECOVERY_EPOCH001_FORMAL_TEST_RUN_RESERVATION_SCHEMA",
            None,
        )
        != _RESERVATION_SCHEMA
        or any(not hasattr(sequence_owner, name) for name in required)
    ):
        pytest.fail(_RESERVATION_RED, pytrace=False)
    validate_shape = (
        sequence_owner.validate_recovery_epoch001_formal_test_run_reservation_shape
    )
    validate_admission = (
        sequence_owner
        .validate_recovery_epoch001_formal_test_run_reservation_admission
    )
    reservation_record = _valid_reservation_record()
    reservation = reservation_record["artifact"]
    source_event_artifact = _valid_publication_evidence()[
        "source_baseline_event"
    ]["artifact"]
    build_reservation = (
        sequence_owner.build_recovery_epoch001_formal_test_run_reservation
    )
    assert "reserved_at_utc" not in inspect.signature(
        build_reservation
    ).parameters
    built_reservation = build_reservation(
        authority_token=reservation["authority_token"],
        challenge_id=reservation["challenge_id"],
        source_baseline_event_identity=reservation[
            "source_baseline_event"
        ],
        source_baseline_event_artifact=source_event_artifact,
        source_closure=reservation["source_closure"],
        formal_node_registry_sha256=reservation[
            "formal_node_registry_sha256"
        ],
        clock_utc=lambda: reservation["reserved_at_utc"],
    )
    assert built_reservation == reservation
    built_raw = _published_bytes(built_reservation)
    assert built_raw == reservation_record["raw_bytes"]
    assert _git_blob_sha1(built_raw) == reservation_record["identity"][
        "git_blob_sha1"
    ]
    assert hashlib.sha256(built_raw).hexdigest() == (
        reservation_record["identity"]["raw_sha256"]
    )
    assert built_reservation[
        "formal_test_run_reservation_sha256"
    ] == reservation_record["identity"]["logical_artifact_sha256"]
    assert set(reservation) == _RESERVATION_KEYS
    assert _issue_codes(validate_shape(reservation)) == frozenset()
    assert set(reservation_record["identity"]) == (
        _RESERVATION_IDENTITY_KEYS
    )

    def admission(
        candidate_record: Mapping[str, Any] | None,
        *,
        reservations: list[Mapping[str, Any]],
        attempts: list[Mapping[str, Any]],
        rerun_requested: bool,
        repository_snapshot: Mapping[str, Any] | None = None,
    ) -> frozenset[str]:
        return _issue_codes(
            validate_admission(
                candidate_record,
                published_reservations=reservations,
                published_attempts=attempts,
                repository_snapshot=(
                    _valid_publication_evidence()["repository_snapshot"]
                    if repository_snapshot is None
                    else repository_snapshot
                ),
                source_baseline_event_artifact=source_event_artifact,
                rerun_requested=rerun_requested,
            )
        )

    assert admission(
        reservation_record,
        reservations=[],
        attempts=[],
        rerun_requested=False,
    ) == frozenset()
    assert "RUN_RESERVATION_INVALID" in admission(
        None,
        reservations=[],
        attempts=[],
        rerun_requested=False,
    )
    failed_history = {
        "artifact": _failure_attempt("A01"),
        "publication": {
            "publication_commit_sha1": "d" * 40,
            "parent_commit_sha1s": ["c" * 40],
            "postverified": True,
        },
    }
    assert "RUN_ATTEMPT_REPLAY" in admission(
        reservation_record,
        reservations=[reservation_record],
        attempts=[failed_history],
        rerun_requested=True,
    )
    assert "RUN_ATTEMPT_REPLAY" in admission(
        reservation_record,
        reservations=[],
        attempts=[failed_history],
        rerun_requested=True,
    )
    valid_snapshot = deepcopy(
        _valid_publication_evidence()["repository_snapshot"]
    )
    invalid_records: list[
        tuple[dict[str, Any], Mapping[str, Any]]
    ] = []
    candidate_record = deepcopy(reservation_record)
    candidate_record["publication"]["postverified"] = False
    invalid_records.append((candidate_record, valid_snapshot))
    candidate_record = deepcopy(reservation_record)
    candidate_record["identity"]["raw_sha256"] = "0" * 64
    _rehash_identity(candidate_record["identity"])
    invalid_records.append((candidate_record, valid_snapshot))
    candidate_record = deepcopy(reservation_record)
    candidate_record["artifact"]["reserved_at_utc"] = (
        "2026-07-24 00:00:01"
    )
    candidate_record["artifact"][
        "formal_test_run_reservation_sha256"
    ] = artifact_sha256(
        _material(
            candidate_record["artifact"],
            "formal_test_run_reservation_sha256",
        )
    )
    invalid_records.append((candidate_record, valid_snapshot))

    missing_path_snapshot = deepcopy(valid_snapshot)
    missing_path_snapshot["path_blob_by_commit"][
        _RESERVATION_COMMIT
    ] = {}
    invalid_records.append(
        (deepcopy(reservation_record), missing_path_snapshot)
    )

    wrong_blob_snapshot = deepcopy(valid_snapshot)
    wrong_blob_snapshot["path_blob_by_commit"][_RESERVATION_COMMIT][
        reservation_record["identity"]["path"]
    ] = "0" * 40
    invalid_records.append(
        (deepcopy(reservation_record), wrong_blob_snapshot)
    )

    ancestry_drift_snapshot = deepcopy(valid_snapshot)
    ancestry_drift_snapshot["parents_by_commit"][_RESERVATION_COMMIT] = [
        _EVENT1_BASE_COMMIT
    ]
    invalid_records.append(
        (deepcopy(reservation_record), ancestry_drift_snapshot)
    )

    candidate_record = deepcopy(reservation_record)
    candidate_record["identity"]["publication_commit_sha1"] = "d" * 40
    _rehash_identity(candidate_record["identity"])
    candidate_record["publication"]["publication_commit_sha1"] = "d" * 40
    candidate_record["publication"]["parent_commit_sha1s"] = ["b" * 40]
    invalid_records.append((candidate_record, valid_snapshot))

    candidate_record = deepcopy(reservation_record)
    candidate_record["identity"]["path"] = (
        f"{candidate_record['identity']['path']}.drift"
    )
    _rehash_identity(candidate_record["identity"])
    candidate_record["publication"]["changed_paths"] = [
        candidate_record["identity"]["path"]
    ]
    invalid_records.append((candidate_record, valid_snapshot))

    for invalid, snapshot in invalid_records:
        assert "RUN_RESERVATION_INVALID" in admission(
            invalid,
            reservations=[],
            attempts=[],
            rerun_requested=False,
            repository_snapshot=snapshot,
        )

    before_event = deepcopy(reservation_record)
    before_event["artifact"][
        "reserved_at_utc"
    ] = "2026-07-23T23:59:59Z"
    before_event = _rebuild_reservation_record(before_event)
    before_event_evidence = _publication_evidence_with_reservation(
        before_event
    )
    assert "RUN_RESERVATION_INVALID" in admission(
        before_event,
        reservations=[],
        attempts=[],
        rerun_requested=False,
        repository_snapshot=before_event_evidence[
            "repository_snapshot"
        ],
    )
    with pytest.raises(ValueError, match="^RUN_RESERVATION_INVALID$"):
        build_reservation(
            authority_token=reservation["authority_token"],
            challenge_id=reservation["challenge_id"],
            source_baseline_event_identity=reservation[
                "source_baseline_event"
            ],
            source_baseline_event_artifact=source_event_artifact,
            source_closure=reservation["source_closure"],
            formal_node_registry_sha256=reservation[
                "formal_node_registry_sha256"
            ],
            clock_utc=lambda: "2026-07-23T23:59:59Z",
        )

    lock_challenge = source_event_artifact["challenge_id"]
    same_challenge_authority_id = artifact_sha256(
        {
            "authority_token": reservation["authority_token"],
            "challenge_id": lock_challenge,
        }
    )
    same_challenge_attempt_id = _attempt_id(
        authority_token=reservation["authority_token"],
        challenge_id=lock_challenge,
        event_sha256=reservation["source_baseline_event"][
            "event_sha256"
        ],
        source_commit_sha1=reservation["source_closure"][
            "source_commit_sha1"
        ],
        formal_node_registry_sha256=reservation[
            "formal_node_registry_sha256"
        ],
    )
    same_challenge = _reservation_fixture(
        authority_token=reservation["authority_token"],
        challenge_id=lock_challenge,
        authority_challenge_id=same_challenge_authority_id,
        attempt_id=same_challenge_attempt_id,
        source_baseline_event=reservation["source_baseline_event"],
        source_closure=reservation["source_closure"],
        formal_node_registry_sha256=reservation[
            "formal_node_registry_sha256"
        ],
    )
    same_challenge_evidence = _publication_evidence_with_reservation(
        same_challenge
    )
    assert "RUN_RESERVATION_INVALID" in admission(
        same_challenge,
        reservations=[],
        attempts=[],
        rerun_requested=False,
        repository_snapshot=same_challenge_evidence[
            "repository_snapshot"
        ],
    )
    with pytest.raises(ValueError, match="^RUN_RESERVATION_INVALID$"):
        build_reservation(
            authority_token=reservation["authority_token"],
            challenge_id=lock_challenge,
            source_baseline_event_identity=reservation[
                "source_baseline_event"
            ],
            source_baseline_event_artifact=source_event_artifact,
            source_closure=reservation["source_closure"],
            formal_node_registry_sha256=reservation[
                "formal_node_registry_sha256"
            ],
            clock_utc=lambda: reservation["reserved_at_utc"],
        )
    assert "ATTEMPT_CONSUMPTION_UNKNOWN_STOP" in admission(
        reservation_record,
        reservations=[reservation_record],
        attempts=[],
        rerun_requested=True,
    )
    second_challenge = "c" * 64
    second_authority_challenge = artifact_sha256(
        {
            "authority_token": reservation["authority_token"],
            "challenge_id": second_challenge,
        }
    )
    second_attempt = _attempt_id(
        authority_token=reservation["authority_token"],
        challenge_id=second_challenge,
        event_sha256=reservation["source_baseline_event"]["event_sha256"],
        source_commit_sha1=(
            reservation["source_closure"]["source_commit_sha1"]
        ),
        formal_node_registry_sha256=(
            reservation["formal_node_registry_sha256"]
        ),
    )
    second = _reservation_fixture(
        authority_token=reservation["authority_token"],
        challenge_id=second_challenge,
        authority_challenge_id=second_authority_challenge,
        attempt_id=second_attempt,
        source_baseline_event=reservation["source_baseline_event"],
        source_closure=reservation["source_closure"],
        formal_node_registry_sha256=(
            reservation["formal_node_registry_sha256"]
        ),
    )
    assert "RUN_ATTEMPT_REPLAY" in admission(
        second,
        reservations=[reservation_record],
        attempts=[],
        rerun_requested=False,
    )


def test_exact134_runner_returns_attempt_v2_only_after_published_reservation_or_red(
) -> None:
    runner = _tool_module_or_red(
        _RUNNER_PATH,
        "emlis_nls_v3_recovery_epoch001_current_step_proof_run_red_target",
        _RUNNER_RED,
    )
    materialize = getattr(
        runner,
        "materialize_recovery_epoch001_formal_test_run_attempt",
        None,
    )
    if (
        getattr(
            runner,
            "RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL",
            None,
        )
        != _RUN_PROTOCOL
        or getattr(
            runner,
            "RECOVERY_EPOCH001_FORMAL_TEST_RUN_ATTEMPT_SCHEMA",
            None,
        )
        != _ATTEMPT_SCHEMA
        or not callable(materialize)
    ):
        pytest.fail(_RUNNER_RED, pytrace=False)
    parameters = tuple(
        inspect.signature(
            runner.run_recovery_epoch001_current_step_proof
        ).parameters
    )
    assert parameters == (
        "requirement_registry",
        "source_baseline_event",
        "run_reservation",
        "publication_evidence",
        "repo_root",
    )
    registry = (
        registry_owner.fresh_recovery_epoch001_current_step_requirement_registry()
    )
    valid, publication_evidence = _valid_v2_attempt_and_evidence()

    def report(attempt: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(attempt[key])
            for key in (
                "collection_node_ids",
                "executed_node_ids",
                "runner_environment",
                "run_start",
                "run_end",
                "run_started_at_utc",
                "run_finished_at_utc",
                "outcomes",
                "counts",
                "exit_code",
                "timed_out",
                "outcome_state",
                "stop_code",
                "body_free",
            )
        }

    assert materialize(
        worker_report=report(valid),
        requirement_registry=registry,
        source_baseline_event=publication_evidence[
            "source_baseline_event"
        ]["artifact"],
        run_reservation=publication_evidence[
            "formal_test_run_reservation"
        ],
        publication_evidence=publication_evidence,
        repo_root=_REPO_ROOT,
    ) == valid

    for expected in (
        _failure_attempt("A01"),
        _failure_attempt("A07"),
        _failure_attempt("INFRA"),
    ):
        actual = materialize(
            worker_report=report(expected),
            requirement_registry=registry,
            source_baseline_event=publication_evidence[
                "source_baseline_event"
            ]["artifact"],
            run_reservation=publication_evidence[
                "formal_test_run_reservation"
            ],
            publication_evidence=publication_evidence,
            repo_root=_REPO_ROOT,
        )
        assert actual["schema_version"] == _ATTEMPT_SCHEMA
        assert actual["outcome_state"] == expected["outcome_state"]
        assert actual["stop_code"] == expected["stop_code"]
        assert actual["exit_code"] == expected["exit_code"]
        assert len(actual["outcomes"]) == 134

    worker_report = report(_failure_attempt("A01"))

    def assert_reservation_rejected(
        run_reservation: Mapping[str, Any] | None,
        evidence: Mapping[str, Any],
    ) -> None:
        try:
            result = materialize(
                worker_report=worker_report,
                requirement_registry=registry,
                source_baseline_event=evidence[
                    "source_baseline_event"
                ]["artifact"],
                run_reservation=run_reservation,
                publication_evidence=evidence,
                repo_root=_REPO_ROOT,
            )
        except ValueError as exc:
            assert str(exc) == "RUN_RESERVATION_INVALID"
        else:
            assert result is None

    assert_reservation_rejected(None, publication_evidence)

    unpublished_evidence = deepcopy(publication_evidence)
    unpublished_evidence["formal_test_run_reservation"]["publication"][
        "postverified"
    ] = False
    assert_reservation_rejected(
        unpublished_evidence["formal_test_run_reservation"],
        unpublished_evidence,
    )

    missing_path_evidence = deepcopy(publication_evidence)
    missing_path_evidence["repository_snapshot"]["path_blob_by_commit"][
        _RESERVATION_COMMIT
    ] = {}
    assert_reservation_rejected(
        missing_path_evidence["formal_test_run_reservation"],
        missing_path_evidence,
    )

    ancestry_drift_evidence = deepcopy(publication_evidence)
    ancestry_drift_evidence["repository_snapshot"]["parents_by_commit"][
        _RESERVATION_COMMIT
    ] = [_EVENT1_BASE_COMMIT]
    assert_reservation_rejected(
        ancestry_drift_evidence["formal_test_run_reservation"],
        ancestry_drift_evidence,
    )

    wrong_blob_evidence = deepcopy(publication_evidence)
    reservation_path = wrong_blob_evidence[
        "formal_test_run_reservation"
    ]["identity"]["path"]
    wrong_blob_evidence["repository_snapshot"]["path_blob_by_commit"][
        _RESERVATION_COMMIT
    ][reservation_path] = "0" * 40
    assert_reservation_rejected(
        wrong_blob_evidence["formal_test_run_reservation"],
        wrong_blob_evidence,
    )

    raw_drift_evidence = deepcopy(publication_evidence)
    raw_drift_evidence["formal_test_run_reservation"]["identity"][
        "raw_sha256"
    ] = "0" * 64
    _rehash_identity(
        raw_drift_evidence["formal_test_run_reservation"]["identity"]
    )
    assert_reservation_rejected(
        raw_drift_evidence["formal_test_run_reservation"],
        raw_drift_evidence,
    )

    commit_drift_evidence = deepcopy(publication_evidence)
    commit_record = commit_drift_evidence[
        "formal_test_run_reservation"
    ]
    commit_record["identity"]["publication_commit_sha1"] = "d" * 40
    _rehash_identity(commit_record["identity"])
    commit_record["publication"]["publication_commit_sha1"] = "d" * 40
    commit_record["publication"]["parent_commit_sha1s"] = [
        _EVENT1_COMMIT
    ]
    assert_reservation_rejected(
        commit_record,
        commit_drift_evidence,
    )

    path_drift_evidence = deepcopy(publication_evidence)
    path_record = path_drift_evidence[
        "formal_test_run_reservation"
    ]
    path_record["identity"]["path"] = (
        f"{path_record['identity']['path']}.drift"
    )
    _rehash_identity(path_record["identity"])
    path_record["publication"]["changed_paths"] = [
        path_record["identity"]["path"]
    ]
    assert_reservation_rejected(
        path_record,
        path_drift_evidence,
    )

    for reserved_at in (
        "2026-07-23T23:59:59Z",
        "2026-07-24T00:00:02Z",
    ):
        temporal_record = deepcopy(
            publication_evidence["formal_test_run_reservation"]
        )
        temporal_record["artifact"]["reserved_at_utc"] = reserved_at
        temporal_record = _rebuild_reservation_record(temporal_record)
        temporal_evidence = _publication_evidence_with_reservation(
            temporal_record
        )
        assert_reservation_rejected(
            temporal_record,
            temporal_evidence,
        )

    event_artifact = publication_evidence[
        "source_baseline_event"
    ]["artifact"]
    lock_challenge = event_artifact["challenge_id"]
    base_reservation = publication_evidence[
        "formal_test_run_reservation"
    ]["artifact"]
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": base_reservation["authority_token"],
            "challenge_id": lock_challenge,
        }
    )
    same_challenge_attempt_id = _attempt_id(
        authority_token=base_reservation["authority_token"],
        challenge_id=lock_challenge,
        event_sha256=base_reservation["source_baseline_event"][
            "event_sha256"
        ],
        source_commit_sha1=base_reservation["source_closure"][
            "source_commit_sha1"
        ],
        formal_node_registry_sha256=base_reservation[
            "formal_node_registry_sha256"
        ],
    )
    same_challenge_record = _reservation_fixture(
        authority_token=base_reservation["authority_token"],
        challenge_id=lock_challenge,
        authority_challenge_id=authority_challenge_id,
        attempt_id=same_challenge_attempt_id,
        source_baseline_event=base_reservation[
            "source_baseline_event"
        ],
        source_closure=base_reservation["source_closure"],
        formal_node_registry_sha256=base_reservation[
            "formal_node_registry_sha256"
        ],
    )
    same_challenge_evidence = _publication_evidence_with_reservation(
        same_challenge_record
    )
    assert_reservation_rejected(
        same_challenge_record,
        same_challenge_evidence,
    )

    assert (
        materialize(
            worker_report=None,
            requirement_registry=registry,
            source_baseline_event=publication_evidence[
                "source_baseline_event"
            ]["artifact"],
            run_reservation=publication_evidence[
                "formal_test_run_reservation"
            ],
            publication_evidence=publication_evidence,
            repo_root=_REPO_ROOT,
        )
        is None
    )
    source = (_REPO_ROOT / _RUNNER_PATH).read_text(encoding="utf-8")
    assert '"accepted": True' not in source


def test_exact134_independent_verifier_recomputes_v2_without_owner_import_or_red(
) -> None:
    verifier = _tool_module_or_red(
        _VERIFIER_PATH,
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify_red_target",
        _VERIFIER_RED,
    )
    required = {
        "verify_recovery_epoch001_formal_test_run_attempt",
        "verify_recovery_epoch001_accepted_test_run_attempt_for_issuance",
        "verify_recovery_epoch001_accepted_test_run_receipt",
    }
    if any(not hasattr(verifier, name) for name in required):
        pytest.fail(_VERIFIER_RED, pytrace=False)
    source = (_REPO_ROOT / _VERIFIER_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=_VERIFIER_PATH)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(
        module.endswith(
            "emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3"
        )
        for module in imported
    )
    valid, publication_evidence = _valid_v2_attempt_and_evidence()
    registry = (
        registry_owner.fresh_recovery_epoch001_current_step_requirement_registry()
    )
    common = {
        "repo_root": _REPO_ROOT,
        "requirement_registry": registry,
        "source_baseline_event": publication_evidence[
            "source_baseline_event"
        ]["artifact"],
        "publication_evidence": publication_evidence,
    }
    verify_shape = verifier.verify_recovery_epoch001_formal_test_run_attempt
    verify_issuance = (
        verifier
        .verify_recovery_epoch001_accepted_test_run_attempt_for_issuance
    )
    assert _issue_codes(verify_shape(valid, **common)) == frozenset()
    assert _issue_codes(verify_issuance(valid, **common)) == frozenset()
    for attack in (
        "A01",
        "A02",
        "A03",
        "A04",
        "A05",
        "A06",
        "A07",
        "A08",
        "A09",
    ):
        failed = _failure_attempt(attack)
        assert _issue_codes(verify_shape(failed, **common)) == frozenset()
        assert _issue_codes(verify_issuance(failed, **common)) == (
            _ACCEPTED_ISSUANCE_NEGATIVE_CODES
        )
    for attack, candidate in _invalid_attempt_cases(valid):
        issues = _issue_codes(verify_shape(candidate, **common))
        assert _ATTACK_EXPECTATIONS[attack] in issues, (
            attack,
            sorted(issues),
        )

    verifier_binding_cases: list[
        tuple[dict[str, Any], dict[str, Any]]
    ] = []
    for reserved_at in (
        "2026-07-23T23:59:59Z",
        "2026-07-24T00:00:02Z",
    ):
        record = deepcopy(
            publication_evidence["formal_test_run_reservation"]
        )
        record["artifact"]["reserved_at_utc"] = reserved_at
        record = _rebuild_reservation_record(record)
        evidence = _publication_evidence_with_reservation(record)
        verifier_binding_cases.append(
            (_attempt_bound_to_reservation(valid, record), evidence)
        )
    event_artifact = publication_evidence[
        "source_baseline_event"
    ]["artifact"]
    base_reservation = publication_evidence[
        "formal_test_run_reservation"
    ]["artifact"]
    lock_challenge = event_artifact["challenge_id"]
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": base_reservation["authority_token"],
            "challenge_id": lock_challenge,
        }
    )
    same_challenge_attempt_id = _attempt_id(
        authority_token=base_reservation["authority_token"],
        challenge_id=lock_challenge,
        event_sha256=base_reservation["source_baseline_event"][
            "event_sha256"
        ],
        source_commit_sha1=base_reservation["source_closure"][
            "source_commit_sha1"
        ],
        formal_node_registry_sha256=base_reservation[
            "formal_node_registry_sha256"
        ],
    )
    same_challenge_record = _reservation_fixture(
        authority_token=base_reservation["authority_token"],
        challenge_id=lock_challenge,
        authority_challenge_id=authority_challenge_id,
        attempt_id=same_challenge_attempt_id,
        source_baseline_event=base_reservation[
            "source_baseline_event"
        ],
        source_closure=base_reservation["source_closure"],
        formal_node_registry_sha256=base_reservation[
            "formal_node_registry_sha256"
        ],
    )
    verifier_binding_cases.append(
        (
            _attempt_bound_to_reservation(
                valid,
                same_challenge_record,
            ),
            _publication_evidence_with_reservation(
                same_challenge_record
            ),
        )
    )
    for candidate, evidence in verifier_binding_cases:
        attacked_common = {
            **common,
            "publication_evidence": evidence,
        }
        assert _issue_codes(
            verify_issuance(candidate, **attacked_common)
        ) == _ACCEPTED_ISSUANCE_NEGATIVE_CODES

    accepted = _valid_accepted_v2_receipt(valid)
    assert _issue_codes(
        verifier.verify_recovery_epoch001_accepted_test_run_receipt(
            accepted,
            **common,
        )
    ) == frozenset()
    receipt_attacks: list[dict[str, Any]] = []

    attacked = deepcopy(accepted)
    attacked["accepted"] = False
    receipt_attacks.append(_rehash_accepted_receipt(attacked))

    attacked = deepcopy(accepted)
    failed = _failure_attempt("A01")
    attacked["formal_test_run_attempt"] = failed
    attacked["formal_test_run_attempt_sha256"] = failed[
        "formal_test_run_attempt_sha256"
    ]
    receipt_attacks.append(_rehash_accepted_receipt(attacked))

    attacked = deepcopy(accepted)
    attacked["accepted_test_run_receipt_sha256"] = "0" * 64
    receipt_attacks.append(attacked)

    for attacked in receipt_attacks:
        assert "ACCEPTED_RECEIPT_NOT_ISSUABLE" in _issue_codes(
            verifier.verify_recovery_epoch001_accepted_test_run_receipt(
                attacked,
                **common,
            )
        )


def test_exact134_step_and_all11_require_accepted_v2_not_attempt_or_red() -> None:
    step_owner = _tool_module_or_red(
        _STEP_RECEIPT_PATH,
        "emlis_ai_recovery_epoch001_step_completion_receipt_v3_red_target",
        _DOWNSTREAM_RED,
    )
    all11_owner = _tool_module_or_red(
        _ALL11_PATH,
        "emlis_nls_v3_recovery_epoch001_all11_receipt_issue_red_target",
        _DOWNSTREAM_RED,
    )
    if (
        getattr(
            all11_owner,
            "RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA",
            None,
        )
        != _ALL11_SCHEMA
        or not hasattr(
            step_owner,
            "build_recovery_epoch001_current_step_completion_receipt",
        )
        or not hasattr(
            all11_owner,
            "stage_recovery_epoch001_all11_current_step_completion_receipts",
        )
        or not hasattr(
            all11_owner,
            "build_recovery_epoch001_all11_completion_chain",
        )
    ):
        pytest.fail(_DOWNSTREAM_RED, pytrace=False)
    registry = (
        registry_owner.fresh_recovery_epoch001_current_step_requirement_registry()
    )
    valid, publication_evidence = _valid_v2_attempt_and_evidence()
    accepted = _valid_accepted_v2_receipt(valid)
    source_event = publication_evidence["source_baseline_event"]["artifact"]
    step0 = (
        step_owner.build_recovery_epoch001_current_step_completion_receipt(
            step_number=0,
            requirement_registry=registry,
            accepted_test_run_receipt=accepted,
            repo_root=_REPO_ROOT,
            previous_receipt=None,
            step0_parent_authority=source_event,
            prior_receipts=(),
            publication_evidence=publication_evidence,
        )
    )
    assert step0["step_number"] == 0
    assert step0["verdict"] == "PROVED"
    receipts = (
        all11_owner
        .stage_recovery_epoch001_all11_current_step_completion_receipts(
            requirement_registry=registry,
            accepted_test_run_receipt=accepted,
            source_baseline_event=source_event,
            publication_evidence=publication_evidence,
            repo_root=_REPO_ROOT,
        )
    )
    assert len(receipts) == 11
    chain = all11_owner.build_recovery_epoch001_all11_completion_chain(
        receipts=receipts,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        source_baseline_event=source_event,
        publication_evidence=publication_evidence,
        repo_root=_REPO_ROOT,
    )
    assert chain["schema_version"] == _ALL11_SCHEMA
    assert chain["publication_state"] == "PUBLISHED_ATOMIC"

    bad_inputs: list[Mapping[str, Any]] = [valid]
    candidate = deepcopy(accepted)
    candidate["accepted"] = False
    bad_inputs.append(_rehash_accepted_receipt(candidate))
    candidate = deepcopy(accepted)
    candidate["schema_version"] = (
        "cocolon.emlis.nls_v3.recovery_epoch001."
        "accepted_test_run_receipt.v1"
    )
    bad_inputs.append(_rehash_accepted_receipt(candidate))
    candidate = deepcopy(accepted)
    candidate["formal_test_run_attempt"]["counts"]["failed"] = False
    _rehash_attempt(candidate["formal_test_run_attempt"])
    candidate["formal_test_run_attempt_sha256"] = candidate[
        "formal_test_run_attempt"
    ]["formal_test_run_attempt_sha256"]
    bad_inputs.append(_rehash_accepted_receipt(candidate))
    bad_inputs.append(_valid_accepted_v2_receipt(_failure_attempt("A01")))

    for bad in bad_inputs:
        with pytest.raises(ValueError) as step_error:
            step_owner.build_recovery_epoch001_current_step_completion_receipt(
                step_number=0,
                requirement_registry=registry,
                accepted_test_run_receipt=bad,
                repo_root=_REPO_ROOT,
                previous_receipt=None,
                step0_parent_authority=source_event,
                prior_receipts=(),
                publication_evidence=publication_evidence,
            )
        assert "ACCEPTED_RECEIPT_NOT_ISSUABLE" in str(step_error.value)
        with pytest.raises(ValueError) as all11_error:
            (
                all11_owner
                .stage_recovery_epoch001_all11_current_step_completion_receipts(
                    requirement_registry=registry,
                    accepted_test_run_receipt=bad,
                    source_baseline_event=source_event,
                    publication_evidence=publication_evidence,
                    repo_root=_REPO_ROOT,
                )
            )
        assert "ACCEPTED_RECEIPT_NOT_ISSUABLE" in str(
            all11_error.value
        )


def test_exact134_future_owner_tests_and_verifier_are_in_current_closure_or_red(
) -> None:
    closure = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT
    )
    paths = {
        row["path"]
        for row in closure.get("files", [])
        if type(row) is dict and type(row.get("path")) is str
    }
    required = _FUTURE_SOURCE_SURFACE | _RED_TEST_SURFACE
    missing = sorted(required - paths)
    if missing:
        pytest.fail(f"{_CLOSURE_RED}:{','.join(missing)}", pytrace=False)
    completion = set(closure.get("views", {}).get("completion_proof", []))
    if not required <= completion:
        pytest.fail(
            f"{_CLOSURE_RED}:{','.join(sorted(required - completion))}",
            pytrace=False,
        )
