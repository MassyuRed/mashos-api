# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_product_quality_measurement_event import (
    NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
    NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
    assert_product_quality_measurement_event_meta_only,
    normalize_product_quality_event,
    product_quality_event_to_scorecard_row,
)
from emlis_ai_product_quality_validation_plan import (
    P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES,
    assert_product_quality_validation_plan_meta_only,
    build_product_quality_validation_plan,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta

VISIBLE_COMMENT = "この記録では、仕事の話について気持ちが残っている状態として見えます。"
SECRET_RAW_INPUT = "P7_SECRET_RAW_INPUT_SHOULD_NOT_SURVIVE"
SECRET_COMMENT = "P7_SECRET_COMMENT_BODY_SHOULD_NOT_SURVIVE"


def _normal_rebuild_internal_meta() -> dict[str, object]:
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "passed",
        "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
        "visible_surface_acceptance_gate": {
            "evaluated": True,
            "passed": True,
            "classification": "pass",
            "action": "allow",
        },
        "phase20_13_post_final_gate_recovery": {
            "attempted": True,
            "applied": True,
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "public_candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "final_surface_origin_candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
            "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "public_display_allowed_by_boundary": True,
            "public_candidate_rebuilt_after_recovery": True,
            "diagnostic_surface_used": False,
            "normal_observation_rebuild_attempted": True,
            "normal_observation_rebuild_applied": True,
            "normal_observation_rebuild_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "normal_observation_rebuild_blocked_reasons": [],
            "raw_input_included": False,
            "comment_text_body_included": False,
            "reply_service_public_boundary": {
                "public_display_allowed": True,
                "blocked": False,
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "public_candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "adopted_candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "final_surface_origin_candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
                "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "normal_observation_rebuild_attempted": True,
                "normal_observation_rebuild_applied": True,
                "normal_observation_rebuild_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        },
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": "passed",
            "composer_status": "generated",
            "composer_source": "ai_generated",
            "phase20_13_post_final_gate_recovery": {
                "normal_observation_rebuild_attempted": True,
                "normal_observation_rebuild_applied": True,
                "normal_observation_rebuild_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "public_display_allowed_by_boundary": True,
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        },
    }


def test_p7_validation_plan_lists_normal_rebuild_as_allowed_public_candidate_source() -> None:
    plan = build_product_quality_validation_plan(run_id="p7_normal_rebuild_validation_plan")

    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE in P12_ALLOWED_PUBLIC_CANDIDATE_SOURCES
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE in plan["p12_allowed_public_candidate_sources"]
    assert (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        in plan["gate_recovery_public_surface_leak_repair_validation"]["allowed_public_candidate_sources"]
    )
    assert_product_quality_validation_plan_meta_only(plan)


def test_p7_public_feedback_meta_exposes_normal_rebuild_body_free_diagnostics() -> None:
    internal_meta = _normal_rebuild_internal_meta()
    # These unsafe source fields must never be copied into public meta.
    internal_meta["phase20_13_post_final_gate_recovery_with_secret"] = {
        "raw_input": SECRET_RAW_INPUT,
        "comment_text": SECRET_COMMENT,
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )

    normal_rebuild = public_meta["diagnostic_summary"]["normal_observation_rebuild"]
    assert normal_rebuild == {
        "attempted": True,
        "applied": True,
        "source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "public_boundary": {"public_display_allowed": True, "blocked": False},
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    dumped = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in dumped
    assert SECRET_COMMENT not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped


def test_p7_product_quality_event_keeps_normal_rebuild_surface_origin_public_and_known() -> None:
    internal_meta = _normal_rebuild_internal_meta()
    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
        subscription_tier="free",
    )
    event = normalize_product_quality_event(
        run_id="p7_normal_rebuild_event",
        row_id="row_normal_rebuild",
        source_type="regression_fixture",
        source_case_id="normal_observation_rebuild_surface_origin",
        family="mixed_emotion",
        comment_text=VISIBLE_COMMENT,
        public_meta=public_meta,
        internal_meta=internal_meta,
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 0,
            "reason_covered_count": 0,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
    )

    origin = event["surface_origin"]
    assert origin["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert origin["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert origin["public_display_allowed_by_boundary"] is True
    assert origin["normal_observation_rebuild_attempted"] is True
    assert origin["normal_observation_rebuild_applied"] is True
    assert origin["gate_recovery_material_surface_detected"] is False
    assert origin["post_final_gate_recovery_material_surface_detected"] is False
    assert event["gate_results"]["normal_observation_rebuild_attempted"] is True
    assert event["gate_results"]["normal_observation_rebuild_applied"] is True
    assert event["blockers"] == []

    row = product_quality_event_to_scorecard_row(event)
    assert row["surface_origin_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert row["surface_origin_normal_observation_rebuild_attempted"] is True
    assert row["surface_origin_normal_observation_rebuild_applied"] is True

    dumped = json.dumps({"event": event, "row": row}, ensure_ascii=False, sort_keys=True)
    assert VISIBLE_COMMENT not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped
    assert_product_quality_measurement_event_meta_only(event)
