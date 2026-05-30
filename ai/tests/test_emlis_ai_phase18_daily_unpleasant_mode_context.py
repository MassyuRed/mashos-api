# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Mapping

from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from test_emlis_ai_complete_sentence_plan_two_stage_section_meta import _seed, _two_stage_plan


def _contains_forbidden_raw_key(value: Any) -> bool:
    forbidden = {
        "raw_text",
        "raw_input",
        "input_text",
        "user_input",
        "current_input",
        "memo",
        "memo_text",
        "memo_action",
        "raw_user_text",
        "original_text",
        "source_text",
        "comment_text",
        "body",
        "text",
    }
    if isinstance(value, Mapping):
        return any(str(key) in forbidden or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def test_phase18_5_ratio_only_daily_unpleasant_plan_does_not_fall_back_to_standard_state_answer() -> None:
    plan = _two_stage_plan()

    assert plan["reception_mode_id"] == "daily_unpleasant_reception"
    assert plan["ratio_reason"] == "daily_unpleasant_reception_light"
    assert plan["mode_context_schema_version"] == "cocolon.emlis.two_stage.mode_context.v1"
    assert plan["mode_context_source_phase"] == "Phase18_product_quality_stabilization"
    assert plan["mode_context"]["reception_mode_id"] == "daily_unpleasant_reception"
    assert plan["mode_context"]["ratio_reason"] == "daily_unpleasant_reception_light"
    assert plan["coverage_group_only_mode_selection_used"] is False
    assert plan["case_id_branch_used"] is False
    assert plan["public_response_key_added"] is False
    assert _contains_forbidden_raw_key(plan["mode_context"]) is False


def test_phase18_5_daily_unpleasant_mode_context_is_propagated_to_sentence_lines_and_surface_realizer() -> None:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )

    assert [line.meta["two_stage_section_id"] for line in sentence_plan.sentence_plans] == ["observation", "reception"]
    for line in sentence_plan.sentence_plans:
        assert line.meta["two_stage_reception_mode_id"] == "daily_unpleasant_reception"
        assert line.meta["two_stage_ratio_reason"] == "daily_unpleasant_reception_light"
        assert line.meta["two_stage_mode_context_schema_version"] == "cocolon.emlis.two_stage.mode_context.v1"
        assert line.meta["two_stage_mode_context_propagated_to_sentence_line"] is True
        assert line.meta["two_stage_mode_context_propagated_to_surface_realizer"] is True
        assert line.meta["two_stage_mode_context_coverage_group_only_mode_selection_used"] is False
        assert line.meta["two_stage_mode_context_case_id_branch_used"] is False

    realization = build_complete_surface_realization_v2(sentence_plan=sentence_plan)

    assert realization.status == "ready"
    assert "不快さ" in realization.comment_text or "怖さ" in realization.comment_text or "嫌な反応" in realization.comment_text
    assert "軽く流しにくい" in realization.comment_text or "受け取れます" in realization.comment_text
    assert "生活・体調・お金" not in realization.comment_text
    assert "続けるペース" not in realization.comment_text

    two_stage = realization.two_stage_surface_realization
    mode_context = two_stage["two_stage_mode_context"]
    assert mode_context["schema_version"] == "cocolon.emlis.two_stage.mode_context.v1"
    assert mode_context["source_phase"] == "Phase18_product_quality_stabilization"
    assert mode_context["reception_mode_id"] == "daily_unpleasant_reception"
    assert mode_context["ratio_reason"] == "daily_unpleasant_reception_light"
    assert mode_context["mode_context_propagated_to_sentence_line"] is True
    assert mode_context["mode_context_propagated_to_surface_realizer"] is True
    assert mode_context["coverage_group_only_mode_selection_used"] is False
    assert mode_context["case_id_branch_used"] is False
    assert mode_context["comment_text_body_included"] is False
    assert mode_context["public_response_key_added"] is False

    policy = two_stage["two_stage_mode_specific_surface_policy"]
    assert policy["mode_ids"] == ["daily_unpleasant_reception"]
    assert all(key.startswith("daily_unpleasant") for key in policy["surface_keys"])
    assert policy["case_id_branch_used"] is False
    assert policy["comment_text_body_included"] is False

    quality = two_stage["daily_unpleasant_reception_surface_quality"]
    assert quality["applied"] is True
    assert quality["observation_event_reaction_shape_applied"] is True
    assert quality["natural_short_reception_applied"] is True
    assert quality["forbidden_surface_hits"] == []

    meta = realization.as_meta(include_realized_text=False)
    assert meta["two_stage_mode_context_propagated_to_sentence_line"] is True
    assert meta["two_stage_mode_context_propagated_to_surface_realizer"] is True
    assert meta["two_stage_mode_context_coverage_group_only_mode_selection_used"] is False
    assert meta["two_stage_mode_context_case_id_branch_used"] is False
    assert meta["two_stage_mode_context_comment_text_body_included"] is False
    assert meta["two_stage_mode_context_public_response_key_added"] is False
