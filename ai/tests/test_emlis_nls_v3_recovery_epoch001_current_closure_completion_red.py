# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 001 canonical-current-closure completion RED freeze.

The tests in this file reserve the collision-free current candidate, freeze
the exact owner/verifier/receipt/single-graph responsibilities, and expose
each missing responsibility as a causal RED.  They do not create a successful
Step 0-10 receipt, lock a source baseline, authorize P2, or run a corpus.
"""

import ast
import hashlib
import importlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from helpers import emlis_nls_v3_s0_s1_baseline as s01


_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP0_10_CANONICAL_CURRENT_"
    "CLOSURE_AND_STANDALONE_COMPLETION_PROOF_NONCONFORMANCE_REMEDIATION_"
    "RED_FREEZE_ONLY"
)
_SOURCE_PIN = "bd62ef0eec2348e3b190ec2a39c3794886ccd10d"
_COCOLON_PIN = "3cb7867c3f8cbe39ee38ffe5c55179df81b5b0fa"
_DETAILED_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
_RECOVERY_CANDIDATE = "nls_v3_rc_0034"
_RECOVERY_SCOPE = (
    "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_CANDIDATE_ONLY"
)
_RECOVERY_DISPOSITION = (
    "CURRENT_CLOSURE_CANDIDATE_NOT_BASELINE_NOT_CYCLE_ACCEPTANCE"
)
_RC0032_DISPOSITION = "FAILED_PREREQUISITE_CANDIDATE_HISTORY_ONLY"
_RC0033_DISPOSITION = "PREEXISTING_SYNTHETIC_LATER_RC_ONLY"

_CLOSURE_MODULE = (
    "emlis_ai_recovery_epoch001_canonical_current_closure_v3"
)
_CLOSURE_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_canonical_current_closure_v3.py"
)
_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "canonical_current_closure.v1"
)
_RECEIPT_MODULE = (
    "emlis_ai_recovery_epoch001_step_completion_receipt_v3"
)
_RECEIPT_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_step_completion_receipt_v3.py"
)
_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_completion_receipt.v1"
)
_SUCCESSOR_MODULE = "emlis_ai_step9_recovery_epoch001_successor_v3"
_SUCCESSOR_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step9_recovery_epoch001_successor_v3.py"
)
_INDEPENDENT_VERIFIER_PATH = (
    "ai/tools/emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
)
_THIS_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
)
_STEP5_RED_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_SEMANTIC_"
    "RESTATEMENT_WITNESS_AND_DEPTH_NONINFLATION_REMEDIATION_RED_FREEZE_ONLY"
)
_STEP5_RED_COCOLON_ENTRY_HEAD = (
    "ec66fdbadef3ebee4b5a531f77391252146b2e4e"
)
_STEP5_RED_MASHOS_API_ENTRY_HEAD = (
    "21600c3d07b4f3d870beb3acb0bd78bf3e898f36"
)
_STEP5_RECONCILIATION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_TYPED_"
    "SUBGRAPH_BIJECTION_AND_POSITIVE_INPUT_CONTRACT_RECONCILIATION_READ_ONLY"
)
_STEP5_RED_CORRECTION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_TYPED_"
    "SUBGRAPH_BIJECTION_AND_POSITIVE_INPUT_CONTRACT_RECONCILIATION_RED_"
    "CORRECTION_AND_REFREEZE_ONLY"
)
_STEP5_RED_CORRECTION_COCOLON_ENTRY_HEAD = (
    "3bd0bcb8077ecaab07b04e913bdffaa2f66f3c7f"
)
_STEP5_RED_CORRECTION_MASHOS_API_ENTRY_HEAD = (
    "e485f4a3c07ec0edeb2c248a74449b95f5017a58"
)
_STEP5_CARDINALITY_RECONCILIATION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_POSITIVE_"
    "BINDING_CARDINALITY_ASSERTION_AND_GREEN_DENOMINATOR_RECONCILIATION_"
    "READ_ONLY"
)
_STEP5_CARDINALITY_RED_CORRECTION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_POSITIVE_"
    "BINDING_CARDINALITY_ASSERTION_AND_GREEN_DENOMINATOR_RECONCILIATION_RED_"
    "CORRECTION_AND_REFREEZE_ONLY"
)
_STEP5_CARDINALITY_RECONCILIATION_COCOLON_ENTRY_HEAD = (
    "ad8095d2e3e8ed6eb642bb5f4c014484edbb608e"
)
_STEP5_CARDINALITY_RECONCILIATION_MASHOS_API_ENTRY_HEAD = (
    "d9a65dc7d5ee329ba3387c8659f435f3fb9f8e8d"
)
_STEP5_CARDINALITY_RED_CORRECTION_COCOLON_ENTRY_HEAD = (
    "db507d9737b078b97a69d5651e62ce43aff27ea1"
)
_STEP5_CARDINALITY_RED_CORRECTION_MASHOS_API_ENTRY_HEAD = (
    "d9a65dc7d5ee329ba3387c8659f435f3fb9f8e8d"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_BOUND_"
    "SELECTED_INTERSECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_RECONCILIATION_"
    "READ_ONLY"
)
_STEP5_BOUND_SELECTED_RED_CORRECTION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_BOUND_"
    "SELECTED_INTERSECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_RECONCILIATION_RED_"
    "CORRECTION_AND_REFREEZE_ONLY"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_COCOLON_ENTRY_HEAD = (
    "cad49a542aa60d2cbac9497d00c85cf7857a7316"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_MASHOS_API_ENTRY_HEAD = (
    "f2e73dfcc0b1f0091f077c41afbf9110e4b1b333"
)
_STEP5_BOUND_SELECTED_RED_CORRECTION_COCOLON_ENTRY_HEAD = (
    "d5892abc8ee50619e6d751f2e191c8a21cc0eff0"
)
_STEP5_BOUND_SELECTED_RED_CORRECTION_MASHOS_API_ENTRY_HEAD = (
    "f2e73dfcc0b1f0091f077c41afbf9110e4b1b333"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_CURRENT_AUTHORITY_BLOB = (
    "d15439587bd1a795f51b90fe7e65ca47bee0ff97"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_EXECUTION_PLAN_BLOB = (
    "eb72ef4dc0833173efa8f7e16a0a15a6a71ba029"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_RESULT_BLOB = (
    "1d5a91eb0d2f46563c54fc68f12b8f154f5ae2f3"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_RECEIPT_BLOB = (
    "3842046ec8d07cf1cfafb980bd1a1336445aff99"
)
_STEP5_BOUND_SELECTED_RECONCILIATION_HANDOFF_BLOB = (
    "d1dbb6c199486ad5c95f13b18142fec875e199b9"
)
_STEP5_BOUND_SELECTED_STOP_RESULT_BLOB = (
    "8c5254e267d9bddf10f681784ae0a901e2d4122f"
)
_STEP5_BOUND_SELECTED_STOP_RECEIPT_BLOB = (
    "a75164968cc49a073c0f1413792c4205c041a9a7"
)
_STEP5_BOUND_SELECTED_STOP_HANDOFF_BLOB = (
    "352ba688754e15e11cdd354623c2c84aff91d72e"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_UNMATCHED_"
    "OPTIONAL_SELECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_RECONCILIATION_"
    "READ_ONLY"
)
_STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_STEP5_CROSS_ROLE_UNMATCHED_"
    "OPTIONAL_SELECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_RECONCILIATION_RED_"
    "CORRECTION_AND_REFREEZE_ONLY"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_COCOLON_ENTRY_HEAD = (
    "a9be4960aca76427cb0dcd66730dce8c4a84d7dc"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_MASHOS_API_ENTRY_HEAD = (
    "b43f84a6b868e983a91c40e73735e03865806818"
)
_STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_COCOLON_ENTRY_HEAD = (
    "d2c50d5559ee69303c1e93ab6074eea40c25b0b7"
)
_STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_MASHOS_API_ENTRY_HEAD = (
    "b43f84a6b868e983a91c40e73735e03865806818"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_CURRENT_AUTHORITY_BLOB = (
    "8762def982bc16417b617faf45161d77b9e9bb01"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_EXECUTION_PLAN_BLOB = (
    "5a561b315426d6a3d67302619f740804fc6829aa"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_RESULT_BLOB = (
    "d624d99c81eb6234bab0807e623ef5b187b4d0c0"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_RECEIPT_BLOB = (
    "b6efcd9252b9b1a7e0cd09aad0491d1c58c9d57a"
)
_STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_HANDOFF_BLOB = (
    "223b6d4c82a71642476cdea1686bf37b4e23c8ad"
)
_STEP5_CARDINALITY_RECONCILIATION_CURRENT_AUTHORITY_BLOB = (
    "c298cd7759bc0e6df81b4be0231eafd048c41a2c"
)
_STEP5_CARDINALITY_RECONCILIATION_EXECUTION_PLAN_BLOB = (
    "201828886ccee706af38c42c1fceb6b848d53278"
)
_STEP5_CARDINALITY_RECONCILIATION_RESULT_BLOB = (
    "e0f7d270a265251cbf1204f784dd7c0e283b1946"
)
_STEP5_CARDINALITY_RECONCILIATION_RECEIPT_BLOB = (
    "0eee62cfcaece10c79ae0267d2f4df6d835c6a33"
)
_STEP5_CARDINALITY_RECONCILIATION_HANDOFF_BLOB = (
    "61f309fd4f96e164448ae685b5584f26b0a474a9"
)
_STEP5_RECONCILIATION_CURRENT_AUTHORITY_BLOB = (
    "662ba8d1bbc67a23dc155cfdd7e163aadbe8af7c"
)
_STEP5_RECONCILIATION_EXECUTION_PLAN_BLOB = (
    "748b787977e059d1c10b3d83b290429152a69ac3"
)
_STEP5_RECONCILIATION_RESULT_BLOB = (
    "691ab5bf5be7fd51b6a1d4683bd167ba2c5f37ac"
)
_STEP5_RECONCILIATION_RECEIPT_BLOB = (
    "a33d26fa141d059fedbe47b031927a1444ddcde4"
)
_STEP5_RECONCILIATION_HANDOFF_BLOB = (
    "d67f265ca06441009a064ac2179a76431774dd57"
)
_STEP5_PARENT_ADDENDUM_BLOB = (
    "df8d2e49287554b3da2867afde634b3afbec4a37"
)
_STEP5_PARENT_RECEIPT_BLOB = (
    "fdb64ba8ddab5b050556eb8025b77fd026c7aa50"
)
_STEP5_PARENT_HANDOFF_BLOB = (
    "ed9f5725ebd843bd258ef767dd0b7a7b74df8277"
)
_EXECUTION_AND_CLOSURE_PLAN_BLOB = (
    "4f4cdd8fd43af06844b8c303443c3635ce62d0ba"
)
_PREDECESSOR_CAUSAL_RED_RECEIPT_BLOB = (
    "e78d528600fef27ce3de52ef91c1118d6866d2ed"
)
_CROSS_ROLE_WITNESS_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_witness.v1"
)
_CROSS_ROLE_ADAPTER_VERSION = (
    "cocolon.emlis.nls_v3."
    "grounded_cross_role_semantic_restatement_adapter.20260723.v1"
)
_CROSS_ROLE_DEPTH_SCHEMA = (
    "cocolon.emlis.nls_v3.cross_role_semantic_depth_equivalence.v1"
)
_REFINED_SOURCE_SNAPSHOT_SCHEMA = (
    "cocolon.emlis.nls_v3.refined_source_snapshot.v2"
)
_CROSS_ROLE_PROOF_CODE = "TYPED_SEMANTIC_GRAPH_EQUIVALENCE"
_CROSS_ROLE_PROOF_BASIS = "COMPLETE_BODY_FREE_TYPED_COMPONENT_BIJECTION"
_CROSS_ROLE_EFFECT_SCOPE = "CONTENT_DEPTH_ONLY"
_CROSS_ROLE_CLOSURE_RULE = (
    "INCIDENT_RELATION_AND_UNKNOWN_AFFECTED_GRAPH_CLOSURE"
)
_CROSS_ROLE_FULL_REPLAY_POSITIVE = (
    "INDEPENDENT_ROLE_LOCAL_FULL_TYPED_GRAPH_REPLAY"
)
_CROSS_ROLE_NONIDENTICAL_POSITIVE = (
    "EXPLICIT_REFERENT_PREDICATE_CLOSED_SINGLE_COMPONENT_RESTATEMENT"
)
_CROSS_ROLE_DEFAULT_GRAPH_NEGATIVE = (
    "EMPTY_WITNESS_FALSE_COLLAPSE_NEGATIVE"
)
_STEP5_CARDINALITY_RULE = (
    "BINDING_COUNT_EQUALS_BOTH_ELIGIBLE_CLOSED_GRAPH_COMPONENT_COUNTS_"
    "AND_IS_POSITIVE"
)
_STEP5_BOUND_OBLIGATION_PRESENCE_RULE = (
    "EACH_ROLE_BOUND_OBLIGATION_SET_NONEMPTY_AND_SELECTED_INTERSECTION_"
    "NOT_REQUIRED"
)
_STEP5_UNMATCHED_OPTIONAL_SELECTION_RULE = (
    "CONTENT_DEPTH_ONLY_WITNESS_DOES_NOT_CHANGE_OPTIONAL_OBLIGATION_"
    "DECISION_STATUS"
)
_STEP5_AUTHORITATIVE_EXACT7_NODES = (
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
        "::test_recovery_epoch001_step5_cross_role_red_authority_and_surface_"
        "are_exact"
    ),
    (
        "ai/tests/test_emlis_ai_grounded_observation_semantic_restatement.py"
        "::test_cross_role_semantic_restatement_contract_false_collapse_and_"
        "tamper_red"
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
        "::test_recovery_epoch001_s5_cross_role_semantic_owner_is_resolved_or_"
        "red"
    ),
    (
        "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py"
        "::test_s4_cross_role_refined_snapshot_lineage_alias_and_tamper_red"
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
        "::test_recovery_epoch001_s5_cross_role_inventory_owner_is_resolved_"
        "or_red"
    ),
    (
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py"
        "::test_s5_cross_role_depth_noninflation_floor_and_effect_scope_red"
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
        "::test_recovery_epoch001_s5_cross_role_content_consumer_is_resolved_"
        "or_red"
    ),
)
_STEP5_CORRECTION_REFREEZE_RED_EXPECTATION = {
    "collected": 7,
    "lineage_passed": 1,
    "causal_failed": 6,
    "errors": 0,
    "unexpected": 0,
}
_STEP5_IMPLEMENTATION_GREEN_EXPECTATION = {
    "collected": 7,
    "passed": 7,
    "failed": 0,
    "errors": 0,
    "unexpected": 0,
}
_STEP5_UNMATCHED_OPTIONAL_RED_EXPECTATION = {
    "collected": 7,
    "passed": 5,
    "causal_failed": 2,
    "errors": 0,
    "unexpected": 0,
}

_HERE = Path(__file__).resolve()
_AI_ROOT = _HERE.parents[1]
_REPO_ROOT = _AI_ROOT.parent

_FUTURE_CORE_SURFACE = frozenset(
    {
        _CLOSURE_PATH,
        _RECEIPT_PATH,
        _SUCCESSOR_PATH,
        _INDEPENDENT_VERIFIER_PATH,
        "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py",
        "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py",
        "ai/tools/emlis_nls_v3_batch_run.py",
    }
)
_FUTURE_TEST_SURFACE = frozenset(
    {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py",
        "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py",
    }
)
_FUTURE_ADD_PATHS = frozenset(
    {
        _CLOSURE_PATH,
        _RECEIPT_PATH,
        _SUCCESSOR_PATH,
        _INDEPENDENT_VERIFIER_PATH,
    }
)
_STEP5_FUTURE_SOURCE_SURFACE = frozenset(
    {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ),
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py",
    }
)
_STEP5_RED_TEST_SURFACE = frozenset(
    {
        "ai/tests/test_emlis_ai_grounded_observation_semantic_restatement.py",
        "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py",
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        _THIS_PATH,
    }
)
_STEP5_BOUND_SELECTED_RED_CORRECTION_TEST_SURFACE = frozenset(
    {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        _THIS_PATH,
    }
)
_STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_TEST_SURFACE = frozenset(
    {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        _THIS_PATH,
    }
)
_STEP5_UNMATCHED_OPTIONAL_FUTURE_SOURCE_SURFACE = frozenset(
    {
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py",
    }
)
_STEP5_UNMATCHED_OPTIONAL_PROTECTED_SOURCE_SURFACE = frozenset(
    {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ),
    }
)
_MERGED_FUTURE_CORE_SURFACE = (
    _FUTURE_CORE_SURFACE | _STEP5_FUTURE_SOURCE_SURFACE
)
_MERGED_FUTURE_TEST_SURFACE = (
    _FUTURE_TEST_SURFACE | _STEP5_RED_TEST_SURFACE
)
_STEP5_PROTECTED_SURFACE = frozenset(
    {
        (
            "ai/services/ai_inference/"
            "emlis_ai_refined_source_partition_v3.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_nls_v3_artifact_contract.py"
        ),
    }
)
_CROSS_ROLE_NEGATIVE_CODES = frozenset(
    {
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_TYPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_ADAPTER_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_KIND_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_CODE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PROOF_BASIS_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH",
    }
)
_STEP5_PARENT_DESIGN_UNRESOLVED = frozenset(
    {
        "BODY_FREE_TYPED_CROSS_ROLE_EQUIVALENCE",
        "TRUSTED_CROSS_SOURCE_EQUIVALENCE_WITNESS",
    }
)
_STEP5_PREIMPLEMENTATION_SOURCE_BLOBS = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_observation_semantic_restatement_v3.py"
    ): "d28e2ab3086fa09a62c8dbdb3d887a7bff116c78",
    (
        "ai/services/ai_inference/"
        "emlis_ai_semantic_obligation_inventory_v3.py"
    ): "685ff7ccc8f5d7fd04dc9ed301b1649b608a868a",
    (
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
    ): "7172a628f5ecdfb6ba888c36d42a6a62d0d7c22e",
}
_STEP5_PREIMPLEMENTATION_SOURCE_SHA256 = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_observation_semantic_restatement_v3.py"
    ): "a014e942b34c2c8f2a424dda0b0ecd30cb34ff99112e813d2182ad84d34b65fc",
    (
        "ai/services/ai_inference/"
        "emlis_ai_semantic_obligation_inventory_v3.py"
    ): "0a66adbf3163cf3aad1d4454a8a26aa6292284911b4bd5ba1825e0780e3aa2bc",
    (
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
    ): "ec2ccfc92c5566e8ec780e67db54b4a4c620a9334f2ab2cac91a314550f43f0d",
}
_STEP5_PREIMPLEMENTATION_SOURCE_DISPOSITION = (
    "HISTORICAL_PREIMPLEMENTATION_NOT_FUTURE_RESULT"
)
_STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_SOURCE_BLOBS = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_observation_semantic_restatement_v3.py"
    ): "cd2caeac0dfa4b502c798e1e5f65653033c96e2c",
    (
        "ai/services/ai_inference/"
        "emlis_ai_semantic_obligation_inventory_v3.py"
    ): "241d38331b00fd6c7bd17d4c8a30b6b52b0c3f69",
    (
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
    ): "6096dd41e46fe9d9abc7695b49b3125b2f87cea1",
}
_STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_SOURCE_SHA256 = {
    (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_observation_semantic_restatement_v3.py"
    ): "348003adbe7991de1717a8a2a7ca9d26a04e7f42caccdef2e4a0f31634f171b6",
    (
        "ai/services/ai_inference/"
        "emlis_ai_semantic_obligation_inventory_v3.py"
    ): "ddc42e6f30c46876b4ccc6c7f936c6cc7dcc6f394cbc2d9825694c7617b465f9",
    (
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
    ): "3c9c51a9e514169a1b17d408329b3d2d526bab08b8663e0fb2606ae358eec3bb",
}
_STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_TEST_BLOBS = {
    "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": (
        "f2e702a75c2294d689e3f55a6b7b7b8da149fa2a"
    ),
    _THIS_PATH: "51454fe9d1f0f6267d04e5f9872689be0072bed7",
}
_STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_TEST_SHA256 = {
    "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": (
        "cb55178ca5df4746074b7d1c242d46463c5335d7d0a7962900933e5c11cf62f9"
    ),
    _THIS_PATH: (
        "0ddbe5c7e1aef2f56276775694e0b016c5902e367fa1de98e7848cc6ab6e3cb1"
    ),
}

_PROTECTED_SHA256 = {
    "ai/services/ai_inference/emlis_ai_step9_dependency_manifest_v3.py": (
        "19a21d5853c44130c2c874e8b9c6bbbc0a1fc79591c529fb060e7c1e3cd7742e"
    ),
    "ai/services/ai_inference/emlis_ai_step9_artifact_contract_v3.py": (
        "216d6d1105a158dc9807d6dada006cff13050b2e2a7b133a31bdf479b5ab2d56"
    ),
    "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py": (
        "ce2a9818b46196fa5966a2e13394cc1b51089aab664e6660e86c4526f9050c51"
    ),
    "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py": (
        "4fa8770d82273b328e0a968b1315ec68f6c57cdf4aec576dbc36434f5453833d"
    ),
    "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py": (
        "e1e62049fc521658597124832d700a4842aca995ffd9ae38f8db583b7ba4f13f"
    ),
    "ai/services/ai_inference/emlis_ai_step10_dependency_manifest_v3.py": (
        "3bc1311c264cbbae71e69c643d055575e9b80c58b71d321ff28e744ad0ee090c"
    ),
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
    ): "ec6007f5b35fdcc0ec8a330822e4fe9086884dada2415e8557d7f314e2a65127",
    "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py": (
        "fffda42687a77f5f2c1f83d39c96cbf4eb7099438b8c0f7179dacdf5b02ceb14"
    ),
    "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py": (
        "652bd446bd33995d9575b6db60f765caa97305b98d439d294de33bc569ea9f80"
    ),
    "ai/tests/fixtures/emlis_nls_v3_s0_boundary_20260714.json": (
        "57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024"
    ),
    "ai/tests/fixtures/emlis_nls_v3_s1_baseline_receipt_20260714.json": (
        "669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518"
    ),
    "ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json": (
        "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6"
    ),
    "ai/services/ai_inference/emlis_ai_reply_service.py": (
        "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a"
    ),
    "ai/services/ai_inference/emlis_ai_step11_cycle_evidence_v3.py": (
        "e9f77f7411b581e96a7035d05aa3a50eb4628cbba37a02b0786a0d35b818d43d"
    ),
}

_CURRENT_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_STOPPED_V2_ANCHORS = (
    "ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_reception_candidate_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_reception_candidate_selector_v2.py",
)

_STEP_SEEDS: dict[int, frozenset[str]] = {
    0: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "ai/tests/test_emlis_nls_v3_s0_s1.py",
            "ai/tests/fixtures/emlis_nls_v3_s0_boundary_20260714.json",
            *_CURRENT_OWNER_PATHS,
            *_STOPPED_V2_ANCHORS,
        }
    ),
    1: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "ai/tests/test_emlis_nls_v3_s0_s1.py",
            "ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json",
            "ai/tests/fixtures/emlis_nls_v3_s1_baseline_receipt_20260714.json",
            *_CURRENT_OWNER_PATHS,
            "ai/services/ai_inference/api_emotion_submit.py",
            "ai/services/ai_inference/emotion_submit_service.py",
            "ai/services/ai_inference/emlis_ai_current_input_bundle.py",
            "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
            "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
            "ai/services/ai_inference/emlis_ai_perspective_observers.py",
            "ai/services/ai_inference/emlis_ai_observation_integrator_service.py",
            "ai/services/ai_inference/emlis_ai_safety_triage.py",
        }
    ),
    2: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py",
            "ai/tests/test_emlis_nls_v3_s2_sample_registry.py",
            "ai/tests/schemas/emlis_nls_v3_sample_case_v1.schema.json",
            "ai/tests/schemas/emlis_nls_v3_coverage_matrix_v1.schema.json",
            "ai/tests/schemas/emlis_nls_v3_sample_batch_manifest_v1.schema.json",
            "ai/tests/schemas/emlis_nls_v3_corpus_registry_v1.schema.json",
            "ai/tests/fixtures/emlis_nls_v3_s2_corpus_registry_20260714.json",
            "ai/tests/fixtures/emlis_nls_v3/contract/valid_v1.jsonl",
            "ai/tests/fixtures/emlis_nls_v3/contract/invalid_v1.jsonl",
            "ai/tests/fixtures/emlis_nls_v3/contract/legacy_v1.jsonl",
        }
    ),
    3: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py",
            "ai/tests/schemas/emlis_nls_v3_case_evidence_receipt_v2.schema.json",
            (
                "ai/tests/fixtures/emlis_nls_v3/contract/"
                "step3_valid_artifacts_v1.json"
            ),
            "ai/tests/fixtures/emlis_nls_v3_s3_red_attack_catalog_20260715.json",
            "ai/tests/fixtures/emlis_nls_v3_s3_contract_receipt_20260715.json",
        }
    ),
    4: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_semantic_obligation_inventory_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_grounded_observation_semantic_restatement_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
            "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
            "ai/services/ai_inference/emlis_ai_observation_stage_context_v3.py",
            "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py",
        }
    ),
    5: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_semantic_obligation_inventory_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py",
            "ai/services/ai_inference/emlis_ai_observation_stage_context_v3.py",
            "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        }
    ),
    6: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py",
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py",
        }
    ),
    7: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py",
            "ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py",
            "ai/services/ai_inference/emlis_ai_surface_grammar_catalog_v3.py",
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py",
        }
    ),
    8: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_body_semantic_atom_parser_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_independent_semantic_matcher_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_step8_artifact_contract_v3.py",
            "ai/services/ai_inference/emlis_ai_surface_grammar_catalog_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_surface_grammar_catalog_v3_step8.py"
            ),
            "ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py",
        }
    ),
    9: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_step9_dependency_manifest_v3.py",
            "ai/services/ai_inference/emlis_ai_step9_artifact_contract_v3.py",
            "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py",
            "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py",
            "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py",
            _SUCCESSOR_PATH,
            "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py",
        }
    ),
    10: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py",
            "ai/services/ai_inference/emlis_ai_reply_service.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_step10_app_reachable_contract_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py",
            "ai/tools/emlis_nls_v3_batch_run.py",
            "ai/tools/emlis_nls_v3_cumulative_regression.py",
            "ai/tools/emlis_nls_v3_output_diff.py",
            "ai/tools/emlis_nls_v3_receipt_verify.py",
            "ai/tests/schemas/emlis_nls_v3_case_evidence_receipt_v3.schema.json",
            "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py",
        }
    ),
}
_CROSS_STEP_SEEDS = frozenset(
    {
        _CLOSURE_PATH,
        _RECEIPT_PATH,
        _INDEPENDENT_VERIFIER_PATH,
        _THIS_PATH,
        "ai/tests/conftest.py",
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
        ),
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py",
    }
)

_CLOSURE_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_CANDIDATE_IDENTITY_INVALID",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_SEED_MISSING",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_FILE_MISSING",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_EXTRA_FILE",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_GIT_BLOB_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_EXISTING_LOCAL_IMPORT_UNLISTED",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_EDGE_MISSING",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_EDGE_TARGET_UNRESOLVED",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_ROLE_BINDING_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_EDGE",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_CUE_INGRESS",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_PRIVATE_BODY_INGRESS",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_SELF_NORMALIZATION_SCOPE_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_START_END_DRIFT",
    }
)
_RECEIPT_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_LINEAGE_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_REWRITE_FORBIDDEN",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_AS_CURRENT_FORBIDDEN",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_CURRENT_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ACTUAL_OWNER_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STRICT_CONTRACT_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_POSITIVE_PROOF_INVALID",
        (
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "INDEPENDENT_NEGATIVE_PROOF_INVALID"
        ),
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ARTIFACT_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_PARENT_CHAIN_INVALID",
        (
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "SOURCE_OR_VIEW_ROOT_MISMATCH"
        ),
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STOP_NOT_FALSE",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_NEXT_AUTHORITY_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_BODY_FREE_REQUIRED",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HASH_MISMATCH",
    }
)
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

_CLOSURE_OWNER_RED = (
    "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_OWNER_NOT_PROVED"
)
_CLOSURE_VERIFIER_RED = (
    "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_INDEPENDENT_VERIFIER_NOT_PROVED"
)
_RECEIPT_OWNER_RED = (
    "RECOVERY_EPOCH001_CURRENT_COMPLETION_RECEIPT_OWNER_NOT_PROVED"
)
_STEP5_PARENT_DESIGN_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_REQUIRED"
)
_STEP5_CROSS_ROLE_OWNER_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_SEMANTIC_RESTATEMENT_OWNER_NOT_PROVED"
)
_STEP5_CROSS_ROLE_INVENTORY_OWNER_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_REFINED_SNAPSHOT_BINDING_NOT_PROVED"
)
_STEP5_CROSS_ROLE_CONTENT_CONSUMER_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_DEPTH_NONINFLATION_NOT_PROVED"
)
_STEP5_CROSS_ROLE_UNMATCHED_OPTIONAL_SELECTION_RED = (
    "RECOVERY_EPOCH001_S5_CROSS_ROLE_UNMATCHED_OPTIONAL_SELECTION_POLICY_"
    "NOT_PROVED"
)
_STEP9_SUCCESSOR_RED = (
    "RECOVERY_EPOCH001_STEP9_STANDALONE_SUCCESSOR_OWNER_NOT_PROVED"
)
_STEP10_SINGLE_GRAPH_RED = (
    "RECOVERY_EPOCH001_STEP10_SAME_GRAPH_NO_LOCAL_CLONE_NOT_PROVED"
)
_STEP10_START_END_RED = (
    "RECOVERY_EPOCH001_STEP10_CLOSURE_START_END_BINDING_NOT_PROVED"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module_or_red(module_name: str, red_code: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            pytest.fail(red_code, pytrace=False)
        raise


def _tool_module_or_red(path: str, red_code: str) -> ModuleType:
    absolute = _REPO_ROOT / path
    if not absolute.is_file():
        pytest.fail(red_code, pytrace=False)
    spec = importlib.util.spec_from_file_location(
        "emlis_nls_v3_recovery_epoch001_closure_receipt_verify",
        absolute,
    )
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


def test_recovery_epoch001_candidate_identity_surface_and_history_are_exact() -> None:
    assert _AUTHORITY.endswith("REMEDIATION_RED_FREEZE_ONLY")
    assert _SOURCE_PIN == "bd62ef0eec2348e3b190ec2a39c3794886ccd10d"
    assert _COCOLON_PIN == "3cb7867c3f8cbe39ee38ffe5c55179df81b5b0fa"
    assert _RECOVERY_CANDIDATE == "nls_v3_rc_0034"
    assert _RECOVERY_SCOPE.endswith("CANDIDATE_ONLY")
    assert _RECOVERY_DISPOSITION.endswith("NOT_CYCLE_ACCEPTANCE")
    assert _RC0032_DISPOSITION == "FAILED_PREREQUISITE_CANDIDATE_HISTORY_ONLY"
    assert _RC0033_DISPOSITION == "PREEXISTING_SYNTHETIC_LATER_RC_ONLY"

    production_occurrences: set[str] = set()
    for root in (_AI_ROOT / "services", _AI_ROOT / "tools"):
        for path in root.rglob("*.py"):
            if _RECOVERY_CANDIDATE in path.read_text(encoding="utf-8"):
                production_occurrences.add(
                    path.relative_to(_REPO_ROOT).as_posix()
                )
    assert production_occurrences <= _FUTURE_CORE_SURFACE

    synthetic_path = (
        _AI_ROOT / "tests" / "test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py"
    )
    assert synthetic_path.read_text(encoding="utf-8").count(
        "nls_v3_rc_0033"
    ) == 4


def test_recovery_epoch001_future_core_and_test_surface_are_exact() -> None:
    assert len(_FUTURE_CORE_SURFACE) == 7
    assert len(_FUTURE_TEST_SURFACE) == 3
    assert len(_FUTURE_ADD_PATHS) == 4
    assert _FUTURE_ADD_PATHS <= _FUTURE_CORE_SURFACE
    assert not (_FUTURE_CORE_SURFACE & set(_PROTECTED_SHA256))
    assert not (_FUTURE_TEST_SURFACE & set(_PROTECTED_SHA256))
    assert _STEP5_PARENT_DESIGN_UNRESOLVED == {
        "BODY_FREE_TYPED_CROSS_ROLE_EQUIVALENCE",
        "TRUSTED_CROSS_SOURCE_EQUIVALENCE_WITNESS",
    }
    assert not any(
        marker in path
        for path in _FUTURE_CORE_SURFACE | _FUTURE_TEST_SURFACE
        for marker in (
            "api_emotion_submit.py",
            "emlis_ai_reply_service.py",
            "emlis_ai_step11_cycle_evidence_v3.py",
            "fixtures/",
            "schemas/",
            "generated/",
        )
    )
    for path in _FUTURE_CORE_SURFACE - _FUTURE_ADD_PATHS:
        assert (_REPO_ROOT / path).is_file(), path
    add_presence = {
        path: (_REPO_ROOT / path).is_file() for path in _FUTURE_ADD_PATHS
    }
    assert set(add_presence.values()) in ({False}, {True})


def test_recovery_epoch001_step5_cross_role_red_authority_and_surface_are_exact() -> None:
    assert _STEP5_RED_AUTHORITY.endswith("REMEDIATION_RED_FREEZE_ONLY")
    assert _STEP5_RECONCILIATION_AUTHORITY.endswith(
        "POSITIVE_INPUT_CONTRACT_RECONCILIATION_READ_ONLY"
    )
    assert _STEP5_RED_CORRECTION_AUTHORITY.endswith(
        "RED_CORRECTION_AND_REFREEZE_ONLY"
    )
    assert _STEP5_CARDINALITY_RECONCILIATION_AUTHORITY.endswith(
        "BINDING_CARDINALITY_ASSERTION_AND_GREEN_DENOMINATOR_"
        "RECONCILIATION_READ_ONLY"
    )
    assert _STEP5_CARDINALITY_RED_CORRECTION_AUTHORITY.endswith(
        "BINDING_CARDINALITY_ASSERTION_AND_GREEN_DENOMINATOR_"
        "RECONCILIATION_RED_CORRECTION_AND_REFREEZE_ONLY"
    )
    assert _STEP5_BOUND_SELECTED_RECONCILIATION_AUTHORITY.endswith(
        "BOUND_SELECTED_INTERSECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_"
        "RECONCILIATION_READ_ONLY"
    )
    assert _STEP5_BOUND_SELECTED_RED_CORRECTION_AUTHORITY.endswith(
        "BOUND_SELECTED_INTERSECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_"
        "RECONCILIATION_RED_CORRECTION_AND_REFREEZE_ONLY"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_AUTHORITY.endswith(
        "UNMATCHED_OPTIONAL_SELECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_"
        "RECONCILIATION_READ_ONLY"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_AUTHORITY.endswith(
        "UNMATCHED_OPTIONAL_SELECTION_AND_CONTENT_DEPTH_ONLY_CONTRACT_"
        "RECONCILIATION_RED_CORRECTION_AND_REFREEZE_ONLY"
    )
    assert _STEP5_RED_COCOLON_ENTRY_HEAD == (
        "ec66fdbadef3ebee4b5a531f77391252146b2e4e"
    )
    assert _STEP5_RED_MASHOS_API_ENTRY_HEAD == (
        "21600c3d07b4f3d870beb3acb0bd78bf3e898f36"
    )
    assert _STEP5_RED_CORRECTION_COCOLON_ENTRY_HEAD == (
        "3bd0bcb8077ecaab07b04e913bdffaa2f66f3c7f"
    )
    assert _STEP5_RED_CORRECTION_MASHOS_API_ENTRY_HEAD == (
        "e485f4a3c07ec0edeb2c248a74449b95f5017a58"
    )
    assert _STEP5_CARDINALITY_RECONCILIATION_COCOLON_ENTRY_HEAD == (
        "ad8095d2e3e8ed6eb642bb5f4c014484edbb608e"
    )
    assert _STEP5_CARDINALITY_RECONCILIATION_MASHOS_API_ENTRY_HEAD == (
        "d9a65dc7d5ee329ba3387c8659f435f3fb9f8e8d"
    )
    assert _STEP5_CARDINALITY_RED_CORRECTION_COCOLON_ENTRY_HEAD == (
        "db507d9737b078b97a69d5651e62ce43aff27ea1"
    )
    assert _STEP5_CARDINALITY_RED_CORRECTION_MASHOS_API_ENTRY_HEAD == (
        "d9a65dc7d5ee329ba3387c8659f435f3fb9f8e8d"
    )
    assert _STEP5_BOUND_SELECTED_RECONCILIATION_COCOLON_ENTRY_HEAD == (
        "cad49a542aa60d2cbac9497d00c85cf7857a7316"
    )
    assert _STEP5_BOUND_SELECTED_RECONCILIATION_MASHOS_API_ENTRY_HEAD == (
        "f2e73dfcc0b1f0091f077c41afbf9110e4b1b333"
    )
    assert _STEP5_BOUND_SELECTED_RED_CORRECTION_COCOLON_ENTRY_HEAD == (
        "d5892abc8ee50619e6d751f2e191c8a21cc0eff0"
    )
    assert _STEP5_BOUND_SELECTED_RED_CORRECTION_MASHOS_API_ENTRY_HEAD == (
        "f2e73dfcc0b1f0091f077c41afbf9110e4b1b333"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_COCOLON_ENTRY_HEAD == (
        "a9be4960aca76427cb0dcd66730dce8c4a84d7dc"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_MASHOS_API_ENTRY_HEAD == (
        "b43f84a6b868e983a91c40e73735e03865806818"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_COCOLON_ENTRY_HEAD == (
        "d2c50d5559ee69303c1e93ab6074eea40c25b0b7"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_MASHOS_API_ENTRY_HEAD == (
        "b43f84a6b868e983a91c40e73735e03865806818"
    )
    assert {
        _STEP5_PARENT_ADDENDUM_BLOB,
        _STEP5_PARENT_RECEIPT_BLOB,
        _STEP5_PARENT_HANDOFF_BLOB,
        _EXECUTION_AND_CLOSURE_PLAN_BLOB,
        _PREDECESSOR_CAUSAL_RED_RECEIPT_BLOB,
    } == {
        "df8d2e49287554b3da2867afde634b3afbec4a37",
        "fdb64ba8ddab5b050556eb8025b77fd026c7aa50",
        "ed9f5725ebd843bd258ef767dd0b7a7b74df8277",
        "4f4cdd8fd43af06844b8c303443c3635ce62d0ba",
        "e78d528600fef27ce3de52ef91c1118d6866d2ed",
    }
    assert {
        _STEP5_RECONCILIATION_CURRENT_AUTHORITY_BLOB,
        _STEP5_RECONCILIATION_EXECUTION_PLAN_BLOB,
        _STEP5_RECONCILIATION_RESULT_BLOB,
        _STEP5_RECONCILIATION_RECEIPT_BLOB,
        _STEP5_RECONCILIATION_HANDOFF_BLOB,
    } == {
        "662ba8d1bbc67a23dc155cfdd7e163aadbe8af7c",
        "748b787977e059d1c10b3d83b290429152a69ac3",
        "691ab5bf5be7fd51b6a1d4683bd167ba2c5f37ac",
        "a33d26fa141d059fedbe47b031927a1444ddcde4",
        "d67f265ca06441009a064ac2179a76431774dd57",
    }
    assert {
        _STEP5_CARDINALITY_RECONCILIATION_CURRENT_AUTHORITY_BLOB,
        _STEP5_CARDINALITY_RECONCILIATION_EXECUTION_PLAN_BLOB,
        _STEP5_CARDINALITY_RECONCILIATION_RESULT_BLOB,
        _STEP5_CARDINALITY_RECONCILIATION_RECEIPT_BLOB,
        _STEP5_CARDINALITY_RECONCILIATION_HANDOFF_BLOB,
    } == {
        "c298cd7759bc0e6df81b4be0231eafd048c41a2c",
        "201828886ccee706af38c42c1fceb6b848d53278",
        "e0f7d270a265251cbf1204f784dd7c0e283b1946",
        "0eee62cfcaece10c79ae0267d2f4df6d835c6a33",
        "61f309fd4f96e164448ae685b5584f26b0a474a9",
    }
    assert {
        _STEP5_BOUND_SELECTED_RECONCILIATION_CURRENT_AUTHORITY_BLOB,
        _STEP5_BOUND_SELECTED_RECONCILIATION_EXECUTION_PLAN_BLOB,
        _STEP5_BOUND_SELECTED_RECONCILIATION_RESULT_BLOB,
        _STEP5_BOUND_SELECTED_RECONCILIATION_RECEIPT_BLOB,
        _STEP5_BOUND_SELECTED_RECONCILIATION_HANDOFF_BLOB,
        _STEP5_BOUND_SELECTED_STOP_RESULT_BLOB,
        _STEP5_BOUND_SELECTED_STOP_RECEIPT_BLOB,
        _STEP5_BOUND_SELECTED_STOP_HANDOFF_BLOB,
    } == {
        "d15439587bd1a795f51b90fe7e65ca47bee0ff97",
        "eb72ef4dc0833173efa8f7e16a0a15a6a71ba029",
        "1d5a91eb0d2f46563c54fc68f12b8f154f5ae2f3",
        "3842046ec8d07cf1cfafb980bd1a1336445aff99",
        "d1dbb6c199486ad5c95f13b18142fec875e199b9",
        "8c5254e267d9bddf10f681784ae0a901e2d4122f",
        "a75164968cc49a073c0f1413792c4205c041a9a7",
        "352ba688754e15e11cdd354623c2c84aff91d72e",
    }
    assert {
        _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_CURRENT_AUTHORITY_BLOB,
        _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_EXECUTION_PLAN_BLOB,
        _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_RESULT_BLOB,
        _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_RECEIPT_BLOB,
        _STEP5_UNMATCHED_OPTIONAL_RECONCILIATION_HANDOFF_BLOB,
    } == {
        "8762def982bc16417b617faf45161d77b9e9bb01",
        "5a561b315426d6a3d67302619f740804fc6829aa",
        "d624d99c81eb6234bab0807e623ef5b187b4d0c0",
        "b6efcd9252b9b1a7e0cd09aad0491d1c58c9d57a",
        "223b6d4c82a71642476cdea1686bf37b4e23c8ad",
    }
    assert _CROSS_ROLE_WITNESS_SCHEMA.endswith(
        "grounded_cross_role_semantic_restatement_witness.v1"
    )
    assert _CROSS_ROLE_ADAPTER_VERSION.endswith(
        "grounded_cross_role_semantic_restatement_adapter.20260723.v1"
    )
    assert _CROSS_ROLE_DEPTH_SCHEMA.endswith(
        "cross_role_semantic_depth_equivalence.v1"
    )
    assert _REFINED_SOURCE_SNAPSHOT_SCHEMA.endswith(
        "refined_source_snapshot.v2"
    )
    assert _CROSS_ROLE_PROOF_CODE == "TYPED_SEMANTIC_GRAPH_EQUIVALENCE"
    assert _CROSS_ROLE_PROOF_BASIS == (
        "COMPLETE_BODY_FREE_TYPED_COMPONENT_BIJECTION"
    )
    assert _CROSS_ROLE_EFFECT_SCOPE == "CONTENT_DEPTH_ONLY"
    assert _CROSS_ROLE_CLOSURE_RULE.endswith("AFFECTED_GRAPH_CLOSURE")
    assert _CROSS_ROLE_FULL_REPLAY_POSITIVE.endswith(
        "FULL_TYPED_GRAPH_REPLAY"
    )
    assert _CROSS_ROLE_NONIDENTICAL_POSITIVE.endswith(
        "CLOSED_SINGLE_COMPONENT_RESTATEMENT"
    )
    assert _CROSS_ROLE_DEFAULT_GRAPH_NEGATIVE.startswith("EMPTY_WITNESS_")
    assert _STEP5_CARDINALITY_RULE == (
        "BINDING_COUNT_EQUALS_BOTH_ELIGIBLE_CLOSED_GRAPH_COMPONENT_COUNTS_"
        "AND_IS_POSITIVE"
    )
    assert _STEP5_BOUND_OBLIGATION_PRESENCE_RULE == (
        "EACH_ROLE_BOUND_OBLIGATION_SET_NONEMPTY_AND_SELECTED_INTERSECTION_"
        "NOT_REQUIRED"
    )
    assert _STEP5_UNMATCHED_OPTIONAL_SELECTION_RULE == (
        "CONTENT_DEPTH_ONLY_WITNESS_DOES_NOT_CHANGE_OPTIONAL_OBLIGATION_"
        "DECISION_STATUS"
    )
    assert _STEP5_AUTHORITATIVE_EXACT7_NODES == (
        (
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_"
            "red.py::test_recovery_epoch001_step5_cross_role_red_authority_and_"
            "surface_are_exact"
        ),
        (
            "ai/tests/"
            "test_emlis_ai_grounded_observation_semantic_restatement.py"
            "::test_cross_role_semantic_restatement_contract_false_collapse_"
            "and_tamper_red"
        ),
        (
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_"
            "red.py::test_recovery_epoch001_s5_cross_role_semantic_owner_is_"
            "resolved_or_red"
        ),
        (
            "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py"
            "::test_s4_cross_role_refined_snapshot_lineage_alias_and_tamper_"
            "red"
        ),
        (
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_"
            "red.py::test_recovery_epoch001_s5_cross_role_inventory_owner_is_"
            "resolved_or_red"
        ),
        (
            "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py"
            "::test_s5_cross_role_depth_noninflation_floor_and_effect_scope_"
            "red"
        ),
        (
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_"
            "red.py::test_recovery_epoch001_s5_cross_role_content_consumer_is_"
            "resolved_or_red"
        ),
    )
    assert _STEP5_CORRECTION_REFREEZE_RED_EXPECTATION == {
        "collected": 7,
        "lineage_passed": 1,
        "causal_failed": 6,
        "errors": 0,
        "unexpected": 0,
    }
    assert _STEP5_IMPLEMENTATION_GREEN_EXPECTATION == {
        "collected": 7,
        "passed": 7,
        "failed": 0,
        "errors": 0,
        "unexpected": 0,
    }
    assert _STEP5_UNMATCHED_OPTIONAL_RED_EXPECTATION == {
        "collected": 7,
        "passed": 5,
        "causal_failed": 2,
        "errors": 0,
        "unexpected": 0,
    }

    assert len(_STEP5_FUTURE_SOURCE_SURFACE) == 3
    assert len(_STEP5_RED_TEST_SURFACE) == 4
    assert _STEP5_BOUND_SELECTED_RED_CORRECTION_TEST_SURFACE == {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        _THIS_PATH,
    }
    assert (
        _STEP5_BOUND_SELECTED_RED_CORRECTION_TEST_SURFACE
        <= _STEP5_RED_TEST_SURFACE
    )
    assert not (
        _STEP5_BOUND_SELECTED_RED_CORRECTION_TEST_SURFACE
        & _STEP5_FUTURE_SOURCE_SURFACE
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_TEST_SURFACE == {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
        _THIS_PATH,
    }
    assert (
        _STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_TEST_SURFACE
        == _STEP5_BOUND_SELECTED_RED_CORRECTION_TEST_SURFACE
    )
    assert _STEP5_UNMATCHED_OPTIONAL_FUTURE_SOURCE_SURFACE == {
        "ai/services/ai_inference/emlis_ai_content_selection_v3.py",
    }
    assert _STEP5_UNMATCHED_OPTIONAL_PROTECTED_SOURCE_SURFACE == {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ),
    }
    assert not (
        _STEP5_UNMATCHED_OPTIONAL_RED_CORRECTION_TEST_SURFACE
        & _STEP5_UNMATCHED_OPTIONAL_FUTURE_SOURCE_SURFACE
    )
    assert not (
        _STEP5_UNMATCHED_OPTIONAL_PROTECTED_SOURCE_SURFACE
        & _STEP5_UNMATCHED_OPTIONAL_FUTURE_SOURCE_SURFACE
    )
    assert len(_MERGED_FUTURE_CORE_SURFACE) == 10
    assert len(_MERGED_FUTURE_TEST_SURFACE) == 6
    assert _STEP5_FUTURE_SOURCE_SURFACE <= _MERGED_FUTURE_CORE_SURFACE
    assert _STEP5_RED_TEST_SURFACE <= _MERGED_FUTURE_TEST_SURFACE
    assert not (_STEP5_FUTURE_SOURCE_SURFACE & _STEP5_RED_TEST_SURFACE)
    assert not (_STEP5_PROTECTED_SURFACE & _MERGED_FUTURE_CORE_SURFACE)
    assert not (_STEP5_PROTECTED_SURFACE & _MERGED_FUTURE_TEST_SURFACE)
    assert all(
        (_REPO_ROOT / path).is_file()
        for path in _STEP5_FUTURE_SOURCE_SURFACE | _STEP5_RED_TEST_SURFACE
    )
    assert set(_STEP5_PREIMPLEMENTATION_SOURCE_BLOBS) == (
        _STEP5_FUTURE_SOURCE_SURFACE
    )
    assert set(_STEP5_PREIMPLEMENTATION_SOURCE_SHA256) == (
        _STEP5_FUTURE_SOURCE_SURFACE
    )
    assert _STEP5_PREIMPLEMENTATION_SOURCE_BLOBS == {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ): "d28e2ab3086fa09a62c8dbdb3d887a7bff116c78",
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ): "685ff7ccc8f5d7fd04dc9ed301b1649b608a868a",
        (
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
        ): "7172a628f5ecdfb6ba888c36d42a6a62d0d7c22e",
    }
    assert _STEP5_PREIMPLEMENTATION_SOURCE_SHA256 == {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ): (
            "a014e942b34c2c8f2a424dda0b0ecd30cb34ff99112e813d2182ad84d34b65fc"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ): (
            "0a66adbf3163cf3aad1d4454a8a26aa6292284911b4bd5ba1825e0780e3aa2bc"
        ),
        (
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
        ): (
            "ec2ccfc92c5566e8ec780e67db54b4a4c620a9334f2ab2cac91a314550f43f0d"
        ),
    }
    assert _STEP5_PREIMPLEMENTATION_SOURCE_DISPOSITION == (
        "HISTORICAL_PREIMPLEMENTATION_NOT_FUTURE_RESULT"
    )
    assert set(_STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_SOURCE_BLOBS) == (
        _STEP5_FUTURE_SOURCE_SURFACE
    )
    assert set(_STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_SOURCE_SHA256) == (
        _STEP5_FUTURE_SOURCE_SURFACE
    )
    assert _STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_SOURCE_BLOBS == {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ): "cd2caeac0dfa4b502c798e1e5f65653033c96e2c",
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ): "241d38331b00fd6c7bd17d4c8a30b6b52b0c3f69",
        (
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
        ): "6096dd41e46fe9d9abc7695b49b3125b2f87cea1",
    }
    assert _STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_SOURCE_SHA256 == {
        (
            "ai/services/ai_inference/"
            "emlis_ai_grounded_observation_semantic_restatement_v3.py"
        ): (
            "348003adbe7991de1717a8a2a7ca9d26a04e7f42caccdef2e4a0f31634f171b6"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_semantic_obligation_inventory_v3.py"
        ): (
            "ddc42e6f30c46876b4ccc6c7f936c6cc7dcc6f394cbc2d9825694c7617b465f9"
        ),
        (
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
        ): (
            "3c9c51a9e514169a1b17d408329b3d2d526bab08b8663e0fb2606ae358eec3bb"
        ),
    }
    assert _STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_TEST_BLOBS == {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": (
            "f2e702a75c2294d689e3f55a6b7b7b8da149fa2a"
        ),
        _THIS_PATH: "51454fe9d1f0f6267d04e5f9872689be0072bed7",
    }
    assert _STEP5_UNMATCHED_OPTIONAL_RED_ENTRY_TEST_SHA256 == {
        "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": (
            "cb55178ca5df4746074b7d1c242d46463c5335d7d0a7962900933e5c11cf62f9"
        ),
        _THIS_PATH: (
            "0ddbe5c7e1aef2f56276775694e0b016c5902e367fa1de98e7848cc6ab6e3cb1"
        ),
    }

    assert len(_CROSS_ROLE_NEGATIVE_CODES) == 18
    assert all(
        code.startswith("CROSS_ROLE_SEMANTIC_RESTATEMENT_")
        for code in _CROSS_ROLE_NEGATIVE_CODES
    )
    assert {
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_PLAN_BINDING_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_SOURCE_WITNESS_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ROLE_PAIR_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_UNRESOLVED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_COMPONENT_KIND_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_AMBIGUOUS",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_GRAPH_MISMATCH",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_EFFECT_SCOPE_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_DEPTH_CONTRACT_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_BODY_FREE_REQUIRED",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_ORDER_INVALID",
        "CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_HASH_MISMATCH",
    } <= _CROSS_ROLE_NEGATIVE_CODES


def test_recovery_epoch001_step_seed_roots_are_exact_and_resolvable() -> None:
    assert set(_STEP_SEEDS) == set(range(11))
    assert all(_STEP_SEEDS[step] for step in range(11))
    assert _SUCCESSOR_PATH in _STEP_SEEDS[9]
    assert {
        "ai/services/ai_inference/emlis_ai_surface_grammar_catalog_v3.py",
        (
            "ai/services/ai_inference/"
            "emlis_ai_surface_grammar_catalog_v3_step8.py"
        ),
    } <= (_STEP_SEEDS[7] | _STEP_SEEDS[8])
    assert (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_observation_semantic_restatement_v3.py"
    ) in _STEP_SEEDS[4]
    assert {_CLOSURE_PATH, _RECEIPT_PATH, _INDEPENDENT_VERIFIER_PATH} <= (
        _CROSS_STEP_SEEDS
    )

    all_seeds = set().union(*_STEP_SEEDS.values(), _CROSS_STEP_SEEDS)
    unresolved = {
        path for path in all_seeds
        if not (_REPO_ROOT / path).is_file()
    }
    assert unresolved in (set(), set(_FUTURE_ADD_PATHS))
    assert _DETAILED_DESIGN_SHA256 == s01.DESIGN_SHA256


def test_recovery_epoch001_step0_step1_dual_lineage_is_exact() -> None:
    historical_owners, historical_owner_root = (
        s01.historical_source_owner_snapshot()
    )
    current_owners, current_owner_root = s01.current_source_owner_snapshot()
    compatibility_owners, compatibility_owner_root = s01.source_owner_snapshot()
    assert len(historical_owners) == len(current_owners) == 5
    assert historical_owner_root == (
        "ed9d7463778909c97115096345d25d6ce260d21ed737a72d7c06ccd8e08687ac"
    )
    assert current_owner_root == (
        "187b370490ff701a0f91041ec7ab90b769ebc73cb80f43ba9739854dc717325d"
    )
    assert current_owner_root != historical_owner_root
    assert compatibility_owners == historical_owners
    assert compatibility_owner_root == historical_owner_root
    assert tuple(row["path"] for row in current_owners) == _CURRENT_OWNER_PATHS

    historical_closure, historical_closure_root = (
        s01.historical_dependency_closure()
    )
    current_closure, current_closure_root = s01.current_dependency_closure()
    compatibility_closure, compatibility_closure_root = s01.dependency_closure()
    assert len(historical_closure) == 17
    assert len(current_closure) == 38
    assert historical_closure_root == (
        "3d42e942239666dc37d14c9c2969d548988c02e38ac497bb65b825d9b4c1f3bd"
    )
    assert current_closure_root == (
        "948d1ff82c0c311c7c3c0c5189013c5c08af2a72415ad599505aec245e0a1c7c"
    )
    assert current_closure_root != historical_closure_root
    assert compatibility_closure == historical_closure
    assert compatibility_closure_root == historical_closure_root


def test_recovery_epoch001_historical_and_public_artifacts_are_immutable() -> None:
    assert len(_PROTECTED_SHA256) == 14
    for path, expected_sha256 in _PROTECTED_SHA256.items():
        assert _sha256(_REPO_ROOT / path) == expected_sha256, path


def test_recovery_epoch001_canonical_current_closure_owner_is_proved_or_red() -> None:
    module = _module_or_red(_CLOSURE_MODULE, _CLOSURE_OWNER_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA",
                "RECOVERY_EPOCH001_CANDIDATE_VERSION_ID",
                "RECOVERY_EPOCH001_SCOPE",
                "RECOVERY_EPOCH001_DISPOSITION",
                "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_NEGATIVE_CODES",
                "fresh_recovery_epoch001_canonical_current_closure",
                "validate_recovery_epoch001_canonical_current_closure_shape",
            }
        ),
        _CLOSURE_OWNER_RED,
    )
    assert module.RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA == (
        _CLOSURE_SCHEMA
    )
    assert module.RECOVERY_EPOCH001_CANDIDATE_VERSION_ID == _RECOVERY_CANDIDATE
    assert module.RECOVERY_EPOCH001_SCOPE == _RECOVERY_SCOPE
    assert module.RECOVERY_EPOCH001_DISPOSITION == _RECOVERY_DISPOSITION
    assert frozenset(
        module.RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_NEGATIVE_CODES
    ) == _CLOSURE_NEGATIVE_CODES
    closure = module.fresh_recovery_epoch001_canonical_current_closure()
    assert module.validate_recovery_epoch001_canonical_current_closure_shape(
        closure
    ) == ()
    assert set(closure["step_views"]) == {
        f"step_{number}" for number in range(11)
    }
    assert set(closure["views"]) == {
        "semantic_execution",
        "dormant_runtime",
        "completion_proof",
        "all_relevant",
    }
    assert closure["candidate_version_id"] == _RECOVERY_CANDIDATE
    assert closure["source_predecessor_commit"] == _SOURCE_PIN
    assert (
        type(closure["source_commit"]) is str
        and len(closure["source_commit"]) == 40
        and all(
            character in "0123456789abcdef"
            for character in closure["source_commit"]
        )
    )


def test_recovery_epoch001_independent_verifier_rederives_graph_or_red() -> None:
    verifier = _tool_module_or_red(
        _INDEPENDENT_VERIFIER_PATH,
        _CLOSURE_VERIFIER_RED,
    )
    _required_attributes(
        verifier,
        frozenset(
            {
                "fresh_recovery_epoch001_canonical_current_closure",
                "verify_recovery_epoch001_canonical_current_closure",
                "verify_recovery_epoch001_current_step_completion_receipt",
            }
        ),
        _CLOSURE_VERIFIER_RED,
    )
    source = (_REPO_ROOT / _INDEPENDENT_VERIFIER_PATH).read_text(
        encoding="utf-8"
    )
    imported = {
        node.module
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert _CLOSURE_MODULE not in imported
    assert _RECEIPT_MODULE not in imported
    independently_derived = (
        verifier.fresh_recovery_epoch001_canonical_current_closure(
            repo_root=_REPO_ROOT
        )
    )
    assert verifier.verify_recovery_epoch001_canonical_current_closure(
        independently_derived,
        repo_root=_REPO_ROOT,
    ) == ()


def test_recovery_epoch001_current_step_receipt_owner_is_proved_or_red() -> None:
    module = _module_or_red(_RECEIPT_MODULE, _RECEIPT_OWNER_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_SCHEMA",
                "RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_NEGATIVE_CODES",
                "RECOVERY_EPOCH001_NEXT_AUTHORITY_BY_STEP",
                "build_recovery_epoch001_current_step_completion_receipt",
                "validate_recovery_epoch001_current_step_completion_receipt_shape",
            }
        ),
        _RECEIPT_OWNER_RED,
    )
    assert module.RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_SCHEMA == (
        _RECEIPT_SCHEMA
    )
    assert frozenset(
        module.RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_NEGATIVE_CODES
    ) == _RECEIPT_NEGATIVE_CODES
    assert module.RECOVERY_EPOCH001_NEXT_AUTHORITY_BY_STEP == (
        _NEXT_AUTHORITY_BY_STEP
    )
    assert set(module.RECOVERY_EPOCH001_NEXT_AUTHORITY_BY_STEP) == set(
        range(11)
    )


def test_recovery_epoch001_s5_cross_role_semantic_owner_is_resolved_or_red() -> None:
    semantic_module = _module_or_red(
        "emlis_ai_grounded_observation_semantic_restatement_v3",
        _STEP5_CROSS_ROLE_OWNER_RED,
    )
    _required_attributes(
        semantic_module,
        frozenset(
            {
                "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA",
                "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION",
                "CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA",
                "GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_NEGATIVE_CODES",
                "_GroundedCrossRoleTypedSemanticComponent",
                "GroundedCrossRoleSemanticComponentBinding",
                "GroundedCrossRoleSemanticRestatementWitness",
                "_project_grounded_cross_role_typed_semantic_components",
                (
                    "_build_grounded_cross_role_semantic_restatement_witness_"
                    "from_typed_components"
                ),
                (
                    "_validate_grounded_cross_role_semantic_restatement_"
                    "witness_from_typed_components"
                ),
                "build_grounded_cross_role_semantic_restatement_witness",
                "validate_grounded_cross_role_semantic_restatement_witness",
            }
        ),
        _STEP5_CROSS_ROLE_OWNER_RED,
    )
    assert (
        semantic_module.GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_WITNESS_SCHEMA
        == _CROSS_ROLE_WITNESS_SCHEMA
    )
    assert (
        semantic_module.GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_ADAPTER_VERSION
        == _CROSS_ROLE_ADAPTER_VERSION
    )
    assert (
        semantic_module.CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA
        == _CROSS_ROLE_DEPTH_SCHEMA
    )
    assert frozenset(
        semantic_module.GROUND_CROSS_ROLE_SEMANTIC_RESTATEMENT_NEGATIVE_CODES
    ) == _CROSS_ROLE_NEGATIVE_CODES


def test_recovery_epoch001_s5_cross_role_inventory_owner_is_resolved_or_red() -> None:
    inventory_module = _module_or_red(
        "emlis_ai_semantic_obligation_inventory_v3",
        _STEP5_CROSS_ROLE_INVENTORY_OWNER_RED,
    )
    _required_attributes(
        inventory_module,
        frozenset(
            {
                "REFINED_SOURCE_SNAPSHOT_SCHEMA",
                "CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA",
                "CrossRoleSemanticDepthComponentBinding",
                "CrossRoleSemanticDepthEquivalence",
            }
        ),
        _STEP5_CROSS_ROLE_INVENTORY_OWNER_RED,
    )
    assert inventory_module.REFINED_SOURCE_SNAPSHOT_SCHEMA == (
        _REFINED_SOURCE_SNAPSHOT_SCHEMA
    )
    assert inventory_module.CROSS_ROLE_SEMANTIC_DEPTH_EQUIVALENCE_SCHEMA == (
        _CROSS_ROLE_DEPTH_SCHEMA
    )
    snapshot_fields = set(
        inventory_module.GroundedSourceSnapshot.__dataclass_fields__
    )
    required_snapshot_fields = {
        "refined_source_snapshot_schema_version",
        "cross_role_semantic_restatement_witness_sha256",
        "cross_role_semantic_depth_equivalence",
    }
    missing_snapshot_fields = sorted(
        required_snapshot_fields - snapshot_fields
    )
    if missing_snapshot_fields:
        pytest.fail(
            (
                f"{_STEP5_CROSS_ROLE_INVENTORY_OWNER_RED}:"
                f"{','.join(missing_snapshot_fields)}"
            ),
            pytrace=False,
        )


def test_recovery_epoch001_s5_cross_role_content_consumer_is_resolved_or_red() -> None:
    from test_emlis_nls_v3_s5_content_selection_stage_context import (
        _CROSS_ROLE_UNMATCHED_SELECTION_RED,
        _assert_cross_role_unmatched_optional_selection_policy,
        _assert_exact_cross_role_graph_bijection,
        _body_free_input_matching,
        _independent_full_replay_supplemental,
        _known_input,
        _normal_result,
        _refined_result,
    )
    from emlis_ai_content_selection_v3 import (
        build_content_selection_plan,
        validate_content_selection_policy,
    )
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    original = _known_input()
    full_replay_supplemental = (
        _independent_full_replay_supplemental(original)
    )
    normal_result = _normal_result(original)[2]
    normal_depth = build_content_selection_plan(normal_result)["depth"]
    (
        _current,
        supplemental,
        partition,
        partition_issues,
        snapshot,
        result,
        refined_plan,
    ) = _refined_result(original, full_replay_supplemental)
    missing_snapshot_fields = tuple(
        name
        for name in (
            "refined_source_snapshot_schema_version",
            "cross_role_semantic_restatement_witness_sha256",
            "cross_role_semantic_depth_equivalence",
        )
        if not hasattr(snapshot, name)
    )
    if missing_snapshot_fields:
        pytest.fail(
            (
                f"{_STEP5_CROSS_ROLE_CONTENT_CONSUMER_RED}:"
                f"{','.join(missing_snapshot_fields)}"
            ),
            pytrace=False,
        )
    if snapshot.cross_role_semantic_depth_equivalence is None:
        pytest.fail(
            (
                f"{_STEP5_CROSS_ROLE_CONTENT_CONSUMER_RED}:"
                "empty_depth_equivalence"
            ),
            pytrace=False,
        )

    assert supplemental != original
    assert supplemental is not original
    assert artifact_sha256(supplemental) != artifact_sha256(original)
    assert all(
        str(supplemental[field]).strip() == str(original[field]).strip()
        and supplemental[field] != original[field]
        for field in ("thought_text", "action_text")
    )
    assert partition_issues == ()
    assert partition["cross_source_bindings"] == []
    assert partition["question_need_decision_is_semantic_source"] is False
    assert partition["control_plane_owner_role"] == "original_input"
    assert snapshot.semantic_source_roles == (
        "original_input",
        "supplemental_answer",
    )
    assert (
        snapshot.cross_role_semantic_depth_equivalence.effect_scope
        == _CROSS_ROLE_EFFECT_SCOPE
    )
    _assert_exact_cross_role_graph_bijection(snapshot)
    if refined_plan["depth"] != normal_depth:
        pytest.fail(
            _STEP5_CROSS_ROLE_CONTENT_CONSUMER_RED,
            pytrace=False,
        )
    assert validate_content_selection_policy(
        refined_plan,
        inventory_result=result,
    ) == ()
    assert _CROSS_ROLE_UNMATCHED_SELECTION_RED == (
        _STEP5_CROSS_ROLE_UNMATCHED_OPTIONAL_SELECTION_RED
    )

    layered_input = _body_free_input_matching(
        lambda candidate_snapshot, _candidate_result, candidate_plan: (
            candidate_plan["depth"] == "layered"
            and bool(candidate_snapshot.relations)
            and bool(candidate_snapshot.unknowns)
        )
    )
    (
        _unmatched_current,
        _unmatched_supplemental,
        unmatched_partition,
        unmatched_partition_issues,
        unmatched_snapshot,
        unmatched_result,
        unmatched_plan,
    ) = _refined_result(_known_input(), layered_input)
    assert unmatched_partition_issues == ()
    assert unmatched_partition["cross_source_bindings"] == []
    assert (
        unmatched_snapshot
        .cross_role_semantic_depth_equivalence
        .effect_scope
        == _CROSS_ROLE_EFFECT_SCOPE
    )
    _assert_cross_role_unmatched_optional_selection_policy(
        unmatched_snapshot,
        unmatched_result,
        unmatched_plan,
    )


def test_recovery_epoch001_step9_standalone_successor_is_proved_or_red() -> None:
    module = _module_or_red(_SUCCESSOR_MODULE, _STEP9_SUCCESSOR_RED)
    _required_attributes(
        module,
        frozenset(
            {
                "RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH",
                "RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH_ID",
                "build_semantic_candidate_set",
                "evaluate_semantic_hard_gate",
                "validate_semantic_hard_gate_result",
                "select_semantic_candidate_lexicographically",
                "validate_semantic_selection_result",
                "apply_bounded_recovery",
                "validate_bounded_recovery_result",
            }
        ),
        _STEP9_SUCCESSOR_RED,
    )
    graph = module.RECOVERY_EPOCH001_STEP9_SUCCESSOR_GRAPH
    assert graph["candidate_version_id"] == _RECOVERY_CANDIDATE
    assert graph["canonical_current_closure_schema"] == _CLOSURE_SCHEMA


def test_recovery_epoch001_step9_step10_use_one_graph_without_clone_or_red() -> None:
    adapter_path = (
        _AI_ROOT
        / "services"
        / "ai_inference"
        / "emlis_ai_dormant_runtime_adapter_v3.py"
    )
    step9_test_path = (
        _AI_ROOT / "tests" / "test_emlis_nls_v3_s9_hard_gate_selector_recovery.py"
    )
    adapter_source = adapter_path.read_text(encoding="utf-8")
    step9_test_source = step9_test_path.read_text(encoding="utf-8")
    adapter_tree = ast.parse(adapter_source)
    forbidden_names = {
        "_clone_successor_function",
        "_SUCCESSOR_BUILD_SEMANTIC_CANDIDATE_SET",
        "_SUCCESSOR_EVALUATE_SEMANTIC_HARD_GATE",
        "_SUCCESSOR_SELECT_SEMANTIC_CANDIDATE_LEXICOGRAPHICALLY",
        "_SUCCESSOR_APPLY_BOUNDED_RECOVERY",
    }
    names = {
        node.id for node in ast.walk(adapter_tree)
        if isinstance(node, ast.Name)
    } | {
        node.name for node in ast.walk(adapter_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if "FunctionType" in names or names & forbidden_names:
        pytest.fail(_STEP10_SINGLE_GRAPH_RED, pytrace=False)
    if _SUCCESSOR_MODULE not in adapter_source:
        pytest.fail(_STEP10_SINGLE_GRAPH_RED, pytrace=False)
    if _SUCCESSOR_MODULE not in step9_test_source:
        pytest.fail(_STEP10_SINGLE_GRAPH_RED, pytrace=False)


def test_recovery_epoch001_step10_binds_fresh_start_and_end_closure_or_red() -> None:
    evidence_source = (
        _AI_ROOT / "services" / "ai_inference" / "emlis_ai_step10_evidence_v3.py"
    ).read_text(encoding="utf-8")
    runner_source = (
        _AI_ROOT / "tools" / "emlis_nls_v3_batch_run.py"
    ).read_text(encoding="utf-8")
    required_markers = {
        _CLOSURE_MODULE,
        "source_closure_start_sha256",
        "source_closure_end_sha256",
        "canonical_current_closure_sha256",
    }
    if not all(
        marker in evidence_source and marker in runner_source
        for marker in required_markers
    ):
        pytest.fail(_STEP10_START_END_RED, pytrace=False)
