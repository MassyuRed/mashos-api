# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 candidate builder for EmlisAI User Label Connection Observation v1.

This module turns Phase 3 text-free edge material into backend-internal
Mechanism candidates.  It does not generate ``comment_text``, does not add
public response keys, does not connect to the reply runtime, and does not make a
candidate visible before the later User Label Connection Gate.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
from typing import Any, Final

from emlis_ai_user_label_connection_material import assert_user_label_connection_material_meta_contract
from emlis_ai_user_label_connection_types import (
    EDGE_FAMILY_ACTION_STATE_BRIDGE,
    EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
    EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
    EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
    EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
    EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
    SOURCE_SCOPE_OWNED_HISTORY,
    SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE,
)

USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_connection_candidate.v1"
USER_LABEL_CONNECTION_CANDIDATE_KIND: Final = "user_label_connection_mechanism"

MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT: Final = "same_label_line_current_alignment"
MECHANISM_FAMILY_SAME_ENVIRONMENT_DIFFERENT_STATE_ROUTE: Final = "same_environment_different_state_route"
MECHANISM_FAMILY_SAME_STATE_DIFFERENT_ENVIRONMENT_ROUTE: Final = "same_state_different_environment_route"
MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE: Final = "unresolved_weight_line"
MECHANISM_FAMILY_VALUE_ANCHOR_LINE: Final = "value_anchor_line"
MECHANISM_FAMILY_RECOVERY_OR_SHIFT_LINE: Final = "recovery_or_shift_line"

CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE: Final = "insufficient_evidence"
CANDIDATE_QUALITY_GATE_CANDIDATE: Final = "gate_candidate"
CANDIDATE_QUALITY_BLOCKED: Final = "blocked"

INFERENCE_STRENGTH_SOFT: Final = "soft"
INFERENCE_STRENGTH_MEDIUM: Final = "medium"

FORBIDDEN_CLAIMS: Final = (
    "diagnosis",
    "personality_claim",
    "cause_claim_without_evidence",
    "advice",
    "future_prediction",
    "always_claim",
    "should_statement",
    "period_tendency_from_single_record",
)

_ALLOWED_SOURCE_SCOPES: Final = frozenset({SOURCE_SCOPE_OWNED_HISTORY, SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE})
_ALLOWED_MECHANISM_FAMILIES: Final = frozenset(
    {
        MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT,
        MECHANISM_FAMILY_SAME_ENVIRONMENT_DIFFERENT_STATE_ROUTE,
        MECHANISM_FAMILY_SAME_STATE_DIFFERENT_ENVIRONMENT_ROUTE,
        MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE,
        MECHANISM_FAMILY_VALUE_ANCHOR_LINE,
        MECHANISM_FAMILY_RECOVERY_OR_SHIFT_LINE,
    }
)
_ALLOWED_CANDIDATE_QUALITIES: Final = frozenset(
    {CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE, CANDIDATE_QUALITY_GATE_CANDIDATE, CANDIDATE_QUALITY_BLOCKED}
)
_ALLOWED_INFERENCE_STRENGTHS: Final = frozenset({INFERENCE_STRENGTH_SOFT, INFERENCE_STRENGTH_MEDIUM})
_ALLOWED_SOURCE_FIELD_IDS: Final = frozenset(
    {"category", "emotion_details", "emotions", "strength", "memo_action", "memo", "created_at", "selected_at"}
)
_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "raw_user_text",
        "rawUserText",
        "source_text",
        "sourceText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo",
        "memo_action",
        "memo_text",
        "memoText",
        "memo_action_text",
        "memoActionText",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "reply_text",
        "replyText",
        "realized_text",
        "realizedText",
        "body",
        "text",
    }
)


