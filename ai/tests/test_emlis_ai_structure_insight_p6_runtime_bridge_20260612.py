# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Iterable

import pytest

from test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612 import (
    _install_p5_runtime_history_context,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
PUBLIC_META_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_public_feedback_meta.py"
RED_LEDGER_PATH = PROJECT_ROOT / "docs" / "Cocolon_EmlisAI_P5_P6_RedLedger_RuntimeRepair_R0_20260612.md"

EXPECTED_P6_BUILDER_IMPORTS = {
    "emlis_ai_structure_insight_p6_entry_freeze": "build_structure_insight_p6_entry_freeze",
    "emlis_ai_structure_insight_p6_inventory": "build_structure_insight_p6_inventory",
    "emlis_ai_structure_insight_p6_family_boundary": "build_structure_insight_p6_family_boundary",
    "emlis_ai_structure_insight_p6_relation_policy": "build_structure_insight_p6_relation_policy",
    "emlis_ai_structure_insight_p6_quality_rubric": "build_structure_insight_p6_quality_rubric",
    "emlis_ai_structure_insight_p6_gate_hardening": "build_structure_insight_p6_gate_hardening",
    "emlis_ai_structure_insight_p6_surface_role_plan": "build_structure_insight_p6_surface_role_plan",
    "emlis_ai_structure_insight_p6_family_review": "build_structure_insight_p6_family_review",
    "emlis_ai_structure_insight_p6_product_quality_review": "build_structure_insight_p6_product_quality_review",
    "emlis_ai_structure_insight_p6_regression_handoff": "build_structure_insight_p6_regression_handoff",
}

OPTIONAL_FOUNDATION_IMPORTS = {
    "emlis_ai_structure_insight_candidate": "build_structure_insight_candidate_meta",
    "emlis_ai_structure_insight_gate": "build_structure_insight_gate_report",
    "emlis_ai_structure_insight_surface": "build_structure_insight_surface_for_line",
}

EXPECTED_P6_RUNTIME_SUMMARY_TOKENS = {
    "cocolon.emlis.structure_insight.p6_runtime_bridge.v1",
    "P6_RuntimeBridge_Repair_20260612",
    "p6_runtime_bridge",
    "structure_insight_p6_runtime_bridge",
    "p6_runtime_evaluated",
    "p6_visible_applied",
    "visible_family",
    "p5_dependency_status",
    "p6_step_summary",
    "p6_0_entry_freeze",
    "p6_1_inventory",
    "p6_2_family_boundary",
    "p6_3_relation_policy",
    "p6_4_quality_rubric",
    "p6_5_gate_hardening",
    "p6_6_surface_role_plan",
    "p6_7_family_review",
    "p6_8_product_quality_review",
    "p6_9_regression_handoff",
    "no_connect_family_preserved",
    "p6_visible_not_applied_reason_codes",
    "comment_text_owner",
    "input_feedback.comment_text",
    "public_response_key_added",
    "rn_visible_contract_changed",
    "api_route_changed",
    "db_schema_changed",
    "release_allowed",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
    "raw_input_included",
    "reviewer_free_text_included",
}

EXPECTED_P6_RUNTIME_BOUNDARY_TOKENS = {
    "p5_dependency_status",
    "p5_ready",
    "p5_hold",
    "p5_return_required",
    "p4_return_required",
    "structure_question",
    "visible_family",
    "daily_unpleasant",
    "daily_positive",
    "positive_only",
    "low_information",
    "safety_triage_required",
    "no_connect_family_preserved",
    "diagnosis_blocked",
    "personality_classification_blocked",
    "cause_assertion_blocked",
    "future_prediction_blocked",
    "action_instruction_blocked",
    "target_judgement_blocked",
    "insight_seed_count",
    "p6_post_connection_gate_blocked",
    "gate_threshold_relaxed",
}

EXPECTED_PUBLIC_META_TOKENS = {
    "_build_p6_runtime_bridge_public_summary",
    "_pick_p6_runtime_bridge_source",
    "structure_insight_p6_runtime_bridge",
    "p6_runtime_bridge",
    "p6_runtime_evaluated",
    "p6_visible_applied",
    "visible_family",
    "p5_dependency_status",
    "no_connect_family_preserved",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
    "release_allowed",
}

P6_MODULE_PATHS = [
    PROJECT_ROOT / "services" / "ai_inference" / f"{module_name}.py"
    for module_name in EXPECTED_P6_BUILDER_IMPORTS
]


def _source(path: Path = REPLY_SERVICE_PATH) -> str:
    return path.read_text(encoding="utf-8")


def _module(path: Path = REPLY_SERVICE_PATH) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _imported_names_for(module_name: str) -> set[str]:
    names: set[str] = set()
    for node in _module().body:
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            names.update(alias.name for alias in node.names)
    return names


def _called_function_names(path: Path = REPLY_SERVICE_PATH) -> list[str]:
    calls: list[str] = []
    for node in ast.walk(_module(path)):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)
    return calls


