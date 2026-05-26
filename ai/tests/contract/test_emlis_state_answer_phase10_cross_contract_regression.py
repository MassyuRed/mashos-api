from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _pydantic_field_names(model: Any) -> set[str]:
    fields = getattr(model, "model_fields", None)
    if fields is None:  # pydantic v1 fallback
        fields = getattr(model, "__fields__", {})
    return set(fields.keys())


def _pydantic_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value.dict()


def _all_mapping_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_all_mapping_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_mapping_keys(child))
    return keys


def test_phase10_emotion_submit_response_contract_keeps_state_answer_material_internal_only() -> None:
    from api_emotion_submit import EmotionSubmitInputFeedback, EmotionSubmitRequest, EmotionSubmitResponse
    from emlis_ai_public_feedback_meta import (
        build_public_emlis_input_feedback_meta,
        should_include_public_input_feedback,
    )
    from emlis_ai_state_answer_composer_contract import build_state_answer_composer_role_plan
    from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
    from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract

    current_input = {
        "id": "phase10-cross-contract-self-denial",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": "自分はダメな人間だと思う。何度も考えて言葉にしているけどつらい。",
        "memo_action": "仕事のやり取りで失敗した気がして、夜まで考えていた。",
        "emotion_details": [{"type": "自己嫌悪", "strength": "strong"}],
        "emotions": ["自己嫌悪"],
        "category": ["仕事"],
    }
    visible_comment = (
        "今、そう感じていることは事実として重く置かれているように見えます。"
        "Emlisには、その言葉だけであなた全体を決めてよいようには見えません。"
        "ここまで言葉にして向き合おうとしていることまで、なかったことにはできないように見えます。"
    )

    state_answer_contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    role_plan = build_state_answer_composer_role_plan(state_answer_contract)
    gate_boundary = build_state_answer_gate_boundary_report(
        visible_surface=visible_comment,
        state_answer_surface_contract=state_answer_contract,
        current_input=current_input,
    )
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "tier": "free",
            "observation_status": "passed",
            "state_answer_surface_contract": state_answer_contract,
            "emlis_state_answer_surface_contract": state_answer_contract,
            "state_answer_composer_role_plan": role_plan,
            "environment_state_output_frame": state_answer_contract.get("environment_state_output_frame"),
            "state_answer_gate_boundary": gate_boundary,
            "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
            "visible_surface_acceptance_gate": {
                "evaluated": True,
                "passed": True,
                "classification": "pass",
                "action": "allow",
            },
            "memo": current_input["memo"],
            "memo_action": current_input["memo_action"],
            "raw_input": current_input["memo"],
            "raw_text": current_input["memo_action"],
            "comment_text": visible_comment,
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    assert state_answer_contract["state_answer_surface_contract_material_only"] is True
    assert state_answer_contract["public_response_key_added"] is False
    assert state_answer_contract["api_route_changed"] is False
    assert state_answer_contract["db_physical_name_changed"] is False
    assert state_answer_contract["rn_visible_contract_changed"] is False
    assert state_answer_contract["comment_text_body_included"] is False
    assert state_answer_contract["raw_input_included"] is False
    assert role_plan["section_role_order"] == ["state_answer_observation", "human_follow"]
    assert role_plan["sentence_plan_unit_roles"] == ["observation_section", "human_follow_section"]
    assert role_plan["public_response_key_added"] is False
    assert gate_boundary["passed"] is True
    assert gate_boundary["public_meta_summary_only"] is True
    assert public_meta["observation_status"] == "passed"
    assert public_meta["state_answer_gate_boundary"]["public_meta_summary_only"] is True

    assert _pydantic_field_names(EmotionSubmitRequest) == {
        "user_id",
        "emotions",
        "memo",
        "memo_action",
        "category",
        "created_at",
        "is_secret",
        "notify_friends",
    }
    assert _pydantic_field_names(EmotionSubmitInputFeedback) == {"comment_text", "emlis_ai"}
    assert _pydantic_field_names(EmotionSubmitResponse) == {"status", "id", "created_at", "input_feedback"}

    response = EmotionSubmitResponse(
        status="ok",
        id="phase10-emotion-id",
        created_at="2026-05-26T00:00:00+00:00",
        input_feedback=EmotionSubmitInputFeedback(
            comment_text=visible_comment,
            emlis_ai=public_meta,
        ),
    )
    response_dump = _pydantic_dump(response)
    public_keys = _all_mapping_keys(response_dump)
    dumped_response = _dump(response_dump)
    dumped_meta = _dump(public_meta)

    assert should_include_public_input_feedback(visible_comment, public_meta) is True
    assert set(response_dump) == {"status", "id", "created_at", "input_feedback"}
    assert {"comment_text", "emlis_ai"}.issubset(public_keys)
    assert "state_answer_gate_boundary" in public_keys  # small public summary only
    assert public_meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert public_meta["public_feedback_meta_boundary"]["comment_text_included"] is False

    forbidden_public_keys = {
        "environment_state_output_frame",
        "environment_state_output_surface",
        "state_answer_surface_contract",
        "emlis_state_answer_surface_contract",
        "state_answer_composer_role_plan",
        "state_answer_composer_payload",
        "human_follow_layer",
        "observation_layer",
        "ratio_policy",
        "special_handling",
        "metaphor_policy",
        "surface_policy",
        "memo",
        "memo_action",
        "raw_input",
        "raw_text",
        "comment_text_body",
    }
    assert forbidden_public_keys.isdisjoint(public_keys)
    assert '"environment_state_output_frame":' not in dumped_meta
    assert '"state_answer_surface_contract":' not in dumped_meta
    assert '"emlis_state_answer_surface_contract":' not in dumped_meta
    assert current_input["memo"] not in dumped_response
    assert current_input["memo_action"] not in dumped_response


