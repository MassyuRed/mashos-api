#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build the inert Recovery Epoch 001 all11 atomic-publication candidate."""

import hashlib
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"
for _path in (str(_INFERENCE_ROOT), str(_TOOLS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3 import (
    validate_recovery_epoch001_accepted_test_run_receipt_shape,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    validate_recovery_epoch001_current_step_requirement_registry_shape,
)
from emlis_ai_recovery_epoch001_step_completion_receipt_v3 import (
    build_recovery_epoch001_current_step_completion_receipt,
    validate_recovery_epoch001_current_step_completion_receipt_shape,
)
import emlis_nls_v3_recovery_epoch001_closure_receipt_verify as independent


RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.all11_completion_chain.v2"
)
RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_NEGATIVE_CODES = frozenset(
    {
        "ALL11_INCOMPLETE",
        "RECEIPT_ORDER_INVALID",
        "SOURCE_OR_ROOT_MISMATCH",
        "PARENT_CHAIN_INVALID",
        "STOP_TRIGGERED",
        "NEXT_AUTHORITY_INVALID",
        "OWNER_VERIFIER_CONFLICT",
        "SEQUENCE_INVALID",
        "PUBLICATION_CONFLICT",
        "P2_NOT_AUTHORIZED",
        "BODY_FREE_VIOLATION",
        "HASH_MISMATCH",
        "ACCEPTED_RECEIPT_NOT_ISSUABLE",
    }
)

_CANDIDATE = "nls_v3_rc_0034"
_LOGICAL_CYCLE = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH = "NLS_V3_CYCLE001_RECOVERY_EPOCH_001"
_REPOSITORY = "MassyuRed/Cocolon"
_PREFIX = "EmlisAIの実装済み資料/documents/"
_ACCEPTED_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "AcceptedTestRunExact134_BodyFree_Receipt_20260724.json"
)
_STEP_PATHS = tuple(
    (
        f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
        f"Step{step:02d}_CurrentStepCompletion_PROVED_BodyFree_"
        "Receipt_20260724.json"
    )
    for step in range(11)
)
_ACCEPTED_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "accepted_test_run_receipt.v2"
)
_STEP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_completion_receipt.v1"
)
_STEP10_NEXT_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
    "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
)
_TOP_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "source_closure",
        "registry_sha256",
        "formal_node_registry_sha256",
        "accepted_test_run_artifact",
        "accepted_test_run_receipt_sha256",
        "receipt_count",
        "ordered_steps",
        "receipts",
        "receipt_artifacts",
        "receipt_sha256s",
        "required_sequence_event_2",
        "next_authority",
        "publication_state",
        "automatic_progression",
        "body_free",
        "all11_completion_chain_sha256",
    }
)
_IDENTITY_KEYS = frozenset(
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
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:+-]{1,512}$")


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
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    try:
        if type(value) is list:
            return all(_body_free(item, seen) for item in value)
        return all(
            type(key) is str
            and not any(
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
                    "environment_dump",
                )
            )
            and _body_free(item, seen)
            for key, item in value.items()
        )
    finally:
        seen.remove(identity)


def _material(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: item
        for key, item in value.items()
        if key != "all11_completion_chain_sha256"
    }


def _published_bytes(value: Mapping[str, Any]) -> bytes:
    return canonical_json_bytes(value) + b"\n"


def _git_blob_sha1(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(
        prefix + raw,
        usedforsecurity=False,
    ).hexdigest()


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
        "repository_full_name": _REPOSITORY,
        "path": path,
        "git_blob_sha1": _git_blob_sha1(raw),
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "logical_artifact_sha256": value[hash_key],
        "body_free": True,
    }


def _attempt(
    accepted: Mapping[str, Any],
) -> Mapping[str, Any]:
    value = accepted.get("formal_test_run_attempt")
    return value if type(value) is dict else {}


