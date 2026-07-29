from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import inspect
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"
for _import_root in (_INFERENCE_ROOT, _TOOLS_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

import emlis_ai_recovery_epoch002_canonical_current_closure_v3 as _owner
import emlis_nls_v3_recovery_epoch002_closure_receipt_verify as _independent
import emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3 as _parent
import emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight as _preflight


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_POST_P0_PARENT_ADDENDUM_"
    "POST_D2_REMEDIATION_D1_ACTUAL_UNCLASSIFIED_IMPORT_EXACT3_AND_"
    "VERSIONED_CURRENT_STRICT_PREFLIGHT_CONNECTION_CAUSAL_RED_FREEZE_ONLY"
)
_ENTRY_COMMIT_SHA1 = "32efb22cd1843d2d2103f0a981fd3e4be9623dc2"
_ENTRY_TREE_SHA1 = "077b9150057f7562f700b6825b23d978276b42a0"
_LOCK_PATH = (
    "ai/configs/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
)
_LOCK_BLOB_SHA1 = "0822fcb010985cd0d384f250a9e8a1fe16dc8fd4"
_LOCK_RAW_SHA256 = (
    "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
)
_EXPECTED_UNCLASSIFIED = (
    "models",
    "models_updated",
    "self_structure_engine.rules",
)
_EXPECTED_REACHABLE_OWNER_PATHS = {
    "models": (
        "ai/services/analysis_engine/self_structure_engine/rules.py",
    ),
    "models_updated": (
        "ai/services/analysis_engine/self_structure_engine/rules.py",
    ),
    "self_structure_engine.rules": (
        "ai/services/ai_inference/astor_self_structure_report.py",
    ),
}
_ENTRY_SOURCE_IDENTITIES = {
    "ai/services/analysis_engine/self_structure_engine/rules.py": {
        "git_blob_sha1": "dbc8c93c8fb9c41aae6db330ad9eba81b18a9bc4",
        "raw_sha256": (
            "94aa10be7e4ec169f39bcc26bc8c58280d37b0cc3e7e40ec5032d1a6e2b1dd85"
        ),
    },
    "ai/services/ai_inference/astor_self_structure_report.py": {
        "git_blob_sha1": "b3d0e29ef2a04ee8ace406a27de157a6ac70c1da",
        "raw_sha256": (
            "7f2bd21e454d8bb0fe54f5af31ff14dfd3141d51c858dfc34dd8d0586780160b"
        ),
    },
    "ai/services/analysis_engine/models.py": {
        "git_blob_sha1": "b391e6b8dc6467595b82d927be36aafb394594d6",
        "raw_sha256": (
            "cd9ff7674d0908524a16b14b3ad9a7f6775ffa747b61e160aa4f1f820f64e4c0"
        ),
    },
}
_EXACT30_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_"
    "bootstrap_source_runtime_expected_observed_contract_red.py"
)
_EXACT30_RAW_SHA256 = (
    "8c8fcaf5211064ca59127a8081dc41ae8b9207472f070746c84a8e4b591a07e5"
)
_HISTORICAL_VERIFIER_API = (
    "verify_recovery_epoch003_bootstrap_source_runtime_contract"
)
_CURRENT_VERIFIER_API = (
    "verify_recovery_epoch003_bootstrap_source_runtime_contract_current"
)
_HISTORICAL_PREFLIGHT_API = "evaluate_recovery_epoch003_preflight_contract"
_CURRENT_PREFLIGHT_API = (
    "execute_recovery_epoch003_current_strict_preflight_v1"
)
_CURRENT_PARENT_API = (
    "execute_recovery_epoch003_current_strict_parent_phase_v1"
)
_HISTORICAL_VERIFIER_SOURCE_SHA256 = (
    "6479a4d409d2d4971c78caf60067c769fc6308dde87ec60149d13e610a5e100f"
)
_HISTORICAL_PREFLIGHT_SOURCE_SHA256 = (
    "2aa5bc3704ec806046ae817512e5db1171b369b0fa49e395fdc9b28b6ea20109"
)
_CURRENT_PROFILE_OVERRIDE_STOP = (
    "RECOVERY_EPOCH003_CURRENT_STRICT_PROFILE_OVERRIDE_FORBIDDEN"
)
_CURRENT_PARENT_INVALID_STOP = (
    "RECOVERY_EPOCH003_CURRENT_STRICT_PARENT_PHASE_INVALID"
)
_CURRENT_ZERO_EFFECTS = {
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
_TEST_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch003_actual_unclassified_import_exact3_"
    "and_versioned_current_strict_preflight_connection_red.py"
)
_ORDERED_NODE_IDS = tuple(
    f"{_TEST_PATH}::{name}"
    for name in (
        "test_m01_owner_actual_head_unclassified_exact3_noncredit_diagnostic",
        (
            "test_m02_independent_actual_head_unclassified_exact3_"
            "noncredit_diagnostic"
        ),
        "test_m03_actual_reachable_import_owner_paths_exact2",
        (
            "test_m04_green_requires_unmodified_lock_manifest_parity_"
            "and_zero_unresolved"
        ),
        "test_p01_versioned_current_strict_api_separated_from_historical",
        (
            "test_p02_current_preflight_rejects_downgrade_fallback_"
            "and_fixture_credit"
        ),
        "test_f01_source_syntax_import_and_identity_drift_fail_closed",
        "test_z01_all_success_and_failure_branches_keep_effects_zero",
    )
)
_ORDERED_NODE_IDS_SHA256 = (
    "22c217b28ae1916ac7817dcfa091ea107a85e483ce5959241e44200c6c9a79de"
)
_OWNER_FAILURE = (
    "RECOVERY_EPOCH003_SOURCE_BOOTSTRAP_BUILD_INVALID",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _git(*args: str, cwd: Path = _REPO_ROOT) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout.strip()


def _git_bytes(*args: str, cwd: Path = _REPO_ROOT) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        timeout=30,
    ).stdout


