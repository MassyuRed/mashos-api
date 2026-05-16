# -*- coding: utf-8 -*-
from __future__ import annotations

"""Limited Surface Realizer stabilization helpers for EmlisAI.

Step 8 keeps the Limited Composer on the no-template route: it chooses
opener/particle/predicate/tail components from relation and PhraseUnit metadata,
not from raw input text or fixed completed observation sentences.
"""

from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_limited_relation_taxonomy import (
    canonical_relation_type,
    normalize_relation_type,
    relation_family,
)

LIMITED_SURFACE_REALIZER_VERSION = "emlis.limited_surface_realizer.stabilization.v1"
LIMITED_SURFACE_REALIZER_TARGET_STEP = "8_limited_surface_realizer_stabilization"
LIMITED_SURFACE_REALIZER_STAGE = "opener_particle_predicate_tail_variation_by_relation"
LIMITED_SURFACE_UNIT_TYPES = ("opener", "particle", "predicate", "tail_variation")

SurfaceCandidate = Tuple[str, str, str]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _repeated(values: Sequence[Any]) -> list[str]:
    counts: dict[str, int] = {}
    for value in values or []:
        item = _clean(value)
        if item:
            counts[item] = counts.get(item, 0) + 1
    return [key for key, count in counts.items() if count >= 2]


def _particle_key(particle: Any) -> str:
    value = _clean(particle)
    return {"が": "ga", "も": "mo", "まで": "made", "を": "wo", "に": "ni"}.get(value, value or "none")


def surface_opener_key(*, relation_type: Any, sequence_order: int) -> str:
    relation = normalize_relation_type(relation_type)
    if int(sequence_order or 0) <= 0:
        return "none"
    if relation in {"contrast", "approach_avoidance"}:
        return "contrast_after"
    if relation == "tension":
        return "tension_inside"
    if relation == "coexistence":
        return "coexistence_same_time"
    if relation in {"sequence", "progress", "recovery", "continuation"}:
        return "sequence_from" if int(sequence_order or 0) == 1 else "sequence_next"
    if relation in {"limit", "distance"}:
        return "limit_next" if int(sequence_order or 0) <= 2 else "limit_later"
    return "generic_next" if int(sequence_order or 0) <= 2 else "generic_continue"


def relation_tail_candidates(*, relation_type: Any, role_keys: Iterable[Any] = (), polarity: Any = "") -> tuple[SurfaceCandidate, ...]:
    relation = normalize_relation_type(relation_type, roles=role_keys)
    roles = set(_dedupe(role_keys))
    pol = _clean(polarity)
    if relation == "surface":
        return (("が", "表に出ています", "surface_visible"), ("が", "前面にあります", "front"), ("も", "見えています", "visible"))
    if relation in {"value", "approach"} or roles.intersection({"value_wish", "wish_to_rely", "avoidance_wish"}):
        return (("が", "言葉になっています", "worded"), ("が", "前面にあります", "front"), ("も", "見えています", "visible"))
    if relation == "pressure":
        return (("が", "強く残っています", "strong_remain"), ("が", "続いています", "continue"), ("も", "残っています", "remain"), ("も", "見えています", "visible"))
    if relation in {"progress", "recovery", "sequence", "continuation"}:
        return (("が", "形になっています", "progress_shape"), ("も", "見えています", "visible"), ("が", "続いています", "continue"), ("も", "残っています", "remain"))
    if relation in {"contrast", "approach_avoidance", "coexistence"}:
        return (("も", "重なっています", "stack"), ("も", "残っています", "remain"), ("も", "見えています", "visible"), ("が", "混ざっています", "mixed"), ("も", "並んでいます", "parallel"))
    if relation == "tension":
        return (("が", "ぶつかっています", "tension"), ("も", "重なっています", "stack"), ("も", "残っています", "remain"))
    if relation == "limit":
        return (("まで", "来ています", "limit_arrived"), ("も", "残っています", "remain"), ("も", "見えています", "visible"), ("も", "あります", "exists"))
    if relation == "context":
        return (("も", "見えています", "visible"), ("も", "重なっています", "stack"), ("も", "残っています", "remain"))
    if pol == "positive":
        return (("が", "形になっています", "progress_shape"), ("も", "見えています", "visible"), ("が", "続いています", "continue"))
    return (("も", "見えています", "visible"), ("も", "残っています", "remain"), ("が", "前面にあります", "front"))


