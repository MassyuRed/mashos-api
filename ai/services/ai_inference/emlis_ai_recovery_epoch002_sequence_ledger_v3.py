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
import json
import math
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any, Mapping, Sequence
import unicodedata

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
    load_canonical_json_bytes,
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
    RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS,
    RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA,
    RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS,
    RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA,
    RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS,
    RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA,
    build_recovery_epoch003_source_bootstrap_closure,
    build_recovery_epoch003_source_bootstrap_closure_v2,
    validate_recovery_epoch002_bootstrap_manifest,
    validate_recovery_epoch002_source_closure,
    validate_recovery_epoch003_source_bootstrap_contract_state,
    validate_recovery_epoch003_source_bootstrap_contract_state_v2,
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
_LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_completion_receipt.v2"
)
_LINEAGE02_SUCCESSOR_COMPLETION_KEYS = (
    RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_KEYS
    | frozenset(
        {"lineage_recovery_decision_external_identity_sha256"}
    )
)
_LINEAGE02_SUCCESSOR_GREEN_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
    "SourceIdentityLineage02_Successor_GREEN_Result_20260728.json"
)
_LINEAGE02_SUCCESSOR_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2"
    "SourceIdentityLineage02_SourceBaselineEligibilitySuccessor"
    "Completion_BodyFree_Receipt_20260728.json"
)
_LINEAGE02_RECOVERY_DECISION_EXTERNAL_IDENTITY_SHA256 = (
    "9602c7cf4092594950d988c05a886c0780c32ff1eebc9fa940"
    "9d00959becad13"
)
_HISTORICAL_SUCCESSOR_SOURCE_CLOSURE_SHA256 = (
    "d4156b14eddf5e1f6a13411017bd522784b26e3e67d780203a"
    "727cc7cc1aa97f"
)
_SUCCESS_HISTORICAL_S1_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_successor_red_result.v1"
)
_SUCCESS_HISTORICAL_S1_KEYS = _keys(
    """
    schema_version authority_token source_entry_commit_sha1
    source_entry_tree_sha1 successor_test_file successor_node_count collected
    failed passed collection_errors owner_issue_codes independent_issue_codes
    state automatic_progression body_free receipt_sha256
    """
)
_SUCCESS_HISTORICAL_S1_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_POST_D2_"
    "SOURCE_BASELINE_ELIGIBILITY_SUCCESSION_ACCEPTED_STEP0_10_ALL11_"
    "EVENT2_ATOMIC_SUCCESS_OWNER_GRAPH_AND_FORMAL_PARENT_CONTINUATION_"
    "REMEDIATION_RED_FREEZE_ONLY"
)
_SUCCESS_HISTORICAL_S1_TEST_FILE = {
    "path": (
        "ai/tests/test_emlis_nls_v3_recovery_epoch002_post_d2_success_"
        "owner_graph_and_formal_parent_continuation_red.py"
    ),
    "git_blob_sha1": "1616de8b9f738b7037b6e18a64113280fa6ec478",
    "raw_sha256": (
        "3e5cdcd5c2cd2113f273f6cc1a43ff09bdd4845b14cd7aea"
        "49237d26cfc0753b"
    ),
}
_SUCCESS_HISTORICAL_S1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
    "Successor_RED_Result_20260726.json"
)
_SUCCESS_HISTORICAL_S1_LOGICAL_SHA256 = (
    "7b3b6d0890038642d69feb18e46630fbf97a5918fe0e95db"
    "766b8c8175e2d179"
)
_SUCCESS_HISTORICAL_S1_IDENTITY = {
    "artifact_role": "SUCCESSOR_CAUSAL_RED_RESULT",
    "schema_version": _SUCCESS_HISTORICAL_S1_SCHEMA,
    "repository_full_name": "MassyuRed/Cocolon",
    "path": _SUCCESS_HISTORICAL_S1_PATH,
    "git_blob_sha1": "fa2ac8978294e9eb92211147c09989ae7583455e",
    "raw_sha256": (
        "f03bf71f267813d25664ceacd1344d74fb354156a9c65b19c"
        "14a3c7f315e4c03"
    ),
    "logical_artifact_sha256": _SUCCESS_HISTORICAL_S1_LOGICAL_SHA256,
    "publication_commit_sha1": "a45a958cab1a5e1d052e6b470dd26d8e19764b7b",
    "body_free": True,
    "identity_sha256": (
        "1504bf4f58ca02b76df7f0a9fd6f88a429b01a56c59b7a90"
        "82648a25fb3614b4"
    ),
}
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


