# -*- coding: utf-8 -*-
from __future__ import annotations

from types import SimpleNamespace

import pytest

import emlis_ai_step11_semantic_overlay_v3 as overlay


def _required_choice_unknowns(text: str) -> list[overlay.Step11TypedUnknown]:
    """Exercise required-source binding without a corpus or sample oracle."""

    nucleus_id = "nucleus:decision"
    anchor = overlay._anchor(
        source_slot="thought",
        role="nucleus",
        text=text,
        start=0,
        end=len(text),
    )
    inventory_result = SimpleNamespace(
        source_snapshot=SimpleNamespace(
            nuclei=(
                SimpleNamespace(
                    source_id=nucleus_id,
                    source_fields=("memo",),
                ),
            ),
            relations=(),
            unknowns=(
                SimpleNamespace(
                    source_id="unknown:decision",
                    dimension_code="EXPLICIT_CHOICE_DECISION_UNKNOWN",
                    affected_nucleus_ids=(nucleus_id,),
                    required=True,
                ),
            ),
        )
    )
    return overlay._source_unknowns(
        inventory_result,
        [anchor],
        active_nucleus_ids=frozenset({nucleus_id}),
        projection={"thought_text": text, "action_text": ""},
        relations=(),
        anchor_ids_by_nucleus={nucleus_id: (anchor.anchor_id,)},
    )


def test_required_explicit_choice_dimension_types_generic_open_hesitation() -> None:
    rows = _required_choice_unknowns(
        "参加したい気持ちはあるのに迷うなんて、準備不足なのかな。"
    )

    assert len(rows) == 1
    assert rows[0].unknown_type == "decision_state"
    assert rows[0].decision_state == "open"
    assert rows[0].source_unknown_ids == ("unknown:decision",)
    assert rows[0].target_nucleus_ids == ("nucleus:decision",)
    assert rows[0].epistemic_basis == "frozen_required"


def test_required_choice_lifecycle_ambiguity_fails_closed() -> None:
    with pytest.raises(overlay.Step11SemanticOverlayError) as exc_info:
        _required_choice_unknowns("参加すると決めたのに、まだ迷っている。")

    assert exc_info.value.code == (
        "STEP11_OVERLAY_REQUIRED_UNKNOWN_UNCLASSIFIED"
    )


def test_nonexplicit_dimension_does_not_promote_generic_hesitation() -> None:
    assert (
        overlay._frozen_unknown_type(
            "CHOICE_DECISION_UNKNOWN",
            "参加したい気持ちはあるのに迷うなんて、準備不足なのかな。",
        )
        is None
    )


def test_explicit_dimension_without_source_uncertainty_fails_closed() -> None:
    assert (
        overlay._frozen_unknown_type(
            "EXPLICIT_CHOICE_DECISION_UNKNOWN",
            "参加条件を読み直した。",
        )
        is None
    )
