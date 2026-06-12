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
from test_emlis_ai_structure_insight_p6_limited_surface_r7_20260612 import (
    _gate_reports,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPLY_SERVICE_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
PUBLIC_META_PATH = PROJECT_ROOT / "services" / "ai_inference" / "emlis_ai_public_feedback_meta.py"

R8_REQUIRED_NO_CONNECT_FAMILIES = {
    "low_information_short",
    "daily_unpleasant",
    "daily_positive",
    "positive_only",
    "safety_triage_required",
    "safety_adjacent",
    "self_denial",
    "target_judgement",
    "anger_or_boundary",
    "limited_grounding",
}

R8_RUNTIME_REQUIRED_TOKENS = {
    "R8_NoConnectFamilySafetyLowInfoDailyPositiveRegression_20260612",
    "r8_no_connect_regression",
    "no_connect_family_runtime",
    "no_connect_family_visible_applied",
    "low_information_short",
    "daily_unpleasant",
    "daily_positive",
    "positive_only",
    "safety_triage_required",
    "safety_adjacent",
    "self_denial",
    "target_judgement",
    "anger_or_boundary",
    "limited_grounding",
    "no_deep_insight_for_daily",
    "no_deep_insight_for_low_information",
    "no_deep_insight_for_positive_only",
    "no_deep_insight_for_safety_adjacent",
}

R8_PUBLIC_META_REQUIRED_TOKENS = {
    "r8_no_connect_regression",
    "no_connect_family_runtime",
    "no_connect_family_visible_applied",
    "no_deep_insight_for_daily",
    "no_deep_insight_for_low_information",
    "no_deep_insight_for_positive_only",
    "no_deep_insight_for_safety_adjacent",
}


def _source(path: Path = REPLY_SERVICE_PATH) -> str:
    return path.read_text(encoding="utf-8")


def _missing_tokens(text: str, tokens: set[str]) -> list[str]:
    return sorted(token for token in tokens if token not in text)


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    forbidden = {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "reviewer_free_text",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body",
        "text",
    }
    if isinstance(value, dict):
        return any(str(key) in forbidden or _contains_forbidden_text_payload_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def _ready_structure_question_chain() -> dict[str, Any]:
    from test_emlis_ai_structure_insight_p6_limited_surface_r7_20260612 import _ready_structure_question_chain

    return _ready_structure_question_chain()


def _no_connect_chain(family: str) -> dict[str, Any]:
    from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
    from emlis_ai_structure_insight_p6_gate_hardening import build_structure_insight_p6_gate_hardening
    from emlis_ai_structure_insight_p6_quality_rubric import build_structure_insight_p6_quality_rubric
    from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy
    from emlis_ai_structure_insight_p6_surface_role_plan import build_structure_insight_p6_surface_role_plan

    material_quality = "eligible"
    if family == "low_information_short":
        runtime_family = "low_information"
        material_quality = "low_information"
    elif family == "safety_adjacent":
        runtime_family = "safety_triage_required"
    elif family == "self_denial":
        runtime_family = "self_denial_safety_adjacent"
    elif family == "anger_or_boundary":
        runtime_family = "anger_attack_or_target_blame"
    else:
        runtime_family = family

    boundary = build_structure_insight_p6_family_boundary(
        family=runtime_family,
        material_quality=material_quality,
        current_input_grounded=True,
        observation_status="passed",
        safety_adjacent=family in {"safety_adjacent", "self_denial"},
        target_judgement_required=family == "target_judgement",
        run_id=f"p6-r8-no-connect-boundary-{family}",
    )
    policy = build_structure_insight_p6_relation_policy(
        relation_family="history_fact_line_as_insight",
        p6_family_boundary=boundary,
        low_information_overread_risk=family == "low_information_short",
        target_judgement_required=family == "target_judgement",
        self_denial_identity_fact_required=family == "self_denial",
        run_id=f"p6-r8-no-connect-policy-{family}",
    )
    quality = build_structure_insight_p6_quality_rubric(
        review_rows=[],
        p6_relation_policy=policy,
        p6_family_boundary=boundary,
        run_id=f"p6-r8-no-connect-quality-{family}",
    )
    gate = build_structure_insight_p6_gate_hardening(
        proposed_surface=None,
        relation_family="history_fact_line_as_insight",
        p6_relation_policy=policy,
        p6_quality_rubric=quality,
        run_id=f"p6-r8-no-connect-gate-{family}",
    )
    surface_role_plan = build_structure_insight_p6_surface_role_plan(
        family=runtime_family,
        relation_family="history_fact_line_as_insight",
        p6_family_boundary=boundary,
        p6_relation_policy=policy,
        p6_quality_rubric=quality,
        p6_gate_hardening=gate,
        requested_insight_seed_count=0,
        target_judgement_risk=family == "target_judgement",
        surface_plan_meta={
            "r8_no_connect_regression": True,
            "fixed_sentence_template_added": False,
            "public_response_key_added": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "release_allowed": False,
        },
        run_id=f"p6-r8-no-connect-surface-plan-{family}",
    )
    return {
        "runtime_family": runtime_family,
        "boundary": boundary,
        "policy": policy,
        "quality": quality,
        "gate": gate,
        "surface_role_plan": surface_role_plan,
    }


def test_r8_reply_service_and_public_meta_keep_no_connect_regression_markers() -> None:
    reply_source = _source(REPLY_SERVICE_PATH)
    public_source = _source(PUBLIC_META_PATH)

    assert _missing_tokens(reply_source, R8_RUNTIME_REQUIRED_TOKENS) == []
    assert _missing_tokens(public_source, R8_PUBLIC_META_REQUIRED_TOKENS) == []
    assert "public_response_key_added\": True" not in reply_source
    assert "rn_visible_contract_changed\": True" not in reply_source
    assert "db_schema_changed\": True" not in reply_source


def test_r8_limited_surface_still_allows_only_structure_question_after_regression_guard() -> None:
    from emlis_ai_structure_insight_p6_limited_surface_connection import (
        build_structure_insight_p6_limited_surface_connection,
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
        run_id="p6-r8-allowed-structure-question-control",
    )

    assert result.applied is True
    meta = result.as_meta()
    assert meta["visible_family"] == "structure_question"
    assert meta["insight_seed_count"] == 1
    assert meta["no_connect_family_visible_applied"] is False
    assert meta["body_free"]["surface_body_included"] is False


@pytest.mark.parametrize("family", sorted(R8_REQUIRED_NO_CONNECT_FAMILIES))
def test_r8_direct_no_connect_family_never_receives_p6_visible_surface(family: str) -> None:
    from emlis_ai_structure_insight_p6_limited_surface_connection import (
        build_structure_insight_p6_limited_surface_connection,
        structure_insight_p6_limited_surface_connection_public_summary,
    )

    chain = _no_connect_chain(family)
    result = build_structure_insight_p6_limited_surface_connection(
        "見えたこと:\n見えている範囲だけを受け取ります。\n\nEmlisから:\nここは重くしません。",
        observation_status="passed",
        p6_family_boundary=chain["boundary"],
        p6_relation_policy=chain["policy"],
        p6_quality_rubric=chain["quality"],
        p6_gate_hardening=chain["gate"],
        p6_surface_role_plan=chain["surface_role_plan"],
        existing_gate_reports=_gate_reports(),
        proposed_surface="構造の深掘りを出してはいけません。",
        run_id=f"p6-r8-direct-no-connect-{family}",
    )

    assert result.applied is False
    meta = result.as_meta()
    assert meta["visible_applied"] is False
    assert meta["visible_family"] == "none"
    assert meta["insight_seed_count"] == 0
    assert meta["max_insight_seed_count"] == 1
    assert meta["no_connect_family_visible_applied"] is False
    assert meta["comment_text_owner"] == "input_feedback.comment_text"
    assert meta["public_contract"]["public_response_key_added"] is False
    assert meta["body_free"]["comment_text_body_included"] is False
    assert meta["body_free"]["candidate_body_included"] is False
    assert meta["body_free"]["surface_body_included"] is False
    assert any("no_connect_family" in str(reason) for reason in meta["blocked_reason_codes"])

    public_summary = structure_insight_p6_limited_surface_connection_public_summary(meta)
    assert public_summary["visible_applied"] is False
    assert public_summary["visible_family"] == "none"
    assert public_summary["insight_seed_count"] == 0
    assert public_summary["release_allowed"] is False
    assert _contains_forbidden_text_payload_key(public_summary) is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("case_id", "current_input", "expected_family"),
    [
        (
            "daily-positive",
            {
                "id": "p6-r8-daily-positive-001",
                "created_at": "2026-06-12T00:00:00Z",
                "memo": "今日は少しだけ前に進めてうれしかった。",
                "memo_action": "できたことを残した。",
                "emotion_details": [{"type": "うれしい", "strength": "medium"}],
                "emotions": ["うれしい", "安心"],
                "category": ["daily_positive"],
            },
            "daily_positive",
        ),
        (
            "target-judgement",
            {
                "id": "p6-r8-target-judgement-001",
                "created_at": "2026-06-12T00:00:00Z",
                "memo": "あの人は絶対にわざと私を軽く扱っていると思う。",
                "memo_action": "相手への判断を残した。",
                "emotion_details": [{"type": "怒り", "strength": "strong"}],
                "emotions": ["怒り"],
                "category": ["target_judgement"],
            },
            "target_judgement",
        ),
    ],
)
async def test_r8_actual_reply_runtime_blocks_no_connect_family_visible_surface(
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    current_input: dict[str, Any],
    expected_family: str,
) -> None:
    _install_p5_runtime_history_context(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id=f"p6-r8-runtime-{case_id}",
        subscription_tier="plus",
        current_input=current_input,
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
    assert p6_runtime_bridge.get("r8_no_connect_regression") is True
    assert p6_runtime_bridge.get("runtime_family") == expected_family
    assert p6_runtime_bridge.get("no_connect_family_runtime") == expected_family
    assert p6_runtime_bridge.get("visible_applied") is False
    assert p6_runtime_bridge.get("p6_visible_applied") is False
    assert p6_runtime_bridge.get("visible_family") == "none"
    assert p6_runtime_bridge.get("insight_seed_count") == 0
    assert p6_runtime_bridge.get("no_connect_family_visible_applied") is False
    assert any("no_connect_family" in str(reason) for reason in p6_runtime_bridge.get("blocked_reason_codes") or [])
    assert p6_runtime_bridge.get("public_contract", {}).get("public_response_key_added") is False
    assert p6_runtime_bridge.get("body_free", {}).get("comment_text_body_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("candidate_body_included") is False
    assert p6_runtime_bridge.get("body_free", {}).get("surface_body_included") is False
    assert p6_runtime_bridge.get("release_allowed") is False

    serialized = json.dumps(p6_runtime_bridge, ensure_ascii=False, sort_keys=True)
    assert current_input["memo"] not in serialized
    assert "構造の深掘り" not in serialized
