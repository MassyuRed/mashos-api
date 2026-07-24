# -*- coding: utf-8 -*-
from __future__ import annotations

"""Causal RED for all11 current-step PROVED issuance reconciliation.

This test contract freezes the literal Step 0--10 requirement registry,
dedicated independent-negative sources, accepted-run provenance, independent
verification, and all11 atomicity.  It does not issue a receipt, lock a source
baseline, authorize P2, or execute product output.
"""

import ast
import hashlib
import importlib
import importlib.util
import inspect
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_"
    "PROVED_ISSUANCE_AND_INDEPENDENT_PROOF_SOURCE_CLOSURE_RECONCILIATION_"
    "RED_FREEZE_ONLY"
)
_COCOLON_ENTRY = "232738e728ff35c5d8ae7b19884ac80394cad72a"
_MASHOS_API_ENTRY = "8def65c53df9b50795b52a22b6779e5adc5c4465"
_DESIGN_BLOB = "f074cdd402eb9f160e6f3fbae67527d386e31161"
_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
_CANDIDATE = "nls_v3_rc_0034"
_REGISTRY_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_requirement_registry.v1"
)
_ACCEPTED_RUN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "accepted_test_run_receipt.v1"
)
_ALL11_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "all11_completion_chain.v1"
)
_BASELINE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "source_baseline_event.v1"
)
_EVENT_1 = "SOURCE_BASELINE_LOCKED"
_EVENT_2 = "STEP0_10_PREREQUISITES_PROVED"
_REGISTRY_MODULE = (
    "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3"
)
_REGISTRY_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3.py"
)
_ACCEPTED_RUN_MODULE = (
    "emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3"
)
_ACCEPTED_RUN_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3.py"
)
_CLOSURE_MODULE = (
    "emlis_ai_recovery_epoch001_canonical_current_closure_v3"
)
_CLOSURE_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_canonical_current_closure_v3.py"
)
_RECEIPT_MODULE = (
    "emlis_ai_recovery_epoch001_step_completion_receipt_v3"
)
_RECEIPT_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_step_completion_receipt_v3.py"
)
_VERIFIER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
)
_RUNNER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
)
_ISSUER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_all11_receipt_issue.py"
)
_SEQUENCE_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_sequence_ledger_v3.py"
)
_ATOMIC_PUBLISHER_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch001_atomic_publication_bundle_v3.py"
)
_CURRENT_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
)
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_proved_receipt_contract_red.py"
)
_ACCEPTED_SUCCESS_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_exact134_accepted_success_red.py"
)
_SEQUENCE_PUBLICATION_RED_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_sequence_ledger_publication_red.py"
)
_FUTURE_SOURCE_SURFACE = frozenset(
    {
        _CLOSURE_PATH,
        _RECEIPT_PATH,
        _VERIFIER_PATH,
        _REGISTRY_PATH,
        _ACCEPTED_RUN_PATH,
        _RUNNER_PATH,
        _ISSUER_PATH,
        _SEQUENCE_OWNER_PATH,
        _ATOMIC_PUBLISHER_PATH,
    }
)
_NEGATIVE_SOURCE_PATHS = {
    0: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step00_independent_negative.py"
    ),
    1: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step01_independent_negative.py"
    ),
    2: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step02_independent_negative.py"
    ),
    3: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step03_independent_negative.py"
    ),
    4: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step04_independent_negative.py"
    ),
    5: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step05_independent_negative.py"
    ),
    6: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step06_independent_negative.py"
    ),
    7: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step07_independent_negative.py"
    ),
    8: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step08_independent_negative.py"
    ),
    9: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step09_independent_negative.py"
    ),
    10: (
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
        "step10_independent_negative.py"
    ),
}
_TEST_SURFACE = frozenset(
    {
        _CURRENT_RED_PATH,
        _THIS_PATH,
        _ACCEPTED_SUCCESS_RED_PATH,
        _SEQUENCE_PUBLICATION_RED_PATH,
        *_NEGATIVE_SOURCE_PATHS.values(),
    }
)
_PROTECTED_SHA256 = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
    ): "ec6007f5b35fdcc0ec8a330822e4fe9086884dada2415e8557d7f314e2a65127",
    "ai/services/ai_inference/emlis_ai_reply_service.py": (
        "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a"
    ),
    "ai/services/ai_inference/emlis_ai_step11_cycle_evidence_v3.py": (
        "e9f77f7411b581e96a7035d05aa3a50eb4628cbba37a02b0786a0d35b818d43d"
    ),
    "ai/services/ai_inference/emlis_ai_step9_dependency_manifest_v3.py": (
        "19a21d5853c44130c2c874e8b9c6bbbc0a1fc79591c529fb060e7c1e3cd7742e"
    ),
    "ai/services/ai_inference/emlis_ai_step10_dependency_manifest_v3.py": (
        "3bc1311c264cbbae71e69c643d055575e9b80c58b71d321ff28e744ad0ee090c"
    ),
}


def _literal_nodes(path: str, *names: str) -> tuple[str, ...]:
    return tuple(f"{path}::{name}" for name in names)


