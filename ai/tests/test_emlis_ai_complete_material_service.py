from __future__ import annotations

from typing import Any

from emlis_ai_complete_material_service import (
    COMPLETE_MATERIAL_SERVICE_VERSION,
    COMPLETE_MATERIAL_STAGE,
    CompleteMaterialBundle,
    CompleteMaterialUnit,
    build_complete_material_bundle,
    build_complete_material_service_contract_meta,
    build_complete_material_service_meta,
)
from emlis_ai_types import EvidenceSpan


def _contains_forbidden_raw_key(value: Any) -> bool:
    forbidden = {
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
    if isinstance(value, dict):
        return any(key in forbidden or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def test_step3_contract_meta_is_additive_and_does_not_touch_response_shape() -> None:
    meta = build_complete_material_service_contract_meta()

    assert meta["version"] == COMPLETE_MATERIAL_SERVICE_VERSION
    assert meta["target_step"] == COMPLETE_MATERIAL_STAGE
    assert meta["material_service_added"] is True
    assert meta["evidence_span_required"] is True
    assert meta["source_anchor_required"] is True
    assert meta["phrase_unit_role_required"] is True
    assert meta["relation_type_required"] is True
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["fixed_sentence_template_added"] is False
    assert meta["completion_sentence_templates_added"] is False
    assert meta["response_shape_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["raw_input_included"] is False


def test_step3_builds_source_bound_materials_from_evidence_spans_without_raw_meta() -> None:
    bundle = build_complete_material_bundle(
        evidence_spans=[
            EvidenceSpan(
                span_id="s1",
                raw_text="今日は仕事で疲れて、集中も切れている。",
                start_index=0,
                end_index=22,
                detected_type="event",
                source_field="memo",
            ),
            EvidenceSpan(
                span_id="s2",
                raw_text="お茶を飲んで少し落ち着いた。",
                start_index=23,
                end_index=39,
                detected_type="value",
                source_field="memo",
            ),
        ],
        coverage_group="energy_recovery",
    )

    assert isinstance(bundle, CompleteMaterialBundle)
    assert bundle.usable is True
    assert bundle.used_evidence_span_ids == ("s1", "s2")
    assert bundle.used_phrase_unit_ids
    assert set(bundle.role_types) >= {"fatigue_accumulation", "small_repair"}
    assert {unit.relation_type for unit in bundle.usable_materials} >= {"pressure", "recovery"}

    meta = bundle.as_meta()
    assert meta["target_step"] == COMPLETE_MATERIAL_STAGE
    assert meta["usable_material_count"] >= 2
    assert meta["comment_text_generated"] is False
    assert meta["response_shape_changed"] is False
    assert meta["raw_text_included"] is False
    assert meta["raw_input_included"] is False
    assert _contains_forbidden_raw_key(meta) is False
    assert all(row["source_anchor"]["source_anchor_present"] is True for row in meta["rows"])
    assert all(row["raw_text_included"] is False for row in meta["rows"])
    assert meta["focus_selector_input"]["raw_input_included"] is False


def test_step3_uses_existing_phrase_units_and_rejects_unsafe_material_before_sentence_plan() -> None:
    evidence_spans = [
        {"span_id": "s1", "raw_text": "仕事で疲れがたまっている", "source_field": "memo", "detected_type": "event", "start_index": 0, "end_index": 12},
        {"span_id": "s2", "raw_text": "不安", "source_field": "memo", "detected_type": "event", "start_index": 13, "end_index": 15},
        {"span_id": "s3", "raw_text": "自分のことを", "source_field": "memo", "detected_type": "event", "start_index": 16, "end_index": 22},
        {"span_id": "s4", "raw_text": "考え始め", "source_field": "memo", "detected_type": "event", "start_index": 23, "end_index": 27},
    ]
    phrase_units = [
        {"phrase_unit_id": "pu_good", "evidence_span_id": "s1", "compressed_text": "疲れが重なっていること", "role": "fatigue_accumulation", "polarity": "negative", "must_keep": True},
        {"phrase_unit_id": "pu_label", "evidence_span_id": "s2", "compressed_text": "不安", "role": "anxiety_return"},
        {"phrase_unit_id": "pu_particle", "evidence_span_id": "s3", "compressed_text": "自分のことを", "role": "current_expression"},
        {"phrase_unit_id": "pu_unfinished", "evidence_span_id": "s4", "compressed_text": "考え始め", "role": "anticipation_loop"},
        {"phrase_unit_id": "pu_rootless", "compressed_text": "疲れが重なっていること", "role": "fatigue_accumulation"},
    ]

    bundle = build_complete_material_bundle(evidence_spans=evidence_spans, phrase_units=phrase_units)
    meta = bundle.as_meta()

    assert {unit.phrase_unit_id for unit in bundle.usable_materials} == {"pu_good"}
    assert meta["usable_material_count"] == 1
    assert meta["rejected_material_count"] == 4
    blocked = meta["blocked_reason_keys"]
    assert "emotion_label_only" in blocked
    assert "orphan_particle" in blocked
    assert "unfinished_phrase" in blocked
    assert "evidence_span_id_missing" in blocked
    assert meta["rows"][0]["relation_type"] == "pressure"
    assert meta["rows"][0]["canonical_relation_type"] == "pressure"
    assert meta["rows"][0]["relation_family"] == "pressure_or_load"
    assert _contains_forbidden_raw_key(meta) is False


def test_step3_rejects_non_text_evidence_and_overclaim_safety_material() -> None:
    meta = build_complete_material_service_meta(
        evidence_spans=[
            {"span_id": "s1", "raw_text": "悲しみ", "source_field": "emotion_details", "detected_type": "emotion"},
            {"span_id": "s2", "raw_text": "これはADHDの症状です", "source_field": "memo", "detected_type": "event"},
            {"span_id": "s3", "raw_text": "でも", "source_field": "memo", "detected_type": "relation_marker"},
        ]
    )

    assert meta["usable_material_count"] == 0
    assert meta["usable"] is False
    blocked = meta["blocked_reason_keys"]
    assert "non_text_material_source" in blocked
    assert "unsafe_or_overclaim_material" in blocked
    assert "connector_only_material" in blocked
    assert meta["comment_text_generated"] is False
    assert meta["raw_input_required_for_improvement"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_complete_material_unit_is_sentence_plan_seed_but_not_public_response() -> None:
    unit = CompleteMaterialUnit(
        material_id="cm1",
        phrase_unit_id="pu1",
        evidence_span_id="s1",
        material_text="頼りたい気持ち",
        role="wish_to_rely",
        polarity="mixed",
        must_keep=True,
        source_anchor={"evidence_span_id": "s1", "source_field": "memo", "start_index": 0, "end_index": 6, "source_anchor_present": True},
    )

    seed = unit.as_focus_seed()
    meta = unit.as_meta()

    assert unit.usable is True
    assert seed["phrase_unit_id"] == "pu1"
    assert seed["evidence_span_id"] == "s1"
    assert seed["relation_type"] in {"approach", "approach_avoidance"}
    assert meta["raw_input_included"] is False
    assert meta["fixed_sentence_template"] is False
    assert "comment_text" not in meta
    assert _contains_forbidden_raw_key(meta) is False
