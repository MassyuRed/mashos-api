#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent publication verifier for Recovery Epoch 002.

This verifier intentionally does not import the publication owner.
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


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
RECOVERY_EPOCH002_P0_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id parent_design receipt
    p0_external_identity_sha256
    """
)
RECOVERY_EPOCH002_P0_PARENT_DESIGN_KEYS = _keys(
    "path publication_commit_sha1 git_blob_sha1 raw_sha256"
)
RECOVERY_EPOCH002_P0_RECEIPT_KEYS = _keys(
    """
    path publication_commit_sha1 git_blob_sha1 raw_sha256
    logical_receipt_sha256
    """
)

_ROLE_SOURCE_BASELINE = "SOURCE_BASELINE_EVENT"
_ROLE_READINESS = "BOOTSTRAP_READINESS"
_ROLE_RESERVATION = "FORMAL_TEST_RUN_RESERVATION"
_ROLE_IDENTITY_ALIASES = {
    _ROLE_SOURCE_BASELINE: {
        "EVENT1",
        "SOURCE_BASELINE_EVENT",
    },
    _ROLE_READINESS: {"READINESS", "BOOTSTRAP_READINESS"},
    _ROLE_RESERVATION: {"FORMAL_TEST_RUN_RESERVATION"},
}
_ROLE_ARTIFACT_HASH_KEYS = {
    _ROLE_SOURCE_BASELINE: "event_sha256",
    _ROLE_READINESS: "bootstrap_readiness_receipt_sha256",
    _ROLE_RESERVATION: "formal_test_run_reservation_sha256",
}
_ROLE_SCHEMAS = {
    _ROLE_SOURCE_BASELINE: (
        "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v1"
    ),
    _ROLE_READINESS: (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_readiness.v1"
    ),
    _ROLE_RESERVATION: (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_test_run_reservation.v1"
    ),
}
_IDENTITY_ROLE_SCHEMAS = {
    alias: _ROLE_SCHEMAS[role]
    for role, aliases in _ROLE_IDENTITY_ALIASES.items()
    for alias in aliases
}
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def verify_recovery_epoch002_artifact_identity(
    identity: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(identity) is not dict:
        return ("ARTIFACT_IDENTITY_INVALID",)
    if set(identity) != RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS:
        return ("ARTIFACT_IDENTITY_INVALID",)
    if (
        identity.get("body_free") is not True
        or identity.get("identity_sha256")
        != _hash_without(identity, "identity_sha256")
    ):
        return ("ARTIFACT_IDENTITY_INVALID",)
    return ()


def verify_recovery_epoch002_operational_artifact_identity(
    identity: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate a publication identity at the operational boundary."""

    if verify_recovery_epoch002_artifact_identity(identity):
        return ("ARTIFACT_IDENTITY_INVALID",)
    identity_path = identity.get("path")
    parsed_path = (
        PurePosixPath(identity_path)
        if isinstance(identity_path, str) and identity_path
        else None
    )
    if (
        identity.get("artifact_role")
        not in _IDENTITY_ROLE_SCHEMAS
        or identity.get("schema_version")
        != _IDENTITY_ROLE_SCHEMAS.get(identity.get("artifact_role"))
        or identity.get("repository_full_name") != "MassyuRed/Cocolon"
        or parsed_path is None
        or parsed_path.is_absolute()
        or parsed_path.as_posix() != identity_path
        or ".." in parsed_path.parts
        or parsed_path.parent.as_posix()
        != "EmlisAIの実装済み資料/documents"
        or parsed_path.suffix != ".json"
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
    ):
        return ("ARTIFACT_IDENTITY_INVALID",)
    return ()


