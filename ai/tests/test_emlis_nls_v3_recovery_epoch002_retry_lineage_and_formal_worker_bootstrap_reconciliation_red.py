# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for the Recovery Epoch 002 lineage/bootstrap repair.

This file is the complete D1 oracle.  It freezes the append-only retry
lineage, pre-reservation bootstrap readiness, durable checkpoint, body-free
diagnostic, and publication-reconciliation boundary described by the
Recovery Epoch 002 parent design.  It does not implement that boundary.

The test uses only body-free in-memory records.  It does not run formal
exact134, create an event/readiness/reservation/attempt, write a Git ref,
publish an artifact, authorize P2, or advance Cycle 001.
"""

from copy import deepcopy
import ast
import hashlib
import importlib.util
from pathlib import Path
import re
import sys
from typing import Any, Callable, Mapping


_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_TOOLS_ROOT = _AI_ROOT / "tools"
for _path in (_INFERENCE_ROOT, _TOOLS_ROOT, _HERE.parent):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_POST_RESERVATION_RETRY_"
    "LINEAGE_AND_FORMAL_WORKER_BOOTSTRAP_COMPLETENESS_RECONCILIATION_"
    "RED_FREEZE_ONLY"
)
_KAREN_DIARY_ENTRY = "700f749f5149cac1f8bd4bab8a364d524a56985b"
_COCOLON_ENTRY = "64f27c5c12acc6704f8973de7c4139808c10cee4"
_MASHOS_API_ENTRY = "e4917fd7380cdf9b8a29c8ad1c9d045d162f56fd"
_MASHOS_API_ENTRY_TREE = "1c8970e91dbc793fcb3b81b51c73291f0326a565"
_PARENT_DESIGN_BLOB = "af00c5c4a49207fb94108afbf383ea0e830620ae"
_PARENT_DESIGN_SHA256 = (
    "8b6564442d69fea1b38cb59ea3c5302874e6f92f87bfd5ce0728985094739829"
)
_P0_EXTERNAL_IDENTITY_SHA256 = (
    "0b5f4b0e3c3c023867a858782869c570e5a55c27cb72d8db108c309408581ce0"
)
_THIS_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_retry_lineage_and_"
    "formal_worker_bootstrap_reconciliation_red.py"
)

_FUTURE_ROLE_PATHS = {
    "lineage_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "publication_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ),
    "worker_evidence_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
    "preflight_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "formal_parent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
    "formal_runner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ),
    "independent_verifier": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "dependency_lock": (
        "ai/configs/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
    ),
}
_ROLE_OWNERS = {
    "sequence_lineage_owner": _FUTURE_ROLE_PATHS["lineage_owner"],
    "bootstrap_closure_owner": _FUTURE_ROLE_PATHS["closure_owner"],
    "publication_owner": _FUTURE_ROLE_PATHS["publication_owner"],
    "readiness_owner": _FUTURE_ROLE_PATHS["preflight_owner"],
    "preflight_owner": _FUTURE_ROLE_PATHS["preflight_owner"],
    "formal_worker_owner": _FUTURE_ROLE_PATHS["formal_runner"],
    "checkpoint_owner": _FUTURE_ROLE_PATHS["worker_evidence_owner"],
    "terminal_result_owner": _FUTURE_ROLE_PATHS[
        "worker_evidence_owner"
    ],
    "formal_parent_owner": _FUTURE_ROLE_PATHS["formal_parent"],
    "independent_verifier": _FUTURE_ROLE_PATHS[
        "independent_verifier"
    ],
    "canonical_current_closure_owner": _FUTURE_ROLE_PATHS["closure_owner"],
    "reproducible_dependency_lock": _FUTURE_ROLE_PATHS["dependency_lock"],
}
_TARGET_APIS = {
    "lineage": (
        "lineage_owner",
        "validate_recovery_epoch002_lineage_state",
    ),
    "bootstrap": (
        "preflight_owner",
        "validate_recovery_epoch002_bootstrap_state",
    ),
    "closure": (
        "closure_owner",
        "validate_recovery_epoch002_closure_state",
    ),
    "parent": (
        "formal_parent",
        "validate_recovery_epoch002_parent_state",
    ),
    "runner": (
        "worker_evidence_owner",
        "validate_recovery_epoch002_attempt_state",
    ),
    "publication": (
        "independent_verifier",
        "verify_recovery_epoch002_publication_state",
    ),
}

_SCHEMAS = {
    "p0_external_identity": (
        "cocolon.emlis.nls_v3.step11.cycle001."
        "recovery_epoch002.p0_external_identity.v1"
    ),
    "candidate_allocation": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "candidate_allocation.v1"
    ),
    "event1": "cocolon.emlis.nls_v3.recovery_epoch002.sequence_event.v1",
    "bootstrap_manifest": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_manifest.v1"
    ),
    "readiness": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_readiness.v1"
    ),
    "reservation": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_test_run_reservation.v1"
    ),
    "checkpoint": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_checkpoint.v1"
    ),
    "terminal_result": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_terminal_result.v1"
    ),
    "diagnostic": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_diagnostic.v1"
    ),
    "unknown_disposition": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "attempt_consumption_unknown_disposition.v1"
    ),
    "ready_unused": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "ready_unused_authority_stop.v1"
    ),
    "success_lineage": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "success_lineage.v1"
    ),
}
_P0_EXTERNAL_IDENTITY_KEYS = frozenset(
    {
        "schema_version",
        "logical_cycle_id",
        "recovery_epoch_id",
        "parent_design",
        "receipt",
        "p0_external_identity_sha256",
    }
)
_P0_PARENT_DESIGN_KEYS = frozenset(
    {
        "path",
        "publication_commit_sha1",
        "git_blob_sha1",
        "raw_sha256",
    }
)
_P0_RECEIPT_KEYS = frozenset(
    {
        "path",
        "publication_commit_sha1",
        "git_blob_sha1",
        "raw_sha256",
        "logical_receipt_sha256",
    }
)
_EXTERNAL_IDENTITY_KEYS = frozenset(
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
_SOURCE_CLOSURE_KEYS = frozenset(
    {
        "repository_full_name",
        "source_ref",
        "source_commit_sha1",
        "source_tree_sha1",
        "worktree_clean",
        "detailed_design_sha256",
        "source_dependency_closure_sha256",
        "canonical_current_closure_sha256",
        "requirement_registry_sha256",
        "formal_node_registry_sha256",
        "proof_source_closure_sha256",
        "formal_test_manifest_sha256",
        "bootstrap_closure_sha256",
        "d2_final_closure_sha256",
        "source_closure_sha256",
    }
)
_D2_FINAL_CLOSURE_PREIMAGE_KEYS = (
    "source_commit_sha1",
    "source_tree_sha1",
    "canonical_current_closure_sha256",
    "source_dependency_closure_sha256",
    "proof_source_closure_sha256",
    "requirement_registry_sha256",
    "formal_node_registry_sha256",
    "formal_test_manifest_sha256",
    "bootstrap_closure_sha256",
    "detailed_design_sha256",
)
_CANDIDATE_ALLOCATION_KEYS = frozenset(
    {
        "schema_version",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "d2_final_closure_sha256",
        "d2_completion_receipt",
        "allocated_at_utc",
        "candidate_allocation_sha256",
    }
)
_EVENT1_KEYS = frozenset(
    {
        "schema_version",
        "ledger_id",
        "event_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "event_name",
        "event_ordinal",
        "state",
        "timestamp_utc",
        "timestamp_kind",
        "authority",
        "challenge_id",
        "source_closure",
        "prior_event",
        "primary_evidence_artifact",
        "publication",
        "automatic_progression",
        "body_free",
        "event_sha256",
        "p0_external_identity",
        "candidate_allocation",
        "bootstrap_closure",
    }
)
_PUBLISHED_EVENT1_IDENTITY_KEYS = frozenset(
    {
        "identity_kind",
        "ledger_id",
        "recovery_epoch_id",
        "event_id",
        "event_name",
        "event_ordinal",
        "state",
        "timestamp_utc",
        "candidate_version_id",
        "event_path",
        "event_git_blob_sha1",
        "event_raw_sha256",
        "event_sha256",
        "publication_commit_sha1",
        "p0_external_identity_sha256",
        "source_closure_sha256",
        "bootstrap_closure_sha256",
        "identity_sha256",
    }
)
_RESERVATION_KEYS = frozenset(
    {
        "schema_version",
        "authority_token",
        "challenge_id",
        "authority_challenge_id",
        "attempt_id",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "formal_node_registry_sha256",
        "reservation_state",
        "reserved_at_utc",
        "source_baseline_event",
        "source_closure",
        "automatic_progression",
        "body_free",
        "formal_test_run_reservation_sha256",
        "reservation_ordinal",
        "publication_base_commit_sha1",
        "bootstrap_readiness_artifact",
        "prior_reservation_count",
        "prior_reservation_history",
        "prior_reservation_history_sha256",
        "lineage_state",
        "event1_challenge_id",
        "preflight_challenge_id",
    }
)
_PRIOR_RESERVATION_ROW_KEYS = frozenset(
    {
        "reservation_ordinal",
        "reservation_artifact",
        "attempt_id",
        "disposition_kind",
        "disposition_artifact",
    }
)
_SUCCESS_LINEAGE_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "source_baseline_event",
        "successful_reservation",
        "prior_reservation_count",
        "prior_reservation_history",
        "prior_reservation_history_sha256",
        "success_lineage_sha256",
    }
)
_READINESS_KEYS = frozenset(
    {
        "schema_version",
        "authority_token",
        "event1_challenge_id",
        "preflight_challenge_id",
        "preflight_id",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "source_closure",
        "bootstrap_closure",
        "python_runtime_identity",
        "pytest_distribution_identity",
        "dependency_lock_identity",
        "environment_profile",
        "preflight_owner_identity",
        "preflight_argv_sha256",
        "loaded_plugin_manifest_sha256",
        "readiness_state",
        "formal_collection_state",
        "formal_execution_state",
        "pytest_main_called",
        "owner_validation_state",
        "independent_verification_state",
        "preflight_started_at_utc",
        "preflight_finished_at_utc",
        "readiness_receipt_path",
        "automatic_progression",
        "body_free",
        "bootstrap_readiness_receipt_sha256",
    }
)
_PREFLIGHT_CHECKPOINT_KEYS = frozenset(
    {
        "schema_version",
        "phase",
        "logical_cycle_id",
        "recovery_epoch_id",
        "authority_token_id",
        "event1_challenge_id",
        "preflight_challenge_id",
        "preflight_id",
        "candidate_version_id",
        "source_baseline_event_sha256",
        "source_closure_sha256",
        "bootstrap_closure_sha256",
        "checkpoint_ordinal",
        "stage_enum",
        "prior_checkpoint_sha256",
        "observed_at_utc",
        "body_free",
        "checkpoint_sha256",
    }
)
_FORMAL_CHECKPOINT_KEYS = frozenset(
    {
        "schema_version",
        "phase",
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
        "checkpoint_ordinal",
        "stage_enum",
        "observed_at_utc",
        "prior_checkpoint_sha256",
        "body_free",
        "checkpoint_sha256",
    }
)
_UNKNOWN_DISPOSITION_KEYS = frozenset(
    {
        "schema_version",
        "reservation_artifact",
        "attempt_id",
        "checkpoint_status",
        "last_valid_stage",
        "terminal_result_status",
        "exit_class",
        "exit_code",
        "signal_number",
        "stop_code",
        "automatic_retry",
        "body_free",
        "attempt_consumption_unknown_disposition_sha256",
    }
)
_TERMINAL_RESULT_KEYS = frozenset(
    {
        "schema_version",
        "logical_cycle_id",
        "recovery_epoch_id",
        "authority_token_id",
        "event1_challenge_id",
        "formal_run_challenge_id",
        "formal_authority_challenge_id",
        "attempt_id",
        "candidate_version_id",
        "source_baseline_event_sha256",
        "source_closure_sha256",
        "bootstrap_closure_sha256",
        "formal_test_run_reservation_sha256",
        "terminal_checkpoint_sha256",
        "collection_node_ids",
        "executed_node_ids",
        "states",
        "collection_errors",
        "exit_class",
        "exit_code",
        "signal_number",
        "timed_out",
        "python_runtime_identity_sha256",
        "pytest_distribution_identity_sha256",
        "started_at_utc",
        "finished_at_utc",
        "body_free",
        "formal_worker_result_sha256",
    }
)
_DIAGNOSTIC_KEYS = frozenset(
    {
        "schema_version",
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
        "process_start_observed",
        "exit_class",
        "exit_code",
        "signal_number",
        "checkpoint_status",
        "last_valid_stage",
        "terminal_result_status",
        "valid_result_identity_sha256",
        "stop_code",
        "body_free",
        "diagnostic_sha256",
    }
)
_BOOTSTRAP_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "source_commit_sha1",
        "source_tree_sha1",
        "formal_owner_artifacts",
        "formal_owner_artifacts_sha256",
        "formal_test_node_ids",
        "formal_test_manifest",
        "formal_test_manifest_sha256",
        "conftest_plugin_mode",
        "pytest_plugins_environment_variable_removed",
        "pytest_entrypoint_autoload_disabled",
        "explicit_plugin_allowlist",
        "loaded_plugin_manifest",
        "loaded_plugin_manifest_sha256",
        "import_manifest",
        "import_manifest_sha256",
        "dependency_lock_identity",
        "installed_distributions",
        "installed_distributions_sha256",
        "python_runtime_identity",
        "pytest_distribution_identity",
        "environment_profile",
        "environment_profile_sha256",
        "preflight_argv",
        "preflight_argv_sha256",
        "formal_worker_argv",
        "formal_worker_argv_sha256",
        "unclassified_import_count",
        "unresolved_dynamic_import_count",
        "body_free",
        "bootstrap_closure_sha256",
    }
)
_IMPORT_MANIFEST_ROW_KEYS = frozenset(
    {
        "import_name",
        "classification",
        "owner_paths",
        "target_identity",
    }
)
_FIRST_PARTY_IMPORT_TARGET_KEYS = frozenset(
    {
        "path",
        "git_blob_sha1",
        "raw_sha256",
    }
)
_STDLIB_IMPORT_TARGET_KEYS = frozenset(
    {
        "module_name",
        "python_runtime_identity_sha256",
    }
)
_THIRD_PARTY_IMPORT_TARGET_KEYS = frozenset(
    {
        "module_name",
        "normalized_distribution_name",
        "distribution_version",
        "wheel_sha256",
        "installed_record_closure_sha256",
    }
)
_ATTEMPT_ID_PREIMAGE_KEYS = (
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
_PREFLIGHT_ID_PREIMAGE_KEYS = (
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
_SELF_HASH_RULES = {
    _SCHEMAS["p0_external_identity"]: "p0_external_identity_sha256",
    _SCHEMAS["candidate_allocation"]: "candidate_allocation_sha256",
    _SCHEMAS["event1"]: "event_sha256",
    _SCHEMAS["bootstrap_manifest"]: "bootstrap_closure_sha256",
    _SCHEMAS["readiness"]: "bootstrap_readiness_receipt_sha256",
    _SCHEMAS["reservation"]: "formal_test_run_reservation_sha256",
    _SCHEMAS["checkpoint"]: "checkpoint_sha256",
    _SCHEMAS["terminal_result"]: "formal_worker_result_sha256",
    _SCHEMAS["diagnostic"]: "diagnostic_sha256",
    _SCHEMAS["unknown_disposition"]: (
        "attempt_consumption_unknown_disposition_sha256"
    ),
    _SCHEMAS["success_lineage"]: "success_lineage_sha256",
}

_INSTALLER_IDENTITY_CLASS = "PIP_REQUIRE_HASHES_WHEEL_LOCK_V1"
_CONFTEST_PLUGIN_MODE = "DISABLED_BY_NOCONFTEST"
_FORMAL_PYTEST_OPTIONS = (
    "-q",
    "--disable-warnings",
    "--noconftest",
    "-p",
    "no:cacheprovider",
)
_IMPORT_CLASSIFICATIONS = frozenset(
    {
        "FIRST_PARTY",
        "STDLIB_BOUND_TO_PYTHON_RUNTIME",
        "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
    }
)
_FORMAL_PLUGIN_ALLOWLIST: tuple[str, ...] = ()
_PHASE_ORDER = (
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT",
    "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
    "PARENT_SPAWN_INTENT_PERSISTED",
    "FORMAL_EXACT134_ONCE",
    "TERMINAL_RESULT_OR_UNKNOWN_STOP",
)
_STAGE_GRAPH = {
    "PARENT_SPAWN_INTENT_PERSISTED": ("CHILD_PROCESS_ENTRY",),
    "CHILD_PROCESS_ENTRY": ("SOURCE_BINDING_VALIDATED",),
    "SOURCE_BINDING_VALIDATED": ("RUNTIME_PROFILE_VALIDATED",),
    "RUNTIME_PROFILE_VALIDATED": ("PYTEST_IMPORT_VALIDATED",),
    "PYTEST_IMPORT_VALIDATED": ("FORMAL_PLUGIN_BOOTSTRAP_VALIDATED",),
    "FORMAL_PLUGIN_BOOTSTRAP_VALIDATED": ("PYTEST_MAIN_ENTERING",),
    "PYTEST_MAIN_ENTERING": ("COLLECTION_STARTED",),
    "COLLECTION_STARTED": (
        "COLLECTION_FINISHED",
        "COLLECTION_FAILED",
    ),
    "COLLECTION_FINISHED": ("EXECUTION_STARTED",),
    "COLLECTION_FAILED": ("TERMINAL_RESULT_PERSISTED",),
    "EXECUTION_STARTED": ("EXECUTION_FINISHED",),
    "EXECUTION_FINISHED": ("TERMINAL_RESULT_PERSISTED",),
    "TERMINAL_RESULT_PERSISTED": (),
}
_DIAGNOSTIC_IDENTIFIER_ALLOWLIST = frozenset(
    {
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
        "checkpoint_ordinal",
        "stage_enum",
    }
)
_FORBIDDEN_DIAGNOSTIC_KEYS = frozenset(
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
        "generated_body",
        "prompt_text",
        "response_text",
        "private_review_data",
        "secret",
        "credential",
        "invalid_result_sha256",
    }
)
_REQUIRED_EXPORTS: dict[str, dict[str, Any]] = {
    "lineage": {
        "RECOVERY_EPOCH002_EVENT1_SCHEMA": _SCHEMAS["event1"],
        "RECOVERY_EPOCH002_EVENT1_KEYS": _EVENT1_KEYS,
        "RECOVERY_EPOCH002_PUBLISHED_EVENT1_IDENTITY_KEYS": (
            _PUBLISHED_EVENT1_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_CANDIDATE_ALLOCATION_KEYS": (
            _CANDIDATE_ALLOCATION_KEYS
        ),
        "RECOVERY_EPOCH002_READINESS_KEYS": _READINESS_KEYS,
        "RECOVERY_EPOCH002_RESERVATION_KEYS": _RESERVATION_KEYS,
        "RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS": (
            _PRIOR_RESERVATION_ROW_KEYS
        ),
        "RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS": _SUCCESS_LINEAGE_KEYS,
        "RECOVERY_EPOCH002_ATTEMPT_ID_PREIMAGE_KEYS": (
            _ATTEMPT_ID_PREIMAGE_KEYS
        ),
        "RECOVERY_EPOCH002_PREFLIGHT_ID_PREIMAGE_KEYS": (
            _PREFLIGHT_ID_PREIMAGE_KEYS
        ),
    },
    "bootstrap": {
        "RECOVERY_EPOCH002_READINESS_SCHEMA": _SCHEMAS["readiness"],
        "RECOVERY_EPOCH002_READINESS_KEYS": _READINESS_KEYS,
        "RECOVERY_EPOCH002_CONFTEST_PLUGIN_MODE": _CONFTEST_PLUGIN_MODE,
        "RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS": (
            _FORMAL_PYTEST_OPTIONS
        ),
        "RECOVERY_EPOCH002_FORMAL_PLUGIN_ALLOWLIST": (
            _FORMAL_PLUGIN_ALLOWLIST
        ),
    },
    "closure": {
        "RECOVERY_EPOCH002_SOURCE_CLOSURE_KEYS": _SOURCE_CLOSURE_KEYS,
        "RECOVERY_EPOCH002_D2_FINAL_CLOSURE_PREIMAGE_KEYS": (
            _D2_FINAL_CLOSURE_PREIMAGE_KEYS
        ),
        "RECOVERY_EPOCH002_BOOTSTRAP_CLOSURE_KEYS": (
            _BOOTSTRAP_MANIFEST_KEYS
        ),
        "RECOVERY_EPOCH002_IMPORT_MANIFEST_ROW_KEYS": (
            _IMPORT_MANIFEST_ROW_KEYS
        ),
        "RECOVERY_EPOCH002_FIRST_PARTY_IMPORT_TARGET_KEYS": (
            _FIRST_PARTY_IMPORT_TARGET_KEYS
        ),
        "RECOVERY_EPOCH002_STDLIB_IMPORT_TARGET_KEYS": (
            _STDLIB_IMPORT_TARGET_KEYS
        ),
        "RECOVERY_EPOCH002_THIRD_PARTY_IMPORT_TARGET_KEYS": (
            _THIRD_PARTY_IMPORT_TARGET_KEYS
        ),
        "RECOVERY_EPOCH002_IMPORT_CLASSIFICATIONS": (
            _IMPORT_CLASSIFICATIONS
        ),
        "RECOVERY_EPOCH002_INSTALLER_IDENTITY_CLASS": (
            _INSTALLER_IDENTITY_CLASS
        ),
    },
    "parent": {
        "RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER": _PHASE_ORDER,
    },
    "runner": {
        "RECOVERY_EPOCH002_PREFLIGHT_CHECKPOINT_KEYS": (
            _PREFLIGHT_CHECKPOINT_KEYS
        ),
        "RECOVERY_EPOCH002_FORMAL_CHECKPOINT_KEYS": (
            _FORMAL_CHECKPOINT_KEYS
        ),
        "RECOVERY_EPOCH002_TERMINAL_RESULT_KEYS": _TERMINAL_RESULT_KEYS,
        "RECOVERY_EPOCH002_DIAGNOSTIC_KEYS": _DIAGNOSTIC_KEYS,
        "RECOVERY_EPOCH002_UNKNOWN_DISPOSITION_KEYS": (
            _UNKNOWN_DISPOSITION_KEYS
        ),
        "RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH": _STAGE_GRAPH,
        "RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS": (
            _FORBIDDEN_DIAGNOSTIC_KEYS
        ),
    },
    "publication": {
        "RECOVERY_EPOCH002_ARTIFACT_IDENTITY_KEYS": (
            _EXTERNAL_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_P0_EXTERNAL_IDENTITY_KEYS": (
            _P0_EXTERNAL_IDENTITY_KEYS
        ),
        "RECOVERY_EPOCH002_P0_PARENT_DESIGN_KEYS": (
            _P0_PARENT_DESIGN_KEYS
        ),
        "RECOVERY_EPOCH002_P0_RECEIPT_KEYS": _P0_RECEIPT_KEYS,
    },
}
_PROTECTED_SHA256 = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_nls_v3_artifact_contract.py"
    ): "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b",
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3.py"
    ): "b5d40243578d7b6118cafd827f07de1b181ea9c1274f686447c9d031e112a8f9",
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch001_sequence_ledger_v3.py"
    ): "5fbdda03b25830fa8d77c7b9bc6d4c782cc3ebacac94d854cdc146d58d72968b",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
    ): "600b0eec2850ff58529c5ffe40a251ee119236265cfa745dbcf2e27fbbc0ed33",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch001_formal_parent_orchestrator_v3.py"
    ): "6293b075e48c5501f9e443545d7d04484b92265f0378ff30d847bed81a66a7b0",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
    ): "df42d097ec356c9c5a860ffda54e5cdf119d3a1d8cef0518576f99d0dbd8c749",
    "ai/tests/conftest.py": (
        "2f269b3589da7c619c44c638422799271379ff70a70c04cd1283d1fca812a999"
    ),
    "ai/tests/helpers/emlis_ai_fb172_migration.py": (
        "94cbf59a31f92a966df6a87b8c4a046b02a12dd8b0fee1b693a839f32b7fde48"
    ),
    (
        "ai/services/ai_inference/emotion_submit_service.py"
    ): "818ee1edb7ac4ff5f12cc7f8537eeb10fedc9f7dd37a4d165c5248a7249830f2",
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch001_canonical_current_closure_v3.py"
    ): "c8cc109adbb0b95e5d571b7d75f267d52d5076e17b169fd96699667b02782436",
    (
        "ai/services/ai_inference/api_emotion_submit.py"
    ): "0705dc5cd7d4a78a4b8f6de1721b80b1ea6ae70b1d48a064acff9a8277af1822",
    (
        "ai/services/ai_inference/emlis_ai_reply_service.py"
    ): "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a",
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_cycle_evidence_v3.py"
    ): "e9f77f7411b581e96a7035d05aa3a50eb4628cbba37a02b0786a0d35b818d43d",
    "requirements.txt": (
        "202215a8c33f37a1f2e55953bf3f96b65e3be3b5fefd9859df81297b9aac82fb"
    ),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(
    role: str,
    seed: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    value = {
        "artifact_role": role.upper().replace("-", "_"),
        "schema_version": f"cocolon.emlis.nls_v3.test.{role}.v1",
        "repository_full_name": "MassyuRed/Cocolon",
        "path": f"EmlisAIの実装済み資料/documents/{role}_{digest}.json",
        "git_blob_sha1": hashlib.sha1(seed.encode("utf-8")).hexdigest(),
        "raw_sha256": digest,
        "logical_artifact_sha256": hashlib.sha256(
            f"logical:{seed}".encode("utf-8")
        ).hexdigest(),
        "publication_commit_sha1": digest[:40],
        "body_free": True,
        "identity_sha256": "",
    }
    value["identity_sha256"] = artifact_sha256(
        _material(value, "identity_sha256")
    )
    return value


def _source_closure() -> dict[str, Any]:
    value: dict[str, Any] = {
        "repository_full_name": "MassyuRed/mashos-api",
        "source_ref": "refs/heads/main",
        "source_commit_sha1": "1" * 40,
        "source_tree_sha1": "2" * 40,
        "worktree_clean": True,
        "detailed_design_sha256": "0" * 64,
        "source_dependency_closure_sha256": "3" * 64,
        "canonical_current_closure_sha256": "4" * 64,
        "requirement_registry_sha256": "5" * 64,
        "formal_node_registry_sha256": "6" * 64,
        "proof_source_closure_sha256": "7" * 64,
        "formal_test_manifest_sha256": "8" * 64,
        "bootstrap_closure_sha256": "8" * 64,
        "d2_final_closure_sha256": "9" * 64,
        "source_closure_sha256": "",
    }
    value["source_closure_sha256"] = artifact_sha256(
        _material(value, "source_closure_sha256")
    )
    return value


def _material(value: Mapping[str, Any], key: str) -> dict[str, Any]:
    out = deepcopy(dict(value))
    out.pop(key, None)
    return out


def _history() -> list[dict[str, Any]]:
    return [
        {
            "reservation_ordinal": 1,
            "reservation_artifact": _identity("reservation", "ordinal-1"),
            "attempt_id": hashlib.sha256(
                b"epoch002-prior-attempt-ordinal-1"
            ).hexdigest(),
            "disposition_kind": "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
            "disposition_artifact": _identity(
                "unknown-disposition",
                "ordinal-1-disposition",
            ),
        }
    ]


def _reservation() -> dict[str, Any]:
    history = _history()
    event = _identity("event1", "epoch002-event1")
    readiness = _identity("readiness", "epoch002-readiness-2")
    closure = _source_closure()
    challenge_id = "a" * 64
    event1_challenge_id = "b" * 64
    preflight_challenge_id = "c" * 64
    authority_token = "epoch002-formal-authority-002"
    candidate_version_id = "nls_v3_rc_test_epoch002_post_d2"
    history_sha = artifact_sha256(
        {"prior_reservation_history": history}
    )
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": authority_token,
            "challenge_id": challenge_id,
        }
    )
    attempt_preimage = {
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": candidate_version_id,
        "authority_token": authority_token,
        "challenge_id": challenge_id,
        "authority_challenge_id": authority_challenge_id,
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
        "preflight_challenge_id": preflight_challenge_id,
        "reservation_ordinal": 2,
        "prior_reservation_history_sha256": history_sha,
    }
    assert tuple(attempt_preimage) == _ATTEMPT_ID_PREIMAGE_KEYS
    value: dict[str, Any] = {
        "schema_version": _SCHEMAS["reservation"],
        "authority_token": authority_token,
        "challenge_id": challenge_id,
        "authority_challenge_id": authority_challenge_id,
        "attempt_id": artifact_sha256(attempt_preimage),
        "candidate_version_id": candidate_version_id,
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "formal_node_registry_sha256": closure[
            "formal_node_registry_sha256"
        ],
        "reservation_state": "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN",
        "reserved_at_utc": "2026-07-26T12:00:00Z",
        "source_baseline_event": event,
        "source_closure": closure,
        "automatic_progression": False,
        "body_free": True,
        "formal_test_run_reservation_sha256": "",
        "reservation_ordinal": 2,
        "publication_base_commit_sha1": "d" * 40,
        "bootstrap_readiness_artifact": readiness,
        "prior_reservation_count": 1,
        "prior_reservation_history": history,
        "prior_reservation_history_sha256": history_sha,
        "lineage_state": (
            "RETRY_AFTER_PUBLISHED_CONSUMPTION_UNKNOWN_STOP"
        ),
        "event1_challenge_id": event1_challenge_id,
        "preflight_challenge_id": preflight_challenge_id,
    }
    value["formal_test_run_reservation_sha256"] = artifact_sha256(
        _material(value, "formal_test_run_reservation_sha256")
    )
    return value


def _lineage_state() -> dict[str, Any]:
    reservation = _reservation()
    event_commit = reservation["source_baseline_event"][
        "publication_commit_sha1"
    ]
    current_head = reservation["publication_base_commit_sha1"]
    prior_history = deepcopy(reservation["prior_reservation_history"])
    return {
        "event1_count": 1,
        "event1_commit_sha1": event_commit,
        "event1_ancestor_of_current_head": True,
        "current_head_sha1": current_head,
        "publication_parent_commit_sha1": current_head,
        "publication_parent_count": 1,
        "expected_old_sha1": current_head,
        "observed_old_sha1": current_head,
        "changed_paths": [
            reservation["bootstrap_readiness_artifact"]["path"].replace(
                "readiness_",
                "reservation_",
            )
        ],
        "expected_changed_paths": [
            reservation["bootstrap_readiness_artifact"]["path"].replace(
                "readiness_",
                "reservation_",
            )
        ],
        "postverified": True,
        "event1_candidate_version_id": reservation[
            "candidate_version_id"
        ],
        "readiness_candidate_version_id": reservation[
            "candidate_version_id"
        ],
        "reservation_candidate_version_id": reservation[
            "candidate_version_id"
        ],
        "result_candidate_version_id": reservation["candidate_version_id"],
        "accepted_candidate_version_id": reservation[
            "candidate_version_id"
        ],
        "candidate_allocated_after_d2_postverification": True,
        "inherits_epoch001_acceptance_credit": False,
        "event1_challenge_id": reservation["event1_challenge_id"],
        "preflight_challenge_id": reservation[
            "preflight_challenge_id"
        ],
        "formal_run_challenge_id": reservation["challenge_id"],
        "reservation": reservation,
        "published_reservations": prior_history,
        "declared_prior_reservation_history": prior_history,
        "prior_reservation_unresolved": False,
        "result_publication_pending": False,
        "success_event2_published": False,
        "identity_reuse_detected": False,
        "readiness_publication_commit_sha1": current_head,
        "readiness_consumed": False,
        "earlier_ready_dispositions": [
            "RESERVATION_PUBLISHED",
        ],
        "source_closure_sha256": artifact_sha256(
            reservation["source_closure"]
        ),
        "event1_source_closure_sha256": artifact_sha256(
            reservation["source_closure"]
        ),
        "readiness_source_closure_sha256": artifact_sha256(
            reservation["source_closure"]
        ),
        "child_source_closure_sha256": artifact_sha256(
            reservation["source_closure"]
        ),
        "success_lineage_history_sha256": artifact_sha256(
            {"prior_reservation_history": prior_history}
        ),
        "accepted_lineage_history_sha256": artifact_sha256(
            {"prior_reservation_history": prior_history}
        ),
    }


def _bootstrap_manifest() -> dict[str, Any]:
    owner_artifacts = [
        {
            "role": role,
            "path": path,
            "git_blob_sha1": "1" * 40,
            "raw_sha256": hashlib.sha256(
                f"owner:{role}:{path}".encode("utf-8")
            ).hexdigest(),
        }
        for role, path in sorted(_ROLE_OWNERS.items())
    ]
    formal_test_manifest = [
        {
            "path": "ai/tests/test_formal_example.py",
            "git_blob_sha1": "4" * 40,
            "raw_sha256": "5" * 64,
        }
    ]
    import_manifest = [
        {
            "import_name": "example",
            "classification": "FIRST_PARTY",
            "owner_paths": ["ai/tests/test_formal_example.py"],
            "target_identity": {
                "path": "ai/services/ai_inference/example.py",
                "git_blob_sha1": "5" * 40,
                "raw_sha256": "6" * 64,
            },
        },
        {
            "import_name": "json",
            "classification": "STDLIB_BOUND_TO_PYTHON_RUNTIME",
            "owner_paths": ["ai/tests/test_formal_example.py"],
            "target_identity": {
                "module_name": "json",
                "python_runtime_identity_sha256": "7" * 64,
            },
        },
        {
            "import_name": "pytest",
            "classification": (
                "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION"
            ),
            "owner_paths": ["ai/tests/test_formal_example.py"],
            "target_identity": {
                "module_name": "pytest",
                "normalized_distribution_name": "pytest",
                "distribution_version": "8.4.1",
                "wheel_sha256": "8" * 64,
                "installed_record_closure_sha256": "9" * 64,
            },
        },
    ]
    installed_distributions = [
        {
            "normalized_distribution_name": "pytest",
            "distribution_version": "8.4.1",
            "wheel_sha256": "8" * 64,
            "installed_record_closure_sha256": "9" * 64,
        }
    ]
    environment_profile = {
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
        _FUTURE_ROLE_PATHS["preflight_owner"],
        "--preflight",
    ]
    formal_worker_argv = [
        "python",
        "-I",
        "-B",
        _FUTURE_ROLE_PATHS["formal_runner"],
        "--internal-exact134-child",
        *_FORMAL_PYTEST_OPTIONS,
    ]
    value: dict[str, Any] = {
        "schema_version": _SCHEMAS["bootstrap_manifest"],
        "source_commit_sha1": "1" * 40,
        "source_tree_sha1": "2" * 40,
        "formal_owner_artifacts": owner_artifacts,
        "formal_owner_artifacts_sha256": artifact_sha256(
            owner_artifacts
        ),
        "formal_test_node_ids": [
            f"ai/tests/test_formal_example.py::test_node_{number:03d}"
            for number in range(1, 135)
        ],
        "formal_test_manifest": formal_test_manifest,
        "formal_test_manifest_sha256": artifact_sha256(
            formal_test_manifest
        ),
        "conftest_plugin_mode": _CONFTEST_PLUGIN_MODE,
        "pytest_plugins_environment_variable_removed": True,
        "pytest_entrypoint_autoload_disabled": True,
        "explicit_plugin_allowlist": list(_FORMAL_PLUGIN_ALLOWLIST),
        "loaded_plugin_manifest": [],
        "loaded_plugin_manifest_sha256": artifact_sha256([]),
        "import_manifest": import_manifest,
        "import_manifest_sha256": artifact_sha256(import_manifest),
        "dependency_lock_identity": {
            "identity_class": _INSTALLER_IDENTITY_CLASS,
            "path": _FUTURE_ROLE_PATHS["dependency_lock"],
            "raw_sha256": "b" * 64,
        },
        "installed_distributions": installed_distributions,
        "installed_distributions_sha256": artifact_sha256(
            installed_distributions
        ),
        "python_runtime_identity": {
            "executable_sha256": "c" * 64,
            "implementation": "CPYTHON",
            "version": "3.12.13",
            "build_sha256": "d" * 64,
        },
        "pytest_distribution_identity": {
            "normalized_distribution_name": "pytest",
            "distribution_version": "8.4.1",
            "wheel_sha256": "8" * 64,
            "installed_record_closure_sha256": "9" * 64,
        },
        "environment_profile": environment_profile,
        "environment_profile_sha256": artifact_sha256(
            environment_profile
        ),
        "preflight_argv": preflight_argv,
        "preflight_argv_sha256": artifact_sha256(preflight_argv),
        "formal_worker_argv": formal_worker_argv,
        "formal_worker_argv_sha256": artifact_sha256(
            formal_worker_argv
        ),
        "unclassified_import_count": 0,
        "unresolved_dynamic_import_count": 0,
        "body_free": True,
        "bootstrap_closure_sha256": "",
    }
    value["bootstrap_closure_sha256"] = artifact_sha256(
        _material(value, "bootstrap_closure_sha256")
    )
    return value


def _readiness() -> dict[str, Any]:
    closure = _source_closure()
    manifest = _bootstrap_manifest()
    value: dict[str, Any] = {
        "schema_version": _SCHEMAS["readiness"],
        "authority_token": "epoch002-preflight-authority-002",
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": "nls_v3_rc_test_epoch002_post_d2",
        "event1_challenge_id": "b" * 64,
        "preflight_challenge_id": "c" * 64,
        "preflight_id": "e" * 64,
        "source_baseline_event": _identity("event1", "epoch002-event1"),
        "source_closure": closure,
        "bootstrap_closure": manifest,
        "python_runtime_identity": deepcopy(
            manifest["python_runtime_identity"]
        ),
        "pytest_distribution_identity": deepcopy(
            manifest["pytest_distribution_identity"]
        ),
        "dependency_lock_identity": {
            **deepcopy(manifest["dependency_lock_identity"]),
        },
        "environment_profile": {
            "fixed": {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            },
            "removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"],
            "inherited_path_sha256": "f" * 64,
            "lang": "C.UTF-8",
            "lc_all": "C.UTF-8",
        },
        "preflight_owner_identity": {
            "path": _FUTURE_ROLE_PATHS["preflight_owner"],
            "git_blob_sha1": "1" * 40,
            "raw_sha256": "2" * 64,
        },
        "preflight_argv_sha256": manifest["preflight_argv_sha256"],
        "loaded_plugin_manifest_sha256": manifest[
            "loaded_plugin_manifest_sha256"
        ],
        "readiness_state": "READY_FOR_EXACT_ONE_FORMAL_SPAWN",
        "formal_collection_state": "NOT_STARTED",
        "formal_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "preflight_started_at_utc": "2026-07-26T11:58:00Z",
        "preflight_finished_at_utc": "2026-07-26T11:59:00Z",
        "readiness_receipt_path": (
            "EmlisAIの実装済み資料/documents/"
            "RecoveryEpoch002_Readiness_TestOnly.json"
        ),
        "automatic_progression": False,
        "body_free": True,
        "bootstrap_readiness_receipt_sha256": "",
    }
    value["bootstrap_readiness_receipt_sha256"] = artifact_sha256(
        _material(value, "bootstrap_readiness_receipt_sha256")
    )
    return value


def _bootstrap_state() -> dict[str, Any]:
    readiness = _readiness()
    manifest = readiness["bootstrap_closure"]
    closure_sha = manifest["bootstrap_closure_sha256"]
    runtime_sha = artifact_sha256(manifest["python_runtime_identity"])
    pytest_sha = artifact_sha256(manifest["pytest_distribution_identity"])
    environment_sha = manifest["environment_profile_sha256"]
    return {
        "phase_order": list(_PHASE_ORDER),
        "preflight_present": True,
        "preflight_state": "READY_FOR_EXACT_ONE_FORMAL_SPAWN",
        "reservation_count_delta": 0,
        "formal_exact134_invocation_count": 0,
        "pytest_main_called": False,
        "collection_started": False,
        "formal_test_module_imported": False,
        "loaded_plugins": [],
        "bootstrap_manifest": manifest,
        "static_import_manifest_complete": True,
        "runtime_materialization_matches_lock": True,
        "owner_issue_codes": [],
        "independent_issue_codes": [],
        "readiness_receipt": readiness,
        "readiness_external_identity": _identity(
            "readiness",
            "epoch002-readiness-2",
        ),
        "readiness_is_immediate_base": True,
        "readiness_is_stale": False,
        "readiness_reused": False,
        "source_closure_sha256": artifact_sha256(
            readiness["source_closure"]
        ),
        "child_source_closure_sha256": artifact_sha256(
            readiness["source_closure"]
        ),
        "bootstrap_closure_sha256": closure_sha,
        "child_bootstrap_closure_sha256": closure_sha,
        "python_runtime_sha256": runtime_sha,
        "child_python_runtime_sha256": runtime_sha,
        "pytest_identity_sha256": pytest_sha,
        "child_pytest_identity_sha256": pytest_sha,
        "environment_profile_sha256": environment_sha,
        "child_environment_profile_sha256": environment_sha,
        "preflight_argv_sha256": manifest["preflight_argv_sha256"],
        "child_preflight_argv_sha256": manifest[
            "preflight_argv_sha256"
        ],
        "formal_worker_argv_sha256": manifest[
            "formal_worker_argv_sha256"
        ],
        "child_formal_worker_argv_sha256": manifest[
            "formal_worker_argv_sha256"
        ],
        "earlier_ready_dispositions": ["RESERVATION_PUBLISHED"],
    }


def _checkpoint(
    ordinal: int,
    stage: str,
    prior: str | None,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "schema_version": _SCHEMAS["checkpoint"],
        "phase": "FORMAL_RUN",
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "authority_token_id": "epoch002-formal-authority-002",
        "event1_challenge_id": "b" * 64,
        "preflight_challenge_id": "c" * 64,
        "formal_run_challenge_id": "a" * 64,
        "formal_authority_challenge_id": "d" * 64,
        "preflight_id": "e" * 64,
        "attempt_id": "f" * 64,
        "reservation_ordinal": 2,
        "formal_test_run_reservation_sha256": "0" * 64,
        "candidate_version_id": "nls_v3_rc_test_epoch002_post_d2",
        "source_baseline_event_sha256": "1" * 64,
        "source_closure_sha256": "2" * 64,
        "bootstrap_closure_sha256": "3" * 64,
        "checkpoint_ordinal": ordinal,
        "stage_enum": stage,
        "prior_checkpoint_sha256": prior,
        "observed_at_utc": f"2026-07-26T12:00:{ordinal:02d}Z",
        "body_free": True,
        "checkpoint_sha256": "",
    }
    value["checkpoint_sha256"] = artifact_sha256(
        _material(value, "checkpoint_sha256")
    )
    return value


def _checkpoint_chain() -> list[dict[str, Any]]:
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
    out: list[dict[str, Any]] = []
    prior: str | None = None
    for ordinal, stage in enumerate(stages, start=1):
        row = _checkpoint(ordinal, stage, prior)
        out.append(row)
        prior = row["checkpoint_sha256"]
    return out


def _runner_state() -> dict[str, Any]:
    checkpoints = _checkpoint_chain()
    result = {
        "schema_version": _SCHEMAS["terminal_result"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "authority_token_id": "epoch002-formal-authority-002",
        "event1_challenge_id": "b" * 64,
        "formal_run_challenge_id": "a" * 64,
        "formal_authority_challenge_id": "d" * 64,
        "attempt_id": "f" * 64,
        "candidate_version_id": "nls_v3_rc_test_epoch002_post_d2",
        "source_baseline_event_sha256": "1" * 64,
        "source_closure_sha256": "2" * 64,
        "bootstrap_closure_sha256": "3" * 64,
        "formal_test_run_reservation_sha256": "0" * 64,
        "terminal_checkpoint_sha256": checkpoints[-1][
            "checkpoint_sha256"
        ],
        "collection_node_ids": [
            f"ai/tests/test_formal_example.py::test_node_{number:03d}"
            for number in range(1, 135)
        ],
        "executed_node_ids": [
            f"ai/tests/test_formal_example.py::test_node_{number:03d}"
            for number in range(1, 135)
        ],
        "states": {
            (
                f"ai/tests/test_formal_example.py::test_node_{number:03d}"
            ): ("FAILED" if number == 134 else "PASSED")
            for number in range(1, 135)
        },
        "collection_errors": 0,
        "exit_class": "EXITED",
        "exit_code": 1,
        "signal_number": None,
        "timed_out": False,
        "python_runtime_identity_sha256": "4" * 64,
        "pytest_distribution_identity_sha256": "5" * 64,
        "started_at_utc": "2026-07-26T12:00:00Z",
        "finished_at_utc": "2026-07-26T12:01:00Z",
        "body_free": True,
        "formal_worker_result_sha256": "",
    }
    result["formal_worker_result_sha256"] = artifact_sha256(
        _material(result, "formal_worker_result_sha256")
    )
    diagnostic: dict[str, Any] = {
        "schema_version": _SCHEMAS["diagnostic"],
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "authority_token_id": "epoch002-formal-authority-002",
        "event1_challenge_id": "b" * 64,
        "preflight_challenge_id": "c" * 64,
        "formal_run_challenge_id": "a" * 64,
        "formal_authority_challenge_id": "d" * 64,
        "preflight_id": "e" * 64,
        "attempt_id": "f" * 64,
        "reservation_ordinal": 2,
        "process_start_observed": True,
        "exit_class": "EXITED",
        "exit_code": 1,
        "signal_number": None,
        "checkpoint_status": "VALID",
        "last_valid_stage": "TERMINAL_RESULT_PERSISTED",
        "terminal_result_status": "VALID",
        "valid_result_identity_sha256": result[
            "formal_worker_result_sha256"
        ],
        "stop_code": "FORMAL_FAILURE_ATTEMPT_PUBLISHED_STOP",
        "body_free": True,
        "diagnostic_sha256": "",
    }
    diagnostic["diagnostic_sha256"] = artifact_sha256(
        _material(diagnostic, "diagnostic_sha256")
    )
    return {
        "reservation_published_and_postverified": True,
        "parent_spawn_intent_persisted": True,
        "child_process_created": True,
        "exit_class": "EXITED",
        "exit_code": 1,
        "signal_number": None,
        "timed_out": False,
        "checkpoint_status": "VALID",
        "checkpoint_chain": checkpoints,
        "terminal_result_status": "VALID",
        "terminal_result": result,
        "terminal_result_publication_succeeded": True,
        "same_attempt_rerun_requested": False,
        "synthetic_collection_observation": False,
        "multiple_run_results_ranked": False,
        "earlier_consumed_lineage_dropped": False,
        "diagnostics": diagnostic,
        "unknown_disposition": None,
    }


def _publication_state() -> dict[str, Any]:
    readiness = _readiness()
    current_head = "d" * 40
    path = _identity("readiness", "publication")["path"]
    return {
        "artifact_role": "BOOTSTRAP_READINESS",
        "artifact": readiness,
        "artifact_external_identity": _identity(
            "readiness",
            "publication",
        ),
        "receipt_contains_self_commit_blob_or_raw_identity": False,
        "expected_old_sha1": current_head,
        "observed_old_sha1": current_head,
        "parent_commit_sha1s": [current_head],
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
    }


def _parent_state() -> dict[str, Any]:
    return {
        "phase_order": list(_PHASE_ORDER),
        "preflight_state": "READY_FOR_EXACT_ONE_FORMAL_SPAWN",
        "readiness_published_and_postverified": True,
        "reservation_published_and_postverified": False,
        "parent_spawn_intent_persisted": False,
        "formal_exact134_invocation_count": 0,
        "terminal_result_status": "NOT_STARTED",
        "terminal_result_publication_succeeded": False,
        "automatic_progression": False,
    }


def _closure_state() -> dict[str, Any]:
    return {
        "event1_closure_sha256": "1" * 64,
        "current_source_closure_sha256": "1" * 64,
        "current_proof_closure_sha256": "2" * 64,
        "event1_proof_closure_sha256": "2" * 64,
        "current_registry_closure_sha256": "3" * 64,
        "event1_registry_closure_sha256": "3" * 64,
        "current_bootstrap_closure_sha256": "4" * 64,
        "event1_bootstrap_closure_sha256": "4" * 64,
        "static_import_manifest_complete": True,
        "third_party_distribution_mapping_complete": True,
        "unclassified_import_count": 0,
        "unresolved_dynamic_import_count": 0,
    }


_RED_CASES = (
    ("L01", "lineage", None),
    ("L02", "lineage", "RESERVATION_TRANSACTION_PARENT_POLICY_INVALID"),
    ("L03", "lineage", "EVENT1_ANCESTRY_INVALID"),
    ("L04", "publication", "RESERVATION_NOT_PUBLISHED_STOP"),
    ("L05", "lineage", "RESERVATION_LINEAGE_INVALID"),
    ("L06", "lineage", "NEW_RESERVATION_FORBIDDEN"),
    ("L07", "lineage", "REPLAY_FORBIDDEN"),
    ("L08", "lineage", "SUCCESS_ALREADY_PUBLISHED"),
    ("L09", "closure", "EVENT1_REUSE_FORBIDDEN"),
    ("L10", "lineage", "SUCCESS_LINEAGE_INVALID"),
    ("L11", "lineage", "DUPLICATE_EVENT1"),
    ("L12", "lineage", "PHASE_CHALLENGE_COLLISION"),
    ("L13", "lineage", "RUN_RESERVATION_INVALID"),
    ("L14", "lineage", "READY_TO_RESERVATION_DRIFT_STOP"),
    ("L15", "lineage", "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"),
    (
        "L16",
        "lineage",
        "EPOCH002_RELEASE_CANDIDATE_BOUNDARY_CONFLICT_STOP",
    ),
    ("L17", "lineage", "CANDIDATE_LINEAGE_INVALID"),
    ("L18", "lineage", "SOURCE_BASELINE_PUBLICATION_FORBIDDEN"),
    (
        "B01",
        "parent",
        "PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",
    ),
    ("B02", "bootstrap", "READINESS_FORBIDDEN"),
    ("B03", "bootstrap", "READINESS_FORBIDDEN"),
    ("B04", "bootstrap", "READINESS_FORBIDDEN"),
    ("B05", "bootstrap", "READINESS_FORBIDDEN"),
    ("B06", "bootstrap", "RESERVATION_FORBIDDEN"),
    ("B07", "runner", "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"),
    ("B08", "runner", "CHECKPOINT_INVALID"),
    ("B09", "runner", "FORMAL_ATTEMPT_FORBIDDEN"),
    ("B10", "runner", "BODY_FREE_VIOLATION"),
    (
        "B11",
        "runner",
        "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
    ),
    ("B12", "publication", "READINESS_SELF_REFERENCE_INVALID"),
    ("B13", "publication", "READINESS_RECEIPT_NOT_PUBLISHED_STOP"),
    ("B14", "bootstrap", "READINESS_FORBIDDEN"),
    ("B15", "closure", "READINESS_FORBIDDEN"),
    ("B16", "runner", "UNKNOWN_DISPOSITION_INVALID"),
    (
        "B17",
        "runner",
        "TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",
    ),
    ("B18", "runner", "BODY_ORACLE_VIOLATION"),
    (
        "B19",
        "lineage",
        "NEXT_PREFLIGHT_AND_RESERVATION_FORBIDDEN",
    ),
    ("B20", "lineage", "READINESS_LINEAGE_INVALID"),
    (
        "B21",
        "publication",
        "RESERVATION_PUBLICATION_OUTCOME_UNKNOWN_STOP",
    ),
    ("B22", "publication", "READY_UNUSED_ONLY"),
    ("B23", "lineage", "RUN_RESERVATION_INVALID"),
    ("B24", "lineage", "RUN_RESERVATION_INVALID"),
)


def _states_for_case(case_id: str, role: str) -> list[dict[str, Any]]:
    factories: dict[str, Callable[[], dict[str, Any]]] = {
        "lineage": _lineage_state,
        "bootstrap": _bootstrap_state,
        "closure": _closure_state,
        "parent": _parent_state,
        "runner": _runner_state,
        "publication": _publication_state,
    }
    state = factories[role]()

    if case_id == "L01":
        return [state]
    if case_id == "L02":
        state["publication_parent_commit_sha1"] = state[
            "event1_commit_sha1"
        ]
        state["reservation_parent_policy"] = "EVENT1_DIRECT_PARENT_REQUIRED"
    elif case_id == "L03":
        state["event1_ancestor_of_current_head"] = False
    elif case_id == "L04":
        variants = []
        for field, value in (
            ("observed_old_sha1", "e" * 40),
            ("parent_commit_sha1s", ["d" * 40, "e" * 40]),
            ("changed_paths", ["forbidden/extra.json"]),
            ("postfetch_matches_candidate", False),
        ):
            row = deepcopy(state)
            row[field] = value
            variants.append(row)
        return variants
    elif case_id == "L05":
        variants = []
        for history in (
            [],
            [*state["published_reservations"], state["published_reservations"][0]],
            list(reversed(state["published_reservations"])),
        ):
            row = deepcopy(state)
            row["declared_prior_reservation_history"] = history
            variants.append(row)
        return variants
    elif case_id == "L06":
        variants = []
        for field in (
            "prior_reservation_unresolved",
            "result_publication_pending",
        ):
            row = deepcopy(state)
            row[field] = True
            variants.append(row)
        return variants
    elif case_id == "L07":
        state["identity_reuse_detected"] = True
    elif case_id == "L08":
        state["success_event2_published"] = True
    elif case_id == "L09":
        state["current_bootstrap_closure_sha256"] = "9" * 64
    elif case_id == "L10":
        state["accepted_lineage_history_sha256"] = artifact_sha256([])
    elif case_id == "L11":
        state["event1_count"] = 2
    elif case_id == "L12":
        variants = []
        pairs = (
            ("event1_challenge_id", "preflight_challenge_id"),
            ("event1_challenge_id", "formal_run_challenge_id"),
            ("preflight_challenge_id", "formal_run_challenge_id"),
        )
        for left, right in pairs:
            row = deepcopy(state)
            row[right] = row[left]
            variants.append(row)
        return variants
    elif case_id == "L13":
        variants = []
        row = deepcopy(state)
        row["reservation"]["reservation_ordinal"] = True
        variants.append(row)
        row = deepcopy(state)
        row["reservation"]["reservation_ordinal"] = 0
        variants.append(row)
        row = deepcopy(state)
        row["reservation"].pop("lineage_state")
        variants.append(row)
        row = deepcopy(state)
        row["reservation"]["forbidden_extra"] = True
        variants.append(row)
        row = deepcopy(state)
        row["reservation"]["prior_reservation_history_sha256"] = "0" * 64
        variants.append(row)
        row = deepcopy(state)
        row["reservation"]["attempt_id"] = "0" * 64
        variants.append(row)
        return variants
    elif case_id == "L14":
        state["readiness_source_closure_sha256"] = "0" * 64
    elif case_id == "L15":
        state["child_source_closure_sha256"] = "0" * 64
        state["reservation_consumed"] = True
    elif case_id == "L16":
        variants = []
        row = deepcopy(state)
        row["reservation"]["candidate_version_id"] = "nls_v3_rc_0034"
        variants.append(row)
        row = deepcopy(state)
        row["reservation"].pop("candidate_version_id")
        variants.append(row)
        row = deepcopy(state)
        row["inherits_epoch001_acceptance_credit"] = True
        variants.append(row)
        return variants
    elif case_id == "L17":
        state["result_candidate_version_id"] = "different-candidate"
    elif case_id == "L18":
        state["candidate_allocated_after_d2_postverification"] = False
    elif case_id == "B01":
        variants = []
        for present, result in ((False, "ABSENT"), (True, "FAILED")):
            row = deepcopy(state)
            row["preflight_state"] = result
            row["readiness_published_and_postverified"] = present
            row["reservation_published_and_postverified"] = False
            row["formal_exact134_invocation_count"] = 0
            variants.append(row)
        return variants
    elif case_id == "B02":
        variants = []
        for field in (
            "pytest_main_called",
            "collection_started",
            "formal_test_module_imported",
        ):
            row = deepcopy(state)
            row[field] = True
            variants.append(row)
        return variants
    elif case_id == "B03":
        variants = []
        row = deepcopy(state)
        row["loaded_plugins"] = ["helpers.emlis_ai_fb172_migration"]
        variants.append(row)
        row = deepcopy(state)
        row["bootstrap_manifest"]["explicit_plugin_allowlist"] = [
            "helpers.emlis_ai_fb172_migration"
        ]
        row["bootstrap_manifest"]["import_manifest"] = [
            item
            for item in row["bootstrap_manifest"]["import_manifest"]
            if item["import_name"] != "pytest"
        ]
        variants.append(row)
        row = deepcopy(state)
        row["bootstrap_manifest"]["formal_worker_argv"].remove(
            "--noconftest"
        )
        variants.append(row)
        return variants
    elif case_id == "B04":
        variants = []
        for field in (
            "runtime_materialization_matches_lock",
            "static_import_manifest_complete",
        ):
            row = deepcopy(state)
            row[field] = False
            variants.append(row)
        return variants
    elif case_id == "B05":
        variants = []
        for field in (
            "child_python_runtime_sha256",
            "child_pytest_identity_sha256",
            "child_environment_profile_sha256",
            "child_preflight_argv_sha256",
            "child_formal_worker_argv_sha256",
        ):
            row = deepcopy(state)
            row[field] = "0" * 64
            variants.append(row)
        return variants
    elif case_id == "B06":
        variants = []
        for field in (
            "readiness_is_stale",
            "readiness_reused",
        ):
            row = deepcopy(state)
            row[field] = True
            variants.append(row)
        row = deepcopy(state)
        row["readiness_is_immediate_base"] = False
        variants.append(row)
        return variants
    elif case_id == "B07":
        variants = []
        for exit_class in (
            "SPAWN_FAILED",
            "EXITED",
            "SIGNALED",
            "TIMED_OUT",
        ):
            row = deepcopy(state)
            row["exit_class"] = exit_class
            row["terminal_result_status"] = "ABSENT"
            row["terminal_result"] = None
            row["checkpoint_chain"] = row["checkpoint_chain"][:3]
            row["same_attempt_rerun_requested"] = False
            variants.append(row)
        return variants
    elif case_id == "B08":
        variants = []
        row = deepcopy(state)
        row["checkpoint_chain"][4]["checkpoint_ordinal"] = 3
        variants.append(row)
        row = deepcopy(state)
        row["checkpoint_chain"][4]["stage_enum"] = "EXECUTION_FINISHED"
        variants.append(row)
        row = deepcopy(state)
        row["checkpoint_status"] = "INVALID_PARTIAL_JSON"
        variants.append(row)
        row = deepcopy(state)
        row["checkpoint_status"] = "SYMLINK_SUBSTITUTION"
        variants.append(row)
        return variants
    elif case_id == "B09":
        state["checkpoint_status"] = "ABSENT"
        state["checkpoint_chain"] = []
        state["synthetic_collection_observation"] = True
    elif case_id == "B10":
        variants = []
        for key in sorted(_FORBIDDEN_DIAGNOSTIC_KEYS):
            row = deepcopy(state)
            row["diagnostics"][key] = "forbidden"
            variants.append(row)
        return variants
    elif case_id == "B11":
        state["terminal_result_publication_succeeded"] = False
    elif case_id == "B12":
        state["receipt_contains_self_commit_blob_or_raw_identity"] = True
    elif case_id == "B13":
        variants = []
        for field, value in (
            ("observed_old_sha1", "e" * 40),
            ("parent_commit_sha1s", ["d" * 40, "e" * 40]),
            ("path_preexisted", True),
            ("changed_paths", ["forbidden/extra.json"]),
            ("postfetch_matches_candidate", False),
        ):
            row = deepcopy(state)
            row[field] = value
            variants.append(row)
        return variants
    elif case_id == "B14":
        state["independent_issue_codes"] = ["INDEPENDENT_DISAGREEMENT"]
    elif case_id == "B15":
        variants = []
        row = deepcopy(state)
        row["static_import_manifest_complete"] = False
        variants.append(row)
        row = deepcopy(state)
        row["third_party_distribution_mapping_complete"] = False
        variants.append(row)
        return variants
    elif case_id == "B16":
        base = {
            "schema_version": _SCHEMAS["unknown_disposition"],
            "reservation_artifact": _identity("reservation", "ordinal-2"),
            "attempt_id": "f" * 64,
            "checkpoint_status": "ABSENT",
            "last_valid_stage": None,
            "terminal_result_status": "ABSENT",
            "exit_class": "UNKNOWN",
            "exit_code": None,
            "signal_number": None,
            "stop_code": "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
            "automatic_retry": False,
            "body_free": True,
            "attempt_consumption_unknown_disposition_sha256": "0" * 64,
        }
        variants = []
        for key, value in (
            ("outcomes", {}),
            ("counts", {"collected": 134}),
            ("collection_state", "FINISHED"),
            ("synthetic_exit_code", 1),
        ):
            row = deepcopy(state)
            row["unknown_disposition"] = {**base, key: value}
            variants.append(row)
        return variants
    elif case_id == "B17":
        variants = []
        row = deepcopy(state)
        last_node = row["terminal_result"]["collection_node_ids"][-1]
        row["terminal_result"]["states"][last_node] = "PASSED"
        variants.append(row)
        row = deepcopy(state)
        row["multiple_run_results_ranked"] = True
        variants.append(row)
        row = deepcopy(state)
        row["earlier_consumed_lineage_dropped"] = True
        variants.append(row)
        return variants
    elif case_id == "B18":
        state["terminal_result_status"] = "INVALID"
        state["diagnostics"]["invalid_result_sha256"] = "0" * 64
    elif case_id == "B19":
        state["earlier_ready_dispositions"] = [
            "RESERVATION_PUBLISHED",
            "UNRESOLVED",
        ]
    elif case_id == "B20":
        variants = []
        row = deepcopy(state)
        row["earlier_ready_dispositions"] = [
            "RESERVATION_PUBLISHED",
            "READY_UNUSED_AUTHORITY_STOP_PUBLISHED",
        ]
        variants.append(row)
        row = deepcopy(state)
        row["earlier_ready_dispositions"] = [
            "READY_UNUSED_AUTHORITY_STOP_PUBLISHED",
            "READY_UNUSED_REUSED",
        ]
        variants.append(row)
        return variants
    elif case_id == "B21":
        state["reservation_write_outcome"] = "UNKNOWN"
        state["postfetch_succeeded"] = False
        state["authoritative_reservation_presence"] = "UNKNOWN"
    elif case_id == "B22":
        variants = []
        row = deepcopy(state)
        row["ready_receipt_marked_consumed"] = True
        variants.append(row)
        row = deepcopy(state)
        row["fabricated_reservation_detected"] = True
        variants.append(row)
        return variants
    elif case_id == "B23":
        variants = []
        for key in (
            "authority_token",
            "challenge_id",
            "authority_challenge_id",
            "source_baseline_event",
            "source_closure",
            "formal_test_run_reservation_sha256",
        ):
            row = deepcopy(state)
            row["reservation"].pop(key)
            variants.append(row)
        row = deepcopy(state)
        row["reservation"]["formal_run_challenge_id"] = row[
            "reservation"
        ].pop("challenge_id")
        variants.append(row)
        return variants
    elif case_id == "B24":
        variants = []
        row = deepcopy(state)
        row["reservation"]["formal_test_run_reservation_sha256"] = "0" * 64
        variants.append(row)
        row = deepcopy(state)
        row["reservation"]["authority_challenge_id"] = "0" * 64
        variants.append(row)
        row = deepcopy(state)
        row["reservation"]["formal_run_challenge_id"] = "0" * 64
        variants.append(row)
        return variants
    else:
        raise AssertionError(f"unknown RED case: {case_id}")
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


def _target_api_or_red(
    role: str,
    case_id: str,
) -> Callable[[Mapping[str, Any]], Any]:
    owner_key, api_name = _TARGET_APIS[role]
    relative = _FUTURE_ROLE_PATHS[owner_key]
    absolute = _REPO_ROOT / relative
    if not absolute.is_file():
        pytest.fail(
            f"{case_id}_RECOVERY_EPOCH002_OWNER_PATH_NOT_IMPLEMENTED",
            pytrace=False,
        )
    module_name = (
        f"_emlis_nls_v3_recovery_epoch002_{role}_{case_id.lower()}_target"
    )
    spec = importlib.util.spec_from_file_location(module_name, absolute)
    if spec is None or spec.loader is None:
        pytest.fail(
            f"{case_id}_RECOVERY_EPOCH002_OWNER_IMPORT_NOT_PROVED",
            pytrace=False,
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    for export_name, expected in _REQUIRED_EXPORTS[role].items():
        if not hasattr(module, export_name):
            pytest.fail(
                f"{case_id}_{export_name}_NOT_IMPLEMENTED",
                pytrace=False,
            )
        if getattr(module, export_name) != expected:
            pytest.fail(
                f"{case_id}_{export_name}_CONTRACT_DRIFT",
                pytrace=False,
            )
    api = getattr(module, api_name, None)
    if not callable(api):
        pytest.fail(
            f"{case_id}_{api_name.upper()}_NOT_IMPLEMENTED",
            pytrace=False,
        )
    return api


def test_d1_authority_entry_and_protected_bytes_are_frozen() -> None:
    assert _AUTHORITY.endswith("RED_FREEZE_ONLY")
    assert re.fullmatch(r"[0-9a-f]{40}", _KAREN_DIARY_ENTRY)
    assert re.fullmatch(r"[0-9a-f]{40}", _COCOLON_ENTRY)
    assert re.fullmatch(r"[0-9a-f]{40}", _MASHOS_API_ENTRY)
    assert re.fullmatch(r"[0-9a-f]{40}", _MASHOS_API_ENTRY_TREE)
    assert re.fullmatch(r"[0-9a-f]{40}", _PARENT_DESIGN_BLOB)
    assert re.fullmatch(r"[0-9a-f]{64}", _PARENT_DESIGN_SHA256)
    assert re.fullmatch(r"[0-9a-f]{64}", _P0_EXTERNAL_IDENTITY_SHA256)
    assert _HERE.relative_to(_REPO_ROOT).as_posix() == _THIS_PATH
    for relative, expected in sorted(_PROTECTED_SHA256.items()):
        assert _sha256(_REPO_ROOT / relative) == expected


def test_current_epoch001_direct_parent_conflict_is_confirmed() -> None:
    path = _REPO_ROOT / _FUTURE_ROLE_PATHS["lineage_owner"].replace(
        "epoch002",
        "epoch001",
    )
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_reservation_record_valid"
    )
    function_source = ast.get_source_segment(source, function) or ""
    assert "publication.get(\"parent_commit_sha1s\")" in function_source
    assert "source_baseline_event" in function_source
    assert "== [event_commit]" in function_source
    assert "repository_snapshot" in function_source


def test_current_epoch001_bootstrap_and_checkpoint_gaps_are_confirmed() -> None:
    parent_path = _REPO_ROOT / _FUTURE_ROLE_PATHS[
        "formal_parent"
    ].replace("epoch002", "epoch001")
    runner_path = _REPO_ROOT / _FUTURE_ROLE_PATHS[
        "formal_runner"
    ].replace("epoch002", "epoch001")
    parent_source = parent_path.read_text(encoding="utf-8")
    runner_source = runner_path.read_text(encoding="utf-8")
    conftest_source = (_REPO_ROOT / "ai/tests/conftest.py").read_text(
        encoding="utf-8"
    )
    assert "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT" not in parent_source
    assert "pytest.main(" in runner_source
    assert "stdout=subprocess.DEVNULL" in runner_source
    assert "stderr=subprocess.DEVNULL" in runner_source
    assert "\"collection_node_ids\": list(expected_nodes)" in runner_source
    assert 'pytest_plugins = ("helpers.emlis_ai_fb172_migration",)' in (
        conftest_source
    )


def test_d1_exact_repair_boundary_and_matrix_are_closed() -> None:
    assert len(_FUTURE_ROLE_PATHS) == 9
    assert len(set(_FUTURE_ROLE_PATHS.values())) == 9
    assert len(_ROLE_OWNERS) == 12
    assert _FORMAL_PLUGIN_ALLOWLIST == ()
    assert _CONFTEST_PLUGIN_MODE == "DISABLED_BY_NOCONFTEST"
    assert _INSTALLER_IDENTITY_CLASS == "PIP_REQUIRE_HASHES_WHEEL_LOCK_V1"
    assert _FORMAL_PYTEST_OPTIONS == (
        "-q",
        "--disable-warnings",
        "--noconftest",
        "-p",
        "no:cacheprovider",
    )
    assert _IMPORT_CLASSIFICATIONS == {
        "FIRST_PARTY",
        "STDLIB_BOUND_TO_PYTHON_RUNTIME",
        "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
    }
    assert len(_P0_EXTERNAL_IDENTITY_KEYS) == 6
    assert len(_EXTERNAL_IDENTITY_KEYS) == 10
    assert len(_SOURCE_CLOSURE_KEYS) == 15
    assert len(_D2_FINAL_CLOSURE_PREIMAGE_KEYS) == 10
    assert len(_CANDIDATE_ALLOCATION_KEYS) == 8
    assert len(_EVENT1_KEYS) == 23
    assert len(_PUBLISHED_EVENT1_IDENTITY_KEYS) == 18
    assert len(_RESERVATION_KEYS) == 25
    assert len(_PRIOR_RESERVATION_ROW_KEYS) == 5
    assert len(_SUCCESS_LINEAGE_KEYS) == 8
    assert len(_READINESS_KEYS) == 30
    assert len(_PREFLIGHT_CHECKPOINT_KEYS) == 18
    assert len(_FORMAL_CHECKPOINT_KEYS) == 23
    assert len(_UNKNOWN_DISPOSITION_KEYS) == 13
    assert len(_TERMINAL_RESULT_KEYS) == 28
    assert len(_DIAGNOSTIC_KEYS) == 22
    assert len(_BOOTSTRAP_MANIFEST_KEYS) == 31
    assert len(_IMPORT_MANIFEST_ROW_KEYS) == 4
    assert len(_FIRST_PARTY_IMPORT_TARGET_KEYS) == 3
    assert len(_STDLIB_IMPORT_TARGET_KEYS) == 2
    assert len(_THIRD_PARTY_IMPORT_TARGET_KEYS) == 5
    assert len(_STAGE_GRAPH) == 13
    assert len(_DIAGNOSTIC_IDENTIFIER_ALLOWLIST) == 12
    assert set(_SELF_HASH_RULES.values()) == {
        "p0_external_identity_sha256",
        "candidate_allocation_sha256",
        "event_sha256",
        "bootstrap_closure_sha256",
        "bootstrap_readiness_receipt_sha256",
        "formal_test_run_reservation_sha256",
        "checkpoint_sha256",
        "formal_worker_result_sha256",
        "diagnostic_sha256",
        "attempt_consumption_unknown_disposition_sha256",
        "success_lineage_sha256",
    }
    ids = [row[0] for row in _RED_CASES]
    assert ids == [
        *(f"L{number:02d}" for number in range(1, 19)),
        *(f"B{number:02d}" for number in range(1, 25)),
    ]
    assert len(ids) == len(set(ids)) == 42


@pytest.mark.parametrize(
    ("case_id", "role", "expected_code"),
    _RED_CASES,
    ids=[row[0] for row in _RED_CASES],
)
def test_recovery_epoch002_minimum_causal_red_matrix(
    case_id: str,
    role: str,
    expected_code: str | None,
) -> None:
    api = _target_api_or_red(role, case_id)
    for state in _states_for_case(case_id, role):
        issues = _issue_codes(api(deepcopy(state)))
        if expected_code is None:
            assert issues == (), case_id
        else:
            assert issues == (expected_code,), case_id
