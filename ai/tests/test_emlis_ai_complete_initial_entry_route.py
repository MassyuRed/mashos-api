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


@pytest.mark.asyncio
async def test_step3_passes_entry_ap0_to_registry_before_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step3-entry-ap0-injection-user",
        subscription_tier="free",
        current_input=_sample_current_input("step3-entry-ap0-injection-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    multi = reply.meta["multi_perspective"]
    phase_gate = multi["phase_gate"]
    resolution = multi["composer_client_resolution"]
    seed = diagnostic["complete_initial_pre_generation_diagnostic_seed"]
    decision = diagnostic["complete_initial_entry_ap0_decision"]

    # Step2 seed is still built before registry/candidate generation.
    assert seed["version"] == "emlis.complete_initial.pre_generation_diagnostic_seed.v1"
    assert seed["step"] == "Step2_pre_generation_diagnostic_seed"
    assert seed["built_after_source_evidence_scope_rollout"] is True
    assert seed["built_before_registry_resolution"] is True
    assert seed["built_before_candidate_generation"] is True
    assert seed["created_before_registry_resolution"] is True
    assert seed["created_before_candidate_generation"] is True
    assert seed["uses_post_generation_display_gate"] is False
    assert seed["display_gate_relaxed"] is False
    assert seed["raw_input_included"] is False
    assert seed["generated_candidate_included"] is False
    assert seed["generated_text_included"] is False

    # Step3 consumes that seed and injects its Entry AP0 decision into the resolver.
    assert seed["resolver_injection_deferred_to_step3"] is False
    assert seed["resolver_ap0_injection_pending"] is False
    assert seed["ap0_decision_not_injected_to_registry_in_step2"] is True
    assert seed["ap0_decision_injected_to_registry_in_step3"] is True
    assert seed["used_for_registry_resolution"] is True
    assert seed["resolver_injection_completed_in_step3"] is True
    assert seed["step3_resolver_ap0_decision_injection_ready"] is True
    assert seed["step3_resolver_ap0_decision_source"] == "complete_initial_entry_ap0_decision"

    assert seed["entry_ap0_green"] is True
    assert decision["green"] is True
    assert decision["entry_gate_only"] is True
    assert decision["uses_post_generation_display_gate"] is False
    assert decision["used_for_registry_resolution"] is True
    assert decision["ap0_decision_injected_to_registry_in_step3"] is True
    assert seed["coverage_matrix_seed"]["binding_infrastructure_ready"] is True

    assert resolution["connection_status"] == "default_client_resolved"
    assert resolution["pre_connection_stop_stage"] == "default_resolved"
    assert resolution["default_client_used"] is True
    assert resolution["complete_initial_client_used"] is True
    assert resolution["resolved_client_class"] == "CocolonCompleteComposerClient"
    assert resolution["resolution_source"] == "cocolon_complete_composer_initial"
    assert resolution["complete_initial_gate"]["reason"] == "complete_initial_client_resolved"
    assert resolution["complete_initial_gate"]["ap0_green"] is True
    assert resolution["complete_initial_gate"]["release_allowed"] is True

    assert phase_gate["step2_pre_generation_diagnostic_seed_ready"] is True
    assert phase_gate["complete_initial_entry_ap0_resolver_injection_deferred_to_step3"] is False
    assert phase_gate["complete_initial_entry_ap0_resolver_injection_pending"] is False
    assert phase_gate["complete_initial_entry_ap0_used_for_registry_resolution"] is True
    assert phase_gate["complete_initial_entry_ap0_injected_to_registry_in_step3"] is True
    assert phase_gate["complete_initial_entry_ap0_resolver_injection_completed_in_step3"] is True
    assert phase_gate["step3_resolver_ap0_decision_injection_ready"] is True
    assert phase_gate["complete_initial_client_resolved"] is True
    assert phase_gate["step3_complete_initial_client_resolved"] is True

    assert diagnostic["complete_initial_entry_ap0_materials"]["coverage_matrix_seed"] == seed["coverage_matrix_seed"]
    assert diagnostic["complete_initial_entry_ap0_used_for_registry_resolution"] is True
    assert diagnostic["complete_initial_entry_ap0_resolver_injection_pending"] is False
    assert diagnostic["complete_initial_entry_ap0_injected_to_registry_in_step3"] is True
    assert diagnostic["complete_initial_entry_ap0_resolver_injection_completed_in_step3"] is True
    assert diagnostic["complete_initial_client_resolved"] is True
    assert diagnostic["step3_complete_initial_client_resolved"] is True

    assert reply.meta["complete_initial_pre_generation_diagnostic_seed"] == seed
    assert multi["complete_initial_pre_generation_diagnostic_seed"] == seed
    assert multi["complete_initial_entry_ap0_decision"] == decision

    serialized_seed = json.dumps(seed, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized_seed
    assert "memo_action" not in serialized_seed
    assert "current_input" not in serialized_seed


@pytest.mark.asyncio
async def test_step3_entry_ap0_red_is_injected_but_registry_still_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "off")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step3-entry-ap0-red-user",
        subscription_tier="free",
        current_input=_sample_current_input("step3-entry-ap0-red-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    resolution = reply.meta["multi_perspective"]["composer_client_resolution"]
    seed = diagnostic["complete_initial_pre_generation_diagnostic_seed"]
    decision = diagnostic["complete_initial_entry_ap0_decision"]

    assert seed["entry_ap0_green"] is False
    assert decision["green"] is False
    assert "rollout_allowed" in decision["unmet_checks"]
    assert seed["resolver_injection_deferred_to_step3"] is False
    assert seed["resolver_ap0_injection_pending"] is False
    assert seed["ap0_decision_injected_to_registry_in_step3"] is True
    assert seed["used_for_registry_resolution"] is True
    assert decision["used_for_registry_resolution"] is True
    assert decision["ap0_decision_injected_to_registry_in_step3"] is True

    assert resolution["connection_status"] == "blocked_ap0"
    assert resolution["pre_connection_stop_stage"] == "ap0"
    assert resolution["default_client_used"] is False
    assert resolution["complete_initial_client_used"] is False
    assert "complete_initial_ap0_not_green" in resolution["rejection_reasons"]

    assert phase_gate["complete_initial_entry_ap0_used_for_registry_resolution"] is True
    assert phase_gate["complete_initial_entry_ap0_resolver_injection_pending"] is False
    assert phase_gate["complete_initial_entry_ap0_injected_to_registry_in_step3"] is True
    assert phase_gate["complete_initial_client_resolved"] is False
    assert diagnostic["complete_initial_client_resolved"] is False
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step4_resolution_meta_is_fixed_for_resolved_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step4-resolution-resolved-user",
        subscription_tier="free",
        current_input=_sample_current_input("step4-resolution-resolved-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    resolution = reply.meta["multi_perspective"]["composer_client_resolution"]
    step4 = diagnostic["complete_initial_resolution"]

    assert diagnostic["step4_resolution_meta_fixed"] is True
    assert diagnostic["complete_initial_resolution_meta_fixed"] is True
    assert diagnostic["composer_client_resolution"] == resolution
    assert diagnostic["complete_initial_gate"] == resolution["complete_initial_gate"]
    assert diagnostic["composer_client_resolution_rejection_reasons"] == []
    assert diagnostic["complete_initial_resolution_rejection_reasons"] == []

    assert step4["version"] == "emlis.complete_initial.step4.resolution_meta.v1"
    assert step4["step"] == "Step4_resolution_meta_fixed"
    assert step4["connection_status"] == "default_client_resolved"
    assert step4["pre_connection_stop_stage"] == "default_resolved"
    assert step4["complete_initial_client_resolved"] is True
    assert step4["composer_client_not_connected"] is False
    assert step4["composer_client_not_connected_reason_group"] == "resolved"
    assert step4["reason_group"] == "resolved"
    assert step4["primary_reason"] == "complete_initial_client_resolved"
    assert step4["complete_initial_gate"]["reason"] == "complete_initial_client_resolved"
    assert step4["display_gate_relaxed"] is False
    assert step4["comment_text_contract"] == "passed_only"
    assert step4["raw_input_included"] is False
    assert step4["generated_candidate_included"] is False

    assert phase_gate["step4_resolution_meta_fixed"] is True
    assert phase_gate["step4_complete_initial_resolution_ready"] is True
    assert phase_gate["step4_resolution_reason_group"] == "resolved"
    assert phase_gate["step4_complete_initial_gate_reason"] == "complete_initial_client_resolved"
    assert phase_gate["step4_blocked_by_ap0"] is False
    assert phase_gate["step4_blocked_by_rollout"] is False
    assert phase_gate["step4_blocked_by_safety"] is False


@pytest.mark.asyncio
async def test_step4_resolution_meta_splits_rollout_from_ap0_registry_block(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "off")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step4-resolution-rollout-user",
        subscription_tier="free",
        current_input=_sample_current_input("step4-resolution-rollout-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    resolution = reply.meta["multi_perspective"]["composer_client_resolution"]
    step4 = diagnostic["complete_initial_resolution"]

    # Registry remains fail-closed with the same raw AP0 stop, but Step4 exposes
    # the actionable root group as rollout because the Entry AP0 unmet check is rollout_allowed.
    assert resolution["connection_status"] == "blocked_ap0"
    assert resolution["pre_connection_stop_stage"] == "ap0"
    assert "complete_initial_ap0_not_green" in resolution["rejection_reasons"]
    assert diagnostic["composer_client_resolution"] == resolution
    assert diagnostic["complete_initial_gate"]["reason"] == "complete_initial_ap0_not_green"

    assert step4["connection_status"] == "blocked_ap0"
    assert step4["pre_connection_stop_stage"] == "ap0"
    assert step4["composer_client_not_connected"] is True
    assert step4["reason_group"] == "rollout"
    assert step4["composer_client_not_connected_reason_group"] == "rollout"
    assert step4["blocked_by_rollout"] is True
    assert step4["blocked_by_ap0"] is False
    assert "rollout_allowed" in step4["entry_unmet_checks"]
    assert step4["display_gate_relaxed"] is False
    assert reply.comment_text == ""

    assert diagnostic["complete_initial_resolution_reason_group"] == "rollout"
    assert diagnostic["composer_client_not_connected_reason_group"] == "rollout"
    assert phase_gate["step4_resolution_reason_group"] == "rollout"
    assert phase_gate["step4_blocked_by_rollout"] is True
    assert phase_gate["step4_blocked_by_ap0"] is False
    assert phase_gate["step4_blocked_by_safety"] is False


@pytest.mark.asyncio
async def test_step4_resolution_meta_splits_safety_before_composer(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step4-resolution-safety-user",
        subscription_tier="free",
        current_input={
            "id": "step4-resolution-safety-input",
            "created_at": "2026-05-16T00:00:00Z",
            "memo": "生きていたくない。もう無理。",
            "memo_action": "",
            "emotion_details": [{"type": "不安", "strength": "strong"}],
            "emotions": ["不安"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    resolution = reply.meta["multi_perspective"]["composer_client_resolution"]
    step4 = diagnostic["complete_initial_resolution"]

    assert resolution["connection_status"] == "blocked_safety"
    assert resolution["pre_connection_stop_stage"] == "safety"
    assert "safety_boundary" in resolution["rejection_reasons"]
    assert diagnostic["composer_client_resolution"] == resolution

    assert step4["connection_status"] == "blocked_safety"
    assert step4["pre_connection_stop_stage"] == "safety"
    assert step4["composer_client_not_connected"] is True
    assert step4["reason_group"] == "safety"
    assert step4["composer_client_not_connected_reason_group"] == "safety"
    assert step4["blocked_by_safety"] is True
    assert step4["blocked_by_ap0"] is False
    assert step4["blocked_by_rollout"] is False
    assert step4["raw_input_included"] is False
    assert step4["generated_candidate_included"] is False
    assert reply.comment_text == ""

    assert diagnostic["complete_initial_resolution_reason_group"] == "safety"
    assert diagnostic["composer_client_not_connected_reason_group"] == "safety"
    assert phase_gate["step4_resolution_reason_group"] == "safety"
    assert phase_gate["step4_blocked_by_safety"] is True
    assert phase_gate["step4_blocked_by_ap0"] is False
    assert phase_gate["step4_blocked_by_rollout"] is False


@pytest.mark.asyncio
async def test_step5_candidate_generation_path_keeps_existing_gates_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step5-candidate-gate-user",
        subscription_tier="free",
        current_input=_sample_current_input("step5-candidate-gate-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    runtime = diagnostic["complete_initial_runtime"]

    assert diagnostic["step4_resolution_meta_fixed"] is True
    assert diagnostic["step5_candidate_generation_path_confirmed"] is True
    assert step5["version"] == "emlis.complete_initial.step5.candidate_generation_path.v1"
    assert step5["step"] == "Step5_candidate_generation_path_confirmation"
    assert step5["complete_initial_client_resolved"] is True
    assert step5["candidate_generation_attempted"] is True
    assert step5["complete_composer_client_generate_called"] is True
    assert step5["candidate_generated"] is True
    assert step5["candidate_status"] == "generated"
    assert step5["composer_source"] == "ai_generated"

    assert step5["existing_reader_grounding_template_display_gates_preserved"] is True
    assert step5["reader_gate_evaluated"] is True
    assert step5["grounding_gate_evaluated"] is True
    assert step5["template_gate_evaluated"] is True
    assert step5["display_gate_evaluated"] is True
    assert set(step5["gate_results"].keys()) == {"reader", "grounding", "template_echo", "display"}

    # Step5 confirms generation path only. It must not bypass the existing gates.
    assert step5["display_observation_status"] != "passed"
    assert reply.comment_text == ""
    assert step5["public_comment_text_present"] is False
    assert step5["candidate_comment_text_present"] is True
    assert step5["non_passed_comment_text_empty"] is True
    assert step5["passed_only_comment_text_contract_preserved"] is True

    assert step5["fallback_used"] is False
    assert step5["fallback_observation_sentence_added"] is False
    assert step5["fixed_string_renderer_used"] is False
    assert step5["display_gate_relaxed"] is False
    assert step5["raw_input_included"] is False
    assert step5["generated_candidate_text_included"] is False
    assert step5["candidate_text_included"] is False

    assert runtime["version"] == "emlis.complete_initial.runtime.v1"
    assert runtime["candidate_generation_attempted"] is True
    assert runtime["candidate_generated"] is True
    assert runtime["candidate_status"] == "generated"
    assert runtime["composer_source"] == "ai_generated"
    assert runtime["used_evidence_span_count"] >= 1
    assert runtime["used_phrase_unit_count"] >= 1
    assert runtime["sentence_binding_count"] >= 1
    assert runtime["binding_present"] is True
    assert runtime["comment_text_contract"] == "passed_only"
    assert runtime["public_comment_text_present"] is False
    assert runtime["candidate_comment_text_present"] is True
    assert runtime["raw_input_included"] is False
    assert runtime["generated_candidate_text_included"] is False

    for binding in runtime["sentence_bindings"]:
        assert binding["sentence_id"]
        assert binding["used_evidence_span_ids"]
        assert binding["used_phrase_unit_ids"]
        assert binding["relation_type"]
        assert binding["raw_input_included"] is False
        assert "text" not in binding
        assert "surface_text" not in binding
        assert "realized_text" not in binding

    serialized_bindings = json.dumps(runtime["sentence_bindings"], ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized_bindings
    assert "surface_text" not in serialized_bindings
    assert "realized_text" not in serialized_bindings

    assert phase_gate["step5_candidate_generation_path_confirmed"] is True
    assert phase_gate["step5_complete_initial_candidate_generation_attempted"] is True
    assert phase_gate["step5_complete_composer_client_generate_called"] is True
    assert phase_gate["step5_complete_initial_candidate_generated"] is True
    assert phase_gate["step5_existing_gates_preserved_after_generation"] is True
    assert phase_gate["step5_non_passed_comment_text_empty"] is True
    assert phase_gate["step5_no_fallback_used"] is True
    assert phase_gate["step5_display_gate_relaxed"] is False
    assert phase_gate["step5_runtime_sentence_binding_count"] >= 1


@pytest.mark.asyncio
async def test_step5_ap0_red_does_not_run_complete_generate(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "off")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step5-ap0-red-user",
        subscription_tier="free",
        current_input=_sample_current_input("step5-ap0-red-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    step5 = diagnostic["complete_initial_candidate_generation_path"]
    runtime = diagnostic["complete_initial_runtime"]

    assert diagnostic["complete_initial_resolution_reason_group"] == "rollout"
    assert step5["complete_initial_client_resolved"] is False
    assert step5["candidate_generation_attempted"] is False
    assert step5["complete_composer_client_generate_called"] is False
    assert step5["candidate_generated"] is False
    assert runtime["client_status"] == "not_resolved"
    assert runtime["candidate_generation_attempted"] is False
    assert runtime["candidate_generated"] is False
    assert step5["public_comment_text_present"] is False
    assert step5["non_passed_comment_text_empty"] is True
    assert reply.comment_text == ""
    assert step5["fallback_used"] is False
    assert step5["display_gate_relaxed"] is False
    assert phase_gate["step5_candidate_generation_path_confirmed"] is True
    assert phase_gate["step5_complete_composer_client_generate_called"] is False
    assert phase_gate["step5_no_fallback_used"] is True


@pytest.mark.asyncio
async def test_step6_final_ap0_and_scorecard_connection_meta_is_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step6-final-ap0-scorecard-user",
        subscription_tier="free",
        current_input=_sample_current_input("step6-final-ap0-scorecard-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    multi = reply.meta["multi_perspective"]
    phase_gate = multi["phase_gate"]
    step6 = diagnostic["step6_final_ap0_scorecard_connection"]
    next_improvement = diagnostic["complete_initial_next_improvement_meta"]

    assert step6["version"] == "emlis.complete_initial.step6.final_ap0_scorecard_connection.v1"
    assert step6["step"] == "Step6_Final_AP0_scorecard_connection"
    assert step6["ready"] is True
    assert step6["meta_only"] is True
    assert step6["additive"] is True

    # Step6 records the execution-after-Gate Final AP0 separately from Entry AP0.
    assert step6["entry_ap0_used_for_registry_resolution"] is True
    assert step6["entry_ap0_gate_only"] is True
    assert step6["final_ap0_uses_post_generation_results"] is True
    assert step6["final_ap0_decision_connected"] is True
    assert step6["final_ap0_decision_ready"] is True
    assert diagnostic["complete_initial_final_ap0_decision"] == diagnostic["step18_ap0_migration_decision"]
    assert diagnostic["complete_initial_final_ap0_report"] == diagnostic["complete_composer_initial_ap0_report"]

    # Step6 also connects the scorecard event/harness without changing the public output.
    assert step6["scorecard_event_connected"] is True
    assert step6["scorecard_harness_connected"] is True
    assert step6["scorecard_candidate_generation_attempted"] is True
    assert step6["scorecard_candidate_generated"] is True
    assert step6["scorecard_binding_pass"] is True
    assert step6["scorecard_event_kind"] == "complete_composer_initial_reply_attempt"
    assert diagnostic["complete_initial_final_scorecard_event"] == diagnostic["complete_scorecard_event"]
    assert diagnostic["complete_initial_final_scorecard_harness"] == diagnostic["complete_scorecard_harness"]

    assert step6["next_improvement_meta_visible"] is True
    assert next_improvement["visible_from_meta_only"] is True
    assert next_improvement["raw_input_required"] is False
    assert isinstance(next_improvement["improvement_reason_codes"], list)
    assert next_improvement["improvement_reason_codes"]

    assert step6["comment_text_contract"] == "passed_only"
    assert step6["passed_only_comment_text_contract_preserved"] is True
    assert step6["public_comment_text_assigned_by_step6"] is False
    assert step6["display_gate_relaxed"] is False
    assert step6["fixed_fallback_used"] is False
    assert step6["raw_input_included"] is False
    assert step6["generated_candidate_text_included"] is False
    assert reply.comment_text == ""

    assert phase_gate["step6_final_ap0_scorecard_connection_ready"] is True
    assert phase_gate["step6_final_ap0_scorecard_connected"] is True
    assert phase_gate["step6_final_ap0_decision_ready"] is True
    assert phase_gate["step6_scorecard_event_connected"] is True
    assert phase_gate["step6_scorecard_harness_connected"] is True
    assert phase_gate["step6_next_improvement_meta_visible"] is True
    assert phase_gate["step6_public_response_shape_preserved"] is True
    assert phase_gate["step6_passed_only_contract_preserved"] is True
    assert phase_gate["step6_raw_input_included"] is False
    assert phase_gate["step6_display_gate_relaxed"] is False

    assert reply.meta["step6_final_ap0_scorecard_connection"] == step6
    assert reply.meta["complete_initial_final_ap0_scorecard_connection"] == step6
    assert reply.meta["complete_initial_next_improvement_meta"] == next_improvement
    assert multi["step6_final_ap0_scorecard_connection"] == step6

    serialized_step6 = json.dumps(step6, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized_step6
    assert "memo_action" not in serialized_step6
    assert "current_input" not in serialized_step6
    assert "surface_text" not in serialized_step6
    assert "realized_text" not in serialized_step6


@pytest.mark.asyncio
async def test_step6_rollout_red_still_records_final_ap0_and_scorecard_event(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "off")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step6-rollout-red-user",
        subscription_tier="free",
        current_input=_sample_current_input("step6-rollout-red-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    step6 = diagnostic["step6_final_ap0_scorecard_connection"]
    scorecard_event = diagnostic["complete_initial_final_scorecard_event"]

    assert diagnostic["complete_initial_resolution_reason_group"] == "rollout"
    assert step6["final_ap0_decision_connected"] is True
    assert step6["final_ap0_decision_ready"] is True
    assert step6["scorecard_event_connected"] is True
    assert scorecard_event["scorecard_event_connected"] is True
    assert scorecard_event["complete_candidate_seen"] is False
    assert step6["scorecard_candidate_generation_attempted"] is False
    assert step6["scorecard_candidate_generated"] is False
    assert step6["scorecard_display_passed"] is False
    assert step6["next_improvement_meta_visible"] is True
    assert step6["display_gate_relaxed"] is False
    assert step6["raw_input_included"] is False
    assert reply.comment_text == ""

    assert phase_gate["step6_final_ap0_scorecard_connection_ready"] is True
    assert phase_gate["step6_scorecard_event_connected"] is True
    assert phase_gate["step6_scorecard_candidate_generated"] is False
    assert phase_gate["step6_next_improvement_meta_visible"] is True
