from __future__ import annotations

from types import SimpleNamespace

import pytest

from emlis_ai_complete_reply_diagnostics_service import (
    build_complete_reply_diagnostics_contract_meta,
    build_complete_reply_service_diagnostics,
)

COMPLETE_MODEL = "cocolon_emlis_observation_composer.a1.v1"
COMPLETE_METHOD = "complete_initial_binding_first_composer"


def _complete_candidate(span_id: str = "e1") -> dict:
    return {
        "schema_version": "emlis.complete_composer.response.v1",
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": COMPLETE_MODEL,
        "generation_method": COMPLETE_METHOD,
        "generation_scope": "scoped_graph_evidence_composer",
        "coverage_scope": "recovery",
        "comment_text": "疲れているけれど、少し整えたい気持ちも同じ場所にある流れとして見ています。",
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
    composer_model = COMPLETE_MODEL

    def generate(self, payload):
        span_id = "e1"
        spans = payload.get("evidence_spans") or []
        if spans:
            span_id = str(spans[0].get("span_id") or span_id)
        return _complete_candidate(span_id=span_id)


def test_step11_contract_meta_keeps_public_response_contract_unchanged() -> None:
    meta = build_complete_reply_diagnostics_contract_meta()

    assert meta["reply_service_integration_added"] is True
    assert meta["diagnostic_summary_integration_added"] is True
    assert meta["repair_trace_connection_added"] is True
    assert meta["scorecard_event_connection_added"] is True
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["comment_text_written_by_step11"] is False
    assert meta["response_shape_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["external_ai_allowed"] is False
    assert meta["local_llm_allowed"] is False
    assert meta["fixed_sentence_template_allowed"] is False
    assert meta["raw_input_included"] is False


def test_step11_diagnostics_connect_complete_meta_repair_trace_and_scorecard_event() -> None:
    display = SimpleNamespace(
        observation_status="passed",
        comment_text="疲れているけれど、少し整えたい気持ちも同じ場所にある流れとして見ています。",
        rejection_reasons=[],
    )
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_complete_candidate(),
        display_decision=display,
        gate_trace={"display_gate": {"passed": True}},
        resolution_meta={"source": "provided", "explicit_client_used": True},
        release_meta={"enabled": True},
        diagnostic_summary={"coverage_group": "recovery", "observation_status": "passed"},
        phase_gate={"comment_text_allowed": True},
        scorecard_harness={"ready": True},
    )

    assert diagnostics["complete_reply_service_diagnostics_added"] is True
    assert diagnostics["complete_reply_service_integrated"] is True
    assert diagnostics["complete_meta_connected"] is True
    assert diagnostics["repair_trace_connected"] is True
    assert diagnostics["repair_trace_count"] == 1
    assert diagnostics["scorecard_event_connected"] is True
    assert diagnostics["scorecard_event"]["scorecard_event_connected"] is True
    assert diagnostics["scorecard_event"]["binding_pass"] is True
    assert diagnostics["complete_runtime_meta"]["raw_input_included"] is False
    assert diagnostics["comment_text_key_written"] is False
    assert diagnostics["response_shape_changed"] is False


@pytest.mark.asyncio
async def test_step11_runtime_meta_is_attached_without_breaking_passed_only_contract(monkeypatch: pytest.MonkeyPatch) -> None:
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
    ):
        monkeypatch.delenv(name, raising=False)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step11-complete-e2e-user",
        subscription_tier="free",
        current_input={
            "id": "step11-complete-e2e-input",
            "created_at": "2026-05-15T00:00:00Z",
            "memo": "疲れているけれど、少し整えたい気持ちもある。",
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
    multi = reply.meta["multi_perspective"]
    phase_gate = multi["phase_gate"]
    step11 = reply.meta["step11_complete_reply_service_diagnostics"]

    assert step11 == diagnostic["step11_complete_reply_service_diagnostics"]
    assert step11 == multi["step11_complete_reply_service_diagnostics"]
    assert step11["complete_reply_service_diagnostics_added"] is True
    assert step11["complete_meta_connected"] is True
    assert step11["scorecard_event_connected"] is True
    assert step11["comment_text_contract"] == "passed_only"
    assert step11["response_shape_changed"] is False
    assert reply.meta["complete_composer_initial_scorecard_event"] == step11["scorecard_event"]
    assert diagnostic["complete_composer_initial_scorecard_event"] == step11["scorecard_event"]
    assert diagnostic["observation_diagnostic_lockdown_ready"] is True
    assert diagnostic["step3_observation_diagnostic_lockdown_ready"] is True
    assert diagnostic["candidate_generated_before_display_gate"] == step11["complete_candidate_generated"]
    assert diagnostic["complete_candidate_generated_before_display_gate"] == step11["complete_candidate_generated"]
    assert diagnostic["observation_diagnostic_lockdown_meta"]["ready"] is True
    assert diagnostic["observation_diagnostic_lockdown_meta"]["trace_id"] == reply.meta["observation_trace_id"]
    assert diagnostic["observation_diagnostic_lockdown_meta"]["candidate_generated_before_display_gate"] == step11["complete_candidate_generated"]
    assert diagnostic["observation_diagnostic_lockdown_meta"]["raw_input_included"] is False
    assert diagnostic["observation_diagnostic_lockdown_meta"]["comment_text_included"] is False
    assert phase_gate["step11_complete_reply_service_diagnostics_ready"] is True
    assert phase_gate["step3_observation_diagnostic_lockdown_ready"] is True
    assert phase_gate["complete_scorecard_event_connected"] is True
    assert phase_gate["complete_response_shape_changed"] is False
    assert reply.comment_text == "" or reply.meta["observation_status"] == "passed"
