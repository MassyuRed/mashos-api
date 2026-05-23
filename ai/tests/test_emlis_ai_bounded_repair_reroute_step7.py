# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

import pytest

from emlis_ai_bounded_repair_reroute import (
    ACTION_NO_REPAIR,
    BOUNDED_REPAIR_REROUTE_VERSION,
    ACTION_RERENDER_SHALLOW_V2,
    ACTION_REROUTE_LOW_INFORMATION,
    ACTION_BLOCK,
    assert_bounded_repair_reroute_meta_only,
    decide_bounded_repair_reroute,
)
from emlis_ai_reply_service import _regeneration_reasons_for_retry
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_types import DisplayDecision
from fixtures.emlis_ai_runtime_surface_red_fixtures import RUNTIME_SURFACE_BASELINE_RED_FIXTURES


class DummyLimitedComposerClient:
    pass


def _decision_from_report(report: dict[str, object], *extra_reasons: str) -> DisplayDecision:
    action = str(report.get("action") or "")
    reasons = [
        "runtime_surface_pre_return_gate_failed",
        *[str(reason) for reason in list(report.get("rejection_reasons") or [])],
        *( [f"runtime_surface_pre_return_gate_action_{action}"] if action else [] ),
        *extra_reasons,
    ]
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=reasons,
        gate_trace={"runtime_surface_pre_return_gate": report},
    )


def test_step7_template_major_surface_requests_one_bounded_shallow_v2_rerender() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[0]
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
        rerender_allowed=True,
        rerender_attempted=False,
        rerender_attempt_limit=1,
    )
    decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_report(report),
        composer_source="ai_generated",
        runtime_surface_pre_return_gate_report=report,
    )

    assert report["action"] == ACTION_RERENDER_SHALLOW_V2
    assert decision.action == ACTION_RERENDER_SHALLOW_V2
    assert decision.shallow_v2_rerender_allowed is True
    assert decision.low_information_reroute_allowed is False
    assert decision.rerender_attempt_limit == 1
    meta = decision.as_meta()
    assert meta["version"] == BOUNDED_REPAIR_REROUTE_VERSION
    assert meta["display_gate_relaxed"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    # The meta must not leak the bad public body, even though the decision used it in-memory.
    assert "まだないかこと" not in str(meta)
    assert_bounded_repair_reroute_meta_only(meta)


def test_step7_low_information_reroute_is_bounded_and_meta_only() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[1]
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta={"profile_key": "complete_initial", "composer_source": "ai_generated"},
        rerender_allowed=False,
        rerender_attempted=False,
        rerender_attempt_limit=1,
        low_information_reroute_allowed=True,
    )
    decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_report(report, "safe_unit_insufficient"),
        composer_source="ai_generated",
        runtime_surface_pre_return_gate_report=report,
    )

    assert report["action"] == ACTION_REROUTE_LOW_INFORMATION
    assert decision.action == ACTION_REROUTE_LOW_INFORMATION
    assert decision.allowed is True
    assert decision.low_information_reroute_allowed is True
    meta = decision.as_meta()
    assert meta["low_information_reroute_allowed"] is True
    assert meta["display_gate_relaxed"] is False
    assert meta["public_status_extended"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert "今までこと" not in str(meta)
    assert_bounded_repair_reroute_meta_only(meta)


def test_step7_safety_and_unavailable_source_never_reroute_to_displayed_text() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[0]
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
    )

    safety_decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_report(report),
        composer_source="ai_generated",
        safety_report=SimpleNamespace(requires_block=True),
        runtime_surface_pre_return_gate_report=report,
    )
    assert safety_decision.action == ACTION_BLOCK
    assert safety_decision.low_information_reroute_allowed is False
    assert "safety_blocked_no_reroute" in safety_decision.blocked_reasons

    unavailable_source_decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_report(report),
        composer_source="unavailable",
        runtime_surface_pre_return_gate_report=report,
    )
    assert unavailable_source_decision.action == ACTION_BLOCK
    assert unavailable_source_decision.low_information_reroute_allowed is False
    assert "source_unavailable_or_non_ai_no_surface_reroute" in unavailable_source_decision.blocked_reasons


def test_step7_passed_or_no_runtime_gate_is_no_repair() -> None:
    passed_decision = DisplayDecision(
        observation_status="passed",
        comment_text="Emlisです。\n今は、少し整理できているように見えます。",
        rejection_reasons=[],
        gate_trace={},
    )
    decision = decide_bounded_repair_reroute(
        display_decision=passed_decision,
        composer_source="ai_generated",
        runtime_surface_pre_return_gate_report=None,
    )
    assert decision.action == ACTION_NO_REPAIR
    assert decision.allowed is False
    assert decision.repair_reasons == ("already_passed",)


def test_step7_limited_composer_consumes_only_surface_rerender_reason_for_retry() -> None:
    retry_reasons = _regeneration_reasons_for_retry(
        [
            "phase_not_complete",
            "runtime_surface_pre_return_gate_failed",
            "runtime_surface_pre_return_gate_action_rerender_shallow_v2",
            "surface_template_major",
        ],
        DummyLimitedComposerClient(),
    )

    assert "phase_not_complete" not in retry_reasons
    assert "runtime_surface_pre_return_gate_failed" not in retry_reasons
    assert retry_reasons == [
        "runtime_surface_pre_return_gate_action_rerender_shallow_v2",
    ]


def test_step7_meta_contract_rejects_text_payload_or_gate_relaxation() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[-1]
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
    )
    decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_report(report),
        composer_source="ai_generated",
        runtime_surface_pre_return_gate_report=report,
    )
    meta = decision.as_meta()

    unsafe_text = dict(meta)
    unsafe_text["comment_text"] = "表示してはいけない本文"
    with pytest.raises(ValueError):
        assert_bounded_repair_reroute_meta_only(unsafe_text)

    unsafe_relaxed = dict(meta)
    unsafe_relaxed["display_gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_bounded_repair_reroute_meta_only(unsafe_relaxed)


def test_step7_empty_placeholder_surface_fail_closed_without_candidate_is_not_a_surface_repair_block() -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text="",
        composer_meta={"composer_source": "unavailable"},
        rerender_allowed=True,
        rerender_attempted=False,
        rerender_attempt_limit=1,
        low_information_reroute_allowed=False,
    )
    decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_report(
            report,
            "phase_not_complete",
            "composer_source_unavailable",
            "empty_comment_text",
            "empty_comment_text_without_candidate",
        ),
        composer_source="unavailable",
        runtime_surface_pre_return_gate_report=report,
    )

    assert report["action"] == "fail_closed"
    assert decision.action == ACTION_NO_REPAIR
    assert decision.low_information_reroute_allowed is False
    assert "placeholder_runtime_surface_gate_without_candidate" in decision.repair_reasons
    assert "source_unavailable_or_non_ai_no_surface_reroute" not in decision.blocked_reasons
    meta = decision.as_meta()
    assert meta["display_gate_relaxed"] is False
    assert meta["comment_text_body_included"] is False
    assert_bounded_repair_reroute_meta_only(meta)
