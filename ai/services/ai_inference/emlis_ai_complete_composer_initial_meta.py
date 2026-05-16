# -*- coding: utf-8 -*-
from __future__ import annotations

"""Commit-1 meta helpers for the EmlisAI Complete Composer initial path.

These helpers are internal / QA meta only. They make the AP0 -> Complete
Composer initial decision explicit without generating user-facing
``comment_text`` and without changing public API routes, DB physical names,
response keys, or RN display behavior.
"""

from typing import Any, Dict, Iterable, Mapping

COMPLETE_COMPOSER_INITIAL_TERM_META_VERSION = "emlis.complete_composer_initial_terms.v1"
COMPLETE_COMPOSER_INITIAL_AP0_REPORT_VERSION = "emlis.complete_composer_initial.ap0_decision_report.v1"

LIMITED_COMPOSER_TERM = "限定Composer"
COMPLETE_COMPOSER_TERM = "完全Composer"
COMPLETE_COMPOSER_INITIAL_TERM = "完全Composer初期版"
COMPLETE_COMPOSER_PRODUCT_TERM = "完全Composer商品品質版"
EMLIS_OBSERVATION_VISIBLE_TITLE = "Emlis の観測"

LIMITED_COMPOSER_MODEL = "cocolon_limited_composer.v1"
COMPLETE_COMPOSER_INITIAL_MODEL = "cocolon_emlis_observation_composer.a1.v1"

COMPLETE_COMPOSER_INITIAL_ALIASES: tuple[str, ...] = (
    "a_plan",
    "a-plan",
    "a1",
    "a_1",
    "a-plan-equivalent",
    "a_plan_equivalent",
    "complete",
    "complete-initial",
    "complete_initial",
    "complete_composer",
    "complete-composer",
    "complete_composer_initial",
    "complete-composer-initial",
    "complete_initial_composer",
    "complete-initial-composer",
    "cocolon_emlis_observation_composer_a1",
    "cocolon_emlis_observation_composer.a1",
    "cocolon_emlis_observation_composer.a1.v1",
)

