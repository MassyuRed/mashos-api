# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from test_emlis_ai_user_label_connection_p5_runtime_bridge_20260612 import (
    _install_p5_runtime_history_context,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
PUBLIC_META_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_public_feedback_meta.py"
R7_MODULE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_structure_insight_p6_limited_surface_connection.py"


def _source(path: Path = REPLY_SERVICE_PATH) -> str:
    return path.read_text(encoding="utf-8")


def _module(path: Path = REPLY_SERVICE_PATH) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _called_function_names(path: Path = REPLY_SERVICE_PATH) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(_module(path)):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)
    return calls


def _imported_names_for(module_name: str) -> set[str]:
    names: set[str] = set()
    for node in _module().body:
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            names.update(alias.name for alias in node.names)
    return names


def _gate_reports() -> dict[str, dict[str, bool]]:
    return {
        "display_gate": {"passed": True},
        "grounding": {"passed": True},
        "template_echo": {"passed": True},
        "safety": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
    }


def _ready_structure_question_chain() -> dict[str, Any]:
    from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
    from emlis_ai_structure_insight_p6_gate_hardening import build_structure_insight_p6_gate_hardening
    from emlis_ai_structure_insight_p6_quality_rubric import (
        P6_QUALITY_RUBRIC_DIMENSION_TARGETS,
        build_structure_insight_p6_quality_rubric,
    )
    from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy
    from emlis_ai_structure_insight_p6_surface_role_plan import build_structure_insight_p6_surface_role_plan
    from emlis_ai_structure_insight_p6_limited_surface_connection import (
        build_structure_insight_p6_limited_surface_candidate_probe,
    )

    family_boundary = build_structure_insight_p6_family_boundary(
        family="structure_question",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        observation_status_connectable=True,
        pre_gate_body_generated=False,
        user_dictionary_fact_assertion_required=False,
        target_judgement_required=False,
        safety_adjacent=False,
        emergency_safety=False,
        source_unavailable=False,
    )
    relation_policy = build_structure_insight_p6_relation_policy(
        relation_family="desire_blockage_conflict",
        p6_family_boundary=family_boundary,
        low_information_overread_risk=False,
        target_judgement_required=False,
        self_denial_identity_fact_required=False,
        period_tendency_required=False,
        user_dictionary_fact_claim_required=False,
        gate_required_bypassed=False,
        pre_gate_body_generated=False,
    )
    row = {
        "row_id": "p6-r7-structure-question-ready",
        "case_id": "p6-r7-structure-question-ready",
        "family": "structure_question",
        "relation_family": "desire_blockage_conflict",
        "ratings": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
        "red_flags": [],
        "repair_flags": [],
        "ratings_only": True,
        "body_free_row_only": True,
        "release_allowed": False,
        "public_response_key_added": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
    }
    quality_rubric = build_structure_insight_p6_quality_rubric(
        review_rows=[row],
        p6_relation_policy=relation_policy,
        p6_family_boundary=family_boundary,
    )
    probe_text, probe_meta = build_structure_insight_p6_limited_surface_candidate_probe(
        family="structure_question",
        relation_family="desire_blockage_conflict",
    )
    gate_hardening = build_structure_insight_p6_gate_hardening(
        proposed_surface=probe_text,
        relation_family="desire_blockage_conflict",
        p6_relation_policy=relation_policy,
        p6_quality_rubric=quality_rubric,
        gate_meta={
            "gate_threshold_relaxed": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
        },
        user_dictionary_meta={"user_dictionary_fact_claim_required": False},
    )
    surface_role_plan = build_structure_insight_p6_surface_role_plan(
        family="structure_question",
        relation_family="desire_blockage_conflict",
        p6_family_boundary=family_boundary,
        p6_relation_policy=relation_policy,
        p6_quality_rubric=quality_rubric,
        p6_gate_hardening=gate_hardening,
        requested_insight_seed_count=1,
        target_judgement_risk=False,
        surface_plan_meta={
            "fixed_sentence_template_added": False,
            "input_specific_template_added": False,
            "public_response_key_added": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "release_allowed": False,
        },
    )
    return {
        "family_boundary": family_boundary,
        "relation_policy": relation_policy,
        "quality_rubric": quality_rubric,
        "probe_text": probe_text,
        "probe_meta": probe_meta,
        "gate_hardening": gate_hardening,
        "surface_role_plan": surface_role_plan,
    }