def _missing_tokens(text: str, tokens: Iterable[str]) -> list[str]:
    return sorted(token for token in tokens if token not in text)


def test_r5_baseline_confirms_p6_modules_exist_but_r0_keeps_runtime_unconnected_red() -> None:
    missing_paths = [str(path.relative_to(PROJECT_ROOT)) for path in P6_MODULE_PATHS if not path.exists()]
    assert missing_paths == [], f"P6 focused modules are missing before runtime bridge repair: {missing_paths}"

    assert RED_LEDGER_PATH.exists(), "R0 red ledger must remain present before P6 runtime repair."
    ledger = RED_LEDGER_PATH.read_text(encoding="utf-8")
    for token in (
        "P6-RED-001",
        "P6-RED-002",
        "P6-RED-003",
        "P6-RED-004",
        "P6-RED-005",
        "P6-RED-006",
        "P6 test green = Structure Insight visible in actual comment_text",
        "release_allowed: false",
        "public_response_key_added: false",
        "comment_text_body_in_public_meta_allowed: false",
    ):
        assert token in ledger


def test_p6_runtime_bridge_reply_service_imports_p6_chain_builders() -> None:
    missing: dict[str, str] = {}
    for module_name, builder_name in EXPECTED_P6_BUILDER_IMPORTS.items():
        if builder_name not in _imported_names_for(module_name):
            missing[module_name] = builder_name

    foundation_missing: dict[str, str] = {}
    for module_name, builder_name in OPTIONAL_FOUNDATION_IMPORTS.items():
        if builder_name not in _imported_names_for(module_name):
            foundation_missing[module_name] = builder_name

    assert missing == {}, (
        "P6 runtime bridge is not wired into emlis_ai_reply_service.py. "
        f"Missing P6-0..P6-9 builder imports: {missing}. "
        f"Optional foundation imports still absent: {foundation_missing}"
    )


def test_p6_runtime_bridge_reply_service_has_body_free_runtime_summary_contract() -> None:
    source = _source()
    missing = _missing_tokens(source, EXPECTED_P6_RUNTIME_SUMMARY_TOKENS)
    assert missing == [], (
        "P6 runtime bridge must expose a body-free internal summary that separates "
        "runtime_evaluated / visible_applied / p5_dependency_status / visible_family before P6 can be called connected. "
        f"Missing tokens: {missing}"
    )


def test_p6_runtime_bridge_enforces_p5_handoff_no_connect_family_and_single_seed_boundaries() -> None:
    source = _source()
    calls = set(_called_function_names())

    assert "build_structure_insight_p6_entry_freeze" in calls, (
        "P6 must enter through P6-0 entry freeze so P5 handoff status can hold, p5_return, or p4_return before runtime evaluation."
    )
    assert "build_structure_insight_p6_family_boundary" in calls, (
        "P6 must run the family boundary in reply_service so non-structure_question families are not deep-insight visible by accident."
    )
    assert "build_structure_insight_p6_gate_hardening" in calls, (
        "P6 must run gate hardening before any visible seed reaches comment_text."
    )
    assert "build_structure_insight_p6_surface_role_plan" in calls, (
        "P6 limited surface must be role-planned before any one-seed structure insight can be applied."
    )
    assert _missing_tokens(source, EXPECTED_P6_RUNTIME_BOUNDARY_TOKENS) == []


