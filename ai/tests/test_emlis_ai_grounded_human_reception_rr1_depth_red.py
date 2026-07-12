# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR1 intentional RED contracts for response depth and language variety.

The tests use semantic depth, move counts, structural fingerprints, and frozen
hashes.  They never make a completed reception sentence the expected value.
RR2 and later stages own the production repair that turns the RED subset green.
"""

import ast
from collections import Counter
from dataclasses import asdict
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
    reception_active_acts,
    reception_effective_speaker_presence,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
_EXACT8 = _FIXTURE_ROOT / "grounded_human_reception_exact8_v2_20260712.json"
_FREEZE = _FIXTURE_ROOT / "grounded_human_reception_rr0_r8_freeze_20260712.json"
_SENTENCE_END_RE = re.compile(r"[。！？!?]+")
_LAYERED_CASE_IDS = ("B", "C", "I6-L03", "I6-C01")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    return plan, surface, observation.strip(), reception.strip(), report


def _case_artifacts(case_id: str):
    exact8 = _load(_EXACT8)
    case = next(row for row in exact8["cases"] if row["case_id"] == case_id)
    return _artifacts(case["exact_current_input"])


def _sentence_count(value: str) -> int:
    return len(tuple(part for part in _SENTENCE_END_RE.split(value) if part.strip()))


def _terminal_lexical_family(value: str) -> str:
    if "受け止め" in value:
        return "receive"
    if "感じ" in value:
        return "feel"
    if "大切にして" in value:
        return "cherish"
    if "思えません" in value:
        return "bounded_counterposition"
    return "other"


def _legacy_sentence_skeleton(plan, reception: str) -> tuple[object, ...]:
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    return (
        _sentence_count(reception),
        len(reception_active_acts(reception_plan, "full")),
        _terminal_lexical_family(reception),
        reception_effective_speaker_presence(reception_plan, "full"),
    )


def _walk_mapping(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk_mapping(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk_mapping(nested)


@pytest.mark.parametrize("case_id", _LAYERED_CASE_IDS)
def test_rr1_layered_cases_require_v2_depth_and_multiple_move_contract(
    case_id: str,
) -> None:
    plan, _surface, _observation, _reception, _report = _case_artifacts(case_id)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    depth_policy = getattr(reception_plan, "depth_policy", None)
    moves = getattr(reception_plan, "moves", None)

    assert depth_policy is not None, "RR2 GroundedReceptionDepthPolicy is missing"
    assert depth_policy.level == "layered"
    assert depth_policy.raw_character_count_used is False
    assert depth_policy.selected_move_count >= 2
    assert depth_policy.min_sentences >= 2
    assert moves is not None and len(moves) >= 2
    assert sum(bool(move.required) for move in moves) >= 2


@pytest.mark.parametrize("case_id", _LAYERED_CASE_IDS)
def test_rr1_layered_cases_do_not_collapse_to_one_reception_sentence(
    case_id: str,
) -> None:
    _plan, _surface, _observation, reception, _report = _case_artifacts(case_id)
    assert _sentence_count(reception) >= 2, (
        f"{case_id}: layered human reception collapsed to one sentence"
    )


def test_rr1_terminal_lexical_family_concentration_is_within_exact8_threshold() -> None:
    families = Counter(
        _terminal_lexical_family(_case_artifacts(case_id)[3])
        for case_id in _load(_EXACT8)["case_order"]
    )
    assert max(families.values()) <= 4, dict(families)


def test_rr1_sentence_skeleton_concentration_is_within_exact8_threshold() -> None:
    fingerprints = Counter()
    for case_id in _load(_EXACT8)["case_order"]:
        plan, _surface, _observation, reception, _report = _case_artifacts(case_id)
        fingerprints[_legacy_sentence_skeleton(plan, reception)] += 1
    assert max(fingerprints.values()) <= 3, dict(fingerprints)


def test_rr1_observation_freeze_and_existing_gate_contract_remain_green() -> None:
    freeze = _load(_FREEZE)
    expected = {row["case_id"]: row for row in freeze["cases"]}
    for case_id in freeze["case_order"]:
        _plan, _surface, observation, _reception, report = _case_artifacts(case_id)
        assert _sha256_text(observation) == expected[case_id][
            "current_observation_section_sha256"
        ]
        assert report.public_observation_status == "passed"
        assert report.semantic_quality_gate == "passed"


def test_rr1_short_inputs_are_not_water_filled() -> None:
    for case_id in ("A", "I6-S03"):
        plan, _surface, _observation, reception, _report = _case_artifacts(case_id)
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        assert _sentence_count(reception) == 1
        assert len(reception_active_acts(reception_plan, "full")) == 1


def test_rr1_self_denial_safety_and_bounded_counterposition_remain_green() -> None:
    for case_id in ("D", "I6-D02"):
        plan, _surface, _observation, reception, report = _case_artifacts(case_id)
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        assert _sentence_count(reception) == 2
        assert "felt_state_is_real" in reception_plan.safety_modifier_codes
        assert "identity_claim_is_not_accepted" in reception_plan.safety_modifier_codes
        assert report.public_observation_status == "passed"
        assert report.semantic_quality_gate == "passed"


def test_rr1_raw_length_control_pair_uses_semantics_not_character_count() -> None:
    long_single_opportunity = {
        "memo": (
            "今日はずっと重い。何をしても重く感じる。朝から重く、昼にも重く、"
            "今も同じ重さが続いている。何度言い直しても、ただしんどくて重い。"
        ),
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["生活"],
    }
    short_protected = {
        "memo": "自分には価値がない。それでも相談先は消さなかった。",
        "memo_action": "",
        "emotions": ["悲しみ"],
        "category": ["人生"],
    }
    long_result = _artifacts(long_single_opportunity)
    short_result = _artifacts(short_protected)
    long_plan = long_result[0].response_plan.human_reception_plan
    short_plan = short_result[0].response_plan.human_reception_plan
    assert long_plan is not None and short_plan is not None
    assert len(long_single_opportunity["memo"]) > len(short_protected["memo"])
    assert long_plan.primary_reception_act == "stay_with_current_burden"
    assert long_plan.secondary_reception_act is None
    assert _sentence_count(long_result[3]) == 1
    assert short_plan.primary_reception_act == "hold_help_seeking"
    assert short_plan.secondary_reception_act == "bounded_counter_self_denial"
    assert _sentence_count(short_result[3]) == 2

    for payload in (asdict(long_plan), asdict(short_plan)):
        assert "raw_character_count" not in payload
        assert "input_character_count" not in payload
        for mapping in _walk_mapping(payload):
            if "raw_character_count_used" in mapping:
                assert mapping["raw_character_count_used"] is False


def test_rr1_file_contains_no_exact_completed_reception_expectation() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or not any(
            isinstance(operator, ast.Eq) for operator in node.ops
        ):
            continue
        values = (node.left, *node.comparators)
        has_completed_body_field = any(
            isinstance(value, ast.Attribute)
            and value.attr in {"text", "comment_text", "current_body"}
            for value in values
        )
        has_literal_sentence = any(
            isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and len(value.value) >= 20
            for value in values
        )
        assert not (has_completed_body_field and has_literal_sentence)

