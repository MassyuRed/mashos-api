from __future__ import annotations

import ast
import builtins
from collections import deque
from collections.abc import Iterator as IteratorABC
from collections.abc import Mapping as MappingABC
from collections.abc import Sequence as SequenceABC
from collections.abc import Set as SetABC
import copy
from functools import lru_cache, partial
import hashlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path, PurePath
import re
import runpy
import shutil
import subprocess
import sys
from types import FunctionType, GenericAlias, MethodType, ModuleType, UnionType
from typing import Any, Callable, Mapping

import pytest


_TEST_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch004_operational_admission_v2_"
    "event1_connection_actual_git_identity_parent_phase3_red.py"
)
_ENTRY_COMMIT_SHA1 = "97e8dd4d7021b8a1781d534aaa603f71dffa41b9"
_ENTRY_TREE_SHA1 = "cd3fc3da0976bbbcb708319e4bc8cbbb6a73ec19"
_LOGICAL_CYCLE_ID = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH_ID = "NLS_V3_CYCLE001_RECOVERY_EPOCH_004"
_D1_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH004_ADDITIVE_CORRECTIVE_P0_"
    "POSTVERIFIED_D1_OPERATIONAL_ADMISSION_V2_EVENT1_CONNECTION_OWNER_"
    "INDEPENDENT_SCHEMA_DISPATCH_ACTUAL_GIT_SOURCE_SUBJECT_OWNER_"
    "EXECUTOR_INDEPENDENT_EXECUTOR_IDENTITY_PARENT_PHASE3_EVIDENCE_AND_"
    "V1_EXACT16_EXACT8_INVARIANCE_CAUSAL_RED_FREEZE_ONLY"
)
_D1_AUTHORITY_STATE = "DEFINED_INACTIVE_SEPARATE_MASH_APPROVAL_REQUIRED"
_NON_CREDIT_FIXTURE_MARKER = (
    "MEMORY_ONLY_NON_CREDIT_CONTRACT_FIXTURE_NO_PUBLICATION_NO_EFFECT"
)
_CURRENT_P0_EXTERNAL_IDENTITY_SHA256 = (
    "aa602f6c7c39ea1ad0ece9ed6974c76b7dc8f3a4207540a290e3bb3eb06fe046"
)
_OLD_PARTIAL_P0_EXTERNAL_IDENTITY_SHA256 = (
    "e6659e9366b2c03b0ceef16bf2e0f8604d5e11226bbfd3fb1b070f9ab8bcac6a"
)
_CURRENT_RECONCILIATION_EXTERNAL_IDENTITY_SHA256 = (
    "c9eb76e54e6d956e9f082f46fdaf71abe6068a33a379fcb3c4b6c3c267542649"
)
_CURRENT_P0_EXTERNAL_IDENTITY = {
    "schema_version": (
        "cocolon.emlis.nls_v3.step11.cycle001.recovery_epoch004."
        "additive_corrective_p0_external_identity.v1"
    ),
    "logical_cycle_id": _LOGICAL_CYCLE_ID,
    "recovery_epoch_id": _RECOVERY_EPOCH_ID,
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
        _CURRENT_P0_EXTERNAL_IDENTITY_SHA256
    ),
}
_CURRENT_RECONCILIATION_EXTERNAL_IDENTITY = {
    "artifact_role": (
        "RECOVERY_EPOCH003_PRESTART_D2_IDENTITY_PREIMAGE_MISMATCH_"
        "DOWNSTREAM_CREDIT_PARTIAL_EPOCH004_P0_DISPOSITION_"
        "RECONCILIATION_RECEIPT"
    ),
    "body_free": True,
    "git_blob_sha1": "71798663e56d77e4b092dd5efd6d8999fb9fd81e",
    "identity_sha256": (
        _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY_SHA256
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
_HISTORICAL_CANDIDATE_VERSION_IDS = (
    "nls_v3_rc_0010",
    "nls_v3_rc_0027",
    "nls_v3_rc_0032",
    "nls_v3_rc_0034",
    "nls_v3_rc_epoch002_success_0001",
)
_CANDIDATE_VERSION_ID = (
    "nls_v3_cycle001_recovery_epoch004_non_credit_contract_fixture_0001"
)

_EVENT_SCHEMA_V2 = (
    "cocolon.emlis.nls_v3.recovery_epoch004.sequence_event.v2"
)
_OPERATIONAL_ADMISSION_SCHEMA_V2 = (
    "cocolon.emlis.nls_v3.recovery_epoch004.operational_admission.v2"
)
_CANDIDATE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004.candidate_allocation.v1"
)
_SOURCE_CLOSURE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "source_baseline_eligibility_closure.v1"
)
_BOOTSTRAP_CLOSURE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "formal_worker_bootstrap_manifest.v1"
)
_REFERENCE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "reference_runtime_observation.v1"
)
_REFERENCE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch004_PreEvent1_"
    "ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_OPERATIONAL_ADMISSION_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch004_"
    "OperationalAdmissionV2_BodyFree_Receipt.json"
)
_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch004_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event.json"
)

_OWNER_API = (
    "validate_recovery_epoch004_sequence_event1_contract_state_v2"
)
_INDEPENDENT_API = (
    "verify_recovery_epoch004_sequence_event1_contract_state_v2"
)
_PARENT_PHASE3_API = (
    "validate_recovery_epoch004_parent_phase3_event1_evidence_state_v2"
)
_PARENT_RECONSTRUCT_API = (
    "_reconstruct_recovery_epoch004_parent_phase3_event1_connection_v2"
)
_PARENT_POSTFETCH_VERIFY_API = (
    "_validate_recovery_epoch004_parent_phase3_postfetch_evidence_v2"
)
_ACTUAL_GIT_POSTFETCH_VERIFICATION_PROFILE = (
    "ACTUAL_GIT_POSTFETCH_VERIFIED_CREDIT_ELIGIBLE"
)

_OWNER_FAILURE = ("RECOVERY_EPOCH004_EVENT1_V2_CONNECTION_INVALID",)
_INDEPENDENT_FAILURE = (
    "RECOVERY_EPOCH004_EVENT1_V2_INDEPENDENT_VERIFICATION_INVALID",
)
_PARENT_FAILURE = (
    "RECOVERY_EPOCH004_PARENT_PHASE3_EVENT1_EVIDENCE_INVALID",
)

_CAUSAL_RED_SIGNATURES = {
    "O01": (
        "O01_RECOVERY_EPOCH004_EVENT1_V2_OWNER_API_NOT_IMPLEMENTED"
    ),
    "O02": (
        "O02_RECOVERY_EPOCH004_EVENT1_V2_INDEPENDENT_API_NOT_IMPLEMENTED"
    ),
    "O03": (
        "O03_RECOVERY_EPOCH004_EVENT1_V2_EXECUTOR_IDENTITY_"
        "CONNECTION_NOT_IMPLEMENTED"
    ),
    "O04": (
        "O04_RECOVERY_EPOCH004_EVENT1_V2_SCHEMA_DISPATCH_NOT_IMPLEMENTED"
    ),
    "O05": (
        "O05_RECOVERY_EPOCH004_EVENT1_V2_EXACT23_EXACTLY_ONCE_"
        "NOT_IMPLEMENTED"
    ),
    "O06": (
        "O06_RECOVERY_EPOCH004_PARENT_PHASE3_REEXECUTION_NOT_IMPLEMENTED"
    ),
    "O07": (
        "O07_RECOVERY_EPOCH004_EVENT1_V2_FAIL_CLOSED_ZERO_EFFECTS_"
        "NOT_IMPLEMENTED"
    ),
}

_ORACLE_NAMES = (
    "EVENT1_V2_OWNER_SCHEMA_DISPATCH_PUBLIC_SIGNATURE_AND_INVALID_ENVELOPE",
    (
        "EVENT1_V2_INDEPENDENT_SCHEMA_DISPATCH_REEXECUTES_WITHOUT_"
        "OWNER_TRUST"
    ),
    (
        "SOURCE_SUBJECT_OWNER_INDEPENDENT_SAME_ACTUAL_GIT_ROOT_HEAD_TREE_"
        "MODULE_BLOB_RAW"
    ),
    "UNKNOWN_MIXED_AND_V2_TO_V1_FALLBACK_REJECTED_FAIL_CLOSED",
    (
        "EVENT1_EXACT23_NESTS_DISTINCT_CANDIDATE_AND_CONSUMES_OA_V2_"
        "EXACTLY_ONCE"
    ),
    (
        "PARENT_PHASE3_RECONSTRUCTS_ACTUAL_POSTFETCH_AND_CALLS_"
        "INDEPENDENT_ONCE"
    ),
    "MISSING_MIXED_STALE_IDENTITY_EVIDENCE_FAILS_CLOSED_ZERO_EFFECTS",
    "V1_EXACT16_EXACT8_AND_PREDECESSOR_ORACLES_REMAIN_IMMUTABLE",
)
_ORACLE_LIST_SHA256 = (
    "8f91b84d07f3272e1e342ecf7fd3bb0015596b29608bda6251c42e9bd5a8de58"
)

_NODE_NAMES = (
    (
        "test_o01_event1_v2_owner_schema_dispatch_public_signature_and_"
        "invalid_envelope"
    ),
    (
        "test_o02_event1_v2_independent_schema_dispatch_reexecutes_"
        "without_owner_trust"
    ),
    (
        "test_o03_source_subject_owner_independent_same_actual_git_root_"
        "head_tree_module_blob_raw"
    ),
    (
        "test_o04_unknown_mixed_and_v2_to_v1_fallback_rejected_"
        "fail_closed"
    ),
    (
        "test_o05_event1_exact23_nests_distinct_candidate_and_consumes_"
        "oa_v2_exactly_once"
    ),
    (
        "test_o06_parent_phase3_reconstructs_actual_postfetch_and_calls_"
        "independent_once"
    ),
    (
        "test_o07_missing_mixed_stale_identity_evidence_fail_closed_with_"
        "zero_effects"
    ),
    (
        "test_o08_v1_exact16_exact8_and_predecessor_oracles_remain_"
        "immutable"
    ),
)
_ORDERED_NODE_IDS = tuple(f"{_TEST_PATH}::{name}" for name in _NODE_NAMES)
_ORDERED_NODE_LIST_SHA256 = (
    "e2661d946c060efc44ce7da06f8c55f51d10dfad2af4f5f0526bd38109c340bc"
)

_EVENT_KEYS_ORDERED = (
    "schema_version",
    "ledger_id",
    "event_id",
    "logical_cycle_id",
    "recovery_epoch_id",
    "candidate_version_id",
    "event_ordinal",
    "event_name",
    "state",
    "prior_event",
    "challenge_id",
    "timestamp_utc",
    "timestamp_kind",
    "authority",
    "p0_external_identity",
    "candidate_allocation",
    "source_closure",
    "bootstrap_closure",
    "primary_evidence_artifact",
    "publication",
    "body_free",
    "automatic_progression",
    "event_sha256",
)
_CANDIDATE_KEYS_ORDERED = (
    "schema_version",
    "logical_cycle_id",
    "recovery_epoch_id",
    "candidate_version_id",
    "allocated_at_utc",
    "p0_external_identity_sha256",
    "source_closure_sha256",
    "reference_runtime_observation_external_identity_sha256",
    "candidate_allocation_sha256",
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
_V2_PREDECESSOR_KEYS_ORDERED = (
    "p0_external_identity",
    "epoch003_immutable_predecessor_set_sha256",
    "epoch003_reconciliation_receipt_external_identity",
    "d1_event1_connection_receipt_external_identity",
    "d2_event1_connection_receipt_external_identity",
    "reference_runtime_observation_external_identity",
    "final_source_identity_contract_sha256",
    "predecessor_bindings_sha256",
)
_SOURCE_SUBJECT_KEYS = frozenset(
    {
        "repository_full_name",
        "source_ref",
        "repository_root",
        "head_commit_sha1",
        "head_tree_sha1",
        "origin_main_commit_sha1",
        "worktree_clean",
    }
)
_EXECUTOR_KEYS = frozenset(
    {
        *_SOURCE_SUBJECT_KEYS,
        "module_path",
        "module_origin",
        "git_blob_sha1",
        "raw_sha256",
    }
)
_CONNECTION_STATE_KEYS = frozenset(
    {
        "verification_profile",
        "credit_eligible",
        "approved_authority_token",
        "authority_state",
        "logical_cycle_id",
        "recovery_epoch_id",
        "p0_external_identity",
        "historical_candidate_version_ids",
        "reference_runtime_observation",
        "reference_runtime_observation_external_identity",
        "operational_admission",
        "operational_admission_external_identity",
        "event1",
        "event1_consumption_count",
        "source_subject",
        "owner_executor",
        "independent_executor",
        "source_baseline_state",
        "later_effect_counts",
        "automatic_progression",
    }
)
_PARENT_STATE_KEYS = frozenset(
    {
        "verification_profile",
        "credit_eligible",
        "approved_authority_token",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_repository_root",
        "source_subject",
        "owner_executor",
        "independent_executor",
        "parent_phase_evidence_state",
        "event1_connection_state",
        "source_baseline_state_before",
        "automatic_progression",
    }
)
_LATER_EFFECT_KEYS = frozenset(
    {
        "artifact_publication_count",
        "candidate_publication_count",
        "event1_publication_count",
        "runtime_materialization_count",
        "readiness_creation_count",
        "failure_creation_count",
        "reservation_creation_count",
        "attempt_creation_count",
        "formal_exact134_invocation_count",
        "source_baseline_lock_count",
    }
)
_V1_ADMISSION_KEYSET_SHA256 = (
    "965d297c7413c243cdebbc744f15334ca5eb0972801fd4254d443369f9caf66b"
)
_V1_PREDECESSOR_KEYSET_SHA256 = (
    "ea2dfb2bf3289209bf272ec460173fd5b9ae0429e4adc7c6f900ced4b44458d8"
)

_MODULE_NAMES = {
    "contract": "emlis_ai_nls_v3_artifact_contract",
    "sequence": "emlis_ai_recovery_epoch002_sequence_ledger_v3",
    "closure": "emlis_ai_recovery_epoch002_canonical_current_closure_v3",
    "independent": (
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify"
    ),
    "parent": (
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3"
    ),
    "preflight": (
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight"
    ),
}
_MANDATORY_DIRECT_PATHS = {
    "sequence": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "independent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "parent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
}
_FORMAL_OWNER_PATHS = (
    "ai/tools/emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py",
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ),
    _MANDATORY_DIRECT_PATHS["parent"],
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    _MANDATORY_DIRECT_PATHS["independent"],
    _MANDATORY_DIRECT_PATHS["sequence"],
)
_FROZEN_TOP_LEVEL_COMPLEX_MUTATION_HASHES = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): frozenset(
        {
            "33f33cabef8ecd5598af15a0c269445a761aa0b4c67d474a531577297219251f"
        }
    ),
    _MANDATORY_DIRECT_PATHS["sequence"]: frozenset(
        {
            "a54ee0031474ff2ab7501f74f46626252a3841813b4c8169a5ec0e7fb5c76c7a"
        }
    ),
}
_FROZEN_TOP_LEVEL_CONTROL_FLOW_HASHES = {
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ): frozenset(
        {
            "1d8999836d4869ecc42b1b80cfe3c398fc149f9595203dd38eeb428a0c819e8a",
            "b160a5c917570fbb22307e5ee0947b17aefda630d9d5a2ef0b028a4607b2c28b",
        }
    ),
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): frozenset(
        {
            "1d8999836d4869ecc42b1b80cfe3c398fc149f9595203dd38eeb428a0c819e8a",
            "b160a5c917570fbb22307e5ee0947b17aefda630d9d5a2ef0b028a4607b2c28b",
        }
    ),
}
_FROZEN_TOP_LEVEL_SORTED_KEY_CALL_HASHES = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): frozenset(
        {
            "7b297f4f8428ba430edbf0bc67c02a55aecf26571d078349c9da85bc47e16cd5"
        }
    ),
}
_FROZEN_TOP_LEVEL_OWNED_CALLABLE_CLOSURE_SHA256 = {
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ): "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a",
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): "c00e77830c5ac6a7ea78ee04ab9ab6a5eb3626d50da98f2ca5d1b5a6a30c91e2",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ): "2a1534385671970295235a69664edc829bbaca5fc2e7855c66cb3ac0fe571d77",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ): "f141673eca2dffe87d548a7fd0866ccf4bd7ecc5878b9d9d1061760075ba4268",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): "cabc3a3828e42c6da98c9d2969c81ba485db877bbe8306f7e71d321aa3a2e6fa",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ): "1858a563712853387cddc94856cb7757d69e4f23c05f3bb22846024b393666ad",
    _MANDATORY_DIRECT_PATHS[
        "sequence"
    ]: "5edf576eaf07b27f74afee75b6f4e9aef6e78b43a99938dcecc5b08fae20ef59",
}
_FROZEN_IMPORT_SURFACE_SHA256 = {
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ): "4942ba51e3a18aa0c2d8b9f4f06c0d06b2cc85187e372720474eb11dc1df83a5",
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): "fabe5eb58637529a6e8f74fdb005f389ee53f086862e9931cbefc00831037cbc",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ): "9ed21ef18db9d1c467fb089df34b54470a055657d6b80fe8df45753abdff91d8",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ): (
        "e82376028353c9f788da0caf797784f9ad74f8227d72cf77776b0cad7a4c1dd6",
        "886519bedf3536cc3f53ca64f29ae3c11117d27eeb62c164627910ec307e6980",
    ),
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): "f90206d21a1f051e44ccc888e69bca6a7ba0486c11201a83e9be6f60412ddca8",
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ): "6f7674fa27b5501510efa0258f18c716408978c15355e369647ec5816c17e93a",
    _MANDATORY_DIRECT_PATHS[
        "sequence"
    ]: "996e721b42385911f74b57468648b6589202fb08398c3d7d7d1c8897c598df8c",
}
_FROZEN_CLASS_DEFINITION_HASHES = {
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ): {
        "_RecoveryEpoch003PublicationRolePaths": (
            "8ac4bef024bc41aa21410751f810c5f43fad8110582688ccedef7f4805b8c742"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ): {
        "_CheckpointWriter": (
            "7b6e9466073e61564decd8f78adb66faba8e89aaadfeff6e63c41138b2eaedbf"
        ),
        "_BodyFreePytestCapture": (
            "fa300958a52b3cc96400c437e82c3524e3caac04371b4f5238fccd48d26d5eb5"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ): {
        "_AdditivePhaseOrderCompatibility": (
            "d0efdeaf67eadf2bff8e72e5c4279ddd83f63272d19f5b37841dd01ef5ad2ac4"
        ),
        "RecoveryEpoch002ParentPorts": (
            "44d718d1b9bf22db6b3d7bc678cdafb96f753c2008e8a6a67124fad67bf79ada"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ): {
        "_RecoveryEpoch003IndependentHistoricalByteFormError": (
            "222b5381a2a4457eb01108913ef96cba9c372ce32bf10f4ac4c9102742a95413"
        ),
    },
    _MANDATORY_DIRECT_PATHS["sequence"]: {
        "_RecoveryEpoch003HistoricalByteFormError": (
            "c084f18dd2fa6c583832387b5f9c875913232fb1f6737c002f8d2e88d806c4c1"
        ),
    },
}
_CANONICAL_LOADER_PATH = (
    "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py"
)
_CANONICAL_LOADER_BLOB_SHA1 = (
    "953d062fa858870e65d96cf03694d68c99003594"
)
_CANONICAL_LOADER_RAW_SHA256 = (
    "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b"
)

_FUNCTION_SOURCE_HASHES = {
    _CANONICAL_LOADER_PATH: {
        "canonical_json_bytes": (
            "394387ad45c71df8437e6d2755d4043eaf6bb8e19f20514b508a8f40687c341c"
        ),
        "load_canonical_json_bytes": (
            "2176bce9b2421ccb3cd0217af346d164f4fd10bdca7b3d1d1223e81e0f168865"
        ),
    },
    _MANDATORY_DIRECT_PATHS["sequence"]: {
        "build_recovery_epoch003_operational_admission": (
            "ad85c66692d2b8e9bb3787ef6d8afff21c0e4b4f4a08c1fa6978e1a07e8bbfae"
        ),
        "validate_recovery_epoch003_sequence_event1_contract_state": (
            "63ef2fb2e3a17e5aac2605cd82d8b40e7ffd07e1b0f1bec5baeb6dc994249695"
        ),
        "_recovery_epoch003_current_event_valid": (
            "17bc86dda311ac503e7634f459a5f62a8c9993fd0e4d00aced4410e69b093e32"
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
    _MANDATORY_DIRECT_PATHS["independent"]: {
        "verify_recovery_epoch003_reference_runtime_observation": (
            "05cd2d7f8182fe1dc0ec20536445ab7d63ba092e47ff8f3f649211f1e1cb60b9"
        ),
        "verify_recovery_epoch003_operational_admission_contract": (
            "089bfb98ddf540ef85aa2ddcf97b15ab5cef8e6e55a35c5bad6ad4cfe2de50c5"
        ),
        "_recovery_epoch003_current_event_nested_valid": (
            "78e835d067f5f9d1474a3d6d4b7c58bdf920829b7140ca8adb7a0bd08c571493"
        ),
    },
    _MANDATORY_DIRECT_PATHS["parent"]: {
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
        "_recovery_epoch003_baseline_valid": (
            "5087babfcc289f89548708858cf7a690bf21c5edbca0153e3cc2cbaa7f611df7"
        ),
    },
}
_FUNCTION_CLOSURE_HASHES = {
    _CANONICAL_LOADER_PATH: {
        "canonical_json_bytes": (
            "cf4bd5ed402efc4f1447165b07e2069f62ee54ce6335749667399fc2d2d4bdca"
        ),
        "load_canonical_json_bytes": (
            "a0a3fa040927c2bdb00439fe7bcd7f9fb94b45c99a58fb609806dd4de0304e2d"
        ),
    },
    _MANDATORY_DIRECT_PATHS["sequence"]: {
        "build_recovery_epoch003_operational_admission": (
            "9485762c76b129193340a020ca1451d6057f1cc304feebd66f0c59b8924af49b"
        ),
        "validate_recovery_epoch003_sequence_event1_contract_state": (
            "a1505bfe2fbe0e686d87b558629373dbcac81385103cbb2d06b205c8f9259183"
        ),
        "_recovery_epoch003_current_event_valid": (
            "65749a64dfdb5e4e6467abea393be3ad7f7c4fa1e9d9c5f2c043675b80300ee5"
        ),
    },
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): {
        "build_recovery_epoch003_source_bootstrap_closure": (
            "62db6c968383ed40d800baa6e39cb4936a1465d36732fbf6b68500a4183397ca"
        ),
        "validate_recovery_epoch003_source_bootstrap_contract_state": (
            "2a625a395d949e14d5e64b9f1d2da7dc33f36c828cfd5136b93b16fa4dd9fe5a"
        ),
    },
    _MANDATORY_DIRECT_PATHS["independent"]: {
        "verify_recovery_epoch003_reference_runtime_observation": (
            "84a395143d8cc57b685c1fd34978049492667fc81a88706442b7b82be48ce02b"
        ),
        "verify_recovery_epoch003_operational_admission_contract": (
            "d5667d97607f961627b1344a7b1004d9217040f5a2039b5922d795bca3ba47bc"
        ),
        "_recovery_epoch003_current_event_nested_valid": (
            "b77e0ade244e0e675a5c2378d9a1831a2117b190005eea79edbbc9c34ba19fb0"
        ),
    },
    _MANDATORY_DIRECT_PATHS["parent"]: {
        "validate_recovery_epoch003_parent_phase_evidence_state": (
            "0e994b5e0629320dea620768306a943c005ef06b3dba345c41a0a804c29edb36"
        ),
        "execute_recovery_epoch003_current_strict_parent_phase_v1": (
            "8956696ec98447b255e598a758692642834876484ec2c3f4b43b7b2e6c07e4a1"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): {
        "materialize_recovery_epoch003_reference_runtime": (
            "2156c02e2f494ff4d44b2dc9ee81b83c73f103d5e1c4f91275630bbd2ecabe35"
        ),
        "build_recovery_epoch003_reference_runtime_observation": (
            "f190ae2147cb2a0fda9c5281cfb3fc540cb8b386638522213d50bcb33b5d6544"
        ),
        "execute_recovery_epoch003_current_strict_preflight_v1": (
            "09b9506640a6e935583c77cfab54a6504ebaf73bacf956c8e89668485770b48a"
        ),
        "_recovery_epoch003_baseline_valid": (
            "f21f3c73b6d48841268dc3b4dea62698d27605a984b96bdc43fd899ea95af349"
        ),
    },
}
_V1_SEMANTIC_SURFACE_HASHES = {
    _CANONICAL_LOADER_PATH: (
        "3642263bbcbe674c7ffda8bd048587382095e2fa73d466afe156b0dba4ff9481"
    ),
    _MANDATORY_DIRECT_PATHS["sequence"]: (
        "fb16b996e085c7c8a6f8a49bcf4678f9b769254fe7de54b9c677a5bed19cb771"
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): (
        "ef32ff3ce2899be6ce74fe16c4b7dc118fb43ee33f1536aa0011c114f0aa578c"
    ),
    _MANDATORY_DIRECT_PATHS["independent"]: (
        "dedc9b657f2b61fe0f8ce23337087e06f9bd1aeccc515a0aefa04453c08def87"
    ),
    _MANDATORY_DIRECT_PATHS["parent"]: (
        "cb243283ccde3d6d61e2f9766464d720f820784c73cdc5d288dc46d1071da02b"
    ),
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): (
        "63632644df22821d8de8b00104f57a6c24e387867959152c6dd4445471744643"
    ),
}
_V1_CROSS_MODULE_SEMANTIC_SURFACE_SHA256 = (
    "3c011ddd89fca8d9dd962e56c76cabac60e32c0fd6980fad5c1afc7f211bdfe2"
)

_PREDECESSOR_TEST_IDENTITIES = {
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_operational_admission_"
        "contract_red.py"
    ): (
        "cd79f1be2f2321c90deb817c93e75e848ba7d3fe",
        "9af99873afd7d77f151e4b6b0a75f350bfc96a1aea781e047f162d1e5379560d",
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_bootstrap_source_runtime_"
        "expected_observed_contract_red.py"
    ): (
        "dda02f15be90387dd045ef117a5961961e2cae2b",
        "8c8fcaf5211064ca59127a8081dc41ae8b9207472f070746c84a8e4b591a07e5",
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_actual_unclassified_import_"
        "exact3_and_versioned_current_strict_preflight_connection_red.py"
    ): (
        "f705b5296088c15accc76eb629bac637d16c714a",
        "cda6119f9dc85fd386eb2447f1c85d8e250b973388866dad2fff6855d342311a",
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_prestart_predecessor_actual_"
        "git_bytes_exact6_operational_admission_v2_schema_dispatch_red.py"
    ): (
        "b61913a784512d65d712ee9bc6f15736b4ae91d2",
        "ac136e06c8eaa0bb9d7342b8cbe5669f974865e89d4fecbb0c24257893d6bb1a",
    ),
}
_IMMUTABLE_FIXTURE_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_bootstrap_source_runtime_"
    "expected_observed_contract_red.py"
)

_FORBIDDEN_EFFECT_CALL_NAMES = frozenset(
    {
        "__import__",
        "build_recovery_epoch002_readiness_artifact",
        "compile",
        "eval",
        "exec",
        "execute_recovery_epoch003_current_strict_preflight_v1",
        "importlib.import_module",
        "importlib.reload",
        "importlib.util.module_from_spec",
        "importlib.util.spec_from_file_location",
        "materialize_recovery_epoch003_reference_runtime",
        "materialize_recovery_epoch003_reference_runtime_v2",
        "os.chdir",
        "os.chroot",
        "os.kill",
        "os.killpg",
        "os.popen",
        "os.setegid",
        "os.seteuid",
        "os.setgid",
        "os.setgroups",
        "os.setregid",
        "os.setresgid",
        "os.setresuid",
        "os.setreuid",
        "os.setuid",
        "os.system",
        "pytest.main",
        "runpy.run_module",
        "runpy.run_path",
        "run_recovery_epoch002_current_step_proof",
        "subprocess.Popen",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
        "subprocess.getoutput",
        "subprocess.getstatusoutput",
        "sys.path.append",
        "sys.path.extend",
        "sys.path.insert",
        "sys.path.remove",
    }
)
_FORBIDDEN_EFFECT_CALL_TAILS = frozenset(
    {
        "Popen",
        "SourceFileLoader",
        "SourcelessFileLoader",
        "call",
        "chdir",
        "chroot",
        "chmod",
        "chown",
        "check_call",
        "check_output",
        "exec_module",
        "fdopen",
        "fork",
        "forkpty",
        "fchmod",
        "fchown",
        "fsync",
        "ftruncate",
        "get_code",
        "getoutput",
        "getstatusoutput",
        "load_module",
        "link",
        "lchmod",
        "lchown",
        "makedirs",
        "mkdtemp",
        "mkfifo",
        "mknod",
        "mkstemp",
        "mkdir",
        "module_from_spec",
        "open",
        "popen",
        "putenv",
        "remove",
        "removedirs",
        "rename",
        "renames",
        "replace",
        "rmdir",
        "run_module",
        "run_path",
        "spec_from_file_location",
        "system",
        "TemporaryDirectory",
        "NamedTemporaryFile",
        "touch",
        "truncate",
        "unlink",
        "unsetenv",
        "utime",
        "write",
        "write_bytes",
        "write_text",
        "writelines",
        "connect",
        "connect_ex",
        "create_connection",
        "create_server",
        "open_connection",
        "send",
        "sendall",
        "sendfile",
        "serve_forever",
        "setegid",
        "seteuid",
        "setgid",
        "setgroups",
        "setregid",
        "setresgid",
        "setresuid",
        "setreuid",
        "setuid",
        "start_server",
        "symlink",
        "sync",
        "umask",
        "urlopen",
    }
)
_FORBIDDEN_OWNER_TRUST_CALL_NAMES = frozenset(
    {
        "__import__",
        "compile",
        "eval",
        "exec",
        "importlib.import_module",
        "importlib.reload",
        "importlib.util.module_from_spec",
        "importlib.util.spec_from_file_location",
        "runpy.run_module",
        "runpy.run_path",
    }
)
_FORBIDDEN_OWNER_TRUST_CALL_TAILS = frozenset(
    {
        "SourceFileLoader",
        "SourcelessFileLoader",
        "exec_module",
        "get_code",
        "load_module",
        "module_from_spec",
        "run_module",
        "run_path",
        "spec_from_file_location",
    }
)


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
    payload = copy.deepcopy(dict(value))
    payload.pop(key, None)
    return _sha256_value(payload)


def _sha1_text(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout


def _remote_main_commit(root: Path) -> str:
    output = _git(
        root,
        "ls-remote",
        "--exit-code",
        "origin",
        "refs/heads/main",
    )
    rows = output.splitlines()
    assert len(rows) == 1
    commit, separator, ref = rows[0].partition("\t")
    assert separator == "\t"
    assert ref == "refs/heads/main"
    assert len(commit) == 40
    assert all(character in "0123456789abcdef" for character in commit)
    return commit


def _canonical_remote_repository(remote: str) -> str:
    value = remote.strip().removesuffix("/")
    if "://" in value:
        scheme, location = value.split("://", 1)
        assert scheme in {"git", "http", "https", "ssh"}
        authority, separator, path = location.partition("/")
        assert separator == "/" and authority
    else:
        authority, separator, path = value.partition(":")
        assert separator == ":" and authority and "@" in authority
    host_with_port = authority.rsplit("@", 1)[-1]
    host = host_with_port.partition(":")[0].lower()
    assert host in {
        "git.chatgpt-team.site",
        "github.com",
        "ssh.github.com",
        "www.github.com",
    }
    normalized_path = path.removesuffix(".git").strip("/")
    components = normalized_path.split("/")
    assert len(components) >= 2
    return "/".join(components[-2:])


def _repository_root(*, require_current_clean: bool = False) -> Path:
    configured = os.environ.get("MASHOS_API_SOURCE_REPOSITORY_ROOT")
    root = (
        Path(configured)
        if configured
        else Path(__file__).resolve().parents[2]
    ).resolve()
    assert _git(root, "rev-parse", "--show-toplevel") == str(root)
    remote = _git(root, "remote", "get-url", "origin")
    assert _canonical_remote_repository(remote) == "MassyuRed/mashos-api"
    assert (
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                _ENTRY_COMMIT_SHA1,
                "HEAD",
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode
        == 0
    )
    assert _git(root, "rev-parse", f"{_ENTRY_COMMIT_SHA1}^{{tree}}") == (
        _ENTRY_TREE_SHA1
    )
    expected_head = os.environ.get("MASHOS_API_EXPECTED_HEAD_COMMIT_SHA1")
    expected_tree = os.environ.get("MASHOS_API_EXPECTED_HEAD_TREE_SHA1")
    if expected_head is not None:
        assert _git(root, "rev-parse", "HEAD") == expected_head
    if expected_tree is not None:
        assert _git(root, "rev-parse", "HEAD^{tree}") == expected_tree
    if require_current_clean:
        assert _remote_main_commit(root) == _git(
            root,
            "rev-parse",
            "origin/main",
        )
        assert _git(root, "symbolic-ref", "--quiet", "HEAD") == (
            "refs/heads/main"
        )
        assert (
            _git(root, "status", "--porcelain", "--untracked-files=all")
            == ""
        )
        assert (
            subprocess.run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    _ENTRY_COMMIT_SHA1,
                    "origin/main",
                ],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
        )
        assert (
            subprocess.run(
                [
                    "git",
                    "merge-base",
                    "--is-ancestor",
                    "origin/main",
                    "HEAD",
                ],
                cwd=root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            ).returncode
            == 0
        )
    return root


def _prepare_imports(root: Path) -> None:
    for path in (
        root / "ai" / "services" / "ai_inference",
        root / "ai" / "tools",
    ):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


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
        "git_blob_sha1": _sha1_text(f"non-credit:blob:{role}:{path}"),
        "logical_artifact_sha256": logical_hash,
        "path": path,
        "publication_commit_sha1": _sha1_text(
            f"non-credit:commit:{role}:{path}"
        ),
        "raw_sha256": _sha256_text(f"non-credit:raw:{role}:{path}"),
        "repository_full_name": "MassyuRed/Cocolon",
        "schema_version": schema,
        "identity_sha256": "",
    }
    value["identity_sha256"] = _hash_without(value, "identity_sha256")
    return value


