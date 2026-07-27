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
    RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS,
    RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA,
    RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS,
    validate_recovery_epoch002_bootstrap_manifest,
    validate_recovery_epoch002_source_closure,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT = (
    "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
)


_SUCCESS_FORBIDDEN_STATE_KEYS = frozenset(
    {
        "stdout",
        "stderr",
        "traceback",
        "exception_message",
        "free_form_reason",
        "raw_environment",
        "absolute_temporary_path",
        "pid",
        "hostname",
        "raw_body",
        "raw_payload",
        "generated_body",
        "private_body",
        "private_payload",
        "prompt_text",
        "response_text",
        "private_review_data",
        "secret",
        "credential",
        "invalid_result_sha256",
    }
)


def _success_contains_forbidden_state_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _SUCCESS_FORBIDDEN_STATE_KEYS for key in value
        ) or any(
            _success_contains_forbidden_state_key(item)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(
            _success_contains_forbidden_state_key(item) for item in value
        )
    return False


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
RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v2"
)
RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS = RECOVERY_EPOCH002_EVENT1_KEYS
RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS = _keys(
    """
    approval_kind transition_authority_token publication_authority_token
    operational_admission
    """
)
RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS = _keys(
    """
    repository_full_name branch base_commit_sha1 event_path
    supporting_artifact_count supporting_artifacts
    supporting_artifact_set_sha256 expected_changed_path_count
    ref_update_mode publication_state transaction_capability
    """
)
RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_OPTIONAL_KEYS = _keys(
    "ref_update_mode transaction_capability"
)
RECOVERY_EPOCH002_TRANSACTION_CAPABILITY_KEYS = _keys(
    """
    schema_version provider_class provider_identity_sha256
    repository_full_name source_ref base_commit_sha1
    expected_changed_path_count authoritative_ref_read
    expected_old_compare_and_swap commit_parent_tree_and_recursive_read
    full_changed_and_unchanged_postfetch_verification challenge_id
    operational_admission_identity_sha256 observed_at_utc
    transaction_capability_sha256
    """
)
_SUCCESS_PATHS = (
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
RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS = tuple(
    sorted(_SUCCESS_PATHS[:14])
)
RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS = tuple(sorted(_SUCCESS_PATHS))
RECOVERY_EPOCH002_SUCCESSOR_SUCCESSION_STATE_KEYS = _keys(
    """
    reflection_contract_version
    bootstrap_closure candidate_allocation candidate_operational_identity
    causal_red_evidence causal_red_evidence_artifact
    causal_red_postfetch_evidence combined_green_evidence
    combined_green_evidence_artifact combined_green_postfetch_evidence
    event1 event1_publication operational_admission_publication
    operational_admission_receipt parent_addendum_external_identity
    parent_addendum_postfetch_evidence successor_completion_publication
    successor_completion_receipt successor_source_closure
    """
)
RECOVERY_EPOCH002_SUCCESS_EVENT2_STATE_KEYS = _keys(
    """
    reflection_contract_version
    artifacts_by_path atomic_publication_manifest
    candidate_identities_by_path event2 postfetch_observation
    publication_transaction terminal_commit_observation
    """
)
_SUCCESS_ARTIFACT_CONTRACT_BY_PATH = {
    _SUCCESS_PATHS[0]: (
        "ACCEPTED_TEST_RUN_RECEIPT",
        "accepted_test_run_receipt_sha256",
    ),
    **{
        _SUCCESS_PATHS[step + 1]: (
            "CURRENT_STEP_COMPLETION_RECEIPT",
            "receipt_sha256",
        )
        for step in range(11)
    },
    _SUCCESS_PATHS[12]: (
        "ALL11_COMPLETION_CHAIN",
        "all11_completion_chain_sha256",
    ),
    _SUCCESS_PATHS[13]: (
        "ALL11_ATOMIC_PUBLICATION_MANIFEST",
        "atomic_publication_manifest_sha256",
    ),
    _SUCCESS_PATHS[14]: ("SEQUENCE_EVENT_2", "event_sha256"),
}
RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_completion_receipt.v1"
)
RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id
    historical_d2_final_closure_sha256
    historical_d2_completion_receipt_identity_sha256
    parent_addendum_external_identity_sha256
    successor_source_closure_sha256 causal_red_evidence_sha256
    combined_green_evidence_sha256 state automatic_progression body_free
    receipt_sha256
    """
)
RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorCompletion_BodyFree_Receipt_20260726.json"
)
RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.candidate_allocation.v2"
)
RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    historical_d2_final_closure_sha256 historical_d2_completion_receipt
    successor_source_closure_sha256 successor_completion_receipt
    allocated_at_utc candidate_allocation_sha256
    """
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "p1_operational_admission_receipt.v1"
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id
    successor_completion_receipt successor_source_closure_sha256
    repository_full_name source_ref authority challenge_id scope
    transport_capability durable_store_capability owner_validation_state
    independent_verification_state issued_at_utc expires_at_utc state
    automatic_progression body_free operational_admission_sha256
    """
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_OPTIONAL_KEYS = _keys(
    "transport_capability durable_store_capability"
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_OPERATION_SET = (
    "OPERATIONAL_ADMISSION_PUBLICATION",
    "SOURCE_BASELINE_EVENT1_PUBLICATION",
    "BOOTSTRAP_READINESS_PUBLICATION",
    "FORMAL_RESERVATION_PUBLICATION",
    "PARENT_SPAWN_INTENT_PERSISTENCE",
    "FORMAL_ATTEMPT_WRITE_ONCE_CLAIM",
    "FORMAL_EXACT134_SINGLE_INVOCATION",
    "CHECKPOINT_DURABLE_WRITE",
    "TERMINAL_DURABLE_WRITE_AND_RECOVERY",
    "TERMINAL_DISPOSITION_PUBLICATION",
    "SUCCESS_EXACT15_PUBLICATION",
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_AUTHORITY_KEYS = _keys(
    """
    approval_kind admission_authority_token publication_authority_token
    authority_sha256
    """
)
RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCOPE_KEYS = _keys(
    """
    repository_full_name source_ref successor_source_closure_sha256
    operation_set scope_sha256
    """
)
RECOVERY_EPOCH002_TRANSPORT_CAPABILITY_KEYS = _keys(
    """
    schema_version provider_class provider_identity_sha256
    authoritative_ref_read expected_old_compare_and_swap
    commit_parent_tree_read recursive_tree_read
    exact_changed_path_verification complete_unchanged_path_verification
    full_postfetch_verification scope_sha256 challenge_id observed_at_utc
    transport_capability_sha256
    """
)
RECOVERY_EPOCH002_DURABLE_STORE_CAPABILITY_KEYS = _keys(
    """
    schema_version provider_class provider_identity_sha256
    owner_only_permissions no_symlink_following
    same_directory_temporary_write atomic_write_replace
    file_and_directory_fsync write_once_attempt_claim
    session_interruption_survival exact_terminal_recovery_read
    body_free_retention_contract scope_sha256 challenge_id observed_at_utc
    durable_store_capability_sha256
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
    """Validate the markerless historical Epoch002 source-baseline event1.

    HISTORICAL_NON_NORMATIVE: transport fields are checked only because they
    are immutable bytes of the already-issued Event1 record.  They do not
    define the current GitHub reflection contract.
    """

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
    if (
        state.get("reflection_contract_version")
        == RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
    ):
        return (
            state.get("changed_paths") != state.get("expected_changed_paths")
            or state.get("postverified") is not True
        )
    # HISTORICAL_NON_NORMATIVE: markerless D1 evidence retains its recorded
    # direct-parent/expected-old validation without governing current writes.
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


