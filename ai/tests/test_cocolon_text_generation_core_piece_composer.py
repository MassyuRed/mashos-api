from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cocolon_text_generation_core.adapters.piece_composer import (
    PIECE_COMPOSER_MODEL,
    PieceComposer,
    build_runtime_piece_plan,
    evaluate_piece_composer,
)


@dataclass(frozen=True)
class _PiecePlan:
    focus_key: str = "ideal_capacity_switch_gap"
    question: str = "整理したい気持ちと、量が多すぎる時の動きをどう扱いたい？"
    answer: str = "全部整理しようとする気持ちがありつつ、量が多すぎる時は目についたものから手をつける流れがあります。"
    selected_block_keys: Optional[List[str]] = None
    coverage_roles: Optional[List[str]] = None
    must_keep_signal_keys: Optional[List[str]] = None
    source_claims: Optional[List[str]] = None
    answer_preservation_policy: str = "preserve_user_claims"
    overcompression_risk: bool = True
    minimum_detail_level: str = "source_scaled"
    reason: str = "value_observation_signal:ideal_capacity_switch_gap"

    def __post_init__(self):
        object.__setattr__(self, "selected_block_keys", self.selected_block_keys or ["ideal_capacity_switch_gap"])
        object.__setattr__(self, "coverage_roles", self.coverage_roles or ["ideal_capacity_switch_gap"])
        object.__setattr__(self, "must_keep_signal_keys", self.must_keep_signal_keys or ["ideal_capacity_switch_gap"])
        object.__setattr__(
            self,
            "source_claims",
            self.source_claims
            if self.source_claims is not None
            else [
                "全部整理しようとする",
                "量が多すぎて嫌になる",
                "目についたものから手をつける",
            ],
        )


def test_piece_composer_passes_question_and_answer_through_common_core_guard():
    plan = _PiecePlan()
    evaluation = PieceComposer().compose(
        plan,
        question_text=plan.question,
        answer_text=plan.answer,
        source_texts=plan.source_claims,
        source_id="piece-preview-test",
    )
    meta = evaluation.as_meta()

    assert evaluation.passed is True
    assert evaluation.question_result.status == "generated"
    assert evaluation.answer_result.status == "generated"
    assert evaluation.answer_result.text
    assert meta["piece_composer_connected"] is True
    assert meta["preview_publish_no_regeneration"] is True
    assert meta["preview_publish_mutation_allowed"] is False
    assert meta["composer_model"] == PIECE_COMPOSER_MODEL
    assert meta["input_contract"]["legacy_boundary_names"] == ["reflection", "mymodel_qna"]


def test_piece_composer_rejects_emlis_voice_and_diagnosis_surface():
    plan = _PiecePlan()
    evaluation = evaluate_piece_composer(
        plan,
        question_text=plan.question,
        answer_text="Emlisです。あなたはこういう人です。",
        source_texts=plan.source_claims,
    )

    assert evaluation.passed is False
    assert evaluation.answer_result.status == "rejected"
    assert evaluation.answer_result.text == ""
    assert "piece_common_core_rejected:answer" in evaluation.rejection_reasons
    assert "forbidden_surface_pattern" in evaluation.rejection_reasons


def test_piece_composer_fails_closed_without_source_claims_or_source_texts():
    plan = build_runtime_piece_plan(
        focus_key="runtime_missing_source",
        question="問いを整える？",
        answer="答えを整える。",
        source_claims=[],
        must_keep_signal_keys=["missing_source"],
    )
    evaluation = evaluate_piece_composer(plan, question_text="問いを整える？", answer_text="答えを整える。", source_texts=[])

    assert evaluation.contract.usable is False
    assert evaluation.passed is False
    assert evaluation.question_result.status == "unavailable"
    assert evaluation.answer_result.status == "unavailable"
    assert evaluation.answer_result.text == ""
    assert "piece_source_claims_missing" in evaluation.rejection_reasons
