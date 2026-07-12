from __future__ import annotations

import json

from emlis_ai_input_material_bundle import (
    EMLIS_INPUT_MATERIAL_BUNDLE_SCHEMA_VERSION,
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_LOW_INFORMATION,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    SEMANTIC_MATERIAL_SOURCE,
    SEMANTIC_RELATION_MATERIAL_GENERATION_DISABLED,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_EVENT,
    VISIBLE_SLOT_EMOTION_DIRECTION,
    VISIBLE_SLOT_EVENT,
    VISIBLE_SLOT_RELATIONSHIP,
    VISIBLE_SLOT_TARGET,
    VISIBLE_SLOT_UNRESOLVED_WEIGHT,
    assert_emlis_input_material_bundle_meta,
    build_emlis_input_material_bundle,
)
from emlis_ai_observation_eligibility_router import (
    EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY,
    assert_emlis_observation_eligibility_route_meta,
    response_kind_for_material_quality,
    route_emlis_observation_material_eligibility,
)
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY
from emlis_ai_reception_mode_resolver import resolve_emlis_reception_mode_meta
from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta


PHASE19_FORBIDDEN_IDS = (
    "self_understanding_learning_shift",
    "relationship_gratitude_recovery",
    "learning_shift_feature_family",
    "relationship_gratitude_feature_family",
)


