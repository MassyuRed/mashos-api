# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from types import SimpleNamespace
from typing import Any

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
import emotion_submit_service as submit_service
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_types import GreetingDecision

_COMPLETE_INITIAL_ENV = {
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
    "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_initial",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE": "all",
}
_COMPLETE_INITIAL_ENV_KEYS = (
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
_LOW_INFORMATION_ENV_KEYS = (
    "COCOLON_EMLIS_OBSERVATION_ROUTER_ENABLED",
    "COCOLON_EMLIS_LOW_INFORMATION_OBSERVATION_ENABLED",
    "COCOLON_EMLIS_USER_FACT_GROUNDING_BOUNDARY_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_SENTENCE_ROLES_ENABLED",
)
_SECRET_RAW_INPUT = "これはPhase18-9でpublic responseへ出してはいけない入力本文です"
_SECRET_EVIDENCE = "これはPhase18-9でpublic responseへ出してはいけない根拠全文です"
_SECRET_INTERNAL_COMMENT = "これはPhase18-9でpublic metaへ混ぜてはいけない内部comment_textです"
_VISIBLE_TWO_STAGE_COMMENT = "見えたこと：\n不安と迷いが同時に残っているように見えます。\n\nEmlisから：\n急いで結論にしなくても、今はその揺れをそのまま置いてよさそうです。"


def _clear_emlis_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*_COMPLETE_INITIAL_ENV_KEYS, *_LOW_INFORMATION_ENV_KEYS):
        monkeypatch.delenv(name, raising=False)


def _enable_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_emlis_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)


