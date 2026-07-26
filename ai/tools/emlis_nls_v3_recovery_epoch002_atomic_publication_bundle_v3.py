#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Side-effect-free publication plans for Recovery Epoch 002.

The owner prepares and validates one-new-path/one-parent publication
transactions.  Git transport is deliberately outside this module: a caller
must publish the prepared bytes through an explicit port and then supply
fresh post-fetch observations for validation.
"""

from copy import deepcopy
import hashlib
from pathlib import PurePosixPath
import re
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch002_sequence_ledger_v3 import (
    validate_recovery_epoch002_event1_artifact,
    validate_recovery_epoch002_reservation_artifact,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight import (
    validate_recovery_epoch002_operational_readiness_bindings,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3 import (
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS,
    validate_recovery_epoch002_operational_terminal_result,
    validate_recovery_epoch002_unknown_disposition,
)


RECOVERY_EPOCH002_PUBLICATION_REPOSITORY = "MassyuRed/Cocolon"
RECOVERY_EPOCH002_PUBLICATION_REF = "refs/heads/main"
RECOVERY_EPOCH002_PUBLICATION_ROLES = frozenset(
    {
        "SOURCE_BASELINE_EVENT",
        "BOOTSTRAP_READINESS",
        "FORMAL_TEST_RUN_RESERVATION",
        "FORMAL_WORKER_TERMINAL_RESULT",
        "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
        "READY_UNUSED_AUTHORITY_STOP",
    }
)
RECOVERY_EPOCH002_PUBLICATION_CANDIDATE_KEYS = frozenset(
    {
        "artifact_role",
        "repository_full_name",
        "source_ref",
        "path",
        "path_preexisted",
        "expected_old_sha1",
        "expected_changed_paths",
        "artifact",
        "canonical_raw_sha256",
        "candidate_git_blob_sha1",
        "logical_artifact_sha256",
        "body_free",
        "publication_candidate_sha256",
    }
)
RECOVERY_EPOCH002_PUBLICATION_RESULT_KEYS = frozenset(
    {
        "artifact_role",
        "repository_full_name",
        "source_ref",
        "path",
        "path_preexisted",
        "expected_old_sha1",
        "observed_old_sha1",
        "publication_commit_sha1",
        "parent_commit_sha1s",
        "changed_paths",
        "expected_changed_paths",
        "candidate_git_blob_sha1",
        "postfetch_git_blob_sha1",
        "postfetch_commit_sha1",
        "postfetch_succeeded",
        "postfetch_matches_candidate",
        "body_free",
        "publication_result_sha256",
    }
)
RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS = frozenset(
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
RECOVERY_EPOCH002_READY_UNUSED_AUTHORITY_STOP_KEYS = frozenset(
    {
        "schema_version",
        "readiness_artifact",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "preflight_id",
        "stop_code",
        "automatic_progression",
        "body_free",
        "ready_unused_authority_stop_sha256",
    }
)

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DOCUMENT_ROOT = PurePosixPath("EmlisAIの実装済み資料/documents")
_ROLE_LOGICAL_HASH_KEYS = {
    "SOURCE_BASELINE_EVENT": "event_sha256",
    "BOOTSTRAP_READINESS": "bootstrap_readiness_receipt_sha256",
    "FORMAL_TEST_RUN_RESERVATION": "formal_test_run_reservation_sha256",
    "FORMAL_WORKER_TERMINAL_RESULT": "formal_worker_result_sha256",
    "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION": (
        "attempt_consumption_unknown_disposition_sha256"
    ),
    "READY_UNUSED_AUTHORITY_STOP": "ready_unused_authority_stop_sha256",
}
_ROLE_SCHEMAS = {
    "SOURCE_BASELINE_EVENT": (
        "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v1"
    ),
    "BOOTSTRAP_READINESS": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_readiness.v1"
    ),
    "FORMAL_TEST_RUN_RESERVATION": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_test_run_reservation.v1"
    ),
    "FORMAL_WORKER_TERMINAL_RESULT": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_terminal_result.v1"
    ),
    "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "attempt_consumption_unknown_disposition.v1"
    ),
    "READY_UNUSED_AUTHORITY_STOP": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "ready_unused_authority_stop.v1"
    ),
}
def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(
        header + payload,
        usedforsecurity=False,
    ).hexdigest()


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        if any(
            key in RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS
            for key in value
        ):
            return True
        return any(_contains_forbidden_key(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _artifact_logical_hash(
    artifact_role: str,
    artifact: Mapping[str, Any],
) -> Any:
    key = _ROLE_LOGICAL_HASH_KEYS.get(artifact_role)
    return None if key is None else artifact.get(key)


def _external_readiness_identity_valid(identity: Any) -> bool:
    return (
        type(identity) is dict
        and set(identity) == RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
        and identity.get("artifact_role") == "BOOTSTRAP_READINESS"
        and identity.get("schema_version")
        == _ROLE_SCHEMAS["BOOTSTRAP_READINESS"]
        and identity.get("repository_full_name")
        == RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        and _new_document_path_valid(identity.get("path"))
        and _SHA1_RE.fullmatch(str(identity.get("git_blob_sha1", "")))
        is not None
        and _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is not None
        and _SHA256_RE.fullmatch(str(identity.get("raw_sha256", "")))
        is not None
        and _SHA256_RE.fullmatch(
            str(identity.get("logical_artifact_sha256", ""))
        )
        is not None
        and identity.get("body_free") is True
        and identity.get("identity_sha256")
        == _hash_without(identity, "identity_sha256")
    )


def validate_recovery_epoch002_ready_unused_authority_stop(
    artifact: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the one-use readiness disposition when no reservation exists."""

    if (
        type(artifact) is not dict
        or set(artifact)
        != RECOVERY_EPOCH002_READY_UNUSED_AUTHORITY_STOP_KEYS
        or artifact.get("schema_version")
        != _ROLE_SCHEMAS["READY_UNUSED_AUTHORITY_STOP"]
        or not _external_readiness_identity_valid(
            artifact.get("readiness_artifact")
        )
        or not isinstance(artifact.get("candidate_version_id"), str)
        or not artifact.get("candidate_version_id")
        or artifact.get("candidate_version_id") == "nls_v3_rc_0034"
        or artifact.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or artifact.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or _SHA256_RE.fullmatch(str(artifact.get("preflight_id", "")))
        is None
        or artifact.get("stop_code") != "READY_UNUSED_AUTHORITY_STOP"
        or artifact.get("automatic_progression") is not False
        or artifact.get("body_free") is not True
        or artifact.get("ready_unused_authority_stop_sha256")
        != _hash_without(
            artifact,
            "ready_unused_authority_stop_sha256",
        )
    ):
        return ("READY_UNUSED_AUTHORITY_STOP_INVALID",)
    return ()


