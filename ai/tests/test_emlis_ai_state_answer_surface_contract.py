from __future__ import annotations

import json

from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_state_answer_surface_contract import (
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_MATERIAL_ID,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_PHASE,
    EMLIS_STATE_ANSWER_SURFACE_CONTRACT_SCHEMA_VERSION,
    build_emlis_state_answer_surface_contract,
    state_answer_surface_contract_composer_payload,
    state_answer_surface_contract_forward_meta,
    state_answer_surface_contract_gate_report,
)


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
    surface_policy = meta["surface_policy"]

    assert surface_policy["completed_reply_generated"] is False
    assert surface_policy["comment_text_generated"] is False
    assert surface_policy["public_payload_changed"] is False
    assert surface_policy["public_response_key_added"] is False
    assert surface_policy["api_route_changed"] is False
    assert surface_policy["response_key_changed"] is False
    assert surface_policy["db_physical_name_changed"] is False
    assert surface_policy["rn_visible_contract_changed"] is False
    assert surface_policy["schema_file_materialized"] is False
    assert surface_policy["must_not_generate_cause_from_category"] is True
    assert surface_policy["must_not_generate_cause_from_emotion_strength"] is True
    assert surface_policy["must_not_generate_period_tendency_from_single_record"] is True
    assert surface_policy["cause_from_category"] is False
    assert surface_policy["cause_from_emotion_strength"] is False
    assert surface_policy["period_tendency_from_single_record"] is False
    assert surface_policy["personality_tendency_allowed"] is False


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
    assert meta["surface_policy"]["cause_from_category"] is False
    assert meta["surface_policy"]["cause_from_emotion_strength"] is False
    assert meta["surface_policy"]["period_tendency_from_single_record"] is False
    assert current_input["memo"] not in encoded
    assert '"raw_text":' not in encoded
