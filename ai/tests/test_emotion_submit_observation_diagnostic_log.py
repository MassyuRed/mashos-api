from __future__ import annotations

import json
import logging
from types import SimpleNamespace

import pytest

import emotion_submit_service as service

_DIAGNOSTIC_ENV_NAMES = (
    "EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED",
    "EMLIS_AI_OBSERVATION_RESULT_LOG_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_RESULT_LOG_ENABLED",
    "EMLIS_AI_OBSERVATION_DEBUG_LOG",
    "EMLIS_AI_OBSERVATION_DEBUG_LOGS",
)


def _clear_diagnostic_env(monkeypatch) -> None:
    for name in _DIAGNOSTIC_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def _lockdown_records(caplog) -> list[dict]:
    prefix = "emlis_observation_diagnostic_lockdown "
    records: list[dict] = []
    for record in caplog.records:
        message = record.getMessage()
        if prefix not in message:
            continue
        records.append(json.loads(message.split(prefix, 1)[1]))
    return records


def _patch_persist_baseline(monkeypatch, *, render_reply):
    monkeypatch.setattr(
        service,
        "normalize_submission_payload",
        lambda **_kwargs: {
            "emotions_tags": ["neutral"],
            "emotion_details": [{"name": "neutral", "strength": 50}],
            "emotion_strength_avg": 50,
            "category": ["daily"],
            "has_memo_input": True,
        },
    )

    async def fake_insert_emotion_row(**_kwargs):
        return {
            "id": "emotion-log-1",
            "created_at": "2026-05-17T02:35:05.000000+00:00",
        }

    async def fake_invalidate_prefix(_prefix: str):
        return None

    async def fake_subscription_tier_for_user(*_args, **_kwargs):
        return "free"

    monkeypatch.setattr(service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(service, "invalidate_prefix", fake_invalidate_prefix)
    monkeypatch.setattr(
        service,
        "_global_summary_activity_date_from_created_at",
        lambda _created_at: "2026-05-17",
    )
    monkeypatch.setattr(service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)
    monkeypatch.setattr(service, "render_emlis_ai_reply", render_reply)


@pytest.mark.asyncio
async def test_persist_emits_one_lockdown_record_on_success_with_new_env(monkeypatch, caplog) -> None:
    _clear_diagnostic_env(monkeypatch)
    monkeypatch.setenv("EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED", "1")
    caplog.set_level(logging.INFO)
    visible_comment = "これはログへ出してはいけない観測本文です"
    raw_memo = "これはログへ出してはいけない入力本文です"

    async def fake_render_reply(**_kwargs):
        return SimpleNamespace(
            comment_text=visible_comment,
            meta={
                "observation_status": "passed",
                "observation_trace_id": "emlisobs-success",
                "diagnostic_summary": {
                    "stage": "display",
                    "primary_reason": "passed",
                    "coverage_group": "positive_recovery",
                    "composer_status": "generated",
                    "composer_source": "ai_generated",
                    "gate_results": {
                        "reader": {"passed": True},
                        "grounding": {"passed": True},
                        "template_echo": {"passed": True},
                        "display": {"passed": True},
                    },
                },
            },
        )

    _patch_persist_baseline(monkeypatch, render_reply=fake_render_reply)

    result = await service.persist_emotion_submission(
        user_id="user-1",
        emotions=["neutral"],
        memo=raw_memo,
        memo_action=None,
        category=["daily"],
    )

    records = _lockdown_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert result["input_feedback_comment"] == visible_comment
    assert record["emotion_log_id"] == "emotion-log-1"
    assert record["trace_id"] == "emlisobs-success"
    assert record["observation_status"] == "passed"
    assert record["comment_text_length"] == len(visible_comment)
    assert record["classification"] == "passed_displayed"
    assert record["raw_input_included"] is False
    assert record["comment_text_included"] is False
    assert "emlis_observation_result" not in caplog.text
    assert visible_comment not in caplog.text
    assert raw_memo not in caplog.text


@pytest.mark.asyncio
async def test_persist_returns_public_sanitized_meta_while_lockdown_uses_internal_meta(monkeypatch, caplog) -> None:
    _clear_diagnostic_env(monkeypatch)
    monkeypatch.setenv("EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED", "1")
    caplog.set_level(logging.INFO)
    visible_comment = "これはpublic metaへ入れてはいけない観測本文です"
    raw_memo = "これはpublic metaへ入れてはいけない入力本文です"
    raw_evidence = "これはpublic metaへ入れてはいけない根拠全文です"

    async def fake_render_reply(**_kwargs):
        return SimpleNamespace(
            comment_text=visible_comment,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "observation_trace_id": "emlisobs-step3-boundary",
                "diagnostic_summary": {
                    "stage": "display",
                    "primary_reason": "passed",
                    "coverage_group": "low_information",
                    "composer_status": "generated",
                    "composer_source": "ai_generated",
                    "gate_results": {
                        "reader": {"passed": True, "primary_reason": "passed"},
                        "display": {"passed": True, "primary_reason": "passed"},
                    },
                },
                "complete_reply_service_diagnostics": {
                    "used_phrase_unit_ids": ["phrase-unit-internal-only"],
                    "relation_types": ["relation-internal-only"],
                    "current_input": {"memo": raw_memo},
                    "comment_text": visible_comment,
                },
                "multi_perspective": {
                    "evidence_spans": [{"raw_text": raw_evidence, "source_text": raw_memo}],
                    "observation_graph": {"nodes": [{"text": raw_evidence}]},
                },
                "current_input": {"memo": raw_memo},
                "comment_text": visible_comment,
            },
        )

    _patch_persist_baseline(monkeypatch, render_reply=fake_render_reply)

    result = await service.persist_emotion_submission(
        user_id="user-1",
        emotions=["neutral"],
        memo=raw_memo,
        memo_action=None,
        category=["daily"],
    )

    public_meta = result["input_feedback_meta"]
    dumped_public_meta = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert public_meta["schema_version"] == "emlis.public_input_feedback_meta.v1"
    assert public_meta["observation_status"] == "passed"
    assert public_meta["public_feedback_meta_boundary"]["sanitized"] is True
    assert public_meta["public_feedback_meta_boundary"]["internal_meta_returned"] is False
    assert "complete_reply_service_diagnostics" not in public_meta
    assert "multi_perspective" not in public_meta
    assert "current_input" not in dumped_public_meta
    assert visible_comment not in dumped_public_meta
    assert raw_memo not in dumped_public_meta
    assert raw_evidence not in dumped_public_meta

    records = _lockdown_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert record["trace_id"] == "emlisobs-step3-boundary"
    assert record["classification"] == "passed_displayed"
    assert record["used_phrase_unit_ids"] == ["phrase-unit-internal-only"]
    assert record["relation_types"] == ["relation-internal-only"]
    assert visible_comment not in caplog.text
    assert raw_memo not in caplog.text
    assert raw_evidence not in caplog.text