LEGACY_COMPOSER_ALIAS_READINGS: Dict[str, str] = {
    "b_plan": LIMITED_COMPOSER_TERM,
    "b-plan": LIMITED_COMPOSER_TERM,
    "limited": LIMITED_COMPOSER_TERM,
    "limited_composer": LIMITED_COMPOSER_TERM,
    "cocolon_limited_composer": LIMITED_COMPOSER_TERM,
    **{alias: COMPLETE_COMPOSER_INITIAL_TERM for alias in COMPLETE_COMPOSER_INITIAL_ALIASES},
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean(value).lower() in {"1", "true", "yes", "y", "on", "passed", "green", "ok", "enabled", "enable"}


def _mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values: Iterable[Any] = [value]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out




def _release_blocker_list(value: Any) -> list[Dict[str, Any]]:
    """Normalize AP0 release blockers while preserving check_key structure."""
    if value is None:
        return []
    if isinstance(value, Mapping):
        values: Iterable[Any] = [value]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    out: list[Dict[str, Any]] = []
    seen: set[str] = set()
    for raw in values:
        if isinstance(raw, Mapping):
            item = dict(raw)
            check_key = _clean(item.get("check_key") or item.get("key") or item.get("reason") or item.get("primary_reason"))
            reason = _clean(item.get("reason") or item.get("primary_reason") or item.get("blocker") or check_key)
            if not check_key:
                continue
            normalized = {
                "check_key": check_key,
                "reason": reason or check_key,
                "return_steps": _list(item.get("return_steps")),
            }
            for key, value in item.items():
                normalized.setdefault(str(key), value)
        else:
            text = _clean(raw)
            if not text:
                continue
            check_key = text.split(":", 1)[1] if text.startswith("ap0_unmet:") and ":" in text else text
            normalized = {"check_key": check_key, "reason": text, "return_steps": []}
        marker = f"{normalized.get('check_key')}::{normalized.get('reason')}"
        if marker not in seen:
            seen.add(marker)
            out.append(normalized)
    return out


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in values:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_complete_composer_initial_term_meta(*, include_legacy_aliases: bool = True) -> Dict[str, Any]:
    """Return the canonical naming contract for Commit-1 additive meta."""

    meta: Dict[str, Any] = {
        "version": COMPLETE_COMPOSER_INITIAL_TERM_META_VERSION,
        "canonical_composer_term": LIMITED_COMPOSER_TERM,
        "base_composer_term": LIMITED_COMPOSER_TERM,
        "limited_composer_term": LIMITED_COMPOSER_TERM,
        "target_composer_term": COMPLETE_COMPOSER_INITIAL_TERM,
        "target_composer_family_term": COMPLETE_COMPOSER_TERM,
        "target_composer_stage_term": COMPLETE_COMPOSER_INITIAL_TERM,
        "complete_composer_term": COMPLETE_COMPOSER_TERM,
        "complete_composer_initial_term": COMPLETE_COMPOSER_INITIAL_TERM,
        "complete_composer_product_term": COMPLETE_COMPOSER_PRODUCT_TERM,
        "base_model": LIMITED_COMPOSER_MODEL,
        "target_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "visible_title": EMLIS_OBSERVATION_VISIBLE_TITLE,
        "comment_text_contract": "passed_only",
        "legacy_name_policy": "compat_alias_preserved_no_physical_rename",
        "physical_rename_allowed": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "public_response_key_change": False,
        "rn_visible_title_changed": False,
        "response_shape_changed": False,
        "external_ai_allowed": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_allowed": False,
        "raw_input_required_for_improvement": False,
    }
    if include_legacy_aliases:
        meta["legacy_alias_readings"] = dict(LEGACY_COMPOSER_ALIAS_READINGS)
        meta["complete_composer_initial_aliases"] = list(COMPLETE_COMPOSER_INITIAL_ALIASES)
    return meta


def build_complete_composer_initial_ap0_decision_report(ap0_decision: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Build the AP0 entry report for Complete Composer initial implementation.

    The report is derived from existing Step18 decision keys instead of
    replacing them. Existing callers can continue reading ``can_proceed_to_a1``,
    ``unmet_checks`` and ``return_steps`` while Commit-1 meta clarifies that
    A-1 / ``a_plan_equivalent`` means 完全Composer初期版.
    """

    decision = _mapping(ap0_decision)
    can_enter = bool(_bool(decision.get("can_proceed_to_a1")) or _bool(decision.get("can_enter_step19")))
    unmet_checks = _list(decision.get("unmet_checks"))
    return_steps = _list(decision.get("return_steps"))
    check_results = _mapping(decision.get("check_results"))
    check_blockers = [
        str(item.get("check_key") or key)
        for key, item in check_results.items()
        if isinstance(item, Mapping) and item.get("blocking") and not item.get("green")
    ]
    explicit_blockers = _release_blocker_list(decision.get("release_blockers"))
    inferred_blockers = []
    if not explicit_blockers:
        for key in _dedupe([*unmet_checks, *check_blockers]):
            check_item = _mapping(check_results.get(key))
            inferred_blockers.append({
                "check_key": key,
                "reason": _clean(check_item.get("reason") or check_item.get("primary_reason")) or f"ap0_unmet:{key}",
                "return_steps": _list(check_item.get("return_steps")),
            })
    release_blockers = explicit_blockers or inferred_blockers
    term_meta = build_complete_composer_initial_term_meta()
    next_step = _clean(decision.get("next_step")) or ("Step19_a_plan_equivalent_composer" if can_enter else (return_steps[0] if return_steps else "Step18_ap0_migration_decision"))
    report_decision = "enter_complete_composer_initial_implementation" if can_enter else "return_to_limited_composer_work"

    return {
        "version": COMPLETE_COMPOSER_INITIAL_AP0_REPORT_VERSION,
        "purpose": "commit1_ap0_entry_report_for_complete_composer_initial",
        "status": "green" if can_enter else "red",
        "green": bool(can_enter),
        "ready": True,
        "entry_decision": report_decision,
        "can_enter_complete_composer_initial": bool(can_enter),
        "can_proceed_to_complete_initial": bool(can_enter),
        "can_proceed_to_a1": bool(can_enter),
        "ap0_decision": _clean(decision.get("decision")),
        "next_step": next_step,
        "compat_next_step": next_step,
        "unmet_checks": unmet_checks,
        "return_steps": return_steps,
        "release_blockers": release_blockers,
        "release_blocker_keys": [str(item.get("check_key") or "") for item in release_blockers if str(item.get("check_key") or "")],
        "release_blocker_count": len(release_blockers),
        "check_order": _list(decision.get("check_order")),
        "green_checks": _list(decision.get("green_checks")),
        "term_meta": term_meta,
        "canonical_composer_term": term_meta["canonical_composer_term"],
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "target_composer_stage_term": term_meta["target_composer_stage_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "legacy_alias_readings": dict(term_meta.get("legacy_alias_readings") or {}),
        "contract_boundary": {
            "comment_text_contract": "passed_only",
            "visible_title": EMLIS_OBSERVATION_VISIBLE_TITLE,
            "db_physical_name_changed": False,
            "api_route_changed": False,
            "public_response_key_change": False,
            "rn_visible_title_changed": False,
            "response_shape_changed": False,
        },
        "no_external_ai": True,
        "no_local_llm": True,
        "no_fixed_sentence_template": True,
        "raw_input_required_for_improvement": False,
        "implementation_log": {
            "commit_unit": "Commit 1",
            "scope": "ap0_decision_report_helper_and_naming_meta",
            "response_shape_changed": False,
            "user_visible_text_changed": False,
        },
    }


def attach_complete_composer_initial_ap0_report(ap0_decision: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    """Return an AP0 decision copy with Commit-1 additive report fields."""

    out = _mapping(ap0_decision)
    report = build_complete_composer_initial_ap0_decision_report(out)
    term_meta = report["term_meta"]
    release_blockers = _release_blocker_list(out.get("release_blockers")) or _release_blocker_list(report.get("release_blockers"))

    out.setdefault("composer_term_meta", term_meta)
    out.setdefault("canonical_composer_term", term_meta["canonical_composer_term"])
    out.setdefault("target_composer_term", term_meta["target_composer_term"])
    out.setdefault("target_composer_family_term", term_meta["target_composer_family_term"])
    out.setdefault("target_composer_stage_term", term_meta["target_composer_stage_term"])
    out.setdefault("complete_composer_initial_term", term_meta["complete_composer_initial_term"])
    out.setdefault("legacy_alias_readings", dict(term_meta.get("legacy_alias_readings") or {}))
    out["can_proceed_to_complete_initial"] = bool(report.get("can_proceed_to_complete_initial"))
    out["release_blockers"] = release_blockers
    out["release_blocker_keys"] = [str(item.get("check_key") or "") for item in release_blockers if str(item.get("check_key") or "")]
    out["release_blocker_count"] = len(release_blockers)
    out["complete_composer_initial_ap0_report"] = report
    out["ap0_decision_report"] = report
    return out


__all__ = [
    "COMPLETE_COMPOSER_INITIAL_ALIASES",
    "COMPLETE_COMPOSER_INITIAL_AP0_REPORT_VERSION",
    "COMPLETE_COMPOSER_INITIAL_MODEL",
    "COMPLETE_COMPOSER_INITIAL_TERM",
    "COMPLETE_COMPOSER_INITIAL_TERM_META_VERSION",
    "COMPLETE_COMPOSER_PRODUCT_TERM",
    "COMPLETE_COMPOSER_TERM",
    "EMLIS_OBSERVATION_VISIBLE_TITLE",
    "LEGACY_COMPOSER_ALIAS_READINGS",
    "LIMITED_COMPOSER_MODEL",
    "LIMITED_COMPOSER_TERM",
    "attach_complete_composer_initial_ap0_report",
    "build_complete_composer_initial_ap0_decision_report",
    "build_complete_composer_initial_term_meta",
]
