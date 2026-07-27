# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for the post-D2 Recovery Epoch 002 success continuation.

This exact64 oracle freezes the additive successor closure, terminal-v2
evidence, accepted/Step/all11 owners, atomic success publication,
independent verification, and formal-parent continuation defined by the
post-D2 Parent Addendum.  It does not implement any production owner.

All fixtures are body-free contract probes.  The test does not allocate a
candidate, publish Event1, create readiness or a reservation, invoke formal
exact134, publish terminal or success artifacts, authorize P2, or advance
Cycle 001.
"""

from copy import deepcopy
import ast
from functools import lru_cache
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping

import pytest


_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_TOOLS_ROOT = _AI_ROOT / "tools"
for _path in (_INFERENCE_ROOT, _TOOLS_ROOT, _HERE.parent):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from emlis_ai_nls_v3_artifact_contract import (  # noqa: E402
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (  # noqa: E402
    RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS,
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256,
    RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP,
)
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (  # noqa: E402
    fresh_recovery_epoch001_canonical_current_closure,
)
from emlis_nls_v3_recovery_epoch002_closure_receipt_verify import (  # noqa: E402
    verify_recovery_epoch002_published_artifact,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_POST_D2_SOURCE_BASELINE_"
    "ELIGIBILITY_SUCCESSION_ACCEPTED_STEP0_10_ALL11_EVENT2_ATOMIC_"
    "SUCCESS_OWNER_GRAPH_AND_FORMAL_PARENT_CONTINUATION_REMEDIATION_"
    "RED_FREEZE_ONLY"
)
_FUTURE_P1_AUTHORITY_TOKEN = (
    "FIXTURE_ONLY_UNISSUED_RECOVERY_EPOCH002_FUTURE_P1_AUTHORITY"
)
_FUTURE_EVENT2_AUTHORITY_TOKEN = (
    "FIXTURE_ONLY_UNISSUED_RECOVERY_EPOCH002_FUTURE_EVENT2_AUTHORITY"
)
_KAREN_DIARY_ENTRY = "700f749f5149cac1f8bd4bab8a364d524a56985b"
_COCOLON_ENTRY = "e862a5600dd90927d7b74ef3214cc284908a2a4f"
_MASHOS_API_ENTRY = "5eb4d6d1f0a18a715f33305e7fb7cfe92be42d74"
_MASHOS_API_ENTRY_TREE = "b7ad6dd2dbc90e9db296f8599103597d6bbd7ff7"
_PARENT_ADDENDUM_BASE_COMMIT = "2c3fc3d3b29365b073ee228c0ac536d4ffc3cffc"
_PARENT_ADDENDUM_PUBLICATION_COMMIT = (
    "462c933a597233b111962bb2e8ac41f0182dac12"
)
# A fixture value, not a frozen future Cocolon head.  Validators must accept
# the freshly observed authority-ref commit supplied by each future gate.
_SYNTHETIC_FRESH_COCOLON_VERIFICATION_COMMIT = "6" * 40
_PARENT_ADDENDUM_BLOB = "8016eeb3e2731dc837423e48497d424b01ab34d4"
_PARENT_ADDENDUM_SHA256 = (
    "10ecd8dfb549c514c0fca2f9bd7c0bde225feb5eabc1100a13375187c6ef7300"
)
_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256 = (
    "527eb11a767582a2f86531e34e044dffa9f0ed034af91ef063c3acc33813ba6d"
)
_PARENT_ADDENDUM_RECEIPT_SHA256 = (
    "913058df480e113f949185d874ed48ddfddb21b36773c5ec5d77771aba3873ac"
)
_PARENT_ADDENDUM_RECEIPT_RAW_SHA256 = (
    "b81a9956a6419d1bdb1cb9440569f151da2aeb22230c72ee774944d6aefdc6e8"
)
_PARENT_ADDENDUM_RECEIPT_BLOB = (
    "06972af95e59daf953e3ef059ba38a3d4a295f42"
)
_PARENT_ADDENDUM_RECEIPT_ROLE = (
    "PARENT_ADDENDUM_DESIGN_FROZEN_RECEIPT"
)
_PARENT_ADDENDUM_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_successor_parent_addendum_design_frozen_receipt.v1"
)
_PARENT_ADDENDUM_RECEIPT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_BodyFree_Receipt_20260726.json"
)
_PARENT_ADDENDUM_DESIGN_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_20260726.md"
)
_PARENT_ADDENDUM_HANDOFF_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_Handoff_20260726.md"
)
_PARENT_ADDENDUM_EXECUTION_PLAN_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_ExecutionAndClosurePlan_ReadOnly_20260723.md"
)
_PARENT_ADDENDUM_LATEST_SNAPSHOT_PATH = (
    "Cocolon_前提資料/07_latest_snapshot_diff.md"
)
_PARENT_ADDENDUM_CHANGED_PATHS = (
    _PARENT_ADDENDUM_LATEST_SNAPSHOT_PATH,
    _PARENT_ADDENDUM_EXECUTION_PLAN_PATH,
    _PARENT_ADDENDUM_DESIGN_PATH,
    _PARENT_ADDENDUM_RECEIPT_PATH,
    _PARENT_ADDENDUM_HANDOFF_PATH,
)
_PARENT_ADDENDUM_RECEIPT_STATE = (
    "RECOVERY_EPOCH002_POST_D2_SOURCE_BASELINE_ELIGIBILITY_SUCCESSION_"
    "PARENT_ADDENDUM_DESIGN_FROZEN_AUTHORITY_STOP"
)
_HISTORICAL_D2_FINAL_CLOSURE_SHA256 = (
    "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_SHA256 = (
    "0af065a6499ff99164d206f6fddafafaa91f3436de191f20078e6c4aa858253c"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_RAW_SHA256 = (
    "fd68f2f241fcb959def548cd2b6d8cb475415a4466c81363bfceef2ca3ac27a1"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_BLOB = (
    "d93f7e63e8a941a15f11cfdc088a8613af041e41"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_COMMIT = (
    "8d26f3344be8b1e6a4661f958d8279a6236191d1"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "retry_lineage_and_formal_worker_bootstrap_oracle_correction_"
    "refreeze_and_implementation_green_receipt.v1"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
    "PostReservationRetryLineageAndFormalWorkerBootstrapCompleteness"
    "Reconciliation_OracleExact5CollisionCorrectionRefreezeAnd"
    "Implementation_GREEN_BodyFree_Receipt_20260726.json"
)
_HISTORICAL_D2_COMPLETION_RECEIPT_KEYS = _keys(
    """
    schema_version d2_final_closure_sha256 state automatic_progression
    body_free receipt_sha256
    """
)
_P0_EXTERNAL_IDENTITY_SHA256 = (
    "0b5f4b0e3c3c023867a858782869c570e5a55c27cb72d8db108c309408581ce0"
)
_P0_PARENT_DESIGN_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "AttemptConsumptionUnknownPostReservationRetryLineageAnd"
    "FormalWorkerBootstrapNonconformance_EpochInvalidationAnd"
    "RecoveryEpoch002_ParentDesign_ReadOnly_20260725.md"
)
_P0_PARENT_DESIGN_COMMIT = (
    "832a93becb7795f2a3f1f4110d75ae03e9444ef4"
)
_P0_PARENT_DESIGN_BLOB = "af00c5c4a49207fb94108afbf383ea0e830620ae"
_P0_PARENT_DESIGN_RAW_SHA256 = (
    "8b6564442d69fea1b38cb59ea3c5302874e6f92f87bfd5ce0728985094739829"
)
_P0_RECEIPT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "AttemptConsumptionUnknownPostReservationRetryLineageAnd"
    "FormalWorkerBootstrapNonconformance_EpochInvalidationAnd"
    "RecoveryEpoch002_ParentDesign_ReadOnly_BodyFree_Receipt_20260725.json"
)
_P0_RECEIPT_COMMIT = "149fb1e9156d245d8399a4bb3bf7a6f202099a56"
_P0_RECEIPT_BLOB = "25081708104ba208c54887e53ed2d2c34c1d175e"
_P0_RECEIPT_RAW_SHA256 = (
    "740accc32f3bdfe4458f9a2e6cb2692bacde0feaebc24d03764be10318642c4c"
)
_P0_RECEIPT_LOGICAL_SHA256 = (
    "d2cd0b3541db68ccddcb9357ba78ffb3ea72df2c0b87e7c49b17b688e6cfffb2"
)
_THIS_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_post_d2_success_"
    "owner_graph_and_formal_parent_continuation_red.py"
)
_HISTORICAL_D1_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_retry_lineage_and_"
    "formal_worker_bootstrap_reconciliation_red.py"
)

_ROLE_PATHS = {
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
_ROLE_BINDINGS = tuple(sorted(_ROLE_PATHS.items()))
_DISTINCT_OWNER_PATHS = frozenset(_ROLE_PATHS.values())
_NEW_SUCCESS_OWNER_PATHS = (
    _ROLE_PATHS["accepted_test_run_receipt_owner"],
    _ROLE_PATHS["current_step_completion_receipt_owner"],
    _ROLE_PATHS["all11_receipt_owner"],
)
_EXISTING_SINGLE_PUBLICATION_ROLES = frozenset(
    {
        "SOURCE_BASELINE_EVENT",
        "BOOTSTRAP_READINESS",
        "FORMAL_TEST_RUN_RESERVATION",
        "FORMAL_WORKER_TERMINAL_RESULT",
        "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
        "READY_UNUSED_AUTHORITY_STOP",
    }
)
_POST_D2_SINGLE_PUBLICATION_ROLES = (
    _EXISTING_SINGLE_PUBLICATION_ROLES
    | {
        "SUCCESSOR_COMPLETION_RECEIPT",
        "P1_OPERATIONAL_ADMISSION_RECEIPT",
    }
)

_SCHEMAS = {
    "successor_closure": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "post_d2_source_baseline_eligibility_successor_closure.v1"
    ),
    "successor_completion": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "post_d2_source_baseline_eligibility_successor_completion_receipt.v1"
    ),
    "success_owner_graph": (
        "cocolon.emlis.nls_v3.recovery_epoch002.success_owner_graph.v1"
    ),
    "success_contract_manifest": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "success_contract_test_manifest.v1"
    ),
    "bootstrap_v2": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_manifest.v2"
    ),
    "readiness": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_readiness.v1"
    ),
    "candidate_v2": (
        "cocolon.emlis.nls_v3.recovery_epoch002.candidate_allocation.v2"
    ),
    "event_v2": (
        "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v2"
    ),
    "operational_admission": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "p1_operational_admission_receipt.v1"
    ),
    "transaction_capability": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "git_transaction_capability.v1"
    ),
    "transport_capability": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "git_transport_capability.v1"
    ),
    "durable_store_capability": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "durable_store_capability.v1"
    ),
    "terminal_v2": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_terminal_result.v2"
    ),
    "unknown_disposition": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "attempt_consumption_unknown_disposition.v1"
    ),
    "accepted": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "accepted_test_run_receipt.v1"
    ),
    "success_lineage": (
        "cocolon.emlis.nls_v3.recovery_epoch002.success_lineage.v1"
    ),
    "step": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "current_step_completion_receipt.v1"
    ),
    "step_artifact_evidence": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "current_step_artifact_evidence.v1"
    ),
    "all11": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "all11_completion_chain.v1"
    ),
    "atomic_manifest": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "all11_atomic_publication_manifest.v1"
    ),
}

_SUCCESSOR_CLOSURE_KEYS = _keys(
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
_SUCCESSOR_COMPLETION_KEYS = _keys(
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
_BOOTSTRAP_V2_KEYS = _keys(
    """
    schema_version source_commit_sha1 source_tree_sha1
    formal_owner_artifacts formal_owner_artifacts_sha256
    formal_test_node_ids formal_test_manifest formal_test_manifest_sha256
    conftest_plugin_mode pytest_plugins_environment_variable_removed
    pytest_entrypoint_autoload_disabled explicit_plugin_allowlist
    loaded_plugin_manifest loaded_plugin_manifest_sha256 import_manifest
    import_manifest_sha256 dependency_lock_identity
    installed_distributions installed_distributions_sha256
    python_runtime_identity pytest_distribution_identity environment_profile
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
_OWNER_BINDING_KEYS = _keys("role path git_blob_sha1 raw_sha256")
_SOURCE_FILE_IDENTITY_KEYS = _keys("path git_blob_sha1 raw_sha256")
_PROOF_SOURCE_KEYS = _keys("path git_blob_sha1 sha256")
_VERIFIER_CONSTRAINT_KEYS = _keys(
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
_CANDIDATE_V2_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    historical_d2_final_closure_sha256 historical_d2_completion_receipt
    successor_source_closure_sha256 successor_completion_receipt
    allocated_at_utc candidate_allocation_sha256
    """
)
_EVENT_V2_KEYS = _keys(
    """
    schema_version ledger_id event_id logical_cycle_id recovery_epoch_id
    candidate_version_id event_name event_ordinal state timestamp_utc
    timestamp_kind authority challenge_id source_closure prior_event
    primary_evidence_artifact publication automatic_progression body_free
    event_sha256 p0_external_identity candidate_allocation bootstrap_closure
    """
)
_EVENT_AUTHORITY_KEYS = _keys(
    """
    approval_kind transition_authority_token publication_authority_token
    operational_admission
    """
)
_EVENT_PUBLICATION_KEYS = _keys(
    """
    repository_full_name branch base_commit_sha1 event_path
    supporting_artifact_count supporting_artifacts
    supporting_artifact_set_sha256 expected_changed_path_count
    ref_update_mode publication_state transaction_capability
    """
)
_EVENT_PUBLICATION_OPTIONAL_KEYS = _keys(
    "ref_update_mode transaction_capability"
)
_TRANSACTION_CAPABILITY_KEYS = _keys(
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
_SUCCESS_PUBLICATION_TRANSACTION_KEYS = _keys(
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
_SUCCESS_PUBLICATION_TRANSACTION_REQUIRED_KEYS = _keys(
    """
    reflection_contract_version changed_paths target_blob_sha1_by_path
    ref_update_result ref_update_attempt_count
    publication_commit_sha1_by_path write_commits
    """
)
_WRITE_COMMIT_KEYS = _keys("commit_sha1 changed_paths")
_TERMINAL_COMMIT_OBSERVATION_KEYS = _keys(
    """
    commit_sha1 tree_sha1 authoritative_ref_read authoritative_tree_read
    paths_present
    """
)
_OPERATIONAL_ADMISSION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id
    successor_completion_receipt successor_source_closure_sha256
    repository_full_name source_ref authority challenge_id scope
    transport_capability durable_store_capability owner_validation_state
    independent_verification_state issued_at_utc expires_at_utc state
    automatic_progression body_free operational_admission_sha256
    """
)
_OPERATIONAL_ADMISSION_OPTIONAL_KEYS = _keys(
    "transport_capability durable_store_capability"
)
_ADMISSION_AUTHORITY_KEYS = _keys(
    """
    approval_kind admission_authority_token publication_authority_token
    authority_sha256
    """
)
_ADMISSION_SCOPE_KEYS = _keys(
    """
    repository_full_name source_ref successor_source_closure_sha256
    operation_set scope_sha256
    """
)
_ADMISSION_OPERATION_SET = (
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
_TRANSPORT_CAPABILITY_KEYS = _keys(
    """
    schema_version provider_class provider_identity_sha256
    authoritative_ref_read expected_old_compare_and_swap
    commit_parent_tree_read recursive_tree_read
    exact_changed_path_verification complete_unchanged_path_verification
    full_postfetch_verification scope_sha256 challenge_id observed_at_utc
    transport_capability_sha256
    """
)
_DURABLE_STORE_CAPABILITY_KEYS = _keys(
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

_TERMINAL_V2_KEYS = _keys(
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
_EXACT1_PUBLICATION_KEYS = _keys(
    """
    reflection_contract_version artifact identity changed_paths
    parent_commit_sha1s expected_old_sha1 observed_old_sha1
    postfetch_evidence postfetch_state
    """
)
_SINGLE_PUBLICATION_TRANSACTION_KEYS = _keys(
    """
    reflection_contract_version artifact_role path expected_changed_paths
    parent_commit_sha1s
    expected_old_sha1 requested_expected_old_sha1 observed_old_sha1
    head_commit_sha1 target_absent_at_base unchanged_path_mismatches
    owner_issue_codes independent_issue_codes postfetch_state publication
    """
)
_CURRENT_REFLECTION_CONTRACT = "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
_OUTCOME_KEYS = _keys(
    """
    test_node_id source_path source_blob_sha1 source_sha256 result
    expected_closed_code actual_closed_code evidence_sha256
    """
)
_COUNTS_KEYS = _keys(
    """
    collected executed passed failed errors skipped xfailed xpassed deselected
    collection_errors
    """
)
_NEGATIVE_CLOSED_CODES = (
    "design_hash_mismatch",
    "emotion_options_mismatch",
    "corpus_registry:keyset_mismatch",
    "MISSING_FIELD",
    "OBLIGATION_INVENTORY_OVERFLOW",
    "SEMANTIC_INVENTORY_RESULT_TYPE_INVALID",
    "DISCOURSE_PARENT_REVALIDATION_FAILED",
    "AST_PARENT_REVALIDATION_FAILED",
    "CANDIDATE_UTF8_REQUIRED",
    "HARD_GATE_RESULT_TYPE_INVALID",
    "RUNTIME_STATE_TYPE_INVALID",
)
_FORMAL_NODE_IDS = tuple(
    node_id
    for step in range(11)
    for node_id in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
)
_NEGATIVE_CLOSED_CODE_BY_NODE = {
    row["independent_negative_proof"]["test_node_id"]: (
        row["independent_negative_proof"]["expected_closed_code"]
    )
    for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
}
_NEGATIVE_NODE_IDS = tuple(
    row["independent_negative_proof"]["test_node_id"]
    for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
)
_OBSERVED_NEGATIVE_CLOSED_CODES = (
    "design_hash_mismatch",
    "emotion_options_mismatch",
    "corpus_registry:keyset_mismatch",
    "MISSING_FIELD",
    "OBLIGATION_INVENTORY_OVERFLOW",
    "SEMANTIC_INVENTORY_RESULT_TYPE_INVALID",
    "DISCOURSE_PARENT_REVALIDATION_FAILED",
    "AST_PARENT_REVALIDATION_FAILED",
    "CANDIDATE_UTF8_REQUIRED",
    "HARD_GATE_RESULT_TYPE_INVALID",
    "RUNTIME_STATE_TYPE_INVALID",
)
_OBSERVED_NEGATIVE_CLOSED_CODE_BY_NODE = dict(
    zip(
        _NEGATIVE_NODE_IDS,
        _OBSERVED_NEGATIVE_CLOSED_CODES,
        strict=True,
    )
)

_READINESS_KEYS = _keys(
    """
    schema_version authority_token event1_challenge_id
    preflight_challenge_id preflight_id candidate_version_id
    logical_cycle_id recovery_epoch_id source_baseline_event source_closure
    bootstrap_closure python_runtime_identity pytest_distribution_identity
    dependency_lock_identity environment_profile preflight_owner_identity
    preflight_argv_sha256 loaded_plugin_manifest_sha256 readiness_state
    formal_collection_state formal_execution_state pytest_main_called
    owner_validation_state independent_verification_state
    preflight_started_at_utc preflight_finished_at_utc
    readiness_receipt_path automatic_progression body_free
    bootstrap_readiness_receipt_sha256
    """
)
_RESERVATION_KEYS = _keys(
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
_ACCEPTED_KEYS = _keys(
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
_PRIOR_RESERVATION_ROW_KEYS = _keys(
    """
    reservation_ordinal reservation_artifact attempt_id disposition_kind
    disposition_artifact
    """
)
_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)

_STEP_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    step_number lineage current_binding actual_owners strict_contracts
    positive_proof independent_negative_proof artifact_receipt parent_binding
    completion_condition stop_conditions next_authority verdict
    automatic_progression body_free receipt_sha256
    """
)
_STEP_LINEAGE_KEYS = _keys(
    """
    kind historical_disposition historical_rewrite historical_as_current
    backfill
    """
)
_STEP_CURRENT_BINDING_KEYS = _keys(
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
_ACTUAL_OWNER_KEYS = _keys("path git_blob_sha1 sha256 symbol role")
_STRICT_CONTRACT_KEYS = _keys(
    """
    contract_id schema_version validator_path validator_blob_sha1
    validator_symbol invariant_ids
    """
)
_ARTIFACT_RECEIPT_KEYS = _keys(
    """
    schema_version step_number required_artifact_schema_version
    owner_binding_sha256 strict_contract_binding_sha256
    requirement_registry_sha256 accepted_test_run_receipt_sha256
    formal_completion_evidence_sha256 body_free
    """
)
_PARENT_BINDING_KEYS = _keys(
    """
    parent_kind parent_step_number source_baseline_event_identity_sha256
    parent_receipt_sha256
    """
)
_COMPLETION_CONDITION_KEYS = _keys(
    "condition_id required satisfied evidence_sha256"
)
_STOP_CONDITION_KEYS = _keys(
    """
    condition_id proof_scope proof_node_registry_sha256
    accepted_test_run_receipt_sha256 triggered evidence_sha256
    """
)
_ALL11_KEYS = _keys(
    """
    schema_version candidate_version_id logical_cycle_id recovery_epoch_id
    source_baseline_event source_closure registry_sha256
    formal_node_registry_sha256 accepted_test_run_artifact
    accepted_test_run_receipt_sha256 receipt_count ordered_steps receipts
    receipt_artifacts receipt_sha256s required_sequence_event_2
    next_authority publication_state automatic_progression body_free
    all11_completion_chain_sha256
    """
)
_REQUIRED_EVENT2_KEYS = _keys(
    """
    event_id event_name event_ordinal state prior_event_identity_sha256
    """
)

_ATOMIC_MANIFEST_KEYS = _keys(
    """
    schema_version candidate_version_id logical_cycle_id recovery_epoch_id
    source_baseline_event base_commit_sha1 core_artifact_count core_artifacts
    core_artifact_set_sha256 event_supporting_artifact_count
    expected_changed_path_count event_path ref_update_mode body_free
    atomic_publication_manifest_sha256
    """
)
_CANDIDATE_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 body_free
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
_CORE_PATHS = tuple(sorted(_SUCCESS_PATHS[:13]))
_EVENT2_SUPPORTING_PATHS = tuple(sorted(_SUCCESS_PATHS[:14]))
_SUCCESS_CHANGED_PATHS = tuple(sorted(_SUCCESS_PATHS))
_ACCEPTED_PATH = _SUCCESS_PATHS[0]
_STEP_PATHS = _SUCCESS_PATHS[1:12]
_ALL11_PATH = _SUCCESS_PATHS[12]
_ATOMIC_MANIFEST_PATH = _SUCCESS_PATHS[13]
_EVENT2_PATH = _SUCCESS_PATHS[14]

_PHASE_ORDER = (
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT",
    "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
    "PARENT_SPAWN_INTENT_PERSISTED",
    "FORMAL_EXACT134_ONCE",
    "TERMINAL_RESULT_OR_UNKNOWN_STOP",
    "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED",
    "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED",
)
_EXECUTABLE_PHASES = (
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT",
    "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_EXACT134_ONCE",
    "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED",
    "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED",
)
_EXTERNAL_PORTS = (
    "observe_event1_publication",
    "run_bootstrap_preflight",
    "publish_readiness",
    "publish_reservation",
    "spawn_exact134_once",
    "publish_terminal_disposition",
    "publish_success_exact15",
)
_PARENT_VALID_TERMINAL_INPUT_KEYS = _keys(
    """
    tag terminal_kind terminal_result terminal_disposition_artifact
    terminal_disposition_postfetch_evidence
    """
)
_PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS = _keys(
    """
    tag unknown_disposition terminal_disposition_artifact
    terminal_disposition_postfetch_evidence
    """
)
_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS = _keys(
    """
    accepted step all11 atomic_manifest event2
    """
)
_UNKNOWN_DISPOSITION_KEYS = _keys(
    """
    schema_version reservation_artifact attempt_id checkpoint_status
    last_valid_stage terminal_result_status exit_class exit_code signal_number
    stop_code automatic_retry body_free
    attempt_consumption_unknown_disposition_sha256
    """
)
_SHARED_PRIMITIVE_ALLOWLIST = (
    "canonical_json_bytes",
    "artifact_sha256",
)

_SUCCESSOR_COMPLETION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorCompletion_BodyFree_Receipt_20260726.json"
)
_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_P1OperationalAdmission_"
    "BodyFree_Receipt_20260726.json"
)
_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_SequenceEvent01_"
    "SourceBaselineLocked_BodyFree_Event_20260726.json"
)

_TARGET_APIS = {
    "closure": (
        _ROLE_PATHS["bootstrap_closure_owner"],
        "validate_recovery_epoch002_successor_closure_state",
    ),
    "sequence": (
        _ROLE_PATHS["sequence_lineage_owner"],
        "validate_recovery_epoch002_successor_succession_state",
    ),
    "event2": (
        _ROLE_PATHS["sequence_lineage_owner"],
        "validate_recovery_epoch002_success_event2_state",
    ),
    "terminal": (
        _ROLE_PATHS["terminal_result_owner"],
        "validate_recovery_epoch002_success_terminal_state",
    ),
    "runner": (
        _ROLE_PATHS["formal_worker_owner"],
        "validate_recovery_epoch002_closed_code_capture_state",
    ),
    "accepted": (
        _ROLE_PATHS["accepted_test_run_receipt_owner"],
        "validate_recovery_epoch002_accepted_test_run_state",
    ),
    "step": (
        _ROLE_PATHS["current_step_completion_receipt_owner"],
        "validate_recovery_epoch002_step_completion_state",
    ),
    "all11": (
        _ROLE_PATHS["all11_receipt_owner"],
        "validate_recovery_epoch002_all11_completion_state",
    ),
    "publication": (
        _ROLE_PATHS["publication_owner"],
        "validate_recovery_epoch002_success_publication_state",
    ),
    "single_publication": (
        _ROLE_PATHS["publication_owner"],
        "validate_recovery_epoch002_post_d2_single_publication_state",
    ),
    "independent": (
        _ROLE_PATHS["independent_verifier"],
        "verify_recovery_epoch002_success_contract_state",
    ),
    "parent": (
        _ROLE_PATHS["formal_parent_owner"],
        "validate_recovery_epoch002_formal_parent_continuation_state",
    ),
}
_REQUIRED_EXPORTS: dict[str, dict[str, Any]] = {
    "closure": {
        "RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA": (
            _SCHEMAS["successor_closure"]
        ),
        "RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS": (
            _SUCCESSOR_CLOSURE_KEYS
        ),
        "RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA": _SCHEMAS["bootstrap_v2"],
        "RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS": _BOOTSTRAP_V2_KEYS,
        "RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_SCHEMA": (
            _SCHEMAS["success_owner_graph"]
        ),
        "RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_KEYS": (
            _SUCCESS_OWNER_GRAPH_KEYS
        ),
        "RECOVERY_EPOCH002_SUCCESS_OWNER_BINDING_KEYS": (
            _OWNER_BINDING_KEYS
        ),
        "RECOVERY_EPOCH002_INDEPENDENT_VERIFIER_CONSTRAINT_KEYS": (
            _VERIFIER_CONSTRAINT_KEYS
        ),
        "RECOVERY_EPOCH002_SUCCESS_OWNER_ROLE_BINDINGS": _ROLE_BINDINGS,
        "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_SCHEMA": (
            _SCHEMAS["success_contract_manifest"]
        ),
        "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_KEYS": (
            _SUCCESS_CONTRACT_MANIFEST_KEYS
        ),
        "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_FILE_KEYS": (
            _SOURCE_FILE_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE": (
            _PARENT_ADDENDUM_RECEIPT_ROLE
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA": (
            _PARENT_ADDENDUM_RECEIPT_SCHEMA
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH": (
            _PARENT_ADDENDUM_RECEIPT_PATH
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS": (
            _EXTERNAL_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256": (
            _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS": (
            _PARENT_ADDENDUM_CHANGED_PATHS
        ),
    },
    "sequence": {
        "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_ROLE": (
            "D2_COMPLETION_RECEIPT"
        ),
        "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_SCHEMA": (
            _HISTORICAL_D2_COMPLETION_RECEIPT_SCHEMA
        ),
        "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_PATH": (
            _HISTORICAL_D2_COMPLETION_RECEIPT_PATH
        ),
        "RECOVERY_EPOCH002_D2_COMPLETION_RECEIPT_KEYS": (
            _HISTORICAL_D2_COMPLETION_RECEIPT_KEYS
        ),
        "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_SCHEMA": (
            _SCHEMAS["successor_completion"]
        ),
        "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_KEYS": (
            _SUCCESSOR_COMPLETION_KEYS
        ),
        "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH": (
            _SUCCESSOR_COMPLETION_PATH
        ),
        "RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_SCHEMA": (
            _SCHEMAS["candidate_v2"]
        ),
        "RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_V2_KEYS": (
            _CANDIDATE_V2_KEYS
        ),
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA": _SCHEMAS["event_v2"],
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS": _EVENT_V2_KEYS,
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS": (
            _EVENT_AUTHORITY_KEYS
        ),
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS": (
            _EVENT_PUBLICATION_KEYS
        ),
        "RECOVERY_EPOCH002_TRANSACTION_CAPABILITY_KEYS": (
            _TRANSACTION_CAPABILITY_KEYS
        ),
        "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCHEMA": (
            _SCHEMAS["operational_admission"]
        ),
        "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_KEYS": (
            _OPERATIONAL_ADMISSION_KEYS
        ),
        "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_OPERATION_SET": (
            _ADMISSION_OPERATION_SET
        ),
        "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_AUTHORITY_KEYS": (
            _ADMISSION_AUTHORITY_KEYS
        ),
        "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_SCOPE_KEYS": (
            _ADMISSION_SCOPE_KEYS
        ),
        "RECOVERY_EPOCH002_TRANSPORT_CAPABILITY_KEYS": (
            _TRANSPORT_CAPABILITY_KEYS
        ),
        "RECOVERY_EPOCH002_DURABLE_STORE_CAPABILITY_KEYS": (
            _DURABLE_STORE_CAPABILITY_KEYS
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE": (
            _PARENT_ADDENDUM_RECEIPT_ROLE
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA": (
            _PARENT_ADDENDUM_RECEIPT_SCHEMA
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH": (
            _PARENT_ADDENDUM_RECEIPT_PATH
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS": (
            _EXTERNAL_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256": (
            _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS": (
            _PARENT_ADDENDUM_CHANGED_PATHS
        ),
    },
    "event2": {
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_SCHEMA": _SCHEMAS["event_v2"],
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_V2_KEYS": _EVENT_V2_KEYS,
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_AUTHORITY_KEYS": (
            _EVENT_AUTHORITY_KEYS
        ),
        "RECOVERY_EPOCH002_SEQUENCE_EVENT_PUBLICATION_KEYS": (
            _EVENT_PUBLICATION_KEYS
        ),
        "RECOVERY_EPOCH002_TRANSACTION_CAPABILITY_KEYS": (
            _TRANSACTION_CAPABILITY_KEYS
        ),
        "RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS": (
            _EVENT2_SUPPORTING_PATHS
        ),
        "RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS": (
            _SUCCESS_CHANGED_PATHS
        ),
    },
    "terminal": {
        "RECOVERY_EPOCH002_TERMINAL_RESULT_V2_SCHEMA": (
            _SCHEMAS["terminal_v2"]
        ),
        "RECOVERY_EPOCH002_TERMINAL_RESULT_V2_KEYS": _TERMINAL_V2_KEYS,
        "RECOVERY_EPOCH002_FORMAL_NODE_OUTCOME_KEYS": _OUTCOME_KEYS,
        "RECOVERY_EPOCH002_FORMAL_RESULT_COUNTS_KEYS": _COUNTS_KEYS,
        "RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODES": _NEGATIVE_CLOSED_CODES,
    },
    "runner": {
        "RECOVERY_EPOCH002_REGISTERED_NEGATIVE_NODE_IDS": (
            _NEGATIVE_NODE_IDS
        ),
    },
    "accepted": {
        "RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_SCHEMA": _SCHEMAS["accepted"],
        "RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_KEYS": _ACCEPTED_KEYS,
        "RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS": _SUCCESS_LINEAGE_KEYS,
        "RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS": (
            _PRIOR_RESERVATION_ROW_KEYS
        ),
        "RECOVERY_EPOCH002_EXTERNAL_IDENTITY_KEYS": (
            _EXTERNAL_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_PROOF_SOURCE_KEYS": _PROOF_SOURCE_KEYS,
    },
    "step": {
        "RECOVERY_EPOCH002_STEP_COMPLETION_SCHEMA": _SCHEMAS["step"],
        "RECOVERY_EPOCH002_STEP_COMPLETION_KEYS": _STEP_KEYS,
        "RECOVERY_EPOCH002_STEP_CURRENT_BINDING_KEYS": (
            _STEP_CURRENT_BINDING_KEYS
        ),
        "RECOVERY_EPOCH002_STEP_LINEAGE_KEYS": _STEP_LINEAGE_KEYS,
        "RECOVERY_EPOCH002_STEP_ACTUAL_OWNER_KEYS": _ACTUAL_OWNER_KEYS,
        "RECOVERY_EPOCH002_STEP_STRICT_CONTRACT_KEYS": (
            _STRICT_CONTRACT_KEYS
        ),
        "RECOVERY_EPOCH002_STEP_ARTIFACT_RECEIPT_KEYS": (
            _ARTIFACT_RECEIPT_KEYS
        ),
        "RECOVERY_EPOCH002_STEP_PARENT_BINDING_KEYS": (
            _PARENT_BINDING_KEYS
        ),
        "RECOVERY_EPOCH002_STEP_COMPLETION_CONDITION_KEYS": (
            _COMPLETION_CONDITION_KEYS
        ),
        "RECOVERY_EPOCH002_STEP_STOP_CONDITION_KEYS": (
            _STOP_CONDITION_KEYS
        ),
    },
    "all11": {
        "RECOVERY_EPOCH002_ALL11_COMPLETION_SCHEMA": _SCHEMAS["all11"],
        "RECOVERY_EPOCH002_ALL11_COMPLETION_KEYS": _ALL11_KEYS,
        "RECOVERY_EPOCH002_ALL11_REQUIRED_EVENT2_KEYS": (
            _REQUIRED_EVENT2_KEYS
        ),
        "RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS": (
            _CANDIDATE_IDENTITY_KEYS
        ),
    },
    "publication": {
        "RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_SCHEMA": (
            _SCHEMAS["atomic_manifest"]
        ),
        "RECOVERY_EPOCH002_ATOMIC_SUCCESS_MANIFEST_KEYS": (
            _ATOMIC_MANIFEST_KEYS
        ),
        "RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS": (
            _CANDIDATE_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS": _EXTERNAL_IDENTITY_KEYS,
        "RECOVERY_EPOCH002_SUCCESS_PATHS": _SUCCESS_PATHS,
        "RECOVERY_EPOCH002_SUCCESS_CORE_PATHS": _CORE_PATHS,
        "RECOVERY_EPOCH002_EVENT2_SUPPORTING_PATHS": (
            _EVENT2_SUPPORTING_PATHS
        ),
        "RECOVERY_EPOCH002_SUCCESS_CHANGED_PATHS": (
            _SUCCESS_CHANGED_PATHS
        ),
        "RECOVERY_EPOCH002_PUBLICATION_ROLES": (
            _POST_D2_SINGLE_PUBLICATION_ROLES
        ),
    },
    "single_publication": {
        "RECOVERY_EPOCH002_PUBLICATION_ROLES": (
            _POST_D2_SINGLE_PUBLICATION_ROLES
        ),
        "RECOVERY_EPOCH002_SUCCESSOR_COMPLETION_PATH": (
            _SUCCESSOR_COMPLETION_PATH
        ),
        "RECOVERY_EPOCH002_OPERATIONAL_ADMISSION_PATH": (
            _OPERATIONAL_ADMISSION_PATH
        ),
    },
    "independent": {
        "RECOVERY_EPOCH002_SHARED_PRIMITIVE_ALLOWLIST": (
            _SHARED_PRIMITIVE_ALLOWLIST
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE": (
            _PARENT_ADDENDUM_RECEIPT_ROLE
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA": (
            _PARENT_ADDENDUM_RECEIPT_SCHEMA
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH": (
            _PARENT_ADDENDUM_RECEIPT_PATH
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS": (
            _EXTERNAL_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256": (
            _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        ),
        "RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS": (
            _PARENT_ADDENDUM_CHANGED_PATHS
        ),
    },
    "parent": {
        "RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER": _PHASE_ORDER,
        "RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES": (
            _EXECUTABLE_PHASES
        ),
        "RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES": _EXTERNAL_PORTS,
        "RECOVERY_EPOCH002_FORMAL_PARENT_TERMINAL_INPUT_TAGS": (
            frozenset(
                {
                    "VALID_TERMINAL_RESULT",
                    "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
                }
            )
        ),
        "RECOVERY_EPOCH002_FORMAL_PARENT_VALID_TERMINAL_INPUT_KEYS": (
            _PARENT_VALID_TERMINAL_INPUT_KEYS
        ),
        "RECOVERY_EPOCH002_FORMAL_PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS": (
            _PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS
        ),
        "RECOVERY_EPOCH002_FORMAL_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS": (
            _PARENT_SUCCESS_ARTIFACT_COUNT_KEYS
        ),
    },
}

_PERMANENT_PROTECTED_SHA256 = {
    _HISTORICAL_D1_PATH: (
        "70d6db7fe3e9f42c59a01fdba5e73752ba6aa1e7c2c4e6d7bf2581dbd5090ce5"
    ),
    _ROLE_PATHS["preflight_owner"]: (
        "4b0bab51f295e67ba081d4abe9fa2567ae0589514d2429a64c6903c7ded61495"
    ),
    _ROLE_PATHS["reproducible_dependency_lock"]: (
        "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
    ),
}

# Entry identities are frozen as S1 evidence.  They are deliberately not
# runtime assertions because the separately approved S2 must modify these
# exact paths while the same causal test bytes turn GREEN.
_S1_MUTABLE_PROTECTED_SHA256 = {
    _ROLE_PATHS["bootstrap_closure_owner"]: (
        "29471406e4a1c0e93603aaecdaccc328bd1e6cab89e91b5ad41f4e6091f80480"
    ),
    _ROLE_PATHS["sequence_lineage_owner"]: (
        "dc8a1d8e964a02db2d042ba71955170f5b65832c497a79d21c580dfbd00bc347"
    ),
    _ROLE_PATHS["terminal_result_owner"]: (
        "4f2bb7fe28b7172266ffd7953aa518eccad28c95754daabf3d40c6fede854384"
    ),
    _ROLE_PATHS["formal_worker_owner"]: (
        "17fcb514bf9b9a41380da8fddab1101e498467f04d887cad50bf3d0f2a648b8e"
    ),
    _ROLE_PATHS["formal_parent_owner"]: (
        "6dbf685939678f7497b52d6a422a7515ae79d3be490bb6646705bd3969f9a886"
    ),
    _ROLE_PATHS["publication_owner"]: (
        "f854b29a81f16b52a42fd235b95550edfd178fd1f4eb3aafe7e0ded102f7da2c"
    ),
    _ROLE_PATHS["independent_verifier"]: (
        "4ae8b8078b25343f06819da6baae5c9586d5031453c6def5bd2f4927f130306f"
    ),
}
_S1_INDEPENDENT_NEGATIVE_SHA256 = dict(
    zip(
        (
            row["independent_negative_proof"]["source_path"]
            for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
        ),
        (
            "ae977c994fe463a505a1cb2fd1372be6625d3317b180932f6f3417610b76ea2d",
            "3429b6f4959daadda6cf9cbb8dc457117e423664cdf84c366373f29c9b46f57f",
            "1bf1afa067c671aaca0ba3126dc12c1137fee6463c7461b3c28bc3c24439c05b",
            "d96c4188f8d57eede7b5529c963288b7f246e03b5ff4e2f4422ad0d327d8e465",
            "ae1f4be4e87b493f6996de53da5ba3eb5ce2852b2b0ddb731dc4198457bdfdeb",
            "aebda07c80a48c4a75360c841087dd09fb74b4f5ebda640765257df4badd5331",
            "31f961cd5cad09638acf4e8c15a8ead8362a478afab844dab2049359a5658089",
            "cc308d6f86caf9b140c990d5abbe0c14e010827bf41465a0d3833d482b150ce4",
            "db74c86e45eb1448d8d2142b5b028f3fc846e5bc5806ec24b05cae47223cd9cd",
            "59d5b126be1ae95d6d4b2d3590c754210d010e1da1ae52e07ed13395754c5101",
            "a17e8a7b65e085f322d32271d131c705f9bda346cd9a183f972d024ea12183a9",
        ),
        strict=True,
    )
)

_CASES = (
    ("C01", "HISTORICAL_D2_IMMUTABLE", "closure", "HISTORICAL_D2_REWRITE_FORBIDDEN"),
    ("C02", "SUCCESSOR_CLOSURE_EXACT20", "closure", "SUCCESSOR_SOURCE_CLOSURE_INVALID"),
    ("C03", "FINAL_SOURCE_COMMIT_TREE_BOUND", "closure", "SUCCESSOR_SOURCE_IDENTITY_MISMATCH"),
    ("C04", "D2_CLOSURE_ANCESTOR_BOUND", "closure", "HISTORICAL_D2_ANCESTRY_INVALID"),
    ("C05", "D2_RECEIPT_IDENTITY_BOUND", "closure", "HISTORICAL_D2_RECEIPT_BINDING_INVALID"),
    ("C06", "PARENT_ADDENDUM_IDENTITY_BOUND", "closure", "PARENT_ADDENDUM_BINDING_INVALID"),
    ("C07", "SUCCESS_OWNER_GRAPH_EXACT15_ROLE12_PATH", "closure", "SUCCESS_OWNER_GRAPH_INVALID"),
    ("C08", "SUCCESS_CONTRACT_TEST_MANIFEST_BOUND", "closure", "SUCCESS_CONTRACT_TEST_MANIFEST_BINDING_INVALID"),
    ("C09", "COMPLETION_RECEIPT_RED_GREEN_BOUND", "sequence", "SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID"),
    ("C10", "ALLOCATION_EVENT1_OWNER_AUTHORITY_AND_CURRENT_REFLECTION_CONTRACT", "sequence", "SUCCESSOR_OPERATIONAL_SUCCESSION_INVALID"),
    ("T01", "TERMINAL_V2_EXACT32", "terminal", "TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED"),
    ("T02", "COLLECTION_EXACT134_REGISTRY_ORDER", "terminal", "TERMINAL_COLLECTION_ORDER_INVALID"),
    ("T03", "EXECUTION_EXACT134_REGISTRY_ORDER", "terminal", "TERMINAL_EXECUTION_ORDER_INVALID"),
    ("T04", "OUTCOME_ROW_EXACT8", "terminal", "TERMINAL_OUTCOME_EVIDENCE_INVALID"),
    ("T05", "PINNED_SOURCE_IDENTITY_PER_NODE", "terminal", "TERMINAL_SOURCE_IDENTITY_MISMATCH"),
    ("T06", "EXPECTED_CLOSED_CODE_EXACT11", "terminal", "TERMINAL_EXPECTED_CLOSED_CODE_MISMATCH"),
    ("T07", "ACTUAL_CLOSED_CODE_OBSERVED_EXACT11", "runner", "TERMINAL_ACTUAL_CLOSED_CODE_NOT_OBSERVED"),
    ("T08", "COUNTS_EXACT10_STATES_PARITY", "terminal", "TERMINAL_COUNTS_STATE_PARITY_INVALID"),
    ("T09", "TERMINAL_SUCCESS_PREDICATE_EXACT", "terminal", "TERMINAL_SUCCESS_PREDICATE_NOT_PROVED"),
    ("T10", "TERMINAL_TARGET_CONTENT_POSTVERIFIED", "terminal", "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP"),
    ("A01", "POSTVERIFIED_TERMINAL_REQUIRED", "accepted", "POSTVERIFIED_TERMINAL_REQUIRED"),
    ("A02", "TERMINAL_ALL_SUCCESS_ONLY", "accepted", "TERMINAL_ALL_SUCCESS_REQUIRED"),
    ("A03", "FORMAL_INVOCATION_EXACT1", "accepted", "FORMAL_INVOCATION_EXACT1_REQUIRED"),
    ("A04", "SOURCE_RUNTIME_BOOTSTRAP_PARITY", "accepted", "SOURCE_RUNTIME_BOOTSTRAP_PARITY_INVALID"),
    ("A05", "EVENT_READINESS_RESERVATION_PARITY", "accepted", "EVENT_READINESS_RESERVATION_PARITY_INVALID"),
    ("A06", "COMPLETE_RETRY_HISTORY_BOUND", "accepted", "SUCCESS_LINEAGE_INVALID"),
    ("A07", "ACCEPTED_BODY_FREE_SELF_HASH", "accepted", "ACCEPTED_TEST_RUN_RECEIPT_INVALID"),
    ("A08", "UNCERTAINTY_ACCEPTED_EXACT0", "accepted", "ACCEPTED_RECEIPT_FORBIDDEN_UNDER_UNCERTAINTY"),
    ("R01", "ACCEPTED_RECEIPT_REQUIRED", "step", "ACCEPTED_TEST_RUN_RECEIPT_REQUIRED"),
    ("R02", "STEP_RECEIPT_EXACT11_ORDERED", "step", "STEP_RECEIPT_CHAIN_INVALID"),
    ("R03", "STEP00_EVENT1_ACCEPTED_BIND", "step", "STEP00_PARENT_BINDING_INVALID"),
    ("R04", "STEP01_10_IMMEDIATE_PARENT_CHAIN", "step", "STEP_PARENT_CHAIN_INVALID"),
    ("R05", "CURRENT_SOURCE_VIEW_ROOT_BIND", "step", "CURRENT_SOURCE_VIEW_ROOT_INVALID"),
    ("R06", "ACTUAL_OWNER_STRICT_CONTRACT_BIND", "step", "STEP_OWNER_CONTRACT_BINDING_INVALID"),
    ("R07", "POSITIVE_PROOF_OUTCOME_BIND", "step", "POSITIVE_PROOF_OUTCOME_BINDING_INVALID"),
    ("R08", "NEGATIVE_PROOF_OBSERVED_CODE_BIND", "step", "NEGATIVE_PROOF_OBSERVED_CODE_BINDING_INVALID"),
    ("R09", "ALL11_ACCEPTED_AND_EXACT11_BIND", "all11", "ALL11_COMPLETION_CHAIN_INVALID"),
    ("R10", "NO_EPOCH001_CREDIT_BACKFILL_OR_P2", "all11", "EPOCH001_CREDIT_BACKFILL_OR_P2_FORBIDDEN"),
    ("B01", "SUCCESS_PATHS_EXACT15_ABSENT_AT_T", "publication", "SUCCESS_PATH_ALREADY_EXISTS_AT_T"),
    ("B02", "CORE_ARTIFACTS_EXACT13", "publication", "SUCCESS_CORE_ARTIFACT_SET_INVALID"),
    ("B03", "SUPPORTING_ARTIFACTS_EXACT14", "event2", "EVENT2_SUPPORTING_ARTIFACT_SET_INVALID"),
    ("B04", "MANIFEST_CORE_SET_HASH", "publication", "ATOMIC_MANIFEST_CORE_SET_HASH_INVALID"),
    ("B05", "EVENT2_SUPPORT_SET_HASH", "event2", "EVENT2_SUPPORTING_ARTIFACT_SET_HASH_INVALID"),
    ("B06", "EVENT2_EVENT1_ANCESTRY", "event2", "EVENT2_EVENT1_ANCESTRY_INVALID"),
    ("B07", "EVENT2_TERMINAL_SUCCESS_LINEAGE", "event2", "EVENT2_TERMINAL_SUCCESS_LINEAGE_INVALID"),
    ("B08", "MULTIPLE_WRITE_OPERATIONS_ALLOWED", "publication", "SUCCESS_PUBLICATION_POSTFETCH_INVALID"),
    ("B09", "NONCONFLICTING_HEAD_DRIFT_ALLOWED", "publication", "SUCCESS_PUBLICATION_POSTFETCH_INVALID"),
    ("B10", "SPECIAL_TRANSPORT_NON_NORMATIVE", "publication", "SUCCESS_PUBLICATION_POSTFETCH_INVALID"),
    ("B11", "TARGET_SCOPED_POSTVERIFY", "publication", "SUCCESS_PUBLICATION_POSTFETCH_INVALID"),
    ("B12", "UNKNOWN_RESULT_REFETCH_BEFORE_RETRY", "publication", "SUCCESS_PUBLICATION_UNKNOWN_RESULT_RECONCILIATION_STOP"),
    ("I01", "VERIFIER_OWNER_IMPORT_SPLIT", "independent", "VERIFIER_OWNER_IMPORT_FORBIDDEN"),
    ("I02", "TERMINAL_SCHEMA_INDEPENDENT", "independent", "INDEPENDENT_TERMINAL_SCHEMA_INVALID"),
    ("I03", "ACCEPTED_STEP_ALL11_INDEPENDENT", "independent", "INDEPENDENT_SUCCESS_RECEIPT_INVALID"),
    ("I04", "EVENT2_EXACT14_15_INDEPENDENT", "independent", "INDEPENDENT_EVENT2_ATOMIC_CARDINALITY_INVALID"),
    ("I05", "TARGET_BYTES_HASHES_AND_SCOPE_INDEPENDENT", "independent", "INDEPENDENT_GIT_GRAPH_BYTES_HASH_INVALID"),
    ("I06", "OWNER_VERIFIER_DISAGREEMENT_STOP", "independent", "OWNER_VERIFIER_DISAGREEMENT_STOP"),
    ("P01", "FORMAL_PARENT_PHASE_ORDER_EXACT9", "parent", "FORMAL_PARENT_PHASE_ORDER_INVALID"),
    ("P02", "EXECUTABLE_PHASES_EXACT7", "parent", "FORMAL_PARENT_EXECUTABLE_PHASE_SET_INVALID"),
    ("P03", "EXTERNAL_PORTS_EXACT7", "parent", "FORMAL_PARENT_EXTERNAL_PORT_SET_INVALID"),
    ("P04", "ONE_PORT_CALL_NO_AUTOPROGRESSION", "parent", "FORMAL_PARENT_PHASE_EXECUTION_INVALID"),
    ("P05", "FAILURE_TERMINAL_PUBLICATION_STOP", "parent", "FAILURE_TERMINAL_SUCCESS_PUBLICATION_FORBIDDEN"),
    ("P06", "UNKNOWN_DISPOSITION_NO_RERUN", "parent", "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"),
    ("P07", "SUCCESS_TERMINAL_THEN_EXACT15_ONLY", "parent", "SUCCESS_EXACT15_PHASE_REQUIRED"),
    ("P08", "EVENT2_POSTVERIFY_STEP_PROVED_P2_STOP", "parent", "P2_SEPARATE_APPROVAL_REQUIRED"),
)
_CASE_BY_ID = {row[0]: row for row in _CASES}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _git_head_tree() -> tuple[str, str]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    return commit, tree


@lru_cache(maxsize=1)
def _canonical_current_closure() -> dict[str, Any]:
    return fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT
    )


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _canonical_raw_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(dict(value)) + b"\n"


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(
        header + payload,
        usedforsecurity=False,
    ).hexdigest()


def _source_file_identity(relative: str) -> dict[str, str]:
    payload = (_REPO_ROOT / relative).read_bytes()
    return {
        "path": relative,
        "git_blob_sha1": _git_blob_sha1(payload),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _proof_source_identity(relative: str) -> dict[str, str]:
    identity = _source_file_identity(relative)
    return {
        "path": identity["path"],
        "git_blob_sha1": identity["git_blob_sha1"],
        "sha256": identity["raw_sha256"],
    }


def _source_paths_for_formal_nodes() -> tuple[str, ...]:
    return tuple(
        sorted({node_id.partition("::")[0] for node_id in _FORMAL_NODE_IDS})
    )


def _proof_sources_for_formal_nodes() -> list[dict[str, str]]:
    return [
        _proof_source_identity(path)
        for path in _source_paths_for_formal_nodes()
    ]


def _test_node_ids(relative: str) -> tuple[str, ...]:
    tree = ast.parse(
        (_REPO_ROOT / relative).read_text(encoding="utf-8"),
        filename=relative,
    )
    return tuple(
        f"{relative}::{node.name}"
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _successor_test_node_ids() -> tuple[str, ...]:
    return tuple(
        f"{_THIS_PATH}::test_{case_id.lower()}_{boundary.lower()}"
        for case_id, boundary, _role, _code in _CASES
    )


def _historical_d1_node_ids() -> tuple[str, ...]:
    concrete = _test_node_ids(_HISTORICAL_D1_PATH)
    assert len(concrete) == 5
    parameterized = concrete[-1]
    case_ids = (
        *(f"L{number:02d}" for number in range(1, 19)),
        *(f"B{number:02d}" for number in range(1, 25)),
    )
    return (
        *concrete[:4],
        *(f"{parameterized}[{case_id}]" for case_id in case_ids),
    )


def _success_contract_node_ids() -> tuple[str, ...]:
    return (
        *_historical_d1_node_ids(),
        *_successor_test_node_ids(),
    )


def _candidate_identity(
    *,
    artifact_role: str,
    path: str,
    artifact: Mapping[str, Any],
    logical_hash_key: str,
) -> dict[str, Any]:
    assert artifact.get("body_free") is True
    assert artifact.get(logical_hash_key) == _hash_without(
        artifact,
        logical_hash_key,
    )
    payload = _canonical_raw_bytes(artifact)
    return {
        "artifact_role": artifact_role,
        "schema_version": artifact["schema_version"],
        "repository_full_name": "MassyuRed/Cocolon",
        "path": path,
        "git_blob_sha1": _git_blob_sha1(payload),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "logical_artifact_sha256": artifact[logical_hash_key],
        "body_free": True,
    }


def _external_identity_from_candidate(
    candidate: Mapping[str, Any],
    *,
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


def _single_artifact_postfetch(
    identity: Mapping[str, Any],
    *,
    base_commit_sha1: str,
    base_tree_sha1: str = "b" * 40,
    target_tree_sha1: str = "c" * 40,
) -> dict[str, Any]:
    """Build a complete synthetic exact1 publication observation."""

    artifact = {
        "path": identity["path"],
        "git_blob_sha1": identity["git_blob_sha1"],
        "raw_sha256": identity["raw_sha256"],
        "logical_artifact_sha256": identity[
            "logical_artifact_sha256"
        ],
        "body_free": identity["body_free"],
    }
    unchanged_path_observation = {
        "scope": "ALL_PATHS_EXCEPT_EXACT1_TARGET",
        "mode_type_sha_complete": True,
        "mismatches": [],
    }
    unchanged_path_observation["observation_sha256"] = artifact_sha256(
        unchanged_path_observation
    )
    return {
        "repository_full_name": identity["repository_full_name"],
        "verification_ref": "refs/heads/main",
        "verification_commit_sha1": identity["publication_commit_sha1"],
        "authoritative_ref_read": True,
        "authoritative_base_tree_read": True,
        "base_tree_sha1": base_tree_sha1,
        "target_tree_sha1": target_tree_sha1,
        "publication_commit_sha1": identity["publication_commit_sha1"],
        "publication_reachable_from_verification_ref": True,
        "publication_parent_commit_sha1s": [base_commit_sha1],
        "publication_changed_paths": [identity["path"]],
        "target_absent_at_base": True,
        "semantic_ancestor_verified": True,
        "target_tree_build_count": 1,
        "publication_commit_parent_count": 1,
        "requested_expected_old_sha1": base_commit_sha1,
        "observed_old_sha1": base_commit_sha1,
        "server_side_expected_old_applied": True,
        "authoritative_head_read": True,
        "authoritative_parent_read": True,
        "authoritative_tree_read": True,
        "authoritative_recursive_tree_read": True,
        "changed_path_proof_complete": True,
        "artifact_at_publication": artifact,
        "artifact_at_verification_ref": deepcopy(artifact),
        "unchanged_path_observation": unchanged_path_observation,
        "unchanged_path_mismatches": [],
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "postfetch_state": "POSTVERIFIED",
    }


_DELETE_MUTATION = "__DELETE_EXACT1_POSTFETCH_FIELD__"
_WRONG_SINGLE_PARENT_MUTATION = "__WRONG_EXACT1_SINGLE_PARENT__"
_COMPLETE_EXACT1_POSTFETCH_MUTATIONS: tuple[
    tuple[tuple[str, ...], Any],
    ...,
] = (
    (("authoritative_ref_read",), _DELETE_MUTATION),
    (("authoritative_head_read",), _DELETE_MUTATION),
    (("artifact_at_verification_ref",), _DELETE_MUTATION),
    (("repository_full_name",), "Other/Repository"),
    (("verification_ref",), "refs/heads/other"),
    (("verification_commit_sha1",), "not-a-sha1"),
    (("authoritative_ref_read",), False),
    (("publication_changed_paths",), ["forbidden/extra.json"]),
    (("target_absent_at_base",), False),
    (("authoritative_head_read",), False),
    (
        ("artifact_at_verification_ref", "path"),
        "forbidden/other.json",
    ),
    (("artifact_at_verification_ref", "git_blob_sha1"), "f" * 40),
    (("artifact_at_verification_ref", "raw_sha256"), "f" * 64),
    (
        ("artifact_at_verification_ref", "logical_artifact_sha256"),
        "f" * 64,
    ),
    (("artifact_at_verification_ref", "body_free"), False),
    (("owner_issue_codes",), ["OWNER_ISSUE"]),
    (("independent_issue_codes",), ["INDEPENDENT_ISSUE"]),
    (("postfetch_state",), "UNKNOWN"),
)


def _mutate_complete_exact1_postfetch(
    evidence: dict[str, Any],
    mutation_path: tuple[str, ...],
    value: Any,
) -> None:
    target = evidence
    for key in mutation_path[:-1]:
        target = target[key]
    final_key = mutation_path[-1]
    if value == _DELETE_MUTATION:
        target.pop(final_key)
    else:
        if value == _WRONG_SINGLE_PARENT_MUTATION:
            current_parent = target[final_key][0]
            replacement = [
                "0" * 40
                if current_parent != "0" * 40
                else "1" * 40
            ]
        else:
            replacement = deepcopy(value)
        if target.get(final_key) == replacement:
            current = target[final_key]
            if type(current) is bool:
                replacement = not current
            elif type(current) is str and len(current) in {40, 64}:
                replacement = (
                    "0" * len(current)
                    if current != "0" * len(current)
                    else "1" * len(current)
                )
            elif type(current) is list:
                replacement = [*current, "DIFFERENT_VALUE"]
            else:
                replacement = "DIFFERENT_VALUE"
        target[final_key] = replacement
    if (
        mutation_path[0] == "unchanged_path_observation"
        and final_key != "observation_sha256"
    ):
        observation = evidence["unchanged_path_observation"]
        observation["observation_sha256"] = _hash_without(
            observation,
            "observation_sha256",
        )
        if final_key == "mismatches":
            evidence["unchanged_path_mismatches"] = deepcopy(
                observation["mismatches"]
            )


_EXTERNAL_IDENTITY_FIELD_MUTATIONS: tuple[
    tuple[str, Any],
    ...,
] = (
    ("artifact_role", "WRONG_ROLE"),
    ("schema_version", "wrong.schema.v1"),
    ("repository_full_name", "Other/Repository"),
    ("path", "forbidden/other.json"),
    ("git_blob_sha1", "f" * 40),
    ("raw_sha256", "f" * 64),
    ("logical_artifact_sha256", "f" * 64),
    ("publication_commit_sha1", "f" * 40),
    ("body_free", False),
    ("identity_sha256", "f" * 64),
)


def _mutate_external_identity_field(
    identity: dict[str, Any],
    field: str,
    value: Any,
) -> None:
    replacement = deepcopy(value)
    if identity.get(field) == replacement:
        current = identity[field]
        if type(current) is bool:
            replacement = not current
        elif type(current) is str and len(current) in {40, 64}:
            replacement = (
                "0" * len(current)
                if current != "0" * len(current)
                else "1" * len(current)
            )
        else:
            replacement = "DIFFERENT_VALUE"
    identity[field] = replacement
    if field != "identity_sha256":
        identity["identity_sha256"] = _hash_without(
            identity,
            "identity_sha256",
        )


def _exact1_publication_contract_mutations(
    baseline: Mapping[str, Any],
    publication_getter: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    logical_hash_key: str,
) -> list[dict[str, Any]]:
    """Generate current target-scoped exact1 negative observations."""

    variants: list[dict[str, Any]] = []

    def variant(
        mutator: Callable[[dict[str, Any], dict[str, Any]], None],
    ) -> None:
        row = deepcopy(baseline)
        publication = publication_getter(row)
        mutator(row, publication)
        variants.append(row)

    for field, value in (
        ("postfetch_state", "UNKNOWN"),
        ("changed_paths", ["forbidden/other.json"]),
    ):
        variant(
            lambda _row,
            publication,
            field=field,
            value=value: publication.__setitem__(
                field,
                deepcopy(value),
            )
        )
    required_publication_keys = frozenset(
        {
            "reflection_contract_version",
            "artifact",
            "identity",
            "changed_paths",
            "postfetch_evidence",
            "postfetch_state",
        }
    )
    for key in sorted(required_publication_keys):
        variant(
            lambda _row, publication, key=key: publication.pop(key)
        )
    variant(
        lambda _row, publication: publication.__setitem__(
            "unexpected_key",
            "forbidden",
        )
    )
    variant(
        lambda _row, publication: publication["artifact"].__setitem__(
            logical_hash_key,
            "f" * 64,
        )
    )

    def mutate_identity(
        _row: dict[str, Any],
        publication: dict[str, Any],
        mutation: str,
        field: str | None = None,
        value: Any = None,
    ) -> None:
        identity = publication["identity"]
        if mutation == "missing_key":
            assert field is not None
            identity.pop(field)
            if "identity_sha256" in identity:
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
        elif mutation == "extra_key":
            identity["unexpected_key"] = "forbidden"
            identity["identity_sha256"] = _hash_without(
                identity,
                "identity_sha256",
            )
        else:
            assert field is not None
            _mutate_external_identity_field(identity, field, value)

    for field in sorted(_EXTERNAL_IDENTITY_KEYS):
        variant(
            lambda row,
            publication,
            field=field: mutate_identity(
                row,
                publication,
                "missing_key",
                field,
            )
        )
    variant(
        lambda row, publication: mutate_identity(
            row,
            publication,
            "extra_key",
        )
    )
    for field, value in (
        mutation
        for mutation in _EXTERNAL_IDENTITY_FIELD_MUTATIONS
        if mutation[0] != "publication_commit_sha1"
    ):
        variant(
            lambda row,
            publication,
            field=field,
            value=value: mutate_identity(
                row,
                publication,
                "field",
                field,
                value,
            )
        )

    for mutation_path, value in _COMPLETE_EXACT1_POSTFETCH_MUTATIONS:
        variant(
            lambda _row,
            publication,
            mutation_path=mutation_path,
            value=value: _mutate_complete_exact1_postfetch(
                publication["postfetch_evidence"],
                mutation_path,
                value,
            )
        )
    return variants


def _mutate_parent_disposition_identity(
    terminal_input: dict[str, Any],
    field: str,
    value: Any,
) -> None:
    _mutate_external_identity_field(
        terminal_input["terminal_disposition_artifact"],
        field,
        value,
    )


def _historical_d2_completion_external_identity() -> dict[str, Any]:
    candidate = {
        "artifact_role": "D2_COMPLETION_RECEIPT",
        "schema_version": _HISTORICAL_D2_COMPLETION_RECEIPT_SCHEMA,
        "repository_full_name": "MassyuRed/Cocolon",
        "path": _HISTORICAL_D2_COMPLETION_RECEIPT_PATH,
        "git_blob_sha1": _HISTORICAL_D2_COMPLETION_RECEIPT_BLOB,
        "raw_sha256": _HISTORICAL_D2_COMPLETION_RECEIPT_RAW_SHA256,
        "logical_artifact_sha256": (
            _HISTORICAL_D2_COMPLETION_RECEIPT_SHA256
        ),
        "body_free": True,
    }
    return _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=(
            _HISTORICAL_D2_COMPLETION_RECEIPT_COMMIT
        ),
    )


def _parent_addendum_external_identity() -> dict[str, Any]:
    candidate = {
        "artifact_role": _PARENT_ADDENDUM_RECEIPT_ROLE,
        "schema_version": _PARENT_ADDENDUM_RECEIPT_SCHEMA,
        "repository_full_name": "MassyuRed/Cocolon",
        "path": _PARENT_ADDENDUM_RECEIPT_PATH,
        "git_blob_sha1": _PARENT_ADDENDUM_RECEIPT_BLOB,
        "raw_sha256": _PARENT_ADDENDUM_RECEIPT_RAW_SHA256,
        "logical_artifact_sha256": _PARENT_ADDENDUM_RECEIPT_SHA256,
        "body_free": True,
    }
    identity = _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=_PARENT_ADDENDUM_PUBLICATION_COMMIT,
    )
    assert (
        identity["identity_sha256"]
        == _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
    )
    return identity


def _parent_addendum_postfetch_evidence() -> dict[str, Any]:
    """Represent the corrected historical exact5 postfetch predicate.

    This is a body-free observation envelope for future owners and the
    independent verifier.  It is not an operational publication result and
    grants no authority to publish an Event1.
    """

    identity = _parent_addendum_external_identity()
    receipt_observation = {
        "path": _PARENT_ADDENDUM_RECEIPT_PATH,
        "git_blob_sha1": _PARENT_ADDENDUM_RECEIPT_BLOB,
        "raw_sha256": _PARENT_ADDENDUM_RECEIPT_RAW_SHA256,
        "raw_byte_count": 3502,
        "trailing_lf_count": 1,
        "schema_version": _PARENT_ADDENDUM_RECEIPT_SCHEMA,
        "body_free": True,
        "automatic_progression": False,
        "state": _PARENT_ADDENDUM_RECEIPT_STATE,
        "logical_artifact_sha256": _PARENT_ADDENDUM_RECEIPT_SHA256,
        "bound_markdown_path": _PARENT_ADDENDUM_DESIGN_PATH,
        "bound_markdown_raw_sha256": _PARENT_ADDENDUM_SHA256,
    }
    markdown_observation = {
        "path": _PARENT_ADDENDUM_DESIGN_PATH,
        "git_blob_sha1": _PARENT_ADDENDUM_BLOB,
        "raw_sha256": _PARENT_ADDENDUM_SHA256,
        "raw_byte_count": 91072,
    }
    return {
        "repository_full_name": "MassyuRed/Cocolon",
        "verification_ref": "refs/heads/main",
        "verification_commit_sha1": (
            _SYNTHETIC_FRESH_COCOLON_VERIFICATION_COMMIT
        ),
        "verification_commit_kind": "FRESH_AUTHORITY_REF_OBSERVATION",
        "authoritative_ref_read": True,
        "publication_commit_sha1": _PARENT_ADDENDUM_PUBLICATION_COMMIT,
        "publication_reachable_from_verification_ref": True,
        "publication_parent_commit_sha1s": [
            _PARENT_ADDENDUM_BASE_COMMIT
        ],
        "publication_changed_paths": list(
            _PARENT_ADDENDUM_CHANGED_PATHS
        ),
        "receipt_absent_at_base": True,
        "receipt_at_publication": receipt_observation,
        "markdown_at_publication": markdown_observation,
        "receipt_at_verification_ref": deepcopy(receipt_observation),
        "markdown_at_verification_ref": deepcopy(markdown_observation),
        "parent_addendum_external_identity": identity,
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "postfetch_state": "POSTVERIFIED",
    }


def _p0_external_identity() -> dict[str, Any]:
    identity = {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11.cycle001."
            "recovery_epoch002.p0_external_identity.v1"
        ),
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "parent_design": {
            "path": _P0_PARENT_DESIGN_PATH,
            "publication_commit_sha1": _P0_PARENT_DESIGN_COMMIT,
            "git_blob_sha1": _P0_PARENT_DESIGN_BLOB,
            "raw_sha256": _P0_PARENT_DESIGN_RAW_SHA256,
        },
        "receipt": {
            "path": _P0_RECEIPT_PATH,
            "publication_commit_sha1": _P0_RECEIPT_COMMIT,
            "git_blob_sha1": _P0_RECEIPT_BLOB,
            "raw_sha256": _P0_RECEIPT_RAW_SHA256,
            "logical_receipt_sha256": _P0_RECEIPT_LOGICAL_SHA256,
        },
        "p0_external_identity_sha256": "",
    }
    identity["p0_external_identity_sha256"] = hashlib.sha256(
        canonical_json_bytes(
            {
                key: value
                for key, value in identity.items()
                if key != "p0_external_identity_sha256"
            }
        )
        + b"\n"
    ).hexdigest()
    assert (
        identity["p0_external_identity_sha256"]
        == _P0_EXTERNAL_IDENTITY_SHA256
    )
    return identity


def _success_contract_manifest() -> dict[str, Any]:
    test_files = [
        _source_file_identity(path)
        for path in sorted((_HISTORICAL_D1_PATH, _THIS_PATH))
    ]
    manifest = {
        "schema_version": _SCHEMAS["success_contract_manifest"],
        "historical_node_count": 46,
        "successor_node_count": 64,
        "total_node_count": 110,
        "test_files": test_files,
        "test_files_sha256": artifact_sha256(test_files),
        "test_node_ids": list(_success_contract_node_ids()),
        "success_contract_test_manifest_sha256": "",
    }
    manifest["success_contract_test_manifest_sha256"] = _hash_without(
        manifest,
        "success_contract_test_manifest_sha256",
    )
    return manifest


def _success_owner_graph() -> dict[str, Any]:
    bindings = []
    for role, path in _ROLE_BINDINGS:
        identity = _source_file_identity(path)
        bindings.append(
            {
                "role": role,
                "path": path,
                "git_blob_sha1": identity["git_blob_sha1"],
                "raw_sha256": identity["raw_sha256"],
            }
        )
    verifier = next(
        row for row in bindings if row["role"] == "independent_verifier"
    )
    graph = {
        "schema_version": _SCHEMAS["success_owner_graph"],
        "owner_role_count": 15,
        "owner_path_count": 12,
        "owner_role_bindings": bindings,
        "independent_verifier_constraints": {
            "verifier_path": verifier["path"],
            "verifier_git_blob_sha1": verifier["git_blob_sha1"],
            "verifier_raw_sha256": verifier["raw_sha256"],
            "forbidden_owner_import_count": 0,
            "shared_primitive_allowlist": list(
                _SHARED_PRIMITIVE_ALLOWLIST
            ),
        },
        "success_owner_graph_sha256": "",
    }
    graph["success_owner_graph_sha256"] = _hash_without(
        graph,
        "success_owner_graph_sha256",
    )
    return graph


def _bootstrap_v2() -> dict[str, Any]:
    source_commit, source_tree = _git_head_tree()
    owner_graph = _success_owner_graph()
    formal_manifest = [
        _source_file_identity(path)
        for path in _source_paths_for_formal_nodes()
    ]
    dependency_lock_path = (
        _REPO_ROOT / _ROLE_PATHS["reproducible_dependency_lock"]
    )
    dependency_lock = json.loads(
        dependency_lock_path.read_text(encoding="utf-8")
    )
    installed_distributions = [
        {
            "normalized_distribution_name": row[
                "normalized_distribution_name"
            ],
            "distribution_version": row["distribution_version"],
            "wheel_sha256": row["wheel_sha256"],
            "installed_record_closure_sha256": row[
                "installed_record_closure_sha256"
            ],
        }
        for row in dependency_lock["distributions"]
    ]
    installed_by_name = {
        row["normalized_distribution_name"]: row
        for row in installed_distributions
    }
    python_runtime_identity = {
        "executable_sha256": "3" * 64,
        "implementation": "CPYTHON",
        "version": "3.12.13",
        "build_sha256": "4" * 64,
    }
    runtime_identity_sha256 = artifact_sha256(python_runtime_identity)
    formal_owner_path = formal_manifest[0]["path"]
    artifact_contract_path = (
        "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py"
    )
    artifact_contract_identity = _source_file_identity(
        artifact_contract_path
    )
    import_manifest = [
        {
            "import_name": "emlis_ai_nls_v3_artifact_contract",
            "classification": "FIRST_PARTY",
            "owner_paths": [formal_owner_path],
            "target_identity": artifact_contract_identity,
        },
        {
            "import_name": "json",
            "classification": "STDLIB_BOUND_TO_PYTHON_RUNTIME",
            "owner_paths": [formal_owner_path],
            "target_identity": {
                "module_name": "json",
                "python_runtime_identity_sha256": (
                    runtime_identity_sha256
                ),
            },
        },
        {
            "import_name": "pytest",
            "classification": (
                "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION"
            ),
            "owner_paths": [formal_owner_path],
            "target_identity": {
                "module_name": "pytest",
                **installed_by_name["pytest"],
            },
        },
    ]
    environment = {
        "fixed": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
        "removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"],
        "inherited_path_sha256": "a" * 64,
        "lang": "C.UTF-8",
        "lc_all": "C.UTF-8",
    }
    preflight_argv = [
        "python",
        "-I",
        "-B",
        _ROLE_PATHS["preflight_owner"],
        "--preflight",
    ]
    worker_argv = [
        "python",
        "-I",
        "-B",
        _ROLE_PATHS["formal_worker_owner"],
        "--internal-exact134-child",
        "-q",
        "--disable-warnings",
        "--noconftest",
        "-p",
        "no:cacheprovider",
    ]
    manifest = {
        "schema_version": _SCHEMAS["bootstrap_v2"],
        "source_commit_sha1": source_commit,
        "source_tree_sha1": source_tree,
        "formal_owner_artifacts": deepcopy(
            owner_graph["owner_role_bindings"]
        ),
        "formal_owner_artifacts_sha256": artifact_sha256(
            owner_graph["owner_role_bindings"]
        ),
        "formal_test_node_ids": list(_FORMAL_NODE_IDS),
        "formal_test_manifest": formal_manifest,
        "formal_test_manifest_sha256": artifact_sha256(formal_manifest),
        "conftest_plugin_mode": "DISABLED_BY_NOCONFTEST",
        "pytest_plugins_environment_variable_removed": True,
        "pytest_entrypoint_autoload_disabled": True,
        "explicit_plugin_allowlist": [],
        "loaded_plugin_manifest": [],
        "loaded_plugin_manifest_sha256": artifact_sha256([]),
        "import_manifest": import_manifest,
        "import_manifest_sha256": artifact_sha256(import_manifest),
        "dependency_lock_identity": {
            "identity_class": "PIP_REQUIRE_HASHES_WHEEL_LOCK_V1",
            "path": _ROLE_PATHS["reproducible_dependency_lock"],
            "raw_sha256": hashlib.sha256(
                dependency_lock_path.read_bytes()
            ).hexdigest(),
        },
        "installed_distributions": installed_distributions,
        "installed_distributions_sha256": artifact_sha256(
            installed_distributions
        ),
        "python_runtime_identity": python_runtime_identity,
        "pytest_distribution_identity": installed_by_name["pytest"],
        "environment_profile": environment,
        "environment_profile_sha256": artifact_sha256(environment),
        "preflight_argv": preflight_argv,
        "preflight_argv_sha256": artifact_sha256(preflight_argv),
        "formal_worker_argv": worker_argv,
        "formal_worker_argv_sha256": artifact_sha256(worker_argv),
        "unclassified_import_count": 0,
        "unresolved_dynamic_import_count": 0,
        "body_free": True,
        "bootstrap_closure_sha256": "",
    }
    manifest["bootstrap_closure_sha256"] = _hash_without(
        manifest,
        "bootstrap_closure_sha256",
    )
    return manifest


def _successor_source_closure() -> dict[str, Any]:
    source_commit, source_tree = _git_head_tree()
    canonical = _canonical_current_closure()
    bootstrap = _bootstrap_v2()
    graph = _success_owner_graph()
    contract = _success_contract_manifest()
    proof_sources = _proof_sources_for_formal_nodes()
    closure = {
        "schema_version": _SCHEMAS["successor_closure"],
        "repository_full_name": "MassyuRed/mashos-api",
        "source_ref": "refs/heads/main",
        "source_commit_sha1": source_commit,
        "source_tree_sha1": source_tree,
        "worktree_clean": True,
        "detailed_design_sha256": (
            "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
        ),
        "parent_addendum_external_identity_sha256": (
            _parent_addendum_external_identity()["identity_sha256"]
        ),
        "historical_d2_final_closure_sha256": (
            _HISTORICAL_D2_FINAL_CLOSURE_SHA256
        ),
        "historical_d2_completion_receipt_identity_sha256": (
            _historical_d2_completion_external_identity()[
                "identity_sha256"
            ]
        ),
        "source_dependency_closure_sha256": canonical[
            "source_dependency_closure_sha256"
        ],
        "canonical_current_closure_sha256": canonical[
            "canonical_current_closure_sha256"
        ],
        "requirement_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
        ),
        "formal_node_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "proof_source_closure_sha256": artifact_sha256(proof_sources),
        "formal_test_manifest_sha256": (
            bootstrap["formal_test_manifest_sha256"]
        ),
        "bootstrap_closure_sha256": (
            bootstrap["bootstrap_closure_sha256"]
        ),
        "success_owner_graph_sha256": (
            graph["success_owner_graph_sha256"]
        ),
        "success_contract_test_manifest_sha256": (
            contract["success_contract_test_manifest_sha256"]
        ),
        "source_closure_sha256": "",
    }
    closure["source_closure_sha256"] = _hash_without(
        closure,
        "source_closure_sha256",
    )
    return closure


def _closure_state() -> dict[str, Any]:
    source_closure = _successor_source_closure()
    bootstrap = _bootstrap_v2()
    owner_graph = _success_owner_graph()
    contract_manifest = _success_contract_manifest()
    return {
        "historical_d2_rewrite_requested": False,
        "successor_source_closure": source_closure,
        "bootstrap_closure": bootstrap,
        "success_owner_graph": owner_graph,
        "success_contract_test_manifest": contract_manifest,
        "source_observation": {
            "source_commit_sha1": source_closure["source_commit_sha1"],
            "source_tree_sha1": source_closure["source_tree_sha1"],
            "worktree_clean": True,
        },
        "historical_d2_ancestry": {
            "source_commit_sha1": "3" * 40,
            "source_tree_sha1": "4" * 40,
            "final_closure_sha256": _HISTORICAL_D2_FINAL_CLOSURE_SHA256,
            "verified_ancestor": True,
        },
        "historical_d2_completion_receipt": (
            _historical_d2_completion_external_identity()
        ),
        "parent_addendum_external_identity": (
            _parent_addendum_external_identity()
        ),
        "parent_addendum_postfetch_evidence": (
            _parent_addendum_postfetch_evidence()
        ),
    }


def _successor_completion_fixture() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    closure = _successor_source_closure()
    contract = _success_contract_manifest()
    causal_red_artifact = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "post_d2_successor_red_result.v1"
        ),
        "authority_token": _AUTHORITY,
        "source_entry_commit_sha1": _MASHOS_API_ENTRY,
        "source_entry_tree_sha1": _MASHOS_API_ENTRY_TREE,
        "successor_test_file": _source_file_identity(_THIS_PATH),
        "successor_node_count": 64,
        "collected": 64,
        "failed": 64,
        "passed": 0,
        "collection_errors": 0,
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "state": "SUCCESSOR_CAUSAL_RED_FROZEN",
        "automatic_progression": False,
        "body_free": True,
        "receipt_sha256": "",
    }
    causal_red_artifact["receipt_sha256"] = _hash_without(
        causal_red_artifact,
        "receipt_sha256",
    )
    causal_red_candidate = _candidate_identity(
        artifact_role="SUCCESSOR_CAUSAL_RED_RESULT",
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
            "Successor_RED_Result_20260726.json"
        ),
        artifact=causal_red_artifact,
        logical_hash_key="receipt_sha256",
    )
    causal_red_identity = _external_identity_from_candidate(
        causal_red_candidate,
        publication_commit_sha1="a" * 40,
    )
    contract_node_ids = list(_success_contract_node_ids())
    combined_green_artifact = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "post_d2_successor_targeted_green_result.v1"
        ),
        "causal_red_evidence_sha256": causal_red_identity[
            "logical_artifact_sha256"
        ],
        "successor_source_commit_sha1": closure["source_commit_sha1"],
        "successor_source_tree_sha1": closure["source_tree_sha1"],
        "successor_source_closure_sha256": closure[
            "source_closure_sha256"
        ],
        "success_contract_test_manifest_sha256": contract[
            "success_contract_test_manifest_sha256"
        ],
        "test_node_ids": contract_node_ids,
        "executed_node_ids": list(contract_node_ids),
        "outcome_states": {
            node_id: "PASSED" for node_id in contract_node_ids
        },
        "counts": {
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
        },
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "state": "SUCCESSOR_TARGETED_GREEN_COMPLETED",
        "automatic_progression": False,
        "body_free": True,
        "receipt_sha256": "",
    }
    combined_green_artifact["receipt_sha256"] = _hash_without(
        combined_green_artifact,
        "receipt_sha256",
    )
    combined_green_candidate = _candidate_identity(
        artifact_role="SUCCESSOR_COMBINED_GREEN_RESULT",
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2_"
            "Successor_GREEN_Result_20260726.json"
        ),
        artifact=combined_green_artifact,
        logical_hash_key="receipt_sha256",
    )
    combined_green_identity = _external_identity_from_candidate(
        combined_green_candidate,
        publication_commit_sha1="b" * 40,
    )
    completion = {
        "schema_version": _SCHEMAS["successor_completion"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "historical_d2_final_closure_sha256": (
            _HISTORICAL_D2_FINAL_CLOSURE_SHA256
        ),
        "historical_d2_completion_receipt_identity_sha256": (
            _historical_d2_completion_external_identity()[
                "identity_sha256"
            ]
        ),
        "parent_addendum_external_identity_sha256": (
            _parent_addendum_external_identity()["identity_sha256"]
        ),
        "successor_source_closure_sha256": (
            closure["source_closure_sha256"]
        ),
        "causal_red_evidence_sha256": (
            causal_red_identity["logical_artifact_sha256"]
        ),
        "combined_green_evidence_sha256": (
            combined_green_identity["logical_artifact_sha256"]
        ),
        "state": "SUCCESSOR_SOURCE_BASELINE_ELIGIBILITY_PROVED",
        "automatic_progression": False,
        "body_free": True,
        "receipt_sha256": "",
    }
    completion["receipt_sha256"] = _hash_without(
        completion,
        "receipt_sha256",
    )
    return (
        completion,
        causal_red_artifact,
        causal_red_identity,
        combined_green_artifact,
        combined_green_identity,
    )


def _transaction_capability(
    *,
    base_commit_sha1: str,
    expected_changed_path_count: int,
    challenge_id: str,
    admission_identity_sha256: str,
    observed_at_utc: str,
) -> dict[str, Any]:
    """Build a legacy optional diagnostic fixture, not current canonical input."""

    transaction = {
        "schema_version": _SCHEMAS["transaction_capability"],
        "provider_class": "EXPECTED_OLD_CAS_CAPABLE_GITHUB_TRANSPORT",
        "provider_identity_sha256": "c" * 64,
        "repository_full_name": "MassyuRed/Cocolon",
        "source_ref": "refs/heads/main",
        "base_commit_sha1": base_commit_sha1,
        "expected_changed_path_count": expected_changed_path_count,
        "authoritative_ref_read": True,
        "expected_old_compare_and_swap": True,
        "commit_parent_tree_and_recursive_read": True,
        "full_changed_and_unchanged_postfetch_verification": True,
        "challenge_id": challenge_id,
        "operational_admission_identity_sha256": (
            admission_identity_sha256
        ),
        "observed_at_utc": observed_at_utc,
        "transaction_capability_sha256": "",
    }
    transaction["transaction_capability_sha256"] = _hash_without(
        transaction,
        "transaction_capability_sha256",
    )
    return transaction


def _operational_admission_fixture(
    *,
    completion_identity: Mapping[str, Any],
    source_closure: Mapping[str, Any],
) -> dict[str, Any]:
    authority = {
        "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
        "admission_authority_token": _FUTURE_P1_AUTHORITY_TOKEN,
        "publication_authority_token": _FUTURE_P1_AUTHORITY_TOKEN,
        "authority_sha256": "",
    }
    authority["authority_sha256"] = _hash_without(
        authority,
        "authority_sha256",
    )
    scope = {
        "repository_full_name": "MassyuRed/Cocolon",
        "source_ref": "refs/heads/main",
        "successor_source_closure_sha256": (
            source_closure["source_closure_sha256"]
        ),
        "operation_set": list(_ADMISSION_OPERATION_SET),
        "scope_sha256": "",
    }
    scope["scope_sha256"] = _hash_without(scope, "scope_sha256")
    admission = {
        "schema_version": _SCHEMAS["operational_admission"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "successor_completion_receipt": dict(completion_identity),
        "successor_source_closure_sha256": (
            source_closure["source_closure_sha256"]
        ),
        "repository_full_name": "MassyuRed/Cocolon",
        "source_ref": "refs/heads/main",
        "authority": authority,
        "challenge_id": "d" * 64,
        "scope": scope,
        "owner_validation_state": "PROVED",
        "independent_verification_state": "PROVED",
        "issued_at_utc": "2026-07-26T12:01:00Z",
        "expires_at_utc": "2026-07-26T12:30:00Z",
        "state": "P1_OPERATIONAL_ADMISSION_PROVED",
        "automatic_progression": False,
        "body_free": True,
        "operational_admission_sha256": "",
    }
    admission["operational_admission_sha256"] = _hash_without(
        admission,
        "operational_admission_sha256",
    )
    return admission


def _candidate_allocation_fixture(
    *,
    source_closure: Mapping[str, Any],
    completion_identity: Mapping[str, Any],
) -> dict[str, Any]:
    d2_receipt = _historical_d2_completion_external_identity()
    allocation = {
        "schema_version": _SCHEMAS["candidate_v2"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": "nls_v3_rc_epoch002_success_0001",
        "historical_d2_final_closure_sha256": (
            _HISTORICAL_D2_FINAL_CLOSURE_SHA256
        ),
        "historical_d2_completion_receipt": d2_receipt,
        "successor_source_closure_sha256": (
            source_closure["source_closure_sha256"]
        ),
        "successor_completion_receipt": dict(completion_identity),
        "allocated_at_utc": "2026-07-26T12:02:00Z",
        "candidate_allocation_sha256": "",
    }
    allocation["candidate_allocation_sha256"] = _hash_without(
        allocation,
        "candidate_allocation_sha256",
    )
    return allocation


def _event1_fixture(
    *,
    source_closure: Mapping[str, Any],
    bootstrap_closure: Mapping[str, Any],
    completion_identity: Mapping[str, Any],
    admission_identity: Mapping[str, Any],
    candidate_allocation: Mapping[str, Any],
) -> dict[str, Any]:
    p0_identity = _p0_external_identity()
    challenge = "1" * 64
    publication = {
        "repository_full_name": "MassyuRed/Cocolon",
        "branch": "main",
        "base_commit_sha1": "4" * 40,
        "event_path": _EVENT1_PATH,
        "supporting_artifact_count": 1,
        "supporting_artifacts": [dict(completion_identity)],
        "supporting_artifact_set_sha256": artifact_sha256(
            [dict(completion_identity)]
        ),
        "expected_changed_path_count": 1,
        "publication_state": "PUBLISHED_ATOMIC",
    }
    event = {
        "schema_version": _SCHEMAS["event_v2"],
        "ledger_id": "recovery_epoch002_sequence",
        "event_id": "recovery_epoch002_event_01",
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": candidate_allocation[
            "candidate_version_id"
        ],
        "event_name": "SOURCE_BASELINE_LOCKED",
        "event_ordinal": 1,
        "state": "SOURCE_BASELINE_LOCKED",
        "timestamp_utc": "2026-07-26T12:03:00Z",
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": _FUTURE_P1_AUTHORITY_TOKEN,
            "publication_authority_token": _FUTURE_P1_AUTHORITY_TOKEN,
            "operational_admission": dict(admission_identity),
        },
        "challenge_id": challenge,
        "source_closure": dict(source_closure),
        "prior_event": p0_identity,
        "primary_evidence_artifact": dict(completion_identity),
        "publication": publication,
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
        "p0_external_identity": p0_identity,
        "candidate_allocation": dict(candidate_allocation),
        "bootstrap_closure": dict(bootstrap_closure),
    }
    event["event_sha256"] = _hash_without(event, "event_sha256")
    return event


def _sequence_state() -> dict[str, Any]:
    source_closure = _successor_source_closure()
    bootstrap = _bootstrap_v2()
    (
        completion,
        causal_red_artifact,
        causal_red_identity,
        combined_green_artifact,
        combined_green_identity,
    ) = _successor_completion_fixture()
    completion_candidate = _candidate_identity(
        artifact_role="SUCCESSOR_COMPLETION_RECEIPT",
        path=_SUCCESSOR_COMPLETION_PATH,
        artifact=completion,
        logical_hash_key="receipt_sha256",
    )
    completion_identity = _external_identity_from_candidate(
        completion_candidate,
        publication_commit_sha1="3" * 40,
    )
    admission = _operational_admission_fixture(
        completion_identity=completion_identity,
        source_closure=source_closure,
    )
    admission_candidate = _candidate_identity(
        artifact_role="P1_OPERATIONAL_ADMISSION_RECEIPT",
        path=_OPERATIONAL_ADMISSION_PATH,
        artifact=admission,
        logical_hash_key="operational_admission_sha256",
    )
    admission_identity = _external_identity_from_candidate(
        admission_candidate,
        publication_commit_sha1="4" * 40,
    )
    allocation = _candidate_allocation_fixture(
        source_closure=source_closure,
        completion_identity=completion_identity,
    )
    event1 = _event1_fixture(
        source_closure=source_closure,
        bootstrap_closure=bootstrap,
        completion_identity=completion_identity,
        admission_identity=admission_identity,
        candidate_allocation=allocation,
    )
    event1_candidate = _candidate_identity(
        artifact_role="SOURCE_BASELINE_EVENT",
        path=_EVENT1_PATH,
        artifact=event1,
        logical_hash_key="event_sha256",
    )
    event1_identity = _external_identity_from_candidate(
        event1_candidate,
        publication_commit_sha1="5" * 40,
    )
    return {
        "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
        "successor_source_closure": source_closure,
        "bootstrap_closure": bootstrap,
        "parent_addendum_external_identity": (
            _parent_addendum_external_identity()
        ),
        "parent_addendum_postfetch_evidence": (
            _parent_addendum_postfetch_evidence()
        ),
        "successor_completion_receipt": completion,
        "causal_red_evidence_artifact": causal_red_artifact,
        "causal_red_evidence": causal_red_identity,
        "causal_red_postfetch_evidence": _single_artifact_postfetch(
            causal_red_identity,
            base_commit_sha1="9" * 40,
        ),
        "combined_green_evidence_artifact": combined_green_artifact,
        "combined_green_evidence": combined_green_identity,
        "combined_green_postfetch_evidence": _single_artifact_postfetch(
            combined_green_identity,
            base_commit_sha1="a" * 40,
            base_tree_sha1="c" * 40,
            target_tree_sha1="d" * 40,
        ),
        "successor_completion_publication": {
            "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
            "artifact": completion,
            "identity": completion_identity,
            "changed_paths": [_SUCCESSOR_COMPLETION_PATH],
            "parent_commit_sha1s": ["2" * 40],
            "expected_old_sha1": "2" * 40,
            "observed_old_sha1": "2" * 40,
            "postfetch_evidence": _single_artifact_postfetch(
                completion_identity,
                base_commit_sha1="2" * 40,
            ),
            "postfetch_state": "POSTVERIFIED",
        },
        "operational_admission_receipt": admission,
        "operational_admission_publication": {
            "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
            "artifact": admission,
            "identity": admission_identity,
            "changed_paths": [_OPERATIONAL_ADMISSION_PATH],
            "parent_commit_sha1s": ["3" * 40],
            "expected_old_sha1": "3" * 40,
            "observed_old_sha1": "3" * 40,
            "postfetch_evidence": _single_artifact_postfetch(
                admission_identity,
                base_commit_sha1="3" * 40,
                base_tree_sha1="c" * 40,
                target_tree_sha1="d" * 40,
            ),
            "postfetch_state": "POSTVERIFIED",
        },
        "candidate_allocation": allocation,
        "event1": event1,
        "event1_publication": {
            "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
            "artifact": event1,
            "identity": event1_identity,
            "changed_paths": [_EVENT1_PATH],
            "parent_commit_sha1s": ["4" * 40],
            "expected_old_sha1": "4" * 40,
            "observed_old_sha1": "4" * 40,
            "postfetch_evidence": _single_artifact_postfetch(
                event1_identity,
                base_commit_sha1="4" * 40,
                base_tree_sha1="d" * 40,
                target_tree_sha1="e" * 40,
            ),
            "postfetch_state": "POSTVERIFIED",
        },
        "candidate_operational_identity": {
            "candidate_version_id": allocation["candidate_version_id"],
            "event1_identity_sha256": event1_identity["identity_sha256"],
        },
    }


def _single_publication_state() -> dict[str, Any]:
    sequence = _sequence_state()
    return {
        "supported_roles": sorted(_POST_D2_SINGLE_PUBLICATION_ROLES),
        "additive_role_paths": {
            "SUCCESSOR_COMPLETION_RECEIPT": _SUCCESSOR_COMPLETION_PATH,
            "P1_OPERATIONAL_ADMISSION_RECEIPT": _OPERATIONAL_ADMISSION_PATH,
        },
        "exact1_transactions": [
            {
                "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
                "artifact_role": "SUCCESSOR_COMPLETION_RECEIPT",
                "path": _SUCCESSOR_COMPLETION_PATH,
                "expected_changed_paths": [_SUCCESSOR_COMPLETION_PATH],
                "parent_commit_sha1s": ["2" * 40],
                "expected_old_sha1": "2" * 40,
                "requested_expected_old_sha1": "2" * 40,
                "observed_old_sha1": "2" * 40,
                "head_commit_sha1": "3" * 40,
                "target_absent_at_base": True,
                "unchanged_path_mismatches": [],
                "owner_issue_codes": [],
                "independent_issue_codes": [],
                "postfetch_state": "POSTVERIFIED",
                "publication": deepcopy(
                    sequence["successor_completion_publication"]
                ),
            },
            {
                "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
                "artifact_role": "P1_OPERATIONAL_ADMISSION_RECEIPT",
                "path": _OPERATIONAL_ADMISSION_PATH,
                "expected_changed_paths": [_OPERATIONAL_ADMISSION_PATH],
                "parent_commit_sha1s": ["3" * 40],
                "expected_old_sha1": "3" * 40,
                "requested_expected_old_sha1": "3" * 40,
                "observed_old_sha1": "3" * 40,
                "head_commit_sha1": "4" * 40,
                "target_absent_at_base": True,
                "unchanged_path_mismatches": [],
                "owner_issue_codes": [],
                "independent_issue_codes": [],
                "postfetch_state": "POSTVERIFIED",
                "publication": deepcopy(
                    sequence["operational_admission_publication"]
                ),
            },
        ],
    }


def _formal_checkpoint_chain(
    terminal: Mapping[str, Any],
    *,
    reservation_ordinal: int = 2,
    preflight_challenge_id: str = "0" * 64,
    preflight_id: str = "f" * 64,
    attempt_minute: int | None = None,
) -> list[dict[str, Any]]:
    stages = (
        "PARENT_SPAWN_INTENT_PERSISTED",
        "CHILD_PROCESS_ENTRY",
        "SOURCE_BINDING_VALIDATED",
        "RUNTIME_PROFILE_VALIDATED",
        "PYTEST_IMPORT_VALIDATED",
        "FORMAL_PLUGIN_BOOTSTRAP_VALIDATED",
        "PYTEST_MAIN_ENTERING",
        "COLLECTION_STARTED",
        "COLLECTION_FINISHED",
        "EXECUTION_STARTED",
        "EXECUTION_FINISHED",
        "TERMINAL_RESULT_PERSISTED",
    )
    if attempt_minute is None:
        observed_times = (
            "2026-07-26T12:09:50Z",
            "2026-07-26T12:09:51Z",
            "2026-07-26T12:09:52Z",
            "2026-07-26T12:09:53Z",
            "2026-07-26T12:09:54Z",
            "2026-07-26T12:09:55Z",
            "2026-07-26T12:10:00Z",
            "2026-07-26T12:10:01Z",
            "2026-07-26T12:10:10Z",
            "2026-07-26T12:10:11Z",
            "2026-07-26T12:11:59Z",
            "2026-07-26T12:12:00Z",
        )
    else:
        observed_times = tuple(
            (
                f"2026-07-26T12:{attempt_minute:02d}:"
                f"{10 + index:02d}Z"
            )
            for index in range(len(stages))
        )
    stages_and_times = tuple(zip(stages, observed_times, strict=True))
    checkpoints: list[dict[str, Any]] = []
    prior: str | None = None
    for ordinal, (stage, observed_at) in enumerate(
        stages_and_times,
        start=1,
    ):
        checkpoint = {
            "schema_version": (
                "cocolon.emlis.nls_v3.recovery_epoch002."
                "formal_worker_checkpoint.v1"
            ),
            "phase": "FORMAL_RUN",
            "logical_cycle_id": terminal["logical_cycle_id"],
            "recovery_epoch_id": terminal["recovery_epoch_id"],
            "authority_token_id": terminal["authority_token_id"],
            "event1_challenge_id": terminal["event1_challenge_id"],
            "preflight_challenge_id": preflight_challenge_id,
            "formal_run_challenge_id": terminal[
                "formal_run_challenge_id"
            ],
            "formal_authority_challenge_id": terminal[
                "formal_authority_challenge_id"
            ],
            "preflight_id": preflight_id,
            "attempt_id": terminal["attempt_id"],
            "reservation_ordinal": reservation_ordinal,
            "formal_test_run_reservation_sha256": terminal[
                "formal_test_run_reservation_sha256"
            ],
            "candidate_version_id": terminal["candidate_version_id"],
            "source_baseline_event_sha256": terminal[
                "source_baseline_event_sha256"
            ],
            "source_closure_sha256": terminal[
                "source_closure_sha256"
            ],
            "bootstrap_closure_sha256": terminal[
                "bootstrap_closure_sha256"
            ],
            "checkpoint_ordinal": ordinal,
            "stage_enum": stage,
            "observed_at_utc": observed_at,
            "prior_checkpoint_sha256": prior,
            "body_free": True,
            "checkpoint_sha256": "",
        }
        checkpoint["checkpoint_sha256"] = _hash_without(
            checkpoint,
            "checkpoint_sha256",
        )
        checkpoints.append(checkpoint)
        prior = checkpoint["checkpoint_sha256"]
    return checkpoints


def _terminal_state() -> dict[str, Any]:
    source_identities = {
        row["path"]: row
        for row in (
            _source_file_identity(path)
            for path in _source_paths_for_formal_nodes()
        )
    }
    observations = dict(_OBSERVED_NEGATIVE_CLOSED_CODE_BY_NODE)
    outcomes = []
    for node_id in _FORMAL_NODE_IDS:
        source_path = node_id.partition("::")[0]
        source = source_identities[source_path]
        expected = _NEGATIVE_CLOSED_CODE_BY_NODE.get(node_id)
        outcome = {
            "test_node_id": node_id,
            "source_path": source_path,
            "source_blob_sha1": source["git_blob_sha1"],
            "source_sha256": source["raw_sha256"],
            "result": "PASSED",
            "expected_closed_code": expected,
            "actual_closed_code": observations.get(node_id),
            "evidence_sha256": "",
        }
        outcome["evidence_sha256"] = _hash_without(
            outcome,
            "evidence_sha256",
        )
        outcomes.append(outcome)
    states = {node_id: "PASSED" for node_id in _FORMAL_NODE_IDS}
    counts = {
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
    terminal = {
        "schema_version": _SCHEMAS["terminal_v2"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "authority_token_id": "1" * 64,
        "event1_challenge_id": "2" * 64,
        "formal_run_challenge_id": "3" * 64,
        "formal_authority_challenge_id": "4" * 64,
        "attempt_id": "5" * 64,
        "candidate_version_id": "nls_v3_rc_epoch002_success_0001",
        "source_baseline_event_sha256": "6" * 64,
        "source_closure_sha256": "7" * 64,
        "bootstrap_closure_sha256": "8" * 64,
        "formal_test_run_reservation_sha256": "9" * 64,
        "terminal_checkpoint_sha256": "",
        "collection_node_ids": list(_FORMAL_NODE_IDS),
        "executed_node_ids": list(_FORMAL_NODE_IDS),
        "states": states,
        "collection_errors": 0,
        "exit_class": "EXITED",
        "exit_code": 0,
        "signal_number": None,
        "timed_out": False,
        "python_runtime_identity_sha256": "b" * 64,
        "pytest_distribution_identity_sha256": "c" * 64,
        "started_at_utc": "2026-07-26T12:10:00Z",
        "finished_at_utc": "2026-07-26T12:12:00Z",
        "body_free": True,
        "formal_worker_result_sha256": "",
        "outcomes": outcomes,
        "counts": counts,
        "formal_node_outcome_evidence_sha256": artifact_sha256(outcomes),
        "formal_exact134_invocation_count": 1,
    }
    checkpoints = _formal_checkpoint_chain(terminal)
    terminal["terminal_checkpoint_sha256"] = checkpoints[-1][
        "checkpoint_sha256"
    ]
    terminal["formal_worker_result_sha256"] = _hash_without(
        terminal,
        "formal_worker_result_sha256",
    )
    terminal_candidate = _candidate_identity(
        artifact_role="FORMAL_WORKER_TERMINAL_RESULT",
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_FormalWorker_"
            "Attempt05_TerminalResult_20260726.json"
        ),
        artifact=terminal,
        logical_hash_key="formal_worker_result_sha256",
    )
    terminal_identity = _external_identity_from_candidate(
        terminal_candidate,
        publication_commit_sha1="e" * 40,
    )
    return {
        "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
        "terminal_result": terminal,
        "locked_formal_node_ids": list(_FORMAL_NODE_IDS),
        "locked_negative_code_by_node": dict(
            _NEGATIVE_CLOSED_CODE_BY_NODE
        ),
        "locked_source_manifest": [
            source_identities[path]
            for path in sorted(source_identities)
        ],
        "runner_closed_code_observations": observations,
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "checkpoint_chain": checkpoints,
        "retry_history": {
            "successful_reservation_ordinal": 2,
            "consumed_attempt_ids": ["d" * 64],
            "successful_attempt_id": terminal["attempt_id"],
        },
        "parity_bindings": {
            "source_closure_sha256": terminal["source_closure_sha256"],
            "bootstrap_closure_sha256": terminal[
                "bootstrap_closure_sha256"
            ],
            "event1_candidate_version_id": terminal[
                "candidate_version_id"
            ],
            "readiness_candidate_version_id": terminal[
                "candidate_version_id"
            ],
            "reservation_candidate_version_id": terminal[
                "candidate_version_id"
            ],
            "python_runtime_identity_sha256": terminal[
                "python_runtime_identity_sha256"
            ],
            "pytest_distribution_identity_sha256": terminal[
                "pytest_distribution_identity_sha256"
            ],
        },
        "terminal_publication": {
            "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
            "artifact": deepcopy(terminal),
            "identity": terminal_identity,
            "changed_paths": [terminal_candidate["path"]],
            "parent_commit_sha1s": ["d" * 40],
            "expected_old_sha1": "d" * 40,
            "observed_old_sha1": "d" * 40,
            "postfetch_evidence": _single_artifact_postfetch(
                terminal_identity,
                base_commit_sha1="d" * 40,
            ),
            "postfetch_state": "POSTVERIFIED",
        },
    }


def _rehash_terminal_state(state: dict[str, Any]) -> None:
    terminal = state["terminal_result"]
    for outcome in terminal.get("outcomes", []):
        if type(outcome) is dict and "evidence_sha256" in outcome:
            outcome["evidence_sha256"] = _hash_without(
                outcome,
                "evidence_sha256",
            )
    terminal["formal_node_outcome_evidence_sha256"] = artifact_sha256(
        terminal.get("outcomes", [])
    )
    terminal["formal_worker_result_sha256"] = _hash_without(
        terminal,
        "formal_worker_result_sha256",
    )
    publication = state.get("terminal_publication")
    if type(publication) is dict:
        old_postfetch = publication["postfetch_evidence"]
        publication["artifact"] = deepcopy(terminal)
        candidate = _candidate_identity(
            artifact_role="FORMAL_WORKER_TERMINAL_RESULT",
            path=publication["identity"]["path"],
            artifact=terminal,
            logical_hash_key="formal_worker_result_sha256",
        )
        publication["identity"] = _external_identity_from_candidate(
            candidate,
            publication_commit_sha1=publication["identity"][
                "publication_commit_sha1"
            ],
        )
        publication["postfetch_evidence"] = _single_artifact_postfetch(
            publication["identity"],
            base_commit_sha1=publication["parent_commit_sha1s"][0],
            base_tree_sha1=old_postfetch["base_tree_sha1"],
            target_tree_sha1=old_postfetch["target_tree_sha1"],
        )


def _canonical_step_view_sha256_by_step(
    source_closure: Mapping[str, Any],
) -> dict[str, str]:
    """Reuse the existing canonical closure's frozen Step-view meaning."""

    closure = _canonical_current_closure()
    assert closure["canonical_current_closure_sha256"] == (
        source_closure["canonical_current_closure_sha256"]
    )
    assert closure["source_dependency_closure_sha256"] == (
        source_closure["source_dependency_closure_sha256"]
    )
    return {
        str(step): artifact_sha256(
            closure["step_views"][f"step_{step}"]
        )
        for step in range(11)
    }


def _strict_artifact_external_identity(
    *,
    artifact_role: str,
    path: str,
    artifact: Mapping[str, Any],
    logical_hash_key: str,
    publication_commit_sha1: str,
) -> dict[str, Any]:
    """Derive exact10 only from a strict artifact's canonical bytes."""

    expected_hash_keys = {
        (
            "BOOTSTRAP_READINESS",
            _SCHEMAS["readiness"],
        ): "bootstrap_readiness_receipt_sha256",
        (
            "FORMAL_TEST_RUN_RESERVATION",
            (
                "cocolon.emlis.nls_v3.recovery_epoch002."
                "formal_test_run_reservation.v1"
            ),
        ): "formal_test_run_reservation_sha256",
        (
            "FORMAL_WORKER_TERMINAL_RESULT",
            _SCHEMAS["terminal_v2"],
        ): "formal_worker_result_sha256",
        (
            "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
            _SCHEMAS["unknown_disposition"],
        ): "attempt_consumption_unknown_disposition_sha256",
        (
            "SOURCE_BASELINE_EVENT",
            _SCHEMAS["event_v2"],
        ): "event_sha256",
    }
    assert expected_hash_keys[
        (artifact_role, artifact["schema_version"])
    ] == logical_hash_key
    assert artifact[logical_hash_key] == _hash_without(
        artifact,
        logical_hash_key,
    )
    candidate = _candidate_identity(
        artifact_role=artifact_role,
        path=path,
        artifact=artifact,
        logical_hash_key=logical_hash_key,
    )
    return _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=publication_commit_sha1,
    )


def _readiness_preflight_id(
    readiness: Mapping[str, Any],
) -> str:
    return artifact_sha256(
        {
            "logical_cycle_id": readiness["logical_cycle_id"],
            "recovery_epoch_id": readiness["recovery_epoch_id"],
            "candidate_version_id": readiness["candidate_version_id"],
            "authority_token": readiness["authority_token"],
            "event1_challenge_id": readiness["event1_challenge_id"],
            "preflight_challenge_id": readiness[
                "preflight_challenge_id"
            ],
            "source_baseline_event_identity_sha256": readiness[
                "source_baseline_event"
            ]["identity_sha256"],
            "source_closure_sha256": readiness["source_closure"][
                "source_closure_sha256"
            ],
            "bootstrap_closure_sha256": readiness[
                "bootstrap_closure"
            ]["bootstrap_closure_sha256"],
        }
    )


def _readiness_artifact_fixture(
    sequence: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_closure = deepcopy(sequence["successor_source_closure"])
    bootstrap = deepcopy(sequence["bootstrap_closure"])
    event = sequence["event1"]
    event_identity = sequence["event1_publication"]["identity"]
    owner_row = next(
        row
        for row in bootstrap["formal_owner_artifacts"]
        if row["role"] == "preflight_owner"
    )
    authority_token = _FUTURE_P1_AUTHORITY_TOKEN
    preflight_challenge_id = "0" * 64
    readiness = {
        "schema_version": _SCHEMAS["readiness"],
        "authority_token": authority_token,
        "event1_challenge_id": event["challenge_id"],
        "preflight_challenge_id": preflight_challenge_id,
        "preflight_id": "",
        "candidate_version_id": event["candidate_version_id"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "source_baseline_event": deepcopy(event_identity),
        "source_closure": source_closure,
        "bootstrap_closure": bootstrap,
        "python_runtime_identity": deepcopy(
            bootstrap["python_runtime_identity"]
        ),
        "pytest_distribution_identity": deepcopy(
            bootstrap["pytest_distribution_identity"]
        ),
        "dependency_lock_identity": deepcopy(
            bootstrap["dependency_lock_identity"]
        ),
        "environment_profile": deepcopy(
            bootstrap["environment_profile"]
        ),
        "preflight_owner_identity": {
            "path": owner_row["path"],
            "git_blob_sha1": owner_row["git_blob_sha1"],
            "raw_sha256": owner_row["raw_sha256"],
        },
        "preflight_argv_sha256": bootstrap["preflight_argv_sha256"],
        "loaded_plugin_manifest_sha256": bootstrap[
            "loaded_plugin_manifest_sha256"
        ],
        "readiness_state": "READY_FOR_EXACT_ONE_FORMAL_SPAWN",
        "formal_collection_state": "NOT_STARTED",
        "formal_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "preflight_started_at_utc": "2026-07-26T12:04:00Z",
        "preflight_finished_at_utc": "2026-07-26T12:05:00Z",
        "readiness_receipt_path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
            "BootstrapReadiness_BodyFree_20260726.json"
        ),
        "automatic_progression": False,
        "body_free": True,
        "bootstrap_readiness_receipt_sha256": "",
    }
    readiness["preflight_id"] = _readiness_preflight_id(readiness)
    assert set(readiness) == _READINESS_KEYS
    readiness["bootstrap_readiness_receipt_sha256"] = _hash_without(
        readiness,
        "bootstrap_readiness_receipt_sha256",
    )
    identity = _strict_artifact_external_identity(
        artifact_role="BOOTSTRAP_READINESS",
        path=readiness["readiness_receipt_path"],
        artifact=readiness,
        logical_hash_key="bootstrap_readiness_receipt_sha256",
        publication_commit_sha1="6" * 40,
    )
    return readiness, identity


def _current_published_artifact_state() -> dict[str, Any]:
    """Build a current target-scoped postverify observation."""

    readiness, identity = _readiness_artifact_fixture(_sequence_state())
    path = identity["path"]
    return {
        "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
        "artifact_role": "BOOTSTRAP_READINESS",
        "artifact": readiness,
        "artifact_external_identity": identity,
        "receipt_contains_self_commit_blob_or_raw_identity": False,
        "changed_paths": [path],
        "expected_changed_paths": [path],
        "path_preexisted": False,
        "postfetch_succeeded": True,
        "postfetch_matches_candidate": True,
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "reservation_write_outcome": "NOT_ATTEMPTED",
        "authoritative_reservation_presence": "ABSENT",
        "ready_receipt_marked_consumed": False,
        "fabricated_reservation_detected": False,
        "postfetch_commit_sha1": "f" * 40,
        "postfetch_git_blob_sha1": identity["git_blob_sha1"],
    }


def _reservation_attempt_id(
    reservation: Mapping[str, Any],
) -> str:
    source_closure = reservation["source_closure"]
    event_identity = reservation["source_baseline_event"]
    readiness_identity = reservation["bootstrap_readiness_artifact"]
    return artifact_sha256(
        {
            "logical_cycle_id": reservation["logical_cycle_id"],
            "recovery_epoch_id": reservation["recovery_epoch_id"],
            "candidate_version_id": reservation["candidate_version_id"],
            "authority_token": reservation["authority_token"],
            "challenge_id": reservation["challenge_id"],
            "authority_challenge_id": reservation[
                "authority_challenge_id"
            ],
            "source_baseline_event_sha256": event_identity[
                "logical_artifact_sha256"
            ],
            "source_baseline_event_identity_sha256": event_identity[
                "identity_sha256"
            ],
            "canonical_current_closure_sha256": source_closure[
                "canonical_current_closure_sha256"
            ],
            "source_dependency_closure_sha256": source_closure[
                "source_dependency_closure_sha256"
            ],
            "proof_source_closure_sha256": source_closure[
                "proof_source_closure_sha256"
            ],
            "requirement_registry_sha256": source_closure[
                "requirement_registry_sha256"
            ],
            "formal_node_registry_sha256": source_closure[
                "formal_node_registry_sha256"
            ],
            "bootstrap_closure_sha256": source_closure[
                "bootstrap_closure_sha256"
            ],
            "bootstrap_readiness_identity_sha256": readiness_identity[
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
    )


def _reservation_artifact_fixture(
    *,
    sequence: Mapping[str, Any],
    readiness_artifact: Mapping[str, Any],
    readiness_identity: Mapping[str, Any],
    prior_history: list[dict[str, Any]],
    reservation_ordinal: int,
    publication_base_commit_sha1: str,
    publication_commit_sha1: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    assert reservation_ordinal == len(prior_history) + 1
    assert all(
        set(row) == _PRIOR_RESERVATION_ROW_KEYS
        for row in prior_history
    )
    event = sequence["event1"]
    event_identity = sequence["event1_publication"]["identity"]
    source_closure = deepcopy(sequence["successor_source_closure"])
    candidate_version_id = event["candidate_version_id"]
    authority_token = (
        f"{_FUTURE_P1_AUTHORITY_TOKEN}_RESERVATION_"
        f"{reservation_ordinal:02d}"
    )
    challenge_id = hashlib.sha256(
        f"reservation-challenge-{reservation_ordinal}".encode("utf-8")
    ).hexdigest()
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": authority_token,
            "challenge_id": challenge_id,
        }
    )
    history = deepcopy(prior_history)
    history_sha256 = artifact_sha256(
        {"prior_reservation_history": history}
    )
    if not history:
        lineage_state = "INITIAL"
    elif history[-1][
        "disposition_kind"
    ] == "FORMAL_FAILURE_ATTEMPT_PUBLISHED":
        lineage_state = "RETRY_AFTER_PUBLISHED_FORMAL_FAILURE"
    else:
        lineage_state = (
            "RETRY_AFTER_PUBLISHED_CONSUMPTION_UNKNOWN_STOP"
        )
    reservation = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "formal_test_run_reservation.v1"
        ),
        "authority_token": authority_token,
        "challenge_id": challenge_id,
        "authority_challenge_id": authority_challenge_id,
        "attempt_id": "",
        "candidate_version_id": candidate_version_id,
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "formal_node_registry_sha256": source_closure[
            "formal_node_registry_sha256"
        ],
        "reservation_state": "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN",
        "reserved_at_utc": (
            f"2026-07-26T12:{5 + reservation_ordinal:02d}:00Z"
        ),
        "source_baseline_event": deepcopy(event_identity),
        "source_closure": source_closure,
        "automatic_progression": False,
        "body_free": True,
        "formal_test_run_reservation_sha256": "",
        "reservation_ordinal": reservation_ordinal,
        "publication_base_commit_sha1": (
            publication_base_commit_sha1
        ),
        "bootstrap_readiness_artifact": deepcopy(readiness_identity),
        "prior_reservation_count": len(history),
        "prior_reservation_history": history,
        "prior_reservation_history_sha256": history_sha256,
        "lineage_state": lineage_state,
        "event1_challenge_id": event["challenge_id"],
        "preflight_challenge_id": readiness_artifact[
            "preflight_challenge_id"
        ],
    }
    reservation["attempt_id"] = _reservation_attempt_id(reservation)
    assert set(reservation) == _RESERVATION_KEYS
    reservation["formal_test_run_reservation_sha256"] = (
        _hash_without(
            reservation,
            "formal_test_run_reservation_sha256",
        )
    )
    identity = _strict_artifact_external_identity(
        artifact_role="FORMAL_TEST_RUN_RESERVATION",
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
            f"Reservation{reservation_ordinal:02d}_"
            "BodyFree_20260726.json"
        ),
        artifact=reservation,
        logical_hash_key="formal_test_run_reservation_sha256",
        publication_commit_sha1=publication_commit_sha1,
    )
    return reservation, identity


def _bind_terminal_to_reservation(
    terminal: dict[str, Any],
    *,
    readiness: Mapping[str, Any],
    reservation: Mapping[str, Any],
) -> None:
    terminal["authority_token_id"] = artifact_sha256(
        {"authority_token": reservation["authority_token"]}
    )
    terminal["event1_challenge_id"] = reservation[
        "event1_challenge_id"
    ]
    terminal["formal_run_challenge_id"] = reservation["challenge_id"]
    terminal["formal_authority_challenge_id"] = reservation[
        "authority_challenge_id"
    ]
    terminal["attempt_id"] = reservation["attempt_id"]
    terminal["candidate_version_id"] = reservation[
        "candidate_version_id"
    ]
    terminal["source_baseline_event_sha256"] = reservation[
        "source_baseline_event"
    ]["logical_artifact_sha256"]
    terminal["source_closure_sha256"] = reservation[
        "source_closure"
    ]["source_closure_sha256"]
    terminal["bootstrap_closure_sha256"] = readiness[
        "bootstrap_closure"
    ]["bootstrap_closure_sha256"]
    terminal["formal_test_run_reservation_sha256"] = reservation[
        "formal_test_run_reservation_sha256"
    ]
    terminal["python_runtime_identity_sha256"] = artifact_sha256(
        readiness["python_runtime_identity"]
    )
    terminal["pytest_distribution_identity_sha256"] = artifact_sha256(
        readiness["pytest_distribution_identity"]
    )


def _failed_terminal_artifact_fixture(
    *,
    terminal_template: Mapping[str, Any],
    readiness: Mapping[str, Any],
    reservation: Mapping[str, Any],
) -> dict[str, Any]:
    terminal = deepcopy(terminal_template)
    _bind_terminal_to_reservation(
        terminal,
        readiness=readiness,
        reservation=reservation,
    )
    failed_node = terminal["collection_node_ids"][-1]
    terminal["states"][failed_node] = "FAILED"
    terminal["outcomes"][-1]["result"] = "FAILED"
    terminal["outcomes"][-1]["evidence_sha256"] = _hash_without(
        terminal["outcomes"][-1],
        "evidence_sha256",
    )
    terminal["counts"]["passed"] = 133
    terminal["counts"]["failed"] = 1
    terminal["exit_code"] = 1
    checkpoints = _formal_checkpoint_chain(
        terminal,
        reservation_ordinal=reservation["reservation_ordinal"],
        preflight_challenge_id=readiness[
            "preflight_challenge_id"
        ],
        preflight_id=readiness["preflight_id"],
        attempt_minute=5 + reservation["reservation_ordinal"],
    )
    terminal["started_at_utc"] = checkpoints[0]["observed_at_utc"]
    terminal["finished_at_utc"] = checkpoints[-1]["observed_at_utc"]
    terminal["terminal_checkpoint_sha256"] = checkpoints[-1][
        "checkpoint_sha256"
    ]
    terminal["formal_node_outcome_evidence_sha256"] = artifact_sha256(
        terminal["outcomes"]
    )
    terminal["formal_worker_result_sha256"] = _hash_without(
        terminal,
        "formal_worker_result_sha256",
    )
    assert set(terminal) == _TERMINAL_V2_KEYS
    return terminal


def _unknown_disposition_artifact_fixture(
    *,
    reservation_identity: Mapping[str, Any],
    attempt_id: str,
) -> dict[str, Any]:
    disposition = {
        "schema_version": _SCHEMAS["unknown_disposition"],
        "reservation_artifact": deepcopy(reservation_identity),
        "attempt_id": attempt_id,
        "checkpoint_status": "ABSENT",
        "last_valid_stage": None,
        "terminal_result_status": "ABSENT",
        "exit_class": "UNKNOWN",
        "exit_code": None,
        "signal_number": None,
        "stop_code": "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "automatic_retry": False,
        "body_free": True,
        "attempt_consumption_unknown_disposition_sha256": "",
    }
    assert set(disposition) == _UNKNOWN_DISPOSITION_KEYS
    disposition[
        "attempt_consumption_unknown_disposition_sha256"
    ] = _hash_without(
        disposition,
        "attempt_consumption_unknown_disposition_sha256",
    )
    return disposition


def _accepted_state() -> dict[str, Any]:
    sequence = _sequence_state()
    terminal_state = _terminal_state()
    terminal = terminal_state["terminal_result"]
    event1 = sequence["event1"]
    event1_identity = sequence["event1_publication"]["identity"]
    terminal["candidate_version_id"] = event1["candidate_version_id"]
    terminal["event1_challenge_id"] = event1["challenge_id"]
    terminal["source_baseline_event_sha256"] = event1["event_sha256"]
    terminal["source_closure_sha256"] = sequence[
        "successor_source_closure"
    ]["source_closure_sha256"]
    terminal["bootstrap_closure_sha256"] = sequence[
        "bootstrap_closure"
    ]["bootstrap_closure_sha256"]
    readiness_artifact, readiness_identity = (
        _readiness_artifact_fixture(sequence)
    )
    prior_reservation_artifact, prior_reservation = (
        _reservation_artifact_fixture(
            sequence=sequence,
            readiness_artifact=readiness_artifact,
            readiness_identity=readiness_identity,
            prior_history=[],
            reservation_ordinal=1,
            publication_base_commit_sha1="6" * 40,
            publication_commit_sha1="7" * 40,
        )
    )
    prior_terminal_artifact = _failed_terminal_artifact_fixture(
        terminal_template=terminal,
        readiness=readiness_artifact,
        reservation=prior_reservation_artifact,
    )
    prior_disposition = _strict_artifact_external_identity(
        artifact_role="FORMAL_WORKER_TERMINAL_RESULT",
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_Attempt01_"
            "TerminalResult_20260726.json"
        ),
        artifact=prior_terminal_artifact,
        logical_hash_key="formal_worker_result_sha256",
        publication_commit_sha1="8" * 40,
    )
    history = [
        {
            "reservation_ordinal": 1,
            "reservation_artifact": prior_reservation,
            "attempt_id": prior_reservation_artifact["attempt_id"],
            "disposition_kind": "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
            "disposition_artifact": prior_disposition,
        }
    ]
    successful_reservation_artifact, successful_reservation = (
        _reservation_artifact_fixture(
            sequence=sequence,
            readiness_artifact=readiness_artifact,
            readiness_identity=readiness_identity,
            prior_history=history,
            reservation_ordinal=2,
            publication_base_commit_sha1="8" * 40,
            publication_commit_sha1="9" * 40,
        )
    )
    _bind_terminal_to_reservation(
        terminal,
        readiness=readiness_artifact,
        reservation=successful_reservation_artifact,
    )
    terminal_state["checkpoint_chain"] = _formal_checkpoint_chain(
        terminal,
        reservation_ordinal=2,
        preflight_challenge_id=readiness_artifact[
            "preflight_challenge_id"
        ],
        preflight_id=readiness_artifact["preflight_id"],
    )
    terminal["terminal_checkpoint_sha256"] = terminal_state[
        "checkpoint_chain"
    ][-1]["checkpoint_sha256"]
    terminal_state["retry_history"] = {
        "successful_reservation_ordinal": 2,
        "consumed_attempt_ids": [
            prior_reservation_artifact["attempt_id"]
        ],
        "successful_attempt_id": terminal["attempt_id"],
    }
    terminal_state["parity_bindings"] = {
        "source_closure_sha256": sequence[
            "successor_source_closure"
        ]["source_closure_sha256"],
        "bootstrap_closure_sha256": readiness_artifact[
            "bootstrap_closure"
        ]["bootstrap_closure_sha256"],
        "event1_candidate_version_id": event1["candidate_version_id"],
        "readiness_candidate_version_id": readiness_artifact[
            "candidate_version_id"
        ],
        "reservation_candidate_version_id": (
            successful_reservation_artifact["candidate_version_id"]
        ),
        "python_runtime_identity_sha256": artifact_sha256(
            readiness_artifact["python_runtime_identity"]
        ),
        "pytest_distribution_identity_sha256": artifact_sha256(
            readiness_artifact["pytest_distribution_identity"]
        ),
    }
    terminal_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_FormalWorker_"
        "Attempt02_TerminalResult_20260726.json"
    )
    terminal_state["terminal_publication"]["identity"]["path"] = (
        terminal_path
    )
    terminal_state["terminal_publication"]["changed_paths"] = [
        terminal_path
    ]
    _rehash_terminal_state(terminal_state)
    terminal_publication = terminal_state["terminal_publication"]
    terminal_publication["parent_commit_sha1s"] = ["9" * 40]
    terminal_publication["expected_old_sha1"] = "9" * 40
    terminal_publication["observed_old_sha1"] = "9" * 40
    terminal_publication["postfetch_evidence"] = (
        _single_artifact_postfetch(
            terminal_publication["identity"],
            base_commit_sha1="9" * 40,
            base_tree_sha1="2" * 40,
            target_tree_sha1="3" * 40,
        )
    )
    terminal_identity = terminal_state["terminal_publication"]["identity"]
    lineage = {
        "schema_version": _SCHEMAS["success_lineage"],
        "candidate_version_id": terminal["candidate_version_id"],
        "source_baseline_event": event1_identity,
        "successful_reservation": successful_reservation,
        "prior_reservation_count": 1,
        "prior_reservation_history": history,
        "prior_reservation_history_sha256": artifact_sha256(
            {"prior_reservation_history": history}
        ),
        "success_lineage_sha256": "",
    }
    lineage["success_lineage_sha256"] = _hash_without(
        lineage,
        "success_lineage_sha256",
    )
    outcomes = terminal["outcomes"]
    proof_sources_by_path = {
        row["source_path"]: {
            "path": row["source_path"],
            "git_blob_sha1": row["source_blob_sha1"],
            "sha256": row["source_sha256"],
        }
        for row in outcomes
    }
    proof_sources = [
        proof_sources_by_path[path]
        for path in sorted(proof_sources_by_path)
    ]
    step_views = _canonical_step_view_sha256_by_step(
        sequence["successor_source_closure"]
    )
    accepted = {
        "schema_version": _SCHEMAS["accepted"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": terminal["candidate_version_id"],
        "formal_worker_terminal_result": deepcopy(terminal),
        "formal_worker_result_sha256": terminal[
            "formal_worker_result_sha256"
        ],
        "terminal_result_artifact": deepcopy(terminal_identity),
        "success_lineage": lineage,
        "step_view_sha256_by_step": step_views,
        "proof_sources": proof_sources,
        "proof_source_closure_sha256": artifact_sha256(proof_sources),
        "owner_validation_state": "PROVED",
        "independent_verification_state": "PROVED",
        "accepted": True,
        "body_free": True,
        "automatic_progression": False,
        "accepted_test_run_receipt_sha256": "",
    }
    accepted["accepted_test_run_receipt_sha256"] = _hash_without(
        accepted,
        "accepted_test_run_receipt_sha256",
    )
    return {
        "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
        "accepted_test_run_receipt": accepted,
        "terminal_publication": terminal_state["terminal_publication"],
        "terminal_owner_state": terminal_state,
        "source_context": {
            "successor_source_closure": sequence[
                "successor_source_closure"
            ],
            "bootstrap_closure": sequence["bootstrap_closure"],
            "event1_artifact": event1,
            "event1_identity": event1_identity,
            "event1_postfetch_evidence": sequence[
                "event1_publication"
            ]["postfetch_evidence"],
            "candidate_allocation": sequence["candidate_allocation"],
            "readiness_artifact": readiness_artifact,
            "readiness_identity": readiness_identity,
            "readiness_postfetch_evidence": (
                _single_artifact_postfetch(
                    readiness_identity,
                    base_commit_sha1="5" * 40,
                    base_tree_sha1="e" * 40,
                    target_tree_sha1="f" * 40,
                )
            ),
            "successful_reservation_artifact": (
                successful_reservation_artifact
            ),
            "successful_reservation_identity": successful_reservation,
            "successful_reservation_postfetch_evidence": (
                _single_artifact_postfetch(
                    successful_reservation,
                    base_commit_sha1="8" * 40,
                    base_tree_sha1="1" * 40,
                    target_tree_sha1="2" * 40,
                )
            ),
        },
        "retry_history_observation": {
            "prior_reservation_history": deepcopy(history),
            "prior_reservation_artifacts": [
                prior_reservation_artifact
            ],
            "prior_disposition_artifacts": [
                prior_terminal_artifact
            ],
            "prior_reservation_postfetch_evidence": [
                _single_artifact_postfetch(
                    prior_reservation,
                    base_commit_sha1="6" * 40,
                    base_tree_sha1="f" * 40,
                    target_tree_sha1="0" * 40,
                )
            ],
            "prior_disposition_postfetch_evidence": [
                _single_artifact_postfetch(
                    prior_disposition,
                    base_commit_sha1="7" * 40,
                    base_tree_sha1="0" * 40,
                    target_tree_sha1="1" * 40,
                )
            ],
            "successful_reservation_ordinal": 2,
            "successful_attempt_id": terminal["attempt_id"],
        },
        "issuance_requested": True,
    }


def _rehash_accepted_state(state: dict[str, Any]) -> None:
    accepted = state["accepted_test_run_receipt"]
    terminal = accepted["formal_worker_terminal_result"]
    for outcome in terminal.get("outcomes", []):
        if type(outcome) is dict and "evidence_sha256" in outcome:
            outcome["evidence_sha256"] = _hash_without(
                outcome,
                "evidence_sha256",
            )
    terminal["formal_node_outcome_evidence_sha256"] = artifact_sha256(
        terminal.get("outcomes", [])
    )
    terminal["formal_worker_result_sha256"] = _hash_without(
        terminal,
        "formal_worker_result_sha256",
    )
    accepted["formal_worker_result_sha256"] = terminal[
        "formal_worker_result_sha256"
    ]
    terminal_publication = state["terminal_publication"]
    terminal_postfetch = terminal_publication["postfetch_evidence"]
    candidate = _candidate_identity(
        artifact_role="FORMAL_WORKER_TERMINAL_RESULT",
        path=terminal_publication["identity"]["path"],
        artifact=terminal,
        logical_hash_key="formal_worker_result_sha256",
    )
    terminal_publication["artifact"] = deepcopy(terminal)
    terminal_publication["identity"] = _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=terminal_publication["identity"][
            "publication_commit_sha1"
        ],
    )
    terminal_publication[
        "postfetch_evidence"
    ] = _single_artifact_postfetch(
        terminal_publication["identity"],
        base_commit_sha1=terminal_publication[
            "parent_commit_sha1s"
        ][0],
        base_tree_sha1=terminal_postfetch["base_tree_sha1"],
        target_tree_sha1=terminal_postfetch["target_tree_sha1"],
    )
    accepted["terminal_result_artifact"] = deepcopy(
        terminal_publication["identity"]
    )
    lineage = accepted["success_lineage"]
    lineage["prior_reservation_history_sha256"] = artifact_sha256(
        {
            "prior_reservation_history": lineage[
                "prior_reservation_history"
            ]
        }
    )
    lineage["success_lineage_sha256"] = _hash_without(
        lineage,
        "success_lineage_sha256",
    )
    accepted["accepted_test_run_receipt_sha256"] = _hash_without(
        accepted,
        "accepted_test_run_receipt_sha256",
    )


