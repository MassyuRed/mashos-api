# -*- coding: utf-8 -*-
from __future__ import annotations

"""Gate 0 R1 RED tests for current-input semantic retention.

These tests intentionally describe the approved structure that the received
R0 snapshot does not yet satisfy.  They assert Evidence-bound nuclei,
relations, and functional atoms; they never assert a completed public body.
Production code must not import this test module or branch on these fixtures.
"""

from collections.abc import Iterable
from typing import Any

import pytest

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)


_CASES = {
    case.case_id: case
    for case in (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
}


def _artifacts(case_id: str) -> tuple[Any, tuple[Any, ...], Any, Any, Any]:
    current_input = _CASES[case_id].as_current_input()
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return plan, spans, resolver, sentence_plan, surface


def _span_ids_containing(spans: Iterable[Any], anchor: str) -> set[str]:
    return {
        span.span_id
        for span in spans
        if anchor in str(span.raw_text or "")
    }


def _nucleus_ids_containing(plan: Any, spans: Iterable[Any], anchor: str) -> set[str]:
    source_ids = _span_ids_containing(spans, anchor)
    assert source_ids, f"test anchor does not resolve to Evidence: {anchor}"
    return {
        nucleus.nucleus_id
        for nucleus in plan.nuclei
        if source_ids.intersection(nucleus.source_span_ids)
    }


def _assert_required_anchors(plan: Any, spans: Iterable[Any], anchors: Iterable[str]) -> None:
    required = set(plan.coverage_requirements.required_nucleus_ids)
    for anchor in anchors:
        nucleus_ids = _nucleus_ids_containing(plan, spans, anchor)
        assert required.intersection(nucleus_ids), (
            anchor,
            sorted(nucleus_ids),
            sorted(required),
        )


def _relations_between(
    plan: Any,
    spans: Iterable[Any],
    *,
    from_anchor: str,
    to_anchor: str,
    relation_type: str | None = None,
) -> tuple[Any, ...]:
    from_ids = _nucleus_ids_containing(plan, spans, from_anchor)
    to_ids = _nucleus_ids_containing(plan, spans, to_anchor)
    return tuple(
        relation
        for relation in plan.relations
        if relation.from_nucleus_id in from_ids
        and relation.to_nucleus_id in to_ids
        and (relation_type is None or relation.type == relation_type)
    )


def _assert_required_relation(
    plan: Any,
    spans: Iterable[Any],
    *,
    from_anchor: str,
    to_anchor: str,
    relation_type: str,
) -> None:
    matches = _relations_between(
        plan,
        spans,
        from_anchor=from_anchor,
        to_anchor=to_anchor,
        relation_type=relation_type,
    )
    required = set(plan.coverage_requirements.required_relation_ids)
    assert matches, (from_anchor, relation_type, to_anchor)
    assert any(relation.relation_id in required for relation in matches), (
        from_anchor,
        relation_type,
        to_anchor,
        sorted(required),
    )


def test_known_b_keeps_shift_result_evaluation_and_concrete_change_required() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("B")
    _assert_required_anchors(
        plan,
        spans,
        (
            "疑問の対象が物になった",
            "人への興味が薄れた",
            "とても良い変化",
            "すぐに行動する勇気",
            "色んな場所を見て",
        ),
    )


def test_l01_keeps_each_major_turn_endpoint_required_without_four_item_cap() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("I6-L01")
    _assert_required_anchors(
        plan,
        spans,
        (
            "空欄を見るだけで手が止まった",
            "章立てだけは整えた",
            "一節を書けた",
            "完成には遠い",
            "作業の入口は作れた",
            "次回も同じ順で進めたい",
            "終わった箇所へ印を付けた",
        ),
    )
    assert len(plan.coverage_requirements.required_nucleus_ids) > 4


def test_l02_keeps_local_contrast_direction_as_required_relation() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("I6-L02")
    _assert_required_relation(
        plan,
        spans,
        from_anchor="場を乱したくない",
        to_anchor="黙ったままだと違和感が残った",
        relation_type="contrast",
    )


def test_l02_keeps_boundary_intention_to_saved_action_direction() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("I6-L02")
    _assert_required_relation(
        plan,
        spans,
        from_anchor="境界だけ短く伝えるつもり",
        to_anchor="三行に縮めて保存した",
        relation_type="action_supports_change",
    )


def test_l03_keeps_reversal_wish_unknown_next_action_and_record_required() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("I6-L03")
    _assert_required_anchors(
        plan,
        spans,
        (
            "想定より淡く出た",
            "失敗だと片づけそうになった",
            "細かな模様が見えた",
            "特徴を残したい",
            "焼成条件はまだ不明",
            "温度だけ変えるつもり",
            "温度と写真番号を作業帳へ記録した",
        ),
    )


def test_l03_provisional_failure_to_discovery_is_required_reversal() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("I6-L03")
    _assert_required_relation(
        plan,
        spans,
        from_anchor="失敗だと片づけそうになった",
        to_anchor="細かな模様が見えた",
        relation_type="preserves_despite",
    )


def test_l03_pale_result_to_provisional_failure_is_not_required_shift() -> None:
    plan, spans, _resolver, _sentence_plan, _surface = _artifacts("I6-L03")
    matches = _relations_between(
        plan,
        spans,
        from_anchor="想定より淡く出た",
        to_anchor="失敗だと片づけそうになった",
        relation_type="shift_from_to",
    )
    required = set(plan.coverage_requirements.required_relation_ids)
    assert not any(relation.relation_id in required for relation in matches)


def test_s03_preserves_source_predicate_without_new_sensation_family() -> None:
    plan, spans, _resolver, _sentence_plan, surface = _artifacts("I6-S03")
    nucleus_ids = _nucleus_ids_containing(plan, spans, "胸の内側が苦しい感じ")
    nucleus = next(item for item in plan.nuclei if item.nucleus_id in nucleus_ids)
    attributes = set(nucleus.semantic_frame.attribute_codes)
    assert "lexical:preserve_source_predicate" in attributes
    assert "lexical:no_new_sensation_family" in attributes
    assert "胸の内側が苦しい感じ" in surface.text
    assert "重さ" not in surface.text


def test_s03_keeps_short_state_reception_in_a_separate_two_stage_line() -> None:
    _plan, _spans, _resolver, sentence_plan, surface = _artifacts("I6-S03")
    assert len(sentence_plan.lines) == 2
    observation_line, reception_line = sentence_plan.lines
    assert observation_line.binding.line_role == "primary_observation"
    assert reception_line.binding.line_role == "human_follow"
    assert "human_follow:integrated_current_state" in reception_line.binding.functional_atom_ids
    assert "human_follow_delivery:separate" in reception_line.binding.functional_atom_ids
    assert "human_follow_delivery:integrated" not in reception_line.binding.functional_atom_ids
    assert sentence_plan.human_follow_covered is True
    assert surface.text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in surface.text


@pytest.mark.parametrize(
    ("case_id", "target_anchor"),
    (
        ("D", "いい事なんて絶対にない"),
        ("I6-D01", "作業記録を捨てるつもりはない"),
    ),
)
def test_self_denial_counterdirection_follow_is_not_classified_as_burden(
    case_id: str,
    target_anchor: str,
) -> None:
    plan, spans, _resolver, sentence_plan, _surface = _artifacts(case_id)
    target_ids = _nucleus_ids_containing(plan, spans, target_anchor)
    follow_lines = tuple(
        line
        for line in sentence_plan.lines
        if target_ids.intersection(line.binding.nucleus_ids)
        and any(
            atom.startswith("human_follow:")
            for atom in line.binding.functional_atom_ids
        )
    )
    assert follow_lines
    atoms = {
        atom
        for line in follow_lines
        for atom in line.binding.functional_atom_ids
    }
    assert "human_follow:protective_counterdirection" in atoms
    assert "human_follow:burden_expression" not in atoms
    assert "human_follow_delivery:separate" in atoms
    assert "human_follow_delivery:integrated" not in atoms
