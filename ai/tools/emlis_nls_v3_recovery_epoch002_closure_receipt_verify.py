#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent publication verifier for Recovery Epoch 002.

This verifier intentionally does not import the publication owner.
"""

from copy import deepcopy
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
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
    green_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
        "Successor_GREEN_Result_20260726.json"
    )
    if (
        type(closure) is not dict
        or type(completion) is not dict
        or set(completion) != _SUCCESS_COMPLETION_KEYS
        or completion.get("schema_version") != _SUCCESS_COMPLETION_SCHEMA
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
        != _SUCCESS_COMPLETION_PATH
        or not _success_exact1_valid(
            publication,
            artifact=completion,
            roles=frozenset({"SUCCESSOR_COMPLETION_RECEIPT"}),
            schema=_SUCCESS_COMPLETION_SCHEMA,
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
        or type(completion_identity) is not dict
        or set(completion_identity)
        != RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS
        or completion_identity.get("artifact_role")
        != "SUCCESSOR_COMPLETION_RECEIPT"
        or completion_identity.get("path") != _SUCCESS_COMPLETION_PATH
        or completion_identity.get("body_free") is not True
        or completion_identity.get("identity_sha256")
        != _hash_without(completion_identity, "identity_sha256")
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
]
