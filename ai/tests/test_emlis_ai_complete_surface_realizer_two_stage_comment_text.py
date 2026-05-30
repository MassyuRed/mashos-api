# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from typing import Any, Mapping

from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_STATUS_READY,
    COMPLETE_SURFACE_STATUS_UNAVAILABLE,
    EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION,
    EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE,
    EMLIS_TWO_STAGE_SURFACE_REALIZATION_SCHEMA_VERSION,
    build_complete_surface_realization_v2,
)
from test_emlis_ai_complete_sentence_plan_two_stage_section_meta import (
    _contains_forbidden_raw_key,
    _seed,
    _two_stage_plan,
)


FORBIDDEN_BODY_FRAGMENTS = (
    "先を考え続ける流れ",
    "pressure or limit",
)

PHASE17_3_FORBIDDEN_MODE_SURFACE_FRAGMENTS = (
    "achievement",
    "positive state",
    "positive_state",
    "perfection fear",
    "perfection_fear",
    "pressure or limit",
    "pressure_or_limit",
    "role_",
    "同じ流れ",
    "同じ場所",
    "別々の向き",
    "片方だけに寄らず",
    "自立できます",
    "もっと頑張りましょう",
    "完全に回復しています",
)


def _two_stage_sections(comment_text: str) -> tuple[str, str]:
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    observation, reception = comment_text.split("\n\nEmlisから：\n", 1)
    observation = observation.removeprefix("見えたこと：\n")
    return observation.strip(), reception.strip()


def _broken_reception_missing_plan() -> CompleteSentencePlanV2:
    plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )
    broken_lines = tuple(
        replace(
            line,
            meta={
                **dict(line.meta),
                "two_stage_section_id": "observation",
                "two_stage_section_role": "state_answer_observation",
                "two_stage_display_label": "見えたこと",
                "two_stage_section_order_index": 0,
            },
        )
        for line in plan.sentence_plans
    )
    return replace(plan, sentence_plans=broken_lines)


def _phase17_two_stage_line(
    *,
    sentence_id: str,
    role: str,
    section_id: str,
    order_index: int,
    line_role: str = "opening",
    relation_type: str = "center",
    mode_id: str = "phase17_2_internal_role_surface_test",
    ratio_reason: str = "phase17_2_internal_role_surface_test",
) -> CompleteSentencePlanLine:
    label = "見えたこと" if section_id == "observation" else "Emlisから"
    return CompleteSentencePlanLine(
        sentence_id=sentence_id,
        line_role=line_role,
        relation_type=relation_type,
        phrase_unit_ids=(f"pu_{sentence_id}",),
        evidence_span_ids=(f"span_{sentence_id}",),
        must_include_roles=(role,),
        meta={
            "two_stage_section_id": section_id,
            "two_stage_section_role": "state_answer_observation" if section_id == "observation" else "human_reception",
            "two_stage_display_label": label,
            "two_stage_comment_text_section_label": f"{label}：",
            "two_stage_section_label_required": True,
            "two_stage_section_order_index": order_index,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_surface_plan_required": True,
            "two_stage_reception_mode_id": mode_id,
            "two_stage_ratio_reason": ratio_reason,
        },
    )


def _phase17_internal_role_surface_plan() -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id="phase17_internal_role_surface_plan",
        coverage_group="phase17_internal_role_surface",
        sentence_budget=3,
        sentence_plans=(
            _phase17_two_stage_line(
                sentence_id="phase17_role_achievement",
                role="achievement",
                section_id="observation",
                order_index=0,
                line_role="opening",
                relation_type="center",
            ),
            CompleteSentencePlanLine(
                sentence_id="phase17_role_perfection_positive",
                line_role="relation",
                relation_type="contrast",
                phrase_unit_ids=("pu_phase17_role_perfection", "pu_phase17_role_positive"),
                evidence_span_ids=("span_phase17_role_perfection", "span_phase17_role_positive"),
                must_include_roles=("perfection_fear", "positive_state"),
                meta={
                    "two_stage_section_id": "reception",
                    "two_stage_section_role": "human_reception",
                    "two_stage_display_label": "Emlisから",
                    "two_stage_comment_text_section_label": "Emlisから：",
                    "two_stage_section_label_required": True,
                    "two_stage_section_order_index": 1,
                    "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
                    "two_stage_section_surface_plan_required": True,
                    "two_stage_reception_mode_id": "phase17_2_internal_role_surface_test",
                    "two_stage_ratio_reason": "phase17_2_internal_role_surface_test",
                },
            ),
        ),
        meta={
            "two_stage_section_surface_plan_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_labels_required": True,
        },
    )


