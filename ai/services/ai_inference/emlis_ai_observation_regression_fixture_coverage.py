# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 13 regression fixture coverage for EmlisAI observation replies.

This module is intentionally meta-only.  It defines the regression fixture
coverage groups required by Step 13, normalizes scorecard/runtime events into
fixture coverage events, and exposes scorecard fields without storing raw user
input or public comment text.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
import re
from typing import Any, Final

from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    UNKNOWN_SLOT_DESIRED_DIRECTION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
)

OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION: Final = "emlis.observation_regression_fixture_coverage.v1"
OBSERVATION_REGRESSION_FIXTURE_SUITE_VERSION: Final = "emlis.observation_regression_fixture_suite.v1"
OBSERVATION_REGRESSION_FIXTURE_EVENT_VERSION: Final = "emlis.observation_regression_fixture_event.v1"
OBSERVATION_REGRESSION_FIXTURE_DEFINITIONS_VERSION: Final = "emlis.observation_regression_fixture_definitions.v1"
OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP: Final = "Step13_Regression_Fixture_Coverage"

FIXTURE_GROUP_SHORT_LOW_INFORMATION: Final = "short_low_information"
FIXTURE_GROUP_LONG_LOW_INFORMATION: Final = "long_low_information"
FIXTURE_GROUP_SHORT_ELIGIBLE: Final = "short_eligible"
FIXTURE_GROUP_STANDARD_ELIGIBLE: Final = "standard_eligible"
FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT: Final = "subscription_explicit_fact"
FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT: Final = "subscription_implicit_fact"
FIXTURE_GROUP_FREE_USER_FACT_BLOCK: Final = "free_user_fact_block"
FIXTURE_GROUP_OVERCLAIM_INDUCING: Final = "overclaim_inducing"

# Short aliases used by Step13 tests and handoff tooling.
FIXTURE_SHORT_LOW_INFORMATION: Final = FIXTURE_GROUP_SHORT_LOW_INFORMATION
FIXTURE_LONG_LOW_INFORMATION: Final = FIXTURE_GROUP_LONG_LOW_INFORMATION
FIXTURE_SHORT_ELIGIBLE: Final = FIXTURE_GROUP_SHORT_ELIGIBLE
FIXTURE_STANDARD_ELIGIBLE: Final = FIXTURE_GROUP_STANDARD_ELIGIBLE
FIXTURE_SUBSCRIPTION_EXPLICIT_FACT: Final = FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT
FIXTURE_SUBSCRIPTION_IMPLICIT_FACT: Final = FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT
FIXTURE_FREE_USER_FACT_BLOCK: Final = FIXTURE_GROUP_FREE_USER_FACT_BLOCK
FIXTURE_OVERCLAIM_INDUCTION: Final = FIXTURE_GROUP_OVERCLAIM_INDUCING

# Additional aliases retained for older drafts and Product Quality handoff code.
OBSERVATION_FIXTURE_GROUP_SHORT_LOW_INFORMATION: Final = FIXTURE_GROUP_SHORT_LOW_INFORMATION
OBSERVATION_FIXTURE_GROUP_LONG_LOW_INFORMATION: Final = FIXTURE_GROUP_LONG_LOW_INFORMATION
OBSERVATION_FIXTURE_GROUP_SHORT_ELIGIBLE: Final = FIXTURE_GROUP_SHORT_ELIGIBLE
OBSERVATION_FIXTURE_GROUP_STANDARD_ELIGIBLE: Final = FIXTURE_GROUP_STANDARD_ELIGIBLE
OBSERVATION_FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT: Final = FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT
OBSERVATION_FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT: Final = FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT
OBSERVATION_FIXTURE_GROUP_FREE_USER_FACT_BOUNDARY: Final = FIXTURE_GROUP_FREE_USER_FACT_BLOCK
OBSERVATION_FIXTURE_GROUP_OVERCLAIM_INDUCTION: Final = FIXTURE_GROUP_OVERCLAIM_INDUCING
FIXTURE_GROUP_FREE_WITH_USER_MODEL: Final = FIXTURE_GROUP_FREE_USER_FACT_BLOCK
FIXTURE_GROUP_OVERCLAIM_INDUCEMENT: Final = FIXTURE_GROUP_OVERCLAIM_INDUCING
FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_USER_FACT: Final = FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT
FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_USER_FACT: Final = FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT

OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS: Final = (
    FIXTURE_GROUP_SHORT_LOW_INFORMATION,
    FIXTURE_GROUP_LONG_LOW_INFORMATION,
    FIXTURE_GROUP_SHORT_ELIGIBLE,
    FIXTURE_GROUP_STANDARD_ELIGIBLE,
    FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT,
    FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT,
    FIXTURE_GROUP_FREE_USER_FACT_BLOCK,
    FIXTURE_GROUP_OVERCLAIM_INDUCING,
)
OBSERVATION_REGRESSION_FIXTURE_GROUP_ORDER: Final = OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS
REQUIRED_OBSERVATION_REGRESSION_FIXTURE_GROUPS: Final = OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS

_SPACE_RE: Final = re.compile(r"\s+")
_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
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
        "memo",
        "memo_text",
        "memoText",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "reply_text",
        "replyText",
        "surface_text",
        "expected_surface_text",
        "expected_comment_text",
        "realized_text",
        "must_equal_text",
        "expected_body",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "public_status_extended",
        "observation_status_enum_extended",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "reader_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_achieved",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = [values]
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean(value).lower() in {"1", "true", "yes", "y", "on", "passed", "pass"}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)


def _meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        result = as_meta()
        return dict(result) if isinstance(result, Mapping) else {}
    return {}


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _safe_fact_refs(refs: Any) -> list[dict[str, Any]]:
    if refs is None:
        return []
    if isinstance(refs, Mapping):
        iterable: Iterable[Any] = [refs]
    elif isinstance(refs, Sequence) and not isinstance(refs, (str, bytes, bytearray)):
        iterable = refs
    else:
        iterable = [refs]
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            fact_id = _clean(item.get("fact_id") or item.get("id") or item.get("ref_id") or item.get("source_id")) or f"user_fact_ref_{index + 1}"
            ref: dict[str, Any] = {"fact_id": fact_id}
            for key in ("source_kind", "kind", "mode", "role", "status"):
                text = _clean(item.get(key))
                if text:
                    ref[key] = text
        else:
            fact_id = _clean(item)
            if not fact_id:
                continue
            ref = {"fact_id": fact_id}
        marker = json.dumps(ref, ensure_ascii=False, sort_keys=True)
        if marker not in seen:
            seen.add(marker)
            out.append(ref)
    return out


def _expected_kind_for_group(group: str) -> str:
    if group in {FIXTURE_GROUP_SHORT_LOW_INFORMATION, FIXTURE_GROUP_LONG_LOW_INFORMATION, FIXTURE_GROUP_OVERCLAIM_INDUCING}:
        return OBSERVATION_REPLY_KIND_LOW_INFORMATION
    if group in {FIXTURE_GROUP_SHORT_ELIGIBLE, FIXTURE_GROUP_STANDARD_ELIGIBLE, FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT, FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT}:
        return OBSERVATION_REPLY_KIND_ELIGIBLE
    return ""


def _expected_status_from_kind(kind: str) -> str:
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        return OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if kind == OBSERVATION_REPLY_KIND_ELIGIBLE:
        return OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    return ""


def _event_meta(event: Mapping[str, Any]) -> dict[str, Any]:
    for key in (
        "observation_reply_meta",
        "observation_reply_contract",
        "step10_observation_display_repair_integration",
        "diagnostic_summary",
        "emlis_ai",
    ):
        meta = _meta(event.get(key))
        if meta.get("observation_reply_kind") or meta.get("eligibility_status"):
            return meta
    return {}


def _event_passed_body(event: Mapping[str, Any]) -> bool:
    status = _clean(event.get("observation_status") or event.get("backend_observation_status"))
    return bool(
        (status == "passed" and (event.get("comment_text_present") is True or event.get("passed_body_returned") is True))
        or event.get("comment_text_present") is True
        or event.get("passed_body_returned") is True
        or event.get("display_confirmed") is True
        or _as_int(event.get("passed_display_count")) > 0
    )


