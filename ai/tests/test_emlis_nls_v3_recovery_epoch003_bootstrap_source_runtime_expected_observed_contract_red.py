# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for the Recovery Epoch 003 bootstrap/runtime contract.

This exact30 oracle freezes the P0-defined schema-pair dispatch,
pre-Event1 expected versus post-Event1 observed separation, Event1
immutability, independent operational projection, and pre-reservation
failure behavior.  It deliberately targets additive Epoch003 APIs on the
unchanged seven production owners.  Missing APIs fail inside each test, not
during collection.

All fixtures are body-free and in-memory.  This file does not materialize a
runtime, allocate a candidate, publish Event1, create readiness or a
reservation, invoke formal exact134, or advance Cycle 001.

The exact30 oracle denominator is distinct from the future formal-worker
manifest.  The embedded Epoch003 bootstrap fixture binds the authoritative
Step00--10 exact134 node sequence and its exact21 source manifest.
"""

import ast
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import re
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

from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    payload = dict(value)
    payload.pop(key, None)
    return _sha256_value(payload)


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_D1_BOOTSTRAP_SOURCE_"
    "RUNTIME_EXPECTED_OBSERVED_SEPARATION_SCHEMA_PAIR_DISPATCH_EVENT1_"
    "IMMUTABILITY_AND_INDEPENDENT_OPERATIONAL_PROJECTION_RED_FREEZE_ONLY"
)
_CORRECTION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_D1_BOOTSTRAP_FORMAL_"
    "EXACT134_MANIFEST_AND_REFERENCE_RUNTIME_ROOT_IDENTITY_BINDING_"
    "ORACLE_CORRECTION_AND_CAUSAL_RED_REFREEZE_ONLY"
)
_LOGICAL_CYCLE_ID = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH_ID = "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
_CANDIDATE_VERSION_ID = "fixture_only_unallocated_epoch003_candidate"
_REPOSITORY_FULL_NAME = "MassyuRed/mashos-api"
_SOURCE_REF = "refs/heads/main"
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_bootstrap_source_runtime_"
    "expected_observed_contract_red.py"
)
_P0_EXTERNAL_IDENTITY_SHA256 = (
    "74286b862eeee1663d2758ee18d1e848316da6fc27b12fef38c149c5a2b52f36"
)
_P0_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch003.p0_external_identity.v1"
)
_EPOCH002_SOURCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_closure.v1"
)
_EPOCH002_BOOTSTRAP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_bootstrap_manifest.v2"
)
_SOURCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "source_baseline_eligibility_closure.v1"
)
_BOOTSTRAP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "formal_worker_bootstrap_manifest.v1"
)
_REFERENCE_OBSERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "reference_runtime_observation.v1"
)
_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.sequence_event.v1"
)
_OPERATIONAL_OBSERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "operational_runtime_observation.v1"
)
_READINESS_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "bootstrap_readiness_receipt.v1"
)
_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "formal_worker_bootstrap_preflight_failure_receipt.v1"
)
_KNOWN_SCHEMA_PAIRS = (
    (_EPOCH002_SOURCE_SCHEMA, _EPOCH002_BOOTSTRAP_SCHEMA),
    (_SOURCE_SCHEMA, _BOOTSTRAP_SCHEMA),
)
_FAILURE_CLASSES = (
    "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
    "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
    "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
    "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
    "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
)
_STOP_CODE = "PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP"
_HISTORICAL_CHALLENGE_IDS = (
    "5d58979338cbc30ce603df884d466981895e05198196925e209424a129c4b0f9",
    "6c315203ce98f635feb80b04f27ab7dcb43545f2883b8a6fcca36c8c1cb7acf4",
)
_PREFLIGHT_CHALLENGE_ID = _sha256_text(
    "fixture-only-recovery-epoch003-preflight-challenge"
)
_PREFLIGHT_ID = _sha256_text(
    "fixture-only-recovery-epoch003-preflight-id"
)
_FORMAL_EXACT134_STEP_COUNTS = (4, 9, 14, 23, 19, 16, 5, 8, 9, 11, 16)
_FORMAL_EXACT134_NODE_IDS_SHA256 = (
    "0ab1039a35b8621a257617688cc5d63bb331f5c32dd08f34df1173a6b9e57118"
)

_REFERENCE_OBSERVATION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PreEvent1_ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event.json"
)
_OPERATIONAL_OBSERVATION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_OperationalRuntimeObservation_BodyFree_Receipt.json"
)
_READINESS_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_BootstrapReadiness_BodyFree_Receipt.json"
)
_FAILURE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_BootstrapPreflightFailure_BodyFree_Receipt.json"
)
_STANDALONE_PATHS = (
    _REFERENCE_OBSERVATION_PATH,
    _EVENT1_PATH,
    _OPERATIONAL_OBSERVATION_PATH,
    _READINESS_PATH,
    _FAILURE_PATH,
)
_PUBLICATION_ROLE_PATHS = {
    "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION": (
        _REFERENCE_OBSERVATION_PATH
    ),
    "RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT": _EVENT1_PATH,
    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION": (
        _OPERATIONAL_OBSERVATION_PATH
    ),
    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION_FAILURE_EVIDENCE": (
        _OPERATIONAL_OBSERVATION_PATH
    ),
    "RECOVERY_EPOCH003_BOOTSTRAP_READINESS": _READINESS_PATH,
    "RECOVERY_EPOCH003_FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE": (
        _FAILURE_PATH
    ),
}
_PUBLICATION_ROLES = tuple(_PUBLICATION_ROLE_PATHS)

_SOURCE_CLOSURE_KEYS = _keys(
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
_BOOTSTRAP_KEYS = _keys(
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
_REFERENCE_OBSERVATION_KEYS = _keys(
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
_EVENT_KEYS = _keys(
    """
    schema_version ledger_id event_id logical_cycle_id recovery_epoch_id
    candidate_version_id event_ordinal event_name state prior_event
    challenge_id timestamp_utc timestamp_kind authority p0_external_identity
    candidate_allocation source_closure bootstrap_closure
    primary_evidence_artifact publication body_free automatic_progression
    event_sha256
    """
)
_OPERATIONAL_OBSERVATION_KEYS = _keys(
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
_READINESS_KEYS = _keys(
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
_FAILURE_KEYS = _keys(
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
_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role body_free git_blob_sha1 identity_sha256
    logical_artifact_sha256 path publication_commit_sha1 raw_sha256
    repository_full_name schema_version
    """
)
_P0_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id parent_design receipt
    p0_external_identity_sha256
    """
)
_P0_PARENT_KEYS = _keys(
    "path publication_commit_sha1 git_blob_sha1 raw_sha256"
)
_P0_RECEIPT_KEYS = _keys(
    """
    path publication_commit_sha1 git_blob_sha1 raw_sha256
    logical_receipt_sha256
    """
)
_RUNTIME_IDENTITY_KEYS = _keys(
    "executable_sha256 implementation version build_sha256"
)
_DISTRIBUTION_KEYS = _keys(
    """
    normalized_distribution_name distribution_version wheel_sha256
    installed_record_closure_sha256
    """
)
_DEPENDENCY_LOCK_KEYS = _keys("identity_class path raw_sha256")
_RUNTIME_MATERIALIZATION_KEYS = _keys(
    """
    schema_version runtime_root_identity_sha256
    python_executable_relative_path installed_directory_relative_path
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    distribution_count runtime_materialization_state body_free
    runtime_materialization_sha256
    """
)
_ENVIRONMENT_POLICY_KEYS = _keys("fixed removed inherited_path_sha256 lang lc_all")
_ENVIRONMENT_FIXED_KEYS = _keys(
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD PYTHONDONTWRITEBYTECODE"
)
_OWNER_ROW_KEYS = _keys("role path git_blob_sha1 raw_sha256")
_TEST_ROW_KEYS = _keys("path git_blob_sha1 raw_sha256")
_IMPORT_ROW_KEYS = _keys(
    "import_name classification owner_paths target_identity"
)
_PROJECTION_KEYS = _keys(
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
_PARENT_PHASE_ORDER = (
    "REFERENCE_RUNTIME_OBSERVATION_PUBLISHED_AND_POSTVERIFIED",
    "SOURCE_BOOTSTRAP_CLOSURE_AND_OPERATIONAL_ADMISSION_"
    "PUBLISHED_AND_POSTVERIFIED",
    "CANDIDATE_ALLOCATED",
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT",
    "READINESS_OR_FAILURE_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
)

_ROLE_PATHS = {
    "closure": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "sequence": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "publication": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ),
    "independent": (
        "ai/tools/emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "execution": (
        "ai/tools/emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ),
    "parent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
    "preflight": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
}
_TARGET_APIS = {
    "closure": (
        _ROLE_PATHS["closure"],
        "validate_recovery_epoch003_source_bootstrap_contract_state",
    ),
    "sequence": (
        _ROLE_PATHS["sequence"],
        "validate_recovery_epoch003_sequence_event1_contract_state",
    ),
    "publication": (
        _ROLE_PATHS["publication"],
        "validate_recovery_epoch003_publication_contract_state",
    ),
    "independent": (
        _ROLE_PATHS["independent"],
        "verify_recovery_epoch003_bootstrap_source_runtime_contract",
    ),
    "execution": (
        _ROLE_PATHS["execution"],
        "validate_recovery_epoch003_formal_execution_gate_state",
    ),
    "parent": (
        _ROLE_PATHS["parent"],
        "validate_recovery_epoch003_parent_phase_state",
    ),
    "preflight": (
        _ROLE_PATHS["preflight"],
        "evaluate_recovery_epoch003_preflight_contract",
    ),
}
_REQUIRED_EXPORTS = {
    "closure": {
        "RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA": _SOURCE_SCHEMA,
        "RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA": _BOOTSTRAP_SCHEMA,
        "RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS": _SOURCE_CLOSURE_KEYS,
        "RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS": _BOOTSTRAP_KEYS,
        "RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS": _KNOWN_SCHEMA_PAIRS,
    },
    "sequence": {
        "RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA": _EVENT_SCHEMA,
        "RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS": _EVENT_KEYS,
    },
    "publication": {
        "RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS": (
            _PUBLICATION_ROLE_PATHS
        ),
    },
    "independent": {
        "RECOVERY_EPOCH003_OPERATIONAL_PROJECTION_KEYS": _PROJECTION_KEYS,
        "RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS": _KNOWN_SCHEMA_PAIRS,
        "RECOVERY_EPOCH003_FAILURE_CLASSES": _FAILURE_CLASSES,
    },
    "execution": {
        "RECOVERY_EPOCH003_READINESS_SCHEMA": _READINESS_SCHEMA,
        "RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE": _STOP_CODE,
    },
    "parent": {
        "RECOVERY_EPOCH003_PARENT_PHASE_ORDER": _PARENT_PHASE_ORDER,
    },
    "preflight": {
        "RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA": (
            _REFERENCE_OBSERVATION_SCHEMA
        ),
        "RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA": (
            _OPERATIONAL_OBSERVATION_SCHEMA
        ),
        "RECOVERY_EPOCH003_READINESS_SCHEMA": _READINESS_SCHEMA,
        "RECOVERY_EPOCH003_FAILURE_SCHEMA": _FAILURE_SCHEMA,
        "RECOVERY_EPOCH003_FAILURE_CLASSES": _FAILURE_CLASSES,
        "RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE": _STOP_CODE,
    },
}


def _p0_external_identity() -> dict[str, Any]:
    value = {
        "schema_version": _P0_SCHEMA,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "parent_design": {
            "path": (
                "EmlisAIの実装済み資料/documents/"
                "NLSv3_Step11_Cycle001_RecoveryEpoch002_Lineage02_"
                "Event1V2_BootstrapPreflightContractUnreachable_"
                "SourceBaselineInvalidationAndRecoveryEpoch003_"
                "ParentDesign_ReadOnly_20260729.md"
            ),
            "publication_commit_sha1": (
                "75add120f099b3775c837d918662926230ddbc99"
            ),
            "git_blob_sha1": (
                "faec07d12a277f4746e3aebd1db3778a12b67579"
            ),
            "raw_sha256": (
                "5fe64c022d8e21886c5531e102f673586c15b56d176072a556a4803a79681d4a"
            ),
        },
        "receipt": {
            "path": (
                "EmlisAIの実装済み資料/documents/"
                "NLSv3_Step11_Cycle001_RecoveryEpoch002_Lineage02_"
                "Event1V2_BootstrapPreflightContractUnreachable_"
                "SourceBaselineInvalidationAndRecoveryEpoch003_"
                "ParentDesign_ReadOnly_BodyFree_Receipt_20260729.json"
            ),
            "publication_commit_sha1": (
                "a4bdbc9fe144932fb445afcba81096f666d99d69"
            ),
            "git_blob_sha1": (
                "7139227bbb5cb67102024786059c13a069dfb3f8"
            ),
            "raw_sha256": (
                "dd4af55855eb82fc1de5725a6c10873967def2a0e8e56d4ebc293be4258bd045"
            ),
            "logical_receipt_sha256": (
                "904baff49d3efd09a4a1486298962646d7c56a7f90e3ce8191d7e26072cf66db"
            ),
        },
        "p0_external_identity_sha256": "",
    }
    value["p0_external_identity_sha256"] = _hash_without(
        value,
        "p0_external_identity_sha256",
    )
    return value


def _external_identity(
    *,
    role: str,
    schema: str,
    path: str,
    logical_hash: str,
) -> dict[str, Any]:
    value = {
        "artifact_role": role,
        "body_free": True,
        "git_blob_sha1": _sha1_text("fixture-blob:" + role + ":" + path),
        "identity_sha256": "",
        "logical_artifact_sha256": logical_hash,
        "path": path,
        "publication_commit_sha1": _sha1_text(
            "fixture-publication:" + role + ":" + path
        ),
        "raw_sha256": _sha256_text("fixture-raw:" + role + ":" + path),
        "repository_full_name": "MassyuRed/Cocolon",
        "schema_version": schema,
    }
    value["identity_sha256"] = _hash_without(value, "identity_sha256")
    return value


def _runtime_identity(label: str) -> dict[str, Any]:
    return {
        "executable_sha256": _sha256_text(label + ":python-executable"),
        "implementation": "CPython",
        "version": "3.13.fixture",
        "build_sha256": _sha256_text(label + ":python-build"),
    }


def _pytest_distribution(label: str) -> dict[str, Any]:
    return {
        "normalized_distribution_name": "pytest",
        "distribution_version": "8.4.1",
        "wheel_sha256": _sha256_text(label + ":pytest-wheel"),
        "installed_record_closure_sha256": _sha256_text(
            label + ":pytest-record"
        ),
    }


def _dependency_lock() -> dict[str, Any]:
    return {
        "identity_class": "EXACT_HASH_LOCK",
        "path": (
            "ai/configs/"
            "emlis_nls_v3_recovery_epoch002_formal_worker_"
            "bootstrap_lock_v1.json"
        ),
        "raw_sha256": _sha256_text("fixture:dependency-lock"),
    }


def _environment_policy() -> dict[str, Any]:
    return {
        "fixed": {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        "removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"],
        "inherited_path_sha256": _sha256_text("fixture:inherited-path"),
        "lang": "C.UTF-8",
        "lc_all": "C.UTF-8",
    }


def _runtime_materialization(label: str) -> dict[str, Any]:
    lock = _dependency_lock()
    value = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "runtime_materialization.v1"
        ),
        "runtime_root_identity_sha256": _sha256_text(
            label + ":opaque-runtime-root"
        ),
        "python_executable_relative_path": "bin/python",
        "installed_directory_relative_path": "installed",
        "dependency_lock_raw_sha256": lock["raw_sha256"],
        "wheel_bundle_manifest_sha256": _sha256_text(
            "fixture:wheel-bundle"
        ),
        "distribution_count": 1,
        "runtime_materialization_state": "MATERIALIZED_FIXTURE_ONLY",
        "body_free": True,
        "runtime_materialization_sha256": "",
    }
    value["runtime_materialization_sha256"] = _hash_without(
        value,
        "runtime_materialization_sha256",
    )
    return value


def _owner_artifacts() -> list[dict[str, Any]]:
    role_by_path = {
        _ROLE_PATHS["closure"]: "canonical_current_closure",
        _ROLE_PATHS["sequence"]: "sequence_ledger",
        _ROLE_PATHS["publication"]: "atomic_publication_bundle",
        _ROLE_PATHS["independent"]: "independent_closure_verifier",
        _ROLE_PATHS["execution"]: "current_step_proof_gate",
        _ROLE_PATHS["parent"]: "formal_parent_orchestrator",
        _ROLE_PATHS["preflight"]: "formal_worker_bootstrap_preflight",
    }
    return [
        {
            "role": role,
            "path": path,
            "git_blob_sha1": _sha1_text("fixture-owner-blob:" + path),
            "raw_sha256": _sha256_text("fixture-owner-raw:" + path),
        }
        for path, role in sorted(
            role_by_path.items(),
            key=lambda row: (row[1], row[0]),
        )
    ]


def _formal_test_manifest() -> list[dict[str, Any]]:
    paths = sorted(
        {
            node_id.split("::", 1)[0]
            for node_id in _formal_exact134_node_ids()
        }
    )
    return [
        {
            "path": path,
            "git_blob_sha1": _sha1_text(
                "fixture-formal-test-blob:" + path
            ),
            "raw_sha256": _sha256_text(
                "fixture-formal-test-raw:" + path
            ),
        }
        for path in paths
    ]


def _import_manifest(
    python_identity: Mapping[str, Any],
    pytest_identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    python_hash = _sha256_value(python_identity)
    return [
        {
            "import_name": "emlis_ai_nls_v3_artifact_contract",
            "classification": "FIRST_PARTY",
            "owner_paths": [
                "ai/services/ai_inference/"
                "emlis_ai_nls_v3_artifact_contract.py"
            ],
            "target_identity": {
                "path": (
                    "ai/services/ai_inference/"
                    "emlis_ai_nls_v3_artifact_contract.py"
                ),
                "git_blob_sha1": _sha1_text(
                    "fixture:artifact-contract-blob"
                ),
                "raw_sha256": _sha256_text(
                    "fixture:artifact-contract-raw"
                ),
            },
        },
        {
            "import_name": "hashlib",
            "classification": "STDLIB_BOUND_TO_PYTHON_RUNTIME",
            "owner_paths": [],
            "target_identity": {
                "module_name": "hashlib",
                "python_runtime_identity_sha256": python_hash,
            },
        },
        {
            "import_name": "pytest",
            "classification": "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
            "owner_paths": [],
            "target_identity": {
                "module_name": "pytest",
                **dict(pytest_identity),
            },
        },
    ]


def _reference_observation() -> dict[str, Any]:
    python_identity = _runtime_identity("expected")
    pytest_identity = _pytest_distribution("expected")
    installed = [deepcopy(pytest_identity)]
    environment = _environment_policy()
    value = {
        "schema_version": _REFERENCE_OBSERVATION_SCHEMA,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "authority_token": "FIXTURE_ONLY_UNISSUED_REFERENCE_AUTHORITY",
        "source_commit_sha1": _sha1_text("fixture:source-commit"),
        "source_tree_sha1": _sha1_text("fixture:source-tree"),
        "dependency_lock_identity": _dependency_lock(),
        "wheel_bundle_manifest_sha256": _sha256_text(
            "fixture:wheel-bundle"
        ),
        "runtime_materialization": _runtime_materialization("reference"),
        "python_runtime_identity": python_identity,
        "pytest_distribution_identity": pytest_identity,
        "installed_distributions": installed,
        "installed_distributions_sha256": _sha256_value(installed),
        "environment_policy": environment,
        "environment_policy_sha256": _sha256_value(environment),
        "reservation_count_delta": 0,
        "formal_exact134_invocation_count": 0,
        "collection_state": "NOT_STARTED",
        "test_execution_state": "NOT_STARTED",
        "body_free": True,
        "reference_runtime_observation_sha256": "",
    }
    value["reference_runtime_observation_sha256"] = _hash_without(
        value,
        "reference_runtime_observation_sha256",
    )
    return value


def _bootstrap_closure(
    reference: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> dict[str, Any]:
    owners = _owner_artifacts()
    tests = _formal_test_manifest()
    imports = _import_manifest(
        reference["python_runtime_identity"],
        reference["pytest_distribution_identity"],
    )
    environment = deepcopy(reference["environment_policy"])
    preflight_argv = [
        "python",
        "-m",
        "ai.tools.emlis_nls_v3_recovery_epoch002_"
        "formal_worker_bootstrap_preflight",
    ]
    formal_argv = [
        "python",
        "-m",
        "pytest",
        "--noconftest",
        "-p",
        "no:cacheprovider",
        *_formal_exact134_node_ids(),
    ]
    value = {
        "schema_version": _BOOTSTRAP_SCHEMA,
        "source_commit_sha1": reference["source_commit_sha1"],
        "source_tree_sha1": reference["source_tree_sha1"],
        "formal_owner_artifacts": owners,
        "formal_owner_artifacts_sha256": _sha256_value(owners),
        "formal_test_node_ids": list(_formal_exact134_node_ids()),
        "formal_test_manifest": tests,
        "formal_test_manifest_sha256": _sha256_value(tests),
        "conftest_plugin_mode": "NOCONFTEST",
        "pytest_plugins_environment_variable_removed": True,
        "pytest_entrypoint_autoload_disabled": True,
        "explicit_plugin_allowlist": [],
        "loaded_plugin_manifest": [],
        "loaded_plugin_manifest_sha256": _sha256_value([]),
        "import_manifest": imports,
        "import_manifest_sha256": _sha256_value(imports),
        "dependency_lock_identity": deepcopy(
            reference["dependency_lock_identity"]
        ),
        "wheel_bundle_manifest_sha256": reference[
            "wheel_bundle_manifest_sha256"
        ],
        "expected_installed_distributions": deepcopy(
            reference["installed_distributions"]
        ),
        "expected_installed_distributions_sha256": reference[
            "installed_distributions_sha256"
        ],
        "expected_python_runtime_identity": deepcopy(
            reference["python_runtime_identity"]
        ),
        "expected_pytest_distribution_identity": deepcopy(
            reference["pytest_distribution_identity"]
        ),
        "reference_runtime_observation_external_identity": deepcopy(
            reference_identity
        ),
        "environment_policy": environment,
        "environment_policy_sha256": _sha256_value(environment),
        "preflight_argv": preflight_argv,
        "preflight_argv_sha256": _sha256_value(preflight_argv),
        "formal_worker_argv": formal_argv,
        "formal_worker_argv_sha256": _sha256_value(formal_argv),
        "unclassified_import_count": 0,
        "unresolved_dynamic_import_count": 0,
        "body_free": True,
        "bootstrap_closure_sha256": "",
    }
    value["bootstrap_closure_sha256"] = _hash_without(
        value,
        "bootstrap_closure_sha256",
    )
    return value


def _source_closure(
    reference_identity: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
) -> dict[str, Any]:
    value = {
        "schema_version": _SOURCE_SCHEMA,
        "repository_full_name": _REPOSITORY_FULL_NAME,
        "source_ref": _SOURCE_REF,
        "source_commit_sha1": bootstrap["source_commit_sha1"],
        "source_tree_sha1": bootstrap["source_tree_sha1"],
        "worktree_clean": True,
        "detailed_design_sha256": (
            "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
        ),
        "epoch003_p0_external_identity_sha256": (
            _P0_EXTERNAL_IDENTITY_SHA256
        ),
        "epoch002_predecessor_set_sha256": _sha256_text(
            "fixture:epoch002-predecessor-set"
        ),
        "d1_red_receipt_external_identity_sha256": _sha256_text(
            "fixture:d1-red-receipt"
        ),
        "d2_green_receipt_external_identity_sha256": _sha256_text(
            "fixture:d2-green-receipt"
        ),
        "source_dependency_closure_sha256": _sha256_text(
            "fixture:source-dependency-closure"
        ),
        "canonical_current_closure_sha256": _sha256_text(
            "fixture:canonical-current-closure"
        ),
        "requirement_registry_sha256": _sha256_text(
            "fixture:requirement-registry"
        ),
        "formal_node_registry_sha256": _sha256_text(
            "fixture:formal-node-registry"
        ),
        "proof_source_closure_sha256": _sha256_text(
            "fixture:proof-source-closure"
        ),
        "formal_test_manifest_sha256": bootstrap[
            "formal_test_manifest_sha256"
        ],
        "bootstrap_closure_sha256": bootstrap["bootstrap_closure_sha256"],
        "reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "source_closure_sha256": "",
    }
    value["source_closure_sha256"] = _hash_without(
        value,
        "source_closure_sha256",
    )
    return value


def _operational_admission_identity() -> dict[str, Any]:
    logical_hash = _sha256_text("fixture:operational-admission")
    return _external_identity(
        role="RECOVERY_EPOCH003_OPERATIONAL_ADMISSION",
        schema=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "OperationalAdmission_BodyFree_Receipt.json"
        ),
        logical_hash=logical_hash,
    )


def _primary_evidence_identity() -> dict[str, Any]:
    logical_hash = _sha256_text("fixture:d2-green-evidence")
    return _external_identity(
        role="RECOVERY_EPOCH003_D2_GREEN_RECEIPT",
        schema=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d2_green_receipt.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "D2_GREEN_BodyFree_Receipt.json"
        ),
        logical_hash=logical_hash,
    )


def _candidate_allocation(
    source: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> dict[str, Any]:
    value = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "candidate_allocation.v1"
        ),
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": _CANDIDATE_VERSION_ID,
        "allocated_at_utc": "2026-07-29T00:00:00Z",
        "p0_external_identity_sha256": _P0_EXTERNAL_IDENTITY_SHA256,
        "source_closure_sha256": source["source_closure_sha256"],
        "reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "candidate_allocation_sha256": "",
    }
    value["candidate_allocation_sha256"] = _hash_without(
        value,
        "candidate_allocation_sha256",
    )
    return value


def _event1(
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
) -> dict[str, Any]:
    p0 = _p0_external_identity()
    candidate = _candidate_allocation(source, reference_identity)
    operational_admission = _operational_admission_identity()
    primary = _primary_evidence_identity()
    supporting = sorted(
        [deepcopy(reference_identity), deepcopy(primary)],
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        ),
    )
    publication = {
        "base_commit_sha1": _sha1_text("fixture:event1-base-commit"),
        "branch": "main",
        "event_path": _EVENT1_PATH,
        "expected_changed_path_count": 1 + len(supporting),
        "publication_state": "FIXTURE_ONLY_NOT_PUBLISHED",
        "repository_full_name": "MassyuRed/Cocolon",
        "supporting_artifact_count": len(supporting),
        "supporting_artifact_set_sha256": _sha256_value(supporting),
        "supporting_artifacts": supporting,
    }
    value = {
        "schema_version": _EVENT_SCHEMA,
        "ledger_id": "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003",
        "event_id": "NLS_V3_RECOVERY_EPOCH003_SEQUENCE_EVENT_01",
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": _CANDIDATE_VERSION_ID,
        "event_ordinal": 1,
        "event_name": "SOURCE_BASELINE_LOCKED",
        "state": "PUBLISHED_POSTVERIFIED_FIXTURE_ONLY",
        "prior_event": deepcopy(p0),
        "challenge_id": _sha256_text("fixture:epoch003-event1-challenge"),
        "timestamp_utc": "2026-07-29T00:01:00Z",
        "timestamp_kind": "FIXTURE_ONLY",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_AUTHORITY_FIXTURE_ONLY",
            "operational_admission": operational_admission,
            "publication_authority_token": (
                "FIXTURE_ONLY_UNISSUED_EVENT1_PUBLICATION_AUTHORITY"
            ),
            "transition_authority_token": (
                "FIXTURE_ONLY_UNISSUED_EVENT1_TRANSITION_AUTHORITY"
            ),
        },
        "p0_external_identity": deepcopy(p0),
        "candidate_allocation": candidate,
        "source_closure": deepcopy(source),
        "bootstrap_closure": deepcopy(bootstrap),
        "primary_evidence_artifact": primary,
        "publication": publication,
        "body_free": True,
        "automatic_progression": False,
        "event_sha256": "",
    }
    value["event_sha256"] = _hash_without(value, "event_sha256")
    return value


def _projection_from_event(event: Mapping[str, Any]) -> dict[str, Any]:
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


def _projection_from_operational(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: deepcopy(observation[key])
        for key in _PROJECTION_KEYS
    }


def _operational_observation(
    event: Mapping[str, Any],
    event_identity: Mapping[str, Any],
    reference_runtime_root_identity_sha256: str,
) -> dict[str, Any]:
    expected = _projection_from_event(event)
    operational_runtime = _runtime_materialization("operational")
    value = {
        "schema_version": _OPERATIONAL_OBSERVATION_SCHEMA,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": _CANDIDATE_VERSION_ID,
        "authority_token": "FIXTURE_ONLY_UNISSUED_PREFLIGHT_AUTHORITY",
        "preflight_challenge_id": _PREFLIGHT_CHALLENGE_ID,
        "preflight_id": _PREFLIGHT_ID,
        "source_baseline_event_external_identity_sha256": event_identity[
            "identity_sha256"
        ],
        "source_closure_sha256": event["source_closure"][
            "source_closure_sha256"
        ],
        "bootstrap_closure_sha256": event["bootstrap_closure"][
            "bootstrap_closure_sha256"
        ],
        "source_commit_sha1": expected["source_commit_sha1"],
        "source_tree_sha1": expected["source_tree_sha1"],
        "worktree_clean": True,
        "formal_owner_artifacts_sha256": expected[
            "formal_owner_artifacts_sha256"
        ],
        "formal_test_manifest_sha256": expected[
            "formal_test_manifest_sha256"
        ],
        "import_manifest_sha256": expected["import_manifest_sha256"],
        "dependency_lock_raw_sha256": expected[
            "dependency_lock_raw_sha256"
        ],
        "wheel_bundle_manifest_sha256": expected[
            "wheel_bundle_manifest_sha256"
        ],
        "installed_distributions_sha256": expected[
            "installed_distributions_sha256"
        ],
        "pytest_distribution_identity": deepcopy(
            expected["pytest_distribution_identity"]
        ),
        "python_runtime_identity": deepcopy(
            expected["python_runtime_identity"]
        ),
        "loaded_plugin_manifest_sha256": expected[
            "loaded_plugin_manifest_sha256"
        ],
        "preflight_argv_sha256": expected["preflight_argv_sha256"],
        "formal_worker_argv_sha256": expected[
            "formal_worker_argv_sha256"
        ],
        "environment_policy": deepcopy(
            event["bootstrap_closure"]["environment_policy"]
        ),
        "environment_policy_sha256": expected[
            "environment_policy_sha256"
        ],
        "runtime_materialization": operational_runtime,
        "runtime_root_identity_sha256": operational_runtime[
            "runtime_root_identity_sha256"
        ],
        "reference_runtime_root_identity_sha256": (
            reference_runtime_root_identity_sha256
        ),
        "attempt_registry_root_identity_sha256": _sha256_text(
            "fixture:attempt-registry-root"
        ),
        "owner_operational_projection_sha256": "",
        "independent_operational_projection_sha256": "",
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "reservation_count_delta": 0,
        "formal_exact134_invocation_count": 0,
        "collection_state": "NOT_STARTED",
        "test_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "body_free": True,
        "operational_runtime_observation_sha256": "",
    }
    observed = _projection_from_operational(value)
    projection_hash = _sha256_value(observed)
    value["owner_operational_projection_sha256"] = projection_hash
    value["independent_operational_projection_sha256"] = projection_hash
    value["operational_runtime_observation_sha256"] = _hash_without(
        value,
        "operational_runtime_observation_sha256",
    )
    return value


def _readiness_receipt(
    event: Mapping[str, Any],
    event_identity: Mapping[str, Any],
    observation: Mapping[str, Any],
    observation_identity: Mapping[str, Any],
) -> dict[str, Any]:
    expected_hash = _sha256_value(_projection_from_event(event))
    observed_hash = _sha256_value(
        _projection_from_operational(observation)
    )
    value = {
        "schema_version": _READINESS_SCHEMA,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": _CANDIDATE_VERSION_ID,
        "authority_token": "FIXTURE_ONLY_UNISSUED_PREFLIGHT_AUTHORITY",
        "event1_external_identity_sha256": event_identity[
            "identity_sha256"
        ],
        "event1_bootstrap_closure": deepcopy(event["bootstrap_closure"]),
        "event1_bootstrap_closure_sha256": event["bootstrap_closure"][
            "bootstrap_closure_sha256"
        ],
        "operational_runtime_observation_external_identity": deepcopy(
            observation_identity
        ),
        "operational_runtime_observation_sha256": observation[
            "operational_runtime_observation_sha256"
        ],
        "expected_observed_projection_sha256": _sha256_value(
            {"expected": expected_hash, "observed": observed_hash}
        ),
        "readiness_receipt_path": _READINESS_PATH,
        "preflight_started_at_utc": "2026-07-29T00:02:00Z",
        "preflight_finished_at_utc": "2026-07-29T00:03:00Z",
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "reservation_count_delta": 0,
        "formal_exact134_invocation_count": 0,
        "collection_state": "NOT_STARTED",
        "test_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "automatic_progression": False,
        "body_free": True,
        "bootstrap_readiness_receipt_sha256": "",
    }
    value["bootstrap_readiness_receipt_sha256"] = _hash_without(
        value,
        "bootstrap_readiness_receipt_sha256",
    )
    return value


def _baseline_state() -> dict[str, Any]:
    reference = _reference_observation()
    reference_identity = _external_identity(
        role="RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION",
        schema=_REFERENCE_OBSERVATION_SCHEMA,
        path=_REFERENCE_OBSERVATION_PATH,
        logical_hash=reference["reference_runtime_observation_sha256"],
    )
    bootstrap = _bootstrap_closure(reference, reference_identity)
    source = _source_closure(reference_identity, bootstrap)
    event = _event1(source, bootstrap, reference_identity)
    event_identity = _external_identity(
        role="RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT",
        schema=_EVENT_SCHEMA,
        path=_EVENT1_PATH,
        logical_hash=event["event_sha256"],
    )
    operational = _operational_observation(
        event,
        event_identity,
        reference["runtime_materialization"][
            "runtime_root_identity_sha256"
        ],
    )
    operational_identity = _external_identity(
        role="RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
        schema=_OPERATIONAL_OBSERVATION_SCHEMA,
        path=_OPERATIONAL_OBSERVATION_PATH,
        logical_hash=operational[
            "operational_runtime_observation_sha256"
        ],
    )
    readiness = _readiness_receipt(
        event,
        event_identity,
        operational,
        operational_identity,
    )
    return {
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": _CANDIDATE_VERSION_ID,
        "source_closure": source,
        "bootstrap_closure": bootstrap,
        "reference_runtime_observation": reference,
        "reference_runtime_observation_external_identity": (
            reference_identity
        ),
        "event1_at_publication": event,
        "event1_at_postfetch": deepcopy(event),
        "event1_external_identity": event_identity,
        "event1_publication_raw_sha256": hashlib.sha256(
            _canonical_bytes(event) + b"\n"
        ).hexdigest(),
        "event1_postfetch_raw_sha256": hashlib.sha256(
            _canonical_bytes(event) + b"\n"
        ).hexdigest(),
        "operational_runtime_observation": operational,
        "operational_runtime_observation_external_identity": (
            operational_identity
        ),
        "expected_operational_projection": _projection_from_event(event),
        "owner_operational_projection": _projection_from_operational(
            operational
        ),
        "independent_operational_projection": (
            _projection_from_operational(operational)
        ),
        "readiness_candidate": readiness,
        "failure_candidate": None,
        "preflight_challenge_id": _PREFLIGHT_CHALLENGE_ID,
        "preflight_id": _PREFLIGHT_ID,
        "preflight_started_at_utc": "2026-07-29T00:02:00Z",
        "preflight_finished_at_utc": "2026-07-29T00:03:00Z",
        "reference_materialization_performed": True,
        "operational_materialization_performed": True,
        "reservation_count_delta": 0,
        "attempt_id": None,
        "formal_exact134_invocation_count": 0,
        "collection_state": "NOT_STARTED",
        "test_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "automatic_progression": False,
        "body_free": True,
    }


def _refresh_event_state(state: dict[str, Any]) -> None:
    event = state["event1_at_postfetch"]
    event["event_sha256"] = _hash_without(event, "event_sha256")
    state["event1_postfetch_raw_sha256"] = hashlib.sha256(
        _canonical_bytes(event) + b"\n"
    ).hexdigest()


def _refresh_operational_state(
    state: dict[str, Any],
    *,
    independent_projection: Mapping[str, Any] | None = None,
) -> None:
    observation = state["operational_runtime_observation"]
    owner_projection = _projection_from_operational(observation)
    independent = deepcopy(
        independent_projection
        if independent_projection is not None
        else owner_projection
    )
    state["owner_operational_projection"] = owner_projection
    state["independent_operational_projection"] = independent
    observation["owner_operational_projection_sha256"] = _sha256_value(
        owner_projection
    )
    observation[
        "independent_operational_projection_sha256"
    ] = _sha256_value(independent)
    observation["operational_runtime_observation_sha256"] = _hash_without(
        observation,
        "operational_runtime_observation_sha256",
    )
    role = (
        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
        if owner_projection == independent
        else (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION_"
            "FAILURE_EVIDENCE"
        )
    )
    state["operational_runtime_observation_external_identity"] = (
        _external_identity(
            role=role,
            schema=_OPERATIONAL_OBSERVATION_SCHEMA,
            path=_OPERATIONAL_OBSERVATION_PATH,
            logical_hash=observation[
                "operational_runtime_observation_sha256"
            ],
        )
    )
    state["readiness_candidate"] = _readiness_receipt(
        state["event1_at_publication"],
        state["event1_external_identity"],
        observation,
        state["operational_runtime_observation_external_identity"],
    )


def _failure_input(failure_class: str) -> dict[str, Any]:
    state = _baseline_state()
    if failure_class == "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED":
        state["source_closure"]["schema_version"] = _EPOCH002_SOURCE_SCHEMA
        state["source_closure"]["source_closure_sha256"] = _hash_without(
            state["source_closure"],
            "source_closure_sha256",
        )
        state["event1_at_publication"]["source_closure"] = deepcopy(
            state["source_closure"]
        )
        state["event1_at_publication"]["event_sha256"] = _hash_without(
            state["event1_at_publication"],
            "event_sha256",
        )
        state["operational_materialization_performed"] = False
        state["operational_runtime_observation"] = None
        state["operational_runtime_observation_external_identity"] = None
        state["owner_operational_projection"] = None
        state["independent_operational_projection"] = None
        state["readiness_candidate"] = None
    elif failure_class == "SOURCE_BOOTSTRAP_BASELINE_MISMATCH":
        state["source_closure"]["source_tree_sha1"] = _sha1_text(
            "fixture:mismatched-source-tree"
        )
        state["source_closure"]["source_closure_sha256"] = _hash_without(
            state["source_closure"],
            "source_closure_sha256",
        )
        state["operational_materialization_performed"] = False
        state["operational_runtime_observation"] = None
        state["operational_runtime_observation_external_identity"] = None
        state["owner_operational_projection"] = None
        state["independent_operational_projection"] = None
        state["readiness_candidate"] = None
    elif failure_class == "OPERATIONAL_MATERIALIZATION_BINDING_MISSING":
        state["operational_runtime_observation"] = None
        state["operational_runtime_observation_external_identity"] = None
        state["owner_operational_projection"] = None
        state["independent_operational_projection"] = None
        state["readiness_candidate"] = None
    elif failure_class == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH":
        observation = state["operational_runtime_observation"]
        observation["python_runtime_identity"]["executable_sha256"] = (
            _sha256_text("fixture:mismatched-operational-python")
        )
        _refresh_operational_state(state)
    elif (
        failure_class
        == "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
    ):
        independent = deepcopy(state["independent_operational_projection"])
        independent["environment_policy_sha256"] = _sha256_text(
            "fixture:independent-projection-disagreement"
        )
        _refresh_operational_state(
            state,
            independent_projection=independent,
        )
    else:
        raise AssertionError(failure_class)
    state["failure_candidate"] = "EVALUATOR_MUST_BUILD_EXACT29"
    return state


def _issue_codes(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple) and all(
        isinstance(item, str) for item in value
    ):
        return value
    if isinstance(value, list) and all(
        isinstance(item, str) for item in value
    ):
        return tuple(value)
    if isinstance(value, Mapping):
        for key in ("issue_codes", "issues", "validation_issues"):
            if key in value:
                return _issue_codes(value[key])
    raise AssertionError(f"unexpected issue-code result: {type(value)!r}")


def _assert_failure_receipt(
    receipt: Any,
    failure_class: str,
) -> None:
    assert isinstance(receipt, Mapping)
    assert set(receipt) == _FAILURE_KEYS
    assert len(receipt) == 29
    assert receipt["schema_version"] == _FAILURE_SCHEMA
    assert receipt["logical_cycle_id"] == _LOGICAL_CYCLE_ID
    assert receipt["recovery_epoch_id"] == _RECOVERY_EPOCH_ID
    assert receipt["candidate_version_id"] == _CANDIDATE_VERSION_ID
    assert receipt["preflight_challenge_id"] == _PREFLIGHT_CHALLENGE_ID
    assert receipt["preflight_id"] == _PREFLIGHT_ID
    assert receipt["failure_class"] == failure_class
    assert receipt["failure_issue_codes"]
    assert receipt["failure_issue_codes"] == sorted(
        set(receipt["failure_issue_codes"])
    )
    assert receipt["stop_code"] == _STOP_CODE
    assert receipt["reservation_count_delta"] == 0
    assert receipt["attempt_id"] is None
    assert receipt["formal_exact134_invocation_count"] == 0
    assert receipt["automatic_retry"] is False
    assert receipt["automatic_progression"] is False
    assert receipt["body_free"] is True
    assert receipt["receipt_sha256"] == _hash_without(
        receipt,
        "receipt_sha256",
    )
    observation_identity = receipt[
        "operational_runtime_observation_external_identity"
    ]
    observation_hash = receipt["operational_runtime_observation_sha256"]
    owner_hash = receipt["owner_operational_projection_sha256"]
    independent_hash = receipt[
        "independent_operational_projection_sha256"
    ]
    expected_observed_hash = receipt[
        "expected_observed_projection_sha256"
    ]
    if failure_class in {
        "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
        "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
    }:
        assert receipt["failure_stage"] == "BEFORE_MATERIALIZATION"
        assert (
            observation_identity,
            observation_hash,
            owner_hash,
            independent_hash,
            expected_observed_hash,
        ) == (None, None, None, None, None)
    elif failure_class == "OPERATIONAL_MATERIALIZATION_BINDING_MISSING":
        assert receipt["failure_stage"] == "MATERIALIZATION_BINDING"
        assert (
            observation_identity,
            observation_hash,
            owner_hash,
            independent_hash,
            expected_observed_hash,
        ) == (None, None, None, None, None)
    elif failure_class == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH":
        assert receipt["failure_stage"] == "EXPECTED_OBSERVED_COMPARISON"
        assert set(observation_identity) == _EXTERNAL_IDENTITY_KEYS
        assert observation_hash == observation_identity[
            "logical_artifact_sha256"
        ]
        assert re.fullmatch(r"[0-9a-f]{64}", owner_hash)
        assert re.fullmatch(r"[0-9a-f]{64}", independent_hash)
        assert owner_hash == independent_hash
        expected_hash = _sha256_value(
            _projection_from_event(
                _failure_input(failure_class)["event1_at_publication"]
            )
        )
        assert expected_observed_hash == _sha256_value(
            {"expected": expected_hash, "observed": owner_hash}
        )
    else:
        assert failure_class == (
            "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
        )
        assert receipt["failure_stage"] == "INDEPENDENT_PROJECTION"
        assert set(observation_identity) == _EXTERNAL_IDENTITY_KEYS
        assert observation_hash == observation_identity[
            "logical_artifact_sha256"
        ]
        assert re.fullmatch(r"[0-9a-f]{64}", owner_hash)
        assert re.fullmatch(r"[0-9a-f]{64}", independent_hash)
        assert owner_hash != independent_hash
        assert expected_observed_hash == _sha256_value(
            {"owner": owner_hash, "independent": independent_hash}
        )


def _assert_readiness_receipt(receipt: Any) -> None:
    assert isinstance(receipt, Mapping)
    assert set(receipt) == _READINESS_KEYS
    assert len(receipt) == 24
    assert receipt["schema_version"] == _READINESS_SCHEMA
    assert receipt["readiness_receipt_path"] == _READINESS_PATH
    assert receipt["reservation_count_delta"] == 0
    assert receipt["formal_exact134_invocation_count"] == 0
    assert receipt["collection_state"] == "NOT_STARTED"
    assert receipt["test_execution_state"] == "NOT_STARTED"
    assert receipt["pytest_main_called"] is False
    assert receipt["automatic_progression"] is False
    assert receipt["body_free"] is True
    assert receipt["bootstrap_readiness_receipt_sha256"] == _hash_without(
        receipt,
        "bootstrap_readiness_receipt_sha256",
    )


_CASES = (
    ("S01", "known_epoch002_schema_pair_preserved", "closure"),
    ("S02", "epoch003_schema_pair_supported", "closure"),
    ("S03", "mixed_schema_pair_rejected", "closure"),
    ("S04", "unknown_schema_pair_rejected", "independent"),
    ("R01", "reference_external_identity_bound", "closure"),
    ("R02", "reference_operational_roots_distinct", "preflight"),
    ("R03", "runtime_and_pytest_parity", "preflight"),
    ("R04", "lock_record_and_distribution_parity", "preflight"),
    ("R05", "source_owner_plugin_argv_environment_parity", "independent"),
    ("R06", "operational_materialization_binding_required", "preflight"),
    ("E01", "event1_excludes_operational_facts", "sequence"),
    ("E02", "placeholder_runtime_identity_rejected", "closure"),
    ("E03", "event1_postfetch_bytes_immutable", "sequence"),
    ("E04", "epoch002_challenge_not_inherited", "sequence"),
    ("I01", "owner_independent_projection_equal", "independent"),
    ("I02", "independent_owner_import_separation", "independent"),
    ("I03", "projection_disagreement_fails_closed", "independent"),
    ("F01", "schema_unsupported_failure_receipt", "preflight"),
    ("F02", "baseline_mismatch_failure_receipt", "preflight"),
    ("F03", "materialization_missing_failure_receipt", "preflight"),
    ("F04", "runtime_mismatch_failure_receipt", "preflight"),
    ("F05", "independent_disagreement_failure_receipt", "preflight"),
    ("P01", "readiness_or_failure_exact_one", "preflight"),
    ("P02", "every_failure_zero_effects", "preflight"),
    ("P03", "execution_gate_requires_postverified_readiness", "execution"),
    ("P04", "parent_phase_order_and_no_autoprogression", "parent"),
    ("A01", "artifact_paths_and_roles", "publication"),
    ("A02", "nested_source_bootstrap_only_in_event1", "sequence"),
    ("A03", "publication_candidate_scope", "publication"),
    ("A04", "all_required_owner_paths_bound", "closure"),
)
_CASE_BY_ID = {row[0]: row for row in _CASES}


def _oracle_node_ids() -> tuple[str, ...]:
    return tuple(
        f"{_THIS_PATH}::test_{case_id.lower()}_{boundary}"
        for case_id, boundary, _role in _CASES
    )


def _formal_exact134_node_ids() -> tuple[str, ...]:
    return tuple(
        node_id
        for step in range(11)
        for node_id in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
    )


def _assert_static_contract() -> None:
    assert _AUTHORITY.endswith("RED_FREEZE_ONLY")
    assert _CORRECTION_AUTHORITY == (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_D1_BOOTSTRAP_FORMAL_"
        "EXACT134_MANIFEST_AND_REFERENCE_RUNTIME_ROOT_IDENTITY_BINDING_"
        "ORACLE_CORRECTION_AND_CAUSAL_RED_REFREEZE_ONLY"
    )
    assert _HERE.relative_to(_REPO_ROOT).as_posix() == _THIS_PATH
    assert len(_ROLE_PATHS) == len(set(_ROLE_PATHS.values())) == 7
    assert all((_REPO_ROOT / path).is_file() for path in _ROLE_PATHS.values())
    assert len(_STANDALONE_PATHS) == len(set(_STANDALONE_PATHS)) == 5
    assert len(_PUBLICATION_ROLE_PATHS) == 6
    assert set(_PUBLICATION_ROLE_PATHS.values()) == set(_STANDALONE_PATHS)
    assert len(_SOURCE_CLOSURE_KEYS) == 20
    assert len(_BOOTSTRAP_KEYS) == 33
    assert len(_REFERENCE_OBSERVATION_KEYS) == 21
    assert len(_EVENT_KEYS) == 23
    assert len(_OPERATIONAL_OBSERVATION_KEYS) == 41
    assert len(_READINESS_KEYS) == 24
    assert len(_FAILURE_KEYS) == 29
    assert len(_EXTERNAL_IDENTITY_KEYS) == 10
    assert len(_P0_KEYS) == 6
    assert len(_P0_PARENT_KEYS) == 4
    assert len(_P0_RECEIPT_KEYS) == 5
    assert len(_RUNTIME_IDENTITY_KEYS) == 4
    assert len(_DISTRIBUTION_KEYS) == 4
    assert len(_DEPENDENCY_LOCK_KEYS) == 3
    assert len(_RUNTIME_MATERIALIZATION_KEYS) == 10
    assert len(_ENVIRONMENT_POLICY_KEYS) == 5
    assert len(_ENVIRONMENT_FIXED_KEYS) == 2
    assert len(_OWNER_ROW_KEYS) == 4
    assert len(_TEST_ROW_KEYS) == 3
    assert len(_IMPORT_ROW_KEYS) == 4
    assert len(_PROJECTION_KEYS) == 14
    assert len(_PARENT_PHASE_ORDER) == 7
    assert len(_FAILURE_CLASSES) == len(set(_FAILURE_CLASSES)) == 5
    assert len(_KNOWN_SCHEMA_PAIRS) == len(set(_KNOWN_SCHEMA_PAIRS)) == 2
    assert _PREFLIGHT_CHALLENGE_ID not in _HISTORICAL_CHALLENGE_IDS
    assert _PREFLIGHT_ID not in _HISTORICAL_CHALLENGE_IDS
    for value in (
        _P0_EXTERNAL_IDENTITY_SHA256,
        _PREFLIGHT_CHALLENGE_ID,
        _PREFLIGHT_ID,
        *_HISTORICAL_CHALLENGE_IDS,
    ):
        assert re.fullmatch(r"[0-9a-f]{64}", value)
    p0 = _p0_external_identity()
    assert set(p0) == _P0_KEYS
    assert set(p0["parent_design"]) == _P0_PARENT_KEYS
    assert set(p0["receipt"]) == _P0_RECEIPT_KEYS
    assert p0["p0_external_identity_sha256"] == (
        _P0_EXTERNAL_IDENTITY_SHA256
    )
    baseline = _baseline_state()
    assert set(baseline["source_closure"]) == _SOURCE_CLOSURE_KEYS
    assert set(baseline["bootstrap_closure"]) == _BOOTSTRAP_KEYS
    assert (
        set(baseline["reference_runtime_observation"])
        == _REFERENCE_OBSERVATION_KEYS
    )
    assert set(baseline["event1_at_publication"]) == _EVENT_KEYS
    assert (
        set(baseline["operational_runtime_observation"])
        == _OPERATIONAL_OBSERVATION_KEYS
    )
    assert set(baseline["readiness_candidate"]) == _READINESS_KEYS
    assert (
        baseline["event1_at_publication"]
        == baseline["event1_at_postfetch"]
    )
    assert (
        baseline["event1_publication_raw_sha256"]
        == baseline["event1_postfetch_raw_sha256"]
    )
    assert (
        baseline["expected_operational_projection"]
        == baseline["owner_operational_projection"]
        == baseline["independent_operational_projection"]
    )
    exact134 = _formal_exact134_node_ids()
    assert tuple(
        len(RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step])
        for step in range(11)
    ) == _FORMAL_EXACT134_STEP_COUNTS
    assert len(exact134) == len(set(exact134)) == 134
    assert _sha256_value(list(exact134)) == (
        _FORMAL_EXACT134_NODE_IDS_SHA256
    )
    assert baseline["bootstrap_closure"]["formal_test_node_ids"] == list(
        exact134
    )
    assert baseline["bootstrap_closure"]["formal_worker_argv"][-134:] == list(
        exact134
    )
    formal_manifest = baseline["bootstrap_closure"][
        "formal_test_manifest"
    ]
    assert len(formal_manifest) == 21
    assert [row["path"] for row in formal_manifest] == sorted(
        {node_id.split("::", 1)[0] for node_id in exact134}
    )
    assert all(row["path"] != _THIS_PATH for row in formal_manifest)
    reference_root = baseline["reference_runtime_observation"][
        "runtime_materialization"
    ]["runtime_root_identity_sha256"]
    operational_root = baseline["operational_runtime_observation"][
        "runtime_root_identity_sha256"
    ]
    assert baseline["operational_runtime_observation"][
        "reference_runtime_root_identity_sha256"
    ] == reference_root
    assert reference_root != operational_root
    ids = [row[0] for row in _CASES]
    assert ids == [
        *(f"S{number:02d}" for number in range(1, 5)),
        *(f"R{number:02d}" for number in range(1, 7)),
        *(f"E{number:02d}" for number in range(1, 5)),
        *(f"I{number:02d}" for number in range(1, 4)),
        *(f"F{number:02d}" for number in range(1, 6)),
        *(f"P{number:02d}" for number in range(1, 5)),
        *(f"A{number:02d}" for number in range(1, 5)),
    ]
    assert len(ids) == len(set(ids)) == 30
    expected_names = tuple(
        node.rsplit("::", 1)[1] for node in _oracle_node_ids()
    )
    actual_names = tuple(
        name
        for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    )
    assert actual_names == expected_names
    assert len(_oracle_node_ids()) == len(set(_oracle_node_ids())) == 30
    for name in expected_names:
        assert not inspect.signature(globals()[name]).parameters


@lru_cache(maxsize=None)
def _load_role_module(role: str) -> Any:
    relative = _ROLE_PATHS[role]
    absolute = _REPO_ROOT / relative
    module_name = f"_recovery_epoch003_d1_{role}_target"
    spec = importlib.util.spec_from_file_location(module_name, absolute)
    if spec is None or spec.loader is None:
        raise AssertionError(relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _target_api_or_red(
    role: str,
    case_id: str,
) -> Callable[[Mapping[str, Any]], Any]:
    red = (
        f"{case_id}_RECOVERY_EPOCH003_BOOTSTRAP_SOURCE_RUNTIME_"
        "CONTRACT_NOT_IMPLEMENTED"
    )
    try:
        module = _load_role_module(role)
    except Exception:
        pytest.fail(red, pytrace=False)
    for export_name, expected in _REQUIRED_EXPORTS[role].items():
        if not hasattr(module, export_name):
            pytest.fail(red, pytrace=False)
        if getattr(module, export_name) != expected:
            pytest.fail(red, pytrace=False)
    api_name = _TARGET_APIS[role][1]
    api = getattr(module, api_name, None)
    if not callable(api):
        pytest.fail(red, pytrace=False)
    return api


def _forbidden_independent_imports() -> tuple[str, ...]:
    source = (_REPO_ROOT / _ROLE_PATHS["independent"]).read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    forbidden = {
        Path(path).stem
        for role, path in _ROLE_PATHS.items()
        if role not in {"independent"}
    }
    violations: set[str] = set()
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        for module in modules:
            if module.rsplit(".", 1)[-1] in forbidden:
                violations.add(module.rsplit(".", 1)[-1])
    return tuple(sorted(violations))


def _assert_case(case_id: str) -> None:
    _assert_static_contract()
    _case_id, _boundary, role = _CASE_BY_ID[case_id]
    api = _target_api_or_red(role, case_id)
    baseline = _baseline_state()

    if case_id == "S01":
        state = {
            "source_closure": {
                "schema_version": _EPOCH002_SOURCE_SCHEMA,
            },
            "bootstrap_closure": {
                "schema_version": _EPOCH002_BOOTSTRAP_SCHEMA,
            },
        }
        assert _issue_codes(api(state)) == ()
    elif case_id == "S02":
        assert _issue_codes(api(deepcopy(baseline))) == ()
    elif case_id == "S03":
        state = deepcopy(baseline)
        state["source_closure"]["schema_version"] = _EPOCH002_SOURCE_SCHEMA
        assert _issue_codes(api(state)) == (
            "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
        )
    elif case_id == "S04":
        state = deepcopy(baseline)
        state["source_closure"]["schema_version"] = (
            "cocolon.emlis.nls_v3.recovery_epoch999.source.v1"
        )
        state["bootstrap_closure"]["schema_version"] = (
            "cocolon.emlis.nls_v3.recovery_epoch999.bootstrap.v1"
        )
        assert _issue_codes(api(state)) == (
            "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
        )
    elif case_id == "R01":
        state = deepcopy(baseline)
        state["bootstrap_closure"][
            "reference_runtime_observation_external_identity"
        ]["identity_sha256"] = _sha256_text(
            "fixture:wrong-reference-external-identity"
        )
        assert _issue_codes(api(state)) == (
            "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
        )
    elif case_id == "R02":
        state = deepcopy(baseline)
        state["operational_runtime_observation"][
            "runtime_root_identity_sha256"
        ] = state["reference_runtime_observation"][
            "runtime_materialization"
        ]["runtime_root_identity_sha256"]
        _refresh_operational_state(state)
        _assert_failure_receipt(
            api(state),
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
        )
    elif case_id == "R03":
        state = _failure_input(
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
        )
        state["operational_runtime_observation"][
            "pytest_distribution_identity"
        ]["distribution_version"] = "0.fixture-mismatch"
        _refresh_operational_state(state)
        _assert_failure_receipt(
            api(state),
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
        )
    elif case_id == "R04":
        state = deepcopy(baseline)
        state["operational_runtime_observation"][
            "installed_distributions_sha256"
        ] = _sha256_text("fixture:mismatched-installed-record-closure")
        _refresh_operational_state(state)
        _assert_failure_receipt(
            api(state),
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
        )
    elif case_id == "R05":
        state = deepcopy(baseline)
        state["operational_runtime_observation"][
            "formal_worker_argv_sha256"
        ] = _sha256_text("fixture:mismatched-worker-argv")
        _refresh_operational_state(state)
        assert _issue_codes(api(state)) == (
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
        )
    elif case_id == "R06":
        _assert_failure_receipt(
            api(
                _failure_input(
                    "OPERATIONAL_MATERIALIZATION_BINDING_MISSING"
                )
            ),
            "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
        )
    elif case_id == "E01":
        state = deepcopy(baseline)
        state["event1_at_postfetch"][
            "runtime_root_identity_sha256"
        ] = _sha256_text("fixture:forbidden-event1-runtime-root")
        _refresh_event_state(state)
        assert _issue_codes(api(state)) == (
            "RECOVERY_EPOCH003_EVENT1_OPERATIONAL_FACT_FORBIDDEN",
        )
    elif case_id == "E02":
        state = deepcopy(baseline)
        state["bootstrap_closure"][
            "expected_python_runtime_identity"
        ]["executable_sha256"] = "0" * 64
        state["bootstrap_closure"][
            "expected_python_runtime_identity"
        ]["build_sha256"] = "0" * 64
        state["bootstrap_closure"][
            "environment_policy"
        ]["inherited_path_sha256"] = "0" * 64
        assert _issue_codes(api(state)) == (
            "RECOVERY_EPOCH003_RUNTIME_IDENTITY_PLACEHOLDER_FORBIDDEN",
        )
    elif case_id == "E03":
        state = deepcopy(baseline)
        state["event1_at_postfetch"]["timestamp_utc"] = (
            "2026-07-29T00:01:01Z"
        )
        _refresh_event_state(state)
        assert _issue_codes(api(state)) == (
            "RECOVERY_EPOCH003_EVENT1_IMMUTABILITY_VIOLATION",
        )
    elif case_id == "E04":
        state = deepcopy(baseline)
        state["event1_at_postfetch"]["challenge_id"] = (
            _HISTORICAL_CHALLENGE_IDS[0]
        )
        _refresh_event_state(state)
        assert _issue_codes(api(state)) == (
            "RECOVERY_EPOCH003_CHALLENGE_PROVENANCE_INHERITANCE_FORBIDDEN",
        )
    elif case_id == "I01":
        assert _issue_codes(api(deepcopy(baseline))) == ()
    elif case_id == "I02":
        assert _forbidden_independent_imports() == ()
        assert _issue_codes(api(deepcopy(baseline))) == ()
    elif case_id == "I03":
        state = _failure_input(
            "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
        )
        assert _issue_codes(api(state)) == (
            "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
        )
    elif case_id in {"F01", "F02", "F03", "F04", "F05"}:
        failure_class = {
            "F01": "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
            "F02": "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
            "F03": "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
            "F04": "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
            "F05": "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
        }[case_id]
        _assert_failure_receipt(
            api(_failure_input(failure_class)),
            failure_class,
        )
    elif case_id == "P01":
        receipt = api(deepcopy(baseline))
        _assert_readiness_receipt(receipt)
        assert receipt["schema_version"] != _FAILURE_SCHEMA
    elif case_id == "P02":
        for failure_class in _FAILURE_CLASSES:
            receipt = api(_failure_input(failure_class))
            _assert_failure_receipt(receipt, failure_class)
            assert receipt["reservation_count_delta"] == 0
            assert receipt["formal_exact134_invocation_count"] == 0
            assert receipt["automatic_progression"] is False
    elif case_id == "P03":
        state = {
            "event1_external_identity": deepcopy(
                baseline["event1_external_identity"]
            ),
            "readiness_receipt": None,
            "readiness_postverified": False,
            "reservation_count_delta": 0,
            "formal_exact134_invocation_count": 0,
            "automatic_progression": False,
        }
        assert _issue_codes(api(state)) == (_STOP_CODE,)
        state["formal_exact134_invocation_count"] = 1
        assert _issue_codes(api(state)) == (_STOP_CODE,)
    elif case_id == "P04":
        state = {
            "phase_order": list(_PARENT_PHASE_ORDER),
            "completed_phases": [],
            "next_phase": _PARENT_PHASE_ORDER[0],
            "reservation_count_delta": 0,
            "formal_exact134_invocation_count": 0,
            "automatic_progression": False,
        }
        assert _issue_codes(api(state)) == ()
        state["automatic_progression"] = True
        assert _issue_codes(api(state)) == (
            "RECOVERY_EPOCH003_AUTOMATIC_PROGRESSION_FORBIDDEN",
        )
    elif case_id == "A01":
        for artifact_role, path in _PUBLICATION_ROLE_PATHS.items():
            state = {
                "artifact_role": artifact_role,
                "path": path,
                "changed_paths": [path],
                "body_free": True,
                "automatic_progression": False,
            }
            assert _issue_codes(api(state)) == ()
    elif case_id == "A02":
        assert "source_closure" in baseline["event1_at_publication"]
        assert "bootstrap_closure" in baseline["event1_at_publication"]
        assert not any(
            "SourceClosure" in path or "BootstrapClosure" in path
            for path in _STANDALONE_PATHS
        )
        assert _issue_codes(api(deepcopy(baseline))) == ()
    elif case_id == "A03":
        state = {
            "artifact_role": (
                "RECOVERY_EPOCH003_BOOTSTRAP_READINESS"
            ),
            "path": _READINESS_PATH,
            "changed_paths": [
                _READINESS_PATH,
                "forbidden/extra-artifact.json",
            ],
            "body_free": True,
            "automatic_progression": False,
        }
        assert _issue_codes(api(state)) == (
            "RECOVERY_EPOCH003_PUBLICATION_SCOPE_INVALID",
        )
    elif case_id == "A04":
        assert tuple(sorted(_ROLE_PATHS.values())) == tuple(
            sorted(
                {
                    "ai/services/ai_inference/"
                    "emlis_ai_recovery_epoch002_"
                    "canonical_current_closure_v3.py",
                    "ai/services/ai_inference/"
                    "emlis_ai_recovery_epoch002_sequence_ledger_v3.py",
                    "ai/tools/"
                    "emlis_nls_v3_recovery_epoch002_"
                    "atomic_publication_bundle_v3.py",
                    "ai/tools/"
                    "emlis_nls_v3_recovery_epoch002_"
                    "closure_receipt_verify.py",
                    "ai/tools/"
                    "emlis_nls_v3_recovery_epoch002_"
                    "current_step_proof_run.py",
                    "ai/tools/"
                    "emlis_nls_v3_recovery_epoch002_"
                    "formal_parent_orchestrator_v3.py",
                    "ai/tools/"
                    "emlis_nls_v3_recovery_epoch002_"
                    "formal_worker_bootstrap_preflight.py",
                }
            )
        )
        assert _issue_codes(api(deepcopy(baseline))) == ()
    else:
        raise AssertionError(case_id)


def test_s01_known_epoch002_schema_pair_preserved() -> None:
    _assert_case("S01")


def test_s02_epoch003_schema_pair_supported() -> None:
    _assert_case("S02")


def test_s03_mixed_schema_pair_rejected() -> None:
    _assert_case("S03")


def test_s04_unknown_schema_pair_rejected() -> None:
    _assert_case("S04")


def test_r01_reference_external_identity_bound() -> None:
    _assert_case("R01")


def test_r02_reference_operational_roots_distinct() -> None:
    _assert_case("R02")


def test_r03_runtime_and_pytest_parity() -> None:
    _assert_case("R03")


def test_r04_lock_record_and_distribution_parity() -> None:
    _assert_case("R04")


def test_r05_source_owner_plugin_argv_environment_parity() -> None:
    _assert_case("R05")


def test_r06_operational_materialization_binding_required() -> None:
    _assert_case("R06")


def test_e01_event1_excludes_operational_facts() -> None:
    _assert_case("E01")


def test_e02_placeholder_runtime_identity_rejected() -> None:
    _assert_case("E02")


def test_e03_event1_postfetch_bytes_immutable() -> None:
    _assert_case("E03")


def test_e04_epoch002_challenge_not_inherited() -> None:
    _assert_case("E04")


def test_i01_owner_independent_projection_equal() -> None:
    _assert_case("I01")


def test_i02_independent_owner_import_separation() -> None:
    _assert_case("I02")


def test_i03_projection_disagreement_fails_closed() -> None:
    _assert_case("I03")


def test_f01_schema_unsupported_failure_receipt() -> None:
    _assert_case("F01")


def test_f02_baseline_mismatch_failure_receipt() -> None:
    _assert_case("F02")


def test_f03_materialization_missing_failure_receipt() -> None:
    _assert_case("F03")


def test_f04_runtime_mismatch_failure_receipt() -> None:
    _assert_case("F04")


def test_f05_independent_disagreement_failure_receipt() -> None:
    _assert_case("F05")


def test_p01_readiness_or_failure_exact_one() -> None:
    _assert_case("P01")


def test_p02_every_failure_zero_effects() -> None:
    _assert_case("P02")


def test_p03_execution_gate_requires_postverified_readiness() -> None:
    _assert_case("P03")


def test_p04_parent_phase_order_and_no_autoprogression() -> None:
    _assert_case("P04")


def test_a01_artifact_paths_and_roles() -> None:
    _assert_case("A01")


def test_a02_nested_source_bootstrap_only_in_event1() -> None:
    _assert_case("A02")


def test_a03_publication_candidate_scope() -> None:
    _assert_case("A03")


def test_a04_all_required_owner_paths_bound() -> None:
    _assert_case("A04")
