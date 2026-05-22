# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 SentencePlan Observation Roles for EmlisAI observation replies.

This module adds observation-reply role metadata to existing Complete
SentencePlan lines.  It deliberately preserves the public/legacy ``line_role``
contract (``opening`` / ``core`` / ``relation`` / ``closing``) and stores the
new logical observation roles only under additive meta.

It does not generate user-facing ``comment_text``, does not extend public
``observation_status``, and does not change API routes, DB physical names, or
RN display contracts.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_observation_reply_contract import (
    MAX_OBSERVATION_INFERENCE_DEPTH,
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
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

OBSERVATION_SENTENCE_PLAN_ROLES_VERSION: Final = "emlis.observation_sentence_plan_roles.v1"
OBSERVATION_SENTENCE_PLAN_ROLES_STEP: Final = "Step7_SentencePlan_Observation_Roles"
SURFACE_ROLE_MERGE_EMPATHY_INPUT_ARRANGEMENT: Final = "empathy+input_arrangement"

_ALLOWED_OBSERVATION_ROLES: Final = frozenset(
    {
        OBSERVATION_ROLE_EMPATHY,
        OBSERVATION_ROLE_INPUT_ARRANGEMENT,
        OBSERVATION_ROLE_STATE_VERBALIZATION,
        OBSERVATION_ROLE_COMPANION_CLOSE,
        OBSERVATION_ROLE_LOW_INFO_RECEIVE,
        OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
        OBSERVATION_ROLE_LOW_INFO_QUESTION,
    }
)
_ALLOWED_REPLY_KINDS: Final = frozenset({OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION})
_ALLOWED_USER_FACT_MODES: Final = frozenset(
    {
        USER_FACT_GROUNDING_MODE_DISABLED,
        USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    }
)
_RAW_PAYLOAD_KEYS: Final = frozenset(
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
        "input_feedback_comment",
        "inputFeedbackComment",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "public_status_extended",
        "observation_status_enum_extended",
        "public_response_key_change",
        "api_response_key_change",
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
        "completed_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "public_line_role_enum_extended",
        "line_role_public_enum_extended",
        "line_role_changed",
        "public_line_role_changed",
        "low_info_deep_relation_allowed",
        "low_info_eligible_promotion_allowed",
        "user_fact_may_promote_to_eligible",
        "assert_current_event_from_user_fact",
    }
)
_SPACE_RE: Final = re.compile(r"\s+")


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


def _safe_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _safe_int(value: Any, *, default: int = 0, minimum: int = 0, maximum: int = 999) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(number, maximum))


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean(key)
        if not key_text or key_text in _RAW_PAYLOAD_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _contains_raw_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _RAW_PAYLOAD_KEYS:
                return True
            if _contains_raw_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_raw_payload_key(item) for item in value)
    return False


def _as_meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        result = as_meta()
        return dict(result) if isinstance(result, Mapping) else {}
    return {}