def _validate_recovery_epoch002_historical_event1_artifact(
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


def validate_recovery_epoch002_event1_artifact(
    event: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate either immutable historical-v1 or current successor-v2 Event1."""

    if (
        type(event) is dict
        and event.get("schema_version")
        == RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA
    ):
        return (
            ()
            if _current_recovery_epoch002_event1_v2_artifact_valid(event)
            else ("SOURCE_BASELINE_EVENT_INVALID",)
        )
    return _validate_recovery_epoch002_historical_event1_artifact(event)


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


def _current_recovery_epoch002_event1_v2_artifact_valid(
    event: Any,
) -> bool:
    """Validate the intrinsic, self-contained successor Event1-v2 contract."""

    if type(event) is not dict:
        return False
    closure = event.get("source_closure")
    allocation = event.get("candidate_allocation")
    completion_identity = event.get("primary_evidence_artifact")
    bootstrap = event.get("bootstrap_closure")
    p0_identity = event.get("p0_external_identity")
    authority = event.get("authority")
    admission_identity = (
        authority.get("operational_admission")
        if type(authority) is dict
        else None
    )
    publication = event.get("publication")
    transaction = (
        publication.get("transaction_capability")
        if type(publication) is dict
        else None
    )
    event_at = _utc_seconds(event.get("timestamp_utc"))
    allocated_at = (
        _utc_seconds(allocation.get("allocated_at_utc"))
        if type(allocation) is dict
        else None
    )
    closure_sha256_keys = (
        {
            key
            for key in closure
            if key.endswith("_sha256")
        }
        if type(closure) is dict
        else set()
    )
    if (
        set(event) != RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS
        or event.get("schema_version")
        != RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA
        or event.get("ledger_id") != "recovery_epoch002_sequence"
        or event.get("event_id") != "recovery_epoch002_event_01"
        or event.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or event.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not isinstance(event.get("candidate_version_id"), str)
        or event.get("candidate_version_id") in {"", "nls_v3_rc_0034"}
        or event.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or event.get("event_ordinal") != 1
        or not _is_plain_int(event.get("event_ordinal"))
        or event.get("state") != "SOURCE_BASELINE_LOCKED"
        or event_at is None
        or event.get("timestamp_kind")
        != "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE"
        or _SHA256_RE.fullmatch(
            str(event.get("challenge_id", ""))
        )
        is None
        or event.get("automatic_progression") is not False
        or event.get("body_free") is not True
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or type(closure) is not dict
        or set(closure)
        != RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS
        or closure.get("schema_version")
        != RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA
        or closure.get("repository_full_name") != "MassyuRed/mashos-api"
        or closure.get("source_ref") != "refs/heads/main"
        or closure.get("worktree_clean") is not True
        or _SHA1_RE.fullmatch(
            str(closure.get("source_commit_sha1", ""))
        )
        is None
        or _SHA1_RE.fullmatch(
            str(closure.get("source_tree_sha1", ""))
        )
        is None
        or any(
            _SHA256_RE.fullmatch(str(closure.get(key, ""))) is None
            for key in closure_sha256_keys
        )
        or closure.get("source_closure_sha256")
        != _hash_without(closure, "source_closure_sha256")
        or type(allocation) is not dict
        or set(allocation) != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_KEYS
        or allocation.get("schema_version")
        != RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_SCHEMA
        or allocation.get("logical_cycle_id")
        != event.get("logical_cycle_id")
        or allocation.get("recovery_epoch_id")
        != event.get("recovery_epoch_id")
        or allocation.get("candidate_version_id")
        != event.get("candidate_version_id")
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
        or allocated_at >= event_at
        or allocation.get("candidate_allocation_sha256")
        != _hash_without(allocation, "candidate_allocation_sha256")
        or not _successor_completion_identity_valid(completion_identity)
        or type(bootstrap) is not dict
        or set(bootstrap) != RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS
        or bootstrap.get("schema_version")
        != RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA
        or bootstrap.get("source_commit_sha1")
        != closure.get("source_commit_sha1")
        or bootstrap.get("source_tree_sha1")
        != closure.get("source_tree_sha1")
        or bootstrap.get("body_free") is not True
        or bootstrap.get("bootstrap_closure_sha256")
        != _hash_without(bootstrap, "bootstrap_closure_sha256")
        or closure.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or not _p0_external_identity_valid(p0_identity)
        or p0_identity.get("p0_external_identity_sha256")
        != _P0_EXTERNAL_IDENTITY_SHA256
        or event.get("prior_event") != p0_identity
        or type(authority) is not dict
        or set(authority)
        != RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or not isinstance(
            authority.get("transition_authority_token"),
            str,
        )
        or not authority.get("transition_authority_token")
        or authority.get("transition_authority_token")
        != authority.get("publication_authority_token")
        or not _document_identity_valid(admission_identity)
        or admission_identity.get("artifact_role")
        != "P1_OPERATIONAL_ADMISSION_RECEIPT"
        or admission_identity.get("schema_version")
        != RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCHEMA
        or admission_identity.get("path")
        != _SUCCESS_OPERATIONAL_ADMISSION_PATH
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
        or _SHA1_RE.fullmatch(
            str(publication.get("base_commit_sha1", ""))
        )
        is None
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
        or (
            "ref_update_mode" in publication
            and publication.get("ref_update_mode")
            != "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
        )
        or publication.get("publication_state") != "PUBLISHED_ATOMIC"
        or not _current_transaction_capability_valid(
            transaction,
            expected_changed_path_count=1,
            challenge_id=event.get("challenge_id"),
        )
        or (
            type(transaction) is dict
            and "operational_admission_identity_sha256" in transaction
            and transaction.get(
                "operational_admission_identity_sha256"
            )
            != admission_identity.get("identity_sha256")
        )
    ):
        return False
    return True


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
    """Validate one strict historical exact13 or Lineage02 exact14 receipt."""

    if (
        type(receipt) is not dict
        or _successor_completion_contract(receipt) is None
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


def _successor_completion_contract(
    receipt: Any,
) -> tuple[str, str] | None:
    if type(receipt) is not dict:
        return None
    if (
        receipt.get("schema_version")
        == RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA
        and set(receipt) == RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_KEYS
    ):
        return (
            (
                "EmlisAIの実装済み資料/documents/"
                "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
                "Successor_GREEN_Result_20260726.json"
            ),
            RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH,
        )
    if (
        receipt.get("schema_version")
        == _LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA
        and set(receipt) == _LINEAGE02_SUCCESSOR_COMPLETION_KEYS
        and receipt.get(
            "lineage_recovery_decision_external_identity_sha256"
        )
        == _LINEAGE02_RECOVERY_DECISION_EXTERNAL_IDENTITY_SHA256
    ):
        return (
            _LINEAGE02_SUCCESSOR_GREEN_PATH,
            _LINEAGE02_SUCCESSOR_COMPLETION_PATH,
        )
    return None


def _successor_completion_identity_valid(identity: Any) -> bool:
    if (
        not _document_identity_valid(identity)
        or identity.get("artifact_role") != "SUCCESSOR_COMPLETION_RECEIPT"
    ):
        return False
    return (
        identity.get("schema_version"),
        identity.get("path"),
    ) in {
        (
            RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA,
            RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH,
        ),
        (
            _LINEAGE02_SUCCESSOR_COMPLETION_SCHEMA,
            _LINEAGE02_SUCCESSOR_COMPLETION_PATH,
        ),
    }


def _success_completion_evidence_valid(
    state: Mapping[str, Any],
) -> bool:
    closure = state.get("successor_source_closure")
    completion = state.get("successor_completion_receipt")
    red = state.get("causal_red_evidence_artifact")
    red_identity = state.get("causal_red_evidence")
    green = state.get("combined_green_evidence_artifact")
    green_identity = state.get("combined_green_evidence")
    completion_contract = _successor_completion_contract(completion)
    if completion_contract is None:
        return False
    green_path, completion_path = completion_contract
    if (
        type(closure) is not dict
        or closure.get("source_closure_sha256")
        == _HISTORICAL_SUCCESSOR_SOURCE_CLOSURE_SHA256
        or validate_recovery_epoch002_successor_completion_receipt(
            completion
        )
        or completion.get("successor_source_closure_sha256")
        != closure.get("source_closure_sha256")
        or type(red) is not dict
        or set(red) != _SUCCESS_HISTORICAL_S1_KEYS
        or red.get("schema_version") != _SUCCESS_HISTORICAL_S1_SCHEMA
        or red.get("authority_token")
        != _SUCCESS_HISTORICAL_S1_AUTHORITY
        or type(red.get("successor_test_file")) is not dict
        or red.get("successor_test_file")
        != _SUCCESS_HISTORICAL_S1_TEST_FILE
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
        != _SUCCESS_HISTORICAL_S1_LOGICAL_SHA256
        or red_identity != _SUCCESS_HISTORICAL_S1_IDENTITY
        or red.get("receipt_sha256")
        != _hash_without(red, "receipt_sha256")
        or not _success_identity_for_artifact(
            red,
            red_identity,
            role="SUCCESSOR_CAUSAL_RED_RESULT",
            path=_SUCCESS_HISTORICAL_S1_PATH,
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
            path=completion_path,
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
        or not _successor_completion_identity_valid(completion_identity)
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
        or not _successor_completion_identity_valid(
            allocation.get("successor_completion_receipt")
        )
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


RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.sequence_event.v1"
)
RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS = _keys(
    """
    schema_version ledger_id event_id logical_cycle_id recovery_epoch_id
    candidate_version_id event_ordinal event_name state prior_event
    challenge_id timestamp_utc timestamp_kind authority p0_external_identity
    candidate_allocation source_closure bootstrap_closure
    primary_evidence_artifact publication body_free automatic_progression
    event_sha256
    """
)
_RECOVERY_EPOCH003_HISTORICAL_CHALLENGE_IDS = frozenset(
    {
        "5d58979338cbc30ce603df884d466981895e05198196925e209424a129c4b0f9",
        "6c315203ce98f635feb80b04f27ab7dcb43545f2883b8a6fcca36c8c1cb7acf4",
    }
)
_RECOVERY_EPOCH003_EVENT_FORBIDDEN_KEYS = frozenset(
    {
        "runtime_materialization",
        "runtime_root_identity_sha256",
        "reference_runtime_root_identity_sha256",
        "attempt_registry_root_identity_sha256",
        "operational_runtime_observation",
        "readiness_receipt",
        "failure_receipt",
        "reservation",
        "attempt",
        "pytest_main_called",
        "formal_exact134_invocation_count",
        "collection_state",
        "test_execution_state",
    }
)
_RECOVERY_EPOCH003_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RECOVERY_EPOCH003_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_RECOVERY_EPOCH003_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
_RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role body_free git_blob_sha1 identity_sha256
    logical_artifact_sha256 path publication_commit_sha1 raw_sha256
    repository_full_name schema_version
    """
)
_RECOVERY_EPOCH003_P0_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id parent_design receipt
    p0_external_identity_sha256
    """
)
_RECOVERY_EPOCH003_P0_PARENT_KEYS = _keys(
    "path publication_commit_sha1 git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_P0_RECEIPT_KEYS = _keys(
    """
    path publication_commit_sha1 git_blob_sha1 raw_sha256
    logical_receipt_sha256
    """
)
_RECOVERY_EPOCH003_AUTHORITY_KEYS = _keys(
    """
    approval_kind operational_admission publication_authority_token
    transition_authority_token
    """
)
_RECOVERY_EPOCH003_CANDIDATE_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    allocated_at_utc p0_external_identity_sha256 source_closure_sha256
    reference_runtime_observation_external_identity_sha256
    candidate_allocation_sha256
    """
)
_RECOVERY_EPOCH003_PUBLICATION_KEYS = _keys(
    """
    base_commit_sha1 branch event_path expected_changed_path_count
    publication_state repository_full_name supporting_artifact_count
    supporting_artifact_set_sha256 supporting_artifacts
    """
)
_RECOVERY_EPOCH003_P0_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch003.p0_external_identity.v1"
)
_RECOVERY_EPOCH003_P0_IDENTITY_SHA256 = (
    "74286b862eeee1663d2758ee18d1e848316da6fc27b12fef38c149c5a2b52f36"
)
_RECOVERY_EPOCH003_EVENT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event.json"
)
_RECOVERY_EPOCH003_REFERENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "reference_runtime_observation.v1"
)
_RECOVERY_EPOCH003_REFERENCE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PreEvent1_ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
)
_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "OperationalAdmission_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_FINAL_PRE_EVENT1_REFERENCE_"
    "RUNTIME_OBSERVATION_AND_SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_"
    "CARRIER_ISSUANCE_INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_RECOVERY_EPOCH003_EVENT1_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_DISTINCT_CANDIDATE_"
    "ALLOCATION_AND_SEQUENCE_EVENT1_SOURCE_BASELINE_LOCK_PUBLICATION_"
    "INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id predecessor_bindings
    source_closure bootstrap_closure authority scope freshness
    effect_boundary owner_validation_state independent_verification_state
    state automatic_progression body_free operational_admission_sha256
    """
)
_RECOVERY_EPOCH003_PREDECESSOR_KEYS = _keys(
    """
    p0_external_identity
    operational_admission_parent_addendum_receipt_external_identity
    bootstrap_contract_d1_receipt_external_identity
    bootstrap_contract_d2_receipt_external_identity
    operational_admission_contract_d1_receipt_external_identity
    operational_admission_contract_d2_receipt_external_identity
    reference_runtime_observation_external_identity
    predecessor_bindings_sha256
    """
)
_RECOVERY_EPOCH003_ADMISSION_AUTHORITY_KEYS = _keys(
    """
    approval_kind admission_authority_token publication_authority_token
    authority_sha256
    """
)
_RECOVERY_EPOCH003_ADMISSION_SCOPE_KEYS = _keys(
    """
    artifact_repository_full_name source_repository_full_name source_ref
    source_commit_sha1 source_tree_sha1 source_closure_sha256
    bootstrap_closure_sha256
    reference_runtime_observation_external_identity_sha256
    next_authority_token operation_set separate_explicit_authority_required
    scope_sha256
    """
)
_RECOVERY_EPOCH003_FRESHNESS_KEYS = _keys(
    """
    issued_at_utc expires_at_utc validity_mode bound_source_commit_sha1
    bound_source_tree_sha1
    bound_reference_runtime_observation_external_identity_sha256
    event1_path_state_at_issuance maximum_event1_consumption_count
    invalidation_conditions reuse_allowed freshness_sha256
    """
)
_RECOVERY_EPOCH003_FRESHNESS_POLICY_KEYS = (
    _RECOVERY_EPOCH003_FRESHNESS_KEYS
    - {"issued_at_utc", "freshness_sha256"}
)
_RECOVERY_EPOCH003_EFFECT_KEYS = _keys(
    """
    reference_runtime_materialization_count_delta
    reference_runtime_observation_publication_count
    operational_admission_publication_count
    operational_runtime_materialization_count candidate_allocation_count
    sequence_event1_count readiness_artifact_count formal_reservation_count
    formal_attempt_count formal_exact134_invocation_count
    formal_test_collection_count test_execution_count pytest_main_call_count
    source_baseline_state effect_boundary_sha256
    """
)
_RECOVERY_EPOCH003_REFERENCE_PUBLICATION_STATE_KEYS = _keys(
    """
    artifact_repository_root external_identity postfetch_body
    admission_base_commit_sha1 admission_base_tree_sha1
    reference_publication_is_ancestor_of_admission_base
    reference_path_blob_at_admission_base_sha1
    """
)
_RECOVERY_EPOCH003_SOURCE_OBSERVATION_KEYS = _keys(
    """
    source_repository_root source_commit_sha1 source_tree_sha1
    worktree_clean
    """
)
_RECOVERY_EPOCH003_OPERATION_SET = (
    "OPERATIONAL_ADMISSION_PUBLICATION",
    "DISTINCT_CANDIDATE_ALLOCATION",
    "SOURCE_BASELINE_EVENT1_PUBLICATION",
    "OPERATIONAL_RUNTIME_MATERIALIZATION",
    "OPERATIONAL_RUNTIME_OBSERVATION_PUBLICATION",
    "BOOTSTRAP_READINESS_OR_FAILURE_PUBLICATION",
    "FORMAL_ATTEMPT_ONE_SHOT_RESERVATION_PUBLICATION",
)
_RECOVERY_EPOCH003_INVALIDATION_CONDITIONS = (
    "ADMISSION_IDENTITY_ALREADY_BOUND_BY_EVENT1",
    "REFERENCE_OR_PREDECESSOR_IDENTITY_NOT_REACHABLE_OR_BYTE_DRIFTED",
    "SOURCE_COMMIT_OR_TREE_DRIFTED_OR_WORKTREE_NOT_CLEAN",
    "SOURCE_OR_BOOTSTRAP_CLOSURE_MISMATCH",
)
_RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS = {
    "operational_admission_parent_addendum_receipt_external_identity": (
        (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PARENT_ADDENDUM_"
            "DESIGN_FROZEN_RECEIPT"
        ),
        (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission_parent_addendum_design_frozen_receipt.v1"
        ),
        (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "FinalSourceBootstrapReferenceRuntimeClosureAndOperational"
            "AdmissionContractUnreachable_P0ParentAddendum_Design_ReadOnly_"
            "BodyFree_Receipt_20260729.json"
        ),
        "e8cc49a4983bb1c7e46948fb92ea605ce8fde7aa3a07926fbf047725e14bbf43",
    ),
    "bootstrap_contract_d1_receipt_external_identity": (
        (
            "RECOVERY_EPOCH003_D1_BOOTSTRAP_ORACLE_CORRECTION_CAUSAL_RED_"
            "REFREEZE_RECEIPT"
        ),
        (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d1_bootstrap_oracle_correction_causal_red_refreeze_receipt.v1"
        ),
        (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_D1_"
            "BootstrapFormalExact134ManifestAndReferenceRuntimeRootIdentity"
            "Binding_OracleCorrectionAndCausalREDRefreeze_"
            "BodyFree_Receipt_20260729.json"
        ),
        "d9164d82715abb519b549a7581737a37ebd3bf153b53284697cbe4573a8edb9e",
    ),
    "bootstrap_contract_d2_receipt_external_identity": (
        (
            "RECOVERY_EPOCH003_D2_BOOTSTRAP_SOURCE_RUNTIME_TARGETED_GREEN_"
            "RECEIPT"
        ),
        (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d2_bootstrap_source_runtime_targeted_green_receipt.v1"
        ),
        (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_D2_"
            "BootstrapSourceRuntimeExpectedObservedSeparationSchemaPair"
            "DispatchEvent1ImmutabilityAndIndependentOperationalProjection_"
            "ImplementationAndTargetedGREEN_BodyFree_Receipt_20260729.json"
        ),
        "cbd665b12b3af16b251a66073222d12823fb8776207922616718290e4bddc738",
    ),
    "operational_admission_contract_d1_receipt_external_identity": (
        (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_CAUSAL_RED_"
            "RECEIPT"
        ),
        (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission_contract_causal_red_receipt.v1"
        ),
        (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "PostP0ParentAddendum_D1_OperationalAdmissionSourceBootstrap"
            "CarrierReferenceMaterializerEvent1BindingAndPhaseEvidence"
            "Contract_CausalRED_FreezeOnly_BodyFree_Receipt_20260729.json"
        ),
        "d1897d23f89d8df0fce8fd5591b77aeb3e2832197d1474aa8827b810805c174b",
    ),
    "operational_admission_contract_d2_receipt_external_identity": (
        (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_TARGETED_"
            "GREEN_RECEIPT"
        ),
        (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission_contract_targeted_green_receipt.v1"
        ),
        (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "PostP0ParentAddendum_D2_OperationalAdmissionSourceBootstrap"
            "CarrierReferenceMaterializerEvent1BindingAndPhaseEvidence"
            "Contract_ImplementationAndTargetedGREEN_"
            "BodyFree_Receipt_20260729.json"
        ),
        None,
    ),
}


def _recovery_epoch003_hash_without(
    value: Mapping[str, Any],
    key: str,
) -> str:
    material = dict(value)
    material.pop(key, None)
    return artifact_sha256(material)


def _recovery_epoch003_event_hash(value: Mapping[str, Any]) -> str:
    payload = dict(value)
    payload.pop("event_sha256", None)
    return artifact_sha256(payload)


def _recovery_epoch003_external_identity_valid(
    value: Any,
    *,
    role: str,
    schema: str | None,
    path: str | None,
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        or value.get("artifact_role") != role
        or (
            value.get("schema_version") != schema
            if schema is not None
            else not isinstance(value.get("schema_version"), str)
            or not value.get("schema_version")
        )
        or (
            value.get("path") != path
            if path is not None
            else not isinstance(value.get("path"), str)
            or not value.get("path")
            or PurePosixPath(value["path"]).is_absolute()
            or ".." in PurePosixPath(value["path"]).parts
        )
        or value.get("repository_full_name") != "MassyuRed/Cocolon"
        or value.get("body_free") is not True
        or _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("git_blob_sha1", ""))
        )
        is None
        or _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("publication_commit_sha1", ""))
        )
        is None
        or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(value.get("raw_sha256", ""))
        )
        is None
        or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(value.get("logical_artifact_sha256", ""))
        )
        is None
    ):
        return False
    material = dict(value)
    material.pop("identity_sha256", None)
    return value.get("identity_sha256") == artifact_sha256(material)


def _recovery_epoch003_p0_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_P0_KEYS
        or value.get("schema_version") != _RECOVERY_EPOCH003_P0_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or type(value.get("parent_design")) is not dict
        or set(value["parent_design"])
        != _RECOVERY_EPOCH003_P0_PARENT_KEYS
        or type(value.get("receipt")) is not dict
        or set(value["receipt"]) != _RECOVERY_EPOCH003_P0_RECEIPT_KEYS
    ):
        return False
    identity_fields = (
        value["parent_design"],
        value["receipt"],
    )
    if any(
        _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(row.get(key, ""))
        )
        is None
        for row in identity_fields
        for key in (
            "publication_commit_sha1",
            "git_blob_sha1",
        )
    ) or any(
        _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(row.get(key, ""))
        )
        is None
        for row in identity_fields
        for key in (
            "raw_sha256",
            *(
                ("logical_receipt_sha256",)
                if row is value["receipt"]
                else ()
            ),
        )
    ):
        return False
    material = dict(value)
    material.pop("p0_external_identity_sha256", None)
    return (
        value.get("p0_external_identity_sha256")
        == _RECOVERY_EPOCH003_P0_IDENTITY_SHA256
        == artifact_sha256(material)
    )


def _recovery_epoch003_candidate_valid(
    value: Any,
    *,
    event: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_CANDIDATE_KEYS
        or value.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "candidate_allocation.v1"
        )
        or value.get("logical_cycle_id") != event.get("logical_cycle_id")
        or value.get("recovery_epoch_id")
        != event.get("recovery_epoch_id")
        or value.get("candidate_version_id")
        != event.get("candidate_version_id")
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(value.get("allocated_at_utc", ""))
        )
        is None
        or value.get("p0_external_identity_sha256")
        != _RECOVERY_EPOCH003_P0_IDENTITY_SHA256
        or value.get("source_closure_sha256")
        != event["source_closure"].get("source_closure_sha256")
        or value.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != event["bootstrap_closure"][
            "reference_runtime_observation_external_identity"
        ].get("identity_sha256")
    ):
        return False
    material = dict(value)
    material.pop("candidate_allocation_sha256", None)
    return value.get("candidate_allocation_sha256") == artifact_sha256(
        material
    )


def _recovery_epoch003_authority_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_AUTHORITY_KEYS
        and isinstance(value.get("approval_kind"), str)
        and bool(value.get("approval_kind"))
        and isinstance(value.get("publication_authority_token"), str)
        and bool(value.get("publication_authority_token"))
        and isinstance(value.get("transition_authority_token"), str)
        and bool(value.get("transition_authority_token"))
        and value.get("publication_authority_token")
        != value.get("transition_authority_token")
        and _recovery_epoch003_external_identity_valid(
            value.get("operational_admission"),
            role="RECOVERY_EPOCH003_OPERATIONAL_ADMISSION",
            schema=None,
            path=None,
        )
    )


def _recovery_epoch003_publication_valid(
    value: Any,
    *,
    event: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_PUBLICATION_KEYS
        or _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("base_commit_sha1", ""))
        )
        is None
        or value.get("branch") != "main"
        or value.get("event_path") != _RECOVERY_EPOCH003_EVENT_PATH
        or value.get("repository_full_name") != "MassyuRed/Cocolon"
        or not isinstance(value.get("publication_state"), str)
        or not value.get("publication_state")
        or type(value.get("supporting_artifacts")) is not list
    ):
        return False
    supporting = value["supporting_artifacts"]
    primary = event["primary_evidence_artifact"]
    reference = event["bootstrap_closure"][
        "reference_runtime_observation_external_identity"
    ]
    if (
        supporting
        != sorted(
            supporting,
            key=lambda row: (
                row.get("artifact_role")
                if type(row) is dict
                else "",
                row.get("path") if type(row) is dict else "",
                row.get("identity_sha256")
                if type(row) is dict
                else "",
            ),
        )
        or len(
            {
                (
                    row.get("artifact_role"),
                    row.get("path"),
                    row.get("identity_sha256"),
                )
                for row in supporting
                if type(row) is dict
            }
        )
        != len(supporting)
        or supporting
        != sorted(
            [deepcopy(reference), deepcopy(primary)],
            key=lambda row: (
                row["artifact_role"],
                row["path"],
                row["identity_sha256"],
            ),
        )
        or value.get("supporting_artifact_count") != len(supporting)
        or value.get("expected_changed_path_count")
        != 1 + len(supporting)
        or value.get("supporting_artifact_set_sha256")
        != artifact_sha256(supporting)
    ):
        return False
    return all(
        type(row) is dict
        and set(row) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        for row in supporting
    )


def _recovery_epoch003_event_contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return bool(
            set(value) & _RECOVERY_EPOCH003_EVENT_FORBIDDEN_KEYS
        ) or any(
            _recovery_epoch003_event_contains_forbidden_key(item)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(
            _recovery_epoch003_event_contains_forbidden_key(item)
            for item in value
        )
    return False


def _recovery_epoch003_event_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or value.get("ledger_id")
        != "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003"
        or value.get("event_id")
        != "NLS_V3_RECOVERY_EPOCH003_SEQUENCE_EVENT_01"
        or value.get("event_ordinal") != 1
        or value.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or not isinstance(value.get("candidate_version_id"), str)
        or not value.get("candidate_version_id")
        or not isinstance(value.get("state"), str)
        or not value.get("state")
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(value.get("timestamp_utc", ""))
        )
        is None
        or not isinstance(value.get("timestamp_kind"), str)
        or not value.get("timestamp_kind")
        or value.get("body_free") is not True
        or value.get("automatic_progression") is not False
        or value.get("event_sha256") != _recovery_epoch003_event_hash(value)
        or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(value.get("challenge_id", ""))
        )
        is None
    ):
        return False
    required_objects = (
        "prior_event",
        "authority",
        "p0_external_identity",
        "candidate_allocation",
        "source_closure",
        "bootstrap_closure",
        "primary_evidence_artifact",
        "publication",
    )
    if any(type(value.get(key)) is not dict for key in required_objects):
        return False
    if (
        value["source_closure"].get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "source_baseline_eligibility_closure.v1"
        )
        or value["bootstrap_closure"].get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "formal_worker_bootstrap_manifest.v1"
        )
        or validate_recovery_epoch003_source_bootstrap_contract_state(
            {
                "source_closure": value["source_closure"],
                "bootstrap_closure": value["bootstrap_closure"],
            }
        )
        != ()
        or not _recovery_epoch003_p0_valid(value["p0_external_identity"])
        or value["prior_event"] != value["p0_external_identity"]
        or not _recovery_epoch003_candidate_valid(
            value["candidate_allocation"],
            event=value,
        )
        or not _recovery_epoch003_authority_valid(value["authority"])
        or not _recovery_epoch003_external_identity_valid(
            value["primary_evidence_artifact"],
            role="RECOVERY_EPOCH003_D2_GREEN_RECEIPT",
            schema=None,
            path=None,
        )
        or not _recovery_epoch003_external_identity_valid(
            value["bootstrap_closure"][
                "reference_runtime_observation_external_identity"
            ],
            role="RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION",
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
        )
        or not _recovery_epoch003_publication_valid(
            value["publication"],
            event=value,
        )
    ):
        return False
    return not _recovery_epoch003_event_contains_forbidden_key(value)


def _recovery_epoch003_generic_external_identity_valid(
    value: Any,
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        and isinstance(value.get("artifact_role"), str)
        and bool(value.get("artifact_role"))
        and isinstance(value.get("schema_version"), str)
        and bool(value.get("schema_version"))
        and isinstance(value.get("path"), str)
        and bool(value.get("path"))
        and not PurePosixPath(value["path"]).is_absolute()
        and ".." not in PurePosixPath(value["path"]).parts
        and value.get("repository_full_name") == "MassyuRed/Cocolon"
        and value.get("body_free") is True
        and _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("git_blob_sha1", ""))
        )
        is not None
        and _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("publication_commit_sha1", ""))
        )
        is not None
        and _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(value.get("raw_sha256", ""))
        )
        is not None
        and _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(value.get("logical_artifact_sha256", ""))
        )
        is not None
        and value.get("identity_sha256")
        == _recovery_epoch003_hash_without(value, "identity_sha256")
    )


def _recovery_epoch003_predecessors_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_PREDECESSOR_KEYS
        or not _recovery_epoch003_p0_valid(value.get("p0_external_identity"))
        or value.get("predecessor_bindings_sha256")
        != _recovery_epoch003_hash_without(
            value,
            "predecessor_bindings_sha256",
        )
    ):
        return False
    identities = {
        key: value.get(key)
        for key in _RECOVERY_EPOCH003_PREDECESSOR_KEYS
        - {"p0_external_identity", "predecessor_bindings_sha256"}
    }
    if any(
        not _recovery_epoch003_generic_external_identity_valid(identity)
        for identity in identities.values()
    ):
        return False
    for key, contract in (
        _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS.items()
    ):
        role, schema, path, fixed_identity = contract
        identity = identities.get(key)
        if (
            identity.get("artifact_role") != role
            or identity.get("schema_version") != schema
            or identity.get("path") != path
            or (
                fixed_identity is not None
                and identity.get("identity_sha256") != fixed_identity
            )
        ):
            return False
    return _recovery_epoch003_external_identity_valid(
        identities["reference_runtime_observation_external_identity"],
        role="RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION",
        schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
        path=_RECOVERY_EPOCH003_REFERENCE_PATH,
    )


def _recovery_epoch003_admission_authority_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_ADMISSION_AUTHORITY_KEYS
        and value.get("approval_kind") == "EXPLICIT_SEPARATE_APPROVAL"
        and value.get("admission_authority_token")
        == _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        and value.get("publication_authority_token")
        == _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        and value.get("authority_sha256")
        == _recovery_epoch003_hash_without(value, "authority_sha256")
    )


def _recovery_epoch003_admission_scope_valid(
    value: Any,
    *,
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_ADMISSION_SCOPE_KEYS
        and value.get("artifact_repository_full_name")
        == "MassyuRed/Cocolon"
        and value.get("source_repository_full_name")
        == "MassyuRed/mashos-api"
        and value.get("source_ref") == "refs/heads/main"
        and value.get("source_commit_sha1")
        == source.get("source_commit_sha1")
        == bootstrap.get("source_commit_sha1")
        and value.get("source_tree_sha1")
        == source.get("source_tree_sha1")
        == bootstrap.get("source_tree_sha1")
        and value.get("source_closure_sha256")
        == source.get("source_closure_sha256")
        and value.get("bootstrap_closure_sha256")
        == bootstrap.get("bootstrap_closure_sha256")
        and value.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        == reference_identity.get("identity_sha256")
        and value.get("next_authority_token")
        == _RECOVERY_EPOCH003_EVENT1_AUTHORITY
        and value.get("operation_set")
        == list(_RECOVERY_EPOCH003_OPERATION_SET)
        and value.get("separate_explicit_authority_required") is True
        and value.get("scope_sha256")
        == _recovery_epoch003_hash_without(value, "scope_sha256")
    )


def _recovery_epoch003_freshness_policy_valid(
    value: Any,
    *,
    source: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_FRESHNESS_POLICY_KEYS
        and value.get("expires_at_utc") is None
        and value.get("validity_mode")
        == "IDENTITY_STABLE_SINGLE_EVENT1_CONSUMPTION"
        and value.get("bound_source_commit_sha1")
        == source.get("source_commit_sha1")
        and value.get("bound_source_tree_sha1")
        == source.get("source_tree_sha1")
        and value.get(
            "bound_reference_runtime_observation_external_identity_sha256"
        )
        == reference_identity.get("identity_sha256")
        and value.get("event1_path_state_at_issuance") == "ABSENT"
        and value.get("maximum_event1_consumption_count") == 1
        and value.get("invalidation_conditions")
        == list(_RECOVERY_EPOCH003_INVALIDATION_CONDITIONS)
        and value.get("reuse_allowed") is False
    )


def _recovery_epoch003_git(
    root: Path,
    *args: str,
) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _recovery_epoch003_git_changed_paths(
    root: Path,
    commit: str,
) -> list[str] | None:
    try:
        raw = subprocess.run(
            [
                "git",
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                "-z",
                commit,
            ],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
        return [
            item.decode("utf-8")
            for item in raw.split(b"\0")
            if item
        ]
    except (OSError, UnicodeError, subprocess.SubprocessError):
        return None


def _recovery_epoch003_git_raw(
    root: Path,
    revision: str,
    path: str,
) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout


def _recovery_epoch003_identity_at_base_valid(
    root: Path,
    base: str,
    identity: Mapping[str, Any],
) -> bool:
    commit = identity["publication_commit_sha1"]
    path = identity["path"]
    try:
        parents = _recovery_epoch003_git(
            root,
            "show",
            "-s",
            "--format=%P",
            commit,
        ).split()
        changed = _recovery_epoch003_git_changed_paths(root, commit)
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, base],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{base}:{path}",
        )
        raw = _recovery_epoch003_git_raw(root, base, path)
        body = load_canonical_json_bytes(raw)
        intervening = _recovery_epoch003_git(
            root,
            "rev-list",
            f"{commit}..{base}",
            "--",
            path,
        ).splitlines()
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    logical_fields = (
        "receipt_sha256",
        "reference_runtime_observation_sha256",
    )
    logical_values = [
        body[key]
        for key in logical_fields
        if key in body and isinstance(body[key], str)
    ]
    return bool(
        len(parents) == 1
        and changed == [path]
        and ancestry
        and intervening == []
        and blob == identity.get("git_blob_sha1")
        and hashlib.sha256(raw).hexdigest()
        == identity.get("raw_sha256")
        and raw == canonical_json_bytes(body) + b"\n"
        and body.get("schema_version")
        == identity.get("schema_version")
        and body.get("body_free") is True
        and len(logical_values) == 1
        and logical_values[0]
        == identity.get("logical_artifact_sha256")
        and logical_values[0]
        == _recovery_epoch003_hash_without(
            body,
            logical_fields[
                next(
                    index
                    for index, field in enumerate(logical_fields)
                    if field in body
                )
            ],
        )
    )


def _recovery_epoch003_p0_at_base_valid(
    root: Path,
    base: str,
    p0: Mapping[str, Any],
) -> bool:
    for key in ("parent_design", "receipt"):
        member = p0[key]
        path = member["path"]
        commit = member["publication_commit_sha1"]
        try:
            ancestry = subprocess.run(
                ["git", "merge-base", "--is-ancestor", commit, base],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode == 0
            blob = _recovery_epoch003_git(
                root,
                "rev-parse",
                f"{base}:{path}",
            )
            raw = _recovery_epoch003_git_raw(root, base, path)
            intervening = _recovery_epoch003_git(
                root,
                "rev-list",
                f"{commit}..{base}",
                "--",
                path,
            ).splitlines()
        except (OSError, subprocess.SubprocessError):
            return False
        if (
            not ancestry
            or intervening != []
            or blob != member.get("git_blob_sha1")
            or hashlib.sha256(raw).hexdigest()
            != member.get("raw_sha256")
        ):
            return False
        if key == "receipt":
            try:
                body = load_canonical_json_bytes(raw)
            except (UnicodeError, ValueError, json.JSONDecodeError):
                return False
            if (
                body.get("body_free") is not True
                or raw != canonical_json_bytes(body) + b"\n"
                or body.get("receipt_sha256")
                != member.get("logical_receipt_sha256")
                or body.get("receipt_sha256")
                != _recovery_epoch003_hash_without(
                    body,
                    "receipt_sha256",
                )
            ):
                return False
    return True


def _recovery_epoch003_predecessors_at_base_valid(
    root: Path,
    base: str,
    predecessors: Mapping[str, Any],
) -> bool:
    if not _recovery_epoch003_p0_at_base_valid(
        root,
        base,
        predecessors["p0_external_identity"],
    ):
        return False
    return all(
        _recovery_epoch003_identity_at_base_valid(
            root,
            base,
            predecessors[key],
        )
        for key in _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS
    )


def _recovery_epoch003_source_observation_valid(
    value: Any,
    *,
    source: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_SOURCE_OBSERVATION_KEYS
        or not isinstance(value.get("source_repository_root"), str)
        or not value.get("source_repository_root")
        or value.get("worktree_clean") is not True
    ):
        return False
    root = Path(value["source_repository_root"]).resolve()
    try:
        commit = _recovery_epoch003_git(root, "rev-parse", "HEAD")
        tree = _recovery_epoch003_git(root, "rev-parse", "HEAD^{tree}")
        clean = (
            _recovery_epoch003_git(
                root,
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(
        clean
        and value.get("source_commit_sha1") == commit
        == source.get("source_commit_sha1")
        and value.get("source_tree_sha1") == tree
        == source.get("source_tree_sha1")
    )


def _recovery_epoch003_reference_publication_valid(
    value: Any,
    *,
    reference_identity: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value)
        != _RECOVERY_EPOCH003_REFERENCE_PUBLICATION_STATE_KEYS
        or not isinstance(value.get("artifact_repository_root"), str)
        or not value.get("artifact_repository_root")
        or value.get("external_identity") != reference_identity
        or type(value.get("postfetch_body")) is not dict
        or value["postfetch_body"].get(
            "reference_runtime_observation_sha256"
        )
        != reference_identity.get("logical_artifact_sha256")
    ):
        return False
    root = Path(value["artifact_repository_root"]).resolve()
    base = value.get("admission_base_commit_sha1")
    try:
        actual_base = _recovery_epoch003_git(root, "rev-parse", "HEAD")
        actual_tree = _recovery_epoch003_git(
            root,
            "rev-parse",
            "HEAD^{tree}",
        )
        path_blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{base}:{_RECOVERY_EPOCH003_REFERENCE_PATH}",
        )
        ancestry = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                reference_identity["publication_commit_sha1"],
                str(base),
            ],
            cwd=root,
            timeout=20,
        ).returncode == 0
        raw = subprocess.run(
            [
                "git",
                "show",
                f"{base}:{_RECOVERY_EPOCH003_REFERENCE_PATH}",
            ],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
        body = load_canonical_json_bytes(raw)
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    return bool(
        base == actual_base
        and value.get("admission_base_tree_sha1") == actual_tree
        and value.get(
            "reference_publication_is_ancestor_of_admission_base"
        )
        is ancestry
        and ancestry
        and value.get("reference_path_blob_at_admission_base_sha1")
        == path_blob
        == reference_identity.get("git_blob_sha1")
        and hashlib.sha256(raw).hexdigest()
        == reference_identity.get("raw_sha256")
        and raw == canonical_json_bytes(body) + b"\n"
        and body == value.get("postfetch_body")
        and _recovery_epoch003_identity_at_base_valid(
            root,
            base,
            reference_identity,
        )
    )


def build_recovery_epoch003_operational_admission(
    state: Mapping[str, Any],
) -> dict[str, Any] | tuple[str, ...]:
    """Build the nested source/bootstrap admission carrier without effects."""

    failure = ("RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_BUILD_INVALID",)
    try:
        required = _keys(
            """
            predecessor_bindings source_closure bootstrap_closure authority
            scope freshness_policy reference_publication_state
            source_repository_observation
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        source = state.get("source_closure")
        bootstrap = state.get("bootstrap_closure")
        predecessors = state.get("predecessor_bindings")
        reference_identity = (
            predecessors.get(
                "reference_runtime_observation_external_identity"
            )
            if type(predecessors) is dict
            else None
        )
        if (
            type(source) is not dict
            or set(source) != RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS
            or source.get("schema_version")
            != RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA
            or type(bootstrap) is not dict
            or set(bootstrap)
            != RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS
            or bootstrap.get("schema_version")
            != RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA
            or validate_recovery_epoch003_source_bootstrap_contract_state(
                {
                    "source_closure": source,
                    "bootstrap_closure": bootstrap,
                }
            )
            != ()
            or not _recovery_epoch003_predecessors_valid(predecessors)
            or bootstrap.get(
                "reference_runtime_observation_external_identity"
            )
            != reference_identity
            or source.get(
                "reference_runtime_observation_external_identity_sha256"
            )
            != reference_identity.get("identity_sha256")
            or not _recovery_epoch003_admission_authority_valid(
                state.get("authority")
            )
            or not _recovery_epoch003_admission_scope_valid(
                state.get("scope"),
                source=source,
                bootstrap=bootstrap,
                reference_identity=reference_identity,
            )
            or not _recovery_epoch003_freshness_policy_valid(
                state.get("freshness_policy"),
                source=source,
                reference_identity=reference_identity,
            )
            or not _recovery_epoch003_source_observation_valid(
                state.get("source_repository_observation"),
                source=source,
            )
            or not _recovery_epoch003_reference_publication_valid(
                state.get("reference_publication_state"),
                reference_identity=reference_identity,
            )
        ):
            return failure
        artifact_root = Path(
            state["reference_publication_state"][
                "artifact_repository_root"
            ]
        ).resolve()
        base = state["reference_publication_state"][
            "admission_base_commit_sha1"
        ]
        derived = build_recovery_epoch003_source_bootstrap_closure(
            {
                "source_repository_root": state[
                    "source_repository_observation"
                ]["source_repository_root"],
                "source_commit_sha1": state[
                    "source_repository_observation"
                ]["source_commit_sha1"],
                "source_tree_sha1": state[
                    "source_repository_observation"
                ]["source_tree_sha1"],
                "reference_runtime_observation": state[
                    "reference_publication_state"
                ]["postfetch_body"],
                (
                    "reference_runtime_observation_external_identity"
                ): reference_identity,
            }
        )
        if (
            type(derived) is not dict
            or derived.get("source_closure") != source
            or derived.get("bootstrap_closure") != bootstrap
            or not _recovery_epoch003_predecessors_at_base_valid(
                artifact_root,
                base,
                predecessors,
            )
        ):
            return failure
        admission_exists = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{base}:{_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH}",
            ],
            cwd=artifact_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        event_exists = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{base}:{_RECOVERY_EPOCH003_EVENT_PATH}",
            ],
            cwd=artifact_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        if admission_exists or event_exists:
            return failure
        freshness = {
            "issued_at_utc": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            **deepcopy(state["freshness_policy"]),
            "freshness_sha256": "",
        }
        freshness["freshness_sha256"] = _recovery_epoch003_hash_without(
            freshness,
            "freshness_sha256",
        )
        effect = {
            "reference_runtime_materialization_count_delta": 1,
            "reference_runtime_observation_publication_count": 1,
            "operational_admission_publication_count": 1,
            "operational_runtime_materialization_count": 0,
            "candidate_allocation_count": 0,
            "sequence_event1_count": 0,
            "readiness_artifact_count": 0,
            "formal_reservation_count": 0,
            "formal_attempt_count": 0,
            "formal_exact134_invocation_count": 0,
            "formal_test_collection_count": 0,
            "test_execution_count": 0,
            "pytest_main_call_count": 0,
            "source_baseline_state": "UNLOCKED",
            "effect_boundary_sha256": "",
        }
        effect["effect_boundary_sha256"] = _recovery_epoch003_hash_without(
            effect,
            "effect_boundary_sha256",
        )
        result = {
            "schema_version": (
                _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA
            ),
            "logical_cycle_id": "NLS_V3_CYCLE_001",
            "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_003",
            "predecessor_bindings": deepcopy(predecessors),
            "source_closure": deepcopy(source),
            "bootstrap_closure": deepcopy(bootstrap),
            "authority": deepcopy(state["authority"]),
            "scope": deepcopy(state["scope"]),
            "freshness": freshness,
            "effect_boundary": effect,
            "owner_validation_state": "PROVED",
            "independent_verification_state": "PROVED",
            "state": (
                "SOURCE_BOOTSTRAP_REFERENCE_RUNTIME_CLOSED_AWAITING_"
                "SEPARATE_CANDIDATE_EVENT1_AUTHORITY"
            ),
            "automatic_progression": False,
            "body_free": True,
            "operational_admission_sha256": "",
        }
        result["operational_admission_sha256"] = (
            _recovery_epoch003_hash_without(
                result,
                "operational_admission_sha256",
            )
        )
        return result
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