def _phase17_unknown_role_surface_plan() -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id="phase17_unknown_role_surface_plan",
        coverage_group="phase17_unknown_role_surface",
        sentence_budget=2,
        sentence_plans=(
            _phase17_two_stage_line(
                sentence_id="phase17_unknown_observation",
                role="unregistered_debug_role",
                section_id="observation",
                order_index=0,
                line_role="opening",
                relation_type="center",
            ),
            _phase17_two_stage_line(
                sentence_id="phase17_unknown_reception",
                role="positive_state",
                section_id="reception",
                order_index=1,
                line_role="closing",
                relation_type="recovery",
            ),
        ),
        meta={
            "two_stage_section_surface_plan_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_labels_required": True,
        },
    )


def _phase17_3_mode_surface_line(
    *,
    sentence_id: str,
    roles: tuple[str, ...],
    section_id: str,
    order_index: int,
    mode_id: str,
    line_role: str = "opening",
    relation_type: str = "center",
) -> CompleteSentencePlanLine:
    label = "見えたこと" if section_id == "observation" else "Emlisから"
    return CompleteSentencePlanLine(
        sentence_id=sentence_id,
        line_role=line_role,
        relation_type=relation_type,
        phrase_unit_ids=(f"pu_{sentence_id}",),
        evidence_span_ids=(f"span_{sentence_id}",),
        must_include_roles=tuple(roles),
        meta={
            "two_stage_section_id": section_id,
            "two_stage_section_role": "state_answer_observation" if section_id == "observation" else "human_reception",
            "two_stage_display_label": label,
            "two_stage_comment_text_section_label": f"{label}：",
            "two_stage_section_label_required": True,
            "two_stage_section_order_index": order_index,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_surface_plan_required": True,
            "two_stage_reception_mode_id": mode_id,
            "two_stage_ratio_reason": "phase17_3_mode_specific_surface_policy_test",
        },
    )


def _phase17_3_mode_surface_plan(
    mode_id: str,
    lines: tuple[CompleteSentencePlanLine, ...],
) -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id=f"phase17_3_mode_surface_policy_{mode_id}",
        coverage_group="phase17_3_mode_specific_surface_policy",
        sentence_budget=len(lines),
        sentence_plans=lines,
        meta={
            "two_stage_section_surface_plan_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_labels_required": True,
        },
    )




def _phase17_3_mode_policy_plan(*, mode_id: str, first_role: str, second_role: str, third_role: str) -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id=f"phase17_3_mode_policy_{mode_id}",
        coverage_group="phase17_3_mode_specific_surface_policy",
        sentence_budget=3,
        sentence_plans=(
            _phase17_two_stage_line(
                sentence_id=f"phase17_3_{mode_id}_observation",
                role=first_role,
                section_id="observation",
                order_index=0,
                line_role="opening",
                relation_type="center",
                mode_id=mode_id,
                ratio_reason="phase17_3_mode_specific_two_stage_surface_policy",
            ),
            _phase17_two_stage_line(
                sentence_id=f"phase17_3_{mode_id}_reception",
                role=second_role,
                section_id="reception",
                order_index=1,
                line_role="relation",
                relation_type="recovery",
                mode_id=mode_id,
                ratio_reason="phase17_3_mode_specific_two_stage_surface_policy",
            ),
            _phase17_two_stage_line(
                sentence_id=f"phase17_3_{mode_id}_closing",
                role=third_role,
                section_id="reception",
                order_index=2,
                line_role="closing",
                relation_type="coexistence",
                mode_id=mode_id,
                ratio_reason="phase17_3_mode_specific_two_stage_surface_policy",
            ),
        ),
        meta={
            "two_stage_section_surface_plan_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_labels_required": True,
        },
    )


