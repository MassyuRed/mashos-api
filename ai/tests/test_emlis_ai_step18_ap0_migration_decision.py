from __future__ import annotations

import pytest

from emlis_ai_ap0_migration_decision_service import (
    STEP18_DECISION_PROCEED,
    STEP18_DECISION_RETURN,
    STEP18_REQUIRED_COVERAGE_GROUPS,
    STEP18_REQUIRED_INPUT_AREAS,
    STEP18_VERSION,
    build_step18_ap0_migration_decision,
)
from emlis_ai_rollout_metrics_service import aggregate_emlis_rollout_metrics, build_emlis_rollout_metric_event
from fixtures.emlis_ai_step17_broad_input_cases import (
    STEP17_BROAD_DAILY_INPUT_CASES,
    STEP17_CONTEXT_SCOPE_CASES,
    STEP17_FIXTURE_VERSION,
    STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS,
    STEP17_LONG_MEANING_ARC_CASE,
)


def _diagnostic_summary(**extra):
    summary = {
        "version": "emlis.diagnostic_summary.v1",
        "observation_status": "passed",
        "stage": "display",
        "primary_reason": "passed",
        "secondary_reasons": [],
        "feature_flag_enabled": True,
        "rollout_stage": "limited_cases",
        "rollout_attempted": True,
        "scope_status": "eligible",
        "coverage_scope": "partial_observation",
        "composer_model": "cocolon_limited_composer.v1",
        "composer_status": "generated",
        "comment_text_allowed": True,
        "coverage_groups": list(STEP18_REQUIRED_COVERAGE_GROUPS),
        "coverage_primary_group": "energy_fatigue",
        "coverage_unclassified_reasons": [],
        "coverage_unmapped_reasons": [],
        "coverage_matrix": {
            "version": "emlis.coverage_matrix.v1",
            "coverage_groups": list(STEP18_REQUIRED_COVERAGE_GROUPS),
            "primary_coverage_group": "energy_fatigue",
            "unclassified_reasons": [],
            "unmapped_reason_codes": [],
            "next_steps": [],
        },
        "default_composer_resolution": {
            "default_client_resolved": True,
            "default_client_used": True,
            "default_connection_active": True,
            "resolved_client_class": "CocolonLimitedComposerClient",
            "composer_model": "cocolon_limited_composer.v1",
        },
        "registry_resolution": {
            "default_client_resolved": True,
            "composer_attempted": True,
            "connection_status": "default_limited_composer_connected",
        },
        "release_decision": {
            "stage": "limited_cases",
            "enabled": True,
            "attempted": True,
            "cohort": "limited_case",
            "reason_code": "scope_limited_case_allowed",
        },
        "normal_connection": {
            "ready": True,
            "attempted": True,
            "composer_model": "cocolon_limited_composer.v1",
        },
    }
    summary.update(extra)
    return summary


def _event(status: str, reason: str, coverage_group: str, *, attempted: bool = True):
    return build_emlis_rollout_metric_event(
        release_meta={
            "version": "emlis.limited_composer_release.v1",
            "stage": "limited_cases",
            "enabled": attempted,
            "attempted": attempted,
            "cohort": "limited_case" if attempted else "blocked",
            "reason_code": "scope_limited_case_allowed" if attempted else "feature_flag_disabled",
            "rejection_reasons": [] if reason == "passed" else [reason],
        },
        phase7_rollout_metrics={
            "version": "emlis.phase7_rollout_metrics.v1",
            "attempted": attempted,
            "observation_status": status,
            "stage": "limited_cases",
        },
        diagnostic_summary={
            **_diagnostic_summary(
                observation_status=status,
                stage="display" if status == "passed" else "composer",
                primary_reason=reason,
                secondary_reasons=[] if reason == "passed" else [reason],
                coverage_primary_group=coverage_group,
                coverage_groups=[coverage_group],
                composer_model="cocolon_limited_composer.v1" if attempted else "not_connected",
                composer_status="generated" if attempted else "not_attempted",
                comment_text_allowed=status == "passed",
            ),
        },
    )


