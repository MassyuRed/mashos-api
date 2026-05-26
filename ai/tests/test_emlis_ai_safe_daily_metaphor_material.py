from __future__ import annotations

import json

from emlis_ai_safe_daily_metaphor_material import (
    EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID,
    EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE,
    EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION,
    build_emlis_ai_safe_daily_metaphor_material,
    safe_daily_metaphor_material_composer_payload,
    safe_daily_metaphor_material_forward_meta,
    safe_daily_metaphor_material_gate_report,
)
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract


def _input(
    *,
    memo: str,
    emotion: str = "不安",
    strength: str = "medium",
    action: str = "その場で考えていた",
    category: str = "生活",
) -> dict[str, object]:
    return {
        "id": f"safe-daily-metaphor-{emotion}-{strength}",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": memo,
        "memo_action": action,
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "category": [category],
        "is_secret": False,
    }


def test_phase6_safe_daily_metaphor_selects_family_only_for_structure_question_without_text_leak() -> None:
    current_input = _input(memo="なぜ確認していないのに相手の答えを自分で決めてしまうのかわからない")

    meta = build_emlis_ai_safe_daily_metaphor_material(current_input).as_meta()
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert meta["schema_version"] == EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION
    assert meta["material_id"] == EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID
    assert meta["source_phase"] == EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE
    assert meta["safe_daily_metaphor_material_connected"] is True
    assert meta["mode"] == "safe_daily_analogy"
    assert meta["selected_analogy_family"] == "unchecked_answer_sheet"
    assert meta["safe_daily_analogy_id"] == "safe_daily_analogy.unchecked_answer_sheet.v1"
    assert meta["selection"]["trigger_policy"]["allowed_trigger_detected"] is True
    assert meta["selection"]["corresponding_structure_id_detected"] is True
    assert meta["free_metaphor_generation_allowed"] is False
    assert meta["completed_metaphor_sentence_generated"] is False
    assert meta["fixed_metaphor_template_used"] is False
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert '"comment_text":' not in encoded
    assert '"raw_text":' not in encoded
    assert '"metaphor_sentence":' not in encoded


def test_phase6_safe_daily_metaphor_stays_none_without_structure_understanding_trigger() -> None:
    current_input = _input(
        memo="この職場でやっていけるか不安",
        action="新しい仕事を任された",
        category="仕事",
    )

    meta = build_emlis_ai_safe_daily_metaphor_material(current_input).as_meta()

    assert meta["mode"] == "none"
    assert meta["selected_analogy_family"] is None
    assert meta["safe_daily_analogy_id"] is None
    assert meta["selection"]["selection_reason"] == "not_structure_understanding_request"
    assert meta["selection"]["trigger_policy"]["allowed_trigger_detected"] is False


def test_phase6_safe_daily_metaphor_suppresses_strong_self_denial_grief_and_anger() -> None:
    self_denial = build_emlis_ai_safe_daily_metaphor_material(
        _input(
            memo="なぜ自分はダメな人間だと思ってしまうのか知りたい",
            emotion="悲しみ",
            strength="strong",
            action="ミスを思い出していた",
            category="仕事",
        )
    ).as_meta()
    grief = build_emlis_ai_safe_daily_metaphor_material(
        _input(
            memo="なぜこんなに悲しいのか整理したい",
            emotion="悲しみ",
            strength="strong",
            action="一人で言葉にしていた",
            category="人間関係",
        )
    ).as_meta()
    anger = build_emlis_ai_safe_daily_metaphor_material(
        _input(
            memo="上司の扱いが理不尽で怒りが出る。なぜ同じことになるのか知りたい",
            emotion="怒り",
            strength="medium",
            action="急な対応を求められた",
            category="仕事",
        )
    ).as_meta()
    panic_like = build_emlis_ai_safe_daily_metaphor_material(
        _input(
            memo="なぜ息ができないくらい怖くなるのか整理したい",
            emotion="不安",
            strength="strong",
            action="その場で固まっていた",
            category="生活",
        )
    ).as_meta()
    specialist = build_emlis_ai_safe_daily_metaphor_material(
        _input(
            memo="なぜ法律的に訴訟した方がいいのか分からない",
            emotion="不安",
            strength="medium",
            action="調べながら考えていた",
            category="法律",
        )
    ).as_meta()

    assert self_denial["mode"] == "none"
    assert "strong_self_denial_suppresses_metaphor" in self_denial["selection"]["suppression"]["suppression_reason_ids"]
    assert self_denial["selection"]["suppression"]["strong_self_denial_suppressed"] is True

    assert grief["mode"] == "none"
    assert "strong_grief_or_loneliness_suppresses_metaphor" in grief["selection"]["suppression"]["suppression_reason_ids"]
    assert grief["selection"]["suppression"]["strong_grief_or_loneliness_suppressed"] is True

    assert anger["mode"] == "none"
    assert "anger_suppresses_metaphor" in anger["selection"]["suppression"]["suppression_reason_ids"]
    assert anger["selection"]["suppression"]["anger_suppressed"] is True

    assert panic_like["mode"] == "none"
    assert "panic_like_input_suppresses_metaphor" in panic_like["selection"]["suppression"]["suppression_reason_ids"]
    assert panic_like["selection"]["suppression"]["panic_like_input_suppressed"] is True

    assert specialist["mode"] == "none"
    assert "specialist_context_suppresses_metaphor" in specialist["selection"]["suppression"]["suppression_reason_ids"]
    assert specialist["selection"]["suppression"]["specialist_context_suppressed"] is True


