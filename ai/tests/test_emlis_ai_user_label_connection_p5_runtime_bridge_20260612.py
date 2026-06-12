# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Iterable

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
P5_LIMITED_VISIBLE_CONNECTION_PATH = (
    PROJECT_ROOT
    / "services"
    / "ai_inference"
    / "emlis_ai_user_label_connection_p5_limited_visible_connection.py"
)
RED_LEDGER_PATH = PROJECT_ROOT / "docs" / "Cocolon_EmlisAI_P5_P6_RedLedger_RuntimeRepair_R0_20260612.md"

EXPECTED_P5_BUILDER_IMPORTS = {
    "emlis_ai_user_label_connection_p5_readiness": "build_user_label_connection_p5_readiness",
    "emlis_ai_user_label_connection_p5_visibility_boundary": "build_user_label_connection_p5_visibility_boundary",
    "emlis_ai_user_label_connection_p5_eligibility_matrix": "build_user_label_connection_p5_eligibility_matrix",
    "emlis_ai_user_label_connection_p5_surface_role_plan": "build_user_label_connection_p5_surface_role_plan",
    "emlis_ai_user_label_connection_p5_safety_guard": "build_user_label_connection_p5_safety_guard",
    "emlis_ai_user_label_connection_p5_product_quality_review": "build_user_label_connection_p5_product_quality_review",
    "emlis_ai_user_label_connection_p5_limited_visible_connection": "build_user_label_connection_p5_limited_visible_connection",
    "emlis_ai_user_label_connection_p5_regression_handoff": "build_user_label_connection_p5_regression_handoff",
}

EXPECTED_RUNTIME_SUMMARY_TOKENS = {
    "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1",
    "p5_runtime_evaluated",
    "p5_visible_applied",
    "p5_product_quality_confirmed",
    "p5_1_visibility_boundary",
    "p5_2_eligibility_matrix",
    "p5_3_surface_role_plan",
    "p5_4_safety_guard",
    "p5_5_product_quality_review",
    "p5_6_limited_visible_connection",
    "p5_7_regression_handoff",
    "p5_product_quality_review_missing",
    "release_allowed",
    "comment_text_body_included",
    "candidate_body_included",
    "surface_body_included",
    "visible_connection_route",
    "p5_6_boundary_internal_phase8_connector",
    "phase8_connector_scope",
    "p5_6_internal_boundary_only",
    "legacy_phase8_direct_call_used",
    "p5_visible_connection_r3_old_phase8_direct_call_used",
    "p5_visible_connection_r3_phase8_internal_only",
}

R0_LEDGER_REQUIRED_TOKENS = {
    "schema_version: cocolon.emlis.p5_p6.red_ledger.r0_20260612.v1",
    "scope: P5_P6_runtime_repair_only",
    "p7_out_of_scope: true",
    "runtime_complete_claim_allowed: false",
    "product_quality_complete_claim_allowed: false",
    "release_allowed: false",
    "public_response_key_added: false",
    "rn_visible_contract_changed: false",
    "db_schema_changed: false",
    "gate_threshold_relaxed: false",
    "fixed_comment_text_added: false",
    "case_specific_route_added: false",
    "full_backend_suite_green_claim_allowed: false",
    "P5-RED-001",
    "P5-RED-002",
    "P5-RED-003",
    "P5-RED-004",
    "P5-RED-005",
    "P5-RED-006",
    "P6-RED-001",
    "P6-RED-002",
    "P6-RED-003",
    "P6-RED-004",
    "P6-RED-005",
    "P6-RED-006",
    "P7-OUT-001",
    "P7-OUT-002",
    "P7-OUT-003",
}


def _source() -> str:
    return REPLY_SERVICE_PATH.read_text(encoding="utf-8")


def _module() -> ast.Module:
    return ast.parse(_source(), filename=str(REPLY_SERVICE_PATH))


def _imported_names_for(module_name: str) -> set[str]:
    names: set[str] = set()
    for node in _module().body:
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            names.update(alias.name for alias in node.names)
    return names


def _called_function_names() -> list[str]:
    calls: list[str] = []
    for node in ast.walk(_module()):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)
    return calls


