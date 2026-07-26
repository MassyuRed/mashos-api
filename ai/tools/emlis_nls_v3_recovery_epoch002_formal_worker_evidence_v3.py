#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Durable, body-free formal-worker evidence for Recovery Epoch 002."""

from copy import deepcopy
from datetime import datetime, timezone
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
    RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


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
            key in RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS
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
    "RECOVERY_EPOCH002_FORMAL_STAGE_GRAPH",
    "RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS",
    "validate_recovery_epoch002_checkpoint_chain",
    "validate_recovery_epoch002_terminal_result",
    "validate_recovery_epoch002_operational_terminal_result",
    "validate_recovery_epoch002_diagnostic",
    "validate_recovery_epoch002_unknown_disposition",
    "validate_recovery_epoch002_attempt_state",
    "write_recovery_epoch002_body_free_json_once",
]
