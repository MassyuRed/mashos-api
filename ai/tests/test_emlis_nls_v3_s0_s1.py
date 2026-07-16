# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent Step 0/1 contracts for Natural Language Surface v3."""

import ast
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import re

from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_grounded_sentence_surface import split_two_stage_surface
from helpers.emlis_nls_v3_s0_s1_baseline import (
    DESIGN_SHA256,
    EMOTION_TYPES,
    CATEGORY_TYPES,
    OBSERVATION_STAGES,
    RUNTIME_STATES,
    S0_PATH,
    S0_SCHEMA_VERSION,
    S1_INPUT_PATH,
    S1_INPUT_SCHEMA_VERSION,
    S1_RECEIPT_PATH,
    S1_RECEIPT_SCHEMA_VERSION,
    S1_VISIBLE_PATH,
    S1_VISIBLE_SCHEMA_VERSION,
    V2_SOURCE_PATHS,
    build_source_resource_bound_policy,
    dependency_closure,
    discover_v2_immutable_manifest,
    hmac_commit_json,
    hmac_commit_text,
    load_baseline_cases,
    load_json,
    obligation_inventory_upper_bound,
    sha256_file,
    source_owner_snapshot,
    validate_input_contract,
    validate_obligation_inventory_count,
    validate_source_resource_counts,
    validate_step0,
    validate_step1,
)


_AI_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FROZEN_ARTIFACT_SHA256 = {
    "step0": "57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024",
    "input_contract": "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6",
    "visible": "ba7e1f3d11bd7cd156da80dc6594e889b10e57b123df2e6b9c80e4345f47286d",
    "step1_receipt": "669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518",
}


