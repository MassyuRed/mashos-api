# -*- coding: utf-8 -*-
from __future__ import annotations

"""P11 real-device F/E/G regression handling.

The real-device cases are QA fixtures only.  They must not become runtime routes,
exact body locks, or a reason to allow Gate Recovery material surface text into
public ``comment_text``.  Product quality checks source lineage and forbidden
surface classes instead of exact public body equality.
"""

import json
from pathlib import Path
from typing import Any

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
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
    assert_product_quality_measurement_event_meta_only,
    normalize_product_quality_event,
)
from emlis_ai_product_quality_measurement_runner import (
    assert_product_quality_measurement_run_meta_only,
    dump_product_quality_measurement_run,
    run_product_quality_measurement,
)
from emlis_ai_types import ReplyEnvelope
from fixtures.emlis_ai_real_device_gate_recovery_regression_cases_p11 import (
    P11_FORBIDDEN_PUBLIC_FRAGMENTS,
    P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES,
    P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION,
    assert_p11_real_device_gate_recovery_fixture_meta_only,
    build_p11_real_device_gate_recovery_regression_fixtures,
    build_p11_real_device_product_quality_input_cases,
    get_p11_fixture_by_id,
)

_ALLOWED_COMMENT = (
    "見えたこと：\n"
    "いまは、選ばれた感情と行動の流れを分けて扱う必要がありそうです。\n"
    "Emlisから：\n"
    "急いで意味を決めず、いま扱える範囲から整理します。"
)
_NORMAL_REBUILD_ALLOWED_COMMENT = (
    "この記録では、予定の変化を受けたあと、不安がまだ落ち着ききっていない状態として見えます。"
    "その中で、返事を急がずに置き直したい感じもEmlisは受け取りました。"
)
_LEAK_COMMENT = (
    "見えたこと：\n"
    "今回の入力では、生活に関する記録として、平穏の向きが出ています。\n"
    "関係の動き、行動の向き、時間の動きが一緒に置かれています。\n"
    "Emlisから：\n"
    "原因や結論までは決めず、いま置かれた材料だけで受け取ります。"
)


def _base_public_gate_meta() -> dict[str, Any]:
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "passed",
        "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
        "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
        "diagnostic_summary": {
            "binding_required_count": 1,
            "binding_supported_count": 1,
            "reason_required_count": 1,
            "reason_covered_count": 1,
            "surface_signature_key": "p11_real_device_regression_source_lineage",
        },
    }


