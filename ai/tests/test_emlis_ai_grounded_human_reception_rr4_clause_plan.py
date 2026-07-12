# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR4 contracts for Move-bound SentencePlan / Reception ClausePlan."""

from dataclasses import asdict, replace
import json
from pathlib import Path

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception import (
    reception_active_moves,
    reception_move_predicate_family,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
    build_grounded_sentence_plan,
    validate_grounded_sentence_plan,
)


_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)
_EXPECTED_CLAUSE_COUNT = {
    "A": 1,
    "B": 2,
    "C": 2,
    "D": 2,
    "I6-S03": 1,
    "I6-L03": 2,
    "I6-C01": 2,
    "I6-D02": 2,
}
_CLAUSE_FIELDS = {
    "sentence_slot",
    "move_ids",
    "opening_strategy",
    "connector_policy",
    "terminal_predicate_family",
    "quote_budget",
    "speaker_presence",
}


def _load_cases():
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))["cases"]


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    reception_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    assert len(reception_lines) == 1
    return plan, reception_plan, sentence_plan, reception_lines[0], resolver


def _case(case_id):
    row = next(row for row in _load_cases() if row["case_id"] == case_id)
    return _artifacts(row["exact_current_input"])


def _replace_human_line(sentence_plan, replacement):
    return replace(
        sentence_plan,
        lines=tuple(
            replacement
            if line.binding.line_role == "human_follow"
            else line
            for line in sentence_plan.lines
        ),
    )


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_CLAUSE_COUNT))
def test_rr4_exact8_binds_depth_moves_to_one_final_reception_line(
    case_id,
) -> None:
    plan, reception, sentence_plan, line, resolver = _case(case_id)
    moves = reception_active_moves(reception, "full")
    move_index = {move.move_id: move for move in moves}
    clauses = line.reception_clause_plans
    flattened = tuple(
        move_id for clause in clauses for move_id in clause.move_ids
    )

    assert sentence_plan.schema_version == GROUND_SENTENCE_PLAN_SCHEMA_VERSION
    assert sentence_plan.lines[-1] is line
    assert line.surface_function == "render_human_follow"
    assert line.binding.relation_ids == ()
    assert len(clauses) == _EXPECTED_CLAUSE_COUNT[case_id]
    assert (
        reception.depth_policy.min_sentences
        <= len(clauses)
        <= reception.depth_policy.max_sentences
    )
    assert tuple(clause.sentence_slot for clause in clauses) == tuple(
        range(1, len(clauses) + 1)
    )
    assert flattened == tuple(move.move_id for move in moves)
    assert {
        move.move_id for move in reception.moves if move.required
    } <= set(flattened)

    quote_budget = 0
    for clause in clauses:
        assert set(asdict(clause)) == _CLAUSE_FIELDS
        assert 1 <= len(clause.move_ids) <= min(
            2,
            reception.depth_policy.max_moves_per_sentence,
        )
        move = move_index[clause.move_ids[0]]
        assert clause.opening_strategy == move.surface_strategy
        assert clause.terminal_predicate_family == (
            reception_move_predicate_family(move)
        )
        assert clause.speaker_presence == move.speaker_presence
        assert clause.connector_policy == (
            "contrast_safe"
            if move.move_role == "bounded_counterposition"
            else "none"
        )
        assert clause.quote_budget in {0, 1}
        quote_budget += clause.quote_budget
    assert quote_budget <= reception.quote_policy.max_anchor_count

    atoms = set(line.binding.functional_atom_ids)
    assert {
        f"reception_depth:{reception.depth_policy.level}",
        f"reception_safety_mode:{reception.depth_policy.safety_mode}",
        f"reception_move_count:{len(moves)}",
        f"reception_clause_count:{len(clauses)}",
        "reception_raw_character_count_used:false",
        "reception_distinctness:required",
        "reception_non_enumeration:required",
        "human_follow_delivery:separate",
    } <= atoms
    for move in moves:
        slot = next(
            clause.sentence_slot
            for clause in clauses
            if move.move_id in clause.move_ids
        )
        assert {
            f"reception_move:{move.move_id}",
            f"reception_move_role:{move.move_id}:{move.move_role}",
            f"reception_move_act:{move.move_id}:{move.reception_act}",
            (
                "reception_surface_strategy:"
                f"{move.move_id}:{move.surface_strategy}"
            ),
            f"reception_sentence_slot:{move.move_id}:{slot}",
            (
                "reception_move_required:"
                f"{move.move_id}:{str(move.required).lower()}"
            ),
            (
                "reception_move_predicate:"
                f"{move.move_id}:{reception_move_predicate_family(move)}"
            ),
        } <= atoms

    for observation_line in sentence_plan.lines[:-1]:
        assert observation_line.reception_clause_plans == ()
        assert not any(
            atom.startswith("reception_")
            for atom in observation_line.binding.functional_atom_ids
        )
    assert validate_grounded_sentence_plan(
        sentence_plan,
        plan,
        resolver,
    ) == ()


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_CLAUSE_COUNT))
def test_rr4_human_line_grounding_covers_selected_move_union(
    case_id,
) -> None:
    _plan, reception, _sentence_plan, line, resolver = _case(case_id)
    moves = reception_active_moves(reception, "full")
    expected_nuclei = {
        nucleus_id
        for move in moves
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
    }
    expected_evidence = {
        span_id
        for move in moves
        for span_id in move.source_evidence_span_ids
    }
    # The outer binding remains the evidence-complete legacy Gate envelope;
    # ClausePlan is the exact Move owner during the RR3-RR6 compatibility
    # window.  Every selected Move must still be contained in that envelope.
    assert expected_nuclei <= set(line.binding.nucleus_ids)
    assert expected_evidence <= set(line.binding.evidence_span_ids)
    assert line.binding.nucleus_ids == tuple(
        dict.fromkeys(
            (
                *reception.target_nucleus_ids,
                *reception.support_nucleus_ids,
            )
        )
    )
    assert line.binding.evidence_span_ids == reception.source_evidence_span_ids
    assert resolver.unresolved_ids(line.binding.evidence_span_ids) == ()


