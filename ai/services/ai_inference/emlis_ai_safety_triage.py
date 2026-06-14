# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-2 Safety Triage for EmlisAI.

This module is the internal, meta-only split between:

* normal safe observation;
* non-emergency self-denial that should receive a safe state answer;
* safety-support-required material that should use a separate safety surface;
* emergency safety boundaries that must not be converted into Emlis observation.

It never creates public text, never stores raw user input in meta, and never
relaxes the existing Safety / Grounding / Template / Display gates.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import re
from typing import Any, Final

from emlis_ai_response_contract import (
    EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION,
    build_internal_response_contract,
    response_kind_for_safety_triage_kind,
)

EMLIS_SAFETY_TRIAGE_SCHEMA_VERSION: Final = "cocolon.emlis.safety_triage.v1"
EMLIS_SAFETY_TRIAGE_PHASE: Final = "Phase20-2_Safety_Triage"
EMLIS_SAFETY_TRIAGE_META_KEY: Final = "emlis_safety_triage"

TRIAGE_SAFE_OBSERVATION: Final = "safe_observation"
TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER: Final = "self_denial_safe_state_answer"
TRIAGE_SAFETY_SUPPORT_REQUIRED: Final = "safety_support_required"
TRIAGE_SAFETY_BLOCKED_EMERGENCY: Final = "safety_blocked_emergency"

RESPONSE_NORMAL_OBSERVATION: Final = "normal_observation"
RESPONSE_SELF_DENIAL_SAFE_STATE_ANSWER: Final = "self_denial_safe_state_answer"
RESPONSE_SAFETY_SUPPORT_REQUIRED: Final = "safety_support_required"
RESPONSE_SAFETY_BLOCKED_EMERGENCY: Final = "safety_blocked_emergency"

_EMERGENCY_SELF_HARM_RE: Final = re.compile(
    r"(死にたい|消えたい|生きていたくない|生きたくない|いなくなりたい|終わりにしたい|"
    r"生きるのをやめたい|自殺|自傷$|リスカ|OD|オーバードーズ|過量服薬|首を吊|首吊|首をつ|飛び降り|"
    r"自分を傷つけたい|自分を傷つけよう|自分を傷つけるつもり|自分を傷つけそう|傷つけたい衝動|傷つけそう)",
    re.IGNORECASE,
)
_EMERGENCY_HARM_TO_OTHERS_RE: Final = re.compile(
    r"(殺したい|刺したい|殴り殺|火をつけたい|危害を加えたい)",
    re.IGNORECASE,
)
_SUPPORT_REQUIRED_RE: Final = re.compile(
    r"(安全が保てない|今すぐ危ない|助けてほしい|助けが必要|緊急|救急|通報|抑えられない|止められない)",
    re.IGNORECASE,
)
_EXPRESSION_DIFFICULTY_RE: Final = re.compile(
    r"(上手く表現できない|うまく表現できない|表現できない|"
    r"言葉にできない|言葉に出来ない|整理できない|言い切れない|"
    r"うまく言えない|上手く言えない)",
    re.IGNORECASE,
)
_SELF_DENIAL_HARD_MARKER_RE: Final = re.compile(
    r"((?:自分|私|わたし|俺|僕)(?:なんか|など|は|が|を|だけ|には|の)?[^。！？!?\n]{0,36}"
    r"(?:嫌い|きらい|ダメ|だめ|駄目|価値がない|価値ない|いらない|最低|クズ|責め|追い込|"
    r"許せない|好きになれない|下げ|続けられない人間|悪い)|"
    r"自分を傷つけてるのは私|自分を傷つけているのは私|自分を傷つけてる|自分を傷つけている|"
    r"自分のせい|私のせい|私が悪い|自分が悪い|いい事なんて絶対にない|いいことなんて絶対にない)",
    re.IGNORECASE,
)
# Keep inability-as-identity separate from expression difficulty.  General
# exhaustion such as ``何もできないくらい消耗`` must remain normal observation
# unless the text also contains self-worth / identity-denial markers.
_SELF_DENIAL_IDENTITY_INABILITY_RE: Final = re.compile(
    r"((?:自分|私|わたし|俺|僕)(?:なんか|など|は|が|には)?[^。！？!?\n]{0,16}(?:何も|なにも|何にも)できない|"
    r"(?:自分|私|わたし|俺|僕)(?:なんか|など|は|が)?[^。！？!?\n]{0,16}できない(?:人間|奴|やつ)|"
    r"できない自分|できない人間)",
    re.IGNORECASE,
)
_SELF_DENIAL_RE: Final = re.compile(
    _SELF_DENIAL_HARD_MARKER_RE.pattern + r"|" + _SELF_DENIAL_IDENTITY_INABILITY_RE.pattern,
    re.IGNORECASE,
)
_CONTINUATION_REFUSAL_RE: Final = re.compile(
    r"(続けて[^。！？!?\n]{0,20}(?:いい事なんて絶対にない|いいことなんて絶対にない|良くない|よくない)|"
    r"続けたくない|このままではない|このままじゃない)",
    re.IGNORECASE,
)

