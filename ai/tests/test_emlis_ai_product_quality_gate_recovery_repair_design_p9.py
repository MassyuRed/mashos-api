# -*- coding: utf-8 -*-
from __future__ import annotations

import json

from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
)
from emlis_ai_product_quality_blocker_matrix import (
    assert_product_quality_blocker_matrix_meta_only,
    build_product_quality_blocker_matrix,
    classify_product_quality_blocker,
)
from emlis_ai_product_quality_generation_repair_design import (
    assert_product_quality_generation_repair_design_meta_only,
    build_product_quality_generation_repair_design,
    dump_product_quality_generation_repair_design,
)
from emlis_ai_product_quality_measurement_runner import run_product_quality_measurement
from emlis_ai_types import ReplyEnvelope

VISIBLE_COMMENT = "P9 Gate Recovery leak regression visible body must not be serialized as material"
SECRET_INPUT = "P9 secret input body must not be serialized"
P9_REPAIR_TRACK = "gate_recovery_public_surface_boundary_repair"


def _gate_recovery_leak_event() -> dict[str, object]:
    return {
        "schema_version": "cocolon.emlis.product_quality.measurement_event.v1",
        "run_id": "pq_p9_gate_recovery",
        "row_id": "row_gate_recovery_public_leak",
        "family": "relationship_boundary",
        "public_display_reached": True,
        "comment_text_present": True,
        "comment_text_length": 64,
        "surface_origin": {
            "schema_version": "cocolon.emlis.product_quality.surface_origin.v1",
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
            "composer_model": GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
            "generation_method": GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
            "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
            "public_display_allowed_by_boundary": False,
            "gate_recovery_material_surface_detected": True,
            "post_final_gate_recovery_material_surface_detected": False,
            "internal_policy_sentence_leak_risk": True,
            "template_meta_false_negative_risk": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "binding": {
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "binding_passed": True,
        },
        "reason_coverage": {
            "reason_required_count": 0,
            "reason_covered_count": 0,
            "reason_coverage_passed": True,
        },
        "surface_quality": {"template_major_count": 0, "mirror_only_detected": False},
        "safety": {"safety_major_count": 0},
        "blockers": [
            BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
            BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
        ],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def test_p9_blocker_matrix_keeps_gate_recovery_public_leak_on_boundary_owner_and_event_family() -> None:
    classified = classify_product_quality_blocker(
        BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
        family="relationship_boundary",
    )
    assert classified["blocker_group"] == "surface_quality"
    assert classified["likely_owner_area"] == "surface_quality_gate_and_recovery_boundary"
    assert classified["severity"] == "critical"
    assert classified["release_blocking"] is True
    assert "emlis_ai_gate_recovery_public_candidate_builder.py" in classified["candidate_modules"]
    assert "emlis_ai_product_quality_generation_repair_design.py" in classified["candidate_modules"]
    assert classified["target_metric"] == "gate_recovery_public_leak_count"
    assert classified["target_metric_value"] == 0
    assert classified["public_contract_change_allowed"] is False
    assert classified["gate_relaxation_allowed"] is False

    matrix = build_product_quality_blocker_matrix(
        run_id="pq_p9_gate_recovery",
        events=[_gate_recovery_leak_event()],
        run_blockers=[BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK],
    )
    gate_rows = [
        row for row in matrix["rows"]
        if row["blocker_id"] == BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK
    ]
    assert len(gate_rows) == 1
    assert gate_rows[0]["family"] == "relationship_boundary"
    assert gate_rows[0]["likely_owner_area"] == "surface_quality_gate_and_recovery_boundary"
    assert gate_rows[0]["release_blocking"] is True
    assert gate_rows[0]["product_gate_ready"] is False
    assert gate_rows[0]["public_release_applied"] is False
    assert gate_rows[0]["raw_input_included"] is False
    assert gate_rows[0]["comment_text_body_included"] is False
    assert_product_quality_blocker_matrix_meta_only(matrix)


def test_p9_generation_repair_design_routes_gate_recovery_leak_to_dedicated_boundary_track() -> None:
    matrix = build_product_quality_blocker_matrix(
        run_id="pq_p9_gate_recovery_design",
        events=[_gate_recovery_leak_event()],
        run_blockers=[
            BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            "display_not_reached",
        ],
    )
    design = build_product_quality_generation_repair_design(
        run_id="pq_p9_gate_recovery_design",
        blocker_matrix=matrix,
    )

    assert P9_REPAIR_TRACK in design["repair_execution_order"]
    assert design["repair_execution_order"].index(P9_REPAIR_TRACK) < design["repair_execution_order"].index("display_reach_repair")
    assert P9_REPAIR_TRACK in design["phase5_focus_tracks"]

    gate_rows = [row for row in design["rows"] if row["repair_track"] == P9_REPAIR_TRACK]
    assert gate_rows
    row = next(row for row in gate_rows if row["source_blocker_id"] == BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK)
    assert row["target_owner_area"] == "surface_quality_gate_and_recovery_boundary"
    assert row["target_metric"] == "gate_recovery_public_leak_count"
    assert row["target_metric_value"] == 0
    assert row["generation_logic_change_required"] is True
    assert row["contract_change_allowed"] is False
    assert row["public_contract_change_allowed"] is False
    assert row["gate_relaxation_allowed"] is False
    assert row["fixed_template_allowed"] is False
    assert row["runtime_fixture_branch_allowed"] is False
    assert "emlis_ai_gate_recovery_public_boundary.py" in row["candidate_modules"]
    assert "emlis_ai_gate_recovery_public_candidate_builder.py" in row["candidate_modules"]
    assert "emlis_ai_product_quality_generation_repair_design.py" in row["candidate_modules"]
    assert "enforce_gate_recovery_public_boundary_before_display_gate" in row["repair_operation_ids"]
    assert "route_low_information_recovery_to_low_information_observation_composer" in row["repair_operation_ids"]
    assert "route_original_candidate_to_bounded_repair" in row["repair_operation_ids"]
    assert "stop_post_final_direct_material_surface_promotion" in row["repair_operation_ids"]
    assert "gate_recovery_material_surface_public_fallback" in row["forbidden_operation_ids"]
    assert "diagnostic_recovery_surface_to_comment_text" in row["forbidden_operation_ids"]
    assert "display_reached_only_from_allowed_public_candidate_source" in row["acceptance_check_ids"]
    assert "manual_triage_mapping_required" not in design["repair_execution_order"]

    dumped = dump_product_quality_generation_repair_design(design)
    assert VISIBLE_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert_product_quality_generation_repair_design_meta_only(design)


def test_p9_measurement_runner_connects_surface_origin_blocker_to_generation_repair_track() -> None:
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
                    "surface_signature_key": "p9_gate_recovery_signature",
                },
            },
        )

    run = run_product_quality_measurement(
        input_cases=[
            {
                "case_id": "p9_gate_recovery_surface_origin",
                "family": "relationship_boundary",
                "current_input": {"memo": SECRET_INPUT},
            }
        ],
        renderer=renderer,
        run_id="pq_p9_runner",
        created_at="2026-06-05T00:00:00Z",
        env={},
        enable_composer=True,
    )

    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in run["blockers"]
    design = run["generation_repair_design"]
    assert P9_REPAIR_TRACK in run["phase5_repair_execution_order"]
    assert any(row["repair_track"] == P9_REPAIR_TRACK for row in design["rows"])
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False

    dumped = json.dumps(run, ensure_ascii=False, sort_keys=True)
    assert VISIBLE_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
