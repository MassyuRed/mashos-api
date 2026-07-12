# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR2 contracts for the body-free Reception Opportunity Inventory."""

from dataclasses import asdict, replace
import inspect
import json
from pathlib import Path

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import (
    build_grounded_observation_plan,
    build_grounded_reception_opportunities,
    validate_grounded_human_reception_plan,
)


_FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "grounded_human_reception_exact8_v2_20260712.json"
)
_EXPECTED_FAMILIES = {
    "A": {"current_burden"},
    "B": {"concrete_effort", "lived_change"},
    "C": {"retained_intention", "lived_change"},
    "D": {"current_burden", "counterdirection"},
    "I6-S03": {"current_burden"},
    "I6-L03": {"concrete_effort", "retained_intention"},
    "I6-C01": {"concrete_effort", "retained_intention", "lived_change"},
    "I6-D02": {"current_burden", "help_seeking", "counterdirection"},
}
_EXPECTED_ACT_BY_FAMILY = {
    "current_burden": "stay_with_current_burden",
    "concrete_effort": "honor_concrete_effort",
    "retained_intention": "protect_retained_intention",
    "lived_change": "recognize_lived_change",
    "help_seeking": "hold_help_seeking",
    "counterdirection": "bounded_counter_self_denial",
    "words_placed": "respect_words_placed",
}
_OPPORTUNITY_FIELDS = {
    "opportunity_id",
    "family",
    "reception_act",
    "target_nucleus_ids",
    "support_nucleus_ids",
    "source_evidence_span_ids",
    "retention",
    "priority",
    "source_field_count",
    "safety_required",
}


def _load_fixture():
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    reception_plan = plan.response_plan.human_reception_plan
    assert reception_plan is not None
    return plan, reception_plan, resolver


def _case(case_id: str):
    row = next(
        item for item in _load_fixture()["cases"] if item["case_id"] == case_id
    )
    return _artifacts(row["exact_current_input"])


def _validate(plan, reception_plan, resolver):
    return validate_grounded_human_reception_plan(
        reception_plan,
        expected_target_ids=plan.response_plan.human_follow_target_ids,
        nucleus_index={item.nucleus_id: item for item in plan.nuclei},
        resolver=resolver,
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
    )


@pytest.mark.parametrize("case_id", tuple(_EXPECTED_FAMILIES))
def test_rr2_exact8_inventory_comes_from_distinct_semantic_families(
    case_id: str,
) -> None:
    plan, reception_plan, resolver = _case(case_id)
    opportunities = reception_plan.opportunities

    assert {item.family for item in opportunities} == _EXPECTED_FAMILIES[case_id]
    assert [item.opportunity_id for item in opportunities] == [
        f"ro{index}" for index in range(1, len(opportunities) + 1)
    ]
    assert len({item.family for item in opportunities}) == len(opportunities)
    assert all(
        item.reception_act == _EXPECTED_ACT_BY_FAMILY[item.family]
        for item in opportunities
    )
    assert _validate(plan, reception_plan, resolver) == ()


@pytest.mark.parametrize("case_id", ("A", "I6-S03"))
def test_rr2_short_state_has_one_quiet_opportunity(case_id: str) -> None:
    _plan, reception_plan, _resolver = _case(case_id)
    assert len(reception_plan.opportunities) == 1
    assert reception_plan.opportunities[0].family == "current_burden"
    assert reception_plan.opportunities[0].safety_required is False


def test_rr2_opportunity_meta_is_body_free_and_evidence_resolved() -> None:
    for case_id in _EXPECTED_FAMILIES:
        _plan, reception_plan, resolver = _case(case_id)
        owned = set(reception_plan.observation_owned_nucleus_ids)
        for opportunity in reception_plan.opportunities:
            payload = asdict(opportunity)
            assert set(payload) == _OPPORTUNITY_FIELDS
            assert all(
                ord(character) < 128
                for character in json.dumps(payload, ensure_ascii=False)
            )
            assert set(opportunity.target_nucleus_ids).issubset(owned)
            assert set(opportunity.support_nucleus_ids).issubset(owned)
            assert resolver.unresolved_ids(
                opportunity.source_evidence_span_ids
            ) == ()


