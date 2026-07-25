#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Own the Recovery Epoch 001 formal success/failure parent boundary.

The parent owns ordering, one-shot lane selection, and STOP behavior. Git
object creation, ref mutation, and post-fetch observation stay behind the
explicit ports supplied by the caller.
"""

from pathlib import Path
import sys
from typing import Any, Mapping, Protocol


_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
for _path in (str(_HERE.parent), str(_INFERENCE_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


RECOVERY_EPOCH001_FORMAL_PARENT_PROTOCOL = (
    "RECOVERY_EPOCH001_FORMAL_SUCCESS_FAILURE_LANE_V1"
)
RECOVERY_EPOCH001_FORMAL_PARENT_PHASE_ORDER = (
    "PRE_EVENT1_ADMISSION",
    "EVENT1_EXACT2_POSTVERIFIED",
    "RESERVATION_EXACT1_POSTVERIFIED",
    "FORMAL_EXACT134_ONCE",
    "ATTEMPT_OWNER_AND_INDEPENDENT_VERIFIED",
    "TERMINAL_LANE_SELECTED",
    "TERMINAL_PUBLICATION_POSTVERIFIED",
)
RECOVERY_EPOCH001_FORMAL_PARENT_TERMINAL_STATES = frozenset(
    {
        "STEP0_10_PREREQUISITES_PROVED",
        "FORMAL_FAILURE_ATTEMPT_PUBLISHED_STOP",
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "STOPPED",
    }
)

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
_ALL11_PATH = (
    f"{_PREFIX}NLSv3_Step11_Cycle001_RecoveryEpoch001_"
    "All11CompletionChain_BodyFree_Chain_20260724.json"
)


class RecoveryEpoch001FormalParentPorts(Protocol):
    def publish_and_postfetch(
        self,
        *,
        request: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Publish one exact candidate and return a post-fetch observation."""

    def run_exact134_once(
        self,
        *,
        requirement_registry: Mapping[str, Any],
        source_baseline_event: Mapping[str, Any],
        run_reservation: Mapping[str, Any],
        publication_evidence: Mapping[str, Any],
        repo_root: Path,
    ) -> Mapping[str, Any]:
        """Consume the published reservation exactly once."""


def _issue_codes(value: Any) -> tuple[str, ...]:
    if type(value) not in (tuple, list, set, frozenset):
        return ()
    return tuple(
        sorted(
            row if type(row) is str else str(getattr(row, "code", ""))
            for row in value
        )
    )


def _result(
    *,
    terminal_state: str,
    stop_code: str | None,
    attempt_id: str | None,
    event1_commit: str | None,
    reservation_commit: str | None,
    terminal_commit: str | None,
) -> dict[str, Any]:
    if terminal_state not in RECOVERY_EPOCH001_FORMAL_PARENT_TERMINAL_STATES:
        terminal_state = "STOPPED"
        stop_code = stop_code or "FORMAL_PARENT_STOP"
    return {
        "protocol": RECOVERY_EPOCH001_FORMAL_PARENT_PROTOCOL,
        "terminal_state": terminal_state,
        "stop_code": stop_code,
        "attempt_id": attempt_id,
        "event1_publication_commit_sha1": event1_commit,
        "reservation_publication_commit_sha1": reservation_commit,
        "terminal_publication_commit_sha1": terminal_commit,
        "automatic_progression": False,
        "p2_authorized": False,
        "body_free": True,
    }


