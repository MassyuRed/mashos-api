# -*- coding: utf-8 -*-
from __future__ import annotations

"""Public observation surface requirement decision for EmlisAI.

PublicObservationRecovery P1 material.

The decision made here is intentionally body-free.  It decides whether a public
EmlisAI candidate must keep the labelled two-stage shape, may use a plain state
answer, or belongs to the low-information/safety/infra lane.  It does not render
text, does not add public response keys, does not relax gates, and does not use
fixture-specific wording as a runtime route.
"""

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final
import json

from emlis_ai_two_stage_applicability import build_two_stage_applicability_decision

PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.public_surface_requirement.v1"
)
PUBLIC_SURFACE_REQUIREMENT_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P1_SurfaceRequirementDecision"
)

SURFACE_REQUIREMENT_LABELLED_TWO_STAGE: Final = "labelled_two_stage"
SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER: Final = "plain_state_answer"
SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION: Final = "low_information_observation"
SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER: Final = "self_denial_safe_state_answer"
SURFACE_REQUIREMENT_SAFETY_BLOCKED: Final = "safety_blocked"
SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED: Final = "infrastructure_fail_closed"

LABELLED_TWO_STAGE_SHAPE_KIND: Final = "labelled_two_stage"
PLAIN_STATE_ANSWER_SHAPE_KIND: Final = "plain_state_answer"
LOW_INFORMATION_SHAPE_KIND: Final = "low_information_observation"
LABELLED_TWO_STAGE_OBSERVATION_MARKER: Final = "見えたこと：\n"
LABELLED_TWO_STAGE_RECEPTION_BOUNDARY: Final = "\n\nEmlisから：\n"

_SURFACE_REQUIREMENT_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
        SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
        SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
        SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
        SURFACE_REQUIREMENT_SAFETY_BLOCKED,
        SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    }
)
_LOW_INFORMATION_MATERIAL_QUALITIES: Final[frozenset[str]] = frozenset(
    {"low_information"}
)
_LIMITED_GROUNDING_MATERIAL_QUALITIES: Final[frozenset[str]] = frozenset(
    {"limited_grounding"}
)
_HIGH_INFORMATION_QUALITY_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "eligible",
        "normal",
        "rich",
        "high",
        "sufficient",
        "sufficient_input_material",
        "structure_question",
        "long_meaning_arc",
    }
)
_TWO_STAGE_FIXTURE_FAMILY_MARKERS: Final[tuple[str, ...]] = (
    "phase17",
    "phase19",
    "product_visible",
    "two_stage",
    "labelled_two_stage",
)
_TWO_STAGE_REASON_MARKERS: Final[tuple[str, ...]] = (
    "self_understanding",
    "structure_question",
    "long_meaning_arc",
    "relation_boundary",
    "relationship_boundary",
    "required_structure",
    "strict_structure_family",
    "two_stage",
    "labelled_two_stage",
    "product_visible",
)
_SOURCE_UNAVAILABLE_REASON_MARKERS: Final[tuple[str, ...]] = (
    "source_unavailable",
    "composer_source_unavailable",
    "complete_initial_surface_unavailable",
    "limited_composer_shallow_empty_candidate",
    "sentence_plan_unavailable",
)
_P4_3_RICH_VISIBLE_LOW_INFO_BOUNDARY_SOURCE: Final = (
    "rich_visible_material_low_information_surface_boundary"
)
_P4_3_SOURCE_UNAVAILABLE_BOUNDARY_SOURCE: Final = (
    "source_unavailable_high_information_surface_boundary"
)
_RICH_VISIBLE_EVENTISH_SLOTS: Final[frozenset[str]] = frozenset({"event", "action", "time"})
_RICH_VISIBLE_REACTIONISH_SLOTS: Final[frozenset[str]] = frozenset(
    {"emotion_direction", "unresolved_weight"}
)
_RICH_VISIBLE_MEANING_SLOTS: Final[frozenset[str]] = frozenset(
    {"relationship", "target", "change", "value"}
)
_RICH_VISIBLE_RELATION_MATERIAL_IDS: Final[frozenset[str]] = frozenset(
    {
        "relationship_end",
        "support_from_other",
        "gratitude_or_return_intent",
        "relationship_material",
        "support_received_material",
        "boundary_or_transition",
        "future_intention",
        "self_observation",
        "value_or_self_understanding_material",
        "self_understanding_learning",
        "small_change_preservation",
        "value_preservation",
    }
)
_RELATIONSHIP_TRANSITION_VISIBLE_SLOT_MARKERS: Final[frozenset[str]] = frozenset(
    {"relationship", "action", "change", "value", "target"}
)
_RELATIONSHIP_TRANSITION_ACTION_SLOT_MARKERS: Final[frozenset[str]] = frozenset(
    {"action", "target"}
)
_RELATIONSHIP_TRANSITION_MEANING_SLOT_MARKERS: Final[frozenset[str]] = frozenset(
    {"change", "value"}
)
_RELATIONSHIP_TRANSITION_MATERIAL_IDS: Final[frozenset[str]] = frozenset(
    {
        "relationship_end",
        "support_from_other",
        "gratitude_or_return_intent",
        "boundary_or_transition",
        "future_intention",
        "relationship_material",
        "support_received_material",
    }
)
_TWO_STAGE_META_TRUE_KEYS: Final[tuple[str, ...]] = (
    "two_stage_required",
    "two_stage_reception_gate_required",
    "state_answer_two_stage_display_required",
    "state_answer_two_stage_reception_surface_required",
    "state_answer_joined_comment_text_required",
    "state_answer_section_labels_required",
    "two_stage_display_required",
    "two_stage_reception_surface_required",
    "joined_comment_text_required",
    "section_labels_required",
    "two_stage_section_surface_plan_required",
)
_TWO_STAGE_META_SHAPE_KEYS: Final[tuple[str, ...]] = (
    "state_answer_expected_comment_text_shape",
    "expected_comment_text_shape",
)
_INFRASTRUCTURE_REASON_MARKERS: Final[tuple[str, ...]] = (
    "timeout",
    "exception",
    "infrastructure_error",
    "reply_timeout_or_error",
)
_SAFETY_REASON_MARKERS: Final[tuple[str, ...]] = (
    "safety_blocked",
    "requires_block",
    "emergency",
    "self_harm",
    "medical",
    "legal",
)
_BODY_FORBIDDEN_EXACT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
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
        "candidateCommentText",
        "public_comment_text",
        "publicCommentText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "body",
        "text",
        "surface_text",
        "surfaceText",
        "evidence_text",
        "evidenceText",
    }
)
_PUBLIC_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "public_response_key_added",
    "rn_visible_contract_changed",
    "response_shape_changed",
    "api_route_changed",
    "db_physical_name_changed",
)
_GATE_POLICY_KEYS: Final[tuple[str, ...]] = (
    "display_gate_relaxed",
    "runtime_surface_gate_relaxed",
    "visible_surface_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "safety_gate_relaxed",
)
_REQUIRED_DECISION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "surface_requirement_family",
        "two_stage_required",
        "plain_state_answer_allowed",
        "low_information_allowed",
        "required_comment_text_shape",
        "decision_sources",
        "material_quality_family",
        "input_material_classification",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
        "public_contract",
        "gate_policy",
    }
)
_REQUIRED_SHAPE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "kind",
        "starts_with",
        "contains_boundary",
        "labels_required",
        "observation_section_required",
        "reception_section_required",
        "comment_text_body_included",
    }
)
_REQUIRED_CLASSIFICATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "memo_present",
        "memo_action_present",
        "emotions_present",
        "categories_present",
        "memo_text_len",
        "memo_action_text_len",
        "high_information_input",
        "low_information_material",
        "body_free",
        "raw_input_included",
        "comment_text_body_included",
    }
)


