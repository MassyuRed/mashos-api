from __future__ import annotations

import json

from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_state_answer_surface_contract import (
    EMLIS_OBSERVATION_DISPLAY_LABEL,
    EMLIS_RECEPTION_DISPLAY_LABEL,
    EMLIS_RECEPTION_MODE_SUMMARY_MATERIAL_ID,
    EMLIS_RECEPTION_SECTION_MATERIAL_ID,
    EMLIS_RECEPTION_SECTION_MATERIAL_SCHEMA_VERSION,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_PHASE,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
    EMLIS_TWO_STAGE_RECEPTION_MATERIAL_ID,
    EMLIS_TWO_STAGE_RECEPTION_SCHEMA_VERSION,
    EMLIS_TWO_STAGE_SECTION_ORDER,
    build_emlis_state_answer_surface_contract,
    state_answer_surface_contract_composer_payload,
    state_answer_surface_contract_forward_meta,
    state_answer_surface_contract_gate_report,
)
from fixtures.emlis_ai_two_stage_reception_cases import TWO_STAGE_RECEPTION_CASES


def _standard_current_input() -> dict[str, object]:
    return {
        "id": "emo-state-answer-1",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": "この職場でやっていけるか不安",
        "memo_action": "新しい仕事を任された",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "emotions": ["不安"],
        "category": ["仕事"],
        "is_secret": False,
    }


