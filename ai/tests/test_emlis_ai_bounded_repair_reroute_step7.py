# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from emlis_ai_bounded_repair_reroute import (
    ACTION_NO_REPAIR,
    BOUNDED_REPAIR_REROUTE_VERSION,
    ACTION_RERENDER_SURFACE,
    ACTION_RERENDER_SHALLOW_V2,
    ACTION_REROUTE_LOW_INFORMATION,
    ACTION_BLOCK,
    assert_bounded_repair_reroute_meta_only,
    decide_bounded_repair_reroute,
)
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import GROUND_OBSERVATION_REPLY_GENERATION_PATH
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    build_plan_preserving_recovery_sequence,
)
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_visible_surface_acceptance_gate import (
    ACTION_RERENDER_SURFACE as VISIBLE_ACTION_RERENDER_SURFACE,
    CLASSIFICATION_REPAIR_REQUIRED,
    build_visible_surface_acceptance_gate_report,
)
from emlis_ai_types import DisplayDecision
from fixtures.emlis_ai_runtime_surface_red_fixtures import RUNTIME_SURFACE_BASELINE_RED_FIXTURES


class DummyLimitedComposerClient:
    pass


def _canonical_case_a():
    return next(
        case for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES
        if case.case_id == "A"
    )


def _canonical_recovery_sequence():
    current_input = normalize_emlis_current_input(_canonical_case_a().as_current_input())
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    return build_plan_preserving_recovery_sequence(plan, resolver)


def _render_with(composer_client):
    return asyncio.run(
        render_emlis_ai_reply(
            user_id="step7-canonical-recovery-owner",
            subscription_tier="free",
            current_input=_canonical_case_a().as_current_input(),
            composer_client=composer_client,
        )
    )


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


def _decision_from_visible_report(report: dict[str, object], *extra_reasons: str) -> DisplayDecision:
    action = str(report.get("action") or "")
    classification = str(report.get("classification") or "")
    reasons = [
        "visible_surface_acceptance_gate_failed",
        *[str(reason) for reason in list(report.get("rejection_reasons") or [])],
        *( [f"visible_surface_acceptance_gate_action_{action}"] if action else [] ),
        *( [f"visible_surface_acceptance_gate_classification_{classification}"] if classification else [] ),
        *extra_reasons,
    ]
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=reasons,
        gate_trace={"visible_surface_acceptance_gate": report},
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


def test_step7_canonical_recovery_sequence_preserves_one_grounded_plan() -> None:
    sequence = _canonical_recovery_sequence()

    assert tuple(item.recovery_stage for item in sequence) == GROUND_RECOVERY_STAGES
    assert all(item.required_coverage_preserved for item in sequence)
    assert all(item.required_nucleus_ids == sequence[0].required_nucleus_ids for item in sequence)
    assert all(item.required_relation_ids == sequence[0].required_relation_ids for item in sequence)
    assert all(not item.unresolved_evidence_span_ids for item in sequence)
    assert all(item.synthetic_evidence_id_used is False for item in sequence)


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


def test_step6_visible_surface_rerender_enters_one_bounded_repair_loop() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="Emlisです。\n今は、不安の重さが先に出ているように見えます。",
        selected_emotions=(("悲しみ", "medium"), ("不安", "medium")),
        rerender_allowed=True,
        rerender_attempted=False,
    )

    decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_visible_report(report),
        composer_source="ai_generated",
        visible_surface_acceptance_gate_report=report,
    )

    assert report["classification"] == CLASSIFICATION_REPAIR_REQUIRED
    assert report["action"] == VISIBLE_ACTION_RERENDER_SURFACE
    assert decision.action == ACTION_RERENDER_SURFACE
    assert decision.surface_rerender_allowed is True
    assert decision.shallow_v2_rerender_allowed is False
    assert decision.rerender_attempt_limit == 1
    assert decision.visible_surface_gate_evaluated is True
    assert decision.visible_surface_gate_action == VISIBLE_ACTION_RERENDER_SURFACE
    assert "bounded_visible_surface_rerender_required" in decision.repair_reasons
    meta = decision.as_meta()
    assert meta["visible_surface_gate_evaluated"] is True
    assert meta["surface_rerender_allowed"] is True
    assert meta["display_gate_relaxed"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["raw_input_included"] is False
    assert "不安の重さ" not in str(meta)
    assert_bounded_repair_reroute_meta_only(meta)


def test_step6_visible_surface_rerender_attempt_limit_remains_one_and_second_failure_blocks() -> None:
    report = build_visible_surface_acceptance_gate_report(
        comment_text="Emlisです。\n今は、不安の重さが先に出ているように見えます。",
        selected_emotions=(("悲しみ", "medium"), ("不安", "medium")),
        rerender_allowed=True,
        rerender_attempted=True,
    )

    decision = decide_bounded_repair_reroute(
        display_decision=_decision_from_visible_report(report),
        composer_source="ai_generated",
        visible_surface_acceptance_gate_report=report,
    )

    assert decision.rerender_attempted is True
    assert decision.rerender_attempt_limit == 1
    assert decision.action in {ACTION_BLOCK, "fail_closed"}
    assert decision.surface_rerender_allowed is False
    assert "bounded_surface_repair_not_available" in decision.blocked_reasons
    meta = decision.as_meta()
    assert meta["surface_rerender_allowed"] is False
    assert meta["display_gate_relaxed"] is False
    assert "不安の重さ" not in str(meta)
    assert_bounded_repair_reroute_meta_only(meta)


def test_step7_limited_composer_cannot_select_a_second_substantive_body_route() -> None:
    canonical = _render_with(None)
    limited = _render_with(DummyLimitedComposerClient())

    assert limited.comment_text == canonical.comment_text
    for reply in (canonical, limited):
        assert reply.meta["generation_path"] == GROUND_OBSERVATION_REPLY_GENERATION_PATH
        assert reply.meta["composer_source"] == "grounded_plan_realizer"
        assert reply.meta["semantic_quality_gate"] == "passed"
        assert reply.meta["grounded_observation"]["public_reply_path_connected"] is True
        assert reply.comment_text not in json.dumps(reply.meta, ensure_ascii=False)
        assert reply.meta["raw_input_included"] is False
        assert reply.meta["comment_text_body_included"] is False
