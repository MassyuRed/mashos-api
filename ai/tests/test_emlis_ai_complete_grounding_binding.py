from __future__ import annotations

from copy import deepcopy
from typing import Any

from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from emlis_ai_complete_grounding_binding import (
    build_complete_binding_aware_grounding_contract_meta as build_complete_grounding_bridge_contract_meta,
    build_complete_grounding_binding_bundle,
    judge_complete_grounding_binding,
)
from emlis_ai_complete_grounding_service import (
    build_complete_grounding_contract_meta as build_complete_grounding_service_contract_meta,
    build_complete_grounding_report_meta,
    judge_complete_grounding,
)
from emlis_ai_grounding_judge import (
    _COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
    _COMPLETE_BINDING_AWARE_TARGET_STEP,
    _REJECTION_COMPLETE_BINDING_MISSING,
    _REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING,
    _REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING,
    _REJECTION_COMPLETE_OVER_ECHO,
    _REJECTION_COMPLETE_RELATION_NOT_EXPRESSED,
    build_complete_binding_aware_grounding_contract_meta,
    judge_grounding,
)
from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph


_FORBIDDEN_RAW_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo_text",
    "raw_user_text",
    "original_text",
    "source_text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _relationship_seed() -> dict[str, Any]:
    return {
        "coverage_group": "relationship",
        "sentence_budget": 3,
        "graph_nodes": [
            {
                "node_id": "n1",
                "material_id": "m1",
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "role": "wish_to_rely",
                "relation_type": "approach_avoidance",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n2",
                "material_id": "m2",
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s2",
                "role": "burden_fear",
                "relation_type": "approach_avoidance",
                "must_keep": True,
                "source_anchor_present": True,
            },
        ],
    }


def _span(span_id: str, text: str = "sanitized evidence handle") -> EvidenceSpan:
    return EvidenceSpan(
        span_id=span_id,
        raw_text=text,
        start_index=0,
        end_index=len(text),
        detected_type="complete_fixture",
        confidence=1.0,
        source_field="memo",
    )


def _evidence() -> list[EvidenceSpan]:
    # Deliberately does not surface-match the generated Japanese text. Step 8
    # should pass via Complete binding, not relaxed surface matching.
    return [_span("s1", "anchor alpha"), _span("s2", "anchor beta")]


def _graph() -> ObservationGraph:
    return ObservationGraph(
        primary_state=GraphClaim(
            claim_id="c1",
            claim_type="primary_state",
            text="complete candidate source-bound state",
            evidence_span_ids=["s1"],
            confidence=0.9,
        )
    )


def _realization_input() -> dict[str, Any]:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    assert realization.ready is True
    return realization.as_grounding_input()


def test_step8_contract_meta_is_additive_and_complete_binding_first() -> None:
    meta = build_complete_binding_aware_grounding_contract_meta()

    assert meta["version"] == _COMPLETE_BINDING_AWARE_GROUNDING_VERSION
    assert meta["target_step"] == _COMPLETE_BINDING_AWARE_TARGET_STEP
    assert meta["binding_aware_grounding_strengthened"] is True
    assert meta["accepts_complete_sentence_plan_v2"] is True
    assert meta["accepts_surface_realizer_grounding_input"] is True
    assert meta["requires_sentence_id"] is True
    assert meta["requires_used_evidence_span_ids"] is True
    assert meta["requires_used_phrase_unit_ids"] is True
    assert meta["requires_relation_type"] is True
    assert meta["unsupported_sentence_release_blocker"] is True
    assert meta["relation_not_expressed_repair_target"] is True
    assert meta["over_echo_repair_target"] is True
    assert meta["comment_text_key_written"] is False
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["response_shape_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["raw_input_included"] is False


def test_step8_bridge_service_builds_sanitized_binding_bundle() -> None:
    grounding_input = _realization_input()
    bundle = build_complete_grounding_binding_bundle(grounding_input=grounding_input)
    contract = build_complete_grounding_bridge_contract_meta()

    assert contract["target_step"] == _COMPLETE_BINDING_AWARE_TARGET_STEP
    assert contract["accepts_complete_surface_realizer_v2_grounding_input"] is True
    assert bundle["target_step"] == _COMPLETE_BINDING_AWARE_TARGET_STEP
    assert bundle["complete_binding_aware_grounding"] is True
    assert bundle["binding_count"] == len(grounding_input["surface_lines"])
    assert bundle["comment_text_key_written"] is False
    assert bundle["comment_text_contract"] == "passed_only"
    assert bundle["response_shape_changed"] is False
    assert bundle["raw_input_included"] is False
    assert _contains_forbidden_raw_key(bundle) is False


def test_step8_bridge_service_judges_complete_grounding_input() -> None:
    grounding_input = _realization_input()
    report = judge_complete_grounding_binding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=grounding_input,
    )

    assert report.passed is True
    assert report.binding_diagnostics["target_step"] == _COMPLETE_BINDING_AWARE_TARGET_STEP
    assert report.binding_diagnostics["complete_binding_aware_grounding"] is True


