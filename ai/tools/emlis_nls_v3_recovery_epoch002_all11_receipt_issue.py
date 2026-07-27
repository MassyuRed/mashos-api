# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 002 all-11 completion-chain owner."""

from copy import deepcopy
import hashlib
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256,
)
from emlis_ai_recovery_epoch002_step_completion_receipt_v3 import (
    validate_recovery_epoch002_step_completion_state,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_ALL11_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "all11_completion_chain.v1"
)
RECOVERY_EPOCH002_ALL11_COMPLETION_KEYS = _keys(
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
RECOVERY_EPOCH002_ALL11_REQUIRED_EVENT2_KEYS = _keys(
    """
    event_id event_name event_ordinal state prior_event_identity_sha256
    """
)
RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 body_free
    """
)
RECOVERY_EPOCH002_ALL11_COMPLETION_STATE_KEYS = _keys(
    """
    accepted_test_run_artifact accepted_test_run_receipt
    all11_completion_chain ordered_steps receipt_artifacts receipt_sha256s
    receipts source_context terminal_result
    """
)
_STEP_COMPLETION_STATE_KEYS = _keys(
    """
    accepted_test_run_artifact accepted_test_run_receipt ordered_steps
    receipt_artifacts receipt_sha256s receipts source_context
    terminal_result
    """
)
_SOURCE_CONTEXT_KEYS = _keys(
    """
    bootstrap_closure candidate_allocation event1_artifact event1_identity
    event1_postfetch_evidence readiness_artifact readiness_identity
    readiness_postfetch_evidence successful_reservation_artifact
    successful_reservation_identity
    successful_reservation_postfetch_evidence successor_source_closure
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
_ACCEPTED_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_AcceptedTestRunExact134_"
    "BodyFree_Receipt_20260726.json"
)
_STEP_PATHS = tuple(
    "EmlisAIの実装済み資料/documents/"
    f"NLSv3_Step11_Cycle001_RecoveryEpoch002_Step{step:02d}_"
    "CurrentStepCompletion_PROVED_BodyFree_Receipt_20260726.json"
    for step in range(11)
)
_FORBIDDEN_STATE_KEYS = frozenset(
    {
        "stdout", "stderr", "traceback", "exception_message",
        "free_form_reason", "raw_environment", "absolute_temporary_path",
        "pid", "hostname", "raw_body", "raw_payload", "generated_body",
        "private_body", "private_payload", "prompt_text", "response_text",
        "private_review_data", "secret", "credential",
        "invalid_result_sha256",
    }
)


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _contains_forbidden_state_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(key in _FORBIDDEN_STATE_KEYS for key in value) or any(
            _contains_forbidden_state_key(item) for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_state_key(item) for item in value)
    return False


