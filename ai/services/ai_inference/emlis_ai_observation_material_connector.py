# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 6 Material / Focus / Relation Connector for observation replies.

This module carries the already-fixed observation-reply decisions from Step 2
(eligibility), Step 3 (user fact grounding), and Step 4 (internal questions)
into the existing Complete Material / Focus Selector / Relation Graph layers.

It is deliberately meta-only.  It does not generate public ``comment_text``, it
keeps public ``observation_status`` as ``passed`` via the Step 1 reply contract,
and it does not relax Display Gate or change DB/API/RN contracts.  For
low-information observation replies, user facts may remain focus hints for
subscription plans, but they must not promote the input to an eligible
observation or assert the current event.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_internal_question_service import (
    INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT,
    INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN,
    INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT,
    INTERNAL_QUESTION_SURFACE_QUESTION,
    InternalQuestionSet,
    assert_internal_question_set_contract,
    build_internal_question_set,
)
from emlis_ai_observation_eligibility_service import (
    OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED,
    assert_observation_eligibility_decision_contract,
    route_observation_eligibility,
)
from emlis_ai_observation_reply_contract import (
    MAX_OBSERVATION_INFERENCE_DEPTH,
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    USER_FACT_GROUNDING_MODE_DISABLED,
    assert_observation_reply_meta_contract,
    build_observation_reply_meta,
)
from emlis_ai_user_fact_grounding_boundary import (
    USER_FACT_USE_FOCUS_SELECTION,
    USER_FACT_USE_INTERNAL_QUESTION_ANSWER,
    USER_FACT_USE_RELATION_WEIGHT,
    assert_user_fact_grounding_decision_contract,
    resolve_user_fact_grounding_boundary,
)

OBSERVATION_MATERIAL_CONNECTOR_VERSION: Final = "emlis.observation_material_connector.v1"
OBSERVATION_MATERIAL_CONNECTOR_STEP: Final = "Step6_Material_Focus_Relation_Connector"
LOW_INFORMATION_RELATION_CONFIDENCE_LIMIT: Final = 0.34
ELIGIBLE_RELATION_CONFIDENCE_LIMIT: Final = 1.0

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
        "note",
        "summary",
        "label",
        "trigger",
        "likely_meaning",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "comment_text_generated",
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
        "external_ai_used",
        "local_llm_used",
        "user_fact_may_promote_to_eligible",
        "promote_low_info_to_eligible",
        "assert_current_event_from_user_fact",
        "user_fact_used_for_current_event_assertion",
        "personality_tendency_allowed",
        "unsupported_assertion_allowed",
    }
)

