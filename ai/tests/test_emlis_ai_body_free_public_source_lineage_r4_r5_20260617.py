# -*- coding: utf-8 -*-
from __future__ import annotations

"""R4/R5 body-free lineage record and RED-DC-001 root-source tests."""

import json
from typing import Any, Mapping, Sequence

from emlis_ai_body_free_public_source_lineage import (
    BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION,
    assert_body_free_public_source_lineage_record,
    build_body_free_public_source_lineage_record,
    sanitize_body_free_public_source_lineage_record,
)
from emlis_ai_gate_recovery_public_candidate_builder import build_public_candidate_after_gate_recovery
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, SafetyBoundaryReport


_FORBIDDEN_BODY_KEYS = {
    "raw_input",
    "memo",
    "memo_action",
    "emotion_details",
    "comment_text",
    "commentText",
    "candidate_comment_text",
    "public_comment_text",
    "surface_text",
    "surface_body",
    "candidate_body",
    "generated_text",
    "realized_text",
    "text",
    "body",
    "source_text",
    "input_text",
    "evidence_text",
    "reviewer_free_text",
    "traceback",
    "terminal_output",
}


class _MaterialRoute:
    material_quality = "eligible"

    def as_meta(self) -> dict[str, Any]:
        return {
            "material_quality": self.material_quality,
            "safety_triage_kind": "safe_observation",
            "raw_input_included": False,
            "comment_text_body_included": False,
        }


def _display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["visible_surface_acceptance_gate_failed"],
        trace_id="r4-r5-body-free-lineage",
    )


