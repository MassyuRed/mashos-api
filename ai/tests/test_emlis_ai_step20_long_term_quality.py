# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step20 A-2 long-term operation quality tests for EmlisAI.

The Step20 contract is intentionally meta-only.  It checks long-term readiness
signals such as previous-output similarity, surface variation, history/cross-core
scope, QA metrics, and distance drift without changing ``comment_text``.
"""

from typing import Any

import pytest

from emlis_ai_a_plan_equivalent_composer_service import promote_step19_a_plan_equivalent_response
from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_long_term_quality_service import (
    STEP20_PHASE,
    STEP20_REQUIRED_CHECKS,
    STEP20_SIMILARITY_THRESHOLD,
    STEP20_VERSION,
    build_step20_long_term_quality_meta,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_types import EvidenceSpan
from fixtures.emlis_ai_step17_broad_input_cases import (
    STEP17_BROAD_DAILY_INPUT_CASES,
    STEP17_CONTEXT_SCOPE_CASES,
    STEP17_SURFACE_VARIATION_SERIES,
)


def _current_input(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": case["case_id"],
        "created_at": "2026-05-15T00:00:00Z",
        "memo": case["memo"],
        "memo_action": "",
        "emotion_details": [{"type": case.get("emotion") or "自己理解", "strength": "medium"}],
        "emotions": [case.get("emotion") or "自己理解"],
        "category": [case.get("category") or "生活"],
    }


def _external_spans(case: dict[str, Any]) -> list[EvidenceSpan]:
    spans: list[EvidenceSpan] = []
    for raw in case.get("external_context_spans") or []:
        text = str(raw["raw_text"])
        spans.append(
            EvidenceSpan(
                span_id=str(raw["span_id"]),
                raw_text=text,
                start_index=0,
                end_index=len(text),
                detected_type=str(raw.get("detected_type") or "context"),
                confidence=1.0,
                source_field=str(raw.get("source_field") or "history"),
            )
        )
    return spans


def _build_candidate(case: dict[str, Any], *, include_external_context: bool = False):
    current_input = _current_input(case)
    current_evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(current_evidence)
    board = build_perspective_board(evidence_spans=current_evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=current_evidence)
    evidence_for_payload = [*current_evidence, *(_external_spans(case) if include_external_context else [])]
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence_for_payload,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id=case["case_id"],
        limited_observation_scope=scope,
    )
    candidate = CocolonLimitedComposerClient().generate(payload)
    current_evidence_ids = {span.span_id for span in current_evidence}
    return candidate, current_evidence, current_evidence_ids, evidence_for_payload


def _release_meta(stage: str = "limited_cases") -> dict[str, Any]:
    return {
        "enabled": True,
        "attempted": True,
        "stage": stage,
        "cohort": "limited_case",
        "reason_code": "scope_limited_case_allowed",
        "rejection_reasons": [],
    }


def _green_ap0() -> dict[str, Any]:
    return {
        "version": "emlis.step18_ap0_migration_decision.v1",
        "phase": "A-P0",
        "decision_ready": True,
        "can_proceed_to_a1": True,
        "can_enter_step19": True,
        "decision": "proceed_to_step19_a1",
        "return_steps": [],
        "unmet_checks": [],
    }


def _promoted(case: dict[str, Any], *, include_external_context: bool = False):
    candidate, current_evidence, current_ids, evidence_for_payload = _build_candidate(
        case,
        include_external_context=include_external_context,
    )
    promoted = promote_step19_a_plan_equivalent_response(
        candidate,
        release_meta=_release_meta(),
        step18_ap0_migration_decision=_green_ap0(),
    )
    return promoted, current_evidence, current_ids, evidence_for_payload


def _previous_record(response: dict[str, Any], *, created_at: str) -> dict[str, Any]:
    meta = dict(response.get("composer_meta") or {})
    return {
        "created_at": created_at,
        "comment_text": response["comment_text"],
        "composer_model": response["composer_model"],
        "composer_meta": meta,
        "profile_key": meta.get("profile_key"),
        "surface_tail_keys": list((meta.get("step13_surface_realizer") or {}).get("used_tail_keys") or []),
        "used_evidence_span_ids": list(response.get("used_evidence_span_ids") or []),
    }


def test_step20_marks_long_term_green_with_previous_sample_and_varied_surface() -> None:
    previous, _prev_evidence, _prev_ids, _prev_payload_evidence = _promoted(STEP17_SURFACE_VARIATION_SERIES[0])
    current, current_evidence, current_ids, _payload_evidence = _promoted(STEP17_SURFACE_VARIATION_SERIES[1])

    step20 = build_step20_long_term_quality_meta(
        response=current,
        previous_outputs=[_previous_record(previous, created_at="2026-05-14T23:50:00Z")],
        evidence_spans=current_evidence,
        used_evidence_span_ids=current["used_evidence_span_ids"],
        current_evidence_span_ids=sorted(current_ids),
        step19_a_plan_equivalent=current["composer_meta"]["step19_a_plan_equivalent"],
        current_input={"id": "step20-green-current"},
    )

    assert step20["version"] == STEP20_VERSION
    assert step20["phase"] == STEP20_PHASE
    assert step20["implementation_ready"] is True
    assert step20["ready"] is True
    assert step20["long_term_operation_ready"] is True
    assert step20["can_continue_a_plan_operation"] is True
    assert step20["previous_output_sample_available"] is True
    assert set(STEP20_REQUIRED_CHECKS).issubset(set(step20["required_checks"]))
    assert all(check["green"] is True for check in step20["checks"].values())
    assert step20["previous_output_similarity"]["max_similarity"] < STEP20_SIMILARITY_THRESHOLD
    assert step20["surface_variation_policy"]["passed"] is True
    assert step20["history_completion_allowed"] is False
    assert step20["history_is_evidence_only"] is True
    assert step20["comment_text_changed"] is False
    assert step20["comment_text_contract_preserved"] is True
    assert step20["passed_only_preserved"] is True
    assert step20["db_physical_name_changed"] is False
    assert step20["api_route_changed"] is False
    assert step20["public_response_key_change"] is False


def test_step20_blocks_same_profile_duplicate_surface_and_text_similarity() -> None:
    current, current_evidence, current_ids, _payload_evidence = _promoted(STEP17_BROAD_DAILY_INPUT_CASES[0])
    previous = _previous_record(current, created_at="2026-05-14T23:50:00Z")

    step20 = build_step20_long_term_quality_meta(
        response=current,
        previous_outputs=[previous],
        evidence_spans=current_evidence,
        used_evidence_span_ids=current["used_evidence_span_ids"],
        current_evidence_span_ids=sorted(current_ids),
        step19_a_plan_equivalent=current["composer_meta"]["step19_a_plan_equivalent"],
    )

    assert step20["ready"] is False
    assert step20["previous_output_similarity"]["max_similarity"] >= STEP20_SIMILARITY_THRESHOLD
    assert step20["checks"]["previous_output_similarity"]["green"] is False
    assert step20["checks"]["surface_variation_policy"]["green"] is False
    assert "previous_output_similarity_too_high" in step20["blocking_reasons"]
    assert "same_profile_tail_repetition" in step20["blocking_reasons"]


def test_step20_treats_history_and_cross_core_as_evidence_only_not_completion() -> None:
    case = STEP17_CONTEXT_SCOPE_CASES[0]
    current, current_evidence, current_ids, evidence_for_payload = _promoted(case, include_external_context=True)
    previous_case, _prev_evidence, _prev_ids, _prev_payload = _promoted(STEP17_BROAD_DAILY_INPUT_CASES[4])
    bad_response = dict(current)
    bad_response["comment_text"] = f"{current['comment_text']}\n前から本当は同じ性格が続いています。"

    step20 = build_step20_long_term_quality_meta(
        response=bad_response,
        previous_outputs=[_previous_record(previous_case, created_at="2026-05-14T23:50:00Z")],
        evidence_spans=evidence_for_payload,
        used_evidence_span_ids=current["used_evidence_span_ids"],
        current_evidence_span_ids=sorted(current_ids),
        history_scope={"enabled": True, "policy": "history_is_evidence_only"},
        cross_core_scope={"cross_core_enabled": False, "policy": "cross_core_context_is_evidence_only"},
        step19_a_plan_equivalent=current["composer_meta"]["step19_a_plan_equivalent"],
    )

    assert step20["history_completion_allowed"] is False
    assert step20["overclaim_history_completion"] is True
    assert step20["ready"] is False
    assert step20["checks"]["history_cross_core_scope"]["green"] is False
    assert "overclaim_history_completion" in step20["blocking_reasons"]
    assert any(
        surface in step20["history_cross_core_scope"]["unsupported_history_completion_surfaces"]
        for surface in ("前から", "本当は", "性格")
    )


@pytest.mark.asyncio
async def test_step20_runtime_meta_is_attached_as_qa_only_without_breaking_display_contract(monkeypatch: pytest.MonkeyPatch) -> None:
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
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "limited_cases")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step20-runtime-user",
        subscription_tier="free",
        current_input={
            "id": "step20-runtime-input",
            "created_at": "2026-05-15T00:00:00Z",
            "memo": "昨日から疲れが抜けない。今日は少し休みたい。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["体調"],
            "previous_emlis_outputs": [
                {
                    "created_at": "2026-05-14T23:40:00Z",
                    "comment_text": "Emlisです。今日は洗い物を少し終えて、台所が整ったことで落ち着きが戻っていました。",
                    "profile_key": "positive_progress",
                    "surface_tail_keys": ["progress", "calm"],
                }
            ],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    step20 = reply.meta["step20_long_term_quality"]
    diagnostic = reply.meta["diagnostic_summary"]
    multi = reply.meta["multi_perspective"]
    phase_gate = multi["phase_gate"]

    assert step20 == reply.meta["a2_long_term_quality"]
    assert step20 == reply.meta["long_term_quality"]
    assert step20 == diagnostic["step20_long_term_quality"]
    assert step20 == multi["step20_long_term_quality"]
    assert step20["phase"] == STEP20_PHASE
    assert step20["implementation_ready"] is True
    assert step20["previous_output_sample_available"] is True
    assert step20["history_completion_allowed"] is False
    assert step20["comment_text_contract_preserved"] is True
    assert step20["passed_only_preserved"] is True
    assert phase_gate["step20_long_term_quality_ready"] == step20["ready"]
    assert phase_gate["step20_previous_output_sample_available"] is True
    assert phase_gate["step20_history_is_evidence_only"] == step20["history_is_evidence_only"]
    assert reply.comment_text == "" or reply.meta["observation_status"] == "passed"
