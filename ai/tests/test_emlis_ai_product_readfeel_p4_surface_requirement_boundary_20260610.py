# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-3 tests for public surface-requirement boundary correction.

P4-3 corrects the boundary between true low-information, rich current input,
limited grounding, and source-unavailable high-information material.  It must
not loosen gates, force material quality to eligible, add public/RN/API/DB keys,
or erase the P4-2 local replay that reproduced the old overroute.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    build_emlis_input_material_bundle,
)
from emlis_ai_limited_grounding_reception_surface import (
    assert_limited_grounding_reception_surface_meta,
    build_limited_grounding_reception_surface_plan,
    is_limited_grounding_reception_required,
)
from emlis_ai_public_surface_requirement import (
    LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    assert_public_surface_requirement_decision,
    assert_public_surface_requirement_decision_meta_only,
    resolve_public_surface_requirement,
)


_FORBIDDEN_META_KEYS = {
    "raw_input",
    "rawInput",
    "current_input",
    "currentInput",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "observation_text",
    "observationText",
    "reception_text",
    "receptionText",
    "body",
    "text",
}


def _assert_body_free(value: Mapping[str, Any]) -> None:
    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert not (set(node.keys()) & _FORBIDDEN_META_KEYS)
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(value)
    assert_public_surface_requirement_decision_meta_only(value)


def _rich_daily_current_input() -> dict[str, Any]:
    return {
        "memo": (
            "仕事で相手の言い方に引っかかったあと、嬉しさもあるのに、境界線をどこに置けばいいのかが"
            "ずっと残っている。自分が悪いだけなのか、相手との距離を考え直す合図なのか、まだ判断できない。"
        ),
        "memo_action": "すぐに返事せず、明日は一度、自分が守りたい距離を書き出してから話す。",
        "emotions": ["喜び", "違和感", "不安"],
        "category": ["仕事", "人間関係"],
    }


def _rich_visible_low_information_route() -> dict[str, Any]:
    return {
        "material_quality": MATERIAL_QUALITY_LOW_INFORMATION,
        "material_sufficient": False,
        "response_kind": "low_information_observation",
        "visible_material_slots": [
            "event",
            "action",
            "emotion_direction",
            "relationship",
            "target",
        ],
        "unknown_slots": ["cause"],
        "relation_material_ids": ["relationship_material", "boundary_or_transition"],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "gate_relaxed": False,
    }


def _true_low_information_current_input() -> dict[str, Any]:
    return {
        "memo": "疲れた",
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "category": [],
    }


def _source_unavailable_high_information_current_input() -> dict[str, Any]:
    return {
        "memo": (
            "仕事で大きな予定が崩れて、悔しさと不安が同時に残っている。"
            "今日の出来事として整理したい気持ちはあるが、まだ何から見ればいいか決めきれていない。"
        ),
        "memo_action": "明日は予定を組み直す前に、何が負担だったかだけ書き出す。",
        "emotions": ["不安", "悔しさ"],
        "category": ["仕事"],
    }


def _source_unavailable_high_information_route() -> dict[str, Any]:
    return {
        "material_quality": MATERIAL_QUALITY_ELIGIBLE,
        "material_sufficient": True,
        "response_kind": "normal_observation",
        "safety_triage_kind": "safe_observation",
        "visible_material_slots": ["event", "action", "emotion_direction", "target"],
        "unknown_slots": ["cause"],
        "relation_material_ids": [],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "gate_relaxed": False,
    }