def _accepted_valid(
    accepted: Mapping[str, Any],
    *,
    registry: Mapping[str, Any],
    source_event: Mapping[str, Any],
    publication_evidence: Mapping[str, Any],
    root: Path,
) -> bool:
    return not validate_recovery_epoch001_accepted_test_run_receipt_shape(
        accepted,
        requirement_registry=registry,
        source_baseline_event=source_event,
        publication_evidence=publication_evidence,
        repo_root=root,
    )


def stage_recovery_epoch001_all11_current_step_completion_receipts(
    *,
    requirement_registry: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
    source_baseline_event: Mapping[str, Any],
    publication_evidence: Mapping[str, Any],
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return exact11 only after owner and independent checks all agree."""

    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    accepted = dict(accepted_test_run_receipt)
    event = dict(source_baseline_event)
    evidence = dict(publication_evidence)
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=root,
    ):
        raise ValueError("ALL11_INCOMPLETE")
    if not _accepted_valid(
        accepted,
        registry=registry,
        source_event=event,
        publication_evidence=evidence,
        root=root,
    ):
        raise ValueError("ACCEPTED_RECEIPT_NOT_ISSUABLE")
    if independent.verify_recovery_epoch001_accepted_test_run_receipt(
        accepted,
        repo_root=root,
        requirement_registry=registry,
        source_baseline_event=event,
        publication_evidence=evidence,
    ):
        raise ValueError("OWNER_VERIFIER_CONFLICT")
    staged: list[dict[str, Any]] = []
    for step in range(11):
        previous = staged[-1] if staged else None
        receipt = build_recovery_epoch001_current_step_completion_receipt(
            step_number=step,
            requirement_registry=registry,
            accepted_test_run_receipt=accepted,
            repo_root=root,
            previous_receipt=previous,
            step0_parent_authority=event,
            prior_receipts=tuple(staged),
            publication_evidence=evidence,
        )
        owner_issues = (
            validate_recovery_epoch001_current_step_completion_receipt_shape(
                receipt,
                repo_root=root,
                previous_receipt=previous,
                step0_parent_authority=event,
                requirement_registry=registry,
                accepted_test_run_receipt=accepted,
                prior_receipts=tuple(staged),
                publication_evidence=evidence,
            )
        )
        verifier_issues = (
            independent.verify_recovery_epoch001_current_step_completion_receipt(
                receipt,
                repo_root=root,
                previous_receipt=previous,
                step0_parent_authority=event,
                requirement_registry=registry,
                accepted_test_run_receipt=accepted,
                prior_receipts=tuple(staged),
                publication_evidence=evidence,
            )
        )
        if owner_issues or verifier_issues:
            raise ValueError("OWNER_VERIFIER_CONFLICT")
        staged.append(receipt)
    return tuple(staged)


def build_recovery_epoch001_all11_completion_chain(
    *,
    receipts: Sequence[Mapping[str, Any]],
    requirement_registry: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
    source_baseline_event: Mapping[str, Any],
    publication_evidence: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build the exact11 v2 candidate; this function performs no write."""

    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    accepted = dict(accepted_test_run_receipt)
    event = dict(source_baseline_event)
    evidence = dict(publication_evidence)
    receipt_rows = [
        dict(receipt) for receipt in receipts if type(receipt) is dict
    ]
    if len(receipt_rows) != 11:
        raise ValueError("ALL11_INCOMPLETE")
    if not _accepted_valid(
        accepted,
        registry=registry,
        source_event=event,
        publication_evidence=evidence,
        root=root,
    ):
        raise ValueError("ACCEPTED_RECEIPT_NOT_ISSUABLE")
    attempt = _attempt(accepted)
    source_closure = attempt.get("source_closure")
    event_identity = attempt.get("source_baseline_event")
    if (
        type(source_closure) is not dict
        or type(event_identity) is not dict
    ):
        raise ValueError("SOURCE_OR_ROOT_MISMATCH")
    accepted_identity = _artifact_identity(
        value=accepted,
        path=_ACCEPTED_PATH,
        role="ACCEPTED_TEST_RUN_RECEIPT",
        schema=_ACCEPTED_SCHEMA,
        hash_key="accepted_test_run_receipt_sha256",
    )
    receipt_identities = [
        _artifact_identity(
            value=receipt,
            path=_STEP_PATHS[step],
            role="CURRENT_STEP_COMPLETION_RECEIPT",
            schema=_STEP_SCHEMA,
            hash_key="receipt_sha256",
        )
        for step, receipt in enumerate(receipt_rows)
    ]
    chain: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA,
        "candidate_version_id": _CANDIDATE,
        "logical_cycle_id": _LOGICAL_CYCLE,
        "recovery_epoch_id": _RECOVERY_EPOCH,
        "source_baseline_event": dict(event_identity),
        "source_closure": dict(source_closure),
        "registry_sha256": registry["registry_sha256"],
        "formal_node_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "accepted_test_run_artifact": accepted_identity,
        "accepted_test_run_receipt_sha256": accepted[
            "accepted_test_run_receipt_sha256"
        ],
        "receipt_count": 11,
        "ordered_steps": list(range(11)),
        "receipts": receipt_rows,
        "receipt_artifacts": receipt_identities,
        "receipt_sha256s": [
            receipt["receipt_sha256"] for receipt in receipt_rows
        ],
        "required_sequence_event_2": {
            "event_id": (
                "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_002_"
                "STEP0_10_PREREQUISITES_PROVED"
            ),
            "event_name": "STEP0_10_PREREQUISITES_PROVED",
            "event_ordinal": 2,
            "state": "STEP0_10_PREREQUISITES_PROVED",
            "prior_event_identity_sha256": event_identity[
                "identity_sha256"
            ],
        },
        "next_authority": _STEP10_NEXT_AUTHORITY,
        "publication_state": "PUBLISHED_ATOMIC",
        "automatic_progression": False,
        "body_free": True,
    }
    chain["all11_completion_chain_sha256"] = artifact_sha256(
        _material(chain)
    )
    issues = validate_recovery_epoch001_all11_completion_chain(
        chain,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        source_baseline_event=event,
        publication_evidence=evidence,
        repo_root=root,
    )
    if issues:
        raise ValueError(issues[0])
    verifier_issues = independent.verify_recovery_epoch001_all11_completion_chain(
        chain,
        repo_root=root,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        source_baseline_event=event,
        publication_evidence=evidence,
    )
    if verifier_issues:
        raise ValueError("OWNER_VERIFIER_CONFLICT")
    return chain