def test_r7_reply_service_imports_and_calls_limited_surface_boundary() -> None:
    assert R7_MODULE_PATH.exists(), "R7 limited surface boundary module must exist."
    source = _source()
    assert "from emlis_ai_structure_insight_p6_limited_surface_connection import" in source
    assert "build_structure_insight_p6_limited_surface_candidate_probe" in source
    assert "build_structure_insight_p6_limited_surface_connection" in source
    assert "REASON_P6_POST_CONNECTION_GATE_BLOCKED" in source

    for token in (
        "r7_limited_surface_connection",
        "r7_structure_question_only",
        "limited_surface_allowed_family_only",
        "structure_question",
        "max_insight_seed_count",
        "input_feedback.comment_text",
        "p6_post_connection_gate_blocked",
        "gate_threshold_relaxed",
    ):
        assert token in source
    assert "public_response_key_added\": True" not in source
    assert "rn_visible_contract_changed\": True" not in source
    assert "db_schema_changed\": True" not in source


def test_r7_direct_connection_applies_only_one_seed_for_structure_question() -> None:
    from emlis_ai_structure_insight_p6_limited_surface_connection import (
        assert_structure_insight_p6_limited_surface_connection_contract,
        build_structure_insight_p6_limited_surface_connection,
        structure_insight_p6_limited_surface_connection_public_summary,
    )

    chain = _ready_structure_question_chain()
    result = build_structure_insight_p6_limited_surface_connection(
        "見えたこと:\nいま見えています。\n\nEmlisから:\nここは受け取れます。",
        observation_status="passed",
        p6_family_boundary=chain["family_boundary"],
        p6_relation_policy=chain["relation_policy"],
        p6_quality_rubric=chain["quality_rubric"],
        p6_gate_hardening=chain["gate_hardening"],
        p6_surface_role_plan=chain["surface_role_plan"],
        existing_gate_reports=_gate_reports(),
        proposed_surface=chain["probe_text"],
        structure_insight_surface_meta=chain["probe_meta"],
        run_id="p6-r7-direct-structure-question",
    )

    assert result.applied is True
    assert result.comment_text.count("Emlisから:") == 1
    assert result.comment_text.count(chain["probe_text"]) == 1
    assert result.comment_text.count("見えたこと:") == 1

    meta = result.as_meta()
    assert_structure_insight_p6_limited_surface_connection_contract(meta)
    assert meta["schema_version"] == "cocolon.emlis.structure_insight.p6_limited_surface_connection.r7.v1"
    assert meta["visible_family"] == "structure_question"
    assert meta["insight_seed_count"] == 1
    assert meta["max_insight_seed_count"] == 1
    assert meta["comment_text_owner"] == "input_feedback.comment_text"
    assert meta["public_contract"]["public_response_key_added"] is False
    assert meta["public_contract"]["rn_visible_contract_changed"] is False
    assert meta["body_free"]["comment_text_body_included"] is False
    assert meta["body_free"]["candidate_body_included"] is False
    assert meta["body_free"]["surface_body_included"] is False
    assert meta["release_allowed"] is False

    summary = structure_insight_p6_limited_surface_connection_public_summary(meta)
    assert summary["visible_applied"] is True
    assert summary["visible_family"] == "structure_question"
    assert summary["insight_seed_count"] == 1
    serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert chain["probe_text"] not in serialized
    for forbidden in ("raw_input", "comment_text_body", "candidate_body", "surface_body"):
        assert f'"{forbidden}": true' not in serialized.lower()


def test_r7_direct_connection_blocks_non_structure_question_family() -> None:
    from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
    from emlis_ai_structure_insight_p6_limited_surface_connection import build_structure_insight_p6_limited_surface_connection
    from emlis_ai_structure_insight_p6_quality_rubric import build_structure_insight_p6_quality_rubric
    from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy
    from emlis_ai_structure_insight_p6_gate_hardening import build_structure_insight_p6_gate_hardening
    from emlis_ai_structure_insight_p6_surface_role_plan import build_structure_insight_p6_surface_role_plan

    family_boundary = build_structure_insight_p6_family_boundary(
        family="daily_positive",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        observation_status_connectable=True,
        pre_gate_body_generated=False,
        user_dictionary_fact_assertion_required=False,
        target_judgement_required=False,
        safety_adjacent=False,
        emergency_safety=False,
        source_unavailable=False,
    )
    relation_policy = build_structure_insight_p6_relation_policy(
        relation_family="positive_change_recovery",
        p6_family_boundary=family_boundary,
    )
    quality_rubric = build_structure_insight_p6_quality_rubric(
        review_rows=[],
        p6_relation_policy=relation_policy,
        p6_family_boundary=family_boundary,
    )
    gate_hardening = build_structure_insight_p6_gate_hardening(
        proposed_surface=None,
        relation_family="positive_change_recovery",
        p6_relation_policy=relation_policy,
        p6_quality_rubric=quality_rubric,
    )
    surface_role_plan = build_structure_insight_p6_surface_role_plan(
        family="daily_positive",
        relation_family="positive_change_recovery",
        p6_family_boundary=family_boundary,
        p6_relation_policy=relation_policy,
        p6_quality_rubric=quality_rubric,
        p6_gate_hardening=gate_hardening,
        requested_insight_seed_count=0,
        surface_plan_meta={"fixed_sentence_template_added": False},
    )

    result = build_structure_insight_p6_limited_surface_connection(
        "見えたこと:\n今日の変化が見えています。\n\nEmlisから:\nその明るさはそのまま受け取れます。",
        observation_status="passed",
        p6_family_boundary=family_boundary,
        p6_relation_policy=relation_policy,
        p6_quality_rubric=quality_rubric,
        p6_gate_hardening=gate_hardening,
        p6_surface_role_plan=surface_role_plan,
        existing_gate_reports=_gate_reports(),
    )
    meta = result.as_meta()
    assert result.applied is False
    assert meta["visible_family"] == "none"
    assert meta["insight_seed_count"] == 0
    assert any(str(reason).startswith("p6_limited_surface_family_not_structure_question") for reason in meta["blocked_reason_codes"])
    assert meta["no_connect_family_visible_applied"] is False
    assert meta["public_contract"]["public_response_key_added"] is False
    assert meta["body_free"]["surface_body_included"] is False


