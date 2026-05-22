from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from emlis_ai_complete_composer_initial_meta import COMPLETE_COMPOSER_INITIAL_MODEL
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_complete_product_quality_measurement_connection import normalize_observation_row_to_product_quality_event
from emlis_ai_complete_reply_diagnostics_service import build_complete_reply_service_diagnostics
from emlis_ai_complete_surface_quality_signature import (
    SURFACE_QUALITY_SIGNATURE_VERSION,
    SurfaceQualitySignatureError,
    assert_surface_quality_signature_meta_only,
    build_surface_quality_signature,
    dump_surface_quality_signature,
    normalize_surface_signature_to_scorecard_event,
)
from emlis_ai_runtime_surface_source_lock import build_runtime_surface_source_lock

_TEMPLATE_LIKE_TEXT = (
    "Emlisです。\n"
    "体調を整えることが中心にあります。\n"
    "その中でも、お仕事頑張ってお金を貯めて今後一人暮らしをすることも見えています。\n"
    "その中でも、だいぶ先になることも重なっています。"
)
_GRAMMAR_RISK_TEXT = (
    "Emlisです。\n"
    "最近仲良くなった男の人にはなんて事ない日を大切にしてもらえることが中心にあります。\n"
    "その中でも、だからこそ私から離れことも見えています。\n"
    "同じ時間の中に重なっていることも残っています。"
)


def _complete_candidate() -> dict:
    return {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
        "coverage_scope": "short_daily",
        "used_evidence_span_ids": ["ev-1"],
        "used_relation_ids": ["rel-1"],
        "composer_meta": {
            "complete_composer_client_added": True,
            "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
            "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
            "coverage_group": "short_daily",
            "sentence_plan": {"version": "sentence_plan.step2.test"},
            "surface_realizer": {"version": "surface_realizer.step2.test"},
            "tone_policy": {"version": "tone_policy.step2.test"},
            "self_repair": {"version": "self_repair.step2.test", "ready": True},
            "used_phrase_unit_ids": ["ph-1"],
            "relation_types": ["coexistence"],
            "grounding_input": {"binding_count": 1},
        },
    }


def test_step2_surface_signature_detects_screenshot_like_template_backbone_without_text_body() -> None:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)

    assert signature["schema_version"] == SURFACE_QUALITY_SIGNATURE_VERSION
    assert signature["line_count"] == 4
    assert signature["body_sentence_count"] == 3
    assert signature["line_role_sequence"][0] == "greeting"
    assert signature["opening_family_key"] == "center_phrase"
    assert signature["connector_key_sequence"] == ["none", "none", "sono_nakademo", "sono_nakademo"]
    assert signature["predicate_key_sequence"][1] == "center"
    assert signature["generic_center_phrase_count"] == 1
    assert signature["same_connector_run_max"] == 2
    assert signature["same_ending_family_count"] >= 3
    assert signature["template_major"] is True
    assert "same_connector_run" in signature["template_major_reasons"]
    assert signature["comment_text_body_included"] is False
    assert signature["raw_text_included"] is False

    dumped = dump_surface_quality_signature(signature)
    assert _TEMPLATE_LIKE_TEXT not in dumped
    assert "体調を整える" not in dumped
    assert '"comment_text":' not in dumped


def test_step2_surface_signature_detects_malformed_nominalization_as_grammar_warning() -> None:
    signature = build_surface_quality_signature(comment_text=_GRAMMAR_RISK_TEXT)

    assert signature["malformed_nominalization_risk"] is True
    assert "stem_koto_hanareru" in signature["grammar_warning_codes"]
    assert signature["grammar_warning_count"] >= 1
    assert signature["template_major"] is True
    assert signature["raw_input_included"] is False
    assert signature["comment_text_body_included"] is False


def test_step2_surface_signature_does_not_overcollapse_different_natural_shapes() -> None:
    pressure_text = (
        "Emlisです。\n"
        "まず、疲れの蓄積が前面にあります。\n"
        "同時に、小さな回復も少し戻ってきています。\n"
        "最後は、安心できる場所が背景として支えています。"
    )
    relation_text = (
        "Emlisです。\n"
        "はじめに、近づきたい気持ちが前に出ています。\n"
        "一方で、負担になる怖さも同じ場所に残っています。\n"
        "締めでは、距離感の揺れが境目として残っています。"
    )

    pressure = build_surface_quality_signature(comment_text=pressure_text)
    relation = build_surface_quality_signature(comment_text=relation_text)

    assert pressure["surface_signature_id"] != relation["surface_signature_id"]
    assert pressure["template_major"] is False
    assert relation["template_major"] is False
    assert pressure["connector_key_sequence"] != relation["connector_key_sequence"]


