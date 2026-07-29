#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Side-effect-free publication plans for Recovery Epoch 002.

The owner prepares target-scoped artifacts and validates their content after
publication.  Git transport is deliberately outside this module: a caller
may use the ordinary available GitHub write function and then supply fresh
target-path observations for validation.  Legacy field names that mention an
``expected_old`` ref are retained as diagnostic schema compatibility only;
they do not require compare-and-swap, direct-child, or one-commit transport.
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
RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT = (
    "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
)
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
        "reflection_contract_version",
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
        "reflection_contract_version",
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
_LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_completion_receipt.v2"
)
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
_SOURCE_BASELINE_EVENT_SCHEMAS = frozenset(
    {
        _ROLE_SCHEMAS["SOURCE_BASELINE_EVENT"],
        "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v2",
    }
)


def _role_schema_valid(artifact_role: str, schema_version: Any) -> bool:
    if artifact_role == "SOURCE_BASELINE_EVENT":
        return schema_version in _SOURCE_BASELINE_EVENT_SCHEMAS
    if artifact_role == "SUCCESSOR_COMPLETION_RECEIPT":
        return (
            schema_version
            == _ROLE_SCHEMAS["SUCCESSOR_COMPLETION_RECEIPT"]
            or schema_version == _LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA
        )
    return schema_version == _ROLE_SCHEMAS.get(artifact_role)

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
_LINEAGE02_SUCCESSOR_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2"
    "SourceIdentityLineage02_SourceBaselineEligibilitySuccessor"
    "Completion_BodyFree_Receipt_20260728.json"
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_P1OperationalAdmission_"
    "BodyFree_Receipt_20260726.json"
)


def _role_schema_path_valid(
    artifact_role: str,
    schema_version: Any,
    path: Any,
) -> bool:
    if artifact_role != "SUCCESSOR_COMPLETION_RECEIPT":
        return True
    return (
        schema_version
        == _ROLE_SCHEMAS["SUCCESSOR_COMPLETION_RECEIPT"]
        and path == RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH
    ) or (
        schema_version == _LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA
        and path == _LINEAGE02_SUCCESSOR_COMPLETION_PATH
    )


