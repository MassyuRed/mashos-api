# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 2 freeze guards without opening either holdout body."""

import json
from pathlib import Path
import re

from helpers.emlis_nls_v2_s2_development import (
    APP_VALID_CATEGORIES,
    APP_VALID_EMOTIONS,
    DEVELOPMENT_FIXTURE_PATH,
    EVALUATION_FAMILIES,
    load_development_cases,
    sha256_file,
)


_TEST_ROOT = Path(__file__).resolve().parent
_MANIFEST_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v2_s2_corpus_manifest_20260713.json"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "case_id",
        "current_input",
        "memo",
        "memo_action",
        "raw_input",
        "raw_text",
        "source_text",
        "surface_text",
        "candidate_text",
        "expected_text",
    }
)


def _load_manifest() -> dict:
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def _assert_body_free_manifest(value) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            assert key not in _FORBIDDEN_BODY_KEYS
            _assert_body_free_manifest(child)
    elif isinstance(value, list):
        for child in value:
            _assert_body_free_manifest(child)


def test_step2_manifest_freezes_14_families_70_cases_and_three_cohorts() -> None:
    manifest = _load_manifest()
    assert manifest["schema_version"] == (
        "cocolon.emlis.nls_v2.evaluation_corpus_manifest.v1"
    )
    assert manifest["step2_status"] == "completed"
    assert manifest["artifact_role"] == (
        "evaluation_corpus_freeze_not_expected_surface"
    )
    assert manifest["body_free_metadata"] is True
    assert tuple(manifest["family_order"]) == EVALUATION_FAMILIES
    assert manifest["family_count"] == 14
    assert manifest["cases_per_family"] == 5
    assert manifest["total_case_count"] == 70

    cohorts = manifest["cohorts"]
    assert set(cohorts) == {"development", "holdout_a", "holdout_b"}
    assert {
        key: row["case_count"] for key, row in cohorts.items()
    } == {"development": 42, "holdout_a": 14, "holdout_b": 14}
    assert {
        key: row["cases_per_family"] for key, row in cohorts.items()
    } == {"development": 3, "holdout_a": 1, "holdout_b": 1}
    assert sum(row["case_count"] for row in cohorts.values()) == 70


def test_step2_fixture_hashes_are_live_without_importing_holdout_content() -> None:
    manifest = _load_manifest()
    for row in manifest["cohorts"].values():
        fixture_path = (_MANIFEST_PATH.parent / row["fixture_ref"]).resolve()
        assert _SHA256_RE.fullmatch(row["fixture_sha256"])
        assert fixture_path.is_file()
        assert sha256_file(fixture_path) == row["fixture_sha256"]
        assert _SHA256_RE.fullmatch(row["case_identity_sha256"])

    assert (
        (_MANIFEST_PATH.parent / manifest["cohorts"]["development"]["fixture_ref"]).resolve()
        == DEVELOPMENT_FIXTURE_PATH.resolve()
    )
    assert all(
        _SHA256_RE.fullmatch(manifest[key])
        for key in (
            "corpus_identity_sha256",
            "current_input_identity_set_sha256",
            "semantic_contract_set_sha256",
        )
    )


def test_step2_development_fixture_has_only_app_valid_options_and_no_answer_text() -> None:
    cases = load_development_cases()
    assert len(cases) == 42
    assert {case.family for case in cases} == set(EVALUATION_FAMILIES)
    for case in cases:
        assert set(case.current_input["emotions"]) <= APP_VALID_EMOTIONS
        assert set(case.current_input["category"]) <= APP_VALID_CATEGORIES
        assert case.semantic_obligation_codes
        assert case.forbidden_claim_codes
        assert case.min_depth
        assert case.max_depth

    manifest = _load_manifest()
    contract = manifest["case_contract"]
    assert contract["fixed_as_answer"] == []
    assert contract["expected_surface_allowed"] is False
    assert contract["expected_terminal_allowed"] is False
    assert contract["expected_predicate_allowed"] is False
    assert contract["single_expected_sentence_count_allowed"] is False
    assert contract["v1_string_match_required"] is False


def test_step2_holdouts_remain_sealed_from_development_loader_and_step3_tests() -> None:
    manifest = _load_manifest()
    policy = manifest["separation_policy"]
    assert policy == {
        "separate_fixture_per_cohort": True,
        "development_loader_knows_holdout_paths": False,
        "step3_content_planner_uses_development_only": True,
        "holdout_a_first_evaluation_owner": "step8_after_v2_freeze",
        "holdout_b_first_evaluation_owner": (
            "step9_without_code_change_after_holdout_a"
        ),
        "holdout_failure_action": "stop_without_case_specific_repair",
    }
    assert manifest["holdout_a_opened_for_evaluation"] is False
    assert manifest["holdout_b_opened_for_evaluation"] is False
    assert manifest["cohorts"]["holdout_a"]["development_test_import_allowed"] is False
    assert manifest["cohorts"]["holdout_b"]["development_test_import_allowed"] is False

    development_loader_source = (
        _TEST_ROOT / "helpers" / "emlis_nls_v2_s2_development.py"
    ).read_text(encoding="utf-8")
    step3_test_source = (
        _TEST_ROOT / "test_emlis_nls_v2_s3_content_plan.py"
    ).read_text(encoding="utf-8")
    for forbidden_fixture_name in (
        "emlis_nls_v2_s2_holdout_a14_20260713.json",
        "emlis_nls_v2_s2_holdout_b14_20260713.json",
    ):
        assert forbidden_fixture_name not in development_loader_source
        assert forbidden_fixture_name not in step3_test_source


def test_step2_manifest_is_body_free_and_records_completed_freeze_checks() -> None:
    manifest = _load_manifest()
    _assert_body_free_manifest(manifest)
    assert manifest["raw_input_included"] is False
    assert manifest["raw_text_included"] is False
    assert manifest["surface_text_included"] is False
    assert manifest["candidate_text_included"] is False
    assert manifest["expected_text_included"] is False
    assert manifest["freeze_validation"] == {
        "required_field_case_count": 70,
        "app_valid_option_case_count": 70,
        "family_depth_contract_case_count": 70,
        "semantic_obligation_case_count": 70,
        "forbidden_claim_case_count": 70,
        "expected_surface_case_count": 0,
        "duplicate_case_id_count": 0,
        "duplicate_current_input_identity_count": 0,
        "exact8_current_input_identity_overlap_count": 0,
        "families_with_five_distinct_semantic_obligation_sets": 14,
        "same_meaning_expression_swap_used_as_holdout": False,
        "self_denial_observation_boundary_case_count": 5,
        "history_lookup_enabled": False,
    }
