# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from emlis_ai_user_label_connection_p5_limited_visible_connection import (
    USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE,
    assert_user_label_connection_p5_limited_visible_connection_contract,
    build_user_label_connection_p5_limited_visible_connection,
    user_label_connection_p5_limited_visible_connection_public_summary,
)
from test_emlis_ai_user_label_connection_p5_visibility_boundary_20260611 import _visibility_boundary
from test_emlis_ai_user_label_connection_p5_eligibility_matrix_20260611 import _matrix
from test_emlis_ai_user_label_connection_p5_surface_role_plan_20260611 import _plan
from test_emlis_ai_user_label_connection_p5_safety_guard_20260611 import _guard
from test_emlis_ai_user_label_connection_p5_product_quality_review_20260611 import _review

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
P5_6_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_user_label_connection_p5_limited_visible_connection.py"
OLD_PHASE8_BUILDER = "build_user_label_connection_limited_visible_surface_connection"
P5_6_BUILDER = "build_user_label_connection_p5_limited_visible_connection"


def _called_function_names(path: Path) -> list[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[str] = []
    for node in ast.walk(module):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
    return calls


def _existing_gate_reports(**overrides: Any) -> dict[str, Any]:
    reports = {
        "display_gate": {"passed": True},
        "grounding": {"passed": True},
        "template_echo": {"passed": True},
        "safety": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
    }
    reports.update(overrides)
    return reports


def _p5_chain() -> dict[str, Mapping[str, Any]]:
    visibility = _visibility_boundary(run_id="p5_r3_visibility_source")
    matrix = _matrix(p5_visibility_boundary=visibility, run_id="p5_r3_matrix_source")
    plan = _plan(p5_eligibility_matrix=matrix, run_id="p5_r3_plan_source")
    guard = _guard(p5_surface_role_plan=plan, run_id="p5_r3_guard_source")
    review = _review(p5_safety_guard=guard, run_id="p5_r3_review_source")
    return {
        "p5_visibility_boundary": visibility,
        "p5_eligibility_matrix": matrix,
        "p5_surface_role_plan": plan,
        "p5_safety_guard": guard,
        "p5_product_quality_review": review,
    }


def test_r3_reply_service_calls_p5_6_boundary_not_old_phase8_visible_connector_directly() -> None:
    reply_calls = _called_function_names(REPLY_SERVICE_PATH)
    p5_6_calls = _called_function_names(P5_6_PATH)

    assert P5_6_BUILDER in reply_calls
    assert OLD_PHASE8_BUILDER not in reply_calls
    assert OLD_PHASE8_BUILDER in p5_6_calls

    reply_source = REPLY_SERVICE_PATH.read_text(encoding="utf-8")
    for token in (
        "P5_RuntimeBridge_Repair_R3_20260612",
        "p5_visible_connection_r3_route",
        "p5_visible_connection_r3_old_phase8_direct_call_used",
        "p5_visible_connection_r3_phase8_internal_only",
        "p5_post_connection_gate_blocked",
    ):
        assert token in reply_source


def test_r3_p5_6_meta_proves_phase8_connector_is_internal_and_body_free() -> None:
    chain = _p5_chain()
    result = build_user_label_connection_p5_limited_visible_connection(
        "今回の入力は、まず今の状態として受け取ります。",
        observation_status="passed",
        **chain,
        existing_gate_reports=_existing_gate_reports(),
        run_id="p5_r3_visible_connection_boundary",
    )
    meta = result.as_meta()
    summary = user_label_connection_p5_limited_visible_connection_public_summary(meta)

    assert result.applied is True
    assert meta["visible_connection_route"] == "p5_6_boundary_internal_phase8_connector"
    assert meta["p5_6_boundary_enforced"] is True
    assert meta["phase8_connector_scope"] == USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE
    assert meta["legacy_phase8_direct_call_used"] is False
    assert meta["phase8_connector_called_inside_p5_6_boundary"] is True
    assert meta["phase8_direct_reply_service_call_allowed"] is False
    assert meta["phase8_direct_visible_connection_from_reply_service"] is False
    assert meta["post_connection_regate_required"] is True
    assert meta["post_connection_gate_passed"] is True
    assert meta["public_contract"]["public_response_key_added"] is False
    assert meta["body_free"]["comment_text_body_included"] is False
    assert meta["body_free"]["history_raw_text_included"] is False
    assert summary["visible_connection_route"] == "p5_6_boundary_internal_phase8_connector"
    assert summary["phase8_connector_scope"] == USER_LABEL_CONNECTION_P5_6_PHASE8_CONNECTOR_SCOPE
    assert summary["legacy_phase8_direct_call_used"] is False
    assert summary["comment_text_body_included"] is False
    assert_user_label_connection_p5_limited_visible_connection_contract(meta)