def _accepted_unknown_prior_state() -> dict[str, Any]:
    """Build the other valid append-only prior-disposition branch."""

    return _accepted_state_with_history(
        (
            "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
        )
    )


def _accepted_state_with_history(
    disposition_kinds: tuple[str, ...],
    *,
    prior_reservation_alias_ordinals: frozenset[int] = frozenset(),
    disposition_role_alias_by_ordinal: Mapping[int, str] | None = None,
    successful_reservation_role_alias: bool = False,
) -> dict[str, Any]:
    """Build valid zero/one/multi-row append-only retry histories."""

    allowed_kinds = {
        "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
    }
    assert set(disposition_kinds) <= allowed_kinds
    assert len(disposition_kinds) <= 2
    disposition_aliases = dict(
        disposition_role_alias_by_ordinal or {}
    )
    valid_ordinals = frozenset(range(1, len(disposition_kinds) + 1))
    assert prior_reservation_alias_ordinals <= valid_ordinals
    assert frozenset(disposition_aliases) <= valid_ordinals
    state = _accepted_state()
    sequence = _sequence_state()
    accepted = state["accepted_test_run_receipt"]
    lineage = accepted["success_lineage"]
    readiness_artifact = state["source_context"]["readiness_artifact"]
    readiness_identity = state["source_context"]["readiness_identity"]
    readiness_postfetch = state["source_context"][
        "readiness_postfetch_evidence"
    ]
    prior_history: list[dict[str, Any]] = []
    reservation_artifacts: list[dict[str, Any]] = []
    disposition_artifacts: list[dict[str, Any]] = []
    reservation_postfetch: list[dict[str, Any]] = []
    disposition_postfetch: list[dict[str, Any]] = []
    commit_digits = iter("789ab")
    tree_digits = iter("012345")
    previous_commit = readiness_identity["publication_commit_sha1"]
    previous_tree = readiness_postfetch["target_tree_sha1"]
    terminal_template = state["terminal_owner_state"][
        "terminal_result"
    ]

    for ordinal, disposition_kind in enumerate(
        disposition_kinds,
        start=1,
    ):
        reservation_commit = next(commit_digits) * 40
        reservation_target_tree = next(tree_digits) * 40
        reservation_artifact, reservation_identity = (
            _reservation_artifact_fixture(
                sequence=sequence,
                readiness_artifact=readiness_artifact,
                readiness_identity=readiness_identity,
                prior_history=prior_history,
                reservation_ordinal=ordinal,
                publication_base_commit_sha1=previous_commit,
                publication_commit_sha1=reservation_commit,
            )
        )
        if ordinal in prior_reservation_alias_ordinals:
            _alias_external_identity_role(
                reservation_identity,
                "RESERVATION",
            )
        reservation_artifacts.append(reservation_artifact)
        reservation_postfetch.append(
            _single_artifact_postfetch(
                reservation_identity,
                base_commit_sha1=previous_commit,
                base_tree_sha1=previous_tree,
                target_tree_sha1=reservation_target_tree,
            )
        )
        previous_commit = reservation_commit
        previous_tree = reservation_target_tree

        disposition_commit = next(commit_digits) * 40
        disposition_target_tree = next(tree_digits) * 40
        if disposition_kind == "FORMAL_FAILURE_ATTEMPT_PUBLISHED":
            disposition_artifact = _failed_terminal_artifact_fixture(
                terminal_template=terminal_template,
                readiness=readiness_artifact,
                reservation=reservation_artifact,
            )
            disposition_role = "FORMAL_WORKER_TERMINAL_RESULT"
            logical_hash_key = "formal_worker_result_sha256"
            disposition_name = "TerminalResult"
        else:
            disposition_artifact = (
                _unknown_disposition_artifact_fixture(
                    reservation_identity=reservation_identity,
                    attempt_id=reservation_artifact["attempt_id"],
                )
            )
            disposition_role = (
                "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION"
            )
            logical_hash_key = (
                "attempt_consumption_unknown_disposition_sha256"
            )
            disposition_name = "ConsumptionUnknownDisposition"
        disposition_identity = _strict_artifact_external_identity(
            artifact_role=disposition_role,
            path=(
                "EmlisAIの実装済み資料/documents/"
                "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
                f"Attempt{ordinal:02d}_{disposition_name}_"
                "20260726.json"
            ),
            artifact=disposition_artifact,
            logical_hash_key=logical_hash_key,
            publication_commit_sha1=disposition_commit,
        )
        if ordinal in disposition_aliases:
            alias_role = disposition_aliases[ordinal]
            expected_alias = (
                "TERMINAL_RESULT"
                if disposition_kind
                == "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
                else "UNKNOWN_DISPOSITION"
            )
            assert alias_role == expected_alias
            _alias_external_identity_role(
                disposition_identity,
                alias_role,
            )
        disposition_artifacts.append(disposition_artifact)
        disposition_postfetch.append(
            _single_artifact_postfetch(
                disposition_identity,
                base_commit_sha1=previous_commit,
                base_tree_sha1=previous_tree,
                target_tree_sha1=disposition_target_tree,
            )
        )
        prior_history.append(
            {
                "reservation_ordinal": ordinal,
                "reservation_artifact": reservation_identity,
                "attempt_id": reservation_artifact["attempt_id"],
                "disposition_kind": disposition_kind,
                "disposition_artifact": disposition_identity,
            }
        )
        previous_commit = disposition_commit
        previous_tree = disposition_target_tree

    successful_ordinal = len(prior_history) + 1
    successful_commit = next(commit_digits) * 40
    successful_target_tree = next(tree_digits) * 40
    successful_artifact, successful_identity = (
        _reservation_artifact_fixture(
            sequence=sequence,
            readiness_artifact=readiness_artifact,
            readiness_identity=readiness_identity,
            prior_history=prior_history,
            reservation_ordinal=successful_ordinal,
            publication_base_commit_sha1=previous_commit,
            publication_commit_sha1=successful_commit,
        )
    )
    if successful_reservation_role_alias:
        _alias_external_identity_role(
            successful_identity,
            "RESERVATION",
        )
    successful_postfetch = _single_artifact_postfetch(
        successful_identity,
        base_commit_sha1=previous_commit,
        base_tree_sha1=previous_tree,
        target_tree_sha1=successful_target_tree,
    )

    terminal_state = state["terminal_owner_state"]
    terminal = terminal_state["terminal_result"]
    _bind_terminal_to_reservation(
        terminal,
        readiness=readiness_artifact,
        reservation=successful_artifact,
    )
    checkpoints = _formal_checkpoint_chain(
        terminal,
        reservation_ordinal=successful_ordinal,
        preflight_challenge_id=readiness_artifact[
            "preflight_challenge_id"
        ],
        preflight_id=readiness_artifact["preflight_id"],
    )
    terminal["terminal_checkpoint_sha256"] = checkpoints[-1][
        "checkpoint_sha256"
    ]
    terminal_state["checkpoint_chain"] = checkpoints
    terminal_state["retry_history"] = {
        "successful_reservation_ordinal": successful_ordinal,
        "consumed_attempt_ids": [
            row["attempt_id"] for row in prior_history
        ],
        "successful_attempt_id": terminal["attempt_id"],
    }
    terminal_state["parity_bindings"] = {
        "source_closure_sha256": sequence[
            "successor_source_closure"
        ]["source_closure_sha256"],
        "bootstrap_closure_sha256": readiness_artifact[
            "bootstrap_closure"
        ]["bootstrap_closure_sha256"],
        "event1_candidate_version_id": sequence["event1"][
            "candidate_version_id"
        ],
        "readiness_candidate_version_id": readiness_artifact[
            "candidate_version_id"
        ],
        "reservation_candidate_version_id": successful_artifact[
            "candidate_version_id"
        ],
        "python_runtime_identity_sha256": artifact_sha256(
            readiness_artifact["python_runtime_identity"]
        ),
        "pytest_distribution_identity_sha256": artifact_sha256(
            readiness_artifact["pytest_distribution_identity"]
        ),
    }
    terminal_publication = state["terminal_publication"]
    terminal_target_tree = next(tree_digits) * 40
    terminal_path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_FormalWorker_"
        f"Attempt{successful_ordinal:02d}_"
        "TerminalResult_20260726.json"
    )
    terminal_publication["identity"]["path"] = terminal_path
    terminal_publication["changed_paths"] = [terminal_path]
    terminal_publication["parent_commit_sha1s"] = [successful_commit]
    terminal_publication["expected_old_sha1"] = successful_commit
    terminal_publication["observed_old_sha1"] = successful_commit
    terminal_publication["postfetch_evidence"] = (
        _single_artifact_postfetch(
            terminal_publication["identity"],
            base_commit_sha1=successful_commit,
            base_tree_sha1=successful_target_tree,
            target_tree_sha1=terminal_target_tree,
        )
    )
    _rehash_terminal_state(terminal_state)
    accepted["formal_worker_terminal_result"] = deepcopy(
        terminal_state["terminal_result"]
    )
    accepted["formal_worker_result_sha256"] = terminal_state[
        "terminal_result"
    ]["formal_worker_result_sha256"]
    accepted["terminal_result_artifact"] = deepcopy(
        terminal_state["terminal_publication"]["identity"]
    )
    lineage["successful_reservation"] = successful_identity
    lineage["prior_reservation_count"] = len(prior_history)
    lineage["prior_reservation_history"] = prior_history
    state["source_context"][
        "successful_reservation_identity"
    ] = successful_identity
    state["source_context"][
        "successful_reservation_postfetch_evidence"
    ] = successful_postfetch
    state["source_context"]["successful_reservation_artifact"] = (
        successful_artifact
    )
    state["retry_history_observation"] = {
        "prior_reservation_history": deepcopy(prior_history),
        "prior_reservation_artifacts": reservation_artifacts,
        "prior_disposition_artifacts": disposition_artifacts,
        "prior_reservation_postfetch_evidence": reservation_postfetch,
        "prior_disposition_postfetch_evidence": disposition_postfetch,
        "successful_reservation_ordinal": successful_ordinal,
        "successful_attempt_id": terminal["attempt_id"],
    }
    _rehash_accepted_state(state)
    return state