def test_phase2_state_answer_surface_contract_builds_text_free_layered_material() -> None:
    current_input = _standard_current_input()

    contract = build_emlis_state_answer_surface_contract(current_input)
    meta = contract.as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["schema_version"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION
    assert meta["material_id"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    assert meta["source_phase"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_PHASE
    assert meta["state_answer_surface_contract_connected"] is True
    assert meta["environment_state_output_frame_connected"] is True
    assert meta["observation_structure_material_connected"] is True
    assert meta["observation_layer"]["section_role"] == "state_answer_observation"
    assert [step["step_id"] for step in meta["observation_layer"]["steps"]] == [
        "intent_pickup",
        "surface_state_observation",
        "unconfirmed_area",
        "deeper_state_observation",
        "fact_boundary",
    ]
    assert all(step["section_role"] == "observation" for step in meta["observation_layer"]["steps"])
    assert meta["human_follow_layer"]["section_role"] == "human_follow"
    assert meta["human_follow_layer"]["follow_mode"] == "emlis_impression_not_fact"
    assert meta["human_follow_layer"]["personality_claim_allowed"] is False
    assert meta["ratio_policy"]["default_ratio"] == {"observation": 0.6, "human_follow": 0.4}
    assert meta["ratio_policy"]["resolved_ratio"]["reason"] == "standard_state_answer"
    assert meta["metaphor_policy"]["mode"] == "none"
    assert meta["metaphor_policy"]["free_metaphor_generation_allowed"] is False
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"raw_text":' not in encoded
    assert '"comment_text":' not in encoded


def test_phase2_contract_keeps_public_api_db_rn_and_causal_boundaries_unchanged() -> None:
    meta = build_emlis_state_answer_surface_contract(_standard_current_input()).as_meta()

    assert "surface_policy" not in meta
    assert meta["completed_reply_generated"] is False
    assert meta["comment_text_generated"] is False
    assert meta["public_payload_changed"] is False
    assert meta["public_response_key_added"] is False
    assert meta["api_route_changed"] is False
    assert meta["response_key_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["schema_file_materialized"] is False
    assert meta["state_answer_surface_policy_material_only"] is True
    assert meta["state_answer_surface_policy_must_not_generate_completed_reply"] is True
    assert meta["state_answer_surface_policy_must_not_generate_comment_text"] is True
    assert meta["state_answer_surface_policy_must_not_generate_cause_from_category"] is True
    assert meta["state_answer_surface_policy_must_not_generate_cause_from_emotion_strength"] is True
    assert meta["state_answer_surface_policy_must_not_generate_period_tendency_from_single_record"] is True
    assert meta["state_answer_surface_policy_cause_from_category"] is False
    assert meta["state_answer_surface_policy_cause_from_emotion_strength"] is False
    assert meta["state_answer_surface_policy_period_tendency_from_single_record"] is False
    assert meta["state_answer_surface_policy_personality_tendency_allowed"] is False


def test_phase2_contract_attaches_to_observation_structure_material_without_public_text() -> None:
    current_input = _standard_current_input()

    material = build_observation_structure_material(current_input=current_input)
    meta = material.as_meta()
    composer_payload = material.composer_payload()
    gate_report = material.gate_report()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["state_answer_surface_contract_connected"] is True
    assert meta["state_answer_surface_contract_material_id"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    assert meta["state_answer_surface_contract_schema_version"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION
    assert meta["state_answer_surface_contract_observation_layer_connected"] is True
    assert meta["state_answer_surface_contract_human_follow_layer_connected"] is True
    assert composer_payload["state_answer_surface_contract_connected"] is True
    assert composer_payload["state_answer_surface_contract"]["material_id"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    assert gate_report["state_answer_surface_contract_connected"] is True
    assert gate_report["state_answer_surface_contract_gate_report"]["state_answer_surface_contract_connected"] is True
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"raw_text":' not in encoded
    assert '"comment_text":' not in encoded


def test_phase2_contract_helpers_return_safe_forward_gate_and_composer_payloads() -> None:
    contract = build_emlis_state_answer_surface_contract(_standard_current_input())

    forward_meta = state_answer_surface_contract_forward_meta(contract)
    gate_report = state_answer_surface_contract_gate_report(forward_meta)
    composer_payload = state_answer_surface_contract_composer_payload(forward_meta)

    assert forward_meta["material_id"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    assert gate_report["material_id"] == EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID
    assert gate_report["comment_text_generated"] is False
    assert gate_report["raw_text_included"] is False
    assert gate_report["cause_from_category"] is False
    assert composer_payload["state_answer_surface_contract_connected"] is True
    assert composer_payload["dictionary_is_observation_material_only"] is True
    assert composer_payload["comment_text_generated"] is False
    assert composer_payload["raw_text_included"] is False


def test_phase2_contract_handles_low_information_without_cause_or_period_tendency() -> None:
    current_input = {
        "id": "emo-state-answer-low-info",
        "created_at": "2026-05-26T01:00:00Z",
        "memo": "無理",
        "memo_action": "",
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "category": ["仕事"],
    }

    meta = build_emlis_state_answer_surface_contract(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["observation_layer"]["scope_marker_policy"]["single_record_only"] is True
    assert meta["observation_layer"]["scope_marker_policy"]["must_not_surface_as_period_tendency"] is True
    assert meta["human_follow_layer"]["must_ground_to_input"] is True
    assert meta["special_handling"]["self_denial"]["must_include_input_evidence"] is True
    assert meta["special_handling"]["anger"]["target_judgement_agreement_allowed"] is False
    assert "surface_policy" not in meta
    assert meta["state_answer_surface_policy_cause_from_category"] is False
    assert meta["state_answer_surface_policy_cause_from_emotion_strength"] is False
    assert meta["state_answer_surface_policy_period_tendency_from_single_record"] is False
    assert current_input["memo"] not in encoded
    assert '"raw_text":' not in encoded



def _two_stage_case_input(case_id: str) -> dict[str, object]:
    for case in TWO_STAGE_RECEPTION_CASES:
        if case.get("case_id") == case_id:
            return dict(case["current_input"])
    raise AssertionError(f"missing two-stage fixture case: {case_id}")


def test_phase7_surface_contract_adds_two_stage_reception_material_without_public_contract_change() -> None:
    current_input = _two_stage_case_input("daily_unpleasant_encounter_A")

    meta = build_emlis_state_answer_surface_contract(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    two_stage = meta["two_stage_reception"]
    reception_mode = meta["reception_mode"]
    reception_section = meta["reception_section_material"]
    reception_assistance = meta["reception_assistance"]

    assert two_stage["schema_version"] == EMLIS_TWO_STAGE_RECEPTION_SCHEMA_VERSION
    assert two_stage["material_id"] == EMLIS_TWO_STAGE_RECEPTION_MATERIAL_ID
    assert two_stage["enabled"] is True
    assert two_stage["display_labels"] == {
        "observation": EMLIS_OBSERVATION_DISPLAY_LABEL,
        "reception": EMLIS_RECEPTION_DISPLAY_LABEL,
    }
    assert two_stage["section_order"] == list(EMLIS_TWO_STAGE_SECTION_ORDER)
    assert two_stage["surface_joiner"] == "comment_text_two_stage_joiner"
    assert two_stage["public_response_key_added"] is False
    assert two_stage["rn_visible_contract_changed"] is False
    assert two_stage["completed_reply_generated"] is False
    assert two_stage["comment_text_generated"] is False

    assert meta["observation_layer"]["display_label"] == EMLIS_OBSERVATION_DISPLAY_LABEL
    assert meta["human_follow_layer"]["display_label"] == EMLIS_RECEPTION_DISPLAY_LABEL
    assert reception_section["schema_version"] == EMLIS_RECEPTION_SECTION_MATERIAL_SCHEMA_VERSION
    assert reception_section["material_id"] == EMLIS_RECEPTION_SECTION_MATERIAL_ID
    assert reception_section["display_label"] == EMLIS_RECEPTION_DISPLAY_LABEL
    assert reception_section["section_role"] == "emlis_reception"
    assert reception_section["completed_reply_generated"] is False
    assert reception_section["comment_text_generated"] is False
    assert reception_section["public_response_key_added"] is False
    assert reception_section["rn_visible_contract_changed"] is False

    assert reception_mode["material_id"] == EMLIS_RECEPTION_MODE_SUMMARY_MATERIAL_ID
    assert reception_mode["reception_mode_id"] == "daily_unpleasant_reception"
    assert reception_mode["primary_reason"] == "event_fact_with_explicit_negative_reaction"
    assert reception_mode["backend_internal_mode_only"] is True
    assert reception_mode["public_response_key_added"] is False
    assert reception_mode["public_status_extended"] is False

    assert reception_assistance["dictionary_id"] == "emlis_reception_assistance_dictionary"
    assert reception_assistance["dictionary_material_only"] is True
    assert reception_assistance["general_dictionary_used"] is False
    assert reception_assistance["completed_reply_generated"] is False
    assert reception_assistance["comment_text_generated_by_dictionary"] is False

    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"raw_text":' not in encoded
    assert '"comment_text":' not in encoded
    assert '"observation_text":' not in encoded
    assert '"reception_text":' not in encoded


def test_phase7_forward_gate_and_composer_payload_keep_two_stage_material_safe() -> None:
    contract = build_emlis_state_answer_surface_contract(_two_stage_case_input("daily_unpleasant_encounter_A"))

    forward_meta = state_answer_surface_contract_forward_meta(contract)
    gate_report = state_answer_surface_contract_gate_report(forward_meta)
    composer_payload = state_answer_surface_contract_composer_payload(forward_meta)

    assert forward_meta["two_stage_reception_connected"] is True
    assert forward_meta["reception_section_material_connected"] is True
    assert forward_meta["reception_mode_connected"] is True
    assert forward_meta["reception_assistance_dictionary_connected"] is True
    assert forward_meta["two_stage_reception"]["public_response_key_added"] is False
    assert forward_meta["two_stage_reception"]["rn_visible_contract_changed"] is False

    assert gate_report["two_stage_reception_connected"] is True
    assert gate_report["two_stage_display_enabled"] is True
    assert gate_report["observation_display_label"] == EMLIS_OBSERVATION_DISPLAY_LABEL
    assert gate_report["reception_display_label"] == EMLIS_RECEPTION_DISPLAY_LABEL
    assert gate_report["two_stage_section_order"] == list(EMLIS_TWO_STAGE_SECTION_ORDER)
    assert gate_report["reception_mode_id"] == "daily_unpleasant_reception"
    assert gate_report["reception_assistance_dictionary_material_only"] is True
    assert gate_report["comment_text_generated"] is False
    assert gate_report["raw_text_included"] is False

    assert composer_payload["two_stage_reception_connected"] is True
    assert composer_payload["reception_section_material_connected"] is True
    assert composer_payload["two_stage_reception"]["material_id"] == EMLIS_TWO_STAGE_RECEPTION_MATERIAL_ID
    assert composer_payload["reception_section_material"]["material_id"] == EMLIS_RECEPTION_SECTION_MATERIAL_ID
    assert composer_payload["reception_mode"]["reception_mode_id"] == "daily_unpleasant_reception"
    assert composer_payload["reception_assistance"]["dictionary_material_only"] is True
    assert composer_payload["comment_text_generated"] is False
    assert composer_payload["raw_text_included"] is False
    assert composer_payload["rn_visible_contract_changed"] is False


def test_phase7_b_case_keeps_self_denial_or_uncertainty_mode_without_daily_unpleasant() -> None:
    current_input = _two_stage_case_input("self_confidence_uncertainty_B")

    meta = build_emlis_state_answer_surface_contract(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["two_stage_reception"]["display_labels"] == {
        "observation": EMLIS_OBSERVATION_DISPLAY_LABEL,
        "reception": EMLIS_RECEPTION_DISPLAY_LABEL,
    }
    assert meta["reception_section_material"]["display_label"] == EMLIS_RECEPTION_DISPLAY_LABEL
    assert meta["reception_mode"]["reception_mode_id"] in {"self_denial_support", "uncertainty_support"}
    assert meta["reception_mode"]["reception_mode_id"] != "daily_unpleasant_reception"
    assert meta["reception_mode"]["identity_claim_accepted_as_fact"] is False
    assert meta["reception_section_material"]["target_judgement_agreement_allowed"] is False
    assert meta["two_stage_reception"]["public_response_key_added"] is False
    assert meta["two_stage_reception"]["rn_visible_contract_changed"] is False
    assert current_input["memo"] not in encoded
    assert '"raw_text":' not in encoded
    assert '"comment_text":' not in encoded