_RESPONSE_KIND_BY_TRIAGE: Final = {
    TRIAGE_SAFE_OBSERVATION: RESPONSE_NORMAL_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER: RESPONSE_SELF_DENIAL_SAFE_STATE_ANSWER,
    TRIAGE_SAFETY_SUPPORT_REQUIRED: RESPONSE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY: RESPONSE_SAFETY_BLOCKED_EMERGENCY,
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("　", " ")).strip()


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _is_self_denial_non_emergency(value: str) -> bool:
    """Detect non-emergency self-denial without treating expression difficulty as identity denial.

    P7-HOLD-004 narrows the older broad "self reference + できない" pattern.
    Expression difficulty such as ``表現できない`` or ``言葉にできない`` stays on
    the normal observation path unless a hard self-worth marker or an
    identity-shaped inability marker is also present.  This helper returns only
    booleans and never exposes matched text to meta.
    """

    if _SELF_DENIAL_HARD_MARKER_RE.search(value):
        return True
    if _SELF_DENIAL_IDENTITY_INABILITY_RE.search(value):
        return True
    if _EXPRESSION_DIFFICULTY_RE.search(value):
        return False
    return False


def _text_from_current_input(current_input: Any | None) -> str:
    if not isinstance(current_input, Mapping):
        return _clean(current_input)
    parts: list[str] = []
    for key in (
        "memo",
        "memo_text",
        "text",
        "input_text",
        "body",
        "memo_action",
        "memoAction",
        "action_text",
        "action",
    ):
        value = _clean(current_input.get(key))
        if value:
            parts.append(value)
    return "\n".join(parts)


