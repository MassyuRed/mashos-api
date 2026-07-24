#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build and verify inert Recovery Epoch 001 atomic-publication candidates.

This module deliberately has no transport or ref-write capability.  It only
constructs deterministic body-free object bundles and validates test-owned
Git object-graph observations supplied by an orchestrator.
"""

import hashlib
import json
import re
from typing import Any, Mapping


from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)


RECOVERY_EPOCH001_CANDIDATE_PUBLICATION_VALID_STATE = (
    "CANDIDATE_UNREACHABLE_VALID_NOT_PUBLISHED"
)
RECOVERY_EPOCH001_PUBLISHED_ATOMIC_VALID_STATE = "PUBLISHED_ATOMIC_VALID"

_REPOSITORY = "MassyuRed/Cocolon"
_BRANCH = "main"
_REF = "refs/heads/main"
_REF_UPDATE_MODE = "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
_WRITE_MODE = "SINGLE_TREE_SINGLE_COMMIT_EXPECTED_OLD_SHA_LEASE"
_PREFIX = "EmlisAIの実装済み資料/documents/"
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
_EVENT1_SUPPORTING_PATHS = frozenset({_SOURCE_RECEIPT_PATH})
_EVENT2_CORE_PATHS = frozenset({_ACCEPTED_PATH, *_STEP_PATHS, _ALL11_PATH})
_EVENT2_SUPPORTING_PATHS = frozenset(
    {*_EVENT2_CORE_PATHS, _MANIFEST_PATH}
)
_EVENT1_CHANGED_PATHS = frozenset(
    {*_EVENT1_SUPPORTING_PATHS, _EVENT1_PATH}
)
_EVENT2_CHANGED_PATHS = frozenset(
    {*_EVENT2_SUPPORTING_PATHS, _EVENT2_PATH}
)

_SOURCE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "source_baseline_closure_receipt.v2"
)
_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch001.sequence_event.v2"
)
_ACCEPTED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "accepted_test_run_receipt.v2"
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
_IDENTITY_KEYS = frozenset(
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
_SUPPORTING_KEYS = frozenset(
    {
        "repository_full_name",
        "branch",
        "base_commit_sha1",
        "base_tree_sha1",
        "supporting_artifact_count",
        "supporting_artifact_paths",
        "supporting_artifacts",
        "canonical_bytes_by_path",
        "expected_git_blob_sha1_by_path",
        "expected_raw_sha256_by_path",
        "expected_logical_artifact_sha256_by_path",
        "ref_update_mode",
        "body_free",
    }
)
_BUNDLE_KEYS = frozenset(
    {
        "repository_full_name",
        "branch",
        "base_commit_sha1",
        "base_tree_sha1",
        "event_path",
        "changed_path_count",
        "changed_paths",
        "canonical_bytes_by_path",
        "expected_git_blob_sha1_by_path",
        "expected_raw_sha256_by_path",
        "expected_logical_artifact_sha256_by_path",
        "ref_update_mode",
        "candidate_state",
        "body_free",
    }
)
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def _published_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _git_blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(
        prefix + raw,
        usedforsecurity=False,
    ).hexdigest()


def _decode(raw: Any) -> dict[str, Any] | None:
    if type(raw) is not bytes or not raw.endswith(b"\n"):
        return None
    try:
        value = json.loads(raw[:-1].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if type(value) is not dict or _published_bytes(value) != raw:
        return None
    return value


def _artifact_meta(path: str) -> tuple[str, str, str] | None:
    if path == _SOURCE_RECEIPT_PATH:
        return (
            "SOURCE_BASELINE_CLOSURE_RECEIPT",
            _SOURCE_RECEIPT_SCHEMA,
            "source_baseline_closure_receipt_sha256",
        )
    if path == _ACCEPTED_PATH:
        return (
            "ACCEPTED_TEST_RUN_RECEIPT",
            _ACCEPTED_SCHEMA,
            "accepted_test_run_receipt_sha256",
        )
    if path in _STEP_PATHS:
        return (
            "CURRENT_STEP_COMPLETION_RECEIPT",
            _STEP_SCHEMA,
            "receipt_sha256",
        )
    if path == _ALL11_PATH:
        return (
            "ALL11_COMPLETION_CHAIN",
            _ALL11_SCHEMA,
            "all11_completion_chain_sha256",
        )
    if path == _MANIFEST_PATH:
        return (
            "ALL11_ATOMIC_PUBLICATION_MANIFEST",
            _MANIFEST_SCHEMA,
            "atomic_publication_manifest_sha256",
        )
    return None


def _logical_sha(path: str, value: Mapping[str, Any]) -> str | None:
    if path in {_EVENT1_PATH, _EVENT2_PATH}:
        result = value.get("event_sha256")
    else:
        meta = _artifact_meta(path)
        result = value.get(meta[2]) if meta is not None else None
    return result if type(result) is str and _SHA_RE.fullmatch(result) else None


def _identity(
    *,
    path: str,
    value: Mapping[str, Any],
    raw: bytes,
) -> dict[str, Any]:
    meta = _artifact_meta(path)
    if meta is None:
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    role, schema, hash_key = meta
    return {
        "artifact_role": role,
        "schema_version": schema,
        "repository_full_name": _REPOSITORY,
        "path": path,
        "git_blob_sha1": _git_blob_sha1(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "logical_artifact_sha256": value[hash_key],
        "body_free": True,
    }


def _expected_supporting_paths(paths: frozenset[str]) -> frozenset[str] | None:
    if paths == _EVENT1_SUPPORTING_PATHS:
        return _EVENT1_SUPPORTING_PATHS
    if paths == _EVENT2_SUPPORTING_PATHS:
        return _EVENT2_SUPPORTING_PATHS
    return None


def _base_tree(
    base_snapshot: Mapping[str, Any],
) -> tuple[str, str] | None:
    head = base_snapshot.get("head_commit_sha1")
    commits = base_snapshot.get("commits")
    if (
        type(head) is not str
        or _COMMIT_RE.fullmatch(head) is None
        or type(commits) is not dict
        or type(commits.get(head)) is not dict
    ):
        return None
    tree = commits[head].get("tree_sha1")
    if (
        type(tree) is not str
        or _COMMIT_RE.fullmatch(tree) is None
        or type(base_snapshot.get("trees")) is not dict
        or type(base_snapshot["trees"].get(tree)) is not dict
    ):
        return None
    return head, tree


def _build_supporting_set(
    *,
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
    base_snapshot: Mapping[str, Any],
    expected_paths: frozenset[str],
) -> dict[str, Any]:
    if (
        type(artifacts_by_path) is not dict
        or frozenset(artifacts_by_path) != expected_paths
    ):
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    base = _base_tree(base_snapshot)
    if base is None:
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    base_commit, base_tree = base
    paths = sorted(expected_paths)
    values = {
        path: dict(artifacts_by_path[path])
        for path in paths
        if type(artifacts_by_path[path]) is dict
    }
    if set(values) != set(paths):
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    raw_by_path = {
        path: _published_bytes(values[path])
        for path in paths
    }
    identities = [
        _identity(path=path, value=values[path], raw=raw_by_path[path])
        for path in paths
    ]
    result: dict[str, Any] = {
        "repository_full_name": _REPOSITORY,
        "branch": _BRANCH,
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
            path: _logical_sha(path, values[path])
            for path in paths
        },
        "ref_update_mode": _REF_UPDATE_MODE,
        "body_free": True,
    }
    if validate_recovery_epoch001_atomic_publication_supporting_set(
        result,
        artifacts_by_path=values,
    ):
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    return result


def build_recovery_epoch001_event1_atomic_publication_supporting_set(
    *,
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
    base_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return _build_supporting_set(
        artifacts_by_path=artifacts_by_path,
        base_snapshot=base_snapshot,
        expected_paths=_EVENT1_SUPPORTING_PATHS,
    )


def build_recovery_epoch001_event2_atomic_publication_supporting_set(
    *,
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
    base_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return _build_supporting_set(
        artifacts_by_path=artifacts_by_path,
        base_snapshot=base_snapshot,
        expected_paths=_EVENT2_SUPPORTING_PATHS,
    )


def _supporting_issue(
    value: Any,
    *,
    artifacts_by_path: Mapping[str, Mapping[str, Any]] | None,
) -> str | None:
    if type(value) is not dict or set(value) != _SUPPORTING_KEYS:
        return "PUBLICATION_BUNDLE_INVALID"
    paths = value.get("supporting_artifact_paths")
    identities = value.get("supporting_artifacts")
    if (
        type(paths) is not list
        or any(type(path) is not str for path in paths)
        or paths != sorted(paths)
        or len(paths) != len(set(paths))
    ):
        return "PUBLICATION_BUNDLE_INVALID"
    expected = _expected_supporting_paths(frozenset(paths))
    if expected is None or set(paths) != set(expected):
        return "PUBLICATION_BUNDLE_INVALID"
    if (
        value.get("repository_full_name") != _REPOSITORY
        or value.get("branch") != _BRANCH
        or _COMMIT_RE.fullmatch(str(value.get("base_commit_sha1", "")))
        is None
        or _COMMIT_RE.fullmatch(str(value.get("base_tree_sha1", "")))
        is None
        or value.get("supporting_artifact_count") != len(paths)
        or value.get("ref_update_mode") != _REF_UPDATE_MODE
        or value.get("body_free") is not True
        or type(identities) is not list
        or len(identities) != len(paths)
        or identities != sorted(
            identities,
            key=lambda row: row.get("path", "")
            if type(row) is dict
            else "",
        )
    ):
        return "PUBLICATION_BUNDLE_INVALID"
    maps = [
        value.get("canonical_bytes_by_path"),
        value.get("expected_git_blob_sha1_by_path"),
        value.get("expected_raw_sha256_by_path"),
        value.get("expected_logical_artifact_sha256_by_path"),
    ]
    if any(type(item) is not dict or set(item) != set(paths) for item in maps):
        return "PUBLICATION_BUNDLE_INVALID"
    supplied = (
        dict(artifacts_by_path)
        if type(artifacts_by_path) is dict
        else None
    )
    if supplied is not None and set(supplied) != set(paths):
        return "PUBLICATION_BUNDLE_INVALID"
    for index, path in enumerate(paths):
        raw = value["canonical_bytes_by_path"][path]
        decoded = _decode(raw)
        if decoded is None:
            return "PUBLICATION_BUNDLE_INVALID"
        artifact = decoded if supplied is None else supplied.get(path)
        meta = _artifact_meta(path)
        identity = identities[index]
        if (
            type(artifact) is not dict
            or artifact != decoded
            or meta is None
            or type(identity) is not dict
            or set(identity) != _IDENTITY_KEYS
            or identity
            != _identity(path=path, value=artifact, raw=raw)
            or value["expected_git_blob_sha1_by_path"][path]
            != _git_blob_sha1(raw)
            or value["expected_raw_sha256_by_path"][path]
            != hashlib.sha256(raw).hexdigest()
            or value["expected_logical_artifact_sha256_by_path"][path]
            != _logical_sha(path, artifact)
        ):
            return "PUBLICATION_BUNDLE_INVALID"
    return None


def validate_recovery_epoch001_atomic_publication_supporting_set(
    value: Any,
    *,
    artifacts_by_path: Mapping[str, Mapping[str, Any]] | None = None,
) -> tuple[str, ...]:
    try:
        issue = _supporting_issue(
            value,
            artifacts_by_path=artifacts_by_path,
        )
        return () if issue is None else (issue,)
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("PUBLICATION_BUNDLE_INVALID",)


def _build_bundle(
    *,
    event: Mapping[str, Any],
    supporting_set: Mapping[str, Any],
    base_snapshot: Mapping[str, Any],
    expected_supporting: frozenset[str],
    expected_event_path: str,
) -> dict[str, Any]:
    if (
        type(event) is not dict
        or type(supporting_set) is not dict
        or frozenset(
            supporting_set.get("supporting_artifact_paths", ())
        )
        != expected_supporting
        or _supporting_issue(
            supporting_set,
            artifacts_by_path=None,
        )
        is not None
    ):
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    base = _base_tree(base_snapshot)
    if (
        base is None
        or base
        != (
            supporting_set.get("base_commit_sha1"),
            supporting_set.get("base_tree_sha1"),
        )
        or event.get("schema_version") != _EVENT_SCHEMA
        or event.get("publication", {}).get("event_path")
        != expected_event_path
    ):
        raise ValueError("PUBLICATION_BUNDLE_INVALID")
    values_raw = dict(supporting_set["canonical_bytes_by_path"])
    event_raw = _published_bytes(event)
    values_raw[expected_event_path] = event_raw
    paths = sorted(values_raw)
    result: dict[str, Any] = {
        "repository_full_name": _REPOSITORY,
        "branch": _BRANCH,
        "base_commit_sha1": base[0],
        "base_tree_sha1": base[1],
        "event_path": expected_event_path,
        "changed_path_count": len(paths),
        "changed_paths": paths,
        "canonical_bytes_by_path": values_raw,
        "expected_git_blob_sha1_by_path": {
            **dict(supporting_set["expected_git_blob_sha1_by_path"]),
            expected_event_path: _git_blob_sha1(event_raw),
        },
        "expected_raw_sha256_by_path": {
            **dict(supporting_set["expected_raw_sha256_by_path"]),
            expected_event_path: hashlib.sha256(event_raw).hexdigest(),
        },
        "expected_logical_artifact_sha256_by_path": {
            **dict(
                supporting_set[
                    "expected_logical_artifact_sha256_by_path"
                ]
            ),
            expected_event_path: event["event_sha256"],
        },
        "ref_update_mode": _REF_UPDATE_MODE,
        "candidate_state": (
            RECOVERY_EPOCH001_CANDIDATE_PUBLICATION_VALID_STATE
        ),
        "body_free": True,
    }
    return result


def build_recovery_epoch001_event1_atomic_publication_bundle(
    *,
    event: Mapping[str, Any],
    supporting_set: Mapping[str, Any],
    base_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return _build_bundle(
        event=event,
        supporting_set=supporting_set,
        base_snapshot=base_snapshot,
        expected_supporting=_EVENT1_SUPPORTING_PATHS,
        expected_event_path=_EVENT1_PATH,
    )


def build_recovery_epoch001_event2_atomic_publication_bundle(
    *,
    event: Mapping[str, Any],
    supporting_set: Mapping[str, Any],
    base_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    return _build_bundle(
        event=event,
        supporting_set=supporting_set,
        base_snapshot=base_snapshot,
        expected_supporting=_EVENT2_SUPPORTING_PATHS,
        expected_event_path=_EVENT2_PATH,
    )


def _candidate_issue(
    value: Any,
    *,
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
) -> str | None:
    if (
        type(value) is not dict
        or set(value) != _BUNDLE_KEYS
        or type(event) is not dict
        or type(artifacts_by_path) is not dict
    ):
        return "PUBLICATION_BUNDLE_INVALID"
    event_path = event.get("publication", {}).get("event_path")
    supporting_paths = frozenset(artifacts_by_path)
    if (
        event_path == _EVENT1_PATH
        and supporting_paths == _EVENT1_SUPPORTING_PATHS
    ):
        expected_paths = _EVENT1_CHANGED_PATHS
    elif (
        event_path == _EVENT2_PATH
        and supporting_paths == _EVENT2_SUPPORTING_PATHS
    ):
        expected_paths = _EVENT2_CHANGED_PATHS
    else:
        return "PUBLICATION_BUNDLE_INVALID"
    paths = value.get("changed_paths")
    if (
        type(paths) is not list
        or paths != sorted(paths)
        or len(paths) != len(set(paths))
        or frozenset(paths) != expected_paths
        or value.get("changed_path_count") != len(expected_paths)
        or value.get("event_path") != event_path
    ):
        return "PUBLICATION_BUNDLE_INVALID"
    publication = event.get("publication")
    expected_identities: list[dict[str, Any]] = []
    for path in sorted(supporting_paths):
        artifact = artifacts_by_path[path]
        if type(artifact) is not dict:
            return "PUBLICATION_BUNDLE_INVALID"
        raw = _published_bytes(artifact)
        try:
            expected_identities.append(
                _identity(path=path, value=artifact, raw=raw)
            )
        except (KeyError, ValueError):
            return "PUBLICATION_BUNDLE_INVALID"
    if (
        type(publication) is not dict
        or publication.get("repository_full_name") != _REPOSITORY
        or publication.get("branch") != _BRANCH
        or publication.get("base_commit_sha1")
        != value.get("base_commit_sha1")
        or publication.get("supporting_artifact_count")
        != len(expected_identities)
        or publication.get("supporting_artifacts")
        != expected_identities
        or publication.get("supporting_artifact_set_sha256")
        != artifact_sha256(expected_identities)
        or publication.get("expected_changed_path_count")
        != len(expected_paths)
        or publication.get("ref_update_mode") != _REF_UPDATE_MODE
        or publication.get("publication_state") != "PUBLISHED_ATOMIC"
    ):
        return "PUBLICATION_BUNDLE_INVALID"
    if event_path == _EVENT2_PATH:
        chain = artifacts_by_path.get(_ALL11_PATH)
        if (
            type(chain) is not dict
            or chain.get("schema_version") != _ALL11_SCHEMA
            or chain.get("publication_state") != "PUBLISHED_ATOMIC"
        ):
            return "PUBLICATION_BUNDLE_INVALID"
    values: dict[str, Mapping[str, Any]] = {
        **artifacts_by_path,
        event_path: event,
    }
    maps = (
        value.get("canonical_bytes_by_path"),
        value.get("expected_git_blob_sha1_by_path"),
        value.get("expected_raw_sha256_by_path"),
        value.get("expected_logical_artifact_sha256_by_path"),
    )
    if any(type(item) is not dict or set(item) != set(paths) for item in maps):
        return "PUBLICATION_BUNDLE_INVALID"
    for path, artifact in values.items():
        raw = _published_bytes(artifact)
        if (
            value["canonical_bytes_by_path"].get(path) != raw
            or value["expected_git_blob_sha1_by_path"].get(path)
            != _git_blob_sha1(raw)
            or value["expected_raw_sha256_by_path"].get(path)
            != hashlib.sha256(raw).hexdigest()
            or value[
                "expected_logical_artifact_sha256_by_path"
            ].get(path)
            != _logical_sha(path, artifact)
        ):
            return "PUBLICATION_BUNDLE_INVALID"
    if (
        value.get("repository_full_name") != _REPOSITORY
        or value.get("branch") != _BRANCH
        or value.get("ref_update_mode") != _REF_UPDATE_MODE
        or value.get("candidate_state")
        != RECOVERY_EPOCH001_CANDIDATE_PUBLICATION_VALID_STATE
        or value.get("body_free") is not True
    ):
        return "PUBLICATION_BUNDLE_INVALID"
    return None


def validate_recovery_epoch001_atomic_publication_candidate(
    value: Any,
    *,
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    try:
        issue = _candidate_issue(
            value,
            event=event,
            artifacts_by_path=artifacts_by_path,
        )
        return () if issue is None else (issue,)
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("PUBLICATION_BUNDLE_INVALID",)


def classify_recovery_epoch001_atomic_publication_candidate(
    value: Any,
    *,
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
) -> str:
    issues = validate_recovery_epoch001_atomic_publication_candidate(
        value,
        event=event,
        artifacts_by_path=artifacts_by_path,
    )
    return (
        RECOVERY_EPOCH001_CANDIDATE_PUBLICATION_VALID_STATE
        if not issues
        else issues[0]
    )


def _preflight_issue(
    value: Any,
    *,
    repository_snapshot: Mapping[str, Any],
    transport_capabilities: Mapping[str, Any],
) -> str | None:
    if type(value) is not dict or type(repository_snapshot) is not dict:
        return "PUBLICATION_BUNDLE_INVALID"
    if (
        type(transport_capabilities) is not dict
        or transport_capabilities
        != {
            "base_tree_read": True,
            "expected_old_sha_lease": True,
            "single_ref_update": True,
        }
    ):
        return "PUBLICATION_REF_UPDATE_FAILED_STOP"
    base = _base_tree(repository_snapshot)
    if base is None:
        return "PUBLICATION_HEAD_DRIFT_STOP"
    actual_commit, actual_tree = base
    if (
        actual_commit != value.get("base_commit_sha1")
        or actual_tree != value.get("base_tree_sha1")
    ):
        return "PUBLICATION_HEAD_DRIFT_STOP"
    entries = repository_snapshot["trees"][actual_tree]
    paths = value.get("changed_paths")
    if type(paths) is not list:
        return "PUBLICATION_BUNDLE_INVALID"
    if any(path in entries for path in paths):
        return "PUBLICATION_PATH_CONFLICT"
    return None


def validate_recovery_epoch001_atomic_publication_preflight(
    value: Any,
    *,
    repository_snapshot: Mapping[str, Any],
    transport_capabilities: Mapping[str, Any],
) -> tuple[str, ...]:
    try:
        issue = _preflight_issue(
            value,
            repository_snapshot=repository_snapshot,
            transport_capabilities=transport_capabilities,
        )
        return () if issue is None else (issue,)
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("PUBLICATION_REF_UPDATE_FAILED_STOP",)


def _ref_issue(
    value: Any,
    *,
    transaction: Mapping[str, Any],
    repository_snapshot: Mapping[str, Any],
    candidate_snapshot: Mapping[str, Any],
    transport_capabilities: Mapping[str, Any],
) -> str | None:
    preflight = _preflight_issue(
        value,
        repository_snapshot=repository_snapshot,
        transport_capabilities=transport_capabilities,
    )
    if preflight is not None:
        return preflight
    if type(transaction) is not dict or type(candidate_snapshot) is not dict:
        return "PUBLICATION_REF_UPDATE_FAILED_STOP"
    base = value.get("base_commit_sha1")
    target = transaction.get("target_commit_sha1")
    target_tree = transaction.get("target_tree_sha1")
    if (
        transaction.get("write_mode") != _WRITE_MODE
        or transaction.get("expected_old_sha") != base
        or transaction.get("parent_commit_sha1s") != [base]
        or transaction.get("body_free") is not True
        or _COMMIT_RE.fullmatch(str(target or "")) is None
        or _COMMIT_RE.fullmatch(str(target_tree or "")) is None
    ):
        return "PUBLICATION_REF_UPDATE_FAILED_STOP"
    commits = candidate_snapshot.get("commits")
    trees = candidate_snapshot.get("trees")
    changes = candidate_snapshot.get("changed_paths_by_commit")
    if (
        type(commits) is not dict
        or type(commits.get(target)) is not dict
        or commits[target].get("parent_commit_sha1s") != [base]
        or commits[target].get("tree_sha1") != target_tree
        or type(trees) is not dict
        or type(trees.get(target_tree)) is not dict
        or type(changes) is not dict
        or changes.get(target) != value.get("changed_paths")
    ):
        return "PUBLICATION_REF_UPDATE_FAILED_STOP"
    base_tree = value.get("base_tree_sha1")
    base_entries = repository_snapshot["trees"].get(base_tree)
    if type(base_entries) is not dict:
        return "PUBLICATION_REF_UPDATE_FAILED_STOP"
    expected_entries = dict(base_entries)
    expected_entries.update(value["expected_git_blob_sha1_by_path"])
    if trees[target_tree] != expected_entries:
        return "PUBLICATION_REF_UPDATE_FAILED_STOP"
    return None


def validate_recovery_epoch001_atomic_ref_update_plan(
    value: Any,
    *,
    transaction: Mapping[str, Any],
    repository_snapshot: Mapping[str, Any],
    candidate_snapshot: Mapping[str, Any],
    transport_capabilities: Mapping[str, Any],
) -> tuple[str, ...]:
    try:
        issue = _ref_issue(
            value,
            transaction=transaction,
            repository_snapshot=repository_snapshot,
            candidate_snapshot=candidate_snapshot,
            transport_capabilities=transport_capabilities,
        )
        return () if issue is None else (issue,)
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("PUBLICATION_REF_UPDATE_FAILED_STOP",)


def _result_issue(
    value: Any,
    *,
    transaction: Mapping[str, Any],
    candidate_snapshot: Mapping[str, Any],
    repository_snapshot: Mapping[str, Any],
    ref_update_observation: Mapping[str, Any],
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
) -> str | None:
    if _candidate_issue(
        value,
        event=event,
        artifacts_by_path=artifacts_by_path,
    ) is not None:
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    if (
        type(transaction) is not dict
        or type(candidate_snapshot) is not dict
        or type(repository_snapshot) is not dict
        or type(ref_update_observation) is not dict
    ):
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    base = value.get("base_commit_sha1")
    target = transaction.get("target_commit_sha1")
    target_tree = transaction.get("target_tree_sha1")
    expected_observation = {
        "ref": _REF,
        "lease_precondition": {
            "expected_old_sha": base,
            "target_commit_sha1": target,
        },
        "observed_head_before": base,
        "server_result": "EXPECTED_OLD_SHA_MATCHED_AND_UPDATED",
        "observed_head_after": target,
        "body_free": True,
    }
    if ref_update_observation != expected_observation:
        if (
            ref_update_observation.get("server_result")
            == "EXPECTED_OLD_SHA_MISMATCH"
        ):
            return "PUBLICATION_REF_UPDATE_FAILED_STOP"
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    if repository_snapshot.get("head_commit_sha1") != target:
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    commits = repository_snapshot.get("commits")
    trees = repository_snapshot.get("trees")
    blobs = repository_snapshot.get("blobs")
    changed = repository_snapshot.get("changed_paths_by_commit")
    if (
        type(commits) is not dict
        or type(commits.get(target)) is not dict
        or commits[target].get("parent_commit_sha1s") != [base]
        or commits[target].get("tree_sha1") != target_tree
        or type(trees) is not dict
        or type(trees.get(target_tree)) is not dict
        or type(blobs) is not dict
        or type(changed) is not dict
        or changed.get(target) != value.get("changed_paths")
    ):
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    candidate_commits = candidate_snapshot.get("commits")
    candidate_trees = candidate_snapshot.get("trees")
    if (
        type(candidate_commits) is not dict
        or candidate_commits.get(target) != commits[target]
        or type(candidate_trees) is not dict
        or candidate_trees.get(target_tree) != trees[target_tree]
    ):
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    base_tree = value.get("base_tree_sha1")
    base_entries = candidate_snapshot.get("trees", {}).get(base_tree)
    if type(base_entries) is not dict:
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    expected_entries = dict(base_entries)
    expected_entries.update(value["expected_git_blob_sha1_by_path"])
    if trees[target_tree] != expected_entries:
        return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    values: dict[str, Mapping[str, Any]] = {
        **artifacts_by_path,
        event["publication"]["event_path"]: event,
    }
    for path in value["changed_paths"]:
        blob = value["expected_git_blob_sha1_by_path"][path]
        raw = value["canonical_bytes_by_path"][path]
        artifact = values.get(path)
        if (
            trees[target_tree].get(path) != blob
            or blobs.get(blob) != raw
            or _git_blob_sha1(raw) != blob
            or hashlib.sha256(raw).hexdigest()
            != value["expected_raw_sha256_by_path"][path]
            or type(artifact) is not dict
            or _published_bytes(artifact) != raw
            or _logical_sha(path, artifact)
            != value[
                "expected_logical_artifact_sha256_by_path"
            ][path]
        ):
            return "PUBLICATION_POSTVERIFY_CONFLICT_STOP"
    return None


def validate_recovery_epoch001_atomic_publication_result(
    value: Any,
    *,
    transaction: Mapping[str, Any],
    candidate_snapshot: Mapping[str, Any],
    repository_snapshot: Mapping[str, Any],
    ref_update_observation: Mapping[str, Any],
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    try:
        issue = _result_issue(
            value,
            transaction=transaction,
            candidate_snapshot=candidate_snapshot,
            repository_snapshot=repository_snapshot,
            ref_update_observation=ref_update_observation,
            event=event,
            artifacts_by_path=artifacts_by_path,
        )
        return () if issue is None else (issue,)
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("PUBLICATION_POSTVERIFY_CONFLICT_STOP",)


def classify_recovery_epoch001_atomic_publication_result(
    value: Any,
    *,
    transaction: Mapping[str, Any],
    candidate_snapshot: Mapping[str, Any],
    repository_snapshot: Mapping[str, Any],
    ref_update_observation: Mapping[str, Any],
    event: Mapping[str, Any],
    artifacts_by_path: Mapping[str, Mapping[str, Any]],
) -> str:
    issues = validate_recovery_epoch001_atomic_publication_result(
        value,
        transaction=transaction,
        candidate_snapshot=candidate_snapshot,
        repository_snapshot=repository_snapshot,
        ref_update_observation=ref_update_observation,
        event=event,
        artifacts_by_path=artifacts_by_path,
    )
    return (
        RECOVERY_EPOCH001_PUBLISHED_ATOMIC_VALID_STATE
        if not issues
        else issues[0]
    )


if __name__ == "__main__":
    raise SystemExit("inert contract module; no publication transport exists")