def _allowed_renderer(**_: object) -> ReplyEnvelope:
    meta = _base_public_gate_meta()
    meta.update(
        {
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "composer_model": "low_information_observation_composer_recovery",
            "generation_method": "low_information_observation_recovery_after_gate_recovery",
            "surface_origin": {
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
                "composer_model": "low_information_observation_composer_recovery",
                "generation_method": "low_information_observation_recovery_after_gate_recovery",
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "public_display_allowed_by_boundary": True,
                "gate_recovery_material_surface_detected": False,
                "post_final_gate_recovery_material_surface_detected": False,
                "internal_policy_sentence_leak_risk": False,
                "template_meta_false_negative_risk": False,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        }
    )
    return ReplyEnvelope(comment_text=_ALLOWED_COMMENT, meta=meta)


def _normal_rebuild_allowed_renderer(**_: object) -> ReplyEnvelope:
    meta = _base_public_gate_meta()
    meta.update(
        {
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
            "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
            "normal_observation_rebuild_attempted": True,
            "normal_observation_rebuild_applied": True,
            "normal_observation_rebuild_source_kind": (
                CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
            ),
            "reply_service_public_boundary": {
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "public_display_allowed": True,
                "normal_observation_rebuild_attempted": True,
                "normal_observation_rebuild_applied": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "surface_origin": {
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
                "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
                "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
                "public_display_allowed_by_boundary": True,
                "gate_recovery_material_surface_detected": False,
                "post_final_gate_recovery_material_surface_detected": False,
                "internal_policy_sentence_leak_risk": False,
                "template_meta_false_negative_risk": False,
                "normal_observation_rebuild_attempted": True,
                "normal_observation_rebuild_applied": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        }
    )
    return ReplyEnvelope(comment_text=_NORMAL_REBUILD_ALLOWED_COMMENT, meta=meta)


def _leaky_renderer(**kwargs: object) -> ReplyEnvelope:
    current_input = kwargs.get("current_input") if isinstance(kwargs.get("current_input"), dict) else {}
    model = str(current_input.get("p11_observed_surface_model") or GATE_RECOVERY_MATERIAL_SURFACE_MODEL)
    generation_method = str(
        current_input.get("p11_observed_generation_method") or GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
    )
    is_post_final = model == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
    if is_post_final:
        generation_method = POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
    meta = _base_public_gate_meta()
    meta.update(
        {
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
            "composer_model": model,
            "generation_method": generation_method,
            "surface_quality_signature": {
                "surface_template_major": False,
                "template_major": False,
            },
            "surface_origin": {
                "candidate_source_kind": CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
                "composer_model": model,
                "generation_method": generation_method,
                "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
                "public_display_allowed_by_boundary": False,
                "gate_recovery_material_surface_detected": True,
                "post_final_gate_recovery_material_surface_detected": bool(is_post_final),
                "internal_policy_sentence_leak_risk": True,
                "template_meta_false_negative_risk": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
        }
    )
    return ReplyEnvelope(comment_text=_LEAK_COMMENT, meta=meta)


def test_p11_real_device_feg_fixtures_are_meta_only_not_exact_runtime_routes() -> None:
    fixtures = build_p11_real_device_gate_recovery_regression_fixtures()

    assert len(fixtures) == 3
    assert {fixture["real_device_case_label"] for fixture in fixtures} == {"F", "E", "G"}
    for fixture in fixtures:
        assert fixture["schema_version"] == "cocolon.emlis.real_device.gate_recovery_regression_fixture.v1"
        assert fixture["source_revision"] == P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION
        assert fixture["exact_comment_text_required"] is False
        assert fixture["exact_comment_text_locked"] is False
        assert fixture["exact_runtime_condition_allowed"] is False
        assert fixture["case_specific_runtime_branch"] is False
        assert fixture["case_specific_runtime_condition_allowed"] is False
        assert fixture["runtime_branching_uses_fixture_strings"] is False
        assert fixture["fixture_text_used_for_runtime_branching"] is False
        assert CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE not in fixture[
            "expected_allowed_public_candidate_source_kinds"
        ]
        assert set(fixture["expected_allowed_public_candidate_source_kinds"]).issubset(
            set(ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS)
        )
        assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE in fixture[
            "expected_allowed_public_candidate_source_kinds"
        ]
        assert "material_slot_echo_only" in fixture["forbidden_surface_classes"]
        assert "category_emotion_slot_label_listing" in fixture["forbidden_surface_classes"]
        for fragment in P11_FORBIDDEN_PUBLIC_FRAGMENTS:
            assert fragment in fixture["forbidden_public_fragments"]
    assert_p11_real_device_gate_recovery_fixture_meta_only(fixtures)


def test_p11_real_device_feg_gate_recovery_surface_leak_is_blocked_by_source_origin() -> None:
    run = run_product_quality_measurement(
        input_cases=build_p11_real_device_product_quality_input_cases(),
        renderer=_leaky_renderer,
        run_id="p11_real_device_leak_regression",
        created_at="2026-06-05T00:00:00Z",
        env={},
        enable_composer=True,
    )

    assert len(run["measurement_events"]) == 3
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in run["blockers"]
    assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in run["blockers"]
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False
    assert run["surface_origin_summary"]["surface_origin_event_count"] == 3
    assert run["surface_origin_summary"]["gate_recovery_material_surface_event_count"] == 3
    assert run["machine_metrics"]["public_display_reached_via_gate_recovery_material_surface_count"] == 3

    for event in run["measurement_events"]:
        fixture = get_p11_fixture_by_id(event["source"]["source_case_id"])
        assert event["public_display_reached"] is True
        assert event["surface_origin"]["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
        assert event["surface_origin"]["public_surface_role"] == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
        assert event["surface_origin"]["public_display_allowed_by_boundary"] is False
        assert event["surface_origin"]["gate_recovery_material_surface_detected"] is True
        for blocker in fixture.expected_blockers_when_leaked:
            assert blocker in event["blockers"]
        assert BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC in event["blockers"]

    dumped = dump_product_quality_measurement_run(run)
    assert _LEAK_COMMENT not in dumped
    assert "\"comment_text\":" not in dumped
    assert "\"raw_input\":" not in dumped
    assert_product_quality_measurement_run_meta_only(run)


def test_p11_real_device_feg_allowed_sources_are_checked_by_lineage_not_exact_body() -> None:
    events = []
    for index, fixture in enumerate(P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES, start=1):
        reply = _allowed_renderer()
        event = normalize_product_quality_event(
            run_id="p11_real_device_allowed_source_regression",
            row_id=f"p11_allowed_{index}",
            source_type="regression_fixture",
            source_case_id=fixture.fixture_id,
            source_revision=P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION,
            family=fixture.family,
            reply=reply,
            comment_text=reply.comment_text,
            public_meta=reply.meta,
            internal_meta=reply.meta,
            composer_resolution={},
            machine_metrics={},
        )
        events.append(event)

    assert len(events) == 3
    for event in events:
        assert event["public_display_reached"] is True
        assert event["comment_text_present"] is True
        assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in event["blockers"]
        assert BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK not in event["blockers"]
        assert event["surface_origin"]["candidate_source_kind"] in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
        assert event["surface_origin"]["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
        assert event["surface_origin"]["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
        assert event["surface_origin"]["gate_recovery_material_surface_detected"] is False
        assert event["surface_origin"]["post_final_gate_recovery_material_surface_detected"] is False
        assert event["surface_origin"]["internal_policy_sentence_leak_risk"] is False
        assert event["surface_origin"]["template_meta_false_negative_risk"] is False
        assert_product_quality_measurement_event_meta_only(event)
        for fragment in P11_FORBIDDEN_PUBLIC_FRAGMENTS:
            assert fragment not in _ALLOWED_COMMENT

    dumped = json.dumps(events, ensure_ascii=False, sort_keys=True)
    assert _ALLOWED_COMMENT not in dumped
    assert "expected_comment_text" not in dumped
    assert "exact_comment_text" not in dumped
    assert "\"comment_text\":" not in dumped
    assert "\"raw_input\":" not in dumped


def test_p11_real_device_feg_normal_rebuild_allowed_source_is_checked_by_lineage_not_exact_body() -> None:
    events = []
    for index, fixture in enumerate(P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES, start=1):
        reply = _normal_rebuild_allowed_renderer()
        event = normalize_product_quality_event(
            run_id="p11_real_device_normal_rebuild_allowed_source_regression",
            row_id=f"p11_normal_rebuild_allowed_{index}",
            source_type="regression_fixture",
            source_case_id=fixture.fixture_id,
            source_revision=P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_REVISION,
            family=fixture.family,
            reply=reply,
            comment_text=reply.comment_text,
            public_meta=reply.meta,
            internal_meta=reply.meta,
            composer_resolution={},
            machine_metrics={},
        )
        events.append(event)

    assert len(events) == 3
    for event in events:
        assert event["public_display_reached"] is True
        assert event["comment_text_present"] is True
        assert event["blockers"] == []
        assert event["surface_origin"]["candidate_source_kind"] == (
            CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        )
        assert event["surface_origin"]["candidate_source_kind"] in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
        assert event["surface_origin"]["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
        assert event["surface_origin"]["public_display_allowed_by_boundary"] is True
        assert event["surface_origin"]["gate_recovery_material_surface_detected"] is False
        assert event["surface_origin"]["post_final_gate_recovery_material_surface_detected"] is False
        assert event["surface_origin"]["normal_observation_rebuild_attempted"] is True
        assert event["surface_origin"]["normal_observation_rebuild_applied"] is True
        assert event["gate_results"]["normal_observation_rebuild_attempted"] is True
        assert event["gate_results"]["normal_observation_rebuild_applied"] is True
        assert event["surface_origin"]["internal_policy_sentence_leak_risk"] is False
        assert event["surface_origin"]["template_meta_false_negative_risk"] is False
        assert_product_quality_measurement_event_meta_only(event)
        for fragment in P11_FORBIDDEN_PUBLIC_FRAGMENTS:
            assert fragment not in _NORMAL_REBUILD_ALLOWED_COMMENT

    dumped = json.dumps(events, ensure_ascii=False, sort_keys=True)
    assert _NORMAL_REBUILD_ALLOWED_COMMENT not in dumped
    assert "expected_comment_text" not in dumped
    assert "exact_comment_text" not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped


def test_p11_real_device_fixture_ids_do_not_create_runtime_service_branches() -> None:
    service_root = Path(__file__).resolve().parents[1] / "services" / "ai_inference"
    service_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(service_root.glob("emlis_ai_*.py"))
        if path.is_file()
    )

    for fixture in P11_REAL_DEVICE_GATE_RECOVERY_REGRESSION_FIXTURES:
        assert fixture.fixture_id not in service_text
    assert "p11_real_device_case_label" not in service_text
    assert "p11_observed_surface_model" not in service_text
    assert "p11_observed_generation_method" not in service_text

    serialized_fixtures = json.dumps(
        build_p11_real_device_gate_recovery_regression_fixtures(),
        ensure_ascii=False,
        sort_keys=True,
    )
    assert "\"case_specific_runtime_branch\": false" in serialized_fixtures
    assert "runtime_branching_uses_fixture_strings" in serialized_fixtures
