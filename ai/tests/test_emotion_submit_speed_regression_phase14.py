from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

import emotion_submit_service as service
from emlis_ai_observation_diagnostic_lockdown import build_observation_diagnostic_lockdown
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from fixtures.emlis_ai_two_stage_reception_cases import TWO_STAGE_RECEPTION_CASES


SECRET_RAW_INPUT = "これはPhase14でmetaへ出してはいけない入力本文です"
SECRET_COMMENT = "これはPhase14でmetaへ出してはいけないcomment_text本文です"


def _case(case_id: str) -> dict[str, Any]:
    for case in TWO_STAGE_RECEPTION_CASES:
        if case["case_id"] == case_id:
            return dict(case)
    raise AssertionError(f"missing fixture case: {case_id}")


A_CURRENT_INPUT = _case("daily_unpleasant_encounter_A")["current_input"]


def _patch_persist_baseline(monkeypatch, *, render_reply):
    monkeypatch.setattr(
        service,
        "normalize_submission_payload",
        lambda **_kwargs: {
            "emotions_tags": ["怒り"],
            "emotion_details": [{"type": "怒り", "strength": "medium"}],
            "emotion_strength_avg": 2.0,
            "category": ["生活"],
            "has_memo_input": True,
        },
    )

    async def fake_insert_emotion_row(**_kwargs):
        return {
            "id": "phase14-emotion-log-1",
            "created_at": "2026-05-26T00:00:00.000000+00:00",
        }

    async def fake_invalidate_prefix(_prefix: str):
        return None

    async def fake_subscription_tier_for_user(*_args, **_kwargs):
        return "free"

    monkeypatch.setattr(service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(service, "invalidate_prefix", fake_invalidate_prefix)
    monkeypatch.setattr(service, "_global_summary_activity_date_from_created_at", lambda _created_at: "2026-05-26")
    monkeypatch.setattr(service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)
    monkeypatch.setattr(service, "render_emlis_ai_reply", render_reply)


def _assert_no_text_payload(value: Any) -> None:
    dumped = json.dumps(value, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    for forbidden_key in (
        '"memo"',
        '"memo_action"',
        '"raw_input"',
        '"raw_text"',
        '"comment_text"',
        '"candidate_comment_text"',
    ):
        assert forbidden_key not in dumped


def test_phase14_reception_probe_identifies_daily_unpleasant_branch_without_text_payload() -> None:
    probe = service._build_phase14_reception_mode_timing_probe(A_CURRENT_INPUT)

    assert probe["probe_succeeded"] is True
    assert probe["daily_reception_branch"] is True
    assert probe["reception_mode_id"] == "daily_unpleasant_reception"
    assert probe["shared_evidence_elapsed_ms"] >= 0
    assert probe["reception_mode_elapsed_ms"] >= 0
    assert probe["probe_elapsed_ms"] >= 0
    assert probe["raw_input_included"] is False
    assert probe["comment_text_body_included"] is False
    _assert_no_text_payload(probe)


@pytest.mark.parametrize("case", TWO_STAGE_RECEPTION_CASES, ids=lambda case: case["case_id"])
def test_phase14_two_stage_fixture_reception_probe_stays_under_submit_budget(case: dict[str, Any]) -> None:
    probe = service._build_phase14_reception_mode_timing_probe(case["current_input"])

    assert probe["probe_succeeded"] is True
    assert probe["probe_elapsed_ms"] < int(service._emlis_ai_reply_timeout_seconds() * 1000)
    assert probe["shared_evidence_elapsed_ms"] >= 0
    assert probe["reception_mode_elapsed_ms"] >= 0
    assert probe["raw_input_included"] is False
    assert probe["comment_text_body_included"] is False
    _assert_no_text_payload(probe)


@pytest.mark.asyncio
async def test_phase14_persist_attaches_submit_speed_regression_summary_on_displayed_reply(monkeypatch) -> None:
    visible_comment = "見えたこと：\n不快で怖さもある出来事に出くわして、怒りが残っているように見えます。\n\nEmlisから：\nうわ、それは嫌でしたね。"

    async def fake_render_reply(**_kwargs):
        return SimpleNamespace(
            comment_text=visible_comment,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "observation_status": "passed",
                "observation_trace_id": "phase14-trace-displayed",
                "diagnostic_summary": {
                    "stage": "display",
                    "primary_reason": "passed",
                    "coverage_group": "daily_reception",
                    "composer_status": "generated",
                    "composer_source": "ai_generated",
                    "composer_elapsed_ms": 11,
                },
                "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
                "visible_surface_acceptance_gate": {"evaluated": True, "passed": True, "classification": "pass", "action": "allow"},
                "comment_text": SECRET_COMMENT,
                "raw_input": SECRET_RAW_INPUT,
            },
        )

    _patch_persist_baseline(monkeypatch, render_reply=fake_render_reply)

    result = await service.persist_emotion_submission(
        user_id="user-phase14",
        emotions=["怒り"],
        memo=A_CURRENT_INPUT["memo"],
        memo_action=A_CURRENT_INPUT["memo_action"],
        category=A_CURRENT_INPUT["category"],
    )

    assert result["input_feedback_comment"] == visible_comment
    meta = result["input_feedback_meta"]
    speed = meta["submit_speed_regression"]
    assert speed["schema_version"] == "cocolon.emlis.submit_speed_regression.v1"
    assert speed["source_phase"] == "Phase14_speed_regression"
    assert speed["trace_id"] == "phase14-trace-displayed"
    assert speed["reply_elapsed_ms"] >= 0
    assert speed["reply_timeout_budget_ms"] > 0
    assert speed["reply_completed_within_budget"] is True
    assert speed["public_meta_elapsed_ms"] >= 0
    assert speed["submit_elapsed_ms"] >= 0
    assert speed["composer_elapsed_ms"] == 11
    assert speed["comment_text_present"] is True
    assert speed["public_feedback_included"] is True
    assert speed["saved_emotion_success"] is True
    assert speed["emlis_display_fail_closed"] is False
    assert speed["daily_reception_branch"] is True
    assert speed["reception_mode_id"] == "daily_unpleasant_reception"
    assert speed["heavy_diagnostics_added_before_display"] is False
    assert speed["general_dictionary_lookup_used"] is False
    assert speed["raw_input_included"] is False
    assert speed["comment_text_body_included"] is False
    _assert_no_text_payload(meta)


@pytest.mark.asyncio
async def test_phase14_timeout_keeps_save_success_and_marks_emlis_display_fail_closed(monkeypatch) -> None:
    async def slow_render_reply(**_kwargs):
        await asyncio.sleep(0.05)
        return SimpleNamespace(comment_text="should not return", meta={"observation_status": "passed"})

    _patch_persist_baseline(monkeypatch, render_reply=slow_render_reply)
    monkeypatch.setattr(service, "_emlis_ai_reply_timeout_seconds", lambda: 0.001)

    result = await service.persist_emotion_submission(
        user_id="user-phase14",
        emotions=["怒り"],
        memo=A_CURRENT_INPUT["memo"],
        memo_action=A_CURRENT_INPUT["memo_action"],
        category=A_CURRENT_INPUT["category"],
    )

    assert result["inserted"]["id"] == "phase14-emotion-log-1"
    assert result["input_feedback_comment"] == ""
    meta = result["input_feedback_meta"]
    assert meta["observation_status"] == "unavailable"
    assert "emlis_ai_reply_timeout" in meta["rejection_reasons"]
    speed = meta["submit_speed_regression"]
    assert speed["saved_emotion_success"] is True
    assert speed["public_feedback_included"] is False
    assert speed["emlis_display_fail_closed"] is True
    assert speed["reply_timeout"] is True
    assert speed["reply_completed_within_budget"] is False
    assert speed["fail_closed_reason_code"] == "emlis_ai_reply_timeout"
    assert "emlis_ai_reply_timeout" in speed["reason_codes"]
    assert speed["daily_reception_branch"] is True
    _assert_no_text_payload(meta)


def test_phase14_inclusion_summary_uses_timeout_reason_family() -> None:
    internal_meta = {
        "observation_status": "unavailable",
        "rejection_reasons": ["emlis_ai_timeout_or_error", "emlis_ai_reply_timeout"],
    }
    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=False,
        subscription_tier="free",
    )

    summary = service._build_public_feedback_inclusion_summary(
        input_feedback_comment="",
        internal_input_feedback_meta=internal_meta,
        public_input_feedback_meta=public_meta,
    )

    assert summary["public_feedback_included"] is False
    assert summary["public_feedback_not_included_reply_timeout_or_error"] is True
    assert summary["candidate_fail_closed_display_absent"] is True
    assert summary["reason_family"] == "reply_timeout_or_error"
    assert "emlis_ai_reply_timeout" in summary["reason_codes"]
    _assert_no_text_payload(summary)


