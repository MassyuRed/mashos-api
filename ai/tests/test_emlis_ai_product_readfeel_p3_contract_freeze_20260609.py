from __future__ import annotations

import json

import pytest

from emlis_ai_product_quality_contract_freeze import (
    RN_EMLIS_OBSERVATION_TITLE,
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
    dump_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES
from fixtures.emlis_ai_product_readfeel_fixture_families import (
    assert_product_readfeel_fixture_family_meta_only,
    build_product_readfeel_fixture_family_registry,
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_p3_0_contract_freeze_keeps_rn_api_db_gate_release_and_template_boundaries() -> None:
    freeze = build_emlis_ai_product_quality_contract_freeze()

    assert freeze["contract_frozen"] is True
    assert freeze["measurement_connection_only"] is True
    assert freeze["runtime_behavior_changed"] is False

    contract = freeze["contract_assertions"]
    assert contract["api_route_changed"] is False
    assert contract["request_key_changed"] is False
    assert contract["response_shape_changed"] is False
    assert contract["public_response_key_added"] is False
    assert contract["db_physical_name_changed"] is False
    assert contract["rn_visible_contract_changed"] is False
    assert contract["rn_visible_title_changed"] is False
    assert contract["display_gate_relaxed"] is False
    assert contract["grounding_gate_relaxed"] is False
    assert contract["reader_gate_relaxed"] is False
    assert contract["template_gate_relaxed"] is False
    assert contract["gate_relaxed"] is False
    assert contract["raw_input_included"] is False
    assert contract["comment_text_body_included"] is False
    assert contract["candidate_body_included"] is False

    rn_contract = freeze["rn_display_contract"]
    assert rn_contract["title"] == RN_EMLIS_OBSERVATION_TITLE == "Emlisの観測"
    assert rn_contract["requires_observation_status"] == "passed"
    assert rn_contract["requires_comment_text_non_empty"] is True
    assert rn_contract["contract_change_allowed"] is False

    api_contract = freeze["api_public_input_feedback_contract"]
    assert api_contract["route"] == "/emotion/submit"
    assert api_contract["comment_text_required"] is True
    assert api_contract["public_observation_status_required"] == "passed"
    assert api_contract["contract_change_allowed"] is False

    assert freeze["product_gate_ready"] is False
    assert freeze["product_gate_reached"] is False
    assert freeze["product_gate_public_release_applied"] is False
    assert freeze["public_release_applied"] is False
    assert freeze["public_release_applied"] is False

    dumped = dump_emlis_ai_product_quality_contract_freeze(freeze)
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"raw_input":' not in dumped


def test_p3_0_contract_freeze_blocks_exact_text_locks_and_case_specific_runtime_branches() -> None:
    freeze = build_emlis_ai_product_quality_contract_freeze()

    assert freeze["exact_comment_text_required"] is False
    assert freeze["case_specific_runtime_branch"] is False
    assert freeze["runtime_branching_uses_fixture_strings"] is False
    assert freeze["fixture_text_used_for_runtime_branching"] is False
    assert "exact comment_text fixture lock" in freeze["non_targets"]
    assert "case-specific runtime branch" in freeze["non_targets"]
    assert "fixture strings as runtime conditions" in freeze["non_targets"]

    for unsafe in (
        {"exact_comment_text_required": True},
        {"case_specific_runtime_branch": True},
        {"runtime_branching_uses_fixture_strings": True},
        {"fixture_text_used_for_runtime_branching": True},
        {"nested": {"case_specific_runtime_condition_allowed": True}},
    ):
        with pytest.raises(ValueError):
            assert_emlis_ai_product_quality_contract_freeze_meta_only(unsafe)


def test_p3_0_uses_existing_twelve_readfeel_families_without_family_enum_expansion() -> None:
    registry = build_product_readfeel_fixture_family_registry()

    assert len(PRODUCT_READFEEL_REQUIRED_FAMILIES) == 12
    assert tuple(registry["required_families"]) == PRODUCT_READFEEL_REQUIRED_FAMILIES
    assert registry["missing_families"] == []
    assert registry["phase3_fixture_family_definition_ready"] is True
    assert registry["exact_comment_text_required"] is False
    assert registry["case_specific_runtime_branch"] is False
    assert registry["runtime_branching_uses_fixture_strings"] is False
    assert registry["fixture_text_used_for_runtime_branching"] is False
    assert registry["product_gate_ready"] is False
    assert registry["public_release_applied"] is False
    assert "limited_grounding" not in registry["required_families"]
    assert "source_unavailable_high_information" not in registry["required_families"]
    assert_product_readfeel_fixture_family_meta_only(registry)


def test_p3_0_fixture_family_guard_still_rejects_body_payload_exact_lock_and_runtime_branch() -> None:
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"current_input": {"memo": "出してはいけない"}})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"comment_text": "固定文にしてはいけない"})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"exact_comment_text_required": True})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"case_specific_runtime_branch": True})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"fixture_text_used_for_runtime_branching": True})
    with pytest.raises(ValueError):
        assert_product_readfeel_fixture_family_meta_only({"product_gate_ready": True})


def test_p3_0_contract_freeze_material_is_meta_only_after_json_roundtrip() -> None:
    freeze = build_emlis_ai_product_quality_contract_freeze()
    parsed = json.loads(dump_emlis_ai_product_quality_contract_freeze(freeze))

    assert parsed["product_gate_ready"] is False
    assert parsed["public_release_applied"] is False
    assert parsed["contract_assertions"]["response_shape_changed"] is False
    assert parsed["contract_assertions"]["rn_visible_contract_changed"] is False
    assert parsed["exact_comment_text_required"] is False
    assert parsed["case_specific_runtime_branch"] is False
    assert_emlis_ai_product_quality_contract_freeze_meta_only(parsed)
    parsed_dump = _dump(parsed)
    assert '"raw_input":' not in parsed_dump
    assert '"comment_text_body":' not in parsed_dump