_SUCCESS_CANDIDATE_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 body_free
    """
)
_SUCCESS_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
_SUCCESS_EXACT1_KEYS = _keys(
    """
    reflection_contract_version artifact identity changed_paths
    parent_commit_sha1s expected_old_sha1 observed_old_sha1
    postfetch_evidence postfetch_state
    """
)
_SUCCESS_POSTFETCH_KEYS = _keys(
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
    """
)
_SUCCESS_POSTFETCH_ARTIFACT_KEYS = _keys(
    "path git_blob_sha1 raw_sha256 logical_artifact_sha256 body_free"
)
_SUCCESS_UNCHANGED_KEYS = _keys(
    "scope mode_type_sha_complete mismatches observation_sha256"
)
_SUCCESS_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_P1OperationalAdmission_"
    "BodyFree_Receipt_20260726.json"
)
_SUCCESS_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_SequenceEvent01_"
    "SourceBaselineLocked_BodyFree_Event_20260726.json"
)
_SUCCESS_PARENT_IDENTITY = {
    "artifact_role": RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE,
    "schema_version": RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA,
    "repository_full_name": "MassyuRed/Cocolon",
    "path": RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH,
    "git_blob_sha1": "06972af95e59daf953e3ef059ba38a3d4a295f42",
    "raw_sha256": (
        "b81a9956a6419d1bdb1cb9440569f151da2aeb22230c72ee774944d6aefdc6e8"
    ),
    "logical_artifact_sha256": (
        "913058df480e113f949185d874ed48ddfddb21b36773c5ec5d77771aba3873ac"
    ),
    "publication_commit_sha1": "462c933a597233b111962bb2e8ac41f0182dac12",
    "body_free": True,
    "identity_sha256": RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256,
}
_SUCCESS_D2_IDENTITY = {
    "artifact_role": "D2_COMPLETION_RECEIPT",
    "schema_version": RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA,
    "repository_full_name": "MassyuRed/Cocolon",
    "path": RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_PATH,
    "git_blob_sha1": "d93f7e63e8a941a15f11cfdc088a8613af041e41",
    "raw_sha256": (
        "fd68f2f241fcb959def548cd2b6d8cb475415a4466c81363bfceef2ca3ac27a1"
    ),
    "logical_artifact_sha256": (
        "0af065a6499ff99164d206f6fddafafaa91f3436de191f20078e6c4aa858253c"
    ),
    "publication_commit_sha1": "8d26f3344be8b1e6a4661f958d8279a6236191d1",
    "body_free": True,
    "identity_sha256": "",
}
_SUCCESS_D2_IDENTITY["identity_sha256"] = _hash_without(
    _SUCCESS_D2_IDENTITY,
    "identity_sha256",
)


def _success_identity_for_artifact(
    artifact: Any,
    identity: Any,
    *,
    role: str,
    path: str,
    logical_hash_key: str,
) -> bool:
    if (
        type(artifact) is not dict
        or type(identity) is not dict
        or set(identity) != _SUCCESS_EXTERNAL_IDENTITY_KEYS
        or _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is None
        or artifact.get("body_free") is not True
        or artifact.get(logical_hash_key)
        != _hash_without(artifact, logical_hash_key)
    ):
        return False
    payload = canonical_json_bytes(dict(artifact)) + b"\n"
    header = f"blob {len(payload)}\0".encode("ascii")
    expected = {
        "artifact_role": role,
        "schema_version": artifact.get("schema_version"),
        "repository_full_name": "MassyuRed/Cocolon",
        "path": path,
        "git_blob_sha1": hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest(),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "logical_artifact_sha256": artifact.get(logical_hash_key),
        "publication_commit_sha1": identity.get(
            "publication_commit_sha1"
        ),
        "body_free": True,
        "identity_sha256": "",
    }
    expected["identity_sha256"] = _hash_without(
        expected,
        "identity_sha256",
    )
    return identity == expected


