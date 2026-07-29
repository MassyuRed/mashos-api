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
import json
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
from typing import Any, Mapping, Protocol

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
    load_canonical_json_bytes,
)
from emlis_ai_recovery_epoch002_canonical_current_closure_v3 import (
    RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS,
    RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA,
    RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS,
    RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA,
    build_recovery_epoch003_source_bootstrap_closure,
    validate_recovery_epoch003_source_bootstrap_contract_state,
)
from emlis_ai_recovery_epoch002_sequence_ledger_v3 import (
    RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS,
    RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA,
    validate_recovery_epoch002_event1_artifact,
    validate_recovery_epoch002_reservation_artifact,
    validate_recovery_epoch003_sequence_event1_contract_state,
)
from emlis_nls_v3_recovery_epoch002_closure_receipt_verify import (
    verify_recovery_epoch002_success_contract_state,
    verify_recovery_epoch002_artifact_identity,
    verify_recovery_epoch002_published_artifact,
    verify_recovery_epoch003_operational_admission_contract,
)
from emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3 import (
    RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS,
    validate_recovery_epoch002_success_publication_state,
    validate_recovery_epoch003_publication_contract_state,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight import (
    RECOVERY_EPOCH003_FAILURE_CLASSES,
    RECOVERY_EPOCH003_FAILURE_SCHEMA,
    RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA,
    RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE,
    RECOVERY_EPOCH003_READINESS_SCHEMA,
    RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA,
    execute_recovery_epoch003_current_strict_preflight_v1,
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
RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_REQUIRED_KEYS = (
    RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS
    - frozenset(
        {
            "expected_old_sha1",
            "observed_old_sha1",
            "parent_commit_sha1s",
            "automatic_progression",
            "body_free",
        }
    )
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
    state_keys = set(state) if type(state) is dict else frozenset()
    if (
        type(state) is not dict
        or not RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_REQUIRED_KEYS
        <= state_keys
        or not state_keys <= RECOVERY_EPOCH002_FRESH_PUBLICATION_STATE_KEYS
        or state.get("reflection_contract_version")
        != "COCOLON_GITHUB_REFLECTION_CONTRACT_V1"
        or state.get("artifact_role") != artifact_role
        or state.get("artifact") != artifact
        or (
            "automatic_progression" in state
            and state.get("automatic_progression") is not False
        )
        or ("body_free" in state and state.get("body_free") is not True)
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


RECOVERY_EPOCH003_PARENT_PHASE_ORDER = (
    "REFERENCE_RUNTIME_OBSERVATION_PUBLISHED_AND_POSTVERIFIED",
    (
        "SOURCE_BOOTSTRAP_CLOSURE_AND_OPERATIONAL_ADMISSION_"
        "PUBLISHED_AND_POSTVERIFIED"
    ),
    "CANDIDATE_ALLOCATED",
    "EVENT1_PUBLISHED_AND_POSTVERIFIED",
    "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT",
    "READINESS_OR_FAILURE_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
)


def validate_recovery_epoch003_parent_phase_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the additive Epoch003 phase cursor without advancing it."""

    try:
        if (
            type(state) is dict
            and state.get("automatic_progression") is True
        ):
            return (
                "RECOVERY_EPOCH003_AUTOMATIC_PROGRESSION_FORBIDDEN",
            )
        if type(state) is not dict:
            return ("RECOVERY_EPOCH003_PARENT_PHASE_STATE_INVALID",)
        phase_order = state.get("phase_order")
        completed = state.get("completed_phases")
        if (
            phase_order != list(RECOVERY_EPOCH003_PARENT_PHASE_ORDER)
            or type(completed) is not list
            or len(completed) > len(RECOVERY_EPOCH003_PARENT_PHASE_ORDER)
            or completed
            != list(RECOVERY_EPOCH003_PARENT_PHASE_ORDER[: len(completed)])
            or state.get("next_phase")
            != (
                RECOVERY_EPOCH003_PARENT_PHASE_ORDER[len(completed)]
                if len(completed)
                < len(RECOVERY_EPOCH003_PARENT_PHASE_ORDER)
                else None
            )
            or state.get("reservation_count_delta") != 0
            or state.get("formal_exact134_invocation_count") != 0
            or state.get("automatic_progression") is not False
        ):
            return ("RECOVERY_EPOCH003_PARENT_PHASE_STATE_INVALID",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_EPOCH003_PARENT_PHASE_STATE_INVALID",)


_RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER = (
    "REFERENCE_RUNTIME_OBSERVATION_PUBLISHED_AND_POSTVERIFIED",
    (
        "SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_CARRIER_"
        "PUBLISHED_AND_POSTVERIFIED"
    ),
    (
        "CANDIDATE_ALLOCATED_WITH_EVENT1_"
        "PUBLISHED_AND_POSTVERIFIED"
    ),
    "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT",
    "READINESS_OR_FAILURE_PUBLISHED_AND_POSTVERIFIED",
    "FORMAL_RESERVATION_PUBLISHED_AND_POSTVERIFIED",
)
_RECOVERY_EPOCH003_EVIDENCE_STATE_KEYS = frozenset(
    {
        "artifact_repository_root",
        "source_repository_root",
        "phase_order",
        "completed_phases",
        "phase_evidence",
        "next_phase",
        "reservation_count_delta",
        "formal_exact134_invocation_count",
        "automatic_progression",
    }
)
_RECOVERY_EPOCH003_PHASE_EVIDENCE_KEYS = frozenset(
    {
        "phase",
        "artifact_records",
        "runtime_records",
        "owner_validation_state",
        "independent_verification_state",
        "phase_evidence_sha256",
    }
)
_RECOVERY_EPOCH003_ARTIFACT_RECORD_KEYS = frozenset(
    {
        "external_identity",
        "published_body",
        "postfetch_body",
        "publication_base_commit_sha1",
        "changed_paths",
    }
)
_RECOVERY_EPOCH003_RUNTIME_RECORD_KEYS = frozenset(
    {
        "evidence_role",
        "evidence_body",
        "logical_sha256",
        "body_free",
    }
)
_RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS = frozenset(
    {
        "artifact_role",
        "body_free",
        "git_blob_sha1",
        "identity_sha256",
        "logical_artifact_sha256",
        "path",
        "publication_commit_sha1",
        "raw_sha256",
        "repository_full_name",
        "schema_version",
    }
)
_RECOVERY_EPOCH003_PHASE_ARTIFACT_ROLES = (
    frozenset({"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}),
    frozenset({"RECOVERY_EPOCH003_OPERATIONAL_ADMISSION"}),
    frozenset({"RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT"}),
    frozenset(),
    frozenset(
        {
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
            "RECOVERY_EPOCH003_BOOTSTRAP_READINESS",
            "RECOVERY_EPOCH003_FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE",
        }
    ),
    frozenset(
        {"RECOVERY_EPOCH003_FORMAL_ATTEMPT_ONE_SHOT_RESERVATION"}
    ),
)
_RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_ROLE = (
    "OPERATIONAL_RUNTIME_OBSERVATION_CANDIDATE"
)
_RECOVERY_EPOCH003_READINESS_RUNTIME_ROLES = frozenset(
    {
        "BOOTSTRAP_READINESS_CANDIDATE",
        "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE_CANDIDATE",
    }
)


def _recovery_epoch003_evidence_external_identity_valid(
    value: Any,
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        and value.get("repository_full_name") == "MassyuRed/Cocolon"
        and value.get("body_free") is True
        and isinstance(value.get("artifact_role"), str)
        and bool(value.get("artifact_role"))
        and isinstance(value.get("schema_version"), str)
        and bool(value.get("schema_version"))
        and isinstance(value.get("path"), str)
        and bool(value.get("path"))
        and not PurePosixPath(value["path"]).is_absolute()
        and ".." not in PurePosixPath(value["path"]).parts
        and _CONTINUATION_SHA1_RE.fullmatch(
            str(value.get("git_blob_sha1", ""))
        )
        is not None
        and _CONTINUATION_SHA1_RE.fullmatch(
            str(value.get("publication_commit_sha1", ""))
        )
        is not None
        and _CONTINUATION_SHA256_RE.fullmatch(
            str(value.get("raw_sha256", ""))
        )
        is not None
        and _CONTINUATION_SHA256_RE.fullmatch(
            str(value.get("logical_artifact_sha256", ""))
        )
        is not None
        and value.get("identity_sha256")
        == _hash_without(value, "identity_sha256")
    )


def _recovery_epoch003_artifact_record_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_ARTIFACT_RECORD_KEYS
        or not _recovery_epoch003_evidence_external_identity_valid(
            value.get("external_identity")
        )
        or type(value.get("published_body")) is not dict
        or value.get("published_body") != value.get("postfetch_body")
        or _CONTINUATION_SHA1_RE.fullmatch(
            str(value.get("publication_base_commit_sha1", ""))
        )
        is None
    ):
        return False
    identity = value["external_identity"]
    body = value["published_body"]
    logical_fields = (
        "operational_admission_sha256",
        "reference_runtime_observation_sha256",
        "event_sha256",
        "operational_runtime_observation_sha256",
        "bootstrap_readiness_receipt_sha256",
        "receipt_sha256",
        "formal_test_run_reservation_sha256",
    )
    logical_values = [
        body[key]
        for key in logical_fields
        if key in body and isinstance(body[key], str)
    ]
    return bool(
        value.get("changed_paths") == [identity["path"]]
        and len(logical_values) == 1
        and logical_values[0] == identity["logical_artifact_sha256"]
    )


def _recovery_epoch003_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _recovery_epoch003_artifact_record_repository_valid(
    value: Mapping[str, Any],
    *,
    root: Path,
) -> bool:
    identity = value["external_identity"]
    commit = identity["publication_commit_sha1"]
    path = identity["path"]
    try:
        parents = _recovery_epoch003_git(
            root,
            "show",
            "-s",
            "--format=%P",
            commit,
        ).split()
        changed = _recovery_epoch003_git(
            root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
        ).splitlines()
        blob = _recovery_epoch003_git(
            root,
            "rev-parse",
            f"{commit}:{path}",
        )
        raw = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=root,
            check=True,
            capture_output=True,
            timeout=20,
        ).stdout
        body = load_canonical_json_bytes(raw)
        reachable = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    return bool(
        len(parents) == 1
        and parents[0] == value.get("publication_base_commit_sha1")
        and changed == value.get("changed_paths")
        and reachable
        and blob == identity.get("git_blob_sha1")
        and hashlib.sha256(raw).hexdigest()
        == identity.get("raw_sha256")
        and body == value.get("published_body")
        == value.get("postfetch_body")
    )


def _recovery_epoch003_runtime_record_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_RUNTIME_RECORD_KEYS
        and isinstance(value.get("evidence_role"), str)
        and bool(value.get("evidence_role"))
        and type(value.get("evidence_body")) is dict
        and value.get("logical_sha256")
        == artifact_sha256(value["evidence_body"])
        and value.get("body_free") is True
    )


def _recovery_epoch003_phase_membership_valid(
    phase_index: int,
    artifact_records: list[dict[str, Any]],
    runtime_records: list[dict[str, Any]],
) -> bool:
    artifact_roles = [
        row["external_identity"]["artifact_role"]
        for row in artifact_records
    ]
    runtime_roles = [row["evidence_role"] for row in runtime_records]
    if phase_index in {0, 1, 2, 5}:
        return bool(
            len(artifact_roles) == 1
            and set(artifact_roles)
            == _RECOVERY_EPOCH003_PHASE_ARTIFACT_ROLES[phase_index]
            and runtime_roles == []
        )
    if phase_index == 3:
        return bool(
            artifact_roles == []
            and len(runtime_roles) == 2
            and _RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_ROLE
            in runtime_roles
            and len(
                set(runtime_roles)
                & _RECOVERY_EPOCH003_READINESS_RUNTIME_ROLES
            )
            == 1
        )
    return bool(
        runtime_roles == []
        and len(artifact_roles) == 2
        and "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
        in artifact_roles
        and len(
            set(artifact_roles)
            & {
                "RECOVERY_EPOCH003_BOOTSTRAP_READINESS",
                (
                    "RECOVERY_EPOCH003_FORMAL_WORKER_"
                    "BOOTSTRAP_PREFLIGHT_FAILURE"
                ),
            }
        )
        == 1
    )


def _validate_recovery_epoch003_parent_phase_evidence_state_legacy_internal(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Retain the pre-Addendum validator for internal history only."""

    failure = ("RECOVERY_EPOCH003_PARENT_PHASE_EVIDENCE_INVALID",)
    try:
        if (
            type(state) is not dict
            or set(state) != _RECOVERY_EPOCH003_EVIDENCE_STATE_KEYS
            or not isinstance(state.get("artifact_repository_root"), str)
            or not state["artifact_repository_root"]
            or not isinstance(state.get("source_repository_root"), str)
            or not state["source_repository_root"]
            or state.get("phase_order")
            != list(_RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER)
            or type(state.get("completed_phases")) is not list
            or state["completed_phases"]
            != list(
                _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[
                    : len(state["completed_phases"])
                ]
            )
            or len(state["completed_phases"])
            > len(_RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER)
            or state.get("next_phase")
            != (
                _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[
                    len(state["completed_phases"])
                ]
                if len(state["completed_phases"])
                < len(_RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER)
                else None
            )
            or state.get("reservation_count_delta") != 0
            or state.get("formal_exact134_invocation_count") != 0
            or state.get("automatic_progression") is not False
            or type(state.get("phase_evidence")) is not list
            or len(state["phase_evidence"])
            != len(state["completed_phases"])
        ):
            return failure
        artifact_root = Path(state["artifact_repository_root"]).resolve()
        source_root = Path(state["source_repository_root"]).resolve()
        if (
            artifact_root.is_symlink()
            or not artifact_root.is_dir()
            or source_root.is_symlink()
            or not source_root.is_dir()
        ):
            return failure
        try:
            _recovery_epoch003_git(artifact_root, "rev-parse", "HEAD")
            _recovery_epoch003_git(source_root, "rev-parse", "HEAD")
        except (OSError, subprocess.SubprocessError):
            return failure
        for index, row in enumerate(state["phase_evidence"]):
            if (
                type(row) is not dict
                or set(row) != _RECOVERY_EPOCH003_PHASE_EVIDENCE_KEYS
                or row.get("phase")
                != _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[index]
                or row.get("owner_validation_state") != "PROVED"
                or row.get("independent_verification_state") != "PROVED"
                or row.get("phase_evidence_sha256")
                != _hash_without(row, "phase_evidence_sha256")
                or type(row.get("artifact_records")) is not list
                or type(row.get("runtime_records")) is not list
                or any(
                    not _recovery_epoch003_artifact_record_valid(record)
                    for record in row["artifact_records"]
                )
                or any(
                    not _recovery_epoch003_artifact_record_repository_valid(
                        record,
                        root=artifact_root,
                    )
                    for record in row["artifact_records"]
                )
                or any(
                    not _recovery_epoch003_runtime_record_valid(record)
                    for record in row["runtime_records"]
                )
            ):
                return failure
            artifact_records = row["artifact_records"]
            runtime_records = row["runtime_records"]
            if artifact_records != sorted(
                artifact_records,
                key=lambda record: (
                    record["external_identity"]["artifact_role"],
                    record["external_identity"]["path"],
                    record["external_identity"]["identity_sha256"],
                ),
            ) or runtime_records != sorted(
                runtime_records,
                key=lambda record: (
                    record["evidence_role"],
                    record["logical_sha256"],
                ),
            ):
                return failure
            if not _recovery_epoch003_phase_membership_valid(
                index,
                artifact_records,
                runtime_records,
            ):
                return failure
            if index == 4:
                candidates = {
                    record["evidence_role"]: record
                    for record in state["phase_evidence"][3][
                        "runtime_records"
                    ]
                }
                candidate_role_by_artifact_role = {
                    (
                        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
                    ): "OPERATIONAL_RUNTIME_OBSERVATION_CANDIDATE",
                    "RECOVERY_EPOCH003_BOOTSTRAP_READINESS": (
                        "BOOTSTRAP_READINESS_CANDIDATE"
                    ),
                    (
                        "RECOVERY_EPOCH003_FORMAL_WORKER_"
                        "BOOTSTRAP_PREFLIGHT_FAILURE"
                    ): (
                        "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_"
                        "FAILURE_CANDIDATE"
                    ),
                }
                for record in artifact_records:
                    artifact_role = record["external_identity"][
                        "artifact_role"
                    ]
                    candidate = candidates.get(
                        candidate_role_by_artifact_role.get(
                            artifact_role,
                            "",
                        )
                    )
                    if (
                        candidate is None
                        or candidate["evidence_body"]
                        != record["published_body"]
                        or candidate["logical_sha256"]
                        != record["external_identity"][
                            "logical_artifact_sha256"
                        ]
                    ):
                        return failure
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


# The evidence validator above is retained as the historical D1
# implementation.  The additive D2 implementation below deliberately
# redefines only the current public validator: legacy parent APIs and their
# frozen behavior remain untouched.


def _e3_keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


_E3_REFERENCE_KEYS = _e3_keys(
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
_E3_ADMISSION_KEYS = _e3_keys(
    """
    schema_version logical_cycle_id recovery_epoch_id predecessor_bindings
    source_closure bootstrap_closure authority scope freshness
    effect_boundary owner_validation_state independent_verification_state
    state automatic_progression body_free operational_admission_sha256
    """
)
_E3_PREDECESSOR_KEYS = _e3_keys(
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
_E3_OPERATIONAL_KEYS = _e3_keys(
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
_E3_READINESS_KEYS = _e3_keys(
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
_E3_FAILURE_KEYS = _e3_keys(
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
_E3_MATERIALIZATION_KEYS = _e3_keys(
    """
    schema_version runtime_root_identity_sha256
    python_executable_relative_path installed_directory_relative_path
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    distribution_count runtime_materialization_state body_free
    runtime_materialization_sha256
    """
)
_E3_RUNTIME_IDENTITY_KEYS = _e3_keys(
    "executable_sha256 implementation version build_sha256"
)
_E3_DISTRIBUTION_KEYS = _e3_keys(
    """
    normalized_distribution_name distribution_version wheel_sha256
    installed_record_closure_sha256
    """
)
_E3_ENVIRONMENT_KEYS = _e3_keys(
    "fixed removed inherited_path_sha256 lang lc_all"
)
_E3_ENVIRONMENT_FIXED_KEYS = _e3_keys(
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD PYTHONDONTWRITEBYTECODE"
)
_E3_PROJECTION_KEYS = _e3_keys(
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
_E3_ADMISSION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
)
_E3_MATERIALIZATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.runtime_materialization.v1"
)
_E3_FINAL_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_FINAL_PRE_EVENT1_REFERENCE_"
    "RUNTIME_OBSERVATION_AND_SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_"
    "CARRIER_ISSUANCE_INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_E3_PREFLIGHT_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_POST_EVENT1_LOCKED_RUNTIME_"
    "MATERIALIZATION_OPERATIONAL_RUNTIME_OBSERVATION_READINESS_OR_FAILURE_"
    "CANDIDATE_AND_INDEPENDENT_PREFLIGHT_VERIFICATION_ONLY"
)
_E3_LOCK_PATH = (
    "ai/configs/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
)
_E3_LOCK_RAW = (
    "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
)
_E3_WHEEL_BUNDLE = (
    "63f3915ccf57845dc0c4b5d14762207d23d1cb7a435a9de8411add8491ba6fc8"
)
_E3_INSTALLED = (
    "0e2e4b5ec3f3b1aef7fad4474af28d8eeea8fa7bec1a57a9cb7180fc81b80e42"
)
_E3_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
_E3_ROLE_SCHEMA_HASH = {
    "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION": (
        RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA,
        "reference_runtime_observation_sha256",
    ),
    "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION": (
        _E3_ADMISSION_SCHEMA,
        "operational_admission_sha256",
    ),
    "RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT": (
        RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA,
        "event_sha256",
    ),
    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION": (
        RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA,
        "operational_runtime_observation_sha256",
    ),
    (
        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
        "OBSERVATION_FAILURE_EVIDENCE"
    ): (
        RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA,
        "operational_runtime_observation_sha256",
    ),
    "RECOVERY_EPOCH003_BOOTSTRAP_READINESS": (
        RECOVERY_EPOCH003_READINESS_SCHEMA,
        "bootstrap_readiness_receipt_sha256",
    ),
    "RECOVERY_EPOCH003_FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE": (
        RECOVERY_EPOCH003_FAILURE_SCHEMA,
        "receipt_sha256",
    ),
}


def _e3_sha1(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and _CONTINUATION_SHA1_RE.fullmatch(value) is not None
    )


def _e3_sha256(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and _CONTINUATION_SHA256_RE.fullmatch(value) is not None
    )


def _e3_environment_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _E3_ENVIRONMENT_KEYS
        and type(value.get("fixed")) is dict
        and set(value["fixed"]) == _E3_ENVIRONMENT_FIXED_KEYS
        and value["fixed"].get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
        and value["fixed"].get("PYTHONDONTWRITEBYTECODE") == "1"
        and value.get("removed")
        == ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"]
        and _e3_sha256(value.get("inherited_path_sha256"))
        and value.get("inherited_path_sha256") != "0" * 64
        and isinstance(value.get("lang"), str)
        and bool(value.get("lang"))
        and isinstance(value.get("lc_all"), str)
        and bool(value.get("lc_all"))
    )


def _e3_environment_shape_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _E3_ENVIRONMENT_KEYS
        and type(value.get("fixed")) is dict
        and set(value["fixed"]) == _E3_ENVIRONMENT_FIXED_KEYS
        and all(
            isinstance(item, str)
            for item in value["fixed"].values()
        )
        and type(value.get("removed")) is list
        and all(
            isinstance(item, str) and item
            for item in value["removed"]
        )
        and len(value["removed"]) == len(set(value["removed"]))
        and _e3_sha256(value.get("inherited_path_sha256"))
        and isinstance(value.get("lang"), str)
        and bool(value.get("lang"))
        and isinstance(value.get("lc_all"), str)
        and bool(value.get("lc_all"))
    )


def _e3_distribution_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _E3_DISTRIBUTION_KEYS
        and isinstance(value.get("normalized_distribution_name"), str)
        and bool(value.get("normalized_distribution_name"))
        and isinstance(value.get("distribution_version"), str)
        and bool(value.get("distribution_version"))
        and _e3_sha256(value.get("wheel_sha256"))
        and _e3_sha256(value.get("installed_record_closure_sha256"))
    )


def _e3_runtime_identity_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _E3_RUNTIME_IDENTITY_KEYS
        and value.get("implementation") == "CPYTHON"
        and value.get("version") == "3.12.13"
        and _e3_sha256(value.get("executable_sha256"))
        and _e3_sha256(value.get("build_sha256"))
    )


def _e3_runtime_identity_shape_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _E3_RUNTIME_IDENTITY_KEYS
        and isinstance(value.get("implementation"), str)
        and bool(value.get("implementation"))
        and isinstance(value.get("version"), str)
        and bool(value.get("version"))
        and _e3_sha256(value.get("executable_sha256"))
        and _e3_sha256(value.get("build_sha256"))
    )


def _e3_materialization_shape_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _E3_MATERIALIZATION_KEYS
        or value.get("schema_version") != _E3_MATERIALIZATION_SCHEMA
        or not _e3_sha256(value.get("runtime_root_identity_sha256"))
        or not _e3_sha256(value.get("dependency_lock_raw_sha256"))
        or not _e3_sha256(value.get("wheel_bundle_manifest_sha256"))
        or not isinstance(value.get("distribution_count"), int)
        or isinstance(value.get("distribution_count"), bool)
        or value["distribution_count"] <= 0
        or not isinstance(value.get("runtime_materialization_state"), str)
        or not value["runtime_materialization_state"]
        or value.get("body_free") is not True
        or value.get("runtime_materialization_sha256")
        != _hash_without(value, "runtime_materialization_sha256")
    ):
        return False
    return all(
        isinstance(value.get(key), str)
        and bool(value[key])
        and not PurePosixPath(value[key]).is_absolute()
        and ".." not in PurePosixPath(value[key]).parts
        for key in (
            "python_executable_relative_path",
            "installed_directory_relative_path",
        )
    )


