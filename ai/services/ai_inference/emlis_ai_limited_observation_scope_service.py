# -*- coding: utf-8 -*-
from __future__ import annotations

"""Limited Observation Scope for the EmlisAI B-plan.

The scope gate decides what may be verbalized by the internal Limited Composer.
It never creates user-facing observation text.  Phase 8 additionally keeps
emotion/category-only graph labels out of the body path and adds grounded source
spans required by real-input profiles.
"""

import re
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple

from emlis_ai_safety_boundary_service import build_emlis_safety_boundary_decision, normalize_safety_boundary_codes
from emlis_ai_types import (
    EvidenceSpan,
    GraphClaim,
    LimitedObservationScope,
    LimitedScopeExcludedItem,
    ObservationGraph,
    RelationEdge,
)

_MIN_PRIMARY_CONFIDENCE = 0.35
_MIN_CLAIM_CONFIDENCE = 0.25
_MIN_RELATION_CONFIDENCE = 0.25
_MAX_CORE_TENSIONS = 1
_MAX_OPTIONAL_CLAIMS = 4
_MAX_CLAIMS_PER_GROUP = 1
_TEXT_SOURCE_FIELDS = {"memo", "memo_action"}
_SCOPE_EXPANSION_VERSION = "emlis.scope_expansion.v1"
_SCOPE_SAFETY_BOUNDARY_VERSION = "emlis.scope_safety_boundary.v1"
_SAFETY_BOUNDARY_REASON = "limited_scope_safety_boundary"

_REQUIRED_MISSING_INFO_BLOCKERS = {
    "no_current_input_text",
    "perspective_board_contract_not_ready",
    "graph_primary_state_missing",
}

_GRAPH_GROUPS: Tuple[Tuple[str, str], ...] = (
    ("value_or_strength_signals", "value_or_strength"),
    ("pressure_sources", "pressure"),
    ("limit_signals", "limit"),
    ("self_awareness", "self_awareness"),
)

_POSITIVE_RE = re.compile(r"(楽しか|楽し|笑え|元気|嬉し|うれし|リラックス|安心|ほっと|落ち着|回復|優先|整え|家のこと|片付け|気持ちが軽|ちゃんとでき|できた)")
_PRESSURE_RE = re.compile(r"(不安|心配|焦|緊張|不便|ダメージ|悪化|気をつけ|気を付け|責め|きつ|言い方|腹が立|怒|怖|こわ|しんどい|つら|辛|傷つ|悔し|迷惑|困らせ|重い|嫌われ|嫌だ|嫌にな|落ちる|多すぎ|詰ま|追いつ|余裕がない|失敗)")
_LIMIT_RE = re.compile(r"(限界|逃げ出|投げ出|何もしたくない|もう無理|無理|休みたい|疲れ|疲労|消耗|だるい|気が抜け|止まらなく|動けなく|抱え|一人で考え|つらい|辛い|苦し|面倒|距離|全部嫌|嫌だ)")
_SELF_RE = re.compile(r"(分かって|わかって|分かる|わかる|考えすぎ|考え始め|完璧|適当に|気づいて|気づい|理解して|ちゃんと見|自分でも|見えている)")
_WISH_RE = re.compile(r"(頼りたい|相談したい|話したい|助けを借りたい|支えてほしい|生活したい|普通に生活|優先|整え|したい|大事にしたい|大切にしたい|守りたい|選びたい|欲しい|ほしい|願い)")
_GROUP_TO_COVERAGE = {
    "pressure_sources": ("anxiety", "anger_hurt", "relationship"),
    "limit_signals": ("energy_fatigue", "limit_escape"),
    "self_awareness": ("long_meaning_arc",),
    "value_or_strength_signals": ("positive_recovery", "value_wish"),
}