def _success_candidate_for_artifact(
    artifact: Any,
    *,
    role: str,
    path: str,
    logical_hash_key: str,
) -> dict[str, Any] | None:
    if (
        type(artifact) is not dict
        or artifact.get("body_free") is not True
        or artifact.get(logical_hash_key)
        != _hash_without(artifact, logical_hash_key)
    ):
        return None
    payload = canonical_json_bytes(dict(artifact)) + b"\n"
    header = f"blob {len(payload)}\0".encode("ascii")
    return {
        "artifact_role": role,
        "schema_version": artifact.get("schema_version"),
        "repository_full_name": "MassyuRed/Cocolon",
        "path": path,
        "git_blob_sha1": hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest(),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "logical_artifact_sha256": artifact.get(logical_hash_key),
        "body_free": True,
    }


def _success_postfetch_valid(
    evidence: Any,
    identity: Mapping[str, Any],
) -> bool:
    if (
        type(evidence) is not dict
        or not {
            "repository_full_name",
            "verification_ref",
            "verification_commit_sha1",
            "publication_commit_sha1",
            "publication_changed_paths",
            "target_absent_at_base",
            "authoritative_ref_read",
            "authoritative_head_read",
            "artifact_at_publication",
            "artifact_at_verification_ref",
            "owner_issue_codes",
            "independent_issue_codes",
            "postfetch_state",
        }.issubset(evidence)
        or not set(evidence).issubset(_SUCCESS_POSTFETCH_KEYS)
        or type(identity) is not dict
        or _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is None
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
        evidence.get("repository_full_name") == "MassyuRed/Cocolon"
        and evidence.get("verification_ref") == "refs/heads/main"
        and _SHA1_RE.fullmatch(
            str(evidence.get("verification_commit_sha1", ""))
        )
        is not None
        and evidence.get("authoritative_ref_read") is True
        and evidence.get("authoritative_head_read") is True
        and evidence.get("publication_commit_sha1")
        == identity.get("publication_commit_sha1")
        and evidence.get("publication_changed_paths")
        == [identity.get("path")]
        and evidence.get("target_absent_at_base") is True
        and type(evidence.get("artifact_at_publication")) is dict
        and set(evidence["artifact_at_publication"])
        == _SUCCESS_POSTFETCH_ARTIFACT_KEYS
        and evidence["artifact_at_publication"] == artifact
        and type(evidence.get("artifact_at_verification_ref")) is dict
        and set(evidence["artifact_at_verification_ref"])
        == _SUCCESS_POSTFETCH_ARTIFACT_KEYS
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
    logical_hash_key: str,
) -> bool:
    if (
        type(publication) is not dict
        or not {
            "reflection_contract_version",
            "artifact",
            "identity",
            "changed_paths",
            "postfetch_evidence",
            "postfetch_state",
        }.issubset(publication)
        or not set(publication).issubset(_SUCCESS_EXACT1_KEYS)
        or publication.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        or publication.get("changed_paths") != [path]
        or publication.get("postfetch_state") != "POSTVERIFIED"
        or not _success_identity_for_artifact(
            publication.get("artifact"),
            publication.get("identity"),
            role=role,
            path=path,
            logical_hash_key=logical_hash_key,
        )
        or not _success_postfetch_valid(
            publication.get("postfetch_evidence"),
            publication["identity"],
        )
    ):
        return False
    return True


def _current_transaction_capability_valid(
    transaction: Any,
    *,
    expected_changed_path_count: int,
    challenge_id: Any,
) -> bool:
    """Treat transport capability data as optional diagnostic metadata."""

    if transaction is None:
        return True
    return (
        type(transaction) is dict
        and set(transaction).issubset(RECOVERY_EPOCH002_TRANSACTION_CAPABILITY_KEYS)
        and transaction.get("repository_full_name") == "MassyuRed/Cocolon"
        and transaction.get("source_ref") == "refs/heads/main"
        and transaction.get("expected_changed_path_count")
        == expected_changed_path_count
        and transaction.get("challenge_id") == challenge_id
        and (
            "transaction_capability_sha256" not in transaction
            or transaction.get("transaction_capability_sha256")
            == _hash_without(transaction, "transaction_capability_sha256")
        )
    )


