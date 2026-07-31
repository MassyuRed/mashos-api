#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent publication verifier for Recovery Epoch 002.

This verifier intentionally does not import the publication owner.
"""

from copy import deepcopy
import ast
import base64
import csv
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import compat32
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any, Mapping
import unicodedata
import zipfile

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
    load_canonical_json_bytes,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT = (
    "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
)


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
_SOURCE_BASELINE_EVENT_SCHEMAS = frozenset(
    {
        _ROLE_SCHEMAS[_ROLE_SOURCE_BASELINE],
        "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v2",
    }
)


def _role_schema_valid(role: str, schema_version: Any) -> bool:
    if role == _ROLE_SOURCE_BASELINE:
        return schema_version in _SOURCE_BASELINE_EVENT_SCHEMAS
    return schema_version == _ROLE_SCHEMAS.get(role)


def _identity_role_schema_valid(
    artifact_role: Any,
    schema_version: Any,
) -> bool:
    if artifact_role in _ROLE_IDENTITY_ALIASES[_ROLE_SOURCE_BASELINE]:
        return schema_version in _SOURCE_BASELINE_EVENT_SCHEMAS
    return schema_version == _IDENTITY_ROLE_SCHEMAS.get(artifact_role)


_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

RECOVERY_EPOCH002_SHARED_PRIMITIVE_ALLOWLIST = (
    "canonical_json_bytes",
    "artifact_sha256",
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE = (
    "PARENT_ADDENDUM_DESIGN_FROZEN_RECEIPT"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_successor_parent_addendum_design_frozen_receipt.v1"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_BodyFree_Receipt_20260726.json"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS = (
    RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256 = (
    "527eb11a767582a2f86531e34e044dffa9f0ed034af91ef063c3acc33813ba6d"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS = (
    "Cocolon_前提資料/07_latest_snapshot_diff.md",
    (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_ExecutionAndClosurePlan_ReadOnly_20260723.md"
    ),
    (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
        "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
        "ParentAddendum_ReadOnly_20260726.md"
    ),
    RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH,
    (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
        "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
        "ParentAddendum_ReadOnly_Handoff_20260726.md"
    ),
)

_SUCCESS_TERMINAL_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_terminal_result.v2"
)
_SUCCESS_TERMINAL_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id authority_token_id
    event1_challenge_id formal_run_challenge_id
    formal_authority_challenge_id attempt_id candidate_version_id
    source_baseline_event_sha256 source_closure_sha256
    bootstrap_closure_sha256 formal_test_run_reservation_sha256
    terminal_checkpoint_sha256 collection_node_ids executed_node_ids states
    collection_errors exit_class exit_code signal_number timed_out
    python_runtime_identity_sha256 pytest_distribution_identity_sha256
    started_at_utc finished_at_utc body_free formal_worker_result_sha256
    outcomes counts formal_node_outcome_evidence_sha256
    formal_exact134_invocation_count
    """
)
_SUCCESS_OUTCOME_KEYS = _keys(
    """
    test_node_id source_path source_blob_sha1 source_sha256 result
    expected_closed_code actual_closed_code evidence_sha256
    """
)
_SUCCESS_COUNTS_KEYS = _keys(
    """
    collected executed passed failed errors skipped xfailed xpassed deselected
    collection_errors
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
_SUCCESS_FORMAL_CHECKPOINT_KEYS = _keys(
    """
    schema_version phase logical_cycle_id recovery_epoch_id authority_token_id
    event1_challenge_id preflight_challenge_id formal_run_challenge_id
    formal_authority_challenge_id preflight_id attempt_id reservation_ordinal
    formal_test_run_reservation_sha256 candidate_version_id
    source_baseline_event_sha256 source_closure_sha256
    bootstrap_closure_sha256 checkpoint_ordinal stage_enum observed_at_utc
    prior_checkpoint_sha256 body_free checkpoint_sha256
    """
)
_SUCCESS_FORMAL_STAGE_GRAPH = {
    "PARENT_SPAWN_INTENT_PERSISTED": ("CHILD_PROCESS_ENTRY",),
    "CHILD_PROCESS_ENTRY": ("SOURCE_BINDING_VALIDATED",),
    "SOURCE_BINDING_VALIDATED": ("RUNTIME_PROFILE_VALIDATED",),
    "RUNTIME_PROFILE_VALIDATED": ("PYTEST_IMPORT_VALIDATED",),
    "PYTEST_IMPORT_VALIDATED": ("FORMAL_PLUGIN_BOOTSTRAP_VALIDATED",),
    "FORMAL_PLUGIN_BOOTSTRAP_VALIDATED": ("PYTEST_MAIN_ENTERING",),
    "PYTEST_MAIN_ENTERING": ("COLLECTION_STARTED",),
    "COLLECTION_STARTED": ("COLLECTION_FINISHED", "COLLECTION_FAILED"),
    "COLLECTION_FINISHED": ("EXECUTION_STARTED",),
    "COLLECTION_FAILED": ("TERMINAL_RESULT_PERSISTED",),
    "EXECUTION_STARTED": ("EXECUTION_FINISHED",),
    "EXECUTION_FINISHED": ("TERMINAL_RESULT_PERSISTED",),
    "TERMINAL_RESULT_PERSISTED": (),
}
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
    "identity_sha256": (
        RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
    ),
}
_SUCCESS_ACCEPTED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "accepted_test_run_receipt.v1"
)
_SUCCESS_ACCEPTED_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    formal_worker_terminal_result formal_worker_result_sha256
    terminal_result_artifact success_lineage step_view_sha256_by_step
    proof_sources proof_source_closure_sha256 owner_validation_state
    independent_verification_state accepted body_free automatic_progression
    accepted_test_run_receipt_sha256
    """
)
_SUCCESS_LINEAGE_KEYS = _keys(
    """
    schema_version candidate_version_id source_baseline_event
    successful_reservation prior_reservation_count prior_reservation_history
    prior_reservation_history_sha256 success_lineage_sha256
    """
)
_SUCCESS_HISTORY_ROW_KEYS = _keys(
    """
    reservation_ordinal reservation_artifact attempt_id disposition_kind
    disposition_artifact
    """
)
_SUCCESS_RESERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_test_run_reservation.v1"
)
_SUCCESS_RESERVATION_KEYS = _keys(
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
_SUCCESS_UNKNOWN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "attempt_consumption_unknown_disposition.v1"
)
_SUCCESS_UNKNOWN_KEYS = _keys(
    """
    schema_version reservation_artifact attempt_id checkpoint_status
    last_valid_stage terminal_result_status exit_class exit_code signal_number
    stop_code automatic_retry body_free
    attempt_consumption_unknown_disposition_sha256
    """
)
_SUCCESS_STEP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "current_step_completion_receipt.v1"
)
_SUCCESS_STEP_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    step_number lineage current_binding actual_owners strict_contracts
    positive_proof independent_negative_proof artifact_receipt parent_binding
    completion_condition stop_conditions next_authority verdict
    automatic_progression body_free receipt_sha256
    """
)
_SUCCESS_STEP_BINDING_KEYS = _keys(
    """
    source_commit_sha1 source_tree_sha1
    source_baseline_event_identity_sha256 successor_source_closure_sha256
    canonical_current_closure_sha256 source_dependency_closure_sha256
    proof_source_closure_sha256 requirement_registry_sha256
    formal_node_registry_sha256 bootstrap_closure_sha256
    formal_node_outcome_evidence_sha256 accepted_test_run_receipt_sha256
    step_view_key step_view_sha256 full_graph_sha256
    """
)
_SUCCESS_STEP_LINEAGE_KEYS = _keys(
    """
    kind historical_disposition historical_rewrite historical_as_current
    backfill
    """
)
_SUCCESS_OWNER_KEYS = _keys(
    "path git_blob_sha1 sha256 symbol role"
)
_SUCCESS_CONTRACT_KEYS = _keys(
    """
    contract_id schema_version validator_path validator_blob_sha1
    validator_symbol invariant_ids
    """
)
_SUCCESS_ARTIFACT_RECEIPT_KEYS = _keys(
    """
    schema_version step_number required_artifact_schema_version
    owner_binding_sha256 strict_contract_binding_sha256
    requirement_registry_sha256 accepted_test_run_receipt_sha256
    formal_completion_evidence_sha256 body_free
    """
)
_SUCCESS_PARENT_BINDING_KEYS = _keys(
    """
    parent_kind parent_step_number source_baseline_event_identity_sha256
    parent_receipt_sha256
    """
)
_SUCCESS_COMPLETION_CONDITION_KEYS = _keys(
    "condition_id required satisfied evidence_sha256"
)
_SUCCESS_STOP_KEYS = _keys(
    """
    condition_id proof_scope proof_node_registry_sha256
    accepted_test_run_receipt_sha256 triggered evidence_sha256
    """
)
_SUCCESS_CANDIDATE_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 body_free
    """
)
_SUCCESS_ALL11_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.all11_completion_chain.v1"
)
_SUCCESS_ALL11_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    source_baseline_event source_closure formal_node_registry_sha256
    registry_sha256 accepted_test_run_artifact
    accepted_test_run_receipt_sha256 ordered_steps receipt_count receipts
    receipt_artifacts receipt_sha256s publication_state
    required_sequence_event_2 next_authority automatic_progression body_free
    all11_completion_chain_sha256
    """
)
_SUCCESS_REQUIRED_EVENT2_KEYS = _keys(
    """
    event_id event_name event_ordinal state prior_event_identity_sha256
    """
)
_SUCCESS_ACCEPTED_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_AcceptedTestRunExact134_"
    "BodyFree_Receipt_20260726.json"
)
_SUCCESS_STEP_PATHS = tuple(
    "EmlisAIの実装済み資料/documents/"
    f"NLSv3_Step11_Cycle001_RecoveryEpoch002_Step{step:02d}_"
    "CurrentStepCompletion_PROVED_BodyFree_Receipt_20260726.json"
    for step in range(11)
)
_SUCCESS_CANONICAL_STEP_VIEW_SHA256_BY_STEP = {
    "0": "b1d94ffcd56144e6bd22f4410e9765f885839ff0436af4532c422b17c8649a2c",
    "1": "bd1bbed69c7b43a17cd31d2002f641fbb31ea63622cbe742712b238993bff9dd",
    "2": "93fd0896af8e625380f345634a5ea4e8093c6383470cd04d74357bd39e2251ff",
    "3": "e549b461ca24dd727037c391f0b530bbfd0581bf79c0381b9fa7ccebfb291ad5",
    "4": "c6d1b4fa3511f7c5b3fb5605116befcbdd606970ef621f14cb1557da88300327",
    "5": "ebb4a91fdedb2bfb709eb410852832df0f6a3c9e30fb29b04f61b260bd413c5f",
    "6": "2de4b40332a435891aa6dbdc40c894de58ede0f72637f9f0c35e5a3160aac352",
    "7": "4decf4d69e8972b3d25cf084e63eab4e91ef77e8252b417db2cf9982ce46abf0",
    "8": "cbb30f886ff7dd299c78afb0e11a581d14ce758643799254482969ad2b3a5dba",
    "9": "ba1311563c03409f42f36ee6b9e28c2a9aad0c96f57765fed0a47edb95784a44",
    "10": "7726a2e4f9b8d357667bf44f0559de79096cbbcd6ff72c0784861b86509a78fb",
}
_SUCCESS_FROZEN_REGISTRY_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3.py"
)
_SUCCESS_FROZEN_REGISTRY_GIT_BLOB_SHA1 = (
    "c2bef050d410cd823a8605bb86a44d13793fe06e"
)
_SUCCESS_FROZEN_REGISTRY_RAW_SHA256 = (
    "b5d40243578d7b6118cafd827f07de1b181ea9c1274f686447c9d031e112a8f9"
)
_SUCCESS_FROZEN_REGISTRY_SHA256 = (
    "70a75ae561fad0846604d05b1262615be4c4a16b36b332150f8c7dc04ee71728"
)
_SUCCESS_FROZEN_FORMAL_NODE_REGISTRY_SHA256 = (
    "fbe29ce0b819563cb5db2dc79fec8277b32ae0dea5a3a5cba64230ba4a1f73cf"
)
_SUCCESS_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_closure.v1"
)
_SUCCESS_CLOSURE_KEYS = _keys(
    """
    schema_version repository_full_name source_ref source_commit_sha1
    source_tree_sha1 worktree_clean detailed_design_sha256
    parent_addendum_external_identity_sha256
    historical_d2_final_closure_sha256
    historical_d2_completion_receipt_identity_sha256
    source_dependency_closure_sha256 canonical_current_closure_sha256
    requirement_registry_sha256 formal_node_registry_sha256
    proof_source_closure_sha256 formal_test_manifest_sha256
    bootstrap_closure_sha256 success_owner_graph_sha256
    success_contract_test_manifest_sha256 source_closure_sha256
    """
)
_SUCCESS_BOOTSTRAP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_bootstrap_manifest.v2"
)
_SUCCESS_BOOTSTRAP_KEYS = _keys(
    """
    schema_version source_commit_sha1 source_tree_sha1 formal_owner_artifacts
    formal_owner_artifacts_sha256 formal_test_node_ids formal_test_manifest
    formal_test_manifest_sha256 conftest_plugin_mode
    pytest_plugins_environment_variable_removed
    pytest_entrypoint_autoload_disabled explicit_plugin_allowlist
    loaded_plugin_manifest loaded_plugin_manifest_sha256 import_manifest
    import_manifest_sha256 dependency_lock_identity installed_distributions
    installed_distributions_sha256 python_runtime_identity
    pytest_distribution_identity environment_profile
    environment_profile_sha256 preflight_argv preflight_argv_sha256
    formal_worker_argv formal_worker_argv_sha256 unclassified_import_count
    unresolved_dynamic_import_count body_free bootstrap_closure_sha256
    """
)
_SUCCESS_OWNER_GRAPH_KEYS = _keys(
    """
    schema_version owner_role_count owner_path_count owner_role_bindings
    independent_verifier_constraints success_owner_graph_sha256
    """
)
_SUCCESS_OWNER_BINDING_KEYS = _keys("role path git_blob_sha1 raw_sha256")
_SUCCESS_VERIFIER_CONSTRAINT_KEYS = _keys(
    """
    verifier_path verifier_git_blob_sha1 verifier_raw_sha256
    forbidden_owner_import_count shared_primitive_allowlist
    """
)
_SUCCESS_CONTRACT_MANIFEST_KEYS = _keys(
    """
    schema_version historical_node_count successor_node_count total_node_count
    test_files test_files_sha256 test_node_ids
    success_contract_test_manifest_sha256
    """
)
_SUCCESS_CONTRACT_TEST_FILE_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
_SUCCESS_ROLE_PATHS = {
    "sequence_lineage_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "bootstrap_closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "publication_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ),
    "readiness_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "preflight_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "formal_worker_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ),
    "checkpoint_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
    "terminal_result_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
    "formal_parent_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
    "independent_verifier": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "canonical_current_closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "reproducible_dependency_lock": (
        "ai/configs/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
    ),
    "accepted_test_run_receipt_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_accepted_test_run_receipt_v3.py"
    ),
    "current_step_completion_receipt_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_step_completion_receipt_v3.py"
    ),
    "all11_receipt_owner": (
        "ai/tools/emlis_nls_v3_recovery_epoch002_all11_receipt_issue.py"
    ),
}
_SUCCESS_D1_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_retry_lineage_and_"
    "formal_worker_bootstrap_reconciliation_red.py"
)
_SUCCESS_RED_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_post_d2_success_"
    "owner_graph_and_formal_parent_continuation_red.py"
)
_SUCCESS_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_completion_receipt.v1"
)
_LINEAGE02_SUCCESS_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_completion_receipt.v2"
)
_SUCCESS_COMPLETION_KEYS = _keys(
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
_LINEAGE02_SUCCESS_COMPLETION_KEYS = (
    _SUCCESS_COMPLETION_KEYS
    | frozenset(
        {"lineage_recovery_decision_external_identity_sha256"}
    )
)
_LINEAGE02_RECOVERY_DECISION_EXTERNAL_IDENTITY_SHA256 = (
    "9602c7cf4092594950d988c05a886c0780c32ff1eebc9fa940"
    "9d00959becad13"
)
_HISTORICAL_SUCCESSOR_SOURCE_CLOSURE_SHA256 = (
    "d4156b14eddf5e1f6a13411017bd522784b26e3e67d780203a"
    "727cc7cc1aa97f"
)
_SUCCESS_RED_KEYS = _keys(
    """
    schema_version authority_token source_entry_commit_sha1
    source_entry_tree_sha1 successor_test_file successor_node_count collected
    failed passed collection_errors owner_issue_codes independent_issue_codes
    state automatic_progression body_free receipt_sha256
    """
)
_SUCCESS_HISTORICAL_S1_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_successor_red_result.v1"
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
_SUCCESS_GREEN_KEYS = _keys(
    """
    schema_version causal_red_evidence_sha256 successor_source_commit_sha1
    successor_source_tree_sha1 successor_source_closure_sha256
    success_contract_test_manifest_sha256 test_node_ids executed_node_ids
    outcome_states counts owner_issue_codes independent_issue_codes state
    automatic_progression body_free receipt_sha256
    """
)
_SUCCESS_CANDIDATE_V2_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    historical_d2_final_closure_sha256 historical_d2_completion_receipt
    successor_source_closure_sha256 successor_completion_receipt
    allocated_at_utc candidate_allocation_sha256
    """
)
_SUCCESS_ADMISSION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id
    successor_completion_receipt successor_source_closure_sha256
    repository_full_name source_ref authority challenge_id scope
    transport_capability durable_store_capability owner_validation_state
    independent_verification_state issued_at_utc expires_at_utc state
    automatic_progression body_free operational_admission_sha256
    """
)
_SUCCESS_ADMISSION_OPTIONAL_KEYS = _keys(
    "transport_capability durable_store_capability"
)
_SUCCESS_ADMISSION_AUTHORITY_KEYS = _keys(
    """
    approval_kind admission_authority_token publication_authority_token
    authority_sha256
    """
)
_SUCCESS_ADMISSION_SCOPE_KEYS = _keys(
    """
    repository_full_name source_ref successor_source_closure_sha256
    operation_set scope_sha256
    """
)
_SUCCESS_ADMISSION_OPERATIONS = (
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
_SUCCESS_TRANSPORT_KEYS = _keys(
    """
    schema_version provider_class provider_identity_sha256
    authoritative_ref_read expected_old_compare_and_swap
    commit_parent_tree_read recursive_tree_read
    exact_changed_path_verification complete_unchanged_path_verification
    full_postfetch_verification scope_sha256 challenge_id observed_at_utc
    transport_capability_sha256
    """
)
_SUCCESS_DURABLE_KEYS = _keys(
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
_SUCCESS_EVENT_KEYS = _keys(
    """
    schema_version ledger_id event_id logical_cycle_id recovery_epoch_id
    candidate_version_id event_name event_ordinal state timestamp_utc
    timestamp_kind authority challenge_id source_closure prior_event
    primary_evidence_artifact publication automatic_progression body_free
    event_sha256 p0_external_identity candidate_allocation bootstrap_closure
    """
)
_SUCCESS_EVENT_AUTHORITY_KEYS = _keys(
    """
    approval_kind transition_authority_token publication_authority_token
    operational_admission
    """
)
_SUCCESS_EVENT_PUBLICATION_KEYS = _keys(
    """
    repository_full_name branch base_commit_sha1 event_path
    supporting_artifact_count supporting_artifacts
    supporting_artifact_set_sha256 expected_changed_path_count
    ref_update_mode publication_state transaction_capability
    """
)
_SUCCESS_EVENT_PUBLICATION_OPTIONAL_KEYS = _keys(
    "ref_update_mode transaction_capability"
)
_SUCCESS_TRANSACTION_CAPABILITY_KEYS = _keys(
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
_SUCCESS_P0_EXTERNAL_IDENTITY_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch002.p0_external_identity.v1"
)
_SUCCESS_P0_EXTERNAL_IDENTITY_SHA256 = (
    "0b5f4b0e3c3c023867a858782869c570e5a55c27cb72d8db108c309408581ce0"
)
_SUCCESS_D2_IDENTITY = {
    "artifact_role": "D2_COMPLETION_RECEIPT",
    "schema_version": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "retry_lineage_and_formal_worker_bootstrap_oracle_correction_"
        "refreeze_and_implementation_green_receipt.v1"
    ),
    "repository_full_name": "MassyuRed/Cocolon",
    "path": (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
        "PostReservationRetryLineageAndFormalWorkerBootstrapCompleteness"
        "Reconciliation_OracleExact5CollisionCorrectionRefreezeAnd"
        "Implementation_GREEN_BodyFree_Receipt_20260726.json"
    ),
    "git_blob_sha1": "d93f7e63e8a941a15f11cfdc088a8613af041e41",
    "raw_sha256": (
        "fd68f2f241fcb959def548cd2b6d8cb475415a4466c81363bfceef2ca3ac27a1"
    ),
    "logical_artifact_sha256": (
        "0af065a6499ff99164d206f6fddafafaa91f3436de191f20078e6c4aa858253c"
    ),
    "publication_commit_sha1": "8d26f3344be8b1e6a4661f958d8279a6236191d1",
    "body_free": True,
    "identity_sha256": (
        "7420f1ec60d0db3e83ae2a6fd1c900217256bc0e1b356a353bf74e0155681157"
    ),
}
_SUCCESS_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorCompletion_BodyFree_Receipt_20260726.json"
)
_LINEAGE02_SUCCESS_GREEN_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
    "SourceIdentityLineage02_Successor_GREEN_Result_20260728.json"
)
_LINEAGE02_SUCCESS_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2"
    "SourceIdentityLineage02_SourceBaselineEligibilitySuccessor"
    "Completion_BodyFree_Receipt_20260728.json"
)
_SUCCESS_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_P1OperationalAdmission_"
    "BodyFree_Receipt_20260726.json"
)
_SUCCESS_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_SequenceEvent01_"
    "SourceBaselineLocked_BodyFree_Event_20260726.json"
)
_SUCCESS_ALL11_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_All11CompletionChain_"
    "BodyFree_Chain_20260726.json"
)
_SUCCESS_MANIFEST_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_All11AtomicPublication_"
    "BodyFree_Manifest_20260726.json"
)
_SUCCESS_EVENT2_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_SequenceEvent02_"
    "Step0_10PrerequisitesProved_BodyFree_Event_20260726.json"
)
_SUCCESS_PATHS = (
    _SUCCESS_ACCEPTED_PATH,
    *_SUCCESS_STEP_PATHS,
    _SUCCESS_ALL11_PATH,
    _SUCCESS_MANIFEST_PATH,
    _SUCCESS_EVENT2_PATH,
)
_SUCCESS_CORE_PATHS = tuple(sorted(_SUCCESS_PATHS[:13]))
_SUCCESS_SUPPORTING_PATHS = tuple(sorted(_SUCCESS_PATHS[:14]))
_SUCCESS_CHANGED_PATHS = tuple(sorted(_SUCCESS_PATHS))
_SUCCESS_MANIFEST_KEYS = _keys(
    """
    schema_version candidate_version_id logical_cycle_id recovery_epoch_id
    source_baseline_event base_commit_sha1 core_artifact_count core_artifacts
    core_artifact_set_sha256 event_supporting_artifact_count
    expected_changed_path_count event_path ref_update_mode body_free
    atomic_publication_manifest_sha256
    """
)
_SUCCESS_TERMINAL_OBSERVATION_KEYS = _keys(
    """
    commit_sha1 tree_sha1 authoritative_ref_read authoritative_tree_read
    paths_present
    """
)
_SUCCESS_TRANSACTION_KEYS = _keys(
    """
    reflection_contract_version target_tree_build_count
    success_commit_build_count terminal_commit_sha1
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
    """
)
_SUCCESS_TRANSACTION_REQUIRED_KEYS = _keys(
    """
    reflection_contract_version changed_paths target_blob_sha1_by_path
    ref_update_result ref_update_attempt_count
    publication_commit_sha1_by_path write_commits
    """
)
_SUCCESS_WRITE_COMMIT_KEYS = _keys("commit_sha1 changed_paths")
_SUCCESS_ATOMIC_POSTFETCH_KEYS = _keys(
    """
    head_commit_sha1 parent_commit_sha1s target_tree_sha1
    authoritative_ref_read authoritative_head_read authoritative_parent_read
    authoritative_tree_read authoritative_recursive_tree_read changed_paths
    changed_path_proof_complete artifact_raw_sha256_by_path
    artifact_git_blob_sha1_by_path artifact_logical_sha256_by_path
    artifact_schema_by_path artifact_body_free_by_path
    publication_external_identities unchanged_path_observation
    unchanged_path_mismatches owner_issue_codes independent_issue_codes state
    """
)
_SUCCESS_CONTRACT_STATE_KEYS = _keys(
    """
    parent_addendum_external_identity parent_addendum_postfetch_evidence
    successor_closure_owner_state successor_succession_owner_state
    terminal_owner_state accepted_owner_state step_owner_state
    all11_owner_state publication_owner_state verifier_source_observation
    verifier_import_violations shared_primitive_allowlist owner_issue_codes
    independent_issue_codes publication_requested
    """
)
_SUCCESS_CLOSURE_OWNER_STATE_KEYS = _keys(
    """
    bootstrap_closure historical_d2_ancestry
    historical_d2_completion_receipt historical_d2_rewrite_requested
    parent_addendum_external_identity parent_addendum_postfetch_evidence
    source_observation success_contract_test_manifest success_owner_graph
    successor_source_closure
    """
)
_SUCCESS_SUCCESSION_OWNER_STATE_KEYS = _keys(
    """
    reflection_contract_version bootstrap_closure candidate_allocation
    candidate_operational_identity
    causal_red_evidence causal_red_evidence_artifact
    causal_red_postfetch_evidence combined_green_evidence
    combined_green_evidence_artifact combined_green_postfetch_evidence
    event1 event1_publication operational_admission_publication
    operational_admission_receipt parent_addendum_external_identity
    parent_addendum_postfetch_evidence successor_completion_publication
    successor_completion_receipt successor_source_closure
    """
)
_SUCCESS_TERMINAL_OWNER_STATE_KEYS = _keys(
    """
    reflection_contract_version checkpoint_chain independent_issue_codes
    locked_formal_node_ids
    locked_negative_code_by_node locked_source_manifest owner_issue_codes
    parity_bindings retry_history runner_closed_code_observations
    terminal_publication terminal_result
    """
)
_SUCCESS_ACCEPTED_OWNER_STATE_KEYS = _keys(
    """
    reflection_contract_version accepted_test_run_receipt issuance_requested
    retry_history_observation source_context terminal_owner_state
    terminal_publication
    """
)
_SUCCESS_STEP_OWNER_STATE_KEYS = _keys(
    """
    accepted_test_run_artifact accepted_test_run_receipt ordered_steps
    receipt_artifacts receipt_sha256s receipts source_context
    terminal_result
    """
)
_SUCCESS_ALL11_OWNER_STATE_KEYS = _keys(
    """
    accepted_test_run_artifact accepted_test_run_receipt
    all11_completion_chain ordered_steps receipt_artifacts receipt_sha256s
    receipts source_context terminal_result
    """
)
_SUCCESS_PUBLICATION_OWNER_STATE_KEYS = _keys(
    """
    reflection_contract_version artifacts_by_path atomic_publication_manifest
    candidate_identities_by_path event2 postfetch_observation
    publication_transaction terminal_commit_observation
    """
)
_SUCCESS_SOURCE_CONTEXT_KEYS = _keys(
    """
    bootstrap_closure candidate_allocation event1_artifact event1_identity
    event1_postfetch_evidence readiness_artifact readiness_identity
    readiness_postfetch_evidence successful_reservation_artifact
    successful_reservation_identity
    successful_reservation_postfetch_evidence successor_source_closure
    """
)
_SUCCESS_RETRY_HISTORY_KEYS = _keys(
    """
    consumed_attempt_ids successful_attempt_id
    successful_reservation_ordinal
    """
)
_SUCCESS_PARITY_BINDING_KEYS = _keys(
    """
    bootstrap_closure_sha256 event1_candidate_version_id
    pytest_distribution_identity_sha256 python_runtime_identity_sha256
    readiness_candidate_version_id reservation_candidate_version_id
    source_closure_sha256
    """
)
_SUCCESS_RETRY_HISTORY_OBSERVATION_KEYS = _keys(
    """
    prior_disposition_artifacts prior_disposition_postfetch_evidence
    prior_reservation_artifacts prior_reservation_history
    prior_reservation_postfetch_evidence successful_attempt_id
    successful_reservation_ordinal
    """
)
_SUCCESS_FORBIDDEN_STATE_KEYS = frozenset(
    {
        "stdout", "stderr", "traceback", "exception_message",
        "free_form_reason", "raw_environment", "absolute_temporary_path",
        "pid", "hostname", "raw_body", "raw_payload", "generated_body",
        "private_body", "private_payload", "prompt_text", "response_text",
        "private_review_data", "secret", "credential",
        "invalid_result_sha256",
    }
)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SUCCESS_VERIFIER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
)
_SUCCESS_FROZEN_IMPORT_MANIFEST_SHA256 = (
    "dd9985ebd820271e32f8a5c69de33b6dbf08121c80f16f58835b2c281add4013"
)
_SUCCESS_VERIFIER_STDLIB_ROOTS = frozenset(
    {
        "__future__",
        "ast",
        "copy",
        "datetime",
        "hashlib",
        "json",
        "pathlib",
        "re",
        "stat",
        "subprocess",
        "typing",
    }
)


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


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


def _success_plain_int(value: Any) -> bool:
    return type(value) is int


def _success_live_git_identity() -> dict[str, Any] | None:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    if (
        _SHA1_RE.fullmatch(commit) is None
        or _SHA1_RE.fullmatch(tree) is None
    ):
        return None
    return {
        "source_commit_sha1": commit,
        "source_tree_sha1": tree,
        "worktree_clean": status == "",
    }


def _success_frozen_bootstrap_fixture_valid(bootstrap: Any) -> bool:
    live_git = _success_live_git_identity()
    return (
        type(bootstrap) is dict
        and live_git is not None
        and live_git["worktree_clean"] is True
        and bootstrap.get("source_commit_sha1")
        == live_git["source_commit_sha1"]
        and bootstrap.get("source_tree_sha1")
        == live_git["source_tree_sha1"]
        and bootstrap.get("import_manifest_sha256")
        == _SUCCESS_FROZEN_IMPORT_MANIFEST_SHA256
    )


def _success_source_identity(path: str) -> dict[str, str] | None:
    if (
        not isinstance(path, str)
        or not path
        or PurePosixPath(path).is_absolute()
        or ".." in PurePosixPath(path).parts
    ):
        return None
    current = _REPO_ROOT
    for component in PurePosixPath(path).parts:
        current = current / component
        try:
            current_stat = current.lstat()
        except OSError:
            return None
        if stat.S_ISLNK(current_stat.st_mode):
            return None
    if not stat.S_ISREG(current_stat.st_mode):
        return None
    try:
        payload = current.read_bytes()
    except OSError:
        return None
    header = f"blob {len(payload)}\0".encode("ascii")
    return {
        "git_blob_sha1": hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest(),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _success_frozen_registry_rows() -> list[dict[str, Any]] | None:
    """Read the frozen registry as inert literal data, never as owner code."""

    identity = _success_source_identity(_SUCCESS_FROZEN_REGISTRY_PATH)
    if identity != {
        "git_blob_sha1": _SUCCESS_FROZEN_REGISTRY_GIT_BLOB_SHA1,
        "sha256": _SUCCESS_FROZEN_REGISTRY_RAW_SHA256,
    }:
        return None
    target = _REPO_ROOT / _SUCCESS_FROZEN_REGISTRY_PATH
    try:
        tree = ast.parse(
            target.read_text(encoding="utf-8"),
            filename=_SUCCESS_FROZEN_REGISTRY_PATH,
        )
    except (OSError, SyntaxError, UnicodeError):
        return None
    rows: Any = None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(
            isinstance(target_node, ast.Name)
            and target_node.id
            == "_RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS"
            for target_node in node.targets
        ):
            try:
                rows = ast.literal_eval(node.value)
            except (TypeError, ValueError):
                return None
            break
    if (
        type(rows) is not list
        or len(rows) != 11
        or any(
            type(row) is not dict or row.get("step_number") != step
            for step, row in enumerate(rows)
        )
    ):
        return None
    registry_material = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch001."
            "current_step_requirement_registry.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0034",
        "recovery_epoch": 1,
        "red_freeze_authority": (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
            "CURRENT_STEP_COMPLETION_RECEIPT_PROVED_ISSUANCE_AND_"
            "INDEPENDENT_PROOF_SOURCE_CLOSURE_RECONCILIATION_"
            "RED_FREEZE_ONLY"
        ),
        "detailed_design_sha256": (
            "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
        ),
        "required_sequence_event_1": "SOURCE_BASELINE_LOCKED",
        "completion_sequence_event_2": "STEP0_10_PREREQUISITES_PROVED",
        "steps": rows,
        "automatic_progression": False,
        "body_free": True,
    }
    formal_nodes = {
        str(step): row.get("formal_completion_node_ids")
        for step, row in enumerate(rows)
    }
    flattened = [
        node_id
        for step in range(11)
        for node_id in formal_nodes[str(step)]
        if isinstance(node_id, str)
    ]
    if (
        artifact_sha256(registry_material)
        != _SUCCESS_FROZEN_REGISTRY_SHA256
        or artifact_sha256({"step_nodes": formal_nodes})
        != _SUCCESS_FROZEN_FORMAL_NODE_REGISTRY_SHA256
        or len(flattened) != 134
        or len(set(flattened)) != 134
    ):
        return None
    return rows


def _success_expected_step_owners(
    registry_row: Mapping[str, Any],
) -> list[dict[str, Any]] | None:
    expected: list[dict[str, Any]] = []
    owners = registry_row.get("actual_owners")
    if type(owners) is not list:
        return None
    for owner in owners:
        if type(owner) is not dict:
            return None
        identity = _success_source_identity(owner.get("path"))
        if identity is None:
            return None
        expected.append(
            {
                "path": owner.get("path"),
                "git_blob_sha1": identity["git_blob_sha1"],
                "sha256": identity["sha256"],
                "symbol": owner.get("symbol"),
                "role": owner.get("role"),
            }
        )
    return expected


def _success_expected_step_contracts(
    registry_row: Mapping[str, Any],
) -> list[dict[str, Any]] | None:
    expected: list[dict[str, Any]] = []
    contracts = registry_row.get("strict_contracts")
    if type(contracts) is not list:
        return None
    for contract in contracts:
        if type(contract) is not dict:
            return None
        identity = _success_source_identity(contract.get("validator_path"))
        if identity is None:
            return None
        expected.append(
            {
                "contract_id": contract.get("contract_id"),
                "schema_version": contract.get("schema_version"),
                "validator_path": contract.get("validator_path"),
                "validator_blob_sha1": identity["git_blob_sha1"],
                "validator_symbol": contract.get("validator_symbol"),
                "invariant_ids": list(contract.get("invariant_ids", ())),
            }
        )
    return expected


def _success_expected_owner_graph() -> dict[str, Any] | None:
    bindings: list[dict[str, str]] = []
    for role, path in sorted(_SUCCESS_ROLE_PATHS.items()):
        identity = _success_source_identity(path)
        if identity is None:
            return None
        bindings.append(
            {
                "role": role,
                "path": path,
                "git_blob_sha1": identity["git_blob_sha1"],
                "raw_sha256": identity["sha256"],
            }
        )
    verifier = next(
        (
            row
            for row in bindings
            if row["role"] == "independent_verifier"
        ),
        None,
    )
    if verifier is None:
        return None
    graph = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "success_owner_graph.v1"
        ),
        "owner_role_count": 15,
        "owner_path_count": 12,
        "owner_role_bindings": bindings,
        "independent_verifier_constraints": {
            "verifier_path": verifier["path"],
            "verifier_git_blob_sha1": verifier["git_blob_sha1"],
            "verifier_raw_sha256": verifier["raw_sha256"],
            "forbidden_owner_import_count": 0,
            "shared_primitive_allowlist": [
                "canonical_json_bytes",
                "artifact_sha256",
            ],
        },
        "success_owner_graph_sha256": "",
    }
    graph["success_owner_graph_sha256"] = _hash_without(
        graph,
        "success_owner_graph_sha256",
    )
    return graph


def _success_test_functions(path: str) -> tuple[str, ...] | None:
    target = (_REPO_ROOT / path).resolve()
    try:
        target.relative_to(_REPO_ROOT)
        tree = ast.parse(
            target.read_text(encoding="utf-8"),
            filename=path,
        )
    except (OSError, SyntaxError, UnicodeError, ValueError):
        return None
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _success_expected_contract_manifest() -> dict[str, Any] | None:
    historical = _success_test_functions(_SUCCESS_D1_PATH)
    successor = _success_test_functions(_SUCCESS_RED_PATH)
    if (
        historical is None
        or successor is None
        or len(historical) < 5
        or len(successor) != 64
    ):
        return None
    historical_nodes = [
        *(f"{_SUCCESS_D1_PATH}::{name}" for name in historical[:4]),
        *(
            f"{_SUCCESS_D1_PATH}::{historical[-1]}[{case_id}]"
            for case_id in (
                *(f"L{number:02d}" for number in range(1, 19)),
                *(f"B{number:02d}" for number in range(1, 25)),
            )
        ),
    ]
    node_ids = [
        *historical_nodes,
        *(f"{_SUCCESS_RED_PATH}::{name}" for name in successor),
    ]
    files: list[dict[str, str]] = []
    for path in sorted((_SUCCESS_D1_PATH, _SUCCESS_RED_PATH)):
        identity = _success_source_identity(path)
        if identity is None:
            return None
        files.append(
            {
                "path": path,
                "git_blob_sha1": identity["git_blob_sha1"],
                "raw_sha256": identity["sha256"],
            }
        )
    manifest = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "success_contract_test_manifest.v1"
        ),
        "historical_node_count": 46,
        "successor_node_count": 64,
        "total_node_count": 110,
        "test_files": files,
        "test_files_sha256": artifact_sha256(files),
        "test_node_ids": node_ids,
        "success_contract_test_manifest_sha256": "",
    }
    manifest["success_contract_test_manifest_sha256"] = _hash_without(
        manifest,
        "success_contract_test_manifest_sha256",
    )
    return manifest


def _success_bootstrap_valid(
    bootstrap: Any,
    *,
    closure: Mapping[str, Any],
    graph: Mapping[str, Any],
    registry_rows: list[dict[str, Any]],
) -> bool:
    if (
        type(bootstrap) is not dict
        or set(bootstrap) != _SUCCESS_BOOTSTRAP_KEYS
        or bootstrap.get("schema_version") != _SUCCESS_BOOTSTRAP_SCHEMA
        or bootstrap.get("source_commit_sha1")
        != closure.get("source_commit_sha1")
        or bootstrap.get("source_tree_sha1")
        != closure.get("source_tree_sha1")
        or bootstrap.get("body_free") is not True
        or bootstrap.get("bootstrap_closure_sha256")
        != _hash_without(bootstrap, "bootstrap_closure_sha256")
    ):
        return False
    owner_rows = graph.get("owner_role_bindings")
    formal_nodes = [
        node_id
        for row in registry_rows
        for node_id in row["formal_completion_node_ids"]
    ]
    formal_paths = sorted(
        {node_id.partition("::")[0] for node_id in formal_nodes}
    )
    formal_manifest: list[dict[str, str]] = []
    for path in formal_paths:
        identity = _success_source_identity(path)
        if identity is None:
            return False
        formal_manifest.append(
            {
                "path": path,
                "git_blob_sha1": identity["git_blob_sha1"],
                "raw_sha256": identity["sha256"],
            }
        )
    if (
        bootstrap.get("formal_owner_artifacts") != owner_rows
        or bootstrap.get("formal_owner_artifacts_sha256")
        != artifact_sha256(owner_rows)
        or bootstrap.get("formal_test_node_ids") != formal_nodes
        or bootstrap.get("formal_test_manifest") != formal_manifest
        or bootstrap.get("formal_test_manifest_sha256")
        != artifact_sha256(formal_manifest)
        or bootstrap.get("conftest_plugin_mode")
        != "DISABLED_BY_NOCONFTEST"
        or bootstrap.get("pytest_plugins_environment_variable_removed")
        is not True
        or bootstrap.get("pytest_entrypoint_autoload_disabled") is not True
        or bootstrap.get("explicit_plugin_allowlist") != []
        or bootstrap.get("loaded_plugin_manifest") != []
        or bootstrap.get("loaded_plugin_manifest_sha256")
        != artifact_sha256([])
        or bootstrap.get("unclassified_import_count") != 0
        or type(bootstrap.get("unclassified_import_count")) is not int
        or bootstrap.get("unresolved_dynamic_import_count") != 0
        or type(bootstrap.get("unresolved_dynamic_import_count")) is not int
    ):
        return False
    lock_identity = bootstrap.get("dependency_lock_identity")
    if (
        type(lock_identity) is not dict
        or set(lock_identity) != {"identity_class", "path", "raw_sha256"}
        or lock_identity.get("identity_class")
        != "PIP_REQUIRE_HASHES_WHEEL_LOCK_V1"
        or lock_identity.get("path")
        != _SUCCESS_ROLE_PATHS["reproducible_dependency_lock"]
    ):
        return False
    lock_path = _REPO_ROOT / lock_identity["path"]
    try:
        lock_stat = lock_path.lstat()
        if (
            stat.S_ISLNK(lock_stat.st_mode)
            or not stat.S_ISREG(lock_stat.st_mode)
        ):
            return False
        lock_bytes = lock_path.read_bytes()
        dependency_lock = json.loads(lock_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return False
    if hashlib.sha256(lock_bytes).hexdigest() != lock_identity.get(
        "raw_sha256"
    ):
        return False
    if not _success_frozen_bootstrap_fixture_valid(bootstrap):
        return False
    lock_rows = dependency_lock.get("distributions")
    installed = bootstrap.get("installed_distributions")
    if type(lock_rows) is not list or type(installed) is not list:
        return False
    expected_installed = [
        {
            "normalized_distribution_name": row.get(
                "normalized_distribution_name"
            ),
            "distribution_version": row.get("distribution_version"),
            "wheel_sha256": row.get("wheel_sha256"),
            "installed_record_closure_sha256": row.get(
                "installed_record_closure_sha256"
            ),
        }
        for row in lock_rows
        if type(row) is dict
    ]
    installed_by_name = {
        row.get("normalized_distribution_name"): row
        for row in installed
        if type(row) is dict
    }
    python_identity = bootstrap.get("python_runtime_identity")
    environment = bootstrap.get("environment_profile")
    role_paths = {
        row["role"]: row["path"]
        for row in owner_rows
        if type(row) is dict and "role" in row and "path" in row
    }
    if (
        installed != expected_installed
        or dependency_lock.get("distribution_count") != len(installed)
        or bootstrap.get("installed_distributions_sha256")
        != artifact_sha256(installed)
        or bootstrap.get("pytest_distribution_identity")
        != installed_by_name.get("pytest")
        or type(python_identity) is not dict
        or set(python_identity)
        != {"executable_sha256", "implementation", "version", "build_sha256"}
        or python_identity.get("implementation") != "CPYTHON"
        or not isinstance(python_identity.get("version"), str)
        or not python_identity.get("version")
        or _SHA256_RE.fullmatch(
            str(python_identity.get("executable_sha256", ""))
        )
        is None
        or _SHA256_RE.fullmatch(
            str(python_identity.get("build_sha256", ""))
        )
        is None
        or type(environment) is not dict
        or environment
        != {
            "fixed": {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            },
            "removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"],
            "inherited_path_sha256": environment.get(
                "inherited_path_sha256"
            ),
            "lang": "C.UTF-8",
            "lc_all": "C.UTF-8",
        }
        or _SHA256_RE.fullmatch(
            str(environment.get("inherited_path_sha256", ""))
        )
        is None
        or bootstrap.get("environment_profile_sha256")
        != artifact_sha256(environment)
        or bootstrap.get("preflight_argv")
        != [
            "python", "-I", "-B", role_paths.get("preflight_owner"),
            "--preflight",
        ]
        or bootstrap.get("preflight_argv_sha256")
        != artifact_sha256(bootstrap.get("preflight_argv"))
        or bootstrap.get("formal_worker_argv")
        != [
            "python", "-I", "-B", role_paths.get("formal_worker_owner"),
            "--internal-exact134-child", "-q", "--disable-warnings",
            "--noconftest", "-p", "no:cacheprovider",
        ]
        or bootstrap.get("formal_worker_argv_sha256")
        != artifact_sha256(bootstrap.get("formal_worker_argv"))
    ):
        return False
    module_map = dependency_lock.get("module_distribution_map")
    resolution = dependency_lock.get("resolution")
    namespace_map = (
        resolution.get("namespace_module_distribution_map")
        if type(resolution) is dict
        else None
    )
    import_rows = bootstrap.get("import_manifest")
    if (
        type(module_map) is not dict
        or type(namespace_map) is not dict
        or type(import_rows) is not list
        or bootstrap.get("import_manifest_sha256")
        != artifact_sha256(import_rows)
    ):
        return False
    runtime_hash = artifact_sha256(python_identity)
    import_names: list[str] = []
    allowed_owner_paths = set(role_paths.values()) | set(formal_paths)
    for row in import_rows:
        if (
            type(row) is not dict
            or set(row)
            != {"import_name", "classification", "owner_paths", "target_identity"}
        ):
            return False
        import_name = row.get("import_name")
        owner_paths_for_import = row.get("owner_paths")
        target = row.get("target_identity")
        if (
            not isinstance(import_name, str)
            or not import_name
            or type(owner_paths_for_import) is not list
            or owner_paths_for_import
            != sorted(set(owner_paths_for_import))
            or not owner_paths_for_import
            or any(
                owner_path not in allowed_owner_paths
                for owner_path in owner_paths_for_import
            )
            or type(target) is not dict
        ):
            return False
        import_names.append(import_name)
        classification = row.get("classification")
        if classification == "FIRST_PARTY":
            path = target.get("path")
            identity = (
                _success_source_identity(path)
                if isinstance(path, str)
                else None
            )
            if (
                identity is None
                or target
                != {
                    "path": path,
                    "git_blob_sha1": identity["git_blob_sha1"],
                    "raw_sha256": identity["sha256"],
                }
            ):
                return False
            allowed_owner_paths.add(path)
        elif classification == "STDLIB_BOUND_TO_PYTHON_RUNTIME":
            if target != {
                "module_name": import_name,
                "python_runtime_identity_sha256": runtime_hash,
            }:
                return False
        elif classification == "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION":
            prefixes = [
                prefix
                for prefix in module_map
                if import_name == prefix
                or import_name.startswith(f"{prefix}.")
            ]
            if not prefixes:
                return False
            longest = max(prefixes, key=len)
            if (
                import_name == longest
                and len(namespace_map.get(longest, ())) > 1
            ):
                return False
            expected_distribution = module_map[longest]
            if target != {
                "module_name": import_name,
                **installed_by_name.get(expected_distribution, {}),
            }:
                return False
        else:
            return False
    return import_names == sorted(set(import_names))


def _success_verifier_import_violations() -> tuple[str, ...]:
    """Replay the verifier's own import boundary from its pinned source."""

    target = (_REPO_ROOT / _SUCCESS_VERIFIER_PATH).resolve()
    try:
        tree = ast.parse(target.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return ("VERIFIER_SOURCE_UNREADABLE",)
    violations: set[str] = set()
    shared_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.partition(".")[0]
                if root not in _SUCCESS_VERIFIER_STDLIB_ROOTS:
                    violations.add(f"FORBIDDEN_VERIFIER_IMPORT:{alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.partition(".")[0]
            if module == "emlis_ai_nls_v3_artifact_contract":
                shared_imports.extend(alias.name for alias in node.names)
            elif root not in _SUCCESS_VERIFIER_STDLIB_ROOTS:
                violations.add(f"FORBIDDEN_VERIFIER_IMPORT:{module}")
        elif isinstance(node, ast.Call):
            dynamic_name: str | None = None
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                dynamic_name = "__import__"
            elif (
                isinstance(node.func, ast.Attribute)
                and node.func.attr in {"import_module", "__import__"}
            ):
                dynamic_name = node.func.attr
            if dynamic_name is not None:
                violations.add(
                    f"FORBIDDEN_DYNAMIC_VERIFIER_IMPORT:{dynamic_name}"
                )
    if tuple(sorted(shared_imports)) != tuple(
        sorted(RECOVERY_EPOCH002_SHARED_PRIMITIVE_ALLOWLIST)
    ):
        violations.add("SHARED_PRIMITIVE_ALLOWLIST_INVALID")
    return tuple(sorted(violations))


def _success_candidate_identity(
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


def _success_external_identity(
    artifact: Any,
    identity: Any,
    *,
    allowed_roles: frozenset[str],
    schema: str,
    logical_hash_key: str,
) -> dict[str, Any] | None:
    if (
        type(identity) is not dict
        or set(identity) != RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
        or identity.get("artifact_role") not in allowed_roles
        or identity.get("schema_version") != schema
        or identity.get("repository_full_name") != "MassyuRed/Cocolon"
        or identity.get("body_free") is not True
        or not isinstance(identity.get("path"), str)
        or not identity.get("path")
        or _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is None
    ):
        return None
    candidate = _success_candidate_identity(
        artifact,
        role=identity["artifact_role"],
        path=identity["path"],
        logical_hash_key=logical_hash_key,
    )
    if candidate is None or candidate.get("schema_version") != schema:
        return None
    expected = {
        **candidate,
        "publication_commit_sha1": identity["publication_commit_sha1"],
        "identity_sha256": "",
    }
    expected["identity_sha256"] = _hash_without(
        expected,
        "identity_sha256",
    )
    return expected


def _success_postfetch_valid(
    evidence: Any,
    identity: Any,
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
        or set(identity) != RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
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
        identity.get("identity_sha256")
        == _hash_without(identity, "identity_sha256")
        and evidence.get("repository_full_name") == "MassyuRed/Cocolon"
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


def _success_exact1_valid(
    publication: Any,
    *,
    artifact: Any,
    roles: frozenset[str],
    schema: str,
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
        or publication.get("artifact") != artifact
        or type(publication.get("identity")) is not dict
        or publication.get("changed_paths")
        != [publication["identity"].get("path")]
        or publication.get("postfetch_state") != "POSTVERIFIED"
    ):
        return False
    expected = _success_external_identity(
        artifact,
        publication["identity"],
        allowed_roles=roles,
        schema=schema,
        logical_hash_key=logical_hash_key,
    )
    return (
        expected == publication["identity"]
        and _success_postfetch_valid(
            publication.get("postfetch_evidence"),
            publication["identity"],
        )
    )


def _success_parent_evidence_valid(identity: Any, evidence: Any) -> bool:
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
        and type(evidence) is dict
        and set(evidence)
        == _keys(
            """
            repository_full_name verification_ref verification_commit_sha1
            verification_commit_kind authoritative_ref_read
            publication_commit_sha1
            publication_reachable_from_verification_ref
            publication_parent_commit_sha1s publication_changed_paths
            receipt_absent_at_base receipt_at_publication
            markdown_at_publication receipt_at_verification_ref
            markdown_at_verification_ref parent_addendum_external_identity
            owner_issue_codes independent_issue_codes postfetch_state
            """
        )
        and evidence.get("repository_full_name") == "MassyuRed/Cocolon"
        and evidence.get("verification_ref") == "refs/heads/main"
        and _SHA1_RE.fullmatch(
            str(evidence.get("verification_commit_sha1", ""))
        )
        is not None
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


def _success_closure_owner_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_CLOSURE_OWNER_STATE_KEYS
    ):
        return False
    closure = state.get("successor_source_closure")
    bootstrap = state.get("bootstrap_closure")
    graph = state.get("success_owner_graph")
    contract_manifest = state.get("success_contract_test_manifest")
    registry_rows = _success_frozen_registry_rows()
    expected_graph = _success_expected_owner_graph()
    expected_contract_manifest = _success_expected_contract_manifest()
    live_git = _success_live_git_identity()
    if (
        registry_rows is None
        or expected_graph is None
        or expected_contract_manifest is None
        or state.get("historical_d2_rewrite_requested") is not False
        or type(closure) is not dict
        or set(closure) != _SUCCESS_CLOSURE_KEYS
        or closure.get("schema_version") != _SUCCESS_CLOSURE_SCHEMA
        or closure.get("repository_full_name") != "MassyuRed/mashos-api"
        or closure.get("source_ref") != "refs/heads/main"
        or live_git is None
        or live_git.get("worktree_clean") is not True
        or closure.get("source_commit_sha1")
        != live_git.get("source_commit_sha1")
        or closure.get("source_tree_sha1")
        != live_git.get("source_tree_sha1")
        or _SHA1_RE.fullmatch(
            str(closure.get("source_commit_sha1", ""))
        )
        is None
        or _SHA1_RE.fullmatch(
            str(closure.get("source_tree_sha1", ""))
        )
        is None
        or closure.get("worktree_clean") is not True
        or closure.get("detailed_design_sha256")
        != "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
        or closure.get("parent_addendum_external_identity_sha256")
        != RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        or closure.get("historical_d2_final_closure_sha256")
        != "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
        or closure.get(
            "historical_d2_completion_receipt_identity_sha256"
        )
        != _SUCCESS_D2_IDENTITY["identity_sha256"]
        or closure.get("requirement_registry_sha256")
        != _SUCCESS_FROZEN_REGISTRY_SHA256
        or closure.get("formal_node_registry_sha256")
        != _SUCCESS_FROZEN_FORMAL_NODE_REGISTRY_SHA256
        or any(
            _SHA256_RE.fullmatch(str(closure.get(key, ""))) is None
            for key in (
                "source_dependency_closure_sha256",
                "canonical_current_closure_sha256",
                "proof_source_closure_sha256",
                "formal_test_manifest_sha256",
                "bootstrap_closure_sha256",
                "success_owner_graph_sha256",
                "success_contract_test_manifest_sha256",
                "source_closure_sha256",
            )
        )
        or closure.get("source_closure_sha256")
        != _hash_without(closure, "source_closure_sha256")
        or graph != expected_graph
        or set(graph) != _SUCCESS_OWNER_GRAPH_KEYS
        or any(
            type(row) is not dict
            or set(row) != _SUCCESS_OWNER_BINDING_KEYS
            for row in graph["owner_role_bindings"]
        )
        or type(graph.get("independent_verifier_constraints")) is not dict
        or set(graph["independent_verifier_constraints"])
        != _SUCCESS_VERIFIER_CONSTRAINT_KEYS
        or closure.get("success_owner_graph_sha256")
        != graph.get("success_owner_graph_sha256")
        or contract_manifest != expected_contract_manifest
        or set(contract_manifest) != _SUCCESS_CONTRACT_MANIFEST_KEYS
        or any(
            type(row) is not dict
            or set(row) != _SUCCESS_CONTRACT_TEST_FILE_KEYS
            for row in contract_manifest["test_files"]
        )
        or closure.get("success_contract_test_manifest_sha256")
        != contract_manifest.get("success_contract_test_manifest_sha256")
    ):
        return False
    observation = state.get("source_observation")
    ancestry = state.get("historical_d2_ancestry")
    if (
        observation
        != {
            "source_commit_sha1": closure["source_commit_sha1"],
            "source_tree_sha1": closure["source_tree_sha1"],
            "worktree_clean": True,
        }
        or type(ancestry) is not dict
        or set(ancestry)
        != {
            "source_commit_sha1",
            "source_tree_sha1",
            "final_closure_sha256",
            "verified_ancestor",
        }
        or _SHA1_RE.fullmatch(
            str(ancestry.get("source_commit_sha1", ""))
        )
        is None
        or _SHA1_RE.fullmatch(
            str(ancestry.get("source_tree_sha1", ""))
        )
        is None
        or ancestry.get("final_closure_sha256")
        != "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
        or ancestry.get("verified_ancestor") is not True
        or ancestry.get("source_commit_sha1")
        == closure.get("source_commit_sha1")
        or ancestry.get("source_tree_sha1")
        == closure.get("source_tree_sha1")
        or state.get("historical_d2_completion_receipt")
        != _SUCCESS_D2_IDENTITY
        or state.get("parent_addendum_external_identity")
        != _SUCCESS_PARENT_IDENTITY
        or not _success_parent_evidence_valid(
            state.get("parent_addendum_external_identity"),
            state.get("parent_addendum_postfetch_evidence"),
        )
        or not _success_bootstrap_valid(
            bootstrap,
            closure=closure,
            graph=graph,
            registry_rows=registry_rows,
        )
        or closure.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or closure.get("formal_test_manifest_sha256")
        != bootstrap.get("formal_test_manifest_sha256")
    ):
        return False
    return True


def _success_parent_addendum_valid(state: Mapping[str, Any]) -> bool:
    if any(
        "PARENT_ADDENDUM_POSTFETCH_ISSUE" in state.get(key, ())
        for key in ("owner_issue_codes", "independent_issue_codes")
    ):
        return False
    identity = state.get("parent_addendum_external_identity")
    evidence = state.get("parent_addendum_postfetch_evidence")
    if not _success_parent_evidence_valid(identity, evidence):
        return False
    for owner_key in (
        "successor_closure_owner_state",
        "successor_succession_owner_state",
    ):
        owner = state.get(owner_key)
        if (
            type(owner) is not dict
            or owner.get("parent_addendum_external_identity") != identity
            or owner.get("parent_addendum_postfetch_evidence") != evidence
        ):
            return False
        closure = owner.get("successor_source_closure")
        if (
            type(closure) is not dict
            or closure.get("parent_addendum_external_identity_sha256")
            != RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        ):
            return False
    sequence = state["successor_succession_owner_state"]
    completion = sequence.get("successor_completion_receipt")
    event = sequence.get("event1")
    event_closure = (
        event.get("source_closure") if type(event) is dict else None
    )
    supporting = (
        event.get("publication", {}).get("supporting_artifacts")
        if type(event) is dict
        else None
    )
    return (
        type(completion) is dict
        and completion.get("parent_addendum_external_identity_sha256")
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        and type(event) is dict
        and "parent_addendum_external_identity_sha256" not in event
        and type(event_closure) is dict
        and event_closure.get(
            "parent_addendum_external_identity_sha256"
        )
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        and type(supporting) is list
        and not (
            len(supporting) > 1
            and _SUCCESS_PARENT_IDENTITY in supporting
        )
    )


def _success_checkpoint_chain_valid(chain: Any) -> bool:
    if type(chain) is not list or not chain:
        return False
    prior_hash: str | None = None
    prior_stage: str | None = None
    binding: tuple[Any, ...] | None = None
    binding_names = (
        "logical_cycle_id",
        "recovery_epoch_id",
        "authority_token_id",
        "event1_challenge_id",
        "preflight_challenge_id",
        "formal_run_challenge_id",
        "formal_authority_challenge_id",
        "preflight_id",
        "attempt_id",
        "reservation_ordinal",
        "formal_test_run_reservation_sha256",
        "candidate_version_id",
        "source_baseline_event_sha256",
        "source_closure_sha256",
        "bootstrap_closure_sha256",
    )
    for ordinal, row in enumerate(chain, start=1):
        if (
            type(row) is not dict
            or set(row) != _SUCCESS_FORMAL_CHECKPOINT_KEYS
            or row.get("schema_version")
            != (
                "cocolon.emlis.nls_v3.recovery_epoch002."
                "formal_worker_checkpoint.v1"
            )
            or row.get("phase") != "FORMAL_RUN"
            or row.get("checkpoint_ordinal") != ordinal
            or type(row.get("checkpoint_ordinal")) is not int
            or row.get("prior_checkpoint_sha256") != prior_hash
            or row.get("body_free") is not True
            or row.get("checkpoint_sha256")
            != _hash_without(row, "checkpoint_sha256")
        ):
            return False
        current_binding = tuple(row.get(key) for key in binding_names)
        if binding is None:
            binding = current_binding
        elif current_binding != binding:
            return False
        stage = row.get("stage_enum")
        if prior_stage is None:
            if stage != "PARENT_SPAWN_INTENT_PERSISTED":
                return False
        elif stage not in _SUCCESS_FORMAL_STAGE_GRAPH.get(prior_stage, ()):
            return False
        prior_hash = row["checkpoint_sha256"]
        prior_stage = stage
    return prior_stage == "TERMINAL_RESULT_PERSISTED"


def _success_terminal_owner_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_TERMINAL_OWNER_STATE_KEYS
    ):
        return False
    registry_rows = _success_frozen_registry_rows()
    if registry_rows is None:
        return False
    expected_nodes = [
        node_id
        for row in registry_rows
        for node_id in row["formal_completion_node_ids"]
    ]
    expected_negative_codes = {
        row["independent_negative_proof"]["test_node_id"]: (
            row["independent_negative_proof"]["expected_closed_code"]
        )
        for row in registry_rows
    }
    expected_sources: list[dict[str, str]] = []
    for source_path in sorted(
        {node_id.partition("::")[0] for node_id in expected_nodes}
    ):
        source_identity = _success_source_identity(source_path)
        if source_identity is None:
            return False
        expected_sources.append(
            {
                "path": source_path,
                "git_blob_sha1": source_identity["git_blob_sha1"],
                "raw_sha256": source_identity["sha256"],
            }
        )
    terminal = state.get("terminal_result")
    nodes = state.get("locked_formal_node_ids")
    negative_codes = state.get("locked_negative_code_by_node")
    sources = state.get("locked_source_manifest")
    outcomes = terminal.get("outcomes") if type(terminal) is dict else None
    if (
        type(terminal) is not dict
        or set(terminal) != _SUCCESS_TERMINAL_KEYS
        or terminal.get("schema_version") != _SUCCESS_TERMINAL_SCHEMA
        or terminal.get("body_free") is not True
        or terminal.get("formal_worker_result_sha256")
        != _hash_without(terminal, "formal_worker_result_sha256")
        or type(nodes) is not list
        or nodes != expected_nodes
        or terminal.get("collection_node_ids") != nodes
        or terminal.get("executed_node_ids") != nodes
        or type(negative_codes) is not dict
        or negative_codes != expected_negative_codes
        or type(sources) is not list
        or sources != expected_sources
        or type(outcomes) is not list
        or len(outcomes) != 134
    ):
        return False
    source_by_path: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if (
            type(source) is not dict
            or set(source) != {"path", "git_blob_sha1", "raw_sha256"}
            or not isinstance(source.get("path"), str)
            or _SHA1_RE.fullmatch(str(source.get("git_blob_sha1", "")))
            is None
            or _SHA256_RE.fullmatch(str(source.get("raw_sha256", "")))
            is None
        ):
            return False
        source_by_path[source["path"]] = source
    runner_codes = state.get("runner_closed_code_observations")
    if runner_codes != negative_codes:
        return False
    for node, outcome in zip(nodes, outcomes, strict=True):
        source_path = node.partition("::")[0]
        source = source_by_path.get(source_path)
        expected_code = negative_codes.get(node)
        if (
            type(outcome) is not dict
            or set(outcome) != _SUCCESS_OUTCOME_KEYS
            or outcome.get("test_node_id") != node
            or outcome.get("source_path") != source_path
            or source is None
            or outcome.get("source_blob_sha1")
            != source.get("git_blob_sha1")
            or outcome.get("source_sha256") != source.get("raw_sha256")
            or outcome.get("result") != "PASSED"
            or outcome.get("expected_closed_code") != expected_code
            or outcome.get("actual_closed_code") != expected_code
            or outcome.get("evidence_sha256")
            != _hash_without(outcome, "evidence_sha256")
        ):
            return False
    counts = terminal.get("counts")
    states = terminal.get("states")
    if (
        terminal.get("formal_node_outcome_evidence_sha256")
        != artifact_sha256(outcomes)
        or type(states) is not dict
        or states != {node: "PASSED" for node in nodes}
        or type(counts) is not dict
        or set(counts) != _SUCCESS_COUNTS_KEYS
        or any(type(value) is not int for value in counts.values())
        or counts
        != {
            "collected": 134,
            "executed": 134,
            "passed": 134,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
            "deselected": 0,
            "collection_errors": 0,
        }
        or terminal.get("collection_errors") != 0
        or terminal.get("exit_class") != "EXITED"
        or terminal.get("exit_code") != 0
        or type(terminal.get("exit_code")) is not int
        or terminal.get("signal_number") is not None
        or terminal.get("timed_out") is not False
        or terminal.get("formal_exact134_invocation_count") != 1
        or type(terminal.get("formal_exact134_invocation_count")) is not int
        or state.get("owner_issue_codes") != []
        or state.get("independent_issue_codes") != []
    ):
        return False
    chain = state.get("checkpoint_chain")
    retry = state.get("retry_history")
    parity = state.get("parity_bindings")
    if (
        not _success_checkpoint_chain_valid(chain)
        or terminal.get("terminal_checkpoint_sha256")
        != chain[-1].get("checkpoint_sha256")
        or type(retry) is not dict
        or set(retry)
        != {
            "successful_reservation_ordinal",
            "consumed_attempt_ids",
            "successful_attempt_id",
        }
        or type(retry.get("successful_reservation_ordinal")) is not int
        or retry.get("successful_reservation_ordinal") < 1
        or type(retry.get("consumed_attempt_ids")) is not list
        or any(
            type(attempt_id) is not str
            or not attempt_id
            for attempt_id in retry.get("consumed_attempt_ids")
        )
        or len(retry.get("consumed_attempt_ids"))
        != retry.get("successful_reservation_ordinal") - 1
        or len(set(retry.get("consumed_attempt_ids")))
        != len(retry.get("consumed_attempt_ids"))
        or retry.get("successful_attempt_id") != terminal.get("attempt_id")
        or retry.get("successful_attempt_id")
        in retry.get("consumed_attempt_ids")
        or type(parity) is not dict
        or set(parity) != _SUCCESS_PARITY_BINDING_KEYS
        or parity.get("source_closure_sha256")
        != terminal.get("source_closure_sha256")
        or parity.get("bootstrap_closure_sha256")
        != terminal.get("bootstrap_closure_sha256")
        or any(
            parity.get(key) != terminal.get("candidate_version_id")
            for key in (
                "event1_candidate_version_id",
                "readiness_candidate_version_id",
                "reservation_candidate_version_id",
            )
        )
        or parity.get("python_runtime_identity_sha256")
        != terminal.get("python_runtime_identity_sha256")
        or parity.get("pytest_distribution_identity_sha256")
        != terminal.get("pytest_distribution_identity_sha256")
        or not _success_exact1_valid(
            state.get("terminal_publication"),
            artifact=terminal,
            roles=frozenset(
                {"FORMAL_WORKER_TERMINAL_RESULT", "TERMINAL_RESULT"}
            ),
            schema=_SUCCESS_TERMINAL_SCHEMA,
            logical_hash_key="formal_worker_result_sha256",
        )
    ):
        return False
    return True


def _success_reservation_body_valid(
    artifact: Any,
    *,
    expected_ordinal: int,
    expected_history: list[dict[str, Any]],
) -> bool:
    return (
        type(artifact) is dict
        and set(artifact) == _SUCCESS_RESERVATION_KEYS
        and artifact.get("schema_version") == _SUCCESS_RESERVATION_SCHEMA
        and artifact.get("reservation_ordinal") == expected_ordinal
        and type(artifact.get("reservation_ordinal")) is int
        and artifact.get("prior_reservation_count")
        == len(expected_history)
        and type(artifact.get("prior_reservation_count")) is int
        and artifact.get("prior_reservation_history") == expected_history
        and artifact.get("prior_reservation_history_sha256")
        == artifact_sha256(
            {"prior_reservation_history": expected_history}
        )
        and artifact.get("reservation_state")
        == "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN"
        and artifact.get("automatic_progression") is False
        and artifact.get("body_free") is True
        and artifact.get("formal_test_run_reservation_sha256")
        == _hash_without(
            artifact,
            "formal_test_run_reservation_sha256",
        )
    )


def _success_disposition_contract(
    artifact: Any,
    *,
    disposition_kind: str,
    reservation_identity: Mapping[str, Any],
    attempt_id: str,
) -> tuple[bool, str, frozenset[str], str]:
    if disposition_kind == "FORMAL_FAILURE_ATTEMPT_PUBLISHED":
        valid = (
            type(artifact) is dict
            and set(artifact) == _SUCCESS_TERMINAL_KEYS
            and artifact.get("schema_version") == _SUCCESS_TERMINAL_SCHEMA
            and artifact.get("attempt_id") == attempt_id
            and artifact.get("body_free") is True
            and artifact.get("formal_worker_result_sha256")
            == _hash_without(
                artifact,
                "formal_worker_result_sha256",
            )
            and type(artifact.get("counts")) is dict
            and type(artifact["counts"].get("failed")) is int
            and artifact["counts"].get("failed", 0) > 0
        )
        return (
            valid,
            _SUCCESS_TERMINAL_SCHEMA,
            frozenset(
                {"FORMAL_WORKER_TERMINAL_RESULT", "TERMINAL_RESULT"}
            ),
            "formal_worker_result_sha256",
        )
    valid = (
        disposition_kind
        == "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED"
        and type(artifact) is dict
        and set(artifact) == _SUCCESS_UNKNOWN_KEYS
        and artifact.get("schema_version") == _SUCCESS_UNKNOWN_SCHEMA
        and artifact.get("reservation_artifact") == reservation_identity
        and artifact.get("attempt_id") == attempt_id
        and artifact.get("stop_code")
        == "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
        and artifact.get("automatic_retry") is False
        and artifact.get("body_free") is True
        and artifact.get(
            "attempt_consumption_unknown_disposition_sha256"
        )
        == _hash_without(
            artifact,
            "attempt_consumption_unknown_disposition_sha256",
        )
    )
    return (
        valid,
        _SUCCESS_UNKNOWN_SCHEMA,
        frozenset(
            {
                "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
                "UNKNOWN_DISPOSITION",
            }
        ),
        "attempt_consumption_unknown_disposition_sha256",
    )


def _success_accepted_lineage_valid(
    state: Mapping[str, Any],
    accepted: Mapping[str, Any],
) -> bool:
    lineage = accepted.get("success_lineage")
    observation = state.get("retry_history_observation")
    context = state.get("source_context")
    if (
        type(lineage) is not dict
        or set(lineage) != _SUCCESS_LINEAGE_KEYS
        or lineage.get("schema_version")
        != "cocolon.emlis.nls_v3.recovery_epoch002.success_lineage.v1"
        or lineage.get("success_lineage_sha256")
        != _hash_without(lineage, "success_lineage_sha256")
        or type(observation) is not dict
        or set(observation)
        != _SUCCESS_RETRY_HISTORY_OBSERVATION_KEYS
        or type(context) is not dict
        or set(context) != _SUCCESS_SOURCE_CONTEXT_KEYS
    ):
        return False
    history = lineage.get("prior_reservation_history")
    reservation_bodies = observation.get("prior_reservation_artifacts")
    disposition_bodies = observation.get("prior_disposition_artifacts")
    reservation_fetches = observation.get(
        "prior_reservation_postfetch_evidence"
    )
    disposition_fetches = observation.get(
        "prior_disposition_postfetch_evidence"
    )
    if (
        type(history) is not list
        or history != observation.get("prior_reservation_history")
        or lineage.get("prior_reservation_count") != len(history)
        or type(lineage.get("prior_reservation_count")) is not int
        or lineage.get("prior_reservation_history_sha256")
        != artifact_sha256({"prior_reservation_history": history})
        or any(
            type(rows) is not list or len(rows) != len(history)
            for rows in (
                reservation_bodies,
                disposition_bodies,
                reservation_fetches,
                disposition_fetches,
            )
        )
    ):
        return False
    attempt_ids: set[str] = set()
    identity_hashes: set[str] = set()
    previous_history: list[dict[str, Any]] = []
    for index, row in enumerate(history):
        ordinal = index + 1
        if (
            type(row) is not dict
            or set(row) != _SUCCESS_HISTORY_ROW_KEYS
            or row.get("reservation_ordinal") != ordinal
            or not isinstance(row.get("attempt_id"), str)
            or row["attempt_id"] in attempt_ids
            or row.get("disposition_kind")
            not in {
                "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
                "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
            }
        ):
            return False
        reservation_identity = row.get("reservation_artifact")
        disposition_identity = row.get("disposition_artifact")
        reservation_body = reservation_bodies[index]
        disposition_body = disposition_bodies[index]
        if (
            not _success_reservation_body_valid(
                reservation_body,
                expected_ordinal=ordinal,
                expected_history=previous_history,
            )
            or row.get("attempt_id") != reservation_body.get("attempt_id")
        ):
            return False
        expected_reservation = _success_external_identity(
            reservation_body,
            reservation_identity,
            allowed_roles=frozenset(
                {"FORMAL_TEST_RUN_RESERVATION", "RESERVATION"}
            ),
            schema=_SUCCESS_RESERVATION_SCHEMA,
            logical_hash_key="formal_test_run_reservation_sha256",
        )
        valid_disposition, schema, roles, hash_key = (
            _success_disposition_contract(
                disposition_body,
                disposition_kind=row["disposition_kind"],
                reservation_identity=reservation_identity,
                attempt_id=row["attempt_id"],
            )
        )
        expected_disposition = _success_external_identity(
            disposition_body,
            disposition_identity,
            allowed_roles=roles,
            schema=schema,
            logical_hash_key=hash_key,
        )
        if (
            expected_reservation != reservation_identity
            or not valid_disposition
            or expected_disposition != disposition_identity
        ):
            return False
        for identity in (reservation_identity, disposition_identity):
            identity_hash = identity.get("identity_sha256")
            if identity_hash in identity_hashes:
                return False
            identity_hashes.add(identity_hash)
        if not _success_postfetch_valid(
            reservation_fetches[index],
            reservation_identity,
        ):
            return False
        if not _success_postfetch_valid(
            disposition_fetches[index],
            disposition_identity,
        ):
            return False
        attempt_ids.add(row["attempt_id"])
        previous_history.append(deepcopy(row))

    successful_identity = lineage.get("successful_reservation")
    successful_body = context.get("successful_reservation_artifact")
    successful_ordinal = len(history) + 1
    successful_fetch = context.get(
        "successful_reservation_postfetch_evidence"
    )
    if (
        not _success_reservation_body_valid(
            successful_body,
            expected_ordinal=successful_ordinal,
            expected_history=history,
        )
        or _success_external_identity(
            successful_body,
            successful_identity,
            allowed_roles=frozenset(
                {"FORMAL_TEST_RUN_RESERVATION", "RESERVATION"}
            ),
            schema=_SUCCESS_RESERVATION_SCHEMA,
            logical_hash_key="formal_test_run_reservation_sha256",
        )
        != successful_identity
        or successful_identity
        != context.get("successful_reservation_identity")
        or observation.get("successful_reservation_ordinal")
        != successful_ordinal
        or type(observation.get("successful_reservation_ordinal")) is not int
        or observation.get("successful_attempt_id")
        != successful_body.get("attempt_id")
        or successful_body.get("attempt_id") in attempt_ids
        or successful_identity.get("identity_sha256") in identity_hashes
        or not _success_postfetch_valid(
            successful_fetch,
            successful_identity,
        )
    ):
        return False
    terminal = accepted.get("formal_worker_terminal_result")
    terminal_publication = state.get("terminal_publication")
    return (
        lineage.get("candidate_version_id")
        == accepted.get("candidate_version_id")
        == successful_body.get("candidate_version_id")
        == terminal.get("candidate_version_id")
        and lineage.get("source_baseline_event")
        == context.get("event1_identity")
        and lineage.get("source_baseline_event", {}).get("identity_sha256")
        == successful_body.get("source_baseline_event", {}).get(
            "identity_sha256"
        )
        and terminal.get("attempt_id") == successful_body.get("attempt_id")
        and type(terminal_publication) is dict
        and (
            state.get("reflection_contract_version")
            == RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
            or (
                terminal_publication.get("parent_commit_sha1s")
                == [successful_identity.get("publication_commit_sha1")]
                and terminal_publication.get(
                    "postfetch_evidence", {}
                ).get("base_tree_sha1")
                == successful_fetch.get("target_tree_sha1")
            )
        )
    )


def _success_accepted_owner_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_ACCEPTED_OWNER_STATE_KEYS
    ):
        return False
    accepted = state.get("accepted_test_run_receipt")
    if (
        type(accepted) is not dict
        or set(accepted) != _SUCCESS_ACCEPTED_KEYS
        or accepted.get("schema_version") != _SUCCESS_ACCEPTED_SCHEMA
        or accepted.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or accepted.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or accepted.get("owner_validation_state") != "PROVED"
        or accepted.get("independent_verification_state") != "PROVED"
        or accepted.get("accepted") is not True
        or accepted.get("body_free") is not True
        or accepted.get("automatic_progression") is not False
        or accepted.get("accepted_test_run_receipt_sha256")
        != _hash_without(
            accepted,
            "accepted_test_run_receipt_sha256",
        )
    ):
        return False
    context = state.get("source_context")
    if (
        type(context) is not dict
        or set(context) != _SUCCESS_SOURCE_CONTEXT_KEYS
        or (
            type(context.get("readiness_postfetch_evidence")) is dict
            and context["readiness_postfetch_evidence"].get(
                "postfetch_state"
            )
            in {"UNKNOWN", "PENDING"}
            and state.get("issuance_requested") is True
        )
    ):
        return False
    terminal = accepted.get("formal_worker_terminal_result")
    terminal_publication = state.get("terminal_publication")
    if (
        type(terminal) is not dict
        or set(terminal) != _SUCCESS_TERMINAL_KEYS
        or terminal.get("schema_version") != _SUCCESS_TERMINAL_SCHEMA
        or terminal.get("body_free") is not True
        or terminal.get("formal_worker_result_sha256")
        != _hash_without(terminal, "formal_worker_result_sha256")
        or not _success_exact1_valid(
            terminal_publication,
            artifact=terminal,
            roles=frozenset(
                {"FORMAL_WORKER_TERMINAL_RESULT", "TERMINAL_RESULT"}
            ),
            schema=_SUCCESS_TERMINAL_SCHEMA,
            logical_hash_key="formal_worker_result_sha256",
        )
        or accepted.get("terminal_result_artifact")
        != terminal_publication.get("identity")
        or accepted.get("formal_worker_result_sha256")
        != terminal.get("formal_worker_result_sha256")
        or terminal.get("executed_node_ids")
        != terminal.get("collection_node_ids")
        or len(terminal.get("collection_node_ids", ())) != 134
        or len(terminal.get("outcomes", ())) != 134
        or type(terminal.get("states")) is not dict
        or set(terminal["states"]) != set(terminal["collection_node_ids"])
        or any(value != "PASSED" for value in terminal["states"].values())
        or any(
            type(row) is not dict or row.get("result") != "PASSED"
            for row in terminal["outcomes"]
        )
        or type(terminal.get("counts")) is not dict
        or terminal["counts"].get("passed") != 134
        or any(
            terminal["counts"].get(key) != 0
            for key in (
                "failed",
                "errors",
                "skipped",
                "xfailed",
                "xpassed",
                "deselected",
                "collection_errors",
            )
        )
        or terminal.get("collection_errors") != 0
        or terminal.get("exit_class") != "EXITED"
        or terminal.get("exit_code") != 0
        or type(terminal.get("exit_code")) is not int
        or terminal.get("signal_number") is not None
        or terminal.get("timed_out") is not False
        or terminal.get("formal_exact134_invocation_count") != 1
        or type(terminal.get("formal_exact134_invocation_count")) is not int
    ):
        return False
    terminal_owner = state.get("terminal_owner_state")
    parity = (
        terminal_owner.get("parity_bindings")
        if type(terminal_owner) is dict
        else None
    )
    closure = context.get("successor_source_closure")
    bootstrap = context.get("bootstrap_closure")
    if (
        type(terminal_owner) is not dict
        or terminal_owner.get("terminal_result") != terminal
        or terminal_owner.get("terminal_publication")
        != terminal_publication
        or not _success_terminal_owner_valid(terminal_owner)
        or type(parity) is not dict
        or type(closure) is not dict
        or type(bootstrap) is not dict
        or terminal.get("source_closure_sha256")
        != closure.get("source_closure_sha256")
        or terminal.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or parity.get("source_closure_sha256")
        != terminal.get("source_closure_sha256")
        or parity.get("bootstrap_closure_sha256")
        != terminal.get("bootstrap_closure_sha256")
        or parity.get("python_runtime_identity_sha256")
        != terminal.get("python_runtime_identity_sha256")
        or parity.get("pytest_distribution_identity_sha256")
        != terminal.get("pytest_distribution_identity_sha256")
    ):
        return False
    event = context.get("event1_artifact")
    readiness = context.get("readiness_artifact")
    reservation = context.get("successful_reservation_artifact")
    allocation = context.get("candidate_allocation")
    candidate = accepted.get("candidate_version_id")
    if (
        any(
            type(value) is not dict
            for value in (event, readiness, reservation, allocation)
        )
        or any(
            value.get("candidate_version_id") != candidate
            for value in (terminal, event, readiness, reservation, allocation)
        )
        or parity.get("event1_candidate_version_id") != candidate
        or parity.get("readiness_candidate_version_id") != candidate
        or parity.get("reservation_candidate_version_id") != candidate
        or not _success_accepted_lineage_valid(state, accepted)
    ):
        return False
    proof_sources = accepted.get("proof_sources")
    step_views = accepted.get("step_view_sha256_by_step")
    expected_proof_sources_by_path: dict[str, dict[str, Any]] = {}
    for outcome in terminal["outcomes"]:
        source_path = outcome.get("source_path")
        source_identity = {
            "path": source_path,
            "git_blob_sha1": outcome.get("source_blob_sha1"),
            "sha256": outcome.get("source_sha256"),
        }
        if (
            not isinstance(source_path, str)
            or not source_path
            or (
                source_path in expected_proof_sources_by_path
                and expected_proof_sources_by_path[source_path]
                != source_identity
            )
        ):
            return False
        expected_proof_sources_by_path[source_path] = source_identity
    expected_proof_sources = [
        expected_proof_sources_by_path[path]
        for path in sorted(expected_proof_sources_by_path)
    ]
    return (
        type(proof_sources) is list
        and proof_sources == expected_proof_sources
        and all(
            type(row) is dict
            and set(row) == {"path", "git_blob_sha1", "sha256"}
            for row in proof_sources
        )
        and accepted.get("proof_source_closure_sha256")
        == artifact_sha256(proof_sources)
        and accepted.get("proof_source_closure_sha256")
        == closure.get("proof_source_closure_sha256")
        and step_views == _SUCCESS_CANONICAL_STEP_VIEW_SHA256_BY_STEP
    )


def _success_base_step_valid(receipt: Any, step: int) -> bool:
    return (
        type(receipt) is dict
        and set(receipt) == _SUCCESS_STEP_KEYS
        and receipt.get("schema_version") == _SUCCESS_STEP_SCHEMA
        and receipt.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and receipt.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        and receipt.get("step_number") == step
        and type(receipt.get("step_number")) is int
        and receipt.get("lineage")
        == {
            "kind": "current",
            "historical_disposition": "IMMUTABLE_NONCURRENT_EVIDENCE",
            "historical_rewrite": False,
            "historical_as_current": False,
            "backfill": False,
        }
        and set(receipt["lineage"]) == _SUCCESS_STEP_LINEAGE_KEYS
        and receipt.get("verdict") == "PROVED"
        and receipt.get("automatic_progression") is False
        and receipt.get("body_free") is True
        and receipt.get("receipt_sha256")
        == _hash_without(receipt, "receipt_sha256")
    )


def _success_step_owner_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_STEP_OWNER_STATE_KEYS
    ):
        return False
    registry_rows = _success_frozen_registry_rows()
    if registry_rows is None:
        return False
    all_formal_nodes = [
        node_id
        for row in registry_rows
        for node_id in row["formal_completion_node_ids"]
    ]
    global_stop_ids = frozenset.intersection(
        *(
            frozenset(row["stop_condition_ids"])
            for row in registry_rows
        )
    )
    accepted = state.get("accepted_test_run_receipt")
    accepted_hash = (
        accepted.get("accepted_test_run_receipt_sha256")
        if type(accepted) is dict
        else None
    )
    accepted_artifact = state.get("accepted_test_run_artifact")
    if (
        type(accepted) is not dict
        or set(accepted) != _SUCCESS_ACCEPTED_KEYS
        or accepted.get("schema_version") != _SUCCESS_ACCEPTED_SCHEMA
        or accepted.get("accepted") is not True
        or accepted.get("body_free") is not True
        or accepted.get("automatic_progression") is not False
        or accepted_hash
        != _hash_without(accepted, "accepted_test_run_receipt_sha256")
        or type(accepted_artifact) is not dict
        or set(accepted_artifact) != _SUCCESS_CANDIDATE_KEYS
        or accepted_artifact
        != _success_candidate_identity(
            accepted,
            role="ACCEPTED_TEST_RUN_RECEIPT",
            path=_SUCCESS_ACCEPTED_PATH,
            logical_hash_key="accepted_test_run_receipt_sha256",
        )
    ):
        return False
    receipts = state.get("receipts")
    artifacts = state.get("receipt_artifacts")
    hashes = state.get("receipt_sha256s")
    if (
        state.get("ordered_steps") != list(range(11))
        or type(receipts) is not list
        or len(receipts) != 11
        or type(artifacts) is not list
        or len(artifacts) != 11
        or type(hashes) is not list
        or len(hashes) != 11
        or any(
            not _success_base_step_valid(receipt, step)
            for step, receipt in enumerate(receipts)
        )
        or any(
            type(candidate) is not dict
            or set(candidate) != _SUCCESS_CANDIDATE_KEYS
            or candidate
            != _success_candidate_identity(
                receipts[step],
                role="CURRENT_STEP_COMPLETION_RECEIPT",
                path=_SUCCESS_STEP_PATHS[step],
                logical_hash_key="receipt_sha256",
            )
            for step, candidate in enumerate(artifacts)
        )
        or hashes != [receipt["receipt_sha256"] for receipt in receipts]
    ):
        return False
    success_lineage = accepted.get("success_lineage")
    event_identity = (
        success_lineage.get("source_baseline_event")
        if type(success_lineage) is dict
        else None
    )
    if type(event_identity) is not dict:
        return False
    if receipts[0].get("parent_binding") != {
        "parent_kind": "SOURCE_BASELINE_EVENT_AND_ACCEPTED",
        "parent_step_number": None,
        "source_baseline_event_identity_sha256": event_identity.get(
            "identity_sha256"
        ),
        "parent_receipt_sha256": accepted_hash,
    } or set(receipts[0]["parent_binding"]) != _SUCCESS_PARENT_BINDING_KEYS:
        return False
    for step in range(1, 11):
        parent = receipts[step].get("parent_binding")
        if (
            type(parent) is not dict
            or set(parent) != _SUCCESS_PARENT_BINDING_KEYS
            or parent
            != {
                "parent_kind": "PREVIOUS_STEP_RECEIPT",
                "parent_step_number": step - 1,
                "source_baseline_event_identity_sha256": event_identity.get(
                    "identity_sha256"
                ),
                "parent_receipt_sha256": receipts[step - 1][
                    "receipt_sha256"
                ],
            }
        ):
            return False
    context = state.get("source_context")
    closure = (
        context.get("successor_source_closure")
        if type(context) is dict
        else None
    )
    terminal = state.get("terminal_result")
    if (
        type(context) is not dict
        or set(context) != _SUCCESS_SOURCE_CONTEXT_KEYS
        or type(closure) is not dict
        or type(terminal) is not dict
        or terminal != accepted.get("formal_worker_terminal_result")
        or terminal.get("formal_worker_result_sha256")
        != accepted.get("formal_worker_result_sha256")
        or terminal.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or terminal.get("source_closure_sha256")
        != closure.get("source_closure_sha256")
        or accepted.get("proof_source_closure_sha256")
        != closure.get("proof_source_closure_sha256")
        or closure.get("requirement_registry_sha256")
        != _SUCCESS_FROZEN_REGISTRY_SHA256
        or closure.get("formal_node_registry_sha256")
        != _SUCCESS_FROZEN_FORMAL_NODE_REGISTRY_SHA256
        or terminal.get("formal_node_outcome_evidence_sha256")
        != artifact_sha256(terminal.get("outcomes"))
    ):
        return False
    outcome_rows = terminal.get("outcomes")
    if (
        type(outcome_rows) is not list
        or [row.get("test_node_id") for row in outcome_rows]
        != all_formal_nodes
        or any(
            type(row) is not dict
            or set(row) != _SUCCESS_OUTCOME_KEYS
            or row.get("evidence_sha256")
            != _hash_without(row, "evidence_sha256")
            for row in outcome_rows
        )
    ):
        return False
    outcomes = {row["test_node_id"]: row for row in outcome_rows}
    if len(outcomes) != len(outcome_rows):
        return False
    for step, (receipt, registry_row) in enumerate(
        zip(receipts, registry_rows, strict=True)
    ):
        binding = receipt.get("current_binding")
        expected_binding = {
            "source_commit_sha1": closure.get("source_commit_sha1"),
            "source_tree_sha1": closure.get("source_tree_sha1"),
            "source_baseline_event_identity_sha256": event_identity.get(
                "identity_sha256"
            ),
            "successor_source_closure_sha256": closure.get(
                "source_closure_sha256"
            ),
            "canonical_current_closure_sha256": closure.get(
                "canonical_current_closure_sha256"
            ),
            "source_dependency_closure_sha256": closure.get(
                "source_dependency_closure_sha256"
            ),
            "proof_source_closure_sha256": accepted.get(
                "proof_source_closure_sha256"
            ),
            "requirement_registry_sha256": closure.get(
                "requirement_registry_sha256"
            ),
            "formal_node_registry_sha256": closure.get(
                "formal_node_registry_sha256"
            ),
            "bootstrap_closure_sha256": closure.get(
                "bootstrap_closure_sha256"
            ),
            "formal_node_outcome_evidence_sha256": terminal.get(
                "formal_node_outcome_evidence_sha256"
            ),
            "accepted_test_run_receipt_sha256": accepted_hash,
            "step_view_key": f"step_{step}",
            "step_view_sha256": accepted.get(
                "step_view_sha256_by_step",
                {},
            ).get(str(step)),
            "full_graph_sha256": closure.get(
                "canonical_current_closure_sha256"
            ),
        }
        if (
            type(binding) is not dict
            or set(binding) != _SUCCESS_STEP_BINDING_KEYS
            or binding != expected_binding
        ):
            return False
        owners = receipt.get("actual_owners")
        contracts = receipt.get("strict_contracts")
        expected_owners = _success_expected_step_owners(registry_row)
        expected_contracts = _success_expected_step_contracts(registry_row)
        if (
            expected_owners is None
            or expected_contracts is None
            or owners != expected_owners
            or contracts != expected_contracts
            or any(
                type(owner) is not dict
                or set(owner) != _SUCCESS_OWNER_KEYS
                for owner in owners
            )
            or any(
                type(contract) is not dict
                or set(contract) != _SUCCESS_CONTRACT_KEYS
                for contract in contracts
            )
        ):
            return False
        artifact_receipt = receipt.get("artifact_receipt")
        completion = receipt.get("completion_condition")
        stops = receipt.get("stop_conditions")
        positive = receipt.get("positive_proof")
        negative = receipt.get("independent_negative_proof")
        positive_node = registry_row["positive_proof"]["test_node_id"]
        negative_contract = registry_row["independent_negative_proof"]
        negative_node = negative_contract["test_node_id"]
        formal_nodes = list(registry_row["formal_completion_node_ids"])
        completion_hash = artifact_sha256(
            {
                "step_number": step,
                "formal_node_ids": formal_nodes,
                "outcome_evidence_sha256s": [
                    outcomes[node_id]["evidence_sha256"]
                    for node_id in formal_nodes
                ],
                "accepted_test_run_receipt_sha256": accepted_hash,
            }
        )
        expected_stops: list[dict[str, Any]] = []
        for condition_id in registry_row["stop_condition_ids"]:
            is_global = condition_id in global_stop_ids
            proof_nodes = all_formal_nodes if is_global else formal_nodes
            proof_scope = (
                "GLOBAL_EXACT134"
                if is_global
                else "STEP_EXACT_REQUIRED_NODES"
            )
            proof_node_registry_sha256 = artifact_sha256(
                {"node_ids": proof_nodes}
            )
            expected_stops.append(
                {
                    "condition_id": condition_id,
                    "proof_scope": proof_scope,
                    "proof_node_registry_sha256": (
                        proof_node_registry_sha256
                    ),
                    "accepted_test_run_receipt_sha256": accepted_hash,
                    "triggered": False,
                    "evidence_sha256": artifact_sha256(
                        {
                            "condition_id": condition_id,
                            "proof_scope": proof_scope,
                            "proof_node_registry_sha256": (
                                proof_node_registry_sha256
                            ),
                            "outcome_evidence_sha256s": [
                                outcomes[node_id]["evidence_sha256"]
                                for node_id in proof_nodes
                            ],
                            "accepted_test_run_receipt_sha256": (
                                accepted_hash
                            ),
                            "triggered": False,
                        }
                    ),
                }
            )
        expected_next_authority = (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            f"SUCCESS_CANDIDATE_STEP{step + 1:02d}_"
            "GENERATION_SAME_APPROVED_PHASE"
            if step < 10
            else "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            "SUCCESS_EXACT15_PUBLICATION_AND_POSTVERIFY_ONLY"
        )
        if (
            type(artifact_receipt) is not dict
            or set(artifact_receipt) != _SUCCESS_ARTIFACT_RECEIPT_KEYS
            or artifact_receipt.get("schema_version")
            != (
                "cocolon.emlis.nls_v3.recovery_epoch002."
                "current_step_artifact_evidence.v1"
            )
            or artifact_receipt.get("step_number") != step
            or type(artifact_receipt.get("step_number")) is not int
            or artifact_receipt.get(
                "required_artifact_schema_version"
            )
            != registry_row["artifact_receipt_schema_version"]
            or artifact_receipt.get("owner_binding_sha256")
            != artifact_sha256(expected_owners)
            or artifact_receipt.get("strict_contract_binding_sha256")
            != artifact_sha256(expected_contracts)
            or artifact_receipt.get("requirement_registry_sha256")
            != _SUCCESS_FROZEN_REGISTRY_SHA256
            or artifact_receipt.get(
                "accepted_test_run_receipt_sha256"
            )
            != accepted_hash
            or artifact_receipt.get("formal_completion_evidence_sha256")
            != completion_hash
            or artifact_receipt.get("body_free") is not True
            or type(positive) is not dict
            or set(positive) != _SUCCESS_OUTCOME_KEYS
            or positive != outcomes.get(positive_node)
            or positive.get("test_node_id") != positive_node
            or positive.get("result") != "PASSED"
            or positive.get("evidence_sha256")
            != _hash_without(positive, "evidence_sha256")
            or type(negative) is not dict
            or set(negative) != _SUCCESS_OUTCOME_KEYS
            or negative != outcomes.get(negative_node)
            or negative.get("test_node_id") != negative_node
            or negative.get("result") != "PASSED"
            or negative.get("expected_closed_code")
            != negative_contract["expected_closed_code"]
            or negative.get("actual_closed_code")
            != negative_contract["expected_closed_code"]
            or negative.get("evidence_sha256")
            != _hash_without(negative, "evidence_sha256")
            or type(completion) is not dict
            or set(completion) != _SUCCESS_COMPLETION_CONDITION_KEYS
            or completion.get("condition_id")
            != registry_row["completion_condition_ids"][0]
            or completion.get("required") is not True
            or completion.get("satisfied") is not True
            or completion.get("evidence_sha256") != completion_hash
            or type(stops) is not list
            or any(
                type(stop) is not dict
                or set(stop) != _SUCCESS_STOP_KEYS
                or stop.get("accepted_test_run_receipt_sha256")
                != accepted_hash
                or stop.get("triggered") is not False
                or _SHA256_RE.fullmatch(
                    str(stop.get("evidence_sha256", ""))
                )
                is None
                for stop in stops
            )
            or stops != expected_stops
            or receipt.get("next_authority")
            != expected_next_authority
        ):
            return False
    return True


def _success_all11_owner_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_ALL11_OWNER_STATE_KEYS
    ):
        return False
    step_state = {
        key: state[key] for key in _SUCCESS_STEP_OWNER_STATE_KEYS
    }
    if not _success_step_owner_valid(step_state):
        return False
    chain = state.get("all11_completion_chain")
    accepted = state.get("accepted_test_run_receipt")
    receipts = state.get("receipts")
    artifacts = state.get("receipt_artifacts")
    hashes = state.get("receipt_sha256s")
    if (
        type(chain) is not dict
        or set(chain) != _SUCCESS_ALL11_KEYS
        or chain.get("schema_version") != _SUCCESS_ALL11_SCHEMA
        or chain.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or chain.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or chain.get("body_free") is not True
        or chain.get("automatic_progression") is not False
        or chain.get("all11_completion_chain_sha256")
        != _hash_without(chain, "all11_completion_chain_sha256")
        or type(accepted) is not dict
        or type(receipts) is not list
        or len(receipts) != 11
        or type(artifacts) is not list
        or len(artifacts) != 11
        or type(hashes) is not list
        or len(hashes) != 11
        or state.get("ordered_steps") != list(range(11))
        or chain.get("receipt_count") != 11
        or type(chain.get("receipt_count")) is not int
        or chain.get("ordered_steps") != list(range(11))
        or chain.get("receipts") != receipts
        or chain.get("receipt_artifacts") != artifacts
        or chain.get("receipt_sha256s") != hashes
        or hashes != [receipt.get("receipt_sha256") for receipt in receipts]
        or any(
            not _success_base_step_valid(receipt, step)
            for step, receipt in enumerate(receipts)
        )
        or any(
            type(identity) is not dict
            or set(identity) != _SUCCESS_CANDIDATE_KEYS
            or identity.get("artifact_role")
            != "CURRENT_STEP_COMPLETION_RECEIPT"
            or identity.get("logical_artifact_sha256")
            != receipts[step].get("receipt_sha256")
            or identity
            != _success_candidate_identity(
                receipts[step],
                role="CURRENT_STEP_COMPLETION_RECEIPT",
                path=_SUCCESS_STEP_PATHS[step],
                logical_hash_key="receipt_sha256",
            )
            for step, identity in enumerate(artifacts)
        )
        or chain.get("accepted_test_run_artifact")
        != state.get("accepted_test_run_artifact")
        or chain.get("accepted_test_run_receipt_sha256")
        != accepted.get("accepted_test_run_receipt_sha256")
        or chain.get("accepted_test_run_artifact", {}).get(
            "logical_artifact_sha256"
        )
        != accepted.get("accepted_test_run_receipt_sha256")
        or chain.get("candidate_version_id")
        != accepted.get("candidate_version_id")
    ):
        return False
    success_lineage = accepted.get("success_lineage")
    event_identity = (
        success_lineage.get("source_baseline_event")
        if type(success_lineage) is dict
        else None
    )
    context = state.get("source_context")
    closure = (
        context.get("successor_source_closure")
        if type(context) is dict
        else None
    )
    required_event2 = chain.get("required_sequence_event_2")
    return (
        type(context) is dict
        and set(context) == _SUCCESS_SOURCE_CONTEXT_KEYS
        and chain.get("source_baseline_event") == event_identity
        and chain.get("source_closure") == closure
        and chain.get("registry_sha256")
        == closure.get("requirement_registry_sha256")
        and chain.get("formal_node_registry_sha256")
        == closure.get("formal_node_registry_sha256")
        and type(required_event2) is dict
        and set(required_event2) == _SUCCESS_REQUIRED_EVENT2_KEYS
        and required_event2
        == {
            "event_id": "recovery_epoch002_event_02",
            "event_name": "STEP0_10_PREREQUISITES_PROVED",
            "event_ordinal": 2,
            "state": "STEP0_10_PREREQUISITES_PROVED",
            "prior_event_identity_sha256": event_identity.get(
                "identity_sha256"
            ),
        }
        and chain.get("publication_state") == "PUBLISHED_ATOMIC"
        and chain.get("next_authority")
        == (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            "P2_SEPARATE_APPROVAL_ONLY"
        )
    )


def _success_direct_artifact_valid(
    artifact: Any,
    identity: Any,
    postfetch: Any,
    *,
    role: str,
    schema: str,
    path: str,
    logical_hash_key: str,
) -> bool:
    return (
        type(identity) is dict
        and identity.get("path") == path
        and type(postfetch) is dict
        and _success_external_identity(
            artifact,
            identity,
            allowed_roles=frozenset({role}),
            schema=schema,
            logical_hash_key=logical_hash_key,
        )
        == identity
        and _success_postfetch_valid(postfetch, identity)
    )


def _success_completion_contract(
    completion: Any,
) -> tuple[str, str, str] | None:
    if type(completion) is not dict:
        return None
    if (
        completion.get("schema_version") == _SUCCESS_COMPLETION_SCHEMA
        and set(completion) == _SUCCESS_COMPLETION_KEYS
    ):
        return (
            _SUCCESS_COMPLETION_SCHEMA,
            (
                "EmlisAIの実装済み資料/documents/"
                "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
                "Successor_GREEN_Result_20260726.json"
            ),
            _SUCCESS_COMPLETION_PATH,
        )
    if (
        completion.get("schema_version")
        == _LINEAGE02_SUCCESS_COMPLETION_SCHEMA
        and set(completion) == _LINEAGE02_SUCCESS_COMPLETION_KEYS
        and completion.get(
            "lineage_recovery_decision_external_identity_sha256"
        )
        == _LINEAGE02_RECOVERY_DECISION_EXTERNAL_IDENTITY_SHA256
    ):
        return (
            _LINEAGE02_SUCCESS_COMPLETION_SCHEMA,
            _LINEAGE02_SUCCESS_GREEN_PATH,
            _LINEAGE02_SUCCESS_COMPLETION_PATH,
        )
    return None


def _success_completion_identity_valid(identity: Any) -> bool:
    return (
        type(identity) is dict
        and set(identity) == RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
        and identity.get("artifact_role")
        == "SUCCESSOR_COMPLETION_RECEIPT"
        and (
            identity.get("schema_version"),
            identity.get("path"),
        )
        in {
            (
                _SUCCESS_COMPLETION_SCHEMA,
                _SUCCESS_COMPLETION_PATH,
            ),
            (
                _LINEAGE02_SUCCESS_COMPLETION_SCHEMA,
                _LINEAGE02_SUCCESS_COMPLETION_PATH,
            ),
        }
        and identity.get("body_free") is True
        and identity.get("identity_sha256")
        == _hash_without(identity, "identity_sha256")
    )


def _success_completion_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_SUCCESSION_OWNER_STATE_KEYS
        or state.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
    ):
        return False
    closure = state.get("successor_source_closure")
    completion = state.get("successor_completion_receipt")
    red = state.get("causal_red_evidence_artifact")
    red_identity = state.get("causal_red_evidence")
    green = state.get("combined_green_evidence_artifact")
    green_identity = state.get("combined_green_evidence")
    expected_contract_manifest = _success_expected_contract_manifest()
    completion_contract = _success_completion_contract(completion)
    if completion_contract is None:
        return False
    completion_schema, green_path, completion_path = completion_contract
    if (
        type(closure) is not dict
        or closure.get("source_closure_sha256")
        == _HISTORICAL_SUCCESSOR_SOURCE_CLOSURE_SHA256
        or completion.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or completion.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or completion.get("historical_d2_final_closure_sha256")
        != (
            "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
        )
        or completion.get(
            "historical_d2_completion_receipt_identity_sha256"
        )
        != _SUCCESS_D2_IDENTITY["identity_sha256"]
        or completion.get("parent_addendum_external_identity_sha256")
        != RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        or completion.get("successor_source_closure_sha256")
        != closure.get("source_closure_sha256")
        or completion.get("state")
        != "SUCCESSOR_SOURCE_BASELINE_ELIGIBILITY_PROVED"
        or completion.get("automatic_progression") is not False
        or completion.get("body_free") is not True
        or completion.get("receipt_sha256")
        != _hash_without(completion, "receipt_sha256")
        or type(red) is not dict
        or set(red) != _SUCCESS_RED_KEYS
        or red.get("schema_version")
        != _SUCCESS_HISTORICAL_S1_SCHEMA
        or red.get("authority_token")
        != _SUCCESS_HISTORICAL_S1_AUTHORITY
        or red.get("source_entry_commit_sha1")
        != "5eb4d6d1f0a18a715f33305e7fb7cfe92be42d74"
        or red.get("source_entry_tree_sha1")
        != "b7ad6dd2dbc90e9db296f8599103597d6bbd7ff7"
        or type(red.get("successor_test_file")) is not dict
        or red.get("successor_test_file")
        != _SUCCESS_HISTORICAL_S1_TEST_FILE
        or red.get("successor_node_count") != 64
        or type(red.get("successor_node_count")) is not int
        or red.get("collected") != 64
        or type(red.get("collected")) is not int
        or red.get("failed") != 64
        or type(red.get("failed")) is not int
        or red.get("passed") != 0
        or type(red.get("passed")) is not int
        or red.get("collection_errors") != 0
        or type(red.get("collection_errors")) is not int
        or red.get("owner_issue_codes") != []
        or red.get("independent_issue_codes") != []
        or red.get("state") != "SUCCESSOR_CAUSAL_RED_FROZEN"
        or red.get("automatic_progression") is not False
        or red.get("body_free") is not True
        or red.get("receipt_sha256")
        != _SUCCESS_HISTORICAL_S1_LOGICAL_SHA256
        or red_identity != _SUCCESS_HISTORICAL_S1_IDENTITY
        or red.get("receipt_sha256")
        != _hash_without(red, "receipt_sha256")
        or not _success_direct_artifact_valid(
            red,
            red_identity,
            state.get("causal_red_postfetch_evidence"),
            role="SUCCESSOR_CAUSAL_RED_RESULT",
            schema=red.get("schema_version"),
            path=_SUCCESS_HISTORICAL_S1_PATH,
            logical_hash_key="receipt_sha256",
        )
    ):
        return False
    green_nodes = green.get("test_node_ids") if type(green) is dict else None
    green_states = green.get("outcome_states") if type(green) is dict else None
    if (
        type(green) is not dict
        or set(green) != _SUCCESS_GREEN_KEYS
        or green.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "post_d2_successor_targeted_green_result.v1"
        )
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
        or expected_contract_manifest is None
        or green.get("success_contract_test_manifest_sha256")
        != expected_contract_manifest.get(
            "success_contract_test_manifest_sha256"
        )
        or type(green_nodes) is not list
        or green_nodes != expected_contract_manifest.get("test_node_ids")
        or len(green_nodes) != 110
        or len(set(green_nodes)) != 110
        or green.get("executed_node_ids") != green_nodes
        or type(green_states) is not dict
        or green_states != {node: "PASSED" for node in green_nodes}
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
        or any(
            type(value) is not int for value in green["counts"].values()
        )
        or green.get("owner_issue_codes") != []
        or green.get("independent_issue_codes") != []
        or green.get("state") != "SUCCESSOR_TARGETED_GREEN_COMPLETED"
        or green.get("automatic_progression") is not False
        or green.get("body_free") is not True
        or green.get("receipt_sha256")
        != _hash_without(green, "receipt_sha256")
        or not _success_direct_artifact_valid(
            green,
            green_identity,
            state.get("combined_green_postfetch_evidence"),
            role="SUCCESSOR_COMBINED_GREEN_RESULT",
            schema=green.get("schema_version"),
            path=green_path,
            logical_hash_key="receipt_sha256",
        )
        or completion.get("causal_red_evidence_sha256")
        != red_identity.get("logical_artifact_sha256")
        or completion.get("combined_green_evidence_sha256")
        != green_identity.get("logical_artifact_sha256")
    ):
        return False
    publication = state.get("successor_completion_publication")
    if (
        type(publication) is not dict
        or publication.get("identity", {}).get("path")
        != completion_path
        or not _success_exact1_valid(
            publication,
            artifact=completion,
            roles=frozenset({"SUCCESSOR_COMPLETION_RECEIPT"}),
            schema=completion_schema,
            logical_hash_key="receipt_sha256",
        )
    ):
        return False
    return True


def _success_utc_seconds(value: Any) -> datetime | None:
    if (
        not isinstance(value, str)
        or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T"
            r"[0-9]{2}:[0-9]{2}:[0-9]{2}Z",
            value,
        )
        is None
    ):
        return None
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _success_p0_external_identity_valid(identity: Any) -> bool:
    if (
        type(identity) is not dict
        or set(identity) != RECOVERY_EPOCH002_P0_EXTERNAL_IDENTITY_KEYS
        or identity.get("schema_version")
        != _SUCCESS_P0_EXTERNAL_IDENTITY_SCHEMA
        or identity.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or identity.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or identity.get("p0_external_identity_sha256")
        != _SUCCESS_P0_EXTERNAL_IDENTITY_SHA256
        or identity.get("p0_external_identity_sha256")
        != hashlib.sha256(
            canonical_json_bytes(
                {
                    key: value
                    for key, value in identity.items()
                    if key != "p0_external_identity_sha256"
                }
            )
            + b"\n"
        ).hexdigest()
    ):
        return False
    parent = identity.get("parent_design")
    receipt = identity.get("receipt")
    if (
        type(parent) is not dict
        or set(parent) != RECOVERY_EPOCH002_P0_PARENT_DESIGN_KEYS
        or type(receipt) is not dict
        or set(receipt) != RECOVERY_EPOCH002_P0_RECEIPT_KEYS
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
    )


def _success_capabilities_valid(admission: Mapping[str, Any]) -> bool:
    authority = admission.get("authority")
    scope = admission.get("scope")
    if (
        type(authority) is not dict
        or set(authority) != _SUCCESS_ADMISSION_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or not isinstance(authority.get("admission_authority_token"), str)
        or not authority.get("admission_authority_token")
        or authority.get("publication_authority_token")
        != authority.get("admission_authority_token")
        or authority.get("authority_sha256")
        != _hash_without(authority, "authority_sha256")
        or type(scope) is not dict
        or set(scope) != _SUCCESS_ADMISSION_SCOPE_KEYS
        or scope.get("repository_full_name") != "MassyuRed/Cocolon"
        or scope.get("source_ref") != "refs/heads/main"
        or scope.get("successor_source_closure_sha256")
        != admission.get("successor_source_closure_sha256")
        or scope.get("operation_set")
        != list(_SUCCESS_ADMISSION_OPERATIONS)
        or scope.get("scope_sha256")
        != _hash_without(scope, "scope_sha256")
    ):
        return False
    return True


def _success_operational_succession_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_SUCCESSION_OWNER_STATE_KEYS
    ):
        return False
    closure = state.get("successor_source_closure")
    completion_publication = state.get("successor_completion_publication")
    completion_identity = (
        completion_publication.get("identity")
        if type(completion_publication) is dict
        else None
    )
    allocation = state.get("candidate_allocation")
    event = state.get("event1")
    allocated_at = (
        _success_utc_seconds(allocation.get("allocated_at_utc"))
        if type(allocation) is dict
        else None
    )
    event_at = (
        _success_utc_seconds(event.get("timestamp_utc"))
        if type(event) is dict
        else None
    )
    if (
        type(closure) is not dict
        or type(completion_identity) is not dict
        or type(allocation) is not dict
        or set(allocation) != _SUCCESS_CANDIDATE_V2_KEYS
        or allocation.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "candidate_allocation.v2"
        )
        or allocation.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or allocation.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not isinstance(allocation.get("candidate_version_id"), str)
        or not allocation.get("candidate_version_id")
        or allocation.get("candidate_version_id") == "nls_v3_rc_0034"
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
        or type(event) is not dict
        or event_at is None
        or allocated_at >= event_at
    ):
        return False
    admission = state.get("operational_admission_receipt")
    admission_publication = state.get("operational_admission_publication")
    issued_at = (
        _success_utc_seconds(admission.get("issued_at_utc"))
        if type(admission) is dict
        else None
    )
    expires_at = (
        _success_utc_seconds(admission.get("expires_at_utc"))
        if type(admission) is dict
        else None
    )
    if (
        type(admission) is not dict
        or not (
            _SUCCESS_ADMISSION_KEYS - _SUCCESS_ADMISSION_OPTIONAL_KEYS
        )
        <= set(admission)
        or not set(admission) <= _SUCCESS_ADMISSION_KEYS
        or admission.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "p1_operational_admission_receipt.v1"
        )
        or admission.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or admission.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or admission.get("successor_completion_receipt")
        != completion_identity
        or admission.get("successor_source_closure_sha256")
        != closure.get("source_closure_sha256")
        or admission.get("repository_full_name") != "MassyuRed/Cocolon"
        or admission.get("source_ref") != "refs/heads/main"
        or not isinstance(admission.get("challenge_id"), str)
        or _SHA256_RE.fullmatch(admission.get("challenge_id", "")) is None
        or not _success_capabilities_valid(admission)
        or admission.get("owner_validation_state") != "PROVED"
        or admission.get("independent_verification_state") != "PROVED"
        or issued_at is None
        or expires_at is None
        or not issued_at < allocated_at < event_at < expires_at
        or admission.get("state") != "P1_OPERATIONAL_ADMISSION_PROVED"
        or admission.get("automatic_progression") is not False
        or admission.get("body_free") is not True
        or admission.get("operational_admission_sha256")
        != _hash_without(admission, "operational_admission_sha256")
        or type(admission_publication) is not dict
        or admission_publication.get("identity", {}).get("path")
        != _SUCCESS_ADMISSION_PATH
        or not _success_exact1_valid(
            admission_publication,
            artifact=admission,
            roles=frozenset({"P1_OPERATIONAL_ADMISSION_RECEIPT"}),
            schema=admission.get("schema_version"),
            logical_hash_key="operational_admission_sha256",
        )
    ):
        return False
    admission_identity = admission_publication["identity"]
    authority = event.get("authority")
    publication = event.get("publication")
    transaction = (
        publication.get("transaction_capability")
        if type(publication) is dict
        else None
    )
    transaction_at = (
        _success_utc_seconds(transaction.get("observed_at_utc"))
        if type(transaction) is dict
        else None
    )
    admission_authority = admission["authority"]
    if (
        set(event) != _SUCCESS_EVENT_KEYS
        or event.get("schema_version")
        != "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v2"
        or event.get("ledger_id") != "recovery_epoch002_sequence"
        or event.get("event_id") != "recovery_epoch002_event_01"
        or event.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or event.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or event.get("candidate_version_id")
        != allocation.get("candidate_version_id")
        or event.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or event.get("event_ordinal") != 1
        or type(event.get("event_ordinal")) is not int
        or event.get("state") != "SOURCE_BASELINE_LOCKED"
        or event.get("timestamp_kind")
        != "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE"
        or not _success_p0_external_identity_valid(
            event.get("p0_external_identity")
        )
        or event.get("prior_event")
        != event.get("p0_external_identity")
        or _SHA256_RE.fullmatch(
            str(event.get("challenge_id", ""))
        )
        is None
        or type(authority) is not dict
        or set(authority) != _SUCCESS_EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or authority.get("transition_authority_token")
        != admission_authority.get("admission_authority_token")
        or authority.get("publication_authority_token")
        != admission_authority.get("publication_authority_token")
        or authority.get("operational_admission") != admission_identity
        or event.get("source_closure") != closure
        or event.get("candidate_allocation") != allocation
        or event.get("bootstrap_closure") != state.get("bootstrap_closure")
        or event.get("primary_evidence_artifact") != completion_identity
        or event.get("automatic_progression") is not False
        or event.get("body_free") is not True
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or type(publication) is not dict
        or not (
            _SUCCESS_EVENT_PUBLICATION_KEYS
            - _SUCCESS_EVENT_PUBLICATION_OPTIONAL_KEYS
        )
        <= set(publication)
        or not set(publication) <= _SUCCESS_EVENT_PUBLICATION_KEYS
        or publication.get("repository_full_name") != "MassyuRed/Cocolon"
        or publication.get("branch") != "main"
        or publication.get("event_path") != _SUCCESS_EVENT1_PATH
        or publication.get("supporting_artifact_count") != 1
        or type(publication.get("supporting_artifact_count")) is not int
        or publication.get("supporting_artifacts")
        != [completion_identity]
        or publication.get("supporting_artifact_set_sha256")
        != artifact_sha256([completion_identity])
        or publication.get("expected_changed_path_count") != 1
        or type(publication.get("expected_changed_path_count")) is not int
        or publication.get("publication_state") != "PUBLISHED_ATOMIC"
    ):
        return False
    event_publication = state.get("event1_publication")
    if (
        type(event_publication) is not dict
        or event_publication.get("identity", {}).get("path")
        != _SUCCESS_EVENT1_PATH
        or not _success_exact1_valid(
            event_publication,
            artifact=event,
            roles=frozenset({"SOURCE_BASELINE_EVENT"}),
            schema=event.get("schema_version"),
            logical_hash_key="event_sha256",
        )
    ):
        return False
    event_identity = event_publication["identity"]
    return state.get("candidate_operational_identity") == {
        "candidate_version_id": allocation["candidate_version_id"],
        "event1_identity_sha256": event_identity["identity_sha256"],
    }


def _success_atomic_manifest_valid(manifest: Any) -> bool:
    required_keys = _SUCCESS_MANIFEST_KEYS - {"ref_update_mode"}
    return (
        type(manifest) is dict
        and required_keys <= set(manifest)
        and set(manifest) <= _SUCCESS_MANIFEST_KEYS
        and manifest.get("schema_version")
        == (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "all11_atomic_publication_manifest.v1"
        )
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


def _success_event2_atomic_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_PUBLICATION_OWNER_STATE_KEYS
        or state.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
    ):
        return False
    manifest = state.get("atomic_publication_manifest")
    event = state.get("event2")
    artifacts = state.get("artifacts_by_path")
    candidates = state.get("candidate_identities_by_path")
    transaction = state.get("publication_transaction")
    terminal = state.get("terminal_commit_observation")
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
    completion_identity = (
        allocation.get("successor_completion_receipt")
        if type(allocation) is dict
        else None
    )
    if (
        type(manifest) is not dict
        or not (
            _SUCCESS_MANIFEST_KEYS - {"ref_update_mode"}
        )
        <= set(manifest)
        or not set(manifest) <= _SUCCESS_MANIFEST_KEYS
        or manifest.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "all11_atomic_publication_manifest.v1"
        )
        or manifest.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or manifest.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or manifest.get("body_free") is not True
        or manifest.get("core_artifact_count") != 13
        or type(manifest.get("core_artifact_count")) is not int
        or type(manifest.get("core_artifacts")) is not list
        or manifest.get("event_supporting_artifact_count") != 14
        or type(manifest.get("event_supporting_artifact_count")) is not int
        or manifest.get("expected_changed_path_count") != 15
        or type(manifest.get("expected_changed_path_count")) is not int
        or manifest.get("event_path") != _SUCCESS_EVENT2_PATH
        or type(event) is not dict
        or set(event) != _SUCCESS_EVENT_KEYS
        or event.get("schema_version")
        != "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v2"
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
        or _success_utc_seconds(event.get("timestamp_utc")) is None
        or _SHA256_RE.fullmatch(
            str(event.get("challenge_id", ""))
        )
        is None
        or not _success_p0_external_identity_valid(
            event.get("p0_external_identity")
        )
        or type(allocation) is not dict
        or set(allocation) != _SUCCESS_CANDIDATE_V2_KEYS
        or allocation.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "candidate_allocation.v2"
        )
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
        or not _success_completion_identity_valid(completion_identity)
        or _success_utc_seconds(allocation.get("allocated_at_utc")) is None
        or allocation.get("candidate_allocation_sha256")
        != _hash_without(allocation, "candidate_allocation_sha256")
        or type(bootstrap) is not dict
        or set(bootstrap) != _SUCCESS_BOOTSTRAP_KEYS
        or bootstrap.get("schema_version") != _SUCCESS_BOOTSTRAP_SCHEMA
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
    ):
        return False
    publication = event.get("publication")
    authority = event.get("authority")
    supporting = (
        publication.get("supporting_artifacts")
        if type(publication) is dict
        else None
    )
    if (
        type(publication) is not dict
        or not (
            _SUCCESS_EVENT_PUBLICATION_KEYS
            - _SUCCESS_EVENT_PUBLICATION_OPTIONAL_KEYS
        )
        <= set(publication)
        or not set(publication) <= _SUCCESS_EVENT_PUBLICATION_KEYS
        or publication.get("supporting_artifact_count") != 14
        or type(publication.get("supporting_artifact_count")) is not int
        or type(supporting) is not list
        or len(supporting) != 14
        or publication.get("expected_changed_path_count") != 15
        or type(publication.get("expected_changed_path_count")) is not int
        or publication.get("event_path") != _SUCCESS_EVENT2_PATH
        or publication.get("repository_full_name") != "MassyuRed/Cocolon"
        or publication.get("branch") != "main"
        or _SHA1_RE.fullmatch(
            str(publication.get("base_commit_sha1", ""))
        )
        is None
        or publication.get("publication_state") != "PUBLISHED_ATOMIC"
        or type(authority) is not dict
        or set(authority) != _SUCCESS_EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or not isinstance(
            authority.get("transition_authority_token"),
            str,
        )
        or not authority.get("transition_authority_token")
        or authority.get("publication_authority_token")
        != authority.get("transition_authority_token")
        or type(authority.get("operational_admission")) is not dict
        or set(authority["operational_admission"])
        != RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
        or authority["operational_admission"].get("artifact_role")
        != "P1_OPERATIONAL_ADMISSION_RECEIPT"
        or authority["operational_admission"].get("body_free") is not True
        or authority["operational_admission"].get("identity_sha256")
        != _hash_without(
            authority["operational_admission"],
            "identity_sha256",
        )
        or (
            type(transaction) is dict
            and _SUCCESS_TRANSACTION_REQUIRED_KEYS <= set(transaction)
            and set(transaction) <= _SUCCESS_TRANSACTION_KEYS
            and transaction.get("changed_paths")
            != list(_SUCCESS_CHANGED_PATHS)
        )
        or type(artifacts) is not dict
    ):
        return False
    if set(artifacts) != set(_SUCCESS_CHANGED_PATHS):
        return False
    candidate_shape_valid = (
        type(candidates) is dict
        and set(candidates) == set(_SUCCESS_CHANGED_PATHS)
        and all(
            type(candidates[path]) is dict
            and set(candidates[path]) == _SUCCESS_CANDIDATE_KEYS
            and candidates[path].get("path") == path
            and candidates[path].get("artifact_role")
            == _success_atomic_candidate_contract(path)[0]
            and candidates[path].get("body_free") is True
            for path in _SUCCESS_CHANGED_PATHS
        )
    )
    if (
        not candidate_shape_valid
        or any(
            type(row) is not dict
            or set(row) != _SUCCESS_CANDIDATE_KEYS
            or row.get("path") != path
            or row.get("artifact_role")
            != _success_atomic_candidate_contract(path)[0]
            or row.get("body_free") is not True
            for path, row in zip(
                _SUCCESS_SUPPORTING_PATHS,
                supporting,
                strict=True,
            )
        )
    ):
        return False
    if (
        manifest.get("atomic_publication_manifest_sha256")
        != _hash_without(
            manifest,
            "atomic_publication_manifest_sha256",
        )
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or [row.get("path") for row in manifest["core_artifacts"]]
        != list(_SUCCESS_CORE_PATHS)
        or [row.get("path") for row in supporting]
        != list(_SUCCESS_SUPPORTING_PATHS)
        or manifest.get("core_artifact_set_sha256")
        != artifact_sha256(manifest["core_artifacts"])
        or publication.get("supporting_artifact_set_sha256")
        != artifact_sha256(supporting)
    ):
        return False
    accepted = artifacts.get(_SUCCESS_ACCEPTED_PATH)
    all11 = artifacts.get(_SUCCESS_ALL11_PATH)
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
    primary = event.get("primary_evidence_artifact")
    lineage_valid = (
        type(event1_identity) is dict
        and event.get("prior_event") == event1_identity
        and manifest.get("candidate_version_id")
        == accepted.get("candidate_version_id")
        and manifest.get("candidate_version_id")
        == all11.get("candidate_version_id")
        and manifest.get("candidate_version_id")
        == event.get("candidate_version_id")
        and manifest.get("source_baseline_event") == event1_identity
        and manifest.get("source_baseline_event")
        == event.get("prior_event")
        and type(all11) is dict
        and all11.get("source_baseline_event") == event1_identity
        and event.get("candidate_version_id")
        == accepted.get("candidate_version_id")
        and allocation.get("candidate_version_id")
        == accepted.get("candidate_version_id")
        and bootstrap.get("bootstrap_closure_sha256")
        == accepted.get("formal_worker_terminal_result", {}).get(
            "bootstrap_closure_sha256"
        )
        and event.get("source_closure") == all11.get("source_closure")
        and all11.get("accepted_test_run_receipt_sha256")
        == accepted.get("accepted_test_run_receipt_sha256")
        and all11.get("candidate_version_id")
        == accepted.get("candidate_version_id")
    )
    if not lineage_valid:
        return False
    return (
        candidate_shape_valid
        and (
            type(primary) is dict
            and set(primary) == _SUCCESS_CANDIDATE_KEYS
            and primary.get("path") == _SUCCESS_ALL11_PATH
            and primary.get("artifact_role") == "ALL11_COMPLETION_CHAIN"
            and primary.get("body_free") is True
        )
    )


def _success_atomic_candidate_contract(
    path: str,
) -> tuple[str, str]:
    if path == _SUCCESS_ACCEPTED_PATH:
        return (
            "ACCEPTED_TEST_RUN_RECEIPT",
            "accepted_test_run_receipt_sha256",
        )
    if path in _SUCCESS_STEP_PATHS:
        return ("CURRENT_STEP_COMPLETION_RECEIPT", "receipt_sha256")
    if path == _SUCCESS_ALL11_PATH:
        return ("ALL11_COMPLETION_CHAIN", "all11_completion_chain_sha256")
    if path == _SUCCESS_MANIFEST_PATH:
        return (
            "ALL11_ATOMIC_PUBLICATION_MANIFEST",
            "atomic_publication_manifest_sha256",
        )
    return ("SEQUENCE_EVENT_2", "event_sha256")


def _success_event2_cardinality_valid(state: Any) -> bool:
    """Replay the Event2-owned exact15 projection before Git replay."""

    if (
        type(state) is not dict
        or set(state) != _SUCCESS_PUBLICATION_OWNER_STATE_KEYS
    ):
        return False
    manifest = state.get("atomic_publication_manifest")
    event = state.get("event2")
    publication = (
        event.get("publication") if type(event) is dict else None
    )
    supporting = (
        publication.get("supporting_artifacts")
        if type(publication) is dict
        else None
    )
    transaction = state.get("publication_transaction")
    artifacts = state.get("artifacts_by_path")
    accepted = (
        artifacts.get(_SUCCESS_ACCEPTED_PATH)
        if type(artifacts) is dict
        else None
    )
    success_lineage = (
        accepted.get("success_lineage")
        if type(accepted) is dict
        else None
    )
    primary = event.get("primary_evidence_artifact")
    core = (
        manifest.get("core_artifacts")
        if type(manifest) is dict
        else None
    )
    return (
        type(manifest) is dict
        and manifest.get("core_artifact_count") == 13
        and type(manifest.get("core_artifact_count")) is int
        and type(core) is list
        and len(core) == 13
        and all(type(row) is dict for row in core)
        and [row.get("path") for row in core]
        == list(_SUCCESS_CORE_PATHS)
        and manifest.get("core_artifact_set_sha256")
        == artifact_sha256(core)
        and manifest.get("event_supporting_artifact_count") == 14
        and type(manifest.get("event_supporting_artifact_count")) is int
        and manifest.get("expected_changed_path_count") == 15
        and type(manifest.get("expected_changed_path_count")) is int
        and manifest.get("event_path") == _SUCCESS_EVENT2_PATH
        and type(publication) is dict
        and publication.get("supporting_artifact_count") == 14
        and type(publication.get("supporting_artifact_count")) is int
        and type(supporting) is list
        and len(supporting) == 14
        and all(type(row) is dict for row in supporting)
        and [row.get("path") for row in supporting]
        == list(_SUCCESS_SUPPORTING_PATHS)
        and publication.get("supporting_artifact_set_sha256")
        == artifact_sha256(supporting)
        and publication.get("expected_changed_path_count") == 15
        and type(publication.get("expected_changed_path_count")) is int
        and publication.get("event_path") == _SUCCESS_EVENT2_PATH
        and type(transaction) is dict
        and (
            "changed_paths" not in transaction
            or transaction.get("changed_paths")
            == list(_SUCCESS_CHANGED_PATHS)
        )
        and type(artifacts) is dict
        and type(success_lineage) is dict
        and event.get("prior_event")
        == success_lineage.get("source_baseline_event")
        and primary
        == _success_candidate_identity(
            artifacts.get(_SUCCESS_ALL11_PATH),
            role="ALL11_COMPLETION_CHAIN",
            path=_SUCCESS_ALL11_PATH,
            logical_hash_key="all11_completion_chain_sha256",
        )
    )


def _success_git_candidate_bytes_valid(state: Any) -> bool:
    """Replay central candidate bytes under the Git-bytes owner."""

    if type(state) is not dict:
        return False
    artifacts = state.get("artifacts_by_path")
    candidates = state.get("candidate_identities_by_path")
    if type(artifacts) is not dict or type(candidates) is not dict:
        return False
    for path in _SUCCESS_CHANGED_PATHS:
        role, logical_hash_key = _success_atomic_candidate_contract(path)
        if candidates.get(path) != _success_candidate_identity(
            artifacts.get(path),
            role=role,
            path=path,
            logical_hash_key=logical_hash_key,
        ):
            return False
    return True


def _success_write_scope_valid(
    transaction: Mapping[str, Any],
) -> bool:
    """Independently verify each approved write commit and its target paths."""

    expected_paths = set(_SUCCESS_CHANGED_PATHS)
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


def _success_event2_transaction_valid(
    event: Any,
    *,
    terminal_commit: str,
) -> bool:
    publication = event.get("publication") if type(event) is dict else None
    capability = (
        publication.get("transaction_capability")
        if type(publication) is dict
        else None
    )
    authority = event.get("authority") if type(event) is dict else None
    admission = (
        authority.get("operational_admission")
        if type(authority) is dict
        else None
    )
    if capability is None:
        return True
    return (
        type(capability) is dict
        and set(capability).issubset(_SUCCESS_TRANSACTION_CAPABILITY_KEYS)
        and capability.get("repository_full_name") == "MassyuRed/Cocolon"
        and capability.get("source_ref") == "refs/heads/main"
        and capability.get("expected_changed_path_count") == 15
        and type(capability.get("expected_changed_path_count")) is int
        and capability.get("challenge_id") == event.get("challenge_id")
        and _SHA256_RE.fullmatch(
            str(capability.get("challenge_id", ""))
        )
        is not None
        and (
            "transaction_capability_sha256" not in capability
            or capability.get("transaction_capability_sha256")
            == _hash_without(capability, "transaction_capability_sha256")
        )
    )


def _success_git_publication_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != _SUCCESS_PUBLICATION_OWNER_STATE_KEYS
        or state.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
    ):
        return False
    terminal = state.get("terminal_commit_observation")
    transaction = state.get("publication_transaction")
    manifest = state.get("atomic_publication_manifest")
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
        or not _success_atomic_manifest_valid(manifest)
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
        != list(_SUCCESS_CHANGED_PATHS)
        or type(artifacts) is not dict
        or set(artifacts) != set(_SUCCESS_CHANGED_PATHS)
        or type(candidates) is not dict
        or set(candidates) != set(_SUCCESS_CHANGED_PATHS)
        or not _success_event2_transaction_valid(
            event,
            terminal_commit=terminal["commit_sha1"],
        )
    ):
        return False
    expected_candidates: dict[str, dict[str, Any]] = {}
    for path in _SUCCESS_CHANGED_PATHS:
        role, hash_key = _success_atomic_candidate_contract(path)
        candidate = _success_candidate_identity(
            artifacts[path],
            role=role,
            path=path,
            logical_hash_key=hash_key,
        )
        if (
            candidate is None
            or type(candidates[path]) is not dict
            or set(candidates[path]) != _SUCCESS_CANDIDATE_KEYS
            or candidates[path] != candidate
        ):
            return False
        expected_candidates[path] = candidate
    publication = event.get("publication")
    supporting = (
        publication.get("supporting_artifacts")
        if type(publication) is dict
        else None
    )
    if (
        manifest.get("core_artifacts")
        != [
            expected_candidates[path]
            for path in _SUCCESS_CORE_PATHS
        ]
        or manifest.get("event_supporting_artifact_count") != 14
        or type(manifest.get("event_supporting_artifact_count")) is not int
        or manifest.get("expected_changed_path_count") != 15
        or type(manifest.get("expected_changed_path_count")) is not int
        or manifest.get("event_path") != _SUCCESS_EVENT2_PATH
        or type(supporting) is not list
        or supporting
        != [
            expected_candidates[path]
            for path in _SUCCESS_SUPPORTING_PATHS
        ]
        or publication.get("supporting_artifact_set_sha256")
        != artifact_sha256(supporting)
        or event.get("primary_evidence_artifact")
        != expected_candidates[_SUCCESS_ALL11_PATH]
    ):
        return False
    blob_map = {
        path: expected_candidates[path]["git_blob_sha1"]
        for path in _SUCCESS_CHANGED_PATHS
    }
    commit_by_path = transaction["publication_commit_sha1_by_path"]
    expected_external = []
    for path in _SUCCESS_CHANGED_PATHS:
        identity = {
            **expected_candidates[path],
            "publication_commit_sha1": commit_by_path[path],
            "identity_sha256": "",
        }
        identity["identity_sha256"] = _hash_without(
            identity,
            "identity_sha256",
        )
        expected_external.append(identity)
    if (
        transaction.get("target_blob_sha1_by_path") != blob_map
        or transaction.get("ref_update_result") not in {"SUCCEEDED", "UNKNOWN"}
        or type(transaction.get("ref_update_attempt_count")) is not int
        or transaction.get("ref_update_attempt_count") < 1
    ):
        return False
    postfetch = state.get("postfetch_observation")
    if (
        type(postfetch) is not dict
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
        or not set(postfetch).issubset(_SUCCESS_ATOMIC_POSTFETCH_KEYS)
        or _SHA1_RE.fullmatch(str(postfetch.get("head_commit_sha1", "")))
        is None
        or postfetch.get("authoritative_ref_read") is not True
        or postfetch.get("authoritative_head_read") is not True
        or postfetch.get("changed_paths")
        != list(_SUCCESS_CHANGED_PATHS)
        or postfetch.get("artifact_raw_sha256_by_path")
        != {
            path: expected_candidates[path]["raw_sha256"]
            for path in _SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("artifact_git_blob_sha1_by_path") != blob_map
        or postfetch.get("artifact_logical_sha256_by_path")
        != {
            path: expected_candidates[path]["logical_artifact_sha256"]
            for path in _SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("artifact_schema_by_path")
        != {
            path: expected_candidates[path]["schema_version"]
            for path in _SUCCESS_CHANGED_PATHS
        }
        or postfetch.get("artifact_body_free_by_path")
        != {path: True for path in _SUCCESS_CHANGED_PATHS}
        or postfetch.get("publication_external_identities")
        != expected_external
        or postfetch.get("owner_issue_codes") != []
        or postfetch.get("independent_issue_codes") != []
        or postfetch.get("state") != "POSTVERIFIED"
    ):
        return False
    return True


def _success_owner_graph_bindings_valid(
    state: Mapping[str, Any],
) -> bool:
    """Require every success owner to describe one identical lineage."""

    closure_owner = state.get("successor_closure_owner_state")
    succession = state.get("successor_succession_owner_state")
    terminal_owner = state.get("terminal_owner_state")
    accepted_owner = state.get("accepted_owner_state")
    step_owner = state.get("step_owner_state")
    all11_owner = state.get("all11_owner_state")
    publication = state.get("publication_owner_state")
    if any(
        type(owner) is not dict
        for owner in (
            closure_owner,
            succession,
            terminal_owner,
            accepted_owner,
            step_owner,
            all11_owner,
            publication,
        )
    ):
        return False

    accepted = accepted_owner.get("accepted_test_run_receipt")
    accepted_context = accepted_owner.get("source_context")
    step_context = step_owner.get("source_context")
    all11_context = all11_owner.get("source_context")
    closure = closure_owner.get("successor_source_closure")
    bootstrap = closure_owner.get("bootstrap_closure")
    event1_publication = succession.get("event1_publication")
    event1_identity = (
        event1_publication.get("identity")
        if type(event1_publication) is dict
        else None
    )
    artifacts = publication.get("artifacts_by_path")
    candidates = publication.get("candidate_identities_by_path")
    event2 = publication.get("event2")
    manifest = publication.get("atomic_publication_manifest")
    all11 = all11_owner.get("all11_completion_chain")
    lineage = accepted.get("success_lineage") if type(accepted) is dict else None
    admission = succession.get("operational_admission_receipt")
    admission_publication = succession.get(
        "operational_admission_publication"
    )
    event1 = succession.get("event1")
    if (
        type(accepted) is not dict
        or type(accepted_context) is not dict
        or type(step_context) is not dict
        or type(all11_context) is not dict
        or type(closure) is not dict
        or type(bootstrap) is not dict
        or type(event1_identity) is not dict
        or type(artifacts) is not dict
        or type(candidates) is not dict
        or type(event2) is not dict
        or type(manifest) is not dict
        or type(all11) is not dict
        or type(lineage) is not dict
        or type(admission) is not dict
        or type(admission_publication) is not dict
        or type(event1) is not dict
    ):
        return False

    receipts = step_owner.get("receipts")
    receipt_artifacts = step_owner.get("receipt_artifacts")
    if (
        terminal_owner != accepted_owner.get("terminal_owner_state")
        or terminal_owner.get("terminal_result")
        != accepted.get("formal_worker_terminal_result")
        or terminal_owner.get("terminal_publication")
        != accepted_owner.get("terminal_publication")
        or step_owner.get("terminal_result")
        != accepted.get("formal_worker_terminal_result")
        or step_owner.get("accepted_test_run_receipt") != accepted
        or all11_owner.get("accepted_test_run_receipt") != accepted
        or all11_owner.get("receipts") != receipts
        or all11_owner.get("receipt_artifacts") != receipt_artifacts
        or all11_owner.get("receipt_sha256s")
        != step_owner.get("receipt_sha256s")
        or step_context != accepted_context
        or all11_context != accepted_context
    ):
        return False

    if (
        succession.get("successor_source_closure") != closure
        or accepted_context.get("successor_source_closure") != closure
        or step_context.get("successor_source_closure") != closure
        or all11_context.get("successor_source_closure") != closure
        or succession.get("bootstrap_closure") != bootstrap
        or accepted_context.get("bootstrap_closure") != bootstrap
        or succession.get("parent_addendum_external_identity")
        != closure_owner.get("parent_addendum_external_identity")
        or state.get("parent_addendum_external_identity")
        != closure_owner.get("parent_addendum_external_identity")
        or accepted_context.get("event1_artifact")
        != succession.get("event1")
        or accepted_context.get("event1_identity") != event1_identity
        or accepted_context.get("candidate_allocation")
        != succession.get("candidate_allocation")
        or lineage.get("source_baseline_event") != event1_identity
    ):
        return False

    event2_authority = event2.get("authority")
    event2_publication = event2.get("publication")
    event2_transaction = (
        event2_publication.get("transaction_capability")
        if type(event2_publication) is dict
        else None
    )
    admission_authority = admission.get("authority")
    admission_identity = admission_publication.get("identity")
    event1_authority = event1.get("authority")
    event1_at = _success_utc_seconds(event1.get("timestamp_utc"))
    event2_at = _success_utc_seconds(event2.get("timestamp_utc"))
    admission_expires_at = _success_utc_seconds(
        admission.get("expires_at_utc")
    )
    if (
        type(event2_authority) is not dict
        or type(admission_authority) is not dict
        or type(admission_identity) is not dict
        or type(event1_authority) is not dict
        or event2_authority.get("operational_admission")
        != admission_identity
        or event1_authority.get("operational_admission")
        != admission_identity
        or event2_authority.get("transition_authority_token")
        != event2_authority.get("publication_authority_token")
        or event2_authority.get("transition_authority_token")
        in {
            admission_authority.get("admission_authority_token"),
            admission_authority.get("publication_authority_token"),
            "",
            None,
        }
        or event1_at is None
        or event2_at is None
        or admission_expires_at is None
        or not event1_at < event2_at < admission_expires_at
    ):
        return False

    if (
        all11.get("source_closure") != closure
        or all11.get("source_baseline_event") != event1_identity
        or event2.get("source_closure") != closure
        or event2.get("prior_event") != event1_identity
        or event2.get("p0_external_identity")
        != event1.get("p0_external_identity")
        or event2.get("candidate_allocation")
        != succession.get("candidate_allocation")
        or event2.get("bootstrap_closure") != bootstrap
        or manifest.get("source_baseline_event") != event1_identity
        or artifacts.get(_SUCCESS_ACCEPTED_PATH) != accepted
        or candidates.get(_SUCCESS_ACCEPTED_PATH)
        != step_owner.get("accepted_test_run_artifact")
        or artifacts.get(_SUCCESS_ALL11_PATH) != all11
        or candidates.get(_SUCCESS_ALL11_PATH)
        != event2.get("primary_evidence_artifact")
    ):
        return False

    if (
        type(receipts) is not list
        or len(receipts) != 11
        or type(receipt_artifacts) is not list
        or len(receipt_artifacts) != 11
    ):
        return False
    return all(
        artifacts.get(_SUCCESS_STEP_PATHS[step]) == receipts[step]
        and candidates.get(_SUCCESS_STEP_PATHS[step])
        == receipt_artifacts[step]
        for step in range(11)
    )


def _verify_recovery_epoch002_success_contract_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Independently replay the post-D2 success contract graph."""

    if type(state) is not dict:
        return ("PARENT_ADDENDUM_BINDING_INVALID",)
    if not _success_parent_addendum_valid(state):
        return ("PARENT_ADDENDUM_BINDING_INVALID",)
    if not _success_closure_owner_valid(
        state.get("successor_closure_owner_state")
    ):
        return ("OWNER_VERIFIER_DISAGREEMENT_STOP",)
    succession = state.get("successor_succession_owner_state")
    if not _success_completion_valid(succession):
        return ("SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID",)
    if not _success_operational_succession_valid(succession):
        return ("SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID",)

    source_observation = state.get("verifier_source_observation")
    actual_import_violations = _success_verifier_import_violations()
    if (
        actual_import_violations
        or state.get("verifier_import_violations")
        != list(actual_import_violations)
        or state.get("shared_primitive_allowlist")
        != list(RECOVERY_EPOCH002_SHARED_PRIMITIVE_ALLOWLIST)
        or type(source_observation) is not dict
        or set(source_observation)
        != {"path", "git_blob_sha1", "raw_sha256"}
        or source_observation.get("path") != _SUCCESS_VERIFIER_PATH
        or _success_source_identity(source_observation.get("path", ""))
        != {
            "git_blob_sha1": source_observation.get("git_blob_sha1"),
            "sha256": source_observation.get("raw_sha256"),
        }
    ):
        return ("VERIFIER_OWNER_IMPORT_FORBIDDEN",)
    if not _success_terminal_owner_valid(
        state.get("terminal_owner_state")
    ):
        return ("INDEPENDENT_TERMINAL_SCHEMA_INVALID",)
    if (
        not _success_accepted_owner_valid(
            state.get("accepted_owner_state")
        )
        or not _success_step_owner_valid(state.get("step_owner_state"))
        or not _success_all11_owner_valid(
            state.get("all11_owner_state")
        )
    ):
        return ("INDEPENDENT_SUCCESS_RECEIPT_INVALID",)
    publication = state.get("publication_owner_state")
    if not _success_git_candidate_bytes_valid(publication):
        return ("INDEPENDENT_GIT_GRAPH_BYTES_HASH_INVALID",)
    if not _success_event2_cardinality_valid(publication):
        return ("INDEPENDENT_EVENT2_ATOMIC_CARDINALITY_INVALID",)
    if not _success_git_publication_valid(publication):
        return ("INDEPENDENT_GIT_GRAPH_BYTES_HASH_INVALID",)
    if not _success_event2_atomic_valid(publication):
        return ("INDEPENDENT_EVENT2_ATOMIC_CARDINALITY_INVALID",)
    if not _success_owner_graph_bindings_valid(state):
        return ("OWNER_VERIFIER_DISAGREEMENT_STOP",)
    if (
        state.get("owner_issue_codes") != []
        or state.get("independent_issue_codes") != []
        or state.get("publication_requested") is not False
    ):
        return ("OWNER_VERIFIER_DISAGREEMENT_STOP",)
    return ()


def verify_recovery_epoch002_success_contract_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed while independently replaying the success graph."""

    try:
        if (
            type(state) is not dict
            or set(state) != _SUCCESS_CONTRACT_STATE_KEYS
            or _success_contains_forbidden_state_key(state)
        ):
            return ("PARENT_ADDENDUM_BINDING_INVALID",)
        return _verify_recovery_epoch002_success_contract_state_impl(state)
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("OWNER_VERIFIER_DISAGREEMENT_STOP",)


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
        or not _identity_role_schema_valid(
            identity.get("artifact_role"),
            identity.get("schema_version"),
        )
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
    if (
        state.get("reflection_contract_version")
        == RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
    ):
        expected_paths = state.get("expected_changed_paths")
        changed_paths = state.get("changed_paths")
        return (
            type(expected_paths) is not list
            or len(expected_paths) != 1
            or type(changed_paths) is not list
            or changed_paths != expected_paths
            or (
                require_new_path
                and state.get("path_preexisted") is not False
            )
            or state.get("postfetch_succeeded") is not True
            or state.get("postfetch_matches_candidate") is not True
            or state.get("owner_issue_codes") != []
            or state.get("independent_issue_codes") != []
        )
    # HISTORICAL_NON_NORMATIVE: markerless D1 evidence retains its original
    # expected-old/direct-parent checks, but cannot govern current reflection.
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
        or not _role_schema_valid(
            role,
            artifact.get("schema_version"),
        )
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
        or _SHA1_RE.fullmatch(
            str(state.get("postfetch_commit_sha1", ""))
        )
        is None
        or state.get("postfetch_git_blob_sha1")
        != identity.get("git_blob_sha1")
    ):
        return ("PUBLISHED_ARTIFACT_IDENTITY_MISMATCH",)
    return ()


RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS = _keys(
    """
    source_commit_sha1 source_tree_sha1 formal_owner_artifacts_sha256
    formal_test_manifest_sha256 import_manifest_sha256
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    installed_distributions_sha256 pytest_distribution_identity
    python_runtime_identity loaded_plugin_manifest_sha256
    preflight_argv_sha256 formal_worker_argv_sha256
    environment_policy_sha256
    """
)
RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS = (
    (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "post_d2_source_baseline_eligibility_successor_closure.v1",
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_manifest.v2",
    ),
    (
        "cocolon.emlis.nls_v3.recovery_epoch003."
        "source_baseline_eligibility_closure.v1",
        "cocolon.emlis.nls_v3.recovery_epoch003."
        "formal_worker_bootstrap_manifest.v1",
    ),
)
RECOVERY_EPOCH003_FAILURE_CLASSES = (
    "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
    "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
    "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
    "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
    "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
)
_RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role body_free git_blob_sha1 identity_sha256
    logical_artifact_sha256 path publication_commit_sha1 raw_sha256
    repository_full_name schema_version
    """
)
_RECOVERY_EPOCH003_SOURCE_KEYS = _keys(
    """
    schema_version repository_full_name source_ref source_commit_sha1
    source_tree_sha1 worktree_clean detailed_design_sha256
    epoch003_p0_external_identity_sha256 epoch002_predecessor_set_sha256
    d1_red_receipt_external_identity_sha256
    d2_green_receipt_external_identity_sha256
    source_dependency_closure_sha256 canonical_current_closure_sha256
    requirement_registry_sha256 formal_node_registry_sha256
    proof_source_closure_sha256 formal_test_manifest_sha256
    bootstrap_closure_sha256
    reference_runtime_observation_external_identity_sha256
    source_closure_sha256
    """
)
_RECOVERY_EPOCH003_BOOTSTRAP_KEYS = _keys(
    """
    schema_version source_commit_sha1 source_tree_sha1
    formal_owner_artifacts formal_owner_artifacts_sha256
    formal_test_node_ids formal_test_manifest formal_test_manifest_sha256
    conftest_plugin_mode pytest_plugins_environment_variable_removed
    pytest_entrypoint_autoload_disabled explicit_plugin_allowlist
    loaded_plugin_manifest loaded_plugin_manifest_sha256 import_manifest
    import_manifest_sha256 dependency_lock_identity
    wheel_bundle_manifest_sha256 expected_installed_distributions
    expected_installed_distributions_sha256 expected_python_runtime_identity
    expected_pytest_distribution_identity
    reference_runtime_observation_external_identity environment_policy
    environment_policy_sha256 preflight_argv preflight_argv_sha256
    formal_worker_argv formal_worker_argv_sha256 unclassified_import_count
    unresolved_dynamic_import_count body_free bootstrap_closure_sha256
    """
)
_RECOVERY_EPOCH003_REFERENCE_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id authority_token
    source_commit_sha1 source_tree_sha1 dependency_lock_identity
    wheel_bundle_manifest_sha256 runtime_materialization
    python_runtime_identity pytest_distribution_identity
    installed_distributions installed_distributions_sha256
    environment_policy environment_policy_sha256 reservation_count_delta
    formal_exact134_invocation_count collection_state test_execution_state
    body_free reference_runtime_observation_sha256
    """
)
_RECOVERY_EPOCH003_OPERATIONAL_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    authority_token preflight_challenge_id preflight_id
    source_baseline_event_external_identity_sha256 source_closure_sha256
    bootstrap_closure_sha256 source_commit_sha1 source_tree_sha1
    worktree_clean formal_owner_artifacts_sha256
    formal_test_manifest_sha256 import_manifest_sha256
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    installed_distributions_sha256 pytest_distribution_identity
    python_runtime_identity loaded_plugin_manifest_sha256
    preflight_argv_sha256 formal_worker_argv_sha256 environment_policy
    environment_policy_sha256 runtime_materialization
    runtime_root_identity_sha256 reference_runtime_root_identity_sha256
    attempt_registry_root_identity_sha256
    owner_operational_projection_sha256
    independent_operational_projection_sha256 owner_validation_state
    independent_verification_state reservation_count_delta
    formal_exact134_invocation_count collection_state test_execution_state
    pytest_main_called body_free operational_runtime_observation_sha256
    """
)
_RECOVERY_EPOCH003_READINESS_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    authority_token event1_external_identity_sha256
    event1_bootstrap_closure event1_bootstrap_closure_sha256
    operational_runtime_observation_external_identity
    operational_runtime_observation_sha256
    expected_observed_projection_sha256 readiness_receipt_path
    preflight_started_at_utc preflight_finished_at_utc
    owner_validation_state independent_verification_state
    reservation_count_delta formal_exact134_invocation_count
    collection_state test_execution_state pytest_main_called
    automatic_progression body_free bootstrap_readiness_receipt_sha256
    """
)
_RECOVERY_EPOCH003_FAILURE_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    authority_token preflight_challenge_id preflight_id
    event1_external_identity_sha256 source_closure_sha256
    bootstrap_closure_sha256 operational_runtime_observation_state
    operational_runtime_observation_external_identity
    operational_runtime_observation_sha256
    owner_operational_projection_sha256
    independent_operational_projection_sha256
    expected_observed_projection_sha256 failure_stage failure_class
    failure_issue_codes stop_code reservation_count_delta attempt_id
    formal_exact134_invocation_count owner_validation_state
    independent_verification_state automatic_retry automatic_progression
    body_free receipt_sha256
    """
)
_RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_KEYS = _keys(
    """
    schema_version runtime_root_identity_sha256
    python_executable_relative_path installed_directory_relative_path
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    distribution_count runtime_materialization_state body_free
    runtime_materialization_sha256
    """
)
_RECOVERY_EPOCH003_RUNTIME_IDENTITY_KEYS = _keys(
    "executable_sha256 implementation version build_sha256"
)
_RECOVERY_EPOCH003_DISTRIBUTION_KEYS = _keys(
    """
    normalized_distribution_name distribution_version wheel_sha256
    installed_record_closure_sha256
    """
)
_RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS = _keys(
    "identity_class path raw_sha256"
)
_RECOVERY_EPOCH003_ENVIRONMENT_KEYS = _keys(
    "fixed removed inherited_path_sha256 lang lc_all"
)
_RECOVERY_EPOCH003_ENVIRONMENT_FIXED_KEYS = _keys(
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD PYTHONDONTWRITEBYTECODE"
)
_RECOVERY_EPOCH003_OWNER_ROW_KEYS = _keys(
    "role path git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_TEST_ROW_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_IMPORT_ROW_KEYS = _keys(
    "import_name classification owner_paths target_identity"
)
_RECOVERY_EPOCH003_FIRST_PARTY_TARGET_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_STDLIB_TARGET_KEYS = _keys(
    "module_name python_runtime_identity_sha256"
)
_RECOVERY_EPOCH003_THIRD_PARTY_TARGET_KEYS = _keys(
    """
    module_name normalized_distribution_name distribution_version
    wheel_sha256 installed_record_closure_sha256
    """
)
_RECOVERY_EPOCH003_EVENT_KEYS = _keys(
    """
    schema_version ledger_id event_id logical_cycle_id recovery_epoch_id
    candidate_version_id event_ordinal event_name state prior_event
    challenge_id timestamp_utc timestamp_kind authority p0_external_identity
    candidate_allocation source_closure bootstrap_closure
    primary_evidence_artifact publication body_free automatic_progression
    event_sha256
    """
)
_RECOVERY_EPOCH003_EVENT_AUTHORITY_KEYS = _keys(
    """
    approval_kind operational_admission publication_authority_token
    transition_authority_token
    """
)
_RECOVERY_EPOCH003_EVENT_CANDIDATE_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    allocated_at_utc p0_external_identity_sha256 source_closure_sha256
    reference_runtime_observation_external_identity_sha256
    candidate_allocation_sha256
    """
)
_RECOVERY_EPOCH003_EVENT_PUBLICATION_KEYS = _keys(
    """
    base_commit_sha1 branch event_path expected_changed_path_count
    publication_state repository_full_name supporting_artifact_count
    supporting_artifact_set_sha256 supporting_artifacts
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
_RECOVERY_EPOCH003_REFERENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "reference_runtime_observation.v1"
)
_RECOVERY_EPOCH003_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.sequence_event.v1"
)
_RECOVERY_EPOCH003_OPERATIONAL_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "operational_runtime_observation.v1"
)
_RECOVERY_EPOCH003_READINESS_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "bootstrap_readiness_receipt.v1"
)
_RECOVERY_EPOCH003_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "formal_worker_bootstrap_preflight_failure_receipt.v1"
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
_RECOVERY_EPOCH003_EVENT_PATH = (
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
_RECOVERY_EPOCH003_STOP_CODE = (
    "PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP"
)
_RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.runtime_materialization.v1"
)
_RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256 = (
    "74286b862eeee1663d2758ee18d1e848316da6fc27b12fef38c149c5a2b52f36"
)
_RECOVERY_EPOCH003_EPOCH002_PREDECESSOR_SET_SHA256 = (
    "44ef0cf922e8fb6503ae4a96f458a60abc8fbae2e48aa11863269ff783d7343d"
)
_RECOVERY_EPOCH003_OWNER_ROLE_PATHS_SHA256 = (
    "f88a2c5dd2c4b0dacfd909f79a73f230b07eed0cfb79a27bc752853a565a380f"
)
_RECOVERY_EPOCH003_FORMAL_NODE_IDS_SHA256 = (
    "0ab1039a35b8621a257617688cc5d63bb331f5c32dd08f34df1173a6b9e57118"
)
_RECOVERY_EPOCH003_FORMAL_TEST_PATHS_SHA256 = (
    "fca7be99d0501352b58f140020651b77db2ee7997b85d56d8551a2106056db85"
)
_RECOVERY_EPOCH003_PREFLIGHT_ARGV = [
    "python",
    "-m",
    "ai.tools.emlis_nls_v3_recovery_epoch002_"
    "formal_worker_bootstrap_preflight",
]
_RECOVERY_EPOCH003_FORMAL_WORKER_ARGV_PREFIX = [
    "python",
    "-m",
    "pytest",
    "--noconftest",
    "-p",
    "no:cacheprovider",
]
_RECOVERY_EPOCH003_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
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
_RECOVERY_EPOCH003_MATERIALIZATION_REQUEST_KEYS = _keys(
    """
    authority_token artifact_repository_root source_repository_root
    expected_source_commit_sha1 expected_source_tree_sha1
    dependency_lock_path wheelhouse_path destination_root environment
    """
)
_RECOVERY_EPOCH003_MATERIALIZATION_RESULT_KEYS = _keys(
    """
    runtime_root wheel_snapshot_root runtime_materialization
    effective_environment_policy
    """
)
_RECOVERY_EPOCH003_LOCK_PATH = (
    "ai/configs/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
)
_RECOVERY_EPOCH003_LOCK_RAW_SHA256 = (
    "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
)
_RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256 = (
    "801ba54efc0f6655238d14e7c153fb70b555801489aa8ba028515fc64d9c05f4"
)
_RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256 = (
    "63f3915ccf57845dc0c4b5d14762207d23d1cb7a435a9de8411add8491ba6fc8"
)
_RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256 = (
    "0e2e4b5ec3f3b1aef7fad4474af28d8eeea8fa7bec1a57a9cb7180fc81b80e42"
)
_RECOVERY_EPOCH003_DETAILED_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
_RECOVERY_EPOCH003_CORRECTED_D1_IDENTITY_SHA256 = (
    "d9164d82715abb519b549a7581737a37ebd3bf153b53284697cbe4573a8edb9e"
)
_RECOVERY_EPOCH003_BOOTSTRAP_D2_IDENTITY_SHA256 = (
    "cbd665b12b3af16b251a66073222d12823fb8776207922616718290e4bddc738"
)
_RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_SHA256 = (
    "70a75ae561fad0846604d05b1262615be4c4a16b36b332150f8c7dc04ee71728"
)
_RECOVERY_EPOCH003_FORMAL_NODE_REGISTRY_SHA256 = (
    "fbe29ce0b819563cb5db2dc79fec8277b32ae0dea5a3a5cba64230ba4a1f73cf"
)
_RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3.py"
)
_RECOVERY_EPOCH003_ROOT_NONCE_FILE = ".cocolon-root-nonce"
_RECOVERY_EPOCH003_ROOT_IDENTITY_PREIMAGE_KEYS = _keys(
    """
    schema_version materialization_kind root_nonce_sha256
    source_commit_sha1 source_tree_sha1 dependency_lock_raw_sha256
    wheel_bundle_manifest_sha256 installed_distributions_sha256
    python_runtime_identity_sha256 pytest_distribution_identity_sha256
    environment_policy_sha256
    """
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


def _recovery_epoch003_expected_projection(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    source = event["source_closure"]
    bootstrap = event["bootstrap_closure"]
    return {
        "source_commit_sha1": source["source_commit_sha1"],
        "source_tree_sha1": source["source_tree_sha1"],
        "formal_owner_artifacts_sha256": bootstrap[
            "formal_owner_artifacts_sha256"
        ],
        "formal_test_manifest_sha256": bootstrap[
            "formal_test_manifest_sha256"
        ],
        "import_manifest_sha256": bootstrap["import_manifest_sha256"],
        "dependency_lock_raw_sha256": bootstrap[
            "dependency_lock_identity"
        ]["raw_sha256"],
        "wheel_bundle_manifest_sha256": bootstrap[
            "wheel_bundle_manifest_sha256"
        ],
        "installed_distributions_sha256": bootstrap[
            "expected_installed_distributions_sha256"
        ],
        "pytest_distribution_identity": deepcopy(
            bootstrap["expected_pytest_distribution_identity"]
        ),
        "python_runtime_identity": deepcopy(
            bootstrap["expected_python_runtime_identity"]
        ),
        "loaded_plugin_manifest_sha256": bootstrap[
            "loaded_plugin_manifest_sha256"
        ],
        "preflight_argv_sha256": bootstrap["preflight_argv_sha256"],
        "formal_worker_argv_sha256": bootstrap[
            "formal_worker_argv_sha256"
        ],
        "environment_policy_sha256": bootstrap[
            "environment_policy_sha256"
        ],
    }


def _recovery_epoch003_observed_projection(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: deepcopy(observation[key])
        for key in RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS
    }


def _recovery_epoch003_external_identity_valid(
    value: Any,
    *,
    roles: frozenset[str],
    schema: str,
    path: str,
    logical_hash: str,
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        and value.get("artifact_role") in roles
        and value.get("schema_version") == schema
        and value.get("path") == path
        and value.get("repository_full_name") == "MassyuRed/Cocolon"
        and value.get("body_free") is True
        and _SHA1_RE.fullmatch(str(value.get("git_blob_sha1", "")))
        is not None
        and _SHA1_RE.fullmatch(
            str(value.get("publication_commit_sha1", ""))
        )
        is not None
        and _SHA256_RE.fullmatch(str(value.get("raw_sha256", "")))
        is not None
        and _SHA256_RE.fullmatch(str(logical_hash)) is not None
        and value.get("logical_artifact_sha256") == logical_hash
        and value.get("identity_sha256")
        == _hash_without(value, "identity_sha256")
    )


def _recovery_epoch003_sha1(value: Any) -> bool:
    return (
        isinstance(value, str)
        and _SHA1_RE.fullmatch(value) is not None
    )


def _recovery_epoch003_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and _SHA256_RE.fullmatch(value) is not None
    )


def _recovery_epoch003_runtime_identity_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_RUNTIME_IDENTITY_KEYS
        and isinstance(value.get("implementation"), str)
        and bool(value.get("implementation"))
        and isinstance(value.get("version"), str)
        and bool(value.get("version"))
        and _recovery_epoch003_sha256(value.get("executable_sha256"))
        and _recovery_epoch003_sha256(value.get("build_sha256"))
        and value.get("executable_sha256") != "0" * 64
        and value.get("build_sha256") != "0" * 64
    )


def _recovery_epoch003_distribution_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
        and isinstance(value.get("normalized_distribution_name"), str)
        and bool(value.get("normalized_distribution_name"))
        and isinstance(value.get("distribution_version"), str)
        and bool(value.get("distribution_version"))
        and _recovery_epoch003_sha256(value.get("wheel_sha256"))
        and _recovery_epoch003_sha256(
            value.get("installed_record_closure_sha256")
        )
    )


def _recovery_epoch003_environment_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_ENVIRONMENT_KEYS
        and type(value.get("fixed")) is dict
        and set(value["fixed"]) == _RECOVERY_EPOCH003_ENVIRONMENT_FIXED_KEYS
        and value["fixed"].get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
        and value["fixed"].get("PYTHONDONTWRITEBYTECODE") == "1"
        and value.get("removed")
        == ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"]
        and _recovery_epoch003_sha256(
            value.get("inherited_path_sha256")
        )
        and value.get("inherited_path_sha256") != "0" * 64
        and isinstance(value.get("lang"), str)
        and bool(value.get("lang"))
        and isinstance(value.get("lc_all"), str)
        and bool(value.get("lc_all"))
    )


def _recovery_epoch003_materialization_valid(
    value: Any,
    *,
    dependency_lock_raw_sha256: str,
    wheel_bundle_manifest_sha256: str,
    distribution_count: int,
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_KEYS
        or value.get("schema_version")
        != _RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_SCHEMA
        or not _recovery_epoch003_sha256(
            value.get("runtime_root_identity_sha256")
        )
        or value.get("dependency_lock_raw_sha256")
        != dependency_lock_raw_sha256
        or value.get("wheel_bundle_manifest_sha256")
        != wheel_bundle_manifest_sha256
        or type(value.get("distribution_count")) is not int
        or value.get("distribution_count") != distribution_count
        or not isinstance(value.get("runtime_materialization_state"), str)
        or not value.get("runtime_materialization_state")
        or value.get("body_free") is not True
        or value.get("runtime_materialization_sha256")
        != _hash_without(value, "runtime_materialization_sha256")
    ):
        return False
    for key in (
        "python_executable_relative_path",
        "installed_directory_relative_path",
    ):
        path = value.get(key)
        if (
            not isinstance(path, str)
            or not path
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
        ):
            return False
    return True


def _recovery_epoch003_bootstrap_contract_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_BOOTSTRAP_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS[1][1]
        or not _recovery_epoch003_sha1(value.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(value.get("source_tree_sha1"))
        or value.get("body_free") is not True
        or value.get("bootstrap_closure_sha256")
        != _hash_without(value, "bootstrap_closure_sha256")
        or value.get("conftest_plugin_mode") != "NOCONFTEST"
        or value.get("pytest_plugins_environment_variable_removed")
        is not True
        or value.get("pytest_entrypoint_autoload_disabled") is not True
        or value.get("explicit_plugin_allowlist") != []
        or value.get("loaded_plugin_manifest") != []
        or value.get("loaded_plugin_manifest_sha256")
        != artifact_sha256([])
        or value.get("unclassified_import_count") != 0
        or value.get("unresolved_dynamic_import_count") != 0
    ):
        return False

    owners = value.get("formal_owner_artifacts")
    if (
        type(owners) is not list
        or len(owners) != 7
        or any(
            type(row) is not dict
            or set(row) != _RECOVERY_EPOCH003_OWNER_ROW_KEYS
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or not isinstance(row.get("path"), str)
            or not row.get("path")
            or not _recovery_epoch003_sha1(row.get("git_blob_sha1"))
            or not _recovery_epoch003_sha256(row.get("raw_sha256"))
            for row in owners
        )
        or artifact_sha256(
            [[row["role"], row["path"]] for row in owners]
        )
        != _RECOVERY_EPOCH003_OWNER_ROLE_PATHS_SHA256
        or value.get("formal_owner_artifacts_sha256")
        != artifact_sha256(owners)
    ):
        return False

    nodes = value.get("formal_test_node_ids")
    tests = value.get("formal_test_manifest")
    if (
        type(nodes) is not list
        or len(nodes) != 134
        or len(nodes) != len(set(nodes))
        or any(not isinstance(node, str) or not node for node in nodes)
        or artifact_sha256(nodes)
        != _RECOVERY_EPOCH003_FORMAL_NODE_IDS_SHA256
        or type(tests) is not list
        or len(tests) != 21
        or any(
            type(row) is not dict
            or set(row) != _RECOVERY_EPOCH003_TEST_ROW_KEYS
            or not isinstance(row.get("path"), str)
            or not row.get("path")
            or not _recovery_epoch003_sha1(row.get("git_blob_sha1"))
            or not _recovery_epoch003_sha256(row.get("raw_sha256"))
            for row in tests
        )
        or artifact_sha256([row["path"] for row in tests])
        != _RECOVERY_EPOCH003_FORMAL_TEST_PATHS_SHA256
        or value.get("formal_test_manifest_sha256")
        != artifact_sha256(tests)
    ):
        return False

    imports = value.get("import_manifest")
    if (
        type(imports) is not list
        or not imports
        or any(
            type(row) is not dict
            or set(row) != _RECOVERY_EPOCH003_IMPORT_ROW_KEYS
            or not isinstance(row.get("import_name"), str)
            or not row.get("import_name")
            or row.get("classification")
            not in {
                "FIRST_PARTY",
                "STDLIB_BOUND_TO_PYTHON_RUNTIME",
                "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
            }
            or type(row.get("owner_paths")) is not list
            or type(row.get("target_identity")) is not dict
            for row in imports
        )
        or [row["import_name"] for row in imports]
        != sorted({row["import_name"] for row in imports})
        or value.get("import_manifest_sha256") != artifact_sha256(imports)
    ):
        return False

    lock = value.get("dependency_lock_identity")
    installed = value.get("expected_installed_distributions")
    pytest_identity = value.get("expected_pytest_distribution_identity")
    runtime_identity = value.get("expected_python_runtime_identity")
    if (
        type(lock) is not dict
        or set(lock) != _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        or lock.get("identity_class") != "EXACT_HASH_LOCK"
        or not isinstance(lock.get("path"), str)
        or not lock.get("path")
        or not _recovery_epoch003_sha256(lock.get("raw_sha256"))
        or not _recovery_epoch003_sha256(
            value.get("wheel_bundle_manifest_sha256")
        )
        or type(installed) is not list
        or not installed
        or any(
            not _recovery_epoch003_distribution_valid(row)
            for row in installed
        )
        or [row["normalized_distribution_name"] for row in installed]
        != sorted(
            {
                row["normalized_distribution_name"]
                for row in installed
            }
        )
        or value.get("expected_installed_distributions_sha256")
        != artifact_sha256(installed)
        or not _recovery_epoch003_distribution_valid(pytest_identity)
        or pytest_identity.get("normalized_distribution_name") != "pytest"
        or pytest_identity not in installed
        or not _recovery_epoch003_runtime_identity_valid(runtime_identity)
    ):
        return False

    runtime_identity_hash = artifact_sha256(runtime_identity)
    distribution_by_name = {
        row["normalized_distribution_name"]: row for row in installed
    }
    for row in imports:
        target = row["target_identity"]
        owner_paths = row["owner_paths"]
        if (
            owner_paths != sorted(set(owner_paths))
            or any(
                not isinstance(path, str) or not path
                for path in owner_paths
            )
        ):
            return False
        if row["classification"] == "FIRST_PARTY":
            if (
                set(target) != _RECOVERY_EPOCH003_FIRST_PARTY_TARGET_KEYS
                or not owner_paths
                or not _recovery_epoch003_sha1(
                    target.get("git_blob_sha1")
                )
                or not _recovery_epoch003_sha256(
                    target.get("raw_sha256")
                )
            ):
                return False
        elif row["classification"] == "STDLIB_BOUND_TO_PYTHON_RUNTIME":
            if (
                set(target) != _RECOVERY_EPOCH003_STDLIB_TARGET_KEYS
                or target.get("module_name") != row["import_name"]
                or target.get("python_runtime_identity_sha256")
                != runtime_identity_hash
            ):
                return False
        else:
            distribution = distribution_by_name.get(
                target.get("normalized_distribution_name")
            )
            if (
                set(target) != _RECOVERY_EPOCH003_THIRD_PARTY_TARGET_KEYS
                or target.get("module_name") != row["import_name"]
                or distribution is None
                or {
                    key: target.get(key)
                    for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
                }
                != distribution
            ):
                return False

    reference_identity = value.get(
        "reference_runtime_observation_external_identity"
    )
    environment = value.get("environment_policy")
    preflight_argv = value.get("preflight_argv")
    formal_argv = value.get("formal_worker_argv")
    return bool(
        _recovery_epoch003_external_identity_valid(
            reference_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
            ),
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
            logical_hash=reference_identity.get(
                "logical_artifact_sha256"
            )
            if type(reference_identity) is dict
            else "",
        )
        and _recovery_epoch003_environment_valid(environment)
        and value.get("environment_policy_sha256")
        == artifact_sha256(environment)
        and preflight_argv == _RECOVERY_EPOCH003_PREFLIGHT_ARGV
        and value.get("preflight_argv_sha256")
        == artifact_sha256(preflight_argv)
        and formal_argv
        == [*_RECOVERY_EPOCH003_FORMAL_WORKER_ARGV_PREFIX, *nodes]
        and value.get("formal_worker_argv_sha256")
        == artifact_sha256(formal_argv)
    )


def _recovery_epoch003_source_contract_valid(
    source: Any,
    bootstrap: Mapping[str, Any],
) -> bool:
    if (
        type(source) is not dict
        or set(source) != _RECOVERY_EPOCH003_SOURCE_KEYS
        or source.get("schema_version")
        != RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS[1][0]
        or source.get("repository_full_name") != "MassyuRed/mashos-api"
        or source.get("source_ref") != "refs/heads/main"
        or source.get("worktree_clean") is not True
        or source.get("epoch003_p0_external_identity_sha256")
        != _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
        or not _recovery_epoch003_sha1(source.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(source.get("source_tree_sha1"))
        or source.get("source_commit_sha1")
        != bootstrap.get("source_commit_sha1")
        or source.get("source_tree_sha1")
        != bootstrap.get("source_tree_sha1")
        or source.get("formal_test_manifest_sha256")
        != bootstrap.get("formal_test_manifest_sha256")
        or source.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or source.get("source_closure_sha256")
        != _hash_without(source, "source_closure_sha256")
    ):
        return False
    return all(
        _recovery_epoch003_sha256(source.get(key))
        for key in _RECOVERY_EPOCH003_SOURCE_KEYS
        - {
            "schema_version",
            "repository_full_name",
            "source_ref",
            "source_commit_sha1",
            "source_tree_sha1",
            "worktree_clean",
        }
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


def _recovery_epoch003_current_event_nested_valid(
    event: Mapping[str, Any],
) -> bool:
    candidate = event.get("candidate_allocation")
    authority = event.get("authority")
    publication = event.get("publication")
    p0 = event.get("p0_external_identity")
    source = event.get("source_closure")
    bootstrap = event.get("bootstrap_closure")
    if any(
        type(value) is not dict
        for value in (
            candidate,
            authority,
            publication,
            p0,
            source,
            bootstrap,
            event.get("prior_event"),
            event.get("primary_evidence_artifact"),
        )
    ):
        return False
    reference = bootstrap.get(
        "reference_runtime_observation_external_identity"
    )
    admission = authority.get("operational_admission")
    if (
        event.get("challenge_id")
        in _RECOVERY_EPOCH003_HISTORICAL_CHALLENGE_IDS
        or not _recovery_epoch003_p0_valid(p0)
        or event.get("prior_event") != p0
        or type(candidate) is not dict
        or set(candidate) != _RECOVERY_EPOCH003_EVENT_CANDIDATE_KEYS
        or candidate.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "candidate_allocation.v1"
        )
        or candidate.get("logical_cycle_id")
        != event.get("logical_cycle_id")
        or candidate.get("recovery_epoch_id")
        != event.get("recovery_epoch_id")
        or candidate.get("candidate_version_id")
        != event.get("candidate_version_id")
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(candidate.get("allocated_at_utc", ""))
        )
        is None
        or candidate.get("p0_external_identity_sha256")
        != _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
        or candidate.get("source_closure_sha256")
        != source.get("source_closure_sha256")
        or type(reference) is not dict
        or candidate.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference.get("identity_sha256")
        or candidate.get("candidate_allocation_sha256")
        != _hash_without(candidate, "candidate_allocation_sha256")
        or type(authority) is not dict
        or set(authority) != _RECOVERY_EPOCH003_EVENT_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or authority.get("publication_authority_token")
        != _RECOVERY_EPOCH003_EVENT1_AUTHORITY
        or authority.get("transition_authority_token")
        != _RECOVERY_EPOCH003_EVENT1_AUTHORITY
        or not _recovery_epoch003_external_identity_valid(
            admission,
            roles=frozenset(
                {"RECOVERY_EPOCH003_OPERATIONAL_ADMISSION"}
            ),
            schema=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA,
            path=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH,
            logical_hash=(
                admission.get("logical_artifact_sha256")
                if type(admission) is dict
                else ""
            ),
        )
        or event.get("primary_evidence_artifact") != admission
        or not _recovery_epoch003_external_identity_valid(
            reference,
            roles=frozenset(
                {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
            ),
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
            logical_hash=reference.get("logical_artifact_sha256"),
        )
        or source.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference.get("identity_sha256")
        or type(publication) is not dict
        or set(publication) != _RECOVERY_EPOCH003_EVENT_PUBLICATION_KEYS
        or not _recovery_epoch003_sha1(
            publication.get("base_commit_sha1")
        )
        or publication.get("branch") != "main"
        or publication.get("event_path") != _RECOVERY_EPOCH003_EVENT_PATH
        or publication.get("repository_full_name") != "MassyuRed/Cocolon"
        or not isinstance(publication.get("publication_state"), str)
        or not publication.get("publication_state")
        or type(publication.get("supporting_artifacts")) is not list
        or _recovery_epoch003_event_contains_forbidden_key(event)
    ):
        return False
    supporting = publication["supporting_artifacts"]
    expected = sorted(
        [deepcopy(admission), deepcopy(reference)],
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        ),
    )
    return bool(
        supporting == expected
        and supporting
        == sorted(
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
        and publication.get("supporting_artifact_count") == 2
        and publication.get("expected_changed_path_count") == 1
        and publication.get("supporting_artifact_set_sha256")
        == artifact_sha256(supporting)
    )


def _recovery_epoch003_source_bootstrap_baseline_valid(
    state: Mapping[str, Any],
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    *,
    require_current_profile: bool,
) -> bool:
    reference_identity = bootstrap.get(
        "reference_runtime_observation_external_identity"
    )
    reference = state.get("reference_runtime_observation")
    state_reference_identity = state.get(
        "reference_runtime_observation_external_identity"
    )
    event = state.get("event1_at_publication")
    postfetch = state.get("event1_at_postfetch")
    event_identity = state.get("event1_external_identity")
    installed = (
        reference.get("installed_distributions")
        if type(reference) is dict
        else None
    )
    lock = (
        reference.get("dependency_lock_identity")
        if type(reference) is dict
        else None
    )
    runtime = (
        reference.get("runtime_materialization")
        if type(reference) is dict
        else None
    )
    if (
        state.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or state.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or not isinstance(state.get("candidate_version_id"), str)
        or not state.get("candidate_version_id")
        or not _recovery_epoch003_sha256(
            state.get("preflight_challenge_id")
        )
        or not _recovery_epoch003_sha256(state.get("preflight_id"))
        or state.get("reference_materialization_performed") is not True
        or state.get("reservation_count_delta") != 0
        or state.get("attempt_id") is not None
        or state.get("formal_exact134_invocation_count") != 0
        or state.get("collection_state") != "NOT_STARTED"
        or state.get("test_execution_state") != "NOT_STARTED"
        or state.get("pytest_main_called") is not False
        or state.get("automatic_progression") is not False
        or state.get("body_free") is not True
        or not _recovery_epoch003_bootstrap_contract_valid(bootstrap)
        or not _recovery_epoch003_source_contract_valid(
            source,
            bootstrap,
        )
        or type(reference_identity) is not dict
        or source.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or reference_identity != state_reference_identity
    ):
        return False
    if (
        type(reference) is not dict
        or set(reference) != _RECOVERY_EPOCH003_REFERENCE_KEYS
        or reference.get("schema_version")
        != _RECOVERY_EPOCH003_REFERENCE_SCHEMA
        or reference.get("logical_cycle_id")
        != state.get("logical_cycle_id")
        or reference.get("recovery_epoch_id")
        != state.get("recovery_epoch_id")
        or not isinstance(reference.get("authority_token"), str)
        or not reference.get("authority_token")
        or (
            require_current_profile
            and reference.get("authority_token")
            != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        )
        or reference.get("source_commit_sha1")
        != bootstrap.get("source_commit_sha1")
        or reference.get("source_tree_sha1")
        != bootstrap.get("source_tree_sha1")
        or reference.get("dependency_lock_identity")
        != bootstrap.get("dependency_lock_identity")
        or reference.get("wheel_bundle_manifest_sha256")
        != bootstrap.get("wheel_bundle_manifest_sha256")
        or reference.get("python_runtime_identity")
        != bootstrap.get("expected_python_runtime_identity")
        or reference.get("pytest_distribution_identity")
        != bootstrap.get("expected_pytest_distribution_identity")
        or reference.get("installed_distributions")
        != bootstrap.get("expected_installed_distributions")
        or reference.get("installed_distributions_sha256")
        != bootstrap.get("expected_installed_distributions_sha256")
        or reference.get("environment_policy")
        != bootstrap.get("environment_policy")
        or reference.get("environment_policy_sha256")
        != bootstrap.get("environment_policy_sha256")
        or type(installed) is not list
        or reference.get("installed_distributions_sha256")
        != artifact_sha256(installed)
        or reference.get("pytest_distribution_identity")
        not in installed
        or type(lock) is not dict
        or set(lock) != _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        or lock.get("identity_class") != "EXACT_HASH_LOCK"
        or not _recovery_epoch003_materialization_valid(
            runtime,
            dependency_lock_raw_sha256=lock.get("raw_sha256"),
            wheel_bundle_manifest_sha256=reference.get(
                "wheel_bundle_manifest_sha256"
            ),
            distribution_count=len(installed),
        )
        or reference.get("reservation_count_delta") != 0
        or reference.get("formal_exact134_invocation_count") != 0
        or reference.get("collection_state") != "NOT_STARTED"
        or reference.get("test_execution_state") != "NOT_STARTED"
        or reference.get("body_free") is not True
        or reference.get("reference_runtime_observation_sha256")
        != _hash_without(
            reference,
            "reference_runtime_observation_sha256",
        )
        or not _recovery_epoch003_external_identity_valid(
            state_reference_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
            ),
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
            logical_hash=reference.get(
                "reference_runtime_observation_sha256"
            ),
        )
    ):
        return False
    if (
        type(event) is not dict
        or set(event) != _RECOVERY_EPOCH003_EVENT_KEYS
        or event.get("schema_version") != _RECOVERY_EPOCH003_EVENT_SCHEMA
        or event.get("logical_cycle_id") != state.get("logical_cycle_id")
        or event.get("recovery_epoch_id")
        != state.get("recovery_epoch_id")
        or event.get("candidate_version_id")
        != state.get("candidate_version_id")
        or event.get("ledger_id")
        != "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003"
        or event.get("event_id")
        != "NLS_V3_RECOVERY_EPOCH003_SEQUENCE_EVENT_01"
        or event.get("event_ordinal") != 1
        or event.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or not isinstance(event.get("state"), str)
        or not event.get("state")
        or not _recovery_epoch003_sha256(event.get("challenge_id"))
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(event.get("timestamp_utc", ""))
        )
        is None
        or not isinstance(event.get("timestamp_kind"), str)
        or not event.get("timestamp_kind")
        or event.get("source_closure") != source
        or event.get("bootstrap_closure") != bootstrap
        or event.get("body_free") is not True
        or event.get("automatic_progression") is not False
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or (
            not (
                not require_current_profile
                and reference.get("authority_token")
                == "FIXTURE_ONLY_UNISSUED_REFERENCE_AUTHORITY"
                and event.get("timestamp_kind") == "FIXTURE_ONLY"
                and event.get("authority", {}).get("approval_kind")
                == "EXPLICIT_SEPARATE_AUTHORITY_FIXTURE_ONLY"
                and event.get("publication", {}).get("publication_state")
                == "FIXTURE_ONLY_NOT_PUBLISHED"
            )
            and not _recovery_epoch003_current_event_nested_valid(event)
        )
        or postfetch != event
        or state.get("event1_publication_raw_sha256")
        != hashlib.sha256(canonical_json_bytes(event) + b"\n").hexdigest()
        or state.get("event1_postfetch_raw_sha256")
        != state.get("event1_publication_raw_sha256")
        or not _recovery_epoch003_external_identity_valid(
            event_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT"}
            ),
            schema=_RECOVERY_EPOCH003_EVENT_SCHEMA,
            path=_RECOVERY_EPOCH003_EVENT_PATH,
            logical_hash=event.get("event_sha256"),
        )
    ):
        return False
    return True


def _recovery_epoch003_early_failure_receipt_valid(
    receipt: Any,
    *,
    failure_class: str,
    state: Mapping[str, Any],
) -> bool:
    stage = (
        "MATERIALIZATION_BINDING"
        if failure_class
        == "OPERATIONAL_MATERIALIZATION_BINDING_MISSING"
        else "BEFORE_MATERIALIZATION"
    )
    source = state.get("source_closure")
    bootstrap = state.get("bootstrap_closure")
    event_identity = state.get("event1_external_identity")
    return bool(
        type(receipt) is dict
        and set(receipt) == _RECOVERY_EPOCH003_FAILURE_KEYS
        and receipt.get("schema_version") == _RECOVERY_EPOCH003_FAILURE_SCHEMA
        and receipt.get("logical_cycle_id") == state.get("logical_cycle_id")
        and receipt.get("recovery_epoch_id")
        == state.get("recovery_epoch_id")
        and receipt.get("candidate_version_id")
        == state.get("candidate_version_id")
        and receipt.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and receipt.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        and isinstance(receipt.get("candidate_version_id"), str)
        and bool(receipt.get("candidate_version_id"))
        and receipt.get("authority_token")
        == "UNISSUED_RECOVERY_EPOCH003_PREFLIGHT_AUTHORITY"
        and _SHA256_RE.fullmatch(
            str(receipt.get("preflight_challenge_id", ""))
        )
        is not None
        and receipt.get("preflight_challenge_id")
        == state.get("preflight_challenge_id")
        and _SHA256_RE.fullmatch(str(receipt.get("preflight_id", "")))
        is not None
        and receipt.get("preflight_id") == state.get("preflight_id")
        and receipt.get("event1_external_identity_sha256")
        == (
            event_identity.get("identity_sha256")
            if type(event_identity) is dict
            else None
        )
        and _recovery_epoch003_sha256(
            receipt.get("event1_external_identity_sha256")
        )
        and receipt.get("source_closure_sha256")
        == (
            source.get("source_closure_sha256")
            if type(source) is dict
            else None
        )
        and _recovery_epoch003_sha256(
            receipt.get("source_closure_sha256")
        )
        and receipt.get("bootstrap_closure_sha256")
        == (
            bootstrap.get("bootstrap_closure_sha256")
            if type(bootstrap) is dict
            else None
        )
        and _recovery_epoch003_sha256(
            receipt.get("bootstrap_closure_sha256")
        )
        and receipt.get("operational_runtime_observation_state")
        == "NOT_AVAILABLE"
        and receipt.get("failure_stage") == stage
        and receipt.get("failure_class") == failure_class
        and receipt.get("failure_issue_codes") == [failure_class]
        and receipt.get("stop_code") == _RECOVERY_EPOCH003_STOP_CODE
        and receipt.get("reservation_count_delta") == 0
        and receipt.get("attempt_id") is None
        and receipt.get("formal_exact134_invocation_count") == 0
        and receipt.get("owner_validation_state") == "NOT_STARTED"
        and receipt.get("independent_verification_state")
        == "NOT_STARTED"
        and receipt.get("automatic_retry") is False
        and receipt.get("automatic_progression") is False
        and receipt.get("body_free") is True
        and (
            receipt.get(
                "operational_runtime_observation_external_identity"
            ),
            receipt.get("operational_runtime_observation_sha256"),
            receipt.get("owner_operational_projection_sha256"),
            receipt.get("independent_operational_projection_sha256"),
            receipt.get("expected_observed_projection_sha256"),
        )
        == (None, None, None, None, None)
        and receipt.get("receipt_sha256")
        == _hash_without(receipt, "receipt_sha256")
    )


def _recovery_epoch003_early_failure_result(
    state: Mapping[str, Any],
    failure_class: str,
) -> tuple[str, ...]:
    readiness = state.get("readiness_candidate")
    failure = state.get("failure_candidate")
    if type(failure) is dict:
        if (
            readiness is not None
            or not _recovery_epoch003_early_failure_receipt_valid(
                failure,
                failure_class=failure_class,
                state=state,
            )
        ):
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        return (failure_class,)
    if failure in {None, "EVALUATOR_MUST_BUILD_EXACT29"}:
        return (failure_class,)
    return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)


def _recovery_epoch003_identity_chain_valid(
    state: Mapping[str, Any],
    *,
    event: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> bool:
    reference = state.get("reference_runtime_observation")
    reference_identity = state.get(
        "reference_runtime_observation_external_identity"
    )
    event_identity = state.get("event1_external_identity")
    observation_identity = state.get(
        "operational_runtime_observation_external_identity"
    )
    bootstrap = state.get("bootstrap_closure")
    reference_runtime = (
        reference.get("runtime_materialization")
        if type(reference) is dict
        else None
    )
    operational_runtime = observation.get("runtime_materialization")
    installed = (
        bootstrap.get("expected_installed_distributions")
        if type(bootstrap) is dict
        else None
    )
    return bool(
        type(reference) is dict
        and set(reference) == _RECOVERY_EPOCH003_REFERENCE_KEYS
        and reference.get("schema_version")
        == _RECOVERY_EPOCH003_REFERENCE_SCHEMA
        and reference.get("reference_runtime_observation_sha256")
        == _hash_without(
            reference,
            "reference_runtime_observation_sha256",
        )
        and _recovery_epoch003_external_identity_valid(
            reference_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
            ),
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
            logical_hash=reference.get(
                "reference_runtime_observation_sha256"
            ),
        )
        and event.get("event_sha256")
        == _hash_without(event, "event_sha256")
        and _recovery_epoch003_external_identity_valid(
            event_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT"}
            ),
            schema=_RECOVERY_EPOCH003_EVENT_SCHEMA,
            path=_RECOVERY_EPOCH003_EVENT_PATH,
            logical_hash=event.get("event_sha256"),
        )
        and set(observation) == _RECOVERY_EPOCH003_OPERATIONAL_KEYS
        and observation.get("schema_version")
        == _RECOVERY_EPOCH003_OPERATIONAL_SCHEMA
        and observation.get("logical_cycle_id")
        == state.get("logical_cycle_id")
        and observation.get("recovery_epoch_id")
        == state.get("recovery_epoch_id")
        and observation.get("candidate_version_id")
        == state.get("candidate_version_id")
        and isinstance(observation.get("authority_token"), str)
        and bool(observation.get("authority_token"))
        and observation.get("preflight_challenge_id")
        == state.get("preflight_challenge_id")
        and observation.get("preflight_id") == state.get("preflight_id")
        and observation.get(
            "source_baseline_event_external_identity_sha256"
        )
        == event_identity.get("identity_sha256")
        and observation.get("source_closure_sha256")
        == event["source_closure"].get("source_closure_sha256")
        and observation.get("bootstrap_closure_sha256")
        == event["bootstrap_closure"].get("bootstrap_closure_sha256")
        and observation.get("worktree_clean") is True
        and observation.get("environment_policy")
        == bootstrap.get("environment_policy")
        and observation.get("environment_policy_sha256")
        == artifact_sha256(observation.get("environment_policy"))
        and type(installed) is list
        and _recovery_epoch003_materialization_valid(
            operational_runtime,
            dependency_lock_raw_sha256=observation.get(
                "dependency_lock_raw_sha256"
            ),
            wheel_bundle_manifest_sha256=observation.get(
                "wheel_bundle_manifest_sha256"
            ),
            distribution_count=len(installed),
        )
        and observation.get("runtime_root_identity_sha256")
        == operational_runtime.get("runtime_root_identity_sha256")
        and type(reference_runtime) is dict
        and observation.get("reference_runtime_root_identity_sha256")
        == reference_runtime.get("runtime_root_identity_sha256")
        and observation.get("runtime_root_identity_sha256")
        != observation.get("reference_runtime_root_identity_sha256")
        and _recovery_epoch003_sha256(
            observation.get("attempt_registry_root_identity_sha256")
        )
        and observation.get("owner_validation_state") == "VALID"
        and observation.get("independent_verification_state") == "VALID"
        and observation.get("reservation_count_delta") == 0
        and observation.get("formal_exact134_invocation_count") == 0
        and observation.get("collection_state") == "NOT_STARTED"
        and observation.get("test_execution_state") == "NOT_STARTED"
        and observation.get("pytest_main_called") is False
        and observation.get("body_free") is True
        and state.get("operational_materialization_performed") is True
        and observation.get("operational_runtime_observation_sha256")
        == _hash_without(
            observation,
            "operational_runtime_observation_sha256",
        )
        and _recovery_epoch003_external_identity_valid(
            observation_identity,
            roles=frozenset(
                {
                    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
                    (
                        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                        "OBSERVATION_FAILURE_EVIDENCE"
                    ),
                }
            ),
            schema=_RECOVERY_EPOCH003_OPERATIONAL_SCHEMA,
            path=_RECOVERY_EPOCH003_OPERATIONAL_PATH,
            logical_hash=observation.get(
                "operational_runtime_observation_sha256"
            ),
        )
    )


def _recovery_epoch003_readiness_valid(
    state: Mapping[str, Any],
    *,
    expected_hash: str,
    observed_hash: str,
) -> bool:
    readiness = state.get("readiness_candidate")
    event = state["event1_at_publication"]
    event_identity = state["event1_external_identity"]
    observation = state["operational_runtime_observation"]
    observation_identity = state[
        "operational_runtime_observation_external_identity"
    ]
    return bool(
        type(readiness) is dict
        and state.get("failure_candidate") is None
        and set(readiness) == _RECOVERY_EPOCH003_READINESS_KEYS
        and readiness.get("schema_version")
        == _RECOVERY_EPOCH003_READINESS_SCHEMA
        and readiness.get("logical_cycle_id")
        == state.get("logical_cycle_id")
        and readiness.get("recovery_epoch_id")
        == state.get("recovery_epoch_id")
        and readiness.get("candidate_version_id")
        == state.get("candidate_version_id")
        and readiness.get("authority_token")
        == observation.get("authority_token")
        and readiness.get("event1_external_identity_sha256")
        == event_identity.get("identity_sha256")
        and readiness.get("event1_bootstrap_closure")
        == event.get("bootstrap_closure")
        and readiness.get("event1_bootstrap_closure_sha256")
        == event["bootstrap_closure"].get("bootstrap_closure_sha256")
        and readiness.get(
            "operational_runtime_observation_external_identity"
        )
        == observation_identity
        and observation_identity.get("artifact_role")
        == "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
        and readiness.get("operational_runtime_observation_sha256")
        == observation.get("operational_runtime_observation_sha256")
        and readiness.get("expected_observed_projection_sha256")
        == artifact_sha256(
            {"expected": expected_hash, "observed": observed_hash}
        )
        and readiness.get("readiness_receipt_path")
        == _RECOVERY_EPOCH003_READINESS_PATH
        and readiness.get("preflight_started_at_utc")
        == state.get("preflight_started_at_utc")
        and readiness.get("preflight_finished_at_utc")
        == state.get("preflight_finished_at_utc")
        and _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(readiness.get("preflight_started_at_utc", ""))
        )
        is not None
        and _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(readiness.get("preflight_finished_at_utc", ""))
        )
        is not None
        and readiness.get("preflight_started_at_utc")
        <= readiness.get("preflight_finished_at_utc")
        and readiness.get("owner_validation_state") == "VALID"
        and readiness.get("independent_verification_state") == "VALID"
        and readiness.get("reservation_count_delta") == 0
        and readiness.get("formal_exact134_invocation_count") == 0
        and readiness.get("collection_state") == "NOT_STARTED"
        and readiness.get("test_execution_state") == "NOT_STARTED"
        and readiness.get("pytest_main_called") is False
        and readiness.get("automatic_progression") is False
        and readiness.get("body_free") is True
        and readiness.get("bootstrap_readiness_receipt_sha256")
        == _hash_without(
            readiness,
            "bootstrap_readiness_receipt_sha256",
        )
    )


def _recovery_epoch003_failure_receipt_valid(
    receipt: Any,
    *,
    state: Mapping[str, Any],
    failure_class: str,
    observation_hash: str,
    expected_hash: str,
    owner_hash: str,
    independent_hash: str,
) -> bool:
    observation = state.get("operational_runtime_observation")
    state_identity = state.get(
        "operational_runtime_observation_external_identity"
    )
    event_identity = state.get("event1_external_identity")
    source = state.get("source_closure")
    bootstrap = state.get("bootstrap_closure")
    expected_identity = (
        deepcopy(state_identity) if type(state_identity) is dict else None
    )
    if type(expected_identity) is dict:
        expected_identity["artifact_role"] = (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
            "OBSERVATION_FAILURE_EVIDENCE"
        )
        expected_identity["identity_sha256"] = _hash_without(
            expected_identity,
            "identity_sha256",
        )
    if (
        type(receipt) is not dict
        or set(receipt) != _RECOVERY_EPOCH003_FAILURE_KEYS
        or receipt.get("schema_version") != _RECOVERY_EPOCH003_FAILURE_SCHEMA
        or receipt.get("logical_cycle_id")
        != state.get("logical_cycle_id")
        or receipt.get("recovery_epoch_id")
        != state.get("recovery_epoch_id")
        or receipt.get("candidate_version_id")
        != state.get("candidate_version_id")
        or receipt.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or receipt.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or receipt.get("authority_token")
        != (
            observation.get("authority_token")
            if type(observation) is dict
            else None
        )
        or not isinstance(receipt.get("authority_token"), str)
        or not receipt.get("authority_token")
        or receipt.get("preflight_challenge_id")
        != state.get("preflight_challenge_id")
        or receipt.get("preflight_id") != state.get("preflight_id")
        or receipt.get("event1_external_identity_sha256")
        != (
            event_identity.get("identity_sha256")
            if type(event_identity) is dict
            else None
        )
        or receipt.get("source_closure_sha256")
        != (
            source.get("source_closure_sha256")
            if type(source) is dict
            else None
        )
        or receipt.get("bootstrap_closure_sha256")
        != (
            bootstrap.get("bootstrap_closure_sha256")
            if type(bootstrap) is dict
            else None
        )
        or not all(
            _recovery_epoch003_sha256(receipt.get(key))
            for key in (
                "preflight_challenge_id",
                "preflight_id",
                "event1_external_identity_sha256",
                "source_closure_sha256",
                "bootstrap_closure_sha256",
            )
        )
        or receipt.get("operational_runtime_observation_state")
        != "OBSERVED"
        or not all(
            _recovery_epoch003_sha256(value)
            for value in (
                observation_hash,
                expected_hash,
                owner_hash,
                independent_hash,
                receipt.get("expected_observed_projection_sha256"),
            )
        )
        or receipt.get("failure_class") != failure_class
        or receipt.get("failure_issue_codes") != [failure_class]
        or receipt.get("stop_code") != _RECOVERY_EPOCH003_STOP_CODE
        or receipt.get("reservation_count_delta") != 0
        or receipt.get("attempt_id") is not None
        or receipt.get("formal_exact134_invocation_count") != 0
        or receipt.get("automatic_retry") is not False
        or receipt.get("automatic_progression") is not False
        or receipt.get("body_free") is not True
        or receipt.get("receipt_sha256")
        != _hash_without(receipt, "receipt_sha256")
    ):
        return False
    identity = receipt.get(
        "operational_runtime_observation_external_identity"
    )
    combined_hash = receipt.get("expected_observed_projection_sha256")
    if (
        receipt.get("operational_runtime_observation_sha256")
        != observation_hash
        or receipt.get(
            "operational_runtime_observation_external_identity"
        )
        != expected_identity
        or not _recovery_epoch003_external_identity_valid(
            identity,
            roles=frozenset(
                {
                    (
                        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                        "OBSERVATION_FAILURE_EVIDENCE"
                    )
                }
            ),
            schema=_RECOVERY_EPOCH003_OPERATIONAL_SCHEMA,
            path=_RECOVERY_EPOCH003_OPERATIONAL_PATH,
            logical_hash=observation_hash,
        )
    ):
        return False
    if failure_class == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH":
        return bool(
            receipt.get("failure_stage")
            == "EXPECTED_OBSERVED_COMPARISON"
            and receipt.get("owner_validation_state") == "INVALID"
            and receipt.get("independent_verification_state") == "VALID"
            and receipt.get("owner_operational_projection_sha256")
            == owner_hash
            and receipt.get(
                "independent_operational_projection_sha256"
            )
            == owner_hash
            and combined_hash
            == artifact_sha256(
                {"expected": expected_hash, "observed": owner_hash}
            )
        )
    return bool(
        receipt.get("failure_stage") == "INDEPENDENT_PROJECTION"
        and receipt.get("owner_validation_state") == "VALID"
        and receipt.get("independent_verification_state") == "INVALID"
        and receipt.get("owner_operational_projection_sha256")
        == owner_hash
        and receipt.get(
            "independent_operational_projection_sha256"
        )
        == independent_hash
        and owner_hash != independent_hash
        and combined_hash
        == artifact_sha256(
            {"owner": owner_hash, "independent": independent_hash}
        )
    )


def _recovery_epoch003_p0_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_P0_KEYS
        or value.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.step11.cycle001."
            "recovery_epoch003.p0_external_identity.v1"
        )
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
    for row in (value["parent_design"], value["receipt"]):
        if (
            not _recovery_epoch003_sha1(
                row.get("publication_commit_sha1")
            )
            or not _recovery_epoch003_sha1(row.get("git_blob_sha1"))
            or not _recovery_epoch003_sha256(row.get("raw_sha256"))
        ):
            return False
    return bool(
        _recovery_epoch003_sha256(
            value["receipt"].get("logical_receipt_sha256")
        )
        and value.get("p0_external_identity_sha256")
        == _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
        == _hash_without(value, "p0_external_identity_sha256")
    )


def _recovery_epoch003_reference_body_valid(
    value: Any,
    *,
    strict_frozen: bool = False,
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_REFERENCE_KEYS
        or value.get("schema_version") != _RECOVERY_EPOCH003_REFERENCE_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or value.get("authority_token")
        != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        or not _recovery_epoch003_sha1(value.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(value.get("source_tree_sha1"))
        or value.get("reservation_count_delta") != 0
        or value.get("formal_exact134_invocation_count") != 0
        or value.get("collection_state") != "NOT_STARTED"
        or value.get("test_execution_state") != "NOT_STARTED"
        or value.get("body_free") is not True
        or value.get("reference_runtime_observation_sha256")
        != _hash_without(
            value,
            "reference_runtime_observation_sha256",
        )
    ):
        return False
    lock = value.get("dependency_lock_identity")
    installed = value.get("installed_distributions")
    environment = value.get("environment_policy")
    structurally_valid = bool(
        type(lock) is dict
        and set(lock) == _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        and lock.get("identity_class") == "EXACT_HASH_LOCK"
        and isinstance(lock.get("path"), str)
        and bool(lock.get("path"))
        and _recovery_epoch003_sha256(lock.get("raw_sha256"))
        and _recovery_epoch003_sha256(
            value.get("wheel_bundle_manifest_sha256")
        )
        and type(installed) is list
        and bool(installed)
        and all(
            _recovery_epoch003_distribution_valid(row)
            for row in installed
        )
        and [row["normalized_distribution_name"] for row in installed]
        == sorted(
            {
                row["normalized_distribution_name"]
                for row in installed
            }
        )
        and value.get("installed_distributions_sha256")
        == artifact_sha256(installed)
        and _recovery_epoch003_distribution_valid(
            value.get("pytest_distribution_identity")
        )
        and value.get("pytest_distribution_identity") in installed
        and value["pytest_distribution_identity"].get(
            "normalized_distribution_name"
        )
        == "pytest"
        and _recovery_epoch003_runtime_identity_valid(
            value.get("python_runtime_identity")
        )
        and _recovery_epoch003_environment_valid(environment)
        and value.get("environment_policy_sha256")
        == artifact_sha256(environment)
        and _recovery_epoch003_materialization_valid(
            value.get("runtime_materialization"),
            dependency_lock_raw_sha256=lock["raw_sha256"],
            wheel_bundle_manifest_sha256=value[
                "wheel_bundle_manifest_sha256"
            ],
            distribution_count=len(installed),
        )
    )
    if not structurally_valid:
        return False
    if not strict_frozen:
        return True
    runtime = value["python_runtime_identity"]
    materialization = value["runtime_materialization"]
    return bool(
        lock
        == {
            "identity_class": "EXACT_HASH_LOCK",
            "path": _RECOVERY_EPOCH003_LOCK_PATH,
            "raw_sha256": _RECOVERY_EPOCH003_LOCK_RAW_SHA256,
        }
        and len(installed) == 46
        and value.get("wheel_bundle_manifest_sha256")
        == _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        and value.get("installed_distributions_sha256")
        == _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
        and runtime.get("implementation") == "CPYTHON"
        and runtime.get("version") == "3.12.13"
        and materialization.get("runtime_materialization_state")
        == "VERIFIED_LOCKED_REFERENCE_RUNTIME"
        and materialization.get("dependency_lock_raw_sha256")
        == _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        and materialization.get("wheel_bundle_manifest_sha256")
        == _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        and materialization.get("distribution_count") == 46
    )


def _recovery_epoch003_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _recovery_epoch003_actual_artifact_identity_valid(
    root: Path,
    identity: Mapping[str, Any],
    body: Mapping[str, Any],
) -> bool:
    commit = identity["publication_commit_sha1"]
    path = identity["path"]
    try:
        blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{commit}:{path}",
        )
        raw = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
        observed = load_canonical_json_bytes(raw)
        head_blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"HEAD:{path}",
        )
        intervening = _recovery_epoch003_git(
            root,
            "rev-list",
            f"{commit}..HEAD",
            "--",
            path,
        ).splitlines()
        reachable = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    return bool(
        reachable
        and blob == identity.get("git_blob_sha1")
        and head_blob == blob
        and intervening == []
        and hashlib.sha256(raw).hexdigest()
        == identity.get("raw_sha256")
        and raw == canonical_json_bytes(body) + b"\n"
        and observed == body
    )


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


def _recovery_epoch003_reference_publication_shape_valid(
    value: Any,
    *,
    reference: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    return bool(
        type(value) is dict
        and set(value)
        == _RECOVERY_EPOCH003_REFERENCE_PUBLICATION_STATE_KEYS
        and isinstance(value.get("artifact_repository_root"), str)
        and bool(value.get("artifact_repository_root"))
        and value.get("external_identity") == reference_identity
        and value.get("postfetch_body") == reference
        and _recovery_epoch003_sha1(
            value.get("admission_base_commit_sha1")
        )
        and _recovery_epoch003_sha1(
            value.get("admission_base_tree_sha1")
        )
        and value.get(
            "reference_publication_is_ancestor_of_admission_base"
        )
        is True
        and value.get("reference_path_blob_at_admission_base_sha1")
        == reference_identity.get("git_blob_sha1")
    )


def _recovery_epoch003_reference_publication_actual_valid(
    value: Mapping[str, Any],
    *,
    reference: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    root = Path(value["artifact_repository_root"]).resolve()
    base = value["admission_base_commit_sha1"]
    publication_commit = reference_identity["publication_commit_sha1"]
    try:
        tree = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{base}^{{tree}}",
        )
        blob = _recovery_epoch003_git(
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
                base,
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        base_reaches_head = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, "HEAD"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        publication_parents = _recovery_epoch003_git(
            root,
            "show",
            "-s",
            "--format=%P",
            publication_commit,
        ).split()
        publication_changed_paths = _recovery_epoch003_git_changed_paths(
            root,
            publication_commit,
        )
        intervening_path_commits = _recovery_epoch003_git(
            root,
            "rev-list",
            f"{publication_commit}..{base}",
            "--",
            _RECOVERY_EPOCH003_REFERENCE_PATH,
        ).splitlines()
        parent_path_exists = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                (
                    f"{publication_parents[0]}:"
                    f"{_RECOVERY_EPOCH003_REFERENCE_PATH}"
                ),
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
    except (IndexError, OSError, subprocess.SubprocessError):
        return False
    return bool(
        value.get("admission_base_tree_sha1") == tree
        and value.get(
            "reference_publication_is_ancestor_of_admission_base"
        )
        is ancestry
        and ancestry
        and base_reaches_head
        and len(publication_parents) == 1
        and publication_changed_paths
        == [_RECOVERY_EPOCH003_REFERENCE_PATH]
        and not parent_path_exists
        and intervening_path_commits == []
        and value.get("reference_path_blob_at_admission_base_sha1")
        == blob
        == reference_identity.get("git_blob_sha1")
        and _recovery_epoch003_actual_artifact_identity_valid(
            root,
            reference_identity,
            reference,
        )
    )


def _recovery_epoch003_paths_disjoint(left: Path, right: Path) -> bool:
    if left == right:
        return False
    try:
        left.relative_to(right)
        return False
    except ValueError:
        pass
    try:
        right.relative_to(left)
        return False
    except ValueError:
        return True


def _recovery_epoch003_path_has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _recovery_epoch003_expected_repository(
    root: Path,
    repository_name: str,
) -> bool:
    try:
        head = _recovery_epoch003_git(root, "rev-parse", "HEAD")
        main = _recovery_epoch003_git(
            root,
            "rev-parse",
            "refs/heads/main",
        )
        top_level = Path(
            _recovery_epoch003_git(
                root,
                "rev-parse",
                "--show-toplevel",
            )
        ).resolve()
        origin = _recovery_epoch003_git(
            root,
            "config",
            "--get",
            "remote.origin.url",
        ).rstrip("/").removesuffix(".git")
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(
        top_level == root
        and head == main
        and (
            origin.endswith(f"/MassyuRed/{repository_name}")
            or origin.endswith(f":MassyuRed/{repository_name}")
        )
    )


def _recovery_epoch003_strict_json_file(
    path: Path,
) -> tuple[dict[str, Any], bytes] | None:
    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key")
            value[key] = item
        return value

    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            observed = os.fstat(descriptor)
            if not stat.S_ISREG(observed.st_mode):
                return None
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
        finally:
            os.close(descriptor)
        raw = b"".join(chunks)
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(token)
            ),
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return None
    return (value, raw) if type(value) is dict else None


def _recovery_epoch003_environment_policy(
    environment: Any,
) -> dict[str, Any] | None:
    if (
        type(environment) is not dict
        or any(
            not isinstance(key, str)
            or not isinstance(value, str)
            for key, value in environment.items()
        )
        or any(
            key.startswith("PIP_")
            or key
            in {
                "PYTHONPATH",
                "PYTHONHOME",
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
            }
            for key in environment
        )
    ):
        return None
    path = environment.get("PATH")
    lang = environment.get("LANG")
    lc_all = environment.get("LC_ALL")
    if not all(
        isinstance(value, str) and bool(value)
        for value in (path, lang, lc_all)
    ):
        return None
    return {
        "fixed": {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        "removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"],
        "inherited_path_sha256": hashlib.sha256(
            path.encode("utf-8")
        ).hexdigest(),
        "lang": lang,
        "lc_all": lc_all,
    }


def _recovery_epoch003_sanitized_environment(
    environment: Mapping[str, str],
) -> dict[str, str]:
    return {
        "PATH": environment["PATH"],
        "LANG": environment["LANG"],
        "LC_ALL": environment["LC_ALL"],
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _recovery_epoch003_wheel_record_sha256(path: Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/RECORD")
            ]
            if len(names) != 1:
                return None
            return hashlib.sha256(archive.read(names[0])).hexdigest()
    except (OSError, KeyError, zipfile.BadZipFile):
        return None


def _recovery_epoch003_normalize_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _recovery_epoch003_wheel_metadata(
    path: Path,
) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            metadata_names = [
                name
                for name in names
                if name.endswith(".dist-info/METADATA")
            ]
            top_level_names = [
                name
                for name in names
                if name.endswith(".dist-info/top_level.txt")
            ]
            if len(metadata_names) != 1:
                return None
            message = BytesParser(policy=compat32).parsebytes(
                archive.read(metadata_names[0])
            )
            raw_name = message.get("Name")
            version = message.get("Version")
            if not isinstance(raw_name, str) or not isinstance(version, str):
                return None
            top_levels: set[str] = set()
            if len(top_level_names) == 1:
                top_levels.update(
                    line.strip()
                    for line in archive.read(top_level_names[0])
                    .decode("utf-8")
                    .splitlines()
                    if line.strip()
                )
            if not top_levels:
                for member in names:
                    parts = member.split("/")
                    if not parts or parts[0].endswith(".dist-info"):
                        continue
                    if parts[0].endswith(".data"):
                        if (
                            len(parts) >= 3
                            and parts[1] in {"purelib", "platlib"}
                        ):
                            parts = parts[2:]
                        else:
                            continue
                    first = parts[0]
                    if first.endswith(".py"):
                        first = first[:-3]
                    if first.isidentifier() and first != "__pycache__":
                        top_levels.add(first)
            return {
                "normalized_distribution_name": (
                    _recovery_epoch003_normalize_distribution_name(
                        raw_name
                    )
                ),
                "distribution_version": version,
                "requires_dist": sorted(
                    message.get_all("Requires-Dist") or []
                ),
                "top_level_imports": sorted(top_levels),
            }
    except (OSError, UnicodeError, KeyError, zipfile.BadZipFile):
        return None


def _recovery_epoch003_wheel_directory_valid(
    directory: Path,
    lock: Mapping[str, Any],
    *,
    immutable: bool,
) -> bool:
    try:
        entries = list(os.scandir(directory))
        rows = lock["distributions"]
        expected_names = {row["wheel_filename"] for row in rows}
        if (
            directory.is_symlink()
            or not directory.is_dir()
            or len(entries) != 46
            or {entry.name for entry in entries} != expected_names
            or any(
                entry.is_symlink()
                or not entry.is_file(follow_symlinks=False)
                for entry in entries
            )
            or (
                immutable
                and (
                    directory.stat().st_mode
                    & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                    or any(
                        entry.stat(follow_symlinks=False).st_mode
                        & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                        or entry.stat(follow_symlinks=False).st_nlink != 1
                        or entry.stat(follow_symlinks=False).st_uid
                        != os.geteuid()
                        for entry in entries
                    )
                )
            )
        ):
            return False
        for row in rows:
            wheel = directory / row["wheel_filename"]
            payload = wheel.read_bytes()
            metadata = _recovery_epoch003_wheel_metadata(wheel)
            if (
                hashlib.sha256(payload).hexdigest()
                != row["wheel_sha256"]
                or _recovery_epoch003_wheel_record_sha256(wheel)
                != row["wheel_record_sha256"]
                or metadata
                != {
                    "normalized_distribution_name": row[
                        "normalized_distribution_name"
                    ],
                    "distribution_version": row[
                        "distribution_version"
                    ],
                    "requires_dist": row["requires_dist"],
                    "top_level_imports": row["top_level_imports"],
                }
            ):
                return False
    except (KeyError, OSError, TypeError):
        return False
    return True


def _recovery_epoch003_wheel_target_tags_valid(
    lock: Mapping[str, Any],
    target: Mapping[str, Any],
) -> bool:
    rows = lock.get("distributions")
    supported = target.get("supported_tags")
    observed = target.get("wheel_identities")
    if (
        type(rows) is not list
        or type(supported) is not list
        or not supported
        or supported != sorted(set(supported))
        or any(type(tag) is not str or not tag for tag in supported)
        or type(observed) is not list
        or len(observed) != len(rows)
    ):
        return False
    expected_by_filename = {
        row.get("wheel_filename"): row
        for row in rows
        if type(row) is dict
    }
    if (
        len(expected_by_filename) != len(rows)
        or [item.get("filename") for item in observed]
        != sorted(expected_by_filename)
    ):
        return False
    supported_set = set(supported)
    for item in observed:
        if (
            type(item) is not dict
            or set(item) != {"filename", "name", "version", "tags"}
        ):
            return False
        row = expected_by_filename.get(item["filename"])
        tags = item.get("tags")
        if (
            type(row) is not dict
            or _recovery_epoch003_normalize_distribution_name(
                str(item.get("name", ""))
            )
            != row.get("normalized_distribution_name")
            or item.get("version") != row.get("distribution_version")
            or type(tags) is not list
            or not tags
            or tags != sorted(set(tags))
            or any(type(tag) is not str or not tag for tag in tags)
            or not supported_set.intersection(tags)
        ):
            return False
    return True


def _recovery_epoch003_installed_closure(
    directory: Path,
    runtime_root: Path,
) -> dict[str, tuple[str, str]] | None:
    if (
        directory.is_symlink()
        or not directory.is_dir()
        or runtime_root.is_symlink()
        or not runtime_root.is_dir()
    ):
        return None
    directory = directory.absolute()
    runtime_root = runtime_root.absolute()
    try:
        directory.relative_to(runtime_root)
    except ValueError:
        return None

    def actual_file(path_text: str) -> tuple[Path, bool] | None:
        candidate = Path(
            os.path.normpath(str(directory / path_text))
        ).absolute()
        try:
            candidate.relative_to(runtime_root)
        except ValueError:
            return None
        current = runtime_root
        for component in candidate.relative_to(runtime_root).parts:
            current /= component
            try:
                current_stat = current.lstat()
            except OSError:
                return None
            if stat.S_ISLNK(current_stat.st_mode):
                return None
        try:
            final_stat = candidate.lstat()
        except OSError:
            return None
        if not stat.S_ISREG(final_stat.st_mode):
            return None
        try:
            candidate.relative_to(directory)
            importable = True
        except ValueError:
            importable = False
        return candidate, importable

    def digest_matches(path: Path, encoded: str, size: str) -> bool:
        payload = path.read_bytes()
        if size and int(size) != len(payload):
            return False
        if not encoded:
            return True
        try:
            algorithm, expected = encoded.split("=", 1)
        except ValueError:
            return False
        actual = base64.urlsafe_b64encode(
            hashlib.sha256(payload).digest()
        ).rstrip(b"=").decode("ascii")
        return algorithm == "sha256" and actual == expected

    result: dict[str, tuple[str, str]] = {}
    try:
        for metadata_path in sorted(
            directory.glob("*.dist-info/METADATA")
        ):
            record_path = metadata_path.parent / "RECORD"
            if (
                metadata_path.is_symlink()
                or record_path.is_symlink()
                or not metadata_path.is_file()
                or not record_path.is_file()
            ):
                return None
            message = BytesParser(policy=compat32).parsebytes(
                metadata_path.read_bytes()
            )
            raw_name = message.get("Name")
            version = message.get("Version")
            if not isinstance(raw_name, str) or not isinstance(version, str):
                return None
            name = _recovery_epoch003_normalize_distribution_name(
                raw_name
            )
            if name in result:
                return None
            closure_rows: list[dict[str, Any]] = []
            with record_path.open(
                encoding="utf-8",
                newline="",
            ) as handle:
                for path_text, digest, size in csv.reader(handle):
                    if (
                        path_text.endswith(".pyc")
                        or "/__pycache__/" in path_text
                    ):
                        continue
                    observed = actual_file(path_text)
                    if observed is None:
                        return None
                    actual_path, importable = observed
                    if not digest_matches(actual_path, digest, size):
                        return None
                    if (
                        not importable
                        or actual_path == record_path.absolute()
                    ):
                        continue
                    payload = actual_path.read_bytes()
                    closure_rows.append(
                        {
                            "path": actual_path.relative_to(
                                directory
                            ).as_posix(),
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "size": len(payload),
                        }
                    )
            closure_rows.sort(key=lambda row: row["path"])
            result[name] = (
                version,
                artifact_sha256({"record_entries": closure_rows}),
            )
    except (OSError, UnicodeError, ValueError):
        return None
    return result


def _recovery_epoch003_runtime_probe(
    python_executable: Path,
    environment: Mapping[str, str],
    wheel_filenames: list[str],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    probe = (
        "import json,platform,sys;"
        "from packaging.tags import sys_tags;"
        "from packaging.utils import parse_wheel_filename;"
        "filenames=json.loads(sys.argv[1]);"
        "parsed=[(f,parse_wheel_filename(f)) for f in filenames];"
        "print(json.dumps({"
        "'python_build':list(platform.python_build()),"
        "'python_compiler':platform.python_compiler(),"
        "'platform':platform.platform(),"
        "'system':platform.system(),"
        "'machine':platform.machine(),"
        "'abi_flags':sys.abiflags,"
        "'byte_order':sys.byteorder,"
        "'python_cache_tag':sys.implementation.cache_tag,"
        "'sys_platform':sys.platform,"
        "'implementation':platform.python_implementation().upper(),"
        "'version':platform.python_version(),"
        "'supported_tags':sorted(str(t) for t in sys_tags()),"
        "'wheel_identities':["
        "{'filename':f,'name':str(p[0]),'version':str(p[1]),"
        "'tags':sorted(str(t) for t in p[3])} for f,p in parsed]"
        "},sort_keys=True))"
    )
    try:
        if (
            python_executable.is_symlink()
            or not python_executable.is_file()
            or not stat.S_ISREG(python_executable.lstat().st_mode)
        ):
            return None
        observed = json.loads(
            subprocess.run(
                [
                    str(python_executable),
                    "-I",
                    "-B",
                    "-c",
                    probe,
                    json.dumps(wheel_filenames, separators=(",", ":")),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
                env=dict(environment),
            ).stdout
        )
        identity = {
            "executable_sha256": hashlib.sha256(
                python_executable.read_bytes()
            ).hexdigest(),
            "implementation": observed["implementation"],
            "version": observed["version"],
            "build_sha256": artifact_sha256(
                {
                    "python_build": observed["python_build"],
                    "python_compiler": observed["python_compiler"],
                    "platform": observed["platform"],
                    "abi_flags": observed["abi_flags"],
                }
            ),
        }
        target = {
            key: observed[key]
            for key in (
                "system",
                "machine",
                "abi_flags",
                "byte_order",
                "python_cache_tag",
                "sys_platform",
                "supported_tags",
                "wheel_identities",
            )
        }
    except (
        KeyError,
        OSError,
        subprocess.SubprocessError,
        TypeError,
        json.JSONDecodeError,
    ):
        return None
    return identity, target


def _recovery_epoch003_root_identity(
    runtime_root: Path,
    *,
    request: Mapping[str, Any],
    lock: Mapping[str, Any],
    installed: list[dict[str, Any]],
    runtime_identity: Mapping[str, Any],
    pytest_identity: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> str | None:
    nonce_path = runtime_root / _RECOVERY_EPOCH003_ROOT_NONCE_FILE
    try:
        descriptor = os.open(
            nonce_path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            nonce_stat = os.fstat(descriptor)
            nonce = os.read(descriptor, 33)
        finally:
            os.close(descriptor)
    except OSError:
        return None
    if (
        not stat.S_ISREG(nonce_stat.st_mode)
        or len(nonce) != 32
        or nonce_stat.st_nlink != 1
        or nonce_stat.st_uid != os.geteuid()
        or nonce_stat.st_mode
        & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
    ):
        return None
    wheel_manifest = [
        {
            "wheel_filename": row["wheel_filename"],
            "wheel_sha256": row["wheel_sha256"],
            "wheel_record_sha256": row["wheel_record_sha256"],
        }
        for row in lock["distributions"]
    ]
    preimage = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "runtime_root_identity_preimage.v1"
        ),
        "materialization_kind": "REFERENCE",
        "root_nonce_sha256": hashlib.sha256(nonce).hexdigest(),
        "source_commit_sha1": request["expected_source_commit_sha1"],
        "source_tree_sha1": request["expected_source_tree_sha1"],
        "dependency_lock_raw_sha256": (
            _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        ),
        "wheel_bundle_manifest_sha256": artifact_sha256(wheel_manifest),
        "installed_distributions_sha256": artifact_sha256(installed),
        "python_runtime_identity_sha256": artifact_sha256(
            runtime_identity
        ),
        "pytest_distribution_identity_sha256": artifact_sha256(
            pytest_identity
        ),
        "environment_policy_sha256": artifact_sha256(policy),
    }
    if set(preimage) != _RECOVERY_EPOCH003_ROOT_IDENTITY_PREIMAGE_KEYS:
        return None
    return artifact_sha256(preimage)


def _recovery_epoch003_materialization_state_valid(
    request: Any,
    result: Any,
    reference: Mapping[str, Any],
) -> bool:
    if (
        type(request) is not dict
        or set(request) != _RECOVERY_EPOCH003_MATERIALIZATION_REQUEST_KEYS
        or type(result) is not dict
        or set(result) != _RECOVERY_EPOCH003_MATERIALIZATION_RESULT_KEYS
        or request.get("authority_token")
        != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        or request.get("expected_source_commit_sha1")
        != reference.get("source_commit_sha1")
        or request.get("expected_source_tree_sha1")
        != reference.get("source_tree_sha1")
        or result.get("runtime_materialization")
        != reference.get("runtime_materialization")
    ):
        return False
    path_keys = (
        "artifact_repository_root",
        "source_repository_root",
        "dependency_lock_path",
        "wheelhouse_path",
        "destination_root",
    )
    if any(
        not isinstance(request.get(key), str) or not request.get(key)
        for key in path_keys
    ) or any(
        not isinstance(result.get(key), str) or not result.get(key)
        for key in ("runtime_root", "wheel_snapshot_root")
    ):
        return False
    raw_paths = {
        "artifact": Path(request["artifact_repository_root"]).absolute(),
        "source": Path(request["source_repository_root"]).absolute(),
        "lock": Path(request["dependency_lock_path"]).absolute(),
        "wheelhouse": Path(request["wheelhouse_path"]).absolute(),
        "destination": Path(request["destination_root"]).absolute(),
        "runtime": Path(result["runtime_root"]).absolute(),
        "snapshot": Path(result["wheel_snapshot_root"]).absolute(),
    }
    if any(
        _recovery_epoch003_path_has_symlink_component(path)
        for path in raw_paths.values()
    ):
        return False
    paths = {key: path.resolve() for key, path in raw_paths.items()}
    policy = _recovery_epoch003_environment_policy(
        request.get("environment")
    )
    if (
        policy is None
        or result.get("effective_environment_policy") != policy
        or reference.get("environment_policy") != policy
        or reference.get("environment_policy_sha256")
        != artifact_sha256(policy)
        or paths["destination"] != paths["runtime"]
        or paths["lock"]
        != (paths["source"] / _RECOVERY_EPOCH003_LOCK_PATH).resolve()
        or any(
            not _recovery_epoch003_paths_disjoint(
                paths[left],
                paths[right],
            )
            for left, right in (
                ("runtime", "snapshot"),
                ("runtime", "artifact"),
                ("runtime", "source"),
                ("runtime", "wheelhouse"),
                ("snapshot", "artifact"),
                ("snapshot", "source"),
                ("snapshot", "wheelhouse"),
                ("artifact", "source"),
            )
        )
        or not _recovery_epoch003_expected_repository(
            paths["artifact"],
            "Cocolon",
        )
        or not _recovery_epoch003_expected_repository(
            paths["source"],
            "mashos-api",
        )
    ):
        return False
    loaded = _recovery_epoch003_strict_json_file(paths["lock"])
    if loaded is None:
        return False
    lock, raw = loaded
    try:
        commit = _recovery_epoch003_git(
            paths["source"],
            "rev-parse",
            "HEAD",
        )
        tree = _recovery_epoch003_git(
            paths["source"],
            "rev-parse",
            "HEAD^{tree}",
        )
        clean = (
            _recovery_epoch003_git(
                paths["source"],
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        )
        rows = lock["distributions"]
        installed = [
            {
                key: row[key]
                for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
            }
            for row in rows
        ]
        installed.sort(
            key=lambda row: row["normalized_distribution_name"]
        )
        wheel_manifest = [
            {
                "wheel_filename": row["wheel_filename"],
                "wheel_sha256": row["wheel_sha256"],
                "wheel_record_sha256": row["wheel_record_sha256"],
            }
            for row in rows
        ]
    except (KeyError, TypeError):
        return False
    if (
        not clean
        or commit != request.get("expected_source_commit_sha1")
        or tree != request.get("expected_source_tree_sha1")
        or hashlib.sha256(raw).hexdigest()
        != _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        or lock.get("lock_sha256")
        != _RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256
        or lock.get("lock_sha256")
        != _hash_without(lock, "lock_sha256")
        or lock.get("distribution_count") != 46
        or type(rows) is not list
        or len(rows) != 46
        or lock.get("target", {}).get("implementation") != "CPYTHON"
        or lock.get("target", {}).get("python_version") != "3.12.13"
        or lock.get("target", {}).get("platform") != "linux-x86_64"
        or lock.get("target", {}).get("machine") != "x86_64"
        or lock.get("resolution", {}).get("pip_version") != "26.0.1"
        or artifact_sha256(wheel_manifest)
        != _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        or artifact_sha256(installed)
        != _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
        or reference.get("installed_distributions") != installed
        or not _recovery_epoch003_wheel_directory_valid(
            paths["wheelhouse"],
            lock,
            immutable=False,
        )
        or not _recovery_epoch003_wheel_directory_valid(
            paths["snapshot"],
            lock,
            immutable=True,
        )
    ):
        return False
    materialization = result.get("runtime_materialization")
    if (
        not _recovery_epoch003_materialization_valid(
            materialization,
            dependency_lock_raw_sha256=(
                _RECOVERY_EPOCH003_LOCK_RAW_SHA256
            ),
            wheel_bundle_manifest_sha256=(
                _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
            ),
            distribution_count=46,
        )
        or materialization.get("runtime_materialization_state")
        != "VERIFIED_LOCKED_REFERENCE_RUNTIME"
    ):
        return False
    python_relative = PurePosixPath(
        materialization["python_executable_relative_path"]
    )
    installed_relative = PurePosixPath(
        materialization["installed_directory_relative_path"]
    )
    if (
        python_relative.is_absolute()
        or installed_relative.is_absolute()
        or ".." in python_relative.parts
        or ".." in installed_relative.parts
    ):
        return False
    python_executable = paths["runtime"] / Path(*python_relative.parts)
    installed_directory = paths["runtime"] / Path(
        *installed_relative.parts
    )
    installed_closure = _recovery_epoch003_installed_closure(
        installed_directory,
        paths["runtime"],
    )
    if (
        installed_closure is None
        or set(installed_closure)
        != {
            row["normalized_distribution_name"] for row in installed
        }
        or any(
            installed_closure[row["normalized_distribution_name"]]
            != (
                row["distribution_version"],
                row["installed_record_closure_sha256"],
            )
            for row in installed
        )
    ):
        return False
    environment = _recovery_epoch003_sanitized_environment(
        request["environment"]
    )
    probed = _recovery_epoch003_runtime_probe(
        python_executable,
        environment,
        sorted(row["wheel_filename"] for row in rows),
    )
    if probed is None:
        return False
    runtime_identity, target = probed
    pytest_identity = next(
        (
            row
            for row in installed
            if row["normalized_distribution_name"] == "pytest"
        ),
        None,
    )
    if pytest_identity is None:
        return False
    try:
        installer_pip = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "pip",
                "--version",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.split()
        pytest_version = subprocess.run(
            [
                str(python_executable),
                "-I",
                "-B",
                "-c",
                (
                    "import importlib.metadata as m;"
                    "print(m.version('pytest'))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return False
    root_identity = _recovery_epoch003_root_identity(
        paths["runtime"],
        request=request,
        lock=lock,
        installed=installed,
        runtime_identity=runtime_identity,
        pytest_identity=pytest_identity,
        policy=policy,
    )
    return bool(
        runtime_identity == reference.get("python_runtime_identity")
        and _recovery_epoch003_wheel_target_tags_valid(lock, target)
        and runtime_identity.get("implementation") == "CPYTHON"
        and runtime_identity.get("version") == "3.12.13"
        and target.get("system") == "Linux"
        and target.get("machine") == "x86_64"
        and target.get("abi_flags")
        == lock["target"].get("abi_flags")
        and target.get("byte_order")
        == lock["target"].get("byte_order")
        and target.get("python_cache_tag")
        == lock["target"].get("python_cache_tag")
        and target.get("sys_platform") == "linux"
        and len(installer_pip) >= 2
        and installer_pip[1] == "26.0.1"
        and pytest_version == pytest_identity["distribution_version"]
        and reference.get("pytest_distribution_identity")
        == pytest_identity
        and root_identity
        == materialization.get("runtime_root_identity_sha256")
    )


def verify_recovery_epoch003_reference_runtime_observation(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Independently verify the transient reference runtime and receipt."""

    failure = (
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION_VERIFICATION_INVALID",
    )
    try:
        required = _keys(
            """
            verification_mode materialization_request
            materialization_result reference_runtime_observation
            reference_runtime_observation_external_identity
            reference_publication_state
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        mode = state.get("verification_mode")
        if mode not in {
            "BODY_ONLY_BEFORE_PUBLICATION",
            "BODY_AND_POSTFETCH",
        }:
            return failure
        reference = state.get("reference_runtime_observation")
        if (
            not _recovery_epoch003_reference_body_valid(
                reference,
                strict_frozen=True,
            )
            or not _recovery_epoch003_materialization_state_valid(
                state.get("materialization_request"),
                state.get("materialization_result"),
                reference,
            )
        ):
            return failure
        identity = state.get(
            "reference_runtime_observation_external_identity"
        )
        publication = state.get("reference_publication_state")
        if mode == "BODY_ONLY_BEFORE_PUBLICATION":
            return () if identity is None and publication is None else failure
        if (
            not _recovery_epoch003_external_identity_valid(
                identity,
                roles=frozenset(
                    {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
                ),
                schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
                path=_RECOVERY_EPOCH003_REFERENCE_PATH,
                logical_hash=reference[
                    "reference_runtime_observation_sha256"
                ],
            )
            or not _recovery_epoch003_reference_publication_shape_valid(
                publication,
                reference=reference,
                reference_identity=identity,
            )
            or not _recovery_epoch003_reference_publication_actual_valid(
                publication,
                reference=reference,
                reference_identity=identity,
            )
        ):
            return failure
        return ()
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


def _recovery_epoch003_generic_identity_valid(value: Any) -> bool:
    if type(value) is not dict:
        return False
    return _recovery_epoch003_external_identity_valid(
        value,
        roles=frozenset({str(value.get("artifact_role", ""))}),
        schema=str(value.get("schema_version", "")),
        path=str(value.get("path", "")),
        logical_hash=str(value.get("logical_artifact_sha256", "")),
    )


def _recovery_epoch003_admission_predecessors_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_PREDECESSOR_KEYS
        or not _recovery_epoch003_p0_valid(value.get("p0_external_identity"))
        or value.get("predecessor_bindings_sha256")
        != _hash_without(value, "predecessor_bindings_sha256")
    ):
        return False
    expected_roles = {
        (
            "operational_admission_parent_addendum_receipt_external_identity"
        ): (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PARENT_ADDENDUM_"
            "DESIGN_FROZEN_RECEIPT"
        ),
        "bootstrap_contract_d1_receipt_external_identity": (
            "RECOVERY_EPOCH003_D1_BOOTSTRAP_ORACLE_CORRECTION_CAUSAL_RED_"
            "REFREEZE_RECEIPT"
        ),
        "bootstrap_contract_d2_receipt_external_identity": (
            "RECOVERY_EPOCH003_D2_BOOTSTRAP_SOURCE_RUNTIME_TARGETED_GREEN_"
            "RECEIPT"
        ),
        (
            "operational_admission_contract_d1_receipt_external_identity"
        ): (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_CAUSAL_RED_"
            "RECEIPT"
        ),
        (
            "operational_admission_contract_d2_receipt_external_identity"
        ): (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_TARGETED_"
            "GREEN_RECEIPT"
        ),
        "reference_runtime_observation_external_identity": (
            "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"
        ),
    }
    if not all(
        _recovery_epoch003_generic_identity_valid(value.get(key))
        and value[key].get("artifact_role") == role
        for key, role in expected_roles.items()
    ):
        return False
    for key, contract in (
        _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS.items()
    ):
        role, schema, path, _fixed_identity = contract
        identity = value[key]
        if (
            identity.get("artifact_role") != role
            or identity.get("schema_version") != schema
            or identity.get("path") != path
        ):
            return False
    reference = value["reference_runtime_observation_external_identity"]
    return bool(
        reference.get("schema_version")
        == _RECOVERY_EPOCH003_REFERENCE_SCHEMA
        and reference.get("path") == _RECOVERY_EPOCH003_REFERENCE_PATH
    )


def _recovery_epoch003_predecessor_at_base_valid(
    root: Path,
    base: str,
    identity: Mapping[str, Any],
    *,
    fixed_identity_sha256: str | None,
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
        head_blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"HEAD:{path}",
        )
        raw = subprocess.run(
            ["git", "show", f"{base}:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
        body = load_canonical_json_bytes(raw)
        intervening = _recovery_epoch003_git(
            root,
            "rev-list",
            f"{commit}..{base}",
            "--",
            path,
        ).splitlines()
        after_base = _recovery_epoch003_git(
            root,
            "rev-list",
            f"{base}..HEAD",
            "--",
            path,
        ).splitlines()
        parent_path_exists = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{parents[0]}:{path}",
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
    except (
        IndexError,
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    return bool(
        len(parents) == 1
        and changed == [path]
        and not parent_path_exists
        and ancestry
        and intervening == []
        and after_base == []
        and blob == identity.get("git_blob_sha1")
        and head_blob == identity.get("git_blob_sha1")
        and hashlib.sha256(raw).hexdigest()
        == identity.get("raw_sha256")
        and (
            fixed_identity_sha256 is None
            or identity.get("identity_sha256")
            == fixed_identity_sha256
        )
        and raw == canonical_json_bytes(body) + b"\n"
        and body.get("schema_version")
        == identity.get("schema_version")
        and body.get("body_free") is True
        and body.get("receipt_sha256")
        == identity.get("logical_artifact_sha256")
        and body.get("receipt_sha256")
        == _hash_without(body, "receipt_sha256")
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
            head_blob = _recovery_epoch003_git(
                root,
                "rev-parse",
                f"HEAD:{path}",
            )
            raw = subprocess.run(
                ["git", "show", f"{base}:{path}"],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=20,
            ).stdout
            intervening = _recovery_epoch003_git(
                root,
                "rev-list",
                f"{commit}..{base}",
                "--",
                path,
            ).splitlines()
            after_base = _recovery_epoch003_git(
                root,
                "rev-list",
                f"{base}..HEAD",
                "--",
                path,
            ).splitlines()
        except (OSError, subprocess.SubprocessError):
            return False
        if (
            not ancestry
            or intervening != []
            or after_base != []
            or blob != member.get("git_blob_sha1")
            or head_blob != member.get("git_blob_sha1")
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
                != _hash_without(body, "receipt_sha256")
            ):
                return False
    return True


def _recovery_epoch003_predecessors_at_base_valid(
    root: Path,
    base: str,
    predecessors: Mapping[str, Any],
) -> bool:
    if (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", base, "HEAD"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode
        != 0
    ):
        return False
    if not _recovery_epoch003_p0_at_base_valid(
        root,
        base,
        predecessors["p0_external_identity"],
    ):
        return False
    for key, contract in (
        _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS.items()
    ):
        role, schema, path, fixed_identity = contract
        identity = predecessors[key]
        if (
            identity.get("artifact_role") != role
            or identity.get("schema_version") != schema
            or identity.get("path") != path
            or not _recovery_epoch003_predecessor_at_base_valid(
                root,
                base,
                identity,
                fixed_identity_sha256=fixed_identity,
            )
        ):
            return False
    return True


def _recovery_epoch003_admission_body_valid(
    admission: Any,
    *,
    reference: Mapping[str, Any],
) -> bool:
    if (
        type(admission) is not dict
        or set(admission) != _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS
        or admission.get("schema_version")
        != _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA
        or admission.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or admission.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or admission.get("owner_validation_state") != "PROVED"
        or admission.get("independent_verification_state") != "PROVED"
        or admission.get("state")
        != (
            "SOURCE_BOOTSTRAP_REFERENCE_RUNTIME_CLOSED_AWAITING_"
            "SEPARATE_CANDIDATE_EVENT1_AUTHORITY"
        )
        or admission.get("automatic_progression") is not False
        or admission.get("body_free") is not True
        or admission.get("operational_admission_sha256")
        != _hash_without(admission, "operational_admission_sha256")
        or not _recovery_epoch003_admission_predecessors_valid(
            admission.get("predecessor_bindings")
        )
    ):
        return False
    source = admission.get("source_closure")
    bootstrap = admission.get("bootstrap_closure")
    if (
        not _recovery_epoch003_bootstrap_contract_valid(bootstrap)
        or not _recovery_epoch003_source_contract_valid(source, bootstrap)
        or not _recovery_epoch003_reference_body_valid(reference)
    ):
        return False
    predecessors = admission["predecessor_bindings"]
    reference_identity = predecessors[
        "reference_runtime_observation_external_identity"
    ]
    if (
        bootstrap.get(
            "reference_runtime_observation_external_identity"
        )
        != reference_identity
        or source.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or reference_identity.get("logical_artifact_sha256")
        != reference.get("reference_runtime_observation_sha256")
        or reference.get("source_commit_sha1")
        != source.get("source_commit_sha1")
        or reference.get("source_tree_sha1")
        != source.get("source_tree_sha1")
    ):
        return False
    authority = admission.get("authority")
    scope = admission.get("scope")
    freshness = admission.get("freshness")
    effect = admission.get("effect_boundary")
    if (
        type(authority) is not dict
        or set(authority) != _RECOVERY_EPOCH003_ADMISSION_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or authority.get("admission_authority_token")
        != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        or authority.get("publication_authority_token")
        != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        or authority.get("authority_sha256")
        != _hash_without(authority, "authority_sha256")
        or type(scope) is not dict
        or set(scope) != _RECOVERY_EPOCH003_ADMISSION_SCOPE_KEYS
        or scope.get("artifact_repository_full_name")
        != "MassyuRed/Cocolon"
        or scope.get("source_repository_full_name")
        != "MassyuRed/mashos-api"
        or scope.get("source_ref") != "refs/heads/main"
        or scope.get("source_commit_sha1")
        != source.get("source_commit_sha1")
        or scope.get("source_tree_sha1") != source.get("source_tree_sha1")
        or scope.get("source_closure_sha256")
        != source.get("source_closure_sha256")
        or scope.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or scope.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or scope.get("next_authority_token")
        != _RECOVERY_EPOCH003_EVENT1_AUTHORITY
        or scope.get("operation_set")
        != list(_RECOVERY_EPOCH003_OPERATION_SET)
        or scope.get("separate_explicit_authority_required") is not True
        or scope.get("scope_sha256") != _hash_without(scope, "scope_sha256")
    ):
        return False
    if (
        type(freshness) is not dict
        or set(freshness) != _RECOVERY_EPOCH003_FRESHNESS_KEYS
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(freshness.get("issued_at_utc", ""))
        )
        is None
        or freshness.get("expires_at_utc") is not None
        or freshness.get("validity_mode")
        != "IDENTITY_STABLE_SINGLE_EVENT1_CONSUMPTION"
        or freshness.get("bound_source_commit_sha1")
        != source.get("source_commit_sha1")
        or freshness.get("bound_source_tree_sha1")
        != source.get("source_tree_sha1")
        or freshness.get(
            "bound_reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or freshness.get("event1_path_state_at_issuance") != "ABSENT"
        or freshness.get("maximum_event1_consumption_count") != 1
        or freshness.get("invalidation_conditions")
        != list(_RECOVERY_EPOCH003_INVALIDATION_CONDITIONS)
        or freshness.get("reuse_allowed") is not False
        or freshness.get("freshness_sha256")
        != _hash_without(freshness, "freshness_sha256")
    ):
        return False
    expected_effect = {
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
    }
    return bool(
        type(effect) is dict
        and set(effect) == _RECOVERY_EPOCH003_EFFECT_KEYS
        and all(effect.get(key) == value for key, value in expected_effect.items())
        and effect.get("effect_boundary_sha256")
        == _hash_without(effect, "effect_boundary_sha256")
    )


def _recovery_epoch003_source_observation_shape_valid(
    value: Any,
    *,
    source: Mapping[str, Any],
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_SOURCE_OBSERVATION_KEYS
        and isinstance(value.get("source_repository_root"), str)
        and bool(value.get("source_repository_root"))
        and value.get("source_commit_sha1")
        == source.get("source_commit_sha1")
        and value.get("source_tree_sha1") == source.get("source_tree_sha1")
        and value.get("worktree_clean") is True
    )


def _recovery_epoch003_source_observation_actual_valid(
    value: Mapping[str, Any],
) -> bool:
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
        and commit == value.get("source_commit_sha1")
        and tree == value.get("source_tree_sha1")
    )


def _recovery_epoch003_git_file_identity(
    root: Path,
    path: str,
) -> dict[str, str] | None:
    try:
        blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"HEAD:{path}",
        )
        raw = subprocess.run(
            ["git", "show", f"HEAD:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return {
        "path": path,
        "git_blob_sha1": blob,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _recovery_epoch003_literal_assignment(
    root: Path,
    path: str,
    name: str,
) -> Any:
    tree = ast.parse(
        subprocess.run(
            ["git", "show", f"HEAD:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout.decode("utf-8")
    )
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if (
            value is not None
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in targets
            )
        ):
            return ast.literal_eval(value)
    raise ValueError("literal assignment missing")


def _recovery_epoch003_top_level_symbols(
    root: Path,
    path: str,
) -> frozenset[str]:
    tree = ast.parse(
        subprocess.run(
            ["git", "show", f"HEAD:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout.decode("utf-8")
    )
    result: set[str] = set()
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            result.add(node.name)
        elif isinstance(node, ast.Import):
            result.update(
                alias.asname or alias.name.partition(".")[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            result.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name != "*"
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target]
            )
            result.update(
                target.id
                for target in targets
                if isinstance(target, ast.Name)
            )
    return frozenset(result)


def _recovery_epoch003_requirement_registry_actual_valid(
    root: Path,
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
) -> bool:
    path = _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH
    try:
        nodes_by_step = _recovery_epoch003_literal_assignment(
            root,
            path,
            "RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP",
        )
        rows = _recovery_epoch003_literal_assignment(
            root,
            path,
            "_RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS",
        )
        registry_hash = _recovery_epoch003_literal_assignment(
            root,
            path,
            "RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256",
        )
        formal_registry_hash = _recovery_epoch003_literal_assignment(
            root,
            path,
            "RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256",
        )
        registry_material = {
            "schema_version": _recovery_epoch003_literal_assignment(
                root,
                path,
                "RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_SCHEMA",
            ),
            "candidate_version_id": _recovery_epoch003_literal_assignment(
                root,
                path,
                "RECOVERY_EPOCH001_CANDIDATE_VERSION_ID",
            ),
            "recovery_epoch": 1,
            "red_freeze_authority": _recovery_epoch003_literal_assignment(
                root,
                path,
                "RECOVERY_EPOCH001_REGISTRY_RED_FREEZE_AUTHORITY",
            ),
            "detailed_design_sha256": _recovery_epoch003_literal_assignment(
                root,
                path,
                "RECOVERY_EPOCH001_DETAILED_DESIGN_SHA256",
            ),
            "required_sequence_event_1": (
                _recovery_epoch003_literal_assignment(
                    root,
                    path,
                    "RECOVERY_EPOCH001_REQUIRED_SEQUENCE_EVENT_1",
                )
            ),
            "completion_sequence_event_2": (
                _recovery_epoch003_literal_assignment(
                    root,
                    path,
                    "RECOVERY_EPOCH001_COMPLETION_SEQUENCE_EVENT_2",
                )
            ),
            "steps": rows,
            "automatic_progression": False,
            "body_free": True,
        }
        ordered_nodes = [
            node
            for step in range(11)
            for node in nodes_by_step[step]
        ]
        formal_root = artifact_sha256(
            {
                "step_nodes": {
                    str(step): list(nodes_by_step[step])
                    for step in range(11)
                }
            }
        )
        if (
            type(nodes_by_step) is not dict
            or set(nodes_by_step) != set(range(11))
            or type(rows) is not list
            or len(rows) != 11
            or [row.get("step_number") for row in rows]
            != list(range(11))
            or ordered_nodes != bootstrap.get("formal_test_node_ids")
            or len(ordered_nodes) != 134
            or len(set(ordered_nodes)) != 134
            or formal_root != formal_registry_hash
            or formal_registry_hash
            != _RECOVERY_EPOCH003_FORMAL_NODE_REGISTRY_SHA256
            or registry_hash
            != _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_SHA256
            or artifact_sha256(registry_material) != registry_hash
            or source.get("requirement_registry_sha256")
            != registry_hash
            or source.get("formal_node_registry_sha256")
            != formal_registry_hash
        ):
            return False
        for step, row in enumerate(rows):
            if (
                type(row) is not dict
                or row.get("formal_completion_node_ids")
                != nodes_by_step[step]
            ):
                return False
            bindings = [
                *row.get("actual_owners", []),
                *[
                    {
                        "path": contract.get("validator_path"),
                        "symbol": contract.get("validator_symbol"),
                    }
                    for contract in row.get("strict_contracts", [])
                    if type(contract) is dict
                ],
            ]
            for binding in bindings:
                if type(binding) is not dict:
                    return False
                binding_path = binding.get("path")
                symbol = binding.get("symbol")
                if (
                    type(binding_path) is not str
                    or type(symbol) is not str
                    or symbol
                    not in _recovery_epoch003_top_level_symbols(
                        root,
                        binding_path,
                    )
                ):
                    return False
            for proof_key in (
                "positive_proof",
                "independent_negative_proof",
            ):
                proof = row.get(proof_key)
                if type(proof) is not dict:
                    return False
                proof_path = proof.get("source_path")
                node_id = proof.get("test_node_id")
                if (
                    type(proof_path) is not str
                    or type(node_id) is not str
                    or not node_id.startswith(f"{proof_path}::test_")
                    or node_id.rpartition("::")[2]
                    not in _recovery_epoch003_top_level_symbols(
                        root,
                        proof_path,
                    )
                ):
                    return False
    except (
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        SyntaxError,
        subprocess.SubprocessError,
    ):
        return False
    return True


def _recovery_epoch003_independent_import_manifest(
    root: Path,
    *,
    lock: Mapping[str, Any],
    runtime_identity: Mapping[str, Any],
    seed_paths: set[str],
) -> list[dict[str, Any]]:
    """Re-derive the owner import closure from repository bytes.

    This implementation is deliberately local to the independent verifier;
    it does not import or call the owner-side closure builder.
    """

    module_distribution_map = lock.get("module_distribution_map")
    distributions = {
        row.get("normalized_distribution_name"): row
        for row in lock.get("distributions", [])
        if type(row) is dict
    }
    if type(module_distribution_map) is not dict:
        raise ValueError("module distribution map invalid")
    tracked_modes = {
        path: metadata.split()[0]
        for line in _recovery_epoch003_git(
            root,
            "ls-files",
            "-s",
            "*.py",
        ).splitlines()
        if line and "\t" in line
        for metadata, path in [line.split("\t", 1)]
    }
    tracked_paths = tuple(
        sorted(
            path
            for path, mode in tracked_modes.items()
            if mode in {"100644", "100755"}
        )
    )
    tracked_set = frozenset(tracked_paths)

    def source_bytes(path: str) -> bytes:
        return subprocess.run(
            ["git", "show", f"HEAD:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout

    def search_roots(importer_path: str) -> tuple[PurePosixPath, ...]:
        if importer_path.startswith("ai/tests/"):
            return (
                PurePosixPath("ai/tests"),
                PurePosixPath("ai/tests/helpers"),
                PurePosixPath("ai/tools"),
                PurePosixPath("ai/services/ai_inference"),
                PurePosixPath("ai/services"),
                PurePosixPath(),
            )
        return (
            PurePosixPath("ai/tests/helpers"),
            PurePosixPath("ai/tools"),
            PurePosixPath("ai/services/ai_inference"),
            PurePosixPath("ai/services"),
            PurePosixPath(),
        )

    def resolve_first_party_binding(
        module_name: str,
        importer_path: str,
    ) -> tuple[str, PurePosixPath] | None:
        relative = PurePosixPath(*module_name.split("."))
        for search_root in search_roots(importer_path):
            for suffix in (
                relative / "__init__.py",
                PurePosixPath(f"{relative}.py"),
            ):
                candidate = (search_root / suffix).as_posix()
                if candidate in tracked_set:
                    return candidate, search_root
        return None

    def resolve_first_party(
        module_name: str,
        importer_path: str,
    ) -> str | None:
        binding = resolve_first_party_binding(module_name, importer_path)
        return binding[0] if binding is not None else None

    def relative_module(
        runtime_module_name: str | None,
        importer_is_package: bool,
        module_name: str | None,
        level: int,
    ) -> str:
        if level == 0:
            if module_name is None:
                raise ValueError("empty absolute import")
            return module_name
        if runtime_module_name is None:
            raise ValueError("relative file import has no runtime package")
        package = runtime_module_name.split(".")
        if not importer_is_package:
            package = package[:-1]
        if not package or level > len(package):
            raise ValueError("relative import above runtime package")
        base = package[: len(package) - level + 1]
        if module_name:
            base.extend(module_name.split("."))
        return ".".join(base)

    export_cache: dict[str, frozenset[str]] = {}

    def exported_names(path: str) -> frozenset[str]:
        cached = export_cache.get(path)
        if cached is not None:
            return cached
        tree = ast.parse(source_bytes(path).decode("utf-8"))
        names: set[str] = set()

        def bind(target: ast.AST) -> None:
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for child in target.elts:
                    bind(child)

        for statement in tree.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                names.add(statement.name)
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    bind(target)
            elif isinstance(statement, ast.AnnAssign):
                if statement.value is not None:
                    bind(statement.target)
            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    names.add(
                        alias.asname or alias.name.split(".", 1)[0]
                    )
            elif isinstance(statement, ast.ImportFrom):
                for alias in statement.names:
                    if alias.name != "*":
                        names.add(alias.asname or alias.name)
        result = frozenset(names)
        export_cache[path] = result
        return result

    def import_available(
        node: ast.AST,
        importer_path: str,
        runtime_module_name: str | None,
        importer_is_package: bool,
    ) -> bool:
        if isinstance(node, ast.Import):
            return all(
                resolve_first_party(alias.name, importer_path) is not None
                for alias in node.names
            )
        if not isinstance(node, ast.ImportFrom):
            return False
        base = relative_module(
            runtime_module_name,
            importer_is_package,
            node.module,
            node.level,
        )
        base_path = resolve_first_party(base, importer_path)
        exports = (
            exported_names(base_path)
            if base_path is not None
            else frozenset()
        )
        for alias in node.names:
            if alias.name == "*":
                return False
            if (
                resolve_first_party(
                    f"{base}.{alias.name}",
                    importer_path,
                )
                is not None
                or alias.name in exports
            ):
                continue
            return False
        return base_path is not None or bool(node.names)

    def import_error_only_handler(node: ast.ExceptHandler) -> bool:
        expected = {"ImportError", "ModuleNotFoundError"}
        if isinstance(node.type, ast.Name):
            return node.type.id in expected
        return bool(
            isinstance(node.type, ast.Tuple)
            and node.type.elts
            and all(
                isinstance(item, ast.Name) and item.id in expected
                for item in node.type.elts
            )
        )

    def runtime_nodes(
        node: ast.AST,
        importer_path: str,
        runtime_module_name: str | None,
        importer_is_package: bool,
    ) -> list[ast.AST]:
        result = [node]
        if isinstance(node, ast.Try):
            primary_imports = [
                statement
                for statement in node.body
                if isinstance(statement, (ast.Import, ast.ImportFrom))
            ]
            if (
                primary_imports
                and len(primary_imports) == len(node.body)
                and all(
                    import_available(
                        statement,
                        importer_path,
                        runtime_module_name,
                        importer_is_package,
                    )
                    for statement in primary_imports
                )
                and all(
                    import_error_only_handler(handler)
                    for handler in node.handlers
                )
            ):
                children: list[ast.AST] = [
                    *node.body,
                    *node.orelse,
                    *node.finalbody,
                ]
            else:
                children = [
                    *node.body,
                    *node.handlers,
                    *node.orelse,
                    *node.finalbody,
                ]
        else:
            children = list(ast.iter_child_nodes(node))
        for child in children:
            result.extend(
                runtime_nodes(
                    child,
                    importer_path,
                    runtime_module_name,
                    importer_is_package,
                )
            )
        return result

    importers: dict[str, set[str]] = {}
    first_party_targets: dict[str, str] = {}
    pending: list[tuple[str, str | None]] = [
        (path, None) for path in sorted(seed_paths)
    ]
    visited: set[tuple[str, str | None]] = set()

    def record(module_name: str, importer_path: str) -> None:
        if not module_name:
            raise ValueError("empty import")
        importers.setdefault(module_name, set()).add(importer_path)
        target_binding = resolve_first_party_binding(
            module_name,
            importer_path,
        )
        if target_binding is None:
            return
        target_path, selected_root = target_binding
        previous = first_party_targets.setdefault(
            module_name,
            target_path,
        )
        if previous != target_path:
            raise ValueError("ambiguous first-party import")
        parts = module_name.split(".")
        for index in range(1, len(parts)):
            package_name = ".".join(parts[:index])
            package_path = (
                selected_root
                / PurePosixPath(*parts[:index])
                / "__init__.py"
            ).as_posix()
            if package_path not in tracked_set:
                continue
            importers.setdefault(package_name, set()).add(importer_path)
            prior = first_party_targets.setdefault(
                package_name,
                package_path,
            )
            if prior != package_path:
                raise ValueError("ambiguous first-party package")
            package_item = (package_path, package_name)
            if package_item not in visited:
                pending.append(package_item)
        target_item = (target_path, module_name)
        if target_item not in visited:
            pending.append(target_item)

    def record_file(
        target_path: str,
        importer_path: str,
        runtime_context: str | None,
    ) -> None:
        import_name = f"file:{target_path}"
        importers.setdefault(import_name, set()).add(importer_path)
        previous = first_party_targets.setdefault(import_name, target_path)
        if previous != target_path:
            raise ValueError("ambiguous first-party file import")
        target_item = (target_path, runtime_context)
        if target_item not in visited:
            pending.append(target_item)

    while pending:
        path, runtime_module_name = pending.pop(0)
        visit_key = (path, runtime_module_name)
        if visit_key in visited:
            continue
        if path not in tracked_set:
            raise ValueError("untracked import owner")
        visited.add(visit_key)
        tree = ast.parse(source_bytes(path).decode("utf-8"))
        importer_is_package = path.endswith("/__init__.py")
        reachable = runtime_nodes(
            tree,
            path,
            runtime_module_name,
            importer_is_package,
        )
        reachable_ids = {id(node) for node in reachable}
        parent_by_id = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        scope_types = (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Lambda,
            ast.ClassDef,
        )

        def evaluate_paths(
            node: ast.AST,
            path_values: Mapping[str, set[Path]],
            collection_names: set[str],
        ) -> set[Path]:
            if isinstance(node, ast.Name):
                return set(path_values.get(node.id, ()))
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
            ):
                return {Path(node.value)}
            if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                groups = [
                    evaluate_paths(item, path_values, collection_names)
                    for item in node.elts
                ]
                if any(not group for group in groups):
                    return set()
                return {value for group in groups for value in group}
            if isinstance(node, ast.Dict):
                groups = [
                    evaluate_paths(item, path_values, collection_names)
                    for item in node.values
                ]
                if any(not group for group in groups):
                    return set()
                return {value for group in groups for value in group}
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                left_values = evaluate_paths(
                    node.left,
                    path_values,
                    collection_names,
                )
                right_values = evaluate_paths(
                    node.right,
                    path_values,
                    collection_names,
                )
                if not left_values or not right_values:
                    return set()
                return {
                    left / right
                    for left in left_values
                    for right in right_values
                }
            if isinstance(node, ast.Attribute) and node.attr == "parent":
                return {
                    value.parent
                    for value in evaluate_paths(
                        node.value,
                        path_values,
                        collection_names,
                    )
                }
            if isinstance(node, ast.Subscript):
                if (
                    isinstance(node.value, ast.Attribute)
                    and node.value.attr == "parents"
                    and isinstance(node.slice, ast.Constant)
                    and type(node.slice.value) is int
                ):
                    return {
                        value.parents[node.slice.value]
                        for value in evaluate_paths(
                            node.value.value,
                            path_values,
                            collection_names,
                        )
                        if 0 <= node.slice.value < len(value.parents)
                    }
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id in collection_names
                ):
                    return set(path_values.get(node.value.id, ()))
                return set()
            if isinstance(node, ast.Call):
                function = node.func
                if (
                    (
                        isinstance(function, ast.Name)
                        and function.id == "Path"
                    )
                    or (
                        isinstance(function, ast.Attribute)
                        and function.attr == "Path"
                    )
                ) and len(node.args) == 1 and not node.keywords:
                    return evaluate_paths(
                        node.args[0],
                        path_values,
                        collection_names,
                    )
                if isinstance(function, ast.Attribute):
                    base = evaluate_paths(
                        function.value,
                        path_values,
                        collection_names,
                    )
                    if (
                        function.attr in {"resolve", "absolute"}
                        and not node.args
                        and not node.keywords
                    ):
                        return {
                            (
                                value.absolute()
                                if value.is_absolute()
                                else (root / value).absolute()
                            )
                            for value in base
                        }
                    if function.attr == "joinpath":
                        if not node.args or node.keywords:
                            return set()
                        values = base
                        for argument in node.args:
                            argument_values = evaluate_paths(
                                argument,
                                path_values,
                                collection_names,
                            )
                            if not values or not argument_values:
                                return set()
                            values = {
                                left / right
                                for left in values
                                for right in argument_values
                            }
                        return values
            return set()

        def target_names(target: ast.AST) -> set[str]:
            if isinstance(target, ast.Name):
                return {target.id}
            if isinstance(target, (ast.Tuple, ast.List)):
                return {
                    name
                    for item in target.elts
                    for name in target_names(item)
                }
            return set()

        def scope_assignments(
            scope: ast.AST,
            *,
            before_line: int | None,
        ) -> list[ast.Assign | ast.AnnAssign | ast.For]:
            result: list[ast.Assign | ast.AnnAssign | ast.For] = []

            def visit(node: ast.AST) -> None:
                if node is not scope and isinstance(node, scope_types):
                    return
                if id(node) not in reachable_ids:
                    return
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.For)):
                    if (
                        before_line is None
                        or getattr(node, "lineno", before_line) < before_line
                    ):
                        result.append(node)
                for child in ast.iter_child_nodes(node):
                    visit(child)

            for child in ast.iter_child_nodes(scope):
                visit(child)
            return sorted(
                result,
                key=lambda item: (
                    getattr(item, "lineno", 0),
                    getattr(item, "col_offset", 0),
                ),
            )

        def apply_assignments(
            assignments: list[ast.Assign | ast.AnnAssign | ast.For],
            path_values: dict[str, set[Path]],
            collection_names: set[str],
        ) -> None:
            for _ in range(len(assignments) + 1):
                changed = False
                for assignment in assignments:
                    if isinstance(assignment, ast.Assign):
                        targets = list(assignment.targets)
                        value_node = assignment.value
                    elif isinstance(assignment, ast.AnnAssign):
                        targets = [assignment.target]
                        value_node = assignment.value
                    else:
                        targets = [assignment.target]
                        value_node = assignment.iter
                    if value_node is None:
                        continue
                    values = evaluate_paths(
                        value_node,
                        path_values,
                        collection_names,
                    )
                    is_collection = bool(
                        isinstance(
                            value_node,
                            (ast.Dict, ast.List, ast.Tuple, ast.Set),
                        )
                        or (
                            isinstance(value_node, ast.Name)
                            and value_node.id in collection_names
                        )
                    )
                    for target in targets:
                        for name in target_names(target):
                            if is_collection and name not in collection_names:
                                collection_names.add(name)
                                changed = True
                            if not values:
                                continue
                            previous = path_values.get(name, set())
                            merged = previous | values
                            if merged != previous:
                                path_values[name] = merged
                                changed = True
                if not changed:
                    break

        module_assignments = scope_assignments(
            tree,
            before_line=None,
        )

        def lexical_scope(node: ast.AST) -> ast.AST:
            current = parent_by_id.get(id(node))
            while current is not None:
                if isinstance(current, scope_types):
                    return current
                current = parent_by_id.get(id(current))
            return tree

        def environment_for(
            node: ast.AST,
        ) -> tuple[dict[str, set[Path]], set[str]]:
            path_values: dict[str, set[Path]] = {
                "__file__": {(root / path).absolute()}
            }
            collections: set[str] = set()
            apply_assignments(
                module_assignments,
                path_values,
                collections,
            )
            scope = lexical_scope(node)
            if scope is not tree:
                local_assignments = scope_assignments(
                    scope,
                    before_line=getattr(node, "lineno", 0),
                )
                local_bound = {
                    name
                    for assignment in scope_assignments(
                        scope,
                        before_line=None,
                    )
                    for target in (
                        list(assignment.targets)
                        if isinstance(assignment, ast.Assign)
                        else [assignment.target]
                    )
                    for name in target_names(target)
                }
                if isinstance(
                    scope,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
                ):
                    local_bound.update(
                        argument.arg
                        for argument in (
                            *scope.args.posonlyargs,
                            *scope.args.args,
                            *scope.args.kwonlyargs,
                        )
                    )
                    if scope.args.vararg is not None:
                        local_bound.add(scope.args.vararg.arg)
                    if scope.args.kwarg is not None:
                        local_bound.add(scope.args.kwarg.arg)
                for name in local_bound:
                    path_values.pop(name, None)
                    collections.discard(name)
                apply_assignments(
                    local_assignments,
                    path_values,
                    collections,
                )
            return path_values, collections

        resolved_file_targets: set[tuple[str, str | None]] = set()
        spec_bindings: dict[tuple[int, str], int] = {}
        exec_bindings: dict[tuple[int, str], int] = {}
        for node in reachable:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    record(alias.name, path)
            elif isinstance(node, ast.ImportFrom):
                base = relative_module(
                    runtime_module_name,
                    importer_is_package,
                    node.module,
                    node.level,
                )
                resolved_any = False
                if resolve_first_party(base, path) is not None:
                    record(base, path)
                    resolved_any = True
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidate = f"{base}.{alias.name}"
                    if resolve_first_party(candidate, path) is not None:
                        record(candidate, path)
                        resolved_any = True
                if not resolved_any:
                    record(base, path)
            elif isinstance(node, ast.Call):
                function = node.func
                function_name = (
                    function.id
                    if isinstance(function, ast.Name)
                    else (
                        function.attr
                        if isinstance(function, ast.Attribute)
                        else ""
                    )
                )
                if function_name in {"__import__", "import_module"}:
                    if (
                        not node.args
                        or not isinstance(node.args[0], ast.Constant)
                        or not isinstance(node.args[0].value, str)
                    ):
                        raise ValueError("unresolved dynamic import")
                    record(node.args[0].value, path)
                elif function_name == "spec_from_file_location":
                    if len(node.args) < 2:
                        raise ValueError("unresolved file import")
                    assignment = parent_by_id.get(id(node))
                    if (
                        isinstance(assignment, ast.Assign)
                        and assignment.value is node
                        and len(assignment.targets) == 1
                        and isinstance(assignment.targets[0], ast.Name)
                    ):
                        spec_name = assignment.targets[0].id
                    elif (
                        isinstance(assignment, ast.AnnAssign)
                        and assignment.value is node
                        and isinstance(assignment.target, ast.Name)
                    ):
                        spec_name = assignment.target.id
                    else:
                        raise ValueError("unbound file import spec")
                    scope_key = id(lexical_scope(node))
                    binding_key = (scope_key, spec_name)
                    spec_bindings[binding_key] = (
                        spec_bindings.get(binding_key, 0) + 1
                    )
                    path_values, collections = environment_for(node)
                    resolved: set[str] = set()
                    path_candidates = evaluate_paths(
                        node.args[1],
                        path_values,
                        collections,
                    )
                    if not path_candidates:
                        raise ValueError("unresolved file import")
                    for candidate in path_candidates:
                        absolute = (
                            candidate
                            if candidate.is_absolute()
                            else (root / candidate).absolute()
                        )
                        try:
                            relative = absolute.relative_to(root).as_posix()
                        except ValueError as exc:
                            raise ValueError(
                                "file import outside repository"
                            ) from exc
                        if relative not in tracked_set:
                            raise ValueError("untracked file import")
                        resolved.add(relative)
                    if not resolved:
                        raise ValueError("unresolved file import")
                    alias_values = evaluate_paths(
                        node.args[0],
                        path_values,
                        collections,
                    )
                    runtime_context: str | None = None
                    if len(alias_values) == 1:
                        alias = str(next(iter(alias_values)))
                        if (
                            alias
                            and all(
                                part.isidentifier()
                                for part in alias.split(".")
                            )
                        ):
                            runtime_context = alias
                    resolved_file_targets.update(
                        (candidate, runtime_context)
                        for candidate in sorted(resolved)
                    )
                elif function_name == "exec_module":
                    owner = (
                        function.value
                        if isinstance(function, ast.Attribute)
                        else None
                    )
                    if (
                        not isinstance(owner, ast.Attribute)
                        or owner.attr != "loader"
                        or not isinstance(owner.value, ast.Name)
                    ):
                        raise ValueError("unbound file import execution")
                    binding_key = (
                        id(lexical_scope(node)),
                        owner.value.id,
                    )
                    exec_bindings[binding_key] = (
                        exec_bindings.get(binding_key, 0) + 1
                    )
        if (
            set(spec_bindings) != set(exec_bindings)
            or any(count != 1 for count in spec_bindings.values())
            or any(count != 1 for count in exec_bindings.values())
        ):
            raise ValueError("unmatched file import execution")
        for target_path, runtime_context in sorted(
            resolved_file_targets,
            key=lambda item: (item[0], item[1] or ""),
        ):
            record_file(target_path, path, runtime_context)

    runtime_hash = artifact_sha256(runtime_identity)
    rows: list[dict[str, Any]] = []
    for import_name in sorted(importers):
        owner_paths = sorted(importers[import_name])
        first_party_path = first_party_targets.get(import_name)
        root_name = import_name.split(".", 1)[0]
        if first_party_path is not None:
            target = _recovery_epoch003_git_file_identity(
                root,
                first_party_path,
            )
            if target is None:
                raise ValueError("first-party target missing")
            rows.append(
                {
                    "import_name": import_name,
                    "classification": "FIRST_PARTY",
                    "owner_paths": owner_paths,
                    "target_identity": target,
                }
            )
        elif (
            root_name in sys.stdlib_module_names
            or import_name == "__future__"
        ):
            rows.append(
                {
                    "import_name": import_name,
                    "classification": (
                        "STDLIB_BOUND_TO_PYTHON_RUNTIME"
                    ),
                    "owner_paths": owner_paths,
                    "target_identity": {
                        "module_name": import_name,
                        "python_runtime_identity_sha256": runtime_hash,
                    },
                }
            )
        else:
            matching_prefixes = [
                prefix
                for prefix in module_distribution_map
                if (
                    import_name == prefix
                    or import_name.startswith(f"{prefix}.")
                )
            ]
            distribution_name = (
                module_distribution_map[
                    max(matching_prefixes, key=len)
                ]
                if matching_prefixes
                else None
            )
            distribution = distributions.get(distribution_name)
            if type(distribution) is not dict:
                raise ValueError(f"unclassified import: {import_name}")
            rows.append(
                {
                    "import_name": import_name,
                    "classification": (
                        "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION"
                    ),
                    "owner_paths": owner_paths,
                    "target_identity": {
                        "module_name": import_name,
                        **{
                            key: distribution[key]
                            for key in (
                                _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
                            )
                        },
                    },
                }
            )
    if not rows:
        raise ValueError("empty import manifest")
    return rows


def _recovery_epoch003_actual_source_bootstrap_valid(
    observation: Mapping[str, Any],
    admission: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> bool:
    root = Path(observation["source_repository_root"]).resolve()
    source = admission["source_closure"]
    bootstrap = admission["bootstrap_closure"]
    if (
        not _recovery_epoch003_expected_repository(root, "mashos-api")
        or not _recovery_epoch003_source_observation_actual_valid(
            observation
        )
        or not _recovery_epoch003_reference_body_valid(
            reference,
            strict_frozen=True,
        )
        or reference.get("source_commit_sha1")
        != source.get("source_commit_sha1")
        or reference.get("source_tree_sha1")
        != source.get("source_tree_sha1")
    ):
        return False
    owners = bootstrap["formal_owner_artifacts"]
    tests = bootstrap["formal_test_manifest"]
    for row in owners:
        actual = _recovery_epoch003_git_file_identity(
            root,
            row["path"],
        )
        if actual is None or {
            key: row[key] for key in actual
        } != actual:
            return False
    for row in tests:
        actual = _recovery_epoch003_git_file_identity(
            root,
            row["path"],
        )
        if actual != row:
            return False
    test_paths = {row["path"] for row in tests}
    for node_id in bootstrap["formal_test_node_ids"]:
        try:
            path, function_name = node_id.split("::", 1)
            raw = subprocess.run(
                ["git", "show", f"HEAD:{path}"],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=20,
            ).stdout
            tree = ast.parse(raw.decode("utf-8"))
        except (
            OSError,
            UnicodeError,
            ValueError,
            SyntaxError,
            subprocess.SubprocessError,
        ):
            return False
        if (
            path not in test_paths
            or not function_name.startswith("test_")
            or function_name
            not in {
                node.name
                for node in tree.body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            }
        ):
            return False
    for row in bootstrap["import_manifest"]:
        owner_paths = row["owner_paths"]
        if (
            owner_paths != sorted(set(owner_paths))
            or any(
                _recovery_epoch003_git_file_identity(root, path) is None
                for path in owner_paths
            )
        ):
            return False
        if row["classification"] == "FIRST_PARTY":
            actual = _recovery_epoch003_git_file_identity(
                root,
                row["target_identity"]["path"],
            )
            if actual != row["target_identity"]:
                return False
    lock_raw = subprocess.run(
        ["git", "show", f"HEAD:{_RECOVERY_EPOCH003_LOCK_PATH}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout
    try:
        lock = json.loads(lock_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return False
    independently_derived_imports = (
        _recovery_epoch003_independent_import_manifest(
            root,
            lock=lock,
            runtime_identity=bootstrap[
                "expected_python_runtime_identity"
            ],
            seed_paths={
                *(row["path"] for row in owners),
                *(row["path"] for row in tests),
            },
        )
    )
    proof_owner = next(
        (
            row
            for row in owners
            if row["role"] == "current_step_proof_gate"
        ),
        None,
    )
    return bool(
        hashlib.sha256(lock_raw).hexdigest()
        == _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        and lock.get("lock_sha256")
        == _RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256
        and source.get("detailed_design_sha256")
        == _RECOVERY_EPOCH003_DETAILED_DESIGN_SHA256
        and source.get("epoch003_p0_external_identity_sha256")
        == _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
        and source.get("epoch002_predecessor_set_sha256")
        == _RECOVERY_EPOCH003_EPOCH002_PREDECESSOR_SET_SHA256
        and source.get("d1_red_receipt_external_identity_sha256")
        == _RECOVERY_EPOCH003_CORRECTED_D1_IDENTITY_SHA256
        and source.get("d2_green_receipt_external_identity_sha256")
        == _RECOVERY_EPOCH003_BOOTSTRAP_D2_IDENTITY_SHA256
        and source.get("source_dependency_closure_sha256")
        == artifact_sha256(bootstrap["import_manifest"])
        and independently_derived_imports == bootstrap["import_manifest"]
        and _recovery_epoch003_requirement_registry_actual_valid(
            root,
            source,
            bootstrap,
        )
        and source.get("canonical_current_closure_sha256")
        == artifact_sha256(owners)
        and source.get("requirement_registry_sha256")
        == _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_SHA256
        and source.get("formal_node_registry_sha256")
        == _RECOVERY_EPOCH003_FORMAL_NODE_REGISTRY_SHA256
        and proof_owner is not None
        and source.get("proof_source_closure_sha256")
        == artifact_sha256(proof_owner)
        and source.get("formal_test_manifest_sha256")
        == artifact_sha256(tests)
        and source.get("bootstrap_closure_sha256")
        == bootstrap.get("bootstrap_closure_sha256")
    )


def _recovery_epoch003_admission_publication_actual_valid(
    state: Mapping[str, Any],
    *,
    admission: Mapping[str, Any],
    admission_identity: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> bool:
    root = Path(state["artifact_repository_root"]).resolve()
    reference_state = state["reference_publication_state"]
    commit = admission_identity["publication_commit_sha1"]
    try:
        parents = _recovery_epoch003_git(
            root,
            "show",
            "-s",
            "--format=%P",
            commit,
        ).split()
        changed = _recovery_epoch003_git_changed_paths(root, commit)
        base_tree = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{parents[0]}^{{tree}}",
        )
        admission_existed_at_base = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                (
                    f"{parents[0]}:"
                    f"{_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH}"
                ),
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        event_exists_at_commit = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{commit}:{_RECOVERY_EPOCH003_EVENT_PATH}",
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
    except (OSError, subprocess.SubprocessError, IndexError):
        return False
    return bool(
        len(parents) == 1
        and parents[0] == reference_state.get("admission_base_commit_sha1")
        and base_tree == reference_state.get("admission_base_tree_sha1")
        and changed == [_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH]
        and not admission_existed_at_base
        and not event_exists_at_commit
        and _recovery_epoch003_actual_artifact_identity_valid(
            root,
            admission_identity,
            admission,
        )
        and _recovery_epoch003_reference_publication_actual_valid(
            reference_state,
            reference=state["reference_runtime_observation"],
            reference_identity=reference_identity,
        )
    )


def verify_recovery_epoch003_operational_admission_contract(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Independently validate the admission body and causal publication."""

    failure = (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_VERIFICATION_INVALID",
    )
    try:
        required = _keys(
            """
            verification_mode artifact_repository_root
            source_repository_observation operational_admission
            operational_admission_external_identity
            reference_runtime_observation reference_publication_state
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        mode = state.get("verification_mode")
        if mode not in {
            "BODY_ONLY_BEFORE_PUBLICATION",
            "BODY_AND_POSTFETCH",
        }:
            return failure
        admission = state.get("operational_admission")
        reference = state.get("reference_runtime_observation")
        if (
            not _recovery_epoch003_admission_body_valid(
                admission,
                reference=reference,
            )
            or not _recovery_epoch003_source_observation_shape_valid(
                state.get("source_repository_observation"),
                source=admission["source_closure"],
            )
        ):
            return failure
        reference_identity = admission["predecessor_bindings"][
            "reference_runtime_observation_external_identity"
        ]
        if not _recovery_epoch003_reference_publication_shape_valid(
            state.get("reference_publication_state"),
            reference=reference,
            reference_identity=reference_identity,
        ):
            return failure
        admission_identity = state.get(
            "operational_admission_external_identity"
        )
        if mode == "BODY_ONLY_BEFORE_PUBLICATION":
            return () if admission_identity is None else failure
        if (
            not isinstance(state.get("artifact_repository_root"), str)
            or not state.get("artifact_repository_root")
            or not _recovery_epoch003_expected_repository(
                Path(state["artifact_repository_root"]).resolve(),
                "Cocolon",
            )
            or not _recovery_epoch003_external_identity_valid(
                admission_identity,
                roles=frozenset(
                    {"RECOVERY_EPOCH003_OPERATIONAL_ADMISSION"}
                ),
                schema=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA,
                path=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH,
                logical_hash=admission[
                    "operational_admission_sha256"
                ],
            )
            or not _recovery_epoch003_source_observation_actual_valid(
                state["source_repository_observation"]
            )
            or not _recovery_epoch003_reference_body_valid(
                reference,
                strict_frozen=True,
            )
            or not _recovery_epoch003_actual_source_bootstrap_valid(
                state["source_repository_observation"],
                admission,
                reference,
            )
            or not _recovery_epoch003_predecessors_at_base_valid(
                Path(state["artifact_repository_root"]).resolve(),
                state["reference_publication_state"][
                    "admission_base_commit_sha1"
                ],
                admission["predecessor_bindings"],
            )
            or not _recovery_epoch003_admission_publication_actual_valid(
                state,
                admission=admission,
                admission_identity=admission_identity,
                reference_identity=reference_identity,
            )
        ):
            return failure
        return ()
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


def _verify_recovery_epoch003_bootstrap_source_runtime_contract_impl(
    state: Mapping[str, Any],
    *,
    require_current_profile: bool,
) -> tuple[str, ...]:
    """Independently derive Epoch003 exact14 expected/observed projections."""

    try:
        if type(state) is not dict:
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        source = state.get("source_closure")
        bootstrap = state.get("bootstrap_closure")
        if type(source) is not dict or type(bootstrap) is not dict:
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        pair = (
            source.get("schema_version"),
            bootstrap.get("schema_version"),
        )
        if pair not in RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS:
            return _recovery_epoch003_early_failure_result(
                state,
                "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
            )
        if pair == RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS[0]:
            return (
                _recovery_epoch003_early_failure_result(
                    state,
                    "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
                )
                if require_current_profile
                else ()
            )
        if not _recovery_epoch003_source_bootstrap_baseline_valid(
            state,
            source,
            bootstrap,
            require_current_profile=require_current_profile,
        ):
            return _recovery_epoch003_early_failure_result(
                state,
                "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
            )

        event = state.get("event1_at_publication")
        observation = state.get("operational_runtime_observation")
        if type(event) is not dict or type(observation) is not dict:
            return _recovery_epoch003_early_failure_result(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
            )
        observation_identity = state.get(
            "operational_runtime_observation_external_identity"
        )
        if (
            not isinstance(observation.get("authority_token"), str)
            or not observation.get("authority_token")
            or not _recovery_epoch003_external_identity_valid(
                observation_identity,
                roles=frozenset(
                    {
                        (
                            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                            "OBSERVATION"
                        ),
                        (
                            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                            "OBSERVATION_FAILURE_EVIDENCE"
                        ),
                    }
                ),
                schema=_RECOVERY_EPOCH003_OPERATIONAL_SCHEMA,
                path=_RECOVERY_EPOCH003_OPERATIONAL_PATH,
                logical_hash=observation.get(
                    "operational_runtime_observation_sha256"
                ),
            )
        ):
            return _recovery_epoch003_early_failure_result(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
            )
        started = state.get("preflight_started_at_utc")
        finished = state.get("preflight_finished_at_utc")
        if (
            _RECOVERY_EPOCH003_UTC_RE.fullmatch(str(started)) is None
            or _RECOVERY_EPOCH003_UTC_RE.fullmatch(str(finished)) is None
            or started > finished
        ):
            return _recovery_epoch003_early_failure_result(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
            )
        identity_chain_valid = _recovery_epoch003_identity_chain_valid(
            state,
            event=event,
            observation=observation,
        )
        expected = _recovery_epoch003_expected_projection(event)
        owner = _recovery_epoch003_observed_projection(observation)
        independent = _recovery_epoch003_observed_projection(observation)
        recorded_owner = state.get("owner_operational_projection")
        owner_shape_valid = bool(
            set(expected) == RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS
            and type(owner) is dict
            and set(owner) == RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS
            and type(recorded_owner) is dict
            and set(recorded_owner)
            == RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS
            and recorded_owner == owner
        )
        owner_hash = artifact_sha256(owner)
        independently_derived_hash = artifact_sha256(independent)
        declared_independent_hash = observation.get(
            "independent_operational_projection_sha256"
        )
        detected_failure: str | None = None
        if (
            not identity_chain_valid
            or not owner_shape_valid
            or state.get("expected_operational_projection") != expected
            or expected != owner
            or observation.get("owner_operational_projection_sha256")
            != owner_hash
        ):
            detected_failure = "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
        elif not _recovery_epoch003_sha256(declared_independent_hash):
            detected_failure = "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
        elif declared_independent_hash != independently_derived_hash:
            detected_failure = (
                "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
            )
        elif state[
            "operational_runtime_observation_external_identity"
        ].get("artifact_role") != (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
        ):
            detected_failure = "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"

        readiness = state.get("readiness_candidate")
        failure = state.get("failure_candidate")
        if readiness is None and failure is None:
            return ()
        if detected_failure is not None:
            if type(failure) is not dict:
                return (detected_failure,)
            receipt_independent_hash = (
                owner_hash
                if detected_failure
                == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
                else declared_independent_hash
            )
            if (
                readiness is not None
                or not isinstance(receipt_independent_hash, str)
                or not _recovery_epoch003_failure_receipt_valid(
                    failure,
                    state=state,
                    failure_class=detected_failure,
                    observation_hash=observation.get(
                        "operational_runtime_observation_sha256"
                    ),
                    expected_hash=artifact_sha256(expected),
                    owner_hash=owner_hash,
                    independent_hash=receipt_independent_hash,
                )
            ):
                return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
            return (detected_failure,)
        if failure is not None:
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        if not _recovery_epoch003_readiness_valid(
            state,
            expected_hash=artifact_sha256(expected),
            observed_hash=owner_hash,
        ):
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)


def verify_recovery_epoch003_bootstrap_source_runtime_contract(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Verify the historical frozen profile and current Epoch003 profile."""

    return _verify_recovery_epoch003_bootstrap_source_runtime_contract_impl(
        state,
        require_current_profile=False,
    )


def _verify_recovery_epoch003_bootstrap_source_runtime_contract_current(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Verify only the non-fixture current Epoch003 operational profile."""

    return _verify_recovery_epoch003_bootstrap_source_runtime_contract_impl(
        state,
        require_current_profile=True,
    )


def verify_recovery_epoch003_bootstrap_source_runtime_contract_current(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed while verifying only the current Epoch003 profile."""

    try:
        return (
            _verify_recovery_epoch003_bootstrap_source_runtime_contract_current(
                state
            )
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)


_RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_PRESTART_PREDECESSOR_"
    "CANONICAL_BYTES_REMEDIATED_FINAL_PRE_EVENT1_REFERENCE_RUNTIME_"
    "OBSERVATION_AND_OPERATIONAL_ADMISSION_V2_ISSUANCE_ONLY"
)
_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v2"
)
_RECOVERY_EPOCH003_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_RECOVERY_EPOCH003_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _recovery_epoch003_independent_v2_git_raw(
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


class _RecoveryEpoch003IndependentHistoricalByteFormError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _recovery_epoch003_independent_v2_derivation_result(
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


def _recovery_epoch003_independent_v2_repository_root(
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
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "REPOSITORY_OR_BASE_DRIFT"
        )
    return root


def _recovery_epoch003_independent_v2_strict_historical_json(
    raw: bytes,
) -> dict[str, Any]:
    invalid = "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_STRICT_JSON_INVALID"
    if (
        raw.startswith(b"\xef\xbb\xbf")
        or b"\r" in raw
        or not raw.endswith(b"\n")
        or raw.endswith(b"\n\n")
    ):
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(invalid)
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
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(invalid)


def _recovery_epoch003_independent_v2_historical_git_bytes(
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
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(topology)
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
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(topology)
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
        publication_raw = _recovery_epoch003_independent_v2_git_raw(
            root,
            publication_commit_sha1,
            path,
        )
        anchor_raw = _recovery_epoch003_independent_v2_git_raw(
            root,
            _RECOVERY_EPOCH003_HISTORICAL_ANCHOR_COMMIT,
            path,
        )
        head_raw = _recovery_epoch003_independent_v2_git_raw(
            root,
            validation_head,
            path,
        )
    except _RecoveryEpoch003IndependentHistoricalByteFormError:
        raise
    except (OSError, subprocess.SubprocessError, UnicodeError):
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(topology)
    if (
        publication_blob != git_blob_sha1
        or anchor_blob != git_blob_sha1
        or head_blob != git_blob_sha1
        or publication_raw != anchor_raw
        or publication_raw != head_raw
        or hashlib.sha256(publication_raw).hexdigest() != raw_sha256
    ):
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(identity)
    return publication_raw


def _recovery_epoch003_independent_v2_historical_row(
    root: Path,
    *,
    validation_head: str,
    binding_path: str,
    container_identity_kind: str,
    container_identity_sha256: str,
    identity: Mapping[str, Any],
    logical_identity_key: str,
) -> dict[str, Any]:
    raw = _recovery_epoch003_independent_v2_historical_git_bytes(
        root,
        validation_head=validation_head,
        path=identity["path"],
        publication_commit_sha1=identity["publication_commit_sha1"],
        git_blob_sha1=identity["git_blob_sha1"],
        raw_sha256=identity["raw_sha256"],
    )
    body = _recovery_epoch003_independent_v2_strict_historical_json(raw)
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
        or logical != _hash_without(
            body,
            "receipt_sha256",
        )
    ):
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_LOGICAL_HASH_MISMATCH"
        )
    try:
        load_canonical_json_bytes(raw)
    except ValueError as exc:
        if str(exc) != "CANONICAL_BYTES_MISMATCH":
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "CANONICAL_DISPOSITION_MISMATCH"
            )
    except (json.JSONDecodeError, UnicodeError):
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "CANONICAL_DISPOSITION_MISMATCH"
        )
    else:
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "CANONICAL_DISPOSITION_MISMATCH"
        )
    try:
        projection = canonical_json_bytes(body) + b"\n"
    except (TypeError, UnicodeError, ValueError):
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_PROJECTION_MISMATCH"
        )
    if projection == raw:
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
        raise _RecoveryEpoch003IndependentHistoricalByteFormError(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_PROJECTION_MISMATCH"
        )
    row["row_sha256"] = _hash_without(
        row,
        "row_sha256",
    )
    return row


def _recovery_epoch003_independent_v2_derive_historical_byte_form(
    state: Mapping[str, Any],
    *,
    phase: str,
) -> dict[str, Any]:
    owner = "INDEPENDENT_VERIFIER"
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
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID"
            )
        artifact_root = _recovery_epoch003_independent_v2_repository_root(
            state.get("artifact_repository_root"),
            repository_name="Cocolon",
            expected_head=state.get(
                "expected_artifact_head_commit_sha1"
            ),
            expected_tree=state.get(
                "expected_artifact_head_tree_sha1"
            ),
        )
        source_root = _recovery_epoch003_independent_v2_repository_root(
            state.get("source_repository_root"),
            repository_name="mashos-api",
            expected_head=state.get("expected_source_head_commit_sha1"),
            expected_tree=state.get("expected_source_head_tree_sha1"),
        )
        if artifact_root == source_root:
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
                != _hash_without(
                    seed,
                    "historical_predecessor_seed_sha256",
                )
            ):
                raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
                != _hash_without(
                    predecessors,
                    "predecessor_bindings_sha256",
                )
            ):
                raise _RecoveryEpoch003IndependentHistoricalByteFormError(
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
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "BINDING_SET_INVALID"
            )
        if not _recovery_epoch003_p0_valid(p0):
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_SEED_INVALID"
            )
        for key, identity in direct.items():
            role, schema, path, _fixed_identity = (
                _RECOVERY_EPOCH003_PREDECESSOR_IDENTITY_CONTRACTS[key]
            )
            if (
                not _recovery_epoch003_generic_identity_valid(
                    identity
                )
                or identity.get("artifact_role") != role
                or identity.get("schema_version") != schema
                or identity.get("path") != path
            ):
                raise _RecoveryEpoch003IndependentHistoricalByteFormError(
                    "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                    "HISTORICAL_FALLBACK_FORBIDDEN"
                )

        _recovery_epoch003_independent_v2_historical_git_bytes(
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
            _recovery_epoch003_independent_v2_historical_row(
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
            raise _RecoveryEpoch003IndependentHistoricalByteFormError(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "BINDING_SET_INVALID"
            )
        historical_binding_core_sha256 = artifact_sha256(rows)
        _recovery_epoch003_independent_v2_repository_root(
            str(artifact_root),
            repository_name="Cocolon",
            expected_head=state[
                "expected_artifact_head_commit_sha1"
            ],
            expected_tree=state["expected_artifact_head_tree_sha1"],
        )
        _recovery_epoch003_independent_v2_repository_root(
            str(source_root),
            repository_name="mashos-api",
            expected_head=state["expected_source_head_commit_sha1"],
            expected_tree=state["expected_source_head_tree_sha1"],
        )
        return _recovery_epoch003_independent_v2_derivation_result(
            owner=owner,
            phase=phase,
            input_binding_sha256=input_binding,
            historical_binding_core_sha256=(
                historical_binding_core_sha256
            ),
            failure_code=None,
        )
    except _RecoveryEpoch003IndependentHistoricalByteFormError as exc:
        return _recovery_epoch003_independent_v2_derivation_result(
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
        return _recovery_epoch003_independent_v2_derivation_result(
            owner=owner,
            phase=phase,
            input_binding_sha256=input_binding,
            historical_binding_core_sha256=None,
            failure_code=(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID"
            ),
        )


def verify_recovery_epoch003_prestart_historical_receipt_byte_form_eligibility_v1(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Independently derive actual-Git historical exact6 without effects."""

    return _recovery_epoch003_independent_v2_derive_historical_byte_form(
        state,
        phase="PRESTART",
    )


def _recovery_epoch003_independent_v2_historical_seed_from_predecessors(
    predecessors: Mapping[str, Any],
) -> dict[str, Any]:
    """Independently project typed historical exact6 from exact8."""

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
    seed["historical_predecessor_seed_sha256"] = _hash_without(
        seed,
        "historical_predecessor_seed_sha256",
    )
    return seed


def _recovery_epoch003_independent_v2_cross_lane_issues(
    prestart: Mapping[str, Any],
    post_reference: Mapping[str, Any],
) -> tuple[str, ...]:
    """Require both independent lanes to derive one actual-byte core."""

    if (
        prestart.get("state") != "VALID"
        or prestart.get("derivation_owner") != "INDEPENDENT_VERIFIER"
        or prestart.get("derivation_phase") != "PRESTART"
        or post_reference.get("state") != "VALID"
        or post_reference.get("derivation_owner")
        != "INDEPENDENT_VERIFIER"
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


def _recovery_epoch003_reference_body_valid_v2(
    value: Any,
    *,
    strict_frozen: bool = False,
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_REFERENCE_KEYS
        or value.get("schema_version") != _RECOVERY_EPOCH003_REFERENCE_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or value.get("authority_token")
        != _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
        or not _recovery_epoch003_sha1(value.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(value.get("source_tree_sha1"))
        or value.get("reservation_count_delta") != 0
        or value.get("formal_exact134_invocation_count") != 0
        or value.get("collection_state") != "NOT_STARTED"
        or value.get("test_execution_state") != "NOT_STARTED"
        or value.get("body_free") is not True
        or value.get("reference_runtime_observation_sha256")
        != _hash_without(
            value,
            "reference_runtime_observation_sha256",
        )
    ):
        return False
    lock = value.get("dependency_lock_identity")
    installed = value.get("installed_distributions")
    environment = value.get("environment_policy")
    structurally_valid = bool(
        type(lock) is dict
        and set(lock) == _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        and lock.get("identity_class") == "EXACT_HASH_LOCK"
        and isinstance(lock.get("path"), str)
        and bool(lock.get("path"))
        and _recovery_epoch003_sha256(lock.get("raw_sha256"))
        and _recovery_epoch003_sha256(
            value.get("wheel_bundle_manifest_sha256")
        )
        and type(installed) is list
        and bool(installed)
        and all(
            _recovery_epoch003_distribution_valid(row)
            for row in installed
        )
        and [row["normalized_distribution_name"] for row in installed]
        == sorted(
            {
                row["normalized_distribution_name"]
                for row in installed
            }
        )
        and value.get("installed_distributions_sha256")
        == artifact_sha256(installed)
        and _recovery_epoch003_distribution_valid(
            value.get("pytest_distribution_identity")
        )
        and value.get("pytest_distribution_identity") in installed
        and value["pytest_distribution_identity"].get(
            "normalized_distribution_name"
        )
        == "pytest"
        and _recovery_epoch003_runtime_identity_valid(
            value.get("python_runtime_identity")
        )
        and _recovery_epoch003_environment_valid(environment)
        and value.get("environment_policy_sha256")
        == artifact_sha256(environment)
        and _recovery_epoch003_materialization_valid(
            value.get("runtime_materialization"),
            dependency_lock_raw_sha256=lock["raw_sha256"],
            wheel_bundle_manifest_sha256=value[
                "wheel_bundle_manifest_sha256"
            ],
            distribution_count=len(installed),
        )
    )
    if not structurally_valid:
        return False
    if not strict_frozen:
        return True
    runtime = value["python_runtime_identity"]
    materialization = value["runtime_materialization"]
    return bool(
        lock
        == {
            "identity_class": "EXACT_HASH_LOCK",
            "path": _RECOVERY_EPOCH003_LOCK_PATH,
            "raw_sha256": _RECOVERY_EPOCH003_LOCK_RAW_SHA256,
        }
        and len(installed) == 46
        and value.get("wheel_bundle_manifest_sha256")
        == _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        and value.get("installed_distributions_sha256")
        == _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
        and runtime.get("implementation") == "CPYTHON"
        and runtime.get("version") == "3.12.13"
        and materialization.get("runtime_materialization_state")
        == "VERIFIED_LOCKED_REFERENCE_RUNTIME"
        and materialization.get("dependency_lock_raw_sha256")
        == _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        and materialization.get("wheel_bundle_manifest_sha256")
        == _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        and materialization.get("distribution_count") == 46
    )

def _recovery_epoch003_materialization_state_valid_v2(
    request: Any,
    result: Any,
    reference: Mapping[str, Any],
) -> bool:
    if (
        type(request) is not dict
        or set(request) != _RECOVERY_EPOCH003_MATERIALIZATION_REQUEST_KEYS
        or type(result) is not dict
        or set(result) != _RECOVERY_EPOCH003_MATERIALIZATION_RESULT_KEYS
        or request.get("authority_token")
        != _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
        or request.get("expected_source_commit_sha1")
        != reference.get("source_commit_sha1")
        or request.get("expected_source_tree_sha1")
        != reference.get("source_tree_sha1")
        or result.get("runtime_materialization")
        != reference.get("runtime_materialization")
    ):
        return False
    path_keys = (
        "artifact_repository_root",
        "source_repository_root",
        "dependency_lock_path",
        "wheelhouse_path",
        "destination_root",
    )
    if any(
        not isinstance(request.get(key), str) or not request.get(key)
        for key in path_keys
    ) or any(
        not isinstance(result.get(key), str) or not result.get(key)
        for key in ("runtime_root", "wheel_snapshot_root")
    ):
        return False
    raw_paths = {
        "artifact": Path(request["artifact_repository_root"]).absolute(),
        "source": Path(request["source_repository_root"]).absolute(),
        "lock": Path(request["dependency_lock_path"]).absolute(),
        "wheelhouse": Path(request["wheelhouse_path"]).absolute(),
        "destination": Path(request["destination_root"]).absolute(),
        "runtime": Path(result["runtime_root"]).absolute(),
        "snapshot": Path(result["wheel_snapshot_root"]).absolute(),
    }
    if any(
        _recovery_epoch003_path_has_symlink_component(path)
        for path in raw_paths.values()
    ):
        return False
    paths = {key: path.resolve() for key, path in raw_paths.items()}
    policy = _recovery_epoch003_environment_policy(
        request.get("environment")
    )
    if (
        policy is None
        or result.get("effective_environment_policy") != policy
        or reference.get("environment_policy") != policy
        or reference.get("environment_policy_sha256")
        != artifact_sha256(policy)
        or paths["destination"] != paths["runtime"]
        or paths["lock"]
        != (paths["source"] / _RECOVERY_EPOCH003_LOCK_PATH).resolve()
        or any(
            not _recovery_epoch003_paths_disjoint(
                paths[left],
                paths[right],
            )
            for left, right in (
                ("runtime", "snapshot"),
                ("runtime", "artifact"),
                ("runtime", "source"),
                ("runtime", "wheelhouse"),
                ("snapshot", "artifact"),
                ("snapshot", "source"),
                ("snapshot", "wheelhouse"),
                ("artifact", "source"),
            )
        )
        or not _recovery_epoch003_expected_repository(
            paths["artifact"],
            "Cocolon",
        )
        or not _recovery_epoch003_expected_repository(
            paths["source"],
            "mashos-api",
        )
    ):
        return False
    loaded = _recovery_epoch003_strict_json_file(paths["lock"])
    if loaded is None:
        return False
    lock, raw = loaded
    try:
        commit = _recovery_epoch003_git(
            paths["source"],
            "rev-parse",
            "HEAD",
        )
        tree = _recovery_epoch003_git(
            paths["source"],
            "rev-parse",
            "HEAD^{tree}",
        )
        clean = (
            _recovery_epoch003_git(
                paths["source"],
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        )
        rows = lock["distributions"]
        installed = [
            {
                key: row[key]
                for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
            }
            for row in rows
        ]
        installed.sort(
            key=lambda row: row["normalized_distribution_name"]
        )
        wheel_manifest = [
            {
                "wheel_filename": row["wheel_filename"],
                "wheel_sha256": row["wheel_sha256"],
                "wheel_record_sha256": row["wheel_record_sha256"],
            }
            for row in rows
        ]
    except (KeyError, TypeError):
        return False
    if (
        not clean
        or commit != request.get("expected_source_commit_sha1")
        or tree != request.get("expected_source_tree_sha1")
        or hashlib.sha256(raw).hexdigest()
        != _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        or lock.get("lock_sha256")
        != _RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256
        or lock.get("lock_sha256")
        != _hash_without(lock, "lock_sha256")
        or lock.get("distribution_count") != 46
        or type(rows) is not list
        or len(rows) != 46
        or lock.get("target", {}).get("implementation") != "CPYTHON"
        or lock.get("target", {}).get("python_version") != "3.12.13"
        or lock.get("target", {}).get("platform") != "linux-x86_64"
        or lock.get("target", {}).get("machine") != "x86_64"
        or lock.get("resolution", {}).get("pip_version") != "26.0.1"
        or artifact_sha256(wheel_manifest)
        != _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        or artifact_sha256(installed)
        != _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
        or reference.get("installed_distributions") != installed
        or not _recovery_epoch003_wheel_directory_valid(
            paths["wheelhouse"],
            lock,
            immutable=False,
        )
        or not _recovery_epoch003_wheel_directory_valid(
            paths["snapshot"],
            lock,
            immutable=True,
        )
    ):
        return False
    materialization = result.get("runtime_materialization")
    if (
        not _recovery_epoch003_materialization_valid(
            materialization,
            dependency_lock_raw_sha256=(
                _RECOVERY_EPOCH003_LOCK_RAW_SHA256
            ),
            wheel_bundle_manifest_sha256=(
                _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
            ),
            distribution_count=46,
        )
        or materialization.get("runtime_materialization_state")
        != "VERIFIED_LOCKED_REFERENCE_RUNTIME"
    ):
        return False
    python_relative = PurePosixPath(
        materialization["python_executable_relative_path"]
    )
    installed_relative = PurePosixPath(
        materialization["installed_directory_relative_path"]
    )
    if (
        python_relative.is_absolute()
        or installed_relative.is_absolute()
        or ".." in python_relative.parts
        or ".." in installed_relative.parts
    ):
        return False
    python_executable = paths["runtime"] / Path(*python_relative.parts)
    installed_directory = paths["runtime"] / Path(
        *installed_relative.parts
    )
    installed_closure = _recovery_epoch003_installed_closure(
        installed_directory,
        paths["runtime"],
    )
    if (
        installed_closure is None
        or set(installed_closure)
        != {
            row["normalized_distribution_name"] for row in installed
        }
        or any(
            installed_closure[row["normalized_distribution_name"]]
            != (
                row["distribution_version"],
                row["installed_record_closure_sha256"],
            )
            for row in installed
        )
    ):
        return False
    environment = _recovery_epoch003_sanitized_environment(
        request["environment"]
    )
    probed = _recovery_epoch003_runtime_probe(
        python_executable,
        environment,
        sorted(row["wheel_filename"] for row in rows),
    )
    if probed is None:
        return False
    runtime_identity, target = probed
    pytest_identity = next(
        (
            row
            for row in installed
            if row["normalized_distribution_name"] == "pytest"
        ),
        None,
    )
    if pytest_identity is None:
        return False
    try:
        installer_pip = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "pip",
                "--version",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.split()
        pytest_version = subprocess.run(
            [
                str(python_executable),
                "-I",
                "-B",
                "-c",
                (
                    "import importlib.metadata as m;"
                    "print(m.version('pytest'))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return False
    root_identity = _recovery_epoch003_root_identity(
        paths["runtime"],
        request=request,
        lock=lock,
        installed=installed,
        runtime_identity=runtime_identity,
        pytest_identity=pytest_identity,
        policy=policy,
    )
    return bool(
        runtime_identity == reference.get("python_runtime_identity")
        and _recovery_epoch003_wheel_target_tags_valid(lock, target)
        and runtime_identity.get("implementation") == "CPYTHON"
        and runtime_identity.get("version") == "3.12.13"
        and target.get("system") == "Linux"
        and target.get("machine") == "x86_64"
        and target.get("abi_flags")
        == lock["target"].get("abi_flags")
        and target.get("byte_order")
        == lock["target"].get("byte_order")
        and target.get("python_cache_tag")
        == lock["target"].get("python_cache_tag")
        and target.get("sys_platform") == "linux"
        and len(installer_pip) >= 2
        and installer_pip[1] == "26.0.1"
        and pytest_version == pytest_identity["distribution_version"]
        and reference.get("pytest_distribution_identity")
        == pytest_identity
        and root_identity
        == materialization.get("runtime_root_identity_sha256")
    )

def verify_recovery_epoch003_reference_runtime_observation_v2(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Independently verify the v2-bound reference runtime and receipt."""

    failure = (
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION_VERIFICATION_INVALID",
    )
    try:
        required = _keys(
            """
            verification_mode materialization_request
            materialization_result reference_runtime_observation
            reference_runtime_observation_external_identity
            reference_publication_state
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        mode = state.get("verification_mode")
        if mode not in {
            "STRICT_REFERENCE_BODY_BEFORE_PUBLICATION",
            "STRICT_REFERENCE_BODY_AND_POSTFETCH",
        }:
            return failure
        reference = state.get("reference_runtime_observation")
        if (
            not _recovery_epoch003_reference_body_valid_v2(
                reference,
                strict_frozen=True,
            )
            or not _recovery_epoch003_materialization_state_valid_v2(
                state.get("materialization_request"),
                state.get("materialization_result"),
                reference,
            )
        ):
            return failure
        identity = state.get(
            "reference_runtime_observation_external_identity"
        )
        publication = state.get("reference_publication_state")
        if mode == "STRICT_REFERENCE_BODY_BEFORE_PUBLICATION":
            return () if identity is None and publication is None else failure
        if (
            not _recovery_epoch003_external_identity_valid(
                identity,
                roles=frozenset(
                    {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
                ),
                schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
                path=_RECOVERY_EPOCH003_REFERENCE_PATH,
                logical_hash=reference[
                    "reference_runtime_observation_sha256"
                ],
            )
            or not _recovery_epoch003_reference_publication_shape_valid(
                publication,
                reference=reference,
                reference_identity=identity,
            )
            or not _recovery_epoch003_reference_publication_actual_valid(
                publication,
                reference=reference,
                reference_identity=identity,
            )
        ):
            return failure
        return ()
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


_RECOVERY_EPOCH003_V2_EVENT1_AUTHORITY = None
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


def _recovery_epoch003_admission_body_valid_v2(
    admission: Any,
    *,
    reference: Mapping[str, Any],
) -> bool:
    if (
        type(admission) is not dict
        or set(admission) != _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS
        or admission.get("schema_version")
        != _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_SCHEMA
        or admission.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or admission.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or admission.get("owner_validation_state") != "PROVED"
        or admission.get("independent_verification_state") != "PROVED"
        or admission.get("state")
        != (
            "SOURCE_BOOTSTRAP_REFERENCE_RUNTIME_CLOSED_AWAITING_"
            "SEPARATE_V2_EVENT1_CONNECTION_DESIGN_AND_AUTHORITY"
        )
        or admission.get("automatic_progression") is not False
        or admission.get("body_free") is not True
        or admission.get("operational_admission_sha256")
        != _hash_without(admission, "operational_admission_sha256")
        or not _recovery_epoch003_admission_predecessors_valid(
            admission.get("predecessor_bindings")
        )
    ):
        return False
    source = admission.get("source_closure")
    bootstrap = admission.get("bootstrap_closure")
    if (
        not _recovery_epoch003_bootstrap_contract_valid(bootstrap)
        or not _recovery_epoch003_source_contract_valid(source, bootstrap)
        or not _recovery_epoch003_reference_body_valid_v2(reference)
    ):
        return False
    predecessors = admission["predecessor_bindings"]
    reference_identity = predecessors[
        "reference_runtime_observation_external_identity"
    ]
    if (
        bootstrap.get(
            "reference_runtime_observation_external_identity"
        )
        != reference_identity
        or source.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or reference_identity.get("logical_artifact_sha256")
        != reference.get("reference_runtime_observation_sha256")
        or reference.get("source_commit_sha1")
        != source.get("source_commit_sha1")
        or reference.get("source_tree_sha1")
        != source.get("source_tree_sha1")
    ):
        return False
    authority = admission.get("authority")
    scope = admission.get("scope")
    freshness = admission.get("freshness")
    effect = admission.get("effect_boundary")
    if (
        type(authority) is not dict
        or set(authority) != _RECOVERY_EPOCH003_ADMISSION_AUTHORITY_KEYS
        or authority.get("approval_kind") != "EXPLICIT_SEPARATE_APPROVAL"
        or authority.get("admission_authority_token")
        != _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
        or authority.get("publication_authority_token")
        != _RECOVERY_EPOCH003_V2_FINAL_ISSUANCE_AUTHORITY
        or authority.get("authority_sha256")
        != _hash_without(authority, "authority_sha256")
        or type(scope) is not dict
        or set(scope) != _RECOVERY_EPOCH003_ADMISSION_SCOPE_KEYS
        or scope.get("artifact_repository_full_name")
        != "MassyuRed/Cocolon"
        or scope.get("source_repository_full_name")
        != "MassyuRed/mashos-api"
        or scope.get("source_ref") != "refs/heads/main"
        or scope.get("source_commit_sha1")
        != source.get("source_commit_sha1")
        or scope.get("source_tree_sha1") != source.get("source_tree_sha1")
        or scope.get("source_closure_sha256")
        != source.get("source_closure_sha256")
        or scope.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or scope.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or scope.get("next_authority_token")
        != _RECOVERY_EPOCH003_V2_EVENT1_AUTHORITY
        or scope.get("operation_set")
        != list(_RECOVERY_EPOCH003_V2_OPERATION_SET)
        or scope.get("separate_explicit_authority_required") is not True
        or scope.get("scope_sha256") != _hash_without(scope, "scope_sha256")
    ):
        return False
    if (
        type(freshness) is not dict
        or set(freshness) != _RECOVERY_EPOCH003_FRESHNESS_KEYS
        or _RECOVERY_EPOCH003_UTC_RE.fullmatch(
            str(freshness.get("issued_at_utc", ""))
        )
        is None
        or freshness.get("expires_at_utc") is not None
        or freshness.get("validity_mode")
        != "IDENTITY_STABLE_SINGLE_FUTURE_EVENT1_CAPABILITY"
        or freshness.get("bound_source_commit_sha1")
        != source.get("source_commit_sha1")
        or freshness.get("bound_source_tree_sha1")
        != source.get("source_tree_sha1")
        or freshness.get(
            "bound_reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or freshness.get("event1_path_state_at_issuance") != "ABSENT"
        or freshness.get("maximum_event1_consumption_count") != 1
        or freshness.get("invalidation_conditions")
        != list(_RECOVERY_EPOCH003_V2_INVALIDATION_CONDITIONS)
        or freshness.get("reuse_allowed") is not False
        or freshness.get("freshness_sha256")
        != _hash_without(freshness, "freshness_sha256")
    ):
        return False
    expected_effect = {
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
    }
    return bool(
        type(effect) is dict
        and set(effect) == _RECOVERY_EPOCH003_EFFECT_KEYS
        and all(effect.get(key) == value for key, value in expected_effect.items())
        and effect.get("effect_boundary_sha256")
        == _hash_without(effect, "effect_boundary_sha256")
    )

def _recovery_epoch003_actual_source_bootstrap_valid_v2(
    observation: Mapping[str, Any],
    admission: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> bool:
    root = Path(observation["source_repository_root"]).resolve()
    source = admission["source_closure"]
    bootstrap = admission["bootstrap_closure"]
    if (
        not _recovery_epoch003_expected_repository(root, "mashos-api")
        or not _recovery_epoch003_source_observation_actual_valid(
            observation
        )
        or not _recovery_epoch003_reference_body_valid_v2(
            reference,
            strict_frozen=True,
        )
        or reference.get("source_commit_sha1")
        != source.get("source_commit_sha1")
        or reference.get("source_tree_sha1")
        != source.get("source_tree_sha1")
    ):
        return False
    owners = bootstrap["formal_owner_artifacts"]
    tests = bootstrap["formal_test_manifest"]
    for row in owners:
        actual = _recovery_epoch003_git_file_identity(
            root,
            row["path"],
        )
        if actual is None or {
            key: row[key] for key in actual
        } != actual:
            return False
    for row in tests:
        actual = _recovery_epoch003_git_file_identity(
            root,
            row["path"],
        )
        if actual != row:
            return False
    test_paths = {row["path"] for row in tests}
    for node_id in bootstrap["formal_test_node_ids"]:
        try:
            path, function_name = node_id.split("::", 1)
            raw = subprocess.run(
                ["git", "show", f"HEAD:{path}"],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=20,
            ).stdout
            tree = ast.parse(raw.decode("utf-8"))
        except (
            OSError,
            UnicodeError,
            ValueError,
            SyntaxError,
            subprocess.SubprocessError,
        ):
            return False
        if (
            path not in test_paths
            or not function_name.startswith("test_")
            or function_name
            not in {
                node.name
                for node in tree.body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            }
        ):
            return False
    for row in bootstrap["import_manifest"]:
        owner_paths = row["owner_paths"]
        if (
            owner_paths != sorted(set(owner_paths))
            or any(
                _recovery_epoch003_git_file_identity(root, path) is None
                for path in owner_paths
            )
        ):
            return False
        if row["classification"] == "FIRST_PARTY":
            actual = _recovery_epoch003_git_file_identity(
                root,
                row["target_identity"]["path"],
            )
            if actual != row["target_identity"]:
                return False
    lock_raw = subprocess.run(
        ["git", "show", f"HEAD:{_RECOVERY_EPOCH003_LOCK_PATH}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout
    try:
        lock = json.loads(lock_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return False
    independently_derived_imports = (
        _recovery_epoch003_independent_import_manifest(
            root,
            lock=lock,
            runtime_identity=bootstrap[
                "expected_python_runtime_identity"
            ],
            seed_paths={
                *(row["path"] for row in owners),
                *(row["path"] for row in tests),
            },
        )
    )
    proof_owner = next(
        (
            row
            for row in owners
            if row["role"] == "current_step_proof_gate"
        ),
        None,
    )
    return bool(
        hashlib.sha256(lock_raw).hexdigest()
        == _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        and lock.get("lock_sha256")
        == _RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256
        and source.get("detailed_design_sha256")
        == _RECOVERY_EPOCH003_DETAILED_DESIGN_SHA256
        and source.get("epoch003_p0_external_identity_sha256")
        == _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
        and source.get("epoch002_predecessor_set_sha256")
        == _RECOVERY_EPOCH003_EPOCH002_PREDECESSOR_SET_SHA256
        and source.get("d1_red_receipt_external_identity_sha256")
        == _RECOVERY_EPOCH003_CORRECTED_D1_IDENTITY_SHA256
        and source.get("d2_green_receipt_external_identity_sha256")
        == _RECOVERY_EPOCH003_BOOTSTRAP_D2_IDENTITY_SHA256
        and source.get("source_dependency_closure_sha256")
        == artifact_sha256(bootstrap["import_manifest"])
        and independently_derived_imports == bootstrap["import_manifest"]
        and _recovery_epoch003_requirement_registry_actual_valid(
            root,
            source,
            bootstrap,
        )
        and source.get("canonical_current_closure_sha256")
        == artifact_sha256(owners)
        and source.get("requirement_registry_sha256")
        == _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_SHA256
        and source.get("formal_node_registry_sha256")
        == _RECOVERY_EPOCH003_FORMAL_NODE_REGISTRY_SHA256
        and proof_owner is not None
        and source.get("proof_source_closure_sha256")
        == artifact_sha256(proof_owner)
        and source.get("formal_test_manifest_sha256")
        == artifact_sha256(tests)
        and source.get("bootstrap_closure_sha256")
        == bootstrap.get("bootstrap_closure_sha256")
    )


def verify_recovery_epoch003_operational_admission_contract_v2(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Verify v2 by independently re-reading actual historical Git bytes."""

    failure = (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_VERIFICATION_INVALID",
    )
    try:
        required = _keys(
            """
            verification_mode artifact_repository_root
            source_repository_observation operational_admission
            operational_admission_external_identity
            reference_runtime_observation reference_publication_state
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        mode = state.get("verification_mode")
        if mode not in {
            "STRICT_PREPUBLICATION_ACTUAL",
            "STRICT_POSTFETCH_ACTUAL",
        }:
            return failure
        admission = state.get("operational_admission")
        reference = state.get("reference_runtime_observation")
        source_observation = state.get("source_repository_observation")
        reference_publication = state.get("reference_publication_state")
        if (
            not _recovery_epoch003_admission_body_valid_v2(
                admission,
                reference=reference,
            )
            or not _recovery_epoch003_source_observation_shape_valid(
                source_observation,
                source=admission["source_closure"],
            )
        ):
            return failure
        reference_identity = admission["predecessor_bindings"][
            "reference_runtime_observation_external_identity"
        ]
        if (
            not _recovery_epoch003_reference_publication_shape_valid(
                reference_publication,
                reference=reference,
                reference_identity=reference_identity,
            )
            or not isinstance(state.get("artifact_repository_root"), str)
            or not state.get("artifact_repository_root")
        ):
            return failure
        artifact_root = Path(
            state["artifact_repository_root"]
        ).resolve(strict=True)
        if (
            not _recovery_epoch003_expected_repository(
                artifact_root,
                "Cocolon",
            )
            or not _recovery_epoch003_source_observation_actual_valid(
                source_observation
            )
            or not _recovery_epoch003_reference_body_valid_v2(
                reference,
                strict_frozen=True,
            )
            or not _recovery_epoch003_reference_publication_actual_valid(
                reference_publication,
                reference=reference,
                reference_identity=reference_identity,
            )
            or not _recovery_epoch003_actual_source_bootstrap_valid_v2(
                source_observation,
                admission,
                reference,
            )
        ):
            return failure
        artifact_head = _recovery_epoch003_git(
            artifact_root,
            "rev-parse",
            "HEAD",
        )
        artifact_tree = _recovery_epoch003_git(
            artifact_root,
            "rev-parse",
            "HEAD^{tree}",
        )
        derivation = (
            _recovery_epoch003_independent_v2_derive_historical_byte_form(
                {
                    "artifact_repository_root": str(artifact_root),
                    "expected_artifact_head_commit_sha1": artifact_head,
                    "expected_artifact_head_tree_sha1": artifact_tree,
                    "predecessor_bindings": admission[
                        "predecessor_bindings"
                    ],
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
        )
        historical_binding_core_sha256 = derivation.get(
            "historical_binding_core_sha256"
        )
        if (
            derivation.get("state") != "VALID"
            or _RECOVERY_EPOCH003_SHA256_RE.fullmatch(
                str(historical_binding_core_sha256)
            )
            is None
        ):
            return failure
        prestart = (
            _recovery_epoch003_independent_v2_derive_historical_byte_form(
                {
                    "artifact_repository_root": str(artifact_root),
                    "expected_artifact_head_commit_sha1": artifact_head,
                    "expected_artifact_head_tree_sha1": artifact_tree,
                    "historical_predecessor_seed": (
                        _recovery_epoch003_independent_v2_historical_seed_from_predecessors(
                            admission["predecessor_bindings"]
                        )
                    ),
                    "source_repository_root": source_observation[
                        "source_repository_root"
                    ],
                    "expected_source_head_commit_sha1": (
                        source_observation["source_commit_sha1"]
                    ),
                    "expected_source_head_tree_sha1": (
                        source_observation["source_tree_sha1"]
                    ),
                    "automatic_progression": False,
                },
                phase="PRESTART",
            )
        )
        if _recovery_epoch003_independent_v2_cross_lane_issues(
            prestart,
            derivation,
        ):
            return failure
        admission_identity = state.get(
            "operational_admission_external_identity"
        )
        if mode == "STRICT_PREPUBLICATION_ACTUAL":
            admission_exists = (
                subprocess.run(
                    [
                        "git",
                        "cat-file",
                        "-e",
                        (
                            f"{artifact_head}:"
                            f"{_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH}"
                        ),
                    ],
                    cwd=artifact_root,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=20,
                ).returncode
                == 0
            )
            return (
                ()
                if (
                    admission_identity is None
                    and not admission_exists
                    and artifact_head
                    == reference_publication.get(
                        "admission_base_commit_sha1"
                    )
                    and artifact_tree
                    == reference_publication.get(
                        "admission_base_tree_sha1"
                    )
                )
                else failure
            )
        if (
            not _recovery_epoch003_external_identity_valid(
                admission_identity,
                roles=frozenset(
                    {"RECOVERY_EPOCH003_OPERATIONAL_ADMISSION"}
                ),
                schema=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_SCHEMA,
                path=_RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PATH,
                logical_hash=admission[
                    "operational_admission_sha256"
                ],
            )
            or not _recovery_epoch003_admission_publication_actual_valid(
                state,
                admission=admission,
                admission_identity=admission_identity,
                reference_identity=reference_identity,
            )
        ):
            return failure
        return ()
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


_RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004.sequence_event.v2"
)
_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004.operational_admission.v2"
)
_RECOVERY_EPOCH004_CANDIDATE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004.candidate_allocation.v1"
)
_RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "source_baseline_eligibility_closure.v1"
)
_RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "formal_worker_bootstrap_manifest.v1"
)
_RECOVERY_EPOCH004_REFERENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "reference_runtime_observation.v1"
)
_RECOVERY_EPOCH004_RUNTIME_MATERIALIZATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004.runtime_materialization.v1"
)
_RECOVERY_EPOCH004_LOGICAL_CYCLE_ID = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH004_RECOVERY_EPOCH_ID = (
    "NLS_V3_CYCLE001_RECOVERY_EPOCH_004"
)
_RECOVERY_EPOCH004_D1_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH004_ADDITIVE_CORRECTIVE_P0_"
    "POSTVERIFIED_D1_OPERATIONAL_ADMISSION_V2_EVENT1_CONNECTION_OWNER_"
    "INDEPENDENT_SCHEMA_DISPATCH_ACTUAL_GIT_SOURCE_SUBJECT_OWNER_"
    "EXECUTOR_INDEPENDENT_EXECUTOR_IDENTITY_PARENT_PHASE3_EVIDENCE_AND_"
    "V1_EXACT16_EXACT8_INVARIANCE_CAUSAL_RED_FREEZE_ONLY"
)
_RECOVERY_EPOCH004_D1_AUTHORITY_STATE = (
    "DEFINED_INACTIVE_SEPARATE_MASH_APPROVAL_REQUIRED"
)
_RECOVERY_EPOCH004_NON_CREDIT_MARKER = (
    "MEMORY_ONLY_NON_CREDIT_CONTRACT_FIXTURE_NO_PUBLICATION_NO_EFFECT"
)
_RECOVERY_EPOCH004_ACTUAL_GIT_PROFILE = (
    "ACTUAL_GIT_POSTFETCH_VERIFIED_CREDIT_ELIGIBLE"
)
_RECOVERY_EPOCH004_REFERENCE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch004_PreEvent1_"
    "ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch004_"
    "OperationalAdmissionV2_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH004_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch004_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event.json"
)
_RECOVERY_EPOCH004_ENTRY_COMMIT_SHA1 = (
    "97e8dd4d7021b8a1781d534aaa603f71dffa41b9"
)
_RECOVERY_EPOCH004_OWNER_MODULE_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
)
_RECOVERY_EPOCH004_INDEPENDENT_MODULE_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
)

RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS = _RECOVERY_EPOCH003_EVENT_KEYS
_RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS = (
    _RECOVERY_EPOCH003_EVENT_CANDIDATE_KEYS
)
_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_KEYS = (
    _RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS
)
_RECOVERY_EPOCH004_PREDECESSOR_KEYS = _keys(
    """
    p0_external_identity epoch003_immutable_predecessor_set_sha256
    epoch003_reconciliation_receipt_external_identity
    d1_event1_connection_receipt_external_identity
    d2_event1_connection_receipt_external_identity
    reference_runtime_observation_external_identity
    final_source_identity_contract_sha256 predecessor_bindings_sha256
    """
)
_RECOVERY_EPOCH004_SOURCE_SUBJECT_KEYS = _keys(
    """
    repository_full_name source_ref repository_root head_commit_sha1
    head_tree_sha1 origin_main_commit_sha1 worktree_clean
    """
)
_RECOVERY_EPOCH004_EXECUTOR_KEYS = (
    _RECOVERY_EPOCH004_SOURCE_SUBJECT_KEYS
    | _keys("module_path module_origin git_blob_sha1 raw_sha256")
)
RECOVERY_EPOCH004_EVENT1_CONNECTION_STATE_KEYS = _keys(
    """
    verification_profile credit_eligible approved_authority_token
    authority_state logical_cycle_id recovery_epoch_id p0_external_identity
    historical_candidate_version_ids reference_runtime_observation
    reference_runtime_observation_external_identity operational_admission
    operational_admission_external_identity event1 event1_consumption_count
    source_subject owner_executor independent_executor source_baseline_state
    later_effect_counts automatic_progression
    """
)
_RECOVERY_EPOCH004_LATER_EFFECT_KEYS = _keys(
    """
    artifact_publication_count candidate_publication_count
    event1_publication_count runtime_materialization_count
    readiness_creation_count failure_creation_count
    reservation_creation_count attempt_creation_count
    formal_exact134_invocation_count source_baseline_lock_count
    """
)
_RECOVERY_EPOCH004_EXTERNAL_IDENTITY_KEYS = (
    _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
)
_RECOVERY_EPOCH004_SOURCE_KEYS = _keys(
    """
    schema_version repository_full_name source_ref source_commit_sha1
    source_tree_sha1 worktree_clean detailed_design_sha256
    epoch004_p0_external_identity_sha256
    epoch003_immutable_predecessor_set_sha256
    d1_red_receipt_external_identity_sha256
    d2_green_receipt_external_identity_sha256
    source_dependency_closure_sha256 canonical_current_closure_sha256
    requirement_registry_sha256 formal_node_registry_sha256
    proof_source_closure_sha256 formal_test_manifest_sha256
    bootstrap_closure_sha256
    reference_runtime_observation_external_identity_sha256
    source_closure_sha256
    """
)
_RECOVERY_EPOCH004_BOOTSTRAP_KEYS = _RECOVERY_EPOCH003_BOOTSTRAP_KEYS
_RECOVERY_EPOCH004_REFERENCE_KEYS = _RECOVERY_EPOCH003_REFERENCE_KEYS
_RECOVERY_EPOCH004_EVENT_AUTHORITY_KEYS = (
    _RECOVERY_EPOCH003_EVENT_AUTHORITY_KEYS
)
_RECOVERY_EPOCH004_EVENT_PUBLICATION_KEYS = (
    _RECOVERY_EPOCH003_EVENT_PUBLICATION_KEYS
)
_RECOVERY_EPOCH004_ADMISSION_AUTHORITY_KEYS = (
    _RECOVERY_EPOCH003_ADMISSION_AUTHORITY_KEYS
)
_RECOVERY_EPOCH004_ADMISSION_SCOPE_KEYS = (
    _RECOVERY_EPOCH003_ADMISSION_SCOPE_KEYS
)
_RECOVERY_EPOCH004_FRESHNESS_KEYS = _RECOVERY_EPOCH003_FRESHNESS_KEYS
_RECOVERY_EPOCH004_EFFECT_KEYS = _keys(
    """
    reference_runtime_materialization_count_delta
    reference_runtime_observation_publication_count
    operational_admission_publication_count
    operational_runtime_materialization_count candidate_allocation_count
    sequence_event1_count readiness_artifact_count failure_artifact_count
    formal_reservation_count formal_attempt_count
    formal_exact134_invocation_count formal_test_collection_count
    test_execution_count pytest_main_call_count source_baseline_state
    effect_boundary_sha256
    """
)
_RECOVERY_EPOCH004_EFFECT_COUNT_KEYS = (
    _RECOVERY_EPOCH004_EFFECT_KEYS
    - {"source_baseline_state", "effect_boundary_sha256"}
)
_RECOVERY_EPOCH004_SOURCE_SHA256_KEYS = (
    "detailed_design_sha256",
    "epoch004_p0_external_identity_sha256",
    "epoch003_immutable_predecessor_set_sha256",
    "d1_red_receipt_external_identity_sha256",
    "d2_green_receipt_external_identity_sha256",
    "source_dependency_closure_sha256",
    "canonical_current_closure_sha256",
    "requirement_registry_sha256",
    "formal_node_registry_sha256",
    "proof_source_closure_sha256",
    "formal_test_manifest_sha256",
    "bootstrap_closure_sha256",
    "reference_runtime_observation_external_identity_sha256",
    "source_closure_sha256",
)
_RECOVERY_EPOCH004_HISTORICAL_CANDIDATE_VERSION_IDS = (
    "nls_v3_rc_0010",
    "nls_v3_rc_0027",
    "nls_v3_rc_0032",
    "nls_v3_rc_0034",
    "nls_v3_rc_epoch002_success_0001",
)
_RECOVERY_EPOCH004_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_RECOVERY_EPOCH004_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RECOVERY_EPOCH004_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)

_RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY = {
    "schema_version": (
        "cocolon.emlis.nls_v3.step11.cycle001.recovery_epoch004."
        "additive_corrective_p0_external_identity.v1"
    ),
    "logical_cycle_id": _RECOVERY_EPOCH004_LOGICAL_CYCLE_ID,
    "recovery_epoch_id": _RECOVERY_EPOCH004_RECOVERY_EPOCH_ID,
    "parent_design": {
        "path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch004_"
            "AdditiveCorrectiveP0_AfterEpoch003PrestartD2ReceiptIdentity"
            "PreimageContractMismatchAndPartialP0NonCredit_ParentDesign_"
            "ReadOnly_20260730.md"
        ),
        "publication_commit_sha1": (
            "501d49daa93a1d0856aaecca30ad3cfda668fad4"
        ),
        "git_blob_sha1": "e154e6556219be1d465ca06800cdc9655d69f89b",
        "raw_sha256": (
            "5a053db1fd0707571dc492c124d01eba1382ac3a49929723f94f0a20aee59268"
        ),
    },
    "receipt": {
        "path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch004_"
            "AdditiveCorrectiveP0_AfterEpoch003PrestartD2ReceiptIdentity"
            "PreimageContractMismatchAndPartialP0NonCredit_ParentDesign_"
            "ReadOnly_BodyFree_Receipt_20260730.json"
        ),
        "publication_commit_sha1": (
            "aaf94138088c8c67c2f8502c5da8e55bff783483"
        ),
        "git_blob_sha1": "4c04d66c45e461be9d3d3351c9cb4ba39d337963",
        "raw_sha256": (
            "ea8f2821285cde598252e35d5a2c88227069706502ec3a212a4c6a8f5d7c7e35"
        ),
        "logical_receipt_sha256": (
            "49d2ff073f75af360202685060f35c7bc01b2d0289e3c9856d7444d60b78eda4"
        ),
    },
    "p0_external_identity_sha256": (
        "aa602f6c7c39ea1ad0ece9ed6974c76b7dc8f3a4207540a290e3bb3eb06fe046"
    ),
}
_RECOVERY_EPOCH004_RECONCILIATION_EXTERNAL_IDENTITY = {
    "artifact_role": (
        "RECOVERY_EPOCH003_PRESTART_D2_IDENTITY_PREIMAGE_MISMATCH_"
        "DOWNSTREAM_CREDIT_PARTIAL_EPOCH004_P0_DISPOSITION_"
        "RECONCILIATION_RECEIPT"
    ),
    "body_free": True,
    "git_blob_sha1": "71798663e56d77e4b092dd5efd6d8999fb9fd81e",
    "identity_sha256": (
        "c9eb76e54e6d956e9f082f46fdaf71abe6068a33a379fcb3c4b6c3c267542649"
    ),
    "logical_artifact_sha256": (
        "b8a8789988b57961ccfc8edb84e8612ed38b5205153da651fc3886e4ca5ebf24"
    ),
    "path": (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
        "PrestartD2ReceiptIdentityPreimageContractMismatch_"
        "DownstreamActiveCreditAndPartialRecoveryEpoch004P0Publication"
        "Disposition_ContractReconciliation_Design_ReadOnly_BodyFree_"
        "Receipt_20260730.json"
    ),
    "publication_commit_sha1": (
        "ae3a90d50d2411cc548008c58a21b345ebfc9a29"
    ),
    "raw_sha256": (
        "8ee1149049dc3f37d974baf707fff784848c6105de0ab7557853bc09b327716a"
    ),
    "repository_full_name": "MassyuRed/Cocolon",
    "schema_version": (
        "cocolon.emlis.nls_v3.step11.cycle001.recovery_epoch003."
        "prestart_d2_receipt_identity_preimage_mismatch_downstream_credit_"
        "partial_epoch004_p0_disposition_reconciliation_receipt.v1"
    ),
}


def _recovery_epoch004_external_identity_valid(
    value: Any,
    *,
    role: str | None,
    schema: str | None,
    path: str | None,
    logical_hash: str | None,
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH004_EXTERNAL_IDENTITY_KEYS
        or (role is not None and value.get("artifact_role") != role)
        or (
            schema is not None
            and value.get("schema_version") != schema
        )
        or (path is not None and value.get("path") != path)
        or (
            logical_hash is not None
            and value.get("logical_artifact_sha256") != logical_hash
        )
        or not isinstance(value.get("artifact_role"), str)
        or not value.get("artifact_role")
        or not isinstance(value.get("schema_version"), str)
        or not value.get("schema_version")
        or not isinstance(value.get("path"), str)
        or not value.get("path")
        or PurePosixPath(value["path"]).is_absolute()
        or ".." in PurePosixPath(value["path"]).parts
        or value.get("repository_full_name") != "MassyuRed/Cocolon"
        or value.get("body_free") is not True
        or _RECOVERY_EPOCH004_SHA1_RE.fullmatch(
            str(value.get("git_blob_sha1", ""))
        )
        is None
        or _RECOVERY_EPOCH004_SHA1_RE.fullmatch(
            str(value.get("publication_commit_sha1", ""))
        )
        is None
        or _RECOVERY_EPOCH004_SHA256_RE.fullmatch(
            str(value.get("raw_sha256", ""))
        )
        is None
        or _RECOVERY_EPOCH004_SHA256_RE.fullmatch(
            str(value.get("logical_artifact_sha256", ""))
        )
        is None
    ):
        return False
    return value.get("identity_sha256") == _hash_without(
        value,
        "identity_sha256",
    )


def _recovery_epoch004_p0_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and value == _RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY
        and value.get("p0_external_identity_sha256")
        == _hash_without(value, "p0_external_identity_sha256")
    )


def _recovery_epoch004_reconciliation_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and value == _RECOVERY_EPOCH004_RECONCILIATION_EXTERNAL_IDENTITY
        and value.get("identity_sha256")
        == _hash_without(value, "identity_sha256")
    )


def _recovery_epoch004_git(
    root: Path,
    *args: str,
) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.returncode, result.stdout.strip()


def _recovery_epoch004_git_bytes(
    root: Path,
    *args: str,
) -> tuple[int, bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        timeout=20,
    )
    return result.returncode, result.stdout


def _recovery_epoch004_remote_repository(remote: str) -> str:
    value = remote.strip().removesuffix("/")
    if "://" in value:
        scheme, separator, location = value.partition("://")
        if separator != "://" or scheme not in {"git", "http", "https", "ssh"}:
            return ""
        authority, separator, path = location.partition("/")
        if separator != "/" or not authority:
            return ""
    else:
        authority, separator, path = value.partition(":")
        if separator != ":" or not authority or "@" not in authority:
            return ""
    host = authority.rsplit("@", 1)[-1].partition(":")[0].lower()
    if host not in {
        "git.chatgpt-team.site",
        "github.com",
        "ssh.github.com",
        "www.github.com",
    }:
        return ""
    components = path.removesuffix(".git").strip("/").split("/")
    if len(components) < 2:
        return ""
    return components[-2] + "/" + components[-1]


def _recovery_epoch004_actual_git_binding_valid(
    state: Mapping[str, Any],
) -> bool:
    subject = state.get("source_subject")
    owner = state.get("owner_executor")
    independent = state.get("independent_executor")
    if (
        type(subject) is not dict
        or set(subject) != _RECOVERY_EPOCH004_SOURCE_SUBJECT_KEYS
        or type(owner) is not dict
        or set(owner) != _RECOVERY_EPOCH004_EXECUTOR_KEYS
        or type(independent) is not dict
        or set(independent) != _RECOVERY_EPOCH004_EXECUTOR_KEYS
        or subject.get("repository_full_name") != "MassyuRed/mashos-api"
        or subject.get("source_ref") != "refs/heads/main"
        or subject.get("worktree_clean") is not True
        or any(
            owner.get(key) != subject.get(key)
            or independent.get(key) != subject.get(key)
            for key in _RECOVERY_EPOCH004_SOURCE_SUBJECT_KEYS
        )
        or owner.get("module_path")
        != _RECOVERY_EPOCH004_OWNER_MODULE_PATH
        or independent.get("module_path")
        != _RECOVERY_EPOCH004_INDEPENDENT_MODULE_PATH
        or _RECOVERY_EPOCH004_SHA1_RE.fullmatch(
            str(subject.get("head_commit_sha1", ""))
        )
        is None
        or _RECOVERY_EPOCH004_SHA1_RE.fullmatch(
            str(subject.get("head_tree_sha1", ""))
        )
        is None
        or _RECOVERY_EPOCH004_SHA1_RE.fullmatch(
            str(subject.get("origin_main_commit_sha1", ""))
        )
        is None
    ):
        return False
    root = Path(str(subject.get("repository_root", ""))).resolve()
    owner_path = (root / _RECOVERY_EPOCH004_OWNER_MODULE_PATH).resolve()
    independent_path = (
        root / _RECOVERY_EPOCH004_INDEPENDENT_MODULE_PATH
    ).resolve()
    if (
        str(root) != subject.get("repository_root")
        or owner.get("module_origin") != str(owner_path)
        or independent.get("module_origin") != str(independent_path)
        or not owner_path.is_file()
        or not independent_path.is_file()
    ):
        return False
    code, top = _recovery_epoch004_git(
        root,
        "rev-parse",
        "--show-toplevel",
    )
    if code != 0 or top != str(root):
        return False
    code, head = _recovery_epoch004_git(root, "rev-parse", "HEAD")
    if code != 0 or head != subject.get("head_commit_sha1"):
        return False
    code, tree = _recovery_epoch004_git(root, "rev-parse", "HEAD^{tree}")
    if code != 0 or tree != subject.get("head_tree_sha1"):
        return False
    code, origin_main = _recovery_epoch004_git(
        root,
        "rev-parse",
        "origin/main",
    )
    if (
        code != 0
        or origin_main != subject.get("origin_main_commit_sha1")
    ):
        return False
    code, branch = _recovery_epoch004_git(
        root,
        "symbolic-ref",
        "--quiet",
        "HEAD",
    )
    if code != 0 or branch != "refs/heads/main":
        return False
    code, status = _recovery_epoch004_git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
    )
    if code != 0 or status != "":
        return False
    for earlier, later in (
        (_RECOVERY_EPOCH004_ENTRY_COMMIT_SHA1, "HEAD"),
        ("origin/main", "HEAD"),
    ):
        code, _output = _recovery_epoch004_git(
            root,
            "merge-base",
            "--is-ancestor",
            earlier,
            later,
        )
        if code != 0:
            return False
    for executor, relative_path, source_path in (
        (
            owner,
            _RECOVERY_EPOCH004_OWNER_MODULE_PATH,
            owner_path,
        ),
        (
            independent,
            _RECOVERY_EPOCH004_INDEPENDENT_MODULE_PATH,
            independent_path,
        ),
    ):
        code, blob = _recovery_epoch004_git(
            root,
            "rev-parse",
            f"HEAD:{relative_path}",
        )
        if code != 0 or blob != executor.get("git_blob_sha1"):
            return False
        code, hashed = _recovery_epoch004_git(
            root,
            "hash-object",
            relative_path,
        )
        if code != 0 or hashed != blob:
            return False
        code, raw = _recovery_epoch004_git_bytes(
            root,
            "show",
            f"HEAD:{relative_path}",
        )
        if (
            code != 0
            or raw != source_path.read_bytes()
            or hashlib.sha256(raw).hexdigest()
            != executor.get("raw_sha256")
        ):
            return False
    code, remote = _recovery_epoch004_git(
        root,
        "remote",
        "get-url",
        "origin",
    )
    if (
        code != 0
        or _recovery_epoch004_remote_repository(remote)
        != "MassyuRed/mashos-api"
    ):
        return False
    code, remote_main = _recovery_epoch004_git(
        root,
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/heads/main",
    )
    rows = remote_main.splitlines()
    return bool(
        code == 0
        and len(rows) == 1
        and rows[0]
        == str(subject["origin_main_commit_sha1"])
        + "\trefs/heads/main"
    )


def _recovery_epoch004_reference_valid(
    reference: Any,
    reference_identity: Any,
    subject: Mapping[str, Any],
) -> bool:
    if (
        type(reference) is not dict
        or set(reference) != _RECOVERY_EPOCH004_REFERENCE_KEYS
        or reference.get("schema_version")
        != _RECOVERY_EPOCH004_REFERENCE_SCHEMA
        or reference.get("logical_cycle_id")
        != _RECOVERY_EPOCH004_LOGICAL_CYCLE_ID
        or reference.get("recovery_epoch_id")
        != _RECOVERY_EPOCH004_RECOVERY_EPOCH_ID
        or reference.get("authority_token")
        != _RECOVERY_EPOCH004_NON_CREDIT_MARKER
        or reference.get("source_commit_sha1")
        != subject.get("head_commit_sha1")
        or reference.get("source_tree_sha1")
        != subject.get("head_tree_sha1")
        or reference.get("reservation_count_delta") != 0
        or type(reference.get("reservation_count_delta")) is not int
        or reference.get("formal_exact134_invocation_count") != 0
        or type(reference.get("formal_exact134_invocation_count"))
        is not int
        or reference.get("collection_state") != "NOT_STARTED"
        or reference.get("test_execution_state") != "NOT_STARTED"
        or reference.get("body_free") is not True
        or reference.get("installed_distributions_sha256")
        != artifact_sha256(reference.get("installed_distributions"))
        or reference.get("environment_policy_sha256")
        != artifact_sha256(reference.get("environment_policy"))
        or reference.get("reference_runtime_observation_sha256")
        != _hash_without(
            reference,
            "reference_runtime_observation_sha256",
        )
    ):
        return False
    runtime = reference.get("runtime_materialization")
    return bool(
        type(runtime) is dict
        and runtime.get("schema_version")
        == _RECOVERY_EPOCH004_RUNTIME_MATERIALIZATION_SCHEMA
        and runtime.get("runtime_materialization_state")
        == "NON_CREDIT_CONTRACT_FIXTURE_NOT_MATERIALIZED"
        and runtime.get("body_free") is True
        and runtime.get("runtime_materialization_sha256")
        == _hash_without(runtime, "runtime_materialization_sha256")
        and _recovery_epoch004_external_identity_valid(
            reference_identity,
            role="RECOVERY_EPOCH004_REFERENCE_RUNTIME_OBSERVATION",
            schema=_RECOVERY_EPOCH004_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH004_REFERENCE_PATH,
            logical_hash=reference[
                "reference_runtime_observation_sha256"
            ],
        )
    )


def _recovery_epoch004_bootstrap_valid(
    bootstrap: Any,
    reference: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
    subject: Mapping[str, Any],
) -> bool:
    return bool(
        type(bootstrap) is dict
        and set(bootstrap) == _RECOVERY_EPOCH004_BOOTSTRAP_KEYS
        and bootstrap.get("schema_version")
        == _RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA
        and bootstrap.get("source_commit_sha1")
        == subject.get("head_commit_sha1")
        and bootstrap.get("source_tree_sha1")
        == subject.get("head_tree_sha1")
        and bootstrap.get("formal_owner_artifacts_sha256")
        == artifact_sha256(bootstrap.get("formal_owner_artifacts"))
        and bootstrap.get("formal_test_manifest_sha256")
        == artifact_sha256(bootstrap.get("formal_test_manifest"))
        and bootstrap.get("loaded_plugin_manifest_sha256")
        == artifact_sha256(bootstrap.get("loaded_plugin_manifest"))
        and bootstrap.get("import_manifest_sha256")
        == artifact_sha256(bootstrap.get("import_manifest"))
        and bootstrap.get("expected_installed_distributions_sha256")
        == artifact_sha256(
            bootstrap.get("expected_installed_distributions")
        )
        and bootstrap.get("environment_policy_sha256")
        == artifact_sha256(bootstrap.get("environment_policy"))
        and bootstrap.get("preflight_argv_sha256")
        == artifact_sha256(bootstrap.get("preflight_argv"))
        and bootstrap.get("formal_worker_argv_sha256")
        == artifact_sha256(bootstrap.get("formal_worker_argv"))
        and bootstrap.get("dependency_lock_identity")
        == reference.get("dependency_lock_identity")
        and bootstrap.get("wheel_bundle_manifest_sha256")
        == reference.get("wheel_bundle_manifest_sha256")
        and bootstrap.get("expected_installed_distributions")
        == reference.get("installed_distributions")
        and bootstrap.get("expected_python_runtime_identity")
        == reference.get("python_runtime_identity")
        and bootstrap.get("expected_pytest_distribution_identity")
        == reference.get("pytest_distribution_identity")
        and bootstrap.get(
            "reference_runtime_observation_external_identity"
        )
        == reference_identity
        and bootstrap.get("environment_policy")
        == reference.get("environment_policy")
        and bootstrap.get("unclassified_import_count") == 0
        and type(bootstrap.get("unclassified_import_count")) is int
        and bootstrap.get("unresolved_dynamic_import_count") == 0
        and type(bootstrap.get("unresolved_dynamic_import_count")) is int
        and bootstrap.get("body_free") is True
        and bootstrap.get("bootstrap_closure_sha256")
        == _hash_without(bootstrap, "bootstrap_closure_sha256")
    )


def _recovery_epoch004_source_valid(
    source: Any,
    bootstrap: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
    subject: Mapping[str, Any],
) -> bool:
    if (
        type(source) is not dict
        or set(source) != _RECOVERY_EPOCH004_SOURCE_KEYS
        or source.get("schema_version")
        != _RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA
        or source.get("repository_full_name")
        != subject.get("repository_full_name")
        or source.get("source_ref") != subject.get("source_ref")
        or source.get("source_commit_sha1")
        != subject.get("head_commit_sha1")
        or source.get("source_tree_sha1")
        != subject.get("head_tree_sha1")
        or source.get("worktree_clean") is not True
        or source.get("epoch004_p0_external_identity_sha256")
        != _RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY[
            "p0_external_identity_sha256"
        ]
        or source.get("formal_test_manifest_sha256")
        != bootstrap.get("formal_test_manifest_sha256")
        or source.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or source.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or any(
            _RECOVERY_EPOCH004_SHA256_RE.fullmatch(
                str(source.get(key, ""))
            )
            is None
            for key in _RECOVERY_EPOCH004_SOURCE_SHA256_KEYS
        )
    ):
        return False
    return source.get("source_closure_sha256") == _hash_without(
        source,
        "source_closure_sha256",
    )


def _recovery_epoch004_candidate_valid(
    candidate: Any,
    event: Mapping[str, Any],
    source: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
    historical_ids: Any,
) -> bool:
    if (
        type(candidate) is not dict
        or set(candidate) != _RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS
        or candidate.get("schema_version")
        != _RECOVERY_EPOCH004_CANDIDATE_SCHEMA
        or candidate.get("logical_cycle_id")
        != _RECOVERY_EPOCH004_LOGICAL_CYCLE_ID
        or candidate.get("recovery_epoch_id")
        != _RECOVERY_EPOCH004_RECOVERY_EPOCH_ID
        or not isinstance(candidate.get("candidate_version_id"), str)
        or not candidate.get("candidate_version_id")
        or candidate.get("candidate_version_id")
        != event.get("candidate_version_id")
        or candidate.get("candidate_version_id") in historical_ids
        or _RECOVERY_EPOCH004_UTC_RE.fullmatch(
            str(candidate.get("allocated_at_utc", ""))
        )
        is None
        or candidate.get("p0_external_identity_sha256")
        != _RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY[
            "p0_external_identity_sha256"
        ]
        or candidate.get("source_closure_sha256")
        != source.get("source_closure_sha256")
        or candidate.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
    ):
        return False
    return candidate.get("candidate_allocation_sha256") == _hash_without(
        candidate,
        "candidate_allocation_sha256",
    )


def _recovery_epoch004_admission_valid(
    admission: Any,
    admission_identity: Any,
    reference_identity: Mapping[str, Any],
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    state: Mapping[str, Any],
) -> bool:
    if (
        type(admission) is not dict
        or set(admission) != _RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_KEYS
        or admission.get("schema_version")
        != _RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA
        or admission.get("logical_cycle_id")
        != _RECOVERY_EPOCH004_LOGICAL_CYCLE_ID
        or admission.get("recovery_epoch_id")
        != _RECOVERY_EPOCH004_RECOVERY_EPOCH_ID
        or admission.get("source_closure") != source
        or admission.get("bootstrap_closure") != bootstrap
        or admission.get("owner_validation_state")
        != "PROVED_NON_CREDIT_CONTRACT_FIXTURE"
        or admission.get("independent_verification_state")
        != "PROVED_NON_CREDIT_CONTRACT_FIXTURE"
        or admission.get("state")
        != "NON_CREDIT_CONTRACT_FIXTURE_AWAITING_EVENT1"
        or admission.get("automatic_progression") is not False
        or admission.get("body_free") is not True
        or admission.get("operational_admission_sha256")
        != _hash_without(admission, "operational_admission_sha256")
        or not _recovery_epoch004_external_identity_valid(
            admission_identity,
            role="RECOVERY_EPOCH004_OPERATIONAL_ADMISSION",
            schema=_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA,
            path=_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_PATH,
            logical_hash=admission.get("operational_admission_sha256"),
        )
    ):
        return False
    predecessor = admission.get("predecessor_bindings")
    if (
        type(predecessor) is not dict
        or set(predecessor) != _RECOVERY_EPOCH004_PREDECESSOR_KEYS
        or not _recovery_epoch004_p0_valid(
            predecessor.get("p0_external_identity")
        )
        or _RECOVERY_EPOCH004_SHA256_RE.fullmatch(
            str(
                predecessor.get(
                    "epoch003_immutable_predecessor_set_sha256",
                    "",
                )
            )
        )
        is None
        or not _recovery_epoch004_reconciliation_valid(
            predecessor.get(
                "epoch003_reconciliation_receipt_external_identity"
            )
        )
        or not _recovery_epoch004_external_identity_valid(
            predecessor.get(
                "d1_event1_connection_receipt_external_identity"
            ),
            role=None,
            schema=None,
            path=None,
            logical_hash=None,
        )
        or not _recovery_epoch004_external_identity_valid(
            predecessor.get(
                "d2_event1_connection_receipt_external_identity"
            ),
            role=None,
            schema=None,
            path=None,
            logical_hash=None,
        )
        or predecessor.get(
            "reference_runtime_observation_external_identity"
        )
        != reference_identity
        or predecessor.get("final_source_identity_contract_sha256")
        != artifact_sha256(
            {
                "source_subject": state.get("source_subject"),
                "owner_executor": state.get("owner_executor"),
                "independent_executor": state.get(
                    "independent_executor"
                ),
            }
        )
        or predecessor.get("predecessor_bindings_sha256")
        != _hash_without(predecessor, "predecessor_bindings_sha256")
        or source.get("epoch003_immutable_predecessor_set_sha256")
        != predecessor.get(
            "epoch003_immutable_predecessor_set_sha256"
        )
    ):
        return False
    authority = admission.get("authority")
    scope = admission.get("scope")
    freshness = admission.get("freshness")
    effect = admission.get("effect_boundary")
    return bool(
        type(authority) is dict
        and set(authority) == _RECOVERY_EPOCH004_ADMISSION_AUTHORITY_KEYS
        and authority.get("approval_kind")
        == "NON_CREDIT_CONTRACT_FIXTURE_ONLY"
        and authority.get("admission_authority_token")
        == _RECOVERY_EPOCH004_NON_CREDIT_MARKER
        and authority.get("publication_authority_token")
        == _RECOVERY_EPOCH004_NON_CREDIT_MARKER
        and authority.get("authority_sha256")
        == _hash_without(authority, "authority_sha256")
        and type(scope) is dict
        and set(scope) == _RECOVERY_EPOCH004_ADMISSION_SCOPE_KEYS
        and scope.get("artifact_repository_full_name")
        == "MassyuRed/Cocolon"
        and scope.get("source_repository_full_name")
        == state["source_subject"].get("repository_full_name")
        and scope.get("source_ref")
        == state["source_subject"].get("source_ref")
        and scope.get("source_commit_sha1")
        == state["source_subject"].get("head_commit_sha1")
        and scope.get("source_tree_sha1")
        == state["source_subject"].get("head_tree_sha1")
        and scope.get("source_closure_sha256")
        == source.get("source_closure_sha256")
        and scope.get("bootstrap_closure_sha256")
        == bootstrap.get("bootstrap_closure_sha256")
        and scope.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        == reference_identity.get("identity_sha256")
        and scope.get("next_authority_token")
        == _RECOVERY_EPOCH004_NON_CREDIT_MARKER
        and scope.get("operation_set")
        == ["CANDIDATE_ALLOCATED_WITH_EVENT1_PUBLISHED_AND_POSTVERIFIED"]
        and scope.get("separate_explicit_authority_required") is True
        and scope.get("scope_sha256")
        == _hash_without(scope, "scope_sha256")
        and type(freshness) is dict
        and set(freshness) == _RECOVERY_EPOCH004_FRESHNESS_KEYS
        and _RECOVERY_EPOCH004_UTC_RE.fullmatch(
            str(freshness.get("issued_at_utc", ""))
        )
        is not None
        and freshness.get("expires_at_utc") is None
        and freshness.get("validity_mode")
        == "IDENTITY_STABLE_SINGLE_EVENT1_CONSUMPTION"
        and freshness.get("bound_source_commit_sha1")
        == state["source_subject"].get("head_commit_sha1")
        and freshness.get("bound_source_tree_sha1")
        == state["source_subject"].get("head_tree_sha1")
        and freshness.get(
            "bound_reference_runtime_observation_external_identity_sha256"
        )
        == reference_identity.get("identity_sha256")
        and freshness.get("event1_path_state_at_issuance") == "ABSENT"
        and freshness.get("maximum_event1_consumption_count") == 1
        and type(freshness.get("maximum_event1_consumption_count")) is int
        and freshness.get("invalidation_conditions")
        == [
            "SOURCE_COMMIT_OR_TREE_DRIFT",
            "ORIGIN_MAIN_DRIFT",
            "WORKTREE_NOT_CLEAN",
            "EVENT1_ALREADY_CONSUMED",
        ]
        and freshness.get("reuse_allowed") is False
        and freshness.get("freshness_sha256")
        == _hash_without(freshness, "freshness_sha256")
        and type(effect) is dict
        and set(effect) == _RECOVERY_EPOCH004_EFFECT_KEYS
        and all(
            type(effect.get(key)) is int and effect.get(key) == 0
            for key in _RECOVERY_EPOCH004_EFFECT_COUNT_KEYS
        )
        and effect.get("source_baseline_state") == "UNLOCKED"
        and effect.get("effect_boundary_sha256")
        == _hash_without(effect, "effect_boundary_sha256")
    )


def _recovery_epoch004_event_valid(
    event: Any,
    admission_identity: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
    state: Mapping[str, Any],
) -> bool:
    if (
        type(event) is not dict
        or set(event) != RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS
        or event.get("schema_version")
        != _RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA
        or event.get("ledger_id")
        != "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH004"
        or event.get("event_id")
        != "NLS_V3_RECOVERY_EPOCH004_SEQUENCE_EVENT_01"
        or event.get("logical_cycle_id")
        != _RECOVERY_EPOCH004_LOGICAL_CYCLE_ID
        or event.get("recovery_epoch_id")
        != _RECOVERY_EPOCH004_RECOVERY_EPOCH_ID
        or event.get("event_ordinal") != 1
        or type(event.get("event_ordinal")) is not int
        or event.get("event_name") != "SOURCE_BASELINE_LOCKED"
        or event.get("state") != "NON_CREDIT_CONTRACT_FIXTURE_ONLY"
        or _RECOVERY_EPOCH004_SHA256_RE.fullmatch(
            str(event.get("challenge_id", ""))
        )
        is None
        or _RECOVERY_EPOCH004_UTC_RE.fullmatch(
            str(event.get("timestamp_utc", ""))
        )
        is None
        or event.get("timestamp_kind") != "NON_CREDIT_TEST_ONLY"
        or event.get("body_free") is not True
        or event.get("automatic_progression") is not False
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or not _recovery_epoch004_p0_valid(
            event.get("p0_external_identity")
        )
        or event.get("prior_event") != event.get("p0_external_identity")
    ):
        return False
    source = event.get("source_closure")
    bootstrap = event.get("bootstrap_closure")
    reference = state.get("reference_runtime_observation")
    if (
        not _recovery_epoch004_bootstrap_valid(
            bootstrap,
            reference,
            reference_identity,
            state["source_subject"],
        )
        or not _recovery_epoch004_source_valid(
            source,
            bootstrap,
            reference_identity,
            state["source_subject"],
        )
        or not _recovery_epoch004_candidate_valid(
            event.get("candidate_allocation"),
            event,
            source,
            reference_identity,
            state.get("historical_candidate_version_ids"),
        )
    ):
        return False
    authority = event.get("authority")
    publication = event.get("publication")
    supporting = (
        publication.get("supporting_artifacts")
        if type(publication) is dict
        else None
    )
    expected_supporting = sorted(
        [admission_identity, reference_identity],
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        ),
    )
    return bool(
        type(authority) is dict
        and set(authority) == _RECOVERY_EPOCH004_EVENT_AUTHORITY_KEYS
        and authority.get("approval_kind")
        == "NON_CREDIT_CONTRACT_FIXTURE_ONLY"
        and authority.get("operational_admission") == admission_identity
        and authority.get("publication_authority_token")
        == _RECOVERY_EPOCH004_NON_CREDIT_MARKER
        and authority.get("transition_authority_token")
        == _RECOVERY_EPOCH004_NON_CREDIT_MARKER
        and event.get("primary_evidence_artifact") == admission_identity
        and type(publication) is dict
        and set(publication) == _RECOVERY_EPOCH004_EVENT_PUBLICATION_KEYS
        and _RECOVERY_EPOCH004_SHA1_RE.fullmatch(
            str(publication.get("base_commit_sha1", ""))
        )
        is not None
        and publication.get("branch") == "main"
        and publication.get("event_path") == _RECOVERY_EPOCH004_EVENT1_PATH
        and publication.get("expected_changed_path_count") == 1
        and type(publication.get("expected_changed_path_count")) is int
        and publication.get("publication_state")
        == "NON_CREDIT_CONTRACT_FIXTURE_NOT_PUBLISHED"
        and publication.get("repository_full_name") == "MassyuRed/Cocolon"
        and type(supporting) is list
        and supporting == expected_supporting
        and publication.get("supporting_artifact_count") == 2
        and type(publication.get("supporting_artifact_count")) is int
        and publication.get("supporting_artifact_set_sha256")
        == artifact_sha256(supporting)
    )


def _recovery_epoch004_connection_valid(state: Any) -> bool:
    if (
        type(state) is not dict
        or set(state) != RECOVERY_EPOCH004_EVENT1_CONNECTION_STATE_KEYS
        or not (
            (
                state.get("verification_profile")
                == _RECOVERY_EPOCH004_NON_CREDIT_MARKER
                and state.get("credit_eligible") is False
            )
            or (
                state.get("verification_profile")
                == _RECOVERY_EPOCH004_ACTUAL_GIT_PROFILE
                and state.get("credit_eligible") is True
            )
        )
        or state.get("approved_authority_token")
        != _RECOVERY_EPOCH004_D1_AUTHORITY
        or state.get("authority_state")
        != _RECOVERY_EPOCH004_D1_AUTHORITY_STATE
        or state.get("logical_cycle_id")
        != _RECOVERY_EPOCH004_LOGICAL_CYCLE_ID
        or state.get("recovery_epoch_id")
        != _RECOVERY_EPOCH004_RECOVERY_EPOCH_ID
        or not _recovery_epoch004_p0_valid(
            state.get("p0_external_identity")
        )
        or state.get("historical_candidate_version_ids")
        != list(_RECOVERY_EPOCH004_HISTORICAL_CANDIDATE_VERSION_IDS)
        or state.get("event1_consumption_count") != 1
        or type(state.get("event1_consumption_count")) is not int
        or state.get("source_baseline_state") != "UNLOCKED"
        or type(state.get("later_effect_counts")) is not dict
        or set(state["later_effect_counts"])
        != _RECOVERY_EPOCH004_LATER_EFFECT_KEYS
        or any(
            type(value) is not int or value != 0
            for value in state["later_effect_counts"].values()
        )
        or state.get("automatic_progression") is not False
    ):
        return False
    reference = state.get("reference_runtime_observation")
    reference_identity = state.get(
        "reference_runtime_observation_external_identity"
    )
    admission = state.get("operational_admission")
    admission_identity = state.get(
        "operational_admission_external_identity"
    )
    event = state.get("event1")
    if (
        not _recovery_epoch004_reference_valid(
            reference,
            reference_identity,
            state.get("source_subject"),
        )
        or type(event) is not dict
        or not _recovery_epoch004_admission_valid(
            admission,
            admission_identity,
            reference_identity,
            event.get("source_closure"),
            event.get("bootstrap_closure"),
            state,
        )
        or not _recovery_epoch004_event_valid(
            event,
            admission_identity,
            reference_identity,
            state,
        )
        or event.get("candidate_version_id") == ""
        or event.get("candidate_allocation", {}).get(
            "candidate_version_id"
        )
        != event.get("candidate_version_id")
    ):
        return False
    return _recovery_epoch004_actual_git_binding_valid(state)


def verify_recovery_epoch004_sequence_event1_contract_state_v2(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Independently verify Epoch004 Event1 v2 without owner trust."""

    failure = (
        "RECOVERY_EPOCH004_EVENT1_V2_INDEPENDENT_VERIFICATION_INVALID",
    )
    try:
        return () if _recovery_epoch004_connection_valid(state) else failure
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        RuntimeError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


__all__ = [
    "RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT",
    "RECOVERY_EPOCH002_P0_EXTERNAL_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_P0_PARENT_DESIGN_KEYS",
    "RECOVERY_EPOCH002_P0_RECEIPT_KEYS",
    "RECOVERY_EPOCH002_SHARED_PRIMITIVE_ALLOWLIST",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS",
    "verify_recovery_epoch002_artifact_identity",
    "verify_recovery_epoch002_operational_artifact_identity",
    "verify_recovery_epoch002_p0_external_identity",
    "verify_recovery_epoch002_publication_state",
    "verify_recovery_epoch002_published_artifact",
    "verify_recovery_epoch002_success_contract_state",
    "RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS",
    "RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS",
    "RECOVERY_EPOCH003_FAILURE_CLASSES",
    "verify_recovery_epoch003_prestart_historical_receipt_byte_form_eligibility_v1",
    "verify_recovery_epoch003_reference_runtime_observation",
    "verify_recovery_epoch003_reference_runtime_observation_v2",
    "verify_recovery_epoch003_operational_admission_contract",
    "verify_recovery_epoch003_operational_admission_contract_v2",
    "verify_recovery_epoch003_bootstrap_source_runtime_contract",
    "verify_recovery_epoch003_bootstrap_source_runtime_contract_current",
    "RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS",
    "RECOVERY_EPOCH004_EVENT1_CONNECTION_STATE_KEYS",
    "verify_recovery_epoch004_sequence_event1_contract_state_v2",
]