def _assert_actual_head_contract() -> None:
    assert _git("rev-parse", f"{_ENTRY_COMMIT_SHA1}^{{tree}}") == (
        _ENTRY_TREE_SHA1
    )
    assert (
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                _ENTRY_COMMIT_SHA1,
                "HEAD",
            ],
            cwd=_REPO_ROOT,
            capture_output=True,
            timeout=30,
        ).returncode
        == 0
    )
    assert _git("status", "--porcelain", "--untracked-files=all") == ""


def _runtime_identity() -> dict[str, str]:
    executable = Path(sys.executable).resolve()
    build = {
        "python_build": list(platform.python_build()),
        "python_compiler": platform.python_compiler(),
        "platform": platform.platform(),
        "abi_flags": sys.abiflags,
    }
    return {
        "executable_sha256": hashlib.sha256(
            executable.read_bytes()
        ).hexdigest(),
        "implementation": platform.python_implementation().upper(),
        "version": platform.python_version(),
        "build_sha256": _sha256_value(build),
    }


def _lock() -> dict[str, Any]:
    raw = _git_bytes("show", f"HEAD:{_LOCK_PATH}")
    assert hashlib.sha256(raw).hexdigest() == _LOCK_RAW_SHA256
    assert _git("rev-parse", f"HEAD:{_LOCK_PATH}") == _LOCK_BLOB_SHA1
    value = json.loads(raw)
    assert isinstance(value, dict)
    return value


def _seed_paths() -> set[str]:
    return {
        path for _role, path in _owner._RECOVERY_EPOCH003_OWNER_ROLE_PATHS
    } | set(_owner._RECOVERY_EPOCH003_FORMAL_TEST_PATHS)


