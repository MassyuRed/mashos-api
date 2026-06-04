# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_product_quality_contract_freeze import (
    PRODUCT_QUALITY_CONTRACT_FREEZE_VERSION,
    RN_EMLIS_OBSERVATION_TITLE,
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
    dump_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_readfeel_scorecard import build_product_readfeel_scorecard
from emlis_ai_product_readfeel_long_run_product_gate import build_product_readfeel_long_run_product_gate
from emlis_ai_runtime_surface_blind_qa_long_run import build_runtime_surface_blind_qa_long_run_report
from emlis_ai_user_label_connection_product_quality_qa import build_user_label_connection_product_quality_qa_summary
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)

SECRET_RAW_INPUT = "phase0 raw input must not leak"
SECRET_COMMENT = "phase0 comment body must not leak"
VISIBLE_COMMENT = "Phase0 visible comment text is carried only by input_feedback.comment_text."


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_emlis_ai_product_quality_phase0_contract_freeze_fixes_rn_api_db_and_release_boundaries() -> None:
    freeze = build_emlis_ai_product_quality_contract_freeze()

    assert freeze["schema_version"] == PRODUCT_QUALITY_CONTRACT_FREEZE_VERSION
    assert freeze["contract_frozen"] is True
    assert freeze["measurement_connection_only"] is True
    assert freeze["runtime_behavior_changed"] is False

    contract = freeze["contract_assertions"]
    assert contract["api_route_changed"] is False
    assert contract["response_shape_changed"] is False
    assert contract["public_response_key_added"] is False
    assert contract["db_physical_name_changed"] is False
    assert contract["rn_visible_contract_changed"] is False
    assert contract["rn_visible_title_changed"] is False
    assert contract["display_gate_relaxed"] is False
    assert contract["grounding_gate_relaxed"] is False
    assert contract["template_gate_relaxed"] is False

    rn_contract = freeze["rn_display_contract"]
    assert rn_contract["title"] == RN_EMLIS_OBSERVATION_TITLE
    assert rn_contract["requires_observation_status"] == "passed"
    assert rn_contract["requires_comment_text_non_empty"] is True
    assert rn_contract["meta_only_passed_does_not_display"] is True
    assert rn_contract["contract_change_allowed"] is False

    product_material = freeze["product_quality_material_contract"]
    assert product_material["meta_only"] is True
    assert product_material["product_gate_ready"] is False
    assert product_material["public_release_applied"] is False
    assert product_material["release_judgment_deferred"] is True
    assert product_material["machine_metrics_used_for_read_feeling"] is False
    assert product_material["read_feeling_auto_filled_from_machine_metrics"] is False

    assert freeze["product_gate_ready"] is False
    assert freeze["public_release_applied"] is False
    assert freeze["raw_input_included"] is False
    assert freeze["comment_text_body_included"] is False


def test_emlis_ai_product_quality_phase0_contract_freeze_is_meta_only_and_rejects_body_or_release_flags() -> None:
    freeze = build_emlis_ai_product_quality_contract_freeze()
    dumped = dump_emlis_ai_product_quality_contract_freeze(freeze)
    assert "phase0 raw input" not in dumped
    assert "phase0 comment body" not in dumped

    parsed = json.loads(dumped)
    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False

    unsafe_body = dict(freeze)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(unsafe_body)

    unsafe_release = dict(freeze)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_emlis_ai_product_quality_contract_freeze_meta_only(unsafe_release)


def test_emlis_ai_public_boundary_does_not_include_body_payloads_and_requires_public_comment_text_and_passed_status() -> None:
    internal_meta = {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "passed",
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": "passed",
            "comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
        },
        "runtime_surface_pre_return_gate": {
            "passed": True,
            "action": "pass",
            "comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
        },
        "comment_text": SECRET_COMMENT,
        "raw_input": SECRET_RAW_INPUT,
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    public_dump = _dump(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert SECRET_RAW_INPUT not in public_dump
    assert SECRET_COMMENT not in public_dump
    assert "\"comment_text\":" not in public_dump
    assert "\"raw_input\":" not in public_dump
    assert should_include_public_input_feedback(VISIBLE_COMMENT, public_meta) is True
    assert should_include_public_input_feedback("", public_meta) is False
    assert should_include_public_input_feedback(VISIBLE_COMMENT, {"observation_status": "rejected"}) is False
    assert should_include_public_input_feedback(VISIBLE_COMMENT, None) is False


def test_emlis_ai_product_materials_never_set_product_gate_ready_or_public_release() -> None:
    scorecard = build_product_readfeel_scorecard(events=[], blind_qa_reviews=[], run_id="phase0-contract-freeze")
    phase11 = build_product_readfeel_long_run_product_gate(
        events=[],
        product_readfeel_scorecard=scorecard,
    )
    runtime_blind_qa = build_runtime_surface_blind_qa_long_run_report(
        events=[],
        blind_qa_reviews=[],
        run_id="phase0-contract-freeze",
    )
    user_label_qa = build_user_label_connection_product_quality_qa_summary(
        events=[],
        blind_qa_reviews=[],
        run_id="phase0-contract-freeze",
    )

    for material in (scorecard, phase11, runtime_blind_qa, user_label_qa):
        assert material["product_gate_ready"] is False
        assert material["public_release_applied"] is False
        assert material.get("product_gate_public_release_applied") is not True
        assert material.get("raw_input_included", False) is False
        assert material.get("comment_text_body_included", False) is False
        assert "\"comment_text\":" not in _dump(material)