@lru_cache(maxsize=1)
def _immutable_fixture_module() -> ModuleType:
    root = _repository_root()
    path = root / _IMMUTABLE_FIXTURE_PATH
    spec = importlib.util.spec_from_file_location(
        "_recovery_epoch003_immutable_non_credit_fixture",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _actual_source_subject() -> dict[str, Any]:
    root = _repository_root(require_current_clean=True)
    return {
        "repository_full_name": "MassyuRed/mashos-api",
        "source_ref": "refs/heads/main",
        "repository_root": str(root),
        "head_commit_sha1": _git(root, "rev-parse", "HEAD"),
        "head_tree_sha1": _git(root, "rev-parse", "HEAD^{tree}"),
        "origin_main_commit_sha1": _git(
            root,
            "rev-parse",
            "origin/main",
        ),
        "worktree_clean": True,
    }


def _actual_executor(
    role: str,
    subject: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(str(subject["repository_root"]))
    path = _MANDATORY_DIRECT_PATHS[role]
    module = _module(role)
    origin = Path(inspect.getsourcefile(module) or "").resolve()
    raw = _git_bytes(root, "show", f"HEAD:{path}")
    assert origin == (root / path).resolve()
    assert origin.read_bytes() == raw
    return {
        **copy.deepcopy(dict(subject)),
        "module_path": path,
        "module_origin": str(origin),
        "git_blob_sha1": _git(root, "rev-parse", f"HEAD:{path}"),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
    }


def _reference_and_closures(
    subject: Mapping[str, Any],
    *,
    source_schema: str,
    bootstrap_schema: str,
    p0_external_identity_sha256: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    legacy = _immutable_fixture_module()
    reference = legacy._reference_observation()
    reference["schema_version"] = _REFERENCE_SCHEMA_V1
    reference["logical_cycle_id"] = _LOGICAL_CYCLE_ID
    reference["recovery_epoch_id"] = _RECOVERY_EPOCH_ID
    reference["authority_token"] = _NON_CREDIT_FIXTURE_MARKER
    reference["source_commit_sha1"] = subject["head_commit_sha1"]
    reference["source_tree_sha1"] = subject["head_tree_sha1"]
    reference["runtime_materialization"]["schema_version"] = (
        "cocolon.emlis.nls_v3.recovery_epoch004."
        "runtime_materialization.v1"
    )
    reference["runtime_materialization"][
        "runtime_materialization_state"
    ] = "NON_CREDIT_CONTRACT_FIXTURE_NOT_MATERIALIZED"
    reference["runtime_materialization"][
        "runtime_materialization_sha256"
    ] = _hash_without(
        reference["runtime_materialization"],
        "runtime_materialization_sha256",
    )
    reference["reference_runtime_observation_sha256"] = _hash_without(
        reference,
        "reference_runtime_observation_sha256",
    )
    reference_identity = _external_identity(
        role="RECOVERY_EPOCH004_REFERENCE_RUNTIME_OBSERVATION",
        schema=_REFERENCE_SCHEMA_V1,
        path=_REFERENCE_PATH,
        logical_hash=reference[
            "reference_runtime_observation_sha256"
        ],
    )
    bootstrap = legacy._bootstrap_closure(
        reference,
        reference_identity,
    )
    bootstrap["schema_version"] = bootstrap_schema
    bootstrap["source_commit_sha1"] = subject["head_commit_sha1"]
    bootstrap["source_tree_sha1"] = subject["head_tree_sha1"]
    bootstrap[
        "reference_runtime_observation_external_identity"
    ] = copy.deepcopy(reference_identity)
    bootstrap["bootstrap_closure_sha256"] = _hash_without(
        bootstrap,
        "bootstrap_closure_sha256",
    )
    source = legacy._source_closure(reference_identity, bootstrap)
    source["schema_version"] = source_schema
    source["repository_full_name"] = "MassyuRed/mashos-api"
    source["source_ref"] = "refs/heads/main"
    source["source_commit_sha1"] = subject["head_commit_sha1"]
    source["source_tree_sha1"] = subject["head_tree_sha1"]
    source["worktree_clean"] = True
    source.pop("epoch003_p0_external_identity_sha256")
    source["epoch004_p0_external_identity_sha256"] = (
        p0_external_identity_sha256
    )
    source.pop("epoch002_predecessor_set_sha256")
    source["epoch003_immutable_predecessor_set_sha256"] = _sha256_text(
        "immutable-epoch003-predecessor-set"
    )
    source["bootstrap_closure_sha256"] = bootstrap[
        "bootstrap_closure_sha256"
    ]
    source[
        "reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    source["source_closure_sha256"] = _hash_without(
        source,
        "source_closure_sha256",
    )
    assert len(reference) == 21
    assert len(source) == 20
    assert len(bootstrap) == 33
    return reference, reference_identity, source, bootstrap


def _non_credit_receipt_identity(stage: str) -> dict[str, Any]:
    return _external_identity(
        role=(
            f"RECOVERY_EPOCH004_{stage}_EVENT1_CONNECTION_"
            "NON_CREDIT_CONTRACT_FIXTURE_RECEIPT"
        ),
        schema=(
            "cocolon.emlis.nls_v3.recovery_epoch004."
            f"{stage.lower()}_event1_connection_non_credit_fixture_receipt."
            "v1"
        ),
        path=(
            "EmlisAIの実装済み資料/documents/"
            f"NON_CREDIT_TEST_ONLY_RecoveryEpoch004_{stage}_Receipt.json"
        ),
        logical_hash=_sha256_text(f"non-credit:{stage}:receipt"),
    )


def _operational_admission_fixture(
    *,
    subject: Mapping[str, Any],
    owner_executor: Mapping[str, Any],
    independent_executor: Mapping[str, Any],
    reference_identity: Mapping[str, Any],
    source: Mapping[str, Any],
    bootstrap: Mapping[str, Any],
    p0_external_identity: Mapping[str, Any],
    reconciliation_external_identity: Mapping[str, Any],
    admission_schema: str,
    reuse_allowed: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    predecessor = {
        "p0_external_identity": copy.deepcopy(
            dict(p0_external_identity)
        ),
        "epoch003_immutable_predecessor_set_sha256": _sha256_text(
            "immutable-epoch003-predecessor-set"
        ),
        "epoch003_reconciliation_receipt_external_identity": (
            copy.deepcopy(dict(reconciliation_external_identity))
        ),
        "d1_event1_connection_receipt_external_identity": (
            _non_credit_receipt_identity("D1")
        ),
        "d2_event1_connection_receipt_external_identity": (
            _non_credit_receipt_identity("D2")
        ),
        "reference_runtime_observation_external_identity": (
            copy.deepcopy(dict(reference_identity))
        ),
        "final_source_identity_contract_sha256": _sha256_value(
            {
                "source_subject": subject,
                "owner_executor": owner_executor,
                "independent_executor": independent_executor,
            }
        ),
        "predecessor_bindings_sha256": "",
    }
    predecessor["predecessor_bindings_sha256"] = _hash_without(
        predecessor,
        "predecessor_bindings_sha256",
    )
    authority = {
        "approval_kind": "NON_CREDIT_CONTRACT_FIXTURE_ONLY",
        "admission_authority_token": _NON_CREDIT_FIXTURE_MARKER,
        "publication_authority_token": _NON_CREDIT_FIXTURE_MARKER,
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
        "source_commit_sha1": subject["head_commit_sha1"],
        "source_tree_sha1": subject["head_tree_sha1"],
        "source_closure_sha256": source["source_closure_sha256"],
        "bootstrap_closure_sha256": bootstrap[
            "bootstrap_closure_sha256"
        ],
        "reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "next_authority_token": _NON_CREDIT_FIXTURE_MARKER,
        "operation_set": [
            "CANDIDATE_ALLOCATED_WITH_EVENT1_PUBLISHED_AND_POSTVERIFIED"
        ],
        "separate_explicit_authority_required": True,
        "scope_sha256": "",
    }
    scope["scope_sha256"] = _hash_without(scope, "scope_sha256")
    freshness = {
        "issued_at_utc": "2026-07-30T00:00:00Z",
        "expires_at_utc": None,
        "validity_mode": "IDENTITY_STABLE_SINGLE_EVENT1_CONSUMPTION",
        "bound_source_commit_sha1": subject["head_commit_sha1"],
        "bound_source_tree_sha1": subject["head_tree_sha1"],
        "bound_reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "event1_path_state_at_issuance": "ABSENT",
        "maximum_event1_consumption_count": 1,
        "invalidation_conditions": [
            "SOURCE_COMMIT_OR_TREE_DRIFT",
            "ORIGIN_MAIN_DRIFT",
            "WORKTREE_NOT_CLEAN",
            "EVENT1_ALREADY_CONSUMED",
        ],
        "reuse_allowed": reuse_allowed,
        "freshness_sha256": "",
    }
    freshness["freshness_sha256"] = _hash_without(
        freshness,
        "freshness_sha256",
    )
    effect = {
        "reference_runtime_materialization_count_delta": 0,
        "reference_runtime_observation_publication_count": 0,
        "operational_admission_publication_count": 0,
        "operational_runtime_materialization_count": 0,
        "candidate_allocation_count": 0,
        "sequence_event1_count": 0,
        "readiness_artifact_count": 0,
        "failure_artifact_count": 0,
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
        "schema_version": admission_schema,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "predecessor_bindings": predecessor,
        "source_closure": copy.deepcopy(dict(source)),
        "bootstrap_closure": copy.deepcopy(dict(bootstrap)),
        "authority": authority,
        "scope": scope,
        "freshness": freshness,
        "effect_boundary": effect,
        "owner_validation_state": "PROVED_NON_CREDIT_CONTRACT_FIXTURE",
        "independent_verification_state": (
            "PROVED_NON_CREDIT_CONTRACT_FIXTURE"
        ),
        "state": "NON_CREDIT_CONTRACT_FIXTURE_AWAITING_EVENT1",
        "automatic_progression": False,
        "body_free": True,
        "operational_admission_sha256": "",
    }
    admission["operational_admission_sha256"] = _hash_without(
        admission,
        "operational_admission_sha256",
    )
    admission_identity = _external_identity(
        role="RECOVERY_EPOCH004_OPERATIONAL_ADMISSION",
        schema=admission_schema,
        path=_OPERATIONAL_ADMISSION_PATH,
        logical_hash=admission["operational_admission_sha256"],
    )
    assert set(predecessor) == set(_V2_PREDECESSOR_KEYS_ORDERED)
    assert len(admission) == 16
    return admission, admission_identity


def _connection_fixture(
    *,
    event_schema: str = _EVENT_SCHEMA_V2,
    admission_schema: str = _OPERATIONAL_ADMISSION_SCHEMA_V2,
    candidate_schema: str = _CANDIDATE_SCHEMA_V1,
    source_schema: str = _SOURCE_CLOSURE_SCHEMA_V1,
    bootstrap_schema: str = _BOOTSTRAP_CLOSURE_SCHEMA_V1,
    candidate_version_id: str = _CANDIDATE_VERSION_ID,
    event1_consumption_count: int = 1,
    reuse_allowed: bool = False,
    expected_changed_path_count: int = 1,
    include_reference_support: bool = True,
    automatic_progression: bool = False,
    p0_external_identity: Mapping[str, Any] = (
        _CURRENT_P0_EXTERNAL_IDENTITY
    ),
    reconciliation_external_identity: Mapping[str, Any] = (
        _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY
    ),
) -> dict[str, Any]:
    subject = _actual_source_subject()
    owner_executor = _actual_executor("sequence", subject)
    independent_executor = _actual_executor("independent", subject)
    reference, reference_identity, source, bootstrap = (
        _reference_and_closures(
            subject,
            source_schema=source_schema,
            bootstrap_schema=bootstrap_schema,
            p0_external_identity_sha256=p0_external_identity[
                "p0_external_identity_sha256"
            ],
        )
    )
    admission, admission_identity = _operational_admission_fixture(
        subject=subject,
        owner_executor=owner_executor,
        independent_executor=independent_executor,
        reference_identity=reference_identity,
        source=source,
        bootstrap=bootstrap,
        p0_external_identity=p0_external_identity,
        reconciliation_external_identity=(
            reconciliation_external_identity
        ),
        admission_schema=admission_schema,
        reuse_allowed=reuse_allowed,
    )
    candidate = {
        "schema_version": candidate_schema,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": candidate_version_id,
        "allocated_at_utc": "2026-07-30T00:01:00Z",
        "p0_external_identity_sha256": (
            p0_external_identity["p0_external_identity_sha256"]
        ),
        "source_closure_sha256": source["source_closure_sha256"],
        "reference_runtime_observation_external_identity_sha256": (
            reference_identity["identity_sha256"]
        ),
        "candidate_allocation_sha256": "",
    }
    candidate["candidate_allocation_sha256"] = _hash_without(
        candidate,
        "candidate_allocation_sha256",
    )
    supporting = [copy.deepcopy(admission_identity)]
    if include_reference_support:
        supporting.append(copy.deepcopy(reference_identity))
    supporting.sort(
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        )
    )
    publication = {
        "base_commit_sha1": _sha1_text("non-credit:event1:base"),
        "branch": "main",
        "event_path": _EVENT1_PATH,
        "expected_changed_path_count": expected_changed_path_count,
        "publication_state": (
            "NON_CREDIT_CONTRACT_FIXTURE_NOT_PUBLISHED"
        ),
        "repository_full_name": "MassyuRed/Cocolon",
        "supporting_artifact_count": len(supporting),
        "supporting_artifact_set_sha256": _sha256_value(supporting),
        "supporting_artifacts": supporting,
    }
    event = {
        "schema_version": event_schema,
        "ledger_id": "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH004",
        "event_id": "NLS_V3_RECOVERY_EPOCH004_SEQUENCE_EVENT_01",
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "candidate_version_id": candidate_version_id,
        "event_ordinal": 1,
        "event_name": "SOURCE_BASELINE_LOCKED",
        "state": "NON_CREDIT_CONTRACT_FIXTURE_ONLY",
        "prior_event": copy.deepcopy(dict(p0_external_identity)),
        "challenge_id": _sha256_text("non-credit:epoch004:event1"),
        "timestamp_utc": "2026-07-30T00:02:00Z",
        "timestamp_kind": "NON_CREDIT_TEST_ONLY",
        "authority": {
            "approval_kind": "NON_CREDIT_CONTRACT_FIXTURE_ONLY",
            "operational_admission": copy.deepcopy(admission_identity),
            "publication_authority_token": _NON_CREDIT_FIXTURE_MARKER,
            "transition_authority_token": _NON_CREDIT_FIXTURE_MARKER,
        },
        "p0_external_identity": copy.deepcopy(
            dict(p0_external_identity)
        ),
        "candidate_allocation": candidate,
        "source_closure": copy.deepcopy(source),
        "bootstrap_closure": copy.deepcopy(bootstrap),
        "primary_evidence_artifact": copy.deepcopy(admission_identity),
        "publication": publication,
        "body_free": True,
        "automatic_progression": automatic_progression,
        "event_sha256": "",
    }
    event["event_sha256"] = _hash_without(event, "event_sha256")
    later_effects = {key: 0 for key in _LATER_EFFECT_KEYS}
    state = {
        "verification_profile": _NON_CREDIT_FIXTURE_MARKER,
        "credit_eligible": False,
        "approved_authority_token": _D1_AUTHORITY,
        "authority_state": _D1_AUTHORITY_STATE,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "p0_external_identity": copy.deepcopy(
            dict(p0_external_identity)
        ),
        "historical_candidate_version_ids": list(
            _HISTORICAL_CANDIDATE_VERSION_IDS
        ),
        "reference_runtime_observation": reference,
        "reference_runtime_observation_external_identity": (
            reference_identity
        ),
        "operational_admission": admission,
        "operational_admission_external_identity": admission_identity,
        "event1": event,
        "event1_consumption_count": event1_consumption_count,
        "source_subject": subject,
        "owner_executor": owner_executor,
        "independent_executor": independent_executor,
        "source_baseline_state": "UNLOCKED",
        "later_effect_counts": later_effects,
        "automatic_progression": automatic_progression,
    }
    assert set(state) == _CONNECTION_STATE_KEYS
    assert set(subject) == _SOURCE_SUBJECT_KEYS
    assert set(owner_executor) == _EXECUTOR_KEYS
    assert set(independent_executor) == _EXECUTOR_KEYS
    assert set(event) == set(_EVENT_KEYS_ORDERED)
    assert set(candidate) == set(_CANDIDATE_KEYS_ORDERED)
    assert set(later_effects) == _LATER_EFFECT_KEYS
    return state


def _rehash_external_identity(value: dict[str, Any]) -> None:
    value["identity_sha256"] = _hash_without(value, "identity_sha256")


def _rehash_event(state: dict[str, Any]) -> None:
    event = state["event1"]
    event["candidate_allocation"]["candidate_allocation_sha256"] = (
        _hash_without(
            event["candidate_allocation"],
            "candidate_allocation_sha256",
        )
    )
    event["event_sha256"] = _hash_without(event, "event_sha256")


def _rehash_admission_and_event(state: dict[str, Any]) -> None:
    admission = state["operational_admission"]
    predecessor = admission["predecessor_bindings"]
    predecessor["predecessor_bindings_sha256"] = _hash_without(
        predecessor,
        "predecessor_bindings_sha256",
    )
    for object_key, hash_key in (
        ("authority", "authority_sha256"),
        ("scope", "scope_sha256"),
        ("freshness", "freshness_sha256"),
        ("effect_boundary", "effect_boundary_sha256"),
    ):
        admission[object_key][hash_key] = _hash_without(
            admission[object_key],
            hash_key,
        )
    admission["operational_admission_sha256"] = _hash_without(
        admission,
        "operational_admission_sha256",
    )
    admission_identity = state[
        "operational_admission_external_identity"
    ]
    admission_identity["logical_artifact_sha256"] = admission[
        "operational_admission_sha256"
    ]
    _rehash_external_identity(admission_identity)
    event = state["event1"]
    event["authority"]["operational_admission"] = copy.deepcopy(
        admission_identity
    )
    event["primary_evidence_artifact"] = copy.deepcopy(
        admission_identity
    )
    reference_identity = state[
        "reference_runtime_observation_external_identity"
    ]
    supporting = sorted(
        [
            copy.deepcopy(admission_identity),
            copy.deepcopy(reference_identity),
        ],
        key=lambda row: (
            row["artifact_role"],
            row["path"],
            row["identity_sha256"],
        ),
    )
    event["publication"]["supporting_artifacts"] = supporting
    event["publication"]["supporting_artifact_count"] = 2
    event["publication"]["supporting_artifact_set_sha256"] = (
        _sha256_value(supporting)
    )
    _rehash_event(state)


def _normalize_source_bindings(state: dict[str, Any]) -> None:
    subject = state["source_subject"]
    reference = state["reference_runtime_observation"]
    reference["source_commit_sha1"] = subject["head_commit_sha1"]
    reference["source_tree_sha1"] = subject["head_tree_sha1"]
    reference["reference_runtime_observation_sha256"] = _hash_without(
        reference,
        "reference_runtime_observation_sha256",
    )
    reference_identity = state[
        "reference_runtime_observation_external_identity"
    ]
    reference_identity["logical_artifact_sha256"] = reference[
        "reference_runtime_observation_sha256"
    ]
    _rehash_external_identity(reference_identity)
    bootstrap = state["event1"]["bootstrap_closure"]
    bootstrap["source_commit_sha1"] = subject["head_commit_sha1"]
    bootstrap["source_tree_sha1"] = subject["head_tree_sha1"]
    bootstrap[
        "reference_runtime_observation_external_identity"
    ] = copy.deepcopy(reference_identity)
    bootstrap["bootstrap_closure_sha256"] = _hash_without(
        bootstrap,
        "bootstrap_closure_sha256",
    )
    source = state["event1"]["source_closure"]
    source["repository_full_name"] = subject["repository_full_name"]
    source["source_ref"] = subject["source_ref"]
    source["source_commit_sha1"] = subject["head_commit_sha1"]
    source["source_tree_sha1"] = subject["head_tree_sha1"]
    source["worktree_clean"] = subject["worktree_clean"]
    source["bootstrap_closure_sha256"] = bootstrap[
        "bootstrap_closure_sha256"
    ]
    source[
        "reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    source["source_closure_sha256"] = _hash_without(
        source,
        "source_closure_sha256",
    )
    admission = state["operational_admission"]
    admission["source_closure"] = copy.deepcopy(source)
    admission["bootstrap_closure"] = copy.deepcopy(bootstrap)
    admission["predecessor_bindings"][
        "reference_runtime_observation_external_identity"
    ] = copy.deepcopy(reference_identity)
    admission["scope"].update(
        {
            "source_repository_full_name": subject[
                "repository_full_name"
            ],
            "source_ref": subject["source_ref"],
            "source_commit_sha1": subject["head_commit_sha1"],
            "source_tree_sha1": subject["head_tree_sha1"],
            "source_closure_sha256": source["source_closure_sha256"],
            "bootstrap_closure_sha256": bootstrap[
                "bootstrap_closure_sha256"
            ],
            (
                "reference_runtime_observation_external_identity_sha256"
            ): reference_identity["identity_sha256"],
        }
    )
    admission["freshness"].update(
        {
            "bound_source_commit_sha1": subject["head_commit_sha1"],
            "bound_source_tree_sha1": subject["head_tree_sha1"],
            (
                "bound_reference_runtime_observation_external_identity_"
                "sha256"
            ): reference_identity["identity_sha256"],
        }
    )
    state["operational_admission"]["predecessor_bindings"][
        "final_source_identity_contract_sha256"
    ] = _sha256_value(
        {
            "source_subject": state["source_subject"],
            "owner_executor": state["owner_executor"],
            "independent_executor": state["independent_executor"],
        }
    )
    candidate = state["event1"]["candidate_allocation"]
    candidate["source_closure_sha256"] = source["source_closure_sha256"]
    candidate[
        "reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    state["event1"]["source_closure"] = source
    state["event1"]["bootstrap_closure"] = bootstrap
    _rehash_admission_and_event(state)


def _rehash_reference_chain(state: dict[str, Any]) -> None:
    reference = state["reference_runtime_observation"]
    reference["reference_runtime_observation_sha256"] = _hash_without(
        reference,
        "reference_runtime_observation_sha256",
    )
    reference_identity = state[
        "reference_runtime_observation_external_identity"
    ]
    reference_identity["logical_artifact_sha256"] = reference[
        "reference_runtime_observation_sha256"
    ]
    _rehash_external_identity(reference_identity)
    bootstrap = state["event1"]["bootstrap_closure"]
    bootstrap[
        "reference_runtime_observation_external_identity"
    ] = copy.deepcopy(reference_identity)
    bootstrap["bootstrap_closure_sha256"] = _hash_without(
        bootstrap,
        "bootstrap_closure_sha256",
    )
    source = state["event1"]["source_closure"]
    source["bootstrap_closure_sha256"] = bootstrap[
        "bootstrap_closure_sha256"
    ]
    source[
        "reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    source["source_closure_sha256"] = _hash_without(
        source,
        "source_closure_sha256",
    )
    admission = state["operational_admission"]
    admission["source_closure"] = copy.deepcopy(source)
    admission["bootstrap_closure"] = copy.deepcopy(bootstrap)
    admission["predecessor_bindings"][
        "reference_runtime_observation_external_identity"
    ] = copy.deepcopy(reference_identity)
    admission["scope"]["source_closure_sha256"] = source[
        "source_closure_sha256"
    ]
    admission["scope"]["bootstrap_closure_sha256"] = bootstrap[
        "bootstrap_closure_sha256"
    ]
    admission["scope"][
        "reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    admission["freshness"][
        "bound_reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    candidate = state["event1"]["candidate_allocation"]
    candidate["source_closure_sha256"] = source["source_closure_sha256"]
    candidate[
        "reference_runtime_observation_external_identity_sha256"
    ] = reference_identity["identity_sha256"]
    _rehash_admission_and_event(state)


def _coherent_artifact_source_forgery(
    state: Mapping[str, Any],
    *,
    field: str,
) -> dict[str, Any]:
    assert field in {"head_commit_sha1", "head_tree_sha1"}
    forged = copy.deepcopy(dict(state))
    actual_subject = copy.deepcopy(forged["source_subject"])
    artifact_subject = copy.deepcopy(actual_subject)
    artifact_subject[field] = "0" * 40
    forged["source_subject"] = artifact_subject
    _normalize_source_bindings(forged)
    forged["source_subject"] = actual_subject
    forged["operational_admission"]["predecessor_bindings"][
        "final_source_identity_contract_sha256"
    ] = _sha256_value(
        {
            "source_subject": forged["source_subject"],
            "owner_executor": forged["owner_executor"],
            "independent_executor": forged["independent_executor"],
        }
    )
    _rehash_admission_and_event(forged)
    return forged


def _coherent_git_forgery(
    state: Mapping[str, Any],
    *,
    role: str,
    field: str,
) -> dict[str, Any]:
    forged = copy.deepcopy(dict(state))
    original = forged[role][field]
    replacement: Any
    if isinstance(original, bool):
        replacement = not original
    elif field in {
        "git_blob_sha1",
        "head_commit_sha1",
        "head_tree_sha1",
        "origin_main_commit_sha1",
    }:
        replacement = "0" * 40
    elif field == "raw_sha256":
        replacement = "0" * 64
    else:
        replacement = f"{original}.forged"
    if field in _SOURCE_SUBJECT_KEYS:
        for target in (
            "source_subject",
            "owner_executor",
            "independent_executor",
        ):
            forged[target][field] = replacement
        _normalize_source_bindings(forged)
    else:
        forged[role][field] = replacement
        forged["operational_admission"]["predecessor_bindings"][
            "final_source_identity_contract_sha256"
        ] = _sha256_value(
            {
                "source_subject": forged["source_subject"],
                "owner_executor": forged["owner_executor"],
                "independent_executor": forged[
                    "independent_executor"
                ],
            }
        )
        _rehash_admission_and_event(forged)
    return forged


def _alternate_p0_external_identity() -> dict[str, Any]:
    value = copy.deepcopy(_CURRENT_P0_EXTERNAL_IDENTITY)
    value["parent_design"]["raw_sha256"] = "0" * 64
    value["p0_external_identity_sha256"] = _hash_without(
        value,
        "p0_external_identity_sha256",
    )
    assert value["p0_external_identity_sha256"] not in {
        _CURRENT_P0_EXTERNAL_IDENTITY_SHA256,
        _OLD_PARTIAL_P0_EXTERNAL_IDENTITY_SHA256,
    }
    return value


def _alternate_reconciliation_external_identity() -> dict[str, Any]:
    value = copy.deepcopy(_CURRENT_RECONCILIATION_EXTERNAL_IDENTITY)
    value["raw_sha256"] = "0" * 64
    value["identity_sha256"] = _hash_without(value, "identity_sha256")
    assert value["identity_sha256"] != (
        _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY_SHA256
    )
    return value


def _body_publication_evidence(
    body: Mapping[str, Any],
    external_identity: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "path": external_identity["path"],
        "publication_commit_sha1": external_identity[
            "publication_commit_sha1"
        ],
        "git_blob_sha1": external_identity["git_blob_sha1"],
        "raw_sha256": external_identity["raw_sha256"],
        "logical_artifact_sha256": external_identity[
            "logical_artifact_sha256"
        ],
        "identity_sha256": external_identity["identity_sha256"],
        "published_body": copy.deepcopy(dict(body)),
        "postfetch_body": copy.deepcopy(dict(body)),
    }


def _parent_fixture(
    connection: Mapping[str, Any],
) -> dict[str, Any]:
    event = connection["event1"]
    event_identity = _external_identity(
        role="RECOVERY_EPOCH004_SOURCE_BASELINE_EVENT",
        schema=_EVENT_SCHEMA_V2,
        path=_EVENT1_PATH,
        logical_hash=event["event_sha256"],
    )
    phase_evidence = {
        "completed_phases": [
            "REFERENCE_PUBLISHED_AND_POSTVERIFIED",
            "OPERATIONAL_ADMISSION_PUBLISHED_AND_POSTVERIFIED",
            "CANDIDATE_ALLOCATED_WITH_EVENT1_PUBLISHED_AND_POSTVERIFIED",
        ],
        "phase_evidence": {
            "reference_runtime_observation": _body_publication_evidence(
                connection["reference_runtime_observation"],
                connection[
                    "reference_runtime_observation_external_identity"
                ],
            ),
            "reference_runtime_observation_external_identity": (
                copy.deepcopy(
                    connection[
                        "reference_runtime_observation_external_identity"
                    ]
                )
            ),
            "operational_admission": _body_publication_evidence(
                connection["operational_admission"],
                connection["operational_admission_external_identity"],
            ),
            "operational_admission_external_identity": copy.deepcopy(
                connection["operational_admission_external_identity"]
            ),
            "event1": _body_publication_evidence(
                event,
                event_identity,
            ),
            "event1_external_identity": event_identity,
        },
        "next_phase": (
            "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT"
        ),
        "next_phase_state": "NOT_STARTED",
        "source_baseline_transition": (
            "LOCK_ONLY_AFTER_ACTUAL_EVENT1_POSTFETCH_VERIFICATION"
        ),
        "automatic_progression": False,
    }
    state = {
        "verification_profile": _NON_CREDIT_FIXTURE_MARKER,
        "credit_eligible": False,
        "approved_authority_token": _D1_AUTHORITY,
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "source_repository_root": connection["source_subject"][
            "repository_root"
        ],
        "source_subject": copy.deepcopy(connection["source_subject"]),
        "owner_executor": copy.deepcopy(connection["owner_executor"]),
        "independent_executor": copy.deepcopy(
            connection["independent_executor"]
        ),
        "parent_phase_evidence_state": phase_evidence,
        "event1_connection_state": copy.deepcopy(dict(connection)),
        "source_baseline_state_before": "UNLOCKED",
        "automatic_progression": False,
    }
    assert set(state) == _PARENT_STATE_KEYS
    return state


def _preflight_formal_owner_import_closure(root: Path) -> None:
    resolved_root = root.resolve()
    assert len(_FORMAL_OWNER_PATHS) == 7
    assert len(set(_FORMAL_OWNER_PATHS)) == 7
    for relative_path in _FORMAL_OWNER_PATHS:
        source_path = (resolved_root / relative_path).resolve()
        assert source_path.is_relative_to(resolved_root)
        assert source_path.is_file()
        _assert_no_effect_aliases(source_path)


def _module(role: str) -> ModuleType:
    root = _repository_root()
    _prepare_imports(root)
    _preflight_formal_owner_import_closure(root)
    return importlib.import_module(_MODULE_NAMES[role])


def _fresh_role_module(role: str, label: str) -> ModuleType:
    root = _repository_root()
    _prepare_imports(root)
    _preflight_formal_owner_import_closure(root)
    path = root / _MANDATORY_DIRECT_PATHS[role]
    spec = importlib.util.spec_from_file_location(
        f"_recovery_epoch004_{label}_{role}",
        path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _resolve_formal_owner_modules_for_read_only_guard(
    trusted_root: Path,
) -> dict[str, ModuleType]:
    resolved_modules: dict[str, ModuleType] = {}
    for relative_path in _FORMAL_OWNER_PATHS:
        module = importlib.import_module(Path(relative_path).stem)
        assert type(module) is ModuleType
        source_path = Path(inspect.getsourcefile(module) or "").resolve()
        assert source_path == (trusted_root / relative_path).resolve()
        resolved_modules[relative_path] = module
    assert set(resolved_modules) == set(_FORMAL_OWNER_PATHS)
    return resolved_modules


def _guard_api_read_only(
    api: Callable[[Mapping[str, Any]], Any],
    *,
    formal_owner_modules: Mapping[str, ModuleType] | None = None,
) -> Callable[[Mapping[str, Any]], Any]:
    trusted_root = _repository_root().resolve()
    trusted_git_path_text = shutil.which("git")
    assert trusted_git_path_text is not None
    trusted_git = Path(trusted_git_path_text).resolve()
    assert trusted_git.is_file()
    _prepare_imports(trusted_root)
    _preflight_formal_owner_import_closure(trusted_root)
    if formal_owner_modules is None:
        guarded_modules = _resolve_formal_owner_modules_for_read_only_guard(
            trusted_root
        )
    else:
        assert set(formal_owner_modules) == set(_FORMAL_OWNER_PATHS)
        guarded_modules = {}
        for relative_path in _FORMAL_OWNER_PATHS:
            module = formal_owner_modules[relative_path]
            assert type(module) is ModuleType
            source_path = Path(
                inspect.getsourcefile(module) or ""
            ).resolve()
            assert source_path == (trusted_root / relative_path).resolve()
            guarded_modules[relative_path] = module
    api_module = sys.modules.get(api.__module__)
    assert type(api_module) is ModuleType
    api_source_path = Path(inspect.getsourcefile(api) or "").resolve()
    api_relative_path = api_source_path.relative_to(trusted_root).as_posix()
    assert api_relative_path in guarded_modules
    guarded_modules[api_relative_path] = api_module

    def guarded_api(state: Mapping[str, Any]) -> Any:
        before_module_state = _formal_owner_module_state_sha256(
            guarded_modules,
            trusted_root,
        )
        delegated_run = subprocess.run

        def read_only_git_run(*args: Any, **kwargs: Any) -> Any:
            if args:
                assert len(args) == 1
                assert "args" not in kwargs
                command = args[0]
            else:
                assert "args" in kwargs
                command = kwargs.pop("args")
            assert isinstance(command, (list, tuple))
            argv = tuple(command)
            assert argv and all(type(item) is str for item in argv)
            requested_git = (
                Path(argv[0]).resolve()
                if Path(argv[0]).is_absolute()
                else Path(
                    shutil.which(argv[0], path=os.environ.get("PATH"))
                    or ""
                ).resolve()
            )
            assert requested_git == trusted_git
            index = 1
            root_bound_by_argv = False
            if index < len(argv) and argv[index] == "-C":
                assert index + 1 < len(argv)
                assert Path(argv[index + 1]).resolve() == trusted_root
                root_bound_by_argv = True
                index += 2
            assert index < len(argv)
            subcommand = argv[index]
            assert subcommand in {
                "hash-object",
                "ls-files",
                "ls-remote",
                "merge-base",
                "remote",
                "rev-parse",
                "show",
                "status",
                "symbolic-ref",
            }
            subcommand_args = argv[index + 1 :]
            assert all("\x00" not in item for item in subcommand_args)
            formal_paths = frozenset(_FORMAL_OWNER_PATHS)

            def safe_ref(value: str) -> bool:
                plain = value.removesuffix("^{tree}")
                return value in {
                    "HEAD",
                    "HEAD^{tree}",
                    "origin/main",
                } or bool(
                    len(plain) == 40
                    and all(
                        character in "0123456789abcdef"
                        for character in plain
                    )
                )

            git_args = argv[index:]
            read_only_shape = (
                git_args == ("remote", "get-url", "origin")
                or git_args
                == (
                    "ls-remote",
                    "--exit-code",
                    "origin",
                    "refs/heads/main",
                )
                or git_args == ("rev-parse", "--show-toplevel")
                or (
                    len(git_args) == 2
                    and git_args[0] == "rev-parse"
                    and (
                        safe_ref(git_args[1])
                        or (
                            git_args[1].startswith("HEAD:")
                            and git_args[1][5:] in formal_paths
                        )
                    )
                )
                or (
                    len(git_args) == 4
                    and git_args[:2] == (
                        "merge-base",
                        "--is-ancestor",
                    )
                    and safe_ref(git_args[2])
                    and safe_ref(git_args[3])
                )
                or (
                    len(git_args) == 2
                    and git_args[0] == "show"
                    and git_args[1].startswith("HEAD:")
                    and git_args[1][5:] in formal_paths
                )
                or (
                    len(git_args) == 2
                    and git_args[0] == "hash-object"
                    and git_args[1] in formal_paths
                )
                or (
                    len(git_args) == 3
                    and git_args[:2]
                    == ("ls-files", "--error-unmatch")
                    and git_args[2] in formal_paths
                )
                or git_args
                == ("status", "--porcelain", "--untracked-files=all")
                or git_args == ("symbolic-ref", "--quiet", "HEAD")
            )
            assert read_only_shape
            assert kwargs.get("shell", False) is False
            assert kwargs.get("executable") is None
            assert kwargs.get("preexec_fn") is None
            assert not kwargs.get("pass_fds", ())
            assert kwargs.get("start_new_session", False) is False
            assert kwargs.get("input") is None
            cwd = kwargs.get("cwd")
            if cwd is not None:
                assert Path(cwd).resolve() == trusted_root
            else:
                assert root_bound_by_argv
            supplied_env = kwargs.get("env")
            assert supplied_env is None
            child_env = {
                key: value
                for key, value in os.environ.items()
                if not (
                    key.startswith("GIT_")
                    or key
                    in {
                        "LD_AUDIT",
                        "LD_LIBRARY_PATH",
                        "LD_PRELOAD",
                        "PYTHONPATH",
                    }
                )
            }
            child_env.update(
                {
                    "GIT_ATTR_NOSYSTEM": "1",
                    "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_CONFIG_NOSYSTEM": "1",
                    "GIT_EXTERNAL_DIFF": "",
                    "GIT_OPTIONAL_LOCKS": "0",
                    "GIT_PAGER": "cat",
                    "GIT_TERMINAL_PROMPT": "0",
                    "PATH": str(trusted_git.parent),
                }
            )
            kwargs["env"] = child_env
            guarded_argv = (str(trusted_git), *argv[1:])
            return delegated_run(list(guarded_argv), **kwargs)

        subprocess.run = read_only_git_run
        try:
            return api(state)
        finally:
            try:
                assert _formal_owner_module_state_sha256(
                    guarded_modules,
                    trusted_root,
                ) == before_module_state
            finally:
                subprocess.run = delegated_run

    guarded_api.__wrapped__ = api  # type: ignore[attr-defined]
    guarded_api.__name__ = api.__name__
    guarded_api.__qualname__ = api.__qualname__
    guarded_api.__module__ = api.__module__
    return guarded_api


def _module_level_bindings(
    tree: ast.Module,
) -> dict[str, list[ast.AST]]:
    bindings: dict[str, list[ast.AST]] = {}

    def add(name: str | None, node: ast.AST) -> None:
        if name:
            bindings.setdefault(name, []).append(node)

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add(node.name, node)
            for expression in (
                *node.decorator_list,
                *node.args.defaults,
                *(
                    value
                    for value in node.args.kw_defaults
                    if value is not None
                ),
            ):
                visit(expression)
            return
        if isinstance(node, ast.ClassDef):
            add(node.name, node)
            for expression in (
                *node.decorator_list,
                *node.bases,
                *(keyword.value for keyword in node.keywords),
            ):
                visit(expression)
            return
        if isinstance(node, ast.Lambda):
            for expression in (
                *node.args.defaults,
                *(
                    value
                    for value in node.args.kw_defaults
                    if value is not None
                ),
            ):
                visit(expression)
            return
        if isinstance(node, ast.Import):
            for alias in node.names:
                add(alias.asname or alias.name.partition(".")[0], alias)
            return
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                add(alias.asname or alias.name, alias)
            return
        if isinstance(node, ast.ExceptHandler):
            add(node.name, node)
        if isinstance(node, ast.MatchAs):
            add(node.name, node)
        elif isinstance(node, ast.MatchStar):
            add(node.name, node)
        elif isinstance(node, ast.MatchMapping):
            add(node.rest, node)
        if isinstance(node, ast.Name) and isinstance(
            node.ctx,
            (ast.Store, ast.Del),
        ):
            add(node.id, node)
        if isinstance(
            node,
            (ast.ListComp, ast.SetComp, ast.GeneratorExp),
        ):
            visit(node.elt)
            for generator in node.generators:
                visit(generator.iter)
                for condition in generator.ifs:
                    visit(condition)
            return
        if isinstance(node, ast.DictComp):
            visit(node.key)
            visit(node.value)
            for generator in node.generators:
                visit(generator.iter)
                for condition in generator.ifs:
                    visit(condition)
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in tree.body:
        visit(statement)
    return bindings


def _runtime_function_node(
    module: ModuleType,
    name: str,
) -> ast.FunctionDef:
    source_path = Path(inspect.getsourcefile(module) or "").resolve()
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    bindings = _module_level_bindings(tree)
    nodes = bindings.get(name)
    assert nodes is not None and len(nodes) == 1
    node = nodes[0]
    assert isinstance(node, ast.FunctionDef)
    runtime = ModuleType.__getattribute__(module, name)
    assert inspect.isfunction(runtime)
    assert runtime.__module__ == module.__name__
    assert runtime.__name__ == name
    assert runtime.__qualname__ == name
    assert runtime.__code__.co_firstlineno == node.lineno
    assert Path(inspect.getsourcefile(runtime) or "").resolve() == source_path
    return node


def _require_api(
    role: str,
    name: str,
    oracle: str,
) -> Callable[[Mapping[str, Any]], Any]:
    module = _module(role)
    api = getattr(module, name, None)
    if not callable(api):
        pytest.fail(_CAUSAL_RED_SIGNATURES[oracle], pytrace=False)
    _runtime_function_node(module, name)
    _assert_no_effect_aliases(module)
    _assert_no_cached_effect_objects(module)
    if role == "independent":
        _assert_independent_owner_boundary(module)
        _assert_no_owner_runtime_references(module)
    _assert_no_effect_sink_calls(module, name)
    return _guard_api_read_only(api)


def _function_node(module: ModuleType, name: str) -> ast.FunctionDef:
    return _runtime_function_node(module, name)


def _reachable_function_names(
    module: ModuleType,
    root_name: str,
) -> tuple[str, ...]:
    source = Path(inspect.getsourcefile(module) or "").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert len(functions) == sum(
        isinstance(node, ast.FunctionDef) for node in tree.body
    )
    assert root_name in functions
    pending = [root_name]
    seen: list[str] = []
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.append(name)
        node = _runtime_function_node(module, name)
        calls: set[str] = set()
        for child in ast.walk(node):
            if not (
                isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
            ):
                continue
            called_name = child.id
            if called_name in functions:
                calls.add(called_name)
                continue
            runtime_value = vars(module).get(called_name)
            if (
                inspect.isfunction(runtime_value)
                and runtime_value.__module__ == module.__name__
                and runtime_value.__name__ in functions
            ):
                calls.add(runtime_value.__name__)
        pending.extend(sorted(calls - set(seen)))
    return tuple(seen)


def _reachable_source(module: ModuleType, root_name: str) -> str:
    return "\n".join(
        inspect.getsource(getattr(module, name))
        for name in _reachable_function_names(module, root_name)
    )


def _reachable_call_names(
    module: ModuleType,
    root_name: str,
) -> frozenset[str]:
    names: set[str] = set()
    for function_name in _reachable_function_names(module, root_name):
        node = _function_node(module, function_name)
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            function = child.func
            if isinstance(function, ast.Name):
                names.add(function.id)
            elif isinstance(function, ast.Attribute):
                parts = [function.attr]
                value = function.value
                while isinstance(value, ast.Attribute):
                    parts.append(value.attr)
                    value = value.value
                if isinstance(value, ast.Name):
                    parts.append(value.id)
                else:
                    parts.append("@dynamic")
                names.add(".".join(reversed(parts)))
    return frozenset(names)


def _function_source_sha256(path: str, name: str) -> str:
    raw = (_repository_root() / path).read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        ):
            source = "".join(lines[node.lineno - 1 : node.end_lineno])
            if not source.endswith("\n"):
                source += "\n"
            return hashlib.sha256(source.encode("utf-8")).hexdigest()
    raise AssertionError(f"missing frozen function: {path}::{name}")


def _function_closure_sha256(path: str, root_name: str) -> str:
    text = (_repository_root() / path).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert root_name in functions
    pending = [root_name]
    seen: list[str] = []
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.append(name)
        node = functions[name]
        callees = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in functions
        }
        pending.extend(sorted(callees - set(seen)))
    rows: list[dict[str, str]] = []
    for name in seen:
        node = functions[name]
        source = "".join(lines[node.lineno - 1 : node.end_lineno])
        if not source.endswith("\n"):
            source += "\n"
        rows.append(
            {
                "name": name,
                "source_sha256": hashlib.sha256(
                    source.encode("utf-8")
                ).hexdigest(),
            }
        )
    return _sha256_value(rows)


def _bound_names(node: ast.stmt) -> frozenset[str]:
    names: set[str] = set()

    def add_target(target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, (ast.List, ast.Tuple)):
            for item in target.elts:
                add_target(item)

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(node.name)
    elif isinstance(node, ast.Assign):
        for target in node.targets:
            add_target(target)
    elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
        add_target(node.target)
    elif isinstance(node, ast.Import):
        for alias in node.names:
            names.add(alias.asname or alias.name.partition(".")[0])
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            names.add(alias.asname or alias.name)
    return frozenset(names)


def _stable_semantic_value(
    value: Any,
    active_ids: frozenset[int] = frozenset(),
    repository_root: Path | None = None,
) -> Any:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        return {"type": "float", "value": repr(value)}
    if type(value) is bytes:
        return {"type": "bytes", "hex": value.hex()}
    value_id = id(value)
    assert value_id not in active_ids
    nested_ids = active_ids | {value_id}
    if type(value) in {list, tuple}:
        return {
            "type": type(value).__name__,
            "items": [
                _stable_semantic_value(
                    item,
                    nested_ids,
                    repository_root,
                )
                for item in value
            ],
        }
    if type(value) in {set, frozenset}:
        items = [
            _stable_semantic_value(item, nested_ids, repository_root)
            for item in value
        ]
        items.sort(key=_canonical_bytes)
        return {"type": type(value).__name__, "items": items}
    if type(value) is dict:
        items = [
            [
                _stable_semantic_value(key, nested_ids, repository_root),
                _stable_semantic_value(item, nested_ids, repository_root),
            ]
            for key, item in value.items()
        ]
        items.sort(key=lambda item: _canonical_bytes(item[0]))
        return {"type": "dict", "items": items}
    if isinstance(value, Path):
        if repository_root is not None:
            try:
                relative = value.resolve().relative_to(
                    repository_root.resolve()
                )
            except ValueError:
                pass
            else:
                return {
                    "type": (
                        f"{type(value).__module__}."
                        f"{type(value).__qualname__}"
                    ),
                    "repository_relative": relative.as_posix(),
                }
        return {
            "type": f"{type(value).__module__}.{type(value).__qualname__}",
            "value": str(value),
        }
    if isinstance(value, type):
        return {
            "type": "type",
            "module": value.__module__,
            "qualname": value.__qualname__,
        }
    if callable(value):
        return {
            "type": "callable",
            "module": getattr(value, "__module__", None),
            "qualname": getattr(value, "__qualname__", None),
        }
    rendered = repr(value)
    assert " at 0x" not in rendered
    return {
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        "repr": rendered,
    }


def _observable_module_state_value(
    value: Any,
    *,
    owned_module_names: frozenset[str],
    repository_root: Path,
    active_ids: frozenset[int] = frozenset(),
) -> Any:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        return {"type": "float", "value": float.hex(value)}
    if type(value) is bytes:
        return {"type": "bytes", "hex": value.hex()}
    if type(value) is bytearray:
        return {"type": "bytearray", "hex": bytes(value).hex()}

    value_type = type(value)
    type_identity = {
        "module": type.__getattribute__(value_type, "__module__"),
        "qualname": type.__getattribute__(value_type, "__qualname__"),
    }
    value_id = id(value)
    if value_id in active_ids:
        return {"cycle": type_identity}
    nested_ids = active_ids | {value_id}

    def nested(item: Any) -> Any:
        return _observable_module_state_value(
            item,
            owned_module_names=owned_module_names,
            repository_root=repository_root,
            active_ids=nested_ids,
        )

    def instance_attributes(item: Any) -> Any:
        try:
            attributes = object.__getattribute__(item, "__dict__")
        except AttributeError:
            return None
        assert type(attributes) is dict
        return [
            {"name": name, "value": nested(attribute)}
            for name, attribute in sorted(dict.items(attributes))
        ]

    if isinstance(value, ModuleType):
        module_bindings = ModuleType.__getattribute__(value, "__dict__")
        return {
            "type": "module",
            "name": dict.get(module_bindings, "__name__"),
            "file": dict.get(module_bindings, "__file__"),
        }
    if type(value) is FunctionType:
        module_name = object.__getattribute__(value, "__module__")
        identity = {
            "type": "function",
            "module": module_name,
            "name": object.__getattribute__(value, "__name__"),
            "qualname": object.__getattribute__(value, "__qualname__"),
            "firstlineno": object.__getattribute__(
                value,
                "__code__",
            ).co_firstlineno,
        }
        if module_name not in owned_module_names:
            return identity
        closure = object.__getattribute__(value, "__closure__")
        closure_state: list[Any] = []
        for cell in closure or ():
            try:
                cell_value = cell.cell_contents
            except ValueError:
                closure_state.append({"empty_cell": True})
            else:
                closure_state.append(nested(cell_value))
        return {
            **identity,
            "attributes": instance_attributes(value),
            "defaults": nested(
                object.__getattribute__(value, "__defaults__")
            ),
            "kwdefaults": nested(
                object.__getattribute__(value, "__kwdefaults__")
            ),
            "annotations": nested(
                object.__getattribute__(value, "__annotations__")
            ),
            "closure": closure_state,
        }
    if type(value) is MethodType:
        return {
            "type": "method",
            "function": nested(
                object.__getattribute__(value, "__func__")
            ),
            "self": nested(object.__getattribute__(value, "__self__")),
        }
    if isinstance(value, type):
        module_name = type.__getattribute__(value, "__module__")
        identity = {
            "type": "type",
            "module": module_name,
            "qualname": type.__getattribute__(value, "__qualname__"),
        }
        if module_name not in owned_module_names:
            return identity
        namespace = type.__getattribute__(value, "__dict__")
        return {
            **identity,
            "bases": [
                {
                    "module": type.__getattribute__(base, "__module__"),
                    "qualname": type.__getattribute__(base, "__qualname__"),
                }
                for base in type.__getattribute__(value, "__bases__")
            ],
            "namespace": [
                {"name": name, "value": nested(attribute)}
                for name, attribute in sorted(namespace.items())
                if name not in {"__dict__", "__weakref__"}
            ],
        }
    if type(value) is staticmethod:
        return {
            "type": "staticmethod",
            "function": nested(
                object.__getattribute__(value, "__func__")
            ),
        }
    if type(value) is classmethod:
        return {
            "type": "classmethod",
            "function": nested(
                object.__getattribute__(value, "__func__")
            ),
        }
    if type(value) is property:
        return {
            "type": "property",
            "get": nested(object.__getattribute__(value, "fget")),
            "set": nested(object.__getattribute__(value, "fset")),
            "delete": nested(object.__getattribute__(value, "fdel")),
            "doc": object.__getattribute__(value, "__doc__"),
        }
    if type(value) is partial:
        return {
            "type": "partial",
            "function": nested(
                object.__getattribute__(value, "func")
            ),
            "args": nested(object.__getattribute__(value, "args")),
            "keywords": nested(
                object.__getattribute__(value, "keywords")
            ),
            "attributes": instance_attributes(value),
        }
    if type(value) is GenericAlias:
        return {
            "type": "generic_alias",
            "origin": nested(
                object.__getattribute__(value, "__origin__")
            ),
            "args": nested(object.__getattribute__(value, "__args__")),
        }
    if type(value) is UnionType:
        return {
            "type": "union",
            "args": nested(object.__getattribute__(value, "__args__")),
        }
    if isinstance(value, Path):
        try:
            relative = value.resolve().relative_to(
                repository_root.resolve()
            )
        except ValueError:
            path_value = str(value)
        else:
            path_value = relative.as_posix()
        return {
            "type": type_identity,
            "path": path_value,
            "repository_relative": not Path(path_value).is_absolute(),
        }
    if isinstance(value, PurePath):
        return {
            "type": type_identity,
            "path": value.as_posix(),
        }
    if isinstance(value, re.Pattern):
        return {
            "type": type_identity,
            "pattern": value.pattern,
            "flags": value.flags,
        }
    if type_identity == {"module": "_abc", "qualname": "_abc_data"}:
        return {
            "type": type_identity,
            "managed_only_by_frozen_abc_class_surface": True,
        }
    if isinstance(value, dict):
        items = [
            [nested(key), nested(item)]
            for key, item in dict.items(value)
        ]
        return {
            "type": type_identity,
            "items": items,
            "attributes": instance_attributes(value),
        }
    if isinstance(value, list):
        return {
            "type": type_identity,
            "items": [nested(item) for item in list.__iter__(value)],
            "attributes": instance_attributes(value),
        }
    if isinstance(value, tuple):
        return {
            "type": type_identity,
            "items": [nested(item) for item in tuple.__iter__(value)],
            "attributes": instance_attributes(value),
        }
    if isinstance(value, set):
        items = [nested(item) for item in set.__iter__(value)]
        items.sort(key=_canonical_bytes)
        return {
            "type": type_identity,
            "items": items,
            "attributes": instance_attributes(value),
        }
    if isinstance(value, frozenset):
        items = [nested(item) for item in frozenset.__iter__(value)]
        items.sort(key=_canonical_bytes)
        return {
            "type": type_identity,
            "items": items,
            "attributes": instance_attributes(value),
        }
    attributes = instance_attributes(value)
    assert attributes is not None, (
        "opaque module-global state is not permitted: "
        f"{type_identity['module']}.{type_identity['qualname']}"
    )
    return {"type": type_identity, "attributes": attributes}


def _formal_owner_module_state_sha256(
    modules_by_path: Mapping[str, ModuleType],
    root: Path,
) -> str:
    assert set(modules_by_path) == set(_FORMAL_OWNER_PATHS)
    runtime_metadata_names = {"__builtins__"}
    owned_module_names = frozenset(
        ModuleType.__getattribute__(module, "__name__")
        for module in modules_by_path.values()
    )
    rows: list[dict[str, Any]] = []
    for path in sorted(modules_by_path):
        module = modules_by_path[path]
        assert type(module) is ModuleType
        bindings = ModuleType.__getattribute__(module, "__dict__")
        assert type(bindings) is dict
        rows.append(
            {
                "path": path,
                "bindings": [
                    {
                        "name": name,
                        "value": _observable_module_state_value(
                            value,
                            owned_module_names=owned_module_names,
                            repository_root=root,
                        ),
                    }
                    for name, value in sorted(dict.items(bindings))
                    if name not in runtime_metadata_names
                ],
            }
        )
    return _sha256_value(rows)


def _semantic_surface_sha256(
    path: str,
    root_names: tuple[str, ...],
) -> str:
    root = _repository_root()
    _preflight_formal_owner_import_closure(root)
    text = (root / path).read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    bindings: dict[str, list[ast.stmt]] = {}
    for statement in tree.body:
        for name in _bound_names(statement):
            bindings.setdefault(name, []).append(statement)
        if isinstance(
            statement,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue
        for child in ast.walk(statement):
            if (
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id
                in {
                    "compile",
                    "delattr",
                    "eval",
                    "exec",
                    "globals",
                    "locals",
                    "setattr",
                }
            ):
                raise AssertionError(
                    f"dynamic module rebinding forbidden: {path}"
                )
    pending = list(root_names)
    seen_names: set[str] = set()
    statement_rows: dict[tuple[int, int], dict[str, Any]] = {}
    import_rows: dict[tuple[int, str], dict[str, Any]] = {}
    while pending:
        name = pending.pop(0)
        if name in seen_names:
            continue
        seen_names.add(name)
        nodes = bindings.get(name)
        assert nodes is not None and len(nodes) == 1, f"{path}::{name}"
        node = nodes[0]
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            aliases = {
                alias.asname or (
                    alias.name.partition(".")[0]
                    if isinstance(node, ast.Import)
                    else alias.name
                ): alias
                for alias in node.names
            }
            alias = aliases[name]
            import_rows[(node.lineno, name)] = {
                "kind": type(node).__name__,
                "level": node.level if isinstance(node, ast.ImportFrom) else 0,
                "module": (
                    node.module if isinstance(node, ast.ImportFrom) else None
                ),
                "name": alias.name,
                "asname": alias.asname,
            }
            continue
        key = (node.lineno, node.end_lineno or node.lineno)
        if key not in statement_rows:
            source = "".join(lines[node.lineno - 1 : node.end_lineno])
            if not source.endswith("\n"):
                source += "\n"
            statement_rows[key] = {
                "kind": type(node).__name__,
                "bound_names": sorted(_bound_names(node)),
                "source_sha256": hashlib.sha256(
                    source.encode("utf-8")
                ).hexdigest(),
            }
        for child in ast.walk(node):
            if (
                isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
                and child.id in bindings
                and child.id not in seen_names
            ):
                pending.append(child.id)
    ordered_rows = [
        ((line, end_line, ""), row)
        for (line, end_line), row in statement_rows.items()
    ]
    ordered_rows.extend(
        ((line, line, name), row)
        for (line, name), row in import_rows.items()
    )
    ordered_rows.sort(key=lambda item: item[0])
    root = _repository_root()
    _prepare_imports(root)
    module = importlib.import_module(Path(path).stem)
    runtime_rows = []
    for name in sorted(seen_names):
        node = bindings[name][0]
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            runtime_rows.append(
                {
                    "binding": name,
                    "runtime_value": _stable_semantic_value(
                        getattr(module, name)
                    ),
                }
            )
    return _sha256_value(
        {
            "source_rows": [row for _, row in ordered_rows],
            "runtime_rows": runtime_rows,
        }
    )


def _cross_module_semantic_surface_sha256(
    roots_by_path: Mapping[str, tuple[str, ...]],
) -> str:
    root = _repository_root()
    _prepare_imports(root)
    _preflight_formal_owner_import_closure(root)
    local_module_paths: dict[str, str] = {}
    for directory in (
        root / "ai" / "services" / "ai_inference",
        root / "ai" / "tools",
    ):
        for source_path in sorted(directory.glob("*.py")):
            module_name = source_path.stem
            relative_path = source_path.relative_to(root).as_posix()
            assert module_name not in local_module_paths
            local_module_paths[module_name] = relative_path

    module_cache: dict[
        str,
        tuple[
            str,
            list[str],
            ast.Module,
            dict[str, list[ast.stmt]],
            ModuleType,
        ],
    ] = {}

    def load_module(
        path: str,
    ) -> tuple[
        str,
        list[str],
        ast.Module,
        dict[str, list[ast.stmt]],
        ModuleType,
    ]:
        cached = module_cache.get(path)
        if cached is not None:
            return cached
        source_path = (root / path).resolve()
        text = source_path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        tree = ast.parse(text)
        bindings: dict[str, list[ast.stmt]] = {}
        for statement in tree.body:
            assert not isinstance(statement, ast.Delete)
            for name in _bound_names(statement):
                bindings.setdefault(name, []).append(statement)
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue
            for child in ast.walk(statement):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                    and child.func.id
                    in {
                        "compile",
                        "delattr",
                        "eval",
                        "exec",
                        "globals",
                        "locals",
                        "setattr",
                    }
                ):
                    raise AssertionError(
                        f"dynamic module rebinding forbidden: {path}"
                    )
        module = importlib.import_module(source_path.stem)
        assert Path(inspect.getsourcefile(module) or "").resolve() == (
            source_path
        )
        cached = (text, lines, tree, bindings, module)
        module_cache[path] = cached
        return cached

    def local_target_path(module_name: str | None) -> str | None:
        if not module_name:
            return None
        return local_module_paths.get(module_name.rsplit(".", 1)[-1])

    def alias_binding(
        node: ast.Import | ast.ImportFrom,
        name: str,
    ) -> ast.alias:
        for alias in node.names:
            bound = alias.asname or (
                alias.name.partition(".")[0]
                if isinstance(node, ast.Import)
                else alias.name
            )
            if bound == name:
                return alias
        raise AssertionError(f"missing import binding: {name}")

    pending = sorted(
        (path, name)
        for path, names in roots_by_path.items()
        for name in names
    )
    seen: set[tuple[str, str]] = set()
    rows: list[dict[str, Any]] = []
    while pending:
        path, name = pending.pop(0)
        identity = (path, name)
        if identity in seen:
            continue
        seen.add(identity)
        _, lines, _, bindings, module = load_module(path)
        nodes = bindings.get(name)
        assert nodes is not None and len(nodes) == 1, f"{path}::{name}"
        node = nodes[0]
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            alias = alias_binding(node, name)
            target_path = local_target_path(
                node.module
                if isinstance(node, ast.ImportFrom)
                else alias.name
            )
            row: dict[str, Any] = {
                "path": path,
                "binding": name,
                "kind": type(node).__name__,
                "level": (
                    node.level if isinstance(node, ast.ImportFrom) else 0
                ),
                "module": (
                    node.module if isinstance(node, ast.ImportFrom) else None
                ),
                "name": alias.name,
                "asname": alias.asname,
                "local_target_path": target_path,
            }
            runtime_value = getattr(module, name)
            if isinstance(runtime_value, ModuleType):
                row["runtime_binding"] = {
                    "type": "module",
                    "name": runtime_value.__name__,
                }
            else:
                row["runtime_binding"] = _stable_semantic_value(
                    runtime_value,
                    repository_root=root,
                )
            if target_path is not None and isinstance(node, ast.ImportFrom):
                assert alias.name != "*"
                target_name = alias.name
                target_module = load_module(target_path)[4]
                assert runtime_value is getattr(target_module, target_name)
                row["local_target_binding"] = target_name
                pending.append((target_path, target_name))
            rows.append(row)
            continue

        decorator_lines = [
            decorator.lineno
            for decorator in getattr(node, "decorator_list", ())
        ]
        start_line = min([node.lineno, *decorator_lines])
        end_line = node.end_lineno or node.lineno
        source = "".join(lines[start_line - 1 : end_line])
        if not source.endswith("\n"):
            source += "\n"
        runtime_value = getattr(module, name)
        row = {
            "path": path,
            "binding": name,
            "kind": type(node).__name__,
            "bound_names": sorted(_bound_names(node)),
            "source_sha256": hashlib.sha256(
                source.encode("utf-8")
            ).hexdigest(),
        }
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert inspect.isfunction(runtime_value)
            assert runtime_value.__name__ == name
            assert runtime_value.__module__ == module.__name__
            assert Path(
                inspect.getsourcefile(runtime_value) or ""
            ).resolve() == (root / path).resolve()
            assert runtime_value.__code__.co_firstlineno == node.lineno
            row["runtime_binding"] = {
                "type": "function",
                "module": runtime_value.__module__,
                "qualname": runtime_value.__qualname__,
                "firstlineno": runtime_value.__code__.co_firstlineno,
            }
        elif isinstance(node, ast.ClassDef):
            assert inspect.isclass(runtime_value)
            assert runtime_value.__name__ == name
            assert runtime_value.__module__ == module.__name__
            row["runtime_binding"] = {
                "type": "class",
                "module": runtime_value.__module__,
                "qualname": runtime_value.__qualname__,
            }
        else:
            row["runtime_binding"] = _stable_semantic_value(
                runtime_value,
                repository_root=root,
            )
        rows.append(row)

        for child in ast.walk(node):
            if (
                isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
                and child.id in bindings
                and (path, child.id) not in seen
            ):
                pending.append((path, child.id))
            if isinstance(child, ast.ImportFrom):
                target_path = local_target_path(child.module)
                if target_path is not None:
                    for alias in child.names:
                        assert alias.name != "*"
                        pending.append((target_path, alias.name))
            if isinstance(child, ast.Attribute):
                base = child.value
                if not isinstance(base, ast.Name):
                    continue
                import_nodes = bindings.get(base.id)
                if import_nodes is None or len(import_nodes) != 1:
                    continue
                import_node = import_nodes[0]
                if not isinstance(import_node, ast.Import):
                    continue
                alias = alias_binding(import_node, base.id)
                target_path = local_target_path(alias.name)
                if target_path is not None:
                    pending.append((target_path, child.attr))

    rows.sort(
        key=lambda row: (
            row["path"],
            row["binding"],
            row["kind"],
        )
    )
    return _sha256_value(rows)


def _assert_runtime_function_bindings(
    path: str,
    root_names: tuple[str, ...],
) -> None:
    root = _repository_root()
    _prepare_imports(root)
    _preflight_formal_owner_import_closure(root)
    module = importlib.import_module(Path(path).stem)
    source_path = (root / path).resolve()
    text = source_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    pending = list(root_names)
    seen: set[str] = set()
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.add(name)
        assert name in functions
        assert sum(name in _bound_names(node) for node in tree.body) == 1
        node = functions[name]
        value = getattr(module, name)
        assert inspect.isfunction(value)
        assert value.__name__ == name
        assert value.__module__ == module.__name__
        assert Path(inspect.getsourcefile(value) or "").resolve() == source_path
        assert value.__code__.co_firstlineno == node.lineno
        callees = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in functions
        }
        pending.extend(sorted(callees - seen))


def _assert_public_signature(api: Callable[..., Any]) -> None:
    signature = inspect.signature(api)
    assert tuple(signature.parameters) == ("state",)
    parameter = signature.parameters["state"]
    assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameter.default is inspect.Parameter.empty


def _schema_probe(
    *,
    event_schema: str,
    admission_schema: str,
    candidate_schema: str = _CANDIDATE_SCHEMA_V1,
    source_schema: str = _SOURCE_CLOSURE_SCHEMA_V1,
    bootstrap_schema: str = _BOOTSTRAP_CLOSURE_SCHEMA_V1,
    extras: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "event1": {
            "schema_version": event_schema,
            "candidate_allocation": {
                "schema_version": candidate_schema,
            },
            "source_closure": {"schema_version": source_schema},
            "bootstrap_closure": {"schema_version": bootstrap_schema},
            "authority": {
                "operational_admission": {
                    "schema_version": admission_schema,
                }
            },
        },
        "automatic_progression": False,
    }
    if extras:
        state.update(copy.deepcopy(dict(extras)))
    return state


def _assert_module_actual_git_identity(
    api: Callable[..., Any],
    path: str,
) -> None:
    root = _repository_root()
    origin = Path(
        inspect.getsourcefile(inspect.unwrap(api)) or ""
    ).resolve()
    assert origin == (root / path).resolve()
    blob = _git(root, "rev-parse", f"HEAD:{path}")
    raw = _git_bytes(root, "show", f"HEAD:{path}")
    assert hashlib.sha256(raw).hexdigest() == hashlib.sha256(
        origin.read_bytes()
    ).hexdigest()
    assert blob == _git(root, "hash-object", path)


def _assert_executor_actual_git_identity(
    executor: Mapping[str, Any],
    *,
    api: Callable[..., Any],
    path: str,
) -> None:
    root = _repository_root(require_current_clean=True)
    origin = Path(
        inspect.getsourcefile(inspect.unwrap(api)) or ""
    ).resolve()
    raw = _git_bytes(root, "show", f"HEAD:{path}")
    assert set(executor) == _EXECUTOR_KEYS
    assert executor["repository_full_name"] == "MassyuRed/mashos-api"
    assert executor["source_ref"] == "refs/heads/main"
    assert executor["repository_root"] == str(root)
    assert executor["head_commit_sha1"] == _git(root, "rev-parse", "HEAD")
    assert executor["head_tree_sha1"] == _git(
        root,
        "rev-parse",
        "HEAD^{tree}",
    )
    assert executor["origin_main_commit_sha1"] == _git(
        root,
        "rev-parse",
        "origin/main",
    )
    assert executor["worktree_clean"] is True
    assert executor["module_path"] == path
    assert executor["module_origin"] == str(origin)
    assert executor["git_blob_sha1"] == _git(
        root,
        "rev-parse",
        f"HEAD:{path}",
    )
    assert executor["raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert origin.read_bytes() == raw


def _module_imports_name(
    module: ModuleType,
    *,
    imported_module: str,
    imported_name: str | None = None,
) -> bool:
    source = Path(inspect.getsourcefile(module) or "").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    matches: list[ast.alias] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            if imported_name is None:
                matches.extend(
                    alias
                    for alias in node.names
                    if alias.name == imported_module
                )
        elif isinstance(node, ast.ImportFrom):
            if node.module != imported_module:
                continue
            if imported_name is None:
                matches.extend(node.names)
            else:
                matches.extend(
                    alias
                    for alias in node.names
                    if alias.name == imported_name
                )
    if imported_name is None:
        return bool(matches)
    return len(matches) == 1 and matches[0].asname is None


def _dotted_ast_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_ast_name(node.value)
        if prefix is not None:
            return f"{prefix}.{node.attr}"
    return None


def _assert_independent_owner_boundary(module: ModuleType) -> None:
    root = _repository_root()
    source_path = Path(inspect.getsourcefile(module) or "").resolve()
    assert source_path == (
        root / _MANDATORY_DIRECT_PATHS["independent"]
    ).resolve()
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    local_module_paths = {
        path.stem: path.resolve()
        for directory in (
            root / "ai" / "services" / "ai_inference",
            root / "ai" / "tools",
        )
        for path in directory.glob("*.py")
    }
    allowed_local_imports = {
        _MODULE_NAMES["contract"]: {
            "artifact_sha256",
            "canonical_json_bytes",
            "load_canonical_json_bytes",
        },
    }
    imported_module_bindings = {
        alias.asname or alias.name.partition(".")[0]
        for statement in tree.body
        if isinstance(statement, ast.Import)
        for alias in statement.names
    }
    declared_import_bindings = frozenset(
        set(imported_module_bindings)
        | {
            alias.asname or alias.name
            for statement in tree.body
            if isinstance(statement, ast.ImportFrom)
            for alias in statement.names
            if alias.name != "*"
        }
    )
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            source_name: str | None = None
            targets: tuple[ast.AST, ...] = ()
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
                if isinstance(node.value, ast.Name):
                    source_name = node.value.id
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
                targets = (node.target,)
                if isinstance(node.value, ast.Name):
                    source_name = node.value.id
            if source_name not in imported_module_bindings:
                continue
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id not in imported_module_bindings
                ):
                    imported_module_bindings.add(target.id)
                    changed = True
    forbidden_bridge_modules = {
        "builtins",
        "functools",
        "gc",
        "importlib",
        "inspect",
        "operator",
        "pydoc",
        "pkgutil",
        "runpy",
    }
    forbidden_bridge_attributes = {
        "__base__",
        "__bases__",
        "__builtins__",
        "__class__",
        "__closure__",
        "__code__",
        "__defaults__",
        "__dict__",
        "__kwdefaults__",
        "__annotations__",
        "__doc__",
        "__func__",
        "__globals__",
        "__getattribute__",
        "__module__",
        "__name__",
        "__qualname__",
        "__mro__",
        "__subclasses__",
        "__traceback__",
        "ag_frame",
        "cell_contents",
        "cr_frame",
        "_getframe",
        "_module",
        "f_back",
        "f_builtins",
        "f_code",
        "f_globals",
        "f_locals",
        "gi_frame",
        "locate",
        "modules",
        "tb_frame",
        "tb_next",
    }
    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    allowed_sys_attributes = {
        "executable",
        "stdlib_module_names",
    }

    def mutation_targets(node: ast.AST) -> tuple[ast.AST, ...]:
        if isinstance(node, ast.Assign):
            return tuple(node.targets)
        if isinstance(
            node,
            (ast.AnnAssign, ast.AugAssign, ast.NamedExpr),
        ):
            return (node.target,)
        if isinstance(node, (ast.For, ast.AsyncFor)):
            return (node.target,)
        if isinstance(node, (ast.With, ast.AsyncWith)):
            return tuple(
                item.optional_vars
                for item in node.items
                if item.optional_vars is not None
            )
        if isinstance(node, ast.comprehension):
            return (node.target,)
        if isinstance(node, ast.Delete):
            return tuple(node.targets)
        return ()

    def mutation_target_leaves(
        target: ast.AST,
    ) -> tuple[ast.AST, ...]:
        if isinstance(target, (ast.Tuple, ast.List)):
            return tuple(
                leaf
                for element in target.elts
                for leaf in mutation_target_leaves(element)
            )
        if isinstance(target, ast.Starred):
            return mutation_target_leaves(target.value)
        return (target,)

    def target_root_name(node: ast.AST) -> str | None:
        value = node
        while isinstance(value, (ast.Attribute, ast.Subscript)):
            value = value.value
        return value.id if isinstance(value, ast.Name) else None

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id not in {
                "__builtins__",
                "__import__",
                "compile",
                "eval",
                "exec",
                "globals",
                "locals",
                "open",
            }
            if (
                isinstance(node.ctx, ast.Load)
                and node.id
                in {
                    "delattr",
                    "getattr",
                    "setattr",
                    "vars",
                }
            ):
                parent = parents.get(node)
                assert isinstance(parent, ast.Call)
                assert parent.func is node
            if (
                isinstance(node.ctx, ast.Load)
                and node.id in imported_module_bindings
            ):
                parent = parents.get(node)
                allowed_attribute_base = (
                    isinstance(parent, ast.Attribute)
                    and parent.value is node
                )
                allowed_literal_getattr = (
                    isinstance(parent, ast.Call)
                    and isinstance(parent.func, ast.Name)
                    and parent.func.id == "getattr"
                    and bool(parent.args)
                    and parent.args[0] is node
                    and len(parent.args) >= 2
                    and isinstance(parent.args[1], ast.Constant)
                    and isinstance(parent.args[1].value, str)
                )
                assert allowed_attribute_base or allowed_literal_getattr
        if isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_bridge_attributes
            dotted = _dotted_ast_name(node)
            if dotted is not None and dotted.startswith("sys."):
                sys_attribute = dotted.split(".", 2)[1]
                assert sys_attribute in allowed_sys_attributes
        if isinstance(node, ast.Subscript):
            subscripted_name = _dotted_ast_name(node.value)
            assert subscripted_name not in {
                "__builtins__",
                "sys.modules",
            }
        for target in mutation_targets(node):
            for leaf in mutation_target_leaves(target):
                if isinstance(leaf, ast.Name):
                    assert leaf.id not in declared_import_bindings
                if isinstance(leaf, (ast.Attribute, ast.Subscript)):
                    assert (
                        target_root_name(leaf)
                        not in imported_module_bindings
                    )
        if isinstance(node, ast.Call):
            call_name = _dotted_ast_name(node.func)
            if call_name is not None:
                tail = call_name.rsplit(".", 1)[-1]
                assert call_name not in _FORBIDDEN_OWNER_TRUST_CALL_NAMES
                assert tail not in _FORBIDDEN_OWNER_TRUST_CALL_TAILS
                assert call_name not in {
                    "__import__",
                    "compile",
                    "delattr",
                    "eval",
                    "exec",
                    "globals",
                    "locals",
                    "setattr",
                    "vars",
                }
            assert not isinstance(node.func, ast.Subscript)
            if (
                isinstance(node.func, ast.Name)
                and node.func.id == "getattr"
            ):
                assert len(node.args) >= 2
                assert isinstance(node.args[1], ast.Constant)
                assert isinstance(node.args[1].value, str)
                assert node.args[1].value not in {
                    _OWNER_API,
                    *_FORBIDDEN_OWNER_TRUST_CALL_TAILS,
                    *forbidden_bridge_attributes,
                }
                if (
                    isinstance(node.args[0], ast.Name)
                    and node.args[0].id == "sys"
                ):
                    assert (
                        node.args[1].value in allowed_sys_attributes
                    )
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if value is None:
                continue
            alias_name = _dotted_ast_name(value)
            if alias_name is not None:
                tail = alias_name.rsplit(".", 1)[-1]
                assert (
                    alias_name not in _FORBIDDEN_OWNER_TRUST_CALL_NAMES
                )
                assert tail not in _FORBIDDEN_OWNER_TRUST_CALL_TAILS
    for node in ast.walk(tree):
        imported: list[tuple[str, set[str] | None]] = []
        if isinstance(node, ast.Import):
            assert not any(
                alias.name.partition(".")[0]
                in forbidden_bridge_modules
                for alias in node.names
            )
            imported.extend((alias.name, None) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert (
                node.module.partition(".")[0]
                not in forbidden_bridge_modules | {"sys"}
            )
            imported.append(
                (
                    node.module,
                    {alias.name for alias in node.names},
                )
            )
        for imported_module, imported_names in imported:
            local_name = imported_module.rsplit(".", 1)[-1]
            if local_name not in local_module_paths:
                continue
            assert local_name in allowed_local_imports
            if imported_names is not None:
                assert imported_names <= allowed_local_imports[local_name]


def _assert_no_owner_runtime_references(module: ModuleType) -> None:
    owner_module_name = _MODULE_NAMES["sequence"]
    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    import_expectations: dict[str, set[str]] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                binding = alias.asname or alias.name.partition(".")[0]
                expected = (
                    alias.name
                    if alias.asname
                    else alias.name.partition(".")[0]
                )
                import_expectations.setdefault(binding, set()).add(expected)
        elif isinstance(statement, ast.ImportFrom) and statement.module:
            for alias in statement.names:
                if alias.name == "*":
                    continue
                binding = alias.asname or alias.name
                import_expectations.setdefault(binding, set()).add(
                    f"{statement.module}.{alias.name}"
                )
    import_bindings = set(import_expectations)
    imported_module_ids = {
        id(vars(module)[name])
        for name in import_bindings
        if isinstance(vars(module).get(name), ModuleType)
    }
    seen: set[int] = set()

    def visit(value: Any) -> None:
        value_id = id(value)
        if value_id in seen:
            return
        seen.add(value_id)
        if isinstance(value, ModuleType):
            assert type(value) is ModuleType
            assert value.__name__.rsplit(".", 1)[-1] != owner_module_name
            if value_id in imported_module_ids:
                matching_bindings = {
                    name
                    for name in import_bindings
                    if vars(module).get(name) is value
                }
                assert matching_bindings
                assert any(
                    value.__name__ in import_expectations[name]
                    for name in matching_bindings
                )
            else:
                for name, item in vars(value).items():
                    if not name.startswith("__"):
                        visit(item)
            return
        if inspect.isfunction(value):
            assert value.__module__.rsplit(".", 1)[-1] != owner_module_name
            if value.__module__ != module.__name__:
                return
            for item in value.__defaults__ or ():
                visit(item)
            for item in (value.__kwdefaults__ or {}).values():
                visit(item)
            for cell in value.__closure__ or ():
                visit(cell.cell_contents)
            for item in vars(value).values():
                visit(item)
            return
        if inspect.ismethod(value):
            visit(value.__func__)
            visit(value.__self__)
            return
        if isinstance(value, dict):
            items = dict.items(value)
            for item in items:
                visit(item)
            return
        if type(value) in {list, tuple, set, frozenset, deque}:
            for item in value:
                visit(item)
            return
        assert not isinstance(value, IteratorABC)
        if type(value) is partial:
            visit(value.func)
            visit(value.args)
            visit(value.keywords or {})
            return
        if type(value) is property:
            for accessor in (value.fget, value.fset, value.fdel):
                if (
                    inspect.isfunction(accessor)
                    and accessor.__module__ == module.__name__
                ):
                    _assert_no_effect_sink_calls(
                        module,
                        accessor.__name__,
                    )
            visit(value.fget)
            visit(value.fset)
            visit(value.fdel)
            return
        if isinstance(value, type) and value.__module__ == module.__name__:
            for item in type.__getattribute__(value, "__dict__").values():
                visit(item)
            return
        wrapped = inspect.getattr_static(value, "__wrapped__", None)
        if wrapped is not None:
            visit(wrapped)
        if (
            not isinstance(value, type)
            and type(value).__module__ == module.__name__
        ):
            try:
                instance_dict = object.__getattribute__(
                    value,
                    "__dict__",
                )
            except AttributeError:
                instance_dict = None
            if instance_dict is not None:
                assert type(instance_dict) is dict
                for item in dict.values(instance_dict):
                    visit(item)

    for name, value in vars(module).items():
        if not name.startswith("__"):
            visit(value)


def _assert_no_effect_aliases(module_or_path: ModuleType | Path) -> None:
    source_path = (
        Path(inspect.getsourcefile(module_or_path) or "")
        if isinstance(module_or_path, ModuleType)
        else module_or_path
    )
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_from_imports = {
        "builtins": {
            "__import__",
            "compile",
            "eval",
            "exec",
            "open",
        },
        "importlib": {"import_module", "reload"},
        "importlib.machinery": {
            "SourceFileLoader",
            "SourcelessFileLoader",
        },
        "importlib.util": {
            "module_from_spec",
            "spec_from_file_location",
        },
        "io": {"open"},
        "operator": {"attrgetter", "methodcaller"},
        "os": {
            "_exit",
            "chdir",
            "chmod",
            "chown",
            "chroot",
            "execl",
            "execle",
            "execlp",
            "execlpe",
            "execv",
            "execve",
            "execvp",
            "execvpe",
            "fdopen",
            "fchmod",
            "fchown",
            "fork",
            "forkpty",
            "fsync",
            "ftruncate",
            "link",
            "lchmod",
            "lchown",
            "kill",
            "killpg",
            "makedirs",
            "mkdir",
            "mkfifo",
            "mknod",
            "open",
            "popen",
            "posix_spawn",
            "posix_spawnp",
            "putenv",
            "remove",
            "removedirs",
            "rename",
            "renames",
            "replace",
            "rmdir",
            "spawnl",
            "spawnle",
            "spawnlp",
            "spawnlpe",
            "spawnv",
            "spawnve",
            "spawnvp",
            "spawnvpe",
            "setegid",
            "seteuid",
            "setgid",
            "setgroups",
            "setregid",
            "setresgid",
            "setresuid",
            "setreuid",
            "setuid",
            "symlink",
            "sync",
            "system",
            "truncate",
            "umask",
            "unlink",
            "unsetenv",
            "utime",
            "write",
        },
        "runpy": {"run_module", "run_path"},
        "shutil": {
            "copy",
            "copy2",
            "copyfile",
            "copytree",
            "move",
            "rmtree",
        },
        "subprocess": {
            "Popen",
            "call",
            "check_call",
            "check_output",
            "getoutput",
            "getstatusoutput",
            "run",
        },
    }
    forbidden_attributes = {
        f"{module_name}.{name}"
        for module_name, names in forbidden_from_imports.items()
        for name in names
    }
    forbidden_attributes.update(
        {
            "os.environ",
            "Path.mkdir",
            "Path.chmod",
            "Path.hardlink_to",
            "Path.link_to",
            "Path.open",
            "Path.rename",
            "Path.replace",
            "Path.rmdir",
            "Path.symlink_to",
            "Path.touch",
            "Path.unlink",
            "Path.write_bytes",
            "Path.write_text",
        }
    )
    forbidden_alias_tails = {
        attribute.rsplit(".", 1)[-1]
        for attribute in forbidden_attributes
    }
    forbidden_reflection_tails = {
        "__base__",
        "__bases__",
        "__builtins__",
        "__class__",
        "__closure__",
        "__code__",
        "__defaults__",
        "__dict__",
        "__kwdefaults__",
        "__annotations__",
        "__doc__",
        "__func__",
        "__globals__",
        "__getattribute__",
        "__module__",
        "__setattr__",
        "__name__",
        "__qualname__",
        "__mro__",
        "__subclasses__",
        "__traceback__",
        "_getframe",
        "_module",
        "ag_frame",
        "attrgetter",
        "cell_contents",
        "cr_frame",
        "delattr",
        "f_back",
        "f_builtins",
        "f_code",
        "f_globals",
        "f_locals",
        "gi_frame",
        "methodcaller",
        "modules",
        "setattr",
        "tb_frame",
        "tb_next",
        "vars",
    }
    module_aliases = {
        alias.asname or alias.name.partition(".")[0]: alias.name
        for statement in tree.body
        if isinstance(statement, ast.Import)
        for alias in statement.names
    }
    declared_import_bindings = frozenset(
        {
            alias.asname or alias.name.partition(".")[0]
            for statement in tree.body
            if isinstance(statement, ast.Import)
            for alias in statement.names
        }
        | {
            alias.asname or alias.name
            for statement in tree.body
            if isinstance(statement, ast.ImportFrom)
            for alias in statement.names
            if alias.name != "*"
        }
    )
    module_object_aliases = set(module_aliases)
    for statement in tree.body:
        if (
            isinstance(statement, ast.ImportFrom)
            and statement.module == "pathlib"
        ):
            for alias in statement.names:
                if alias.name == "Path":
                    module_aliases[alias.asname or alias.name] = "Path"
        if (
            isinstance(statement, ast.ImportFrom)
            and statement.module == "importlib"
        ):
            for alias in statement.names:
                if alias.name == "metadata":
                    binding = alias.asname or alias.name
                    module_aliases[binding] = "importlib.metadata"
                    module_object_aliases.add(binding)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            source_name: str | None = None
            targets: tuple[ast.AST, ...] = ()
            if isinstance(node, ast.Assign):
                targets = tuple(node.targets)
                if isinstance(node.value, ast.Name):
                    source_name = node.value.id
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
                targets = (node.target,)
                if isinstance(node.value, ast.Name):
                    source_name = node.value.id
            if source_name not in module_aliases:
                continue
            for target in targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id not in module_aliases
                ):
                    module_aliases[target.id] = module_aliases[source_name]
                    if source_name in module_object_aliases:
                        module_object_aliases.add(target.id)
                    changed = True

    def normalized_dotted_name(node: ast.AST) -> str | None:
        dotted = _dotted_ast_name(node)
        if dotted is None:
            return None
        root_name, separator, suffix = dotted.partition(".")
        canonical_root = module_aliases.get(root_name, root_name)
        return (
            f"{canonical_root}.{suffix}"
            if separator
            else canonical_root
        )

    def mutation_targets(node: ast.AST) -> tuple[ast.AST, ...]:
        if isinstance(node, ast.Assign):
            return tuple(node.targets)
        if isinstance(
            node,
            (ast.AnnAssign, ast.AugAssign, ast.NamedExpr),
        ):
            return (node.target,)
        if isinstance(node, (ast.For, ast.AsyncFor)):
            return (node.target,)
        if isinstance(node, (ast.With, ast.AsyncWith)):
            return tuple(
                item.optional_vars
                for item in node.items
                if item.optional_vars is not None
            )
        if isinstance(node, ast.comprehension):
            return (node.target,)
        if isinstance(node, ast.Delete):
            return tuple(node.targets)
        return ()

    def mutation_target_leaves(
        target: ast.AST,
    ) -> tuple[ast.AST, ...]:
        if isinstance(target, (ast.Tuple, ast.List)):
            return tuple(
                leaf
                for element in target.elts
                for leaf in mutation_target_leaves(element)
            )
        if isinstance(target, ast.Starred):
            return mutation_target_leaves(target.value)
        return (target,)

    def target_root_name(node: ast.AST) -> str | None:
        value = node
        while isinstance(value, (ast.Attribute, ast.Subscript)):
            value = value.value
        return value.id if isinstance(value, ast.Name) else None

    def assert_literal_getattr_safe(node: ast.Call) -> None:
        call_name = _dotted_ast_name(node.func)
        if (
            not isinstance(node.func, ast.Name)
            or node.func.id != "getattr"
        ) and (
            call_name is None
            or call_name.rsplit(".", 1)[-1] != "getattr"
        ):
            return
        assert len(node.args) >= 2
        assert isinstance(node.args[1], ast.Constant)
        assert isinstance(node.args[1].value, str)
        assert node.args[1].value not in (
            forbidden_alias_tails | forbidden_reflection_tails
        )
        target_name = normalized_dotted_name(node.args[0])
        if target_name is not None:
            assert (
                f"{target_name}.{node.args[1].value}"
                not in forbidden_attributes
            )

    def assert_binding_expression_safe(expression: ast.AST | None) -> None:
        if expression is None:
            return

        def visit(node: ast.AST) -> None:
            if isinstance(node, ast.Call):
                assert_literal_getattr_safe(node)
                call_name = _dotted_ast_name(node.func)
                if call_name is not None:
                    assert (
                        call_name.rsplit(".", 1)[-1]
                        not in forbidden_reflection_tails
                    )
                else:
                    visit(node.func)
                for argument in node.args:
                    visit(argument)
                for keyword in node.keywords:
                    visit(keyword.value)
                return
            alias_name = _dotted_ast_name(node)
            if alias_name is not None:
                tail = alias_name.rsplit(".", 1)[-1]
                if isinstance(node, ast.Name):
                    assert alias_name not in {
                        "__import__",
                        "compile",
                        "eval",
                        "exec",
                        "open",
                    }
                else:
                    assert alias_name not in forbidden_attributes
                    assert tail not in forbidden_alias_tails
                    assert tail not in forbidden_reflection_tails
                return
            for child in ast.iter_child_nodes(node):
                visit(child)

        visit(expression)

    def assert_binding_time_calls_safe(expression: ast.AST | None) -> None:
        if expression is None:
            return
        assert not any(
            isinstance(child, ast.NamedExpr)
            for child in ast.walk(expression)
        )
        assert not any(
            isinstance(child, ast.Call)
            for child in ast.walk(expression)
        )
        for child in ast.walk(expression):
            if not isinstance(child, ast.Call):
                continue
            call_name = _dotted_ast_name(child.func)
            if call_name is not None:
                tail = call_name.rsplit(".", 1)[-1]
                assert call_name not in forbidden_attributes
                assert call_name not in {
                    "__import__",
                    "compile",
                    "eval",
                    "exec",
                    "open",
                    "vars",
                }
                assert tail not in _FORBIDDEN_EFFECT_CALL_TAILS
                assert tail not in forbidden_reflection_tails
            assert_literal_getattr_safe(child)

    parents = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    forbidden_network_roots = {
        "asyncio",
        "builtins",
        "cffi",
        "cloudpickle",
        "ctypes",
        "dill",
        "ftplib",
        "functools",
        "http.client",
        "httpx",
        "imaplib",
        "itertools",
        "marshal",
        "multiprocessing",
        "operator",
        "pickle",
        "pkgutil",
        "poplib",
        "pydoc",
        "requests",
        "runpy",
        "shelve",
        "smtplib",
        "socket",
        "socketserver",
        "ssl",
        "telnetlib",
        "tempfile",
        "threading",
        "urllib",
        "webbrowser",
    }
    allowed_import_roots = {
        "__future__",
        "argparse",
        "ast",
        "base64",
        "copy",
        "csv",
        "datetime",
        "email",
        "hashlib",
        "importlib",
        "json",
        "math",
        "os",
        "packaging",
        "pathlib",
        "platform",
        "pytest",
        "re",
        "secrets",
        "shutil",
        "stat",
        "subprocess",
        "sys",
        "typing",
        "unicodedata",
        "zipfile",
    }
    source_relative = source_path.resolve().relative_to(
        _repository_root().resolve()
    ).as_posix()
    import_surface: list[dict[str, Any]] = []
    for imported_node in ast.walk(tree):
        if isinstance(imported_node, ast.Import):
            import_surface.append(
                {
                    "kind": "import",
                    "module": "",
                    "level": 0,
                    "names": sorted(
                        (
                            {
                                "name": alias.name,
                                "asname": alias.asname or "",
                            }
                            for alias in imported_node.names
                        ),
                        key=lambda row: (row["name"], row["asname"]),
                    ),
                }
            )
        elif isinstance(imported_node, ast.ImportFrom):
            import_surface.append(
                {
                    "kind": "from",
                    "module": imported_node.module or "",
                    "level": imported_node.level,
                    "names": sorted(
                        (
                            {
                                "name": alias.name,
                                "asname": alias.asname or "",
                            }
                            for alias in imported_node.names
                        ),
                        key=lambda row: (row["name"], row["asname"]),
                    ),
                }
            )
    import_surface.sort(
        key=lambda row: (
            row["kind"],
            row["module"],
            row["level"],
            _canonical_bytes(row["names"]),
        )
    )
    expected_import_surface = _FROZEN_IMPORT_SURFACE_SHA256[
        source_relative
    ]
    allowed_import_surface_hashes = (
        expected_import_surface
        if isinstance(expected_import_surface, tuple)
        else (expected_import_surface,)
    )
    assert _sha256_value(import_surface) in allowed_import_surface_hashes
    observed_class_nodes = [
        class_node
        for class_node in ast.walk(tree)
        if isinstance(class_node, ast.ClassDef)
    ]
    observed_class_names = [
        class_node.name for class_node in observed_class_nodes
    ]
    assert len(observed_class_names) == len(set(observed_class_names))
    module_level_bindings = _module_level_bindings(tree)
    for class_node in observed_class_nodes:
        assert not class_node.decorator_list
        assert not class_node.keywords
        assert module_level_bindings.get(class_node.name) == [class_node]
    observed_class_hashes = {
        class_node.name: hashlib.sha256(
            ast.dump(
                class_node,
                annotate_fields=True,
                include_attributes=False,
            ).encode("utf-8")
        ).hexdigest()
        for class_node in observed_class_nodes
    }
    assert observed_class_hashes == (
        _FROZEN_CLASS_DEFINITION_HASHES.get(
            source_relative,
            {},
        )
    )
    observed_function_nodes = [
        function_node
        for function_node in tree.body
        if isinstance(
            function_node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        )
    ]
    observed_function_names = [
        function_node.name for function_node in observed_function_nodes
    ]
    assert len(observed_function_names) == len(
        set(observed_function_names)
    )
    for function_node in observed_function_nodes:
        assert module_level_bindings.get(function_node.name) == [
            function_node
        ]
    observed_top_level_complex_mutations = frozenset(
        hashlib.sha256(
            ast.dump(
                statement,
                annotate_fields=True,
                include_attributes=False,
            ).encode("utf-8")
        ).hexdigest()
        for statement in tree.body
        for target in mutation_targets(statement)
        for leaf in mutation_target_leaves(target)
        if isinstance(leaf, (ast.Attribute, ast.Subscript))
    )
    assert observed_top_level_complex_mutations == (
        _FROZEN_TOP_LEVEL_COMPLEX_MUTATION_HASHES.get(
            source_relative,
            frozenset(),
        )
    )
    assert not any(
        isinstance(statement, ast.AugAssign) for statement in tree.body
    )
    assert not any(
        isinstance(node, ast.NamedExpr)
        for statement in tree.body
        if not isinstance(
            statement,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        )
        for node in ast.walk(statement)
    )
    observed_top_level_control_flow = frozenset(
        hashlib.sha256(
            ast.dump(
                statement,
                annotate_fields=True,
                include_attributes=False,
            ).encode("utf-8")
        ).hexdigest()
        for statement in tree.body
        if isinstance(
            statement,
            (
                ast.AsyncFor,
                ast.AsyncWith,
                ast.For,
                ast.If,
                ast.Match,
                ast.Try,
                ast.TryStar,
                ast.While,
                ast.With,
            ),
        )
    )
    assert observed_top_level_control_flow == (
        _FROZEN_TOP_LEVEL_CONTROL_FLOW_HASHES.get(
            source_relative,
            frozenset(),
        )
    )
    observed_top_level_sorted_key_calls = frozenset(
        hashlib.sha256(
            ast.dump(
                binding_node,
                annotate_fields=True,
                include_attributes=False,
            ).encode("utf-8")
        ).hexdigest()
        for statement in tree.body
        if not isinstance(
            statement,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Import,
                ast.ImportFrom,
            ),
        )
        for binding_node in ast.walk(statement)
        if (
            isinstance(binding_node, ast.Call)
            and isinstance(binding_node.func, ast.Name)
            and binding_node.func.id == "sorted"
            and binding_node.keywords
        )
    )
    assert observed_top_level_sorted_key_calls == (
        _FROZEN_TOP_LEVEL_SORTED_KEY_CALL_HASHES.get(
            source_relative,
            frozenset(),
        )
    )
    scalable_binding_calls = {
        "Path",
        "PurePosixPath",
        "_ROLE_IDENTITY_ALIASES.items",
        "_SUCCESS_ROLE_PATHS.items",
        "_e3_keys",
        "_hash_without",
        "_keys",
        "_success_contract_test_node_ids",
        "dict",
        "frozenset",
        "hashlib.sha1",
        "hashlib.sha256",
        "json.dumps",
        "list",
        "node_id.split",
        "range",
        "re.compile",
        "resolve",
        "set",
        "sorted",
        "split",
        "str",
        "tuple",
    }
    frozen_binding_call_counts = {
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
        ): {
            "_RecoveryEpoch003PublicationRolePaths": 1,
        },
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
        ): {
            "SystemExit": 1,
            "_main": 1,
            "sys.path.insert": 1,
        },
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
        ): {
            "_AdditivePhaseOrderCompatibility": 1,
        },
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
        ): {
            "SystemExit": 1,
            "_main": 1,
            "sys.path.insert": 1,
        },
    }
    observed_frozen_binding_calls: dict[str, int] = {}

    def binding_call_name(node: ast.AST) -> str | None:
        dotted = _dotted_ast_name(node)
        if dotted is not None:
            return dotted
        if isinstance(node, ast.Attribute):
            return node.attr
        return None

    def walk_binding_nodes(node: ast.AST) -> Any:
        for child in ast.iter_child_nodes(node):
            if isinstance(
                child,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue
            yield child
            yield from walk_binding_nodes(child)

    function_nodes_by_name = {
        node.name: node for node in observed_function_nodes
    }
    top_level_owned_roots: set[str] = set()
    for statement in tree.body:
        if isinstance(
            statement,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            continue
        for binding_node in (
            statement,
            *walk_binding_nodes(statement),
        ):
            if (
                isinstance(binding_node, ast.Call)
                and isinstance(binding_node.func, ast.Name)
                and binding_node.func.id in function_nodes_by_name
            ):
                top_level_owned_roots.add(binding_node.func.id)
    top_level_owned_closure: set[str] = set()
    pending_owned = sorted(top_level_owned_roots)
    while pending_owned:
        owned_name = pending_owned.pop(0)
        if owned_name in top_level_owned_closure:
            continue
        top_level_owned_closure.add(owned_name)
        owned_node = function_nodes_by_name[owned_name]
        referenced_owned = {
            child.id
            for child in ast.walk(owned_node)
            if (
                isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
                and child.id in function_nodes_by_name
            )
        }
        pending_owned.extend(
            sorted(referenced_owned - top_level_owned_closure)
        )
    owned_callable_hashes = {
        name: hashlib.sha256(
            ast.dump(
                function_nodes_by_name[name],
                annotate_fields=True,
                include_attributes=False,
            ).encode("utf-8")
        ).hexdigest()
        for name in sorted(top_level_owned_closure)
    }
    assert _sha256_value(owned_callable_hashes) == (
        _FROZEN_TOP_LEVEL_OWNED_CALLABLE_CLOSURE_SHA256[
            source_relative
        ]
    )

    top_level_builtin_callables = {
        "SystemExit",
        "dict",
        "frozenset",
        "list",
        "range",
        "set",
        "sorted",
        "str",
        "tuple",
    }

    def top_level_lexical_bindings(statement: ast.AST) -> set[str]:
        names: set[str] = set()

        def visit(node: ast.AST) -> None:
            if node is not statement and isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                return
            if isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, ast.Name) and isinstance(
                node.ctx,
                (ast.Store, ast.Del),
            ):
                names.add(node.id)
            for child in ast.iter_child_nodes(node):
                visit(child)

        visit(statement)
        return names

    def assert_top_level_call_binding(
        callable_node: ast.AST,
        name: str,
        lexical_bindings: set[str],
    ) -> None:
        if (
            isinstance(callable_node, ast.Attribute)
            and _dotted_ast_name(callable_node) is None
        ):
            return
        root_name, separator, _ = name.partition(".")
        if separator:
            if root_name not in declared_import_bindings:
                return
            assert root_name not in lexical_bindings
            bindings = module_level_bindings.get(root_name)
            assert bindings is not None and len(bindings) == 1
            assert isinstance(bindings[0], ast.alias)
            return
        if name in top_level_builtin_callables:
            assert name not in lexical_bindings
            assert name not in module_level_bindings
            return
        assert name not in lexical_bindings
        bindings = module_level_bindings.get(name)
        assert bindings is not None and len(bindings) == 1
        assert isinstance(
            bindings[0],
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.alias,
            ),
        )

    callback_keyword_names = {
        "callback",
        "cls",
        "default",
        "hook",
        "key",
        "object_hook",
        "object_pairs_hook",
        "parse_constant",
        "parse_float",
        "parse_int",
        "predicate",
    }

    def assert_top_level_call_arguments(
        call: ast.Call,
        name: str,
    ) -> None:
        assert all(keyword.arg is not None for keyword in call.keywords)
        keyword_names = {
            keyword.arg
            for keyword in call.keywords
            if keyword.arg is not None
        }
        if name == "sorted":
            return
        assert not (keyword_names & callback_keyword_names)
        if name == "json.dumps":
            assert keyword_names <= {
                "allow_nan",
                "check_circular",
                "ensure_ascii",
                "indent",
                "separators",
                "skipkeys",
                "sort_keys",
            }

    frozen_for_path = frozen_binding_call_counts.get(
        source_relative,
        {},
    )
    for statement in tree.body:
        if isinstance(
            statement,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Import,
                ast.ImportFrom,
            ),
        ):
            continue
        lexical_bindings = top_level_lexical_bindings(statement)
        for binding_node in (
            statement,
            *walk_binding_nodes(statement),
        ):
            if not isinstance(binding_node, ast.Call):
                continue
            name = binding_call_name(binding_node.func)
            assert name is not None
            assert_top_level_call_binding(
                binding_node.func,
                name,
                lexical_bindings,
            )
            assert_top_level_call_arguments(binding_node, name)
            if name in frozen_for_path:
                observed_frozen_binding_calls[name] = (
                    observed_frozen_binding_calls.get(name, 0) + 1
                )
            else:
                assert name in scalable_binding_calls
            if name == "sorted" and binding_node.keywords:
                call_hash = hashlib.sha256(
                    ast.dump(
                        binding_node,
                        annotate_fields=True,
                        include_attributes=False,
                    ).encode("utf-8")
                ).hexdigest()
                assert call_hash in observed_top_level_sorted_key_calls
    assert observed_frozen_binding_calls == frozen_for_path
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert not node.decorator_list
            for default_expression in (
                *node.args.defaults,
                *node.args.kw_defaults,
            ):
                if default_expression is None:
                    continue
                assert not any(
                    isinstance(
                        default_node,
                        (
                            ast.Attribute,
                            ast.Await,
                            ast.Call,
                            ast.Dict,
                            ast.DictComp,
                            ast.GeneratorExp,
                            ast.Lambda,
                            ast.List,
                            ast.ListComp,
                            ast.Set,
                            ast.SetComp,
                            ast.Subscript,
                            ast.Yield,
                            ast.YieldFrom,
                        ),
                    )
                    for default_node in ast.walk(default_expression)
                )
            assert node.name not in {
                "__delattr__",
                "__dict__",
                "__getattr__",
                "__getattribute__",
                "__getitem__",
                "__iter__",
                "__next__",
                "__setattr__",
                "__setitem__",
            }
        if isinstance(node, ast.Name):
            assert node.id not in {
                "__builtins__",
                "__import__",
                "compile",
                "eval",
                "exec",
                "globals",
                "locals",
                "open",
            }
            if (
                isinstance(node.ctx, ast.Load)
                and node.id
                in {
                    "delattr",
                    "getattr",
                    "setattr",
                    "vars",
                }
            ):
                parent = parents.get(node)
                assert isinstance(parent, ast.Call)
                assert parent.func is node
            if (
                isinstance(node.ctx, ast.Load)
                and node.id in module_object_aliases
            ):
                parent = parents.get(node)
                allowed_attribute_base = (
                    isinstance(parent, ast.Attribute)
                    and parent.value is node
                )
                allowed_literal_getattr = (
                    isinstance(parent, ast.Call)
                    and isinstance(parent.func, ast.Name)
                    and parent.func.id == "getattr"
                    and bool(parent.args)
                    and parent.args[0] is node
                    and len(parent.args) >= 2
                    and isinstance(parent.args[1], ast.Constant)
                    and isinstance(parent.args[1].value, str)
                )
                assert allowed_attribute_base or allowed_literal_getattr
        if isinstance(node, ast.Import):
            assert all(
                alias.name.partition(".")[0] in allowed_import_roots
                or alias.name.partition(".")[0].startswith("emlis_")
                for alias in node.names
            )
            assert all(
                alias.name.partition(".")[0] != "importlib"
                for alias in node.names
            )
            assert not any(
                any(
                    alias.name == root_name
                    or alias.name.startswith(f"{root_name}.")
                    for root_name in forbidden_network_roots
                )
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            imported_module = node.module or ""
            imported_root = imported_module.partition(".")[0]
            assert (
                imported_root in allowed_import_roots
                or imported_root.startswith("emlis_")
            )
            if imported_module == "importlib":
                assert all(alias.name == "metadata" for alias in node.names)
            assert not any(
                imported_module == root_name
                or imported_module.startswith(f"{root_name}.")
                for root_name in forbidden_network_roots
            )
        if isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_reflection_tails
            name = normalized_dotted_name(node)
            if (
                name is not None
                and name.startswith("importlib.metadata.")
            ):
                assert name in {
                    "importlib.metadata.distribution",
                    "importlib.metadata.version",
                }
            if (
                name in forbidden_attributes
                or node.attr in forbidden_alias_tails
            ):
                parent = parents.get(node)
                assert isinstance(parent, ast.Call) and parent.func is node
        if isinstance(node, ast.Call):
            call_name = normalized_dotted_name(node.func)
            if call_name is not None:
                assert call_name not in {
                    "__import__",
                    "compile",
                    "eval",
                    "exec",
                    "os.putenv",
                    "os.unsetenv",
                }
                assert (
                    call_name.rsplit(".", 1)[-1]
                    not in forbidden_reflection_tails
                )
            if isinstance(node.func, ast.Subscript):
                subscripted_name = normalized_dotted_name(node.func.value)
                assert subscripted_name not in {
                    "__builtins__",
                    "sys.modules",
                }
            assert_literal_getattr_safe(node)
            for argument in node.args:
                assert_binding_expression_safe(argument)
            for keyword in node.keywords:
                assert_binding_expression_safe(keyword.value)
        for target in mutation_targets(node):
            for leaf in mutation_target_leaves(target):
                if isinstance(leaf, ast.Name):
                    assert leaf.id not in declared_import_bindings
                root_name = target_root_name(leaf)
                if isinstance(leaf, (ast.Attribute, ast.Subscript)):
                    assert root_name not in module_aliases
                    target_name = normalized_dotted_name(leaf)
                    assert (
                        target_name is None
                        or not target_name.startswith("os.environ")
                    )

    for node in tree.body:
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            for child in ast.walk(node):
                if not isinstance(child, ast.Call):
                    continue
                call_name = _dotted_ast_name(child.func)
                if call_name is not None:
                    tail = call_name.rsplit(".", 1)[-1]
                    assert call_name not in forbidden_attributes
                    assert call_name not in {
                        "__import__",
                        "compile",
                        "eval",
                        "exec",
                        "open",
                        "vars",
                    }
                    assert tail not in _FORBIDDEN_EFFECT_CALL_TAILS
                    assert tail not in forbidden_reflection_tails
                assert_literal_getattr_safe(child)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            forbidden = forbidden_from_imports.get(node.module or "", set())
            assert not any(alias.name in forbidden for alias in node.names)
        elif isinstance(
            node,
            (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr),
        ):
            assert_binding_expression_safe(node.value)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            assert_binding_expression_safe(node.iter)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                assert_binding_expression_safe(item.context_expr)
        elif isinstance(node, ast.comprehension):
            assert_binding_expression_safe(node.iter)
            for expression in node.ifs:
                assert_binding_expression_safe(expression)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for expression in (
                *node.args.defaults,
                *node.args.kw_defaults,
                *node.decorator_list,
            ):
                assert_binding_expression_safe(expression)
                assert_binding_time_calls_safe(expression)
        elif isinstance(node, ast.Lambda):
            for expression in (
                *node.args.defaults,
                *node.args.kw_defaults,
            ):
                assert_binding_expression_safe(expression)
                assert_binding_time_calls_safe(expression)
        elif isinstance(node, ast.ClassDef):
            for expression in (
                *node.bases,
                *(keyword.value for keyword in node.keywords),
                *node.decorator_list,
            ):
                assert_binding_expression_safe(expression)
                assert_binding_time_calls_safe(expression)
            for statement in node.body:
                if not isinstance(
                    statement,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef,
                    ),
                ):
                    assert_binding_time_calls_safe(statement)


