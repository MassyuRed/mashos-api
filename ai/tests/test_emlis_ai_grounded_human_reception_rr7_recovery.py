# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR7 Move-preserving recovery and fail-closed runtime contracts."""

from dataclasses import replace
import json
from pathlib import Path

import pytest

import emlis_ai_reply_service as reply_service
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception import (
    GroundedHumanReceptionSurfaceError,
    realize_grounded_human_reception,
    reception_active_moves,
    validate_grounded_human_reception_surface,
)
from emlis_ai_grounded_observation_gate import (
    RECEPTION_GATE_REPORT_FIELDS,
    evaluate_grounded_observation_gate,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    GroundedSentenceSurfaceError,
    build_grounded_sentence_plan,
    build_reception_recovery_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_TEST_ROOT = Path(__file__).resolve().parent
_EXACT8 = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)
_LONG3 = {
    "memo": (
        "前は何も変わっていないと思った。けれど昨日より一つ進んだ。"
        "そこから、今の方向は残したいと思った。まだ結論は出ていない。"
        "次も自分で確かめたい。"
    ),
    "memo_action": "結果を表に記録して、試した順番も残した。",
    "emotions": ["自己理解"],
    "category": ["仕事"],
}


def _cases():
    return json.loads(_EXACT8.read_text(encoding="utf-8"))["cases"]


