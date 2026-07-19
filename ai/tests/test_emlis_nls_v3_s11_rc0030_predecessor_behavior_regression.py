# -*- coding: utf-8 -*-
from __future__ import annotations

"""Behavior regression for immutable rc0027-rc0029 predecessors."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Callable

from emlis_ai_step11_rc0028_experiment_runtime_adapter_v3 import (
    execute_step11_rc0028_experiment_private,
    validate_step11_rc0028_experiment_private_execution,
)
from emlis_ai_step11_rc0029_experiment_runtime_adapter_v3 import (
    execute_step11_rc0029_experiment_private,
    validate_step11_rc0029_experiment_private_execution,
)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3"
)
_P5_PREDECESSOR = "3897331a5f605762e09f9953e47801d45d3c5da2"
_CONTROL_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
)
_EXPECTED_BODY_FREE_RESULT_SHA256 = {
    ("rc0028", "nls3s_b001_0001"): (
        "5f42aa4a0041ba96b39e63d2dac57338e5c88686449f07cf1e8a77317162da76"
    ),
    ("rc0029", "nls3s_b001_0001"): (
        "7c66fc8a2472c16f0b24abed043784945b8e87d58a610b4a9ad8cd04da4070d5"
    ),
    ("rc0029", "nls3s_b001_0002"): (
        "0455bb0be235506a783c351612432041312f29796710075ba374279e317ed5d5"
    ),
    ("rc0029", "nls3s_b001_0009"): (
        "b1a542511146f0a02790e2e2c6f42756655bf3cc33e80bfb9895568bb4869903"
    ),
}
_FROZEN_RC0029_PREFIXES = {
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py": (
        103_805,
        "43e99c6077e93db61908e11672d08122cb5928fe63fe64ae0ca565659b43bff4",
    ),
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py": (
        290_131,
        "2f797d7aad7f16b234b8a8dad57204b5788e4ae23e43306ac8ca5da790eba7a2",
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_natural_surface_matcher_v3.py"
    ): (
        589_793,
        "9bdae4b5c3d99e99dd01b622b9b191afbfa0e601789fba082a03c069b70028b5",
    ),
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py": (
        129_756,
        "6911291682508bcd6df66d39acb7a6b29b1cfc411434d1ff13160125c9af6c9a",
    ),
}
_PREDECESSOR_RUNTIME_OWNERS = (
    "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py",
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3.py"
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0029_experiment_runtime_adapter_v3.py"
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0028_experiment_surface_catalog_v3.py"
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0029_experiment_surface_catalog_v3.py"
    ),
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{_P5_PREDECESSOR}:{path}"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


@lru_cache(maxsize=1)
def _authority() -> tuple[
    dict[str, dict[str, Any]], dict[str, str], dict[str, str]
]:
    samples = {
        row["case_id"]: row
        for row in (
            json.loads(line)
            for line in (
                _FIXTURE_ROOT / "generated" / "batch_001.jsonl"
            ).read_text(encoding="utf-8").splitlines()
            if line
        )
    }
    batch_manifest = json.loads(
        (_FIXTURE_ROOT / "generated" / "batch_001_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    commitments = {
        row["case_id"]: row["case_commitment"]
        for row in batch_manifest["case_commitments"]
    }
    closures = {
        version: json.loads(
            (
                _FIXTURE_ROOT
                / "cycle_001"
                / filename
            ).read_text(encoding="utf-8")
        )["source_dependency_closure_sha256"]
        for version, filename in {
            "rc0028": (
                "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
            ),
            "rc0029": (
                "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
            ),
        }.items()
    }
    return samples, commitments, closures


def _execute(
    runner: Callable[..., Any],
    *,
    case_id: str,
    version: str,
) -> Any:
    samples, commitments, closures = _authority()
    return runner(
        samples[case_id]["input"],
        case_id=case_id,
        source_case_commitment=commitments[case_id],
        source_dependency_closure_sha256=closures[version],
    )


def test_rc0030_p5_keeps_rc0029_prefixes_byte_exact() -> None:
    for path, (byte_count, expected) in _FROZEN_RC0029_PREFIXES.items():
        source = (_REPO_ROOT / path).read_bytes()
        assert len(source) >= byte_count
        assert _sha256(source[:byte_count]) == expected


def test_rc0030_p5_keeps_shared_and_predecessor_runtime_owners_immutable() -> None:
    for path in _PREDECESSOR_RUNTIME_OWNERS:
        assert (_REPO_ROOT / path).read_bytes() == _git_bytes(path), path


def test_rc0030_p5_keeps_rc0028_selected_behavior_deterministic() -> None:
    first = _execute(
        execute_step11_rc0028_experiment_private,
        case_id=_CONTROL_IDS[0],
        version="rc0028",
    )
    second = _execute(
        execute_step11_rc0028_experiment_private,
        case_id=_CONTROL_IDS[0],
        version="rc0028",
    )
    assert validate_step11_rc0028_experiment_private_execution(first) == ()
    assert validate_step11_rc0028_experiment_private_execution(second) == ()
    assert first.body_free_result.disposition == "selected"
    assert first.body_free_result.result_sha256 == (
        _EXPECTED_BODY_FREE_RESULT_SHA256[("rc0028", _CONTROL_IDS[0])]
    )
    assert first.body_free_result == second.body_free_result
    assert first.selected_final_utf8_bytes == second.selected_final_utf8_bytes


def test_rc0030_p5_keeps_all_rc0029_controls_selected_without_regression() -> None:
    executions = tuple(
        _execute(
            execute_step11_rc0029_experiment_private,
            case_id=case_id,
            version="rc0029",
        )
        for case_id in _CONTROL_IDS
    )
    assert all(
        validate_step11_rc0029_experiment_private_execution(row) == ()
        for row in executions
    )
    assert all(row.body_free_result.disposition == "selected" for row in executions)
    assert all(row.body_free_result.closed_failure_codes == () for row in executions)
    assert all(row.selected_final_utf8_bytes is not None for row in executions)
    assert tuple(row.body_free_result.result_sha256 for row in executions) == tuple(
        _EXPECTED_BODY_FREE_RESULT_SHA256[("rc0029", case_id)]
        for case_id in _CONTROL_IDS
    )
