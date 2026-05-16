from __future__ import annotations

from typing import Any

from emlis_ai_complete_focus_selector import (
    COMPLETE_COVERAGE_PLAN_SCHEMA_VERSION,
    COMPLETE_FOCUS_SELECTOR_STAGE,
    COMPLETE_FOCUS_SELECTOR_VERSION,
    CompleteCoveragePlan,
    CompleteFocusItem,
    build_complete_coverage_plan,
    build_complete_focus_selector_contract_meta,
    build_complete_focus_selector_meta,
)
from emlis_ai_complete_material_service import CompleteMaterialBundle, CompleteMaterialUnit
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


def _unit(
    material_id: str,
    *,
    role: str,
    relation_type: str,
    must_keep: bool = False,
    evidence_span_id: str | None = None,
) -> CompleteMaterialUnit:
    span_id = evidence_span_id or f"s_{material_id}"
    return CompleteMaterialUnit(
        material_id=material_id,
        phrase_unit_id=f"pu_{material_id}",
        evidence_span_id=span_id,
        material_text=f"{role}の材料",
        role=role,
        relation_type=relation_type,
        polarity="mixed",
        must_keep=must_keep,
        source_anchor={
            "evidence_span_id": span_id,
            "source_field": "memo",
            "start_index": 0,
            "end_index": 8,
            "source_anchor_present": True,
        },
    )


