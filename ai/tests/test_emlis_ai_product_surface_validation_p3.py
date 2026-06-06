# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_product_quality_measurement_event import (
    normalize_product_quality_event,
    product_quality_event_to_scorecard_row,
)
from emlis_ai_product_surface_validation import (
    PRODUCT_SURFACE_BLOCKER_NONE,
    PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED,
    PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY,
    assert_product_surface_validation_summary,
    build_product_surface_validation_summary,
    product_surface_validation_public_summary,
    resolve_product_surface_requirement_from_sources,
)
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    public_surface_requirement_public_summary,
    resolve_public_surface_requirement,
)


PLAIN_VISIBLE_COMMENT = (
    "この記録では、人とのやり取りについて、喜びの動きがまだ落ち着ききっていない状態として見えます。"
)
LABELLED_VISIBLE_COMMENT = (
    "見えたこと：\n"
    "相手との距離感を確かめながら、自分の反応を整理しようとしている流れが見えます。\n\n"
    "Emlisから：\n"
    "すぐに結論へ押し込まず、今の揺れを見失わないように受け取りました。"
)
SECRET_RAW_INPUT = "p3 raw input must not appear"
SECRET_COMMENT_BODY = "p3 comment body must not appear"


def _passed_public_meta() -> dict[str, object]:
    return {
        "observation_status": "passed",
        "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
        "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
        "display_gate": {"passed": True},
        "state_answer_gate_boundary": {"passed": True},
    }


def _labelled_requirement() -> dict[str, object]:
    return resolve_public_surface_requirement(
        current_input={
            "memo": "人との関係で距離感を考え続けている",
            "memo_action": "相手への返し方を整理した",
            "emotions": ["joy", "anxiety"],
            "categories": ["relationship"],
        },
        composer_meta={
            "material_quality": "sufficient_input_material",
            "two_stage_required": True,
            "state_answer_joined_comment_text_required": True,
            "state_answer_section_labels_required": True,
        },
        fixture_family_meta={"fixture_family": "phase19_product_visible_relationship_boundary"},
        comment_text_present=True,
    )


def _plain_requirement() -> dict[str, object]:
    return resolve_public_surface_requirement(
        current_input={
            "memo": "今日の作業で少し疲れた",
            "memo_action": "休む予定を入れた",
            "emotions": ["tired"],
            "categories": ["daily"],
        },
        composer_meta={"material_quality": "sufficient_input_material"},
        comment_text_present=True,
    )


def test_p3_detects_rn_visible_but_invalid_plain_surface_for_two_stage_required() -> None:
    summary = build_product_surface_validation_summary(
        comment_text=PLAIN_VISIBLE_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=_labelled_requirement(),
        candidate_generation_summary={
            "candidate_source_kind": "normal_observation_rebuild_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
        },
        input_feedback_included=True,
    )

    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["two_stage_required"] is True
    assert summary["plain_surface_used"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    assert_product_surface_validation_summary(summary)


def test_p3_accepts_labelled_two_stage_shape_without_relaxing_contracts() -> None:
    summary = build_product_surface_validation_summary(
        comment_text=LABELLED_VISIBLE_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=_labelled_requirement(),
        candidate_generation_summary={
            "candidate_source_kind": "labelled_two_stage_surface_recomposition_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
        },
        input_feedback_included=True,
    )

    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_NONE
    assert summary["labelled_two_stage_shape"]["labels_present"] is True
    assert summary["labelled_two_stage_shape"]["section_budget_valid"] is True
    assert summary["public_contract"] == {
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
    }
    assert summary["gate_policy"] == {
        "display_gate_relaxed": False,
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
    }
    assert_product_surface_validation_summary(summary)


def test_p3_plain_state_answer_remains_valid_for_plain_requirement() -> None:
    summary = build_product_surface_validation_summary(
        comment_text=PLAIN_VISIBLE_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=_plain_requirement(),
        candidate_generation_summary={
            "candidate_source_kind": "normal_observation_rebuild_candidate",
            "composer_source": "ai_generated",
            "candidate_status": "generated",
        },
        input_feedback_included=True,
    )

    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert summary["plain_state_answer_allowed"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["blocker_code"] == PRODUCT_SURFACE_BLOCKER_NONE


def test_p3_public_feedback_meta_carries_body_free_validation_without_changing_visibility() -> None:
    product_surface_validation = build_product_surface_validation_summary(
        comment_text=PLAIN_VISIBLE_COMMENT,
        emlis_ai_public_meta=_passed_public_meta(),
        surface_requirement=_labelled_requirement(),
        candidate_generation_summary={"candidate_source_kind": "normal_observation_rebuild_candidate"},
        input_feedback_included=True,
    )

    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "free",
            "observation_status": "passed",
            PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY: product_surface_validation,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    assert public_meta["observation_status"] == "passed"
    assert should_include_public_input_feedback(PLAIN_VISIBLE_COMMENT, public_meta) is True
    assert public_meta[PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY]["rn_visible"] is True
    assert public_meta[PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY]["product_surface_valid"] is False
    dumped = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT_BODY not in dumped
    assert "comment_text\":" not in dumped
    assert "raw_input\":" not in dumped


def test_p3_product_quality_event_records_product_surface_validation_without_body_payload() -> None:
    requirement = public_surface_requirement_public_summary(_labelled_requirement())
    event = normalize_product_quality_event(
        run_id="p3_run",
        row_id="relationship_boundary_plain_misroute",
        source_type="regression_fixture",
        source_case_id="phase19_D_plain_shape",
        family="relationship_boundary",
        comment_text=PLAIN_VISIBLE_COMMENT,
        public_meta={
            **_passed_public_meta(),
            "surface_requirement": requirement,
        },
        internal_meta={
            "observation_status": "passed",
            "surface_requirement": requirement,
        },
        composer_resolution={
            "composer_source": "ai_generated",
            "candidate_status": "generated",
            "candidate_source_kind": "normal_observation_rebuild_candidate",
        },
    )

    validation = event["surface_quality"]["product_surface_validation"]
    assert validation["rn_visible"] is True
    assert validation["product_surface_valid"] is False
    assert validation["blocker_code"] == PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED
    assert PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED in event["blockers"]

    row = product_quality_event_to_scorecard_row(event)
    assert row["product_surface_valid"] is False
    assert row["product_surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert row["product_surface_blocker_code"] == PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED

    dumped = json.dumps(event, ensure_ascii=False, sort_keys=True)
    assert PLAIN_VISIBLE_COMMENT not in dumped
    assert "comment_text\":" not in dumped
    assert "raw_input\":" not in dumped


def test_p3_resolves_requirement_from_nested_body_free_sources() -> None:
    requirement = public_surface_requirement_public_summary(_labelled_requirement())
    found = resolve_product_surface_requirement_from_sources(
        {
            "diagnostic_summary": {
                "product_surface_validation": {
                    "surface_requirement": requirement,
                }
            }
        }
    )

    assert found["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert found["two_stage_required"] is True
    assert found["raw_input_included"] is False
    assert found["comment_text_body_included"] is False

    summary = product_surface_validation_public_summary(
        build_product_surface_validation_summary(
            comment_text=LABELLED_VISIBLE_COMMENT,
            emlis_ai_public_meta=_passed_public_meta(),
            surface_requirement=found,
            candidate_generation_summary={"candidate_source_kind": "labelled_two_stage_surface_recomposition_candidate"},
            input_feedback_included=True,
        )
    )
    assert summary["product_surface_valid"] is True
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
