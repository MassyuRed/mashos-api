# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR6 Runtime Gate/final-guard contracts for Depth and Move ownership."""

from dataclasses import replace
import json
from pathlib import Path
import re

import pytest

import emlis_ai_reply_service as reply_service
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import (
    RECEPTION_GATE_REPORT_FIELDS,
    evaluate_grounded_observation_gate,
    grounded_gate_meta_is_body_free,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    OBSERVATION_SECTION_LABEL,
    RECEPTION_SECTION_LABEL,
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_TEST_ROOT = Path(__file__).resolve().parent
_EXACT8 = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)
_UNSEEN8 = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_r6_unseen8_20260712.json"
)
_SENTENCE_END_RE = re.compile(r"[。！？!?]+")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    return plan, sentence_plan, surface, report, resolver


def _replace_reception(surface, text: str):
    observation, _reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    return replace(
        surface,
        text=(
            f"{OBSERVATION_SECTION_LABEL}\n{observation}\n\n"
            f"{RECEPTION_SECTION_LABEL}\n{text}"
        ),
        lines=tuple(
            replace(line, text=text)
            if line.binding.line_role == "human_follow"
            else line
            for line in surface.lines
        ),
    )


def _replace_plan_reception(plan, reception_plan):
    return replace(
        plan,
        response_plan=replace(
            plan.response_plan,
            human_reception_plan=reception_plan,
        ),
    )


def test_rr6_exact8_passes_all_twelve_gates_with_body_free_diagnostics() -> None:
    for case in _load(_EXACT8)["cases"]:
        plan, _sentence_plan, surface, report, _resolver = _artifacts(
            case["exact_current_input"]
        )
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        meta = report.as_body_free_meta()

        assert len(RECEPTION_GATE_REPORT_FIELDS) == 12
        assert report.passed is True
        assert report.all_reception_gates_passed is True
        assert all(
            getattr(report, field_name) == "passed"
            for field_name in RECEPTION_GATE_REPORT_FIELDS
        )
        assert report.reception_depth_level == reception_plan.depth_policy.level
        assert report.reception_safety_mode == (
            reception_plan.depth_policy.safety_mode
        )
        assert report.reception_opportunity_count == len(
            reception_plan.opportunities
        )
        assert report.reception_planned_move_count == len(reception_plan.moves)
        assert report.reception_realized_move_count == len(
            report.reception_move_roles
        )
        assert report.reception_realized_move_count == len(
            report.reception_surface_strategies
        )
        assert report.reception_realized_move_count == len(
            report.reception_terminal_predicate_families
        )
        assert report.raw_character_count_used is False
        assert grounded_gate_meta_is_body_free(meta) is True
        serialized = json.dumps(meta, ensure_ascii=False, sort_keys=True)
        assert surface.text not in serialized
        assert case["exact_current_input"].get("memo", "") not in serialized


