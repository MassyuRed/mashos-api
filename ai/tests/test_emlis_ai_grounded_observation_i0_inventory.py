# -*- coding: utf-8 -*-
from __future__ import annotations

"""I0 guards for evidence freeze, reachability, and content ownership."""

from pathlib import Path

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    DISPOSITION_ISOLATE_FIXTURE,
    DISPOSITION_KEEP_FUNCTIONAL,
    DISPOSITION_KEEP_SAFETY,
    DISPOSITION_REMOVE_SUBSTANTIVE,
    GROUND_OBSERVATION_I0_FILE_FINGERPRINTS,
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
    GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES,
    GROUND_OBSERVATION_I0_REACHABLE_PHRASE_COUNTS,
    GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY,
    GROUND_OBSERVATION_I0_RUNTIME_MODULE_OWNERSHIP,
    ISSUE_METADATA_TRUTH,
    REACHABILITY_DIAGNOSTIC,
    REACHABILITY_PRODUCTION,
    REACHABILITY_SHADOW,
    REACHABILITY_TEST,
    build_ground_observation_i0_runtime_import_graph,
    evaluate_ground_observation_i0_negative_reachability,
    ground_observation_i0_reachable_modules,
    validate_ground_observation_i0_inventory,
)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_AI_INFERENCE_ROOT = _BACKEND_ROOT / "ai" / "services" / "ai_inference"
_REPLY_SERVICE_MODULE = "emlis_ai_reply_service"


def _module_graph() -> tuple[dict[str, Path], dict[str, set[str]], set[str]]:
    modules, edges = build_ground_observation_i0_runtime_import_graph(_BACKEND_ROOT)
    reachable = set(ground_observation_i0_reachable_modules(_REPLY_SERVICE_MODULE, edges))
    return modules, edges, reachable


def test_i0_inventory_schema_and_failure_evidence_are_complete() -> None:
    validate_ground_observation_i0_inventory()
    assert {entry.disposition for entry in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY} == {
        DISPOSITION_KEEP_FUNCTIONAL,
        DISPOSITION_KEEP_SAFETY,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        DISPOSITION_ISOLATE_FIXTURE,
    }
    assert {entry.reachability for entry in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY} == {
        REACHABILITY_PRODUCTION,
        REACHABILITY_DIAGNOSTIC,
        REACHABILITY_TEST,
        REACHABILITY_SHADOW,
    }
    metadata_truth_entries = [
        entry for entry in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY
        if entry.issue_kind == ISSUE_METADATA_TRUTH
    ]
    assert {entry.file_path for entry in metadata_truth_entries} == {
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "ai/services/ai_inference/emlis_ai_input_material_bundle.py",
        "ai/services/ai_inference/emlis_ai_self_denial_safe_state_answer.py",
    }
    for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES:
        expectation = case.as_structural_expectation()
        assert expectation["expected_exact_comment_text"] is None
        assert expectation["runtime_case_route_allowed"] is False
        assert case.legacy_runtime_fact_codes
        assert all("。" not in code and "、" not in code for code in case.required_structure_codes)
        assert all("。" not in code and "、" not in code for code in case.prohibited_structure_codes)
        assert case.legacy_visible_body not in str(expectation)


def test_i0_final_cutover_fingerprints_remain_a_historical_snapshot() -> None:
    paths: set[str] = set()
    for item in GROUND_OBSERVATION_I0_FILE_FINGERPRINTS:
        path = _BACKEND_ROOT / item.file_path
        assert path.exists()
        assert item.file_path not in paths
        paths.add(item.file_path)
        assert len(item.sha256) == 64
        int(item.sha256, 16)


def test_i0_inventory_symbols_and_tokens_resolve_to_actual_files() -> None:
    for item in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY:
        path = _BACKEND_ROOT / item.file_path
        assert path.exists()
        source = path.read_text(encoding="utf-8")
        for token in item.source_tokens:
            assert token in source


