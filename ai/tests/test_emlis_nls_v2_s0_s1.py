# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 0/1 contracts for the model-free Natural Language Surface v2 work."""

import asyncio
from collections import Counter
import json
from pathlib import Path
import re

from helpers.emlis_ai_grounded_human_reception_r6_qa import (
    split_reception_sentences,
)
from helpers.emlis_nls_v2_s1_baseline import (
    S0_FREEZE_PATH,
    S0_SCHEMA_VERSION,
    S1_RECEIPT_PATH,
    S1_RECEIPT_SCHEMA_VERSION,
    S1_VISIBLE_PATH,
    S1_VISIBLE_SCHEMA_VERSION,
    assert_body_free_metadata,
    load_baseline_cases,
    load_json,
    public_backend_snapshot,
    sha256_file,
    sha256_json,
    sha256_text,
    source_snapshot,
)
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_grounded_sentence_surface import split_two_stage_surface


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_QUOTE_RE = re.compile(r"「([^」]+)」|『([^』]+)』")


def _quote_metrics(value: str) -> dict[str, int]:
    spans = [left or right for left, right in _QUOTE_RE.findall(str(value or ""))]
    compact = re.sub(r"\s+", "", str(value or ""))
    quoted_chars = sum(len(item) for item in spans)
    return {
        "span_count": len(spans),
        "quoted_character_count": quoted_chars,
        "section_character_count": len(compact),
        "dependency_basis_points": round(10_000 * quoted_chars / max(1, len(compact))),
    }


def test_step0_freezes_received_design_source_and_current_owner_without_drift() -> None:
    freeze = load_json(S0_FREEZE_PATH)
    live_manifest, live_snapshot_sha256 = source_snapshot()

    assert freeze["schema_version"] == S0_SCHEMA_VERSION
    assert freeze["step0_status"] == "completed"
    assert freeze["current_product_status"] == "repair_required"
    assert freeze["progression_authority"] == "none"
    assert freeze["valid_for_runtime_switch"] is False

    received = {row["role"]: row for row in freeze["received_artifacts"]}
    assert received["backend_source_archive"] == {
        "role": "backend_source_archive",
        "received_ref": "mashos-api(222).zip",
        "design_basis_ref": "mashos-api(221).zip",
        "sha256": "a5efd0e7cd110c9bb95ba543d1c68c1094951b7de160ef9cf91341eb41b5bae1",
        "byte_identical_to_design_basis": True,
    }
    assert received["rn_source_archive"]["byte_identical_to_design_basis"] is True
    assert received["premise_archive"]["byte_identical_to_design_basis"] is True
    assert all(_SHA256_RE.fullmatch(row["sha256"]) for row in received.values())

    frozen_manifest = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in freeze["source_snapshot_files"]
    ]
    assert frozen_manifest == live_manifest
    assert freeze["source_snapshot_sha256"] == live_snapshot_sha256
    assert live_snapshot_sha256 == sha256_json(live_manifest)


