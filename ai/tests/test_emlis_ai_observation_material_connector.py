from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_complete_focus_selector import build_complete_coverage_plan
from emlis_ai_complete_material_service import build_complete_material_bundle
from emlis_ai_complete_relation_graph_service import build_complete_relation_graph
from emlis_ai_observation_material_connector import (
    LOW_INFORMATION_RELATION_CONFIDENCE_LIMIT,
    OBSERVATION_MATERIAL_CONNECTOR_STEP,
    assert_material_focus_relation_connector_contract,
    build_material_focus_relation_connector,
    dump_material_focus_relation_connector,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_EVENT,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
)


def _input(memo: str) -> dict[str, Any]:
    return {
        "id": f"obs-step6-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def _evidence_and_phrase_units() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        [
            {
                "span_id": "s_known_scope",
                "raw_text": "言葉になる前の重さが残っている",
                "source_field": "memo",
                "detected_type": "event",
                "start_index": 0,
                "end_index": 16,
            }
        ],
        [
            {
                "phrase_unit_id": "pu_known_scope",
                "evidence_span_id": "s_known_scope",
                "compressed_text": "言葉になる前の重さが残っていること",
                "role": "fatigue_accumulation",
                "relation_type": "pressure",
                "polarity": "negative",
                "must_keep": True,
            }
        ],
    )


