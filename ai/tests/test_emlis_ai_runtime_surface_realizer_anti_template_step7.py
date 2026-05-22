from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP,
    COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION,
    build_complete_surface_realization_v2,
    build_complete_surface_realizer_contract_meta,
    build_complete_surface_realizer_v2_meta,
)
from emlis_ai_complete_surface_realizer_anti_template import (
    assert_surface_realizer_anti_template_meta_only,
    build_surface_realizer_anti_template_report,
)
from emlis_ai_relation_surface_contract import detect_relation_surface, relation_marker_phrase


def _center_seed() -> dict[str, Any]:
    return {
        "coverage_group": "short_daily",
        "sentence_budget": 2,
        "graph_nodes": [
            {
                "node_id": "n-center",
                "material_id": "m-center",
                "phrase_unit_id": "pu-center",
                "evidence_span_id": "span-center",
                "role": "primary_phrase",
                "relation_type": "center",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n-current",
                "material_id": "m-current",
                "phrase_unit_id": "pu-current",
                "evidence_span_id": "span-current",
                "role": "current_expression",
                "relation_type": "center",
                "source_anchor_present": True,
            },
        ],
    }


def _mixed_seed() -> dict[str, Any]:
    return {
        "coverage_group": "long_meaning_arc",
        "sentence_budget": 4,
        "graph_nodes": [
            {"node_id": "n1", "material_id": "m1", "phrase_unit_id": "pu1", "evidence_span_id": "s1", "role": "fatigue_accumulation", "relation_type": "pressure", "must_keep": True, "source_anchor_present": True},
            {"node_id": "n2", "material_id": "m2", "phrase_unit_id": "pu2", "evidence_span_id": "s2", "role": "value_wish", "relation_type": "contrast", "source_anchor_present": True},
            {"node_id": "n3", "material_id": "m3", "phrase_unit_id": "pu3", "evidence_span_id": "s3", "role": "small_repair", "relation_type": "recovery", "source_anchor_present": True},
            {"node_id": "n4", "material_id": "m4", "phrase_unit_id": "pu4", "evidence_span_id": "s4", "role": "hurt_core", "relation_type": "residue", "source_anchor_present": True},
        ],
    }


def test_step7_surface_realizer_anti_template_contract_is_additive() -> None:
    meta = build_complete_surface_realizer_contract_meta()

    assert meta["version"] == "emlis.complete_surface_realizer.v2_1"
    assert meta["surface_realizer_2_1_anti_template_version"] == COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION
    assert meta["surface_realizer_2_1_anti_template_step"] == COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP
    assert meta["surface_realizer_2_1_anti_template_added"] is True
    assert meta["generic_center_opening_policy_enabled"] is True
    assert meta["same_connector_consecutive_guard_enabled"] is True
    assert meta["predicate_family_stack_guard_enabled"] is True
    assert meta["relation_line_forced_for_all_inputs"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["surface_realizer_anti_template_relaxes_gate"] is False
    assert meta["surface_realizer_anti_template_adds_fixed_sentence_templates"] is False
    assert meta["input_specific_surface_branch_added"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["raw_input_included"] is False
    assert_surface_realizer_anti_template_meta_only(meta["surface_realizer_anti_template_policy"])


def test_step7_center_opening_does_not_emit_generic_center_backbone() -> None:
    meta = build_complete_surface_realizer_v2_meta(sentence_plan_seed=_center_seed())

    assert meta["status"] == "ready"
    assert meta["ready"] is True
    assert "中心にあります" not in meta["realized_text"]
    assert "中心にある感覚" not in meta["realized_text"]
    assert "その中でも" not in meta["realized_text"]
    assert meta["surface_anti_template_guard_passed"] is True
    assert meta["surface_anti_template_report"]["generic_center_opening_count"] == 0
    assert meta["surface_anti_template_report"]["same_connector_key_run_max"] <= 1
    assert "center_core" not in meta["predicate_keys"]
    assert meta["completion_sentence_template_used"] is False
    assert meta["input_specific_template_used"] is False
    assert meta["response_shape_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["raw_input_included"] is False


def test_step7_mixed_surface_distributes_connector_predicate_and_ending_families() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_mixed_seed())
    report = realization.surface_anti_template_report

    assert realization.ready is True
    assert report["anti_template_major_detected"] is False
    assert report["generic_center_opening_count"] == 0
    assert report["same_connector_key_run_max"] <= 1
    assert report["same_predicate_family_count"] <= 2
    assert report["same_ending_family_count"] <= 2
    assert "その中でも" not in realization.realized_text
    assert "同じ時間の中" not in realization.realized_text
    assert "中心にあります" not in realization.realized_text


def test_step7_anti_template_report_catches_old_backbone_without_text_payload() -> None:
    rows = [
        {"sentence_id": "s1", "line_role": "opening", "connector_key": "none", "predicate_key": "center_core", "ending_key": "aru", "role_phrase_key": "primary_phrase"},
        {"sentence_id": "s2", "line_role": "core", "connector_key": "core_inside", "predicate_key": "visible_reply", "ending_key": "teimasu", "role_phrase_key": "current_expression"},
        {"sentence_id": "s3", "line_role": "core", "connector_key": "core_inside", "predicate_key": "visible_other", "ending_key": "teimasu", "role_phrase_key": "current_expression"},
    ]

    report = build_surface_realizer_anti_template_report(rows)

    assert report["generic_center_opening_count"] == 1
    assert report["same_connector_key_run_max"] == 2
    assert report["anti_template_major_detected"] is True
    assert "generic_center_opening" in report["anti_template_major_reasons"]
    assert "same_connector_key_run" in report["anti_template_major_reasons"]
    assert report["completion_sentence_template_used"] is False
    assert report["raw_input_included"] is False
    assert report["comment_text_body_included"] is False
    with pytest.raises(ValueError):
        unsafe = dict(report)
        unsafe["surface_text"] = "本文を入れてはいけない"
        assert_surface_realizer_anti_template_meta_only(unsafe)


def test_step7_coexistence_relation_marker_does_not_use_same_time_template() -> None:
    phrase = relation_marker_phrase("coexistence")
    signal = detect_relation_surface(phrase, expected_relation_types=("coexistence",))

    assert "同じ時間の中" not in phrase
    assert signal["reader_relation_signal_detected"] is True
    assert "coexistence" in signal["reader_relation_signal_relation_types"]
    assert signal["raw_input_included"] is False