@dataclass(frozen=True)
class ObservationRegressionFixture:
    fixture_id: str
    fixture_group: str
    expected_observation_reply_kind: str
    expected_eligibility_status: str
    expected_unknown_slots: tuple[str, ...] = ()
    expected_question_required: bool = False
    expected_user_fact_grounding_mode: str = USER_FACT_GROUNDING_MODE_DISABLED
    subscription_tier: str = "free"
    expected_facts_used: tuple[Mapping[str, Any], ...] = ()
    expected_facts_ignored: tuple[Mapping[str, Any], ...] = ()
    expected_surface_disclosure_required: bool = False
    expected_surface_disclosure_forbidden: bool = False
    expected_free_user_fact_blocked: bool = False
    expected_current_event_assertion_forbidden: bool = True
    expected_overclaim_count: int = 0
    expected_template_skeleton_repeat_count: int = 0
    min_sentence_count: int = 2
    max_sentence_count: int = 5
    required_observation_roles: tuple[str, ...] = ()

    def as_registry_item(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "fixture_group": self.fixture_group,
            "coverage_group": self.fixture_group,
            "subscription_tier": self.subscription_tier,
            "plan": self.subscription_tier,
            "expected_observation_reply_kind": self.expected_observation_reply_kind,
            "expected_eligibility_status": self.expected_eligibility_status,
            "expected_question_required": self.expected_question_required,
            "expected_unknown_slots": list(self.expected_unknown_slots),
            "expected_user_fact_grounding_mode": self.expected_user_fact_grounding_mode,
            "expected_facts_used": _safe_fact_refs(self.expected_facts_used),
            "expected_facts_ignored": _safe_fact_refs(self.expected_facts_ignored),
            "expected_surface_disclosure_required": self.expected_surface_disclosure_required,
            "expected_surface_disclosure_forbidden": self.expected_surface_disclosure_forbidden,
            "expected_free_user_fact_blocked": self.expected_free_user_fact_blocked,
            "expected_current_event_assertion_forbidden": self.expected_current_event_assertion_forbidden,
            "expected_overclaim_count": self.expected_overclaim_count,
            "expected_template_skeleton_repeat_count": self.expected_template_skeleton_repeat_count,
            "min_sentence_count": self.min_sentence_count,
            "max_sentence_count": self.max_sentence_count,
            "required_observation_roles": list(self.required_observation_roles),
            "expected_observation_roles": list(self.required_observation_roles),
            "exact_comment_text_locked": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "display_gate_relaxed": False,
            "fixed_fallback_used": False,
            "external_ai_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }


OBSERVATION_REGRESSION_FIXTURES: Final = (
    ObservationRegressionFixture(
        fixture_id="step13_short_low_info_fatigue",
        fixture_group=FIXTURE_GROUP_SHORT_LOW_INFORMATION,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        expected_unknown_slots=(UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_CURRENT_FEELING_TARGET, UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_DESIRED_DIRECTION, UNKNOWN_SLOT_RELATION),
        expected_question_required=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_short_low_info_unspecified_no",
        fixture_group=FIXTURE_GROUP_SHORT_LOW_INFORMATION,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        expected_unknown_slots=(UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_CURRENT_FEELING_TARGET, UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_DESIRED_DIRECTION, UNKNOWN_SLOT_RELATION),
        expected_question_required=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_short_low_info_yabai",
        fixture_group=FIXTURE_GROUP_SHORT_LOW_INFORMATION,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        expected_unknown_slots=(UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_CURRENT_FEELING_TARGET, UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_DESIRED_DIRECTION, UNKNOWN_SLOT_RELATION),
        expected_question_required=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_long_low_info_vague_reference",
        fixture_group=FIXTURE_GROUP_LONG_LOW_INFORMATION,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        expected_unknown_slots=(UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_RELATION),
        expected_question_required=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_short_eligible_environment_blocked",
        fixture_group=FIXTURE_GROUP_SHORT_ELIGIBLE,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        required_observation_roles=("empathy", "input_arrangement", "state_verbalization"),
        min_sentence_count=2,
        max_sentence_count=3,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_standard_eligible_change_stuck_fatigue",
        fixture_group=FIXTURE_GROUP_STANDARD_ELIGIBLE,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        required_observation_roles=("empathy", "input_arrangement", "state_verbalization", "companion_close"),
        min_sentence_count=3,
        max_sentence_count=4,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_subscription_explicit_fact_environment",
        fixture_group=FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT,
        subscription_tier="premium",
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        expected_user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        expected_facts_used=({"fact_id": "uf_environment_change_wish", "source_kind": "user_dictionary", "mode": USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE},),
        expected_surface_disclosure_required=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_subscription_implicit_fact_focus",
        fixture_group=FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT,
        subscription_tier="premium",
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        expected_user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
        expected_facts_used=({"fact_id": "uf_repeated_environment_weight", "source_kind": "user_dictionary", "mode": USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS},),
        expected_surface_disclosure_forbidden=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_free_user_fact_block_same_input",
        fixture_group=FIXTURE_GROUP_FREE_USER_FACT_BLOCK,
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        expected_unknown_slots=(UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_RELATION),
        expected_question_required=True,
        expected_user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_DISABLED,
        expected_facts_ignored=({"fact_id": "uf_environment_change_wish", "source_kind": "user_dictionary", "mode": USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE},),
        expected_free_user_fact_blocked=True,
    ),
    ObservationRegressionFixture(
        fixture_id="step13_overclaim_inducing_many_facts",
        fixture_group=FIXTURE_GROUP_OVERCLAIM_INDUCING,
        subscription_tier="premium",
        expected_observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        expected_eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        expected_unknown_slots=(UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_RELATION),
        expected_question_required=True,
        expected_user_fact_grounding_mode=USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
        expected_facts_used=(
            {"fact_id": "uf_environment_change_wish", "source_kind": "user_dictionary", "mode": USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS},
            {"fact_id": "uf_repeated_work_fatigue", "source_kind": "user_dictionary", "mode": USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS},
            {"fact_id": "uf_relationship_burden", "source_kind": "user_dictionary", "mode": USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS},
        ),
        expected_current_event_assertion_forbidden=True,
    ),
)


def iter_observation_regression_fixtures(*, groups: Sequence[str] | Iterable[str] | None = None) -> tuple[ObservationRegressionFixture, ...]:
    allowed = set(_dedupe(groups)) if groups is not None else None
    return tuple(fixture for fixture in OBSERVATION_REGRESSION_FIXTURES if allowed is None or fixture.fixture_group in allowed)


def _definition_fixture_by_group() -> dict[str, ObservationRegressionFixture]:
    by_group: dict[str, ObservationRegressionFixture] = {}
    for fixture in OBSERVATION_REGRESSION_FIXTURES:
        by_group.setdefault(fixture.fixture_group, fixture)
    return by_group


def build_observation_regression_fixture_definitions() -> list[dict[str, Any]]:
    by_group = _definition_fixture_by_group()
    definitions: list[dict[str, Any]] = []
    for group in OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS:
        item = by_group[group].as_registry_item()
        if group in {FIXTURE_GROUP_SHORT_LOW_INFORMATION, FIXTURE_GROUP_LONG_LOW_INFORMATION, FIXTURE_GROUP_OVERCLAIM_INDUCING}:
            item["expected_observation_roles"] = ["low_info_receive", "low_info_known_scope", "low_info_question"]
        elif not item.get("expected_observation_roles"):
            item["expected_observation_roles"] = list(item.get("required_observation_roles") or [])
        item.update(
            {
                "version": OBSERVATION_REGRESSION_FIXTURE_DEFINITIONS_VERSION,
                "schema_version": OBSERVATION_REGRESSION_FIXTURE_DEFINITIONS_VERSION,
                "source_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
            }
        )
        assert_observation_regression_fixture_coverage_contract(item, allow_partial=True)
        definitions.append(item)
    return definitions


def build_observation_regression_fixture_registry(*, include_input_text: bool = False) -> dict[str, Any]:
    # include_input_text is intentionally ignored.  Step13 artifacts stay meta-only.
    fixtures = [fixture.as_registry_item() for fixture in OBSERVATION_REGRESSION_FIXTURES]
    covered_groups = _dedupe(item["fixture_group"] for item in fixtures)
    missing_groups = [group for group in OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS if group not in covered_groups]
    registry = {
        "version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "schema_version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "source_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "required_fixture_groups": list(OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS),
        "covered_fixture_groups": covered_groups,
        "missing_fixture_groups": missing_groups,
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
        "exact_comment_text_locked": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_observation_regression_fixture_coverage_contract(registry, allow_partial=True)
    return registry


def build_observation_regression_fixture_coverage_summary() -> dict[str, Any]:
    registry = build_observation_regression_fixture_registry()
    counts = {group: 0 for group in OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS}
    for fixture in registry["fixtures"]:
        counts[fixture["fixture_group"]] = counts.get(fixture["fixture_group"], 0) + 1
    summary = {
        "version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "schema_version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "source_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step13_regression_fixture_coverage_ready": not registry["missing_fixture_groups"],
        "required_fixture_groups": list(OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS),
        "covered_fixture_groups": registry["covered_fixture_groups"],
        "missing_fixture_groups": registry["missing_fixture_groups"],
        "fixture_count": registry["fixture_count"],
        "group_counts": counts,
        "short_low_information_examples_present": counts.get(FIXTURE_GROUP_SHORT_LOW_INFORMATION, 0) >= 3,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "exact_comment_text_locked": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
    }
    assert_observation_regression_fixture_coverage_contract(summary, allow_partial=True)
    return summary


def build_observation_regression_fixture_suite(*, include_input_text: bool = False) -> dict[str, Any]:
    registry = build_observation_regression_fixture_registry(include_input_text=include_input_text)
    registry.update(
        {
            "version": OBSERVATION_REGRESSION_FIXTURE_SUITE_VERSION,
            "schema_version": OBSERVATION_REGRESSION_FIXTURE_SUITE_VERSION,
            "fixture_suite_ready": not registry["missing_fixture_groups"],
            "step13_regression_fixture_coverage_ready": not registry["missing_fixture_groups"],
            "scorecard_event_projection_available": True,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
    )
    assert_observation_regression_fixture_coverage_contract(registry, allow_partial=True)
    return registry


def fixture_by_coverage_group(group: str, *, suite: Mapping[str, Any] | None = None) -> dict[str, Any]:
    data = dict(suite or build_observation_regression_fixture_suite())
    fixtures = data.get("fixtures") or build_observation_regression_fixture_registry().get("fixtures") or []
    for item in fixtures:
        if isinstance(item, Mapping) and _clean(item.get("fixture_group") or item.get("coverage_group")) == group:
            return dict(item)
    return {}


def build_observation_regression_fixture_scorecard_event(
    fixture: ObservationRegressionFixture | Mapping[str, Any],
    *,
    observed_meta: Mapping[str, Any] | Any | None = None,
    observation_status: str = "passed",
    comment_text_present: bool = True,
    display_confirmed: bool | None = None,
    reasons: Sequence[str] | None = None,
    surface_signature_family_key: str | None = None,
) -> dict[str, Any]:
    item = fixture.as_registry_item() if isinstance(fixture, ObservationRegressionFixture) else dict(fixture)
    meta = _meta(observed_meta)
    expected_kind = _clean(item.get("expected_observation_reply_kind")) or _expected_kind_for_group(_clean(item.get("fixture_group")))
    actual_kind = _clean(meta.get("observation_reply_kind")) or expected_kind
    actual_status = _clean(meta.get("eligibility_status")) or _expected_status_from_kind(actual_kind)
    user_fact_mode = _clean(meta.get("user_fact_grounding_mode") or item.get("expected_user_fact_grounding_mode")) or USER_FACT_GROUNDING_MODE_DISABLED
    facts_used = _safe_fact_refs(meta.get("facts_used") or item.get("expected_facts_used"))
    event = {
        "version": OBSERVATION_REGRESSION_FIXTURE_EVENT_VERSION,
        "source_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "fixture_id": _clean(item.get("fixture_id")),
        "row_id": _clean(item.get("fixture_id")),
        "coverage_group": _clean(item.get("fixture_group")),
        "fixture_group": _clean(item.get("fixture_group")),
        "observation_status": observation_status,
        "comment_text_present": bool(comment_text_present),
        "passed_body_returned": observation_status == "passed" and bool(comment_text_present),
        "display_confirmed": bool(comment_text_present if display_confirmed is None else display_confirmed),
        "passed_display_count": 1 if observation_status == "passed" and bool(comment_text_present) else 0,
        "observation_reply_meta": {
            "observation_reply_kind": actual_kind,
            "eligibility_status": actual_status,
            "eligible_for_full_observation": actual_kind == OBSERVATION_REPLY_KIND_ELIGIBLE,
            "question_required": bool(meta.get("question_required", item.get("expected_question_required", False))),
            "unknown_slots": _dedupe(meta.get("unknown_slots") or item.get("expected_unknown_slots")),
            "user_fact_grounding_mode": user_fact_mode,
            "facts_used": facts_used,
            "plan": _clean(item.get("subscription_tier") or item.get("plan") or "free"),
            "subscription_tier": _clean(item.get("subscription_tier") or item.get("plan") or "free"),
            "user_fact_may_promote_to_eligible": False,
            "free_user_fact_blocked": bool(meta.get("free_user_fact_blocked", item.get("expected_free_user_fact_blocked", False))),
            "surface_disclosure_required": bool(
                meta.get("surface_disclosure_required", item.get("expected_surface_disclosure_required", False))
            ),
            "surface_disclosure_forbidden": bool(
                meta.get("surface_disclosure_forbidden", item.get("expected_surface_disclosure_forbidden", False))
            ),
            "must_not_assert_current_event_from_user_fact": True,
        },
        "expected_observation_reply_kind": expected_kind,
        "expected_eligibility_status": _expected_status_from_kind(expected_kind),
        "plan": _clean(item.get("subscription_tier") or item.get("plan") or "free"),
        "user_fact_grounding_mode": user_fact_mode,
        "facts_used": facts_used,
        "surface_disclosure_required": bool(
            meta.get("surface_disclosure_required", item.get("expected_surface_disclosure_required", False))
        ),
        "surface_disclosure_forbidden": bool(
            meta.get("surface_disclosure_forbidden", item.get("expected_surface_disclosure_forbidden", False))
        ),
        "top_rejection_reasons": list(reasons or []),
        "surface_signature_family_key": surface_signature_family_key or f"step13:{item.get('fixture_group')}:{item.get('fixture_id')}",
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
    }
    assert_observation_regression_fixture_coverage_contract(event, allow_partial=True)
    return event


def build_observation_regression_fixture_scorecard_events(
    fixtures: Sequence[ObservationRegressionFixture] | Iterable[ObservationRegressionFixture] | None = None,
    *,
    observed_meta_by_fixture_id: Mapping[str, Mapping[str, Any] | Any] | None = None,
) -> list[dict[str, Any]]:
    observed = observed_meta_by_fixture_id or {}
    return [build_observation_regression_fixture_scorecard_event(fixture, observed_meta=observed.get(fixture.fixture_id)) for fixture in list(fixtures or OBSERVATION_REGRESSION_FIXTURES)]


def _expected_kind_for_event_group(group: str, event: Mapping[str, Any], actual_kind: str) -> str:
    if group == FIXTURE_GROUP_FREE_USER_FACT_BLOCK:
        return actual_kind or _clean(event.get("expected_observation_reply_kind")) or OBSERVATION_REPLY_KIND_LOW_INFORMATION
    return _expected_kind_for_group(group) or _clean(event.get("expected_observation_reply_kind"))


def normalize_observation_regression_fixture_event(event: Mapping[str, Any] | None) -> dict[str, Any]:
    if _contains_text_payload_key(event or {}):
        raise ValueError("Step13 fixture event must not include raw input or comment_text payload keys")
    data = dict(event or {})
    group = _clean(data.get("fixture_group") or data.get("observation_fixture_group") or data.get("coverage_group"))
    meta = _event_meta(data)
    actual_kind = _clean(meta.get("observation_reply_kind") or data.get("observation_reply_kind"))
    if not actual_kind:
        actual_kind = _clean(data.get("expected_observation_reply_kind")) or _expected_kind_for_group(group)
    actual_status = _clean(meta.get("eligibility_status") or data.get("eligibility_status")) or _expected_status_from_kind(actual_kind)
    expected_kind = _expected_kind_for_event_group(group, data, actual_kind)
    expected_status = _expected_status_from_kind(expected_kind)
    passed_body = _event_passed_body(data)
    question_required = bool(meta.get("question_required") is True or data.get("question_required") is True)
    unknown_slots = _dedupe(meta.get("unknown_slots") or data.get("unknown_slots"))
    facts_used = _safe_fact_refs(data.get("facts_used") or meta.get("facts_used"))
    user_fact_mode = _clean(data.get("user_fact_grounding_mode") or meta.get("user_fact_grounding_mode") or USER_FACT_GROUNDING_MODE_DISABLED)
    reasons: list[str] = []
    if not group or group not in OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS:
        reasons.append("unsupported_fixture_group")
    if not passed_body:
        reasons.append("passed_body_missing")
    if actual_kind != expected_kind:
        reasons.append("reply_kind_mismatch")
    if actual_status != expected_status:
        reasons.append("eligibility_status_mismatch")
    if expected_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        if not question_required:
            reasons.append("low_information_question_missing")
        if not unknown_slots:
            reasons.append("low_information_unknown_slots_missing")
        if data.get("eligible_for_full_observation") is True or meta.get("eligible_for_full_observation") is True:
            reasons.append("false_eligible")
        if data.get("user_fact_may_promote_to_eligible") is True or meta.get("user_fact_may_promote_to_eligible") is True:
            reasons.append("low_info_user_fact_promotion_allowed")
    if expected_kind == OBSERVATION_REPLY_KIND_ELIGIBLE:
        if meta.get("eligible_for_full_observation") is not True and data.get("eligible_for_full_observation") is not True:
            reasons.append("eligible_for_full_observation_missing")
    if group == FIXTURE_GROUP_FREE_USER_FACT_BLOCK:
        if facts_used or data.get("free_user_fact_violation") is True or meta.get("free_user_fact_violation") is True:
            reasons.append("free_fixture_facts_used")
        if user_fact_mode != USER_FACT_GROUNDING_MODE_DISABLED:
            reasons.append("free_fixture_user_fact_mode_not_disabled")
    if group == FIXTURE_GROUP_SUBSCRIPTION_EXPLICIT_FACT:
        if user_fact_mode != USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE:
            reasons.append("explicit_user_fact_mode_missing")
        if not facts_used:
            reasons.append("explicit_user_fact_facts_used_missing")
        if meta.get("surface_disclosure_required") is not True and data.get("surface_disclosure_required") is not True:
            reasons.append("explicit_user_fact_surface_disclosure_missing")
    if group == FIXTURE_GROUP_SUBSCRIPTION_IMPLICIT_FACT:
        if user_fact_mode != USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS:
            reasons.append("implicit_user_fact_mode_missing")
        if not facts_used:
            reasons.append("implicit_user_fact_facts_used_missing")
        if meta.get("surface_disclosure_required") is True or data.get("surface_disclosure_required") is True:
            reasons.append("implicit_user_fact_surface_disclosure_unexpected")
    if data.get("assert_current_event_from_user_fact") is True or meta.get("assert_current_event_from_user_fact") is True or data.get("unsupported_current_event_assertion") is True:
        reasons.append("overclaim_detected")
    if _as_int(data.get("overclaim_count")) > 0 or _as_int(meta.get("overclaim_count")) > 0:
        reasons.append("overclaim_detected")
    if _as_int(data.get("template_skeleton_repeat_count")) > 0 or _as_int(meta.get("template_skeleton_repeat_count")) > 0:
        reasons.append("template_skeleton_repeat_detected")
    for flag in ("display_gate_relaxed", "public_status_extended", "rn_visible_contract_changed", "fixed_fallback_used", "external_ai_used", "local_llm_used"):
        if data.get(flag) is True:
            reasons.append(flag)
    reasons = _dedupe(reasons)
    false_eligible = expected_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and actual_kind == OBSERVATION_REPLY_KIND_ELIGIBLE
    normalized = {
        "version": OBSERVATION_REGRESSION_FIXTURE_EVENT_VERSION,
        "source_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "fixture_id": _clean(data.get("fixture_id") or data.get("row_id") or data.get("trace_id")),
        "fixture_group": group,
        "coverage_group": group,
        "expected_observation_reply_kind": expected_kind,
        "expected_eligibility_status": expected_status,
        "actual_observation_reply_kind": actual_kind,
        "actual_eligibility_status": actual_status,
        "observation_status": _clean(data.get("observation_status") or data.get("backend_observation_status")),
        "plan": _clean(data.get("plan") or meta.get("plan") or data.get("subscription_tier") or "free"),
        "passed_body_returned": passed_body,
        "always_display_success": passed_body,
        "eligible_observation_success": expected_kind == OBSERVATION_REPLY_KIND_ELIGIBLE and actual_kind == OBSERVATION_REPLY_KIND_ELIGIBLE and passed_body,
        "low_info_observation_success": expected_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and actual_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and passed_body,
        "false_eligible": false_eligible,
        "free_user_fact_violation": any(reason in reasons for reason in ("free_fixture_facts_used", "free_fixture_user_fact_mode_not_disabled")),
        "overclaim": "overclaim_detected" in reasons,
        "template_skeleton_repeat": "template_skeleton_repeat_detected" in reasons,
        "failure_reasons": reasons,
        "fixture_failure_reasons": reasons,
        "fixture_expectation_passed": not reasons,
        "passed": not reasons,
        "question_required": question_required,
        "unknown_slots": unknown_slots,
        "user_fact_grounding_mode": user_fact_mode,
        "facts_used_count": len(facts_used),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "rn_visible_contract_changed": False,
    }
    assert_observation_regression_fixture_coverage_contract(normalized, allow_partial=True)
    return normalized


def build_observation_regression_fixture_coverage(
    fixture_results: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    *,
    suite: Mapping[str, Any] | None = None,
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    scorecard_events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    raw_events = list(fixture_results or []) + list(events or []) + list(scorecard_events or [])
    fixture_events = [event for event in raw_events if isinstance(event, Mapping) and _clean(event.get("fixture_group") or event.get("observation_fixture_group") or event.get("coverage_group")) in OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS]
    normalized = [normalize_observation_regression_fixture_event(event) for event in fixture_events]
    required_groups = list((suite or {}).get("required_fixture_groups") or OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS)
    observed_groups = _dedupe(event.get("fixture_group") for event in normalized if event.get("fixture_group"))
    missing_groups = [group for group in required_groups if group not in observed_groups]
    failure_events = [event for event in normalized if event.get("fixture_expectation_passed") is not True]
    expected_eligible = [event for event in normalized if event.get("expected_observation_reply_kind") == OBSERVATION_REPLY_KIND_ELIGIBLE]
    expected_low = [event for event in normalized if event.get("expected_observation_reply_kind") == OBSERVATION_REPLY_KIND_LOW_INFORMATION]
    false_eligible_count = sum(1 for event in normalized if event.get("false_eligible") is True)
    free_user_fact_violation_count = sum(1 for event in normalized if event.get("free_user_fact_violation") is True)
    overclaim_count = sum(1 for event in normalized if event.get("overclaim") is True)
    template_repeat_count = sum(1 for event in normalized if event.get("template_skeleton_repeat") is True)
    by_group: dict[str, dict[str, Any]] = {}
    for group in required_groups:
        group_events = [event for event in normalized if event.get("fixture_group") == group]
        failures = _dedupe(reason for event in group_events for reason in (event.get("fixture_failure_reasons") or []))
        by_group[group] = {"fixture_group": group, "event_count": len(group_events), "passed": bool(group_events and not failures), "failure_reasons": failures}
    failure_reason_counts: dict[str, int] = {}
    for event in failure_events:
        for reason in event.get("fixture_failure_reasons") or []:
            failure_reason_counts[reason] = failure_reason_counts.get(reason, 0) + 1
    release_blockers: list[str] = []
    if not normalized:
        release_blockers.append("observation_regression_fixture_events_missing")
    if missing_groups:
        release_blockers.append("observation_regression_fixture_groups_missing")
    if failure_events:
        release_blockers.append("observation_regression_fixture_groups_failed")
    if false_eligible_count:
        release_blockers.append("false_eligible_detected")
    if free_user_fact_violation_count:
        release_blockers.append("free_user_fact_violation_detected")
    if overclaim_count:
        release_blockers.append("overclaim_detected")
    if template_repeat_count:
        release_blockers.append("template_skeleton_repeat_detected")
    ready = bool(normalized and not missing_groups and not failure_events and false_eligible_count == 0 and free_user_fact_violation_count == 0 and overclaim_count == 0 and template_repeat_count == 0)
    pass_count = sum(1 for event in normalized if event.get("fixture_expectation_passed") is True)
    report = {
        "version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "schema_version": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "source_step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step": OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "run_id": _clean(run_id),
        "fixture_coverage_ready": ready,
        "step13_regression_fixture_coverage_ready": ready,
        "observation_regression_fixture_coverage_ready": ready,
        "required_fixture_groups": required_groups,
        "observed_fixture_groups": observed_groups,
        "covered_fixture_groups": observed_groups,
        "missing_fixture_groups": missing_groups,
        "failed_fixture_groups": _dedupe(event.get("fixture_group") for event in failure_events),
        "fixture_event_count": len(normalized),
        "fixture_pass_count": pass_count,
        "fixture_failure_count": len(failure_events),
        "required_fixture_group_count": len(required_groups),
        "observed_required_fixture_group_count": len([group for group in observed_groups if group in required_groups]),
        "fixture_coverage_rate": _rate(len([group for group in required_groups if group in observed_groups]), len(required_groups)),
        "fixture_pass_rate": _rate(pass_count, len(normalized)),
        "fixture_success_coverage_rate": _rate(pass_count, len(normalized)),
        "always_display_rate": _rate(sum(1 for event in normalized if event.get("always_display_success") is True), len(normalized)),
        "eligible_observation_rate": _rate(sum(1 for event in expected_eligible if event.get("eligible_observation_success") is True), len(expected_eligible)),
        "low_info_observation_rate": _rate(sum(1 for event in expected_low if event.get("low_info_observation_success") is True), len(expected_low)),
        "false_eligible_count": false_eligible_count,
        "free_user_fact_violation_count": free_user_fact_violation_count,
        "overclaim_count": overclaim_count,
        "template_skeleton_repeat_count": template_repeat_count,
        "failure_reason_counts": failure_reason_counts,
        "by_fixture_group": by_group,
        "events": normalized,
        "release_blockers": _dedupe(release_blockers),
        "qa_gaps": _dedupe(release_blockers),
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "rn_visible_contract_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "fixed_fallback_used": False,
        "external_ai_used": False,
    }
    assert_observation_regression_fixture_coverage_contract(report, allow_partial=True)
    return report


def build_observation_regression_fixture_coverage_report(
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    *,
    suite: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    return build_observation_regression_fixture_coverage(events=events, suite=suite, run_id=run_id)


def aggregate_observation_regression_fixture_coverage(
    events: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    return build_observation_regression_fixture_coverage(events=events)


def normalize_observation_regression_fixture_coverage_to_scorecard_fields(report: Mapping[str, Any] | None) -> dict[str, Any]:
    data = dict(report or {})
    return {
        "observation_regression_fixture_coverage_version": _clean(data.get("version")) or OBSERVATION_REGRESSION_FIXTURE_COVERAGE_VERSION,
        "observation_regression_fixture_coverage_step": _clean(data.get("step")) or OBSERVATION_REGRESSION_FIXTURE_COVERAGE_STEP,
        "step13_regression_fixture_coverage_ready": bool(data.get("step13_regression_fixture_coverage_ready") or data.get("fixture_coverage_ready")),
        "step13_observation_regression_fixture_coverage_ready": bool(data.get("step13_regression_fixture_coverage_ready") or data.get("fixture_coverage_ready")),
        "observation_regression_fixture_coverage_ready": bool(data.get("observation_regression_fixture_coverage_ready") or data.get("fixture_coverage_ready")),
        "observation_regression_required_fixture_group_count": data.get("required_fixture_group_count", len(OBSERVATION_REGRESSION_REQUIRED_FIXTURE_GROUPS)),
        "observation_regression_observed_required_fixture_group_count": data.get("observed_required_fixture_group_count", 0),
        "observation_regression_missing_fixture_groups": list(data.get("missing_fixture_groups") or []),
        "observation_regression_observed_fixture_groups": list(data.get("observed_fixture_groups") or []),
        "observation_regression_failed_fixture_groups": list(data.get("failed_fixture_groups") or []),
        "observation_regression_fixture_failure_count": data.get("fixture_failure_count", 0),
        "observation_regression_fixture_coverage_rate": data.get("fixture_coverage_rate", 0.0),
        "observation_regression_fixture_success_coverage_rate": data.get("fixture_success_coverage_rate", data.get("fixture_pass_rate", 0.0)),
        "observation_regression_fixture_pass_rate": data.get("fixture_pass_rate", 0.0),
        "observation_regression_fixture_release_blockers": list(data.get("release_blockers") or []),
        "observation_regression_release_blockers": list(data.get("release_blockers") or []),
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def assert_observation_regression_fixture_coverage_contract(
    payload: Mapping[str, Any] | None,
    *,
    allow_fixture_text: bool = False,
    allow_partial: bool = True,
) -> None:
    data = dict(payload or {})
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"Step13 regression fixture coverage must not set {flag}=true")
    if not allow_fixture_text and _contains_text_payload_key(data):
        raise ValueError("Step13 scorecard/coverage meta must not include raw input or comment_text payload keys")
    if data.get("exact_comment_text_locked") is True:
        raise ValueError("Step13 fixtures must not lock exact comment_text")
    if not allow_partial:
        missing = data.get("missing_fixture_groups") or data.get("missing_coverage_groups")
        if isinstance(missing, Sequence) and not isinstance(missing, (str, bytes, bytearray)) and list(missing):
            raise ValueError(f"Step13 regression fixture groups missing: {list(missing)}")


def assert_observation_regression_fixture_suite_contract(suite: Mapping[str, Any] | None) -> None:
    assert_observation_regression_fixture_coverage_contract(suite, allow_partial=False)


def assert_observation_regression_fixture_coverage_report_contract(report: Mapping[str, Any] | None, *, allow_partial: bool = True) -> None:
    assert_observation_regression_fixture_coverage_contract(report, allow_partial=allow_partial)


def dump_observation_regression_fixture_coverage(payload: Mapping[str, Any] | None = None) -> str:
    source = dict(payload or build_observation_regression_fixture_coverage_summary())
    assert_observation_regression_fixture_coverage_contract(source, allow_partial=True)
    return json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


# Backward/forward compatible names for Step13 handoff tooling.
build_observation_regression_fixture_catalog = build_observation_regression_fixture_suite
build_observation_regression_scorecard_events = build_observation_regression_fixture_scorecard_events
build_observation_reply_regression_fixture_coverage = build_observation_regression_fixture_coverage
build_emlis_ai_observation_regression_fixture_coverage_summary = build_observation_regression_fixture_coverage_summary
build_emlis_ai_observation_regression_fixture_registry = build_observation_regression_fixture_registry
build_emlis_ai_observation_regression_fixture_scorecard_events = build_observation_regression_fixture_scorecard_events
build_emlis_ai_observation_regression_fixture_coverage = build_observation_regression_fixture_coverage
