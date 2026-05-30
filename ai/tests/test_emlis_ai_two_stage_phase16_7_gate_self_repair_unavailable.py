# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_complete_self_repair_service import run_complete_self_repair_loop
from emlis_ai_complete_surface_realizer import CompleteSurfaceLineV2, CompleteSurfaceRealizationV2, build_complete_surface_realization_v2
from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
from emlis_ai_two_stage_reception_gate import build_two_stage_reception_gate_report
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report
from test_emlis_ai_complete_sentence_plan_two_stage_section_meta import _seed, _two_stage_plan
from test_emlis_ai_two_stage_required_gate_connection import (
    A_CURRENT_INPUT,
    REQUIRED_COMPOSER_META,
    UNLABELLED_COMPLETE_SURFACE,
    _assert_meta_only,
)
from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2


PHASE16_7_LABEL_REASON_CODES = {
    "two_stage_required_but_unrealized",
    "two_stage_complete_surface_realizer_label_missing",
    "two_stage_complete_surface_blocked_by_gate",
}


def test_phase16_7_two_stage_gate_reports_required_unrealized_label_missing_reason_codes() -> None:
    report = build_two_stage_reception_gate_report(
        visible_surface=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=REQUIRED_COMPOSER_META,
    )

    assert report["passed"] is False
    assert PHASE16_7_LABEL_REASON_CODES.issubset(set(report["rejection_reasons"]))
    assert PHASE16_7_LABEL_REASON_CODES.issubset(set(report["two_stage_unavailable_reason_codes"]))
    assert report["two_stage_required_but_unrealized"] is True
    assert report["two_stage_complete_surface_realizer_label_missing"] is True
    assert report["two_stage_complete_surface_blocked_by_gate"] is True
    assert report["display_gate_relaxed"] is False
    _assert_meta_only(report)


def test_phase16_7_visible_and_state_gates_propagate_unavailable_reason_codes_without_body() -> None:
    visible = build_visible_surface_acceptance_gate_report(
        comment_text=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=REQUIRED_COMPOSER_META,
        rerender_allowed=False,
    )
    state = build_state_answer_gate_boundary_report(
        visible_surface=UNLABELLED_COMPLETE_SURFACE,
        current_input=A_CURRENT_INPUT,
        composer_meta=REQUIRED_COMPOSER_META,
    )

    for report in (visible, state):
        assert report["passed"] is False
        assert PHASE16_7_LABEL_REASON_CODES.issubset(set(report["rejection_reasons"]))
        assert PHASE16_7_LABEL_REASON_CODES.issubset(set(report["two_stage_unavailable_reason_codes"]))
        assert report["two_stage_required_but_unrealized"] is True
        assert report["two_stage_complete_surface_blocked_by_gate"] is True
        assert report["display_gate_relaxed"] is False
        _assert_meta_only(report)


def _single_line_realization_without_two_stage_meta() -> CompleteSurfaceRealizationV2:
    line = CompleteSurfaceLineV2(
        sentence_id="line_without_section_meta",
        line_role="core",
        relation_type="center",
        surface_text="根拠のある範囲で短く置きます。",
        phrase_unit_ids=("pu_probe",),
        evidence_span_ids=("ev_probe",),
        predicate_key="probe_predicate",
        surface_signature={"signature_id": "probe"},
        source_sentence_plan_line={
            "sentence_id": "line_without_section_meta",
            "line_role": "core",
            "relation_type": "center",
            "phrase_unit_ids": ["pu_probe"],
            "evidence_span_ids": ["ev_probe"],
            "meta": {},
        },
        meta={},
    )
    return CompleteSurfaceRealizationV2(
        plan_id="surface_without_two_stage_meta",
        coverage_group="phase16_7_probe",
        surface_lines=(line,),
        meta={"source": "phase16_7_test", "raw_input_included": False},
    )


def test_phase16_7_self_repair_fails_closed_when_section_meta_is_missing() -> None:
    realization = _single_line_realization_without_two_stage_meta()

    result = run_complete_self_repair_loop(
        surface_realization=realization,
        gate_reasons=["two_stage_label_missing"],
        max_attempts=1,
    )

    assert result.aborted is True
    assert "two_stage_complete_surface_realizer_label_missing" in result.gate_reasons
    assert "two_stage_section_meta_missing_fail_closed" in result.rejection_reasons
    meta = result.as_meta(include_realized_text=False)
    assert meta["display_gate_relaxed"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["raw_input_included"] is False
    assert "realized_text" not in meta


def test_phase16_7_self_repair_can_rebuild_labels_from_existing_section_meta_without_fixed_body() -> None:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )
    realization = build_complete_surface_realization_v2(sentence_plan=sentence_plan)

    result = run_complete_self_repair_loop(
        surface_realization=realization,
        gate_reasons=["two_stage_label_missing"],
        max_attempts=1,
    )

    assert result.repaired is True
    assert result.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in result.comment_text
    meta = result.as_meta(include_realized_text=False)
    assert meta["display_gate_relaxed"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["raw_input_included"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert "realized_text" not in meta