def test_i0_runtime_reachability_ownership_matches_actual_import_graph() -> None:
    modules, edges, reachable = _module_graph()
    reverse_edges: dict[str, set[str]] = {name: set() for name in modules}
    for caller, callees in edges.items():
        for callee in callees:
            reverse_edges[callee].add(caller)

    for item in GROUND_OBSERVATION_I0_RUNTIME_MODULE_OWNERSHIP:
        assert item.module_name in modules
        assert modules[item.module_name] == _BACKEND_ROOT / item.file_path
        assert tuple(sorted(reverse_edges[item.module_name])) == item.direct_callers
        assert tuple(sorted(edges[item.module_name])) == item.direct_callees
        for test_owner_path in item.test_owner_paths:
            assert (_BACKEND_ROOT / test_owner_path).exists()
        if item.reachability == REACHABILITY_PRODUCTION:
            assert item.module_name in reachable
        else:
            assert item.module_name not in reachable

    for item in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY:
        path = Path(item.file_path)
        if path.suffix != ".py" or "tests" in path.parts:
            continue
        module_name = path.stem
        assert module_name in modules
        if item.reachability == REACHABILITY_PRODUCTION:
            assert module_name in reachable
        elif item.reachability in {REACHABILITY_DIAGNOSTIC, REACHABILITY_SHADOW}:
            assert module_name not in reachable
    assert "emlis_ai_response_contract_qa_matrix" not in reachable
    assert {
        "emlis_ai_grounded_observation_plan",
        "emlis_ai_grounded_sentence_surface",
        "emlis_ai_grounded_observation_gate",
    } <= reachable
    assert not GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES.intersection(reachable)


def test_i0_fb172_b7_retired_routes_and_tokens_have_zero_public_reply_reachability() -> None:
    assert evaluate_ground_observation_i0_negative_reachability(_BACKEND_ROOT) == ()


def test_i0_known_fixture_phrase_occurrences_cannot_increase_in_reachable_runtime() -> None:
    modules, _edges, reachable = _module_graph()
    for phrase, expected_by_file in GROUND_OBSERVATION_I0_REACHABLE_PHRASE_COUNTS.items():
        actual_by_file: dict[str, int] = {}
        for module_name in reachable:
            path = modules[module_name]
            count = path.read_text(encoding="utf-8").count(phrase)
            if count:
                actual_by_file[path.name] = count
        assert actual_by_file == expected_by_file


def test_i0_canonical_runtime_modules_contain_no_abcd_fixture_phrases() -> None:
    for module_name in (
        "emlis_ai_grounded_observation_plan.py",
        "emlis_ai_grounded_sentence_surface.py",
        "emlis_ai_grounded_observation_gate.py",
    ):
        source = (_AI_INFERENCE_ROOT / module_name).read_text(encoding="utf-8")
        for phrase in GROUND_OBSERVATION_I0_REACHABLE_PHRASE_COUNTS:
            assert phrase not in source


def test_i0_display_contract_and_semantic_quality_owners_are_separate() -> None:
    test_entry = next(
        entry for entry in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY
        if entry.file_path == "ai/tests/test_emlis_ai_phase20_10_real_device_recheck.py"
    )
    diagnostic_entry = next(
        entry for entry in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY
        if entry.file_path == "ai/services/ai_inference/emlis_ai_response_contract_qa_matrix.py"
    )
    assert test_entry.reachability == REACHABILITY_TEST
    assert diagnostic_entry.reachability == REACHABILITY_DIAGNOSTIC
    assert test_entry.disposition == diagnostic_entry.disposition == DISPOSITION_ISOLATE_FIXTURE
    assert "Product Read Feel" in test_entry.rationale

    source = (_BACKEND_ROOT / test_entry.file_path).read_text(encoding="utf-8")
    assert "何があったか" not in source
    assert "事実として確定" not in source
    assert 'assert "見えたこと："' not in source
    assert 'assert "Emlisから："' not in source
    assert "visible_material_slots" not in source
    assert "unknown_slots" not in source
    assert "gate_recovery_attempts" not in source
    assert '"actual_device_evidence": False' in source
    assert "product_readfeel_status" in source
    assert "grounded_observation" in source
    assert "def test_phase20_10_real_device" not in source