def test_phase14_diagnostic_lockdown_carries_speed_summary_without_body() -> None:
    speed_summary = service._build_submit_speed_regression_summary(
        trace_id="phase14-lockdown-trace",
        reply_elapsed_ms=501,
        reply_timeout_budget_ms=500,
        public_meta_elapsed_ms=2,
        submit_elapsed_ms=510,
        internal_input_feedback_meta={
            "observation_status": "unavailable",
            "rejection_reasons": ["emlis_ai_timeout_or_error", "emlis_ai_reply_timeout"],
        },
        public_input_feedback_meta={
            "observation_status": "unavailable",
            "rejection_reasons": ["emlis_ai_timeout_or_error", "emlis_ai_reply_timeout"],
        },
        reception_probe={
            "probe_succeeded": True,
            "probe_elapsed_ms": 1,
            "shared_evidence_elapsed_ms": 0,
            "reception_mode_elapsed_ms": 1,
            "reception_mode_id": "daily_unpleasant_reception",
            "reception_mode_family": "daily_reception",
            "daily_reception_branch": True,
        },
        comment_text_present=False,
        public_feedback_included=False,
        saved_emotion_success=True,
        reply_timeout=True,
        reply_error_type="TimeoutError",
    )
    diagnostic = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta={
            "observation_status": "unavailable",
            "rejection_reasons": ["emlis_ai_timeout_or_error", "emlis_ai_reply_timeout"],
            "submit_speed_regression": speed_summary,
            "comment_text": SECRET_COMMENT,
            "raw_input": SECRET_RAW_INPUT,
        },
        emotion_log_id="phase14-emotion-log-1",
        created_at="2026-05-26T00:00:00+00:00",
    )

    assert diagnostic["classification"] == "backend_exception_or_timeout"
    assert diagnostic["reply_elapsed_ms"] == 501
    assert diagnostic["reply_timeout"] is True
    assert diagnostic["emlis_display_fail_closed"] is True
    assert diagnostic["fail_closed_reason_code"] == "emlis_ai_reply_timeout"
    assert diagnostic["daily_reception_branch"] is True
    assert diagnostic["reception_mode_id"] == "daily_unpleasant_reception"
    _assert_no_text_payload(diagnostic)
