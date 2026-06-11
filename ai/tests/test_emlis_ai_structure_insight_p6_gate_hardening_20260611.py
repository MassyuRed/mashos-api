# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
from emlis_ai_structure_insight_p6_gate_hardening import (
    GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE,
    GATE_DECISION_BLOCK_SURFACE_CANDIDATE,
    GATE_DECISION_REVIEW_REQUIRED,
    REASON_ADVICE_SURFACE,
    REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE,
    REASON_COMMENT_TEXT_BODY_IN_META_DETECTED,
    REASON_DIAGNOSIS_SURFACE,
    REASON_FUTURE_PREDICTION_SURFACE,
    REASON_PERSONALITY_CLAIM_SURFACE,
    REASON_PUBLIC_CONTRACT_MUTATION_DETECTED,
    REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE,
    REASON_SOFT_EXPRESSION_MISSING,
    REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE,
    REASON_TARGET_INTENT_ASSERTION_SURFACE,
    STRUCTURE_INSIGHT_P6_GATE_HARDENING_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_GATE_HARDENING_STEP,
    STRUCTURE_INSIGHT_P6_GATE_HARDENING_SUMMARY_SCHEMA_VERSION,
    assert_structure_insight_p6_gate_hardening_contract,
    build_structure_insight_p6_gate_hardening,
    dump_structure_insight_p6_gate_hardening_public_summary,
)
from emlis_ai_structure_insight_p6_quality_rubric import (
    P6_QUALITY_RUBRIC_DIMENSION_TARGETS,
    build_structure_insight_p6_quality_rubric,
)
from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy


FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "history_context",
    "historyContext",
    "history_records",
    "historyRecords",
    "history_raw_text",
    "historyRawText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_comment_text",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "reply_text",
    "replyText",
    "display_text",
    "displayText",
    "observation_text",
    "reception_text",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_free_text",
    "raw_test_output",
    "test_output",
    "command_output",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _boundary() -> dict[str, Any]:
    return build_structure_insight_p6_family_boundary(
        family="structure_question",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        run_id="p6_gate_boundary_source",
    )


def _policy(relation_family: str = "desire_blockage_conflict") -> dict[str, Any]:
    return build_structure_insight_p6_relation_policy(
        relation_family=relation_family,
        p6_family_boundary=_boundary(),
        run_id=f"p6_gate_policy_{relation_family}",
    )


def _quality(
    relation_family: str = "desire_blockage_conflict",
    *,
    ratings: dict[str, float] | None = None,
    red_flags: list[str] | None = None,
    repair_flags: list[str] | None = None,
) -> dict[str, Any]:
    return build_structure_insight_p6_quality_rubric(
        review_rows=[
            {
                "row_id": f"p6_gate_quality_{relation_family}",
                "family": "structure_question",
                "relation_family": relation_family,
                "ratings": ratings or dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
                "red_flags": red_flags or [],
                "repair_flags": repair_flags or [],
            }
        ],
        p6_relation_policy=_policy(relation_family),
        p6_family_boundary=_boundary(),
        run_id=f"p6_gate_quality_report_{relation_family}",
    )


def test_p6_5_allows_body_free_soft_surface_after_ready_policy_and_quality() -> None:
    surface = "変えたい気持ちと動けない状態が重なっているように見えます。"
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface=surface,
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(),
        run_id="p6_gate_safe_soft_surface",
    )
    summary = report["summary"]

    assert report["schema_version"] == STRUCTURE_INSIGHT_P6_GATE_HARDENING_SCHEMA_VERSION
    assert report["step"] == STRUCTURE_INSIGHT_P6_GATE_HARDENING_STEP
    assert summary["schema_version"] == STRUCTURE_INSIGHT_P6_GATE_HARDENING_SUMMARY_SCHEMA_VERSION
    assert report["decision"] == GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE
    assert report["passed"] is True
    assert summary["soft_expression_required_enforced"] is True
    assert summary["soft_expression_marker_detected"] is True
    assert summary["comment_text_written_by_gate"] is False
    assert summary["public_response_key_added"] is False
    assert summary["body_free"]["comment_text_body_included"] is False
    assert _contains_forbidden_raw_key(report) is False
    assert surface not in json.dumps(report, ensure_ascii=False)
    assert_structure_insight_p6_gate_hardening_contract(report)


def test_p6_5_blocks_missing_soft_expression() -> None:
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface="変えたい気持ちと動けない状態が重なっています。",
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(),
    )

    assert report["decision"] == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    assert report["summary"]["soft_expression_missing_blocked"] is True
    assert REASON_SOFT_EXPRESSION_MISSING in report["summary"]["decision_reason_codes"]