def _capture_manifest(
    build: Callable[[], list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]] | None, tuple[str, ...] | None]:
    try:
        return build(), None
    except (
        OSError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        message = str(exc)
        if isinstance(exc, ValueError) and message.startswith(
            "unclassified import: "
        ):
            return None, (
                "UNCLASSIFIED_IMPORT",
                message.removeprefix("unclassified import: "),
            )
        if isinstance(exc, ValueError) and message in {
            "unresolved dynamic import",
            "unresolved file import",
        }:
            return None, ("UNRESOLVED_DYNAMIC_IMPORT", message)
        return None, ("FAIL_CLOSED", type(exc).__name__, message)


def _owner_manifest(
    lock: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> tuple[list[dict[str, Any]] | None, tuple[str, ...] | None]:
    return _capture_manifest(
        lambda: _owner._recovery_epoch003_import_manifest(
            _REPO_ROOT,
            lock=lock,
            runtime_identity=runtime,
        )
    )


def _independent_manifest(
    lock: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> tuple[list[dict[str, Any]] | None, tuple[str, ...] | None]:
    seeds = _seed_paths()
    return _capture_manifest(
        lambda: _independent._recovery_epoch003_independent_import_manifest(
            _REPO_ROOT,
            lock=lock,
            runtime_identity=runtime,
            seed_paths=seeds,
        )
    )


def _noncredit_progressive_diagnostic(
    derive: Callable[
        [Mapping[str, Any], Mapping[str, Any]],
        tuple[list[dict[str, Any]] | None, tuple[str, ...] | None],
    ],
    lock: Mapping[str, Any],
    runtime: Mapping[str, Any],
) -> tuple[
    tuple[str, ...],
    dict[str, tuple[str, ...]],
    list[dict[str, Any]],
    int,
]:
    """Enumerate blockers without granting the fabricated mapping credit."""

    diagnostic_lock = deepcopy(lock)
    mapping = diagnostic_lock["module_distribution_map"]
    distributions = diagnostic_lock["distributions"]
    assert isinstance(mapping, dict)
    assert isinstance(distributions, list) and distributions
    distribution_name = min(
        row["normalized_distribution_name"]
        for row in distributions
        if isinstance(row, dict)
    )
    missing: list[str] = []
    for _iteration in range(32):
        manifest, failure = derive(diagnostic_lock, runtime)
        if failure is None:
            assert manifest is not None
            owner_paths = {
                row["import_name"]: tuple(row["owner_paths"])
                for row in manifest
                if row["import_name"] in missing
            }
            assert lock != diagnostic_lock
            return tuple(missing), owner_paths, manifest, 0
        assert failure[0] == "UNCLASSIFIED_IMPORT"
        name = failure[1]
        assert name not in missing
        missing.append(name)
        mapping[name] = distribution_name
    raise AssertionError("noncredit diagnostic did not terminate")


def _assert_manifest(value: Any) -> None:
    assert isinstance(value, list)
    assert value
    assert value == sorted(value, key=lambda row: row["import_name"])
    assert len({row["import_name"] for row in value}) == len(value)
    assert all(
        isinstance(row, dict)
        and set(row)
        == {
            "import_name",
            "classification",
            "owner_paths",
            "target_identity",
        }
        and row["classification"]
        in {
            "FIRST_PARTY",
            "STDLIB_BOUND_TO_PYTHON_RUNTIME",
            "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
        }
        and row["owner_paths"] == sorted(set(row["owner_paths"]))
        for row in value
    )


def _load_immutable_test_module(
    path: str,
    raw_sha256: str,
    module_name: str,
) -> Any:
    raw = _git_bytes("show", f"HEAD:{path}")
    assert hashlib.sha256(raw).hexdigest() == raw_sha256
    worktree_raw = (_REPO_ROOT / path).read_bytes()
    assert worktree_raw == raw
    assert hashlib.sha256(worktree_raw).hexdigest() == raw_sha256
    spec = importlib.util.spec_from_file_location(
        module_name,
        _REPO_ROOT / path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _assert_oracle_denominator() -> None:
    raw = (_REPO_ROOT / _TEST_PATH).read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    names = tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )
    observed = tuple(f"{_TEST_PATH}::{name}" for name in names)
    assert observed == _ORDERED_NODE_IDS
    assert len(observed) == len(set(observed)) == 8
    assert _sha256_value(list(observed)) == _ORDERED_NODE_IDS_SHA256


def _broad_exception_imports(
    path: str,
    raw: bytes,
) -> dict[str, set[tuple[str, int]]]:
    tree = ast.parse(raw.decode("utf-8"))
    result: dict[str, set[tuple[str, int]]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if not (
            isinstance(node.type, ast.Name)
            and node.type.id in {"Exception", "BaseException"}
        ):
            continue
        for statement in node.body:
            for child in ast.walk(statement):
                if isinstance(child, ast.Import):
                    names = [alias.name for alias in child.names]
                elif isinstance(child, ast.ImportFrom):
                    if child.level:
                        names = [
                            "." * child.level + (child.module or "")
                        ]
                    else:
                        names = [child.module or ""]
                else:
                    continue
                for name in names:
                    if name in _EXPECTED_UNCLASSIFIED:
                        result.setdefault(name, set()).add(
                            (path, child.lineno)
                        )
    return result


def _called_names(node: ast.AST) -> tuple[str, ...]:
    result: list[str] = []
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        if isinstance(child.func, ast.Name):
            result.append(child.func.id)
        elif isinstance(child.func, ast.Attribute):
            result.append(child.func.attr)
    return tuple(result)


def _caught_names(function: Callable[..., Any]) -> frozenset[str]:
    tree = ast.parse(inspect.getsource(function))
    result: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        values = (
            node.type.elts
            if isinstance(node.type, ast.Tuple)
            else [node.type]
        )
        for value in values:
            if isinstance(value, ast.Name):
                result.add(value.id)
            elif isinstance(value, ast.Attribute):
                result.add(value.attr)
    return frozenset(result)


def _historical_pair_state() -> dict[str, Any]:
    pair = _independent.RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS[0]
    return {
        "source_closure": {"schema_version": pair[0]},
        "bootstrap_closure": {"schema_version": pair[1]},
    }


def _is_fixture_readiness(value: Any, fixture: Any) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("schema_version") == fixture._READINESS_SCHEMA
        and value.get("bootstrap_readiness_receipt_sha256")
    )


def _current_failure_code(value: Any, fixture: Any | None = None) -> str:
    assert isinstance(value, Mapping)
    if fixture is not None:
        assert not _is_fixture_readiness(value, fixture)
    assert value.get("body_free") is True
    assert value.get("automatic_progression") is False
    assert value.get("source_baseline_state") == "UNLOCKED"
    assert value.get("pytest_main_called") is False
    assert {
        key: value.get(key) for key in _CURRENT_ZERO_EFFECTS
    } == _CURRENT_ZERO_EFFECTS
    codes = [
        value.get(key)
        for key in ("failure_class", "failure_code", "stop_code")
        if isinstance(value.get(key), str) and value.get(key)
    ]
    assert len(codes) == 1
    return codes[0]


def test_m01_owner_actual_head_unclassified_exact3_noncredit_diagnostic() -> None:
    _assert_actual_head_contract()
    lock = _lock()
    runtime = _runtime_identity()
    manifest, failure = _owner_manifest(lock, runtime)
    if failure is not None:
        assert failure == ("UNCLASSIFIED_IMPORT", "models")
        missing, owner_paths, _diagnostic_manifest, credit = (
            _noncredit_progressive_diagnostic(
                _owner_manifest,
                lock,
                runtime,
            )
        )
        assert missing == _EXPECTED_UNCLASSIFIED
        assert owner_paths == _EXPECTED_REACHABLE_OWNER_PATHS
        assert credit == 0
        assert lock == _lock()
        pytest.fail(
            "M01_CAUSAL_RED:"
            f"actual_unclassified={missing!r};"
            "diagnostic_credit=0;owner_manifest=NOT_DERIVED"
        )
    _assert_manifest(manifest)


def test_m02_independent_actual_head_unclassified_exact3_noncredit_diagnostic() -> None:
    _assert_actual_head_contract()
    lock = _lock()
    runtime = _runtime_identity()
    manifest, failure = _independent_manifest(lock, runtime)
    if failure is not None:
        assert failure == ("UNCLASSIFIED_IMPORT", "models")
        missing, owner_paths, _diagnostic_manifest, credit = (
            _noncredit_progressive_diagnostic(
                _independent_manifest,
                lock,
                runtime,
            )
        )
        assert missing == _EXPECTED_UNCLASSIFIED
        assert owner_paths == _EXPECTED_REACHABLE_OWNER_PATHS
        assert credit == 0
        assert lock == _lock()
        pytest.fail(
            "M02_CAUSAL_RED:"
            f"actual_unclassified={missing!r};"
            "diagnostic_credit=0;independent_manifest=NOT_DERIVED"
        )
    _assert_manifest(manifest)


def test_m03_actual_reachable_import_owner_paths_exact2() -> None:
    _assert_oracle_denominator()
    assert _git("rev-parse", f"{_ENTRY_COMMIT_SHA1}^{{tree}}") == (
        _ENTRY_TREE_SHA1
    )
    observed: dict[str, set[tuple[str, int]]] = {}
    for path, identity in _ENTRY_SOURCE_IDENTITIES.items():
        raw = _git_bytes("show", f"{_ENTRY_COMMIT_SHA1}:{path}")
        assert hashlib.sha256(raw).hexdigest() == identity["raw_sha256"]
        assert _git(
            "rev-parse",
            f"{_ENTRY_COMMIT_SHA1}:{path}",
        ) == identity["git_blob_sha1"]
        for name, rows in _broad_exception_imports(path, raw).items():
            observed.setdefault(name, set()).update(rows)
    assert {
        name: tuple(sorted({path for path, _line in rows}))
        for name, rows in observed.items()
    } == _EXPECTED_REACHABLE_OWNER_PATHS
    assert {
        name: tuple(sorted(line for _path, line in rows))
        for name, rows in observed.items()
    } == {
        "models": (35,),
        "models_updated": (33,),
        "self_structure_engine.rules": (78,),
    }

    rules = ast.parse(
        _git_bytes(
            "show",
            (
                f"{_ENTRY_COMMIT_SHA1}:"
                "ai/services/analysis_engine/self_structure_engine/rules.py"
            ),
        ).decode("utf-8")
    )
    astor_report = ast.parse(
        _git_bytes(
            "show",
            (
                f"{_ENTRY_COMMIT_SHA1}:"
                "ai/services/ai_inference/astor_self_structure_report.py"
            ),
        ).decode("utf-8")
    )
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.level == 2
        and node.module == "models"
        for node in ast.walk(rules)
    )
    assert any(
        isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module == "analysis_engine.self_structure_engine.rules"
        for node in ast.walk(astor_report)
    )


def test_m04_green_requires_unmodified_lock_manifest_parity_and_zero_unresolved(
) -> None:
    _assert_actual_head_contract()
    lock = _lock()
    runtime = _runtime_identity()
    before_lock = deepcopy(lock)
    before_runtime = deepcopy(runtime)
    owner_manifest, owner_failure = _owner_manifest(lock, runtime)
    independent_manifest, independent_failure = _independent_manifest(
        lock,
        runtime,
    )
    if owner_failure is not None or independent_failure is not None:
        pytest.fail(
            "M04_CAUSAL_RED:"
            f"owner={owner_failure!r};independent={independent_failure!r};"
            "manifest_parity=NOT_DERIVED;unclassified_exact0=NOT_MET;"
            "unresolved_dynamic_exact0=NOT_CREDITED"
        )
    _assert_manifest(owner_manifest)
    _assert_manifest(independent_manifest)
    assert owner_manifest == independent_manifest
    assert not (
        set(_EXPECTED_UNCLASSIFIED)
        & {row["import_name"] for row in owner_manifest}
    )
    assert lock == before_lock
    assert runtime == before_runtime
    assert not (
        set(_EXPECTED_UNCLASSIFIED)
        & set(lock["module_distribution_map"])
    )
    build_source = inspect.getsource(
        _owner.build_recovery_epoch003_source_bootstrap_closure
    )
    assert "_recovery_epoch003_import_manifest(" in build_source
    assert '"unclassified_import_count": 0' in build_source
    assert '"unresolved_dynamic_import_count": 0' in build_source


def test_p01_versioned_current_strict_api_separated_from_historical() -> None:
    historical_verifier = getattr(
        _independent,
        _HISTORICAL_VERIFIER_API,
        None,
    )
    current_verifier = getattr(_independent, _CURRENT_VERIFIER_API, None)
    historical_preflight = getattr(
        _preflight,
        _HISTORICAL_PREFLIGHT_API,
        None,
    )
    current_preflight = getattr(_preflight, _CURRENT_PREFLIGHT_API, None)
    current_parent = getattr(_parent, _CURRENT_PARENT_API, None)
    assert callable(historical_verifier)
    assert callable(historical_preflight)
    missing = tuple(
        name
        for name, value in (
            (_CURRENT_VERIFIER_API, current_verifier),
            (_CURRENT_PREFLIGHT_API, current_preflight),
            (_CURRENT_PARENT_API, current_parent),
        )
        if not callable(value)
    )
    if missing:
        pytest.fail(
            "P01_CAUSAL_RED:"
            f"missing_versioned_current_strict_symbols={missing!r}"
        )
    assert current_verifier is not historical_verifier
    assert current_preflight is not historical_preflight
    assert _CURRENT_VERIFIER_API in _independent.__all__
    assert _CURRENT_PREFLIGHT_API in _preflight.__all__
    assert _CURRENT_PARENT_API in _parent.__all__
    assert tuple(inspect.signature(current_verifier).parameters) == ("state",)
    assert tuple(inspect.signature(current_preflight).parameters) == ("state",)
    assert tuple(inspect.signature(current_parent).parameters) == ("state",)
    assert hashlib.sha256(
        inspect.getsource(historical_verifier).encode("utf-8")
    ).hexdigest() == _HISTORICAL_VERIFIER_SOURCE_SHA256
    assert hashlib.sha256(
        inspect.getsource(historical_preflight).encode("utf-8")
    ).hexdigest() == _HISTORICAL_PREFLIGHT_SOURCE_SHA256

    historical_state = _historical_pair_state()
    assert historical_verifier(deepcopy(historical_state)) == ()
    assert current_verifier(deepcopy(historical_state)) == (
        "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
    )

    current_preflight_node = ast.parse(
        inspect.getsource(current_preflight)
    ).body[0]
    current_preflight_calls = _called_names(current_preflight_node)
    assert current_preflight_calls.count(_CURRENT_VERIFIER_API) == 1
    assert _HISTORICAL_VERIFIER_API not in current_preflight_calls
    assert _HISTORICAL_PREFLIGHT_API not in current_preflight_calls
    assert "build_recovery_epoch002_operational_preflight_attestation" not in (
        current_preflight_calls
    )
    assert "_preflight_cli_result" not in current_preflight_calls
    assert "_main" not in current_preflight_calls

    current_parent_node = ast.parse(
        inspect.getsource(current_parent)
    ).body[0]
    current_parent_calls = _called_names(current_parent_node)
    assert current_parent_calls.count(_CURRENT_PREFLIGHT_API) == 1
    assert (
        current_parent_calls.count(
            "validate_recovery_epoch003_parent_phase_evidence_state"
        )
        == 1
    )
    for forbidden in (
        _HISTORICAL_PREFLIGHT_API,
        "validate_recovery_epoch003_parent_phase_state",
        "build_recovery_epoch002_operational_preflight_attestation",
        "execute_recovery_epoch002_parent_phase",
        "_main",
    ):
        assert forbidden not in current_parent_calls


def test_p02_current_preflight_rejects_downgrade_fallback_and_fixture_credit() -> None:
    fixture = _load_immutable_test_module(
        _EXACT30_PATH,
        _EXACT30_RAW_SHA256,
        "_epoch003_d1_exact30_immutable_for_current_strict_negative",
    )
    historical_verifier = getattr(
        _independent,
        _HISTORICAL_VERIFIER_API,
    )
    historical_preflight = getattr(_preflight, _HISTORICAL_PREFLIGHT_API)
    current_verifier = getattr(_independent, _CURRENT_VERIFIER_API, None)
    current_preflight = getattr(_preflight, _CURRENT_PREFLIGHT_API, None)
    current_parent = getattr(_parent, _CURRENT_PARENT_API, None)
    missing = tuple(
        name
        for name, value in (
            (_CURRENT_VERIFIER_API, current_verifier),
            (_CURRENT_PREFLIGHT_API, current_preflight),
            (_CURRENT_PARENT_API, current_parent),
        )
        if not callable(value)
    )
    if missing:
        pytest.fail(
            "P02_CAUSAL_RED:"
            f"missing_current_strict_negative_gate_symbols={missing!r}"
        )

    fixture_state = fixture._baseline_state()
    assert historical_verifier(deepcopy(fixture_state)) == ()
    assert _is_fixture_readiness(
        historical_preflight(deepcopy(fixture_state)),
        fixture,
    )
    assert _current_failure_code(
        current_preflight(_historical_pair_state()),
        fixture,
    ) == "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED"
    assert _current_failure_code(
        current_preflight(deepcopy(fixture_state)),
        fixture,
    ) == "SOURCE_BOOTSTRAP_BASELINE_MISMATCH"
    parent_input = _historical_pair_state()
    parent_before = deepcopy(parent_input)
    assert _current_failure_code(
        current_parent(parent_input),
        fixture,
    ) == _CURRENT_PARENT_INVALID_STOP
    assert parent_input == parent_before

    for key, value in (
        ("profile", "historical"),
        ("verification_mode", "HISTORICAL_COMPATIBLE"),
        ("allow_historical_fallback", True),
    ):
        state = _historical_pair_state()
        state[key] = value
        assert _current_failure_code(
            current_preflight(state),
            fixture,
        ) == _CURRENT_PROFILE_OVERRIDE_STOP
    assert current_verifier(deepcopy(fixture_state)) == (
        "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
    )


def test_f01_source_syntax_import_and_identity_drift_fail_closed() -> None:
    build = _owner.build_recovery_epoch003_source_bootstrap_closure
    state = {
        "source_repository_root": str(_REPO_ROOT),
        "source_commit_sha1": _git("rev-parse", "HEAD"),
        "source_tree_sha1": _git("rev-parse", "HEAD^{tree}"),
        "reference_runtime_observation": {},
        "reference_runtime_observation_external_identity": {},
    }
    assert build(deepcopy(state)) == _OWNER_FAILURE
    for key in ("source_commit_sha1", "source_tree_sha1"):
        drifted = deepcopy(state)
        drifted[key] = "0" * 40
        assert build(drifted) == _OWNER_FAILURE

    owner_catches = _caught_names(build)
    independent_catches = _caught_names(
        _independent.verify_recovery_epoch003_operational_admission_contract
    )
    required = {
        "OSError",
        "SubprocessError",
        "SyntaxError",
        "TypeError",
        "UnicodeError",
        "ValueError",
    }
    assert required <= owner_catches
    assert required <= independent_catches

    source = inspect.getsource(build)
    for token in (
        '"status"',
        '"--porcelain"',
        '"--untracked-files=all"',
        '"HEAD"',
        '"HEAD^{tree}"',
    ):
        assert token in source
    assert '"unresolved dynamic import"' in inspect.getsource(
        _owner._recovery_epoch003_import_manifest
    )
    assert '"unclassified import: {import_name}"' in inspect.getsource(
        _owner._recovery_epoch003_import_manifest
    )
    assert '"unresolved dynamic import"' in inspect.getsource(
        _independent._recovery_epoch003_independent_import_manifest
    )
    assert '"unclassified import: {import_name}"' in inspect.getsource(
        _independent._recovery_epoch003_independent_import_manifest
    )
    assert build({"source_repository_root": str(_REPO_ROOT)}) == (
        _OWNER_FAILURE
    )


def test_z01_all_success_and_failure_branches_keep_effects_zero() -> None:
    _assert_oracle_denominator()
    before = (
        _git("rev-parse", "HEAD"),
        _git("rev-parse", "HEAD^{tree}"),
        _git("status", "--porcelain", "--untracked-files=all"),
    )
    lock = _lock()
    runtime = _runtime_identity()
    lock_before = deepcopy(lock)
    runtime_before = deepcopy(runtime)
    _owner_manifest(lock, runtime)
    _independent_manifest(lock, runtime)

    historical_state = _historical_pair_state()
    historical_state_before = deepcopy(historical_state)
    getattr(_independent, _HISTORICAL_VERIFIER_API)(
        deepcopy(historical_state)
    )
    current_verifier = getattr(_independent, _CURRENT_VERIFIER_API, None)
    current_preflight = getattr(_preflight, _CURRENT_PREFLIGHT_API, None)
    current_parent = getattr(_parent, _CURRENT_PARENT_API, None)
    missing = tuple(
        name
        for name, value in (
            (_CURRENT_VERIFIER_API, current_verifier),
            (_CURRENT_PREFLIGHT_API, current_preflight),
            (_CURRENT_PARENT_API, current_parent),
        )
        if not callable(value)
    )
    if missing:
        pytest.fail(
            "Z01_CAUSAL_RED:"
            f"zero_effect_branch_contract_unreachable={missing!r}"
        )
    assert current_verifier(deepcopy(historical_state)) == (
        "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
    )
    assert _current_failure_code(
        current_preflight(deepcopy(historical_state))
    ) == "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED"
    assert _current_failure_code(
        current_parent(deepcopy(historical_state))
    ) == _CURRENT_PARENT_INVALID_STOP

    after = (
        _git("rev-parse", "HEAD"),
        _git("rev-parse", "HEAD^{tree}"),
        _git("status", "--porcelain", "--untracked-files=all"),
    )
    assert before == after
    assert before[2] == ""
    assert lock == lock_before
    assert runtime == runtime_before
    assert historical_state == historical_state_before

    forbidden_calls = {
        "materialize_recovery_epoch003_reference_runtime",
        "build_recovery_epoch003_reference_runtime_observation",
        "publish",
        "publish_recovery_epoch003_operational_admission",
        "allocate_candidate",
        "issue_event1",
        "reserve",
        "create_reservation",
        "create_attempt",
        "run_formal_exact134",
        "pytest_main",
        "main",
    }
    functions = [
        _owner._recovery_epoch003_import_manifest,
        _independent._recovery_epoch003_independent_import_manifest,
        getattr(_independent, _HISTORICAL_VERIFIER_API),
    ]
    functions.extend(
        (current_verifier, current_preflight, current_parent)
    )
    for function in functions:
        node = ast.parse(inspect.getsource(function))
        assert forbidden_calls.isdisjoint(_called_names(node))
    assert _AUTHORITY.endswith("CAUSAL_RED_FREEZE_ONLY")