def test_rr2_selector_has_no_fixture_or_raw_body_input_route() -> None:
    parameters = set(
        inspect.signature(build_grounded_reception_opportunities).parameters
    )
    assert {
        "raw_text",
        "raw_character_count",
        "input_character_count",
        "case_id",
        "expected_hash",
        "completed_sentence",
    }.isdisjoint(parameters)


def test_rr2_unseen_structure_uses_the_same_general_inventory_route() -> None:
    unseen = (
        {
            "memo": "今日は机の上を片づけた。",
            "memo_action": "",
            "emotions": ["平穏"],
            "category": ["生活"],
        },
        {
            "memo": "続けたい。",
            "memo_action": "",
            "emotions": ["平穏"],
            "category": ["生活"],
        },
    )
    for current_input in unseen:
        plan, reception_plan, resolver = _artifacts(current_input)
        assert reception_plan.opportunities
        assert reception_plan.moves[0].reception_act == (
            reception_plan.primary_reception_act
        )
        assert _validate(plan, reception_plan, resolver) == ()


def test_rr2_does_not_create_ungrounded_self_denial_counterposition() -> None:
    plan, reception_plan, resolver = _artifacts(
        {
            "memo": "自分には価値がない。",
            "memo_action": "",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        }
    )
    assert "counterdirection" not in {
        item.family for item in reception_plan.opportunities
    }
    assert "bounded_counter_self_denial" not in {
        item.reception_act for item in reception_plan.opportunities
    }
    assert _validate(plan, reception_plan, resolver) == ()


@pytest.mark.parametrize(
    "memo,memo_action",
    (
        ("自分には何もできない。それでも記録は残した。", ""),
        ("自分には何もできない。", "表に記録した。"),
    ),
)
def test_rr2_performed_action_grounds_required_counter_opportunity(
    memo: str,
    memo_action: str,
) -> None:
    plan, reception_plan, resolver = _artifacts(
        {
            "memo": memo,
            "memo_action": memo_action,
            "emotions": ["悲しみ"],
            "category": ["人生"],
        }
    )
    counter = next(
        item
        for item in reception_plan.opportunities
        if item.family == "counterdirection"
    )
    assert counter.safety_required is True
    assert _validate(plan, reception_plan, resolver) == ()


def test_rr2_unperformed_negative_action_is_not_effort_or_counterevidence() -> None:
    plan, reception_plan, resolver = _artifacts(
        {
            "memo": "自分には何もできない。",
            "memo_action": "まだ動けていない。",
            "emotions": ["悲しみ"],
            "category": ["人生"],
        }
    )
    assert {item.family for item in reception_plan.opportunities} == {
        "current_burden"
    }
    assert _validate(plan, reception_plan, resolver) == ()


def test_rr2_validator_rejects_family_act_and_evidence_corruption() -> None:
    plan, reception_plan, resolver = _case("B")
    first = reception_plan.opportunities[0]
    mismatched = replace(first, reception_act="respect_words_placed")
    invalid_plan = replace(
        reception_plan,
        opportunities=(mismatched, *reception_plan.opportunities[1:]),
    )
    assert "human_reception_opportunity_act_mismatch" in _validate(
        plan, invalid_plan, resolver
    )

    unresolved = replace(first, source_evidence_span_ids=("s999999",))
    invalid_plan = replace(
        reception_plan,
        opportunities=(unresolved, *reception_plan.opportunities[1:]),
    )
    issues = _validate(plan, invalid_plan, resolver)
    assert "human_reception_opportunity_evidence_mismatch" in issues
    assert (
        "human_reception_opportunity_unresolved_evidence:s999999" in issues
    )

    safety_plan, safety_reception, safety_resolver = _case("I6-D02")
    help_opportunity = safety_reception.opportunities[0]
    assert help_opportunity.family == "help_seeking"
    weakened = replace(help_opportunity, safety_required=False)
    invalid_plan = replace(
        safety_reception,
        opportunities=(weakened, *safety_reception.opportunities[1:]),
    )
    assert "human_reception_opportunity_safety_required_mismatch" in _validate(
        safety_plan, invalid_plan, safety_resolver
    )