def _merge_meta_sources(*values: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        meta = _as_meta(value)
        if not meta:
            continue
        nested = meta.get("observation_material_connector") or meta.get("material_focus_relation_connector") or meta.get("observation_reply_meta")
        if isinstance(nested, Mapping):
            merged.update(_json_safe_mapping(nested))
        nested_meta = meta.get("meta")
        if isinstance(nested_meta, Mapping):
            merged.update(_json_safe_mapping(nested_meta))
        merged.update(_json_safe_mapping(meta))
    return merged


def _normalize_reply_kind(value: Any) -> str:
    kind = _clean(value)
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        return OBSERVATION_REPLY_KIND_LOW_INFORMATION
    return OBSERVATION_REPLY_KIND_ELIGIBLE


def _normalize_user_fact_mode(value: Any) -> str:
    mode = _clean(value) or USER_FACT_GROUNDING_MODE_DISABLED
    if mode not in _ALLOWED_USER_FACT_MODES:
        return USER_FACT_GROUNDING_MODE_DISABLED
    return mode


def _normalize_depths(value: Any) -> list[int]:
    values = value if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else [value]
    out: list[int] = []
    for raw in values:
        depth = _safe_int(raw, default=0, minimum=0, maximum=MAX_OBSERVATION_INFERENCE_DEPTH)
        if 1 <= depth <= MAX_OBSERVATION_INFERENCE_DEPTH and depth not in out:
            out.append(depth)
    return out


def _line_copy_with_meta(line: CompleteSentencePlanLine, meta_patch: Mapping[str, Any], *, extra_repair: Iterable[Any] = (), extra_forbidden: Iterable[Any] = ()) -> CompleteSentencePlanLine:
    merged_meta = {**dict(line.meta), **_json_safe_mapping(meta_patch)}
    return CompleteSentencePlanLine(
        sentence_id=line.sentence_id,
        line_role=line.line_role,
        relation_type=line.relation_type,
        focus_rank=line.focus_rank,
        phrase_unit_ids=line.phrase_unit_ids,
        evidence_span_ids=line.evidence_span_ids,
        must_include_roles=line.must_include_roles,
        optional_roles=line.optional_roles,
        forbidden_surface_keys=tuple(_dedupe(list(line.forbidden_surface_keys) + list(extra_forbidden))),
        max_chars=line.max_chars,
        surface_intent=line.surface_intent,
        repair_policy=tuple(_dedupe(list(line.repair_policy) + list(extra_repair))),
        meta=merged_meta,
        schema_version=line.schema_version,
    )


@dataclass(frozen=True)
class ObservationSentencePlanRoleContext:
    observation_reply_kind: str = OBSERVATION_REPLY_KIND_ELIGIBLE
    eligibility_status: str = OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    question_required: bool = False
    known_scope_only: bool = False
    user_fact_grounding_mode: str = USER_FACT_GROUNDING_MODE_DISABLED
    surface_disclosure_required: bool = False
    unknown_slots: tuple[str, ...] = field(default_factory=tuple)
    inference_depths: tuple[int, ...] = field(default_factory=tuple)
    coverage_group: str = ""

    @property
    def low_information(self) -> bool:
        return self.observation_reply_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or self.eligibility_status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION

    @property
    def required_roles(self) -> tuple[str, ...]:
        if self.low_information:
            return (
                OBSERVATION_ROLE_LOW_INFO_RECEIVE,
                OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
                OBSERVATION_ROLE_LOW_INFO_QUESTION,
            )
        return (
            OBSERVATION_ROLE_EMPATHY,
            OBSERVATION_ROLE_INPUT_ARRANGEMENT,
            OBSERVATION_ROLE_STATE_VERBALIZATION,
        )

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": OBSERVATION_SENTENCE_PLAN_ROLES_VERSION,
            "source_step": OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
            "step": OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "question_required": bool(self.question_required),
            "known_scope_only": bool(self.known_scope_only),
            "user_fact_grounding_mode": self.user_fact_grounding_mode,
            "surface_disclosure_required": bool(self.surface_disclosure_required),
            "unknown_slots": list(self.unknown_slots),
            "inference_depths": list(self.inference_depths),
            "coverage_group": self.coverage_group,
            "required_observation_roles": list(self.required_roles),
            "existing_line_role_preserved": True,
            "line_role_public_enum_extended": False,
            "public_line_role_enum_extended": False,
            "observation_roles_meta_only": True,
            "comment_text_generated": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "response_shape_changed": False,
            "display_gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
        }


def build_observation_sentence_plan_role_context(*sources: Any, coverage_group: Any = "") -> ObservationSentencePlanRoleContext:
    meta = _merge_meta_sources(*sources)
    group = _clean(coverage_group) or _clean(meta.get("coverage_group"))
    kind = _normalize_reply_kind(meta.get("observation_reply_kind"))
    low_information = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or _clean(meta.get("eligibility_status")) == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    status = OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION if low_information else OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    if low_information:
        kind = OBSERVATION_REPLY_KIND_LOW_INFORMATION
    return ObservationSentencePlanRoleContext(
        observation_reply_kind=kind,
        eligibility_status=status,
        question_required=_safe_bool(meta.get("question_required"), default=low_information),
        known_scope_only=_safe_bool(meta.get("known_scope_only") or meta.get("low_information_known_scope_only"), default=low_information),
        user_fact_grounding_mode=_normalize_user_fact_mode(meta.get("user_fact_grounding_mode")),
        surface_disclosure_required=_safe_bool(meta.get("surface_disclosure_required"), default=False),
        unknown_slots=tuple(_dedupe(meta.get("unknown_slots"))),
        inference_depths=tuple(_normalize_depths(meta.get("inference_depths"))),
        coverage_group=group,
    )


