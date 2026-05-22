from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_connection import (
    build_complete_product_quality_measurement_connection,
)
from emlis_ai_complete_surface_quality_branching import resolve_runtime_surface_quality_branch
from emlis_ai_complete_surface_quality_signature import build_surface_quality_signature
from emlis_ai_runtime_surface_complete_activation_branch import (
    RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_VERSION,
    assert_runtime_surface_complete_activation_branch_meta_only,
    build_runtime_surface_complete_activation_branch,
    dump_runtime_surface_complete_activation_branch,
)
from emlis_ai_runtime_surface_source_lock import build_runtime_surface_source_lock

_NATURAL_TEXT = (
    "Emlisです。\n"
    "今は、自分の内側を少し整え直したい時間が前に出ています。\n"
    "急いで決めるよりも、いま残っている疲れを見落とさないことが大事そうです。\n"
    "その奥には、次へ進みたい気持ちも一緒に残っています。"
)
_TEMPLATE_LIKE_TEXT = (
    "Emlisです。\n"
    "体調を整えることが中心にあります。\n"
    "その中でも、お仕事を頑張って今後の準備をすることも見えています。\n"
    "その中でも、だいぶ先になることも重なっています。"
)


def _source_lock(source: str, *, requested: str | None = None, used: bool = False) -> dict[str, object]:
    return {
        "schema_version": "emlis.runtime_surface_source_lock.v1",
        "runtime_surface_source_lock_ready": True,
        "runtime_surface_source_locked": True,
        "trace_id": f"trace-{source}",
        "emotion_log_id": f"emotion-{source}",
        "observation_status": "passed" if source != "unavailable" else "unavailable",
        "backend_comment_text_present": source != "unavailable",
        "backend_comment_text_length": 120 if source != "unavailable" else 0,
        "display_confirmed": source != "unavailable",
        "coverage_group": "short_daily",
        "composer_requested": requested or source,
        "composer_resolved": source,
        "composer_source": source,
        "composer_model": "emlis.test",
        "complete_initial_client_used": used,
        "limited_reader_repair_applied": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
    }


def _green_review() -> dict[str, object]:
    return {
        "review_id": "green-step6",
        "coverage_group": "short_daily",
        "ratings": {
            "read_feeling": "green",
            "evidence_retention": "green",
            "distance": "green",
            "naturalness": "green",
            "non_template": "green",
        },
    }


