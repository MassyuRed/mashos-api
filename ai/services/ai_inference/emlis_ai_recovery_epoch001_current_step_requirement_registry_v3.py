# -*- coding: utf-8 -*-
from __future__ import annotations

"""Literal Step 0--10 requirement registry for Recovery Epoch 001.

The registry is the sole semantic authority for current-step proof issuance.
It is body-free, immutable by construction, and contains an explicit exact134
formal-node denominator.  It never discovers tests or accepts caller-supplied
owner, contract, proof, STOP, or next-authority maps.
"""

import ast
import copy
from pathlib import Path
import re
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_requirement_registry.v1"
)
RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_NEGATIVE_CODES = frozenset(
    ['RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ARTIFACT_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_BODY_FREE_REQUIRED',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_COMPLETION_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_CONTRACT_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_HASH_MISMATCH',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_LINEAGE_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NEXT_AUTHORITY_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ORDER_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_OWNER_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PARENT_OR_SOURCE_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PROOF_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STEP_INVALID',
 'RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STOP_INVALID']
)
RECOVERY_EPOCH001_CANDIDATE_VERSION_ID = "nls_v3_rc_0034"
RECOVERY_EPOCH001_REGISTRY_RED_FREEZE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_"
    "PROVED_ISSUANCE_AND_INDEPENDENT_PROOF_SOURCE_CLOSURE_RECONCILIATION_"
    "RED_FREEZE_ONLY"
)
RECOVERY_EPOCH001_DETAILED_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
RECOVERY_EPOCH001_REQUIRED_SEQUENCE_EVENT_1 = "SOURCE_BASELINE_LOCKED"
RECOVERY_EPOCH001_COMPLETION_SEQUENCE_EVENT_2 = "STEP0_10_PREREQUISITES_PROVED"
RECOVERY_EPOCH001_FORMAL_NODE_COUNT = 134
RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256 = (
    "70a75ae561fad0846604d05b1262615be4c4a16b36b332150f8c7dc04ee71728"
)
RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256 = (
    "fbe29ce0b819563cb5db2dc79fec8277b32ae0dea5a3a5cba64230ba4a1f73cf"
)

_RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS = [{'step_number': 0,
  'actual_owners': [{'path': 'ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py',
                     'symbol': 'build_step0',
                     'role': 'design_boundary_owner'}],
  'strict_contracts': [{'contract_id': 'STEP0_DESIGN_IDENTITY_AND_V2_BOUNDARY',
                        'schema_version': 'cocolon.emlis.nls_v3.step0_version_boundary.v1',
                        'validator_path': 'ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py',
                        'validator_symbol': 'validate_step0',
                        'invariant_ids': ['DESIGN_IDENTITY_FIXED',
                                          'V2_IMMUTABLE_STOPPED',
                                          'PUBLIC_BOUNDARY_UNCHANGED']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s0_s1.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_freezes_live_design_identity_owner_and_v2_immutable_boundary'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step00_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step00_independent_negative.py::test_recovery_epoch001_step00_independent_negative',
                                 'validator_path': 'ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py',
                                 'validator_symbol': 'validate_step0',
                                 'attack_id': 'EMPTY_STEP0_DESIGN_BOUNDARY',
                                 'expected_closed_code': 'design_hash_mismatch'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_freezes_live_design_identity_owner_and_v2_immutable_boundary',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_independent_negative_mutations_are_rejected',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_step1_remain_runtime_disconnected_after_step3_contract_addition',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step00_independent_negative.py::test_recovery_epoch001_step00_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.step0_version_boundary.v1',
  'parent_binding_kind': 'SOURCE_BASELINE_LOCKED_EVENT_1',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_0_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'DESIGN_IMPLEMENTATION_CONFLICT',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'V2_MODIFICATION_OR_REOPEN_REQUIRED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP1_CURRENT_COMPLETION_PROOF_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 1,
  'actual_owners': [{'path': 'ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py',
                     'symbol': 'validate_step1',
                     'role': 'baseline_receipt_owner'}],
  'strict_contracts': [{'contract_id': 'STEP1_BASELINE_INPUT_AND_RECEIPT_BINDING',
                        'schema_version': 'cocolon.emlis.nls_v3.step1_baseline_receipt.v1',
                        'validator_path': 'ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py',
                        'validator_symbol': 'validate_step1',
                        'invariant_ids': ['SOURCE_BASELINE_BOUND',
                                          'APP_INPUT_CONTRACT_BOUND',
                                          'MEASURED_NOT_INVENTED']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s0_s1.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_receipt_is_body_free_parent_bound_and_measured'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step01_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step01_independent_negative.py::test_recovery_epoch001_step01_independent_negative',
                                 'validator_path': 'ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py',
                                 'validator_symbol': 'validate_input_contract',
                                 'attack_id': 'EMPTY_STEP1_INPUT_CONTRACT',
                                 'expected_closed_code': 'emotion_options_mismatch'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_actual_rn_input_contract_is_closed_and_hash_bound',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_input_contract_independent_negative_mutations_are_rejected',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_backend_compatibility_gap_is_bound_to_live_source_contract',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_source_resource_bounds_are_lossless_dynamic_and_boundary_closed',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_receipt_is_body_free_parent_bound_and_measured',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_current_v1_regenerates_all_28_committed_outputs_and_gates',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_dependency_closure_and_body_leak_mutations_are_rejected',
                                 'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_known_regressions_and_future_supabase_intake_do_not_fake_progress',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step01_independent_negative.py::test_recovery_epoch001_step01_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.step1_baseline_receipt.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_1_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'SOURCE_SNAPSHOT_MISMATCH',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'UI_SUBMIT_CONTRACT_UNRESOLVED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP2_CURRENT_COMPLETION_PROOF_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 2,
  'actual_owners': [{'path': 'ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py',
                     'symbol': 'build_corpus_registry',
                     'role': 'corpus_registry_owner'}],
  'strict_contracts': [{'contract_id': 'STEP2_APP_REACHABLE_CORPUS_REGISTRY',
                        'schema_version': 'cocolon.emlis.nls_v3.corpus_registry.v1',
                        'validator_path': 'ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py',
                        'validator_symbol': 'validate_corpus_registry',
                        'invariant_ids': ['APP_REACHABLE_ONLY',
                                          'DUPLICATE_POLICY_CLOSED',
                                          'ANNOTATION_RUNTIME_DISCONNECTED']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_app_reachable_positive_and_independent_negative_fixtures'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step02_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step02_independent_negative.py::test_recovery_epoch001_step02_independent_negative',
                                 'validator_path': 'ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py',
                                 'validator_symbol': 'validate_corpus_registry',
                                 'attack_id': 'EMPTY_CORPUS_REGISTRY',
                                 'expected_closed_code': 'corpus_registry:keyset_mismatch'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_app_reachable_positive_and_independent_negative_fixtures',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_sample_schema_cross_fields_and_forbidden_annotations_are_closed',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_json_and_jsonl_are_utf8_lf_canonical_and_adversarially_strict',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_exact_normalized_near_duplicate_policies_are_distinct_and_order_stable',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_identity_commitments_separate_input_case_and_private_hmac_domains',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_coverage_matrix_is_complete_recomputed_body_free_and_strictly_typed',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_schema_files_are_closed_and_runtime_bound_without_new_dependency',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_projection_is_an_explicit_deep_copy_allowlist',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_rn_contract_binding_and_independent_drift_mutations_are_red',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_registry_separates_corpora_binds_tests_and_never_counts_fixture_progress',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_manifest_binds_actual_files_review_and_transition_authority',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_near_candidates_require_explicit_review_before_validation',
                                 'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_previous_step_artifacts_remain_byte_frozen',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step02_independent_negative.py::test_recovery_epoch001_step02_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.corpus_registry.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_2_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'TEST_ANNOTATION_RUNTIME_INGRESS',
                         'UNREACHABLE_INPUT_ACCEPTED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP3_CURRENT_COMPLETION_PROOF_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 3,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py',
                     'symbol': 'validate_artifact_chain',
                     'role': 'strict_artifact_contract_owner'}],
  'strict_contracts': [{'contract_id': 'STEP3_STRICT_ARTIFACT_CHAIN',
                        'schema_version': 'cocolon.emlis.nls_v3.case_evidence_receipt.v2',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py',
                        'validator_symbol': 'validate_artifact_chain',
                        'invariant_ids': ['CLOSED_KEYSETS',
                                          'INDEPENDENT_VALIDATION',
                                          'BODY_FREE_RECEIPT']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_hand_authored_valid_bundle_passes_all_owner_validators'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step03_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step03_independent_negative.py::test_recovery_epoch001_step03_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py',
                                 'validator_symbol': 'validate_observation_stage_context',
                                 'attack_id': 'EMPTY_OBSERVATION_STAGE_ARTIFACT',
                                 'expected_closed_code': 'MISSING_FIELD'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_hand_authored_valid_bundle_passes_all_owner_validators',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_every_top_level_artifact_field_is_required',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_owner_and_nested_keysets_are_closed',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_invalid_enums_are_rejected_by_each_owner',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_bool_and_integer_types_are_never_coerced',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_adversarial_nested_shapes_fail_closed_without_exceptions',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_duplicate_ids_and_references_are_rejected_owner_by_owner',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_each_owner_rejects_one_byte_parent_hash_drift',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_future_stage_requires_resolved_upstream_authority',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_obligation_references_and_bound_reception_are_closed',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_content_discourse_ast_cross_references_are_closed',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_witness_has_no_internal_ids_and_spans_bind_actual_utf8_bytes',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_binding_contract_requires_unique_resolved_refs',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_generic_body_retained_metadata_attacks_fail_closed',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_receipt_is_strict_body_free_and_upstream_bound',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_v2_import_guard_detects_static_and_dynamic_probes',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_active_canonical_serializer_is_single_and_deterministic',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_canonical_codec_rejects_ambiguous_or_non_json_input',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_validator_remains_independent_from_future_builders',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_red_attack_catalog_is_complete_body_free_and_step_scoped',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_step0_step2_and_batch001_remain_byte_frozen',
                                 'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_completion_receipt_binds_implementation_and_next_authority',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step03_independent_negative.py::test_recovery_epoch001_step03_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.case_evidence_receipt.v2',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_3_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SELF_DECLARED_BUILDER_VALIDATOR_AUTHORITY',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'STRICT_SCHEMA_RELAXATION_REQUIRED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP4_SEMANTIC_INVENTORY_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 4,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py',
                     'symbol': 'build_semantic_obligation_inventory',
                     'role': 'semantic_obligation_inventory_owner'}],
  'strict_contracts': [{'contract_id': 'STEP4_LOSSLESS_SEMANTIC_OBLIGATIONS',
                        'schema_version': 'cocolon.emlis.nls_v3.semantic_obligation_ledger.v1',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py',
                        'validator_symbol': 'validate_semantic_obligation_inventory',
                        'invariant_ids': ['REQUIRED_MEANING_LOSSLESS',
                                          'SOURCE_ROLES_DISTINCT',
                                          'RESOURCE_BOUND_CLOSED']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_known_normal_builds_lossless_machine_safe_alias_inventory'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step04_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step04_independent_negative.py::test_recovery_epoch001_step04_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py',
                                 'validator_symbol': 'validate_obligation_inventory_count',
                                 'attack_id': 'BOUND_PLUS_ONE_OBLIGATION_COUNT',
                                 'expected_closed_code': 'OBLIGATION_INVENTORY_OVERFLOW'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_known_normal_builds_lossless_machine_safe_alias_inventory',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_batch001_all_100_build_and_validate_without_surface_or_runtime',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_is_deterministic_body_free_and_ignores_fixture_cues',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_cross_input_plan_and_resolver_cannot_bind_to_another_input',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_same_shape_input_swap_changes_v3_source_commitments',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_exact_source_replay_rejects_added_deleted_and_rebound_meaning',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_alias_and_snapshot_authority_forgery_are_rejected',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_coherently_resigned_snapshot_rebinds_to_original_source',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_restatement_relation_is_typed_and_cannot_inflate_depth',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_restatement_unit_is_losslessly_bound_and_forgery_is_rejected',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_pre_question_preserves_all_unknowns_and_hash_boundaries',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_frozen_source_policy_rejects_in_process_artifact_drift',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_refined_context_requires_and_consumes_the_partition_owner',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_source_unavailable_is_label_bounded_and_empty_fails_closed',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_self_denial_keeps_identity_boundary_and_concrete_action_distinct',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_separate_safety_owner_is_delegated',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_inventory_bound_is_exact_step1_formula_and_components_are_strict',
                                 'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_cross_role_refined_snapshot_lineage_alias_and_tamper_red',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step04_independent_negative.py::test_recovery_epoch001_step04_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.semantic_obligation_ledger.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_4_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'ORIGINAL_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'SURFACE_POSTHOC_REQUIRED_MEANING'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP5_REFINED_CONTENT_SELECTION_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 5,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_content_selection_v3.py',
                     'symbol': 'build_content_selection_plan',
                     'role': 'content_selection_owner'}],
  'strict_contracts': [{'contract_id': 'STEP5_REQUIRED_COVERAGE_STAGE_DEPTH',
                        'schema_version': 'cocolon.emlis.nls_v3.content_selection_plan.v1',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_content_selection_v3.py',
                        'validator_symbol': 'validate_content_selection_plan',
                        'invariant_ids': ['REQUIRED_COVERAGE_COMPLETE',
                                          'STAGE_SOURCE_POLICY_BOUND',
                                          'DEPTH_NONINFLATION']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_normal_plan_has_exact_required_coverage_and_no_unproven_status'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step05_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step05_independent_negative.py::test_recovery_epoch001_step05_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_content_selection_v3.py',
                                 'validator_symbol': 'validate_content_selection_policy',
                                 'attack_id': 'INVALID_SEMANTIC_INVENTORY_PARENT',
                                 'expected_closed_code': 'SEMANTIC_INVENTORY_RESULT_TYPE_INVALID'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_stage_context_is_explicit_body_free_and_future_authority_bound',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_refined_schema_is_bound_but_stops_without_partition_owner',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_refined_partition_reaches_content_selection_body_free',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_refined_active_role_drop_is_independently_rejected',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_normal_plan_has_exact_required_coverage_and_no_unproven_status',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_batch001_all_100_match_reviewed_depth_and_required_coverage',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_depth_uses_typed_meaning_units_not_repetition_or_length',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_self_denial_and_concrete_action_require_layered_separation',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_required_meaning_cannot_be_deferred_omitted_or_relabelled',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_depth_budget_parent_hash_and_coverage_are_not_self_declared',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_revalidates_step4_against_shrink_reid_relabel_and_downgrade',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_pre_question_preserves_every_unknown_and_observation',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_source_unavailable_is_limited_to_labels_or_explicit_unknown',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_new_modules_are_runtime_disconnected_and_do_not_read_fixture_cues',
                                 'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_cross_role_depth_noninflation_floor_and_effect_scope_red',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step05_independent_negative.py::test_recovery_epoch001_step05_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.content_selection_plan.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_5_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PRE_QUESTION_UNKNOWN_COMPLETION_REQUIRED',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'SYNONYM_REPETITION_REQUIRED_FOR_DEPTH'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP6_DISCOURSE_GRAPH_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 6,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py',
                     'symbol': 'build_discourse_graph_plans',
                     'role': 'discourse_graph_owner'}],
  'strict_contracts': [{'contract_id': 'STEP6_CONTENT_DERIVED_DISCOURSE_GRAPH',
                        'schema_version': 'cocolon.emlis.nls_v3.discourse_plan.v1',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py',
                        'validator_symbol': 'validate_discourse_graph_plan_set',
                        'invariant_ids': ['CONTENT_DERIVED_SIGNATURE',
                                          'NO_FAMILY_OR_FIXTURE_CUE',
                                          'BOUNDED_STRUCTURAL_VARIATION']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_batch001_all_100_are_strict_bounded_and_semantically_ordered'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step06_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step06_independent_negative.py::test_recovery_epoch001_step06_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py',
                                 'validator_symbol': 'validate_discourse_graph_plan_set',
                                 'attack_id': 'INVALID_DISCOURSE_PARENT_CHAIN',
                                 'expected_closed_code': 'DISCOURSE_PARENT_REVALIDATION_FAILED'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_batch001_all_100_are_strict_bounded_and_semantically_ordered',
                                 'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_input_swap_changes_content_derived_signatures',
                                 'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_recomputes_candidate_set_and_rejects_coherent_mutation',
                                 'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_has_no_fixture_or_surface_generation_cues',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step06_independent_negative.py::test_recovery_epoch001_step06_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.discourse_plan.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_6_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'FAMILY_FIXED_STRUCTURE_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'SYNONYM_CANDIDATE_COUNT_INFLATION'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP7_TYPED_AST_RENDERER_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 7,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py',
                     'symbol': 'build_typed_surface_ast',
                     'role': 'typed_surface_ast_owner'},
                    {'path': 'ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py',
                     'symbol': 'render_canonical_surface',
                     'role': 'canonical_renderer_owner'}],
  'strict_contracts': [{'contract_id': 'STEP7_TYPED_AST_CANONICAL_BYTES',
                        'schema_version': 'cocolon.emlis.nls_v3.surface_ast.v1',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py',
                        'validator_symbol': 'validate_typed_surface_ast',
                        'invariant_ids': ['CLOSED_TYPED_NODE_UNION',
                                          'CANONICAL_UTF8_BYTES',
                                          'NO_POST_GATE_TEXT_REPAIR']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_batch001_all_100_render_canonical_input_bound_bytes'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step07_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step07_independent_negative.py::test_recovery_epoch001_step07_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py',
                                 'validator_symbol': 'validate_typed_surface_ast',
                                 'attack_id': 'INVALID_AST_PARENT_CHAIN',
                                 'expected_closed_code': 'AST_PARENT_REVALIDATION_FAILED'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_batch001_all_100_render_canonical_input_bound_bytes',
                                 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_all_structural_candidates_render_to_distinct_bytes',
                                 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_authority_is_opaque_and_every_visible_field_is_revalidated',
                                 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_arbitrary_ast_source_swap_and_relation_reversal_fail_closed',
                                 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_catalog_in_place_and_rebind_mutations_are_rejected',
                                 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_low_information_fallback_and_reserved_label_anchor_are_safe',
                                 'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_closed_api_has_no_post_gate_text_or_stopped_module_dependency',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step07_independent_negative.py::test_recovery_epoch001_step07_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.surface_ast.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_7_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['ARBITRARY_TEXT_NODE_REQUIRED',
                         'BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'POST_GATE_STRING_REPAIR_REQUIRED',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP8_BODY_ONLY_PARSER_MATCHER_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 8,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_body_semantic_atom_parser_v3.py',
                     'symbol': 'parse_body_semantic_atoms',
                     'role': 'body_only_parser_owner'},
                    {'path': 'ai/services/ai_inference/emlis_ai_independent_semantic_matcher_v3.py',
                     'symbol': 'match_parsed_surface_witness',
                     'role': 'independent_matcher_owner'}],
  'strict_contracts': [{'contract_id': 'STEP8_BODY_ONLY_INDEPENDENT_BINDING',
                        'schema_version': 'cocolon.emlis.nls_v3.verified_surface_binding.v2',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_step8_artifact_contract_v3.py',
                        'validator_symbol': 'validate_verified_surface_binding_v2',
                        'invariant_ids': ['BODY_ONLY_PARSE',
                                          'RENDERER_INDEPENDENT_MATCH',
                                          'SOURCE_SWAP_REJECTED']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_all_100_inputs_and_596_candidates_parse_and_bind'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step08_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step08_independent_negative.py::test_recovery_epoch001_step08_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_body_semantic_atom_parser_v3.py',
                                 'validator_symbol': 'parse_body_semantic_atoms',
                                 'attack_id': 'NON_UTF8_CANDIDATE_BYTES',
                                 'expected_closed_code': 'CANDIDATE_UTF8_REQUIRED'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_v1_release_bytes_remain_frozen_with_v2_side_by_side',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_all_100_inputs_and_596_candidates_parse_and_bind',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_contracts_are_closed_hash_bound_and_semantically_signed',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_generic_body_stale_witness_and_clause_deletion_fail',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_source_swap_authority_forgery_and_toctou_fail',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_relation_unknown_graph_role_and_feature_mutations_fail',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_stage_boundary_and_source_role_are_fail_closed',
                                 'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_syntax_dependency_drift_and_import_boundaries_fail_closed',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step08_independent_negative.py::test_recovery_epoch001_step08_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.verified_surface_binding.v2',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_8_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CANDIDATE_METADATA_REQUIRED_FOR_COVERAGE',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP9_STANDALONE_SUCCESSOR_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 9,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py',
                     'symbol': 'validate_semantic_hard_gate_result',
                     'role': 'hard_gate_owner'},
                    {'path': 'ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py',
                     'symbol': 'select_semantic_candidates',
                     'role': 'selector_owner'},
                    {'path': 'ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py',
                     'symbol': 'select_with_bounded_recovery',
                     'role': 'bounded_recovery_owner'}],
  'strict_contracts': [{'contract_id': 'STEP9_HARD_GATE_SELECTOR_BOUNDED_RECOVERY',
                        'schema_version': 'cocolon.emlis.nls_v3.hard_gate_candidate_decision.v1',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py',
                        'validator_symbol': 'validate_semantic_hard_gate_result',
                        'invariant_ids': ['HARD_FAILURE_NOT_WEIGHTED',
                                          'LEXICOGRAPHIC_SELECTION',
                                          'REQUIRED_MEANING_NOT_DELETED']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_all_100_inputs_596_candidates_hard_pass_and_select'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step09_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step09_independent_negative.py::test_recovery_epoch001_step09_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_step9_artifact_contract_v3.py',
                                 'validator_symbol': 'validate_hard_gate_result_structure',
                                 'attack_id': 'INVALID_HARD_GATE_RESULT_TYPE',
                                 'expected_closed_code': 'HARD_GATE_RESULT_TYPE_INVALID'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_step0_step8_bytes_and_side_by_side_policies_are_frozen',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_decision_contracts_reject_malformed_shapes_fail_closed',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_all_100_inputs_596_candidates_hard_pass_and_select',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_each_of_twenty_gate_rows_has_a_dedicated_negative_path',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_v2_recurrence_attacks_and_result_self_declaration_fail',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_selector_is_lexicographic_permutation_invariant_and_hard_only',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_bounded_recovery_rebuild_split_and_minimal_lanes',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_no_valid_candidate_stays_failure_and_never_counts_v1',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_pre_question_source_context_is_not_recovered_or_selected',
                                 'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_modules_are_runtime_disconnected_and_fixture_cue_free',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step09_independent_negative.py::test_recovery_epoch001_step09_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.hard_gate_candidate_decision.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_9_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'HARD_FAILURE_WEIGHTED_SCORE_RESCUE',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'REQUIRED_OBLIGATION_DELETION_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_STEP10_SINGLE_GRAPH_DORMANT_INTEGRATION_COMPLETION_VERIFICATION_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}},
 {'step_number': 10,
  'actual_owners': [{'path': 'ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py',
                     'symbol': 'execute_dormant_v3',
                     'role': 'dormant_runtime_owner'},
                    {'path': 'ai/tools/emlis_nls_v3_batch_run.py',
                     'symbol': 'run_batch',
                     'role': 'batch_runner_owner'}],
  'strict_contracts': [{'contract_id': 'STEP10_DORMANT_RUNTIME_SAME_BYTES_EVIDENCE',
                        'schema_version': 'cocolon.emlis.nls_v3.dormant_runtime_execution.v1',
                        'validator_path': 'ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py',
                        'validator_symbol': 'validate_dormant_runtime_execution',
                        'invariant_ids': ['PUBLIC_OWNER_REMAINS_V1',
                                          'RUNNER_USES_RUNTIME_BYTES',
                                          'PRIVATE_AND_BODY_FREE_EVIDENCE_SEPARATE']}],
  'positive_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py',
                     'test_node_id': 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_runtime_execution_recomputes_the_full_parent_chain_and_frozen_rc'},
  'independent_negative_proof': {'source_path': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step10_independent_negative.py',
                                 'test_node_id': 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step10_independent_negative.py::test_recovery_epoch001_step10_independent_negative',
                                 'validator_path': 'ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py',
                                 'validator_symbol': 'validate_runtime_owner_state',
                                 'attack_id': 'INVALID_RUNTIME_OWNER_STATE_TYPE',
                                 'expected_closed_code': 'RUNTIME_STATE_TYPE_INVALID'},
  'formal_completion_node_ids': ['ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_public_contract_is_unchanged_and_default_owner_is_disabled_v1',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_state_machine_is_fail_closed_and_tester_authority_is_opaque',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_reply_bridge_preserves_selected_canonical_utf8_bytes_exactly',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_runtime_execution_recomputes_the_full_parent_chain_and_frozen_rc',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_delivery_keeps_v3_success_and_v1_fallback_boundaries_separate',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_batch_runner_aborts_infrastructure_and_lineage_failures',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_private_io_rejects_ancestor_symlinks',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_runtime_app_reachable_adapter_matches_frozen_step2_policy',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_private_body_full_and_body_free_hmac_evidence_are_separate',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_receipt_v3_schema_and_step11_evidence_builders_are_closed',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_partial_batch_cannot_claim_formal_completion_or_acceptance',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_cumulative_uses_fresh_closure_and_rejects_missing_or_duplicate_cases',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_output_diff_is_body_free_and_commitment_based',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_rn_api_db_and_step9_historical_boundaries_remain_frozen',
                                 'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_local_emotion_submit_e2e_preserves_db_and_public_contract',
                                 'ai/tests/test_emlis_nls_v3_recovery_epoch001_step10_independent_negative.py::test_recovery_epoch001_step10_independent_negative'],
  'artifact_receipt_schema_version': 'cocolon.emlis.nls_v3.dormant_runtime_execution.v1',
  'parent_binding_kind': 'PREVIOUS_CURRENT_STEP_PROVED_RECEIPT',
  'source_binding_kind': 'SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW',
  'completion_condition_ids': ['STEP_10_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED'],
  'stop_condition_ids': ['BACKFILL_FORBIDDEN',
                         'CASE_FAMILY_PHRASE_DISPATCH_REQUIRED',
                         'GENERIC_BODY_RETAINED_METADATA_ATTACK_UNCLOSED',
                         'MODEL_FREE_COMMON_STRUCTURE_REPEATED_MAJOR_FAILURE',
                         'ORIGINAL_AND_SUPPLEMENTAL_SOURCE_UNSEPARABLE',
                         'PUBLIC_API_DB_RN_CHANGE_REQUIRED',
                         'PUBLIC_API_DB_RN_NAMING_SAFETY_OWNER_CHANGE_REQUIRED',
                         'RAW_OR_PRIVATE_BODY_PUBLIC_META_INGRESS',
                         'REQUIRED_MEANING_DELETING_RECOVERY_REQUIRED',
                         'SEMANTIC_OBLIGATION_NOT_TRACEABLE_TO_FINAL_BODY',
                         'STOPPED_V2_CHANGE_OR_IMPORT_REQUIRED',
                         'V3_ACTIVATION_REQUIRED_FOR_RUNNER'],
  'next_authority': 'NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY',
  'lineage': {'kind': 'current',
              'recovery_epoch': 1,
              'historical_disposition': 'IMMUTABLE_NONCURRENT_EVIDENCE',
              'historical_rewrite': False,
              'historical_as_current': False,
              'backfill': False}}]
RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS = tuple(
    copy.deepcopy(_RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS)
)
RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP = {0: ['ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_freezes_live_design_identity_owner_and_v2_immutable_boundary',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_independent_negative_mutations_are_rejected',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step0_step1_remain_runtime_disconnected_after_step3_contract_addition',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step00_independent_negative.py::test_recovery_epoch001_step00_independent_negative'],
 1: ['ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_actual_rn_input_contract_is_closed_and_hash_bound',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_input_contract_independent_negative_mutations_are_rejected',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_backend_compatibility_gap_is_bound_to_live_source_contract',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_source_resource_bounds_are_lossless_dynamic_and_boundary_closed',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_receipt_is_body_free_parent_bound_and_measured',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_current_v1_regenerates_all_28_committed_outputs_and_gates',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_dependency_closure_and_body_leak_mutations_are_rejected',
     'ai/tests/test_emlis_nls_v3_s0_s1.py::test_step1_known_regressions_and_future_supabase_intake_do_not_fake_progress',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step01_independent_negative.py::test_recovery_epoch001_step01_independent_negative'],
 2: ['ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_app_reachable_positive_and_independent_negative_fixtures',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_sample_schema_cross_fields_and_forbidden_annotations_are_closed',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_json_and_jsonl_are_utf8_lf_canonical_and_adversarially_strict',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_exact_normalized_near_duplicate_policies_are_distinct_and_order_stable',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_identity_commitments_separate_input_case_and_private_hmac_domains',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_coverage_matrix_is_complete_recomputed_body_free_and_strictly_typed',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_schema_files_are_closed_and_runtime_bound_without_new_dependency',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_projection_is_an_explicit_deep_copy_allowlist',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_rn_contract_binding_and_independent_drift_mutations_are_red',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_registry_separates_corpora_binds_tests_and_never_counts_fixture_progress',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_manifest_binds_actual_files_review_and_transition_authority',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_near_candidates_require_explicit_review_before_validation',
     'ai/tests/test_emlis_nls_v3_s2_sample_registry.py::test_step2_previous_step_artifacts_remain_byte_frozen',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step02_independent_negative.py::test_recovery_epoch001_step02_independent_negative'],
 3: ['ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_hand_authored_valid_bundle_passes_all_owner_validators',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_every_top_level_artifact_field_is_required',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_owner_and_nested_keysets_are_closed',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_invalid_enums_are_rejected_by_each_owner',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_bool_and_integer_types_are_never_coerced',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_adversarial_nested_shapes_fail_closed_without_exceptions',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_duplicate_ids_and_references_are_rejected_owner_by_owner',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_each_owner_rejects_one_byte_parent_hash_drift',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_future_stage_requires_resolved_upstream_authority',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_obligation_references_and_bound_reception_are_closed',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_content_discourse_ast_cross_references_are_closed',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_witness_has_no_internal_ids_and_spans_bind_actual_utf8_bytes',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_binding_contract_requires_unique_resolved_refs',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_generic_body_retained_metadata_attacks_fail_closed',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_receipt_is_strict_body_free_and_upstream_bound',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_v2_import_guard_detects_static_and_dynamic_probes',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_active_canonical_serializer_is_single_and_deterministic',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_canonical_codec_rejects_ambiguous_or_non_json_input',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_validator_remains_independent_from_future_builders',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_red_attack_catalog_is_complete_body_free_and_step_scoped',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_step0_step2_and_batch001_remain_byte_frozen',
     'ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py::test_s3_completion_receipt_binds_implementation_and_next_authority',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step03_independent_negative.py::test_recovery_epoch001_step03_independent_negative'],
 4: ['ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_known_normal_builds_lossless_machine_safe_alias_inventory',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_batch001_all_100_build_and_validate_without_surface_or_runtime',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_is_deterministic_body_free_and_ignores_fixture_cues',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_cross_input_plan_and_resolver_cannot_bind_to_another_input',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_same_shape_input_swap_changes_v3_source_commitments',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_exact_source_replay_rejects_added_deleted_and_rebound_meaning',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_alias_and_snapshot_authority_forgery_are_rejected',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_coherently_resigned_snapshot_rebinds_to_original_source',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_restatement_relation_is_typed_and_cannot_inflate_depth',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_restatement_unit_is_losslessly_bound_and_forgery_is_rejected',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_pre_question_preserves_all_unknowns_and_hash_boundaries',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_frozen_source_policy_rejects_in_process_artifact_drift',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_refined_context_requires_and_consumes_the_partition_owner',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_source_unavailable_is_label_bounded_and_empty_fails_closed',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_self_denial_keeps_identity_boundary_and_concrete_action_distinct',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_separate_safety_owner_is_delegated',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_inventory_bound_is_exact_step1_formula_and_components_are_strict',
     'ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py::test_s4_cross_role_refined_snapshot_lineage_alias_and_tamper_red',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step04_independent_negative.py::test_recovery_epoch001_step04_independent_negative'],
 5: ['ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_stage_context_is_explicit_body_free_and_future_authority_bound',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_refined_schema_is_bound_but_stops_without_partition_owner',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_refined_partition_reaches_content_selection_body_free',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_refined_active_role_drop_is_independently_rejected',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_normal_plan_has_exact_required_coverage_and_no_unproven_status',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_batch001_all_100_match_reviewed_depth_and_required_coverage',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_depth_uses_typed_meaning_units_not_repetition_or_length',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_self_denial_and_concrete_action_require_layered_separation',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_required_meaning_cannot_be_deferred_omitted_or_relabelled',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_depth_budget_parent_hash_and_coverage_are_not_self_declared',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_revalidates_step4_against_shrink_reid_relabel_and_downgrade',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_pre_question_preserves_every_unknown_and_observation',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_source_unavailable_is_limited_to_labels_or_explicit_unknown',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_new_modules_are_runtime_disconnected_and_do_not_read_fixture_cues',
     'ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py::test_s5_cross_role_depth_noninflation_floor_and_effect_scope_red',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step05_independent_negative.py::test_recovery_epoch001_step05_independent_negative'],
 6: ['ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_batch001_all_100_are_strict_bounded_and_semantically_ordered',
     'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_input_swap_changes_content_derived_signatures',
     'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_recomputes_candidate_set_and_rejects_coherent_mutation',
     'ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py::test_s6_has_no_fixture_or_surface_generation_cues',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step06_independent_negative.py::test_recovery_epoch001_step06_independent_negative'],
 7: ['ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_batch001_all_100_render_canonical_input_bound_bytes',
     'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_all_structural_candidates_render_to_distinct_bytes',
     'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_authority_is_opaque_and_every_visible_field_is_revalidated',
     'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_arbitrary_ast_source_swap_and_relation_reversal_fail_closed',
     'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_catalog_in_place_and_rebind_mutations_are_rejected',
     'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_low_information_fallback_and_reserved_label_anchor_are_safe',
     'ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py::test_s7_closed_api_has_no_post_gate_text_or_stopped_module_dependency',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step07_independent_negative.py::test_recovery_epoch001_step07_independent_negative'],
 8: ['ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_v1_release_bytes_remain_frozen_with_v2_side_by_side',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_all_100_inputs_and_596_candidates_parse_and_bind',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_contracts_are_closed_hash_bound_and_semantically_signed',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_generic_body_stale_witness_and_clause_deletion_fail',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_source_swap_authority_forgery_and_toctou_fail',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_relation_unknown_graph_role_and_feature_mutations_fail',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_stage_boundary_and_source_role_are_fail_closed',
     'ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py::test_s8_syntax_dependency_drift_and_import_boundaries_fail_closed',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step08_independent_negative.py::test_recovery_epoch001_step08_independent_negative'],
 9: ['ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_step0_step8_bytes_and_side_by_side_policies_are_frozen',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_decision_contracts_reject_malformed_shapes_fail_closed',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_all_100_inputs_596_candidates_hard_pass_and_select',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_each_of_twenty_gate_rows_has_a_dedicated_negative_path',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_v2_recurrence_attacks_and_result_self_declaration_fail',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_selector_is_lexicographic_permutation_invariant_and_hard_only',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_bounded_recovery_rebuild_split_and_minimal_lanes',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_no_valid_candidate_stays_failure_and_never_counts_v1',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_pre_question_source_context_is_not_recovered_or_selected',
     'ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py::test_s9_modules_are_runtime_disconnected_and_fixture_cue_free',
     'ai/tests/test_emlis_nls_v3_recovery_epoch001_step09_independent_negative.py::test_recovery_epoch001_step09_independent_negative'],
 10: ['ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_public_contract_is_unchanged_and_default_owner_is_disabled_v1',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_state_machine_is_fail_closed_and_tester_authority_is_opaque',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_reply_bridge_preserves_selected_canonical_utf8_bytes_exactly',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_runtime_execution_recomputes_the_full_parent_chain_and_frozen_rc',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_delivery_keeps_v3_success_and_v1_fallback_boundaries_separate',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_batch_runner_aborts_infrastructure_and_lineage_failures',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_private_io_rejects_ancestor_symlinks',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_runtime_app_reachable_adapter_matches_frozen_step2_policy',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_private_body_full_and_body_free_hmac_evidence_are_separate',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_receipt_v3_schema_and_step11_evidence_builders_are_closed',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_partial_batch_cannot_claim_formal_completion_or_acceptance',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_cumulative_uses_fresh_closure_and_rejects_missing_or_duplicate_cases',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_output_diff_is_body_free_and_commitment_based',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_rn_api_db_and_step9_historical_boundaries_remain_frozen',
      'ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py::test_s10_local_emotion_submit_e2e_preserves_db_and_public_contract',
      'ai/tests/test_emlis_nls_v3_recovery_epoch001_step10_independent_negative.py::test_recovery_epoch001_step10_independent_negative']}

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:-]{1,512}$")
_TOP_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "recovery_epoch",
        "red_freeze_authority",
        "detailed_design_sha256",
        "required_sequence_event_1",
        "completion_sequence_event_2",
        "steps",
        "automatic_progression",
        "body_free",
        "registry_sha256",
    }
)
_ROW_KEYS = frozenset(
    {
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
)


def _body_free(value: Any, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is str:
        return _BODY_FREE_TOKEN_RE.fullmatch(value) is not None
    if type(value) not in (list, dict):
        return False
    seen = set() if active is None else active
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    try:
        if type(value) is list:
            return all(_body_free(item, seen) for item in value)
        for key, item in value.items():
            if type(key) is not str:
                return False
            lowered = key.lower()
            if any(
                token in lowered
                for token in (
                    "raw_body",
                    "candidate_body",
                    "prompt_text",
                    "response_text",
                    "user_text",
                    "stdout",
                    "stderr",
                    "traceback",
                )
            ):
                return False
            if not _body_free(item, seen):
                return False
        return True
    finally:
        seen.remove(identity)


def _top_level_symbols(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, ast.Import):
            result.update(alias.asname or alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name != "*"
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            result.update(
                target.id for target in targets if isinstance(target, ast.Name)
            )
    return result


def _registry_material() -> dict[str, Any]:
    return {
        "schema_version": (
            RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_REGISTRY_SCHEMA
        ),
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "recovery_epoch": 1,
        "red_freeze_authority": RECOVERY_EPOCH001_REGISTRY_RED_FREEZE_AUTHORITY,
        "detailed_design_sha256": RECOVERY_EPOCH001_DETAILED_DESIGN_SHA256,
        "required_sequence_event_1": (
            RECOVERY_EPOCH001_REQUIRED_SEQUENCE_EVENT_1
        ),
        "completion_sequence_event_2": (
            RECOVERY_EPOCH001_COMPLETION_SEQUENCE_EVENT_2
        ),
        "steps": copy.deepcopy(
            _RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS
        ),
        "automatic_progression": False,
        "body_free": True,
    }


def fresh_recovery_epoch001_current_step_requirement_registry() -> dict[str, Any]:
    """Return a fresh immutable-denominator registry candidate."""

    registry = _registry_material()
    registry["registry_sha256"] = artifact_sha256(registry)
    return registry


def _path_symbol_valid(root: Path, path_value: Any, symbol_value: Any) -> bool:
    if type(path_value) is not str or type(symbol_value) is not str:
        return False
    path = root / path_value
    return path.is_file() and symbol_value in _top_level_symbols(path)


def _validate_recovery_epoch001_current_step_requirement_registry_shape_impl(
    value: Any,
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Fail closed on any denominator, source, lineage, or hash drift."""

    if type(value) is not dict:
        return ("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID",)
    issues: set[str] = set()
    expected = fresh_recovery_epoch001_current_step_requirement_registry()
    if set(value) != _TOP_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
    steps = value.get("steps")
    if type(steps) is not list:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
        steps = []
    if [row.get("step_number") for row in steps if type(row) is dict] != list(
        range(11)
    ):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ORDER_INVALID")
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STEP_INVALID")
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    seen_nodes: set[str] = set()
    for step, row in enumerate(steps):
        expected_row = (
            _RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS[step]
            if step < 11
            else None
        )
        if type(row) is not dict or set(row) != _ROW_KEYS:
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
            continue
        if expected_row is None or row.get("step_number") != step:
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STEP_INVALID")
            continue
        if row.get("actual_owners") != expected_row["actual_owners"]:
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_OWNER_INVALID")
        for owner in row.get("actual_owners", []):
            if type(owner) is not dict or not _path_symbol_valid(
                root, owner.get("path"), owner.get("symbol")
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_OWNER_INVALID"
                )
        if row.get("strict_contracts") != expected_row["strict_contracts"]:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_CONTRACT_INVALID"
            )
        for contract in row.get("strict_contracts", []):
            if type(contract) is not dict or not _path_symbol_valid(
                root,
                contract.get("validator_path"),
                contract.get("validator_symbol"),
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_CONTRACT_INVALID"
                )
        if (
            row.get("positive_proof") != expected_row["positive_proof"]
            or row.get("independent_negative_proof")
            != expected_row["independent_negative_proof"]
        ):
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PROOF_INVALID")
        for proof_key in ("positive_proof", "independent_negative_proof"):
            proof = row.get(proof_key)
            node_id = proof.get("test_node_id") if type(proof) is dict else None
            path_value = proof.get("source_path") if type(proof) is dict else None
            function_name = (
                node_id.rpartition("::")[2] if type(node_id) is str else None
            )
            if (
                type(node_id) is not str
                or type(path_value) is not str
                or not node_id.startswith(f"{path_value}::test_")
                or not _path_symbol_valid(root, path_value, function_name)
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PROOF_INVALID"
                )
        nodes_for_step = row.get("formal_completion_node_ids")
        expected_nodes = RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
        if (
            type(nodes_for_step) is not list
            or nodes_for_step != expected_nodes
            or any(type(node) is not str for node in nodes_for_step)
            or any(node in seen_nodes for node in nodes_for_step)
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID"
            )
        if type(nodes_for_step) is list:
            seen_nodes.update(
                node for node in nodes_for_step if type(node) is str
            )
        if row.get("artifact_receipt_schema_version") != (
            expected_row["artifact_receipt_schema_version"]
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ARTIFACT_INVALID"
            )
        if (
            row.get("parent_binding_kind")
            != expected_row["parent_binding_kind"]
            or row.get("source_binding_kind")
            != expected_row["source_binding_kind"]
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
                "PARENT_OR_SOURCE_INVALID"
            )
        if row.get("completion_condition_ids") != (
            expected_row["completion_condition_ids"]
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_COMPLETION_INVALID"
            )
        if row.get("stop_condition_ids") != expected_row["stop_condition_ids"]:
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STOP_INVALID")
        if row.get("next_authority") != expected_row["next_authority"]:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
                "NEXT_AUTHORITY_INVALID"
            )
        if row.get("lineage") != expected_row["lineage"]:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_LINEAGE_INVALID"
            )
    if len(seen_nodes) != RECOVERY_EPOCH001_FORMAL_NODE_COUNT:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID")
    if value != expected:
        if value.get("schema_version") != expected["schema_version"]:
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
        if steps != expected["steps"] and not issues:
            issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
    if value.get("body_free") is not True or not _body_free(value):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_BODY_FREE_REQUIRED")
    try:
        material = {key: value[key] for key in value if key != "registry_sha256"}
        expected_hash = artifact_sha256(material)
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("registry_sha256") != expected_hash
        or value.get("registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
        or _SHA_RE.fullmatch(str(value.get("registry_sha256", ""))) is None
    ):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_HASH_MISMATCH")
    formal_root = artifact_sha256(
        {
            "step_nodes": {
                str(step): list(RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step])
                for step in range(11)
            }
        }
    )
    if formal_root != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID")
    return tuple(sorted(issues))


def validate_recovery_epoch001_current_step_requirement_registry_shape(
    value: Any,
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    try:
        return (
            _validate_recovery_epoch001_current_step_requirement_registry_shape_impl(
                value,
                repo_root=repo_root,
            )
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID",)
