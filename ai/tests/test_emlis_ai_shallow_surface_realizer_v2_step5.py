# -*- coding: utf-8 -*-
from __future__ import annotations

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report


def _payload(evidence_spans):
    ids = [str(item.get("span_id") or "") for item in evidence_spans if str(item.get("span_id") or "")]
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {"display_name_call": "Mashさん", "greeting_text": "Emlisです"},
        "observation_graph": {
            "primary_state": {"claim_id": "c1", "claim_type": "primary_state", "text": "source anchored", "evidence_span_ids": ids[:3]},
            "core_tensions": [],
            "pressure_sources": [],
            "limit_signals": [],
            "self_awareness": [],
            "value_or_strength_signals": [],
            "safety_boundaries": [],
            "forbidden_claims": [],
            "missing_information": [],
        },
        "evidence_spans": evidence_spans,
        "limited_observation_scope": {"scope_status": "eligible", "coverage_scope": "partial_observation"},
        "composition_contract": {"forbidden_output_surfaces": []},
    }


def test_step5_shallow_surface_realizer_v2_replaces_old_current_input_core_skeleton() -> None:
    evidence = [
        {"span_id": "sh1", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sh2", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]

    result = CocolonLimitedComposerClient().generate(_payload(evidence))
    text = result["comment_text"]
    meta = result["composer_meta"]
    plan = meta["step5_shallow_surface_realizer_v2"]

    assert result["composer_source"] == "ai_generated"
    assert meta["shallow_v2_used"] is True
    assert meta["shallow_realizer_version"] == "shallow_surface_realizer.v2"
    assert plan["version"] == "emlis.shallow_surface_realizer_plan.v2"
    assert plan["eligible"] is True
    assert plan["old_current_input_core_skeleton_disabled"] is True
    assert plan["center_phrase_disabled"] is True
    assert plan["default_sono_nakademo_disabled"] is True
    assert plan["generic_center_phrase_count"] == 0
    assert plan["same_connector_run_max"] <= 1
    assert {"receive_line", "state_arrangement_line"}.issubset(set(plan["sentence_roles"]))

    assert "中心にあります" not in text
    assert "その中でも" not in text
    assert "も見えています" not in text
    assert "今までこと" not in text
    assert "大丈夫こと" not in text
    assert "先に出ています" in text

    surface_report = build_runtime_surface_pre_return_gate_report(
        comment_text=text,
        composer_meta=meta,
    )
    assert surface_report["passed"] is True
    assert surface_report["generic_center_phrase_count"] == 0
    assert surface_report["surface_template_major"] is False


def test_step5_shallow_surface_realizer_v2_keeps_relation_binding_meta_only() -> None:
    evidence = [
        {"span_id": "sh1", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sh2", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sh3", "raw_text": "それでも資料のことが気になっている。", "detected_type": "event", "source_field": "memo"},
    ]

    result = CocolonLimitedComposerClient().generate(_payload(evidence))
    meta = result["composer_meta"]
    plan = meta["step5_shallow_surface_realizer_v2"]
    bundle = result["sentence_binding_bundle"]

    assert result["composer_source"] == "ai_generated"
    assert plan["relation_bearing_surface"] is True
    assert plan["raw_input_included"] is False
    assert plan["comment_text_body_included"] is False
    assert bundle["profile_key"] == "current_input_core"
    assert all("text" not in row for row in bundle["relation_taxonomy"]["binding_relation_rows"])
    assert set(bundle["used_evidence_span_ids"]).issuperset({"sh1", "sh2"})
    assert "receive_first" in meta["surface_tail_keys"]
    assert "center" not in meta["surface_tail_keys"]
