# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 002 append-only lineage reconciliation.

This module separates semantic event ancestry from Git transaction
parenthood.  It validates already-observed, body-free reconciliation state;
it does not allocate a candidate, publish an event, reserve an authority, or
run the formal worker.
"""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import PurePosixPath
import re
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch002_canonical_current_closure_v3 import (
    validate_recovery_epoch002_bootstrap_manifest,
    validate_recovery_epoch002_source_closure,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_EVENT1_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v1"
)
RECOVERY_EPOCH002_EVENT1_KEYS = _keys(
    """
    schema_version ledger_id event_id logical_cycle_id recovery_epoch_id
    candidate_version_id event_name event_ordinal state timestamp_utc
    timestamp_kind authority challenge_id source_closure prior_event
    primary_evidence_artifact publication automatic_progression body_free
    event_sha256 p0_external_identity candidate_allocation bootstrap_closure
    """
)
RECOVERY_EPOCH002_PUBLISHED_EVENT1_IDENTITY_KEYS = _keys(
    """
    identity_kind ledger_id recovery_epoch_id event_id event_name
    event_ordinal state timestamp_utc candidate_version_id event_path
    event_git_blob_sha1 event_raw_sha256 event_sha256
    publication_commit_sha1 p0_external_identity_sha256
    source_closure_sha256 bootstrap_closure_sha256 identity_sha256
    """
)
RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    d2_final_closure_sha256 d2_completion_receipt allocated_at_utc
    candidate_allocation_sha256
    """
)
RECOVERY_EPOCH002_READINESS_KEYS = _keys(
    """
    schema_version authority_token event1_challenge_id preflight_challenge_id
    preflight_id candidate_version_id logical_cycle_id recovery_epoch_id
    source_baseline_event source_closure bootstrap_closure
    python_runtime_identity pytest_distribution_identity
    dependency_lock_identity environment_profile preflight_owner_identity
    preflight_argv_sha256 loaded_plugin_manifest_sha256 readiness_state
    formal_collection_state formal_execution_state pytest_main_called
    owner_validation_state independent_verification_state
    preflight_started_at_utc preflight_finished_at_utc readiness_receipt_path
    automatic_progression body_free bootstrap_readiness_receipt_sha256
    """
)
RECOVERY_EPOCH002_RESERVATION_KEYS = _keys(
    """
    schema_version authority_token challenge_id authority_challenge_id
    attempt_id candidate_version_id logical_cycle_id recovery_epoch_id
    formal_node_registry_sha256 reservation_state reserved_at_utc
    source_baseline_event source_closure automatic_progression body_free
    formal_test_run_reservation_sha256 reservation_ordinal
    publication_base_commit_sha1 bootstrap_readiness_artifact
    prior_reservation_count prior_reservation_history
    prior_reservation_history_sha256 lineage_state event1_challenge_id
    preflight_challenge_id
    """
)
RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS = _keys(
    """
    reservation_ordinal reservation_artifact attempt_id disposition_kind
    disposition_artifact
    """
)
RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS = _keys(
    """
    schema_version candidate_version_id source_baseline_event
    successful_reservation prior_reservation_count prior_reservation_history
    prior_reservation_history_sha256 success_lineage_sha256
    """
)
RECOVERY_EPOCH002_ATTEMPT_ID_PREIMAGE_KEYS = (
    "logical_cycle_id",
    "recovery_epoch_id",
    "candidate_version_id",
    "authority_token",
    "challenge_id",
    "authority_challenge_id",
    "source_baseline_event_sha256",
    "source_baseline_event_identity_sha256",
    "canonical_current_closure_sha256",
    "source_dependency_closure_sha256",
    "proof_source_closure_sha256",
    "requirement_registry_sha256",
    "formal_node_registry_sha256",
    "bootstrap_closure_sha256",
    "bootstrap_readiness_identity_sha256",
    "preflight_challenge_id",
    "reservation_ordinal",
    "prior_reservation_history_sha256",
)
RECOVERY_EPOCH002_PREFLIGHT_ID_PREIMAGE_KEYS = (
    "logical_cycle_id",
    "recovery_epoch_id",
    "candidate_version_id",
    "authority_token",
    "event1_challenge_id",
    "preflight_challenge_id",
    "source_baseline_event_identity_sha256",
    "source_closure_sha256",
    "bootstrap_closure_sha256",
)

_RESERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_test_run_reservation.v1"
)
_ALLOWED_LINEAGE_STATES = frozenset(
    {
        "INITIAL",
        "RETRY_AFTER_PUBLISHED_FORMAL_FAILURE",
        "RETRY_AFTER_PUBLISHED_CONSUMPTION_UNKNOWN_STOP",
    }
)
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
_PRIOR_DISPOSITION_ROLES = {
    "FORMAL_FAILURE_ATTEMPT_PUBLISHED": frozenset(
        {"FORMAL_WORKER_TERMINAL_RESULT", "TERMINAL_RESULT"}
    ),
    "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED": frozenset(
        {
            "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
            "UNKNOWN_DISPOSITION",
        }
    ),
}
_P0_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id parent_design receipt
    p0_external_identity_sha256
    """
)
_P0_PARENT_DESIGN_KEYS = _keys(
    "path publication_commit_sha1 git_blob_sha1 raw_sha256"
)
_P0_RECEIPT_KEYS = _keys(
    """
    path publication_commit_sha1 git_blob_sha1 raw_sha256
    logical_receipt_sha256
    """
)
_P0_EXTERNAL_IDENTITY_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch002.p0_external_identity.v1"
)
_CANDIDATE_ALLOCATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.candidate_allocation.v1"
)
RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_ROLE = "D2_COMPLETION_RECEIPT"
RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "retry_lineage_and_formal_worker_bootstrap_oracle_correction_"
    "refreeze_and_implementation_green_receipt.v1"
)
RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
    "PostReservationRetryLineageAndFormalWorkerBootstrapCompleteness"
    "Reconciliation_OracleExact5CollisionCorrectionRefreezeAnd"
    "Implementation_GREEN_BodyFree_Receipt_20260726.json"
)
RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_KEYS = _keys(
    """
    schema_version d2_final_closure_sha256 state automatic_progression
    body_free receipt_sha256
    """
)
_P0_EXTERNAL_IDENTITY_SHA256 = (
    "0b5f4b0e3c3c023867a858782869c570e5a55c27cb72d8db108c309408581ce0"
)
_EVENT_AUTHORITY_KEYS = _keys(
    """
    approval_kind transition_authority_token publication_authority_token
    """
)
_EVENT_PUBLICATION_KEYS = _keys(
    """
    repository_full_name branch base_commit_sha1 event_path
    supporting_artifact_count supporting_artifacts
    supporting_artifact_set_sha256 expected_changed_path_count
    ref_update_mode publication_state
    """
)
_UTC_SECONDS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)


def _is_plain_int(value: Any) -> bool:
    return type(value) is int


def _utc_seconds(value: Any) -> datetime | None:
    if not isinstance(value, str) or _UTC_SECONDS_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _document_path_valid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and ".." not in path.parts
        and path.parent.as_posix()
        == "EmlisAIの実装済み資料/documents"
        and path.suffix == ".json"
    )


def _document_identity_valid(identity: Any) -> bool:
    if type(identity) is not dict or set(identity) != _EXTERNAL_IDENTITY_KEYS:
        return False
    path_text = identity.get("path")
    path = (
        PurePosixPath(path_text)
        if isinstance(path_text, str) and path_text
        else None
    )
    return (
        isinstance(identity.get("artifact_role"), str)
        and bool(identity.get("artifact_role"))
        and isinstance(identity.get("schema_version"), str)
        and bool(identity.get("schema_version"))
        and identity.get("repository_full_name") == "MassyuRed/Cocolon"
        and path is not None
        and _document_path_valid(path_text)
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


def _p0_external_identity_valid(identity: Any) -> bool:
    if type(identity) is not dict or set(identity) != _P0_EXTERNAL_IDENTITY_KEYS:
        return False
    parent = identity.get("parent_design")
    receipt = identity.get("receipt")
    if (
        identity.get("schema_version") != _P0_EXTERNAL_IDENTITY_SCHEMA
        or identity.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or identity.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or type(parent) is not dict
        or set(parent) != _P0_PARENT_DESIGN_KEYS
        or type(receipt) is not dict
        or set(receipt) != _P0_RECEIPT_KEYS
    ):
        return False
    for row in (parent, receipt):
        path = row.get("path")
        parsed = (
            PurePosixPath(path)
            if isinstance(path, str) and path
            else None
        )
        if (
            parsed is None
            or parsed.is_absolute()
            or parsed.as_posix() != path
            or ".." in parsed.parts
            or parsed.parent.as_posix()
            != "EmlisAIの実装済み資料/documents"
            or parsed.suffix not in {".md", ".json"}
            or _SHA1_RE.fullmatch(
                str(row.get("publication_commit_sha1", ""))
            )
            is None
            or _SHA1_RE.fullmatch(str(row.get("git_blob_sha1", "")))
            is None
            or _SHA256_RE.fullmatch(str(row.get("raw_sha256", "")))
            is None
        ):
            return False
    return (
        _SHA256_RE.fullmatch(
            str(receipt.get("logical_receipt_sha256", ""))
        )
        is not None
        and identity.get("p0_external_identity_sha256")
        == hashlib.sha256(
            canonical_json_bytes(
                {
                    key: value
                    for key, value in identity.items()
                    if key != "p0_external_identity_sha256"
                }
            )
            + b"\n"
        ).hexdigest()
    )


def _expected_d2_completion_receipt_sha256(
    d2_final_closure_sha256: str,
) -> str:
    return artifact_sha256(
        {
            "schema_version": (
                RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA
            ),
            "d2_final_closure_sha256": d2_final_closure_sha256,
            "state": "IMPLEMENTED_TARGETED_GREEN",
            "automatic_progression": False,
            "body_free": True,
        }
    )


def build_recovery_epoch002_d2_completion_receipt(
    *,
    d2_final_closure_sha256: str,
) -> dict[str, Any]:
    """Build the deterministic body-free receipt for the final D2 closure."""

    if _SHA256_RE.fullmatch(d2_final_closure_sha256) is None:
        raise ValueError("D2_FINAL_CLOSURE_INVALID")
    receipt: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA,
        "d2_final_closure_sha256": d2_final_closure_sha256,
        "state": "IMPLEMENTED_TARGETED_GREEN",
        "automatic_progression": False,
        "body_free": True,
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = (
        _expected_d2_completion_receipt_sha256(
            d2_final_closure_sha256
        )
    )
    return receipt


def validate_recovery_epoch002_d2_completion_receipt(
    receipt: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the deterministic receipt that closes D2."""

    closure = (
        receipt.get("d2_final_closure_sha256")
        if type(receipt) is dict
        else None
    )
    if (
        type(receipt) is not dict
        or set(receipt) != RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_KEYS
        or receipt.get("schema_version")
        != RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA
        or _SHA256_RE.fullmatch(str(closure or "")) is None
        or receipt.get("state") != "IMPLEMENTED_TARGETED_GREEN"
        or receipt.get("automatic_progression") is not False
        or receipt.get("body_free") is not True
        or receipt.get("receipt_sha256")
        != _expected_d2_completion_receipt_sha256(closure)
    ):
        return ("D2_COMPLETION_RECEIPT_INVALID",)
    return ()


