# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for sequence-ledger and atomic-publication reconciliation.

All Git state is a typed in-memory object graph.  No test calls GitHub,
updates a ref, publishes an artifact, starts formal exact134, or authorizes
P2.
"""

from copy import deepcopy
import ast
import hashlib
import importlib.util
import inspect
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Callable, Mapping

import pytest

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
import test_emlis_nls_v3_recovery_epoch001_exact134_accepted_success_red as accepted_red


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_EXACT134_"
    "SUCCESS_AND_SEQUENCE_EVENT1_EVENT2_SHAREABLE_LEDGER_ATOMIC_PUBLICATION_"
    "CONTRACT_RECONCILIATION_RED_FREEZE_ONLY"
)
_KAREN_DIARY_PIN = "700f749f5149cac1f8bd4bab8a364d524a56985b"
_COCOLON_RED_ENTRY_PIN = "fee21e9a92450d4171536f280e859d95e344804e"
_SOURCE_RED_ENTRY_PIN = "78276950d0d7650968fe938bc63a6e13455a8d6c"
_SOURCE_RED_ENTRY_TREE = "e13b8bcfce4d56ab1b25d0a4309326b8cc36eca2"
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
_LEDGER = "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_SEQUENCE_LEDGER"
_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch001.sequence_event.v2"
)
_SOURCE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "source_baseline_closure_receipt.v2"
)
_ACCEPTED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.accepted_test_run_receipt.v2"
)
_STEP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_completion_receipt.v1"
)
_ALL11_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.all11_completion_chain.v2"
)
_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "all11_atomic_publication_manifest.v2"
)
_CANDIDATE_STATE = "CANDIDATE_UNREACHABLE_VALID_NOT_PUBLISHED"
_PUBLISHED_STATE = "PUBLISHED_ATOMIC_VALID"
_REF_UPDATE_MODE = "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
_PREFIX = "EmlisAIの実装済み資料/documents/"

_SEQUENCE_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_sequence_ledger_v3.py"
)
_PUBLISHER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_atomic_publication_bundle_v3.py"
)
_VERIFIER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
)
_STEP_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_step_completion_receipt_v3.py"
)
_ALL11_OWNER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_all11_receipt_issue.py"
)
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_sequence_ledger_publication_red.py"
)
_ACCEPTED_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_exact134_accepted_success_red.py"
)

_SOURCE_RECEIPT_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "SourceBaselineClosure_BodyFree_Receipt_20260724.json"
)
_EVENT1_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event_20260724.json"
)
_ACCEPTED_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "AcceptedTestRunExact134_BodyFree_Receipt_20260724.json"
)
_STEP_PATHS = tuple(
    (
        f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
        f"Step{step:02d}_CurrentStepCompletion_PROVED_BodyFree_"
        "Receipt_20260724.json"
    )
    for step in range(11)
)
_ALL11_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "All11CompletionChain_BodyFree_Chain_20260724.json"
)
_MANIFEST_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "All11AtomicPublication_BodyFree_Manifest_20260724.json"
)
_EVENT2_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "SequenceEvent02_Step0_10PrerequisitesProved_BodyFree_Event_20260724.json"
)
_EVENT1_PATHS = frozenset({_SOURCE_RECEIPT_PATH, _EVENT1_PATH})
_CORE_PATHS = frozenset({_ACCEPTED_PATH, *_STEP_PATHS, _ALL11_PATH})
_EVENT2_SUPPORTING_PATHS = tuple(sorted({*_CORE_PATHS, _MANIFEST_PATH}))
_EVENT2_PATHS = frozenset({*_EVENT2_SUPPORTING_PATHS, _EVENT2_PATH})
_EVENT_PATHS_EXACT17 = _EVENT1_PATHS | _EVENT2_PATHS
_RESERVATION_PATH_TEMPLATE = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_Attempt_"
    "<64hex_attempt_id>_FormalTestRunReservation_BodyFree_"
    "Receipt_20260724.json"
)

_P0_DOCUMENT_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_ProcessNonconformance_"
    "CanonicalRecoveryEpoch001_ParentDesignAddendum_ReadOnly_20260723.md"
)
_P0_RECEIPT_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_ProcessNonconformance_"
    "CanonicalRecoveryEpoch001_ParentDesignAddendum_ReadOnly_"
    "BodyFree_Receipt_20260723.json"
)
_P0_DOCUMENT_BLOB = "3333ae29ec0f4e9dde614bc9cd520448f61d2386"
_P0_RECEIPT_BLOB = "bdfbd559535db06ae4af35fe1bb58716d6566126"
_P0_DOCUMENT_RAW_SHA256 = (
    "46333ede4b86a9ced0a5223e8df8dea35287548c676ce15c7787602b9a62b45c"
)
_P0_RECEIPT_RAW_SHA256 = (
    "70563fa0732f97e9c54d3e8371741253e834440a618936e448a31b4d1cf5c30e"
)
_P0_DOCUMENT_COMMIT = "90a2c009b8a463110e01b907224e52ea50912bd8"
_P0_RECEIPT_COMMIT = "f20165e3eda11dc0262373d5f82f63377df76f10"
_EVENT1_BASE_COMMIT = "a" * 40
_EVENT1_COMMIT = "b" * 40
_RESERVATION_COMMIT = "c" * 40
_EVENT2_COMMIT = "d" * 40

_EVENT_KEYS = frozenset(
    {
        "schema_version",
        "ledger_id",
        "event_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "event_name",
        "event_ordinal",
        "state",
        "timestamp_utc",
        "timestamp_kind",
        "authority",
        "challenge_id",
        "source_closure",
        "prior_event",
        "primary_evidence_artifact",
        "publication",
        "automatic_progression",
        "body_free",
        "event_sha256",
    }
)
_AUTHORITY_KEYS = frozenset(
    {
        "approval_kind",
        "transition_authority_token",
        "publication_authority_token",
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
_ARTIFACT_IDENTITY_KEYS = frozenset(
    {
        "artifact_role",
        "schema_version",
        "repository_full_name",
        "path",
        "git_blob_sha1",
        "raw_sha256",
        "logical_artifact_sha256",
        "body_free",
    }
)
_PUBLICATION_KEYS = frozenset(
    {
        "repository_full_name",
        "branch",
        "base_commit_sha1",
        "event_path",
        "supporting_artifact_count",
        "supporting_artifacts",
        "supporting_artifact_set_sha256",
        "expected_changed_path_count",
        "ref_update_mode",
        "publication_state",
    }
)
_P0_KEYS = frozenset(
    {
        "identity_kind",
        "event_name",
        "event_ordinal",
        "state",
        "recovery_epoch_id",
        "original_authority",
        "timestamp_utc",
        "document_path",
        "document_publication_commit_sha1",
        "document_git_blob_sha1",
        "document_raw_sha256",
        "receipt_path",
        "receipt_publication_commit_sha1",
        "receipt_git_blob_sha1",
        "receipt_raw_sha256",
        "anchor_publication_commit_sha1",
        "identity_sha256",
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
_SOURCE_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "baseline_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "lock_authority_token",
        "lock_challenge_id",
        "source_closure",
        "prior_anchor",
        "automatic_progression",
        "body_free",
        "source_baseline_closure_receipt_sha256",
    }
)
_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "base_commit_sha1",
        "core_artifact_count",
        "core_artifacts",
        "core_artifact_set_sha256",
        "event_supporting_artifact_count",
        "expected_changed_path_count",
        "event_path",
        "ref_update_mode",
        "body_free",
        "atomic_publication_manifest_sha256",
    }
)

_SEQUENCE_EXPECTATIONS = {
    "L01": "EVENT_SCHEMA_INVALID",
    "L02": "EVENT_SCHEMA_INVALID",
    "L03": "EVENT_TIMESTAMP_INVALID",
    "L04": "PRIOR_EVENT_INVALID",
    "L05": "P0_BACKFILL_FORBIDDEN",
    "L06": "ARTIFACT_IDENTITY_INVALID",
    "L07": "PRIOR_EVENT_INVALID",
    "L08": "SEQUENCE_INVALID",
    "L09": "ARTIFACT_IDENTITY_INVALID",
    "S01": "ALL11_INCOMPLETE",
    "S03": "OWNER_VERIFIER_CONFLICT",
    "S04": "P2_NOT_AUTHORIZED",
}
_PUBLICATION_EXPECTATIONS = {
    "P01": "PUBLICATION_BUNDLE_INVALID",
    "P02": "PUBLICATION_BUNDLE_INVALID",
    "P03": "PUBLICATION_BUNDLE_INVALID",
    "P05": "PUBLICATION_HEAD_DRIFT_STOP",
    "P06": "PUBLICATION_REF_UPDATE_FAILED_STOP",
    "P07": "PUBLICATION_POSTVERIFY_CONFLICT_STOP",
    "P08": "PUBLICATION_PATH_CONFLICT",
    "P09": "PUBLICATION_POSTVERIFY_CONFLICT_STOP",
    "P10": "PUBLICATION_BUNDLE_INVALID",
}

_SEQUENCE_OWNER_RED = "RECOVERY_EPOCH001_SEQUENCE_LEDGER_V2_OWNER_NOT_PROVED"
_PUBLISHER_RED = "RECOVERY_EPOCH001_ATOMIC_PUBLICATION_OWNER_NOT_PROVED"
_VERIFIER_RED = (
    "RECOVERY_EPOCH001_SEQUENCE_PUBLICATION_INDEPENDENT_VERIFIER_NOT_PROVED"
)

_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent


def _material(value: Mapping[str, Any], hash_key: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != hash_key}


def _published_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _git_blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(prefix + raw).hexdigest()


def _fake_tree_id(entries: Mapping[str, str]) -> str:
    """Return an opaque deterministic ID for the test-owned fake Git graph."""

    return hashlib.sha1(canonical_json_bytes(dict(sorted(entries.items())))).hexdigest()


def _identity_hash(value: dict[str, Any]) -> None:
    value["identity_sha256"] = artifact_sha256(
        _material(value, "identity_sha256")
    )


def _issue_codes(value: Any) -> tuple[str, ...]:
    if type(value) not in (tuple, list, set, frozenset):
        return ()
    return tuple(
        row if type(row) is str else str(getattr(row, "code", ""))
        for row in value
    )


def _module_or_red(path: str, name: str, red_code: str) -> ModuleType:
    absolute = _REPO_ROOT / path
    if not absolute.is_file():
        pytest.fail(red_code, pytrace=False)
    spec = importlib.util.spec_from_file_location(name, absolute)
    if spec is None or spec.loader is None:
        pytest.fail(red_code, pytrace=False)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sequence_apis_or_red() -> tuple[ModuleType, ModuleType]:
    sequence = _module_or_red(
        _SEQUENCE_OWNER_PATH,
        "emlis_ai_recovery_epoch001_sequence_ledger_v3_red_target",
        _SEQUENCE_OWNER_RED,
    )
    verifier = _module_or_red(
        _VERIFIER_PATH,
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify_sequence_target",
        _VERIFIER_RED,
    )
    required = {
        "RECOVERY_EPOCH001_SEQUENCE_EVENT_SCHEMA",
        "RECOVERY_EPOCH001_INDEPENDENT_SEQUENCE_VERIFIER",
        "build_recovery_epoch001_source_baseline_closure_receipt",
        "build_recovery_epoch001_sequence_event_1",
        "build_recovery_epoch001_sequence_event_2",
        "validate_recovery_epoch001_sequence_transition_candidate",
        "validate_recovery_epoch001_owner_verifier_agreement",
    }
    verifier_required = {
        "verify_recovery_epoch001_sequence_transition_candidate",
    }
    if any(not hasattr(sequence, name) for name in required):
        pytest.fail(_SEQUENCE_OWNER_RED, pytrace=False)
    if any(not hasattr(verifier, name) for name in verifier_required):
        pytest.fail(_VERIFIER_RED, pytrace=False)
    return sequence, verifier


def _publication_apis_or_red() -> tuple[ModuleType, ModuleType]:
    publisher = _module_or_red(
        _PUBLISHER_PATH,
        "emlis_nls_v3_recovery_epoch001_atomic_publication_bundle_v3_red_target",
        _PUBLISHER_RED,
    )
    verifier = _module_or_red(
        _VERIFIER_PATH,
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify_publication_target",
        _VERIFIER_RED,
    )
    required = {
        "RECOVERY_EPOCH001_CANDIDATE_PUBLICATION_VALID_STATE",
        "RECOVERY_EPOCH001_PUBLISHED_ATOMIC_VALID_STATE",
        "build_recovery_epoch001_event1_atomic_publication_supporting_set",
        "build_recovery_epoch001_event2_atomic_publication_supporting_set",
        "build_recovery_epoch001_event1_atomic_publication_bundle",
        "build_recovery_epoch001_event2_atomic_publication_bundle",
        "validate_recovery_epoch001_atomic_publication_supporting_set",
        "validate_recovery_epoch001_atomic_publication_candidate",
        "validate_recovery_epoch001_atomic_publication_preflight",
        "validate_recovery_epoch001_atomic_ref_update_plan",
        "validate_recovery_epoch001_atomic_publication_result",
        "classify_recovery_epoch001_atomic_publication_candidate",
        "classify_recovery_epoch001_atomic_publication_result",
    }
    verifier_required = {
        "verify_recovery_epoch001_atomic_publication_supporting_set",
        "verify_recovery_epoch001_atomic_publication_candidate",
        "verify_recovery_epoch001_atomic_publication_preflight",
        "verify_recovery_epoch001_atomic_ref_update_plan",
        "verify_recovery_epoch001_atomic_publication_result",
    }
    if any(not hasattr(publisher, name) for name in required):
        pytest.fail(_PUBLISHER_RED, pytrace=False)
    if any(not hasattr(verifier, name) for name in verifier_required):
        pytest.fail(_VERIFIER_RED, pytrace=False)
    return publisher, verifier


def _artifact_identity(
    *,
    value: Mapping[str, Any],
    path: str,
    role: str,
    schema: str,
    hash_key: str,
) -> tuple[dict[str, Any], bytes]:
    raw = _published_bytes(value)
    identity = {
        "artifact_role": role,
        "schema_version": schema,
        "repository_full_name": "MassyuRed/Cocolon",
        "path": path,
        "git_blob_sha1": _git_blob_sha1(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "logical_artifact_sha256": value[hash_key],
        "body_free": True,
    }
    return identity, raw


def _artifact_meta() -> dict[str, tuple[str, str, str]]:
    result = {
        _ACCEPTED_PATH: (
            "ACCEPTED_TEST_RUN_RECEIPT",
            _ACCEPTED_SCHEMA,
            "accepted_test_run_receipt_sha256",
        ),
        _ALL11_PATH: (
            "ALL11_COMPLETION_CHAIN",
            _ALL11_SCHEMA,
            "all11_completion_chain_sha256",
        ),
        _MANIFEST_PATH: (
            "ALL11_ATOMIC_PUBLICATION_MANIFEST",
            _MANIFEST_SCHEMA,
            "atomic_publication_manifest_sha256",
        ),
    }
    for path in _STEP_PATHS:
        result[path] = (
            "CURRENT_STEP_COMPLETION_RECEIPT",
            _STEP_SCHEMA,
            "receipt_sha256",
        )
    return result


def _base_snapshot(
    *,
    head_commit: str,
    parent_commit: str,
    entries: Mapping[str, str],
    blobs: Mapping[str, bytes],
) -> dict[str, Any]:
    tree = _fake_tree_id(entries)
    return {
        "snapshot_kind": "BODY_FREE_FAKE_GIT_OBJECT_GRAPH_V1",
        "head_commit_sha1": head_commit,
        "commits": {
            _P0_DOCUMENT_COMMIT: {
                "parent_commit_sha1s": ["0" * 40],
                "tree_sha1": "1" * 40,
            },
            _P0_RECEIPT_COMMIT: {
                "parent_commit_sha1s": [_P0_DOCUMENT_COMMIT],
                "tree_sha1": "2" * 40,
            },
            head_commit: {
                "parent_commit_sha1s": [parent_commit],
                "tree_sha1": tree,
            },
        },
        "trees": {tree: dict(entries)},
        "blobs": dict(blobs),
        "changed_paths_by_commit": {},
        "legacy_path_blob_by_commit": {
            _P0_DOCUMENT_COMMIT: {
                _P0_DOCUMENT_PATH: _P0_DOCUMENT_BLOB,
            },
            _P0_RECEIPT_COMMIT: {
                _P0_DOCUMENT_PATH: _P0_DOCUMENT_BLOB,
                _P0_RECEIPT_PATH: _P0_RECEIPT_BLOB,
            },
        },
        "legacy_raw_sha256_by_commit_path": {
            _P0_DOCUMENT_COMMIT: {
                _P0_DOCUMENT_PATH: _P0_DOCUMENT_RAW_SHA256,
            },
            _P0_RECEIPT_COMMIT: {
                _P0_DOCUMENT_PATH: _P0_DOCUMENT_RAW_SHA256,
                _P0_RECEIPT_PATH: _P0_RECEIPT_RAW_SHA256,
            },
        },
    }


def _logical_artifact_sha256(
    path: str,
    value: Mapping[str, Any],
) -> str:
    if path in {_EVENT1_PATH, _EVENT2_PATH}:
        return str(value["event_sha256"])
    if path == _SOURCE_RECEIPT_PATH:
        return str(value["source_baseline_closure_receipt_sha256"])
    _role, _schema, hash_key = _artifact_meta()[path]
    return str(value[hash_key])


def _identity_for_supporting_path(
    path: str,
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if path == _SOURCE_RECEIPT_PATH:
        role = "SOURCE_BASELINE_CLOSURE_RECEIPT"
        schema = _SOURCE_RECEIPT_SCHEMA
        hash_key = "source_baseline_closure_receipt_sha256"
    else:
        role, schema, hash_key = _artifact_meta()[path]
    identity, _raw = _artifact_identity(
        value=value,
        path=path,
        role=role,
        schema=schema,
        hash_key=hash_key,
    )
    return identity


def _supporting_set(
    *,
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
    base_commit: str,
    base_tree: str,
) -> dict[str, Any]:
    paths = sorted(artifacts_by_path)
    raw_by_path = {
        path: _published_bytes(artifacts_by_path[path])
        for path in paths
    }
    identities = [
        _identity_for_supporting_path(path, artifacts_by_path[path])
        for path in paths
    ]
    return {
        "repository_full_name": "MassyuRed/Cocolon",
        "branch": "main",
        "base_commit_sha1": base_commit,
        "base_tree_sha1": base_tree,
        "supporting_artifact_count": len(paths),
        "supporting_artifact_paths": paths,
        "supporting_artifacts": identities,
        "canonical_bytes_by_path": raw_by_path,
        "expected_git_blob_sha1_by_path": {
            path: _git_blob_sha1(raw)
            for path, raw in raw_by_path.items()
        },
        "expected_raw_sha256_by_path": {
            path: hashlib.sha256(raw).hexdigest()
            for path, raw in raw_by_path.items()
        },
        "expected_logical_artifact_sha256_by_path": {
            path: _logical_artifact_sha256(
                path,
                artifacts_by_path[path],
            )
            for path in paths
        },
        "ref_update_mode": _REF_UPDATE_MODE,
        "body_free": True,
    }


def _bundle(
    *,
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
    base_commit: str,
    base_tree: str,
) -> dict[str, Any]:
    values = {**artifacts_by_path, event["publication"]["event_path"]: event}
    raw_by_path = {
        path: _published_bytes(value) for path, value in values.items()
    }
    return {
        "repository_full_name": "MassyuRed/Cocolon",
        "branch": "main",
        "base_commit_sha1": base_commit,
        "base_tree_sha1": base_tree,
        "event_path": event["publication"]["event_path"],
        "changed_path_count": len(raw_by_path),
        "changed_paths": sorted(raw_by_path),
        "canonical_bytes_by_path": raw_by_path,
        "expected_git_blob_sha1_by_path": {
            path: _git_blob_sha1(raw)
            for path, raw in raw_by_path.items()
        },
        "expected_raw_sha256_by_path": {
            path: hashlib.sha256(raw).hexdigest()
            for path, raw in raw_by_path.items()
        },
        "expected_logical_artifact_sha256_by_path": {
            path: _logical_artifact_sha256(path, value)
            for path, value in values.items()
        },
        "ref_update_mode": _REF_UPDATE_MODE,
        "candidate_state": _CANDIDATE_STATE,
        "body_free": True,
    }


def _transaction(
    *,
    bundle: Mapping[str, Any],
    base_snapshot: Mapping[str, Any],
    target_commit: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    base_tree = bundle["base_tree_sha1"]
    entries = deepcopy(base_snapshot["trees"][base_tree])
    entries.update(bundle["expected_git_blob_sha1_by_path"])
    target_tree = _fake_tree_id(entries)
    transaction = {
        "target_commit_sha1": target_commit,
        "target_tree_sha1": target_tree,
        "parent_commit_sha1s": [bundle["base_commit_sha1"]],
        "write_mode": "SINGLE_TREE_SINGLE_COMMIT_EXPECTED_OLD_SHA_LEASE",
        "expected_old_sha": bundle["base_commit_sha1"],
        "body_free": True,
    }
    candidate = deepcopy(base_snapshot)
    candidate["commits"][target_commit] = {
        "parent_commit_sha1s": [bundle["base_commit_sha1"]],
        "tree_sha1": target_tree,
    }
    candidate["trees"][target_tree] = entries
    candidate["changed_paths_by_commit"][target_commit] = list(
        bundle["changed_paths"]
    )
    for raw in bundle["canonical_bytes_by_path"].values():
        candidate["blobs"][_git_blob_sha1(raw)] = raw
    return transaction, candidate


def _ref_update_observation(
    *,
    bundle: Mapping[str, Any],
    target_commit: str,
) -> dict[str, Any]:
    return {
        "ref": "refs/heads/main",
        "lease_precondition": {
            "expected_old_sha": bundle["base_commit_sha1"],
            "target_commit_sha1": target_commit,
        },
        "observed_head_before": bundle["base_commit_sha1"],
        "server_result": "EXPECTED_OLD_SHA_MATCHED_AND_UPDATED",
        "observed_head_after": target_commit,
        "body_free": True,
    }


def _published_snapshot(
    *,
    candidate_snapshot: Mapping[str, Any],
    target_commit: str,
) -> dict[str, Any]:
    result = deepcopy(candidate_snapshot)
    result["head_commit_sha1"] = target_commit
    return result


def _event1_case() -> dict[str, Any]:
    registry, closure, _nodes, _codes, _files = (
        accepted_red._formal_nodes_and_context()
    )
    source_closure = accepted_red._source_closure(
        registry=registry,
        closure=closure,
    )
    fixture = accepted_red._event1_fixture(source_closure)
    receipt = fixture["source_receipt_artifact"]
    event = fixture["artifact"]
    assert set(receipt) == _SOURCE_RECEIPT_KEYS
    assert set(event) == _EVENT_KEYS
    base_entries = {
        _P0_DOCUMENT_PATH: _P0_DOCUMENT_BLOB,
        _P0_RECEIPT_PATH: _P0_RECEIPT_BLOB,
    }
    snapshot = _base_snapshot(
        head_commit=_EVENT1_BASE_COMMIT,
        parent_commit=_P0_RECEIPT_COMMIT,
        entries=base_entries,
        blobs={},
    )
    base_tree = snapshot["commits"][_EVENT1_BASE_COMMIT]["tree_sha1"]
    artifacts = {_SOURCE_RECEIPT_PATH: receipt}
    supporting_set = _supporting_set(
        artifacts_by_path=artifacts,
        base_commit=_EVENT1_BASE_COMMIT,
        base_tree=base_tree,
    )
    bundle = _bundle(
        event=event,
        artifacts_by_path=artifacts,
        base_commit=_EVENT1_BASE_COMMIT,
        base_tree=base_tree,
    )
    transaction, candidate = _transaction(
        bundle=bundle,
        base_snapshot=snapshot,
        target_commit=_EVENT1_COMMIT,
    )
    published = _published_snapshot(
        candidate_snapshot=candidate,
        target_commit=_EVENT1_COMMIT,
    )
    ref_update_observation = _ref_update_observation(
        bundle=bundle,
        target_commit=_EVENT1_COMMIT,
    )
    return {
        "event": event,
        "artifacts_by_path": artifacts,
        "supporting_set": supporting_set,
        "bundle": bundle,
        "base_snapshot": snapshot,
        "transaction": transaction,
        "candidate_snapshot": candidate,
        "published_snapshot": published,
        "ref_update_observation": ref_update_observation,
        "published_identity": fixture["identity"],
        "source_closure": source_closure,
        "source_receipt": receipt,
    }


def _future_downstream_artifacts() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    valid, evidence = accepted_red._valid_v2_attempt_and_evidence()
    registry = (
        accepted_red.registry_owner
        .fresh_recovery_epoch001_current_step_requirement_registry()
    )
    source_event = evidence["source_baseline_event"]["artifact"]
    accepted = (
        accepted_red.accepted_owner
        .build_recovery_epoch001_accepted_test_run_receipt(
            formal_test_run_attempt=valid,
            requirement_registry=registry,
            source_baseline_event=source_event,
            publication_evidence=evidence,
            repo_root=_REPO_ROOT,
        )
    )
    all11_owner = _module_or_red(
        _ALL11_OWNER_PATH,
        "emlis_nls_v3_recovery_epoch001_all11_receipt_issue_fixture_target",
        _SEQUENCE_OWNER_RED,
    )
    receipts = list(
        all11_owner.stage_recovery_epoch001_all11_current_step_completion_receipts(
            requirement_registry=registry,
            accepted_test_run_receipt=accepted,
            source_baseline_event=source_event,
            publication_evidence=evidence,
            repo_root=_REPO_ROOT,
        )
    )
    chain = all11_owner.build_recovery_epoch001_all11_completion_chain(
        receipts=receipts,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        source_baseline_event=source_event,
        publication_evidence=evidence,
        repo_root=_REPO_ROOT,
    )
    return accepted, receipts, chain, evidence


def _event2_case() -> dict[str, Any]:
    accepted, receipts, chain, evidence = _future_downstream_artifacts()
    valid_source = valid_source_closure(evidence)
    values: dict[str, dict[str, Any]] = {_ACCEPTED_PATH: accepted}
    values.update(
        {path: receipt for path, receipt in zip(_STEP_PATHS, receipts)}
    )
    values[_ALL11_PATH] = chain
    meta = _artifact_meta()
    identities: dict[str, dict[str, Any]] = {}
    for path in sorted(_CORE_PATHS):
        role, schema, hash_key = meta[path]
        identities[path], _raw = _artifact_identity(
            value=values[path],
            path=path,
            role=role,
            schema=schema,
            hash_key=hash_key,
        )
    core = [identities[path] for path in sorted(_CORE_PATHS)]
    manifest: dict[str, Any] = {
        "schema_version": _MANIFEST_SCHEMA,
        "candidate_version_id": _CANDIDATE,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "source_baseline_event": deepcopy(
            evidence["source_baseline_event"]["identity"]
        ),
        "base_commit_sha1": _RESERVATION_COMMIT,
        "core_artifact_count": 13,
        "core_artifacts": core,
        "core_artifact_set_sha256": artifact_sha256(core),
        "event_supporting_artifact_count": 14,
        "expected_changed_path_count": 15,
        "event_path": _EVENT2_PATH,
        "ref_update_mode": _REF_UPDATE_MODE,
        "body_free": True,
        "atomic_publication_manifest_sha256": "",
    }
    manifest["atomic_publication_manifest_sha256"] = artifact_sha256(
        _material(manifest, "atomic_publication_manifest_sha256")
    )
    values[_MANIFEST_PATH] = manifest
    identities[_MANIFEST_PATH], _raw = _artifact_identity(
        value=manifest,
        path=_MANIFEST_PATH,
        role="ALL11_ATOMIC_PUBLICATION_MANIFEST",
        schema=_MANIFEST_SCHEMA,
        hash_key="atomic_publication_manifest_sha256",
    )
    supporting = [
        identities[path] for path in _EVENT2_SUPPORTING_PATHS
    ]
    authority = (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "EVENT2_TEST_OWNED_FIXTURE_ONLY"
    )
    event: dict[str, Any] = {
        "schema_version": _EVENT_SCHEMA,
        "ledger_id": _LEDGER,
        "event_id": (
            "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_002_"
            "STEP0_10_PREREQUISITES_PROVED"
        ),
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "event_name": "STEP0_10_PREREQUISITES_PROVED",
        "event_ordinal": 2,
        "state": "STEP0_10_PREREQUISITES_PROVED",
        "timestamp_utc": "2026-07-24T00:00:05Z",
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": authority,
            "publication_authority_token": authority,
        },
        "challenge_id": "e" * 64,
        "source_closure": deepcopy(valid_source),
        "prior_event": deepcopy(evidence["source_baseline_event"]["identity"]),
        "primary_evidence_artifact": deepcopy(identities[_ALL11_PATH]),
        "publication": {
            "repository_full_name": "MassyuRed/Cocolon",
            "branch": "main",
            "base_commit_sha1": _RESERVATION_COMMIT,
            "event_path": _EVENT2_PATH,
            "supporting_artifact_count": 14,
            "supporting_artifacts": supporting,
            "supporting_artifact_set_sha256": artifact_sha256(supporting),
            "expected_changed_path_count": 15,
            "ref_update_mode": _REF_UPDATE_MODE,
            "publication_state": "PUBLISHED_ATOMIC",
        },
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
    }
    event["event_sha256"] = artifact_sha256(
        _material(event, "event_sha256")
    )
    event1_case = _event1_case()
    reservation = evidence["formal_test_run_reservation"]
    base_entries = deepcopy(
        event1_case["published_snapshot"]["trees"][
            event1_case["transaction"]["target_tree_sha1"]
        ]
    )
    base_entries[reservation["identity"]["path"]] = reservation["identity"][
        "git_blob_sha1"
    ]
    base_blobs = deepcopy(event1_case["published_snapshot"]["blobs"])
    base_blobs[reservation["identity"]["git_blob_sha1"]] = reservation[
        "raw_bytes"
    ]
    base_tree = _fake_tree_id(base_entries)
    base_snapshot = deepcopy(event1_case["published_snapshot"])
    base_snapshot["head_commit_sha1"] = _RESERVATION_COMMIT
    base_snapshot["commits"][_RESERVATION_COMMIT] = {
        "parent_commit_sha1s": [_EVENT1_COMMIT],
        "tree_sha1": base_tree,
    }
    base_snapshot["trees"][base_tree] = base_entries
    base_snapshot["blobs"] = base_blobs
    base_snapshot["changed_paths_by_commit"][_RESERVATION_COMMIT] = [
        reservation["identity"]["path"]
    ]
    bundle = _bundle(
        event=event,
        artifacts_by_path=values,
        base_commit=_RESERVATION_COMMIT,
        base_tree=base_tree,
    )
    supporting_set = _supporting_set(
        artifacts_by_path=values,
        base_commit=_RESERVATION_COMMIT,
        base_tree=base_tree,
    )
    transaction, candidate = _transaction(
        bundle=bundle,
        base_snapshot=base_snapshot,
        target_commit=_EVENT2_COMMIT,
    )
    published = _published_snapshot(
        candidate_snapshot=candidate,
        target_commit=_EVENT2_COMMIT,
    )
    ref_update_observation = _ref_update_observation(
        bundle=bundle,
        target_commit=_EVENT2_COMMIT,
    )
    return {
        "event": event,
        "artifacts_by_path": values,
        "supporting_set": supporting_set,
        "artifact_meta": meta,
        "bundle": bundle,
        "base_snapshot": base_snapshot,
        "transaction": transaction,
        "candidate_snapshot": candidate,
        "published_snapshot": published,
        "ref_update_observation": ref_update_observation,
        "published_event1_identity": evidence[
            "source_baseline_event"
        ]["identity"],
        "publication_evidence": evidence,
        "source_closure": valid_source,
    }


def valid_source_closure(evidence: Mapping[str, Any]) -> dict[str, Any]:
    return deepcopy(
        evidence["source_baseline_event"]["artifact"]["source_closure"]
    )


def _rehash_event(case: dict[str, Any]) -> None:
    event = case["event"]
    event["publication"]["supporting_artifact_count"] = len(
        event["publication"]["supporting_artifacts"]
    )
    event["publication"]["supporting_artifact_set_sha256"] = artifact_sha256(
        event["publication"]["supporting_artifacts"]
    )
    event["event_sha256"] = artifact_sha256(
        _material(event, "event_sha256")
    )


def _rebuild_event2_case(case: dict[str, Any]) -> None:
    values = case["artifacts_by_path"]
    meta = case["artifact_meta"]
    identities: dict[str, dict[str, Any]] = {}
    for path in sorted(_CORE_PATHS):
        role, schema, hash_key = meta[path]
        value = values[path]
        value[hash_key] = artifact_sha256(_material(value, hash_key))
        identities[path], _raw = _artifact_identity(
            value=value,
            path=path,
            role=role,
            schema=schema,
            hash_key=hash_key,
        )
    manifest = values[_MANIFEST_PATH]
    core = [identities[path] for path in sorted(_CORE_PATHS)]
    manifest["core_artifacts"] = core
    manifest["core_artifact_count"] = len(core)
    manifest["core_artifact_set_sha256"] = artifact_sha256(core)
    manifest["atomic_publication_manifest_sha256"] = artifact_sha256(
        _material(manifest, "atomic_publication_manifest_sha256")
    )
    identities[_MANIFEST_PATH], _raw = _artifact_identity(
        value=manifest,
        path=_MANIFEST_PATH,
        role="ALL11_ATOMIC_PUBLICATION_MANIFEST",
        schema=_MANIFEST_SCHEMA,
        hash_key="atomic_publication_manifest_sha256",
    )
    supporting = [
        identities[path] for path in _EVENT2_SUPPORTING_PATHS
    ]
    case["event"]["primary_evidence_artifact"] = deepcopy(
        identities[_ALL11_PATH]
    )
    case["event"]["publication"]["supporting_artifacts"] = supporting
    _rehash_event(case)
    base_tree = case["bundle"]["base_tree_sha1"]
    case["bundle"] = _bundle(
        event=case["event"],
        artifacts_by_path=values,
        base_commit=case["bundle"]["base_commit_sha1"],
        base_tree=base_tree,
    )
    case["supporting_set"] = _supporting_set(
        artifacts_by_path=values,
        base_commit=case["bundle"]["base_commit_sha1"],
        base_tree=base_tree,
    )
    transaction, candidate = _transaction(
        bundle=case["bundle"],
        base_snapshot=case["base_snapshot"],
        target_commit=case["transaction"]["target_commit_sha1"],
    )
    case["transaction"] = transaction
    case["candidate_snapshot"] = candidate
    case["published_snapshot"] = _published_snapshot(
        candidate_snapshot=candidate,
        target_commit=transaction["target_commit_sha1"],
    )
    case["ref_update_observation"] = _ref_update_observation(
        bundle=case["bundle"],
        target_commit=transaction["target_commit_sha1"],
    )


def _sequence_issues(
    owner: ModuleType,
    verifier: ModuleType,
    case: Mapping[str, Any],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    kwargs = {
        "evidence_artifacts_by_path": case["artifacts_by_path"],
        "repository_snapshot": case["base_snapshot"],
    }
    return (
        _issue_codes(
            owner.validate_recovery_epoch001_sequence_transition_candidate(
                case["event"],
                **kwargs,
            )
        ),
        _issue_codes(
            verifier.verify_recovery_epoch001_sequence_transition_candidate(
                case["event"],
                **kwargs,
            )
        ),
    )


def _assert_sequence_exact(
    owner: ModuleType,
    verifier: ModuleType,
    case: Mapping[str, Any],
    expected: str,
) -> None:
    owner_issues, verifier_issues = _sequence_issues(owner, verifier, case)
    assert owner_issues == (expected,), owner_issues
    assert verifier_issues == (expected,), verifier_issues


def _publication_issues(
    owner: ModuleType,
    verifier: ModuleType,
    phase: str,
    case: Mapping[str, Any],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if phase == "supporting":
        owner_fn = (
            owner.validate_recovery_epoch001_atomic_publication_supporting_set
        )
        verifier_fn = (
            verifier
            .verify_recovery_epoch001_atomic_publication_supporting_set
        )
        kwargs = {
            "artifacts_by_path": case["artifacts_by_path"],
        }
        subject = case["supporting_set"]
    elif phase == "candidate":
        owner_fn = owner.validate_recovery_epoch001_atomic_publication_candidate
        verifier_fn = (
            verifier.verify_recovery_epoch001_atomic_publication_candidate
        )
        kwargs = {
            "event": case["event"],
            "artifacts_by_path": case["artifacts_by_path"],
        }
        subject = case["bundle"]
    elif phase == "preflight":
        owner_fn = owner.validate_recovery_epoch001_atomic_publication_preflight
        verifier_fn = (
            verifier.verify_recovery_epoch001_atomic_publication_preflight
        )
        kwargs = {
            "repository_snapshot": case["base_snapshot"],
            "transport_capabilities": case.get(
                "transport_capabilities",
                {
                    "base_tree_read": True,
                    "expected_old_sha_lease": True,
                    "single_ref_update": True,
                },
            ),
        }
        subject = case["bundle"]
    elif phase == "ref":
        owner_fn = owner.validate_recovery_epoch001_atomic_ref_update_plan
        verifier_fn = verifier.verify_recovery_epoch001_atomic_ref_update_plan
        kwargs = {
            "transaction": case["transaction"],
            "repository_snapshot": case["base_snapshot"],
            "candidate_snapshot": case["candidate_snapshot"],
            "transport_capabilities": case.get(
                "transport_capabilities",
                {
                    "base_tree_read": True,
                    "expected_old_sha_lease": True,
                    "single_ref_update": True,
                },
            ),
        }
        subject = case["bundle"]
    elif phase == "published":
        owner_fn = owner.validate_recovery_epoch001_atomic_publication_result
        verifier_fn = (
            verifier.verify_recovery_epoch001_atomic_publication_result
        )
        kwargs = {
            "transaction": case["transaction"],
            "candidate_snapshot": case["candidate_snapshot"],
            "repository_snapshot": case["published_snapshot"],
            "ref_update_observation": case["ref_update_observation"],
            "event": case["event"],
            "artifacts_by_path": case["artifacts_by_path"],
        }
        subject = case["bundle"]
    else:
        raise AssertionError(f"unknown phase: {phase}")
    return (
        _issue_codes(owner_fn(subject, **kwargs)),
        _issue_codes(verifier_fn(subject, **kwargs)),
    )


def _assert_publication_exact(
    owner: ModuleType,
    verifier: ModuleType,
    phase: str,
    case: Mapping[str, Any],
    expected: str,
) -> None:
    owner_issues, verifier_issues = _publication_issues(
        owner,
        verifier,
        phase,
        case,
    )
    assert owner_issues == (expected,), owner_issues
    assert verifier_issues == (expected,), verifier_issues
    try:
        if phase == "candidate":
            state = (
                owner.classify_recovery_epoch001_atomic_publication_candidate(
                    case["bundle"],
                    event=case["event"],
                    artifacts_by_path=case["artifacts_by_path"],
                )
            )
            assert state != _CANDIDATE_STATE
        elif phase == "published":
            state = owner.classify_recovery_epoch001_atomic_publication_result(
                case["bundle"],
                transaction=case["transaction"],
                candidate_snapshot=case["candidate_snapshot"],
                repository_snapshot=case["published_snapshot"],
                ref_update_observation=case["ref_update_observation"],
                event=case["event"],
                artifacts_by_path=case["artifacts_by_path"],
            )
            assert state != _PUBLISHED_STATE
    except ValueError:
        pass


def _assert_sequence_clean(
    owner: ModuleType,
    verifier: ModuleType,
    case: Mapping[str, Any],
) -> None:
    owner_issues, verifier_issues = _sequence_issues(
        owner,
        verifier,
        case,
    )
    assert owner_issues == (), owner_issues
    assert verifier_issues == (), verifier_issues


def _assert_publication_clean(
    owner: ModuleType,
    verifier: ModuleType,
    phase: str,
    case: Mapping[str, Any],
) -> None:
    owner_issues, verifier_issues = _publication_issues(
        owner,
        verifier,
        phase,
        case,
    )
    assert owner_issues == (), owner_issues
    assert verifier_issues == (), verifier_issues


def _remove_bundle_path(case: dict[str, Any], path: str) -> None:
    bundle = case["bundle"]
    bundle["changed_paths"].remove(path)
    bundle["canonical_bytes_by_path"].pop(path)
    bundle["expected_git_blob_sha1_by_path"].pop(path)
    bundle["expected_raw_sha256_by_path"].pop(path)
    bundle["expected_logical_artifact_sha256_by_path"].pop(path)
    bundle["changed_path_count"] = len(bundle["changed_paths"])


def _add_bundle_path(
    case: dict[str, Any],
    *,
    path: str,
    value: Mapping[str, Any],
    logical_sha256: str,
) -> None:
    raw = _published_bytes(value)
    bundle = case["bundle"]
    case["artifacts_by_path"][path] = deepcopy(value)
    bundle["changed_paths"].append(path)
    bundle["changed_paths"].sort()
    bundle["canonical_bytes_by_path"][path] = raw
    bundle["expected_git_blob_sha1_by_path"][path] = _git_blob_sha1(raw)
    bundle["expected_raw_sha256_by_path"][path] = hashlib.sha256(
        raw
    ).hexdigest()
    bundle["expected_logical_artifact_sha256_by_path"][
        path
    ] = logical_sha256
    bundle["changed_path_count"] = len(bundle["changed_paths"])


def _replace_chain_receipt(
    case: dict[str, Any],
    *,
    index: int,
    receipt: Mapping[str, Any],
) -> None:
    path = _STEP_PATHS[index]
    row = deepcopy(receipt)
    row["receipt_sha256"] = artifact_sha256(
        _material(row, "receipt_sha256")
    )
    case["artifacts_by_path"][path] = deepcopy(row)
    chain = case["artifacts_by_path"][_ALL11_PATH]
    chain["receipts"][index] = deepcopy(row)
    chain["receipt_sha256s"][index] = row["receipt_sha256"]
    identity, _raw = _artifact_identity(
        value=row,
        path=path,
        role="CURRENT_STEP_COMPLETION_RECEIPT",
        schema=_STEP_SCHEMA,
        hash_key="receipt_sha256",
    )
    chain["receipt_artifacts"][index] = identity


def _assert_independent_verifier_imports_are_split() -> None:
    tree = ast.parse(
        (_REPO_ROOT / _VERIFIER_PATH).read_text(encoding="utf-8")
    )
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
    allowed_local = {"emlis_ai_nls_v3_artifact_contract"}
    local_imports = {
        imported.rsplit(".", maxsplit=1)[-1]
        for imported in imports
        if imported.startswith(("emlis_", "ai."))
    }
    assert local_imports <= allowed_local, sorted(local_imports)


def _event2_builder_kwargs(case: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "published_event1_identity": case["published_event1_identity"],
        "source_closure": case["source_closure"],
        "all11_completion_chain": case["artifacts_by_path"][_ALL11_PATH],
        "all11_completion_chain_identity": case["event"][
            "primary_evidence_artifact"
        ],
        "supporting_set": case["supporting_set"],
        "supporting_artifacts": case["event"]["publication"][
            "supporting_artifacts"
        ],
        "authority_token": case["event"]["authority"][
            "transition_authority_token"
        ],
        "challenge_id": case["event"]["challenge_id"],
        "publication": case["event"]["publication"],
        "formal_test_run_evidence": case["publication_evidence"],
        "evidence_artifacts_by_path": case["artifacts_by_path"],
        "repository_snapshot": case["base_snapshot"],
        "clock_utc": lambda: case["event"]["timestamp_utc"],
    }


def test_sequence_red_authority_literal_paths_and_legacy_anchor_are_exact(
) -> None:
    assert _AUTHORITY.endswith("_RED_FREEZE_ONLY")
    assert _AUTHORITY == (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_EXACT134_"
        "SUCCESS_AND_SEQUENCE_EVENT1_EVENT2_SHAREABLE_LEDGER_ATOMIC_PUBLICATION_"
        "CONTRACT_RECONCILIATION_RED_FREEZE_ONLY"
    )
    assert _KAREN_DIARY_PIN == "700f749f5149cac1f8bd4bab8a364d524a56985b"
    assert _COCOLON_RED_ENTRY_PIN == "fee21e9a92450d4171536f280e859d95e344804e"
    assert _SOURCE_RED_ENTRY_PIN == "78276950d0d7650968fe938bc63a6e13455a8d6c"
    assert _SOURCE_RED_ENTRY_TREE == "e13b8bcfce4d56ab1b25d0a4309326b8cc36eca2"
    assert _DESIGN_BLOB == "7e7d454d888141cbdb872244bf6df93c046e0b6c"
    assert len(_DESIGN_SHA256) == 64
    assert len(_DETAILED_DESIGN_SHA256) == 64
    assert _EVENT_SCHEMA.endswith("sequence_event.v2")
    assert _SOURCE_RECEIPT_SCHEMA.endswith(
        "source_baseline_closure_receipt.v2"
    )
    assert _ALL11_SCHEMA.endswith("all11_completion_chain.v2")
    assert _MANIFEST_SCHEMA.endswith("all11_atomic_publication_manifest.v2")
    assert len(_EVENT_KEYS) == 20
    assert len(_AUTHORITY_KEYS) == 3
    assert len(_SOURCE_CLOSURE_KEYS) == 10
    assert len(_ARTIFACT_IDENTITY_KEYS) == 8
    assert len(_PUBLICATION_KEYS) == 10
    assert len(_P0_KEYS) == 17
    assert len(_PUBLISHED_EVENT_IDENTITY_KEYS) == 14
    assert len(_SOURCE_RECEIPT_KEYS) == 12
    assert len(_MANIFEST_KEYS) == 15
    assert len(_EVENT1_PATHS) == 2
    assert len(_CORE_PATHS) == 13
    assert len(_EVENT2_SUPPORTING_PATHS) == 14
    assert len(_EVENT2_PATHS) == 15
    assert len(_EVENT_PATHS_EXACT17) == 17
    assert _EVENT1_PATHS.isdisjoint(_EVENT2_PATHS)
    assert _P0_DOCUMENT_BLOB == "3333ae29ec0f4e9dde614bc9cd520448f61d2386"
    assert _P0_RECEIPT_BLOB == "bdfbd559535db06ae4af35fe1bb58716d6566126"
    assert len(_P0_DOCUMENT_RAW_SHA256) == 64
    assert len(_P0_RECEIPT_RAW_SHA256) == 64
    assert _P0_DOCUMENT_COMMIT == "90a2c009b8a463110e01b907224e52ea50912bd8"
    assert _P0_RECEIPT_COMMIT == "f20165e3eda11dc0262373d5f82f63377df76f10"
    assert set(_SEQUENCE_EXPECTATIONS) == {
        "L01",
        "L02",
        "L03",
        "L04",
        "L05",
        "L06",
        "L07",
        "L08",
        "L09",
        "S01",
        "S03",
        "S04",
    }
    assert set(_PUBLICATION_EXPECTATIONS) == {
        "P01",
        "P02",
        "P03",
        "P05",
        "P06",
        "P07",
        "P08",
        "P09",
        "P10",
    }


def test_sequence_owner_publisher_and_independent_verifier_surface_or_red(
) -> None:
    sequence, _sequence_verifier = _sequence_apis_or_red()
    publisher, _publication_verifier = _publication_apis_or_red()
    assert sequence.RECOVERY_EPOCH001_SEQUENCE_EVENT_SCHEMA == _EVENT_SCHEMA
    assert (
        publisher.RECOVERY_EPOCH001_CANDIDATE_PUBLICATION_VALID_STATE
        == _CANDIDATE_STATE
    )
    assert (
        publisher.RECOVERY_EPOCH001_PUBLISHED_ATOMIC_VALID_STATE
        == _PUBLISHED_STATE
    )
    assert callable(
        sequence.RECOVERY_EPOCH001_INDEPENDENT_SEQUENCE_VERIFIER
    )
    _assert_independent_verifier_imports_are_split()


def test_sequence_valid_candidate_is_unreachable_not_published_or_red(
) -> None:
    sequence, sequence_verifier = _sequence_apis_or_red()
    publisher, publication_verifier = _publication_apis_or_red()
    event1 = _event1_case()
    receipt = sequence.build_recovery_epoch001_source_baseline_closure_receipt(
        source_closure=event1["source_closure"],
        prior_anchor=event1["event"]["prior_event"],
        authority_token=event1["event"]["authority"][
            "transition_authority_token"
        ],
        challenge_id=event1["event"]["challenge_id"],
    )
    assert receipt == event1["source_receipt"]
    built_supporting1 = (
        publisher
        .build_recovery_epoch001_event1_atomic_publication_supporting_set(
            artifacts_by_path=event1["artifacts_by_path"],
            base_snapshot=event1["base_snapshot"],
        )
    )
    assert built_supporting1 == event1["supporting_set"]
    _assert_publication_clean(
        publisher,
        publication_verifier,
        "supporting",
        event1,
    )
    built_event1 = sequence.build_recovery_epoch001_sequence_event_1(
        source_baseline_closure_receipt=receipt,
        source_baseline_closure_receipt_identity=event1["event"][
            "primary_evidence_artifact"
        ],
        supporting_set=built_supporting1,
        prior_anchor=event1["event"]["prior_event"],
        publication=event1["event"]["publication"],
        clock_utc=lambda: event1["event"]["timestamp_utc"],
    )
    assert built_event1 == event1["event"]
    built_bundle1 = (
        publisher.build_recovery_epoch001_event1_atomic_publication_bundle(
            event=event1["event"],
            supporting_set=built_supporting1,
            base_snapshot=event1["base_snapshot"],
        )
    )
    assert built_bundle1 == event1["bundle"]
    _assert_sequence_clean(sequence, sequence_verifier, event1)
    _assert_publication_clean(
        publisher,
        publication_verifier,
        "candidate",
        event1,
    )
    assert publisher.classify_recovery_epoch001_atomic_publication_candidate(
        event1["bundle"],
        event=event1["event"],
        artifacts_by_path=event1["artifacts_by_path"],
    ) == _CANDIDATE_STATE

    event2 = _event2_case()
    assert (
        event2["published_event1_identity"]
        == event1["published_identity"]
    )
    assert _issue_codes(
        sequence.validate_recovery_epoch001_owner_verifier_agreement(
            owner_issues=(),
            verifier_issues=(),
        )
    ) == ()
    built_supporting2 = (
        publisher
        .build_recovery_epoch001_event2_atomic_publication_supporting_set(
            artifacts_by_path=event2["artifacts_by_path"],
            base_snapshot=event2["base_snapshot"],
        )
    )
    assert built_supporting2 == event2["supporting_set"]
    _assert_publication_clean(
        publisher,
        publication_verifier,
        "supporting",
        event2,
    )
    built_event2 = sequence.build_recovery_epoch001_sequence_event_2(
        **_event2_builder_kwargs(event2)
    )
    assert built_event2 == event2["event"]
    built_bundle2 = (
        publisher.build_recovery_epoch001_event2_atomic_publication_bundle(
            event=event2["event"],
            supporting_set=built_supporting2,
            base_snapshot=event2["base_snapshot"],
        )
    )
    assert built_bundle2 == event2["bundle"]
    _assert_sequence_clean(sequence, sequence_verifier, event2)
    _assert_publication_clean(
        publisher,
        publication_verifier,
        "candidate",
        event2,
    )
    assert publisher.classify_recovery_epoch001_atomic_publication_candidate(
        event2["bundle"],
        event=event2["event"],
        artifacts_by_path=event2["artifacts_by_path"],
    ) == _CANDIDATE_STATE


def test_sequence_valid_published_requires_lease_direct_child_and_postfetch_or_red(
) -> None:
    sequence, sequence_verifier = _sequence_apis_or_red()
    publisher, publication_verifier = _publication_apis_or_red()
    for case in (_event1_case(), _event2_case()):
        _assert_sequence_clean(sequence, sequence_verifier, case)
        for phase in (
            "supporting",
            "candidate",
            "preflight",
            "ref",
            "published",
        ):
            _assert_publication_clean(
                publisher,
                publication_verifier,
                phase,
                case,
            )
        assert (
            publisher.classify_recovery_epoch001_atomic_publication_result(
                case["bundle"],
                transaction=case["transaction"],
                candidate_snapshot=case["candidate_snapshot"],
                repository_snapshot=case["published_snapshot"],
                ref_update_observation=case["ref_update_observation"],
                event=case["event"],
                artifacts_by_path=case["artifacts_by_path"],
            )
            == _PUBLISHED_STATE
        )


def test_l01_event_v2_exact_schema_required_fields() -> None:
    sequence, verifier = _sequence_apis_or_red()
    for missing in (
        "state",
        "timestamp_utc",
        "prior_event",
        "primary_evidence_artifact",
    ):
        case = _event1_case()
        case["event"].pop(missing)
        case["event"]["event_sha256"] = artifact_sha256(
            _material(case["event"], "event_sha256")
        )
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L01"],
        )
    case = _event1_case()
    case["event"]["unexpected"] = "FORBIDDEN"
    _rehash_event(case)
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["L01"],
    )


def test_l02_event_ordinal_bool_is_rejected() -> None:
    sequence, verifier = _sequence_apis_or_red()
    for value in (False, True):
        case = _event1_case()
        case["event"]["event_ordinal"] = value
        _rehash_event(case)
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L02"],
        )


def test_l03_event_timestamp_is_internal_utc_seconds_and_monotonic() -> None:
    sequence, verifier = _sequence_apis_or_red()
    assert "timestamp_utc" not in inspect.signature(
        sequence.build_recovery_epoch001_sequence_event_1
    ).parameters
    assert "timestamp_utc" not in inspect.signature(
        sequence.build_recovery_epoch001_sequence_event_2
    ).parameters
    for value in (
        "2026-07-24 00:00:00Z",
        "2026-07-24T09:00:00+09:00",
        "2026-07-24T00:00:00.000Z",
        "2026-07-22T22:37:06Z",
    ):
        case = _event1_case()
        case["event"]["timestamp_utc"] = value
        _rehash_event(case)
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L03"],
        )
    case = _event2_case()
    case["event"]["timestamp_utc"] = "2026-07-24T00:00:01Z"
    _rehash_event(case)
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["L03"],
    )


def test_l04_event1_requires_exact_legacy_p0_anchor_identity_and_ancestry(
) -> None:
    sequence, verifier = _sequence_apis_or_red()
    mutations = {
        "document_path": f"{_P0_DOCUMENT_PATH}.drift",
        "document_publication_commit_sha1": "3" * 40,
        "document_git_blob_sha1": "3" * 40,
        "document_raw_sha256": "3" * 64,
        "receipt_path": f"{_P0_RECEIPT_PATH}.drift",
        "receipt_publication_commit_sha1": "4" * 40,
        "receipt_git_blob_sha1": "4" * 40,
        "receipt_raw_sha256": "4" * 64,
        "anchor_publication_commit_sha1": "4" * 40,
    }
    for key, value in mutations.items():
        case = _event1_case()
        case["event"]["prior_event"][key] = value
        _identity_hash(case["event"]["prior_event"])
        _rehash_event(case)
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L04"],
        )
    case = _event1_case()
    sibling = "5" * 40
    case["base_snapshot"]["commits"][sibling] = {
        "parent_commit_sha1s": ["0" * 40],
        "tree_sha1": case["base_snapshot"]["commits"][
            _EVENT1_BASE_COMMIT
        ]["tree_sha1"],
    }
    case["base_snapshot"]["commits"][_EVENT1_BASE_COMMIT][
        "parent_commit_sha1s"
    ] = [sibling]
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["L04"],
    )


def test_l05_late_event0_backfill_is_forbidden() -> None:
    sequence, verifier = _sequence_apis_or_red()
    case = _event1_case()
    event0_path = f"{_PREFIX}ForbiddenLateSequenceEvent00.json"
    evidence = deepcopy(case["event"]["primary_evidence_artifact"])
    event0: dict[str, Any] = {
        "schema_version": _EVENT_SCHEMA,
        "ledger_id": _LEDGER,
        "event_id": (
            "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_000_"
            "LATE_PARENT_WRAPPER"
        ),
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "event_name": "PARENT_ADDENDUM_FROZEN",
        "event_ordinal": 0,
        "state": "DEFINED_NOT_STARTED",
        "timestamp_utc": "2026-07-22T22:37:07Z",
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": (
                "FORBIDDEN_TEST_OWNED_LATE_EVENT0"
            ),
            "publication_authority_token": (
                "FORBIDDEN_TEST_OWNED_LATE_EVENT0"
            ),
        },
        "challenge_id": "6" * 64,
        "source_closure": deepcopy(case["source_closure"]),
        "prior_event": deepcopy(case["event"]["prior_event"]),
        "primary_evidence_artifact": evidence,
        "publication": {
            "repository_full_name": "MassyuRed/Cocolon",
            "branch": "main",
            "base_commit_sha1": _P0_RECEIPT_COMMIT,
            "event_path": event0_path,
            "supporting_artifact_count": 1,
            "supporting_artifacts": [deepcopy(evidence)],
            "supporting_artifact_set_sha256": artifact_sha256([evidence]),
            "expected_changed_path_count": 2,
            "ref_update_mode": _REF_UPDATE_MODE,
            "publication_state": "PUBLISHED_ATOMIC",
        },
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
    }
    event0["event_sha256"] = artifact_sha256(
        _material(event0, "event_sha256")
    )
    event0_raw = _published_bytes(event0)
    event0_commit = "6" * 40
    wrapper: dict[str, Any] = {
        "identity_kind": "PUBLISHED_SEQUENCE_EVENT",
        "ledger_id": _LEDGER,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "event_id": event0["event_id"],
        "event_name": event0["event_name"],
        "event_ordinal": event0["event_ordinal"],
        "state": event0["state"],
        "timestamp_utc": event0["timestamp_utc"],
        "event_path": event0_path,
        "event_git_blob_sha1": _git_blob_sha1(event0_raw),
        "event_raw_sha256": hashlib.sha256(event0_raw).hexdigest(),
        "event_sha256": event0["event_sha256"],
        "publication_commit_sha1": event0_commit,
        "identity_sha256": "",
    }
    _identity_hash(wrapper)
    assert set(wrapper) == _PUBLISHED_EVENT_IDENTITY_KEYS
    base_tree = case["base_snapshot"]["commits"][
        _EVENT1_BASE_COMMIT
    ]["tree_sha1"]
    entries = deepcopy(case["base_snapshot"]["trees"][base_tree])
    source_raw = _published_bytes(case["source_receipt"])
    entries[_SOURCE_RECEIPT_PATH] = _git_blob_sha1(source_raw)
    entries[event0_path] = wrapper["event_git_blob_sha1"]
    wrapper_tree = _fake_tree_id(entries)
    case["base_snapshot"]["trees"][wrapper_tree] = entries
    case["base_snapshot"]["blobs"][_git_blob_sha1(source_raw)] = source_raw
    case["base_snapshot"]["blobs"][
        wrapper["event_git_blob_sha1"]
    ] = event0_raw
    case["base_snapshot"]["commits"][event0_commit] = {
        "parent_commit_sha1s": [_P0_RECEIPT_COMMIT],
        "tree_sha1": wrapper_tree,
    }
    case["base_snapshot"]["changed_paths_by_commit"][event0_commit] = [
        _SOURCE_RECEIPT_PATH,
        event0_path,
    ]
    case["base_snapshot"]["commits"][_EVENT1_BASE_COMMIT] = {
        "parent_commit_sha1s": [event0_commit],
        "tree_sha1": wrapper_tree,
    }
    case["event"]["prior_event"] = wrapper
    _rehash_event(case)
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["L05"],
    )


def test_l06_event_blob_self_reference_is_forbidden() -> None:
    sequence, verifier = _sequence_apis_or_red()
    case = _event1_case()
    old_path = case["event"]["primary_evidence_artifact"]["path"]
    case["event"]["primary_evidence_artifact"]["path"] = _EVENT1_PATH
    for row in case["event"]["publication"]["supporting_artifacts"]:
        if row["path"] == old_path:
            row["path"] = _EVENT1_PATH
    _rehash_event(case)
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["L06"],
    )


def test_l07_event2_requires_exact_published_event1_identity() -> None:
    sequence, verifier = _sequence_apis_or_red()
    mutations = {
        "event_path": f"{_EVENT1_PATH}.drift",
        "event_git_blob_sha1": "8" * 40,
        "event_raw_sha256": "8" * 64,
        "event_sha256": "9" * 64,
        "publication_commit_sha1": "8" * 40,
    }
    for key, value in mutations.items():
        case = _event2_case()
        case["event"]["prior_event"][key] = value
        _identity_hash(case["event"]["prior_event"])
        _rehash_event(case)
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L07"],
        )


def test_l08_event2_requires_published_event1_ancestry_and_no_skip() -> None:
    sequence, verifier = _sequence_apis_or_red()
    for ordinal in (1, 3):
        case = _event2_case()
        case["event"]["event_ordinal"] = ordinal
        _rehash_event(case)
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L08"],
        )
    case = _event2_case()
    sibling = "5" * 40
    base_tree = case["base_snapshot"]["commits"][
        _RESERVATION_COMMIT
    ]["tree_sha1"]
    case["base_snapshot"]["commits"][sibling] = {
        "parent_commit_sha1s": [_P0_RECEIPT_COMMIT],
        "tree_sha1": base_tree,
    }
    case["base_snapshot"]["commits"][_RESERVATION_COMMIT][
        "parent_commit_sha1s"
    ] = [sibling]
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["L08"],
    )


def test_l09_primary_evidence_identity_is_exact() -> None:
    sequence, verifier = _sequence_apis_or_red()
    mutations = {
        "path": f"{_SOURCE_RECEIPT_PATH}.drift",
        "git_blob_sha1": "a" * 40,
        "raw_sha256": "a" * 64,
        "logical_artifact_sha256": "b" * 64,
    }
    for key, value in mutations.items():
        case = _event1_case()
        old_path = case["event"]["primary_evidence_artifact"]["path"]
        case["event"]["primary_evidence_artifact"][key] = value
        for row in case["event"]["publication"]["supporting_artifacts"]:
            if row["path"] == old_path:
                row[key] = value
        _rehash_event(case)
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["L09"],
        )


def test_s01_event2_rejects_non_exact11_receipt_sequence() -> None:
    sequence, verifier = _sequence_apis_or_red()
    cases: list[dict[str, Any]] = []

    missing = _event2_case()
    chain = missing["artifacts_by_path"][_ALL11_PATH]
    for key in ("receipts", "receipt_artifacts", "receipt_sha256s"):
        chain[key].pop()
    chain["ordered_steps"].pop()
    chain["receipt_count"] = 10
    _rebuild_event2_case(missing)
    cases.append(missing)

    extra = _event2_case()
    chain = extra["artifacts_by_path"][_ALL11_PATH]
    for key in ("receipts", "receipt_artifacts", "receipt_sha256s"):
        chain[key].append(deepcopy(chain[key][-1]))
    chain["ordered_steps"].append(11)
    chain["receipt_count"] = 12
    _rebuild_event2_case(extra)
    cases.append(extra)

    duplicate = _event2_case()
    chain = duplicate["artifacts_by_path"][_ALL11_PATH]
    for key in ("receipts", "receipt_artifacts", "receipt_sha256s"):
        chain[key][5] = deepcopy(chain[key][4])
    _rebuild_event2_case(duplicate)
    cases.append(duplicate)

    reordered = _event2_case()
    chain = reordered["artifacts_by_path"][_ALL11_PATH]
    for key in (
        "ordered_steps",
        "receipts",
        "receipt_artifacts",
        "receipt_sha256s",
    ):
        chain[key][0], chain[key][1] = chain[key][1], chain[key][0]
    _rebuild_event2_case(reordered)
    cases.append(reordered)

    for case in cases:
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            _SEQUENCE_EXPECTATIONS["S01"],
        )


def test_s02_event2_rejects_all11_root_parent_and_boundary_conflicts(
) -> None:
    sequence, verifier = _sequence_apis_or_red()

    root_drift = _event2_case()
    root_drift["artifacts_by_path"][_ALL11_PATH]["source_closure"][
        "source_commit_sha1"
    ] = "e" * 40
    _rebuild_event2_case(root_drift)

    parent_drift = _event2_case()
    receipt = deepcopy(parent_drift["artifacts_by_path"][_STEP_PATHS[5]])
    receipt["parent_binding"]["previous_receipt_sha256"] = "e" * 64
    _replace_chain_receipt(parent_drift, index=5, receipt=receipt)
    _rebuild_event2_case(parent_drift)

    boundary_drift = _event2_case()
    receipt = deepcopy(boundary_drift["artifacts_by_path"][_STEP_PATHS[10]])
    receipt["next_authority"] = "P2_AUTOMATIC_START"
    _replace_chain_receipt(boundary_drift, index=10, receipt=receipt)
    boundary_drift["artifacts_by_path"][_ALL11_PATH][
        "next_authority"
    ] = "P2_AUTOMATIC_START"
    _rebuild_event2_case(boundary_drift)

    for case, expected in (
        (root_drift, "SOURCE_OR_ROOT_DRIFT"),
        (parent_drift, "SEQUENCE_INVALID"),
        (boundary_drift, "P2_NOT_AUTHORIZED"),
    ):
        _assert_sequence_exact(
            sequence,
            verifier,
            case,
            expected,
        )


def test_s03_event2_rejects_owner_verifier_disagreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sequence, _verifier = _sequence_apis_or_red()
    issues = _issue_codes(
        sequence.validate_recovery_epoch001_owner_verifier_agreement(
            owner_issues=(),
            verifier_issues=("HASH_MISMATCH",),
        )
    )
    assert issues == (_SEQUENCE_EXPECTATIONS["S03"],)
    case = _event2_case()
    monkeypatch.setattr(
        sequence,
        "RECOVERY_EPOCH001_INDEPENDENT_SEQUENCE_VERIFIER",
        lambda *_args, **_kwargs: ("HASH_MISMATCH",),
    )
    with pytest.raises(ValueError, match="^OWNER_VERIFIER_CONFLICT$"):
        sequence.build_recovery_epoch001_sequence_event_2(
            **_event2_builder_kwargs(case)
        )


def test_s04_step10_never_authorizes_or_starts_p2() -> None:
    sequence, verifier = _sequence_apis_or_red()
    case = _event2_case()
    case["event"]["automatic_progression"] = True
    _rehash_event(case)
    _assert_sequence_exact(
        sequence,
        verifier,
        case,
        _SEQUENCE_EXPECTATIONS["S04"],
    )


def test_p01_event1_atomic_bundle_requires_exact2_paths() -> None:
    publisher, verifier = _publication_apis_or_red()
    missing = _event1_case()
    _remove_bundle_path(missing, _SOURCE_RECEIPT_PATH)
    extra = _event1_case()
    value = {
        "schema_version": "cocolon.test.extra.v1",
        "body_free": True,
        "artifact_sha256": "",
    }
    value["artifact_sha256"] = artifact_sha256(
        _material(value, "artifact_sha256")
    )
    _add_bundle_path(
        extra,
        path=f"{_PREFIX}UnexpectedEvent1Extra.json",
        value=value,
        logical_sha256=value["artifact_sha256"],
    )
    for case in (missing, extra):
        _assert_publication_exact(
            publisher,
            verifier,
            "candidate",
            case,
            _PUBLICATION_EXPECTATIONS["P01"],
        )


def test_p02_event2_atomic_bundle_requires_exact15_paths() -> None:
    publisher, verifier = _publication_apis_or_red()
    missing = _event2_case()
    _remove_bundle_path(missing, _STEP_PATHS[10])
    extra = _event2_case()
    value = {
        "schema_version": "cocolon.test.extra.v1",
        "body_free": True,
        "artifact_sha256": "",
    }
    value["artifact_sha256"] = artifact_sha256(
        _material(value, "artifact_sha256")
    )
    _add_bundle_path(
        extra,
        path=f"{_PREFIX}UnexpectedEvent2Extra.json",
        value=value,
        logical_sha256=value["artifact_sha256"],
    )
    for case in (missing, extra):
        _assert_publication_exact(
            publisher,
            verifier,
            "candidate",
            case,
            _PUBLICATION_EXPECTATIONS["P02"],
        )


def test_p03_supporting_artifacts_are_exact_unique_and_lexical() -> None:
    publisher, verifier = _publication_apis_or_red()
    event1_cases: list[dict[str, Any]] = []

    event1_missing = _event1_case()
    path = event1_missing["supporting_set"][
        "supporting_artifact_paths"
    ].pop()
    event1_missing["supporting_set"]["supporting_artifacts"].pop()
    for key in (
        "canonical_bytes_by_path",
        "expected_git_blob_sha1_by_path",
        "expected_raw_sha256_by_path",
        "expected_logical_artifact_sha256_by_path",
    ):
        event1_missing["supporting_set"][key].pop(path)
    event1_missing["supporting_set"]["supporting_artifact_count"] = 0
    event1_missing["artifacts_by_path"].pop(path)
    event1_cases.append(event1_missing)

    event1_extra = _event1_case()
    path = f"{_PREFIX}UnexpectedEvent1SupportingArtifact.json"
    value: dict[str, Any] = {
        "schema_version": "cocolon.test.unexpected.v1",
        "body_free": True,
        "artifact_sha256": "",
    }
    value["artifact_sha256"] = artifact_sha256(
        _material(value, "artifact_sha256")
    )
    identity, raw = _artifact_identity(
        value=value,
        path=path,
        role="UNEXPECTED_ARTIFACT",
        schema=value["schema_version"],
        hash_key="artifact_sha256",
    )
    event1_extra["artifacts_by_path"][path] = value
    event1_extra["supporting_set"][
        "supporting_artifact_paths"
    ].append(path)
    event1_extra["supporting_set"][
        "supporting_artifact_paths"
    ].sort()
    event1_extra["supporting_set"]["supporting_artifacts"].append(
        identity
    )
    event1_extra["supporting_set"]["supporting_artifacts"].sort(
        key=lambda row: row["path"]
    )
    event1_extra["supporting_set"]["canonical_bytes_by_path"][
        path
    ] = raw
    event1_extra["supporting_set"][
        "expected_git_blob_sha1_by_path"
    ][path] = _git_blob_sha1(raw)
    event1_extra["supporting_set"][
        "expected_raw_sha256_by_path"
    ][path] = hashlib.sha256(raw).hexdigest()
    event1_extra["supporting_set"][
        "expected_logical_artifact_sha256_by_path"
    ][path] = value["artifact_sha256"]
    event1_extra["supporting_set"]["supporting_artifact_count"] = 2
    event1_cases.append(event1_extra)

    for case in event1_cases:
        _assert_publication_exact(
            publisher,
            verifier,
            "supporting",
            case,
            _PUBLICATION_EXPECTATIONS["P03"],
        )
        with pytest.raises(
            ValueError,
            match="^PUBLICATION_BUNDLE_INVALID$",
        ):
            publisher.build_recovery_epoch001_event1_atomic_publication_bundle(
                event=case["event"],
                supporting_set=case["supporting_set"],
                base_snapshot=case["base_snapshot"],
            )

    cases: list[dict[str, Any]] = []

    missing = _event2_case()
    path = missing["supporting_set"]["supporting_artifact_paths"].pop()
    missing["supporting_set"]["supporting_artifacts"].pop()
    for key in (
        "canonical_bytes_by_path",
        "expected_git_blob_sha1_by_path",
        "expected_raw_sha256_by_path",
        "expected_logical_artifact_sha256_by_path",
    ):
        missing["supporting_set"][key].pop(path)
    missing["supporting_set"]["supporting_artifact_count"] = 13
    missing["artifacts_by_path"].pop(path)
    cases.append(missing)

    extra = _event2_case()
    path = f"{_PREFIX}UnexpectedArtifact.json"
    value: dict[str, Any] = {
        "schema_version": "cocolon.test.unexpected.v1",
        "body_free": True,
        "artifact_sha256": "",
    }
    value["artifact_sha256"] = artifact_sha256(
        _material(value, "artifact_sha256")
    )
    identity, raw = _artifact_identity(
        value=value,
        path=path,
        role="UNEXPECTED_ARTIFACT",
        schema=value["schema_version"],
        hash_key="artifact_sha256",
    )
    extra["artifacts_by_path"][path] = value
    extra["supporting_set"]["supporting_artifact_paths"].append(path)
    extra["supporting_set"]["supporting_artifact_paths"].sort()
    extra["supporting_set"]["supporting_artifacts"].append(identity)
    extra["supporting_set"]["supporting_artifacts"].sort(
        key=lambda row: row["path"]
    )
    extra["supporting_set"]["canonical_bytes_by_path"][path] = raw
    extra["supporting_set"]["expected_git_blob_sha1_by_path"][
        path
    ] = _git_blob_sha1(raw)
    extra["supporting_set"]["expected_raw_sha256_by_path"][
        path
    ] = hashlib.sha256(raw).hexdigest()
    extra["supporting_set"][
        "expected_logical_artifact_sha256_by_path"
    ][path] = value["artifact_sha256"]
    extra["supporting_set"]["supporting_artifact_count"] = 15
    cases.append(extra)

    duplicate = _event2_case()
    duplicate["supporting_set"]["supporting_artifacts"].append(
        deepcopy(
            duplicate["supporting_set"]["supporting_artifacts"][0]
        )
    )
    duplicate["supporting_set"]["supporting_artifact_paths"].append(
        duplicate["supporting_set"]["supporting_artifact_paths"][0]
    )
    duplicate["supporting_set"]["supporting_artifact_count"] = 15
    cases.append(duplicate)

    reordered = _event2_case()
    reordered["supporting_set"]["supporting_artifacts"].reverse()
    reordered["supporting_set"]["supporting_artifact_paths"].reverse()
    cases.append(reordered)

    for case in cases:
        _assert_publication_exact(
            publisher,
            verifier,
            "supporting",
            case,
            _PUBLICATION_EXPECTATIONS["P03"],
        )
        with pytest.raises(
            ValueError,
            match="^PUBLICATION_BUNDLE_INVALID$",
        ):
            publisher.build_recovery_epoch001_event2_atomic_publication_bundle(
                event=case["event"],
                supporting_set=case["supporting_set"],
                base_snapshot=case["base_snapshot"],
            )

    event1_event_cases: list[dict[str, Any]] = []
    event1_missing_event = _event1_case()
    event1_missing_event["event"]["publication"][
        "supporting_artifacts"
    ].clear()
    event1_event_cases.append(event1_missing_event)

    event1_extra_event = _event1_case()
    row = deepcopy(
        event1_extra_event["event"]["publication"][
            "supporting_artifacts"
        ][0]
    )
    row["path"] = f"{_PREFIX}UnexpectedEvent1PublicationArtifact.json"
    event1_extra_event["event"]["publication"][
        "supporting_artifacts"
    ].append(row)
    event1_event_cases.append(event1_extra_event)

    for case in event1_event_cases:
        _rehash_event(case)
        case["bundle"] = _bundle(
            event=case["event"],
            artifacts_by_path=case["artifacts_by_path"],
            base_commit=case["bundle"]["base_commit_sha1"],
            base_tree=case["bundle"]["base_tree_sha1"],
        )
        _assert_publication_exact(
            publisher,
            verifier,
            "candidate",
            case,
            _PUBLICATION_EXPECTATIONS["P03"],
        )

    event_cases: list[dict[str, Any]] = []
    missing_event = _event2_case()
    missing_event["event"]["publication"]["supporting_artifacts"].pop()
    event_cases.append(missing_event)

    extra_event = _event2_case()
    row = deepcopy(
        extra_event["event"]["publication"]["supporting_artifacts"][0]
    )
    row["path"] = f"{_PREFIX}UnexpectedEventSupportingArtifact.json"
    extra_event["event"]["publication"]["supporting_artifacts"].append(row)
    event_cases.append(extra_event)

    duplicate_event = _event2_case()
    duplicate_event["event"]["publication"][
        "supporting_artifacts"
    ].append(
        deepcopy(
            duplicate_event["event"]["publication"][
                "supporting_artifacts"
            ][0]
        )
    )
    event_cases.append(duplicate_event)

    reordered_event = _event2_case()
    reordered_event["event"]["publication"][
        "supporting_artifacts"
    ].reverse()
    event_cases.append(reordered_event)

    for case in event_cases:
        _rehash_event(case)
        case["bundle"] = _bundle(
            event=case["event"],
            artifacts_by_path=case["artifacts_by_path"],
            base_commit=case["bundle"]["base_commit_sha1"],
            base_tree=case["bundle"]["base_tree_sha1"],
        )
        _assert_publication_exact(
            publisher,
            verifier,
            "candidate",
            case,
            _PUBLICATION_EXPECTATIONS["P03"],
        )


def test_p04_sequential_writes_and_partial_visibility_never_publish() -> None:
    publisher, verifier = _publication_apis_or_red()

    sequential = _event2_case()
    sequential["transaction"]["write_mode"] = "SEQUENTIAL_CONTENTS_API"
    _assert_publication_exact(
        publisher,
        verifier,
        "ref",
        sequential,
        "PUBLICATION_REF_UPDATE_FAILED_STOP",
    )

    for visible_count in range(1, 15):
        partial = _event2_case()
        base_tree = partial["bundle"]["base_tree_sha1"]
        entries = deepcopy(
            partial["base_snapshot"]["trees"][base_tree]
        )
        visible_paths = partial["bundle"]["changed_paths"][:visible_count]
        entries.update(
            {
                path: partial["bundle"][
                    "expected_git_blob_sha1_by_path"
                ][path]
                for path in visible_paths
            }
        )
        partial_tree = _fake_tree_id(entries)
        target_commit = partial["transaction"]["target_commit_sha1"]
        partial["published_snapshot"]["trees"][partial_tree] = entries
        partial["published_snapshot"]["commits"][target_commit][
            "tree_sha1"
        ] = partial_tree
        partial["published_snapshot"]["changed_paths_by_commit"][
            target_commit
        ] = visible_paths
        _assert_publication_exact(
            publisher,
            verifier,
            "published",
            partial,
            "PUBLICATION_POSTVERIFY_CONFLICT_STOP",
        )


def test_p05_head_drift_before_ref_update_is_cas_stop() -> None:
    publisher, verifier = _publication_apis_or_red()
    head_drift = _event2_case()
    sibling = "5" * 40
    base = head_drift["bundle"]["base_commit_sha1"]
    base_tree = head_drift["bundle"]["base_tree_sha1"]
    head_drift["base_snapshot"]["commits"][sibling] = {
        "parent_commit_sha1s": [base],
        "tree_sha1": base_tree,
    }
    head_drift["base_snapshot"]["head_commit_sha1"] = sibling
    _assert_publication_exact(
        publisher,
        verifier,
        "ref",
        head_drift,
        _PUBLICATION_EXPECTATIONS["P05"],
    )

    stale_tree = _event2_case()
    actual_tree = stale_tree["bundle"]["base_tree_sha1"]
    entries = deepcopy(stale_tree["base_snapshot"]["trees"][actual_tree])
    unrelated_path = f"{_PREFIX}UnrelatedSibling.json"
    entries[unrelated_path] = "5" * 40
    stale_tree_id = _fake_tree_id(entries)
    stale_tree["base_snapshot"]["trees"][stale_tree_id] = entries
    stale_tree["base_snapshot"]["blobs"]["5" * 40] = b"unrelated\n"
    stale_tree["bundle"]["base_tree_sha1"] = stale_tree_id
    _assert_publication_exact(
        publisher,
        verifier,
        "preflight",
        stale_tree,
        _PUBLICATION_EXPECTATIONS["P05"],
    )


def test_p06_ref_update_requires_lease_direct_child_and_single_parent(
) -> None:
    publisher, verifier = _publication_apis_or_red()
    cases: list[dict[str, Any]] = []

    no_lease_capability = _event2_case()
    no_lease_capability["transport_capabilities"] = {
        "base_tree_read": True,
        "expected_old_sha_lease": False,
        "single_ref_update": True,
    }
    no_base_tree_capability = _event2_case()
    no_base_tree_capability["transport_capabilities"] = {
        "base_tree_read": False,
        "expected_old_sha_lease": True,
        "single_ref_update": True,
    }
    no_single_ref_capability = _event2_case()
    no_single_ref_capability["transport_capabilities"] = {
        "base_tree_read": True,
        "expected_old_sha_lease": True,
        "single_ref_update": False,
    }
    for case in (
        no_lease_capability,
        no_base_tree_capability,
        no_single_ref_capability,
    ):
        _assert_publication_exact(
            publisher,
            verifier,
            "preflight",
            case,
            _PUBLICATION_EXPECTATIONS["P06"],
        )

    wrong_parent = _event2_case()
    wrong_parent["transaction"]["parent_commit_sha1s"] = ["5" * 40]
    target = wrong_parent["transaction"]["target_commit_sha1"]
    wrong_parent["candidate_snapshot"]["commits"]["5" * 40] = {
        "parent_commit_sha1s": ["0" * 40],
        "tree_sha1": wrong_parent["bundle"]["base_tree_sha1"],
    }
    wrong_parent["candidate_snapshot"]["commits"][target][
        "parent_commit_sha1s"
    ] = ["5" * 40]
    cases.append(wrong_parent)

    merge_commit = _event2_case()
    merge_commit["transaction"]["parent_commit_sha1s"] = [
        merge_commit["bundle"]["base_commit_sha1"],
        "5" * 40,
    ]
    target = merge_commit["transaction"]["target_commit_sha1"]
    merge_commit["candidate_snapshot"]["commits"]["5" * 40] = {
        "parent_commit_sha1s": ["0" * 40],
        "tree_sha1": merge_commit["bundle"]["base_tree_sha1"],
    }
    merge_commit["candidate_snapshot"]["commits"][target][
        "parent_commit_sha1s"
    ] = deepcopy(merge_commit["transaction"]["parent_commit_sha1s"])
    cases.append(merge_commit)

    lease_preimage_drift = _event2_case()
    lease_preimage_drift["transaction"]["expected_old_sha"] = "5" * 40
    cases.append(lease_preimage_drift)

    unleased = _event2_case()
    unleased["transaction"]["write_mode"] = "UNLEASED_FORCE_REF_UPDATE"
    cases.append(unleased)

    for case in cases:
        _assert_publication_exact(
            publisher,
            verifier,
            "ref",
            case,
            _PUBLICATION_EXPECTATIONS["P06"],
        )

    lease_rejected = _event2_case()
    competing_head = "5" * 40
    base = lease_rejected["bundle"]["base_commit_sha1"]
    base_tree = lease_rejected["bundle"]["base_tree_sha1"]
    lease_rejected["published_snapshot"] = deepcopy(
        lease_rejected["candidate_snapshot"]
    )
    lease_rejected["published_snapshot"]["commits"][competing_head] = {
        "parent_commit_sha1s": [base],
        "tree_sha1": base_tree,
    }
    lease_rejected["published_snapshot"]["changed_paths_by_commit"][
        competing_head
    ] = []
    lease_rejected["published_snapshot"][
        "head_commit_sha1"
    ] = competing_head
    lease_rejected["ref_update_observation"][
        "server_result"
    ] = "EXPECTED_OLD_SHA_MISMATCH"
    lease_rejected["ref_update_observation"][
        "observed_head_before"
    ] = competing_head
    lease_rejected["ref_update_observation"][
        "observed_head_after"
    ] = competing_head
    _assert_publication_exact(
        publisher,
        verifier,
        "published",
        lease_rejected,
        _PUBLICATION_EXPECTATIONS["P06"],
    )


def test_p07_orphan_objects_are_not_published_state() -> None:
    publisher, verifier = _publication_apis_or_red()
    case = _event2_case()
    case["published_snapshot"] = deepcopy(case["candidate_snapshot"])
    _assert_publication_exact(
        publisher,
        verifier,
        "published",
        case,
        _PUBLICATION_EXPECTATIONS["P07"],
    )


def test_p08_existing_target_path_is_immutable_conflict() -> None:
    publisher, verifier = _publication_apis_or_red()
    for existing_blob in (
        None,
        "5" * 40,
    ):
        case = _event1_case()
        path = _SOURCE_RECEIPT_PATH
        blob = (
            case["bundle"]["expected_git_blob_sha1_by_path"][path]
            if existing_blob is None
            else existing_blob
        )
        old_tree = case["bundle"]["base_tree_sha1"]
        entries = deepcopy(case["base_snapshot"]["trees"][old_tree])
        entries[path] = blob
        new_tree = _fake_tree_id(entries)
        case["base_snapshot"]["trees"][new_tree] = entries
        case["base_snapshot"]["commits"][
            case["bundle"]["base_commit_sha1"]
        ]["tree_sha1"] = new_tree
        case["bundle"]["base_tree_sha1"] = new_tree
        if existing_blob is not None:
            case["base_snapshot"]["blobs"][existing_blob] = b"occupied\n"
        _assert_publication_exact(
            publisher,
            verifier,
            "preflight",
            case,
            _PUBLICATION_EXPECTATIONS["P08"],
        )


def test_p09_postfetch_tree_blob_bytes_and_hashes_are_exact() -> None:
    publisher, verifier = _publication_apis_or_red()
    cases: list[dict[str, Any]] = []

    wrong_tree = _event2_case()
    target = wrong_tree["transaction"]["target_commit_sha1"]
    wrong_tree["published_snapshot"]["commits"][target][
        "tree_sha1"
    ] = "5" * 40
    wrong_tree["published_snapshot"]["trees"]["5" * 40] = {}
    cases.append(wrong_tree)

    missing_path = _event2_case()
    target = missing_path["transaction"]["target_commit_sha1"]
    tree = missing_path["transaction"]["target_tree_sha1"]
    entries = deepcopy(missing_path["published_snapshot"]["trees"][tree])
    entries.pop(_STEP_PATHS[0])
    changed_tree = _fake_tree_id(entries)
    missing_path["published_snapshot"]["trees"][changed_tree] = entries
    missing_path["published_snapshot"]["commits"][target][
        "tree_sha1"
    ] = changed_tree
    cases.append(missing_path)

    wrong_blob = _event2_case()
    target = wrong_blob["transaction"]["target_commit_sha1"]
    tree = wrong_blob["transaction"]["target_tree_sha1"]
    entries = deepcopy(wrong_blob["published_snapshot"]["trees"][tree])
    entries[_STEP_PATHS[0]] = "5" * 40
    changed_tree = _fake_tree_id(entries)
    wrong_blob["published_snapshot"]["trees"][changed_tree] = entries
    wrong_blob["published_snapshot"]["commits"][target][
        "tree_sha1"
    ] = changed_tree
    wrong_blob["published_snapshot"]["blobs"]["5" * 40] = b"wrong\n"
    cases.append(wrong_blob)

    wrong_bytes = _event2_case()
    blob = wrong_bytes["bundle"]["expected_git_blob_sha1_by_path"][
        _STEP_PATHS[0]
    ]
    wrong_bytes["published_snapshot"]["blobs"][blob] = b"wrong\n"
    cases.append(wrong_bytes)

    wrong_logical_hash = _event2_case()
    path = _STEP_PATHS[0]
    value = deepcopy(wrong_logical_hash["artifacts_by_path"][path])
    value["receipt_sha256"] = "5" * 64
    raw = _published_bytes(value)
    blob = _git_blob_sha1(raw)
    target = wrong_logical_hash["transaction"]["target_commit_sha1"]
    tree = wrong_logical_hash["transaction"]["target_tree_sha1"]
    entries = deepcopy(
        wrong_logical_hash["published_snapshot"]["trees"][tree]
    )
    entries[path] = blob
    changed_tree = _fake_tree_id(entries)
    wrong_logical_hash["published_snapshot"]["trees"][
        changed_tree
    ] = entries
    wrong_logical_hash["published_snapshot"]["commits"][target][
        "tree_sha1"
    ] = changed_tree
    wrong_logical_hash["published_snapshot"]["blobs"][blob] = raw
    cases.append(wrong_logical_hash)

    wrong_changed_set = _event2_case()
    target = wrong_changed_set["transaction"]["target_commit_sha1"]
    wrong_changed_set["published_snapshot"]["changed_paths_by_commit"][
        target
    ] = wrong_changed_set["bundle"]["changed_paths"][:-1]
    cases.append(wrong_changed_set)

    sibling_removed = _event2_case()
    target = sibling_removed["transaction"]["target_commit_sha1"]
    tree = sibling_removed["transaction"]["target_tree_sha1"]
    entries = deepcopy(
        sibling_removed["published_snapshot"]["trees"][tree]
    )
    assert _P0_DOCUMENT_PATH not in sibling_removed["bundle"][
        "changed_paths"
    ]
    entries.pop(_P0_DOCUMENT_PATH)
    changed_tree = _fake_tree_id(entries)
    sibling_removed["published_snapshot"]["trees"][
        changed_tree
    ] = entries
    sibling_removed["published_snapshot"]["commits"][target][
        "tree_sha1"
    ] = changed_tree
    sibling_removed["transaction"]["target_tree_sha1"] = changed_tree
    sibling_removed["candidate_snapshot"]["trees"][
        changed_tree
    ] = deepcopy(entries)
    sibling_removed["candidate_snapshot"]["commits"][target][
        "tree_sha1"
    ] = changed_tree
    cases.append(sibling_removed)

    parent_drift = _event2_case()
    target = parent_drift["transaction"]["target_commit_sha1"]
    parent_drift["published_snapshot"]["commits"][target][
        "parent_commit_sha1s"
    ] = [_EVENT1_COMMIT]
    cases.append(parent_drift)

    for case in cases:
        _assert_publication_exact(
            publisher,
            verifier,
            "published",
            case,
            _PUBLICATION_EXPECTATIONS["P09"],
        )


def test_p10_staged_v1_chain_cannot_be_relabelled_as_published_v2() -> None:
    publisher, verifier = _publication_apis_or_red()
    case = _event2_case()
    case["artifacts_by_path"][_ALL11_PATH][
        "publication_state"
    ] = "STAGED_NOT_PUBLISHED"
    _rebuild_event2_case(case)
    _assert_publication_exact(
        publisher,
        verifier,
        "candidate",
        case,
        _PUBLICATION_EXPECTATIONS["P10"],
    )
