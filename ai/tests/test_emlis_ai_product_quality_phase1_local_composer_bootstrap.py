# -*- coding: utf-8 -*-
from __future__ import annotations

import os

import pytest

from emlis_ai_product_quality_measurement_runner import (
    COMPOSER_FEATURE_DISABLED_REASON,
    COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER,
    LOCAL_PRODUCT_QA_PROFILE,
    LOCAL_PRODUCT_QA_ROLLOUT_STAGE,
    assert_product_quality_measurement_runner_bootstrap_meta_only,
    build_local_product_qa_composer_env,
    dump_local_product_qa_composer_bootstrap,
    resolve_local_product_qa_composer_bootstrap,
)


def test_phase1_local_product_qa_composer_env_is_local_overlay_and_does_not_mutate_process_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", raising=False)
    monkeypatch.delenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", raising=False)
    monkeypatch.delenv("COCOLON_EMLIS_DEFAULT_COMPOSER", raising=False)

    before = dict(os.environ)
    env = build_local_product_qa_composer_env({}, requested_composer="limited", enable_composer=True)

    assert env["COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED"] == "true"
    assert env["COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE"] == LOCAL_PRODUCT_QA_ROLLOUT_STAGE
    assert env["COCOLON_EMLIS_DEFAULT_COMPOSER"] == "limited"
    assert env["COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE"] != "all"
    assert "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED" not in before
    assert "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED" not in os.environ


def test_phase1_local_product_qa_composer_bootstrap_resolves_limited_path_without_release_or_contract_changes() -> None:
    report = resolve_local_product_qa_composer_bootstrap(env={}, requested_composer="limited", enable_composer=True)

    assert report["schema_version"] == "cocolon.emlis.product_quality.measurement_runner.bootstrap.v1"
    assert report["run_profile"] == LOCAL_PRODUCT_QA_PROFILE
    assert report["run_status"] == "ready"
    assert report["measurement_can_continue"] is True
    assert report["composer_generation_path_open"] is True
    assert report["blockers"] == []
    assert report["rollout_stage"] == "internal"
    assert report["rollout_stage_defaulted_to_all"] is False
    assert report["complete_initial_default"] is False

    composer = report["composer_resolution"]
    assert composer["default_limited_enabled"] is True
    assert composer["default_client_used"] is True
    assert composer["resolution_source"] == "cocolon_limited_composer"
    assert composer["composer_model"] == "cocolon_limited_composer.v1"
    assert composer["requested_composer"] == "limited"
    assert composer["complete_initial_client_used"] is False
    assert composer["qa_profile"] == LOCAL_PRODUCT_QA_PROFILE

    assert report["public_contract"] == {
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert report["contract_freeze"]["product_gate_ready"] is False
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False
    assert_product_quality_measurement_runner_bootstrap_meta_only(report)


def test_phase1_local_product_qa_composer_disabled_is_recorded_as_blocker_and_not_success() -> None:
    report = resolve_local_product_qa_composer_bootstrap(env={}, enable_composer=False)

    assert report["run_status"] == "blocked"
    assert report["measurement_can_continue"] is False
    assert report["composer_generation_path_open"] is False
    assert report["composer_generation_path_not_open"] is True
    assert COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER in report["blockers"]
    assert "composer_feature_flag_disabled_for_product_qa" in report["blockers"]

    composer = report["composer_resolution"]
    assert composer["default_limited_enabled"] is False
    assert composer["default_client_used"] is False
    assert composer["resolution_source"] == "none"
    assert COMPOSER_FEATURE_DISABLED_REASON in composer["rejection_reasons"]
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False
    assert_product_quality_measurement_runner_bootstrap_meta_only(report)


def test_phase1_complete_initial_request_is_not_defaulted_and_blocks_without_ap0_green() -> None:
    report = resolve_local_product_qa_composer_bootstrap(
        env={},
        requested_composer="complete_initial",
        enable_composer=True,
    )

    assert report["requested_composer"] == "complete_initial"
    assert report["complete_initial_default"] is False
    assert report["run_status"] == "blocked"
    assert report["measurement_can_continue"] is False
    assert COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER in report["blockers"]
    assert "complete_initial_not_ready_for_product_qa" in report["blockers"]
    assert report["composer_resolution"]["complete_initial_client_used"] is False
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False


def test_phase1_bootstrap_dump_is_meta_only() -> None:
    dumped = dump_local_product_qa_composer_bootstrap(
        resolve_local_product_qa_composer_bootstrap(env={}, enable_composer=False)
    )

    assert "\"comment_text\":" not in dumped
    assert "\"raw_input\":" not in dumped
    assert "\"candidate_body\":" not in dumped
    assert "\"product_gate_ready\":false" in dumped
    assert "\"public_release_applied\":false" in dumped