def _d2_completion_receipt_identity_valid(
    identity: Any,
    *,
    d2_final_closure_sha256: Any,
) -> bool:
    """Require the one postverified D2 receipt selected by this closure."""

    return (
        _document_identity_valid(identity)
        and identity.get("artifact_role")
        == RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_ROLE
        and identity.get("schema_version")
        == RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA
        and identity.get("path")
        == RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_PATH
        and _SHA256_RE.fullmatch(str(d2_final_closure_sha256 or ""))
        is not None
        and identity.get("logical_artifact_sha256")
        == _expected_d2_completion_receipt_sha256(
            d2_final_closure_sha256
        )
    )


def _prior_history_valid(
    history: Any,
    expected_count: Any,
) -> bool:
    if type(history) is not list or not _is_plain_int(expected_count):
        return False
    if expected_count < 0 or len(history) != expected_count:
        return False
    seen_attempts: set[str] = set()
    seen_identities: set[str] = set()

    def identity_valid(
        identity: Any,
        *,
        roles: frozenset[str],
    ) -> bool:
        return (
            type(identity) is dict
            and set(identity) == _EXTERNAL_IDENTITY_KEYS
            and identity.get("artifact_role") in roles
            and isinstance(identity.get("schema_version"), str)
            and bool(identity.get("schema_version"))
            and identity.get("repository_full_name") == "MassyuRed/Cocolon"
            and isinstance(identity.get("path"), str)
            and identity.get("path", "").startswith(
                "EmlisAIの実装済み資料/documents/"
            )
            and _SHA1_RE.fullmatch(
                str(identity.get("git_blob_sha1", ""))
            )
            is not None
            and _SHA1_RE.fullmatch(
                str(identity.get("publication_commit_sha1", ""))
            )
            is not None
            and all(
                _SHA256_RE.fullmatch(str(identity.get(name, ""))) is not None
                for name in (
                    "raw_sha256",
                    "logical_artifact_sha256",
                    "identity_sha256",
                )
            )
            and identity.get("body_free") is True
            and identity.get("identity_sha256")
            == _hash_without(identity, "identity_sha256")
        )

    for expected_ordinal, row in enumerate(history, start=1):
        if type(row) is not dict:
            return False
        if set(row) != RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS:
            return False
        if row.get("reservation_ordinal") != expected_ordinal:
            return False
        if not _is_plain_int(row.get("reservation_ordinal")):
            return False
        attempt_id = row.get("attempt_id")
        disposition_kind = row.get("disposition_kind")
        disposition_roles = _PRIOR_DISPOSITION_ROLES.get(disposition_kind)
        if (
            not identity_valid(
                row.get("reservation_artifact"),
                roles=frozenset(
                    {"FORMAL_TEST_RUN_RESERVATION", "RESERVATION"}
                ),
            )
            or disposition_roles is None
            or not identity_valid(
                row.get("disposition_artifact"),
                roles=disposition_roles,
            )
            or not isinstance(attempt_id, str)
            or _SHA256_RE.fullmatch(attempt_id) is None
            or attempt_id in seen_attempts
        ):
            return False
        identities = (
            row["reservation_artifact"]["identity_sha256"],
            row["disposition_artifact"]["identity_sha256"],
        )
        if any(identity in seen_identities for identity in identities):
            return False
        seen_attempts.add(attempt_id)
        seen_identities.update(identities)
    return True


