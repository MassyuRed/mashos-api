from __future__ import annotations

import json

from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract

SECRET_MEMO = "これはpublic metaへ出してはいけない自己否定入力本文"
SECRET_ACTION = "これはpublic metaへ出してはいけない行動本文"
SECRET_COMMENT = "これはpublic metaへ出してはいけないcomment_text本文"
SECRET_EVIDENCE = "これはpublic metaへ出してはいけないraw evidence全文"
VISIBLE_COMMENT = "今の入力では、強い自己否定の言葉が出ている状態が見えます。"


def _input() -> dict[str, object]:
    return {
        "id": "phase8-public-meta-self-denial",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": SECRET_MEMO,
        "memo_action": SECRET_ACTION,
        "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
        "emotions": ["悲しみ"],
        "category": ["生活"],
        "is_secret": False,
    }


def _contract() -> dict[str, object]:
    return build_emlis_state_answer_surface_contract(_input()).as_meta()


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_phase8_public_meta_keeps_state_answer_boundary_summary_only_and_blocks_passed_status() -> None:
    contract = _contract()
    gate_report = build_state_answer_gate_boundary_report(
        visible_surface="あなたは素晴らしい人です。もう大丈夫です。",
        state_answer_surface_contract=contract,
    )
    internal_meta = {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "passed",
        "rejection_reasons": [],
        "state_answer_gate_boundary": gate_report,
        "state_answer_surface_contract": {**contract, "memo": SECRET_MEMO, "comment_text": SECRET_COMMENT},
        "raw_input": SECRET_MEMO,
        "raw_text": SECRET_EVIDENCE,
        "comment_text": SECRET_COMMENT,
        "diagnostic_summary": {
            "stage": "display",
            "primary_reason": "passed",
            "gate_results": {
                "state_answer": {"passed": False, "primary_reason": "state_answer_gate_boundary"}
            },
        },
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
    )
    dumped = _dump(public_meta)

    assert public_meta["observation_status"] == "rejected"
    assert "public_feedback_state_answer_gate_blocked" in public_meta["rejection_reasons"]
    assert public_meta["state_answer_gate_boundary"]["passed"] is False
    assert public_meta["state_answer_gate_boundary"]["blocked"] is True
    assert '"state_answer_surface_contract"' not in dumped
    assert '"memo"' not in dumped
    assert '"memo_action"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped
    assert '"raw_text"' not in dumped
    assert SECRET_MEMO not in dumped
    assert SECRET_ACTION not in dumped
    assert SECRET_COMMENT not in dumped
    assert SECRET_EVIDENCE not in dumped
    assert should_include_public_input_feedback(VISIBLE_COMMENT, public_meta) is False


def test_phase8_public_meta_allows_passed_state_answer_boundary_without_contract_body() -> None:
    contract = _contract()
    gate_report = build_state_answer_gate_boundary_report(
        visible_surface="Emlisには、その言葉だけであなた全体を決めてよいようには見えません。",
        state_answer_surface_contract=contract,
    )
    internal_meta = {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "passed",
        "state_answer_gate_boundary": gate_report,
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=True,
    )
    dumped = _dump(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["state_answer_gate_boundary"]["passed"] is True
    assert public_meta["state_answer_gate_boundary"]["public_meta_summary_only"] is True
    assert '"state_answer_surface_contract"' not in dumped
    assert SECRET_MEMO not in dumped
    assert should_include_public_input_feedback(VISIBLE_COMMENT, public_meta) is True
