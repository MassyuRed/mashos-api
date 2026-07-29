# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for the Recovery Epoch003 OperationalAdmission Addendum.

This exact44 oracle freezes the additive contract introduced by the
post-P0 parent Addendum.  It targets the new exact7 public API surface and
the existing Event1/publication surfaces that must be corrected by the
later D2.  Missing APIs fail inside every node, never during collection.

All bodies are deterministic, body-free unit fixtures.  This file does not
materialize a runtime, publish an artifact, allocate a candidate, create
Event1/readiness/reservation/attempt state, invoke formal exact134, or
advance Cycle001.
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
import tempfile
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
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_POST_P0_PARENT_ADDENDUM_"
    "D1_OPERATIONAL_ADMISSION_SOURCE_BOOTSTRAP_CARRIER_REFERENCE_"
    "MATERIALIZER_EVENT1_BINDING_AND_PHASE_EVIDENCE_CONTRACT_CAUSAL_RED_"
    "FREEZE_ONLY"
)
_D2_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_POST_P0_PARENT_ADDENDUM_"
    "D2_OPERATIONAL_ADMISSION_SOURCE_BOOTSTRAP_CARRIER_REFERENCE_"
    "MATERIALIZER_EVENT1_BINDING_AND_PHASE_EVIDENCE_CONTRACT_"
    "IMPLEMENTATION_AND_TARGETED_GREEN_ONLY"
)
_FINAL_ISSUANCE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_FINAL_PRE_EVENT1_REFERENCE_"
    "RUNTIME_OBSERVATION_AND_SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_"
    "CARRIER_ISSUANCE_INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_EVENT1_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_DISTINCT_CANDIDATE_"
    "ALLOCATION_AND_SEQUENCE_EVENT1_SOURCE_BASELINE_LOCK_PUBLICATION_"
    "INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_LOGICAL_CYCLE_ID = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH_ID = "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_operational_admission_contract_"
    "red.py"
)
_IMMUTABLE_D1_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_bootstrap_source_runtime_"
    "expected_observed_contract_red.py"
)
_IMMUTABLE_D1_RAW_SHA256 = (
    "8c8fcaf5211064ca59127a8081dc41ae8b9207472f070746c84a8e4b591a07e5"
)
_MISSING_CONTRACT_SUFFIX = (
    "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_NOT_IMPLEMENTED"
)

_OPERATIONAL_ADMISSION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
)
_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "OperationalAdmission_BodyFree_Receipt.json"
)
_REFERENCE_PATH = (
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

_OPERATIONAL_ADMISSION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id predecessor_bindings
    source_closure bootstrap_closure authority scope freshness
    effect_boundary owner_validation_state independent_verification_state
    state automatic_progression body_free operational_admission_sha256
    """
)
_PREDECESSOR_KEYS = _keys(
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
_AUTHORITY_KEYS = _keys(
    """
    approval_kind admission_authority_token publication_authority_token
    authority_sha256
    """
)
_SCOPE_KEYS = _keys(
    """
    artifact_repository_full_name source_repository_full_name source_ref
    source_commit_sha1 source_tree_sha1 source_closure_sha256
    bootstrap_closure_sha256
    reference_runtime_observation_external_identity_sha256
    next_authority_token operation_set separate_explicit_authority_required
    scope_sha256
    """
)
_FRESHNESS_KEYS = _keys(
    """
    issued_at_utc expires_at_utc validity_mode bound_source_commit_sha1
    bound_source_tree_sha1
    bound_reference_runtime_observation_external_identity_sha256
    event1_path_state_at_issuance maximum_event1_consumption_count
    invalidation_conditions reuse_allowed freshness_sha256
    """
)
_EFFECT_KEYS = _keys(
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
_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role body_free git_blob_sha1 identity_sha256
    logical_artifact_sha256 path publication_commit_sha1 raw_sha256
    repository_full_name schema_version
    """
)
_REFERENCE_PUBLICATION_STATE_KEYS = _keys(
    """
    artifact_repository_root external_identity postfetch_body
    admission_base_commit_sha1 admission_base_tree_sha1
    reference_publication_is_ancestor_of_admission_base
    reference_path_blob_at_admission_base_sha1
    """
)
_SOURCE_OBSERVATION_KEYS = _keys(
    """
    source_repository_root source_commit_sha1 source_tree_sha1
    worktree_clean
    """
)
_MATERIALIZATION_REQUEST_KEYS = _keys(
    """
    authority_token artifact_repository_root source_repository_root
    expected_source_commit_sha1 expected_source_tree_sha1
    dependency_lock_path wheelhouse_path destination_root environment
    """
)
_MATERIALIZATION_RESULT_KEYS = _keys(
    """
    runtime_root wheel_snapshot_root runtime_materialization
    effective_environment_policy
    """
)
_ROOT_IDENTITY_PREIMAGE_KEYS = _keys(
    """
    schema_version materialization_kind root_nonce_sha256
    source_commit_sha1 source_tree_sha1 dependency_lock_raw_sha256
    wheel_bundle_manifest_sha256 installed_distributions_sha256
    python_runtime_identity_sha256 pytest_distribution_identity_sha256
    environment_policy_sha256
    """
)
_PHASE_STATE_KEYS = _keys(
    """
    artifact_repository_root source_repository_root phase_order
    completed_phases phase_evidence next_phase reservation_count_delta
    formal_exact134_invocation_count automatic_progression
    """
)
_PHASE_EVIDENCE_KEYS = _keys(
    """
    phase artifact_records runtime_records owner_validation_state
    independent_verification_state phase_evidence_sha256
    """
)
_ARTIFACT_RECORD_KEYS = _keys(
    """
    external_identity published_body postfetch_body
    publication_base_commit_sha1 changed_paths
    """
)
_RUNTIME_RECORD_KEYS = _keys(
    "evidence_role evidence_body logical_sha256 body_free"
)

_OPERATION_SET = (
    "OPERATIONAL_ADMISSION_PUBLICATION",
    "DISTINCT_CANDIDATE_ALLOCATION",
    "SOURCE_BASELINE_EVENT1_PUBLICATION",
    "OPERATIONAL_RUNTIME_MATERIALIZATION",
    "OPERATIONAL_RUNTIME_OBSERVATION_PUBLICATION",
    "BOOTSTRAP_READINESS_OR_FAILURE_PUBLICATION",
    "FORMAL_ATTEMPT_ONE_SHOT_RESERVATION_PUBLICATION",
)
_INVALIDATION_CONDITIONS = (
    "ADMISSION_IDENTITY_ALREADY_BOUND_BY_EVENT1",
    "REFERENCE_OR_PREDECESSOR_IDENTITY_NOT_REACHABLE_OR_BYTE_DRIFTED",
    "SOURCE_COMMIT_OR_TREE_DRIFTED_OR_WORKTREE_NOT_CLEAN",
    "SOURCE_OR_BOOTSTRAP_CLOSURE_MISMATCH",
)
_PHASE_ORDER = (
    "REFERENCE_RUNTIME_OBSERVATION_PUBLISHED_AND_POSTVERIFIED",
    "SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_CARRIER_"
    "PUBLISHED_AND_POSTVERIFIED",
    "CANDIDATE_ALLOCATED_WITH_EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT",
    "READINESS_OR_FAILURE_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
)

_PUBLICATION_ROLE_PATHS = {
    "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION": _REFERENCE_PATH,
    "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION": _OPERATIONAL_ADMISSION_PATH,
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
    "parent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
    "preflight": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
}
_API_SPECS = {
    "materialize": (
        "preflight",
        "materialize_recovery_epoch003_reference_runtime",
        9,
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_MATERIALIZATION_INVALID",
    ),
    "build_reference": (
        "preflight",
        "build_recovery_epoch003_reference_runtime_observation",
        2,
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION_INVALID",
    ),
    "verify_reference": (
        "independent",
        "verify_recovery_epoch003_reference_runtime_observation",
        6,
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION_VERIFICATION_INVALID",
    ),
    "build_source": (
        "closure",
        "build_recovery_epoch003_source_bootstrap_closure",
        5,
        "RECOVERY_EPOCH003_SOURCE_BOOTSTRAP_BUILD_INVALID",
    ),
    "build_admission": (
        "sequence",
        "build_recovery_epoch003_operational_admission",
        8,
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_BUILD_INVALID",
    ),
    "verify_admission": (
        "independent",
        "verify_recovery_epoch003_operational_admission_contract",
        7,
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_VERIFICATION_INVALID",
    ),
    "phase": (
        "parent",
        "validate_recovery_epoch003_parent_phase_evidence_state",
        9,
        "RECOVERY_EPOCH003_PARENT_PHASE_EVIDENCE_INVALID",
    ),
}
_EXISTING_TARGETS = {
    "publication": (
        "publication",
        "validate_recovery_epoch003_publication_contract_state",
    ),
    "event": (
        "sequence",
        "validate_recovery_epoch003_sequence_event1_contract_state",
    ),
}

_LOCK_PATH = (
    "ai/configs/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
)
_LOCK_BLOB_SHA1 = "0822fcb010985cd0d384f250a9e8a1fe16dc8fd4"
_LOCK_RAW_SHA256 = (
    "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
)
_LOCK_LOGICAL_SHA256 = (
    "801ba54efc0f6655238d14e7c153fb70b555801489aa8ba028515fc64d9c05f4"
)
_WHEEL_BUNDLE_SHA256 = (
    "63f3915ccf57845dc0c4b5d14762207d23d1cb7a435a9de8411add8491ba6fc8"
)
_INSTALLED_DISTRIBUTIONS_SHA256 = (
    "0e2e4b5ec3f3b1aef7fad4474af28d8eeea8fa7bec1a57a9cb7180fc81b80e42"
)

_ADDENDUM_EXTERNAL_IDENTITY = {
    "artifact_role": (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PARENT_ADDENDUM_"
        "DESIGN_FROZEN_RECEIPT"
    ),
    "body_free": True,
    "git_blob_sha1": "15f35643c01be32ae4e56e9312c1e67b32075623",
    "logical_artifact_sha256": (
        "de707a6947537c6c2335586f7a5990850dbbbcd62c89e7fe6e3427d42635f404"
    ),
    "path": (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
        "FinalSourceBootstrapReferenceRuntimeClosureAndOperationalAdmission"
        "ContractUnreachable_P0ParentAddendum_Design_ReadOnly_"
        "BodyFree_Receipt_20260729.json"
    ),
    "publication_commit_sha1": "1ed317111f64075d08e4a91d467dff7b9ebc3841",
    "raw_sha256": (
        "fe4804fedae2f67e0fdd12199c0cc07439888103afc6e4b3738736b71d97eb69"
    ),
    "repository_full_name": "MassyuRed/Cocolon",
    "schema_version": (
        "cocolon.emlis.nls_v3.recovery_epoch003."
        "operational_admission_parent_addendum_design_frozen_receipt.v1"
    ),
    "identity_sha256": (
        "e8cc49a4983bb1c7e46948fb92ea605ce8fde7aa3a07926fbf047725e14bbf43"
    ),
}


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
        "git_blob_sha1": _sha1_text(f"fixture:blob:{role}:{path}"),
        "logical_artifact_sha256": logical_hash,
        "path": path,
        "publication_commit_sha1": _sha1_text(
            f"fixture:commit:{role}:{path}"
        ),
        "raw_sha256": _sha256_text(f"fixture:raw:{role}:{path}"),
        "repository_full_name": "MassyuRed/Cocolon",
        "schema_version": schema,
        "identity_sha256": "",
    }
    value["identity_sha256"] = _hash_without(value, "identity_sha256")
    return value