def _recovery_epoch003_current_event_authority_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_AUTHORITY_KEYS
        and value.get("approval_kind") == "EXPLICIT_SEPARATE_APPROVAL"
        and value.get("publication_authority_token")
        == _RECOVERY_EPOCH003_EVENT1_AUTHORITY
        and value.get("transition_authority_token")
        == _RECOVERY_EPOCH003_EVENT1_AUTHORITY
        and _recovery_epoch003_external_identity_valid(
            value.get("operational_admission"),
            role="RECOVERY_EPOCH003_OPERATIONAL_ADMISSION",
            schema=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA,
            path=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH,
        )
    )


def _recovery_epoch003_current_publication_valid(
    value: Any,
    *,
    event: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_PUBLICATION_KEYS
        or _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("base_commit_sha1", ""))
        )
        is None
        or value.get("branch") != "main"
        or value.get("event_path") != _RECOVERY_EPOCH003_EVENT_PATH
        or value.get("repository_full_name") != "MassyuRed/Cocolon"
        or not isinstance(value.get("publication_state"), str)
        or not value.get("publication_state")
        or type(value.get("supporting_artifacts")) is not list
    ):
        return False
    admission = event["authority"]["operational_admission"]
    reference = event["bootstrap_closure"][
        "reference_runtime_observation_external_identity"
    ]
    expected = sorted(
        [deepcopy(admission), deepcopy(reference)],
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        ),
    )
    supporting = value["supporting_artifacts"]
    return bool(
        supporting == expected
        and value.get("supporting_artifact_count") == 2
        and value.get("expected_changed_path_count") == 1
        and value.get("supporting_artifact_set_sha256")
        == artifact_sha256(supporting)
    )