def _eligible_evidence_and_phrase_units() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        [
            {
                "span_id": "s_wish",
                "raw_text": "環境を変えたい気持ちがある",
                "source_field": "memo",
                "detected_type": "event",
                "start_index": 0,
                "end_index": 14,
            },
            {
                "span_id": "s_block",
                "raw_text": "変えられない状態が続いて疲れている",
                "source_field": "memo",
                "detected_type": "event",
                "start_index": 15,
                "end_index": 33,
            },
        ],
        [
            {
                "phrase_unit_id": "pu_wish",
                "evidence_span_id": "s_wish",
                "compressed_text": "環境を変えたい気持ちがあること",
                "role": "value_wish",
                "relation_type": "coexistence",
                "polarity": "mixed",
                "must_keep": True,
            },
            {
                "phrase_unit_id": "pu_block",
                "evidence_span_id": "s_block",
                "compressed_text": "変えられない状態が続いて疲れていること",
                "role": "fatigue_accumulation",
                "relation_type": "pressure",
                "polarity": "negative",
                "must_keep": True,
            },
        ],
    )


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
        "comment_text",
        "commentText",
    }
    if isinstance(value, dict):
        return any(key in forbidden or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def test_step6_connector_builds_low_information_known_scope_contract() -> None:
    connector = build_material_focus_relation_connector(current_input=_input("疲れた"), subscription_tier="free")
    meta = connector.as_meta()
    dumped = dump_material_focus_relation_connector(connector)

    assert meta["source_step"] == OBSERVATION_MATERIAL_CONNECTOR_STEP
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    assert meta["eligible_for_full_observation"] is False
    assert meta["question_required"] is True
    assert UNKNOWN_SLOT_EVENT in meta["unknown_slots"]
    assert meta["known_scope_only"] is True
    assert meta["low_information_known_scope_only"] is True
    assert meta["deep_relation_allowed"] is False
    assert meta["relation_confidence_limit"] == LOW_INFORMATION_RELATION_CONFIDENCE_LIMIT
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert "疲れた" not in dumped
    assert _contains_forbidden_raw_key(meta) is False
    assert_material_focus_relation_connector_contract(meta)


def test_step6_flows_low_information_meta_to_material_focus_and_relation_layers() -> None:
    evidence_spans, phrase_units = _evidence_and_phrase_units()
    bundle = build_complete_material_bundle(
        evidence_spans=evidence_spans,
        phrase_units=phrase_units,
        current_input=_input("疲れた"),
        subscription_tier="free",
    )
    bundle_meta = bundle.as_meta()
    focus_input = bundle.as_focus_selector_input()

    assert bundle_meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert bundle_meta["known_scope_only"] is True
    assert focus_input["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert focus_input["materials"][0]["low_information_known_scope_only"] is True

    plan = build_complete_coverage_plan(material_bundle=bundle)
    plan_meta = plan.as_meta()
    assert plan_meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert plan_meta["low_information_known_scope_only"] is True
    assert plan_meta["focus_selection_mode"] == "known_scope_only"
    assert plan_meta["selected_focus_count"] == 1
    assert plan_meta["focus_rows"][0]["focus_role"] == "known_scope"
    assert "central_target_selection_blocked" in plan_meta["focus_rows"][0]["selection_reasons"]

    graph = build_complete_relation_graph(coverage_plan=plan)
    graph_meta = graph.as_meta()
    assert graph_meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert graph_meta["deep_relation_allowed"] is False
    assert graph_meta["relation_confidence_limited"] is True
    assert graph_meta["relation_binding_seed"]["deep_relation_allowed"] is False
    assert graph_meta["relation_binding_seed"]["sentence_bindings"][0]["focus_selection_mode"] == "known_scope_only"
    assert graph_meta["comment_text_generated"] is False
    assert graph_meta["public_response_key_change"] is False
    assert _contains_forbidden_raw_key(graph_meta) is False


def test_step6_eligible_meta_allows_depth_three_relation_flow() -> None:
    evidence_spans, phrase_units = _eligible_evidence_and_phrase_units()
    current_input = _input("環境を変えたいけど、変えられなくて疲れた。")
    bundle = build_complete_material_bundle(
        evidence_spans=evidence_spans,
        phrase_units=phrase_units,
        current_input=current_input,
        subscription_tier="free",
    )
    plan = build_complete_coverage_plan(material_bundle=bundle)
    graph = build_complete_relation_graph(coverage_plan=plan)
    meta = graph.as_meta()

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["eligibility_status"] == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    assert meta["eligible_for_full_observation"] is True
    assert meta["question_required"] is False
    assert meta["deep_relation_allowed"] is True
    assert meta["known_scope_only"] is False
    assert meta["max_inference_depth_used"] == 3
    assert meta["relation_depth_policy"] == "eligible_depth_1_to_3"
    assert meta["relation_binding_seed"]["deep_relation_allowed"] is True
    assert set(meta["used_evidence_span_ids"]) == {"s_wish", "s_block"}
    assert _contains_forbidden_raw_key(meta) is False


def test_step6_subscription_low_information_user_fact_is_hint_not_promotion() -> None:
    connector = build_material_focus_relation_connector(
        current_input=_input("疲れた"),
        subscription_tier="premium",
        user_facts=[{"fact_id": "fact-env-001", "source_kind": "derived_user_model", "text": "環境の話"}],
    )
    meta = connector.as_meta()
    dumped = dump_material_focus_relation_connector(meta)

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert meta["user_fact_focus_hint_ids"] == ["fact-env-001"]
    assert meta["user_fact_may_hint"] is True
    assert meta["user_fact_may_promote_to_eligible"] is False
    assert "internal_question_answer" not in meta["allowed_user_fact_uses"]
    assert meta["deep_relation_allowed"] is False
    assert "環境の話" not in dumped
    assert "text" not in json.dumps(meta["facts_used"], ensure_ascii=False)
    assert_material_focus_relation_connector_contract(meta)


def test_step6_contract_rejects_raw_payload_public_drift_and_low_info_promotion() -> None:
    valid = build_material_focus_relation_connector(current_input=_input("疲れた"), subscription_tier="free").as_meta()

    invalid_raw = dict(valid)
    invalid_raw["raw_input"] = "疲れた"
    with pytest.raises(ValueError):
        assert_material_focus_relation_connector_contract(invalid_raw)

    invalid_public = dict(valid)
    invalid_public["api_route_changed"] = True
    with pytest.raises(ValueError):
        assert_material_focus_relation_connector_contract(invalid_public)

    invalid_promotion = dict(valid)
    invalid_promotion["user_fact_may_promote_to_eligible"] = True
    with pytest.raises(ValueError):
        assert_material_focus_relation_connector_contract(invalid_promotion)

    invalid_deep = dict(valid)
    invalid_deep["deep_relation_allowed"] = True
    with pytest.raises(ValueError):
        assert_material_focus_relation_connector_contract(invalid_deep)