def _role_artifact_issues(
    artifact_role: str,
    artifact: Mapping[str, Any],
) -> tuple[str, ...]:
    if artifact_role == "SOURCE_BASELINE_EVENT":
        return validate_recovery_epoch002_event1_artifact(artifact)
    if artifact_role == "BOOTSTRAP_READINESS":
        manifest = artifact.get("bootstrap_closure")
        return validate_recovery_epoch002_operational_readiness_bindings(
            artifact,
            manifest,
        )
    if artifact_role == "FORMAL_TEST_RUN_RESERVATION":
        return validate_recovery_epoch002_reservation_artifact(artifact)
    if artifact_role == "FORMAL_WORKER_TERMINAL_RESULT":
        return validate_recovery_epoch002_operational_terminal_result(
            artifact
        )
    if artifact_role == "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION":
        return validate_recovery_epoch002_unknown_disposition(artifact)
    if artifact_role == "READY_UNUSED_AUTHORITY_STOP":
        return validate_recovery_epoch002_ready_unused_authority_stop(
            artifact
        )
    return ("PUBLICATION_ARTIFACT_ROLE_INVALID",)


def _new_document_path_valid(path: Any) -> bool:
    if not isinstance(path, str) or not path:
        return False
    parsed = PurePosixPath(path)
    return (
        not parsed.is_absolute()
        and ".." not in parsed.parts
        and parsed.as_posix() == path
        and parsed.parent == _DOCUMENT_ROOT
        and parsed.suffix == ".json"
    )


