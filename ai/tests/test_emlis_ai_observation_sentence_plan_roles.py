from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_complete_focus_selector import build_complete_coverage_plan
from emlis_ai_complete_material_service import build_complete_material_bundle
from emlis_ai_complete_relation_graph_service import build_complete_relation_graph
from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2_meta
from emlis_ai_observation_reply_contract import (
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_EMPATHY,
    OBSERVATION_ROLE_INPUT_ARRANGEMENT,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    OBSERVATION_ROLE_STATE_VERBALIZATION,
    USER_FACT_GROUNDING_MODE_DISABLED,
)
from emlis_ai_observation_sentence_plan_roles import (
    OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
    SURFACE_ROLE_MERGE_EMPATHY_INPUT_ARRANGEMENT,
    assert_observation_sentence_plan_roles_contract,
    build_observation_sentence_plan_roles_contract_meta,
    dump_observation_sentence_plan_roles,
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


def _input(memo: str) -> dict[str, Any]:
    return {
        "id": f"obs-step7-{abs(hash(memo))}",
        "created_at": "2026-05-20T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "emotions": ["疲れ"],
        "category": ["生活"],
    }


def _low_info_evidence_and_phrase_units() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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


def test_step7_contract_meta_is_meta_only_and_preserves_existing_line_role_contract() -> None:
    meta = build_observation_sentence_plan_roles_contract_meta()

    assert meta["source_step"] == OBSERVATION_SENTENCE_PLAN_ROLES_STEP
    assert meta["sentence_plan_observation_roles_added"] is True
    assert meta["existing_line_role_preserved"] is True
    assert meta["observation_roles_meta_only"] is True
    assert meta["short_eligible_role_merge_allowed"] is True
    assert meta["low_info_question_role_required"] is True
    assert meta["public_line_role_enum_extended"] is False
    assert meta["comment_text_generated"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step7_short_eligible_merges_empathy_and_input_arrangement_but_keeps_state_role() -> None:
    meta = build_complete_sentence_plan_v2_meta(
        sentence_plan_seed={
            "coverage_group": "short_daily",
            "sentence_budget": 4,
            "observation_reply_kind": OBSERVATION_REPLY_KIND_ELIGIBLE,
            "eligibility_status": "eligible",
            "question_required": False,
            "user_fact_grounding_mode": USER_FACT_GROUNDING_MODE_DISABLED,
            "inference_depths": [1, 2, 3],
            "graph_nodes": [
                {
                    "node_id": "n_wish",
                    "material_id": "m_wish",
                    "phrase_unit_id": "pu_wish",
                    "evidence_span_id": "s_wish",
                    "role": "value_wish",
                    "relation_type": "coexistence",
                    "focus_rank": 1,
                    "must_keep": True,
                    "source_anchor_present": True,
                },
                {
                    "node_id": "n_block",
                    "material_id": "m_block",
                    "phrase_unit_id": "pu_block",
                    "evidence_span_id": "s_block",
                    "role": "fatigue_accumulation",
                    "relation_type": "pressure",
                    "focus_rank": 2,
                    "must_keep": True,
                    "source_anchor_present": True,
                },
            ],
        }
    )

    assert meta["observation_sentence_plan_roles_ready"] is True
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert meta["line_roles"] == ["opening", "core"]
    assert meta["public_line_role_enum_extended"] is False
    assert set(meta["sentence_plan_observation_roles"]).issuperset(
        {OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION}
    )
    assert meta["surface_role_merge_present"] is True
    opening = meta["sentence_plans"][0]["meta"]
    core = meta["sentence_plans"][1]["meta"]
    assert SURFACE_ROLE_MERGE_EMPATHY_INPUT_ARRANGEMENT in opening["surface_role_merge"]
    assert OBSERVATION_ROLE_EMPATHY in opening["observation_roles"]
    assert OBSERVATION_ROLE_INPUT_ARRANGEMENT in opening["observation_roles"]
    assert OBSERVATION_ROLE_STATE_VERBALIZATION in core["observation_roles"]
    assert core["inference_depth"] in {1, 2, 3}
    assert meta["comment_text_generated"] is False
    assert _contains_forbidden_raw_key(meta) is False
    assert_observation_sentence_plan_roles_contract(meta)


def test_step7_low_information_plan_requires_question_role_without_deep_relation() -> None:
    evidence_spans, phrase_units = _low_info_evidence_and_phrase_units()
    bundle = build_complete_material_bundle(
        evidence_spans=evidence_spans,
        phrase_units=phrase_units,
        current_input=_input("疲れた"),
        subscription_tier="free",
    )
    coverage_plan = build_complete_coverage_plan(material_bundle=bundle)
    graph = build_complete_relation_graph(coverage_plan=coverage_plan)
    meta = build_complete_sentence_plan_v2_meta(observation_graph=graph)

    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["known_scope_only"] is True
    assert meta["question_required"] is True
    assert meta["low_info_question_role_required"] is True
    assert meta["low_info_question_role_present"] is True
    assert set(meta["sentence_plan_observation_roles"]).issuperset(
        {OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION}
    )
    assert meta["low_info_deep_relation_allowed"] is False
    assert meta["low_info_eligible_promotion_allowed"] is False
    assert max(line["meta"].get("inference_depth") or 0 for line in meta["sentence_plans"]) <= 2
    assert all(line["line_role"] in {"opening", "core", "relation", "closing"} for line in meta["sentence_plans"])
    assert meta["public_line_role_enum_extended"] is False
    assert meta["comment_text_generated"] is False
    assert _contains_forbidden_raw_key(meta) is False
    assert_observation_sentence_plan_roles_contract(meta)


def test_step7_contract_rejects_raw_payload_public_line_role_extension_and_missing_low_info_question() -> None:
    evidence_spans, phrase_units = _low_info_evidence_and_phrase_units()
    bundle = build_complete_material_bundle(
        evidence_spans=evidence_spans,
        phrase_units=phrase_units,
        current_input=_input("疲れた"),
        subscription_tier="free",
    )
    meta = build_complete_sentence_plan_v2_meta(observation_graph=build_complete_relation_graph(coverage_plan=build_complete_coverage_plan(material_bundle=bundle)))

    invalid_raw = dict(meta)
    invalid_raw["raw_input"] = "疲れた"
    with pytest.raises(ValueError):
        assert_observation_sentence_plan_roles_contract(invalid_raw)

    invalid_line_role_extension = dict(meta)
    invalid_line_role_extension["public_line_role_enum_extended"] = True
    with pytest.raises(ValueError):
        assert_observation_sentence_plan_roles_contract(invalid_line_role_extension)

    invalid_low_info = dict(meta)
    invalid_low_info["low_info_question_role_present"] = False
    with pytest.raises(ValueError):
        assert_observation_sentence_plan_roles_contract(invalid_low_info)

    dumped = dump_observation_sentence_plan_roles(meta)
    assert "疲れた" not in dumped
    assert "commentText" not in dumped
    assert "public_comment_text" not in dumped