def _assert_no_cached_effect_objects(module: ModuleType) -> None:
    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    import_expectations: dict[str, set[str]] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                binding = alias.asname or alias.name.partition(".")[0]
                expected = (
                    alias.name
                    if alias.asname
                    else alias.name.partition(".")[0]
                )
                import_expectations.setdefault(binding, set()).add(expected)
        elif isinstance(statement, ast.ImportFrom) and statement.module:
            for alias in statement.names:
                if alias.name == "*":
                    continue
                binding = alias.asname or alias.name
                import_expectations.setdefault(binding, set()).add(
                    f"{statement.module}.{alias.name}"
                )
    import_bindings = set(import_expectations)
    imported_module_ids = {
        id(vars(module)[name])
        for name in import_bindings
        if isinstance(vars(module).get(name), ModuleType)
    }
    effect_sinks = [
        builtins.__import__,
        builtins.compile,
        builtins.eval,
        builtins.exec,
        builtins.open,
        io.open,
        Path.mkdir,
        Path.open,
        Path.rename,
        Path.replace,
        Path.touch,
        Path.unlink,
        Path.write_bytes,
        Path.write_text,
    ]
    for effect_module, names in (
        (
            os,
            (
                "_exit",
                "chdir",
                "chmod",
                "chown",
                "chroot",
                "execl",
                "execle",
                "execlp",
                "execlpe",
                "execv",
                "execve",
                "execvp",
                "execvpe",
                "fdopen",
                "fchmod",
                "fchown",
                "fork",
                "forkpty",
                "fsync",
                "ftruncate",
                "kill",
                "killpg",
                "link",
                "lchmod",
                "lchown",
                "makedirs",
                "mkdir",
                "mkfifo",
                "mknod",
                "open",
                "popen",
                "posix_spawn",
                "posix_spawnp",
                "putenv",
                "remove",
                "removedirs",
                "rename",
                "renames",
                "replace",
                "rmdir",
                "spawnl",
                "spawnle",
                "spawnlp",
                "spawnlpe",
                "spawnv",
                "spawnve",
                "spawnvp",
                "spawnvpe",
                "setegid",
                "seteuid",
                "setgid",
                "setgroups",
                "setregid",
                "setresgid",
                "setresuid",
                "setreuid",
                "setuid",
                "symlink",
                "sync",
                "system",
                "truncate",
                "umask",
                "unlink",
                "unsetenv",
                "write",
            ),
        ),
        (
            shutil,
            (
                "copy",
                "copy2",
                "copyfile",
                "copytree",
                "move",
                "rmtree",
            ),
        ),
        (
            subprocess,
            (
                "Popen",
                "call",
                "check_call",
                "check_output",
                "getoutput",
                "getstatusoutput",
                "run",
            ),
        ),
    ):
        effect_sinks.extend(
            getattr(effect_module, name)
            for name in names
            if hasattr(effect_module, name)
        )
    sink_ids = {id(sink) for sink in effect_sinks}
    seen: set[int] = set()

    def visit(value: Any) -> None:
        value_id = id(value)
        assert value_id not in sink_ids
        if value_id in seen:
            return
        seen.add(value_id)
        assert not isinstance(value, io.IOBase)
        if isinstance(value, ModuleType):
            assert type(value) is ModuleType
            if value_id in imported_module_ids:
                matching_bindings = {
                    name
                    for name in import_bindings
                    if vars(module).get(name) is value
                }
                assert matching_bindings
                assert any(
                    value.__name__ in import_expectations[name]
                    for name in matching_bindings
                )
            else:
                for name, item in vars(value).items():
                    if not name.startswith("__"):
                        visit(item)
            return
        if isinstance(value, dict):
            items = dict.items(value)
            for item in items:
                visit(item)
            return
        if type(value) in {list, tuple, set, frozenset, deque}:
            for item in value:
                visit(item)
            return
        assert not isinstance(value, IteratorABC)
        if type(value) is partial:
            visit(value.func)
            visit(value.args)
            visit(value.keywords or {})
            return
        if type(value) is property:
            for accessor in (value.fget, value.fset, value.fdel):
                if (
                    inspect.isfunction(accessor)
                    and accessor.__module__ == module.__name__
                ):
                    _assert_no_effect_sink_calls(
                        module,
                        accessor.__name__,
                    )
            visit(value.fget)
            visit(value.fset)
            visit(value.fdel)
            return
        if inspect.isfunction(value):
            if value.__module__ != module.__name__:
                return
            for item in value.__defaults__ or ():
                visit(item)
            for item in (value.__kwdefaults__ or {}).values():
                visit(item)
            for cell in value.__closure__ or ():
                visit(cell.cell_contents)
            for item in vars(value).values():
                visit(item)
            return
        if inspect.ismethod(value):
            visit(value.__func__)
            visit(value.__self__)
            return
        if isinstance(value, type) and value.__module__ == module.__name__:
            for item in type.__getattribute__(value, "__dict__").values():
                visit(item)
            return
        wrapped = inspect.getattr_static(value, "__wrapped__", None)
        if wrapped is not None:
            visit(wrapped)
        if (
            not isinstance(value, type)
            and type(value).__module__ == module.__name__
        ):
            try:
                instance_dict = object.__getattribute__(
                    value,
                    "__dict__",
                )
            except AttributeError:
                instance_dict = None
            if instance_dict is not None:
                assert type(instance_dict) is dict
                for item in dict.values(instance_dict):
                    visit(item)

    for name, value in vars(module).items():
        if not name.startswith("__"):
            visit(value)


