# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic SentencePlan helpers for Cocolon text generation.

Phase 4 keeps planning mechanical. It can group already-built PhraseUnits by
caller-supplied role strings, but it does not decide what those roles mean.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Tuple

from cocolon_text_generation_core.phrase_units import phrase_units_by_id, usable_phrase_units
from cocolon_text_generation_core.policies import compact_tokens
from cocolon_text_generation_core.types import PhraseUnit, SentencePlan

SENTENCE_PLAN_BUILDER_NAME = "cocolon_text_generation_core.sentence_plan.v1"
REJECTION_SENTENCE_PLAN_EMPTY = "sentence_plan_empty"
REJECTION_SENTENCE_PLAN_UNIT_MISSING = "sentence_plan_unit_missing"


def _clean_token(value: object) -> str:
    return str(value or "").strip()


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean_token(key)
        if not key_text:
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            out[key_text] = item
        elif isinstance(item, (list, tuple)):
            out[key_text] = [v if isinstance(v, (str, int, float, bool)) or v is None else str(v) for v in item]
        elif isinstance(item, Mapping):
            out[key_text] = _json_safe_mapping(item)
        else:
            out[key_text] = str(item)
    return out


@dataclass(frozen=True)
class SentencePlanBuildResult:
    sentence_plans: Iterable[SentencePlan] = field(default_factory=tuple)
    skipped_plan_ids: Iterable[str] = field(default_factory=tuple)
    rejection_reasons: Iterable[str] = field(default_factory=tuple)
    builder_name: str = SENTENCE_PLAN_BUILDER_NAME
    meta: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        plans = tuple(plan for plan in self.sentence_plans or () if getattr(plan, "usable", False))
        object.__setattr__(self, "sentence_plans", plans)
        object.__setattr__(self, "skipped_plan_ids", compact_tokens(self.skipped_plan_ids))
        object.__setattr__(self, "rejection_reasons", compact_tokens(self.rejection_reasons))
        object.__setattr__(self, "builder_name", _clean_token(self.builder_name) or SENTENCE_PLAN_BUILDER_NAME)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    @property
    def usable(self) -> bool:
        return bool(self.sentence_plans)

    def as_meta(self) -> dict[str, Any]:
        return {
            "builder_name": self.builder_name,
            "sentence_plans": [plan.as_meta() for plan in self.sentence_plans],
            "skipped_plan_ids": list(self.skipped_plan_ids),
            "rejection_reasons": list(self.rejection_reasons),
            "meta": dict(self.meta),
        }


def phrase_unit_ids_for_roles(
    phrase_units: Iterable[PhraseUnit] | None,
    roles: Iterable[object] | object,
    *,
    max_units: int = 2,
) -> Tuple[str, ...]:
    """Return unit ids with roles exactly matching caller-provided strings."""

    if isinstance(roles, (str, bytes)):
        role_tokens = (_clean_token(roles),)
    else:
        role_tokens = compact_tokens(roles)  # type: ignore[arg-type]
    role_set = set(role_tokens)
    if not role_set:
        return tuple()
    out: list[str] = []
    for unit in usable_phrase_units(phrase_units):
        if unit.role in role_set and unit.phrase_unit_id not in out:
            out.append(unit.phrase_unit_id)
        if max_units > 0 and len(out) >= max_units:
            break
    return tuple(out)


def build_sentence_plan(
    *,
    sentence_plan_id: object,
    phrase_unit_ids: Iterable[object] | object,
    relation_type: object = "",
    line_role: object = "",
    max_chars: int = 120,
    must_include: bool = True,
    meta: Mapping[str, Any] | None = None,
) -> SentencePlan | None:
    """Build one common SentencePlan, or None when no phrase ids exist."""

    if isinstance(phrase_unit_ids, (str, bytes)):
        ids = (_clean_token(phrase_unit_ids),)
    else:
        ids = compact_tokens(phrase_unit_ids)  # type: ignore[arg-type]
    if not ids:
        return None
    plan_meta = _json_safe_mapping(meta)
    plan_meta.update({"source_builder": SENTENCE_PLAN_BUILDER_NAME, "role_meaning_interpreted": False})
    return SentencePlan(
        sentence_plan_id=_clean_token(sentence_plan_id),
        phrase_unit_ids=ids,
        relation_type=_clean_token(relation_type),
        line_role=_clean_token(line_role),
        max_chars=max_chars,
        must_include=must_include,
        meta=plan_meta,
    )