def _dedupe(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out



def _scope_safety_boundary_meta(*, graph: ObservationGraph, evidence_spans: Sequence[EvidenceSpan]) -> Dict[str, Any]:
    """Return Step10 scope-side safety boundary diagnostics.

    Step10 keeps the fail-closed safety decision inside the scope layer so the
    Limited Composer never receives a normal body-generation request when the
    current input contains a safety boundary.  This is developer-facing meta;
    it stores only stable codes, never raw unsafe source fragments.
    """

    decision = build_emlis_safety_boundary_decision(graph=graph, evidence_spans=evidence_spans)
    detector_meta = decision.as_meta()
    requires_block = bool(detector_meta.get("requires_block"))
    graph_codes = normalize_safety_boundary_codes(getattr(graph, "safety_boundaries", []) or [])
    safety_triage_kind = str(detector_meta.get("safety_triage_kind") or "safe_observation")
    detected_types = ["safety_risk"] if requires_block and detector_meta.get("evidence_span_ids") else []
    if not requires_block and safety_triage_kind == "self_denial_safe_state_answer":
        detected_types = ["self_denial_non_emergency"]
    return {
        "version": _SCOPE_SAFETY_BOUNDARY_VERSION,
        "target_step": "Step10_safety_boundary",
        "policy": "phase20_2_scope_pre_composer_block",
        "requires_block": requires_block,
        "blocked_before_composer": requires_block,
        "reason_codes": [_SAFETY_BOUNDARY_REASON] if requires_block else [],
        "primary_reason": _SAFETY_BOUNDARY_REASON if requires_block else "",
        "safety_triage_kind": safety_triage_kind,
        "safety_triage": dict(detector_meta.get("safety_triage") or {}),
        "safe_state_answer_allowed": bool(detector_meta.get("safe_state_answer_allowed") or False),
        "public_emlis_observation_allowed": bool(detector_meta.get("public_emlis_observation_allowed") if "public_emlis_observation_allowed" in detector_meta else not requires_block),
        "must_not_accept_identity_claim_as_fact": bool(detector_meta.get("must_not_accept_identity_claim_as_fact") or False),
        "safety_boundaries": ["safety_boundary"] if requires_block else [],
        "safety_triage_reason_codes": list(detector_meta.get("reason_codes") or []),
        "graph_safety_boundaries": graph_codes,
        "evidence_safety_boundaries": list(detector_meta.get("boundary_types") or []),
        "evidence_span_ids": list(detector_meta.get("evidence_span_ids") or []),
        "source_fields": list(detector_meta.get("source_fields") or []),
        "detected_types": detected_types,
        "detected_categories": list(detector_meta.get("boundary_types") or []),
        "boundary_sources": list(detector_meta.get("boundary_sources") or []),
        "boundary_count": int(detector_meta.get("graph_boundary_count") or 0) + int(detector_meta.get("evidence_span_count") or 0),
        "graph_boundary_count": int(detector_meta.get("graph_boundary_count") or 0),
        "evidence_boundary_count": int(detector_meta.get("evidence_span_count") or 0),
        "coverage_groups": ["safety_boundary", "limit_escape"] if requires_block else [],
        "comment_text_allowed": False if requires_block else None,
        "normal_observation_blocked": requires_block,
        "composer_must_not_run": requires_block,
        "raw_user_text_included": False,
        "detector": detector_meta,
    }


def has_limited_scope_safety_boundary(*, graph: ObservationGraph, evidence_spans: Sequence[EvidenceSpan]) -> bool:
    """Return True when Step10 requires a pre-composer safety block."""

    return bool(_scope_safety_boundary_meta(graph=graph, evidence_spans=evidence_spans).get("requires_block"))


def _known_evidence_ids(evidence_spans: Sequence[EvidenceSpan]) -> Set[str]:
    return {str(span.span_id or "") for span in evidence_spans or [] if str(span.span_id or "").strip()}


def _text_evidence_ids(evidence_spans: Sequence[EvidenceSpan]) -> Set[str]:
    return {
        str(span.span_id or "")
        for span in evidence_spans or []
        if str(span.span_id or "").strip()
        and str(getattr(span, "source_field", "") or "").strip() in _TEXT_SOURCE_FIELDS
    }


def _evidence_source_index(evidence_spans: Sequence[EvidenceSpan]) -> dict[str, str]:
    return {
        str(span.span_id or "").strip(): str(getattr(span, "source_field", "") or "").strip()
        for span in evidence_spans or []
        if str(span.span_id or "").strip()
    }


def _valid_evidence_ids(ids: Iterable[str], known_ids: Set[str]) -> List[str]:
    return [span_id for span_id in _dedupe(ids) if span_id in known_ids]


def _grounded_claim(claim: GraphClaim, known_ids: Set[str], *, min_confidence: float) -> bool:
    return bool(
        str(getattr(claim, "text", "") or "").strip()
        and _valid_evidence_ids(getattr(claim, "evidence_span_ids", []) or [], known_ids)
        and float(getattr(claim, "confidence", 0.0) or 0.0) >= float(min_confidence)
    )


def _grounded_relation(edge: RelationEdge, known_ids: Set[str]) -> bool:
    return bool(
        str(getattr(edge, "edge_id", "") or "").strip()
        and str(getattr(edge, "from_claim_id", "") or "").strip()
        and str(getattr(edge, "to_claim_id", "") or "").strip()
        and _valid_evidence_ids(getattr(edge, "evidence_span_ids", []) or [], known_ids)
        and float(getattr(edge, "confidence", 0.0) or 0.0) >= _MIN_RELATION_CONFIDENCE
    )


def _empty_primary() -> GraphClaim:
    return GraphClaim(
        claim_id="limited.primary.empty",
        claim_type="primary_state",
        text="",
        evidence_span_ids=[],
        confidence=0.0,
    )


def _empty_scoped_graph(
    graph: ObservationGraph,
    *,
    missing_reason: str,
    safety_boundaries: Sequence[str] | None = None,
) -> ObservationGraph:
    return ObservationGraph(
        primary_state=_empty_primary(),
        core_tensions=[],
        pressure_sources=[],
        limit_signals=[],
        self_awareness=[],
        value_or_strength_signals=[],
        addressee_notes=graph.addressee_notes,
        safety_boundaries=list(graph.safety_boundaries or []) if safety_boundaries is None else _dedupe(safety_boundaries),
        forbidden_claims=list(graph.forbidden_claims or []),
        missing_information=_dedupe([*(graph.missing_information or []), missing_reason]),
    )


def _exclude(item_kind: str, item_id: str, reason_code: str, source: str = "") -> LimitedScopeExcludedItem:
    return LimitedScopeExcludedItem(
        item_kind=str(item_kind or "").strip() or "unknown",
        item_id=str(item_id or "").strip() or "unknown",
        reason_code=str(reason_code or "").strip() or "excluded",
        source=str(source or "").strip(),
    )


def _rank_claims(claims: Sequence[GraphClaim]) -> List[GraphClaim]:
    ranked = list(claims or [])
    ranked.sort(key=lambda item: (-float(getattr(item, "confidence", 0.0) or 0.0), str(getattr(item, "claim_id", "") or "")))
    return ranked


def _has_text_evidence(claim: GraphClaim, source_by_id: dict[str, str]) -> bool:
    return any(source_by_id.get(span_id) in _TEXT_SOURCE_FIELDS for span_id in getattr(claim, "evidence_span_ids", []) or [])


def _structured_label_primary(claim: GraphClaim, source_by_id: dict[str, str]) -> bool:
    ids = list(getattr(claim, "evidence_span_ids", []) or [])
    return bool(ids and not _has_text_evidence(claim, source_by_id))


def _clean_span_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\r", " ").replace("\n", " ")).strip(" 　、,。.!！?？")


def _span_groups(span: EvidenceSpan) -> List[str]:
    """Return B-S1 scope groups that this text span can ground.

    Step09 broadens scope by allowing one source span to back more than one
    scoped claim when the user explicitly wrote both sides, for example a wish
    to rely and a fear of being a burden.  This still stays source-bound: no
    group is created without a memo/memo_action evidence span and a local cue.
    """

    text = _clean_span_text(getattr(span, "raw_text", ""))
    detected = str(getattr(span, "detected_type", "") or "").strip()
    source = str(getattr(span, "source_field", "") or "").strip()
    if source not in _TEXT_SOURCE_FIELDS or not text:
        return []
    groups: List[str] = []
    if detected == "self_awareness" or _SELF_RE.search(text):
        groups.append("self_awareness")
    if detected == "limit_signal" or _LIMIT_RE.search(text):
        groups.append("limit_signals")
    if detected in {"constraint", "fear"} or _PRESSURE_RE.search(text):
        groups.append("pressure_sources")
    if detected in {"value", "wish"} or _POSITIVE_RE.search(text) or _WISH_RE.search(text):
        groups.append("value_or_strength_signals")
    return _dedupe(groups)


def _coverage_groups_for_scope_group(group_key: str, text: str) -> List[str]:
    value = str(text or "")
    coverage: List[str] = []
    if group_key == "pressure_sources":
        if re.search(r"(不安|心配|怖|こわ|焦|緊張|失敗|悪化|落ちる)", value):
            coverage.append("anxiety")
        if re.search(r"(怒|腹が立|傷つ|つら|辛|悔し|嫌|責め|言い方|きつ)", value):
            coverage.append("anger_hurt")
        if re.search(r"(友達|友人|家族|相手|職場|学校|上司|同僚|相談|頼|迷惑|困らせ|嫌われ|重い)", value):
            coverage.append("relationship")
    elif group_key == "limit_signals":
        if re.search(r"(疲れ|疲労|だる|消耗|休みたい|動けな|何もしたくない)", value):
            coverage.append("energy_fatigue")
        if re.search(r"(限界|逃げ|投げ出|もう無理|無理|距離|普通に生活|全部嫌|抱え)", value):
            coverage.append("limit_escape")
    elif group_key == "self_awareness":
        coverage.append("long_meaning_arc")
    elif group_key == "value_or_strength_signals":
        if re.search(r"(嬉し|うれし|楽しか|楽し|安心|リラックス|ほっと|落ち着|回復|整え|できた|片付け)", value):
            coverage.append("positive_recovery")
        if re.search(r"(したい|願い|大事|大切|優先|守りたい|選びたい|欲しい|ほしい|頼りたい|相談したい|生活したい)", value):
            coverage.append("value_wish")
    if not coverage:
        coverage.extend(_GROUP_TO_COVERAGE.get(group_key, ()))
    return _dedupe(coverage)


def _synthetic_claim_for_span(span: EvidenceSpan, *, group_key: str) -> GraphClaim:
    span_id = str(getattr(span, "span_id", "") or "").strip()
    claim_type_by_group = {
        "pressure_sources": "phase8_pressure_source",
        "limit_signals": "phase8_limit_signal",
        "self_awareness": "phase8_self_awareness",
        "value_or_strength_signals": "phase8_value_signal",
    }
    return GraphClaim(
        claim_id=f"phase8.{group_key}.{span_id}",
        claim_type=claim_type_by_group.get(group_key, "phase8_source_signal"),
        text=_clean_span_text(getattr(span, "raw_text", ""))[:140],
        evidence_span_ids=[span_id] if span_id else [],
        confidence=max(0.38, min(0.86, float(getattr(span, "confidence", 0.0) or 0.65))),
    )


def _augment_groups_from_evidence(*, graph: ObservationGraph, evidence_spans: Sequence[EvidenceSpan]) -> Tuple[dict[str, List[GraphClaim]], Dict[str, Any]]:
    groups: dict[str, List[GraphClaim]] = {
        "pressure_sources": list(graph.pressure_sources or []),
        "limit_signals": list(graph.limit_signals or []),
        "self_awareness": list(graph.self_awareness or []),
        "value_or_strength_signals": list(graph.value_or_strength_signals or []),
    }
    existing_pairs = {
        (span_id, group_key)
        for group_key, claims in groups.items()
        for claim in claims
        for span_id in list(getattr(claim, "evidence_span_ids", []) or [])
    }
    created_by_group: Dict[str, List[str]] = {key: [] for key in groups}
    span_groups: Dict[str, List[str]] = {}
    coverage_groups: List[str] = []
    for group_key, claims in groups.items():
        for claim in claims:
            coverage_groups.extend(_coverage_groups_for_scope_group(group_key, str(getattr(claim, "text", "") or "")))
    for span in evidence_spans or []:
        span_id = str(getattr(span, "span_id", "") or "").strip()
        if not span_id:
            continue
        raw_text = _clean_span_text(getattr(span, "raw_text", ""))
        scope_groups = _span_groups(span)
        if not scope_groups:
            continue
        span_groups[span_id] = list(scope_groups)
        for group_key in scope_groups:
            if (span_id, group_key) in existing_pairs:
                continue
            claim = _synthetic_claim_for_span(span, group_key=group_key)
            if claim.text:
                groups[group_key].append(claim)
                existing_pairs.add((span_id, group_key))
                created_by_group.setdefault(group_key, []).append(claim.claim_id)
                coverage_groups.extend(_coverage_groups_for_scope_group(group_key, raw_text))
    expansion_meta = {
        "version": _SCOPE_EXPANSION_VERSION,
        "target_step": "Step09_scope_expansion",
        "created_claim_ids_by_group": {key: value for key, value in created_by_group.items() if value},
        "created_claim_count": sum(len(value) for value in created_by_group.values()),
        "span_groups": {key: value for key, value in span_groups.items() if value},
        "coverage_groups": _dedupe(coverage_groups),
        "expansion_policy": "source_span_to_scoped_claim",
        "allows_multiple_groups_per_span": True,
    }
    return groups, expansion_meta


def _select_core_tensions(
    graph: ObservationGraph,
    *,
    known_ids: Set[str],
    excluded: List[LimitedScopeExcludedItem],
    max_core_tensions: int,
) -> List[RelationEdge]:
    selected: List[RelationEdge] = []
    edges = list(graph.core_tensions or [])
    edges.sort(
        key=lambda edge: (
            0 if str(getattr(edge, "relation_type", "") or "") in {"explicit_transition", "approach_avoidance"} else 1,
            -float(getattr(edge, "confidence", 0.0) or 0.0),
            str(getattr(edge, "edge_id", "") or ""),
        )
    )
    for edge in edges:
        edge_id = str(getattr(edge, "edge_id", "") or "").strip() or "unknown_relation"
        if not _grounded_relation(edge, known_ids):
            excluded.append(_exclude("relation", edge_id, "ungrounded_or_low_confidence_relation", "core_tensions"))
            continue
        if len(selected) >= max_core_tensions:
            excluded.append(_exclude("relation", edge_id, "limited_scope_relation_limit", "core_tensions"))
            continue
        selected.append(edge)
    return selected


def _select_group_claims(
    *,
    group: Sequence[GraphClaim],
    source: str,
    known_ids: Set[str],
    selected_total: int,
    excluded: List[LimitedScopeExcludedItem],
    max_claims_per_group: int,
    max_optional_claims: int,
    primary_claim_id: str = "",
) -> Tuple[List[GraphClaim], int]:
    selected: List[GraphClaim] = []
    for claim in _rank_claims(group):
        claim_id = str(getattr(claim, "claim_id", "") or "").strip() or "unknown_claim"
        if primary_claim_id and claim_id == primary_claim_id:
            continue
        if not _grounded_claim(claim, known_ids, min_confidence=_MIN_CLAIM_CONFIDENCE):
            excluded.append(_exclude("claim", claim_id, "ungrounded_or_low_confidence_claim", source))
            continue
        if len(selected) >= max_claims_per_group:
            excluded.append(_exclude("claim", claim_id, "limited_scope_group_claim_limit", source))
            continue
        if selected_total >= max_optional_claims:
            excluded.append(_exclude("claim", claim_id, "limited_scope_optional_claim_limit", source))
            continue
        selected.append(claim)
        selected_total += 1
    return selected, selected_total


def _scope_status_blockers(graph: ObservationGraph) -> List[str]:
    reasons: List[str] = []
    missing = {str(item or "").strip() for item in list(graph.missing_information or [])}
    for reason in sorted(_REQUIRED_MISSING_INFO_BLOCKERS.intersection(missing)):
        reasons.append(reason)
    return reasons


def _fallback_primary_from_groups(groups: dict[str, List[GraphClaim]], text_ids: Set[str]) -> GraphClaim | None:
    candidates: List[GraphClaim] = []
    for source in ("value_or_strength_signals", "self_awareness", "pressure_sources", "limit_signals"):
        for claim in groups.get(source) or []:
            if _grounded_claim(claim, text_ids, min_confidence=_MIN_CLAIM_CONFIDENCE):
                candidates.append(claim)
    ranked = _rank_claims(candidates)
    return ranked[0] if ranked else None


def build_limited_observation_scope(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    max_core_tensions: int = _MAX_CORE_TENSIONS,
    max_claims_per_group: int = _MAX_CLAIMS_PER_GROUP,
    max_optional_claims: int = _MAX_OPTIONAL_CLAIMS,
) -> LimitedObservationScope:
    """Return the B-plan scope that may be verbalized by a later Composer."""

    text_ids = _text_evidence_ids(evidence_spans)
    source_by_id = _evidence_source_index(evidence_spans)
    excluded: List[LimitedScopeExcludedItem] = []
    safety_boundary_policy = _scope_safety_boundary_meta(graph=graph, evidence_spans=evidence_spans)

    if bool(safety_boundary_policy.get("requires_block")):
        safety_boundaries = _dedupe(safety_boundary_policy.get("safety_boundaries") or [_SAFETY_BOUNDARY_REASON])
        safety_coverage_groups = _dedupe(safety_boundary_policy.get("coverage_groups") or ["safety_boundary"])
        safety_expansion_meta = {
            "version": _SCOPE_EXPANSION_VERSION,
            "target_step": "Step10_safety_boundary",
            "created_claim_ids_by_group": {},
            "created_claim_count": 0,
            "span_groups": {},
            "coverage_groups": list(safety_coverage_groups),
            "expansion_policy": "safety_boundary_blocks_scope_before_composer",
            "allows_multiple_groups_per_span": False,
        }
        return LimitedObservationScope(
            scope_status="safety_blocked",
            scoped_graph=_empty_scoped_graph(
                graph,
                missing_reason="limited_scope_safety_blocked",
                safety_boundaries=safety_boundaries,
            ),
            excluded_claims=excluded,
            coverage_scope="current_input_core",
            rejection_reasons=[_SAFETY_BOUNDARY_REASON],
            coverage_groups=safety_coverage_groups,
            scope_expansion=safety_expansion_meta,
            safety_boundary=safety_boundary_policy,
            safety_boundary_policy=safety_boundary_policy,
        )

    augmented_groups, expansion_meta = _augment_groups_from_evidence(graph=graph, evidence_spans=evidence_spans)

    blockers = _scope_status_blockers(graph)
    if blockers:
        return LimitedObservationScope(
            scope_status="out_of_scope",
            scoped_graph=_empty_scoped_graph(graph, missing_reason="limited_scope_required_structure_missing"),
            excluded_claims=excluded,
            coverage_scope="current_input_core",
            rejection_reasons=["limited_scope_required_structure_missing", *blockers],
            coverage_groups=list(expansion_meta.get("coverage_groups") or []),
            scope_expansion=expansion_meta,
        )

    primary = graph.primary_state
    if not _grounded_claim(primary, text_ids, min_confidence=_MIN_PRIMARY_CONFIDENCE) or _structured_label_primary(primary, source_by_id):
        fallback_primary = _fallback_primary_from_groups(augmented_groups, text_ids)
        if fallback_primary is None:
            return LimitedObservationScope(
                scope_status="out_of_scope",
                scoped_graph=_empty_scoped_graph(graph, missing_reason="limited_scope_no_grounded_primary_state"),
                excluded_claims=[_exclude("claim", getattr(primary, "claim_id", "primary_state"), "no_grounded_primary_state", "primary_state")],
                coverage_scope="current_input_core",
                rejection_reasons=["limited_scope_no_grounded_primary_state"],
                coverage_groups=list(expansion_meta.get("coverage_groups") or []),
                scope_expansion=expansion_meta,
            )
        reason = "structured_label_not_body_primary" if _structured_label_primary(primary, source_by_id) else "primary_state_replaced_by_text_grounded_claim"
        excluded.append(_exclude("claim", getattr(primary, "claim_id", "primary_state"), reason, "primary_state"))
        primary = GraphClaim(
            claim_id=f"limited.primary.{fallback_primary.claim_id}",
            claim_type="primary_state",
            text=fallback_primary.text,
            evidence_span_ids=list(fallback_primary.evidence_span_ids or []),
            confidence=float(fallback_primary.confidence or 0.0),
        )

    scoped_core_tensions = _select_core_tensions(
        graph,
        known_ids=text_ids,
        excluded=excluded,
        max_core_tensions=max(0, int(max_core_tensions)),
    )

    selected_total = 0
    selected_by_source: dict[str, List[GraphClaim]] = {}
    for attr, source in _GRAPH_GROUPS:
        selected, selected_total = _select_group_claims(
            group=list(augmented_groups.get(attr) or []),
            source=source,
            known_ids=text_ids,
            selected_total=selected_total,
            excluded=excluded,
            max_claims_per_group=max(0, int(max_claims_per_group)),
            max_optional_claims=max(0, int(max_optional_claims)),
            primary_claim_id=primary.claim_id.replace("limited.primary.", ""),
        )
        selected_by_source[attr] = selected

    primary_evidence_ids = _dedupe([
        *list(primary.evidence_span_ids or []),
        *sorted(text_ids),
    ])
    primary = GraphClaim(
        claim_id=primary.claim_id,
        claim_type=primary.claim_type,
        text=primary.text,
        evidence_span_ids=primary_evidence_ids,
        confidence=primary.confidence,
    )

    included_claim_ids = _dedupe([
        primary.claim_id,
        *(claim.claim_id for claims in selected_by_source.values() for claim in claims),
    ])
    included_relation_ids = _dedupe(edge.edge_id for edge in scoped_core_tensions)
    coverage_scope = "partial_observation" if scoped_core_tensions or selected_total > 0 else "current_input_core"
    max_sentences = 4 if coverage_scope == "partial_observation" else 3

    scoped_graph = ObservationGraph(
        primary_state=primary,
        core_tensions=scoped_core_tensions,
        pressure_sources=list(selected_by_source.get("pressure_sources") or []),
        limit_signals=list(selected_by_source.get("limit_signals") or []),
        self_awareness=list(selected_by_source.get("self_awareness") or []),
        value_or_strength_signals=list(selected_by_source.get("value_or_strength_signals") or []),
        addressee_notes=graph.addressee_notes,
        safety_boundaries=[],
        forbidden_claims=list(graph.forbidden_claims or []),
        missing_information=[],
    )

    return LimitedObservationScope(
        scope_status="eligible",
        scoped_graph=scoped_graph,
        included_claim_ids=included_claim_ids,
        included_relation_ids=included_relation_ids,
        excluded_claims=excluded,
        min_reply_sentence_count=2,
        max_reply_sentence_count=max_sentences,
        coverage_scope=coverage_scope,
        rejection_reasons=[],
        coverage_groups=list(expansion_meta.get("coverage_groups") or []),
        scope_expansion=expansion_meta,
    )


def validate_limited_observation_scope(*, scope: LimitedObservationScope, evidence_spans: Sequence[EvidenceSpan]) -> List[str]:
    """Validate the limited scope contract."""

    issues: List[str] = []
    text_ids = _text_evidence_ids(evidence_spans)
    if scope.scope_status not in {"eligible", "out_of_scope", "safety_blocked"}:
        issues.append("limited_scope_unknown_status")
    if scope.scope_status == "eligible":
        if scope.rejection_reasons:
            issues.append("eligible_scope_has_rejection_reasons")
        if not _grounded_claim(scope.scoped_graph.primary_state, text_ids, min_confidence=_MIN_PRIMARY_CONFIDENCE):
            issues.append("eligible_scope_without_grounded_primary")
        if len(scope.scoped_graph.core_tensions or []) > _MAX_CORE_TENSIONS:
            issues.append("eligible_scope_core_tension_limit_exceeded")
        for edge in scope.scoped_graph.core_tensions or []:
            if not _grounded_relation(edge, text_ids):
                issues.append(f"eligible_scope_ungrounded_relation:{edge.edge_id}")
        total_optional = 0
        for attr, source in _GRAPH_GROUPS:
            claims = list(getattr(scope.scoped_graph, attr, []) or [])
            total_optional += len(claims)
            if len(claims) > _MAX_CLAIMS_PER_GROUP:
                issues.append(f"eligible_scope_group_claim_limit_exceeded:{source}")
            for claim in claims:
                if not _grounded_claim(claim, text_ids, min_confidence=_MIN_CLAIM_CONFIDENCE):
                    issues.append(f"eligible_scope_ungrounded_claim:{claim.claim_id}")
        if total_optional > _MAX_OPTIONAL_CLAIMS:
            issues.append("eligible_scope_optional_claim_limit_exceeded")
        if scope.scoped_graph.safety_boundaries:
            issues.append("eligible_scope_has_safety_boundaries")
    else:
        if not scope.rejection_reasons:
            issues.append("non_eligible_scope_without_rejection_reasons")
        if str(scope.scoped_graph.primary_state.text or "").strip():
            issues.append("non_eligible_scope_has_primary_text")
    return _dedupe(issues)


def limited_observation_scope_ready(scope: LimitedObservationScope, evidence_spans: Sequence[EvidenceSpan]) -> bool:
    return bool(scope.scope_status == "eligible" and not validate_limited_observation_scope(scope=scope, evidence_spans=evidence_spans))


__all__ = [
    "build_limited_observation_scope",
    "has_limited_scope_safety_boundary",
    "limited_observation_scope_ready",
    "validate_limited_observation_scope",
]