def test_p6_runtime_bridge_public_meta_summary_is_body_free_and_not_a_top_level_response_contract() -> None:
    public_meta_source = _source(PUBLIC_META_PATH)
    missing = _missing_tokens(public_meta_source, EXPECTED_PUBLIC_META_TOKENS)
    assert missing == [], (
        "P6 runtime bridge public meta must be sanitized into the existing input_feedback/emlis_ai diagnostic path "
        "using safe identifiers/booleans only. "
        f"Missing tokens: {missing}"
    )

    reply_source = _source()
    assert "public_response_key_added\": True" not in reply_source
    assert "rn_visible_contract_changed\": True" not in reply_source
    assert "db_schema_changed\": True" not in reply_source


@pytest.mark.asyncio
async def test_p6_runtime_bridge_actual_reply_exposes_body_free_runtime_summary_after_p5_handoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R5 red test against the actual reply runtime path.

    P6 modules and focused tests existing is not enough. P6 is not runtime-connected
    until render_emlis_ai_reply leaves a P6-specific body-free summary that proves
    P5 handoff dependency, family/no-connect boundaries, and release_allowed=false.
    """

    _install_p5_runtime_history_context(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="p6-runtime-bridge-red-user",
        subscription_tier="plus",
        current_input={
            "id": "p6-runtime-current-001",
            "created_at": "2026-06-12T00:00:00Z",
            "memo": "やりたい気持ちはあるのに、動こうとすると怖さも同時に出てきて、何が引っかかっているのかを見失う。",
            "memo_action": "考えを整理しようとしている。",
            "emotion_details": [
                {"type": "迷い", "strength": "strong"},
                {"type": "怖さ", "strength": "medium"},
            ],
            "emotions": ["迷い", "怖さ"],
            "category": ["自己理解"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta.get("diagnostic_summary") if isinstance(reply.meta.get("diagnostic_summary"), dict) else {}
    p5_runtime_bridge = (
        reply.meta.get("user_label_connection_p5_runtime_bridge")
        or diagnostic.get("user_label_connection_p5_runtime_bridge")
        or reply.meta.get("p5_runtime_bridge")
    )
    p6_runtime_bridge = (
        reply.meta.get("structure_insight_p6_runtime_bridge")
        or diagnostic.get("structure_insight_p6_runtime_bridge")
        or reply.meta.get("p6_runtime_bridge")
    )

    assert isinstance(p5_runtime_bridge, dict), "R5 depends on the already-repaired P5 runtime bridge being present."
    assert p5_runtime_bridge.get("schema_version") == "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1"
    assert p5_runtime_bridge.get("runtime_evaluated") is True

    assert isinstance(p6_runtime_bridge, dict), (
        "P6 runtime bridge summary is missing from the actual reply meta. "
        "P6 focused module/test green is not runtime connection evidence."
    )
    assert p6_runtime_bridge.get("schema_version") == "cocolon.emlis.structure_insight.p6_runtime_bridge.v1"
    assert p6_runtime_bridge.get("runtime_evaluated") is True
    assert p6_runtime_bridge.get("visible_applied") in {True, False}
    assert p6_runtime_bridge.get("visible_family") in {"structure_question", "none"}
    assert p6_runtime_bridge.get("p5_dependency_status") in {
        "p5_ready",
        "p5_hold",
        "p5_return_required",
        "p4_return_required",
    }
    step_summary = p6_runtime_bridge.get("p6_step_summary") or {}
    for key in (
        "p6_0_entry_freeze",
        "p6_1_inventory",
        "p6_2_family_boundary",
        "p6_3_relation_policy",
        "p6_4_quality_rubric",
        "p6_5_gate_hardening",
        "p6_6_surface_role_plan",
        "p6_7_family_review",
        "p6_8_product_quality_review",
        "p6_9_regression_handoff",
    ):
        assert key in step_summary
    assert p6_runtime_bridge.get("comment_text_owner") == "input_feedback.comment_text"
    assert p6_runtime_bridge.get("public_contract", {}).get("public_response_key_added") is False
    assert p6_runtime_bridge.get("public_contract", {}).get("release_allowed") is False
    assert p6_runtime_bridge.get("body_free", {}).get("raw_input_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("comment_text_body_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("candidate_body_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("surface_body_included") is False
    assert p6_runtime_bridge.get("release_allowed") is False