def test_phase10_state_answer_gate_block_cannot_return_passed_comment_text_public_display() -> None:
    from emlis_ai_public_feedback_meta import (
        build_public_emlis_input_feedback_meta,
        should_include_public_input_feedback,
    )
    from emlis_ai_state_answer_gate_boundary import build_state_answer_gate_boundary_report
    from emlis_ai_state_answer_surface_contract import build_emlis_state_answer_surface_contract

    current_input = {
        "id": "phase10-anger-boundary",
        "created_at": "2026-05-26T00:00:00Z",
        "memo": "上司の扱いが理不尽で怒りが出た。軽く見られている気がする。",
        "memo_action": "会議で自分の発言を遮られた。",
        "emotion_details": [{"type": "怒り", "strength": "strong"}],
        "emotions": ["怒り"],
        "category": ["仕事"],
    }
    blocked_comment = "上司が悪いです。あなたの怒りは正しいです。そんな人とは距離を取った方がいいです。"
    contract = build_emlis_state_answer_surface_contract(current_input).as_meta()
    gate_boundary = build_state_answer_gate_boundary_report(
        visible_surface=blocked_comment,
        state_answer_surface_contract=contract,
        current_input=current_input,
    )
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            "state_answer_gate_boundary": gate_boundary,
            "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
            "visible_surface_acceptance_gate": {
                "evaluated": True,
                "passed": True,
                "classification": "pass",
                "action": "allow",
            },
            "comment_text": blocked_comment,
        },
        comment_text_present=True,
    )

    assert gate_boundary["passed"] is False
    assert gate_boundary["terminal_surface_block"] is True
    assert "anger_target_judgement_agreement" in gate_boundary["rejection_reasons"]
    assert gate_boundary["anger_target_judgement_agreement_blocked"] is True
    assert gate_boundary["public_response_key_change"] is False
    assert public_meta["observation_status"] == "rejected"
    assert "public_feedback_state_answer_gate_blocked" in public_meta["rejection_reasons"]
    assert should_include_public_input_feedback(blocked_comment, public_meta) is False
    assert blocked_comment not in _dump(public_meta)
    assert "comment_text" not in public_meta


