# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step20 A-2 long-term quality checks for EmlisAI.

This module is a developer / QA measurement layer.  It never edits
``comment_text`` and never uses history to complete a user's hidden intention.
History and cross-core material may only be treated as evidence / scope metadata.
"""

import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

STEP20_VERSION = "emlis.step20_long_term_quality.v1"
STEP20_PHASE = "A-2"
STEP20_STEP = "Step20_long_term_quality"
STEP20_PURPOSE = "a_plan_equivalent_long_term_operation_quality"
STEP20_SIMILARITY_THRESHOLD = 0.92
STEP20_REQUIRED_CHECKS: tuple[str, ...] = (
    "previous_output_similarity",
    "surface_variation_policy",
    "history_cross_core_scope",
    "qa_metrics",
    "distance_boundary",
)

_CURRENT_SOURCE_FIELDS = {"memo", "memo_action", "text", "free_text", "current_input"}
_HISTORY_SOURCE_FIELDS = {
    "history",
    "similar_input",
    "same_day_recent_input",
    "canonical_history",
    "derived_user_model",
    "cross_core_context",
    "piece",
    "analysis",
    "self_structure_report",
    "emotion_report",
}
_UNSUPPORTED_HISTORY_COMPLETION_SURFACES = (
    "前から",
    "以前から",
    "ずっと",
    "いつも",
    "毎回",
    "本当は",
    "本心",
    "根っこ",
    "性格",
    "タイプ",
    "傾向があります",
    "あなたは",
    "あなたの本質",
    "本来のあなた",
)
_DISTANCE_DRIFT_SURFACES = (
    "あなたは",
    "あなたの性格",
    "あなたの本質",
    "こういう人",
    "診断",
    "タイプです",
)

_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[\s　、,。.!！?？『』「」（）()\[\]【】:：;；]+")
_SENTENCE_SPLIT_RE = re.compile(r"[。！？!?\n]+")


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").strip())


def _compact(value: Any) -> str:
    return _PUNCT_RE.sub("", str(value or ""))


def _mapping(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    data: Dict[str, Any] = {}
    for key in (
        "comment_text",
        "composer_model",
        "composer_source",
        "generation_method",
        "generation_scope",
        "coverage_scope",
        "used_evidence_span_ids",
        "composer_meta",
        "rejection_reasons",
        "created_at",
        "profile_key",
        "case_id",
        "input_id",
    ):
        if hasattr(value, key):
            data[key] = getattr(value, key)
    return data


def _list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values: Iterable[Any] = [value]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    out: List[str] = []
    for raw in values:
        item = _clean(raw)
        if item and item not in out:
            out.append(item)
    return out


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean(value).lower() in {"1", "true", "yes", "y", "on", "passed", "green", "ok", "ready", "enabled"}


def _float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


def _nested(source: Mapping[str, Any] | None, *keys: str) -> Dict[str, Any]:
    if not isinstance(source, Mapping):
        return {}
    for key in keys:
        value = source.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _composer_meta(response: Mapping[str, Any], explicit_meta: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    if isinstance(explicit_meta, Mapping):
        return dict(explicit_meta)
    meta = response.get("composer_meta") if isinstance(response, Mapping) else None
    return dict(meta) if isinstance(meta, Mapping) else {}


def _profile_key(response: Mapping[str, Any], composer_meta: Mapping[str, Any], diagnostic_summary: Mapping[str, Any]) -> str:
    return (
        _clean(response.get("profile_key"))
        or _clean(composer_meta.get("profile_key"))
        or _clean(_nested(composer_meta, "composer_diagnostic").get("profile_key"))
        or _clean(diagnostic_summary.get("profile_key"))
        or _clean(diagnostic_summary.get("coverage_scope"))
        or "unknown"
    )


def _surface_tail_keys_from_meta(composer_meta: Mapping[str, Any]) -> List[str]:
    surface = (
        _nested(composer_meta, "step13_surface_realizer")
        or _nested(composer_meta, "surface_realizer")
        or _nested(composer_meta, "surface_realizer_meta")
    )
    return _list(surface.get("used_tail_keys") or surface.get("predicate_keys") or surface.get("surface_tail_keys"))


def _sentence_tail_signature(text: str) -> List[str]:
    tails: List[str] = []
    for raw in _SENTENCE_SPLIT_RE.split(str(text or "")):
        line = _clean(raw)
        if not line:
            continue
        compact = _compact(line)
        if not compact:
            continue
        tails.append(compact[-10:])
    return tails


def _ngrams(value: str, n: int = 3) -> set[str]:
    compact = _compact(value)
    if not compact:
        return set()
    if len(compact) <= n:
        return {compact}
    return {compact[index : index + n] for index in range(0, len(compact) - n + 1)}


def _similarity(left: str, right: str) -> float:
    left_set = _ngrams(left)
    right_set = _ngrams(right)
    if not left_set and not right_set:
        return 1.0
    if not left_set or not right_set:
        return 0.0
    return round(len(left_set.intersection(right_set)) / max(1, len(left_set.union(right_set))), 4)


def _previous_record(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, str):
        return {"comment_text": raw}
    record = _mapping(raw)
    meta = _composer_meta(record)
    if "profile_key" not in record and meta:
        record["profile_key"] = _profile_key(record, meta, {})
    if "surface_tail_keys" not in record:
        record["surface_tail_keys"] = _list(record.get("surface_tail_keys") or _surface_tail_keys_from_meta(meta))
    if "line_tail_signatures" not in record:
        record["line_tail_signatures"] = _sentence_tail_signature(_clean(record.get("comment_text")))
    return record


def _previous_records(previous_outputs: Sequence[Any] | None) -> List[Dict[str, Any]]:
    return [_previous_record(item) for item in list(previous_outputs or [])]


def _current_record(response: Mapping[str, Any], composer_meta: Mapping[str, Any], diagnostic_summary: Mapping[str, Any], comment_text: str) -> Dict[str, Any]:
    return {
        "comment_text": comment_text,
        "composer_model": _clean(response.get("composer_model") or diagnostic_summary.get("composer_model")),
        "profile_key": _profile_key(response, composer_meta, diagnostic_summary),
        "surface_tail_keys": _surface_tail_keys_from_meta(composer_meta),
        "line_tail_signatures": _sentence_tail_signature(comment_text),
        "used_evidence_span_ids": _list(response.get("used_evidence_span_ids")),
    }


def _similarity_report(current: Mapping[str, Any], previous: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    current_text = _clean(current.get("comment_text"))
    current_profile = _clean(current.get("profile_key"))
    comparisons: List[Dict[str, Any]] = []
    for index, record in enumerate(previous):
        previous_text = _clean(record.get("comment_text"))
        if not previous_text:
            continue
        score = _similarity(current_text, previous_text)
        same_profile = bool(current_profile and current_profile == _clean(record.get("profile_key")))
        comparisons.append(
            {
                "index": index,
                "similarity": score,
                "same_profile": same_profile,
                "profile_key": _clean(record.get("profile_key")),
                "created_at": _clean(record.get("created_at")),
            }
        )
    max_similarity = max((item["similarity"] for item in comparisons), default=0.0)
    max_same_profile_similarity = max((item["similarity"] for item in comparisons if item.get("same_profile")), default=0.0)
    similar = [item for item in comparisons if item["similarity"] >= STEP20_SIMILARITY_THRESHOLD]
    similar_same_profile = [item for item in similar if item.get("same_profile")]
    return {
        "threshold": STEP20_SIMILARITY_THRESHOLD,
        "comparison_count": len(comparisons),
        "max_similarity": max_similarity,
        "max_same_profile_similarity": max_same_profile_similarity,
        "similar_previous_outputs": similar,
        "similar_same_profile_outputs": similar_same_profile,
        "passed": not similar_same_profile and max_similarity < 0.985,
        "sample_available": bool(comparisons),
    }


def _surface_report(current: Mapping[str, Any], previous: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    current_profile = _clean(current.get("profile_key"))
    current_tail_keys = _list(current.get("surface_tail_keys")) or _list(current.get("line_tail_signatures"))
    current_tail_tuple = tuple(current_tail_keys)
    same_profile_repeats: List[Dict[str, Any]] = []
    any_repeats: List[Dict[str, Any]] = []
    for index, record in enumerate(previous):
        previous_tail_keys = _list(record.get("surface_tail_keys")) or _list(record.get("line_tail_signatures"))
        if not previous_tail_keys or not current_tail_tuple:
            continue
        previous_tuple = tuple(previous_tail_keys)
        repeated = previous_tuple == current_tail_tuple
        same_profile = bool(current_profile and current_profile == _clean(record.get("profile_key")))
        if repeated:
            payload = {
                "index": index,
                "same_profile": same_profile,
                "profile_key": _clean(record.get("profile_key")),
                "surface_tail_keys": list(previous_tuple),
            }
            any_repeats.append(payload)
            if same_profile:
                same_profile_repeats.append(payload)
    return {
        "policy": "avoid_same_profile_tail_sequence_repetition",
        "current_profile_key": current_profile,
        "current_surface_tail_keys": list(current_tail_tuple),
        "same_profile_tail_repetitions": same_profile_repeats,
        "any_profile_tail_repetitions": any_repeats,
        "tail_variation_ready": bool(current_tail_tuple),
        "passed": bool(current_tail_tuple and not same_profile_repeats),
        "sample_available": bool(previous),
    }


def _evidence_record(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, Mapping):
        return dict(raw)
    if is_dataclass(raw):
        return asdict(raw)
    data: Dict[str, Any] = {}
    for key in ("span_id", "raw_text", "source_field", "detected_type", "confidence"):
        if hasattr(raw, key):
            data[key] = getattr(raw, key)
    return data


def _evidence_records(evidence_spans: Sequence[Any] | None) -> List[Dict[str, Any]]:
    return [_evidence_record(item) for item in list(evidence_spans or [])]


def _source_field(record: Mapping[str, Any]) -> str:
    return _clean(record.get("source_field") or record.get("source") or record.get("kind")).lower()


def _evidence_span_id(record: Mapping[str, Any]) -> str:
    return _clean(record.get("span_id") or record.get("evidence_span_id") or record.get("id"))


def _is_current_evidence(record: Mapping[str, Any]) -> bool:
    source = _source_field(record)
    if not source:
        return True
    return source in _CURRENT_SOURCE_FIELDS or source.startswith("memo")


def _is_history_or_cross_core(record: Mapping[str, Any]) -> bool:
    source = _source_field(record)
    return bool(source in _HISTORY_SOURCE_FIELDS or "history" in source or "cross" in source or "piece" in source or "analysis" in source)


def _history_scope_report(
    *,
    comment_text: str,
    evidence_spans: Sequence[Any] | None,
    used_evidence_span_ids: Sequence[Any] | None,
    current_evidence_span_ids: Sequence[Any] | None,
    history_scope: Mapping[str, Any] | None,
    cross_core_scope: Mapping[str, Any] | None,
) -> Dict[str, Any]:
    records = _evidence_records(evidence_spans)
    used_ids = set(_list(used_evidence_span_ids))
    explicit_current_ids = set(_list(current_evidence_span_ids))
    current_ids: set[str] = set(explicit_current_ids)
    external_ids: set[str] = set()
    evidence_by_id: Dict[str, Dict[str, Any]] = {}
    for record in records:
        span_id = _evidence_span_id(record)
        if not span_id:
            continue
        evidence_by_id[span_id] = dict(record)
        if _is_history_or_cross_core(record) and (explicit_current_ids and span_id not in explicit_current_ids or not _is_current_evidence(record)):
            external_ids.add(span_id)
        else:
            current_ids.add(span_id)
    used_external_ids = sorted(used_ids.intersection(external_ids))
    unused_external_ids = sorted(external_ids.difference(used_ids))

    compact_text = _compact(comment_text)
    current_compact = "".join(_compact(record.get("raw_text")) for sid, record in evidence_by_id.items() if sid in current_ids)
    used_compact = "".join(_compact(evidence_by_id[sid].get("raw_text")) for sid in used_ids if sid in evidence_by_id)
    surfaced_external_terms: List[str] = []
    for sid in external_ids:
        raw = _clean(evidence_by_id.get(sid, {}).get("raw_text"))
        for fragment in re.split(r"[、,。.!！?？\s]+", raw):
            token = _compact(fragment)
            if len(token) >= 4 and token in compact_text and token not in current_compact and token not in used_compact:
                if token not in surfaced_external_terms:
                    surfaced_external_terms.append(token)

    unsupported_surfaces = [surface for surface in _UNSUPPORTED_HISTORY_COMPLETION_SURFACES if surface in comment_text and _compact(surface) not in current_compact and _compact(surface) not in used_compact]
    history_meta = dict(history_scope or {}) if isinstance(history_scope, Mapping) else {}
    cross_core_meta = dict(cross_core_scope or {}) if isinstance(cross_core_scope, Mapping) else {}
    history_enabled = bool(history_meta or cross_core_meta or external_ids)
    overclaim = bool(surfaced_external_terms or unsupported_surfaces)
    history_used_as_evidence_only = bool(not overclaim and all(sid in used_ids for sid in used_external_ids))
    return {
        "policy": "history_and_cross_core_are_evidence_only_not_completion",
        "history_enabled": history_enabled,
        "current_evidence_span_ids": sorted(current_ids),
        "external_context_span_ids": sorted(external_ids),
        "used_evidence_span_ids": sorted(used_ids),
        "used_external_context_span_ids": used_external_ids,
        "unused_external_context_span_ids": unused_external_ids,
        "surfaced_external_terms_without_current_grounding": surfaced_external_terms,
        "unsupported_history_completion_surfaces": unsupported_surfaces,
        "history_scope": history_meta,
        "cross_core_scope": cross_core_meta,
        "history_used_as_evidence_only": history_used_as_evidence_only,
        "history_completion_allowed": False,
        "overclaim_history_completion": overclaim,
        "passed": not overclaim,
    }


def _qa_report(
    *,
    comment_text: str,
    response: Mapping[str, Any],
    composer_meta: Mapping[str, Any],
    step19_a_plan_equivalent: Mapping[str, Any],
    similarity: Mapping[str, Any],
    surface: Mapping[str, Any],
    history_scope: Mapping[str, Any],
) -> Dict[str, Any]:
    line_count = len([part for part in _SENTENCE_SPLIT_RE.split(comment_text) if _clean(part)])
    fixed_flags = {
        "external_ai_used": _bool(composer_meta.get("external_ai_used")) or _bool(step19_a_plan_equivalent.get("external_ai_used")),
        "fallback_observation_sentence_added": _bool(composer_meta.get("fallback_observation_sentence_added")) or _bool(step19_a_plan_equivalent.get("fallback_observation_sentence_added")),
        "fixed_observation_sentence_added": _bool(composer_meta.get("fixed_observation_sentence_added")) or _bool(step19_a_plan_equivalent.get("fixed_observation_sentence_added")),
        "fixed_closing_sentence_added": _bool(composer_meta.get("fixed_closing_sentence_added")) or _bool(step19_a_plan_equivalent.get("fixed_closing_sentence_added")),
        "role_completion_templates_added": _bool(composer_meta.get("role_completion_templates_added")) or _bool(step19_a_plan_equivalent.get("role_completion_templates_added")),
    }
    distance_surfaces = [surface for surface in _DISTANCE_DRIFT_SURFACES if surface in comment_text]
    quality_flags = _list(response.get("quality_flags"))
    core = _nested(composer_meta, "text_generation_core", "core_text_generation")
    quality_flags.extend(_list(core.get("quality_flags")))
    blockers: List[str] = []
    for key, value in fixed_flags.items():
        if value:
            blockers.append(key)
    if distance_surfaces:
        blockers.append("distance_boundary_drift")
    if _bool(history_scope.get("overclaim_history_completion")):
        blockers.append("overclaim_history_completion")
    if not _bool(similarity.get("passed")):
        blockers.append("previous_output_similarity_too_high")
    if not _bool(surface.get("passed")):
        blockers.append("surface_tail_repetition")
    return {
        "policy": "no_template_no_overinterpretation_no_diagnosis",
        "line_count": line_count,
        "quality_flags": quality_flags,
        "distance_drift_surfaces": distance_surfaces,
        "fixed_text_flags": fixed_flags,
        "template_like": any(fixed_flags.values()),
        "overinterpretation_detected": _bool(history_scope.get("overclaim_history_completion")),
        "diagnosis_like_detected": bool(distance_surfaces),
        "blocking_reasons": blockers,
        "passed": not blockers,
    }


def _check(name: str, passed: bool, *, reason: str = "", evidence: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "check_key": name,
        "phase": STEP20_PHASE,
        "green": bool(passed),
        "status": "green" if passed else "red",
        "primary_reason": "green" if passed else (reason or f"{name}_not_ready"),
        "reason": "green" if passed else (reason or f"{name}_not_ready"),
        "evidence": dict(evidence or {}),
    }


def build_step20_long_term_quality_meta(
    *,
    response: Mapping[str, Any] | None = None,
    comment_text: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
    previous_outputs: Sequence[Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    used_evidence_span_ids: Sequence[Any] | None = None,
    current_evidence_span_ids: Sequence[Any] | None = None,
    history_scope: Mapping[str, Any] | None = None,
    cross_core_scope: Mapping[str, Any] | None = None,
    qa_metrics: Mapping[str, Any] | None = None,
    step19_a_plan_equivalent: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    current_input: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build Step20 A-2 long-term operation quality meta.

    ``ready`` requires an actual previous-output sample.  Runtime single-input
    calls therefore expose the contract as implementation-ready but do not claim
    long-term Green without same-user history material.
    """

    response_map = _mapping(response)
    summary = _mapping(diagnostic_summary)
    meta = _composer_meta(response_map, composer_meta)
    text = _clean(comment_text if comment_text is not None else response_map.get("comment_text"))
    used_ids = _list(used_evidence_span_ids if used_evidence_span_ids is not None else response_map.get("used_evidence_span_ids"))
    step19 = _mapping(step19_a_plan_equivalent)
    prev = _previous_records(previous_outputs)
    current = _current_record(response_map, meta, summary, text)
    current["used_evidence_span_ids"] = used_ids
    similarity = _similarity_report(current, prev)
    surface = _surface_report(current, prev)
    history = _history_scope_report(
        comment_text=text,
        evidence_spans=evidence_spans,
        used_evidence_span_ids=used_ids,
        current_evidence_span_ids=current_evidence_span_ids,
        history_scope=history_scope,
        cross_core_scope=cross_core_scope,
    )
    qa = _qa_report(
        comment_text=text,
        response=response_map,
        composer_meta=meta,
        step19_a_plan_equivalent=step19,
        similarity=similarity,
        surface=surface,
        history_scope=history,
    )
    explicit_qa = dict(qa_metrics or {}) if isinstance(qa_metrics, Mapping) else {}
    if explicit_qa:
        qa["external_qa_metrics"] = explicit_qa
        if _bool(explicit_qa.get("failed")) or _list(explicit_qa.get("blocking_reasons")):
            qa["passed"] = False
            qa["blocking_reasons"] = _list([*qa.get("blocking_reasons", []), *_list(explicit_qa.get("blocking_reasons")), "external_qa_metrics_failed"])

    previous_sample_available = bool(prev)
    same_profile_previous_count = sum(1 for record in prev if _clean(record.get("profile_key")) == current["profile_key"])
    checks = {
        "previous_output_similarity": _check(
            "previous_output_similarity",
            bool(previous_sample_available and similarity.get("passed")),
            reason="previous_output_sample_missing" if not previous_sample_available else "previous_output_similarity_too_high",
            evidence=similarity,
        ),
        "surface_variation_policy": _check(
            "surface_variation_policy",
            bool(previous_sample_available and surface.get("passed")),
            reason="surface_variation_sample_missing" if not previous_sample_available else "same_profile_tail_repetition",
            evidence=surface,
        ),
        "history_cross_core_scope": _check(
            "history_cross_core_scope",
            bool(history.get("passed")),
            reason="overclaim_history_completion",
            evidence=history,
        ),
        "qa_metrics": _check(
            "qa_metrics",
            bool(qa.get("passed")),
            reason="long_term_qa_metrics_failed",
            evidence=qa,
        ),
        "distance_boundary": _check(
            "distance_boundary",
            not bool(qa.get("distance_drift_surfaces")),
            reason="distance_boundary_drift",
            evidence={"distance_drift_surfaces": qa.get("distance_drift_surfaces", [])},
        ),
    }
    blocking_reasons: List[str] = []
    for key, check in checks.items():
        if not check.get("green"):
            reason = _clean(check.get("primary_reason")) or f"{key}_not_ready"
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
    for reason in _list(qa.get("blocking_reasons")):
        if reason not in blocking_reasons:
            blocking_reasons.append(reason)

    # A-2 may be evaluated before Step19 is fully Green in local/runtime paths,
    # but it must not claim operation readiness unless A-1 is at least preserved.
    step19_ready_or_preserved = bool(
        _bool(step19.get("ready"))
        or _bool(step19.get("b_plan_gate_preserved"))
        or not step19
    )
    if not step19_ready_or_preserved and "step19_a1_not_ready" not in blocking_reasons:
        blocking_reasons.append("step19_a1_not_ready")

    ready = bool(not blocking_reasons and previous_sample_available and text)
    return {
        "version": STEP20_VERSION,
        "phase": STEP20_PHASE,
        "step": STEP20_STEP,
        "purpose": STEP20_PURPOSE,
        "implementation_ready": True,
        "decision_ready": True,
        "ready": ready,
        "green": ready,
        "long_term_operation_ready": ready,
        "can_continue_a_plan_operation": ready,
        "previous_output_sample_available": previous_sample_available,
        "previous_output_count": len(prev),
        "same_profile_previous_output_count": same_profile_previous_count,
        "profile_key": current["profile_key"],
        "composer_model": _clean(response_map.get("composer_model") or step19.get("composer_model") or summary.get("composer_model")),
        "comment_text_changed": False,
        "comment_text_contract_preserved": True,
        "comment_text_contract": "passed_only",
        "b_plan_gate_preserved": True,
        "scoped_graph_preserved": True,
        "scoped_grounding_preserved": True,
        "fail_closed_preserved": True,
        "passed_only_preserved": True,
        "history_is_evidence_only": bool(history.get("history_used_as_evidence_only")),
        "history_completion_allowed": False,
        "overclaim_history_completion": bool(history.get("overclaim_history_completion")),
        "previous_output_similarity": similarity,
        "previous_output_similarity_policy": {
            "threshold": STEP20_SIMILARITY_THRESHOLD,
            "same_profile_only_blocks_rollout": True,
        },
        "surface_variation_policy": surface,
        "history_cross_core_scope": history,
        "qa_metrics": qa,
        "checks": checks,
        "required_checks": list(STEP20_REQUIRED_CHECKS),
        "test_contracts": [
            "same_profile_consecutive_inputs",
            "history_use_or_not_use_judgement",
            "long_term_surface_variation",
            "overclaim_history_completion",
        ],
        "current_input_id": _clean((current_input or {}).get("id") if isinstance(current_input, Mapping) else ""),
        "external_ai_used": False,
        "fallback_observation_sentence_added": False,
        "fixed_observation_sentence_added": False,
        "fixed_closing_sentence_added": False,
        "role_completion_templates_added": False,
        "general_knowledge_completion_allowed": False,
        "user_true_intention_completed_from_history": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "public_response_key_change": False,
        "blocking_reasons": blocking_reasons,
        "primary_reason": "green" if ready else (blocking_reasons[0] if blocking_reasons else "not_ready"),
        "next_step": "long_term_operation" if ready else "Step20_long_term_quality_qa",
    }