def _assert_success_without_mutation(
    api: Callable[[Mapping[str, Any]], Any],
    state: Mapping[str, Any],
) -> None:
    original = copy.deepcopy(state)
    assert api(state) == ()
    assert state == original


def _assert_failure_without_mutation(
    api: Callable[[Mapping[str, Any]], Any],
    state: Mapping[str, Any],
    expected: tuple[str, ...],
) -> None:
    original = copy.deepcopy(state)
    assert api(state) == expected
    assert state == original


def _assert_versioned_constants(module: ModuleType) -> None:
    assert module._RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA == (
        _EVENT_SCHEMA_V2
    )
    assert module._RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA == (
        _OPERATIONAL_ADMISSION_SCHEMA_V2
    )
    assert module._RECOVERY_EPOCH004_CANDIDATE_SCHEMA == (
        _CANDIDATE_SCHEMA_V1
    )
    assert module._RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA == (
        _SOURCE_CLOSURE_SCHEMA_V1
    )
    assert module._RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA == (
        _BOOTSTRAP_CLOSURE_SCHEMA_V1
    )
    assert module._RECOVERY_EPOCH004_REFERENCE_SCHEMA == (
        _REFERENCE_SCHEMA_V1
    )
    assert module._RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY == (
        _CURRENT_P0_EXTERNAL_IDENTITY
    )
    assert module._RECOVERY_EPOCH004_RECONCILIATION_EXTERNAL_IDENTITY == (
        _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY
    )
    assert module._RECOVERY_EPOCH004_D1_AUTHORITY == _D1_AUTHORITY
    assert tuple(
        module._RECOVERY_EPOCH004_HISTORICAL_CANDIDATE_VERSION_IDS
    ) == _HISTORICAL_CANDIDATE_VERSION_IDS
    assert set(module.RECOVERY_EPOCH004_EVENT1_CONNECTION_STATE_KEYS) == (
        _CONNECTION_STATE_KEYS
    )
    assert set(module._RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_KEYS) == (
        set(_V1_ADMISSION_KEYS_ORDERED)
    )
    assert set(module._RECOVERY_EPOCH004_PREDECESSOR_KEYS) == set(
        _V2_PREDECESSOR_KEYS_ORDERED
    )


