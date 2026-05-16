# -*- coding: utf-8 -*-
from __future__ import annotations

"""Grounding judge for EmlisAI output.

Phase 4 adds scoped grounding support for the Limited Composer path.  When a
B-plan scoped graph is supplied, this judge validates the text against that
scoped graph only and does not require unused claims from the full graph to be
reflected.  Evidence can also be restricted to the scoped graph's evidence ids
so excluded full-graph material cannot silently ground the generated text.

Step 6 adds binding-aware grounding.  When a Limited Composer candidate carries
SentenceBinding metadata, the judge can validate generated sentences against the
composer-declared evidence / phrase / relation binding instead of relying only
on surface overlap.  This is additive and fail-closed: unsupported diagnosis,
overclaim, out-of-scope evidence, and missing declared evidence still reject.

Step 8 extends the judge for Complete Composer initial-version grounding.
Surface Realizer 2.0 can pass sanitized grounding_input rows, and the judge then
checks sentence_id, used_evidence_span_ids, used_phrase_unit_ids, and
relation_type per sentence.  Complete mode is stricter than the Limited path but
still does not change DB/API/RN/public response shape.
"""

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from emlis_ai_types import EvidenceSpan, GroundingReport, GroundingSentenceClaim, ObservationGraph

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_FUNCTION_WORD_RE = re.compile(
    r"^(入力全体|Emlis|言葉|気持ち|状態|場所|重さ|力|願い|自覚|負荷|部分|反応|感覚|中|二つ|その二つ|今|今回)$"
)
_RELATION_RE = re.compile(
    r"(同じ場所|同じ中|並んで|せめぎ合|重なって|だけではなく|一方|簡単には|その中でも|そこに|離れていない|二つの間|つながって|同時に)"
)
_GENERIC_RELATION_SENTENCE_RE = re.compile(r"(その二つ|二つの間|同じ場所|同じ中|並んで|重なって|離れていない|同時に)")
_OVERCLAIM_RE = re.compile(r"(本当は|本当の願い|頼りたい|愛されたい|前向き|強い人|性格|診断|病気|治療|医療|弱さではなく)")
# Step14: A-plan readiness guard surfaces.  These are rejection signatures,
# not generation rules.
_STEP14_DIAGNOSIS_LIKE_RE = re.compile(r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|自律神経|依存症|PTSD|医療|心理療法|心理学的")
_STEP14_PERSONALITY_LABEL_RE = re.compile(r"(?:あなた|その人|本人)(?:は|の)(?:[^。！？!?]{0,28})?(?:性格|人格|本質|タイプ|こういう人|弱い人|強い人|怠け|甘え)")
_STEP14_GENERAL_KNOWLEDGE_RE = re.compile(r"(?:一般的に|普通は|多くの人|誰でも|人はみんな|よくあること|心理学的には|科学的には|医学的には)(?:[^。！？!?]{0,48})(?:です|あります|なります|と言われています)")
_STEP14_ADVICE_ASSERTION_RE = re.compile(r"(?:必要があります|すべきです|するべきです|しなければなりません|正解です|間違いです)")
_GREETING_SENTENCE_RE = re.compile(r"^[^。！？!?\n]{1,40}さん、(?:こんにちは|おはようございます|こんばんは)[。.!！]?$")

_STEP6_BINDING_AWARE_GROUNDING_VERSION = "emlis.binding_aware_grounding.v1"
_STEP6_BINDING_AWARE_TARGET_STEP = "6_binding_aware_grounding"
_COMPLETE_BINDING_AWARE_GROUNDING_VERSION = "emlis.complete_binding_aware_grounding.v1"
_COMPLETE_BINDING_AWARE_TARGET_STEP = "Step8_Binding_aware_Grounding"
# Backward-friendly aliases for tests/integration code that names the step explicitly.
_STEP8_COMPLETE_BINDING_AWARE_GROUNDING_VERSION = _COMPLETE_BINDING_AWARE_GROUNDING_VERSION
_STEP8_COMPLETE_BINDING_AWARE_TARGET_STEP = _COMPLETE_BINDING_AWARE_TARGET_STEP

_REJECTION_BINDING_DECLARED_EVIDENCE_NOT_FOUND = "binding_declared_evidence_not_found"
_REJECTION_BINDING_DECLARED_EVIDENCE_OUT_OF_SCOPE = "binding_declared_evidence_out_of_scope"
_REJECTION_BINDING_TEXT_MISMATCH = "binding_sentence_text_mismatch"
_REJECTION_COMPLETE_BINDING_MISSING = "complete_sentence_binding_missing"
_REJECTION_COMPLETE_BINDING_EVIDENCE_IDS_MISSING = "complete_binding_evidence_span_ids_missing"
_REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING = "complete_binding_phrase_unit_ids_missing"
_REJECTION_COMPLETE_BINDING_PHRASE_UNIT_IDS_MISSING = _REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING
_REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING = "complete_binding_relation_type_missing"
# Backward-friendly aliases for Step 8 tests and future gate code.
_REJECTION_COMPLETE_PHRASE_BINDING_MISSING = _REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING
_REJECTION_COMPLETE_RELATION_BINDING_MISSING = _REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING
_REJECTION_COMPLETE_RELATION_NOT_EXPRESSED = "relation_not_expressed"
_REJECTION_COMPLETE_OVER_ECHO = "over_echo"

_COMPLETE_RELATION_TEXT_PATTERNS: Dict[str, re.Pattern[str]] = {
    "contrast": re.compile(r"別々|一方|片方|並んで|寄らず|同じ場所|せめぎ"),
    "coexistence": re.compile(r"同時|同じ時間|重な|片方だけ|同じ中|並んで"),
    "pressure": re.compile(r"圧力|負荷|重さ|限界|強く|前面"),
    "approach_avoidance": re.compile(r"近づ|止ま|避け|両方|一方向|決まりきって"),
    "recovery": re.compile(r"回復|戻|取り直|それでも|消えず"),
    "residue": re.compile(r"残|余韻|あと|終わったあと"),
}


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _normalize(text: Any) -> str:
    return re.sub(r"[\s、。.!！?？「」『』（）()]+", "", str(text or "")).strip()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _tokens(values: Any) -> List[str]:
    out: List[str] = []
    for value in _as_list(values):
        token = _clean(value)
        if token and token not in out:
            out.append(token)
    return out


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _char_ngrams(text: Any, n: int = 3) -> Set[str]:
    compact = _normalize(text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def _ngram_overlap(a: Any, b: Any) -> float:
    aa = _char_ngrams(a)
    bb = _char_ngrams(b)
    if not aa or not bb:
        return 0.0
    return len(aa.intersection(bb)) / max(1, min(len(aa), len(bb)))


def _terms(text: Any) -> Set[str]:
    cleaned = re.sub(r"[「」『』、。.!！?？\s]", " ", str(text or ""))
    chunks = [c.strip() for c in re.split(r"[ /・,，]+", cleaned) if c.strip()]
    out: Set[str] = set()
    for chunk in chunks:
        if _FUNCTION_WORD_RE.match(chunk):
            continue
        if len(chunk) >= 2:
            out.add(chunk[:18])
        # Add compact substrings for long Japanese clauses.
        if len(chunk) >= 6:
            out.add(chunk[:6])
            out.add(chunk[-6:])
    return out


def _span_matches_sentence(sentence: str, span: EvidenceSpan) -> bool:
    raw = str(span.raw_text or "").strip()
    if not raw:
        return False
    sentence_norm = _normalize(sentence)
    raw_norm = _normalize(raw)
    if len(raw_norm) >= 3 and (raw_norm in sentence_norm or sentence_norm in raw_norm):
        return True
    sentence_terms = _terms(sentence)
    span_terms = _terms(raw)
    if sentence_terms.intersection(span_terms):
        return True
    return _ngram_overlap(sentence, raw) >= 0.18


def _step14_unbacked_reason(sentence: str, evidence_text: str) -> str:
    """Return a Step14 reason when a natural sentence completes beyond evidence."""

    if _STEP14_DIAGNOSIS_LIKE_RE.search(sentence) and not _STEP14_DIAGNOSIS_LIKE_RE.search(evidence_text):
        return "unsupported_diagnosis_like"
    if _STEP14_PERSONALITY_LABEL_RE.search(sentence) and not _STEP14_PERSONALITY_LABEL_RE.search(evidence_text):
        return "unsupported_personality_label"
    if _STEP14_GENERAL_KNOWLEDGE_RE.search(sentence) and not _STEP14_GENERAL_KNOWLEDGE_RE.search(evidence_text):
        return "unsupported_general_knowledge_completion"
    if _STEP14_ADVICE_ASSERTION_RE.search(sentence) and not _STEP14_ADVICE_ASSERTION_RE.search(evidence_text):
        return "unsupported_advice_assertion"
    return ""


def _dedupe(values: Iterable[Any] | Any | None) -> List[str]:
    out: List[str] = []
    if values is None:
        return out
    if isinstance(values, (str, bytes)):
        src: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        src = values
    else:
        src = [values]
    for value in src:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out


def _relation_edge_evidence(graph: ObservationGraph) -> List[str]:
    out: List[str] = []
    for edge in graph.core_tensions:
        for span_id in edge.evidence_span_ids:
            if span_id and span_id not in out:
                out.append(span_id)
    return out


def _graph_evidence_ids(graph: ObservationGraph) -> List[str]:
    out: List[str] = []
    primary = getattr(graph, "primary_state", None)
    for span_id in list(getattr(primary, "evidence_span_ids", []) or []):
        if span_id and span_id not in out:
            out.append(span_id)
    for group in (graph.pressure_sources, graph.limit_signals, graph.self_awareness, graph.value_or_strength_signals):
        for claim in group:
            for span_id in claim.evidence_span_ids:
                if span_id and span_id not in out:
                    out.append(span_id)
    for edge in graph.core_tensions:
        for span_id in edge.evidence_span_ids:
            if span_id and span_id not in out:
                out.append(span_id)
    return out


def _filter_evidence_spans(
    evidence_spans: Sequence[EvidenceSpan],
    *,
    allowed_evidence_span_ids: Optional[Sequence[str]],
) -> tuple[List[EvidenceSpan], List[str], List[str]]:
    all_ids = [str(span.span_id or "") for span in evidence_spans or [] if str(span.span_id or "").strip()]
    allowed_ids = _dedupe(allowed_evidence_span_ids or [])
    if not allowed_ids:
        return list(evidence_spans or []), [], []
    allowed_set = set(allowed_ids)
    scoped_spans = [span for span in evidence_spans or [] if str(span.span_id or "").strip() in allowed_set]
    ignored_ids = [span_id for span_id in all_ids if span_id not in allowed_set]
    return scoped_spans, allowed_ids, ignored_ids


def _binding_text(row: Mapping[str, Any]) -> str:
    return _clean(
        row.get("text")
        or row.get("sentence")
        or row.get("candidate_sentence")
        or row.get("surface_text")
        or row.get("display_text")
    )


def _binding_declared_evidence_ids(row: Mapping[str, Any]) -> List[str]:
    return _dedupe(row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or row.get("declared_evidence_span_ids") or [])


def _binding_declared_phrase_ids(row: Mapping[str, Any]) -> List[str]:
    return _dedupe(row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or row.get("declared_phrase_unit_ids") or [])


def _binding_rows_from_meta(binding_meta: Any) -> List[Mapping[str, Any]]:
    """Extract sentence binding rows from Limited and Complete meta shapes."""

    candidates: List[Mapping[str, Any]] = []

    def is_row_like(item: Mapping[str, Any]) -> bool:
        if not isinstance(item, Mapping):
            return False
        has_sentence_id = bool(_clean(item.get("sentence_id") or item.get("id")))
        has_binding = bool(
            item.get("used_evidence_span_ids")
            or item.get("evidence_span_ids")
            or item.get("declared_evidence_span_ids")
            or item.get("used_phrase_unit_ids")
            or item.get("phrase_unit_ids")
            or item.get("declared_phrase_unit_ids")
            or item.get("relation_type")
            or item.get("declared_relation_type")
        )
        has_text = bool(_binding_text(item))
        return has_sentence_id and (has_binding or has_text)

    def extend_from_value(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, (list, tuple, set)):
            for child in value:
                extend_from_value(child)
            return
        if not isinstance(value, Mapping):
            return

        for key in (
            "sentence_binding_bundle",
            "binding_bundle",
            "binding",
            "source_sentence_binding_bundle",
            "grounding_input",
            "complete_grounding_input",
            "surface_grounding_input",
        ):
            nested = value.get(key)
            if isinstance(nested, Mapping) or isinstance(nested, (list, tuple, set)):
                extend_from_value(nested)

        for key in (
            "sentence_bindings",
            "bindings",
            "items",
            "binding_rows_sanitized",
            "surface_lines",
            "surface_component_rows",
            "grounding_rows",
            "complete_grounding_rows",
        ):
            nested = value.get(key)
            if isinstance(nested, Mapping):
                extend_from_value(nested.get("bindings") or nested.get("sentence_bindings") or nested.get("items") or nested)
            else:
                extend_from_value(nested)

        if is_row_like(value):
            candidates.append(value)

    extend_from_value(binding_meta)

    rows: List[Mapping[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(candidates, start=1):
        sentence_id = _clean(item.get("sentence_id") or item.get("id") or f"s{index}")
        text_key = _normalize(_binding_text(item))
        ids_key = ",".join(_binding_declared_evidence_ids(item))
        key = f"{sentence_id}:{text_key}:{ids_key}" or f"row-{index}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(item)
    return rows


def _binding_for_sentence(
    rows: Sequence[Mapping[str, Any]],
    *,
    sentence: str,
    body_index: int,
) -> tuple[Mapping[str, Any] | None, str]:
    if not rows:
        return None, ""
    sentence_norm = _normalize(sentence)
    for row in rows:
        text = _binding_text(row)
        if text and (_normalize(text) == sentence_norm or _ngram_overlap(sentence, text) >= 0.72):
            return row, "text"
    if 0 <= body_index < len(rows):
        return rows[body_index], "order"
    return None, ""


def _binding_support(
    row: Mapping[str, Any] | None,
    *,
    evidence_by_id: Mapping[str, EvidenceSpan],
    allowed_ids: Sequence[str],
    require_phrase_unit_ids: bool = False,
    require_relation_type: bool = False,
) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        reasons: List[str] = []
        if require_phrase_unit_ids or require_relation_type:
            reasons.append(_REJECTION_COMPLETE_BINDING_MISSING)
        return {
            "binding_used": False,
            "sentence_id": "",
            "line_role": "",
            "declared_evidence_span_ids": [],
            "declared_phrase_unit_ids": [],
            "declared_relation_type": "",
            "supported_evidence_span_ids": [],
            "rejection_reasons": reasons,
        }

    allowed_set = set(_dedupe(allowed_ids or []))
    all_ids = set(evidence_by_id.keys())
    declared_evidence = _binding_declared_evidence_ids(row)
    declared_phrase = _binding_declared_phrase_ids(row)
    relation_type = _clean(row.get("relation_type") or row.get("relation") or row.get("declared_relation_type"))
    not_found = [span_id for span_id in declared_evidence if span_id not in all_ids]
    out_of_scope = [span_id for span_id in declared_evidence if span_id in all_ids and allowed_set and span_id not in allowed_set]
    supported = [span_id for span_id in declared_evidence if span_id in all_ids and (not allowed_set or span_id in allowed_set)]

    reasons: List[str] = []
    if not declared_evidence:
        reasons.append(_REJECTION_COMPLETE_BINDING_EVIDENCE_IDS_MISSING if (require_phrase_unit_ids or require_relation_type) else _REJECTION_BINDING_DECLARED_EVIDENCE_NOT_FOUND)
    if not_found:
        reasons.append(_REJECTION_BINDING_DECLARED_EVIDENCE_NOT_FOUND)
    if out_of_scope:
        reasons.append(_REJECTION_BINDING_DECLARED_EVIDENCE_OUT_OF_SCOPE)
    if require_phrase_unit_ids and not declared_phrase:
        reasons.append(_REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING)
    if require_relation_type and not relation_type:
        reasons.append(_REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING)
        reasons.append(_REJECTION_COMPLETE_RELATION_NOT_EXPRESSED)

    if require_phrase_unit_ids or require_relation_type:
        binding_used = bool(supported and declared_phrase and relation_type and not reasons)
    else:
        binding_used = bool(supported and (declared_phrase or relation_type) and not reasons)

    return {
        "binding_used": binding_used,
        "sentence_id": _clean(row.get("sentence_id") or row.get("id")),
        "line_role": _clean(row.get("line_role") or row.get("role")),
        "declared_evidence_span_ids": declared_evidence,
        "declared_phrase_unit_ids": declared_phrase,
        "declared_relation_type": relation_type,
        "supported_evidence_span_ids": supported,
        "rejection_reasons": _dedupe(reasons),
    }


def _source_step_text(value: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for key in ("source_step", "target_step", "step", "stage", "version", "schema_version"):
        item = value.get(key)
        if item:
            parts.append(str(item))
    return " ".join(parts)


def _is_complete_binding_mode(*, grounding_scope: str, binding_source_meta: Mapping[str, Any]) -> bool:
    scope = _clean(grounding_scope).lower()
    if scope.startswith("complete"):
        return True
    if binding_source_meta.get("complete_binding_aware_grounding") is True:
        return True
    marker = _source_step_text(binding_source_meta).lower()
    if "step8_binding_aware_grounding" in marker or "complete_binding_aware_grounding" in marker:
        return True
    if "complete_surface" in marker or "complete_sentence_plan" in marker or "complete_composer_initial" in marker:
        return True
    if isinstance(binding_source_meta.get("grounding_input"), Mapping) or isinstance(binding_source_meta.get("complete_grounding_input"), Mapping):
        return True
    if binding_source_meta.get("surface_lines"):
        return True
    return False


def _complete_allowed_ids_from_meta(value: Mapping[str, Any]) -> List[str]:
    candidates: List[str] = []
    for key in ("used_evidence_span_ids", "allowed_evidence_span_ids", "evidence_span_ids"):
        candidates.extend(_tokens(value.get(key)))
    for row in _binding_rows_from_meta(value):
        candidates.extend(_binding_declared_evidence_ids(row))
    return _dedupe(candidates)


def _relation_expressed_by_surface(sentence: str, relation_type: str) -> bool:
    relation = _clean(relation_type).lower()
    if not relation or relation in {"center", "context", "unknown", "neutral"}:
        return True
    pattern = _COMPLETE_RELATION_TEXT_PATTERNS.get(relation)
    if pattern is not None:
        return bool(pattern.search(sentence or ""))
    return bool(_RELATION_RE.search(sentence or ""))


def _complete_over_echo_reason(sentence: str, evidence_spans: Sequence[EvidenceSpan]) -> str:
    sentence_norm = _normalize(sentence)
    if len(sentence_norm) < 18:
        return ""
    for span in evidence_spans or []:
        raw_norm = _normalize(getattr(span, "raw_text", ""))
        if len(raw_norm) < 18:
            continue
        if sentence_norm == raw_norm or raw_norm in sentence_norm or sentence_norm in raw_norm:
            return _REJECTION_COMPLETE_OVER_ECHO
        if _ngram_overlap(sentence, getattr(span, "raw_text", "")) >= 0.92 and len(sentence_norm) >= int(len(raw_norm) * 0.7):
            return _REJECTION_COMPLETE_OVER_ECHO
    return ""


def build_complete_binding_aware_grounding_contract_meta() -> dict[str, Any]:
    return {
        "version": _COMPLETE_BINDING_AWARE_GROUNDING_VERSION,
        "target_step": _COMPLETE_BINDING_AWARE_TARGET_STEP,
        "stage": "complete_composer_initial",
        "implementation_unit": "Commit 8",
        "binding_aware_grounding_strengthened": True,
        "complete_binding_aware_grounding": True,
        "accepts_complete_sentence_plan_v2": True,
        "accepts_surface_realizer_grounding_input": True,
        "requires_sentence_id": True,
        "sentence_id_required": True,
        "requires_used_evidence_span_ids": True,
        "used_evidence_span_ids_required": True,
        "requires_used_phrase_unit_ids": True,
        "used_phrase_unit_ids_required": True,
        "requires_relation_type": True,
        "relation_type_required": True,
        "unsupported_sentence_release_blocker": True,
        "relation_not_expressed_repair_target": True,
        "over_echo_repair_target": True,
        "overclaim_reject_preferred": True,
        "surface_threshold_relaxed": False,
        "guard_threshold_relaxed": False,
        "display_gate_relaxed": False,
        "comment_text_contract": "passed_only",
        "comment_text_key_written": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
        "raw_input_included": False,
    }


def judge_grounding(
    *,
    comment_text: Any,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    allowed_evidence_span_ids: Optional[Sequence[str]] = None,
    grounding_scope: str = "full_graph",
    binding_meta: Optional[Mapping[str, Any]] = None,
    sentence_binding_bundle: Optional[Mapping[str, Any]] = None,
    sentence_bindings: Any = None,
    complete_grounding_input: Optional[Mapping[str, Any]] = None,
    surface_grounding_input: Optional[Mapping[str, Any]] = None,
) -> GroundingReport:
    binding_source_meta: Dict[str, Any] = {}
    if isinstance(binding_meta, Mapping):
        binding_source_meta.update(dict(binding_meta))
    if isinstance(sentence_binding_bundle, Mapping):
        binding_source_meta["sentence_binding_bundle"] = sentence_binding_bundle
    if sentence_bindings is not None:
        binding_source_meta["sentence_bindings"] = sentence_bindings
    if isinstance(complete_grounding_input, Mapping):
        binding_source_meta["complete_grounding_input"] = complete_grounding_input
        binding_source_meta.setdefault("grounding_input", complete_grounding_input)
    if isinstance(surface_grounding_input, Mapping):
        binding_source_meta["surface_grounding_input"] = surface_grounding_input
        binding_source_meta.setdefault("grounding_input", surface_grounding_input)

    complete_binding_mode = _is_complete_binding_mode(
        grounding_scope=grounding_scope,
        binding_source_meta=binding_source_meta,
    )
    binding_rows = _binding_rows_from_meta(binding_source_meta)

    effective_comment_text = comment_text
    if not _clean(effective_comment_text):
        for key in ("complete_grounding_input", "surface_grounding_input", "grounding_input"):
            payload = binding_source_meta.get(key)
            if isinstance(payload, Mapping):
                effective_comment_text = payload.get("comment_text") or payload.get("realized_text") or payload.get("surface_text") or ""
                if _clean(effective_comment_text):
                    break

    graph_evidence_ids_list = _graph_evidence_ids(graph)
    # For scoped grounding callers can explicitly pass allowed ids.  If they
    # mark the call as limited/scoped but omit ids, fall back to the scoped
    # graph's own evidence ids rather than the full input evidence list.
    effective_allowed_ids = list(allowed_evidence_span_ids or [])
    if not effective_allowed_ids and str(grounding_scope or "").startswith(("limited", "scoped")):
        effective_allowed_ids = list(graph_evidence_ids_list)
    if not effective_allowed_ids and complete_binding_mode:
        effective_allowed_ids = _complete_allowed_ids_from_meta(binding_source_meta)

    scoped_evidence_spans, allowed_ids, ignored_ids = _filter_evidence_spans(
        evidence_spans,
        allowed_evidence_span_ids=effective_allowed_ids,
    )
    evidence_for_matching = scoped_evidence_spans if allowed_ids else list(evidence_spans or [])

    sentences = _sentences(effective_comment_text)
    evidence_text = "\n".join(str(span.raw_text or "") for span in evidence_for_matching)
    relation_edge_ids = _relation_edge_evidence(graph)
    graph_evidence_ids = set(graph_evidence_ids_list)
    evidence_by_id = {
        str(span.span_id or "").strip(): span
        for span in evidence_for_matching
        if str(span.span_id or "").strip()
    }

    claims: List[GroundingSentenceClaim] = []
    unsupported = 0
    relation_supported_count = 0
    body_index = 0
    binding_used_count = 0
    binding_rejection_reasons: List[str] = []
    declared_relation_types: List[str] = []
    declared_phrase_unit_ids: List[str] = []
    complete_relation_not_expressed_count = 0
    complete_over_echo_count = 0

    for idx, sentence in enumerate(sentences):
        if "Emlisです" in sentence or _GREETING_SENTENCE_RE.match(sentence):
            claims.append(GroundingSentenceClaim(sentence_index=idx, sentence=sentence, evidence_span_ids=[], relation_supported=True))
            continue

        relation_supported = bool(_RELATION_RE.search(sentence))
        matched_ids = [span.span_id for span in evidence_for_matching if _span_matches_sentence(sentence, span)]
        binding_row, binding_match_mode = _binding_for_sentence(binding_rows, sentence=sentence, body_index=body_index)
        binding = _binding_support(
            binding_row,
            evidence_by_id=evidence_by_id,
            allowed_ids=allowed_ids,
            require_phrase_unit_ids=complete_binding_mode,
            require_relation_type=complete_binding_mode,
        )
        body_index += 1

        binding_sentence_id = str(binding.get("sentence_id") or "")
        binding_line_role = str(binding.get("line_role") or "")
        binding_declared_evidence = list(binding.get("declared_evidence_span_ids") or [])
        binding_declared_phrase = list(binding.get("declared_phrase_unit_ids") or [])
        binding_relation = str(binding.get("declared_relation_type") or "")
        binding_supported_ids = list(binding.get("supported_evidence_span_ids") or [])
        sentence_binding_used = bool(binding.get("binding_used"))
        sentence_binding_reasons = list(binding.get("rejection_reasons") or [])

        if complete_binding_mode and binding_relation and binding_line_role == "relation" and not _relation_expressed_by_surface(sentence, binding_relation):
            sentence_binding_reasons.append(_REJECTION_COMPLETE_RELATION_NOT_EXPRESSED)
            complete_relation_not_expressed_count += 1
        if binding_relation:
            declared_relation_types.append(binding_relation)
            relation_supported = True
        declared_phrase_unit_ids.extend(binding_declared_phrase)
        if sentence_binding_reasons:
            binding_rejection_reasons.extend(sentence_binding_reasons)

        if sentence_binding_used:
            # Complete and Limited both keep the declared evidence ids as the
            # primary grounding support when binding validates.  This avoids
            # promoting unrelated surface matches while still preserving the old
            # Step 6 path.
            matched_ids = binding_supported_ids[:5] or matched_ids
            binding_used_count += 1
        if relation_supported:
            relation_supported_count += 1
        if not matched_ids and relation_supported and _GENERIC_RELATION_SENTENCE_RE.search(sentence):
            matched_ids = relation_edge_ids[:5]

        unsupported_reason = _step14_unbacked_reason(sentence, evidence_text)
        if not unsupported_reason and _OVERCLAIM_RE.search(sentence) and not _OVERCLAIM_RE.search(evidence_text):
            unsupported_reason = "unsupported_overclaim"
        if complete_binding_mode:
            echo_reason = _complete_over_echo_reason(sentence, [span for span in evidence_for_matching if span.span_id in set(binding_supported_ids or matched_ids)])
            if echo_reason:
                complete_over_echo_count += 1
                if not unsupported_reason:
                    unsupported_reason = echo_reason
        if not unsupported_reason and sentence_binding_reasons and (not matched_ids or complete_binding_mode):
            # In Complete mode missing phrase/relation binding is a blocker even
            # when surface text happens to overlap. This prevents accidental
            # promotion of unbound text to the visible observation.
            unsupported_reason = sentence_binding_reasons[0]
        elif not unsupported_reason and not matched_ids:
            unsupported_reason = "no_evidence_span_or_relation"

        if unsupported_reason:
            unsupported += 1
        claims.append(
            GroundingSentenceClaim(
                sentence_index=idx,
                sentence=sentence,
                evidence_span_ids=list(dict.fromkeys(matched_ids))[:5],
                relation_supported=relation_supported,
                unsupported_reason=unsupported_reason,
                binding_used=bool(sentence_binding_used and matched_ids and not unsupported_reason),
                binding_sentence_id=binding_sentence_id,
                binding_evidence_span_ids=list(dict.fromkeys(binding_supported_ids or binding_declared_evidence))[:5],
                binding_phrase_unit_ids=list(dict.fromkeys(binding_declared_phrase)),
                binding_relation_type=binding_relation,
                declared_evidence_span_ids=list(dict.fromkeys(binding_declared_evidence)),
                declared_phrase_unit_ids=list(dict.fromkeys(binding_declared_phrase)),
                declared_relation_type=binding_relation,
                grounding_support_source=(f"declared_{binding_match_mode}_binding" if sentence_binding_used else "surface_or_relation"),
                binding_support_reason=(f"declared_{binding_match_mode}_binding" if sentence_binding_used else ""),
                used_phrase_unit_ids=list(dict.fromkeys(binding_declared_phrase)),
                relation_type=binding_relation,
            )
        )

    content_sentence_count = len([s for s in sentences if "Emlisです" not in s and not _GREETING_SENTENCE_RE.match(s)])
    coverage_ratio = 0.0 if content_sentence_count <= 0 else 1.0 - (unsupported / max(1, content_sentence_count))
    reasons: List[str] = []
    if content_sentence_count <= 0:
        reasons.append("empty_text")
    if unsupported > 0:
        reasons.append("unsupported_sentence")
    for claim in claims:
        if claim.unsupported_reason in {
            "unsupported_diagnosis_like",
            "unsupported_personality_label",
            "unsupported_general_knowledge_completion",
            "unsupported_advice_assertion",
            "unsupported_overclaim",
            _REJECTION_COMPLETE_OVER_ECHO,
            _REJECTION_COMPLETE_RELATION_NOT_EXPRESSED,
            _REJECTION_COMPLETE_BINDING_MISSING,
            _REJECTION_COMPLETE_BINDING_EVIDENCE_IDS_MISSING,
            _REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING,
            _REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING,
        }:
            reasons.append(claim.unsupported_reason)
    if graph.core_tensions and relation_supported_count < 1:
        reasons.append("core_relation_not_reflected")
    if graph_evidence_ids and not any(set(c.evidence_span_ids).intersection(graph_evidence_ids) for c in claims):
        reasons.append("graph_evidence_not_used")
    if allowed_ids and not evidence_for_matching:
        reasons.append("scoped_evidence_not_found")
    if binding_rejection_reasons:
        reasons.extend(binding_rejection_reasons)

    reasons = list(dict.fromkeys(reasons))
    binding_rejection_reasons = _dedupe(binding_rejection_reasons)
    binding_missing = bool(binding_rows and len(binding_rows) < content_sentence_count) or bool(complete_binding_mode and not binding_rows and content_sentence_count > 0)
    repair_targets = [reason for reason in reasons if reason in {_REJECTION_COMPLETE_RELATION_NOT_EXPRESSED, _REJECTION_COMPLETE_OVER_ECHO, "unsupported_sentence"}]
    binding_diagnostics = {
        "version": _COMPLETE_BINDING_AWARE_GROUNDING_VERSION if complete_binding_mode else _STEP6_BINDING_AWARE_GROUNDING_VERSION,
        "target_step": _COMPLETE_BINDING_AWARE_TARGET_STEP if complete_binding_mode else _STEP6_BINDING_AWARE_TARGET_STEP,
        "binding_aware_grounding": True,
        "complete_binding_aware_grounding": complete_binding_mode,
        "binding_present": bool(binding_rows),
        "binding_used": bool(binding_used_count),
        "binding_count": len(binding_rows),
        "expected_binding_count": content_sentence_count,
        "binding_missing": binding_missing,
        "binding_supported_sentence_count": binding_used_count,
        "binding_rejection_reasons": binding_rejection_reasons,
        "declared_relation_types": _dedupe(declared_relation_types),
        "declared_phrase_unit_ids": _dedupe(declared_phrase_unit_ids),
        "sentence_id_checked": bool(binding_rows),
        "evidence_span_ids_checked": bool(binding_rows),
        "phrase_unit_ids_checked": bool(binding_rows),
        "relation_type_checked": bool(binding_rows),
        "surface_realizer_grounding_input_supported": complete_binding_mode,
        "complete_sentence_plan_v2_supported": complete_binding_mode,
        "relation_not_expressed_count": complete_relation_not_expressed_count,
        "over_echo_count": complete_over_echo_count,
        "repair_targets": repair_targets,
        "unsupported_sentence_is_release_blocker": True,
        "relation_not_expressed_is_repair_target": True,
        "over_echo_is_repair_target": True,
        "overclaim_reject_preferred": True,
        "surface_threshold_relaxed": False,
        "guard_threshold_relaxed": False,
        "display_gate_relaxed": False,
        "response_shape_changed": False,
        "raw_input_included": False,
    }
    return GroundingReport(
        passed=not reasons and coverage_ratio >= 0.65,
        sentence_claims=claims,
        rejection_reasons=reasons,
        coverage_ratio=round(coverage_ratio, 3),
        confidence=0.87 if binding_used_count and not reasons else (0.86 if not reasons else 0.42),
        grounding_scope=str(grounding_scope or "full_graph"),
        allowed_evidence_span_ids=allowed_ids,
        ignored_evidence_span_ids=ignored_ids,
        binding_present=bool(binding_rows),
        binding_used=bool(binding_used_count),
        binding_missing=binding_missing,
        binding_count=len(binding_rows),
        expected_binding_count=content_sentence_count,
        binding_supported_sentence_count=binding_used_count,
        binding_version=str(binding_source_meta.get("binding_version") or binding_source_meta.get("version") or binding_diagnostics["version"]),
        relation_types=_dedupe(declared_relation_types),
        binding_rejection_reasons=binding_rejection_reasons,
        declared_relation_types=_dedupe(declared_relation_types),
        declared_phrase_unit_ids=_dedupe(declared_phrase_unit_ids),
        binding_diagnostics=binding_diagnostics,
        binding_aware_grounding=binding_diagnostics,
    )


__all__ = [
    "judge_grounding",
    "build_complete_binding_aware_grounding_contract_meta",
    "_STEP6_BINDING_AWARE_GROUNDING_VERSION",
    "_COMPLETE_BINDING_AWARE_GROUNDING_VERSION",
    "_STEP8_COMPLETE_BINDING_AWARE_GROUNDING_VERSION",
    "_COMPLETE_BINDING_AWARE_TARGET_STEP",
    "_STEP8_COMPLETE_BINDING_AWARE_TARGET_STEP",
    "_REJECTION_BINDING_DECLARED_EVIDENCE_NOT_FOUND",
    "_REJECTION_BINDING_DECLARED_EVIDENCE_OUT_OF_SCOPE",
    "_REJECTION_COMPLETE_BINDING_MISSING",
    "_REJECTION_COMPLETE_BINDING_EVIDENCE_IDS_MISSING",
    "_REJECTION_COMPLETE_BINDING_PHRASE_UNIT_MISSING",
    "_REJECTION_COMPLETE_BINDING_PHRASE_UNIT_IDS_MISSING",
    "_REJECTION_COMPLETE_BINDING_RELATION_TYPE_MISSING",
    "_REJECTION_COMPLETE_PHRASE_BINDING_MISSING",
    "_REJECTION_COMPLETE_RELATION_BINDING_MISSING",
    "_REJECTION_COMPLETE_RELATION_NOT_EXPRESSED",
    "_REJECTION_COMPLETE_OVER_ECHO",
]
