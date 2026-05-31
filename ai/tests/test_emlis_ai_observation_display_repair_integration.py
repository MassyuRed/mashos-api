from __future__ import annotations

from emlis_ai_observation_display_repair_integration import (
    attach_observation_display_repair_meta,
    integrate_observation_display_repair,
)
from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)


def _rejected_display(*reasons: str) -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="step10-test-trace",
    )


def _reader(*reasons: str) -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=True,
        conversational=False,
        report_like=False,
        rejection_reasons=list(reasons),
    )


def _grounding(*reasons: str) -> GroundingReport:
    return GroundingReport(
        passed=False,
        rejection_reasons=list(reasons),
    )


def test_step10_low_information_branch_passes_existing_display_contract() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step10-low-info",
        original_display_decision=_rejected_display("too_short_for_observation"),
        original_reader_report=_reader("too_short_for_observation"),
        original_grounding_report=_grounding("graph_evidence_not_used"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert result.display_decision.comment_text.strip()
    assert "詳しく残せそうなら、何があったか残してみませんか" in result.display_decision.comment_text
    assert "よければ、何がありましたか" not in result.display_decision.comment_text

    meta = result.as_meta()
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert meta["display_gate_relaxed"] is False
    assert meta["public_status_extended"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["fixed_fallback_used"] is False
    assert meta["external_ai_used"] is False
    assert meta["phase20_3_input_material_bundle"]
    composer_meta = meta["low_information_observation_composer_meta"]
    assert composer_meta["phase20_4_low_information_material_surface_ready"] is True
    assert composer_meta["low_information_surface_from_visible_material_slots"] is True
    assert composer_meta["unknown_prompt_from_unknown_slots"] is True
    assert composer_meta["visible_material_slots"]
    assert composer_meta["material_unknown_slots"]


def test_step10_feature_flag_disabled_does_not_block_low_information_by_itself() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step10-feature-flag-low-info",
        original_display_decision=DisplayDecision(
            observation_status="unavailable",
            comment_text="",
            rejection_reasons=["default_limited_composer_feature_disabled"],
            trace_id="step10-feature-flag-low-info",
        ),
        original_reader_report=_reader("default_limited_composer_feature_disabled"),
        original_grounding_report=_grounding("default_limited_composer_feature_disabled"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
        composer_client_resolution={
            "connection_status": "blocked_feature_flag",
            "pre_connection_stop_stage": "flag",
            "release_allowed": False,
            "default_client_used": False,
            "rejection_reasons": ["default_limited_composer_feature_disabled"],
        },
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert result.display_decision.comment_text.strip()
    assert result.blocked_reasons == ()


def test_step10_feature_flag_disabled_does_not_reroute_eligible_input_to_low_information() -> None:
    result = integrate_observation_display_repair(
        current_input={
            "memo": (
                "リラックスできる時間はあるのに、現実と向き合う瞬間の重さが残っている。"
                "普通に生活したい気持ちもあるけれど、悪化することも分かっていて、たまに逃げ出したくなる。"
            ),
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step10-feature-flag-eligible",
        original_display_decision=DisplayDecision(
            observation_status="unavailable",
            comment_text="",
            rejection_reasons=[
                "default_limited_composer_feature_disabled",
                "composer_source_unavailable",
                "empty_comment_text",
                "too_short_for_observation",
            ],
            trace_id="step10-feature-flag-eligible",
        ),
        original_reader_report=_reader("default_limited_composer_feature_disabled"),
        original_grounding_report=_grounding("default_limited_composer_feature_disabled"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
        composer_client_resolution={
            "connection_status": "blocked_feature_flag",
            "pre_connection_stop_stage": "flag",
            "release_allowed": False,
            "default_client_used": False,
            "rejection_reasons": ["default_limited_composer_feature_disabled"],
        },
    )

    assert result.applied is False
    assert result.display_decision.observation_status == "unavailable"
    assert result.display_decision.comment_text == ""
    assert "composer_resolution_blocked_feature_flag" in result.blocked_reasons
    assert "default_limited_composer_feature_disabled" in result.blocked_reasons


def test_step10_repairable_eligible_failure_discards_candidate_and_reroutes_to_low_information() -> None:
    failed_candidate = ConversationComposerCandidate(
        comment_text="あなたはいつも環境で疲れているのでしょう。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="step10-eligible-repair",
    )

    result = integrate_observation_display_repair(
        current_input={"memo": "環境を変えたいけど変えられなくて疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step10-eligible-repair",
        original_display_decision=_rejected_display("relation_confidence_low", "overclaim"),
        original_reader_report=_reader("relation_confidence_low"),
        original_grounding_report=_grounding("unsupported_sentence"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="ai_generated",
        original_composer_candidate=failed_candidate,
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    assert result.composer_candidate is not failed_candidate
    assert "eligible_branch_repaired_to_low_information" in result.repair_reasons

    meta = result.as_meta()
    assert meta["rerouted_from_eligible"] is True
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["public_status_extended"] is False


def test_step10_does_not_repair_blocked_rollout_resolution() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step10-blocked-rollout",
        original_display_decision=DisplayDecision(
            observation_status="unavailable",
            comment_text="",
            rejection_reasons=["composer_source_unavailable"],
            trace_id="step10-blocked-rollout",
        ),
        original_reader_report=_reader("composer_source_unavailable"),
        original_grounding_report=_grounding("composer_source_unavailable"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
        composer_client_resolution={
            "connection_status": "blocked_rollout",
            "pre_connection_stop_stage": "rollout",
            "release_allowed": False,
            "default_client_used": False,
            "rejection_reasons": ["limited_composer_rollout_not_allowed"],
        },
    )

    assert result.applied is False
    assert result.display_decision.observation_status == "unavailable"
    assert result.display_decision.comment_text == ""
    assert "composer_resolution_blocked_rollout" in result.blocked_reasons
    assert "composer_resolution_pre_connection_rollout_stop" in result.blocked_reasons
    assert "limited_composer_rollout_not_allowed" in result.blocked_reasons

    meta = result.as_meta()
    assert meta["applied"] is False
    assert meta["low_information_repair_applied"] is False
    assert meta["final_observation_status"] == "unavailable"
    assert meta["comment_text_present"] is False
    assert meta["comment_text_allowed"] is False
    assert meta["public_status_extended"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False


def test_step10_rollout_block_meta_contract_is_attached_consistently() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="step10-rollout-meta-contract",
        original_display_decision=DisplayDecision(
            observation_status="unavailable",
            comment_text="",
            rejection_reasons=["composer_source_unavailable"],
            trace_id="step10-rollout-meta-contract",
        ),
        original_reader_report=_reader("composer_source_unavailable"),
        original_grounding_report=_grounding("composer_source_unavailable"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
        composer_client_resolution={
            "connection_status": "blocked_rollout",
            "pre_connection_stop_stage": "rollout",
            "release_allowed": False,
            "default_client_used": False,
            "rejection_reasons": ["limited_composer_rollout_not_allowed"],
        },
        repair_allowed=False,
        repair_block_reason="step10_blocked_by_phase7_rollout",
    )

    attached = attach_observation_display_repair_meta(
        {
            "diagnostic_summary": {"comment_text_allowed": False},
            "multi_perspective": {"phase_gate": {}},
        },
        result,
    )

    step10 = attached["step10_observation_display_repair_integration"]
    assert attached["observation_display_repair_integration"] == step10
    assert attached["diagnostic_summary"]["step10_observation_display_repair_integration"] == step10
    assert attached["diagnostic_summary"]["observation_display_repair_integration"] == step10
    assert attached["diagnostic_summary"]["comment_text_allowed"] is False
    assert attached["multi_perspective"]["step10_observation_display_repair_integration"] == step10
    assert attached["multi_perspective"]["observation_display_repair_integration"] == step10

    assert step10["applied"] is False
    assert step10["low_information_repair_applied"] is False
    assert step10["original_observation_status"] == "unavailable"
    assert step10["final_observation_status"] == "unavailable"
    assert step10["comment_text_present"] is False
    assert step10["comment_text_allowed"] is False
    assert "step10_blocked_by_phase7_rollout" in step10["blocked_reasons"]
    assert "composer_resolution_blocked_rollout" in step10["blocked_reasons"]
    assert "composer_resolution_pre_connection_rollout_stop" in step10["blocked_reasons"]
    assert "limited_composer_rollout_not_allowed" in step10["blocked_reasons"]
    assert step10["public_status_extended"] is False
    assert step10["observation_status_enum_extended"] is False
    assert step10["rn_visible_contract_changed"] is False
    assert step10["api_route_changed"] is False
    assert step10["db_physical_name_changed"] is False
    assert step10["response_shape_changed"] is False

    phase_gate = attached["multi_perspective"]["phase_gate"]
    assert phase_gate["step10_observation_display_repair_integration_ready"] is True
    assert phase_gate["step10_low_information_display_repair_applied"] is False
    assert phase_gate["step10_display_gate_relaxed"] is False
    assert phase_gate["step10_public_status_extended"] is False


def test_step10_does_not_repair_safety_blocked_input() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "危険なことをしたい", "memo_action": ""},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_blocked"]),
        trace_id="step10-safety",
        original_display_decision=DisplayDecision(
            observation_status="safety_blocked",
            comment_text="",
            rejection_reasons=["safety_boundary"],
            trace_id="step10-safety",
        ),
        original_reader_report=_reader("safety_boundary"),
        original_grounding_report=_grounding("safety_boundary"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="",
        original_composer_candidate=None,
    )

    assert result.applied is False
    assert result.display_decision.observation_status == "safety_blocked"
    assert "safety_boundary" in result.blocked_reasons