def _assert_no_effect_sink_calls(
    module: ModuleType,
    api_name: str,
) -> None:
    source_path = Path(inspect.getsourcefile(module) or "")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    module_aliases = {
        alias.asname or alias.name.partition(".")[0]: alias.name
        for statement in tree.body
        if isinstance(statement, ast.Import)
        for alias in statement.names
    }
    from_import_bindings: dict[str, tuple[str, str]] = {
        alias.asname or alias.name: (statement.module, alias.name)
        for statement in tree.body
        if isinstance(statement, ast.ImportFrom)
        and statement.module is not None
        for alias in statement.names
        if alias.name != "*"
    }
    for statement in tree.body:
        if not isinstance(statement, ast.ImportFrom) or not statement.module:
            continue
        if statement.module == "pathlib":
            for alias in statement.names:
                if alias.name in {"Path", "PurePosixPath"}:
                    module_aliases[alias.asname or alias.name] = alias.name
        if statement.module == "importlib":
            for alias in statement.names:
                if alias.name == "metadata":
                    module_aliases[
                        alias.asname or alias.name
                    ] = "importlib.metadata"
    reachable_functions = set(
        _reachable_function_names(module, api_name)
    )
    safe_bare_calls = {
        "BytesParser",
        "OSError",
        "Path",
        "PurePosixPath",
        "TypeError",
        "ValueError",
        "all",
        "any",
        "artifact_sha256",
        "bool",
        "build_recovery_epoch003_source_bootstrap_closure",
        "bytes",
        "canonical_json_bytes",
        "deepcopy",
        "dict",
        "enumerate",
        "float",
        "frozenset",
        "int",
        "isinstance",
        "iter",
        "len",
        "list",
        "load_canonical_json_bytes",
        "max",
        "min",
        "next",
        "range",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "type",
        "validate_recovery_epoch003_source_bootstrap_contract_state",
        "validate_recovery_epoch003_source_bootstrap_contract_state_v2",
        "validate_recovery_epoch003_publication_contract_state",
        "validate_recovery_epoch003_sequence_event1_contract_state",
        "verify_recovery_epoch003_operational_admission_contract",
        "zip",
        _INDEPENDENT_API,
    }
    safe_module_calls = {
        "ast.iter_child_nodes",
        "ast.literal_eval",
        "ast.parse",
        "ast.walk",
        "base64.urlsafe_b64encode",
        "csv.reader",
        "hashlib.sha1",
        "hashlib.sha256",
        "importlib.metadata.distribution",
        "importlib.metadata.version",
        "json.dumps",
        "json.loads",
        "math.isfinite",
        "re.compile",
        "re.fullmatch",
        "secrets.token_bytes",
        "secrets.token_hex",
        "stat.S_IMODE",
        "stat.S_ISDIR",
        "stat.S_ISLNK",
        "stat.S_ISREG",
        "subprocess.run",
        "unicodedata.normalize",
    }
    safe_method_tails = {
        "absolute",
        "add",
        "append",
        "as_posix",
        "copy",
        "decode",
        "discard",
        "encode",
        "endswith",
        "extend",
        "fullmatch",
        "get",
        "group",
        "hexdigest",
        "intersection",
        "is_absolute",
        "is_dir",
        "is_file",
        "is_symlink",
        "isidentifier",
        "items",
        "keys",
        "lower",
        "lstat",
        "match",
        "namelist",
        "partition",
        "pop",
        "read",
        "read_bytes",
        "read_text",
        "relative_to",
        "removeprefix",
        "removesuffix",
        "resolve",
        "rpartition",
        "rsplit",
        "rstrip",
        "setdefault",
        "sort",
        "split",
        "splitlines",
        "startswith",
        "stat",
        "strip",
        "update",
        "upper",
        "values",
    }
    safe_global_types = {
        bool,
        bytes,
        dict,
        float,
        frozenset,
        int,
        list,
        Path,
        re.Pattern,
        set,
        str,
        tuple,
    }
    module_bound_names = set(_module_level_bindings(tree))
    mutating_method_tails = {
        "add",
        "append",
        "clear",
        "difference_update",
        "discard",
        "extend",
        "insert",
        "intersection_update",
        "pop",
        "popitem",
        "remove",
        "reverse",
        "setdefault",
        "sort",
        "symmetric_difference_update",
        "update",
    }
    callback_capable_tails = {
        "dumps",
        "loads",
        "max",
        "min",
        "sort",
        "sorted",
    }
    callback_keyword_names = {
        "callback",
        "cls",
        "default",
        "hook",
        "key",
        "object_hook",
        "object_pairs_hook",
        "parse_constant",
        "parse_float",
        "parse_int",
        "predicate",
    }

    def expression_root_name(node: ast.AST) -> str | None:
        value = node
        while isinstance(value, (ast.Attribute, ast.Subscript)):
            value = value.value
        return value.id if isinstance(value, ast.Name) else None

    def mutation_targets(node: ast.AST) -> tuple[ast.AST, ...]:
        if isinstance(node, ast.Assign):
            return tuple(node.targets)
        if isinstance(
            node,
            (ast.AnnAssign, ast.AugAssign, ast.NamedExpr),
        ):
            return (node.target,)
        if isinstance(node, (ast.For, ast.AsyncFor)):
            return (node.target,)
        if isinstance(node, (ast.With, ast.AsyncWith)):
            return tuple(
                item.optional_vars
                for item in node.items
                if item.optional_vars is not None
            )
        if isinstance(node, ast.comprehension):
            return (node.target,)
        if isinstance(node, ast.Delete):
            return tuple(node.targets)
        return ()

    def mutation_target_leaves(
        target: ast.AST,
    ) -> tuple[ast.AST, ...]:
        if isinstance(target, (ast.Tuple, ast.List)):
            return tuple(
                leaf
                for element in target.elts
                for leaf in mutation_target_leaves(element)
            )
        if isinstance(target, ast.Starred):
            return mutation_target_leaves(target.value)
        return (target,)

    def mutation_target_names(target: ast.AST) -> set[str]:
        return {
            leaf.id
            for leaf in mutation_target_leaves(target)
            if isinstance(leaf, ast.Name)
        }

    def assignment_parts(
        node: ast.AST,
    ) -> tuple[ast.AST | None, tuple[ast.AST, ...]]:
        if isinstance(node, ast.Assign):
            return node.value, tuple(node.targets)
        if isinstance(node, ast.AnnAssign):
            return node.value, (node.target,)
        if isinstance(node, ast.NamedExpr):
            return node.value, (node.target,)
        return None, ()

    def non_assignment_binding_names(
        function_node: ast.FunctionDef,
    ) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(function_node):
            if isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                if node is not function_node:
                    names.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    names.add(
                        alias.asname
                        or (
                            alias.name.partition(".")[0]
                            if isinstance(node, ast.Import)
                            else alias.name
                        )
                    )
            elif (
                isinstance(node, ast.ExceptHandler)
                and isinstance(node.name, str)
            ):
                names.add(node.name)
            elif isinstance(node, (ast.MatchAs, ast.MatchStar)):
                if node.name is not None:
                    names.add(node.name)
            elif (
                isinstance(node, ast.MatchMapping)
                and node.rest is not None
            ):
                names.add(node.rest)
        return names

    def nested_scope_argument_names(
        function_node: ast.FunctionDef,
    ) -> set[str]:
        names: set[str] = set()
        for node in ast.walk(function_node):
            if node is function_node or not isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
            ):
                continue
            arguments = node.args
            names.update(
                argument.arg
                for argument in (
                    *arguments.posonlyargs,
                    *arguments.args,
                    *arguments.kwonlyargs,
                )
            )
            if arguments.vararg is not None:
                names.add(arguments.vararg.arg)
            if arguments.kwarg is not None:
                names.add(arguments.kwarg.arg)
        return names

    function_nodes = {
        function_name: _function_node(module, function_name)
        for function_name in reachable_functions
    }
    for function_node in function_nodes.values():
        assert not any(
            isinstance(node, (ast.Global, ast.Nonlocal))
            for node in ast.walk(function_node)
        )

    def state_aliases_for(
        function_node: ast.FunctionDef,
        state_returning_functions: set[str],
    ) -> set[str]:
        module_state_aliases = set(module_bound_names)
        changed = True
        while changed:
            changed = False
            for node in ast.walk(function_node):
                value, targets = assignment_parts(node)
                if value is None:
                    continue
                aliases_module_state = (
                    expression_root_name(value) in module_state_aliases
                    or (
                        isinstance(value, ast.Call)
                        and isinstance(value.func, ast.Name)
                        and value.func.id in state_returning_functions
                    )
                )
                if not aliases_module_state:
                    continue
                for target in targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id not in module_state_aliases
                    ):
                        module_state_aliases.add(target.id)
                        changed = True
        return module_state_aliases

    state_returning_functions: set[str] = set()
    changed = True
    while changed:
        changed = False
        for function_name, function_node in function_nodes.items():
            if function_name in state_returning_functions:
                continue
            aliases = state_aliases_for(
                function_node,
                state_returning_functions,
            )
            for return_node in (
                node
                for node in ast.walk(function_node)
                if isinstance(node, ast.Return)
                and node.value is not None
            ):
                return_value = return_node.value
                if (
                    expression_root_name(return_value) in aliases
                    or (
                        isinstance(return_value, ast.Call)
                        and isinstance(return_value.func, ast.Name)
                        and return_value.func.id
                        in state_returning_functions
                    )
                ):
                    state_returning_functions.add(function_name)
                    changed = True
                    break

    builtin_mutator_types = {"bytearray", "dict", "list", "set"}
    for function_name, function_node in function_nodes.items():
        module_state_aliases = state_aliases_for(
            function_node,
            state_returning_functions,
        )
        local_binding_names = {
            node.id
            for node in ast.walk(function_node)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, (ast.Store, ast.Del))
        } | {
            node.arg
            for node in ast.walk(function_node)
            if isinstance(node, ast.arg)
        } | non_assignment_binding_names(function_node)
        nested_argument_names = nested_scope_argument_names(
            function_node
        )
        nested_callback_definitions: dict[
            str,
            list[ast.FunctionDef | ast.AsyncFunctionDef],
        ] = {}
        for candidate in ast.walk(function_node):
            if (
                candidate is not function_node
                and isinstance(
                    candidate,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            ):
                nested_callback_definitions.setdefault(
                    candidate.name,
                    [],
                ).append(candidate)
        fresh_mutable_names: set[str] = set()

        def is_fresh_mutable(expression: ast.AST) -> bool:
            if isinstance(
                expression,
                (
                    ast.Dict,
                    ast.DictComp,
                    ast.List,
                    ast.ListComp,
                    ast.Set,
                    ast.SetComp,
                ),
            ):
                return True
            if isinstance(expression, ast.Name):
                return expression.id in fresh_mutable_names
            if isinstance(expression, ast.IfExp):
                return is_fresh_mutable(
                    expression.body
                ) and is_fresh_mutable(expression.orelse)
            if not isinstance(expression, ast.Call):
                return False
            call_name = _dotted_ast_name(expression.func)
            if call_name == "json.loads":
                return all(
                    keyword.arg is not None
                    and (
                        keyword.arg not in callback_keyword_names
                        or (
                            isinstance(
                                keyword.value,
                                ast.Constant,
                            )
                            and keyword.value.value is None
                        )
                    )
                    for keyword in expression.keywords
                )
            if call_name in {
                "ast.literal_eval",
                "bytearray",
                "copy.deepcopy",
                "deepcopy",
                "dict",
                "hashlib.sha1",
                "hashlib.sha256",
                "list",
                "set",
                "sorted",
            }:
                return True
            return bool(
                isinstance(expression.func, ast.Attribute)
                and expression.func.attr == "copy"
                and isinstance(expression.func.value, ast.Name)
                and expression.func.value.id in fresh_mutable_names
            )

        changed = True
        while changed:
            changed = False
            for node in ast.walk(function_node):
                value, targets = assignment_parts(node)
                if value is None or not is_fresh_mutable(value):
                    continue
                for target in targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id not in fresh_mutable_names
                    ):
                        fresh_mutable_names.add(target.id)
                        changed = True
        assert fresh_mutable_names.isdisjoint(local_binding_names & {
            argument.arg
            for argument in (
                *function_node.args.posonlyargs,
                *function_node.args.args,
                *function_node.args.kwonlyargs,
            )
        })
        if function_node.args.vararg is not None:
            assert function_node.args.vararg.arg not in fresh_mutable_names
        if function_node.args.kwarg is not None:
            assert function_node.args.kwarg.arg not in fresh_mutable_names
        assert fresh_mutable_names.isdisjoint(nested_argument_names)
        assert fresh_mutable_names.isdisjoint(
            non_assignment_binding_names(function_node)
            - {
                argument.arg
                for argument in (
                    *function_node.args.posonlyargs,
                    *function_node.args.args,
                    *function_node.args.kwonlyargs,
                )
            }
        )
        for node in ast.walk(function_node):
            value, targets = assignment_parts(node)
            for target in targets:
                rebound_fresh = (
                    mutation_target_names(target)
                    & fresh_mutable_names
                )
                if rebound_fresh:
                    assert isinstance(target, ast.Name)
                    assert rebound_fresh == {target.id}
                    assert value is not None
                    assert is_fresh_mutable(value)
            if targets:
                continue
            for target in mutation_targets(node):
                if (
                    mutation_target_names(target)
                    & fresh_mutable_names
                ):
                    raise AssertionError(
                        "fresh mutable local has non-fresh rebinding"
                    )
        safe_augassign_names: set[str] = set()

        def is_safe_augassign_value(expression: ast.AST) -> bool:
            if isinstance(expression, ast.Constant):
                return type(expression.value) in {
                    bool,
                    bytes,
                    float,
                    int,
                    str,
                    type(None),
                }
            if isinstance(expression, ast.Name):
                return expression.id in safe_augassign_names
            if isinstance(expression, ast.IfExp):
                return is_safe_augassign_value(
                    expression.body
                ) and is_safe_augassign_value(expression.orelse)
            return bool(
                isinstance(expression, ast.Call)
                and _dotted_ast_name(expression.func)
                in {
                    "Path",
                    "PurePosixPath",
                    "bytes",
                    "float",
                    "int",
                    "len",
                    "str",
                    "tuple",
                }
            )

        changed = True
        while changed:
            changed = False
            for node in ast.walk(function_node):
                value, targets = assignment_parts(node)
                if (
                    value is None
                    or not is_safe_augassign_value(value)
                ):
                    continue
                for target in targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id not in safe_augassign_names
                    ):
                        safe_augassign_names.add(target.id)
                        changed = True
        argument_names = {
            argument.arg
            for argument in (
                *function_node.args.posonlyargs,
                *function_node.args.args,
                *function_node.args.kwonlyargs,
            )
        }
        if function_node.args.vararg is not None:
            argument_names.add(function_node.args.vararg.arg)
        if function_node.args.kwarg is not None:
            argument_names.add(function_node.args.kwarg.arg)
        assert safe_augassign_names.isdisjoint(argument_names)
        assert safe_augassign_names.isdisjoint(
            nested_argument_names
        )
        assert safe_augassign_names.isdisjoint(
            non_assignment_binding_names(function_node)
            - argument_names
        )
        for node in ast.walk(function_node):
            value, targets = assignment_parts(node)
            for target in targets:
                rebound_safe = (
                    mutation_target_names(target)
                    & safe_augassign_names
                )
                if rebound_safe:
                    assert isinstance(target, ast.Name)
                    assert rebound_safe == {target.id}
                    assert value is not None
                    assert is_safe_augassign_value(value)
            if targets or isinstance(node, ast.AugAssign):
                continue
            for target in mutation_targets(node):
                if (
                    mutation_target_names(target)
                    & safe_augassign_names
                ):
                    raise AssertionError(
                        "safe augmented local has unsafe rebinding"
                    )
        mutator_callable_aliases: set[str] = set()
        changed = True
        while changed:
            changed = False
            for node in ast.walk(function_node):
                value, targets = assignment_parts(node)
                if value is None:
                    continue
                aliases_mutator = (
                    isinstance(value, ast.Name)
                    and value.id in mutator_callable_aliases
                )
                if isinstance(value, ast.Attribute):
                    root_name = expression_root_name(value.value)
                    aliases_mutator = aliases_mutator or bool(
                        value.attr in mutating_method_tails
                        and (
                            root_name in module_state_aliases
                            or root_name in builtin_mutator_types
                            or root_name is None
                        )
                    )
                if not aliases_mutator:
                    continue
                for target in targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id not in mutator_callable_aliases
                    ):
                        mutator_callable_aliases.add(target.id)
                        changed = True
        for node in ast.walk(function_node):
            if isinstance(node, ast.AugAssign):
                assert isinstance(node.target, ast.Name)
                assert node.target.id in safe_augassign_names
                assert node.target.id not in module_state_aliases
            for target in mutation_targets(node):
                if isinstance(node, ast.AugAssign):
                    continue
                for leaf in mutation_target_leaves(target):
                    assert not isinstance(leaf, ast.Attribute)
                    if isinstance(leaf, ast.Subscript):
                        assert isinstance(leaf.value, ast.Name)
                        assert leaf.value.id in fresh_mutable_names
                        assert (
                            leaf.value.id
                            not in module_state_aliases
                        )
            if isinstance(node, ast.Call):
                assert isinstance(node.func, (ast.Name, ast.Attribute))
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "iter"
                ):
                    assert len(node.args) == 1
                    assert not node.keywords
                if isinstance(node.func, ast.Name):
                    reachable_runtime = vars(module).get(node.func.id)
                    runtime_is_reachable = bool(
                        inspect.isfunction(reachable_runtime)
                        and reachable_runtime.__module__
                        == module.__name__
                        and reachable_runtime.__name__
                        in reachable_functions
                    )
                    assert (
                        node.func.id not in reachable_functions
                        or runtime_is_reachable
                    )
                    if runtime_is_reachable:
                        assert (
                            node.func.id
                            not in local_binding_names
                        )
                        assert (
                            getattr(module, node.func.id)
                            is reachable_runtime
                        )
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in reachable_functions
                ):
                    assert inspect.isfunction(reachable_runtime)
                    assert reachable_runtime.__module__ == module.__name__
                    assert reachable_runtime.__name__ == node.func.id
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in safe_bare_calls
                ):
                    assert node.func.id not in local_binding_names
                call_name = _dotted_ast_name(node.func)
                call_tail = (
                    call_name.rsplit(".", 1)[-1]
                    if call_name is not None
                    else node.func.attr
                )
                if call_tail in callback_capable_tails:
                    assert all(
                        keyword.arg is not None
                        for keyword in node.keywords
                    )
                for keyword in node.keywords:
                    if keyword.arg not in callback_keyword_names:
                        continue
                    assert call_tail in callback_capable_tails
                    callback_expression = keyword.value
                    if (
                        isinstance(callback_expression, ast.Constant)
                        and callback_expression.value is None
                    ):
                        continue
                    if isinstance(callback_expression, ast.Lambda):
                        continue
                    assert isinstance(callback_expression, ast.Name)
                    callback_name = callback_expression.id
                    assert (
                        callback_name
                        not in mutator_callable_aliases
                    )
                    builtin_callback = getattr(
                        builtins,
                        callback_name,
                        None,
                    )
                    if builtin_callback in {
                        bytes,
                        float,
                        int,
                        str,
                    }:
                        assert callback_name not in local_binding_names
                        assert vars(module).get(callback_name) in {
                            None,
                            builtin_callback,
                        }
                        continue
                    runtime_callback = vars(module).get(
                        callback_name
                    )
                    if (
                        inspect.isfunction(runtime_callback)
                        and runtime_callback.__module__
                        == module.__name__
                        and runtime_callback.__name__
                        in reachable_functions
                    ):
                        assert callback_name not in local_binding_names
                        assert (
                            getattr(module, callback_name)
                            is runtime_callback
                        )
                        continue
                    definitions = nested_callback_definitions.get(
                        callback_name,
                        [],
                    )
                    assert len(definitions) == 1
                    definition = definitions[0]
                    assert not definition.decorator_list
                    binding_nodes: list[ast.AST] = []
                    for binding_candidate in ast.walk(function_node):
                        if (
                            isinstance(
                                binding_candidate,
                                (
                                    ast.FunctionDef,
                                    ast.AsyncFunctionDef,
                                    ast.ClassDef,
                                ),
                            )
                            and binding_candidate.name == callback_name
                        ):
                            binding_nodes.append(binding_candidate)
                        elif (
                            isinstance(binding_candidate, ast.Name)
                            and isinstance(
                                binding_candidate.ctx,
                                (ast.Store, ast.Del),
                            )
                            and binding_candidate.id == callback_name
                        ):
                            binding_nodes.append(binding_candidate)
                        elif (
                            isinstance(binding_candidate, ast.arg)
                            and binding_candidate.arg == callback_name
                        ):
                            binding_nodes.append(binding_candidate)
                        elif (
                            isinstance(
                                binding_candidate,
                                ast.ExceptHandler,
                            )
                            and binding_candidate.name == callback_name
                        ):
                            binding_nodes.append(binding_candidate)
                        elif (
                            isinstance(
                                binding_candidate,
                                (ast.MatchAs, ast.MatchStar),
                            )
                            and binding_candidate.name == callback_name
                        ):
                            binding_nodes.append(binding_candidate)
                        elif (
                            isinstance(
                                binding_candidate,
                                ast.MatchMapping,
                            )
                            and binding_candidate.rest == callback_name
                        ):
                            binding_nodes.append(binding_candidate)
                        elif isinstance(
                            binding_candidate,
                            (ast.Import, ast.ImportFrom),
                        ):
                            for alias in binding_candidate.names:
                                bound_name = (
                                    alias.asname
                                    or (
                                        alias.name.partition(".")[0]
                                        if isinstance(
                                            binding_candidate,
                                            ast.Import,
                                        )
                                        else alias.name
                                    )
                                )
                                if bound_name == callback_name:
                                    binding_nodes.append(alias)
                    assert binding_nodes == [definition]
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in mutator_callable_aliases
                if isinstance(node.func, ast.Attribute):
                    attribute_root = expression_root_name(
                        node.func
                    )
                    if attribute_root in module_aliases:
                        assert (
                            attribute_root
                            not in local_binding_names
                        )
                        canonical_module_name = module_aliases[
                            attribute_root
                        ]
                        expected_module = sys.modules.get(
                            canonical_module_name
                        )
                        if expected_module is not None:
                            assert (
                                type(expected_module) is ModuleType
                            )
                            assert (
                                vars(module).get(attribute_root)
                                is expected_module
                            )
                    receiver_root = expression_root_name(node.func.value)
                    if call_tail in mutating_method_tails:
                        assert isinstance(node.func.value, ast.Name)
                        assert (
                            node.func.value.id in fresh_mutable_names
                        )
                        assert (
                            node.func.value.id
                            not in module_state_aliases
                        )
                if call_tail in {"max", "min", "sort", "sorted"}:
                    for keyword in node.keywords:
                        if keyword.arg != "key":
                            continue
                        assert isinstance(
                            keyword.value,
                            (ast.Lambda, ast.Name),
                        )
    for call in _reachable_call_names(module, api_name):
        tail = call.rsplit(".", 1)[-1]
        assert call not in _FORBIDDEN_EFFECT_CALL_NAMES
        assert tail not in _FORBIDDEN_EFFECT_CALL_NAMES
        assert tail not in _FORBIDDEN_EFFECT_CALL_TAILS
        if "." not in call:
            if call in reachable_functions:
                continue
            if call in safe_bare_calls:
                runtime_value = vars(module).get(call)
                builtin_value = getattr(builtins, call, None)
                if builtin_value is not None:
                    assert runtime_value in {None, builtin_value}
                else:
                    imported_binding = from_import_bindings.get(call)
                    assert imported_binding is not None
                    imported_module_name, imported_name = imported_binding
                    imported_module = sys.modules.get(
                        imported_module_name
                    )
                    assert type(imported_module) is ModuleType
                    expected_runtime = ModuleType.__getattribute__(
                        imported_module,
                        imported_name,
                    )
                    assert runtime_value is expected_runtime
                continue
            runtime_value = vars(module).get(call)
            if (
                inspect.isfunction(runtime_value)
                and runtime_value.__module__ == module.__name__
                and runtime_value.__name__ in reachable_functions
            ):
                continue
            raise AssertionError(f"non-allowlisted reachable call: {call}")
        root_name = call.partition(".")[0]
        canonical_root = module_aliases.get(root_name)
        canonical_call = (
            f"{canonical_root}.{call.partition('.')[2]}"
            if canonical_root is not None
            else call
        )
        if canonical_call in safe_module_calls:
            continue
        if canonical_root is not None:
            raise AssertionError(
                f"non-allowlisted module call: {canonical_call}"
            )
        if root_name in vars(module):
            global_value = vars(module)[root_name]
            assert (
                type(global_value) in safe_global_types
                or (
                    isinstance(global_value, MappingABC)
                    and tail in {"get", "items", "keys", "values"}
                )
            )
        assert tail in safe_method_tails