def _candidate_identity(
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


def _validate_recovery_epoch002_all11_completion_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate accepted + exact11 current receipts as one frozen chain."""

    if (
        type(state) is not dict
        or set(state) != RECOVERY_EPOCH002_ALL11_COMPLETION_STATE_KEYS
    ):
        return ("ALL11_COMPLETION_CHAIN_INVALID",)
    chain = state.get("all11_completion_chain")
    accepted = state.get("accepted_test_run_receipt")
    receipts = state.get("receipts")
    receipt_artifacts = state.get("receipt_artifacts")
    receipt_hashes = state.get("receipt_sha256s")
    accepted_artifact = state.get("accepted_test_run_artifact")
    expected_accepted_artifact = _candidate_identity(
        accepted,
        role="ACCEPTED_TEST_RUN_RECEIPT",
        path=_ACCEPTED_PATH,
        logical_hash_key="accepted_test_run_receipt_sha256",
    )
    if (
        type(chain) is not dict
        or set(chain) != RECOVERY_EPOCH002_ALL11_COMPLETION_KEYS
        or chain.get("schema_version")
        != RECOVERY_EPOCH002_ALL11_COMPLETION_SCHEMA
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
        or type(receipt_artifacts) is not list
        or len(receipt_artifacts) != 11
        or type(receipt_hashes) is not list
        or len(receipt_hashes) != 11
        or state.get("ordered_steps") != list(range(11))
        or chain.get("receipt_count") != 11
        or type(chain.get("receipt_count")) is not int
        or chain.get("ordered_steps") != list(range(11))
        or chain.get("receipts") != receipts
        or chain.get("receipt_artifacts") != receipt_artifacts
        or chain.get("receipt_sha256s") != receipt_hashes
        or receipt_hashes
        != [receipt.get("receipt_sha256") for receipt in receipts]
        or any(
            type(receipt) is not dict
            or set(receipt) != _STEP_KEYS
            or receipt.get("step_number") != step
            or receipt.get("receipt_sha256")
            != _hash_without(receipt, "receipt_sha256")
            for step, receipt in enumerate(receipts)
        )
        or any(
            type(identity) is not dict
            or set(identity)
            != RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS
            or identity
            != _candidate_identity(
                receipts[step],
                role="CURRENT_STEP_COMPLETION_RECEIPT",
                path=_STEP_PATHS[step],
                logical_hash_key="receipt_sha256",
            )
            for step, identity in enumerate(receipt_artifacts)
        )
        or type(accepted_artifact) is not dict
        or set(accepted_artifact)
        != RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS
        or accepted_artifact != expected_accepted_artifact
        or chain.get("accepted_test_run_artifact")
        != accepted_artifact
        or chain.get("accepted_test_run_receipt_sha256")
        != accepted.get("accepted_test_run_receipt_sha256")
        or chain.get("accepted_test_run_artifact", {}).get(
            "logical_artifact_sha256"
        )
        != accepted.get("accepted_test_run_receipt_sha256")
        or chain.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or chain.get("registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
        or chain.get("formal_node_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
    ):
        return ("ALL11_COMPLETION_CHAIN_INVALID",)

    success_lineage = accepted.get("success_lineage")
    event_identity = (
        success_lineage.get("source_baseline_event")
        if type(success_lineage) is dict
        else None
    )
    source_context = state.get("source_context")
    source_closure = (
        source_context.get("successor_source_closure")
        if type(source_context) is dict
        else None
    )
    required_event2 = chain.get("required_sequence_event_2")
    accepted_hash = accepted.get("accepted_test_run_receipt_sha256")
    if (
        type(source_context) is not dict
        or set(source_context) != _SOURCE_CONTEXT_KEYS
        or type(source_closure) is not dict
        or type(event_identity) is not dict
        or chain.get("source_baseline_event") != event_identity
        or chain.get("source_closure") != source_closure
        or any(
            receipt.get("candidate_version_id")
            != accepted.get("candidate_version_id")
            or receipt.get("current_binding", {}).get(
                "source_baseline_event_identity_sha256"
            )
            != event_identity.get("identity_sha256")
            or receipt.get("current_binding", {}).get(
                "successor_source_closure_sha256"
            )
            != source_closure.get("source_closure_sha256")
            or receipt.get("current_binding", {}).get(
                "accepted_test_run_receipt_sha256"
            )
            != accepted_hash
            or receipt.get("parent_binding", {}).get(
                "parent_receipt_sha256"
            )
            != (
                accepted_hash
                if step == 0
                else receipts[step - 1].get("receipt_sha256")
            )
            for step, receipt in enumerate(receipts)
        )
        or type(required_event2) is not dict
        or set(required_event2)
        != RECOVERY_EPOCH002_ALL11_REQUIRED_EVENT2_KEYS
        or required_event2
        != {
            "event_id": "recovery_epoch002_event_02",
            "event_name": "STEP0_10_PREREQUISITES_PROVED",
            "event_ordinal": 2,
            "state": "STEP0_10_PREREQUISITES_PROVED",
            "prior_event_identity_sha256": event_identity.get(
                "identity_sha256"
            ),
        }
        or chain.get("publication_state") != "PUBLISHED_ATOMIC"
    ):
        return ("ALL11_COMPLETION_CHAIN_INVALID",)

    if (
        chain.get("next_authority")
        != (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            "P2_SEPARATE_APPROVAL_ONLY"
        )
        or any(
            receipt.get("lineage")
            != {
                "kind": "current",
                "historical_disposition": "IMMUTABLE_NONCURRENT_EVIDENCE",
                "historical_rewrite": False,
                "historical_as_current": False,
                "backfill": False,
            }
            for receipt in receipts
        )
    ):
        return ("EPOCH001_CREDIT_BACKFILL_OR_P2_FORBIDDEN",)
    step_state = {
        key: state[key] for key in _STEP_COMPLETION_STATE_KEYS
    }
    if validate_recovery_epoch002_step_completion_state(step_state) != ():
        return ("ALL11_COMPLETION_CHAIN_INVALID",)
    return ()


def validate_recovery_epoch002_all11_completion_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed all11 chain state."""

    try:
        if _contains_forbidden_state_key(state):
            return ("ALL11_COMPLETION_CHAIN_INVALID",)
        return _validate_recovery_epoch002_all11_completion_state_impl(state)
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("ALL11_COMPLETION_CHAIN_INVALID",)


__all__ = [
    "RECOVERY_EPOCH002_ALL11_COMPLETION_SCHEMA",
    "RECOVERY_EPOCH002_ALL11_COMPLETION_KEYS",
    "RECOVERY_EPOCH002_ALL11_REQUIRED_EVENT2_KEYS",
    "RECOVERY_EPOCH002_ATOMIC_SUCCESS_CANDIDATE_IDENTITY_KEYS",
    "validate_recovery_epoch002_all11_completion_state",
]
