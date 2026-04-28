from __future__ import annotations


def test_emlis_ai_capability_profiles_reserve_cross_core_fields():
    from emlis_ai_capability import resolve_emlis_ai_capability_for_tier

    free = resolve_emlis_ai_capability_for_tier("free")
    plus = resolve_emlis_ai_capability_for_tier("plus")
    premium = resolve_emlis_ai_capability_for_tier("premium")

    assert free.source_scope == "current_input_only"
    assert plus.source_scope == "current_input_with_owned_history"
    assert premium.source_scope == "current_input_with_owned_history"
    assert free.cross_core_enabled is False
    assert plus.cross_core_enabled is False
    assert premium.cross_core_enabled is False
    assert free.structure_model_enabled is False
    assert plus.structure_model_enabled is False
    assert premium.structure_model_enabled is False


def test_emlis_ai_quality_gate_blocks_free_history_usage_in_meta():
    from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
    from emlis_ai_quality_gate import evaluate_emlis_ai_quality_gate

    result = evaluate_emlis_ai_quality_gate(
        comment_text="今回は悲しみが近くにあって、その気持ちを置いておきたかったのですね。",
        capability=resolve_emlis_ai_capability_for_tier("free"),
        used_sources=["current_input", "history"],
        evidence_by_line={"receive": [{"kind": "emotion", "ref_id": "current"}]},
        fallback_used=False,
    )

    assert result.current_input_central is True
    assert result.history_allowed is False
    assert result.passed is False


def test_emlis_ai_quality_gate_passes_current_input_only_reply():
    from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
    from emlis_ai_quality_gate import evaluate_emlis_ai_quality_gate

    result = evaluate_emlis_ai_quality_gate(
        comment_text="今回は怒りが近くにあって、その気持ちを置いておきたかったのですね。",
        capability=resolve_emlis_ai_capability_for_tier("free"),
        used_sources=["current_input"],
        evidence_by_line={"receive": [{"kind": "emotion", "ref_id": "current"}]},
        fallback_used=False,
    )

    meta = result.as_meta()
    assert result.passed is True
    assert meta["schema_version"] == "emlis.quality.v1"
    assert meta["diagnosis_blocked"] is True
    assert meta["overclaim_suppressed"] is True


def test_emlis_ai_quality_gate_detects_diagnosis_like_overclaim():
    from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
    from emlis_ai_quality_gate import evaluate_emlis_ai_quality_gate

    result = evaluate_emlis_ai_quality_gate(
        comment_text="これはうつ病です。",
        capability=resolve_emlis_ai_capability_for_tier("premium"),
        used_sources=["current_input", "history"],
        evidence_by_line={"receive": [{"kind": "emotion", "ref_id": "current"}]},
        fallback_used=False,
    )

    assert result.overclaim_suppressed is False
    assert result.diagnosis_blocked is False
    assert result.passed is False
