# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for identity-bound historical receipt byte-form remediation.

This exact11 oracle uses an explicitly supplied clean Cocolon repository
and an explicitly supplied clean mashos-api source repository.  It derives
the frozen historical exact6 from actual Git history and bytes.  Missing
additive APIs are resolved lazily inside each node, so they cannot create a
collection error.

The test never clones, searches for a repository, accesses a network,
materializes a runtime, publishes an artifact, allocates a candidate,
creates Event1/readiness/failure/reservation/attempt state, invokes formal
exact134, or advances Cycle001.
"""

import ast
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping
import unicodedata

import pytest


_TEST_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_prestart_predecessor_actual_git_"
    "bytes_exact6_operational_admission_v2_schema_dispatch_red.py"
)
_REPO_ROOT = Path(__file__).resolve().parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"

_LOGICAL_CYCLE_ID = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH_ID = "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
_ARTIFACT_REPOSITORY = "MassyuRed/Cocolon"
_SOURCE_REPOSITORY = "MassyuRed/mashos-api"
_SOURCE_REF = "refs/heads/main"
_HISTORICAL_ANCHOR_COMMIT = "7795950eefc4a925d18e44ac1dbc94fbd90033d0"
_HISTORICAL_ANCHOR_TREE = "e7226b8a39860b7b57577c877898b317e02d6ebd"
_FROZEN_SEED_SHA256 = (
    "3a08461e6f06c820038a29c5c547476842560f41865929e4c05454b220afaa00"
)
_V2_FINAL_IDENTIFIER = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_PRESTART_PREDECESSOR_"
    "CANONICAL_BYTES_REMEDIATED_FINAL_PRE_EVENT1_REFERENCE_RUNTIME_"
    "OBSERVATION_AND_OPERATIONAL_ADMISSION_V2_ISSUANCE_ONLY"
)
_V1_FINAL_IDENTIFIER = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_FINAL_PRE_EVENT1_REFERENCE_"
    "RUNTIME_OBSERVATION_AND_SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_"
    "CARRIER_ISSUANCE_INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_V1_OPERATIONAL_ADMISSION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
)
_V2_OPERATIONAL_ADMISSION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v2"
)
_DERIVATION_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "historical_receipt_byte_form_derivation_result.v1"
)
_SEED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.historical_predecessor_seed.v1"
)

_ORACLE_NAMES = (
    "PRESTART_OWNER_DERIVES_FROZEN_SEED_ACTUAL_EXACT6",
    "PRESTART_INDEPENDENT_DERIVES_SAME_CORE_WITHOUT_OWNER_RESULT",
    "POST_REFERENCE_OWNER_DERIVES_COMPLETE_EXACT8_SAME_CORE",
    (
        "V2_FINAL_IDENTIFIER_CONNECTS_REFERENCE_OWNER_INDEPENDENT_"
        "MATERIALIZER_OBSERVATION_CLOSURE_AND_PARENT_PHASE1"
    ),
    "V2_STRICT_PREPUBLICATION_INDEPENDENT_READS_ACTUAL_GIT_EXACT6",
    (
        "V2_STRICT_POSTFETCH_AND_PRE_EVENT1_PARENT_PHASES1_AND2_"
        "REEXECUTE_INDEPENDENT_ACTUAL_PATHS"
    ),
    "ORIGINAL_IDENTITIES_REMAIN_PRIMARY_AND_PROJECTION_IS_NOT_SUBSTITUTE",
    (
        "UNKNOWN_INJECTED_PROFILE_NAME_SELECTED_OR_FIXTURE_ONLY_INPUT_"
        "REJECTED"
    ),
    (
        "GIT_JSON_LOGICAL_PROJECTION_BASE_HEAD_AND_CROSS_LANE_DRIFT_"
        "FAIL_CLOSED"
    ),
    "V1_EXACT16_EXACT8_CANONICAL_LOADER_AND_APIS_REMAIN_UNCHANGED",
    (
        "DERIVATION_VALIDATION_SUCCESS_AND_FAILURE_INVOCATION_EFFECT_"
        "DELTAS_EXACT0"
    ),
)
_ORACLE_LIST_SHA256 = (
    "cce4bafb92cee323000baaf201f79b359053683ed5768293407e6845edec6ad0"
)
_NODE_NAMES = (
    "test_o01_prestart_owner_derives_frozen_seed_actual_exact6",
    (
        "test_o02_prestart_independent_derives_same_core_without_owner_"
        "result"
    ),
    "test_o03_post_reference_owner_derives_complete_exact8_same_core",
    (
        "test_o04_v2_final_identifier_connects_reference_owner_independent_"
        "materializer_observation_closure_and_parent_phase1"
    ),
    (
        "test_o05_v2_strict_prepublication_independent_reads_actual_git_"
        "exact6"
    ),
    (
        "test_o06_v2_strict_postfetch_and_pre_event1_parent_phases1_and2_"
        "reexecute_independent_actual_paths"
    ),
    (
        "test_o07_original_identities_remain_primary_and_projection_is_"
        "not_substitute"
    ),
    (
        "test_o08_unknown_injected_profile_name_selected_or_fixture_only_"
        "input_rejected"
    ),
    (
        "test_o09_git_json_logical_projection_base_head_and_cross_lane_"
        "drift_fail_closed"
    ),
    (
        "test_o10_v1_exact16_exact8_canonical_loader_and_apis_remain_"
        "unchanged"
    ),
    (
        "test_o11_derivation_validation_success_and_failure_invocation_"
        "effect_deltas_exact0"
    ),
)
_ORDERED_NODE_IDS = tuple(f"{_TEST_PATH}::{name}" for name in _NODE_NAMES)
_ORDERED_NODE_LIST_SHA256 = (
    "8e4fd061ea71338fd4e254881af8d19b27961d4f0e563cac4958f74df34e2ad4"
)
_CAUSAL_RED_SIGNATURES = {
    "O01": "O01_PRESTART_OWNER_ACTUAL_EXACT6_API_NOT_IMPLEMENTED",
    "O02": "O02_PRESTART_INDEPENDENT_ACTUAL_EXACT6_API_NOT_IMPLEMENTED",
    "O03": "O03_POST_REFERENCE_OWNER_CORE_SEAM_NOT_IMPLEMENTED",
    "O04": "O04_V2_FINAL_IDENTIFIER_CONNECTION_NOT_IMPLEMENTED",
    "O05": "O05_V2_STRICT_PREPUBLICATION_ACTUAL_GIT_NOT_IMPLEMENTED",
    "O06": "O06_V2_POSTFETCH_PARENT_REEXECUTION_NOT_IMPLEMENTED",
    "O07": "O07_PRIMARY_IDENTITY_PROJECTION_BOUNDARY_NOT_IMPLEMENTED",
    "O08": "O08_UNKNOWN_PROFILE_FIXTURE_REJECTION_NOT_IMPLEMENTED",
    "O09": "O09_GIT_JSON_CROSS_LANE_FAIL_CLOSED_NOT_IMPLEMENTED",
    "O11": "O11_DERIVATION_EFFECT_EXACT0_RESULT_NOT_IMPLEMENTED",
}

_MODULE_NAMES = {
    "contract": "emlis_ai_nls_v3_artifact_contract",
    "sequence": "emlis_ai_recovery_epoch002_sequence_ledger_v3",
    "closure": "emlis_ai_recovery_epoch002_canonical_current_closure_v3",
    "independent": "emlis_nls_v3_recovery_epoch002_closure_receipt_verify",
    "parent": "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3",
    "preflight": (
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight"
    ),
}
_OWNER_PRESTART_API = (
    "derive_recovery_epoch003_prestart_historical_receipt_byte_form_"
    "eligibility_v1"
)
_INDEPENDENT_PRESTART_API = (
    "verify_recovery_epoch003_prestart_historical_receipt_byte_form_"
    "eligibility_v1"
)
_MATERIALIZER_V2_API = "materialize_recovery_epoch003_reference_runtime_v2"
_REFERENCE_BUILDER_V2_API = (
    "build_recovery_epoch003_reference_runtime_observation_v2"
)
_REFERENCE_VERIFIER_V2_API = (
    "verify_recovery_epoch003_reference_runtime_observation_v2"
)
_SOURCE_BUILDER_V2_API = (
    "build_recovery_epoch003_source_bootstrap_closure_v2"
)
_SOURCE_VALIDATOR_V2_API = (
    "validate_recovery_epoch003_source_bootstrap_contract_state_v2"
)
_ADMISSION_BUILDER_V2_API = (
    "build_recovery_epoch003_operational_admission_v2"
)
_ADMISSION_VERIFIER_V2_API = (
    "verify_recovery_epoch003_operational_admission_contract_v2"
)
_PARENT_V2_API = (
    "validate_recovery_epoch003_parent_pre_event1_phase_evidence_state_v2"
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


_DERIVATION_RESULT_KEYS = _keys(
    """
    schema_version derivation_owner derivation_phase state failure_code
    input_binding_sha256 historical_binding_core_sha256
    source_baseline_state body_free automatic_progression pytest_main_called
    reference_runtime_materialization_count_delta
    operational_runtime_materialization_count_delta
    reference_observation_publication_count_delta
    operational_admission_publication_count_delta
    runtime_publication_count_delta candidate_publication_count_delta
    event1_publication_count_delta readiness_publication_count_delta
    failure_publication_count_delta reservation_count_delta
    attempt_count_delta formal_exact134_invocation_count_delta
    formal_collection_count_delta formal_execution_count_delta
    """
)
_DELTA_KEYS = _keys(
    """
    reference_runtime_materialization_count_delta
    operational_runtime_materialization_count_delta
    reference_observation_publication_count_delta
    operational_admission_publication_count_delta
    runtime_publication_count_delta candidate_publication_count_delta
    event1_publication_count_delta readiness_publication_count_delta
    failure_publication_count_delta reservation_count_delta
    attempt_count_delta formal_exact134_invocation_count_delta
    formal_collection_count_delta formal_execution_count_delta
    """
)
_TRANSIENT_ROW_KEYS = _keys(
    """
    binding_path container_identity_kind container_identity_sha256
    receipt_schema_version path publication_commit_sha1 git_blob_sha1
    raw_sha256 logical_hash_field logical_artifact_sha256 actual_byte_count
    canonical_projection_byte_count_with_lf
    canonical_projection_sha256_with_lf canonical_loader_error
    byte_form_state body_free row_sha256
    """
)
_V1_ADMISSION_KEYS_ORDERED = (
    "schema_version",
    "logical_cycle_id",
    "recovery_epoch_id",
    "predecessor_bindings",
    "source_closure",
    "bootstrap_closure",
    "authority",
    "scope",
    "freshness",
    "effect_boundary",
    "owner_validation_state",
    "independent_verification_state",
    "state",
    "automatic_progression",
    "body_free",
    "operational_admission_sha256",
)
_V1_PREDECESSOR_KEYS_ORDERED = (
    "p0_external_identity",
    (
        "operational_admission_parent_addendum_receipt_external_identity"
    ),
    "bootstrap_contract_d1_receipt_external_identity",
    "bootstrap_contract_d2_receipt_external_identity",
    "operational_admission_contract_d1_receipt_external_identity",
    "operational_admission_contract_d2_receipt_external_identity",
    "reference_runtime_observation_external_identity",
    "predecessor_bindings_sha256",
)
_CLOSED_FAILURE_CODES = frozenset(
    {
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID",
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_SEED_INVALID",
        (
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "REPOSITORY_OR_BASE_DRIFT"
        ),
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_BINDING_SET_INVALID",
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_GIT_IDENTITY_MISMATCH",
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_HISTORY_TOPOLOGY_INVALID",
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_STRICT_JSON_INVALID",
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_LOGICAL_HASH_MISMATCH",
        (
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "CANONICAL_DISPOSITION_MISMATCH"
        ),
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_PROJECTION_MISMATCH",
        "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_CROSS_LANE_MISMATCH",
        (
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
            "HISTORICAL_FALLBACK_FORBIDDEN"
        ),
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_BUILD_INVALID",
        (
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_"
            "VERIFICATION_INVALID"
        ),
        "RECOVERY_EPOCH003_PARENT_PRE_EVENT1_V2_INVALID",
    }
)

_P0_EXTERNAL_IDENTITY = {
    "schema_version": (
        "cocolon.emlis.nls_v3.step11.cycle001."
        "recovery_epoch003.p0_external_identity.v1"
    ),
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
        "git_blob_sha1": "faec07d12a277f4746e3aebd1db3778a12b67579",
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
        "git_blob_sha1": "7139227bbb5cb67102024786059c13a069dfb3f8",
        "raw_sha256": (
            "dd4af55855eb82fc1de5725a6c10873967def2a0e8e56d4ebc293be4258bd045"
        ),
        "logical_receipt_sha256": (
            "904baff49d3efd09a4a1486298962646d7c56a7f90e3ce8191d7e26072cf66db"
        ),
    },
    "p0_external_identity_sha256": (
        "74286b862eeee1663d2758ee18d1e848316da6fc27b12fef38c149c5a2b52f36"
    ),
}


def _external_identity(
    *,
    artifact_role: str,
    schema_version: str,
    path: str,
    publication_commit_sha1: str,
    git_blob_sha1: str,
    raw_sha256: str,
    logical_artifact_sha256: str,
    identity_sha256: str,
) -> dict[str, Any]:
    return {
        "artifact_role": artifact_role,
        "body_free": True,
        "git_blob_sha1": git_blob_sha1,
        "identity_sha256": identity_sha256,
        "logical_artifact_sha256": logical_artifact_sha256,
        "path": path,
        "publication_commit_sha1": publication_commit_sha1,
        "raw_sha256": raw_sha256,
        "repository_full_name": _ARTIFACT_REPOSITORY,
        "schema_version": schema_version,
    }


_DIRECT_IDENTITIES = {
    (
        "operational_admission_parent_addendum_"
        "receipt_external_identity"
    ): _external_identity(
        artifact_role=(
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_PARENT_ADDENDUM_"
            "DESIGN_FROZEN_RECEIPT"
        ),
        schema_version=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission_parent_addendum_design_frozen_receipt.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "FinalSourceBootstrapReferenceRuntimeClosureAndOperational"
            "AdmissionContractUnreachable_P0ParentAddendum_Design_ReadOnly_"
            "BodyFree_Receipt_20260729.json"
        ),
        publication_commit_sha1=(
            "1ed317111f64075d08e4a91d467dff7b9ebc3841"
        ),
        git_blob_sha1="15f35643c01be32ae4e56e9312c1e67b32075623",
        raw_sha256=(
            "fe4804fedae2f67e0fdd12199c0cc07439888103afc6e4b3738736b71d97eb69"
        ),
        logical_artifact_sha256=(
            "de707a6947537c6c2335586f7a5990850dbbbcd62c89e7fe6e3427d42635f404"
        ),
        identity_sha256=(
            "e8cc49a4983bb1c7e46948fb92ea605ce8fde7aa3a07926fbf047725e14bbf43"
        ),
    ),
    "bootstrap_contract_d1_receipt_external_identity": _external_identity(
        artifact_role=(
            "RECOVERY_EPOCH003_D1_BOOTSTRAP_ORACLE_CORRECTION_CAUSAL_RED_"
            "REFREEZE_RECEIPT"
        ),
        schema_version=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d1_bootstrap_oracle_correction_causal_red_refreeze_receipt.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_D1_"
            "BootstrapFormalExact134ManifestAndReferenceRuntimeRootIdentity"
            "Binding_OracleCorrectionAndCausalREDRefreeze_"
            "BodyFree_Receipt_20260729.json"
        ),
        publication_commit_sha1=(
            "31601a4f5ea3583ef1e9a839c55a8ace7677fd3e"
        ),
        git_blob_sha1="1ad1d3610916f48a3d7adafac76fcb93c4d47538",
        raw_sha256=(
            "0b6e491dedeb684b3f7d32b3a3acd231fbc724b994a75b1419c855428894a405"
        ),
        logical_artifact_sha256=(
            "cabe7aa0d50e94083edfd95b4641383aaa9ff11e44e60e7ea538e93252490370"
        ),
        identity_sha256=(
            "d9164d82715abb519b549a7581737a37ebd3bf153b53284697cbe4573a8edb9e"
        ),
    ),
    "bootstrap_contract_d2_receipt_external_identity": _external_identity(
        artifact_role=(
            "RECOVERY_EPOCH003_D2_BOOTSTRAP_SOURCE_RUNTIME_TARGETED_GREEN_"
            "RECEIPT"
        ),
        schema_version=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "d2_bootstrap_source_runtime_targeted_green_receipt.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_D2_"
            "BootstrapSourceRuntimeExpectedObservedSeparationSchemaPair"
            "DispatchEvent1ImmutabilityAndIndependentOperationalProjection_"
            "ImplementationAndTargetedGREEN_BodyFree_Receipt_20260729.json"
        ),
        publication_commit_sha1=(
            "1da49a13ee8a0a16d9c856861af55a3deb7468e4"
        ),
        git_blob_sha1="fd2396953e1a3fe6d8e2172f1cdf30a197406b0a",
        raw_sha256=(
            "a24184570ce97d46d4e13652c2417e77b41f730832861aa0cbddb9a9b3e5d6dd"
        ),
        logical_artifact_sha256=(
            "39ffbe4a791624c550eeb5d70d5326a26c88fee9e0a3880ae93e53066db570db"
        ),
        identity_sha256=(
            "cbd665b12b3af16b251a66073222d12823fb8776207922616718290e4bddc738"
        ),
    ),
    (
        "operational_admission_contract_d1_"
        "receipt_external_identity"
    ): _external_identity(
        artifact_role=(
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_CAUSAL_RED_"
            "RECEIPT"
        ),
        schema_version=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission_contract_causal_red_receipt.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "PostP0ParentAddendum_D1_OperationalAdmissionSourceBootstrap"
            "CarrierReferenceMaterializerEvent1BindingAndPhaseEvidence"
            "Contract_CausalRED_FreezeOnly_BodyFree_Receipt_20260729.json"
        ),
        publication_commit_sha1=(
            "7204220e366227182c78b44d254854c33e738147"
        ),
        git_blob_sha1="96cd768000f39738e95402b12aea0ca22dfbef50",
        raw_sha256=(
            "b859e4d6c89ca2912c4459d5d4a1844b2fd439b8fad71a4242d84b062d69bccd"
        ),
        logical_artifact_sha256=(
            "5a085d47b04fc75d5c4191261f1c9b8c00655932ac7e32bfe2096c43bd7e6650"
        ),
        identity_sha256=(
            "d1897d23f89d8df0fce8fd5591b77aeb3e2832197d1474aa8827b810805c174b"
        ),
    ),
    (
        "operational_admission_contract_d2_"
        "receipt_external_identity"
    ): _external_identity(
        artifact_role=(
            "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_CONTRACT_TARGETED_"
            "GREEN_RECEIPT"
        ),
        schema_version=(
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "operational_admission_contract_targeted_green_receipt.v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
            "PostP0ParentAddendum_D2_OperationalAdmissionSourceBootstrap"
            "CarrierReferenceMaterializerEvent1BindingAndPhaseEvidence"
            "Contract_ImplementationAndTargetedGREEN_"
            "BodyFree_Receipt_20260729.json"
        ),
        publication_commit_sha1=(
            "520d406102a31625be942fbbc903b0e01660c598"
        ),
        git_blob_sha1="7e0926d01e8d8b447ca110a0a09ff7b17e2ef488",
        raw_sha256=(
            "ccf3f5d5bb789910cdb3f7ff3fe10c208b5ce1ca91dffde117b5f01025604066"
        ),
        logical_artifact_sha256=(
            "922af50cc7475247cc95cb4199a54fd76c3649b87f8bf36e9b723326a9df9b61"
        ),
        identity_sha256=(
            "85dc3b8d64a12fa62f390e1c9ba654162c3f404122d0eb92f949647d6fcb3e30"
        ),
    ),
}

_CANONICAL_LOADER_PATH = (
    "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py"
)
_CANONICAL_LOADER_BLOB_SHA1 = "953d062fa858870e65d96cf03694d68c99003594"
_CANONICAL_LOADER_RAW_SHA256 = (
    "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b"
)
_FUNCTION_SOURCE_HASHES = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_nls_v3_artifact_contract.py"
    ): {
        "canonical_json_bytes": (
            "394387ad45c71df8437e6d2755d4043eaf6bb8e19f20514b508a8f40687c341c"
        ),
        "load_canonical_json_bytes": (
            "2176bce9b2421ccb3cd0217af346d164f4fd10bdca7b3d1d1223e81e0f168865"
        ),
    },
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ): {
        "build_recovery_epoch003_operational_admission": (
            "ad85c66692d2b8e9bb3787ef6d8afff21c0e4b4f4a08c1fa6978e1a07e8bbfae"
        ),
        "validate_recovery_epoch003_sequence_event1_contract_state": (
            "63ef2fb2e3a17e5aac2605cd82d8b40e7ffd07e1b0f1bec5baeb6dc994249695"
        ),
    },
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): {
        "build_recovery_epoch003_source_bootstrap_closure": (
            "24bf12d6d1937ae5dc54dc74a45094a779df2338ea40ff4862ddb710c4789002"
        ),
        "validate_recovery_epoch003_source_bootstrap_contract_state": (
            "eb255d7243f45acf194f20044748d1ad20971653faa3c09fbd39668021ed321e"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ): {
        "verify_recovery_epoch003_reference_runtime_observation": (
            "05cd2d7f8182fe1dc0ec20536445ab7d63ba092e47ff8f3f649211f1e1cb60b9"
        ),
        "verify_recovery_epoch003_operational_admission_contract": (
            "089bfb98ddf540ef85aa2ddcf97b15ab5cef8e6e55a35c5bad6ad4cfe2de50c5"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ): {
        "validate_recovery_epoch003_parent_phase_evidence_state": (
            "fcb7056bbd2868ad59115832c4f68a2c9728a945780ae4a9f5a546eaf4826c3e"
        ),
        "execute_recovery_epoch003_current_strict_parent_phase_v1": (
            "0865deb09995a19d6b0e91249e4a3176ed3cb64f55806e73cda3d56c5035a138"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): {
        "materialize_recovery_epoch003_reference_runtime": (
            "558f7cba3b57df408508974fa03ab6927cfb1830f92931bef615562ccc4e953b"
        ),
        "build_recovery_epoch003_reference_runtime_observation": (
            "9792f7446d6f26b48239df10c05f6283943259ee7eb65c0b3cd2ba8bd1bc364e"
        ),
        "execute_recovery_epoch003_current_strict_preflight_v1": (
            "faf706fa297e912ac43b534eda6da744449ec905f4cd3cb374951e70bb9b1cdc"
        ),
    },
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = dict(value)
    material.pop(key, None)
    return _sha256_value(material)


def _required_environment_path(name: str) -> Path:
    value = os.environ.get(name)
    if not value or not Path(value).is_absolute():
        raise AssertionError(f"{name}_EXPLICIT_ABSOLUTE_PATH_REQUIRED")
    return Path(value).resolve(strict=True)


def _required_environment_sha(name: str, length: int) -> str:
    value = os.environ.get(name, "")
    if re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is None:
        raise AssertionError(f"{name}_EXPLICIT_SHA_REQUIRED")
    return value


def _git(root: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def _is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=root,
            capture_output=True,
            timeout=30,
        ).returncode
        == 0
    )


def _assert_repository(
    root: Path,
    *,
    expected_name: str,
    expected_head: str,
    expected_tree: str,
) -> None:
    assert _git(root, "rev-parse", "--show-toplevel") == str(root)
    assert _git(root, "rev-parse", "HEAD") == expected_head
    assert _git(root, "rev-parse", "HEAD^{tree}") == expected_tree
    assert _git(root, "rev-parse", "origin/main") == expected_head
    assert _git(root, "status", "--porcelain", "--untracked-files=all") == ""
    remote = _git(root, "remote", "get-url", "origin")
    assert remote in {
        f"https://github.com/{expected_name}.git",
        f"https://github.com/{expected_name}",
    }


def _repository_inputs() -> tuple[Path, Path, str, str, str, str]:
    artifact_root = _required_environment_path(
        "COCOLON_ARTIFACT_REPOSITORY_ROOT"
    )
    source_root = _required_environment_path(
        "MASHOS_API_SOURCE_REPOSITORY_ROOT"
    )
    artifact_head = _required_environment_sha(
        "COCOLON_EXPECTED_HEAD_COMMIT_SHA1", 40
    )
    artifact_tree = _required_environment_sha(
        "COCOLON_EXPECTED_HEAD_TREE_SHA1", 40
    )
    source_head = _required_environment_sha(
        "MASHOS_API_EXPECTED_HEAD_COMMIT_SHA1", 40
    )
    source_tree = _required_environment_sha(
        "MASHOS_API_EXPECTED_HEAD_TREE_SHA1", 40
    )
    _assert_repository(
        artifact_root,
        expected_name=_ARTIFACT_REPOSITORY,
        expected_head=artifact_head,
        expected_tree=artifact_tree,
    )
    _assert_repository(
        source_root,
        expected_name=_SOURCE_REPOSITORY,
        expected_head=source_head,
        expected_tree=source_tree,
    )
    assert _git(artifact_root, "rev-parse", f"{_HISTORICAL_ANCHOR_COMMIT}^{{tree}}") == (
        _HISTORICAL_ANCHOR_TREE
    )
    assert _is_ancestor(
        artifact_root,
        _HISTORICAL_ANCHOR_COMMIT,
        artifact_head,
    )
    return (
        artifact_root,
        source_root,
        artifact_head,
        artifact_tree,
        source_head,
        source_tree,
    )


@lru_cache(maxsize=None)
def _module(role: str) -> Any:
    for root in (_INFERENCE_ROOT, _TOOLS_ROOT):
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
    return importlib.import_module(_MODULE_NAMES[role])


def _require_api(
    role: str,
    name: str,
    case_id: str,
) -> Callable[[Mapping[str, Any]], Any]:
    api = getattr(_module(role), name, None)
    if not callable(api):
        pytest.fail(_CAUSAL_RED_SIGNATURES[case_id], pytrace=False)
    return api


def _frozen_seed() -> dict[str, Any]:
    seed = {
        "schema_version": _SEED_SCHEMA,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "p0_external_identity": deepcopy(_P0_EXTERNAL_IDENTITY),
        "historical_receipt_external_identities": deepcopy(
            _DIRECT_IDENTITIES
        ),
        "historical_predecessor_seed_sha256": _FROZEN_SEED_SHA256,
    }
    assert _hash_without(
        seed,
        "historical_predecessor_seed_sha256",
    ) == _FROZEN_SEED_SHA256
    return seed


def _prestart_request() -> dict[str, Any]:
    (
        artifact_root,
        source_root,
        artifact_head,
        artifact_tree,
        source_head,
        source_tree,
    ) = _repository_inputs()
    return {
        "artifact_repository_root": str(artifact_root),
        "expected_artifact_head_commit_sha1": artifact_head,
        "expected_artifact_head_tree_sha1": artifact_tree,
        "historical_predecessor_seed": _frozen_seed(),
        "source_repository_root": str(source_root),
        "expected_source_head_commit_sha1": source_head,
        "expected_source_head_tree_sha1": source_tree,
        "automatic_progression": False,
    }


def _strict_json(raw: bytes) -> Any:
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in raw
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n")
    text = raw[:-1].decode("utf-8", errors="strict")

    def reject_constant(value: str) -> Any:
        raise ValueError(value)

    def closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(key)
            result[key] = value
        return result

    value = json.loads(
        text,
        parse_constant=reject_constant,
        object_pairs_hook=closed_object,
    )

    def nfc_stable(item: Any) -> bool:
        if type(item) is str:
            return unicodedata.normalize("NFC", item) == item
        if type(item) is list:
            return all(nfc_stable(child) for child in item)
        if type(item) is dict:
            return all(
                unicodedata.normalize("NFC", key) == key
                and nfc_stable(child)
                for key, child in item.items()
            )
        if type(item) is float:
            return math.isfinite(item)
        return item is None or type(item) in {bool, int}

    assert nfc_stable(value)
    return value


def _assert_history_record(
    root: Path,
    *,
    validation_head: str,
    path: str,
    publication_commit: str,
    blob: str,
    raw_sha256: str,
) -> bytes:
    parents = _git(
        root,
        "rev-list",
        "--parents",
        "-n",
        "1",
        publication_commit,
    ).split()
    assert len(parents) == 2
    parent = parents[1]
    changed = tuple(
        line
        for line in _git(
            root,
            "-c",
            "core.quotepath=false",
            "diff-tree",
            "--root",
            "--no-commit-id",
            "--name-only",
            "-r",
            publication_commit,
        ).splitlines()
        if line
    )
    assert changed == (path,)
    assert (
        subprocess.run(
            ["git", "cat-file", "-e", f"{parent}:{path}"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        ).returncode
        != 0
    )
    assert _is_ancestor(root, publication_commit, _HISTORICAL_ANCHOR_COMMIT)
    assert _is_ancestor(root, publication_commit, validation_head)
    assert (
        _git(
            root,
            "log",
            "--format=%H",
            f"{publication_commit}..{validation_head}",
            "--",
            path,
        )
        == ""
    )
    assert _git(root, "rev-parse", f"{publication_commit}:{path}") == blob
    assert _git(root, "rev-parse", f"{_HISTORICAL_ANCHOR_COMMIT}:{path}") == blob
    assert _git(root, "rev-parse", f"{validation_head}:{path}") == blob
    raw = _git_bytes(root, "show", f"{publication_commit}:{path}")
    assert raw == _git_bytes(root, "show", f"{validation_head}:{path}")
    assert hashlib.sha256(raw).hexdigest() == raw_sha256
    return raw


def _assert_p0_identity(
    root: Path,
    validation_head: str,
    p0: Mapping[str, Any],
) -> None:
    assert set(p0) == _keys(
        """
        schema_version logical_cycle_id recovery_epoch_id parent_design
        receipt p0_external_identity_sha256
        """
    )
    assert p0["p0_external_identity_sha256"] == _hash_without(
        p0,
        "p0_external_identity_sha256",
    )
    parent = p0["parent_design"]
    _assert_history_record(
        root,
        validation_head=validation_head,
        path=parent["path"],
        publication_commit=parent["publication_commit_sha1"],
        blob=parent["git_blob_sha1"],
        raw_sha256=parent["raw_sha256"],
    )


def _expected_rows() -> list[dict[str, Any]]:
    request = _prestart_request()
    root = Path(request["artifact_repository_root"])
    head = request["expected_artifact_head_commit_sha1"]
    seed = request["historical_predecessor_seed"]
    p0 = seed["p0_external_identity"]
    _assert_p0_identity(root, head, p0)
    contract = _module("contract")

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
    for key, identity in seed[
        "historical_receipt_external_identities"
    ].items():
        assert set(identity) == _keys(
            """
            artifact_role body_free git_blob_sha1 identity_sha256
            logical_artifact_sha256 path publication_commit_sha1 raw_sha256
            repository_full_name schema_version
            """
        )
        assert identity["identity_sha256"] == _hash_without(
            identity,
            "identity_sha256",
        )
        bindings.append(
            (
                key,
                "EXACT10_EXTERNAL_IDENTITY_V1",
                identity["identity_sha256"],
                identity,
                "logical_artifact_sha256",
            )
        )

    rows: list[dict[str, Any]] = []
    for (
        binding_path,
        container_kind,
        container_hash,
        identity,
        logical_key,
    ) in sorted(bindings, key=lambda item: item[0]):
        raw = _assert_history_record(
            root,
            validation_head=head,
            path=identity["path"],
            publication_commit=identity["publication_commit_sha1"],
            blob=identity["git_blob_sha1"],
            raw_sha256=identity["raw_sha256"],
        )
        body = _strict_json(raw)
        logical = body.get("receipt_sha256")
        assert logical == identity[logical_key]
        assert logical == _hash_without(body, "receipt_sha256")
        assert body.get("body_free") is True
        with pytest.raises(ValueError, match="^CANONICAL_BYTES_MISMATCH$"):
            contract.load_canonical_json_bytes(raw)
        projection = contract.canonical_json_bytes(body) + b"\n"
        assert projection != raw
        row = {
            "binding_path": binding_path,
            "container_identity_kind": container_kind,
            "container_identity_sha256": container_hash,
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
        row["row_sha256"] = _hash_without(row, "row_sha256")
        assert set(row) == _TRANSIENT_ROW_KEYS
        rows.append(row)
    assert len(rows) == 6
    return rows


def _expected_core() -> str:
    return _sha256_value(_expected_rows())


def _assert_zero_effects(result: Mapping[str, Any]) -> None:
    assert all(result.get(key) == 0 for key in _DELTA_KEYS)
    assert result.get("source_baseline_state") == "UNLOCKED"
    assert result.get("body_free") is True
    assert result.get("automatic_progression") is False
    assert result.get("pytest_main_called") is False


def _assert_derivation_result(
    result: Any,
    *,
    owner: str,
    valid: bool,
    expected_input_binding: str | None,
    expected_core: str | None,
    expected_failure: str | None = None,
) -> None:
    assert type(result) is dict
    assert set(result) == _DERIVATION_RESULT_KEYS
    assert result["schema_version"] == _DERIVATION_RESULT_SCHEMA
    assert result["derivation_owner"] == owner
    assert result["derivation_phase"] == "PRESTART"
    assert result["state"] == ("VALID" if valid else "INVALID")
    assert result["input_binding_sha256"] == expected_input_binding
    assert result["historical_binding_core_sha256"] == expected_core
    if valid:
        assert result["failure_code"] is None
    else:
        assert result["failure_code"] in _CLOSED_FAILURE_CODES
        if expected_failure is not None:
            assert result["failure_code"] == expected_failure
    _assert_zero_effects(result)


def _function_node(module: Any, name: str) -> ast.FunctionDef:
    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                assert isinstance(node, ast.FunctionDef)
                return node
    raise AssertionError(name)


def _reachable_functions(module: Any, root_name: str) -> tuple[str, ...]:
    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    pending = [root_name]
    reached: set[str] = set()
    while pending:
        name = pending.pop()
        if name in reached or name not in functions:
            continue
        reached.add(name)
        for node in ast.walk(functions[name]):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    pending.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    pending.append(node.func.attr)
    return tuple(sorted(reached))


def _reachable_source(module: Any, root_name: str) -> str:
    return "\n".join(
        inspect.getsource(getattr(module, name))
        for name in _reachable_functions(module, root_name)
        if callable(getattr(module, name, None))
    )


def _reachable_uses_scalar(
    module: Any,
    root_name: str,
    scalar: str,
) -> bool:
    source = _reachable_source(module, root_name)
    if scalar in source:
        return True
    scalar_names = {
        name
        for name, value in vars(module).items()
        if (
            value == scalar
            and isinstance(value, str)
            or isinstance(value, (tuple, list, set, frozenset))
            and scalar in value
        )
    }
    tree = ast.parse(source)
    used_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    return bool(scalar_names & used_names)


def _call_names(module: Any, root_name: str) -> frozenset[str]:
    tree = ast.parse(_reachable_source(module, root_name))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                names.add(node.func.attr)
    return frozenset(names)


def _dotted_name(node: ast.AST) -> str | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def _reachable_call_targets(
    module: Any,
    root_name: str,
) -> frozenset[str]:
    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    aliases: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                aliases[alias.asname or alias.name.split(".", 1)[0]] = (
                    alias.name
                )
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                aliases[alias.asname or alias.name] = (
                    f"{node.module}.{alias.name}"
                )

    targets: set[str] = set()
    for name in _reachable_functions(module, root_name):
        function = functions[name]
        for node in ast.walk(function):
            if not isinstance(node, ast.Call):
                continue
            dotted = _dotted_name(node.func)
            if dotted is not None:
                first, *rest = dotted.split(".")
                targets.add(".".join([aliases.get(first, first), *rest]))
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
                and len(node.args) >= 2
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            ):
                base = _dotted_name(node.args[0])
                if base is not None:
                    first, *rest = base.split(".")
                    targets.add(
                        ".".join(
                            [
                                aliases.get(first, first),
                                *rest,
                                node.args[1].value,
                            ]
                        )
                    )
    return frozenset(targets)


def _assert_no_effect_sink_calls(module: Any, root_name: str) -> None:
    names = set(_call_names(module, root_name))
    names.update(
        target.rsplit(".", 1)[-1]
        for target in _reachable_call_targets(module, root_name)
    )
    exact_forbidden = {
        "materialize_recovery_epoch002_locked_runtime",
        _MATERIALIZER_V2_API.removesuffix("_v2"),
        _MATERIALIZER_V2_API,
        "build_recovery_epoch002_readiness_artifact",
        _REFERENCE_BUILDER_V2_API.removesuffix("_v2"),
        _REFERENCE_BUILDER_V2_API,
        _ADMISSION_BUILDER_V2_API.removesuffix("_v2"),
        _ADMISSION_BUILDER_V2_API,
        "execute_recovery_epoch003_current_strict_parent_phase_v1",
        "execute_recovery_epoch003_current_strict_preflight_v1",
    }
    assert exact_forbidden.isdisjoint(names)


def _function_source_sha256(path: str, name: str) -> str:
    raw = (_REPO_ROOT / path).read_bytes()
    text = raw.decode("utf-8")
    tree = ast.parse(text)
    node = next(
        item
        for item in tree.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and item.name == name
    )
    start = min(
        [node.lineno]
        + [decorator.lineno for decorator in node.decorator_list]
    )
    physical = "".join(
        text.splitlines(keepends=True)[start - 1 : node.end_lineno]
    ).encode("utf-8")
    return hashlib.sha256(physical).hexdigest()


def _rehash_seed(seed: dict[str, Any]) -> dict[str, Any]:
    seed["historical_predecessor_seed_sha256"] = _hash_without(
        seed,
        "historical_predecessor_seed_sha256",
    )
    return seed


def test_o01_prestart_owner_derives_frozen_seed_actual_exact6() -> None:
    expected_core = _expected_core()
    owner = _require_api("sequence", _OWNER_PRESTART_API, "O01")
    result = owner(_prestart_request())
    _assert_derivation_result(
        result,
        owner="OWNER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )


def test_o02_prestart_independent_derives_same_core_without_owner_result() -> None:
    expected_core = _expected_core()
    independent_module = _module("independent")
    independent = _require_api(
        "independent",
        _INDEPENDENT_PRESTART_API,
        "O02",
    )
    signature = inspect.signature(independent)
    assert len(signature.parameters) == 1
    source_tree = ast.parse(
        _reachable_source(independent_module, _INDEPENDENT_PRESTART_API)
    )
    referenced = {
        node.id
        for node in ast.walk(source_tree)
        if isinstance(node, ast.Name)
    } | {
        node.attr
        for node in ast.walk(source_tree)
        if isinstance(node, ast.Attribute)
    }
    call_targets = _reachable_call_targets(
        independent_module,
        _INDEPENDENT_PRESTART_API,
    )
    assert _OWNER_PRESTART_API not in referenced
    assert not any(
        target == _OWNER_PRESTART_API
        or target.endswith(f".{_OWNER_PRESTART_API}")
        for target in call_targets
    )
    assert "owner_result" not in referenced
    result = independent(_prestart_request())
    _assert_derivation_result(
        result,
        owner="INDEPENDENT_VERIFIER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )


def test_o03_post_reference_owner_derives_complete_exact8_same_core() -> None:
    expected_core = _expected_core()
    sequence = _module("sequence")
    owner = _require_api("sequence", _OWNER_PRESTART_API, "O03")
    builder = _require_api("sequence", _ADMISSION_BUILDER_V2_API, "O03")
    prestart = owner(_prestart_request())
    _assert_derivation_result(
        prestart,
        owner="OWNER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )
    source = _reachable_source(sequence, _ADMISSION_BUILDER_V2_API)
    calls = _call_names(sequence, _ADMISSION_BUILDER_V2_API)
    assert "POST_REFERENCE" in source
    assert "predecessor_bindings_sha256" in source
    assert "historical_binding_core_sha256" in source
    assert "canonical_projection_sha256_with_lf" in source
    assert "IDENTITY_BOUND_HISTORICAL_NONCANONICAL_JSON" in source
    assert _MATERIALIZER_V2_API not in calls
    _assert_no_effect_sink_calls(sequence, _ADMISSION_BUILDER_V2_API)
    invalid = builder(
        {
            "predecessor_bindings": None,
            "source_closure": None,
            "bootstrap_closure": None,
            "authority": None,
            "scope": None,
            "freshness_policy": None,
            "reference_publication_state": None,
            "source_repository_observation": None,
        }
    )
    assert invalid == (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_BUILD_INVALID",
    )
    assert re.fullmatch(r"[0-9a-f]{64}", expected_core)


def test_o04_v2_final_identifier_connects_reference_owner_independent_materializer_observation_closure_and_parent_phase1() -> None:
    required = (
        ("preflight", _MATERIALIZER_V2_API),
        ("preflight", _REFERENCE_BUILDER_V2_API),
        ("independent", _REFERENCE_VERIFIER_V2_API),
        ("closure", _SOURCE_BUILDER_V2_API),
        ("closure", _SOURCE_VALIDATOR_V2_API),
        ("sequence", _ADMISSION_BUILDER_V2_API),
        ("independent", _ADMISSION_VERIFIER_V2_API),
        ("parent", _PARENT_V2_API),
    )
    for role, name in required:
        _require_api(role, name, "O04")
    for role, name in required[:7]:
        module = _module(role)
        assert _reachable_uses_scalar(
            module,
            name,
            _V2_FINAL_IDENTIFIER,
        )
        v1_name = name.removesuffix("_v2")
        assert v1_name not in _call_names(module, name)
        assert not any(
            target == v1_name or target.endswith(f".{v1_name}")
            for target in _reachable_call_targets(module, name)
        )
    parent_calls = _call_names(_module("parent"), _PARENT_V2_API)
    parent_source = _reachable_source(_module("parent"), _PARENT_V2_API)
    assert _REFERENCE_VERIFIER_V2_API in parent_calls
    assert "STRICT_REFERENCE_BODY_AND_POSTFETCH" in parent_source
    assert _MATERIALIZER_V2_API not in parent_calls
    assert _V2_OPERATIONAL_ADMISSION_SCHEMA != _V1_OPERATIONAL_ADMISSION_SCHEMA


def test_o05_v2_strict_prepublication_independent_reads_actual_git_exact6() -> None:
    expected_core = _expected_core()
    independent = _module("independent")
    derive = _require_api(
        "independent",
        _INDEPENDENT_PRESTART_API,
        "O05",
    )
    verifier = _require_api(
        "independent",
        _ADMISSION_VERIFIER_V2_API,
        "O05",
    )
    result = derive(_prestart_request())
    _assert_derivation_result(
        result,
        owner="INDEPENDENT_VERIFIER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )
    source = _reachable_source(independent, _ADMISSION_VERIFIER_V2_API)
    calls = _call_names(independent, _ADMISSION_VERIFIER_V2_API)
    assert "STRICT_PREPUBLICATION_ACTUAL" in source
    assert "historical_binding_core_sha256" in source
    assert "canonical_projection_sha256_with_lf" in source
    assert {
        "publication_commit_sha1",
        "git_blob_sha1",
        "raw_sha256",
        "receipt_sha256",
    } <= set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source))
    assert _MATERIALIZER_V2_API not in calls
    assert _REFERENCE_BUILDER_V2_API not in calls
    v1_verifier = _ADMISSION_VERIFIER_V2_API.removesuffix("_v2")
    assert v1_verifier not in calls
    assert not any(
        target == v1_verifier or target.endswith(f".{v1_verifier}")
        for target in _reachable_call_targets(
            independent,
            _ADMISSION_VERIFIER_V2_API,
        )
    )
    invalid = verifier(
        {
            "verification_mode": "STRICT_PREPUBLICATION_ACTUAL",
            "artifact_repository_root": str(_repository_inputs()[0]),
            "source_repository_observation": None,
            "operational_admission": None,
            "operational_admission_external_identity": None,
            "reference_runtime_observation": None,
            "reference_publication_state": None,
        }
    )
    assert invalid == (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_VERIFICATION_INVALID",
    )


def test_o06_v2_strict_postfetch_and_pre_event1_parent_phases1_and2_reexecute_independent_actual_paths() -> None:
    _require_api(
        "independent",
        _REFERENCE_VERIFIER_V2_API,
        "O06",
    )
    _require_api(
        "independent",
        _ADMISSION_VERIFIER_V2_API,
        "O06",
    )
    parent_api = _require_api("parent", _PARENT_V2_API, "O06")
    parent = _module("parent")
    source = _reachable_source(parent, _PARENT_V2_API)
    calls = _call_names(parent, _PARENT_V2_API)
    assert _REFERENCE_VERIFIER_V2_API in calls
    assert _ADMISSION_VERIFIER_V2_API in calls
    assert "STRICT_REFERENCE_BODY_AND_POSTFETCH" in source
    assert "STRICT_POSTFETCH_ACTUAL" in source
    assert "completed_phases" in source
    assert "reference_materialization_request" in source
    assert "reference_materialization_result" in source
    assert _reachable_uses_scalar(
        parent,
        _PARENT_V2_API,
        "REFERENCE_RUNTIME_OBSERVATION_PUBLISHED_AND_POSTVERIFIED",
    )
    assert _reachable_uses_scalar(
        parent,
        _PARENT_V2_API,
        "SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_CARRIER_"
        "PUBLISHED_AND_POSTVERIFIED",
    )
    assert "deepcopy" in calls
    assert _MATERIALIZER_V2_API not in calls
    assert _REFERENCE_BUILDER_V2_API not in calls
    _assert_no_effect_sink_calls(parent, _PARENT_V2_API)
    invalid = parent_api(
        {
            "parent_phase_evidence_state": {},
            "reference_materialization_request": None,
            "reference_materialization_result": None,
            "automatic_progression": False,
        }
    )
    assert invalid == ("RECOVERY_EPOCH003_PARENT_PRE_EVENT1_V2_INVALID",)


def test_o07_original_identities_remain_primary_and_projection_is_not_substitute() -> None:
    rows = _expected_rows()
    expected_core = _sha256_value(rows)
    owner = _require_api("sequence", _OWNER_PRESTART_API, "O07")
    valid_result = owner(_prestart_request())
    _assert_derivation_result(
        valid_result,
        owner="OWNER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )
    assert not (
        {
            "canonical_projection_sha256_with_lf",
            "canonical_projection_byte_count_with_lf",
            "historical_receipt_rows",
        }
        & set(valid_result)
    )

    request = _prestart_request()
    seed = request["historical_predecessor_seed"]
    key = "bootstrap_contract_d1_receipt_external_identity"
    identity = seed["historical_receipt_external_identities"][key]
    projected = next(row for row in rows if row["binding_path"] == key)
    identity["raw_sha256"] = projected[
        "canonical_projection_sha256_with_lf"
    ]
    identity["identity_sha256"] = _hash_without(
        identity,
        "identity_sha256",
    )
    _rehash_seed(seed)
    result = owner(request)
    _assert_derivation_result(
        result,
        owner="OWNER",
        valid=False,
        expected_input_binding=seed["historical_predecessor_seed_sha256"],
        expected_core=None,
        expected_failure=(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_GIT_IDENTITY_MISMATCH"
        ),
    )


def test_o08_unknown_injected_profile_name_selected_or_fixture_only_input_rejected() -> None:
    owner = _require_api("sequence", _OWNER_PRESTART_API, "O08")
    independent = _require_api(
        "independent",
        _INDEPENDENT_PRESTART_API,
        "O08",
    )
    cases: list[tuple[dict[str, Any], str | None, str]] = []

    selected = _prestart_request()
    selected["selected_profile_name"] = (
        "IDENTITY_BOUND_HISTORICAL_EXACT6"
    )
    cases.append(
        (
            selected,
            None,
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID",
        )
    )

    fixture = _prestart_request()
    fixture["fixture_only"] = True
    cases.append(
        (
            fixture,
            None,
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_INPUT_INVALID",
        )
    )

    injected = _prestart_request()
    seed = injected["historical_predecessor_seed"]
    seed["historical_receipt_external_identities"][
        "unknown_receipt_external_identity"
    ] = deepcopy(
        seed["historical_receipt_external_identities"][
            "bootstrap_contract_d1_receipt_external_identity"
        ]
    )
    _rehash_seed(seed)
    cases.append(
        (
            injected,
            seed["historical_predecessor_seed_sha256"],
            (
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "BINDING_SET_INVALID"
            ),
        )
    )

    for request, input_binding, failure in cases:
        for api, derivation_owner in (
            (owner, "OWNER"),
            (independent, "INDEPENDENT_VERIFIER"),
        ):
            result = api(deepcopy(request))
            _assert_derivation_result(
                result,
                owner=derivation_owner,
                valid=False,
                expected_input_binding=input_binding,
                expected_core=None,
                expected_failure=failure,
            )


def test_o09_git_json_logical_projection_base_head_and_cross_lane_drift_fail_closed() -> None:
    expected_core = _expected_core()
    owner = _require_api("sequence", _OWNER_PRESTART_API, "O09")
    independent = _require_api(
        "independent",
        _INDEPENDENT_PRESTART_API,
        "O09",
    )
    _require_api("sequence", _ADMISSION_BUILDER_V2_API, "O09")
    _require_api(
        "independent",
        _ADMISSION_VERIFIER_V2_API,
        "O09",
    )

    owner_valid = owner(_prestart_request())
    independent_valid = independent(_prestart_request())
    assert (
        owner_valid["historical_binding_core_sha256"]
        == independent_valid["historical_binding_core_sha256"]
        == expected_core
    )

    for api, derivation_owner in (
        (owner, "OWNER"),
        (independent, "INDEPENDENT_VERIFIER"),
    ):
        head_drift = _prestart_request()
        head_drift["expected_artifact_head_commit_sha1"] = "0" * 40
        drift_result = api(head_drift)
        _assert_derivation_result(
            drift_result,
            owner=derivation_owner,
            valid=False,
            expected_input_binding=None,
            expected_core=None,
            expected_failure=(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "REPOSITORY_OR_BASE_DRIFT"
            ),
        )

    logical_drift = _prestart_request()
    seed = logical_drift["historical_predecessor_seed"]
    identity = seed["historical_receipt_external_identities"][
        "bootstrap_contract_d2_receipt_external_identity"
    ]
    identity["logical_artifact_sha256"] = "0" * 64
    identity["identity_sha256"] = _hash_without(
        identity,
        "identity_sha256",
    )
    _rehash_seed(seed)
    logical_result = independent(logical_drift)
    _assert_derivation_result(
        logical_result,
        owner="INDEPENDENT_VERIFIER",
        valid=False,
        expected_input_binding=seed["historical_predecessor_seed_sha256"],
        expected_core=None,
        expected_failure=(
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_LOGICAL_HASH_MISMATCH"
        ),
    )

    owner_source = _reachable_source(
        _module("sequence"),
        _ADMISSION_BUILDER_V2_API,
    )
    independent_source = _reachable_source(
        _module("independent"),
        _ADMISSION_VERIFIER_V2_API,
    )
    for source in (owner_source, independent_source):
        assert (
            "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_CROSS_LANE_MISMATCH"
            in source
        )
        assert "canonical_projection_sha256_with_lf" in source


def test_o10_v1_exact16_exact8_canonical_loader_and_apis_remain_unchanged() -> None:
    assert _sha256_value(_ORACLE_NAMES) == _ORACLE_LIST_SHA256
    assert _sha256_value(_ORDERED_NODE_IDS) == _ORDERED_NODE_LIST_SHA256

    loader_raw = (_REPO_ROOT / _CANONICAL_LOADER_PATH).read_bytes()
    assert hashlib.sha256(loader_raw).hexdigest() == (
        _CANONICAL_LOADER_RAW_SHA256
    )
    assert _git(
        _REPO_ROOT,
        "rev-parse",
        f"HEAD:{_CANONICAL_LOADER_PATH}",
    ) == _CANONICAL_LOADER_BLOB_SHA1

    for path, functions in _FUNCTION_SOURCE_HASHES.items():
        for name, expected in functions.items():
            assert _function_source_sha256(path, name) == expected

    contract = _module("contract")
    canonical = contract.canonical_json_bytes({"b": 2, "a": 1}) + b"\n"
    assert canonical == b'{"a":1,"b":2}\n'
    assert contract.load_canonical_json_bytes(canonical) == {"a": 1, "b": 2}
    with pytest.raises(ValueError, match="^CANONICAL_BYTES_MISMATCH$"):
        contract.load_canonical_json_bytes(b'{\n  "a": 1,\n  "b": 2\n}\n')

    sequence = _module("sequence")
    independent = _module("independent")
    assert sequence._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA == (
        _V1_OPERATIONAL_ADMISSION_SCHEMA
    )
    assert independent._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA == (
        _V1_OPERATIONAL_ADMISSION_SCHEMA
    )
    assert set(sequence._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS) == (
        set(_V1_ADMISSION_KEYS_ORDERED)
    )
    assert set(independent._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS) == (
        set(_V1_ADMISSION_KEYS_ORDERED)
    )
    assert set(sequence._RECOVERY_EPOCH003_PREDECESSOR_KEYS) == set(
        _V1_PREDECESSOR_KEYS_ORDERED
    )
    assert set(independent._RECOVERY_EPOCH003_PREDECESSOR_KEYS) == set(
        _V1_PREDECESSOR_KEYS_ORDERED
    )
    assert _sha256_value(_V1_ADMISSION_KEYS_ORDERED) == (
        "965d297c7413c243cdebbc744f15334ca5eb0972801fd4254d443369f9caf66b"
    )
    assert _sha256_value(_V1_PREDECESSOR_KEYS_ORDERED) == (
        "ea2dfb2bf3289209bf272ec460173fd5b9ae0429e4adc7c6f900ced4b44458d8"
    )
    v1_owner_source = inspect.getsource(
        sequence.build_recovery_epoch003_operational_admission
    )
    v1_verifier_source = inspect.getsource(
        independent.verify_recovery_epoch003_operational_admission_contract
    )
    for module in (
        sequence,
        independent,
        _module("closure"),
        _module("preflight"),
    ):
        assert module._RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY == (
            _V1_FINAL_IDENTIFIER
        )
    assert "BODY_ONLY_BEFORE_PUBLICATION" in v1_verifier_source
    assert "BODY_AND_POSTFETCH" in v1_verifier_source
    assert _V2_OPERATIONAL_ADMISSION_SCHEMA not in v1_owner_source
    assert _V2_OPERATIONAL_ADMISSION_SCHEMA not in v1_verifier_source


def test_o11_derivation_validation_success_and_failure_invocation_effect_deltas_exact0() -> None:
    expected_core = _expected_core()
    owner = _require_api("sequence", _OWNER_PRESTART_API, "O11")
    independent = _require_api(
        "independent",
        _INDEPENDENT_PRESTART_API,
        "O11",
    )
    reference_verifier = _require_api(
        "independent",
        _REFERENCE_VERIFIER_V2_API,
        "O11",
    )
    admission_verifier = _require_api(
        "independent",
        _ADMISSION_VERIFIER_V2_API,
        "O11",
    )
    (
        artifact_root,
        source_root,
        artifact_head,
        artifact_tree,
        source_head,
        source_tree,
    ) = _repository_inputs()
    before = {
        "artifact_head": _git(artifact_root, "rev-parse", "HEAD"),
        "artifact_tree": _git(artifact_root, "rev-parse", "HEAD^{tree}"),
        "artifact_status": _git(
            artifact_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        ),
        "source_head": _git(source_root, "rev-parse", "HEAD"),
        "source_tree": _git(source_root, "rev-parse", "HEAD^{tree}"),
        "source_status": _git(
            source_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        ),
    }

    owner_success = owner(_prestart_request())
    independent_success = independent(_prestart_request())
    invalid_request = _prestart_request()
    invalid_request["expected_source_head_tree_sha1"] = "f" * 40
    owner_failure = owner(invalid_request)
    independent_failure = independent(invalid_request)
    reference_validation_failure = reference_verifier(
        {
            "verification_mode": "STRICT_REFERENCE_BODY_BEFORE_PUBLICATION",
            "materialization_request": None,
            "materialization_result": None,
            "reference_runtime_observation": None,
            "reference_runtime_observation_external_identity": None,
            "reference_publication_state": None,
        }
    )
    admission_validation_failure = admission_verifier(
        {
            "verification_mode": "STRICT_PREPUBLICATION_ACTUAL",
            "artifact_repository_root": str(artifact_root),
            "source_repository_observation": {
                "source_repository_root": str(source_root),
                "source_commit_sha1": source_head,
                "source_tree_sha1": source_tree,
                "worktree_clean": True,
            },
            "operational_admission": None,
            "operational_admission_external_identity": None,
            "reference_runtime_observation": None,
            "reference_publication_state": None,
        }
    )
    assert (
        type(reference_validation_failure) is tuple
        and len(reference_validation_failure) == 1
        and isinstance(reference_validation_failure[0], str)
        and reference_validation_failure[0]
    )
    assert admission_validation_failure == (
        "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_V2_VERIFICATION_INVALID",
    )
    assert _MATERIALIZER_V2_API not in _call_names(
        _module("independent"),
        _REFERENCE_VERIFIER_V2_API,
    )
    assert _MATERIALIZER_V2_API not in _call_names(
        _module("independent"),
        _ADMISSION_VERIFIER_V2_API,
    )
    for role, name in (
        ("sequence", _OWNER_PRESTART_API),
        ("independent", _INDEPENDENT_PRESTART_API),
        ("independent", _REFERENCE_VERIFIER_V2_API),
        ("independent", _ADMISSION_VERIFIER_V2_API),
    ):
        _assert_no_effect_sink_calls(_module(role), name)

    _assert_derivation_result(
        owner_success,
        owner="OWNER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )
    _assert_derivation_result(
        independent_success,
        owner="INDEPENDENT_VERIFIER",
        valid=True,
        expected_input_binding=_FROZEN_SEED_SHA256,
        expected_core=expected_core,
    )
    for result, derivation_owner in (
        (owner_failure, "OWNER"),
        (independent_failure, "INDEPENDENT_VERIFIER"),
    ):
        _assert_derivation_result(
            result,
            owner=derivation_owner,
            valid=False,
            expected_input_binding=None,
            expected_core=None,
            expected_failure=(
                "RECOVERY_EPOCH003_HISTORICAL_BYTE_FORM_"
                "REPOSITORY_OR_BASE_DRIFT"
            ),
        )

    after = {
        "artifact_head": _git(artifact_root, "rev-parse", "HEAD"),
        "artifact_tree": _git(artifact_root, "rev-parse", "HEAD^{tree}"),
        "artifact_status": _git(
            artifact_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        ),
        "source_head": _git(source_root, "rev-parse", "HEAD"),
        "source_tree": _git(source_root, "rev-parse", "HEAD^{tree}"),
        "source_status": _git(
            source_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        ),
    }
    assert before == after == {
        "artifact_head": artifact_head,
        "artifact_tree": artifact_tree,
        "artifact_status": "",
        "source_head": source_head,
        "source_tree": source_tree,
        "source_status": "",
    }