def test_r7_public_meta_summary_is_body_free_and_nested_under_existing_p6_path() -> None:
    from emlis_ai_public_feedback_meta import _build_p6_runtime_bridge_public_summary

    source = _source(PUBLIC_META_PATH)
    for token in (
        "r7_limited_surface_evaluated",
        "r7_limited_surface_connected",
        "limited_surface_allowed_family_only",
        "max_insight_seed_count",
        "post_connection_regate_required",
        "comment_text_owner",
    ):
        assert token in source

    internal_meta = {
        "structure_insight_p6_runtime_bridge": {
            "schema_version": "cocolon.emlis.structure_insight.p6_runtime_bridge.v1",
            "step": "P6_RuntimeBridge_Repair_20260612",
            "runtime_evaluated": True,
            "visible_applied": False,
            "visible_family": "none",
            "p5_dependency_status": "p5_ready",
            "r7_limited_surface_evaluated": True,
            "limited_surface_attempted": True,
            "limited_surface_candidate_generated": True,
            "limited_surface_section_placement": "seen_section",
            "insight_seed_count": 0,
            "p6_post_connection_gate_blocked": False,
            "limited_surface_meta": {
                "runtime_family": "structure_question",
                "relation_family": "desire_blockage_conflict",
                "surface_key": "structure_question_desire_blockage_insight_seed",
                "section_placement": "seen_section",
                "visible_applied": False,
                "visible_family": "none",
                "insight_seed_count": 0,
                "comment_text_body_included": False,
                "candidate_body_included": False,
                "surface_body_included": False,
            },
            "blocked_reason_codes": ["ratings_only_review_rows_missing"],
        }
    }
    public_summary = _build_p6_runtime_bridge_public_summary(internal_meta)
    assert public_summary["public_meta_summary_only"] is True
    assert public_summary["r7_limited_surface_evaluated"] is True
    assert public_summary["r7_limited_surface_connected"] is False
    assert public_summary["visible_family"] == "none"
    assert public_summary["limited_surface_allowed_family_only"] == "structure_question"
    assert public_summary["max_insight_seed_count"] == 1
    assert public_summary["comment_text_owner"] == "input_feedback.comment_text"
    assert public_summary["public_response_key_added"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["candidate_body_included"] is False
    assert public_summary["surface_body_included"] is False
    serialized = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)
    assert "動きたい向き" not in serialized
    assert "Emlisから" not in serialized


@pytest.mark.asyncio
async def test_r7_actual_reply_keeps_runtime_meta_body_free_and_structure_question_limited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_p5_runtime_history_context(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="p6-r7-runtime-user",
        subscription_tier="plus",
        current_input={
            "id": "p6-r7-current-001",
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
    p6_runtime_bridge = (
        reply.meta.get("structure_insight_p6_runtime_bridge")
        or diagnostic.get("structure_insight_p6_runtime_bridge")
        or reply.meta.get("p6_runtime_bridge")
    )
    assert isinstance(p6_runtime_bridge, dict)
    assert p6_runtime_bridge.get("schema_version") == "cocolon.emlis.structure_insight.p6_runtime_bridge.v1"
    assert p6_runtime_bridge.get("runtime_evaluated") is True
    assert p6_runtime_bridge.get("r7_limited_surface_evaluated") is True
    assert p6_runtime_bridge.get("visible_family") in {"structure_question", "none"}
    assert p6_runtime_bridge.get("max_insight_seed_count") == 1
    assert p6_runtime_bridge.get("comment_text_owner") == "input_feedback.comment_text"
    assert p6_runtime_bridge.get("public_contract", {}).get("public_response_key_added") is False
    assert p6_runtime_bridge.get("body_free", {}).get("comment_text_body_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("candidate_body_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("surface_body_included") is False
    assert p6_runtime_bridge.get("release_allowed") is False
