# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR5 contracts for the deterministic Multi-Move Reception realizer."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_human_reception import (
    GroundedHumanReceptionSurfaceError,
    realize_grounded_human_reception,
    reception_active_moves,
    reception_move_predicate_family,
    validate_grounded_human_reception_surface,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
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
_FREEZE = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_rr0_r8_freeze_20260712.json"
)
_EXPECTED_SENTENCE_COUNT = {
    "A": 1,
    "B": 2,
    "C": 2,
    "D": 2,
    "I6-S03": 1,
    "I6-L03": 2,
    "I6-C01": 2,
    "I6-D02": 2,
}
_SENTENCE_END_RE = re.compile(r"[。！？!?]+")
_QUOTE_RE = re.compile(r"「([^」]*)」")
_POLICY_RE = re.compile(
    r"(?:理由|原因).{0,20}(?:決めつけ|断定)|"
    r"入力から言える範囲|診断はしません|ここでは事実として扱いません|"
    r"原因は分かりません"
)
_ADVICE_RE = re.compile(
    r"(?:してください|しましょう|してみて|すべき|した方がいい|"
    r"相談して|連絡して|受診して)"
)
_UNSUPPORTED_RE = re.compile(
    r"(?:必ず|絶対に|確実に|成功|解決|安全です|危険度|診断|"
    r"あなたは(?:強い|優しい|立派|素晴らしい))"
)
_FAMILY_MARKER = {
    "human_response_attention_stood_out": re.compile(r"印象に残|見過ご"),
    "human_response_attention_not_overlooked": re.compile(r"印象に残|見過ご"),
    "human_response_significance_not_minimized": re.compile(r"軽く扱"),
    "human_response_significance_effort_made_concrete": re.compile(
        r"軽いこと|大切"
    ),
    "human_response_significance_intention_preserved": re.compile(
        r"消さず|残しておきたい"
    ),
    "human_response_significance_change_confirmed": re.compile(
        r"変化|扱いたく"
    ),
    "human_response_significance_help_preserved": re.compile(
        r"一歩|残しておきたい"
    ),
    "human_response_significance_words_placed": re.compile(r"言葉|軽く扱"),
    "human_response_quiet_presence": re.compile(r"軽く扱|小さくせず"),
    "human_response_felt_respect_for_effort": re.compile(r"手間.*大切"),
    "human_response_felt_gentle_respect": re.compile(r"そっと.*大切"),
    "human_response_recognize_change": re.compile(
        r"(?:うれし|変化|軽く扱|軽いこと|見過ご)"
    ),
    "human_response_hold_help_seeking": re.compile(
        r"(?:助け|踏みとどまり).*(?:見過ご|大切)"
    ),
    "human_response_bounded_counterposition": re.compile(
        r"Emlis.*自身.*思えません"
    ),
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    result = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    observation, reception, issues = split_two_stage_surface(result.text)
    assert issues == ()
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    human_line = next(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    direct = realize_grounded_human_reception(
        reception_plan,
        {nucleus.nucleus_id: nucleus for nucleus in plan.nuclei},
        resolver,
        clause_plans=human_line.reception_clause_plans,
    )
    return (
        plan,
        reception_plan,
        sentence_plan,
        human_line,
        result,
        direct,
        observation,
        reception,
        resolver,
    )


def _case(case_id):
    row = next(
        row
        for row in _load(_EXACT8)["cases"]
        if row["case_id"] == case_id
    )
    return _artifacts(row["exact_current_input"])


def _sentences(text):
    return tuple(
        part.strip()
        for part in _SENTENCE_END_RE.split(text)
        if part.strip()
    )


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_SENTENCE_COUNT))
def test_rr5_exact8_realizes_every_planned_move_without_observation_regression(
    case_id,
) -> None:
    (
        _plan,
        reception_plan,
        _sentence_plan,
        human_line,
        _result,
        direct,
        observation,
        reception,
        resolver,
    ) = _case(case_id)
    active_moves = reception_active_moves(reception_plan, "full")
    clause_move_ids = tuple(
        move_id
        for clause in human_line.reception_clause_plans
        for move_id in clause.move_ids
    )
    expected_move_ids = tuple(move.move_id for move in active_moves)
    expected_roles = tuple(move.move_role for move in active_moves)
    expected_families = tuple(
        reception_move_predicate_family(move) for move in active_moves
    )
    expected_nucleus_ids = {
        nucleus_id
        for move in active_moves
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
    }
    expected_evidence_span_ids = {
        span_id
        for move in active_moves
        for span_id in move.source_evidence_span_ids
    }
    frozen = next(
        row
        for row in _load(_FREEZE)["cases"]
        if row["case_id"] == case_id
    )

    assert reception == direct.text
    assert direct == realize_grounded_human_reception(
        reception_plan,
        {
            nucleus.nucleus_id: nucleus
            for nucleus in _plan.nuclei
        },
        resolver,
        clause_plans=human_line.reception_clause_plans,
    )
    assert hashlib.sha256(observation.encode("utf-8")).hexdigest() == (
        frozen["current_observation_section_sha256"]
    )
    assert direct.sentence_count == _EXPECTED_SENTENCE_COUNT[case_id]
    assert direct.sentence_count == len(human_line.reception_clause_plans)
    assert clause_move_ids == expected_move_ids == direct.realized_move_ids
    assert direct.realized_move_roles == expected_roles
    assert direct.move_predicate_families == expected_families
    assert direct.realized_clause_move_ids == tuple(
        clause.move_ids for clause in human_line.reception_clause_plans
    )
    assert {
        move.move_id for move in reception_plan.moves if move.required
    } <= set(direct.realized_move_ids)
    assert set(direct.grounded_nucleus_ids) == expected_nucleus_ids
    assert set(direct.grounded_evidence_span_ids) == (
        expected_evidence_span_ids
    )
    assert (
        reception_plan.depth_policy.min_sentences
        <= direct.sentence_count
        <= reception_plan.depth_policy.max_sentences
    )
    assert resolver.unresolved_ids(direct.grounded_evidence_span_ids) == ()
    assert validate_grounded_human_reception_surface(
        direct,
        reception_plan,
        resolver,
    ) == ()


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_SENTENCE_COUNT))
def test_rr5_move_families_have_distinct_visible_responsibilities(
    case_id,
) -> None:
    (
        _plan,
        _reception_plan,
        _sentence_plan,
        _human_line,
        _result,
        direct,
        _observation,
        _reception,
        _resolver,
    ) = _case(case_id)
    sentences = _sentences(direct.text)

    assert len(sentences) == len(direct.move_predicate_families)
    for sentence, family in zip(sentences, direct.move_predicate_families):
        assert family in _FAMILY_MARKER
        assert _FAMILY_MARKER[family].search(sentence)
    if len(direct.move_predicate_families) > 1:
        assert len(set(direct.move_predicate_families)) == len(
            direct.move_predicate_families
        )
        assert len(set(sentences)) == len(sentences)


