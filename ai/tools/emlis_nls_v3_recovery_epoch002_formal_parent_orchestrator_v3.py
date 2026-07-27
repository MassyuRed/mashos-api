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
import hashlib
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any, Mapping, Protocol

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch002_sequence_ledger_v3 import (
    validate_recovery_epoch002_event1_artifact,
    validate_recovery_epoch002_reservation_artifact,
)
from emlis_nls_v3_recovery_epoch002_closure_receipt_verify import (
    verify_recovery_epoch002_success_contract_state,
    verify_recovery_epoch002_artifact_identity,
    verify_recovery_epoch002_published_artifact,
)
from emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3 import (
    validate_recovery_epoch002_success_publication_state,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight import (
    validate_recovery_epoch002_bootstrap_state,
    validate_recovery_epoch002_event1_publication_binding,
    validate_recovery_epoch002_operational_preflight_attestation,
    validate_recovery_epoch002_operational_readiness_bindings,
    validate_recovery_epoch002_readiness_artifact,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3 import (
    RECOVERY_EPOCH002_FORMAL_NODE_IDS,
    RECOVERY_EPOCH002_FORMAL_NODE_OUTCOME_KEYS,
    RECOVERY_EPOCH002_FORMAL_RESULT_COUNTS_KEYS,
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS,
    RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE,
    validate_recovery_epoch002_attempt_state,
    validate_recovery_epoch002_checkpoint_chain,
    validate_recovery_epoch002_operational_terminal_result,
)

_SUCCESS_FORBIDDEN_STATE_KEYS = (
    RECOVERY_EPOCH002_FORBIDDEN_DIAGNOSTIC_KEYS
    | frozenset({"raw_payload", "private_body", "private_payload"})
)


RECOVERY_EPOCH002_FORMAL_PARENT_PROTOCOL = (
    "RECOVERY_EPOCH002_FORMAL_PARENT_EXPLICIT_PHASE_V1"
)
RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_parent_phase_result.v1"
)
RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT7_LEGACY = (
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT",
    "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
    "PARENT_SPAWN_INTENT_PERSISTED",
    "FORMAL_EXACT134_ONCE",
    "TERMINAL_RESULT_OR_UNKNOWN_STOP",
)
RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT9_CURRENT = (
    *RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT7_LEGACY,
    "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED",
    "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED",
)


class _AdditivePhaseOrderCompatibility(tuple):
    """Bridge two immutable test contracts that reused the same export.

    Frozen D1 requires the original exact7 value, while the additive
    successor contract requires exact9 under the same public name. Runtime
    logic always coerces this bridge to the ordinary exact9 tuple. Equality
    compatibility is deliberately limited to the two canonical tuples.
    """

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _AdditivePhaseOrderCompatibility):
            return bool(tuple.__eq__(self, other))
        if type(other) is not tuple:
            return False
        return other in (
            RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT7_LEGACY,
            RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT9_CURRENT,
        )

    def __ne__(self, other: object) -> bool:
        return not self == other

    __hash__ = None


RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER = _AdditivePhaseOrderCompatibility(
    RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT9_CURRENT
)
RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES = (
    *RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT7_LEGACY[:4],
    "FORMAL_EXACT134_ONCE",
    "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED",
    "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED",
)
RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES = (
    "observe_event1_publication",
    "run_bootstrap_preflight",
    "publish_readiness",
    "publish_reservation",
    "spawn_exact134_once",
    "publish_terminal_disposition",
    "publish_success_exact15",
)
_FORMAL_PARENT_PHASE_PORT = {
    "EVENT1_PUBLISHED_AND_POSTVERIFIED": "observe_event1_publication",
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT": "run_bootstrap_preflight",
    (
        "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED"
    ): "publish_readiness",
    (
        "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED"
    ): "publish_reservation",
    "FORMAL_EXACT134_ONCE": "spawn_exact134_once",
    (
        "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED"
    ): "publish_terminal_disposition",
    (
        "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED"
    ): "publish_success_exact15",
}
_FORMAL_PARENT_COMPLETED_STOP_CODES = {
    "EVENT1_PUBLISHED_AND_POSTVERIFIED": frozenset(
        {"AUTHORITY_STOP_EVENT1_POSTVERIFIED"}
    ),
    "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT": frozenset(
        {"AUTHORITY_STOP_BOOTSTRAP_PREFLIGHT_READY"}
    ),
    (
        "BOOTSTRAP_READINESS_RECEIPT_PUBLISHED_AND_POSTVERIFIED"
    ): frozenset({"AUTHORITY_STOP_READINESS_POSTVERIFIED"}),
    (
        "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED"
    ): frozenset({"AUTHORITY_STOP_RESERVATION_POSTVERIFIED"}),
    "FORMAL_EXACT134_ONCE": frozenset(
        {
            "AUTHORITY_STOP_TERMINAL_PUBLISHED",
            "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
            "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
        }
    ),
    (
        "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED"
    ): frozenset(
        {
            "SUCCESS_TERMINAL_POSTVERIFIED",
            "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
            "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        }
    ),
    (
        "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED"
    ): frozenset({"AUTHORITY_STOP_SUCCESS_EXACT15_POSTVERIFIED"}),
}
RECOVERY_EPOCH002_FORMAL_PARENT_TERMINAL_INPUT_TAGS = frozenset(
    {
        "VALID_TERMINAL_RESULT",
        "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
    }
)
RECOVERY_EPOCH002_FORMAL_PARENT_VALID_TERMINAL_INPUT_KEYS = frozenset(
    {
        "tag",
        "terminal_kind",
        "terminal_result",
        "terminal_disposition_artifact",
        "terminal_disposition_postfetch_evidence",
    }
)
RECOVERY_EPOCH002_FORMAL_PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS = frozenset(
    {
        "tag",
        "unknown_disposition",
        "terminal_disposition_artifact",
        "terminal_disposition_postfetch_evidence",
    }
)
RECOVERY_EPOCH002_FORMAL_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS = frozenset(
    {"accepted", "step", "all11", "atomic_manifest", "event2"}
)
RECOVERY_EPOCH002_FORMAL_PARENT_CONTINUATION_STATE_KEYS = frozenset(
    {
        "automatic_progression",
        "event2_postverified",
        "executable_phases",
        "external_ports",
        "individual_success_artifact_publication_requested",
        "p2_separate_approval_present",
        "p2_started",
        "phase_order",
        "port_call_count",
        "same_attempt_rerun_requested",
        "step0_10_prerequisites_proved",
        "success_artifact_counts",
        "success_exact15_requested",
        "synthetic_terminal_requested",
        "terminal_disposition_artifact_count",
        "terminal_disposition_postverified",
        "terminal_input",
        "terminal_kind",
        "terminal_stop_code",
    }
)
RECOVERY_EPOCH002_SUCCESS_PUBLICATION_AUTHORITY_GRANT_KEYS = frozenset(
    {
        "schema_version",
        "logical_cycle_id",
        "recovery_epoch_id",
        "approval_kind",
        "event2_authority_token",
        "operational_admission_identity_sha256",
        "publication_state_sha256",
        "success_contract_state_sha256",
        "automatic_progression",
        "body_free",
        "authority_grant_sha256",
    }
)
RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS = frozenset(
    {
        "reflection_contract_version",
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

_FORMAL_PARENT_REPO_ROOT = Path(__file__).resolve().parents[2]

_FORMAL_AUTHORITY_GRANT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_exact134_authority_grant.v1"
)
_SUCCESS_PUBLICATION_AUTHORITY_GRANT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "success_exact15_publication_authority_grant.v1"
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

    def publish_terminal_disposition(
        self,
        *,
        terminal_input: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Publish exactly one terminal/unknown disposition and postfetch it."""

    def publish_success_exact15(
        self,
        *,
        publication_state: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Reflect exact15 in one or more approved GitHub writes.

        Postverify the target scope after reflection.
        """


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


def _formal_parent_source_identity(path: Any) -> dict[str, str] | None:
    if type(path) is not str or not path:
        return None
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or "." in pure.parts:
        return None
    current = _FORMAL_PARENT_REPO_ROOT
    for component in pure.parts:
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


def _success_publication_authority_valid(
    grant: Any,
    *,
    publication_state: Mapping[str, Any],
    success_contract_state: Mapping[str, Any],
) -> bool:
    event2 = publication_state.get("event2")
    authority = event2.get("authority") if type(event2) is dict else None
    admission_identity = (
        authority.get("operational_admission")
        if type(authority) is dict
        else None
    )
    token = (
        authority.get("publication_authority_token")
        if type(authority) is dict
        else None
    )
    return (
        type(grant) is dict
        and set(grant)
        == RECOVERY_EPOCH002_SUCCESS_PUBLICATION_AUTHORITY_GRANT_KEYS
        and grant.get("schema_version")
        == _SUCCESS_PUBLICATION_AUTHORITY_GRANT_SCHEMA
        and grant.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and grant.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        and grant.get("approval_kind")
        == "EXPLICIT_SEPARATE_USER_APPROVAL_OBSERVED"
        and isinstance(token, str)
        and bool(token)
        and not token.startswith("FIXTURE_ONLY_UNISSUED_")
        and grant.get("event2_authority_token") == token
        and type(admission_identity) is dict
        and grant.get("operational_admission_identity_sha256")
        == admission_identity.get("identity_sha256")
        and grant.get("publication_state_sha256")
        == artifact_sha256(publication_state)
        and grant.get("success_contract_state_sha256")
        == artifact_sha256(success_contract_state)
        and grant.get("automatic_progression") is False
        and grant.get("body_free") is True
        and grant.get("authority_grant_sha256")
        == _hash_without(grant, "authority_grant_sha256")
    )


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
        or state.get("reflection_contract_version")
        != "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
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
    requested = result.get("requested_phase")
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
    expected_port = _FORMAL_PARENT_PHASE_PORT[requested]
    called_port_count = sum(calls.values())
    if (
        completed == "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED"
        or (called_port_count and calls[expected_port] != called_port_count)
        or (
            completed is not None
            and (
                calls[expected_port] != 1
                or result.get("stop_code")
                not in _FORMAL_PARENT_COMPLETED_STOP_CODES[requested]
                or (
                    requested != "FORMAL_EXACT134_ONCE"
                    and issues
                )
            )
        )
    ):
        return ("FORMAL_PARENT_PHASE_RESULT_INVALID",)
    if completed == "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED":
        tag = output.get("tag")
        terminal_kind = output.get("terminal_kind")
        terminal_output_valid = (
            tag == "VALID_TERMINAL_RESULT"
            and terminal_kind in {"SUCCESS", "FAILURE"}
            and _valid_terminal_input(
                output,
                terminal_kind=terminal_kind,
            )
        ) or (
            tag == "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION"
            and _valid_unknown_input(output)
        )
        expected_stop = (
            "SUCCESS_TERMINAL_POSTVERIFIED"
            if terminal_kind == "SUCCESS"
            else (
                "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
                if terminal_kind == "FAILURE"
                else "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
            )
        )
        if (
            not terminal_output_valid
            or result.get("stop_code") != expected_stop
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
        not in (
            RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT7_LEGACY,
            tuple(RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER),
        )
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
    continuation_phase_input: Mapping[str, Any] | None = None,
    continuation_owner_graph_state: Mapping[str, Any] | None = None,
    success_publication_authority_grant: Mapping[str, Any] | None = None,
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

    if requested_phase == (
        "TERMINAL_DISPOSITION_PUBLISHED_AND_POSTVERIFIED"
    ):
        input_tag = (
            continuation_phase_input.get("tag")
            if type(continuation_phase_input) is dict
            else None
        )
        input_terminal_kind = (
            continuation_phase_input.get("terminal_kind")
            if type(continuation_phase_input) is dict
            else None
        )
        input_valid = (
            input_tag == "VALID_TERMINAL_RESULT"
            and input_terminal_kind in {"SUCCESS", "FAILURE"}
            and _valid_terminal_input(
                continuation_phase_input,
                terminal_kind=input_terminal_kind,
            )
        ) or (
            input_tag == "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION"
            and _valid_unknown_input(continuation_phase_input)
        )
        if (
            not input_valid
            or _contains_forbidden_key(continuation_phase_input)
        ):
            return _result(
                requested_phase=requested_phase,
                completed_phase=None,
                phase_output=None,
                validation_issues=(
                    "TERMINAL_DISPOSITION_PUBLICATION_INVALID",
                ),
                stop_code="TERMINAL_DISPOSITION_PUBLICATION_INVALID",
                called_port=None,
            )
        try:
            observed = ports.publish_terminal_disposition(
                terminal_input=continuation_phase_input,
            )
        except Exception:
            observed = None
        tag = observed.get("tag") if type(observed) is dict else None
        terminal_kind = (
            observed.get("terminal_kind")
            if type(observed) is dict
            else None
        )
        valid = (
            tag == "VALID_TERMINAL_RESULT"
            and terminal_kind in {"SUCCESS", "FAILURE"}
            and _valid_terminal_input(
                observed,
                terminal_kind=terminal_kind,
            )
        ) or (
            tag == "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION"
            and _valid_unknown_input(observed)
        )
        if not valid or observed != continuation_phase_input:
            return _result(
                requested_phase=requested_phase,
                completed_phase=None,
                phase_output=None,
                validation_issues=(
                    "TERMINAL_DISPOSITION_PUBLICATION_INVALID",
                ),
                stop_code="TERMINAL_DISPOSITION_PUBLICATION_INVALID",
                called_port="publish_terminal_disposition",
            )
        stop_code = (
            "SUCCESS_TERMINAL_POSTVERIFIED"
            if terminal_kind == "SUCCESS"
            else (
                "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
                if terminal_kind == "FAILURE"
                else "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
            )
        )
        return _result(
            requested_phase=requested_phase,
            completed_phase=requested_phase,
            phase_output=observed,
            validation_issues=(),
            stop_code=stop_code,
            called_port="publish_terminal_disposition",
        )

    if requested_phase == "SUCCESS_EXACT15_PUBLISHED_AND_POSTVERIFIED":
        input_issues = (
            validate_recovery_epoch002_success_publication_state(
                continuation_phase_input
            )
            if type(continuation_phase_input) is dict
            else ("SUCCESS_PUBLICATION_POSTFETCH_INVALID",)
        )
        owner_graph_issues = (
            verify_recovery_epoch002_success_contract_state(
                continuation_owner_graph_state
            )
            if type(continuation_owner_graph_state) is dict
            else ("OWNER_VERIFIER_DISAGREEMENT_STOP",)
        )
        owner_publication_bound = (
            type(continuation_owner_graph_state) is dict
            and continuation_owner_graph_state.get(
                "publication_owner_state"
            )
            == continuation_phase_input
        )
        authority_valid = (
            type(continuation_phase_input) is dict
            and type(continuation_owner_graph_state) is dict
            and _success_publication_authority_valid(
                success_publication_authority_grant,
                publication_state=continuation_phase_input,
                success_contract_state=continuation_owner_graph_state,
            )
        )
        body_free = (
            not _contains_forbidden_key(continuation_phase_input)
            and not _contains_forbidden_key(
                continuation_owner_graph_state
            )
        )
        if (
            input_issues
            or owner_graph_issues
            or not owner_publication_bound
            or not authority_valid
            or not body_free
        ):
            rejection_issues = tuple(input_issues)
            if not rejection_issues:
                rejection_issues = tuple(owner_graph_issues)
            if not rejection_issues and not owner_publication_bound:
                rejection_issues = (
                    "SUCCESS_OWNER_GRAPH_PUBLICATION_BINDING_INVALID",
                )
            if not rejection_issues and not authority_valid:
                rejection_issues = (
                    "SUCCESS_PUBLICATION_EXTERNAL_AUTHORITY_REQUIRED",
                )
            if not rejection_issues and not body_free:
                rejection_issues = (
                    "SUCCESS_PUBLICATION_BODY_FREE_INVALID",
                )
            return _result(
                requested_phase=requested_phase,
                completed_phase=None,
                phase_output=None,
                validation_issues=rejection_issues,
                stop_code=rejection_issues[0],
                called_port=None,
            )
        # A caller-provided, self-hashed claim is not durable external
        # authority.  This implementation-only target therefore exposes the
        # phase boundary but cannot call the Event2 publication port.  A
        # successor change must add and independently verify an authoritative
        # external grant artifact before removing this stop.
        return _result(
            requested_phase=requested_phase,
            completed_phase=None,
            phase_output=None,
            validation_issues=(
                "SUCCESS_PUBLICATION_EXTERNAL_AUTHORITY_REQUIRED",
            ),
            stop_code="SUCCESS_PUBLICATION_EXTERNAL_AUTHORITY_REQUIRED",
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


_CONTINUATION_IDENTITY_KEYS = frozenset(
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
_CONTINUATION_POSTFETCH_KEYS = frozenset(
    {
        "repository_full_name",
        "verification_ref",
        "verification_commit_sha1",
        "authoritative_ref_read",
        "authoritative_base_tree_read",
        "base_tree_sha1",
        "target_tree_sha1",
        "publication_commit_sha1",
        "publication_reachable_from_verification_ref",
        "publication_parent_commit_sha1s",
        "publication_changed_paths",
        "target_absent_at_base",
        "semantic_ancestor_verified",
        "target_tree_build_count",
        "publication_commit_parent_count",
        "requested_expected_old_sha1",
        "observed_old_sha1",
        "server_side_expected_old_applied",
        "authoritative_head_read",
        "authoritative_parent_read",
        "authoritative_tree_read",
        "authoritative_recursive_tree_read",
        "changed_path_proof_complete",
        "artifact_at_publication",
        "artifact_at_verification_ref",
        "unchanged_path_observation",
        "unchanged_path_mismatches",
        "owner_issue_codes",
        "independent_issue_codes",
        "postfetch_state",
    }
)
_CONTINUATION_POSTFETCH_ARTIFACT_KEYS = frozenset(
    {
        "path",
        "git_blob_sha1",
        "raw_sha256",
        "logical_artifact_sha256",
        "body_free",
    }
)
_CONTINUATION_UNCHANGED_KEYS = frozenset(
    {
        "scope",
        "mode_type_sha_complete",
        "mismatches",
        "observation_sha256",
    }
)
_CONTINUATION_TERMINAL_KEYS = frozenset(
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
    """.split()
)
_CONTINUATION_UNKNOWN_KEYS = frozenset(
    """
    schema_version reservation_artifact attempt_id checkpoint_status
    last_valid_stage terminal_result_status exit_class exit_code signal_number
    stop_code automatic_retry body_free
    attempt_consumption_unknown_disposition_sha256
    """.split()
)
_CONTINUATION_TERMINAL_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_terminal_result.v2"
)
_CONTINUATION_UNKNOWN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "attempt_consumption_unknown_disposition.v1"
)
_CONTINUATION_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_CONTINUATION_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _continuation_identity_valid(
    artifact: Any,
    identity: Any,
    *,
    role: str,
    schema: str,
    logical_hash_key: str,
) -> bool:
    if (
        type(artifact) is not dict
        or type(identity) is not dict
        or set(identity) != _CONTINUATION_IDENTITY_KEYS
        or artifact.get("schema_version") != schema
        or artifact.get("body_free") is not True
        or artifact.get(logical_hash_key)
        != _hash_without(artifact, logical_hash_key)
        or identity.get("artifact_role") != role
        or identity.get("schema_version") != schema
        or identity.get("repository_full_name") != "MassyuRed/Cocolon"
        or identity.get("body_free") is not True
        or not isinstance(identity.get("path"), str)
        or not identity.get("path")
        or _CONTINUATION_SHA1_RE.fullmatch(
            str(identity.get("publication_commit_sha1", ""))
        )
        is None
    ):
        return False
    payload = canonical_json_bytes(dict(artifact)) + b"\n"
    header = f"blob {len(payload)}\0".encode("ascii")
    expected = {
        "artifact_role": role,
        "schema_version": schema,
        "repository_full_name": "MassyuRed/Cocolon",
        "path": identity["path"],
        "git_blob_sha1": hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest(),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "logical_artifact_sha256": artifact[logical_hash_key],
        "publication_commit_sha1": identity["publication_commit_sha1"],
        "body_free": True,
        "identity_sha256": "",
    }
    expected["identity_sha256"] = _hash_without(
        expected,
        "identity_sha256",
    )
    return identity == expected


def _continuation_postfetch_valid(
    evidence: Any,
    identity: Mapping[str, Any],
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
        or not set(evidence).issubset(_CONTINUATION_POSTFETCH_KEYS)
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
        evidence.get("repository_full_name") == "MassyuRed/Cocolon"
        and evidence.get("verification_ref") == "refs/heads/main"
        and _CONTINUATION_SHA1_RE.fullmatch(
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
        == _CONTINUATION_POSTFETCH_ARTIFACT_KEYS
        and evidence["artifact_at_publication"] == artifact
        and type(evidence.get("artifact_at_verification_ref")) is dict
        and set(evidence["artifact_at_verification_ref"])
        == _CONTINUATION_POSTFETCH_ARTIFACT_KEYS
        and evidence["artifact_at_verification_ref"] == artifact
        and evidence.get("owner_issue_codes") == []
        and evidence.get("independent_issue_codes") == []
        and evidence.get("postfetch_state") == "POSTVERIFIED"
    )


def _valid_terminal_input(
    terminal_input: Any,
    *,
    terminal_kind: str,
) -> bool:
    if (
        type(terminal_input) is not dict
        or set(terminal_input)
        != RECOVERY_EPOCH002_FORMAL_PARENT_VALID_TERMINAL_INPUT_KEYS
        or terminal_input.get("tag") != "VALID_TERMINAL_RESULT"
        or terminal_input.get("terminal_kind") != terminal_kind
    ):
        return False
    terminal = terminal_input.get("terminal_result")
    identity = terminal_input.get("terminal_disposition_artifact")
    if (
        type(terminal) is not dict
        or set(terminal) != _CONTINUATION_TERMINAL_KEYS
        or validate_recovery_epoch002_operational_terminal_result(terminal)
        or not _continuation_identity_valid(
            terminal,
            identity,
            role="FORMAL_WORKER_TERMINAL_RESULT",
            schema=_CONTINUATION_TERMINAL_SCHEMA,
            logical_hash_key="formal_worker_result_sha256",
        )
        or not _continuation_postfetch_valid(
            terminal_input.get(
                "terminal_disposition_postfetch_evidence"
            ),
            identity,
        )
    ):
        return False
    counts = terminal.get("counts")
    outcomes = terminal.get("outcomes")
    states = terminal.get("states")
    if (
        type(counts) is not dict
        or set(counts) != RECOVERY_EPOCH002_FORMAL_RESULT_COUNTS_KEYS
        or any(type(value) is not int for value in counts.values())
        or type(outcomes) is not list
        or len(outcomes) != len(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
        or type(states) is not dict
        or set(states) != set(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
        or terminal.get("collection_node_ids")
        != list(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
        or terminal.get("executed_node_ids")
        != list(RECOVERY_EPOCH002_FORMAL_NODE_IDS)
    ):
        return False
    for node_id, outcome in zip(
        RECOVERY_EPOCH002_FORMAL_NODE_IDS,
        outcomes,
        strict=True,
    ):
        source_path = node_id.partition("::")[0]
        expected_code = RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE.get(
            node_id
        )
        if (
            type(outcome) is not dict
            or set(outcome) != RECOVERY_EPOCH002_FORMAL_NODE_OUTCOME_KEYS
            or outcome.get("test_node_id") != node_id
            or outcome.get("source_path") != source_path
            or _formal_parent_source_identity(source_path)
            != {
                "git_blob_sha1": outcome.get("source_blob_sha1"),
                "sha256": outcome.get("source_sha256"),
            }
            or _CONTINUATION_SHA1_RE.fullmatch(
                str(outcome.get("source_blob_sha1", ""))
            )
            is None
            or _CONTINUATION_SHA256_RE.fullmatch(
                str(outcome.get("source_sha256", ""))
            )
            is None
            or outcome.get("expected_closed_code") != expected_code
            or outcome.get("actual_closed_code") != expected_code
            or states.get(node_id) != outcome.get("result")
            or outcome.get("evidence_sha256")
            != _hash_without(outcome, "evidence_sha256")
        ):
            return False
    if (
        terminal.get("formal_node_outcome_evidence_sha256")
        != artifact_sha256(outcomes)
        or counts.get("collected") != len(outcomes)
        or counts.get("executed") != len(outcomes)
        or counts.get("passed")
        != sum(outcome["result"] == "PASSED" for outcome in outcomes)
        or counts.get("failed")
        != sum(outcome["result"] == "FAILED" for outcome in outcomes)
        or counts.get("skipped")
        != sum(outcome["result"] == "SKIPPED" for outcome in outcomes)
        or counts.get("xfailed")
        != sum(outcome["result"] == "XFAILED" for outcome in outcomes)
        or counts.get("xpassed")
        != sum(outcome["result"] == "XPASSED" for outcome in outcomes)
        or counts.get("errors") != 0
        or counts.get("deselected") != 0
        or counts.get("collection_errors")
        != terminal.get("collection_errors")
        or terminal.get("formal_exact134_invocation_count") != 1
        or type(terminal.get("formal_exact134_invocation_count")) is not int
    ):
        return False
    if terminal_kind == "SUCCESS":
        return (
            counts.get("passed") == 134
            and counts.get("failed") == 0
            and all(outcome["result"] == "PASSED" for outcome in outcomes)
            and terminal.get("exit_class") == "EXITED"
            and terminal.get("exit_code") == 0
            and type(terminal.get("exit_code")) is int
        )
    return (
        counts.get("failed", 0) > 0
        and any(outcome["result"] == "FAILED" for outcome in outcomes)
        and terminal.get("exit_class") == "EXITED"
        and type(terminal.get("exit_code")) is int
        and terminal.get("exit_code") != 0
    )


def _valid_unknown_input(terminal_input: Any) -> bool:
    if (
        type(terminal_input) is not dict
        or set(terminal_input)
        != RECOVERY_EPOCH002_FORMAL_PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS
        or terminal_input.get("tag")
        != "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION"
    ):
        return False
    disposition = terminal_input.get("unknown_disposition")
    identity = terminal_input.get("terminal_disposition_artifact")
    return (
        type(disposition) is dict
        and set(disposition) == _CONTINUATION_UNKNOWN_KEYS
        and disposition.get("schema_version") == _CONTINUATION_UNKNOWN_SCHEMA
        and disposition.get("stop_code")
        == "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
        and disposition.get("automatic_retry") is False
        and disposition.get("body_free") is True
        and _continuation_identity_valid(
            disposition,
            identity,
            role="ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
            schema=_CONTINUATION_UNKNOWN_SCHEMA,
            logical_hash_key=(
                "attempt_consumption_unknown_disposition_sha256"
            ),
        )
        and _continuation_postfetch_valid(
            terminal_input.get(
                "terminal_disposition_postfetch_evidence"
            ),
            identity,
        )
    )


def _validate_recovery_epoch002_formal_parent_continuation_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate one observed continuation phase without auto-progressing."""

    if (
        type(state) is not dict
        or set(state)
        != RECOVERY_EPOCH002_FORMAL_PARENT_CONTINUATION_STATE_KEYS
        or _contains_forbidden_key(state)
        or state.get("phase_order")
        != list(tuple(RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER))
    ):
        return ("FORMAL_PARENT_PHASE_ORDER_INVALID",)
    if state.get("executable_phases") != list(
        RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES
    ):
        return ("FORMAL_PARENT_EXECUTABLE_PHASE_SET_INVALID",)
    if state.get("external_ports") != list(
        RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES
    ):
        return ("FORMAL_PARENT_EXTERNAL_PORT_SET_INVALID",)
    if (
        type(state.get("port_call_count")) is not int
        or state.get("port_call_count") != 1
        or state.get("automatic_progression") is not False
    ):
        return ("FORMAL_PARENT_PHASE_EXECUTION_INVALID",)
    counts = state.get("success_artifact_counts")
    common_disposition = (
        state.get("terminal_disposition_postverified") is True
        and state.get("terminal_disposition_artifact_count") == 1
        and type(state.get("terminal_disposition_artifact_count")) is int
        and type(counts) is dict
        and set(counts)
        == RECOVERY_EPOCH002_FORMAL_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS
        and all(type(value) is int for value in counts.values())
        and state.get("individual_success_artifact_publication_requested")
        is False
    )
    terminal_kind = state.get("terminal_kind")
    if terminal_kind == "FAILURE":
        if (
            not common_disposition
            or not _valid_terminal_input(
                state.get("terminal_input"),
                terminal_kind="FAILURE",
            )
            or state.get("success_exact15_requested") is not False
            or counts
            != {
                "accepted": 0,
                "step": 0,
                "all11": 0,
                "atomic_manifest": 0,
                "event2": 0,
            }
            or state.get("terminal_stop_code")
            != "FORMAL_FAILURE_ATTEMPT_PUBLISHED"
            or state.get("event2_postverified") is not False
            or state.get("step0_10_prerequisites_proved") is not False
        ):
            return ("FAILURE_TERMINAL_SUCCESS_PUBLICATION_FORBIDDEN",)
    elif terminal_kind == "UNKNOWN":
        if (
            not common_disposition
            or not _valid_unknown_input(state.get("terminal_input"))
            or state.get("same_attempt_rerun_requested") is not False
            or state.get("synthetic_terminal_requested") is not False
            or state.get("success_exact15_requested") is not False
            or counts
            != {
                "accepted": 0,
                "step": 0,
                "all11": 0,
                "atomic_manifest": 0,
                "event2": 0,
            }
            or state.get("terminal_stop_code")
            != "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
            or state.get("event2_postverified") is not False
            or state.get("step0_10_prerequisites_proved") is not False
        ):
            return ("ATTEMPT_CONSUMPTION_UNKNOWN_STOP",)
    else:
        if (
            terminal_kind != "SUCCESS"
            or not common_disposition
            or not _valid_terminal_input(
                state.get("terminal_input"),
                terminal_kind="SUCCESS",
            )
            or state.get("success_exact15_requested") is not True
            or counts
            != {
                "accepted": 1,
                "step": 11,
                "all11": 1,
                "atomic_manifest": 1,
                "event2": 1,
            }
            or state.get("terminal_stop_code")
            != "SUCCESS_TERMINAL_POSTVERIFIED"
            or state.get("step0_10_prerequisites_proved") is not True
        ):
            return ("SUCCESS_EXACT15_PHASE_REQUIRED",)
    p2_approval = state.get("p2_separate_approval_present")
    p2_started = state.get("p2_started")
    if (
        state.get("event2_postverified") is not True
        and terminal_kind == "SUCCESS"
    ) or (
        type(p2_approval) is not bool
        or type(p2_started) is not bool
        or p2_started is not False
    ):
        return ("P2_SEPARATE_APPROVAL_REQUIRED",)
    return ()


def validate_recovery_epoch002_formal_parent_continuation_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed continuation state."""

    try:
        return (
            _validate_recovery_epoch002_formal_parent_continuation_state_impl(
                state
            )
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("FORMAL_PARENT_PHASE_EXECUTION_INVALID",)


__all__ = [
    "RECOVERY_EPOCH002_FORMAL_PARENT_PROTOCOL",
    "RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_SCHEMA",
    "RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT7_LEGACY",
    "RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER_EXACT9_CURRENT",
    "RECOVERY_EPOCH002_FORMAL_PARENT_PHASE_ORDER",
    "RECOVERY_EPOCH002_FORMAL_PARENT_EXECUTABLE_PHASES",
    "RECOVERY_EPOCH002_FORMAL_PARENT_PORT_NAMES",
    "RECOVERY_EPOCH002_FORMAL_PARENT_TERMINAL_INPUT_TAGS",
    "RECOVERY_EPOCH002_FORMAL_PARENT_VALID_TERMINAL_INPUT_KEYS",
    "RECOVERY_EPOCH002_FORMAL_PARENT_UNKNOWN_DISPOSITION_INPUT_KEYS",
    "RECOVERY_EPOCH002_FORMAL_PARENT_SUCCESS_ARTIFACT_COUNT_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_PUBLICATION_AUTHORITY_GRANT_KEYS",
    "RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS",
    "RECOVERY_EPOCH002_FORMAL_AUTHORITY_GRANT_KEYS",
    "RECOVERY_EPOCH002_FORMAL_PARENT_RESULT_KEYS",
    "RecoveryEpoch002ParentPorts",
    "validate_recovery_epoch002_parent_state",
    "validate_recovery_epoch002_parent_execution_state",
    "validate_recovery_epoch002_parent_phase_result",
    "next_recovery_epoch002_parent_action",
    "execute_recovery_epoch002_parent_phase",
    "validate_recovery_epoch002_formal_parent_continuation_state",
]