def test_step8_compat_grounding_service_keeps_stable_import_surface() -> None:
    grounding_input = _realization_input()
    contract = build_complete_grounding_service_contract_meta()
    report = judge_complete_grounding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=grounding_input,
    )
    report_meta = build_complete_grounding_report_meta(report)

    assert contract["target_step"] == _COMPLETE_BINDING_AWARE_TARGET_STEP
    assert contract["requires_sentence_id"] is True
    assert contract["requires_used_evidence_span_ids"] is True
    assert contract["requires_used_phrase_unit_ids"] is True
    assert contract["requires_relation_type"] is True
    assert report.passed is True
    assert report_meta["passed"] is True
    assert report_meta["binding_used"] is True
    assert report_meta["response_shape_changed"] is False
    assert report_meta["raw_input_included"] is False


def test_step8_complete_surface_grounding_input_passes_by_declared_sentence_binding() -> None:
    grounding_input = _realization_input()
    report = judge_grounding(
        comment_text=grounding_input["realized_text"],
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_scope="complete_initial_binding_scope",
        complete_grounding_input=grounding_input,
    )

    assert report.passed is True
    assert report.binding_present is True
    assert report.binding_used is True
    assert report.binding_count == len(grounding_input["surface_lines"])
    assert report.binding_supported_sentence_count == len(grounding_input["surface_lines"])
    assert report.binding_diagnostics["version"] == _COMPLETE_BINDING_AWARE_GROUNDING_VERSION
    assert report.binding_diagnostics["target_step"] == _COMPLETE_BINDING_AWARE_TARGET_STEP
    assert report.binding_diagnostics["complete_binding_aware_grounding"] is True
    assert report.binding_diagnostics["sentence_id_checked"] is True
    assert report.binding_diagnostics["evidence_span_ids_checked"] is True
    assert report.binding_diagnostics["phrase_unit_ids_checked"] is True
    assert report.binding_diagnostics["relation_type_checked"] is True
    assert report.binding_diagnostics["surface_threshold_relaxed"] is False
    assert report.binding_diagnostics["guard_threshold_relaxed"] is False
    assert report.binding_diagnostics["display_gate_relaxed"] is False
    assert report.binding_diagnostics["response_shape_changed"] is False
    assert report.binding_diagnostics["raw_input_included"] is False

    content_claims = [claim for claim in report.sentence_claims if claim.binding_sentence_id]
    assert len(content_claims) == len(grounding_input["surface_lines"])
    assert all(claim.binding_used for claim in content_claims)
    assert all(claim.binding_evidence_span_ids for claim in content_claims)
    assert all(claim.binding_phrase_unit_ids for claim in content_claims)
    assert all(claim.binding_relation_type == "approach_avoidance" for claim in content_claims)
    assert _contains_forbidden_raw_key(report.binding_diagnostics) is False