@dataclass(frozen=True)
class UserLabelConnectionCandidateEvidence:
    """Text-free evidence summary for a Phase 4 Mechanism candidate."""

    evidence_record_count: int = 0
    current_record_included: bool = False
    history_record_count: int = 0
    source_field_ids: tuple[str, ...] = field(default_factory=tuple)
    requires_external_knowledge: bool = False
    raw_text_included: bool = False
    raw_input_included: bool = False
    comment_text_body_included: bool = False

    def __post_init__(self) -> None:
        for field_id in self.source_field_ids:
            if field_id not in _ALLOWED_SOURCE_FIELD_IDS:
                raise ValueError(f"unsupported candidate source field id: {field_id}")
        if self.requires_external_knowledge:
            raise ValueError("User Label Connection candidate must not require external knowledge")
        if self.raw_text_included or self.raw_input_included or self.comment_text_body_included:
            raise ValueError("User Label Connection candidate evidence must be text-free")

    def as_meta(self) -> dict[str, Any]:
        return {
            "evidence_record_count": int(max(0, self.evidence_record_count)),
            "current_record_included": bool(self.current_record_included),
            "history_record_count": int(max(0, self.history_record_count)),
            "source_field_ids": list(_dedupe(self.source_field_ids)),
            "requires_external_knowledge": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        }


@dataclass(frozen=True)
class UserLabelConnectionSurfacePermission:
    """Permission flags that keep Phase 4 candidates invisible until Gate."""

    may_surface_now: bool = False
    may_surface_after_user_label_connection_gate: bool = False
    must_use_soft_expression: bool = True
    must_use_scope_marker: bool = True
    must_not_surface_as_fact: bool = True
    must_not_surface_as_personality: bool = True
    must_not_surface_as_diagnosis: bool = True
    must_not_surface_as_cause: bool = True
    must_not_surface_as_advice: bool = True

    def __post_init__(self) -> None:
        if self.may_surface_now:
            raise ValueError("Phase 4 candidates must not surface before User Label Connection Gate")
        for field_name in (
            "must_use_soft_expression",
            "must_use_scope_marker",
            "must_not_surface_as_fact",
            "must_not_surface_as_personality",
            "must_not_surface_as_diagnosis",
            "must_not_surface_as_cause",
            "must_not_surface_as_advice",
        ):
            if getattr(self, field_name) is not True:
                raise ValueError(f"User Label Connection surface permission requires {field_name}=true")

    def as_meta(self) -> dict[str, Any]:
        return {
            "may_surface_now": False,
            "may_surface_after_user_label_connection_gate": bool(self.may_surface_after_user_label_connection_gate),
            "must_use_soft_expression": True,
            "must_use_scope_marker": True,
            "must_not_surface_as_fact": True,
            "must_not_surface_as_personality": True,
            "must_not_surface_as_diagnosis": True,
            "must_not_surface_as_cause": True,
            "must_not_surface_as_advice": True,
        }