def choose_limited_surface_parts(
    *,
    relation_type: Any,
    line_role: Any = "",
    role_keys: Iterable[Any] = (),
    polarity: Any = "",
    current_candidates: Sequence[SurfaceCandidate] | None = None,
    used_tail_keys: Sequence[Any] | None = None,
) -> SurfaceCandidate:
    """Choose a stable particle/predicate/tail key.

    The function uses relation/role metadata and avoids repeating tail keys when
    alternatives exist.  It never returns a completed observation sentence.
    """

    used = set(_dedupe(used_tail_keys or ()))
    relation = normalize_relation_type(relation_type, roles=role_keys, line_role=_clean(line_role))
    candidates: list[SurfaceCandidate] = []
    for item in list(current_candidates or ()):  # preserve existing relation-specific priorities
        if len(item) == 3 and _clean(item[2]):
            candidates.append((item[0], item[1], item[2]))
    for item in relation_tail_candidates(relation_type=relation, role_keys=role_keys, polarity=polarity):
        if item not in candidates:
            candidates.append(item)

    # Prefer non-generic, unused tails.  "written" is retained only when there is
    # no safer relation-aware alternative.
    for particle, predicate, key in candidates:
        if key not in used and key != "written":
            return particle, predicate, key
    for particle, predicate, key in candidates:
        if key not in used:
            return particle, predicate, key
    return candidates[0] if candidates else ("が", "見えています", "visible")


def build_surface_component_row(
    *,
    line_role: Any,
    relation_type: Any,
    role_keys: Iterable[Any] = (),
    phrase_unit_ids: Iterable[Any] = (),
    sequence_order: int = 0,
    particle: Any = "",
    predicate_key: Any = "",
    shallow_path: bool = False,
) -> dict[str, Any]:
    roles = _dedupe(role_keys)
    relation = normalize_relation_type(relation_type, roles=roles, line_role=_clean(line_role))
    key = _clean(predicate_key)
    return {
        "surface_version": LIMITED_SURFACE_REALIZER_VERSION,
        "target_step": LIMITED_SURFACE_REALIZER_TARGET_STEP,
        "line_role": _clean(line_role) or "observation",
        "relation_type": relation,
        "canonical_relation_type": canonical_relation_type(relation),
        "relation_family": relation_family(relation),
        "sequence_order": int(sequence_order or 0),
        "opener_key": surface_opener_key(relation_type=relation, sequence_order=int(sequence_order or 0)),
        "particle_key": _particle_key(particle),
        "predicate_key": key,
        "tail_key": key,
        "role_keys": roles,
        "phrase_unit_ids": _dedupe(phrase_unit_ids),
        "componentized_surface": True,
        "relation_aware_surface": True,
        "shallow_observation_path": bool(shallow_path),
        "completion_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "raw_text_included": False,
    }