def _e3_materialization_valid(value: Any, state: str) -> bool:
    if (
        not _e3_materialization_shape_valid(value)
        or value.get("dependency_lock_raw_sha256") != _E3_LOCK_RAW
        or value.get("wheel_bundle_manifest_sha256") != _E3_WHEEL_BUNDLE
        or value.get("distribution_count") != 46
        or value.get("runtime_materialization_state") != state
    ):
        return False
    return True


def _e3_reference_body_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _E3_REFERENCE_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or value.get("authority_token") != _E3_FINAL_AUTHORITY
        or not _e3_sha1(value.get("source_commit_sha1"))
        or not _e3_sha1(value.get("source_tree_sha1"))
        or value.get("reservation_count_delta") != 0
        or value.get("formal_exact134_invocation_count") != 0
        or value.get("collection_state") != "NOT_STARTED"
        or value.get("test_execution_state") != "NOT_STARTED"
        or value.get("body_free") is not True
        or value.get("reference_runtime_observation_sha256")
        != _hash_without(
            value,
            "reference_runtime_observation_sha256",
        )
    ):
        return False
    installed = value.get("installed_distributions")
    pytest_identity = value.get("pytest_distribution_identity")
    environment = value.get("environment_policy")
    return bool(
        value.get("dependency_lock_identity")
        == {
            "identity_class": "EXACT_HASH_LOCK",
            "path": _E3_LOCK_PATH,
            "raw_sha256": _E3_LOCK_RAW,
        }
        and value.get("wheel_bundle_manifest_sha256")
        == _E3_WHEEL_BUNDLE
        and type(installed) is list
        and len(installed) == 46
        and all(_e3_distribution_valid(row) for row in installed)
        and [
            row["normalized_distribution_name"] for row in installed
        ]
        == sorted(
            {
                row["normalized_distribution_name"]
                for row in installed
            }
        )
        and value.get("installed_distributions_sha256")
        == _E3_INSTALLED
        == artifact_sha256(installed)
        and _e3_runtime_identity_valid(
            value.get("python_runtime_identity")
        )
        and _e3_distribution_valid(pytest_identity)
        and pytest_identity in installed
        and pytest_identity.get("normalized_distribution_name")
        == "pytest"
        and _e3_environment_valid(environment)
        and value.get("environment_policy_sha256")
        == artifact_sha256(environment)
        and _e3_materialization_valid(
            value.get("runtime_materialization"),
            "VERIFIED_LOCKED_REFERENCE_RUNTIME",
        )
    )


