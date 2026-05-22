from __future__ import annotations

import json
from typing import Any

import pytest

from emlis_ai_observation_regression_fixture_coverage import (
    FIXTURE_FREE_USER_FACT_BLOCK,
    FIXTURE_LONG_LOW_INFORMATION,
    FIXTURE_OVERCLAIM_INDUCTION,
    FIXTURE_SHORT_ELIGIBLE,
    FIXTURE_SHORT_LOW_INFORMATION,
    FIXTURE_STANDARD_ELIGIBLE,
    FIXTURE_SUBSCRIPTION_EXPLICIT_FACT,
    FIXTURE_SUBSCRIPTION_IMPLICIT_FACT,
    OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
    OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS,
    assert_observation_regression_fixture_coverage_contract,
    build_observation_regression_fixture_coverage,
    build_observation_regression_fixture_definitions,
    dump_observation_regression_fixture_coverage,
    normalize_observation_regression_fixture_event,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_COMPANION_CLOSE,
    OBSERVATION_ROLE_EMPATHY,
    OBSERVATION_ROLE_INPUT_ARRANGEMENT,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    OBSERVATION_ROLE_STATE_VERBALIZATION,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
)
from emlis_ai_observation_scorecard_blind_qa import build_observation_scorecard_blind_qa


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in ("raw_input", "raw_text", "input_text", "user_input", "comment_text", "reply_text", "body", "text"):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _event(
    group: str,
    *,
    kind: str,
    plan: str = "free",
    user_fact_mode: str = USER_FACT_GROUNDING_MODE_DISABLED,
    roles: list[str] | None = None,
    unknown_slots: list[str] | None = None,
    facts_used: list[dict[str, str]] | None = None,
    surface_disclosure_required: bool = False,
    question_required: bool | None = None,
    line_count: int | None = None,
    surface_role_merge: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    low_info = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    meta = {
        "observation_reply_kind": kind,
        "eligibility_status": "low_information" if low_info else "eligible",
        "eligible_for_full_observation": not low_info,
        "question_required": low_info if question_required is None else question_required,
        "unknown_slots": unknown_slots or (["event"] if low_info else []),
        "sentence_plan_observation_roles": roles or [],
        "user_fact_grounding_mode": user_fact_mode,
        "facts_used": facts_used or [],
        "surface_disclosure_required": surface_disclosure_required,
        "plan": plan,
        "user_fact_may_promote_to_eligible": False,
        "must_not_assert_current_event_from_user_fact": True,
    }
    event = {
        "fixture_id": f"fx-{group}",
        "fixture_group": group,
        "coverage_group": group,
        "observation_status": "passed",
        "passed_body_returned": True,
        "comment_text_present": True,
        "observation_reply_meta": meta,
        "expected_observation_reply_kind": kind,
        "expected_eligibility_status": "low_information" if low_info else "eligible",
        "plan": plan,
        "user_fact_grounding_mode": user_fact_mode,
        "line_count": line_count or (2 if low_info else 3),
        "surface_role_merge": surface_role_merge or [],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    if extra:
        event.update(extra)
    return event


def _full_fixture_events() -> list[dict[str, Any]]:
    return [
        _event(
            FIXTURE_SHORT_LOW_INFORMATION,
            kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            roles=[OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
            unknown_slots=["event"],
            extra={"known_scope_only": True},
        ),
        _event(
            FIXTURE_LONG_LOW_INFORMATION,
            kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            roles=[OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
            unknown_slots=["event", "relation"],
            extra={"known_scope_only": True, "relation_confidence_limited": True},
        ),
        _event(
            FIXTURE_SHORT_ELIGIBLE,
            kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            roles=[OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
            line_count=2,
            surface_role_merge=["empathy+input_arrangement"],
        ),
        _event(
            FIXTURE_STANDARD_ELIGIBLE,
            kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            roles=[
                OBSERVATION_ROLE_EMPATHY,
                OBSERVATION_ROLE_INPUT_ARRANGEMENT,
                OBSERVATION_ROLE_STATE_VERBALIZATION,
                OBSERVATION_ROLE_COMPANION_CLOSE,
            ],
            line_count=4,
        ),
        _event(
            FIXTURE_SUBSCRIPTION_EXPLICIT_FACT,
            kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            plan="subscription",
            user_fact_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
            roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
            facts_used=[{"fact_id": "fact-env"}],
            surface_disclosure_required=True,
        ),
        _event(
            FIXTURE_SUBSCRIPTION_IMPLICIT_FACT,
            kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            plan="subscription",
            user_fact_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
            roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
            facts_used=[{"fact_id": "fact-focus"}],
            surface_disclosure_required=False,
        ),
        _event(
            FIXTURE_FREE_USER_FACT_BLOCK,
            kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            plan="free",
            user_fact_mode=USER_FACT_GROUNDING_MODE_DISABLED,
            roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
            extra={"free_user_fact_blocked": True, "facts_ignored_count": 1},
        ),
        _event(
            FIXTURE_OVERCLAIM_INDUCTION,
            kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            plan="subscription",
            user_fact_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
            roles=[OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
            facts_used=[{"fact_id": "fact-1"}, {"fact_id": "fact-2"}],
            unknown_slots=["event"],
            extra={"known_scope_only": True, "overclaim_count": 0, "assert_current_event_from_user_fact": False},
        ),
    ]


def test_step13_fixture_definitions_cover_all_required_groups_and_are_meta_only() -> None:
    definitions = build_observation_regression_fixture_definitions()

    assert [item["fixture_group"] for item in definitions] == list(OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS)
    assert len(definitions) == 8
    for item in definitions:
        assert item["version"] == "emlis.observation_regression_fixture_definitions.v1"
        assert item["expected_observation_reply_kind"] in {OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION}
        _assert_meta_only(item)


def test_step13_full_regression_fixture_coverage_passes_all_groups_and_connects_to_scorecard() -> None:
    events = _full_fixture_events()
    coverage = build_observation_regression_fixture_coverage(scorecard_events=events, run_id="step13-full")

    assert coverage["version"] == OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION
    assert coverage["step13_regression_fixture_coverage_ready"] is True
    assert coverage["fixture_coverage_rate"] == 1.0
    assert coverage["missing_fixture_groups"] == []
    assert coverage["failed_fixture_groups"] == []
    _assert_meta_only(coverage)

    scorecard = build_observation_scorecard_blind_qa(
        scorecard_events=events,
        blind_qa_reviews=[
            {
                "review_id": "blind-step13",
                "ratings": {
                    "read_feeling": "green",
                    "input_arrangement": "green",
                    "state_verbalization": "green",
                    "low_info_question_quality": "green",
                    "user_fact_boundary": "green",
                    "overclaim_absence": "green",
                    "non_template": "green",
                },
            }
        ],
    )
    assert scorecard["step13_observation_regression_fixture_coverage_ready"] is True
    assert scorecard["observation_regression_fixture_coverage_rate"] == 1.0
    _assert_meta_only(scorecard)


def test_step13_detects_missing_and_failed_fixture_groups() -> None:
    bad_short_low_info = _event(
        FIXTURE_SHORT_LOW_INFORMATION,
        kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        roles=[OBSERVATION_ROLE_STATE_VERBALIZATION],
        extra={"eligible_for_full_observation": True},
    )
    coverage = build_observation_regression_fixture_coverage(scorecard_events=[bad_short_low_info])

    assert coverage["step13_regression_fixture_coverage_ready"] is False
    assert FIXTURE_SHORT_LOW_INFORMATION in coverage["failed_fixture_groups"]
    assert FIXTURE_LONG_LOW_INFORMATION in coverage["missing_fixture_groups"]
    assert "reply_kind_mismatch" in coverage["by_fixture_group"][FIXTURE_SHORT_LOW_INFORMATION]["failure_reasons"]
    assert "observation_regression_fixture_groups_missing" in coverage["release_blockers"]
    assert "observation_regression_fixture_groups_failed" in coverage["release_blockers"]
    _assert_meta_only(coverage)


def test_step13_free_fixture_fails_if_user_facts_are_used() -> None:
    free_violation = _event(
        FIXTURE_FREE_USER_FACT_BLOCK,
        kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        plan="free",
        user_fact_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        facts_used=[{"fact_id": "fact-leak"}],
        roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
        extra={"free_user_fact_violation": True},
    )
    normalized = normalize_observation_regression_fixture_event(free_violation)

    assert normalized["fixture_expectation_passed"] is False
    assert "free_fixture_facts_used" in normalized["fixture_failure_reasons"]
    assert "free_fixture_user_fact_mode_not_disabled" in normalized["fixture_failure_reasons"]


def test_step13_rejects_raw_or_comment_text_payloads() -> None:
    with pytest.raises(ValueError):
        normalize_observation_regression_fixture_event({"fixture_group": FIXTURE_SHORT_LOW_INFORMATION, "raw_input": "must not persist"})
    with pytest.raises(ValueError):
        assert_observation_regression_fixture_coverage_contract({"comment_text": "must not persist"})

    dumped = dump_observation_regression_fixture_coverage(build_observation_regression_fixture_coverage(scorecard_events=_full_fixture_events()))
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped
    json.loads(dumped)


def test_low_information_short_input_returns_passed_body() -> None:
    event = _event(
        FIXTURE_SHORT_LOW_INFORMATION,
        kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        roles=[OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
        unknown_slots=["event"],
    )
    normalized = normalize_observation_regression_fixture_event(event)
    assert normalized["fixture_expectation_passed"] is True
    assert normalized["actual_observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert normalized["always_display_success"] is True
    assert normalized["question_required"] is True


def test_long_ambiguous_input_returns_low_info_question() -> None:
    event = _event(
        FIXTURE_LONG_LOW_INFORMATION,
        kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        roles=[OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
        unknown_slots=["event", "relation"],
        extra={"known_scope_only": True, "relation_confidence_limited": True},
    )
    normalized = normalize_observation_regression_fixture_event(event)
    assert normalized["fixture_expectation_passed"] is True
    assert normalized["actual_eligibility_status"] == "low_information"
    assert "event" in normalized["unknown_slots"]
    assert normalized["question_required"] is True


def test_user_fact_does_not_promote_low_info() -> None:
    event = _event(
        FIXTURE_OVERCLAIM_INDUCTION,
        kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        plan="subscription",
        user_fact_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
        facts_used=[{"fact_id": "fact-history-a"}, {"fact_id": "fact-history-b"}],
        roles=[OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
        unknown_slots=["event"],
        extra={"user_fact_may_promote_to_eligible": False, "assert_current_event_from_user_fact": False},
    )
    normalized = normalize_observation_regression_fixture_event(event)
    assert normalized["fixture_expectation_passed"] is True
    assert normalized["actual_observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert normalized["false_eligible"] is False
    assert normalized["overclaim"] is False


def test_free_never_uses_user_fact() -> None:
    event = _event(
        FIXTURE_FREE_USER_FACT_BLOCK,
        kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        plan="free",
        user_fact_mode=USER_FACT_GROUNDING_MODE_DISABLED,
        roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
        facts_used=[],
        extra={"free_user_fact_blocked": True, "facts_ignored_count": 1},
    )
    normalized = normalize_observation_regression_fixture_event(event)
    assert normalized["fixture_expectation_passed"] is True
    assert normalized["plan"] == "free"
    assert normalized["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_DISABLED
    assert normalized["facts_used_count"] == 0


def test_subscription_explicit_user_fact_requires_disclosure() -> None:
    event = _event(
        FIXTURE_SUBSCRIPTION_EXPLICIT_FACT,
        kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        plan="subscription",
        user_fact_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
        facts_used=[{"fact_id": "fact-explicit"}],
        surface_disclosure_required=True,
    )
    normalized = normalize_observation_regression_fixture_event(event)
    assert normalized["fixture_expectation_passed"] is True
    assert normalized["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    assert normalized["facts_used_count"] == 1


def test_subscription_implicit_user_fact_no_surface_disclosure() -> None:
    event = _event(
        FIXTURE_SUBSCRIPTION_IMPLICIT_FACT,
        kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        plan="subscription",
        user_fact_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
        roles=[OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION],
        facts_used=[{"fact_id": "fact-implicit"}],
        surface_disclosure_required=False,
    )
    normalized = normalize_observation_regression_fixture_event(event)
    assert normalized["fixture_expectation_passed"] is True
    assert normalized["user_fact_grounding_mode"] == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
    assert normalized["facts_used_count"] == 1


def test_short_eligible_role_merge_allowed() -> None:
    definitions = {item["fixture_group"]: item for item in build_observation_regression_fixture_definitions()}
    short_eligible = definitions[FIXTURE_SHORT_ELIGIBLE]
    assert short_eligible["expected_observation_reply_kind"] == OBSERVATION_REPLY_KIND_ELIGIBLE
    assert OBSERVATION_ROLE_EMPATHY in short_eligible["expected_observation_roles"]
    assert OBSERVATION_ROLE_INPUT_ARRANGEMENT in short_eligible["expected_observation_roles"]
    assert OBSERVATION_ROLE_STATE_VERBALIZATION in short_eligible["expected_observation_roles"]


def test_low_info_question_not_only_question() -> None:
    definitions = {item["fixture_group"]: item for item in build_observation_regression_fixture_definitions()}
    short_low = definitions[FIXTURE_SHORT_LOW_INFORMATION]
    assert OBSERVATION_ROLE_LOW_INFO_RECEIVE in short_low["expected_observation_roles"]
    assert OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE in short_low["expected_observation_roles"]
    assert OBSERVATION_ROLE_LOW_INFO_QUESTION in short_low["expected_observation_roles"]
    assert short_low["expected_question_required"] is True


def test_display_gate_accepts_low_info_observation() -> None:
    coverage = build_observation_regression_fixture_coverage(
        scorecard_events=[
            _event(
                FIXTURE_SHORT_LOW_INFORMATION,
                kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
                roles=[OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION],
                unknown_slots=["event"],
            )
        ]
    )
    assert coverage["by_fixture_group"][FIXTURE_SHORT_LOW_INFORMATION]["passed"] is True
    assert coverage["always_display_rate"] == 1.0


def test_no_new_public_status_required() -> None:
    definitions = build_observation_regression_fixture_definitions()
    coverage = build_observation_regression_fixture_coverage(scorecard_events=_full_fixture_events())
    assert all(item["public_status_extended"] is False for item in definitions)
    assert coverage["public_status_extended"] is False
    assert coverage["observation_status_enum_extended"] is False
    assert coverage["rn_visible_contract_changed"] is False
