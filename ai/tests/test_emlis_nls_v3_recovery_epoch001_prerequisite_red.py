# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 001 Step 0-10 prerequisite remediation RED freeze.

This file reserves the next strict candidate identity and freezes only the
causal RED contracts needed to repair the Step 4, Step 5, and Step 10
prerequisite failures.  It does not implement any production owner, create a
successful completion receipt, lock a source baseline, or authorize a run.
"""

import ast
from copy import deepcopy
import hashlib
import importlib
import inspect
from pathlib import Path
import re
from types import ModuleType
from typing import Any

import pytest

import emlis_ai_semantic_obligation_inventory_v3 as inventory_module
import emlis_ai_step10_dependency_manifest_v3 as historical_step10_manifest


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP0_10_PREREQUISITE_"
    "NONCONFORMANCE_REMEDIATION_RED_FREEZE_ONLY"
)
_SOURCE_PIN = "c9739a0e2de5632d08607636656ada2f712c62b9"
_RECOVERY_CANDIDATE_VERSION_ID = "nls_v3_rc_0032"
_SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"
_SOURCE_PREDECESSOR_DISPOSITION = (
    "SOURCE_PREDECESSOR_ONLY_NOT_CYCLE_ACCEPTANCE"
)
_RECOVERY_SCOPE = "RECOVERY_EPOCH001_PREREQUISITE_ONLY"
_RECOVERY_BASELINE_MANIFEST_MODULE = (
    "emlis_ai_recovery_epoch001_source_baseline_manifest_v3"
)
_RECOVERY_BASELINE_MANIFEST_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
)
_RECOVERY_IMPLEMENTATION_PRESENT = True

_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"

_HISTORICAL_STEP10_MANIFEST_PATH = (
    "ai/services/ai_inference/emlis_ai_step10_dependency_manifest_v3.py"
)
_HISTORICAL_STEP10_MANIFEST_SOURCE_SHA256 = (
    "3bc1311c264cbbae71e69c643d055575e9b80c58b71d321ff28e744ad0ee090c"
)
_HISTORICAL_STEP10_CLOSURE_SHA256 = (
    "2b4cd6cb5ea0f0d69ae7de31930dd6833ba21fce8eb7262f579cad514f14a8e9"
)
_HISTORICAL_STEP10_ARTIFACT_SHA256 = (
    "83af18e635b16a7ca5680940f7362e9b844961bf2ac23101ba65a1b44fcc1af2"
)

_FUTURE_PRODUCTION_SURFACE = frozenset(
    {
        "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
        "ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py",
        _RECOVERY_BASELINE_MANIFEST_PATH,
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py",
        "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py",
        "ai/tools/emlis_nls_v3_batch_run.py",
    }
)
_FUTURE_TEST_SURFACE = frozenset(
    {
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py",
        "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py",
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py",
    }
)
_PROTECTED_PATHS = frozenset(
    {
        _HISTORICAL_STEP10_MANIFEST_PATH,
        "ai/services/ai_inference/emlis_ai_reply_service.py",
        "ai/services/ai_inference/emlis_ai_step11_cycle_evidence_v3.py",
    }
)

_STEP4_OWNER_RED = (
    "RECOVERY_EPOCH001_STEP4_REFINED_SOURCE_PARTITION_OWNER_NOT_PROVED"
)
_STEP4_INTEGRATION_RED = (
    "RECOVERY_EPOCH001_STEP4_REFINED_SOURCE_PARTITION_INTEGRATION_NOT_PROVED"
)
_STEP4_NEGATIVE_RED = (
    "RECOVERY_EPOCH001_STEP4_INDEPENDENT_NEGATIVE_PARTITION_NOT_PROVED"
)
_STEP5_GUARD_RED = (
    "RECOVERY_EPOCH001_STEP5_CLOSED_DEPENDENCY_GUARD_NOT_PROVED"
)
_STEP5_NEGATIVE_RED = (
    "RECOVERY_EPOCH001_STEP5_INDEPENDENT_NEGATIVE_GUARD_NOT_PROVED"
)
_STEP10_SUCCESSOR_RED = (
    "RECOVERY_EPOCH001_STEP10_VERSIONED_SUCCESSOR_CLOSURE_NOT_PROVED"
)
_STEP10_NEGATIVE_RED = (
    "RECOVERY_EPOCH001_STEP10_INDEPENDENT_SUCCESSOR_NEGATIVE_NOT_PROVED"
)

_REFINED_PARTITION_NEGATIVE_CODES = frozenset(
    {
        "REFINED_SOURCE_PARTITION_REQUIRED",
        "REFINED_SOURCE_ROLE_BINDING_INVALID",
        "REFINED_ORIGINAL_SOURCE_PRESERVATION_FAILED",
        "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH",
        "REFINED_SOURCE_ID_ALIAS_COLLISION",
        "REFINED_CROSS_SOURCE_BINDING_UNAUTHORIZED",
        "QUESTION_DECISION_SEMANTIC_SOURCE_FORBIDDEN",
        "REFINED_SOURCE_PARTITION_BODY_FREE_REQUIRED",
        "REFINED_CONTROL_PLANE_OWNER_DRIFT",
        "REFINED_RESOURCE_BOUND_POLICY_DRIFT",
    }
)
_DEPENDENCY_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_SOURCE_BASELINE_ENTRY_INVALID",
        "RECOVERY_SOURCE_BASELINE_REQUIRED_PATH_MISSING",
        "RECOVERY_SOURCE_BASELINE_EXTRA_PATH",
        "RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT",
        "RECOVERY_SOURCE_BASELINE_UNLISTED_IMPORTER",
        "RECOVERY_SOURCE_BASELINE_UNBOUND_LOCAL_IMPORT",
        "RECOVERY_SOURCE_BASELINE_OWNER_ROLE_MISMATCH",
        "RECOVERY_SOURCE_BASELINE_IMPORT_EDGE_FORBIDDEN",
        "RECOVERY_SOURCE_BASELINE_PUBLIC_DIRECT_IMPORT_FORBIDDEN",
        "RECOVERY_SOURCE_BASELINE_EVALUATION_CUE_INGRESS",
        "RECOVERY_SOURCE_BASELINE_RAW_BODY_INGRESS",
        "RECOVERY_SOURCE_BASELINE_DEFAULT_OWNER_OR_DORMANT_STATE_DRIFT",
        "RECOVERY_SOURCE_BASELINE_CANDIDATE_IDENTITY_INVALID",
        "RECOVERY_SOURCE_BASELINE_PREDECESSOR_BINDING_INVALID",
        "RECOVERY_SOURCE_BASELINE_HISTORICAL_STEP10_BINDING_INVALID",
    }
)
_DEPENDENCY_ROLES = frozenset(
    {
        "semantic_core",
        "offline_runtime",
        "evidence",
        "test",
        "tool",
        "contract",
    }
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload,
        usedforsecurity=False,
    ).hexdigest()


def _module_or_red(module_name: str, red_code: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            pytest.fail(red_code, pytrace=False)
        raise


def _issue_codes(value: Any) -> frozenset[str]:
    if not isinstance(value, (tuple, list, set, frozenset)):
        return frozenset()
    return frozenset(
        row if type(row) is str else str(getattr(row, "code", ""))
        for row in value
    )


def _imported_modules(path: Path) -> frozenset[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return frozenset(result)


def _body_free_refined_partition_probe() -> dict[str, Any]:
    """Hand-authored artifact used independently of the future builder."""

    return {
        "schema_version": "cocolon.emlis.nls_v3.refined_source_partition.v1",
        "stage": "refined_observation",
        "source_partitions": [
            {
                "source_role": "original_input",
                "source_id_namespace": "original_input",
                "source_ids": ["original_input:probe-001"],
                "plan_commitment_sha256": "1" * 64,
                "resolver_commitment_sha256": "2" * 64,
                "bundle_commitment_sha256": "3" * 64,
                "partition_commitment_sha256": "4" * 64,
                "obligation_kinds": [
                    "eligibility",
                    "evidence",
                    "nucleus",
                    "opportunity",
                    "reception",
                    "relation",
                    "safety_boundary",
                    "unknown",
                ],
                "owns_control_plane": True,
                "body_free": True,
            },
            {
                "source_role": "supplemental_answer",
                "source_id_namespace": "supplemental_answer",
                "source_ids": ["supplemental_answer:probe-001"],
                "plan_commitment_sha256": "5" * 64,
                "resolver_commitment_sha256": "6" * 64,
                "bundle_commitment_sha256": "7" * 64,
                "partition_commitment_sha256": "8" * 64,
                "obligation_kinds": [
                    "evidence",
                    "nucleus",
                    "relation",
                    "unknown",
                ],
                "owns_control_plane": False,
                "body_free": True,
            },
        ],
        "original_source_commitment_sha256": "4" * 64,
        "supplemental_source_commitment_sha256": "8" * 64,
        "semantic_source_roles": ["original_input", "supplemental_answer"],
        "stage_lineage_roles": [
            "original_input",
            "question_need_decision",
            "supplemental_answer",
        ],
        "question_need_decision_is_semantic_source": False,
        "control_plane_owner_role": "original_input",
        "trusted_future_authority": {
            "permitted_stage": "refined_observation",
            "question_decision_commitment_sha256": "9" * 64,
            "original_input_bundle_sha256": "3" * 64,
            "supplemental_answer_bundle_sha256": "7" * 64,
        },
        "cross_source_bindings": [],
        "resource_bound_policy": {
            "combined_obligations_must_satisfy_current_step1_bound": True,
            "implicit_bound_doubling_permitted": False,
        },
        "body_free": True,
    }


def _manifest_with_source_bytes(
    manifest: dict[str, Any],
    *,
    path: str,
    source: bytes,
) -> dict[str, Any]:
    mutated = deepcopy(manifest)
    mutated["files"][path]["sha256"] = hashlib.sha256(source).hexdigest()
    return mutated


def test_recovery_epoch001_red_scope_candidate_and_history_are_exact() -> None:
    assert _AUTHORITY.endswith("REMEDIATION_RED_FREEZE_ONLY")
    assert re.fullmatch(r"nls_v3_rc_[0-9]{4}", _RECOVERY_CANDIDATE_VERSION_ID)
    assert _RECOVERY_CANDIDATE_VERSION_ID == "nls_v3_rc_0032"
    assert _SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID == "nls_v3_rc_0027"
    assert _SOURCE_PREDECESSOR_DISPOSITION == (
        "SOURCE_PREDECESSOR_ONLY_NOT_CYCLE_ACCEPTANCE"
    )
    assert _RECOVERY_SCOPE == "RECOVERY_EPOCH001_PREREQUISITE_ONLY"
    assert _SOURCE_PIN == "c9739a0e2de5632d08607636656ada2f712c62b9"
    assert historical_step10_manifest.FROZEN_STEP10_CANDIDATE_VERSION_ID == (
        "nls_v3_rc_0010"
    )
    assert _sha256(_REPO_ROOT / _HISTORICAL_STEP10_MANIFEST_PATH) == (
        _HISTORICAL_STEP10_MANIFEST_SOURCE_SHA256
    )

    occurrences: set[str] = set()
    for root in (_AI_ROOT / "services", _AI_ROOT / "tools"):
        for path in root.rglob("*.py"):
            if _RECOVERY_CANDIDATE_VERSION_ID in path.read_text(encoding="utf-8"):
                occurrences.add(path.relative_to(_REPO_ROOT).as_posix())
    if _RECOVERY_IMPLEMENTATION_PRESENT:
        assert occurrences
        assert occurrences <= _FUTURE_PRODUCTION_SURFACE
    else:
        assert occurrences == set()


def test_recovery_epoch001_future_implementation_surface_is_exact_and_closed() -> None:
    assert len(_FUTURE_PRODUCTION_SURFACE) == 6
    assert len(_FUTURE_TEST_SURFACE) == 4
    assert not (_FUTURE_PRODUCTION_SURFACE & _PROTECTED_PATHS)
    assert not any(
        marker in path
        for path in _FUTURE_PRODUCTION_SURFACE | _FUTURE_TEST_SURFACE
        for marker in (
            "api_emotion_submit.py",
            "emlis_ai_reply_service.py",
            "step11_cycle_evidence",
            "fixtures/",
            "schemas/",
            "rn/",
            "database/",
        )
    )
    expected_new = {
        "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
        _RECOVERY_BASELINE_MANIFEST_PATH,
    }
    if _RECOVERY_IMPLEMENTATION_PRESENT:
        assert all((_REPO_ROOT / path).is_file() for path in expected_new)
    else:
        assert all(not (_REPO_ROOT / path).exists() for path in expected_new)


def test_recovery_epoch001_step10_collection_alias_is_assertion_neutral() -> None:
    path = (
        _AI_ROOT
        / "tests"
        / "test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    aliases = [
        alias
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "emlis_ai_dormant_runtime_adapter_v3"
        for alias in node.names
        if alias.name == "tester_allowlist_policy_sha256"
    ]
    assert len(aliases) == 1
    assert aliases[0].asname == "_tester_allowlist_policy_sha256"
    assert not any(
        isinstance(node, ast.Name)
        and node.id == "tester_allowlist_policy_sha256"
        for node in ast.walk(tree)
    )
    assert any(
        isinstance(node, ast.Name)
        and node.id == "_tester_allowlist_policy_sha256"
        for node in ast.walk(tree)
    )


def test_recovery_epoch001_default_public_and_historical_boundaries_are_frozen(
) -> None:
    reply_path = _INFERENCE_ROOT / "emlis_ai_reply_service.py"
    reply_source = reply_path.read_text(encoding="utf-8")
    assert '_NLS_V3_STEP10_PUBLIC_ROUTING_STATE = "disabled"' in reply_source
    assert _RECOVERY_BASELINE_MANIFEST_MODULE not in _imported_modules(reply_path)
    assert _HISTORICAL_STEP10_MANIFEST_PATH in _PROTECTED_PATHS
    assert "ai/services/ai_inference/emlis_ai_reply_service.py" in _PROTECTED_PATHS
    assert "ai/services/ai_inference/emlis_ai_step11_cycle_evidence_v3.py" in (
        _PROTECTED_PATHS
    )


def test_recovery_epoch001_step5_raw_text_guard_conflict_is_causally_frozen() -> None:
    target_modules = frozenset(
        {
            "emlis_ai_grounded_observation_semantic_restatement_v3",
            "emlis_ai_observation_stage_context_v3",
            "emlis_ai_semantic_obligation_inventory_v3",
            "emlis_ai_content_selection_v3",
        }
    )
    direct_importers = {
        "ai/services/ai_inference/"
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3.py": (
            "8d4ceb1e4a45655569516ea93ae5696972adb8fd"
        ),
        "ai/services/ai_inference/"
        "emlis_ai_grounded_lexical_role_experiment_snapshot_v3.py": (
            "262ab4332c7797b2b94f050536a3f3e82638a06d"
        ),
        "ai/services/ai_inference/"
        "emlis_ai_grounded_relation_construction_authority_successor_v3.py": (
            "d622874a8ac2c9686a2e716c55c5b7816b46efa8"
        ),
        "ai/services/ai_inference/"
        "emlis_ai_step11_rc0031_reception_focus_authority_v3.py": (
            "7ddd4b62a5a46bf55bb97063d58801228849dd68"
        ),
    }
    declaration_only = {
        "ai/services/ai_inference/"
        "emlis_ai_rc0028_experiment_dependency_manifest_v3.py": (
            "c8111fd28714ef596d67c42fe1936d9a560db643"
        )
    }
    for relative_path, blob in direct_importers.items():
        path = _REPO_ROOT / relative_path
        assert _git_blob_sha1(path) == blob
        assert _imported_modules(path) & target_modules
    for relative_path, blob in declaration_only.items():
        path = _REPO_ROOT / relative_path
        assert _git_blob_sha1(path) == blob
        assert not (_imported_modules(path) & target_modules)
        assert any(
            module in path.read_text(encoding="utf-8")
            for module in target_modules
        )
    assert not (
        set(direct_importers) | set(declaration_only)
    ) & _FUTURE_PRODUCTION_SURFACE


def test_recovery_epoch001_step4_refined_partition_owner_is_proved_or_red() -> None:
    owner = _module_or_red("emlis_ai_refined_source_partition_v3", _STEP4_OWNER_RED)
    assert getattr(owner, "REFINED_SOURCE_PARTITION_SCHEMA", None) == (
        "cocolon.emlis.nls_v3.refined_source_partition.v1"
    )
    assert type(getattr(owner, "RefinedSourcePartitionError", None)) is type
    build = getattr(owner, "build_refined_source_partition", None)
    validate = getattr(owner, "validate_refined_source_partition", None)
    validate_shape = getattr(
        owner,
        "validate_refined_source_partition_shape",
        None,
    )
    assert callable(build), _STEP4_OWNER_RED
    assert callable(validate), _STEP4_OWNER_RED
    assert callable(validate_shape), _STEP4_OWNER_RED
    expected_build_parameters = (
        "original_plan",
        "original_resolver",
        "supplemental_plan",
        "supplemental_resolver",
        "observation_stage_context",
        "original_input_bundle",
        "supplemental_answer_bundle",
        "trusted_future_authority",
    )
    assert tuple(inspect.signature(build).parameters) == expected_build_parameters
    assert tuple(inspect.signature(validate).parameters) == (
        "value",
        *expected_build_parameters,
    )
    assert _REFINED_PARTITION_NEGATIVE_CODES <= frozenset(
        getattr(owner, "REFINED_SOURCE_PARTITION_NEGATIVE_CODES", ())
    )


def test_recovery_epoch001_step4_independent_partition_mutations_are_proved_or_red(
) -> None:
    owner = _module_or_red(
        "emlis_ai_refined_source_partition_v3",
        _STEP4_NEGATIVE_RED,
    )
    validate_shape = owner.validate_refined_source_partition_shape
    probe = _body_free_refined_partition_probe()
    assert _issue_codes(validate_shape(probe)) == frozenset()

    missing_owner = deepcopy(probe)
    missing_owner.pop("source_partitions")
    assert "REFINED_SOURCE_PARTITION_REQUIRED" in _issue_codes(
        validate_shape(missing_owner)
    )

    role_swap = deepcopy(probe)
    role_swap["source_partitions"][0]["source_role"] = "supplemental_answer"
    role_swap["source_partitions"][1]["source_role"] = "original_input"
    assert "REFINED_SOURCE_ROLE_BINDING_INVALID" in _issue_codes(
        validate_shape(role_swap)
    )

    original_overwrite = deepcopy(probe)
    original_overwrite["source_partitions"][0][
        "partition_commitment_sha256"
    ] = "8" * 64
    assert "REFINED_ORIGINAL_SOURCE_PRESERVATION_FAILED" in _issue_codes(
        validate_shape(original_overwrite)
    )

    commitment_mismatch = deepcopy(probe)
    commitment_mismatch["trusted_future_authority"][
        "original_input_bundle_sha256"
    ] = "0" * 64
    assert "REFINED_SOURCE_PARTITION_COMMITMENT_MISMATCH" in _issue_codes(
        validate_shape(commitment_mismatch)
    )

    id_collision = deepcopy(probe)
    id_collision["source_partitions"][1]["source_ids"] = list(
        id_collision["source_partitions"][0]["source_ids"]
    )
    assert "REFINED_SOURCE_ID_ALIAS_COLLISION" in _issue_codes(
        validate_shape(id_collision)
    )

    unauthorized_binding = deepcopy(probe)
    unauthorized_binding["cross_source_bindings"] = [
        {
            "from_source_id": "original_input:probe-001",
            "to_source_id": "supplemental_answer:probe-001",
        }
    ]
    assert "REFINED_CROSS_SOURCE_BINDING_UNAUTHORIZED" in _issue_codes(
        validate_shape(unauthorized_binding)
    )

    question_as_source = deepcopy(probe)
    question_as_source["question_need_decision_is_semantic_source"] = True
    assert "QUESTION_DECISION_SEMANTIC_SOURCE_FORBIDDEN" in _issue_codes(
        validate_shape(question_as_source)
    )

    body_leak = deepcopy(probe)
    body_leak["raw_body"] = "synthetic-probe-must-not-be-accepted"
    assert "REFINED_SOURCE_PARTITION_BODY_FREE_REQUIRED" in _issue_codes(
        validate_shape(body_leak)
    )

    control_plane_drift = deepcopy(probe)
    control_plane_drift["control_plane_owner_role"] = "supplemental_answer"
    assert "REFINED_CONTROL_PLANE_OWNER_DRIFT" in _issue_codes(
        validate_shape(control_plane_drift)
    )

    resource_policy_drift = deepcopy(probe)
    resource_policy_drift["resource_bound_policy"][
        "implicit_bound_doubling_permitted"
    ] = True
    assert "REFINED_RESOURCE_BOUND_POLICY_DRIFT" in _issue_codes(
        validate_shape(resource_policy_drift)
    )


def test_recovery_epoch001_step4_inventory_integration_is_proved_or_red() -> None:
    parameters = inspect.signature(
        inventory_module.build_grounded_source_snapshot
    ).parameters
    if "refined_source_partition" not in parameters:
        pytest.fail(_STEP4_INTEGRATION_RED, pytrace=False)
    source = inspect.getsource(inventory_module.build_grounded_source_snapshot)
    assert "validate_refined_source_partition" in source, _STEP4_INTEGRATION_RED
    assert "original_input" in source and "supplemental_answer" in source


def test_recovery_epoch001_step5_closed_dependency_guard_is_proved_or_red() -> None:
    owner = _module_or_red(
        _RECOVERY_BASELINE_MANIFEST_MODULE,
        _STEP5_GUARD_RED,
    )
    assert getattr(owner, "RECOVERY_EPOCH001_CANDIDATE_VERSION_ID", None) == (
        _RECOVERY_CANDIDATE_VERSION_ID
    )
    assert getattr(owner, "RECOVERY_EPOCH001_SCOPE", None) == _RECOVERY_SCOPE
    assert getattr(
        owner,
        "RECOVERY_EPOCH001_SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID",
        None,
    ) == _SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID
    assert getattr(
        owner,
        "RECOVERY_EPOCH001_SOURCE_PREDECESSOR_DISPOSITION",
        None,
    ) == _SOURCE_PREDECESSOR_DISPOSITION
    assert getattr(
        owner,
        "RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST_SCHEMA",
        None,
    ) == (
        "cocolon.emlis.nls_v3.recovery_epoch001_source_baseline_manifest.v1"
    )
    manifest = getattr(owner, "RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST", None)
    assert type(manifest) is dict, _STEP5_GUARD_RED
    assert callable(
        getattr(owner, "build_recovery_epoch001_source_baseline_manifest", None)
    )
    assert callable(
        getattr(owner, "validate_recovery_epoch001_source_baseline_manifest", None)
    )
    assert callable(
        getattr(
            owner,
            "validate_recovery_epoch001_source_baseline_manifest_shape",
            None,
        )
    )
    assert callable(
        getattr(owner, "fresh_recovery_epoch001_source_closure_sha256", None)
    )
    assert callable(getattr(owner, "validate_recovery_epoch001_source_guard", None))
    assert _issue_codes(
        owner.validate_recovery_epoch001_source_baseline_manifest()
    ) == frozenset()
    assert manifest.get("candidate_version_id") == _RECOVERY_CANDIDATE_VERSION_ID
    assert manifest.get("scope") == _RECOVERY_SCOPE
    assert manifest.get("body_free") is True


def test_recovery_epoch001_step5_independent_negative_guard_is_proved_or_red() -> None:
    owner = _module_or_red(
        _RECOVERY_BASELINE_MANIFEST_MODULE,
        _STEP5_NEGATIVE_RED,
    )
    assert _DEPENDENCY_NEGATIVE_CODES <= frozenset(
        getattr(owner, "RECOVERY_EPOCH001_SOURCE_BASELINE_NEGATIVE_CODES", ())
    )
    validate_shape = owner.validate_recovery_epoch001_source_baseline_manifest_shape
    source_guard = owner.validate_recovery_epoch001_source_guard
    manifest = deepcopy(owner.RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST)
    assert _issue_codes(validate_shape(manifest)) == frozenset()
    assert type(manifest.get("files")) is dict and manifest["files"]
    assert all(
        type(row) is dict
        and set(row) == {"sha256", "role", "runtime_connected", "body_free"}
        for row in manifest["files"].values()
    )
    assert {
        row.get("role")
        for row in manifest["files"].values()
        if type(row) is dict
    } <= _DEPENDENCY_ROLES

    inventory_path = (
        "ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py"
    )
    content_selection_path = (
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
    )
    reply_path = "ai/services/ai_inference/emlis_ai_reply_service.py"
    adapter_path = (
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py"
    )
    step5_test_path = (
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py"
    )
    required_paths = {
        inventory_path,
        content_selection_path,
        reply_path,
        adapter_path,
        step5_test_path,
    }
    assert required_paths <= set(manifest["files"])

    missing = deepcopy(manifest)
    missing["files"].pop(inventory_path)
    assert "RECOVERY_SOURCE_BASELINE_REQUIRED_PATH_MISSING" in _issue_codes(
        validate_shape(missing)
    )

    extra = deepcopy(manifest)
    extra["files"][
        "ai/services/ai_inference/emlis_ai_unlisted_recovery_probe_v3.py"
    ] = {
        "sha256": "a" * 64,
        "role": "semantic_core",
        "runtime_connected": False,
        "body_free": True,
    }
    assert "RECOVERY_SOURCE_BASELINE_EXTRA_PATH" in _issue_codes(
        validate_shape(extra)
    )

    first_path = sorted(manifest["files"])[0]
    invalid_hash = deepcopy(manifest)
    invalid_hash["files"][first_path]["sha256"] = "0" * 64
    assert "RECOVERY_SOURCE_BASELINE_ENTRY_INVALID" in _issue_codes(
        validate_shape(invalid_hash)
    )

    forbidden_role = deepcopy(manifest)
    forbidden_role["files"][first_path]["role"] = "public_runtime"
    assert "RECOVERY_SOURCE_BASELINE_OWNER_ROLE_MISMATCH" in _issue_codes(
        validate_shape(forbidden_role)
    )

    drift_source = b"# recovery epoch source hash drift probe\n"
    assert "RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT" in _issue_codes(
        source_guard(inventory_path, drift_source, manifest)
    )

    assert "RECOVERY_SOURCE_BASELINE_UNLISTED_IMPORTER" in _issue_codes(
        source_guard(
            "ai/services/ai_inference/emlis_ai_not_in_baseline_v3.py",
            b"import emlis_ai_semantic_obligation_inventory_v3\n",
            manifest,
        )
    )

    unbound_source = b"import emlis_ai_unbound_recovery_probe_v3\n"
    unbound_manifest = _manifest_with_source_bytes(
        manifest,
        path=content_selection_path,
        source=unbound_source,
    )
    assert "RECOVERY_SOURCE_BASELINE_UNBOUND_LOCAL_IMPORT" in _issue_codes(
        source_guard(content_selection_path, unbound_source, unbound_manifest)
    )

    public_direct_source = (
        b"import emlis_ai_semantic_obligation_inventory_v3\n"
    )
    public_direct_manifest = _manifest_with_source_bytes(
        manifest,
        path=reply_path,
        source=public_direct_source,
    )
    assert (
        "RECOVERY_SOURCE_BASELINE_PUBLIC_DIRECT_IMPORT_FORBIDDEN"
        in _issue_codes(
            source_guard(reply_path, public_direct_source, public_direct_manifest)
        )
    )

    forbidden_edge_source = (
        b"import test_emlis_nls_v3_s5_content_selection_stage_context\n"
    )
    forbidden_edge_manifest = _manifest_with_source_bytes(
        manifest,
        path=adapter_path,
        source=forbidden_edge_source,
    )
    assert "RECOVERY_SOURCE_BASELINE_IMPORT_EDGE_FORBIDDEN" in _issue_codes(
        source_guard(adapter_path, forbidden_edge_source, forbidden_edge_manifest)
    )

    cue_source = b'EXPECTED_ANSWER_CUE = "forbidden"\n'
    cue_manifest = _manifest_with_source_bytes(
        manifest,
        path=content_selection_path,
        source=cue_source,
    )
    assert "RECOVERY_SOURCE_BASELINE_EVALUATION_CUE_INGRESS" in _issue_codes(
        source_guard(content_selection_path, cue_source, cue_manifest)
    )

    raw_body_source = b"raw_input = request.body\n"
    raw_body_manifest = _manifest_with_source_bytes(
        manifest,
        path=content_selection_path,
        source=raw_body_source,
    )
    assert "RECOVERY_SOURCE_BASELINE_RAW_BODY_INGRESS" in _issue_codes(
        source_guard(content_selection_path, raw_body_source, raw_body_manifest)
    )

    declaration_only_source = (
        b'DEPENDENCY_PATH = "emlis_ai_semantic_obligation_inventory_v3"\n'
    )
    declaration_only_manifest = _manifest_with_source_bytes(
        manifest,
        path=content_selection_path,
        source=declaration_only_source,
    )
    declaration_codes = _issue_codes(
        source_guard(
            content_selection_path,
            declaration_only_source,
            declaration_only_manifest,
        )
    )
    assert not declaration_codes & {
        "RECOVERY_SOURCE_BASELINE_UNBOUND_LOCAL_IMPORT",
        "RECOVERY_SOURCE_BASELINE_IMPORT_EDGE_FORBIDDEN",
        "RECOVERY_SOURCE_BASELINE_PUBLIC_DIRECT_IMPORT_FORBIDDEN",
    }


def test_recovery_epoch001_step10_versioned_successor_is_proved_or_red() -> None:
    owner = _module_or_red(
        _RECOVERY_BASELINE_MANIFEST_MODULE,
        _STEP10_SUCCESSOR_RED,
    )
    manifest = owner.RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST
    assert owner.RECOVERY_EPOCH001_CANDIDATE_VERSION_ID == (
        _RECOVERY_CANDIDATE_VERSION_ID
    )
    assert manifest["source_predecessor"] == {
        "candidate_version_id": _SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID,
        "disposition": _SOURCE_PREDECESSOR_DISPOSITION,
    }
    assert manifest["historical_step10"] == {
        "candidate_version_id": "nls_v3_rc_0010",
        "manifest_source_sha256": _HISTORICAL_STEP10_MANIFEST_SOURCE_SHA256,
        "manifest_artifact_sha256": _HISTORICAL_STEP10_ARTIFACT_SHA256,
        "dependency_closure_sha256": _HISTORICAL_STEP10_CLOSURE_SHA256,
        "disposition": "HISTORICAL_IMMUTABLE_NOT_CURRENT_AUTHORITY",
    }
    frozen = owner.FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256
    assert re.fullmatch(r"[0-9a-f]{64}", frozen) and frozen != "0" * 64
    assert manifest["source_closure_sha256"] == frozen
    assert owner.fresh_recovery_epoch001_source_closure_sha256() == frozen

    runtime_boundary = manifest["step10_runtime_boundary"]
    assert runtime_boundary["default_public_routing_state"] == "disabled"
    assert runtime_boundary["production_owner"] == (
        "grounded_sentence_surface_canonical_v1"
    )
    assert runtime_boundary["v3_general_account_visible"] is False
    assert runtime_boundary["owner_activation_permitted"] is False
    assert runtime_boundary["reply_service_public_export"] == [
        "render_emlis_ai_reply"
    ]

    expected_importers = {
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py",
        "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py",
        "ai/tools/emlis_nls_v3_batch_run.py",
    }
    assert all(
        _RECOVERY_BASELINE_MANIFEST_MODULE in _imported_modules(_REPO_ROOT / path)
        for path in expected_importers
    )


def test_recovery_epoch001_step10_independent_successor_mutations_are_proved_or_red(
) -> None:
    owner = _module_or_red(
        _RECOVERY_BASELINE_MANIFEST_MODULE,
        _STEP10_NEGATIVE_RED,
    )
    validate_shape = owner.validate_recovery_epoch001_source_baseline_manifest_shape
    manifest = deepcopy(owner.RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST)

    reused_candidate = deepcopy(manifest)
    reused_candidate["candidate_version_id"] = "nls_v3_rc_0010"
    assert "RECOVERY_SOURCE_BASELINE_CANDIDATE_IDENTITY_INVALID" in _issue_codes(
        validate_shape(reused_candidate)
    )

    predecessor_as_acceptance = deepcopy(manifest)
    predecessor_as_acceptance["source_predecessor"]["disposition"] = (
        "CYCLE_ACCEPTED_PARENT"
    )
    assert (
        "RECOVERY_SOURCE_BASELINE_PREDECESSOR_BINDING_INVALID"
        in _issue_codes(validate_shape(predecessor_as_acceptance))
    )

    historical_rewrite = deepcopy(manifest)
    historical_rewrite["historical_step10"]["dependency_closure_sha256"] = (
        "a" * 64
    )
    assert (
        "RECOVERY_SOURCE_BASELINE_HISTORICAL_STEP10_BINDING_INVALID"
        in _issue_codes(validate_shape(historical_rewrite))
    )

    public_enable = deepcopy(manifest)
    public_enable["step10_runtime_boundary"][
        "default_public_routing_state"
    ] = "enabled"
    assert (
        "RECOVERY_SOURCE_BASELINE_DEFAULT_OWNER_OR_DORMANT_STATE_DRIFT"
        in _issue_codes(validate_shape(public_enable))
    )

    public_export = deepcopy(manifest)
    public_export["step10_runtime_boundary"]["reply_service_public_export"].append(
        "render_emlis_ai_reply_v3"
    )
    assert (
        "RECOVERY_SOURCE_BASELINE_DEFAULT_OWNER_OR_DORMANT_STATE_DRIFT"
        in _issue_codes(validate_shape(public_export))
    )
