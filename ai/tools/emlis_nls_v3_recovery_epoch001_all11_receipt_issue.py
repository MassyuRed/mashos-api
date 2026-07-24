#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Atomically stage, but never publish, Recovery Epoch 001 all11 receipts.

This tool has no filesystem or GitHub write path.  It builds all eleven
PROVED candidates in memory, requires owner and independent-verifier
agreement for every item, and returns nothing partial on failure.
"""

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

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3 import (
    RECOVERY_EPOCH001_SEQUENCE_EVENT_2,
    RECOVERY_EPOCH001_SEQUENCE_EVENT_2_ORDINAL,
    validate_recovery_epoch001_accepted_test_run_receipt_shape,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    fresh_recovery_epoch001_current_step_requirement_registry,
    validate_recovery_epoch001_current_step_requirement_registry_shape,
)
from emlis_ai_recovery_epoch001_step_completion_receipt_v3 import (
    build_recovery_epoch001_current_step_completion_receipt,
    validate_recovery_epoch001_current_step_completion_receipt_shape,
)
import emlis_nls_v3_recovery_epoch001_closure_receipt_verify as independent


RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.all11_completion_chain.v1"
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
    }
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:+-]{1,512}$")
_PUBLICATION_STATE = "STAGED_NOT_PUBLISHED"
_STEP10_NEXT_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
    "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
)
_TOP_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "recovery_epoch",
        "source_baseline_event_sha256",
        "baseline_id",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "accepted_test_run_receipt_sha256",
        "receipt_count",
        "ordered_steps",
        "receipts",
        "receipt_sha256s",
        "required_sequence_event_2",
        "next_authority",
        "publication_state",
        "automatic_progression",
        "body_free",
        "all11_completion_chain_sha256",
    }
)


def _body_free(value: Any, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is str:
        return _BODY_FREE_TOKEN_RE.fullmatch(value) is not None
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
        for key, item in value.items():
            if type(key) is not str:
                return False
            if any(
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
        seen.remove(identity)


def _material(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in sorted(set(value) - {"all11_completion_chain_sha256"})
    }


def stage_recovery_epoch001_all11_current_step_completion_receipts(
    *,
    requirement_registry: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
    source_baseline_event: Mapping[str, Any],
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], ...]:
    """Return exact11 only after owner and independent checks all agree."""

    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    accepted = dict(accepted_test_run_receipt)
    event = dict(source_baseline_event)
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=root,
    ):
        raise ValueError("ALL11_INCOMPLETE")
    if validate_recovery_epoch001_accepted_test_run_receipt_shape(
        accepted,
        requirement_registry=registry,
        source_baseline_event=event,
        repo_root=root,
    ):
        raise ValueError("ALL11_INCOMPLETE")
    if independent.verify_recovery_epoch001_accepted_test_run_receipt(
        accepted,
        repo_root=root,
        requirement_registry=registry,
        source_baseline_event=event,
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
            )
        )
        if owner_issues or verifier_issues:
            staged.clear()
            raise ValueError("OWNER_VERIFIER_CONFLICT")
        staged.append(receipt)
    if len(staged) != 11:
        staged.clear()
        raise ValueError("ALL11_INCOMPLETE")
    return tuple(staged)


def build_recovery_epoch001_all11_completion_chain(
    *,
    receipts: Sequence[Mapping[str, Any]],
    requirement_registry: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
    source_baseline_event: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build a body-free event-2 candidate without publishing it."""

    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    accepted = dict(accepted_test_run_receipt)
    event = dict(source_baseline_event)
    receipt_rows = [dict(receipt) for receipt in receipts]
    if len(receipt_rows) != 11:
        raise ValueError("ALL11_INCOMPLETE")
    chain: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA,
        "candidate_version_id": accepted["candidate_version_id"],
        "recovery_epoch": 1,
        "source_baseline_event_sha256": event["event_sha256"],
        "baseline_id": accepted["baseline_id"],
        "source_commit": accepted["source_commit"],
        "source_tree": accepted["source_tree"],
        "canonical_current_closure_sha256": accepted[
            "canonical_current_closure_sha256"
        ],
        "source_dependency_closure_sha256": accepted[
            "source_dependency_closure_sha256"
        ],
        "registry_sha256": registry["registry_sha256"],
        "accepted_test_run_receipt_sha256": accepted[
            "accepted_test_run_receipt_sha256"
        ],
        "receipt_count": 11,
        "ordered_steps": list(range(11)),
        "receipts": receipt_rows,
        "receipt_sha256s": [
            receipt["receipt_sha256"] for receipt in receipt_rows
        ],
        "required_sequence_event_2": {
            "event_name": RECOVERY_EPOCH001_SEQUENCE_EVENT_2,
            "event_ordinal": RECOVERY_EPOCH001_SEQUENCE_EVENT_2_ORDINAL,
            "event_1_sha256": event["event_sha256"],
        },
        "next_authority": _STEP10_NEXT_AUTHORITY,
        "publication_state": _PUBLICATION_STATE,
        "automatic_progression": False,
        "body_free": True,
    }
    chain["all11_completion_chain_sha256"] = artifact_sha256(chain)
    issues = validate_recovery_epoch001_all11_completion_chain(
        chain,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        source_baseline_event=event,
        repo_root=root,
    )
    verifier_issues = independent.verify_recovery_epoch001_all11_completion_chain(
        chain,
        repo_root=root,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        source_baseline_event=event,
    )
    if issues or verifier_issues:
        raise ValueError(
            "OWNER_VERIFIER_CONFLICT"
            if verifier_issues
            else issues[0]
        )
    return chain


