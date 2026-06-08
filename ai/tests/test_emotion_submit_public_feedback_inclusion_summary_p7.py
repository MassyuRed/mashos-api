# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_complete_initial_surface_availability import (
    COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY,
)
from emlis_ai_product_surface_validation import (
    PRODUCT_SURFACE_BLOCKER_NONE,
    PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED,
    PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY,
    build_product_surface_validation_summary,
    product_surface_validation_public_summary,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
)
from emotion_submit_service import (
    _build_public_feedback_inclusion_summary,
    _public_visible_surface_gate_blocks,
    _with_public_feedback_inclusion_summary,
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
SECRET_RAW_INPUT = "P7 raw input must not appear"
SECRET_COMMENT_TEXT = "P7 generated comment body must not appear"


def _base_passed_public_meta() -> dict[str, object]:
    return {
        "observation_status": "passed",
        "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
        "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
        "state_answer_gate_boundary": {"passed": True},
    }


def test_p7_summary_does_not_treat_visible_surface_yellow_warn_as_absence() -> None:
    public_meta = {
        **_base_passed_public_meta(),
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": False,
            "classification": "yellow",
            "action": "warn",
        },
    }

    assert _public_visible_surface_gate_blocks(public_meta) is False

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=PLAIN_VISIBLE_COMMENT,
        internal_input_feedback_meta={
            "observation_status": "passed",
            "diagnostic_summary": {
                "raw_input": SECRET_RAW_INPUT,
                "comment_text": SECRET_COMMENT_TEXT,
            },
        },
        public_input_feedback_meta=public_meta,
    )

    assert summary["public_feedback_included"] is True
    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["public_feedback_not_included_visible_surface_gate"] is False
    assert summary["public_feedback_absence_reason_family"] == ""
    assert summary["first_blocker_family"] == ""
    assert summary["first_blocker_code"] == ""
    assert summary["reason_family"] != "visible_surface_gate"
    assert summary["reason_family"] != "rn_visible_contract"
    assert summary["rn_payload_absent"] is False
    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT_TEXT not in dumped


def test_p7_summary_keeps_visible_surface_repair_required_as_absence() -> None:
    public_meta = {
        **_base_passed_public_meta(),
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": False,
            "classification": "repair_required",
            "action": "rerender_surface",
        },
    }

    assert _public_visible_surface_gate_blocks(public_meta) is True

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=PLAIN_VISIBLE_COMMENT,
        internal_input_feedback_meta={"observation_status": "passed"},
        public_input_feedback_meta=public_meta,
    )

    assert summary["public_feedback_included"] is False
    assert summary["public_reached"] is False
    assert summary["rn_visible"] is False
    assert summary["public_feedback_not_included_visible_surface_gate"] is True
    assert summary["public_feedback_absence_reason_family"] == "visible_surface_gate"
    assert summary["reason_family"] == "visible_surface_gate"


def test_p7_summary_blocks_visible_surface_passed_false_without_warn() -> None:
    public_meta = {
        **_base_passed_public_meta(),
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": False,
            "classification": "yellow",
            "action": "allow",
        },
    }

    assert _public_visible_surface_gate_blocks(public_meta) is True

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=PLAIN_VISIBLE_COMMENT,
        internal_input_feedback_meta={"observation_status": "passed"},
        public_input_feedback_meta=public_meta,
    )

    assert summary["public_feedback_included"] is False
    assert summary["public_reached"] is False
    assert summary["rn_visible"] is False
    assert summary["public_feedback_not_included_visible_surface_gate"] is True
    assert summary["public_feedback_absence_reason_family"] == "visible_surface_gate"


def test_p7_summary_separates_rn_visible_from_product_surface_valid() -> None:
    product_surface_validation = product_surface_validation_public_summary(
        build_product_surface_validation_summary(
            input_feedback_included=True,
            comment_text=PLAIN_VISIBLE_COMMENT,
            emlis_ai_public_meta=_base_passed_public_meta(),
            surface_requirement={
                "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
                "two_stage_required": True,
                "plain_state_answer_allowed": False,
                "low_information_allowed": False,
                "raw_input": SECRET_RAW_INPUT,
                "comment_text": SECRET_COMMENT_TEXT,
            },
            candidate_generation_summary={
                "candidate_source_kind": "normal_observation_rebuild_candidate",
                "composer_source": "ai_generated",
                "candidate_status": "generated",
                "candidate_generated_before_display_gate": True,
                "comment_text": SECRET_COMMENT_TEXT,
            },
        )
    )
    public_meta = {
        **_base_passed_public_meta(),
        PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY: product_surface_validation,
    }

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=PLAIN_VISIBLE_COMMENT,
        internal_input_feedback_meta={
            "observation_status": "passed",
            "diagnostic_summary": {"raw_input": SECRET_RAW_INPUT, "comment_text": SECRET_COMMENT_TEXT},
        },
        public_input_feedback_meta=public_meta,
    )

    assert summary["schema_version"] == "cocolon.emlis.public_observation_recovery_summary.v1"
    assert summary["source_phase"] == "PublicObservationRecovery_P7_PublicFeedbackInclusionSummary"
    assert summary["public_feedback_included"] is True
    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is False
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["two_stage_required"] is True
    assert summary["plain_surface_allowed"] is False
    assert summary["candidate_source_kind"] == "normal_observation_rebuild_candidate"
    assert summary["first_blocker_family"] == "two_stage_shape_required"
    assert summary["first_blocker_code"] == PRODUCT_SURFACE_BLOCKER_PLAIN_USED_FOR_TWO_STAGE_REQUIRED
    assert summary["public_feedback_absence_reason_family"] == ""
    assert summary["reason_family"] == "two_stage_shape_required"
    assert summary["raw_input_included"] is False
    assert summary["comment_text_body_included"] is False
    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT_TEXT not in dumped


