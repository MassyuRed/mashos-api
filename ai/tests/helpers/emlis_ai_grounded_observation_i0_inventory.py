# -*- coding: utf-8 -*-
from __future__ import annotations

"""I0 evidence freeze and runtime content inventory for the core repair.

This test-only module records the received local snapshot, real-device A-D
failure evidence, runtime reachability ownership, and substantive content paths
that later I2-I5 work must remove, generalize, or isolate. Production reply code
must never import this module.
"""

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

GROUND_OBSERVATION_I0_INVENTORY_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_observation.i0_inventory.mandatory_two_stage.v4"
GROUND_OBSERVATION_I0_SOURCE_SNAPSHOT_SHA256: Final = "1049e10b29726ffc7098a59aad2d6c008d743788b0369f1ef4131b73ff06f305"
GROUND_OBSERVATION_I0_INPUT_SAMPLE_SHA256: Final = "4df8dbf79137bf9fe22503132f1baf45f828bc7507de5ff2eb6979d80a57397d"
GROUND_OBSERVATION_I0_INTENTIONALLY_MODIFIED_PATHS: Final[frozenset[str]] = frozenset(
    {
        "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
        "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
        "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
        "ai/services/ai_inference/emlis_ai_reply_service.py",
    }
)

REACHABILITY_PRODUCTION: Final = "production_reachable"
REACHABILITY_DIAGNOSTIC: Final = "diagnostic_only"
REACHABILITY_TEST: Final = "test_only"
REACHABILITY_SHADOW: Final = "non_public_shadow"
ALLOWED_REACHABILITY: Final = frozenset(
    {REACHABILITY_PRODUCTION, REACHABILITY_DIAGNOSTIC, REACHABILITY_TEST, REACHABILITY_SHADOW}
)

DISPOSITION_KEEP_FUNCTIONAL: Final = "keep_functional"
DISPOSITION_KEEP_SAFETY: Final = "keep_safety"
DISPOSITION_REMOVE_SUBSTANTIVE: Final = "remove_substantive"
DISPOSITION_ISOLATE_FIXTURE: Final = "isolate_fixture"
ALLOWED_DISPOSITIONS: Final = frozenset(
    {
        DISPOSITION_KEEP_FUNCTIONAL,
        DISPOSITION_KEEP_SAFETY,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        DISPOSITION_ISOLATE_FIXTURE,
    }
)

ISSUE_COMPLETED_SURFACE: Final = "completed_semantic_surface"
ISSUE_EXAMPLE_CUE: Final = "example_or_event_cue"
ISSUE_LABEL_ASSEMBLY: Final = "label_assembly"
ISSUE_SYNTHETIC_EVIDENCE: Final = "synthetic_evidence_id"
ISSUE_QUESTION_ESCAPE: Final = "question_dominance"
ISSUE_FIXED_SAFE_BODY: Final = "fixed_safe_state_body"
ISSUE_SOURCE_SHAPING: Final = "source_phrase_shaping"
ISSUE_UI_OR_GRAMMAR: Final = "ui_or_functional_grammar"
ISSUE_SAFETY_BOUNDARY: Final = "safety_boundary"
ISSUE_FIXTURE_OWNER: Final = "fixture_or_qa_owner"
ISSUE_METADATA_TRUTH: Final = "metadata_path_truth_mismatch"


@dataclass(frozen=True)
class SnapshotFileFingerprint:
    file_path: str
    sha256: str
    ownership: str