def test_phase16_4_surface_realizer_joins_sentence_lines_into_labelled_two_stage_comment_text() -> None:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )

    realization = build_complete_surface_realization_v2(sentence_plan=sentence_plan)

    assert realization.status == COMPLETE_SURFACE_STATUS_READY
    assert realization.comment_text.count("見えたこと：") == 1
    assert realization.comment_text.count("Emlisから：") == 1
    observation_body, reception_body = _two_stage_sections(realization.comment_text)
    assert observation_body
    assert reception_body
    assert all(fragment not in realization.comment_text for fragment in FORBIDDEN_BODY_FRAGMENTS)

    summary = realization.two_stage_surface_realization
    assert summary["schema_version"] == EMLIS_TWO_STAGE_SURFACE_REALIZATION_SCHEMA_VERSION
    assert summary["required"] is True
    assert summary["applied"] is True
    assert summary["expected_comment_text_shape"] == "labelled_two_stage_text"
    assert summary["labels_present"] is True
    assert summary["section_order_valid"] is True
    assert summary["observation_section_non_empty"] is True
    assert summary["reception_section_non_empty"] is True
    assert summary["section_line_counts"] == {"observation": 1, "reception": 1}
    assert summary["comment_text_body_included"] is False
    assert summary["public_response_key_added"] is False
    assert summary["raw_input_included"] is False
    assert summary["completed_reply_template_used"] is False
    assert summary["fixed_sentence_template_used"] is False
    assert summary["surface_body_fixed_by_phase16_4"] is False
    assert summary["gate_relaxed"] is False