def _missing_tokens(text: str, tokens: Iterable[str]) -> list[str]:
    return sorted(token for token in tokens if token not in text)



async def _p5_runtime_empty_dict(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {}


async def _p5_runtime_empty_list(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    return []


async def _p5_runtime_none(*args: Any, **kwargs: Any) -> None:
    return None


def _install_p5_runtime_history_context(monkeypatch: pytest.MonkeyPatch) -> None:
    import emlis_ai_context_service as context_service

    async def _last_input(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "id": "p5-runtime-history-001",
            "created_at": "2026-06-11T00:00:00Z",
            "memo": "同じ仕事の不安があった。",
            "memo_action": "考え続けた。",
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "emotions": ["不安"],
            "category": ["仕事"],
        }

    async def _same_day_inputs(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [await _last_input()]

    async def _similar_inputs(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
        return [
            await _last_input(),
            {
                "id": "p5-runtime-history-002",
                "created_at": "2026-06-10T00:00:00Z",
                "memo": "判断が重くて言い切れない。",
                "memo_action": "立ち止まった。",
                "emotion_details": [{"type": "不安", "strength": "medium"}],
                "emotions": ["不安"],
                "category": ["仕事"],
            },
        ]

    monkeypatch.setattr(context_service, "_get_input_summary_for_user", _p5_runtime_empty_dict)
    monkeypatch.setattr(context_service, "_get_myweb_home_summary_for_user", _p5_runtime_empty_dict)
    monkeypatch.setattr(context_service, "_get_latest_today_question_answer_for_user", _p5_runtime_empty_dict)
    monkeypatch.setattr(context_service, "_list_recent_today_question_answers_for_user", _p5_runtime_empty_list)
    monkeypatch.setattr(context_service, "get_last_input_for_user", _last_input)
    monkeypatch.setattr(context_service, "list_same_day_recent_inputs", _same_day_inputs)
    monkeypatch.setattr(context_service, "search_similar_inputs", _similar_inputs)
    monkeypatch.setattr(context_service, "load_emlis_ai_user_model_for_user", _p5_runtime_none)


def test_r0_red_ledger_is_fixed_and_completion_labels_are_removed() -> None:
    assert RED_LEDGER_PATH.exists(), "R0 red ledger document must be committed before runtime repair."
    ledger = RED_LEDGER_PATH.read_text(encoding="utf-8")

    missing = _missing_tokens(ledger, R0_LEDGER_REQUIRED_TOKENS)
    assert missing == [], f"R0 red ledger is missing required blocker/out-of-scope markers: {missing}"
    assert "P5 test green = P5 runtime complete" in ledger
    assert "P6 test green = Structure Insight visible in actual comment_text" in ledger
    assert "P5/P6 repair complete = release_allowed" in ledger


def test_p5_runtime_bridge_reply_service_imports_p5_chain_builders() -> None:
    missing: dict[str, str] = {}
    for module_name, builder_name in EXPECTED_P5_BUILDER_IMPORTS.items():
        imported_names = _imported_names_for(module_name)
        if builder_name not in imported_names:
            missing[module_name] = builder_name

    assert missing == {}, (
        "P5 runtime bridge is not wired into emlis_ai_reply_service.py. "
        f"Missing P5 builder imports: {missing}"
    )


def test_p5_runtime_bridge_reply_service_has_body_free_step_summary_contract() -> None:
    source = _source()
    missing = _missing_tokens(source, EXPECTED_RUNTIME_SUMMARY_TOKENS)
    assert missing == [], (
        "P5 runtime bridge must expose a body-free internal summary that separates "
        "runtime_evaluated / visible_applied / product_quality_confirmed before P5 can be called complete. "
        f"Missing tokens: {missing}"
    )


def test_p5_runtime_bridge_blocks_old_phase8_direct_visible_connection_from_reply_service() -> None:
    direct_calls = [
        name
        for name in _called_function_names()
        if name == "build_user_label_connection_limited_visible_surface_connection"
    ]
    assert direct_calls == [], (
        "reply_service must not call the old Phase8 visible connector directly after R1/R2. "
        "It must go through build_user_label_connection_p5_limited_visible_connection so P5-1 through P5-6 boundaries are enforced."
    )


def test_p5_visible_connection_r3_keeps_phase8_connector_inside_p5_6_boundary_only() -> None:
    reply_calls = _called_function_names()
    assert "build_user_label_connection_p5_limited_visible_connection" in reply_calls
    assert "build_user_label_connection_limited_visible_surface_connection" not in reply_calls

    p5_module_source = P5_LIMITED_VISIBLE_CONNECTION_PATH.read_text(encoding="utf-8")
    p5_module_ast = ast.parse(p5_module_source, filename=str(P5_LIMITED_VISIBLE_CONNECTION_PATH))
    p5_imported_old_connector = False
    p5_calls_old_connector = False
    for node in ast.walk(p5_module_ast):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "emlis_ai_user_label_connection_surface"
            and any(alias.name == "build_user_label_connection_limited_visible_surface_connection" for alias in node.names)
        ):
            p5_imported_old_connector = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "build_user_label_connection_limited_visible_surface_connection":
                p5_calls_old_connector = True

    assert p5_imported_old_connector is True
    assert p5_calls_old_connector is True
    for token in (
        "p5_6_boundary_internal_phase8_connector",
        "p5_6_internal_boundary_only",
        "legacy_phase8_direct_call_used",
        "post_connection_regate_required",
        "p5_6_boundary_enforced",
        "phase8_direct_visible_connection_from_reply_service",
    ):
        assert token in p5_module_source


def test_p5_runtime_bridge_keeps_public_contract_static_before_visible_connection_repair() -> None:
    ledger = RED_LEDGER_PATH.read_text(encoding="utf-8")
    assert "public_response_key_added: false" in ledger
    assert "rn_visible_contract_changed: false" in ledger
    assert "db_schema_changed: false" in ledger
    assert "raw_input_in_public_meta_allowed: false" in ledger
    assert "comment_text_body_in_public_meta_allowed: false" in ledger
    assert "candidate_body_in_public_meta_allowed: false" in ledger
    assert "surface_body_in_public_meta_allowed: false" in ledger


@pytest.mark.asyncio
async def test_p5_runtime_bridge_actual_reply_exposes_body_free_runtime_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    """R1 red test against the actual reply runtime path.

    The current baseline may still expose Phase8 user-label metadata. That is not enough.
    P5 is not runtime-complete until reply_service leaves a P5-specific, body-free
    runtime bridge summary that separates runtime_evaluated, visible_applied, and
    product_quality_confirmed.
    """

    _install_p5_runtime_history_context(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="p5-runtime-bridge-red-user",
        subscription_tier="plus",
        current_input={
            "id": "p5-runtime-current-001",
            "created_at": "2026-06-12T00:00:00Z",
            "memo": "また仕事の判断で言い切れなくなっている。前も同じところで詰まった気がする。",
            "memo_action": "考え込んでいる。",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "emotions": ["不安"],
            "category": ["仕事"],
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

    assert isinstance(p5_runtime_bridge, dict), (
        "P5 runtime bridge summary is missing from the actual reply meta. "
        "Phase8 user_label_connection_meta_only / visible_surface metadata is not P5 runtime completion evidence."
    )
    assert p5_runtime_bridge.get("schema_version") == "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1"
    assert p5_runtime_bridge.get("runtime_evaluated") is True
    assert "p5_1_visibility_boundary" in (p5_runtime_bridge.get("p5_step_summary") or {})
    assert "p5_6_limited_visible_connection" in (p5_runtime_bridge.get("p5_step_summary") or {})
    assert p5_runtime_bridge.get("public_contract", {}).get("public_response_key_added") is False
    assert p5_runtime_bridge.get("body_free", {}).get("comment_text_body_included") is False
    assert p5_runtime_bridge.get("release_allowed") is False
    assert p5_runtime_bridge.get("visible_connection_route") == "p5_6_boundary_internal_phase8_connector"
    assert p5_runtime_bridge.get("phase8_connector_scope") == "p5_6_internal_boundary_only"
    assert p5_runtime_bridge.get("legacy_phase8_direct_call_used") is False
    assert p5_runtime_bridge.get("post_connection_regate_required") is True
    assert p5_runtime_bridge.get("reply_service_direct_phase8_call_allowed") is False