def _assert_no_body_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        assert not (set(value.keys()) & _FORBIDDEN_BODY_KEYS)
        for nested in value.values():
            _assert_no_body_keys(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            _assert_no_body_keys(nested)


def test_r4_body_free_lineage_record_sanitizer_strips_body_and_forces_closed_flags() -> None:
    unsafe = {
        "schema_version": "unsafe.schema.must.not.persist",
        "source_phase": "DisplayContractRedClassification_R4_R5_Test",
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        "root_candidate_source_kind": "ai_generated",
        "recovery_input_candidate_source_kind": "ai_generated",
        "selected_public_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        "pre_public_candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        "final_public_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        "recovery_context": RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        "recovery_pass_index": "2",
        "two_stage_required": True,
        "raw_input": "raw input must not leak",
        "comment_text": "public body must not leak",
        "candidate_body": "candidate body must not leak",
        "traceback": "traceback must not leak",
        "raw_input_included": True,
        "comment_text_body_included": True,
        "candidate_body_included": True,
        "display_gate_relaxed": True,
        "runtime_surface_gate_relaxed": True,
        "visible_surface_gate_relaxed": True,
        "grounding_gate_relaxed": True,
        "template_gate_relaxed": True,
        "safety_gate_relaxed": True,
    }

    record = sanitize_body_free_public_source_lineage_record(unsafe)

    assert record["schema_version"] == BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION
    assert record["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert record["root_candidate_source_kind"] == "ai_generated"
    assert record["pre_public_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    assert record["final_public_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert record["complete_initial_surface_recomposition_attempted"] is True
    assert record["complete_initial_surface_recomposition_final_used"] is False
    assert record["labelled_two_stage_surface_recomposition_final_used"] is True
    assert record["body_free"] is True
    assert record["raw_input_included"] is False
    assert record["comment_text_body_included"] is False
    assert record["candidate_body_included"] is False
    assert record["display_gate_relaxed"] is False
    assert record["runtime_surface_gate_relaxed"] is False
    assert record["visible_surface_gate_relaxed"] is False
    assert record["grounding_gate_relaxed"] is False
    assert record["template_gate_relaxed"] is False
    assert record["safety_gate_relaxed"] is False
    _assert_no_body_keys(record)
    assert_body_free_public_source_lineage_record(record)


def test_r4_builder_emits_only_body_free_identifiers_and_flags() -> None:
    record = build_body_free_public_source_lineage_record(
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        recovery_pass_index=2,
        root_candidate_source_kind="ai_generated",
        recovery_input_candidate_source_kind=CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        selected_public_candidate_source_kind=CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        pre_public_candidate_source_kind=CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        final_public_candidate_source_kind=CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        surface_requirement={"surface_requirement_family": "labelled_two_stage", "two_stage_required": True},
    )

    assert record["root_candidate_source_kind"] == "ai_generated"
    assert record["recovery_input_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert record["selected_public_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert record["final_public_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert record["two_stage_required"] is True
    _assert_no_body_keys(record)
    assert_body_free_public_source_lineage_record(record)


def test_r5_gate_recovery_preserves_original_root_when_final_candidate_meta_is_stale() -> None:
    original = ConversationComposerCandidate(
        comment_text="original body is rejected and must not be copied into lineage meta",
        composer_source="ai_generated",
        status="generated",
        composer_model="unsupported_original_composer.v1",
        generation_method="unsupported_original_generation",
        composer_meta={
            "candidate_source_kind": "ai_generated",
            "original_candidate_source_kind": "ai_generated",
            "root_candidate_source_kind": "ai_generated",
            "candidate_lineage": {"original_candidate_source": "ai_generated"},
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )
    labelled = ConversationComposerCandidate(
        comment_text="見えたこと：\n状態の線だけを返します。\n\nEmlisから：\n本文はpublic candidateの外へ複製しません。",
        composer_source="ai_generated",
        status="generated",
        composer_model="labelled_two_stage_surface_recomposition_v1",
        generation_method="labelled_two_stage_surface_recomposition",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            # This stale final-candidate alias used to overwrite RED-DC-001 root lineage.
            "original_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            "root_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            "candidate_lineage": {
                "root_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
                "original_candidate_source": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            },
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    result = build_public_candidate_after_gate_recovery(
        current_input={"memo": "raw input must not be serialized"},
        material_route=_MaterialRoute(),
        original_composer_candidate=original,
        original_display_decision=_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            ],
        },
        trace_id="r5-red-dc-001-root-preservation",
        recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        labelled_two_stage_surface_recomposition_candidate=labelled,
    )

    assert result.candidate is not None
    composer_meta = result.candidate.composer_meta
    lineage = composer_meta["candidate_lineage"]
    body_free_lineage = composer_meta["body_free_public_source_lineage"]
    assert composer_meta["original_candidate_source_kind"] == "ai_generated"
    assert composer_meta["root_candidate_source_kind"] == "ai_generated"
    assert lineage["original_candidate_source"] == "ai_generated"
    assert lineage["root_candidate_source_kind"] == "ai_generated"
    assert composer_meta["final_public_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert body_free_lineage["root_candidate_source_kind"] == "ai_generated"
    assert body_free_lineage["final_public_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    _assert_no_body_keys(composer_meta)
    assert_body_free_public_source_lineage_record(body_free_lineage)


def test_r4_public_meta_uses_sanitized_body_free_lineage_without_body_leak() -> None:
    internal_meta = {
        "observation_status": "passed",
        "body_free_public_source_lineage": {
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            "root_candidate_source_kind": "ai_generated",
            "recovery_input_candidate_source_kind": "ai_generated",
            "selected_public_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            "pre_public_candidate_source_kind": CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
            "final_public_candidate_source_kind": CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            "comment_text": "must not leak",
            "raw_input": "must not leak",
            "display_gate_relaxed": True,
            "raw_input_included": True,
        },
    }

    public_meta = build_public_emlis_input_feedback_meta(internal_meta, comment_text_present=True)

    lineage = public_meta["public_surface_lineage"]
    dumped = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    assert lineage["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert lineage["root_candidate_source_kind"] == "ai_generated"
    assert lineage["pre_public_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert lineage["final_public_candidate_source_kind"] == (
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    )
    assert lineage["display_gate_relaxed"] is False
    assert lineage["raw_input_included"] is False
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped
    _assert_no_body_keys(public_meta)
