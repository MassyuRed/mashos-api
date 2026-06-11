# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
from emlis_ai_structure_insight_p6_gate_hardening import build_structure_insight_p6_gate_hardening
from emlis_ai_structure_insight_p6_quality_rubric import (
    P6_QUALITY_RUBRIC_DIMENSION_TARGETS,
    build_structure_insight_p6_quality_rubric,
)
from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy
from emlis_ai_structure_insight_p6_surface_role_plan import (
    FAMILY_STRUCTURE_QUESTION,
    P6_STRUCTURE_QUESTION_ALLOWED_RELATION_FAMILIES,
    REASON_FAMILY_REVIEW_DEFERRED_TO_P6_7,
    REASON_FIXED_SENTENCE_TEMPLATE_DETECTED,
    REASON_INITIAL_BLOCK_RELATION_FAMILY,
    REASON_INSIGHT_SEED_COUNT_ABOVE_LIMIT,
    REASON_P6_GATE_HARDENING_NOT_PASSED,
    REASON_RELATION_NOT_ALLOWED_FOR_STRUCTURE_QUESTION,
    REASON_VALUE_LINE_TARGET_JUDGEMENT_RISK_BLOCKED,
    ROLE_NON_IMPOSING_RECEPTION_BOUNDARY,
    ROLE_OBSERVATION_INSIGHT_SEED,
    ROLE_SOFT_INFERENCE_SURFACE_REQUIRED,
    SECTION_HUMAN_RECEPTION,
    STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_STEP,
    SURFACE_PLAN_BLOCKED,
    SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED,
    SURFACE_PLAN_META_ONLY,
    assert_structure_insight_p6_surface_role_plan_contract,
    build_structure_insight_p6_surface_role_plan,
    dump_structure_insight_p6_surface_role_plan_public_summary,
)


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


def _boundary(family: str = FAMILY_STRUCTURE_QUESTION) -> dict[str, Any]:
    return build_structure_insight_p6_family_boundary(
        family=family,
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        run_id=f"p6_surface_role_boundary_{family}",
    )


def _policy(relation_family: str = "desire_blockage_conflict") -> dict[str, Any]:
    return build_structure_insight_p6_relation_policy(
        relation_family=relation_family,
        p6_family_boundary=_boundary(),
        run_id=f"p6_surface_role_policy_{relation_family}",
    )


def _quality(relation_family: str = "desire_blockage_conflict") -> dict[str, Any]:
    return build_structure_insight_p6_quality_rubric(
        review_rows=[
            {
                "row_id": f"p6_surface_role_quality_{relation_family}",
                "family": FAMILY_STRUCTURE_QUESTION,
                "relation_family": relation_family,
                "ratings": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
            }
        ],
        p6_relation_policy=_policy(relation_family),
        p6_family_boundary=_boundary(),
        run_id=f"p6_surface_role_quality_report_{relation_family}",
    )


def _gate(relation_family: str = "desire_blockage_conflict", *, soft: bool = True) -> dict[str, Any]:
    surface = (
        "変えたい気持ちと動けない状態が重なっているように見えます。"
        if soft
        else "変えたい気持ちと動けない状態が重なっています。"
    )
    return build_structure_insight_p6_gate_hardening(
        proposed_surface=surface,
        relation_family=relation_family,
        p6_relation_policy=_policy(relation_family),
        p6_quality_rubric=_quality(relation_family),
        run_id=f"p6_surface_role_gate_{relation_family}",
    )


def _ready_plan(relation_family: str = "desire_blockage_conflict", **overrides: Any) -> dict[str, Any]:
    kwargs = {
        "family": FAMILY_STRUCTURE_QUESTION,
        "relation_family": relation_family,
        "p6_family_boundary": _boundary(),
        "p6_relation_policy": _policy(relation_family),
        "p6_quality_rubric": _quality(relation_family),
        "p6_gate_hardening": _gate(relation_family),
        "run_id": f"p6_surface_role_plan_{relation_family}",
    }
    kwargs.update(overrides)
    return build_structure_insight_p6_surface_role_plan(**kwargs)


def test_p6_6_connects_limited_surface_role_plan_only_for_structure_question() -> None:
    plan = _ready_plan()
    summary = plan["summary"]

    assert plan["schema_version"] == STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SCHEMA_VERSION
    assert plan["step"] == STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_STEP
    assert plan["family"] == FAMILY_STRUCTURE_QUESTION
    assert plan["surface_plan_kind"] == SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
    assert plan["limited_surface_candidate"] is True
    assert plan["max_insight_seed_count"] == 1
    assert plan["planned_insight_seed_count"] == 1
    assert summary["observation_section_seed_count"] == 1
    assert ROLE_OBSERVATION_INSIGHT_SEED in plan["must_include_roles"]
    assert ROLE_SOFT_INFERENCE_SURFACE_REQUIRED in plan["must_include_roles"]
    assert ROLE_NON_IMPOSING_RECEPTION_BOUNDARY in plan["section_role_plan"][SECTION_HUMAN_RECEPTION]
    assert plan["public_contract"]["fixed_sentence_template_added"] is False
    assert plan["body_free"]["surface_body_included"] is False
    assert _contains_forbidden_raw_key(plan) is False
    assert_structure_insight_p6_surface_role_plan_contract(plan)


