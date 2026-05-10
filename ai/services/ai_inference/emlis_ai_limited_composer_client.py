# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cocolon internal limited Composer client for EmlisAI B-plan.

Phase 2 implements the synchronous ConversationComposerClient contract only. It
consumes a scoped ObservationGraph payload and EvidenceSpan payloads, returns a
schema-shaped candidate, and does not connect itself to the normal render path.
It does not call external AI, read public knowledge, or return fallback text.
"""

import re
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

_RESPONSE_SCHEMA_VERSION = "emlis.composer.response.v1"
_COMPOSER_MODEL = "cocolon_limited_composer.v1"
_GENERATION_METHOD = "scoped_graph_evidence_composer"
_GENERATION_SCOPE = "scoped_graph_only"
_ALLOWED_SOURCE = "ai_generated"
_UNAVAILABLE_SOURCE = "unavailable"
_MAX_FRAGMENT_CHARS = 84
_MIN_BODY_LINES = 2
_MAX_BODY_LINES = 4

_SPACE_RE = re.compile(r"\s+")
_SENTENCE_END_RE = re.compile(r"[。！？!?]+$")
_PIPE_SPLIT_RE = re.compile(r"\s*\|\s*")
_TRAILING_MARKER_RE = re.compile(r"[、,]?と$")

_FORBIDDEN_SURFACES = (
    "そこには",
    "もありました",
    "も含まれていました",
    "受け取りました",
    "と思います",
    "として見ています",
    "一緒に見ます",
    "今の私は",
    "あなたは",
    "あなたの",
    "あなたが",
    "あなたに",
    "入力全体では",
    "言葉の流れには",
    "外からは見えにくい緊張",
    "まだ決めきれない揺れ",
    "急いで片づけず",
)

_RELATION_WORD_BY_TYPE: Dict[str, Tuple[str, str]] = {
    "limit_tension": ("重なって", "います"),
    "explicit_transition": ("つながって", "います"),
    "coexistence": ("同時に", "あります"),
    "coexisting": ("同時に", "あります"),
    "constraint": ("つながって", "います"),
    "pressure": ("つながって", "います"),
}
_DEFAULT_RELATION_WORD = ("同じ中", "にあります")
_GROUP_KEYS = (
    "pressure_sources",
    "limit_signals",
    "self_awareness",
    "value_or_strength_signals",
)
_MARKER_NAMES = (
    "_line_primary",
    "_line_pressure",
    "_line_limit",
    "_line_closing",
    "closing_template",
    "role_template",
    "static_observation_text",
    "fallback_observation",
)


class CocolonLimitedComposerClient:
    """Generate a limited Emlis candidate from a scoped payload."""

    composer_model = _COMPOSER_MODEL

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(payload, Mapping):
            return _unavailable_response("limited_composer_invalid_payload")

        scope = _scope_meta(payload)
        coverage_scope = _clean(scope.get("coverage_scope")) or _coverage_scope(_graph(payload))
        if _clean(scope.get("scope_status")) and _clean(scope.get("scope_status")) != "eligible":
            return _unavailable_response("limited_scope_not_eligible", coverage_scope=coverage_scope)

        graph = _graph(payload)
        if not graph:
            return _unavailable_response("limited_composer_missing_graph", coverage_scope=coverage_scope)
        if list(graph.get("safety_boundaries") or []):
            return _unavailable_response("limited_composer_safety_boundary", coverage_scope=coverage_scope)
        if list(graph.get("missing_information") or []):
            return _unavailable_response("limited_composer_missing_information", coverage_scope=coverage_scope)

        evidence_items = [item for item in list(payload.get("evidence_spans") or []) if isinstance(item, Mapping)]
        evidence_by_id = _evidence_by_id(evidence_items)
        if not evidence_by_id:
            return _unavailable_response("limited_composer_missing_evidence", coverage_scope=coverage_scope)

        primary = graph.get("primary_state") if isinstance(graph.get("primary_state"), Mapping) else {}
        primary_ids = _ids(primary.get("evidence_span_ids"))
        primary_parts = _evidence_phrases(primary_ids, evidence_by_id, backup_text=primary.get("text"))
        if not primary_parts:
            return _unavailable_response("limited_composer_missing_primary_evidence", coverage_scope=coverage_scope)

        relation = _first_relation(graph.get("core_tensions"))
        optional = _optional_phrases(graph=graph, evidence_by_id=evidence_by_id, used_ids=primary_ids)
        lines = _compose_lines(
            payload=payload,
            primary_parts=primary_parts,
            optional_parts=optional,
            relation=relation,
        )
        min_body, max_body = _body_limits(scope)
        greeting_count = 1 if lines and "Emlis" in lines[0] else 0
        body_lines = lines[greeting_count:][:max_body]
        lines = lines[:greeting_count] + body_lines
        if len(body_lines) < min_body:
            return _unavailable_response("limited_composer_minimum_body_not_met", coverage_scope=coverage_scope)

        comment_text = "\n".join(line for line in lines if line).strip()
        if not comment_text:
            return _unavailable_response("limited_composer_empty_candidate", coverage_scope=coverage_scope)

        matched_forbidden = _matched_forbidden_surfaces(payload=payload, text=comment_text)
        if matched_forbidden:
            return _unavailable_response(
                "limited_composer_forbidden_surface",
                matched_forbidden=matched_forbidden,
                coverage_scope=coverage_scope,
            )

        used_evidence_ids = _dedupe([
            *primary_ids,
            *[item[0] for item in optional],
            *_ids(relation.get("evidence_span_ids") if relation else []),
        ])
        used_evidence_ids = [span_id for span_id in used_evidence_ids if span_id in evidence_by_id]
        if not used_evidence_ids:
            return _unavailable_response("limited_composer_no_used_evidence", coverage_scope=coverage_scope)

        return {
            "schema_version": _RESPONSE_SCHEMA_VERSION,
            "response_schema_version": _RESPONSE_SCHEMA_VERSION,
            "composer_source": _ALLOWED_SOURCE,
            "status": "generated",
            "composer_model": _COMPOSER_MODEL,
            "generation_method": _GENERATION_METHOD,
            "generation_scope": _GENERATION_SCOPE,
            "fixed_string_renderer_used": False,
            "coverage_scope": coverage_scope,
            "comment_text": comment_text,
            "used_evidence_span_ids": used_evidence_ids,
            "used_claim_ids": _used_claim_ids(graph),
            "used_relation_ids": _used_relation_ids(graph),
            "confidence": _confidence(primary=primary, optional_count=len(optional), relation=relation),
            "composer_meta": {
                "limited_composer": True,
                "generation_scope": _GENERATION_SCOPE,
                "external_ai_used": False,
                "body_line_count": len(body_lines),
            },
        }


def _scope_meta(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("limited_observation_scope", "limited_scope", "scope_meta", "scope"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _graph(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    value = payload.get("observation_graph")
    return value if isinstance(value, Mapping) else {}


def _unavailable_response(reason: str, *, matched_forbidden: Sequence[str] | None = None, coverage_scope: str = "") -> Dict[str, Any]:
    reasons = [str(reason or "limited_composer_unavailable").strip()]
    if matched_forbidden:
        reasons.append("limited_composer_forbidden_output_surface")
    return {
        "schema_version": _RESPONSE_SCHEMA_VERSION,
        "response_schema_version": _RESPONSE_SCHEMA_VERSION,
        "composer_source": _UNAVAILABLE_SOURCE,
        "status": "unavailable",
        "composer_model": _COMPOSER_MODEL,
        "generation_method": _GENERATION_METHOD,
        "generation_scope": _GENERATION_SCOPE,
        "fixed_string_renderer_used": False,
        "coverage_scope": coverage_scope or "current_input_core",
        "comment_text": "",
        "used_evidence_span_ids": [],
        "used_claim_ids": [],
        "used_relation_ids": [],
        "confidence": 0.0,
        "rejection_reasons": _dedupe(reasons),
        "matched_forbidden_surfaces": list(matched_forbidden or []),
        "composer_meta": {
            "limited_composer": True,
            "generation_scope": _GENERATION_SCOPE,
            "external_ai_used": False,
        },
    }


def _clean(value: Any, *, limit: int = _MAX_FRAGMENT_CHARS) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()
    text = _SENTENCE_END_RE.sub("", text).strip(" 　、,。.!！?？『』\"'")
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(" 　、,。.!！?？")
    return text


def _phrase(value: Any, *, limit: int = 72) -> str:
    return _TRAILING_MARKER_RE.sub("", _clean(value, limit=limit)).strip(" 　、,。.!！?？")


def _anchor_phrase_from_span(span: Mapping[str, Any], *, limit: int = 28) -> str:
    """Return a short literal anchor from a source span, not a full raw quote.

    The phrase is cut from the user's own wording so the Grounding Judge can
    still match it, while long raw clauses are not pasted into the observation.
    """

    raw = _phrase(span.get("raw_text"), limit=180)
    if not raw:
        return ""
    if len(raw) <= limit:
        return raw
    candidates: List[str] = []
    for sep in ("から", "けど", "だけど", "でも", "ときに", "ことが"):
        if sep in raw:
            left, right = raw.split(sep, 1)
            left = left.strip(" 　、,。.!！?？")
            right = right.strip(" 　、,。.!！?？")
            if len(left) >= 4:
                candidates.append(left)
            if len(right) >= 4:
                candidates.append(right)
    candidates.append(raw)
    for candidate in candidates:
        text = _phrase(candidate, limit=limit)
        if text:
            return text
    return _phrase(raw, limit=limit)


def _ids(values: Any) -> List[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    return _dedupe(str(item or "").strip() for item in values if str(item or "").strip())


def _dedupe(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out


def _evidence_by_id(items: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    out: Dict[str, Mapping[str, Any]] = {}
    for item in items:
        span_id = str(item.get("span_id") or "").strip()
        if span_id:
            out[span_id] = item
    return out


def _evidence_phrases(ids: Sequence[str], evidence_by_id: Mapping[str, Mapping[str, Any]], *, backup_text: Any = None) -> List[str]:
    out: List[str] = []
    for span_id in ids:
        span = evidence_by_id.get(span_id)
        if not span:
            continue
        text = _anchor_phrase_from_span(span, limit=26)
        if text and text not in out:
            out.append(text)
    if out:
        return out[:3]
    for part in _PIPE_SPLIT_RE.split(str(backup_text or "")):
        text = _phrase(part, limit=80)
        if text and text not in out:
            out.append(text)
    return out[:3]


def _first_relation(value: Any) -> Dict[str, Any]:
    relations = [item for item in list(value or []) if isinstance(item, Mapping)]
    if not relations:
        return {}
    relations.sort(key=lambda item: (-float(item.get("confidence") or 0.0), str(item.get("edge_id") or "")))
    return dict(relations[0])


def _relation_words(relation: Mapping[str, Any]) -> Tuple[str, str]:
    relation_type = str(relation.get("relation_type") or "").strip()
    return _RELATION_WORD_BY_TYPE.get(relation_type, _DEFAULT_RELATION_WORD)


def _finish(value: Any) -> str:
    text = _clean(value, limit=180).strip(" 　、,。.!！?？")
    return "".join([text, "。"]) if text else ""


def _join_two(left: str, right: str, relation: Mapping[str, Any]) -> str:
    word, tail = _relation_words(relation)
    left_text = _phrase(left, limit=78)
    right_text = _phrase(right, limit=78)
    if not left_text:
        return _finish(right_text)
    if not right_text or right_text == left_text:
        return _finish(left_text)
    return _finish("".join([left_text, "、", right_text, "が", word, tail]))


def _greeting(payload: Mapping[str, Any]) -> str:
    addressee = payload.get("addressee") if isinstance(payload.get("addressee"), Mapping) else {}
    call = _clean(addressee.get("display_name_call"), limit=28)
    greeting = _clean(addressee.get("greeting_text"), limit=32)
    if not greeting:
        greeting = "".join(["Emlis", "です"])
    if call and call not in greeting:
        return _finish("".join([call, "、", greeting]))
    return _finish(greeting)


def _optional_phrases(*, graph: Mapping[str, Any], evidence_by_id: Mapping[str, Mapping[str, Any]], used_ids: Sequence[str]) -> List[Tuple[str, str, str]]:
    selected: List[Tuple[str, str, str]] = []
    used = set(_ids(used_ids))
    for group_key in _GROUP_KEYS:
        claims = [item for item in list(graph.get(group_key) or []) if isinstance(item, Mapping)]
        claims.sort(key=lambda item: (-float(item.get("confidence") or 0.0), str(item.get("claim_id") or "")))
        for claim in claims:
            for span_id in _ids(claim.get("evidence_span_ids")):
                if span_id in used or span_id not in evidence_by_id:
                    continue
                text = _anchor_phrase_from_span(evidence_by_id[span_id], limit=22)
                if not text:
                    continue
                selected.append((span_id, text, group_key))
                used.add(span_id)
                break
            if selected and selected[-1][2] == group_key:
                break
        if len(selected) >= 2:
            break
    return selected[:2]


def _compose_lines(*, payload: Mapping[str, Any], primary_parts: Sequence[str], optional_parts: Sequence[Tuple[str, str, str]], relation: Mapping[str, Any]) -> List[str]:
    lines: List[str] = []
    greeting = _greeting(payload)
    if greeting:
        lines.append(greeting)
    if len(primary_parts) >= 2:
        lines.append(_join_two(primary_parts[0], primary_parts[1], relation))
    else:
        lines.append(_finish(primary_parts[0]))
    support_texts = [item[1] for item in optional_parts if item[1]]
    support_relation = {"relation_type": "explicit_transition"}
    if len(support_texts) >= 2:
        lines.append(_join_two(support_texts[0], support_texts[1], support_relation))
    elif support_texts:
        anchor = support_texts[0]
        primary_anchor = primary_parts[0] if primary_parts else ""
        lines.append(_join_two(primary_anchor, anchor, support_relation) if primary_anchor and primary_anchor != anchor else _finish(anchor))
    return [line for line in lines if line][:5]


def _body_limits(scope: Mapping[str, Any]) -> Tuple[int, int]:
    try:
        min_count = int(scope.get("min_reply_sentence_count") or _MIN_BODY_LINES)
    except Exception:
        min_count = _MIN_BODY_LINES
    try:
        max_count = int(scope.get("max_reply_sentence_count") or _MAX_BODY_LINES)
    except Exception:
        max_count = _MAX_BODY_LINES
    return max(1, min(3, min_count)), max(2, min(4, max_count))


def _matched_forbidden_surfaces(*, payload: Mapping[str, Any], text: str) -> List[str]:
    contract = payload.get("composition_contract") if isinstance(payload.get("composition_contract"), Mapping) else {}
    configured = [str(item or "").strip() for item in list(contract.get("forbidden_output_surfaces") or [])]
    patterns = _dedupe([*_FORBIDDEN_SURFACES, *configured])
    return [surface for surface in patterns if surface and surface in text]


def _coverage_scope(graph: Mapping[str, Any]) -> str:
    if list(graph.get("core_tensions") or []) or any(list(graph.get(key) or []) for key in _GROUP_KEYS):
        return "partial_observation"
    return "current_input_core"


def _used_claim_ids(graph: Mapping[str, Any]) -> List[str]:
    ids: List[str] = []
    primary = graph.get("primary_state") if isinstance(graph.get("primary_state"), Mapping) else {}
    primary_id = str(primary.get("claim_id") or "").strip()
    if primary_id:
        ids.append(primary_id)
    for group_key in _GROUP_KEYS:
        for claim in list(graph.get(group_key) or []):
            if isinstance(claim, Mapping):
                claim_id = str(claim.get("claim_id") or "").strip()
                if claim_id:
                    ids.append(claim_id)
    return _dedupe(ids)


def _used_relation_ids(graph: Mapping[str, Any]) -> List[str]:
    return _dedupe(str(edge.get("edge_id") or "").strip() for edge in list(graph.get("core_tensions") or []) if isinstance(edge, Mapping))


def _confidence(*, primary: Mapping[str, Any], optional_count: int, relation: Mapping[str, Any]) -> float:
    base = float(primary.get("confidence") or 0.0) if isinstance(primary, Mapping) else 0.0
    bonus = 0.04 if relation else 0.0
    bonus += min(0.08, 0.03 * max(0, int(optional_count)))
    return round(max(0.0, min(0.94, base + bonus)), 3)


def audit_limited_composer_contract() -> List[str]:
    issues: List[str] = []
    for marker in _MARKER_NAMES:
        if marker in globals():
            issues.append(marker)
    return issues


__all__ = ["CocolonLimitedComposerClient", "audit_limited_composer_contract"]
