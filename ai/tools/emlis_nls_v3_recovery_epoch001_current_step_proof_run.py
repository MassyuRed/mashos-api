#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run the literal Recovery Epoch 001 exact134 proof denominator.

The runner is inert until called by a separately authorized formal P1 lane.
It disables third-party pytest autoload, selects every frozen node explicitly,
and returns only body-free node outcomes and start/end source bindings.
"""

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any, Mapping


_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TEST_HELPERS_ROOT = _REPO_ROOT / "ai" / "tests" / "helpers"
for _path in (str(_INFERENCE_ROOT), str(_TEST_HELPERS_ROOT)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    fresh_recovery_epoch001_canonical_current_closure,
    validate_recovery_epoch001_canonical_current_closure_shape,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    RECOVERY_EPOCH001_FORMAL_NODE_COUNT,
    fresh_recovery_epoch001_current_step_requirement_registry,
    validate_recovery_epoch001_current_step_requirement_registry_shape,
)


RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL = (
    "RECOVERY_EPOCH001_PYTEST_EXACT134_BODY_FREE_V1"
)
RECOVERY_EPOCH001_FORMAL_NODE_COUNT = 134
RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS = 3600
RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN: str | None = None
RECOVERY_EPOCH001_PROOF_ENVIRONMENT_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID",
        "RECOVERY_PROOF_ENVIRONMENT_WORKTREE_NOT_CLEAN",
        "RECOVERY_PROOF_ENVIRONMENT_BASELINE_EVENT_INVALID",
        "RECOVERY_PROOF_ENVIRONMENT_CLOSURE_INVALID",
        "RECOVERY_PROOF_ENVIRONMENT_REGISTRY_INVALID",
        "RECOVERY_PROOF_ENVIRONMENT_NODE_SET_INVALID",
    }
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:+-]{1,512}$")
_BASELINE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001.source_baseline_event.v1"
)
_BASELINE_EVENT_NAME = "SOURCE_BASELINE_LOCKED"
_RUNNER_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
)
_CHALLENGE_RE = re.compile(r"^[0-9a-f]{64}$")
_WORKER_RESULT_KEYS = frozenset(
    {
        "collection_node_ids",
        "executed_node_ids",
        "states",
        "collection_errors",
        "exit_code",
        "python_version",
        "pytest_version",
    }
)
_WORKER_ENVIRONMENT_FIXED = {
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
}
_WORKER_ENVIRONMENT_REMOVED = (
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
)
_PYTEST_OPTIONS = (
    "-q",
    "--disable-warnings",
    "-p",
    "no:cacheprovider",
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
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    source_tree = subprocess.run(
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
    if (
        _COMMIT_RE.fullmatch(source_commit) is None
        or _COMMIT_RE.fullmatch(source_tree) is None
    ):
        raise ValueError("RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID")
    return source_commit, source_tree, status == ""


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload,
        usedforsecurity=False,
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def collect_recovery_epoch001_current_step_proof_nodes() -> tuple[str, ...]:
    """Return Step 0--10 nodes, with each dedicated negative last."""

    registry = fresh_recovery_epoch001_current_step_requirement_registry()
    return tuple(_formal_nodes(registry))


def _source_binding(
    *,
    repo_root: Path,
    closure: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> dict[str, Any]:
    source_commit, source_tree, clean = _git_identity(repo_root)
    return {
        "source_commit": source_commit,
        "source_tree": source_tree,
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "registry_sha256": registry["registry_sha256"],
        "worktree_clean": clean,
    }


def _baseline_event_valid(
    event: Any,
    *,
    binding: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> bool:
    return (
        type(event) is dict
        and event.get("schema_version") == _BASELINE_EVENT_SCHEMA
        and event.get("event_name") == _BASELINE_EVENT_NAME
        and event.get("event_ordinal") == 1
        and event.get("candidate_version_id")
        == RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
        and event.get("recovery_epoch") == 1
        and event.get("source_commit") == binding.get("source_commit")
        and event.get("source_tree") == binding.get("source_tree")
        and event.get("canonical_current_closure_sha256")
        == binding.get("canonical_current_closure_sha256")
        and event.get("source_dependency_closure_sha256")
        == binding.get("source_dependency_closure_sha256")
        and event.get("registry_sha256") == registry.get("registry_sha256")
        and RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN is not None
        and event.get("formal_p1_authority")
        == RECOVERY_EPOCH001_SELECTED_FORMAL_P1_AUTHORITY_TOKEN
        and _CHALLENGE_RE.fullmatch(str(event.get("challenge_id", "")))
        is not None
        and event.get("automatic_progression") is False
        and event.get("body_free") is True
        and _body_free(event)
        and _SHA_RE.fullmatch(str(event.get("event_sha256", ""))) is not None
        and event.get("event_sha256")
        == artifact_sha256(
            {
                key: event[key]
                for key in sorted(set(event) - {"event_sha256"})
            }
        )
    )


def validate_recovery_epoch001_proof_environment(
    *,
    requirement_registry: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Validate clean-tree, event-1, closure, registry, and exact134 entry."""

    issues: set[str] = set()
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
        issues.add("RECOVERY_PROOF_ENVIRONMENT_REGISTRY_INVALID")
    try:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=root
        )
        if validate_recovery_epoch001_canonical_current_closure_shape(
            closure,
            repo_root=root,
        ):
            issues.add("RECOVERY_PROOF_ENVIRONMENT_CLOSURE_INVALID")
        binding = _source_binding(
            repo_root=root,
            closure=closure,
            registry=registry,
        )
    except (
        FileNotFoundError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ):
        issues.add("RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID")
        binding = {}
    if binding.get("worktree_clean") is not True:
        issues.add("RECOVERY_PROOF_ENVIRONMENT_WORKTREE_NOT_CLEAN")
    if not _baseline_event_valid(
        source_baseline_event,
        binding=binding,
        registry=registry,
    ):
        issues.add("RECOVERY_PROOF_ENVIRONMENT_BASELINE_EVENT_INVALID")
    nodes = _formal_nodes(registry)
    if (
        len(nodes) != RECOVERY_EPOCH001_FORMAL_NODE_COUNT
        or len(nodes) != len(set(nodes))
        or tuple(nodes)
        != collect_recovery_epoch001_current_step_proof_nodes()
    ):
        issues.add("RECOVERY_PROOF_ENVIRONMENT_NODE_SET_INVALID")
    for node_id in nodes:
        source_path, separator, function_name = node_id.partition("::")
        path = root / source_path
        if (
            separator != "::"
            or not function_name.startswith("test_")
            or not path.is_file()
        ):
            issues.add("RECOVERY_PROOF_ENVIRONMENT_NODE_SET_INVALID")
    return tuple(sorted(issues))


