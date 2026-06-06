# -*- coding: utf-8 -*-
from __future__ import annotations

"""P0 acceptance tests for current public-observation recovery red-state names."""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_public_observation_recovery_status import (
    RECOVERY_STATE_PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED,
    RECOVERY_STATE_PRODUCT_SURFACE_VALID,
    RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE,
    assert_public_observation_recovery_status,
    name_public_observation_recovery_state,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    resolve_public_surface_requirement,
)

_FORBIDDEN_META_KEYS = {
    "raw_input",
    "current_input",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
    "candidate_comment_text",
    "public_comment_text",
    "body",
    "text",
    "candidate_body",
    "surface_body",
}


def _assert_body_free(meta: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & _FORBIDDEN_META_KEYS)
            for child in value.values():
                walk(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                walk(child)

    walk(meta)


def _labelled_requirement() -> dict[str, Any]:
    return resolve_public_surface_requirement(
        current_input={
            "memo": "人との距離を考え直したい気持ちと嬉しさが同時に残っている。" * 4,
            "memo_action": "一度、自分の境界線を書き出してから話す。",
            "emotions": ["喜び", "不安"],
            "category": ["人間関係"],
        },
        material_route={"material_quality": "eligible", "material_sufficient": True},
        composer_meta={
            "state_answer_two_stage_display_required": True,
            "state_answer_joined_comment_text_required": True,
            "state_answer_section_labels_required": True,
            "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        diagnostic_summary={"reason_codes": ["relationship_boundary", "two_stage_required"]},
    )


def _plain_requirement() -> dict[str, Any]:
    return resolve_public_surface_requirement(
        current_input={"memo": "今日は少し落ち着いていた。", "memo_action": "夜は早く寝る。"},
        material_route={"material_quality": "eligible", "visible_material_slots": ["event", "action"]},
        composer_meta={"composer_source": "ai_generated", "candidate_status": "generated"},
        diagnostic_summary={},
    )


def test_p0_names_c_public_feedback_absent_complete_initial_surface_unavailable() -> None:
    summary = name_public_observation_recovery_state(
        comment_text="",
        public_meta={
            "public_observation_status": "unavailable",
            "first_backend_blocker": "complete_initial_surface_unavailable",
        },
        input_feedback_included=False,
        surface_requirement=_labelled_requirement(),
        candidate_generation={
            "candidate_source_kind": "none",
            "composer_source": "unavailable",
            "candidate_status": "unavailable",
            "candidate_generated_before_display_gate": False,
            "first_blocker_code": "complete_initial_surface_unavailable",
        },
        normal_observation_rebuild_used=False,
    )

    assert_public_observation_recovery_status(summary)
    assert summary["recovery_state_name"] == (
        RECOVERY_STATE_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE
    )
    assert summary["public_reached"] is False
    assert summary["rn_visible"] is False
    assert summary["product_surface_valid"] is False
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["recovery_lane"] == "complete_initial_surface_recomposition"
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["normal_observation_rebuild_blocker"] == "source_unavailable_not_rebuildable"
    _assert_body_free(summary)


def test_p0_names_d_rn_visible_but_plain_surface_invalid_for_two_stage_required() -> None:
    plain_surface = (
        "この記録では、人とのやり取りについて、喜びの動きがまだ落ち着ききっていない状態として見えます。"
        "次にどう動くかを探しているところもEmlisは受け取りました。"
    )
    summary = name_public_observation_recovery_state(
        comment_text=plain_surface,
        public_meta={"public_observation_status": "passed"},
        input_feedback_included=True,
        surface_requirement=_labelled_requirement(),
        candidate_generation={
            "candidate_source_kind": "normal_observation_rebuild_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
            "candidate_generated_before_display_gate": True,
        },
        normal_observation_rebuild_used=True,
    )

    assert_public_observation_recovery_status(summary)
    assert summary["recovery_state_name"] == (
        RECOVERY_STATE_PRODUCT_SURFACE_INVALID_PLAIN_USED_FOR_TWO_STAGE_REQUIRED
    )
    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["two_stage_required"] is True
    assert summary["plain_surface_used"] is True
    assert summary["labelled_two_stage_shape"]["labels_present"] is False
    _assert_body_free(summary)


def test_p0_plain_allowed_surface_can_be_product_valid_without_two_stage_labels() -> None:
    summary = name_public_observation_recovery_state(
        comment_text="この記録では、今日は少し落ち着いていた状態として見えます。夜は早く休もうとしているところもEmlisは受け取りました。",
        public_meta={"public_observation_status": "passed"},
        input_feedback_included=True,
        surface_requirement=_plain_requirement(),
        candidate_generation={
            "candidate_source_kind": "normal_observation_rebuild_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
            "candidate_generated_before_display_gate": True,
        },
    )

    assert summary["recovery_state_name"] == RECOVERY_STATE_PRODUCT_SURFACE_VALID
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert summary["two_stage_required"] is False
    assert summary["plain_state_answer_allowed"] is True
    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    _assert_body_free(summary)


def test_p0_labelled_two_stage_shape_is_product_valid_for_two_stage_required() -> None:
    summary = name_public_observation_recovery_state(
        comment_text=(
            "見えたこと：\n"
            "この記録では、人とのやり取りのあと、嬉しさと境界線の迷いが同時に残っている状態として見えます。\n\n"
            "Emlisから：\n"
            "すぐに結論へ寄せず、自分が守りたい距離を確かめようとしているところもEmlisは受け取りました。"
        ),
        public_meta={"public_observation_status": "passed"},
        input_feedback_included=True,
        surface_requirement=_labelled_requirement(),
        candidate_generation={
            "candidate_source_kind": "complete_initial_surface_recomposition_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
            "candidate_generated_before_display_gate": True,
        },
    )

    assert summary["recovery_state_name"] == RECOVERY_STATE_PRODUCT_SURFACE_VALID
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["two_stage_required"] is True
    assert summary["labelled_two_stage_shape"]["labels_present"] is True
    assert summary["product_surface_valid"] is True
    _assert_body_free(summary)