def build_recovery_epoch002_publication_candidate(
    *,
    artifact_role: str,
    source_ref: str,
    path: str,
    expected_old_sha1: str,
    artifact: Mapping[str, Any],
    logical_artifact_sha256: str,
) -> dict[str, Any]:
    """Build an inert exact-one-path publication candidate."""

    if artifact_role not in RECOVERY_EPOCH002_PUBLICATION_ROLES:
        raise ValueError("PUBLICATION_ARTIFACT_ROLE_INVALID")
    if source_ref != RECOVERY_EPOCH002_PUBLICATION_REF:
        raise ValueError("PUBLICATION_REF_INVALID")
    if not _new_document_path_valid(path):
        raise ValueError("PUBLICATION_PATH_INVALID")
    if _SHA1_RE.fullmatch(expected_old_sha1) is None:
        raise ValueError("PUBLICATION_BASE_INVALID")
    if type(artifact) is not dict or artifact.get("body_free") is not True:
        raise ValueError("PUBLICATION_ARTIFACT_INVALID")
    if (
        _contains_forbidden_key(artifact)
        or artifact.get("schema_version") != _ROLE_SCHEMAS[artifact_role]
        or _role_artifact_issues(artifact_role, artifact)
        or _SHA256_RE.fullmatch(logical_artifact_sha256) is None
        or _artifact_logical_hash(artifact_role, artifact)
        != logical_artifact_sha256
        or _hash_without(
            artifact,
            _ROLE_LOGICAL_HASH_KEYS[artifact_role],
        )
        != logical_artifact_sha256
    ):
        raise ValueError("PUBLICATION_ARTIFACT_INVALID")
    payload = _canonical_json_bytes(artifact)
    candidate: dict[str, Any] = {
        "artifact_role": artifact_role,
        "repository_full_name": RECOVERY_EPOCH002_PUBLICATION_REPOSITORY,
        "source_ref": source_ref,
        "path": path,
        "path_preexisted": False,
        "expected_old_sha1": expected_old_sha1,
        "expected_changed_paths": [path],
        "artifact": deepcopy(dict(artifact)),
        "canonical_raw_sha256": hashlib.sha256(payload).hexdigest(),
        "candidate_git_blob_sha1": _git_blob_sha1(payload),
        "logical_artifact_sha256": logical_artifact_sha256,
        "body_free": True,
        "publication_candidate_sha256": "",
    }
    candidate["publication_candidate_sha256"] = _hash_without(
        candidate,
        "publication_candidate_sha256",
    )
    return candidate


