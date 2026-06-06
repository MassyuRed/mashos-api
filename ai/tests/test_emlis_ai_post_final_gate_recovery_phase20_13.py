# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-13 post-final gate recovery regression tests.

These tests pin the P3/P6 public-boundary behavior for the Phase20-13
post-final recovery path: Gate Recovery material surfaces may be recorded as
meta-only diagnostic recovery evidence, but they must not be promoted directly
to public ``passed + comment_text``.  Low-information recovery and P8
``normal_observation_rebuild_candidate`` may pass only as rebuilt public
observation candidates through the existing Gates.
"""

from collections.abc import Mapping
from typing import Any
import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
)
from emlis_ai_observation_eligibility_router import EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
)
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY, ResponseKind
from emlis_ai_safety_triage import EMLIS_SAFETY_TRIAGE_META_KEY, TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import DisplayDecision, GreetingDecision


_PHASE20_13_ENV_KEYS = (
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
)

_FORCED_FINAL_VISIBLE_GATE_REJECTION = "phase20_13_forced_final_visible_gate_rejection"
_POST_FINAL_META_KEY = "phase20_13_post_final_gate_recovery"
_PUBLIC_FORBIDDEN_EXACT_KEYS = {
    "response_kind",
    "safety_triage_kind",
    "material_quality",
    "observation_text",
    "reception_text",
    "raw_input",
    "raw_text",
    "comment_text_body",
    "comment_text",
}

_PUBLIC_FALSE_BOUNDARY_FLAGS = {
    "raw_input_included",
    "raw_text_included",
    "comment_text_body_included",
    "comment_text_included",
}

_NORMAL_INPUT = {
    "memo": "今日は仕事で予定が急に変わって、気持ちの置き場がなくなった。",
    "memo_action": "予定変更の連絡を受けて、帰ってからも考え続けていた。",
    "emotions": ["不安"],
    "category": ["仕事"],
}
_LOW_INFORMATION_INPUT = {
    "memo": "なんか今日は全部だるい。\n何もしたくない。",
    "memo_action": "",
    "emotions": ["悲しみ", "不安"],
    "category": ["生活"],
}
_LIMITED_GROUNDING_INPUT = {
    "memo": "今、不安が強い。",
    "memo_action": "",
    "emotions": ["不安"],
    "category": ["仕事"],
}
_SELF_DENIAL_INPUT = {
    "memo": "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
    "memo_action": "",
    "emotions": ["悲しみ"],
    "category": ["人生", "価値観"],
}
_EMERGENCY_INPUT = {
    "memo": "もう死にたい。自分を傷つけたい衝動がある。",
    "memo_action": "",
    "emotions": ["悲しみ"],
    "category": ["人生"],
}


@pytest.fixture(autouse=True)
def _patch_source_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="phase20-13-post-final-gate-recovery",
            slot_key="phase20-13-post-final-gate-recovery",
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


@pytest.fixture()
def phase20_13_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _PHASE20_13_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _public_meta(reply: Any) -> dict[str, Any]:
    return build_public_emlis_input_feedback_meta(
        _mapping(getattr(reply, "meta", {})),
        comment_text_present=bool(str(getattr(reply, "comment_text", "") or "").strip()),
        subscription_tier="free",
    )


def _internal_contract(reply: Any) -> Mapping[str, Any]:
    return _mapping(_mapping(getattr(reply, "meta", {})).get(EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY))


def _material_route(reply: Any) -> Mapping[str, Any]:
    return _mapping(_mapping(getattr(reply, "meta", {})).get(EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY))


def _safety_triage(reply: Any) -> Mapping[str, Any]:
    return _mapping(_mapping(getattr(reply, "meta", {})).get(EMLIS_SAFETY_TRIAGE_META_KEY))


def _post_final_recovery_meta(reply: Any) -> Mapping[str, Any]:
    meta = _mapping(getattr(reply, "meta", {}))
    direct = _mapping(meta.get(_POST_FINAL_META_KEY))
    if direct:
        return direct
    diagnostic = _mapping(meta.get("diagnostic_summary"))
    return _mapping(diagnostic.get(_POST_FINAL_META_KEY))


def _force_first_nonempty_visible_surface_recheck_failure(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    original = reply_service._build_visible_surface_acceptance_report_for_candidate
    state: dict[str, Any] = {
        "forced": False,
        "nonempty_candidate_seen": False,
        "forced_reasons": [],
    }

    def wrapped_visible_surface_report(**kwargs: Any) -> dict[str, Any]:
        report = dict(original(**kwargs))
        comment_text = str(kwargs.get("comment_text") or "").strip()
        if not comment_text:
            return report
        state["nonempty_candidate_seen"] = True
        if state["forced"]:
            return report
        state["forced"] = True
        state["forced_reasons"] = [_FORCED_FINAL_VISIBLE_GATE_REJECTION]
        report.update(
            {
                "evaluated": True,
                "passed": False,
                "blocked": True,
                "classification": "repair_required",
                "action": "rerender_surface",
                "rerender_recommended": True,
                "surface_repair_requested": True,
                "rejection_reasons": [_FORCED_FINAL_VISIBLE_GATE_REJECTION],
                "repair_reason_family": "phase20_13_final_pre_return_probe",
                "display_gate_relaxed": False,
                "safety_gate_relaxed": False,
                "grounding_gate_relaxed": False,
                "template_gate_relaxed": False,
                "fixed_fallback_used": False,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "public_response_key_change": False,
            }
        )
        return report

    monkeypatch.setattr(
        reply_service,
        "_build_visible_surface_acceptance_report_for_candidate",
        wrapped_visible_surface_report,
    )
    return state


def _force_second_nonempty_visible_surface_recheck_failure(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    original = reply_service._build_visible_surface_acceptance_report_for_candidate
    state: dict[str, Any] = {
        "forced": False,
        "forced_count": 0,
        "nonempty_candidate_seen": False,
        "nonempty_call_count": 0,
        "forced_reasons": [],
        "calls": [],
    }

    def wrapped_visible_surface_report(**kwargs: Any) -> dict[str, Any]:
        report = dict(original(**kwargs))
        comment_text = str(kwargs.get("comment_text") or "").strip()
        if not comment_text:
            return report
        state["nonempty_candidate_seen"] = True
        state["nonempty_call_count"] = int(state.get("nonempty_call_count") or 0) + 1
        state["calls"].append(
            {
                "index": state["nonempty_call_count"],
                "rerender_attempted": bool(kwargs.get("rerender_attempted")),
                "status_passed_before_force": bool(report.get("passed")),
                "rejection_reasons_before_force": list(report.get("rejection_reasons") or []),
                "classification_before_force": str(report.get("classification") or ""),
                "action_before_force": str(report.get("action") or ""),
                "comment_text_prefix": comment_text[:32],
                "composer_model": str(getattr(kwargs.get("composer_candidate"), "composer_model", "") or ""),
            }
        )
        composer_model = str(getattr(kwargs.get("composer_candidate"), "composer_model", "") or "")
        if (
            composer_model != _Phase20_13NormalObservationComposerClient.composer_model
            or state["nonempty_call_count"] not in {2, 3}
        ):
            return report
        state["forced"] = True
        state["forced_count"] = int(state.get("forced_count") or 0) + 1
        state["forced_reasons"] = [
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
            "surface_grammar_warning",
            _FORCED_FINAL_VISIBLE_GATE_REJECTION,
        ]
        report.update(
            {
                "evaluated": True,
                "passed": False,
                "blocked": True,
                "classification": "repair_required",
                "action": "rerender_surface",
                "rerender_recommended": True,
                "surface_repair_requested": True,
                "rejection_reasons": list(state["forced_reasons"]),
                "repair_reason_family": "surface_relation_skeleton_major",
                "display_gate_relaxed": False,
                "safety_gate_relaxed": False,
                "grounding_gate_relaxed": False,
                "template_gate_relaxed": False,
                "fixed_fallback_used": False,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "public_response_key_change": False,
            }
        )
        return report

    monkeypatch.setattr(
        reply_service,
        "_build_visible_surface_acceptance_report_for_candidate",
        wrapped_visible_surface_report,
    )
    return state


def _force_initial_phase20_13_normal_display_decision_pass(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Let the custom normal candidate reach final pre-return in this test only.

    The fixture source bundle is intentionally sparse, so the first display
    decision can fail before the final pre-return gate. P6 needs to isolate the
    post-final branch, so this helper simulates the pre-final display pass once
    for the custom ai_generated candidate without changing production gates.
    """

    original = reply_service.decide_emlis_observation_display
    state: dict[str, Any] = {"forced_initial_pass": False}

    def wrapped_decide(**kwargs: Any) -> Any:
        decision = original(**kwargs)
        comment_text = str(kwargs.get("comment_text") or "").strip()
        if (
            not state["forced_initial_pass"]
            and comment_text.startswith("この記録では、仕事の予定が急に変わったあと")
            and str(getattr(decision, "observation_status", "") or "") != "passed"
        ):
            state["forced_initial_pass"] = True
            return DisplayDecision(
                observation_status="passed",
                comment_text=comment_text,
                rejection_reasons=[],
                trace_id=str(kwargs.get("trace_id") or "phase20-13-normal-initial-pass-probe"),
            )
        return decision

    monkeypatch.setattr(reply_service, "decide_emlis_observation_display", wrapped_decide)
    return state


