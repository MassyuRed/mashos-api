from __future__ import annotations

import json
from typing import Any, Mapping

import pytest

from emlis_ai_observation_structure_connection_service import (
    assert_observation_structure_connection_contract,
    build_observation_structure_connection,
    observation_structure_connection_forward_composer_meta,
)
from emlis_ai_observation_structure_dictionary_loader import load_observation_structure_dictionary
from emlis_ai_observation_structure_material_service import (
    assert_observation_structure_material_contract,
    build_observation_structure_material,
    observation_structure_material_composer_payload,
    observation_structure_material_forward_meta,
    observation_structure_material_gate_report,
)
from fixtures.emlis_ai_observation_structure_phase5_cases import PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES

_PHASE6_ACTION_CONVERSION_CASE_IDS = {
    "phase5_unexpressed_output_stop_could_not_say",
    "phase5_self_shape_alignment_aligned_to_context",
    "phase5_action_conversion_history_gaman",
    "phase5_action_conversion_history_with_thought_action_gap",
    "phase5_conversion_history_closure_gaman_unfinished",
    "phase5_unformed_self_insight_wakaranai",
}

_FORBIDDEN_RAW_OR_PUBLIC_TEXT_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "memo",
    "memo_action",
    "memoText",
    "memoAction",
    "thought_text",
    "action_text",
    "comment_text",
    "commentText",
    "reply_text",
    "replyText",
    "surface_text",
    "surfaceText",
    "completed_reply_text",
    "completedReplyText",
}

_FORBIDDEN_DICTIONARY_TEXT_KEYS = {
    "definition",
    "evidence_requirements",
    "allowed_inference",
    "forbidden_inference",
    "surface_policy",
    "default_direction",
    "strong_hand_direction",
    "notes",
}

_PHASE6_FALSE_FLAGS = {
    "comment_text_generated",
    "dictionary_returns_completed_reply",
    "dictionary_returned_completed_reply",
    "completed_reply_from_dictionary",
    "display_gate_relaxed",
    "api_route_changed",
    "response_key_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "cause_inferred_from_category",
    "cause_inferred_from_emotion_strength",
    "personality_tendency_allowed",
}

_FORBIDDEN_SURFACE_OR_INFERENCE_FRAGMENTS = (
    "本当は何をしたかった",
    "本当は何を言いたかった",
    "相手のため",
    "優しさ",
    "自己犠牲",
    "我慢しがちな",
    "我慢できる人",
    "主体性がない",
    "迎合的",
    "相手が怖かった",
    "相手が悪い",
    "混乱",
    "迷走",
    "答えを急がせる",
)

_RELATION_FORBIDDEN_POLICY_EXPECTATIONS: Mapping[str, tuple[str, ...]] = {
    "unexpressed_output_stop": ("人格化", "本当は", "原因", "行動指示"),
    "self_shape_alignment": ("人格化", "支配", "評価", "本音"),
    "action_conversion_history": ("補完", "相手のため", "人格", "根拠なし"),
    "conversion_history_closure": ("一つ", "根拠なし", "評価", "AI側"),
    "unformed_self_insight": ("情報不足", "診断", "原因", "質問"),
}

_ENTRY_FORBIDDEN_POLICY_EXPECTATIONS: Mapping[str, tuple[str, ...]] = {
    "word_could_not_say": ("本音補完", "原因", "人格"),
    "word_aligned_to_context": ("人格", "評価", "相手原因"),
    "word_gaman": ("補完", "決め打ち", "人格", "閉じ方"),
    "word_wakaranai": ("情報不足", "診断", "原因"),
}


def _phase6_cases() -> tuple[Mapping[str, Any], ...]:
    return tuple(
        case
        for case in PHASE5_OBSERVATION_STRUCTURE_BLIND_QA_CASES
        if case["case_id"] in _PHASE6_ACTION_CONVERSION_CASE_IDS
    )


def _assert_no_forbidden_meta_keys(payload: Any) -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            assert key not in _FORBIDDEN_RAW_OR_PUBLIC_TEXT_KEYS
            assert key not in _FORBIDDEN_DICTIONARY_TEXT_KEYS
            _assert_no_forbidden_meta_keys(value)
        return
    if isinstance(payload, (list, tuple, set)):
        for item in payload:
            _assert_no_forbidden_meta_keys(item)


def _assert_phase6_false_flags_are_explicit(payload: Mapping[str, Any]) -> None:
    for flag in _PHASE6_FALSE_FLAGS:
        assert payload.get(flag) is False, flag


def _assert_current_input_text_not_forwarded(payload: Mapping[str, Any], current_input: Mapping[str, Any]) -> None:
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for source_key in ("memo", "memo_action"):
        raw_text = str(current_input.get(source_key) or "").strip()
        if raw_text:
            assert raw_text not in dumped


def _assert_forbidden_surface_or_inference_fragments_not_forwarded(payload: Mapping[str, Any]) -> None:
    dumped = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for fragment in _FORBIDDEN_SURFACE_OR_INFERENCE_FRAGMENTS:
        assert fragment not in dumped