def _base(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    return plan, sentence_plan, resolver


def _eligible_stages(reception_plan):
    return tuple(
        stage
        for stage in GROUND_RECOVERY_STAGES
        if stage != "minimal_grounded"
        or (
            reception_plan.depth_policy.level == "minimal"
            and reception_plan.depth_policy.safety_mode == "standard"
            and len(reception_plan.moves) == 1
        )
    )


def _stage_artifacts(plan, base_sentence_plan, resolver, stage):
    sentence_plan = (
        base_sentence_plan
        if stage == "full"
        else build_reception_recovery_sentence_plan(
            base_sentence_plan,
            plan,
            resolver,
            recovery_stage=stage,
        )
    )
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    return sentence_plan, surface, report


def test_rr7_exact8_recovery_preserves_required_moves_depth_and_observation() -> None:
    for case in _cases():
        plan, base_sentence_plan, resolver = _base(case["exact_current_input"])
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        required_ids = {
            move.move_id for move in reception_plan.moves if move.required
        }
        base_surface = realize_grounded_sentence_plan(
            base_sentence_plan,
            plan,
            resolver,
        )
        base_observation, _base_reception, issues = split_two_stage_surface(
            base_surface.text
        )
        assert issues == ()

        for stage in _eligible_stages(reception_plan):
            _sentence_plan, surface, report = _stage_artifacts(
                plan,
                base_sentence_plan,
                resolver,
                stage,
            )
            observation, _reception, issues = split_two_stage_surface(
                surface.text
            )

            assert issues == ()
            assert observation == base_observation
            assert required_ids.issubset(
                move.move_id
                for move in reception_active_moves(reception_plan, stage)
            )
            assert report.reception_realized_move_count >= (
                reception_plan.depth_policy.min_realized_moves
            )
            assert all(
                getattr(report, field_name) == "passed"
                for field_name in RECEPTION_GATE_REPORT_FIELDS
            )
            assert report.passed is True

        if "minimal_grounded" not in _eligible_stages(reception_plan):
            with pytest.raises(
                GroundedSentenceSurfaceError,
                match="human_reception_minimal_grounded_not_allowed",
            ):
                build_reception_recovery_sentence_plan(
                    base_sentence_plan,
                    plan,
                    resolver,
                    recovery_stage="minimal_grounded",
                )


@pytest.mark.parametrize("case_id", ("D", "I6-D02"))
def test_rr7_safety_recovery_never_drops_felt_help_or_counter_move(
    case_id,
) -> None:
    case = next(item for item in _cases() if item["case_id"] == case_id)
    plan, base_sentence_plan, resolver = _base(case["exact_current_input"])
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None

    for stage in ("full", "optional_removed", "integrated", "hedged"):
        _sentence_plan, surface, report = _stage_artifacts(
            plan,
            base_sentence_plan,
            resolver,
            stage,
        )
        roles = set(report.reception_move_roles)
        acts = {move.reception_act for move in reception_active_moves(reception_plan, stage)}

        assert "bounded_counterposition" in roles
        if case_id == "D":
            assert "felt_response" in roles
            assert "stay_with_current_burden" in acts
        else:
            assert "hold_help_seeking" in acts
        _observation, reception, issues = split_two_stage_surface(surface.text)
        assert issues == ()
        assert "思えません" in reception
        assert "思いたくありません" not in reception
        assert report.reception_sentence_count == 2
        assert report.passed is True


def test_rr7_optional_removed_drops_only_a_synthetic_optional_third_move() -> None:
    plan, _sentence_plan, _resolver = _base(_LONG3)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    assert len(reception_plan.moves) == 3

    optional_third = replace(reception_plan.moves[-1], required=False)
    synthetic = replace(
        reception_plan,
        depth_policy=replace(
            reception_plan.depth_policy,
            min_realized_moves=2,
        ),
        moves=(*reception_plan.moves[:-1], optional_third),
    )

    assert len(reception_active_moves(synthetic, "full")) == 3
    assert tuple(
        move.move_id
        for move in reception_active_moves(synthetic, "optional_removed")
    ) == tuple(move.move_id for move in synthetic.moves[:2])
    assert len(reception_active_moves(synthetic, "integrated")) == 3
    assert len(reception_active_moves(synthetic, "hedged")) == 3
    with pytest.raises(
        GroundedHumanReceptionSurfaceError,
        match="human_reception_minimal_grounded_not_allowed",
    ):
        reception_active_moves(synthetic, "minimal_grounded")


def test_rr7_three_required_moves_survive_every_eligible_recovery_stage() -> None:
    plan, base_sentence_plan, resolver = _base(_LONG3)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    assert len(reception_plan.moves) == 3
    assert all(move.required for move in reception_plan.moves)

    for stage in ("full", "optional_removed", "integrated", "hedged"):
        _sentence_plan, _surface, report = _stage_artifacts(
            plan,
            base_sentence_plan,
            resolver,
            stage,
        )
        assert report.reception_realized_move_count == 3
        assert 2 <= report.reception_sentence_count <= 3
        assert report.reception_sentence_count == (
            2 if stage == "integrated" else 3
        )
        assert report.reception_depth_proportionality_gate == "passed"
        assert report.passed is True


def test_rr7_required_move_grounding_diagnostics_cannot_be_partially_removed() -> None:
    plan, base_sentence_plan, resolver = _base(_LONG3)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    human_line = next(
        line
        for line in base_sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    direct = realize_grounded_human_reception(
        reception_plan,
        {nucleus.nucleus_id: nucleus for nucleus in plan.nuclei},
        resolver,
        clause_plans=human_line.reception_clause_plans,
    )
    first_move = reception_active_moves(reception_plan, "full")[0]
    partial = replace(
        direct,
        grounded_nucleus_ids=first_move.target_nucleus_ids,
        grounded_evidence_span_ids=first_move.source_evidence_span_ids,
    )
    issues = validate_grounded_human_reception_surface(
        partial,
        reception_plan,
        resolver,
    )

    assert "human_reception_surface_grounding_mismatch" in issues
    assert "human_reception_surface_evidence_mismatch" in issues


@pytest.mark.asyncio
async def test_rr7_all_gate_failures_return_no_generic_or_observation_only_body(
    monkeypatch,
) -> None:
    case = next(item for item in _cases() if item["case_id"] == "B")
    original_gate = reply_service.evaluate_grounded_observation_gate

    def forced_failure(**kwargs):
        report = original_gate(**kwargs)
        return replace(
            report,
            semantic_quality_gate="failed",
            public_observation_status="rejected",
            public_comment_present=False,
            rejection_reasons=("rr7_forced_gate_failure",),
        )

    monkeypatch.setattr(
        reply_service,
        "evaluate_grounded_observation_gate",
        forced_failure,
    )
    reply = await reply_service.render_emlis_ai_reply(
        user_id="rr7-fail-closed",
        subscription_tier="free",
        current_input=case["exact_current_input"],
    )

    assert reply.comment_text == ""
    assert reply.meta["public_observation_status"] == "rejected"
    assert reply.meta["fallback_used"] is False
    gate = reply.meta["grounded_observation"]
    assert gate["recovery_steps"] == [
        "full",
        "optional_removed",
        "integrated",
        "hedged",
    ]
    assert gate["recovery_skipped_stages"] == ["minimal_grounded"]
    assert gate["recovery_failure_codes"] == []


@pytest.mark.asyncio
async def test_rr7_surface_failure_reason_is_body_free_and_next_stage_can_pass(
    monkeypatch,
) -> None:
    case = next(item for item in _cases() if item["case_id"] == "B")
    original_gate = reply_service.evaluate_grounded_observation_gate
    original_builder = reply_service.build_reception_recovery_sentence_plan

    def fail_full_gate_only(**kwargs):
        report = original_gate(**kwargs)
        if kwargs["sentence_plan"].recovery_stage != "full":
            return report
        return replace(
            report,
            semantic_quality_gate="failed",
            public_observation_status="rejected",
            public_comment_present=False,
            rejection_reasons=("rr7_forced_full_failure",),
        )

    def fail_optional(*args, recovery_stage, **kwargs):
        if recovery_stage == "optional_removed":
            raise GroundedSentenceSurfaceError("synthetic_surface_failure")
        return original_builder(
            *args,
            recovery_stage=recovery_stage,
            **kwargs,
        )

    monkeypatch.setattr(
        reply_service,
        "evaluate_grounded_observation_gate",
        fail_full_gate_only,
    )
    monkeypatch.setattr(
        reply_service,
        "build_reception_recovery_sentence_plan",
        fail_optional,
    )
    reply = await reply_service.render_emlis_ai_reply(
        user_id="rr7-recovery-reason",
        subscription_tier="free",
        current_input=case["exact_current_input"],
    )

    assert reply.comment_text
    assert reply.meta["public_observation_status"] == "passed"
    gate = reply.meta["grounded_observation"]
    assert gate["recovery_steps"] == [
        "full",
        "optional_removed",
        "integrated",
    ]
    assert gate["recovery_failure_codes"] == [
        "recovery_stage_surface_failed:optional_removed"
    ]
    assert case["exact_current_input"]["memo"] not in json.dumps(
        gate,
        ensure_ascii=False,
        sort_keys=True,
    )


@pytest.mark.asyncio
async def test_rr7_all_surface_failures_return_body_free_rejected_envelope(
    monkeypatch,
) -> None:
    case = next(item for item in _cases() if item["case_id"] == "B")

    def fail_every_surface(*_args, **_kwargs):
        raise GroundedSentenceSurfaceError("synthetic_all_surface_failure")

    monkeypatch.setattr(
        reply_service,
        "realize_grounded_sentence_plan",
        fail_every_surface,
    )
    reply = await reply_service.render_emlis_ai_reply(
        user_id="rr7-all-surface-fail",
        subscription_tier="free",
        current_input=case["exact_current_input"],
    )

    assert reply.comment_text == ""
    assert reply.meta["public_observation_status"] == "rejected"
    assert reply.meta["fallback_used"] is False
    gate = reply.meta["grounded_observation"]
    assert gate["recovery_steps"] == [
        "full",
        "optional_removed",
        "integrated",
        "hedged",
    ]
    assert gate["recovery_skipped_stages"] == ["minimal_grounded"]
    assert gate["recovery_failure_codes"] == [
        "recovery_stage_surface_failed:full",
        "recovery_stage_surface_failed:optional_removed",
        "recovery_stage_surface_failed:integrated",
        "recovery_stage_surface_failed:hedged",
    ]
    assert gate["runtime_final_contract_guard"] == "failed"
    assert case["exact_current_input"]["memo"] not in json.dumps(
        gate,
        ensure_ascii=False,
        sort_keys=True,
    )