class _Phase20_13NormalObservationComposerClient:
    composer_model = "phase20_13_normal_observation_post_final_test_client.v1"

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        evidence_ids = [
            str(item.get("span_id") or "").strip()
            for item in list(payload.get("evidence_spans") or [])
            if isinstance(item, Mapping) and str(item.get("span_id") or "").strip()
        ]
        return {
            "comment_text": (
                "この記録では、仕事の予定が急に変わったあと、不安がまだ落ち着ききっていない状態として見えます。"
                "帰ってからも考え続けていて、気持ちの置き場を探している感じが残っています。"
            ),
            "composer_source": "ai_generated",
            "response_schema_version": "cocolon.emlis.phase20_13.normal_observation.test_response.v1",
            "composer_model": self.composer_model,
            "generation_method": "phase20_13_normal_observation_ai_generated_candidate",
            "coverage_scope": "current_input_only",
            "generation_scope": "current_input_only",
            "confidence": 0.91,
            "used_evidence_span_ids": evidence_ids[:3],
            "used_claim_ids": ["claim_phase20_13_normal_observation"],
            "used_relation_ids": ["work_schedule_change_state"],
            "fixed_string_renderer_used": False,
            "composer_meta": {
                "candidate_source_kind": "complete_initial_composer",
                "public_surface_role": "public_observation_candidate",
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_lineage": {
                    "original_candidate_present": False,
                    "original_candidate_source": "complete_initial_composer",
                    "recovery_plan_used": False,
                    "diagnostic_surface_used": False,
                    "public_candidate_rebuilt_after_recovery": False,
                },
                "two_stage_section_surface_plan": {
                    "required": False,
                    "source_phase": "Phase20-13_NormalObservation_PostFinal_Test",
                    "phase20_13_plain_surface_for_post_final_probe": True,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                },
            },
        }


