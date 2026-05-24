# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step9 regression / QA coverage for EmlisAI runtime surface quality.

This file does not add a runtime path. It locks the Step0-8 contracts together:
red surfaces are never public ``passed + comment_text`` again, safe Shallow V2
surfaces can still pass, low-information specificity stays displayable, and
scorecard/diagnostics keep surface failures as blockers rather than promotions.
"""

import json
from typing import Any

from emlis_ai_complete_reply_diagnostics_service import (
    attach_complete_reply_service_diagnostics,
    build_complete_reply_service_diagnostics,
)
from emlis_ai_complete_scorecard_service import (
    aggregate_complete_scorecard_events,
    normalize_complete_scorecard_event,
)
from emlis_ai_display_gate import decide_emlis_observation_display, phase8_display_gate_contract_ready
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_low_information_observation_composer import build_emlis_ai_low_information_observation
from emlis_ai_observation_reply_contract import (
    OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
)
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW,
    build_runtime_surface_pre_return_gate_report,
    dump_runtime_surface_pre_return_gate_report,
)
from emlis_ai_types import GroundingReport, ListenerReaderReport, TemplateEchoReport
from fixtures.emlis_ai_runtime_surface_red_fixtures import RUNTIME_SURFACE_BASELINE_RED_FIXTURES


_PASSING_READER = ListenerReaderReport(
    understandable=True,
    addressee_clear=True,
    speaker_integrity_ok=True,
    conversational=True,
    report_like=False,
    confidence=1.0,
)
_PASSING_GROUNDING = GroundingReport(passed=True, coverage_ratio=1.0, confidence=1.0)
_PASSING_TEMPLATE = TemplateEchoReport(passed=True)

_FORBIDDEN_SURFACE_MARKERS = (
    "今までこと",
    "大丈夫こと",
    "まだないかこと",
    "しれないどれこと",
    "上手になせなくてこと",
    "中心にあります",
    "その中でも",
    "も見えています",
    "も重なっています",
)


def _payload(evidence_spans: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [str(item.get("span_id") or "") for item in evidence_spans if str(item.get("span_id") or "")]
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {"display_name_call": "Mashさん", "greeting_text": "Emlisです"},
        "observation_graph": {
            "primary_state": {
                "claim_id": "c1",
                "claim_type": "primary_state",
                "text": "source anchored",
                "evidence_span_ids": ids[:3],
            },
            "core_tensions": [],
            "pressure_sources": [],
            "limit_signals": [],
            "self_awareness": [],
            "value_or_strength_signals": [],
            "safety_boundaries": [],
            "forbidden_claims": [],
            "missing_information": [],
        },
        "evidence_spans": evidence_spans,
        "limited_observation_scope": {"scope_status": "eligible", "coverage_scope": "partial_observation"},
        "composition_contract": {"forbidden_output_surfaces": []},
    }


def _low_info_input(memo: str, *, emotions: list[str] | None = None) -> dict[str, Any]:
    labels = list(emotions or [])
    return {
        "id": f"step9-low-info-{abs(hash((memo, tuple(labels))))}",
        "created_at": "2026-05-23T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": label, "strength": "medium"} for label in labels],
        "emotions": labels,
        "category": ["生活"],
    }


def _display_decision(
    text: str,
    *,
    composer_meta: dict[str, Any],
    observation_reply_kind: str = "",
    quality_meta: dict[str, Any] | None = None,
):
    surface_report = build_runtime_surface_pre_return_gate_report(
        comment_text=text,
        composer_meta=composer_meta,
    )
    return decide_emlis_observation_display(
        comment_text=text,
        reader_report=_PASSING_READER,
        grounding_report=_PASSING_GROUNDING,
        template_echo_report=_PASSING_TEMPLATE,
        composer_source="ai_generated",
        phase_completion_ready=True,
        observation_reply_kind=observation_reply_kind,
        observation_quality_meta=quality_meta,
        runtime_surface_pre_return_gate_report=surface_report,
    )


def _complete_candidate(meta: dict[str, Any] | None = None) -> dict[str, Any]:
    composer_meta = {
        "profile_key": "current_input_core",
        "coverage_scope": "current_input_core",
        "shallow_observation_path": True,
        "composer_source": "ai_generated",
        "shallow_realizer_version": "shallow_surface_realizer.v2",
        "shallow_v2_used": True,
        "malformed_phrase_unit_blocked_count": 2,
    }
    composer_meta.update(meta or {})
    return {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": "emlis.limited_composer.v1",
        "generation_method": "limited_current_input_core",
        "coverage_scope": "current_input_core",
        "used_evidence_span_ids": ["ev-step9"],
        "used_relation_ids": ["rel-step9"],
        "composer_meta": composer_meta,
    }


def _assert_no_public_contract_mutation(meta: dict[str, Any]) -> None:
    for key in (
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "reader_gate_relaxed",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "raw_input_included",
        "comment_text_body_included",
    ):
        if key in meta:
            assert meta[key] is False, key


def test_step9_all_baseline_red_fixtures_are_never_public_passed_comments() -> None:
    for fixture in RUNTIME_SURFACE_BASELINE_RED_FIXTURES:
        surface_report = build_runtime_surface_pre_return_gate_report(
            comment_text=fixture.public_body,
            composer_meta=fixture.composer_meta,
        )
        decision = decide_emlis_observation_display(
            comment_text=fixture.public_body,
            reader_report=_PASSING_READER,
            grounding_report=_PASSING_GROUNDING,
            template_echo_report=_PASSING_TEMPLATE,
            composer_source="ai_generated",
            phase_completion_ready=True,
            runtime_surface_pre_return_gate_report=surface_report,
        )

        assert surface_report["evaluated"] is True, fixture.fixture_id
        assert surface_report["passed"] is False, fixture.fixture_id
        assert decision.observation_status != OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY, fixture.fixture_id
        assert decision.comment_text == "", fixture.fixture_id
        assert "runtime_surface_pre_return_gate_failed" in decision.rejection_reasons
        assert set(fixture.expected_rejection_reasons).issubset(set(decision.rejection_reasons))
        assert decision.gate_trace["display_gate"]["comment_text_allowed"] is False
        assert phase8_display_gate_contract_ready(decision) is True

        dumped_report = dump_runtime_surface_pre_return_gate_report(surface_report)
        dumped_trace = json.dumps(decision.gate_trace, ensure_ascii=False, sort_keys=True)
        for marker in fixture.forbidden_surface_markers:
            assert marker not in dumped_report, (fixture.fixture_id, marker)
            assert marker not in dumped_trace, (fixture.fixture_id, marker)
        _assert_no_public_contract_mutation(surface_report)
        _assert_no_public_contract_mutation(decision.gate_trace["display_gate"])


def test_step9_safe_shallow_v2_surface_is_allowed_without_old_skeleton() -> None:
    evidence = [
        {"span_id": "step9-sh1", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "step9-sh2", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "step9-sh3", "raw_text": "それでも資料のことが気になっている。", "detected_type": "event", "source_field": "memo"},
    ]
    result = CocolonLimitedComposerClient().generate(_payload(evidence))
    text = str(result["comment_text"])
    meta = dict(result["composer_meta"])

    assert result["composer_source"] == "ai_generated"
    assert meta["shallow_v2_used"] is True
    assert meta["shallow_realizer_version"] == "shallow_surface_realizer.v2"
    for marker in _FORBIDDEN_SURFACE_MARKERS:
        assert marker not in text

    surface_report = build_runtime_surface_pre_return_gate_report(comment_text=text, composer_meta=meta)
    assert surface_report["passed"] is True
    assert surface_report["action"] == ACTION_ALLOW
    assert surface_report["surface_template_major"] is False
    assert surface_report["generic_center_phrase_count"] == 0

    decision = _display_decision(text, composer_meta=meta)
    assert decision.observation_status == OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY
    assert decision.comment_text == text
    assert decision.rejection_reasons == []
    assert decision.gate_trace["display_gate"]["comment_text_allowed"] is True
    assert phase8_display_gate_contract_ready(decision) is True


def test_step9_low_information_specificity_anchor_and_anchorless_cases_keep_display_contract() -> None:
    anchored = build_emlis_ai_low_information_observation(
        current_input=_low_info_input("大丈夫かどうか不安"),
        subscription_tier="free",
    )
    anchored_meta = anchored.as_meta()
    assert anchored_meta["low_information_specificity_used"] is True
    assert anchored_meta["uses_safe_anchor"] is True
    assert anchored_meta["safe_anchor_surface_kind"] == "safety_confirmation"
    assert "大丈夫かどうか" in anchored.body
    assert "詳しく残せそうなら、何について大丈夫か気になっているのか残してみませんか" in anchored.body

    anchored_decision = _display_decision(
        anchored.body,
        composer_meta={"profile_key": "low_information", "composer_source": "ai_generated"},
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        quality_meta=anchored_meta,
    )
    assert anchored_decision.observation_status == OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY
    assert anchored_decision.comment_text == anchored.body
    assert anchored_decision.gate_trace["display_gate"]["low_information_quality_passed"] is True
    assert anchored_decision.gate_trace["display_gate"]["comment_text_allowed"] is True

    anchorless = build_emlis_ai_low_information_observation(
        current_input=_low_info_input("あれだけ", emotions=[]),
        subscription_tier="free",
    )
    anchorless_meta = anchorless.as_meta()
    assert anchorless_meta["low_information_specificity_used"] is False
    assert anchorless_meta["safe_anchor_count"] == 0
    assert anchorless_meta["uses_safe_anchor"] is False
    assert "言葉になる前の重さ" in anchorless.body

    anchorless_decision = _display_decision(
        anchorless.body,
        composer_meta={"profile_key": "low_information", "composer_source": "ai_generated"},
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        quality_meta=anchorless_meta,
    )
    assert anchorless_decision.observation_status == OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY
    assert anchorless_decision.comment_text == anchorless.body
    assert anchorless_decision.gate_trace["display_gate"]["comment_text_allowed"] is True
    assert phase8_display_gate_contract_ready(anchored_decision) is True
    assert phase8_display_gate_contract_ready(anchorless_decision) is True
    _assert_no_public_contract_mutation(anchored_meta)
    _assert_no_public_contract_mutation(anchorless_meta)


def test_step9_scorecard_keeps_surface_block_as_release_blocker_not_public_comment() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[1]
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
        rerender_allowed=True,
        rerender_attempted=True,
    )
    decision = decide_emlis_observation_display(
        comment_text=fixture.public_body,
        reader_report=_PASSING_READER,
        grounding_report=_PASSING_GROUNDING,
        template_echo_report=_PASSING_TEMPLATE,
        composer_source="ai_generated",
        phase_completion_ready=True,
        runtime_surface_pre_return_gate_report=report,
    )
    diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=_complete_candidate({"runtime_surface_pre_return_gate": report}),
        display_decision=decision,
        gate_trace=decision.gate_trace,
        diagnostic_summary={"trace_id": "step9-scorecard-surface-lock", "emotion_log_id": "emotion-step9"},
    )
    diagnostic_summary: dict[str, Any] = {}
    phase_gate: dict[str, Any] = {}
    attach_complete_reply_service_diagnostics(
        diagnostic_summary=diagnostic_summary,
        phase_gate=phase_gate,
        diagnostics=diagnostics,
    )
    normalized = normalize_complete_scorecard_event(diagnostics["scorecard_event"])
    aggregate = aggregate_complete_scorecard_events([diagnostics["scorecard_event"]])

    assert report["passed"] is False
    assert decision.observation_status != OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY
    assert decision.comment_text == ""
    assert diagnostics["runtime_surface_pre_return_gate_evaluated"] is True
    assert diagnostics["runtime_surface_pre_return_gate_passed"] is False
    assert diagnostics["surface_template_major_blocked"] is True
    assert normalized["runtime_surface_pre_return_gate_failed_count"] == 1
    assert aggregate["runtime_surface_pre_return_gate_failed_count"] == 1
    assert "runtime_surface_gate_failed_detected" in aggregate["release_blockers"]
    assert "surface_template_major_blocked_detected" in aggregate["release_blockers"]
    assert diagnostic_summary["runtime_surface_pre_return_gate_evaluated"] is True
    assert phase_gate["runtime_surface_step8_diagnostics_ready"] is True

    dumped = json.dumps(
        {"diagnostics": diagnostics, "summary": diagnostic_summary, "phase_gate": phase_gate},
        ensure_ascii=False,
        sort_keys=True,
    )
    for marker in _FORBIDDEN_SURFACE_MARKERS:
        assert marker not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    _assert_no_public_contract_mutation(diagnostics)
    _assert_no_public_contract_mutation(diagnostic_summary)
    _assert_no_public_contract_mutation(phase_gate)
