# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

import pytest

import emlis_ai_step11_semantic_overlay_v3 as overlay


@pytest.mark.parametrize(
    "text",
    (
        "今の情報だけでは選べない。",
        "候補を選べなくて迷っている。",
        "今はまだ一つに選べません。",
        "まだ決められない。",
        "方針を決められていません。",
        "結論が出ていない。",
    ),
)
def test_open_decision_negative_morphology_is_typed(text: str) -> None:
    assert overlay._explicit_unknown_types(text) == ("decision_state",)
    assert (
        overlay._frozen_unknown_type("EXPLICIT_CHOICE_UNKNOWN", text)
        == "decision_state"
    )


@pytest.mark.parametrize(
    "text",
    (
        "候補を一つ選べた。",
        "候補を一つ選んだ。",
        "昨日のうちに決められた。",
        "方針を決定した。",
    ),
)
def test_completed_decision_morphology_is_not_open(text: str) -> None:
    assert "decision_state" not in overlay._explicit_unknown_types(text)
    assert (
        overlay._frozen_unknown_type("EXPLICIT_CHOICE_UNKNOWN", text)
        != "decision_state"
    )


def _typed_unknown(
    *,
    anchor_id: str,
    target_nucleus_id: str,
    source_unknown_ids: tuple[str, ...],
    source_rule: str,
    epistemic_basis: str,
) -> overlay.Step11TypedUnknown:
    return overlay.Step11TypedUnknown(
        unknown_id="s11unk_0000000000000000",
        unknown_type="decision_state",
        source_slots=("thought",),
        source_anchor_ids=(anchor_id,),
        target_nucleus_ids=(target_nucleus_id,),
        source_unknown_ids=source_unknown_ids,
        source_rules=(source_rule,),
        epistemic_basis=epistemic_basis,
        decision_state="open",
        context_nucleus_ids=(target_nucleus_id,),
        context_anchor_ids=(anchor_id,),
    )


def test_canonical_unknown_merges_exact_source_ownership_provenance() -> None:
    text = "今の情報だけでは選べない"
    nucleus = overlay._anchor(
        source_slot="thought",
        role="nucleus",
        text=text,
        start=0,
        end=len(text),
    )
    grammar = overlay._anchor(
        source_slot="thought",
        role="unknown",
        text=text,
        start=0,
        end=len(text),
    )

    result = overlay._canonical_unknowns(
        (
            _typed_unknown(
                anchor_id=nucleus.anchor_id,
                target_nucleus_id="nucleus:s1",
                source_unknown_ids=(),
                source_rule="grammar_decision_state",
                epistemic_basis="explicit_unknown",
            ),
            _typed_unknown(
                anchor_id=grammar.anchor_id,
                target_nucleus_id="nucleus:s1",
                source_unknown_ids=("unknown:s1",),
                source_rule="frozen_required_unknown",
                epistemic_basis="frozen_required",
            ),
        ),
        (nucleus, grammar),
    )

    assert len(result) == 1
    assert result[0].source_unknown_ids == ("unknown:s1",)
    assert result[0].source_rules == (
        "frozen_required_unknown",
        "grammar_decision_state",
    )
    assert result[0].epistemic_basis == "frozen_required"
    assert len(result[0].source_anchor_ids) == 1
    assert len(result[0].context_anchor_ids) == 1


def test_canonical_unknown_does_not_merge_equal_text_at_other_range() -> None:
    text = "選べない。選べない"
    first = overlay._anchor(
        source_slot="thought",
        role="unknown",
        text=text,
        start=0,
        end=4,
    )
    second_start = text.rfind("選べない")
    second = overlay._anchor(
        source_slot="thought",
        role="unknown",
        text=text,
        start=second_start,
        end=len(text),
    )
    rows = tuple(
        overlay.Step11TypedUnknown(
            unknown_id="s11unk_0000000000000000",
            unknown_type="unspecified",
            source_slots=("thought",),
            source_anchor_ids=(anchor.anchor_id,),
            target_nucleus_ids=("nucleus:s1",),
            source_unknown_ids=(),
            source_rules=("grammar_unspecified",),
            epistemic_basis="explicit_unknown",
        )
        for anchor in (first, second)
    )

    assert len(overlay._canonical_unknowns(rows, (first, second))) == 2


def test_closed_connective_normalizes_only_to_unique_exact_nucleus() -> None:
    text = "でも、今の情報だけでは選べない"
    source_start = len("でも、")
    nucleus = overlay._anchor(
        source_slot="thought",
        role="nucleus",
        text=text,
        start=source_start,
        end=len(text),
    )

    rows = overlay._grammar_unknowns(
        {"thought_text": text, "action_text": ""},
        [nucleus],
        active_slots=frozenset({"thought"}),
        anchor_ids_by_nucleus={"nucleus:s1": (nucleus.anchor_id,)},
        relations=(),
    )

    assert len(rows) == 1
    assert rows[0].unknown_type == "decision_state"
    assert rows[0].source_anchor_ids == (nucleus.anchor_id,)
    assert rows[0].target_nucleus_ids == ("nucleus:s1",)


def test_closed_connective_does_not_normalize_ambiguous_binding() -> None:
    text = "でも、今の情報だけでは選べない"
    source_start = len("でも、")
    nucleus = overlay._anchor(
        source_slot="thought",
        role="nucleus",
        text=text,
        start=source_start,
        end=len(text),
    )

    binding = overlay._closed_prefix_exact_nucleus_binding(
        source_text=text,
        source_slot="thought",
        start=0,
        end=len(text),
        target_nucleus_ids=("nucleus:s1", "nucleus:s2"),
        anchors=(nucleus,),
        anchor_ids_by_nucleus={
            "nucleus:s1": (nucleus.anchor_id,),
            "nucleus:s2": (nucleus.anchor_id,),
        },
    )

    assert binding is None


def test_relation_unknown_requires_exact_two_endpoint_set() -> None:
    relation = SimpleNamespace(
        from_nucleus_id="nucleus:s1",
        to_nucleus_id="nucleus:s2",
    )

    assert overlay._exact_relation_unknown_endpoint_set(
        ("nucleus:s1", "nucleus:s2"), (relation,)
    )
    assert not overlay._exact_relation_unknown_endpoint_set(
        ("nucleus:s1",), (relation,)
    )
    assert not overlay._exact_relation_unknown_endpoint_set(
        ("nucleus:s1", "nucleus:s2", "nucleus:s3"), (relation,)
    )


def test_one_ended_grammar_relation_downgrades_to_unspecified() -> None:
    text = "関係がまだ分からない。"
    nucleus = overlay._anchor(
        source_slot="thought",
        role="nucleus",
        text=text,
        start=0,
        end=len(text),
    )

    rows = overlay._grammar_unknowns(
        {"thought_text": text, "action_text": ""},
        [nucleus],
        active_slots=frozenset({"thought"}),
        anchor_ids_by_nucleus={"nucleus:s1": (nucleus.anchor_id,)},
        relations=(),
    )

    assert len(rows) == 1
    assert rows[0].unknown_type == "unspecified"
    assert rows[0].source_rules == (
        "grammar_relation_without_exact_endpoints_as_unspecified",
    )
