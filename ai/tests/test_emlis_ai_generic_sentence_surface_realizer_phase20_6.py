from __future__ import annotations

from pathlib import Path
import json

import emlis_ai_complete_surface_realizer as surface_realizer
from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_two_stage_section_surface_plan import build_two_stage_section_surface_plan
from emlis_ai_complete_surface_realizer import (
    EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID,
    EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_MODE_IDS,
    build_complete_surface_realization_v2,
    _realize_line,
)


_OLD_C_COMPLETED_SURFACE_SNIPPETS = (
    "人へ向いていた疑問が物や環境を見る方向へ移り",
    "人への疑問だけに寄りすぎていた負荷",
    "授業で得た視点を日常の観察やメモへ移す行動",
    "考え込みすぎの重さから行動へ向き直る流れ",
)

_OLD_D_COMPLETED_SURFACE_SNIPPETS = (
    "少し戻る動きとして、その前の悲しさを残しながら",
    "友達の優しさや自分のために怒ってくれる存在",
    "前の関係が終わった痛みを消すものではなく",
    "受け取った優しさを別の形で返したい意図",
)


def _line(
    *,
    sentence_id: str,
    section_id: str,
    mode_id: str,
    ratio_reason: str,
    roles: tuple[str, ...],
    relation_type: str,
    line_role: str = "core",
    order_index: int = 0,
) -> CompleteSentencePlanLine:
    return CompleteSentencePlanLine(
        sentence_id=sentence_id,
        line_role=line_role,
        relation_type=relation_type,
        phrase_unit_ids=(f"pu_{sentence_id}",),
        evidence_span_ids=(f"ev_{sentence_id}",),
        must_include_roles=roles,
        max_chars=180,
        surface_intent="observe_current_input_material",
        repair_policy=("grounding_current_input_only", "assertion_soften"),
        meta={
            "two_stage_section_id": section_id,
            "two_stage_display_label": "見えたこと：" if section_id == "observation" else "Emlisから：",
            "two_stage_section_label_required": True,
            "two_stage_expected_comment_text_shape": "labelled_two_stage_text",
            "two_stage_section_order_index": order_index,
            "two_stage_reception_mode_id": mode_id,
            "two_stage_ratio_reason": ratio_reason,
        },
    )


def _realized_line_for(line: CompleteSentencePlanLine):
    return _realize_line(
        line,
        sequence_index=0,
        used_predicate_keys=(),
        used_ending_keys=(),
        used_connector_keys=(),
    )


def test_phase20_9_c_d_dedicated_mode_sets_are_removed_from_surface_policy_runtime() -> None:
    assert not hasattr(surface_realizer, "EMLIS_TWO_STAGE_SELF_UNDERSTANDING_LEARNING_SHIFT_MODE_IDS")
    assert not hasattr(surface_realizer, "EMLIS_TWO_STAGE_RELATIONSHIP_GRATITUDE_RECOVERY_MODE_IDS")
    assert EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID == "generic_sentence_plan_surface"
    assert EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID not in EMLIS_TWO_STAGE_MODE_SPECIFIC_SURFACE_POLICY_MODE_IDS


def test_phase20_9_source_no_longer_contains_c_d_completed_surface_bodies_or_dispatch_symbols() -> None:
    source_path = Path(__file__).parents[1] / "services" / "ai_inference" / "emlis_ai_complete_surface_realizer.py"
    source = source_path.read_text(encoding="utf-8")

    for snippet in (*_OLD_C_COMPLETED_SURFACE_SNIPPETS, *_OLD_D_COMPLETED_SURFACE_SNIPPETS):
        assert snippet not in source

    assert "_learning_shift_surface_text_for_line" not in source
    assert "_relationship_gratitude_surface_text_for_line" not in source
    assert "phase20_6_generic_sentence_surface_body_source" in source
    assert "sentence_plan_relation_material_tone_boundary_policy" in source


def test_phase20_9_self_understanding_material_realizes_from_generic_sentence_plan() -> None:
    line = _line(
        sentence_id="phase20_9_c_observation",
        section_id="observation",
        mode_id=EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID,
        ratio_reason="generic_relation_material",
        roles=("self_understanding_learning", "action_or_learning_practice"),
        relation_type="coexistence",
    )

    realized = _realized_line_for(line)
    text = realized.surface_text
    meta = realized.meta

    assert text
    assert "見えています" in text
    assert "見方" in text or "行動" in text
    for snippet in _OLD_C_COMPLETED_SURFACE_SNIPPETS:
        assert snippet not in text
    assert meta["phase20_6_generic_sentence_surface_applied"] is True
    assert meta["phase20_6_generic_sentence_surface_mode_id"] == EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID
    assert meta["phase20_6_generic_sentence_surface_mode_specific_bank_used"] is False
    assert meta["phase20_6_generic_sentence_surface_case_specific_route_used"] is False
    assert meta["phase20_6_generic_sentence_surface_c_d_specific_runtime_cue_used"] is False
    assert meta["phase20_6_generic_sentence_surface_observation_words_bound_to_relation"] is True
    assert meta["raw_input_included"] is False
    assert meta["phase20_6_generic_sentence_surface_public_response_key_added"] is False


