from __future__ import annotations

import json

import pytest

from emlis_ai_observation_diagnostic_lockdown import build_observation_diagnostic_lockdown

_COMPLETE_MODEL = "cocolon_emlis_observation_composer.a1.v1"
_COMPLETE_METHOD = "complete_initial_binding_first_composer"
_SECRET_MEMO = "疲れているけれど、少し整えたい気持ちもある。"
_SECRET_COMMENT = "疲れているけれど、少し整えたい気持ちも同じ場所にある流れとして見ています。"


def _clear_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
    ):
        monkeypatch.delenv(name, raising=False)


def _complete_candidate(span_id: str = "e1") -> dict:
    return {
        "schema_version": "emlis.complete_composer.response.v1",
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": _COMPLETE_MODEL,
        "generation_method": _COMPLETE_METHOD,
        "generation_scope": "scoped_graph_evidence_composer",
        "coverage_scope": "recovery",
        "comment_text": _SECRET_COMMENT,
        "used_evidence_span_ids": [span_id],
        "used_claim_ids": ["claim-recovery"],
        "used_relation_ids": ["recovery"],
        "confidence": 0.72,
        "fixed_string_renderer_used": False,
        "composer_meta": {
            "complete_composer_client_added": True,
            "coverage_group": "recovery",
            "coverage_scope": "recovery",
            "used_evidence_span_ids": [span_id],
            "used_phrase_unit_ids": ["phrase-recovery"],
            "used_relation_ids": ["recovery"],
            "relation_types": ["recovery"],
            "sentence_bindings": [
                {
                    "sentence_id": "complete-s1",
                    "used_evidence_span_ids": [span_id],
                    "used_phrase_unit_ids": ["phrase-recovery"],
                    "relation_type": "recovery",
                }
            ],
            "grounding_input": {
                "binding_count": 1,
                "sentence_bindings": [
                    {
                        "sentence_id": "complete-s1",
                        "used_evidence_span_ids": [span_id],
                        "used_phrase_unit_ids": ["phrase-recovery"],
                        "relation_type": "recovery",
                    }
                ],
            },
            "material_service": {"ready": True, "material_count": 1},
            "coverage_plan": {"ready": True, "coverage_group": "recovery"},
            "relation_graph": {"ready": True, "relation_types": ["recovery"]},
            "sentence_plan": {"usable": True, "sentence_budget": 2},
            "surface_realizer": {"ready": True, "surface_signature": ["opening:gentle"]},
            "self_repair": {"ready": True, "repair_attempted": True},
            "repair_trace": [
                {
                    "attempt": 1,
                    "source_gate": "grounding",
                    "reason_code": "relation_not_expressed",
                    "applied_operation": "relation_phrase_insert",
                    "before_plan_id": "plan-before",
                    "after_plan_id": "plan-after",
                    "evidence_ids_unchanged": True,
                    "relation_ids_unchanged": True,
                    "safety_level_unchanged": True,
                    "result": "passed",
                }
            ],
            "external_ai_used": False,
            "local_llm_used": False,
            "fixed_sentence_template_used": False,
            "fallback_observation_sentence_added": False,
            "raw_input_included": False,
        },
    }


class _CompleteMetaComposer:
    composer_model = _COMPLETE_MODEL

    def generate(self, payload):
        span_id = "e1"
        spans = payload.get("evidence_spans") or []
        if spans:
            span_id = str(spans[0].get("span_id") or span_id)
        return _complete_candidate(span_id=span_id)


@pytest.mark.asyncio
async def test_step3_reply_meta_exposes_candidate_gate_repair_for_lockdown_without_text(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_composer_env(monkeypatch)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step3-observation-diagnostic-lockdown-user",
        subscription_tier="free",
        current_input={
            "id": "step3-observation-diagnostic-lockdown-input",
            "created_at": "2026-05-17T00:00:00Z",
            "memo": _SECRET_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_CompleteMetaComposer(),
    )

    diagnostic = reply.meta["diagnostic_summary"]
    lockdown_meta = diagnostic["observation_diagnostic_lockdown"]
    complete = reply.meta["complete_reply_service_diagnostics"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]

    assert diagnostic["observation_diagnostic_lockdown_ready"] is True
    assert diagnostic["candidate_generated_before_display_gate"] is True
    assert diagnostic["complete_candidate_generated_before_display_gate"] is True
    assert diagnostic["gate_results_extractable_for_observation_diagnostic"] is True
    assert diagnostic["repair_extractable_for_observation_diagnostic"] is True
    assert lockdown_meta["ready"] is True
    assert lockdown_meta["candidate_generated_before_display_gate"] is True
    assert lockdown_meta["gate_results_extractable"] is True
    assert lockdown_meta["repair_extractable"] is True
    assert lockdown_meta["raw_input_included"] is False
    assert lockdown_meta["comment_text_included"] is False
    assert complete["candidate_generated_before_display_gate"] is True
    assert complete["complete_candidate_generated_before_display_gate"] is True
    assert phase_gate["observation_diagnostic_lockdown_ready"] is True

    serialized_lockdown_meta = json.dumps(lockdown_meta, ensure_ascii=False, sort_keys=True)
    assert _SECRET_MEMO not in serialized_lockdown_meta
    assert _SECRET_COMMENT not in serialized_lockdown_meta

    record = build_observation_diagnostic_lockdown(
        input_feedback_comment=reply.comment_text,
        input_feedback_meta=reply.meta,
        emotion_log_id="emotion-step3-001",
        created_at="2026-05-17T02:35:05.000000+00:00",
    )

    assert record["candidate"]["generated"] is True
    assert record["candidate"]["generated_before_display_gate"] is True
    assert record["composer_client_resolution"]["connection_status"] == "provided_client"
    assert record["classification"] != "pre_connection_stop"
    assert record["classification"] in {
        "candidate_generated_but_reader_rejected",
        "candidate_generated_but_grounding_rejected",
        "candidate_generated_but_template_rejected",
        "candidate_generated_but_display_rejected",
        "public_feedback_not_included_empty_comment_text",
        "passed_displayed",
    }
    assert record["raw_input_included"] is False
    assert record["comment_text_included"] is False

    serialized_record = json.dumps(record, ensure_ascii=False, sort_keys=True)
    assert _SECRET_MEMO not in serialized_record
    assert _SECRET_COMMENT not in serialized_record
    assert not any(reason.startswith("{") for reason in record["display_rejection_reasons"])