def test_step8_requires_phrase_unit_ids_even_when_evidence_binding_exists() -> None:
    grounding_input = deepcopy(_realization_input())
    grounding_input["surface_lines"][0]["used_phrase_unit_ids"] = []

    report = judge_grounding(
        comment_text=grounding_input["realized_text"],
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_scope="complete_initial_binding_scope",
        complete_grounding_input=grounding_input,
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert _REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING in report.rejection_reasons
    assert _REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING in report.binding_rejection_reasons
    assert report.binding_diagnostics["unsupported_sentence_is_release_blocker"] is True
    assert report.binding_diagnostics["surface_threshold_relaxed"] is False


def test_step8_requires_relation_type_and_marks_relation_not_expressed() -> None:
    grounding_input = deepcopy(_realization_input())
    grounding_input["surface_lines"][0]["relation_type"] = ""

    report = judge_grounding(
        comment_text=grounding_input["realized_text"],
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_scope="complete_initial_binding_scope",
        complete_grounding_input=grounding_input,
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert _REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING in report.rejection_reasons
    assert _REJECTION_COMPLETE_RELATION_NOT_EXPRESSED in report.rejection_reasons
    assert _REJECTION_COMPLETE_RELATION_NOT_EXPRESSED in report.binding_diagnostics["repair_targets"]
    assert report.binding_diagnostics["relation_not_expressed_is_repair_target"] is True


def test_step8_missing_complete_binding_rows_is_release_blocker() -> None:
    grounding_input = _realization_input()

    report = judge_grounding(
        comment_text=grounding_input["realized_text"],
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_scope="complete_initial_binding_scope",
        # no complete_grounding_input / no binding rows
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert _REJECTION_COMPLETE_BINDING_MISSING in report.rejection_reasons
    assert report.binding_missing is True
    assert report.binding_diagnostics["binding_missing"] is True


def test_step8_complete_over_echo_is_repair_target_not_gate_relaxation() -> None:
    grounding_input = deepcopy(_realization_input())
    first_surface = grounding_input["surface_lines"][0]["surface_text"]
    evidence = [_span("s1", first_surface), _span("s2", "anchor beta")]

    report = judge_grounding(
        comment_text=grounding_input["realized_text"],
        graph=_graph(),
        evidence_spans=evidence,
        grounding_scope="complete_initial_binding_scope",
        complete_grounding_input=grounding_input,
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert _REJECTION_COMPLETE_OVER_ECHO in report.rejection_reasons
    assert _REJECTION_COMPLETE_OVER_ECHO in report.binding_diagnostics["repair_targets"]
    assert report.binding_diagnostics["over_echo_is_repair_target"] is True
    assert report.binding_diagnostics["surface_threshold_relaxed"] is False


def test_step8_overclaim_still_rejects_even_when_binding_is_present() -> None:
    grounding_input = {
        "version": "emlis.complete_surface_realization.v2",
        "target_step": _COMPLETE_BINDING_AWARE_TARGET_STEP,
        "realized_text": "本当は誰かに頼りたい願いがあります。",
        "used_evidence_span_ids": ["s1"],
        "used_phrase_unit_ids": ["pu1"],
        "surface_lines": [
            {
                "sentence_id": "complete_s1",
                "surface_text": "本当は誰かに頼りたい願いがあります。",
                "line_role": "core",
                "relation_type": "approach_avoidance",
                "used_evidence_span_ids": ["s1"],
                "used_phrase_unit_ids": ["pu1"],
                "target_step": _COMPLETE_BINDING_AWARE_TARGET_STEP,
                "raw_input_included": False,
            }
        ],
        "raw_input_included": False,
    }

    report = judge_grounding(
        comment_text=grounding_input["realized_text"],
        graph=_graph(),
        evidence_spans=[_span("s1", "今日は会議と資料修正が続いた。")],
        grounding_scope="complete_initial_binding_scope",
        complete_grounding_input=grounding_input,
    )

    assert report.passed is False
    assert "unsupported_sentence" in report.rejection_reasons
    assert "unsupported_overclaim" in report.rejection_reasons
    assert report.binding_present is True
    assert report.binding_diagnostics["overclaim_reject_preferred"] is True
    assert report.binding_diagnostics["guard_threshold_relaxed"] is False


def test_step8_complete_grounding_bridge_wrapper_returns_binding_bundle() -> None:
    from emlis_ai_complete_grounding_binding import (
        build_complete_grounding_binding_bundle,
        judge_complete_binding_aware_grounding,
    )

    grounding_input = _realization_input()
    report = judge_complete_binding_aware_grounding(
        graph=_graph(),
        evidence_spans=_evidence(),
        grounding_input=grounding_input,
    )
    bundle = build_complete_grounding_binding_bundle(grounding_input=grounding_input)

    assert report.passed is True
    assert report.binding_diagnostics["complete_binding_aware_grounding"] is True
    assert bundle["version"] == _COMPLETE_BINDING_AWARE_GROUNDING_VERSION
    assert bundle["binding_present"] is True
    assert bundle["comment_text_key_written"] is False
    assert bundle["response_shape_changed"] is False
    assert bundle["raw_input_included"] is False