def test_phase16_4_surface_realizer_meta_is_summary_only_without_public_contract_change() -> None:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )
    realization = build_complete_surface_realization_v2(sentence_plan=sentence_plan)
    meta = realization.as_meta(include_realized_text=False)

    assert meta["two_stage_surface_realization_applied"] is True
    assert meta["two_stage_comment_text_generated"] is True
    assert meta["two_stage_surface_realization_comment_text_body_included"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["comment_text_publicly_assigned"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert "realized_text" not in meta
    assert _contains_forbidden_raw_key(meta) is False


def test_phase16_4_surface_realizer_fail_closes_when_required_reception_section_is_missing() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan=_broken_reception_missing_plan())

    assert realization.status == COMPLETE_SURFACE_STATUS_UNAVAILABLE
    assert realization.comment_text == ""
    assert "two_stage_complete_sentence_plan_reception_section_missing" in realization.validation_errors
    summary = realization.two_stage_surface_realization
    assert summary["required"] is True
    assert summary["applied"] is False
    assert summary["reception_section_non_empty"] is False
    assert "two_stage_complete_sentence_plan_reception_section_missing" in summary["validation_errors"]

def test_phase17_2_internal_role_terms_are_surface_mapped_without_english_label_leak() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan=_phase17_internal_role_surface_plan())

    assert realization.status == COMPLETE_SURFACE_STATUS_READY
    assert realization.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in realization.comment_text
    assert "achievement" not in realization.comment_text
    assert "positive state" not in realization.comment_text
    assert "positive_state" not in realization.comment_text
    assert "perfection fear" not in realization.comment_text
    assert "perfection_fear" not in realization.comment_text
    assert "role_" not in realization.comment_text
    assert "気持ちが動いた変化" in realization.comment_text
    assert "完璧に元気でいようとする怖さ" in realization.comment_text
    assert "少し整えようとする動き" in realization.comment_text

    meta = realization.as_meta(include_realized_text=False)
    assert meta["internal_role_surface_policy_source_phase"] == "Phase17_2_internal_role_surface_phrase_bank"
    assert meta["internal_role_surface_phrase_bank_added"] is True
    assert meta["unknown_role_fallback_leaks_english_role_label"] is False
    assert meta["internal_role_surface_completion_template_used"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["raw_input_included"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_phase17_2_unknown_role_fallback_does_not_render_internal_role_key() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan=_phase17_unknown_role_surface_plan())

    assert realization.status == COMPLETE_SURFACE_STATUS_READY
    assert "unregistered debug role" not in realization.comment_text
    assert "unregistered_debug_role" not in realization.comment_text
    assert "role_unregistered_debug_role" not in realization.comment_text
    assert "根拠のある材料" in realization.comment_text
    assert "少し整えようとする動き" in realization.comment_text

    first_line = realization.surface_lines[0]
    assert first_line.role_phrase_key == "unknown_internal_structural_label_unregistered_debug_role"
    assert first_line.surface_text.startswith("根拠のある材料")
    assert first_line.meta.get("raw_input_included") is not True
    assert first_line.meta.get("fixed_sentence_template_used") is not True
    assert first_line.usable is True



def test_phase17_3_mode_specific_two_stage_surface_policy_renders_non_daily_product_surfaces() -> None:
    cases = (
        (
            "self_denial_support",
            ("self_confidence_uncertainty", "attempt_to_change", "challenge_attempt"),
            ("自信をつけたい気持ちと不安", "挑戦したい気持ち"),
        ),
        (
            "daily_positive_reception",
            ("work_fatigue", "conversation_wish", "joy_or_surprise"),
            ("仕事後の疲れ", "誰かと話したい気持ち", "小さく動いたサイン"),
        ),
        (
            "self_understanding_follow",
            ("self_blame_flow", "gentle_self_observation", "positive_state"),
            ("自分を責める流れ", "気持ちを少し優しく見ようとする方向", "否定だけで終わらせず"),
        ),
        (
            "effort_support",
            ("independence_intention", "health_pace", "sustainable_pace"),
            ("自立したい気持ち", "体調", "続けるペース"),
        ),
    )
    forbidden_fragments = (
        "achievement",
        "positive state",
        "positive_state",
        "perfection fear",
        "perfection_fear",
        "pressure or limit",
        "同じ流れ",
        "同じ場所",
        "別々の向き",
        "片方だけに寄らず",
        "role_",
    )

    for mode_id, roles, expected_fragments in cases:
        realization = build_complete_surface_realization_v2(
            sentence_plan=_phase17_3_mode_policy_plan(
                mode_id=mode_id,
                first_role=roles[0],
                second_role=roles[1],
                third_role=roles[2],
            )
        )

        assert realization.status == COMPLETE_SURFACE_STATUS_READY
        assert realization.comment_text.startswith("見えたこと：\n")
        assert "\n\nEmlisから：\n" in realization.comment_text
        assert all(fragment in realization.comment_text for fragment in expected_fragments), (mode_id, realization.comment_text)
        assert all(fragment not in realization.comment_text for fragment in forbidden_fragments), (mode_id, realization.comment_text)

        summary = realization.two_stage_surface_realization["mode_specific_two_stage_surface_policy"]
        assert summary["schema_version"] == "cocolon.emlis_two_stage.mode_specific_surface_policy.v1"
        assert summary["source_phase"] == "Phase17_3_mode_specific_two_stage_surface_policy"
        assert summary["applied"] is True
        assert summary["case_id_branch_used"] is False
        assert summary["relation_skeleton_suppressed"] is True
        assert summary["internal_role_label_suppressed"] is True
        assert summary["raw_input_included"] is False
        assert summary["comment_text_body_included"] is False
        assert summary["fixed_sentence_template_used"] is False


def test_phase17_3_mode_specific_surface_policy_breaks_repeated_predicate_stack_without_contract_change() -> None:
    realization = build_complete_surface_realization_v2(
        sentence_plan=_phase17_3_mode_policy_plan(
            mode_id="self_denial_support",
            first_role="self_confidence_uncertainty",
            second_role="attempt_to_change",
            third_role="challenge_attempt",
        )
    )

    assert realization.status == COMPLETE_SURFACE_STATUS_READY
    assert "same_predicate_family_stack" not in realization.validation_errors
    assert "tone_guard:ending_family_repetition" not in realization.validation_errors

    meta = realization.as_meta(include_realized_text=False)
    assert meta["mode_specific_two_stage_surface_policy_supported"] is True
    assert meta["mode_specific_two_stage_surface_policy_applied"] is True
    assert meta["mode_specific_two_stage_surface_policy_case_id_branch_used"] is False
    assert meta["mode_specific_two_stage_surface_policy_fixed_sentence_template_used"] is False
    assert meta["mode_specific_two_stage_surface_policy_raw_input_included"] is False
    assert meta["mode_specific_two_stage_surface_policy_comment_text_body_included"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_phase17_3_mode_specific_surface_policy_handles_non_daily_two_stage_modes_without_case_branch() -> None:
    cases: tuple[tuple[str, tuple[CompleteSentencePlanLine, ...], tuple[str, ...]], ...] = (
        (
            "self_denial_support",
            (
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_self_denial_obs",
                    roles=("self_confidence_uncertainty", "attempt_to_change"),
                    section_id="observation",
                    order_index=0,
                    mode_id="self_denial_support",
                ),
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_self_denial_rec",
                    roles=("self_denial", "challenge_attempt"),
                    section_id="reception",
                    order_index=1,
                    mode_id="self_denial_support",
                    line_role="relation",
                    relation_type="contrast",
                ),
            ),
            ("自信", "不安", "挑戦"),
        ),
        (
            "daily_positive_reception",
            (
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_daily_positive_obs",
                    roles=("work_fatigue", "conversation_wish"),
                    section_id="observation",
                    order_index=0,
                    mode_id="daily_positive_reception",
                ),
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_daily_positive_rec",
                    roles=("achievement", "joy_or_surprise"),
                    section_id="reception",
                    order_index=1,
                    mode_id="daily_positive_reception",
                    line_role="relation",
                    relation_type="recovery",
                ),
            ),
            ("仕事", "話したい", "受け取"),
        ),
        (
            "self_understanding_follow",
            (
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_self_understanding_obs",
                    roles=("self_blame_flow", "gentle_self_observation"),
                    section_id="observation",
                    order_index=0,
                    mode_id="self_understanding_follow",
                    line_role="relation",
                    relation_type="contrast",
                ),
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_self_understanding_rec",
                    roles=("perfection_fear", "positive_state"),
                    section_id="reception",
                    order_index=1,
                    mode_id="self_understanding_follow",
                    line_role="relation",
                    relation_type="recovery",
                ),
            ),
            ("責め", "優しく", "終わらせず"),
        ),
        (
            "effort_support",
            (
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_effort_pace_obs",
                    roles=("independence_intention", "life_context", "health_pace", "money_context"),
                    section_id="observation",
                    order_index=0,
                    mode_id="effort_support",
                ),
                _phase17_3_mode_surface_line(
                    sentence_id="phase17_3_effort_pace_rec",
                    roles=("sustainable_pace", "pressure_or_limit"),
                    section_id="reception",
                    order_index=1,
                    mode_id="effort_support",
                    line_role="relation",
                    relation_type="balance",
                ),
            ),
            ("自立", "生活", "お金", "続け"),
        ),
    )

    for mode_id, lines, required_fragments in cases:
        realization = build_complete_surface_realization_v2(
            sentence_plan=_phase17_3_mode_surface_plan(mode_id, lines),
        )
        assert realization.status == COMPLETE_SURFACE_STATUS_READY, (mode_id, realization.validation_errors)
        assert realization.comment_text.startswith("見えたこと：\n")
        assert "\n\nEmlisから：\n" in realization.comment_text
        assert all(fragment in realization.comment_text for fragment in required_fragments), realization.comment_text
        assert all(fragment not in realization.comment_text for fragment in PHASE17_3_FORBIDDEN_MODE_SURFACE_FRAGMENTS), realization.comment_text

        summary = realization.two_stage_surface_realization["two_stage_mode_specific_surface_policy"]
        assert summary["schema_version"] == EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SCHEMA_VERSION
        assert summary["source_phase"] == EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE
        assert summary["applied"] is True
        assert summary["case_id_branch_used"] is False
        assert summary["relation_skeleton_suppressed"] is True
        assert summary["internal_role_label_suppressed"] is True
        assert summary["comment_text_body_included"] is False
        assert summary["raw_input_included"] is False
        assert summary["fixed_sentence_template_used"] is False
        assert summary["public_response_key_added"] is False