def test_rr4_clause_plan_meta_is_body_free() -> None:
    for case_id in _EXPECTED_CLAUSE_COUNT:
        _plan, _reception, _sentence_plan, line, _resolver = _case(case_id)
        payload = json.dumps(
            [asdict(clause) for clause in line.reception_clause_plans],
            ensure_ascii=False,
        )
        assert all(ord(character) < 128 for character in payload)


@pytest.mark.parametrize("case_id", ("D", "I6-D02"))
def test_rr4_bounded_counterposition_is_independent_final_clause(
    case_id,
) -> None:
    _plan, reception, _sentence_plan, line, _resolver = _case(case_id)
    move_index = {move.move_id: move for move in reception.moves}
    bounded = tuple(
        clause
        for clause in line.reception_clause_plans
        if move_index[clause.move_ids[0]].move_role
        == "bounded_counterposition"
    )
    assert len(bounded) == 1
    assert bounded[0] is line.reception_clause_plans[-1]
    assert len(bounded[0].move_ids) == 1
    assert bounded[0].connector_policy == "contrast_safe"
    assert bounded[0].speaker_presence == "explicit_emlis"


def test_rr4_validator_rejects_clause_and_observation_mutations() -> None:
    plan, _reception, sentence_plan, line, resolver = _case("B")
    clauses = line.reception_clause_plans

    dropped = _replace_human_line(
        sentence_plan,
        replace(line, reception_clause_plans=clauses[:-1]),
    )
    assert "human_reception_clause_plan_mismatch" in (
        validate_grounded_sentence_plan(dropped, plan, resolver)
    )

    duplicate = (
        clauses[0],
        replace(clauses[1], move_ids=clauses[0].move_ids),
    )
    duplicated = _replace_human_line(
        sentence_plan,
        replace(line, reception_clause_plans=duplicate),
    )
    duplicate_issues = validate_grounded_sentence_plan(
        duplicated,
        plan,
        resolver,
    )
    assert "human_reception_clause_plan_mismatch" in duplicate_issues
    assert "human_reception_clause_move_duplicate" in duplicate_issues

    wrong_slot = _replace_human_line(
        sentence_plan,
        replace(
            line,
            reception_clause_plans=(
                replace(clauses[0], sentence_slot=2),
                clauses[1],
            ),
        ),
    )
    assert "human_reception_clause_plan_mismatch" in (
        validate_grounded_sentence_plan(wrong_slot, plan, resolver)
    )

    first_observation = sentence_plan.lines[0]
    leaked = replace(
        sentence_plan,
        lines=(
            replace(first_observation, reception_clause_plans=clauses),
            *sentence_plan.lines[1:],
        ),
    )
    assert (
        f"reception_clause_plan_leaked:{first_observation.binding.sentence_id}"
        in validate_grounded_sentence_plan(leaked, plan, resolver)
    )


def test_rr4_long_arc_three_moves_receive_three_internal_slots() -> None:
    plan, reception, sentence_plan, line, resolver = _artifacts(
        {
            "memo": (
                "前は何も変わっていないと思った。けれど昨日より一つ進んだ。"
                "そこから、今の方向は残したいと思った。まだ結論は出ていない。"
                "次も自分で確かめたい。"
            ),
            "memo_action": "結果を表に記録して、試した順番も残した。",
            "emotions": ["自己理解"],
            "category": ["仕事"],
        }
    )
    assert reception.depth_policy.level == "layered"
    assert len(reception.moves) == 3
    assert len(line.reception_clause_plans) == 3
    assert tuple(
        clause.sentence_slot for clause in line.reception_clause_plans
    ) == (1, 2, 3)
    assert validate_grounded_sentence_plan(
        sentence_plan,
        plan,
        resolver,
    ) == ()