def test_step4_contract_meta_is_additive_and_does_not_touch_public_shape() -> None:
    meta = build_complete_focus_selector_contract_meta()

    assert meta["version"] == COMPLETE_FOCUS_SELECTOR_VERSION
    assert meta["target_step"] == COMPLETE_FOCUS_SELECTOR_STAGE
    assert meta["focus_selector_added"] is True
    assert meta["coverage_plan_added"] is True
    assert meta["selects_observation_nucleus"] is True
    assert meta["summarize_all_materials"] is False
    assert "short_daily" in meta["coverage_groups_supported"]
    assert "long_meaning_arc" in meta["coverage_groups_supported"]
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["fixed_sentence_template_added"] is False
    assert meta["response_shape_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["raw_input_included"] is False


def test_step4_builds_recovery_coverage_plan_with_prior_pressure_support() -> None:
    bundle = CompleteMaterialBundle(
        coverage_group="recovery",
        materials=(
            _unit("load", role="fatigue_accumulation", relation_type="pressure", must_keep=True),
            _unit("repair", role="small_repair", relation_type="recovery", must_keep=True),
        ),
    )

    plan = build_complete_coverage_plan(material_bundle=bundle)
    meta = plan.as_meta()
    seed = plan.as_sentence_plan_seed()

    assert isinstance(plan, CompleteCoveragePlan)
    assert plan.ready is True
    assert meta["schema_version"] == COMPLETE_COVERAGE_PLAN_SCHEMA_VERSION
    assert meta["target_step"] == COMPLETE_FOCUS_SELECTOR_STAGE
    assert meta["coverage_group"] == "recovery"
    assert meta["sentence_budget"] == 3
    assert set(meta["relation_types"]) >= {"pressure", "recovery"}
    assert set(meta["used_evidence_span_ids"]) == {"s_load", "s_repair"}
    assert meta["summarize_all_materials"] is False
    assert meta["comment_text_generated"] is False
    assert seed["target_step"] == "Step6_SentencePlan_2_0"
    assert set(seed["required_line_roles"]) >= {"opening", "core", "relation"}
    assert _contains_forbidden_raw_key(meta) is False


def test_step4_conflict_selector_keeps_observation_nucleus_and_defers_extra_materials() -> None:
    bundle = CompleteMaterialBundle(
        coverage_group="conflict",
        materials=(
            _unit("wish", role="wish_to_rely", relation_type="approach_avoidance", must_keep=True),
            _unit("fear", role="burden_fear", relation_type="approach_avoidance", must_keep=True),
            _unit("value", role="value_wish", relation_type="coexistence"),
            _unit("load", role="fatigue_accumulation", relation_type="pressure"),
            _unit("repair", role="small_repair", relation_type="recovery"),
        ),
    )

    plan = build_complete_coverage_plan(material_bundle=bundle)
    meta = plan.as_meta()

    assert plan.ready is True
    assert meta["coverage_group"] == "conflict"
    assert meta["sentence_budget"] == 3
    assert meta["selected_focus_count"] == 3
    assert meta["optional_focus_count"] == 2
    assert "approach_avoidance" in meta["relation_types"]
    assert meta["observation_nucleus_selected"] is True
    assert meta["full_summary_mode"] is False
    assert set(meta["optional_material_ids"]).issubset({"load", "repair", "value"})
    assert _contains_forbidden_raw_key(meta) is False


def test_step4_short_daily_caps_focus_and_marks_overinterpretation_guard() -> None:
    bundle = CompleteMaterialBundle(
        coverage_group="short_daily",
        materials=(
            _unit("state", role="loss_of_control", relation_type="pressure", must_keep=True),
            _unit("wobble", role="anxiety_return", relation_type="contrast"),
            _unit("context", role="known_action", relation_type="context"),
            _unit("repair", role="small_repair", relation_type="recovery"),
        ),
    )

    plan = build_complete_coverage_plan(material_bundle=bundle)
    meta = plan.as_meta()

    assert plan.ready is True
    assert meta["coverage_group"] == "short_daily"
    assert meta["sentence_budget"] == 2
    assert meta["selected_focus_count"] == 2
    assert meta["optional_focus_count"] == 2
    assert meta["short_input_overinterpretation_guard_enabled"] is True
    assert meta["summarize_all_materials"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step4_can_build_from_material_service_input_without_raw_text() -> None:
    plan = build_complete_coverage_plan(
        coverage_group="energy_recovery",
        evidence_spans=[
            EvidenceSpan(span_id="s1", raw_text="今日は仕事で疲れて、集中も切れている。", start_index=0, end_index=22, detected_type="event", source_field="memo"),
            EvidenceSpan(span_id="s2", raw_text="お茶を飲んで少し落ち着いた。", start_index=23, end_index=39, detected_type="value", source_field="memo"),
        ],
    )
    meta = plan.as_meta()

    assert plan.ready is True
    assert meta["coverage_group"] == "recovery"
    assert meta["selected_focus_count"] >= 1
    assert set(meta["relation_types"]).intersection({"pressure", "recovery"})
    assert meta["source_material_summary"]["source_step"] == "Step3_Material_service"
    assert meta["comment_text_generated"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step4_unavailable_when_materials_are_missing_or_not_source_bound() -> None:
    meta = build_complete_focus_selector_meta(
        focus_selector_input={
            "coverage_group": "history_cross_core",
            "materials": [
                {
                    "material_id": "rootless",
                    "phrase_unit_id": "pu_rootless",
                    "role": "known_action",
                    "relation_type": "context",
                    "must_keep": True,
                    "source_anchor": {"source_anchor_present": False},
                }
            ],
        }
    )

    assert meta["status"] == "unavailable"
    assert meta["ready"] is False
    assert meta["coverage_group"] == "history_cross_core"
    assert "evidence_span_id_missing" in meta["validation_errors"]
    assert "source_anchor_missing" in meta["validation_errors"]
    assert meta["history_cross_core_requires_explicit_evidence"] is True
    assert meta["comment_text_generated"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_complete_focus_item_is_internal_sentence_plan_seed_not_public_response() -> None:
    item = CompleteFocusItem(
        material_id="cm1",
        phrase_unit_id="pu1",
        evidence_span_id="s1",
        role="wish_to_rely",
        relation_type="approach_avoidance",
        focus_rank=1,
        must_keep=True,
        source_anchor_present=True,
        selection_reasons=("must_keep_material",),
    )

    focus_seed = item.as_sentence_plan_focus()
    meta = item.as_meta()

    assert item.usable is True
    assert focus_seed["phrase_unit_id"] == "pu1"
    assert focus_seed["relation_type"] == "approach_avoidance"
    assert focus_seed["raw_input_included"] is False
    assert meta["comment_text_generated"] is False
    assert meta["fixed_sentence_template"] is False
    assert "comment_text" not in meta
    assert _contains_forbidden_raw_key(meta) is False
