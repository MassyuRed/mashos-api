from __future__ import annotations

from typing import Any

from emlis_ai_complete_focus_selector import build_complete_coverage_plan
from emlis_ai_complete_material_service import CompleteMaterialBundle, CompleteMaterialUnit
from emlis_ai_complete_relation_graph_service import (
    COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION,
    COMPLETE_RELATION_GRAPH_SERVICE_VERSION,
    COMPLETE_RELATION_GRAPH_STAGE,
    CompleteObservationGraphV2,
    CompleteRelationGraphNode,
    build_complete_relation_graph,
    build_complete_relation_graph_contract_meta,
    build_complete_relation_graph_meta,
    relation_surface_policy,
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


def test_step5_contract_meta_is_additive_and_bridges_existing_taxonomy() -> None:
    meta = build_complete_relation_graph_contract_meta()

    assert meta["version"] == COMPLETE_RELATION_GRAPH_SERVICE_VERSION
    assert meta["target_step"] == COMPLETE_RELATION_GRAPH_STAGE
    assert meta["relation_graph_bridge_added"] is True
    assert meta["observation_graph_2_0_bridge_added"] is True
    assert meta["existing_relation_taxonomy_bridged"] is True
    assert meta["relation_type_pre_generation_constraint"] is True
    assert meta["relation_type_preserved_in_meta"] is True
    assert meta["relation_type_preserved_in_sentence_binding_seed"] is True
    assert "contrast" in meta["allowed_relation_types"]
    assert "coexistence" in meta["allowed_relation_types"]
    assert "pressure" in meta["allowed_relation_types"]
    assert "recovery" in meta["allowed_relation_types"]
    assert "approach_avoidance" in meta["allowed_relation_types"]
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


def test_step5_builds_relation_graph_from_recovery_coverage_plan() -> None:
    bundle = CompleteMaterialBundle(
        coverage_group="recovery",
        materials=(
            _unit("load", role="fatigue_accumulation", relation_type="pressure", must_keep=True),
            _unit("repair", role="small_repair", relation_type="recovery", must_keep=True),
        ),
    )
    plan = build_complete_coverage_plan(material_bundle=bundle)
    graph = build_complete_relation_graph(coverage_plan=plan)
    meta = graph.as_meta()
    seed = graph.as_sentence_plan_seed()
    binding = graph.as_relation_binding_seed()

    assert isinstance(graph, CompleteObservationGraphV2)
    assert graph.ready is True
    assert meta["schema_version"] == COMPLETE_OBSERVATION_GRAPH_V2_SCHEMA_VERSION
    assert meta["target_step"] == COMPLETE_RELATION_GRAPH_STAGE
    assert meta["coverage_group"] == "recovery"
    assert meta["graph_node_count"] == 2
    assert set(meta["relation_types"]) == {"pressure", "recovery"}
    assert set(meta["used_evidence_span_ids"]) == {"s_load", "s_repair"}
    assert set(meta["used_phrase_unit_ids"]) == {"pu_load", "pu_repair"}
    assert meta["relation_type_preserved_in_sentence_binding_seed"] is True
    assert meta["relation_binding_seed"]["sentence_binding_count"] == 2
    assert set(binding["relation_types"]) == {"pressure", "recovery"}
    assert seed["target_step"] == "Step6_SentencePlan_2_0"
    assert set(row["relation_type"] for row in seed["relation_binding_seed"]["sentence_bindings"]) == {"pressure", "recovery"}
    assert any(edge["edge_role"] == "recovery_after_load_bridge" for edge in meta["relation_edges"])
    assert meta["limited_relation_taxonomy_bridge"]["all_relation_types_mapped"] is True
    assert meta["relation_after_text_generation"] is False
    assert meta["comment_text_generated"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step5_conflict_graph_preserves_approach_avoidance_constraint() -> None:
    bundle = CompleteMaterialBundle(
        coverage_group="conflict",
        materials=(
            _unit("wish", role="wish_to_rely", relation_type="approach_avoidance", must_keep=True),
            _unit("fear", role="burden_fear", relation_type="approach_avoidance", must_keep=True),
            _unit("value", role="value_wish", relation_type="coexistence"),
        ),
    )

    graph = build_complete_relation_graph(material_bundle=bundle)
    meta = graph.as_meta()
    policies = {item["relation_type"]: item for item in meta["relation_surface_policies"]}

    assert graph.ready is True
    assert meta["coverage_group"] == "conflict"
    assert "approach_avoidance" in meta["relation_types"]
    assert "approach_avoidance" in meta["all_relation_types"]
    assert policies["approach_avoidance"]["surface_intent"] == "preserve_approach_and_avoidance_together"
    assert "choose_one_side" in policies["approach_avoidance"]["forbidden_surface_keys"]
    assert set(row["relation_type"] for row in meta["relation_binding_seed"]["sentence_bindings"]).issuperset({"approach_avoidance"})
    assert meta["relation_type_pre_generation_constraint"] is True
    assert meta["completion_sentence_templates_added"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step5_can_build_from_evidence_spans_without_exposing_raw_input() -> None:
    graph = build_complete_relation_graph(
        coverage_group="energy_recovery",
        evidence_spans=[
            EvidenceSpan(span_id="s1", raw_text="今日は仕事で疲れて、集中も切れている。", start_index=0, end_index=22, detected_type="event", source_field="memo"),
            EvidenceSpan(span_id="s2", raw_text="お茶を飲んで少し落ち着いた。", start_index=23, end_index=39, detected_type="value", source_field="memo"),
        ],
    )
    meta = graph.as_meta()

    assert graph.ready is True
    assert meta["coverage_group"] == "recovery"
    assert set(meta["relation_types"]).intersection({"pressure", "recovery"})
    assert meta["source_coverage_plan_summary"]["source_step"] == "Step4_FocusSelector_CoveragePlan"
    assert meta["comment_text_generated"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step5_unavailable_when_relation_is_unmapped_or_source_bound_ids_are_missing() -> None:
    meta = build_complete_relation_graph_meta(
        coverage_plan={
            "coverage_group": "conflict",
            "sentence_budget": 2,
            "required_line_roles": ["opening", "core", "relation"],
            "focus_items": [
                {
                    "material_id": "rootless",
                    "phrase_unit_id": "pu_rootless",
                    "role": "value_wish",
                    "relation_type": "invented_relation",
                    "focus_rank": 1,
                    "source_anchor_present": False,
                }
            ],
        }
    )

    assert meta["status"] == "unavailable"
    assert meta["ready"] is False
    assert "relation_type_unmapped" in meta["validation_errors"]
    assert "evidence_span_id_missing" in meta["validation_errors"]
    assert "source_anchor_missing" in meta["validation_errors"]
    assert meta["all_relation_types_mapped"] is False
    assert meta["unmapped_relation_types"] == ["invented_relation"]
    assert meta["comment_text_generated"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_relation_graph_node_is_internal_sentence_plan_seed_not_public_response() -> None:
    node = CompleteRelationGraphNode(
        node_id="rg1",
        material_id="cm1",
        phrase_unit_id="pu1",
        evidence_span_id="s1",
        role="fatigue_accumulation",
        relation_type="pressure",
        focus_rank=1,
        must_keep=True,
        source_anchor_present=True,
        selection_reasons=("must_keep_material",),
    )
    meta = node.as_meta()
    focus = node.as_sentence_plan_focus()
    policy = relation_surface_policy("pressure")

    assert node.usable is True
    assert focus["relation_type"] == "pressure"
    assert focus["relation_pre_generation_constraint"] is True
    assert meta["comment_text_generated"] is False
    assert meta["fixed_sentence_template"] is False
    assert "comment_text" not in meta
    assert policy["surface_intent"] == "observe_pressure_without_personality_or_cause_claim"
    assert "diagnosis_claim" in policy["forbidden_surface_keys"]
    assert _contains_forbidden_raw_key(meta) is False