@dataclass(frozen=True)
class EmlisSafetyTriageDecision:
    safety_triage_kind: str = TRIAGE_SAFE_OBSERVATION
    response_kind: str = RESPONSE_NORMAL_OBSERVATION
    normal_observation_allowed: bool = True
    safe_state_answer_allowed: bool = False
    public_emlis_observation_allowed: bool = True
    public_input_feedback_allowed: bool = True
    requires_separate_safety_surface: bool = False
    blocked_reason: str | None = None
    must_not_accept_identity_claim_as_fact: bool = False
    continuation_refusal_detected: bool = False
    reason_codes: list[str] = field(default_factory=list)
    boundary_types: list[str] = field(default_factory=list)
    evidence_span_ids: list[str] = field(default_factory=list)
    source_fields: list[str] = field(default_factory=list)
    source: str = "text"

    @property
    def requires_block(self) -> bool:
        return self.safety_triage_kind in {
            TRIAGE_SAFETY_SUPPORT_REQUIRED,
            TRIAGE_SAFETY_BLOCKED_EMERGENCY,
        }

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": EMLIS_SAFETY_TRIAGE_SCHEMA_VERSION,
            "source_phase": EMLIS_SAFETY_TRIAGE_PHASE,
            "safety_triage_kind": self.safety_triage_kind,
            "response_kind": self.response_kind,
            "normal_observation_allowed": bool(self.normal_observation_allowed),
            "safe_state_answer_allowed": bool(self.safe_state_answer_allowed),
            "public_emlis_observation_allowed": bool(self.public_emlis_observation_allowed),
            "public_input_feedback_allowed": bool(self.public_input_feedback_allowed),
            "requires_block": bool(self.requires_block),
            "requires_separate_safety_surface": bool(self.requires_separate_safety_surface),
            "blocked_reason": self.blocked_reason,
            "must_not_accept_identity_claim_as_fact": bool(self.must_not_accept_identity_claim_as_fact),
            "continuation_refusal_detected": bool(self.continuation_refusal_detected),
            "reason_codes": list(self.reason_codes or []),
            "boundary_types": list(self.boundary_types or []),
            "evidence_span_ids": list(self.evidence_span_ids or []),
            "source_fields": list(self.source_fields or []),
            "raw_user_text_included": False,
            "comment_text_generated": False,
            "contract_schema_version": EMLIS_INTERNAL_RESPONSE_CONTRACT_SCHEMA_VERSION,
            "source": _clean(self.source) or "text",
        }

    def build_internal_response_contract(self, *, reason: str = "phase20_2_safety_triage") -> dict[str, Any]:
        return build_internal_response_contract(
            response_kind=self.response_kind,
            reason=reason,
        )


def classify_emlis_safety_triage_text(text: Any) -> EmlisSafetyTriageDecision:
    value = _clean(text)
    if not value:
        return EmlisSafetyTriageDecision(source="empty")

    reason_codes: list[str] = []
    boundary_types: list[str] = []
    if _EMERGENCY_SELF_HARM_RE.search(value):
        reason_codes.append("self_harm_emergency")
        boundary_types.append("self_harm")
    if _EMERGENCY_HARM_TO_OTHERS_RE.search(value):
        reason_codes.append("harm_to_others_emergency")
        boundary_types.append("harm_to_others")
    if reason_codes:
        return EmlisSafetyTriageDecision(
            safety_triage_kind=TRIAGE_SAFETY_BLOCKED_EMERGENCY,
            response_kind=RESPONSE_SAFETY_BLOCKED_EMERGENCY,
            normal_observation_allowed=False,
            safe_state_answer_allowed=False,
            public_emlis_observation_allowed=False,
            public_input_feedback_allowed=False,
            requires_separate_safety_surface=True,
            blocked_reason="safety_blocked_emergency",
            must_not_accept_identity_claim_as_fact=True,
            reason_codes=_dedupe(reason_codes),
            boundary_types=_dedupe(boundary_types),
        )

    if _SUPPORT_REQUIRED_RE.search(value):
        return EmlisSafetyTriageDecision(
            safety_triage_kind=TRIAGE_SAFETY_SUPPORT_REQUIRED,
            response_kind=RESPONSE_SAFETY_SUPPORT_REQUIRED,
            normal_observation_allowed=False,
            safe_state_answer_allowed=False,
            public_emlis_observation_allowed=False,
            public_input_feedback_allowed=False,
            requires_separate_safety_surface=True,
            blocked_reason="safety_support_required",
            must_not_accept_identity_claim_as_fact=True,
            reason_codes=["safety_support_required"],
            boundary_types=["safety_support_required"],
        )

    if _is_self_denial_non_emergency(value):
        return EmlisSafetyTriageDecision(
            safety_triage_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
            response_kind=RESPONSE_SELF_DENIAL_SAFE_STATE_ANSWER,
            normal_observation_allowed=False,
            safe_state_answer_allowed=True,
            public_emlis_observation_allowed=True,
            public_input_feedback_allowed=True,
            requires_separate_safety_surface=False,
            blocked_reason=None,
            must_not_accept_identity_claim_as_fact=True,
            continuation_refusal_detected=bool(_CONTINUATION_REFUSAL_RE.search(value)),
            reason_codes=["self_denial_non_emergency"],
            boundary_types=[],
        )

    return EmlisSafetyTriageDecision()


