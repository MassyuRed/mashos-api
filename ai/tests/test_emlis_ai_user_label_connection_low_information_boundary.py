# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_candidate import build_user_label_connection_candidate_meta
from emlis_ai_user_label_connection_gate import (
    GATE_ACTION_BLOCK_SURFACE_PLAN,
    assert_user_label_connection_gate_meta_contract,
    build_user_label_connection_gate_decision,
    build_user_label_connection_gate_report,
)
from emlis_ai_user_label_connection_material import build_user_label_connection_material


def _current_low_information() -> dict[str, object]:
    return {
        "id": "current-phase5-low-info-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "",
        "memo": "なんか無理",
    }


def _normal_current() -> dict[str, object]:
    return {
        "id": "current-phase5-low-boundary-normal-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場でうまく話せなかった",
        "memo": "このまま続けられるかわからない",
    }


def _history() -> dict[str, object]:
    return {
        "id": "history-phase5-low-info-001",
        "created_at": "2026-05-28T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": "職場で説明を求められた",
        "memo": "続けたい気持ちと限界が同時にある",
    }


def _normal_material() -> Any:
    return build_user_label_connection_material(
        _normal_current(),
        source_bundle=SourceBundle(
            user_id="phase5-low-boundary-user",
            display_name="Mash",
            current_input=_normal_current(),
            last_input=_history(),
            similar_inputs=[_history()],
        ),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
    )


def test_phase5_low_information_material_does_not_promote_history_connection_to_surface_candidate() -> None:
    low_material = build_user_label_connection_material(
        _current_low_information(),
        source_bundle=SourceBundle(
            user_id="phase5-low-info-user",
            display_name="Mash",
            current_input=_current_low_information(),
            last_input=_history(),
            similar_inputs=[_history()],
        ),
        capability=resolve_emlis_ai_capability_for_tier("plus"),
        observation_reply_meta={
            "eligibility_status": "low_information",
            "eligible_for_full_observation": False,
            "question_required": True,
        },
    )

    report = build_user_label_connection_gate_report(
        material=low_material,
        proposed_surface="今回と近い記録の範囲では、以前も無理だった線のように見えます。",
    )

    assert report["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert report["passed"] is False
    assert report["blocked"] is True
    assert "low_information_history_promotion_blocked" in report["rejection_reasons"]
    assert report["allow_limited_surface_plan"] is False
    assert report["surface_plan_generated"] is False
    assert report["comment_text_generated"] is False
    assert_user_label_connection_gate_meta_contract(report)


def test_phase5_low_information_reply_meta_blocks_even_if_normal_history_candidate_is_supplied() -> None:
    normal_material = _normal_material()
    candidate = build_user_label_connection_candidate_meta(normal_material)

    report = build_user_label_connection_gate_decision(
        candidate,
        material=normal_material,
        observation_reply_meta={
            "observation_reply_kind": "low_information",
            "eligible_for_full_observation": False,
            "question_required": True,
        },
        proposed_surface="今回と近い記録の範囲では、似た状態ラベルと環境ラベルが同じ線の上に出ているように見えます。",
    )

    assert report["action"] == GATE_ACTION_BLOCK_SURFACE_PLAN
    assert report["passed"] is False
    assert report["blocked"] is True
    assert "low_information_history_promotion_blocked" in report["rejection_reasons"]
    assert report["allow_limited_surface_plan"] is False
    assert_user_label_connection_gate_meta_contract(report)
