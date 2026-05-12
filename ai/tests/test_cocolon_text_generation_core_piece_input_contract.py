from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from cocolon_text_generation_core.adapters.piece_composer_input_contract import (
    CHANNEL_ANSWER,
    CHANNEL_QUESTION,
    PIECE_INPUT_CONTRACT_MODEL,
    REJECTION_PIECE_SOURCE_MISSING,
    build_piece_composer_input_contract,
)
from cocolon_text_generation_core.policies import CORE_ID_PIECE


@dataclass(frozen=True)
class _PiecePlan:
    focus_key: str = "ideal_capacity_switch_gap"
    question: str = "整理したい気持ちと、量が多すぎる時の動きをどう扱いたい？"
    answer: str = "全部整理しようとする気持ちがありつつ、量が多すぎる時は目についたものから手をつける流れがあります。"
    selected_block_keys: Optional[List[str]] = None
    coverage_roles: Optional[List[str]] = None
    must_keep_block_keys: Optional[List[str]] = None
    must_keep_signal_keys: Optional[List[str]] = None
    source_claims: Optional[List[str]] = None
    answer_preservation_policy: str = "preserve_user_claims"
    overcompression_risk: bool = True
    minimum_detail_level: str = "source_scaled"
    reason: str = "value_observation_signal:ideal_capacity_switch_gap"

    def __post_init__(self):
        object.__setattr__(self, "selected_block_keys", ["ideal_capacity_switch_gap"] if self.selected_block_keys is None else self.selected_block_keys)
        object.__setattr__(self, "coverage_roles", ["ideal_capacity_switch_gap"] if self.coverage_roles is None else self.coverage_roles)
        object.__setattr__(self, "must_keep_block_keys", ["ideal_capacity_switch_gap"] if self.must_keep_block_keys is None else self.must_keep_block_keys)
        object.__setattr__(self, "must_keep_signal_keys", ["ideal_capacity_switch_gap"] if self.must_keep_signal_keys is None else self.must_keep_signal_keys)
        object.__setattr__(
            self,
            "source_claims",
            [
                "全部整理しようとする",
                "量が多すぎて嫌になる",
                "目についたものから手をつける",
            ] if self.source_claims is None else self.source_claims,
        )


def test_piece_input_contract_builds_separate_question_and_answer_payloads():
    contract = build_piece_composer_input_contract(_PiecePlan())

    assert contract.usable is True
    assert contract.adapter_name == "piece_composer_input_contract.v0"
    assert contract.question_payload is not contract.answer_payload
    assert contract.question_payload.core_id == CORE_ID_PIECE
    assert contract.answer_payload.core_id == CORE_ID_PIECE
    assert contract.question_payload.meta["piece_text_channel"] == CHANNEL_QUESTION
    assert contract.answer_payload.meta["piece_text_channel"] == CHANNEL_ANSWER
    assert contract.question_candidate.text != contract.answer_candidate.text
    assert contract.question_payload.valid_minimum is True
    assert contract.answer_payload.valid_minimum is True


def test_piece_input_contract_exposes_piece_preservation_fields_to_common_payloads():
    contract = build_piece_composer_input_contract(_PiecePlan())

    answer_payload = contract.answer_payload
    meta = contract.meta
    safety_policy = answer_payload.safety_policy

    assert meta["must_keep_signal_keys"] == ["ideal_capacity_switch_gap"]
    assert meta["source_claims"] == [
        "全部整理しようとする",
        "量が多すぎて嫌になる",
        "目についたものから手をつける",
    ]
    assert safety_policy["answer_preservation_policy"] == "preserve_user_claims"
    assert safety_policy["overcompression_risk"] is True
    assert safety_policy["minimum_detail_level"] == "source_scaled"
    assert answer_payload.must_keep_roles == ("ideal_capacity_switch_gap",)
    assert any(unit.role == "ideal_capacity_switch_gap" and unit.must_keep for unit in answer_payload.phrase_units)


def test_piece_input_contract_fails_closed_without_source_claims_or_source_texts():
    contract = build_piece_composer_input_contract(_PiecePlan(source_claims=[]), source_texts=[])

    assert contract.usable is False
    assert REJECTION_PIECE_SOURCE_MISSING in contract.rejection_reasons
    assert contract.question_payload.valid_minimum is False
    assert contract.answer_payload.valid_minimum is False
    assert contract.question_candidate.text == ""
    assert contract.answer_candidate.text == ""


def test_phase10_keeps_input_contract_compatibility_after_piece_composer_is_added():
    from cocolon_text_generation_core.adapters.piece_composer import PieceComposer, PIECE_COMPOSER_MODEL

    contract = build_piece_composer_input_contract(_PiecePlan())
    legacy = contract.meta["legacy_boundary_kept"]

    assert PieceComposer.composer_model == PIECE_COMPOSER_MODEL
    assert legacy["reflection"] == "compat_name_only_not_renamed"
    assert legacy["mymodel_qna"] == "compat_name_only_not_renamed"
    assert contract.question_payload.meta["preview_publish_contract_touched"] is False
    assert contract.answer_payload.meta["preview_publish_contract_touched"] is False
    assert contract.question_payload.composer_model == PIECE_INPUT_CONTRACT_MODEL
    assert contract.answer_payload.composer_model == PIECE_INPUT_CONTRACT_MODEL