_FORWARD_KEYS: Final = (
    "observation_reply_kind",
    "eligibility_status",
    "eligible_for_full_observation",
    "question_required",
    "unknown_slots",
    "known_fragment_evidence_ids",
    "user_fact_grounding_mode",
    "plan",
    "facts_used",
    "user_fact_focus_hint_ids",
    "surface_disclosure_required",
    "allowed_user_fact_uses",
    "internal_question_ids",
    "internal_question_count",
    "question_surface_internal_question_ids",
    "inference_depths",
    "max_inference_depth_allowed",
    "max_inference_depth_used",
    "answered_by_current_input_count",
    "supported_by_user_fact_count",
    "unanswered_count",
    "relation_confidence",
    "relation_confidence_limit",
    "relation_confidence_limited",
    "deep_relation_allowed",
    "known_scope_only",
    "low_information_known_scope_only",
    "focus_selection_mode",
    "relation_depth_policy",
    "user_fact_may_hint",
    "user_fact_may_promote_to_eligible",
    "must_not_assert_current_event_from_user_fact",
    "observation_material_connector_ready",
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


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    if hasattr(value, "__dict__"):
        return _contains_text_payload_key(vars(value))
    return False


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
        if not key_text or key_text in _TEXT_PAYLOAD_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


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
            fact_id = _clean(item.get("fact_id") or item.get("id") or item.get("ref_id") or item.get("source_id"))
            safe: dict[str, Any] = {"fact_id": fact_id or f"user_fact_ref_{index + 1}"}
            for key in ("source", "source_kind", "kind", "ref_id", "mode", "role", "status"):
                value = _clean(item.get(key))
                if value:
                    safe[key] = value
        else:
            safe = {"fact_id": _clean(item) or f"user_fact_ref_{index + 1}"}
        encoded = json.dumps(safe, sort_keys=True, ensure_ascii=False)
        if encoded in seen:
            continue
        seen.add(encoded)
        out.append(safe)
    return out


def _fact_ids(refs: Any) -> list[str]:
    return _dedupe(ref.get("fact_id") for ref in _safe_fact_refs(refs))


def _evidence_ids(known_fragments: Any) -> list[str]:
    if known_fragments is None:
        return []
    if isinstance(known_fragments, Mapping):
        iterable: Iterable[Any] = [known_fragments]
    elif isinstance(known_fragments, Sequence) and not isinstance(known_fragments, (str, bytes, bytearray)):
        iterable = known_fragments
    else:
        iterable = [known_fragments]
    out: list[str] = []
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            value = _clean(item.get("evidence_span_id") or item.get("span_id") or item.get("id") or item.get("ref_id"))
        else:
            value = _clean(
                getattr(item, "evidence_span_id", None)
                or getattr(item, "span_id", None)
                or getattr(item, "id", None)
                or getattr(item, "ref_id", None)
            )
        if not value:
            value = f"evidence_span_{index + 1}"
        if value not in out:
            out.append(value)
    return out


def _question_ids(questions: Any, *, surface_question_only: bool = False) -> list[str]:
    if questions is None:
        return []
    if isinstance(questions, Mapping):
        iterable: Iterable[Any] = [questions]
    elif isinstance(questions, Sequence) and not isinstance(questions, (str, bytes, bytearray)):
        iterable = questions
    else:
        iterable = [questions]
    out: list[str] = []
    for index, item in enumerate(iterable):
        row = _meta(item)
        if not row and isinstance(item, Mapping):
            row = dict(item)
        if surface_question_only and _clean(row.get("surface_use")) != INTERNAL_QUESTION_SURFACE_QUESTION:
            continue
        qid = _clean(row.get("question_id")) or f"iq_{index + 1:03d}"
        if qid not in out:
            out.append(qid)
    return out


def _inference_depths(questions: Any) -> list[int]:
    if questions is None:
        return []
    if isinstance(questions, Mapping):
        iterable: Iterable[Any] = [questions]
    elif isinstance(questions, Sequence) and not isinstance(questions, (str, bytes, bytearray)):
        iterable = questions
    else:
        iterable = [questions]
    out: list[int] = []
    for item in iterable:
        row = _meta(item)
        if not row and isinstance(item, Mapping):
            row = dict(item)
        try:
            depth = int(row.get("inference_depth") or 0)
        except (TypeError, ValueError):
            depth = 0
        if 1 <= depth <= MAX_OBSERVATION_INFERENCE_DEPTH and depth not in out:
            out.append(depth)
    return out


def _allowed_uses(value: Any) -> list[str]:
    return _dedupe(value)


def _resolve_inputs(
    *,
    current_input: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    internal_question_set: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    eligibility = eligibility_decision
    if eligibility is None:
        eligibility = route_observation_eligibility(
            current_input=current_input,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
            capability=capability,
            subscription_tier=subscription_tier,
            user_facts=user_facts,
        )
    eligibility_meta = _meta(eligibility)
    assert_observation_eligibility_decision_contract(eligibility_meta)

    if _clean(eligibility_meta.get("eligibility_status") or eligibility_meta.get("status")) == OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED:
        raise ValueError("Step 6 connector expects inputs after the safety boundary")

    user_fact_boundary = user_fact_grounding_decision
    if user_fact_boundary is None:
        user_fact_boundary = resolve_user_fact_grounding_boundary(
            current_input=current_input,
            eligibility_decision=eligibility,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            source_bundle=source_bundle,
        )
    user_fact_meta = _meta(user_fact_boundary)
    assert_user_fact_grounding_decision_contract(user_fact_meta)

    internal_questions = internal_question_set
    if internal_questions is None:
        internal_questions = build_internal_question_set(
            current_input=current_input,
            eligibility_decision=eligibility,
            user_fact_grounding_decision=user_fact_boundary,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            source_bundle=source_bundle,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
    internal_meta = _meta(internal_questions)
    assert_internal_question_set_contract(internal_meta)
    return eligibility_meta, user_fact_meta, internal_meta


@dataclass(frozen=True)
class ObservationMaterialConnector:
    observation_reply_kind: str
    eligibility_status: str
    eligible_for_full_observation: bool
    question_required: bool
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    known_fragment_evidence_ids: Sequence[str] = field(default_factory=tuple)
    user_fact_grounding_mode: str = USER_FACT_GROUNDING_MODE_DISABLED
    plan: str = "free"
    facts_used: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    user_fact_focus_hint_ids: Sequence[str] = field(default_factory=tuple)
    surface_disclosure_required: bool = False
    allowed_user_fact_uses: Sequence[str] = field(default_factory=tuple)
    internal_question_ids: Sequence[str] = field(default_factory=tuple)
    question_surface_internal_question_ids: Sequence[str] = field(default_factory=tuple)
    inference_depths: Sequence[int] = field(default_factory=tuple)
    answered_by_current_input_count: int = 0
    supported_by_user_fact_count: int = 0
    unanswered_count: int = 0
    relation_confidence: float = 0.0
    observation_reply_meta: Mapping[str, Any] = field(default_factory=dict)

    @property
    def low_information(self) -> bool:
        return (
            self.observation_reply_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
            or self.eligibility_status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        )

    @property
    def relation_confidence_limit(self) -> float:
        return LOW_INFORMATION_RELATION_CONFIDENCE_LIMIT if self.low_information else ELIGIBLE_RELATION_CONFIDENCE_LIMIT

    @property
    def relation_confidence_limited(self) -> bool:
        return bool(self.low_information)

    @property
    def deep_relation_allowed(self) -> bool:
        return not self.low_information

    @property
    def known_scope_only(self) -> bool:
        return bool(self.low_information)

    @property
    def max_inference_depth_used(self) -> int:
        depths = [int(item) for item in self.inference_depths if 1 <= int(item) <= MAX_OBSERVATION_INFERENCE_DEPTH]
        return max(depths or [0])

    @property
    def relation_depth_policy(self) -> str:
        return "known_scope_only_limited_relation" if self.low_information else "eligible_depth_1_to_3"

    @property
    def focus_selection_mode(self) -> str:
        return "known_scope_only" if self.low_information else "observation_nucleus"

    def as_meta(self) -> dict[str, Any]:
        facts = _safe_fact_refs(self.facts_used) if self.plan == "subscription" else []
        meta: dict[str, Any] = {
            "version": OBSERVATION_MATERIAL_CONNECTOR_VERSION,
            "schema_version": OBSERVATION_MATERIAL_CONNECTOR_VERSION,
            "source_step": OBSERVATION_MATERIAL_CONNECTOR_STEP,
            "step": OBSERVATION_MATERIAL_CONNECTOR_STEP,
            "observation_material_connector_ready": True,
            "material_focus_relation_connector_ready": True,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "eligible_for_full_observation": bool(self.eligible_for_full_observation),
            "question_required": bool(self.question_required),
            "unknown_slots": list(self.unknown_slots),
            "known_fragment_evidence_ids": list(self.known_fragment_evidence_ids),
            "user_fact_grounding_mode": self.user_fact_grounding_mode,
            "plan": self.plan,
            "facts_used": facts,
            "user_fact_focus_hint_ids": list(self.user_fact_focus_hint_ids),
            "surface_disclosure_required": bool(self.surface_disclosure_required),
            "allowed_user_fact_uses": list(self.allowed_user_fact_uses),
            "internal_question_ids": list(self.internal_question_ids),
            "internal_question_count": len(self.internal_question_ids),
            "question_surface_internal_question_ids": list(self.question_surface_internal_question_ids),
            "inference_depths": [int(item) for item in self.inference_depths],
            "max_inference_depth_allowed": MAX_OBSERVATION_INFERENCE_DEPTH,
            "max_inference_depth_used": int(self.max_inference_depth_used),
            "answered_by_current_input_count": int(self.answered_by_current_input_count),
            "supported_by_user_fact_count": int(self.supported_by_user_fact_count),
            "unanswered_count": int(self.unanswered_count),
            "relation_confidence": round(float(self.relation_confidence), 3),
            "relation_confidence_limit": self.relation_confidence_limit,
            "relation_confidence_limited": self.relation_confidence_limited,
            "deep_relation_allowed": self.deep_relation_allowed,
            "known_scope_only": self.known_scope_only,
            "low_information_known_scope_only": self.known_scope_only,
            "focus_selection_mode": self.focus_selection_mode,
            "relation_depth_policy": self.relation_depth_policy,
            "user_fact_may_hint": bool(self.plan == "subscription" and (facts or self.user_fact_focus_hint_ids)),
            "user_fact_may_promote_to_eligible": False,
            "must_not_assert_current_event_from_user_fact": True,
            "assert_current_event_from_user_fact": False,
            "user_fact_used_for_current_event_assertion": False,
            "observation_reply_meta": _json_safe_mapping(self.observation_reply_meta),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "fixed_fallback_used": False,
            "fixed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "unsupported_assertion_allowed": False,
            "personality_tendency_allowed": False,
        }
        assert_material_focus_relation_connector_contract(meta)
        return meta


def build_material_focus_relation_connector(
    *,
    current_input: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    internal_question_set: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
) -> ObservationMaterialConnector:
    """Resolve Step 2/3/4 decisions into one Step 6 connector payload."""

    eligibility_meta, user_fact_meta, internal_meta = _resolve_inputs(
        current_input=current_input,
        eligibility_decision=eligibility_decision,
        user_fact_grounding_decision=user_fact_grounding_decision,
        internal_question_set=internal_question_set,
        subscription_tier=subscription_tier,
        capability=capability,
        user_facts=user_facts,
        source_bundle=source_bundle,
        evidence_ledger=evidence_ledger,
        observation_graph=observation_graph,
    )

    kind = _clean(internal_meta.get("observation_reply_kind") or eligibility_meta.get("observation_reply_kind"))
    status = _clean(internal_meta.get("eligibility_status") or eligibility_meta.get("eligibility_status") or eligibility_meta.get("status"))
    low_information = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if low_information:
        kind = OBSERVATION_REPLY_KIND_LOW_INFORMATION
        status = OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    else:
        kind = OBSERVATION_REPLY_KIND_ELIGIBLE
        status = OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE

    plan = _clean(internal_meta.get("plan") or user_fact_meta.get("plan")) or "free"
    facts = _safe_fact_refs(internal_meta.get("facts_used") or user_fact_meta.get("facts_used")) if plan == "subscription" else []
    fact_ids = _fact_ids(facts)
    allowed_uses = _allowed_uses(internal_meta.get("allowed_user_fact_uses") or user_fact_meta.get("allowed_uses"))
    if low_information:
        allowed_uses = [item for item in allowed_uses if item != USER_FACT_USE_INTERNAL_QUESTION_ANSWER]

    questions = list(internal_meta.get("questions") or [])
    internal_question_ids = _question_ids(questions)
    question_surface_ids = _question_ids(questions, surface_question_only=True)
    inference_depths = _inference_depths(questions)
    known_fragment_evidence_ids = _evidence_ids(eligibility_meta.get("known_fragments"))
    unknown_slots = _dedupe(internal_meta.get("unknown_slots") or eligibility_meta.get("unknown_slots"))
    user_fact_focus_hint_ids = _dedupe(internal_meta.get("user_fact_focus_hint_ids"))
    if low_information and plan == "subscription" and not user_fact_focus_hint_ids and fact_ids:
        if USER_FACT_USE_FOCUS_SELECTION in allowed_uses or USER_FACT_USE_RELATION_WEIGHT in allowed_uses:
            user_fact_focus_hint_ids = fact_ids

    observation_reply_meta = build_observation_reply_meta(
        observation_reply_kind=kind,
        eligibility_status=status,
        plan=plan,
        eligible_for_full_observation=not low_information,
        question_required=low_information,
        user_fact_grounding_mode=_clean(internal_meta.get("user_fact_grounding_mode") or user_fact_meta.get("mode")),
        user_fact_allowed=bool(plan == "subscription" and facts),
        user_fact_may_hint=bool(plan == "subscription" and (facts or user_fact_focus_hint_ids)),
        facts_used=facts,
        surface_disclosure_required=bool(internal_meta.get("surface_disclosure_required") or user_fact_meta.get("surface_disclosure_required")),
        unknown_slots=unknown_slots,
        inference_depths=inference_depths,
        primary_reason="material_focus_relation_connector_ready",
    )
    assert_observation_reply_meta_contract(observation_reply_meta)

    return ObservationMaterialConnector(
        observation_reply_kind=kind,
        eligibility_status=status,
        eligible_for_full_observation=not low_information,
        question_required=low_information,
        unknown_slots=tuple(unknown_slots),
        known_fragment_evidence_ids=tuple(known_fragment_evidence_ids),
        user_fact_grounding_mode=_clean(internal_meta.get("user_fact_grounding_mode") or user_fact_meta.get("mode")) or USER_FACT_GROUNDING_MODE_DISABLED,
        plan=plan,
        facts_used=tuple(facts),
        user_fact_focus_hint_ids=tuple(user_fact_focus_hint_ids),
        surface_disclosure_required=bool(internal_meta.get("surface_disclosure_required") or user_fact_meta.get("surface_disclosure_required")),
        allowed_user_fact_uses=tuple(allowed_uses),
        internal_question_ids=tuple(internal_question_ids),
        question_surface_internal_question_ids=tuple(question_surface_ids),
        inference_depths=tuple(inference_depths),
        answered_by_current_input_count=int(internal_meta.get("answered_by_current_input_count") or 0),
        supported_by_user_fact_count=int(internal_meta.get("supported_by_user_fact_count") or 0),
        unanswered_count=int(internal_meta.get("unanswered_count") or 0),
        relation_confidence=float(eligibility_meta.get("relation_confidence") or 0.0),
        observation_reply_meta=observation_reply_meta,
    )


def build_observation_material_connector(**kwargs: Any) -> ObservationMaterialConnector:
    return build_material_focus_relation_connector(**kwargs)


def resolve_observation_material_connector(**kwargs: Any) -> ObservationMaterialConnector:
    return build_material_focus_relation_connector(**kwargs)


def build_emlis_ai_observation_material_connector(**kwargs: Any) -> ObservationMaterialConnector:
    return build_material_focus_relation_connector(**kwargs)


def build_material_focus_relation_connector_meta(**kwargs: Any) -> dict[str, Any]:
    return build_material_focus_relation_connector(**kwargs).as_meta()


def observation_material_connector_forward_meta(value: Any) -> dict[str, Any]:
    """Return only the fields that downstream material/focus/relation layers need."""

    meta = _meta(value)
    if not meta:
        return {}
    if meta.get("observation_material_connector_ready") is not True and "observation_reply_kind" not in meta:
        nested = meta.get("observation_material_connector") or meta.get("material_focus_relation_connector")
        if isinstance(nested, Mapping):
            meta = dict(nested)
    out: dict[str, Any] = {}
    for key in _FORWARD_KEYS:
        if key in meta:
            out[key] = _json_safe_value(meta[key])
    if out:
        out.setdefault("observation_material_connector_ready", True)
        out.setdefault("material_focus_relation_connector_connected", True)
    return out


def assert_material_focus_relation_connector_contract(
    value: Mapping[str, Any] | ObservationMaterialConnector,
    *,
    source: str = "material_focus_relation_connector",
) -> None:
    if isinstance(value, ObservationMaterialConnector):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} must remain meta-only and must not contain raw text/comment keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")

    kind = _clean(value.get("observation_reply_kind"))
    status = _clean(value.get("eligibility_status"))
    if kind not in {OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION}:
        raise ValueError(f"{source} has unsupported observation_reply_kind: {kind or '<empty>'}")
    if status not in {OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION}:
        raise ValueError(f"{source} has unsupported eligibility_status: {status or '<empty>'}")

    low_information = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if low_information:
        if value.get("eligible_for_full_observation") is True:
            raise ValueError("low-information connector must not be full-observation eligible")
        if value.get("question_required") is not True:
            raise ValueError("low-information connector must require a question")
        if value.get("known_scope_only") is not True or value.get("low_information_known_scope_only") is not True:
            raise ValueError("low-information connector must stay known-scope-only")
        if value.get("deep_relation_allowed") is True:
            raise ValueError("low-information connector must not allow deep relation")
        if value.get("user_fact_may_promote_to_eligible") is True:
            raise ValueError("user facts must not promote low-information input to eligible")
    else:
        if value.get("eligible_for_full_observation") is not True:
            raise ValueError("eligible connector must remain full-observation eligible")
        if value.get("deep_relation_allowed") is not True:
            raise ValueError("eligible connector should allow depth-1..3 relation")

    max_allowed = int(value.get("max_inference_depth_allowed") or MAX_OBSERVATION_INFERENCE_DEPTH)
    if max_allowed != MAX_OBSERVATION_INFERENCE_DEPTH:
        raise ValueError("max inference depth must remain 3")
    max_used = int(value.get("max_inference_depth_used") or 0)
    if max_used < 0 or max_used > MAX_OBSERVATION_INFERENCE_DEPTH:
        raise ValueError("max inference depth used must be within 0..3")
    if low_information and max_used > 2:
        raise ValueError("low-information connector must not use depth 3")

    plan = _clean(value.get("plan")) or "free"
    if plan == "free" and value.get("facts_used"):
        raise ValueError("Free connector must not carry facts_used")
    if low_information:
        allowed = set(_dedupe(value.get("allowed_user_fact_uses")))
        if USER_FACT_USE_INTERNAL_QUESTION_ANSWER in allowed:
            raise ValueError("low-information connector must not allow user facts as internal question answers")

    if value.get("must_not_assert_current_event_from_user_fact") is not True:
        raise ValueError("connector must forbid current event assertion from user facts")


def dump_material_focus_relation_connector(value: Mapping[str, Any] | ObservationMaterialConnector) -> str:
    meta = value.as_meta() if isinstance(value, ObservationMaterialConnector) else dict(value)
    assert_material_focus_relation_connector_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


__all__ = [
    "ELIGIBLE_RELATION_CONFIDENCE_LIMIT",
    "LOW_INFORMATION_RELATION_CONFIDENCE_LIMIT",
    "OBSERVATION_MATERIAL_CONNECTOR_STEP",
    "OBSERVATION_MATERIAL_CONNECTOR_VERSION",
    "ObservationMaterialConnector",
    "assert_material_focus_relation_connector_contract",
    "build_emlis_ai_observation_material_connector",
    "build_material_focus_relation_connector",
    "build_material_focus_relation_connector_meta",
    "build_observation_material_connector",
    "dump_material_focus_relation_connector",
    "observation_material_connector_forward_meta",
    "resolve_observation_material_connector",
]
