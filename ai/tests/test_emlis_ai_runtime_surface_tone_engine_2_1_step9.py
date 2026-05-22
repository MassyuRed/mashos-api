# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from emlis_ai_complete_product_quality_scorecard_service import build_complete_product_quality_scorecard
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from emlis_ai_complete_tone_policy import build_complete_tone_policy_contract_meta
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_runtime_surface_tone_engine_2_1 import (
    RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION,
    assert_runtime_surface_tone_engine_2_1_meta_only,
    build_runtime_surface_tone_engine_2_1_report,
    normalize_tone_engine_2_1_to_scorecard_event,
)


def _contains_key(value: Any, key_name: str) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) == key_name or _contains_key(item, key_name) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_key(item, key_name) for item in value)
    return False


def _relationship_seed() -> dict[str, Any]:
    return {
        "coverage_group": "relationship",
        "sentence_budget": 3,
        "graph_nodes": [
            {
                "node_id": "n1",
                "material_id": "m1",
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "role": "relation_distance",
                "relation_type": "coexistence",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n2",
                "material_id": "m2",
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s2",
                "role": "residue",
                "relation_type": "residue",
                "source_anchor_present": True,
            },
        ],
    }


def test_step9_tone_engine_detects_diagnosis_advice_overcomfort_without_text_payload() -> None:
    report = build_runtime_surface_tone_engine_2_1_report(
        comment_text="Emlisです。\n診断として、まずは行動しましょう。\nつらかったね、もう大丈夫です。"
    )

    assert report["tone_engine_2_1_version"] == RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION
    assert report["step9_tone_engine_2_1_ready"] is True
    assert report["tone_guard_major_count"] >= 3
    assert report["tone_safety_major_count"] >= 1
    assert report["tone_distance_major_count"] >= 1
    assert "diagnostic_tone" in report["tone_guard_reasons"]
    assert "advice_like" in report["tone_guard_reasons"]
    assert report["machine_metrics_used_for_read_feeling"] is False
    assert report["read_feeling_auto_filled_from_machine_metrics"] is False
    assert report["read_feeling_score"] is None
    assert report["comment_text_body_included"] is False
    assert not _contains_key(report, "comment_text")
    assert not _contains_key(report, "surface_text")
    assert_runtime_surface_tone_engine_2_1_meta_only(report)

    event = normalize_tone_engine_2_1_to_scorecard_event(report)
    assert event["tone_engine_2_1_major_count"] >= 3
    assert event["tone_guard_passed"] is False
    assert event["read_feeling_requires_blind_qa"] is True
    assert event["machine_metrics_used_for_read_feeling"] is False


def test_step9_tone_policy_contract_keeps_blind_qa_separate_and_does_not_relax_gate() -> None:
    meta = build_complete_tone_policy_contract_meta()

    assert meta["tone_engine_2_1_added"] is True
    assert meta["step9_tone_engine_2_1_ready"] is True
    assert meta["blind_qa_required_for_tone_completion"] is True
    assert meta["machine_metrics_used_for_read_feeling"] is False
    assert meta["read_feeling_auto_filled_from_machine_metrics"] is False
    assert meta["tone_engine_2_1_relaxes_gate"] is False
    assert meta["tone_engine_2_1_uses_fixture_strings"] is False
    assert meta["fixed_sentence_template_added_by_tone"] is False
    assert meta["input_specific_tone_branch_added"] is False
    assert meta["meaning_added_by_tone_engine_2_1"] is False


def test_step9_complete_surface_realizer_carries_tone_engine_2_1_meta_without_machine_read_feeling() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    meta = realization.as_meta(include_realized_text=False)

    assert meta["step9_tone_engine_2_1_ready"] is True
    assert meta["tone_engine_2_1_version"] == RUNTIME_SURFACE_TONE_ENGINE_2_1_VERSION
    assert meta["tone_guard_major_count"] == 0
    assert meta["tone_engine_2_1_report"]["tone_guard_major_count"] == 0
    assert meta["tone_completion_requires_blind_qa"] is True
    assert meta["machine_metrics_used_for_read_feeling"] is False
    assert meta["read_feeling_auto_filled_from_machine_metrics"] is False
    assert "realized_text" not in meta
    assert not _contains_key(meta["tone_engine_2_1_report"], "comment_text")
    assert not _contains_key(meta["tone_engine_2_1_report"], "surface_text")


def test_step9_scorecard_connects_tone_metrics_but_does_not_auto_score_read_feeling() -> None:
    report = build_runtime_surface_tone_engine_2_1_report(
        comment_text="Emlisです。\n診断として、まずは行動しましょう。\nここに置かれた言葉を、Emlisは軽く扱いません。"
    )
    scorecard = build_complete_product_quality_scorecard(
        scorecard_events=[
            {
                "coverage_group": "short_daily",
                "observation_status": "passed",
                "eligible_count": 1,
                "passed_display_count": 1,
                "binding_supported_sentence_count": 1,
                "expected_binding_count": 1,
                "tone_engine_2_1_report": report,
                "top_rejection_reasons": report["blocker_reasons"],
            }
        ]
    )

    assert scorecard["step9_tone_engine_2_1_connected"] is True
    assert scorecard["tone_engine_2_1_major_count"] >= 1
    assert scorecard["tone_safety_major_count"] >= 1
    assert scorecard["safety_major_count"] >= 1
    assert scorecard["read_feeling_score"] is None
    assert scorecard["read_feeling_source"] == "blind_qa_required_not_evaluated"
    assert scorecard["machine_metrics_used_for_read_feeling"] is False
    assert "safety_major_detected" in scorecard["release_blockers"]


def test_step9_final_review_blocks_tone_engine_2_1_risks_without_repairing_text() -> None:
    result = review_emlis_ai_reply_text(
        comment_text="Emlisです。\n診断として、まずは行動しましょう。\nここに置かれた言葉を、Emlisは軽く扱いません。"
    )

    assert result.passed is False
    assert result.repaired_text is None
    codes = [issue.code for issue in result.issues]
    assert any(code.startswith("tone_engine_2_1_diagnostic_tone") for code in codes)
    assert any(code.startswith("tone_engine_2_1_advice_like") for code in codes)
