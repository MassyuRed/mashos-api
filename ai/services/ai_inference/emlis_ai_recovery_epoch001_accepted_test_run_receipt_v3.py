# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free accepted-run provenance for Recovery Epoch 001.

This owner accepts only an exact134 proof run performed against a clean,
locked source baseline.  It derives the baseline identity from event 1 and
never accepts a caller-supplied baseline ID or result map.
"""

import hashlib
from pathlib import Path
import platform
import re
import subprocess
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    fresh_recovery_epoch001_canonical_current_closure,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    RECOVERY_EPOCH001_FORMAL_NODE_COUNT,
    fresh_recovery_epoch001_current_step_requirement_registry,
    validate_recovery_epoch001_current_step_requirement_registry_shape,
)


RECOVERY_EPOCH001_SOURCE_BASELINE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.source_baseline_event.v1"
)
RECOVERY_EPOCH001_SEQUENCE_EVENT_1 = "SOURCE_BASELINE_LOCKED"
RECOVERY_EPOCH001_SEQUENCE_EVENT_1_ORDINAL = 1
RECOVERY_EPOCH001_SEQUENCE_EVENT_2 = "STEP0_10_PREREQUISITES_PROVED"
RECOVERY_EPOCH001_SEQUENCE_EVENT_2_ORDINAL = 2
RECOVERY_EPOCH001_P2_AUTOMATIC_AUTHORIZATION = False
RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN: str | None = None
RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL = (
    "RECOVERY_EPOCH001_PYTEST_EXACT134_BODY_FREE_V1"
)
RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS = 3600
RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.accepted_test_run_receipt.v1"
)
RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_AUTHORITY_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BASELINE_EVENT_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_SOURCE_COMMIT_OR_TREE_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_COLLECTION_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_EXECUTED_NODE_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_PARTIAL",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_START_END_DRIFT",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_WORKTREE_NOT_CLEAN",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BODY_FREE_REQUIRED",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_HASH_MISMATCH",
    }
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")
_CHALLENGE_RE = re.compile(r"^[0-9a-f]{64}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:+-]{1,512}$")
_RUNNER_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
)
_PYTEST_OPTIONS = (
    "-q",
    "--disable-warnings",
    "-p",
    "no:cacheprovider",
)
_OUTCOME_STATES = frozenset(
    {"PASSED", "FAILED", "SKIPPED", "XFAILED", "XPASSED", "NOT_EXECUTED"}
)
_EVENT_KEYS = frozenset(
    {
        "schema_version",
        "event_name",
        "event_ordinal",
        "candidate_version_id",
        "recovery_epoch",
        "formal_p1_authority",
        "challenge_id",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "automatic_progression",
        "body_free",
        "event_sha256",
    }
)
_BINDING_KEYS = frozenset(
    {
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "worktree_clean",
    }
)
_COUNT_KEYS = frozenset(
    {
        "collected",
        "executed",
        "passed",
        "failed",
        "skipped",
        "xfailed",
        "xpassed",
        "deselected",
        "collection_errors",
        "timeouts",
    }
)
_OUTCOME_KEYS = frozenset(
    {
        "test_node_id",
        "source_path",
        "source_blob_sha1",
        "source_sha256",
        "result",
        "expected_closed_code",
        "actual_closed_code",
        "evidence_sha256",
    }
)
_PROOF_SOURCE_KEYS = frozenset(
    {"path", "git_blob_sha1", "sha256"}
)
_RUNNER_ENVIRONMENT_KEYS = frozenset(
    {
        "protocol",
        "python_version",
        "pytest_version",
        "plugin_autoload_disabled",
        "runner_path",
        "runner_git_blob_sha1",
        "runner_sha256",
        "worker_isolated",
        "source_materialization",
        "pytest_addopts_ignored",
        "pytest_plugins_ignored",
        "timeout_seconds",
        "worker_argv_sha256",
        "environment_profile_sha256",
    }
)
_PROOF_RUN_KEYS = frozenset(
    {
        "protocol",
        "candidate_version_id",
        "recovery_epoch",
        "source_baseline_event_sha256",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "formal_node_registry_sha256",
        "collection_node_ids",
        "executed_node_ids",
        "runner_environment",
        "run_start",
        "run_end",
        "outcomes",
        "counts",
        "exit_code",
        "timed_out",
        "body_free",
        "proof_run_sha256",
    }
)
_TOP_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "recovery_epoch",
        "authority_token",
        "challenge_id",
        "source_baseline_event_sha256",
        "baseline_id",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "step_view_sha256_by_step",
        "registry_sha256",
        "formal_node_registry_sha256",
        "collection_node_ids",
        "collection_sha256",
        "executed_node_ids",
        "executed_node_sha256",
        "proof_sources",
        "proof_source_closure_sha256",
        "proof_run_sha256",
        "runner_environment",
        "run_start",
        "run_end",
        "outcomes",
        "counts",
        "exit_code",
        "timed_out",
        "accepted",
        "body_free",
        "accepted_test_run_receipt_sha256",
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
            lowered = key.lower()
            if any(
                token in lowered
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
            ):
                return False
            if not _body_free(item, seen):
                return False
        return True
    finally:
        seen.remove(identity)


def _git_identity(repo_root: Path) -> tuple[str, str, bool]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout
    if _COMMIT_RE.fullmatch(head) is None or _COMMIT_RE.fullmatch(tree) is None:
        raise ValueError("git_identity_invalid")
    return head, tree, status == ""


def _material(value: Mapping[str, Any], hash_key: str) -> dict[str, Any]:
    return {key: value[key] for key in sorted(set(value) - {hash_key})}


def _valid_hash(value: Any) -> bool:
    return type(value) is str and _SHA_RE.fullmatch(value) is not None


def _valid_blob(value: Any) -> bool:
    return type(value) is str and _BLOB_RE.fullmatch(value) is not None


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload,
        usedforsecurity=False,
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _closure_file_rows(
    closure: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    rows = closure.get("files")
    if type(rows) is not list:
        return {}
    return {
        row["path"]: row
        for row in rows
        if type(row) is dict
        and type(row.get("path")) is str
        and set(row) == {"path", "role", "sha256", "git_blob_sha1"}
    }


def _expected_counts(
    *,
    expected_nodes: list[str],
    collection: list[str],
    executed: list[str],
    outcomes: list[Mapping[str, Any]],
    collection_errors: int,
    timed_out: bool,
) -> dict[str, int]:
    states = {
        row["test_node_id"]: row["result"]
        for row in outcomes
        if type(row) is dict
        and type(row.get("test_node_id")) is str
        and type(row.get("result")) is str
    }
    ordered_states = [
        states.get(node_id, "NOT_EXECUTED") for node_id in expected_nodes
    ]
    return {
        "collected": len(collection),
        "executed": len(
            [node_id for node_id in expected_nodes if node_id in executed]
        ),
        "passed": ordered_states.count("PASSED"),
        "failed": (
            ordered_states.count("FAILED")
            + ordered_states.count("NOT_EXECUTED")
        ),
        "skipped": ordered_states.count("SKIPPED"),
        "xfailed": ordered_states.count("XFAILED"),
        "xpassed": ordered_states.count("XPASSED"),
        "deselected": max(0, len(collection) - len(expected_nodes)),
        "collection_errors": collection_errors,
        "timeouts": 1 if timed_out else 0,
    }


def _proof_material_from_receipt(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "protocol": value["runner_environment"]["protocol"],
        "candidate_version_id": value["candidate_version_id"],
        "recovery_epoch": value["recovery_epoch"],
        "source_baseline_event_sha256": value[
            "source_baseline_event_sha256"
        ],
        "source_commit": value["source_commit"],
        "source_tree": value["source_tree"],
        "canonical_current_closure_sha256": value[
            "canonical_current_closure_sha256"
        ],
        "source_dependency_closure_sha256": value[
            "source_dependency_closure_sha256"
        ],
        "registry_sha256": value["registry_sha256"],
        "formal_node_registry_sha256": value[
            "formal_node_registry_sha256"
        ],
        "collection_node_ids": value["collection_node_ids"],
        "executed_node_ids": value["executed_node_ids"],
        "runner_environment": value["runner_environment"],
        "run_start": value["run_start"],
        "run_end": value["run_end"],
        "outcomes": value["outcomes"],
        "counts": value["counts"],
        "exit_code": value["exit_code"],
        "timed_out": value["timed_out"],
        "body_free": value["body_free"],
    }


def _event_valid(
    event: Any,
    *,
    closure: Mapping[str, Any],
    registry: Mapping[str, Any],
    source_commit: str,
    source_tree: str,
) -> bool:
    if type(event) is not dict or set(event) != _EVENT_KEYS:
        return False
    if (
        event.get("schema_version")
        != RECOVERY_EPOCH001_SOURCE_BASELINE_EVENT_SCHEMA
        or event.get("event_name") != RECOVERY_EPOCH001_SEQUENCE_EVENT_1
        or event.get("event_ordinal")
        != RECOVERY_EPOCH001_SEQUENCE_EVENT_1_ORDINAL
        or event.get("candidate_version_id")
        != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
        or event.get("recovery_epoch") != 1
        or RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN is None
        or event.get("formal_p1_authority")
        != RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN
        or _CHALLENGE_RE.fullmatch(str(event.get("challenge_id", "")))
        is None
        or event.get("source_commit") != source_commit
        or event.get("source_tree") != source_tree
        or event.get("canonical_current_closure_sha256")
        != closure.get("canonical_current_closure_sha256")
        or event.get("source_dependency_closure_sha256")
        != closure.get("source_dependency_closure_sha256")
        or event.get("registry_sha256") != registry.get("registry_sha256")
        or event.get("automatic_progression") is not False
        or event.get("body_free") is not True
        or not _body_free(event)
    ):
        return False
    try:
        expected_hash = artifact_sha256(_material(event, "event_sha256"))
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        return False
    return event.get("event_sha256") == expected_hash


def build_recovery_epoch001_source_baseline_event(
    *,
    formal_p1_authority: str,
    challenge_id: str,
    requirement_registry: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build event 1 only for a clean, final, separately authorized P1 tree."""

    if (
        RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN is None
        or formal_p1_authority
        != RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN
        or _CHALLENGE_RE.fullmatch(str(challenge_id)) is None
    ):
        raise ValueError(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_AUTHORITY_INVALID"
        )
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=root,
    ):
        raise ValueError(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH"
        )
    closure = fresh_recovery_epoch001_canonical_current_closure(repo_root=root)
    source_commit, source_tree, clean = _git_identity(root)
    if not clean:
        raise ValueError(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_WORKTREE_NOT_CLEAN"
        )
    event: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH001_SOURCE_BASELINE_EVENT_SCHEMA,
        "event_name": RECOVERY_EPOCH001_SEQUENCE_EVENT_1,
        "event_ordinal": RECOVERY_EPOCH001_SEQUENCE_EVENT_1_ORDINAL,
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "recovery_epoch": 1,
        "formal_p1_authority": formal_p1_authority,
        "challenge_id": challenge_id,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "registry_sha256": registry["registry_sha256"],
        "automatic_progression": False,
        "body_free": True,
    }
    event["event_sha256"] = artifact_sha256(event)
    if not _event_valid(
        event,
        closure=closure,
        registry=registry,
        source_commit=source_commit,
        source_tree=source_tree,
    ):
        raise ValueError(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BASELINE_EVENT_INVALID"
        )
    return event