def _e3_admission_body_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _E3_ADMISSION_KEYS
        and value.get("schema_version") == _E3_ADMISSION_SCHEMA
        and value.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and value.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        and type(value.get("predecessor_bindings")) is dict
        and set(value["predecessor_bindings"])
        == _E3_PREDECESSOR_KEYS
        and value["predecessor_bindings"].get(
            "predecessor_bindings_sha256"
        )
        == _hash_without(
            value["predecessor_bindings"],
            "predecessor_bindings_sha256",
        )
        and type(value.get("source_closure")) is dict
        and set(value["source_closure"])
        == RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS
        and value["source_closure"].get("schema_version")
        == RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA
        and type(value.get("bootstrap_closure")) is dict
        and set(value["bootstrap_closure"])
        == RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS
        and value["bootstrap_closure"].get("schema_version")
        == RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA
        and validate_recovery_epoch003_source_bootstrap_contract_state(
            {
                "source_closure": value["source_closure"],
                "bootstrap_closure": value["bootstrap_closure"],
            }
        )
        == ()
        and all(
            type(value.get(key)) is dict
            for key in (
                "authority",
                "scope",
                "freshness",
                "effect_boundary",
            )
        )
        and value.get("owner_validation_state") == "PROVED"
        and value.get("independent_verification_state") == "PROVED"
        and value.get("state")
        == (
            "SOURCE_BOOTSTRAP_REFERENCE_RUNTIME_CLOSED_AWAITING_"
            "SEPARATE_CANDIDATE_EVENT1_AUTHORITY"
        )
        and value.get("automatic_progression") is False
        and value.get("body_free") is True
        and value.get("operational_admission_sha256")
        == _hash_without(value, "operational_admission_sha256")
    )