def _alias_external_identity_role(
    identity: dict[str, Any],
    alias_role: str,
) -> None:
    """Apply one Parent-Addendum-permitted role alias causally."""

    identity["artifact_role"] = alias_role
    identity["identity_sha256"] = _hash_without(
        identity,
        "identity_sha256",
    )


def _accepted_role_alias_states() -> tuple[dict[str, Any], ...]:
    """Build the four valid exact10 role-alias branches."""

    failure_history = ("FORMAL_FAILURE_ATTEMPT_PUBLISHED",)
    unknown_history = (
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
    )
    return (
        _accepted_state_with_history(
            failure_history,
            prior_reservation_alias_ordinals=frozenset({1}),
        ),
        _accepted_state_with_history(
            failure_history,
            successful_reservation_role_alias=True,
        ),
        _accepted_state_with_history(
            failure_history,
            disposition_role_alias_by_ordinal={
                1: "TERMINAL_RESULT",
            },
        ),
        _accepted_state_with_history(
            unknown_history,
            disposition_role_alias_by_ordinal={
                1: "UNKNOWN_DISPOSITION",
            },
        ),
    )


def _global_stop_condition_ids() -> frozenset[str]:
    stop_sets = [
        frozenset(row["stop_condition_ids"])
        for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
    ]
    return frozenset.intersection(*stop_sets)