def test_o01_event1_v2_owner_schema_dispatch_public_signature_and_invalid_envelope() -> None:
    api = _require_api("sequence", _OWNER_API, "O01")
    _assert_public_signature(api)
    assert api({}) == _OWNER_FAILURE
    fixture = _connection_fixture()
    _assert_success_without_mutation(api, fixture)
    module = _module("sequence")
    _assert_versioned_constants(module)
    source = _reachable_source(module, _OWNER_API)
    for token in (
        "_RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA",
        "_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA",
        "_RECOVERY_EPOCH004_CANDIDATE_SCHEMA",
        "_RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA",
        "_RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA",
        "_RECOVERY_EPOCH004_REFERENCE_SCHEMA",
        "_RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY",
        "_RECOVERY_EPOCH004_D1_AUTHORITY",
        "RECOVERY_EPOCH004_EVENT1_CONNECTION_STATE_KEYS",
        "_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_KEYS",
        "_RECOVERY_EPOCH004_PREDECESSOR_KEYS",
        "credit_eligible",
    ):
        assert token in source
    assert "validate_recovery_epoch003_sequence_event1_contract_state" not in (
        source
    )


def test_o02_event1_v2_independent_schema_dispatch_reexecutes_without_owner_trust(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _require_api("independent", _INDEPENDENT_API, "O02")
    _assert_public_signature(api)
    assert api({}) == _INDEPENDENT_FAILURE
    fixture = _connection_fixture()
    _assert_success_without_mutation(api, fixture)
    module = _module("independent")
    _assert_versioned_constants(module)
    source = _reachable_source(module, _INDEPENDENT_API)
    for token in (
        "_RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA",
        "_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA",
        "_RECOVERY_EPOCH004_CANDIDATE_SCHEMA",
        "_RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA",
        "_RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA",
        "_RECOVERY_EPOCH004_REFERENCE_SCHEMA",
        "_RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY",
        "RECOVERY_EPOCH004_EVENT1_CONNECTION_STATE_KEYS",
    ):
        assert token in source
    assert "validate_recovery_epoch003_sequence_event1_contract_state" not in (
        source
    )
    assert _OWNER_API not in source
    assert not _module_imports_name(
        module,
        imported_module=_MODULE_NAMES["sequence"],
    )
    _assert_independent_owner_boundary(module)
    _assert_no_owner_runtime_references(module)

    def forbidden_owner_trust(_state: Mapping[str, Any]) -> Any:
        raise AssertionError("independent lane called owner validator")

    monkeypatch.setattr(
        _module("sequence"),
        _OWNER_API,
        forbidden_owner_trust,
    )
    _assert_success_without_mutation(api, fixture)

    root = _repository_root()
    pre_resolved_formal_owner_modules = (
        _resolve_formal_owner_modules_for_read_only_guard(root.resolve())
    )
    owner_path = (
        root / _MANDATORY_DIRECT_PATHS["sequence"]
    ).resolve()
    real_import = builtins.__import__
    real_import_module = importlib.import_module
    real_reload = importlib.reload
    real_run_module = runpy.run_module
    real_run_path = runpy.run_path
    real_spec_from_file_location = importlib.util.spec_from_file_location
    source_loader = importlib.machinery.SourceFileLoader
    sourceless_loader = importlib.machinery.SourcelessFileLoader
    real_source_exec_module = source_loader.exec_module
    real_source_load_module = source_loader.load_module
    real_sourceless_exec_module = sourceless_loader.exec_module
    real_sourceless_load_module = sourceless_loader.load_module

    def owner_module_name(value: Any) -> bool:
        return str(value).rsplit(".", 1)[-1] == _MODULE_NAMES["sequence"]

    def owner_location(value: Any) -> bool:
        try:
            return Path(str(value)).resolve() == owner_path
        except (OSError, RuntimeError, ValueError):
            return False

    def guarded_import(
        name: str,
        globals: Mapping[str, Any] | None = None,
        locals: Mapping[str, Any] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> Any:
        assert not owner_module_name(name)
        return real_import(name, globals, locals, fromlist, level)

    def guarded_import_module(
        name: str,
        package: str | None = None,
    ) -> ModuleType:
        assert not owner_module_name(name)
        return real_import_module(name, package)

    def guarded_reload(target: ModuleType) -> ModuleType:
        assert not owner_module_name(target.__name__)
        assert not owner_location(getattr(target, "__file__", ""))
        return real_reload(target)

    def guarded_run_module(name: str, *args: Any, **kwargs: Any) -> Any:
        assert not owner_module_name(name)
        return real_run_module(name, *args, **kwargs)

    def guarded_run_path(path: str, *args: Any, **kwargs: Any) -> Any:
        assert not owner_location(path)
        return real_run_path(path, *args, **kwargs)

    def guarded_spec_from_file_location(
        name: str,
        location: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        assert not owner_module_name(name)
        assert not owner_location(location)
        return real_spec_from_file_location(
            name,
            location,
            *args,
            **kwargs,
        )

    def guarded_source_exec_module(
        loader: Any,
        target: ModuleType,
    ) -> Any:
        assert not owner_location(getattr(loader, "path", ""))
        return real_source_exec_module(loader, target)

    def guarded_source_load_module(
        loader: Any,
        fullname: str | None = None,
    ) -> Any:
        assert not owner_location(getattr(loader, "path", ""))
        assert fullname is None or not owner_module_name(fullname)
        return real_source_load_module(loader, fullname)

    def guarded_sourceless_exec_module(
        loader: Any,
        target: ModuleType,
    ) -> Any:
        assert not owner_location(getattr(loader, "path", ""))
        return real_sourceless_exec_module(loader, target)

    def guarded_sourceless_load_module(
        loader: Any,
        fullname: str | None = None,
    ) -> Any:
        assert not owner_location(getattr(loader, "path", ""))
        assert fullname is None or not owner_module_name(fullname)
        return real_sourceless_load_module(loader, fullname)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    monkeypatch.setattr(
        importlib,
        "import_module",
        guarded_import_module,
    )
    monkeypatch.setattr(importlib, "reload", guarded_reload)
    monkeypatch.setattr(runpy, "run_module", guarded_run_module)
    monkeypatch.setattr(runpy, "run_path", guarded_run_path)
    monkeypatch.setattr(
        importlib.util,
        "spec_from_file_location",
        guarded_spec_from_file_location,
    )
    monkeypatch.setattr(
        source_loader,
        "exec_module",
        guarded_source_exec_module,
    )
    monkeypatch.setattr(
        source_loader,
        "load_module",
        guarded_source_load_module,
    )
    monkeypatch.setattr(
        sourceless_loader,
        "exec_module",
        guarded_sourceless_exec_module,
    )
    monkeypatch.setattr(
        sourceless_loader,
        "load_module",
        guarded_sourceless_load_module,
    )
    fresh_module = _fresh_role_module(
        "independent",
        "owner_sentinel_fresh_import",
    )
    fresh_api_actual = getattr(fresh_module, _INDEPENDENT_API)
    _assert_public_signature(fresh_api_actual)
    _assert_versioned_constants(fresh_module)
    _assert_independent_owner_boundary(fresh_module)
    _assert_no_owner_runtime_references(fresh_module)
    _assert_no_effect_sink_calls(fresh_module, _INDEPENDENT_API)
    fresh_api = _guard_api_read_only(
        fresh_api_actual,
        formal_owner_modules=pre_resolved_formal_owner_modules,
    )
    _assert_success_without_mutation(fresh_api, fixture)
    fresh_calls = _reachable_call_names(fresh_module, _INDEPENDENT_API)
    for call in fresh_calls:
        tail = call.rsplit(".", 1)[-1]
        assert call not in _FORBIDDEN_OWNER_TRUST_CALL_NAMES
        assert tail not in _FORBIDDEN_OWNER_TRUST_CALL_TAILS


def test_o03_source_subject_owner_independent_same_actual_git_root_head_tree_module_blob_raw() -> None:
    owner = _require_api("sequence", _OWNER_API, "O03")
    independent = _require_api("independent", _INDEPENDENT_API, "O03")
    parent = _require_api("parent", _PARENT_PHASE3_API, "O03")
    fixture = _connection_fixture()
    _assert_success_without_mutation(owner, fixture)
    _assert_success_without_mutation(independent, fixture)
    _assert_failure_without_mutation(
        parent,
        _parent_fixture(fixture),
        _PARENT_FAILURE,
    )
    root = _repository_root()
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    assert len(head) == 40 and len(tree) == 40
    _assert_module_actual_git_identity(
        owner,
        _MANDATORY_DIRECT_PATHS["sequence"],
    )
    _assert_module_actual_git_identity(
        independent,
        _MANDATORY_DIRECT_PATHS["independent"],
    )
    _assert_module_actual_git_identity(
        parent,
        _MANDATORY_DIRECT_PATHS["parent"],
    )
    _assert_executor_actual_git_identity(
        fixture["owner_executor"],
        api=owner,
        path=_MANDATORY_DIRECT_PATHS["sequence"],
    )
    _assert_executor_actual_git_identity(
        fixture["independent_executor"],
        api=independent,
        path=_MANDATORY_DIRECT_PATHS["independent"],
    )
    subject = fixture["source_subject"]
    for executor_name in ("owner_executor", "independent_executor"):
        executor = fixture[executor_name]
        for key in _SOURCE_SUBJECT_KEYS:
            assert executor[key] == subject[key]
    tamper_targets = [
        ("source_subject", field)
        for field in sorted(_SOURCE_SUBJECT_KEYS)
    ]
    tamper_targets.extend(
        (role, field)
        for role in ("owner_executor", "independent_executor")
        for field in (
            "module_path",
            "module_origin",
            "git_blob_sha1",
            "raw_sha256",
        )
    )
    for role, field in tamper_targets:
        tampered = _coherent_git_forgery(
            fixture,
            role=role,
            field=field,
        )
        _assert_failure_without_mutation(owner, tampered, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            tampered,
            _INDEPENDENT_FAILURE,
        )
        _assert_failure_without_mutation(
            parent,
            _parent_fixture(tampered),
            _PARENT_FAILURE,
        )
    for role in ("owner_executor", "independent_executor"):
        for field in sorted(_SOURCE_SUBJECT_KEYS):
            tampered = copy.deepcopy(fixture)
            original = tampered[role][field]
            if isinstance(original, bool):
                replacement: Any = not original
            elif field in {
                "head_commit_sha1",
                "head_tree_sha1",
                "origin_main_commit_sha1",
            }:
                replacement = "0" * 40
            else:
                replacement = f"{original}.mixed"
            tampered[role][field] = replacement
            tampered["operational_admission"]["predecessor_bindings"][
                "final_source_identity_contract_sha256"
            ] = _sha256_value(
                {
                    "source_subject": tampered["source_subject"],
                    "owner_executor": tampered["owner_executor"],
                    "independent_executor": tampered[
                        "independent_executor"
                    ],
                }
            )
            _rehash_admission_and_event(tampered)
            _assert_failure_without_mutation(
                owner,
                tampered,
                _OWNER_FAILURE,
            )
            _assert_failure_without_mutation(
                independent,
                tampered,
                _INDEPENDENT_FAILURE,
            )
            _assert_failure_without_mutation(
                parent,
                _parent_fixture(tampered),
                _PARENT_FAILURE,
            )
    cross_source_probes = [
        _coherent_artifact_source_forgery(
            fixture,
            field=field,
        )
        for field in ("head_commit_sha1", "head_tree_sha1")
    ]
    for scope_field in ("source_commit_sha1", "source_tree_sha1"):
        tampered = copy.deepcopy(fixture)
        tampered["operational_admission"]["scope"][
            scope_field
        ] = "0" * 40
        _rehash_admission_and_event(tampered)
        cross_source_probes.append(tampered)
    for freshness_field in (
        "bound_source_commit_sha1",
        "bound_source_tree_sha1",
    ):
        tampered = copy.deepcopy(fixture)
        tampered["operational_admission"]["freshness"][
            freshness_field
        ] = "0" * 40
        _rehash_admission_and_event(tampered)
        cross_source_probes.append(tampered)
    for source_field in ("source_commit_sha1", "source_tree_sha1"):
        tampered = copy.deepcopy(fixture)
        source = tampered["event1"]["source_closure"]
        source[source_field] = "0" * 40
        source["source_closure_sha256"] = _hash_without(
            source,
            "source_closure_sha256",
        )
        tampered["operational_admission"]["source_closure"] = (
            copy.deepcopy(source)
        )
        tampered["operational_admission"]["scope"][
            "source_closure_sha256"
        ] = source["source_closure_sha256"]
        tampered["event1"]["candidate_allocation"][
            "source_closure_sha256"
        ] = source["source_closure_sha256"]
        _rehash_admission_and_event(tampered)
        cross_source_probes.append(tampered)
    for bootstrap_field in ("source_commit_sha1", "source_tree_sha1"):
        tampered = copy.deepcopy(fixture)
        bootstrap = tampered["event1"]["bootstrap_closure"]
        bootstrap[bootstrap_field] = "0" * 40
        bootstrap["bootstrap_closure_sha256"] = _hash_without(
            bootstrap,
            "bootstrap_closure_sha256",
        )
        source = tampered["event1"]["source_closure"]
        source["bootstrap_closure_sha256"] = bootstrap[
            "bootstrap_closure_sha256"
        ]
        source["source_closure_sha256"] = _hash_without(
            source,
            "source_closure_sha256",
        )
        admission = tampered["operational_admission"]
        admission["bootstrap_closure"] = copy.deepcopy(bootstrap)
        admission["source_closure"] = copy.deepcopy(source)
        admission["scope"]["bootstrap_closure_sha256"] = bootstrap[
            "bootstrap_closure_sha256"
        ]
        admission["scope"]["source_closure_sha256"] = source[
            "source_closure_sha256"
        ]
        tampered["event1"]["candidate_allocation"][
            "source_closure_sha256"
        ] = source["source_closure_sha256"]
        _rehash_admission_and_event(tampered)
        cross_source_probes.append(tampered)
    for tampered in cross_source_probes:
        _assert_failure_without_mutation(owner, tampered, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            tampered,
            _INDEPENDENT_FAILURE,
        )
        _assert_failure_without_mutation(
            parent,
            _parent_fixture(tampered),
            _PARENT_FAILURE,
        )
    parent_source = _reachable_source(_module("parent"), _PARENT_PHASE3_API)
    for token in (
        "source_repository_root",
        "source_subject",
        "owner_executor",
        "independent_executor",
        "source_commit_sha1",
        "source_tree_sha1",
        "git_blob_sha1",
        "raw_sha256",
        "origin/main",
        "worktree_clean",
        "credit_eligible",
    ):
        assert token in parent_source


def test_o04_unknown_mixed_and_v2_to_v1_fallback_rejected_fail_closed() -> None:
    owner = _require_api("sequence", _OWNER_API, "O04")
    independent = _require_api("independent", _INDEPENDENT_API, "O04")
    parent = _require_api("parent", _PARENT_PHASE3_API, "O04")
    valid = _connection_fixture()
    _assert_success_without_mutation(owner, valid)
    _assert_success_without_mutation(independent, valid)
    v1_event = _module("sequence").RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA
    v1_admission = _module(
        "sequence"
    )._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA
    probes = (
        _connection_fixture(
            event_schema="cocolon.invalid.unknown_event.v99",
            admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
        ),
        _connection_fixture(
            event_schema=_EVENT_SCHEMA_V2,
            admission_schema="cocolon.invalid.unknown_admission.v99",
        ),
        _connection_fixture(
            event_schema=_EVENT_SCHEMA_V2,
            admission_schema=v1_admission,
        ),
        _connection_fixture(
            event_schema=v1_event,
            admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
        ),
        _connection_fixture(
            event_schema=_EVENT_SCHEMA_V2,
            admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
            candidate_schema="cocolon.invalid.mixed_candidate.v99",
        ),
        _connection_fixture(
            source_schema="cocolon.invalid.mixed_source_closure.v99",
        ),
        _connection_fixture(
            bootstrap_schema="cocolon.invalid.mixed_bootstrap.v99",
        ),
    )
    nested_schema_probes: list[dict[str, Any]] = []
    reference_body = copy.deepcopy(valid)
    reference_body["reference_runtime_observation"][
        "schema_version"
    ] = "cocolon.invalid.reference_body.v99"
    _rehash_reference_chain(reference_body)
    nested_schema_probes.append(reference_body)
    reference_identity = copy.deepcopy(valid)
    reference_identity[
        "reference_runtime_observation_external_identity"
    ]["schema_version"] = "cocolon.invalid.reference_identity.v99"
    _rehash_reference_chain(reference_identity)
    nested_schema_probes.append(reference_identity)
    admission_identity = copy.deepcopy(valid)
    admission_identity[
        "operational_admission_external_identity"
    ]["schema_version"] = "cocolon.invalid.admission_identity.v99"
    _rehash_admission_and_event(admission_identity)
    nested_schema_probes.append(admission_identity)
    nested_authority_identity = copy.deepcopy(valid)
    nested_authority = nested_authority_identity["event1"]["authority"][
        "operational_admission"
    ]
    nested_authority[
        "schema_version"
    ] = "cocolon.invalid.nested_authority_admission.v99"
    _rehash_external_identity(nested_authority)
    _rehash_event(nested_authority_identity)
    nested_schema_probes.append(nested_authority_identity)
    nested_primary_identity = copy.deepcopy(valid)
    nested_primary = nested_primary_identity["event1"][
        "primary_evidence_artifact"
    ]
    nested_primary[
        "schema_version"
    ] = "cocolon.invalid.nested_primary_admission.v99"
    _rehash_external_identity(nested_primary)
    _rehash_event(nested_primary_identity)
    nested_schema_probes.append(nested_primary_identity)
    for probe in (*probes, *nested_schema_probes):
        _assert_failure_without_mutation(owner, probe, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            probe,
            _INDEPENDENT_FAILURE,
        )
        _assert_failure_without_mutation(
            parent,
            _parent_fixture(probe),
            _PARENT_FAILURE,
        )
    fallback = copy.deepcopy(valid)
    fallback["allow_v1_fallback"] = True
    _assert_failure_without_mutation(owner, fallback, _OWNER_FAILURE)
    _assert_failure_without_mutation(
        independent,
        fallback,
        _INDEPENDENT_FAILURE,
    )
    _assert_failure_without_mutation(
        parent,
        _parent_fixture(fallback),
        _PARENT_FAILURE,
    )


def test_o05_event1_exact23_nests_distinct_candidate_and_consumes_oa_v2_exactly_once() -> None:
    owner = _require_api("sequence", _OWNER_API, "O05")
    independent = _require_api("independent", _INDEPENDENT_API, "O05")
    valid = _connection_fixture()
    _assert_success_without_mutation(owner, valid)
    _assert_success_without_mutation(independent, valid)
    owner_module = _module("sequence")
    independent_module = _module("independent")
    assert set(owner_module.RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS) == set(
        _EVENT_KEYS_ORDERED
    )
    assert set(
        owner_module._RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS
    ) == set(_CANDIDATE_KEYS_ORDERED)
    assert set(independent_module.RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS) == (
        set(_EVENT_KEYS_ORDERED)
    )
    assert set(
        independent_module._RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS
    ) == set(_CANDIDATE_KEYS_ORDERED)
    assert len(owner_module.RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS) == 23
    assert len(owner_module._RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS) == 9
    assert set(
        owner_module._RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_KEYS
    ) == set(_V1_ADMISSION_KEYS_ORDERED)
    assert set(
        independent_module._RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_KEYS
    ) == set(_V1_ADMISSION_KEYS_ORDERED)
    assert set(owner_module._RECOVERY_EPOCH004_PREDECESSOR_KEYS) == set(
        _V2_PREDECESSOR_KEYS_ORDERED
    )
    assert set(
        independent_module._RECOVERY_EPOCH004_PREDECESSOR_KEYS
    ) == set(_V2_PREDECESSOR_KEYS_ORDERED)
    assert _hash_without(
        _CURRENT_P0_EXTERNAL_IDENTITY,
        "p0_external_identity_sha256",
    ) == _CURRENT_P0_EXTERNAL_IDENTITY_SHA256
    assert _hash_without(
        _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY,
        "identity_sha256",
    ) == _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY_SHA256
    assert _CURRENT_P0_EXTERNAL_IDENTITY_SHA256 != (
        _OLD_PARTIAL_P0_EXTERNAL_IDENTITY_SHA256
    )
    event = valid["event1"]
    candidate = event["candidate_allocation"]
    publication = event["publication"]
    assert set(event) == set(_EVENT_KEYS_ORDERED)
    assert set(candidate) == set(_CANDIDATE_KEYS_ORDERED)
    assert len(event) == 23 and len(candidate) == 9
    assert candidate["candidate_version_id"] not in (
        valid["historical_candidate_version_ids"]
    )
    assert "candidate_allocation" not in valid
    assert event["p0_external_identity"] == (
        _CURRENT_P0_EXTERNAL_IDENTITY
    )
    assert candidate["p0_external_identity_sha256"] == (
        _CURRENT_P0_EXTERNAL_IDENTITY_SHA256
    )
    assert valid["operational_admission"]["predecessor_bindings"][
        "p0_external_identity"
    ] == _CURRENT_P0_EXTERNAL_IDENTITY
    assert valid["operational_admission"]["predecessor_bindings"][
        "epoch003_reconciliation_receipt_external_identity"
    ] == _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY
    assert valid["event1_consumption_count"] == 1
    assert valid["operational_admission"]["freshness"][
        "maximum_event1_consumption_count"
    ] == 1
    assert valid["operational_admission"]["freshness"][
        "reuse_allowed"
    ] is False
    assert publication["supporting_artifact_count"] == 2
    assert publication["expected_changed_path_count"] == 1
    assert event["primary_evidence_artifact"] == (
        valid["operational_admission_external_identity"]
    )
    assert valid["credit_eligible"] is False
    assert valid["verification_profile"] == _NON_CREDIT_FIXTURE_MARKER
    assert publication["publication_state"] == (
        "NON_CREDIT_CONTRACT_FIXTURE_NOT_PUBLISHED"
    )
    assert set(valid["later_effect_counts"].values()) == {0}
    assert valid["source_baseline_state"] == "UNLOCKED"
    assert valid["automatic_progression"] is False
    for module, api_name in (
        (owner_module, _OWNER_API),
        (independent_module, _INDEPENDENT_API),
    ):
        source = _reachable_source(module, api_name)
        for token in (
            "candidate_version_id",
            "candidate_allocation",
            "candidate_allocation_sha256",
            "historical_candidate_version_ids",
            "primary_evidence_artifact",
            "supporting_artifacts",
            "supporting_artifact_count",
            "expected_changed_path_count",
            "maximum_event1_consumption_count",
            "reuse_allowed",
            "automatic_progression",
            "event_sha256",
            "_RECOVERY_EPOCH004_P0_EXTERNAL_IDENTITY",
            "_RECOVERY_EPOCH004_RECONCILIATION_EXTERNAL_IDENTITY",
            "_RECOVERY_EPOCH004_HISTORICAL_CANDIDATE_VERSION_IDS",
            "credit_eligible",
        ):
            assert token in source
    rebuilt_invalid = [
        _connection_fixture(candidate_version_id=value)
        for value in _HISTORICAL_CANDIDATE_VERSION_IDS
    ]
    rebuilt_invalid.extend(
        [
            _connection_fixture(event1_consumption_count=0),
            _connection_fixture(event1_consumption_count=2),
            _connection_fixture(reuse_allowed=True),
            _connection_fixture(expected_changed_path_count=2),
            _connection_fixture(include_reference_support=False),
            _connection_fixture(automatic_progression=True),
        ]
    )
    for baseline_state in ("LOCKED", "UNKNOWN"):
        invalid = copy.deepcopy(valid)
        invalid["source_baseline_state"] = baseline_state
        rebuilt_invalid.append(invalid)
    for effect_key in sorted(_LATER_EFFECT_KEYS):
        invalid = copy.deepcopy(valid)
        invalid["later_effect_counts"][effect_key] = 1
        rebuilt_invalid.append(invalid)
    missing_effect = copy.deepcopy(valid)
    missing_effect["later_effect_counts"].pop(
        sorted(_LATER_EFFECT_KEYS)[0]
    )
    rebuilt_invalid.append(missing_effect)
    extra_effect = copy.deepcopy(valid)
    extra_effect["later_effect_counts"]["unexpected_effect"] = 0
    rebuilt_invalid.append(extra_effect)
    for duplicate_identity_key in (
        "operational_admission_external_identity",
        "reference_runtime_observation_external_identity",
    ):
        invalid = copy.deepcopy(valid)
        duplicate_identity = copy.deepcopy(
            invalid[duplicate_identity_key]
        )
        supporting = [duplicate_identity, copy.deepcopy(duplicate_identity)]
        invalid["event1"]["publication"][
            "supporting_artifacts"
        ] = supporting
        invalid["event1"]["publication"][
            "supporting_artifact_set_sha256"
        ] = _sha256_value(supporting)
        _rehash_event(invalid)
        rebuilt_invalid.append(invalid)
    primary_mixed = copy.deepcopy(valid)
    primary_mixed["event1"]["primary_evidence_artifact"] = copy.deepcopy(
        primary_mixed[
            "reference_runtime_observation_external_identity"
        ]
    )
    _rehash_event(primary_mixed)
    rebuilt_invalid.append(primary_mixed)
    authority_mixed = copy.deepcopy(valid)
    authority_mixed["event1"]["authority"][
        "operational_admission"
    ] = copy.deepcopy(
        authority_mixed[
            "reference_runtime_observation_external_identity"
        ]
    )
    _rehash_event(authority_mixed)
    rebuilt_invalid.append(authority_mixed)
    for historical_ids in (
        list(_HISTORICAL_CANDIDATE_VERSION_IDS[:-1]),
        [*_HISTORICAL_CANDIDATE_VERSION_IDS, "unexpected_candidate"],
        list(reversed(_HISTORICAL_CANDIDATE_VERSION_IDS)),
        [
            *_HISTORICAL_CANDIDATE_VERSION_IDS,
            _HISTORICAL_CANDIDATE_VERSION_IDS[0],
        ],
        [*_HISTORICAL_CANDIDATE_VERSION_IDS, _CANDIDATE_VERSION_ID],
    ):
        invalid = copy.deepcopy(valid)
        invalid["historical_candidate_version_ids"] = historical_ids
        rebuilt_invalid.append(invalid)
    for invalid in rebuilt_invalid:
        _assert_failure_without_mutation(owner, invalid, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            invalid,
            _INDEPENDENT_FAILURE,
        )
    for mutation in ("missing", "extra"):
        invalid = copy.deepcopy(valid)
        if mutation == "missing":
            invalid["event1"].pop("challenge_id")
        else:
            invalid["event1"]["unexpected"] = True
        _assert_failure_without_mutation(owner, invalid, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            invalid,
            _INDEPENDENT_FAILURE,
        )
    alternate_p0 = _alternate_p0_external_identity()
    alternate_reconciliation = (
        _alternate_reconciliation_external_identity()
    )
    coherent_forged_roots = (
        _connection_fixture(p0_external_identity=alternate_p0),
        _connection_fixture(
            reconciliation_external_identity=alternate_reconciliation
        ),
    )
    for invalid in coherent_forged_roots:
        _assert_failure_without_mutation(owner, invalid, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            invalid,
            _INDEPENDENT_FAILURE,
        )
    cross_binding_forgery: list[dict[str, Any]] = []
    event_p0 = copy.deepcopy(valid)
    event_p0["event1"]["p0_external_identity"] = copy.deepcopy(
        alternate_p0
    )
    event_p0["event1"]["prior_event"] = copy.deepcopy(alternate_p0)
    _rehash_event(event_p0)
    cross_binding_forgery.append(event_p0)
    candidate_p0 = copy.deepcopy(valid)
    candidate_p0["event1"]["candidate_allocation"][
        "p0_external_identity_sha256"
    ] = alternate_p0["p0_external_identity_sha256"]
    _rehash_event(candidate_p0)
    cross_binding_forgery.append(candidate_p0)
    admission_p0 = copy.deepcopy(valid)
    admission_p0["operational_admission"]["predecessor_bindings"][
        "p0_external_identity"
    ] = copy.deepcopy(alternate_p0)
    _rehash_admission_and_event(admission_p0)
    cross_binding_forgery.append(admission_p0)
    admission_reconciliation = copy.deepcopy(valid)
    admission_reconciliation["operational_admission"][
        "predecessor_bindings"
    ]["epoch003_reconciliation_receipt_external_identity"] = (
        copy.deepcopy(alternate_reconciliation)
    )
    _rehash_admission_and_event(admission_reconciliation)
    cross_binding_forgery.append(admission_reconciliation)
    source_p0 = copy.deepcopy(valid)
    source = source_p0["event1"]["source_closure"]
    source["epoch004_p0_external_identity_sha256"] = alternate_p0[
        "p0_external_identity_sha256"
    ]
    source["source_closure_sha256"] = _hash_without(
        source,
        "source_closure_sha256",
    )
    source_p0["operational_admission"]["source_closure"] = (
        copy.deepcopy(source)
    )
    source_p0["operational_admission"]["scope"][
        "source_closure_sha256"
    ] = source["source_closure_sha256"]
    source_p0["event1"]["candidate_allocation"][
        "source_closure_sha256"
    ] = source["source_closure_sha256"]
    _rehash_admission_and_event(source_p0)
    cross_binding_forgery.append(source_p0)
    for invalid in cross_binding_forgery:
        _assert_failure_without_mutation(owner, invalid, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            invalid,
            _INDEPENDENT_FAILURE,
        )


def test_o06_parent_phase3_reconstructs_actual_postfetch_and_calls_independent_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api = _require_api("parent", _PARENT_PHASE3_API, "O06")
    _assert_public_signature(api)
    assert api({}) == _PARENT_FAILURE
    module = _module("parent")
    independent_module = _module("independent")
    reconstruct_actual = getattr(module, _PARENT_RECONSTRUCT_API, None)
    if not callable(reconstruct_actual):
        pytest.fail(_CAUSAL_RED_SIGNATURES["O06"], pytrace=False)
    _assert_public_signature(reconstruct_actual)
    _assert_no_effect_sink_calls(module, _PARENT_RECONSTRUCT_API)
    reconstruct = _guard_api_read_only(reconstruct_actual)
    postfetch_verify_actual = getattr(
        module,
        _PARENT_POSTFETCH_VERIFY_API,
        None,
    )
    if not callable(postfetch_verify_actual):
        pytest.fail(_CAUSAL_RED_SIGNATURES["O06"], pytrace=False)
    _assert_public_signature(postfetch_verify_actual)
    _assert_no_effect_sink_calls(
        module,
        _PARENT_POSTFETCH_VERIFY_API,
    )
    postfetch_verify = _guard_api_read_only(postfetch_verify_actual)
    independent_actual = getattr(module, _INDEPENDENT_API)
    assert independent_actual is getattr(
        independent_module,
        _INDEPENDENT_API,
    )
    connection = _connection_fixture()
    state = _parent_fixture(connection)
    untrusted_direct = copy.deepcopy(connection)
    for key in (
        "reference_runtime_observation",
        "reference_runtime_observation_external_identity",
        "operational_admission",
        "operational_admission_external_identity",
        "event1",
        "source_subject",
        "owner_executor",
        "independent_executor",
    ):
        untrusted_direct[key] = {
            "poisoned_untrusted_direct_connection_slot": key,
        }
    state["event1_connection_state"] = untrusted_direct
    original = copy.deepcopy(state)
    reconstructed = reconstruct(state)
    assert reconstructed == connection
    assert reconstructed is not connection
    assert state == original
    assert postfetch_verify(state) is True
    assert state == original
    calls: list[dict[str, Any]] = []
    reconstruction_calls: list[dict[str, Any]] = []
    postfetch_calls: list[dict[str, Any]] = []
    credit_connection = copy.deepcopy(connection)
    credit_connection["verification_profile"] = (
        _ACTUAL_GIT_POSTFETCH_VERIFICATION_PROFILE
    )
    credit_connection["credit_eligible"] = True
    positive_state = copy.deepcopy(state)
    positive_state["verification_profile"] = (
        _ACTUAL_GIT_POSTFETCH_VERIFICATION_PROFILE
    )
    positive_state["credit_eligible"] = True
    positive_original = copy.deepcopy(positive_state)

    def reconstruction_spy(
        value: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        reconstruction_calls.append(copy.deepcopy(dict(value)))
        if isinstance(value, dict):
            value["automatic_progression"] = True
        return copy.deepcopy(credit_connection)

    def postfetch_spy(value: Mapping[str, Any]) -> bool:
        postfetch_calls.append(copy.deepcopy(dict(value)))
        if isinstance(value, dict):
            value["automatic_progression"] = True
        return True

    def independent_spy(value: Mapping[str, Any]) -> tuple[str, ...]:
        received = copy.deepcopy(dict(value))
        calls.append(received)
        if isinstance(value, dict):
            value["automatic_progression"] = True
        return ()

    assert hasattr(module, _INDEPENDENT_API)
    monkeypatch.setattr(
        module,
        _PARENT_RECONSTRUCT_API,
        reconstruction_spy,
    )
    monkeypatch.setattr(
        module,
        _PARENT_POSTFETCH_VERIFY_API,
        postfetch_spy,
    )
    monkeypatch.setattr(module, _INDEPENDENT_API, independent_spy)
    assert api(positive_state) == ()
    assert positive_state == positive_original
    assert reconstruction_calls == [positive_original]
    assert postfetch_calls == [positive_original]
    assert calls == [credit_connection]

    def postfetch_reject(value: Mapping[str, Any]) -> bool:
        postfetch_calls.append(copy.deepcopy(dict(value)))
        return False

    reconstruction_calls.clear()
    postfetch_calls.clear()
    calls.clear()
    monkeypatch.setattr(
        module,
        _PARENT_POSTFETCH_VERIFY_API,
        postfetch_reject,
    )
    _assert_failure_without_mutation(
        api,
        positive_state,
        _PARENT_FAILURE,
    )
    assert reconstruction_calls == [positive_original]
    assert postfetch_calls == [positive_original]
    assert calls == []

    def independent_reject(
        value: Mapping[str, Any],
    ) -> tuple[str, ...]:
        calls.append(copy.deepcopy(dict(value)))
        return _INDEPENDENT_FAILURE

    reconstruction_calls.clear()
    postfetch_calls.clear()
    calls.clear()
    monkeypatch.setattr(
        module,
        _PARENT_POSTFETCH_VERIFY_API,
        postfetch_spy,
    )
    monkeypatch.setattr(module, _INDEPENDENT_API, independent_reject)
    _assert_failure_without_mutation(
        api,
        positive_state,
        _PARENT_FAILURE,
    )
    assert reconstruction_calls == [positive_original]
    assert postfetch_calls == [positive_original]
    assert calls == [credit_connection]
    monkeypatch.setattr(
        module,
        _PARENT_RECONSTRUCT_API,
        reconstruct_actual,
    )
    monkeypatch.setattr(
        module,
        _PARENT_POSTFETCH_VERIFY_API,
        postfetch_verify_actual,
    )
    monkeypatch.setattr(module, _INDEPENDENT_API, independent_actual)
    assert _module_imports_name(
        module,
        imported_module=_MODULE_NAMES["independent"],
        imported_name=_INDEPENDENT_API,
    )
    source = _reachable_source(module, _PARENT_PHASE3_API)
    for token in (
        "parent_phase_evidence_state",
        "completed_phases",
        "phase_evidence",
        "CANDIDATE_ALLOCATED_WITH_EVENT1_PUBLISHED_AND_POSTVERIFIED",
        "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT",
        "published_body",
        "postfetch_body",
        "publication_commit_sha1",
        "git_blob_sha1",
        "raw_sha256",
        "logical_artifact_sha256",
        "identity_sha256",
        _OWNER_API,
        _INDEPENDENT_API,
        _PARENT_RECONSTRUCT_API,
        _PARENT_POSTFETCH_VERIFY_API,
        "deepcopy",
        "source_baseline_state_before",
        "LOCK_ONLY_AFTER_ACTUAL_EVENT1_POSTFETCH_VERIFICATION",
        "credit_eligible",
    ):
        assert token in source
    assert source.count(_INDEPENDENT_API) == 1
    api_source = inspect.getsource(inspect.unwrap(api))
    assert api_source.count(_PARENT_RECONSTRUCT_API) == 1
    assert (
        api_source.count(_PARENT_POSTFETCH_VERIFY_API) == 1
    )
    assert (
        "validate_recovery_epoch003_parent_phase_evidence_state"
        not in source
    )
    missing_phase = copy.deepcopy(state)
    missing_phase["parent_phase_evidence_state"]["completed_phases"].pop()
    missing_original = copy.deepcopy(missing_phase)
    assert reconstruct(missing_phase) is None
    assert postfetch_verify(missing_phase) is False
    assert missing_phase == missing_original
    calls.clear()
    _assert_failure_without_mutation(api, missing_phase, _PARENT_FAILURE)
    assert calls == []
    missing_postfetch = _parent_fixture(connection)
    del missing_postfetch["parent_phase_evidence_state"]["phase_evidence"][
        "event1"
    ]["postfetch_body"]
    missing_postfetch_original = copy.deepcopy(missing_postfetch)
    assert reconstruct(missing_postfetch) is None
    assert postfetch_verify(missing_postfetch) is False
    assert missing_postfetch == missing_postfetch_original
    calls.clear()
    _assert_failure_without_mutation(
        api,
        missing_postfetch,
        _PARENT_FAILURE,
    )
    assert calls == []
    mixed_postfetch = _parent_fixture(connection)
    mixed_postfetch["parent_phase_evidence_state"]["phase_evidence"][
        "operational_admission"
    ]["postfetch_body"]["automatic_progression"] = True
    mixed_postfetch_original = copy.deepcopy(mixed_postfetch)
    assert reconstruct(mixed_postfetch) is None
    assert postfetch_verify(mixed_postfetch) is False
    assert mixed_postfetch == mixed_postfetch_original
    calls.clear()
    _assert_failure_without_mutation(
        api,
        mixed_postfetch,
        _PARENT_FAILURE,
    )
    assert calls == []


def test_o07_missing_mixed_stale_identity_evidence_fail_closed_with_zero_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = _require_api("sequence", _OWNER_API, "O07")
    independent = _require_api("independent", _INDEPENDENT_API, "O07")
    parent = _require_api("parent", _PARENT_PHASE3_API, "O07")
    valid = _connection_fixture()
    valid_parent = _parent_fixture(valid)
    stale = copy.deepcopy(valid)
    stale["source_subject"]["head_commit_sha1"] = "0" * 40
    mixed = _connection_fixture(
        admission_schema=_module(
            "sequence"
        )._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA,
    )
    locked = copy.deepcopy(valid)
    locked["source_baseline_state"] = "LOCKED"
    later_effect = copy.deepcopy(valid)
    later_effect["later_effect_counts"][
        sorted(_LATER_EFFECT_KEYS)[0]
    ] = 1
    invalid_parent_states = (
        {},
        _parent_fixture(stale),
        _parent_fixture(mixed),
        _parent_fixture(locked),
        _parent_fixture(later_effect),
    )
    root = _repository_root(require_current_clean=True)
    role_modules = {
        "sequence": _module("sequence"),
        "independent": _module("independent"),
        "parent": _module("parent"),
    }
    formal_owner_modules: dict[str, ModuleType] = {}
    for path in _FORMAL_OWNER_PATHS:
        _assert_no_effect_aliases(root / path)
        _prepare_imports(root)
        formal_module = importlib.import_module(Path(path).stem)
        _assert_no_cached_effect_objects(formal_module)
        formal_owner_modules[path] = formal_module
    for role, api_name in (
        ("sequence", _OWNER_API),
        ("independent", _INDEPENDENT_API),
        ("parent", _PARENT_PHASE3_API),
    ):
        module = role_modules[role]
        _assert_no_effect_sink_calls(module, api_name)
        source = _reachable_source(module, api_name)
        assert "pytest.main" not in source
    before_repository = (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "rev-parse", "HEAD^{tree}"),
        _git(root, "status", "--porcelain", "--untracked-files=all"),
    )
    effect_calls: list[tuple[Any, ...]] = []

    def forbidden_effect(*args: Any, **kwargs: Any) -> Any:
        effect_calls.append((*args, kwargs))
        raise AssertionError("D1-frozen validator reached an effect sink")

    real_builtin_open = builtins.open
    real_io_open = io.open
    real_os_open = os.open

    def guarded_builtin_open(
        file: Any,
        mode: str = "r",
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if any(token in mode for token in ("a", "w", "x", "+")):
            return forbidden_effect(file, mode, *args, **kwargs)
        return real_builtin_open(file, mode, *args, **kwargs)

    def guarded_io_open(
        file: Any,
        mode: str = "r",
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if any(token in mode for token in ("a", "w", "x", "+")):
            return forbidden_effect(file, mode, *args, **kwargs)
        return real_io_open(file, mode, *args, **kwargs)

    def guarded_os_open(
        path: Any,
        flags: int,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        write_flags = (
            os.O_APPEND
            | os.O_CREAT
            | os.O_RDWR
            | os.O_TRUNC
            | os.O_WRONLY
        )
        if flags & write_flags:
            return forbidden_effect(path, flags, *args, **kwargs)
        return real_os_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_builtin_open)
    monkeypatch.setattr(io, "open", guarded_io_open)
    monkeypatch.setattr(os, "open", guarded_os_open)
    for name in (
        "write_bytes",
        "write_text",
        "touch",
        "mkdir",
        "unlink",
        "rename",
        "replace",
    ):
        monkeypatch.setattr(Path, name, forbidden_effect)
    for name in ("replace", "rename", "remove", "unlink"):
        monkeypatch.setattr(os, name, forbidden_effect)
    for name in (
        "copy",
        "copy2",
        "copyfile",
        "copytree",
        "move",
        "rmtree",
    ):
        monkeypatch.setattr(shutil, name, forbidden_effect)
    parent_module = role_modules["parent"]
    monkeypatch.setattr(
        parent_module,
        "execute_recovery_epoch003_current_strict_preflight_v1",
        forbidden_effect,
    )
    real_run = subprocess.run
    real_popen = subprocess.Popen
    real_posix_spawn = getattr(os, "posix_spawn", None)
    real_posix_spawnp = getattr(os, "posix_spawnp", None)
    trusted_git_executable = Path(shutil.which("git") or "").resolve()
    assert trusted_git_executable.is_file()
    trusted_popen_depth = [0]
    formal_paths = frozenset(_FORMAL_OWNER_PATHS)

    def sanitized_git_environment() -> dict[str, str]:
        environment = {
            key: value
            for key, value in os.environ.items()
            if not (
                key.startswith("GIT_")
                or key
                in {
                    "LD_AUDIT",
                    "LD_LIBRARY_PATH",
                    "LD_PRELOAD",
                    "PYTHONPATH",
                }
            )
        }
        environment.update(
            {
                "GIT_ATTR_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_EXTERNAL_DIFF": "",
                "GIT_OPTIONAL_LOCKS": "0",
                "GIT_PAGER": "cat",
                "GIT_TERMINAL_PROMPT": "0",
                "PATH": str(trusted_git_executable.parent),
            }
        )
        return environment

    def safe_ref(value: str) -> bool:
        return value in {"HEAD", "HEAD^{tree}", "origin/main"} or bool(
            len(value.removesuffix("^{tree}")) == 40
            and all(
                character in "0123456789abcdef"
                for character in value.removesuffix("^{tree}")
            )
        )

    def read_only_git_command(command: Any) -> bool:
        if not isinstance(command, (list, tuple)):
            return False
        argv = [str(value) for value in command]
        if not argv:
            return False
        executable = argv[0]
        if executable != "git":
            try:
                if Path(executable).resolve() != trusted_git_executable:
                    return False
            except (OSError, RuntimeError, TypeError, ValueError):
                return False
        args = argv[1:]
        if len(args) >= 2 and args[0] == "-C":
            try:
                if Path(args[1]).resolve() != root:
                    return False
            except (OSError, RuntimeError, TypeError, ValueError):
                return False
            args = args[2:]
        if args == ["remote", "get-url", "origin"]:
            return True
        if args == [
            "ls-remote",
            "--exit-code",
            "origin",
            "refs/heads/main",
        ]:
            return True
        if args == ["rev-parse", "--show-toplevel"]:
            return True
        if (
            len(args) == 2
            and args[0] == "rev-parse"
            and (
                safe_ref(args[1])
                or (
                    args[1].startswith("HEAD:")
                    and args[1][5:] in formal_paths
                )
            )
        ):
            return True
        if (
            len(args) == 4
            and args[:2] == ["merge-base", "--is-ancestor"]
            and safe_ref(args[2])
            and safe_ref(args[3])
        ):
            return True
        if (
            len(args) == 2
            and args[0] == "show"
            and args[1].startswith("HEAD:")
            and args[1][5:] in formal_paths
        ):
            return True
        if (
            len(args) == 2
            and args[0] == "hash-object"
            and args[1] in formal_paths
        ):
            return True
        if (
            len(args) == 3
            and args[:2] == ["ls-files", "--error-unmatch"]
            and args[2] in formal_paths
        ):
            return True
        return args in (
            ["status", "--porcelain", "--untracked-files=all"],
            ["symbolic-ref", "--quiet", "HEAD"],
        )

    def safe_process_options(
        command: Any,
        options: Mapping[str, Any],
    ) -> bool:
        argv = (
            [str(value) for value in command]
            if isinstance(command, (list, tuple))
            else []
        )
        root_bound_by_argv = bool(
            len(argv) >= 3
            and argv[1] == "-C"
            and Path(argv[2]).resolve() == root
        )
        cwd = options.get("cwd")
        try:
            cwd_valid = (
                cwd is not None and Path(cwd).resolve() == root
            ) or (cwd is None and root_bound_by_argv)
        except (OSError, RuntimeError, TypeError, ValueError):
            cwd_valid = False
        environment = options.get("env")
        environment_valid = (
            environment is None
            if argv and argv[0] == "git"
            else (
                type(environment) is dict
                and environment == sanitized_git_environment()
            )
        )
        allowed_streams = {
            None,
            subprocess.PIPE,
            subprocess.DEVNULL,
            subprocess.STDOUT,
        }
        return bool(
            cwd_valid
            and options.get("shell", False) is False
            and options.get("executable") is None
            and options.get("preexec_fn") is None
            and environment_valid
            and options.get("pass_fds", ()) == ()
            and options.get("close_fds", True) is True
            and options.get("start_new_session", False) is False
            and options.get("process_group", -1) in {-1, None}
            and options.get("user") is None
            and options.get("group") is None
            and options.get("extra_groups") is None
            and options.get("umask", -1) == -1
            and options.get("creationflags", 0) == 0
            and options.get("startupinfo") is None
            and options.get("stdin") in allowed_streams
            and options.get("stdout") in allowed_streams
            and options.get("stderr") in allowed_streams
        )

    def guarded_run(command: Any, *args: Any, **kwargs: Any) -> Any:
        if (
            args == ()
            and read_only_git_command(command)
            and safe_process_options(command, kwargs)
        ):
            return real_run(command, *args, **kwargs)
        return forbidden_effect(command, *args, **kwargs)

    def guarded_popen(*args: Any, **kwargs: Any) -> Any:
        command = args[0] if args else kwargs.get("args")
        positional_shape_valid = len(args) == 1 or (
            args == () and "args" in kwargs
        )
        if (
            positional_shape_valid
            and read_only_git_command(command)
            and safe_process_options(command, kwargs)
        ):
            trusted_popen_depth[0] += 1
            try:
                return real_popen(*args, **kwargs)
            finally:
                trusted_popen_depth[0] -= 1
        return forbidden_effect(*args, **kwargs)

    for name in (
        "compile",
        "eval",
        "exec",
    ):
        monkeypatch.setattr(builtins, name, forbidden_effect)
    for name in (
        "_exit",
        "execl",
        "execle",
        "execlp",
        "execlpe",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "popen",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "system",
    ):
        if hasattr(os, name):
            monkeypatch.setattr(os, name, forbidden_effect)
    if real_posix_spawn is not None:
        def guarded_posix_spawn(
            path: Any,
            argv: Any,
            env: Any,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            if (
                trusted_popen_depth[0] == 1
                and Path(os.fsdecode(path)).resolve()
                == trusted_git_executable
                and read_only_git_command(argv)
            ):
                return real_posix_spawn(
                    path,
                    argv,
                    env,
                    *args,
                    **kwargs,
                )
            return forbidden_effect(path, argv, env, *args, **kwargs)

    if real_posix_spawnp is not None:
        def guarded_posix_spawnp(
            path: Any,
            argv: Any,
            env: Any,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            if (
                trusted_popen_depth[0] == 1
                and (
                    os.fsdecode(path) == "git"
                    or Path(os.fsdecode(path)).resolve()
                    == trusted_git_executable
                )
                and read_only_git_command(argv)
            ):
                return real_posix_spawnp(
                    path,
                    argv,
                    env,
                    *args,
                    **kwargs,
                )
            return forbidden_effect(path, argv, env, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", guarded_run)
    monkeypatch.setattr(subprocess, "Popen", guarded_popen)
    if real_posix_spawn is not None:
        monkeypatch.setattr(os, "posix_spawn", guarded_posix_spawn)
    if real_posix_spawnp is not None:
        monkeypatch.setattr(os, "posix_spawnp", guarded_posix_spawnp)
    monkeypatch.setattr(runpy, "run_module", forbidden_effect)
    monkeypatch.setattr(runpy, "run_path", forbidden_effect)
    monkeypatch.setattr(importlib, "import_module", forbidden_effect)
    monkeypatch.setattr(importlib, "reload", forbidden_effect)
    monkeypatch.setattr(
        importlib.util,
        "module_from_spec",
        forbidden_effect,
    )
    monkeypatch.setattr(
        importlib.util,
        "spec_from_file_location",
        forbidden_effect,
    )
    for loader in (
        importlib.machinery.SourceFileLoader,
        importlib.machinery.SourcelessFileLoader,
    ):
        for name in ("exec_module", "get_code", "load_module"):
            monkeypatch.setattr(loader, name, forbidden_effect)
    for name in (
        "call",
        "check_call",
        "check_output",
        "getoutput",
        "getstatusoutput",
    ):
        monkeypatch.setattr(subprocess, name, forbidden_effect)
    monkeypatch.setattr(builtins, "__import__", forbidden_effect)
    before_module_state = _formal_owner_module_state_sha256(
        formal_owner_modules,
        root,
    )
    _assert_success_without_mutation(owner, valid)
    _assert_success_without_mutation(independent, valid)
    _assert_failure_without_mutation(
        parent,
        valid_parent,
        _PARENT_FAILURE,
    )
    for value in ({}, stale, mixed):
        _assert_failure_without_mutation(owner, value, _OWNER_FAILURE)
        _assert_failure_without_mutation(
            independent,
            value,
            _INDEPENDENT_FAILURE,
        )
    for value in invalid_parent_states:
        _assert_failure_without_mutation(parent, value, _PARENT_FAILURE)
    assert _formal_owner_module_state_sha256(
        formal_owner_modules,
        root,
    ) == before_module_state
    assert effect_calls == []
    monkeypatch.undo()
    after_repository = (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "rev-parse", "HEAD^{tree}"),
        _git(root, "status", "--porcelain", "--untracked-files=all"),
    )
    assert after_repository == before_repository


def test_o08_v1_exact16_exact8_and_predecessor_oracles_remain_immutable() -> None:
    assert _sha256_value(_ORACLE_NAMES) == _ORACLE_LIST_SHA256
    assert _sha256_value(_ORDERED_NODE_IDS) == _ORDERED_NODE_LIST_SHA256
    assert len(_ORACLE_NAMES) == len(_NODE_NAMES) == 8
    assert _D1_AUTHORITY.endswith("V1_EXACT16_EXACT8_INVARIANCE_CAUSAL_RED_FREEZE_ONLY")
    assert _D1_AUTHORITY_STATE == (
        "DEFINED_INACTIVE_SEPARATE_MASH_APPROVAL_REQUIRED"
    )
    assert _NON_CREDIT_FIXTURE_MARKER == (
        "MEMORY_ONLY_NON_CREDIT_CONTRACT_FIXTURE_NO_PUBLICATION_NO_EFFECT"
    )
    assert _hash_without(
        _CURRENT_P0_EXTERNAL_IDENTITY,
        "p0_external_identity_sha256",
    ) == _CURRENT_P0_EXTERNAL_IDENTITY_SHA256
    assert _hash_without(
        _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY,
        "identity_sha256",
    ) == _CURRENT_RECONCILIATION_EXTERNAL_IDENTITY_SHA256
    assert _CURRENT_P0_EXTERNAL_IDENTITY_SHA256 != (
        _OLD_PARTIAL_P0_EXTERNAL_IDENTITY_SHA256
    )
    assert len(_EVENT_KEYS_ORDERED) == 23
    assert len(_CANDIDATE_KEYS_ORDERED) == 9
    assert len(_V2_PREDECESSOR_KEYS_ORDERED) == 8
    assert len(_CONNECTION_STATE_KEYS) == 20
    assert len(_PARENT_STATE_KEYS) == 13
    assert len(_HISTORICAL_CANDIDATE_VERSION_IDS) == 5
    assert _CANDIDATE_VERSION_ID not in _HISTORICAL_CANDIDATE_VERSION_IDS
    assert _sha256_value(_V1_ADMISSION_KEYS_ORDERED) == (
        _V1_ADMISSION_KEYSET_SHA256
    )
    assert _sha256_value(_V1_PREDECESSOR_KEYS_ORDERED) == (
        _V1_PREDECESSOR_KEYSET_SHA256
    )
    root = _repository_root()
    loader_raw = (root / _CANONICAL_LOADER_PATH).read_bytes()
    assert hashlib.sha256(loader_raw).hexdigest() == (
        _CANONICAL_LOADER_RAW_SHA256
    )
    assert _git(root, "rev-parse", f"HEAD:{_CANONICAL_LOADER_PATH}") == (
        _CANONICAL_LOADER_BLOB_SHA1
    )
    for path, functions in _FUNCTION_SOURCE_HASHES.items():
        for name, expected in functions.items():
            assert _function_source_sha256(path, name) == expected
    for path, functions in _FUNCTION_CLOSURE_HASHES.items():
        for name, expected in functions.items():
            assert _function_closure_sha256(path, name) == expected
    for path, expected in _V1_SEMANTIC_SURFACE_HASHES.items():
        roots = tuple(_FUNCTION_SOURCE_HASHES[path])
        assert _semantic_surface_sha256(path, roots) == expected
        _assert_runtime_function_bindings(path, roots)
    assert _cross_module_semantic_surface_sha256(
        {
            path: tuple(functions)
            for path, functions in _FUNCTION_SOURCE_HASHES.items()
        }
    ) == _V1_CROSS_MODULE_SEMANTIC_SURFACE_SHA256
    for path, (expected_blob, expected_raw) in (
        _PREDECESSOR_TEST_IDENTITIES.items()
    ):
        raw = _git_bytes(root, "show", f"HEAD:{path}")
        assert _git(root, "rev-parse", f"HEAD:{path}") == expected_blob
        assert hashlib.sha256(raw).hexdigest() == expected_raw
    sequence = _module("sequence")
    independent = _module("independent")
    _assert_independent_owner_boundary(independent)
    _assert_no_owner_runtime_references(independent)
    formal_owner_modules: dict[str, ModuleType] = {}
    for path in _FORMAL_OWNER_PATHS:
        _assert_no_effect_aliases(root / path)
        _prepare_imports(root)
        formal_module = importlib.import_module(Path(path).stem)
        _assert_no_cached_effect_objects(formal_module)
        formal_owner_modules[path] = formal_module
    formal_owner_state = _formal_owner_module_state_sha256(
        formal_owner_modules,
        root,
    )
    assert _formal_owner_module_state_sha256(
        formal_owner_modules,
        root,
    ) == formal_owner_state
    assert sequence._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA == (
        "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
    )
    assert independent._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA == (
        "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
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