def _eligible_roles_for_line(line_role: str, *, index: int, total_lines: int, coverage_group: str) -> tuple[list[str], list[str], int | None, list[str], list[str]]:
    short_merge = bool(total_lines <= 2 or _clean(coverage_group) == "short_daily")
    surface_role_merge: list[str] = []
    if line_role == "opening":
        roles = [OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_INPUT_ARRANGEMENT]
        depth = 1
        if short_merge:
            surface_role_merge.append(SURFACE_ROLE_MERGE_EMPATHY_INPUT_ARRANGEMENT)
        repair = ["preserve_empathy_input_arrangement_merge"] if short_merge else ["preserve_empathy_receive_role"]
        forbidden = ["empathy_only_reply", "fixed_sentence_template"]
    elif line_role == "relation":
        roles = [OBSERVATION_ROLE_STATE_VERBALIZATION]
        depth = 3
        repair = ["preserve_state_verbalization", "relation_not_expressed"]
        forbidden = ["unsupported_state_verbalization", "overclaim", "personality_claim"]
    elif line_role == "closing":
        roles = [OBSERVATION_ROLE_COMPANION_CLOSE]
        depth = None
        repair = ["trim_optional_only", "no_action_instruction"]
        forbidden = ["action_instruction", "diagnosis_claim", "over_comfort"]
    else:
        if short_merge and index >= total_lines:
            roles = [OBSERVATION_ROLE_STATE_VERBALIZATION]
            depth = 2
            repair = ["preserve_state_verbalization"]
            forbidden = ["unsupported_state_verbalization", "overclaim"]
        elif total_lines <= 3:
            roles = [OBSERVATION_ROLE_INPUT_ARRANGEMENT, OBSERVATION_ROLE_STATE_VERBALIZATION]
            depth = 2
            repair = ["preserve_input_arrangement", "preserve_state_verbalization"]
            forbidden = ["echo_only_input_arrangement", "unsupported_state_verbalization", "overclaim"]
        else:
            roles = [OBSERVATION_ROLE_INPUT_ARRANGEMENT]
            depth = 2
            repair = ["preserve_input_arrangement"]
            forbidden = ["echo_only_input_arrangement", "full_summary"]
    return roles, surface_role_merge, depth, repair, forbidden


def _low_information_roles_for_line(line_role: str, *, index: int, total_lines: int) -> tuple[list[str], list[str], int | None, list[str], list[str]]:
    last_line = index >= total_lines
    surface_role_merge: list[str] = []
    if line_role == "opening":
        roles = [OBSERVATION_ROLE_LOW_INFO_RECEIVE]
        depth = 1
        repair = ["preserve_low_info_receive"]
        forbidden = ["deep_observation", "overclaim", "event_assertion"]
    elif line_role == "closing":
        roles = [OBSERVATION_ROLE_LOW_INFO_QUESTION]
        depth = None
        repair = ["preserve_low_info_question", "unknown_slot_question_required"]
        forbidden = ["question_only_without_known_scope", "action_instruction", "assert_current_event_from_user_fact"]
    elif line_role == "relation":
        roles = [OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE]
        depth = 2
        repair = ["preserve_known_scope_only"]
        forbidden = ["deep_relation_claim", "unsupported_state_verbalization", "assert_current_event_from_user_fact"]
    else:
        roles = [OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE]
        depth = 1
        repair = ["preserve_known_scope_only"]
        forbidden = ["deep_observation", "unsupported_state_verbalization", "assert_current_event_from_user_fact"]

    if last_line and OBSERVATION_ROLE_LOW_INFO_QUESTION not in roles:
        roles.append(OBSERVATION_ROLE_LOW_INFO_QUESTION)
        repair.append("unknown_slot_question_required")
        forbidden.append("question_only_without_known_scope")
    return roles, surface_role_merge, depth, repair, forbidden