def verify_recovery_epoch002_p0_external_identity(
    identity: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(identity) is not dict:
        return ("P0_EXTERNAL_IDENTITY_INVALID",)
    if set(identity) != RECOVERY_EPOCH002_P0_EXTERNAL_IDENTITY_KEYS:
        return ("P0_EXTERNAL_IDENTITY_INVALID",)
    parent = identity.get("parent_design")
    receipt = identity.get("receipt")
    if (
        type(parent) is not dict
        or set(parent) != RECOVERY_EPOCH002_P0_PARENT_DESIGN_KEYS
        or type(receipt) is not dict
        or set(receipt) != RECOVERY_EPOCH002_P0_RECEIPT_KEYS
        or identity.get("p0_external_identity_sha256")
        != _hash_without(identity, "p0_external_identity_sha256")
    ):
        return ("P0_EXTERNAL_IDENTITY_INVALID",)
    return ()


def _publication_transaction_invalid(
    state: Mapping[str, Any],
    *,
    require_new_path: bool,
) -> bool:
    expected_old = state.get("expected_old_sha1")
    return (
        state.get("observed_old_sha1") != expected_old
        or state.get("parent_commit_sha1s") != [expected_old]
        or state.get("changed_paths") != state.get("expected_changed_paths")
        or type(state.get("expected_changed_paths")) is not list
        or len(state.get("expected_changed_paths", ())) != 1
        or (require_new_path and state.get("path_preexisted") is not False)
        or state.get("postfetch_succeeded") is not True
        or state.get("postfetch_matches_candidate") is not True
    )


def _publication_artifact_binding_invalid(
    state: Mapping[str, Any],
) -> bool:
    role = state.get("artifact_role")
    artifact = state.get("artifact")
    identity = state.get("artifact_external_identity")
    expected_paths = state.get("expected_changed_paths")
    hash_key = _ROLE_ARTIFACT_HASH_KEYS.get(role)
    return (
        role not in _ROLE_ARTIFACT_HASH_KEYS
        or type(artifact) is not dict
        or artifact.get("body_free") is not True
        or not isinstance(artifact.get("schema_version"), str)
        or hash_key not in artifact
        or artifact.get(hash_key) != _hash_without(artifact, hash_key)
        or verify_recovery_epoch002_artifact_identity(identity) != ()
        or identity.get("artifact_role")
        not in _ROLE_IDENTITY_ALIASES.get(role, set())
        or type(expected_paths) is not list
        or len(expected_paths) != 1
        or identity.get("path") != expected_paths[0]
        or state.get("owner_issue_codes") != []
        or state.get("independent_issue_codes") != []
    )


def verify_recovery_epoch002_publication_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Reconcile role-specific Git publication observations."""

    if type(state) is not dict:
        return ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)
    role = state.get("artifact_role")

    # Unknown reservation publication cannot be downgraded to absence or a
    # generic readiness failure.
    if (
        state.get("reservation_write_outcome") == "UNKNOWN"
        or state.get("authoritative_reservation_presence") == "UNKNOWN"
    ):
        return ("RESERVATION_PUBLICATION_OUTCOME_UNKNOWN_STOP",)

    # These observations are valid only for an unused readiness receipt.
    if (
        state.get("ready_receipt_marked_consumed") is True
        or state.get("fabricated_reservation_detected") is True
    ) and role == _ROLE_READINESS:
        return ("READY_UNUSED_ONLY",)

    if state.get("receipt_contains_self_commit_blob_or_raw_identity") is True:
        return ("READINESS_SELF_REFERENCE_INVALID",)

    if role == _ROLE_RESERVATION:
        if (
            _publication_artifact_binding_invalid(state)
            or _publication_transaction_invalid(
            state,
            require_new_path=True,
            )
        ):
            return ("RESERVATION_NOT_PUBLISHED_STOP",)
        if (
            state.get("reservation_write_outcome") != "SUCCEEDED"
            or state.get("authoritative_reservation_presence") != "PRESENT"
            or state.get("ready_receipt_marked_consumed") is not True
            or state.get("fabricated_reservation_detected") is not False
        ):
            return ("RESERVATION_NOT_PUBLISHED_STOP",)
        return ()

    if role == _ROLE_SOURCE_BASELINE:
        if (
            _publication_artifact_binding_invalid(state)
            or _publication_transaction_invalid(
                state,
                require_new_path=True,
            )
        ):
            return ("SOURCE_BASELINE_EVENT_NOT_PUBLISHED_STOP",)
        return ()

    if role == _ROLE_READINESS:
        if (
            _publication_artifact_binding_invalid(state)
            or _publication_transaction_invalid(
            state,
            require_new_path=True,
            )
        ):
            return ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)
        if (
            state.get("reservation_write_outcome") != "NOT_ATTEMPTED"
            or state.get("authoritative_reservation_presence") != "ABSENT"
            or state.get("ready_receipt_marked_consumed") is not False
            or state.get("fabricated_reservation_detected") is not False
        ):
            return ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)
        return ()

    return ("PUBLICATION_ARTIFACT_ROLE_INVALID",)


def verify_recovery_epoch002_published_artifact(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Strict operational verification over logical and raw artifact bytes."""

    issues = verify_recovery_epoch002_publication_state(state)
    if issues:
        return issues
    role = state["artifact_role"]
    artifact = state["artifact"]
    identity = state["artifact_external_identity"]
    hash_key = _ROLE_ARTIFACT_HASH_KEYS[role]
    payload = canonical_json_bytes(artifact) + b"\n"
    header = f"blob {len(payload)}\0".encode("ascii")
    if (
        verify_recovery_epoch002_operational_artifact_identity(identity)
        or artifact.get("schema_version") != _ROLE_SCHEMAS[role]
        or identity.get("schema_version") != artifact.get("schema_version")
        or identity.get("logical_artifact_sha256") != artifact[hash_key]
        or identity.get("raw_sha256")
        != hashlib.sha256(payload).hexdigest()
        or identity.get("git_blob_sha1")
        != hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest()
        or identity.get("repository_full_name") != "MassyuRed/Cocolon"
        or _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is None
        or _SHA256_RE.fullmatch(str(identity.get("raw_sha256", "")))
        is None
        or state.get("postfetch_commit_sha1")
        != identity.get("publication_commit_sha1")
        or state.get("postfetch_git_blob_sha1")
        != identity.get("git_blob_sha1")
    ):
        return ("PUBLISHED_ARTIFACT_IDENTITY_MISMATCH",)
    return ()


__all__ = [
    "RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_P0_EXTERNAL_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_P0_PARENT_DESIGN_KEYS",
    "RECOVERY_EPOCH002_P0_RECEIPT_KEYS",
    "verify_recovery_epoch002_artifact_identity",
    "verify_recovery_epoch002_operational_artifact_identity",
    "verify_recovery_epoch002_p0_external_identity",
    "verify_recovery_epoch002_publication_state",
    "verify_recovery_epoch002_published_artifact",
]