def attach_step20_long_term_quality_meta(
    response: Mapping[str, Any],
    *,
    step20_long_term_quality: Mapping[str, Any],
) -> Dict[str, Any]:
    out = dict(response or {})
    meta = _composer_meta(out)
    step20 = dict(step20_long_term_quality or {})
    meta["step20_long_term_quality"] = step20
    meta["a2_long_term_quality"] = step20
    meta["long_term_quality"] = step20
    out["composer_meta"] = meta
    return out



def build_runtime_surface_step11_long_run_quality_meta(
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    run_id: str = "",
) -> Dict[str, Any]:
    """Build Step11 Runtime Surface long-run QA meta from signature records.

    This wrapper keeps the existing Step20 A-2 text-similarity contract intact
    while exposing the Runtime Surface Quality Step11 check that works from
    row id / coverage / classification / surface-signature meta only.
    """

    from emlis_ai_runtime_surface_blind_qa_long_run import (
        build_runtime_surface_blind_qa_long_run_summary,
    )

    return build_runtime_surface_blind_qa_long_run_summary(
        events=events,
        blind_qa_reviews=blind_qa_reviews,
        run_id=run_id,
    )

def build_emlis_step20_long_term_quality(**kwargs: Any) -> Dict[str, Any]:
    return build_step20_long_term_quality_meta(**kwargs)