def _formal_nodes(registry: Mapping[str, Any]) -> list[str]:
    steps = registry.get("steps")
    if type(steps) is not list:
        return []
    return [
        node
        for row in steps
        if type(row) is dict
        for node in row.get("formal_completion_node_ids", [])
        if type(node) is str
    ]


def _expected_worker_argv_sha256(nodes: list[str]) -> str:
    return artifact_sha256(
        {
            "python_flags": ["-I", "-B"],
            "runner_path": _RUNNER_PATH,
            "worker_mode": "--internal-exact134-child",
            "node_ids": nodes,
            "pytest_options": list(_PYTEST_OPTIONS),
        }
    )


def _proof_run_issues(
    proof_run: Any,
    *,
    registry: Mapping[str, Any],
    event: Mapping[str, Any],
    closure: Mapping[str, Any],
    source_commit: str,
    source_tree: str,
    clean: bool,
    repo_root: Path,
) -> set[str]:
    issues: set[str] = set()
    if type(proof_run) is not dict or set(proof_run) != _PROOF_RUN_KEYS:
        return {"RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID"}
    expected_nodes = _formal_nodes(registry)
    if (
        proof_run.get("protocol")
        != RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL
        or proof_run.get("candidate_version_id")
        != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
        or proof_run.get("recovery_epoch") != 1
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID")
    collection = proof_run.get("collection_node_ids")
    executed = proof_run.get("executed_node_ids")
    if (
        len(expected_nodes) != RECOVERY_EPOCH001_FORMAL_NODE_COUNT
        or type(collection) is not list
        or collection != expected_nodes
        or len(collection) != len(set(collection))
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_COLLECTION_MISMATCH")
        collection = []
    if (
        type(executed) is not list
        or executed != expected_nodes
        or len(executed) != len(set(executed))
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_EXECUTED_NODE_MISMATCH")
        executed = []
    if (
        proof_run.get("source_baseline_event_sha256")
        != event.get("event_sha256")
        or proof_run.get("source_commit") != source_commit
        or proof_run.get("source_tree") != source_tree
    ):
        issues.add(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_SOURCE_COMMIT_OR_TREE_MISMATCH"
        )
    if (
        proof_run.get("canonical_current_closure_sha256")
        != closure.get("canonical_current_closure_sha256")
        or proof_run.get("source_dependency_closure_sha256")
        != closure.get("source_dependency_closure_sha256")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH")
    if (
        proof_run.get("registry_sha256") != registry.get("registry_sha256")
        or proof_run.get("formal_node_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH")
    start = proof_run.get("run_start")
    end = proof_run.get("run_end")
    expected_binding = {
        "source_commit": source_commit,
        "source_tree": source_tree,
        "canonical_current_closure_sha256": (
            closure.get("canonical_current_closure_sha256")
        ),
        "source_dependency_closure_sha256": (
            closure.get("source_dependency_closure_sha256")
        ),
        "registry_sha256": registry.get("registry_sha256"),
        "worktree_clean": True,
    }
    if (
        type(start) is not dict
        or type(end) is not dict
        or set(start) != _BINDING_KEYS
        or set(end) != _BINDING_KEYS
        or start != end
        or start != expected_binding
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_START_END_DRIFT")
    if not clean:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_WORKTREE_NOT_CLEAN")
    files = _closure_file_rows(closure)
    negative_codes = {
        row["independent_negative_proof"]["test_node_id"]: (
            row["independent_negative_proof"]["expected_closed_code"]
        )
        for row in registry.get("steps", [])
        if type(row) is dict
        and type(row.get("independent_negative_proof")) is dict
    }
    outcomes = proof_run.get("outcomes")
    if (
        type(outcomes) is not list
        or len(outcomes) != RECOVERY_EPOCH001_FORMAL_NODE_COUNT
        or [
            item.get("test_node_id")
            for item in outcomes
            if type(item) is dict
        ]
        != expected_nodes
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
        outcomes = []
    for outcome in outcomes:
        node_id = outcome.get("test_node_id") if type(outcome) is dict else None
        source_path = (
            outcome.get("source_path") if type(outcome) is dict else None
        )
        source_row = (
            files.get(source_path) if type(source_path) is str else None
        )
        source_file = repo_root / str(source_path)
        expected_closed_code = negative_codes.get(node_id)
        if (
            type(outcome) is not dict
            or set(outcome) != _OUTCOME_KEYS
            or node_id not in expected_nodes
            or source_path != str(node_id).partition("::")[0]
            or source_row is None
            or not source_file.is_file()
            or outcome.get("source_blob_sha1")
            != source_row.get("git_blob_sha1")
            or outcome.get("source_blob_sha1")
            != _git_blob_sha1(source_file)
            or not _valid_blob(outcome.get("source_blob_sha1"))
            or outcome.get("source_sha256") != source_row.get("sha256")
            or outcome.get("source_sha256") != _file_sha256(source_file)
            or not _valid_hash(outcome.get("source_sha256"))
            or outcome.get("result") not in _OUTCOME_STATES
            or outcome.get("expected_closed_code") != expected_closed_code
            or outcome.get("actual_closed_code")
            != (
                expected_closed_code
                if expected_closed_code is not None
                and outcome.get("result") == "PASSED"
                else None
            )
            or not _valid_hash(outcome.get("evidence_sha256"))
        ):
            issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
            continue
        try:
            outcome_hash = artifact_sha256(
                _material(outcome, "evidence_sha256")
            )
        except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
            outcome_hash = None
        if outcome.get("evidence_sha256") != outcome_hash:
            issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    counts = proof_run.get("counts")
    collection_errors = (
        counts.get("collection_errors") if type(counts) is dict else None
    )
    timed_out = proof_run.get("timed_out")
    expected_counts = (
        _expected_counts(
            expected_nodes=expected_nodes,
            collection=collection,
            executed=executed,
            outcomes=outcomes,
            collection_errors=collection_errors,
            timed_out=timed_out,
        )
        if type(collection_errors) is int
        and not isinstance(collection_errors, bool)
        and collection_errors >= 0
        and type(timed_out) is bool
        else None
    )
    if (
        type(counts) is not dict
        or set(counts) != _COUNT_KEYS
        or counts != expected_counts
        or type(proof_run.get("exit_code")) is not int
        or isinstance(proof_run.get("exit_code"), bool)
        or timed_out is not False
        or counts.get("timeouts") != 0
        or counts.get("collection_errors") != 0
        or (
            counts.get("passed") == RECOVERY_EPOCH001_FORMAL_NODE_COUNT
            and proof_run.get("exit_code") != 0
        )
        or (
            counts.get("failed", 0) > 0
            and proof_run.get("exit_code") == 0
        )
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_PARTIAL")
    environment = proof_run.get("runner_environment")
    runner_row = files.get(_RUNNER_PATH)
    runner_file = repo_root / _RUNNER_PATH
    if (
        type(environment) is not dict
        or set(environment) != _RUNNER_ENVIRONMENT_KEYS
        or environment.get("protocol")
        != RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL
        or environment.get("plugin_autoload_disabled") is not True
        or environment.get("runner_path") != _RUNNER_PATH
        or runner_row is None
        or not runner_file.is_file()
        or environment.get("runner_git_blob_sha1")
        != runner_row.get("git_blob_sha1")
        or environment.get("runner_git_blob_sha1")
        != _git_blob_sha1(runner_file)
        or environment.get("runner_sha256") != runner_row.get("sha256")
        or environment.get("runner_sha256") != _file_sha256(runner_file)
        or environment.get("worker_isolated") is not True
        or environment.get("source_materialization")
        != "DETACHED_PINNED_GIT_WORKTREE"
        or environment.get("pytest_addopts_ignored") is not True
        or environment.get("pytest_plugins_ignored") is not True
        or environment.get("timeout_seconds")
        != RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS
        or environment.get("worker_argv_sha256")
        != _expected_worker_argv_sha256(expected_nodes)
        or not _valid_hash(environment.get("environment_profile_sha256"))
        or environment.get("python_version") != platform.python_version()
        or type(environment.get("pytest_version")) is not str
        or not environment.get("pytest_version")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    if proof_run.get("body_free") is not True or not _body_free(proof_run):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BODY_FREE_REQUIRED")
    try:
        proof_hash = artifact_sha256(
            _material(proof_run, "proof_run_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        proof_hash = None
    if proof_run.get("proof_run_sha256") != proof_hash:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_HASH_MISMATCH")
    return issues


def _proof_sources(outcomes: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    by_path: dict[str, dict[str, str]] = {}
    for outcome in outcomes:
        path = outcome["source_path"]
        row = {
            "path": path,
            "git_blob_sha1": outcome["source_blob_sha1"],
            "sha256": outcome["source_sha256"],
        }
        previous = by_path.setdefault(path, row)
        if previous != row:
            raise ValueError(
                "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID"
            )
    return [by_path[path] for path in sorted(by_path)]


def build_recovery_epoch001_accepted_test_run_receipt(
    *,
    proof_run: Mapping[str, Any],
    requirement_registry: Mapping[str, Any],
    source_baseline_event: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Derive an accepted-run receipt from event 1 and exact134 evidence."""

    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=root,
    ):
        raise ValueError(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH"
        )
    closure = fresh_recovery_epoch001_canonical_current_closure(repo_root=root)
    source_commit, source_tree, clean = _git_identity(root)
    event = dict(source_baseline_event)
    if not _event_valid(
        event,
        closure=closure,
        registry=registry,
        source_commit=source_commit,
        source_tree=source_tree,
    ):
        raise ValueError(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BASELINE_EVENT_INVALID"
        )
    run = dict(proof_run)
    proof_issues = _proof_run_issues(
        run,
        registry=registry,
        event=event,
        closure=closure,
        source_commit=source_commit,
        source_tree=source_tree,
        clean=clean,
        repo_root=root,
    )
    if proof_issues:
        raise ValueError(sorted(proof_issues)[0])
    outcomes = [dict(item) for item in run["outcomes"]]
    proof_sources = _proof_sources(outcomes)
    collection = list(run["collection_node_ids"])
    executed = list(run["executed_node_ids"])
    receipt: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA,
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "recovery_epoch": 1,
        "authority_token": event["formal_p1_authority"],
        "challenge_id": event["challenge_id"],
        "source_baseline_event_sha256": event["event_sha256"],
        "baseline_id": event["event_sha256"],
        "source_commit": source_commit,
        "source_tree": source_tree,
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "step_view_sha256_by_step": {
            str(step): artifact_sha256(closure["step_views"][f"step_{step}"])
            for step in range(11)
        },
        "registry_sha256": registry["registry_sha256"],
        "formal_node_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "collection_node_ids": collection,
        "collection_sha256": artifact_sha256({"node_ids": collection}),
        "executed_node_ids": executed,
        "executed_node_sha256": artifact_sha256({"node_ids": executed}),
        "proof_sources": proof_sources,
        "proof_source_closure_sha256": artifact_sha256(proof_sources),
        "proof_run_sha256": run["proof_run_sha256"],
        "runner_environment": dict(run["runner_environment"]),
        "run_start": dict(run["run_start"]),
        "run_end": dict(run["run_end"]),
        "outcomes": outcomes,
        "counts": dict(run["counts"]),
        "exit_code": run["exit_code"],
        "timed_out": run["timed_out"],
        "accepted": True,
        "body_free": True,
    }
    receipt["accepted_test_run_receipt_sha256"] = artifact_sha256(receipt)
    issues = validate_recovery_epoch001_accepted_test_run_receipt_shape(
        receipt,
        requirement_registry=registry,
        source_baseline_event=event,
        repo_root=root,
    )
    if issues:
        raise ValueError(issues[0])
    return receipt


def _validate_recovery_epoch001_accepted_test_run_receipt_shape_impl(
    value: Any,
    *,
    requirement_registry: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Independently recompute accepted-run provenance from current bytes."""

    if type(value) is not dict:
        return ("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _TOP_KEYS:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID")
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = (
        fresh_recovery_epoch001_current_step_requirement_registry()
        if requirement_registry is None
        else dict(requirement_registry)
    )
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=root,
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH")
    try:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=root
        )
        source_commit, source_tree, clean = _git_identity(root)
    except (
        FileNotFoundError,
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
    ):
        closure = {}
        source_commit = ""
        source_tree = ""
        clean = False
    event = (
        dict(source_baseline_event)
        if type(source_baseline_event) is dict
        else {}
    )
    if not _event_valid(
        event,
        closure=closure,
        registry=registry,
        source_commit=source_commit,
        source_tree=source_tree,
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BASELINE_EVENT_INVALID")
    if (
        value.get("schema_version")
        != RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA
        or value.get("candidate_version_id")
        != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
        or value.get("recovery_epoch") != 1
        or value.get("authority_token") != event.get("formal_p1_authority")
        or value.get("challenge_id") != event.get("challenge_id")
        or value.get("source_baseline_event_sha256")
        != event.get("event_sha256")
        or value.get("baseline_id") != event.get("event_sha256")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_AUTHORITY_INVALID")
    if (
        value.get("source_commit") != source_commit
        or value.get("source_tree") != source_tree
    ):
        issues.add(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_SOURCE_COMMIT_OR_TREE_MISMATCH"
        )
    if (
        value.get("canonical_current_closure_sha256")
        != closure.get("canonical_current_closure_sha256")
        or value.get("source_dependency_closure_sha256")
        != closure.get("source_dependency_closure_sha256")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH")
    expected_views = (
        {
            str(step): artifact_sha256(
                closure.get("step_views", {}).get(f"step_{step}")
            )
            for step in range(11)
        }
        if type(closure.get("step_views")) is dict
        else {}
    )
    if value.get("step_view_sha256_by_step") != expected_views:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH")
    expected_nodes = _formal_nodes(registry)
    collection = value.get("collection_node_ids")
    executed = value.get("executed_node_ids")
    if (
        type(collection) is not list
        or value.get("collection_sha256")
        != artifact_sha256({"node_ids": collection})
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_COLLECTION_MISMATCH")
    if (
        type(executed) is not list
        or value.get("executed_node_sha256")
        != artifact_sha256({"node_ids": executed})
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_EXECUTED_NODE_MISMATCH")
    if (
        value.get("registry_sha256") != registry.get("registry_sha256")
        or value.get("formal_node_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH")
    outcomes = value.get("outcomes")
    if (
        type(outcomes) is not list
        or len(outcomes) != RECOVERY_EPOCH001_FORMAL_NODE_COUNT
        or [
            row.get("test_node_id")
            for row in outcomes
            if type(row) is dict
        ]
        != expected_nodes
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
        outcomes = []
    try:
        proof_sources = _proof_sources(outcomes)
    except (KeyError, TypeError, ValueError):
        proof_sources = []
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    if (
        value.get("proof_sources") != proof_sources
        or value.get("proof_source_closure_sha256")
        != artifact_sha256(proof_sources)
        or any(
            type(row) is not dict or set(row) != _PROOF_SOURCE_KEYS
            for row in proof_sources
        )
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    try:
        proof_candidate = {
            **_proof_material_from_receipt(value),
            "proof_run_sha256": value["proof_run_sha256"],
        }
        issues.update(
            _proof_run_issues(
                proof_candidate,
                registry=registry,
                event=event,
                closure=closure,
                source_commit=source_commit,
                source_tree=source_tree,
                clean=clean,
                repo_root=root,
            )
        )
    except (
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID")
    if value.get("accepted") is not True:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_PARTIAL")
    if value.get("body_free") is not True or not _body_free(value):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BODY_FREE_REQUIRED")
    try:
        expected_hash = artifact_sha256(
            _material(value, "accepted_test_run_receipt_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("accepted_test_run_receipt_sha256") != expected_hash
        or not _valid_hash(value.get("accepted_test_run_receipt_sha256"))
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_recovery_epoch001_accepted_test_run_receipt_shape(
    value: Any,
    *,
    requirement_registry: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    try:
        return _validate_recovery_epoch001_accepted_test_run_receipt_shape_impl(
            value,
            requirement_registry=requirement_registry,
            source_baseline_event=source_baseline_event,
            repo_root=repo_root,
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",)