def _assert_public_contract_unchanged(reply: Any) -> None:
    public_meta = _public_meta(reply)

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                assert key not in _PUBLIC_FORBIDDEN_EXACT_KEYS
                if key in _PUBLIC_FALSE_BOUNDARY_FLAGS:
                    assert item is False
                walk(item)
            return
        if isinstance(value, list):
            for item in value:
                walk(item)

    walk(public_meta)
    assert public_meta.get("observation_text") is None
    assert public_meta.get("reception_text") is None


def _assert_gate_recovery_material_surface_not_public(
    reply: Any,
    *,
    expected_material_quality: str,
    expected_response_kinds: set[str],
) -> None:
    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    public_meta = _public_meta(reply)
    internal = _internal_contract(reply)
    material_route = _material_route(reply)
    post_final = _post_final_recovery_meta(reply)

    assert comment_text == ""
    assert should_include_public_input_feedback(comment_text, public_meta) is False
    assert public_meta.get("observation_status") != "passed"
    assert internal.get("response_kind") in expected_response_kinds
    assert material_route.get("material_quality") == expected_material_quality
    assert "今回の入力では" not in comment_text
    assert "Emlisから：" not in comment_text

    if post_final:
        assert post_final.get("schema_version") == "cocolon.emlis.post_final_gate_recovery.v1"
        assert post_final.get("source_phase") == "Phase20-13_Post_Final_Gate_Recovery"
        assert post_final.get("attempted") is True
        assert post_final.get("applied") is False
        assert post_final.get("attempt_count") == 1
        assert post_final.get("final_status_after_recovery") != "passed"
        assert post_final.get("from_gate") in {
            "final_pre_return_gate",
            "final_visible_surface_acceptance_gate",
        }
        assert "post_final_gate_recovery_material_surface_public_leak" in post_final.get("blocked_reasons", [])
        assert "gate_recovery_diagnostic_surface_promoted_to_public" in post_final.get("blocked_reasons", [])
        assert post_final.get("display_gate_relaxed") is False
        assert post_final.get("safety_gate_relaxed") is False
        assert post_final.get("grounding_gate_relaxed") is False
        assert post_final.get("template_gate_relaxed") is False
        assert post_final.get("fixed_fallback_used") is False
        assert post_final.get("public_response_key_change") is False
        assert post_final.get("comment_text_body_included") is False
        assert post_final.get("raw_input_included") is False
        assert post_final.get("empty_comment_text_exit_allowed") is False
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_normal_observation_does_not_promote_gate_recovery_surface(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-normal-user",
        subscription_tier="free",
        current_input=dict(_NORMAL_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    assert forced_gate["forced"] is False
    _assert_gate_recovery_material_surface_not_public(
        reply,
        expected_material_quality=MATERIAL_QUALITY_ELIGIBLE,
        expected_response_kinds={ResponseKind.INFRASTRUCTURE_ERROR.value},
    )


@pytest.mark.asyncio
async def test_phase20_13_low_information_post_final_recovery_uses_p6_low_information_composer(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-low-information-user",
        subscription_tier="free",
        current_input=dict(_LOW_INFORMATION_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    public_meta = _public_meta(reply)
    internal = _internal_contract(reply)
    material_route = _material_route(reply)
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    assert comment_text
    assert should_include_public_input_feedback(comment_text, public_meta) is True
    assert public_meta.get("observation_status") == "passed"
    assert internal.get("response_kind") == ResponseKind.LOW_INFORMATION_OBSERVATION.value
    assert material_route.get("material_quality") == MATERIAL_QUALITY_LOW_INFORMATION
    assert post_final.get("schema_version") == "cocolon.emlis.post_final_gate_recovery.v1"
    assert post_final.get("attempted") is True
    assert post_final.get("applied") is True
    assert post_final.get("final_status_after_recovery") == "passed"
    assert post_final.get("public_boundary_checked") is True
    assert post_final.get("public_boundary_blocked") is False
    assert post_final.get("public_display_allowed_by_boundary") is True
    boundary = _mapping(post_final.get("gate_recovery_public_boundary_decision"))
    assert boundary.get("candidate_source_kind") == "low_information_observation_composer"
    assert boundary.get("composer_model") == "low_information_observation_composer_recovery"
    assert boundary.get("public_surface_role") == "public_observation_candidate"
    assert boundary.get("public_display_allowed") is True
    assert boundary.get("blockers") == []
    assert "post_final_gate_recovery_material_surface_public_leak" not in post_final.get("blocked_reasons", [])
    assert "gate_recovery_diagnostic_surface_promoted_to_public" not in post_final.get("blocked_reasons", [])
    assert "今回の入力では" not in comment_text
    assert "Emlisから：" not in comment_text
    assert "原因や結論までは" not in comment_text
    assert "誰かを良い悪い" not in comment_text
    assert "何があったか" in comment_text
    assert _LOW_INFORMATION_INPUT["memo"].split("\n", maxsplit=1)[0] not in comment_text
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_normal_observation_post_final_recovery_uses_normal_rebuild_candidate(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_second_nonempty_visible_surface_recheck_failure(monkeypatch)
    initial_display_probe = _force_initial_phase20_13_normal_display_decision_pass(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-normal-observation-post-final-rebuild-user",
        subscription_tier="free",
        current_input=dict(_NORMAL_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_Phase20_13NormalObservationComposerClient(),
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    public_meta = _public_meta(reply)
    internal = _internal_contract(reply)
    material_route = _material_route(reply)
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["nonempty_call_count"] >= 2
    assert forced_gate["forced"] is True
    assert forced_gate["forced_count"] == 2, forced_gate
    assert initial_display_probe["forced_initial_pass"] is True
    assert comment_text
    assert should_include_public_input_feedback(comment_text, public_meta) is True
    assert public_meta.get("observation_status") == "passed"
    assert internal.get("response_kind") == ResponseKind.NORMAL_OBSERVATION.value
    assert material_route.get("material_quality") == MATERIAL_QUALITY_ELIGIBLE

    assert post_final.get("schema_version") == "cocolon.emlis.post_final_gate_recovery.v1"
    assert post_final.get("attempted") is True
    assert post_final.get("applied") is True
    assert post_final.get("attempt_count") == 1
    assert post_final.get("final_status_after_recovery") == "passed"
    assert post_final.get("public_boundary_checked") is True
    assert post_final.get("public_boundary_blocked") is False
    assert post_final.get("public_display_allowed_by_boundary") is True
    assert post_final.get("public_candidate_source_kind") == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert post_final.get("normal_observation_rebuild_attempted") is True
    assert post_final.get("normal_observation_rebuild_applied") is True
    assert post_final.get("normal_observation_rebuild_source_kind") == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )

    boundary = _mapping(post_final.get("gate_recovery_public_boundary_decision"))
    assert boundary.get("candidate_source_kind") == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert boundary.get("composer_model") == "normal_observation_rebuild_candidate_v1"
    assert boundary.get("public_surface_role") == "public_observation_candidate"
    assert boundary.get("public_display_allowed") is True
    assert boundary.get("blockers") == []

    assert "post_final_gate_recovery_material_surface_public_leak" not in post_final.get("blocked_reasons", [])
    assert "gate_recovery_diagnostic_surface_promoted_to_public" not in post_final.get("blocked_reasons", [])
    assert _NORMAL_INPUT["memo"] not in comment_text
    for fragment in (
        "同じ流れ",
        "同じ場所",
        "片方だけに減らさず",
        "状態が一色ではありません",
        "今回の入力では",
        "原因や結論までは",
        "誰かを良い悪い",
        "Emlisから：",
        "見えたこと：",
    ):
        assert fragment not in comment_text
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_limited_grounding_uses_p6_low_information_composer_not_material_surface(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-limited-grounding-user",
        subscription_tier="free",
        current_input=dict(_LIMITED_GROUNDING_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    public_meta = _public_meta(reply)
    internal = _internal_contract(reply)
    material_route = _material_route(reply)
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    assert comment_text
    assert should_include_public_input_feedback(comment_text, public_meta) is True
    assert public_meta.get("observation_status") == "passed"
    assert internal.get("response_kind") == ResponseKind.LIMITED_GROUNDING_OBSERVATION.value
    assert material_route.get("material_quality") == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert post_final.get("attempted") is True
    assert post_final.get("applied") is True
    assert post_final.get("final_status_after_recovery") == "passed"
    if post_final.get("public_boundary_checked") is not None:
        assert post_final.get("public_boundary_blocked") is False
        assert post_final.get("public_display_allowed_by_boundary") is True
        boundary = _mapping(post_final.get("gate_recovery_public_boundary_decision"))
        assert boundary.get("candidate_source_kind") == "low_information_observation_composer"
        assert boundary.get("composer_model") == "low_information_observation_composer_recovery"
        assert boundary.get("public_display_allowed") is True
        assert boundary.get("blockers") == []
    assert "post_final_gate_recovery_material_surface_public_leak" not in post_final.get("blocked_reasons", [])
    assert "gate_recovery_diagnostic_surface_promoted_to_public" not in post_final.get("blocked_reasons", [])
    assert "今回の入力では" not in comment_text
    assert "Emlisから：" not in comment_text
    assert "原因や結論までは" not in comment_text
    assert "誰かを良い悪い" not in comment_text
    assert "何があったか" in comment_text
    assert "原因は" not in comment_text
    assert "あなたは" not in comment_text
    assert "診断" not in comment_text
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_self_denial_prefers_safe_state_answer_over_generic_post_final_recovery(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-self-denial-user",
        subscription_tier="free",
        current_input=dict(_SELF_DENIAL_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    meta = _mapping(getattr(reply, "meta", {}))
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["nonempty_candidate_seen"] is True
    assert forced_gate["forced"] is True
    assert comment_text
    assert meta.get("observation_status") == "passed"
    assert _internal_contract(reply).get("response_kind") == ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER.value
    assert should_include_public_input_feedback(comment_text, _public_meta(reply)) is True
    assert not post_final or post_final.get("applied") is not True
    assert "あなたが悪い" not in comment_text
    assert "事実です" not in comment_text
    _assert_public_contract_unchanged(reply)


@pytest.mark.asyncio
async def test_phase20_13_safety_emergency_does_not_run_post_final_recovery_or_become_observation(
    phase20_13_env: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    forced_gate = _force_first_nonempty_visible_surface_recheck_failure(monkeypatch)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="phase20-13-safety-emergency-user",
        subscription_tier="free",
        current_input=dict(_EMERGENCY_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    comment_text = str(getattr(reply, "comment_text", "") or "").strip()
    meta = _mapping(getattr(reply, "meta", {}))
    public_meta = _public_meta(reply)
    post_final = _post_final_recovery_meta(reply)

    assert forced_gate["forced"] is False
    assert comment_text == ""
    assert meta.get("observation_status") == "safety_blocked"
    assert _internal_contract(reply).get("response_kind") == ResponseKind.SAFETY_BLOCKED_EMERGENCY.value
    assert _safety_triage(reply).get("requires_block") is True
    assert should_include_public_input_feedback(comment_text, public_meta) is False
    assert public_meta.get("observation_status") != "passed"
    assert not post_final or post_final.get("attempted") is not True
    _assert_public_contract_unchanged(reply)
