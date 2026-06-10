from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
    DECISION_P5_READY_AFTER_P4,
    PHASE_P4_FAMILY_TUNING,
    PHASE_P5_USER_LABEL_CONNECTION,
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_p4_p5_connection_decision_20260609 import (
    build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609,
    build_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609,
    dump_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609,
)


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _items_by_phase(decision: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item["target_phase"]): dict(item) for item in decision["connection_items"]}


def test_p4_0_freezes_p3_9_phase_connection_with_p4_allowed_and_p5_held() -> None:
    decision = build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        run_id="p4_0_connection_freeze"
    )
    summary = decision["summary"]
    items = _items_by_phase(decision)

    assert summary["next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert summary["p4_connection_allowed"] is True
    assert summary["p5_connection_allowed"] is False
    assert summary["p5_hold_until_current_only_readfeel_stable"] is True
    assert summary["current_only_readfeel_minimum_met"] is False
    assert summary["main_family_readfeel_minimum_met"] is False
    assert summary["repair_required_families"] == ["daily_unpleasant", "structure_question"]
    assert summary["yellow_families"] == ["self_denial"]
    assert summary["classified_reason_codes"] == [
        "rich_input_low_information_overroute",
        "generic_reception_surface",
    ]
    assert summary["first_repair_target_layers"] == ["input_material_bundle", "ratio_policy"]
    assert "current_only_readfeel_below_minimum" in summary["p5_hold_reason_codes"]
    assert "rich_input_low_information_overroute" in summary["p5_hold_reason_codes"]
    assert "generic_reception_surface" in summary["p5_hold_reason_codes"]
    assert items[PHASE_P4_FAMILY_TUNING]["allowed_to_connect"] is True
    assert items[PHASE_P5_USER_LABEL_CONNECTION]["allowed_to_connect"] is False
    assert "move_to_p4_family_product_tuning" in items[PHASE_P4_FAMILY_TUNING]["recommended_next_action"]
    assert items[PHASE_P5_USER_LABEL_CONNECTION]["recommended_next_action"] == "hold_p5_until_current_only_readfeel_is_stable"
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(decision)


def test_p4_0_keeps_runtime_contract_release_and_p5_visible_flags_false() -> None:
    decision = build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        run_id="p4_0_contract_freeze"
    )
    summary = decision["summary"]
    public_summary = build_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609(
        run_id="p4_0_contract_freeze_summary"
    )

    for payload in (decision, summary, public_summary):
        assert payload["p4_runtime_tuning_applied"] is False
        assert payload["p5_visible_surface_strengthened"] is False
        assert payload["p5_runtime_change_applied"] is False
        assert payload["runtime_repair_applied"] is False
        assert payload["implementation_change_applied"] is False
        assert payload["public_release_applied"] is False
        assert payload["gate_relaxed"] is False
        assert payload["raw_input_included"] is False
        assert payload["comment_text_included"] is False
        assert payload["comment_text_body_included"] is False
        assert payload["candidate_body_included"] is False
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(payload)

    assert summary["public_response_key_change"] is False
    assert summary["response_shape_changed"] is False
    assert summary["api_route_changed"] is False
    assert summary["db_physical_name_changed"] is False
    assert summary["rn_visible_contract_changed"] is False


def test_p4_0_public_summary_dump_is_body_free_and_does_not_look_like_p5_start() -> None:
    dumped = dump_product_readfeel_p3_p4_p5_connection_summary_from_regression_20260609(
        run_id="p4_0_dump"
    )
    parsed = json.loads(dumped)

    assert parsed["next_phase_decision"] == DECISION_P4_NEXT_P5_HOLD
    assert parsed["p4_connection_allowed"] is True
    assert parsed["p5_connection_allowed"] is False
    assert parsed["p5_visible_surface_strengthened"] is False
    assert parsed["p4_runtime_tuning_applied"] is False
    assert '"current_input"' not in dumped
    assert '"memo"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"candidate_body"' not in dumped
    assert "Emlisです" not in dumped
    assert DECISION_P5_READY_AFTER_P4 not in dumped
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(parsed)


def test_p4_0_freeze_guard_rejects_raw_or_comment_body_and_runtime_mutation_flags() -> None:
    decision = build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        run_id="p4_0_guard_source"
    )

    unsafe_raw = dict(decision)
    unsafe_raw["raw_input"] = "出してはいけない"
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(unsafe_raw)

    unsafe_comment = dict(decision)
    unsafe_comment["summary"] = dict(unsafe_comment["summary"])
    unsafe_comment["summary"]["comment_text"] = "Emlis本文をここに残してはいけない"
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(unsafe_comment)

    unsafe_p5 = dict(decision)
    unsafe_p5["p5_visible_surface_strengthened"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(unsafe_p5)

    unsafe_gate = dict(decision)
    unsafe_gate["summary"] = dict(unsafe_gate["summary"])
    unsafe_gate["summary"]["gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(unsafe_gate)

    assert '"raw_input":' not in _dump(decision)