# ---------------------------------------------------------------------------
# Runtime Surface Quality Step11 - meta-only long-run signature measurement
# ---------------------------------------------------------------------------

RUNTIME_SURFACE_LONG_RUN_SIGNATURE_VERSION = "emlis.runtime_surface_long_run_signature.v1"
RUNTIME_SURFACE_LONG_RUN_SIGNATURE_STEP = "Step11_Blind_QA_Long_run"
RUNTIME_SURFACE_LONG_RUN_SIGNATURE_REPEAT_TARGET = 0.0

_STEP11_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
}


def _step11_contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _STEP11_FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _step11_contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_step11_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_long_run_signature_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_long_run_signature",
) -> None:
    """Reject raw input / public observation text in Step11 long-run reports."""

    if _step11_contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for flag in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "reader_gate_relaxed",
        "gate_relaxed",
        "product_gate_achieved",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
    ):
        if value.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def _step11_event_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    if is_dataclass(value):
        return asdict(value)
    return {}


def _step11_event_id(event: Mapping[str, Any], index: int) -> str:
    return (
        _clean(event.get("row_id"))
        or _clean(event.get("candidate_id"))
        or _clean(event.get("trace_id"))
        or _clean(event.get("emotion_log_id"))
        or f"signature-event-{index}"
    )