def _e3_operational_body_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _E3_OPERATIONAL_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or not isinstance(value.get("candidate_version_id"), str)
        or not value.get("candidate_version_id")
        or not isinstance(value.get("authority_token"), str)
        or not value.get("authority_token")
        or not _e3_sha256(value.get("preflight_challenge_id"))
        or not _e3_sha256(value.get("preflight_id"))
        or not _e3_sha1(value.get("source_commit_sha1"))
        or not _e3_sha1(value.get("source_tree_sha1"))
        or type(value.get("worktree_clean")) is not bool
        or not _e3_sha256(value.get("dependency_lock_raw_sha256"))
        or not _e3_sha256(value.get("wheel_bundle_manifest_sha256"))
        or not _e3_sha256(value.get("installed_distributions_sha256"))
        or not _e3_distribution_valid(
            value.get("pytest_distribution_identity")
        )
        or not _e3_runtime_identity_shape_valid(
            value.get("python_runtime_identity")
        )
        or not _e3_environment_shape_valid(
            value.get("environment_policy")
        )
        or value.get("environment_policy_sha256")
        != artifact_sha256(value["environment_policy"])
        or not _e3_materialization_shape_valid(
            value.get("runtime_materialization")
        )
        or value.get("owner_validation_state") != "VALID"
        or value.get("independent_verification_state") != "VALID"
        or value.get("reservation_count_delta") != 0
        or value.get("formal_exact134_invocation_count") != 0
        or value.get("collection_state") != "NOT_STARTED"
        or value.get("test_execution_state") != "NOT_STARTED"
        or value.get("pytest_main_called") is not False
        or value.get("body_free") is not True
        or value.get("operational_runtime_observation_sha256")
        != _hash_without(
            value,
            "operational_runtime_observation_sha256",
        )
    ):
        return False
    roots = (
        value.get("runtime_root_identity_sha256"),
        value.get("reference_runtime_root_identity_sha256"),
        value.get("attempt_registry_root_identity_sha256"),
    )
    return bool(
        all(_e3_sha256(root) for root in roots)
        and _e3_sha256(
            value.get("owner_operational_projection_sha256")
        )
        and _e3_sha256(
            value.get("independent_operational_projection_sha256")
        )
    )


def _e3_identity_valid(
    value: Any,
    *,
    role: str | None = None,
    logical_hash: str | None = None,
) -> bool:
    valid = bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        and value.get("repository_full_name") == "MassyuRed/Cocolon"
        and value.get("body_free") is True
        and isinstance(value.get("artifact_role"), str)
        and bool(value.get("artifact_role"))
        and isinstance(value.get("schema_version"), str)
        and bool(value.get("schema_version"))
        and isinstance(value.get("path"), str)
        and bool(value.get("path"))
        and not PurePosixPath(value["path"]).is_absolute()
        and ".." not in PurePosixPath(value["path"]).parts
        and _e3_sha1(value.get("git_blob_sha1"))
        and _e3_sha1(value.get("publication_commit_sha1"))
        and _e3_sha256(value.get("raw_sha256"))
        and _e3_sha256(value.get("logical_artifact_sha256"))
        and value.get("identity_sha256")
        == _hash_without(value, "identity_sha256")
    )
    if not valid or role is None:
        return valid
    contract = _E3_ROLE_SCHEMA_HASH.get(role)
    return bool(
        contract is not None
        and value.get("artifact_role") == role
        and value.get("schema_version") == contract[0]
        and value.get("path")
        == RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS.get(role)
        and (
            logical_hash is None
            or value.get("logical_artifact_sha256") == logical_hash
        )
    )


def _e3_readiness_body_valid(value: Any) -> bool:
    identity = (
        value.get("operational_runtime_observation_external_identity")
        if type(value) is dict
        else None
    )
    return bool(
        type(value) is dict
        and set(value) == _E3_READINESS_KEYS
        and value.get("schema_version") == RECOVERY_EPOCH003_READINESS_SCHEMA
        and value.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and value.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        and isinstance(value.get("candidate_version_id"), str)
        and bool(value.get("candidate_version_id"))
        and isinstance(value.get("authority_token"), str)
        and bool(value.get("authority_token"))
        and _e3_sha256(value.get("event1_external_identity_sha256"))
        and type(value.get("event1_bootstrap_closure")) is dict
        and set(value["event1_bootstrap_closure"])
        == RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS
        and value.get("event1_bootstrap_closure_sha256")
        == value["event1_bootstrap_closure"].get(
            "bootstrap_closure_sha256"
        )
        and _e3_identity_valid(
            identity,
            role="RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
            logical_hash=value.get(
                "operational_runtime_observation_sha256"
            ),
        )
        and _e3_sha256(
            value.get("expected_observed_projection_sha256")
        )
        and value.get("readiness_receipt_path")
        == RECOVERY_EPOCH003_PUBLICATION_ROLE_PATHS[
            "RECOVERY_EPOCH003_BOOTSTRAP_READINESS"
        ]
        and _E3_UTC_RE.fullmatch(
            str(value.get("preflight_started_at_utc", ""))
        )
        is not None
        and _E3_UTC_RE.fullmatch(
            str(value.get("preflight_finished_at_utc", ""))
        )
        is not None
        and value["preflight_started_at_utc"]
        <= value["preflight_finished_at_utc"]
        and value.get("owner_validation_state") == "VALID"
        and value.get("independent_verification_state") == "VALID"
        and value.get("reservation_count_delta") == 0
        and value.get("formal_exact134_invocation_count") == 0
        and value.get("collection_state") == "NOT_STARTED"
        and value.get("test_execution_state") == "NOT_STARTED"
        and value.get("pytest_main_called") is False
        and value.get("automatic_progression") is False
        and value.get("body_free") is True
        and value.get("bootstrap_readiness_receipt_sha256")
        == _hash_without(
            value,
            "bootstrap_readiness_receipt_sha256",
        )
    )


