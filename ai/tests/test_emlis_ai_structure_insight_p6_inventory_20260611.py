# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_inventory import (
    MODULE_MIRROR_ONLY_SURFACE_DETECTOR,
    MODULE_STRUCTURE_INSIGHT_GATE,
    P6_INVENTORY_TARGET_MODULE_IDS,
    STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_INVENTORY_STEP,
    STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION,
    assert_structure_insight_p6_inventory_contract,
    build_structure_insight_p6_inventory,
    dump_structure_insight_p6_inventory_public_summary,
)


FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "history_context",
    "historyContext",
    "history_records",
    "historyRecords",
    "history_raw_text",
    "historyRawText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "reply_text",
    "replyText",
    "display_text",
    "displayText",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_free_text",
    "raw_test_output",
    "test_output",
    "command_output",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _records_with(module_id: str, **patch: Any) -> list[dict[str, Any]]:
    records = [dict(record) for record in build_structure_insight_p6_inventory()["module_records"]]
    for record in records:
        if record["module_id"] == module_id:
            record.update(patch)
    return records


def test_p6_1_builds_body_free_inventory_for_existing_structure_insight_assets() -> None:
    inventory = build_structure_insight_p6_inventory(run_id="p6_inventory_ready_test")
    summary = inventory["summary"]

    assert inventory["schema_version"] == STRUCTURE_INSIGHT_P6_INVENTORY_SCHEMA_VERSION
    assert inventory["step"] == STRUCTURE_INSIGHT_P6_INVENTORY_STEP
    assert summary["schema_version"] == STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION
    assert summary["p6_inventory_ready"] is True
    assert summary["structure_insight_inventory_confirmed"] is True
    assert summary["ready_for_p6_entry_freeze"] is True
    assert summary["target_module_ids"] == list(P6_INVENTORY_TARGET_MODULE_IDS)
    assert summary["module_count"] == len(P6_INVENTORY_TARGET_MODULE_IDS)
    assert summary["found_module_count"] == len(P6_INVENTORY_TARGET_MODULE_IDS)
    assert summary["inventory_blockers"] == []
    assert summary["candidate_layer_seen"] is True
    assert summary["candidate_material_meta_only_confirmed"] is True
    assert summary["gate_layer_seen"] is True
    assert summary["gate_hardening_confirmed"] is True
    assert summary["limited_surface_layer_seen"] is True
    assert summary["limited_family_boundary_confirmed"] is True
    assert summary["deep_insight_suppression_confirmed"] is True
    assert summary["long_run_product_gate_split_confirmed"] is True
    assert summary["mirror_only_detector_confirmed"] is True
    assert summary["release_allowed"] is False
    assert summary["public_contract"]["public_response_key_added"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(inventory) is False
    assert_structure_insight_p6_inventory_contract(inventory)


def test_p6_1_classifies_existing_phases_as_reusable_but_not_roadmap_p6_completion() -> None:
    inventory = build_structure_insight_p6_inventory(run_id="p6_inventory_phase_boundary_test")
    records = {record["module_id"]: record for record in inventory["module_records"]}

    assert records["emlis_ai_structure_insight_candidate"]["existing_phase_label"] == "Phase7"
    assert records["emlis_ai_structure_insight_gate"]["existing_phase_label"] == "Phase9"
    assert records["emlis_ai_structure_insight_surface"]["existing_phase_label"] == "Phase10"
    assert all(record["existing_phase_is_roadmap_p6_complete"] is False for record in records.values())
    assert inventory["summary"]["existing_phase_to_roadmap_p6_mixed_up"] is False
    assert "emlis_ai_structure_insight_candidate" in inventory["summary"]["extension_needed_module_ids"]
    assert "emlis_ai_structure_insight_gate" in inventory["summary"]["extension_needed_module_ids"]


def test_p6_1_blocks_inventory_when_required_module_is_missing() -> None:
    inventory = build_structure_insight_p6_inventory(
        module_records=_records_with(MODULE_STRUCTURE_INSIGHT_GATE, found=False),
        run_id="p6_inventory_missing_gate_test",
    )
    summary = inventory["summary"]

    assert summary["p6_inventory_ready"] is False
    assert summary["structure_insight_inventory_confirmed"] is False
    assert MODULE_STRUCTURE_INSIGHT_GATE in summary["missing_required_module_ids"]
    assert f"required_structure_insight_module_missing:{MODULE_STRUCTURE_INSIGHT_GATE}" in summary["inventory_blockers"]


def test_p6_1_blocks_phase_confusion_and_missing_mirror_only_signal() -> None:
    phase_confusion = build_structure_insight_p6_inventory(
        module_records=_records_with("emlis_ai_structure_insight_candidate", existing_phase_is_roadmap_p6_complete=True),
        run_id="p6_inventory_phase_confusion_test",
    )
    assert phase_confusion["summary"]["p6_inventory_ready"] is False
    assert "existing_phase_marked_as_roadmap_p6_complete" in phase_confusion["summary"]["inventory_blockers"]

    mirror_missing = build_structure_insight_p6_inventory(
        module_records=_records_with(MODULE_MIRROR_ONLY_SURFACE_DETECTOR, mirror_only_detector_confirmed=False),
        run_id="p6_inventory_mirror_missing_test",
    )
    assert mirror_missing["summary"]["p6_inventory_ready"] is False
    assert "mirror_only_detector_not_confirmed" in mirror_missing["summary"]["inventory_blockers"]


def test_p6_1_public_summary_is_body_free_and_excludes_record_packets() -> None:
    dumped = dump_structure_insight_p6_inventory_public_summary(
        build_structure_insight_p6_inventory(run_id="p6_inventory_public_summary_source")
    )
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == STRUCTURE_INSIGHT_P6_INVENTORY_SUMMARY_SCHEMA_VERSION
    assert parsed["p6_inventory_ready"] is True
    assert parsed["public_response_key_added"] is False
    assert parsed["response_shape_changed"] is False
    assert parsed["raw_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["release_allowed"] is False
    assert '"module_records"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_test_output"' not in dumped
    assert _contains_forbidden_raw_key(parsed) is False
    assert_structure_insight_p6_inventory_contract(parsed, allow_partial=True)


def test_p6_1_contract_rejects_raw_payload_keys_release_and_public_contract_mutation() -> None:
    with pytest.raises(ValueError):
        assert_structure_insight_p6_inventory_contract({"comment_text": "must not leak"}, allow_partial=True)
    with pytest.raises(ValueError):
        assert_structure_insight_p6_inventory_contract({"release_allowed": True}, allow_partial=True)

    clean = build_structure_insight_p6_inventory(run_id="p6_inventory_contract_source")
    contract = dict(clean)
    contract["summary"] = {
        **clean["summary"],
        "public_contract": dict(clean["summary"]["public_contract"], public_response_key_added=True),
    }
    with pytest.raises(ValueError):
        assert_structure_insight_p6_inventory_contract(contract)