_POSITIVE_NODES_BY_STEP = {
    0: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s0_s1.py",
        "test_step0_freezes_live_design_identity_owner_and_v2_immutable_boundary",
        "test_step0_independent_negative_mutations_are_rejected",
        (
            "test_step0_step1_remain_runtime_disconnected_after_"
            "step3_contract_addition"
        ),
    ),
    1: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s0_s1.py",
        "test_step1_actual_rn_input_contract_is_closed_and_hash_bound",
        "test_step1_input_contract_independent_negative_mutations_are_rejected",
        (
            "test_step1_backend_compatibility_gap_is_bound_to_"
            "live_source_contract"
        ),
        (
            "test_step1_source_resource_bounds_are_lossless_dynamic_"
            "and_boundary_closed"
        ),
        "test_step1_receipt_is_body_free_parent_bound_and_measured",
        (
            "test_step1_current_v1_regenerates_all_28_committed_"
            "outputs_and_gates"
        ),
        (
            "test_step1_dependency_closure_and_body_leak_mutations_"
            "are_rejected"
        ),
        (
            "test_step1_known_regressions_and_future_supabase_intake_"
            "do_not_fake_progress"
        ),
    ),
    2: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s2_sample_registry.py",
        "test_step2_app_reachable_positive_and_independent_negative_fixtures",
        (
            "test_step2_sample_schema_cross_fields_and_forbidden_"
            "annotations_are_closed"
        ),
        (
            "test_step2_json_and_jsonl_are_utf8_lf_canonical_and_"
            "adversarially_strict"
        ),
        (
            "test_step2_exact_normalized_near_duplicate_policies_are_"
            "distinct_and_order_stable"
        ),
        (
            "test_step2_identity_commitments_separate_input_case_and_"
            "private_hmac_domains"
        ),
        (
            "test_step2_coverage_matrix_is_complete_recomputed_body_free_"
            "and_strictly_typed"
        ),
        (
            "test_step2_schema_files_are_closed_and_runtime_bound_"
            "without_new_dependency"
        ),
        "test_step2_projection_is_an_explicit_deep_copy_allowlist",
        (
            "test_step2_rn_contract_binding_and_independent_drift_"
            "mutations_are_red"
        ),
        (
            "test_step2_registry_separates_corpora_binds_tests_and_"
            "never_counts_fixture_progress"
        ),
        (
            "test_step2_manifest_binds_actual_files_review_and_"
            "transition_authority"
        ),
        (
            "test_step2_near_candidates_require_explicit_review_before_"
            "validation"
        ),
        "test_step2_previous_step_artifacts_remain_byte_frozen",
    ),
    3: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py",
        "test_s3_hand_authored_valid_bundle_passes_all_owner_validators",
        "test_s3_every_top_level_artifact_field_is_required",
        "test_s3_owner_and_nested_keysets_are_closed",
        "test_s3_invalid_enums_are_rejected_by_each_owner",
        "test_s3_bool_and_integer_types_are_never_coerced",
        (
            "test_s3_adversarial_nested_shapes_fail_closed_without_"
            "exceptions"
        ),
        "test_s3_duplicate_ids_and_references_are_rejected_owner_by_owner",
        "test_s3_each_owner_rejects_one_byte_parent_hash_drift",
        "test_s3_future_stage_requires_resolved_upstream_authority",
        "test_s3_obligation_references_and_bound_reception_are_closed",
        "test_s3_content_discourse_ast_cross_references_are_closed",
        (
            "test_s3_witness_has_no_internal_ids_and_spans_bind_actual_"
            "utf8_bytes"
        ),
        "test_s3_binding_contract_requires_unique_resolved_refs",
        "test_s3_generic_body_retained_metadata_attacks_fail_closed",
        "test_s3_receipt_is_strict_body_free_and_upstream_bound",
        "test_s3_v2_import_guard_detects_static_and_dynamic_probes",
        "test_s3_active_canonical_serializer_is_single_and_deterministic",
        "test_s3_canonical_codec_rejects_ambiguous_or_non_json_input",
        "test_s3_validator_remains_independent_from_future_builders",
        "test_s3_red_attack_catalog_is_complete_body_free_and_step_scoped",
        "test_s3_step0_step2_and_batch001_remain_byte_frozen",
        "test_s3_completion_receipt_binds_implementation_and_next_authority",
    ),
    4: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py",
        "test_s4_known_normal_builds_lossless_machine_safe_alias_inventory",
        (
            "test_s4_batch001_all_100_build_and_validate_without_surface_"
            "or_runtime"
        ),
        "test_s4_is_deterministic_body_free_and_ignores_fixture_cues",
        "test_s4_cross_input_plan_and_resolver_cannot_bind_to_another_input",
        "test_s4_same_shape_input_swap_changes_v3_source_commitments",
        (
            "test_s4_exact_source_replay_rejects_added_deleted_and_"
            "rebound_meaning"
        ),
        "test_s4_alias_and_snapshot_authority_forgery_are_rejected",
        "test_s4_coherently_resigned_snapshot_rebinds_to_original_source",
        "test_s4_restatement_relation_is_typed_and_cannot_inflate_depth",
        (
            "test_s4_restatement_unit_is_losslessly_bound_and_forgery_"
            "is_rejected"
        ),
        "test_s4_pre_question_preserves_all_unknowns_and_hash_boundaries",
        "test_s4_frozen_source_policy_rejects_in_process_artifact_drift",
        "test_s4_refined_context_requires_and_consumes_the_partition_owner",
        "test_s4_source_unavailable_is_label_bounded_and_empty_fails_closed",
        (
            "test_s4_self_denial_keeps_identity_boundary_and_concrete_"
            "action_distinct"
        ),
        "test_s4_separate_safety_owner_is_delegated",
        (
            "test_s4_inventory_bound_is_exact_step1_formula_and_"
            "components_are_strict"
        ),
        "test_s4_cross_role_refined_snapshot_lineage_alias_and_tamper_red",
    ),
    5: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        "test_s5_stage_context_is_explicit_body_free_and_future_authority_bound",
        "test_s5_refined_schema_is_bound_but_stops_without_partition_owner",
        "test_s5_refined_partition_reaches_content_selection_body_free",
        "test_s5_refined_active_role_drop_is_independently_rejected",
        "test_s5_normal_plan_has_exact_required_coverage_and_no_unproven_status",
        (
            "test_s5_batch001_all_100_match_reviewed_depth_and_required_"
            "coverage"
        ),
        "test_s5_depth_uses_typed_meaning_units_not_repetition_or_length",
        (
            "test_s5_self_denial_and_concrete_action_require_layered_"
            "separation"
        ),
        (
            "test_s5_required_meaning_cannot_be_deferred_omitted_or_"
            "relabelled"
        ),
        (
            "test_s5_depth_budget_parent_hash_and_coverage_are_not_"
            "self_declared"
        ),
        (
            "test_s5_revalidates_step4_against_shrink_reid_relabel_and_"
            "downgrade"
        ),
        "test_s5_pre_question_preserves_every_unknown_and_observation",
        (
            "test_s5_source_unavailable_is_limited_to_labels_or_"
            "explicit_unknown"
        ),
        (
            "test_s5_new_modules_are_runtime_disconnected_and_do_not_"
            "read_fixture_cues"
        ),
        "test_s5_cross_role_depth_noninflation_floor_and_effect_scope_red",
    ),
    6: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py",
        "test_s6_batch001_all_100_are_strict_bounded_and_semantically_ordered",
        "test_s6_input_swap_changes_content_derived_signatures",
        "test_s6_recomputes_candidate_set_and_rejects_coherent_mutation",
        "test_s6_has_no_fixture_or_surface_generation_cues",
    ),
    7: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py",
        "test_s7_batch001_all_100_render_canonical_input_bound_bytes",
        "test_s7_all_structural_candidates_render_to_distinct_bytes",
        "test_s7_authority_is_opaque_and_every_visible_field_is_revalidated",
        "test_s7_arbitrary_ast_source_swap_and_relation_reversal_fail_closed",
        "test_s7_catalog_in_place_and_rebind_mutations_are_rejected",
        "test_s7_low_information_fallback_and_reserved_label_anchor_are_safe",
        (
            "test_s7_closed_api_has_no_post_gate_text_or_stopped_module_"
            "dependency"
        ),
    ),
    8: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py",
        "test_s8_v1_release_bytes_remain_frozen_with_v2_side_by_side",
        "test_s8_all_100_inputs_and_596_candidates_parse_and_bind",
        "test_s8_contracts_are_closed_hash_bound_and_semantically_signed",
        "test_s8_generic_body_stale_witness_and_clause_deletion_fail",
        "test_s8_source_swap_authority_forgery_and_toctou_fail",
        "test_s8_relation_unknown_graph_role_and_feature_mutations_fail",
        "test_s8_stage_boundary_and_source_role_are_fail_closed",
        "test_s8_syntax_dependency_drift_and_import_boundaries_fail_closed",
    ),
    9: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py",
        "test_s9_step0_step8_bytes_and_side_by_side_policies_are_frozen",
        "test_s9_decision_contracts_reject_malformed_shapes_fail_closed",
        "test_s9_all_100_inputs_596_candidates_hard_pass_and_select",
        "test_s9_each_of_twenty_gate_rows_has_a_dedicated_negative_path",
        "test_s9_v2_recurrence_attacks_and_result_self_declaration_fail",
        (
            "test_s9_selector_is_lexicographic_permutation_invariant_"
            "and_hard_only"
        ),
        "test_s9_bounded_recovery_rebuild_split_and_minimal_lanes",
        "test_s9_no_valid_candidate_stays_failure_and_never_counts_v1",
        "test_s9_pre_question_source_context_is_not_recovered_or_selected",
        "test_s9_modules_are_runtime_disconnected_and_fixture_cue_free",
    ),
    10: _literal_nodes(
        "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py",
        "test_s10_public_contract_is_unchanged_and_default_owner_is_disabled_v1",
        "test_s10_state_machine_is_fail_closed_and_tester_authority_is_opaque",
        (
            "test_s10_reply_bridge_preserves_selected_canonical_utf8_"
            "bytes_exactly"
        ),
        (
            "test_s10_runtime_execution_recomputes_the_full_parent_chain_"
            "and_frozen_rc"
        ),
        (
            "test_s10_delivery_keeps_v3_success_and_v1_fallback_"
            "boundaries_separate"
        ),
        "test_s10_batch_runner_aborts_infrastructure_and_lineage_failures",
        "test_s10_private_io_rejects_ancestor_symlinks",
        (
            "test_s10_runtime_app_reachable_adapter_matches_frozen_"
            "step2_policy"
        ),
        (
            "test_s10_private_body_full_and_body_free_hmac_evidence_"
            "are_separate"
        ),
        (
            "test_s10_receipt_v3_schema_and_step11_evidence_builders_"
            "are_closed"
        ),
        (
            "test_s10_partial_batch_cannot_claim_formal_completion_"
            "or_acceptance"
        ),
        (
            "test_s10_cumulative_uses_fresh_closure_and_rejects_missing_"
            "or_duplicate_cases"
        ),
        "test_s10_output_diff_is_body_free_and_commitment_based",
        (
            "test_s10_rn_api_db_and_step9_historical_boundaries_"
            "remain_frozen"
        ),
        (
            "test_s10_local_emotion_submit_e2e_preserves_db_and_"
            "public_contract"
        ),
    ),
}