def _success_parent_binding_valid(state: Mapping[str, Any]) -> bool:
    identity = state.get("parent_addendum_external_identity")
    evidence = state.get("parent_addendum_postfetch_evidence")
    completion = state.get("successor_completion_receipt")
    event = state.get("event1")
    event_source_closure = (
        event.get("source_closure") if type(event) is dict else None
    )
    event_publication = (
        event.get("publication") if type(event) is dict else None
    )
    event_supporting = (
        event_publication.get("supporting_artifacts")
        if type(event_publication) is dict
        else None
    )
    receipt = (
        evidence.get("receipt_at_publication")
        if type(evidence) is dict
        else None
    )
    markdown = (
        evidence.get("markdown_at_publication")
        if type(evidence) is dict
        else None
    )
    return (
        identity == _SUCCESS_PARENT_IDENTITY
        and type(completion) is dict
        and completion.get("parent_addendum_external_identity_sha256")
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        and type(event) is dict
        and "parent_addendum_external_identity_sha256" not in event
        and type(event_source_closure) is dict
        and event_source_closure.get(
            "parent_addendum_external_identity_sha256"
        )
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        and type(event_supporting) is list
        and not (
            len(event_supporting) > 1
            and _SUCCESS_PARENT_IDENTITY in event_supporting
        )
        and type(evidence) is dict
        and evidence.get("repository_full_name") == "MassyuRed/Cocolon"
        and evidence.get("verification_ref") == "refs/heads/main"
        and evidence.get("verification_commit_kind")
        == "FRESH_AUTHORITY_REF_OBSERVATION"
        and evidence.get("authoritative_ref_read") is True
        and evidence.get("publication_commit_sha1")
        == _SUCCESS_PARENT_IDENTITY["publication_commit_sha1"]
        and evidence.get("publication_reachable_from_verification_ref")
        is True
        and evidence.get("publication_parent_commit_sha1s")
        == ["2c3fc3d3b29365b073ee228c0ac536d4ffc3cffc"]
        and evidence.get("publication_changed_paths")
        == list(RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS)
        and evidence.get("receipt_absent_at_base") is True
        and type(receipt) is dict
        and receipt.get("git_blob_sha1")
        == _SUCCESS_PARENT_IDENTITY["git_blob_sha1"]
        and receipt.get("raw_sha256")
        == _SUCCESS_PARENT_IDENTITY["raw_sha256"]
        and receipt.get("trailing_lf_count") == 1
        and receipt.get("schema_version")
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA
        and receipt.get("body_free") is True
        and receipt.get("automatic_progression") is False
        and receipt.get("state")
        == (
            "RECOVERY_EPOCH002_POST_D2_SOURCE_BASELINE_ELIGIBILITY_"
            "SUCCESSION_PARENT_ADDENDUM_DESIGN_FROZEN_AUTHORITY_STOP"
        )
        and receipt.get("logical_artifact_sha256")
        == _SUCCESS_PARENT_IDENTITY["logical_artifact_sha256"]
        and receipt.get("bound_markdown_path")
        == (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
            "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
            "ParentAddendum_ReadOnly_20260726.md"
        )
        and receipt.get("bound_markdown_raw_sha256")
        == "10ecd8dfb549c514c0fca2f9bd7c0bde225feb5eabc1100a13375187c6ef7300"
        and type(markdown) is dict
        and markdown.get("git_blob_sha1")
        == "8016eeb3e2731dc837423e48497d424b01ab34d4"
        and markdown.get("raw_sha256")
        == "10ecd8dfb549c514c0fca2f9bd7c0bde225feb5eabc1100a13375187c6ef7300"
        and evidence.get("receipt_at_verification_ref") == receipt
        and evidence.get("markdown_at_verification_ref") == markdown
        and evidence.get("parent_addendum_external_identity") == identity
        and evidence.get("owner_issue_codes") == []
        and evidence.get("independent_issue_codes") == []
        and evidence.get("postfetch_state") == "POSTVERIFIED"
    )