def test_rr6_layered_three_move_surface_passes_three_sentence_gate() -> None:
    current_input = {
        "memo": (
            "前は何も変わっていないと思った。けれど昨日より一つ進んだ。"
            "そこから、今の方向は残したいと思った。まだ結論は出ていない。"
            "次も自分で確かめたい。"
        ),
        "memo_action": "結果を表に記録して、試した順番も残した。",
        "emotions": ["自己理解"],
        "category": ["仕事"],
    }
    plan, _sentence_plan, _surface, report, _resolver = _artifacts(
        current_input
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None

    assert reception_plan.depth_policy.level == "layered"
    assert report.reception_realized_move_count == 3
    assert report.reception_sentence_count == 3
    assert report.reception_depth_plan_gate == "passed"
    assert report.reception_depth_proportionality_gate == "passed"
    assert report.passed is True


def test_rr6_predicate_family_can_pass_without_legacy_owner_lexeme() -> None:
    case = next(
        item for item in _load(_UNSEEN8)["cases"] if item["case_id"] == "R6-U03"
    )
    _plan, _sentence_plan, surface, report, _resolver = _artifacts(
        case["current_input"]
    )
    _observation, reception, issues = split_two_stage_surface(surface.text)

    assert issues == ()
    assert "受け止め" not in reception
    assert report.reception_human_voice_gate == "passed"
    assert report.reception_move_realization_gate == "passed"
    assert report.passed is True


def test_rr6_depth_move_distinctness_and_enumeration_mutations_fail_named_gates() -> None:
    case = next(item for item in _load(_EXACT8)["cases"] if item["case_id"] == "B")
    plan, sentence_plan, surface, _report, resolver = _artifacts(
        case["exact_current_input"]
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None

    raw_count_plan = _replace_plan_reception(
        plan,
        replace(
            reception_plan,
            depth_policy=replace(
                reception_plan.depth_policy,
                raw_character_count_used=True,
            ),
        ),
    )
    raw_count_report = evaluate_grounded_observation_gate(
        plan=raw_count_plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert raw_count_report.reception_depth_plan_gate == "failed"
    assert "reception_raw_character_count_used" in (
        raw_count_report.rejection_reasons
    )

    human_line = next(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    missing_move_atom = f"reception_move:{reception_plan.moves[-1].move_id}"
    mutated_binding = replace(
        human_line.binding,
        functional_atom_ids=tuple(
            atom
            for atom in human_line.binding.functional_atom_ids
            if atom != missing_move_atom
        ),
    )
    missing_sentence_plan = replace(
        sentence_plan,
        lines=tuple(
            replace(line, binding=mutated_binding)
            if line.binding.line_role == "human_follow"
            else line
            for line in sentence_plan.lines
        ),
    )
    missing_surface = replace(
        surface,
        lines=tuple(
            replace(line, binding=mutated_binding)
            if line.binding.line_role == "human_follow"
            else line
            for line in surface.lines
        ),
    )
    missing_report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=missing_sentence_plan,
        surface_result=missing_surface,
        resolver=resolver,
    )
    assert missing_report.reception_move_realization_gate == "failed"
    assert "reception_move_contract_atom_missing" in (
        missing_report.rejection_reasons
    )

    duplicate_move = replace(
        reception_plan.moves[-1],
        move_role=reception_plan.moves[0].move_role,
        reception_act=reception_plan.moves[0].reception_act,
        target_nucleus_ids=reception_plan.moves[0].target_nucleus_ids,
        support_nucleus_ids=reception_plan.moves[0].support_nucleus_ids,
        surface_strategy=reception_plan.moves[0].surface_strategy,
    )
    duplicate_plan = _replace_plan_reception(
        plan,
        replace(
            reception_plan,
            moves=(*reception_plan.moves[:-1], duplicate_move),
        ),
    )
    duplicate_report = evaluate_grounded_observation_gate(
        plan=duplicate_plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert duplicate_report.reception_move_distinctness_gate == "failed"
    assert "reception_duplicate_move_contribution" in (
        duplicate_report.rejection_reasons
    )

    enumerating_plan = _replace_plan_reception(
        plan,
        replace(
            reception_plan,
            distinctness_policy=replace(
                reception_plan.distinctness_policy,
                all_input_enumeration_allowed=True,
            ),
        ),
    )
    enumerating_report = evaluate_grounded_observation_gate(
        plan=enumerating_plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert enumerating_report.reception_non_enumeration_gate == "failed"


def test_rr6_missing_depth_invalid_role_and_depth_relabel_fail_without_crash() -> None:
    case = next(item for item in _load(_EXACT8)["cases"] if item["case_id"] == "B")
    plan, sentence_plan, surface, _report, resolver = _artifacts(
        case["exact_current_input"]
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None

    missing_depth = _replace_plan_reception(
        plan,
        replace(reception_plan, depth_policy=None),
    )
    missing_depth_report = evaluate_grounded_observation_gate(
        plan=missing_depth,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert missing_depth_report.reception_depth_plan_gate == "failed"
    assert "reception_depth_plan_missing" in (
        missing_depth_report.rejection_reasons
    )

    invalid_role = _replace_plan_reception(
        plan,
        replace(
            reception_plan,
            moves=(
                replace(reception_plan.moves[0], move_role="invalid_role"),
                *reception_plan.moves[1:],
            ),
        ),
    )
    invalid_role_report = evaluate_grounded_observation_gate(
        plan=invalid_role,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert invalid_role_report.reception_move_realization_gate == "failed"
    assert invalid_role_report.passed is False

    invalid_role_act = _replace_plan_reception(
        plan,
        replace(
            reception_plan,
            moves=(
                replace(
                    reception_plan.moves[0],
                    move_role="bounded_counterposition",
                    reception_act="stay_with_current_burden",
                ),
                *reception_plan.moves[1:],
            ),
        ),
    )
    invalid_role_act_report = evaluate_grounded_observation_gate(
        plan=invalid_role_act,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert invalid_role_act_report.reception_move_realization_gate == "failed"
    assert invalid_role_act_report.passed is False

    relabeled_depth = replace(
        reception_plan.depth_policy,
        level="focused",
        selection_reason_codes=tuple(
            "depth:focused" if code == "depth:layered" else code
            for code in reception_plan.depth_policy.selection_reason_codes
        ),
    )
    relabeled = _replace_plan_reception(
        plan,
        replace(reception_plan, depth_policy=relabeled_depth),
    )
    relabeled_report = evaluate_grounded_observation_gate(
        plan=relabeled,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    assert relabeled_report.reception_depth_plan_gate == "failed"
    assert "reception_canonical_depth_classification_mismatch" in (
        relabeled_report.rejection_reasons
    )


def test_rr6_focused_sentence_budget_cannot_be_widened_to_three() -> None:
    case = next(
        item for item in _load(_UNSEEN8)["cases"] if item["case_id"] == "R6-U03"
    )
    plan, sentence_plan, surface, _report, resolver = _artifacts(
        case["current_input"]
    )
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    assert reception_plan.depth_policy.level == "focused"
    widened = _replace_plan_reception(
        plan,
        replace(
            reception_plan,
            depth_policy=replace(
                reception_plan.depth_policy,
                max_sentences=3,
            ),
        ),
    )
    report = evaluate_grounded_observation_gate(
        plan=widened,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )

    assert report.reception_depth_plan_gate == "failed"
    assert "reception_focused_depth_contract_invalid" in (
        report.rejection_reasons
    )


def test_rr6_layered_one_line_and_field_enumeration_fail_closed() -> None:
    case = next(item for item in _load(_EXACT8)["cases"] if item["case_id"] == "B")
    plan, sentence_plan, surface, _report, resolver = _artifacts(
        case["exact_current_input"]
    )
    _observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    first_sentence = next(
        part.strip()
        for part in _SENTENCE_END_RE.split(reception)
        if part.strip()
    ) + "。"
    one_line = _replace_reception(surface, first_sentence)
    one_line_report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=one_line,
        resolver=resolver,
    )

    assert one_line_report.reception_move_realization_gate == "failed"
    assert one_line_report.reception_depth_proportionality_gate == "failed"
    assert one_line_report.passed is False

    enumerated = _replace_reception(
        surface,
        "memo、memo_action、emotion、categoryを順番に整理しました。",
    )
    enumerated_report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=enumerated,
        resolver=resolver,
    )
    assert enumerated_report.reception_non_enumeration_gate == "failed"
    assert "reception_input_field_enumeration_visible" in (
        enumerated_report.rejection_reasons
    )


@pytest.mark.asyncio
async def test_rr6_final_guard_requires_each_new_gate(monkeypatch) -> None:
    case = next(item for item in _load(_EXACT8)["cases"] if item["case_id"] == "A")
    _plan, _sentence_plan, _surface, report, _resolver = _artifacts(
        case["exact_current_input"]
    )
    spoofed = replace(report, reception_move_realization_gate="failed")

    monkeypatch.setattr(
        reply_service,
        "evaluate_grounded_observation_gate",
        lambda **_kwargs: spoofed,
    )
    reply = await reply_service.render_emlis_ai_reply(
        user_id="rr6-final-guard",
        subscription_tier="free",
        current_input=case["exact_current_input"],
    )

    assert reply.comment_text == ""
    assert reply.meta["public_observation_status"] == "rejected"
    gate = reply.meta["grounded_observation"]
    assert gate["runtime_reception_contract_guard"] == "failed"
    assert gate["runtime_final_contract_guard"] == "failed"
    assert "runtime_reception_contract_guard_failed" in (
        reply.meta["rejection_reasons"]
    )


@pytest.mark.parametrize(
    ("semantic_status", "public_status"),
    (("failed", "passed"), ("passed", "rejected")),
)
@pytest.mark.asyncio
async def test_rr6_final_guard_normalizes_inconsistent_gate_status(
    monkeypatch,
    semantic_status,
    public_status,
) -> None:
    case = next(item for item in _load(_EXACT8)["cases"] if item["case_id"] == "B")
    original_gate = reply_service.evaluate_grounded_observation_gate

    def inconsistent_gate(**kwargs):
        report = original_gate(**kwargs)
        return replace(
            report,
            semantic_quality_gate=semantic_status,
            public_observation_status=public_status,
            public_comment_present=public_status == "passed",
        )

    monkeypatch.setattr(
        reply_service,
        "evaluate_grounded_observation_gate",
        inconsistent_gate,
    )
    reply = await reply_service.render_emlis_ai_reply(
        user_id="rr6-inconsistent-status",
        subscription_tier="free",
        current_input=case["exact_current_input"],
    )

    assert reply.comment_text == ""
    assert reply.meta["public_observation_status"] == "rejected"
    assert "runtime_gate_public_status_inconsistent" in (
        reply.meta["rejection_reasons"]
    )
    assert reply.meta["grounded_observation"][
        "runtime_final_contract_guard"
    ] == "failed"