def _rollout_metrics(*events):
    aggregate = aggregate_emlis_rollout_metrics(events)
    return {
        "version": "emlis.step16_rollout_metrics.v1",
        "phase": "B-R1",
        "step": "Step16_rollout_metrics",
        "ready": True,
        "aggregation_ready": True,
        "record_count": aggregate["record_count"],
        "rollout_stage": "limited_cases",
        "stage": "limited_cases",
        "attempted": aggregate["attempted"] > 0,
        "attempted_count": aggregate["attempted"],
        "primary_reason": "passed",
        "primary_reason_counts": aggregate["primary_reason_counts"],
        "coverage_group": "energy_fatigue",
        "coverage_group_counts": aggregate["coverage_group_counts"],
        "composer_model": "cocolon_limited_composer.v1",
        "composer_model_counts": aggregate["composer_model_counts"],
        "rollout_metrics_aggregate": aggregate,
        "internal_qa_aggregate": aggregate,
    }


def _step17_summary(**extra):
    cases = [*STEP17_BROAD_DAILY_INPUT_CASES, STEP17_LONG_MEANING_ARC_CASE, *STEP17_CONTEXT_SCOPE_CASES]
    input_areas = sorted({case["input_area"] for case in cases})
    coverage_groups = sorted({group for case in cases for group in case.get("required_coverage_groups", [])})
    profiles = sorted({case["expected_profile"] for case in cases} | {"current_input_core"})
    summary = {
        "version": STEP17_FIXTURE_VERSION,
        "input_areas": input_areas,
        "coverage_groups": coverage_groups,
        "required_coverage_groups": list(STEP18_REQUIRED_COVERAGE_GROUPS),
        "used_evidence_span_ids_checked": True,
        "quality_flags_checked": True,
        "forbidden_surface_checked": True,
        "structure_level_expectations": True,
        "exact_sentence_contract": False,
        "expected_comment_text_locked": False,
        "scope_coverage_ready": True,
        "explicit_out_of_scope_reasons_classified": True,
        "profile_coverage": {
            "known_profiles": profiles,
            "known_profile_variants_passed": True,
            "unknown_shallow_path_covered": True,
            "vocabulary_variants_passed": True,
            "phrase_unit_role_coverage_passed": True,
            "sentence_plan_coverage_passed": True,
        },
        "long_input": {
            "long_meaning_arc_grounded": True,
            "multiple_sentences_or_paragraphs_grounded": True,
            "common_core_guards_passed": True,
            "min_sentence_plans": STEP17_LONG_MEANING_ARC_CASE["min_sentence_plans"],
        },
        "history_cross_core": {
            "history_scope_grounded": True,
            "cross_core_scope_grounded": True,
            "history_current_evidence_separated": True,
            "cross_core_current_input_only_grounded": True,
        },
        "surface_variation_without_template": True,
        "raw_evidence_copy_rejected": True,
        "repeated_surface_rejected": True,
        "general_knowledge_completion_rejected": bool(STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS),
        "completion_sentence_templates_added": False,
        "fallback_observation_sentence_added": False,
    }
    summary.update(extra)
    return summary


def _guard_summary():
    return {
        "version": "emlis.step18_guard_summary.v1",
        "fixed_sentence_guard_passed": True,
        "raw_evidence_copy_rejected": True,
        "repeated_surface_rejected": True,
        "overclaim_guard_passed": True,
        "general_knowledge_completion_rejected": True,
        "completion_sentence_templates_added": False,
        "fallback_observation_sentence_added": False,
    }


def _frontend_summary():
    return {
        "version": "emlis.step18_frontend_boundary_summary.v1",
        "passed_only_contract_preserved": True,
        "frontend_modal_only_passed": True,
        "rejected_comment_text_empty": True,
        "safety_blocked_comment_text_empty": True,
    }


def test_step18_ap0_decision_green_when_step01_to_step17_materials_are_ready() -> None:
    records = [
        _event("passed", "passed", "energy_fatigue"),
        _event("rejected", "unsupported_sentence", "gate_quality"),
        _event("unavailable", "default_limited_composer_feature_disabled", "connection_rollout", attempted=False),
        _event("safety_blocked", "safety_boundary", "safety_boundary", attempted=False),
    ]
    metrics = _rollout_metrics(*records)
    summary = _diagnostic_summary()

    decision = build_step18_ap0_migration_decision(
        diagnostic_summary=summary,
        rollout_metrics=metrics,
        coverage_matrix=summary["coverage_matrix"],
        broad_input_fixture_summary=_step17_summary(),
        guard_test_summary=_guard_summary(),
        frontend_boundary_summary=_frontend_summary(),
    )

    assert decision["version"] == STEP18_VERSION
    assert decision["phase"] == "A-P0"
    assert decision["decision"] == STEP18_DECISION_PROCEED
    assert decision["can_proceed_to_a1"] is True
    assert decision["next_step"] == "Step19_a_plan_equivalent_composer"
    assert decision["return_steps"] == []
    assert decision["unmet_checks"] == []
    assert set(STEP18_REQUIRED_INPUT_AREAS).issubset(set(decision["check_results"]["step17_broad_fixtures"]["evidence"]["input_areas"]))
    assert decision["check_results"]["rollout_distribution"]["evidence"]["do_not_promote_from_passed_only"] is True
    assert decision["post_ap0_checks"][0]["status"] == "deferred"
    assert decision["external_ai_used"] is False
    assert decision["fallback_observation_sentence_added"] is False


