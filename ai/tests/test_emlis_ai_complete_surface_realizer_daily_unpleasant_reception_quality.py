# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_STATUS_UNAVAILABLE,
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
)
from test_emlis_ai_complete_sentence_plan_two_stage_section_meta import (
    _contains_forbidden_raw_key,
    _seed,
    _two_stage_plan,
)


DAILY_UNPLEASANT_FORBIDDEN_FRAGMENTS = (
    "explicit negative reaction",
    "daily event fact",
    "先を考え続ける流れ",
    "pressure or limit",
    "重なりとして",
    "同じ流れ",
    "同じ場所",
    "何があったか残してみませんか",
    "まだ詳しい出来事までは見えません",
    "相手が悪い",
    "あなたの怒りは正しい",
    "危険な目に遭いました",
    "トラウマ",
)


def _build_daily_unpleasant_realization() -> Any:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )
    return build_complete_surface_realization_v2(sentence_plan=sentence_plan)


def test_phase16_5_daily_unpleasant_reception_surface_uses_natural_short_reception_without_skeleton_leak() -> None:
    realization = _build_daily_unpleasant_realization()

    assert realization.ready is True
    comment_text = realization.comment_text
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert comment_text.count("見えたこと：") == 1
    assert comment_text.count("Emlisから：") == 1
    assert all(fragment not in comment_text for fragment in DAILY_UNPLEASANT_FORBIDDEN_FRAGMENTS)
    assert any(marker in comment_text for marker in ("不快さ", "怖さ", "嫌な反応"))
    assert any(marker in comment_text for marker in ("軽く流しにくい", "受け取れます"))

    summary = realization.two_stage_surface_realization["daily_unpleasant_reception_surface_quality"]
    assert summary["applied"] is True
    assert summary["observation_event_reaction_shape_applied"] is True
    assert summary["natural_short_reception_applied"] is True
    assert summary["no_pressure_or_limit_skeleton"] is True
    assert summary["no_relation_skeleton_leak"] is True
    assert summary["no_low_information_prompt_escape"] is True
    assert summary["no_target_judgement_agreement"] is True
    assert summary["no_analytic_register"] is True
    assert summary["no_structural_label_leak"] is True
    assert summary["forbidden_surface_hits"] == []
    assert summary["comment_text_body_included"] is False
    assert summary["surface_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["public_response_key_added"] is False
    assert summary["rn_visible_contract_changed"] is False
    assert summary["fixed_sentence_template_used"] is False
    assert summary["fixed_string_renderer_used"] is False
    assert summary["external_ai_used"] is False
    assert summary["local_llm_used"] is False


def test_phase16_5_daily_unpleasant_reception_meta_is_summary_only_without_raw_or_body() -> None:
    realization = _build_daily_unpleasant_realization()
    meta = realization.as_meta(include_realized_text=False)

    assert "realized_text" not in meta
    assert meta["daily_unpleasant_surface_quality_supported"] is True
    assert meta["daily_unpleasant_surface_quality_applied"] is True
    assert meta["daily_unpleasant_surface_quality_passed"] is True
    summary = meta["daily_unpleasant_reception_surface_quality"]
    assert summary["comment_text_body_included"] is False
    assert summary["surface_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["public_response_key_added"] is False
    assert _contains_forbidden_raw_key(meta) is False


def _manual_daily_unpleasant_surface_line(section_id: str, text: str, sentence_id: str) -> dict[str, Any]:
    display_label = "見えたこと" if section_id == "observation" else "Emlisから"
    section_role = "state_answer_observation" if section_id == "observation" else "emlis_reception"
    section_index = 0 if section_id == "observation" else 1
    two_stage_meta = {
        "two_stage_section_id": section_id,
        "two_stage_section_role": section_role,
        "two_stage_display_label": display_label,
        "two_stage_comment_text_section_label": f"{display_label}：",
        "two_stage_section_label_required": True,
        "two_stage_section_order_index": section_index,
        "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
        "two_stage_section_surface_plan_required": True,
        "two_stage_reception_mode_id": "daily_unpleasant_reception",
        "two_stage_ratio_reason": "daily_unpleasant_reception_light",
    }
    return {
        "sentence_id": sentence_id,
        "line_role": "core",
        "relation_type": "center",
        "surface_text": text,
        "phrase_unit_ids": [f"pu_{sentence_id}"],
        "evidence_span_ids": [f"ev_{sentence_id}"],
        "role_phrase_key": "manual_daily_unpleasant_probe",
        "source_sentence_plan_line": {"sentence_id": sentence_id, "meta": dict(two_stage_meta)},
        "meta": dict(two_stage_meta),
    }


def test_phase16_5_daily_unpleasant_reception_skeleton_leak_is_fail_closed() -> None:
    realization = CompleteSurfaceRealizationV2(
        plan_id="daily_unpleasant_quality_probe",
        coverage_group="short_daily",
        surface_lines=(
            _manual_daily_unpleasant_surface_line("observation", "先を考え続ける流れが前面にあります。", "probe_obs"),
            _manual_daily_unpleasant_surface_line("reception", "pressure or limitとして重なりを保っています。", "probe_rec"),
        ),
    )

    assert realization.status == COMPLETE_SURFACE_STATUS_UNAVAILABLE
    assert realization.comment_text == ""
    assert any(reason.startswith("daily_unpleasant_surface_quality:") for reason in realization.validation_errors)
    quality = realization.two_stage_surface_realization["daily_unpleasant_reception_surface_quality"]
    assert quality["blocked_by_surface_quality"] is True
    assert quality["forbidden_surface_hits"]
    assert realization.two_stage_surface_realization["daily_unpleasant_surface_quality_forbidden_hits"] == quality["forbidden_surface_hits"]
    assert quality["gate_relaxed"] is False