def resolve_public_surface_requirement(
    *,
    current_input: Mapping[str, Any] | None = None,
    material_route: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    fixture_family_meta: Mapping[str, Any] | None = None,
    comment_text_present: bool | None = None,
    p4_3_boundary_correction_enabled: bool = True,
) -> dict[str, Any]:
    """Decide the public surface family before public candidate adoption.

    The returned mapping is safe to place in internal/public-safe diagnostics: it
    keeps only booleans, small identifiers, counts, and contract flags.
    """

    route_meta = _material_route_meta(material_route)
    current = _as_mapping(current_input)
    composer = _as_mapping(composer_meta)
    diagnostic = _as_mapping(diagnostic_summary)
    fixture = _as_mapping(fixture_family_meta)
    containers = _containers(route_meta, composer, diagnostic, fixture)

    material_quality = _material_quality_family(route_meta, composer, diagnostic, fixture)
    input_classification = _input_material_classification(
        current_input=current,
        material_quality=material_quality,
        route_meta=route_meta,
    )
    reason_codes = _reason_codes(containers)

    safety_blocked = _safety_required(containers, reason_codes=reason_codes)
    infrastructure_fail_closed = _infrastructure_failed(containers, reason_codes=reason_codes)
    self_denial_safe_answer = _self_denial_safe_state_answer(containers)
    limited_grounding_requested = _limited_grounding_requested(material_quality=material_quality)
    rich_visible_low_information_boundary = _rich_visible_low_information_boundary_required(
        enabled=p4_3_boundary_correction_enabled,
        material_quality=material_quality,
        input_classification=input_classification,
        route_meta=route_meta,
        containers=containers,
    )
    low_information_requested = False if rich_visible_low_information_boundary else _low_information_requested(
        material_quality=material_quality,
        containers=containers,
    )

    two_stage_decision = _two_stage_applicability_decision(
        composer_meta=composer,
        route_meta=route_meta,
        diagnostic_summary=diagnostic,
        fixture_family_meta=fixture,
        comment_text_present=bool(comment_text_present),
    )
    explicit_two_stage = _explicit_two_stage_required(containers)
    fixture_two_stage = _fixture_requires_two_stage(fixture)
    high_information_two_stage = _high_information_two_stage_required(
        input_classification=input_classification,
        material_quality=material_quality,
        containers=containers,
        reason_codes=reason_codes,
    )
    source_unavailable_high_information_boundary = _source_unavailable_high_information_boundary_required(
        enabled=p4_3_boundary_correction_enabled,
        input_classification=input_classification,
        material_quality=material_quality,
        containers=containers,
        reason_codes=reason_codes,
        rich_visible_low_information_boundary=rich_visible_low_information_boundary,
        low_information_requested=low_information_requested,
    )
    material_relationship_transition_two_stage = (
        False
        if self_denial_safe_answer
        else _material_relationship_transition_two_stage_required(
            input_classification=input_classification,
            material_quality=material_quality,
            route_meta=route_meta,
            containers=containers,
        )
    )
    two_stage_required = bool(
        not safety_blocked
        and not infrastructure_fail_closed
        and not self_denial_safe_answer
        and not low_information_requested
        and (
            limited_grounding_requested
            or explicit_two_stage
            or fixture_two_stage
            or bool(two_stage_decision.get("required"))
            or high_information_two_stage
            or source_unavailable_high_information_boundary
            or rich_visible_low_information_boundary
            or material_relationship_transition_two_stage
        )
    )

    if safety_blocked:
        family = SURFACE_REQUIREMENT_SAFETY_BLOCKED
        plain_allowed = False
        low_info_allowed = False
    elif infrastructure_fail_closed:
        family = SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED
        plain_allowed = False
        low_info_allowed = False
    elif self_denial_safe_answer:
        family = SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER
        plain_allowed = False
        low_info_allowed = False
    elif limited_grounding_requested:
        family = SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
        plain_allowed = False
        low_info_allowed = False
    elif two_stage_required:
        family = SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
        plain_allowed = False
        low_info_allowed = False
    elif low_information_requested:
        family = SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
        plain_allowed = False
        low_info_allowed = True
    else:
        family = SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
        plain_allowed = True
        low_info_allowed = False

    decision_sources = _decision_sources(
        explicit_two_stage=explicit_two_stage,
        fixture_two_stage=fixture_two_stage,
        high_information_two_stage=high_information_two_stage,
        source_unavailable_high_information_boundary=source_unavailable_high_information_boundary,
        rich_visible_low_information_boundary=rich_visible_low_information_boundary,
        material_relationship_transition_two_stage=material_relationship_transition_two_stage,
        two_stage_applicability_required=bool(two_stage_decision.get("required")),
        limited_grounding_requested=limited_grounding_requested,
        low_information_requested=low_information_requested,
        safety_blocked=safety_blocked,
        infrastructure_fail_closed=infrastructure_fail_closed,
        self_denial_safe_answer=self_denial_safe_answer,
        plain_allowed=plain_allowed,
    )

    decision = {
        "schema_version": PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
        "source_phase": PUBLIC_SURFACE_REQUIREMENT_SOURCE_PHASE,
        "surface_requirement_family": family,
        "two_stage_required": bool(two_stage_required),
        "plain_state_answer_allowed": bool(plain_allowed),
        "low_information_allowed": bool(low_info_allowed),
        "required_comment_text_shape": _required_comment_text_shape(family),
        "decision_sources": decision_sources,
        "material_quality_family": material_quality,
        "input_material_classification": input_classification,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_contract": _false_public_contract(),
        "gate_policy": _false_gate_policy(),
    }
    assert_public_surface_requirement_decision(decision)
    return decision