def test_p7_summary_names_complete_initial_absence_without_normal_rebuild() -> None:
    public_meta = {
        "observation_status": "unavailable",
        "rejection_reasons": ["complete_initial_surface_unavailable"],
        COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY: {
            "schema_version": "cocolon.emlis.complete_initial_surface_availability.v1",
            "source_phase": "PublicObservationRecovery_P4_CompleteInitialSurfaceAvailability",
            "complete_initial_client_resolved": True,
            "candidate_generation_attempted": True,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "first_blocker_family": "source_unavailable",
            "first_blocker_code": "complete_initial_surface_unavailable",
            "material_sufficient": True,
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "recovery_lane": "complete_initial_surface_recomposition",
            "normal_observation_rebuild_allowed": False,
            "normal_observation_rebuild_blocker": "source_unavailable_not_rebuildable",
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    }

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment="",
        internal_input_feedback_meta={
            "observation_status": "unavailable",
            "diagnostic_summary": {
                COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY: public_meta[
                    COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY
                ],
                "raw_input": SECRET_RAW_INPUT,
                "comment_text": SECRET_COMMENT_TEXT,
            },
        },
        public_input_feedback_meta=public_meta,
    )

    assert summary["public_feedback_included"] is False
    assert summary["public_reached"] is False
    assert summary["rn_visible"] is False
    assert summary["product_surface_valid"] is False
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["first_blocker_code"] == "complete_initial_surface_unavailable"
    assert summary["public_feedback_absence_reason_family"] == "source_unavailable"
    assert summary["candidate_source_kind"] == ""
    assert "complete_initial_surface_unavailable" in summary["reason_codes"]
    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT_TEXT not in dumped


def test_p7_summary_accepts_product_valid_labelled_surface_and_attaches_aliases() -> None:
    product_surface_validation = product_surface_validation_public_summary(
        build_product_surface_validation_summary(
            input_feedback_included=True,
            comment_text=LABELLED_VISIBLE_COMMENT,
            emlis_ai_public_meta=_base_passed_public_meta(),
            surface_requirement={
                "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
                "two_stage_required": True,
                "plain_state_answer_allowed": False,
                "low_information_allowed": False,
            },
            candidate_generation_summary={
                "candidate_source_kind": "labelled_two_stage_surface_recomposition_candidate",
                "composer_source": "ai_generated",
                "candidate_status": "generated",
                "candidate_generated_before_display_gate": True,
            },
        )
    )
    public_meta = {
        **_base_passed_public_meta(),
        PRODUCT_SURFACE_VALIDATION_PUBLIC_META_KEY: product_surface_validation,
    }

    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=LABELLED_VISIBLE_COMMENT,
        internal_input_feedback_meta={"observation_status": "passed"},
        public_input_feedback_meta=public_meta,
    )
    meta = _with_public_feedback_inclusion_summary(
        internal_input_feedback_meta={"observation_status": "passed"},
        inclusion_summary=summary,
    )

    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["first_blocker_family"] == ""
    assert summary["first_blocker_code"] == ""
    assert summary["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert summary["reason_family"] == "product_surface_valid"
    assert product_surface_validation["blocker_code"] == PRODUCT_SURFACE_BLOCKER_NONE
    diagnostic = meta["diagnostic_summary"]
    assert diagnostic["public_observation_recovery_summary"] == summary
    assert diagnostic["public_feedback_inclusion_summary"] == summary
    assert meta["public_observation_recovery_summary"] == summary
    assert meta["public_feedback_inclusion_summary"] == summary


def test_p7_summary_can_compute_plain_product_valid_when_no_p3_meta_exists() -> None:
    summary = _build_public_feedback_inclusion_summary(
        input_feedback_comment=PLAIN_VISIBLE_COMMENT,
        internal_input_feedback_meta={
            "observation_status": "passed",
            "diagnostic_summary": {
                "surface_requirement": {
                    "surface_requirement_family": SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
                    "two_stage_required": False,
                    "plain_state_answer_allowed": True,
                    "low_information_allowed": False,
                    "comment_text": SECRET_COMMENT_TEXT,
                    "raw_input": SECRET_RAW_INPUT,
                },
                "candidate_generation_summary": {
                    "candidate_source_kind": "normal_observation_rebuild_candidate",
                    "composer_source": "ai_generated",
                    "candidate_status": "generated",
                    "candidate_generated_before_display_gate": True,
                    "comment_text": SECRET_COMMENT_TEXT,
                },
            },
        },
        public_input_feedback_meta=_base_passed_public_meta(),
    )

    assert summary["public_reached"] is True
    assert summary["rn_visible"] is True
    assert summary["product_surface_valid"] is True
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert summary["two_stage_required"] is False
    assert summary["plain_surface_allowed"] is True
    assert summary["candidate_source_kind"] == "normal_observation_rebuild_candidate"
    dumped = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT_TEXT not in dumped
