# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from cocolon_environment_state_output_frame import build_environment_state_output_frame
from cocolon_text_generation_core.adapters.analysis_composer import evaluate_analysis_report_text_safety
from cocolon_text_generation_core.adapters.analysis_environment_state_output_material import (
    build_analysis_environment_state_output_material,
)
from cocolon_text_generation_core.adapters.analysis_environment_state_output_surface import (
    build_analysis_environment_state_output_surface_material,
)
from cocolon_text_generation_core.adapters.piece_environment_state_output_guard import (
    build_piece_environment_state_output_guard,
)
from emlis_ai_public_feedback_meta import (
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_state_answer_composer_contract import build_state_answer_composer_role_plan
from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract


_CURRENT_INPUT = {
    "id": "phase10-current-001",
    "created_at": "2026-05-26T00:00:00Z",
    "memo": "この職場でやっていけるか不安だけど、相手に合わせようとして考え続けている",
    "memo_action": "新しい仕事を任され、返事の前に相手の反応を考えていた",
    "emotion_details": [{"type": "不安", "strength": "medium"}],
    "category": ["仕事"],
}

_PERIOD_RECORDS = [
    {
        "id": "phase10-period-001",
        "created_at": "2026-05-18T09:00:00Z",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "memo": "この職場でやっていけるか不安",
        "memo_action": "新しい仕事を任された",
    },
    {
        "id": "phase10-period-002",
        "created_at": "2026-05-19T10:00:00Z",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo": "ここにいていいか不安",
        "memo_action": "会議で役割が増えた",
    },
    {
        "id": "phase10-period-003",
        "created_at": "2026-05-20T11:00:00Z",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "weak"}],
        "memo": "このまま続けられるか分からない",
        "memo_action": "締切の調整をした",
    },
]