def _rank_triage(decision: EmlisSafetyTriageDecision) -> int:
    return {
        TRIAGE_SAFE_OBSERVATION: 0,
        TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER: 1,
        TRIAGE_SAFETY_SUPPORT_REQUIRED: 2,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY: 3,
    }.get(str(decision.safety_triage_kind), 0)


def merge_emlis_safety_triage_decisions(
    decisions: Iterable[EmlisSafetyTriageDecision],
    *,
    source: str = "merged",
) -> EmlisSafetyTriageDecision:
    items = list(decisions or [])
    if not items:
        return EmlisSafetyTriageDecision(source=source)
    strongest = sorted(items, key=_rank_triage, reverse=True)[0]
    return EmlisSafetyTriageDecision(
        safety_triage_kind=strongest.safety_triage_kind,
        response_kind=strongest.response_kind,
        normal_observation_allowed=strongest.normal_observation_allowed,
        safe_state_answer_allowed=strongest.safe_state_answer_allowed,
        public_emlis_observation_allowed=strongest.public_emlis_observation_allowed,
        public_input_feedback_allowed=strongest.public_input_feedback_allowed,
        requires_separate_safety_surface=strongest.requires_separate_safety_surface,
        blocked_reason=strongest.blocked_reason,
        must_not_accept_identity_claim_as_fact=any(item.must_not_accept_identity_claim_as_fact for item in items),
        continuation_refusal_detected=any(item.continuation_refusal_detected for item in items),
        reason_codes=_dedupe(code for item in items for code in (item.reason_codes or [])),
        boundary_types=_dedupe(kind for item in items for kind in (item.boundary_types or [])),
        evidence_span_ids=_dedupe(span_id for item in items for span_id in (item.evidence_span_ids or [])),
        source_fields=_dedupe(field for item in items for field in (item.source_fields or [])),
        source=source,
    )


def build_emlis_safety_triage_decision(
    *,
    current_input: Any | None = None,
    graph: Any | None = None,
    evidence_spans: Sequence[Any] | None = None,
    graph_safety_boundaries: Sequence[Any] | None = None,
) -> EmlisSafetyTriageDecision:
    decisions: list[EmlisSafetyTriageDecision] = []

    if current_input is not None:
        decision = classify_emlis_safety_triage_text(_text_from_current_input(current_input))
        if decision.safety_triage_kind != TRIAGE_SAFE_OBSERVATION:
            decisions.append(decision)

    for span in list(evidence_spans or []):
        raw_text = _clean(getattr(span, "raw_text", ""))
        if not raw_text:
            continue
        decision = classify_emlis_safety_triage_text(raw_text)
        detected_type = _clean(getattr(span, "detected_type", ""))
        if detected_type == "safety_risk" and decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION:
            decision = EmlisSafetyTriageDecision(
                safety_triage_kind=TRIAGE_SAFETY_SUPPORT_REQUIRED,
                response_kind=RESPONSE_SAFETY_SUPPORT_REQUIRED,
                normal_observation_allowed=False,
                safe_state_answer_allowed=False,
                public_emlis_observation_allowed=False,
                public_input_feedback_allowed=False,
                requires_separate_safety_surface=True,
                blocked_reason="safety_risk_evidence_unclassified",
                must_not_accept_identity_claim_as_fact=True,
                reason_codes=["safety_risk_evidence_unclassified"],
                boundary_types=["safety_boundary"],
            )
        if decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION:
            continue
        decisions.append(
            EmlisSafetyTriageDecision(
                safety_triage_kind=decision.safety_triage_kind,
                response_kind=decision.response_kind,
                normal_observation_allowed=decision.normal_observation_allowed,
                safe_state_answer_allowed=decision.safe_state_answer_allowed,
                public_emlis_observation_allowed=decision.public_emlis_observation_allowed,
                public_input_feedback_allowed=decision.public_input_feedback_allowed,
                requires_separate_safety_surface=decision.requires_separate_safety_surface,
                blocked_reason=decision.blocked_reason,
                must_not_accept_identity_claim_as_fact=decision.must_not_accept_identity_claim_as_fact,
                continuation_refusal_detected=decision.continuation_refusal_detected,
                reason_codes=list(decision.reason_codes or []),
                boundary_types=list(decision.boundary_types or []),
                evidence_span_ids=[_clean(getattr(span, "span_id", ""))],
                source_fields=[_clean(getattr(span, "source_field", ""))],
                source="evidence_span",
            )
        )

    graph_values = list(graph_safety_boundaries or [])
    if graph is not None:
        graph_values.extend(list(getattr(graph, "safety_boundaries", []) or []))
    if _dedupe(graph_values):
        decisions.append(
            EmlisSafetyTriageDecision(
                safety_triage_kind=TRIAGE_SAFETY_SUPPORT_REQUIRED,
                response_kind=RESPONSE_SAFETY_SUPPORT_REQUIRED,
                normal_observation_allowed=False,
                safe_state_answer_allowed=False,
                public_emlis_observation_allowed=False,
                public_input_feedback_allowed=False,
                requires_separate_safety_surface=True,
                blocked_reason="graph_safety_boundary_unclassified",
                must_not_accept_identity_claim_as_fact=True,
                reason_codes=["graph_safety_boundary_unclassified"],
                boundary_types=["safety_boundary"],
                source="observation_graph.safety_boundaries",
            )
        )

    return merge_emlis_safety_triage_decisions(decisions, source="current_input_evidence_graph")


