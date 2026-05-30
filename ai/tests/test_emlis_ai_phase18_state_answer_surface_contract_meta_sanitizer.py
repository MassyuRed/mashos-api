from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_observation_structure_material_service import (
    build_observation_structure_material,
    observation_structure_material_composer_payload,
    observation_structure_material_forward_meta,
    observation_structure_material_gate_report,
)
from emlis_ai_state_answer_surface_contract import (
    build_emlis_state_answer_surface_contract,
    state_answer_surface_contract_composer_payload,
    state_answer_surface_contract_forward_meta,
    state_answer_surface_contract_gate_report,
)

_FORBIDDEN_KEYS = {
    "surface_policy",
    "definition",
    "evidence_requirements",
    "allowed_inference",
    "forbidden_inference",
    "default_direction",
    "strong_hand_direction",
    "notes",
    "raw_input",
    "raw_text",
    "comment_text",
    "body",
    "text",
}


def _current_input() -> dict[str, object]:
    return {
        "id": "phase18-state-answer-meta-sanitizer-1",
        "created_at": "2026-05-30T00:00:00Z",
        "memo": "本当は言いたくなかったけど、その場に合わせて飲み込んだ",
        "memo_action": "相手には大丈夫そうに返した",
        "emotion_details": [
            {"type": "嫌悪", "strength": "medium"},
            {"type": "不安", "strength": "medium"},
        ],
        "category": ["人間関係"],
    }


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            assert key not in _FORBIDDEN_KEYS
            _assert_no_forbidden_keys(child)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_keys(item)


def test_phase18_state_answer_surface_contract_projects_policy_to_summary_flags_only() -> None:
    contract = build_emlis_state_answer_surface_contract(_current_input())

    payloads = (
        contract.as_meta(),
        state_answer_surface_contract_forward_meta(contract),
        state_answer_surface_contract_gate_report(contract),
        state_answer_surface_contract_composer_payload(contract),
    )

    for payload in payloads:
        _assert_no_forbidden_keys(payload)
        dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert "本当は言いたくなかった" not in dumped
        assert "相手には大丈夫そうに返した" not in dumped
        assert payload.get("public_response_key_added") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("display_gate_relaxed") is not True

    meta = payloads[0]
    assert meta["meta_only_sanitizer_schema_version"] == "cocolon.emlis.meta_only_sanitizer.v1"
    assert meta["meta_only_sanitizer_source_phase"] == "Phase18_product_quality_stabilization"
    assert meta["state_answer_surface_policy_material_only"] is True
    assert meta["state_answer_surface_policy_must_not_generate_completed_reply"] is True
    assert meta["state_answer_surface_policy_must_not_generate_comment_text"] is True
    assert meta["state_answer_surface_policy_forbidden_claim_count"] >= 1
    assert meta["surface_policy_key_included"] is False
    assert meta["dictionary_text_key_included"] is False
    assert meta["ratio_policy"]["state_answer_ratio_policy_surface_policy_material_only"] is True


def test_phase18_observation_structure_material_payloads_do_not_reintroduce_policy_bodies() -> None:
    material = build_observation_structure_material(current_input=_current_input())

    payloads = (
        material.as_meta(),
        observation_structure_material_forward_meta(material),
        observation_structure_material_composer_payload(material),
        observation_structure_material_gate_report(material),
    )

    for payload in payloads:
        _assert_no_forbidden_keys(payload)
        dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert "本当は言いたくなかった" not in dumped
        assert "相手には大丈夫そうに返した" not in dumped
        assert payload.get("comment_text_generated") is False
        assert payload.get("raw_input_included") is False
        assert payload.get("raw_text_included") is False
        assert payload.get("public_response_key_added") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("display_gate_relaxed") is False

    meta = payloads[0]
    contract_meta = meta["state_answer_surface_contract"]
    assert contract_meta["state_answer_surface_policy_material_only"] is True
    assert contract_meta["surface_policy_key_included"] is False
    assert contract_meta["dictionary_text_key_included"] is False