def test_step0_freezes_scope_contracts_evaluation_roles_and_holdout_opening() -> None:
    freeze = load_json(S0_FREEZE_PATH)
    roles = freeze["evaluation_artifact_roles"]

    assert roles["exact8"]["holdout"] is False
    assert roles["exact8"]["v2_expected_text"] is False
    assert roles["existing_unseen12"]["holdout"] is False
    assert roles["exact8"]["fixture_sha256"] == sha256_file(
        _TEST_ROOT / "fixtures" / roles["exact8"]["fixture_ref"]
    )
    assert roles["existing_unseen12"]["fixture_sha256"] == sha256_file(
        _TEST_ROOT / "fixtures" / roles["existing_unseen12"]["fixture_ref"]
    )
    assert roles["latest_local_qa_result"]["sha256"] == sha256_file(
        _REPO_ROOT / roles["latest_local_qa_result"]["ref"]
    )
    assert roles["latest_device_readiness_result"]["sha256"] == sha256_file(
        _REPO_ROOT / roles["latest_device_readiness_result"]["ref"]
    )
    assert roles["latest_actual_device_images"] == {
        "design_recorded_archive_ref": "実機確認結果３.zip",
        "directly_reprovided_for_step0": False,
        "role": "design_recorded_product_problem_basis_not_runtime_hash_proof",
        "product_status": "repair_required",
    }

    constraints = freeze["generation_constraints"]
    assert constraints["external_api_used"] is False
    assert constraints["local_llm_used"] is False
    assert constraints["runtime_randomness_allowed"] is False
    assert constraints["v1_production_owner_retained"] is True
    assert constraints["v2_runtime_connected"] is False

    holdout = freeze["holdout_policy"]
    assert holdout["holdout_a_fixture_created"] is False
    assert holdout["holdout_b_fixture_created"] is False
    assert holdout["holdout_a_opened"] is False
    assert holdout["holdout_b_opened"] is False
    assert holdout["holdout_a_first_open_owner"] == "step8_after_v2_freeze"
    assert holdout["holdout_b_first_open_owner"] == "step9_without_code_change"

    assert {
        "emotion_submit_route",
        "api_response_keys",
        "input_feedback_comment_text",
        "input_feedback_observation_status",
        "rn_visibility_predicate",
        "two_stage_visible_order",
        "db_physical_names",
        "db_write_paths",
        "grounding_and_safety",
        "body_free_public_meta",
        "deterministic_runtime",
    } <= set(freeze["unchanged_contracts"])


def test_step0_rn_contract_snapshot_is_hash_bound_and_records_actual_public_paths() -> None:
    contract = load_json(S0_FREEZE_PATH)["public_contract_snapshot"]
    owner_rows = contract["rn_owner_files"]
    assert contract["route"] == "/emotion/submit"
    assert contract["comment_path"] == "input_feedback.comment_text"
    assert contract["status_path"] == "input_feedback.emlis_ai.observation_status"
    assert contract["visibility_predicate"] == "status_passed_and_comment_nonempty"
    assert contract["two_stage_order"] == "observation_then_reception"
    assert contract["rn_owner_snapshot_sha256"] == sha256_json(owner_rows)
    assert all(_SHA256_RE.fullmatch(row["sha256"]) for row in owner_rows)


def test_step1_separates_body_full_visible_artifact_from_body_free_receipt() -> None:
    visible = load_json(S1_VISIBLE_PATH)
    receipt = load_json(S1_RECEIPT_PATH)

    assert visible["schema_version"] == S1_VISIBLE_SCHEMA_VERSION
    assert visible["local_only"] is True
    assert visible["artifact_role"] == "v1_comparison_baseline_not_v2_expected_text"
    assert visible["v2_expected_text"] is False
    assert receipt["schema_version"] == S1_RECEIPT_SCHEMA_VERSION
    assert receipt["body_free_metadata"] is True
    assert receipt["visible_artifact_sha256"] == sha256_file(S1_VISIBLE_PATH)
    assert receipt["visible_artifact_ref"] == (
        "../local_only/emlis_nls_v2_s1_visible_20260713.json"
    )
    assert_body_free_metadata(receipt)

    serialized_receipt = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    for row in visible["cases"]:
        assert row["visible_surface"] not in serialized_receipt
        for source_value in (
            row["current_input"]["memo"],
            row["current_input"]["memo_action"],
        ):
            if source_value:
                assert source_value not in serialized_receipt

    for flag in (
        "raw_input_included",
        "raw_text_included",
        "source_text_included",
        "comment_text_included",
        "surface_body_included",
        "visible_text_included",
        "observation_text_included",
        "reception_text_included",
        "candidate_body_included",
    ):
        assert receipt[flag] is False