def validate_recovery_epoch002_successor_completion_receipt(
    receipt: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the self-contained exact13 successor-completion receipt."""

    if (
        type(receipt) is not dict
        or set(receipt) != RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_KEYS
        or receipt.get("schema_version")
        != RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA
        or receipt.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or receipt.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or receipt.get("historical_d2_final_closure_sha256")
        != (
            "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
        )
        or receipt.get(
            "historical_d2_completion_receipt_identity_sha256"
        )
        != _SUCCESS_D2_IDENTITY["identity_sha256"]
        or receipt.get("parent_addendum_external_identity_sha256")
        != RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        or any(
            _SHA256_RE.fullmatch(str(receipt.get(key, ""))) is None
            for key in (
                "successor_source_closure_sha256",
                "causal_red_evidence_sha256",
                "combined_green_evidence_sha256",
            )
        )
        or receipt.get("state")
        != "SUCCESSOR_SOURCE_BASELINE_ELIGIBILITY_PROVED"
        or receipt.get("automatic_progression") is not False
        or receipt.get("body_free") is not True
        or receipt.get("receipt_sha256")
        != _hash_without(receipt, "receipt_sha256")
    ):
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    return ()


def _success_completion_evidence_valid(
    state: Mapping[str, Any],
) -> bool:
    closure = state.get("successor_source_closure")
    completion = state.get("successor_completion_receipt")
    red = state.get("causal_red_evidence_artifact")
    red_identity = state.get("causal_red_evidence")
    green = state.get("combined_green_evidence_artifact")
    green_identity = state.get("combined_green_evidence")
    red_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
        "Successor_RED_Result_20260726.json"
    )
    green_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
        "Successor_GREEN_Result_20260726.json"
    )
    if (
        type(closure) is not dict
        or validate_recovery_epoch002_successor_completion_receipt(
            completion
        )
        or completion.get("successor_source_closure_sha256")
        != closure.get("source_closure_sha256")
        or type(red) is not dict
        or red.get("state") != "SUCCESSOR_CAUSAL_RED_FROZEN"
        or red.get("source_entry_commit_sha1")
        != "5eb4d6d1f0a18a715f33305e7fb7cfe92be42d74"
        or red.get("source_entry_tree_sha1")
        != "b7ad6dd2dbc90e9db296f8599103597d6bbd7ff7"
        or any(
            not _is_plain_int(red.get(key))
            for key in (
                "successor_node_count",
                "collected",
                "failed",
                "passed",
                "collection_errors",
            )
        )
        or red.get("successor_node_count") != 64
        or red.get("collected") != 64
        or red.get("failed") != 64
        or red.get("passed") != 0
        or red.get("collection_errors") != 0
        or red.get("owner_issue_codes") != []
        or red.get("independent_issue_codes") != []
        or red.get("automatic_progression") is not False
        or red.get("body_free") is not True
        or red.get("receipt_sha256")
        != _hash_without(red, "receipt_sha256")
        or not _success_identity_for_artifact(
            red,
            red_identity,
            role="SUCCESSOR_CAUSAL_RED_RESULT",
            path=red_path,
            logical_hash_key="receipt_sha256",
        )
        or type(green) is not dict
        or green.get("causal_red_evidence_sha256")
        != red_identity.get("logical_artifact_sha256")
        or green.get("successor_source_commit_sha1")
        != closure.get("source_commit_sha1")
        or green.get("successor_source_tree_sha1")
        != closure.get("source_tree_sha1")
        or green.get("successor_source_closure_sha256")
        != closure.get("source_closure_sha256")
        or green.get("success_contract_test_manifest_sha256")
        != closure.get("success_contract_test_manifest_sha256")
        or green.get("test_node_ids")
        != list(RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS)
        or green.get("executed_node_ids") != green.get("test_node_ids")
        or green.get("outcome_states")
        != {
            node_id: "PASSED"
            for node_id in RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS
        }
        or type(green.get("counts")) is not dict
        or any(
            not _is_plain_int(value)
            for value in green["counts"].values()
        )
        or green.get("counts")
        != {
            "collected": 110,
            "executed": 110,
            "passed": 110,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
            "deselected": 0,
            "collection_errors": 0,
        }
        or green.get("owner_issue_codes") != []
        or green.get("independent_issue_codes") != []
        or green.get("state")
        != "SUCCESSOR_TARGETED_GREEN_COMPLETED"
        or green.get("automatic_progression") is not False
        or green.get("body_free") is not True
        or green.get("receipt_sha256")
        != _hash_without(green, "receipt_sha256")
        or not _success_identity_for_artifact(
            green,
            green_identity,
            role="SUCCESSOR_COMBINED_GREEN_RESULT",
            path=green_path,
            logical_hash_key="receipt_sha256",
        )
        or completion.get("causal_red_evidence_sha256")
        != red_identity.get("logical_artifact_sha256")
        or completion.get("combined_green_evidence_sha256")
        != green_identity.get("logical_artifact_sha256")
    ):
        return False
    red_fetch = state.get("causal_red_postfetch_evidence")
    green_fetch = state.get("combined_green_postfetch_evidence")
    completion_publication = state.get("successor_completion_publication")
    return (
        _success_postfetch_valid(
            red_fetch,
            red_identity,
        )
        and _success_postfetch_valid(
            green_fetch,
            green_identity,
        )
        and _success_exact1_publication_valid(
            completion_publication,
            role="SUCCESSOR_COMPLETION_RECEIPT",
            path=RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH,
            logical_hash_key="receipt_sha256",
        )
    )


def validate_recovery_epoch002_operational_admission_receipt(
    admission: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate one self-contained P1 operational-admission receipt."""

    if type(admission) is not dict:
        return ("SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",)
    authority = admission.get("authority")
    scope = admission.get("scope")
    completion_identity = admission.get("successor_completion_receipt")
    issued_at = _utc_seconds(admission.get("issued_at_utc"))
    expires_at = _utc_seconds(admission.get("expires_at_utc"))
    if (
        not (
            RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_KEYS
            - RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_OPTIONAL_KEYS
        )
        <= set(admission)
        or not set(admission) <= RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_KEYS
        or admission.get("schema_version")
        != RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCHEMA
        or admission.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or admission.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not _document_identity_valid(completion_identity)
        or completion_identity.get("artifact_role")
        != "SUCCESSOR_COMPLETION_RECEIPT"
        or completion_identity.get("schema_version")
        != RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA
        or completion_identity.get("path")
        != RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH
        or _SHA256_RE.fullmatch(
            str(admission.get("successor_source_closure_sha256", ""))
        )
        is None
        or admission.get("repository_full_name") != "MassyuRed/Cocolon"
        or admission.get("source_ref") != "refs/heads/main"
        or admission.get("owner_validation_state") != "PROVED"
        or admission.get("independent_verification_state") != "PROVED"
        or issued_at is None
        or expires_at is None
        or issued_at >= expires_at
        or admission.get("state") != "P1_OPERATIONAL_ADMISSION_PROVED"
        or admission.get("automatic_progression") is not False
        or admission.get("body_free") is not True
        or admission.get("operational_admission_sha256")
        != _hash_without(admission, "operational_admission_sha256")
        or type(authority) is not dict
        or set(authority)
        != RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or not isinstance(authority.get("admission_authority_token"), str)
        or not authority.get("admission_authority_token")
        or authority.get("admission_authority_token")
        != authority.get("publication_authority_token")
        or authority.get("authority_sha256")
        != _hash_without(authority, "authority_sha256")
        or type(scope) is not dict
        or set(scope) != RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCOPE_KEYS
        or scope.get("repository_full_name") != "MassyuRed/Cocolon"
        or scope.get("source_ref") != "refs/heads/main"
        or scope.get("successor_source_closure_sha256")
        != admission.get("successor_source_closure_sha256")
        or scope.get("operation_set")
        != list(RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_OPERATION_SET)
        or scope.get("scope_sha256")
        != _hash_without(scope, "scope_sha256")
    ):
        return ("SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",)
    return ()


def _success_admission_valid(
    admission: Any,
    *,
    completion_identity: Mapping[str, Any],
    source_closure: Mapping[str, Any],
) -> bool:
    if (
        validate_recovery_epoch002_operational_admission_receipt(admission)
        or admission.get("successor_completion_receipt")
        != completion_identity
        or admission.get("successor_source_closure_sha256")
        != source_closure.get("source_closure_sha256")
    ):
        return False
    authority = admission.get("authority")
    scope = admission.get("scope")
    if (
        type(authority) is not dict
        or set(authority)
        != RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_AUTHORITY_KEYS
        or type(scope) is not dict
        or scope.get("successor_source_closure_sha256")
        != source_closure.get("source_closure_sha256")
    ):
        return False
    return True


def _success_operational_succession_valid(
    state: Mapping[str, Any],
) -> bool:
    closure = state.get("successor_source_closure")
    completion_publication = state.get("successor_completion_publication")
    completion_identity = (
        completion_publication.get("identity")
        if type(completion_publication) is dict
        else None
    )
    allocation = state.get("candidate_allocation")
    allocated_at = (
        _utc_seconds(allocation.get("allocated_at_utc"))
        if type(allocation) is dict
        else None
    )
    if (
        type(closure) is not dict
        or type(completion_identity) is not dict
        or type(allocation) is not dict
        or set(allocation) != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_KEYS
        or allocation.get("schema_version")
        != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_SCHEMA
        or allocation.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or allocation.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not isinstance(allocation.get("candidate_version_id"), str)
        or allocation.get("candidate_version_id") in {"nls_v3_rc_0034", ""}
        or allocation.get("historical_d2_final_closure_sha256")
        != (
            "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
        )
        or allocation.get("historical_d2_completion_receipt")
        != _SUCCESS_D2_IDENTITY
        or allocation.get("successor_source_closure_sha256")
        != closure.get("source_closure_sha256")
        or allocation.get("successor_completion_receipt")
        != completion_identity
        or allocated_at is None
        or allocation.get("candidate_allocation_sha256")
        != _hash_without(allocation, "candidate_allocation_sha256")
    ):
        return False
    admission = state.get("operational_admission_receipt")
    admission_publication = state.get("operational_admission_publication")
    if (
        not _success_admission_valid(
            admission,
            completion_identity=completion_identity,
            source_closure=closure,
        )
        or not _success_exact1_publication_valid(
            admission_publication,
            role="P1_OPERATIONAL_ADMISSION_RECEIPT",
            path=_SUCCESS_OPERATIONAL_ADMISSION_PATH,
            logical_hash_key="operational_admission_sha256",
        )
    ):
        return False
    admission_identity = admission_publication["identity"]
    event = state.get("event1")
    event_publication = state.get("event1_publication")
    event_at = (
        _utc_seconds(event.get("timestamp_utc"))
        if type(event) is dict
        else None
    )
    admission_issued_at = _utc_seconds(admission.get("issued_at_utc"))
    admission_expires_at = _utc_seconds(admission.get("expires_at_utc"))
    if (
        type(event) is not dict
        or set(event) != RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS
        or event.get("schema_version")
        != RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA
        or event.get("ledger_id") != "recovery_epoch002_sequence"
        or event.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or event.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or event.get("candidate_version_id")
        != allocation.get("candidate_version_id")
        or event.get("event_id") != "recovery_epoch002_event_01"
        or event.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or event.get("event_ordinal") != 1
        or not _is_plain_int(event.get("event_ordinal"))
        or event.get("state") != "SOURCE_BASELINE_LOCKED"
        or event.get("timestamp_kind")
        != "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE"
        or event_at is None
        or admission_issued_at is None
        or admission_expires_at is None
        or not (
            admission_issued_at
            < allocated_at
            < event_at
            < admission_expires_at
        )
        or event.get("source_closure") != closure
        or event.get("candidate_allocation") != allocation
        or event.get("bootstrap_closure")
        != state.get("bootstrap_closure")
        or not _p0_external_identity_valid(
            event.get("p0_external_identity")
        )
        or event.get("p0_external_identity", {}).get(
            "p0_external_identity_sha256"
        )
        != _P0_EXTERNAL_IDENTITY_SHA256
        or event.get("prior_event")
        != event.get("p0_external_identity")
        or _SHA256_RE.fullmatch(
            str(event.get("challenge_id", ""))
        )
        is None
        or event.get("automatic_progression") is not False
        or event.get("body_free") is not True
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
    ):
        return False
    authority = event.get("authority")
    publication = event.get("publication")
    transaction = (
        publication.get("transaction_capability")
        if type(publication) is dict
        else None
    )
    transaction_observed_at = (
        _utc_seconds(transaction.get("observed_at_utc"))
        if type(transaction) is dict
        else None
    )
    if (
        type(authority) is not dict
        or set(authority) != RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or authority.get("transition_authority_token")
        != admission["authority"]["admission_authority_token"]
        or authority.get("publication_authority_token")
        != admission["authority"]["publication_authority_token"]
        or authority.get("operational_admission") != admission_identity
        or type(publication) is not dict
        or not (
            RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS
            - RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_OPTIONAL_KEYS
        )
        <= set(publication)
        or not set(publication)
        <= RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS
        or publication.get("repository_full_name") != "MassyuRed/Cocolon"
        or publication.get("branch") != "main"
        or publication.get("event_path") != _SUCCESS_EVENT1_PATH
        or publication.get("supporting_artifact_count") != 1
        or not _is_plain_int(
            publication.get("supporting_artifact_count")
        )
        or publication.get("supporting_artifacts")
        != [completion_identity]
        or publication.get("supporting_artifact_set_sha256")
        != artifact_sha256([completion_identity])
        or publication.get("expected_changed_path_count") != 1
        or not _is_plain_int(
            publication.get("expected_changed_path_count")
        )
        or publication.get("publication_state") != "PUBLISHED_ATOMIC"
        or not _current_transaction_capability_valid(
            transaction,
            expected_changed_path_count=1,
            challenge_id=event.get("challenge_id"),
        )
        or event.get("primary_evidence_artifact") != completion_identity
        or not _success_exact1_publication_valid(
            event_publication,
            role="SOURCE_BASELINE_EVENT",
            path=_SUCCESS_EVENT1_PATH,
            logical_hash_key="event_sha256",
        )
    ):
        return False
    event_identity = event_publication["identity"]
    return state.get("candidate_operational_identity") == {
        "candidate_version_id": allocation["candidate_version_id"],
        "event1_identity_sha256": event_identity["identity_sha256"],
    }


def _validate_recovery_epoch002_successor_succession_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate completion then admission/allocation/Event1 succession."""

    if type(state) is not dict:
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    if not _success_parent_binding_valid(state):
        return ("PARENT_ADDENDUM_BINDING_INVALID",)
    if not _success_completion_evidence_valid(state):
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    if not _success_operational_succession_valid(state):
        return ("SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",)
    return ()


def _validate_recovery_epoch002_success_event2_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate Event2 cardinality and its Event1/All11 lineage."""

    if type(state) is not dict:
        return ("EVENT2_SUPPORTING_ARTIFACT_SET_INVALID",)
    event = state.get("event2")
    publication = event.get("publication") if type(event) is dict else None
    supporting = (
        publication.get("supporting_artifacts")
        if type(publication) is dict
        else None
    )
    candidates = state.get("candidate_identities_by_path")
    artifacts = state.get("artifacts_by_path")
    authority = event.get("authority") if type(event) is dict else None
    allocation = (
        event.get("candidate_allocation")
        if type(event) is dict
        else None
    )
    bootstrap = (
        event.get("bootstrap_closure")
        if type(event) is dict
        else None
    )
    source_closure = (
        event.get("source_closure")
        if type(event) is dict
        else None
    )
    transaction = (
        publication.get("transaction_capability")
        if type(publication) is dict
        else None
    )
    event_at = (
        _utc_seconds(event.get("timestamp_utc"))
        if type(event) is dict
        else None
    )
    transaction_at = (
        _utc_seconds(transaction.get("observed_at_utc"))
        if type(transaction) is dict
        else None
    )
    if (
        type(event) is not dict
        or set(event) != RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS
        or event.get("schema_version")
        != RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA
        or event.get("ledger_id") != "recovery_epoch002_sequence"
        or event.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or event.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or event.get("event_id") != "recovery_epoch002_event_02"
        or event.get("event_name") != "STEP0_10_PREREQUISITES_PROVED"
        or event.get("event_ordinal") != 2
        or type(event.get("event_ordinal")) is not int
        or event.get("state") != "STEP0_10_PREREQUISITES_PROVED"
        or event.get("timestamp_kind")
        != "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE"
        or event_at is None
        or not _p0_external_identity_valid(
            event.get("p0_external_identity")
        )
        or event.get("p0_external_identity", {}).get(
            "p0_external_identity_sha256"
        )
        != _P0_EXTERNAL_IDENTITY_SHA256
        or type(allocation) is not dict
        or set(allocation) != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_KEYS
        or allocation.get("schema_version")
        != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_SCHEMA
        or allocation.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or allocation.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or allocation.get("candidate_version_id")
        != event.get("candidate_version_id")
        or allocation.get("historical_d2_final_closure_sha256")
        != (
            "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
        )
        or allocation.get("historical_d2_completion_receipt")
        != _SUCCESS_D2_IDENTITY
        or type(source_closure) is not dict
        or allocation.get("successor_source_closure_sha256")
        != source_closure.get("source_closure_sha256")
        or not _document_identity_valid(
            allocation.get("successor_completion_receipt")
        )
        or allocation.get("successor_completion_receipt", {}).get(
            "artifact_role"
        )
        != "SUCCESSOR_COMPLETION_RECEIPT"
        or allocation.get("successor_completion_receipt", {}).get("path")
        != RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH
        or _utc_seconds(allocation.get("allocated_at_utc")) is None
        or allocation.get("candidate_allocation_sha256")
        != _hash_without(allocation, "candidate_allocation_sha256")
        or type(bootstrap) is not dict
        or set(bootstrap) != RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS
        or bootstrap.get("schema_version")
        != RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA
        or bootstrap.get("body_free") is not True
        or bootstrap.get("bootstrap_closure_sha256")
        != _hash_without(bootstrap, "bootstrap_closure_sha256")
        or bootstrap.get("source_commit_sha1")
        != source_closure.get("source_commit_sha1")
        or bootstrap.get("source_tree_sha1")
        != source_closure.get("source_tree_sha1")
        or bootstrap.get("bootstrap_closure_sha256")
        != source_closure.get("bootstrap_closure_sha256")
        or event.get("automatic_progression") is not False
        or event.get("body_free") is not True
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or type(publication) is not dict
        or not (
            RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS
            - RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_OPTIONAL_KEYS
        )
        <= set(publication)
        or not set(publication)
        <= RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS
        or publication.get("supporting_artifact_count") != 14
        or type(publication.get("supporting_artifact_count")) is not int
        or type(supporting) is not list
        or len(supporting) != 14
        or any(
            type(identity) is not dict
            or set(identity) != _SUCCESS_CANDIDATE_KEYS
            for identity in supporting
        )
        or type(candidates) is not dict
        or set(candidates) != set(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
        or [identity["path"] for identity in supporting]
        != list(RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS)
        or supporting
        != [
            candidates[path]
            for path in RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS
        ]
        or publication.get("expected_changed_path_count") != 15
        or type(publication.get("expected_changed_path_count")) is not int
        or publication.get("event_path") != _SUCCESS_PATHS[14]
        or publication.get("repository_full_name") != "MassyuRed/Cocolon"
        or publication.get("branch") != "main"
        or _SHA1_RE.fullmatch(
            str(publication.get("base_commit_sha1", ""))
        )
        is None
        or publication.get("publication_state") != "PUBLISHED_ATOMIC"
        or type(authority) is not dict
        or set(authority) != RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or not isinstance(authority.get("transition_authority_token"), str)
        or not authority.get("transition_authority_token")
        or authority.get("publication_authority_token")
        != authority.get("transition_authority_token")
        or not _document_identity_valid(
            authority.get("operational_admission")
        )
        or not _current_transaction_capability_valid(
            transaction,
            expected_changed_path_count=15,
            challenge_id=event.get("challenge_id"),
        )
        or _SHA256_RE.fullmatch(str(event.get("challenge_id", ""))) is None
        or type(artifacts) is not dict
        or set(artifacts) != set(RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS)
    ):
        return ("EVENT2_SUPPORTING_ARTIFACT_SET_INVALID",)
    expected_candidates = {
        path: _success_candidate_for_artifact(
            artifacts[path],
            role=_SUCCESS_ARTIFACT_CONTRACT_BY_PATH[path][0],
            path=path,
            logical_hash_key=_SUCCESS_ARTIFACT_CONTRACT_BY_PATH[path][1],
        )
        for path in RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS
    }
    if (
        any(candidate is None for candidate in expected_candidates.values())
        or candidates != expected_candidates
    ):
        return ("EVENT2_SUPPORTING_ARTIFACT_SET_INVALID",)
    if publication.get("supporting_artifact_set_sha256") != artifact_sha256(
        supporting
    ):
        return ("EVENT2_SUPPORTING_ARTIFACT_SET_HASH_INVALID",)

    accepted = (
        artifacts.get(_SUCCESS_PATHS[0])
        if type(artifacts) is dict
        else None
    )
    all11 = (
        artifacts.get(_SUCCESS_PATHS[12])
        if type(artifacts) is dict
        else None
    )
    success_lineage = (
        accepted.get("success_lineage")
        if type(accepted) is dict
        else None
    )
    event1_identity = (
        success_lineage.get("source_baseline_event")
        if type(success_lineage) is dict
        else None
    )
    if (
        type(event1_identity) is not dict
        or set(event1_identity) != _SUCCESS_EXTERNAL_IDENTITY_KEYS
        or event.get("prior_event") != event1_identity
        or type(all11) is not dict
        or all11.get("source_baseline_event") != event1_identity
        or event.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or allocation.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or bootstrap.get("bootstrap_closure_sha256")
        != accepted.get("formal_worker_terminal_result", {}).get(
            "bootstrap_closure_sha256"
        )
    ):
        return ("EVENT2_EVENT1_ANCESTRY_INVALID",)

    all11_candidate = candidates.get(_SUCCESS_PATHS[12])
    if (
        type(all11_candidate) is not dict
        or set(all11_candidate) != _SUCCESS_CANDIDATE_KEYS
        or event.get("primary_evidence_artifact") != all11_candidate
        or type(all11) is not dict
        or all11_candidate.get("logical_artifact_sha256")
        != all11.get("all11_completion_chain_sha256")
        or all11.get("accepted_test_run_receipt_sha256")
        != accepted.get("accepted_test_run_receipt_sha256")
        or all11.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or event.get("source_closure") != all11.get("source_closure")
    ):
        return ("EVENT2_TERMINAL_SUCCESS_LINEAGE_INVALID",)
    return ()


def validate_recovery_epoch002_successor_succession_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed successor succession state."""

    try:
        if (
            type(state) is dict
            and (
                "parent_addendum_external_identity" not in state
                or "parent_addendum_postfetch_evidence" not in state
            )
        ):
            return ("PARENT_ADDENDUM_BINDING_INVALID",)
        if (
            type(state) is not dict
            or set(state)
            != RECOVERY_EPOCH002_SUCCESSOR_SUCCESSION_STATE_KEYS
            or state.get("reflection_contract_version")
            != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
            or _success_contains_forbidden_state_key(state)
        ):
            return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
        return _validate_recovery_epoch002_successor_succession_state_impl(
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
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)


def validate_recovery_epoch002_success_event2_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed Event2 success-publication state."""

    try:
        if (
            type(state) is not dict
            or set(state) != RECOVERY_EPOCH002_SUCCESS_EVENT2_STATE_KEYS
            or state.get("reflection_contract_version")
            != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
            or _success_contains_forbidden_state_key(state)
        ):
            return ("EVENT2_SUPPORTING_ARTIFACT_SET_INVALID",)
        return _validate_recovery_epoch002_success_event2_state_impl(state)
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("EVENT2_SUPPORTING_ARTIFACT_SET_INVALID",)


__all__ = [
    "RECOVERY_EPOCH002_EVENT1_SCHEMA",
    "RECOVERY_EPOCH002_EVENT1_KEYS",
    "RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA",
    "RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS",
    "RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS",
    "RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS",
    "RECOVERY_EPOCH002_TRANSACTION_CAPABILITY_KEYS",
    "RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS",
    "RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS",
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
    "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA",
    "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_KEYS",
    "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH",
    "RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_SCHEMA",
    "RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_KEYS",
    "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCHEMA",
    "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_KEYS",
    "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_OPERATION_SET",
    "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_AUTHORITY_KEYS",
    "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCOPE_KEYS",
    "RECOVERY_EPOCH002_TRANSPORT_CAPABILITY_KEYS",
    "RECOVERY_EPOCH002_DURABLE_STORE_CAPABILITY_KEYS",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS",
    "build_recovery_epoch002_attempt_id_preimage",
    "build_recovery_epoch002_d2_completion_receipt",
    "validate_recovery_epoch002_d2_completion_receipt",
    "validate_recovery_epoch002_event1_artifact",
    "validate_recovery_epoch002_reservation_artifact",
    "validate_recovery_epoch002_successor_completion_receipt",
    "validate_recovery_epoch002_operational_admission_receipt",
    "validate_recovery_epoch002_lineage_state",
    "validate_recovery_epoch002_successor_succession_state",
    "validate_recovery_epoch002_success_event2_state",
]