def _step11_coverage_group(event: Mapping[str, Any]) -> str:
    raw = _clean(event.get("coverage_group"))
    if not raw or raw.lower() in {"unknown", "unclassified", "missing", "none", "null"}:
        return "coverage_group_missing"
    return raw


def _step11_signature_family_key(event: Mapping[str, Any]) -> str:
    nested = event.get("surface_quality_signature")
    nested_map = dict(nested) if isinstance(nested, Mapping) else {}
    return (
        _clean(event.get("surface_signature_family_key"))
        or _clean(event.get("signature_family_key"))
        or _clean(nested_map.get("surface_signature_family_key"))
        or _clean(nested_map.get("signature_family_key"))
        or _clean(event.get("surface_signature_id"))
        or _clean(nested_map.get("surface_signature_id"))
    )


def _step11_signature_sample(raw: Any, index: int, *, source: str) -> Dict[str, Any]:
    event = _step11_event_mapping(raw)
    assert_runtime_surface_long_run_signature_meta_only(event, source=f"{source}[{index}]")
    family_key = _step11_signature_family_key(event)
    signature_id = _clean(event.get("surface_signature_id")) or family_key
    return {
        "sample_id": _step11_event_id(event, index),
        "sample_source": source,
        "coverage_group": _step11_coverage_group(event),
        "surface_signature_id": signature_id,
        "surface_signature_family_key": family_key,
        "composer_source": _clean(event.get("composer_source") or event.get("runtime_composer_source")),
        "classification": _clean(event.get("measurement_classification") or event.get("classification")),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }


def build_runtime_surface_long_run_signature_report(
    *,
    events: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    previous_signature_records: Sequence[Mapping[str, Any]] | Iterable[Mapping[str, Any]] | None = None,
    required_coverage_groups: Sequence[str] | None = None,
) -> Dict[str, Any]:
    """Measure same-coverage surface-signature repetition without text bodies.

    Step11 does not compare observation text.  It uses the meta-only
    ``surface_signature_family_key`` produced by Step2/Step3 and optional prior
    signature rows.  This makes long-run diversity visible without logging raw
    input or public ``comment_text`` bodies.
    """

    current_samples = [
        _step11_signature_sample(event, index, source="current_event")
        for index, event in enumerate(list(events or []), start=1)
    ]
    previous_samples = [
        _step11_signature_sample(event, index, source="previous_signature_record")
        for index, event in enumerate(list(previous_signature_records or []), start=1)
    ]
    groups = list(required_coverage_groups or [])
    if not groups:
        # Keep this function independent from complete scorecard imports to avoid
        # dependency cycles.  These are the Runtime Surface Quality coverage groups.
        groups = [
            "short_daily",
            "long_meaning_arc",
            "conflict",
            "recovery",
            "pressure",
            "desire_fear",
            "relationship",
        ]

    current_by_group: Dict[str, List[Dict[str, Any]]] = {}
    previous_by_group: Dict[str, List[Dict[str, Any]]] = {}
    for sample in current_samples:
        current_by_group.setdefault(sample["coverage_group"], []).append(sample)
    for sample in previous_samples:
        previous_by_group.setdefault(sample["coverage_group"], []).append(sample)

    rows: List[Dict[str, Any]] = []
    repeated_pairs: List[Dict[str, Any]] = []
    current_signature_count = 0
    repeat_count = 0
    for group in [*groups, "coverage_group_missing"]:
        current = current_by_group.get(group, [])
        previous = previous_by_group.get(group, [])
        current_keys = [sample["surface_signature_family_key"] for sample in current if sample.get("surface_signature_family_key")]
        previous_keys = [sample["surface_signature_family_key"] for sample in previous if sample.get("surface_signature_family_key")]
        key_counts: Dict[str, int] = {}
        for key in current_keys:
            key_counts[key] = key_counts.get(key, 0) + 1
        within_current_repeat_count = sum(max(0, count - 1) for count in key_counts.values())
        previous_key_set = set(previous_keys)
        previous_repeat_count = sum(1 for key in current_keys if key in previous_key_set)
        group_repeat_count = within_current_repeat_count + previous_repeat_count
        for sample in current:
            key = sample.get("surface_signature_family_key")
            if not key:
                continue
            if key_counts.get(key, 0) > 1 or key in previous_key_set:
                repeated_pairs.append(
                    {
                        "coverage_group": group,
                        "sample_id": sample.get("sample_id"),
                        "surface_signature_family_key": key,
                        "repeated_against": "previous_or_current_same_coverage_signature",
                    }
                )
        current_signature_count += len(current_keys)
        repeat_count += group_repeat_count
        rows.append(
            {
                "coverage_group": group,
                "current_signature_count": len(current_keys),
                "previous_signature_count": len(previous_keys),
                "unique_current_signature_count": len(set(current_keys)),
                "within_current_repeat_count": within_current_repeat_count,
                "previous_repeat_count": previous_repeat_count,
                "surface_signature_repeat_count": group_repeat_count,
                "surface_signature_repeat_rate": round(group_repeat_count / len(current_keys), 4) if current_keys else 0.0,
                "coverage_surface_diversity_rate": round(len(set(current_keys)) / len(current_keys), 4) if current_keys else 0.0,
                "long_run_sample_available": bool(previous_keys or len(current_keys) >= 2),
                "passed": bool(current_keys and group_repeat_count == 0 and (previous_keys or len(current_keys) >= 2)),
                "raw_input_included": False,
                "comment_text_body_included": False,
            }
        )

    sample_available = bool(previous_samples or current_signature_count >= 2)
    signature_sample_available = current_signature_count > 0
    repeat_rate = round(repeat_count / current_signature_count, 4) if current_signature_count else 0.0
    blockers: List[str] = []
    if not signature_sample_available:
        blockers.append("long_run_surface_signature_sample_missing")
    if not sample_available:
        blockers.append("long_run_previous_or_multi_sample_missing")
    if repeat_count > 0:
        blockers.append("long_run_surface_signature_repeat")
    ready = bool(signature_sample_available and sample_available and repeat_count == 0)
    report = {
        "version": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_VERSION,
        "source_step": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_STEP,
        "step": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_STEP,
        "long_run_signature_measurement_ready": ready,
        "long_run_ready": ready,
        "runtime_surface_long_run_ready": ready,
        "current_signature_sample_count": current_signature_count,
        "previous_signature_sample_count": len([sample for sample in previous_samples if sample.get("surface_signature_family_key")]),
        "long_run_sample_available": sample_available,
        "signature_sample_available": signature_sample_available,
        "surface_signature_repeat_count": repeat_count,
        "surface_signature_repeat_rate": repeat_rate,
        "surface_signature_repeat_target": RUNTIME_SURFACE_LONG_RUN_SIGNATURE_REPEAT_TARGET,
        "coverage_rows": rows,
        "by_coverage_group": {row["coverage_group"]: dict(row) for row in rows},
        "repeated_signature_pairs": repeated_pairs,
        "long_run_release_blockers": blockers,
        "release_blockers": blockers,
        "product_gate_candidate_blockers": blockers,
        "product_gate_candidate_long_run_pass": ready,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
    }
    assert_runtime_surface_long_run_signature_meta_only(report)
    return report

__all__ = [
    "build_runtime_surface_long_run_signature_report",
    "assert_runtime_surface_long_run_signature_meta_only",
    "RUNTIME_SURFACE_LONG_RUN_SIGNATURE_VERSION",
    "RUNTIME_SURFACE_LONG_RUN_SIGNATURE_STEP",
    "STEP20_PHASE",
    "STEP20_PURPOSE",
    "STEP20_REQUIRED_CHECKS",
    "STEP20_SIMILARITY_THRESHOLD",
    "STEP20_STEP",
    "STEP20_VERSION",
    "attach_step20_long_term_quality_meta",
    "build_runtime_surface_step11_long_run_quality_meta",
    "build_emlis_step20_long_term_quality",
    "build_step20_long_term_quality_meta",
]