def build_emlis_internal_response_contract_from_safety_triage(
    safety_triage_kind: Any,
    *,
    reason: str = "phase20_2_safety_triage",
) -> dict[str, Any]:
    response_kind = response_kind_for_safety_triage_kind(safety_triage_kind)
    return build_internal_response_contract(response_kind=response_kind, reason=reason)


def assert_emlis_safety_triage_meta(meta: Mapping[str, Any]) -> None:
    if not isinstance(meta, Mapping):
        raise AssertionError("safety triage meta must be a mapping")
    required = {
        "schema_version",
        "source_phase",
        "safety_triage_kind",
        "response_kind",
        "normal_observation_allowed",
        "safe_state_answer_allowed",
        "public_emlis_observation_allowed",
        "public_input_feedback_allowed",
        "requires_separate_safety_surface",
        "must_not_accept_identity_claim_as_fact",
        "raw_user_text_included",
        "contract_schema_version",
    }
    missing = sorted(required.difference(meta.keys()))
    if missing:
        raise AssertionError(f"safety triage meta missing keys: {missing}")
    if meta.get("raw_user_text_included") is not False:
        raise AssertionError("safety triage meta must not include raw user text")
    kind = str(meta.get("safety_triage_kind") or "")
    response_kind = str(meta.get("response_kind") or "")
    if _RESPONSE_KIND_BY_TRIAGE.get(kind) != response_kind:
        raise AssertionError("safety triage kind and response kind mismatch")
    if kind == TRIAGE_SAFETY_BLOCKED_EMERGENCY and meta.get("public_emlis_observation_allowed") is not False:
        raise AssertionError("emergency safety boundary must not allow public Emlis observation")


__all__ = [
    "EMLIS_SAFETY_TRIAGE_SCHEMA_VERSION",
    "EMLIS_SAFETY_TRIAGE_PHASE",
    "EMLIS_SAFETY_TRIAGE_META_KEY",
    "TRIAGE_SAFE_OBSERVATION",
    "TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER",
    "TRIAGE_SAFETY_SUPPORT_REQUIRED",
    "TRIAGE_SAFETY_BLOCKED_EMERGENCY",
    "EmlisSafetyTriageDecision",
    "assert_emlis_safety_triage_meta",
    "build_emlis_internal_response_contract_from_safety_triage",
    "build_emlis_safety_triage_decision",
    "classify_emlis_safety_triage_text",
    "merge_emlis_safety_triage_decisions",
]