_OWNER_BINDINGS = {
    0: (
        {
            "path": "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "symbol": "build_step0",
            "role": "design_boundary_owner",
        },
    ),
    1: (
        {
            "path": "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "symbol": "validate_step1",
            "role": "baseline_receipt_owner",
        },
    ),
    2: (
        {
            "path": "ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py",
            "symbol": "build_corpus_registry",
            "role": "corpus_registry_owner",
        },
    ),
    3: (
        {
            "path": (
                "ai/services/ai_inference/"
                "emlis_ai_nls_v3_artifact_contract.py"
            ),
            "symbol": "validate_artifact_chain",
            "role": "strict_artifact_contract_owner",
        },
    ),
    4: (
        {
            "path": (
                "ai/services/ai_inference/"
                "emlis_ai_semantic_obligation_inventory_v3.py"
            ),
            "symbol": "build_semantic_obligation_inventory",
            "role": "semantic_obligation_inventory_owner",
        },
    ),
    5: (
        {
            "path": (
                "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
            ),
            "symbol": "build_content_selection_plan",
            "role": "content_selection_owner",
        },
    ),
    6: (
        {
            "path": (
                "ai/services/ai_inference/"
                "emlis_ai_discourse_graph_planner_v3.py"
            ),
            "symbol": "build_discourse_graph_plans",
            "role": "discourse_graph_owner",
        },
    ),
    7: (
        {
            "path": (
                "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py"
            ),
            "symbol": "build_typed_surface_ast",
            "role": "typed_surface_ast_owner",
        },
        {
            "path": (
                "ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py"
            ),
            "symbol": "render_canonical_surface",
            "role": "canonical_renderer_owner",
        },
    ),
    8: (
        {
            "path": (
                "ai/services/ai_inference/"
                "emlis_ai_body_semantic_atom_parser_v3.py"
            ),
            "symbol": "parse_body_semantic_atoms",
            "role": "body_only_parser_owner",
        },
        {
            "path": (
                "ai/services/ai_inference/"
                "emlis_ai_independent_semantic_matcher_v3.py"
            ),
            "symbol": "match_parsed_surface_witness",
            "role": "independent_matcher_owner",
        },
    ),
    9: (
        {
            "path": (
                "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py"
            ),
            "symbol": "validate_semantic_hard_gate_result",
            "role": "hard_gate_owner",
        },
        {
            "path": (
                "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py"
            ),
            "symbol": "select_semantic_candidates",
            "role": "selector_owner",
        },
        {
            "path": (
                "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py"
            ),
            "symbol": "select_with_bounded_recovery",
            "role": "bounded_recovery_owner",
        },
    ),
    10: (
        {
            "path": (
                "ai/services/ai_inference/"
                "emlis_ai_dormant_runtime_adapter_v3.py"
            ),
            "symbol": "execute_dormant_v3",
            "role": "dormant_runtime_owner",
        },
        {
            "path": "ai/tools/emlis_nls_v3_batch_run.py",
            "symbol": "run_batch",
            "role": "batch_runner_owner",
        },
    ),
}
_STRICT_CONTRACT_BINDINGS = {
    0: (
        {
            "contract_id": "STEP0_DESIGN_IDENTITY_AND_V2_BOUNDARY",
            "schema_version": (
                "cocolon.emlis.nls_v3.step0_version_boundary.v1"
            ),
            "validator_path": (
                "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py"
            ),
            "validator_symbol": "validate_step0",
            "invariant_ids": [
                "DESIGN_IDENTITY_FIXED",
                "V2_IMMUTABLE_STOPPED",
                "PUBLIC_BOUNDARY_UNCHANGED",
            ],
        },
    ),
    1: (
        {
            "contract_id": "STEP1_BASELINE_INPUT_AND_RECEIPT_BINDING",
            "schema_version": (
                "cocolon.emlis.nls_v3.step1_baseline_receipt.v1"
            ),
            "validator_path": (
                "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py"
            ),
            "validator_symbol": "validate_step1",
            "invariant_ids": [
                "SOURCE_BASELINE_BOUND",
                "APP_INPUT_CONTRACT_BOUND",
                "MEASURED_NOT_INVENTED",
            ],
        },
    ),
    2: (
        {
            "contract_id": "STEP2_APP_REACHABLE_CORPUS_REGISTRY",
            "schema_version": "cocolon.emlis.nls_v3.corpus_registry.v1",
            "validator_path": (
                "ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py"
            ),
            "validator_symbol": "validate_corpus_registry",
            "invariant_ids": [
                "APP_REACHABLE_ONLY",
                "DUPLICATE_POLICY_CLOSED",
                "ANNOTATION_RUNTIME_DISCONNECTED",
            ],
        },
    ),
    3: (
        {
            "contract_id": "STEP3_STRICT_ARTIFACT_CHAIN",
            "schema_version": (
                "cocolon.emlis.nls_v3.case_evidence_receipt.v2"
            ),
            "validator_path": (
                "ai/services/ai_inference/"
                "emlis_ai_nls_v3_artifact_contract.py"
            ),
            "validator_symbol": "validate_artifact_chain",
            "invariant_ids": [
                "CLOSED_KEYSETS",
                "INDEPENDENT_VALIDATION",
                "BODY_FREE_RECEIPT",
            ],
        },
    ),
    4: (
        {
            "contract_id": "STEP4_LOSSLESS_SEMANTIC_OBLIGATIONS",
            "schema_version": (
                "cocolon.emlis.nls_v3.semantic_obligation_ledger.v1"
            ),
            "validator_path": (
                "ai/services/ai_inference/"
                "emlis_ai_semantic_obligation_inventory_v3.py"
            ),
            "validator_symbol": "validate_semantic_obligation_inventory",
            "invariant_ids": [
                "REQUIRED_MEANING_LOSSLESS",
                "SOURCE_ROLES_DISTINCT",
                "RESOURCE_BOUND_CLOSED",
            ],
        },
    ),
    5: (
        {
            "contract_id": "STEP5_REQUIRED_COVERAGE_STAGE_DEPTH",
            "schema_version": (
                "cocolon.emlis.nls_v3.content_selection_plan.v1"
            ),
            "validator_path": (
                "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
            ),
            "validator_symbol": "validate_content_selection_plan",
            "invariant_ids": [
                "REQUIRED_COVERAGE_COMPLETE",
                "STAGE_SOURCE_POLICY_BOUND",
                "DEPTH_NONINFLATION",
            ],
        },
    ),
    6: (
        {
            "contract_id": "STEP6_CONTENT_DERIVED_DISCOURSE_GRAPH",
            "schema_version": "cocolon.emlis.nls_v3.discourse_plan.v1",
            "validator_path": (
                "ai/services/ai_inference/"
                "emlis_ai_discourse_graph_planner_v3.py"
            ),
            "validator_symbol": "validate_discourse_graph_plan_set",
            "invariant_ids": [
                "CONTENT_DERIVED_SIGNATURE",
                "NO_FAMILY_OR_FIXTURE_CUE",
                "BOUNDED_STRUCTURAL_VARIATION",
            ],
        },
    ),
    7: (
        {
            "contract_id": "STEP7_TYPED_AST_CANONICAL_BYTES",
            "schema_version": "cocolon.emlis.nls_v3.surface_ast.v1",
            "validator_path": (
                "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py"
            ),
            "validator_symbol": "validate_typed_surface_ast",
            "invariant_ids": [
                "CLOSED_TYPED_NODE_UNION",
                "CANONICAL_UTF8_BYTES",
                "NO_POST_GATE_TEXT_REPAIR",
            ],
        },
    ),
    8: (
        {
            "contract_id": "STEP8_BODY_ONLY_INDEPENDENT_BINDING",
            "schema_version": (
                "cocolon.emlis.nls_v3.verified_surface_binding.v2"
            ),
            "validator_path": (
                "ai/services/ai_inference/"
                "emlis_ai_step8_artifact_contract_v3.py"
            ),
            "validator_symbol": "validate_verified_surface_binding_v2",
            "invariant_ids": [
                "BODY_ONLY_PARSE",
                "RENDERER_INDEPENDENT_MATCH",
                "SOURCE_SWAP_REJECTED",
            ],
        },
    ),
    9: (
        {
            "contract_id": "STEP9_HARD_GATE_SELECTOR_BOUNDED_RECOVERY",
            "schema_version": (
                "cocolon.emlis.nls_v3.hard_gate_candidate_decision.v1"
            ),
            "validator_path": (
                "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py"
            ),
            "validator_symbol": "validate_semantic_hard_gate_result",
            "invariant_ids": [
                "HARD_FAILURE_NOT_WEIGHTED",
                "LEXICOGRAPHIC_SELECTION",
                "REQUIRED_MEANING_NOT_DELETED",
            ],
        },
    ),
    10: (
        {
            "contract_id": "STEP10_DORMANT_RUNTIME_SAME_BYTES_EVIDENCE",
            "schema_version": (
                "cocolon.emlis.nls_v3.dormant_runtime_execution.v1"
            ),
            "validator_path": (
                "ai/services/ai_inference/"
                "emlis_ai_dormant_runtime_adapter_v3.py"
            ),
            "validator_symbol": "validate_dormant_runtime_execution",
            "invariant_ids": [
                "PUBLIC_OWNER_REMAINS_V1",
                "RUNNER_USES_RUNTIME_BYTES",
                "PRIVATE_AND_BODY_FREE_EVIDENCE_SEPARATE",
            ],
        },
    ),
}
_POSITIVE_PROOF_NODE_BY_STEP = {
    0: _POSITIVE_NODES_BY_STEP[0][0],
    1: _POSITIVE_NODES_BY_STEP[1][4],
    2: _POSITIVE_NODES_BY_STEP[2][0],
    3: _POSITIVE_NODES_BY_STEP[3][0],
    4: _POSITIVE_NODES_BY_STEP[4][0],
    5: _POSITIVE_NODES_BY_STEP[5][4],
    6: _POSITIVE_NODES_BY_STEP[6][0],
    7: _POSITIVE_NODES_BY_STEP[7][0],
    8: _POSITIVE_NODES_BY_STEP[8][1],
    9: _POSITIVE_NODES_BY_STEP[9][2],
    10: _POSITIVE_NODES_BY_STEP[10][3],
}
_NEGATIVE_PROOF_BY_STEP = {
    0: {
        "source_path": _NEGATIVE_SOURCE_PATHS[0],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[0]}::"
            "test_recovery_epoch001_step00_independent_negative"
        ),
        "validator_path": "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
        "validator_symbol": "validate_step0",
        "attack_id": "EMPTY_STEP0_DESIGN_BOUNDARY",
        "expected_closed_code": "design_hash_mismatch",
    },
    1: {
        "source_path": _NEGATIVE_SOURCE_PATHS[1],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[1]}::"
            "test_recovery_epoch001_step01_independent_negative"
        ),
        "validator_path": "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
        "validator_symbol": "validate_input_contract",
        "attack_id": "EMPTY_STEP1_INPUT_CONTRACT",
        "expected_closed_code": "emotion_options_mismatch",
    },
    2: {
        "source_path": _NEGATIVE_SOURCE_PATHS[2],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[2]}::"
            "test_recovery_epoch001_step02_independent_negative"
        ),
        "validator_path": (
            "ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py"
        ),
        "validator_symbol": "validate_corpus_registry",
        "attack_id": "EMPTY_CORPUS_REGISTRY",
        "expected_closed_code": "corpus_registry:keyset_mismatch",
    },
    3: {
        "source_path": _NEGATIVE_SOURCE_PATHS[3],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[3]}::"
            "test_recovery_epoch001_step03_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py"
        ),
        "validator_symbol": "validate_observation_stage_context",
        "attack_id": "EMPTY_OBSERVATION_STAGE_ARTIFACT",
        "expected_closed_code": "MISSING_FIELD",
    },
    4: {
        "source_path": _NEGATIVE_SOURCE_PATHS[4],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[4]}::"
            "test_recovery_epoch001_step04_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ),
        "validator_symbol": "validate_obligation_inventory_count",
        "attack_id": "BOUND_PLUS_ONE_OBLIGATION_COUNT",
        "expected_closed_code": "OBLIGATION_INVENTORY_OVERFLOW",
    },
    5: {
        "source_path": _NEGATIVE_SOURCE_PATHS[5],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[5]}::"
            "test_recovery_epoch001_step05_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
        ),
        "validator_symbol": "validate_content_selection_policy",
        "attack_id": "INVALID_SEMANTIC_INVENTORY_PARENT",
        "expected_closed_code": "SEMANTIC_INVENTORY_RESULT_TYPE_INVALID",
    },
    6: {
        "source_path": _NEGATIVE_SOURCE_PATHS[6],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[6]}::"
            "test_recovery_epoch001_step06_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/"
            "emlis_ai_discourse_graph_planner_v3.py"
        ),
        "validator_symbol": "validate_discourse_graph_plan_set",
        "attack_id": "INVALID_DISCOURSE_PARENT_CHAIN",
        "expected_closed_code": "DISCOURSE_PARENT_REVALIDATION_FAILED",
    },
    7: {
        "source_path": _NEGATIVE_SOURCE_PATHS[7],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[7]}::"
            "test_recovery_epoch001_step07_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py"
        ),
        "validator_symbol": "validate_typed_surface_ast",
        "attack_id": "INVALID_AST_PARENT_CHAIN",
        "expected_closed_code": "AST_PARENT_REVALIDATION_FAILED",
    },
    8: {
        "source_path": _NEGATIVE_SOURCE_PATHS[8],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[8]}::"
            "test_recovery_epoch001_step08_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/"
            "emlis_ai_body_semantic_atom_parser_v3.py"
        ),
        "validator_symbol": "parse_body_semantic_atoms",
        "attack_id": "NON_UTF8_CANDIDATE_BYTES",
        "expected_closed_code": "CANDIDATE_UTF8_REQUIRED",
    },
    9: {
        "source_path": _NEGATIVE_SOURCE_PATHS[9],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[9]}::"
            "test_recovery_epoch001_step09_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/emlis_ai_step9_artifact_contract_v3.py"
        ),
        "validator_symbol": "validate_hard_gate_result_structure",
        "attack_id": "INVALID_HARD_GATE_RESULT_TYPE",
        "expected_closed_code": "HARD_GATE_RESULT_TYPE_INVALID",
    },
    10: {
        "source_path": _NEGATIVE_SOURCE_PATHS[10],
        "test_node_id": (
            f"{_NEGATIVE_SOURCE_PATHS[10]}::"
            "test_recovery_epoch001_step10_independent_negative"
        ),
        "validator_path": (
            "ai/services/ai_inference/"
            "emlis_ai_dormant_runtime_adapter_v3.py"
        ),
        "validator_symbol": "validate_runtime_owner_state",
        "attack_id": "INVALID_RUNTIME_OWNER_STATE_TYPE",
        "expected_closed_code": "RUNTIME_STATE_TYPE_INVALID",
    },
}
_ARTIFACT_SCHEMA_BY_STEP = {
    0: "cocolon.emlis.nls_v3.step0_version_boundary.v1",
    1: "cocolon.emlis.nls_v3.step1_baseline_receipt.v1",
    2: "cocolon.emlis.nls_v3.corpus_registry.v1",
    3: "cocolon.emlis.nls_v3.case_evidence_receipt.v2",
    4: "cocolon.emlis.nls_v3.semantic_obligation_ledger.v1",
    5: "cocolon.emlis.nls_v3.content_selection_plan.v1",
    6: "cocolon.emlis.nls_v3.discourse_plan.v1",
    7: "cocolon.emlis.nls_v3.surface_ast.v1",
    8: "cocolon.emlis.nls_v3.verified_surface_binding.v2",
    9: "cocolon.emlis.nls_v3.hard_gate_candidate_decision.v1",
    10: "cocolon.emlis.nls_v3.dormant_runtime_execution.v1",
}
_GLOBAL_STOP_CONDITION_IDS = (
    "BACKFILL_FORBIDDEN",
    "CASE_FAMILY_PHRASE_DISPATCH_REQUIRED",
    "GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED",
    "MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE",
    "ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE",
    "PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED",
    "RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS",
    "REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED",
    "SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY",
    "STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED",
)
_STEP_STOP_CONDITION_IDS = {
    0: (
        "DESIGN_IMPLEMENTATION_CONFLICT",
        "V2_MODIFICATION_OR_REOPEN_REQUIRED",
    ),
    1: (
        "SOURCE_SNAPSHOT_MISMATCH",
        "UI_SUBMIT_CONTRACT_UNRESOLVED",
    ),
    2: (
        "TEST_ANNOTATION_RUNTIME_INGRESS",
        "UNREACHABLE_INPUT_ACCEPTED",
    ),
    3: (
        "SELF_DECLARED_BUILDER_VALIDATOR_AUTHORITY",
        "STRICT_SCHEMA_RELAXATION_REQUIRED",
    ),
    4: (
        "ORIGINAL_SUPPLEMENTAL_SOURCE_UNSEPARABLE",
        "SURFACE_POSTHOC_REQUIRED_MEANING",
    ),
    5: (
        "PRE_QUESTION_UNKNOWN_COMPLETION_REQUIRED",
        "SYNONYM_REPETITION_REQUIRED_FOR_DEPTH",
    ),
    6: (
        "FAMILY_FIXED_STRUCTURE_REQUIRED",
        "SYNONYM_CANDIDATE_COUNT_INFLATION",
    ),
    7: (
        "ARBITRARY_TEXT_NODE_REQUIRED",
        "POST_GATE_STRING_REPAIR_REQUIRED",
    ),
    8: ("CANDIDATE_METADATA_REQUIRED_FOR_COVERAGE",),
    9: (
        "HARD_FAILURE_WEIGHTED_SCORE_RESCUE",
        "REQUIRED_OBLIGATION_DELETION_REQUIRED",
    ),
    10: (
        "PUBLIC_API_DB_RN_CHANGE_REQUIRED",
        "V3_ACTIVATION_REQUIRED_FOR_RUNNER",
    ),
}
_NEXT_AUTHORITY_BY_STEP = {
    0: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP1_CURRENT_COMPLETION_PROOF_ONLY"
    ),
    1: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP2_CURRENT_COMPLETION_PROOF_ONLY"
    ),
    2: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP3_CURRENT_COMPLETION_PROOF_ONLY"
    ),
    3: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP4_SEMANTIC_INVENTORY_COMPLETION_VERIFICATION_ONLY"
    ),
    4: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP5_REFINED_CONTENT_SELECTION_COMPLETION_VERIFICATION_ONLY"
    ),
    5: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP6_DISCOURSE_GRAPH_COMPLETION_VERIFICATION_ONLY"
    ),
    6: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP7_TYPED_AST_RENDERER_COMPLETION_VERIFICATION_ONLY"
    ),
    7: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP8_BODY_ONLY_PARSER_MATCHER_COMPLETION_VERIFICATION_ONLY"
    ),
    8: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP9_STANDALONE_SUCCESSOR_COMPLETION_VERIFICATION_ONLY"
    ),
    9: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP10_SINGLE_GRAPH_DORMANT_INTEGRATION_COMPLETION_VERIFICATION_ONLY"
    ),
    10: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
    ),
}
_REGISTRY_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STEP_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ORDER_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_OWNER_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_CONTRACT_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PROOF_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ARTIFACT_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PARENT_OR_SOURCE_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_COMPLETION_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STOP_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NEXT_AUTHORITY_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_LINEAGE_INVALID",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_BODY_FREE_REQUIRED",
        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_HASH_MISMATCH",
    }
)
_ACCEPTED_RUN_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_AUTHORITY_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BASELINE_EVENT_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_SOURCE_COMMIT_OR_TREE_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_COLLECTION_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_EXECUTED_NODE_MISMATCH",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_PARTIAL",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_START_END_DRIFT",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_WORKTREE_NOT_CLEAN",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BODY_FREE_REQUIRED",
        "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_HASH_MISMATCH",
    }
)
_EXPECTED_REGISTRY_SHA256 = (
    "70a75ae561fad0846604d05b1262615be4c4a16b36b332150f8c7dc04ee71728"
)
_EXPECTED_FORMAL_NODE_REGISTRY_SHA256 = (
    "fbe29ce0b819563cb5db2dc79fec8277b32ae0dea5a3a5cba64230ba4a1f73cf"
)