def _e3_failure_body_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _E3_FAILURE_KEYS
        or value.get("schema_version") != RECOVERY_EPOCH003_FAILURE_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or not isinstance(value.get("candidate_version_id"), str)
        or not value.get("candidate_version_id")
        or not isinstance(value.get("authority_token"), str)
        or not value.get("authority_token")
        or not _e3_sha256(value.get("preflight_challenge_id"))
        or not _e3_sha256(value.get("preflight_id"))
        or not _e3_sha256(value.get("event1_external_identity_sha256"))
        or not _e3_sha256(value.get("source_closure_sha256"))
        or not _e3_sha256(value.get("bootstrap_closure_sha256"))
        or value.get("failure_class") not in RECOVERY_EPOCH003_FAILURE_CLASSES
        or value.get("failure_issue_codes")
        != [value.get("failure_class")]
        or value.get("stop_code") != RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE
        or value.get("reservation_count_delta") != 0
        or value.get("attempt_id") is not None
        or value.get("formal_exact134_invocation_count") != 0
        or value.get("automatic_retry") is not False
        or value.get("automatic_progression") is not False
        or value.get("body_free") is not True
        or value.get("receipt_sha256")
        != _hash_without(value, "receipt_sha256")
    ):
        return False
    fields = (
        "operational_runtime_observation_sha256",
        "owner_operational_projection_sha256",
        "independent_operational_projection_sha256",
        "expected_observed_projection_sha256",
    )
    identity = value.get(
        "operational_runtime_observation_external_identity"
    )
    failure_class = value["failure_class"]
    early_stage = {
        "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED": "BEFORE_MATERIALIZATION",
        "SOURCE_BOOTSTRAP_BASELINE_MISMATCH": "BEFORE_MATERIALIZATION",
        (
            "OPERATIONAL_MATERIALIZATION_BINDING_MISSING"
        ): "MATERIALIZATION_BINDING",
    }
    if failure_class in early_stage:
        return bool(
            value.get("authority_token")
            == "UNISSUED_RECOVERY_EPOCH003_PREFLIGHT_AUTHORITY"
            and value.get("failure_stage") == early_stage[failure_class]
            and value.get("operational_runtime_observation_state")
            == "NOT_AVAILABLE"
            and identity is None
            and value.get("owner_validation_state") == "NOT_STARTED"
            and value.get("independent_verification_state")
            == "NOT_STARTED"
            and all(value.get(key) is None for key in fields)
        )
    if (
        failure_class
        not in {
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
            "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
        }
        or value.get("operational_runtime_observation_state")
        != "OBSERVED"
        or not _e3_identity_valid(
            identity,
            role=(
                "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                "OBSERVATION_FAILURE_EVIDENCE"
            ),
            logical_hash=value.get(
                "operational_runtime_observation_sha256"
            ),
        )
        or not all(_e3_sha256(value.get(key)) for key in fields)
    ):
        return False
    owner_hash = value["owner_operational_projection_sha256"]
    independent_hash = value[
        "independent_operational_projection_sha256"
    ]
    if failure_class == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH":
        return bool(
            value.get("failure_stage")
            == "EXPECTED_OBSERVED_COMPARISON"
            and value.get("owner_validation_state") == "INVALID"
            and value.get("independent_verification_state") == "VALID"
            and independent_hash == owner_hash
        )
    return bool(
        value.get("failure_stage") == "INDEPENDENT_PROJECTION"
        and value.get("owner_validation_state") == "VALID"
        and value.get("independent_verification_state") == "INVALID"
        and owner_hash != independent_hash
        and value.get("expected_observed_projection_sha256")
        == artifact_sha256(
            {
                "owner": owner_hash,
                "independent": independent_hash,
            }
        )
    )


def _e3_body_valid(role: str, value: Any) -> bool:
    if role == "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION":
        return _e3_reference_body_valid(value)
    if role == "RECOVERY_EPOCH003_OPERATIONAL_ADMISSION":
        return _e3_admission_body_valid(value)
    if role == "RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT":
        return bool(
            type(value) is dict
            and set(value) == RECOVERY_EPOCH003_SEQUENCE_EVENT_KEYS
            and validate_recovery_epoch003_sequence_event1_contract_state(
                value
            )
            == ()
        )
    if role in {
        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
        (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
            "OBSERVATION_FAILURE_EVIDENCE"
        ),
    }:
        return _e3_operational_body_valid(value)
    if role == "RECOVERY_EPOCH003_BOOTSTRAP_READINESS":
        return _e3_readiness_body_valid(value)
    if (
        role
        == "RECOVERY_EPOCH003_FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE"
    ):
        return _e3_failure_body_valid(value)
    return False


def _e3_artifact_record_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_ARTIFACT_RECORD_KEYS
        or type(value.get("external_identity")) is not dict
        or type(value.get("published_body")) is not dict
        or value.get("published_body") != value.get("postfetch_body")
        or not _e3_sha1(value.get("publication_base_commit_sha1"))
    ):
        return False
    identity = value["external_identity"]
    body = value["published_body"]
    role = identity.get("artifact_role")
    contract = _E3_ROLE_SCHEMA_HASH.get(role)
    if contract is None:
        return False
    logical_hash = body.get(contract[1])
    return bool(
        _e3_sha256(logical_hash)
        and _e3_identity_valid(
            identity,
            role=role,
            logical_hash=logical_hash,
        )
        and _e3_body_valid(role, body)
        and value.get("changed_paths") == [identity["path"]]
        and validate_recovery_epoch003_publication_contract_state(
            {
                "artifact_role": role,
                "path": identity["path"],
                "changed_paths": value["changed_paths"],
                "body_free": True,
                "automatic_progression": False,
            }
        )
        == ()
    )


def _e3_runtime_record_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_RUNTIME_RECORD_KEYS
        or value.get("body_free") is not True
        or type(value.get("evidence_body")) is not dict
        or value.get("logical_sha256")
        != artifact_sha256(value["evidence_body"])
    ):
        return False
    role = value.get("evidence_role")
    if role == "OPERATIONAL_RUNTIME_OBSERVATION_CANDIDATE":
        return _e3_operational_body_valid(value["evidence_body"])
    if role == "BOOTSTRAP_READINESS_CANDIDATE":
        return _e3_readiness_body_valid(value["evidence_body"])
    if (
        role
        == "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE_CANDIDATE"
    ):
        return _e3_failure_body_valid(value["evidence_body"])
    return False


def _e3_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _e3_git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout


def _e3_changed_paths(root: Path, commit: str) -> list[str]:
    raw = _e3_git_bytes(
        root,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        "-z",
        commit,
    )
    return [
        item.decode("utf-8")
        for item in raw.split(b"\0")
        if item
    ]


def _e3_path_has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _e3_expected_repository(root: Path, name: str) -> bool:
    try:
        head = _e3_git(root, "rev-parse", "HEAD")
        main = _e3_git(root, "rev-parse", "refs/heads/main")
        top = Path(
            _e3_git(root, "rev-parse", "--show-toplevel")
        ).resolve()
        origin = _e3_git(
            root,
            "config",
            "--get",
            "remote.origin.url",
        ).rstrip("/").removesuffix(".git")
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(
        top == root
        and head == main
        and (
            origin.endswith(f"/MassyuRed/{name}")
            or origin.endswith(f":MassyuRed/{name}")
        )
    )


