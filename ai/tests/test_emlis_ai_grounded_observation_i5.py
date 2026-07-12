# -*- coding: utf-8 -*-
from __future__ import annotations

"""I5 reply cutover, semantic Gate, metadata truth, and public-contract tests."""

import asyncio
from dataclasses import replace
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_reply_service import render_emlis_ai_reply


SERVICE_ROOT = Path(__file__).resolve().parents[1] / "services" / "ai_inference"


def _case(case_id: str):
    return next(
        case
        for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES
        if case.case_id == case_id
    )


def _render(current_input: dict[str, Any]):
    return asyncio.run(
        render_emlis_ai_reply(
            user_id="i5-test-user",
            subscription_tier="free",
            current_input=current_input,
        )
    )


def _assert_body_free(value: Any, raw_values: tuple[str, ...]) -> None:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True)
    for raw in raw_values:
        if raw:
            assert raw not in payload
    forbidden_keys = {
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "surface_text",
        "candidate_body",
    }

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            assert not (forbidden_keys & set(item))
            for nested in item.values():
                visit(nested)
        elif isinstance(item, list):
            for nested in item:
                visit(nested)

    visit(value)


@pytest.mark.parametrize("case_id", ["A", "B", "C", "D"])
def test_i5_known_inputs_use_one_canonical_reply_path_with_truthful_meta(case_id: str) -> None:
    case = _case(case_id)
    reply = _render(case.as_current_input())
    gate = reply.meta["grounded_observation"]

    assert reply.comment_text.strip()
    assert reply.meta["observation_status"] == "passed"
    assert reply.meta["public_observation_status"] == "passed"
    assert reply.meta["generation_path"] == (
        "grounded_observation_plan_sentence_surface_canonical_v1"
    )
    assert reply.meta["generation_method"] == "functional_atom_grounded_realizer"
    assert reply.meta["composer_source"] == "grounded_plan_realizer"
    assert reply.meta["delivery_status"] == "passed"
    assert reply.meta["fixed_sentence_template_used"] is False
    assert reply.meta["case_specific_route_used"] is False
    assert reply.meta["example_cue_route_used"] is False
    assert reply.meta["label_only_assembly_used"] is False
    assert reply.meta["synthetic_evidence_id_used"] is False
    assert gate["plan_validity_gate"] == "passed"
    assert gate["evidence_resolution_gate"] == "passed"
    assert gate["required_coverage_gate"] == "passed"
    assert gate["text_semantic_retention_gate"] == "passed"
    assert gate["anti_template_gate"] == "passed"
    assert gate["question_dominance_gate"] == "passed"
    assert gate["depth_adequacy_gate"] == "passed"
    assert gate["semantic_quality_gate"] == "passed"
    assert gate["delivery_status"] == "passed"
    assert gate["product_readfeel_status"] == "not_evaluated"
    assert gate["public_reply_path_connected"] is True
    assert reply.meta["p5_p6_overlay"]["overlay_applied"] is False
    assert reply.meta["p5_p6_overlay"]["p5_status"] == "human_qa_pending"
    assert reply.meta["p5_p6_overlay"]["p6_status"] == "p5_dependency_hold"
    _assert_body_free(
        gate,
        (case.thought_text, case.action_text, reply.comment_text),
    )


def test_i5_public_meta_keeps_passed_plus_comment_contract_without_new_public_keys() -> None:
    reply = _render(_case("B").as_current_input())
    public = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(reply.comment_text),
        subscription_tier="free",
    )

    assert public["observation_status"] == "passed"
    assert "grounded_observation" not in public
    assert "semantic_quality_gate" not in public
    assert "product_readfeel_status" not in public
    assert "generation_path" not in public
    assert "composer_source" not in public
    assert reply.comment_text not in json.dumps(public, ensure_ascii=False)


@pytest.mark.parametrize(
    ("current_input", "expected_response_kind"),
    [
        (
            {"memo": "安全が保てない。助けが必要。", "emotions": ["不安"]},
            "safety_support_required",
        ),
        (
            {"memo": "もう消えたい。今日で終わりにしたい。", "emotions": ["悲しみ"]},
            "safety_blocked_emergency",
        ),
    ],
)
def test_i5_separate_safety_owner_is_not_converted_to_generic_observation(
    current_input: dict[str, Any],
    expected_response_kind: str,
) -> None:
    reply = _render(current_input)
    gate = reply.meta["grounded_observation"]

    assert reply.comment_text == ""
    assert reply.meta["observation_status"] == "safety_blocked"
    assert gate["semantic_quality_gate"] == "not_evaluated"
    assert gate["rejection_reasons"] == ["separate_safety_surface_owner_preserved"]
    assert reply.meta["internal_response_contract"]["response_kind"] == expected_response_kind


def test_i5_gate_fails_closed_when_runtime_fact_reports_fixed_semantic_surface() -> None:
    current_input = normalize_emlis_current_input(_case("C").as_current_input())
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    fixed_surface = replace(surface, completed_semantic_template_used=True)

    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=fixed_surface,
        resolver=resolver,
    )

    assert report.semantic_quality_gate == "failed"
    assert report.anti_template_gate == "failed"
    assert report.fixed_semantic_surface_used is True
    assert "grounded_anti_template_failed" in report.rejection_reasons


def test_i5_public_reply_call_graph_has_no_pre_i5_substantive_body_owner() -> None:
    source = (SERVICE_ROOT / "emlis_ai_reply_service.py").read_text(encoding="utf-8")
    function_source = inspect.getsource(render_emlis_ai_reply)

    assert "build_grounded_observation_plan(" in function_source
    assert "build_grounded_sentence_plan(" in function_source
    assert "evaluate_grounded_observation_gate(" in function_source
    for retired_owner in (
        "emlis_ai_complete_initial_surface_recomposition",
        "emlis_ai_gate_recovery_loop",
        "emlis_ai_low_information_observation_composer",
        "emlis_ai_limited_grounding_reception_surface",
        "emlis_ai_self_denial_safe_state_answer",
        "emlis_reception_assistance_dictionary",
        "compose_emlis_conversation_candidate",
        "recover_emlis_gate_failure",
    ):
        assert retired_owner not in source