def test_rr5_exact8_keeps_quote_policy_and_visible_safety_boundaries() -> None:
    for case_id in _EXPECTED_SENTENCE_COUNT:
        (
            _plan,
            reception_plan,
            _sentence_plan,
            _human_line,
            _result,
            direct,
            _observation,
            _reception,
            _resolver,
        ) = _case(case_id)
        quotes = tuple(_QUOTE_RE.findall(direct.text))
        assert len(quotes) <= reception_plan.quote_policy.max_anchor_count
        assert all(
            len(quote) <= reception_plan.quote_policy.max_anchor_visible_chars
            for quote in quotes
        )
        assert _POLICY_RE.search(direct.text) is None
        assert _ADVICE_RE.search(direct.text) is None
        assert _UNSUPPORTED_RE.search(direct.text) is None
        assert "?" not in direct.text and "？" not in direct.text


@pytest.mark.parametrize("case_id", ("D", "I6-D02"))
def test_rr5_bounded_counterposition_is_last_grounded_move(
    case_id,
) -> None:
    (
        _plan,
        reception_plan,
        _sentence_plan,
        _human_line,
        _result,
        direct,
        _observation,
        _reception,
        _resolver,
    ) = _case(case_id)
    move_by_id = {move.move_id: move for move in reception_plan.moves}
    final_move_ids = direct.realized_clause_move_ids[-1]

    assert len(final_move_ids) == 1
    assert move_by_id[final_move_ids[0]].move_role == (
        "bounded_counterposition"
    )
    assert "否定せず" in direct.text
    assert "Emlis" in _sentences(direct.text)[-1]
    assert re.search(r"その言葉だけで.*自身.*思えません", direct.text)