def test_phase17_3_mode_specific_surface_policy_meta_is_summary_only() -> None:
    plan = _phase17_3_mode_surface_plan(
        "daily_positive_reception",
        (
            _phase17_3_mode_surface_line(
                sentence_id="phase17_3_meta_obs",
                roles=("work_fatigue", "conversation_wish"),
                section_id="observation",
                order_index=0,
                mode_id="daily_positive_reception",
            ),
            _phase17_3_mode_surface_line(
                sentence_id="phase17_3_meta_rec",
                roles=("achievement", "joy_or_surprise"),
                section_id="reception",
                order_index=1,
                mode_id="daily_positive_reception",
                line_role="relation",
                relation_type="recovery",
            ),
        ),
    )

    realization = build_complete_surface_realization_v2(sentence_plan=plan)
    meta = realization.as_meta(include_realized_text=False)

    assert meta["two_stage_mode_specific_surface_policy_supported"] is True
    assert meta["two_stage_mode_specific_surface_policy_applied"] is True
    assert meta["two_stage_mode_specific_surface_policy_source_phase"] == EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_SOURCE_PHASE
    assert meta["two_stage_mode_specific_surface_policy_case_id_branch_used"] is False
    assert meta["two_stage_mode_specific_surface_policy_comment_text_body_included"] is False
    assert meta["two_stage_mode_specific_surface_policy_public_response_key_added"] is False
    assert meta["two_stage_mode_specific_surface_policy_fixed_sentence_template_used"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["public_comment_text_assigned"] is False
    assert meta["raw_input_included"] is False
    assert "realized_text" not in meta
    assert _contains_forbidden_raw_key(meta) is False