@dataclass(frozen=True)
class RuntimeModuleOwnership:
    file_path: str
    module_name: str
    reachability: str
    direct_callers: tuple[str, ...]
    direct_callees: tuple[str, ...]
    test_owner_paths: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeContentInventoryEntry:
    file_path: str
    symbol_name: str
    issue_kind: str
    reachability: str
    disposition: str
    rationale: str
    necessity: str
    source_tokens: tuple[str, ...]
    later_step_owner: str

    def as_payload(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeNegativeReachabilityBoundary:
    boundary_id: str
    entry_module: str
    scan_scope: str
    forbidden_modules: tuple[str, ...]
    forbidden_tokens: tuple[str, ...]
    replacement_test_refs: tuple[str, ...]


@dataclass(frozen=True)
class KnownRegressionCase:
    case_id: str
    thought_text: str
    action_text: str
    emotions: tuple[str, ...]
    categories: tuple[str, ...]
    legacy_visible_body: str
    legacy_runtime_fact_codes: tuple[str, ...]
    required_structure_codes: tuple[str, ...]
    prohibited_structure_codes: tuple[str, ...]
    screen_sha256: str
    backend_log_sha256: str

    def as_current_input(self) -> dict[str, object]:
        return {
            "memo": self.thought_text,
            "memo_action": self.action_text,
            "emotions": list(self.emotions),
            "category": list(self.categories),
        }

    def as_structural_expectation(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "required_structure_codes": list(self.required_structure_codes),
            "prohibited_structure_codes": list(self.prohibited_structure_codes),
            "expected_exact_comment_text": None,
            "runtime_case_route_allowed": False,
        }


GROUND_OBSERVATION_I0_FILE_FINGERPRINTS: Final[tuple[SnapshotFileFingerprint, ...]] = (
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_grounded_observation_plan.py", "a60434401b1fccdd2a28fd64cdd55dce9817375d0868dd7c259a82030fbdaa7f", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py", "1f3ea3af980eae061cc5b2a884a07bb8b3f1fd984d27c5cb55c7a1ab8a50119a", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_grounded_observation_gate.py", "5ab7653e515efc79e66edc27815fffd2dbb234eb2f225e8f4663c12363623a90", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_evidence_ledger_service.py", "17e51d7ff39535d60f81ad17582f36ab252301502a3a3328e703d116cea7f9e2", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_reply_service.py", "cc77b7bec9ca4f1b7eb875eb8b26f39a8ed13c2b10266f8f92330a59bc90e1c2", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_complete_surface_realizer.py", "1b95855db2179e693caf35bcd7d74a2bb0e09a6852bed83a7fdca2e0fd233d59", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py", "8c492e29607578d58ad0344d4f9ce480958fb25d6b71e51bdbfa0a3a2d0e645e", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_limited_grounding_reception_surface.py", "796a08428984e69763813905f83329129adc53eee32bac4e4b66fed255e253dc", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_low_information_observation_composer.py", "478abdec5266ae1f68779f044561a0f595bfc57106b88a650a7fabd6632809b8", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_self_denial_safe_state_answer.py", "d7c5b9feab1c8e8db7c30a2aea89312dacfba3fcdd3ffac6c1437c39e5527e3f", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_input_material_bundle.py", "a707f9dc6004cf08c73ceafd8abe9a45dedc0b90809444b354aac245fe844623", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_input_meaning_block_service.py", "5b073f1653f4565b9a5e80c45786c33b111b002b83f12ac435824cceb8f16069", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_safety_triage.py", "9aa7ee3b0742fa267e7396b946694d6f99e3ac8f65217e65453b1faad5b2425b", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_limited_composer_client.py", "17024022e915b5a5e182874c615d31324a0091259ab37310e338ead8cd74502a", REACHABILITY_SHADOW),
    SnapshotFileFingerprint("ai/services/ai_inference/emlis_ai_response_contract_qa_matrix.py", "27e2335ed7509bea3ef58d04c1eb1844b13f8a6ede120e216f70fcec23d61c13", REACHABILITY_DIAGNOSTIC),
    SnapshotFileFingerprint("ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json", "227326722e27d6fcd570ed25614205f8a9f9cb74cf78e93dcd22c4b56bf5b1b1", REACHABILITY_PRODUCTION),
    SnapshotFileFingerprint("ai/tests/test_emlis_ai_phase20_10_real_device_recheck.py", "b6e1c2b8ef4834a9fe1cc2b56175e50d52b53732c31bcabd3c31e2afa0d58e37", REACHABILITY_TEST),
    SnapshotFileFingerprint("ai/tests/test_emlis_ai_bounded_repair_reroute_step7.py", "09078ec106ab1480e12ac8db052b4a362ff31e3ac18ada76ef37b57cc0613960", REACHABILITY_TEST),
    SnapshotFileFingerprint("ai/tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py", "f8feeff8f09a95ddaaea1879c8f5217c20839d02515e7e15feea9ddce0f441cf", REACHABILITY_TEST),
)


