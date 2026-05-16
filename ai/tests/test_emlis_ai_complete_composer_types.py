from __future__ import annotations

from typing import Any, Mapping

from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_GENERATION_METHOD,
    COMPLETE_COMPOSER_GENERATION_SCOPE,
    COMPLETE_COMPOSER_MODEL,
    COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION,
    COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
    COMPLETE_COMPOSER_SOURCE_UNAVAILABLE,
    COMPLETE_COMPOSER_STATUS_GENERATED,
    COMPLETE_COMPOSER_STATUS_UNAVAILABLE,
    COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION,
    COMPLETE_TYPES_CONTRACT_VERSION,
    CompleteComposerCandidate,
    CompleteSentencePlanLine,
    CompleteSentencePlanV2,
    RepairTrace,
    build_complete_types_contract_meta,
)


def _contains_forbidden_raw_key(value: Any) -> bool:
    forbidden = {"raw_text", "input_text", "user_input", "current_input", "memo", "raw_user_text", "original_text"}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in forbidden:
                return True
            if _contains_forbidden_raw_key(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _plan() -> CompleteSentencePlanV2:
    return CompleteSentencePlanV2(
        plan_id="complete-plan-1",
        sentence_budget=2,
        coverage_group="conflict",
        sentence_plans=(
            CompleteSentencePlanLine(
                sentence_id="s-1",
                line_role="opening",
                relation_type="contrast",
                focus_rank=1,
                phrase_unit_ids=("pu-1", "pu-1"),
                evidence_span_ids=("ev-1",),
                must_include_roles=("state",),
                optional_roles=("closing",),
                forbidden_surface_keys=("diagnosis",),
                max_chars=90,
                surface_intent="receive_state",
                repair_policy=("keep_must_include", "trim_optional"),
                meta={"memo": "raw user text must be stripped", "safe_note": "kept"},
            ),
            CompleteSentencePlanLine(
                sentence_id="s-2",
                line_role="relation",
                relation_type="coexistence",
                focus_rank=2,
                phrase_unit_ids=("pu-2",),
                evidence_span_ids=("ev-2",),
                must_include_roles=("relation",),
                max_chars=100,
                surface_intent="show_relation",
                repair_policy=("relation_not_expressed",),
            ),
        ),
        meta={"current_input": "must be stripped", "coverage_reason": "kept"},
    )


def test_step2_contract_meta_is_type_only_and_preserves_public_boundaries() -> None:
    meta = build_complete_types_contract_meta()

    assert meta["version"] == COMPLETE_TYPES_CONTRACT_VERSION
    assert meta["stage"] == "complete_composer_initial"
    assert meta["target_composer_term"] == "完全Composer初期版"
    assert meta["composer_model"] == COMPLETE_COMPOSER_MODEL
    assert meta["type_only_step"] is True
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["db_physical_name_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["response_shape_changed"] is False
    assert meta["external_ai_allowed"] is False
    assert meta["local_llm_allowed"] is False
    assert meta["fixed_sentence_template_allowed"] is False
    assert meta["raw_input_required_for_improvement"] is False


def test_sentence_plan_line_requires_sentence_id_evidence_phrase_and_relation() -> None:
    line = CompleteSentencePlanLine(
        sentence_id="s-1",
        line_role="core",
        relation_type="pressure",
        phrase_unit_ids=("pu-1", "pu-1"),
        evidence_span_ids=("ev-1",),
        must_include_roles=("state", "state"),
        max_chars=999,
        meta={"raw_text": "must be stripped", "safe": True},
    )

    assert line.usable is True
    assert line.phrase_unit_ids == ("pu-1",)
    assert line.evidence_span_ids == ("ev-1",)
    assert line.must_include_roles == ("state",)
    assert line.max_chars == 240

    meta = line.as_meta()
    assert meta["sentence_id"] == "s-1"
    assert meta["line_role"] == "core"
    assert meta["relation_type"] == "pressure"
    assert meta["used_evidence_span_ids"] == ["ev-1"]
    assert meta["used_phrase_unit_ids"] == ["pu-1"]
    assert meta["raw_input_included"] is False
    assert meta["meta"] == {"safe": True}

    missing_relation = CompleteSentencePlanLine(
        sentence_id="s-2",
        line_role="core",
        relation_type="",
        phrase_unit_ids=("pu-2",),
        evidence_span_ids=("ev-2",),
    )
    assert missing_relation.usable is False
    assert "relation_type_missing" in missing_relation.validation_reasons


def test_sentence_plan_v2_exports_binding_first_meta_without_api_shape_change() -> None:
    plan = _plan()

    assert plan.schema_version == COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION
    assert plan.usable is True
    assert plan.sentence_budget == 2
    assert plan.used_evidence_span_ids == ("ev-1", "ev-2")
    assert plan.used_phrase_unit_ids == ("pu-1", "pu-2")
    assert plan.used_relation_ids == ("contrast", "coexistence")
    assert plan.relation_types == ("contrast", "coexistence")

    meta = plan.as_meta()
    assert meta["version"] == COMPLETE_SENTENCE_PLAN_SCHEMA_VERSION
    assert meta["sentence_budget"] == 2
    assert meta["coverage_group"] == "conflict"
    assert meta["used_relation_ids"] == ["contrast", "coexistence"]
    assert meta["api_response_shape_changed"] is False
    assert meta["raw_input_included"] is False
    assert _contains_forbidden_raw_key(meta) is False

    bundle = plan.as_sentence_binding_bundle_meta()
    assert bundle["binding_stage"] == "complete_sentence_plan_v2_added"
    assert bundle["sentence_binding_count"] == 2
    assert bundle["relation_types"] == ["contrast", "coexistence"]
    assert bundle["used_evidence_span_ids"] == ["ev-1", "ev-2"]
    assert bundle["used_phrase_unit_ids"] == ["pu-1", "pu-2"]
    assert bundle["response_shape_changed"] is False
    assert bundle["raw_input_included"] is False


def test_sentence_plan_v2_clamps_budget_and_marks_invalid_lines() -> None:
    plan = CompleteSentencePlanV2(
        plan_id="plan-invalid",
        sentence_budget=8,
        coverage_group="short_daily",
        sentence_plans=(
            {
                "sentence_id": "s-invalid",
                "line_role": "not-a-role",
                "relation_type": "",
                "phrase_unit_ids": [],
                "evidence_span_ids": [],
            },
        ),
    )

    assert plan.sentence_budget == 5
    assert plan.usable is False
    assert "line_0_relation_type_missing" in plan.validation_reasons
    assert "line_0_evidence_span_ids_missing" in plan.validation_reasons
    assert plan.as_sentence_binding_bundle_meta()["sentence_binding_count"] == 0


def test_repair_trace_records_only_safe_meaning_preserving_operations() -> None:
    trace = RepairTrace(
        attempt=1,
        source_gate="grounding",
        reason_code="relation_not_expressed",
        applied_operation="make_relation_line_explicit",
        before_plan_id="plan-before",
        after_plan_id="plan-after",
        evidence_ids_unchanged=True,
        relation_ids_unchanged=True,
        safety_level_unchanged=True,
        result="passed",
    )

    assert trace.safe_invariants_held is True
    meta = trace.as_meta()
    assert meta["source_gate"] == "grounding"
    assert meta["meaning_preserved"] is True
    assert meta["new_meaning_added"] is False
    assert meta["raw_input_included"] is False

    unsafe_trace = RepairTrace(
        attempt=1,
        source_gate="grounding",
        reason_code="unsupported_sentence",
        applied_operation="add_new_meaning",
        before_plan_id="plan-before",
        after_plan_id="plan-after",
        evidence_ids_unchanged=False,
        relation_ids_unchanged=True,
        safety_level_unchanged=True,
        result="passed",
    )
    assert unsafe_trace.safe_invariants_held is False
    assert unsafe_trace.as_meta()["new_meaning_added"] is True


def test_complete_candidate_generated_requires_ai_source_ids_and_sentence_binding() -> None:
    plan = _plan()
    candidate = CompleteComposerCandidate(
        status=COMPLETE_COMPOSER_STATUS_GENERATED,
        composer_source=COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
        coverage_scope="conflict",
        comment_text="気持ちが進みたい方と、止まりたい方の両方に分かれて見えます。",
        used_evidence_span_ids=plan.used_evidence_span_ids,
        used_phrase_unit_ids=plan.used_phrase_unit_ids,
        used_relation_ids=plan.used_relation_ids,
        sentence_binding_bundle=plan,
        repair_trace=(
            RepairTrace(
                attempt=1,
                source_gate="template",
                reason_code="same_ending",
                applied_operation="vary_sentence_ending",
                before_plan_id="complete-plan-1",
                after_plan_id="complete-plan-1-r1",
                evidence_ids_unchanged=True,
                relation_ids_unchanged=True,
                safety_level_unchanged=True,
                result="passed",
            ),
        ),
        composer_meta={"scorecard_event_deferred": True, "user_input": "must be stripped"},
    )

    assert candidate.schema_version == COMPLETE_COMPOSER_RESPONSE_SCHEMA_VERSION
    assert candidate.status == COMPLETE_COMPOSER_STATUS_GENERATED
    assert candidate.composer_source == COMPLETE_COMPOSER_SOURCE_AI_GENERATED
    assert candidate.composer_model == COMPLETE_COMPOSER_MODEL
    assert candidate.generation_method == COMPLETE_COMPOSER_GENERATION_METHOD
    assert candidate.generation_scope == COMPLETE_COMPOSER_GENERATION_SCOPE
    assert candidate.generated is True
    assert candidate.display_ready is True
    assert candidate.sentence_binding_count == 2

    meta = candidate.as_meta()
    assert "comment_text" not in meta
    assert meta["comment_text_present"] is True
    assert meta["used_evidence_span_ids"] == ["ev-1", "ev-2"]
    assert meta["used_phrase_unit_ids"] == ["pu-1", "pu-2"]
    assert meta["used_relation_ids"] == ["contrast", "coexistence"]
    assert meta["contract_boundary"]["response_shape_changed"] is False
    assert meta["contract_boundary"]["public_response_key_change"] is False
    assert meta["source_policy"]["external_ai_allowed"] is False
    assert meta["source_policy"]["fixed_fallback_allowed"] is False
    assert meta["raw_input_required_for_improvement"] is False
    assert _contains_forbidden_raw_key(meta) is False

    internal_payload = candidate.as_dict()
    assert internal_payload["comment_text"] == "気持ちが進みたい方と、止まりたい方の両方に分かれて見えます"


def test_complete_candidate_fail_closes_when_generated_candidate_lacks_binding_ids() -> None:
    candidate = CompleteComposerCandidate(
        status=COMPLETE_COMPOSER_STATUS_GENERATED,
        composer_source=COMPLETE_COMPOSER_SOURCE_AI_GENERATED,
        comment_text="根拠なしの候補です。",
        used_evidence_span_ids=(),
        used_phrase_unit_ids=(),
        used_relation_ids=(),
        sentence_binding_bundle={},
    )

    assert candidate.status == COMPLETE_COMPOSER_STATUS_UNAVAILABLE
    assert candidate.composer_source == COMPLETE_COMPOSER_SOURCE_UNAVAILABLE
    assert candidate.comment_text == ""
    assert candidate.used_evidence_span_ids == ()
    assert candidate.used_phrase_unit_ids == ()
    assert candidate.used_relation_ids == ()
    assert candidate.display_ready is False
    assert "used_evidence_span_ids_missing" in candidate.rejection_reasons
    assert "used_phrase_unit_ids_missing" in candidate.rejection_reasons
    assert "used_relation_ids_missing" in candidate.rejection_reasons
    assert "sentence_binding_bundle_missing" in candidate.rejection_reasons


def test_complete_candidate_blocks_external_ai_llm_and_fixed_fallback_sources() -> None:
    for forbidden_source in ("external_ai", "llm_generated", "fixed_fallback"):
        candidate = CompleteComposerCandidate(
            status=COMPLETE_COMPOSER_STATUS_GENERATED,
            composer_source=forbidden_source,
            comment_text="外部生成の候補です。",
            used_evidence_span_ids=("ev-1",),
            used_phrase_unit_ids=("pu-1",),
            used_relation_ids=("contrast",),
            sentence_binding_bundle={"sentence_binding_count": 1, "bindings": [{"sentence_id": "s-1"}]},
        )

        assert candidate.status == COMPLETE_COMPOSER_STATUS_UNAVAILABLE
        assert candidate.composer_source == COMPLETE_COMPOSER_SOURCE_UNAVAILABLE
        assert candidate.comment_text == ""
        assert f"forbidden_composer_source:{forbidden_source}" in candidate.rejection_reasons
        assert "composer_source_not_ai_generated" in candidate.rejection_reasons
        assert candidate.as_meta()["source_policy"]["external_ai_allowed"] is False


def test_complete_candidate_additive_meta_does_not_replace_existing_response_shape() -> None:
    candidate = CompleteComposerCandidate.unavailable("ap0_not_green", coverage_scope="internal_fixture")
    additive = candidate.as_emlis_ai_additive_meta()

    assert additive["complete_composer_internal_types"]["step"] == "Step2_Complete_internal_types"
    assert additive["response_shape_changed"] is False
    assert additive["raw_input_included"] is False
    assert additive["complete_initial"]["status"] == COMPLETE_COMPOSER_STATUS_UNAVAILABLE
    assert additive["complete_initial"]["comment_text_present"] is False
    assert "comment_text" not in additive["complete_initial"]
    assert additive["complete_initial"]["contract_boundary"]["comment_text_contract"] == "passed_only"
    assert additive["complete_initial"]["contract_boundary"]["public_response_key_change"] is False
