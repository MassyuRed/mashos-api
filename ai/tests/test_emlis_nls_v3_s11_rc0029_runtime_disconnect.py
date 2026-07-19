# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0029 remains experiment-only and unreachable from shared runtime."""

import json
from pathlib import Path

import emlis_ai_rc0029_surface_repair_experiment_dependency_manifest_v3 as dependency


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CURRENT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_SHARED_RUNTIME = (
    _REPO_ROOT
    / "ai"
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_runtime_adapter_v3.py"
)


def test_rc0029_has_no_shared_or_public_reverse_import() -> None:
    assert (
        dependency.find_rc0029_surface_repair_forbidden_reverse_imports(
            _REPO_ROOT
        )
        == ()
    )


def test_rc0029_is_absent_from_the_shared_runtime_owner() -> None:
    source = _SHARED_RUNTIME.read_text(encoding="utf-8")
    assert "rc0029" not in source.lower()
    assert "nls_v3_rc_0029_experiment" not in source


def test_rc0029_manifest_cannot_claim_runtime_or_formal_eligibility() -> None:
    manifest = json.loads(_CURRENT.read_text(encoding="utf-8"))
    flags = manifest["flags"]
    assert flags["experimental_only"] is True
    assert flags["runtime_connected"] is False
    assert flags["public_owner_unchanged"] is True
    assert flags["eligible_for_formal"] is False
    assert flags["eligible_for_production"] is False
    assert manifest["forbidden_reverse_imports"] == []