def test_phase20_9_relationship_material_realizes_from_generic_sentence_plan() -> None:
    line = _line(
        sentence_id="phase20_9_d_observation",
        section_id="observation",
        mode_id=EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID,
        ratio_reason="generic_relation_material",
        roles=("relationship_end", "support_from_other", "gratitude_or_return_intent"),
        relation_type="recovery",
    )

    realized = _realized_line_for(line)
    text = realized.surface_text
    meta = realized.meta

    assert text
    assert "見えています" in text
    assert "関係" in text or "支え" in text or "区切り" in text
    for snippet in _OLD_D_COMPLETED_SURFACE_SNIPPETS:
        assert snippet not in text
    assert "元彼" not in text
    assert "相手が悪い" not in text
    assert "してください" not in text
    assert meta["phase20_6_generic_sentence_surface_applied"] is True
    assert meta["phase20_6_generic_sentence_surface_mode_id"] == EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID
    assert meta["phase20_6_generic_sentence_surface_mode_specific_bank_used"] is False
    assert meta["phase20_6_generic_sentence_surface_case_specific_route_used"] is False
    assert meta["phase20_6_generic_sentence_surface_c_d_specific_runtime_cue_used"] is False
    assert meta["phase20_6_generic_sentence_surface_observation_words_bound_to_relation"] is True


def test_phase20_9_two_stage_surface_report_exposes_generic_surface_summary_without_public_shape_change() -> None:
    plan = CompleteSentencePlanV2(
        plan_id="phase20_9_generic_sentence_plan_report",
        sentence_budget=2,
        coverage_group="generic_relation_material",
        sentence_plans=(
            _line(
                sentence_id="phase20_9_report_observation",
                section_id="observation",
                mode_id=EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID,
                ratio_reason="generic_relation_material",
                roles=("self_understanding_learning",),
                relation_type="coexistence",
                line_role="core",
                order_index=0,
            ),
            _line(
                sentence_id="phase20_9_report_reception",
                section_id="reception",
                mode_id=EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID,
                ratio_reason="generic_relation_material",
                roles=("action_or_learning_practice",),
                relation_type="coexistence",
                line_role="closing",
                order_index=1,
            ),
        ),
        meta={"two_stage_section_surface_plan_required": True},
    )

    realization = build_complete_surface_realization_v2(sentence_plan=plan)
    report = realization.two_stage_surface_realization
    phase20_6 = report["phase20_6_generic_sentence_surface"]

    assert realization.ready is True
    assert report["expected_comment_text_shape"] == "labelled_two_stage_text"
    assert report["comment_text_publicly_assigned"] is False
    assert report["public_response_key_added"] is False
    assert phase20_6["applied"] is True
    assert phase20_6["line_count"] == 2
    assert phase20_6["source_material_mode_ids"] == [EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID]
    assert phase20_6["mode_specific_bank_used"] is False
    assert phase20_6["case_specific_route_used"] is False
    assert phase20_6["c_d_specific_runtime_cue_used"] is False
    assert phase20_6["completed_reply_template_used"] is False
    assert phase20_6["raw_input_included"] is False
    assert "見えたこと：" in realization.two_stage_comment_text
    assert "Emlisから：" in realization.two_stage_comment_text


def test_phase20_9_section_surface_plan_uses_generic_relation_ratio_without_legacy_mode_alias() -> None:
    role_plan = {
        "expected_comment_text_shape": "labelled_two_stage_text",
        "section_labels_required": True,
        "resolved_ratio": {"reason": "generic_relation_material"},
        "sections": (
            {"section_id": "observation", "sentence_plan_unit_ids": ("observation_unit",)},
            {"section_id": "reception", "sentence_plan_unit_ids": ("reception_unit",)},
        ),
    }

    surface_plan = build_two_stage_section_surface_plan(role_plan)

    assert surface_plan["reception_mode_id"] == EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID
    assert surface_plan["phase20_9_legacy_dedicated_mode_absent"] is False
    assert surface_plan["phase20_6_generic_sentence_plan_surface_enabled"] is True
    assert surface_plan["phase20_6_mode_specific_completed_surface_bank_used"] is False
    assert surface_plan["ratio_reason"] == "generic_relation_material"
    assert surface_plan["mode_context"]["phase20_6_generic_sentence_surface_expected"] is True
    assert surface_plan["mode_context"]["phase20_9_mode_specific_c_d_bank_used"] is False
    assert surface_plan["public_response_key_added"] is False
    assert surface_plan["rn_visible_contract_changed"] is False


def test_phase20_9_section_surface_plan_does_not_translate_removed_phase19_ratio_reasons() -> None:
    role_plan = {
        "two_stage_display_required": True,
        "sections": [
            {"section_id": "observation", "min_sentences": 1, "max_sentences": 1},
            {"section_id": "reception", "min_sentences": 1, "max_sentences": 2},
        ],
    }
    removed_ratio_reasons = ("removed_phase19_c_ratio", "removed_phase19_d_ratio")
    for removed_ratio_reason in removed_ratio_reasons:
        plan = build_two_stage_section_surface_plan(
            role_plan,
            {"ratio_policy": {"resolved_ratio": {"reason": removed_ratio_reason}}},
            {},
        )

        assert plan["reception_mode_id"] == "standard_state_answer"
        assert plan["ratio_reason"] == removed_ratio_reason
        assert plan["phase20_9_legacy_dedicated_mode_absent"] is False
        assert plan["mode_context"]["phase20_6_generic_sentence_surface_expected"] is False
        assert plan["phase20_6_mode_specific_completed_surface_bank_used"] is False
        assert plan["comment_text_generated"] is False

    generic_plan = build_two_stage_section_surface_plan(
        role_plan,
        {"ratio_policy": {"resolved_ratio": {"reason": "generic_relation_material"}}},
        {},
    )
    assert generic_plan["reception_mode_id"] == EMLIS_TWO_STAGE_GENERIC_SENTENCE_PLAN_SURFACE_MODE_ID
    assert generic_plan["mode_context"]["phase20_6_generic_sentence_surface_expected"] is True
    dumped = json.dumps(generic_plan, ensure_ascii=False)
    assert "removed_phase19_c_ratio" not in dumped
    assert "removed_phase19_d_ratio" not in dumped
