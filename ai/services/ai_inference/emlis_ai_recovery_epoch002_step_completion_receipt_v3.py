# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 002 current-step completion receipt owner."""

from copy import deepcopy
import hashlib
from pathlib import Path, PurePosixPath
import stat
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS,
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256,
    RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_STEP_COMPLETION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "current_step_completion_receipt.v1"
)
RECOVERY_EPOCH002_STEP_COMPLETION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    step_number lineage current_binding actual_owners strict_contracts
    positive_proof independent_negative_proof artifact_receipt parent_binding
    completion_condition stop_conditions next_authority verdict
    automatic_progression body_free receipt_sha256
    """
)
RECOVERY_EPOCH002_STEP_CURRENT_BINDING_KEYS = _keys(
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
RECOVERY_EPOCH002_STEP_LINEAGE_KEYS = _keys(
    """
    kind historical_disposition historical_rewrite historical_as_current
    backfill
    """
)
RECOVERY_EPOCH002_STEP_ACTUAL_OWNER_KEYS = _keys(
    "path git_blob_sha1 sha256 symbol role"
)
RECOVERY_EPOCH002_STEP_STRICT_CONTRACT_KEYS = _keys(
    """
    contract_id schema_version validator_path validator_blob_sha1
    validator_symbol invariant_ids
    """
)
RECOVERY_EPOCH002_STEP_ARTIFACT_RECEIPT_KEYS = _keys(
    """
    schema_version step_number required_artifact_schema_version
    owner_binding_sha256 strict_contract_binding_sha256
    requirement_registry_sha256 accepted_test_run_receipt_sha256
    formal_completion_evidence_sha256 body_free
    """
)
RECOVERY_EPOCH002_STEP_PARENT_BINDING_KEYS = _keys(
    """
    parent_kind parent_step_number source_baseline_event_identity_sha256
    parent_receipt_sha256
    """
)
RECOVERY_EPOCH002_STEP_COMPLETION_CONDITION_KEYS = _keys(
    "condition_id required satisfied evidence_sha256"
)
RECOVERY_EPOCH002_STEP_STOP_CONDITION_KEYS = _keys(
    """
    condition_id proof_scope proof_node_registry_sha256
    accepted_test_run_receipt_sha256 triggered evidence_sha256
    """
)
RECOVERY_EPOCH002_STEP_COMPLETION_STATE_KEYS = _keys(
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
_OUTCOME_KEYS = _keys(
    """
    test_node_id source_path source_blob_sha1 source_sha256 result
    expected_closed_code actual_closed_code evidence_sha256
    """
)
_CANDIDATE_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 body_free
    """
)
_ARTIFACT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "current_step_artifact_evidence.v1"
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
_REPO_ROOT = Path(__file__).resolve().parents[3]
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


def _source_identity(path: str) -> dict[str, str] | None:
    if type(path) is not str or not path or "\\" in path:
        return None
    relative = PurePosixPath(path)
    if (
        relative.is_absolute()
        or relative.as_posix() != path
        or any(component in {".", ".."} for component in relative.parts)
    ):
        return None
    current = _REPO_ROOT
    for component in relative.parts:
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


def _accepted_valid(accepted: Any) -> bool:
    return (
        type(accepted) is dict
        and set(accepted) == _ACCEPTED_KEYS
        and accepted.get("schema_version")
        == (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "accepted_test_run_receipt.v1"
        )
        and accepted.get("accepted") is True
        and accepted.get("body_free") is True
        and accepted.get("automatic_progression") is False
        and accepted.get("accepted_test_run_receipt_sha256")
        == _hash_without(
            accepted,
            "accepted_test_run_receipt_sha256",
        )
    )


def _expected_owners(
    registry_row: Mapping[str, Any],
) -> list[dict[str, Any]] | None:
    owners: list[dict[str, Any]] = []
    for owner in registry_row["actual_owners"]:
        identity = _source_identity(owner["path"])
        if identity is None:
            return None
        owners.append(
            {
                "path": owner["path"],
                "git_blob_sha1": identity["git_blob_sha1"],
                "sha256": identity["sha256"],
                "symbol": owner["symbol"],
                "role": owner["role"],
            }
        )
    return owners


def _expected_contracts(
    registry_row: Mapping[str, Any],
) -> list[dict[str, Any]] | None:
    contracts: list[dict[str, Any]] = []
    for contract in registry_row["strict_contracts"]:
        identity = _source_identity(contract["validator_path"])
        if identity is None:
            return None
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
    return contracts