def _recovery_epoch003_current_event_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or value.get("ledger_id")
        != "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003"
        or value.get("event_id")
        != "NLS_V3_RECOVERY_EPOCH003_SEQUENCE_EVENT_01"
        or value.get("event_ordinal") != 1
        or value.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or not isinstance(value.get("candidate_version_id"), str)
        or not value.get("candidate_version_id")
        or not isinstance(value.get("state"), str)
        or not value.get("state")
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(value.get("timestamp_utc", ""))
        )
        is None
        or not isinstance(value.get("timestamp_kind"), str)
        or not value.get("timestamp_kind")
        or value.get("challenge_id")
        in _RECOVERY_EPOCH003_HISTORICAL_CHALLENGE_IDS
        or value.get("body_free") is not True
        or value.get("automatic_progression") is not False
        or value.get("event_sha256")
        != _recovery_epoch003_event_hash(value)
        or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(value.get("challenge_id", ""))
        )
        is None
    ):
        return False
    required_objects = (
        "prior_event",
        "authority",
        "p0_external_identity",
        "candidate_allocation",
        "source_closure",
        "bootstrap_closure",
        "primary_evidence_artifact",
        "publication",
    )
    if any(type(value.get(key)) is not dict for key in required_objects):
        return False
    admission = value["authority"].get("operational_admission")
    reference = value["bootstrap_closure"].get(
        "reference_runtime_observation_external_identity"
    )
    return bool(
        set(value["source_closure"])
        == RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS
        and value["source_closure"].get("schema_version")
        == RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA
        and set(value["bootstrap_closure"])
        == RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS
        and value["bootstrap_closure"].get("schema_version")
        == RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA
        and validate_recovery_epoch003_source_bootstrap_contract_state(
            {
                "source_closure": value["source_closure"],
                "bootstrap_closure": value["bootstrap_closure"],
            }
        )
        == ()
        and _recovery_epoch003_p0_valid(value["p0_external_identity"])
        and value["prior_event"] == value["p0_external_identity"]
        and _recovery_epoch003_candidate_valid(
            value["candidate_allocation"],
            event=value,
        )
        and _recovery_epoch003_current_event_authority_valid(
            value["authority"]
        )
        and value["primary_evidence_artifact"] == admission
        and _recovery_epoch003_external_identity_valid(
            reference,
            role="RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION",
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
        )
        and value["source_closure"].get(
            "reference_runtime_observation_external_identity_sha256"
        )
        == reference.get("identity_sha256")
        and _recovery_epoch003_current_publication_valid(
            value["publication"],
            event=value,
        )
        and not _recovery_epoch003_event_contains_forbidden_key(value)
    )