def test_step1_cohorts_are_exact8_existing_unseen12_and_existing_i6_probe8() -> None:
    visible = load_json(S1_VISIBLE_PATH)
    receipt = load_json(S1_RECEIPT_PATH)
    live_cases = load_baseline_cases()
    visible_by_identity = {
        (row["cohort"], row["case_id"]): row for row in visible["cases"]
    }

    assert receipt["cohort_case_counts"] == {
        "exact8": 8,
        "existing_unseen12": 12,
        "existing_i6_probe8": 8,
        "total": 28,
    }
    assert receipt["cohort_sources"] == {
        "exact8": {
            "ref": "grounded_human_reception_exact8_v2_20260712.json",
            "sha256": sha256_file(
                _TEST_ROOT
                / "fixtures"
                / "grounded_human_reception_exact8_v2_20260712.json"
            ),
        },
        "existing_unseen12": {
            "ref": "../local_only/grounded_human_reception_rr8_unseen12_20260713.json",
            "sha256": sha256_file(
                _TEST_ROOT
                / "local_only"
                / "grounded_human_reception_rr8_unseen12_20260713.json"
            ),
        },
        "existing_i6_probe8": {
            "ref": "../helpers/emlis_ai_grounded_observation_i6_cases.py",
            "sha256": sha256_file(
                _TEST_ROOT
                / "helpers"
                / "emlis_ai_grounded_observation_i6_cases.py"
            ),
        },
    }
    assert len(live_cases) == len(visible_by_identity) == 28
    assert Counter(case.cohort for case in live_cases) == {
        "exact8": 8,
        "existing_unseen12": 12,
        "existing_i6_probe8": 8,
    }
    assert [
        case.case_id for case in live_cases if case.cohort == "existing_i6_probe8"
    ] == [
        "I6-S01",
        "I6-S02",
        "I6-L01",
        "I6-L02",
        "I6-C02",
        "I6-C03",
        "I6-D01",
        "I6-D03",
    ]

    for case in live_cases:
        row = visible_by_identity[(case.cohort, case.case_id)]
        assert row["current_input"] == dict(case.current_input)
        assert row["current_input_sha256"] == sha256_json(case.current_input)


def test_step1_current_source_regenerates_all_v1_visible_and_section_hashes() -> None:
    visible = load_json(S1_VISIBLE_PATH)
    receipt = load_json(S1_RECEIPT_PATH)
    visible_by_identity = {
        (row["cohort"], row["case_id"]): row for row in visible["cases"]
    }
    metric_by_identity = {
        (row["cohort"], row["case_id"]): row for row in receipt["cases"]
    }

    async def _verify() -> None:
        for case in load_baseline_cases():
            identity = (case.cohort, case.case_id)
            expected = visible_by_identity[identity]
            metrics = metric_by_identity[identity]
            reply = await render_emlis_ai_reply(
                user_id=f"nls-v2-s1-live-{case.case_id}",
                subscription_tier="free",
                current_input=dict(case.current_input),
            )
            current_visible = str(reply.comment_text or "").strip()
            observation, reception, issues = split_two_stage_surface(current_visible)
            assert issues == ()
            observation = observation.strip()
            reception = reception.strip()

            assert current_visible == expected["visible_surface"]
            assert sha256_text(current_visible) == expected["visible_surface_sha256"]
            assert observation == expected["observation_section"]
            assert reception == expected["reception_section"]
            assert sha256_text(observation) == expected["observation_section_sha256"]
            assert sha256_text(reception) == expected["reception_section_sha256"]

            gate = reply.meta["grounded_observation"]
            assert metrics["observation_sentence_count"] == len(
                split_reception_sentences(observation)
            )
            assert metrics["reception_sentence_count"] == len(
                split_reception_sentences(reception)
            )
            assert metrics["observation_quote_dependency"] == _quote_metrics(
                observation
            )
            assert metrics["reception_quote_dependency"] == _quote_metrics(
                reception
            )
            assert metrics["reception_terminal_predicate_families"] == gate[
                "reception_terminal_predicate_families"
            ]
            assert gate["runtime_final_contract_guard"] == "passed"

            public = build_public_emlis_input_feedback_meta(
                reply.meta,
                comment_text_present=bool(current_visible),
                subscription_tier="free",
            )
            assert public["observation_status"] == "passed"
            assert should_include_public_input_feedback(current_visible, public) is True

    asyncio.run(_verify())