def _joined(values: Any) -> str:
    if isinstance(values, str):
        return values
    return "\n".join(str(value) for value in values or ())


def test_phase6_dictionary_keeps_forbidden_inference_policies_for_new_observation_material() -> None:
    dictionary = load_observation_structure_dictionary()
    relations = {relation.relation_id: relation for relation in dictionary.relations}
    entries = {entry.entry_id: entry for entry in dictionary.entries}

    for relation_id, required_fragments in _RELATION_FORBIDDEN_POLICY_EXPECTATIONS.items():
        relation = relations[relation_id]
        assert relation.surface_policy.get("must_not_return_directly") is True
        forbidden_text = _joined(relation.forbidden_inference)
        for fragment in required_fragments:
            assert fragment in forbidden_text

    for entry_id, required_fragments in _ENTRY_FORBIDDEN_POLICY_EXPECTATIONS.items():
        entry = entries[entry_id]
        assert entry.surface_policy.get("must_not_return_directly") is True
        forbidden_text = _joined(entry.forbidden_inference)
        for fragment in required_fragments:
            assert fragment in forbidden_text


@pytest.mark.parametrize("case", _phase6_cases(), ids=lambda case: str(case["case_id"]))
def test_phase6_material_and_connection_meta_stay_meta_only_without_forbidden_inference_leak(
    case: Mapping[str, Any],
) -> None:
    current_input = case["current_input"]
    material = build_observation_structure_material(current_input=current_input)
    connection = build_observation_structure_connection(current_input=current_input)

    payloads: tuple[Mapping[str, Any], ...] = (
        material.as_meta(),
        observation_structure_material_forward_meta(material),
        observation_structure_material_composer_payload(material),
        observation_structure_material_gate_report(material),
        connection.as_meta(),
        observation_structure_connection_forward_composer_meta(connection),
    )

    for payload in payloads:
        _assert_no_forbidden_meta_keys(payload)
        _assert_phase6_false_flags_are_explicit(payload)
        _assert_current_input_text_not_forwarded(payload, current_input)
        _assert_forbidden_surface_or_inference_fragments_not_forwarded(payload)


def test_phase6_material_meta_keeps_dictionary_as_observation_material_only() -> None:
    for case in _phase6_cases():
        material_meta = build_observation_structure_material(current_input=case["current_input"]).as_meta()
        assert_observation_structure_material_contract(material_meta)

        assert material_meta["dictionary_is_observation_material_only"] is True
        assert material_meta["dictionary_returns_completed_reply"] is False
        assert material_meta["dictionary_returned_completed_reply"] is False
        assert material_meta["completed_reply_from_dictionary"] is False
        assert material_meta["comment_text_generated"] is False
        assert material_meta["display_gate_relaxed"] is False
        assert material_meta["api_route_changed"] is False
        assert material_meta["response_key_changed"] is False
        assert material_meta["db_physical_name_changed"] is False
        assert material_meta["rn_visible_contract_changed"] is False
        assert material_meta["cause_inferred_from_category"] is False
        assert material_meta["cause_inferred_from_emotion_strength"] is False
        assert material_meta["personality_tendency_allowed"] is False
        assert material_meta["gate_policy"]["category_is_topic_direction_not_cause"] is True
        assert material_meta["gate_policy"]["emotion_strength_must_not_create_cause"] is True
        assert material_meta["composer_policy"]["dictionary_must_not_return_completed_sentence"] is True


def test_phase6_connection_meta_keeps_public_contract_and_cause_personality_flags_closed() -> None:
    for case in _phase6_cases():
        connection = build_observation_structure_connection(current_input=case["current_input"])
        connection_meta = connection.as_meta()
        composer_meta = observation_structure_connection_forward_composer_meta(connection)
        assert_observation_structure_connection_contract(connection_meta)
        assert_observation_structure_connection_contract(composer_meta)

        assert connection_meta["dictionary_material_only"] is True
        assert connection_meta["dictionary_returns_completed_reply"] is False
        assert connection_meta["dictionary_returned_completed_reply"] is False
        assert connection_meta["completed_reply_from_dictionary"] is False
        assert connection_meta["comment_text_generated"] is False
        assert connection_meta["display_gate_relaxed"] is False
        assert connection_meta["api_route_changed"] is False
        assert connection_meta["response_key_changed"] is False
        assert connection_meta["api_response_key_change"] is False
        assert connection_meta["db_physical_name_changed"] is False
        assert connection_meta["rn_visible_contract_changed"] is False
        assert connection_meta["cause_inferred_from_category"] is False
        assert connection_meta["cause_inferred_from_emotion_strength"] is False
        assert connection_meta["personality_tendency_allowed"] is False
        assert composer_meta["dictionary_must_not_return_completed_sentence"] is True
        assert composer_meta["surface_realizer_owns_natural_language"] is True
        assert composer_meta["must_not_create_cause_without_evidence"] is True
        assert composer_meta["must_not_personality_diagnose"] is True