def _recovery_epoch003_profiled_event_valid(value: Any) -> bool:
    if type(value) is not dict:
        return False
    authority = value.get("authority")
    publication = value.get("publication")
    legacy_fixture_profile = bool(
        type(authority) is dict
        and authority.get("approval_kind")
        == "EXPLICIT_SEPARATE_AUTHORITY_FIXTURE_ONLY"
        and authority.get("publication_authority_token")
        == "FIXTURE_ONLY_UNISSUED_EVENT1_PUBLICATION_AUTHORITY"
        and authority.get("transition_authority_token")
        == "FIXTURE_ONLY_UNISSUED_EVENT1_TRANSITION_AUTHORITY"
        and value.get("timestamp_kind") == "FIXTURE_ONLY"
        and type(publication) is dict
        and publication.get("publication_state")
        == "FIXTURE_ONLY_NOT_PUBLISHED"
    )
    return (
        _recovery_epoch003_event_valid(value)
        if legacy_fixture_profile
        else _recovery_epoch003_current_event_valid(value)
    )


def validate_recovery_epoch003_sequence_event1_contract_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate immutable Epoch003 Event1 bytes without publishing an event."""

    try:
        if type(state) is not dict:
            return ("RECOVERY_EPOCH003_EVENT1_CONTRACT_INVALID",)
        if set(state) == RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS:
            if _recovery_epoch003_profiled_event_valid(state):
                return ()
            if _recovery_epoch003_event_contains_forbidden_key(state):
                return (
                    "RECOVERY_EPOCH003_EVENT1_OPERATIONAL_FACT_FORBIDDEN",
                )
            return ("RECOVERY_EPOCH003_EVENT1_CONTRACT_INVALID",)
        published = state.get("event1_at_publication")
        postfetch = state.get("event1_at_postfetch")
        if (
            type(published) is not dict
            or type(postfetch) is not dict
        ):
            return ("RECOVERY_EPOCH003_EVENT1_CONTRACT_INVALID",)
        if _recovery_epoch003_event_contains_forbidden_key(postfetch):
            return (
                "RECOVERY_EPOCH003_EVENT1_OPERATIONAL_FACT_FORBIDDEN",
            )
        if postfetch.get("challenge_id") in (
            _RECOVERY_EPOCH003_HISTORICAL_CHALLENGE_IDS
        ):
            return (
                "RECOVERY_EPOCH003_CHALLENGE_PROVENANCE_"
                "INHERITANCE_FORBIDDEN",
            )
        if (
            not _recovery_epoch003_profiled_event_valid(published)
            or not _recovery_epoch003_profiled_event_valid(postfetch)
        ):
            return ("RECOVERY_EPOCH003_EVENT1_CONTRACT_INVALID",)
        published_raw = hashlib.sha256(
            canonical_json_bytes(published) + b"\n"
        ).hexdigest()
        postfetch_raw = hashlib.sha256(
            canonical_json_bytes(postfetch) + b"\n"
        ).hexdigest()
        if (
            published != postfetch
            or state.get("event1_publication_raw_sha256")
            != published_raw
            or state.get("event1_postfetch_raw_sha256") != postfetch_raw
            or published_raw != postfetch_raw
        ):
            return (
                "RECOVERY_EPOCH003_EVENT1_IMMUTABILITY_VIOLATION",
            )
        if (
            state.get("source_closure") != published["source_closure"]
            or state.get("bootstrap_closure")
            != published["bootstrap_closure"]
        ):
            return ("RECOVERY_EPOCH003_EVENT1_CONTRACT_INVALID",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_EPOCH003_EVENT1_CONTRACT_INVALID",)


_RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_PRESTART_PREDECESSOR_"
    "CANONICAL_BYTES_REMEDIATED_FINAL_PRE_EVENT1_REFERENCE_RUNTIME_"
    "OBSERVATION_AND_OPERATIONAL_ADMISSION_V2_ISSUANCE_ONLY"
)
_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v2"
)
_RECOVERY_EPOCH003_HISTORICAL_SEED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "historical_predecessor_seed.v1"
)
_RECOVERY_EPOCH003_HISTORICAL_DERIVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "historical_receipt_byte_form_derivation_result.v1"
)
_RECOVERY_EPOCH003_P0_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001.recovery_epoch003."
    "parent_design.body_free_receipt.v1"
)
_RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT = (
    "7795950eefc4a925d18e44ac1dbc94fbd90033d0"
)
_RECOVERY_EPOCH003_HISTORICAL_ANCHOR_TREE = (
    "e7226b8a39860b7b57577c877898b317e02d6ebd"
)
_RECOVERY_EPOCH003_HISTORICAL_SEED_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id p0_external_identity
    historical_receipt_external_identities
    historical_predecessor_seed_sha256
    """
)
_RECOVERY_EPOCH003_HISTORICAL_DIRECT_KEYS = frozenset(
    _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS
)
_RECOVERY_EPOCH003_HISTORICAL_REQUEST_KEYS = _keys(
    """
    artifact_repository_root expected_artifact_head_commit_sha1
    expected_artifact_head_tree_sha1 historical_predecessor_seed
    source_repository_root expected_source_head_commit_sha1
    expected_source_head_tree_sha1 automatic_progression
    """
)
_RECOVERY_EPOCH003_POST_REFERENCE_REQUEST_KEYS = _keys(
    """
    artifact_repository_root expected_artifact_head_commit_sha1
    expected_artifact_head_tree_sha1 predecessor_bindings
    source_repository_root expected_source_head_commit_sha1
    expected_source_head_tree_sha1 automatic_progression
    """
)
_RECOVERY_EPOCH003_HISTORICAL_ROW_KEYS = _keys(
    """
    binding_path container_identity_kind container_identity_sha256
    receipt_schema_version path publication_commit_sha1 git_blob_sha1
    raw_sha256 logical_hash_field logical_artifact_sha256 actual_byte_count
    canonical_projection_byte_count_with_lf
    canonical_projection_sha256_with_lf canonical_loader_error
    byte_form_state body_free row_sha256
    """
)
_RECOVERY_EPOCH003_V2_OPERATION_SET = (
    "OPERATIONAL_ADMISSION_PUBLICATION",
)
_RECOVERY_EPOCH003_V2_INVALIDATION_CONDITIONS = (
    "REFERENCE_OR_PREDECESSOR_IDENTITY_NOT_REACHABLE_OR_BYTE_DRIFTED",
    "SOURCE_COMMIT_OR_TREE_DRIFTED_OR_WORKTREE_NOT_CLEAN",
    "SOURCE_OR_BOOTSTRAP_CLOSURE_MISMATCH",
    "HISTORICAL_RECEIPT_BYTE_FORM_CROSS_LANE_MISMATCH",
    "EVENT1_PATH_PRESENT_WITHOUT_SEPARATE_V2_CONNECTION_AUTHORITY",
)