GROUND_OBSERVATION_I0_RUNTIME_MODULE_OWNERSHIP: Final[tuple[RuntimeModuleOwnership, ...]] = (
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
        "emlis_ai_grounded_observation_plan",
        REACHABILITY_PRODUCTION,
        (
            "emlis_ai_grounded_observation_gate",
            "emlis_ai_grounded_sentence_surface",
            "emlis_ai_reply_service",
        ),
        (
            "emlis_ai_current_input_bundle",
            "emlis_ai_evidence_ledger_service",
            "emlis_ai_observation_integrator_service",
            "emlis_ai_perspective_board",
            "emlis_ai_perspective_observers",
            "emlis_ai_safety_triage",
            "emlis_ai_types",
        ),
        (
            "ai/tests/test_emlis_ai_grounded_observation_plan_i1.py",
            "ai/tests/test_emlis_ai_grounded_observation_i2_i4.py",
            "ai/tests/test_emlis_ai_gate0_r5_semantic_subchecks.py",
            "ai/tests/test_emlis_ai_bounded_repair_reroute_step7.py",
            "ai/tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
            "ai/tests/test_emlis_ai_mandatory_two_stage_runtime_contract_20260712.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
        "emlis_ai_grounded_sentence_surface",
        REACHABILITY_PRODUCTION,
        ("emlis_ai_grounded_observation_gate", "emlis_ai_reply_service"),
        (
            "emlis_ai_evidence_ledger_service",
            "emlis_ai_grounded_observation_plan",
            "emlis_ai_safety_triage",
        ),
        (
            "ai/tests/test_emlis_ai_grounded_observation_i2_i4.py",
            "ai/tests/test_emlis_ai_gate0_r5_semantic_subchecks.py",
            "ai/tests/test_emlis_ai_bounded_repair_reroute_step7.py",
            "ai/tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
            "ai/tests/test_emlis_ai_mandatory_two_stage_runtime_contract_20260712.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
        "emlis_ai_grounded_observation_gate",
        REACHABILITY_PRODUCTION,
        ("emlis_ai_reply_service",),
        (
            "emlis_ai_evidence_ledger_service",
            "emlis_ai_grounded_observation_plan",
            "emlis_ai_grounded_sentence_surface",
        ),
        (
            "ai/tests/test_emlis_ai_grounded_observation_i5.py",
            "ai/tests/test_emlis_ai_gate0_r5_semantic_subchecks.py",
            "ai/tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
            "ai/tests/test_emlis_ai_mandatory_two_stage_runtime_contract_20260712.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_reply_service.py",
        "emlis_ai_reply_service",
        REACHABILITY_PRODUCTION,
        ("emlis_ai_product_quality_measurement_runner", "emotion_submit_service"),
        (
            "emlis_ai_capability",
            "emlis_ai_current_input_bundle",
            "emlis_ai_evidence_ledger_service",
            "emlis_ai_grounded_observation_gate",
            "emlis_ai_grounded_observation_plan",
            "emlis_ai_grounded_sentence_surface",
            "emlis_ai_observation_integrator_service",
            "emlis_ai_perspective_board",
            "emlis_ai_perspective_observers",
            "emlis_ai_response_contract",
            "emlis_ai_safety_triage",
            "emlis_ai_types",
        ),
        (
            "ai/tests/test_emlis_ai_bounded_repair_reroute_step7.py",
            "ai/tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
            "ai/tests/test_emlis_ai_grounded_observation_i5.py",
            "ai/tests/test_emlis_ai_grounded_observation_i6.py",
            "ai/tests/test_emlis_ai_mandatory_two_stage_runtime_contract_20260712.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
        "emlis_ai_evidence_ledger_service",
        REACHABILITY_PRODUCTION,
        (
            "cocolon_environment_state_output_frame",
            "emlis_ai_grounded_observation_gate",
            "emlis_ai_grounded_observation_plan",
            "emlis_ai_grounded_sentence_surface",
            "emlis_ai_observation_eligibility_service",
            "emlis_ai_observation_kernel",
            "emlis_ai_observation_structure_connection_service",
            "emlis_ai_reply_service",
        ),
        ("emlis_ai_current_input_bundle", "emlis_ai_types"),
        (
            "ai/tests/test_emlis_ai_evidence_ledger_service.py",
            "ai/tests/test_emlis_ai_grounded_observation_plan_i1.py",
            "ai/tests/test_emlis_ai_grounded_observation_i2_i4.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "emlis_ai_complete_surface_realizer",
        REACHABILITY_SHADOW,
        (
            "emlis_ai_complete_composer_client",
            "emlis_ai_complete_grounding_binding",
            "emlis_ai_complete_self_repair_service",
        ),
        (
            "emlis_ai_complete_composer_initial_meta",
            "emlis_ai_complete_composer_types",
            "emlis_ai_complete_sentence_planner",
            "emlis_ai_complete_surface_realizer_anti_template",
            "emlis_ai_complete_tone_policy",
            "emlis_ai_limited_relation_taxonomy",
            "emlis_ai_observation_surface_realizer",
            "emlis_ai_relation_surface_contract",
            "emlis_ai_structure_insight_surface",
        ),
        ("ai/tests/test_emlis_ai_complete_surface_realizer_two_stage_comment_text.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "emlis_ai_complete_initial_surface_recomposition",
        REACHABILITY_SHADOW,
        (
            "emlis_ai_gate_recovery_public_candidate_builder",
            "emlis_ai_product_quality_measurement_event",
            "emlis_ai_public_feedback_meta",
        ),
        (
            "emlis_ai_complete_initial_surface_availability",
            "emlis_ai_gate_recovery_public_constants",
            "emlis_ai_limited_grounding_reception_surface",
            "emlis_ai_public_surface_requirement",
            "emlis_ai_types",
        ),
        ("ai/tests/test_emlis_ai_complete_initial_surface_recomposition_body_free_p7.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_limited_grounding_reception_surface.py",
        "emlis_ai_limited_grounding_reception_surface",
        REACHABILITY_SHADOW,
        (
            "emlis_ai_complete_initial_surface_recomposition",
            "emlis_ai_labelled_two_stage_surface_recomposition",
        ),
        (),
        ("ai/tests/test_emlis_ai_limited_grounding_reception_surface_p4.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_low_information_observation_composer.py",
        "emlis_ai_low_information_observation_composer",
        REACHABILITY_SHADOW,
        (
            "emlis_ai_gate_recovery_public_candidate_builder",
            "emlis_ai_observation_display_repair_integration",
            "emlis_ai_observation_surface_realizer_tone",
        ),
        (
            "emlis_ai_input_material_bundle",
            "emlis_ai_internal_question_service",
            "emlis_ai_observation_dictionary_loader",
            "emlis_ai_observation_eligibility_service",
            "emlis_ai_observation_material_connector",
            "emlis_ai_observation_reply_contract",
            "emlis_ai_observation_sentence_plan_roles",
            "emlis_ai_user_fact_grounding_boundary",
        ),
        ("ai/tests/test_emlis_ai_low_information_observation_composer.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_self_denial_safe_state_answer.py",
        "emlis_ai_self_denial_safe_state_answer",
        REACHABILITY_SHADOW,
        (),
        ("emlis_ai_safety_triage", "emlis_ai_types"),
        ("ai/tests/test_emlis_ai_safety_triage_response_contract.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_input_material_bundle.py",
        "emlis_ai_input_material_bundle",
        REACHABILITY_SHADOW,
        (
            "emlis_ai_low_information_observation_composer",
            "emlis_ai_observation_display_repair_integration",
            "emlis_ai_observation_eligibility_router",
            "emlis_ai_observation_eligibility_service",
            "emlis_ai_product_readfeel_p4_material_audit",
            "emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit",
            "emlis_ai_structure_insight_candidate",
            "emlis_ai_structure_insight_gate",
            "emlis_ai_structure_insight_surface",
        ),
        ("emlis_ai_current_input_bundle", "emlis_ai_safety_triage"),
        ("ai/tests/test_emlis_ai_input_material_bundle_phase20_3.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_input_meaning_block_service.py",
        "emlis_ai_input_meaning_block_service",
        REACHABILITY_SHADOW,
        ("emlis_ai_world_model_service",),
        ("emlis_ai_types",),
        (
            "ai/tests/test_emlis_ai_input_meaning_block_service.py",
            "ai/tests/test_emlis_ai_grounded_observation_i2_i4.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_safety_triage.py",
        "emlis_ai_safety_triage",
        REACHABILITY_PRODUCTION,
        (
            "emlis_ai_grounded_observation_plan",
            "emlis_ai_grounded_sentence_surface",
            "emlis_ai_input_material_bundle",
            "emlis_ai_observation_eligibility_router",
            "emlis_ai_product_readfeel_p4_self_denial_yellow_review",
            "emlis_ai_reply_service",
            "emlis_ai_safety_boundary_service",
            "emlis_ai_self_denial_safe_state_answer",
        ),
        ("emlis_ai_response_contract",),
        (
            "ai/tests/test_emlis_ai_safety_triage_response_contract.py",
            "ai/tests/test_emlis_ai_grounded_observation_i2_i4.py",
        ),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_limited_composer_client.py",
        "emlis_ai_limited_composer_client",
        REACHABILITY_SHADOW,
        ("emlis_ai_complete_material_service", "emlis_ai_composer_client_registry"),
        (
            "emlis_ai_a_plan_equivalent_composer_service",
            "emlis_ai_environment_state_output_surface_contract_completion",
            "emlis_ai_limited_relation_taxonomy",
            "emlis_ai_limited_sentence_quality_guard",
            "emlis_ai_limited_surface_realizer",
            "emlis_ai_phrase_unit_grammar_normalizer",
            "emlis_ai_relation_surface_contract",
            "emlis_ai_state_answer_composer_contract",
        ),
        ("ai/tests/test_emlis_ai_limited_composer_client.py",),
    ),
    RuntimeModuleOwnership(
        "ai/services/ai_inference/emlis_ai_response_contract_qa_matrix.py",
        "emlis_ai_response_contract_qa_matrix",
        REACHABILITY_DIAGNOSTIC,
        (),
        (
            "emlis_ai_observation_eligibility_router",
            "emlis_ai_public_feedback_meta",
            "emlis_ai_response_contract",
        ),
        ("ai/tests/test_emlis_ai_response_contract_qa_matrix_phase20_8.py",),
    ),
)

GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES: Final[frozenset[str]] = frozenset(
    {
        "emlis_ai_complete_surface_realizer",
        "emlis_ai_complete_initial_surface_recomposition",
        "emlis_ai_limited_grounding_reception_surface",
        "emlis_ai_low_information_observation_composer",
        "emlis_ai_self_denial_safe_state_answer",
        "emlis_ai_input_material_bundle",
        "emlis_ai_limited_composer_client",
    }
)


GROUND_OBSERVATION_I0_NEGATIVE_REACHABILITY_BOUNDARIES: Final[
    tuple[RuntimeNegativeReachabilityBoundary, ...]
] = (
    RuntimeNegativeReachabilityBoundary(
        boundary_id="fb172_b7_public_reply_retired_route_absent",
        entry_module="emlis_ai_reply_service",
        scan_scope="entry_import_reachability_only",
        forbidden_modules=tuple(
            sorted(
                {
                    *GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES,
                    "emlis_ai_complete_composer_client",
                    "emlis_ai_context_service",
                    "emlis_ai_gate_recovery_public_candidate_builder",
                    "emlis_ai_labelled_two_stage_surface_recomposition",
                }
            )
        ),
        forbidden_tokens=(
            "MODE_RELATIONSHIP_GRATITUDE_RECOVERY",
            "MODE_SELF_UNDERSTANDING_LEARNING_SHIFT",
            "phase19_real_device_C_self_understanding_learning_shift",
            "phase19_real_device_D_relationship_gratitude_recovery",
            "relationship_end_gratitude_recovery",
            "relationship_gratitude_recovery",
            "self_understanding_learning_shift",
        ),
        replacement_test_refs=(
            "ai/tests/test_emlis_ai_fb172_b6_current_owner.py",
            "ai/tests/test_emlis_ai_grounded_observation_i0_inventory.py",
        ),
    ),
)


GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY: Final[tuple[RuntimeContentInventoryEntry, ...]] = (
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "mode-specific substantive surface functions",
        ISSUE_COMPLETED_SURFACE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Mode selection supplies the center meaning of completed observation/follow sentences.",
        "I3 must realize meaning from GroundedSentencePlan; otherwise the canonical plan is not authoritative.",
        ("def _daily_unpleasant_surface_text_for_line", "def _self_denial_support_surface_text_for_line", "def _self_understanding_surface_text_for_line", "def _structure_insight_surface_text_for_line"),
        "I3",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_surface_realizer.py",
        "section labels and functional grammar atoms",
        ISSUE_UI_OR_GRAMMAR,
        REACHABILITY_SHADOW,
        DISPOSITION_KEEP_FUNCTIONAL,
        "Section labels, particles, punctuation, and bounded hedges do not themselves supply input meaning.",
        "The redesign removes semantic sentence banks, not all fixed Japanese literals.",
        ("見えたこと", "Emlisから"),
        "I3",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "_SEMANTIC_MATERIAL_PATTERNS",
        ISSUE_EXAMPLE_CUE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Known fixture-like phrases select semantic material before recomposition.",
        "Removing only final prose would leave the same case-shaped meaning id upstream.",
        ("_SEMANTIC_MATERIAL_PATTERNS", "昨日の自分", "人と比べ"),
        "I2/I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "_compose_observation_sentence / _compose_reception_sentence",
        ISSUE_COMPLETED_SURFACE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Recovery creates substantive text from semantic ids or labels instead of preserving one source-bound plan.",
        "Recovery must re-realize the same plan rather than switching content owners.",
        ("def _compose_observation_sentence", "def _compose_reception_sentence"),
        "I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "topic/emotion/action label assembly",
        ISSUE_LABEL_ASSEMBLY,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Category, selected emotion, and action labels can replace text-present meaning.",
        "Text-present input must retain nuclei; labels remain secondary evidence only.",
        ("def _topic_from_marker", "def _feeling_phrase", "def _action_phrase"),
        "I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "_evidence_span_ids",
        ISSUE_SYNTHETIC_EVIDENCE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Visible slots and relation ids are converted into p5_* ids absent from the Evidence Ledger.",
        "Every binding must resolve to the request-local sN ledger.",
        ("def _evidence_span_ids", "p5_"),
        "I4/I5",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_complete_initial_surface_recomposition.py",
        "recomposition generation-path metadata declarations",
        ISSUE_METADATA_TRUTH,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "The same owner contains fixture-near cues, completed surfaces and label assembly while declaring fixed/case/fixture use false and the source ai_generated.",
        "I5 metadata must be computed from actual runtime path facts rather than self-declared booleans.",
        ("fixed_sentence_template_used", "case_specific_route_used", "exact_fixture_surface_used", '"composer_source": "ai_generated"'),
        "I5",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_limited_grounding_reception_surface.py",
        "limited cue patterns and completed sections",
        ISSUE_EXAMPLE_CUE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "A limited path independently recognizes fixture-like phrases and supplies completed text.",
        "Limited grounding must constrain claim scope inside the same plan.",
        ("_SEMANTIC_MATERIAL_PATTERNS", "def _compose_observation_section", "def _compose_reception_section"),
        "I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_low_information_observation_composer.py",
        "unknown-slot question surface path",
        ISSUE_QUESTION_ESCAPE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Unknown event/cause/target can become the main reply despite an explicit short state.",
        "P7 must observe known state first and keep unknowns as claim boundaries.",
        ("def _question_surface_for_kind", "def _known_scope_text_from_material_slots"),
        "I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_self_denial_safe_state_answer.py",
        "_compose_body",
        ISSUE_FIXED_SAFE_BODY,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Non-emergency self-denial is replaced by one of two completed bodies.",
        "Safety remains, but state/evaluation/refusal/follow must come from the grounded plan.",
        ("def _compose_body",),
        "I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_self_denial_safe_state_answer.py",
        "fixed-body generation-path metadata declarations",
        ISSUE_METADATA_TRUTH,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "A fixed two-body owner records composer_source=ai_generated and fixed_fallback_used=false.",
        "I5 must expose the actual generation owner without representing a rule-owned fixed body as generated AI content.",
        ('"composer_source": "ai_generated"', '"fixed_fallback_used": False', 'composer_source="ai_generated"'),
        "I5",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_input_material_bundle.py",
        "former semantic phrase-table route (withdrawn)",
        ISSUE_EXAMPLE_CUE,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "I2 removed fixture-near semantic-id generation from the material sufficiency owner.",
        "Text-present meaning must come from canonical nuclei and relations, not a replacement phrase table.",
        ("SEMANTIC_MATERIAL_SOURCE", "SEMANTIC_RELATION_MATERIAL_GENERATION_DISABLED", "def _generic_relation_material_ids"),
        "I2",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_input_material_bundle.py",
        "canonical semantic-owner path-truth metadata",
        ISSUE_METADATA_TRUTH,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "The compatibility bundle now reports that semantic relation material generation is disabled.",
        "I5 can derive final path truth without reviving the former cue owner.",
        ("semantic_material_source", "semantic_relation_material_generation_disabled", "text_present_semantics_owned_by_canonical_plan"),
        "I2/I5",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_safety_triage.py",
        "emergency/support-required perimeter",
        ISSUE_SAFETY_BOUNDARY,
        REACHABILITY_PRODUCTION,
        DISPOSITION_KEEP_SAFETY,
        "Emergency and support-required inputs have a separate Safety owner.",
        "The current repair must not weaken or override the high-risk boundary.",
        ("TRIAGE_SAFETY_SUPPORT_REQUIRED", "TRIAGE_SAFETY_BLOCKED_EMERGENCY", "requires_separate_safety_surface"),
        "I1/I4 non-regression",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_safety_triage.py",
        "former D-near exact self-denial alternatives (withdrawn)",
        ISSUE_EXAMPLE_CUE,
        REACHABILITY_PRODUCTION,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "I2 replaced case wording with speaker-reference plus negative-evaluation structure.",
        "The broad classifier must retain non-emergency Safety while avoiding expression-difficulty false positives.",
        ("_SELF_REFERENCE_RE", "_SELF_WORTH_NEGATION_RE", "def _is_self_denial_non_emergency"),
        "I2",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_limited_composer_client.py",
        "_compress_text / _generic_shallow_phrase",
        ISSUE_SOURCE_SHAPING,
        REACHABILITY_SHADOW,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "The functions mix safe source shaping with content-bearing phrase branches.",
        "I3/I4 must retain grammar-safe shaping and withdraw content supply.",
        ("def _compress_text", "def _generic_shallow_phrase"),
        "I3/I4",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/config/emlis_reception_assistance_dictionary.v1.json",
        "event_hints / reception mode content",
        ISSUE_EXAMPLE_CUE,
        REACHABILITY_PRODUCTION,
        DISPOSITION_REMOVE_SUBSTANTIVE,
        "Concrete event nouns influence reception modes carrying substantive intent.",
        "Unknown nouns must remain source anchors, not content switches.",
        ('"event_hints"', '"reception_modes"', '"follow_shape_families"'),
        "I3/I5",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_response_contract_qa_matrix.py",
        "Phase20 response contract QA corpus",
        ISSUE_FIXTURE_OWNER,
        REACHABILITY_DIAGNOSTIC,
        DISPOSITION_ISOLATE_FIXTURE,
        "The module owns case material but is not reachable from reply_service in the received snapshot.",
        "QA cases may remain diagnostic evidence only.",
        ("PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS", "build_phase20_8_response_contract_qa_cases"),
        "I0/I6",
    ),
    RuntimeContentInventoryEntry(
        "ai/tests/test_emlis_ai_phase20_10_real_device_recheck.py",
        "historical local delivery owner after canonical cutover",
        ISSUE_FIXTURE_OWNER,
        REACHABILITY_TEST,
        DISPOSITION_ISOLATE_FIXTURE,
        "The local test reads canonical body-free metadata and explicitly refuses actual-device or Product Read Feel ownership.",
        "Display contract tests must stay separate from structural semantic tests and device evidence.",
        ("Historical Phase20-10 local public-delivery regression guards", "grounded_observation", "actual_device_evidence"),
        "I0/I6",
    ),
    RuntimeContentInventoryEntry(
        "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
        "build_evidence_ledger / source_text_for_span",
        ISSUE_SOURCE_SHAPING,
        REACHABILITY_PRODUCTION,
        DISPOSITION_KEEP_FUNCTIONAL,
        "The existing ledger owns request-local sN ids, source fields, and offsets without reply text.",
        "I1 must resolve against this contract instead of adding another evidence id system.",
        ("def build_evidence_ledger", "def source_text_for_span", 'span_id=f"s{len(unique) + 1}"'),
        "I1",
    ),
)


GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES: Final[tuple[KnownRegressionCase, ...]] = (
    KnownRegressionCase(
        "A",
        "なんか今日は全部だるい。\n何もしたくない。",
        "",
        ("悲しみ", "不安"),
        ("生活",),
        "見えたこと：\nここから見えているのは、感情の向き、置かれたカテゴリや対象の入口、時間の手がかりまでで、詳しい出来事まではまだ見えていません。\nEmlisから：\n今は、悲しみだけではなく、不安の重さも近くにあるように見えます。詳しく残せそうなら、何があったか残してみませんか。",
        ("public_observation_passed", "low_information_observation_path", "question_surface_visible", "rn_modal_opened"),
        ("current_global_fatigue_retained", "action_motivation_reduction_retained", "selected_emotions_secondary_only", "event_and_cause_unknown", "observation_precedes_unknown_boundary"),
        ("question_replaces_observation", "unknown_event_explanation_dominates", "category_only_body"),
        "dc103263e5ac3a3269224e679779e652d924b82001466dec20860245727f2924",
        "aedd8c858c3f866073bafbf3439612f5a7d8275dea8aa1cd31a70926aa99658e",
    ),
    KnownRegressionCase(
        "B",
        "今までは、人に対して何故？と考えていたけど、疑問の対象が物になったことで、人について考えすぎる事が減った気がする。\n何故それを聞くの？とか聞く意味があるの？と考えてしまってうまくコミュニケーションが取れなくてもやもやしていたけど、物を見ることで人への興味が薄れた。\n私にとってはとても良い変化になった。\n\nそして学校、バイト、趣味で一人の時間が無くなったけど、人との話し方を思い出してきてる。やろう、言おうと思ったときにすぐに行動する勇気が出せるようになった。\n少しずつだけど進歩してる。大丈夫。",
        "創作をする時にリアルさを求めるなら日常に隠れている汚れや傷の意味を知れ。という授業があった。\n意味のない場所に傷や汚れは作れない、作ったとしても違和感になる。と、それから外に出る度に色んな場所を見て、今まで気にしなかった場所も見るようになった。\n傷や汚れの場所、自分のこうかな？という憶測をメモしていった。",
        ("自己理解",),
        ("学習",),
        "見えたこと：\nこの記録では、学習について、自己理解の動きと言葉に分けて見ようとしている動きが重なっている状態として見えます。\nEmlisから：\nすぐに一つへまとめず、いま見えている動きをそのまま置こうとしているところを、Emlisは受け取りました。",
        ("public_observation_passed", "label_assembly_visible", "whole_input_meaning_dropped", "rn_modal_opened"),
        ("attention_shift_evidence_retained", "reduced_interpersonal_overthinking_retained", "class_to_daily_observation_action_retained", "communication_and_immediate_action_change_retained", "user_positive_evaluation_retained", "major_relations_not_collapsed"),
        ("learning_self_understanding_memo_label_assembly", "single_growth_sentence_compression", "permanent_personality_change_claim"),
        "c632e06b8afc45321b8a0ce28501db24a89d5677b5194a4a033bddf725193dc7",
        "07f469023e092aac2ca6ef1569b1b66c2999c38208f5f46f4e0802bd0690c434",
    ),
    KnownRegressionCase(
        "C",
        "「いきなり大きく変わろう」とするよりも、\n「昨日の自分よりほんの少し前に進めたらいい」\nそういう気持ちで過ごしていきたい。\n\n人と比べてしまうと、どうしても焦ったり、自分が遅い気がしてしまう。\nでも、本当は比べる相手は他の誰かじゃなくて、昨日の自分なんだと思う。\n\n昨日より少し出来たことが増えた。\n昨日より少し勇気が出せた。\n昨日より少し気持ちを言葉に出来た。\n\nそういう小さな変化を大切にしていきたい",
        "",
        ("自己理解",),
        ("健康",),
        "見えたこと：\n今は、大きく変わることより、昨日の自分より少し前に進むことを基準に置こうとしている状態に見えます。\nEmlisから：\n人と比べて焦りが出る中でも、小さな変化や少し言葉にできたことを消さずに見ようとしているところを、Emlisは受け取りました。",
        ("public_observation_passed", "fixture_near_semantic_surface_visible", "rn_modal_opened"),
        ("comparison_baseline_shift_retained", "small_progress_intention_retained", "done_courage_verbalization_changes_retained", "urgency_contrast_retained"),
        ("known_phrase_selects_fixed_body", "source_paraphrase_only"),
        "444261f5c1d137e278129f84d1c64821666732ba0056544c762db89d26359069",
        "b8bb99f06ff58a33ce969a5b82da7ad6e9a0c97f840583fd29b9de7b3d5895b2",
    ),
    KnownRegressionCase(
        "D",
        "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
        "",
        ("悲しみ",),
        ("人生", "価値観"),
        "今の入力では、自分への言葉がかなり厳しい方向に寄っています。その言葉をあなた自身の事実として確定せず、傷つけ続けることへの違和感も一緒に出ている状態として受け取れます。",
        ("public_observation_passed", "self_denial_safe_state_answer_path", "fixed_two_body_owner", "rn_modal_opened"),
        ("self_evaluation_retained", "user_continuation_rejection_retained", "identity_fact_boundary_required", "input_grounded_limited_opposition_required", "human_follow_required"),
        ("fixed_two_body_path", "self_denial_label_only", "unsupported_personality_assurance"),
        "7fc70624180c801ceee01d8b2458280725a919d33b20cf4c894f99db051be52e",
        "7ec169f78cc91a69648a5177e00d3d3b1ed437d0404fe5d88bd3a761a5861d82",
    ),
)


GROUND_OBSERVATION_I0_REACHABLE_PHRASE_COUNTS: Final[dict[str, dict[str, int]]] = {
    "なんか今日は全部だるい": {},
    "疑問の対象が物": {},
    "傷や汚れ": {},
    "昨日の自分": {
    },
    "人と比べ": {},
    "小さな変化": {},
    "少し勇気": {},
    "ほんの少し前": {},
    "自分を傷つけてるのは私": {},
    "いい事なんて絶対にない": {},
}


def build_ground_observation_i0_runtime_import_graph(
    backend_root: Path,
) -> tuple[dict[str, Path], dict[str, set[str]]]:
    """Build the import graph used by I0 reachability assertions.

    Only direct imports between top-level ``ai_inference`` Python modules are
    edges.  Tokens in diagnostic or shadow files do not become production
    failures unless an entry module can actually reach those files.
    """

    inference_root = backend_root / "ai" / "services" / "ai_inference"
    modules = {path.stem: path for path in inference_root.glob("*.py")}
    edges: dict[str, set[str]] = {name: set() for name in modules}
    for name, path in modules.items():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = (alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = (node.module.split(".", 1)[0],)
            else:
                continue
            edges[name].update(item for item in imported if item in modules)
    return modules, edges


def ground_observation_i0_reachable_modules(
    entry_module: str,
    edges: dict[str, set[str]],
) -> frozenset[str]:
    reachable: set[str] = set()
    pending = [entry_module]
    while pending:
        current = pending.pop()
        if current in reachable:
            continue
        reachable.add(current)
        pending.extend(edges.get(current, ()))
    return frozenset(reachable)


def evaluate_ground_observation_i0_negative_reachability(
    backend_root: Path,
) -> tuple[str, ...]:
    modules, edges = build_ground_observation_i0_runtime_import_graph(backend_root)
    violations: list[str] = []
    for boundary in GROUND_OBSERVATION_I0_NEGATIVE_REACHABILITY_BOUNDARIES:
        if boundary.entry_module not in modules:
            violations.append(f"{boundary.boundary_id}:missing_entry:{boundary.entry_module}")
            continue
        reachable = ground_observation_i0_reachable_modules(boundary.entry_module, edges)
        for module_name in sorted(set(boundary.forbidden_modules).intersection(reachable)):
            violations.append(f"{boundary.boundary_id}:forbidden_module:{module_name}")
        for module_name in sorted(reachable):
            source = modules[module_name].read_text(encoding="utf-8")
            for token in boundary.forbidden_tokens:
                if token in source:
                    violations.append(
                        f"{boundary.boundary_id}:forbidden_token:{module_name}:{token}"
                    )
        for test_ref in boundary.replacement_test_refs:
            if not (backend_root / test_ref).is_file():
                violations.append(f"{boundary.boundary_id}:missing_test_ref:{test_ref}")
    return tuple(violations)


def validate_ground_observation_i0_inventory() -> None:
    assert GROUND_OBSERVATION_I0_INVENTORY_SCHEMA_VERSION
    assert len(GROUND_OBSERVATION_I0_SOURCE_SNAPSHOT_SHA256) == 64
    assert len(GROUND_OBSERVATION_I0_INPUT_SAMPLE_SHA256) == 64
    assert {item.case_id for item in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES} == {"A", "B", "C", "D"}

    fingerprint_paths: set[str] = set()
    for item in GROUND_OBSERVATION_I0_FILE_FINGERPRINTS:
        assert item.file_path and item.file_path not in fingerprint_paths
        fingerprint_paths.add(item.file_path)
        assert len(item.sha256) == 64
        int(item.sha256, 16)
        assert item.ownership in ALLOWED_REACHABILITY
    assert GROUND_OBSERVATION_I0_INTENTIONALLY_MODIFIED_PATHS <= fingerprint_paths

    ownership_modules: set[str] = set()
    for item in GROUND_OBSERVATION_I0_RUNTIME_MODULE_OWNERSHIP:
        assert item.module_name and item.module_name not in ownership_modules
        ownership_modules.add(item.module_name)
        assert item.file_path.endswith(f"/{item.module_name}.py")
        assert item.reachability in ALLOWED_REACHABILITY
        assert tuple(sorted(item.direct_callers)) == item.direct_callers
        assert tuple(sorted(item.direct_callees)) == item.direct_callees
        assert item.test_owner_paths
        assert all(path.startswith("ai/tests/") for path in item.test_owner_paths)
    assert GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES <= ownership_modules
    assert all(
        item.reachability == REACHABILITY_SHADOW
        for item in GROUND_OBSERVATION_I0_RUNTIME_MODULE_OWNERSHIP
        if item.module_name in GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES
    )

    boundary_ids: set[str] = set()
    for boundary in GROUND_OBSERVATION_I0_NEGATIVE_REACHABILITY_BOUNDARIES:
        assert boundary.boundary_id not in boundary_ids
        boundary_ids.add(boundary.boundary_id)
        assert boundary.entry_module
        assert boundary.scan_scope == "entry_import_reachability_only"
        assert boundary.forbidden_modules == tuple(sorted(set(boundary.forbidden_modules)))
        assert boundary.forbidden_tokens == tuple(sorted(set(boundary.forbidden_tokens)))
        assert boundary.replacement_test_refs
        assert all(path.startswith("ai/tests/") for path in boundary.replacement_test_refs)

    inventory_keys: set[tuple[str, str]] = set()
    for item in GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY:
        key = (item.file_path, item.symbol_name)
        assert key not in inventory_keys
        inventory_keys.add(key)
        assert item.reachability in ALLOWED_REACHABILITY
        assert item.disposition in ALLOWED_DISPOSITIONS
        assert item.rationale and item.necessity and item.source_tokens and item.later_step_owner
        if item.reachability == REACHABILITY_DIAGNOSTIC:
            assert item.disposition == DISPOSITION_ISOLATE_FIXTURE

    for case in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES:
        assert case.thought_text and case.legacy_visible_body and case.legacy_runtime_fact_codes
        assert case.required_structure_codes and case.prohibited_structure_codes
        assert len(case.screen_sha256) == 64 and len(case.backend_log_sha256) == 64
        int(case.screen_sha256, 16)
        int(case.backend_log_sha256, 16)
        expectation = case.as_structural_expectation()
        assert expectation["expected_exact_comment_text"] is None
        assert expectation["runtime_case_route_allowed"] is False


__all__ = [
    "GROUND_OBSERVATION_I0_INVENTORY_SCHEMA_VERSION",
    "GROUND_OBSERVATION_I0_SOURCE_SNAPSHOT_SHA256",
    "GROUND_OBSERVATION_I0_INPUT_SAMPLE_SHA256",
    "GROUND_OBSERVATION_I0_INTENTIONALLY_MODIFIED_PATHS",
    "REACHABILITY_PRODUCTION",
    "REACHABILITY_DIAGNOSTIC",
    "REACHABILITY_TEST",
    "REACHABILITY_SHADOW",
    "DISPOSITION_KEEP_FUNCTIONAL",
    "DISPOSITION_KEEP_SAFETY",
    "DISPOSITION_REMOVE_SUBSTANTIVE",
    "DISPOSITION_ISOLATE_FIXTURE",
    "ISSUE_METADATA_TRUTH",
    "SnapshotFileFingerprint",
    "RuntimeModuleOwnership",
    "RuntimeContentInventoryEntry",
    "RuntimeNegativeReachabilityBoundary",
    "KnownRegressionCase",
    "GROUND_OBSERVATION_I0_FILE_FINGERPRINTS",
    "GROUND_OBSERVATION_I0_RUNTIME_MODULE_OWNERSHIP",
    "GROUND_OBSERVATION_I0_LEGACY_RUNTIME_MODULES",
    "GROUND_OBSERVATION_I0_NEGATIVE_REACHABILITY_BOUNDARIES",
    "GROUND_OBSERVATION_I0_RUNTIME_CONTENT_INVENTORY",
    "GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES",
    "GROUND_OBSERVATION_I0_REACHABLE_PHRASE_COUNTS",
    "build_ground_observation_i0_runtime_import_graph",
    "ground_observation_i0_reachable_modules",
    "evaluate_ground_observation_i0_negative_reachability",
    "validate_ground_observation_i0_inventory",
]
