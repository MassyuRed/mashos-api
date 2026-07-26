#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed Recovery Epoch 002 formal-parent state machine.

The parent owns ordering and admission.  It never performs transport,
durable writes, or worker creation itself.  One explicit phase request calls
at most one supplied port and always returns with automatic progression
disabled.
"""

from copy import deepcopy
from typing import Any, Mapping, Protocol

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch002_sequence_ledger_v3 import (
    validate_recovery_epoch002_event1_artifact,
    validate_recovery_epoch002_reservation_artifact,
)
from emlis_nls_v3_recovery_epoch002_closure_receipt_verify import (
    verify_recovery_epoch002_artifact_identity,
    verify_recovery_epoch002_published_artifact,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight import (
    validate_recovery_epoch002_bootstrap_state,
    validate_recovery_epoch002_event1_publication_binding,
    validate_recovery_epoch002_operational_preflight_attestation,
    validate_recovery_epoch002_operational_readiness_bindings,
    validate_recovery_epoch002_readiness_artifact,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3 import (
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS,
    validate_recovery_epoch002_attempt_state,
    validate_recovery_epoch002_checkpoint_chain,
    validate_recovery_epoch002_operational_terminal_result,
)


RECOVERY_EPOCH002_FORMAL_PARENT_PROTOCOL = (
    "RECOVERY_EPOCH002_FORMAL_PARENT_EXPLICIT_PHASE_V1"
)
RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_parent_phase_result.v1"
)
RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER = (
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT",
    "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
    "PARENT_SPAWN_INTENT_PERSISTED",
    "FORMAL_EXACT134_ONCE",
    "TERMINAL_RESULT_OR_UNKNOWN_STOP",
)
RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES = (
    *RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER[:4],
    "FORMAL_EXACT134_ONCE",
)
RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES = (
    "observe_event1_publication",
    "run_bootstrap_preflight",
    "publish_readiness",
    "publish_reservation",
    "spawn_exact134_once",
)
RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS = frozenset(
    {
        "artifact_role",
        "artifact",
        "artifact_external_identity",
        "receipt_contains_self_commit_blob_or_raw_identity",
        "expected_old_sha1",
        "observed_old_sha1",
        "parent_commit_sha1s",
        "changed_paths",
        "expected_changed_paths",
        "path_preexisted",
        "postfetch_succeeded",
        "postfetch_matches_candidate",
        "postfetch_commit_sha1",
        "postfetch_git_blob_sha1",
        "owner_issue_codes",
        "independent_issue_codes",
        "reservation_write_outcome",
        "authoritative_reservation_presence",
        "ready_receipt_marked_consumed",
        "fabricated_reservation_detected",
        "automatic_progression",
        "body_free",
    }
)
RECOVERY_EPOCH002_FORMAL_AUTHORITY_GRANT_KEYS = frozenset(
    {
        "schema_version",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "attempt_id",
        "formal_run_challenge_id",
        "readiness_identity_sha256",
        "reservation_identity_sha256",
        "formal_exact134_authorized",
        "automatic_progression",
        "body_free",
        "authority_grant_sha256",
    }
)
RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_KEYS = frozenset(
    {
        "schema_version",
        "protocol",
        "requested_phase",
        "completed_phase",
        "phase_output",
        "validation_issues",
        "stop_code",
        "port_call_counts",
        "formal_exact134_invocation_count",
        "automatic_progression",
        "body_free",
        "parent_phase_result_sha256",
    }
)

_FORMAL_AUTHORITY_GRANT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_exact134_authority_grant.v1"
)
_ACCEPTED_ATTEMPT_STOPS = frozenset(
    {
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
    }
)


class RecoveryEpoch002ParentPorts(Protocol):
    """Every side effect remains visible at one explicit phase boundary."""

    def observe_event1_publication(
        self,
        *,
        event1_artifact: Mapping[str, Any],
        event1_external_identity: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Return a fresh post-fetch publication observation."""

    def run_bootstrap_preflight(
        self,
        *,
        event1_artifact: Mapping[str, Any],
        event1_external_identity: Mapping[str, Any],
        event1_publication_state: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Run no-collection bootstrap preflight and return its state."""

    def publish_readiness(
        self,
        *,
        artifact: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Publish one readiness artifact and return fresh post-fetch facts."""

    def publish_reservation(
        self,
        *,
        artifact: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Publish one reservation and return fresh post-fetch facts."""

    def spawn_exact134_once(
        self,
        *,
        authority_grant: Mapping[str, Any],
        event1_artifact: Mapping[str, Any],
        event1_external_identity: Mapping[str, Any],
        event1_publication_state: Mapping[str, Any],
        reservation: Mapping[str, Any],
        readiness: Mapping[str, Any],
        readiness_external_identity: Mapping[str, Any],
        reservation_external_identity: Mapping[str, Any],
        readiness_publication_state: Mapping[str, Any],
        reservation_publication_state: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Persist spawn intent, then consume the grant exactly once.

        The formal runner is the sole owner of checkpoint ordinal one.  A
        separate parent-side write would race its write-once attempt claim.
        """


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


def _fresh_publication_issues(
    state: Mapping[str, Any],
    *,
    artifact_role: str,
    artifact: Mapping[str, Any],
    external_identity: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    if (
        type(state) is not dict
        or set(state) != RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS
        or state.get("artifact_role") != artifact_role
        or state.get("artifact") != artifact
        or state.get("automatic_progression") is not False
        or state.get("body_free") is not True
        or _contains_forbidden_key(state)
        or verify_recovery_epoch002_published_artifact(state)
    ):
        return ("PUBLISHED_ARTIFACT_POSTVERIFY_INVALID",)
    identity = state.get("artifact_external_identity")
    if (
        verify_recovery_epoch002_artifact_identity(identity)
        or (
            external_identity is not None
            and identity != external_identity
        )
    ):
        return ("PUBLISHED_ARTIFACT_POSTVERIFY_INVALID",)
    return ()


def _event1_issues(
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
) -> tuple[str, ...]:
    if (
        validate_recovery_epoch002_event1_artifact(event1_artifact)
        or verify_recovery_epoch002_artifact_identity(
            event1_external_identity
        )
        or event1_external_identity.get("artifact_role")
        not in {"EVENT1", "SOURCE_BASELINE_EVENT"}
        or event1_external_identity.get("logical_artifact_sha256")
        != event1_artifact.get("event_sha256")
        or _fresh_publication_issues(
            event1_publication_state,
            artifact_role="SOURCE_BASELINE_EVENT",
            artifact=event1_artifact,
            external_identity=event1_external_identity,
        )
    ):
        return ("SOURCE_BASELINE_EVENT_NOT_PUBLISHED_STOP",)
    return ()


def _readiness_issues(
    *,
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    bootstrap_state: Mapping[str, Any],
) -> tuple[str, ...]:
    if (
        type(bootstrap_state) is not dict
        or _contains_forbidden_key(bootstrap_state)
        or validate_recovery_epoch002_bootstrap_state(bootstrap_state)
    ):
        return ("PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",)
    readiness = bootstrap_state.get("readiness_receipt")
    manifest = bootstrap_state.get("bootstrap_manifest")
    if (
        validate_recovery_epoch002_readiness_artifact(readiness)
        or validate_recovery_epoch002_operational_readiness_bindings(
            readiness,
            manifest,
        )
        or validate_recovery_epoch002_event1_publication_binding(
            event1_artifact=event1_artifact,
            event1_external_identity=event1_external_identity,
            event1_publication_state=event1_publication_state,
            readiness=readiness,
        )
        or validate_recovery_epoch002_operational_preflight_attestation(
            bootstrap_state.get("operational_preflight_attestation"),
            readiness=readiness,
            event1_external_identity=event1_external_identity,
        )
    ):
        return ("PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",)
    return ()


def _readiness_publication_issues(
    *,
    event1_external_identity: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_publication_state: Mapping[str, Any],
) -> tuple[str, ...]:
    if _fresh_publication_issues(
        readiness_publication_state,
        artifact_role="BOOTSTRAP_READINESS",
        artifact=readiness,
    ):
        return ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)
    if (
        readiness_publication_state.get("expected_old_sha1")
        != event1_external_identity.get("publication_commit_sha1")
    ):
        return ("READINESS_RECEIPT_NOT_PUBLISHED_STOP",)
    return ()


def _reservation_issues(
    *,
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_external_identity: Mapping[str, Any],
    reservation: Mapping[str, Any],
) -> tuple[str, ...]:
    if validate_recovery_epoch002_reservation_artifact(reservation):
        return ("RUN_RESERVATION_INVALID",)
    source_closure = event1_artifact.get("source_closure")
    if (
        reservation.get("source_baseline_event")
        != event1_external_identity
        or reservation.get("source_closure") != source_closure
        or reservation.get("bootstrap_readiness_artifact")
        != readiness_external_identity
        or reservation.get("logical_cycle_id")
        != event1_artifact.get("logical_cycle_id")
        or reservation.get("recovery_epoch_id")
        != event1_artifact.get("recovery_epoch_id")
        or reservation.get("candidate_version_id")
        != event1_artifact.get("candidate_version_id")
        or reservation.get("event1_challenge_id")
        != event1_artifact.get("challenge_id")
        or reservation.get("preflight_challenge_id")
        != readiness.get("preflight_challenge_id")
        or reservation.get("publication_base_commit_sha1")
        != readiness_external_identity.get("publication_commit_sha1")
    ):
        return ("RUN_RESERVATION_INVALID",)
    return ()


def _reservation_publication_issues(
    *,
    readiness_external_identity: Mapping[str, Any],
    reservation: Mapping[str, Any],
    reservation_publication_state: Mapping[str, Any],
) -> tuple[str, ...]:
    if _fresh_publication_issues(
        reservation_publication_state,
        artifact_role="FORMAL_TEST_RUN_RESERVATION",
        artifact=reservation,
    ):
        return ("RESERVATION_NOT_PUBLISHED_STOP",)
    if (
        reservation_publication_state.get("expected_old_sha1")
        != readiness_external_identity.get("publication_commit_sha1")
        or reservation_publication_state.get("expected_old_sha1")
        != reservation.get("publication_base_commit_sha1")
    ):
        return ("RESERVATION_NOT_PUBLISHED_STOP",)
    return ()


def _spawn_intent_issues(
    *,
    checkpoint: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> tuple[str, ...]:
    if (
        type(checkpoint) is not dict
        or _contains_forbidden_key(checkpoint)
        or validate_recovery_epoch002_checkpoint_chain([checkpoint])
    ):
        return ("PARENT_SPAWN_INTENT_INVALID",)
    source_closure = reservation["source_closure"]
    expected = {
        "logical_cycle_id": reservation["logical_cycle_id"],
        "recovery_epoch_id": reservation["recovery_epoch_id"],
        "authority_token_id": artifact_sha256(
            {"authority_token": reservation["authority_token"]}
        ),
        "event1_challenge_id": reservation["event1_challenge_id"],
        "preflight_challenge_id": reservation["preflight_challenge_id"],
        "formal_run_challenge_id": reservation["challenge_id"],
        "formal_authority_challenge_id": reservation[
            "authority_challenge_id"
        ],
        "preflight_id": readiness["preflight_id"],
        "attempt_id": reservation["attempt_id"],
        "reservation_ordinal": reservation["reservation_ordinal"],
        "formal_test_run_reservation_sha256": reservation[
            "formal_test_run_reservation_sha256"
        ],
        "candidate_version_id": reservation["candidate_version_id"],
        "source_baseline_event_sha256": reservation[
            "source_baseline_event"
        ]["logical_artifact_sha256"],
        "source_closure_sha256": source_closure[
            "source_closure_sha256"
        ],
        "bootstrap_closure_sha256": source_closure[
            "bootstrap_closure_sha256"
        ],
        "checkpoint_ordinal": 1,
        "stage_enum": "PARENT_SPAWN_INTENT_PERSISTED",
        "prior_checkpoint_sha256": None,
    }
    if any(checkpoint.get(key) != value for key, value in expected.items()):
        return ("PARENT_SPAWN_INTENT_INVALID",)
    return ()


def _formal_authority_issues(
    *,
    grant: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness_external_identity: Mapping[str, Any],
    reservation_external_identity: Mapping[str, Any],
) -> tuple[str, ...]:
    if (
        type(grant) is not dict
        or set(grant) != RECOVERY_EPOCH002_FORMAL_AUTHORITY_GRANT_KEYS
        or grant.get("schema_version") != _FORMAL_AUTHORITY_GRANT_SCHEMA
        or grant.get("logical_cycle_id")
        != reservation.get("logical_cycle_id")
        or grant.get("recovery_epoch_id")
        != reservation.get("recovery_epoch_id")
        or grant.get("candidate_version_id")
        != reservation.get("candidate_version_id")
        or grant.get("attempt_id") != reservation.get("attempt_id")
        or grant.get("formal_run_challenge_id")
        != reservation.get("challenge_id")
        or grant.get("readiness_identity_sha256")
        != readiness_external_identity.get("identity_sha256")
        or grant.get("reservation_identity_sha256")
        != reservation_external_identity.get("identity_sha256")
        or grant.get("formal_exact134_authorized") is not True
        or grant.get("automatic_progression") is not False
        or grant.get("body_free") is not True
        or grant.get("authority_grant_sha256")
        != _hash_without(grant, "authority_grant_sha256")
        or _contains_forbidden_key(grant)
    ):
        return ("FORMAL_EXACT134_NOT_AUTHORIZED",)
    return ()


def _operational_attempt_issues(
    *,
    state: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    reservation_external_identity: Mapping[str, Any],
) -> tuple[str, ...]:
    """Bind terminal/unknown evidence to this exact consumed reservation."""

    if type(state) is not dict:
        return ("FORMAL_ATTEMPT_FORBIDDEN",)
    diagnostic = state.get("diagnostics")
    disposition = state.get("unknown_disposition")
    expected_diagnostic = {
        "logical_cycle_id": reservation.get("logical_cycle_id"),
        "recovery_epoch_id": reservation.get("recovery_epoch_id"),
        "authority_token_id": artifact_sha256(
            {"authority_token": reservation.get("authority_token")}
        ),
        "event1_challenge_id": reservation.get("event1_challenge_id"),
        "preflight_challenge_id": reservation.get(
            "preflight_challenge_id"
        ),
        "formal_run_challenge_id": reservation.get("challenge_id"),
        "formal_authority_challenge_id": reservation.get(
            "authority_challenge_id"
        ),
        "preflight_id": readiness.get("preflight_id"),
        "attempt_id": reservation.get("attempt_id"),
        "reservation_ordinal": reservation.get("reservation_ordinal"),
    }
    if (
        type(diagnostic) is not dict
        or any(
            diagnostic.get(key) != value
            for key, value in expected_diagnostic.items()
        )
    ):
        return ("DIAGNOSTIC_INVALID",)
    if state.get("terminal_result_status") == "VALID":
        terminal = state.get("terminal_result")
        source_closure = reservation.get("source_closure")
        if (
            type(terminal) is not dict
            or validate_recovery_epoch002_operational_terminal_result(
                terminal
            )
            or type(source_closure) is not dict
            or terminal.get("logical_cycle_id")
            != reservation.get("logical_cycle_id")
            or terminal.get("recovery_epoch_id")
            != reservation.get("recovery_epoch_id")
            or terminal.get("event1_challenge_id")
            != reservation.get("event1_challenge_id")
            or terminal.get("formal_run_challenge_id")
            != reservation.get("challenge_id")
            or terminal.get("formal_authority_challenge_id")
            != reservation.get("authority_challenge_id")
            or terminal.get("attempt_id") != reservation.get("attempt_id")
            or terminal.get("candidate_version_id")
            != reservation.get("candidate_version_id")
            or terminal.get("source_baseline_event_sha256")
            != reservation.get("source_baseline_event", {}).get(
                "logical_artifact_sha256"
            )
            or terminal.get("source_closure_sha256")
            != source_closure.get("source_closure_sha256")
            or terminal.get("bootstrap_closure_sha256")
            != source_closure.get("bootstrap_closure_sha256")
            or terminal.get("formal_test_run_reservation_sha256")
            != reservation.get("formal_test_run_reservation_sha256")
            or disposition is not None
        ):
            return ("TERMINAL_OR_ACCEPTANCE_PUBLICATION_REJECTED",)
        return ()
    if (
        type(disposition) is not dict
        or disposition.get("reservation_artifact")
        != reservation_external_identity
        or disposition.get("attempt_id") != reservation.get("attempt_id")
        or disposition.get("checkpoint_status")
        != state.get("checkpoint_status")
        or disposition.get("terminal_result_status")
        != state.get("terminal_result_status")
        or disposition.get("exit_class") != state.get("exit_class")
        or disposition.get("exit_code") != state.get("exit_code")
        or disposition.get("signal_number") != state.get("signal_number")
        or disposition.get("stop_code")
        != "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
        or diagnostic.get("stop_code")
        != "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
    ):
        return ("UNKNOWN_DISPOSITION_INVALID",)
    return ()


def _result(
    *,
    requested_phase: str,
    completed_phase: str | None,
    phase_output: Mapping[str, Any] | None,
    validation_issues: tuple[str, ...],
    stop_code: str,
    called_port: str | None,
) -> dict[str, Any]:
    calls = {
        name: int(name == called_port)
        for name in RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES
    }
    result: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_SCHEMA,
        "protocol": RECOVERY_EPOCH002_FORMAL_PARENT_PROTOCOL,
        "requested_phase": requested_phase,
        "completed_phase": completed_phase,
        "phase_output": (
            deepcopy(dict(phase_output))
            if type(phase_output) is dict
            else None
        ),
        "validation_issues": list(validation_issues),
        "stop_code": stop_code,
        "port_call_counts": calls,
        "formal_exact134_invocation_count": calls[
            "spawn_exact134_once"
        ],
        "automatic_progression": False,
        "body_free": True,
        "parent_phase_result_sha256": "",
    }
    result["parent_phase_result_sha256"] = _hash_without(
        result,
        "parent_phase_result_sha256",
    )
    return result


def validate_recovery_epoch002_parent_phase_result(
    result: Mapping[str, Any],
) -> tuple[str, ...]:
    if (
        type(result) is not dict
        or set(result) != RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_KEYS
        or result.get("schema_version")
        != RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_SCHEMA
        or result.get("protocol") != RECOVERY_EPOCH002_FORMAL_PARENT_PROTOCOL
        or result.get("requested_phase")
        not in RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES
        or result.get("automatic_progression") is not False
        or result.get("body_free") is not True
        or result.get("parent_phase_result_sha256")
        != _hash_without(result, "parent_phase_result_sha256")
        or _contains_forbidden_key(result)
    ):
        return ("FORMAL_PARENT_PHASE_RESULT_INVALID",)
    calls = result.get("port_call_counts")
    issues = result.get("validation_issues")
    completed = result.get("completed_phase")
    output = result.get("phase_output")
    if (
        type(calls) is not dict
        or tuple(calls) != RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES
        or any(type(value) is not int or value not in {0, 1} for value in calls.values())
        or sum(calls.values()) > 1
        or result.get("formal_exact134_invocation_count")
        != calls["spawn_exact134_once"]
        or type(issues) is not list
        or any(not isinstance(issue, str) or not issue for issue in issues)
        or not isinstance(result.get("stop_code"), str)
        or not result.get("stop_code")
        or (
            completed is None
            and (output is not None or not issues)
        )
        or (
            completed is not None
            and (
                completed != result.get("requested_phase")
                or type(output) is not dict
            )
        )
    ):
        return ("FORMAL_PARENT_PHASE_RESULT_INVALID",)
    return ()


def validate_recovery_epoch002_parent_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Reconcile the legacy post-event1 parent phase used by the D1 matrix."""

    if type(state) is not dict:
        return ("PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",)
    if (
        tuple(state.get("phase_order", ()))
        != RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER
        or state.get("preflight_state")
        != "READY_FOR_EXACT_ONE_FORMAL_SPAWN"
        or state.get("readiness_published_and_postverified") is not True
    ):
        return ("PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",)
    reservation_published = state.get(
        "reservation_published_and_postverified"
    )
    invocation_count = state.get("formal_exact134_invocation_count")
    if type(invocation_count) is not int or type(invocation_count) is bool:
        return ("FORMAL_PARENT_STATE_INVALID",)
    if invocation_count < 0 or invocation_count > 1:
        return ("FORMAL_PARENT_STATE_INVALID",)
    if invocation_count and reservation_published is not True:
        return ("PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",)
    if (
        state.get("parent_spawn_intent_persisted") is True
        and reservation_published is not True
    ):
        return ("PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",)
    if state.get("automatic_progression") is not False:
        return ("FORMAL_PARENT_STATE_INVALID",)
    return ()


def validate_recovery_epoch002_parent_execution_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Require actual Event1 bytes, identity, and fresh post-fetch facts."""

    issues = validate_recovery_epoch002_parent_state(state)
    if issues:
        return issues
    return _event1_issues(
        state.get("event1_artifact"),
        state.get("event1_external_identity"),
        state.get("event1_publication_state"),
    )


def next_recovery_epoch002_parent_action(
    state: Mapping[str, Any],
) -> str:
    """Return the next closed action without executing it."""

    if _event1_issues(
        state.get("event1_artifact"),
        state.get("event1_external_identity"),
        state.get("event1_publication_state"),
    ):
        return "STOP_EVENT1_NOT_POSTVERIFIED"
    if state.get("preflight_state") != "READY_FOR_EXACT_ONE_FORMAL_SPAWN":
        return "RUN_BOOTSTRAP_PREFLIGHT"
    if state.get("readiness_published_and_postverified") is not True:
        return "PUBLISH_READINESS"
    if state.get("reservation_published_and_postverified") is not True:
        return "PUBLISH_RESERVATION"
    if state.get("parent_spawn_intent_persisted") is not True:
        return "SPAWN_FORMAL_EXACT134_ONCE_WITH_RUNNER_OWNED_INTENT"
    if state.get("formal_exact134_invocation_count") == 0:
        return "SPAWN_FORMAL_EXACT134_ONCE"
    if state.get("terminal_result_status") == "VALID":
        if state.get("terminal_result_publication_succeeded") is True:
            return "AUTHORITY_STOP_TERMINAL_PUBLISHED"
        return "AUTHORITY_STOP_TERMINAL_PUBLICATION_PENDING"
    return "AUTHORITY_STOP_ATTEMPT_CONSUMPTION_UNKNOWN"


def execute_recovery_epoch002_parent_phase(
    *,
    requested_phase: str,
    ports: RecoveryEpoch002ParentPorts,
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any] | None = None,
    bootstrap_state: Mapping[str, Any] | None = None,
    readiness_publication_state: Mapping[str, Any] | None = None,
    reservation_artifact: Mapping[str, Any] | None = None,
    reservation_publication_state: Mapping[str, Any] | None = None,
    formal_authority_grant: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute exactly one explicitly requested parent phase.

    No successful phase invokes the next one.  A reservation-port ambiguity
    and every post-reservation ambiguity stop as consumed/unknown.
    """

    if requested_phase not in RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES:
        return _result(
            requested_phase=str(requested_phase),
            completed_phase=None,
            phase_output=None,
            validation_issues=("FORMAL_PARENT_PHASE_INVALID",),
            stop_code="FORMAL_PARENT_PHASE_INVALID",
            called_port=None,
        )

    if requested_phase == "EVENT1_PUBLISHED_AND_POSTVERIFIED":
        if event1_publication_state is not None:
            return _result(
                requested_phase=requested_phase,
                completed_phase=None,
                phase_output=None,
                validation_issues=("FRESH_EVENT1_OBSERVATION_REQUIRED",),
                stop_code="STOP_EVENT1_NOT_POSTVERIFIED",
                called_port=None,
            )
        try:
            observed = ports.observe_event1_publication(
                event1_artifact=event1_artifact,
                event1_external_identity=event1_external_identity,
            )
        except Exception:
            return _result(
                requested_phase=requested_phase,
                completed_phase=None,
                phase_output=None,
                validation_issues=(
                    "SOURCE_BASELINE_EVENT_NOT_PUBLISHED_STOP",
                ),
                stop_code="STOP_EVENT1_NOT_POSTVERIFIED",
                called_port="observe_event1_publication",
            )
        issues = _event1_issues(
            event1_artifact,
            event1_external_identity,
            observed,
        )
        return _result(
            requested_phase=requested_phase,
            completed_phase=requested_phase if not issues else None,
            phase_output=observed if not issues else None,
            validation_issues=issues,
            stop_code=(
                "AUTHORITY_STOP_EVENT1_POSTVERIFIED"
                if not issues
                else "STOP_EVENT1_NOT_POSTVERIFIED"
            ),
            called_port="observe_event1_publication",
        )

    event_issues = _event1_issues(
        event1_artifact,
        event1_external_identity,
        event1_publication_state,
    )
    if event_issues:
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=event_issues,
            stop_code="STOP_EVENT1_NOT_POSTVERIFIED",
            called_port=None,
        )

    if requested_phase == "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT":
        try:
            observed = ports.run_bootstrap_preflight(
                event1_artifact=event1_artifact,
                event1_external_identity=event1_external_identity,
                event1_publication_state=event1_publication_state,
            )
        except Exception:
            observed = None
        issues = _readiness_issues(
            event1_artifact=event1_artifact,
            event1_external_identity=event1_external_identity,
            event1_publication_state=event1_publication_state,
            bootstrap_state=observed,
        )
        return _result(
            requested_phase=requested_phase,
            completed_phase=requested_phase if not issues else None,
            phase_output=observed if not issues else None,
            validation_issues=issues,
            stop_code=(
                "AUTHORITY_STOP_BOOTSTRAP_PREFLIGHT_READY"
                if not issues
                else "PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP"
            ),
            called_port="run_bootstrap_preflight",
        )

    readiness_issues = _readiness_issues(
        event1_artifact=event1_artifact,
        event1_external_identity=event1_external_identity,
        event1_publication_state=event1_publication_state,
        bootstrap_state=bootstrap_state,
    )
    if readiness_issues:
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=readiness_issues,
            stop_code="PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP",
            called_port=None,
        )
    readiness = bootstrap_state["readiness_receipt"]

    if requested_phase == (
        "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED"
    ):
        try:
            observed = ports.publish_readiness(artifact=readiness)
        except Exception:
            observed = None
        issues = _readiness_publication_issues(
            event1_external_identity=event1_external_identity,
            readiness=readiness,
            readiness_publication_state=observed,
        )
        return _result(
            requested_phase=requested_phase,
            completed_phase=requested_phase if not issues else None,
            phase_output=observed if not issues else None,
            validation_issues=issues,
            stop_code=(
                "AUTHORITY_STOP_READINESS_POSTVERIFIED"
                if not issues
                else "READINESS_RECEIPT_NOT_PUBLISHED_STOP"
            ),
            called_port="publish_readiness",
        )

    if (
        type(readiness_publication_state) is not dict
        or _readiness_publication_issues(
            event1_external_identity=event1_external_identity,
            readiness=readiness,
            readiness_publication_state=readiness_publication_state,
        )
    ):
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=("READINESS_RECEIPT_NOT_PUBLISHED_STOP",),
            stop_code="READINESS_RECEIPT_NOT_PUBLISHED_STOP",
            called_port=None,
        )
    readiness_identity = readiness_publication_state[
        "artifact_external_identity"
    ]

    reservation_issues = _reservation_issues(
        event1_artifact=event1_artifact,
        event1_external_identity=event1_external_identity,
        readiness=readiness,
        readiness_external_identity=readiness_identity,
        reservation=reservation_artifact,
    )
    if reservation_issues:
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=reservation_issues,
            stop_code=reservation_issues[0],
            called_port=None,
        )

    if requested_phase == "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED":
        try:
            observed = ports.publish_reservation(
                artifact=reservation_artifact,
            )
        except Exception:
            observed = None
        issues = _reservation_publication_issues(
            readiness_external_identity=readiness_identity,
            reservation=reservation_artifact,
            reservation_publication_state=observed,
        )
        return _result(
            requested_phase=requested_phase,
            completed_phase=requested_phase if not issues else None,
            phase_output=observed if not issues else None,
            validation_issues=issues,
            stop_code=(
                "AUTHORITY_STOP_RESERVATION_POSTVERIFIED"
                if not issues
                else "RESERVATION_PUBLICATION_OUTCOME_UNKNOWN_STOP"
            ),
            called_port="publish_reservation",
        )

    if (
        type(reservation_publication_state) is not dict
        or _reservation_publication_issues(
            readiness_external_identity=readiness_identity,
            reservation=reservation_artifact,
            reservation_publication_state=reservation_publication_state,
        )
    ):
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=("RESERVATION_NOT_PUBLISHED_STOP",),
            stop_code="RESERVATION_NOT_PUBLISHED_STOP",
            called_port=None,
        )
    reservation_identity = reservation_publication_state[
        "artifact_external_identity"
    ]

    authority_issues = _formal_authority_issues(
        grant=formal_authority_grant,
        reservation=reservation_artifact,
        readiness_external_identity=readiness_identity,
        reservation_external_identity=reservation_identity,
    )
    if authority_issues:
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=authority_issues,
            stop_code="FORMAL_EXACT134_NOT_AUTHORIZED",
            called_port=None,
        )
    try:
        observed = ports.spawn_exact134_once(
            authority_grant=formal_authority_grant,
            event1_artifact=event1_artifact,
            event1_external_identity=event1_external_identity,
            event1_publication_state=event1_publication_state,
            reservation=reservation_artifact,
            readiness=readiness,
            readiness_external_identity=readiness_identity,
            reservation_external_identity=reservation_identity,
            readiness_publication_state=readiness_publication_state,
            reservation_publication_state=reservation_publication_state,
        )
    except Exception:
        observed = None
    attempt_issues = (
        validate_recovery_epoch002_attempt_state(observed)
        if type(observed) is dict and not _contains_forbidden_key(observed)
        else ("FORMAL_ATTEMPT_FORBIDDEN",)
    )
    operational_attempt_issues = (
        _operational_attempt_issues(
            state=observed,
            reservation=reservation_artifact,
            readiness=readiness,
            reservation_external_identity=reservation_identity,
        )
        if type(observed) is dict
        else ("FORMAL_ATTEMPT_FORBIDDEN",)
    )
    if operational_attempt_issues:
        attempt_issues = operational_attempt_issues
    accepted = not attempt_issues or (
        attempt_issues in {
            (code,)
            for code in _ACCEPTED_ATTEMPT_STOPS
        }
    )
    if accepted:
        checkpoints = observed.get("checkpoint_chain")
        if (
            type(checkpoints) is not list
            or not checkpoints
            or _spawn_intent_issues(
                checkpoint=checkpoints[0],
                reservation=reservation_artifact,
                readiness=readiness,
            )
        ):
            accepted = False
            attempt_issues = ("CHECKPOINT_INVALID",)
    if not accepted:
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=attempt_issues,
            stop_code="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
            called_port="spawn_exact134_once",
        )
    stop_code = (
        attempt_issues[0]
        if attempt_issues
        else "AUTHORITY_STOP_TERMINAL_PUBLISHED"
    )
    return _result(
        requested_phase=requested_phase,
        completed_phase=requested_phase,
        phase_output=observed,
        validation_issues=attempt_issues,
        stop_code=stop_code,
        called_port="spawn_exact134_once",
    )


__all__ = [
    "RECOVERY_EPOCH002_FORMAL_PARENT_PROTOCOL",
    "RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_SCHEMA",
    "RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER",
    "RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES",
    "RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES",
    "RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS",
    "RECOVERY_EPOCH002_FORMAL_AUTHORITY_GRANT_KEYS",
    "RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_KEYS",
    "RecoveryEpoch002ParentPorts",
    "validate_recovery_epoch002_parent_state",
    "validate_recovery_epoch002_parent_execution_state",
    "validate_recovery_epoch002_parent_phase_result",
    "next_recovery_epoch002_parent_action",
    "execute_recovery_epoch002_parent_phase",
]
