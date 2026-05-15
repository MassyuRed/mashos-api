from __future__ import annotations

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_sentence_quality_guard import judge_limited_sentence_quality
from emlis_ai_template_echo_guard import guard_template_echo


def _step_payload(evidence):
    ids = [str(item.get("span_id") or "") for item in evidence if str(item.get("span_id") or "")]
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {"display_name_call": "Mashさん", "greeting_text": "Emlisです"},
        "observation_graph": {
            "primary_state": {
                "claim_id": "c1",
                "claim_type": "primary_state",
                "text": "source anchored",
                "evidence_span_ids": ids,
            },
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


def _ledger():
    return build_evidence_ledger(
        {
            "id": "step13-surface-guard",
            "created_at": "2026-05-14T00:00:00Z",
            "memo": "家にいると少し整う。現実に戻ると苦しくなる。普通に生活したい。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        }
    )


def _limited_kwargs():
    return {
        "composer_source": "ai_generated",
        "composer_model": "cocolon_limited_composer.v1",
        "generation_method": "scoped_graph_evidence_composer",
        "generation_scope": "scoped_graph_only",
    }


def test_step13_surface_realizer_meta_records_guarded_surface_policy():
    evidence = [
        {"span_id": "sr1", "raw_text": "朝から疲れが溜まっていて、予定も詰まっていて頭が回らない。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr2", "raw_text": "本当は大事にしたい作業を選びたいけれど、休みたい気持ちも強い。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "sr3", "raw_text": "少しだけ机を整えてお茶を飲んだら、少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
    ]
    result = CocolonLimitedComposerClient().generate(_step_payload(evidence))

    surface = result["composer_meta"]["step13_surface_realizer"]
    assert result["composer_source"] == "ai_generated"
    assert surface["version"] == "emlis.surface_realizer.v1"
    assert surface["target_step"] == "Step13_surface_realizer"
    assert surface["grammar_parts_only"] is True
    assert surface["completion_sentence_templates_added"] is False
    assert surface["fixed_observation_sentence_added"] is False
    assert surface["fixed_closing_sentence_added"] is False
    assert surface["generic_closing_added"] is False
    assert surface["claim_relation_derived_tail_only"] is True
    assert surface["raw_evidence_sentence_copy_guarded"] is True
    assert surface["unfinished_phrase_guarded"] is True
    assert surface["repeated_sentence_tail_guarded"] is True
    assert surface["generic_closing_guarded"] is True
    assert surface["length_mode"] in {"short", "medium", "long"}
    assert surface["unique_tail_key_count"] == len(set(surface["used_tail_keys"]))
    assert "一緒に見ます" not in result["comment_text"]
    assert "そこには" not in result["comment_text"]


def test_step13_quality_guard_rejects_generic_closing_sentence():
    evidence = _ledger()
    text = (
        "Mashさん、Emlisです。\n"
        "家にいると少し整う感覚が表に出ています。\n"
        "Emlisは、急いで片づけず、今の言葉として一緒に見ます。"
    )

    report = judge_limited_sentence_quality(
        comment_text=text,
        evidence_spans=evidence,
        composer_meta={"limited_composer": True, "profile_key": "current_input_core"},
    )

    assert report["passed"] is False
    assert "phase8_generic_closing" in report["rejection_reasons"]


def test_step13_template_guard_reports_generic_closing_for_limited_composer():
    evidence = _ledger()
    text = (
        "Mashさん、Emlisです。\n"
        "家にいると少し整う感覚が表に出ています。\n"
        "Emlisは、急いで片づけず、今の言葉として一緒に見ます。"
    )

    report = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_meta={"limited_composer": True, "profile_key": "current_input_core"},
        **_limited_kwargs(),
    )

    assert report.passed is False
    assert "phase8_generic_closing" in report.rejection_reasons
    assert "limited_composer_generic_closing" in report.rejection_reasons