def build_recovery_epoch002_attempt_id_preimage(
    reservation: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Return the canonical attempt preimage, or ``None`` when incomplete."""

    try:
        event = reservation["source_baseline_event"]
        closure = reservation["source_closure"]
        readiness = reservation["bootstrap_readiness_artifact"]
        preimage = {
            "logical_cycle_id": reservation["logical_cycle_id"],
            "recovery_epoch_id": reservation["recovery_epoch_id"],
            "candidate_version_id": reservation["candidate_version_id"],
            "authority_token": reservation["authority_token"],
            "challenge_id": reservation["challenge_id"],
            "authority_challenge_id": reservation[
                "authority_challenge_id"
            ],
            "source_baseline_event_sha256": event[
                "logical_artifact_sha256"
            ],
            "source_baseline_event_identity_sha256": event[
                "identity_sha256"
            ],
            "canonical_current_closure_sha256": closure[
                "canonical_current_closure_sha256"
            ],
            "source_dependency_closure_sha256": closure[
                "source_dependency_closure_sha256"
            ],
            "proof_source_closure_sha256": closure[
                "proof_source_closure_sha256"
            ],
            "requirement_registry_sha256": closure[
                "requirement_registry_sha256"
            ],
            "formal_node_registry_sha256": closure[
                "formal_node_registry_sha256"
            ],
            "bootstrap_closure_sha256": closure[
                "bootstrap_closure_sha256"
            ],
            "bootstrap_readiness_identity_sha256": readiness[
                "identity_sha256"
            ],
            "preflight_challenge_id": reservation[
                "preflight_challenge_id"
            ],
            "reservation_ordinal": reservation["reservation_ordinal"],
            "prior_reservation_history_sha256": reservation[
                "prior_reservation_history_sha256"
            ],
        }
    except (KeyError, TypeError):
        return None
    if tuple(preimage) != RECOVERY_EPOCH002_ATTEMPT_ID_PREIMAGE_KEYS:
        return None
    return preimage


def validate_recovery_epoch002_event1_artifact(
    event: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the body-free Epoch002 source-baseline event1."""

    if (
        type(event) is not dict
        or set(event) != RECOVERY_EPOCH002_EVENT1_KEYS
        or event.get("schema_version") != RECOVERY_EPOCH002_EVENT1_SCHEMA
        or event.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or event.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or event.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or event.get("state") != "SOURCE_BASELINE_LOCKED"
        or event.get("event_ordinal") != 1
        or type(event.get("event_ordinal")) is not int
        or not isinstance(event.get("ledger_id"), str)
        or not event.get("ledger_id")
        or not isinstance(event.get("event_id"), str)
        or not event.get("event_id")
        or not isinstance(event.get("candidate_version_id"), str)
        or not event.get("candidate_version_id")
        or event.get("candidate_version_id") == "nls_v3_rc_0034"
        or _utc_seconds(event.get("timestamp_utc")) is None
        or event.get("timestamp_kind")
        != "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE"
        or _SHA256_RE.fullmatch(str(event.get("challenge_id", "")))
        is None
        or type(event.get("authority")) is not dict
        or validate_recovery_epoch002_source_closure(
            event.get("source_closure")
        )
        or not _document_identity_valid(
            event.get("primary_evidence_artifact")
        )
        or type(event.get("publication")) is not dict
        or event.get("automatic_progression") is not False
        or event.get("body_free") is not True
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
    ):
        return ("SOURCE_BASELINE_EVENT_INVALID",)
    source_closure = event["source_closure"]
    bootstrap = event.get("bootstrap_closure")
    allocation = event.get("candidate_allocation")
    p0_identity = event.get("p0_external_identity")
    authority = event["authority"]
    publication = event["publication"]
    event_timestamp = _utc_seconds(event["timestamp_utc"])
    allocation_timestamp = (
        _utc_seconds(allocation.get("allocated_at_utc"))
        if type(allocation) is dict
        else None
    )
    if (
        set(authority) != _EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind")
        != "EXPLICIT_SEPARATE_APPROVAL"
        or not isinstance(
            authority.get("transition_authority_token"),
            str,
        )
        or not authority.get("transition_authority_token")
        or authority.get("transition_authority_token")
        != authority.get("publication_authority_token")
        or set(publication) != _EVENT_PUBLICATION_KEYS
        or publication.get("repository_full_name") != "MassyuRed/Cocolon"
        or publication.get("branch") != "main"
        or _SHA1_RE.fullmatch(
            str(publication.get("base_commit_sha1", ""))
        )
        is None
        or not isinstance(publication.get("event_path"), str)
        or not _document_path_valid(publication.get("event_path"))
        or type(publication.get("supporting_artifacts")) is not list
        or any(
            not _document_identity_valid(identity)
            for identity in publication.get("supporting_artifacts", [])
        )
        or publication.get("supporting_artifacts")
        != sorted(
            publication.get("supporting_artifacts", []),
            key=lambda identity: identity["path"],
        )
        or len(
            {
                identity["identity_sha256"]
                for identity in publication.get(
                    "supporting_artifacts",
                    [],
                )
            }
        )
        != len(publication.get("supporting_artifacts", []))
        or event.get("primary_evidence_artifact")
        not in publication.get("supporting_artifacts", [])
        or publication.get("supporting_artifact_count")
        != len(publication.get("supporting_artifacts", []))
        or publication.get("supporting_artifact_set_sha256")
        != artifact_sha256(publication.get("supporting_artifacts", []))
        or publication.get("expected_changed_path_count") != 1
        or publication.get("ref_update_mode")
        != "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
        or publication.get("publication_state")
        != "PUBLISHED_ATOMIC"
        or validate_recovery_epoch002_bootstrap_manifest(bootstrap)
        or source_closure.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or type(allocation) is not dict
        or set(allocation) != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_KEYS
        or allocation.get("schema_version")
        != _CANDIDATE_ALLOCATION_SCHEMA
        or allocation.get("logical_cycle_id")
        != event.get("logical_cycle_id")
        or allocation.get("recovery_epoch_id")
        != event.get("recovery_epoch_id")
        or allocation.get("candidate_version_id")
        != event.get("candidate_version_id")
        or allocation.get("d2_final_closure_sha256")
        != source_closure.get("d2_final_closure_sha256")
        or not _d2_completion_receipt_identity_valid(
            allocation.get("d2_completion_receipt"),
            d2_final_closure_sha256=allocation.get(
                "d2_final_closure_sha256"
            ),
        )
        or event.get("primary_evidence_artifact")
        != allocation.get("d2_completion_receipt")
        or allocation_timestamp is None
        or event_timestamp is None
        or allocation_timestamp > event_timestamp
        or allocation.get("candidate_allocation_sha256")
        != _hash_without(allocation, "candidate_allocation_sha256")
        or not _p0_external_identity_valid(p0_identity)
        or p0_identity.get("p0_external_identity_sha256")
        != _P0_EXTERNAL_IDENTITY_SHA256
        or event.get("prior_event") != p0_identity
    ):
        return ("SOURCE_BASELINE_EVENT_INVALID",)
    return ()


def validate_recovery_epoch002_reservation_artifact(
    reservation: Mapping[str, Any],
) -> tuple[str, ...]:
    """Strictly validate the additive reservation record itself."""

    if type(reservation) is not dict:
        return ("RUN_RESERVATION_INVALID",)
    if set(reservation) != RECOVERY_EPOCH002_RESERVATION_KEYS:
        return ("RUN_RESERVATION_INVALID",)
    if reservation.get("schema_version") != _RESERVATION_SCHEMA:
        return ("RUN_RESERVATION_INVALID",)
    source_event = reservation.get("source_baseline_event")
    source_closure = reservation.get("source_closure")
    readiness_identity = reservation.get("bootstrap_readiness_artifact")
    candidate = reservation.get("candidate_version_id")
    challenges = (
        reservation.get("event1_challenge_id"),
        reservation.get("preflight_challenge_id"),
        reservation.get("challenge_id"),
    )
    if (
        reservation.get("reservation_state")
        != "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN"
        or reservation.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or reservation.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not isinstance(candidate, str)
        or not candidate
        or candidate == "nls_v3_rc_0034"
        or not isinstance(reservation.get("authority_token"), str)
        or not reservation.get("authority_token")
        or any(
            not isinstance(value, str)
            or _SHA256_RE.fullmatch(value) is None
            for value in challenges
        )
        or len(set(challenges)) != len(challenges)
        or not isinstance(reservation.get("reserved_at_utc"), str)
        or not reservation.get("reserved_at_utc")
        or _SHA1_RE.fullmatch(
            str(reservation.get("publication_base_commit_sha1", ""))
        )
        is None
        or type(source_event) is not dict
        or type(source_closure) is not dict
        or type(readiness_identity) is not dict
        or _SHA256_RE.fullmatch(
            str(source_event.get("logical_artifact_sha256", ""))
        )
        is None
        or _SHA256_RE.fullmatch(
            str(source_event.get("identity_sha256", ""))
        )
        is None
        or _SHA256_RE.fullmatch(
            str(readiness_identity.get("identity_sha256", ""))
        )
        is None
        or reservation.get("formal_node_registry_sha256")
        != source_closure.get("formal_node_registry_sha256")
        or _SHA256_RE.fullmatch(
            str(reservation.get("formal_node_registry_sha256", ""))
        )
        is None
    ):
        return ("RUN_RESERVATION_INVALID",)
    ordinal = reservation.get("reservation_ordinal")
    count = reservation.get("prior_reservation_count")
    history = reservation.get("prior_reservation_history")
    if (
        not _is_plain_int(ordinal)
        or not _is_plain_int(count)
        or ordinal <= 0
        or count < 0
        or ordinal != count + 1
        or not _prior_history_valid(history, count)
    ):
        return ("RUN_RESERVATION_INVALID",)
    expected_history_hash = artifact_sha256(
        {"prior_reservation_history": history}
    )
    if (
        reservation.get("prior_reservation_history_sha256")
        != expected_history_hash
    ):
        return ("RUN_RESERVATION_INVALID",)
    if reservation.get("lineage_state") not in _ALLOWED_LINEAGE_STATES:
        return ("RUN_RESERVATION_INVALID",)
    authority_challenge = artifact_sha256(
        {
            "authority_token": reservation.get("authority_token"),
            "challenge_id": reservation.get("challenge_id"),
        }
    )
    if reservation.get("authority_challenge_id") != authority_challenge:
        return ("RUN_RESERVATION_INVALID",)
    preimage = build_recovery_epoch002_attempt_id_preimage(reservation)
    if preimage is None:
        return ("RUN_RESERVATION_INVALID",)
    if reservation.get("attempt_id") != artifact_sha256(preimage):
        return ("RUN_RESERVATION_INVALID",)
    if (
        reservation.get("formal_test_run_reservation_sha256")
        != _hash_without(
            reservation,
            "formal_test_run_reservation_sha256",
        )
    ):
        return ("RUN_RESERVATION_INVALID",)
    if reservation.get("automatic_progression") is not False:
        return ("RUN_RESERVATION_INVALID",)
    if reservation.get("body_free") is not True:
        return ("RUN_RESERVATION_INVALID",)
    return ()


def _candidate_boundary_issue(state: Mapping[str, Any]) -> bool:
    reservation = state.get("reservation")
    if not isinstance(reservation, Mapping):
        return False
    candidate = reservation.get("candidate_version_id")
    return (
        not isinstance(candidate, str)
        or not candidate
        or candidate == "nls_v3_rc_0034"
        or state.get("inherits_epoch001_acceptance_credit") is not False
    )


def _reservation_transaction_parent_invalid(
    state: Mapping[str, Any],
) -> bool:
    current_head = state.get("current_head_sha1")
    return (
        state.get("publication_parent_commit_sha1") != current_head
        or state.get("publication_parent_count") != 1
        or state.get("expected_old_sha1") != current_head
        or state.get("observed_old_sha1") != current_head
    )


def _readiness_lineage_invalid(dispositions: Any) -> bool:
    if type(dispositions) is not list:
        return True
    if any(
        item in {"UNRESOLVED", "MISSING", "CONFLICTING"}
        for item in dispositions
    ):
        return False
    if any("REUSED" in str(item) for item in dispositions):
        return True
    unused = [
        item
        for item in dispositions
        if item == "READY_UNUSED_AUTHORITY_STOP_PUBLISHED"
    ]
    if unused and len(dispositions) != 1:
        return True
    return False


def validate_recovery_epoch002_lineage_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Reconcile body-free lineage observations with fail-closed precedence."""

    if type(state) is not dict:
        return ("RESERVATION_LINEAGE_INVALID",)
    reservation = state.get("reservation")
    if not isinstance(reservation, Mapping):
        return ("RUN_RESERVATION_INVALID",)

    # A historical Epoch001 candidate conflict is more specific than the
    # derived reservation hash drift it necessarily causes.
    if _candidate_boundary_issue(state):
        return ("EPOCH002_RELEASE_CANDIDATE_BOUNDARY_CONFLICT_STOP",)
    if state.get("candidate_allocated_after_d2_postverification") is not True:
        return ("SOURCE_BASELINE_PUBLICATION_FORBIDDEN",)
    if _reservation_transaction_parent_invalid(state):
        return ("RESERVATION_TRANSACTION_PARENT_POLICY_INVALID",)
    if state.get("event1_ancestor_of_current_head") is not True:
        return ("EVENT1_ANCESTRY_INVALID",)
    if state.get("event1_count") != 1:
        return ("DUPLICATE_EVENT1",)

    challenges = (
        state.get("event1_challenge_id"),
        state.get("preflight_challenge_id"),
        state.get("formal_run_challenge_id"),
    )
    if any(not isinstance(value, str) for value in challenges):
        return ("PHASE_CHALLENGE_COLLISION",)
    if len(set(challenges)) != len(challenges):
        return ("PHASE_CHALLENGE_COLLISION",)

    if state.get("success_event2_published") is True:
        return ("SUCCESS_ALREADY_PUBLISHED",)
    if (
        state.get("prior_reservation_unresolved") is True
        or state.get("result_publication_pending") is True
    ):
        return ("NEW_RESERVATION_FORBIDDEN",)
    if state.get("identity_reuse_detected") is True:
        return ("REPLAY_FORBIDDEN",)

    published = state.get("published_reservations")
    declared = state.get("declared_prior_reservation_history")
    reservation_history = reservation.get("prior_reservation_history")
    if (
        type(published) is not list
        or declared != published
        or published != reservation_history
    ):
        return ("RESERVATION_LINEAGE_INVALID",)

    dispositions = state.get("earlier_ready_dispositions")
    if type(dispositions) is not list or any(
        item in {"UNRESOLVED", "MISSING", "CONFLICTING"}
        for item in dispositions
    ):
        return ("NEXT_PREFLIGHT_AND_RESERVATION_FORBIDDEN",)
    if _readiness_lineage_invalid(dispositions):
        return ("READINESS_LINEAGE_INVALID",)

    reservation_issues = validate_recovery_epoch002_reservation_artifact(
        reservation
    )
    if reservation_issues:
        return reservation_issues

    reservation_source_closure = reservation.get("source_closure")
    if type(reservation_source_closure) is not dict:
        return ("RUN_RESERVATION_INVALID",)
    source_closure = artifact_sha256(reservation_source_closure)
    if (
        state.get("source_closure_sha256") != source_closure
        or state.get("event1_source_closure_sha256") != source_closure
        or state.get("readiness_source_closure_sha256") != source_closure
    ):
        return ("READY_TO_RESERVATION_DRIFT_STOP",)
    if state.get("child_source_closure_sha256") != source_closure:
        if state.get("reservation_consumed") is True:
            return ("ATTEMPT_CONSUMPTION_UNKNOWN_STOP",)
        return ("READY_TO_RESERVATION_DRIFT_STOP",)

    candidate = reservation.get("candidate_version_id")
    candidate_values = (
        state.get("event1_candidate_version_id"),
        state.get("readiness_candidate_version_id"),
        candidate,
        state.get("result_candidate_version_id"),
        state.get("accepted_candidate_version_id"),
    )
    if any(value != candidate for value in candidate_values):
        return ("CANDIDATE_LINEAGE_INVALID",)
    expected_history_sha256 = artifact_sha256(
        {"prior_reservation_history": reservation_history}
    )
    if (
        state.get("success_lineage_history_sha256")
        != expected_history_sha256
        or state.get("accepted_lineage_history_sha256")
        != expected_history_sha256
    ):
        return ("SUCCESS_LINEAGE_INVALID",)
    return ()


__all__ = [
    "RECOVERY_EPOCH002_EVENT1_SCHEMA",
    "RECOVERY_EPOCH002_EVENT1_KEYS",
    "RECOVERY_EPOCH002_PUBLISHED_EVENT1_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_KEYS",
    "RECOVERY_EPOCH002_READINESS_KEYS",
    "RECOVERY_EPOCH002_RESERVATION_KEYS",
    "RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS",
    "RECOVERY_EPOCH002_ATTEMPT_ID_PREIMAGE_KEYS",
    "RECOVERY_EPOCH002_PREFLIGHT_ID_PREIMAGE_KEYS",
    "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_ROLE",
    "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA",
    "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_PATH",
    "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_KEYS",
    "build_recovery_epoch002_attempt_id_preimage",
    "build_recovery_epoch002_d2_completion_receipt",
    "validate_recovery_epoch002_d2_completion_receipt",
    "validate_recovery_epoch002_event1_artifact",
    "validate_recovery_epoch002_reservation_artifact",
    "validate_recovery_epoch002_lineage_state",
]
