from __future__ import annotations

from typing import Any

from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
    build_complete_product_quality_surface_variation_report,
    build_complete_surface_realization_v2,
    build_complete_surface_signature,
)
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_relation_surface_contract import RELATION_SURFACE_CONTRACT_VERSION, detect_relation_surface

_FORBIDDEN_RAW_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo_text",
    "raw_user_text",
    "original_text",
    "source_text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _positive_recovery_seed() -> dict[str, Any]:
    return {
        "coverage_group": "recovery",
        "sentence_budget": 3,
        "graph_nodes": [
            {
                "node_id": "n-load",
                "material_id": "m-load",
                "phrase_unit_id": "pu-load",
                "evidence_span_id": "span-load",
                "role": "fatigue_accumulation",
                "relation_type": "pressure",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n-repair",
                "material_id": "m-repair",
                "phrase_unit_id": "pu-repair",
                "evidence_span_id": "span-repair",
                "role": "small_repair",
                "relation_type": "recovery",
                "must_keep": True,
                "source_anchor_present": True,
            },
        ],
    }


def _relation_line(realization):
    return next(line for line in realization.surface_lines if line.line_role == "relation" and line.relation_type == "recovery")


def test_step4_surface_recovery_relation_line_uses_relation_surface_contract() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_positive_recovery_seed())
    relation_line = _relation_line(realization)

    assert realization.ready is True
    assert relation_line.surface_text == "戻ってくる動きとその前の重さが同じ流れの中でつながっています。"
    assert relation_line.connector_key == "relation_recovery_contract_load_bridge"
    assert relation_line.predicate_key == "recovery_load_bridge_contract"
    assert relation_line.ending_key == "tsunagaru"
    assert relation_line.meta["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert relation_line.meta["surface_recovery_relation_line_aligned"] is True
    assert relation_line.meta["relation_marker_key"] == "recovery_load_bridge_v1"
    assert relation_line.meta["reader_relation_signal_detected"] is True
    assert "recovery_load_bridge" in relation_line.meta["reader_relation_signal_keys"]
    assert relation_line.meta["meaning_added"] is False
    assert relation_line.meta["gate_relaxed"] is False
    assert relation_line.meta["raw_input_included"] is False


def test_step4_surface_signature_and_grounding_expose_recovery_contract_without_template_major() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_positive_recovery_seed())
    relation_line = _relation_line(realization)
    signature = relation_line.surface_signature
    surface_signature = build_complete_surface_signature(realization)
    variation_report = build_complete_product_quality_surface_variation_report(realization)
    grounding = realization.as_grounding_input()
    meta = realization.as_meta(include_realized_text=False)

    assert signature["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert signature["surface_recovery_relation_line_aligned"] is True
    assert signature["surface_recovery_relation_alignment_step"] == COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP
    assert signature["relation_marker_key"] == "recovery_load_bridge_v1"
    assert signature["connector_key"] == "relation_recovery_contract_load_bridge"
    assert signature["predicate_key"] == "recovery_load_bridge_contract"
    assert signature["completion_sentence_template_used"] is False
    assert signature["role_completed_sentence_template_used"] is False
    assert signature["input_specific_template_used"] is False
    assert signature["raw_input_included"] is False

    assert surface_signature["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert surface_signature["surface_recovery_relation_line_aligned"] is True
    assert "recovery_load_bridge_v1" in surface_signature["surface_relation_marker_keys"]
    assert grounding["surface_recovery_relation_line_aligned"] is True
    assert "recovery_load_bridge" in grounding["reader_relation_signal_keys"]
    assert meta["relation_surface_report"]["surface_recovery_relation_line_aligned"] is True
    assert variation_report["passed"] is True
    assert variation_report["release_blocker"] is False
    assert variation_report["same_ending_major_count"] == 0
    assert variation_report["surface_signature_repeat_count"] == 0
    assert _contains_forbidden_raw_key(meta) is False


def test_step4_surface_recovery_text_is_reader_detectable_without_relaxing_reader_gate() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_positive_recovery_seed())
    signal = detect_relation_surface(realization.realized_text, expected_relation_types=("positive_recovery",))
    reader_report = judge_listener_readability(realization.realized_text, expected_relation_types=("positive_recovery",))

    assert signal["reader_relation_signal_detected"] is True
    assert "recovery" in signal["reader_relation_signal_relation_types"]
    assert "relation_not_expressed" not in reader_report.rejection_reasons