_CLOSURE_RED = "RECOVERY_EPOCH001_RECONCILIATION_CURRENT_CLOSURE_NOT_PROVED"
_REGISTRY_RED = "RECOVERY_EPOCH001_RECONCILIATION_REGISTRY_OWNER_NOT_PROVED"
_ACCEPTED_RUN_RED = (
    "RECOVERY_EPOCH001_RECONCILIATION_ACCEPTED_RUN_OWNER_NOT_PROVED"
)
_RUNNER_RED = "RECOVERY_EPOCH001_RECONCILIATION_PROOF_RUNNER_NOT_PROVED"
_ISSUER_RED = "RECOVERY_EPOCH001_RECONCILIATION_ALL11_ISSUER_NOT_PROVED"
_RECEIPT_RED = "RECOVERY_EPOCH001_RECONCILIATION_RECEIPT_OWNER_NOT_PROVED"
_VERIFIER_RED = (
    "RECOVERY_EPOCH001_RECONCILIATION_INDEPENDENT_VERIFIER_NOT_PROVED"
)
_SEQUENCE_RED = "RECOVERY_EPOCH001_RECONCILIATION_PARENT_SEQUENCE_NOT_PROVED"


_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module_or_red(module_name: str, red_code: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            pytest.fail(red_code, pytrace=False)
        raise


def _tool_module_or_red(path: str, module_name: str, red_code: str) -> ModuleType:
    absolute = _REPO_ROOT / path
    if not absolute.is_file():
        pytest.fail(red_code, pytrace=False)
    spec = importlib.util.spec_from_file_location(module_name, absolute)
    if spec is None or spec.loader is None:
        pytest.fail(red_code, pytrace=False)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _required_attributes(
    module: ModuleType,
    names: frozenset[str],
    red_code: str,
) -> None:
    missing = sorted(name for name in names if not hasattr(module, name))
    if missing:
        pytest.fail(f"{red_code}:{','.join(missing)}", pytrace=False)


def _expected_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for step in range(11):
        positive_node = _POSITIVE_PROOF_NODE_BY_STEP[step]
        positive_path = positive_node.partition("::")[0]
        rows.append(
            {
                "step_number": step,
                "actual_owners": [
                    dict(item) for item in _OWNER_BINDINGS[step]
                ],
                "strict_contracts": [
                    {
                        **item,
                        "invariant_ids": list(item["invariant_ids"]),
                    }
                    for item in _STRICT_CONTRACT_BINDINGS[step]
                ],
                "positive_proof": {
                    "source_path": positive_path,
                    "test_node_id": positive_node,
                },
                "independent_negative_proof": dict(
                    _NEGATIVE_PROOF_BY_STEP[step]
                ),
                "formal_completion_node_ids": [
                    *_POSITIVE_NODES_BY_STEP[step],
                    _NEGATIVE_PROOF_BY_STEP[step]["test_node_id"],
                ],
                "artifact_receipt_schema_version": (
                    _ARTIFACT_SCHEMA_BY_STEP[step]
                ),
                "parent_binding_kind": (
                    "SOURCE_BASELINE_LOCKED_EVENT_1"
                    if step == 0
                    else "PREVIOUS_CURRENT_STEP_PROVED_RECEIPT"
                ),
                "source_binding_kind": (
                    "SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW"
                ),
                "completion_condition_ids": [
                    f"STEP_{step}_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED"
                ],
                "stop_condition_ids": sorted(
                    {
                        *_GLOBAL_STOP_CONDITION_IDS,
                        *_STEP_STOP_CONDITION_IDS[step],
                    }
                ),
                "next_authority": _NEXT_AUTHORITY_BY_STEP[step],
                "lineage": {
                    "kind": "current",
                    "recovery_epoch": 1,
                    "historical_disposition": (
                        "IMMUTABLE_NONCURRENT_EVIDENCE"
                    ),
                    "historical_rewrite": False,
                    "historical_as_current": False,
                    "backfill": False,
                },
            }
        )
    return rows


def _expected_registry_material() -> dict[str, Any]:
    return {
        "schema_version": _REGISTRY_SCHEMA,
        "candidate_version_id": _CANDIDATE,
        "recovery_epoch": 1,
        "red_freeze_authority": _AUTHORITY,
        "detailed_design_sha256": _DESIGN_SHA256,
        "required_sequence_event_1": _EVENT_1,
        "completion_sequence_event_2": _EVENT_2,
        "steps": _expected_rows(),
        "automatic_progression": False,
        "body_free": True,
    }


def _expected_registry() -> dict[str, Any]:
    material = _expected_registry_material()
    return {
        **material,
        "registry_sha256": artifact_sha256(material),
    }


def _formal_node_registry_material() -> dict[str, Any]:
    return {
        "step_nodes": {
            str(step): [
                *_POSITIVE_NODES_BY_STEP[step],
                _NEGATIVE_PROOF_BY_STEP[step]["test_node_id"],
            ]
            for step in range(11)
        }
    }


def test_reconciliation_literal_exact11_and_formal_node_registry_is_frozen() -> None:
    assert _AUTHORITY.endswith("RED_FREEZE_ONLY")
    assert _COCOLON_ENTRY == "232738e728ff35c5d8ae7b19884ac80394cad72a"
    assert _MASHOS_API_ENTRY == "8def65c53df9b50795b52a22b6779e5adc5c4465"
    assert _DESIGN_BLOB == "f074cdd402eb9f160e6f3fbae67527d386e31161"
    assert set(_POSITIVE_NODES_BY_STEP) == set(range(11))
    assert [len(_POSITIVE_NODES_BY_STEP[step]) for step in range(11)] == [
        3,
        8,
        13,
        22,
        18,
        15,
        4,
        7,
        8,
        10,
        15,
    ]
    positive_nodes = [
        node
        for step in range(11)
        for node in _POSITIVE_NODES_BY_STEP[step]
    ]
    negative_nodes = [
        _NEGATIVE_PROOF_BY_STEP[step]["test_node_id"]
        for step in range(11)
    ]
    assert len(positive_nodes) == len(set(positive_nodes)) == 123
    assert len(negative_nodes) == len(set(negative_nodes)) == 11
    assert not (set(positive_nodes) & set(negative_nodes))
    assert len(positive_nodes) + len(negative_nodes) == 134
    assert len(_FUTURE_SOURCE_SURFACE) == 9
    assert len(_TEST_SURFACE) == 15
    assert set(_NEGATIVE_SOURCE_PATHS) == set(range(11))
    assert len(set(_NEGATIVE_SOURCE_PATHS.values())) == 11
    assert not (_FUTURE_SOURCE_SURFACE & _TEST_SURFACE)
    assert not (_FUTURE_SOURCE_SURFACE & set(_PROTECTED_SHA256))
    assert _EXPECTED_REGISTRY_SHA256 == artifact_sha256(
        _expected_registry_material()
    )
    assert _EXPECTED_FORMAL_NODE_REGISTRY_SHA256 == artifact_sha256(
        _formal_node_registry_material()
    )
    rows = _expected_rows()
    assert [row["step_number"] for row in rows] == list(range(11))
    row_keys = {
        "step_number",
        "actual_owners",
        "strict_contracts",
        "positive_proof",
        "independent_negative_proof",
        "formal_completion_node_ids",
        "artifact_receipt_schema_version",
        "parent_binding_kind",
        "source_binding_kind",
        "completion_condition_ids",
        "stop_condition_ids",
        "next_authority",
        "lineage",
    }
    assert all(set(row) == row_keys for row in rows)
    assert rows[0]["parent_binding_kind"] == "SOURCE_BASELINE_LOCKED_EVENT_1"
    assert all(
        row["parent_binding_kind"]
        == "PREVIOUS_CURRENT_STEP_PROVED_RECEIPT"
        for row in rows[1:]
    )
    assert rows[10]["next_authority"].endswith(
        "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
    )

    for path in _TEST_SURFACE | set(_PROTECTED_SHA256):
        assert (_REPO_ROOT / path).is_file(), path
    for path, expected_sha256 in _PROTECTED_SHA256.items():
        assert _sha256(_REPO_ROOT / path) == expected_sha256, path

    nodes_by_path: dict[str, set[str]] = {}
    for node_id in positive_nodes + negative_nodes:
        path, separator, function_name = node_id.partition("::")
        assert separator == "::"
        nodes_by_path.setdefault(path, set()).add(function_name)
    for path, names in nodes_by_path.items():
        tree = ast.parse(
            (_REPO_ROOT / path).read_text(encoding="utf-8"),
            filename=path,
        )
        actual = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        }
        assert names <= actual, path

    for step, path in _NEGATIVE_SOURCE_PATHS.items():
        source = (_REPO_ROOT / path).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=path)
        test_functions = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        ]
        assert test_functions == [
            f"test_recovery_epoch001_step{step:02d}_independent_negative"
        ]
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        assert not any(
            module.startswith("test_emlis_nls_v3_")
            or "independent_negative" in module
            for module in imported_modules
        )
        assert "pytest.fixture" not in source
        assert "pytest.mark.parametrize" not in source
        proof = _NEGATIVE_PROOF_BY_STEP[step]
        assert proof["attack_id"] in source
        assert proof["expected_closed_code"] in source
        assert proof["validator_symbol"] in source
        positive_path = _POSITIVE_PROOF_NODE_BY_STEP[step].partition("::")[0]
        assert proof["source_path"] != positive_path