def test_p6_5_blocks_unsafe_claims_even_when_soft_marker_exists() -> None:
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface=(
            "原因はあなたの性格です。診断が必要かもしれません。"
            "相談しましょう。次は必ずうまくいきます。相手が悪いように見えます。"
            "相手はわざと見下しています。"
        ),
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(),
    )
    reasons = report["summary"]["decision_reason_codes"]

    assert report["decision"] == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    assert report["summary"]["unsafe_insight_surface_blocked"] is True
    assert REASON_DIAGNOSIS_SURFACE in reasons
    assert REASON_PERSONALITY_CLAIM_SURFACE in reasons
    assert REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE in reasons
    assert REASON_ADVICE_SURFACE in reasons
    assert REASON_FUTURE_PREDICTION_SURFACE in reasons
    assert REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE in reasons
    assert REASON_TARGET_INTENT_ASSERTION_SURFACE in reasons


def test_p6_5_blocks_self_denial_identity_claim_as_fact() -> None:
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface="あなたは何もできない状態です、ということかもしれません。",
        relation_family="self_denial_identity_split",
        p6_relation_policy=_policy("self_denial_identity_split"),
        p6_quality_rubric=_quality("self_denial_identity_split"),
    )

    assert report["decision"] == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    assert report["summary"]["self_denial_identity_claim_as_fact_surface_blocked"] is True
    assert REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE in report["summary"]["decision_reason_codes"]


def test_p6_5_review_required_when_relation_policy_is_not_initial_visible_but_surface_is_soft() -> None:
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface="出来事への反応が少し残っているのかもしれません。",
        relation_family="event_reaction_link",
        p6_relation_policy=_policy("event_reaction_link"),
        p6_quality_rubric=_quality("event_reaction_link"),
    )

    assert report["decision"] == GATE_DECISION_REVIEW_REQUIRED
    assert report["review_required"] is True
    assert "p6_relation_policy_not_initial_visible" in report["summary"]["decision_reason_codes"]


def test_p6_5_blocks_red_or_repair_required_quality_before_surface_connection() -> None:
    red = build_structure_insight_p6_gate_hardening(
        proposed_surface="変えたい気持ちが残っているのかもしれません。",
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(red_flags=["diagnosis"]),
    )
    assert red["decision"] == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    assert "p6_quality_rubric_red" in red["summary"]["decision_reason_codes"]

    repair = build_structure_insight_p6_gate_hardening(
        proposed_surface="変えたい気持ちが残っているのかもしれません。",
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(repair_flags=["insight_too_shallow"]),
    )
    assert repair["decision"] == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    assert "p6_quality_rubric_repair_required" in repair["summary"]["decision_reason_codes"]


def test_p6_5_blocks_comment_text_meta_public_contract_mutation_and_dictionary_fact() -> None:
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface="変えたい気持ちが残っているのかもしれません。",
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(),
        gate_meta={"comment_text": "body must not be here", "public_response_key_added": True},
        user_dictionary_meta={"user_dictionary_used_as_fact": True},
    )
    reasons = report["summary"]["decision_reason_codes"]

    assert report["decision"] == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    assert REASON_COMMENT_TEXT_BODY_IN_META_DETECTED in reasons
    assert REASON_PUBLIC_CONTRACT_MUTATION_DETECTED in reasons
    assert "user_dictionary_fact_claim_blocked" in reasons


def test_p6_5_public_summary_stays_body_free() -> None:
    surface = "変えたい気持ちと止まっている状態が重なっているように見えます。"
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface=surface,
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(),
    )
    dumped = dump_structure_insight_p6_gate_hardening_public_summary(report)
    loaded = json.loads(dumped)

    assert loaded["decision"] == GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE
    assert loaded["comment_text_written_by_gate"] is False
    assert loaded["public_response_key_added"] is False
    assert surface not in dumped
    assert _contains_forbidden_raw_key(loaded) is False


def test_p6_5_contract_rejects_body_or_release_flags() -> None:
    report = build_structure_insight_p6_gate_hardening(
        proposed_surface="変えたい気持ちが残っているのかもしれません。",
        relation_family="desire_blockage_conflict",
        p6_relation_policy=_policy(),
        p6_quality_rubric=_quality(),
    )
    leaked = dict(report)
    leaked["comment_text"] = "leak"
    with pytest.raises(ValueError):
        assert_structure_insight_p6_gate_hardening_contract(leaked)

    released = dict(report)
    released["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_structure_insight_p6_gate_hardening_contract(released)