def _row(source: str = "limited") -> dict[str, object]:
    signature = build_surface_quality_signature(comment_text=_TEMPLATE_LIKE_TEXT)
    return {
        "trace_id": f"step6-{source}",
        "emotion_log_id": f"emotion-step6-{source}",
        "coverage_group": "short_daily",
        "backend_status": "passed",
        "backend_len": 120,
        "backend_comment_text_present": True,
        "backend_public_passed": True,
        "frontend_joined": True,
        "frontend_join_status": "joined",
        "modal_opened": True,
        "display_confirmed": True,
        "diagnostic_capture_status": "captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured",
        "classification": "passed_displayed",
        "measurement_classification": "passed_displayed",
        "candidate_generated": True,
        "binding_supported_sentence_count": 2,
        "expected_binding_count": 2,
        "runtime_surface_source_lock": _source_lock(source, requested=source, used=(source == "complete_initial")),
        "surface_quality_signature": signature,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def test_step6_limited_source_routes_to_complete_runtime_activation_before_surface() -> None:
    branch = build_runtime_surface_complete_activation_branch(
        runtime_surface_quality_branch={
            "target_layer": "complete_runtime_activation",
            "selected_reason": "composer_source:limited",
        },
        runtime_surface_source_lock=_source_lock("limited"),
        composer_client_resolution={
            "requested_composer": "limited",
            "connection_status": "provided_client",
            "complete_initial_client_used": False,
        },
    )

    assert branch["version"] == RUNTIME_SURFACE_COMPLETE_ACTIVATION_BRANCH_VERSION
    assert branch["step6_complete_runtime_activation_branch_ready"] is True
    assert branch["target_layer"] == "complete_runtime_activation"
    assert branch["activation_branch_required"] is True
    assert branch["runtime_composer_source"] == "limited"
    assert branch["activation_status"] == "activation_required_but_complete_initial_not_requested"
    assert branch["surface_repair_deferred_until_complete_runtime_measurable"] is True
    assert branch["surface_text_repaired_by_step6"] is False
    assert branch["rn_complete_dedicated_display_branch_added"] is False
    assert branch["display_gate_relaxed"] is False


def test_step6_complete_initial_resolved_is_safe_to_measure_when_source_lock_aligns() -> None:
    branch = build_runtime_surface_complete_activation_branch(
        runtime_surface_quality_branch={"target_layer": "complete_runtime_activation"},
        runtime_surface_source_lock=_source_lock("complete_initial", requested="complete_initial", used=True),
        composer_client_resolution={
            "requested_composer": "complete_initial",
            "canonical_requested_composer": "complete_composer_initial",
            "connection_status": "default_client_resolved",
            "complete_initial_client_used": True,
            "complete_initial_requested": True,
            "resolved_client_class": "CompleteComposerInitialClient",
            "release_allowed": True,
            "complete_initial_gate": {"ap0_green": True, "release_allowed": True, "reason": "ok"},
        },
        complete_initial_entry_ap0_decision={"phase": "complete_initial_entry_ap0", "green": True, "can_proceed_to_a1": True},
        release_meta={"release_allowed": True, "rollout_allowed": True, "stage": "internal"},
    )

    assert branch["activation_status"] == "resolved_complete_initial"
    assert branch["complete_initial_requested"] is True
    assert branch["complete_initial_client_used"] is True
    assert branch["complete_initial_resolved"] is True
    assert branch["complete_initial_source_lock_aligned"] is True
    assert branch["complete_initial_resolution_safe_to_measure"] is True
    assert branch["entry_ap0_or_rollout_required_before_surface_repair"] is False
    assert branch["rn_visible_contract_changed"] is False


def test_step6_ap0_red_does_not_resolve_complete_client_and_keeps_fail_closed() -> None:
    branch = build_runtime_surface_complete_activation_branch(
        runtime_surface_quality_branch={"target_layer": "complete_runtime_activation"},
        runtime_surface_source_lock=_source_lock("unavailable", requested="complete_initial", used=False),
        composer_client_resolution={
            "requested_composer": "complete_initial",
            "canonical_requested_composer": "complete_composer_initial",
            "connection_status": "blocked_ap0",
            "pre_connection_stop_stage": "ap0",
            "complete_initial_client_used": False,
            "complete_initial_requested": True,
        },
        complete_initial_entry_ap0_decision={
            "phase": "complete_initial_entry_ap0",
            "green": False,
            "can_proceed_to_a1": False,
            "unmet_checks": ["ap0_green"],
        },
        release_meta={"release_allowed": True, "rollout_allowed": True},
    )

    assert branch["activation_status"] == "blocked_ap0"
    assert branch["complete_initial_client_used"] is False
    assert branch["complete_initial_resolved"] is False
    assert branch["ap0_red_blocks_complete_client"] is True
    assert branch["entry_ap0_or_rollout_required_before_surface_repair"] is True
    assert branch["display_gate_relaxed"] is False
    assert branch["gate_relaxed"] is False
    assert branch["product_gate_public_release_applied"] is False


def test_step6_measurement_connection_carries_activation_branch_without_text_or_contract_changes() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_row("limited")],
        blind_qa_reviews=[_green_review()],
        run_id="runtime-surface-step6",
    )

    activation = report["runtime_surface_complete_activation_branch"]
    step5 = report["runtime_surface_quality_branch"]
    assert step5["target_layer"] == "complete_runtime_activation"
    assert report["step6_runtime_surface_complete_activation_branch_ready"] is True
    assert activation["runtime_surface_complete_activation_branch_ready"] is True
    assert activation["target_layer"] == "complete_runtime_activation"
    assert activation["runtime_composer_source"] == "limited"
    assert activation["surface_text_repaired_by_step6"] is False
    assert activation["rn_complete_dedicated_display_branch_added"] is False
    assert report["runtime_surface_complete_activation_status"] == activation["activation_status"]
    assert report["public_release_applied"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["api_route_changed"] is False
    assert report["db_physical_name_changed"] is False
    assert report["display_gate_relaxed"] is False

    dumped = json.dumps(report, ensure_ascii=False)
    assert _TEMPLATE_LIKE_TEXT not in dumped
    assert "体調を整える" not in dumped
    assert '"comment_text"' not in dumped


def test_step6_branch_is_meta_only_and_rejects_text_payload_keys() -> None:
    branch = build_runtime_surface_complete_activation_branch(
        runtime_surface_quality_branch={"target_layer": "complete_runtime_activation"},
        runtime_surface_source_lock=_source_lock("limited"),
    )
    dumped = dump_runtime_surface_complete_activation_branch(branch)

    assert json.loads(dumped)["comment_text_body_included"] is False
    assert '"comment_text"' not in dumped
    assert _NATURAL_TEXT not in dumped

    unsafe = dict(branch)
    unsafe["comment_text"] = "出してはいけない本文"
    with pytest.raises(ValueError):
        assert_runtime_surface_complete_activation_branch_meta_only(unsafe)


def test_step6_blocked_complete_request_is_not_misclassified_as_complete_initial_source() -> None:
    lock = build_runtime_surface_source_lock(
        trace_id="trace-step6-blocked-source-lock",
        emotion_log_id="emotion-step6-blocked-source-lock",
        observation_status="unavailable",
        backend_comment_text_length=0,
        display_confirmed=False,
        coverage_group="short_daily",
        resolution_meta={
            "requested_composer": "complete_initial",
            "canonical_requested_composer": "complete_composer_initial",
            "resolution_source": "cocolon_complete_composer_initial",
            "connection_status": "blocked_ap0",
            "default_client_used": False,
            "complete_initial_client_used": False,
        },
    )

    assert lock["composer_requested"] == "complete_initial"
    assert lock["composer_source"] == "unavailable"
    assert lock["composer_resolved"] == "unavailable"
    assert lock["complete_initial_client_used"] is False

    branch = build_runtime_surface_complete_activation_branch(
        runtime_surface_quality_branch={"target_layer": "complete_runtime_activation"},
        runtime_surface_source_lock=lock,
        composer_client_resolution={
            "requested_composer": "complete_initial",
            "canonical_requested_composer": "complete_composer_initial",
            "connection_status": "blocked_ap0",
            "complete_initial_client_used": False,
        },
        complete_initial_entry_ap0_decision={"phase": "complete_initial_entry_ap0", "green": False},
        release_meta={"release_allowed": True, "rollout_allowed": True},
    )

    assert branch["activation_status"] == "blocked_ap0"
    assert branch["complete_initial_resolution_safe_to_measure"] is False
    assert branch["surface_repair_deferred_until_complete_runtime_measurable"] is True
    assert branch["surface_text_repaired_by_step6"] is False