def _encoded(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_phase20_3_short_fatigue_uses_bundle_low_information_not_a_case_route() -> None:
    current_input = {
        "id": "phase20-3-a",
        "memo": "疲れた",
        "memo_action": "",
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "category": ["生活"],
    }

    bundle = build_emlis_input_material_bundle(current_input)
    meta = bundle.as_meta()

    assert bundle.schema_version == EMLIS_INPUT_MATERIAL_BUNDLE_SCHEMA_VERSION
    assert bundle.material_quality == MATERIAL_QUALITY_LOW_INFORMATION
    assert VISIBLE_SLOT_EMOTION_DIRECTION in bundle.visible_material_slots
    assert VISIBLE_SLOT_TARGET in bundle.visible_material_slots
    assert VISIBLE_SLOT_UNRESOLVED_WEIGHT in bundle.visible_material_slots
    assert UNKNOWN_SLOT_EVENT in bundle.unknown_slots
    assert UNKNOWN_SLOT_CAUSE in bundle.unknown_slots
    assert meta["low_information_is_bundle_material_shortage"] is True
    assert meta["case_specific_route_used"] is False
    assert meta["phase19_case_route_used"] is False
    assert meta["phase19_runtime_cue_used"] is False
    assert "疲れた" not in _encoded(meta)
    assert "悲しみ" not in _encoded(meta)
    assert_emlis_input_material_bundle_meta(meta)


def test_phase20_3_long_ambiguous_relation_becomes_limited_grounding() -> None:
    current_input = {
        "memo": "ずっとこういう関係でしんどいけど、どうしたらいいのか分からない",
        "memo_action": "",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "category": ["人間関係"],
    }

    bundle = build_emlis_input_material_bundle(current_input)

    assert bundle.material_quality == MATERIAL_QUALITY_LIMITED_GROUNDING
    assert VISIBLE_SLOT_RELATIONSHIP in bundle.visible_material_slots
    assert VISIBLE_SLOT_EMOTION_DIRECTION in bundle.visible_material_slots
    assert UNKNOWN_SLOT_EVENT in bundle.unknown_slots
    assert UNKNOWN_SLOT_CAUSE in bundle.unknown_slots


def test_phase20_3_c_and_d_like_material_keeps_quality_but_delegates_semantics_to_canonical_plan() -> None:
    d_like_input = {
        "memo": "彼氏と別れたあと、友達が変わらず優しくしてくれて、感謝を別の形で返していきたい",
        "memo_action": "友達が私のために怒ってくれた",
        "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
        "category": ["恋愛", "人間関係"],
    }
    c_like_input = {
        "memo": "人について考えすぎていたけど、日常の中で疑問の対象が変わってきたのかもしれない",
        "memo_action": "授業で見たことをメモした",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "category": ["学習", "価値観"],
    }

    d_meta = build_emlis_input_material_bundle(d_like_input).as_meta()
    c_meta = build_emlis_input_material_bundle(c_like_input).as_meta()

    assert d_meta["material_quality"] == MATERIAL_QUALITY_ELIGIBLE
    assert c_meta["material_quality"] == MATERIAL_QUALITY_ELIGIBLE
    for meta in (d_meta, c_meta):
        assert meta["relation_material_ids"] == []
        assert meta["generic_relation_material_ids"] == []
        assert meta["semantic_material_source"] == SEMANTIC_MATERIAL_SOURCE
        assert meta["semantic_relation_material_generation_disabled"] is SEMANTIC_RELATION_MATERIAL_GENERATION_DISABLED
        assert meta["text_present_semantics_owned_by_canonical_plan"] is True
        assert meta["c_d_specific_runtime_cue_used"] is False
        for forbidden in PHASE19_FORBIDDEN_IDS:
            assert forbidden not in _encoded(meta)


def test_phase20_3_material_quality_maps_to_internal_response_kind_without_public_enum_change() -> None:
    assert response_kind_for_material_quality(MATERIAL_QUALITY_ELIGIBLE) == "normal_observation"
    assert response_kind_for_material_quality(MATERIAL_QUALITY_LOW_INFORMATION) == "low_information_observation"
    assert response_kind_for_material_quality(MATERIAL_QUALITY_LIMITED_GROUNDING) == "limited_grounding_observation"

    route = route_emlis_observation_material_eligibility(
        current_input={
            "memo": "疲れた",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["生活"],
        }
    )
    route_meta = route.as_meta()

    assert route_meta["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert route_meta["response_kind"] == "low_information_observation"
    assert route_meta["public_observation_status"] == "passed"
    assert route_meta["public_response_key_change"] is False
    assert route_meta["observation_status_enum_extended"] is False
    assert route_meta["a_low_information_case_route_used"] is False
    assert route_meta[EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY]["response_kind"] == "low_information_observation"
    assert_emlis_observation_eligibility_route_meta(route_meta)


def test_phase20_3_safety_material_does_not_convert_emergency_to_passed() -> None:
    route = route_emlis_observation_material_eligibility(
        current_input={
            "memo": "死にたい",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["生活"],
        }
    )
    meta = route.as_meta()

    assert meta["material_quality"] == MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
    assert meta["safety_triage_kind"] == "safety_blocked_emergency"
    assert meta["response_kind"] == "safety_blocked_emergency"
    assert meta["public_observation_status"] == "safety_blocked"
    assert meta["public_input_feedback_allowed"] is False


def test_phase20_3_existing_step2_router_carries_material_bundle_meta_without_text_leakage() -> None:
    decision = route_observation_eligibility(
        current_input={
            "memo": "疲れた",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["生活"],
        }
    )
    meta = decision.as_meta()

    assert meta["phase20_3_material_router_connected"] is True
    assert meta["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert meta["phase20_3_case_specific_route_used"] is False
    assert meta["phase20_3_c_d_specific_runtime_cue_used"] is False
    assert "疲れた" not in _encoded(meta["phase20_3_input_material_bundle"])
    assert "悲しみ" not in _encoded(meta["phase20_3_input_material_bundle"])


def test_phase20_3_router_attach_key_is_stable_for_reply_service_meta() -> None:
    route = route_emlis_observation_material_eligibility(
        current_input={
            "memo": "仕事で新しい役割を任されて不安だけど、少しずつ慣れたい",
            "memo_action": "職場で新しい仕事を任された",
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "category": ["仕事"],
        }
    )
    meta = route.as_meta()

    assert EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY == "phase20_3_observation_eligibility_router"
    assert meta["material_quality"] in {MATERIAL_QUALITY_ELIGIBLE, MATERIAL_QUALITY_LIMITED_GROUNDING}
    assert VISIBLE_SLOT_EVENT in meta["visible_material_slots"]
    assert meta["case_specific_route_used"] is False


def test_phase20_3_c_d_phase19_ids_are_not_active_shared_evidence_or_reception_modes() -> None:
    c_like_input = {
        "memo": "人について考えすぎていたけど、日常の中で疑問の対象が変わってきたのかもしれない",
        "memo_action": "授業で見たことをメモした",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "category": ["学習", "価値観"],
    }
    d_like_input = {
        "memo": "彼氏と別れたあと、友達が変わらず優しくしてくれて、感謝を別の形で返していきたい",
        "memo_action": "友達が私のために怒ってくれた",
        "emotion_details": [{"type": "悲しみ", "strength": "medium"}],
        "category": ["恋愛", "人間関係"],
    }

    for current_input in (c_like_input, d_like_input):
        shared_meta = build_emlis_shared_reception_evidence_meta(current_input)
        resolver_meta = resolve_emlis_reception_mode_meta(current_input)

        for forbidden in ("self_understanding_learning_shift", "relationship_gratitude_recovery"):
            assert forbidden not in shared_meta["explicit_reaction_cue_ids"]
            assert forbidden not in shared_meta["self_understanding_change_feature_ids"]
            assert forbidden not in shared_meta["relationship_boundary_support_feature_ids"]
            assert forbidden not in shared_meta["reception_candidate_mode_ids"]
            assert resolver_meta["reception_mode"] != forbidden
            assert forbidden not in resolver_meta["candidate_mode_ids"]
            assert forbidden not in resolver_meta["eligible_dictionary_mode_ids"]

        assert shared_meta["phase20_3_dedicated_c_d_cue_runtime_disabled"] is True
        assert shared_meta["phase20_3_dedicated_c_d_mode_runtime_disabled"] is True
        assert resolver_meta["phase20_3_dedicated_c_d_cue_runtime_disabled"] is True
        assert resolver_meta["phase20_3_dedicated_c_d_mode_runtime_disabled"] is True
        assert shared_meta["generic_relation_material_ids"]


def test_phase20_3_shared_evidence_and_resolver_do_not_select_cd_case_modes() -> None:
    from emlis_ai_reception_mode_resolver import resolve_emlis_reception_mode
    from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta

    c_input = {
        "memo": (
            "今までは、人に対して何故？と考えていたけど、疑問の対象が物になったことで、"
            "人について考えすぎる事が減った気がする。人との話し方を思い出してきてる。"
            "すぐに行動する勇気が出せるようになった。少しずつだけど進歩してる。大丈夫。"
        ),
        "memo_action": "日常に隠れている汚れや傷の意味を知り、外に出る度に色んな場所を見てメモした。",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "category": ["学習"],
    }
    d_input = {
        "memo": (
            "身の回りにある優しさを実感出来ていることが嬉しい。私のために怒ってくれる存在に感謝している。"
            "関係の終わりを区切りにして、別の形で返していきたい。"
        ),
        "memo_action": "彼氏と別れたが、友達が変わらず今も優しくしてくれている。そして私のために怒ってくれている。",
        "emotion_details": [{"type": "喜び", "strength": "medium"}],
        "category": ["恋愛", "人間関係", "価値観"],
    }

    for current_input in (c_input, d_input):
        shared_meta = build_emlis_shared_reception_evidence_meta(current_input)
        assert shared_meta["phase20_3_dedicated_c_d_cue_runtime_disabled"] is True
        assert shared_meta["phase20_3_dedicated_c_d_mode_runtime_disabled"] is True
        assert shared_meta["generic_relation_material_ids"]
        assert not (set(shared_meta["explicit_reaction_cue_ids"]) & set(PHASE19_FORBIDDEN_IDS))
        assert not (set(shared_meta["reception_candidate_mode_ids"]) & set(PHASE19_FORBIDDEN_IDS))

        resolution_meta = resolve_emlis_reception_mode(
            current_input,
            shared_evidence=shared_meta,
        ).as_meta()
        assert resolution_meta["phase20_3_dedicated_c_d_mode_runtime_disabled"] is True
        assert resolution_meta["phase20_3_dedicated_c_d_cue_runtime_disabled"] is True
        assert resolution_meta["reception_mode"] not in PHASE19_FORBIDDEN_IDS
        assert not (set(resolution_meta["candidate_mode_ids"]) & set(PHASE19_FORBIDDEN_IDS))
        assert not (set(resolution_meta["eligible_dictionary_mode_ids"]) & set(PHASE19_FORBIDDEN_IDS))
