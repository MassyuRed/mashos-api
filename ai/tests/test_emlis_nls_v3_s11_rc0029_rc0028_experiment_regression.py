# -*- coding: utf-8 -*-
from __future__ import annotations

"""Immutable rc0028 behavior and append-only byte-prefix regression."""

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from emlis_ai_step11_rc0028_experiment_runtime_adapter_v3 import (
    execute_step11_rc0028_experiment_private,
    validate_step11_rc0028_experiment_private_execution,
)


_REPO = Path(__file__).resolve().parents[2]
_ROOT = Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3"
_BATCH = _ROOT / "generated" / "batch_001.jsonl"
_MANIFEST = _ROOT / "generated" / "batch_001_manifest.json"
_RC0028_MANIFEST = (
    _ROOT / "cycle_001"
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
_PREDECESSOR_COMMIT = "e069ffd782e4d2b960b2c1e770d9018ab78a8b1d"
_EXACT4 = (
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py",
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def test_rc0029_exact4_edits_are_append_only_over_rc0028_predecessor() -> None:
    for relative in _EXACT4:
        predecessor = subprocess.run(
            ["git", "show", f"{_PREDECESSOR_COMMIT}:{relative}"],
            cwd=_REPO,
            check=True,
            capture_output=True,
        ).stdout
        current = (_REPO / relative).read_bytes()
        assert current.startswith(predecessor)
        assert len(current) > len(predecessor)


def test_rc0029_keeps_rc0028_runtime_selected_bytes_stable() -> None:
    sample = json.loads(_BATCH.read_text(encoding="utf-8").splitlines()[0])
    manifest = _load(_MANIFEST)
    closure = _load(_RC0028_MANIFEST)["source_dependency_closure_sha256"]
    commitment = {
        row["case_id"]: row["case_commitment"]
        for row in manifest["case_commitments"]
    }[sample["case_id"]]
    first = execute_step11_rc0028_experiment_private(
        sample["input"],
        case_id=sample["case_id"],
        source_case_commitment=commitment,
        source_dependency_closure_sha256=closure,
    )
    second = execute_step11_rc0028_experiment_private(
        sample["input"],
        case_id=sample["case_id"],
        source_case_commitment=commitment,
        source_dependency_closure_sha256=closure,
    )
    assert validate_step11_rc0028_experiment_private_execution(first) == ()
    assert first.body_free_result == second.body_free_result
    assert first.selected_final_utf8_bytes == second.selected_final_utf8_bytes
    assert hashlib.sha256(first.selected_final_utf8_bytes or b"").hexdigest() == (
        hashlib.sha256(second.selected_final_utf8_bytes or b"").hexdigest()
    )