def _import_targets(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            targets.add(node.module)
    return targets


def _function_source(path: Path, function_name: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"function not found: {function_name}")


def test_step0_freezes_live_design_identity_owner_and_v2_immutable_boundary() -> None:
    step0 = load_json(S0_PATH)
    live_v2, live_v2_hash = discover_v2_immutable_manifest()
    live_owners, live_owner_hash = source_owner_snapshot()

    assert validate_step0(step0) == ()
    assert sha256_file(S0_PATH) == _FROZEN_ARTIFACT_SHA256["step0"]
    assert step0["schema_version"] == S0_SCHEMA_VERSION
    assert step0["design"]["sha256"] == DESIGN_SHA256
    assert step0["version_identity"] == {
        "product_name": "Cocolon EmlisAI",
        "feature_name": "Natural Language Surface",
        "candidate_version": "nls_v3",
        "generation_path": "grounded_natural_language_surface_v3",
        "runtime_state": "offline",
        "allowed_runtime_states": list(RUNTIME_STATES),
        "current_observation_stage": "normal_observation",
        "allowed_observation_stages": list(OBSERVATION_STAGES),
        "runtime_connected": False,
        "runtime_owner": False,
    }
    assert step0["current_runtime"]["production_surface_owner"] == (
        "grounded_sentence_surface_canonical_v1"
    )
    assert step0["current_runtime"]["source_owner_files"] == live_owners
    assert step0["current_runtime"]["source_owner_snapshot_sha256"] == live_owner_hash
    assert step0["v2_boundary"]["immutable_files"] == live_v2
    assert step0["v2_boundary"]["immutable_manifest_sha256"] == live_v2_hash
    assert len(live_v2) == 41
    assert set(V2_SOURCE_PATHS) == {
        row["path"] for row in live_v2 if row["role"] == "stopped_source"
    }
    assert step0["next_step_authority"] == "step1_only"
    assert step0["valid_for_runtime_switch"] is False


def test_step0_independent_negative_mutations_are_rejected() -> None:
    source = load_json(S0_PATH)

    mutation = deepcopy(source)
    mutation["design"]["sha256"] = "0" * 64
    assert "design_hash_mismatch" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["version_identity"]["allowed_observation_stages"].append("invented")
    assert "observation_stage_enum_mismatch" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["version_identity"]["runtime_connected"] = True
    assert "runtime_boundary_changed" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["v2_boundary"]["state"] = "offline_repair"
    assert "v2_not_stopped" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["v2_boundary"]["immutable_files"][0]["sha256"] = "f" * 64
    assert "v2_immutable_manifest_drift" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["current_runtime"]["production_surface_owner"] = "nls_v3"
    assert "production_owner_changed" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["unknown_field"] = False
    assert "strict_contract_mismatch" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["unchanged_contracts"]["db_write_paths_changed"] = True
    assert "strict_contract_mismatch" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["evaluation_policy"]["minimum_cycle_count"] = 1
    assert "strict_contract_mismatch" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["received_artifacts"][0]["sha256"] = "1" * 64
    assert "strict_contract_mismatch" in validate_step0(mutation)

    mutation = deepcopy(source)
    mutation["body_free"] = False
    assert "strict_contract_mismatch" in validate_step0(mutation)


def test_step0_step1_remain_runtime_disconnected_after_step3_contract_addition() -> None:
    v3_modules = sorted(_INFERENCE_ROOT.glob("emlis_ai_nls_v3*.py"))
    assert [path.name for path in v3_modules] == [
        "emlis_ai_nls_v3_artifact_contract.py"
    ]
    reply_targets = _import_targets(_INFERENCE_ROOT / "emlis_ai_reply_service.py")
    helper_targets = _import_targets(
        _AI_ROOT / "tests" / "helpers" / "emlis_nls_v3_s0_s1_baseline.py"
    )
    contract_targets = set().union(*(_import_targets(path) for path in v3_modules))
    assert not any(target.startswith("emlis_ai_nls_v3") for target in reply_targets)
    assert not any(target.startswith("emlis_ai_nls_v3") for target in helper_targets)
    assert "emlis_ai_reply_service" not in contract_targets
    for target in reply_targets | helper_targets | contract_targets:
        assert target not in {
            "emlis_ai_grounded_reception_content_plan_v2",
            "emlis_ai_grounded_reception_candidate_plan_v2",
            "emlis_ai_grounded_human_reception_v2",
            "emlis_ai_grounded_reception_candidate_selector_v2",
        }


def test_step1_actual_rn_input_contract_is_closed_and_hash_bound() -> None:
    contract = load_json(S1_INPUT_PATH)
    app = contract["app_reachable"]

    assert validate_input_contract(contract) == ()
    assert sha256_file(S1_INPUT_PATH) == _FROZEN_ARTIFACT_SHA256["input_contract"]
    assert contract["schema_version"] == S1_INPUT_SCHEMA_VERSION
    assert contract["authority"] == "current_rn_production_files"
    assert tuple(app["emotion_types"]) == EMOTION_TYPES
    assert tuple(app["category_types"]) == CATEGORY_TYPES
    assert app["text_requirement"] == "trimmed_memo_or_memo_action_nonempty"
    assert app["emotion_min_count"] == app["category_min_count"] == 1
    assert app["self_insight_exclusive"] is True
    assert app["self_insight_strength"] == "medium"
    assert app["text_length_limit_added_by_nls_v3"] is False
    assert all(_SHA256_RE.fullmatch(row["sha256"]) for row in contract["rn_owner_files"])
    assert contract["step1_input_contract_status"] == "completed"


def test_step1_input_contract_independent_negative_mutations_are_rejected() -> None:
    source = load_json(S1_INPUT_PATH)

    mutation = deepcopy(source)
    mutation["app_reachable"]["emotion_types"].append("未知")
    assert "emotion_options_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["app_reachable"]["category_types"].pop()
    assert "category_options_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["app_reachable"]["self_insight_exclusive"] = False
    assert "self_insight_contract_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["app_reachable"]["category_min_count"] = 0
    assert "submit_condition_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["app_reachable"]["text_length_limit_added_by_nls_v3"] = True
    assert "invented_text_limit" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["backend_compatibility_boundary"][
        "backend_permissiveness_is_app_valid_authority"
    ] = True
    assert "backend_promoted_to_app_authority" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["unknown_field"] = False
    assert "strict_contract_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["rn_owner_files"][0]["sha256"] = "2" * 64
    assert "strict_contract_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["app_reachable"]["category_unique"] = False
    assert "strict_contract_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["supabase_future_intake"]["raw_corpus_repo_allowed"] = True
    assert "strict_contract_mismatch" in validate_input_contract(mutation)

    mutation = deepcopy(source)
    mutation["source_resource_bound_policy"]["candidate_count_limit"] = 11
    assert "strict_contract_mismatch" in validate_input_contract(mutation)


def test_step1_backend_compatibility_gap_is_bound_to_live_source_contract() -> None:
    boundary = load_json(S1_INPUT_PATH)["backend_compatibility_boundary"]
    api_path = _INFERENCE_ROOT / "api_emotion_submit.py"
    service_path = _INFERENCE_ROOT / "emotion_submit_service.py"
    api_source = api_path.read_text(encoding="utf-8")
    service_source = service_path.read_text(encoding="utf-8")
    emotion_normalizer = _function_source(api_path, "_normalize_emotions")
    category_normalizer = _function_source(api_path, "_normalize_categories")
    submission_normalizer = _function_source(service_path, "normalize_submission_payload")

    assert "List[Union[EmotionItem, str]]" in api_source
    assert "if s not in STRENGTH_SCORE" in emotion_normalizer
    assert 's = "medium"' in emotion_normalizer
    assert "normalized.append(NormalizedEmotion(type=t, strength=s))" in emotion_normalizer
    assert "SELF_INSIGHT_EMOTION_TYPE" not in emotion_normalizer
    assert "if invalid:" in category_normalizer
    assert "Invalid category" in category_normalizer
    assert "if value in seen:" in category_normalizer
    assert "seen.add(value)" in category_normalizer
    assert "if not emotions_tags:" in submission_normalizer
    assert "At least one emotion is required" in submission_normalizer
    assert "if not has_memo_input:" in submission_normalizer
    assert "normalized_categories = []" in submission_normalizer
    assert "accepted without category for compatibility" in api_source
    assert "if has_memo_input and not payload.category:" in api_source
    assert "self_insight_mixed" not in service_source

    assert boundary["legacy_string_emotion_accepted"] is True
    assert boundary["unknown_emotion_type_rejected"] is False
    assert boundary["self_insight_mixed_rejected"] is False
    assert boundary["blank_thought_and_action_rejected"] is False
    assert boundary["empty_emotions_rejected"] is True
    assert boundary["unknown_category_rejected"] is True
    assert boundary["duplicate_category_rejected"] is False
    assert boundary["duplicate_category_deduplicated"] is True


def test_step1_source_resource_bounds_are_lossless_dynamic_and_boundary_closed() -> None:
    contract = load_json(S1_INPUT_PATH)
    policy = contract["source_resource_bound_policy"]
    assert policy == build_source_resource_bound_policy()
    assert policy["global_finite_text_character_limit_present"] is False
    assert policy["global_finite_nucleus_limit_derivable"] is False
    assert policy["global_finite_relation_limit_derivable"] is False
    assert policy["fixed_finite_global_limit_must_not_be_invented"] is True
    assert policy["candidate_count_limit"] == 12
    assert policy["candidate_count_is_obligation_inventory_limit"] is False
    assert policy["truncate_source_or_obligation_inventory_at_bound"] is False
    assert policy["overflow_failure_code"] == "OBLIGATION_INVENTORY_OVERFLOW"
    assert policy["required_boundary_tests"] == [
        "bound_minus_one",
        "bound",
        "bound_plus_one",
    ]
    bounds = policy["source_component_bounds"]
    assert bounds["nucleus_count"]["upper_bound_formula"] == "E"
    assert bounds["relation_count"]["upper_bound_formula"] == (
        "min(N * (N - 1), T + 9)"
    )
    assert bounds["unknown_boundary_count"]["upper_bound"] == 11
    assert bounds["unknown_boundary_count"]["app_reachable_upper_bound"] == 7
    assert bounds["safety_policy_count"]["upper_bound"] == 1
    assert bounds["safety_required_boundary_code_count"]["upper_bound"] == 9
    assert bounds["reception_opportunity_count"]["upper_bound"] == 4
    assert policy["per_request_obligation_inventory_upper_bound_formula"] == (
        "(4*N + R + U) * (S + K + 1) * (O + 2)"
    )
    identities = policy["canonical_obligation_identity_policy"]
    assert identities["base_nonstance"]["maximum_formula"] == (
        "B = 4*N + R + U"
    )
    assert identities["bounded_counterposition"]["maximum_formula"] == (
        "C = (S + K) * B"
    )
    assert identities["bounded_counterposition"][
        "per_target_capacity_required"
    ] is True
    assert identities["bound_emlis_reception"]["maximum_formula"] == (
        "Q = (O + 1) * P"
    )
    assert identities["bound_emlis_reception"][
        "default_authority_present_when_O_is_zero"
    ] is True
    assert identities["bound_emlis_reception"][
        "counterposition_capacity_is_not_runtime_reception_target"
    ] is True
    assert identities["base_nonstance"]["nucleus_identity"] == [
        "kind",
        "nucleus_id",
    ]
    assert identities["base_nonstance"]["relation_identity"] == [
        "grounded_relation_preservation",
        "relation_id",
    ]
    assert identities["base_nonstance"]["unknown_identity"] == [
        "unknown_boundary_preservation",
        "unknown_id",
    ]
    assert identities["canonical_merge"]["same_identity_duplicate_allowed"] is False
    assert identities["canonical_merge"]["semantic_information_drop_allowed"] is False
    assert identities["canonical_merge"]["canonical_failure_must_not_truncate"] is True
    assert identities["canonical_merge"][
        "counting_identity_does_not_narrow_source_authority_codes"
    ] is True
    assert identities["canonical_merge"][
        "secondary_source_authorities_must_be_lossless_union"
    ] is True
    assert identities["normal_surface_eligibility"][
        "minimum_base_nonstance_obligation_count"
    ] == 1
    owner_paths = {row["path"] for row in policy["owner_files"]}
    assert {
        "ai/services/ai_inference/api_emotion_submit.py",
        "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
        "ai/services/ai_inference/emlis_ai_perspective_observers.py",
        "ai/services/ai_inference/emlis_ai_observation_integrator_service.py",
        "ai/services/ai_inference/emlis_ai_safety_triage.py",
        "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    } == owner_paths
    assert all(_SHA256_RE.fullmatch(row["sha256"]) for row in policy["owner_files"])
    assert policy["rn_text_limit_owner"]["path"] == (
        "screens/input/InputMemoSection.js"
    )

    at_bound = {
        "evidence_span_count": 20,
        "text_evidence_span_count": 10,
        "nucleus_count": 20,
        "relation_count": 19,
        "unknown_boundary_count": 11,
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": 9,
        "reception_opportunity_count": 4,
    }
    below_bound = dict(at_bound)
    below_bound["unknown_boundary_count"] = 10
    assert validate_source_resource_counts(below_bound) == ()
    assert validate_source_resource_counts(at_bound) == ()
    for key in (
        "nucleus_count",
        "relation_count",
        "unknown_boundary_count",
        "safety_policy_count",
        "safety_required_boundary_code_count",
        "reception_opportunity_count",
    ):
        mutation = dict(at_bound)
        mutation[key] += 1
        assert validate_source_resource_counts(mutation) == (
            "OBLIGATION_INVENTORY_OVERFLOW",
        )
    inventory_bound = obligation_inventory_upper_bound(at_bound)
    assert inventory_bound == 7260
    assert validate_obligation_inventory_count(at_bound, inventory_bound - 1) == ()
    assert validate_obligation_inventory_count(at_bound, inventory_bound) == ()
    assert validate_obligation_inventory_count(at_bound, inventory_bound + 1) == (
        "OBLIGATION_INVENTORY_OVERFLOW",
    )
    assert validate_obligation_inventory_count(at_bound, True) == (
        "obligation_inventory_count_type_invalid",
    )

    zero_opportunity = {
        "evidence_span_count": 1,
        "text_evidence_span_count": 1,
        "nucleus_count": 1,
        "relation_count": 0,
        "unknown_boundary_count": 0,
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": 0,
        "reception_opportunity_count": 0,
    }
    assert obligation_inventory_upper_bound(zero_opportunity) == 16
    assert policy["canonical_obligation_identity_policy"][
        "bound_emlis_reception"
    ]["reception_authority_token_count_formula"] == "O + 1"


def test_step1_receipt_is_body_free_parent_bound_and_measured() -> None:
    receipt = load_json(S1_RECEIPT_PATH)
    visible = load_json(S1_VISIBLE_PATH)

    assert validate_step1(receipt) == ()
    assert sha256_file(S1_VISIBLE_PATH) == _FROZEN_ARTIFACT_SHA256["visible"]
    assert sha256_file(S1_RECEIPT_PATH) == _FROZEN_ARTIFACT_SHA256[
        "step1_receipt"
    ]
    assert receipt["schema_version"] == S1_RECEIPT_SCHEMA_VERSION
    assert visible["schema_version"] == S1_VISIBLE_SCHEMA_VERSION
    assert visible["local_only"] is True
    assert receipt["parent_step0_sha256"] == sha256_file(S0_PATH)
    assert receipt["input_contract_sha256"] == sha256_file(S1_INPUT_PATH)
    assert receipt["visible_artifact_sha256"] == sha256_file(S1_VISIBLE_PATH)
    assert receipt["cohort_case_counts"] == {
        "exact8": 8,
        "rr8_unseen12": 12,
        "i6_probe8": 8,
        "total": 28,
    }
    latency = receipt["aggregate_metrics"]["runtime_latency"]
    assert latency["sample_count"] == 140
    assert latency["min_ms"] <= latency["median_ms"] <= latency["p95_ms"] <= latency["max_ms"]
    assert latency["acceptance_budget_status"] == (
        "not_invented_pending_step15_protocol"
    )
    assert receipt["performance_budget_invented"] is False
    assert receipt["next_step_authority"] == "step2_only"
    assert receipt["valid_for_runtime_switch"] is False

    serialized_receipt = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
    assert visible["commitment_key_hex"] not in serialized_receipt
    for row in visible["cases"]:
        assert row["visible_surface"] not in serialized_receipt
        for text in (row["current_input"]["memo"], row["current_input"]["memo_action"]):
            if text:
                assert text not in serialized_receipt


def test_step1_current_v1_regenerates_all_28_committed_outputs_and_gates() -> None:
    visible = load_json(S1_VISIBLE_PATH)
    receipt = load_json(S1_RECEIPT_PATH)
    key_hex = visible["commitment_key_hex"]
    visible_by_id = {
        (row["cohort"], row["case_id"]): row for row in visible["cases"]
    }
    metrics_by_id = {
        (row["cohort"], row["case_id"]): row for row in receipt["cases"]
    }

    async def verify() -> None:
        for case in load_baseline_cases():
            identity = (case.cohort, case.case_id)
            stored = visible_by_id[identity]
            metrics = metrics_by_id[identity]
            reply = await render_emlis_ai_reply(
                user_id=f"nls-v3-s1-live-{case.cohort}-{case.case_id}",
                subscription_tier="free",
                current_input=dict(case.current_input),
            )
            body = str(reply.comment_text or "").strip()
            observation, reception, issues = split_two_stage_surface(body)
            assert issues == ()
            observation = observation.strip()
            reception = reception.strip()
            assert body == stored["visible_surface"]
            assert observation == stored["observation_section"]
            assert reception == stored["reception_section"]
            assert metrics["input_identity_commitment"] == hmac_commit_json(
                key_hex,
                f"input:{case.cohort}:{case.case_id}",
                dict(case.current_input),
            )
            assert metrics["v1_body_commitment"] == hmac_commit_text(
                key_hex, f"visible:{case.cohort}:{case.case_id}", body
            )
            assert metrics["observation_commitment"] == hmac_commit_text(
                key_hex,
                f"observation:{case.cohort}:{case.case_id}",
                observation,
            )
            assert metrics["reception_commitment"] == hmac_commit_text(
                key_hex,
                f"reception:{case.cohort}:{case.case_id}",
                reception,
            )
            public = build_public_emlis_input_feedback_meta(
                reply.meta,
                comment_text_present=bool(body),
                subscription_tier="free",
            )
            assert should_include_public_input_feedback(body, public)
            assert public["observation_status"] == "passed"
            gate = reply.meta["grounded_observation"]
            assert gate["semantic_quality_gate"] == "passed"
            assert gate["reception_all_gates_passed"] is True
            assert gate["runtime_final_contract_guard"] == "passed"
            assert stored["reception_depth_level"] == gate[
                "reception_depth_level"
            ]
            assert stored["reception_terminal_predicate_families"] == list(
                gate["reception_terminal_predicate_families"]
            )
            assert metrics["reception_depth_level"] == gate[
                "reception_depth_level"
            ]
            assert metrics["reception_terminal_predicate_families"] == list(
                gate["reception_terminal_predicate_families"]
            )
            assert reply.meta["generation_path"] == (
                "grounded_observation_plan_sentence_surface_canonical_v1"
            )

    asyncio.run(verify())


def test_step1_dependency_closure_and_body_leak_mutations_are_rejected() -> None:
    source = load_json(S1_RECEIPT_PATH)
    live_closure, live_hash = dependency_closure()
    assert source["source_dependency_closure"] == live_closure
    assert source["source_dependency_closure_sha256"] == live_hash
    assert len(live_closure) == 17

    mutation = deepcopy(source)
    mutation["source_dependency_closure"][0]["sha256"] = "0" * 64
    assert "source_dependency_closure_drift" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["comment_text"] = "body must not be here"
    assert "body_free_forbidden_key:comment_text" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["aggregate_metrics"]["runtime_latency"]["sample_count"] -= 1
    assert "latency_sample_count_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["surface_payload"] = "body hidden under an unknown key"
    assert "receipt_keyset_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["cases"][0]["gate_status"]["semantic_quality_gate"] = "failed"
    assert "receipt_gate_status_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["known_regression_inventory"].pop()
    assert "known_regression_inventory_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["source_modified_by_step1"] = True
    assert "receipt_fixed_value_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["body_free"] = False
    issues = validate_step1(mutation)
    assert "receipt_fixed_value_mismatch" in issues

    mutation = deepcopy(source)
    mutation["cases"][0]["runtime_latency"]["samples_ms"][0] += 1.0
    assert "receipt_case_latency_invalid" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["cases"][0]["v1_body_commitment"] = "f" * 64
    assert "receipt_commitment_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["aggregate_metrics"]["invented"] = 1
    assert "aggregate_keyset_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["cases"][0]["reception_depth_level"] = "layered"
    assert "receipt_reception_metric_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["cases"][0]["reception_terminal_predicate_families"] = [
        "invented_predicate"
    ]
    assert "receipt_reception_metric_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["aggregate_metrics"] = []
    assert "aggregate_keyset_mismatch" in validate_step1(mutation)

    mutation = deepcopy(source)
    mutation["aggregate_metrics"]["runtime_latency"] = None
    assert "aggregate_latency_keyset_mismatch" in validate_step1(mutation)


def test_step1_known_regressions_and_future_supabase_intake_do_not_fake_progress() -> None:
    receipt = load_json(S1_RECEIPT_PATH)
    contract = load_json(S1_INPUT_PATH)
    inventory = {row["regression_id"]: row for row in receipt["known_regression_inventory"]}

    assert inventory["V1_KNOWN_COMPARISON_28"]["counts_toward_v3_minimum"] is False
    assert inventory["V2_DEVELOPMENT_42"]["classification"] == (
        "known_regression_not_novel_evidence"
    )
    assert inventory["V2_HOLDOUT_A"] == {
        "regression_id": "V2_HOLDOUT_A",
        "classification": "sealed_historical_only_do_not_reopen",
        "status": "stop",
    }
    assert inventory["V2_HOLDOUT_B"]["status"] == "not_evaluated"
    device4 = inventory["V1_KNOWN_DEVICE_REPRESENTATIVE4_20260713"]
    assert device4["classification"] == (
        "known_legacy_ui_unreachable_device_product_failure"
    )
    assert device4["device_baseline_owner"] == (
        "grounded_sentence_surface_canonical_v1"
    )
    assert device4["case_count"] == 4
    assert device4["local_v1_visual_match_count"] == 4
    assert device4["product_pass_count"] == 0
    assert device4["product_failure_count"] == 4
    assert device4["app_reachable_under_current_contract"] is False
    assert device4["counts_toward_v3_minimum"] is False
    assert device4["formal_v2_evaluation_status"] == "not_executed"
    assert device4["input_identity_binding"][
        "raw_unsalted_short_input_sha256_republished"
    ] is False
    assert device4["evidence_limitations"][
        "screenshot_review_is_raw_body_hash_proof"
    ] is False
    assert device4["evidence_limitations"]["v2_runtime_generation_count"] == 0
    assert len(device4["cases"]) == 4
    assert all(row["failure_codes"] for row in device4["cases"])
    rr10 = inventory["R8_RR10_V1_DEVICE_BASELINE"]
    assert rr10["status"] == "not_run"
    assert rr10["distinct_from_historical_device4"] is True
    assert rr10["representative_case_order"] == ["A", "B", "I6-L03", "I6-D02"]
    assert rr10["actual_device_result_included"] is False
    assert rr10["progression_authority"] == "none"
    assert rr10["valid_for_progression"] is False
    assert all(_SHA256_RE.fullmatch(rr10[key]["sha256"]) for key in (
        "readiness",
        "expected_packet",
        "evidence_template",
        "evidence_verifier",
    ))

    intake = contract["supabase_future_intake"]
    assert intake["current_status"] == "not_received_not_blocking"
    assert intake["raw_corpus_repo_allowed"] is False
    assert intake["raw_corpus_public_receipt_allowed"] is False
    assert intake["current_valid_and_legacy_separated"] is True
    assert intake["replaces_karen_generated_1000"] is False
    assert receipt["valid_for_step2"] is True
    assert receipt["valid_for_runtime_switch"] is False
