# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_module_inventory import build_p7_module_inventory
from emlis_ai_p7_red_ledger import build_p7_red_ledger
from emlis_ai_p7_runner_plan import (
    P7_RUNNER_PLAN_SCHEMA_VERSION,
    assert_p7_runner_plan_contract,
    build_p7_runner_command_matrix,
    build_p7_runner_plan,
)

SECRET_INPUT = "P7-3 raw input must never be serialized"
SECRET_COMMENT = "P7-3 comment_text body must never be serialized"
HEAVY_FILES = {
    "tests/test_emlis_ai_complete_product_quality_positive_recovery_e2e.py",
    "tests/test_emlis_ai_complete_product_quality_connection_e2e.py",
}


def _groups_by_id(plan: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(group["group_id"]): group for group in plan["groups"]}  # type: ignore[index]


def test_p7_3_runner_plan_splits_core_existing_reuse_and_heavy_isolated_groups() -> None:
    plan = build_p7_runner_plan()
    assert_p7_runner_plan_contract(plan)

    assert plan["schema_version"] == P7_RUNNER_PLAN_SCHEMA_VERSION
    assert plan["scope"] == "P7_ProductQualityRunner_split_and_isolated_validation"
    assert plan["release_allowed"] is False
    assert plan["full_backend_suite_green_claim_allowed"] is False
    assert plan["combined_timeout_is_green"] is False
    assert all(value is False for value in plan["public_contract"].values())
    assert all(value is False for value in plan["body_free"].values())

    groups = _groups_by_id(plan)
    assert {"p7_core_contract", "existing_p7_reuse_contract"}.issubset(groups)
    assert groups["p7_core_contract"]["group_kind"] == "p7_core"
    assert groups["existing_p7_reuse_contract"]["group_kind"] == "existing_reuse"
    assert groups["p7_core_contract"]["mainline_pass_condition"] is True
    assert groups["existing_p7_reuse_contract"]["mainline_pass_condition"] is True
    assert "tests/test_emlis_ai_p7_module_inventory_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_runner_plan_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_event_bridge_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_evaluation_matrix_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_blind_qa_material_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_long_run_gate_handoff_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_release_handoff_20260612.py" in groups["p7_core_contract"]["test_files"]
    assert "tests/test_emlis_ai_p7_validation_matrix_20260612.py" in groups["p7_core_contract"]["test_files"]


def test_p7_3_runner_plan_excludes_heavy_e2e_from_mainline_and_links_red_ledger() -> None:
    plan = build_p7_runner_plan(module_inventory=build_p7_module_inventory(), red_ledger=build_p7_red_ledger())
    groups = _groups_by_id(plan)

    mainline_files: set[str] = set()
    heavy_files: set[str] = set()
    heavy_red_refs: set[str] = set()
    for group in groups.values():
        files = set(group["test_files"])  # type: ignore[arg-type]
        if group["group_kind"] == "heavy_isolated_red":
            assert group["mainline_pass_condition"] is False
            assert group["green_claim_scope"] == "isolated_red_only"
            assert group["timeout_hang_is_green"] is False
            assert group["timeout_budget_sec"] == 120
            heavy_files.update(files)
            heavy_red_refs.update(group["red_refs"])  # type: ignore[arg-type]
        else:
            assert not (files & HEAVY_FILES)
            if group["mainline_pass_condition"] is True:
                mainline_files.update(files)

    assert heavy_files == HEAVY_FILES
    assert not (mainline_files & HEAVY_FILES)
    assert heavy_red_refs == {"P7-RED-001", "P7-RED-002", "P7-RED-003"}
    assert set(plan["heavy_isolated_red_refs"]) == heavy_red_refs
    assert plan["release_blockers"] == ["P7-RED-001", "P7-RED-002", "P7-RED-003"]


def test_p7_3_timeout_budget_policy_never_treats_timeout_or_hang_as_green() -> None:
    plan = build_p7_runner_plan()
    policy = plan["timeout_budget_policy"]

    assert policy["split_groups_have_explicit_timeout_budget"] is True
    assert policy["heavy_e2e_has_explicit_timeout_budget"] is True
    assert policy["timeout_hang_is_green"] is False
    assert policy["combined_timeout_is_green"] is False
    assert policy["timeout_claim_action"] == "keep_red_or_hang_in_ledger"
    for group in plan["groups"]:
        assert isinstance(group["timeout_budget_sec"], int)
        assert 1 <= group["timeout_budget_sec"] <= 600
        assert group["timeout_hang_is_green"] is False
        assert group["combined_timeout_is_green"] is False
        assert group["full_backend_suite_green_claim_allowed"] is False


def test_p7_3_command_matrix_is_body_free_and_group_scoped_only() -> None:
    plan = build_p7_runner_plan()
    matrix = build_p7_runner_command_matrix(plan)

    assert len(matrix) == len(plan["groups"])
    for row in matrix:
        assert row["body_free"] is True
        assert row["release_allowed"] is False
        assert row["timeout_hang_is_green"] is False
        assert row["green_claim_scope"] in {"group_only", "isolated_red_only"}
        assert row["command"].startswith("PYTHONPATH=services/ai_inference timeout ")
        assert "pytest -q --tb=short" in row["command"]

    dumped = json.dumps({"plan": plan, "matrix": matrix}, ensure_ascii=False, sort_keys=True)
    assert SECRET_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()


def test_p7_3_runner_plan_contract_rejects_release_timeout_green_and_heavy_mainline_mix() -> None:
    plan = build_p7_runner_plan()

    unsafe_release = dict(plan)
    unsafe_release["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_runner_plan_contract(unsafe_release)

    unsafe_timeout = dict(plan)
    unsafe_timeout["combined_timeout_is_green"] = True
    with pytest.raises(ValueError):
        assert_p7_runner_plan_contract(unsafe_timeout)

    unsafe_body = dict(plan)
    unsafe_body["groups"] = list(plan["groups"])
    unsafe_group = dict(unsafe_body["groups"][0])
    unsafe_group["comment_text"] = SECRET_COMMENT
    unsafe_body["groups"][0] = unsafe_group
    with pytest.raises(ValueError):
        assert_p7_runner_plan_contract(unsafe_body)

    unsafe_heavy = dict(plan)
    unsafe_heavy["groups"] = [dict(group) for group in plan["groups"]]
    unsafe_heavy["groups"][0]["test_files"] = list(unsafe_heavy["groups"][0]["test_files"]) + [
        "tests/test_emlis_ai_complete_product_quality_connection_e2e.py"
    ]
    unsafe_heavy["groups"][0]["command"] += " tests/test_emlis_ai_complete_product_quality_connection_e2e.py"
    with pytest.raises(ValueError):
        assert_p7_runner_plan_contract(unsafe_heavy)
