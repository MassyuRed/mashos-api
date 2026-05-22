from __future__ import annotations

import json

import pytest

from emlis_ai_runtime_surface_quality_contract_inventory import (
    RUNTIME_SURFACE_QUALITY_CONTRACT_INVENTORY_VERSION,
    assert_runtime_surface_quality_contract_inventory_meta_only,
    build_runtime_surface_quality_contract_inventory,
    dump_runtime_surface_quality_contract_inventory,
)


def test_step0_runtime_surface_quality_inventory_fixes_baseline_contracts() -> None:
    inventory = build_runtime_surface_quality_contract_inventory()

    assert inventory["version"] == RUNTIME_SURFACE_QUALITY_CONTRACT_INVENTORY_VERSION
    assert inventory["status"] == "fixed"
    assert inventory["scope"] == "Post ProductGate Measurement Runtime Surface Quality Step0-12"
    assert inventory["runtime_surface_quality_measurement_only"] is True
    assert inventory["step0_baseline_contract_inventory_ready"] is True
    assert inventory["step1_runtime_surface_source_lock_required"] is True
    assert inventory["step2_surface_signature_measurement_required"] is True
    assert inventory["step3_scorecard_surface_metrics_connection_required"] is True
    assert inventory["step4_coverage_runtime_baseline_required"] is True
    assert inventory["step5_branch_resolver_required"] is True
    assert inventory["step5_runtime_surface_quality_branch_resolver_required"] is True
    assert inventory["step6_complete_runtime_activation_branch_required"] is True
    assert inventory["step6_runtime_surface_complete_activation_branch_required"] is True
    assert inventory["step6_complete_runtime_activation_branch_ready"] is False
    assert inventory["step6_runtime_surface_complete_activation_branch_ready"] is False
    assert inventory["step6_complete_runtime_activation_meta_only"] is True
    assert inventory["step7_surface_realizer_2_1_anti_template_required"] is True
    assert inventory["step7_surface_realizer_2_1_anti_template_ready"] is False
    assert inventory["step7_surface_realizer_anti_template_meta_only"] is True
    assert inventory["step8_phrase_unit_grammar_normalizer_required"] is True
    assert inventory["step8_phrase_unit_grammar_normalizer_ready"] is False
    assert inventory["step8_phrase_unit_grammar_normalizer_meta_only"] is True
    assert inventory["phrase_unit_grammar_normalizer_material_stage_only"] is True
    assert inventory["step9_tone_engine_2_1_required"] is True
    assert inventory["step9_tone_engine_2_1_ready"] is False
    assert inventory["step9_tone_engine_2_1_meta_only"] is True
    assert inventory["tone_engine_2_1_surface_constraint_only"] is True
    assert inventory["tone_engine_2_1_blind_qa_required_for_completion"] is True
    assert inventory["step10_surface_aware_self_repair_required"] is True
    assert inventory["step10_surface_aware_self_repair_ready"] is False
    assert inventory["step10_surface_aware_self_repair_meta_only"] is True
    assert inventory["surface_aware_self_repair_plan_surface_only"] is True
    assert inventory["surface_aware_self_repair_fail_closed_on_max_attempts"] is True
    assert inventory["step11_blind_qa_long_run_required"] is True
    assert inventory["step11_blind_qa_long_run_ready"] is False
    assert inventory["step11_blind_qa_long_run_meta_only"] is True
    assert inventory["step11_blind_qa_candidate_bodyless"] is True
    assert inventory["step11_long_run_uses_surface_signature_only"] is True
    assert inventory["step11_read_feeling_requires_blind_qa"] is True
    assert inventory["step12_exit_gate_required"] is True
    assert inventory["step12_exit_gate_ready"] is False
    assert inventory["step12_exit_gate_meta_only"] is True
    assert inventory["step12_exit_gate_handoff_only"] is True
    assert inventory["step12_exit_gate_public_release_applied"] is False
    assert inventory["step12_exit_gate_product_gate_achieved"] is False
    assert inventory["step12_exit_gate_preserves_release_blockers"] is True
    assert inventory["step12_exit_gate_preserves_coverage_gaps"] is True
    assert inventory["step12_exit_gate_preserves_qa_gaps"] is True
    assert inventory["phrase_unit_grammar_normalizer_adds_unsupported_meaning"] is False
    assert inventory["meaning_added_by_phrase_unit_grammar"] is False
    assert inventory["tone_engine_2_1_allowed_in_step9"] is True
    assert inventory["tone_engine_2_1_changes_public_contract"] is False
    assert inventory["tone_engine_2_1_relaxes_gate"] is False
    assert inventory["fixed_sentence_template_added_by_tone"] is False
    assert inventory["input_specific_tone_branch_added"] is False
    assert inventory["meaning_added_by_tone_engine_2_1"] is False
    assert inventory["machine_metrics_used_for_read_feeling"] is False
    assert inventory["read_feeling_auto_filled_from_machine_metrics"] is False
    assert inventory["tone_completion_requires_blind_qa"] is True
    assert inventory["surface_aware_self_repair_allowed_in_step10"] is True
    assert inventory["surface_aware_self_repair_replans_surface_only"] is True
    assert inventory["surface_aware_self_repair_changes_public_contract"] is False
    assert inventory["surface_aware_self_repair_relaxes_gate"] is False
    assert inventory["blind_qa_long_run_allowed_in_step11"] is True
    assert inventory["blind_qa_candidate_includes_text"] is False
    assert inventory["blind_qa_review_includes_text"] is False
    assert inventory["long_run_uses_comment_text"] is False
    assert inventory["long_run_uses_raw_input"] is False
    assert inventory["read_feeling_auto_estimation_allowed"] is False
    assert inventory["runtime_surface_exit_gate_allowed_in_step12"] is True
    assert inventory["runtime_surface_exit_gate_handoff_only"] is True
    assert inventory["runtime_surface_exit_gate_preserves_release_blockers"] is True
    assert inventory["runtime_surface_exit_gate_preserves_coverage_gaps"] is True
    assert inventory["runtime_surface_exit_gate_preserves_qa_gaps"] is True
    assert inventory["runtime_surface_exit_gate_changes_public_contract"] is False
    assert inventory["runtime_surface_exit_gate_relaxes_gate"] is False
    assert inventory["runtime_surface_exit_gate_applies_public_release"] is False
    assert inventory["runtime_surface_exit_gate_declares_product_gate"] is False
    assert inventory["surface_aware_self_repair_meaning_added"] is False
    assert inventory["surface_aware_self_repair_uses_fixture_strings"] is False
    assert inventory["unsupported_sentence_added_by_surface_repair"] is False
    assert inventory["product_gate_achieved"] is False
    assert inventory["public_release_applied"] is False
    assert inventory["rn_visible_contract_change_allowed"] is False
    assert inventory["api_response_key_change_allowed"] is False
    assert inventory["db_physical_rename_allowed"] is False
    assert inventory["gate_relaxation_allowed"] is False
    assert inventory["surface_text_repair_allowed_in_step0_1"] is False
    assert inventory["step2_surface_signature_measurement_required"] is True
    assert inventory["surface_text_repair_allowed_in_step0_2"] is False
    assert inventory["surface_text_repair_allowed_in_step0_3"] is False
    assert inventory["surface_text_repair_allowed_in_step0_4"] is False
    assert inventory["surface_text_repair_allowed_in_step0_5"] is False
    assert inventory["surface_text_repair_allowed_in_step0_6"] is False
    assert inventory["surface_realizer_anti_template_allowed_in_step7"] is True
    assert inventory["surface_realizer_anti_template_repairs_surface_text_only"] is True
    assert inventory["surface_realizer_anti_template_changes_public_contract"] is False
    assert inventory["surface_realizer_anti_template_relaxes_gate"] is False
    assert inventory["surface_realizer_anti_template_adds_fixed_sentence_templates"] is False
    assert inventory["surface_realizer_anti_template_uses_input_specific_branching"] is False
    assert inventory["complete_runtime_activation_repairs_surface_text"] is False
    assert inventory["complete_runtime_activation_changes_public_contract"] is False
    assert inventory["complete_runtime_activation_adds_rn_display_branch"] is False
    assert inventory["complete_runtime_activation_relaxes_entry_ap0"] is False
    assert inventory["branch_resolver_repairs_surface_text"] is False
    assert inventory["branch_resolver_changes_public_contract"] is False
    assert inventory["scorecard_surface_metrics_connection_only"] is True
    assert inventory["coverage_runtime_baseline_only"] is True
    assert inventory["coverage_group_missing_falls_back_to_short_daily"] is False
    assert inventory["runtime_branching_uses_fixture_strings"] is False
    assert inventory["raw_input_included"] is False
    assert inventory["comment_text_body_included"] is False
    assert inventory["surface_text_repaired_by_step6"] is False
    assert inventory["rn_complete_dedicated_display_branch_added"] is False
    assert inventory["surface_text_repaired_by_step7"] is True
    assert inventory["fixed_sentence_template_added_by_step7"] is False
    assert inventory["input_specific_template_added_by_step7"] is False

    assert "Step0: Baseline / Contract Inventory" in inventory["steps_in_scope"]
    assert "Step1: Runtime Surface Source Lock" in inventory["steps_in_scope"]
    assert "Step2: Surface Signature Measurement" in inventory["steps_in_scope"]
    assert "Step3: Scorecard Surface Metrics connection" in inventory["steps_in_scope"]
    assert "Step4: Coverage Runtime Baseline" in inventory["steps_in_scope"]
    assert "Step5: Branch Resolver" in inventory["steps_in_scope"]
    assert "Step6: Complete Runtime Activation Branch" in inventory["steps_in_scope"]
    assert "Step7: Surface Realizer 2.1 Anti-Template" in inventory["steps_in_scope"]
    assert "Step8: PhraseUnit Grammar Normalizer" in inventory["steps_in_scope"]
    assert "Step9: Tone Engine 2.1" in inventory["steps_in_scope"]
    assert "Step10: Surface-aware Self-Repair" in inventory["steps_in_scope"]
    assert "Step11: Blind QA / Long-run" in inventory["steps_in_scope"]
    assert "Step12: Exit Gate" in inventory["steps_in_scope"]
    assert "Step10: Surface-aware Self-Repair" not in inventory["steps_out_of_scope"]
    assert "Step11: Blind QA / Long-run release decision" not in inventory["steps_out_of_scope"]
    assert "Step12: Exit Gate / public release decision" not in inventory["steps_out_of_scope"]
    assert "Step7: Surface Realizer 2.1 Anti-Template repair" not in inventory["steps_out_of_scope"]
    assert "Step9: Tone Engine 2.1 repair" not in inventory["steps_out_of_scope"]

    lock_ids = {item["contract_id"] for item in inventory["contract_locks"]}
    assert "runtime_surface_quality_measurement_only_boundary" in lock_ids
    assert "rn_passed_only_modal_contract" in lock_ids
    assert "api_response_key_stability_boundary" in lock_ids
    assert "db_physical_name_boundary" in lock_ids
    assert "gate_fail_closed_boundary" in lock_ids
    assert "meta_only_raw_body_boundary" in lock_ids
    assert "product_gate_not_achieved_boundary" in lock_ids
    assert "runtime_source_before_surface_fix_boundary" in lock_ids
    assert "complete_runtime_activation_before_surface_repair_boundary" in lock_ids
    assert "surface_realizer_2_1_anti_template_boundary" in lock_ids
    assert "tone_engine_2_1_boundary" in lock_ids
    assert "surface_aware_self_repair_boundary" in lock_ids
    assert "blind_qa_long_run_boundary" in lock_ids
    assert "runtime_surface_quality_step12_exit_gate_boundary" in lock_ids

    allowed = set(inventory["allowed_touch_files"])
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_quality_contract_inventory.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_source_lock.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_surface_quality_signature.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_reply_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_product_quality_measurement_connection.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_product_quality_scorecard_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_release_ladder_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_coverage_baseline.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_surface_quality_branching.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_complete_activation_branch.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_composer_client_registry.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_ap0_migration_decision_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_scorecard_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_coverage_matrix_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_surface_realizer.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_surface_realizer_anti_template.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_sentence_planner.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_relation_surface_contract.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_phrase_unit_grammar_normalizer.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_material_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_phrase_shaping_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_tone_engine_2_1.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_tone_policy.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_reply_final_review_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_self_repair.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_complete_self_repair_service.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_blind_qa_long_run.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_runtime_surface_exit_gate.py" in allowed
    assert "ai/services/ai_inference/emlis_ai_long_term_quality_service.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_self_repair_step10.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_blind_qa_long_run_step11.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_exit_gate_step12.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_phrase_unit_grammar_normalizer_step8.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_quality_branching_step5.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_complete_activation_branch_step6.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_initial_entry_route.py" in allowed
    assert "ai/tests/test_emlis_ai_runtime_surface_realizer_anti_template_step7.py" in allowed
    assert not any(path.startswith("screens/") for path in allowed)


def test_step0_runtime_surface_quality_inventory_dump_is_meta_only() -> None:
    inventory = build_runtime_surface_quality_contract_inventory()
    dumped = dump_runtime_surface_quality_contract_inventory(inventory)
    parsed = json.loads(dumped)

    assert parsed["raw_input_included"] is False
    assert parsed["comment_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert "これは出してはいけない本文" not in dumped

    unsafe = dict(inventory)
    unsafe["commentText"] = "これは出してはいけない本文"
    with pytest.raises(ValueError):
        assert_runtime_surface_quality_contract_inventory_meta_only(unsafe)
