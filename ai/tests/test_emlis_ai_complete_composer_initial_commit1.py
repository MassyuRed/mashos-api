from __future__ import annotations

from emlis_ai_ap0_migration_decision_service import build_step18_ap0_migration_decision
from emlis_ai_complete_composer_initial_meta import (
    COMPLETE_COMPOSER_INITIAL_AP0_REPORT_VERSION,
    build_complete_composer_initial_ap0_decision_report,
    build_complete_composer_initial_term_meta,
)
from emlis_ai_composer_client_registry import default_composer_flag_state, resolve_emlis_ai_composer_client
from emlis_ai_limited_composer_client import CocolonAPlanEquivalentComposerClient
from emlis_ai_complete_composer_client import CocolonCompleteComposerClient


def test_complete_composer_initial_term_meta_preserves_legacy_names_without_physical_rename() -> None:
    meta = build_complete_composer_initial_term_meta()

    assert meta["canonical_composer_term"] == "限定Composer"
    assert meta["target_composer_term"] == "完全Composer初期版"
    assert meta["target_composer_family_term"] == "完全Composer"
    assert meta["target_composer_stage_term"] == "完全Composer初期版"
    assert meta["legacy_alias_readings"]["a_plan_equivalent"] == "完全Composer初期版"
    assert meta["legacy_alias_readings"]["b_plan"] == "限定Composer"
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["visible_title"] == "Emlis の観測"
    assert meta["db_physical_name_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["response_shape_changed"] is False
    assert meta["external_ai_allowed"] is False
    assert meta["local_llm_allowed"] is False
    assert meta["fixed_sentence_template_allowed"] is False


def test_complete_composer_initial_ap0_report_green_is_meta_only_entry_signal() -> None:
    report = build_complete_composer_initial_ap0_decision_report(
        {
            "decision_ready": True,
            "can_proceed_to_a1": True,
            "can_enter_step19": True,
            "decision": "proceed_to_step19_a1",
            "next_step": "Step19_a_plan_equivalent_composer",
            "return_steps": [],
            "unmet_checks": [],
            "green_checks": ["startup_diagnostics", "display_boundary"],
            "check_order": ["startup_diagnostics", "display_boundary"],
            "check_results": {"display_boundary": {"check_key": "display_boundary", "blocking": True, "green": True}},
        }
    )

    assert report["version"] == COMPLETE_COMPOSER_INITIAL_AP0_REPORT_VERSION
    assert report["green"] is True
    assert report["entry_decision"] == "enter_complete_composer_initial_implementation"
    assert report["can_enter_complete_composer_initial"] is True
    assert report["release_blockers"] == []
    assert report["target_composer_stage_term"] == "完全Composer初期版"
    assert report["contract_boundary"]["response_shape_changed"] is False
    assert report["no_external_ai"] is True
    assert report["no_fixed_sentence_template"] is True


def test_complete_composer_initial_ap0_report_red_points_back_to_limited_steps() -> None:
    report = build_complete_composer_initial_ap0_decision_report(
        {
            "decision_ready": True,
            "can_proceed_to_a1": False,
            "can_enter_step19": False,
            "decision": "return_to_b_plan_steps",
            "next_step": "Step17_broad_input_fixtures",
            "return_steps": ["Step17_broad_input_fixtures"],
            "unmet_checks": ["step17_broad_fixtures"],
            "check_results": {
                "step17_broad_fixtures": {
                    "check_key": "step17_broad_fixtures",
                    "blocking": True,
                    "green": False,
                }
            },
        }
    )

    assert report["green"] is False
    assert report["entry_decision"] == "return_to_limited_composer_work"
    assert report["can_enter_complete_composer_initial"] is False
    assert report["return_steps"] == ["Step17_broad_input_fixtures"]
    assert report["release_blockers"][0]["check_key"] == "step17_broad_fixtures"
    assert report["release_blocker_keys"] == ["step17_broad_fixtures"]


def test_step18_decision_attaches_complete_initial_report_additively() -> None:
    decision = build_step18_ap0_migration_decision()

    assert "complete_composer_initial_ap0_report" in decision
    assert "ap0_decision_report" in decision
    assert decision["complete_composer_initial_ap0_report"] == decision["ap0_decision_report"]
    assert decision["composer_term_meta"]["target_composer_stage_term"] == "完全Composer初期版"
    assert decision["target_composer_term"] == "完全Composer初期版"
    assert decision["target_composer_family_term"] == "完全Composer"
    assert decision["target_composer_stage_term"] == "完全Composer初期版"
    assert decision["release_blockers"]
    assert decision["db_physical_name_changed"] is False
    assert decision["api_route_changed"] is False


def test_registry_accepts_complete_initial_alias_without_dropping_a_plan_compatibility() -> None:
    env = {
        "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_composer_initial",
    }
    flag_state = default_composer_flag_state(env)

    assert flag_state["enabled"] is True
    assert flag_state["requested_composer"] == "complete_initial"
    assert flag_state["canonical_requested_composer"] == "complete_composer_initial"
    assert flag_state["complete_composer_initial_requested"] is True
    assert flag_state["step10_complete_composer_client_requested"] is True
    assert flag_state["step19_a_plan_composer_requested"] is False
    assert flag_state["target_composer_stage_term"] == "完全Composer初期版"

    blocked = resolve_emlis_ai_composer_client(env=env, release_allowed=True, release_meta={"stage": "internal", "enabled": True})
    assert blocked.default_client_used is False
    assert "complete_initial_ap0_not_green" in blocked.rejection_reasons

    resolution = resolve_emlis_ai_composer_client(
        env=env,
        release_allowed=True,
        release_meta={"stage": "internal", "enabled": True},
        ap0_decision={"can_proceed_to_a1": True},
    )

    assert resolution.default_client_used is True
    assert isinstance(resolution.composer_client, CocolonCompleteComposerClient)

    legacy_env = {"COCOLON_EMLIS_DEFAULT_COMPOSER": "a_plan_equivalent"}
    legacy = resolve_emlis_ai_composer_client(env=legacy_env, release_allowed=True, release_meta={"stage": "internal", "enabled": True})
    assert legacy.default_client_used is True
    assert isinstance(legacy.composer_client, CocolonAPlanEquivalentComposerClient)