class _RecoveryEpoch003HistoricalByteFormError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _recovery_epoch003_v2_derivation_result(
    *,
    owner: str,
    phase: str,
    input_binding_sha256: str | None,
    historical_binding_core_sha256: str | None,
    failure_code: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": _RECOVERY_EPOCH003_HISTORICAL_DERIVATION_SCHEMA,
        "derivation_owner": owner,
        "derivation_phase": phase,
        "state": "VALID" if failure_code is None else "INVALID",
        "failure_code": failure_code,
        "input_binding_sha256": input_binding_sha256,
        "historical_binding_core_sha256": (
            historical_binding_core_sha256
            if failure_code is None
            else None
        ),
        "source_baseline_state": "UNLOCKED",
        "body_free": True,
        "automatic_progression": False,
        "pytest_main_called": False,
        "reference_runtime_materialization_count_delta": 0,
        "operational_runtime_materialization_count_delta": 0,
        "reference_observation_publication_count_delta": 0,
        "operational_admission_publication_count_delta": 0,
        "runtime_publication_count_delta": 0,
        "candidate_publication_count_delta": 0,
        "event1_publication_count_delta": 0,
        "readiness_publication_count_delta": 0,
        "failure_publication_count_delta": 0,
        "reservation_count_delta": 0,
        "attempt_count_delta": 0,
        "formal_exact134_invocation_count_delta": 0,
        "formal_collection_count_delta": 0,
        "formal_execution_count_delta": 0,
    }


def _recovery_epoch003_v2_repository_root(
    value: Any,
    *,
    repository_name: str,
    expected_head: Any,
    expected_tree: Any,
) -> Path:
    if (
        not isinstance(value, str)
        or not value
        or not Path(value).is_absolute()
        or _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(expected_head)
        )
        is None
        or _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(expected_tree)
        )
        is None
    ):
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID"
        )
    try:
        root = Path(value).resolve(strict=True)
        top = Path(
            _recovery_epoch003_git(
                root,
                "rev-parse",
                "--show-toplevel",
            )
        ).resolve(strict=True)
        head = _recovery_epoch003_git(root, "rev-parse", "HEAD")
        tree = _recovery_epoch003_git(root, "rev-parse", "HEAD^{tree}")
        origin_main = _recovery_epoch003_git(
            root,
            "rev-parse",
            "origin/main",
        )
        clean = (
            _recovery_epoch003_git(
                root,
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        )
        origin = _recovery_epoch003_git(
            root,
            "remote",
            "get-url",
            "origin",
        )
    except (OSError, subprocess.SubprocessError):
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "REPOSITORY_OR_BASE_DRIFT"
        )
    if (
        top != root
        or head != expected_head
        or tree != expected_tree
        or origin_main != expected_head
        or not clean
        or origin
        not in {
            f"https://github.com/MassyuRed/{repository_name}",
            f"https://github.com/MassyuRed/{repository_name}.git",
        }
    ):
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "REPOSITORY_OR_BASE_DRIFT"
        )
    return root


def _recovery_epoch003_v2_strict_historical_json(
    raw: bytes,
) -> dict[str, Any]:
    invalid = "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_STRICT_JSON_INVALID"
    if (
        raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
        or not raw.endswith(b"\n")
        or raw.endswith(b"\n\n")
    ):
        raise _RecoveryEpoch003HistoricalByteFormError(invalid)
    try:
        text = raw[:-1].decode("utf-8", errors="strict")

        def reject_constant(value: str) -> Any:
            raise ValueError(value)

        def closed_object(
            pairs: list[tuple[str, Any]],
        ) -> dict[str, Any]:
            result: dict[str, Any] = {}
            normalized: set[str] = set()
            for key, item in pairs:
                normalized_key = unicodedata.normalize("NFC", key)
                if key in result or normalized_key in normalized:
                    raise ValueError(key)
                normalized.add(normalized_key)
                result[key] = item
            return result

        value = json.loads(
            text,
            parse_constant=reject_constant,
            object_pairs_hook=closed_object,
        )

        def stable(item: Any, depth: int = 0) -> bool:
            if depth > 100:
                return False
            if type(item) is str:
                return (
                    unicodedata.normalize("NFC", item) == item
                    and item.encode("utf-8", errors="strict").decode(
                        "utf-8"
                    )
                    == item
                )
            if type(item) is list:
                return all(stable(child, depth + 1) for child in item)
            if type(item) is dict:
                return all(
                    type(key) is str
                    and unicodedata.normalize("NFC", key) == key
                    and stable(child, depth + 1)
                    for key, child in item.items()
                )
            if type(item) is float:
                return math.isfinite(item)
            return item is None or type(item) in {bool, int}

        if type(value) is not dict or not stable(value):
            raise ValueError("historical json")
        return value
    except (
        json.JSONDecodeError,
        RecursionError,
        UnicodeError,
        ValueError,
    ):
        raise _RecoveryEpoch003HistoricalByteFormError(invalid)


def _recovery_epoch003_v2_historical_git_bytes(
    root: Path,
    *,
    validation_head: str,
    path: str,
    publication_commit_sha1: str,
    git_blob_sha1: str,
    raw_sha256: str,
) -> bytes:
    topology = (
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
        "HISTORY_TOPOLOGY_INVALID"
    )
    identity = (
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_GIT_IDENTITY_MISMATCH"
    )
    try:
        parents = _recovery_epoch003_git(
            root,
            "rev-list",
            "--parents",
            "-n",
            "1",
            publication_commit_sha1,
        ).split()
        changed = _recovery_epoch003_git_changed_paths(
            root,
            publication_commit_sha1,
        )
        if len(parents) != 2:
            raise _RecoveryEpoch003HistoricalByteFormError(topology)
        parent = parents[1]
        parent_has_path = (
            subprocess.run(
                ["git", "cat-file", "-e", f"{parent}:{path}"],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
        )
        reaches_anchor = (
            subprocess.run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    publication_commit_sha1,
                    _RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT,
                ],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
        )
        reaches_head = (
            subprocess.run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    publication_commit_sha1,
                    validation_head,
                ],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
        )
        intervening = _recovery_epoch003_git(
            root,
            "log",
            "--format=%H",
            f"{publication_commit_sha1}..{validation_head}",
            "--",
            path,
        )
        if (
            changed != [path]
            or parent_has_path
            or not reaches_anchor
            or not reaches_head
            or intervening != ""
        ):
            raise _RecoveryEpoch003HistoricalByteFormError(topology)
        publication_blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{publication_commit_sha1}:{path}",
        )
        anchor_blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{_RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT}:{path}",
        )
        head_blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{validation_head}:{path}",
        )
        publication_raw = _recovery_epoch003_git_raw(
            root,
            publication_commit_sha1,
            path,
        )
        anchor_raw = _recovery_epoch003_git_raw(
            root,
            _RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT,
            path,
        )
        head_raw = _recovery_epoch003_git_raw(
            root,
            validation_head,
            path,
        )
    except _RecoveryEpoch003HistoricalByteFormError:
        raise
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise _RecoveryEpoch003HistoricalByteFormError(topology)
    if (
        publication_blob != git_blob_sha1
        or anchor_blob != git_blob_sha1
        or head_blob != git_blob_sha1
        or publication_raw != anchor_raw
        or publication_raw != head_raw
        or hashlib.sha256(publication_raw).hexdigest() != raw_sha256
    ):
        raise _RecoveryEpoch003HistoricalByteFormError(identity)
    return publication_raw