def public_surface_requirement_public_summary(
    decision: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Return a body-free summary suitable for recovery-plan meta."""

    source = _as_mapping(decision)
    if not source:
        return {}
    summary = {
        "schema_version": _clean_identifier(source.get("schema_version"), max_length=128)
        or PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
        "source_phase": _clean_identifier(source.get("source_phase"), max_length=128)
        or PUBLIC_SURFACE_REQUIREMENT_SOURCE_PHASE,
        "surface_requirement_family": _surface_family(source.get("surface_requirement_family")),
        "two_stage_required": bool(source.get("two_stage_required")),
        "plain_state_answer_allowed": bool(source.get("plain_state_answer_allowed")),
        "low_information_allowed": bool(source.get("low_information_allowed")),
        "required_comment_text_shape": _required_comment_text_shape(source.get("surface_requirement_family")),
        "decision_sources": _dedupe(source.get("decision_sources") or []),
        "material_quality_family": _clean_identifier(source.get("material_quality_family"), max_length=96),
        "input_material_classification": _sanitize_input_material_classification(
            source.get("input_material_classification")
        ),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "public_contract": _false_public_contract(),
        "gate_policy": _false_gate_policy(),
    }
    assert_public_surface_requirement_decision(summary)
    return summary


def is_labelled_two_stage_comment_text_shape(comment_text: Any) -> bool:
    shape = labelled_two_stage_comment_text_shape_summary(comment_text)
    return bool(
        shape["labels_present"]
        and shape["label_order_valid"]
        and shape["observation_section_non_empty"]
        and shape["reception_section_non_empty"]
    )


def labelled_two_stage_comment_text_shape_summary(comment_text: Any) -> dict[str, Any]:
    body = str(comment_text or "")
    has_start = body.startswith(LABELLED_TWO_STAGE_OBSERVATION_MARKER)
    boundary_index = body.find(LABELLED_TWO_STAGE_RECEPTION_BOUNDARY)
    label_order_valid = bool(has_start and boundary_index > 0)
    observation_section = ""
    reception_section = ""
    if label_order_valid:
        observation_section = body[len(LABELLED_TWO_STAGE_OBSERVATION_MARKER):boundary_index].strip()
        reception_section = body[boundary_index + len(LABELLED_TWO_STAGE_RECEPTION_BOUNDARY):].strip()
    return {
        "labels_present": bool(has_start and boundary_index >= 0),
        "label_order_valid": bool(label_order_valid),
        "observation_section_non_empty": bool(observation_section),
        "reception_section_non_empty": bool(reception_section),
        "section_budget_checked": False,
        "comment_text_body_included": False,
    }


def assert_public_surface_requirement_decision(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("public surface requirement decision must be a mapping")
    actual_keys = set(value.keys())
    if actual_keys != set(_REQUIRED_DECISION_KEYS):
        raise ValueError(
            "public surface requirement decision key set changed: "
            f"missing={sorted(set(_REQUIRED_DECISION_KEYS) - actual_keys)} "
            f"extra={sorted(actual_keys - set(_REQUIRED_DECISION_KEYS))}"
        )
    if value.get("schema_version") != PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION:
        raise ValueError("unexpected public surface requirement schema_version")
    family = value.get("surface_requirement_family")
    if family not in _SURFACE_REQUIREMENT_FAMILIES:
        raise ValueError("unknown public surface requirement family")
    if not isinstance(value.get("two_stage_required"), bool):
        raise ValueError("two_stage_required must be boolean")
    if not isinstance(value.get("plain_state_answer_allowed"), bool):
        raise ValueError("plain_state_answer_allowed must be boolean")
    if not isinstance(value.get("low_information_allowed"), bool):
        raise ValueError("low_information_allowed must be boolean")
    if family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE:
        if value.get("two_stage_required") is not True:
            raise ValueError("labelled two-stage family must require two-stage")
        if value.get("plain_state_answer_allowed") is not False:
            raise ValueError("labelled two-stage family must not allow plain state answer")
        if value.get("low_information_allowed") is not False:
            raise ValueError("labelled two-stage family must not allow low-information surface")
    if family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
        if value.get("low_information_allowed") is not True:
            raise ValueError("low-information family must allow low-information surface")
        if value.get("plain_state_answer_allowed") is not False:
            raise ValueError("low-information family must not be plain state answer")
    shape = _require_mapping(value.get("required_comment_text_shape"), "required_comment_text_shape")
    if set(shape.keys()) != set(_REQUIRED_SHAPE_KEYS):
        raise ValueError("required_comment_text_shape key set changed")
    classification = _require_mapping(value.get("input_material_classification"), "input_material_classification")
    if set(classification.keys()) != set(_REQUIRED_CLASSIFICATION_KEYS):
        raise ValueError("input_material_classification key set changed")
    public_contract = _require_mapping(value.get("public_contract"), "public_contract")
    if set(public_contract.keys()) != set(_PUBLIC_CONTRACT_KEYS):
        raise ValueError("public_contract key set changed")
    if any(public_contract.get(key) is not False for key in _PUBLIC_CONTRACT_KEYS):
        raise ValueError("public surface requirement must not change public contract")
    gate_policy = _require_mapping(value.get("gate_policy"), "gate_policy")
    if set(gate_policy.keys()) != set(_GATE_POLICY_KEYS):
        raise ValueError("gate_policy key set changed")
    if any(gate_policy.get(key) is not False for key in _GATE_POLICY_KEYS):
        raise ValueError("public surface requirement must not relax gates")
    if value.get("body_free") is not True:
        raise ValueError("public surface requirement must be body-free")
    if value.get("raw_input_included") is not False or value.get("comment_text_body_included") is not False:
        raise ValueError("public surface requirement must not include raw/body text")
    _assert_no_forbidden_body_keys(value)
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def _two_stage_applicability_decision(
    *,
    composer_meta: Mapping[str, Any],
    route_meta: Mapping[str, Any],
    diagnostic_summary: Mapping[str, Any],
    fixture_family_meta: Mapping[str, Any],
    comment_text_present: bool,
) -> dict[str, Any]:
    try:
        return build_two_stage_applicability_decision(
            composer_meta=composer_meta,
            state_answer_surface_contract=_first_mapping(
                composer_meta,
                diagnostic_summary,
                route_meta,
                key="state_answer_surface_contract",
            ),
            state_answer_two_stage_meta=_first_mapping(
                composer_meta,
                diagnostic_summary,
                route_meta,
                key="state_answer_two_stage_meta",
            ),
            two_stage_section_surface_plan=_first_mapping(
                composer_meta,
                diagnostic_summary,
                route_meta,
                fixture_family_meta,
                key="two_stage_section_surface_plan",
            ),
            two_stage_section_plan_meta=_first_mapping(
                composer_meta,
                diagnostic_summary,
                route_meta,
                key="two_stage_section_plan_meta",
            ),
            two_stage_surface_meta=_first_mapping(
                composer_meta,
                diagnostic_summary,
                route_meta,
                key="two_stage_surface_meta",
            ),
            branch_kind=_first_text(
                fixture_family_meta.get("branch_kind"),
                diagnostic_summary.get("branch_kind"),
                composer_meta.get("branch_kind"),
            ),
            candidate_source=_first_text(
                composer_meta.get("composer_source"),
                diagnostic_summary.get("composer_source"),
            ),
            candidate_status=_first_text(
                composer_meta.get("candidate_status"),
                composer_meta.get("status"),
                diagnostic_summary.get("candidate_status"),
            ),
            comment_text_present=comment_text_present,
            explicit_required=True if _explicit_two_stage_required((composer_meta, route_meta, diagnostic_summary, fixture_family_meta)) else None,
        )
    except Exception:
        return {"required": False, "decision_reason": "two_stage_applicability_unavailable"}


def _material_quality_family(*sources: Mapping[str, Any]) -> str:
    for source in sources:
        for key in ("material_quality", "material_quality_family", "eligibility_status", "quality_family"):
            text = _clean_identifier(source.get(key), max_length=96)
            if text:
                return text
        nested = _first_mapping(source, key="input_material_summary")
        if nested:
            text = _clean_identifier(nested.get("material_quality"), max_length=96)
            if text:
                return text
    return "unknown"


def _input_material_classification(
    *,
    current_input: Mapping[str, Any],
    material_quality: str,
    route_meta: Mapping[str, Any],
) -> dict[str, Any]:
    memo = str(current_input.get("memo") or current_input.get("memo_text") or "")
    memo_action = str(current_input.get("memo_action") or "")
    emotions = (
        current_input.get("emotions")
        or current_input.get("emotion_details")
        or current_input.get("emotion")
        or ()
    )
    categories = current_input.get("category") or current_input.get("categories") or ()
    memo_len = len(memo)
    memo_action_len = len(memo_action)
    visible_slots = _visible_material_slots_from_sources(route_meta)
    relation_material_ids = _relation_material_ids_from_sources(route_meta)
    field_count = sum(
        1
        for present in (
            bool(memo.strip()),
            bool(memo_action.strip()),
            bool(_listify(emotions)),
            bool(_listify(categories)),
        )
        if present
    )
    rich_visible_material = _rich_visible_material_signal(
        visible_slots=visible_slots,
        relation_material_ids=relation_material_ids,
    )
    high_information = bool(
        material_quality in _HIGH_INFORMATION_QUALITY_MARKERS
        or _bool(route_meta.get("material_sufficient"))
        or str(route_meta.get("input_material_quality") or "") in _HIGH_INFORMATION_QUALITY_MARKERS
        or (memo_len >= 120 and (memo_action_len >= 20 or bool(emotions) or bool(categories)))
        or (rich_visible_material and (memo_len >= 40 or memo_action_len >= 10 or field_count >= 2))
    )
    return {
        "memo_present": bool(memo.strip()),
        "memo_action_present": bool(memo_action.strip()),
        "emotions_present": bool(_listify(emotions)),
        "categories_present": bool(_listify(categories)),
        "memo_text_len": memo_len,
        "memo_action_text_len": memo_action_len,
        "high_information_input": bool(high_information),
        "low_information_material": bool(material_quality in _LOW_INFORMATION_MATERIAL_QUALITIES),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _sanitize_input_material_classification(value: Any) -> dict[str, Any]:
    source = _as_mapping(value)
    return {
        "memo_present": bool(source.get("memo_present")),
        "memo_action_present": bool(source.get("memo_action_present")),
        "emotions_present": bool(source.get("emotions_present")),
        "categories_present": bool(source.get("categories_present")),
        "memo_text_len": _safe_int(source.get("memo_text_len")),
        "memo_action_text_len": _safe_int(source.get("memo_action_text_len")),
        "high_information_input": bool(source.get("high_information_input")),
        "low_information_material": bool(source.get("low_information_material")),
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }



def _visible_material_slots_from_sources(*sources: Mapping[str, Any]) -> tuple[str, ...]:
    slots: list[str] = []
    for source in sources:
        mapping = _as_mapping(source)
        slots.extend(_dedupe(mapping.get("visible_material_slots") or ()))
        nested = _first_mapping(mapping, key="input_material_summary")
        if nested:
            slots.extend(_dedupe(nested.get("visible_material_slots") or ()))
        bundle = _first_mapping(mapping, key="emlis_input_material_bundle")
        if bundle:
            slots.extend(_dedupe(bundle.get("visible_material_slots") or ()))
    return tuple(_dedupe(slots))


def _relation_material_ids_from_sources(*sources: Mapping[str, Any]) -> tuple[str, ...]:
    ids: list[str] = []
    for source in sources:
        mapping = _as_mapping(source)
        ids.extend(_dedupe(mapping.get("relation_material_ids") or ()))
        ids.extend(_dedupe(mapping.get("generic_relation_material_ids") or ()))
        nested = _first_mapping(mapping, key="input_material_summary")
        if nested:
            ids.extend(_dedupe(nested.get("relation_material_ids") or ()))
            ids.extend(_dedupe(nested.get("generic_relation_material_ids") or ()))
        bundle = _first_mapping(mapping, key="emlis_input_material_bundle")
        if bundle:
            ids.extend(_dedupe(bundle.get("relation_material_ids") or ()))
            ids.extend(_dedupe(bundle.get("generic_relation_material_ids") or ()))
    return tuple(_dedupe(ids))


def _rich_visible_material_signal(
    *,
    visible_slots: Sequence[str],
    relation_material_ids: Sequence[str] = (),
) -> bool:
    visible = set(_dedupe(visible_slots or ()))
    relation_ids = set(_dedupe(relation_material_ids or ()))
    if not visible:
        return False
    has_eventish = bool(visible.intersection(_RICH_VISIBLE_EVENTISH_SLOTS))
    has_reactionish = bool(visible.intersection(_RICH_VISIBLE_REACTIONISH_SLOTS))
    meaning_count = len(visible.intersection(_RICH_VISIBLE_MEANING_SLOTS))
    has_relation_material = bool(relation_ids.intersection(_RICH_VISIBLE_RELATION_MATERIAL_IDS))
    if has_eventish and has_reactionish and len(visible) >= 3:
        return True
    if has_reactionish and (meaning_count >= 2 or has_relation_material) and len(visible) >= 3:
        return True
    if has_eventish and meaning_count >= 2 and has_relation_material:
        return True
    return False


def _rich_visible_low_information_boundary_required(
    *,
    enabled: bool,
    material_quality: str,
    input_classification: Mapping[str, Any],
    route_meta: Mapping[str, Any],
    containers: Sequence[Mapping[str, Any]],
) -> bool:
    """Keep rich visible current material from being surfaced as low-information.

    P4-3 does not force ``material_quality`` to eligible.  It only prevents a
    body-free low-information route marker from choosing the low-information
    public shape when visible material already contains enough event/reaction or
    relationship/change structure to require a normal observation surface.
    """

    if not enabled:
        return False
    if material_quality not in _LOW_INFORMATION_MATERIAL_QUALITIES:
        return False
    if input_classification.get("high_information_input") is not True:
        return False
    visible_slots: list[str] = list(_visible_material_slots_from_sources(route_meta))
    relation_ids: list[str] = list(_relation_material_ids_from_sources(route_meta))
    for container in containers:
        visible_slots.extend(_visible_material_slots_from_sources(container))
        relation_ids.extend(_relation_material_ids_from_sources(container))
    return _rich_visible_material_signal(
        visible_slots=visible_slots,
        relation_material_ids=relation_ids,
    )


def _source_unavailable_high_information_boundary_required(
    *,
    enabled: bool,
    input_classification: Mapping[str, Any],
    material_quality: str,
    containers: Sequence[Mapping[str, Any]],
    reason_codes: Sequence[str],
    rich_visible_low_information_boundary: bool,
    low_information_requested: bool,
) -> bool:
    if not enabled:
        return False
    if low_information_requested:
        return False
    if not (input_classification.get("high_information_input") is True or material_quality in _HIGH_INFORMATION_QUALITY_MARKERS or rich_visible_low_information_boundary):
        return False
    joined_reasons = " ".join(reason_codes).lower()
    if any(marker in joined_reasons for marker in _SOURCE_UNAVAILABLE_REASON_MARKERS):
        return True
    for container in containers:
        values = {
            _clean_lower(container.get("first_blocker_family")),
            _clean_lower(container.get("first_blocker_code")),
            _clean_lower(container.get("primary_reason")),
            _clean_lower(container.get("candidate_failure_reason")),
            _clean_lower(container.get("composer_source")),
            _clean_lower(container.get("candidate_source_kind")),
            _clean_lower(container.get("composer_status")),
            _clean_lower(container.get("candidate_status")),
            _clean_lower(container.get("recovery_lane")),
        }
        if any(any(marker in value for marker in _SOURCE_UNAVAILABLE_REASON_MARKERS) for value in values if value):
            return True
        if container.get("source_unavailable_boundary_kept") is True:
            return True
    return False


def _limited_grounding_requested(*, material_quality: str) -> bool:
    return material_quality in _LIMITED_GROUNDING_MATERIAL_QUALITIES


def _low_information_requested(*, material_quality: str, containers: Sequence[Mapping[str, Any]]) -> bool:
    if material_quality in _LIMITED_GROUNDING_MATERIAL_QUALITIES:
        return False
    if material_quality in _LOW_INFORMATION_MATERIAL_QUALITIES:
        return True
    for container in containers:
        values = {
            _clean_lower(container.get("observation_reply_kind")),
            _clean_lower(container.get("reply_kind")),
            _clean_lower(container.get("eligibility_status")),
            _clean_lower(container.get("candidate_source_kind")),
            _clean_lower(container.get("composer_source")),
        }
        if "low_information_observation" in values or "low_information" in values:
            return True
        if any("low_information" in value for value in values if value):
            return True
        if _bool(container.get("low_information_allowed")) or _bool(container.get("low_information_repair_branch")):
            return True
    return False


def _explicit_two_stage_required(containers: Iterable[Mapping[str, Any]]) -> bool:
    for container in containers:
        for key in _TWO_STAGE_META_TRUE_KEYS:
            if _bool(container.get(key)):
                return True
        for key in _TWO_STAGE_META_SHAPE_KEYS:
            if _clean_identifier(container.get(key), max_length=96) == "labelled_two_stage_text":
                return True
    return False


def _fixture_requires_two_stage(fixture: Mapping[str, Any]) -> bool:
    if not fixture:
        return False
    if _bool(fixture.get("two_stage_required")):
        return True
    if _surface_family(fixture.get("surface_requirement_family")) == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE:
        return True
    family = _clean_lower(
        fixture.get("fixture_family")
        or fixture.get("family")
        or fixture.get("case_family")
        or fixture.get("source_phase")
    )
    return bool(any(marker in family for marker in _TWO_STAGE_FIXTURE_FAMILY_MARKERS))


def _high_information_two_stage_required(
    *,
    input_classification: Mapping[str, Any],
    material_quality: str,
    containers: Sequence[Mapping[str, Any]],
    reason_codes: Sequence[str],
) -> bool:
    if not bool(input_classification.get("high_information_input")) and material_quality not in _HIGH_INFORMATION_QUALITY_MARKERS:
        return False
    joined_reasons = " ".join(reason_codes).lower()
    if any(marker in joined_reasons for marker in _TWO_STAGE_REASON_MARKERS):
        return True
    for container in containers:
        family = _clean_lower(
            container.get("input_family")
            or container.get("case_family")
            or container.get("surface_family")
            or container.get("required_surface_family")
            or container.get("structure_family")
        )
        if any(marker in family for marker in _TWO_STAGE_REASON_MARKERS):
            return True
    return False


def _material_relationship_transition_two_stage_required(
    *,
    input_classification: Mapping[str, Any],
    material_quality: str,
    route_meta: Mapping[str, Any],
    containers: Sequence[Mapping[str, Any]],
) -> bool:
    """Require labelled two-stage for rich relation/transition material.

    This is a material-shaped rule, not a fixture route. It only reads
    body-free slots and material identifiers already produced by Phase20-3, so
    D-equivalent source-unavailable inputs can carry the right public-surface
    requirement without embedding their text or reintroducing a case-specific
    surface.
    """

    if material_quality not in _HIGH_INFORMATION_QUALITY_MARKERS:
        return False
    if not bool(input_classification.get("high_information_input")):
        return False
    if _self_denial_safe_state_answer(containers):
        return False

    route_response_kind = _clean_identifier(route_meta.get("response_kind"), max_length=96)
    if route_response_kind and route_response_kind != "normal_observation":
        return False
    route_safety_kind = _clean_identifier(route_meta.get("safety_triage_kind"), max_length=96)
    if route_safety_kind and route_safety_kind != "safe_observation":
        return False

    visible_slots = set(_dedupe(route_meta.get("visible_material_slots") or ()))
    relation_ids = set(
        _dedupe(
            _listify(route_meta.get("relation_material_ids"))
            + _listify(route_meta.get("generic_relation_material_ids"))
        )
    )

    for container in containers:
        visible_slots.update(_dedupe(container.get("visible_material_slots") or ()))
        relation_ids.update(_dedupe(container.get("relation_material_ids") or ()))
        relation_ids.update(_dedupe(container.get("generic_relation_material_ids") or ()))

    relationship_transition_slots = visible_slots.intersection(_RELATIONSHIP_TRANSITION_VISIBLE_SLOT_MARKERS)
    action_slots = visible_slots.intersection(_RELATIONSHIP_TRANSITION_ACTION_SLOT_MARKERS)
    meaning_slots = visible_slots.intersection(_RELATIONSHIP_TRANSITION_MEANING_SLOT_MARKERS)
    relationship_transition_ids = relation_ids.intersection(_RELATIONSHIP_TRANSITION_MATERIAL_IDS)

    return bool(
        "relationship" in visible_slots
        and len(relationship_transition_slots) >= 3
        and bool(action_slots)
        and bool(meaning_slots)
        and len(relationship_transition_ids) >= 2
    )


def _safety_required(containers: Sequence[Mapping[str, Any]], *, reason_codes: Sequence[str]) -> bool:
    if any(any(marker in reason for marker in _SAFETY_REASON_MARKERS) for reason in reason_codes):
        return True
    for container in containers:
        if _bool(container.get("safety_requires_block")) or _bool(container.get("requires_block")):
            return True
        kind = _clean_lower(container.get("safety_triage_kind") or container.get("safety_kind"))
        if any(marker in kind for marker in _SAFETY_REASON_MARKERS):
            return True
    return False


def _infrastructure_failed(containers: Sequence[Mapping[str, Any]], *, reason_codes: Sequence[str]) -> bool:
    if any(any(marker in reason for marker in _INFRASTRUCTURE_REASON_MARKERS) for reason in reason_codes):
        return True
    for container in containers:
        if _bool(container.get("reply_timeout")) or _bool(container.get("reply_error")):
            return True
        code = _clean_lower(container.get("fail_closed_reason_code") or container.get("first_failure_reason"))
        if any(marker in code for marker in _INFRASTRUCTURE_REASON_MARKERS):
            return True
    return False


def _self_denial_safe_state_answer(containers: Sequence[Mapping[str, Any]]) -> bool:
    for container in containers:
        values = {
            _clean_lower(container.get("response_kind")),
            _clean_lower(container.get("surface_requirement_family")),
            _clean_lower(container.get("candidate_source_kind")),
            _clean_lower(container.get("safety_triage_kind")),
        }
        if SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER in values:
            return True
        if any("self_denial_safe_state_answer" in value for value in values if value):
            return True
    return False


def _decision_sources(
    *,
    explicit_two_stage: bool,
    fixture_two_stage: bool,
    high_information_two_stage: bool,
    source_unavailable_high_information_boundary: bool,
    rich_visible_low_information_boundary: bool,
    material_relationship_transition_two_stage: bool,
    two_stage_applicability_required: bool,
    limited_grounding_requested: bool,
    low_information_requested: bool,
    safety_blocked: bool,
    infrastructure_fail_closed: bool,
    self_denial_safe_answer: bool,
    plain_allowed: bool,
) -> list[str]:
    sources: list[str] = []
    if safety_blocked:
        sources.append("safety_boundary")
    if infrastructure_fail_closed:
        sources.append("infrastructure_fail_closed")
    if self_denial_safe_answer:
        sources.append("self_denial_safe_state_answer")
    if explicit_two_stage:
        sources.append("explicit_two_stage_meta")
    if two_stage_applicability_required:
        sources.append("two_stage_applicability")
    if fixture_two_stage:
        sources.append("fixture_family_meta")
    if high_information_two_stage:
        sources.append("high_information_structure_family")
    if source_unavailable_high_information_boundary:
        sources.append(_P4_3_SOURCE_UNAVAILABLE_BOUNDARY_SOURCE)
    if rich_visible_low_information_boundary:
        sources.append(_P4_3_RICH_VISIBLE_LOW_INFO_BOUNDARY_SOURCE)
    if material_relationship_transition_two_stage:
        sources.append("material_relationship_transition_two_stage")
    if limited_grounding_requested:
        sources.append("limited_grounding_reception_required")
    if low_information_requested:
        sources.append("low_information_material")
        sources.append("low_information_reception_required")
    if plain_allowed:
        sources.append("plain_state_answer_default")
    return list(_dedupe(sources or ["plain_state_answer_default"]))


def _required_comment_text_shape(family_value: Any) -> dict[str, Any]:
    family = _surface_family(family_value)
    if family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE:
        return {
            "kind": LABELLED_TWO_STAGE_SHAPE_KIND,
            "starts_with": LABELLED_TWO_STAGE_OBSERVATION_MARKER,
            "contains_boundary": LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
            "labels_required": True,
            "observation_section_required": True,
            "reception_section_required": True,
            "comment_text_body_included": False,
        }
    if family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
        return {
            "kind": LOW_INFORMATION_SHAPE_KIND,
            "starts_with": LABELLED_TWO_STAGE_OBSERVATION_MARKER,
            "contains_boundary": LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
            "labels_required": True,
            "observation_section_required": True,
            "reception_section_required": True,
            "comment_text_body_included": False,
        }
    return {
        "kind": PLAIN_STATE_ANSWER_SHAPE_KIND,
        "starts_with": "",
        "contains_boundary": "",
        "labels_required": False,
        "observation_section_required": True,
        "reception_section_required": False,
        "comment_text_body_included": False,
    }


def _reason_codes(containers: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    reasons: list[str] = []
    visited: set[int] = set()

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            ident = id(value)
            if ident in visited:
                return
            visited.add(ident)
            for key, child in value.items():
                if key in {"rejection_reasons", "reason_codes", "surface_issue_codes", "blockers", "blocked_reasons"}:
                    reasons.extend(_dedupe(child))
                    continue
                if key in {"primary_reason", "first_failure_reason", "fail_closed_reason_code", "candidate_failure_reason"}:
                    text = _clean_identifier(child, max_length=160)
                    if text:
                        reasons.append(text)
                    continue
                collect(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                collect(child)

    for container in containers:
        collect(container)
    return _dedupe(reasons)


def _containers(*sources: Any) -> tuple[Mapping[str, Any], ...]:
    found: list[Mapping[str, Any]] = []
    queue: list[Mapping[str, Any]] = []
    visited: set[int] = set()
    for source in sources:
        mapping = _as_mapping(source)
        if mapping:
            queue.append(mapping)
    while queue and len(found) < 1024:
        current = queue.pop(0)
        ident = id(current)
        if ident in visited:
            continue
        visited.add(ident)
        found.append(current)
        for child in current.values():
            if isinstance(child, Mapping):
                queue.append(child)
            elif isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
                for item in child:
                    if isinstance(item, Mapping):
                        queue.append(item)
    return tuple(found)


def _first_mapping(*sources: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    for source in sources:
        mapping = _as_mapping(source)
        child = mapping.get(key)
        if isinstance(child, Mapping):
            return child
    return {}


def _first_text(*values: Any) -> str:
    for value in values:
        text = _clean_identifier(value, max_length=128)
        if text:
            return text
    return ""


def _surface_family(value: Any) -> str:
    text = _clean_identifier(value, max_length=96)
    return text if text in _SURFACE_REQUIREMENT_FAMILIES else SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER


def _material_route_meta(material_route: Any) -> Mapping[str, Any]:
    if isinstance(material_route, Mapping):
        return material_route
    as_meta = getattr(material_route, "as_meta", None)
    if callable(as_meta):
        try:
            meta = as_meta()
        except Exception:
            return {}
        return meta if isinstance(meta, Mapping) else {}
    meta = getattr(material_route, "meta", None)
    return meta if isinstance(meta, Mapping) else {}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        text = _clean_identifier(value, max_length=160)
        if text and text not in out:
            out.append(text)
    return out


def _clean_identifier(value: Any, *, max_length: int = 160) -> str:
    text = str(value or "").strip().replace(" ", "_")
    return text[:max_length]


def _clean_lower(value: Any) -> str:
    return _clean_identifier(value, max_length=160).lower()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean_lower(value) in {"1", "true", "yes", "y", "on", "enabled", "enable", "green", "passed", "ok", "allowed", "allow", "required"}


def _safe_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0


def _false_public_contract() -> dict[str, bool]:
    return {key: False for key in _PUBLIC_CONTRACT_KEYS}


def _false_gate_policy() -> dict[str, bool]:
    return {key: False for key in _GATE_POLICY_KEYS}


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    return value


def _assert_no_forbidden_body_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _BODY_FORBIDDEN_EXACT_KEYS:
                raise ValueError(f"public surface requirement must stay body-free: {key}")
            _assert_no_forbidden_body_keys(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            _assert_no_forbidden_body_keys(child)


def assert_public_surface_requirement_decision_meta_only(value: Any) -> None:
    """Assert that a surface requirement payload carries no raw/body text."""

    _assert_no_forbidden_body_keys(value)
    if isinstance(value, Mapping):
        if value.get("raw_input_included") is True:
            raise ValueError("public surface requirement must not include raw input")
        if value.get("comment_text_body_included") is True:
            raise ValueError("public surface requirement must not include comment body")
        public_contract = value.get("public_contract")
        if isinstance(public_contract, Mapping) and any(public_contract.get(key) is True for key in _PUBLIC_CONTRACT_KEYS):
            raise ValueError("public surface requirement must not change public contract")
        gate_policy = value.get("gate_policy")
        if isinstance(gate_policy, Mapping) and any(gate_policy.get(key) is True for key in _GATE_POLICY_KEYS):
            raise ValueError("public surface requirement must not relax gates")


__all__ = [
    "LABELLED_TWO_STAGE_OBSERVATION_MARKER",
    "LABELLED_TWO_STAGE_RECEPTION_BOUNDARY",
    "LABELLED_TWO_STAGE_SHAPE_KIND",
    "LOW_INFORMATION_SHAPE_KIND",
    "PLAIN_STATE_ANSWER_SHAPE_KIND",
    "PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION",
    "PUBLIC_SURFACE_REQUIREMENT_SOURCE_PHASE",
    "SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED",
    "SURFACE_REQUIREMENT_LABELLED_TWO_STAGE",
    "SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION",
    "SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER",
    "SURFACE_REQUIREMENT_SAFETY_BLOCKED",
    "SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER",
    "assert_public_surface_requirement_decision",
    "assert_public_surface_requirement_decision_meta_only",
    "is_labelled_two_stage_comment_text_shape",
    "labelled_two_stage_comment_text_shape_summary",
    "public_surface_requirement_public_summary",
    "resolve_public_surface_requirement",
]
