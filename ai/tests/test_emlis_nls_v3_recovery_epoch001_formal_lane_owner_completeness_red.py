# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for Recovery Epoch 001 formal-lane owner completeness.

This file freezes the missing production manifest semantics, terminal-run
state alignment, checkpoint-preserving timeout/infra handling, and the
formal-parent orchestration boundary.  Every Git graph is test-owned and
in-memory.  The tests do not run exact134, write a ref, publish an artifact,
authorize P2, or advance Cycle 001.
"""

from copy import deepcopy
import ast
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable, Mapping

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    fresh_recovery_epoch001_canonical_current_closure,
)
accepted_red = importlib.import_module(
    "test_emlis_nls_v3_recovery_epoch001_exact134_accepted_success_red"
)
sequence_red = importlib.import_module(
    "test_emlis_nls_v3_recovery_epoch001_sequence_ledger_publication_red"
)


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_FORMAL_SUCCESS_AND_FAILURE_"
    "LANE_OWNER_COMPLETENESS_RECONCILIATION_RED_FREEZE_ONLY"
)
_KAREN_DIARY_ENTRY = "700f749f5149cac1f8bd4bab8a364d524a56985b"
_COCOLON_ENTRY = "5722c4aea2e1d42d7f84e9b36e6322b538615bf2"
_COCOLON_ENTRY_TREE = "a804fcbf4691ea9c842f1c8fa13b368f87836aa0"
_MASHOS_API_ENTRY = "191e9d8be63132f10f94e2b2f54c6bae94ce1f07"
_MASHOS_API_ENTRY_TREE = "e68df6587b8cb674456b3bc9bceb23e0699f33aa"
_DESIGN_BLOB = "7e7d454d888141cbdb872244bf6df93c046e0b6c"
_DESIGN_SHA256 = (
    "8bb377d49f04a33d6d21323a40bcd5ddc0d30eee8d4d2a2700ad7f074e32bb64"
)
_DETAILED_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
_PARENT_PROTOCOL = "RECOVERY_EPOCH001_FORMAL_SUCCESS_FAILURE_LANE_V1"
_PARENT_MODULE_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch001_formal_parent_orchestrator_v3.py"
)
_PUBLISHER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_atomic_publication_bundle_v3.py"
)
_VERIFIER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
)
_RUNNER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
)
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_"
    "formal_lane_owner_completeness_red.py"
)
_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "all11_atomic_publication_manifest.v2"
)
_MANIFEST_BUILDER = (
    "build_recovery_epoch001_all11_atomic_publication_manifest"
)
_MANIFEST_OWNER = (
    "validate_recovery_epoch001_all11_atomic_publication_manifest"
)
_MANIFEST_VERIFIER = (
    "verify_recovery_epoch001_all11_atomic_publication_manifest"
)
_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "logical_cycle_id",
        "recovery_epoch_id",
        "source_baseline_event",
        "base_commit_sha1",
        "core_artifact_count",
        "core_artifacts",
        "core_artifact_set_sha256",
        "event_supporting_artifact_count",
        "expected_changed_path_count",
        "event_path",
        "ref_update_mode",
        "body_free",
        "atomic_publication_manifest_sha256",
    }
)
_TERMINAL_STATE_MATRIX = {
    "SUCCESS": ("SUCCEEDED", None),
    "A01": ("FAILED", "RUN_PARTIAL"),
    "A08": ("FAILED", "RUN_COLLECTION_ERROR"),
    "A07": ("TIMED_OUT", "RUN_TIMED_OUT"),
    "INFRA": ("INFRA_ERROR", "RUN_INFRA_ERROR"),
}
_PARENT_PHASE_ORDER = (
    "PRE_EVENT1_ADMISSION",
    "EVENT1_EXACT2_POSTVERIFIED",
    "RESERVATION_EXACT1_POSTVERIFIED",
    "FORMAL_EXACT134_ONCE",
    "ATTEMPT_OWNER_AND_INDEPENDENT_VERIFIED",
    "TERMINAL_LANE_SELECTED",
    "TERMINAL_PUBLICATION_POSTVERIFIED",
)
_PARENT_TERMINAL_STATES = frozenset(
    {
        "STEP0_10_PREREQUISITES_PROVED",
        "FORMAL_FAILURE_ATTEMPT_PUBLISHED_STOP",
        "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "STOPPED",
    }
)
_PARENT_CHILD_KEYS = frozenset(
    {
        "admit_pre_event1",
        "prepare_event1_publication",
        "verify_event1_publication",
        "prepare_reservation_publication",
        "verify_reservation_publication",
        "validate_attempt_owner",
        "verify_attempt_independent",
        "prepare_failure_attempt_publication",
        "verify_failure_attempt_publication",
        "build_accepted_receipt",
        "verify_accepted_receipt",
        "build_step_receipts",
        "build_all11_chain",
        "build_atomic_manifest",
        "validate_atomic_manifest_owner",
        "verify_atomic_manifest_independent",
        "prepare_event2_publication",
        "verify_event2_publication",
    }
)
_PARENT_RESULT_KEYS = frozenset(
    {
        "protocol",
        "terminal_state",
        "stop_code",
        "attempt_id",
        "event1_publication_commit_sha1",
        "reservation_publication_commit_sha1",
        "terminal_publication_commit_sha1",
        "automatic_progression",
        "p2_authorized",
        "body_free",
    }
)
_PROTECTED_SHA256 = {
    (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "exact134_accepted_success_red.py"
    ): "58ba36ded0a1b51ed9ee03bf4a4f8a88dde06c775c520d713a67505b8f63379f",
    (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "sequence_ledger_publication_red.py"
    ): "2dc0e00f2d53734399bc9f5682fc01c2a1447d8e3974653d71989f11ff339db7",
    (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "current_closure_completion_red.py"
    ): "ec894e14fcc28d6562b0415ab34f18a3cf7be40942c313103f52991888a5db52",
    (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "proved_receipt_contract_red.py"
    ): "ba9f39f83cdaa18096973706e896dd31dfa79ba2d25eec8921d6e6bcf8ef853f",
}

_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module_or_red(path: str, name: str, red_code: str) -> ModuleType:
    absolute = _REPO_ROOT / path
    if not absolute.is_file():
        pytest.fail(red_code, pytrace=False)
    spec = importlib.util.spec_from_file_location(name, absolute)
    if spec is None or spec.loader is None:
        pytest.fail(red_code, pytrace=False)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _issue_codes(value: Any) -> tuple[str, ...]:
    if type(value) not in (tuple, list, set, frozenset):
        return ()
    return tuple(
        sorted(
            row if type(row) is str else str(getattr(row, "code", ""))
            for row in value
        )
    )


def _manifest_api_or_red() -> tuple[ModuleType, ModuleType]:
    publisher, verifier = sequence_red._publication_apis_or_red()
    if (
        not hasattr(publisher, _MANIFEST_BUILDER)
        or not hasattr(publisher, _MANIFEST_OWNER)
    ):
        pytest.fail(
            "RECOVERY_EPOCH001_EVENT2_ATOMIC_MANIFEST_OWNER_NOT_PROVED",
            pytrace=False,
        )
    if not hasattr(verifier, _MANIFEST_VERIFIER):
        pytest.fail(
            "RECOVERY_EPOCH001_EVENT2_ATOMIC_MANIFEST_"
            "INDEPENDENT_VERIFIER_NOT_PROVED",
            pytrace=False,
        )
    return publisher, verifier


def _core_artifacts(case: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        path: deepcopy(case["artifacts_by_path"][path])
        for path in sorted(sequence_red._CORE_PATHS)
    }


def _manifest_validator_kwargs(
    case: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "core_artifacts_by_path": _core_artifacts(case),
        "expected_source_baseline_event": deepcopy(
            case["publication_evidence"]["source_baseline_event"]["identity"]
        ),
        "expected_base_commit_sha1": case["bundle"]["base_commit_sha1"],
    }


def _rewire_event2_manifest(
    case: dict[str, Any],
    *,
    rehash_manifest: bool = True,
) -> None:
    """Coherently rebind all outward hashes after an internal mutation."""

    manifest = case["artifacts_by_path"][sequence_red._MANIFEST_PATH]
    if rehash_manifest:
        manifest["atomic_publication_manifest_sha256"] = artifact_sha256(
            sequence_red._material(
                manifest,
                "atomic_publication_manifest_sha256",
            )
        )
    identities = [
        sequence_red._identity_for_supporting_path(
            path,
            case["artifacts_by_path"][path],
        )
        for path in sequence_red._EVENT2_SUPPORTING_PATHS
    ]
    case["event"]["publication"]["supporting_artifacts"] = identities
    sequence_red._rehash_event(case)
    base_commit = case["bundle"]["base_commit_sha1"]
    base_tree = case["bundle"]["base_tree_sha1"]
    case["supporting_set"] = sequence_red._supporting_set(
        artifacts_by_path=case["artifacts_by_path"],
        base_commit=base_commit,
        base_tree=base_tree,
    )
    case["bundle"] = sequence_red._bundle(
        event=case["event"],
        artifacts_by_path=case["artifacts_by_path"],
        base_commit=base_commit,
        base_tree=base_tree,
    )
    target_commit = case["transaction"]["target_commit_sha1"]
    transaction, candidate = sequence_red._transaction(
        bundle=case["bundle"],
        base_snapshot=case["base_snapshot"],
        target_commit=target_commit,
    )
    case["transaction"] = transaction
    case["candidate_snapshot"] = candidate
    case["published_snapshot"] = sequence_red._published_snapshot(
        candidate_snapshot=candidate,
        target_commit=target_commit,
    )
    case["ref_update_observation"] = sequence_red._ref_update_observation(
        bundle=case["bundle"],
        target_commit=target_commit,
    )


def _mutate_manifest(case: dict[str, Any], attack: str) -> None:
    manifest = case["artifacts_by_path"][sequence_red._MANIFEST_PATH]
    rehash_manifest = True
    if attack == "CORE_COUNT":
        manifest["core_artifact_count"] = 12
    elif attack == "EXTRA_KEY":
        manifest["forbidden_extra"] = "FORBIDDEN"
    elif attack == "CORE_DUPLICATE":
        manifest["core_artifacts"][-1] = deepcopy(
            manifest["core_artifacts"][0]
        )
        manifest["core_artifact_set_sha256"] = artifact_sha256(
            manifest["core_artifacts"]
        )
    elif attack == "CORE_ORDER":
        manifest["core_artifacts"] = list(
            reversed(manifest["core_artifacts"])
        )
        manifest["core_artifact_set_sha256"] = artifact_sha256(
            manifest["core_artifacts"]
        )
    elif attack == "CORE_SET_HASH":
        manifest["core_artifact_set_sha256"] = "0" * 64
    elif attack == "SUPPORTING_COUNT":
        manifest["event_supporting_artifact_count"] = 13
    elif attack == "CHANGED_COUNT":
        manifest["expected_changed_path_count"] = 14
    elif attack == "EVENT_PATH":
        manifest["event_path"] = "forbidden/event2.json"
    elif attack == "REF_MODE":
        manifest["ref_update_mode"] = "UNLEASED_FORCE_FORBIDDEN"
    elif attack == "BODY_FREE":
        manifest["body_free"] = False
    elif attack == "CANDIDATE":
        manifest["candidate_version_id"] = "nls_v3_rc_9999"
    elif attack == "CYCLE":
        manifest["logical_cycle_id"] = "NLS_V3_CYCLE_999"
    elif attack == "EPOCH":
        manifest["recovery_epoch_id"] = "NLS_V3_RECOVERY_EPOCH_999"
    elif attack == "SOURCE_EVENT":
        source = manifest["source_baseline_event"]
        source["publication_commit_sha1"] = "f" * 40
        sequence_red._identity_hash(source)
    elif attack == "BASE_COMMIT":
        manifest["base_commit_sha1"] = "f" * 40
    elif attack == "SELF_HASH":
        manifest["atomic_publication_manifest_sha256"] = "0" * 64
        rehash_manifest = False
    elif attack == "MISSING_KEY":
        manifest.pop("base_commit_sha1")
    else:
        raise AssertionError(f"unknown manifest attack: {attack}")
    _rewire_event2_manifest(case, rehash_manifest=rehash_manifest)


def _attempt_fixture(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if name == "SUCCESS":
        return accepted_red._valid_v2_attempt_and_evidence()
    _valid, evidence = accepted_red._valid_v2_attempt_and_evidence()
    return accepted_red._failure_attempt(name), evidence


def _worker_report(
    attempt: Mapping[str, Any],
    pair: tuple[str, str | None],
) -> dict[str, Any]:
    report = {
        key: deepcopy(attempt[key])
        for key in (
            "collection_node_ids",
            "executed_node_ids",
            "runner_environment",
            "run_start",
            "run_end",
            "run_started_at_utc",
            "run_finished_at_utc",
            "outcomes",
            "counts",
            "exit_code",
            "timed_out",
            "body_free",
        )
    }
    report["outcome_state"], report["stop_code"] = pair
    return report


def _parent_module_or_red() -> ModuleType:
    parent = _module_or_red(
        _PARENT_MODULE_PATH,
        "emlis_nls_v3_recovery_epoch001_formal_parent_orchestrator_v3_"
        "red_target",
        "RECOVERY_EPOCH001_FORMAL_PARENT_ORCHESTRATOR_NOT_PROVED",
    )
    required = {
        "RECOVERY_EPOCH001_FORMAL_PARENT_PROTOCOL",
        "RECOVERY_EPOCH001_FORMAL_PARENT_PHASE_ORDER",
        "RECOVERY_EPOCH001_FORMAL_PARENT_TERMINAL_STATES",
        "RecoveryEpoch001FormalParentPorts",
        "orchestrate_recovery_epoch001_formal_parent_lane",
        "main",
        "_formal_parent_children",
    }
    if any(not hasattr(parent, name) for name in required):
        pytest.fail(
            "RECOVERY_EPOCH001_FORMAL_PARENT_ORCHESTRATOR_NOT_PROVED",
            pytrace=False,
        )
    return parent


class _FakePorts:
    def __init__(self, run_result: Mapping[str, Any]) -> None:
        self.run_result = deepcopy(run_result)
        self.calls: list[tuple[str, str]] = []

    def publish_and_postfetch(
        self,
        *,
        request: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        phase = str(request["phase"])
        self.calls.append(("publish", phase))
        return {
            "phase": phase,
            "transaction": {"target_commit_sha1": phase.lower()},
            "candidate_snapshot": {"phase": phase},
            "repository_snapshot": {"phase": phase},
            "ref_update_observation": {"phase": phase},
            "body_free": True,
        }

    def run_exact134_once(
        self,
        *,
        requirement_registry: Mapping[str, Any],
        source_baseline_event: Mapping[str, Any],
        run_reservation: Mapping[str, Any],
        publication_evidence: Mapping[str, Any],
        repo_root: Path,
    ) -> Mapping[str, Any]:
        del (
            requirement_registry,
            source_baseline_event,
            publication_evidence,
            repo_root,
        )
        attempt_id = str(
            run_reservation.get("artifact", {}).get("attempt_id", "")
        )
        self.calls.append(("run", attempt_id))
        return deepcopy(self.run_result)


def _recording_children(
    calls: list[str],
) -> dict[str, Callable[..., Any]]:
    event1_record = {"artifact": {"event_id": "EVENT1"}, "body_free": True}
    reservation_record = {
        "artifact": {"attempt_id": "attempt-001"},
        "body_free": True,
    }

    def child(name: str, result: Any) -> Callable[..., Any]:
        def invoke(**_kwargs: Any) -> Any:
            calls.append(name)
            return deepcopy(result)

        return invoke

    return {
        "admit_pre_event1": child("admit_pre_event1", ()),
        "prepare_event1_publication": child(
            "prepare_event1_publication",
            {
                "phase": "EVENT1_EXACT2",
                "bundle": {},
                "artifacts_by_path": {},
                "event": {},
                "body_free": True,
            },
        ),
        "verify_event1_publication": child(
            "verify_event1_publication",
            {
                "source_baseline_event": event1_record,
                "publication_commit_sha1": "1" * 40,
            },
        ),
        "prepare_reservation_publication": child(
            "prepare_reservation_publication",
            {
                "phase": "RESERVATION_EXACT1",
                "bundle": {},
                "artifacts_by_path": {},
                "event": None,
                "body_free": True,
            },
        ),
        "verify_reservation_publication": child(
            "verify_reservation_publication",
            {
                "run_reservation": reservation_record,
                "publication_evidence": {
                    "formal_test_run_reservation": reservation_record
                },
                "publication_commit_sha1": "2" * 40,
            },
        ),
        "validate_attempt_owner": child("validate_attempt_owner", ()),
        "verify_attempt_independent": child(
            "verify_attempt_independent",
            (),
        ),
        "prepare_failure_attempt_publication": child(
            "prepare_failure_attempt_publication",
            {
                "phase": "FAILURE_ATTEMPT_EXACT1",
                "bundle": {},
                "artifacts_by_path": {},
                "event": None,
                "body_free": True,
            },
        ),
        "verify_failure_attempt_publication": child(
            "verify_failure_attempt_publication",
            {"publication_commit_sha1": "3" * 40},
        ),
        "build_accepted_receipt": child(
            "build_accepted_receipt",
            {"accepted": True},
        ),
        "verify_accepted_receipt": child("verify_accepted_receipt", ()),
        "build_step_receipts": child(
            "build_step_receipts",
            [{"step_number": step} for step in range(11)],
        ),
        "build_all11_chain": child(
            "build_all11_chain",
            {"all_steps_complete": True},
        ),
        "build_atomic_manifest": child(
            "build_atomic_manifest",
            {"schema_version": _MANIFEST_SCHEMA},
        ),
        "validate_atomic_manifest_owner": child(
            "validate_atomic_manifest_owner",
            (),
        ),
        "verify_atomic_manifest_independent": child(
            "verify_atomic_manifest_independent",
            (),
        ),
        "prepare_event2_publication": child(
            "prepare_event2_publication",
            {
                "phase": "EVENT2_EXACT15",
                "bundle": {},
                "artifacts_by_path": {},
                "event": {},
                "body_free": True,
            },
        ),
        "verify_event2_publication": child(
            "verify_event2_publication",
            {"publication_commit_sha1": "4" * 40},
        ),
    }


def _parent_admission(
    *,
    published_event1_record: Mapping[str, Any] | None = None,
    published_reservations: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    valid, evidence = accepted_red._valid_v2_attempt_and_evidence()
    registry = (
        accepted_red.registry_owner
        .fresh_recovery_epoch001_current_step_requirement_registry()
    )
    return {
        "source_closure": deepcopy(valid["source_closure"]),
        "requirement_registry": registry,
        "cocolon_repository_snapshot": deepcopy(
            evidence["repository_snapshot"]
        ),
        "transport_capabilities": {
            "base_tree_read": True,
            "expected_old_sha_lease": True,
            "single_ref_update": True,
        },
        "published_event1_record": (
            deepcopy(published_event1_record)
            if published_event1_record is not None
            else None
        ),
        "published_reservations": [
            deepcopy(row) for row in (published_reservations or [])
        ],
        "published_failure_attempts": [],
    }


def _assert_parent_result(
    value: Mapping[str, Any],
    *,
    terminal_state: str,
    stop_code: str | None,
) -> None:
    assert set(value) == _PARENT_RESULT_KEYS
    assert value["protocol"] == _PARENT_PROTOCOL
    assert value["terminal_state"] == terminal_state
    assert value["stop_code"] == stop_code
    assert value["automatic_progression"] is False
    assert value["p2_authorized"] is False
    assert value["body_free"] is True


def test_formal_lane_red_authority_and_frozen_predecessors_are_exact() -> None:
    assert _AUTHORITY.endswith("_RED_FREEZE_ONLY")
    assert _KAREN_DIARY_ENTRY == "700f749f5149cac1f8bd4bab8a364d524a56985b"
    assert _COCOLON_ENTRY == "5722c4aea2e1d42d7f84e9b36e6322b538615bf2"
    assert _COCOLON_ENTRY_TREE == "a804fcbf4691ea9c842f1c8fa13b368f87836aa0"
    assert _MASHOS_API_ENTRY == "191e9d8be63132f10f94e2b2f54c6bae94ce1f07"
    assert _MASHOS_API_ENTRY_TREE == (
        "e68df6587b8cb674456b3bc9bceb23e0699f33aa"
    )
    assert _DESIGN_BLOB == "7e7d454d888141cbdb872244bf6df93c046e0b6c"
    assert _DESIGN_SHA256 == (
        "8bb377d49f04a33d6d21323a40bcd5ddc0d30eee8d4d2a2700ad7f074e32bb64"
    )
    assert _DETAILED_DESIGN_SHA256 == (
        "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
    )
    assert len(_MANIFEST_KEYS) == 15
    assert set(_TERMINAL_STATE_MATRIX) == {
        "SUCCESS",
        "A01",
        "A08",
        "A07",
        "INFRA",
    }
    assert len(_PROTECTED_SHA256) == 4
    for path, expected in _PROTECTED_SHA256.items():
        assert _sha256(_REPO_ROOT / path) == expected, path


def test_event2_manifest_production_builder_and_split_validators_or_red(
) -> None:
    publisher, verifier = _manifest_api_or_red()
    assert (
        publisher.RECOVERY_EPOCH001_ALL11_ATOMIC_PUBLICATION_MANIFEST_SCHEMA
        == _MANIFEST_SCHEMA
    )
    case = sequence_red._event2_case()
    builder = getattr(publisher, _MANIFEST_BUILDER)
    owner = getattr(publisher, _MANIFEST_OWNER)
    independent = getattr(verifier, _MANIFEST_VERIFIER)
    expected = case["artifacts_by_path"][sequence_red._MANIFEST_PATH]
    actual = builder(
        core_artifacts_by_path=_core_artifacts(case),
        source_baseline_event=deepcopy(
            case["publication_evidence"]["source_baseline_event"]["identity"]
        ),
        base_commit_sha1=case["bundle"]["base_commit_sha1"],
    )
    assert actual == expected
    assert set(actual) == _MANIFEST_KEYS
    kwargs = _manifest_validator_kwargs(case)
    assert _issue_codes(owner(actual, **kwargs)) == ()
    assert _issue_codes(independent(actual, **kwargs)) == ()


def test_coherently_rehashed_manifest_semantic_attacks_are_closed_or_red(
) -> None:
    publisher, verifier = sequence_red._publication_apis_or_red()
    attacks = (
        "CORE_COUNT",
        "EXTRA_KEY",
        "CORE_DUPLICATE",
        "CORE_ORDER",
        "CORE_SET_HASH",
        "SUPPORTING_COUNT",
        "CHANGED_COUNT",
        "EVENT_PATH",
        "REF_MODE",
        "BODY_FREE",
        "CANDIDATE",
        "CYCLE",
        "EPOCH",
        "SOURCE_EVENT",
        "BASE_COMMIT",
        "SELF_HASH",
        "MISSING_KEY",
    )
    reference = sequence_red._event2_case()
    unexpected: dict[str, dict[str, tuple[str, ...]]] = {}
    for attack in attacks:
        case = deepcopy(reference)
        _mutate_manifest(case, attack)
        phase_issues: dict[str, tuple[str, ...]] = {}
        for phase in ("supporting", "candidate", "published"):
            owner_issues, verifier_issues = sequence_red._publication_issues(
                publisher,
                verifier,
                phase,
                case,
            )
            phase_issues[f"owner_{phase}"] = owner_issues
            phase_issues[f"independent_{phase}"] = verifier_issues
        if any(
            issues != ("PUBLICATION_BUNDLE_INVALID",)
            for issues in phase_issues.values()
        ):
            unexpected[attack] = phase_issues
    assert unexpected == {}, unexpected


@pytest.mark.parametrize(
    "fixture_name",
    tuple(_TERMINAL_STATE_MATRIX),
)
def test_runner_owner_verifier_terminal_state_matrix_and_materialization_or_red(
    fixture_name: str,
) -> None:
    runner = _module_or_red(
        _RUNNER_PATH,
        "emlis_nls_v3_recovery_epoch001_current_step_proof_run_"
        f"{fixture_name.lower()}_red_target",
        "RECOVERY_EPOCH001_FORMAL_FAILURE_OUTCOME_STATE_NOT_ALIGNED",
    )
    verifier = _module_or_red(
        _VERIFIER_PATH,
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify_"
        f"{fixture_name.lower()}_red_target",
        "RECOVERY_EPOCH001_FORMAL_FAILURE_OUTCOME_STATE_NOT_ALIGNED",
    )
    attempt, evidence = _attempt_fixture(fixture_name)
    expected = _TERMINAL_STATE_MATRIX[fixture_name]
    runner_pair = runner._outcome_state_and_stop(
        counts=attempt["counts"],
        exit_code=attempt["exit_code"],
        timed_out=attempt["timed_out"],
    )
    owner_pair = accepted_red.accepted_owner._v2_outcome_state(
        counts=attempt["counts"],
        exit_code=attempt["exit_code"],
        timed_out=attempt["timed_out"],
    )
    independent_pair = verifier._v3_outcome_state(
        attempt["counts"],
        exit_code=attempt["exit_code"],
        timed_out=attempt["timed_out"],
    )
    assert runner_pair == owner_pair == independent_pair == expected

    registry = (
        accepted_red.registry_owner
        .fresh_recovery_epoch001_current_step_requirement_registry()
    )
    source_event = evidence["source_baseline_event"]["artifact"]
    materialized = (
        runner.materialize_recovery_epoch001_formal_test_run_attempt(
            worker_report=_worker_report(attempt, runner_pair),
            requirement_registry=registry,
            source_baseline_event=source_event,
            run_reservation=evidence["formal_test_run_reservation"],
            publication_evidence=evidence,
            repo_root=_REPO_ROOT,
        )
    )
    assert materialized is not None
    assert materialized["outcome_state"] == expected[0]
    assert materialized["stop_code"] == expected[1]
    assert _issue_codes(
        accepted_red.accepted_owner
        .validate_recovery_epoch001_formal_test_run_attempt_shape(
            materialized,
            repo_root=_REPO_ROOT,
            requirement_registry=registry,
        )
    ) == ()
    common = {
        "repo_root": _REPO_ROOT,
        "requirement_registry": registry,
        "source_baseline_event": source_event,
        "publication_evidence": evidence,
    }
    assert _issue_codes(
        verifier.verify_recovery_epoch001_formal_test_run_attempt(
            materialized,
            **common,
        )
    ) == ()


@pytest.mark.parametrize(
    ("terminal_kind", "exit_code", "timed_out"),
    (
        ("TIMEOUT", 124, True),
        ("POST_START_INFRA", 125, False),
    ),
)
def test_worker_terminal_checkpoint_preserves_exact134_failure_envelope_or_red(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    terminal_kind: str,
    exit_code: int,
    timed_out: bool,
) -> None:
    runner = _module_or_red(
        _RUNNER_PATH,
        "emlis_nls_v3_recovery_epoch001_current_step_proof_run_checkpoint_"
        f"{terminal_kind.lower()}_red_target",
        "RECOVERY_EPOCH001_FORMAL_FAILURE_OUTCOME_STATE_NOT_ALIGNED",
    )
    valid, _evidence = accepted_red._valid_v2_attempt_and_evidence()
    expected_nodes = list(valid["collection_node_ids"])
    checkpoint = {
        "collection_node_ids": expected_nodes,
        "executed_node_ids": [],
        "states": {},
        "collection_errors": 0,
        "exit_code": exit_code,
        "python_version": valid["runner_environment"]["python_version"],
        "pytest_version": valid["runner_environment"]["pytest_version"],
    }
    assert runner._valid_worker_result(
        checkpoint,
        expected_nodes=expected_nodes,
    )
    result_path = tmp_path / "worker-result.json"

    def fake_subprocess_run(
        command: list[str],
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[list[str]]:
        result_path.write_text(
            json.dumps(
                checkpoint,
                ensure_ascii=True,
                separators=(",", ":"),
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        if terminal_kind == "TIMEOUT":
            raise subprocess.TimeoutExpired(
                command,
                kwargs.get("timeout"),
            )
        return subprocess.CompletedProcess(command, returncode=2)

    monkeypatch.setattr(runner.subprocess, "run", fake_subprocess_run)
    actual, actual_timed_out = runner._run_exact134_worker(
        pinned_root=tmp_path,
        result_path=result_path,
        expected_nodes=expected_nodes,
    )
    assert actual_timed_out is timed_out
    assert actual == checkpoint
    pair = runner._outcome_state_and_stop(
        counts=runner._counts(
            expected_nodes=expected_nodes,
            collection_node_ids=actual["collection_node_ids"],
            executed_node_ids=actual["executed_node_ids"],
            states_by_node=actual["states"],
            collection_errors=actual["collection_errors"],
            timed_out=actual_timed_out,
        ),
        exit_code=actual["exit_code"],
        timed_out=actual_timed_out,
    )
    assert pair == (
        ("TIMED_OUT", "RUN_TIMED_OUT")
        if terminal_kind == "TIMEOUT"
        else ("INFRA_ERROR", "RUN_INFRA_ERROR")
    )


def test_formal_parent_surface_phase_order_and_terminal_lane_separation_or_red(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = _parent_module_or_red()
    assert parent.RECOVERY_EPOCH001_FORMAL_PARENT_PROTOCOL == _PARENT_PROTOCOL
    assert tuple(parent.RECOVERY_EPOCH001_FORMAL_PARENT_PHASE_ORDER) == (
        _PARENT_PHASE_ORDER
    )
    assert frozenset(
        parent.RECOVERY_EPOCH001_FORMAL_PARENT_TERMINAL_STATES
    ) == _PARENT_TERMINAL_STATES
    parameters = tuple(
        inspect.signature(
            parent.orchestrate_recovery_epoch001_formal_parent_lane
        ).parameters
    )
    assert parameters == (
        "authority_token",
        "event1_challenge_id",
        "formal_run_challenge_id",
        "admission_snapshot",
        "ports",
        "repo_root",
    )
    source = (_REPO_ROOT / _PARENT_MODULE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=_PARENT_MODULE_PATH)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not any(
        name == "subprocess"
        or name.startswith("git")
        or name.startswith("github")
        or name.startswith("ai.tests")
        or name.startswith("test_")
        for name in imported
    )
    production_children = parent._formal_parent_children()
    assert set(production_children) == _PARENT_CHILD_KEYS
    assert all(callable(value) for value in production_children.values())

    valid, evidence = accepted_red._valid_v2_attempt_and_evidence()
    scenarios = (
        (
            "SUCCESS",
            valid,
            (
                "STEP0_10_PREREQUISITES_PROVED",
                None,
            ),
            (
                ("publish", "EVENT1_EXACT2"),
                ("publish", "RESERVATION_EXACT1"),
                ("run", "attempt-001"),
                ("publish", "EVENT2_EXACT15"),
            ),
            {
                "prepare_failure_attempt_publication",
                "verify_failure_attempt_publication",
            },
        ),
        (
            "FAILURE",
            accepted_red._failure_attempt("A01"),
            (
                "FORMAL_FAILURE_ATTEMPT_PUBLISHED_STOP",
                "RUN_PARTIAL",
            ),
            (
                ("publish", "EVENT1_EXACT2"),
                ("publish", "RESERVATION_EXACT1"),
                ("run", "attempt-001"),
                ("publish", "FAILURE_ATTEMPT_EXACT1"),
            ),
            {
                "build_accepted_receipt",
                "verify_accepted_receipt",
                "build_step_receipts",
                "build_all11_chain",
                "build_atomic_manifest",
                "validate_atomic_manifest_owner",
                "verify_atomic_manifest_independent",
                "prepare_event2_publication",
                "verify_event2_publication",
            },
        ),
    )
    for (
        _name,
        run_result,
        terminal,
        expected_port_calls,
        forbidden_children,
    ) in scenarios:
        child_calls: list[str] = []
        children = _recording_children(child_calls)
        monkeypatch.setattr(
            parent,
            "_formal_parent_children",
            lambda children=children: children,
        )
        ports = _FakePorts(run_result)
        result = parent.orchestrate_recovery_epoch001_formal_parent_lane(
            authority_token=_AUTHORITY,
            event1_challenge_id="1" * 64,
            formal_run_challenge_id="2" * 64,
            admission_snapshot=_parent_admission(),
            ports=ports,
            repo_root=_REPO_ROOT,
        )
        _assert_parent_result(
            result,
            terminal_state=terminal[0],
            stop_code=terminal[1],
        )
        assert tuple(ports.calls) == expected_port_calls
        assert not (forbidden_children & set(child_calls))
        assert child_calls[0] == "admit_pre_event1"
        assert child_calls.index("validate_attempt_owner") < (
            child_calls.index("verify_attempt_independent")
        )

    consumed_reservation = evidence["formal_test_run_reservation"]
    consumed_authority = consumed_reservation["artifact"]["authority_token"]
    consumed_event1 = evidence["source_baseline_event"]
    ports = _FakePorts(valid)
    child_calls = []
    children = _recording_children(child_calls)
    monkeypatch.setattr(
        parent,
        "_formal_parent_children",
        lambda: children,
    )
    unknown = parent.orchestrate_recovery_epoch001_formal_parent_lane(
        authority_token=consumed_authority,
        event1_challenge_id=consumed_event1["artifact"]["challenge_id"],
        formal_run_challenge_id=consumed_reservation["artifact"][
            "challenge_id"
        ],
        admission_snapshot=_parent_admission(
            published_event1_record=consumed_event1,
            published_reservations=[consumed_reservation],
        ),
        ports=ports,
        repo_root=_REPO_ROOT,
    )
    _assert_parent_result(
        unknown,
        terminal_state="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        stop_code="ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
    )
    assert ports.calls == []
    assert not (
        {
            "prepare_reservation_publication",
            "validate_attempt_owner",
            "verify_attempt_independent",
            "prepare_failure_attempt_publication",
            "build_accepted_receipt",
            "prepare_event2_publication",
        }
        & set(child_calls)
    )


def test_new_red_and_formal_parent_are_in_current_completion_closure_or_red(
) -> None:
    closure = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT
    )
    required = {
        _THIS_PATH,
        _PARENT_MODULE_PATH,
        _PUBLISHER_PATH,
        _VERIFIER_PATH,
        _RUNNER_PATH,
    }
    paths = {
        row["path"]
        for row in closure.get("files", [])
        if type(row) is dict and type(row.get("path")) is str
    }
    completion = set(closure.get("views", {}).get("completion_proof", []))
    missing = sorted(required - paths)
    if missing or not required <= completion:
        pytest.fail(
            "RECOVERY_EPOCH001_FORMAL_PARENT_PROOF_CLOSURE_NOT_PROVED:"
            + ",".join(sorted((required - paths) | (required - completion))),
            pytrace=False,
        )
