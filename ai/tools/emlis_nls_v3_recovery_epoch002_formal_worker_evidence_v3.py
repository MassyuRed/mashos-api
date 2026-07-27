#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Durable, body-free formal-worker evidence for Recovery Epoch 002."""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import secrets
import stat
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS,
    RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT = (
    "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
)


RECOVERY_EPOCH002_PREFLIGHT_CHECKPOINT_KEYS = _keys(
    """
    schema_version phase logical_cycle_id recovery_epoch_id authority_token_id
    event1_challenge_id preflight_challenge_id preflight_id
    candidate_version_id source_baseline_event_sha256 source_closure_sha256
    bootstrap_closure_sha256 checkpoint_ordinal stage_enum
    prior_checkpoint_sha256 observed_at_utc body_free checkpoint_sha256
    """
)
RECOVERY_EPOCH002_FORMAL_CHECKPOINT_KEYS = _keys(
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
RECOVERY_EPOCH002_TERMINAL_RESULT_KEYS = _keys(
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
    """
)
RECOVERY_EPOCH002_DIAGNOSTIC_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id authority_token_id
    event1_challenge_id preflight_challenge_id formal_run_challenge_id
    formal_authority_challenge_id preflight_id attempt_id reservation_ordinal
    process_start_observed exit_class exit_code signal_number
    checkpoint_status last_valid_stage terminal_result_status
    valid_result_identity_sha256 stop_code body_free diagnostic_sha256
    """
)
RECOVERY_EPOCH002_UNKNOWN_DISPOSITION_KEYS = _keys(
    """
    schema_version reservation_artifact attempt_id checkpoint_status
    last_valid_stage terminal_result_status exit_class exit_code signal_number
    stop_code automatic_retry body_free
    attempt_consumption_unknown_disposition_sha256
    """
)

# Post-D2 success evidence is additive.  These contracts validate supplied
# body-free observations only; they do not execute pytest or publish an
# artifact.
RECOVERY_EPOCH002_TERMINAL_RESULT_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_terminal_result.v2"
)
RECOVERY_EPOCH002_TERMINAL_RESULT_V2_KEYS = _keys(
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
RECOVERY_EPOCH002_FORMAL_NODE_OUTCOME_KEYS = _keys(
    """
    test_node_id source_path source_blob_sha1 source_sha256 result
    expected_closed_code actual_closed_code evidence_sha256
    """
)
RECOVERY_EPOCH002_FORMAL_RESULT_COUNTS_KEYS = _keys(
    """
    collected executed passed failed errors skipped xfailed xpassed deselected
    collection_errors
    """
)
RECOVERY_EPOCH002_FORMAL_NODE_IDS = tuple(
    node_id
    for step in range(11)
    for node_id in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
)
RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE = {
    row["independent_negative_proof"]["test_node_id"]: (
        row["independent_negative_proof"]["expected_closed_code"]
    )
    for row in RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
}
RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODES = tuple(
    RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE[node_id]
    for node_id in RECOVERY_EPOCH002_FORMAL_NODE_IDS
    if node_id in RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE
)
RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH = {
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
RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS = frozenset(
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
_SUCCESS_FORBIDDEN_STATE_KEYS = (
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS
    | frozenset({"raw_payload", "private_body", "private_payload"})
)
RECOVERY_EPOCH002_SUCCESS_TERMINAL_STATE_KEYS = _keys(
    """
    reflection_contract_version checkpoint_chain independent_issue_codes
    locked_formal_node_ids
    locked_negative_code_by_node locked_source_manifest owner_issue_codes
    parity_bindings retry_history runner_closed_code_observations
    terminal_publication terminal_result
    """
)
RECOVERY_EPOCH002_SUCCESS_RETRY_HISTORY_KEYS = _keys(
    """
    consumed_attempt_ids successful_attempt_id
    successful_reservation_ordinal
    """
)
RECOVERY_EPOCH002_SUCCESS_PARITY_BINDING_KEYS = _keys(
    """
    bootstrap_closure_sha256 event1_candidate_version_id
    pytest_distribution_identity_sha256 python_runtime_identity_sha256
    readiness_candidate_version_id reservation_candidate_version_id
    source_closure_sha256
    """
)

_PREFLIGHT_CHECKPOINT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_preflight_checkpoint.v1"
)
_FORMAL_CHECKPOINT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.formal_worker_checkpoint.v1"
)
_TERMINAL_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_terminal_result.v1"
)
_DIAGNOSTIC_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.formal_worker_diagnostic.v1"
)
_UNKNOWN_DISPOSITION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "attempt_consumption_unknown_disposition.v1"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_SECONDS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
_AUTHORITATIVE_FORMAL_NODE_IDS = tuple(
    node
    for step in range(11)
    for node in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
)


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        if any(
            key in _SUCCESS_FORBIDDEN_STATE_KEYS
            for key in value
        ):
            return True
        return any(_contains_forbidden_key(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def validate_recovery_epoch002_checkpoint_chain(
    checkpoints: Sequence[Mapping[str, Any]],
    *,
    allow_prefix: bool = True,
) -> tuple[str, ...]:
    """Validate exact keys, self hashes, ordinals, and graph transitions."""

    if type(checkpoints) is not list or not checkpoints:
        return ("CHECKPOINT_INVALID",)
    prior_hash: str | None = None
    prior_stage: str | None = None
    chain_phase: str | None = None
    chain_binding: tuple[Any, ...] | None = None
    for ordinal, row in enumerate(checkpoints, start=1):
        if type(row) is not dict:
            return ("CHECKPOINT_INVALID",)
        phase = row.get("phase")
        if phase not in {"PREFLIGHT", "FORMAL_RUN"}:
            return ("CHECKPOINT_INVALID",)
        expected_keys = (
            RECOVERY_EPOCH002_PREFLIGHT_CHECKPOINT_KEYS
            if phase == "PREFLIGHT"
            else RECOVERY_EPOCH002_FORMAL_CHECKPOINT_KEYS
        )
        expected_schema = (
            _PREFLIGHT_CHECKPOINT_SCHEMA
            if phase == "PREFLIGHT"
            else _FORMAL_CHECKPOINT_SCHEMA
        )
        if set(row) != expected_keys:
            return ("CHECKPOINT_INVALID",)
        if row.get("schema_version") != expected_schema:
            return ("CHECKPOINT_INVALID",)
        if chain_phase is None:
            chain_phase = phase
        elif phase != chain_phase:
            return ("CHECKPOINT_INVALID",)
        binding_names = (
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
        )
        if phase == "FORMAL_RUN":
            binding_names = (
                *binding_names,
                "formal_run_challenge_id",
                "formal_authority_challenge_id",
                "attempt_id",
                "reservation_ordinal",
                "formal_test_run_reservation_sha256",
            )
        binding = tuple(row.get(name) for name in binding_names)
        if chain_binding is None:
            chain_binding = binding
        elif binding != chain_binding:
            return ("CHECKPOINT_INVALID",)
        if (
            type(row.get("checkpoint_ordinal")) is not int
            or row.get("checkpoint_ordinal") != ordinal
            or row.get("prior_checkpoint_sha256") != prior_hash
            or row.get("body_free") is not True
            or row.get("checkpoint_sha256")
            != _hash_without(row, "checkpoint_sha256")
        ):
            return ("CHECKPOINT_INVALID",)
        stage = row.get("stage_enum")
        if not isinstance(stage, str):
            return ("CHECKPOINT_INVALID",)
        if prior_stage is None:
            if phase == "FORMAL_RUN" and stage != (
                "PARENT_SPAWN_INTENT_PERSISTED"
            ):
                return ("CHECKPOINT_INVALID",)
        elif stage not in RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH.get(
            prior_stage,
            (),
        ):
            return ("CHECKPOINT_INVALID",)
        prior_hash = row["checkpoint_sha256"]
        prior_stage = stage
    if not allow_prefix and prior_stage != "TERMINAL_RESULT_PERSISTED":
        return ("CHECKPOINT_INVALID",)
    return ()


def validate_recovery_epoch002_terminal_result(
    result: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(result) is not dict:
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    if set(result) != RECOVERY_EPOCH002_TERMINAL_RESULT_KEYS:
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    if (
        result.get("schema_version") != _TERMINAL_RESULT_SCHEMA
        or result.get("body_free") is not True
        or result.get("formal_worker_result_sha256")
        != _hash_without(result, "formal_worker_result_sha256")
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    collected = result.get("collection_node_ids")
    executed = result.get("executed_node_ids")
    states = result.get("states")
    allowed_states = {"PASSED", "FAILED", "SKIPPED", "XFAILED", "XPASSED"}
    collection_errors = result.get("collection_errors")
    exit_class = result.get("exit_class")
    exit_code = result.get("exit_code")
    signal_number = result.get("signal_number")
    timed_out = result.get("timed_out")
    if (
        type(collected) is not list
        or type(executed) is not list
        or type(states) is not dict
        or any(not isinstance(node, str) or not node for node in collected)
        or any(not isinstance(node, str) or not node for node in executed)
        or len(collected) != len(set(collected))
        or len(executed) != len(set(executed))
        or set(states) != set(executed)
        or any(node not in collected for node in executed)
        or any(
            not isinstance(state, str) or state not in allowed_states
            for state in states.values()
        )
        or type(collection_errors) is not int
        or type(collection_errors) is bool
        or collection_errors < 0
        or exit_class not in {"EXITED", "SIGNALED", "TIMED_OUT"}
        or type(timed_out) is not bool
        or (
            exit_class == "EXITED"
            and (
                type(exit_code) is not int
                or type(exit_code) is bool
                or signal_number is not None
                or timed_out is not False
            )
        )
        or (
            exit_class == "SIGNALED"
            and (
                exit_code is not None
                or type(signal_number) is not int
                or type(signal_number) is bool
                or signal_number <= 0
                or timed_out is not False
            )
        )
        or (
            exit_class == "TIMED_OUT"
            and (
                exit_code is not None
                or signal_number is not None
                or timed_out is not True
            )
        )
        or (
            collection_errors == 0
            and (
                len(collected) != 134
                or executed != collected
            )
        )
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    return ()


def _utc_seconds(value: Any) -> datetime | None:
    if not isinstance(value, str) or _UTC_SECONDS_RE.fullmatch(value) is None:
        return None
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _ordered_authoritative_subset(nodes: Any) -> bool:
    if type(nodes) is not list:
        return False
    positions_by_node = {
        node: position
        for position, node in enumerate(_AUTHORITATIVE_FORMAL_NODE_IDS)
    }
    positions = [positions_by_node.get(node) for node in nodes]
    return (
        all(position is not None for position in positions)
        and positions == sorted(positions)
    )


def validate_recovery_epoch002_operational_terminal_result(
    result: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate a terminal result identically at write, parent, and publish."""

    if (
        type(result) is dict
        and result.get("schema_version")
        == RECOVERY_EPOCH002_TERMINAL_RESULT_V2_SCHEMA
    ):
        if not _success_terminal_shape_valid(result):
            return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
        v1_result = {
            key: deepcopy(value)
            for key, value in result.items()
            if key in RECOVERY_EPOCH002_TERMINAL_RESULT_KEYS
        }
        v1_result["schema_version"] = _TERMINAL_RESULT_SCHEMA
        v1_result["formal_worker_result_sha256"] = _hash_without(
            v1_result,
            "formal_worker_result_sha256",
        )
        generic_issues = validate_recovery_epoch002_terminal_result(
            v1_result
        )
    else:
        generic_issues = validate_recovery_epoch002_terminal_result(result)
    if generic_issues:
        return generic_issues
    if (
        len(_AUTHORITATIVE_FORMAL_NODE_IDS) != 134
        or len(set(_AUTHORITATIVE_FORMAL_NODE_IDS)) != 134
        or not _ordered_authoritative_subset(
            result.get("collection_node_ids")
        )
        or not _ordered_authoritative_subset(
            result.get("executed_node_ids")
        )
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)

    started = _utc_seconds(result.get("started_at_utc"))
    finished = _utc_seconds(result.get("finished_at_utc"))
    states = result["states"]
    collection_errors = result["collection_errors"]
    exit_code = result["exit_code"]
    if (
        result.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or result.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not isinstance(result.get("candidate_version_id"), str)
        or not result.get("candidate_version_id")
        or result.get("candidate_version_id") == "nls_v3_rc_0034"
        or any(
            _SHA256_RE.fullmatch(str(result.get(key, ""))) is None
            for key in (
                "authority_token_id",
                "event1_challenge_id",
                "formal_run_challenge_id",
                "formal_authority_challenge_id",
                "attempt_id",
                "source_baseline_event_sha256",
                "source_closure_sha256",
                "bootstrap_closure_sha256",
                "formal_test_run_reservation_sha256",
                "terminal_checkpoint_sha256",
                "python_runtime_identity_sha256",
                "pytest_distribution_identity_sha256",
            )
        )
        or result.get("exit_class") != "EXITED"
        or type(exit_code) is not int
        or type(exit_code) is bool
        or exit_code not in {0, 1, 2, 3, 5}
        or result.get("signal_number") is not None
        or result.get("timed_out") is not False
        or started is None
        or finished is None
        or started > finished
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)

    failed_count = sum(state == "FAILED" for state in states.values())
    if (
        (
            collection_errors > 0
            and (exit_code not in {2, 5} or states)
        )
        or (
            collection_errors == 0
            and (
                (exit_code == 0 and failed_count != 0)
                or (exit_code == 1 and failed_count == 0)
                or exit_code in {2, 5}
                or result.get("collection_node_ids")
                != list(_AUTHORITATIVE_FORMAL_NODE_IDS)
                or result.get("executed_node_ids")
                != list(_AUTHORITATIVE_FORMAL_NODE_IDS)
            )
        )
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    return ()


def _exit_observation_valid(
    *,
    exit_class: Any,
    exit_code: Any,
    signal_number: Any,
) -> bool:
    if exit_class == "EXITED":
        return (
            type(exit_code) is int
            and signal_number is None
        )
    if exit_class == "SIGNALED":
        return (
            exit_code is None
            and type(signal_number) is int
            and signal_number > 0
        )
    if exit_class in {"TIMED_OUT", "SPAWN_FAILED", "UNKNOWN"}:
        return exit_code is None and signal_number is None
    return False


def validate_recovery_epoch002_diagnostic(
    diagnostic: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the exact22 closed, body-free diagnostic artifact."""

    if (
        type(diagnostic) is not dict
        or set(diagnostic) != RECOVERY_EPOCH002_DIAGNOSTIC_KEYS
        or diagnostic.get("schema_version") != _DIAGNOSTIC_SCHEMA
        or _contains_forbidden_key(diagnostic)
        or diagnostic.get("body_free") is not True
        or diagnostic.get("diagnostic_sha256")
        != _hash_without(diagnostic, "diagnostic_sha256")
    ):
        return ("DIAGNOSTIC_INVALID",)
    identifier_names = (
        "logical_cycle_id",
        "recovery_epoch_id",
        "authority_token_id",
        "event1_challenge_id",
        "preflight_challenge_id",
        "formal_run_challenge_id",
        "formal_authority_challenge_id",
        "preflight_id",
        "attempt_id",
        "stop_code",
    )
    if (
        any(
            not isinstance(diagnostic.get(name), str)
            or not diagnostic.get(name)
            for name in identifier_names
        )
        or any(
            _SHA256_RE.fullmatch(str(diagnostic.get(name, ""))) is None
            for name in (
                "event1_challenge_id",
                "preflight_challenge_id",
                "formal_run_challenge_id",
                "formal_authority_challenge_id",
                "preflight_id",
                "attempt_id",
            )
        )
        or type(diagnostic.get("reservation_ordinal")) is not int
        or diagnostic.get("reservation_ordinal") <= 0
        or type(diagnostic.get("process_start_observed")) is not bool
        or not _exit_observation_valid(
            exit_class=diagnostic.get("exit_class"),
            exit_code=diagnostic.get("exit_code"),
            signal_number=diagnostic.get("signal_number"),
        )
        or diagnostic.get("checkpoint_status")
        not in {"VALID", "VALID_PREFIX", "ABSENT", "INVALID"}
        or diagnostic.get("terminal_result_status")
        not in {"VALID", "ABSENT", "INVALID"}
    ):
        return ("DIAGNOSTIC_INVALID",)
    checkpoint_status = diagnostic["checkpoint_status"]
    last_stage = diagnostic.get("last_valid_stage")
    if (
        (
            checkpoint_status in {"VALID", "VALID_PREFIX"}
            and last_stage not in RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH
        )
        or (
            checkpoint_status == "ABSENT"
            and last_stage is not None
        )
        or (
            diagnostic.get("exit_class") == "SPAWN_FAILED"
            and diagnostic.get("process_start_observed") is not False
        )
    ):
        return ("DIAGNOSTIC_INVALID",)
    if diagnostic["terminal_result_status"] == "VALID":
        if (
            checkpoint_status != "VALID"
            or last_stage != "TERMINAL_RESULT_PERSISTED"
            or _SHA256_RE.fullmatch(
                str(diagnostic.get("valid_result_identity_sha256", ""))
            )
            is None
        ):
            return ("DIAGNOSTIC_INVALID",)
    elif diagnostic.get("valid_result_identity_sha256") is not None:
        return ("DIAGNOSTIC_INVALID",)
    return ()


def validate_recovery_epoch002_unknown_disposition(
    disposition: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(disposition) is not dict:
        return ("UNKNOWN_DISPOSITION_INVALID",)
    if set(disposition) != RECOVERY_EPOCH002_UNKNOWN_DISPOSITION_KEYS:
        return ("UNKNOWN_DISPOSITION_INVALID",)
    if (
        disposition.get("schema_version") != _UNKNOWN_DISPOSITION_SCHEMA
        or _contains_forbidden_key(disposition)
        or disposition.get("automatic_retry") is not False
        or disposition.get("body_free") is not True
        or disposition.get("stop_code")
        != "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
        or disposition.get("attempt_consumption_unknown_disposition_sha256")
        != _hash_without(
            disposition,
            "attempt_consumption_unknown_disposition_sha256",
        )
    ):
        return ("UNKNOWN_DISPOSITION_INVALID",)
    identity = disposition.get("reservation_artifact")
    checkpoint_status = disposition.get("checkpoint_status")
    last_stage = disposition.get("last_valid_stage")
    if (
        type(identity) is not dict
        or set(identity) != _EXTERNAL_IDENTITY_KEYS
        or identity.get("artifact_role") != "FORMAL_TEST_RUN_RESERVATION"
        or identity.get("body_free") is not True
        or identity.get("identity_sha256")
        != _hash_without(identity, "identity_sha256")
        or _SHA256_RE.fullmatch(
            str(disposition.get("attempt_id", ""))
        )
        is None
        or checkpoint_status
        not in {"VALID_PREFIX", "ABSENT", "INVALID"}
        or disposition.get("terminal_result_status")
        not in {"ABSENT", "INVALID"}
        or (
            checkpoint_status == "VALID_PREFIX"
            and last_stage not in RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH
        )
        or (
            checkpoint_status == "ABSENT"
            and last_stage is not None
        )
        or not _exit_observation_valid(
            exit_class=disposition.get("exit_class"),
            exit_code=disposition.get("exit_code"),
            signal_number=disposition.get("signal_number"),
        )
    ):
        return ("UNKNOWN_DISPOSITION_INVALID",)
    return ()


def validate_recovery_epoch002_attempt_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Reconcile durable observations without synthesizing missing facts."""

    if type(state) is not dict:
        return ("FORMAL_ATTEMPT_FORBIDDEN",)
    diagnostics = state.get("diagnostics")

    # Publishing an invalid body or its hash is more specific than the
    # general body-free attack classification.
    if (
        state.get("terminal_result_status") == "INVALID"
        and isinstance(diagnostics, Mapping)
        and "invalid_result_sha256" in diagnostics
    ):
        return ("BODY_ORACLE_VIOLATION",)
    if _contains_forbidden_key(diagnostics):
        return ("BODY_FREE_VIOLATION",)
    if diagnostics is not None:
        diagnostic_issues = validate_recovery_epoch002_diagnostic(
            diagnostics
        )
        if diagnostic_issues:
            return diagnostic_issues

    disposition = state.get("unknown_disposition")
    if disposition is not None:
        issues = validate_recovery_epoch002_unknown_disposition(disposition)
        if issues:
            return issues
        if (
            disposition.get("checkpoint_status")
            != state.get("checkpoint_status")
            or disposition.get("terminal_result_status")
            != state.get("terminal_result_status")
            or disposition.get("exit_class") != state.get("exit_class")
            or disposition.get("exit_code") != state.get("exit_code")
            or disposition.get("signal_number") != state.get("signal_number")
        ):
            return ("UNKNOWN_DISPOSITION_INVALID",)

    if state.get("synthetic_collection_observation") is True:
        return ("FORMAL_ATTEMPT_FORBIDDEN",)

    checkpoints = state.get("checkpoint_chain")
    checkpoint_status = state.get("checkpoint_status")
    if checkpoint_status in {"VALID", "VALID_PREFIX"}:
        checkpoint_issues = validate_recovery_epoch002_checkpoint_chain(
            checkpoints,
            allow_prefix=True,
        )
        if checkpoint_issues:
            return checkpoint_issues
        if (
            checkpoint_status == "VALID_PREFIX"
            and checkpoints[-1].get("stage_enum")
            == "TERMINAL_RESULT_PERSISTED"
        ):
            return ("CHECKPOINT_INVALID",)
    elif checkpoints:
        return ("CHECKPOINT_INVALID",)
    elif checkpoint_status != "ABSENT":
        return ("CHECKPOINT_INVALID",)
    if disposition is not None:
        last_stage = checkpoints[-1].get("stage_enum") if checkpoints else None
        if (
            disposition.get("last_valid_stage") != last_stage
            or (
                checkpoints
                and disposition.get("attempt_id")
                != checkpoints[-1].get("attempt_id")
            )
        ):
            return ("UNKNOWN_DISPOSITION_INVALID",)

    terminal_status = state.get("terminal_result_status")
    result = state.get("terminal_result")
    if (
        state.get("reservation_published_and_postverified") is True
        and terminal_status != "VALID"
    ):
        if state.get("same_attempt_rerun_requested") is True:
            return ("FORMAL_ATTEMPT_FORBIDDEN",)
        return ("ATTEMPT_CONSUMPTION_UNKNOWN_STOP",)

    if (
        state.get("multiple_run_results_ranked") is True
        or state.get("earlier_consumed_lineage_dropped") is True
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    if terminal_status == "VALID":
        terminal_issues = validate_recovery_epoch002_terminal_result(result)
        if terminal_issues:
            return terminal_issues
        checkpoint_issues = validate_recovery_epoch002_checkpoint_chain(
            checkpoints,
            allow_prefix=False,
        )
        if (
            checkpoint_issues
            or result.get("terminal_checkpoint_sha256")
            != checkpoints[-1].get("checkpoint_sha256")
            or any(
                result.get(name) != checkpoints[-1].get(name)
                for name in (
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
                )
            )
            or result.get("exit_class") != state.get("exit_class")
            or result.get("exit_code") != state.get("exit_code")
            or result.get("signal_number") != state.get("signal_number")
            or result.get("timed_out") != state.get("timed_out")
            or not isinstance(diagnostics, Mapping)
            or diagnostics.get("attempt_id") != result.get("attempt_id")
            or diagnostics.get("terminal_result_status") != "VALID"
            or diagnostics.get("valid_result_identity_sha256")
            != result.get("formal_worker_result_sha256")
        ):
            return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    if (
        terminal_status == "VALID"
        and state.get("terminal_result_publication_succeeded") is not True
    ):
        return (
            "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
        )
    return ()


_SUCCESS_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
_SUCCESS_EXACT1_PUBLICATION_KEYS = _keys(
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
    """
    path git_blob_sha1 raw_sha256 logical_artifact_sha256 body_free
    """
)
_SUCCESS_UNCHANGED_OBSERVATION_KEYS = _keys(
    "scope mode_type_sha_complete mismatches observation_sha256"
)
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


def _success_raw_identity(
    artifact: Mapping[str, Any],
    *,
    path: str,
    role: str,
    logical_hash_key: str,
    publication_commit_sha1: str,
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
    identity = {
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
        "publication_commit_sha1": publication_commit_sha1,
        "body_free": True,
        "identity_sha256": "",
    }
    identity["identity_sha256"] = _hash_without(
        identity,
        "identity_sha256",
    )
    return identity


def _success_postfetch_valid(
    evidence: Any,
    identity: Mapping[str, Any],
    *,
    base_commit_sha1: str,
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
        or set(identity) != _SUCCESS_EXTERNAL_IDENTITY_KEYS
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
        and identity.get("repository_full_name") == "MassyuRed/Cocolon"
        and identity.get("body_free") is True
        and _SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is not None
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
        and evidence.get("artifact_at_publication") == artifact
        and type(evidence.get("artifact_at_verification_ref")) is dict
        and set(evidence["artifact_at_verification_ref"])
        == _SUCCESS_POSTFETCH_ARTIFACT_KEYS
        and evidence.get("artifact_at_verification_ref") == artifact
        and evidence.get("owner_issue_codes") == []
        and evidence.get("independent_issue_codes") == []
        and evidence.get("postfetch_state") == "POSTVERIFIED"
    )


def _success_terminal_shape_valid(terminal: Any) -> bool:
    return (
        type(terminal) is dict
        and set(terminal) == RECOVERY_EPOCH002_TERMINAL_RESULT_V2_KEYS
        and terminal.get("schema_version")
        == RECOVERY_EPOCH002_TERMINAL_RESULT_V2_SCHEMA
        and terminal.get("body_free") is True
        and terminal.get("formal_worker_result_sha256")
        == _hash_without(terminal, "formal_worker_result_sha256")
    )


def _success_terminal_outcomes_valid(
    terminal: Mapping[str, Any],
    locked_sources: Any,
) -> tuple[bool, bool, bool]:
    outcomes = terminal.get("outcomes")
    if type(locked_sources) is not list:
        return False, False, False
    source_by_path: dict[str, Mapping[str, Any]] = {}
    for source in locked_sources:
        if (
            type(source) is not dict
            or set(source) != {"path", "git_blob_sha1", "raw_sha256"}
            or not isinstance(source.get("path"), str)
        ):
            return False, False, False
        source_by_path[source["path"]] = source
    if (
        type(outcomes) is not list
        or len(outcomes) != len(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
    ):
        return False, False, False
    evidence_valid = True
    sources_valid = True
    codes_valid = True
    for node_id, outcome in zip(
        RECOVERY_EPOCH002_FORMAL_NODE_IDS,
        outcomes,
        strict=True,
    ):
        if (
            type(outcome) is not dict
            or set(outcome) != RECOVERY_EPOCH002_FORMAL_NODE_OUTCOME_KEYS
            or outcome.get("test_node_id") != node_id
            or outcome.get("evidence_sha256")
            != _hash_without(outcome, "evidence_sha256")
        ):
            evidence_valid = False
            continue
        source_path = node_id.partition("::")[0]
        source = source_by_path.get(source_path)
        if (
            outcome.get("source_path") != source_path
            or source is None
            or outcome.get("source_blob_sha1")
            != source.get("git_blob_sha1")
            or outcome.get("source_sha256") != source.get("raw_sha256")
        ):
            sources_valid = False
        expected = RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE.get(
            node_id
        )
        if outcome.get("expected_closed_code") != expected:
            codes_valid = False
    if terminal.get("formal_node_outcome_evidence_sha256") != artifact_sha256(
        outcomes
    ):
        evidence_valid = False
    return evidence_valid, sources_valid, codes_valid


def _validate_recovery_epoch002_success_terminal_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate observed exact134 success and its exact1 terminal receipt."""

    if type(state) is not dict:
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    terminal = state.get("terminal_result")
    if not _success_terminal_shape_valid(terminal):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
    if terminal.get("collection_node_ids") != list(
        RECOVERY_EPOCH002_FORMAL_NODE_IDS
    ):
        return ("TERMINAL_COLLECTION_ORDER_INVALID",)
    if (
        type(terminal.get("executed_node_ids")) is list
        and len(terminal["executed_node_ids"])
        == len(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
        and terminal.get("executed_node_ids")
        != list(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
    ):
        return ("TERMINAL_EXECUTION_ORDER_INVALID",)
    evidence_valid, sources_valid, codes_valid = (
        _success_terminal_outcomes_valid(
            terminal,
            state.get("locked_source_manifest"),
        )
    )
    if not evidence_valid:
        return ("TERMINAL_OUTCOME_EVIDENCE_INVALID",)
    if not sources_valid:
        return ("TERMINAL_SOURCE_IDENTITY_MISMATCH",)
    if (
        state.get("locked_formal_node_ids")
        != list(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
        or state.get("locked_negative_code_by_node")
        != RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE
        or not codes_valid
    ):
        return ("TERMINAL_EXPECTED_CLOSED_CODE_MISMATCH",)

    counts = terminal.get("counts")
    states = terminal.get("states")
    outcomes = terminal["outcomes"]
    if (
        type(counts) is not dict
        or set(counts) != RECOVERY_EPOCH002_FORMAL_RESULT_COUNTS_KEYS
        or any(type(value) is not int for value in counts.values())
        or type(states) is not dict
        or set(states) != set(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
        or any(
            states.get(outcome["test_node_id"]) != outcome.get("result")
            for outcome in outcomes
        )
        or counts.get("collected") != len(terminal["collection_node_ids"])
        or counts.get("executed") != len(terminal["executed_node_ids"])
        or counts.get("passed")
        != sum(outcome.get("result") == "PASSED" for outcome in outcomes)
        or counts.get("failed")
        != sum(outcome.get("result") == "FAILED" for outcome in outcomes)
        or counts.get("skipped")
        != sum(outcome.get("result") == "SKIPPED" for outcome in outcomes)
        or counts.get("xfailed")
        != sum(outcome.get("result") == "XFAILED" for outcome in outcomes)
        or counts.get("xpassed")
        != sum(outcome.get("result") == "XPASSED" for outcome in outcomes)
        or counts.get("errors") != 0
        or counts.get("deselected") != 0
        or counts.get("collection_errors")
        != terminal.get("collection_errors")
        or len(terminal["executed_node_ids"]) != len(states)
    ):
        return ("TERMINAL_COUNTS_STATE_PARITY_INVALID",)

    retry = state.get("retry_history")
    parity = state.get("parity_bindings")
    chain = state.get("checkpoint_chain")
    if (
        state.get("owner_issue_codes") != []
        or state.get("independent_issue_codes") != []
        or validate_recovery_epoch002_checkpoint_chain(
            chain,
            allow_prefix=False,
        )
        != ()
        or not chain
        or terminal.get("terminal_checkpoint_sha256")
        != chain[-1].get("checkpoint_sha256")
        or any(outcome.get("result") != "PASSED" for outcome in outcomes)
        or terminal.get("collection_errors") != 0
        or terminal.get("exit_class") != "EXITED"
        or type(terminal.get("exit_code")) is not int
        or terminal.get("exit_code") != 0
        or terminal.get("signal_number") is not None
        or terminal.get("timed_out") is not False
        or terminal.get("formal_exact134_invocation_count") != 1
        or type(terminal.get("formal_exact134_invocation_count")) is not int
        or type(retry) is not dict
        or set(retry) != RECOVERY_EPOCH002_SUCCESS_RETRY_HISTORY_KEYS
        or type(retry.get("successful_reservation_ordinal")) is not int
        or retry.get("successful_reservation_ordinal") < 1
        or type(retry.get("consumed_attempt_ids")) is not list
        or len(retry.get("consumed_attempt_ids"))
        != retry.get("successful_reservation_ordinal") - 1
        or len(set(retry.get("consumed_attempt_ids")))
        != len(retry.get("consumed_attempt_ids"))
        or retry.get("successful_attempt_id") != terminal.get("attempt_id")
        or retry.get("successful_attempt_id")
        in retry.get("consumed_attempt_ids")
        or type(parity) is not dict
        or set(parity) != RECOVERY_EPOCH002_SUCCESS_PARITY_BINDING_KEYS
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
    ):
        return ("TERMINAL_SUCCESS_PREDICATE_NOT_PROVED",)

    publication = state.get("terminal_publication")
    if (
        state.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        or
        type(publication) is not dict
        or not {
            "reflection_contract_version",
            "artifact",
            "identity",
            "changed_paths",
            "postfetch_evidence",
            "postfetch_state",
        }.issubset(publication)
        or not set(publication).issubset(
            _SUCCESS_EXACT1_PUBLICATION_KEYS
        )
        or publication.get("reflection_contract_version")
        != RECOVERY_EPOCH002_CURRENT_REFLECTION_CONTRACT
        or publication.get("artifact") != terminal
        or type(publication.get("identity")) is not dict
        or publication["identity"].get("path")
        not in publication.get("changed_paths", ())
        or publication.get("changed_paths")
        != [publication["identity"].get("path")]
        or publication.get("postfetch_state") != "POSTVERIFIED"
    ):
        return (
            "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
        )
    expected_identity = _success_raw_identity(
        terminal,
        path=publication["identity"].get("path", ""),
        role="FORMAL_WORKER_TERMINAL_RESULT",
        logical_hash_key="formal_worker_result_sha256",
        publication_commit_sha1=publication["identity"].get(
            "publication_commit_sha1",
            "",
        ),
    )
    if (
        expected_identity is None
        or publication["identity"] != expected_identity
        or not _success_postfetch_valid(
            publication.get("postfetch_evidence"),
            publication["identity"],
            base_commit_sha1=publication.get("expected_old_sha1"),
        )
    ):
        return (
            "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
        )
    return ()


def validate_recovery_epoch002_success_terminal_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed exact134 success-terminal state."""

    try:
        if (
            type(state) is not dict
            or set(state) != RECOVERY_EPOCH002_SUCCESS_TERMINAL_STATE_KEYS
            or _contains_forbidden_key(state)
        ):
            return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
        return _validate_recovery_epoch002_success_terminal_state_impl(state)
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)


def _canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    if _contains_forbidden_key(value):
        raise ValueError("body-free evidence contains a forbidden key")
    return canonical_json_bytes(value) + b"\n"


def write_recovery_epoch002_body_free_json_once(
    directory: Path,
    filename: str,
    value: Mapping[str, Any],
) -> Path:
    """Persist one canonical record without overwrite or symlink following."""

    if (
        not filename
        or filename in {".", ".."}
        or "/" in filename
        or "\\" in filename
    ):
        raise ValueError("filename must be one safe path component")
    directory_stat = directory.lstat()
    if (
        not stat.S_ISDIR(directory_stat.st_mode)
        or directory.is_symlink()
        or stat.S_IMODE(directory_stat.st_mode) != 0o700
        or directory_stat.st_uid != os.getuid()
    ):
        raise ValueError("evidence directory must be owner-only 0700")

    payload = _canonical_json_bytes(value)
    dir_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    dir_flags |= getattr(os, "O_NOFOLLOW", 0)
    dir_fd = os.open(directory, dir_flags)
    temp_name = f".{filename}.{secrets.token_hex(12)}.tmp"
    file_fd: int | None = None
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(temp_name, flags, 0o600, dir_fd=dir_fd)
        view = memoryview(payload)
        while view:
            written = os.write(file_fd, view)
            view = view[written:]
        os.fsync(file_fd)
        file_stat = os.fstat(file_fd)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or stat.S_IMODE(file_stat.st_mode) != 0o600
            or file_stat.st_uid != os.getuid()
        ):
            raise ValueError("evidence file identity is invalid")
        os.close(file_fd)
        file_fd = None
        os.link(
            temp_name,
            filename,
            src_dir_fd=dir_fd,
            dst_dir_fd=dir_fd,
            follow_symlinks=False,
        )
        os.unlink(temp_name, dir_fd=dir_fd)
        os.fsync(dir_fd)
    except BaseException:
        if file_fd is not None:
            os.close(file_fd)
        try:
            os.unlink(temp_name, dir_fd=dir_fd)
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(dir_fd)
    return directory / filename


__all__ = [
    "RECOVERY_EPOCH002_PREFLIGHT_CHECKPOINT_KEYS",
    "RECOVERY_EPOCH002_FORMAL_CHECKPOINT_KEYS",
    "RECOVERY_EPOCH002_TERMINAL_RESULT_KEYS",
    "RECOVERY_EPOCH002_DIAGNOSTIC_KEYS",
    "RECOVERY_EPOCH002_UNKNOWN_DISPOSITION_KEYS",
    "RECOVERY_EPOCH002_TERMINAL_RESULT_V2_SCHEMA",
    "RECOVERY_EPOCH002_TERMINAL_RESULT_V2_KEYS",
    "RECOVERY_EPOCH002_FORMAL_NODE_OUTCOME_KEYS",
    "RECOVERY_EPOCH002_FORMAL_RESULT_COUNTS_KEYS",
    "RECOVERY_EPOCH002_FORMAL_NODE_IDS",
    "RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE",
    "RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODES",
    "RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH",
    "RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS",
    "validate_recovery_epoch002_checkpoint_chain",
    "validate_recovery_epoch002_terminal_result",
    "validate_recovery_epoch002_operational_terminal_result",
    "validate_recovery_epoch002_diagnostic",
    "validate_recovery_epoch002_unknown_disposition",
    "validate_recovery_epoch002_attempt_state",
    "validate_recovery_epoch002_success_terminal_state",
    "write_recovery_epoch002_body_free_json_once",
]