def test_phase10_piece_and_analysis_do_not_import_or_accept_emlis_state_answer_temperature() -> None:
    from cocolon_text_generation_core.adapters.analysis_composer import evaluate_analysis_report_text_safety
    from cocolon_text_generation_core.adapters.piece_composer import (
        build_runtime_piece_plan,
        evaluate_piece_composer,
    )

    ai_root = Path(__file__).resolve().parents[2]
    adapter_dir = ai_root / "services" / "ai_inference" / "cocolon_text_generation_core" / "adapters"
    piece_source = (adapter_dir / "piece_composer.py").read_text(encoding="utf-8")
    analysis_source = (adapter_dir / "analysis_composer.py").read_text(encoding="utf-8")

    for source in (piece_source, analysis_source):
        assert "emlis_ai_state_answer_surface_contract" not in source
        assert "emlis_ai_state_answer_composer_contract" not in source
        assert "emlis_ai_human_follow_selector" not in source
        assert "emlis_ai_state_answer_ratio_policy" not in source
        assert "emlis_ai_state_answer_special_cases" not in source
        assert "emlis_ai_safe_daily_metaphor_material" not in source

    assert "emlis_observation_voice_allowed" in piece_source
    assert "no_emlis_voice_leakage" in piece_source
    assert "cross_core_enabled" in analysis_source
    assert "今回の入力では" in analysis_source
    assert "Emlisの観測" in piece_source
    assert "Emlisの観測" in analysis_source

    piece_plan = build_runtime_piece_plan(
        question="この問いは何か",
        answer="この答えは何か",
        source_texts=["この問いは、自分の迷いを少し外に置くためのものです。"],
    )
    piece_result = evaluate_piece_composer(
        piece_plan,
        question_text="この問いは何か。",
        answer_text="Emlisの観測です。",
        source_texts=["この問いは、自分の迷いを少し外に置くためのものです。"],
    )
    assert piece_result.answer_passed is False
    assert "forbidden_surface_pattern" in piece_result.as_meta()["results"]["answer"]["rejection_reasons"]

    analysis_result = evaluate_analysis_report_text_safety(
        "今回の入力では、Emlisには優しさとして感じられます。",
        domain="emotion_structure",
        material_fields=["summary", "emotion"],
        target_period="2026-05-18/2026-05-24",
    )
    assert analysis_result.passed is False
    assert "forbidden_surface_pattern" in analysis_result.rejection_reasons


def test_phase10_public_meta_rejects_state_answer_contract_body_or_raw_evidence_as_public_summary() -> None:
    from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta

    secret = "これはpublic metaへ出してはいけない状態回答contract本文です"
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "version": "emlis_ai_v3",
            "kernel_version": "multi_perspective_observation.v1",
            "observation_status": "passed",
            "state_answer_gate_boundary": {
                "evaluated": True,
                "passed": True,
                "blocked": False,
                "state_answer_contract_body_in_public_meta": True,
                "state_answer_raw_evidence_in_public_meta": True,
                "state_answer_comment_text_body_in_public_meta": True,
                "comment_text": secret,
                "raw_text": secret,
                "raw_input": secret,
            },
            "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
            "visible_surface_acceptance_gate": {
                "evaluated": True,
                "passed": True,
                "classification": "pass",
                "action": "allow",
            },
            "comment_text": secret,
        },
        comment_text_present=True,
    )

    dumped = _dump(public_meta)
    assert public_meta["observation_status"] == "rejected"
    assert public_meta["state_answer_gate_boundary"]["passed"] is False
    assert public_meta["state_answer_gate_boundary"]["blocked"] is True
    assert public_meta["state_answer_gate_boundary"]["public_meta_summary_only"] is True
    assert "state_answer_gate_boundary_public_meta_unsafe" in dumped
    assert secret not in dumped
    assert "comment_text" not in public_meta


def test_phase10_emlis_state_answer_public_route_contract_stays_additive_only() -> None:
    ai_root = Path(__file__).resolve().parents[2]
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
    assert "should_include_public_input_feedback" in source

    response_model_section = source[source.index("class EmotionSubmitInputFeedback"): source.index("async def _fetch_follow_viewer_ids")]
    for forbidden in (
        "environment_state_output_frame",
        "emlis_state_answer_surface_contract",
        "state_answer_surface_contract",
        "state_answer_composer_role_plan",
        "ratio_policy",
        "human_follow_layer",
        "special_handling",
        "metaphor_policy",
    ):
        assert forbidden not in response_model_section