def build_observation_sentence_plan_line_meta(
    *,
    line_role: Any,
    index: int,
    total_lines: int,
    context: ObservationSentencePlanRoleContext | Mapping[str, Any] | None = None,
    coverage_group: Any = "",
) -> dict[str, Any]:
    role = _clean(line_role) or "core"
    ctx = context if isinstance(context, ObservationSentencePlanRoleContext) else build_observation_sentence_plan_role_context(context or {}, coverage_group=coverage_group)
    group = _clean(coverage_group) or ctx.coverage_group
    if ctx.low_information:
        roles, merge, depth, repair, forbidden = _low_information_roles_for_line(role, index=index, total_lines=max(total_lines, 1))
    else:
        roles, merge, depth, repair, forbidden = _eligible_roles_for_line(role, index=index, total_lines=max(total_lines, 1), coverage_group=group)

    if depth is not None:
        max_depth = 2 if ctx.low_information else MAX_OBSERVATION_INFERENCE_DEPTH
        depth = max(1, min(int(depth), max_depth))

    meta = {
        "version": OBSERVATION_SENTENCE_PLAN_ROLES_VERSION,
        "schema_version": OBSERVATION_SENTENCE_PLAN_ROLES_VERSION,
        "source_step": OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
        "step": OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
        "observation_sentence_plan_roles_ready": True,
        "observation_roles": roles,
        "sentence_plan_observation_roles": roles,
        "observation_reply_kind": ctx.observation_reply_kind,
        "eligibility_status": ctx.eligibility_status,
        "inference_depth": depth,
        "known_scope_only": bool(ctx.known_scope_only or ctx.low_information),
        "question_required": bool(ctx.question_required or ctx.low_information),
        "user_fact_grounding_mode": ctx.user_fact_grounding_mode,
        "surface_disclosure_required": bool(ctx.surface_disclosure_required),
        "surface_role_merge": merge,
        "line_role_original": role,
        "existing_line_role_preserved": True,
        "line_role_public_enum_extended": False,
        "public_line_role_enum_extended": False,
        "line_role_changed": False,
        "public_line_role_changed": False,
        "observation_roles_meta_only": True,
        "low_info_question_role_required": bool(ctx.low_information),
        "low_info_question_role_present": OBSERVATION_ROLE_LOW_INFO_QUESTION in roles,
        "comment_text_generated": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "role_repair_policy": repair,
        "role_forbidden_surface_keys": forbidden,
    }
    assert_observation_sentence_plan_line_meta_contract(meta)
    return meta


def annotate_observation_sentence_plan_lines(
    lines: Sequence[CompleteSentencePlanLine | Mapping[str, Any]],
    *,
    observation_context: ObservationSentencePlanRoleContext | Mapping[str, Any] | None = None,
    coverage_group: Any = "",
) -> tuple[CompleteSentencePlanLine, ...]:
    coerced = tuple(line if isinstance(line, CompleteSentencePlanLine) else CompleteSentencePlanLine(**line) for line in lines)
    ctx = observation_context if isinstance(observation_context, ObservationSentencePlanRoleContext) else build_observation_sentence_plan_role_context(observation_context or {}, coverage_group=coverage_group)
    total = len(coerced)
    annotated: list[CompleteSentencePlanLine] = []
    for index, line in enumerate(coerced, start=1):
        role_meta = build_observation_sentence_plan_line_meta(
            line_role=line.line_role,
            index=index,
            total_lines=total,
            context=ctx,
            coverage_group=coverage_group,
        )
        annotated.append(
            _line_copy_with_meta(
                line,
                role_meta,
                extra_repair=role_meta.get("role_repair_policy") or (),
                extra_forbidden=role_meta.get("role_forbidden_surface_keys") or (),
            )
        )
    return tuple(annotated)


def _aggregate_roles_from_lines(lines: Sequence[CompleteSentencePlanLine | Mapping[str, Any]]) -> list[str]:
    out: list[str] = []
    for line in lines:
        meta = line.meta if isinstance(line, CompleteSentencePlanLine) else dict(line.get("meta") or {})
        for role in _dedupe(meta.get("observation_roles") or meta.get("sentence_plan_observation_roles")):
            if role not in out:
                out.append(role)
    return out


