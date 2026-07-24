# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free sequence ledger contracts for Recovery Epoch 001.

This module builds and validates candidates only.  It has no filesystem,
GitHub, ref-update, formal-test execution, or automatic-progression path.
"""

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Callable, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)


RECOVERY_EPOCH001_SEQUENCE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001."
    "recovery_epoch001.sequence_event.v2"
)
RECOVERY_EPOCH001_FORMAL_TEST_RUN_RESERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.formal_test_run_reservation.v1"
)
RECOVERY_EPOCH001_SOURCE_BASELINE_CLOSURE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "source_baseline_closure_receipt.v2"
)
RECOVERY_EPOCH001_INDEPENDENT_SEQUENCE_VERIFIER: Callable[..., Any] = (
    lambda *_args, **_kwargs: ()
)

_CANDIDATE = "nls_v3_rc_0034"
_LOGICAL_CYCLE = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH = "NLS_V3_CYCLE001_RECOVERY_EPOCH_001"
_LEDGER = "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_SEQUENCE_LEDGER"
_PREFIX = "EmlisAIの実装済み資料/documents/"
_REF_UPDATE_MODE = "EXPECTED_OLD_SHA_LEASE_WITH_VERIFIED_DIRECT_CHILD"
_EVENT1_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event_20260724.json"
)
_EVENT2_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "SequenceEvent02_Step0_10PrerequisitesProved_BodyFree_Event_20260724.json"
)
_SOURCE_RECEIPT_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "SourceBaselineClosure_BodyFree_Receipt_20260724.json"
)
_P0_DOCUMENT_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_ProcessNonconformance_"
    "CanonicalRecoveryEpoch001_ParentDesignAddendum_ReadOnly_20260723.md"
)
_P0_RECEIPT_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_ProcessNonconformance_"
    "CanonicalRecoveryEpoch001_ParentDesignAddendum_ReadOnly_"
    "BodyFree_Receipt_20260723.json"
)
_P0_DOCUMENT_BLOB = "3333ae29ec0f4e9dde614bc9cd520448f61d2386"
_P0_RECEIPT_BLOB = "bdfbd559535db06ae4af35fe1bb58716d6566126"
_P0_DOCUMENT_RAW_SHA256 = (
    "46333ede4b86a9ced0a5223e8df8dea35287548c676ce15c7787602b9a62b45c"
)
_P0_RECEIPT_RAW_SHA256 = (
    "70563fa0732f97e9c54d3e8371741253e834440a618936e448a31b4d1cf5c30e"
)
_P0_DOCUMENT_COMMIT = "90a2c009b8a463110e01b907224e52ea50912bd8"
_P0_RECEIPT_COMMIT = "f20165e3eda11dc0262373d5f82f63377df76f10"
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:+-]{1,512}$")

_EVENT_KEYS = frozenset(
    {
        "schema_version",
        "ledger_id",
        "event_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "event_name",
        "event_ordinal",
        "state",
        "timestamp_utc",
        "timestamp_kind",
        "authority",
        "challenge_id",
        "source_closure",
        "prior_event",
        "primary_evidence_artifact",
        "publication",
        "automatic_progression",
        "body_free",
        "event_sha256",
    }
)
_AUTHORITY_KEYS = frozenset(
    {
        "approval_kind",
        "transition_authority_token",
        "publication_authority_token",
    }
)
_SOURCE_CLOSURE_KEYS = frozenset(
    {
        "repository_full_name",
        "source_ref",
        "source_commit_sha1",
        "source_tree_sha1",
        "worktree_clean",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "requirement_registry_sha256",
        "formal_node_registry_sha256",
        "detailed_design_sha256",
    }
)
_ARTIFACT_IDENTITY_KEYS = frozenset(
    {
        "artifact_role",
        "schema_version",
        "repository_full_name",
        "path",
        "git_blob_sha1",
        "raw_sha256",
        "logical_artifact_sha256",
        "body_free",
    }
)
_PUBLISHED_EVENT_IDENTITY_KEYS = frozenset(
    {
        "identity_kind",
        "ledger_id",
        "recovery_epoch_id",
        "event_id",
        "event_name",
        "event_ordinal",
        "state",
        "timestamp_utc",
        "event_path",
        "event_git_blob_sha1",
        "event_raw_sha256",
        "event_sha256",
        "publication_commit_sha1",
        "identity_sha256",
    }
)
_P0_KEYS = frozenset(
    {
        "identity_kind",
        "event_name",
        "event_ordinal",
        "state",
        "recovery_epoch_id",
        "original_authority",
        "timestamp_utc",
        "document_path",
        "document_publication_commit_sha1",
        "document_git_blob_sha1",
        "document_raw_sha256",
        "receipt_path",
        "receipt_publication_commit_sha1",
        "receipt_git_blob_sha1",
        "receipt_raw_sha256",
        "anchor_publication_commit_sha1",
        "identity_sha256",
    }
)
_PUBLICATION_KEYS = frozenset(
    {
        "repository_full_name",
        "branch",
        "base_commit_sha1",
        "event_path",
        "supporting_artifact_count",
        "supporting_artifacts",
        "supporting_artifact_set_sha256",
        "expected_changed_path_count",
        "ref_update_mode",
        "publication_state",
    }
)
_SOURCE_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "baseline_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "lock_authority_token",
        "lock_challenge_id",
        "source_closure",
        "prior_anchor",
        "automatic_progression",
        "body_free",
        "source_baseline_closure_receipt_sha256",
    }
)
_RESERVATION_KEYS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "authority_challenge_id",
        "authority_token",
        "challenge_id",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "source_closure",
        "formal_node_registry_sha256",
        "reserved_at_utc",
        "reservation_state",
        "automatic_progression",
        "body_free",
        "formal_test_run_reservation_sha256",
    }
)
_RESERVATION_IDENTITY_KEYS = frozenset(
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


def _body_free(value: Any, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is str:
        return (
            0 < len(value) <= 4096
            and not any(ord(character) < 32 for character in value)
        )
    if type(value) not in (list, dict):
        return False
    seen = set() if active is None else active
    marker = id(value)
    if marker in seen:
        return False
    seen.add(marker)
    try:
        if type(value) is list:
            return all(_body_free(item, seen) for item in value)
        for key, item in value.items():
            if type(key) is not str or any(
                token in key.lower()
                for token in (
                    "raw_body",
                    "candidate_body",
                    "prompt_text",
                    "response_text",
                    "user_text",
                    "stdout",
                    "stderr",
                    "traceback",
                )
            ):
                return False
            if not _body_free(item, seen):
                return False
        return True
    finally:
        seen.remove(marker)


def _material(value: Mapping[str, Any], hash_key: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != hash_key}


def _published_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(prefix + raw).hexdigest()


def _utc(value: Any) -> datetime | None:
    if type(value) is not str or _UTC_RE.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return None
    return parsed.replace(tzinfo=timezone.utc)


def _identity_valid(value: Any, keys: frozenset[str]) -> bool:
    if type(value) is not dict or set(value) != keys:
        return False
    if "identity_sha256" not in keys:
        return _body_free(value)
    try:
        return (
            value.get("identity_sha256")
            == artifact_sha256(_material(value, "identity_sha256"))
            and _body_free(value)
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        return False


def _p0_anchor() -> dict[str, Any]:
    value: dict[str, Any] = {
        "identity_kind": "LEGACY_IMMUTABLE_P0_ANCHOR",
        "event_name": "PARENT_ADDENDUM_FROZEN",
        "event_ordinal": 0,
        "state": "DEFINED_NOT_STARTED",
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "original_authority": (
            "NLS_V3_STEP11_CYCLE001_PROCESS_NONCONFORMANCE_CANONICAL_"
            "RECOVERY_EPOCH_PARENT_DESIGN_ADDENDUM_READ_ONLY"
        ),
        "timestamp_utc": "2026-07-22T22:37:07Z",
        "document_path": _P0_DOCUMENT_PATH,
        "document_publication_commit_sha1": _P0_DOCUMENT_COMMIT,
        "document_git_blob_sha1": _P0_DOCUMENT_BLOB,
        "document_raw_sha256": _P0_DOCUMENT_RAW_SHA256,
        "receipt_path": _P0_RECEIPT_PATH,
        "receipt_publication_commit_sha1": _P0_RECEIPT_COMMIT,
        "receipt_git_blob_sha1": _P0_RECEIPT_BLOB,
        "receipt_raw_sha256": _P0_RECEIPT_RAW_SHA256,
        "anchor_publication_commit_sha1": _P0_RECEIPT_COMMIT,
        "identity_sha256": "",
    }
    value["identity_sha256"] = artifact_sha256(
        _material(value, "identity_sha256")
    )
    return value


def _is_ancestor(
    snapshot: Mapping[str, Any],
    ancestor: str,
    descendant: str,
) -> bool:
    commits = snapshot.get("commits", {})
    pending = [descendant]
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current == ancestor:
            return True
        if current in seen:
            continue
        seen.add(current)
        row = commits.get(current)
        if type(row) is dict:
            parents = row.get("parent_commit_sha1s")
            if type(parents) is list:
                pending.extend(
                    parent for parent in parents if type(parent) is str
                )
    return False


def _artifact_identity(
    *,
    value: Mapping[str, Any],
    path: str,
    role: str,
    schema: str,
    hash_key: str,
) -> dict[str, Any]:
    raw = _published_bytes(value)
    return {
        "artifact_role": role,
        "schema_version": schema,
        "repository_full_name": "MassyuRed/Cocolon",
        "path": path,
        "git_blob_sha1": _blob_sha1(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "logical_artifact_sha256": value[hash_key],
        "body_free": True,
    }


def build_recovery_epoch001_source_baseline_closure_receipt(
    *,
    source_closure: Mapping[str, Any],
    prior_anchor: Mapping[str, Any],
    authority_token: str,
    challenge_id: str,
) -> dict[str, Any]:
    closure = dict(source_closure)
    anchor = dict(prior_anchor)
    if (
        set(closure) != _SOURCE_CLOSURE_KEYS
        or anchor != _p0_anchor()
        or type(authority_token) is not str
        or not authority_token
        or _SHA_RE.fullmatch(challenge_id) is None
    ):
        raise ValueError("PRIOR_EVENT_INVALID")
    baseline_id = artifact_sha256(
        {
            "logical_cycle_id": _LOGICAL_CYCLE,
            "recovery_epoch_id": _RECOVERY_EPOCH,
            "candidate_version_id": _CANDIDATE,
            "source_closure": closure,
            "prior_anchor.identity_sha256": anchor["identity_sha256"],
        }
    )
    receipt: dict[str, Any] = {
        "schema_version": (
            RECOVERY_EPOCH001_SOURCE_BASELINE_CLOSURE_RECEIPT_SCHEMA
        ),
        "baseline_id": baseline_id,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "lock_authority_token": authority_token,
        "lock_challenge_id": challenge_id,
        "source_closure": closure,
        "prior_anchor": anchor,
        "automatic_progression": False,
        "body_free": True,
        "source_baseline_closure_receipt_sha256": "",
    }
    receipt["source_baseline_closure_receipt_sha256"] = artifact_sha256(
        _material(
            receipt, "source_baseline_closure_receipt_sha256"
        )
    )
    return receipt


def _event_common_valid(event: Mapping[str, Any]) -> str | None:
    if (
        set(event) != _EVENT_KEYS
        or event.get("schema_version")
        != RECOVERY_EPOCH001_SEQUENCE_EVENT_SCHEMA
        or event.get("ledger_id") != _LEDGER
        or event.get("logical_cycle_id") != _LOGICAL_CYCLE
        or event.get("recovery_epoch_id") != _RECOVERY_EPOCH
        or event.get("candidate_version_id") != _CANDIDATE
        or type(event.get("event_ordinal")) is not int
        or isinstance(event.get("event_ordinal"), bool)
        or type(event.get("authority")) is not dict
        or set(event["authority"]) != _AUTHORITY_KEYS
        or event["authority"].get("approval_kind")
        != "EXPLICIT_SEPARATE_APPROVAL"
        or event["authority"].get("transition_authority_token")
        != event["authority"].get("publication_authority_token")
        or type(event["authority"].get("transition_authority_token"))
        is not str
        or not event["authority"].get("transition_authority_token")
        or _SHA_RE.fullmatch(str(event.get("challenge_id", ""))) is None
        or type(event.get("source_closure")) is not dict
        or set(event["source_closure"]) != _SOURCE_CLOSURE_KEYS
        or type(event.get("publication")) is not dict
        or set(event["publication"]) != _PUBLICATION_KEYS
        or event["publication"].get("repository_full_name")
        != "MassyuRed/Cocolon"
        or event["publication"].get("branch") != "main"
        or event["publication"].get("ref_update_mode")
        != _REF_UPDATE_MODE
        or event["publication"].get("publication_state")
        != "PUBLISHED_ATOMIC"
        or event.get("timestamp_kind")
        != "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE"
        or event.get("body_free") is not True
        or not _body_free(event)
    ):
        return "EVENT_SCHEMA_INVALID"
    if (
        _utc(event.get("timestamp_utc")) is None
        or event.get("event_sha256")
        != artifact_sha256(_material(event, "event_sha256"))
    ):
        return "EVENT_TIMESTAMP_INVALID"
    return None


def _event_artifact_identity_valid(
    identity: Any,
    *,
    value: Any,
    path: str,
    role: str,
    schema: str,
    hash_key: str,
) -> bool:
    return (
        type(value) is dict
        and identity
        == _artifact_identity(
            value=value,
            path=path,
            role=role,
            schema=schema,
            hash_key=hash_key,
        )
    )


def _published_event_identity_valid(
    identity: Any,
    *,
    snapshot: Mapping[str, Any],
) -> bool:
    if not _identity_valid(identity, _PUBLISHED_EVENT_IDENTITY_KEYS):
        return False
    commit = identity["publication_commit_sha1"]
    row = snapshot.get("commits", {}).get(commit)
    if type(row) is not dict:
        return False
    tree = snapshot.get("trees", {}).get(row.get("tree_sha1"))
    blob = (
        tree.get(identity["event_path"]) if type(tree) is dict else None
    )
    raw = snapshot.get("blobs", {}).get(blob)
    if (
        blob != identity["event_git_blob_sha1"]
        or type(raw) is not bytes
        or _blob_sha1(raw) != blob
        or hashlib.sha256(raw).hexdigest()
        != identity["event_raw_sha256"]
    ):
        return False
    try:
        import json

        artifact = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return False
    return (
        type(artifact) is dict
        and artifact.get("event_sha256") == identity["event_sha256"]
        and artifact.get("event_id") == identity["event_id"]
        and artifact.get("event_name") == identity["event_name"]
        and artifact.get("event_ordinal") == identity["event_ordinal"]
        and artifact.get("state") == identity["state"]
        and artifact.get("timestamp_utc") == identity["timestamp_utc"]
        and artifact.get("ledger_id") == identity["ledger_id"]
    )


def _all11_issue(
    chain: Any,
    *,
    source_closure: Mapping[str, Any],
) -> str | None:
    if type(chain) is not dict:
        return "ALL11_INCOMPLETE"
    receipts = chain.get("receipts")
    artifacts = chain.get("receipt_artifacts")
    hashes = chain.get("receipt_sha256s")
    if (
        type(receipts) is not list
        or type(artifacts) is not list
        or type(hashes) is not list
        or len(receipts) != 11
        or len(artifacts) != 11
        or len(hashes) != 11
        or chain.get("receipt_count") != 11
        or chain.get("ordered_steps") != list(range(11))
        or [row.get("step_number") for row in receipts] != list(range(11))
        or [row.get("receipt_sha256") for row in receipts] != hashes
        or len(set(hashes)) != 11
    ):
        return "ALL11_INCOMPLETE"
    if chain.get("source_closure") != source_closure:
        return "SOURCE_OR_ROOT_DRIFT"
    previous: Mapping[str, Any] | None = None
    for step, (receipt, identity) in enumerate(zip(receipts, artifacts)):
        if type(receipt) is not dict:
            return "ALL11_INCOMPLETE"
        expected_path = (
            f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
            f"Step{step:02d}_CurrentStepCompletion_PROVED_BodyFree_"
            "Receipt_20260724.json"
        )
        if not _event_artifact_identity_valid(
            identity,
            value=receipt,
            path=expected_path,
            role="CURRENT_STEP_COMPLETION_RECEIPT",
            schema=receipt.get("schema_version"),
            hash_key="receipt_sha256",
        ):
            return "ALL11_INCOMPLETE"
        if step and receipt.get("parent_binding", {}).get(
            "previous_receipt_sha256"
        ) != previous.get("receipt_sha256"):
            return "SEQUENCE_INVALID"
        if step == 10 and (
            receipt.get("next_authority")
            != (
                "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
                "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
            )
        ):
            return "P2_NOT_AUTHORIZED"
        previous = receipt
    if (
        chain.get("next_authority")
        != (
            "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
            "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
        )
        or chain.get("automatic_progression") is not False
    ):
        return "P2_NOT_AUTHORIZED"
    return None


def validate_recovery_epoch001_sequence_transition_candidate(
    value: Any,
    *,
    evidence_artifacts_by_path: Mapping[str, Mapping[str, Any]],
    repository_snapshot: Mapping[str, Any],
) -> tuple[str, ...]:
    try:
        if type(value) is not dict:
            return ("EVENT_SCHEMA_INVALID",)
        common = _event_common_valid(value)
        if common is not None:
            return (common,)
        ordinal = value["event_ordinal"]
        if ordinal == 0:
            return ("P0_BACKFILL_FORBIDDEN",)
        timestamp = _utc(value["timestamp_utc"])
        publication = value["publication"]
        event_path = publication["event_path"]
        supporting = publication["supporting_artifacts"]
        if ordinal == 1:
            if (
                value.get("event_name") != "SOURCE_BASELINE_LOCKED"
                or value.get("state") != "SOURCE_BASELINE_LOCKED"
                or value.get("event_id")
                != (
                    "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_001_"
                    "SOURCE_BASELINE_LOCKED"
                )
                or event_path != _EVENT1_PATH
            ):
                return ("SEQUENCE_INVALID",)
            prior = value.get("prior_event")
            if (
                type(prior) is dict
                and prior.get("identity_kind")
                == "PUBLISHED_SEQUENCE_EVENT"
                and prior.get("event_ordinal") == 0
            ):
                return ("P0_BACKFILL_FORBIDDEN",)
            if prior != _p0_anchor():
                return ("PRIOR_EVENT_INVALID",)
            prior_time = _utc(prior["timestamp_utc"])
            if timestamp is None or prior_time is None or timestamp <= prior_time:
                return ("EVENT_TIMESTAMP_INVALID",)
            base = publication.get("base_commit_sha1")
            if not _is_ancestor(
                repository_snapshot, _P0_RECEIPT_COMMIT, str(base)
            ):
                return ("PRIOR_EVENT_INVALID",)
            primary = value.get("primary_evidence_artifact")
            receipt = evidence_artifacts_by_path.get(_SOURCE_RECEIPT_PATH)
            if (
                primary.get("path")
                == event_path
                if type(primary) is dict
                else True
            ):
                return ("ARTIFACT_IDENTITY_INVALID",)
            if not _event_artifact_identity_valid(
                primary,
                value=receipt,
                path=_SOURCE_RECEIPT_PATH,
                role="SOURCE_BASELINE_CLOSURE_RECEIPT",
                schema=RECOVERY_EPOCH001_SOURCE_BASELINE_CLOSURE_RECEIPT_SCHEMA,
                hash_key="source_baseline_closure_receipt_sha256",
            ):
                return ("ARTIFACT_IDENTITY_INVALID",)
            if supporting != [primary]:
                return ("ARTIFACT_IDENTITY_INVALID",)
            if (
                publication.get("supporting_artifact_count") != 1
                or publication.get("supporting_artifact_set_sha256")
                != artifact_sha256(supporting)
                or publication.get("expected_changed_path_count") != 2
            ):
                return ("EVENT_SCHEMA_INVALID",)
            return ()
        if ordinal != 2:
            return ("SEQUENCE_INVALID",)
        if (
            value.get("event_name") != "STEP0_10_PREREQUISITES_PROVED"
            or value.get("state") != "STEP0_10_PREREQUISITES_PROVED"
            or value.get("event_id")
            != (
                "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_002_"
                "STEP0_10_PREREQUISITES_PROVED"
            )
            or event_path != _EVENT2_PATH
        ):
            return ("SEQUENCE_INVALID",)
        prior = value.get("prior_event")
        if (
            not _published_event_identity_valid(
                prior, snapshot=repository_snapshot
            )
            or prior.get("event_name") != "SOURCE_BASELINE_LOCKED"
            or prior.get("event_ordinal") != 1
        ):
            return ("PRIOR_EVENT_INVALID",)
        base = publication.get("base_commit_sha1")
        if not _is_ancestor(
            repository_snapshot,
            prior["publication_commit_sha1"],
            str(base),
        ):
            return ("SEQUENCE_INVALID",)
        chain_candidates = [
            item
            for item in evidence_artifacts_by_path.values()
            if type(item) is dict
            and item.get("schema_version", "").endswith(
                "all11_completion_chain.v2"
            )
        ]
        chain = chain_candidates[0] if len(chain_candidates) == 1 else None
        chain_issue = _all11_issue(
            chain, source_closure=value["source_closure"]
        )
        if chain_issue is not None:
            return (chain_issue,)
        run_finished = _utc(
            next(
                (
                    item.get("formal_test_run_attempt", {}).get(
                        "run_finished_at_utc"
                    )
                    for item in evidence_artifacts_by_path.values()
                    if type(item) is dict
                    and item.get("schema_version", "").endswith(
                        "accepted_test_run_receipt.v2"
                    )
                ),
                None,
            )
        )
        if (
            timestamp is None
            or _utc(prior["timestamp_utc"]) is None
            or timestamp <= _utc(prior["timestamp_utc"])
            or run_finished is None
            or timestamp <= run_finished
        ):
            return ("EVENT_TIMESTAMP_INVALID",)
        if value.get("automatic_progression") is not False:
            return ("P2_NOT_AUTHORIZED",)
        primary = value.get("primary_evidence_artifact")
        chain_path = (
            f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
            "All11CompletionChain_BodyFree_Chain_20260724.json"
        )
        if not _event_artifact_identity_valid(
            primary,
            value=chain,
            path=chain_path,
            role="ALL11_COMPLETION_CHAIN",
            schema=chain.get("schema_version"),
            hash_key="all11_completion_chain_sha256",
        ):
            return ("ARTIFACT_IDENTITY_INVALID",)
        if (
            publication.get("supporting_artifact_count") != 14
            or len(supporting) != 14
            or supporting != sorted(supporting, key=lambda row: row["path"])
            or len({row["path"] for row in supporting}) != 14
            or publication.get("supporting_artifact_set_sha256")
            != artifact_sha256(supporting)
            or publication.get("expected_changed_path_count") != 15
        ):
            return ("ARTIFACT_IDENTITY_INVALID",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("EVENT_SCHEMA_INVALID",)


def validate_recovery_epoch001_owner_verifier_agreement(
    *,
    owner_issues: Any,
    verifier_issues: Any,
) -> tuple[str, ...]:
    owner = tuple(owner_issues) if type(owner_issues) in (tuple, list) else ()
    verifier = (
        tuple(verifier_issues)
        if type(verifier_issues) in (tuple, list)
        else ()
    )
    return () if owner == verifier else ("OWNER_VERIFIER_CONFLICT",)


def build_recovery_epoch001_sequence_event_1(
    *,
    source_baseline_closure_receipt: Mapping[str, Any],
    source_baseline_closure_receipt_identity: Mapping[str, Any],
    supporting_set: Mapping[str, Any],
    prior_anchor: Mapping[str, Any],
    publication: Mapping[str, Any],
    clock_utc: Callable[[], str],
) -> dict[str, Any]:
    receipt = dict(source_baseline_closure_receipt)
    identity = dict(source_baseline_closure_receipt_identity)
    prior = dict(prior_anchor)
    timestamp = clock_utc()
    event: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH001_SEQUENCE_EVENT_SCHEMA,
        "ledger_id": _LEDGER,
        "event_id": (
            "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_001_"
            "SOURCE_BASELINE_LOCKED"
        ),
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "event_name": "SOURCE_BASELINE_LOCKED",
        "event_ordinal": 1,
        "state": "SOURCE_BASELINE_LOCKED",
        "timestamp_utc": timestamp,
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": receipt["lock_authority_token"],
            "publication_authority_token": receipt["lock_authority_token"],
        },
        "challenge_id": receipt["lock_challenge_id"],
        "source_closure": deepcopy(receipt["source_closure"]),
        "prior_event": prior,
        "primary_evidence_artifact": identity,
        "publication": dict(publication),
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
    }
    event["event_sha256"] = artifact_sha256(
        _material(event, "event_sha256")
    )
    if (
        supporting_set.get("supporting_artifacts") != [identity]
        or event["publication"].get("supporting_artifacts") != [identity]
        or _utc(timestamp) is None
        or _utc(timestamp) <= _utc(prior["timestamp_utc"])
    ):
        raise ValueError("EVENT_SCHEMA_INVALID")
    return event


def build_recovery_epoch001_sequence_event_2(
    *,
    published_event1_identity: Mapping[str, Any],
    source_closure: Mapping[str, Any],
    all11_completion_chain: Mapping[str, Any],
    all11_completion_chain_identity: Mapping[str, Any],
    supporting_set: Mapping[str, Any],
    supporting_artifacts: list[Mapping[str, Any]],
    authority_token: str,
    challenge_id: str,
    publication: Mapping[str, Any],
    formal_test_run_evidence: Mapping[str, Any],
    evidence_artifacts_by_path: Mapping[str, Mapping[str, Any]],
    repository_snapshot: Mapping[str, Any],
    clock_utc: Callable[[], str],
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH001_SEQUENCE_EVENT_SCHEMA,
        "ledger_id": _LEDGER,
        "event_id": (
            "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_002_"
            "STEP0_10_PREREQUISITES_PROVED"
        ),
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "candidate_version_id": _CANDIDATE,
        "event_name": "STEP0_10_PREREQUISITES_PROVED",
        "event_ordinal": 2,
        "state": "STEP0_10_PREREQUISITES_PROVED",
        "timestamp_utc": clock_utc(),
        "timestamp_kind": "ORCHESTRATOR_UTC_BEFORE_REF_UPDATE",
        "authority": {
            "approval_kind": "EXPLICIT_SEPARATE_APPROVAL",
            "transition_authority_token": authority_token,
            "publication_authority_token": authority_token,
        },
        "challenge_id": challenge_id,
        "source_closure": dict(source_closure),
        "prior_event": dict(published_event1_identity),
        "primary_evidence_artifact": dict(
            all11_completion_chain_identity
        ),
        "publication": dict(publication),
        "automatic_progression": False,
        "body_free": True,
        "event_sha256": "",
    }
    event["event_sha256"] = artifact_sha256(
        _material(event, "event_sha256")
    )
    owner_issues = validate_recovery_epoch001_sequence_transition_candidate(
        event,
        evidence_artifacts_by_path=evidence_artifacts_by_path,
        repository_snapshot=repository_snapshot,
    )
    verifier_issues = RECOVERY_EPOCH001_INDEPENDENT_SEQUENCE_VERIFIER(
        event,
        evidence_artifacts_by_path=evidence_artifacts_by_path,
        repository_snapshot=repository_snapshot,
    )
    agreement = validate_recovery_epoch001_owner_verifier_agreement(
        owner_issues=owner_issues,
        verifier_issues=verifier_issues,
    )
    if agreement:
        raise ValueError(agreement[0])
    if owner_issues:
        raise ValueError(owner_issues[0])
    if (
        dict(all11_completion_chain)
        != evidence_artifacts_by_path.get(
            all11_completion_chain_identity["path"]
        )
        or list(supporting_artifacts)
        != event["publication"]["supporting_artifacts"]
        or supporting_set.get("supporting_artifacts")
        != event["publication"]["supporting_artifacts"]
        or type(formal_test_run_evidence) is not dict
    ):
        raise ValueError("ALL11_INCOMPLETE")
    return event


def build_recovery_epoch001_formal_test_run_reservation(
    *,
    authority_token: str,
    challenge_id: str,
    source_baseline_event_identity: Mapping[str, Any],
    source_baseline_event_artifact: Mapping[str, Any],
    source_closure: Mapping[str, Any],
    formal_node_registry_sha256: str,
    clock_utc: Callable[[], str],
) -> dict[str, Any]:
    event_identity = dict(source_baseline_event_identity)
    event = dict(source_baseline_event_artifact)
    closure = dict(source_closure)
    reserved_at = clock_utc()
    event_time = _utc(event_identity.get("timestamp_utc"))
    if (
        not _identity_valid(
            event_identity, _PUBLISHED_EVENT_IDENTITY_KEYS
        )
        or event.get("event_sha256") != event_identity.get("event_sha256")
        or event.get("challenge_id") == challenge_id
        or event_time is None
        or _utc(reserved_at) is None
        or _utc(reserved_at) <= event_time
        or set(closure) != _SOURCE_CLOSURE_KEYS
        or closure.get("formal_node_registry_sha256")
        != formal_node_registry_sha256
    ):
        raise ValueError("RUN_RESERVATION_INVALID")
    authority_challenge_id = artifact_sha256(
        {
            "authority_token": authority_token,
            "challenge_id": challenge_id,
        }
    )
    attempt_id = artifact_sha256(
        {
            "authority_token": authority_token,
            "challenge_id": challenge_id,
            "source_baseline_event.event_sha256": (
                event_identity["event_sha256"]
            ),
            "source_closure.source_commit_sha1": (
                closure["source_commit_sha1"]
            ),
            "formal_node_registry_sha256": formal_node_registry_sha256,
        }
    )
    reservation: dict[str, Any] = {
        "schema_version": (
            RECOVERY_EPOCH001_FORMAL_TEST_RUN_RESERVATION_SCHEMA
        ),
        "attempt_id": attempt_id,
        "authority_challenge_id": authority_challenge_id,
        "authority_token": authority_token,
        "challenge_id": challenge_id,
        "candidate_version_id": _CANDIDATE,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "source_baseline_event": event_identity,
        "source_closure": closure,
        "formal_node_registry_sha256": formal_node_registry_sha256,
        "reserved_at_utc": reserved_at,
        "reservation_state": "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN",
        "automatic_progression": False,
        "body_free": True,
        "formal_test_run_reservation_sha256": "",
    }
    reservation["formal_test_run_reservation_sha256"] = artifact_sha256(
        _material(
            reservation, "formal_test_run_reservation_sha256"
        )
    )
    if validate_recovery_epoch001_formal_test_run_reservation_shape(
        reservation
    ):
        raise ValueError("RUN_RESERVATION_INVALID")
    return reservation


def validate_recovery_epoch001_formal_test_run_reservation_shape(
    value: Any,
) -> tuple[str, ...]:
    try:
        if type(value) is not dict or set(value) != _RESERVATION_KEYS:
            return ("RUN_RESERVATION_INVALID",)
        if (
            value.get("schema_version")
            != RECOVERY_EPOCH001_FORMAL_TEST_RUN_RESERVATION_SCHEMA
            or value.get("candidate_version_id") != _CANDIDATE
            or value.get("logical_cycle_id") != _LOGICAL_CYCLE
            or value.get("recovery_epoch_id") != _RECOVERY_EPOCH
            or _SHA_RE.fullmatch(str(value.get("attempt_id", ""))) is None
            or _SHA_RE.fullmatch(
                str(value.get("authority_challenge_id", ""))
            )
            is None
            or _SHA_RE.fullmatch(str(value.get("challenge_id", ""))) is None
            or not _identity_valid(
                value.get("source_baseline_event"),
                _PUBLISHED_EVENT_IDENTITY_KEYS,
            )
            or type(value.get("source_closure")) is not dict
            or set(value["source_closure"]) != _SOURCE_CLOSURE_KEYS
            or value.get("formal_node_registry_sha256")
            != value["source_closure"].get(
                "formal_node_registry_sha256"
            )
            or _utc(value.get("reserved_at_utc")) is None
            or value.get("reservation_state")
            != "ONE_SHOT_AUTHORITY_CONSUMED_BEFORE_RUN"
            or value.get("automatic_progression") is not False
            or value.get("body_free") is not True
            or not _body_free(value)
            or value.get("authority_challenge_id")
            != artifact_sha256(
                {
                    "authority_token": value.get("authority_token"),
                    "challenge_id": value.get("challenge_id"),
                }
            )
            or value.get("attempt_id")
            != artifact_sha256(
                {
                    "authority_token": value.get("authority_token"),
                    "challenge_id": value.get("challenge_id"),
                    "source_baseline_event.event_sha256": value[
                        "source_baseline_event"
                    ]["event_sha256"],
                    "source_closure.source_commit_sha1": value[
                        "source_closure"
                    ]["source_commit_sha1"],
                    "formal_node_registry_sha256": value[
                        "formal_node_registry_sha256"
                    ],
                }
            )
            or value.get("formal_test_run_reservation_sha256")
            != artifact_sha256(
                _material(
                    value, "formal_test_run_reservation_sha256"
                )
            )
        ):
            return ("RUN_RESERVATION_INVALID",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RUN_RESERVATION_INVALID",)


def _reservation_record_valid(
    record: Any,
    *,
    repository_snapshot: Mapping[str, Any],
    source_baseline_event_artifact: Mapping[str, Any],
) -> bool:
    if (
        type(record) is not dict
        or set(record) != {"artifact", "identity", "raw_bytes", "publication"}
    ):
        return False
    artifact = record["artifact"]
    identity = record["identity"]
    raw = record["raw_bytes"]
    publication = record["publication"]
    if (
        validate_recovery_epoch001_formal_test_run_reservation_shape(
            artifact
        )
        or not _identity_valid(identity, _RESERVATION_IDENTITY_KEYS)
        or type(raw) is not bytes
        or _published_bytes(artifact) != raw
        or identity.get("artifact_role") != "FORMAL_TEST_RUN_RESERVATION"
        or identity.get("schema_version")
        != RECOVERY_EPOCH001_FORMAL_TEST_RUN_RESERVATION_SCHEMA
        or identity.get("repository_full_name") != "MassyuRed/Cocolon"
        or identity.get("path")
        != (
            f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
            f"Attempt_{artifact['attempt_id']}_"
            "FormalTestRunReservation_BodyFree_Receipt_20260724.json"
        )
        or identity.get("git_blob_sha1") != _blob_sha1(raw)
        or identity.get("raw_sha256") != hashlib.sha256(raw).hexdigest()
        or identity.get("logical_artifact_sha256")
        != artifact.get("formal_test_run_reservation_sha256")
        or type(publication) is not dict
        or publication.get("postverified") is not True
        or publication.get("publication_commit_sha1")
        != identity.get("publication_commit_sha1")
        or publication.get("parent_commit_sha1s")
        != [
            artifact["source_baseline_event"][
                "publication_commit_sha1"
            ]
        ]
        or publication.get("changed_paths") != [identity.get("path")]
        or artifact["source_baseline_event"].get("event_sha256")
        != source_baseline_event_artifact.get("event_sha256")
        or artifact.get("challenge_id")
        == source_baseline_event_artifact.get("challenge_id")
        or _utc(artifact.get("reserved_at_utc"))
        <= _utc(artifact["source_baseline_event"].get("timestamp_utc"))
    ):
        return False
    commit = identity["publication_commit_sha1"]
    event_commit = artifact["source_baseline_event"][
        "publication_commit_sha1"
    ]
    return (
        repository_snapshot.get("parents_by_commit", {}).get(commit)
        == [event_commit]
        and repository_snapshot.get("path_blob_by_commit", {})
        .get(commit, {})
        .get(identity["path"])
        == identity["git_blob_sha1"]
    )


def validate_recovery_epoch001_formal_test_run_reservation_admission(
    candidate_record: Mapping[str, Any] | None,
    *,
    published_reservations: list[Mapping[str, Any]],
    published_attempts: list[Mapping[str, Any]],
    repository_snapshot: Mapping[str, Any],
    source_baseline_event_artifact: Mapping[str, Any],
    rerun_requested: bool,
) -> tuple[str, ...]:
    try:
        artifact = (
            candidate_record.get("artifact")
            if type(candidate_record) is dict
            else None
        )
        authority = (
            artifact.get("authority_token")
            if type(artifact) is dict
            else None
        )
        attempts = [
            row
            for row in published_attempts
            if type(row) is dict
            and type(row.get("artifact")) is dict
            and row["artifact"].get("authority_token") == authority
        ]
        reservations = [
            row
            for row in published_reservations
            if type(row) is dict
            and type(row.get("artifact")) is dict
            and row["artifact"].get("authority_token") == authority
        ]
        if attempts:
            return ("RUN_ATTEMPT_REPLAY",)
        if reservations:
            same = any(
                row.get("artifact", {}).get("attempt_id")
                == artifact.get("attempt_id")
                for row in reservations
            )
            if same and rerun_requested:
                return ("ATTEMPT_CONSUMPTION_UNKNOWN_STOP",)
            return ("RUN_ATTEMPT_REPLAY",)
        if not _reservation_record_valid(
            candidate_record,
            repository_snapshot=repository_snapshot,
            source_baseline_event_artifact=source_baseline_event_artifact,
        ):
            return ("RUN_RESERVATION_INVALID",)
        if rerun_requested:
            return ("RUN_ATTEMPT_REPLAY",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RUN_RESERVATION_INVALID",)
