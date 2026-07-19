# -*- coding: utf-8 -*-
from __future__ import annotations

"""Exact downstream dependency closure for the disconnected rc0028 run."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import emlis_ai_rc0028_downstream_experiment_dependency_manifest_v3 as dependency


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CYCLE_ROOT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
)
_UPSTREAM = _CYCLE_ROOT / "cycle001_dependency_manifest_rc0028_experiment.json"
_DOWNSTREAM = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
_TOOL = (
    _REPO_ROOT
    / "ai"
    / "tools"
    / "emlis_nls_v3_rc0028_downstream_experiment_dependency_manifest.py"
)

_REQUIRED_DOWNSTREAM_PATHS = frozenset(
    {
        "ai/services/ai_inference/"
        "emlis_ai_rc0028_downstream_experiment_dependency_manifest_v3.py",
        "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py",
        "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py",
        "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py",
        "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3.py",
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0028_experiment_surface_catalog_v3.py",
        "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
        "rc0028_representative8_body_free.json",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_downstream_dependency_closure.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e0b_downstream_mutation.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e0b_downstream_red.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e2_downstream_integration.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e2_forward_inverse_independence.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e2_runtime_disconnect.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e3_representative8.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0028_e4_frozen100_read_only.py",
        "ai/tests/"
        "test_emlis_nls_v3_s11_rc0028_rc0027_default_behavior_regression.py",
        "ai/tools/emlis_nls_v3_rc0028_bounded_experiment.py",
        "ai/tools/"
        "emlis_nls_v3_rc0028_downstream_experiment_dependency_manifest.py",
    }
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rc0028_downstream_manifest_rebuilds_exactly_from_upstream() -> None:
    build = getattr(
        dependency,
        "build_rc0028_downstream_experiment_dependency_manifest",
        None,
    )
    validate_shape = getattr(
        dependency,
        "validate_rc0028_downstream_experiment_dependency_manifest_shape",
        None,
    )
    validate = getattr(
        dependency,
        "validate_rc0028_downstream_experiment_dependency_manifest",
        None,
    )
    assert callable(build), "RC0028_DOWNSTREAM_MANIFEST_BUILDER_REQUIRED"
    assert callable(validate_shape), "RC0028_DOWNSTREAM_SHAPE_VALIDATOR_REQUIRED"
    assert callable(validate), "RC0028_DOWNSTREAM_MANIFEST_VALIDATOR_REQUIRED"

    upstream = _load(_UPSTREAM)
    downstream = _load(_DOWNSTREAM)
    assert validate_shape(downstream) == ()
    assert validate(
        downstream,
        parent_manifest=upstream,
        repo_root=_REPO_ROOT,
    ) == ()
    assert build(upstream, repo_root=_REPO_ROOT) == downstream


def test_rc0028_downstream_closure_binds_owner_tool_fixture_and_exact_tests() -> None:
    downstream = _load(_DOWNSTREAM)
    modified_rows = downstream.get("modified_owner_file_hashes")
    new_rows = downstream.get("new_file_hashes")
    assert type(modified_rows) is list
    assert type(new_rows) is list
    changed_rows = modified_rows + new_rows
    changed_by_path = {
        row["path"]: row.get("sha256", row.get("current_sha256"))
        for row in changed_rows
    }
    assert _REQUIRED_DOWNSTREAM_PATHS == frozenset(changed_by_path)
    assert all(
        changed_by_path[path] == _sha256(_REPO_ROOT / path)
        for path in changed_by_path
    )
    generated_path = (
        "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
        "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
    )
    assert generated_path not in {
        row["path"] for row in downstream["file_hashes"]
    }
    assert downstream["body_free"] is True
    assert downstream["flags"]["experimental_only"] is True
    assert downstream["flags"]["runtime_connected"] is False
    assert downstream["flags"]["eligible_for_formal"] is False
    assert downstream["flags"]["eligible_for_production"] is False


def test_rc0028_downstream_manifest_tool_verifies_generated_fixture() -> None:
    downstream = _load(_DOWNSTREAM)
    completed = subprocess.run(
        (
            sys.executable,
            str(_TOOL),
            "--parent-manifest",
            str(_UPSTREAM),
            "--repo-root",
            str(_REPO_ROOT),
            "--check",
            str(_DOWNSTREAM),
        ),
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert completed.stdout.strip() == downstream[
        "source_dependency_closure_sha256"
    ]
