# -*- coding: utf-8 -*-
from __future__ import annotations

from cocolon_text_generation_core import CORE_ID_ANALYSIS, CoreTextComposer, STATUS_REJECTED
from cocolon_text_generation_core.result import REJECTION_CANDIDATE_TEXT_MISSING
from cocolon_text_generation_core.adapters.analysis_composer_input_contract import (
    ANALYSIS_DOMAIN_EMOTION,
    ANALYSIS_DOMAIN_SELF_STRUCTURE,
    ANALYSIS_INPUT_CONTRACT_META_KEY,
    REJECTION_ANALYSIS_CROSS_CORE_DISABLED,
    REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE,
    REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION,
    REJECTION_ANALYSIS_TEXT_SAFETY_REJECTED,
    TEXT_GENERATION_META_KEY,
    attach_analysis_input_contract_meta,
    build_analysis_composer_input_contract,
    split_analysis_materials_by_domain,
)


def test_analysis_input_contract_builds_emotion_payload_with_detached_observation_policy() -> None:
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_EMOTION,
        materials=[
            {
                "id": "emotion-1",
                "memo": "不安が続いた。眠る前に気持ちが揺れた。",
                "emotion_details": [{"type": "不安", "strength": "strong"}],
            }
        ],
        output_text="この期間は、不安が続いた記録が増えています。眠る前の揺れも観測されています。",
        target_period="2026-05-01/2026-05-07",
    )

    assert contract.usable is True
    assert contract.payload.core_id == CORE_ID_ANALYSIS
    assert contract.domain == ANALYSIS_DOMAIN_EMOTION
    assert contract.payload.tone_policy["voice_distance"] == "distant_observation_report"
    assert contract.payload.safety_policy["analysis_strict"] is True
    assert contract.payload.safety_policy["cross_core_enabled"] is False
    assert contract.payload.safety_policy["diagnosis_allowed"] is False
    assert contract.as_meta()["analysis_composer_connected"] is False
    assert contract.as_meta()["runtime_connected"] is False
    assert contract.as_meta()["domain_separated"] is True
    assert "Emlisです" in contract.payload.forbidden_surface_patterns


def test_analysis_input_contract_rejects_emotion_domain_self_structure_material() -> None:
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_EMOTION,
        materials=[
            {
                "id": "mixed-1",
                "memo": "不安があった。",
                "memo_action": "相手へ言い返したい動きがあった。",
            }
        ],
        output_text="この期間は、不安が観測されています。",
    )

    assert contract.usable is False
    assert REJECTION_ANALYSIS_EMOTION_CONTAINS_SELF_STRUCTURE in contract.rejection_reasons
    assert contract.candidate.text == ""
    assert contract.as_meta()["domain_separated"] is False


def test_analysis_input_contract_rejects_self_structure_domain_emotion_material() -> None:
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_SELF_STRUCTURE,
        materials=[
            {
                "id": "mixed-2",
                "text_primary": "相手との距離を取りたくなる。",
                "emotion_details": [{"type": "怒り"}],
            }
        ],
        output_text="この期間は、相手との距離を取りたくなる動きが観測されています。",
    )

    assert contract.usable is False
    assert REJECTION_ANALYSIS_SELF_CONTAINS_EMOTION in contract.rejection_reasons
    assert contract.candidate.text == ""
    assert contract.as_meta()["domain_separated"] is False


def test_analysis_input_contract_pre_rejects_diagnosis_and_overclaim_text() -> None:
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_SELF_STRUCTURE,
        materials=[
            {
                "id": "self-1",
                "text_primary": "人との距離を取りたくなる。",
                "role_hint": "対人距離",
                "target_hint": "関係性",
            }
        ],
        output_text="あなたは人との距離を避けているパターンです。心理学的にはトラウマの症状として説明できます。",
    )

    assert contract.usable is False
    assert any(reason.startswith(REJECTION_ANALYSIS_TEXT_SAFETY_REJECTED) for reason in contract.rejection_reasons)
    assert contract.candidate.pre_rejected is True
    assert contract.candidate.text == ""

    result = CoreTextComposer().generate(contract.payload, contract.candidate)
    assert result.status != STATUS_REJECTED
    assert REJECTION_CANDIDATE_TEXT_MISSING in result.rejection_reasons
    assert result.text == ""


def test_analysis_input_contract_rejects_cross_core_enabled_request() -> None:
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_EMOTION,
        materials=[{"id": "emotion-2", "memo": "緊張が続いた。", "emotion": "緊張"}],
        output_text="この期間は、緊張が続いた記録が観測されています。",
        cross_core_enabled=True,
    )

    assert contract.usable is False
    assert REJECTION_ANALYSIS_CROSS_CORE_DISABLED in contract.rejection_reasons
    assert contract.as_meta()["cross_core_enabled"] is False
    assert contract.meta["cross_core_enabled_requested"] is True


def test_analysis_input_contract_keeps_self_structure_independent_from_emlis_and_piece() -> None:
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_SELF_STRUCTURE,
        materials=[
            {
                "id": "self-2",
                "text_primary": "整理したい理想がある。",
                "text_secondary": "目の前の処理へ切り替わる。",
                "role_hint": "切り替え",
                "target_hint": "作業",
                "value_observation_signal_keys": ["ideal_capacity_switch_gap"],
            }
        ],
        output_text="この期間は、整理したい理想と目の前の処理へ切り替わる流れが観測されています。",
    )

    meta = contract.as_meta()
    assert contract.usable is True
    assert contract.domain == ANALYSIS_DOMAIN_SELF_STRUCTURE
    assert meta["emlis_piece_independent"] is True
    assert meta["analysis_composer_connected"] is False
    assert meta["cross_core_enabled"] is False
    assert contract.payload.tone_policy["emlis_observation_voice_allowed"] is False
    assert contract.payload.tone_policy["piece_public_qna_voice_allowed"] is False


def test_analysis_input_contract_adds_meta_without_touching_existing_report_payload_shape() -> None:
    content_json = {
        "metrics": {"totalAll": 3},
        "standardReport": {
            "contentText": "この期間は、不安が続いた記録が増えています。",
        },
    }
    contract = build_analysis_composer_input_contract(
        domain=ANALYSIS_DOMAIN_EMOTION,
        materials=[{"id": "emotion-3", "memo": "不安が続いた。", "emotion": "不安"}],
        content_json=content_json,
    )

    updated = attach_analysis_input_contract_meta(content_json, contract)

    assert "text_generation_core" not in content_json
    assert updated["metrics"] == content_json["metrics"]
    assert updated["standardReport"] == content_json["standardReport"]
    assert TEXT_GENERATION_META_KEY in updated
    assert ANALYSIS_INPUT_CONTRACT_META_KEY in updated[TEXT_GENERATION_META_KEY]
    meta = updated[TEXT_GENERATION_META_KEY][ANALYSIS_INPUT_CONTRACT_META_KEY]
    assert meta["content_json_shape_changed"] is False
    assert meta["standardReport_contract_untouched"] is True
    assert meta["contentText_contract_untouched"] is True


def test_split_analysis_materials_by_domain_separates_emotion_and_self_structure() -> None:
    buckets = split_analysis_materials_by_domain(
        [
            {"id": "emotion-4", "memo": "安心があった。", "emotion": "安心"},
            {"id": "self-3", "text_primary": "整理して進めたい。", "role_hint": "進行"},
        ]
    )

    assert len(buckets[ANALYSIS_DOMAIN_EMOTION]) == 1
    assert len(buckets[ANALYSIS_DOMAIN_SELF_STRUCTURE]) == 1
    assert buckets["unknown"] == ()