def test_reconciliation_current_closure_owns_proof_system_or_red() -> None:
    module = _module_or_red(_CLOSURE_MODULE, _CLOSURE_RED)
    closure = module.fresh_recovery_epoch001_canonical_current_closure(
        repo_root=_REPO_ROOT
    )
    file_paths = {
        row["path"]
        for row in closure.get("files", [])
        if type(row) is dict and type(row.get("path")) is str
    }
    completion_view = set(closure.get("views", {}).get("completion_proof", []))
    required = _FUTURE_SOURCE_SURFACE | _TEST_SURFACE
    missing = sorted(required - file_paths)
    if missing or not required <= completion_view:
        pytest.fail(
            f"{_CLOSURE_RED}:{','.join(missing or sorted(required - completion_view))}",
            pytrace=False,
        )
    for step, negative_path in _NEGATIVE_SOURCE_PATHS.items():
        step_view = closure.get("step_views", {}).get(f"step_{step}", [])
        if negative_path not in step_view:
            pytest.fail(f"{_CLOSURE_RED}:step_{step}", pytrace=False)


def test_reconciliation_requirement_registry_owner_is_proved_or_red() -> None:
    module = _module_or_red(_REGISTRY_MODULE, _REGISTRY_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_SCHEMA",
                "RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_NEGATIVE_CODES",
                "RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS",
                "fresh_recovery_epoch001_current_step_requirement_registry",
                "validate_recovery_epoch001_current_step_requirement_registry_shape",
            }
        ),
        _REGISTRY_RED,
    )
    assert module.RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_SCHEMA == (
        _REGISTRY_SCHEMA
    )
    assert frozenset(
        module.RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_NEGATIVE_CODES
    ) == _REGISTRY_NEGATIVE_CODES
    registry = (
        module.fresh_recovery_epoch001_current_step_requirement_registry()
    )
    assert (
        module.validate_recovery_epoch001_current_step_requirement_registry_shape(
            registry,
            repo_root=_REPO_ROOT,
        )
        == ()
    )
    assert registry == _expected_registry()
    assert list(module.RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS) == (
        _expected_rows()
    )
    source = (_REPO_ROOT / _REGISTRY_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=_REGISTRY_PATH)
    forbidden_calls = {"glob", "iglob", "rglob", "discover", "collect"}
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not (called & forbidden_calls)