def _role_publication_path_valid(
    artifact_role: Any,
    path: Any,
) -> bool:
    if artifact_role != "SUCCESSOR_COMPLETION_RECEIPT":
        return True
    return (
        path == RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH
        or path == _LINEAGE02_SUCCESSOR_COMPLETION_PATH
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
    """Build an inert exact-one-path publication candidate.

    ``expected_old_sha1`` records the pre-write ref observation required by
    the current contract's latest-version check.  It is not a CAS lease.
    """

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
        or not _role_schema_valid(
            artifact_role,
            artifact.get("schema_version"),
        )
        or not _role_schema_path_valid(
            artifact_role,
            artifact.get("schema_version"),
            path,
        )
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
        "reflection_contract_version": (
            RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        ),
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
        or candidate.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
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
        or not _role_schema_valid(
            str(candidate.get("artifact_role", "")),
            artifact.get("schema_version"),
        )
        or not _role_schema_path_valid(
            str(candidate.get("artifact_role", "")),
            artifact.get("schema_version"),
            candidate.get("path"),
        )
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
    required_keys = RECOVERY_EPOCH002_PUBLICATION_RESULT_KEYS - {
        "observed_old_sha1",
        "parent_commit_sha1s",
    }
    if (
        not required_keys <= set(result)
        or not set(result) <= RECOVERY_EPOCH002_PUBLICATION_RESULT_KEYS
    ):
        return ("PUBLICATION_RESULT_INVALID",)
    expected_old = result.get("expected_old_sha1")
    path = result.get("path")
    commit = result.get("publication_commit_sha1")
    if (
        result.get("artifact_role")
        not in RECOVERY_EPOCH002_PUBLICATION_ROLES
        or result.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        or result.get("repository_full_name")
        != RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        or result.get("source_ref") != RECOVERY_EPOCH002_PUBLICATION_REF
        or not _new_document_path_valid(path)
        or not _role_publication_path_valid(
            result.get("artifact_role"),
            path,
        )
        or result.get("path_preexisted") is not False
        or _SHA1_RE.fullmatch(str(expected_old or "")) is None
        or _SHA1_RE.fullmatch(str(commit or "")) is None
        or commit == expected_old
        or _SHA1_RE.fullmatch(
            str(result.get("candidate_git_blob_sha1", ""))
        )
        is None
        or result.get("expected_changed_paths") != [path]
        or result.get("changed_paths") != [path]
        or result.get("postfetch_succeeded") is not True
        or result.get("postfetch_matches_candidate") is not True
        or _SHA1_RE.fullmatch(
            str(result.get("postfetch_commit_sha1", ""))
        )
        is None
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
            "reflection_contract_version",
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
        or not _role_schema_valid(
            str(identity.get("artifact_role", "")),
            identity.get("schema_version"),
        )
        or not _role_schema_path_valid(
            str(identity.get("artifact_role", "")),
            identity.get("schema_version"),
            identity.get("path"),
        )
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
    reflection_contract_version
    target_tree_build_count success_commit_build_count terminal_commit_sha1
    base_tree_sha1 target_tree_sha1 parent_commit_sha1s
    requested_expected_old_sha1 observed_old_sha1
    server_side_expected_old_applied changed_paths
    target_blob_sha1_by_path ref_update_result ref_update_attempt_count
    frozen_success_commit_sha1 reconciled_success_commit_sha1
    same_frozen_success_commit_reused automatic_retry_requested
    publication_only_retry_requested publication_only_authority_present
    new_accepted_receipt_requested rebase_requested
    timestamp_rebuild_requested publication_commit_sha1_by_path
    write_commits
    """.split()
)
_SUCCESS_TRANSACTION_REQUIRED_KEYS = frozenset(
    """
    reflection_contract_version changed_paths target_blob_sha1_by_path
    ref_update_result ref_update_attempt_count
    publication_commit_sha1_by_path write_commits
    """.split()
)
_SUCCESS_WRITE_COMMIT_KEYS = frozenset({"commit_sha1", "changed_paths"})
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
        "reflection_contract_version",
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
    reflection_contract_version artifact_role path expected_changed_paths
    parent_commit_sha1s
    expected_old_sha1 requested_expected_old_sha1 observed_old_sha1
    head_commit_sha1 target_absent_at_base unchanged_path_mismatches
    owner_issue_codes independent_issue_codes postfetch_state publication
    """.split()
)
_SUCCESS_EXACT1_PUBLICATION_KEYS = frozenset(
    """
    reflection_contract_version artifact identity changed_paths
    parent_commit_sha1s expected_old_sha1
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
    required_keys = frozenset(
        {
            "repository_full_name",
            "verification_ref",
            "verification_commit_sha1",
            "publication_changed_paths",
            "target_absent_at_base",
            "authoritative_ref_read",
            "authoritative_head_read",
            "artifact_at_verification_ref",
            "owner_issue_codes",
            "independent_issue_codes",
            "postfetch_state",
        }
    )
    if (
        type(evidence) is not dict
        or not required_keys <= set(evidence)
        or not set(evidence) <= _SUCCESS_EXACT1_POSTFETCH_KEYS
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
    return (
        evidence.get("repository_full_name")
        == RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        and evidence.get("verification_ref")
        == RECOVERY_EPOCH002_PUBLICATION_REF
        and _SHA1_RE.fullmatch(
            str(evidence.get("verification_commit_sha1", ""))
        )
        is not None
        and evidence.get("authoritative_ref_read") is True
        and evidence.get("publication_changed_paths")
        == [identity.get("path")]
        and evidence.get("target_absent_at_base") is True
        and evidence.get("authoritative_head_read") is True
        and type(evidence.get("artifact_at_verification_ref")) is dict
        and set(evidence["artifact_at_verification_ref"])
        == _SUCCESS_EXACT1_ARTIFACT_KEYS
        and evidence["artifact_at_verification_ref"] == artifact
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
    required_keys = frozenset(
        {
            "reflection_contract_version",
            "artifact",
            "identity",
            "changed_paths",
            "postfetch_evidence",
            "postfetch_state",
        }
    )
    if (
        type(publication) is not dict
        or not required_keys <= set(publication)
        or not set(publication) <= _SUCCESS_EXACT1_PUBLICATION_KEYS
        or publication.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        or type(publication.get("artifact")) is not dict
        or type(publication.get("identity")) is not dict
        or set(publication["identity"]) != _SUCCESS_EXTERNAL_IDENTITY_KEYS
        or publication.get("changed_paths") != [path]
        or publication.get("postfetch_state") != "POSTVERIFIED"
    ):
        return False
    artifact = publication["artifact"]
    if (
        not _role_schema_valid(role, artifact.get("schema_version"))
        or not _role_schema_path_valid(
            role,
            artifact.get("schema_version"),
            path,
        )
        or _contains_forbidden_key(artifact)
        or _role_artifact_issues(role, artifact)
    ):
        return False
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
            base_commit_sha1=publication.get("expected_old_sha1", ""),
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
    completion_transaction = transactions[0]
    completion_publication = (
        completion_transaction.get("publication")
        if type(completion_transaction) is dict
        else None
    )
    completion_artifact = (
        completion_publication.get("artifact")
        if type(completion_publication) is dict
        else None
    )
    completion_schema = (
        completion_artifact.get("schema_version")
        if type(completion_artifact) is dict
        else None
    )
    if (
        completion_schema
        == _ROLE_SCHEMAS["SUCCESSOR_COMPLETION_RECEIPT"]
    ):
        completion_path = RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH
    elif completion_schema == _LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA:
        completion_path = _LINEAGE02_SUCCESSOR_COMPLETION_PATH
    else:
        completion_path = None
    if completion_path is None or state.get("additive_role_paths") != {
        "SUCCESSOR_COMPLETION_RECEIPT": completion_path,
        "P1_OPERATIONAL_ADMISSION_RECEIPT": (
            RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH
        ),
    }:
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    contracts = (
        (
            "SUCCESSOR_COMPLETION_RECEIPT",
            completion_path,
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
        required_transaction_keys = frozenset(
            {
                "reflection_contract_version",
                "artifact_role",
                "path",
                "expected_changed_paths",
                "head_commit_sha1",
                "target_absent_at_base",
                "owner_issue_codes",
                "independent_issue_codes",
                "postfetch_state",
                "publication",
            }
        )
        if (
            type(transaction) is not dict
            or not required_transaction_keys <= set(transaction)
            or not set(transaction) <= _SUCCESS_SINGLE_TRANSACTION_KEYS
            or transaction.get("reflection_contract_version")
            != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
            or transaction.get("artifact_role") != role
            or transaction.get("path") != path
            or transaction.get("expected_changed_paths") != [path]
            or _SHA1_RE.fullmatch(
                str(transaction.get("head_commit_sha1", ""))
            )
            is None
            or transaction.get("target_absent_at_base") is not True
            or transaction.get("owner_issue_codes") != []
            or transaction.get("independent_issue_codes") != []
            or transaction.get("postfetch_state") != "POSTVERIFIED"
            or not _success_exact1_publication_valid(
                transaction.get("publication"),
                role=role,
                path=path,
            )
        ):
            return (code,)
    return ()


def _success_manifest_shape_valid(manifest: Any) -> bool:
    required_keys = (
        RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_KEYS
        - {"ref_update_mode"}
    )
    return (
        type(manifest) is dict
        and required_keys <= set(manifest)
        and set(manifest) <= RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_KEYS
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


def _success_write_scope_valid(
    transaction: Mapping[str, Any],
) -> bool:
    """Validate every actual write commit without imposing one-commit shape."""

    expected_paths = set(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
    writes = transaction.get("write_commits")
    commit_by_path = transaction.get("publication_commit_sha1_by_path")
    if (
        type(writes) is not list
        or not writes
        or type(commit_by_path) is not dict
        or set(commit_by_path) != expected_paths
    ):
        return False

    observed_paths: set[str] = set()
    last_commit_by_path: dict[str, str] = {}
    observed_commits: set[str] = set()
    for write in writes:
        if (
            type(write) is not dict
            or set(write) != _SUCCESS_WRITE_COMMIT_KEYS
            or _SHA1_RE.fullmatch(str(write.get("commit_sha1", "")))
            is None
            or write.get("commit_sha1") in observed_commits
            or type(write.get("changed_paths")) is not list
            or not write["changed_paths"]
            or len(write["changed_paths"]) != len(set(write["changed_paths"]))
            or not set(write["changed_paths"]) <= expected_paths
        ):
            return False
        commit_sha1 = write["commit_sha1"]
        observed_commits.add(commit_sha1)
        for path in write["changed_paths"]:
            observed_paths.add(path)
            last_commit_by_path[path] = commit_sha1
    return (
        observed_paths == expected_paths
        and commit_by_path == last_commit_by_path
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
    if capability is None:
        return True
    return (
        type(capability) is dict
        and capability.get("repository_full_name")
        == RECOVERY_EPOCH002_PUBLICATION_REPOSITORY
        and capability.get("source_ref")
        == RECOVERY_EPOCH002_PUBLICATION_REF
        and capability.get("expected_changed_path_count") == 15
        and type(capability.get("expected_changed_path_count")) is int
        and capability.get("challenge_id") == event.get("challenge_id")
        and (
            not isinstance(capability.get("transaction_capability_sha256"), str)
            or capability.get("transaction_capability_sha256")
            == _hash_without(capability, "transaction_capability_sha256")
        )
        and (
            type(admission) is not dict
            or capability.get("operational_admission_identity_sha256")
            in {None, admission.get("identity_sha256")}
        )
    )


def _validate_recovery_epoch002_success_publication_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate one approved exact15 reflection checkpoint."""

    if (
        type(state) is not dict
        or set(state) != _SUCCESS_PUBLICATION_STATE_KEYS
        or state.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
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
    if type(transaction) is dict:
        ref_result = transaction.get("ref_update_result")
        if ref_result == "FAILED":
            return ("SUCCESS_PUBLICATION_WRITE_FAILED_STOP",)
        if ref_result == "NOT_APPLIED":
            return ("SUCCESS_PUBLICATION_NOT_APPLIED_STOP",)
    artifacts = state.get("artifacts_by_path")
    candidates = state.get("candidate_identities_by_path")
    event = state.get("event2")
    if (
        type(terminal) is not dict
        or set(terminal) != _SUCCESS_TERMINAL_OBSERVATION_KEYS
        or terminal.get("authoritative_ref_read") is not True
        or _SHA1_RE.fullmatch(str(terminal.get("commit_sha1", ""))) is None
        or terminal.get("commit_sha1") == "f" * 40
        or terminal.get("paths_present") != []
        or type(transaction) is not dict
        or not _SUCCESS_TRANSACTION_REQUIRED_KEYS <= set(transaction)
        or not set(transaction) <= _SUCCESS_TRANSACTION_KEYS
        or transaction.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        or not _success_manifest_shape_valid(manifest)
        or not _success_write_scope_valid(transaction)
        or (
            "target_tree_build_count" in transaction
            and (
                type(transaction.get("target_tree_build_count")) is not int
                or transaction.get("target_tree_build_count") < 1
            )
        )
        or (
            "success_commit_build_count" in transaction
            and (
                type(transaction.get("success_commit_build_count")) is not int
                or transaction.get("success_commit_build_count") < 1
            )
        )
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
    ):
        return ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)

    expected_blob_map = {
        path: expected_candidates[path]["git_blob_sha1"]
        for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
    }
    commit_by_path = transaction["publication_commit_sha1_by_path"]
    postfetch = state.get("postfetch_observation")
    expected_external = [
        _success_external_identity(
            expected_candidates[path],
            commit_by_path[path],
        )
        for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
    ]
    if (
        transaction.get("target_blob_sha1_by_path") != expected_blob_map
        or transaction.get("ref_update_result") not in {"SUCCEEDED", "UNKNOWN"}
        or type(transaction.get("ref_update_attempt_count")) is not int
        or transaction.get("ref_update_attempt_count") < 1
        or type(postfetch) is not dict
        or not {
            "head_commit_sha1",
            "authoritative_ref_read",
            "authoritative_head_read",
            "changed_paths",
            "artifact_raw_sha256_by_path",
            "artifact_git_blob_sha1_by_path",
            "artifact_logical_sha256_by_path",
            "artifact_schema_by_path",
            "artifact_body_free_by_path",
            "publication_external_identities",
            "owner_issue_codes",
            "independent_issue_codes",
            "state",
        }.issubset(postfetch)
        or not set(postfetch).issubset(_SUCCESS_POSTFETCH_KEYS)
        or _SHA1_RE.fullmatch(
            str(postfetch.get("head_commit_sha1", ""))
        )
        is None
        or postfetch.get("authoritative_ref_read") is not True
        or postfetch.get("authoritative_head_read") is not True
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
        or postfetch.get("owner_issue_codes") != []
        or postfetch.get("independent_issue_codes") != []
        or postfetch.get("state") != "POSTVERIFIED"
    ):
        if transaction.get("ref_update_result") == "UNKNOWN":
            return (
                "SUCCESS_PUBLICATION_UNKNOWN_RESULT_RECONCILIATION_STOP",
            )
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


_RECOVERY_EPOCH003_REFERENCE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PreEvent1_ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event.json"
)
_RECOVERY_EPOCH003_OPERATIONAL_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_OperationalRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_READINESS_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_BootstrapReadiness_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_FAILURE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_BootstrapPreflightFailure_BodyFree_Receipt.json"
)
RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS = {
    "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION": (
        _RECOVERY_EPOCH003_REFERENCE_PATH
    ),
    "RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT": (
        _RECOVERY_EPOCH003_EVENT1_PATH
    ),
    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION": (
        _RECOVERY_EPOCH003_OPERATIONAL_PATH
    ),
    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION_FAILURE_EVIDENCE": (
        _RECOVERY_EPOCH003_OPERATIONAL_PATH
    ),
    "RECOVERY_EPOCH003_BOOTSTRAP_READINESS": (
        _RECOVERY_EPOCH003_READINESS_PATH
    ),
    "RECOVERY_EPOCH003_FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE": (
        _RECOVERY_EPOCH003_FAILURE_PATH
    ),
}


def validate_recovery_epoch003_publication_contract_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate one body-free Epoch003 publication candidate without I/O."""

    try:
        if type(state) is not dict:
            return ("RECOVERY_EPOCH003_PUBLICATION_SCOPE_INVALID",)
        role = state.get("artifact_role")
        path = state.get("path")
        changed_paths = state.get("changed_paths")
        expected_path = RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS.get(role)
        if (
            expected_path is None
            or path != expected_path
            or type(changed_paths) is not list
            or changed_paths != [expected_path]
            or state.get("body_free") is not True
            or state.get("automatic_progression") is not False
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
        ):
            return ("RECOVERY_EPOCH003_PUBLICATION_SCOPE_INVALID",)
        return ()
    except (AttributeError, TypeError, ValueError):
        return ("RECOVERY_EPOCH003_PUBLICATION_SCOPE_INVALID",)


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
    "RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS",
    "validate_recovery_epoch003_publication_contract_state",
]
