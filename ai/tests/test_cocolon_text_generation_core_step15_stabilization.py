# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from cocolon_text_generation_core import (  # noqa: E402
    COMMON_QUALITY_PART_KEYS,
    CORE_ID_EMLIS,
    STEP15_PHASE_LABEL,
    STEP15_STABILIZATION_NAME,
    TextGenerationResult,
    build_core_stabilization_report,
    emlis_observation_output_contract,
)
from cocolon_text_generation_core.adapters.emlis_observation_composer import (  # noqa: E402
    ADAPTER_NAME,
    build_emlis_observation_core_payload,
    evaluate_emlis_observation_candidate,
)
from cocolon_text_generation_core.policies import STATUS_GENERATED, STATUS_UNAVAILABLE  # noqa: E402
from emlis_ai_conversation_composer_service import build_conversation_composer_payload  # noqa: E402
from emlis_ai_evidence_ledger_service import build_evidence_ledger  # noqa: E402
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient  # noqa: E402
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope  # noqa: E402
from emlis_ai_observation_integrator_service import integrate_perspective_board  # noqa: E402
from emlis_ai_perspective_board import build_perspective_board  # noqa: E402
from emlis_ai_perspective_observers import run_perspective_observers  # noqa: E402

SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _payload_for(memo: str = SAMPLE_MEMO):
    current_input = {
        "id": "step15-common-core-stabilization-test",
        "created_at": "2026-05-14T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }
    evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    assert scope.scope_status == "eligible"
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id="step15-common-core-stabilization-test",
    )
    return payload, evidence, scope


def test_step15_emlis_adapter_reports_common_core_stabilization_without_contract_change() -> None:
    payload, evidence, scope = _payload_for()
    result = CocolonLimitedComposerClient().generate(payload)

    assert result["status"] == "generated"
    assert result["comment_text"]
    assert set(result["used_evidence_span_ids"]).issubset({span.span_id for span in evidence})
    assert set(result["used_claim_ids"]).issubset(set(scope.included_claim_ids))

    core_meta = result["composer_meta"]["text_generation_core"]
    step15 = core_meta["step15_common_core_stabilization"]

    assert step15["report_name"] == STEP15_STABILIZATION_NAME
    assert step15["phase"] == STEP15_PHASE_LABEL
    assert step15["core_id"] == CORE_ID_EMLIS
    assert step15["passed"] is True
    assert step15["common_shapes_ready"] is True
    assert step15["issue_codes"] == []
    for key in COMMON_QUALITY_PART_KEYS:
        assert step15["shared_quality_parts"][key] is True
    assert step15["core_specific_contract"]["core_specific_composer"] == "EmlisObservationComposer"
    assert step15["core_specific_contract"]["comment_text_contract"] == "passed_only"
    assert step15["core_specific_contract"]["passed_only_display"] is True
    assert step15["core_specific_contract"]["scoped_grounding"] is True
    assert step15["core_specific_contract"]["db_rename_or_drop"] is False
    assert step15["core_specific_contract"]["public_api_route_change"] is False
    assert step15["core_specific_contract"]["public_response_key_change"] is False
    assert result["composer_meta"]["core_text_generation"] == core_meta
    assert core_meta["common_core_stabilization"] == step15


def test_step15_report_fails_closed_when_common_shapes_are_missing() -> None:
    payload, candidate = build_emlis_observation_core_payload(
        composer_payload={"current_input_id": "step15-missing-shapes"},
        evidence_items=[],
        phrase_units=[],
        sentence_plans=[],
        comment_text="根拠がある範囲だけを扱います。",
        used_evidence_span_ids=[],
        used_phrase_unit_ids=[],
        coverage_scope="partial_observation",
        composer_model="cocolon_limited_composer.v1",
        composer_meta={"covered_roles": ["positive_state"]},
        response={"composer_source": "ai_generated", "fixed_string_renderer_used": False},
    )
    result = TextGenerationResult(
        status=STATUS_UNAVAILABLE,
        text=candidate.text,
        used_evidence_span_ids=candidate.used_evidence_span_ids,
        rejection_reasons=("source_evidence_missing",),
    )
    report = build_core_stabilization_report(
        payload=payload,
        result=result,
        expected_core_id=CORE_ID_EMLIS,
        output_contract=emlis_observation_output_contract(),
        require_guard_results=True,
    ).as_meta()

    assert report["passed"] is False
    assert report["common_shapes_ready"] is False
    assert "common_evidence_span_missing" in report["issue_codes"]
    assert "common_phrase_unit_missing" in report["issue_codes"]
    assert "common_sentence_plan_missing" in report["issue_codes"]
    assert "common_guard_results_missing" in report["issue_codes"]