@dataclass(frozen=True)
class UserLabelConnectionCandidate:
    """Mechanism candidate built from Phase 3 edge material.

    The candidate is an internal observation candidate, not a visible sentence.
    It carries only edge ids, source field ids, counts, booleans, and safe claim
    restrictions.
    """

    candidate_id: str
    source_scope: str
    mechanism_family: str
    supporting_edge_ids: tuple[str, ...]
    evidence: UserLabelConnectionCandidateEvidence
    inference_strength: str = INFERENCE_STRENGTH_SOFT
    candidate_quality: str = CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE
    surface_permission: UserLabelConnectionSurfacePermission = field(default_factory=UserLabelConnectionSurfacePermission)
    forbidden_claims: tuple[str, ...] = FORBIDDEN_CLAIMS
    schema_version: str = USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION
    candidate_kind: str = USER_LABEL_CONNECTION_CANDIDATE_KIND
    requires_user_history: bool = True
    current_input_required: bool = True
    candidate_body_included: bool = False
    comment_text_generated: bool = False
    public_response_key_added: bool = False

    def __post_init__(self) -> None:
        if not str(self.candidate_id or "").strip():
            raise ValueError("candidate_id is required")
        if self.candidate_kind != USER_LABEL_CONNECTION_CANDIDATE_KIND:
            raise ValueError("unexpected User Label Connection candidate kind")
        if self.source_scope not in _ALLOWED_SOURCE_SCOPES:
            raise ValueError(f"unsupported candidate source_scope: {self.source_scope}")
        if self.mechanism_family not in _ALLOWED_MECHANISM_FAMILIES:
            raise ValueError(f"unsupported mechanism_family: {self.mechanism_family}")
        if self.inference_strength not in _ALLOWED_INFERENCE_STRENGTHS:
            raise ValueError(f"unsupported inference_strength: {self.inference_strength}")
        if self.candidate_quality not in _ALLOWED_CANDIDATE_QUALITIES:
            raise ValueError(f"unsupported candidate_quality: {self.candidate_quality}")
        if self.requires_user_history is not True:
            raise ValueError("User Label Connection candidate requires owned user history")
        if self.current_input_required is not True:
            raise ValueError("User Label Connection candidate requires current input")
        if self.candidate_quality == CANDIDATE_QUALITY_GATE_CANDIDATE:
            if self.evidence.evidence_record_count < 2:
                raise ValueError("gate candidate requires evidence_record_count >= 2")
            if self.evidence.current_record_included is not True:
                raise ValueError("gate candidate requires current record evidence")
            if self.evidence.history_record_count < 1:
                raise ValueError("gate candidate requires at least one history record")
        if self.candidate_body_included or self.comment_text_generated or self.public_response_key_added:
            raise ValueError("Phase 4 candidate must not generate body/comment/public response key")
        missing = set(FORBIDDEN_CLAIMS) - set(self.forbidden_claims)
        if missing:
            raise ValueError(f"candidate forbidden_claims missing: {sorted(missing)}")

    def as_meta(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "candidate_kind": self.candidate_kind,
            "source_scope": self.source_scope,
            "requires_user_history": True,
            "current_input_required": True,
            "mechanism_family": self.mechanism_family,
            "supporting_edge_ids": list(_dedupe(self.supporting_edge_ids)),
            "evidence": self.evidence.as_meta(),
            "inference_strength": self.inference_strength,
            "candidate_quality": self.candidate_quality,
            "surface_permission": self.surface_permission.as_meta(),
            "forbidden_claims": list(_dedupe(self.forbidden_claims)),
            "candidate_body_included": False,
            "comment_text_generated": False,
            "public_response_key_added": False,
        }


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Iterable[Any] | Any | None) -> tuple[str, ...]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _as_material_meta(material: Any) -> dict[str, Any]:
    if isinstance(material, Mapping):
        meta = dict(material)
    else:
        as_meta = getattr(material, "as_meta", None)
        meta = dict(as_meta()) if callable(as_meta) else {}
    if meta.get("schema_version"):
        assert_user_label_connection_material_meta_contract(meta)
    return meta


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
    return False


def _edge_score(edge: Mapping[str, Any]) -> float:
    score = edge.get("edge_score") or {}
    try:
        return float(score.get("final_score") or 0.0)
    except Exception:
        return 0.0


def _safe_edge(edge: Mapping[str, Any]) -> bool:
    if edge.get("line_is_fact") is True:
        return False
    if edge.get("raw_text_included") is True or edge.get("comment_text_body_included") is True:
        return False
    if edge.get("line_is_candidate") is False:
        return False
    score = edge.get("edge_score") or {}
    if score.get("score_is_public") is True:
        return False
    return True


def _edge_family(edge: Mapping[str, Any]) -> str:
    return _clean(edge.get("edge_family"))