def test_reconciliation_accepted_run_owner_is_proved_or_red() -> None:
    module = _module_or_red(_ACCEPTED_RUN_MODULE, _ACCEPTED_RUN_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA",
                "RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_NEGATIVE_CODES",
                "build_recovery_epoch001_accepted_test_run_receipt",
                "validate_recovery_epoch001_accepted_test_run_receipt_shape",
            }
        ),
        _ACCEPTED_RUN_RED,
    )
    assert module.RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA == (
        _ACCEPTED_RUN_SCHEMA
    )
    assert frozenset(
        module.RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_NEGATIVE_CODES
    ) == _ACCEPTED_RUN_NEGATIVE_CODES
    builder_parameters = set(
        inspect.signature(
            module.build_recovery_epoch001_accepted_test_run_receipt
        ).parameters
    )
    assert {
        "proof_run",
        "requirement_registry",
        "source_baseline_event",
        "repo_root",
    } <= builder_parameters
    assert "accepted_test_results" not in builder_parameters


def test_reconciliation_proof_runner_contract_is_proved_or_red() -> None:
    module = _tool_module_or_red(
        _RUNNER_PATH,
        "emlis_nls_v3_recovery_epoch001_current_step_proof_run",
        _RUNNER_RED,
    )
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL",
                "RECOVERY_EPOCH001_FORMAL_NODE_COUNT",
                "collect_recovery_epoch001_current_step_proof_nodes",
                "run_recovery_epoch001_current_step_proof",
                "validate_recovery_epoch001_proof_environment",
            }
        ),
        _RUNNER_RED,
    )
    assert module.RECOVERY_EPOCH001_CURRENT_STEP_PROOF_RUN_PROTOCOL == (
        "RECOVERY_EPOCH001_PYTEST_EXACT134_BODY_FREE_V1"
    )
    assert module.RECOVERY_EPOCH001_FORMAL_NODE_COUNT == 134
    assert (
        tuple(module.collect_recovery_epoch001_current_step_proof_nodes())
        == tuple(
            node
            for step in range(11)
            for node in (
                *_POSITIVE_NODES_BY_STEP[step],
                _NEGATIVE_PROOF_BY_STEP[step]["test_node_id"],
            )
        )
    )
    source = (_REPO_ROOT / _RUNNER_PATH).read_text(encoding="utf-8")
    for marker in (
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "collected",
        "deselected",
        "xfailed",
        "xpassed",
        "source_commit",
        "source_tree",
        "run_start",
        "run_end",
    ):
        assert marker in source


