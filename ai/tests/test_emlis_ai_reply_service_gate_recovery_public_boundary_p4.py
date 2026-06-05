# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 reply_service insurance boundary for Gate Recovery candidates.

P3 blocks the normal Gate Recovery material-surface path inside
``recover_emlis_gate_failure``.  P4 is a second boundary: even if a future or
regressed Gate Recovery Loop returns ``applied=True`` with a diagnostic recovery
surface, reply_service must not adopt that candidate as public ``comment_text``.
"""

from typing import Any
from types import SimpleNamespace

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
from emlis_ai_gate_recovery_loop import (
    GateRecoveryLoopResult,
    _gate_recovery_composer_meta,
    build_gate_recovery_surface_binding_meta,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
)
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    TemplateEchoReport,
    GreetingDecision,
)


_COMPOSER_ENV_KEYS = (
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
)


@pytest.fixture(autouse=True)
def _patch_source_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="p4-reply-service-boundary",
            slot_key="p4-reply-service-boundary",
            greeting_text="Emlisです。",
            first_in_slot=False,
        )

    async def empty_dict(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {}

    async def empty_list(*_args: Any, **_kwargs: Any) -> list[Any]:
        return []

    async def none_value(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(context_service, "_resolve_display_name_for_user", fake_display_name)
    monkeypatch.setattr(context_service, "_resolve_timezone_name_for_user", fake_timezone)
    monkeypatch.setattr(context_service, "decide_greeting_for_user", fake_greeting)
    for name, replacement in {
        "_get_input_summary_for_user": empty_dict,
        "_get_myweb_home_summary_for_user": empty_dict,
        "_get_latest_today_question_answer_for_user": empty_dict,
        "_list_recent_today_question_answers_for_user": empty_list,
        "get_last_input_for_user": none_value,
        "list_same_day_recent_inputs": empty_list,
        "search_similar_inputs": empty_list,
        "load_emlis_ai_user_model_for_user": none_value,
        "get_cross_core_context_for_emlis_ai": empty_list,
    }.items():
        if hasattr(context_service, name):
            monkeypatch.setattr(context_service, name, replacement)


def _passed_display() -> DisplayDecision:
    return DisplayDecision(
        observation_status="passed",
        comment_text="Gate Recovery diagnostic body must not be adopted by reply_service.",
        rejection_reasons=[],
        trace_id="p4-reply-service-public-boundary",
    )


def _reader_report() -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=True,
        addressee_clear=True,
        speaker_integrity_ok=True,
        conversational=True,
        report_like=False,
        rejection_reasons=[],
    )


def _result_for_candidate(
    candidate: ConversationComposerCandidate,
    *,
    surface_binding_meta: dict[str, object] | None = None,
) -> GateRecoveryLoopResult:
    return GateRecoveryLoopResult(
        applied=True,
        display_decision=_passed_display(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=True, rejection_reasons=[]),
        template_echo_report=TemplateEchoReport(passed=True, rejection_reasons=[]),
        composer_source=str(candidate.composer_source or "ai_generated"),
        composer_candidate=candidate,
        blocked_reasons=(),
        surface_binding_meta=surface_binding_meta or {},
    )


def _diagnostic_candidate(*, post_final: bool = False) -> ConversationComposerCandidate:
    meta = _gate_recovery_composer_meta(
        material_quality="eligible",
        visible_slots=("relationship", "action", "emotion_direction"),
        unknown_slots=("cause",),
        relation_ids=("relationship_material",),
        policy="shorten_surface",
        recovery_context=(
            RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE
            if post_final
            else RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE
        ),
        post_final_gate_failure=post_final,
    )
    return ConversationComposerCandidate(
        comment_text="この本文はP4 boundary metaへ保存しない。",
        composer_source="ai_generated",
        status="generated",
        composer_model=(
            POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
            if post_final
            else GATE_RECOVERY_MATERIAL_SURFACE_MODEL
        ),
        generation_method=(
            POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
            if post_final
            else GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
        ),
        composer_meta=meta,
    )


def test_p4_reply_service_blocks_pre_public_gate_recovery_material_surface_adoption() -> None:
    result = _result_for_candidate(_diagnostic_candidate())

    decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
        composer_client_resolution=SimpleNamespace(
            rejection_reasons=["default_limited_composer_feature_disabled"]
        ),
    )
    meta = reply_service._build_reply_service_gate_recovery_public_boundary_meta(
        recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
        gate_recovery_loop_result=result,
        public_boundary_decision=decision,
        adopted=False,
    )

    assert decision["public_display_allowed"] is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in decision["blockers"]
    assert BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION in decision["blockers"]
    assert meta["public_display_allowed"] is False
    assert meta["adopted"] is False
    assert meta["blocked"] is True
    assert meta["comment_text_body_included"] is False
    assert meta["raw_input_included"] is False
    assert "comment_text" not in meta
    assert "comment_text" not in meta["gate_recovery_loop_result"]


def test_p4_reply_service_blocks_post_final_gate_recovery_material_surface_adoption() -> None:
    result = _result_for_candidate(_diagnostic_candidate(post_final=True))

    decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    )
    meta = reply_service._build_reply_service_gate_recovery_public_boundary_meta(
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        gate_recovery_loop_result=result,
        public_boundary_decision=decision,
        adopted=False,
    )
    post_final_meta = reply_service._build_phase20_13_post_final_gate_recovery_meta(
        attempted=True,
        applied=False,
        original_final_status="rejected",
        final_status_after_recovery="rejected",
        response_kind="normal_observation",
        material_quality="eligible",
        recovery_policy="post_final_gate_recovery_loop",
        from_gate="final_pre_return_gate",
        blocked_reasons=decision["blockers"],
        public_boundary_meta=meta,
    )

    assert decision["public_display_allowed"] is False
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in decision["blockers"]
    assert meta["adopted"] is False
    assert post_final_meta["applied"] is False
    assert post_final_meta["public_boundary_checked"] is True
    assert post_final_meta["public_boundary_blocked"] is True
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in post_final_meta["public_boundary_blockers"]
    assert post_final_meta["comment_text_body_included"] is False
    assert post_final_meta["raw_input_included"] is False


def test_p4_reply_service_decision_uses_surface_binding_meta_when_candidate_meta_is_missing() -> None:
    surface_binding = build_gate_recovery_surface_binding_meta(
        material_quality="eligible",
        visible_slots=("relationship",),
        unknown_slots=("cause",),
        relation_ids=("relationship_material",),
        policy="shorten_surface",
    )
    candidate = ConversationComposerCandidate(
        comment_text="candidate body must not be copied into P4 meta",
        composer_source="ai_generated",
        status="generated",
        composer_model="",
        generation_method="",
        composer_meta={},
    )
    result = _result_for_candidate(candidate, surface_binding_meta=surface_binding)

    decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    )

    assert decision["public_display_allowed"] is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in decision["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in decision["blockers"]
    assert decision["contract_flags"]["comment_text_body_included"] is False


def test_p4_reply_service_allows_rebuilt_public_observation_candidate() -> None:
    candidate = ConversationComposerCandidate(
        comment_text="この本文はP4 decisionへ保存しない。",
        composer_source="low_information_observation_composer",
        status="generated",
        composer_model="low_information_observation_composer_recovery",
        generation_method="low_information_observation_recovery",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "candidate_lineage": {
                "original_candidate_source": "low_information_observation_composer",
                "public_candidate_rebuilt_after_recovery": True,
            },
        },
    )
    result = _result_for_candidate(candidate)

    decision = reply_service._reply_service_gate_recovery_public_boundary_decision(
        result,
        recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    )
    meta = reply_service._build_reply_service_gate_recovery_public_boundary_meta(
        recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
        gate_recovery_loop_result=result,
        public_boundary_decision=decision,
        adopted=True,
    )

    assert decision["public_display_allowed"] is True
    assert decision["blockers"] == []
    assert meta["public_display_allowed"] is True
    assert meta["adopted"] is True
    assert meta["blocked"] is False
    assert meta["comment_text_body_included"] is False


@pytest.mark.asyncio
async def test_p4_runtime_does_not_adopt_leaky_pre_public_recovery_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in _COMPOSER_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    leaked_result = _result_for_candidate(_diagnostic_candidate())

    def fake_recover_emlis_gate_failure(**_kwargs: Any) -> GateRecoveryLoopResult:
        return leaked_result

    monkeypatch.setattr(reply_service, "recover_emlis_gate_failure", fake_recover_emlis_gate_failure)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="p4-runtime-boundary-user",
        subscription_tier="free",
        current_input={
            "memo": "今日は仕事の予定変更で気持ちが追いつかなかった。",
            "memo_action": "帰ってからも少し考え続けていた。",
            "emotions": ["不安"],
            "category": ["仕事"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "")
    meta = getattr(reply, "meta", {}) or {}
    boundary_meta = meta.get("phase20_5_gate_recovery_public_boundary") or {}

    assert leaked_result.applied is True
    assert "Gate Recovery diagnostic body" not in comment_text
    assert boundary_meta["public_display_allowed"] is False
    assert boundary_meta["adopted"] is False
    assert boundary_meta["blocked"] is True
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in boundary_meta["blocked_reasons"]
    assert boundary_meta["comment_text_body_included"] is False
    assert boundary_meta["raw_input_included"] is False
    assert "comment_text" not in boundary_meta
    phase_gate = meta.get("phase_gate") or {}
    if phase_gate:
        assert phase_gate["phase20_5_reply_service_gate_recovery_public_boundary_checked"] is True
        assert phase_gate["phase20_5_reply_service_gate_recovery_public_boundary_blocked"] is True
        assert phase_gate["phase20_5_reply_service_gate_recovery_adopted"] is False