_PUBLIC_COMMENT = "Emlisです。今回の入力では、仕事という場面で不安が選ばれています。"


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _input_feedback_response(comment_text: str, public_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {"comment_text": comment_text, "emlis_ai": dict(public_meta or {})}
    return {
        "status": "ok",
        "id": "phase10-emotion-log",
        "created_at": "2026-05-26T00:00:00+00:00",
        "input_feedback": feedback,
    }


def _state_answer_contract() -> dict[str, Any]:
    return build_emlis_state_answer_surface_contract(_CURRENT_INPUT).as_meta()


def _public_meta_with_internal_materials(
    *,
    gate: Mapping[str, Any] | None = None,
    visible_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    frame = build_environment_state_output_frame(_CURRENT_INPUT, observation_structure_relation_ids=[])
    contract = _state_answer_contract()
    role_plan = build_state_answer_composer_role_plan(contract)
    internal_meta: dict[str, Any] = {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": "free",
        "observation_status": "passed",
        "observation_trace_id": "phase10-cross-contract",
        "trace_id": "phase10-cross-contract-trace",
        "observation_reply_kind": "eligible_observation",
        # These internal materials are intentionally supplied to prove that the
        # public meta boundary does not expose them as public response keys.
        "environment_state_output_frame": frame,
        "emlis_state_answer_surface_contract": contract,
        "state_answer_surface_contract": contract,
        "state_answer_composer_role_plan": role_plan,
        "memo": _CURRENT_INPUT["memo"],
        "memo_action": _CURRENT_INPUT["memo_action"],
        "raw_text": _CURRENT_INPUT["memo"],
        "comment_text": _PUBLIC_COMMENT,
        "runtime_surface_pre_return_gate": {
            "passed": True,
            "action": "allow",
            "rerender_attempted": False,
            "rejection_reasons": [],
            "state_answer_surface_contract": contract,
            "candidate_comment_text": _PUBLIC_COMMENT,
        },
        "visible_surface_acceptance_gate": visible_gate
        or {
            "evaluated": True,
            "passed": True,
            "classification": "pass",
            "action": "allow",
            "rejection_reasons": [],
            "state_answer_surface_contract": contract,
            "candidate_comment_text": _PUBLIC_COMMENT,
        },
    }
    if gate is not None:
        internal_meta["state_answer_gate_boundary"] = dict(gate)
    return build_public_emlis_input_feedback_meta(internal_meta, comment_text_present=True)


def test_phase10_emotion_submit_public_response_contract_remains_backward_compatible() -> None:
    ai_root = Path(__file__).resolve().parents[1]
    source = (ai_root / "services" / "ai_inference" / "api_emotion_submit.py").read_text(encoding="utf-8")

    assert '@app.post("/emotion/submit", response_model=EmotionSubmitResponse)' in source
    assert '"friend_emotion_feed"' in source
    assert "class EmotionSubmitInputFeedback" in source
    assert "comment_text: str" in source
    assert "emlis_ai: Optional[Dict[str, Any]]" in source
    assert "class EmotionSubmitResponse" in source
    assert "status: str" in source
    assert "id: Optional[Any]" in source
    assert "created_at: str" in source
    assert "input_feedback: Optional[EmotionSubmitInputFeedback]" in source
    assert "environment_state_output_frame:" not in source
    assert "emlis_state_answer_surface_contract:" not in source
    assert "state_answer_surface_contract:" not in source

    public_meta = _public_meta_with_internal_materials()
    response = _input_feedback_response(_PUBLIC_COMMENT, public_meta)

    assert set(response.keys()) == {"status", "id", "created_at", "input_feedback"}
    assert response["input_feedback"] is not None
    assert set(response["input_feedback"].keys()) == {"comment_text", "emlis_ai"}
    assert set(response["input_feedback"]["emlis_ai"].keys()).issuperset(
        {"schema_version", "version", "kernel_version", "tier", "observation_status", "public_feedback_meta_boundary"}
    )
    assert "state_answer" not in response
    assert "environment_state_output_frame" not in response


def test_phase10_internal_state_answer_materials_do_not_become_public_keys() -> None:
    public_meta = _public_meta_with_internal_materials()
    dumped = _json(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["public_feedback_meta_boundary"]["sanitized"] is True
    assert public_meta["public_feedback_meta_boundary"]["internal_meta_returned"] is False
    assert public_meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False
    assert '"environment_state_output_frame":' not in dumped
    assert '"emlis_state_answer_surface_contract":' not in dumped
    assert '"state_answer_surface_contract":' not in dumped
    assert '"state_answer_composer_role_plan":' not in dumped
    assert '"comment_text":' not in dumped
    assert _CURRENT_INPUT["memo"] not in dumped
    assert _CURRENT_INPUT["memo_action"] not in dumped
    assert should_include_public_input_feedback(_PUBLIC_COMMENT, public_meta) is True


def test_phase10_public_feedback_fails_closed_when_state_answer_boundary_marks_contract_leak() -> None:
    unsafe_gate = {
        "evaluated": True,
        "passed": True,
        "blocked": False,
        "terminal_surface_block": False,
        "public_response_key_added": True,
    }
    public_meta = _public_meta_with_internal_materials(gate=unsafe_gate)
    response = _input_feedback_response(_PUBLIC_COMMENT, public_meta)

    assert public_meta["observation_status"] == "rejected"
    assert "public_feedback_state_answer_gate_blocked" in public_meta.get("rejection_reasons", [])
    assert public_meta["state_answer_gate_boundary"]["passed"] is False
    assert public_meta["state_answer_gate_boundary"]["public_meta_summary_only"] is True
    assert should_include_public_input_feedback(_PUBLIC_COMMENT, public_meta) is False
    assert response["input_feedback"] is None


def test_phase10_visible_gate_contract_leak_does_not_unlock_passed_comment_text() -> None:
    visible_gate_with_contract_leak = {
        "evaluated": True,
        "passed": True,
        "classification": "pass",
        "action": "allow",
        "rejection_reasons": [],
        "public_response_key_change": True,
    }
    public_meta = _public_meta_with_internal_materials(visible_gate=visible_gate_with_contract_leak)
    response = _input_feedback_response(_PUBLIC_COMMENT, public_meta)

    assert public_meta["observation_status"] == "passed"
    assert public_meta["visible_surface_acceptance_gate"] == {
        "passed": False,
        "classification": "red",
        "action": "fail_closed",
        "rejection_reasons": ["visible_surface_acceptance_gate_public_meta_unsafe"],
    }
    assert should_include_public_input_feedback(_PUBLIC_COMMENT, public_meta) is False
    assert response["input_feedback"] is None


def test_phase10_emlis_temperature_does_not_leak_into_piece_or_analysis_contracts() -> None:
    frame = build_environment_state_output_frame(_CURRENT_INPUT, observation_structure_relation_ids=[])
    contract = _state_answer_contract()
    piece_guard = build_piece_environment_state_output_guard(frame)
    piece_dump = _json(piece_guard)

    assert piece_guard["connected"] is True
    assert "emlis_voice" in piece_guard["forbidden_surface_claims"]
    assert "analysis_period_tendency" in piece_guard["forbidden_surface_claims"]
    assert '"human_follow_layer":' not in piece_dump
    assert '"emlis_state_answer_surface_contract":' not in piece_dump
    assert '"state_answer_surface_contract":' not in piece_dump
    assert "emlis_impression_not_fact" not in piece_dump
    assert contract["human_follow_layer"]["follow_mode"] == "emlis_impression_not_fact"

    for forbidden_analysis_text in (
        "Emlisです。今回の入力では、Emlisには優しさとして感じられます。",
        "Emlisには、その言葉だけであなた全体を決めてよいようには見えません。",
        "Emlisの感想として、ここまで考えていたことが見えます。",
    ):
        analysis_result = evaluate_analysis_report_text_safety(
            forbidden_analysis_text,
            domain="emotion_structure",
            material_fields=["summary", "category", "emotion"],
            target_period="2026-05-18/2026-05-24",
        )
        assert analysis_result.passed is False, forbidden_analysis_text

    analysis_material = build_analysis_environment_state_output_material(
        _PERIOD_RECORDS,
        period_kind="weekly",
        period_label="2026-05-18/2026-05-24",
        start_at="2026-05-18T00:00:00Z",
        end_at="2026-05-24T23:59:59Z",
    )
    analysis_surface = build_analysis_environment_state_output_surface_material(analysis_material)
    analysis_dump = _json(analysis_surface)
    assert analysis_surface["content_text"].startswith("この期間の記録では")
    assert "Emlis" not in analysis_surface["content_text"]
    assert "今回の入力では" not in analysis_surface["content_text"]
    assert '"human_follow_layer":' not in analysis_dump
    assert '"emlis_state_answer_surface_contract":' not in analysis_dump
    assert '"state_answer_surface_contract":' not in analysis_dump


def test_phase10_state_answer_gate_summary_is_small_and_does_not_return_contract_body() -> None:
    contract = _state_answer_contract()
    gate = build_state_answer_gate_boundary_report(
        visible_surface="Emlisには、相手に合わせようとして考え続けていた流れが見えます。",
        state_answer_surface_contract=contract,
        current_input=_CURRENT_INPUT,
    )
    public_meta = _public_meta_with_internal_materials(gate=gate)
    summary = public_meta["state_answer_gate_boundary"]
    dumped = _json(public_meta)

    assert public_meta["observation_status"] == "passed"
    assert summary["passed"] is True
    assert summary["public_meta_summary_only"] is True
    assert "schema_version" not in summary
    assert "material_id" not in summary
    assert '"state_answer_surface_contract":' not in dumped
    assert '"emlis_state_answer_surface_contract":' not in dumped
    assert '"observation_layer":' not in dumped
    assert '"human_follow_layer":' not in dumped
    assert '"comment_text":' not in dumped
    assert _CURRENT_INPUT["memo"] not in dumped
    assert should_include_public_input_feedback(_PUBLIC_COMMENT, public_meta) is True
