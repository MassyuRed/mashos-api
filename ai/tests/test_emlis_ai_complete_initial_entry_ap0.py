from __future__ import annotations

import json

import pytest

from emlis_ai_ap0_migration_decision_service import (
    COMPLETE_INITIAL_ENTRY_AP0_VERSION,
    build_complete_initial_entry_ap0_decision,
)
from emlis_ai_complete_composer_client import CocolonCompleteComposerClient
from emlis_ai_composer_client_registry import resolve_default_emlis_composer_client


_COMPLETE_INITIAL_ENV = {
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
    "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_initial",
}


def _clear_flags(monkeypatch: pytest.MonkeyPatch) -> None:
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
    ):
        monkeypatch.delenv(name, raising=False)


def _flag_state() -> dict[str, object]:
    return {
        "version": "emlis.default_composer_flag_state.v1",
        "enabled": True,
        "requested_composer": "complete_initial",
        "canonical_requested_composer": "complete_composer_initial",
        "complete_composer_initial_requested": True,
        "complete_initial_client_requested": True,
        "step10_complete_composer_client_requested": True,
    }


def _release_meta(**extra: object) -> dict[str, object]:
    meta = {
        "version": "emlis.limited_composer_release.v1",
        "stage": "limited_cases",
        "enabled": True,
        "rollout_allowed": True,
        "attempted": True,
        "cohort": "limited_case",
        "reason_code": "scope_limited_case_allowed",
        "rejection_reasons": [],
    }
    meta.update(extra)
    return meta


def _contract_meta(**extra: object) -> dict[str, object]:
    meta = {
        "version": "emlis.complete_initial.entry_contract_baseline.v1",
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "complete_meta_overrides_public_observation_status": False,
        "comment_text_contract": "passed_only",
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_used": False,
        "fixed_sentence_template_allowed": False,
        "fallback_observation_sentence_added": False,
        "fixed_observation_sentence_added": False,
        "completion_sentence_templates_added": False,
        "binding_infrastructure_ready": True,
        "safety_requires_block": False,
        "safety_blocked": False,
    }
    meta.update(extra)
    return meta


def _frontend_summary(**extra: object) -> dict[str, object]:
    meta = {
        "version": "emlis.complete_initial.entry_frontend_boundary.v1",
        "passed_only_contract_preserved": True,
        "frontend_modal_only_passed": True,
        "rejected_comment_text_empty": True,
        "unavailable_comment_text_empty": True,
        "safety_blocked_comment_text_empty": True,
    }
    meta.update(extra)
    return meta


def _coverage_seed(**extra: object) -> dict[str, object]:
    meta = {
        "version": "emlis.complete_initial.entry_coverage_seed.v1",
        "coverage_group": "recovery",
        "binding_count": 1,
        "sentence_binding_ready": True,
    }
    meta.update(extra)
    return meta


def _green_decision(**overrides: object) -> dict[str, object]:
    kwargs = {
        "composer_flag_state": _flag_state(),
        "release_meta": _release_meta(),
        "contract_baseline_meta": _contract_meta(),
        "frontend_boundary_summary": _frontend_summary(),
        "coverage_matrix_seed": _coverage_seed(),
    }
    kwargs.update(overrides)
    return build_complete_initial_entry_ap0_decision(**kwargs)


def test_step0_baseline_blocks_complete_initial_when_entry_ap0_is_not_supplied(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)

    client, meta = resolve_default_emlis_composer_client(release_allowed=True)

    assert client is None
    assert meta["connection_status"] == "blocked_ap0"
    assert meta["pre_connection_stop_stage"] == "ap0"
    assert "complete_initial_ap0_not_green" in meta["rejection_reasons"]
    assert meta["default_composer_resolution"]["connection_status"] == "blocked_ap0"


def test_entry_ap0_green_when_contract_rollout_display_and_binding_are_ready() -> None:
    decision = _green_decision()

    assert decision["version"] == COMPLETE_INITIAL_ENTRY_AP0_VERSION
    assert decision["green"] is True
    assert decision["can_proceed_to_a1"] is True
    assert decision["can_proceed_to_complete_initial"] is True
    assert decision["unmet_checks"] == []
    assert decision["release_blockers"] == []
    assert decision["entry_gate_only"] is True
    assert decision["uses_post_generation_display_gate"] is False
    assert decision["display_gate_relaxed"] is False
    assert decision["comment_text_contract"] == "passed_only"
    assert decision["raw_input_included"] is False
    assert decision["complete_composer_initial_ap0_report"]["green"] is True


def test_entry_ap0_red_when_rollout_is_not_allowed() -> None:
    decision = _green_decision(
        release_meta=_release_meta(
            enabled=False,
            rollout_allowed=False,
            attempted=False,
            cohort="blocked_scope",
            reason_code="scope_limited_case_not_eligible",
        )
    )

    assert decision["green"] is False
    assert "rollout_allowed" in decision["unmet_checks"]
    assert any(item["check_key"] == "rollout_allowed" for item in decision["release_blockers"])
    assert decision["complete_composer_initial_ap0_report"]["green"] is False


def test_entry_ap0_red_when_passed_only_display_boundary_is_not_confirmed() -> None:
    decision = _green_decision(
        frontend_boundary_summary=_frontend_summary(
            passed_only_contract_preserved=False,
            frontend_modal_only_passed=False,
            rejected_comment_text_empty=False,
            unavailable_comment_text_empty=False,
            safety_blocked_comment_text_empty=False,
        ),
        contract_baseline_meta=_contract_meta(comment_text_contract=""),
    )

    assert decision["green"] is False
    assert "passed_only_display_boundary" in decision["unmet_checks"]
    assert decision["comment_text_contract_preserved"] is False


def test_entry_ap0_redacts_and_blocks_source_material_keys() -> None:
    decision = _green_decision(
        contract_baseline_meta=_contract_meta(
            current_input={"memo": "これは診断metaへ入れてはいけない本文です"},
        )
    )

    serialized = json.dumps(decision, ensure_ascii=False, sort_keys=True)
    assert decision["green"] is False
    assert "source_material_not_embedded" in decision["unmet_checks"]
    assert "これは診断metaへ入れてはいけない本文です" not in serialized
    assert "current_input" not in serialized
    assert "memo" not in serialized
    assert decision["raw_input_included"] is False


def test_entry_ap0_decision_can_open_existing_registry_when_rollout_is_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)
    decision = _green_decision()

    client, meta = resolve_default_emlis_composer_client(
        release_allowed=True,
        release_meta=_release_meta(),
        ap0_decision=decision,
    )

    assert isinstance(client, CocolonCompleteComposerClient)
    assert meta["connection_status"] == "default_client_resolved"
    assert meta["source"] == "cocolon_complete_composer_initial"
    assert meta["complete_initial_client_used"] is True
    assert meta["ap0_decision_report"]["green"] is True