def build_observation_sentence_plan_roles_meta(
    *,
    lines: Sequence[CompleteSentencePlanLine | Mapping[str, Any]],
    observation_context: ObservationSentencePlanRoleContext | Mapping[str, Any] | None = None,
    coverage_group: Any = "",
) -> dict[str, Any]:
    ctx = observation_context if isinstance(observation_context, ObservationSentencePlanRoleContext) else build_observation_sentence_plan_role_context(observation_context or {}, coverage_group=coverage_group)
    aggregate_roles = _aggregate_roles_from_lines(lines)
    required_roles = list(ctx.required_roles)
    missing = [role for role in required_roles if role not in aggregate_roles]
    low_info_question_present = OBSERVATION_ROLE_LOW_INFO_QUESTION in aggregate_roles
    eligible_merge_present = any(
        SURFACE_ROLE_MERGE_EMPATHY_INPUT_ARRANGEMENT in _dedupe((line.meta if isinstance(line, CompleteSentencePlanLine) else dict(line.get("meta") or {})).get("surface_role_merge"))
        for line in lines
    )
    line_roles = [line.line_role if isinstance(line, CompleteSentencePlanLine) else _clean(line.get("line_role")) for line in lines]
    meta = {
        **ctx.as_meta(),
        "observation_sentence_plan_roles_ready": True,
        "sentence_plan_observation_roles_added": True,
        "observation_roles_attached_to_meta": True,
        "observation_roles_meta_only": True,
        "line_role_preserved": True,
        "existing_line_role_preserved": True,
        "public_line_role_enum_extended": False,
        "line_role_public_enum_extended": False,
        "line_roles": line_roles,
        "observation_role_line_count": len(lines),
        "sentence_plan_observation_roles": aggregate_roles,
        "fulfilled_observation_roles": aggregate_roles,
        "required_observation_roles": required_roles,
        "missing_observation_roles": missing,
        "observation_role_contract_passed": not missing,
        "short_eligible_role_merge_allowed": bool(not ctx.low_information),
        "surface_role_merge_allowed": bool(not ctx.low_information),
        "surface_role_merge_present": eligible_merge_present,
        "low_info_question_role_required": bool(ctx.low_information),
        "low_info_question_role_present": low_info_question_present,
        "low_info_question_role_missing": bool(ctx.low_information and not low_info_question_present),
        "low_info_deep_relation_allowed": False,
        "low_info_eligible_promotion_allowed": False,
        "user_fact_may_promote_to_eligible": False,
        "assert_current_event_from_user_fact": False,
        "comment_text_generated": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }
    assert_observation_sentence_plan_roles_contract(meta)
    return meta


def annotate_observation_sentence_plan(
    plan: CompleteSentencePlanV2,
    *,
    observation_context: ObservationSentencePlanRoleContext | Mapping[str, Any] | None = None,
) -> CompleteSentencePlanV2:
    ctx = observation_context if isinstance(observation_context, ObservationSentencePlanRoleContext) else build_observation_sentence_plan_role_context(observation_context or plan.meta, coverage_group=plan.coverage_group)
    lines = annotate_observation_sentence_plan_lines(plan.sentence_plans, observation_context=ctx, coverage_group=plan.coverage_group)
    role_meta = build_observation_sentence_plan_roles_meta(lines=lines, observation_context=ctx, coverage_group=plan.coverage_group)
    return CompleteSentencePlanV2(
        plan_id=plan.plan_id,
        sentence_budget=plan.sentence_budget,
        coverage_group=plan.coverage_group,
        sentence_plans=lines,
        meta={**dict(plan.meta), **role_meta},
        schema_version=plan.schema_version,
    )


