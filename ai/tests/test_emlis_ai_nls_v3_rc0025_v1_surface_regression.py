# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0025 v1 independent-event Surface and Step 11 diagnostic regressions."""

import asyncio
from dataclasses import replace
from pathlib import Path
import sys
from unittest.mock import patch
from typing import Any, Mapping

from helpers.emlis_nls_v2_s2_development import load_development_cases
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
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_types import ReplyEnvelope


_TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import emlis_nls_v3_step11_regression as step11_regression  # noqa: E402


_DEVELOPMENT_CASES = {
    case.case_id: case for case in load_development_cases()
}
_TARGET_CASE_REF = "NLS2-F03-D03"
_CONTROL_CASE_REFS = ("NLS2-F09-D01", "NLS2-F14-D03")
_REPEATED_STEM_REJECTION = (
    "relation_surface_stem_repetition_without_new_role"
)
_GENERIC_INDEPENDENT_EVENTS = {
    "memo": (
        "朝に端末を落として、画面の保護シートを割ってしまった。"
        "交換の手間が増えて困った。"
    ),
    "memo_action": "使える端末で必要な連絡を先に済ませた。",
    "emotions": ["悲しみ"],
    "category": ["生活"],
}


def _artifacts(current_input: Mapping[str, Any]):
    normalized = normalize_emlis_current_input(dict(current_input))
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(
        normalized,
        evidence_spans=spans,
    )
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    return plan, resolver, sentence_plan, surface, report


def _reply(current_input: Mapping[str, Any]) -> ReplyEnvelope:
    return asyncio.run(
        render_emlis_ai_reply(
            user_id="nls-v3-rc0025-v1-surface-regression",
            subscription_tier="free",
            current_input=dict(current_input),
        )
    )


def _assert_public_reply(reply: ReplyEnvelope) -> None:
    assert type(reply.comment_text) is str
    assert reply.comment_text.strip()
    assert reply.meta["public_observation_status"] == "passed"
    assert reply.meta["delivery_status"] == "passed"
    assert reply.meta["public_comment_present"] is True
    assert reply.meta["case_specific_route_used"] is False
    assert reply.meta["example_cue_route_used"] is False
    assert _REPEATED_STEM_REJECTION not in reply.meta["rejection_reasons"]
    assert (
        reply.meta["grounded_observation"]["runtime_final_contract_guard"]
        == "passed"
    )


def test_rc0025_development42_f03_d03_returns_public_v1_reply() -> None:
    """Reproduce the first rc0024 Development42 stop through production v1."""

    case = _DEVELOPMENT_CASES[_TARGET_CASE_REF]

    _assert_public_reply(_reply(case.current_input))


def test_rc0025_generic_independent_events_share_a_neutral_surface_owner() -> None:
    """Repair the common structure without a case, family, or text route."""

    plan, _resolver, sentence_plan, surface, report = _artifacts(
        _GENERIC_INDEPENDENT_EVENTS
    )
    required_ids = set(plan.coverage_requirements.required_nucleus_ids)
    event_ids = tuple(
        nucleus.nucleus_id
        for nucleus in plan.nuclei
        if nucleus.nucleus_id in required_ids and nucleus.kind == "event"
    )
    assert len(event_ids) == 2
    assert plan.coverage_requirements.required_relation_ids == ()

    event_owners = tuple(
        line
        for line in sentence_plan.lines
        if set(event_ids) <= set(line.binding.nucleus_ids)
    )
    assert len(event_owners) == 1
    event_owner = event_owners[0]
    assert event_owner.binding.nucleus_ids == event_ids
    assert event_owner.binding.relation_ids == ()
    assert event_owner.binding.evidence_span_ids == tuple(
        span_id
        for nucleus in plan.nuclei
        if nucleus.nucleus_id in event_ids
        for span_id in nucleus.source_span_ids
    )
    assert (
        "observation_surface_role:coexisting_event_arc"
        in event_owner.binding.functional_atom_ids
    )
    assert "semantic_arc:coexisting_event_arc" in (
        event_owner.binding.functional_atom_ids
    )
    assert "observation_surface_role:coexisting_observation" not in (
        event_owner.binding.functional_atom_ids
    )

    assert surface.required_coverage_preserved is True
    assert surface.text.strip()
    assert report.passed is True
    assert report.public_observation_status == "passed"
    assert _REPEATED_STEM_REJECTION not in report.rejection_reasons
    _assert_public_reply(_reply(_GENERIC_INDEPENDENT_EVENTS))


def test_rc0025_gate_still_rejects_same_stem_with_same_role() -> None:
    """The repair must not weaken the anti-template Gate."""

    plan, resolver, sentence_plan, surface, _report = _artifacts(
        _GENERIC_INDEPENDENT_EVENTS
    )
    observation_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role != "human_follow"
    )
    assert len(observation_lines) >= 2
    first, second = observation_lines[:2]
    first_role_atoms = tuple(
        atom
        for atom in first.binding.functional_atom_ids
        if atom.startswith(("observation_surface_role:", "semantic_arc:"))
    )
    assert first_role_atoms
    second_atoms = tuple(
        atom
        for atom in second.binding.functional_atom_ids
        if not atom.startswith(("observation_surface_role:", "semantic_arc:"))
    )
    repeated_binding = replace(
        second.binding,
        functional_atom_ids=(*second_atoms, *first_role_atoms),
    )
    repeated_second = replace(second, binding=repeated_binding)
    mutated_sentence_plan = replace(
        sentence_plan,
        lines=tuple(
            repeated_second if line is second else line
            for line in sentence_plan.lines
        ),
    )

    surface_by_id = {line.sentence_id: line for line in surface.lines}
    first_surface = surface_by_id[first.binding.sentence_id]
    mutated_surface = replace(
        surface,
        lines=tuple(
            replace(
                line,
                text=first_surface.text,
                binding=repeated_binding,
            )
            if line.sentence_id == second.binding.sentence_id
            else line
            for line in surface.lines
        ),
    )
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=mutated_sentence_plan,
        surface_result=mutated_surface,
        resolver=resolver,
    )

    assert report.passed is False
    assert _REPEATED_STEM_REJECTION in report.rejection_reasons


def test_rc0025_existing_v1_controls_remain_public() -> None:
    for case_ref in _CONTROL_CASE_REFS:
        _assert_public_reply(_reply(_DEVELOPMENT_CASES[case_ref].current_input))


def test_rc0025_step11_v1_error_names_case_without_body() -> None:
    """A stopped private run identifies its row without exposing input text."""

    async def empty_reply(**_kwargs: Any) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text="",
            meta={"public_observation_status": "rejected"},
        )

    with patch.object(
        step11_regression,
        "render_emlis_ai_reply",
        empty_reply,
    ):
        try:
            asyncio.run(
                step11_regression._v1_body(
                    _GENERIC_INDEPENDENT_EVENTS,
                    _TARGET_CASE_REF,
                )
            )
        except ValueError as exc:
            message = str(exc)
        else:
            raise AssertionError("empty_v1_reply_must_stop_step11")

    assert message == (
        "step11_v1_body_invalid:case_ref=NLS2-F03-D03"
    )
    assert _GENERIC_INDEPENDENT_EVENTS["memo"] not in message
    assert _GENERIC_INDEPENDENT_EVENTS["memo_action"] not in message