def test_p6_6_allowed_structure_question_relations_share_limited_plan() -> None:
    for relation in P6_STRUCTURE_QUESTION_ALLOWED_RELATION_FAMILIES:
        plan = _ready_plan(relation)

        assert plan["surface_plan_kind"] == SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
        assert plan["relation_family"] == relation
        assert plan["planned_insight_seed_count"] == 1


def test_p6_6_non_structure_question_target_families_stay_meta_only_for_p6_7() -> None:
    plan = build_structure_insight_p6_surface_role_plan(
        family="long_meaning_arc",
        relation_family="desire_blockage_conflict",
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_META_ONLY
    assert plan["limited_surface_candidate"] is False
    assert plan["planned_insight_seed_count"] == 0
    assert REASON_FAMILY_REVIEW_DEFERRED_TO_P6_7 in plan["decision_reason_codes"]


def test_p6_6_blocks_initially_blocked_or_target_judgement_risky_relations() -> None:
    for relation in (
        "self_denial_identity_split",
        "low_information_unspecified_weight",
        "period_tendency_from_single_record",
        "history_fact_line_as_insight",
    ):
        plan = _ready_plan(relation)

        assert plan["surface_plan_kind"] == SURFACE_PLAN_BLOCKED
        assert REASON_INITIAL_BLOCK_RELATION_FAMILY in plan["decision_reason_codes"]

    value_line = _ready_plan(
        "value_line_crossed",
        target_judgement_risk=True,
    )
    assert value_line["surface_plan_kind"] == SURFACE_PLAN_BLOCKED
    assert REASON_VALUE_LINE_TARGET_JUDGEMENT_RISK_BLOCKED in value_line["decision_reason_codes"]


def test_p6_6_unknown_relation_is_meta_only_not_initial_surface() -> None:
    plan = build_structure_insight_p6_surface_role_plan(
        family=FAMILY_STRUCTURE_QUESTION,
        relation_family="new_unreviewed_relation",
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_META_ONLY
    assert REASON_RELATION_NOT_ALLOWED_FOR_STRUCTURE_QUESTION in plan["decision_reason_codes"]


def test_p6_6_blocks_when_gate_is_missing_or_not_passed_and_limits_seed_count() -> None:
    missing_gate = _ready_plan(p6_gate_hardening={})
    assert missing_gate["surface_plan_kind"] == SURFACE_PLAN_BLOCKED
    assert "p6_gate_hardening_required" in missing_gate["decision_reason_codes"]

    failed_gate = _ready_plan(p6_gate_hardening=_gate(soft=False))
    assert failed_gate["surface_plan_kind"] == SURFACE_PLAN_BLOCKED
    assert REASON_P6_GATE_HARDENING_NOT_PASSED in failed_gate["decision_reason_codes"]

    too_many = _ready_plan(requested_insight_seed_count=2)
    assert too_many["surface_plan_kind"] == SURFACE_PLAN_BLOCKED
    assert too_many["planned_insight_seed_count"] == 0
    assert REASON_INSIGHT_SEED_COUNT_ABOVE_LIMIT in too_many["decision_reason_codes"]


def test_p6_6_blocks_fixed_sentence_template_or_public_contract_mutation() -> None:
    plan = _ready_plan(
        surface_plan_meta={
            "fixed_sentence_template_added": True,
            "public_response_key_added": True,
        }
    )

    assert plan["surface_plan_kind"] == SURFACE_PLAN_BLOCKED
    assert REASON_FIXED_SENTENCE_TEMPLATE_DETECTED in plan["decision_reason_codes"]
    assert "public_contract_mutation_detected" in plan["decision_reason_codes"]


def test_p6_6_public_summary_stays_body_free() -> None:
    plan = _ready_plan()
    dumped = dump_structure_insight_p6_surface_role_plan_public_summary(plan)
    loaded = json.loads(dumped)

    assert loaded["surface_plan_kind"] == SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
    assert loaded["planned_insight_seed_count"] == 1
    assert loaded["public_contract"]["fixed_sentence_template_added"] is False
    assert _contains_forbidden_raw_key(loaded) is False


def test_p6_6_contract_rejects_body_or_release_flags() -> None:
    plan = _ready_plan()
    leaked = dict(plan)
    leaked["surface_text"] = "leak"
    with pytest.raises(ValueError):
        assert_structure_insight_p6_surface_role_plan_contract(leaked)

    released = dict(plan)
    released["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_structure_insight_p6_surface_role_plan_contract(released)