@pytest.mark.asyncio
async def test_persist_emits_lockdown_record_on_render_exception(monkeypatch, caplog) -> None:
    _clear_diagnostic_env(monkeypatch)
    monkeypatch.setenv("EMLIS_AI_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED", "true")
    caplog.set_level(logging.INFO)
    raw_memo = "例外時にもログへ出してはいけない入力本文です"

    async def fake_render_reply(**_kwargs):
        raise RuntimeError("render failed")

    _patch_persist_baseline(monkeypatch, render_reply=fake_render_reply)

    result = await service.persist_emotion_submission(
        user_id="user-1",
        emotions=["neutral"],
        memo=raw_memo,
        memo_action=None,
        category=["daily"],
    )

    records = _lockdown_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert result["input_feedback_comment"] == ""
    assert result["input_feedback_meta"]["observation_status"] == "unavailable"
    assert record["emotion_log_id"] == "emotion-log-1"
    assert record["observation_status"] == "unavailable"
    assert record["comment_text_length"] == 0
    assert record["classification"] == "backend_exception_or_timeout"
    assert "emlis_ai_timeout_or_error" in record["rejection_reasons"]
    assert raw_memo not in caplog.text


def test_lockdown_log_is_quiet_by_default(monkeypatch, caplog) -> None:
    _clear_diagnostic_env(monkeypatch)
    caplog.set_level(logging.INFO)

    service._log_emlis_ai_observation_diagnostic_lockdown(
        input_feedback_comment="visible comment must not be logged",
        input_feedback_meta={"observation_status": "passed"},
        emotion_log_id="emotion-log-1",
        created_at="2026-05-17T02:35:05.000000+00:00",
    )

    assert _lockdown_records(caplog) == []
    assert "visible comment" not in caplog.text


def test_lockdown_log_classifies_rejected_grounding_without_text_payload(monkeypatch, caplog) -> None:
    _clear_diagnostic_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_OBSERVATION_DIAGNOSTIC_LOCKDOWN_LOG_ENABLED", "on")
    caplog.set_level(logging.INFO)

    service._log_emlis_ai_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta={
            "observation_status": "rejected",
            "observation_trace_id": "emlisobs-grounding",
            "diagnostic_summary": {
                "stage": "grounding",
                "primary_reason": "unsupported_sentence",
                "composer_status": "generated",
                "composer_source": "ai_generated",
                "coverage_group": "conflict",
                "gate_results": {
                    "reader": {"passed": True},
                    "grounding": {"passed": False, "primary_reason": "unsupported_sentence"},
                    "template_echo": {"passed": True},
                    "display": {"passed": False, "primary_reason": "unsupported_sentence"},
                },
            },
            "memo": "raw input key must not be copied to the diagnostic record",
        },
        emotion_log_id="emotion-log-2",
        created_at="2026-05-17T02:36:22.000000+00:00",
    )

    records = _lockdown_records(caplog)
    assert len(records) == 1
    record = records[0]
    assert record["trace_id"] == "emlisobs-grounding"
    assert record["comment_text_length"] == 0
    assert record["classification"] == "candidate_generated_but_grounding_rejected"
    assert "raw input key" not in caplog.text