def test_reconciliation_all11_issuer_contract_is_proved_or_red() -> None:
    module = _tool_module_or_red(
        _ISSUER_PATH,
        "emlis_nls_v3_recovery_epoch001_all11_receipt_issue",
        _ISSUER_RED,
    )
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA",
                "build_recovery_epoch001_all11_completion_chain",
                "validate_recovery_epoch001_all11_completion_chain",
                "stage_recovery_epoch001_all11_current_step_completion_receipts",
            }
        ),
        _ISSUER_RED,
    )
    assert module.RECOVERY_EPOCH001_ALL11_COMPLETION_CHAIN_SCHEMA == (
        _ALL11_SCHEMA
    )
    source = (_REPO_ROOT / _ISSUER_PATH).read_text(encoding="utf-8")
    for marker in (
        "ALL11_INCOMPLETE",
        "RECEIPT_ORDER_INVALID",
        "PUBLICATION_CONFLICT",
        "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY",
    ):
        assert marker in source


def test_reconciliation_receipt_owner_derives_proved_contract_or_red() -> None:
    module = _module_or_red(_RECEIPT_MODULE, _RECEIPT_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED",
                "build_recovery_epoch001_current_step_completion_receipt",
                "validate_recovery_epoch001_current_step_completion_receipt_shape",
            }
        ),
        _RECEIPT_RED,
    )
    parameters = set(
        inspect.signature(
            module.build_recovery_epoch001_current_step_completion_receipt
        ).parameters
    )
    required = {
        "step_number",
        "requirement_registry",
        "accepted_test_run_receipt",
        "repo_root",
        "previous_receipt",
        "step0_parent_authority",
    }
    caller_authority = {
        "actual_owners",
        "strict_contracts",
        "positive_proof",
        "independent_negative_proof",
        "artifact_receipt",
        "parent_binding",
        "completion_condition",
        "stop_conditions",
        "verdict",
        "accepted_test_results",
    }
    if (
        module.RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED is not True
        or not required <= parameters
        or parameters & caller_authority
    ):
        pytest.fail(_RECEIPT_RED, pytrace=False)