def _base_receipt_valid(receipt: Any, step: int) -> bool:
    lineage = receipt.get("lineage") if type(receipt) is dict else None
    return (
        type(receipt) is dict
        and set(receipt) == RECOVERY_EPOCH002_STEP_COMPLETION_KEYS
        and receipt.get("schema_version")
        == RECOVERY_EPOCH002_STEP_COMPLETION_SCHEMA
        and receipt.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and receipt.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        and receipt.get("step_number") == step
        and type(receipt.get("step_number")) is int
        and type(lineage) is dict
        and set(lineage) == RECOVERY_EPOCH002_STEP_LINEAGE_KEYS
        and lineage
        == {
            "kind": "current",
            "historical_disposition": "IMMUTABLE_NONCURRENT_EVIDENCE",
            "historical_rewrite": False,
            "historical_as_current": False,
            "backfill": False,
        }
        and receipt.get("verdict") == "PROVED"
        and receipt.get("automatic_progression") is False
        and receipt.get("body_free") is True
        and receipt.get("receipt_sha256")
        == _hash_without(receipt, "receipt_sha256")
    )


def _validate_recovery_epoch002_step_completion_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the current-only Step00–10 receipt chain."""

    if (
        type(state) is not dict
        or set(state) != RECOVERY_EPOCH002_STEP_COMPLETION_STATE_KEYS
    ):
        return ("ACCEPTED_TEST_RUN_RECEIPT_REQUIRED",)
    accepted = state.get("accepted_test_run_receipt")
    if not _accepted_valid(accepted):
        return ("ACCEPTED_TEST_RUN_RECEIPT_REQUIRED",)
    accepted_hash = accepted["accepted_test_run_receipt_sha256"]
    accepted_artifact = state.get("accepted_test_run_artifact")
    if (
        type(accepted_artifact) is not dict
        or set(accepted_artifact) != _CANDIDATE_KEYS
        or accepted_artifact
        != _candidate_identity(
            accepted,
            role="ACCEPTED_TEST_RUN_RECEIPT",
            path=_ACCEPTED_PATH,
            logical_hash_key="accepted_test_run_receipt_sha256",
        )
    ):
        return ("ACCEPTED_TEST_RUN_RECEIPT_REQUIRED",)

    receipts = state.get("receipts")
    receipt_artifacts = state.get("receipt_artifacts")
    if (
        state.get("ordered_steps") != list(range(11))
        or type(receipts) is not list
        or len(receipts) != 11
        or type(receipt_artifacts) is not list
        or len(receipt_artifacts) != 11
        or type(state.get("receipt_sha256s")) is not list
        or len(state["receipt_sha256s"]) != 11
        or any(
            not _base_receipt_valid(receipt, step)
            for step, receipt in enumerate(receipts)
        )
        or any(
            type(candidate) is not dict
            or set(candidate) != _CANDIDATE_KEYS
            or candidate
            != _candidate_identity(
                receipts[step],
                role="CURRENT_STEP_COMPLETION_RECEIPT",
                path=_STEP_PATHS[step],
                logical_hash_key="receipt_sha256",
            )
            for step, candidate in enumerate(receipt_artifacts)
        )
        or state.get("receipt_sha256s")
        != [receipt["receipt_sha256"] for receipt in receipts]
    ):
        return ("STEP_RECEIPT_CHAIN_INVALID",)

    success_lineage = accepted.get("success_lineage")
    event_identity = (
        success_lineage.get("source_baseline_event")
        if type(success_lineage) is dict
        else None
    )
    step0_parent = receipts[0].get("parent_binding")
    if (
        type(event_identity) is not dict
        or type(step0_parent) is not dict
        or set(step0_parent) != RECOVERY_EPOCH002_STEP_PARENT_BINDING_KEYS
        or step0_parent
        != {
            "parent_kind": "SOURCE_BASELINE_EVENT_AND_ACCEPTED",
            "parent_step_number": None,
            "source_baseline_event_identity_sha256": event_identity.get(
                "identity_sha256"
            ),
            "parent_receipt_sha256": accepted_hash,
        }
    ):
        return ("STEP00_PARENT_BINDING_INVALID",)
    if any(
        type(receipts[step].get("parent_binding")) is not dict
        or set(receipts[step]["parent_binding"])
        != RECOVERY_EPOCH002_STEP_PARENT_BINDING_KEYS
        or receipts[step]["parent_binding"]
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
        for step in range(1, 11)
    ):
        return ("STEP_PARENT_CHAIN_INVALID",)

    source_context = state.get("source_context")
    source_closure = (
        source_context.get("successor_source_closure")
        if type(source_context) is dict
        else None
    )
    terminal = state.get("terminal_result")
    accepted_terminal = accepted.get("formal_worker_terminal_result")
    if (
        type(source_context) is not dict
        or set(source_context) != _SOURCE_CONTEXT_KEYS
        or type(source_closure) is not dict
        or type(terminal) is not dict
        or type(accepted_terminal) is not dict
        or terminal != accepted_terminal
        or terminal.get("formal_worker_result_sha256")
        != accepted.get("formal_worker_result_sha256")
        or terminal.get("candidate_version_id")
        != accepted.get("candidate_version_id")
        or terminal.get("source_closure_sha256")
        != source_closure.get("source_closure_sha256")
        or accepted.get("proof_source_closure_sha256")
        != source_closure.get("proof_source_closure_sha256")
    ):
        return ("CURRENT_SOURCE_VIEW_ROOT_INVALID",)
    all_formal_nodes = [
        node_id
        for step in range(11)
        for node_id in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
    ]
    outcome_rows = terminal.get("outcomes")
    if (
        type(outcome_rows) is not list
        or [row.get("test_node_id") for row in outcome_rows]
        != all_formal_nodes
        or any(
            type(row) is not dict
            or set(row) != _OUTCOME_KEYS
            or row.get("evidence_sha256")
            != _hash_without(row, "evidence_sha256")
            for row in outcome_rows
        )
    ):
        return ("CURRENT_SOURCE_VIEW_ROOT_INVALID",)
    outcomes = {
        row.get("test_node_id"): row
        for row in outcome_rows
    }
    global_stop_ids = frozenset.intersection(
        *(
            frozenset(row["stop_condition_ids"])
            for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
        )
    )
    for step, receipt in enumerate(receipts):
        binding = receipt.get("current_binding")
        expected_binding = {
            "source_commit_sha1": source_closure.get("source_commit_sha1"),
            "source_tree_sha1": source_closure.get("source_tree_sha1"),
            "source_baseline_event_identity_sha256": event_identity.get(
                "identity_sha256"
            ),
            "successor_source_closure_sha256": source_closure.get(
                "source_closure_sha256"
            ),
            "canonical_current_closure_sha256": source_closure.get(
                "canonical_current_closure_sha256"
            ),
            "source_dependency_closure_sha256": source_closure.get(
                "source_dependency_closure_sha256"
            ),
            "proof_source_closure_sha256": accepted.get(
                "proof_source_closure_sha256"
            ),
            "requirement_registry_sha256": (
                RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
            ),
            "formal_node_registry_sha256": (
                RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
            ),
            "bootstrap_closure_sha256": source_closure.get(
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
            "full_graph_sha256": source_closure.get(
                "canonical_current_closure_sha256"
            ),
        }
        if (
            type(binding) is not dict
            or set(binding) != RECOVERY_EPOCH002_STEP_CURRENT_BINDING_KEYS
            or binding != expected_binding
        ):
            return ("CURRENT_SOURCE_VIEW_ROOT_INVALID",)

    for step, (receipt, registry_row) in enumerate(
        zip(
            receipts,
            RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS,
            strict=True,
        )
    ):
        owners = _expected_owners(registry_row)
        contracts = _expected_contracts(registry_row)
        artifact_receipt = receipt.get("artifact_receipt")
        if (
            owners is None
            or contracts is None
            or any(
                type(owner) is not dict
                or set(owner) != RECOVERY_EPOCH002_STEP_ACTUAL_OWNER_KEYS
                for owner in receipt.get("actual_owners", ())
            )
            or any(
                type(contract) is not dict
                or set(contract)
                != RECOVERY_EPOCH002_STEP_STRICT_CONTRACT_KEYS
                for contract in receipt.get("strict_contracts", ())
            )
            or receipt.get("actual_owners") != owners
            or receipt.get("strict_contracts") != contracts
            or type(artifact_receipt) is not dict
            or set(artifact_receipt)
            != RECOVERY_EPOCH002_STEP_ARTIFACT_RECEIPT_KEYS
            or artifact_receipt.get("schema_version")
            != _ARTIFACT_SCHEMA
            or artifact_receipt.get("step_number") != step
            or type(artifact_receipt.get("step_number")) is not int
            or artifact_receipt.get(
                "required_artifact_schema_version"
            )
            != registry_row["artifact_receipt_schema_version"]
            or artifact_receipt.get("owner_binding_sha256")
            != artifact_sha256(owners)
            or artifact_receipt.get("strict_contract_binding_sha256")
            != artifact_sha256(contracts)
            or artifact_receipt.get("requirement_registry_sha256")
            != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
            or artifact_receipt.get("accepted_test_run_receipt_sha256")
            != accepted_hash
            or artifact_receipt.get("body_free") is not True
        ):
            return ("STEP_OWNER_CONTRACT_BINDING_INVALID",)

        positive_node = registry_row["positive_proof"]["test_node_id"]
        positive = receipt.get("positive_proof")
        if (
            type(positive) is not dict
            or set(positive) != _OUTCOME_KEYS
            or positive != outcomes.get(positive_node)
            or positive.get("result") != "PASSED"
            or positive.get("evidence_sha256")
            != _hash_without(positive, "evidence_sha256")
        ):
            return ("POSITIVE_PROOF_OUTCOME_BINDING_INVALID",)

        negative_contract = registry_row["independent_negative_proof"]
        negative_node = negative_contract["test_node_id"]
        negative = receipt.get("independent_negative_proof")
        if (
            type(negative) is not dict
            or set(negative) != _OUTCOME_KEYS
            or negative != outcomes.get(negative_node)
            or negative.get("result") != "PASSED"
            or negative.get("expected_closed_code")
            != negative_contract["expected_closed_code"]
            or negative.get("actual_closed_code")
            != negative_contract["expected_closed_code"]
            or negative.get("evidence_sha256")
            != _hash_without(negative, "evidence_sha256")
        ):
            return ("NEGATIVE_PROOF_OBSERVED_CODE_BINDING_INVALID",)

        formal_nodes = list(
            RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
        )
        completion_hash = artifact_sha256(
            {
                "step_number": step,
                "formal_node_ids": formal_nodes,
                "outcome_evidence_sha256s": [
                    outcomes[node]["evidence_sha256"]
                    for node in formal_nodes
                ],
                "accepted_test_run_receipt_sha256": accepted_hash,
            }
        )
        completion = receipt.get("completion_condition")
        stops = receipt.get("stop_conditions")
        expected_stops: list[dict[str, Any]] = []
        for condition_id in registry_row["stop_condition_ids"]:
            is_global = condition_id in global_stop_ids
            proof_nodes = (
                all_formal_nodes
                if is_global
                else formal_nodes
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
            expected_stops.append(
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
        expected_next_authority = (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            f"SUCCESS_CANDIDATE_STEP{step + 1:02d}_"
            "GENERATION_SAME_APPROVED_PHASE"
            if step < 10
            else "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH002_"
            "SUCCESS_EXACT15_PUBLICATION_AND_POSTVERIFY_ONLY"
        )
        if (
            receipt.get("candidate_version_id")
            != accepted.get("candidate_version_id")
            or
            artifact_receipt.get("formal_completion_evidence_sha256")
            != completion_hash
            or type(completion) is not dict
            or set(completion)
            != RECOVERY_EPOCH002_STEP_COMPLETION_CONDITION_KEYS
            or completion.get("condition_id")
            != registry_row["completion_condition_ids"][0]
            or completion.get("required") is not True
            or completion.get("satisfied") is not True
            or completion.get("evidence_sha256") != completion_hash
            or type(stops) is not list
            or any(
                type(row) is not dict
                or set(row) != RECOVERY_EPOCH002_STEP_STOP_CONDITION_KEYS
                for row in stops
            )
            or stops != expected_stops
            or receipt.get("next_authority") != expected_next_authority
        ):
            return ("STEP_OWNER_CONTRACT_BINDING_INVALID",)
    return ()


def validate_recovery_epoch002_step_completion_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed Step00–10 owner state."""

    try:
        if _contains_forbidden_state_key(state):
            return ("STEP_RECEIPT_CHAIN_INVALID",)
        return _validate_recovery_epoch002_step_completion_state_impl(state)
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("STEP_RECEIPT_CHAIN_INVALID",)


__all__ = [
    "RECOVERY_EPOCH002_STEP_COMPLETION_SCHEMA",
    "RECOVERY_EPOCH002_STEP_COMPLETION_KEYS",
    "RECOVERY_EPOCH002_STEP_CURRENT_BINDING_KEYS",
    "RECOVERY_EPOCH002_STEP_LINEAGE_KEYS",
    "RECOVERY_EPOCH002_STEP_ACTUAL_OWNER_KEYS",
    "RECOVERY_EPOCH002_STEP_STRICT_CONTRACT_KEYS",
    "RECOVERY_EPOCH002_STEP_ARTIFACT_RECEIPT_KEYS",
    "RECOVERY_EPOCH002_STEP_PARENT_BINDING_KEYS",
    "RECOVERY_EPOCH002_STEP_COMPLETION_CONDITION_KEYS",
    "RECOVERY_EPOCH002_STEP_STOP_CONDITION_KEYS",
    "validate_recovery_epoch002_step_completion_state",
]