def validate_recovery_epoch002_publication_candidate(
    candidate: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate a candidate before any transport is invoked."""

    if type(candidate) is not dict:
        return ("PUBLICATION_CANDIDATE_INVALID",)
    if set(candidate) != RECOVERY_EPOCH002_PUBLICATION_CANDIDATE_KEYS:
        return ("PUBLICATION_CANDIDATE_INVALID",)
    artifact = candidate.get("artifact")
    if (
        candidate.get("artifact_role")
        not in RECOVERY_EPOCH002_PUBLICATION_ROLES
        or candidate.get("repository_full_name")
        != RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        or candidate.get("source_ref") != RECOVERY_EPOCH002_PUBLICATION_REF
        or not _new_document_path_valid(candidate.get("path"))
        or candidate.get("path_preexisted") is not False
        or candidate.get("expected_changed_paths")
        != [candidate.get("path")]
        or _SHA1_RE.fullmatch(
            str(candidate.get("expected_old_sha1", ""))
        )
        is None
        or type(artifact) is not dict
        or artifact.get("body_free") is not True
        or _contains_forbidden_key(artifact)
        or artifact.get("schema_version")
        != _ROLE_SCHEMAS.get(str(candidate.get("artifact_role", "")))
        or _artifact_logical_hash(
            str(candidate.get("artifact_role", "")),
            artifact,
        )
        != candidate.get("logical_artifact_sha256")
        or _hash_without(
            artifact,
            _ROLE_LOGICAL_HASH_KEYS[
                str(candidate.get("artifact_role", ""))
            ],
        )
        != candidate.get("logical_artifact_sha256")
        or _role_artifact_issues(
            str(candidate.get("artifact_role", "")),
            artifact,
        )
        or candidate.get("body_free") is not True
    ):
        return ("PUBLICATION_CANDIDATE_INVALID",)
    payload = _canonical_json_bytes(artifact)
    if (
        candidate.get("canonical_raw_sha256")
        != hashlib.sha256(payload).hexdigest()
        or candidate.get("candidate_git_blob_sha1")
        != _git_blob_sha1(payload)
        or candidate.get("publication_candidate_sha256")
        != _hash_without(candidate, "publication_candidate_sha256")
    ):
        return ("PUBLICATION_CANDIDATE_INVALID",)
    return ()


def validate_recovery_epoch002_publication_result(
    result: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate fresh post-fetch facts for one publication transaction."""

    if type(result) is not dict:
        return ("PUBLICATION_RESULT_INVALID",)
    if set(result) != RECOVERY_EPOCH002_PUBLICATION_RESULT_KEYS:
        return ("PUBLICATION_RESULT_INVALID",)
    expected_old = result.get("expected_old_sha1")
    path = result.get("path")
    commit = result.get("publication_commit_sha1")
    if (
        result.get("artifact_role")
        not in RECOVERY_EPOCH002_PUBLICATION_ROLES
        or result.get("repository_full_name")
        != RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        or result.get("source_ref") != RECOVERY_EPOCH002_PUBLICATION_REF
        or not _new_document_path_valid(path)
        or result.get("path_preexisted") is not False
        or _SHA1_RE.fullmatch(str(expected_old or "")) is None
        or _SHA1_RE.fullmatch(str(commit or "")) is None
        or commit == expected_old
        or _SHA1_RE.fullmatch(
            str(result.get("candidate_git_blob_sha1", ""))
        )
        is None
        or result.get("observed_old_sha1") != expected_old
        or result.get("parent_commit_sha1s") != [expected_old]
        or result.get("expected_changed_paths") != [path]
        or result.get("changed_paths") != [path]
        or result.get("postfetch_succeeded") is not True
        or result.get("postfetch_matches_candidate") is not True
        or result.get("postfetch_commit_sha1") != commit
        or result.get("postfetch_git_blob_sha1")
        != result.get("candidate_git_blob_sha1")
        or result.get("body_free") is not True
        or result.get("publication_result_sha256")
        != _hash_without(result, "publication_result_sha256")
    ):
        return ("PUBLICATION_RESULT_INVALID",)
    return ()


def build_recovery_epoch002_artifact_identity(
    *,
    candidate: Mapping[str, Any],
    publication_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Bind post-fetched Git identities to the logical artifact."""

    if validate_recovery_epoch002_publication_candidate(candidate):
        raise ValueError("PUBLICATION_CANDIDATE_INVALID")
    if validate_recovery_epoch002_publication_result(publication_result):
        raise ValueError("PUBLICATION_RESULT_INVALID")
    if any(
        candidate.get(key) != publication_result.get(key)
        for key in (
            "artifact_role",
            "repository_full_name",
            "source_ref",
            "path",
            "expected_old_sha1",
            "candidate_git_blob_sha1",
        )
    ):
        raise ValueError("PUBLICATION_CANDIDATE_RESULT_MISMATCH")
    artifact = candidate["artifact"]
    identity: dict[str, Any] = {
        "artifact_role": candidate["artifact_role"],
        "schema_version": artifact.get("schema_version"),
        "repository_full_name": candidate["repository_full_name"],
        "path": candidate["path"],
        "git_blob_sha1": candidate["candidate_git_blob_sha1"],
        "raw_sha256": candidate["canonical_raw_sha256"],
        "logical_artifact_sha256": candidate[
            "logical_artifact_sha256"
        ],
        "publication_commit_sha1": publication_result[
            "publication_commit_sha1"
        ],
        "body_free": True,
        "identity_sha256": "",
    }
    identity["identity_sha256"] = _hash_without(
        identity,
        "identity_sha256",
    )
    return identity


def validate_recovery_epoch002_artifact_identity(
    identity: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(identity) is not dict:
        return ("ARTIFACT_IDENTITY_INVALID",)
    if set(identity) != RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS:
        return ("ARTIFACT_IDENTITY_INVALID",)
    if (
        identity.get("artifact_role")
        not in RECOVERY_EPOCH002_PUBLICATION_ROLES
        or identity.get("repository_full_name")
        != RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        or not _new_document_path_valid(identity.get("path"))
        or identity.get("schema_version")
        != _ROLE_SCHEMAS.get(identity.get("artifact_role"))
        or _SHA1_RE.fullmatch(str(identity.get("git_blob_sha1", "")))
        is None
        or _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is None
        or _SHA256_RE.fullmatch(str(identity.get("raw_sha256", "")))
        is None
        or _SHA256_RE.fullmatch(
            str(identity.get("logical_artifact_sha256", ""))
        )
        is None
        or identity.get("body_free") is not True
        or identity.get("identity_sha256")
        != _hash_without(identity, "identity_sha256")
    ):
        return ("ARTIFACT_IDENTITY_INVALID",)
    return ()


__all__ = [
    "RECOVERY_EPOCH002_PUBLICATION_REPOSITORY",
    "RECOVERY_EPOCH002_PUBLICATION_REF",
    "RECOVERY_EPOCH002_PUBLICATION_ROLES",
    "RECOVERY_EPOCH002_PUBLICATION_CANDIDATE_KEYS",
    "RECOVERY_EPOCH002_PUBLICATION_RESULT_KEYS",
    "RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_READY_UNUSED_AUTHORITY_STOP_KEYS",
    "build_recovery_epoch002_publication_candidate",
    "validate_recovery_epoch002_publication_candidate",
    "validate_recovery_epoch002_publication_result",
    "build_recovery_epoch002_artifact_identity",
    "validate_recovery_epoch002_artifact_identity",
    "validate_recovery_epoch002_ready_unused_authority_stop",
]