def test_p4_3_rich_visible_material_no_longer_uses_low_information_surface() -> None:
    decision = resolve_public_surface_requirement(
        current_input=_rich_daily_current_input(),
        material_route=_rich_visible_low_information_route(),
        composer_meta={"composer_source": "ai_generated", "candidate_status": "generated"},
        diagnostic_summary={},
    )

    assert_public_surface_requirement_decision(decision)
    assert decision["material_quality_family"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert decision["input_material_classification"]["low_information_material"] is True
    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["low_information_allowed"] is False
    assert "low_information_material" not in decision["decision_sources"]
    assert "low_information_reception_required" not in decision["decision_sources"]
    assert "rich_visible_material_low_information_surface_boundary" in decision["decision_sources"]
    assert decision["required_comment_text_shape"]["contains_boundary"] == LABELLED_TWO_STAGE_RECEPTION_BOUNDARY
    assert decision["public_contract"]["rn_visible_contract_changed"] is False
    assert decision["public_contract"]["public_response_key_added"] is False
    assert decision["gate_policy"]["display_gate_relaxed"] is False
    assert decision["gate_policy"]["visible_surface_gate_relaxed"] is False
    assert decision["raw_input_included"] is False
    assert decision["comment_text_body_included"] is False
    _assert_body_free(decision)


def test_p4_3_local_audit_replay_can_still_show_the_old_overroute_when_disabled() -> None:
    replay_decision = resolve_public_surface_requirement(
        current_input=_rich_daily_current_input(),
        material_route=_rich_visible_low_information_route(),
        composer_meta={},
        diagnostic_summary={},
        p4_3_boundary_correction_enabled=False,
    )

    assert replay_decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    assert replay_decision["low_information_allowed"] is True
    assert "low_information_material" in replay_decision["decision_sources"]
    assert "rich_visible_material_low_information_surface_boundary" not in replay_decision["decision_sources"]
    _assert_body_free(replay_decision)


def test_p4_3_true_low_information_control_stays_low_information_reception_required() -> None:
    bundle = build_emlis_input_material_bundle(_true_low_information_current_input())
    assert bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION

    decision = resolve_public_surface_requirement(
        current_input=_true_low_information_current_input(),
        material_route=bundle.as_meta(),
        composer_meta={},
        diagnostic_summary={},
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    assert decision["two_stage_required"] is False
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is True
    assert "low_information_reception_required" in decision["decision_sources"]
    assert "rich_visible_material_low_information_surface_boundary" not in decision["decision_sources"]
    assert decision["gate_policy"]["display_gate_relaxed"] is False
    _assert_body_free(decision)


def test_p4_3_limited_grounding_keeps_labelled_reception_shape_and_question_only_forbidden() -> None:
    current_input = {
        "memo": (
            "昨日の自分より少し前に進めたらいいと思っている。"
            "人と比べると焦るけれど、小さな変化を大切にしたい。"
        ),
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "category": ["健康", "人生"],
    }
    bundle = build_emlis_input_material_bundle(current_input)
    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING

    decision = resolve_public_surface_requirement(
        current_input=current_input,
        material_route=bundle.as_meta(),
        composer_meta={},
        diagnostic_summary={},
    )
    plan = build_limited_grounding_reception_surface_plan(
        current_input=current_input,
        material_route=bundle.as_meta(),
        surface_requirement=decision,
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["low_information_allowed"] is False
    assert "limited_grounding_reception_required" in decision["decision_sources"]
    assert is_limited_grounding_reception_required(
        material_route=bundle.as_meta(),
        surface_requirement=decision,
    )
    assert plan["question_policy"]["question_only_forbidden"] is True
    assert plan["question_policy"]["question_position"] == "after_reception_optional"
    assert plan["reception_required"] is True
    assert_limited_grounding_reception_surface_meta(plan)
    _assert_body_free(decision)


def test_p4_3_source_unavailable_high_information_boundary_uses_labelled_shape_without_normal_rebuild() -> None:
    decision = resolve_public_surface_requirement(
        current_input=_source_unavailable_high_information_current_input(),
        material_route=_source_unavailable_high_information_route(),
        composer_meta={"composer_source": "unavailable", "candidate_status": "unavailable"},
        diagnostic_summary={
            "first_blocker_family": "source_unavailable",
            "first_blocker_code": "limited_composer_shallow_empty_candidate",
            "normal_observation_rebuild_allowed": False,
            "normal_observation_rebuild_blocker": "source_unavailable_not_rebuildable",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is False
    assert "source_unavailable_high_information_surface_boundary" in decision["decision_sources"]
    assert "low_information_material" not in decision["decision_sources"]
    assert decision["material_quality_family"] == MATERIAL_QUALITY_ELIGIBLE
    assert decision["input_material_classification"]["high_information_input"] is True
    assert decision["public_contract"]["response_shape_changed"] is False
    assert decision["gate_policy"]["runtime_surface_gate_relaxed"] is False
    _assert_body_free(decision)