def _patch_submit_persistence(monkeypatch: pytest.MonkeyPatch, *, inserted_id: str = "phase18-9-emotion-log") -> None:
    async def fake_insert_emotion_row(**kwargs: Any) -> dict[str, Any]:
        return {
            "id": inserted_id,
            "created_at": str(kwargs.get("created_at") or "2026-05-30T00:00:00.000000+00:00"),
        }

    async def fake_invalidate_prefix(_prefix: str) -> None:
        return None

    async def fake_subscription_tier_for_user(*_args: Any, **_kwargs: Any) -> str:
        return "free"

    monkeypatch.setattr(submit_service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(submit_service, "invalidate_prefix", fake_invalidate_prefix)
    monkeypatch.setattr(submit_service, "_global_summary_activity_date_from_created_at", lambda _created_at: "2026-05-30")
    monkeypatch.setattr(submit_service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(submit_service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)


def _patch_real_reply_source_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="phase18-9-product-quality",
            slot_key="phase18-9-product-quality",
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

    async def actual_render(**kwargs: Any):
        return await reply_service.render_emlis_ai_reply(
            **kwargs,
            display_name="Mash",
            timezone_name="Asia/Tokyo",
        )

    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", actual_render)


def _public_response_body(result: Mapping[str, Any]) -> dict[str, Any]:
    comment_text = str(result.get("input_feedback_comment") or "").strip()
    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else None
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {"comment_text": comment_text, "emlis_ai": dict(public_meta or {})}
    inserted = result.get("inserted") if isinstance(result.get("inserted"), Mapping) else {}
    return {
        "status": "ok",
        "id": inserted.get("id"),
        "created_at": str(result.get("created_at") or ""),
        "input_feedback": feedback,
    }


def _walk_values(value: Any) -> list[Any]:
    out: list[Any] = []

    def rec(item: Any) -> None:
        if isinstance(item, Mapping):
            for child in item.values():
                rec(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for child in item:
                rec(child)
        else:
            out.append(item)

    rec(value)
    return out


def _contains_text_recursive(value: Any, needle: str) -> bool:
    target = " ".join(str(needle or "").split())
    if not target:
        return False
    for item in _walk_values(value):
        if isinstance(item, str) and target in " ".join(item.split()):
            return True
    return False


def _assert_public_response_shape_unchanged(body: Mapping[str, Any]) -> None:
    assert set(body.keys()) == {"status", "id", "created_at", "input_feedback"}
    assert "observation_text" not in body
    assert "reception_text" not in body
    feedback = body.get("input_feedback")
    if feedback is not None:
        assert isinstance(feedback, Mapping)
        assert set(feedback.keys()) == {"comment_text", "emlis_ai"}
        assert "observation_text" not in feedback
        assert "reception_text" not in feedback


def _assert_public_meta_is_boundary_safe(public_meta: Mapping[str, Any], *, comment_text: str, forbidden_fragments: Sequence[str]) -> None:
    dumped = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    for forbidden_key in (
        '"raw_input"',
        '"raw_text"',
        '"current_input"',
        '"surface_policy"',
        '"evidence_spans"',
        '"complete_reply_service_diagnostics"',
        '"multi_perspective"',
        '"candidate_comment_text"',
        '"generated_candidate_text"',
    ):
        assert forbidden_key not in dumped
    for fragment in forbidden_fragments:
        if str(fragment or "").strip():
            assert fragment not in dumped
    assert not _contains_text_recursive(public_meta, comment_text)
    boundary = public_meta["public_feedback_meta_boundary"]
    assert boundary["sanitized"] is True
    assert boundary["internal_meta_returned"] is False
    assert boundary["raw_input_included"] is False
    assert boundary["comment_text_included"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "memo,emotions,expected_fragment",
    [
        ("疲れた", ["疲れ"], "疲れの重さ"),
        ("なんか無理", ["疲れ"], "無理かもしれない感じ"),
        ("大丈夫かどうか不安", ["不安"], "大丈夫かどうか"),
    ],
)
async def test_phase18_9_emotion_submit_low_information_cases_return_public_feedback_without_contract_change(
    monkeypatch: pytest.MonkeyPatch,
    memo: str,
    emotions: list[str],
    expected_fragment: str,
) -> None:
    _clear_emlis_flags(monkeypatch)
    _patch_submit_persistence(monkeypatch, inserted_id=f"phase18-9-low-info-{abs(hash(memo))}")
    _patch_real_reply_source_bundle(monkeypatch)

    result = await submit_service.persist_emotion_submission(
        user_id="phase18-9-low-information-user",
        emotions=emotions,
        memo=memo,
        memo_action="",
        category=["生活"],
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    body = _public_response_body(result)

    _assert_public_response_shape_unchanged(body)
    assert body["input_feedback"] is not None
    feedback = body["input_feedback"]
    comment_text = feedback["comment_text"]
    public_meta = feedback["emlis_ai"]

    assert expected_fragment in comment_text
    assert public_meta["schema_version"] == "emlis.public_input_feedback_meta.v1"
    assert public_meta["observation_status"] == "passed"
    assert public_meta["observation_reply_meta"]["observation_reply_kind"] == "low_information_observation"
    assert public_meta["observation_reply_meta"]["question_required"] is True
    step10 = public_meta["step10_observation_display_repair_integration"]
    assert step10["applied"] is True
    assert step10["final_observation_status"] == "passed"
    assert step10["observation_reply_kind"] == "low_information_observation"
    assert step10["public_status_extended"] is False
    assert step10["rn_visible_contract_changed"] is False
    assert step10["display_gate_relaxed"] is False
    assert public_meta["submit_speed_regression"]["public_feedback_included"] is True
    assert public_meta["submit_speed_regression"]["saved_emotion_success"] is True
    assert public_meta["submit_speed_regression"]["comment_text_body_included"] is False
    assert public_meta["submit_speed_regression"]["public_response_key_added"] is False
    assert public_meta["submit_speed_regression"]["rn_visible_contract_changed"] is False
    _assert_public_meta_is_boundary_safe(public_meta, comment_text=comment_text, forbidden_fragments=[memo])


@pytest.mark.asyncio
async def test_phase18_9_emotion_submit_complete_initial_generated_but_rejected_is_not_rn_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_emlis_flags(monkeypatch)
    raw_memo = "疲れているけれど、少し整えたい気持ちもある。"
    _patch_submit_persistence(monkeypatch, inserted_id="phase18-9-complete-initial-rejected")
    captured_diagnostic_meta: dict[str, Any] = {}

    def capture_diagnostic_lockdown(**kwargs: Any) -> None:
        captured_diagnostic_meta.update(dict(kwargs.get("input_feedback_meta") or {}))

    async def fake_render_reply(**_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            comment_text="この候補本文はrejectedなのでpublic responseへ出してはいけません",
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "observation_status": "rejected",
                "observation_trace_id": "phase18-9-complete-initial-generated-rejected",
                "rejection_reasons": ["relation_not_expressed"],
                "diagnostic_summary": {
                    "stage": "reader",
                    "primary_reason": "relation_not_expressed",
                    "coverage_group": "energy_fatigue",
                    "composer_status": "generated",
                    "composer_source": "ai_generated",
                    "gate_results": {
                        "reader": {"passed": False, "primary_reason": "relation_not_expressed"},
                        "grounding": {"passed": True, "primary_reason": "passed"},
                        "template_echo": {"passed": True, "primary_reason": "passed"},
                        "display": {"passed": False, "primary_reason": "relation_not_expressed"},
                    },
                    "display_absence_summary": {
                        "candidate_fail_closed_display_absent": True,
                        "public_feedback_not_included_non_passed": True,
                        "public_feedback_not_included_empty_comment_text": True,
                        "rn_payload_absent": True,
                        "reason_family": "empty_comment_text",
                        "reason_codes": ["relation_not_expressed"],
                    },
                    "complete_initial_candidate_generation_path": {
                        "phase18_candidate_path_contract_version": "cocolon.emlis.complete_initial.candidate_path.v2",
                        "candidate_generation_attempted": True,
                        "complete_composer_client_generate_called": True,
                        "candidate_generated": True,
                        "candidate_generated_before_display_gate": True,
                        "candidate_status": "generated",
                        "candidate_status_before_display_gate": "generated",
                        "candidate_status_after_display_gate": "rejected",
                        "candidate_comment_text_present": True,
                        "public_comment_text_present": False,
                        "non_passed_comment_text_empty": True,
                        "passed_only_comment_text_contract_preserved": True,
                        "display_gate_relaxed": False,
                        "grounding_gate_relaxed": False,
                        "raw_input_included": False,
                        "generated_candidate_text_included": False,
                    },
                },
            },
        )

    monkeypatch.setattr(submit_service, "_log_emlis_ai_observation_diagnostic_lockdown", capture_diagnostic_lockdown)
    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", fake_render_reply)

    result = await submit_service.persist_emotion_submission(
        user_id="phase18-9-complete-initial-user",
        emotions=["自己理解"],
        memo=raw_memo,
        memo_action="",
        category=["生活"],
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    body = _public_response_body(result)
    public_meta = result["input_feedback_meta"]

    _assert_public_response_shape_unchanged(body)
    assert body["input_feedback"] is None
    assert result["input_feedback_comment"] == ""
    assert public_meta["observation_status"] == "rejected"
    assert public_meta["diagnostic_summary"]["composer_status"] == "generated"
    assert public_meta["diagnostic_summary"]["display_absence_summary"]["rn_payload_absent"] is True
    assert public_meta["submit_speed_regression"]["public_feedback_included"] is False
    assert public_meta["submit_speed_regression"]["saved_emotion_success"] is True
    assert public_meta["submit_speed_regression"]["emlis_display_fail_closed"] is True

    step5 = captured_diagnostic_meta["diagnostic_summary"]["complete_initial_candidate_generation_path"]
    assert step5["candidate_generation_attempted"] is True
    assert step5["complete_composer_client_generate_called"] is True
    assert step5["candidate_generated"] is True
    assert step5["candidate_status_before_display_gate"] == "generated"
    assert step5["candidate_status_after_display_gate"] == "rejected"
    assert step5["public_comment_text_present"] is False
    assert step5["non_passed_comment_text_empty"] is True
    assert step5["passed_only_comment_text_contract_preserved"] is True
    assert step5["display_gate_relaxed"] is False
    assert step5["grounding_gate_relaxed"] is False
    assert not _contains_text_recursive(public_meta, raw_memo)


@pytest.mark.asyncio
async def test_phase18_9_emotion_submit_public_meta_boundary_probe_sanitizes_internal_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_emlis_flags(monkeypatch)
    _patch_submit_persistence(monkeypatch, inserted_id="phase18-9-meta-boundary-probe")

    async def fake_render_reply(**_kwargs: Any) -> SimpleNamespace:
        return SimpleNamespace(
            comment_text=_VISIBLE_TWO_STAGE_COMMENT,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "observation_trace_id": "emlisobs-phase18-9-meta-boundary",
                "diagnostic_summary": {
                    "stage": "display",
                    "primary_reason": "passed",
                    "coverage_group": "phase18_meta_boundary_probe",
                    "composer_status": "generated",
                    "composer_source": "ai_generated",
                    "gate_results": {
                        "reader": {"passed": True, "primary_reason": "passed", "raw_text": _SECRET_RAW_INPUT},
                        "grounding": {"passed": True, "primary_reason": "passed", "evidence_spans": [{"raw_text": _SECRET_EVIDENCE}]},
                        "display": {"passed": True, "primary_reason": "passed"},
                    },
                    "surface_policy": {"definition": _SECRET_EVIDENCE, "comment_text": _SECRET_INTERNAL_COMMENT},
                    "complete_reply_service_diagnostics": {"comment_text": _SECRET_INTERNAL_COMMENT},
                },
                "visible_surface_acceptance_gate": {
                    "evaluated": True,
                    "passed": True,
                    "classification": "pass",
                    "action": "allow",
                    "surface_policy": {"notes": _SECRET_EVIDENCE},
                    "comment_text": _SECRET_INTERNAL_COMMENT,
                    "raw_input": _SECRET_RAW_INPUT,
                    "raw_text": _SECRET_EVIDENCE,
                },
                "runtime_surface_pre_return_gate": {
                    "passed": True,
                    "action": "allow",
                    "rerender_attempted": False,
                    "comment_text": _SECRET_INTERNAL_COMMENT,
                    "diagnostics": {"raw_input": _SECRET_RAW_INPUT, "raw_text": _SECRET_EVIDENCE},
                },
                "surface_policy": {"definition": _SECRET_EVIDENCE},
                "current_input": {"memo": _SECRET_RAW_INPUT},
                "raw_input": _SECRET_RAW_INPUT,
                "raw_text": _SECRET_EVIDENCE,
                "comment_text": _SECRET_INTERNAL_COMMENT,
                "evidence_spans": [{"raw_text": _SECRET_EVIDENCE}],
            },
        )

    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", fake_render_reply)

    result = await submit_service.persist_emotion_submission(
        user_id="phase18-9-meta-boundary-user",
        emotions=["不安"],
        memo=_SECRET_RAW_INPUT,
        memo_action="",
        category=["生活"],
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    body = _public_response_body(result)

    _assert_public_response_shape_unchanged(body)
    assert body["input_feedback"] is not None
    feedback = body["input_feedback"]
    public_meta = feedback["emlis_ai"]
    assert feedback["comment_text"] == _VISIBLE_TWO_STAGE_COMMENT
    assert public_meta["observation_status"] == "passed"
    assert public_meta["visible_surface_acceptance_gate"] == {
        "evaluated": True,
        "passed": True,
        "classification": "pass",
        "action": "allow",
    }
    assert public_meta["runtime_surface_pre_return_gate"] == {
        "passed": True,
        "action": "allow",
        "rerender_attempted": False,
    }
    assert public_meta["submit_speed_regression"]["public_feedback_included"] is True
    assert public_meta["submit_speed_regression"]["comment_text_body_included"] is False
    _assert_public_meta_is_boundary_safe(
        public_meta,
        comment_text=_VISIBLE_TWO_STAGE_COMMENT,
        forbidden_fragments=[_SECRET_RAW_INPUT, _SECRET_EVIDENCE, _SECRET_INTERNAL_COMMENT],
    )
    dumped_body = json.dumps(body, ensure_ascii=False, sort_keys=True)
    assert '"surface_policy"' not in dumped_body
    assert _SECRET_RAW_INPUT not in dumped_body
    assert _SECRET_EVIDENCE not in dumped_body
    assert _SECRET_INTERNAL_COMMENT not in dumped_body


@pytest.mark.asyncio
async def test_phase18_9_emotion_submit_timeout_fail_closed_keeps_saved_emotion_success_and_no_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_emlis_flags(monkeypatch)
    _patch_submit_persistence(monkeypatch, inserted_id="phase18-9-timeout")
    raw_memo = "返信timeoutでも保存は成功して表示本文は返さない入力_PHASE18_9"

    async def fake_render_reply(**_kwargs: Any) -> SimpleNamespace:
        raise asyncio.TimeoutError()

    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", fake_render_reply)

    result = await submit_service.persist_emotion_submission(
        user_id="phase18-9-timeout-user",
        emotions=["不安"],
        memo=raw_memo,
        memo_action="",
        category=["生活"],
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    body = _public_response_body(result)
    public_meta = result["input_feedback_meta"]

    _assert_public_response_shape_unchanged(body)
    assert body["input_feedback"] is None
    assert result["input_feedback_comment"] == ""
    assert public_meta["observation_status"] == "unavailable"
    assert "emlis_ai_reply_timeout" in public_meta.get("rejection_reasons", [])
    speed = public_meta["submit_speed_regression"]
    assert speed["saved_emotion_success"] is True
    assert speed["reply_timeout"] is True
    assert speed["public_feedback_included"] is False
    assert speed["emlis_display_fail_closed"] is True
    assert speed["fail_closed_reason_code"] == "emlis_ai_reply_timeout"
    assert speed["comment_text_body_included"] is False
    assert speed["public_response_key_added"] is False
    assert speed["rn_visible_contract_changed"] is False
    dumped = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert raw_memo not in dumped
    assert '"surface_policy"' not in dumped
    assert '"comment_text"' not in dumped


@pytest.mark.asyncio
async def test_phase18_9_emotion_submit_timeout_keeps_save_success_and_omits_rn_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_emlis_flags(monkeypatch)
    raw_memo = "timeout時にもpublic metaへ本文を出してはいけない入力です"
    _patch_submit_persistence(monkeypatch, inserted_id="phase18-9-timeout")
    monkeypatch.setattr(submit_service, "_emlis_ai_reply_timeout_seconds", lambda: 0.001)

    async def slow_render_reply(**_kwargs: Any) -> SimpleNamespace:
        await asyncio.sleep(0.05)
        return SimpleNamespace(
            comment_text="これはtimeout時に表示されてはいけない本文です",
            meta={"observation_status": "passed"},
        )

    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", slow_render_reply)

    result = await submit_service.persist_emotion_submission(
        user_id="phase18-9-timeout-user",
        emotions=["不安"],
        memo=raw_memo,
        memo_action="",
        category=["生活"],
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    body = _public_response_body(result)
    public_meta = result["input_feedback_meta"]

    _assert_public_response_shape_unchanged(body)
    assert body["input_feedback"] is None
    assert result["input_feedback_comment"] == ""
    assert public_meta["observation_status"] == "unavailable"
    assert "emlis_ai_reply_timeout" in public_meta.get("rejection_reasons", [])
    speed = public_meta["submit_speed_regression"]
    assert speed["saved_emotion_success"] is True
    assert speed["reply_timeout"] is True
    assert speed["public_feedback_included"] is False
    assert speed["emlis_display_fail_closed"] is True
    assert speed["public_response_key_added"] is False
    assert speed["rn_visible_contract_changed"] is False
    _assert_public_meta_is_boundary_safe(public_meta, comment_text="", forbidden_fragments=[raw_memo])
