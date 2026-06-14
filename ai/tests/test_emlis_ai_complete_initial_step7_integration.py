from __future__ import annotations

import json

import pytest


_COMPLETE_INITIAL_ENV = {
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
    "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_initial",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE": "all",
}

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"


def _clear_flags(monkeypatch: pytest.MonkeyPatch) -> None:
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
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
    ):
        monkeypatch.delenv(name, raising=False)


def _enable_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)


def _sample_current_input(input_id: str) -> dict[str, object]:
    return {
        "id": input_id,
        "created_at": "2026-05-16T00:00:00Z",
        "memo": _SAMPLE_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


async def _render(input_id: str, user_id: str = "step7-integration-user"):
    from emlis_ai_reply_service import render_emlis_ai_reply

    return await render_emlis_ai_reply(
        user_id=user_id,
        subscription_tier="free",
        current_input=_sample_current_input(input_id),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )


def _diagnostic(reply) -> dict[str, object]:
    return dict(reply.meta["diagnostic_summary"])


def _phase_gate(reply) -> dict[str, object]:
    return dict(reply.meta["multi_perspective"]["phase_gate"])


def _resolution(reply) -> dict[str, object]:
    return dict(reply.meta["multi_perspective"]["composer_client_resolution"])


def _assert_fail_closed_public_shape(reply) -> None:
    assert reply.comment_text == ""
    assert reply.meta["observation_status"] in {"rejected", "unavailable", "safety_blocked"}
    assert reply.meta["diagnostic_summary"]["step6_final_ap0_scorecard_connection"]["comment_text_contract"] == "passed_only"
    assert reply.meta["diagnostic_summary"]["step6_final_ap0_scorecard_connection"]["display_gate_relaxed"] is False
    assert reply.meta["diagnostic_summary"]["step6_final_ap0_scorecard_connection"]["fixed_fallback_used"] is False


@pytest.mark.asyncio
async def test_step7_integration_ap0_red_fails_closed_before_candidate_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_complete_initial(monkeypatch)

    import emlis_ai_reply_service
    from emlis_ai_ap0_migration_decision_service import build_complete_initial_entry_ap0_decision as real_entry_ap0

    def red_contract_entry_ap0(**kwargs):
        contract = dict(kwargs.get("contract_baseline_meta") or {})
        contract["response_shape_changed"] = True
        kwargs["contract_baseline_meta"] = contract
        return real_entry_ap0(**kwargs)

    monkeypatch.setattr(emlis_ai_reply_service, "build_complete_initial_entry_ap0_decision", red_contract_entry_ap0)

    reply = await _render("step7-ap0-red-input", user_id="step7-ap0-red-user")
    diagnostic = _diagnostic(reply)
    phase_gate = _phase_gate(reply)
    resolution = _resolution(reply)
    decision = diagnostic["complete_initial_entry_ap0_decision"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]

    assert decision["green"] is False
    assert "public_contract_baseline" in decision["unmet_checks"]
    assert "rollout_allowed" not in decision["unmet_checks"]
    assert resolution["connection_status"] == "blocked_ap0"
    assert resolution["pre_connection_stop_stage"] == "ap0"
    assert diagnostic["complete_initial_resolution_reason_group"] == "ap0"
    assert phase_gate["complete_initial_client_resolved"] is False
    assert step5["candidate_generation_attempted"] is False
    assert step5["candidate_generated"] is False
    _assert_fail_closed_public_shape(reply)


@pytest.mark.asyncio
async def test_step7_integration_rollout_red_is_visible_and_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "off")

    reply = await _render("step7-rollout-red-input", user_id="step7-rollout-red-user")
    diagnostic = _diagnostic(reply)
    phase_gate = _phase_gate(reply)
    resolution = _resolution(reply)
    decision = diagnostic["complete_initial_entry_ap0_decision"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    step6 = diagnostic["step6_final_ap0_scorecard_connection"]

    assert decision["green"] is False
    assert "rollout_allowed" in decision["unmet_checks"]
    assert resolution["connection_status"] == "blocked_ap0"
    assert resolution["pre_connection_stop_stage"] == "ap0"
    assert diagnostic["complete_initial_resolution_reason_group"] == "rollout"
    assert phase_gate["step4_blocked_by_rollout"] is True
    assert phase_gate["complete_initial_client_resolved"] is False
    assert step5["complete_composer_client_generate_called"] is False
    assert step5["candidate_generated"] is False
    assert step6["scorecard_candidate_generated"] is False
    _assert_fail_closed_public_shape(reply)


@pytest.mark.asyncio
async def test_step7_integration_ap0_green_and_rollout_green_resolves_complete_client(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_complete_initial(monkeypatch)

    reply = await _render("step7-green-resolution-input", user_id="step7-green-resolution-user")
    diagnostic = _diagnostic(reply)
    phase_gate = _phase_gate(reply)
    resolution = _resolution(reply)
    decision = diagnostic["complete_initial_entry_ap0_decision"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]

    assert decision["green"] is True
    assert decision["used_for_registry_resolution"] is True
    assert resolution["connection_status"] == "default_client_resolved"
    assert resolution["resolved_client_class"] == "CocolonCompleteComposerClient"
    assert resolution["complete_initial_gate"]["ap0_green"] is True
    assert resolution["complete_initial_gate"]["release_allowed"] is True
    assert phase_gate["complete_initial_client_resolved"] is True
    assert phase_gate["step3_complete_initial_client_resolved"] is True
    assert step5["candidate_generation_attempted"] is True
    assert step5["complete_composer_client_generate_called"] is True
    assert step5["candidate_generated"] is True
    assert step5["fallback_used"] is False
    assert step5["display_gate_relaxed"] is False


@pytest.mark.asyncio
async def test_step7_integration_stale_fail_closed_expectation_uses_binding_contract_consistency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _enable_complete_initial(monkeypatch)

    reply = await _render("step7-gate-contract-input", user_id="step7-gate-contract-user")
    diagnostic = _diagnostic(reply)
    phase_gate = _phase_gate(reply)
    gate_results = diagnostic["gate_diagnostic"]["gate_results"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    step6 = diagnostic["step6_final_ap0_scorecard_connection"]
    display = step5["gate_results"]["display"]

    assert diagnostic["complete_initial_entry_ap0_decision"]["green"] is True
    assert diagnostic["complete_initial_client_resolved"] is True
    assert step5["candidate_generated"] is True
    assert step5["existing_reader_grounding_template_display_gates_preserved"] is True
    assert all(gate_results[key]["passed"] for key in ("reader", "grounding", "template_echo", "display"))
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()
    assert step5["display_observation_status"] == "passed"
    assert step5["public_comment_text_present"] is True
    assert step5["passed_only_comment_text_contract_preserved"] is True
    assert step5["display_gate_relaxed"] is False

    assert display["binding_required"] is True
    assert display["binding_used"] is True
    assert display["binding_missing"] is False
    assert display["binding_count"] == 3
    assert display["expected_binding_count"] == 3
    assert display["display_binding_contract_consistent"] is True
    assert display["display_binding_trace_repair_applied"] is True
    assert display["display_binding_expected_count_source"] == "accepted_grounding_sentence_count"
    assert step5["gate_results"]["display"]["comment_text_body_included"] is False
    assert step5["gate_results"]["display"]["candidate_body_included"] is False
    assert step5["gate_results"]["display"]["raw_input_included"] is False
    assert step5["gate_results"]["display"]["surface_body_included"] is False

    assert step6["scorecard_display_passed"] is True
    assert step6["public_comment_text_assigned_by_step6"] is False
    assert step6["fixed_fallback_used"] is False
    assert phase_gate["step5_existing_gates_preserved_after_generation"] is True
    assert phase_gate["step6_scorecard_display_passed"] is True


@pytest.mark.asyncio
async def test_step7_integration_gate_passed_public_comment_uses_existing_display_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable_complete_initial(monkeypatch)

    from emlis_ai_types import GroundingReport, GroundingSentenceClaim, ListenerReaderReport, TemplateEchoReport
    import emlis_ai_reply_service

    def passing_reader(_comment_text):
        return ListenerReaderReport(
            understandable=True,
            addressee_clear=True,
            speaker_integrity_ok=True,
            conversational=True,
            report_like=False,
            confidence=1.0,
        )

    def passing_grounding(**_kwargs):
        return GroundingReport(
            passed=True,
            sentence_claims=[
                GroundingSentenceClaim(
                    sentence_index=0,
                    sentence="binding checked",
                    evidence_span_ids=["s1"],
                    relation_supported=True,
                    binding_used=True,
                    binding_sentence_id="sent-1",
                    binding_evidence_span_ids=["s1"],
                    binding_phrase_unit_ids=["cpu1"],
                    binding_relation_type="recovery",
                    grounding_support_source="step7_integration_fixture",
                )
            ],
            coverage_ratio=1.0,
            confidence=1.0,
            binding_used=True,
            binding_present=True,
            binding_missing=False,
            binding_count=1,
            expected_binding_count=1,
            binding_version="step7.integration.fixture",
            relation_types=["recovery"],
            binding_supported_sentence_count=1,
            declared_relation_types=["recovery"],
            declared_phrase_unit_ids=["cpu1"],
        )

    def passing_template(**_kwargs):
        return TemplateEchoReport(passed=True)

    monkeypatch.setattr(emlis_ai_reply_service, "judge_listener_readability", passing_reader)
    monkeypatch.setattr(emlis_ai_reply_service, "judge_grounding", passing_grounding)
    monkeypatch.setattr(emlis_ai_reply_service, "guard_template_echo", passing_template)

    reply = await _render("step7-gate-passed-input", user_id="step7-gate-passed-user")
    diagnostic = _diagnostic(reply)
    phase_gate = _phase_gate(reply)
    gate_results = diagnostic["gate_diagnostic"]["gate_results"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    step6 = diagnostic["step6_final_ap0_scorecard_connection"]

    assert diagnostic["complete_initial_entry_ap0_decision"]["green"] is True
    assert diagnostic["complete_initial_client_resolved"] is True
    assert step5["candidate_generated"] is True
    assert step5["existing_reader_grounding_template_display_gates_preserved"] is True
    assert all(gate_results[key]["passed"] for key in ("reader", "grounding", "template_echo", "display"))
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()
    assert step5["display_observation_status"] == "passed"
    assert step5["public_comment_text_present"] is True
    assert step5["passed_only_comment_text_contract_preserved"] is True
    assert step5["fallback_used"] is False
    assert step5["display_gate_relaxed"] is False
    assert step6["scorecard_display_passed"] is True
    assert step6["public_comment_text_assigned_by_step6"] is False
    assert step6["fixed_fallback_used"] is False
    assert phase_gate["step6_scorecard_display_passed"] is True

    serialized_meta = json.dumps(
        {
            "entry_ap0": diagnostic["complete_initial_entry_ap0_decision"],
            "step5": step5,
            "step6": step6,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    assert _SAMPLE_MEMO not in serialized_meta
    assert "memo_action" not in serialized_meta
    assert "current_input" not in serialized_meta