def test_step18_ap0_decision_returns_to_source_steps_when_unclassified_reason_is_major() -> None:
    record = _event("rejected", "unknown", "unclassified")
    metrics = _rollout_metrics(record)
    aggregate = metrics["rollout_metrics_aggregate"]
    aggregate["unclassified_reason_count"] = 3
    aggregate["coverage_unclassified_reason_count"] = 3
    summary = _diagnostic_summary(
        observation_status="rejected",
        stage="composer",
        primary_reason="unknown",
        coverage_unclassified_reasons=["unknown"],
        coverage_unmapped_reasons=["unknown"],
        comment_text_allowed=False,
    )

    decision = build_step18_ap0_migration_decision(
        diagnostic_summary=summary,
        rollout_metrics=metrics,
        coverage_matrix={"coverage_groups": ["unclassified"], "unclassified_reasons": ["unknown"]},
        broad_input_fixture_summary={"version": STEP17_FIXTURE_VERSION, "input_areas": ["life"], "coverage_groups": ["energy_fatigue"]},
        guard_test_summary={},
        frontend_boundary_summary={"rejected_comment_text_empty": True},
    )

    assert decision["decision"] == STEP18_DECISION_RETURN
    assert decision["can_proceed_to_a1"] is False
    assert "startup_diagnostics" in decision["unmet_checks"]
    assert "step17_broad_fixtures" in decision["unmet_checks"]
    assert "Step01_diagnostic_summary" in decision["return_steps"]
    assert "Step17_broad_input_fixtures" in decision["return_steps"]
    assert decision["comment_text_contract_preserved"] is True


def test_step18_ap0_decision_rejects_passed_only_rollout_distribution() -> None:
    records = [
        _event("passed", "passed", "energy_fatigue"),
        _event("passed", "passed", "relationship"),
    ]
    metrics = _rollout_metrics(*records)
    summary = _diagnostic_summary()

    decision = build_step18_ap0_migration_decision(
        diagnostic_summary=summary,
        rollout_metrics=metrics,
        coverage_matrix=summary["coverage_matrix"],
        broad_input_fixture_summary=_step17_summary(),
        guard_test_summary=_guard_summary(),
        frontend_boundary_summary=_frontend_summary(),
    )

    assert decision["can_proceed_to_a1"] is False
    assert decision["decision"] == STEP18_DECISION_RETURN
    assert "rollout_distribution" in decision["unmet_checks"]
    assert decision["check_results"]["rollout_distribution"]["primary_reason"] == "passed_only_metrics_are_not_enough"
    assert "Step16_rollout_metrics" in decision["return_steps"]


@pytest.mark.asyncio
async def test_step18_runtime_meta_is_attached_without_changing_user_visible_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "limited_cases")

    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step18-runtime-user",
        subscription_tier="free",
        current_input={
            "id": "step18-runtime-input",
            "created_at": "2026-05-15T00:00:00Z",
            "memo": "昨日から疲れが抜けない。今日は少し休みたい。",
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["体調"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    decision = reply.meta["step18_ap0_migration_decision"]
    multi = reply.meta["multi_perspective"]
    diagnostic = reply.meta["diagnostic_summary"]
    phase_gate = multi["phase_gate"]

    assert decision == multi["step18_ap0_migration_decision"]
    assert diagnostic["step18_ap0_migration_decision"] == decision
    assert decision["phase"] == "A-P0"
    assert decision["decision_ready"] is True
    assert decision["can_proceed_to_a1"] is False
    assert "step17_broad_fixtures" in decision["unmet_checks"]
    assert phase_gate["step18_ap0_migration_decision_ready"] is True
    assert phase_gate["step18_ap0_can_proceed_to_a1"] is False
    assert reply.comment_text == "" or reply.meta["observation_status"] == "passed"