def _artifact(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if type(value) is not dict:
        return {}
    nested = value.get("artifact")
    return nested if type(nested) is dict else value


def _commit(value: Mapping[str, Any] | None) -> str | None:
    if type(value) is not dict:
        return None
    commit = value.get("publication_commit_sha1")
    if type(commit) is str:
        return commit
    transaction = value.get("transaction")
    if type(transaction) is dict:
        target = transaction.get("target_commit_sha1")
        return target if type(target) is str else None
    return None


def _matching_consumed_reservation(
    rows: Any,
    *,
    authority_token: str,
) -> Mapping[str, Any] | None:
    if type(rows) is not list:
        return None
    for row in rows:
        if (
            type(row) is dict
            and _artifact(row).get("authority_token") == authority_token
        ):
            return row
    return None


def _admit_pre_event1(
    *,
    admission_snapshot: Mapping[str, Any],
    authority_token: str,
    event1_challenge_id: str,
    repo_root: Path,
) -> tuple[str, ...]:
    del repo_root
    if (
        type(admission_snapshot) is not dict
        or type(authority_token) is not str
        or not authority_token
        or type(event1_challenge_id) is not str
        or len(event1_challenge_id) != 64
        or type(admission_snapshot.get("source_closure")) is not dict
        or type(admission_snapshot.get("requirement_registry")) is not dict
        or type(admission_snapshot.get("cocolon_repository_snapshot"))
        is not dict
        or admission_snapshot.get("transport_capabilities")
        != {
            "base_tree_read": True,
            "expected_old_sha_lease": True,
            "single_ref_update": True,
        }
    ):
        return ("FORMAL_PARENT_ADMISSION_INVALID",)
    return ()


def _prepare_request(
    *,
    phase: str,
    admission_snapshot: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    key = {
        "EVENT1_EXACT2": "event1_publication_request",
        "RESERVATION_EXACT1": "reservation_publication_request",
        "FAILURE_ATTEMPT_EXACT1": "failure_attempt_publication_request",
        "EVENT2_EXACT15": "event2_publication_request",
    }[phase]
    supplied = admission_snapshot.get(key)
    request = dict(supplied) if type(supplied) is dict else {}
    request.update(
        {
            "phase": phase,
            "payload": dict(payload),
            "automatic_progression": False,
            "body_free": True,
        }
    )
    return request


def _prepare_event1_publication(
    **kwargs: Any,
) -> dict[str, Any]:
    return _prepare_request(
        phase="EVENT1_EXACT2",
        admission_snapshot=kwargs["admission_snapshot"],
        payload={
            "authority_token": kwargs["authority_token"],
            "challenge_id": kwargs["event1_challenge_id"],
            "source_closure": kwargs["source_closure"],
        },
    )


def _prepare_reservation_publication(
    **kwargs: Any,
) -> dict[str, Any]:
    return _prepare_request(
        phase="RESERVATION_EXACT1",
        admission_snapshot=kwargs["admission_snapshot"],
        payload={
            "authority_token": kwargs["authority_token"],
            "challenge_id": kwargs["formal_run_challenge_id"],
            "source_baseline_event": kwargs["source_baseline_event"],
            "source_closure": kwargs["source_closure"],
        },
    )


def _prepare_failure_attempt_publication(
    **kwargs: Any,
) -> dict[str, Any]:
    return _prepare_request(
        phase="FAILURE_ATTEMPT_EXACT1",
        admission_snapshot=kwargs["admission_snapshot"],
        payload={
            "formal_test_run_attempt": kwargs["formal_test_run_attempt"],
            "reservation_publication_commit_sha1": kwargs[
                "reservation_publication_commit_sha1"
            ],
        },
    )


def _prepare_event2_publication(
    **kwargs: Any,
) -> dict[str, Any]:
    return _prepare_request(
        phase="EVENT2_EXACT15",
        admission_snapshot=kwargs["admission_snapshot"],
        payload={
            "accepted_test_run_receipt": kwargs[
                "accepted_test_run_receipt"
            ],
            "step_receipts": kwargs["step_receipts"],
            "all11_completion_chain": kwargs[
                "all11_completion_chain"
            ],
            "atomic_manifest": kwargs["atomic_manifest"],
        },
    )


def _verified_publication(
    *,
    expected_phase: str,
    publication_result: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(publication_result) is not dict
        or publication_result.get("phase") != expected_phase
        or publication_result.get("body_free") is not True
    ):
        raise ValueError("FORMAL_PARENT_POSTVERIFY_INVALID")
    verified = publication_result.get("postverified")
    return (
        dict(verified)
        if type(verified) is dict
        else dict(publication_result)
    )


def _verify_event1_publication(**kwargs: Any) -> dict[str, Any]:
    return _verified_publication(
        expected_phase="EVENT1_EXACT2",
        publication_result=kwargs["publication_result"],
    )


def _verify_reservation_publication(**kwargs: Any) -> dict[str, Any]:
    return _verified_publication(
        expected_phase="RESERVATION_EXACT1",
        publication_result=kwargs["publication_result"],
    )


def _verify_failure_attempt_publication(**kwargs: Any) -> dict[str, Any]:
    return _verified_publication(
        expected_phase="FAILURE_ATTEMPT_EXACT1",
        publication_result=kwargs["publication_result"],
    )


def _verify_event2_publication(**kwargs: Any) -> dict[str, Any]:
    return _verified_publication(
        expected_phase="EVENT2_EXACT15",
        publication_result=kwargs["publication_result"],
    )


def _formal_parent_children() -> dict[str, Any]:
    from emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3 import (
        build_recovery_epoch001_accepted_test_run_receipt,
        validate_recovery_epoch001_formal_test_run_attempt_shape,
    )
    from emlis_nls_v3_recovery_epoch001_all11_receipt_issue import (
        build_recovery_epoch001_all11_completion_chain,
        stage_recovery_epoch001_all11_current_step_completion_receipts,
    )
    from emlis_nls_v3_recovery_epoch001_atomic_publication_bundle_v3 import (
        build_recovery_epoch001_all11_atomic_publication_manifest,
        validate_recovery_epoch001_all11_atomic_publication_manifest,
    )
    from emlis_nls_v3_recovery_epoch001_closure_receipt_verify import (
        verify_recovery_epoch001_accepted_test_run_receipt,
        verify_recovery_epoch001_all11_atomic_publication_manifest,
        verify_recovery_epoch001_formal_test_run_attempt,
    )

    return {
        "admit_pre_event1": _admit_pre_event1,
        "prepare_event1_publication": _prepare_event1_publication,
        "verify_event1_publication": _verify_event1_publication,
        "prepare_reservation_publication": (
            _prepare_reservation_publication
        ),
        "verify_reservation_publication": (
            _verify_reservation_publication
        ),
        "validate_attempt_owner": (
            validate_recovery_epoch001_formal_test_run_attempt_shape
        ),
        "verify_attempt_independent": (
            verify_recovery_epoch001_formal_test_run_attempt
        ),
        "prepare_failure_attempt_publication": (
            _prepare_failure_attempt_publication
        ),
        "verify_failure_attempt_publication": (
            _verify_failure_attempt_publication
        ),
        "build_accepted_receipt": (
            build_recovery_epoch001_accepted_test_run_receipt
        ),
        "verify_accepted_receipt": (
            verify_recovery_epoch001_accepted_test_run_receipt
        ),
        "build_step_receipts": (
            stage_recovery_epoch001_all11_current_step_completion_receipts
        ),
        "build_all11_chain": (
            build_recovery_epoch001_all11_completion_chain
        ),
        "build_atomic_manifest": (
            build_recovery_epoch001_all11_atomic_publication_manifest
        ),
        "validate_atomic_manifest_owner": (
            validate_recovery_epoch001_all11_atomic_publication_manifest
        ),
        "verify_atomic_manifest_independent": (
            verify_recovery_epoch001_all11_atomic_publication_manifest
        ),
        "prepare_event2_publication": _prepare_event2_publication,
        "verify_event2_publication": _verify_event2_publication,
    }


def orchestrate_recovery_epoch001_formal_parent_lane(
    authority_token: str,
    event1_challenge_id: str,
    formal_run_challenge_id: str,
    admission_snapshot: Mapping[str, Any],
    ports: RecoveryEpoch001FormalParentPorts,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = (
        _REPO_ROOT
        if repo_root is None
        else Path(repo_root).resolve()
    )
    children = _formal_parent_children()
    admission_issues = _issue_codes(
        children["admit_pre_event1"](
            admission_snapshot=admission_snapshot,
            authority_token=authority_token,
            event1_challenge_id=event1_challenge_id,
            repo_root=root,
        )
    )
    if admission_issues:
        return _result(
            terminal_state="STOPPED",
            stop_code=admission_issues[0],
            attempt_id=None,
            event1_commit=None,
            reservation_commit=None,
            terminal_commit=None,
        )
    consumed = _matching_consumed_reservation(
        admission_snapshot.get("published_reservations"),
        authority_token=authority_token,
    )
    if consumed is not None:
        return _result(
            terminal_state="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
            stop_code="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
            attempt_id=str(_artifact(consumed).get("attempt_id") or "")
            or None,
            event1_commit=_commit(
                admission_snapshot.get("published_event1_record")
            ),
            reservation_commit=_commit(consumed),
            terminal_commit=None,
        )

    source_closure = admission_snapshot["source_closure"]
    registry = admission_snapshot["requirement_registry"]
    event1_commit: str | None = None
    reservation_commit: str | None = None
    attempt_id: str | None = None
    reservation_consumed = False
    try:
        published_event1 = admission_snapshot.get(
            "published_event1_record"
        )
        if type(published_event1) is dict:
            event1_verified = dict(published_event1)
        else:
            event1_request = children["prepare_event1_publication"](
                authority_token=authority_token,
                event1_challenge_id=event1_challenge_id,
                source_closure=source_closure,
                admission_snapshot=admission_snapshot,
                repo_root=root,
            )
            event1_publication = ports.publish_and_postfetch(
                request=event1_request
            )
            event1_verified = children[
                "verify_event1_publication"
            ](
                publication_result=event1_publication,
                admission_snapshot=admission_snapshot,
                repo_root=root,
            )
        event1_commit = _commit(event1_verified)
        source_event_record = event1_verified.get(
            "source_baseline_event",
            event1_verified,
        )
        source_event = _artifact(source_event_record)

        reservation_request = children[
            "prepare_reservation_publication"
        ](
            authority_token=authority_token,
            formal_run_challenge_id=formal_run_challenge_id,
            source_baseline_event=source_event_record,
            source_closure=source_closure,
            admission_snapshot=admission_snapshot,
            repo_root=root,
        )
        reservation_publication = ports.publish_and_postfetch(
            request=reservation_request
        )
        reservation_verified = children[
            "verify_reservation_publication"
        ](
            publication_result=reservation_publication,
            source_baseline_event=source_event_record,
            admission_snapshot=admission_snapshot,
            repo_root=root,
        )
        reservation_consumed = True
        reservation_commit = _commit(reservation_verified)
        run_reservation = reservation_verified["run_reservation"]
        publication_evidence = reservation_verified[
            "publication_evidence"
        ]
        attempt_id = str(
            _artifact(run_reservation).get("attempt_id") or ""
        ) or None

        attempt = dict(
            ports.run_exact134_once(
                requirement_registry=registry,
                source_baseline_event=source_event,
                run_reservation=run_reservation,
                publication_evidence=publication_evidence,
                repo_root=root,
            )
        )
        attempt_id = str(attempt.get("attempt_id") or attempt_id or "") or None
        owner_issues = _issue_codes(
            children["validate_attempt_owner"](
                value=attempt,
                repo_root=root,
                requirement_registry=registry,
            )
        )
        independent_issues = _issue_codes(
            children["verify_attempt_independent"](
                value=attempt,
                repo_root=root,
                requirement_registry=registry,
                source_baseline_event=source_event,
                publication_evidence=publication_evidence,
            )
        )
        if owner_issues or independent_issues or (
            owner_issues != independent_issues
        ):
            return _result(
                terminal_state="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
                stop_code="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
                attempt_id=attempt_id,
                event1_commit=event1_commit,
                reservation_commit=reservation_commit,
                terminal_commit=None,
            )

        outcome_state = attempt.get("outcome_state")
        if outcome_state == "SUCCEEDED":
            accepted = children["build_accepted_receipt"](
                formal_test_run_attempt=attempt,
                requirement_registry=registry,
                source_baseline_event=source_event,
                publication_evidence=publication_evidence,
                repo_root=root,
            )
            accepted_issues = _issue_codes(
                children["verify_accepted_receipt"](
                    value=accepted,
                    repo_root=root,
                    requirement_registry=registry,
                    source_baseline_event=source_event,
                    publication_evidence=publication_evidence,
                )
            )
            if accepted_issues:
                raise ValueError(accepted_issues[0])
            receipts = list(
                children["build_step_receipts"](
                    requirement_registry=registry,
                    accepted_test_run_receipt=accepted,
                    source_baseline_event=source_event,
                    publication_evidence=publication_evidence,
                    repo_root=root,
                )
            )
            chain = children["build_all11_chain"](
                receipts=receipts,
                requirement_registry=registry,
                accepted_test_run_receipt=accepted,
                source_baseline_event=source_event,
                publication_evidence=publication_evidence,
                repo_root=root,
            )
            core_artifacts = {_ACCEPTED_PATH: accepted}
            core_artifacts.update(
                {
                    path: receipt
                    for path, receipt in zip(_STEP_PATHS, receipts)
                }
            )
            core_artifacts[_ALL11_PATH] = chain
            source_event_identity = attempt["source_baseline_event"]
            manifest = children["build_atomic_manifest"](
                core_artifacts_by_path=core_artifacts,
                source_baseline_event=source_event_identity,
                base_commit_sha1=reservation_commit,
            )
            manifest_kwargs = {
                "core_artifacts_by_path": core_artifacts,
                "expected_source_baseline_event": (
                    source_event_identity
                ),
                "expected_base_commit_sha1": reservation_commit,
            }
            manifest_owner = _issue_codes(
                children["validate_atomic_manifest_owner"](
                    value=manifest,
                    **manifest_kwargs,
                )
            )
            manifest_independent = _issue_codes(
                children["verify_atomic_manifest_independent"](
                    value=manifest,
                    **manifest_kwargs,
                )
            )
            if (
                manifest_owner
                or manifest_independent
                or manifest_owner != manifest_independent
            ):
                raise ValueError("PUBLICATION_BUNDLE_INVALID")
            event2_request = children["prepare_event2_publication"](
                accepted_test_run_receipt=accepted,
                step_receipts=receipts,
                all11_completion_chain=chain,
                atomic_manifest=manifest,
                admission_snapshot=admission_snapshot,
                repo_root=root,
            )
            event2_publication = ports.publish_and_postfetch(
                request=event2_request
            )
            event2_verified = children[
                "verify_event2_publication"
            ](
                publication_result=event2_publication,
                admission_snapshot=admission_snapshot,
                repo_root=root,
            )
            return _result(
                terminal_state="STEP0_10_PREREQUISITES_PROVED",
                stop_code=None,
                attempt_id=attempt_id,
                event1_commit=event1_commit,
                reservation_commit=reservation_commit,
                terminal_commit=_commit(event2_verified),
            )

        if outcome_state in {"FAILED", "TIMED_OUT", "INFRA_ERROR"}:
            failure_request = children[
                "prepare_failure_attempt_publication"
            ](
                formal_test_run_attempt=attempt,
                reservation_publication_commit_sha1=reservation_commit,
                admission_snapshot=admission_snapshot,
                repo_root=root,
            )
            failure_publication = ports.publish_and_postfetch(
                request=failure_request
            )
            failure_verified = children[
                "verify_failure_attempt_publication"
            ](
                publication_result=failure_publication,
                formal_test_run_attempt=attempt,
                admission_snapshot=admission_snapshot,
                repo_root=root,
            )
            return _result(
                terminal_state="FORMAL_FAILURE_ATTEMPT_PUBLISHED_STOP",
                stop_code=str(attempt.get("stop_code") or "")
                or "RUN_PARTIAL",
                attempt_id=attempt_id,
                event1_commit=event1_commit,
                reservation_commit=reservation_commit,
                terminal_commit=_commit(failure_verified),
            )
        raise ValueError("FORMAL_PARENT_TERMINAL_STATE_INVALID")
    except (
        AttributeError,
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        return _result(
            terminal_state=(
                "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
                if reservation_consumed
                else "STOPPED"
            ),
            stop_code=(
                "ATTEMPT_CONSUMPTION_UNKNOWN_STOP"
                if reservation_consumed
                else str(exc) or "FORMAL_PARENT_STOP"
            ),
            attempt_id=attempt_id,
            event1_commit=event1_commit,
            reservation_commit=reservation_commit,
            terminal_commit=None,
        )


def main() -> int:
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
