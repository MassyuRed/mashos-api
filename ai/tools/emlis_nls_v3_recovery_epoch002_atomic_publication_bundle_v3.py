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
    validate_recovery_epoch002_operational_admission_receipt,
    validate_recovery_epoch002_reservation_artifact,
    validate_recovery_epoch002_success_event2_state,
    validate_recovery_epoch002_successor_completion_receipt,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight import (
    validate_recovery_epoch002_operational_readiness_bindings,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3 import (
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS,
    validate_recovery_epoch002_operational_terminal_result,
    validate_recovery_epoch002_unknown_disposition,
)

_SUCCESS_FORBIDDEN_STATE_KEYS = (
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS
    | frozenset({"raw_payload", "private_body", "private_payload"})
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
        "SUCCESSOR_COMPLETION_RECEIPT",
        "P1_OPERATIONAL_ADMISSION_RECEIPT",
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
    "SUCCESSOR_COMPLETION_RECEIPT": "receipt_sha256",
    "P1_OPERATIONAL_ADMISSION_RECEIPT": "operational_admission_sha256",
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
    "SUCCESSOR_COMPLETION_RECEIPT": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "post_d2_source_baseline_eligibility_successor_completion_receipt.v1"
    ),
    "P1_OPERATIONAL_ADMISSION_RECEIPT": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "p1_operational_admission_receipt.v1"
    ),
}

RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "all11_atomic_publication_manifest.v1"
)
RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_KEYS = frozenset(
    """
    schema_version candidate_version_id logical_cycle_id recovery_epoch_id
    source_baseline_event base_commit_sha1 core_artifact_count core_artifacts
    core_artifact_set_sha256 event_supporting_artifact_count
    expected_changed_path_count event_path ref_update_mode body_free
    atomic_publication_manifest_sha256
    """.split()
)
RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS = frozenset(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 body_free
    """.split()
)
RECOVERY_EPOCH002_SUCCESS_PATHS = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_AcceptedTestRunExact134_"
    "BodyFree_Receipt_20260726.json",
    *(
        "EmlisAIの実装済み資料/documents/"
        f"NLSv3_Step11_Cycle001_RecoveryEpoch002_Step{step:02d}_"
        "CurrentStepCompletion_PROVED_BodyFree_Receipt_20260726.json"
        for step in range(11)
    ),
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_All11CompletionChain_"
    "BodyFree_Chain_20260726.json",
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_All11AtomicPublication_"
    "BodyFree_Manifest_20260726.json",
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_SequenceEvent02_"
    "Step0_10PrerequisitesProved_BodyFree_Event_20260726.json",
)
RECOVERY_EPOCH002_SUCCESS_CORE_PATHS = tuple(
    sorted(RECOVERY_EPOCH002_SUCCESS_PATHS[:13])
)
RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS = tuple(
    sorted(RECOVERY_EPOCH002_SUCCESS_PATHS[:14])
)
RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS = tuple(
    sorted(RECOVERY_EPOCH002_SUCCESS_PATHS)
)
RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorCompletion_BodyFree_Receipt_20260726.json"
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_P1OperationalAdmission_"
    "BodyFree_Receipt_20260726.json"
)

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
            key in _SUCCESS_FORBIDDEN_STATE_KEYS
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
    if artifact_role == "SUCCESSOR_COMPLETION_RECEIPT":
        return validate_recovery_epoch002_successor_completion_receipt(
            artifact
        )
    if artifact_role == "P1_OPERATIONAL_ADMISSION_RECEIPT":
        return validate_recovery_epoch002_operational_admission_receipt(
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


_SUCCESS_TERMINAL_OBSERVATION_KEYS = frozenset(
    {
        "commit_sha1",
        "tree_sha1",
        "authoritative_ref_read",
        "authoritative_tree_read",
        "paths_present",
    }
)
_SUCCESS_TRANSACTION_KEYS = frozenset(
    """
    target_tree_build_count success_commit_build_count terminal_commit_sha1
    base_tree_sha1 target_tree_sha1 parent_commit_sha1s
    requested_expected_old_sha1 observed_old_sha1
    server_side_expected_old_applied changed_paths
    target_blob_sha1_by_path ref_update_result ref_update_attempt_count
    frozen_success_commit_sha1 reconciled_success_commit_sha1
    same_frozen_success_commit_reused automatic_retry_requested
    publication_only_retry_requested publication_only_authority_present
    new_accepted_receipt_requested rebase_requested
    timestamp_rebuild_requested
    """.split()
)
_SUCCESS_EXTERNAL_IDENTITY_KEYS = RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
_SUCCESS_TRANSACTION_CAPABILITY_KEYS = frozenset(
    """
    schema_version provider_class provider_identity_sha256
    repository_full_name source_ref base_commit_sha1
    expected_changed_path_count authoritative_ref_read
    expected_old_compare_and_swap commit_parent_tree_and_recursive_read
    full_changed_and_unchanged_postfetch_verification challenge_id
    operational_admission_identity_sha256 observed_at_utc
    transaction_capability_sha256
    """.split()
)
_SUCCESS_POSTFETCH_KEYS = frozenset(
    {
        "head_commit_sha1",
        "parent_commit_sha1s",
        "target_tree_sha1",
        "authoritative_ref_read",
        "authoritative_head_read",
        "authoritative_parent_read",
        "authoritative_tree_read",
        "authoritative_recursive_tree_read",
        "changed_paths",
        "changed_path_proof_complete",
        "artifact_raw_sha256_by_path",
        "artifact_git_blob_sha1_by_path",
        "artifact_logical_sha256_by_path",
        "artifact_schema_by_path",
        "artifact_body_free_by_path",
        "publication_external_identities",
        "unchanged_path_observation",
        "unchanged_path_mismatches",
        "owner_issue_codes",
        "independent_issue_codes",
        "state",
    }
)
_SUCCESS_UNCHANGED_KEYS = frozenset(
    {"scope", "mode_type_sha_complete", "mismatches", "observation_sha256"}
)
_SUCCESS_PUBLICATION_STATE_KEYS = frozenset(
    {
        "terminal_commit_observation",
        "artifacts_by_path",
        "candidate_identities_by_path",
        "atomic_publication_manifest",
        "event2",
        "publication_transaction",
        "postfetch_observation",
    }
)
_SUCCESS_SINGLE_PUBLICATION_STATE_KEYS = frozenset(
    {"supported_roles", "additive_role_paths", "exact1_transactions"}
)
_SUCCESS_SINGLE_TRANSACTION_KEYS = frozenset(
    """
    artifact_role path expected_changed_paths parent_commit_sha1s
    expected_old_sha1 requested_expected_old_sha1 observed_old_sha1
    head_commit_sha1 target_absent_at_base unchanged_path_mismatches
    owner_issue_codes independent_issue_codes postfetch_state publication
    """.split()
)
_SUCCESS_EXACT1_PUBLICATION_KEYS = frozenset(
    """
    artifact identity changed_paths parent_commit_sha1s expected_old_sha1
    observed_old_sha1 postfetch_evidence postfetch_state
    """.split()
)
_SUCCESS_EXACT1_POSTFETCH_KEYS = frozenset(
    """
    repository_full_name verification_ref verification_commit_sha1
    authoritative_ref_read authoritative_base_tree_read base_tree_sha1
    target_tree_sha1 publication_commit_sha1
    publication_reachable_from_verification_ref
    publication_parent_commit_sha1s publication_changed_paths
    target_absent_at_base semantic_ancestor_verified target_tree_build_count
    publication_commit_parent_count requested_expected_old_sha1
    observed_old_sha1 server_side_expected_old_applied authoritative_head_read
    authoritative_parent_read authoritative_tree_read
    authoritative_recursive_tree_read changed_path_proof_complete
    artifact_at_publication artifact_at_verification_ref
    unchanged_path_observation unchanged_path_mismatches owner_issue_codes
    independent_issue_codes postfetch_state
    """.split()
)
_SUCCESS_EXACT1_ARTIFACT_KEYS = frozenset(
    "path git_blob_sha1 raw_sha256 logical_artifact_sha256 body_free".split()
)

_SUCCESS_ARTIFACT_CONTRACT_BY_PATH: dict[str, tuple[str, str]] = {
    RECOVERY_EPOCH002_SUCCESS_PATHS[0]: (
        "ACCEPTED_TEST_RUN_RECEIPT",
        "accepted_test_run_receipt_sha256",
    ),
    **{
        RECOVERY_EPOCH002_SUCCESS_PATHS[step + 1]: (
            "CURRENT_STEP_COMPLETION_RECEIPT",
            "receipt_sha256",
        )
        for step in range(11)
    },
    RECOVERY_EPOCH002_SUCCESS_PATHS[12]: (
        "ALL11_COMPLETION_CHAIN",
        "all11_completion_chain_sha256",
    ),
    RECOVERY_EPOCH002_SUCCESS_PATHS[13]: (
        "ALL11_ATOMIC_PUBLICATION_MANIFEST",
        "atomic_publication_manifest_sha256",
    ),
    RECOVERY_EPOCH002_SUCCESS_PATHS[14]: (
        "SEQUENCE_EVENT_2",
        "event_sha256",
    ),
}


def _success_candidate_identity(
    artifact: Any,
    *,
    path: str,
    role: str,
    logical_hash_key: str,
) -> dict[str, Any] | None:
    if (
        type(artifact) is not dict
        or artifact.get("body_free") is not True
        or artifact.get(logical_hash_key)
        != _hash_without(artifact, logical_hash_key)
    ):
        return None
    payload = _canonical_json_bytes(artifact)
    return {
        "artifact_role": role,
        "schema_version": artifact.get("schema_version"),
        "repository_full_name": RECOVERY_EPOCH002_PUBLICATION_REPOSITORY,
        "path": path,
        "git_blob_sha1": _git_blob_sha1(payload),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "logical_artifact_sha256": artifact.get(logical_hash_key),
        "body_free": True,
    }


def _success_external_identity(
    candidate: Mapping[str, Any],
    publication_commit_sha1: str,
) -> dict[str, Any]:
    identity = {
        **dict(candidate),
        "publication_commit_sha1": publication_commit_sha1,
        "identity_sha256": "",
    }
    identity["identity_sha256"] = _hash_without(
        identity,
        "identity_sha256",
    )
    return identity


def _success_exact1_postfetch_valid(
    evidence: Any,
    identity: Mapping[str, Any],
    *,
    base_commit_sha1: str,
) -> bool:
    if (
        type(evidence) is not dict
        or set(evidence) != _SUCCESS_EXACT1_POSTFETCH_KEYS
    ):
        return False
    artifact = {
        "path": identity.get("path"),
        "git_blob_sha1": identity.get("git_blob_sha1"),
        "raw_sha256": identity.get("raw_sha256"),
        "logical_artifact_sha256": identity.get(
            "logical_artifact_sha256"
        ),
        "body_free": identity.get("body_free"),
    }
    unchanged = evidence.get("unchanged_path_observation")
    return (
        evidence.get("repository_full_name")
        == RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        and evidence.get("verification_ref")
        == RECOVERY_EPOCH002_PUBLICATION_REF
        and evidence.get("verification_commit_sha1")
        == identity.get("publication_commit_sha1")
        and evidence.get("authoritative_ref_read") is True
        and evidence.get("authoritative_base_tree_read") is True
        and _SHA1_RE.fullmatch(str(evidence.get("base_tree_sha1", "")))
        is not None
        and _SHA1_RE.fullmatch(str(evidence.get("target_tree_sha1", "")))
        is not None
        and evidence.get("base_tree_sha1") != "f" * 40
        and evidence.get("target_tree_sha1") != "f" * 40
        and evidence.get("base_tree_sha1")
        != evidence.get("target_tree_sha1")
        and evidence.get("publication_commit_sha1")
        == identity.get("publication_commit_sha1")
        and evidence.get("publication_reachable_from_verification_ref")
        is True
        and evidence.get("publication_parent_commit_sha1s")
        == [base_commit_sha1]
        and evidence.get("publication_changed_paths")
        == [identity.get("path")]
        and evidence.get("target_absent_at_base") is True
        and evidence.get("semantic_ancestor_verified") is True
        and type(evidence.get("target_tree_build_count")) is int
        and evidence.get("target_tree_build_count") == 1
        and type(evidence.get("publication_commit_parent_count")) is int
        and evidence.get("publication_commit_parent_count") == 1
        and evidence.get("requested_expected_old_sha1")
        == base_commit_sha1
        and evidence.get("observed_old_sha1") == base_commit_sha1
        and evidence.get("server_side_expected_old_applied") is True
        and evidence.get("authoritative_head_read") is True
        and evidence.get("authoritative_parent_read") is True
        and evidence.get("authoritative_tree_read") is True
        and evidence.get("authoritative_recursive_tree_read") is True
        and evidence.get("changed_path_proof_complete") is True
        and type(evidence.get("artifact_at_publication")) is dict
        and set(evidence["artifact_at_publication"])
        == _SUCCESS_EXACT1_ARTIFACT_KEYS
        and evidence["artifact_at_publication"] == artifact
        and type(evidence.get("artifact_at_verification_ref")) is dict
        and set(evidence["artifact_at_verification_ref"])
        == _SUCCESS_EXACT1_ARTIFACT_KEYS
        and evidence["artifact_at_verification_ref"] == artifact
        and type(unchanged) is dict
        and set(unchanged) == _SUCCESS_UNCHANGED_KEYS
        and unchanged.get("scope") == "ALL_PATHS_EXCEPT_EXACT1_TARGET"
        and unchanged.get("mode_type_sha_complete") is True
        and unchanged.get("mismatches") == []
        and unchanged.get("observation_sha256")
        == _hash_without(unchanged, "observation_sha256")
        and evidence.get("unchanged_path_mismatches") == []
        and evidence.get("owner_issue_codes") == []
        and evidence.get("independent_issue_codes") == []
        and evidence.get("postfetch_state") == "POSTVERIFIED"
    )


def _success_exact1_publication_valid(
    publication: Any,
    *,
    role: str,
    path: str,
) -> bool:
    if (
        type(publication) is not dict
        or set(publication) != _SUCCESS_EXACT1_PUBLICATION_KEYS
        or type(publication.get("artifact")) is not dict
        or type(publication.get("identity")) is not dict
        or set(publication["identity"]) != _SUCCESS_EXTERNAL_IDENTITY_KEYS
        or publication.get("changed_paths") != [path]
        or publication.get("parent_commit_sha1s")
        != [publication.get("expected_old_sha1")]
        or publication.get("observed_old_sha1")
        != publication.get("expected_old_sha1")
        or publication.get("postfetch_state") != "POSTVERIFIED"
    ):
        return False
    artifact = publication["artifact"]
    logical_hash_key = _ROLE_LOGICAL_HASH_KEYS[role]
    candidate = _success_candidate_identity(
        artifact,
        path=path,
        role=role,
        logical_hash_key=logical_hash_key,
    )
    if candidate is None:
        return False
    expected = _success_external_identity(
        candidate,
        publication["identity"].get("publication_commit_sha1", ""),
    )
    return (
        publication["identity"] == expected
        and _success_exact1_postfetch_valid(
            publication.get("postfetch_evidence"),
            expected,
            base_commit_sha1=publication.get("expected_old_sha1"),
        )
    )


def validate_recovery_epoch002_post_d2_single_publication_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the two additive exact1 post-D2 publication roles."""

    if (
        type(state) is not dict
        or set(state) != _SUCCESS_SINGLE_PUBLICATION_STATE_KEYS
        or _contains_forbidden_key(state)
    ):
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    supported_roles = state.get("supported_roles")
    if supported_roles != sorted(RECOVERY_EPOCH002_PUBLICATION_ROLES):
        if (
            type(supported_roles) is list
            and "P1_OPERATIONAL_ADMISSION_RECEIPT"
            not in supported_roles
        ):
            return ("SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",)
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    if state.get("additive_role_paths") != {
        "SUCCESSOR_COMPLETION_RECEIPT": (
            RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH
        ),
        "P1_OPERATIONAL_ADMISSION_RECEIPT": (
            RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH
        ),
    }:
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    transactions = state.get("exact1_transactions")
    if type(transactions) is not list or len(transactions) != 2:
        if (
            type(transactions) is list
            and not any(
                type(transaction) is dict
                and transaction.get("artifact_role")
                == "P1_OPERATIONAL_ADMISSION_RECEIPT"
                for transaction in transactions
            )
        ):
            return ("SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",)
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    contracts = (
        (
            "SUCCESSOR_COMPLETION_RECEIPT",
            RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH,
            "SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",
        ),
        (
            "P1_OPERATIONAL_ADMISSION_RECEIPT",
            RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH,
            "SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",
        ),
    )
    for transaction, (role, path, code) in zip(
        transactions,
        contracts,
        strict=True,
    ):
        if (
            type(transaction) is not dict
            or set(transaction) != _SUCCESS_SINGLE_TRANSACTION_KEYS
            or transaction.get("artifact_role") != role
            or transaction.get("path") != path
            or transaction.get("expected_changed_paths") != [path]
            or transaction.get("parent_commit_sha1s")
            != [transaction.get("expected_old_sha1")]
            or transaction.get("requested_expected_old_sha1")
            != transaction.get("expected_old_sha1")
            or transaction.get("observed_old_sha1")
            != transaction.get("expected_old_sha1")
            or _SHA1_RE.fullmatch(
                str(transaction.get("head_commit_sha1", ""))
            )
            is None
            or transaction.get("target_absent_at_base") is not True
            or transaction.get("unchanged_path_mismatches") != []
            or transaction.get("owner_issue_codes") != []
            or transaction.get("independent_issue_codes") != []
            or transaction.get("postfetch_state") != "POSTVERIFIED"
            or not _success_exact1_publication_valid(
                transaction.get("publication"),
                role=role,
                path=path,
            )
            or transaction["publication"]["identity"].get(
                "publication_commit_sha1"
            )
            != transaction.get("head_commit_sha1")
            or transaction["publication"].get("parent_commit_sha1s")
            != transaction.get("parent_commit_sha1s")
        ):
            return (code,)
    return ()


def _success_manifest_shape_valid(manifest: Any) -> bool:
    return (
        type(manifest) is dict
        and set(manifest) == RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_KEYS
        and manifest.get("schema_version")
        == RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_SCHEMA
        and manifest.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and manifest.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        and manifest.get("body_free") is True
        and manifest.get("atomic_publication_manifest_sha256")
        == _hash_without(
            manifest,
            "atomic_publication_manifest_sha256",
        )
    )


def _success_transaction_capability_valid(
    event: Mapping[str, Any],
    *,
    terminal_commit: str,
) -> bool:
    publication = event.get("publication")
    capability = (
        publication.get("transaction_capability")
        if type(publication) is dict
        else None
    )
    authority = event.get("authority")
    admission = (
        authority.get("operational_admission")
        if type(authority) is dict
        else None
    )
    return (
        type(capability) is dict
        and set(capability) == _SUCCESS_TRANSACTION_CAPABILITY_KEYS
        and capability.get("schema_version")
        == (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "git_transaction_capability.v1"
        )
        and capability.get("provider_class")
        == "EXPECTED_OLD_CAS_CAPABLE_GITHUB_TRANSPORT"
        and capability.get("repository_full_name")
        == RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        and capability.get("source_ref")
        == RECOVERY_EPOCH002_PUBLICATION_REF
        and capability.get("base_commit_sha1") == terminal_commit
        and capability.get("expected_changed_path_count") == 15
        and type(capability.get("expected_changed_path_count")) is int
        and capability.get("authoritative_ref_read") is True
        and capability.get("expected_old_compare_and_swap") is True
        and capability.get("commit_parent_tree_and_recursive_read") is True
        and capability.get(
            "full_changed_and_unchanged_postfetch_verification"
        )
        is True
        and capability.get("challenge_id") == event.get("challenge_id")
        and type(admission) is dict
        and capability.get("operational_admission_identity_sha256")
        == admission.get("identity_sha256")
        and capability.get("transaction_capability_sha256")
        == _hash_without(capability, "transaction_capability_sha256")
    )


def _validate_recovery_epoch002_success_publication_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the frozen one-tree/one-commit success exact15 result."""

    if (
        type(state) is not dict
        or set(state) != _SUCCESS_PUBLICATION_STATE_KEYS
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)
    terminal = state.get("terminal_commit_observation")
    if (
        type(terminal) is dict
        and type(terminal.get("paths_present")) is list
        and set(terminal["paths_present"])
        & set(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
    ):
        return ("SUCCESS_PATH_ALREADY_EXISTS_AT_T",)
    manifest = state.get("atomic_publication_manifest")
    manifest_self_valid = _success_manifest_shape_valid(manifest)
    if (
        manifest_self_valid
        and (
            manifest.get("core_artifact_count") != 13
            or type(manifest.get("core_artifact_count")) is not int
            or type(manifest.get("core_artifacts")) is not list
            or [
                row.get("path")
                for row in manifest.get("core_artifacts", ())
                if type(row) is dict
            ]
            != list(RECOVERY_EPOCH002_SUCCESS_CORE_PATHS)
        )
    ):
        return ("SUCCESS_CORE_ARTIFACT_SET_INVALID",)
    if (
        manifest_self_valid
        and manifest.get("core_artifact_set_sha256")
        != artifact_sha256(manifest["core_artifacts"])
    ):
        return ("ATOMIC_MANIFEST_CORE_SET_HASH_INVALID",)

    transaction = state.get("publication_transaction")
    if (
        type(transaction) is dict
        and {
            "target_tree_build_count",
            "success_commit_build_count",
        }
        <= set(transaction)
        and (
            transaction.get("target_tree_build_count") != 1
            or type(transaction.get("target_tree_build_count")) is not int
            or transaction.get("success_commit_build_count") != 1
            or type(transaction.get("success_commit_build_count")) is not int
        )
    ):
        return ("SUCCESS_PUBLICATION_ONE_TREE_ONE_COMMIT_INVALID",)
    if (
        type(transaction) is dict
        and {"parent_commit_sha1s", "terminal_commit_sha1"}
        <= set(transaction)
        and transaction.get("parent_commit_sha1s")
        != [transaction.get("terminal_commit_sha1")]
    ):
        return ("SUCCESS_COMMIT_DIRECT_PARENT_INVALID",)
    if (
        type(transaction) is dict
        and {
            "requested_expected_old_sha1",
            "observed_old_sha1",
            "terminal_commit_sha1",
            "server_side_expected_old_applied",
        }
        <= set(transaction)
        and (
            transaction.get("requested_expected_old_sha1")
            != transaction.get("terminal_commit_sha1")
            or transaction.get("observed_old_sha1")
            != transaction.get("terminal_commit_sha1")
            or transaction.get("server_side_expected_old_applied") is not True
        )
    ):
        return ("SUCCESS_EXPECTED_OLD_LEASE_INVALID",)
    if type(transaction) is dict and transaction.get(
        "ref_update_result"
    ) == "UNKNOWN":
        if (
            transaction.get("same_frozen_success_commit_reused") is not True
            or transaction.get("frozen_success_commit_sha1")
            != transaction.get("reconciled_success_commit_sha1")
            or transaction.get("ref_update_attempt_count") != 1
            or type(transaction.get("ref_update_attempt_count")) is not int
            or transaction.get("automatic_retry_requested") is not False
            or transaction.get("publication_only_retry_requested") is not False
            or transaction.get("publication_only_authority_present") is not False
            or transaction.get("new_accepted_receipt_requested") is not False
            or transaction.get("rebase_requested") is not False
            or transaction.get("timestamp_rebuild_requested") is not False
        ):
            return (
                "SUCCESS_PUBLICATION_UNKNOWN_RESULT_RECONCILIATION_STOP",
            )

    artifacts = state.get("artifacts_by_path")
    candidates = state.get("candidate_identities_by_path")
    event = state.get("event2")
    if (
        type(terminal) is not dict
        or set(terminal) != _SUCCESS_TERMINAL_OBSERVATION_KEYS
        or terminal.get("authoritative_ref_read") is not True
        or terminal.get("authoritative_tree_read") is not True
        or _SHA1_RE.fullmatch(str(terminal.get("commit_sha1", ""))) is None
        or _SHA1_RE.fullmatch(str(terminal.get("tree_sha1", ""))) is None
        or terminal.get("commit_sha1") == "f" * 40
        or terminal.get("tree_sha1") == "f" * 40
        or terminal.get("paths_present") != []
        or type(transaction) is not dict
        or set(transaction) != _SUCCESS_TRANSACTION_KEYS
        or not _success_manifest_shape_valid(manifest)
        or transaction.get("terminal_commit_sha1")
        != terminal.get("commit_sha1")
        or transaction.get("base_tree_sha1") != terminal.get("tree_sha1")
        or _SHA1_RE.fullmatch(
            str(transaction.get("target_tree_sha1", ""))
        )
        is None
        or transaction.get("target_tree_sha1") == "f" * 40
        or transaction.get("target_tree_sha1")
        == transaction.get("base_tree_sha1")
        or transaction.get("changed_paths")
        != list(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
        or type(artifacts) is not dict
        or set(artifacts) != set(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
        or type(candidates) is not dict
        or set(candidates) != set(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
        or type(event) is not dict
        or not _success_transaction_capability_valid(
            event,
            terminal_commit=terminal["commit_sha1"],
        )
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)

    expected_candidates: dict[str, dict[str, Any]] = {}
    for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS:
        role, hash_key = _SUCCESS_ARTIFACT_CONTRACT_BY_PATH[path]
        candidate = _success_candidate_identity(
            artifacts[path],
            path=path,
            role=role,
            logical_hash_key=hash_key,
        )
        if (
            candidate is None
            or type(candidates[path]) is not dict
            or set(candidates[path])
            != RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS
            or candidates[path] != candidate
        ):
            return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)
        expected_candidates[path] = candidate
    accepted = artifacts[RECOVERY_EPOCH002_SUCCESS_PATHS[0]]
    all11 = artifacts[RECOVERY_EPOCH002_SUCCESS_PATHS[12]]
    accepted_lineage = (
        accepted.get("success_lineage")
        if type(accepted) is dict
        else None
    )
    source_baseline_event = (
        accepted_lineage.get("source_baseline_event")
        if type(accepted_lineage) is dict
        else None
    )
    if (
        manifest.get("core_artifacts")
        != [
            expected_candidates[path]
            for path in RECOVERY_EPOCH002_SUCCESS_CORE_PATHS
        ]
        or manifest.get("base_commit_sha1") != terminal.get("commit_sha1")
        or manifest.get("event_supporting_artifact_count") != 14
        or type(manifest.get("event_supporting_artifact_count")) is not int
        or manifest.get("expected_changed_path_count") != 15
        or type(manifest.get("expected_changed_path_count")) is not int
        or manifest.get("event_path")
        != RECOVERY_EPOCH002_SUCCESS_PATHS[14]
        or manifest.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or manifest.get("candidate_version_id")
        != all11.get("candidate_version_id")
        or manifest.get("candidate_version_id")
        != event.get("candidate_version_id")
        or manifest.get("source_baseline_event")
        != source_baseline_event
        or manifest.get("source_baseline_event")
        != event.get("prior_event")
        or manifest.get("ref_update_mode")
        != "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)

    expected_blob_map = {
        path: expected_candidates[path]["git_blob_sha1"]
        for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
    }
    success_commit = transaction.get("frozen_success_commit_sha1")
    postfetch = state.get("postfetch_observation")
    expected_external = [
        _success_external_identity(
            expected_candidates[path],
            success_commit,
        )
        for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
    ]
    if (
        _SHA1_RE.fullmatch(str(success_commit)) is None
        or transaction.get("target_blob_sha1_by_path") != expected_blob_map
        or transaction.get("ref_update_result") not in {"SUCCEEDED", "UNKNOWN"}
        or transaction.get("ref_update_attempt_count") != 1
        or type(transaction.get("ref_update_attempt_count")) is not int
        or transaction.get("reconciled_success_commit_sha1") != success_commit
        or transaction.get("same_frozen_success_commit_reused") is not True
        or any(
            transaction.get(key) is not False
            for key in (
                "automatic_retry_requested",
                "publication_only_retry_requested",
                "publication_only_authority_present",
                "new_accepted_receipt_requested",
                "rebase_requested",
                "timestamp_rebuild_requested",
            )
        )
        or type(postfetch) is not dict
        or set(postfetch) != _SUCCESS_POSTFETCH_KEYS
        or postfetch.get("head_commit_sha1") != success_commit
        or postfetch.get("parent_commit_sha1s")
        != [terminal.get("commit_sha1")]
        or postfetch.get("target_tree_sha1")
        != transaction.get("target_tree_sha1")
        or any(
            postfetch.get(key) is not True
            for key in (
                "authoritative_ref_read",
                "authoritative_head_read",
                "authoritative_parent_read",
                "authoritative_tree_read",
                "authoritative_recursive_tree_read",
                "changed_path_proof_complete",
            )
        )
        or postfetch.get("changed_paths")
        != list(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
        or postfetch.get("artifact_raw_sha256_by_path")
        != {
            path: expected_candidates[path]["raw_sha256"]
            for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("artifact_git_blob_sha1_by_path")
        != expected_blob_map
        or postfetch.get("artifact_logical_sha256_by_path")
        != {
            path: expected_candidates[path]["logical_artifact_sha256"]
            for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("artifact_schema_by_path")
        != {
            path: expected_candidates[path]["schema_version"]
            for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("artifact_body_free_by_path")
        != {
            path: True
            for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("publication_external_identities")
        != expected_external
        or postfetch.get("unchanged_path_mismatches") != []
        or postfetch.get("owner_issue_codes") != []
        or postfetch.get("independent_issue_codes") != []
        or postfetch.get("state") != "POSTVERIFIED"
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)
    unchanged = postfetch.get("unchanged_path_observation")
    if (
        type(unchanged) is not dict
        or set(unchanged) != _SUCCESS_UNCHANGED_KEYS
        or unchanged.get("scope") != "ALL_PATHS_EXCEPT_SUCCESS_EXACT15"
        or unchanged.get("mode_type_sha_complete") is not True
        or unchanged.get("mismatches") != []
        or unchanged.get("observation_sha256")
        != _hash_without(unchanged, "observation_sha256")
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)
    event2_issues = validate_recovery_epoch002_success_event2_state(state)
    if event2_issues:
        return event2_issues
    return ()


def validate_recovery_epoch002_success_publication_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed success exact15 publication state."""

    try:
        if _contains_forbidden_key(state):
            return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)
        return _validate_recovery_epoch002_success_publication_state_impl(
            state
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)


__all__ = [
    "RECOVERY_EPOCH002_PUBLICATION_REPOSITORY",
    "RECOVERY_EPOCH002_PUBLICATION_REF",
    "RECOVERY_EPOCH002_PUBLICATION_ROLES",
    "RECOVERY_EPOCH002_PUBLICATION_CANDIDATE_KEYS",
    "RECOVERY_EPOCH002_PUBLICATION_RESULT_KEYS",
    "RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_READY_UNUSED_AUTHORITY_STOP_KEYS",
    "RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_SCHEMA",
    "RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_KEYS",
    "RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_PATHS",
    "RECOVERY_EPOCH002_SUCCESS_CORE_PATHS",
    "RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS",
    "RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS",
    "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH",
    "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH",
    "build_recovery_epoch002_publication_candidate",
    "validate_recovery_epoch002_publication_candidate",
    "validate_recovery_epoch002_publication_result",
    "build_recovery_epoch002_artifact_identity",
    "validate_recovery_epoch002_artifact_identity",
    "validate_recovery_epoch002_ready_unused_authority_stop",
    "validate_recovery_epoch002_success_publication_state",
    "validate_recovery_epoch002_post_d2_single_publication_state",
]