def test_step1_receipt_freezes_latency_sentence_quote_predicate_and_public_contract() -> None:
    receipt = load_json(S1_RECEIPT_PATH)
    aggregate = receipt["aggregate_metrics"]
    latency = aggregate["runtime_latency"]

    assert receipt["step1_status"] == "completed"
    assert receipt["current_product_status"] == "repair_required"
    assert receipt["v1_baseline_role"] == "comparison_only_not_v2_expected_text"
    assert receipt["v1_expected_text_for_v2"] is False
    assert receipt["holdout_a_opened"] is False
    assert receipt["holdout_b_opened"] is False
    assert receipt["progression_authority"] == "none"
    assert receipt["valid_for_progression"] is False

    assert latency["measurement_scope"] == (
        "render_emlis_ai_reply_local_process_no_route_db_or_network"
    )
    assert latency["clock"] == "perf_counter_ns"
    assert latency["warmup_runs_per_case"] == 1
    assert latency["samples_per_case"] == 5
    assert latency["sample_count"] == 140
    assert 0 < latency["min_ms"] <= latency["median_ms"] <= latency["p95_ms"]
    assert latency["p95_ms"] <= latency["max_ms"]
    assert latency["acceptance_budget_status"] == "not_fixed_before_step10_shadow"
    assert sum(aggregate["reception_sentence_count_distribution"].values()) == 28
    assert sum(aggregate["visible_sentence_count_distribution"].values()) == 28
    assert aggregate["observation_quote_dependency_basis_points"]["max"] >= 0
    assert aggregate["reception_quote_dependency_basis_points"]["max"] >= 0
    assert sum(
        aggregate["reception_terminal_predicate_family_counts"].values()
    ) >= 28
    assert aggregate["predicate_concentration_limit_status"] == (
        "pending_step2_development42_baseline"
    )

    for row in receipt["cases"]:
        case_latency = row["runtime_latency"]
        assert case_latency["sample_count"] == 5
        assert 0 < case_latency["min_ms"] <= case_latency["median_ms"]
        assert case_latency["median_ms"] <= case_latency["p95_ms"]
        assert case_latency["p95_ms"] <= case_latency["max_ms"]

    live_public_rows, live_public_sha256 = public_backend_snapshot()
    public_contract = receipt["public_contract_snapshot"]
    assert public_contract["backend_owner_files"] == live_public_rows
    assert public_contract["backend_owner_snapshot_sha256"] == live_public_sha256
    assert public_contract["route"] == "/emotion/submit"
    assert public_contract["comment_path"] == "input_feedback.comment_text"
    assert public_contract["status_path"] == (
        "input_feedback.emlis_ai.observation_status"
    )
    assert public_contract["visibility_predicate"] == (
        "status_passed_and_comment_nonempty"
    )
    assert public_contract["api_response_key_changed"] is False
    assert public_contract["rn_visibility_contract_changed"] is False
    assert public_contract["db_write_path_changed"] is False


def test_step1_baseline_keeps_v1_runtime_owner_through_step7_offline_additions() -> None:
    receipt = load_json(S1_RECEIPT_PATH)
    generation = receipt["generation_contract"]
    assert generation == {
        "generation_method": "functional_atom_grounded_realizer",
        "composer_source": "grounded_plan_realizer",
        "generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
        "runtime_owner": "v1",
        "v2_runtime_connected": False,
    }

    inference_root = _AI_ROOT / "services" / "ai_inference"
    content_plan_contract = (
        inference_root / "emlis_ai_grounded_reception_content_plan_v2.py"
    )
    assert content_plan_contract.is_file()
    offline_v2_candidates = (
        "emlis_ai_grounded_human_reception_v2.py",
        "emlis_ai_grounded_reception_candidate_plan_v2.py",
    )
    assert all((inference_root / name).is_file() for name in offline_v2_candidates)

    later_v2_offline_candidates = (
        "emlis_ai_grounded_reception_candidate_selector_v2.py",
    )
    assert all(
        (inference_root / name).is_file()
        for name in later_v2_offline_candidates
    )

    reply_source = (_REPO_ROOT / "ai/services/ai_inference/emlis_ai_reply_service.py").read_text(
        encoding="utf-8"
    )
    assert "from emlis_ai_grounded_observation_plan import" in reply_source
    assert "from emlis_ai_grounded_sentence_surface import" in reply_source
    assert "emlis_ai_grounded_reception_content_plan_v2" not in reply_source
    assert "build_reception_content_plan_v2" not in reply_source
    assert "emlis_ai_grounded_reception_candidate_selector_v2" not in reply_source
    assert "_v2" not in reply_source