def build_sentence_plan_for_roles(
    phrase_units: Iterable[PhraseUnit] | None,
    *,
    sentence_plan_id: object,
    roles: Iterable[object] | object,
    relation_type: object = "",
    line_role: object = "",
    max_units: int = 2,
    max_chars: int = 120,
    must_include: bool = True,
    meta: Mapping[str, Any] | None = None,
) -> SentencePlan | None:
    """Build a plan from exact role-string matches.

    This helper is only a selector. The caller decides which roles should be
    grouped and what relation_type/line_role mean.
    """

    unit_ids = phrase_unit_ids_for_roles(phrase_units, roles, max_units=max_units)
    return build_sentence_plan(
        sentence_plan_id=sentence_plan_id,
        phrase_unit_ids=unit_ids,
        relation_type=relation_type,
        line_role=line_role,
        max_chars=max_chars,
        must_include=must_include,
        meta=meta,
    )


def validate_sentence_plans(
    sentence_plans: Iterable[SentencePlan] | None,
    phrase_units: Iterable[PhraseUnit] | None,
) -> Tuple[str, ...]:
    """Validate that plan unit ids exist in the supplied PhraseUnit set."""

    unit_ids = set(phrase_units_by_id(phrase_units))
    reasons: list[str] = []
    usable_plans = tuple(plan for plan in sentence_plans or () if getattr(plan, "usable", False))
    if not usable_plans:
        reasons.append(REJECTION_SENTENCE_PLAN_EMPTY)
    for plan in usable_plans:
        missing = [unit_id for unit_id in plan.phrase_unit_ids if unit_id not in unit_ids]
        if missing:
            reasons.append(f"{REJECTION_SENTENCE_PLAN_UNIT_MISSING}:{plan.sentence_plan_id}")
    return tuple(dict.fromkeys(reasons))


def build_sentence_plans_for_role_groups(
    phrase_units: Iterable[PhraseUnit] | None,
    role_groups: Iterable[Mapping[str, Any]] | None,
) -> SentencePlanBuildResult:
    """Build plans from caller-supplied role groups.

    Each group can contain either explicit ``phrase_unit_ids`` or ``roles``. No
    default EmlisAI/Piece/Analysis role map is embedded here.
    """

    units = usable_phrase_units(phrase_units)
    plans: list[SentencePlan] = []
    skipped: list[str] = []
    reasons: list[str] = []
    groups = tuple(role_groups or ())

    for index, group in enumerate(groups, start=1):
        if not isinstance(group, Mapping):
            skipped.append(f"index:{index}")
            reasons.append(REJECTION_SENTENCE_PLAN_EMPTY)
            continue
        plan_id = _clean_token(group.get("sentence_plan_id") or group.get("plan_id") or f"sp{index}")
        explicit_ids = group.get("phrase_unit_ids")
        if explicit_ids:
            plan = build_sentence_plan(
                sentence_plan_id=plan_id,
                phrase_unit_ids=explicit_ids,
                relation_type=group.get("relation_type", ""),
                line_role=group.get("line_role", ""),
                max_chars=int(group.get("max_chars") or 120),
                must_include=bool(group.get("must_include", True)),
                meta={"group_index": index},
            )
        else:
            plan = build_sentence_plan_for_roles(
                units,
                sentence_plan_id=plan_id,
                roles=group.get("roles") or (),
                relation_type=group.get("relation_type", ""),
                line_role=group.get("line_role", ""),
                max_units=int(group.get("max_units") or 2),
                max_chars=int(group.get("max_chars") or 120),
                must_include=bool(group.get("must_include", True)),
                meta={"group_index": index},
            )
        if plan is None:
            skipped.append(plan_id or f"index:{index}")
            if bool(group.get("must_include", True)):
                reasons.append(REJECTION_SENTENCE_PLAN_EMPTY)
            continue
        plans.append(plan)

    validation_reasons = validate_sentence_plans(plans, units)
    reasons.extend(validation_reasons)
    return SentencePlanBuildResult(
        sentence_plans=tuple(plans),
        skipped_plan_ids=tuple(skipped),
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        meta={"input_phrase_unit_count": len(units), "input_group_count": len(groups), "role_meaning_interpreted": False},
    )


def usable_sentence_plans(plans: Iterable[SentencePlan] | None) -> Tuple[SentencePlan, ...]:
    return tuple(plan for plan in plans or () if getattr(plan, "usable", False))


__all__ = [
    "REJECTION_SENTENCE_PLAN_EMPTY",
    "REJECTION_SENTENCE_PLAN_UNIT_MISSING",
    "SENTENCE_PLAN_BUILDER_NAME",
    "SentencePlanBuildResult",
    "build_sentence_plan",
    "build_sentence_plan_for_roles",
    "build_sentence_plans_for_role_groups",
    "phrase_unit_ids_for_roles",
    "usable_sentence_plans",
    "validate_sentence_plans",
]