@lru_cache(maxsize=1)
def _legacy() -> Any:
    path = _REPO_ROOT / _IMMUTABLE_D1_PATH
    spec = importlib.util.spec_from_file_location(
        "_recovery_epoch003_immutable_d1_fixture",
        path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(_IMMUTABLE_D1_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _git_identity() -> tuple[str, str]:
    import subprocess

    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return commit, tree


def _reference_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    legacy = _legacy()
    commit, tree = _git_identity()
    reference = legacy._reference_observation()
    reference["authority_token"] = _FINAL_ISSUANCE_AUTHORITY
    reference["source_commit_sha1"] = commit
    reference["source_tree_sha1"] = tree
    reference["reference_runtime_observation_sha256"] = _hash_without(
        reference,
        "reference_runtime_observation_sha256",
    )
    identity = _external_identity(
        role="RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION",
        schema=legacy._REFERENCE_OBSERVATION_SCHEMA,
        path=_REFERENCE_PATH,
        logical_hash=reference["reference_runtime_observation_sha256"],
    )
    return reference, identity


def _remediation_receipt_identity(
    *,
    d2: bool,
) -> dict[str, Any]:
    stage = "D2" if d2 else "D1"
    role = (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_TARGETED_GREEN_"
        "RECEIPT"
        if d2
        else "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_CAUSAL_RED_"
        "RECEIPT"
    )
    schema = (
        "cocolon.emlis.nls_v3.recovery_epoch003."
        "operational_admission_contract_targeted_green_receipt.v1"
        if d2
        else "cocolon.emlis.nls_v3.recovery_epoch003."
        "operational_admission_contract_causal_red_receipt.v1"
    )
    suffix = (
        "ImplementationAndTargetedGREEN"
        if d2
        else "CausalRED_FreezeOnly"
    )
    path = (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
        f"PostP0ParentAddendum_{stage}_"
        "OperationalAdmissionSourceBootstrapCarrierReferenceMaterializer"
        f"Event1BindingAndPhaseEvidenceContract_{suffix}_"
        "BodyFree_Receipt_20260729.json"
    )
    return _external_identity(
        role=role,
        schema=schema,
        path=path,
        logical_hash=_sha256_text(f"fixture:{stage}:receipt"),
    )


def _admission_fixture() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    legacy = _legacy()
    reference, reference_identity = _reference_fixture()
    bootstrap = legacy._bootstrap_closure(reference, reference_identity)
    source = legacy._source_closure(reference_identity, bootstrap)

    corrected_d1 = {
        "artifact_role": (
            "RECOVERY_EPOCH003_D1_BOOTSTRAP_ORACLE_CORRECTION_CAUSAL_RED_"
            "REFREEZE_RECEIPT"
        ),
        "body_free": True,
        "git_blob_sha1": "1ad1d3610916f48a3d7adafac76fcb93c4d47538",
        "identity_sha256": (
            "d9164d82715abb519b549a7581737a37ebd3bf153b53284697cbe4573a8edb9e"
        ),
        "logical_artifact_sha256": (
            "cabe7aa0d50e94083edfd95b4641383aaa9ff11e44e60e7ea538e93252490370"
        ),
        "path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_D1_"
            "BootstrapFormalExact134ManifestAndReferenceRuntimeRootIdentity"
            "Binding_OracleCorrectionAndCausalREDRefreeze_"
            "BodyFree_Receipt_20260729.json"
        ),
        "publication_commit_sha1": (
            "31601a4f5ea3583ef1e9a839c55a8ace7677fd3e"
        ),
        "raw_sha256": (
            "0b6e491dedeb684b3f7d32b3a3acd231fbc724b994a75b1419c855428894a405"
        ),
        "repository_full_name": "MassyuRed/Cocolon",
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d1_bootstrap_oracle_correction_causal_red_refreeze_receipt.v1"
        ),
    }
    d2_green = {
        "artifact_role": (
            "RECOVERY_EPOCH003_D2_BOOTSTRAP_SOURCE_RUNTIME_TARGETED_GREEN_"
            "RECEIPT"
        ),
        "body_free": True,
        "git_blob_sha1": "fd2396953e1a3fe6d8e2172f1cdf30a197406b0a",
        "identity_sha256": (
            "cbd665b12b3af16b251a66073222d12823fb8776207922616718290e4bddc738"
        ),
        "logical_artifact_sha256": (
            "39ffbe4a791624c550eeb5d70d5326a26c88fee9e0a3880ae93e53066db570db"
        ),
        "path": (
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_D2_"
            "BootstrapSourceRuntimeExpectedObservedSeparationSchemaPair"
            "DispatchEvent1ImmutabilityAndIndependentOperationalProjection_"
            "ImplementationAndTargetedGREEN_BodyFree_Receipt_20260729.json"
        ),
        "publication_commit_sha1": (
            "1da49a13ee8a0a16d9c856861af55a3deb7468e4"
        ),
        "raw_sha256": (
            "a24184570ce97d46d4e13652c2417e77b41f730832861aa0cbddb9a9b3e5d6dd"
        ),
        "repository_full_name": "MassyuRed/Cocolon",
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d2_bootstrap_source_runtime_targeted_green_receipt.v1"
        ),
    }
    predecessor = {
        "p0_external_identity": legacy._p0_external_identity(),
        "operational_admission_parent_addendum_receipt_external_identity": (
            deepcopy(_ADDENDUM_EXTERNAL_IDENTITY)
        ),
        "bootstrap_contract_d1_receipt_external_identity": corrected_d1,
        "bootstrap_contract_d2_receipt_external_identity": d2_green,
        "operational_admission_contract_d1_receipt_external_identity": (
            _remediation_receipt_identity(d2=False)
        ),
        "operational_admission_contract_d2_receipt_external_identity": (
            _remediation_receipt_identity(d2=True)
        ),
        "reference_runtime_observation_external_identity": deepcopy(
            reference_identity
        ),
        "predecessor_bindings_sha256": "",
    }
    predecessor["predecessor_bindings_sha256"] = _hash_without(
        predecessor,
        "predecessor_bindings_sha256",
    )
    authority = {
        "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
        "admission_authority_token": _FINAL_ISSUANCE_AUTHORITY,
        "publication_authority_token": _FINAL_ISSUANCE_AUTHORITY,
        "authority_sha256": "",
    }
    authority["authority_sha256"] = _hash_without(
        authority,
        "authority_sha256",
    )
    scope = {
        "artifact_repository_full_name": "MassyuRed/Cocolon",
        "source_repository_full_name": "MassyuRed/mashos-api",
        "source_ref": "refs/heads/main",
        "source_commit_sha1": source["source_commit_sha1"],
        "source_tree_sha1": source["source_tree_sha1"],
        "source_closure_sha256": source["source_closure_sha256"],
        "bootstrap_closure_sha256": bootstrap["bootstrap_closure_sha256"],
        "reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "next_authority_token": _EVENT1_AUTHORITY,
        "operation_set": list(_OPERATION_SET),
        "separate_explicit_authority_required": True,
        "scope_sha256": "",
    }
    scope["scope_sha256"] = _hash_without(scope, "scope_sha256")
    freshness = {
        "issued_at_utc": "2026-07-29T04:00:00Z",
        "expires_at_utc": None,
        "validity_mode": "IDENTITY_STABLE_SINGLE_EVENT1_CONSUMPTION",
        "bound_source_commit_sha1": source["source_commit_sha1"],
        "bound_source_tree_sha1": source["source_tree_sha1"],
        "bound_reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "event1_path_state_at_issuance": "ABSENT",
        "maximum_event1_consumption_count": 1,
        "invalidation_conditions": list(_INVALIDATION_CONDITIONS),
        "reuse_allowed": False,
        "freshness_sha256": "",
    }
    freshness["freshness_sha256"] = _hash_without(
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
    effect["effect_boundary_sha256"] = _hash_without(
        effect,
        "effect_boundary_sha256",
    )
    admission = {
        "schema_version": _OPERATIONAL_ADMISSION_SCHEMA,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "predecessor_bindings": predecessor,
        "source_closure": source,
        "bootstrap_closure": bootstrap,
        "authority": authority,
        "scope": scope,
        "freshness": freshness,
        "effect_boundary": effect,
        "owner_validation_state": "PROVED",
        "independent_verification_state": "PROVED",
        "state": (
            "SOURCE_BOOTSTRAP_REFERENCE_RUNTIME_CLOSED_AWAITING_SEPARATE_"
            "CANDIDATE_EVENT1_AUTHORITY"
        ),
        "automatic_progression": False,
        "body_free": True,
        "operational_admission_sha256": "",
    }
    admission["operational_admission_sha256"] = _hash_without(
        admission,
        "operational_admission_sha256",
    )
    identity = _external_identity(
        role="RECOVERY_EPOCH003_OPERATIONAL_ADMISSION",
        schema=_OPERATIONAL_ADMISSION_SCHEMA,
        path=_OPERATIONAL_ADMISSION_PATH,
        logical_hash=admission["operational_admission_sha256"],
    )
    return admission, identity, reference


def _event_fixture() -> dict[str, Any]:
    legacy = _legacy()
    admission, admission_identity, reference = _admission_fixture()
    reference_identity = admission["predecessor_bindings"][
        "reference_runtime_observation_external_identity"
    ]
    event = legacy._event1(
        admission["source_closure"],
        admission["bootstrap_closure"],
        reference_identity,
    )
    supporting = sorted(
        [deepcopy(admission_identity), deepcopy(reference_identity)],
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        ),
    )
    event["source_closure"] = deepcopy(admission["source_closure"])
    event["bootstrap_closure"] = deepcopy(admission["bootstrap_closure"])
    event["authority"] = {
        "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
        "operational_admission": deepcopy(admission_identity),
        "publication_authority_token": _EVENT1_AUTHORITY,
        "transition_authority_token": _EVENT1_AUTHORITY,
    }
    event["primary_evidence_artifact"] = deepcopy(admission_identity)
    event["publication"]["supporting_artifacts"] = supporting
    event["publication"]["supporting_artifact_count"] = 2
    event["publication"]["supporting_artifact_set_sha256"] = (
        _sha256_value(supporting)
    )
    event["publication"]["expected_changed_path_count"] = 1
    event["event_sha256"] = _hash_without(event, "event_sha256")
    assert reference["authority_token"] == _FINAL_ISSUANCE_AUTHORITY
    return event