def _step_state(
    accepted_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    accepted_state = (
        _accepted_state()
        if accepted_state is None
        else deepcopy(accepted_state)
    )
    accepted = accepted_state["accepted_test_run_receipt"]
    terminal = accepted["formal_worker_terminal_result"]
    outcomes = {
        row["test_node_id"]: row for row in terminal["outcomes"]
    }
    source_closure = accepted_state["source_context"][
        "successor_source_closure"
    ]
    event1_identity = accepted["success_lineage"][
        "source_baseline_event"
    ]
    accepted_hash = accepted["accepted_test_run_receipt_sha256"]
    global_stop_ids = _global_stop_condition_ids()
    receipts: list[dict[str, Any]] = []
    for step, registry_row in enumerate(
        RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
    ):
        owners = []
        for owner in registry_row["actual_owners"]:
            identity = _source_file_identity(owner["path"])
            owners.append(
                {
                    "path": owner["path"],
                    "git_blob_sha1": identity["git_blob_sha1"],
                    "sha256": identity["raw_sha256"],
                    "symbol": owner["symbol"],
                    "role": owner["role"],
                }
            )
        contracts = []
        for contract in registry_row["strict_contracts"]:
            identity = _source_file_identity(contract["validator_path"])
            contracts.append(
                {
                    "contract_id": contract["contract_id"],
                    "schema_version": contract["schema_version"],
                    "validator_path": contract["validator_path"],
                    "validator_blob_sha1": identity["git_blob_sha1"],
                    "validator_symbol": contract["validator_symbol"],
                    "invariant_ids": list(contract["invariant_ids"]),
                }
            )
        formal_nodes = list(
            RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
        )
        outcome_hashes = [
            outcomes[node_id]["evidence_sha256"]
            for node_id in formal_nodes
        ]
        formal_completion_evidence_sha256 = artifact_sha256(
            {
                "step_number": step,
                "formal_node_ids": formal_nodes,
                "outcome_evidence_sha256s": outcome_hashes,
                "accepted_test_run_receipt_sha256": accepted_hash,
            }
        )
        artifact_receipt = {
            "schema_version": _SCHEMAS["step_artifact_evidence"],
            "step_number": step,
            "required_artifact_schema_version": registry_row[
                "artifact_receipt_schema_version"
            ],
            "owner_binding_sha256": artifact_sha256(owners),
            "strict_contract_binding_sha256": artifact_sha256(contracts),
            "requirement_registry_sha256": (
                RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
            ),
            "accepted_test_run_receipt_sha256": accepted_hash,
            "formal_completion_evidence_sha256": (
                formal_completion_evidence_sha256
            ),
            "body_free": True,
        }
        stop_conditions = []
        for condition_id in registry_row["stop_condition_ids"]:
            is_global = condition_id in global_stop_ids
            proof_nodes = (
                list(_FORMAL_NODE_IDS) if is_global else formal_nodes
            )
            proof_scope = (
                "GLOBAL_EXACT134"
                if is_global
                else "STEP_EXACT_REQUIRED_NODES"
            )
            proof_node_registry_sha256 = artifact_sha256(
                {"node_ids": proof_nodes}
            )
            stop_preimage = {
                "condition_id": condition_id,
                "proof_scope": proof_scope,
                "proof_node_registry_sha256": (
                    proof_node_registry_sha256
                ),
                "outcome_evidence_sha256s": [
                    outcomes[node_id]["evidence_sha256"]
                    for node_id in proof_nodes
                ],
                "accepted_test_run_receipt_sha256": accepted_hash,
                "triggered": False,
            }
            stop_conditions.append(
                {
                    "condition_id": condition_id,
                    "proof_scope": proof_scope,
                    "proof_node_registry_sha256": (
                        proof_node_registry_sha256
                    ),
                    "accepted_test_run_receipt_sha256": accepted_hash,
                    "triggered": False,
                    "evidence_sha256": artifact_sha256(stop_preimage),
                }
            )
        parent_hash = (
            accepted_hash
            if step == 0
            else receipts[-1]["receipt_sha256"]
        )
        current_binding = {
            "source_commit_sha1": source_closure["source_commit_sha1"],
            "source_tree_sha1": source_closure["source_tree_sha1"],
            "source_baseline_event_identity_sha256": event1_identity[
                "identity_sha256"
            ],
            "successor_source_closure_sha256": source_closure[
                "source_closure_sha256"
            ],
            "canonical_current_closure_sha256": source_closure[
                "canonical_current_closure_sha256"
            ],
            "source_dependency_closure_sha256": source_closure[
                "source_dependency_closure_sha256"
            ],
            "proof_source_closure_sha256": accepted[
                "proof_source_closure_sha256"
            ],
            "requirement_registry_sha256": (
                RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
            ),
            "formal_node_registry_sha256": (
                RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
            ),
            "bootstrap_closure_sha256": source_closure[
                "bootstrap_closure_sha256"
            ],
            "formal_node_outcome_evidence_sha256": terminal[
                "formal_node_outcome_evidence_sha256"
            ],
            "accepted_test_run_receipt_sha256": accepted_hash,
            "step_view_key": f"step_{step}",
            "step_view_sha256": accepted[
                "step_view_sha256_by_step"
            ][str(step)],
            "full_graph_sha256": source_closure[
                "canonical_current_closure_sha256"
            ],
        }
        receipt = {
            "schema_version": _SCHEMAS["step"],
            "logical_cycle_id": "NLS_V3_CYCLE_001",
            "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
            "candidate_version_id": accepted["candidate_version_id"],
            "step_number": step,
            "lineage": {
                "kind": "current",
                "historical_disposition": (
                    "IMMUTABLE_NONCURRENT_EVIDENCE"
                ),
                "historical_rewrite": False,
                "historical_as_current": False,
                "backfill": False,
            },
            "current_binding": current_binding,
            "actual_owners": owners,
            "strict_contracts": contracts,
            "positive_proof": deepcopy(
                outcomes[registry_row["positive_proof"]["test_node_id"]]
            ),
            "independent_negative_proof": deepcopy(
                outcomes[
                    registry_row["independent_negative_proof"][
                        "test_node_id"
                    ]
                ]
            ),
            "artifact_receipt": artifact_receipt,
            "parent_binding": {
                "parent_kind": (
                    "SOURCE_BASELINE_EVENT_AND_ACCEPTED"
                    if step == 0
                    else "PREVIOUS_STEP_RECEIPT"
                ),
                "parent_step_number": None if step == 0 else step - 1,
                "source_baseline_event_identity_sha256": event1_identity[
                    "identity_sha256"
                ],
                "parent_receipt_sha256": parent_hash,
            },
            "completion_condition": {
                "condition_id": registry_row[
                    "completion_condition_ids"
                ][0],
                "required": True,
                "satisfied": True,
                "evidence_sha256": formal_completion_evidence_sha256,
            },
            "stop_conditions": stop_conditions,
            "next_authority": (
                "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
                f"SUCCESS_CANDIDATE_STEP{step + 1:02d}_"
                "GENERATION_SAME_APPROVED_PHASE"
                if step < 10
                else "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
                "SUCCESS_EXACT15_PUBLICATION_AND_POSTVERIFY_ONLY"
            ),
            "verdict": "PROVED",
            "automatic_progression": False,
            "body_free": True,
            "receipt_sha256": "",
        }
        receipt["receipt_sha256"] = _hash_without(
            receipt,
            "receipt_sha256",
        )
        receipts.append(receipt)
    accepted_candidate = _candidate_identity(
        artifact_role="ACCEPTED_TEST_RUN_RECEIPT",
        path=_ACCEPTED_PATH,
        artifact=accepted,
        logical_hash_key="accepted_test_run_receipt_sha256",
    )
    receipt_artifacts = [
        _candidate_identity(
            artifact_role="CURRENT_STEP_COMPLETION_RECEIPT",
            path=_STEP_PATHS[step],
            artifact=receipt,
            logical_hash_key="receipt_sha256",
        )
        for step, receipt in enumerate(receipts)
    ]
    return {
        "accepted_test_run_receipt": accepted,
        "accepted_test_run_artifact": accepted_candidate,
        "ordered_steps": list(range(11)),
        "receipts": receipts,
        "receipt_artifacts": receipt_artifacts,
        "receipt_sha256s": [
            receipt["receipt_sha256"] for receipt in receipts
        ],
        "source_context": accepted_state["source_context"],
        "terminal_result": terminal,
    }


def _all11_state(
    step_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    step_state = (
        _step_state()
        if step_state is None
        else deepcopy(step_state)
    )
    accepted = step_state["accepted_test_run_receipt"]
    receipts = step_state["receipts"]
    event1_identity = accepted["success_lineage"][
        "source_baseline_event"
    ]
    source_closure = step_state["source_context"][
        "successor_source_closure"
    ]
    all11 = {
        "schema_version": _SCHEMAS["all11"],
        "candidate_version_id": accepted["candidate_version_id"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "source_baseline_event": event1_identity,
        "source_closure": source_closure,
        "registry_sha256": RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256,
        "formal_node_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "accepted_test_run_artifact": step_state[
            "accepted_test_run_artifact"
        ],
        "accepted_test_run_receipt_sha256": accepted[
            "accepted_test_run_receipt_sha256"
        ],
        "receipt_count": 11,
        "ordered_steps": list(range(11)),
        "receipts": deepcopy(receipts),
        "receipt_artifacts": deepcopy(step_state["receipt_artifacts"]),
        "receipt_sha256s": list(step_state["receipt_sha256s"]),
        "required_sequence_event_2": {
            "event_id": "recovery_epoch002_event_02",
            "event_name": "STEP0_10_PREREQUISITES_PROVED",
            "event_ordinal": 2,
            "state": "STEP0_10_PREREQUISITES_PROVED",
            "prior_event_identity_sha256": event1_identity[
                "identity_sha256"
            ],
        },
        "next_authority": (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            "P2_SEPARATE_APPROVAL_ONLY"
        ),
        "publication_state": "PUBLISHED_ATOMIC",
        "automatic_progression": False,
        "body_free": True,
        "all11_completion_chain_sha256": "",
    }
    all11["all11_completion_chain_sha256"] = _hash_without(
        all11,
        "all11_completion_chain_sha256",
    )
    return {
        **step_state,
        "all11_completion_chain": all11,
    }


def _publication_state(
    all11_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    all11_state = (
        _all11_state()
        if all11_state is None
        else deepcopy(all11_state)
    )
    accepted = all11_state["accepted_test_run_receipt"]
    receipts = all11_state["receipts"]
    all11 = all11_state["all11_completion_chain"]
    all11_candidate = _candidate_identity(
        artifact_role="ALL11_COMPLETION_CHAIN",
        path=_ALL11_PATH,
        artifact=all11,
        logical_hash_key="all11_completion_chain_sha256",
    )
    core_by_path = {
        all11_state["accepted_test_run_artifact"]["path"]: all11_state[
            "accepted_test_run_artifact"
        ],
        **{
            row["path"]: row
            for row in all11_state["receipt_artifacts"]
        },
        all11_candidate["path"]: all11_candidate,
    }
    core = [core_by_path[path] for path in _CORE_PATHS]
    terminal_commit = accepted["terminal_result_artifact"][
        "publication_commit_sha1"
    ]
    diagnostic_base_tree_sha1 = "3" * 40
    success_commit = "c" * 40
    success_tree = "4" * 40
    event1 = all11_state["source_context"]["event1_artifact"]
    event1_identity = accepted["success_lineage"][
        "source_baseline_event"
    ]
    manifest = {
        "schema_version": _SCHEMAS["atomic_manifest"],
        "candidate_version_id": accepted["candidate_version_id"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "source_baseline_event": event1_identity,
        "base_commit_sha1": terminal_commit,
        "core_artifact_count": 13,
        "core_artifacts": core,
        "core_artifact_set_sha256": artifact_sha256(core),
        "event_supporting_artifact_count": 14,
        "expected_changed_path_count": 15,
        "event_path": _EVENT2_PATH,
        "body_free": True,
        "atomic_publication_manifest_sha256": "",
    }
    manifest["atomic_publication_manifest_sha256"] = _hash_without(
        manifest,
        "atomic_publication_manifest_sha256",
    )
    manifest_candidate = _candidate_identity(
        artifact_role="ALL11_ATOMIC_PUBLICATION_MANIFEST",
        path=_ATOMIC_MANIFEST_PATH,
        artifact=manifest,
        logical_hash_key="atomic_publication_manifest_sha256",
    )
    supporting_by_path = {
        **core_by_path,
        manifest_candidate["path"]: manifest_candidate,
    }
    supporting = [
        supporting_by_path[path] for path in _EVENT2_SUPPORTING_PATHS
    ]
    admission_identity = event1["authority"]["operational_admission"]
    challenge = "2" * 64
    event2_publication = {
        "repository_full_name": "MassyuRed/Cocolon",
        "branch": "main",
        "base_commit_sha1": terminal_commit,
        "event_path": _EVENT2_PATH,
        "supporting_artifact_count": 14,
        "supporting_artifacts": supporting,
        "supporting_artifact_set_sha256": artifact_sha256(supporting),
        "expected_changed_path_count": 15,
        "publication_state": "PUBLISHED_ATOMIC",
    }
    event2 = {
        "schema_version": _SCHEMAS["event_v2"],
        "ledger_id": event1["ledger_id"],
        "event_id": "recovery_epoch002_event_02",
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": accepted["candidate_version_id"],
        "event_name": "STEP0_10_PREREQUISITES_PROVED",
        "event_ordinal": 2,
        "state": "STEP0_10_PREREQUISITES_PROVED",
        "timestamp_utc": "2026-07-26T12:21:00Z",
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": (
                _FUTURE_EVENT2_AUTHORITY_TOKEN
            ),
            "publication_authority_token": (
                _FUTURE_EVENT2_AUTHORITY_TOKEN
            ),
            "operational_admission": admission_identity,
        },
        "challenge_id": challenge,
        "source_closure": all11["source_closure"],
        "prior_event": event1_identity,
        "primary_evidence_artifact": all11_candidate,
        "publication": event2_publication,
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
        "p0_external_identity": event1["p0_external_identity"],
        "candidate_allocation": event1["candidate_allocation"],
        "bootstrap_closure": event1["bootstrap_closure"],
    }
    event2["event_sha256"] = _hash_without(event2, "event_sha256")
    event2_candidate = _candidate_identity(
        artifact_role="SEQUENCE_EVENT_2",
        path=_EVENT2_PATH,
        artifact=event2,
        logical_hash_key="event_sha256",
    )
    artifacts_by_path = {
        _ACCEPTED_PATH: accepted,
        **{
            _STEP_PATHS[step]: receipt
            for step, receipt in enumerate(receipts)
        },
        _ALL11_PATH: all11,
        _ATOMIC_MANIFEST_PATH: manifest,
        _EVENT2_PATH: event2,
    }
    candidates_by_path = {
        **supporting_by_path,
        _EVENT2_PATH: event2_candidate,
    }
    publication_external_identities = [
        _external_identity_from_candidate(
            candidates_by_path[path],
            publication_commit_sha1=success_commit,
        )
        for path in _SUCCESS_CHANGED_PATHS
    ]
    unchanged_path_observation = {
        "scope": "ALL_PATHS_EXCEPT_SUCCESS_EXACT15",
        "mode_type_sha_complete": True,
        "mismatches": [],
    }
    unchanged_path_observation["observation_sha256"] = artifact_sha256(
        unchanged_path_observation
    )
    return {
        "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
        "terminal_commit_observation": {
            "commit_sha1": terminal_commit,
            "tree_sha1": diagnostic_base_tree_sha1,
            "authoritative_ref_read": True,
            "authoritative_tree_read": True,
            "paths_present": [],
        },
        "artifacts_by_path": artifacts_by_path,
        "candidate_identities_by_path": candidates_by_path,
        "atomic_publication_manifest": manifest,
        "event2": event2,
        "publication_transaction": {
            "reflection_contract_version": _CURRENT_REFLECTION_CONTRACT,
            "target_tree_build_count": 1,
            "success_commit_build_count": 1,
            "terminal_commit_sha1": terminal_commit,
            "base_tree_sha1": diagnostic_base_tree_sha1,
            "target_tree_sha1": success_tree,
            "parent_commit_sha1s": [terminal_commit],
            "requested_expected_old_sha1": terminal_commit,
            "observed_old_sha1": terminal_commit,
            "server_side_expected_old_applied": True,
            "changed_paths": list(_SUCCESS_CHANGED_PATHS),
            "target_blob_sha1_by_path": {
                path: candidates_by_path[path]["git_blob_sha1"]
                for path in _SUCCESS_CHANGED_PATHS
            },
            "publication_commit_sha1_by_path": {
                path: success_commit for path in _SUCCESS_CHANGED_PATHS
            },
            "write_commits": [
                {
                    "commit_sha1": success_commit,
                    "changed_paths": list(_SUCCESS_CHANGED_PATHS),
                }
            ],
            "ref_update_result": "SUCCEEDED",
            "ref_update_attempt_count": 1,
            "frozen_success_commit_sha1": success_commit,
            "reconciled_success_commit_sha1": success_commit,
            "same_frozen_success_commit_reused": True,
            "automatic_retry_requested": False,
            "publication_only_retry_requested": False,
            "publication_only_authority_present": False,
            "new_accepted_receipt_requested": False,
            "rebase_requested": False,
            "timestamp_rebuild_requested": False,
        },
        "postfetch_observation": {
            "head_commit_sha1": success_commit,
            "parent_commit_sha1s": [terminal_commit],
            "target_tree_sha1": success_tree,
            "authoritative_ref_read": True,
            "authoritative_head_read": True,
            "authoritative_parent_read": True,
            "authoritative_tree_read": True,
            "authoritative_recursive_tree_read": True,
            "changed_paths": list(_SUCCESS_CHANGED_PATHS),
            "changed_path_proof_complete": True,
            "artifact_raw_sha256_by_path": {
                path: candidates_by_path[path]["raw_sha256"]
                for path in _SUCCESS_CHANGED_PATHS
            },
            "artifact_git_blob_sha1_by_path": {
                path: candidates_by_path[path]["git_blob_sha1"]
                for path in _SUCCESS_CHANGED_PATHS
            },
            "artifact_logical_sha256_by_path": {
                path: candidates_by_path[path]["logical_artifact_sha256"]
                for path in _SUCCESS_CHANGED_PATHS
            },
            "artifact_schema_by_path": {
                path: candidates_by_path[path]["schema_version"]
                for path in _SUCCESS_CHANGED_PATHS
            },
            "artifact_body_free_by_path": {
                path: candidates_by_path[path]["body_free"]
                for path in _SUCCESS_CHANGED_PATHS
            },
            "publication_external_identities": (
                publication_external_identities
            ),
            "unchanged_path_observation": unchanged_path_observation,
            "unchanged_path_mismatches": [],
            "owner_issue_codes": [],
            "independent_issue_codes": [],
            "state": "POSTVERIFIED",
        },
    }


def _set_publication_write_commits(
    state: dict[str, Any],
    writes: list[dict[str, Any]],
    *,
    verification_head_sha1: str | None = None,
) -> None:
    """Bind final target identities to the last approved write per path."""

    commit_by_path: dict[str, str] = {}
    for write in writes:
        for path in write["changed_paths"]:
            commit_by_path[path] = write["commit_sha1"]
    assert set(commit_by_path) == set(_SUCCESS_CHANGED_PATHS)
    transaction = state["publication_transaction"]
    transaction["write_commits"] = deepcopy(writes)
    transaction["publication_commit_sha1_by_path"] = commit_by_path
    transaction["target_tree_build_count"] = len(writes)
    transaction["success_commit_build_count"] = len(writes)
    transaction["ref_update_attempt_count"] = len(writes)
    transaction["frozen_success_commit_sha1"] = writes[-1]["commit_sha1"]
    transaction["reconciled_success_commit_sha1"] = writes[-1][
        "commit_sha1"
    ]
    postfetch = state["postfetch_observation"]
    postfetch["head_commit_sha1"] = (
        writes[-1]["commit_sha1"]
        if verification_head_sha1 is None
        else verification_head_sha1
    )
    candidates = state["candidate_identities_by_path"]
    postfetch["publication_external_identities"] = [
        _external_identity_from_candidate(
            candidates[path],
            publication_commit_sha1=commit_by_path[path],
        )
        for path in _SUCCESS_CHANGED_PATHS
    ]


def _independent_state(
    accepted_owner_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    accepted_owner_state = (
        _accepted_state()
        if accepted_owner_state is None
        else deepcopy(accepted_owner_state)
    )
    step_owner_state = _step_state(accepted_owner_state)
    all11_owner_state = _all11_state(step_owner_state)
    publication_owner_state = _publication_state(all11_owner_state)
    return {
        "parent_addendum_external_identity": (
            _parent_addendum_external_identity()
        ),
        "parent_addendum_postfetch_evidence": (
            _parent_addendum_postfetch_evidence()
        ),
        "successor_closure_owner_state": _closure_state(),
        "successor_succession_owner_state": _sequence_state(),
        "terminal_owner_state": deepcopy(
            accepted_owner_state["terminal_owner_state"]
        ),
        "accepted_owner_state": accepted_owner_state,
        "step_owner_state": step_owner_state,
        "all11_owner_state": all11_owner_state,
        "publication_owner_state": publication_owner_state,
        "verifier_source_observation": _source_file_identity(
            _ROLE_PATHS["independent_verifier"]
        ),
        "verifier_import_violations": [],
        "shared_primitive_allowlist": list(_SHARED_PRIMITIVE_ALLOWLIST),
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "publication_requested": False,
    }


def _parent_valid_terminal_input(
    terminal_kind: str,
) -> dict[str, Any]:
    """Bind a valid SUCCESS/FAILURE terminal to its exact1 disposition."""

    assert terminal_kind in {"SUCCESS", "FAILURE"}
    terminal_state = _terminal_state()
    if terminal_kind == "FAILURE":
        terminal = terminal_state["terminal_result"]
        failed_node = terminal["collection_node_ids"][-1]
        terminal["states"][failed_node] = "FAILED"
        terminal["outcomes"][-1]["result"] = "FAILED"
        terminal["counts"]["passed"] = 133
        terminal["counts"]["failed"] = 1
        terminal["exit_code"] = 1
        _rehash_terminal_state(terminal_state)
    publication = terminal_state["terminal_publication"]
    tagged = {
        "tag": "VALID_TERMINAL_RESULT",
        "terminal_kind": terminal_kind,
        "terminal_result": deepcopy(terminal_state["terminal_result"]),
        "terminal_disposition_artifact": deepcopy(
            publication["identity"]
        ),
        "terminal_disposition_postfetch_evidence": deepcopy(
            publication["postfetch_evidence"]
        ),
    }
    assert set(tagged) == _PARENT_VALID_TERMINAL_INPUT_KEYS
    return tagged


def _parent_unknown_disposition_input() -> dict[str, Any]:
    """Bind the strict unknown-disposition body to exact1 postfetch facts."""

    sequence = _sequence_state()
    readiness_artifact, readiness_identity = (
        _readiness_artifact_fixture(sequence)
    )
    reservation_artifact, reservation_identity = (
        _reservation_artifact_fixture(
            sequence=sequence,
            readiness_artifact=readiness_artifact,
            readiness_identity=readiness_identity,
            prior_history=[],
            reservation_ordinal=1,
            publication_base_commit_sha1="6" * 40,
            publication_commit_sha1="7" * 40,
        )
    )
    disposition = _unknown_disposition_artifact_fixture(
        reservation_identity=reservation_identity,
        attempt_id=reservation_artifact["attempt_id"],
    )
    candidate = _candidate_identity(
        artifact_role="ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch002_Attempt01_"
            "ConsumptionUnknownDisposition_20260726.json"
        ),
        artifact=disposition,
        logical_hash_key=(
            "attempt_consumption_unknown_disposition_sha256"
        ),
    )
    identity = _external_identity_from_candidate(
        candidate,
        publication_commit_sha1="8" * 40,
    )
    tagged = {
        "tag": "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
        "unknown_disposition": disposition,
        "terminal_disposition_artifact": identity,
        "terminal_disposition_postfetch_evidence": (
            _single_artifact_postfetch(
                identity,
                base_commit_sha1="7" * 40,
            )
        ),
    }
    assert set(tagged) == _PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS
    return tagged


def _rebind_parent_unknown_disposition(
    state: dict[str, Any],
) -> None:
    """Keep an unknown branch byte/hash/identity/postfetch causal."""

    terminal_input = state["terminal_input"]
    disposition = terminal_input["unknown_disposition"]
    disposition[
        "attempt_consumption_unknown_disposition_sha256"
    ] = _hash_without(
        disposition,
        "attempt_consumption_unknown_disposition_sha256",
    )
    old_identity = terminal_input["terminal_disposition_artifact"]
    candidate = _candidate_identity(
        artifact_role="ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
        path=old_identity["path"],
        artifact=disposition,
        logical_hash_key=(
            "attempt_consumption_unknown_disposition_sha256"
        ),
    )
    identity = _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=old_identity[
            "publication_commit_sha1"
        ],
    )
    old_postfetch = terminal_input[
        "terminal_disposition_postfetch_evidence"
    ]
    terminal_input["terminal_disposition_artifact"] = identity
    terminal_input[
        "terminal_disposition_postfetch_evidence"
    ] = _single_artifact_postfetch(
        identity,
        base_commit_sha1=old_postfetch[
            "publication_parent_commit_sha1s"
        ][0],
        base_tree_sha1=old_postfetch["base_tree_sha1"],
        target_tree_sha1=old_postfetch["target_tree_sha1"],
    )


def _parent_state() -> dict[str, Any]:
    return {
        "phase_order": list(_PHASE_ORDER),
        "executable_phases": list(_EXECUTABLE_PHASES),
        "external_ports": list(_EXTERNAL_PORTS),
        "port_call_count": 1,
        "automatic_progression": False,
        "terminal_kind": "SUCCESS",
        "terminal_input": _parent_valid_terminal_input("SUCCESS"),
        "terminal_disposition_postverified": True,
        "terminal_disposition_artifact_count": 1,
        "success_exact15_requested": True,
        "success_artifact_counts": {
            "accepted": 1,
            "step": 11,
            "all11": 1,
            "atomic_manifest": 1,
            "event2": 1,
        },
        "individual_success_artifact_publication_requested": False,
        "same_attempt_rerun_requested": False,
        "synthetic_terminal_requested": False,
        "terminal_stop_code": "SUCCESS_TERMINAL_POSTVERIFIED",
        "event2_postverified": True,
        "step0_10_prerequisites_proved": True,
        "p2_separate_approval_present": False,
        "p2_started": False,
    }


_STATE_FACTORIES: dict[str, Callable[[], dict[str, Any]]] = {
    "closure": _closure_state,
    "sequence": _sequence_state,
    "event2": _publication_state,
    "terminal": _terminal_state,
    "runner": _terminal_state,
    "accepted": _accepted_state,
    "step": _step_state,
    "all11": _all11_state,
    "publication": _publication_state,
    "single_publication": _single_publication_state,
    "independent": _independent_state,
    "parent": _parent_state,
}


def _rehash_closure_state(state: dict[str, Any]) -> None:
    graph = state["success_owner_graph"]
    if "success_owner_graph_sha256" in graph:
        graph["success_owner_graph_sha256"] = _hash_without(
            graph,
            "success_owner_graph_sha256",
        )
    manifest = state["success_contract_test_manifest"]
    if "test_files" in manifest:
        manifest["test_files_sha256"] = artifact_sha256(
            manifest["test_files"]
        )
    if "success_contract_test_manifest_sha256" in manifest:
        manifest["success_contract_test_manifest_sha256"] = _hash_without(
            manifest,
            "success_contract_test_manifest_sha256",
        )
    closure = state["successor_source_closure"]
    closure["success_owner_graph_sha256"] = graph.get(
        "success_owner_graph_sha256"
    )
    closure["success_contract_test_manifest_sha256"] = manifest.get(
        "success_contract_test_manifest_sha256"
    )
    if "source_closure_sha256" in closure:
        closure["source_closure_sha256"] = _hash_without(
            closure,
            "source_closure_sha256",
        )


def _rehash_step_chain(
    state: dict[str, Any],
    *,
    start: int,
    preserve_start_parent: bool,
) -> None:
    receipts = state["receipts"]
    for index in range(start, len(receipts)):
        receipt = receipts[index]
        if index > start or not preserve_start_parent:
            receipt["parent_binding"]["parent_receipt_sha256"] = (
                state["accepted_test_run_receipt"][
                    "accepted_test_run_receipt_sha256"
                ]
                if index == 0
                else receipts[index - 1]["receipt_sha256"]
            )
        receipt["receipt_sha256"] = _hash_without(
            receipt,
            "receipt_sha256",
        )
        state["receipt_sha256s"][index] = receipt["receipt_sha256"]
        state["receipt_artifacts"][index] = _candidate_identity(
            artifact_role="CURRENT_STEP_COMPLETION_RECEIPT",
            path=_STEP_PATHS[index],
            artifact=receipt,
            logical_hash_key="receipt_sha256",
        )
    if "all11_completion_chain" in state:
        all11 = state["all11_completion_chain"]
        all11["receipts"] = deepcopy(receipts)
        all11["receipt_artifacts"] = deepcopy(state["receipt_artifacts"])
        all11["receipt_sha256s"] = list(state["receipt_sha256s"])
        all11["all11_completion_chain_sha256"] = _hash_without(
            all11,
            "all11_completion_chain_sha256",
        )


def _rehash_event(event: dict[str, Any]) -> None:
    event["event_sha256"] = _hash_without(event, "event_sha256")


def _rehash_operational_admission(admission: dict[str, Any]) -> None:
    if "authority_sha256" in admission["authority"]:
        admission["authority"]["authority_sha256"] = _hash_without(
            admission["authority"],
            "authority_sha256",
        )
    if "scope_sha256" in admission["scope"]:
        admission["scope"]["scope_sha256"] = _hash_without(
            admission["scope"],
            "scope_sha256",
        )
    transport = admission.get("transport_capability")
    if type(transport) is dict and "transport_capability_sha256" in transport:
        transport["transport_capability_sha256"] = _hash_without(
            transport,
            "transport_capability_sha256",
        )
    durable = admission.get("durable_store_capability")
    if type(durable) is dict and "durable_store_capability_sha256" in durable:
        durable["durable_store_capability_sha256"] = _hash_without(
            durable,
            "durable_store_capability_sha256",
        )
    if "operational_admission_sha256" in admission:
        admission["operational_admission_sha256"] = _hash_without(
            admission,
            "operational_admission_sha256",
        )


def _refresh_atomic_publication_derived(
    state: dict[str, Any],
    *,
    manifest_changed: bool,
) -> None:
    """Propagate changed manifest/Event2 bytes without repairing semantics."""

    manifest = state["atomic_publication_manifest"]
    event = state["event2"]
    if manifest_changed:
        manifest_candidate = _candidate_identity(
            artifact_role="ALL11_ATOMIC_PUBLICATION_MANIFEST",
            path=_ATOMIC_MANIFEST_PATH,
            artifact=manifest,
            logical_hash_key="atomic_publication_manifest_sha256",
        )
        state["artifacts_by_path"][_ATOMIC_MANIFEST_PATH] = deepcopy(
            manifest
        )
        state["candidate_identities_by_path"][
            _ATOMIC_MANIFEST_PATH
        ] = manifest_candidate
        supporting = event["publication"]["supporting_artifacts"]
        for index, identity in enumerate(supporting):
            if identity["path"] == _ATOMIC_MANIFEST_PATH:
                supporting[index] = manifest_candidate
                break
        event["publication"]["supporting_artifact_set_sha256"] = (
            artifact_sha256(supporting)
        )
        _rehash_event(event)

    event_candidate = _candidate_identity(
        artifact_role="SEQUENCE_EVENT_2",
        path=_EVENT2_PATH,
        artifact=event,
        logical_hash_key="event_sha256",
    )
    state["artifacts_by_path"][_EVENT2_PATH] = deepcopy(event)
    state["candidate_identities_by_path"][_EVENT2_PATH] = event_candidate
    for path in (_ATOMIC_MANIFEST_PATH, _EVENT2_PATH):
        identity = state["candidate_identities_by_path"][path]
        state["publication_transaction"]["target_blob_sha1_by_path"][
            path
        ] = identity["git_blob_sha1"]
        state["postfetch_observation"][
            "artifact_raw_sha256_by_path"
        ][path] = identity["raw_sha256"]
        state["postfetch_observation"][
            "artifact_git_blob_sha1_by_path"
        ][path] = identity["git_blob_sha1"]
        state["postfetch_observation"][
            "artifact_logical_sha256_by_path"
        ][path] = identity["logical_artifact_sha256"]
        state["postfetch_observation"][
            "artifact_schema_by_path"
        ][path] = identity["schema_version"]
        state["postfetch_observation"][
            "artifact_body_free_by_path"
        ][path] = identity["body_free"]
        external_identities = state["postfetch_observation"][
            "publication_external_identities"
        ]
        external_identity = _external_identity_from_candidate(
            identity,
            publication_commit_sha1=state["publication_transaction"][
                "publication_commit_sha1_by_path"
            ][path],
        )
        for index, observed in enumerate(external_identities):
            if observed["path"] == path:
                external_identities[index] = external_identity
                break


def _rebind_completion_chain(
    state: dict[str, Any],
    completion: dict[str, Any],
) -> None:
    """Propagate one completion artifact through all downstream identities."""

    state["successor_completion_receipt"] = completion
    completion_publication = state["successor_completion_publication"]
    completion_candidate = _candidate_identity(
        artifact_role="SUCCESSOR_COMPLETION_RECEIPT",
        path=completion_publication["identity"]["path"],
        artifact=completion,
        logical_hash_key="receipt_sha256",
    )
    completion_identity = _external_identity_from_candidate(
        completion_candidate,
        publication_commit_sha1=completion_publication["identity"][
            "publication_commit_sha1"
        ],
    )
    completion_publication["artifact"] = deepcopy(completion)
    completion_publication["identity"] = completion_identity
    completion_postfetch = completion_publication["postfetch_evidence"]
    completion_publication[
        "postfetch_evidence"
    ] = _single_artifact_postfetch(
        completion_identity,
        base_commit_sha1=completion_publication[
            "parent_commit_sha1s"
        ][0],
        base_tree_sha1=completion_postfetch["base_tree_sha1"],
        target_tree_sha1=completion_postfetch["target_tree_sha1"],
    )

    admission = state["operational_admission_receipt"]
    admission["successor_completion_receipt"] = completion_identity
    _rehash_operational_admission(admission)
    admission_publication = state["operational_admission_publication"]
    admission_candidate = _candidate_identity(
        artifact_role="P1_OPERATIONAL_ADMISSION_RECEIPT",
        path=admission_publication["identity"]["path"],
        artifact=admission,
        logical_hash_key="operational_admission_sha256",
    )
    admission_identity = _external_identity_from_candidate(
        admission_candidate,
        publication_commit_sha1=admission_publication["identity"][
            "publication_commit_sha1"
        ],
    )
    admission_publication["artifact"] = deepcopy(admission)
    admission_publication["identity"] = admission_identity
    admission_postfetch = admission_publication["postfetch_evidence"]
    admission_publication[
        "postfetch_evidence"
    ] = _single_artifact_postfetch(
        admission_identity,
        base_commit_sha1=admission_publication[
            "parent_commit_sha1s"
        ][0],
        base_tree_sha1=admission_postfetch["base_tree_sha1"],
        target_tree_sha1=admission_postfetch["target_tree_sha1"],
    )

    allocation = state["candidate_allocation"]
    allocation["successor_completion_receipt"] = completion_identity
    allocation["candidate_allocation_sha256"] = _hash_without(
        allocation,
        "candidate_allocation_sha256",
    )
    event = state["event1"]
    event["authority"]["operational_admission"] = admission_identity
    event["primary_evidence_artifact"] = completion_identity
    event["candidate_allocation"] = deepcopy(allocation)
    event["publication"]["supporting_artifacts"] = [
        completion_identity
    ]
    event["publication"]["supporting_artifact_set_sha256"] = (
        artifact_sha256([completion_identity])
    )
    transaction = event["publication"].get("transaction_capability")
    if type(transaction) is dict:
        transaction["operational_admission_identity_sha256"] = (
            admission_identity["identity_sha256"]
        )
        transaction["transaction_capability_sha256"] = _hash_without(
            transaction,
            "transaction_capability_sha256",
        )
    _rehash_event(event)
    event_publication = state["event1_publication"]
    event_candidate = _candidate_identity(
        artifact_role="SOURCE_BASELINE_EVENT",
        path=event_publication["identity"]["path"],
        artifact=event,
        logical_hash_key="event_sha256",
    )
    event_identity = _external_identity_from_candidate(
        event_candidate,
        publication_commit_sha1=event_publication["identity"][
            "publication_commit_sha1"
        ],
    )
    event_publication["artifact"] = deepcopy(event)
    event_publication["identity"] = event_identity
    event_postfetch = event_publication["postfetch_evidence"]
    event_publication["postfetch_evidence"] = _single_artifact_postfetch(
        event_identity,
        base_commit_sha1=event_publication["parent_commit_sha1s"][0],
        base_tree_sha1=event_postfetch["base_tree_sha1"],
        target_tree_sha1=event_postfetch["target_tree_sha1"],
    )
    state["candidate_operational_identity"][
        "event1_identity_sha256"
    ] = event_identity["identity_sha256"]


def _rebind_c06_sequence_from_closure_owner(
    state: dict[str, Any],
    closure_owner_state: Mapping[str, Any],
) -> None:
    """Propagate one Parent Addendum observation through Event1."""

    for key in (
        "parent_addendum_external_identity",
        "parent_addendum_postfetch_evidence",
    ):
        if key in closure_owner_state:
            state[key] = deepcopy(closure_owner_state[key])
        else:
            state.pop(key, None)
    source_closure = deepcopy(
        closure_owner_state["successor_source_closure"]
    )
    state["successor_source_closure"] = source_closure
    completion = deepcopy(state["successor_completion_receipt"])
    completion["parent_addendum_external_identity_sha256"] = (
        source_closure["parent_addendum_external_identity_sha256"]
    )
    completion["successor_source_closure_sha256"] = source_closure[
        "source_closure_sha256"
    ]
    completion["receipt_sha256"] = _hash_without(
        completion,
        "receipt_sha256",
    )
    _rebind_completion_chain(state, completion)
    completion_identity = state["successor_completion_publication"][
        "identity"
    ]

    admission = _operational_admission_fixture(
        completion_identity=completion_identity,
        source_closure=source_closure,
    )
    admission_publication = state["operational_admission_publication"]
    admission_candidate = _candidate_identity(
        artifact_role="P1_OPERATIONAL_ADMISSION_RECEIPT",
        path=admission_publication["identity"]["path"],
        artifact=admission,
        logical_hash_key="operational_admission_sha256",
    )
    admission_identity = _external_identity_from_candidate(
        admission_candidate,
        publication_commit_sha1=admission_publication["identity"][
            "publication_commit_sha1"
        ],
    )
    admission_postfetch = admission_publication["postfetch_evidence"]
    admission_publication["artifact"] = deepcopy(admission)
    admission_publication["identity"] = admission_identity
    admission_publication[
        "postfetch_evidence"
    ] = _single_artifact_postfetch(
        admission_identity,
        base_commit_sha1=admission_publication[
            "parent_commit_sha1s"
        ][0],
        base_tree_sha1=admission_postfetch["base_tree_sha1"],
        target_tree_sha1=admission_postfetch["target_tree_sha1"],
    )
    state["operational_admission_receipt"] = admission

    allocation = _candidate_allocation_fixture(
        source_closure=source_closure,
        completion_identity=completion_identity,
    )
    state["candidate_allocation"] = allocation
    event = _event1_fixture(
        source_closure=source_closure,
        bootstrap_closure=state["bootstrap_closure"],
        completion_identity=completion_identity,
        admission_identity=admission_identity,
        candidate_allocation=allocation,
    )
    event_publication = state["event1_publication"]
    event_candidate = _candidate_identity(
        artifact_role="SOURCE_BASELINE_EVENT",
        path=event_publication["identity"]["path"],
        artifact=event,
        logical_hash_key="event_sha256",
    )
    event_identity = _external_identity_from_candidate(
        event_candidate,
        publication_commit_sha1=event_publication["identity"][
            "publication_commit_sha1"
        ],
    )
    event_postfetch = event_publication["postfetch_evidence"]
    event_publication["artifact"] = deepcopy(event)
    event_publication["identity"] = event_identity
    event_publication["postfetch_evidence"] = _single_artifact_postfetch(
        event_identity,
        base_commit_sha1=event_publication[
            "parent_commit_sha1s"
        ][0],
        base_tree_sha1=event_postfetch["base_tree_sha1"],
        target_tree_sha1=event_postfetch["target_tree_sha1"],
    )
    state["event1"] = event
    state["candidate_operational_identity"][
        "event1_identity_sha256"
    ] = event_identity["identity_sha256"]


def _refresh_event1_publication_derived(state: dict[str, Any]) -> None:
    """Rebind Event1 identity/postfetch after an intentional Event mutation."""

    event = state["event1"]
    publication = state["event1_publication"]
    candidate = _candidate_identity(
        artifact_role="SOURCE_BASELINE_EVENT",
        path=publication["identity"]["path"],
        artifact=event,
        logical_hash_key="event_sha256",
    )
    identity = _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=publication["identity"][
            "publication_commit_sha1"
        ],
    )
    publication["artifact"] = deepcopy(event)
    publication["identity"] = identity
    old_postfetch = publication["postfetch_evidence"]
    publication["postfetch_evidence"] = _single_artifact_postfetch(
        identity,
        base_commit_sha1=publication["parent_commit_sha1s"][0],
        base_tree_sha1=old_postfetch["base_tree_sha1"],
        target_tree_sha1=old_postfetch["target_tree_sha1"],
    )
    state["candidate_operational_identity"][
        "event1_identity_sha256"
    ] = identity["identity_sha256"]