class _BodyFreePytestCapture:
    """Minimal worker plugin; it never retains longrepr or captured text."""

    def __init__(self) -> None:
        self.collected: list[str] = []
        self.executed: list[str] = []
        self.states: dict[str, str] = {}
        self.collection_errors = 0

    def pytest_collection_finish(self, session: Any) -> None:
        self.collected = [item.nodeid for item in session.items]

    def pytest_collectreport(self, report: Any) -> None:
        if report.failed:
            self.collection_errors += 1

    def pytest_runtest_logreport(self, report: Any) -> None:
        node_id = report.nodeid
        if report.when == "call" and node_id not in self.executed:
            self.executed.append(node_id)
        was_xfail = bool(getattr(report, "wasxfail", False))
        if report.failed:
            self.states[node_id] = "FAILED"
        elif report.skipped:
            self.states[node_id] = "XFAILED" if was_xfail else "SKIPPED"
        elif report.when == "call":
            self.states[node_id] = "XPASSED" if was_xfail else "PASSED"


def _negative_codes_by_node(
    registry: Mapping[str, Any],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in registry["steps"]:
        proof = row["independent_negative_proof"]
        result[proof["test_node_id"]] = proof["expected_closed_code"]
    return result


def _outcomes(
    *,
    node_ids: list[str],
    states: Mapping[str, str],
    negative_codes: Mapping[str, str],
    repo_root: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for node_id in node_ids:
        source_path = node_id.partition("::")[0]
        path = repo_root / source_path
        expected_closed_code = negative_codes.get(node_id)
        row: dict[str, Any] = {
            "test_node_id": node_id,
            "source_path": source_path,
            "source_blob_sha1": _git_blob_sha1(path),
            "source_sha256": _file_sha256(path),
            "result": states.get(node_id, "NOT_EXECUTED"),
            "expected_closed_code": expected_closed_code,
            "actual_closed_code": (
                expected_closed_code
                if expected_closed_code is not None
                and states.get(node_id) == "PASSED"
                else None
            ),
        }
        row["evidence_sha256"] = artifact_sha256(row)
        rows.append(row)
    return rows


def _counts(
    *,
    expected_nodes: list[str],
    collection_node_ids: list[str],
    executed_node_ids: list[str],
    states_by_node: Mapping[str, str],
    collection_errors: int,
    timed_out: bool,
) -> dict[str, int]:
    states = [
        states_by_node.get(node, "NOT_EXECUTED") for node in expected_nodes
    ]
    return {
        "collected": len(collection_node_ids),
        "executed": len(
            [node for node in expected_nodes if node in executed_node_ids]
        ),
        "passed": states.count("PASSED"),
        "failed": states.count("FAILED") + states.count("NOT_EXECUTED"),
        "skipped": states.count("SKIPPED"),
        "xfailed": states.count("XFAILED"),
        "xpassed": states.count("XPASSED"),
        "deselected": max(0, len(collection_node_ids) - len(expected_nodes)),
        "collection_errors": collection_errors,
        "timeouts": 1 if timed_out else 0,
    }


def _worker_environment() -> dict[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        **_WORKER_ENVIRONMENT_FIXED,
    }
    return environment


def _worker_environment_profile_sha256(environment: Mapping[str, str]) -> str:
    return artifact_sha256(
        {
            "fixed": dict(_WORKER_ENVIRONMENT_FIXED),
            "removed": list(_WORKER_ENVIRONMENT_REMOVED),
            "inherited_path_sha256": hashlib.sha256(
                environment["PATH"].encode("utf-8")
            ).hexdigest(),
            "lang": environment["LANG"],
            "lc_all": environment["LC_ALL"],
        }
    )


def _worker_argv_sha256(nodes: list[str]) -> str:
    return artifact_sha256(
        {
            "python_flags": ["-I", "-B"],
            "runner_path": _RUNNER_PATH,
            "worker_mode": "--internal-exact134-child",
            "node_ids": nodes,
            "pytest_options": list(_PYTEST_OPTIONS),
        }
    )


def _valid_worker_result(
    value: Any,
    *,
    expected_nodes: list[str],
) -> bool:
    if type(value) is not dict or set(value) != _WORKER_RESULT_KEYS:
        return False
    collection = value.get("collection_node_ids")
    executed = value.get("executed_node_ids")
    states = value.get("states")
    if (
        type(collection) is not list
        or any(type(item) is not str for item in collection)
        or len(collection) != len(set(collection))
        or type(executed) is not list
        or any(type(item) is not str for item in executed)
        or len(executed) != len(set(executed))
        or type(states) is not dict
        or any(
            type(node_id) is not str
            or state
            not in {
                "PASSED",
                "FAILED",
                "SKIPPED",
                "XFAILED",
                "XPASSED",
            }
            for node_id, state in states.items()
        )
        or any(node_id not in expected_nodes for node_id in executed)
        or any(node_id not in expected_nodes for node_id in states)
        or type(value.get("collection_errors")) is not int
        or isinstance(value.get("collection_errors"), bool)
        or value["collection_errors"] < 0
        or type(value.get("exit_code")) is not int
        or isinstance(value.get("exit_code"), bool)
        or type(value.get("python_version")) is not str
        or not value["python_version"]
        or type(value.get("pytest_version")) is not str
        or not value["pytest_version"]
    ):
        return False
    return _body_free(value)


def _run_exact134_worker(
    *,
    pinned_root: Path,
    result_path: Path,
    expected_nodes: list[str],
) -> tuple[dict[str, Any], bool]:
    runner_path = pinned_root / _RUNNER_PATH
    environment = _worker_environment()
    command = [
        sys.executable,
        "-I",
        "-B",
        str(runner_path),
        "--internal-exact134-child",
        str(result_path),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=pinned_root,
            env=environment,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return {
            "collection_node_ids": [],
            "executed_node_ids": [],
            "states": {},
            "collection_errors": 0,
            "exit_code": 124,
            "python_version": platform.python_version(),
            "pytest_version": "TIMEOUT",
        }, True
    if completed.returncode != 0 or not result_path.is_file():
        raise ValueError("RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID")
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeError) as exc:
        raise ValueError(
            "RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID"
        ) from exc
    if not _valid_worker_result(result, expected_nodes=expected_nodes):
        raise ValueError("RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID")
    return result, False


def _internal_exact134_child(result_path: Path) -> int:
    """Execute exact134 in a fresh isolated process and emit body-free JSON."""

    registry = fresh_recovery_epoch001_current_step_requirement_registry()
    if validate_recovery_epoch001_current_step_requirement_registry_shape(
        registry,
        repo_root=_REPO_ROOT,
    ):
        return 2
    nodes = _formal_nodes(registry)
    if (
        len(nodes) != RECOVERY_EPOCH001_FORMAL_NODE_COUNT
        or len(nodes) != len(set(nodes))
    ):
        return 2
    capture = _BodyFreePytestCapture()
    import pytest

    exit_code = int(
        pytest.main(
            [*nodes, *_PYTEST_OPTIONS],
            plugins=[capture],
        )
    )
    result: dict[str, Any] = {
        "collection_node_ids": list(capture.collected),
        "executed_node_ids": list(capture.executed),
        "states": dict(capture.states),
        "collection_errors": capture.collection_errors,
        "exit_code": exit_code,
        "python_version": platform.python_version(),
        "pytest_version": pytest.__version__,
    }
    if not _valid_worker_result(result, expected_nodes=nodes):
        return 2
    result_path.write_text(
        json.dumps(
            result,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return 0


def run_recovery_epoch001_current_step_proof(
    *,
    requirement_registry: Mapping[str, Any],
    source_baseline_event: Mapping[str, Any],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Execute the exact134 lane once and return a body-free proof candidate."""

    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = dict(requirement_registry)
    environment_issues = validate_recovery_epoch001_proof_environment(
        requirement_registry=registry,
        source_baseline_event=source_baseline_event,
        repo_root=root,
    )
    if environment_issues:
        raise ValueError(environment_issues[0])
    nodes = list(collect_recovery_epoch001_current_step_proof_nodes())
    source_commit, _, _ = _git_identity(root)
    with tempfile.TemporaryDirectory(
        prefix="emlis-recovery-epoch001-proof-"
    ) as temporary:
        temporary_root = Path(temporary)
        pinned_root = temporary_root / "pinned"
        result_path = temporary_root / "worker-result.json"
        worktree_added = False
        try:
            subprocess.run(
                [
                    "git",
                    "worktree",
                    "add",
                    "--detach",
                    str(pinned_root),
                    source_commit,
                ],
                cwd=root,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=60,
            )
            worktree_added = True
            closure_start = fresh_recovery_epoch001_canonical_current_closure(
                repo_root=pinned_root
            )
            run_start = _source_binding(
                repo_root=pinned_root,
                closure=closure_start,
                registry=registry,
            )
            worker_result, timed_out = _run_exact134_worker(
                pinned_root=pinned_root,
                result_path=result_path,
                expected_nodes=nodes,
            )
            closure_end = fresh_recovery_epoch001_canonical_current_closure(
                repo_root=pinned_root
            )
            run_end = _source_binding(
                repo_root=pinned_root,
                closure=closure_end,
                registry=registry,
            )
            outcomes = _outcomes(
                node_ids=nodes,
                states=worker_result["states"],
                negative_codes=_negative_codes_by_node(registry),
                repo_root=pinned_root,
            )
        except (
            FileNotFoundError,
            OSError,
            subprocess.SubprocessError,
            UnicodeError,
        ) as exc:
            raise ValueError(
                "RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID"
            ) from exc
        finally:
            if worktree_added:
                try:
                    subprocess.run(
                        [
                            "git",
                            "worktree",
                            "remove",
                            "--force",
                            str(pinned_root),
                        ],
                        cwd=root,
                        check=False,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=60,
                    )
                except (OSError, subprocess.SubprocessError):
                    # Cleanup must not replace the authoritative run result
                    # or mask the fail-closed exception from the proof lane.
                    pass
    worker_environment = _worker_environment()
    proof_run: dict[str, Any] = {
        "protocol": RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL,
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "recovery_epoch": 1,
        "source_baseline_event_sha256": (
            source_baseline_event["event_sha256"]
        ),
        "source_commit": run_start["source_commit"],
        "source_tree": run_start["source_tree"],
        "canonical_current_closure_sha256": (
            run_start["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            run_start["source_dependency_closure_sha256"]
        ),
        "registry_sha256": registry["registry_sha256"],
        "formal_node_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "collection_node_ids": list(worker_result["collection_node_ids"]),
        "executed_node_ids": list(worker_result["executed_node_ids"]),
        "runner_environment": {
            "protocol": RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL,
            "python_version": worker_result["python_version"],
            "pytest_version": worker_result["pytest_version"],
            "plugin_autoload_disabled": True,
            "runner_path": _RUNNER_PATH,
            "runner_git_blob_sha1": _git_blob_sha1(root / _RUNNER_PATH),
            "runner_sha256": _file_sha256(root / _RUNNER_PATH),
            "worker_isolated": True,
            "source_materialization": "DETACHED_PINNED_GIT_WORKTREE",
            "pytest_addopts_ignored": True,
            "pytest_plugins_ignored": True,
            "timeout_seconds": (
                RECOVERY_EPOCH001_FORMAL_RUN_TIMEOUT_SECONDS
            ),
            "worker_argv_sha256": _worker_argv_sha256(nodes),
            "environment_profile_sha256": (
                _worker_environment_profile_sha256(worker_environment)
            ),
        },
        "run_start": run_start,
        "run_end": run_end,
        "outcomes": outcomes,
        "counts": _counts(
            expected_nodes=nodes,
            collection_node_ids=worker_result["collection_node_ids"],
            executed_node_ids=worker_result["executed_node_ids"],
            states_by_node=worker_result["states"],
            collection_errors=worker_result["collection_errors"],
            timed_out=timed_out,
        ),
        "exit_code": worker_result["exit_code"],
        "timed_out": timed_out,
        "body_free": True,
    }
    proof_run["proof_run_sha256"] = artifact_sha256(proof_run)
    if not _body_free(proof_run):
        raise ValueError("RECOVERY_PROOF_ENVIRONMENT_ENTRY_INVALID")
    return proof_run


if __name__ == "__main__":
    if (
        len(sys.argv) == 3
        and sys.argv[1] == "--internal-exact134-child"
    ):
        raise SystemExit(_internal_exact134_child(Path(sys.argv[2])))
    raise SystemExit(
        "formal P1 must call run_recovery_epoch001_current_step_proof "
        "with an authorized event-1 object"
    )