def test_phase6_safe_daily_metaphor_candidates_are_daily_state_explanation_only() -> None:
    meta = build_emlis_ai_safe_daily_metaphor_material(
        _input(memo="なぜこのままでいいのか、どうしたらいいかわからない")
    ).as_meta()
    candidates = meta["selection"]["candidate_analogy_families"]

    assert candidates
    assert all(candidate["safe_daily_domain_only"] is True for candidate in candidates)
    assert all(candidate["surface_role"] == "state_explanation_only" for candidate in candidates)
    assert all(candidate["candidate_is_completed_sentence_template"] is False for candidate in candidates)
    assert all(candidate["runtime_fixed_sentence_allowed"] is False for candidate in candidates)
    forbidden_domains = {"medical", "psychological_diagnosis", "legal", "religious", "political", "professional_advice", "attack_or_weapon", "target_attack"}
    assert not {candidate["domain_kind"] for candidate in candidates} & forbidden_domains
    assert meta["gate_policy"]["action_instruction_allowed"] is False
    assert meta["gate_policy"]["medical_domain_analogy_allowed"] is False
    assert meta["gate_policy"]["legal_domain_analogy_allowed"] is False
    assert meta["gate_policy"]["religious_domain_analogy_allowed"] is False
    assert meta["gate_policy"]["aggressive_surface_allowed"] is False


def test_phase6_helpers_return_forward_gate_and_composer_payloads() -> None:
    material = build_emlis_ai_safe_daily_metaphor_material(
        _input(memo="なぜ同じ不安に何度も戻るのかわからない")
    )

    forward_meta = safe_daily_metaphor_material_forward_meta(material)
    gate_report = safe_daily_metaphor_material_gate_report(forward_meta)
    composer_payload = safe_daily_metaphor_material_composer_payload(forward_meta)

    assert forward_meta["material_id"] == EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID
    assert gate_report["safe_daily_metaphor_material_connected"] is True
    assert gate_report["mode"] == "safe_daily_analogy"
    assert gate_report["free_metaphor_generation_allowed"] is False
    assert gate_report["completed_metaphor_sentence_generated"] is False
    assert gate_report["action_instruction_allowed"] is False
    assert composer_payload["safe_daily_metaphor_material_connected"] is True
    assert composer_payload["safe_daily_metaphor_material_only"] is True
    assert composer_payload["comment_text_generated"] is False
    assert composer_payload["raw_text_included"] is False


def test_phase6_safe_daily_metaphor_is_connected_into_state_answer_surface_contract() -> None:
    structure_contract = build_emlis_state_answer_surface_contract(
        _input(memo="なぜ同じ不安に何度も戻るのかわからない")
    ).as_meta()
    standard_contract = build_emlis_state_answer_surface_contract(
        _input(memo="この職場でやっていけるか不安", action="新しい仕事を任された", category="仕事")
    ).as_meta()
    anger_contract = build_emlis_state_answer_surface_contract(
        _input(
            memo="上司の扱いが理不尽で怒りが出る。なぜ同じことになるのか知りたい",
            emotion="怒り",
            category="仕事",
        )
    ).as_meta()

    structure_metaphor = structure_contract["metaphor_policy"]
    standard_metaphor = standard_contract["metaphor_policy"]
    anger_metaphor = anger_contract["metaphor_policy"]

    assert structure_metaphor["safe_daily_metaphor_material_connected"] is True
    assert structure_metaphor["material_id"] == EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID
    assert structure_metaphor["mode"] == "safe_daily_analogy"
    assert structure_metaphor["selected_analogy_family"] == "same_step_on_same_path"
    assert structure_metaphor["free_metaphor_generation_allowed"] is False
    assert structure_metaphor["completed_metaphor_sentence_generated"] is False
    assert structure_metaphor["safe_daily_metaphor_material_payload"]["comment_text_generated"] is False

    assert standard_metaphor["mode"] == "none"
    assert standard_metaphor["selected_analogy_family"] is None

    assert anger_metaphor["mode"] == "none"
    assert "anger_suppresses_metaphor" in anger_metaphor["selection"]["suppression"]["suppression_reason_ids"]
    assert anger_contract["public_response_key_added"] is False
    assert anger_contract["response_key_changed"] is False
    assert anger_contract["db_physical_name_changed"] is False
    assert anger_contract["rn_visible_contract_changed"] is False