def test_step2_reply_diagnostics_carries_signature_id_and_keeps_public_text_out() -> None:
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_complete_candidate(),
        display_decision=SimpleNamespace(
            observation_status="passed",
            rejection_reasons=[],
            comment_text=_TEMPLATE_LIKE_TEXT,
        ),
        gate_trace={"reader": {"passed": True}},
        resolution_meta={"requested_composer": "complete_initial", "source": "complete_composer_registry"},
        diagnostic_summary={"trace_id": "trace-step2", "emotion_log_id": "emotion-step2", "coverage_group": "short_daily"},
    )

    signature = diagnostics["surface_quality_signature"]
    source_lock = diagnostics["runtime_surface_source_lock"]
    assert diagnostics["step2_surface_quality_signature_ready"] is True
    assert signature["template_major"] is True
    assert source_lock["surface_signature_id"] == signature["surface_signature_id"]
    assert diagnostics["scorecard_event"]["surface_signature_id"] == signature["surface_signature_id"]

    dumped = json.dumps(diagnostics, ensure_ascii=False)
    assert _TEMPLATE_LIKE_TEXT not in dumped
    assert "体調を整える" not in dumped
    assert '"comment_text":' not in dumped


def test_step2_measurement_connection_accepts_prebuilt_signature_meta_without_comment_body() -> None:
    signature = build_surface_quality_signature(comment_text=_GRAMMAR_RISK_TEXT)
    source_lock = build_runtime_surface_source_lock(
        trace_id="trace-row-step2",
        emotion_log_id="emotion-row-step2",
        observation_status="passed",
        backend_comment_text_length=120,
        display_confirmed=True,
        coverage_group="relationship",
        resolution_meta={"requested_composer": "complete_initial", "complete_initial_client_used": True},
        runtime_meta={"surface_quality_signature": signature, "surface_realizer_version": "surface.step2.row"},
    )
    row = {
        "trace_id": "trace-row-step2",
        "emotion_log_id": "emotion-row-step2",
        "coverage_group": "relationship",
        "backend_status": "passed",
        "backend_len": 120,
        "backend_comment_text_present": True,
        "backend_public_passed": True,
        "frontend_joined": True,
        "modal_opened": True,
        "display_confirmed": True,
        "classification": "passed_displayed",
        "measurement_classification": "passed_displayed",
        "diagnostic_capture_status": "captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured",
        "candidate_generated": True,
        "binding_supported_sentence_count": 1,
        "expected_binding_count": 1,
        "runtime_surface_source_lock": source_lock,
        "surface_quality_signature": signature,
        "raw_input_included": False,
        "comment_text_included": False,
    }

    event = normalize_observation_row_to_product_quality_event(row)

    assert event["surface_quality_signature_ready"] is True
    assert event["step2_surface_quality_signature_ready"] is True
    assert event["surface_signature_id"] == signature["surface_signature_id"]
    assert event["runtime_surface_source_lock"]["surface_signature_id"] == signature["surface_signature_id"]
    assert event["surface_malformed_nominalization_risk"] is True
    assert "stem_koto_hanareru" in event["surface_grammar_warning_codes"]

    dumped = json.dumps(event, ensure_ascii=False)
    assert _GRAMMAR_RISK_TEXT not in dumped
    assert "離れこと" not in dumped
    assert '"comment_text":' not in dumped


def test_step2_surface_signature_event_fields_and_guard_reject_text_payload_keys() -> None:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    fields = normalize_surface_signature_to_scorecard_event(signature)

    assert fields["surface_quality_signature_ready"] is True
    assert fields["surface_template_major"] is True
    assert fields["surface_signature_id"] == signature["surface_signature_id"]

    unsafe = dict(signature)
    unsafe["comment_text"] = _TEMPLATE_LIKE_TEXT
    with pytest.raises(SurfaceQualitySignatureError):
        assert_surface_quality_signature_meta_only(unsafe)
