from __future__ import annotations

import json

import pytest

from emlis_ai_complete_initial_fixture_qa_service import (
    COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION,
    build_complete_initial_fixture_qa_run,
)
from emlis_ai_complete_scorecard_service import COMPLETE_COVERAGE_GROUP_ORDER, build_complete_initial_fixture_suite

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"


def _event(group: str, *, displayed: bool, binding: bool = True, reasons=None, template: int = 0, safety: int = 0):
    return {
        "version": "emlis.complete_scorecard_event.v1",
        "event_kind": "complete_composer_initial_reply_attempt",
        "complete_candidate_seen": True,
        "complete_candidate_generated": True,
        "complete_candidate_displayed": displayed,
        "eligible_count": 1,
        "passed_display_count": 1 if displayed else 0,
        "candidate_generated_count": 1,
        "observation_status": "passed" if displayed else "rejected",
        "coverage_group": group,
        "coverage_scope": group,
        "binding_pass": binding,
        "binding_count": 2 if binding else 1,
        "used_evidence_span_count": 2 if binding else 1,
        "used_phrase_unit_count": 2 if binding else 0,
        "used_relation_count": 1 if binding else 0,
        "relation_types": ["coexistence" if group != "pressure" else "pressure"],
        "gate_rejection_reasons": list(reasons or []),
        "top_rejection_reasons": list(reasons or []),
        "safety_major_count": safety,
        "template_major_count": template,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


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


def test_step9_fixture_qa_run_aggregates_display_binding_gate_and_non_template_metrics_without_raw_text() -> None:
    run = build_complete_initial_fixture_qa_run(
        scorecard_events=[
            _event("short_daily", displayed=True, binding=True),
            _event("pressure", displayed=False, binding=False, reasons=["unsupported_sentence"]),
            _event("conflict", displayed=False, binding=True, reasons=["template_echo_detected"], template=1),
        ],
        fixture_suite=build_complete_initial_fixture_suite(),
    )

    assert run["version"] == COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION
    assert run["step"] == "Step9_fixture_QA_run"
    assert run["fixture_qa_run_ready"] is True
    assert run["product_scorecard_input_ready"] is True
    assert run["event_count"] == 3
    assert run["display_reach_rate"] == pytest.approx(1 / 3)
    assert run["binding_pass_rate"] == pytest.approx(2 / 3)
    assert run["template_major_count"] >= 1
    assert run["non_template_major_clear"] is False
    assert "template_echo_detected" in run["top_rejection_reasons"]
    assert "unsupported_sentence" in run["top_rejection_reasons"]
    assert set(run["coverage_groups"]) == set(COMPLETE_COVERAGE_GROUP_ORDER)
    assert run["comment_text_contract"] == "passed_only"
    assert run["display_gate_relaxed"] is False
    assert run["input_specific_template_added"] is False
    assert run["fixed_completed_sentence_template_added"] is False
    assert run["raw_input_included"] is False
    assert run["raw_text_included"] is False
    assert run["comment_text_included"] is False

    serialized = json.dumps(run, ensure_ascii=False, sort_keys=True)
    assert "current_input" not in serialized
    assert "memo_action" not in serialized
    assert "source_text" not in serialized
    assert "reply_text" not in serialized


@pytest.mark.asyncio
async def test_step9_fixture_qa_run_is_attached_to_complete_initial_reply_meta(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step9-fixture-qa-run-user",
        subscription_tier="free",
        current_input=_sample_current_input("step9-fixture-qa-run-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]
    qa_run = diagnostic["step9_complete_initial_fixture_qa_run"]
    seed = diagnostic["step9_product_scorecard_seed"]

    assert qa_run == reply.meta["step9_complete_initial_fixture_qa_run"]
    assert qa_run == reply.meta["multi_perspective"]["step9_complete_initial_fixture_qa_run"]
    assert seed == reply.meta["complete_initial_product_scorecard_seed"]
    assert seed == reply.meta["multi_perspective"]["complete_initial_product_scorecard_seed"]
    assert qa_run["version"] == COMPLETE_INITIAL_STEP9_FIXTURE_QA_RUN_VERSION
    assert qa_run["fixture_qa_run_ready"] is True
    assert qa_run["product_scorecard_input_ready"] is True
    assert qa_run["fixture_suite_ready"] is True
    assert qa_run["event_count"] >= 1
    assert qa_run["fixture_count"] >= len(COMPLETE_COVERAGE_GROUP_ORDER)
    assert isinstance(qa_run["gate_reason_summary"], dict)
    assert qa_run["gate_reason_summary"]["ready"] is True
    assert qa_run["comment_text_contract"] == "passed_only"
    assert qa_run["comment_text_written_by_step9"] is False
    assert qa_run["display_gate_relaxed"] is False
    assert qa_run["input_specific_template_added"] is False
    assert qa_run["fixed_completed_sentence_template_added"] is False
    assert qa_run["raw_input_included"] is False
    assert qa_run["comment_text_included"] is False
    assert seed["ready"] is True
    assert seed["can_feed_complete_composer_product_scorecard"] is True
    assert seed["product_gate_reached"] is False
    assert seed["raw_input_included"] is False
    assert seed["comment_text_included"] is False
    assert phase_gate["step9_fixture_qa_run_ready"] is True
    assert phase_gate["step9_product_scorecard_input_ready"] is True
    assert phase_gate["step9_comment_text_contract_preserved"] is True
    assert phase_gate["step9_display_gate_relaxed"] is False

    serialized = json.dumps(qa_run, ensure_ascii=False, sort_keys=True)
    assert _SAMPLE_MEMO not in serialized
    assert "memo_action" not in serialized
    assert "current_input" not in serialized