def _e3_artifact_repository_valid(
    value: Mapping[str, Any],
    *,
    root: Path,
) -> bool:
    identity = value["external_identity"]
    commit = identity["publication_commit_sha1"]
    base = value["publication_base_commit_sha1"]
    path = identity["path"]
    try:
        parents = _e3_git(
            root,
            "show",
            "-s",
            "--format=%P",
            commit,
        ).split()
        changed = _e3_changed_paths(root, commit)
        blob = _e3_git(root, "rev-parse", f"{commit}:{path}")
        raw = _e3_git_bytes(root, "show", f"{commit}:{path}")
        body = load_canonical_json_bytes(raw)
        reachable = subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        absent_at_base = subprocess.run(
            ["git", "cat-file", "-e", f"{base}:{path}"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode != 0
        head_blob = _e3_git(root, "rev-parse", f"HEAD:{path}")
        intervening = _e3_git(
            root,
            "rev-list",
            f"{commit}..HEAD",
            "--",
            path,
        ).splitlines()
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        return False
    return bool(
        parents == [base]
        and changed == value["changed_paths"]
        and changed == [path]
        and reachable
        and absent_at_base
        and intervening == []
        and blob == identity["git_blob_sha1"]
        and head_blob == blob
        and hashlib.sha256(raw).hexdigest() == identity["raw_sha256"]
        and raw == canonical_json_bytes(value["published_body"]) + b"\n"
        and body == value["published_body"] == value["postfetch_body"]
    )


def _e3_source_state(root: Path) -> tuple[str, str] | None:
    try:
        commit = _e3_git(root, "rev-parse", "HEAD")
        tree = _e3_git(root, "rev-parse", "HEAD^{tree}")
        clean = (
            _e3_git(
                root,
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return (commit, tree) if clean else None


def _e3_identity_fresh_at_base(
    root: Path,
    identity: Mapping[str, Any],
    base_commit: str,
) -> bool:
    publication_commit = identity["publication_commit_sha1"]
    path = identity["path"]
    try:
        ancestry = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                publication_commit,
                base_commit,
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode == 0
        blob = _e3_git(
            root,
            "rev-parse",
            f"{base_commit}:{path}",
        )
        raw = _e3_git_bytes(
            root,
            "show",
            f"{base_commit}:{path}",
        )
        intervening = _e3_git(
            root,
            "rev-list",
            f"{publication_commit}..{base_commit}",
            "--",
            path,
        ).splitlines()
    except (OSError, subprocess.SubprocessError):
        return False
    return bool(
        ancestry
        and intervening == []
        and blob == identity["git_blob_sha1"]
        and hashlib.sha256(raw).hexdigest() == identity["raw_sha256"]
    )


def _e3_membership_valid(
    index: int,
    artifacts: list[dict[str, Any]],
    runtime: list[dict[str, Any]],
) -> bool:
    artifact_roles = [
        row["external_identity"]["artifact_role"] for row in artifacts
    ]
    runtime_roles = [row["evidence_role"] for row in runtime]
    if index == 0:
        return bool(
            artifact_roles
            == ["RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"]
            and runtime_roles == []
        )
    if index == 1:
        return bool(
            artifact_roles == ["RECOVERY_EPOCH003_OPERATIONAL_ADMISSION"]
            and runtime_roles == []
        )
    if index == 2:
        return bool(
            artifact_roles == ["RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT"]
            and runtime_roles == []
        )
    if index == 3:
        return bool(
            artifact_roles == []
            and len(runtime_roles) == 2
            and "OPERATIONAL_RUNTIME_OBSERVATION_CANDIDATE"
            in runtime_roles
            and len(
                set(runtime_roles)
                & {
                    "BOOTSTRAP_READINESS_CANDIDATE",
                    (
                        "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_"
                        "FAILURE_CANDIDATE"
                    ),
                }
            )
            == 1
        )
    if index != 4 or runtime_roles != [] or len(artifact_roles) != 2:
        return False
    operational = {
        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
        (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
            "OBSERVATION_FAILURE_EVIDENCE"
        ),
    }
    terminal = {
        "RECOVERY_EPOCH003_BOOTSTRAP_READINESS",
        "RECOVERY_EPOCH003_FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_FAILURE",
    }
    return bool(
        len(set(artifact_roles)) == 2
        and len(set(artifact_roles) & operational) == 1
        and len(set(artifact_roles) & terminal) == 1
    )


def _e3_reference_phase_valid(
    rows: list[dict[str, Any]],
    source_state: tuple[str, str],
) -> bool:
    body = rows[0]["artifact_records"][0]["published_body"]
    return bool(
        _e3_reference_body_valid(body)
        and source_state
        == (body["source_commit_sha1"], body["source_tree_sha1"])
    )


def _e3_admission_phase_valid(
    rows: list[dict[str, Any]],
    *,
    artifact_root: Path,
    source_root: Path,
    source_state: tuple[str, str],
) -> bool:
    reference_record = rows[0]["artifact_records"][0]
    admission_record = rows[1]["artifact_records"][0]
    reference = reference_record["published_body"]
    reference_identity = reference_record["external_identity"]
    admission = admission_record["published_body"]
    admission_identity = admission_record["external_identity"]
    admission_base = admission_record["publication_base_commit_sha1"]
    if (
        not _e3_identity_fresh_at_base(
            artifact_root,
            reference_identity,
            admission_base,
        )
        or admission["predecessor_bindings"].get(
            "reference_runtime_observation_external_identity"
        )
        != reference_identity
        or source_state
        != (
            admission["source_closure"]["source_commit_sha1"],
            admission["source_closure"]["source_tree_sha1"],
        )
    ):
        return False
    rebuilt = build_recovery_epoch003_source_bootstrap_closure(
        {
            "source_repository_root": str(source_root),
            "source_commit_sha1": source_state[0],
            "source_tree_sha1": source_state[1],
            "reference_runtime_observation": reference,
            "reference_runtime_observation_external_identity": (
                reference_identity
            ),
        }
    )
    if (
        type(rebuilt) is not dict
        or rebuilt.get("source_closure") != admission["source_closure"]
        or rebuilt.get("bootstrap_closure")
        != admission["bootstrap_closure"]
    ):
        return False
    publication_state = {
        "artifact_repository_root": str(artifact_root),
        "external_identity": reference_identity,
        "postfetch_body": reference_record["postfetch_body"],
        "admission_base_commit_sha1": admission_base,
        "admission_base_tree_sha1": _e3_git(
            artifact_root,
            "rev-parse",
            f"{admission_base}^{{tree}}",
        ),
        "reference_publication_is_ancestor_of_admission_base": True,
        "reference_path_blob_at_admission_base_sha1": (
            reference_identity["git_blob_sha1"]
        ),
    }
    return (
        verify_recovery_epoch003_operational_admission_contract(
            {
                "verification_mode": "BODY_AND_POSTFETCH",
                "artifact_repository_root": str(artifact_root),
                "source_repository_observation": {
                    "source_repository_root": str(source_root),
                    "source_commit_sha1": source_state[0],
                    "source_tree_sha1": source_state[1],
                    "worktree_clean": True,
                },
                "operational_admission": admission,
                "operational_admission_external_identity": (
                    admission_identity
                ),
                "reference_runtime_observation": reference,
                "reference_publication_state": publication_state,
            }
        )
        == ()
    )


def _e3_event_phase_valid(
    rows: list[dict[str, Any]],
    *,
    artifact_root: Path,
) -> bool:
    reference_record = rows[0]["artifact_records"][0]
    admission_record = rows[1]["artifact_records"][0]
    event_record = rows[2]["artifact_records"][0]
    reference_identity = reference_record["external_identity"]
    admission_identity = admission_record["external_identity"]
    admission = admission_record["published_body"]
    event = event_record["published_body"]
    event_base = event_record["publication_base_commit_sha1"]
    supporting = sorted(
        [reference_identity, admission_identity],
        key=lambda item: (
            item["artifact_role"],
            item["path"],
            item["identity_sha256"],
        ),
    )
    return bool(
        _e3_identity_fresh_at_base(
            artifact_root,
            reference_identity,
            event_base,
        )
        and _e3_identity_fresh_at_base(
            artifact_root,
            admission_identity,
            event_base,
        )
        and event["source_closure"] == admission["source_closure"]
        and event["bootstrap_closure"] == admission["bootstrap_closure"]
        and event["authority"].get("operational_admission")
        == admission_identity
        and event["primary_evidence_artifact"] == admission_identity
        and event["publication"].get("supporting_artifacts")
        == supporting
        and event["publication"].get("supporting_artifact_count") == 2
        and event["publication"].get("expected_changed_path_count") == 1
        and event["publication"].get("base_commit_sha1")
        == event_record["publication_base_commit_sha1"]
        and event["publication"].get("supporting_artifact_set_sha256")
        == artifact_sha256(supporting)
    )


def _e3_projection(event: Mapping[str, Any]) -> dict[str, Any]:
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
        "pytest_distribution_identity": bootstrap[
            "expected_pytest_distribution_identity"
        ],
        "python_runtime_identity": bootstrap[
            "expected_python_runtime_identity"
        ],
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


def _e3_observed_projection(
    operational: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: operational[key]
        for key in _E3_PROJECTION_KEYS
    }


def _e3_phase4_records(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    by_role = {
        item["evidence_role"]: item
        for item in rows[3]["runtime_records"]
    }
    operational = by_role[
        "OPERATIONAL_RUNTIME_OBSERVATION_CANDIDATE"
    ]
    terminal = next(
        by_role[role]
        for role in (
            "BOOTSTRAP_READINESS_CANDIDATE",
            (
                "FORMAL_WORKER_BOOTSTRAP_PREFLIGHT_"
                "FAILURE_CANDIDATE"
            ),
        )
        if role in by_role
    )
    return operational, terminal


def _e3_phase4_valid(
    rows: list[dict[str, Any]],
    source_state: tuple[str, str],
) -> bool:
    reference = rows[0]["artifact_records"][0]["published_body"]
    event_record = rows[2]["artifact_records"][0]
    event = event_record["published_body"]
    operational_record, terminal_record = _e3_phase4_records(rows)
    operational = operational_record["evidence_body"]
    terminal = terminal_record["evidence_body"]
    expected = _e3_projection(event)
    expected_hash = artifact_sha256(expected)
    observed = _e3_observed_projection(operational)
    observed_hash = artifact_sha256(observed)
    owner_hash = operational["owner_operational_projection_sha256"]
    independent_hash = operational[
        "independent_operational_projection_sha256"
    ]
    runtime = operational["runtime_materialization"]
    roots = (
        operational["runtime_root_identity_sha256"],
        operational["reference_runtime_root_identity_sha256"],
        operational["attempt_registry_root_identity_sha256"],
    )
    identity_chain_valid = bool(
        operational["authority_token"] == _E3_PREFLIGHT_AUTHORITY
        and operational[
            "source_baseline_event_external_identity_sha256"
        ]
        == event_record["external_identity"]["identity_sha256"]
        and operational["candidate_version_id"]
        == event["candidate_version_id"]
        and source_state
        == (
            operational["source_commit_sha1"],
            operational["source_tree_sha1"],
        )
        and operational["source_closure_sha256"]
        == event["source_closure"]["source_closure_sha256"]
        and operational["bootstrap_closure_sha256"]
        == event["bootstrap_closure"]["bootstrap_closure_sha256"]
        and operational["worktree_clean"] is True
        and operational["environment_policy"]
        == event["bootstrap_closure"]["environment_policy"]
        and operational["environment_policy_sha256"]
        == artifact_sha256(operational["environment_policy"])
        and runtime["runtime_root_identity_sha256"]
        == operational["runtime_root_identity_sha256"]
        and runtime["dependency_lock_raw_sha256"]
        == operational["dependency_lock_raw_sha256"]
        and runtime["wheel_bundle_manifest_sha256"]
        == operational["wheel_bundle_manifest_sha256"]
        and runtime["distribution_count"]
        == len(
            event["bootstrap_closure"][
                "expected_installed_distributions"
            ]
        )
        and operational["reference_runtime_root_identity_sha256"]
        == reference["runtime_materialization"][
            "runtime_root_identity_sha256"
        ]
        and len(set(roots)) == 3
    )
    identity_mismatch = bool(
        not identity_chain_valid
        or expected != observed
        or owner_hash != observed_hash
    )
    independent_disagreement = bool(
        not identity_mismatch
        and independent_hash != observed_hash
    )
    if (
        set(expected) != _E3_PROJECTION_KEYS
        or set(observed) != _E3_PROJECTION_KEYS
        or terminal.get("candidate_version_id")
        != event["candidate_version_id"]
        or terminal.get("event1_external_identity_sha256")
        != event_record["external_identity"]["identity_sha256"]
    ):
        return False
    if (
        terminal_record["evidence_role"]
        == "BOOTSTRAP_READINESS_CANDIDATE"
    ):
        nested = terminal[
            "operational_runtime_observation_external_identity"
        ]
        return bool(
            not identity_mismatch
            and not independent_disagreement
            and independent_hash == observed_hash == expected_hash
            and terminal["authority_token"]
            == operational["authority_token"]
            and terminal["event1_bootstrap_closure"]
            == event["bootstrap_closure"]
            and terminal["operational_runtime_observation_sha256"]
            == operational["operational_runtime_observation_sha256"]
            and nested["artifact_role"]
            == "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
            and nested["logical_artifact_sha256"]
            == operational["operational_runtime_observation_sha256"]
            and terminal["expected_observed_projection_sha256"]
            == artifact_sha256(
                {"expected": expected_hash, "observed": observed_hash}
            )
        )
    if terminal.get("operational_runtime_observation_state") != "OBSERVED":
        return False
    failure_class = (
        "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
        if identity_mismatch
        else "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
        if independent_disagreement
        else None
    )
    nested = terminal[
        "operational_runtime_observation_external_identity"
    ]
    if (
        failure_class is None
        or terminal["failure_class"] != failure_class
        or terminal["authority_token"] != operational["authority_token"]
        or terminal["preflight_challenge_id"]
        != operational["preflight_challenge_id"]
        or terminal["preflight_id"] != operational["preflight_id"]
        or terminal["source_closure_sha256"]
        != event["source_closure"]["source_closure_sha256"]
        or terminal["bootstrap_closure_sha256"]
        != event["bootstrap_closure"]["bootstrap_closure_sha256"]
        or terminal["operational_runtime_observation_sha256"]
        != operational["operational_runtime_observation_sha256"]
        or nested["artifact_role"]
        != (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
            "OBSERVATION_FAILURE_EVIDENCE"
        )
        or nested["logical_artifact_sha256"]
        != operational["operational_runtime_observation_sha256"]
        or terminal["owner_operational_projection_sha256"]
        != observed_hash
    ):
        return False
    if failure_class == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH":
        return bool(
            terminal["independent_operational_projection_sha256"]
            == observed_hash
            and terminal["expected_observed_projection_sha256"]
            == artifact_sha256(
                {
                    "expected": expected_hash,
                    "observed": observed_hash,
                }
            )
        )
    return bool(
        terminal["independent_operational_projection_sha256"]
        == independent_hash
        and independent_hash != observed_hash
        and terminal["expected_observed_projection_sha256"]
        == artifact_sha256(
            {
                "owner": observed_hash,
                "independent": independent_hash,
            }
        )
    )


def _e3_phase5_valid(
    rows: list[dict[str, Any]],
    *,
    artifact_root: Path,
) -> bool:
    operational_candidate, terminal_candidate = _e3_phase4_records(rows)
    by_role = {
        item["external_identity"]["artifact_role"]: item
        for item in rows[4]["artifact_records"]
    }
    ready = (
        terminal_candidate["evidence_role"]
        == "BOOTSTRAP_READINESS_CANDIDATE"
    )
    operational_role = (
        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
        if ready
        else (
            "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
            "OBSERVATION_FAILURE_EVIDENCE"
        )
    )
    terminal_role = (
        "RECOVERY_EPOCH003_BOOTSTRAP_READINESS"
        if ready
        else (
            "RECOVERY_EPOCH003_FORMAL_WORKER_"
            "BOOTSTRAP_PREFLIGHT_FAILURE"
        )
    )
    operational = by_role.get(operational_role)
    terminal = by_role.get(terminal_role)
    event_identity = rows[2]["artifact_records"][0]["external_identity"]
    if (
        len(by_role) != 2
        or operational is None
        or terminal is None
        or operational["published_body"]
        != operational_candidate["evidence_body"]
        or terminal["published_body"]
        != terminal_candidate["evidence_body"]
        or not _e3_identity_fresh_at_base(
            artifact_root,
            event_identity,
            operational["publication_base_commit_sha1"],
        )
        or not _e3_identity_fresh_at_base(
            artifact_root,
            operational["external_identity"],
            terminal["publication_base_commit_sha1"],
        )
    ):
        return False
    nested = terminal["published_body"].get(
        "operational_runtime_observation_external_identity"
    )
    if nested is None:
        return False
    return nested == operational["external_identity"]


def validate_recovery_epoch003_parent_phase_evidence_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Revalidate exact6 Epoch003 evidence without advancing the cursor."""

    failure = ("RECOVERY_EPOCH003_PARENT_PHASE_EVIDENCE_INVALID",)
    try:
        if (
            type(state) is not dict
            or set(state) != _RECOVERY_EPOCH003_EVIDENCE_STATE_KEYS
            or not isinstance(state.get("artifact_repository_root"), str)
            or not state["artifact_repository_root"]
            or not isinstance(state.get("source_repository_root"), str)
            or not state["source_repository_root"]
            or state.get("phase_order")
            != list(_RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER)
            or type(state.get("completed_phases")) is not list
            or len(state["completed_phases"]) > 5
            or state["completed_phases"]
            != list(
                _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[
                    : len(state["completed_phases"])
                ]
            )
            or state.get("next_phase")
            != _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[
                len(state["completed_phases"])
            ]
            or state.get("reservation_count_delta") != 0
            or state.get("formal_exact134_invocation_count") != 0
            or state.get("automatic_progression") is not False
            or type(state.get("phase_evidence")) is not list
            or len(state["phase_evidence"])
            != len(state["completed_phases"])
        ):
            return failure
        artifact_input = Path(state["artifact_repository_root"])
        source_input = Path(state["source_repository_root"])
        if (
            _e3_path_has_symlink_component(artifact_input)
            or _e3_path_has_symlink_component(source_input)
            or not artifact_input.is_dir()
            or not source_input.is_dir()
        ):
            return failure
        artifact_root = artifact_input.resolve()
        source_root = source_input.resolve()
        _e3_git(artifact_root, "rev-parse", "HEAD")
        _e3_git(source_root, "rev-parse", "HEAD")
        # The initial zero-evidence cursor is shape-only compatibility
        # input.  It grants no repository, publication, or operational
        # credit and therefore intentionally does not assert repository
        # identities yet.
        if not state["completed_phases"]:
            return ()
        if (
            artifact_root == source_root
            or not _e3_expected_repository(artifact_root, "Cocolon")
            or not _e3_expected_repository(source_root, "mashos-api")
        ):
            return failure
        source_state = _e3_source_state(source_root)
        if source_state is None:
            return failure
        rows = state["phase_evidence"]
        for index, row in enumerate(rows):
            if (
                type(row) is not dict
                or set(row) != _RECOVERY_EPOCH003_PHASE_EVIDENCE_KEYS
                or row.get("phase")
                != _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[index]
                or row.get("owner_validation_state") != "PROVED"
                or row.get("independent_verification_state") != "PROVED"
                or row.get("phase_evidence_sha256")
                != _hash_without(row, "phase_evidence_sha256")
                or type(row.get("artifact_records")) is not list
                or type(row.get("runtime_records")) is not list
                or any(
                    not _e3_artifact_record_valid(record)
                    for record in row["artifact_records"]
                )
                or any(
                    not _e3_artifact_repository_valid(
                        record,
                        root=artifact_root,
                    )
                    for record in row["artifact_records"]
                )
                or any(
                    not _e3_runtime_record_valid(record)
                    for record in row["runtime_records"]
                )
            ):
                return failure
            artifacts = row["artifact_records"]
            runtime = row["runtime_records"]
            if artifacts != sorted(
                artifacts,
                key=lambda record: (
                    record["external_identity"]["artifact_role"],
                    record["external_identity"]["path"],
                    record["external_identity"]["identity_sha256"],
                ),
            ) or runtime != sorted(
                runtime,
                key=lambda record: (
                    record["evidence_role"],
                    record["logical_sha256"],
                ),
            ):
                return failure
            if not _e3_membership_valid(index, artifacts, runtime):
                return failure
        count = len(rows)
        if count >= 1 and not _e3_reference_phase_valid(
            rows,
            source_state,
        ):
            return failure
        if count >= 2 and not _e3_admission_phase_valid(
            rows,
            artifact_root=artifact_root,
            source_root=source_root,
            source_state=source_state,
        ):
            return failure
        if count >= 3 and not _e3_event_phase_valid(
            rows,
            artifact_root=artifact_root,
        ):
            return failure
        if count >= 4 and not _e3_phase4_valid(rows, source_state):
            return failure
        if count >= 5 and not _e3_phase5_valid(
            rows,
            artifact_root=artifact_root,
        ):
            return failure
        return ()
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        StopIteration,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


_RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ENVELOPE_KEYS = frozenset(
    {
        "current_strict_preflight_state",
        "parent_phase_evidence_state",
        "automatic_progression",
    }
)
_RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ZERO_EFFECTS = {
    "reference_runtime_materialization_count": 0,
    "operational_runtime_materialization_count": 0,
    "reference_observation_publication_count": 0,
    "operational_admission_publication_count": 0,
    "runtime_publication_count": 0,
    "candidate_publication_count": 0,
    "event1_publication_count": 0,
    "readiness_publication_count": 0,
    "failure_publication_count": 0,
    "reservation_count": 0,
    "attempt_count": 0,
    "formal_exact134_invocation_count": 0,
    "formal_collection_count": 0,
    "formal_execution_count": 0,
}


def _recovery_epoch003_current_strict_parent_result(
    failure_code: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "current_strict_parent_phase_result.v1"
        ),
        "current_strict_parent_phase_state": (
            "VALID" if failure_code is None else "INVALID"
        ),
        "failure_code": failure_code,
        "source_baseline_state": "UNLOCKED",
        "body_free": True,
        "automatic_progression": False,
        "pytest_main_called": False,
        **_RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ZERO_EFFECTS,
    }


def _recovery_epoch003_current_strict_preflight_result_valid(
    result: Any,
) -> bool:
    expected_keys = {
        "schema_version",
        "current_strict_preflight_state",
        "failure_code",
        "source_baseline_state",
        "body_free",
        "automatic_progression",
        "pytest_main_called",
        *_RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ZERO_EFFECTS,
    }
    return bool(
        type(result) is dict
        and set(result) == expected_keys
        and result.get("schema_version")
        == (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "current_strict_preflight_result.v1"
        )
        and result.get("current_strict_preflight_state") == "VALID"
        and result.get("failure_code") is None
        and result.get("source_baseline_state") == "UNLOCKED"
        and result.get("body_free") is True
        and result.get("automatic_progression") is False
        and result.get("pytest_main_called") is False
        and {
            key: result.get(key)
            for key in _RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ZERO_EFFECTS
        }
        == _RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ZERO_EFFECTS
    )


def execute_recovery_epoch003_current_strict_parent_phase_v1(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify the current preflight boundary without advancing the parent."""

    failure_code = "RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_PHASE_INVALID"
    try:
        preflight_source = (
            state.get("current_strict_preflight_state")
            if type(state) is dict
            else state
        )
        evidence_source = (
            state.get("parent_phase_evidence_state")
            if type(state) is dict
            else state
        )
        preflight_state = deepcopy(preflight_source)
        evidence_state = deepcopy(evidence_source)
        preflight_result = (
            execute_recovery_epoch003_current_strict_preflight_v1(
                preflight_state
            )
        )
        evidence_issues = (
            validate_recovery_epoch003_parent_phase_evidence_state(
                evidence_state
            )
        )
        envelope_valid = bool(
            type(state) is dict
            and set(state)
            == _RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_ENVELOPE_KEYS
            and state.get("automatic_progression") is False
            and type(preflight_state) is dict
            and type(evidence_state) is dict
        )
        preflight_boundary_valid = bool(
            type(evidence_state.get("completed_phases")) is list
            and evidence_state["completed_phases"]
            == list(_RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[:3])
            and evidence_state.get("next_phase")
            == _RECOVERY_EPOCH003_EVIDENCE_PHASE_ORDER[3]
        )
        event_record = evidence_state["phase_evidence"][2][
            "artifact_records"
        ][0]
        event_cross_binding_valid = bool(
            type(event_record) is dict
            and preflight_state.get("event1_at_publication")
            == event_record.get("published_body")
            and preflight_state.get("event1_at_postfetch")
            == event_record.get("postfetch_body")
            and preflight_state.get("event1_external_identity")
            == event_record.get("external_identity")
        )
        if (
            envelope_valid
            and preflight_boundary_valid
            and event_cross_binding_valid
            and _recovery_epoch003_current_strict_preflight_result_valid(
                preflight_result
            )
            and evidence_issues == ()
        ):
            return _recovery_epoch003_current_strict_parent_result(None)
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        pass
    return _recovery_epoch003_current_strict_parent_result(failure_code)


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
    "RECOVERY_EPOCH003_PARENT_PHASE_ORDER",
    "validate_recovery_epoch003_parent_phase_state",
    "validate_recovery_epoch003_parent_phase_evidence_state",
    "execute_recovery_epoch003_current_strict_parent_phase_v1",
]