def test_reconciliation_independent_verifier_contract_is_proved_or_red() -> None:
    module = _tool_module_or_red(
        _VERIFIER_PATH,
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify",
        _VERIFIER_RED,
    )
    _required_attributes(
        module,
        frozenset(
            {
                "verify_recovery_epoch001_current_step_requirement_registry",
                "verify_recovery_epoch001_accepted_test_run_receipt",
                "verify_recovery_epoch001_all11_completion_chain",
            }
        ),
        _VERIFIER_RED,
    )
    source = (_REPO_ROOT / _VERIFIER_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=_VERIFIER_PATH)
    imported = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert not {
        _CLOSURE_MODULE,
        _RECEIPT_MODULE,
        _REGISTRY_MODULE,
        _ACCEPTED_RUN_MODULE,
    } & imported


def test_reconciliation_parent_sequence_and_p2_boundary_are_proved_or_red() -> None:
    module = _module_or_red(_ACCEPTED_RUN_MODULE, _SEQUENCE_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_SOURCE_BASELINE_EVENT_SCHEMA",
                "RECOVERY_EPOCH001_SEQUENCE_EVENT_1",
                "RECOVERY_EPOCH001_SEQUENCE_EVENT_1_ORDINAL",
                "RECOVERY_EPOCH001_SEQUENCE_EVENT_2",
                "RECOVERY_EPOCH001_SEQUENCE_EVENT_2_ORDINAL",
                "RECOVERY_EPOCH001_P2_AUTOMATIC_AUTHORIZATION",
            }
        ),
        _SEQUENCE_RED,
    )
    assert module.RECOVERY_EPOCH001_SOURCE_BASELINE_EVENT_SCHEMA == (
        _BASELINE_EVENT_SCHEMA
    )
    assert module.RECOVERY_EPOCH001_SEQUENCE_EVENT_1 == _EVENT_1
    assert module.RECOVERY_EPOCH001_SEQUENCE_EVENT_1_ORDINAL == 1
    assert module.RECOVERY_EPOCH001_SEQUENCE_EVENT_2 == _EVENT_2
    assert module.RECOVERY_EPOCH001_SEQUENCE_EVENT_2_ORDINAL == 2
    assert module.RECOVERY_EPOCH001_P2_AUTOMATIC_AUTHORIZATION is False
    source = (_REPO_ROOT / _ACCEPTED_RUN_PATH).read_text(encoding="utf-8")
    assert 0 <= source.find(_EVENT_1) < source.find(_EVENT_2)
    parameters = set(
        inspect.signature(
            module.build_recovery_epoch001_accepted_test_run_receipt
        ).parameters
    )
    assert "source_baseline_event" in parameters
    assert "baseline_id" not in parameters
