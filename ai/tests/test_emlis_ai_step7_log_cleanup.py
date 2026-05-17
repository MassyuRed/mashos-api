from __future__ import annotations

import logging

from emotion_submit_service import (
    _emlis_ai_observation_debug_logging_enabled,
    _extract_emlis_ai_diagnostic_summary,
    _log_emlis_ai_observation_result,
)

_DEBUG_ENV_NAMES = (
    "EMLIS_AI_OBSERVATION_DEBUG_LOG",
    "EMLIS_AI_OBSERVATION_DEBUG_LOGS",
    "EMLIS_AI_OBSERVATION_RESULT_LOG_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_RESULT_LOG_ENABLED",
)


def _clear_debug_env(monkeypatch) -> None:
    for name in _DEBUG_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_emlis_observation_debug_logging_is_disabled_by_default(monkeypatch) -> None:
    _clear_debug_env(monkeypatch)

    assert _emlis_ai_observation_debug_logging_enabled() is False


def test_emlis_observation_debug_logging_is_opt_in(monkeypatch) -> None:
    _clear_debug_env(monkeypatch)

    for value in ("1", "true", "yes", "y", "on", "debug", " TRUE "):
        monkeypatch.setenv("EMLIS_AI_OBSERVATION_DEBUG_LOG", value)
        assert _emlis_ai_observation_debug_logging_enabled() is True

    for value in ("0", "false", "no", "off", ""):
        _clear_debug_env(monkeypatch)
        monkeypatch.setenv("EMLIS_AI_OBSERVATION_DEBUG_LOG", value)
        assert _emlis_ai_observation_debug_logging_enabled() is False


def test_emlis_observation_debug_logging_supports_legacy_flag_names(monkeypatch) -> None:
    _clear_debug_env(monkeypatch)

    for flag_name in (
        "EMLIS_AI_OBSERVATION_DEBUG_LOGS",
        "EMLIS_AI_OBSERVATION_RESULT_LOG_ENABLED",
        "COCOLON_EMLIS_OBSERVATION_RESULT_LOG_ENABLED",
    ):
        _clear_debug_env(monkeypatch)
        monkeypatch.setenv(flag_name, "true")
        assert _emlis_ai_observation_debug_logging_enabled() is True


def test_extract_emlis_ai_diagnostic_summary_prefers_public_meta_without_raw_input() -> None:
    meta = {
        "diagnostic_summary": {
            "stage": "reader",
            "primary_reason": "relation_not_expressed",
            "coverage_group": "positive_recovery",
        },
        "memo": "raw text must not be read",
        "comment_text": "public comment text must not be copied",
    }

    summary = _extract_emlis_ai_diagnostic_summary(meta)

    assert summary == {
        "stage": "reader",
        "primary_reason": "relation_not_expressed",
        "coverage_group": "positive_recovery",
    }
    assert "memo" not in summary
    assert "comment_text" not in summary


def test_extract_emlis_ai_diagnostic_summary_supports_multi_perspective_meta() -> None:
    meta = {
        "multi_perspective": {
            "diagnostic_summary": {
                "stage": "passed",
                "primary_reason": "passed",
                "coverage_group": "positive_recovery",
            }
        }
    }

    summary = _extract_emlis_ai_diagnostic_summary(meta)

    assert summary["stage"] == "passed"
    assert summary["primary_reason"] == "passed"
    assert summary["coverage_group"] == "positive_recovery"


def test_extract_emlis_ai_diagnostic_summary_returns_empty_for_non_dict() -> None:
    assert _extract_emlis_ai_diagnostic_summary(None) == {}
    assert _extract_emlis_ai_diagnostic_summary("not-meta") == {}


def test_emlis_observation_result_log_is_quiet_by_default(monkeypatch, caplog) -> None:
    _clear_debug_env(monkeypatch)
    caplog.set_level(logging.INFO)

    _log_emlis_ai_observation_result(
        input_feedback_comment="visible comment text must not be logged",
        input_feedback_meta={
            "observation_status": "passed",
            "diagnostic_summary": {
                "stage": "passed",
                "primary_reason": "passed",
                "coverage_group": "positive_recovery",
            },
            "memo": "raw text must not be logged",
        },
    )

    assert "emlis_observation_result" not in caplog.text
    assert "visible comment text" not in caplog.text
    assert "raw text" not in caplog.text


def test_emlis_observation_result_log_is_meta_only_when_enabled(monkeypatch, caplog) -> None:
    _clear_debug_env(monkeypatch)
    monkeypatch.setenv("EMLIS_AI_OBSERVATION_DEBUG_LOG", "true")
    caplog.set_level(logging.INFO)

    _log_emlis_ai_observation_result(
        input_feedback_comment="visible comment text must not be logged",
        input_feedback_meta={
            "observation_status": "passed",
            "diagnostic_summary": {
                "stage": "passed",
                "primary_reason": "passed",
                "coverage_group": "positive_recovery",
            },
            "memo": "raw text must not be logged",
        },
    )

    assert "emlis_observation_result" in caplog.text
    assert "positive_recovery" in caplog.text
    assert "visible comment text" not in caplog.text
    assert "raw text" not in caplog.text
