from __future__ import annotations

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_surface_realizer import choose_limited_surface_parts
from emlis_ai_template_echo_guard import guard_template_echo


def _payload(evidence):
    ids = [str(item.get("span_id") or "") for item in evidence if str(item.get("span_id") or "")]
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {"display_name_call": "Mashさん", "greeting_text": "Emlisです"},
        "observation_graph": {
            "primary_state": {"claim_id": "c1", "claim_type": "primary_state", "text": "source anchored", "evidence_span_ids": ids},
            "core_tensions": [],
            "pressure_sources": [],
            "limit_signals": [],
            "self_awareness": [],
            "value_or_strength_signals": [],
            "safety_boundaries": [],
            "forbidden_claims": [],
            "missing_information": [],
        },
        "evidence_spans": evidence,
        "limited_observation_scope": {"scope_status": "eligible", "coverage_scope": "partial_observation"},
        "composition_contract": {"forbidden_output_surfaces": []},
    }


def _energy_fatigue_evidence():
    return [
        {"span_id": "sf1", "raw_text": "朝から疲れが溜まっていて、予定も詰まっていて頭が回らない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sf2", "raw_text": "本当は大事にしたい作業を選びたいけれど、休みたい気持ちも強い。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sf3", "raw_text": "少しだけ机を整えてお茶を飲んだら、少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]


def test_step8_limited_surface_realizer_records_relation_component_rows_without_templates() -> None:
    result = CocolonLimitedComposerClient().generate(_payload(_energy_fatigue_evidence()))

    assert result["status"] == "generated"
    meta = result["composer_meta"]
    step8 = meta["step8_limited_surface_realizer_stabilization"]
    diagnostic_step8 = meta["composer_diagnostic"]["step8_limited_surface_realizer_stabilization"]

    assert step8["version"] == "emlis.limited_surface_realizer.stabilization.v1"
    assert step8["target_step"] == "8_limited_surface_realizer_stabilization"
    assert step8["limited_surface_realizer_stabilized"] is True
    assert step8["relation_aware_opener_selection"] is True
    assert step8["relation_aware_particle_selection"] is True
    assert step8["relation_aware_predicate_selection"] is True
    assert step8["tail_variation_by_relation"] is True
    assert step8["completion_sentence_templates_added"] is False
    assert step8["role_based_completed_sentence_added"] is False
    assert step8["input_specific_template_added"] is False
    assert step8["display_gate_relaxed"] is False
    assert step8["raw_text_included"] is False
    assert step8["repeated_tail_keys"] == []
    assert step8["surface_tail_key_count"] == step8["unique_tail_key_count"]
    assert len(step8["surface_component_rows"]) == meta["body_line_count"]
    assert diagnostic_step8["surface_component_row_count"] == meta["body_line_count"]
    for row in step8["surface_component_rows"]:
        assert row["target_step"] == "8_limited_surface_realizer_stabilization"
        assert row["raw_text_included"] is False
        assert row["completion_sentence_template_used"] is False
        assert row["role_completed_sentence_template_used"] is False
        assert row["input_specific_template_used"] is False
        assert row["relation_type"]
        assert row["tail_key"]


def test_step8_surface_selector_prefers_unused_relation_tail_over_generic_written() -> None:
    particle, predicate, key = choose_limited_surface_parts(
        relation_type="pressure",
        line_role="fatigue",
        role_keys=("fatigue_accumulation",),
        polarity="negative",
        current_candidates=(("が", "書かれています", "written"),),
        used_tail_keys=("written",),
    )

    assert (particle, predicate, key) in {
        ("が", "強く残っています", "strong_remain"),
        ("が", "続いています", "continue"),
        ("も", "残っています", "remain"),
        ("も", "見えています", "visible"),
    }
    assert key != "written"


def test_step8_generated_surface_does_not_trigger_limited_template_echo_major_detection() -> None:
    result = CocolonLimitedComposerClient().generate(_payload(_energy_fatigue_evidence()))
    report = guard_template_echo(
        comment_text=result["comment_text"],
        evidence_spans=[],
        composer_meta=result["composer_meta"],
        composer_source=result["composer_source"],
        composer_model=result["composer_model"],
        generation_method=result["generation_method"],
        generation_scope=result["generation_scope"],
        coverage_scope=result["coverage_scope"],
    )

    assert report.passed is True
    assert "limited_composer_repeated_surface_tail" not in report.rejection_reasons
    assert "limited_composer_generic_closing" not in report.rejection_reasons