def _materialization_request() -> dict[str, Any]:
    commit, tree = _git_identity()
    return {
        "authority_token": _FINAL_ISSUANCE_AUTHORITY,
        "artifact_repository_root": str(_REPO_ROOT),
        "source_repository_root": str(_REPO_ROOT),
        "expected_source_commit_sha1": commit,
        "expected_source_tree_sha1": tree,
        "dependency_lock_path": str(_REPO_ROOT / _LOCK_PATH),
        "wheelhouse_path": str(_REPO_ROOT / ".missing-wheelhouse"),
        "destination_root": str(_REPO_ROOT / ".missing-runtime-root"),
        "environment": {
            "PATH": "/fixture/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        },
    }


def _materialization_result() -> dict[str, Any]:
    legacy = _legacy()
    reference, _identity = _reference_fixture()
    return {
        "runtime_root": str(_REPO_ROOT / ".missing-runtime-root"),
        "wheel_snapshot_root": str(_REPO_ROOT / ".missing-wheel-snapshot"),
        "runtime_materialization": deepcopy(
            reference["runtime_materialization"]
        ),
        "effective_environment_policy": deepcopy(
            reference["environment_policy"]
        ),
    }


def _reference_verify_state() -> dict[str, Any]:
    reference, identity = _reference_fixture()
    return {
        "verification_mode": "BODY_ONLY_BEFORE_PUBLICATION",
        "materialization_request": _materialization_request(),
        "materialization_result": _materialization_result(),
        "reference_runtime_observation": reference,
        "reference_runtime_observation_external_identity": None,
        "reference_publication_state": None,
    }


def _source_build_state() -> dict[str, Any]:
    reference, identity = _reference_fixture()
    return {
        "source_repository_root": str(_REPO_ROOT),
        "source_commit_sha1": reference["source_commit_sha1"],
        "source_tree_sha1": reference["source_tree_sha1"],
        "reference_runtime_observation": reference,
        "reference_runtime_observation_external_identity": identity,
    }


def _admission_verify_state() -> dict[str, Any]:
    admission, identity, reference = _admission_fixture()
    commit = admission["source_closure"]["source_commit_sha1"]
    tree = admission["source_closure"]["source_tree_sha1"]
    reference_identity = admission["predecessor_bindings"][
        "reference_runtime_observation_external_identity"
    ]
    return {
        "verification_mode": "BODY_ONLY_BEFORE_PUBLICATION",
        "artifact_repository_root": str(_REPO_ROOT),
        "source_repository_observation": {
            "source_repository_root": str(_REPO_ROOT),
            "source_commit_sha1": commit,
            "source_tree_sha1": tree,
            "worktree_clean": True,
        },
        "operational_admission": admission,
        "operational_admission_external_identity": None,
        "reference_runtime_observation": reference,
        "reference_publication_state": {
            "artifact_repository_root": str(_REPO_ROOT),
            "external_identity": reference_identity,
            "postfetch_body": reference,
            "admission_base_commit_sha1": _sha1_text(
                "fixture:admission-base"
            ),
            "admission_base_tree_sha1": _sha1_text(
                "fixture:admission-base-tree"
            ),
            "reference_publication_is_ancestor_of_admission_base": True,
            "reference_path_blob_at_admission_base_sha1": (
                reference_identity["git_blob_sha1"]
            ),
        },
    }


def _phase_start_state() -> dict[str, Any]:
    return {
        "artifact_repository_root": str(_REPO_ROOT),
        "source_repository_root": str(_REPO_ROOT),
        "phase_order": list(_PHASE_ORDER),
        "completed_phases": [],
        "phase_evidence": [],
        "next_phase": _PHASE_ORDER[0],
        "reservation_count_delta": 0,
        "formal_exact134_invocation_count": 0,
        "automatic_progression": False,
    }


@lru_cache(maxsize=None)
def _load_role_module(role: str) -> Any:
    relative = _ROLE_PATHS[role]
    absolute = _REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(
        f"_recovery_epoch003_addendum_d1_{role}",
        absolute,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _required_api_surface_or_red(case_id: str) -> None:
    red = f"{case_id}_{_MISSING_CONTRACT_SUFFIX}"
    for role, api_name, _count, _failure in _API_SPECS.values():
        try:
            module = _load_role_module(role)
        except Exception:
            pytest.fail(red, pytrace=False)
        api = getattr(module, api_name, None)
        if not callable(api):
            pytest.fail(red, pytrace=False)
        parameters = list(inspect.signature(api).parameters.values())
        if (
            len(parameters) != 1
            or parameters[0].name != "state"
            or parameters[0].kind
            not in {
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            }
        ):
            pytest.fail(red, pytrace=False)


def _api(name: str, case_id: str) -> Callable[[Mapping[str, Any]], Any]:
    _required_api_surface_or_red(case_id)
    role, api_name, _count, _failure = _API_SPECS[name]
    return getattr(_load_role_module(role), api_name)


def _existing_api(
    name: str,
    case_id: str,
) -> Callable[[Mapping[str, Any]], Any]:
    _required_api_surface_or_red(case_id)
    role, api_name = _EXISTING_TARGETS[name]
    api = getattr(_load_role_module(role), api_name, None)
    if not callable(api):
        pytest.fail(
            f"{case_id}_{_MISSING_CONTRACT_SUFFIX}",
            pytrace=False,
        )
    return api


def _failure(name: str) -> tuple[str, ...]:
    return (_API_SPECS[name][3],)


def _issues(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(str(item) for item in value)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    if isinstance(value, Mapping):
        raw = value.get("issue_codes")
        if isinstance(raw, (list, tuple)):
            return tuple(str(item) for item in raw)
    raise AssertionError(f"unsupported issue result: {type(value)!r}")


def _forbidden_independent_imports() -> tuple[str, ...]:
    source = (_REPO_ROOT / _ROLE_PATHS["independent"]).read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    forbidden = {
        Path(_ROLE_PATHS[role]).stem
        for role in ("closure", "sequence", "preflight")
    }
    violations: set[str] = set()
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules = [node.module]
        for module in modules:
            tail = module.rsplit(".", 1)[-1]
            if tail in forbidden:
                violations.add(tail)
    return tuple(sorted(violations))


_CASES = (
    ("S01", "materializer_public_signature", "materialize"),
    ("S02", "reference_builder_public_signature", "build_reference"),
    ("S03", "reference_verifier_public_signature", "verify_reference"),
    ("S04", "source_builder_public_signature", "build_source"),
    ("S05", "admission_builder_public_signature", "build_admission"),
    ("S06", "admission_verifier_public_signature", "verify_admission"),
    ("S07", "phase_validator_public_signature", "phase"),
    ("M01", "materializer_strict_exact9_input", "materialize"),
    ("M02", "materializer_exact_final_authority", "materialize"),
    ("M03", "materializer_lock_and_exact46_wheels", "materialize"),
    ("M04", "materializer_nofollow_snapshot_and_disjoint_roots", "materialize"),
    ("M05", "materializer_isolated_pip_and_sanitized_environment", "materialize"),
    ("M06", "materializer_root_identity_and_zero_effects", "materialize"),
    ("R01", "reference_builder_strict_exact2_input", "build_reference"),
    ("R02", "reference_pipeline_final_authority_binding", "build_reference"),
    ("R03", "reference_verifier_two_exact_modes", "verify_reference"),
    ("R04", "reference_fixture_injection_rejected", "verify_reference"),
    ("R05", "reference_independent_owner_import_separation", "verify_reference"),
    ("C01", "source_builder_strict_exact5_input", "build_source"),
    ("C02", "source_builder_source_identity_mismatch_rejected", "build_source"),
    ("C03", "source_builder_reference_identity_mismatch_rejected", "build_source"),
    ("C04", "source_exact20_bootstrap_exact33_nested_carrier", "build_source"),
    ("O01", "admission_builder_strict_exact8_input", "build_admission"),
    ("O02", "admission_exact16_body_and_self_hash", "verify_admission"),
    ("O03", "admission_predecessor_exact8_full_identity", "verify_admission"),
    ("O04", "admission_authority_exact4_final_token", "verify_admission"),
    ("O05", "admission_scope_exact12_operation_set", "verify_admission"),
    ("O06", "admission_freshness_single_event1_consumption", "verify_admission"),
    ("O07", "admission_effect_boundary_exact15", "verify_admission"),
    ("O08", "admission_postfetch_ancestry_not_boolean", "verify_admission"),
    ("P01", "publication_operational_admission_role_path", "publication"),
    ("P02", "publication_exact7_roles_exact6_paths", "publication"),
    ("P03", "publication_each_candidate_exact1_path", "publication"),
    ("E01", "event1_admission_carrier_positive_shape", "event"),
    ("E02", "event1_source_bootstrap_deep_equality", "event"),
    ("E03", "event1_primary_evidence_actual_admission", "event"),
    ("E04", "event1_supporting_exact2_changed_path_exact1", "event"),
    ("E05", "event1_equal_authority_tokens_explicit_approval", "event"),
    ("E06", "candidate_not_standalone_phase_completion", "phase"),
    ("H01", "parent_phase_exact6_initial_state", "phase"),
    ("H02", "parent_phase_name_without_evidence_rejected", "phase"),
    ("H03", "parent_phase_artifact_record_requires_body_postfetch", "phase"),
    ("H04", "parent_phase4_runtime_exact2_membership", "phase"),
    ("H05", "parent_phase5_matches_phase4_candidates", "phase"),
)
_CASE_BY_ID = {row[0]: row for row in _CASES}
_ORDERED_NODE_IDS_SHA256 = (
    "ad249356b9b4def772b65af57a85bf7a4c748629c12dfaf1314444cbb9179e5e"
)


def _oracle_node_ids() -> tuple[str, ...]:
    return tuple(
        f"{_THIS_PATH}::test_{case_id.lower()}_{name}"
        for case_id, name, _target in _CASES
    )


def _assert_static_contract() -> None:
    assert _AUTHORITY.endswith("_CAUSAL_RED_FREEZE_ONLY")
    assert _D2_AUTHORITY.endswith("_IMPLEMENTATION_AND_TARGETED_GREEN_ONLY")
    assert len(_API_SPECS) == 7
    assert [row[2] for row in _API_SPECS.values()] == [
        9,
        2,
        6,
        5,
        8,
        7,
        9,
    ]
    assert len({row[3] for row in _API_SPECS.values()}) == 7
    assert len(_OPERATIONAL_ADMISSION_KEYS) == 16
    assert len(_PREDECESSOR_KEYS) == 8
    assert len(_AUTHORITY_KEYS) == 4
    assert len(_SCOPE_KEYS) == 12
    assert len(_FRESHNESS_KEYS) == 11
    assert len(_EFFECT_KEYS) == 15
    assert len(_EXTERNAL_IDENTITY_KEYS) == 10
    assert len(_REFERENCE_PUBLICATION_STATE_KEYS) == 7
    assert len(_SOURCE_OBSERVATION_KEYS) == 4
    assert len(_MATERIALIZATION_REQUEST_KEYS) == 9
    assert len(_MATERIALIZATION_RESULT_KEYS) == 4
    assert len(_ROOT_IDENTITY_PREIMAGE_KEYS) == 11
    assert len(_PHASE_STATE_KEYS) == 9
    assert len(_PHASE_EVIDENCE_KEYS) == 6
    assert len(_ARTIFACT_RECORD_KEYS) == 5
    assert len(_RUNTIME_RECORD_KEYS) == 4
    assert len(_OPERATION_SET) == len(set(_OPERATION_SET)) == 7
    assert tuple(sorted(_INVALIDATION_CONDITIONS)) == (
        _INVALIDATION_CONDITIONS
    )
    assert len(_PHASE_ORDER) == len(set(_PHASE_ORDER)) == 6
    assert len(_PUBLICATION_ROLE_PATHS) == 7
    assert len(set(_PUBLICATION_ROLE_PATHS.values())) == 6
    assert _OPERATIONAL_ADMISSION_PATH in set(
        _PUBLICATION_ROLE_PATHS.values()
    )
    assert not any(
        "SourceClosure" in path or "BootstrapClosure" in path
        for path in _PUBLICATION_ROLE_PATHS.values()
    )
    lock_bytes = (_REPO_ROOT / _LOCK_PATH).read_bytes()
    assert hashlib.sha1(
        b"blob " + str(len(lock_bytes)).encode("ascii") + b"\0" + lock_bytes
    ).hexdigest() == _LOCK_BLOB_SHA1
    assert hashlib.sha256(lock_bytes).hexdigest() == _LOCK_RAW_SHA256
    lock = json.loads(lock_bytes)
    assert lock["lock_sha256"] == _LOCK_LOGICAL_SHA256
    assert lock["distribution_count"] == len(lock["distributions"]) == 46
    assert len(lock["pip_require_hashes_lines"]) == 46
    assert lock["resolution"]["pip_version"] == "26.0.1"
    assert lock["resolution"]["index_access_during_install"] is False
    immutable_d1 = (_REPO_ROOT / _IMMUTABLE_D1_PATH).read_bytes()
    assert hashlib.sha256(immutable_d1).hexdigest() == (
        _IMMUTABLE_D1_RAW_SHA256
    )
    assert set(_ADDENDUM_EXTERNAL_IDENTITY) == _EXTERNAL_IDENTITY_KEYS
    assert _ADDENDUM_EXTERNAL_IDENTITY["identity_sha256"] == _hash_without(
        _ADDENDUM_EXTERNAL_IDENTITY,
        "identity_sha256",
    )
    admission, identity, reference = _admission_fixture()
    assert set(admission) == _OPERATIONAL_ADMISSION_KEYS
    assert set(admission["predecessor_bindings"]) == _PREDECESSOR_KEYS
    assert set(admission["source_closure"]) == _legacy()._SOURCE_CLOSURE_KEYS
    assert set(admission["bootstrap_closure"]) == _legacy()._BOOTSTRAP_KEYS
    assert set(admission["authority"]) == _AUTHORITY_KEYS
    assert set(admission["scope"]) == _SCOPE_KEYS
    assert set(admission["freshness"]) == _FRESHNESS_KEYS
    assert set(admission["effect_boundary"]) == _EFFECT_KEYS
    assert admission["operational_admission_sha256"] == _hash_without(
        admission,
        "operational_admission_sha256",
    )
    assert identity["logical_artifact_sha256"] == (
        admission["operational_admission_sha256"]
    )
    assert reference["authority_token"] == _FINAL_ISSUANCE_AUTHORITY
    ids = [row[0] for row in _CASES]
    assert ids == [
        *(f"S{number:02d}" for number in range(1, 8)),
        *(f"M{number:02d}" for number in range(1, 7)),
        *(f"R{number:02d}" for number in range(1, 6)),
        *(f"C{number:02d}" for number in range(1, 5)),
        *(f"O{number:02d}" for number in range(1, 9)),
        *(f"P{number:02d}" for number in range(1, 4)),
        *(f"E{number:02d}" for number in range(1, 7)),
        *(f"H{number:02d}" for number in range(1, 6)),
    ]
    assert len(ids) == len(set(ids)) == 44
    expected_names = tuple(
        node.rsplit("::", 1)[1] for node in _oracle_node_ids()
    )
    actual_names = tuple(
        name
        for name, value in globals().items()
        if name.startswith("test_") and callable(value)
    )
    assert actual_names == expected_names
    assert len(_oracle_node_ids()) == len(set(_oracle_node_ids())) == 44
    assert _sha256_value(list(_oracle_node_ids())) == (
        _ORDERED_NODE_IDS_SHA256
    )
    for name in expected_names:
        assert not inspect.signature(globals()[name]).parameters


def _assert_case(case_id: str) -> None:
    _assert_static_contract()
    _case, _name, target = _CASE_BY_ID[case_id]

    if case_id.startswith("S"):
        api = _api(target, case_id)
        assert _issues(api({})) == _failure(target)
        assert _issues(api(None)) == _failure(target)
        return

    if case_id == "M01":
        api = _api("materialize", case_id)
        state = _materialization_request()
        state["unexpected"] = True
        assert _issues(api(state)) == _failure("materialize")
    elif case_id == "M02":
        api = _api("materialize", case_id)
        state = _materialization_request()
        state["authority_token"] = _AUTHORITY
        assert _issues(api(state)) == _failure("materialize")
    elif case_id == "M03":
        api = _api("materialize", case_id)
        with tempfile.TemporaryDirectory() as root:
            wheelhouse = Path(root) / "wheelhouse"
            wheelhouse.mkdir()
            lock = json.loads((_REPO_ROOT / _LOCK_PATH).read_text("utf-8"))
            for row in lock["distributions"][:-1]:
                (wheelhouse / row["wheel_filename"]).touch()
            state = _materialization_request()
            state["wheelhouse_path"] = str(wheelhouse)
            state["destination_root"] = str(Path(root) / "runtime")
            assert _issues(api(state)) == _failure("materialize")
    elif case_id == "M04":
        api = _api("materialize", case_id)
        with tempfile.TemporaryDirectory() as root:
            wheelhouse = Path(root) / "wheelhouse"
            wheelhouse.mkdir()
            (wheelhouse / "forbidden-link.whl").symlink_to(
                Path(root) / "missing-target"
            )
            state = _materialization_request()
            state["wheelhouse_path"] = str(wheelhouse)
            state["destination_root"] = str(wheelhouse)
            assert _issues(api(state)) == _failure("materialize")
    elif case_id == "M05":
        api = _api("materialize", case_id)
        source = (_REPO_ROOT / _ROLE_PATHS["preflight"]).read_text("utf-8")
        for token in (
            "--isolated",
            "--no-index",
            "--no-cache-dir",
            "--require-hashes",
            "--only-binary=:all:",
            "--no-compile",
        ):
            assert token in source
        state = _materialization_request()
        state["environment"]["PIP_INDEX_URL"] = "https://forbidden.invalid/"
        assert _issues(api(state)) == _failure("materialize")
    elif case_id == "M06":
        api = _api("materialize", case_id)
        assert len(_ROOT_IDENTITY_PREIMAGE_KEYS) == 11
        assert len(_MATERIALIZATION_RESULT_KEYS) == 4
        assert _WHEEL_BUNDLE_SHA256 != _INSTALLED_DISTRIBUTIONS_SHA256
        state = _materialization_request()
        state["destination_root"] = state["source_repository_root"]
        assert _issues(api(state)) == _failure("materialize")
    elif case_id == "R01":
        api = _api("build_reference", case_id)
        assert _issues(api({"materialization_request": {}})) == _failure(
            "build_reference"
        )
    elif case_id == "R02":
        api = _api("build_reference", case_id)
        request = _materialization_request()
        request["authority_token"] = _EVENT1_AUTHORITY
        assert _issues(
            api(
                {
                    "materialization_request": request,
                    "materialization_result": _materialization_result(),
                }
            )
        ) == _failure("build_reference")
    elif case_id == "R03":
        api = _api("verify_reference", case_id)
        state = _reference_verify_state()
        state["verification_mode"] = "FIXTURE_ONLY"
        assert _issues(api(state)) == _failure("verify_reference")
    elif case_id == "R04":
        api = _api("verify_reference", case_id)
        state = _reference_verify_state()
        assert _issues(api(state)) == _failure("verify_reference")
    elif case_id == "R05":
        api = _api("verify_reference", case_id)
        assert _forbidden_independent_imports() == ()
        assert _issues(api({})) == _failure("verify_reference")
    elif case_id == "C01":
        api = _api("build_source", case_id)
        assert _issues(api({})) == _failure("build_source")
    elif case_id == "C02":
        api = _api("build_source", case_id)
        state = _source_build_state()
        state["source_commit_sha1"] = "0" * 40
        assert _issues(api(state)) == _failure("build_source")
    elif case_id == "C03":
        api = _api("build_source", case_id)
        state = _source_build_state()
        state["reference_runtime_observation_external_identity"][
            "identity_sha256"
        ] = "0" * 64
        assert _issues(api(state)) == _failure("build_source")
    elif case_id == "C04":
        api = _api("build_source", case_id)
        admission, _identity, _reference = _admission_fixture()
        assert len(admission["source_closure"]) == 20
        assert len(admission["bootstrap_closure"]) == 33
        assert not any(
            "SourceClosure" in path or "BootstrapClosure" in path
            for path in _PUBLICATION_ROLE_PATHS.values()
        )
        state = _source_build_state()
        state["reference_runtime_observation"]["source_tree_sha1"] = "0" * 40
        assert _issues(api(state)) == _failure("build_source")
    elif case_id == "O01":
        api = _api("build_admission", case_id)
        assert _issues(api({})) == _failure("build_admission")
    elif case_id == "O02":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        assert _issues(api(state)) == ()
    elif case_id == "O03":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        state["operational_admission"]["predecessor_bindings"][
            "operational_admission_parent_addendum_receipt_external_identity"
        ] = _ADDENDUM_EXTERNAL_IDENTITY["identity_sha256"]
        state["operational_admission"]["operational_admission_sha256"] = (
            _hash_without(
                state["operational_admission"],
                "operational_admission_sha256",
            )
        )
        assert _issues(api(state)) == _failure("verify_admission")
    elif case_id == "O04":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        authority = state["operational_admission"]["authority"]
        authority["publication_authority_token"] = _EVENT1_AUTHORITY
        authority["authority_sha256"] = _hash_without(
            authority,
            "authority_sha256",
        )
        state["operational_admission"]["operational_admission_sha256"] = (
            _hash_without(
                state["operational_admission"],
                "operational_admission_sha256",
            )
        )
        assert _issues(api(state)) == _failure("verify_admission")
    elif case_id == "O05":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        scope = state["operational_admission"]["scope"]
        scope["operation_set"].append("FORMAL_EXACT134_INVOCATION")
        scope["scope_sha256"] = _hash_without(scope, "scope_sha256")
        state["operational_admission"]["operational_admission_sha256"] = (
            _hash_without(
                state["operational_admission"],
                "operational_admission_sha256",
            )
        )
        assert _issues(api(state)) == _failure("verify_admission")
    elif case_id == "O06":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        freshness = state["operational_admission"]["freshness"]
        freshness["reuse_allowed"] = True
        freshness["freshness_sha256"] = _hash_without(
            freshness,
            "freshness_sha256",
        )
        state["operational_admission"]["operational_admission_sha256"] = (
            _hash_without(
                state["operational_admission"],
                "operational_admission_sha256",
            )
        )
        assert _issues(api(state)) == _failure("verify_admission")
    elif case_id == "O07":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        effect = state["operational_admission"]["effect_boundary"]
        effect["formal_test_collection_count"] = 1
        effect["effect_boundary_sha256"] = _hash_without(
            effect,
            "effect_boundary_sha256",
        )
        state["operational_admission"]["operational_admission_sha256"] = (
            _hash_without(
                state["operational_admission"],
                "operational_admission_sha256",
            )
        )
        assert _issues(api(state)) == _failure("verify_admission")
    elif case_id == "O08":
        api = _api("verify_admission", case_id)
        state = _admission_verify_state()
        state["verification_mode"] = "BODY_AND_POSTFETCH"
        state["operational_admission_external_identity"] = (
            _admission_fixture()[1]
        )
        state["reference_publication_state"][
            "reference_publication_is_ancestor_of_admission_base"
        ] = True
        assert _issues(api(state)) == _failure("verify_admission")
    elif case_id == "P01":
        api = _existing_api("publication", case_id)
        module = _load_role_module("publication")
        assert module.RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS == (
            _PUBLICATION_ROLE_PATHS
        )
        state = {
            "artifact_role": "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION",
            "path": _OPERATIONAL_ADMISSION_PATH,
            "changed_paths": [_OPERATIONAL_ADMISSION_PATH],
            "body_free": True,
            "automatic_progression": False,
        }
        assert _issues(api(state)) == ()
    elif case_id == "P02":
        api = _existing_api("publication", case_id)
        assert len(_PUBLICATION_ROLE_PATHS) == 7
        assert len(set(_PUBLICATION_ROLE_PATHS.values())) == 6
        for role, path in _PUBLICATION_ROLE_PATHS.items():
            state = {
                "artifact_role": role,
                "path": path,
                "changed_paths": [path],
                "body_free": True,
                "automatic_progression": False,
            }
            assert _issues(api(state)) == ()
    elif case_id == "P03":
        api = _existing_api("publication", case_id)
        state = {
            "artifact_role": "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION",
            "path": _OPERATIONAL_ADMISSION_PATH,
            "changed_paths": [
                _OPERATIONAL_ADMISSION_PATH,
                _REFERENCE_PATH,
            ],
            "body_free": True,
            "automatic_progression": False,
        }
        assert _issues(api(state)) == (
            "RECOVERY_EPOCH003_PUBLICATION_SCOPE_INVALID",
        )
    elif case_id == "E01":
        api = _existing_api("event", case_id)
        assert _issues(api(_event_fixture())) == ()
    elif case_id == "E02":
        api = _existing_api("event", case_id)
        event = _event_fixture()
        event["source_closure"]["source_tree_sha1"] = "0" * 40
        event["source_closure"]["source_closure_sha256"] = _hash_without(
            event["source_closure"],
            "source_closure_sha256",
        )
        event["event_sha256"] = _hash_without(event, "event_sha256")
        assert _issues(api(event))
    elif case_id == "E03":
        api = _existing_api("event", case_id)
        event = _event_fixture()
        event["primary_evidence_artifact"] = deepcopy(
            event["publication"]["supporting_artifacts"][1]
        )
        event["event_sha256"] = _hash_without(event, "event_sha256")
        assert _issues(api(event))
    elif case_id == "E04":
        api = _existing_api("event", case_id)
        event = _event_fixture()
        event["publication"]["expected_changed_path_count"] = 3
        event["event_sha256"] = _hash_without(event, "event_sha256")
        assert _issues(api(event))
    elif case_id == "E05":
        api = _existing_api("event", case_id)
        event = _event_fixture()
        event["authority"]["transition_authority_token"] = (
            "NLS_V3_FORBIDDEN_DIFFERENT_TRANSITION_TOKEN"
        )
        event["event_sha256"] = _hash_without(event, "event_sha256")
        assert _issues(api(event))
    elif case_id == "E06":
        api = _api("phase", case_id)
        state = _phase_start_state()
        state["completed_phases"] = ["CANDIDATE_ALLOCATED"]
        state["next_phase"] = _PHASE_ORDER[0]
        assert _issues(api(state)) == _failure("phase")
    elif case_id == "H01":
        api = _api("phase", case_id)
        assert _issues(api(_phase_start_state())) == ()
    elif case_id == "H02":
        api = _api("phase", case_id)
        state = _phase_start_state()
        state["completed_phases"] = [_PHASE_ORDER[0]]
        state["next_phase"] = _PHASE_ORDER[1]
        assert _issues(api(state)) == _failure("phase")
    elif case_id == "H03":
        api = _api("phase", case_id)
        state = _phase_start_state()
        row = {
            "phase": _PHASE_ORDER[0],
            "artifact_records": [
                {
                    "external_identity": _admission_fixture()[1],
                    "published_body": {},
                    "postfetch_body": {},
                    "publication_base_commit_sha1": "0" * 40,
                    "changed_paths": [],
                }
            ],
            "runtime_records": [],
            "owner_validation_state": "PROVED",
            "independent_verification_state": "PROVED",
            "phase_evidence_sha256": "",
        }
        row["phase_evidence_sha256"] = _hash_without(
            row,
            "phase_evidence_sha256",
        )
        state["completed_phases"] = [_PHASE_ORDER[0]]
        state["phase_evidence"] = [row]
        state["next_phase"] = _PHASE_ORDER[1]
        assert _issues(api(state)) == _failure("phase")
    elif case_id == "H04":
        api = _api("phase", case_id)
        state = _phase_start_state()
        row = {
            "phase": _PHASE_ORDER[3],
            "artifact_records": [],
            "runtime_records": [
                {
                    "evidence_role": (
                        "OPERATIONAL_RUNTIME_OBSERVATION_CANDIDATE"
                    ),
                    "evidence_body": {},
                    "logical_sha256": _sha256_value({}),
                    "body_free": True,
                }
            ],
            "owner_validation_state": "PROVED",
            "independent_verification_state": "PROVED",
            "phase_evidence_sha256": "",
        }
        row["phase_evidence_sha256"] = _hash_without(
            row,
            "phase_evidence_sha256",
        )
        state["completed_phases"] = list(_PHASE_ORDER[:4])
        state["phase_evidence"] = [row]
        state["next_phase"] = _PHASE_ORDER[4]
        assert _issues(api(state)) == _failure("phase")
    elif case_id == "H05":
        api = _api("phase", case_id)
        state = _phase_start_state()
        state["completed_phases"] = list(_PHASE_ORDER[:5])
        state["phase_evidence"] = []
        state["next_phase"] = _PHASE_ORDER[5]
        assert _issues(api(state)) == _failure("phase")
    else:
        raise AssertionError(case_id)


def test_s01_materializer_public_signature() -> None:
    _assert_case("S01")


def test_s02_reference_builder_public_signature() -> None:
    _assert_case("S02")


def test_s03_reference_verifier_public_signature() -> None:
    _assert_case("S03")


def test_s04_source_builder_public_signature() -> None:
    _assert_case("S04")


def test_s05_admission_builder_public_signature() -> None:
    _assert_case("S05")


def test_s06_admission_verifier_public_signature() -> None:
    _assert_case("S06")


def test_s07_phase_validator_public_signature() -> None:
    _assert_case("S07")


def test_m01_materializer_strict_exact9_input() -> None:
    _assert_case("M01")


def test_m02_materializer_exact_final_authority() -> None:
    _assert_case("M02")


def test_m03_materializer_lock_and_exact46_wheels() -> None:
    _assert_case("M03")


def test_m04_materializer_nofollow_snapshot_and_disjoint_roots() -> None:
    _assert_case("M04")


def test_m05_materializer_isolated_pip_and_sanitized_environment() -> None:
    _assert_case("M05")


def test_m06_materializer_root_identity_and_zero_effects() -> None:
    _assert_case("M06")


def test_r01_reference_builder_strict_exact2_input() -> None:
    _assert_case("R01")


def test_r02_reference_pipeline_final_authority_binding() -> None:
    _assert_case("R02")


def test_r03_reference_verifier_two_exact_modes() -> None:
    _assert_case("R03")


def test_r04_reference_fixture_injection_rejected() -> None:
    _assert_case("R04")


def test_r05_reference_independent_owner_import_separation() -> None:
    _assert_case("R05")


def test_c01_source_builder_strict_exact5_input() -> None:
    _assert_case("C01")


def test_c02_source_builder_source_identity_mismatch_rejected() -> None:
    _assert_case("C02")


def test_c03_source_builder_reference_identity_mismatch_rejected() -> None:
    _assert_case("C03")


def test_c04_source_exact20_bootstrap_exact33_nested_carrier() -> None:
    _assert_case("C04")


def test_o01_admission_builder_strict_exact8_input() -> None:
    _assert_case("O01")


def test_o02_admission_exact16_body_and_self_hash() -> None:
    _assert_case("O02")


def test_o03_admission_predecessor_exact8_full_identity() -> None:
    _assert_case("O03")


def test_o04_admission_authority_exact4_final_token() -> None:
    _assert_case("O04")


def test_o05_admission_scope_exact12_operation_set() -> None:
    _assert_case("O05")


def test_o06_admission_freshness_single_event1_consumption() -> None:
    _assert_case("O06")


def test_o07_admission_effect_boundary_exact15() -> None:
    _assert_case("O07")


def test_o08_admission_postfetch_ancestry_not_boolean() -> None:
    _assert_case("O08")


def test_p01_publication_operational_admission_role_path() -> None:
    _assert_case("P01")


def test_p02_publication_exact7_roles_exact6_paths() -> None:
    _assert_case("P02")


def test_p03_publication_each_candidate_exact1_path() -> None:
    _assert_case("P03")


def test_e01_event1_admission_carrier_positive_shape() -> None:
    _assert_case("E01")


def test_e02_event1_source_bootstrap_deep_equality() -> None:
    _assert_case("E02")


def test_e03_event1_primary_evidence_actual_admission() -> None:
    _assert_case("E03")


def test_e04_event1_supporting_exact2_changed_path_exact1() -> None:
    _assert_case("E04")


def test_e05_event1_equal_authority_tokens_explicit_approval() -> None:
    _assert_case("E05")


def test_e06_candidate_not_standalone_phase_completion() -> None:
    _assert_case("E06")


def test_h01_parent_phase_exact6_initial_state() -> None:
    _assert_case("H01")


def test_h02_parent_phase_name_without_evidence_rejected() -> None:
    _assert_case("H02")


def test_h03_parent_phase_artifact_record_requires_body_postfetch() -> None:
    _assert_case("H03")


def test_h04_parent_phase4_runtime_exact2_membership() -> None:
    _assert_case("H04")


def test_h05_parent_phase5_matches_phase4_candidates() -> None:
    _assert_case("H05")