def _recovery_epoch003_v2_historical_row(
    root: Path,
    *,
    validation_head: str,
    binding_path: str,
    container_identity_kind: str,
    container_identity_sha256: str,
    identity: Mapping[str, Any],
    logical_identity_key: str,
) -> dict[str, Any]:
    raw = _recovery_epoch003_v2_historical_git_bytes(
        root,
        validation_head=validation_head,
        path=identity["path"],
        publication_commit_sha1=identity["publication_commit_sha1"],
        git_blob_sha1=identity["git_blob_sha1"],
        raw_sha256=identity["raw_sha256"],
    )
    body = _recovery_epoch003_v2_strict_historical_json(raw)
    logical = body.get("receipt_sha256")
    if (
        body.get("body_free") is not True
        or not isinstance(body.get("schema_version"), str)
        or not body.get("schema_version")
        or body.get("schema_version")
        != (
            _RECOVERY_EPOCH003_P0_RECEIPT_SCHEMA
            if container_identity_kind == "P0_EXTERNAL_IDENTITY_V1"
            else identity.get("schema_version")
        )
        or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(str(logical)) is None
        or logical != identity.get(logical_identity_key)
        or logical != _recovery_epoch003_hash_without(
            body,
            "receipt_sha256",
        )
    ):
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_LOGICAL_HASH_MISMATCH"
        )
    try:
        load_canonical_json_bytes(raw)
    except ValueError as exc:
        if str(exc) != "CANONICAL_BYTES_MISMATCH":
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "CANONICAL_DISPOSITION_MISMATCH"
            )
    except (json.JSONDecodeError, UnicodeError):
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "CANONICAL_DISPOSITION_MISMATCH"
        )
    else:
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "CANONICAL_DISPOSITION_MISMATCH"
        )
    try:
        projection = canonical_json_bytes(body) + b"\n"
    except (TypeError, UnicodeError, ValueError):
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_PROJECTION_MISMATCH"
        )
    if projection == raw:
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "CANONICAL_DISPOSITION_MISMATCH"
        )
    row = {
        "binding_path": binding_path,
        "container_identity_kind": container_identity_kind,
        "container_identity_sha256": container_identity_sha256,
        "receipt_schema_version": body["schema_version"],
        "path": identity["path"],
        "publication_commit_sha1": identity[
            "publication_commit_sha1"
        ],
        "git_blob_sha1": identity["git_blob_sha1"],
        "raw_sha256": identity["raw_sha256"],
        "logical_hash_field": "receipt_sha256",
        "logical_artifact_sha256": logical,
        "actual_byte_count": len(raw),
        "canonical_projection_byte_count_with_lf": len(projection),
        "canonical_projection_sha256_with_lf": hashlib.sha256(
            projection
        ).hexdigest(),
        "canonical_loader_error": "CANONICAL_BYTES_MISMATCH",
        "byte_form_state": (
            "IDENTITY_BOUND_HISTORICAL_NONCANONICAL_JSON"
        ),
        "body_free": True,
        "row_sha256": "",
    }
    if set(row) != _RECOVERY_EPOCH003_HISTORICAL_ROW_KEYS:
        raise _RecoveryEpoch003HistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_PROJECTION_MISMATCH"
        )
    row["row_sha256"] = _recovery_epoch003_hash_without(
        row,
        "row_sha256",
    )
    return row


def _recovery_epoch003_v2_derive_historical_byte_form(
    state: Mapping[str, Any],
    *,
    phase: str,
) -> dict[str, Any]:
    owner = "OWNER"
    input_binding: str | None = None
    try:
        required = (
            _RECOVERY_EPOCH003_HISTORICAL_REQUEST_KEYS
            if phase == "PRESTART"
            else _RECOVERY_EPOCH003_POST_REFERENCE_REQUEST_KEYS
        )
        if (
            type(state) is not dict
            or set(state) != required
            or state.get("automatic_progression") is not False
        ):
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID"
            )
        artifact_root = _recovery_epoch003_v2_repository_root(
            state.get("artifact_repository_root"),
            repository_name="Cocolon",
            expected_head=state.get(
                "expected_artifact_head_commit_sha1"
            ),
            expected_tree=state.get(
                "expected_artifact_head_tree_sha1"
            ),
        )
        source_root = _recovery_epoch003_v2_repository_root(
            state.get("source_repository_root"),
            repository_name="mashos-api",
            expected_head=state.get("expected_source_head_commit_sha1"),
            expected_tree=state.get("expected_source_head_tree_sha1"),
        )
        if artifact_root == source_root:
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "REPOSITORY_OR_BASE_DRIFT"
            )
        try:
            anchor_tree = _recovery_epoch003_git(
                artifact_root,
                "rev-parse",
                (
                    f"{_RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT}"
                    "^{tree}"
                ),
            )
            anchor_reaches_head = (
                subprocess.run(
                    [
                        "git",
                        "merge-base",
                        "--is-ancestor",
                        _RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT,
                        state["expected_artifact_head_commit_sha1"],
                    ],
                    cwd=artifact_root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20,
                ).returncode
                == 0
            )
        except (OSError, subprocess.SubprocessError):
            anchor_tree = ""
            anchor_reaches_head = False
        if (
            anchor_tree != _RECOVERY_EPOCH003_HISTORICAL_ANCHOR_TREE
            or not anchor_reaches_head
        ):
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "REPOSITORY_OR_BASE_DRIFT"
            )

        if phase == "PRESTART":
            seed = state.get("historical_predecessor_seed")
            if (
                type(seed) is not dict
                or set(seed) != _RECOVERY_EPOCH003_HISTORICAL_SEED_KEYS
                or seed.get("schema_version")
                != _RECOVERY_EPOCH003_HISTORICAL_SEED_SCHEMA
                or seed.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
                or seed.get("recovery_epoch_id")
                != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
                or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
                    str(
                        seed.get(
                            "historical_predecessor_seed_sha256",
                            "",
                        )
                    )
                )
                is None
                or seed.get("historical_predecessor_seed_sha256")
                != _recovery_epoch003_hash_without(
                    seed,
                    "historical_predecessor_seed_sha256",
                )
            ):
                raise _RecoveryEpoch003HistoricalByteFormError(
                    "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_SEED_INVALID"
                )
            input_binding = seed["historical_predecessor_seed_sha256"]
            p0 = seed.get("p0_external_identity")
            direct = seed.get("historical_receipt_external_identities")
        else:
            predecessors = state.get("predecessor_bindings")
            if (
                type(predecessors) is not dict
                or set(predecessors) != _RECOVERY_EPOCH003_PREDECESSOR_KEYS
                or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
                    str(predecessors.get("predecessor_bindings_sha256", ""))
                )
                is None
                or predecessors.get("predecessor_bindings_sha256")
                != _recovery_epoch003_hash_without(
                    predecessors,
                    "predecessor_bindings_sha256",
                )
            ):
                raise _RecoveryEpoch003HistoricalByteFormError(
                    "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_SEED_INVALID"
                )
            input_binding = predecessors["predecessor_bindings_sha256"]
            p0 = predecessors.get("p0_external_identity")
            direct = {
                key: predecessors.get(key)
                for key in _RECOVERY_EPOCH003_HISTORICAL_DIRECT_KEYS
            }
        if (
            type(direct) is not dict
            or set(direct) != _RECOVERY_EPOCH003_HISTORICAL_DIRECT_KEYS
        ):
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "BINDING_SET_INVALID"
            )
        if not _recovery_epoch003_p0_valid(p0):
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_SEED_INVALID"
            )
        for key, identity in direct.items():
            role, schema, path, _fixed_identity = (
                _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS[key]
            )
            if (
                not _recovery_epoch003_generic_external_identity_valid(
                    identity
                )
                or identity.get("artifact_role") != role
                or identity.get("schema_version") != schema
                or identity.get("path") != path
            ):
                raise _RecoveryEpoch003HistoricalByteFormError(
                    "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                    "HISTORICAL_FALLBACK_FORBIDDEN"
                )

        _recovery_epoch003_v2_historical_git_bytes(
            artifact_root,
            validation_head=state[
                "expected_artifact_head_commit_sha1"
            ],
            path=p0["parent_design"]["path"],
            publication_commit_sha1=p0["parent_design"][
                "publication_commit_sha1"
            ],
            git_blob_sha1=p0["parent_design"]["git_blob_sha1"],
            raw_sha256=p0["parent_design"]["raw_sha256"],
        )
        bindings: list[
            tuple[str, str, str, Mapping[str, Any], str]
        ] = [
            (
                "p0_external_identity.receipt",
                "P0_EXTERNAL_IDENTITY_V1",
                p0["p0_external_identity_sha256"],
                p0["receipt"],
                "logical_receipt_sha256",
            )
        ]
        bindings.extend(
            (
                key,
                "EXACT10_EXTERNAL_IDENTITY_V1",
                direct[key]["identity_sha256"],
                direct[key],
                "logical_artifact_sha256",
            )
            for key in direct
        )
        rows = [
            _recovery_epoch003_v2_historical_row(
                artifact_root,
                validation_head=state[
                    "expected_artifact_head_commit_sha1"
                ],
                binding_path=binding_path,
                container_identity_kind=container_kind,
                container_identity_sha256=container_hash,
                identity=identity,
                logical_identity_key=logical_key,
            )
            for (
                binding_path,
                container_kind,
                container_hash,
                identity,
                logical_key,
            ) in sorted(bindings, key=lambda item: item[0])
        ]
        if len(rows) != 6:
            raise _RecoveryEpoch003HistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "BINDING_SET_INVALID"
            )
        historical_binding_core_sha256 = artifact_sha256(rows)
        _recovery_epoch003_v2_repository_root(
            str(artifact_root),
            repository_name="Cocolon",
            expected_head=state[
                "expected_artifact_head_commit_sha1"
            ],
            expected_tree=state["expected_artifact_head_tree_sha1"],
        )
        _recovery_epoch003_v2_repository_root(
            str(source_root),
            repository_name="mashos-api",
            expected_head=state["expected_source_head_commit_sha1"],
            expected_tree=state["expected_source_head_tree_sha1"],
        )
        return _recovery_epoch003_v2_derivation_result(
            owner=owner,
            phase=phase,
            input_binding_sha256=input_binding,
            historical_binding_core_sha256=(
                historical_binding_core_sha256
            ),
            failure_code=None,
        )
    except _RecoveryEpoch003HistoricalByteFormError as exc:
        return _recovery_epoch003_v2_derivation_result(
            owner=owner,
            phase=phase,
            input_binding_sha256=input_binding,
            historical_binding_core_sha256=None,
            failure_code=exc.code,
        )
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return _recovery_epoch003_v2_derivation_result(
            owner=owner,
            phase=phase,
            input_binding_sha256=input_binding,
            historical_binding_core_sha256=None,
            failure_code=(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID"
            ),
        )