def observation_sentence_plan_roles_meta_for_plan(plan: CompleteSentencePlanV2 | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(plan, CompleteSentencePlanV2):
        return build_observation_sentence_plan_roles_meta(lines=plan.sentence_plans, observation_context=plan.meta, coverage_group=plan.coverage_group)
    meta = dict(plan.get("meta") or {}) if isinstance(plan, Mapping) else {}
    lines = tuple(plan.get("sentence_plans") or plan.get("lines") or ()) if isinstance(plan, Mapping) else tuple()
    return build_observation_sentence_plan_roles_meta(lines=lines, observation_context=meta, coverage_group=plan.get("coverage_group") if isinstance(plan, Mapping) else "")


def build_observation_sentence_plan_roles_contract_meta() -> dict[str, Any]:
    ctx = ObservationSentencePlanRoleContext()
    return {
        **ctx.as_meta(),
        "observation_sentence_plan_roles_ready": True,
        "sentence_plan_observation_roles_added": True,
        "line_role_preserved": True,
        "existing_line_role_preserved": True,
        "observation_roles_attached_to_meta": True,
        "observation_roles_meta_only": True,
        "short_eligible_role_merge_allowed": True,
        "low_information_question_role_required": True,
        "low_info_question_role_required": True,
        "public_line_role_enum_extended": False,
        "line_role_public_enum_extended": False,
        "comment_text_generated": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "response_shape_changed": False,
        "display_gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def assert_observation_sentence_plan_line_meta_contract(value: Mapping[str, Any], *, source: str = "observation_sentence_plan_line_meta") -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_raw_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    roles = _dedupe(value.get("observation_roles") or value.get("sentence_plan_observation_roles"))
    if not roles:
        raise ValueError(f"{source} must contain observation_roles")
    unsupported = [role for role in roles if role not in _ALLOWED_OBSERVATION_ROLES]
    if unsupported:
        raise ValueError(f"{source} has unsupported observation roles: {', '.join(unsupported)}")
    kind = _clean(value.get("observation_reply_kind"))
    if kind not in _ALLOWED_REPLY_KINDS:
        raise ValueError(f"{source} has unsupported observation_reply_kind: {kind or '<empty>'}")
    mode = _clean(value.get("user_fact_grounding_mode")) or USER_FACT_GROUNDING_MODE_DISABLED
    if mode not in _ALLOWED_USER_FACT_MODES:
        raise ValueError(f"{source} has unsupported user_fact_grounding_mode")
    depth = value.get("inference_depth")
    if depth is not None:
        depth_int = _safe_int(depth, default=0, minimum=0, maximum=MAX_OBSERVATION_INFERENCE_DEPTH)
        if depth_int <= 0:
            raise ValueError(f"{source} has invalid inference_depth")
        if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and depth_int > 2:
            raise ValueError("low-information observation roles must not use depth 3")
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and value.get("question_required") is not True:
        raise ValueError("low-information line meta must require a question")
    if value.get("existing_line_role_preserved") is not True:
        raise ValueError("existing line_role must be preserved")


def assert_observation_sentence_plan_roles_contract(value: Mapping[str, Any], *, source: str = "observation_sentence_plan_roles") -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_raw_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    kind = _clean(value.get("observation_reply_kind")) or OBSERVATION_REPLY_KIND_ELIGIBLE
    roles = _dedupe(value.get("sentence_plan_observation_roles") or value.get("fulfilled_observation_roles"))
    if not roles and int(value.get("observation_role_line_count") or 0) == 0:
        return
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        if value.get("low_info_question_role_required") is not True:
            raise ValueError("low-information observation plan must require low_info_question")
        if value.get("low_info_question_role_present") is not True:
            raise ValueError("low-information observation plan must include low_info_question")
        if OBSERVATION_ROLE_LOW_INFO_QUESTION not in roles:
            raise ValueError("low-information observation roles must include low_info_question")
        if value.get("known_scope_only") is not True:
            raise ValueError("low-information observation roles must stay known-scope-only")
    else:
        if OBSERVATION_ROLE_STATE_VERBALIZATION not in roles:
            raise ValueError("eligible observation roles must include state_verbalization")
        if OBSERVATION_ROLE_INPUT_ARRANGEMENT not in roles:
            raise ValueError("eligible observation roles must include input_arrangement")
    if value.get("public_line_role_enum_extended") is True or value.get("line_role_public_enum_extended") is True:
        raise ValueError("observation roles must not extend public line_role enum")


def dump_observation_sentence_plan_roles(value: Mapping[str, Any] | CompleteSentencePlanV2) -> str:
    meta = observation_sentence_plan_roles_meta_for_plan(value) if isinstance(value, CompleteSentencePlanV2) else dict(value)
    assert_observation_sentence_plan_roles_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


# Backward-friendly aliases for tests/callers.
build_sentence_plan_observation_role_context = build_observation_sentence_plan_role_context
apply_observation_sentence_plan_roles = annotate_observation_sentence_plan
apply_observation_sentence_plan_roles_to_lines = annotate_observation_sentence_plan_lines
build_sentence_plan_observation_roles_meta = build_observation_sentence_plan_roles_meta
assert_sentence_plan_observation_roles_contract = assert_observation_sentence_plan_roles_contract


__all__ = [
    "OBSERVATION_SENTENCE_PLAN_ROLES_STEP",
    "OBSERVATION_SENTENCE_PLAN_ROLES_VERSION",
    "SURFACE_ROLE_MERGE_EMPATHY_INPUT_ARRANGEMENT",
    "ObservationSentencePlanRoleContext",
    "annotate_observation_sentence_plan",
    "annotate_observation_sentence_plan_lines",
    "apply_observation_sentence_plan_roles",
    "apply_observation_sentence_plan_roles_to_lines",
    "assert_observation_sentence_plan_line_meta_contract",
    "assert_observation_sentence_plan_roles_contract",
    "assert_sentence_plan_observation_roles_contract",
    "build_observation_sentence_plan_line_meta",
    "build_observation_sentence_plan_role_context",
    "build_observation_sentence_plan_roles_contract_meta",
    "build_observation_sentence_plan_roles_meta",
    "build_sentence_plan_observation_role_context",
    "build_sentence_plan_observation_roles_meta",
    "dump_observation_sentence_plan_roles",
    "observation_sentence_plan_roles_meta_for_plan",
]
