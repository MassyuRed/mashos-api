# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))

from cocolon_text_generation_core.adapters.emlis_observation_composer import (  # noqa: E402
    ADAPTER_NAME,
    evaluate_emlis_observation_candidate,
)
from cocolon_text_generation_core.policies import CORE_ID_EMLIS, STATUS_GENERATED  # noqa: E402
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
        "id": "phase7-core-adapter-test",
        "created_at": "2026-05-11T00:00:00Z",
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
        trace_id="phase7-core-adapter-test",
    )
    return payload, evidence, scope


def test_emlis_limited_composer_attaches_common_core_meta_without_contract_change():
    payload, evidence, scope = _payload_for()
    result = CocolonLimitedComposerClient().generate(payload)

    assert result["composer_source"] == "ai_generated"
    assert result["status"] == "generated"
    assert result["fixed_string_renderer_used"] is False
    assert result["comment_text"]
    assert set(result["used_evidence_span_ids"]).issubset({span.span_id for span in evidence})
    assert set(result["used_claim_ids"]).issubset(set(scope.included_claim_ids))

    core_meta = result["composer_meta"]["text_generation_core"]
    assert core_meta["adapter_name"] == ADAPTER_NAME
    assert core_meta["core_id"] == CORE_ID_EMLIS
    assert core_meta["status"] == STATUS_GENERATED
    assert core_meta["passed"] is True
    assert core_meta["quality_flags"] == []
    assert core_meta["rejection_reasons"] == []
    assert set(core_meta["used_evidence_span_ids"]) == set(result["used_evidence_span_ids"])
    assert core_meta["payload"]["phrase_unit_count"] > 0
    assert core_meta["payload"]["sentence_plan_count"] > 0
    assert result["composer_meta"]["core_text_generation"] == core_meta


def test_emlis_observation_adapter_rejects_broken_surface_fail_closed():
    evidence_items = [
        {
            "span_id": "s1",
            "raw_text": "また急に不安になった",
            "detected_type": "anxiety",
            "confidence": 0.86,
            "source_field": "memo",
        }
    ]
    phrase_units = [
        {
            "phrase_unit_id": "pu1",
            "evidence_span_id": "s1",
            "raw_text": "また急に不安になった",
            "compressed_text": "また急に不安になった",
            "role": "anxiety_return",
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
        composer_payload={"current_input_id": "phase7-broken-surface"},
        evidence_items=evidence_items,
        phrase_units=phrase_units,
        sentence_plans=sentence_plans,
        comment_text="Emlisです。\n不安。\nまた急に不安になったがつながっています。",
        used_evidence_span_ids=["s1"],
        used_phrase_unit_ids=["pu1"],
        coverage_scope="partial_observation",
        composer_model="cocolon_limited_composer.v1",
        composer_meta={"covered_roles": ["anxiety_return"]},
        response={"composer_source": "ai_generated", "fixed_string_renderer_used": False},
    )

    assert evaluation.passed is False
    assert evaluation.result.text == ""
    assert "emotion_label_body_line" in evaluation.result.rejection_reasons
    assert "generic_relation_suffix" in evaluation.result.rejection_reasons
    assert evaluation.as_meta()["adapter_name"] == ADAPTER_NAME


@pytest.mark.asyncio
async def test_phase2_render_meta_completes_scope_marker_without_common_core_regression(monkeypatch):
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase7-core-adapter-render-user",
        subscription_tier="free",
        current_input={
            "id": "phase7-core-adapter-render-input",
            "created_at": "2026-05-11T00:00:00Z",
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
    core_meta = multi["text_generation_core"]
    candidate = multi["composer_candidate"]
    completion = candidate["composer_meta"]["environment_state_output_scope_marker_completion"]
    reason_counter = multi["diagnostic_summary"]["release_ladder_guard"]["reason_counter"]

    assert multi["composer_source"] == "ai_generated"
    assert candidate["status"] == "generated"
    assert candidate["comment_text"]
    assert "今回の入力では" in candidate["comment_text"]
    assert candidate["rejection_reasons"] == []
    assert completion["applied"] is True
    assert completion["before_marker_present"] is False
    assert completion["after_marker_present"] is True
    assert core_meta["adapter_name"] == ADAPTER_NAME
    assert core_meta["passed"] is True
    assert multi["core_text_generation"] == core_meta
    assert multi["phase_gate"]["emlis_observation_composer_adapter_ready"] is True
    assert multi["phase_gate"]["text_generation_core_ready"] is True
    assert "environment_state_output_scope_marker_missing" not in reason_counter
    # Phase 6 confirms the completed surface can pass the public display
    # contract, while the scope-marker repair itself still does not relax gates.
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text
    assert "今回の入力では" in reply.comment_text