def _validate_recovery_epoch001_all11_completion_chain_impl(
    value: Any,
    *,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Validate all11 atomicity, ordering, roots, STOPs, and P2 boundary."""

    if type(value) is not dict:
        return ("ALL11_INCOMPLETE",)
    issues: set[str] = set()
    if set(value) != _TOP_KEYS:
        issues.add("ALL11_INCOMPLETE")
    if (
        value.get("schema_version")
        != RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA
        or value.get("candidate_version_id")
        != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
        or value.get("recovery_epoch") != 1
    ):
        issues.add("ALL11_INCOMPLETE")
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = (
        fresh_recovery_epoch001_current_step_requirement_registry()
        if requirement_registry is None
        else dict(requirement_registry)
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
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=root,
    ):
        issues.add("SOURCE_OR_ROOT_MISMATCH")
    if validate_recovery_epoch001_accepted_test_run_receipt_shape(
        accepted,
        requirement_registry=registry,
        source_baseline_event=event,
        repo_root=root,
    ):
        issues.add("SOURCE_OR_ROOT_MISMATCH")
    receipts = value.get("receipts")
    if type(receipts) is not list or len(receipts) != 11:
        issues.add("ALL11_INCOMPLETE")
        receipts = []
    steps = [
        receipt.get("step_number")
        for receipt in receipts
        if type(receipt) is dict
    ]
    if (
        value.get("receipt_count") != 11
        or value.get("ordered_steps") != list(range(11))
        or steps != list(range(11))
    ):
        issues.add("RECEIPT_ORDER_INVALID")
    previous: Mapping[str, Any] | None = None
    for step, receipt in enumerate(receipts):
        if type(receipt) is not dict:
            issues.add("ALL11_INCOMPLETE")
            continue
        owner_issues = (
            validate_recovery_epoch001_current_step_completion_receipt_shape(
                receipt,
                repo_root=root,
                previous_receipt=previous,
                step0_parent_authority=event,
                requirement_registry=registry,
                accepted_test_run_receipt=accepted,
                prior_receipts=tuple(receipts[:step]),
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
                prior_receipts=tuple(receipts[:step]),
            )
        )
        if owner_issues or verifier_issues:
            issues.add("OWNER_VERIFIER_CONFLICT")
        if receipt.get("verdict") != "PROVED":
            issues.add("ALL11_INCOMPLETE")
        if receipt.get("completion_condition", {}).get("satisfied") is not True:
            issues.add("ALL11_INCOMPLETE")
        if any(
            stop.get("triggered") is not False
            for stop in receipt.get("stop_conditions", [])
            if type(stop) is dict
        ):
            issues.add("STOP_TRIGGERED")
        if step > 0 and receipt.get("parent_binding", {}).get(
            "previous_receipt_sha256"
        ) != previous.get("receipt_sha256"):
            issues.add("PARENT_CHAIN_INVALID")
        expected_next = registry["steps"][step]["next_authority"]
        if receipt.get("next_authority") != expected_next:
            issues.add("NEXT_AUTHORITY_INVALID")
        previous = receipt
    receipt_hashes = [
        receipt.get("receipt_sha256")
        for receipt in receipts
        if type(receipt) is dict
    ]
    if (
        value.get("receipt_sha256s") != receipt_hashes
        or any(
            _SHA_RE.fullmatch(str(receipt_hash)) is None
            for receipt_hash in receipt_hashes
        )
    ):
        issues.add("PARENT_CHAIN_INVALID")
    root_fields = {
        "source_baseline_event_sha256": event.get("event_sha256"),
        "baseline_id": accepted.get("baseline_id"),
        "source_commit": accepted.get("source_commit"),
        "source_tree": accepted.get("source_tree"),
        "canonical_current_closure_sha256": accepted.get(
            "canonical_current_closure_sha256"
        ),
        "source_dependency_closure_sha256": accepted.get(
            "source_dependency_closure_sha256"
        ),
        "registry_sha256": registry.get("registry_sha256"),
        "accepted_test_run_receipt_sha256": accepted.get(
            "accepted_test_run_receipt_sha256"
        ),
    }
    if any(value.get(key) != expected for key, expected in root_fields.items()):
        issues.add("SOURCE_OR_ROOT_MISMATCH")
    if value.get("required_sequence_event_2") != {
        "event_name": RECOVERY_EPOCH001_SEQUENCE_EVENT_2,
        "event_ordinal": RECOVERY_EPOCH001_SEQUENCE_EVENT_2_ORDINAL,
        "event_1_sha256": event.get("event_sha256"),
    }:
        issues.add("SEQUENCE_INVALID")
    if value.get("next_authority") != _STEP10_NEXT_AUTHORITY:
        issues.add("NEXT_AUTHORITY_INVALID")
    if value.get("publication_state") != _PUBLICATION_STATE:
        issues.add("PUBLICATION_CONFLICT")
    if value.get("automatic_progression") is not False:
        issues.add("P2_NOT_AUTHORIZED")
    if value.get("body_free") is not True or not _body_free(value):
        issues.add("BODY_FREE_VIOLATION")
    try:
        expected_hash = artifact_sha256(_material(value))
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("all11_completion_chain_sha256") != expected_hash
        or _SHA_RE.fullmatch(
            str(value.get("all11_completion_chain_sha256", ""))
        )
        is None
    ):
        issues.add("HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_recovery_epoch001_all11_completion_chain(
    value: Any,
    *,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    try:
        return _validate_recovery_epoch001_all11_completion_chain_impl(
            value,
            requirement_registry=requirement_registry,
            accepted_test_run_receipt=accepted_test_run_receipt,
            source_baseline_event=source_baseline_event,
            repo_root=repo_root,
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
        return ("ALL11_INCOMPLETE",)


if __name__ == "__main__":
    raise SystemExit(
        "formal P1 may stage all11 in memory; publication remains separate"
    )