def derive_recovery_epoch003_prestart_historical_receipt_byte_form_eligibility_v1(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive the actual-Git historical exact6 without side effects."""

    return _recovery_epoch003_v2_derive_historical_byte_form(
        state,
        phase="PRESTART",
    )


def _recovery_epoch003_v2_historical_seed_from_predecessors(
    predecessors: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the typed historical exact6 from complete exact8 bindings."""

    seed = {
        "schema_version": _RECOVERY_EPOCH003_HISTORICAL_SEED_SCHEMA,
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_003",
        "p0_external_identity": deepcopy(
            predecessors["p0_external_identity"]
        ),
        "historical_receipt_external_identities": {
            key: deepcopy(predecessors[key])
            for key in sorted(_RECOVERY_EPOCH003_HISTORICAL_DIRECT_KEYS)
        },
        "historical_predecessor_seed_sha256": "",
    }
    seed["historical_predecessor_seed_sha256"] = (
        _recovery_epoch003_hash_without(
            seed,
            "historical_predecessor_seed_sha256",
        )
    )
    return seed


def _recovery_epoch003_v2_cross_lane_issues(
    prestart: Mapping[str, Any],
    post_reference: Mapping[str, Any],
) -> tuple[str, ...]:
    """Require PRESTART and POST_REFERENCE to derive one actual-byte core."""

    if (
        prestart.get("state") != "VALID"
        or prestart.get("derivation_phase") != "PRESTART"
        or post_reference.get("state") != "VALID"
        or post_reference.get("derivation_phase") != "POST_REFERENCE"
        or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
            str(prestart.get("historical_binding_core_sha256"))
        )
        is None
        or prestart.get("historical_binding_core_sha256")
        != post_reference.get("historical_binding_core_sha256")
    ):
        return (
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_CROSS_LANE_MISMATCH",
        )
    return ()


def _recovery_epoch003_v2_admission_authority_valid(
    value: Any,
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_ADMISSION_AUTHORITY_KEYS
        and value.get("approval_kind") == "EXPLICIT_SEPARATE_APPROVAL"
        and value.get("admission_authority_token")
        == _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
        and value.get("publication_authority_token")
        == _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
        and value.get("authority_sha256")
        == _recovery_epoch003_hash_without(value, "authority_sha256")
    )


def _recovery_epoch003_v2_admission_scope_valid(
    value: Any,
    *,
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_ADMISSION_SCOPE_KEYS
        and value.get("artifact_repository_full_name")
        == "MassyuRed/Cocolon"
        and value.get("source_repository_full_name")
        == "MassyuRed/mashos-api"
        and value.get("source_ref") == "refs/heads/main"
        and value.get("source_commit_sha1")
        == source.get("source_commit_sha1")
        == bootstrap.get("source_commit_sha1")
        and value.get("source_tree_sha1")
        == source.get("source_tree_sha1")
        == bootstrap.get("source_tree_sha1")
        and value.get("source_closure_sha256")
        == source.get("source_closure_sha256")
        and value.get("bootstrap_closure_sha256")
        == bootstrap.get("bootstrap_closure_sha256")
        and value.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        == reference_identity.get("identity_sha256")
        and value.get("next_authority_token") is None
        and value.get("operation_set")
        == list(_RECOVERY_EPOCH003_V2_OPERATION_SET)
        and value.get("separate_explicit_authority_required") is True
        and value.get("scope_sha256")
        == _recovery_epoch003_hash_without(value, "scope_sha256")
    )


def _recovery_epoch003_v2_freshness_policy_valid(
    value: Any,
    *,
    source: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_FRESHNESS_POLICY_KEYS
        and value.get("expires_at_utc") is None
        and value.get("validity_mode")
        == "IDENTITY_STABLE_SINGLE_FUTURE_EVENT1_CAPABILITY"
        and value.get("bound_source_commit_sha1")
        == source.get("source_commit_sha1")
        and value.get("bound_source_tree_sha1")
        == source.get("source_tree_sha1")
        and value.get(
            "bound_reference_runtime_observation_external_identity_sha256"
        )
        == reference_identity.get("identity_sha256")
        and value.get("event1_path_state_at_issuance") == "ABSENT"
        and value.get("maximum_event1_consumption_count") == 1
        and value.get("invalidation_conditions")
        == list(_RECOVERY_EPOCH003_V2_INVALIDATION_CONDITIONS)
        and value.get("reuse_allowed") is False
    )


def build_recovery_epoch003_operational_admission_v2(
    state: Mapping[str, Any],
) -> dict[str, Any] | tuple[str, ...]:
    """Build v2 after a private POST_REFERENCE actual-byte derivation."""

    failure = (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_BUILD_INVALID",
    )
    try:
        required = _keys(
            """
            predecessor_bindings source_closure bootstrap_closure authority
            scope freshness_policy reference_publication_state
            source_repository_observation
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        predecessors = state.get("predecessor_bindings")
        source = state.get("source_closure")
        bootstrap = state.get("bootstrap_closure")
        reference_state = state.get("reference_publication_state")
        source_observation = state.get("source_repository_observation")
        reference_identity = (
            predecessors.get(
                "reference_runtime_observation_external_identity"
            )
            if type(predecessors) is dict
            else None
        )
        reference = (
            reference_state.get("postfetch_body")
            if type(reference_state) is dict
            else None
        )
        if (
            type(source) is not dict
            or type(bootstrap) is not dict
            or type(reference) is not dict
            or type(source_observation) is not dict
            or not _recovery_epoch003_predecessors_valid(predecessors)
            or reference.get("authority_token")
            != _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
            or bootstrap.get(
                "reference_runtime_observation_external_identity"
            )
            != reference_identity
            or source.get(
                "reference_runtime_observation_external_identity_sha256"
            )
            != reference_identity.get("identity_sha256")
            or not _recovery_epoch003_v2_admission_authority_valid(
                state.get("authority")
            )
            or not _recovery_epoch003_v2_admission_scope_valid(
                state.get("scope"),
                source=source,
                bootstrap=bootstrap,
                reference_identity=reference_identity,
            )
            or not _recovery_epoch003_v2_freshness_policy_valid(
                state.get("freshness_policy"),
                source=source,
                reference_identity=reference_identity,
            )
            or not _recovery_epoch003_source_observation_valid(
                source_observation,
                source=source,
            )
            or not _recovery_epoch003_reference_publication_valid(
                reference_state,
                reference_identity=reference_identity,
            )
            or validate_recovery_epoch003_source_bootstrap_contract_state_v2(
                {
                    "source_closure": source,
                    "bootstrap_closure": bootstrap,
                }
            )
            != ()
        ):
            return failure
        derived = _recovery_epoch003_v2_derive_historical_byte_form(
            {
                "artifact_repository_root": reference_state[
                    "artifact_repository_root"
                ],
                "expected_artifact_head_commit_sha1": reference_state[
                    "admission_base_commit_sha1"
                ],
                "expected_artifact_head_tree_sha1": reference_state[
                    "admission_base_tree_sha1"
                ],
                "predecessor_bindings": predecessors,
                "source_repository_root": source_observation[
                    "source_repository_root"
                ],
                "expected_source_head_commit_sha1": source_observation[
                    "source_commit_sha1"
                ],
                "expected_source_head_tree_sha1": source_observation[
                    "source_tree_sha1"
                ],
                "automatic_progression": False,
            },
            phase="POST_REFERENCE",
        )
        historical_binding_core_sha256 = derived.get(
            "historical_binding_core_sha256"
        )
        if (
            derived.get("state") != "VALID"
            or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
                str(historical_binding_core_sha256)
            )
            is None
        ):
            return failure
        prestart = _recovery_epoch003_v2_derive_historical_byte_form(
            {
                "artifact_repository_root": reference_state[
                    "artifact_repository_root"
                ],
                "expected_artifact_head_commit_sha1": reference_state[
                    "admission_base_commit_sha1"
                ],
                "expected_artifact_head_tree_sha1": reference_state[
                    "admission_base_tree_sha1"
                ],
                "historical_predecessor_seed": (
                    _recovery_epoch003_v2_historical_seed_from_predecessors(
                        predecessors
                    )
                ),
                "source_repository_root": source_observation[
                    "source_repository_root"
                ],
                "expected_source_head_commit_sha1": source_observation[
                    "source_commit_sha1"
                ],
                "expected_source_head_tree_sha1": source_observation[
                    "source_tree_sha1"
                ],
                "automatic_progression": False,
            },
            phase="PRESTART",
        )
        if _recovery_epoch003_v2_cross_lane_issues(prestart, derived):
            return failure
        rebuilt = build_recovery_epoch003_source_bootstrap_closure_v2(
            {
                "source_repository_root": source_observation[
                    "source_repository_root"
                ],
                "source_commit_sha1": source_observation[
                    "source_commit_sha1"
                ],
                "source_tree_sha1": source_observation[
                    "source_tree_sha1"
                ],
                "reference_runtime_observation": reference,
                "reference_runtime_observation_external_identity": (
                    reference_identity
                ),
            }
        )
        if (
            type(rebuilt) is not dict
            or rebuilt.get("source_closure") != source
            or rebuilt.get("bootstrap_closure") != bootstrap
        ):
            return failure
        artifact_root = Path(
            reference_state["artifact_repository_root"]
        ).resolve()
        base = reference_state["admission_base_commit_sha1"]
        if (
            subprocess.run(
                [
                    "git",
                    "cat-file",
                    "-e",
                    f"{base}:{_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH}",
                ],
                cwd=artifact_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
            or subprocess.run(
                [
                    "git",
                    "cat-file",
                    "-e",
                    f"{base}:{_RECOVERY_EPOCH003_EVENT_PATH}",
                ],
                cwd=artifact_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
        ):
            return failure
        freshness = {
            "issued_at_utc": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            **deepcopy(state["freshness_policy"]),
            "freshness_sha256": "",
        }
        freshness["freshness_sha256"] = _recovery_epoch003_hash_without(
            freshness,
            "freshness_sha256",
        )
        effect = {
            "reference_runtime_materialization_count_delta": 1,
            "reference_runtime_observation_publication_count": 1,
            "operational_admission_publication_count": 1,
            "operational_runtime_materialization_count": 0,
            "candidate_allocation_count": 0,
            "sequence_event1_count": 0,
            "readiness_artifact_count": 0,
            "formal_reservation_count": 0,
            "formal_attempt_count": 0,
            "formal_exact134_invocation_count": 0,
            "formal_test_collection_count": 0,
            "test_execution_count": 0,
            "pytest_main_call_count": 0,
            "source_baseline_state": "UNLOCKED",
            "effect_boundary_sha256": "",
        }
        effect["effect_boundary_sha256"] = _recovery_epoch003_hash_without(
            effect,
            "effect_boundary_sha256",
        )
        result = {
            "schema_version": (
                _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_SCHEMA
            ),
            "logical_cycle_id": "NLS_V3_CYCLE_001",
            "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_003",
            "predecessor_bindings": deepcopy(predecessors),
            "source_closure": deepcopy(source),
            "bootstrap_closure": deepcopy(bootstrap),
            "authority": deepcopy(state["authority"]),
            "scope": deepcopy(state["scope"]),
            "freshness": freshness,
            "effect_boundary": effect,
            "owner_validation_state": "PROVED",
            "independent_verification_state": "PROVED",
            "state": (
                "SOURCE_BOOTSTRAP_REFERENCE_RUNTIME_CLOSED_AWAITING_"
                "SEPARATE_V2_EVENT1_CONNECTION_DESIGN_AND_AUTHORITY"
            ),
            "automatic_progression": False,
            "body_free": True,
            "operational_admission_sha256": "",
        }
        result["operational_admission_sha256"] = (
            _recovery_epoch003_hash_without(
                result,
                "operational_admission_sha256",
            )
        )
        return result
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


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
    "RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA",
    "RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS",
    "derive_recovery_epoch003_prestart_historical_receipt_byte_form_eligibility_v1",
    "build_recovery_epoch003_operational_admission",
    "build_recovery_epoch003_operational_admission_v2",
    "validate_recovery_epoch003_sequence_event1_contract_state",
]