def test_rr5_long_arc_realizes_three_required_moves_in_three_sentences() -> None:
    artifacts = _artifacts(
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
    reception_plan = artifacts[1]
    direct = artifacts[5]

    assert reception_plan.depth_policy.level == "layered"
    assert len(reception_plan.moves) == 3
    assert all(move.required for move in reception_plan.moves)
    assert direct.sentence_count == 3
    assert len(direct.realized_move_ids) == 3
    assert len(set(direct.move_predicate_families)) == 3
    assert direct.source_anchor_count <= 1


def test_rr5_standard_help_can_layer_without_explicit_safety_counter() -> None:
    artifacts = _artifacts(
        {
            "memo": "今日は二つのことを進めた。",
            "memo_action": "相談の予約を取った。必要な資料も送った。",
            "emotions": ["安堵"],
            "category": ["生活"],
        }
    )
    reception_plan = artifacts[1]
    direct = artifacts[5]

    assert reception_plan.depth_policy.safety_mode == "standard"
    assert reception_plan.depth_policy.level == "layered"
    assert len(direct.realized_move_ids) == direct.sentence_count == 2
    assert "hold_help_seeking" in direct.realized_reception_acts
    assert len(set(direct.realized_reception_acts)) == 2
    assert "Emlis" not in direct.text


def test_rr5_depth_uses_opportunities_instead_of_raw_length() -> None:
    long_repeated_burden = {
        "memo": (
            "今日はずっと重い。何をしても重く感じる。朝から重く、昼にも重く、"
            "今も同じ重さが続いている。何度言い直しても、ただしんどくて重い。"
        ),
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["生活"],
    }
    short_help = {
        "memo": "自分には価値がない。それでも相談先は消さなかった。",
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["人生"],
    }
    long_artifacts = _artifacts(long_repeated_burden)
    short_artifacts = _artifacts(short_help)
    long_plan, long_surface = long_artifacts[1], long_artifacts[5]
    short_plan, short_surface = short_artifacts[1], short_artifacts[5]

    assert len(long_repeated_burden["memo"]) > len(short_help["memo"])
    assert long_plan.depth_policy.raw_character_count_used is False
    assert long_plan.depth_policy.level == "minimal"
    assert len(long_plan.moves) == long_surface.sentence_count == 1
    assert short_plan.depth_policy.raw_character_count_used is False
    assert short_plan.depth_policy.safety_mode == "help_seeking_bounded"
    assert len(short_plan.moves) == short_surface.sentence_count == 2


def test_rr5_realizer_and_surface_validator_reject_move_corruption() -> None:
    (
        _plan,
        reception_plan,
        _sentence_plan,
        human_line,
        _result,
        direct,
        _observation,
        _reception,
        resolver,
    ) = _case("B")
    nucleus_index = {
        nucleus.nucleus_id: nucleus for nucleus in _plan.nuclei
    }
    clauses = human_line.reception_clause_plans

    clause_mutations = (
        (
            (*clauses, replace(clauses[-1], sentence_slot=3, move_ids=())),
            "human_reception_clause_count_mismatch",
        ),
        (
            (replace(clauses[0], sentence_slot=2), clauses[1]),
            "human_reception_clause_slot_invalid",
        ),
        (
            (
                replace(clauses[0], connector_policy="grounded_reason"),
                clauses[1],
            ),
            "human_reception_clause_connector_policy_mismatch",
        ),
        (
            (
                replace(clauses[0], quote_budget=1 - clauses[0].quote_budget),
                clauses[1],
            ),
                "human_reception_clause_quote_budget_exceeded",
        ),
        (
            (
                replace(
                    clauses[0],
                    terminal_predicate_family="human_response_quiet_presence",
                ),
                clauses[1],
            ),
            "human_reception_clause_predicate_family_mismatch",
        ),
    )
    for mutated_clauses, expected_reason in clause_mutations:
        with pytest.raises(
            GroundedHumanReceptionSurfaceError,
            match=expected_reason,
        ):
            realize_grounded_human_reception(
                reception_plan,
                nucleus_index,
                resolver,
                clause_plans=mutated_clauses,
            )

    dropped_move = replace(
        direct,
        realized_move_ids=direct.realized_move_ids[:-1],
    )
    dropped_issues = validate_grounded_human_reception_surface(
        dropped_move,
        reception_plan,
        resolver,
    )
    assert "human_reception_realized_move_mismatch" in dropped_issues
    assert "human_reception_required_move_missing" in dropped_issues

    duplicate_family = replace(
        direct,
        move_predicate_families=(
            direct.move_predicate_families[0],
            direct.move_predicate_families[0],
        ),
    )
    assert "human_reception_move_predicate_family_mismatch" in (
        validate_grounded_human_reception_surface(
            duplicate_family,
            reception_plan,
            resolver,
        )
    )