def _edge_ids(edges: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return _dedupe(edge.get("edge_id") for edge in edges)


def _edge_source_fields(edges: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    fields: list[str] = []
    for edge in edges:
        for field_id in edge.get("source_field_ids") or []:
            if field_id in _ALLOWED_SOURCE_FIELD_IDS:
                fields.append(field_id)
    return _dedupe(fields)


def _evidence_point_ids(edges: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    point_ids: list[str] = []
    for edge in edges:
        point_ids.extend(edge.get("evidence_point_ids") or [])
    return _dedupe(point_ids)


def _max_evidence_record_count(edges: Sequence[Mapping[str, Any]]) -> int:
    counts: list[int] = []
    for edge in edges:
        try:
            counts.append(int(edge.get("evidence_record_count") or 0))
        except Exception:
            counts.append(0)
    return max(counts or [0])


def _evidence_from_edges(edges: Sequence[Mapping[str, Any]]) -> UserLabelConnectionCandidateEvidence:
    point_ids = _evidence_point_ids(edges)
    current_record_included = any(point_id.startswith("current:") for point_id in point_ids)
    evidence_record_count = _max_evidence_record_count(edges)
    history_record_count = max(0, evidence_record_count - (1 if current_record_included else 0))
    return UserLabelConnectionCandidateEvidence(
        evidence_record_count=evidence_record_count,
        current_record_included=current_record_included,
        history_record_count=history_record_count,
        source_field_ids=_edge_source_fields(edges),
        requires_external_knowledge=False,
        raw_text_included=False,
        raw_input_included=False,
        comment_text_body_included=False,
    )


def _candidate_quality_for_evidence(evidence: UserLabelConnectionCandidateEvidence) -> str:
    if evidence.current_record_included is not True:
        return CANDIDATE_QUALITY_BLOCKED
    if evidence.evidence_record_count < 2 or evidence.history_record_count < 1:
        return CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE
    return CANDIDATE_QUALITY_GATE_CANDIDATE


def _surface_permission_for(*, quality: str, mechanism_family: str) -> UserLabelConnectionSurfacePermission:
    may_surface_after_gate = bool(
        quality == CANDIDATE_QUALITY_GATE_CANDIDATE
        and mechanism_family != MECHANISM_FAMILY_RECOVERY_OR_SHIFT_LINE
    )
    return UserLabelConnectionSurfacePermission(
        may_surface_now=False,
        may_surface_after_user_label_connection_gate=may_surface_after_gate,
        must_use_soft_expression=True,
        must_use_scope_marker=True,
        must_not_surface_as_fact=True,
        must_not_surface_as_personality=True,
        must_not_surface_as_diagnosis=True,
        must_not_surface_as_cause=True,
        must_not_surface_as_advice=True,
    )


def _candidate_from_edges(
    *,
    source_scope: str,
    mechanism_family: str,
    edges: Sequence[Mapping[str, Any]],
    ordinal: int,
) -> UserLabelConnectionCandidate:
    evidence = _evidence_from_edges(edges)
    quality = _candidate_quality_for_evidence(evidence)
    avg_score = sum(_edge_score(edge) for edge in edges) / max(1, len(edges))
    inference_strength = INFERENCE_STRENGTH_MEDIUM if quality == CANDIDATE_QUALITY_GATE_CANDIDATE and avg_score >= 0.82 else INFERENCE_STRENGTH_SOFT
    return UserLabelConnectionCandidate(
        candidate_id=f"ulc.mechanism.{mechanism_family}.{ordinal:03d}",
        source_scope=source_scope,
        mechanism_family=mechanism_family,
        supporting_edge_ids=_edge_ids(edges),
        evidence=evidence,
        inference_strength=inference_strength,
        candidate_quality=quality,
        surface_permission=_surface_permission_for(quality=quality, mechanism_family=mechanism_family),
        forbidden_claims=FORBIDDEN_CLAIMS,
        candidate_body_included=False,
        comment_text_generated=False,
        public_response_key_added=False,
    )


def _insufficient_candidate(*, source_scope: str, material_meta: Mapping[str, Any]) -> UserLabelConnectionCandidate:
    current_present = material_meta.get("current_point_present") is True
    evidence = UserLabelConnectionCandidateEvidence(
        evidence_record_count=1 if current_present else 0,
        current_record_included=current_present,
        history_record_count=0,
        source_field_ids=tuple(),
        requires_external_knowledge=False,
        raw_text_included=False,
        raw_input_included=False,
        comment_text_body_included=False,
    )
    return UserLabelConnectionCandidate(
        candidate_id="ulc.mechanism.insufficient_evidence.001",
        source_scope=source_scope,
        mechanism_family=MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT,
        supporting_edge_ids=tuple(),
        evidence=evidence,
        inference_strength=INFERENCE_STRENGTH_SOFT,
        candidate_quality=CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE,
        surface_permission=_surface_permission_for(
            quality=CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE,
            mechanism_family=MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT,
        ),
        forbidden_claims=FORBIDDEN_CLAIMS,
        candidate_body_included=False,
        comment_text_generated=False,
        public_response_key_added=False,
    )


def _select_edges_by_family(edges: Sequence[Mapping[str, Any]], families: Iterable[str]) -> tuple[Mapping[str, Any], ...]:
    wanted = set(families)
    selected = [edge for edge in edges if _edge_family(edge) in wanted]
    selected.sort(key=lambda edge: (-_edge_score(edge), _clean(edge.get("edge_id"))))
    return tuple(selected)


def build_user_label_connection_candidates(material: Any, *, max_candidates: int = 4) -> tuple[UserLabelConnectionCandidate, ...]:
    """Build Phase 4 Mechanism candidates from Phase 3 material edges.

    The function returns internal-only candidates.  It intentionally does not
    attach them to public feedback meta or visible EmlisAI text.
    """

    material_meta = _as_material_meta(material)
    source_scope = _clean(material_meta.get("source_scope"))
    if source_scope not in _ALLOWED_SOURCE_SCOPES:
        return tuple()

    raw_edges = material_meta.get("connection_edges") or []
    edges = tuple(edge for edge in raw_edges if isinstance(edge, Mapping) and _safe_edge(edge))
    if not edges:
        return (_insufficient_candidate(source_scope=source_scope, material_meta=material_meta),)

    candidate_specs: list[tuple[str, tuple[Mapping[str, Any], ...]]] = []

    same_label_edges = _select_edges_by_family(
        edges,
        {
            EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
            EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
            EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
            EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
            EDGE_FAMILY_ACTION_STATE_BRIDGE,
        },
    )
    if same_label_edges:
        candidate_specs.append((MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT, same_label_edges))

    unresolved_edges = _select_edges_by_family(edges, {EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE})
    if unresolved_edges:
        candidate_specs.append((MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE, unresolved_edges))

    value_edges = _select_edges_by_family(edges, {EDGE_FAMILY_VALUE_LINE_REAPPEARANCE})
    if value_edges:
        candidate_specs.append((MECHANISM_FAMILY_VALUE_ANCHOR_LINE, value_edges))

    contrast_edges = _select_edges_by_family(edges, {EDGE_FAMILY_CONTRAST_LINE_SHIFT})
    if contrast_edges:
        candidate_specs.append((MECHANISM_FAMILY_SAME_ENVIRONMENT_DIFFERENT_STATE_ROUTE, contrast_edges))

    state_output_edges = _select_edges_by_family(edges, {EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT})
    if state_output_edges and not same_label_edges:
        candidate_specs.append((MECHANISM_FAMILY_SAME_STATE_DIFFERENT_ENVIRONMENT_ROUTE, state_output_edges))

    candidates: list[UserLabelConnectionCandidate] = []
    for ordinal, (mechanism_family, selected_edges) in enumerate(candidate_specs, start=1):
        candidates.append(
            _candidate_from_edges(
                source_scope=source_scope,
                mechanism_family=mechanism_family,
                edges=selected_edges,
                ordinal=ordinal,
            )
        )

    if not candidates:
        candidates.append(_insufficient_candidate(source_scope=source_scope, material_meta=material_meta))

    candidates.sort(
        key=lambda candidate: (
            0 if candidate.candidate_quality == CANDIDATE_QUALITY_GATE_CANDIDATE else 1,
            -candidate.evidence.evidence_record_count,
            candidate.candidate_id,
        )
    )
    limited = tuple(candidates[: max(1, int(max_candidates))])
    for candidate in limited:
        assert_user_label_connection_candidate_meta_contract(candidate.as_meta())
    return limited


def build_user_label_connection_candidate_metas(material: Any, *, max_candidates: int = 4) -> list[dict[str, Any]]:
    return [candidate.as_meta() for candidate in build_user_label_connection_candidates(material, max_candidates=max_candidates)]


def build_user_label_connection_candidate_meta(material: Any) -> dict[str, Any]:
    candidates = build_user_label_connection_candidates(material, max_candidates=1)
    if not candidates:
        return {}
    return candidates[0].as_meta()


def assert_user_label_connection_candidate_meta_contract(meta: Mapping[str, Any]) -> None:
    if meta.get("schema_version") != USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION:
        raise ValueError("unexpected UserLabelConnectionCandidate schema_version")
    if meta.get("candidate_kind") != USER_LABEL_CONNECTION_CANDIDATE_KIND:
        raise ValueError("unexpected UserLabelConnectionCandidate kind")
    if meta.get("source_scope") not in _ALLOWED_SOURCE_SCOPES:
        raise ValueError("unexpected UserLabelConnectionCandidate source_scope")
    if meta.get("requires_user_history") is not True:
        raise ValueError("candidate requires_user_history must be true")
    if meta.get("current_input_required") is not True:
        raise ValueError("candidate current_input_required must be true")
    if meta.get("mechanism_family") not in _ALLOWED_MECHANISM_FAMILIES:
        raise ValueError("unexpected mechanism_family")
    evidence = meta.get("evidence") or {}
    if evidence.get("requires_external_knowledge") is not False:
        raise ValueError("candidate must not require external knowledge")
    for key in ("raw_text_included", "raw_input_included", "comment_text_body_included"):
        if evidence.get(key) is not False:
            raise ValueError(f"candidate evidence violates {key}=false")
    for field_id in evidence.get("source_field_ids") or []:
        if field_id not in _ALLOWED_SOURCE_FIELD_IDS:
            raise ValueError(f"unexpected candidate source field id: {field_id}")
    quality = meta.get("candidate_quality")
    if quality not in _ALLOWED_CANDIDATE_QUALITIES:
        raise ValueError("unexpected candidate_quality")
    if quality == CANDIDATE_QUALITY_GATE_CANDIDATE:
        if int(evidence.get("evidence_record_count") or 0) < 2:
            raise ValueError("gate candidate requires evidence_record_count >= 2")
        if evidence.get("current_record_included") is not True:
            raise ValueError("gate candidate requires current record evidence")
        if int(evidence.get("history_record_count") or 0) < 1:
            raise ValueError("gate candidate requires history evidence")
    if meta.get("inference_strength") not in _ALLOWED_INFERENCE_STRENGTHS:
        raise ValueError("unexpected inference_strength")
    permission = meta.get("surface_permission") or {}
    if permission.get("may_surface_now") is not False:
        raise ValueError("candidate must not surface before Gate")
    for key in (
        "must_use_soft_expression",
        "must_use_scope_marker",
        "must_not_surface_as_fact",
        "must_not_surface_as_personality",
        "must_not_surface_as_diagnosis",
        "must_not_surface_as_cause",
        "must_not_surface_as_advice",
    ):
        if permission.get(key) is not True:
            raise ValueError(f"candidate surface permission violates {key}=true")
    missing_claims = set(FORBIDDEN_CLAIMS) - set(meta.get("forbidden_claims") or [])
    if missing_claims:
        raise ValueError(f"candidate forbidden_claims missing: {sorted(missing_claims)}")
    for key in ("candidate_body_included", "comment_text_generated", "public_response_key_added"):
        if meta.get(key) is not False:
            raise ValueError(f"candidate violates {key}=false")
    if _contains_text_payload_key(meta):
        raise ValueError("UserLabelConnectionCandidate meta must not include raw text/comment/candidate body keys")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


# Compatibility alias for later phases/tests.
def assert_user_label_connection_candidate_meta(meta: Mapping[str, Any]) -> None:
    assert_user_label_connection_candidate_meta_contract(meta)


__all__ = [
    "USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_CANDIDATE_KIND",
    "MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT",
    "MECHANISM_FAMILY_SAME_ENVIRONMENT_DIFFERENT_STATE_ROUTE",
    "MECHANISM_FAMILY_SAME_STATE_DIFFERENT_ENVIRONMENT_ROUTE",
    "MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE",
    "MECHANISM_FAMILY_VALUE_ANCHOR_LINE",
    "MECHANISM_FAMILY_RECOVERY_OR_SHIFT_LINE",
    "CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE",
    "CANDIDATE_QUALITY_GATE_CANDIDATE",
    "CANDIDATE_QUALITY_BLOCKED",
    "FORBIDDEN_CLAIMS",
    "UserLabelConnectionCandidateEvidence",
    "UserLabelConnectionSurfacePermission",
    "UserLabelConnectionCandidate",
    "build_user_label_connection_candidates",
    "build_user_label_connection_candidate_metas",
    "build_user_label_connection_candidate_meta",
    "assert_user_label_connection_candidate_meta",
    "assert_user_label_connection_candidate_meta_contract",
]