def validate_recovery_epoch001_all11_completion_chain(
    value: Any,
    *,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
    publication_evidence: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    try:
        if type(value) is not dict or set(value) != _TOP_KEYS:
            return ("ALL11_INCOMPLETE",)
        root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
        registry = (
            dict(requirement_registry)
            if type(requirement_registry) is dict
            else {}
        )
        accepted = (
            dict(accepted_test_run_receipt)
            if type(accepted_test_run_receipt) is dict
            else {}
        )
        event = (
            dict(source_baseline_event)
            if type(source_baseline_event) is dict
            else {}
        )
        evidence = (
            dict(publication_evidence)
            if type(publication_evidence) is dict
            else {}
        )
        if (
            value.get("schema_version")
            != RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA
            or value.get("candidate_version_id") != _CANDIDATE
            or value.get("logical_cycle_id") != _LOGICAL_CYCLE
            or value.get("recovery_epoch_id") != _RECOVERY_EPOCH
        ):
            return ("ALL11_INCOMPLETE",)
        if not _accepted_valid(
            accepted,
            registry=registry,
            source_event=event,
            publication_evidence=evidence,
            root=root,
        ):
            return ("ACCEPTED_RECEIPT_NOT_ISSUABLE",)
        attempt = _attempt(accepted)
        if (
            value.get("source_baseline_event")
            != attempt.get("source_baseline_event")
            or value.get("source_closure") != attempt.get("source_closure")
            or value.get("registry_sha256")
            != registry.get("registry_sha256")
            or value.get("formal_node_registry_sha256")
            != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ):
            return ("SOURCE_OR_ROOT_MISMATCH",)
        receipts = value.get("receipts")
        artifacts = value.get("receipt_artifacts")
        hashes = value.get("receipt_sha256s")
        if (
            type(receipts) is not list
            or type(artifacts) is not list
            or type(hashes) is not list
            or len(receipts) != 11
            or len(artifacts) != 11
            or len(hashes) != 11
            or value.get("receipt_count") != 11
            or value.get("ordered_steps") != list(range(11))
            or [row.get("step_number") for row in receipts]
            != list(range(11))
            or [row.get("receipt_sha256") for row in receipts] != hashes
        ):
            return ("ALL11_INCOMPLETE",)
        previous: Mapping[str, Any] | None = None
        for step, (receipt, identity) in enumerate(
            zip(receipts, artifacts)
        ):
            if (
                type(receipt) is not dict
                or type(identity) is not dict
                or set(identity) != _IDENTITY_KEYS
                or identity
                != _artifact_identity(
                    value=receipt,
                    path=_STEP_PATHS[step],
                    role="CURRENT_STEP_COMPLETION_RECEIPT",
                    schema=_STEP_SCHEMA,
                    hash_key="receipt_sha256",
                )
            ):
                return ("ALL11_INCOMPLETE",)
            if step and receipt.get("parent_binding", {}).get(
                "previous_receipt_sha256"
            ) != previous.get("receipt_sha256"):
                return ("PARENT_CHAIN_INVALID",)
            if receipt.get("verdict") != "PROVED":
                return ("ALL11_INCOMPLETE",)
            previous = receipt
        expected_accepted_identity = _artifact_identity(
            value=accepted,
            path=_ACCEPTED_PATH,
            role="ACCEPTED_TEST_RUN_RECEIPT",
            schema=_ACCEPTED_SCHEMA,
            hash_key="accepted_test_run_receipt_sha256",
        )
        if (
            value.get("accepted_test_run_artifact")
            != expected_accepted_identity
            or value.get("accepted_test_run_receipt_sha256")
            != accepted.get("accepted_test_run_receipt_sha256")
        ):
            return ("SOURCE_OR_ROOT_MISMATCH",)
        event_identity = attempt["source_baseline_event"]
        if value.get("required_sequence_event_2") != {
            "event_id": (
                "NLS_V3_CYCLE001_RECOVERY_EPOCH001_EVENT_002_"
                "STEP0_10_PREREQUISITES_PROVED"
            ),
            "event_name": "STEP0_10_PREREQUISITES_PROVED",
            "event_ordinal": 2,
            "state": "STEP0_10_PREREQUISITES_PROVED",
            "prior_event_identity_sha256": event_identity[
                "identity_sha256"
            ],
        }:
            return ("SEQUENCE_INVALID",)
        if (
            value.get("next_authority") != _STEP10_NEXT_AUTHORITY
            or value.get("automatic_progression") is not False
        ):
            return ("P2_NOT_AUTHORIZED",)
        if value.get("publication_state") != "PUBLISHED_ATOMIC":
            return ("PUBLICATION_CONFLICT",)
        if value.get("body_free") is not True or not _body_free(value):
            return ("BODY_FREE_VIOLATION",)
        if (
            value.get("all11_completion_chain_sha256")
            != artifact_sha256(_material(value))
            or _SHA_RE.fullmatch(
                str(value.get("all11_completion_chain_sha256", ""))
            )
            is None
        ):
            return ("HASH_MISMATCH",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("ALL11_INCOMPLETE",)


if __name__ == "__main__":
    raise SystemExit("inert candidate builder; publication remains separate")
