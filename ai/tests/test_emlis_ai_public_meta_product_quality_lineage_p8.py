# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_complete_initial_surface_recomposition import (
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_PUBLIC_META_KEY,
)
from emlis_ai_product_quality_measurement_event import (
    normalize_product_quality_event,
    product_quality_event_to_scorecard_row,
)
from emlis_ai_product_quality_validation_plan import P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta


SECRET = "これはpublic metaへ入れてはいけない本文です"


def _surface_requirement(*, two_stage_required: bool) -> dict:
    return {
        "schema_version": "cocolon.emlis.public_surface_requirement.v1",
        "surface_requirement_family": "labelled_two_stage" if two_stage_required else "plain_state_answer",
        "two_stage_required": bool(two_stage_required),
        "plain_state_answer_allowed": not bool(two_stage_required),
        "low_information_allowed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _base_internal_meta(*, source_kind: str, composer_model: str, generation_method: str, two_stage_required: bool) -> dict:
    return {
        "schema_version": "internal.test.v1",
        "observation_status": "passed",
        "candidate_source_kind": source_kind,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_source": "ai_generated",
        "composer_model": composer_model,
        "generation_method": generation_method,
        "public_display_allowed_by_boundary": True,
        "surface_requirement": _surface_requirement(two_stage_required=two_stage_required),
        "surface_requirement_family": "labelled_two_stage" if two_stage_required else "plain_state_answer",
        "two_stage_required": bool(two_stage_required),
        "plain_surface_allowed": not bool(two_stage_required),
        "low_information_allowed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "diagnostic_summary": {
            "stage": "p8_lineage_test",
            "public_surface_lineage": {
                "candidate_source_kind": source_kind,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "composer_model": composer_model,
                "generation_method": generation_method,
                "public_display_allowed_by_boundary": True,
                "surface_requirement": _surface_requirement(two_stage_required=two_stage_required),
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        },
    }


def _assert_body_free(value: dict) -> None:
    dumped = json.dumps(value, ensure_ascii=False, sort_keys=True)
    assert SECRET not in dumped
    assert '"raw_input"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"candidate_body"' not in dumped
    assert '"surface_text"' not in dumped


def test_p8_public_meta_distinguishes_complete_initial_surface_recomposition_lineage_body_free() -> None:
    internal_meta = _base_internal_meta(
        source_kind=CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        composer_model=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        generation_method=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        two_stage_required=True,
    )
    internal_meta[COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY] = {
        **internal_meta,
        "source_unavailable_recovered": True,
        "complete_surface_recomposition_summary": {
            "complete_sentence_plan_connected": True,
            "complete_surface_realizer_connected": True,
        },
    }

    public_meta = build_public_emlis_input_feedback_meta(internal_meta, comment_text_present=True)

    assert public_meta[COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY]["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    )
    lineage = public_meta["public_surface_lineage"]
    assert lineage["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    assert lineage["complete_initial_surface_recomposition_used"] is True
    assert lineage["labelled_two_stage_surface_recomposition_used"] is False
    assert lineage["normal_observation_rebuild_used"] is False
    assert lineage["gate_recovery_material_surface_used_as_public_body"] is False
    assert lineage["public_candidate_source_allowed"] is True
    _assert_body_free(public_meta)


def test_p8_public_meta_distinguishes_labelled_two_stage_recomposition_lineage_body_free() -> None:
    internal_meta = _base_internal_meta(
        source_kind=CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        composer_model=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        generation_method=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        two_stage_required=True,
    )
    internal_meta[LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_PUBLIC_META_KEY] = {
        **internal_meta,
        "labelled_two_stage_surface_recomposition_used": True,
        "normal_observation_rebuild_used": False,
        "complete_initial_surface_recomposition_used": False,
        "labelled_two_stage_surface_recomposition_summary": {
            "labels_present": True,
            "section_budget_valid": True,
        },
    }

    public_meta = build_public_emlis_input_feedback_meta(internal_meta, comment_text_present=True)

    assert public_meta[LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_PUBLIC_META_KEY]["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    lineage = public_meta["public_surface_lineage"]
    assert lineage["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert lineage["complete_initial_surface_recomposition_used"] is False
    assert lineage["normal_observation_rebuild_used"] is False
    assert lineage["gate_recovery_material_surface_used_as_public_body"] is False
    assert lineage["public_candidate_source_allowed"] is True
    _assert_body_free(public_meta)


def test_p8_product_quality_infers_complete_initial_recomposition_from_model_without_unknown_origin() -> None:
    comment_text = "見えたこと：\n状態の構造が見えています。\n\nEmlisから：\nその動きを受け取りました。"
    internal_meta = _base_internal_meta(
        source_kind="",
        composer_model=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        generation_method=COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        two_stage_required=True,
    )
    public_meta = build_public_emlis_input_feedback_meta(
        {
            **internal_meta,
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        },
        comment_text_present=True,
    )

    event = normalize_product_quality_event(
        run_id="p8",
        row_id="complete_initial_recomposition",
        source_case_id="p8_complete_initial_recomposition",
        family="self_understanding_follow",
        comment_text=comment_text,
        public_meta=public_meta,
        internal_meta=internal_meta,
        composer_resolution={
            "composer_model": COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
            "generation_method": COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        },
    )

    origin = event["surface_origin"]
    assert origin["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    assert origin["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert origin["public_display_allowed_by_boundary"] is True
    assert origin["complete_initial_surface_recomposition_used"] is True
    assert origin["labelled_two_stage_surface_recomposition_used"] is False
    assert origin["normal_observation_rebuild_applied"] is False
    assert "public_display_not_reached" not in event["blockers"]

    row = product_quality_event_to_scorecard_row(event)
    assert row["surface_origin_complete_initial_surface_recomposition_used"] is True
    assert row["surface_origin_labelled_two_stage_surface_recomposition_used"] is False
    _assert_body_free(event)
    _assert_body_free(row)


def test_p8_product_quality_infers_labelled_two_stage_recomposition_from_model_without_unknown_origin() -> None:
    comment_text = "見えたこと：\n関係の境界が揺れているように見えます。\n\nEmlisから：\nそこに残っている迷いを受け取りました。"
    internal_meta = _base_internal_meta(
        source_kind="",
        composer_model=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
        generation_method=LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        two_stage_required=True,
    )
    public_meta = build_public_emlis_input_feedback_meta(
        {
            **internal_meta,
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        },
        comment_text_present=True,
    )

    event = normalize_product_quality_event(
        run_id="p8",
        row_id="labelled_two_stage_recomposition",
        source_case_id="p8_labelled_two_stage_recomposition",
        family="relationship_boundary",
        comment_text=comment_text,
        public_meta=public_meta,
        internal_meta=internal_meta,
        composer_resolution={
            "composer_model": LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
            "generation_method": LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
        },
    )

    origin = event["surface_origin"]
    assert origin["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert origin["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert origin["public_display_allowed_by_boundary"] is True
    assert origin["labelled_two_stage_surface_recomposition_used"] is True
    assert origin["complete_initial_surface_recomposition_used"] is False
    assert origin["normal_observation_rebuild_applied"] is False
    assert "public_display_not_reached" not in event["blockers"]

    row = product_quality_event_to_scorecard_row(event)
    assert row["surface_origin_labelled_two_stage_surface_recomposition_used"] is True
    assert row["surface_origin_complete_initial_surface_recomposition_used"] is False
    _assert_body_free(event)
    _assert_body_free(row)


def test_p8_validation_plan_accepts_new_public_observation_candidate_sources() -> None:
    assert CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE in P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES
    assert CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE in P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES
