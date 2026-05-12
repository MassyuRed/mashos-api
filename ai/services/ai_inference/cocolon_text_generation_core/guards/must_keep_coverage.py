# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic must-keep coverage guard."""

from typing import Any, Iterable, Mapping, Sequence

from cocolon_text_generation_core.guards.base import GuardResult, clean_token, make_guard_result, ngram_overlap, normalize_text, token_list

MUST_KEEP_COVERAGE_GUARD_NAME = "cocolon_text_generation_core.guards.must_keep_coverage.v1"
REJECTION_MUST_KEEP_EVIDENCE_MISSING = "must_keep_evidence_missing"
REJECTION_MUST_KEEP_ROLE_MISSING = "must_keep_role_missing"
REJECTION_MUST_KEEP_PHRASE_MISSING = "must_keep_phrase_missing"
REJECTION_MUST_INCLUDE_PLAN_MISSING = "must_include_plan_missing"
QUALITY_FLAG_MUST_KEEP_COVERAGE_FAILED = "must_keep_coverage_failed"
QUALITY_FLAG_MUST_KEEP_EVIDENCE_MISSING = "must_keep_evidence_missing"
QUALITY_FLAG_MUST_KEEP_ROLE_MISSING = "must_keep_role_missing"
QUALITY_FLAG_MUST_KEEP_TEXT_MISSING = "must_keep_text_missing"
REJECTION_MUST_KEEP_PHRASE_UNIT_MISSING = REJECTION_MUST_KEEP_PHRASE_MISSING
REJECTION_MUST_KEEP_EMPTY_PLAN = REJECTION_MUST_INCLUDE_PLAN_MISSING
REJECTION_MUST_KEEP_TEXT_MISSING = "must_keep_text_missing"


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _unit_id(unit: Any) -> str:
    return clean_token(_mapping_get(unit, "phrase_unit_id", ""))


def _unit_role(unit: Any) -> str:
    return clean_token(_mapping_get(unit, "role", ""))


def _unit_span_id(unit: Any) -> str:
    return clean_token(_mapping_get(unit, "evidence_span_id", ""))


def _unit_text(unit: Any) -> str:
    return str(_mapping_get(unit, "text", "") or _mapping_get(unit, "compressed_text", "") or _mapping_get(unit, "raw_text", "") or "").strip()


def _text_reflects_must_keep_unit(comment_text: Any, unit: Any) -> bool:
    body = normalize_text(comment_text)
    unit_text = normalize_text(_unit_text(unit))
    if not body or not unit_text:
        return False
    if unit_text in body or body in unit_text:
        return True
    # Piece answers can preserve a claim by keeping its distinctive part rather
    # than echoing the full source string.  Use a small n-gram threshold to catch
    # safe paraphrase while still rejecting total omission.
    if len(unit_text) >= 6 and ngram_overlap(body, unit_text) >= 0.24:
        return True
    if len(unit_text) >= 4:
        head = unit_text[: min(6, len(unit_text))]
        tail = unit_text[-min(6, len(unit_text)) :]
        return (len(head) >= 4 and head in body) or (len(tail) >= 4 and tail in body)
    return False


def _unit_must_keep(unit: Any) -> bool:
    return bool(_mapping_get(unit, "must_keep", False))


def _plan_must_include(plan: Any) -> bool:
    return bool(_mapping_get(plan, "must_include", False))


def _plan_phrase_unit_ids(plan: Any) -> tuple[str, ...]:
    ids = _mapping_get(plan, "phrase_unit_ids", ())
    return token_list(ids)


def guard_must_keep_coverage(
    comment_text: Any = "",
    *,
    phrase_units: Iterable[Any] | None = None,
    sentence_plans: Iterable[Any] | None = None,
    must_keep_roles: Iterable[object] | object | None = None,
    used_evidence_span_ids: Sequence[object] | None = None,
    used_phrase_unit_ids: Sequence[object] | None = None,
    require_text_for_must_keep: bool = False,
    **_ignored: Any,
) -> GuardResult:
    units = tuple(unit for unit in phrase_units or () if _unit_id(unit))
    plans = tuple(sentence_plans or ())
    role_tokens = token_list(must_keep_roles)
    used_evidence = set(token_list(used_evidence_span_ids))
    used_units = set(token_list(used_phrase_unit_ids))

    reasons: list[str] = []
    matched: list[str] = []
    unit_by_role: dict[str, list[Any]] = {}
    unit_by_id = {_unit_id(unit): unit for unit in units}
    for unit in units:
        role = _unit_role(unit)
        if role:
            unit_by_role.setdefault(role, []).append(unit)

    missing_roles: list[str] = []
    for role in role_tokens:
        if role not in unit_by_role:
            missing_roles.append(role)
            reasons.append(f"{REJECTION_MUST_KEEP_ROLE_MISSING}:{role}")
            matched.append(role)

    required_units: list[Any] = []
    for unit in units:
        if _unit_must_keep(unit) or (_unit_role(unit) in role_tokens):
            required_units.append(unit)

    if not required_units and role_tokens:
        reasons.append(REJECTION_MUST_KEEP_PHRASE_MISSING)

    required_evidence_ids = tuple(dict.fromkeys(_unit_span_id(unit) for unit in required_units if _unit_span_id(unit)))
    missing_evidence_ids: list[str] = []
    if used_evidence:
        missing_evidence_ids = [span_id for span_id in required_evidence_ids if span_id not in used_evidence]
        if missing_evidence_ids:
            reasons.append(f"{REJECTION_MUST_KEEP_EVIDENCE_MISSING}:{','.join(missing_evidence_ids)}")
            matched.extend(missing_evidence_ids)

    missing_plan_units: list[str] = []
    if used_units:
        for unit in required_units:
            unit_id = _unit_id(unit)
            if unit_id and unit_id not in used_units:
                missing_plan_units.append(unit_id)
        if missing_plan_units:
            reasons.append(f"{REJECTION_MUST_KEEP_PHRASE_MISSING}:{','.join(missing_plan_units)}")
            matched.extend(missing_plan_units)

    missing_must_include_plan_ids: list[str] = []
    for index, plan in enumerate(plans, start=1):
        if not _plan_must_include(plan):
            continue
        plan_id = clean_token(_mapping_get(plan, "sentence_plan_id", "")) or f"plan:{index}"
        ids = _plan_phrase_unit_ids(plan)
        if ids and not any(unit_id in unit_by_id for unit_id in ids):
            missing_must_include_plan_ids.append(plan_id)
    if missing_must_include_plan_ids:
        reasons.append(f"{REJECTION_MUST_INCLUDE_PLAN_MISSING}:{','.join(missing_must_include_plan_ids)}")
        matched.extend(missing_must_include_plan_ids)

    missing_text_unit_ids: list[str] = []
    if require_text_for_must_keep and comment_text:
        for unit in required_units:
            unit_id = _unit_id(unit)
            if unit_id and not _text_reflects_must_keep_unit(comment_text, unit):
                missing_text_unit_ids.append(unit_id)
        if missing_text_unit_ids:
            reasons.append(f"{REJECTION_MUST_KEEP_TEXT_MISSING}:{','.join(missing_text_unit_ids)}")
            matched.extend(missing_text_unit_ids)

    coverage_ratio = 1.0
    coverage_missing = set(missing_evidence_ids)
    if missing_text_unit_ids:
        coverage_missing.update(_unit_span_id(unit) for unit in required_units if _unit_id(unit) in set(missing_text_unit_ids) and _unit_span_id(unit))
    if required_evidence_ids:
        coverage_ratio = (len(required_evidence_ids) - len(coverage_missing)) / max(1, len(required_evidence_ids))

    return make_guard_result(
        guard_name=MUST_KEEP_COVERAGE_GUARD_NAME,
        reasons=reasons,
        quality_flags=(QUALITY_FLAG_MUST_KEEP_COVERAGE_FAILED,) if reasons else (),
        matched_texts=matched,
        coverage_ratio=coverage_ratio,
        used_evidence_span_ids=tuple(used_evidence),
        meta={
            "must_keep_roles": list(role_tokens),
            "missing_roles": missing_roles,
            "required_evidence_span_ids": list(required_evidence_ids),
            "missing_evidence_span_ids": missing_evidence_ids,
            "missing_phrase_unit_ids": missing_plan_units,
            "missing_must_include_plan_ids": missing_must_include_plan_ids,
            "missing_text_phrase_unit_ids": missing_text_unit_ids,
            "require_text_for_must_keep": bool(require_text_for_must_keep),
        },
    )


class MustKeepCoverageGuard:
    guard_name = MUST_KEEP_COVERAGE_GUARD_NAME

    def evaluate(self, comment_text: Any = "", **kwargs: Any) -> GuardResult:
        return guard_must_keep_coverage(comment_text, **kwargs)

    def check(self, comment_text: Any = "", **kwargs: Any) -> GuardResult:
        return self.evaluate(comment_text, **kwargs)



def guard_must_keep_coverage_for_payload(
    payload: Any,
    *,
    text: Any = "",
    used_evidence_span_ids: Sequence[object] | None = None,
    used_phrase_unit_ids: Sequence[object] | None = None,
) -> GuardResult:
    return guard_must_keep_coverage(
        text,
        phrase_units=getattr(payload, "phrase_units", ()),
        sentence_plans=getattr(payload, "sentence_plans", ()),
        must_keep_roles=getattr(payload, "must_keep_roles", ()),
        used_evidence_span_ids=used_evidence_span_ids,
        used_phrase_unit_ids=used_phrase_unit_ids,
    )

evaluate_must_keep_coverage = guard_must_keep_coverage
judge_must_keep_coverage = guard_must_keep_coverage
check_must_keep_coverage = guard_must_keep_coverage

__all__ = [
    "MUST_KEEP_COVERAGE_GUARD_NAME",
    "MustKeepCoverageGuard",
    "guard_must_keep_coverage",
    "evaluate_must_keep_coverage",
    "judge_must_keep_coverage",
    "check_must_keep_coverage",
    "REJECTION_MUST_KEEP_PHRASE_UNIT_MISSING",
    "REJECTION_MUST_KEEP_EMPTY_PLAN",
    "REJECTION_MUST_KEEP_TEXT_MISSING",
    "QUALITY_FLAG_MUST_KEEP_EVIDENCE_MISSING",
    "QUALITY_FLAG_MUST_KEEP_ROLE_MISSING",
    "QUALITY_FLAG_MUST_KEEP_TEXT_MISSING",
    "guard_must_keep_coverage_for_payload",
    "REJECTION_MUST_KEEP_EVIDENCE_MISSING",
    "REJECTION_MUST_KEEP_ROLE_MISSING",
    "REJECTION_MUST_KEEP_PHRASE_MISSING",
    "REJECTION_MUST_INCLUDE_PLAN_MISSING",
]
