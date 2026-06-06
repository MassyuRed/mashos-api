# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_product_quality_measurement_event import (
    NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
    NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
    PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION,
    assert_product_quality_measurement_event_meta_only,
    normalize_product_quality_event,
    product_quality_event_to_scorecard_row,
)
from emlis_ai_product_quality_measurement_runner import (
    assert_product_quality_measurement_run_meta_only,
    dump_product_quality_measurement_run,
    run_product_quality_measurement,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_types import ReplyEnvelope

VISIBLE_COMMENT = "P8 surface origin用の表示本文。run materialへ本文を残してはいけない。"
SECRET_INPUT = "P8 secret raw input must never be serialized"


def _passed_public_meta() -> dict[str, object]:
    return build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "free",
            "observation_status": "passed",
            "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
            "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
            "state_answer_gate_boundary": {"passed": True},
        },
        comment_text_present=True,
        subscription_tier="free",
    )


def test_p8_product_quality_event_records_allowed_surface_origin_without_text() -> None:
    event = normalize_product_quality_event(
        run_id="pq_p8_event",
        row_id="row_allowed",
        source_type="fixture_family",
        source_case_id="allowed_surface_origin",
        family="daily_positive",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
        internal_meta={
            "observation_status": "passed",
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "composer_model": "bounded_repaired_original_candidate_v1",
            "generation_method": "bounded_repair_after_gate_recovery",
        },
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 0,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
    )

    origin = event["surface_origin"]
    assert origin["schema_version"] == PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION
    assert origin["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert origin["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert origin["public_display_allowed_by_boundary"] is True
    assert origin["gate_recovery_material_surface_detected"] is False
    assert origin["raw_input_included"] is False
    assert origin["comment_text_body_included"] is False
    assert event["blockers"] == []

    row = product_quality_event_to_scorecard_row(event)
    assert row["surface_origin_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    dumped = json.dumps({"event": event, "row": row}, ensure_ascii=False, sort_keys=True)
    assert VISIBLE_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert_product_quality_measurement_event_meta_only(event)


def test_p8_product_quality_event_records_normal_observation_rebuild_as_allowed_surface_origin_without_text() -> None:
    event = normalize_product_quality_event(
        run_id="pq_p8_event",
        row_id="row_normal_rebuild",
        source_type="regression_fixture",
        source_case_id="normal_observation_rebuild_surface_origin",
        family="relationship_boundary",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
        internal_meta={
            "observation_status": "passed",
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
            "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
            "normal_observation_rebuild_attempted": True,
            "normal_observation_rebuild_applied": True,
            "reply_service_public_boundary": {
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "public_display_allowed": True,
                "normal_observation_rebuild_attempted": True,
                "normal_observation_rebuild_applied": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        },
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 1,
            "reason_covered_count": 1,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
    )

    origin = event["surface_origin"]
    assert origin["schema_version"] == PRODUCT_QUALITY_SURFACE_ORIGIN_SCHEMA_VERSION
    assert origin["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert origin["composer_model"] == NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
    assert origin["generation_method"] == NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD
    assert origin["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert origin["public_display_allowed_by_boundary"] is True
    assert origin["gate_recovery_material_surface_detected"] is False
    assert origin["post_final_gate_recovery_material_surface_detected"] is False
    assert origin["internal_policy_sentence_leak_risk"] is False
    assert origin["template_meta_false_negative_risk"] is False
    assert origin["normal_observation_rebuild_attempted"] is True
    assert origin["normal_observation_rebuild_applied"] is True
    assert origin["raw_input_included"] is False
    assert origin["comment_text_body_included"] is False
    assert event["gate_results"]["normal_observation_rebuild_attempted"] is True
    assert event["gate_results"]["normal_observation_rebuild_applied"] is True
    assert event["blockers"] == []

    row = product_quality_event_to_scorecard_row(event)
    assert row["surface_origin_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert row["surface_origin_normal_observation_rebuild_attempted"] is True
    assert row["surface_origin_normal_observation_rebuild_applied"] is True
    dumped = json.dumps({"event": event, "row": row}, ensure_ascii=False, sort_keys=True)
    assert VISIBLE_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert_product_quality_measurement_event_meta_only(event)


def test_p8_product_quality_event_blocks_public_gate_recovery_surface_origin() -> None:
    event = normalize_product_quality_event(
        run_id="pq_p8_event",
        row_id="row_gate_recovery_leak",
        source_type="regression_fixture",
        source_case_id="gate_recovery_public_leak",
        family="relationship_boundary",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
        internal_meta={
            "observation_status": "passed",
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
            "composer_model": GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
            "generation_method": GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
            "surface_quality_signature": {
                "surface_template_major": False,
                "template_major": False,
            },
        },
        composer_resolution={
            "default_limited_enabled": False,
            "rejection_reasons": ["default_limited_composer_feature_disabled"],
        },
        machine_metrics={
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 0,
            "template_major_count": 0,
            "safety_major_count": 0,
        },
    )

    origin = event["surface_origin"]
    assert origin["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    assert origin["public_surface_role"] == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    assert origin["public_display_allowed_by_boundary"] is False
    assert origin["gate_recovery_material_surface_detected"] is True
    assert origin["template_meta_false_negative_risk"] is True
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in event["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in event["blockers"]
    assert BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE in event["blockers"]
    assert event["product_gate_ready"] is False
    assert event["public_release_applied"] is False

    dumped = json.dumps(event, ensure_ascii=False, sort_keys=True)
    assert VISIBLE_COMMENT not in dumped
    assert '"comment_text":' not in dumped
    assert_product_quality_measurement_event_meta_only(event)


def test_p8_product_quality_event_marks_post_final_gate_recovery_origin() -> None:
    event = normalize_product_quality_event(
        run_id="pq_p8_event",
        row_id="row_post_final_leak",
        source_type="regression_fixture",
        source_case_id="post_final_gate_recovery_public_leak",
        family="daily_unpleasant",
        comment_text=VISIBLE_COMMENT,
        public_meta=_passed_public_meta(),
        internal_meta={
            "observation_status": "passed",
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
            "composer_model": POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
            "generation_method": POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
        },
    )

    origin = event["surface_origin"]
    assert origin["post_final_gate_recovery_material_surface_detected"] is True
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in event["blockers"]
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in event["blockers"]
    assert_product_quality_measurement_event_meta_only(event)


def test_p8_runner_summarizes_surface_origin_and_keeps_release_closed() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text=VISIBLE_COMMENT,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
                "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
                "composer_model": GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
                "generation_method": GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
                "surface_quality_signature": {
                    "surface_template_major": False,
                    "template_major": False,
                },
                "diagnostic_summary": {
                    "binding_required_count": 1,
                    "binding_supported_count": 1,
                    "reason_required_count": 0,
                    "reason_covered_count": 0,
                    "surface_signature_key": "p8_gate_recovery_signature",
                },
            },
        )

    run = run_product_quality_measurement(
        input_cases=[
            {
                "case_id": "p8_gate_recovery_surface_origin",
                "family": "relationship_boundary",
                "current_input": {"memo": SECRET_INPUT},
            }
        ],
        renderer=renderer,
        run_id="pq_p8_runner",
        created_at="2026-06-05T00:00:00Z",
        env={},
        enable_composer=True,
    )

    event = run["measurement_events"][0]
    assert event["surface_origin"]["gate_recovery_material_surface_detected"] is True
    assert run["machine_metrics"]["public_display_reached_via_gate_recovery_material_surface_count"] == 1
    assert run["surface_origin_summary"]["gate_recovery_material_surface_event_count"] == 1
    assert run["surface_origin_summary"]["candidate_source_kind_counts"][CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE] == 1
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in run["blockers"]
    assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in run["blockers"]
    assert BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE in run["blockers"]
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False

    dumped = dump_product_quality_measurement_run(run)
    assert VISIBLE_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert_product_quality_measurement_run_meta_only(run)


def test_p8_runner_counts_normal_observation_rebuild_as_allowed_public_origin() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text=VISIBLE_COMMENT,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
                "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
                "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
                "normal_observation_rebuild_attempted": True,
                "normal_observation_rebuild_applied": True,
                "surface_origin": {
                    "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                    "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
                    "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
                    "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                    "public_display_allowed_by_boundary": True,
                    "gate_recovery_material_surface_detected": False,
                    "post_final_gate_recovery_material_surface_detected": False,
                    "normal_observation_rebuild_attempted": True,
                    "normal_observation_rebuild_applied": True,
                    "raw_input_included": False,
                    "comment_text_body_included": False,
                },
                "diagnostic_summary": {
                    "binding_required_count": 1,
                    "binding_supported_count": 1,
                    "reason_required_count": 1,
                    "reason_covered_count": 1,
                    "surface_signature_key": "p8_normal_rebuild_signature",
                },
            },
        )

    run = run_product_quality_measurement(
        input_cases=[
            {
                "case_id": "p8_normal_observation_rebuild_surface_origin",
                "family": "relationship_boundary",
                "current_input": {"memo": SECRET_INPUT},
            }
        ],
        renderer=renderer,
        run_id="pq_p8_normal_rebuild_runner",
        created_at="2026-06-05T00:00:00Z",
        env={},
        enable_composer=True,
    )

    event = run["measurement_events"][0]
    assert event["surface_origin"]["candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    assert event["surface_origin"]["public_display_allowed_by_boundary"] is True
    assert event["surface_origin"]["normal_observation_rebuild_attempted"] is True
    assert event["surface_origin"]["normal_observation_rebuild_applied"] is True
    assert event["surface_origin"]["gate_recovery_material_surface_detected"] is False
    assert event["surface_origin"]["post_final_gate_recovery_material_surface_detected"] is False
    assert run["machine_metrics"]["public_display_reached_via_gate_recovery_material_surface_count"] == 0
    assert run["surface_origin_summary"]["gate_recovery_material_surface_event_count"] == 0
    assert run["surface_origin_summary"]["post_final_gate_recovery_material_surface_event_count"] == 0
    assert run["surface_origin_summary"]["candidate_source_kind_counts"] == {
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE: 1,
    }
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in run["blockers"]
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in run["blockers"]
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False

    dumped = dump_product_quality_measurement_run(run)
    assert VISIBLE_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert_product_quality_measurement_run_meta_only(run)
