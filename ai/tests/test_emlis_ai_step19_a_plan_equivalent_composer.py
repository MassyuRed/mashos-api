# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step19 A-1 A-plan-equivalent Composer introduction tests.

The contract is structural: Step19 may change the developer-facing
``composer_model`` to the A-plan-equivalent name, but it must not change the
already grounded text, must not add fallback text, and must keep scoped graph /
common Core / display gate boundaries intact.
"""

from typing import Any

import pytest

from cocolon_text_generation_core.adapters.emlis_observation_composer import ADAPTER_NAME
from emlis_ai_a_plan_equivalent_composer_service import (
    STEP19_A_PLAN_COMPOSER_MODEL,
    STEP19_BASE_COMPOSER_MODEL,
    STEP19_GENERATION_METHOD,
    STEP19_REQUIRED_RUNTIME_TESTS,
    build_step19_a_plan_equivalent_meta,
    promote_step19_a_plan_equivalent_response,
)
from emlis_ai_composer_client_registry import default_composer_flag_state, resolve_emlis_ai_composer_client
from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonAPlanEquivalentComposerClient, CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_types import EvidenceSpan
from fixtures.emlis_ai_step17_broad_input_cases import (
    STEP17_BROAD_DAILY_INPUT_CASES,
    STEP17_CONTEXT_SCOPE_CASES,
    STEP17_FORBIDDEN_SURFACES,
    STEP17_LONG_MEANING_ARC_CASE,
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
    external_evidence_ids = {span.span_id for span in evidence_for_payload if span.span_id not in current_evidence_ids}
    return candidate, current_evidence, current_evidence_ids, external_evidence_ids


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


def _assert_promoted_contract(
    *,
    original: dict[str, Any],
    promoted: dict[str, Any],
    current_evidence: list[EvidenceSpan],
    current_ids: set[str],
) -> None:
    assert promoted["composer_model"] == STEP19_A_PLAN_COMPOSER_MODEL
    assert promoted["generation_method"] == STEP19_GENERATION_METHOD
    assert promoted["comment_text"] == original["comment_text"]
    assert promoted["used_evidence_span_ids"] == original["used_evidence_span_ids"]
    assert set(promoted["used_evidence_span_ids"]).issubset(current_ids)
    assert promoted["composer_source"] == "ai_generated"

    meta = promoted["composer_meta"]
    step19 = meta["step19_a_plan_equivalent"]
    assert step19["phase"] == "A-1"
    assert step19["ready"] is True
    assert step19["can_switch_composer_model"] is True
    assert step19["composer_model_before"] == STEP19_BASE_COMPOSER_MODEL
    assert step19["composer_model_after"] == STEP19_A_PLAN_COMPOSER_MODEL
    assert step19["model_name_changed"] is True
    assert step19["b_plan_gate_preserved"] is True
    assert step19["scoped_graph_preserved"] is True
    assert step19["scoped_grounding_preserved"] is True
    assert step19["fail_closed_preserved"] is True
    assert step19["passed_only_preserved"] is True
    assert step19["comment_text_changed"] is False
    assert step19["external_ai_used"] is False
    assert step19["fallback_observation_sentence_added"] is False
    assert step19["fixed_observation_sentence_added"] is False
    assert step19["external_knowledge_completion_used"] is False
    assert set(STEP19_REQUIRED_RUNTIME_TESTS).issubset(set(step19["required_runtime_tests"]))

    core = meta["text_generation_core"]
    assert core["adapter_name"] == ADAPTER_NAME
    assert core["composer_model"] == STEP19_A_PLAN_COMPOSER_MODEL
    assert core["result"]["composer_model"] == STEP19_A_PLAN_COMPOSER_MODEL
    assert set(core["used_evidence_span_ids"]) == set(promoted["used_evidence_span_ids"])

    for forbidden in STEP17_FORBIDDEN_SURFACES:
        assert forbidden not in promoted["comment_text"]

    template_guard = guard_template_echo(
        comment_text=promoted["comment_text"],
        evidence_spans=current_evidence,
        composer_source=promoted["composer_source"],
        composer_model=promoted["composer_model"],
        generation_method=promoted["generation_method"],
        generation_scope=promoted["generation_scope"],
        coverage_scope=promoted["coverage_scope"],
        composer_meta=promoted["composer_meta"],
        used_evidence_span_ids=promoted["used_evidence_span_ids"],
    )
    assert template_guard.passed is True, template_guard.rejection_reasons


@pytest.mark.parametrize(
    "case",
    [STEP17_BROAD_DAILY_INPUT_CASES[0], STEP17_LONG_MEANING_ARC_CASE],
    ids=["broad_daily", "long_meaning_arc"],
)
def test_step19_promotes_broad_and_long_candidates_to_a1_model_without_text_change(case: dict[str, Any]) -> None:
    candidate, current_evidence, current_ids, _external_ids = _build_candidate(case)
    promoted = promote_step19_a_plan_equivalent_response(
        candidate,
        release_meta=_release_meta(),
        step18_ap0_migration_decision=_green_ap0(),
    )

    _assert_promoted_contract(
        original=candidate,
        promoted=promoted,
        current_evidence=current_evidence,
        current_ids=current_ids,
    )


def test_step19_history_and_cross_core_context_stay_outside_promoted_grounding() -> None:
    for case in STEP17_CONTEXT_SCOPE_CASES:
        candidate, current_evidence, current_ids, external_ids = _build_candidate(case, include_external_context=True)
        assert external_ids
        promoted = promote_step19_a_plan_equivalent_response(
            candidate,
            release_meta=_release_meta(),
            step18_ap0_migration_decision=_green_ap0(),
        )
        _assert_promoted_contract(
            original=candidate,
            promoted=promoted,
            current_evidence=current_evidence,
            current_ids=current_ids,
        )
        assert set(promoted["used_evidence_span_ids"]).isdisjoint(external_ids)
        assert set(promoted["composer_meta"]["text_generation_core"]["used_evidence_span_ids"]).isdisjoint(external_ids)
        for span in case["external_context_spans"]:
            for term in span["must_not_surface_terms"]:
                assert term not in promoted["comment_text"]


def test_step19_surface_variation_series_keeps_no_fallback_and_not_one_fixed_template() -> None:
    outputs: list[str] = []
    tail_sequences: list[tuple[str, ...]] = []
    for case in STEP17_SURFACE_VARIATION_SERIES:
        candidate, current_evidence, current_ids, _external_ids = _build_candidate(case)
        promoted = promote_step19_a_plan_equivalent_response(
            candidate,
            release_meta=_release_meta(),
            step18_ap0_migration_decision=_green_ap0(),
        )
        _assert_promoted_contract(
            original=candidate,
            promoted=promoted,
            current_evidence=current_evidence,
            current_ids=current_ids,
        )
        outputs.append(promoted["comment_text"])
        tail_sequences.append(tuple(promoted["composer_meta"]["step13_surface_realizer"]["used_tail_keys"]))

    assert len(set(outputs)) == len(outputs)
    assert len(set(tail_sequences)) == len(tail_sequences)


def test_step19_meta_does_not_mark_ready_when_ap0_is_not_green() -> None:
    candidate, _current_evidence, _current_ids, _external_ids = _build_candidate(STEP17_BROAD_DAILY_INPUT_CASES[0])
    meta = build_step19_a_plan_equivalent_meta(
        composer_model=candidate["composer_model"],
        response=candidate,
        release_meta=_release_meta(),
        ap0_decision={"decision": "return_to_b_c1", "can_proceed_to_a1": False},
    )

    assert meta["ready"] is False
    assert meta["can_switch_composer_model"] is False
    assert meta["composer_model_before"] == STEP19_BASE_COMPOSER_MODEL
    assert meta["composer_model_after"] == STEP19_BASE_COMPOSER_MODEL
    assert "ap0_not_green" in meta["blocking_reasons"]


def test_step19_registry_can_resolve_a_plan_equivalent_client_only_when_requested() -> None:
    env = {
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
        "COCOLON_EMLIS_DEFAULT_COMPOSER": "a_plan_equivalent",
    }
    flag_state = default_composer_flag_state(env)
    assert flag_state["step19_a_plan_composer_requested"] is True
    assert flag_state["requested_composer_model"] == STEP19_A_PLAN_COMPOSER_MODEL

    resolution = resolve_emlis_ai_composer_client(
        env=env,
        release_allowed=True,
        release_meta=_release_meta(),
    )
    assert resolution.default_client_used is True
    assert isinstance(resolution.composer_client, CocolonAPlanEquivalentComposerClient)
    assert resolution.composer_model == STEP19_A_PLAN_COMPOSER_MODEL

    limited_resolution = resolve_emlis_ai_composer_client(
        env={"COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true"},
        release_allowed=True,
        release_meta=_release_meta(),
    )
    assert isinstance(limited_resolution.composer_client, CocolonLimitedComposerClient)
    assert not isinstance(limited_resolution.composer_client, CocolonAPlanEquivalentComposerClient)
    assert limited_resolution.composer_model == STEP19_BASE_COMPOSER_MODEL


@pytest.mark.asyncio
async def test_step19_runtime_meta_is_attached_after_step18_without_breaking_passed_only(monkeypatch: pytest.MonkeyPatch) -> None:
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
        user_id="step19-runtime-user",
        subscription_tier="free",
        current_input={
            "id": "step19-runtime-input",
            "created_at": "2026-05-15T00:00:00Z",
            "memo": "昨日から疲れが抜けない。今日は少し休みたい。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["体調"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    step19 = reply.meta["step19_a_plan_equivalent_composer"]
    multi = reply.meta["multi_perspective"]
    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = multi["phase_gate"]

    assert step19 == reply.meta["step19_a_plan_equivalent"]
    assert step19 == multi["step19_a_plan_equivalent_composer"]
    assert step19 == diagnostic["step19_a_plan_equivalent_composer"]
    assert step19["phase"] == "A-1"
    assert step19["implementation_ready"] is True
    assert step19["b_plan_gate_preserved"] is True
    assert step19["scoped_graph_preserved"] is True
    assert step19["fail_closed_preserved"] is True
    assert step19["passed_only_preserved"] is True
    assert "ap0_not_green" in step19["blocking_reasons"]
    assert phase_gate["step19_a_plan_equivalent_ready"] is False
    assert reply.comment_text == "" or reply.meta["observation_status"] == "passed"