def _sanitize_surface_rows(surface_rows: Sequence[Mapping[str, Any]] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in list(surface_rows or ()):  # never copy display text / raw text
        if not isinstance(row, Mapping):
            continue
        rows.append(
            {
                "surface_version": _clean(row.get("surface_version") or LIMITED_SURFACE_REALIZER_VERSION),
                "target_step": _clean(row.get("target_step") or LIMITED_SURFACE_REALIZER_TARGET_STEP),
                "line_role": _clean(row.get("line_role")),
                "relation_type": normalize_relation_type(row.get("relation_type"), roles=row.get("role_keys") or (), line_role=row.get("line_role")),
                "canonical_relation_type": _clean(row.get("canonical_relation_type") or canonical_relation_type(row.get("relation_type"))),
                "relation_family": _clean(row.get("relation_family") or relation_family(row.get("relation_type"))),
                "sequence_order": int(row.get("sequence_order") or 0),
                "opener_key": _clean(row.get("opener_key")),
                "particle_key": _clean(row.get("particle_key")),
                "predicate_key": _clean(row.get("predicate_key") or row.get("tail_key")),
                "tail_key": _clean(row.get("tail_key") or row.get("predicate_key")),
                "role_keys": _dedupe(row.get("role_keys") or ()),
                "phrase_unit_ids": _dedupe(row.get("phrase_unit_ids") or ()),
                "componentized_surface": True,
                "relation_aware_surface": True,
                "shallow_observation_path": bool(row.get("shallow_observation_path")),
                "completion_sentence_template_used": False,
                "role_completed_sentence_template_used": False,
                "input_specific_template_used": False,
                "raw_text_included": False,
            }
        )
    return rows


def build_surface_stabilization_meta(
    *,
    profile_key: Any,
    coverage_scope: Any = "",
    surface_rows: Sequence[Mapping[str, Any]] | None = None,
    predicate_keys: Sequence[Any] | None = None,
    relation_types: Sequence[Any] | None = None,
    shallow_path: bool = False,
) -> dict[str, Any]:
    rows = _sanitize_surface_rows(surface_rows)
    raw_tail_keys = [_clean(item) for item in list(predicate_keys or ()) if _clean(item)]
    if not raw_tail_keys:
        raw_tail_keys = [_clean(row.get("tail_key") or row.get("predicate_key")) for row in rows if _clean(row.get("tail_key") or row.get("predicate_key"))]
    relations = _dedupe([*(relation_types or ()), *(row.get("relation_type") for row in rows)])
    repeated_tail_keys = _repeated(raw_tail_keys)
    return {
        "version": LIMITED_SURFACE_REALIZER_VERSION,
        "target_step": LIMITED_SURFACE_REALIZER_TARGET_STEP,
        "step": LIMITED_SURFACE_REALIZER_TARGET_STEP,
        "stage": LIMITED_SURFACE_REALIZER_STAGE,
        "limited_surface_realizer_stabilized": True,
        "surface_realizer_stabilized": True,
        "profile_key": _clean(profile_key),
        "coverage_scope": _clean(coverage_scope),
        "shallow_observation_path": bool(shallow_path),
        "surface_unit_types": list(LIMITED_SURFACE_UNIT_TYPES),
        "relation_aware_surface_selection": True,
        "relation_aware_opener_selection": True,
        "relation_aware_particle_selection": True,
        "relation_aware_predicate_selection": True,
        "tail_variation_by_relation": True,
        "tail_variation_enabled": True,
        "repeated_tail_avoidance": True,
        "repeated_tail_keys": repeated_tail_keys,
        "repeated_predicate_keys": repeated_tail_keys,
        "tail_keys": _dedupe(raw_tail_keys),
        "used_tail_keys": _dedupe(raw_tail_keys),
        "predicate_keys": _dedupe(raw_tail_keys),
        "raw_tail_key_sequence": raw_tail_keys,
        "surface_tail_key_count": len(raw_tail_keys),
        "unique_tail_key_count": len(set(raw_tail_keys)),
        "opener_keys": _dedupe(row.get("opener_key") for row in rows),
        "particle_keys": _dedupe(row.get("particle_key") for row in rows),
        "relation_types": relations,
        "relation_family_count": len(_dedupe(row.get("relation_family") for row in rows)),
        "surface_component_rows": rows,
        "relation_component_rows": rows,
        "surface_component_row_count": len(rows),
        "grammar_parts_only": True,
        "componentized_surface_realizer": True,
        "connector_particle_predicate_tail_parts_only": True,
        "completion_sentence_templates_added": False,
        "fixed_observation_sentence_added": False,
        "fixed_closing_sentence_added": False,
        "generic_closing_added": False,
        "role_sentence_templates_added": False,
        "role_based_completed_sentence_added": False,
        "input_specific_template_added": False,
        "example_sentence_match_used": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_guard_relaxed": False,
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_debug": False,
    }