def _rebind_successor_evidence(
    state: dict[str, Any],
    *,
    evidence_kind: str,
    artifact: dict[str, Any],
) -> None:
    """Propagate one S1/S2 semantic receipt through completion lineage."""

    if evidence_kind == "causal_red":
        artifact_key = "causal_red_evidence_artifact"
        identity_key = "causal_red_evidence"
        postfetch_key = "causal_red_postfetch_evidence"
        completion_key = "causal_red_evidence_sha256"
        artifact_role = "SUCCESSOR_CAUSAL_RED_RESULT"
    elif evidence_kind == "combined_green":
        artifact_key = "combined_green_evidence_artifact"
        identity_key = "combined_green_evidence"
        postfetch_key = "combined_green_postfetch_evidence"
        completion_key = "combined_green_evidence_sha256"
        artifact_role = "SUCCESSOR_COMBINED_GREEN_RESULT"
    else:
        raise AssertionError(f"unknown successor evidence: {evidence_kind}")
    artifact["receipt_sha256"] = _hash_without(
        artifact,
        "receipt_sha256",
    )
    old_identity = state[identity_key]
    old_postfetch = state[postfetch_key]
    candidate = _candidate_identity(
        artifact_role=artifact_role,
        path=old_identity["path"],
        artifact=artifact,
        logical_hash_key="receipt_sha256",
    )
    identity = _external_identity_from_candidate(
        candidate,
        publication_commit_sha1=old_identity["publication_commit_sha1"],
    )
    state[artifact_key] = artifact
    state[identity_key] = identity
    state[postfetch_key] = _single_artifact_postfetch(
        identity,
        base_commit_sha1=old_postfetch[
            "publication_parent_commit_sha1s"
        ][0],
        base_tree_sha1=old_postfetch["base_tree_sha1"],
        target_tree_sha1=old_postfetch["target_tree_sha1"],
    )
    completion = deepcopy(state["successor_completion_receipt"])
    completion[completion_key] = identity["logical_artifact_sha256"]
    completion["receipt_sha256"] = _hash_without(
        completion,
        "receipt_sha256",
    )
    _rebind_completion_chain(state, completion)


def _c06_sequence_mutations() -> list[dict[str, Any]]:
    baseline = _sequence_state()
    variants: list[dict[str, Any]] = []

    def variant(mutator: Callable[[dict[str, Any]], None]) -> None:
        row = deepcopy(baseline)
        mutator(row)
        variants.append(row)

    variant(
        lambda row: row.pop("parent_addendum_external_identity")
    )
    variant(
        lambda row: row.pop("parent_addendum_postfetch_evidence")
    )

    def completion_binding(row: dict[str, Any]) -> None:
        completion = deepcopy(row["successor_completion_receipt"])
        completion["parent_addendum_external_identity_sha256"] = "f" * 64
        completion["receipt_sha256"] = _hash_without(
            completion,
            "receipt_sha256",
        )
        _rebind_completion_chain(row, completion)

    variant(completion_binding)

    def event_path_a(row: dict[str, Any]) -> None:
        closure = row["event1"]["source_closure"]
        closure["parent_addendum_external_identity_sha256"] = "f" * 64
        closure["source_closure_sha256"] = _hash_without(
            closure,
            "source_closure_sha256",
        )
        _rehash_event(row["event1"])
        _refresh_event1_publication_derived(row)

    variant(event_path_a)

    def event_direct_key(row: dict[str, Any]) -> None:
        row["event1"][
            "parent_addendum_external_identity_sha256"
        ] = _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        _rehash_event(row["event1"])
        _refresh_event1_publication_derived(row)

    variant(event_direct_key)

    def event_second_supporting(row: dict[str, Any]) -> None:
        publication = row["event1"]["publication"]
        publication["supporting_artifacts"].append(
            deepcopy(row["parent_addendum_external_identity"])
        )
        publication["supporting_artifact_count"] = 2
        publication["supporting_artifact_set_sha256"] = artifact_sha256(
            publication["supporting_artifacts"]
        )
        _rehash_event(row["event1"])
        _refresh_event1_publication_derived(row)

    variant(event_second_supporting)
    return variants


def _c06_independent_mutations() -> list[dict[str, Any]]:
    baseline = _independent_state()
    variants: list[dict[str, Any]] = []
    for closure_mutation in _mutated_states("C06", "closure"):
        row = deepcopy(baseline)
        row["successor_closure_owner_state"] = closure_mutation
        for key in (
            "parent_addendum_external_identity",
            "parent_addendum_postfetch_evidence",
        ):
            if key in closure_mutation:
                row[key] = deepcopy(closure_mutation[key])
            else:
                row.pop(key, None)
        variants.append(row)
        if all(
            key in closure_mutation
            for key in (
                "parent_addendum_external_identity",
                "parent_addendum_postfetch_evidence",
            )
        ):
            coherent = deepcopy(baseline)
            coherent["successor_closure_owner_state"] = deepcopy(
                closure_mutation
            )
            _rebind_c06_sequence_from_closure_owner(
                coherent["successor_succession_owner_state"],
                closure_mutation,
            )
            coherent["parent_addendum_external_identity"] = deepcopy(
                closure_mutation[
                    "parent_addendum_external_identity"
                ]
            )
            coherent["parent_addendum_postfetch_evidence"] = deepcopy(
                closure_mutation[
                    "parent_addendum_postfetch_evidence"
                ]
            )
            variants.append(coherent)
    for sequence_mutation in _c06_sequence_mutations():
        row = deepcopy(baseline)
        row["successor_succession_owner_state"] = sequence_mutation
        for key in (
            "parent_addendum_external_identity",
            "parent_addendum_postfetch_evidence",
        ):
            if key in sequence_mutation:
                row[key] = deepcopy(sequence_mutation[key])
            else:
                row.pop(key, None)
        variants.append(row)
    for issue_key in ("owner_issue_codes", "independent_issue_codes"):
        row = deepcopy(baseline)
        row[issue_key].append("PARENT_ADDENDUM_POSTFETCH_ISSUE")
        variants.append(row)
    return variants


def _independent_succession_mutations(
    case_id: str,
) -> list[dict[str, Any]]:
    baseline = _independent_state()
    variants: list[dict[str, Any]] = []
    for succession_mutation in _mutated_states(case_id, "sequence"):
        row = deepcopy(baseline)
        row["successor_succession_owner_state"] = succession_mutation
        variants.append(row)
    return variants