def test_step15_detects_emlis_contract_boundary_drift() -> None:
    evidence_items = [
        {
            "span_id": "s1",
            "raw_text": "少し安心したけど、不安も戻った",
            "detected_type": "positive_state",
            "confidence": 0.9,
            "source_field": "memo",
        }
    ]
    phrase_units = [
        {
            "phrase_unit_id": "pu1",
            "evidence_span_id": "s1",
            "raw_text": "少し安心したけど、不安も戻った",
            "compressed_text": "安心のあとに不安も戻った",
            "role": "positive_state",
            "must_keep": True,
            "quality_flags": [],
        }
    ]
    sentence_plans = [
        {
            "sentence_plan_id": "sp1",
            "phrase_unit_ids": ["pu1"],
            "relation_type": "observation",
            "line_role": "receive",
            "must_include": True,
        }
    ]
    evaluation = evaluate_emlis_observation_candidate(
        composer_payload={"current_input_id": "step15-contract-drift"},
        evidence_items=evidence_items,
        phrase_units=phrase_units,
        sentence_plans=sentence_plans,
        comment_text="安心のあとに不安も戻った流れがありました。",
        used_evidence_span_ids=["s1"],
        used_phrase_unit_ids=["pu1"],
        coverage_scope="partial_observation",
        composer_model="cocolon_limited_composer.v1",
        composer_meta={"covered_roles": ["positive_state"]},
        response={"composer_source": "ai_generated", "fixed_string_renderer_used": False},
    )
    assert evaluation.result.status == STATUS_GENERATED

    drifted_contract = emlis_observation_output_contract()
    drifted_contract["comment_text_contract"] = "any_status"
    drifted_contract["public_response_key_change"] = True
    report = build_core_stabilization_report(
        payload=evaluation.payload,
        result=evaluation.result,
        expected_core_id=CORE_ID_EMLIS,
        output_contract=drifted_contract,
    ).as_meta()

    assert report["passed"] is False
    assert "emlis_comment_text_contract_not_passed_only" in report["issue_codes"]
    assert "public_response_key_change_requested" in report["issue_codes"]


@pytest.mark.asyncio
async def test_phase0_step15_render_meta_keeps_common_core_passed_but_public_surface_fail_closed(monkeypatch) -> None:
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step15-render-user",
        subscription_tier="free",
        current_input={
            "id": "step15-render-input",
            "created_at": "2026-05-14T00:00:00Z",
            "memo": SAMPLE_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    step15 = multi["step15_common_core_stabilization"]
    candidate = multi["composer_candidate"]

    # Phase 6 confirms the completed surface feeds the public display contract
    # without changing response keys or relaxing the Display Gate.
    completion = candidate["composer_meta"]["environment_state_output_scope_marker_completion"]
    assert candidate["status"] == "generated"
    assert candidate["comment_text"]
    assert "今回の入力では" in candidate["comment_text"]
    assert candidate["rejection_reasons"] == []
    assert completion["applied"] is True
    assert completion["display_gate_relaxed"] is False
    assert multi["scoped_grounding"]["enabled"] is True
    assert multi["phase_gate"]["comment_text_allowed"] is True
    assert multi["phase_gate"]["step15_common_core_stabilization_ready"] is True
    assert multi["phase_gate"]["common_core_stabilization_ready"] is True
    assert step15["passed"] is True
    assert step15["core_specific_contract"]["comment_text_contract"] == "passed_only"
    assert multi["common_core_stabilization"] == step15
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text
    assert "今回の入力では" in reply.comment_text
