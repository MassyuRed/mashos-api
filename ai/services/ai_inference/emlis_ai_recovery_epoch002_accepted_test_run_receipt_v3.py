# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 002 accepted-test-run receipt owner."""

from copy import deepcopy
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    fresh_recovery_epoch001_canonical_current_closure,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3 import (
    validate_recovery_epoch002_success_terminal_state,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "accepted_test_run_receipt.v1"
)
RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    formal_worker_terminal_result formal_worker_result_sha256
    terminal_result_artifact success_lineage step_view_sha256_by_step
    proof_sources proof_source_closure_sha256 owner_validation_state
    independent_verification_state accepted body_free automatic_progression
    accepted_test_run_receipt_sha256
    """
)
RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS = _keys(
    """
    schema_version candidate_version_id source_baseline_event
    successful_reservation prior_reservation_count prior_reservation_history
    prior_reservation_history_sha256 success_lineage_sha256
    """
)
RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS = _keys(
    """
    reservation_ordinal reservation_artifact attempt_id disposition_kind
    disposition_artifact
    """
)
RECOVERY_EPOCH002_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
RECOVERY_EPOCH002_PROOF_SOURCE_KEYS = _keys(
    "path git_blob_sha1 sha256"
)
RECOVERY_EPOCH002_ACCEPTED_STATE_KEYS = _keys(
    """
    accepted_test_run_receipt issuance_requested
    retry_history_observation source_context terminal_owner_state
    terminal_publication
    """
)
RECOVERY_EPOCH002_SOURCE_CONTEXT_KEYS = _keys(
    """
    bootstrap_closure candidate_allocation event1_artifact event1_identity
    event1_postfetch_evidence readiness_artifact readiness_identity
    readiness_postfetch_evidence successful_reservation_artifact
    successful_reservation_identity
    successful_reservation_postfetch_evidence successor_source_closure
    """
)
RECOVERY_EPOCH002_RETRY_HISTORY_OBSERVATION_KEYS = _keys(
    """
    prior_disposition_artifacts prior_disposition_postfetch_evidence
    prior_reservation_artifacts prior_reservation_history
    prior_reservation_postfetch_evidence successful_attempt_id
    successful_reservation_ordinal
    """
)

_SUCCESS_LINEAGE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.success_lineage.v1"
)
_TERMINAL_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_terminal_result.v2"
)
_RESERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_test_run_reservation.v1"
)
_UNKNOWN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "attempt_consumption_unknown_disposition.v1"
)
_TERMINAL_KEYS = _keys(
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
_RESERVATION_KEYS = _keys(
    """
    schema_version authority_token challenge_id authority_challenge_id
    attempt_id candidate_version_id logical_cycle_id recovery_epoch_id
    formal_node_registry_sha256 reservation_state reserved_at_utc
    source_baseline_event source_closure automatic_progression body_free
    formal_test_run_reservation_sha256 reservation_ordinal
    publication_base_commit_sha1 bootstrap_readiness_artifact
    prior_reservation_count prior_reservation_history
    prior_reservation_history_sha256 lineage_state event1_challenge_id
    preflight_challenge_id
    """
)
_UNKNOWN_KEYS = _keys(
    """
    schema_version reservation_artifact attempt_id checkpoint_status
    last_valid_stage terminal_result_status exit_class exit_code signal_number
    stop_code automatic_retry body_free
    attempt_consumption_unknown_disposition_sha256
    """
)
_POSTFETCH_KEYS = _keys(
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
_POSTFETCH_ARTIFACT_KEYS = _keys(
    "path git_blob_sha1 raw_sha256 logical_artifact_sha256 body_free"
)
_UNCHANGED_KEYS = _keys(
    "scope mode_type_sha_complete mismatches observation_sha256"
)
_EXACT1_KEYS = _keys(
    """
    artifact identity changed_paths parent_commit_sha1s expected_old_sha1
    observed_old_sha1 postfetch_evidence postfetch_state
    """
)
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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


def _expected_identity(
    artifact: Any,
    *,
    identity: Mapping[str, Any],
    allowed_roles: frozenset[str],
    schema: str,
    logical_hash_key: str,
) -> dict[str, Any] | None:
    if (
        type(artifact) is not dict
        or artifact.get("schema_version") != schema
        or artifact.get("body_free") is not True
        or artifact.get(logical_hash_key)
        != _hash_without(artifact, logical_hash_key)
        or type(identity) is not dict
        or set(identity) != RECOVERY_EPOCH002_EXTERNAL_IDENTITY_KEYS
        or identity.get("artifact_role") not in allowed_roles
        or identity.get("schema_version") != schema
        or identity.get("repository_full_name") != "MassyuRed/Cocolon"
        or identity.get("body_free") is not True
        or _SHA1_RE.fullmatch(str(identity.get("publication_commit_sha1", "")))
        is None
        or not isinstance(identity.get("path"), str)
        or not identity.get("path")
    ):
        return None
    payload = canonical_json_bytes(dict(artifact)) + b"\n"
    header = f"blob {len(payload)}\0".encode("ascii")
    expected = {
        "artifact_role": identity["artifact_role"],
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
    return expected


def _postfetch_valid(
    evidence: Any,
    identity: Mapping[str, Any],
    *,
    expected_parent_commit: str | None = None,
    expected_base_tree: str | None = None,
) -> bool:
    if (
        type(evidence) is not dict
        or set(evidence) != _POSTFETCH_KEYS
        or type(identity) is not dict
        or set(identity) != RECOVERY_EPOCH002_EXTERNAL_IDENTITY_KEYS
    ):
        return False
    parent = evidence.get("publication_parent_commit_sha1s")
    if (
        type(parent) is not list
        or len(parent) != 1
        or _SHA1_RE.fullmatch(str(parent[0])) is None
    ):
        return False
    if expected_parent_commit is not None and parent != [
        expected_parent_commit
    ]:
        return False
    if (
        expected_base_tree is not None
        and evidence.get("base_tree_sha1") != expected_base_tree
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
    unchanged = evidence.get("unchanged_path_observation")
    return (
        evidence.get("repository_full_name") == "MassyuRed/Cocolon"
        and evidence.get("verification_ref") == "refs/heads/main"
        and evidence.get("verification_commit_sha1")
        == identity.get("publication_commit_sha1")
        and evidence.get("authoritative_ref_read") is True
        and evidence.get("authoritative_base_tree_read") is True
        and _SHA1_RE.fullmatch(str(evidence.get("base_tree_sha1", "")))
        is not None
        and _SHA1_RE.fullmatch(str(evidence.get("target_tree_sha1", "")))
        is not None
        and evidence.get("base_tree_sha1")
        != evidence.get("target_tree_sha1")
        and evidence.get("publication_commit_sha1")
        == identity.get("publication_commit_sha1")
        and evidence.get("publication_reachable_from_verification_ref")
        is True
        and evidence.get("publication_changed_paths")
        == [identity.get("path")]
        and evidence.get("target_absent_at_base") is True
        and evidence.get("semantic_ancestor_verified") is True
        and type(evidence.get("target_tree_build_count")) is int
        and evidence.get("target_tree_build_count") == 1
        and type(evidence.get("publication_commit_parent_count")) is int
        and evidence.get("publication_commit_parent_count") == 1
        and evidence.get("requested_expected_old_sha1") == parent[0]
        and evidence.get("observed_old_sha1") == parent[0]
        and evidence.get("server_side_expected_old_applied") is True
        and evidence.get("authoritative_head_read") is True
        and evidence.get("authoritative_parent_read") is True
        and evidence.get("authoritative_tree_read") is True
        and evidence.get("authoritative_recursive_tree_read") is True
        and evidence.get("changed_path_proof_complete") is True
        and type(evidence.get("artifact_at_publication")) is dict
        and set(evidence["artifact_at_publication"])
        == _POSTFETCH_ARTIFACT_KEYS
        and evidence["artifact_at_publication"] == artifact
        and type(evidence.get("artifact_at_verification_ref")) is dict
        and set(evidence["artifact_at_verification_ref"])
        == _POSTFETCH_ARTIFACT_KEYS
        and evidence["artifact_at_verification_ref"] == artifact
        and type(unchanged) is dict
        and set(unchanged) == _UNCHANGED_KEYS
        and unchanged.get("scope") == "ALL_PATHS_EXCEPT_EXACT1_TARGET"
        and unchanged.get("mode_type_sha_complete") is True
        and unchanged.get("mismatches") == []
        and unchanged.get("observation_sha256")
        == _hash_without(unchanged, "observation_sha256")
        and evidence.get("unchanged_path_mismatches") == []
        and evidence.get("owner_issue_codes") == []
        and evidence.get("independent_issue_codes") == []
        and evidence.get("postfetch_state") == "POSTVERIFIED"
    )


def _terminal_publication_valid(
    publication: Any,
    terminal: Mapping[str, Any],
) -> bool:
    if (
        type(publication) is not dict
        or set(publication) != _EXACT1_KEYS
        or publication.get("artifact") != terminal
        or type(publication.get("identity")) is not dict
        or publication.get("changed_paths")
        != [publication["identity"].get("path")]
        or publication.get("parent_commit_sha1s")
        != [publication.get("expected_old_sha1")]
        or publication.get("observed_old_sha1")
        != publication.get("expected_old_sha1")
        or publication.get("postfetch_state") != "POSTVERIFIED"
    ):
        return False
    expected = _expected_identity(
        terminal,
        identity=publication["identity"],
        allowed_roles=frozenset(
            {"FORMAL_WORKER_TERMINAL_RESULT", "TERMINAL_RESULT"}
        ),
        schema=_TERMINAL_SCHEMA,
        logical_hash_key="formal_worker_result_sha256",
    )
    return (
        expected == publication["identity"]
        and _postfetch_valid(
            publication.get("postfetch_evidence"),
            publication["identity"],
            expected_parent_commit=publication.get("expected_old_sha1"),
        )
    )


def _accepted_shape_valid(accepted: Any) -> bool:
    return (
        type(accepted) is dict
        and set(accepted) == RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_KEYS
        and accepted.get("schema_version")
        == RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_SCHEMA
        and accepted.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and accepted.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        and accepted.get("owner_validation_state") == "PROVED"
        and accepted.get("independent_verification_state") == "PROVED"
        and accepted.get("accepted") is True
        and accepted.get("body_free") is True
        and accepted.get("automatic_progression") is False
        and accepted.get("accepted_test_run_receipt_sha256")
        == _hash_without(
            accepted,
            "accepted_test_run_receipt_sha256",
        )
    )


def _terminal_success_valid(terminal: Any) -> bool:
    if (
        type(terminal) is not dict
        or set(terminal) != _TERMINAL_KEYS
        or terminal.get("schema_version") != _TERMINAL_SCHEMA
        or terminal.get("body_free") is not True
        or terminal.get("formal_worker_result_sha256")
        != _hash_without(terminal, "formal_worker_result_sha256")
        or type(terminal.get("collection_node_ids")) is not list
        or type(terminal.get("executed_node_ids")) is not list
        or terminal.get("executed_node_ids")
        != terminal.get("collection_node_ids")
        or len(terminal.get("collection_node_ids")) != 134
        or type(terminal.get("outcomes")) is not list
        or len(terminal.get("outcomes")) != 134
        or type(terminal.get("states")) is not dict
        or set(terminal.get("states")) != set(
            terminal.get("collection_node_ids")
        )
        or any(value != "PASSED" for value in terminal["states"].values())
        or any(
            type(row) is not dict or row.get("result") != "PASSED"
            for row in terminal["outcomes"]
        )
        or type(terminal.get("counts")) is not dict
        or terminal["counts"].get("passed") != 134
        or any(
            terminal["counts"].get(key) != 0
            for key in (
                "failed",
                "errors",
                "skipped",
                "xfailed",
                "xpassed",
                "deselected",
                "collection_errors",
            )
        )
        or terminal.get("collection_errors") != 0
        or terminal.get("exit_class") != "EXITED"
        or type(terminal.get("exit_code")) is not int
        or terminal.get("exit_code") != 0
        or terminal.get("signal_number") is not None
        or terminal.get("timed_out") is not False
    ):
        return False
    return True


def _reservation_body_valid(
    artifact: Any,
    *,
    expected_ordinal: int,
    expected_history: list[dict[str, Any]],
) -> bool:
    return (
        type(artifact) is dict
        and set(artifact) == _RESERVATION_KEYS
        and artifact.get("schema_version") == _RESERVATION_SCHEMA
        and artifact.get("reservation_ordinal") == expected_ordinal
        and type(artifact.get("reservation_ordinal")) is int
        and artifact.get("prior_reservation_count")
        == len(expected_history)
        and type(artifact.get("prior_reservation_count")) is int
        and artifact.get("prior_reservation_history") == expected_history
        and artifact.get("prior_reservation_history_sha256")
        == artifact_sha256(
            {"prior_reservation_history": expected_history}
        )
        and artifact.get("reservation_state")
        == "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN"
        and artifact.get("automatic_progression") is False
        and artifact.get("body_free") is True
        and artifact.get("formal_test_run_reservation_sha256")
        == _hash_without(
            artifact,
            "formal_test_run_reservation_sha256",
        )
    )


def _disposition_body_valid(
    artifact: Any,
    *,
    disposition_kind: str,
    reservation_identity: Mapping[str, Any],
    attempt_id: str,
) -> tuple[bool, str, frozenset[str], str]:
    if disposition_kind == "FORMAL_FAILURE_ATTEMPT_PUBLISHED":
        valid = (
            type(artifact) is dict
            and set(artifact) == _TERMINAL_KEYS
            and artifact.get("schema_version") == _TERMINAL_SCHEMA
            and artifact.get("attempt_id") == attempt_id
            and artifact.get("body_free") is True
            and artifact.get("formal_worker_result_sha256")
            == _hash_without(
                artifact,
                "formal_worker_result_sha256",
            )
            and type(artifact.get("counts")) is dict
            and artifact["counts"].get("failed", 0) > 0
        )
        return (
            valid,
            _TERMINAL_SCHEMA,
            frozenset(
                {"FORMAL_WORKER_TERMINAL_RESULT", "TERMINAL_RESULT"}
            ),
            "formal_worker_result_sha256",
        )
    valid = (
        type(artifact) is dict
        and set(artifact) == _UNKNOWN_KEYS
        and artifact.get("schema_version") == _UNKNOWN_SCHEMA
        and artifact.get("reservation_artifact") == reservation_identity
        and artifact.get("attempt_id") == attempt_id
        and artifact.get("stop_code")
        == "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
        and artifact.get("automatic_retry") is False
        and artifact.get("body_free") is True
        and artifact.get(
            "attempt_consumption_unknown_disposition_sha256"
        )
        == _hash_without(
            artifact,
            "attempt_consumption_unknown_disposition_sha256",
        )
    )
    return (
        valid,
        _UNKNOWN_SCHEMA,
        frozenset(
            {
                "ATTEMPT_CONSUMPTION_UNKNOWN_DISPOSITION",
                "UNKNOWN_DISPOSITION",
            }
        ),
        "attempt_consumption_unknown_disposition_sha256",
    )


def _success_lineage_valid(
    state: Mapping[str, Any],
    accepted: Mapping[str, Any],
) -> bool:
    lineage = accepted.get("success_lineage")
    observation = state.get("retry_history_observation")
    context = state.get("source_context")
    if (
        type(lineage) is not dict
        or set(lineage) != RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS
        or lineage.get("schema_version") != _SUCCESS_LINEAGE_SCHEMA
        or lineage.get("success_lineage_sha256")
        != _hash_without(lineage, "success_lineage_sha256")
        or type(observation) is not dict
        or set(observation)
        != RECOVERY_EPOCH002_RETRY_HISTORY_OBSERVATION_KEYS
        or type(context) is not dict
    ):
        return False
    history = lineage.get("prior_reservation_history")
    observed_history = observation.get("prior_reservation_history")
    reservation_bodies = observation.get("prior_reservation_artifacts")
    disposition_bodies = observation.get("prior_disposition_artifacts")
    reservation_fetches = observation.get(
        "prior_reservation_postfetch_evidence"
    )
    disposition_fetches = observation.get(
        "prior_disposition_postfetch_evidence"
    )
    if (
        type(history) is not list
        or history != observed_history
        or lineage.get("prior_reservation_count") != len(history)
        or type(lineage.get("prior_reservation_count")) is not int
        or lineage.get("prior_reservation_history_sha256")
        != artifact_sha256({"prior_reservation_history": history})
        or any(
            type(rows) is not list or len(rows) != len(history)
            for rows in (
                reservation_bodies,
                disposition_bodies,
                reservation_fetches,
                disposition_fetches,
            )
        )
    ):
        return False
    attempt_ids: set[str] = set()
    identity_hashes: set[str] = set()
    previous_history: list[dict[str, Any]] = []
    readiness_identity = context.get("readiness_identity")
    readiness_fetch = context.get("readiness_postfetch_evidence")
    previous_commit = (
        readiness_identity.get("publication_commit_sha1")
        if type(readiness_identity) is dict
        else None
    )
    previous_tree = (
        readiness_fetch.get("target_tree_sha1")
        if type(readiness_fetch) is dict
        else None
    )
    for index, row in enumerate(history):
        ordinal = index + 1
        if (
            type(row) is not dict
            or set(row) != RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS
            or row.get("reservation_ordinal") != ordinal
            or not isinstance(row.get("attempt_id"), str)
            or row["attempt_id"] in attempt_ids
            or row.get("disposition_kind")
            not in {
                "FORMAL_FAILURE_ATTEMPT_PUBLISHED",
                "ATTEMPT_CONSUMPTION_UNKNOWN_STOP_PUBLISHED",
            }
        ):
            return False
        reservation_identity = row.get("reservation_artifact")
        disposition_identity = row.get("disposition_artifact")
        reservation_body = reservation_bodies[index]
        disposition_body = disposition_bodies[index]
        if not _reservation_body_valid(
            reservation_body,
            expected_ordinal=ordinal,
            expected_history=previous_history,
        ):
            return False
        if (
            type(reservation_identity) is not dict
            or type(disposition_identity) is not dict
        ):
            return False
        if row.get("attempt_id") != reservation_body.get("attempt_id"):
            return False
        expected_reservation_identity = _expected_identity(
            reservation_body,
            identity=reservation_identity,
            allowed_roles=frozenset(
                {"FORMAL_TEST_RUN_RESERVATION", "RESERVATION"}
            ),
            schema=_RESERVATION_SCHEMA,
            logical_hash_key="formal_test_run_reservation_sha256",
        )
        if expected_reservation_identity != reservation_identity:
            return False
        valid_disposition, schema, roles, hash_key = (
            _disposition_body_valid(
                disposition_body,
                disposition_kind=row["disposition_kind"],
                reservation_identity=reservation_identity,
                attempt_id=row["attempt_id"],
            )
        )
        expected_disposition_identity = _expected_identity(
            disposition_body,
            identity=disposition_identity,
            allowed_roles=roles,
            schema=schema,
            logical_hash_key=hash_key,
        )
        if (
            not valid_disposition
            or expected_disposition_identity != disposition_identity
        ):
            return False
        for identity in (reservation_identity, disposition_identity):
            identity_hash = identity.get("identity_sha256")
            if identity_hash in identity_hashes:
                return False
            identity_hashes.add(identity_hash)
        if not _postfetch_valid(
            reservation_fetches[index],
            reservation_identity,
            expected_parent_commit=previous_commit,
            expected_base_tree=previous_tree,
        ):
            return False
        previous_commit = reservation_identity["publication_commit_sha1"]
        previous_tree = reservation_fetches[index]["target_tree_sha1"]
        if not _postfetch_valid(
            disposition_fetches[index],
            disposition_identity,
            expected_parent_commit=previous_commit,
            expected_base_tree=previous_tree,
        ):
            return False
        previous_commit = disposition_identity["publication_commit_sha1"]
        previous_tree = disposition_fetches[index]["target_tree_sha1"]
        attempt_ids.add(row["attempt_id"])
        previous_history.append(deepcopy(row))

    successful_identity = lineage.get("successful_reservation")
    successful_body = context.get("successful_reservation_artifact")
    successful_ordinal = len(history) + 1
    if (
        type(successful_identity) is not dict
        or type(successful_body) is not dict
        or
        not _reservation_body_valid(
            successful_body,
            expected_ordinal=successful_ordinal,
            expected_history=history,
        )
        or _expected_identity(
            successful_body,
            identity=successful_identity,
            allowed_roles=frozenset(
                {"FORMAL_TEST_RUN_RESERVATION", "RESERVATION"}
            ),
            schema=_RESERVATION_SCHEMA,
            logical_hash_key="formal_test_run_reservation_sha256",
        )
        != successful_identity
        or successful_identity
        != context.get("successful_reservation_identity")
        or observation.get("successful_reservation_ordinal")
        != successful_ordinal
        or type(observation.get("successful_reservation_ordinal")) is not int
        or observation.get("successful_attempt_id")
        != successful_body.get("attempt_id")
        or successful_body.get("attempt_id") in attempt_ids
        or successful_identity.get("identity_sha256") in identity_hashes
        or not _postfetch_valid(
            context.get("successful_reservation_postfetch_evidence"),
            successful_identity,
            expected_parent_commit=previous_commit,
            expected_base_tree=previous_tree,
        )
    ):
        return False
    terminal = accepted.get("formal_worker_terminal_result")
    successful_fetch = context["successful_reservation_postfetch_evidence"]
    terminal_publication = state.get("terminal_publication")
    return (
        type(terminal) is dict
        and lineage.get("candidate_version_id")
        == accepted.get("candidate_version_id")
        == successful_body.get("candidate_version_id")
        == terminal.get("candidate_version_id")
        and lineage.get("source_baseline_event")
        == context.get("event1_identity")
        and lineage.get("source_baseline_event", {}).get("identity_sha256")
        == successful_body.get("source_baseline_event", {}).get(
            "identity_sha256"
        )
        and terminal.get("attempt_id") == successful_body.get("attempt_id")
        and type(terminal_publication) is dict
        and terminal_publication.get("parent_commit_sha1s")
        == [successful_identity.get("publication_commit_sha1")]
        and terminal_publication.get("postfetch_evidence", {}).get(
            "base_tree_sha1"
        )
        == successful_fetch.get("target_tree_sha1")
    )


def _validate_recovery_epoch002_accepted_test_run_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate an observed Accepted receipt without issuing one."""

    if (
        type(state) is not dict
        or set(state) != RECOVERY_EPOCH002_ACCEPTED_STATE_KEYS
    ):
        return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)
    accepted = state.get("accepted_test_run_receipt")
    if not _accepted_shape_valid(accepted):
        return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)

    context = state.get("source_context")
    if (
        type(context) is not dict
        or set(context) != RECOVERY_EPOCH002_SOURCE_CONTEXT_KEYS
    ):
        return ("SOURCE_RUNTIME_BOOTSTRAP_PARITY_INVALID",)
    if (
        type(context.get("readiness_postfetch_evidence")) is dict
        and context["readiness_postfetch_evidence"].get("postfetch_state")
        in {"UNKNOWN", "PENDING"}
        and state.get("issuance_requested") is True
    ):
        return ("ACCEPTED_RECEIPT_FORBIDDEN_UNDER_UNCERTAINTY",)

    terminal = accepted.get("formal_worker_terminal_result")
    if (
        not _terminal_publication_valid(
            state.get("terminal_publication"),
            terminal,
        )
        or accepted.get("terminal_result_artifact")
        != state.get("terminal_publication", {}).get("identity")
        or accepted.get("formal_worker_result_sha256")
        != terminal.get("formal_worker_result_sha256")
    ):
        return ("POSTVERIFIED_TERMINAL_REQUIRED",)
    if not _terminal_success_valid(terminal):
        return ("TERMINAL_ALL_SUCCESS_REQUIRED",)
    if (
        type(terminal.get("formal_exact134_invocation_count")) is not int
        or terminal.get("formal_exact134_invocation_count") != 1
    ):
        return ("FORMAL_INVOCATION_EXACT1_REQUIRED",)

    terminal_owner = state.get("terminal_owner_state")
    source_closure = context.get("successor_source_closure")
    bootstrap = context.get("bootstrap_closure")
    parity = (
        terminal_owner.get("parity_bindings")
        if type(terminal_owner) is dict
        else None
    )
    if (
        type(terminal_owner) is not dict
        or terminal_owner.get("terminal_result") != terminal
        or terminal_owner.get("terminal_publication")
        != state.get("terminal_publication")
        or validate_recovery_epoch002_success_terminal_state(
            terminal_owner
        )
        != ()
        or type(source_closure) is not dict
        or type(bootstrap) is not dict
        or type(parity) is not dict
        or terminal.get("source_closure_sha256")
        != source_closure.get("source_closure_sha256")
        or terminal.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or parity.get("source_closure_sha256")
        != terminal.get("source_closure_sha256")
        or parity.get("bootstrap_closure_sha256")
        != terminal.get("bootstrap_closure_sha256")
        or parity.get("python_runtime_identity_sha256")
        != terminal.get("python_runtime_identity_sha256")
        or parity.get("pytest_distribution_identity_sha256")
        != terminal.get("pytest_distribution_identity_sha256")
    ):
        return ("SOURCE_RUNTIME_BOOTSTRAP_PARITY_INVALID",)

    event = context.get("event1_artifact")
    readiness = context.get("readiness_artifact")
    reservation = context.get("successful_reservation_artifact")
    allocation = context.get("candidate_allocation")
    candidate = accepted.get("candidate_version_id")
    if (
        any(
            type(value) is not dict
            for value in (event, readiness, reservation, allocation)
        )
        or any(
            value.get("candidate_version_id") != candidate
            for value in (terminal, event, readiness, reservation, allocation)
        )
        or parity.get("event1_candidate_version_id") != candidate
        or parity.get("readiness_candidate_version_id") != candidate
        or parity.get("reservation_candidate_version_id") != candidate
    ):
        return ("EVENT_READINESS_RESERVATION_PARITY_INVALID",)

    if not _success_lineage_valid(state, accepted):
        return ("SUCCESS_LINEAGE_INVALID",)

    proof_sources = accepted.get("proof_sources")
    step_views = accepted.get("step_view_sha256_by_step")
    outcomes = terminal.get("outcomes")
    if type(outcomes) is not list:
        return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)
    expected_proof_sources_by_path: dict[str, dict[str, Any]] = {}
    for outcome in outcomes:
        if type(outcome) is not dict:
            return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)
        source_path = outcome.get("source_path")
        source_identity = {
            "path": source_path,
            "git_blob_sha1": outcome.get("source_blob_sha1"),
            "sha256": outcome.get("source_sha256"),
        }
        if (
            not isinstance(source_path, str)
            or not source_path
            or (
                source_path in expected_proof_sources_by_path
                and expected_proof_sources_by_path[source_path]
                != source_identity
            )
        ):
            return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)
        expected_proof_sources_by_path[source_path] = source_identity
    expected_proof_sources = [
        expected_proof_sources_by_path[path]
        for path in sorted(expected_proof_sources_by_path)
    ]
    canonical = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT,
    )
    expected_step_views = {
        str(step): artifact_sha256(
            canonical["step_views"][f"step_{step}"]
        )
        for step in range(11)
    }
    if (
        type(proof_sources) is not list
        or proof_sources != expected_proof_sources
        or any(
            type(row) is not dict
            or set(row) != RECOVERY_EPOCH002_PROOF_SOURCE_KEYS
            for row in proof_sources
        )
        or accepted.get("proof_source_closure_sha256")
        != artifact_sha256(proof_sources)
        or accepted.get("proof_source_closure_sha256")
        != source_closure.get("proof_source_closure_sha256")
        or canonical.get("canonical_current_closure_sha256")
        != source_closure.get("canonical_current_closure_sha256")
        or canonical.get("source_dependency_closure_sha256")
        != source_closure.get("source_dependency_closure_sha256")
        or type(step_views) is not dict
        or set(step_views) != {str(step) for step in range(11)}
        or step_views != expected_step_views
    ):
        return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)
    return ()


def validate_recovery_epoch002_accepted_test_run_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed observed Accepted receipt state."""

    try:
        if _contains_forbidden_state_key(state):
            return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)
        return _validate_recovery_epoch002_accepted_test_run_state_impl(
            state
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
        return ("ACCEPTED_TEST_RUN_RECEIPT_INVALID",)


__all__ = [
    "RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_SCHEMA",
    "RECOVERY_EPOCH002_ACCEPTED_TEST_RUN_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_LINEAGE_KEYS",
    "RECOVERY_EPOCH002_PRIOR_RESERVATION_ROW_KEYS",
    "RECOVERY_EPOCH002_EXTERNAL_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_PROOF_SOURCE_KEYS",
    "validate_recovery_epoch002_accepted_test_run_state",
]
