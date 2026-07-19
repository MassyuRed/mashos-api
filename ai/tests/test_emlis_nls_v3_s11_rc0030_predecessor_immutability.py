# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 byte authority and phase-aware historical evidence for rc0030."""

import ast
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


_REPO_ROOT = Path(__file__).resolve().parents[2]
_P5_PREDECESSOR = "3897331a5f605762e09f9953e47801d45d3c5da2"
_P4_PHASE_PREDECESSOR = "afcd089a872d71b07930592b068bdc3d480b8e3b"
_P4_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0030_surface_planning_experiment.json"
)
_P4_EXACT7_SHA256 = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3.py"
    ): "72c664eec03cf4b29315ae7badc8a85e70f6830d8de745335458c7c633eb5876",
    (
        "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py"
    ): "1926ef12e74f1a9f53015f2d913cbb4b6881606e57e5078c6f8192e2894af4c7",
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3.py"
    ): "139bd2d052fa3362bde86e6e88b039e9fddbd91caf48155cc738265fc22de9c6",
    _P4_MANIFEST_PATH: (
        "147c395d6250553aa9fa2fc1c14888b357827f6f8d8bf64f2dae18e71fd33f60"
    ),
    (
        "ai/tests/test_emlis_nls_v3_s11_rc0030_dependency_closure.py"
    ): "da348ed69fa192e06973c4f64c6215aa46732be6bb161afb0e25f6e0d4cb298c",
    (
        "ai/tests/test_emlis_nls_v3_s11_rc0030_runtime_disconnect.py"
    ): "8f674cbce686aad20978e7822469d3cb3499e1ad16caf99b9b2a99551db6ac3a",
    (
        "ai/tools/"
        "emlis_nls_v3_rc0030_surface_planning_dependency_manifest.py"
    ): "ace6031aa7882853bca2e3e3606192a36d7177aa5c0907d5474d62c644f61ab8",
}
_P4_MANIFEST_ARTIFACT_SHA256 = (
    "ec0f49f013ac4814749ad928849ff5382c9df97bb5fb78df3e89cb75143932f1"
)
_P4_SOURCE_CLOSURE_SHA256 = (
    "29abbb08da497c902ea56cffbc82703801c7228f86e8a4f0f95d00800c31456b"
)
_P4_OWNER_SHA256 = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_natural_surface_matcher_v3.py"
    ): "629305364ac50530265d7d87a6ca28678eb3e1be6ac7289ae770b3b5f871d8c9",
    (
        "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py"
    ): "1926ef12e74f1a9f53015f2d913cbb4b6881606e57e5078c6f8192e2894af4c7",
}
_CURRENT_BYTE_IMMUTABLE = (
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3.py"
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3.py"
    ),
    (
        "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
        "rc0030_representative8_body_free.json"
    ),
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_mutation.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_runtime_disconnect.py",
)
_HISTORICAL_TESTS = {
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_mutation.py": {
        "sha256": (
            "b04e8a6c6038ebc0dfde8b15d520ec9454f290977f611b295c7765299035925e"
        ),
        "node": (
            "test_rc0030_p2_frozen_prefix_p1_and_forward_source_scope_are_exact"
        ),
        "stage_lock": "STEP11_RC0030_P2_RUNTIME_ADAPTER_EARLY",
        "current_bytes_immutable": True,
    },
    "ai/tests/test_emlis_nls_v3_s11_rc0030_forward_inverse_independence.py": {
        "sha256": (
            "e910ba05b8a272784b3a9704604eec510eb153993b1ab094476d5b19631ba30e"
        ),
        "node": "test_rc0030_p3_p2_predecessor_and_inverse_scope_are_exact",
        "stage_lock": "STEP11_RC0030_P3_FROZEN_AUTHORITY_DRIFT",
        "p5_current_stage_lock": "STEP11_RC0030_P3_MATCHER_SUFFIX_DRIFT",
        "current_bytes_immutable": True,
    },
    "ai/tests/test_emlis_nls_v3_s11_rc0029_runtime_disconnect.py": {
        "sha256": (
            "192282d51af4da071a0c2172f95eaa4d8baa4bbb0c08ba44cde227265b41272e"
        ),
        "node": "test_rc0029_has_no_shared_or_public_reverse_import",
        "stage_lock": "find_rc0029_surface_repair_forbidden_reverse_imports",
        "current_bytes_immutable": True,
    },
    "ai/tests/test_emlis_nls_v3_s11_rc0030_dependency_closure.py": {
        "sha256": (
            "da348ed69fa192e06973c4f64c6215aa46732be6bb161afb0e25f6e0d4cb298c"
        ),
        "node": "test_rc0030_p4_manifest_rebuilds_from_immutable_rc0029",
        "stage_lock": "P4_GATE_RUNTIME_CLOSURE",
        "current_bytes_immutable": False,
    },
}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _git_bytes(path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{_P5_PREDECESSOR}:{path}"],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _has_skip_or_xfail(source: str) -> bool:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if (
            isinstance(function, ast.Attribute)
            and function.attr in {"skip", "skipif", "xfail"}
        ):
            return True
    return False


def test_rc0030_p5_predecessor_is_the_exact_p4_git_commit() -> None:
    object_type = subprocess.run(
        ["git", "cat-file", "-t", _P5_PREDECESSOR],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert object_type == "commit"
    for path, expected in _P4_EXACT7_SHA256.items():
        assert _sha256(_git_bytes(path)) == expected


def test_rc0030_p5_predecessor_binds_p4_manifest_and_exact_two_owners() -> None:
    manifest_bytes = _git_bytes(_P4_MANIFEST_PATH)
    manifest: dict[str, Any] = json.loads(manifest_bytes)
    assert _sha256(manifest_bytes) == _P4_EXACT7_SHA256[_P4_MANIFEST_PATH]
    assert artifact_sha256(manifest) == _P4_MANIFEST_ARTIFACT_SHA256
    assert manifest["manifest_phase"] == "P4_GATE_RUNTIME_CLOSURE"
    assert manifest["phase_predecessor_git_commit"] == _P4_PHASE_PREDECESSOR
    assert (
        manifest["source_dependency_closure_sha256"]
        == _P4_SOURCE_CLOSURE_SHA256
    )
    assert manifest["source_file_count"] == 219
    policy = manifest["activation_policy"]
    assert len(policy["active_new_paths"]) == 11
    assert len(policy["reserved_absent_paths"]) == 7
    assert policy["exact18_is_closed_maximum"] is True
    for path, expected in _P4_OWNER_SHA256.items():
        assert _sha256(_git_bytes(path)) == expected


def test_rc0030_p5_preserves_every_non_successor_p4_path_byte_exactly() -> None:
    for path in _CURRENT_BYTE_IMMUTABLE:
        assert (_REPO_ROOT / path).read_bytes() == _git_bytes(path), path


def test_rc0030_p5_historical_stage_locks_are_hash_bound_and_unsuppressed() -> None:
    for path, contract in _HISTORICAL_TESTS.items():
        predecessor = _git_bytes(path)
        source = predecessor.decode("utf-8")
        assert _sha256(predecessor) == contract["sha256"]
        assert f"def {contract['node']}(" in source
        assert contract["stage_lock"] in source
        if "p5_current_stage_lock" in contract:
            assert contract["p5_current_stage_lock"] in source
        assert _has_skip_or_xfail(source) is False
        if contract["current_bytes_immutable"]:
            assert (_REPO_ROOT / path).read_bytes() == predecessor