def _mutated_states(case_id: str, role: str) -> list[dict[str, Any]]:
    state = _STATE_FACTORIES[role]()
    variants: list[dict[str, Any]] = []

    def variant(mutator: Callable[[dict[str, Any]], None]) -> None:
        row = deepcopy(state)
        mutator(row)
        variants.append(row)

    if case_id == "C01":
        state["historical_d2_rewrite_requested"] = True
    elif case_id == "C02":
        state["successor_source_closure"].pop(
            "success_owner_graph_sha256"
        )
    elif case_id == "C03":
        variant(
            lambda row: row["source_observation"].__setitem__(
                "source_commit_sha1", "f" * 40
            )
        )
        variant(
            lambda row: row["source_observation"].__setitem__(
                "source_tree_sha1", "f" * 40
            )
        )
        return variants
    elif case_id == "C04":
        variant(
            lambda row: row["historical_d2_ancestry"].__setitem__(
                "verified_ancestor",
                False,
            )
        )
        variant(
            lambda row: row["historical_d2_ancestry"].__setitem__(
                "source_commit_sha1",
                row["successor_source_closure"]["source_commit_sha1"],
            )
        )
        variant(
            lambda row: row["historical_d2_ancestry"].__setitem__(
                "source_tree_sha1",
                row["successor_source_closure"]["source_tree_sha1"],
            )
        )
        return variants
    elif case_id == "C05":
        def bind_d2_identity(
            row: dict[str, Any],
            mutator: Callable[[dict[str, Any]], None],
            *,
            recompute: bool = True,
        ) -> None:
            identity = row["historical_d2_completion_receipt"]
            mutator(identity)
            if recompute:
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            row["successor_source_closure"][
                "historical_d2_completion_receipt_identity_sha256"
            ] = identity["identity_sha256"]
            _rehash_closure_state(row)

        for key, value in (
            ("artifact_role", "WRONG_D2_RECEIPT"),
            ("schema_version", "forbidden.d2.v0"),
            ("path", "forbidden/d2.json"),
            ("git_blob_sha1", "f" * 40),
            ("raw_sha256", "f" * 64),
            ("logical_artifact_sha256", "f" * 64),
            ("publication_commit_sha1", "f" * 40),
            ("body_free", False),
        ):
            variant(
                lambda row, key=key, value=value: bind_d2_identity(
                    row,
                    lambda identity, key=key, value=value: (
                        identity.__setitem__(key, value)
                    ),
                )
            )
        variant(
            lambda row: bind_d2_identity(
                row,
                lambda identity: identity.pop("artifact_role"),
            )
        )
        variant(
            lambda row: bind_d2_identity(
                row,
                lambda identity: identity.__setitem__(
                    "identity_sha256",
                    "f" * 64,
                ),
                recompute=False,
            )
        )

        def bare_d2_hash(row: dict[str, Any]) -> None:
            row.pop("historical_d2_completion_receipt")

        variant(bare_d2_hash)
        return variants
    elif case_id == "C06":
        def bind_identity(
            row: dict[str, Any],
            mutator: Callable[[dict[str, Any]], None],
            *,
            recompute: bool = True,
        ) -> None:
            identity = row["parent_addendum_external_identity"]
            mutator(identity)
            if recompute:
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            row["parent_addendum_postfetch_evidence"][
                "parent_addendum_external_identity"
            ] = deepcopy(identity)
            row["successor_source_closure"][
                "parent_addendum_external_identity_sha256"
            ] = identity["identity_sha256"]
            _rehash_closure_state(row)

        fixed_field_mutations: tuple[tuple[str, Any], ...] = (
            ("artifact_role", "PARENT_ADDENDUM_MARKDOWN"),
            ("schema_version", "forbidden.parent.addendum.v0"),
            ("repository_full_name", "MassyuRed/mashos-api"),
            ("path", _PARENT_ADDENDUM_DESIGN_PATH),
            ("git_blob_sha1", _PARENT_ADDENDUM_BLOB),
            ("raw_sha256", _PARENT_ADDENDUM_SHA256),
            ("logical_artifact_sha256", "f" * 64),
            ("publication_commit_sha1", _PARENT_ADDENDUM_BASE_COMMIT),
            ("body_free", False),
        )
        for key, value in fixed_field_mutations:
            variant(
                lambda row, key=key, value=value: bind_identity(
                    row,
                    lambda identity, key=key, value=value: (
                        identity.__setitem__(key, value)
                    ),
                )
            )

        variant(
            lambda row: bind_identity(
                row,
                lambda identity: identity.pop("artifact_role"),
            )
        )
        variant(
            lambda row: bind_identity(
                row,
                lambda identity: identity.__setitem__(
                    "unexpected_identity_key",
                    "FORBIDDEN",
                ),
            )
        )
        variant(
            lambda row: bind_identity(
                row,
                lambda identity: identity.__setitem__(
                    "identity_sha256",
                    "f" * 64,
                ),
                recompute=False,
            )
        )

        def bare_hash(row: dict[str, Any]) -> None:
            row.pop("parent_addendum_external_identity")
            row.pop("parent_addendum_postfetch_evidence")

        variant(bare_hash)

        def closure_scalar(row: dict[str, Any]) -> None:
            row["successor_source_closure"][
                "parent_addendum_external_identity_sha256"
            ] = "f" * 64
            _rehash_closure_state(row)

        variant(closure_scalar)

        postfetch_mutations: tuple[tuple[tuple[str, ...], Any], ...] = (
            (("authoritative_ref_read",), False),
            (
                ("verification_commit_kind",),
                "CALLER_SUPPLIED_UNVERIFIED_COMMIT",
            ),
            (("publication_reachable_from_verification_ref",), False),
            (
                ("publication_parent_commit_sha1s",),
                ["f" * 40],
            ),
            (
                ("publication_changed_paths",),
                list(_PARENT_ADDENDUM_CHANGED_PATHS[:-1]),
            ),
            (("receipt_absent_at_base",), False),
            (("receipt_at_publication", "git_blob_sha1"), "f" * 40),
            (("receipt_at_publication", "raw_sha256"), "f" * 64),
            (("receipt_at_publication", "trailing_lf_count"), 0),
            (
                ("receipt_at_publication", "schema_version"),
                "forbidden.parent.addendum.v0",
            ),
            (("receipt_at_publication", "body_free"), False),
            (
                ("receipt_at_publication", "automatic_progression"),
                True,
            ),
            (
                ("receipt_at_publication", "state"),
                "PARENT_ADDENDUM_NOT_FROZEN",
            ),
            (
                (
                    "receipt_at_publication",
                    "logical_artifact_sha256",
                ),
                "f" * 64,
            ),
            (
                ("receipt_at_publication", "bound_markdown_path"),
                "forbidden/ParentAddendum.md",
            ),
            (
                ("receipt_at_publication", "bound_markdown_raw_sha256"),
                "f" * 64,
            ),
            (("markdown_at_publication", "git_blob_sha1"), "f" * 40),
            (("markdown_at_publication", "raw_sha256"), "f" * 64),
            (
                ("receipt_at_verification_ref", "raw_sha256"),
                "f" * 64,
            ),
            (
                ("markdown_at_verification_ref", "raw_sha256"),
                "f" * 64,
            ),
            (("postfetch_state",), "UNKNOWN"),
        )

        def mutate_postfetch(
            row: dict[str, Any],
            path: tuple[str, ...],
            value: Any,
        ) -> None:
            target = row["parent_addendum_postfetch_evidence"]
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value

        for path, value in postfetch_mutations:
            variant(
                lambda row, path=path, value=value: mutate_postfetch(
                    row,
                    path,
                    value,
                )
            )
        variant(
            lambda row: row["parent_addendum_postfetch_evidence"][
                "owner_issue_codes"
            ].append("OWNER_ISSUE")
        )
        variant(
            lambda row: row["parent_addendum_postfetch_evidence"][
                "independent_issue_codes"
            ].append("INDEPENDENT_ISSUE")
        )
        return variants
    elif case_id == "C07":
        def mutate_owner_graph(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            graph = row["success_owner_graph"]
            if mutation == "role_count":
                graph["owner_role_count"] = 14
            elif mutation == "path_count":
                graph["owner_path_count"] = 11
            elif mutation == "binding":
                graph["owner_role_bindings"][0]["git_blob_sha1"] = (
                    "f" * 40
                )
            elif mutation == "verifier_path":
                graph["independent_verifier_constraints"][
                    "verifier_path"
                ] = "forbidden/verifier.py"
            elif mutation == "verifier_blob":
                graph["independent_verifier_constraints"][
                    "verifier_git_blob_sha1"
                ] = "f" * 40
            elif mutation == "verifier_raw":
                graph["independent_verifier_constraints"][
                    "verifier_raw_sha256"
                ] = "f" * 64
            elif mutation == "forbidden_import":
                graph["independent_verifier_constraints"][
                    "forbidden_owner_import_count"
                ] = 1
            else:
                graph["independent_verifier_constraints"][
                    "shared_primitive_allowlist"
                ].reverse()
            _rehash_closure_state(row)

        for mutation in (
            "role_count",
            "path_count",
            "binding",
            "verifier_path",
            "verifier_blob",
            "verifier_raw",
            "forbidden_import",
            "primitive_order",
        ):
            variant(
                lambda row, mutation=mutation: mutate_owner_graph(
                    row,
                    mutation,
                )
            )
        return variants
    elif case_id == "C08":
        def mutate_manifest(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            manifest = row["success_contract_test_manifest"]
            if mutation == "historical_count":
                manifest["historical_node_count"] = 45
            elif mutation == "successor_count":
                manifest["successor_node_count"] = 63
            elif mutation == "total_count":
                manifest["total_node_count"] = 109
            elif mutation == "order":
                manifest["test_node_ids"][-2:] = reversed(
                    manifest["test_node_ids"][-2:]
                )
            elif mutation == "duplicate":
                manifest["test_node_ids"][-1] = manifest[
                    "test_node_ids"
                ][-2]
            elif mutation == "test_file":
                manifest["test_files"][0]["git_blob_sha1"] = "f" * 40
            else:
                row["successor_source_closure"][
                    "success_contract_test_manifest_sha256"
                ] = "f" * 64
                row["successor_source_closure"][
                    "source_closure_sha256"
                ] = _hash_without(
                    row["successor_source_closure"],
                    "source_closure_sha256",
                )
                return
            _rehash_closure_state(row)

        for mutation in (
            "historical_count",
            "successor_count",
            "total_count",
            "order",
            "duplicate",
            "test_file",
            "closure_binding",
        ):
            variant(
                lambda row, mutation=mutation: mutate_manifest(
                    row,
                    mutation,
                )
            )
        return variants
    elif case_id == "C09":
        def swap_red_green(row: dict[str, Any]) -> None:
            completion = deepcopy(row["successor_completion_receipt"])
            (
                completion["causal_red_evidence_sha256"],
                completion["combined_green_evidence_sha256"],
            ) = (
                completion["combined_green_evidence_sha256"],
                completion["causal_red_evidence_sha256"],
            )
            completion["receipt_sha256"] = _hash_without(
                completion,
                "receipt_sha256",
            )
            _rebind_completion_chain(row, completion)

        variant(swap_red_green)
        variant(lambda row: row.pop("causal_red_evidence_artifact"))
        variant(lambda row: row.pop("causal_red_evidence"))
        variant(lambda row: row.pop("causal_red_postfetch_evidence"))
        variant(lambda row: row.pop("combined_green_evidence_artifact"))
        variant(lambda row: row.pop("combined_green_evidence"))
        variant(lambda row: row.pop("combined_green_postfetch_evidence"))
        variant(
            lambda row: row["causal_red_postfetch_evidence"].__setitem__(
                "postfetch_state",
                "UNKNOWN",
            )
        )
        variant(
            lambda row: row[
                "combined_green_postfetch_evidence"
            ]["independent_issue_codes"].append("INDEPENDENT_ISSUE")
        )
        for evidence_key in (
            "causal_red_postfetch_evidence",
            "combined_green_postfetch_evidence",
        ):
            for mutation_path, value in (
                _COMPLETE_EXACT1_POSTFETCH_MUTATIONS
            ):
                variant(
                    lambda row,
                    evidence_key=evidence_key,
                    mutation_path=mutation_path,
                    value=value: _mutate_complete_exact1_postfetch(
                        row[evidence_key],
                        mutation_path,
                        value,
                    )
                )
        for identity_key in (
            "causal_red_evidence",
            "combined_green_evidence",
        ):
            def mutate_identity_shape(
                row: dict[str, Any],
                identity_key: str,
                *,
                extra: bool,
            ) -> None:
                identity = row[identity_key]
                if extra:
                    identity["unexpected_key"] = "forbidden"
                else:
                    identity.pop("path")
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )

            variant(
                lambda row,
                identity_key=identity_key: mutate_identity_shape(
                    row,
                    identity_key,
                    extra=False,
                )
            )
            variant(
                lambda row,
                identity_key=identity_key: mutate_identity_shape(
                    row,
                    identity_key,
                    extra=True,
                )
            )
            for field, value in _EXTERNAL_IDENTITY_FIELD_MUTATIONS:
                variant(
                    lambda row,
                    identity_key=identity_key,
                    field=field,
                    value=value: _mutate_external_identity_field(
                        row[identity_key],
                        field,
                        value,
                    )
                )

        def mutate_red_artifact(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            artifact = deepcopy(row["causal_red_evidence_artifact"])
            if mutation == "state":
                artifact["state"] = "SUCCESSOR_CAUSAL_RED_NOT_FROZEN"
            elif mutation == "counts":
                artifact["failed"] = 63
                artifact["passed"] = 1
            elif mutation == "nodes":
                artifact["successor_node_count"] = 63
            elif mutation == "source":
                artifact["source_entry_commit_sha1"] = "f" * 40
            else:
                artifact["independent_issue_codes"].append(
                    "INDEPENDENT_ISSUE"
                )
            _rebind_successor_evidence(
                row,
                evidence_kind="causal_red",
                artifact=artifact,
            )

        for mutation in (
            "state",
            "counts",
            "nodes",
            "source",
            "issues",
        ):
            variant(
                lambda row, mutation=mutation: mutate_red_artifact(
                    row,
                    mutation,
                )
            )

        def mutate_green_artifact(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            artifact = deepcopy(row["combined_green_evidence_artifact"])
            if mutation == "red_binding":
                artifact["causal_red_evidence_sha256"] = "f" * 64
            elif mutation == "source_commit":
                artifact["successor_source_commit_sha1"] = "f" * 40
            elif mutation == "source_tree":
                artifact["successor_source_tree_sha1"] = "f" * 40
            elif mutation == "closure":
                artifact["successor_source_closure_sha256"] = "f" * 64
            elif mutation == "manifest":
                artifact[
                    "success_contract_test_manifest_sha256"
                ] = "f" * 64
            elif mutation == "node_order":
                artifact["test_node_ids"][-2:] = reversed(
                    artifact["test_node_ids"][-2:]
                )
            elif mutation == "execution":
                artifact["executed_node_ids"].pop()
            elif mutation == "outcome":
                artifact["outcome_states"][
                    artifact["test_node_ids"][-1]
                ] = "FAILED"
            elif mutation == "counts":
                artifact["counts"]["passed"] = 109
                artifact["counts"]["failed"] = 1
            elif mutation == "owner_issue":
                artifact["owner_issue_codes"].append("OWNER_ISSUE")
            elif mutation == "independent_issue":
                artifact["independent_issue_codes"].append(
                    "INDEPENDENT_ISSUE"
                )
            else:
                artifact["state"] = "SUCCESSOR_TARGETED_GREEN_INCOMPLETE"
            _rebind_successor_evidence(
                row,
                evidence_kind="combined_green",
                artifact=artifact,
            )

        for mutation in (
            "red_binding",
            "source_commit",
            "source_tree",
            "closure",
            "manifest",
            "node_order",
            "execution",
            "outcome",
            "counts",
            "owner_issue",
            "independent_issue",
            "state",
        ):
            variant(
                lambda row, mutation=mutation: mutate_green_artifact(
                    row,
                    mutation,
                )
            )
        variants.extend(
            _exact1_publication_contract_mutations(
                state,
                lambda row: row[
                    "successor_completion_publication"
                ],
                logical_hash_key="receipt_sha256",
            )
        )
        return variants
    elif case_id == "C10":
        def allocation_mutation(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            allocation = deepcopy(row["candidate_allocation"])
            recompute = True
            if mutation == "keyset":
                allocation.pop("allocated_at_utc")
            elif mutation == "extra_key":
                allocation["unexpected_key"] = "forbidden"
            elif mutation == "schema":
                allocation["schema_version"] = "wrong.schema.v1"
            elif mutation == "cycle":
                allocation["logical_cycle_id"] = "OTHER_CYCLE"
            elif mutation == "epoch":
                allocation["recovery_epoch_id"] = "OTHER_EPOCH"
            elif mutation == "candidate":
                allocation["candidate_version_id"] = "nls_v3_rc_0034"
            elif mutation == "d2_closure":
                allocation[
                    "historical_d2_final_closure_sha256"
                ] = "f" * 64
            elif mutation == "d2_identity":
                _mutate_external_identity_field(
                    allocation["historical_d2_completion_receipt"],
                    "logical_artifact_sha256",
                    "f" * 64,
                )
            elif mutation == "source":
                allocation[
                    "successor_source_closure_sha256"
                ] = "f" * 64
            elif mutation == "completion":
                _mutate_external_identity_field(
                    allocation["successor_completion_receipt"],
                    "logical_artifact_sha256",
                    "f" * 64,
                )
            elif mutation == "timestamp_after_event":
                allocation["allocated_at_utc"] = "2026-07-26T12:04:00Z"
            elif mutation == "timestamp_noncanonical":
                allocation["allocated_at_utc"] = (
                    "2026-07-26T12:02:00.000Z"
                )
            else:
                allocation["candidate_allocation_sha256"] = "f" * 64
                recompute = False
            if (
                recompute
                and "candidate_allocation_sha256" in allocation
            ):
                allocation["candidate_allocation_sha256"] = _hash_without(
                    allocation,
                    "candidate_allocation_sha256",
                )
            row["candidate_allocation"] = allocation
            row["event1"]["candidate_allocation"] = deepcopy(allocation)
            if mutation == "candidate":
                row["event1"]["candidate_version_id"] = allocation[
                    "candidate_version_id"
                ]
                row["candidate_operational_identity"][
                    "candidate_version_id"
                ] = allocation["candidate_version_id"]
            _rehash_event(row["event1"])
            _refresh_event1_publication_derived(row)

        for mutation in (
            "keyset",
            "extra_key",
            "schema",
            "cycle",
            "epoch",
            "candidate",
            "d2_closure",
            "d2_identity",
            "source",
            "completion",
            "timestamp_after_event",
            "timestamp_noncanonical",
            "self_hash",
        ):
            variant(
                lambda row, mutation=mutation: allocation_mutation(
                    row,
                    mutation,
                )
            )

        def allocation_identity_mutation(
            row: dict[str, Any],
            identity_key: str,
            field: str,
            value: Any,
        ) -> None:
            allocation = deepcopy(row["candidate_allocation"])
            identity = allocation[identity_key]
            if field == "__missing_path__":
                identity.pop("path")
            elif field == "__extra_key__":
                identity["unexpected_key"] = "forbidden"
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            else:
                _mutate_external_identity_field(identity, field, value)
            allocation["candidate_allocation_sha256"] = _hash_without(
                allocation,
                "candidate_allocation_sha256",
            )
            row["candidate_allocation"] = allocation
            row["event1"]["candidate_allocation"] = deepcopy(allocation)
            _rehash_event(row["event1"])
            _refresh_event1_publication_derived(row)

        for identity_key in (
            "historical_d2_completion_receipt",
            "successor_completion_receipt",
        ):
            for field, value in (
                ("__missing_path__", None),
                ("__extra_key__", None),
                *_EXTERNAL_IDENTITY_FIELD_MUTATIONS,
            ):
                variant(
                    lambda row,
                    identity_key=identity_key,
                    field=field,
                    value=value: allocation_identity_mutation(
                        row,
                        identity_key,
                        field,
                        value,
                    )
                )

        def admission_mutation(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            admission = row["operational_admission_receipt"]
            if mutation == "shape":
                admission.pop("operational_admission_sha256")
            elif mutation == "path":
                row["operational_admission_publication"]["identity"][
                    "path"
                ] = "forbidden/admission.json"
                row["operational_admission_publication"]["identity"][
                    "identity_sha256"
                ] = _hash_without(
                    row["operational_admission_publication"]["identity"],
                    "identity_sha256",
                )
            elif mutation == "authority":
                admission["authority"].pop("authority_sha256")
                _rehash_operational_admission(admission)
            elif mutation == "scope_order":
                admission["scope"]["operation_set"].reverse()
                _rehash_operational_admission(admission)
            elif mutation == "transport":
                admission["transport_capability"][
                    "expected_old_compare_and_swap"
                ] = False
                _rehash_operational_admission(admission)
            elif mutation == "durable":
                admission["durable_store_capability"][
                    "write_once_attempt_claim"
                ] = False
                _rehash_operational_admission(admission)
            elif mutation == "freshness":
                admission["expires_at_utc"] = admission["issued_at_utc"]
                _rehash_operational_admission(admission)
            elif mutation == "scope_binding":
                admission["scope"]["repository_full_name"] = (
                    "MassyuRed/mashos-api"
                )
                _rehash_operational_admission(admission)
            elif mutation == "challenge_binding":
                admission["transport_capability"]["challenge_id"] = (
                    "f" * 64
                )
                _rehash_operational_admission(admission)
            elif mutation == "exact1":
                row["operational_admission_publication"][
                    "changed_paths"
                ].append("forbidden/extra.json")
            elif mutation == "admission_direct_parent":
                row["operational_admission_publication"][
                    "parent_commit_sha1s"
                ] = ["f" * 40]
            elif mutation == "admission_expected_old":
                row["operational_admission_publication"][
                    "observed_old_sha1"
                ] = "f" * 40
            elif mutation == "admission_postfetch":
                row["operational_admission_publication"][
                    "postfetch_state"
                ] = "UNKNOWN"
            elif mutation == "admission_independent_postfetch":
                row["operational_admission_publication"][
                    "postfetch_evidence"
                ]["independent_issue_codes"].append("INDEPENDENT_ISSUE")
            elif mutation == "admission_target_absence":
                row["operational_admission_publication"][
                    "postfetch_evidence"
                ]["target_absent_at_base"] = False
            elif mutation == "completion_admission_tree_link":
                row["operational_admission_publication"][
                    "postfetch_evidence"
                ]["base_tree_sha1"] = "f" * 40
            elif mutation == "admission_event_tree_link":
                row["event1_publication"]["postfetch_evidence"][
                    "base_tree_sha1"
                ] = "f" * 40
            elif mutation == "event_authority":
                row["event1"]["authority"][
                    "operational_admission"
                ]["identity_sha256"] = "f" * 64
                _rehash_event(row["event1"])
            elif mutation == "event_authority_token":
                row["event1"]["authority"][
                    "transition_authority_token"
                ] = "DIFFERENT_UNISSUED_FIXTURE_AUTHORITY"
                _rehash_event(row["event1"])
            elif mutation == "event_publication":
                row["event1"]["publication"].pop(
                    "transaction_capability"
                )
                _rehash_event(row["event1"])
            elif mutation == "transaction_binding":
                transaction = row["event1"]["publication"][
                    "transaction_capability"
                ]
                transaction[
                    "operational_admission_identity_sha256"
                ] = "f" * 64
                transaction["transaction_capability_sha256"] = (
                    _hash_without(
                        transaction,
                        "transaction_capability_sha256",
                    )
                )
                _rehash_event(row["event1"])
            elif mutation == "event_direct_parent":
                row["event1_publication"]["parent_commit_sha1s"] = [
                    "f" * 40
                ]
            elif mutation == "event_expected_old":
                row["event1_publication"]["observed_old_sha1"] = "f" * 40
            elif mutation == "event_postfetch":
                row["event1_publication"]["postfetch_state"] = "UNKNOWN"
            elif mutation == "event_independent_postfetch":
                row["event1_publication"]["postfetch_evidence"][
                    "independent_issue_codes"
                ].append("INDEPENDENT_ISSUE")
            elif mutation == "primary_supporting_parity":
                publication = row["event1"]["publication"]
                publication["supporting_artifacts"] = [
                    _parent_addendum_external_identity()
                ]
                publication["supporting_artifact_set_sha256"] = (
                    artifact_sha256(publication["supporting_artifacts"])
                )
                _rehash_event(row["event1"])
            elif mutation == "candidate_without_postfetch":
                row["event1_publication"]["postfetch_state"] = "UNKNOWN"
            else:
                row["candidate_operational_identity"][
                    "event1_identity_sha256"
                ] = "f" * 64
            if mutation in {
                "event_authority",
                "event_authority_token",
                "event_publication",
                "transaction_binding",
                "primary_supporting_parity",
            }:
                _refresh_event1_publication_derived(row)

        for mutation in (
            "shape",
            "path",
            "authority",
            "scope_order",
            "freshness",
            "scope_binding",
            "exact1",
            "admission_postfetch",
            "admission_independent_postfetch",
            "admission_target_absence",
            "event_authority",
            "event_authority_token",
            "event_postfetch",
            "event_independent_postfetch",
            "primary_supporting_parity",
            "candidate_without_postfetch",
            "candidate_identity_mismatch",
        ):
            variant(
                lambda row, mutation=mutation: admission_mutation(
                    row,
                    mutation,
                )
            )
        variants.extend(
            _exact1_publication_contract_mutations(
                state,
                lambda row: row[
                    "operational_admission_publication"
                ],
                logical_hash_key="operational_admission_sha256",
            )
        )
        return variants
    elif case_id == "T01":
        state["terminal_result"].pop(
            "formal_node_outcome_evidence_sha256"
        )
        state["terminal_result"]["formal_worker_result_sha256"] = (
            _hash_without(
                state["terminal_result"],
                "formal_worker_result_sha256",
            )
        )
    elif case_id == "T02":
        terminal = state["terminal_result"]
        terminal["collection_node_ids"][-2:] = reversed(
            terminal["collection_node_ids"][-2:]
        )
        _rehash_terminal_state(state)
    elif case_id == "T03":
        terminal = state["terminal_result"]
        terminal["executed_node_ids"][-2:] = reversed(
            terminal["executed_node_ids"][-2:]
        )
        _rehash_terminal_state(state)
    elif case_id == "T04":
        state["terminal_result"]["outcomes"][0].pop("actual_closed_code")
        _rehash_terminal_state(state)
    elif case_id == "T05":
        state["terminal_result"]["outcomes"][0][
            "source_blob_sha1"
        ] = "f" * 40
        _rehash_terminal_state(state)
    elif case_id == "T06":
        negative_index = _FORMAL_NODE_IDS.index(_NEGATIVE_NODE_IDS[0])
        state["terminal_result"]["outcomes"][negative_index][
            "expected_closed_code"
        ] = "DIFFERENT_CODE"
        _rehash_terminal_state(state)
    elif case_id == "T07":
        node_id = _NEGATIVE_NODE_IDS[0]
        variant(
            lambda row: row[
                "runner_closed_code_observations"
            ].pop(node_id)
        )

        def remove_terminal_actual(row: dict[str, Any]) -> None:
            negative_index = _FORMAL_NODE_IDS.index(node_id)
            row["terminal_result"]["outcomes"][negative_index][
                "actual_closed_code"
            ] = None
            _rehash_terminal_state(row)

        variant(remove_terminal_actual)
        return variants
    elif case_id == "T08":
        def count_mutation(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            terminal = row["terminal_result"]
            if mutation == "passed":
                terminal["counts"]["passed"] = 133
            elif mutation == "bool":
                terminal["counts"]["collected"] = True
            elif mutation == "keyset":
                terminal["counts"].pop("deselected")
            elif mutation == "states":
                terminal["states"][
                    terminal["collection_node_ids"][-1]
                ] = "FAILED"
            else:
                terminal["executed_node_ids"].pop()
            _rehash_terminal_state(row)

        for mutation in (
            "passed",
            "bool",
            "keyset",
            "states",
            "executed",
        ):
            variant(
                lambda row, mutation=mutation: count_mutation(
                    row,
                    mutation,
                )
            )
        return variants
    elif case_id == "T09":
        variant(lambda row: row["owner_issue_codes"].append("OWNER_ISSUE"))
        variant(
            lambda row: row["independent_issue_codes"].append(
                "INDEPENDENT_ISSUE"
            )
        )
        variant(lambda row: row["checkpoint_chain"].pop())

        def skip(row: dict[str, Any]) -> None:
            terminal = row["terminal_result"]
            node_id = terminal["collection_node_ids"][-1]
            terminal["states"][node_id] = "SKIPPED"
            terminal["outcomes"][-1]["result"] = "SKIPPED"
            terminal["counts"]["passed"] = 133
            terminal["counts"]["skipped"] = 1
            _rehash_terminal_state(row)

        variant(skip)

        def collection_error(row: dict[str, Any]) -> None:
            terminal = row["terminal_result"]
            terminal["collection_errors"] = 1
            terminal["counts"]["collection_errors"] = 1
            _rehash_terminal_state(row)

        variant(collection_error)
        for field, value in (
            ("exit_code", True),
            ("exit_code", 1),
            ("exit_class", "SIGNALED"),
            ("signal_number", 9),
            ("timed_out", True),
            ("formal_exact134_invocation_count", 2),
        ):
            def mutate_terminal(
                row: dict[str, Any],
                field: str = field,
                value: Any = value,
            ) -> None:
                row["terminal_result"][field] = value
                _rehash_terminal_state(row)

            variant(mutate_terminal)
        variant(
            lambda row: row["retry_history"].__setitem__(
                "consumed_attempt_ids", []
            )
        )
        return variants
    elif case_id == "T10":
        def mutate_terminal_publication_field(
            row: dict[str, Any],
            field: str,
            value: Any,
        ) -> None:
            row["terminal_publication"][field] = deepcopy(value)

        for field, value in (
            ("postfetch_state", "UNKNOWN"),
            ("changed_paths", ["forbidden/terminal.json"]),
        ):
            variant(
                lambda row,
                field=field,
                value=value: mutate_terminal_publication_field(
                    row,
                    field,
                    value,
                )
            )

        for key in sorted(
            {
                "reflection_contract_version",
                "artifact",
                "identity",
                "changed_paths",
                "postfetch_evidence",
                "postfetch_state",
            }
        ):
            variant(
                lambda row, key=key: row[
                    "terminal_publication"
                ].pop(key)
            )
        variant(
            lambda row: row["terminal_publication"].__setitem__(
                "unexpected_key",
                "forbidden",
            )
        )
        variant(
            lambda row: row["terminal_publication"]["artifact"].__setitem__(
                "formal_worker_result_sha256",
                "f" * 64,
            )
        )

        def mutate_terminal_identity_contract(
            row: dict[str, Any],
            mutation: str,
            field: str | None = None,
            value: Any = None,
        ) -> None:
            identity = row["terminal_publication"]["identity"]
            if mutation == "missing_key":
                assert field is not None
                identity.pop(field)
                if "identity_sha256" in identity:
                    identity["identity_sha256"] = _hash_without(
                        identity,
                        "identity_sha256",
                    )
            elif mutation == "extra_key":
                identity["unexpected_key"] = "forbidden"
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            else:
                assert field is not None
                _mutate_external_identity_field(identity, field, value)

        for field in sorted(_EXTERNAL_IDENTITY_KEYS):
            variant(
                lambda row,
                field=field: mutate_terminal_identity_contract(
                    row,
                    "missing_key",
                    field,
                )
            )
        variant(
            lambda row: mutate_terminal_identity_contract(
                row,
                "extra_key",
            )
        )
        for field, value in _EXTERNAL_IDENTITY_FIELD_MUTATIONS:
            variant(
                lambda row,
                field=field,
                value=value: mutate_terminal_identity_contract(
                    row,
                    "field",
                    field,
                    value,
                )
            )

        for mutation_path, value in _COMPLETE_EXACT1_POSTFETCH_MUTATIONS:
            variant(
                lambda row,
                mutation_path=mutation_path,
                value=value: _mutate_complete_exact1_postfetch(
                    row["terminal_publication"]["postfetch_evidence"],
                    mutation_path,
                    value,
                )
            )
        return variants
    elif case_id == "A01":
        state["terminal_publication"]["postfetch_state"] = "UNKNOWN"
    elif case_id == "A02":
        accepted = state["accepted_test_run_receipt"]
        terminal = accepted["formal_worker_terminal_result"]
        node_id = terminal["collection_node_ids"][-1]
        terminal["states"][node_id] = "FAILED"
        terminal["outcomes"][-1]["result"] = "FAILED"
        terminal["counts"]["passed"] = 133
        terminal["counts"]["failed"] = 1
        _rehash_accepted_state(state)
    elif case_id == "A03":
        state["accepted_test_run_receipt"][
            "formal_worker_terminal_result"
        ]["formal_exact134_invocation_count"] = 2
        _rehash_accepted_state(state)
    elif case_id == "A04":
        variant(
            lambda row: row["source_context"][
                "successor_source_closure"
            ].__setitem__("source_closure_sha256", "f" * 64)
        )
        variant(
            lambda row: row["source_context"][
                "bootstrap_closure"
            ].__setitem__("bootstrap_closure_sha256", "f" * 64)
        )
        variant(
            lambda row: row["terminal_owner_state"][
                "parity_bindings"
            ].__setitem__("python_runtime_identity_sha256", "f" * 64)
        )
        return variants
    elif case_id == "A05":
        def mutate_candidate(
            row: dict[str, Any],
            owner: str,
        ) -> None:
            if owner == "event":
                event = row["source_context"]["event1_artifact"]
                event["candidate_version_id"] = "different_candidate"
                allocation = event["candidate_allocation"]
                allocation["candidate_version_id"] = "different_candidate"
                allocation["candidate_allocation_sha256"] = _hash_without(
                    allocation,
                    "candidate_allocation_sha256",
                )
                _rehash_event(event)
                old_identity = row["source_context"]["event1_identity"]
                candidate = _candidate_identity(
                    artifact_role="SOURCE_BASELINE_EVENT",
                    path=old_identity["path"],
                    artifact=event,
                    logical_hash_key="event_sha256",
                )
                identity = _external_identity_from_candidate(
                    candidate,
                    publication_commit_sha1=old_identity[
                        "publication_commit_sha1"
                    ],
                )
                row["source_context"]["event1_identity"] = identity
                old_postfetch = row["source_context"][
                    "event1_postfetch_evidence"
                ]
                row["source_context"][
                    "event1_postfetch_evidence"
                ] = _single_artifact_postfetch(
                    identity,
                    base_commit_sha1="4" * 40,
                    base_tree_sha1=old_postfetch["base_tree_sha1"],
                    target_tree_sha1=old_postfetch["target_tree_sha1"],
                )
                row["accepted_test_run_receipt"]["success_lineage"][
                    "source_baseline_event"
                ] = identity
                _rehash_accepted_state(row)
            elif owner == "readiness":
                context = row["source_context"]
                readiness = context["readiness_artifact"]
                readiness["candidate_version_id"] = "different_candidate"
                readiness["preflight_id"] = _readiness_preflight_id(
                    readiness
                )
                readiness[
                    "bootstrap_readiness_receipt_sha256"
                ] = _hash_without(
                    readiness,
                    "bootstrap_readiness_receipt_sha256",
                )
                old_identity = context["readiness_identity"]
                identity = _strict_artifact_external_identity(
                    artifact_role="BOOTSTRAP_READINESS",
                    path=old_identity["path"],
                    artifact=readiness,
                    logical_hash_key=(
                        "bootstrap_readiness_receipt_sha256"
                    ),
                    publication_commit_sha1=old_identity[
                        "publication_commit_sha1"
                    ],
                )
                old_postfetch = context[
                    "readiness_postfetch_evidence"
                ]
                context["readiness_identity"] = identity
                context[
                    "readiness_postfetch_evidence"
                ] = _single_artifact_postfetch(
                    identity,
                    base_commit_sha1=old_postfetch[
                        "publication_parent_commit_sha1s"
                    ][0],
                    base_tree_sha1=old_postfetch["base_tree_sha1"],
                    target_tree_sha1=old_postfetch["target_tree_sha1"],
                )
            else:
                context = row["source_context"]
                reservation = context[
                    "successful_reservation_artifact"
                ]
                reservation["candidate_version_id"] = (
                    "different_candidate"
                )
                reservation["attempt_id"] = _reservation_attempt_id(
                    reservation
                )
                reservation[
                    "formal_test_run_reservation_sha256"
                ] = _hash_without(
                    reservation,
                    "formal_test_run_reservation_sha256",
                )
                old_identity = context[
                    "successful_reservation_identity"
                ]
                identity = _strict_artifact_external_identity(
                    artifact_role="FORMAL_TEST_RUN_RESERVATION",
                    path=old_identity["path"],
                    artifact=reservation,
                    logical_hash_key=(
                        "formal_test_run_reservation_sha256"
                    ),
                    publication_commit_sha1=old_identity[
                        "publication_commit_sha1"
                    ],
                )
                old_postfetch = context[
                    "successful_reservation_postfetch_evidence"
                ]
                context["successful_reservation_identity"] = identity
                context[
                    "successful_reservation_postfetch_evidence"
                ] = _single_artifact_postfetch(
                    identity,
                    base_commit_sha1=old_postfetch[
                        "publication_parent_commit_sha1s"
                    ][0],
                    base_tree_sha1=old_postfetch["base_tree_sha1"],
                    target_tree_sha1=old_postfetch["target_tree_sha1"],
                )
                row["accepted_test_run_receipt"]["success_lineage"][
                    "successful_reservation"
                ] = deepcopy(identity)
                _rehash_accepted_state(row)

        for owner in ("event", "readiness", "reservation"):
            variant(
                lambda row, owner=owner: mutate_candidate(row, owner)
            )
        return variants
    elif case_id == "A06":
        def rehash_lineage(row: dict[str, Any]) -> None:
            _rehash_accepted_state(row)

        def remove_history(row: dict[str, Any]) -> None:
            lineage = row["accepted_test_run_receipt"][
                "success_lineage"
            ]
            lineage["prior_reservation_count"] = 0
            lineage["prior_reservation_history"] = []
            rehash_lineage(row)

        variant(remove_history)

        def mutate_prior_row(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            prior = row["accepted_test_run_receipt"][
                "success_lineage"
            ]["prior_reservation_history"][0]
            if mutation == "ordinal":
                prior["reservation_ordinal"] = 2
            elif mutation == "attempt":
                prior["attempt_id"] = row[
                    "accepted_test_run_receipt"
                ]["formal_worker_terminal_result"]["attempt_id"]
            else:
                prior["disposition_kind"] = (
                    "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED"
                )
            rehash_lineage(row)

        for mutation in ("ordinal", "attempt", "disposition_kind"):
            variant(
                lambda row, mutation=mutation: mutate_prior_row(
                    row,
                    mutation,
                )
            )
        variant(
            lambda row: row["retry_history_observation"].__setitem__(
                "successful_reservation_ordinal",
                1,
            )
        )

        def mutate_prior_identity(
            row: dict[str, Any],
            artifact_key: str,
            field: str,
            value: Any,
        ) -> None:
            lineage = row["accepted_test_run_receipt"][
                "success_lineage"
            ]
            identity = lineage["prior_reservation_history"][0][
                artifact_key
            ]
            if field == "__missing_path__":
                identity.pop("path")
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            elif field == "__extra_key__":
                identity["unexpected_key"] = "forbidden"
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            else:
                _mutate_external_identity_field(identity, field, value)
            rehash_lineage(row)

        for artifact_key in (
            "reservation_artifact",
            "disposition_artifact",
        ):
            for field, value in (
                ("__missing_path__", None),
                ("__extra_key__", None),
                *_EXTERNAL_IDENTITY_FIELD_MUTATIONS,
            ):
                variant(
                    lambda row,
                    artifact_key=artifact_key,
                    field=field,
                    value=value: mutate_prior_identity(
                        row,
                        artifact_key,
                        field,
                        value,
                    )
                )

        def mutate_successful_identity(
            row: dict[str, Any],
            field: str,
            value: Any,
        ) -> None:
            lineage = row["accepted_test_run_receipt"][
                "success_lineage"
            ]
            identity = lineage["successful_reservation"]
            if field == "__missing_path__":
                identity.pop("path")
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            elif field == "__extra_key__":
                identity["unexpected_key"] = "forbidden"
                identity["identity_sha256"] = _hash_without(
                    identity,
                    "identity_sha256",
                )
            else:
                _mutate_external_identity_field(identity, field, value)
            rehash_lineage(row)

        for field, value in (
            ("__missing_path__", None),
            ("__extra_key__", None),
            *_EXTERNAL_IDENTITY_FIELD_MUTATIONS,
        ):
            variant(
                lambda row,
                field=field,
                value=value: mutate_successful_identity(
                    row,
                    field,
                        value,
                    )
            )

        def mutate_prior_identity_paired(
            row: dict[str, Any],
            artifact_key: str,
            evidence_key: str,
            field: str,
            value: Any,
        ) -> None:
            mutate_prior_identity(
                row,
                artifact_key,
                field,
                value,
            )
            identity = row["accepted_test_run_receipt"][
                "success_lineage"
            ]["prior_reservation_history"][0][artifact_key]
            observation = row["retry_history_observation"]
            observation["prior_reservation_history"][0][
                artifact_key
            ] = deepcopy(identity)
            if "path" in identity:
                old_postfetch = observation[evidence_key][0]
                observation[evidence_key][0] = (
                    _single_artifact_postfetch(
                        identity,
                        base_commit_sha1=old_postfetch[
                            "publication_parent_commit_sha1s"
                        ][0],
                        base_tree_sha1=old_postfetch["base_tree_sha1"],
                        target_tree_sha1=old_postfetch[
                            "target_tree_sha1"
                        ],
                    )
                )
            _rehash_accepted_state(row)

        paired_field_mutations = (
            ("artifact_role", "WRONG_ROLE"),
            ("schema_version", "wrong.schema.v1"),
            ("repository_full_name", "Other/Repository"),
            ("publication_commit_sha1", "f" * 40),
            ("body_free", False),
            ("identity_sha256", "f" * 64),
        )
        for artifact_key, evidence_key in (
            (
                "reservation_artifact",
                "prior_reservation_postfetch_evidence",
            ),
            (
                "disposition_artifact",
                "prior_disposition_postfetch_evidence",
            ),
        ):
            for field, value in (
                ("__missing_path__", None),
                ("__extra_key__", None),
                *paired_field_mutations,
            ):
                variant(
                    lambda row,
                    artifact_key=artifact_key,
                    evidence_key=evidence_key,
                    field=field,
                    value=value: mutate_prior_identity_paired(
                        row,
                        artifact_key,
                        evidence_key,
                        field,
                        value,
                    )
                )

        def mutate_successful_identity_paired(
            row: dict[str, Any],
            field: str,
            value: Any,
        ) -> None:
            mutate_successful_identity(row, field, value)
            identity = row["accepted_test_run_receipt"][
                "success_lineage"
            ]["successful_reservation"]
            context = row["source_context"]
            context["successful_reservation_identity"] = deepcopy(
                identity
            )
            if "path" in identity:
                old_postfetch = context[
                    "successful_reservation_postfetch_evidence"
                ]
                context[
                    "successful_reservation_postfetch_evidence"
                ] = _single_artifact_postfetch(
                    identity,
                    base_commit_sha1=old_postfetch[
                        "publication_parent_commit_sha1s"
                    ][0],
                    base_tree_sha1=old_postfetch["base_tree_sha1"],
                    target_tree_sha1=old_postfetch["target_tree_sha1"],
                )
            _rehash_accepted_state(row)

        for field, value in (
            ("__missing_path__", None),
            ("__extra_key__", None),
            *(
                row
                for row in paired_field_mutations
                if row[0] != "publication_commit_sha1"
            ),
        ):
            variant(
                lambda row,
                field=field,
                value=value: mutate_successful_identity_paired(
                    row,
                    field,
                    value,
                )
            )

        for evidence_owner, evidence_key in (
            (
                "retry_history_observation",
                "prior_reservation_postfetch_evidence",
            ),
            (
                "retry_history_observation",
                "prior_disposition_postfetch_evidence",
            ),
            (
                "source_context",
                "successful_reservation_postfetch_evidence",
            ),
        ):
            for mutation_path, value in (
                _COMPLETE_EXACT1_POSTFETCH_MUTATIONS
            ):
                def mutate_retry_postfetch(
                    row: dict[str, Any],
                    evidence_owner: str = evidence_owner,
                    evidence_key: str = evidence_key,
                    mutation_path: tuple[str, ...] = mutation_path,
                    value: Any = value,
                ) -> None:
                    evidence = row[evidence_owner][evidence_key]
                    if type(evidence) is list:
                        evidence = evidence[0]
                    _mutate_complete_exact1_postfetch(
                        evidence,
                        mutation_path,
                        value,
                    )

                variant(mutate_retry_postfetch)

        def mutate_lineage_shape(
            row: dict[str, Any],
            key: str,
        ) -> None:
            accepted = row["accepted_test_run_receipt"]
            lineage = accepted["success_lineage"]
            lineage.pop(key)
            if (
                key != "success_lineage_sha256"
                and "success_lineage_sha256" in lineage
            ):
                lineage["success_lineage_sha256"] = _hash_without(
                    lineage,
                    "success_lineage_sha256",
                )
            accepted["accepted_test_run_receipt_sha256"] = (
                _hash_without(
                    accepted,
                    "accepted_test_run_receipt_sha256",
                )
            )

        for key in sorted(_SUCCESS_LINEAGE_KEYS):
            variant(
                lambda row, key=key: mutate_lineage_shape(row, key)
            )

        def extra_lineage_key(row: dict[str, Any]) -> None:
            accepted = row["accepted_test_run_receipt"]
            lineage = accepted["success_lineage"]
            lineage["unexpected_key"] = "forbidden"
            lineage["success_lineage_sha256"] = _hash_without(
                lineage,
                "success_lineage_sha256",
            )
            accepted["accepted_test_run_receipt_sha256"] = (
                _hash_without(
                    accepted,
                    "accepted_test_run_receipt_sha256",
                )
            )

        variant(extra_lineage_key)

        def corrupt_history_hash(row: dict[str, Any]) -> None:
            accepted = row["accepted_test_run_receipt"]
            lineage = accepted["success_lineage"]
            lineage["prior_reservation_history_sha256"] = "f" * 64
            lineage["success_lineage_sha256"] = _hash_without(
                lineage,
                "success_lineage_sha256",
            )
            accepted["accepted_test_run_receipt_sha256"] = (
                _hash_without(
                    accepted,
                    "accepted_test_run_receipt_sha256",
                )
            )

        variant(corrupt_history_hash)

        def corrupt_lineage_hash(row: dict[str, Any]) -> None:
            accepted = row["accepted_test_run_receipt"]
            accepted["success_lineage"][
                "success_lineage_sha256"
            ] = "f" * 64
            accepted["accepted_test_run_receipt_sha256"] = (
                _hash_without(
                    accepted,
                    "accepted_test_run_receipt_sha256",
                )
            )

        variant(corrupt_lineage_hash)

        unknown_kind_mismatch = _accepted_unknown_prior_state()
        unknown_kind_mismatch["accepted_test_run_receipt"][
            "success_lineage"
        ]["prior_reservation_history"][0][
            "disposition_kind"
        ] = "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
        _rehash_accepted_state(unknown_kind_mismatch)
        variants.append(unknown_kind_mismatch)
        unknown_kind_paired = _accepted_unknown_prior_state()
        unknown_lineage_row = unknown_kind_paired[
            "accepted_test_run_receipt"
        ]["success_lineage"]["prior_reservation_history"][0]
        unknown_lineage_row[
            "disposition_kind"
        ] = "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
        unknown_kind_paired["retry_history_observation"][
            "prior_reservation_history"
        ][0] = deepcopy(unknown_lineage_row)
        _rehash_accepted_state(unknown_kind_paired)
        variants.append(unknown_kind_paired)

        def invalid_two_row_history(
            mutation: str,
        ) -> dict[str, Any]:
            row = _accepted_state_with_history(
                (
                    "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
                    "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
                )
            )
            lineage_history = row["accepted_test_run_receipt"][
                "success_lineage"
            ]["prior_reservation_history"]
            observation = row["retry_history_observation"]
            observed_history = observation[
                "prior_reservation_history"
            ]
            if mutation == "reorder":
                lineage_history.reverse()
                observed_history.reverse()
                observation[
                    "prior_reservation_postfetch_evidence"
                ].reverse()
                observation[
                    "prior_disposition_postfetch_evidence"
                ].reverse()
            elif mutation == "duplicate_attempt":
                lineage_history[1]["attempt_id"] = lineage_history[0][
                    "attempt_id"
                ]
                observed_history[1]["attempt_id"] = observed_history[0][
                    "attempt_id"
                ]
            else:
                duplicate = deepcopy(
                    lineage_history[0]["reservation_artifact"]
                )
                lineage_history[1]["reservation_artifact"] = duplicate
                observed_history[1][
                    "reservation_artifact"
                ] = deepcopy(duplicate)
                old_postfetch = observation[
                    "prior_reservation_postfetch_evidence"
                ][1]
                observation[
                    "prior_reservation_postfetch_evidence"
                ][1] = _single_artifact_postfetch(
                    duplicate,
                    base_commit_sha1=old_postfetch[
                        "publication_parent_commit_sha1s"
                    ][0],
                    base_tree_sha1=old_postfetch["base_tree_sha1"],
                    target_tree_sha1=old_postfetch["target_tree_sha1"],
                )
            _rehash_accepted_state(row)
            return row

        for mutation in (
            "reorder",
            "duplicate_attempt",
            "duplicate_identity",
        ):
            variants.append(invalid_two_row_history(mutation))

        def mutate_observed_prior_body_shape(
            row: dict[str, Any],
            artifact_collection: str,
            key: str | None,
        ) -> None:
            artifact = row["retry_history_observation"][
                artifact_collection
            ][0]
            if key is None:
                artifact["unexpected_key"] = "forbidden"
            else:
                artifact.pop(key)

        for artifact_collection, exact_keys in (
            ("prior_reservation_artifacts", _RESERVATION_KEYS),
            ("prior_disposition_artifacts", _TERMINAL_V2_KEYS),
        ):
            for key in sorted(exact_keys):
                variant(
                    lambda row,
                    artifact_collection=artifact_collection,
                    key=key: mutate_observed_prior_body_shape(
                        row,
                        artifact_collection,
                        key,
                    )
                )
            variant(
                lambda row,
                artifact_collection=artifact_collection: (
                    mutate_observed_prior_body_shape(
                        row,
                        artifact_collection,
                        None,
                    )
                )
            )

        for artifact_collection, field, value in (
            ("prior_reservation_artifacts", "body_free", False),
            (
                "prior_reservation_artifacts",
                "automatic_progression",
                True,
            ),
            (
                "prior_reservation_artifacts",
                "formal_test_run_reservation_sha256",
                "f" * 64,
            ),
            ("prior_disposition_artifacts", "body_free", False),
            (
                "prior_disposition_artifacts",
                "formal_worker_result_sha256",
                "f" * 64,
            ),
        ):
            variant(
                lambda row,
                artifact_collection=artifact_collection,
                field=field,
                value=value: row["retry_history_observation"][
                    artifact_collection
                ][0].__setitem__(field, value)
            )

        unknown_body_baseline = _accepted_unknown_prior_state()
        for key in sorted(_UNKNOWN_DISPOSITION_KEYS):
            unknown_body_variant = deepcopy(unknown_body_baseline)
            unknown_body_variant["retry_history_observation"][
                "prior_disposition_artifacts"
            ][0].pop(key)
            variants.append(unknown_body_variant)
        unknown_body_extra = deepcopy(unknown_body_baseline)
        unknown_body_extra["retry_history_observation"][
            "prior_disposition_artifacts"
        ][0]["unexpected_key"] = "forbidden"
        variants.append(unknown_body_extra)
        for field, value in (
            ("body_free", False),
            ("automatic_retry", True),
            (
                "attempt_consumption_unknown_disposition_sha256",
                "f" * 64,
            ),
        ):
            unknown_body_variant = deepcopy(unknown_body_baseline)
            unknown_body_variant["retry_history_observation"][
                "prior_disposition_artifacts"
            ][0][field] = value
            variants.append(unknown_body_variant)
        return variants
    elif case_id == "A07":
        def mutate_accepted_semantic(
            row: dict[str, Any],
            key: str,
            value: Any,
        ) -> None:
            accepted = row["accepted_test_run_receipt"]
            accepted[key] = value
            accepted["accepted_test_run_receipt_sha256"] = (
                _hash_without(
                    accepted,
                    "accepted_test_run_receipt_sha256",
                )
            )

        variant(
            lambda row: mutate_accepted_semantic(
                row,
                "body_free",
                False,
            )
        )
        variant(
            lambda row: mutate_accepted_semantic(
                row,
                "automatic_progression",
                True,
            )
        )

        def missing_accepted_key(
            row: dict[str, Any],
            key: str,
        ) -> None:
            accepted = row["accepted_test_run_receipt"]
            accepted.pop(key)
            if "accepted_test_run_receipt_sha256" in accepted:
                accepted["accepted_test_run_receipt_sha256"] = (
                    _hash_without(
                        accepted,
                        "accepted_test_run_receipt_sha256",
                    )
                )

        for key in sorted(_ACCEPTED_KEYS):
            variant(
                lambda row, key=key: missing_accepted_key(row, key)
            )

        def extra_accepted_key(row: dict[str, Any]) -> None:
            accepted = row["accepted_test_run_receipt"]
            accepted["unexpected_key"] = "forbidden"
            accepted["accepted_test_run_receipt_sha256"] = (
                _hash_without(
                    accepted,
                    "accepted_test_run_receipt_sha256",
                )
            )

        variant(extra_accepted_key)
        variant(
            lambda row: row["accepted_test_run_receipt"].__setitem__(
                "accepted_test_run_receipt_sha256",
                "f" * 64,
            )
        )
        return variants
    elif case_id == "A08":
        for status in ("UNKNOWN", "PENDING"):
            variant(
                lambda row, status=status: row["source_context"][
                    "readiness_postfetch_evidence"
                ].__setitem__("postfetch_state", status)
            )
        return variants
    elif case_id == "R01":
        state.pop("accepted_test_run_receipt")
    elif case_id == "R02":
        state["receipts"][5], state["receipts"][6] = (
            state["receipts"][6],
            state["receipts"][5],
        )
    elif case_id == "R03":
        state["receipts"][0]["parent_binding"][
            "parent_receipt_sha256"
        ] = "f" * 64
        _rehash_step_chain(
            state,
            start=0,
            preserve_start_parent=True,
        )
    elif case_id == "R04":
        state["receipts"][5]["parent_binding"][
            "parent_receipt_sha256"
        ] = state["receipts"][3]["receipt_sha256"]
        _rehash_step_chain(
            state,
            start=5,
            preserve_start_parent=True,
        )
    elif case_id == "R05":
        state["receipts"][0]["current_binding"][
            "full_graph_sha256"
        ] = "f" * 64
        _rehash_step_chain(
            state,
            start=0,
            preserve_start_parent=False,
        )
    elif case_id == "R06":
        def mutate_owner_contract(
            row: dict[str, Any],
            owner: bool,
        ) -> None:
            receipt = row["receipts"][0]
            if owner:
                receipt["actual_owners"][0]["git_blob_sha1"] = "f" * 40
                receipt["artifact_receipt"][
                    "owner_binding_sha256"
                ] = artifact_sha256(receipt["actual_owners"])
            else:
                receipt["strict_contracts"][0][
                    "validator_blob_sha1"
                ] = "f" * 40
                receipt["artifact_receipt"][
                    "strict_contract_binding_sha256"
                ] = artifact_sha256(receipt["strict_contracts"])
            _rehash_step_chain(
                row,
                start=0,
                preserve_start_parent=False,
            )

        variant(lambda row: mutate_owner_contract(row, True))
        variant(lambda row: mutate_owner_contract(row, False))
        return variants
    elif case_id == "R07":
        proof = state["receipts"][0]["positive_proof"]
        proof["test_node_id"] = "different-positive-node"
        proof["evidence_sha256"] = _hash_without(
            proof,
            "evidence_sha256",
        )
        _rehash_step_chain(
            state,
            start=0,
            preserve_start_parent=False,
        )
    elif case_id == "R08":
        proof = state["receipts"][0]["independent_negative_proof"]
        proof["actual_closed_code"] = None
        proof["evidence_sha256"] = _hash_without(
            proof,
            "evidence_sha256",
        )
        _rehash_step_chain(
            state,
            start=0,
            preserve_start_parent=False,
        )
    elif case_id == "R09":
        all11 = state["all11_completion_chain"]
        all11["receipts"][10] = deepcopy(all11["receipts"][9])
        all11["all11_completion_chain_sha256"] = _hash_without(
            all11,
            "all11_completion_chain_sha256",
        )
    elif case_id == "R10":
        def mutate_r10(
            row: dict[str, Any],
            mutation: str,
        ) -> None:
            if mutation in ("historical", "backfill"):
                key = (
                    "historical_as_current"
                    if mutation == "historical"
                    else "backfill"
                )
                row["receipts"][0]["lineage"][key] = True
                _rehash_step_chain(
                    row,
                    start=0,
                    preserve_start_parent=False,
                )
            else:
                all11 = row["all11_completion_chain"]
                all11["next_authority"] = (
                    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
                    "P2_EXECUTE_SAME_PHASE"
                )
                all11["all11_completion_chain_sha256"] = _hash_without(
                    all11,
                    "all11_completion_chain_sha256",
                )

        for mutation in ("historical", "backfill", "p2"):
            variant(
                lambda row, mutation=mutation: mutate_r10(
                    row,
                    mutation,
                )
            )
        return variants
    elif case_id == "B01":
        state["terminal_commit_observation"]["paths_present"] = [
            _SUCCESS_PATHS[0]
        ]
    elif case_id == "B02":
        manifest = state["atomic_publication_manifest"]
        manifest["core_artifacts"].pop(0)
        manifest["core_artifact_count"] = 12
        manifest["core_artifact_set_sha256"] = artifact_sha256(
            manifest["core_artifacts"]
        )
        manifest["atomic_publication_manifest_sha256"] = _hash_without(
            manifest,
            "atomic_publication_manifest_sha256",
        )
        _refresh_atomic_publication_derived(
            state,
            manifest_changed=True,
        )
    elif case_id == "B03":
        event = state["event2"]
        publication = event["publication"]
        publication["supporting_artifacts"].pop()
        publication["supporting_artifact_count"] = 13
        publication["supporting_artifact_set_sha256"] = artifact_sha256(
            publication["supporting_artifacts"]
        )
        _rehash_event(event)
        _refresh_atomic_publication_derived(
            state,
            manifest_changed=False,
        )
    elif case_id == "B04":
        manifest = state["atomic_publication_manifest"]
        manifest["core_artifact_set_sha256"] = "f" * 64
        manifest["atomic_publication_manifest_sha256"] = _hash_without(
            manifest,
            "atomic_publication_manifest_sha256",
        )
        _refresh_atomic_publication_derived(
            state,
            manifest_changed=True,
        )
    elif case_id == "B05":
        event = state["event2"]
        event["publication"][
            "supporting_artifact_set_sha256"
        ] = "f" * 64
        _rehash_event(event)
        _refresh_atomic_publication_derived(
            state,
            manifest_changed=False,
        )
    elif case_id == "B06":
        event = state["event2"]
        alternate_event = deepcopy(_sequence_state()["event1"])
        alternate_event["timestamp_utc"] = "2026-07-26T12:03:30Z"
        _rehash_event(alternate_event)
        event["prior_event"] = _strict_artifact_external_identity(
            artifact_role="SOURCE_BASELINE_EVENT",
            path=_EVENT1_PATH,
            artifact=alternate_event,
            logical_hash_key="event_sha256",
            publication_commit_sha1="5" * 40,
        )
        _rehash_event(event)
        _refresh_atomic_publication_derived(
            state,
            manifest_changed=False,
        )
    elif case_id == "B07":
        event = state["event2"]
        event["primary_evidence_artifact"] = deepcopy(
            event["publication"]["supporting_artifacts"][0]
        )
        _rehash_event(event)
        _refresh_atomic_publication_derived(
            state,
            manifest_changed=False,
        )
    elif case_id == "B08":
        variant(
            lambda row: row["postfetch_observation"][
                "artifact_raw_sha256_by_path"
            ].pop(
                _SUCCESS_CHANGED_PATHS[-1]
            )
        )
        variant(
            lambda row: row["publication_transaction"][
                "target_blob_sha1_by_path"
            ].pop(
                _SUCCESS_CHANGED_PATHS[-1]
            )
        )
        return variants
    elif case_id == "B09":
        variant(
            lambda row: row["postfetch_observation"].__setitem__(
                "changed_paths",
                list(_SUCCESS_CHANGED_PATHS[:-1]),
            )
        )
        variant(
            lambda row: row["postfetch_observation"][
                "artifact_raw_sha256_by_path"
            ].pop(
                _SUCCESS_CHANGED_PATHS[-1]
            )
        )
        return variants
    elif case_id == "B10":
        variant(
            lambda row: row["postfetch_observation"][
                "owner_issue_codes"
            ].append(
                "OWNER_ISSUE"
            )
        )
        variant(
            lambda row: row["postfetch_observation"].__setitem__(
                "state",
                "FAILED",
            )
        )
        return variants
    elif case_id == "B11":
        variant(
            lambda row: row["publication_transaction"]["write_commits"][0][
                "changed_paths"
            ].append("unapproved/non_target_path.json")
        )
        variant(
            lambda row: row["postfetch_observation"].__setitem__(
                "changed_paths",
                list(_SUCCESS_CHANGED_PATHS[:-1]),
            )
        )
        variant(
            lambda row: row["postfetch_observation"][
                "artifact_git_blob_sha1_by_path"
            ].__setitem__(
                _SUCCESS_CHANGED_PATHS[0],
                "f" * 40,
            )
        )
        variant(
            lambda row: row["postfetch_observation"][
                "independent_issue_codes"
            ].append(
                "INDEPENDENT_ISSUE"
            )
        )
        variant(
            lambda row: row["postfetch_observation"].__setitem__(
                "state",
                "FAILED",
            )
        )
        return variants
    elif case_id == "B12":
        state["publication_transaction"]["ref_update_result"] = "UNKNOWN"
        variant(
            lambda row: row["postfetch_observation"].__setitem__(
                "state",
                "UNKNOWN",
            )
        )
        variant(
            lambda row: row["postfetch_observation"][
                "owner_issue_codes"
            ].append("OWNER_ISSUE")
        )
        variant(
            lambda row: row["postfetch_observation"].__setitem__(
                "changed_paths",
                list(_SUCCESS_CHANGED_PATHS[:-1]),
            )
        )
        variant(
            lambda row: row["postfetch_observation"][
                "artifact_raw_sha256_by_path"
            ].__setitem__(
                _SUCCESS_CHANGED_PATHS[0],
                "f" * 64,
            )
        )
        return variants
    elif case_id == "I01":
        state["verifier_import_violations"].append(
            "FORBIDDEN_OWNER_IMPORT:"
            + Path(
                _ROLE_PATHS["accepted_test_run_receipt_owner"]
            ).stem
        )
    elif case_id == "I02":
        terminal_state = state["terminal_owner_state"]
        terminal_state["terminal_result"].pop(
            "formal_node_outcome_evidence_sha256"
        )
        terminal_state["terminal_result"][
            "formal_worker_result_sha256"
        ] = _hash_without(
            terminal_state["terminal_result"],
            "formal_worker_result_sha256",
        )
    elif case_id == "I03":
        state["accepted_owner_state"]["accepted_test_run_receipt"].pop(
            "proof_source_closure_sha256"
        )
    elif case_id == "I04":
        def mutate_event2_cardinality(row: dict[str, Any]) -> None:
            event = row["publication_owner_state"]["event2"]
            publication = event["publication"]
            publication["supporting_artifacts"].pop()
            publication["supporting_artifact_count"] = 13
            publication["supporting_artifact_set_sha256"] = artifact_sha256(
                publication["supporting_artifacts"]
            )
            _rehash_event(event)
            _refresh_atomic_publication_derived(
                row["publication_owner_state"],
                manifest_changed=False,
            )

        variant(
            mutate_event2_cardinality
        )
        variant(
            lambda row: row["publication_owner_state"][
                "publication_transaction"
            ]["changed_paths"].pop()
        )
        return variants
    elif case_id == "I05":
        def mutate_raw(row: dict[str, Any]) -> None:
            observation = row["publication_owner_state"][
                "postfetch_observation"
            ]
            observation["artifact_raw_sha256_by_path"][
                _ACCEPTED_PATH
            ] = "f" * 64

        variant(mutate_raw)

        def mutate_logical(row: dict[str, Any]) -> None:
            row["publication_owner_state"]["candidate_identities_by_path"][
                _ACCEPTED_PATH
            ]["logical_artifact_sha256"] = "f" * 64

        variant(mutate_logical)
        return variants
    elif case_id == "I06":
        variant(
            lambda row: row["independent_issue_codes"].append(
                "INDEPENDENT_SEMANTIC_ERROR"
            )
        )
        variant(
            lambda row: row.__setitem__("publication_requested", True)
        )
        return variants
    elif case_id == "P01":
        state["phase_order"][-2:] = reversed(state["phase_order"][-2:])
    elif case_id == "P02":
        state["executable_phases"].append("PARENT_SPAWN_INTENT_PERSISTED")
    elif case_id == "P03":
        state["external_ports"].remove("publish_success_exact15")
    elif case_id == "P04":
        variant(lambda row: row.__setitem__("port_call_count", 2))
        variant(lambda row: row.__setitem__("automatic_progression", True))
        return variants
    elif case_id == "P05":
        state["terminal_kind"] = "FAILURE"
        state["terminal_input"] = _parent_valid_terminal_input("FAILURE")
        state["success_exact15_requested"] = False
        state["success_artifact_counts"] = {
            "accepted": 0,
            "step": 0,
            "all11": 0,
            "atomic_manifest": 0,
            "event2": 0,
        }
        state["terminal_stop_code"] = "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
        state["event2_postverified"] = False
        state["step0_10_prerequisites_proved"] = False
        variant(
            lambda row: row.__setitem__(
                "success_exact15_requested",
                True,
            )
        )
        variant(
            lambda row: row.__setitem__("event2_postverified", True)
        )
        variant(
            lambda row: row["success_artifact_counts"].__setitem__(
                "accepted",
                1,
            )
        )
        variant(
            lambda row: row["terminal_input"].__setitem__(
                "tag",
                "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
            )
        )
        variant(
            lambda row: row["terminal_input"].pop(
                "terminal_disposition_postfetch_evidence"
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_disposition_postverified",
                False,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_disposition_artifact_count",
                0,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_stop_code",
                "SUCCESS_TERMINAL_POSTVERIFIED",
            )
        )
        variant(
            lambda row: row["terminal_input"].__setitem__(
                "terminal_kind",
                "SUCCESS",
            )
        )
        for count_key in sorted(_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS):
            variant(
                lambda row, count_key=count_key: row[
                    "success_artifact_counts"
                ].__setitem__(count_key, 1)
            )
        for mutation_path, value in _COMPLETE_EXACT1_POSTFETCH_MUTATIONS:
            variant(
                lambda row,
                mutation_path=mutation_path,
                value=value: _mutate_complete_exact1_postfetch(
                    row["terminal_input"][
                        "terminal_disposition_postfetch_evidence"
                    ],
                    mutation_path,
                    value,
                )
            )
        for field, value in _EXTERNAL_IDENTITY_FIELD_MUTATIONS:
            variant(
                lambda row,
                field=field,
                value=value: _mutate_parent_disposition_identity(
                    row["terminal_input"],
                    field,
                    value,
                )
            )
        return variants
    elif case_id == "P06":
        state["terminal_kind"] = "UNKNOWN"
        state["terminal_input"] = _parent_unknown_disposition_input()
        state["success_exact15_requested"] = False
        state["success_artifact_counts"] = {
            "accepted": 0,
            "step": 0,
            "all11": 0,
            "atomic_manifest": 0,
            "event2": 0,
        }
        state["terminal_stop_code"] = "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
        state["event2_postverified"] = False
        state["step0_10_prerequisites_proved"] = False
        variant(
            lambda row: row.__setitem__("same_attempt_rerun_requested", True)
        )
        variant(
            lambda row: row.__setitem__("synthetic_terminal_requested", True)
        )
        variant(
            lambda row: row.__setitem__(
                "success_exact15_requested",
                True,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_disposition_postverified",
                False,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_disposition_artifact_count",
                0,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_stop_code",
                "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
            )
        )
        variant(
            lambda row: row["success_artifact_counts"].__setitem__(
                "event2",
                1,
            )
        )
        variant(
            lambda row: row["terminal_input"].__setitem__(
                "tag",
                "VALID_TERMINAL_RESULT",
            )
        )
        variant(
            lambda row: row["terminal_input"].pop(
                "terminal_disposition_postfetch_evidence"
            )
        )

        def mutate_unknown_retry(row: dict[str, Any]) -> None:
            row["terminal_input"]["unknown_disposition"][
                "automatic_retry"
            ] = True
            _rebind_parent_unknown_disposition(row)

        variant(mutate_unknown_retry)
        def mutate_unknown_stop(row: dict[str, Any]) -> None:
            row["terminal_input"]["unknown_disposition"][
                "stop_code"
            ] = "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
            _rebind_parent_unknown_disposition(row)

        variant(mutate_unknown_stop)

        def mutate_unknown_keyset(row: dict[str, Any]) -> None:
            row["terminal_input"]["unknown_disposition"].pop(
                "last_valid_stage"
            )
            _rebind_parent_unknown_disposition(row)

        variant(mutate_unknown_keyset)
        variant(
            lambda row: row["terminal_input"][
                "unknown_disposition"
            ].__setitem__(
                "attempt_consumption_unknown_disposition_sha256",
                "f" * 64,
            )
        )
        for count_key in sorted(_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS):
            variant(
                lambda row, count_key=count_key: row[
                    "success_artifact_counts"
                ].__setitem__(count_key, 1)
            )
        for mutation_path, value in _COMPLETE_EXACT1_POSTFETCH_MUTATIONS:
            variant(
                lambda row,
                mutation_path=mutation_path,
                value=value: _mutate_complete_exact1_postfetch(
                    row["terminal_input"][
                        "terminal_disposition_postfetch_evidence"
                    ],
                    mutation_path,
                    value,
                )
            )
        for field, value in _EXTERNAL_IDENTITY_FIELD_MUTATIONS:
            variant(
                lambda row,
                field=field,
                value=value: _mutate_parent_disposition_identity(
                    row["terminal_input"],
                    field,
                    value,
                )
            )
        return variants
    elif case_id == "P07":
        variant(
            lambda row: row.__setitem__(
                "terminal_disposition_postverified", False
            )
        )
        variant(
            lambda row: row.__setitem__(
                "success_exact15_requested",
                False,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "individual_success_artifact_publication_requested",
                True,
            )
        )
        variant(
            lambda row: row["terminal_input"].__setitem__(
                "tag",
                "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
            )
        )
        variant(
            lambda row: row["success_artifact_counts"].__setitem__(
                "step",
                10,
            )
        )
        variant(
            lambda row: row.__setitem__(
                "terminal_disposition_artifact_count",
                0,
            )
        )
        variant(
            lambda row: row["terminal_input"].pop(
                "terminal_disposition_postfetch_evidence"
            )
        )
        variant(
            lambda row: row["terminal_input"].pop("terminal_result")
        )
        variant(
            lambda row: row["terminal_input"].__setitem__(
                "unexpected_key",
                "forbidden",
            )
        )
        for count_key in sorted(_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS):
            expected_count = 11 if count_key == "step" else 1
            variant(
                lambda row,
                count_key=count_key,
                expected_count=expected_count: row[
                    "success_artifact_counts"
                ].__setitem__(count_key, expected_count - 1)
            )
        for mutation_path, value in _COMPLETE_EXACT1_POSTFETCH_MUTATIONS:
            variant(
                lambda row,
                mutation_path=mutation_path,
                value=value: _mutate_complete_exact1_postfetch(
                    row["terminal_input"][
                        "terminal_disposition_postfetch_evidence"
                    ],
                    mutation_path,
                    value,
                )
            )
        for field, value in _EXTERNAL_IDENTITY_FIELD_MUTATIONS:
            variant(
                lambda row,
                field=field,
                value=value: _mutate_parent_disposition_identity(
                    row["terminal_input"],
                    field,
                    value,
                )
            )
        return variants
    elif case_id == "P08":
        variant(lambda row: row.__setitem__("event2_postverified", False))

        def _p2_without_approval(row: dict[str, Any]) -> None:
            row["p2_separate_approval_present"] = False
            row["p2_started"] = True

        variant(_p2_without_approval)
        return variants
    else:
        raise AssertionError(f"unknown successor RED case: {case_id}")
    return [state]


def _issue_codes(value: Any) -> tuple[str, ...]:
    if type(value) not in (tuple, list, set, frozenset):
        return ()
    return tuple(
        sorted(
            row if type(row) is str else str(getattr(row, "code", ""))
            for row in value
        )
    )


_FORBIDDEN_VERIFIER_OWNER_MODULES = frozenset(
    Path(path).stem
    for role, path in _ROLE_PATHS.items()
    if path.endswith(".py") and role != "independent_verifier"
)


def _verifier_import_violations(
    source: str,
    *,
    synthetic_modules: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    synthetic = dict(synthetic_modules or {})
    violations: list[str] = []
    shared_imports: list[str] = []
    visited: set[str] = set()

    def local_source(module_name: str) -> str | None:
        if module_name in synthetic:
            return synthetic[module_name]
        relative = Path(*module_name.split(".")).with_suffix(".py")
        leaf = Path(module_name.rpartition(".")[2] + ".py")
        for root in (
            _REPO_ROOT,
            _AI_ROOT,
            _INFERENCE_ROOT,
            _TOOLS_ROOT,
            _HERE.parent,
        ):
            for candidate in (root / relative, root / leaf):
                if candidate.is_file():
                    return candidate.read_text(encoding="utf-8")
        return None

    def inspect_source(
        module_name: str,
        module_source: str,
        *,
        root_source: bool,
    ) -> None:
        if module_name in visited:
            return
        visited.add(module_name)
        tree = ast.parse(module_source)
        imported_modules: list[str] = []
        importlib_module_aliases = {"importlib"}
        builtins_module_aliases = {"builtins"}
        import_module_function_aliases: set[str] = set()
        builtin_import_aliases = {"__import__"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if (
                        alias.name == "importlib"
                        or alias.name.startswith("importlib.")
                    ):
                        importlib_module_aliases.add(
                            alias.asname
                            or alias.name.partition(".")[0]
                        )
                    if (
                        alias.name == "builtins"
                        or alias.name.startswith("builtins.")
                    ):
                        builtins_module_aliases.add(
                            alias.asname
                            or alias.name.partition(".")[0]
                        )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module == "importlib"
            ):
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_function_aliases.add(
                            alias.asname or alias.name
                        )
            elif (
                isinstance(node, ast.ImportFrom)
                and node.module == "builtins"
            ):
                for alias in node.names:
                    if alias.name == "__import__":
                        builtin_import_aliases.add(
                            alias.asname or alias.name
                        )
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                assigned_value = node.value
                targets = (
                    node.targets
                    if isinstance(node, ast.Assign)
                    else [node.target]
                )
                target_names = [
                    target.id
                    for target in targets
                    if isinstance(target, ast.Name)
                ]
                if (
                    isinstance(assigned_value, ast.Name)
                    and assigned_value.id in builtin_import_aliases
                ):
                    builtin_import_aliases.update(target_names)
                elif (
                    isinstance(assigned_value, ast.Name)
                    and assigned_value.id
                    in import_module_function_aliases
                ):
                    import_module_function_aliases.update(target_names)
                elif (
                    isinstance(assigned_value, ast.Attribute)
                    and isinstance(assigned_value.value, ast.Name)
                    and assigned_value.value.id
                    in importlib_module_aliases
                    and assigned_value.attr == "import_module"
                ):
                    import_module_function_aliases.update(target_names)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_modules.append(node.module or "")
                imported_modules.extend(
                    alias.name for alias in node.names
                )
                module = (node.module or "").rpartition(".")[2]
                if (
                    root_source
                    and module == "emlis_ai_nls_v3_artifact_contract"
                ):
                    shared_imports.extend(
                        alias.name for alias in node.names
                    )
            elif isinstance(node, ast.Call):
                dynamic_name: str | None = None
                if isinstance(node.func, ast.Name) and (
                    node.func.id in builtin_import_aliases
                ):
                    dynamic_name = "__import__"
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in importlib_module_aliases
                    and node.func.attr == "import_module"
                ):
                    dynamic_name = "importlib.import_module"
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in builtins_module_aliases
                    and node.func.attr == "__import__"
                ):
                    dynamic_name = "__import__"
                elif (
                    isinstance(node.func, ast.Name)
                    and node.func.id in import_module_function_aliases
                ):
                    dynamic_name = "import_module"
                if dynamic_name is not None:
                    if (
                        not node.args
                        or not isinstance(node.args[0], ast.Constant)
                        or type(node.args[0].value) is not str
                    ):
                        violations.append("UNRESOLVED_DYNAMIC_IMPORT")
                    else:
                        imported_modules.append(node.args[0].value)
        for imported in imported_modules:
            leaf = imported.rpartition(".")[2]
            if leaf in _FORBIDDEN_VERIFIER_OWNER_MODULES:
                violations.append(f"FORBIDDEN_OWNER_IMPORT:{leaf}")
                continue
            if leaf == "emlis_ai_nls_v3_artifact_contract":
                continue
            dependency_source = local_source(imported)
            if dependency_source is not None:
                inspect_source(
                    imported,
                    dependency_source,
                    root_source=False,
                )
                violations.append(
                    f"FORBIDDEN_LOCAL_HELPER_IMPORT:{leaf}"
                )

    inspect_source(
        "<independent_verifier>",
        source,
        root_source=True,
    )
    if (
        len(shared_imports) != len(_SHARED_PRIMITIVE_ALLOWLIST)
        or frozenset(shared_imports)
        != frozenset(_SHARED_PRIMITIVE_ALLOWLIST)
    ):
        violations.append("SHARED_PRIMITIVE_ALLOWLIST_INVALID")
    return tuple(sorted(set(violations)))


def _single_publication_mutations(
    case_id: str,
) -> list[dict[str, Any]]:
    role = (
        "SUCCESSOR_COMPLETION_RECEIPT"
        if case_id == "C09"
        else "P1_OPERATIONAL_ADMISSION_RECEIPT"
    )
    variants: list[dict[str, Any]] = []

    def target(state: dict[str, Any]) -> dict[str, Any]:
        return next(
            row
            for row in state["exact1_transactions"]
            if row["artifact_role"] == role
        )

    state = _single_publication_state()
    state["supported_roles"].remove(role)
    state["exact1_transactions"] = [
        row
        for row in state["exact1_transactions"]
        if row["artifact_role"] != role
    ]
    variants.append(state)

    for field, value in (
        ("artifact_role", "WRONG_ROLE"),
        ("path", "forbidden/other.json"),
        ("expected_changed_paths", ["forbidden/other.json"]),
        ("head_commit_sha1", "not-a-sha1"),
        ("postfetch_state", "UNKNOWN"),
        ("target_absent_at_base", False),
        ("owner_issue_codes", ["OWNER_ISSUE"]),
        ("independent_issue_codes", ["INDEPENDENT_ISSUE"]),
    ):
        state = _single_publication_state()
        target(state)[field] = value
        variants.append(state)
    state = _single_publication_state()
    other_role = (
        "P1_OPERATIONAL_ADMISSION_RECEIPT"
        if role == "SUCCESSOR_COMPLETION_RECEIPT"
        else "SUCCESSOR_COMPLETION_RECEIPT"
    )
    other_publication = next(
        row["publication"]
        for row in state["exact1_transactions"]
        if row["artifact_role"] == other_role
    )
    target(state)["publication"] = deepcopy(other_publication)
    variants.append(state)

    for key in sorted(
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
    ):
        state = _single_publication_state()
        target(state).pop(key)
        variants.append(state)
    state = _single_publication_state()
    target(state)["unexpected_key"] = "forbidden"
    variants.append(state)

    baseline = _single_publication_state()
    logical_hash_key = (
        "receipt_sha256"
        if role == "SUCCESSOR_COMPLETION_RECEIPT"
        else "operational_admission_sha256"
    )
    variants.extend(
        _exact1_publication_contract_mutations(
            baseline,
            lambda row: target(row)["publication"],
            logical_hash_key=logical_hash_key,
        )
    )
    return variants


def _target_api_or_red(
    role: str,
    case_id: str,
) -> Callable[[Mapping[str, Any]], Any]:
    relative, api_name = _TARGET_APIS[role]
    absolute = _REPO_ROOT / relative
    red = (
        f"{case_id}_RECOVERY_EPOCH002_POST_D2_"
        "SUCCESS_OWNER_GRAPH_NOT_IMPLEMENTED"
    )
    if not absolute.is_file():
        pytest.fail(red, pytrace=False)
    module_name = (
        f"_emlis_nls_v3_recovery_epoch002_post_d2_{role}_"
        f"{case_id.lower()}_target"
    )
    spec = importlib.util.spec_from_file_location(module_name, absolute)
    if spec is None or spec.loader is None:
        pytest.fail(red, pytrace=False)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    for export_name, expected in _REQUIRED_EXPORTS[role].items():
        if not hasattr(module, export_name):
            pytest.fail(red, pytrace=False)
        if getattr(module, export_name) != expected:
            pytest.fail(red, pytrace=False)
    dynamic_exports: dict[str, Any] = {}
    if role == "closure":
        dynamic_exports = {
            "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS": (
                _success_contract_node_ids()
            ),
        }
    elif role in {"terminal", "runner"}:
        dynamic_exports = {
            "RECOVERY_EPOCH002_FORMAL_NODE_IDS": _FORMAL_NODE_IDS,
            "RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE": (
                _NEGATIVE_CLOSED_CODE_BY_NODE
            ),
        }
    for export_name, expected in dynamic_exports.items():
        if not hasattr(module, export_name):
            pytest.fail(red, pytrace=False)
        if getattr(module, export_name) != expected:
            pytest.fail(red, pytrace=False)
    api = getattr(module, api_name, None)
    if not callable(api):
        pytest.fail(red, pytrace=False)
    return api


def _assert_static_contract() -> None:
    assert _AUTHORITY.endswith("REMEDIATION_RED_FREEZE_ONLY")
    assert _FUTURE_P1_AUTHORITY_TOKEN.startswith("FIXTURE_ONLY_UNISSUED_")
    assert _FUTURE_EVENT2_AUTHORITY_TOKEN.startswith(
        "FIXTURE_ONLY_UNISSUED_"
    )
    assert len(
        {
            _AUTHORITY,
            _FUTURE_P1_AUTHORITY_TOKEN,
            _FUTURE_EVENT2_AUTHORITY_TOKEN,
        }
    ) == 3
    assert _PARENT_ADDENDUM_PUBLICATION_COMMIT != _COCOLON_ENTRY
    assert (
        _SYNTHETIC_FRESH_COCOLON_VERIFICATION_COMMIT
        != _PARENT_ADDENDUM_PUBLICATION_COMMIT
    )
    for value in (
        _KAREN_DIARY_ENTRY,
        _COCOLON_ENTRY,
        _MASHOS_API_ENTRY,
        _MASHOS_API_ENTRY_TREE,
        _PARENT_ADDENDUM_BASE_COMMIT,
        _PARENT_ADDENDUM_PUBLICATION_COMMIT,
        _PARENT_ADDENDUM_BLOB,
        _PARENT_ADDENDUM_RECEIPT_BLOB,
    ):
        assert re.fullmatch(r"[0-9a-f]{40}", value)
    for value in (
        _PARENT_ADDENDUM_SHA256,
        _PARENT_ADDENDUM_RECEIPT_SHA256,
        _PARENT_ADDENDUM_RECEIPT_RAW_SHA256,
        _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256,
        _HISTORICAL_D2_FINAL_CLOSURE_SHA256,
        _HISTORICAL_D2_COMPLETION_RECEIPT_SHA256,
        _HISTORICAL_D2_COMPLETION_RECEIPT_RAW_SHA256,
        *_S1_MUTABLE_PROTECTED_SHA256.values(),
        *_S1_INDEPENDENT_NEGATIVE_SHA256.values(),
    ):
        assert re.fullmatch(r"[0-9a-f]{64}", value)
    assert _HERE.relative_to(_REPO_ROOT).as_posix() == _THIS_PATH
    parent_identity = _parent_addendum_external_identity()
    assert set(parent_identity) == _EXTERNAL_IDENTITY_KEYS
    assert parent_identity["path"] == _PARENT_ADDENDUM_RECEIPT_PATH
    assert parent_identity["identity_sha256"] == (
        _PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
    )
    parent_postfetch = _parent_addendum_postfetch_evidence()
    assert parent_postfetch["authoritative_ref_read"] is True
    assert parent_postfetch[
        "publication_reachable_from_verification_ref"
    ] is True
    assert parent_postfetch["publication_parent_commit_sha1s"] == [
        _PARENT_ADDENDUM_BASE_COMMIT
    ]
    assert parent_postfetch["publication_changed_paths"] == list(
        _PARENT_ADDENDUM_CHANGED_PATHS
    )
    assert len(_PARENT_ADDENDUM_CHANGED_PATHS) == 5
    assert parent_postfetch["receipt_at_publication"][
        "trailing_lf_count"
    ] == 1
    assert not parent_postfetch["owner_issue_codes"]
    assert not parent_postfetch["independent_issue_codes"]
    for relative, expected in _PERMANENT_PROTECTED_SHA256.items():
        assert _sha256(_REPO_ROOT / relative) == expected
    for relative, expected in _S1_INDEPENDENT_NEGATIVE_SHA256.items():
        assert _sha256(_REPO_ROOT / relative) == expected
    assert len(_ROLE_BINDINGS) == 15
    assert len(_DISTINCT_OWNER_PATHS) == 12
    assert len(_SUCCESSOR_CLOSURE_KEYS) == 20
    assert len(_SUCCESSOR_COMPLETION_KEYS) == 13
    assert len(_BOOTSTRAP_V2_KEYS) == 31
    assert len(_SUCCESS_OWNER_GRAPH_KEYS) == 6
    assert len(_OWNER_BINDING_KEYS) == 4
    assert len(_SOURCE_FILE_IDENTITY_KEYS) == 3
    assert len(_PROOF_SOURCE_KEYS) == 3
    assert len(_VERIFIER_CONSTRAINT_KEYS) == 5
    assert len(_SUCCESS_CONTRACT_MANIFEST_KEYS) == 8
    assert len(_CANDIDATE_V2_KEYS) == 10
    assert len(_EVENT_V2_KEYS) == 23
    assert len(_EVENT_AUTHORITY_KEYS) == 4
    assert len(
        _EVENT_PUBLICATION_KEYS - _EVENT_PUBLICATION_OPTIONAL_KEYS
    ) == 9
    assert len(_SUCCESS_PUBLICATION_TRANSACTION_REQUIRED_KEYS) == 7
    assert len(_WRITE_COMMIT_KEYS) == 2
    assert len(_TERMINAL_COMMIT_OBSERVATION_KEYS) == 5
    assert len(
        _OPERATIONAL_ADMISSION_KEYS
        - _OPERATIONAL_ADMISSION_OPTIONAL_KEYS
    ) == 18
    assert len(_ADMISSION_AUTHORITY_KEYS) == 4
    assert len(_ADMISSION_SCOPE_KEYS) == 5
    assert len(_ADMISSION_OPERATION_SET) == 11
    assert len(_TERMINAL_V2_KEYS) == 32
    assert len(_EXACT1_PUBLICATION_KEYS) == 9
    assert len(_SINGLE_PUBLICATION_TRANSACTION_KEYS) == 15
    assert len(_OUTCOME_KEYS) == 8
    assert len(_COUNTS_KEYS) == 10
    assert len(_READINESS_KEYS) == 30
    assert len(_RESERVATION_KEYS) == 25
    assert len(_NEGATIVE_CLOSED_CODES) == 11
    assert len(_ACCEPTED_KEYS) == 17
    assert len(_SUCCESS_LINEAGE_KEYS) == 8
    assert len(_PRIOR_RESERVATION_ROW_KEYS) == 5
    assert len(_EXTERNAL_IDENTITY_KEYS) == 10
    assert len(_STEP_KEYS) == 20
    assert len(_STEP_LINEAGE_KEYS) == 5
    assert len(_STEP_CURRENT_BINDING_KEYS) == 15
    assert len(_ACTUAL_OWNER_KEYS) == 5
    assert len(_STRICT_CONTRACT_KEYS) == 6
    assert len(_ARTIFACT_RECEIPT_KEYS) == 9
    assert len(_PARENT_BINDING_KEYS) == 4
    assert len(_COMPLETION_CONDITION_KEYS) == 4
    assert len(_STOP_CONDITION_KEYS) == 6
    assert len(_ALL11_KEYS) == 21
    assert len(_REQUIRED_EVENT2_KEYS) == 5
    assert len(_ATOMIC_MANIFEST_KEYS) == 15
    assert len(_CANDIDATE_IDENTITY_KEYS) == 8
    assert len(_SUCCESS_PATHS) == 15
    assert len(_CORE_PATHS) == 13
    assert len(_EVENT2_SUPPORTING_PATHS) == 14
    assert len(_SUCCESS_CHANGED_PATHS) == 15
    assert _CORE_PATHS == tuple(sorted(_SUCCESS_PATHS[:13]))
    assert _EVENT2_SUPPORTING_PATHS == tuple(
        sorted(_SUCCESS_PATHS[:14])
    )
    assert _SUCCESS_CHANGED_PATHS == tuple(sorted(_SUCCESS_PATHS))
    assert len(set(_SUCCESS_CHANGED_PATHS)) == 15
    assert len(_EXISTING_SINGLE_PUBLICATION_ROLES) == 6
    assert len(_POST_D2_SINGLE_PUBLICATION_ROLES) == 8
    assert _POST_D2_SINGLE_PUBLICATION_ROLES - (
        _EXISTING_SINGLE_PUBLICATION_ROLES
    ) == {
        "SUCCESSOR_COMPLETION_RECEIPT",
        "P1_OPERATIONAL_ADMISSION_RECEIPT",
    }
    assert len(_NEW_SUCCESS_OWNER_PATHS) == 3
    assert len(set(_NEW_SUCCESS_OWNER_PATHS)) == 3
    assert len(_PHASE_ORDER) == 9
    assert len(_EXECUTABLE_PHASES) == 7
    assert len(_EXTERNAL_PORTS) == 7
    assert len(_FORMAL_NODE_IDS) == len(set(_FORMAL_NODE_IDS)) == 134
    assert tuple(
        len(RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step])
        for step in range(11)
    ) == (4, 9, 14, 23, 19, 16, 5, 8, 9, 11, 16)
    assert tuple(_FORMAL_NODE_IDS.index(node) for node in _NEGATIVE_NODE_IDS) == (
        3,
        12,
        26,
        49,
        68,
        84,
        89,
        97,
        106,
        117,
        133,
    )
    assert tuple(
        _NEGATIVE_CLOSED_CODE_BY_NODE[node_id]
        for node_id in _NEGATIVE_NODE_IDS
    ) == _NEGATIVE_CLOSED_CODES
    assert _OBSERVED_NEGATIVE_CLOSED_CODE_BY_NODE == (
        _NEGATIVE_CLOSED_CODE_BY_NODE
    )
    assert set(_S1_INDEPENDENT_NEGATIVE_SHA256) == {
        row["independent_negative_proof"]["source_path"]
        for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
    }
    assert len(_historical_d1_node_ids()) == 46
    assert len(_successor_test_node_ids()) == 64
    assert (
        len(_success_contract_node_ids())
        == len(set(_success_contract_node_ids()))
        == 110
    )
    ids = [row[0] for row in _CASES]
    assert ids == [
        *(f"C{number:02d}" for number in range(1, 11)),
        *(f"T{number:02d}" for number in range(1, 11)),
        *(f"A{number:02d}" for number in range(1, 9)),
        *(f"R{number:02d}" for number in range(1, 11)),
        *(f"B{number:02d}" for number in range(1, 13)),
        *(f"I{number:02d}" for number in range(1, 7)),
        *(f"P{number:02d}" for number in range(1, 9)),
    ]
    assert len(ids) == len(set(ids)) == 64
    expected_names = tuple(
        f"test_{case_id.lower()}_{boundary.lower()}"
        for case_id, boundary, _role, _code in _CASES
    )
    actual_names = tuple(
        name
        for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    )
    assert actual_names == expected_names
    for name in expected_names:
        assert not inspect.signature(globals()[name]).parameters


def _assert_case(case_id: str) -> None:
    _assert_static_contract()
    _case, _boundary, role, expected_code = _CASE_BY_ID[case_id]
    if case_id == "I01":
        verifier_path = _REPO_ROOT / _ROLE_PATHS["independent_verifier"]
        verifier_source = verifier_path.read_text(encoding="utf-8")
        actual_violations = _verifier_import_violations(verifier_source)
        if actual_violations:
            pytest.fail(
                "I01_RECOVERY_EPOCH002_POST_D2_"
                "SUCCESS_OWNER_GRAPH_NOT_IMPLEMENTED",
                pytrace=False,
            )
        synthetic_source = (
            verifier_source
            + "\nfrom "
            + Path(
                _ROLE_PATHS["accepted_test_run_receipt_owner"]
            ).stem
            + " import RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_KEYS\n"
        )
        assert _verifier_import_violations(synthetic_source) == (
            "FORBIDDEN_OWNER_IMPORT:"
            + Path(
                _ROLE_PATHS["accepted_test_run_receipt_owner"]
            ).stem,
        )
        package_synthetic_source = (
            verifier_source
            + "\nfrom ai.services.ai_inference import "
            + Path(
                _ROLE_PATHS["accepted_test_run_receipt_owner"]
            ).stem
            + "\n"
        )
        assert _verifier_import_violations(
            package_synthetic_source
        ) == (
            "FORBIDDEN_OWNER_IMPORT:"
            + Path(
                _ROLE_PATHS["accepted_test_run_receipt_owner"]
            ).stem,
        )
        forbidden_owner = Path(
            _ROLE_PATHS["accepted_test_run_receipt_owner"]
        ).stem
        literal_dynamic_source = (
            verifier_source
            + "\nimport importlib\n"
            + f'importlib.import_module("{forbidden_owner}")\n'
        )
        assert _verifier_import_violations(
            literal_dynamic_source
        ) == (f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",)
        importlib_alias_source = (
            verifier_source
            + "\nimport importlib as dynamic_loader\n"
            + (
                "dynamic_loader.import_module"
                f'("{forbidden_owner}")\n'
            )
        )
        assert _verifier_import_violations(
            importlib_alias_source
        ) == (f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",)
        imported_function_source = (
            verifier_source
            + "\nfrom importlib import import_module as load_module\n"
            + f'load_module("{forbidden_owner}")\n'
        )
        assert _verifier_import_violations(
            imported_function_source
        ) == (f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",)
        rebound_builtin_source = (
            verifier_source
            + "\ndynamic_import = __import__\n"
            + f'dynamic_import("{forbidden_owner}")\n'
        )
        assert _verifier_import_violations(
            rebound_builtin_source
        ) == (f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",)
        imported_builtin_source = (
            verifier_source
            + "\nfrom builtins import __import__ as load_module\n"
            + f'load_module("{forbidden_owner}")\n'
        )
        assert _verifier_import_violations(
            imported_builtin_source
        ) == (f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",)
        builtins_alias_source = (
            verifier_source
            + "\nimport builtins as builtin_namespace\n"
            + (
                "builtin_namespace.__import__"
                f'("{forbidden_owner}")\n'
            )
        )
        assert _verifier_import_violations(
            builtins_alias_source
        ) == (f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",)
        unresolved_builtin_source = (
            verifier_source
            + "\nfrom builtins import __import__ as load_module\n"
            + 'module_name = "runtime_selected_module"\n'
            + "load_module(module_name)\n"
        )
        assert _verifier_import_violations(
            unresolved_builtin_source
        ) == ("UNRESOLVED_DYNAMIC_IMPORT",)
        unresolved_dynamic_source = (
            verifier_source
            + "\nimport importlib\n"
            + 'module_name = "runtime_selected_module"\n'
            + "importlib.import_module(module_name)\n"
        )
        assert _verifier_import_violations(
            unresolved_dynamic_source
        ) == ("UNRESOLVED_DYNAMIC_IMPORT",)
        transitive_source = verifier_source + "\nimport verifier_bridge\n"
        assert _verifier_import_violations(
            transitive_source,
            synthetic_modules={
                "verifier_bridge": (
                    f"from {forbidden_owner} import OWNER_API\n"
                )
            },
        ) == (
            "FORBIDDEN_LOCAL_HELPER_IMPORT:verifier_bridge",
            f"FORBIDDEN_OWNER_IMPORT:{forbidden_owner}",
        )
        assert _verifier_import_violations(
            transitive_source,
            synthetic_modules={"verifier_bridge": "LOCAL_COPY = True\n"},
        ) == ("FORBIDDEN_LOCAL_HELPER_IMPORT:verifier_bridge",)
    api = _target_api_or_red(role, case_id)
    baseline = _STATE_FACTORIES[role]()
    assert _issue_codes(api(deepcopy(baseline))) == (), (
        case_id,
        "canonical baseline must be accepted before mutation",
    )
    mutations = _mutated_states(case_id, role)
    assert mutations
    for mutation in mutations:
        assert _issue_codes(api(deepcopy(mutation))) == (expected_code,), (
            case_id,
            expected_code,
        )
    if case_id == "B08":
        multi_write = _publication_state()
        writes = [
            {
                "commit_sha1": "6" * 40,
                "changed_paths": list(_SUCCESS_CHANGED_PATHS[:7]),
            },
            {
                "commit_sha1": "7" * 40,
                "changed_paths": list(_SUCCESS_CHANGED_PATHS[7:]),
            },
        ]
        _set_publication_write_commits(multi_write, writes)
        assert _issue_codes(api(deepcopy(multi_write))) == ()
        assert len(
            {
                identity["publication_commit_sha1"]
                for identity in multi_write["postfetch_observation"][
                    "publication_external_identities"
                ]
            }
        ) == 2
        independent_multi_write = _independent_state()
        _set_publication_write_commits(
            independent_multi_write["publication_owner_state"],
            writes,
        )
        independent_api = _target_api_or_red("independent", case_id)
        assert _issue_codes(
            independent_api(deepcopy(independent_multi_write))
        ) == ()
    if case_id == "B09":
        head_drift = _publication_state()
        head_drift["publication_transaction"]["parent_commit_sha1s"] = [
            "f" * 40
        ]
        head_drift["publication_transaction"][
            "requested_expected_old_sha1"
        ] = "e" * 40
        head_drift["publication_transaction"]["observed_old_sha1"] = (
            "d" * 40
        )
        head_drift["postfetch_observation"]["parent_commit_sha1s"] = [
            "f" * 40
        ]
        head_drift["postfetch_observation"]["head_commit_sha1"] = "9" * 40
        assert _issue_codes(api(deepcopy(head_drift))) == ()
    if case_id == "B10":
        ordinary_transport = _publication_state()
        transaction = ordinary_transport["publication_transaction"]
        for key in tuple(transaction):
            if key not in _SUCCESS_PUBLICATION_TRANSACTION_REQUIRED_KEYS:
                transaction.pop(key)
        assert "transaction_capability" not in ordinary_transport[
            "event2"
        ]["publication"]
        assert "ref_update_mode" not in ordinary_transport[
            "event2"
        ]["publication"]
        assert "ref_update_mode" not in ordinary_transport[
            "atomic_publication_manifest"
        ]
        assert _issue_codes(api(deepcopy(ordinary_transport))) == ()
    if case_id == "C10":
        ordinary_sequence = _sequence_state()
        admission = ordinary_sequence["operational_admission_receipt"]
        assert "transport_capability" not in admission
        assert "durable_store_capability" not in admission
        _rebind_completion_chain(
            ordinary_sequence,
            deepcopy(ordinary_sequence["successor_completion_receipt"]),
        )
        event = ordinary_sequence["event1"]
        assert "transaction_capability" not in event["publication"]
        assert "ref_update_mode" not in event["publication"]
        for publication_key in (
            "successor_completion_publication",
            "operational_admission_publication",
            "event1_publication",
        ):
            publication = ordinary_sequence[publication_key]
            publication["parent_commit_sha1s"] = ["f" * 40]
            publication["expected_old_sha1"] = "e" * 40
            publication["observed_old_sha1"] = "d" * 40
            postfetch = publication["postfetch_evidence"]
            postfetch["authoritative_recursive_tree_read"] = False
            postfetch["unchanged_path_mismatches"] = [
                "unrelated/non_target_path"
            ]
        assert _issue_codes(api(deepcopy(ordinary_sequence))) == ()
        independent_api = _target_api_or_red("independent", case_id)
        assert _issue_codes(
            independent_api(deepcopy(_independent_state()))
        ) == ()

        def sequence_postfetches(
            sequence_state: dict[str, Any],
        ) -> tuple[dict[str, Any], ...]:
            return (
                sequence_state["causal_red_postfetch_evidence"],
                sequence_state["combined_green_postfetch_evidence"],
                sequence_state["successor_completion_publication"][
                    "postfetch_evidence"
                ],
                sequence_state["operational_admission_publication"][
                    "postfetch_evidence"
                ],
                sequence_state["event1_publication"][
                    "postfetch_evidence"
                ],
            )

        def assert_sequence_owner_and_independent(
            sequence_state: dict[str, Any],
        ) -> None:
            assert _issue_codes(api(deepcopy(sequence_state))) == ()
            independent_state = _independent_state()
            independent_state[
                "successor_succession_owner_state"
            ] = deepcopy(sequence_state)
            assert _issue_codes(
                independent_api(deepcopy(independent_state))
            ) == ()

        transport_metadata_absent = _sequence_state()
        for publication_key in (
            "successor_completion_publication",
            "operational_admission_publication",
            "event1_publication",
        ):
            publication = transport_metadata_absent[publication_key]
            for key in (
                "parent_commit_sha1s",
                "expected_old_sha1",
                "observed_old_sha1",
            ):
                publication.pop(key)
        required_postfetch_keys = {
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
        }
        for postfetch in sequence_postfetches(
            transport_metadata_absent
        ):
            for key in tuple(postfetch):
                if key not in required_postfetch_keys:
                    postfetch.pop(key)
        assert_sequence_owner_and_independent(
            transport_metadata_absent
        )

        arbitrary_tree_metadata = _sequence_state()
        for postfetch in sequence_postfetches(arbitrary_tree_metadata):
            postfetch["base_tree_sha1"] = "f" * 40
            postfetch["target_tree_sha1"] = "f" * 40
        assert_sequence_owner_and_independent(arbitrary_tree_metadata)

        published = _current_published_artifact_state()
        assert (
            published["postfetch_commit_sha1"]
            != published["artifact_external_identity"][
                "publication_commit_sha1"
            ]
        )
        assert verify_recovery_epoch002_published_artifact(
            deepcopy(published)
        ) == ()

        bytes_mutated = deepcopy(published)
        bytes_mutated["artifact"]["candidate_version_id"] = (
            "different_candidate"
        )
        assert verify_recovery_epoch002_published_artifact(
            bytes_mutated
        ) == ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)

        hash_mutated = deepcopy(published)
        hash_mutated["postfetch_git_blob_sha1"] = "0" * 40
        assert verify_recovery_epoch002_published_artifact(
            hash_mutated
        ) == ("PUBLISHED_ARTIFACT_IDENTITY_MISMATCH",)

        path_mutated = deepcopy(published)
        path_mutated["changed_paths"] = ["forbidden/other.json"]
        path_mutated["expected_changed_paths"] = [
            "forbidden/other.json"
        ]
        assert verify_recovery_epoch002_published_artifact(
            path_mutated
        ) == ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)
    independent_replay_contracts = {
        "I02": tuple(
            (f"T{number:02d}", "terminal_owner_state")
            for number in range(1, 11)
        ),
        "I03": (
            *(
                (f"A{number:02d}", "accepted_owner_state")
                for number in range(1, 9)
            ),
            *(
                (f"R{number:02d}", "step_owner_state")
                for number in range(1, 9)
            ),
            ("R09", "all11_owner_state"),
            ("R10", "all11_owner_state"),
        ),
        "I04": tuple(
            (f"B{number:02d}", "publication_owner_state")
            for number in range(2, 8)
        ),
        "I05": (
            ("B01", "publication_owner_state"),
            *(
                (f"B{number:02d}", "publication_owner_state")
                for number in range(8, 13)
            ),
        ),
    }
    if case_id in independent_replay_contracts:
        independent_baseline = _independent_state()
        for owner_case_id, owner_state_key in (
            independent_replay_contracts[case_id]
        ):
            owner_role = _CASE_BY_ID[owner_case_id][2]
            for owner_mutation in _mutated_states(
                owner_case_id,
                owner_role,
            ):
                independent_replay = deepcopy(independent_baseline)
                independent_replay[owner_state_key] = owner_mutation
                assert _issue_codes(
                    api(deepcopy(independent_replay))
                ) == (expected_code,), (
                    case_id,
                    owner_case_id,
                    "independent verifier must replay owner negatives",
                )
    if case_id == "C06":
        secondary_contracts = (
            ("sequence", _c06_sequence_mutations),
            ("independent", _c06_independent_mutations),
        )
        for secondary_role, mutation_factory in secondary_contracts:
            secondary_api = _target_api_or_red(
                secondary_role,
                case_id,
            )
            secondary_baseline = _STATE_FACTORIES[secondary_role]()
            assert _issue_codes(
                secondary_api(deepcopy(secondary_baseline))
            ) == (), (
                case_id,
                secondary_role,
                "Parent Addendum full-identity baseline must be accepted",
            )
            for secondary_mutation in mutation_factory():
                assert _issue_codes(
                    secondary_api(deepcopy(secondary_mutation))
                ) == (expected_code,), (
                    case_id,
                    secondary_role,
                    expected_code,
                )
    if case_id == "A06":
        valid_unknown = _accepted_unknown_prior_state()
        valid_history_states = (
            _accepted_state_with_history(()),
            valid_unknown,
            _accepted_state_with_history(
                (
                    "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
                    "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
                )
            ),
            *_accepted_role_alias_states(),
        )
        for valid_history in valid_history_states:
            assert _issue_codes(api(deepcopy(valid_history))) == (), (
                case_id,
                "valid zero/unknown/multi-row lineage must be accepted",
            )
        independent_api = _target_api_or_red(
            "independent",
            case_id,
        )
        independent_baseline = _independent_state()
        assert _issue_codes(
            independent_api(deepcopy(independent_baseline))
        ) == (), (
            case_id,
            "independent accepted baseline must be accepted",
        )

        def accepted_postfetches(
            accepted_state: dict[str, Any],
        ) -> tuple[dict[str, Any], ...]:
            context = accepted_state["source_context"]
            observation = accepted_state[
                "retry_history_observation"
            ]
            return (
                accepted_state["terminal_publication"][
                    "postfetch_evidence"
                ],
                context["event1_postfetch_evidence"],
                context["readiness_postfetch_evidence"],
                context["successful_reservation_postfetch_evidence"],
                *observation[
                    "prior_reservation_postfetch_evidence"
                ],
                *observation[
                    "prior_disposition_postfetch_evidence"
                ],
            )

        def assert_accepted_owner_and_independent(
            accepted_state: dict[str, Any],
        ) -> None:
            assert _issue_codes(api(deepcopy(accepted_state))) == ()
            assert _issue_codes(
                independent_api(
                    deepcopy(_independent_state(accepted_state))
                )
            ) == ()

        accepted_without_tree_metadata = _accepted_state()
        for postfetch in accepted_postfetches(
            accepted_without_tree_metadata
        ):
            postfetch.pop("base_tree_sha1", None)
            postfetch.pop("target_tree_sha1", None)
        assert_accepted_owner_and_independent(
            accepted_without_tree_metadata
        )

        accepted_with_arbitrary_tree_metadata = _accepted_state()
        for postfetch in accepted_postfetches(
            accepted_with_arbitrary_tree_metadata
        ):
            postfetch["base_tree_sha1"] = "f" * 40
            postfetch["target_tree_sha1"] = "f" * 40
        assert_accepted_owner_and_independent(
            accepted_with_arbitrary_tree_metadata
        )

        terminal_head_drift = _accepted_state()
        for publication in (
            terminal_head_drift["terminal_publication"],
            terminal_head_drift["terminal_owner_state"][
                "terminal_publication"
            ],
        ):
            publication["parent_commit_sha1s"] = ["a" * 40]
            publication["expected_old_sha1"] = "a" * 40
            publication["observed_old_sha1"] = "a" * 40
            postfetch = publication["postfetch_evidence"]
            postfetch["publication_parent_commit_sha1s"] = [
                "a" * 40
            ]
            postfetch["base_tree_sha1"] = "b" * 40
        assert _issue_codes(api(deepcopy(terminal_head_drift))) == ()
        assert _issue_codes(
            independent_api(
                deepcopy(_independent_state(terminal_head_drift))
            )
        ) == ()

        for mutation_kind in ("bytes", "hash", "path"):
            terminal_mutated = deepcopy(terminal_head_drift)
            for publication in (
                terminal_mutated["terminal_publication"],
                terminal_mutated["terminal_owner_state"][
                    "terminal_publication"
                ],
            ):
                if mutation_kind == "bytes":
                    publication["artifact"]["attempt_id"] = "0" * 64
                else:
                    artifact_at_head = publication[
                        "postfetch_evidence"
                    ]["artifact_at_verification_ref"]
                    if mutation_kind == "hash":
                        artifact_at_head["raw_sha256"] = "0" * 64
                    else:
                        artifact_at_head["path"] = (
                            "forbidden/other.json"
                        )
            assert _issue_codes(
                api(deepcopy(terminal_mutated))
            ) == ("POSTVERIFIED_TERMINAL_REQUIRED",)
            assert _issue_codes(
                independent_api(
                    deepcopy(_independent_state(terminal_mutated))
                )
            ) == ("INDEPENDENT_TERMINAL_SCHEMA_INVALID",)
        for valid_history in valid_history_states:
            independent_valid = _independent_state(valid_history)
            assert _issue_codes(
                independent_api(deepcopy(independent_valid))
            ) == (), (
                case_id,
                "independent valid history variant must be accepted",
            )
    if case_id == "B12":
        unknown_but_reconciled = _publication_state()
        unknown_but_reconciled["publication_transaction"][
            "ref_update_result"
        ] = "UNKNOWN"
        assert _issue_codes(
            api(deepcopy(unknown_but_reconciled))
        ) == (), (
            case_id,
            "same frozen success commit must be reconcilable after UNKNOWN",
        )
        not_applied = _publication_state()
        not_applied["publication_transaction"]["ref_update_result"] = (
            "NOT_APPLIED"
        )
        assert _issue_codes(api(deepcopy(not_applied))) == (
            "SUCCESS_PUBLICATION_NOT_APPLIED_STOP",
        )
        failed = _publication_state()
        failed["publication_transaction"]["ref_update_result"] = "FAILED"
        assert _issue_codes(api(deepcopy(failed))) == (
            "SUCCESS_PUBLICATION_WRITE_FAILED_STOP",
        )
    if case_id == "I05":
        independent_head_drift = _independent_state()
        independent_head_drift["publication_owner_state"][
            "postfetch_observation"
        ]["parent_commit_sha1s"] = ["f" * 40]
        assert _issue_codes(
            api(deepcopy(independent_head_drift))
        ) == ()
        independent_unknown_reconciled = _independent_state()
        independent_unknown_reconciled["publication_owner_state"][
            "publication_transaction"
        ]["ref_update_result"] = "UNKNOWN"
        assert _issue_codes(
            api(deepcopy(independent_unknown_reconciled))
        ) == (), (
            case_id,
            "independent verifier must accept reconciled UNKNOWN on same S",
        )
    if case_id in {"C09", "C10"}:
        independent_api = _target_api_or_red(
            "independent",
            case_id,
        )
        independent_baseline = _independent_state()
        assert _issue_codes(
            independent_api(deepcopy(independent_baseline))
        ) == (), (
            case_id,
            "independent succession baseline must be accepted",
        )
        for independent_mutation in _independent_succession_mutations(
            case_id
        ):
            assert _issue_codes(
                independent_api(deepcopy(independent_mutation))
            ) == (expected_code,), (
                case_id,
                "independent succession verification must be causal",
            )
        publisher_api = _target_api_or_red(
            "single_publication",
            case_id,
        )
        publisher_baseline = _single_publication_state()
        assert _issue_codes(
            publisher_api(deepcopy(publisher_baseline))
        ) == (), (
            case_id,
            "publisher additive exact1 role baseline must be accepted",
        )
        publisher_head_drift = _single_publication_state()
        target_role = (
            "SUCCESSOR_COMPLETION_RECEIPT"
            if case_id == "C09"
            else "P1_OPERATIONAL_ADMISSION_RECEIPT"
        )
        drifted_transaction = next(
            row
            for row in publisher_head_drift["exact1_transactions"]
            if row["artifact_role"] == target_role
        )
        drifted_transaction["head_commit_sha1"] = "f" * 40
        assert (
            drifted_transaction["head_commit_sha1"]
            != drifted_transaction["publication"]["identity"][
                "publication_commit_sha1"
            ]
        )
        assert _issue_codes(
            publisher_api(deepcopy(publisher_head_drift))
        ) == ()
        for publisher_index, publisher_mutation in enumerate(
            _single_publication_mutations(case_id)
        ):
            assert _issue_codes(
                publisher_api(deepcopy(publisher_mutation))
            ) == (expected_code,), (
                case_id,
                publisher_index,
                "publisher additive exact1 role must be causal",
            )


def test_c01_historical_d2_immutable() -> None:
    _assert_case("C01")


def test_c02_successor_closure_exact20() -> None:
    _assert_case("C02")


def test_c03_final_source_commit_tree_bound() -> None:
    _assert_case("C03")


def test_c04_d2_closure_ancestor_bound() -> None:
    _assert_case("C04")


def test_c05_d2_receipt_identity_bound() -> None:
    _assert_case("C05")


def test_c06_parent_addendum_identity_bound() -> None:
    _assert_case("C06")


def test_c07_success_owner_graph_exact15_role12_path() -> None:
    _assert_case("C07")


def test_c08_success_contract_test_manifest_bound() -> None:
    _assert_case("C08")


def test_c09_completion_receipt_red_green_bound() -> None:
    _assert_case("C09")
    expected_code = "SUCCESSOR_COMPLETION_EVIDENCE_BINDING_INVALID"
    historical_test_identity = {
        "path": _THIS_PATH,
        "git_blob_sha1": "1616de8b9f738b7037b6e18a64113280fa6ec478",
        "raw_sha256": (
            "3e5cdcd5c2cd2113f273f6cc1a43ff09bdd4845b14cd7aea"
            "49237d26cfc0753b"
        ),
    }
    current_test_identity = _source_file_identity(_THIS_PATH)
    assert historical_test_identity["path"] == current_test_identity["path"]
    assert historical_test_identity != current_test_identity

    def actual_s1_state() -> dict[str, Any]:
        state = _sequence_state()
        causal_red = deepcopy(state["causal_red_evidence_artifact"])
        causal_red["successor_test_file"] = deepcopy(
            historical_test_identity
        )
        state["causal_red_evidence"]["publication_commit_sha1"] = (
            "a45a958cab1a5e1d052e6b470dd26d8e19764b7b"
        )
        _rebind_successor_evidence(
            state,
            evidence_kind="causal_red",
            artifact=causal_red,
        )
        actual_artifact = state["causal_red_evidence_artifact"]
        actual_identity = state["causal_red_evidence"]
        assert actual_artifact["receipt_sha256"] == (
            "7b3b6d0890038642d69feb18e46630fbf97a5918fe0e95db"
            "766b8c8175e2d179"
        )
        assert actual_identity["git_blob_sha1"] == (
            "fa2ac8978294e9eb92211147c09989ae7583455e"
        )
        assert actual_identity["raw_sha256"] == (
            "f03bf71f267813d25664ceacd1344d74fb354156a9c65b19c"
            "14a3c7f315e4c03"
        )
        assert actual_identity["identity_sha256"] == (
            "1504bf4f58ca02b76df7f0a9fd6f88a429b01a56c59b7a90"
            "82648a25fb3614b4"
        )
        combined_green = deepcopy(
            state["combined_green_evidence_artifact"]
        )
        combined_green["causal_red_evidence_sha256"] = actual_identity[
            "logical_artifact_sha256"
        ]
        _rebind_successor_evidence(
            state,
            evidence_kind="combined_green",
            artifact=combined_green,
        )
        return state

    def current_active_test_identity_substitution() -> dict[str, Any]:
        state = actual_s1_state()
        causal_red = deepcopy(state["causal_red_evidence_artifact"])
        causal_red["successor_test_file"] = deepcopy(
            current_test_identity
        )
        _rebind_successor_evidence(
            state,
            evidence_kind="causal_red",
            artifact=causal_red,
        )
        combined_green = deepcopy(
            state["combined_green_evidence_artifact"]
        )
        combined_green["causal_red_evidence_sha256"] = state[
            "causal_red_evidence"
        ]["logical_artifact_sha256"]
        _rebind_successor_evidence(
            state,
            evidence_kind="combined_green",
            artifact=combined_green,
        )
        return state

    def nonmanifest_exact110_substitution(
        state: dict[str, Any],
    ) -> dict[str, Any]:
        state = deepcopy(state)
        combined_green = deepcopy(
            state["combined_green_evidence_artifact"]
        )
        node_ids = list(combined_green["test_node_ids"])
        nonmanifest_node = (
            f"{_THIS_PATH}::c09_unique_non_manifest_exact110"
        )
        assert nonmanifest_node not in _success_contract_node_ids()
        node_ids[-1] = nonmanifest_node
        assert len(node_ids) == len(set(node_ids)) == 110
        combined_green["test_node_ids"] = node_ids
        combined_green["executed_node_ids"] = list(node_ids)
        combined_green["outcome_states"] = {
            node_id: "PASSED" for node_id in node_ids
        }
        _rebind_successor_evidence(
            state,
            evidence_kind="combined_green",
            artifact=combined_green,
        )
        return state

    owner_api = _target_api_or_red("sequence", "C09")
    independent_api = _target_api_or_red("independent", "C09")

    def observe(state: dict[str, Any]) -> dict[str, tuple[str, ...]]:
        independent_state = _independent_state()
        independent_state["successor_succession_owner_state"] = deepcopy(
            state
        )
        return {
            "owner": _issue_codes(owner_api(deepcopy(state))),
            "independent": _issue_codes(
                independent_api(independent_state)
            ),
        }

    observed = {
        "actual_published_s1": observe(actual_s1_state()),
        "current_active_test_identity_substitution": observe(
            current_active_test_identity_substitution()
        ),
        "nonmanifest_exact110_from_actual_s1": observe(
            nonmanifest_exact110_substitution(actual_s1_state())
        ),
        "nonmanifest_exact110_from_current_active_substitution": observe(
            nonmanifest_exact110_substitution(
                current_active_test_identity_substitution()
            )
        ),
    }
    assert observed == {
        "actual_published_s1": {
            "owner": (),
            "independent": (),
        },
        "current_active_test_identity_substitution": {
            "owner": (expected_code,),
            "independent": (expected_code,),
        },
        "nonmanifest_exact110_from_actual_s1": {
            "owner": (expected_code,),
            "independent": (expected_code,),
        },
        "nonmanifest_exact110_from_current_active_substitution": {
            "owner": (expected_code,),
            "independent": (expected_code,),
        },
    }, (
        "C09",
        "actual S1 identity and exact110 manifest parity must be causal",
        observed,
    )


def test_c10_allocation_event1_owner_authority_and_current_reflection_contract() -> None:
    _assert_case("C10")


def test_t01_terminal_v2_exact32() -> None:
    _assert_case("T01")


def test_t02_collection_exact134_registry_order() -> None:
    _assert_case("T02")


def test_t03_execution_exact134_registry_order() -> None:
    _assert_case("T03")


def test_t04_outcome_row_exact8() -> None:
    _assert_case("T04")


def test_t05_pinned_source_identity_per_node() -> None:
    _assert_case("T05")


def test_t06_expected_closed_code_exact11() -> None:
    _assert_case("T06")


def test_t07_actual_closed_code_observed_exact11() -> None:
    _assert_case("T07")


def test_t08_counts_exact10_states_parity() -> None:
    _assert_case("T08")


def test_t09_terminal_success_predicate_exact() -> None:
    _assert_case("T09")


def test_t10_terminal_target_content_postverified() -> None:
    _assert_case("T10")


def test_a01_postverified_terminal_required() -> None:
    _assert_case("A01")


def test_a02_terminal_all_success_only() -> None:
    _assert_case("A02")


def test_a03_formal_invocation_exact1() -> None:
    _assert_case("A03")


def test_a04_source_runtime_bootstrap_parity() -> None:
    _assert_case("A04")


def test_a05_event_readiness_reservation_parity() -> None:
    _assert_case("A05")


def test_a06_complete_retry_history_bound() -> None:
    _assert_case("A06")


def test_a07_accepted_body_free_self_hash() -> None:
    _assert_case("A07")


def test_a08_uncertainty_accepted_exact0() -> None:
    _assert_case("A08")


def test_r01_accepted_receipt_required() -> None:
    _assert_case("R01")


def test_r02_step_receipt_exact11_ordered() -> None:
    _assert_case("R02")


def test_r03_step00_event1_accepted_bind() -> None:
    _assert_case("R03")


def test_r04_step01_10_immediate_parent_chain() -> None:
    _assert_case("R04")


def test_r05_current_source_view_root_bind() -> None:
    _assert_case("R05")


def test_r06_actual_owner_strict_contract_bind() -> None:
    _assert_case("R06")


def test_r07_positive_proof_outcome_bind() -> None:
    _assert_case("R07")


def test_r08_negative_proof_observed_code_bind() -> None:
    _assert_case("R08")


def test_r09_all11_accepted_and_exact11_bind() -> None:
    _assert_case("R09")


def test_r10_no_epoch001_credit_backfill_or_p2() -> None:
    _assert_case("R10")


def test_b01_success_paths_exact15_absent_at_t() -> None:
    _assert_case("B01")


def test_b02_core_artifacts_exact13() -> None:
    _assert_case("B02")


def test_b03_supporting_artifacts_exact14() -> None:
    _assert_case("B03")


def test_b04_manifest_core_set_hash() -> None:
    _assert_case("B04")


def test_b05_event2_support_set_hash() -> None:
    _assert_case("B05")


def test_b06_event2_event1_ancestry() -> None:
    _assert_case("B06")


def test_b07_event2_terminal_success_lineage() -> None:
    _assert_case("B07")


def test_b08_multiple_write_operations_allowed() -> None:
    _assert_case("B08")


def test_b09_nonconflicting_head_drift_allowed() -> None:
    _assert_case("B09")


def test_b10_special_transport_non_normative() -> None:
    _assert_case("B10")


def test_b11_target_scoped_postverify() -> None:
    _assert_case("B11")


def test_b12_unknown_result_refetch_before_retry() -> None:
    _assert_case("B12")


def test_i01_verifier_owner_import_split() -> None:
    _assert_case("I01")


def test_i02_terminal_schema_independent() -> None:
    _assert_case("I02")


def test_i03_accepted_step_all11_independent() -> None:
    _assert_case("I03")


def test_i04_event2_exact14_15_independent() -> None:
    _assert_case("I04")


def test_i05_target_bytes_hashes_and_scope_independent() -> None:
    _assert_case("I05")


def test_i06_owner_verifier_disagreement_stop() -> None:
    _assert_case("I06")


def test_p01_formal_parent_phase_order_exact9() -> None:
    _assert_case("P01")


def test_p02_executable_phases_exact7() -> None:
    _assert_case("P02")


def test_p03_external_ports_exact7() -> None:
    _assert_case("P03")


def test_p04_one_port_call_no_autoprogression() -> None:
    _assert_case("P04")


def test_p05_failure_terminal_publication_stop() -> None:
    _assert_case("P05")


def test_p06_unknown_disposition_no_rerun() -> None:
    _assert_case("P06")


def test_p07_success_terminal_then_exact15_only() -> None:
    _assert_case("P07")


def test_p08_event2_postverify_step_proved_p2_stop() -> None:
    _assert_case("P08")
