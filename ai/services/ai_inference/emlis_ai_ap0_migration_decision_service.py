# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step18 A-P0 migration decision for EmlisAI.

This module is developer / internal-QA meta only.  It turns the Step01-17
materials into a checklist decision: proceed to Step19 A-1, or return to the
specific B-plan step that still needs work.  It never generates user-facing
``comment_text`` and it never changes API routes, DB physical names, or public
response keys.
"""

from collections import Counter
from typing import Any, Dict, Iterable, List, Mapping, Sequence

STEP18_VERSION = "emlis.step18_ap0_migration_decision.v1"
STEP18_PHASE = "A-P0"
STEP18_STEP = "Step18_ap0_migration_decision"
STEP18_DECISION_PROCEED = "proceed_to_step19_a1"
STEP18_DECISION_RETURN = "return_to_b_plan_steps"
STEP18_DECISION_HOLD = "hold_in_b_plan"

DIAGNOSTIC_STAGES = {"flag", "rollout", "scope", "composer", "reader", "grounding", "template", "display"}
ROLLOUT_STAGES = {"off", "internal", "tutorial", "limited_cases", "all"}
UNKNOWN_REASON_CODES = {"", "unknown", "unclassified", "not_classified", "gate_not_classified", "composer_not_classified"}

STEP18_REQUIRED_INPUT_AREAS = (
    "life",
    "body_condition",
    "relationship",
    "study",
    "work",
    "long_meaning_arc",
    "history_scope",
    "cross_core_scope",
)

STEP18_REQUIRED_COVERAGE_GROUPS = (
    "energy_fatigue",
    "anxiety",
    "anger_hurt",
    "positive_recovery",
    "relationship",
    "limit_escape",
    "value_wish",
    "long_meaning_arc",
)

STEP18_BLOCKING_CHECKS = (
    "startup_diagnostics",
    "normal_connection",
    "rollout_distribution",
    "step17_broad_fixtures",
    "scope_coverage",
    "composer_coverage",
    "long_input",
    "history_cross_core",
    "template_avoidance",
    "display_boundary",
)

_CHECK_META: Dict[str, Dict[str, Any]] = {
    "startup_diagnostics": {
        "label": "起動診断",
        "return_steps": ["Step01_diagnostic_summary", "Step02_pre_connection", "Step03_scope_diagnostic", "Step04_composer_diagnostic", "Step05_gate_diagnostic"],
    },
    "normal_connection": {
        "label": "通常接続",
        "return_steps": ["Step06_b_plan_normal_connection", "Step07_scoped_grounding_frontend_passed_only"],
    },
    "rollout_distribution": {
        "label": "段階リリース計測",
        "return_steps": ["Step16_rollout_metrics"],
    },
    "step17_broad_fixtures": {
        "label": "広い入力 fixture",
        "return_steps": ["Step17_broad_input_fixtures"],
    },
    "scope_coverage": {
        "label": "scope coverage",
        "return_steps": ["Step08_coverage_matrix", "Step09_scope_expansion", "Step10_safety_boundary"],
    },
    "composer_coverage": {
        "label": "Composer coverage",
        "return_steps": ["Step11_phrase_unit_role_expansion", "Step12_profile_sentence_plan_expansion", "Step13_surface_realizer"],
    },
    "long_input": {
        "label": "long input",
        "return_steps": ["Step12_profile_sentence_plan_expansion", "Step15_common_core_stabilization"],
    },
    "history_cross_core": {
        "label": "history / cross core",
        "return_steps": ["Step09_scope_expansion", "Step18_ap0_migration_decision"],
    },
    "template_avoidance": {
        "label": "template 回避",
        "return_steps": ["Step13_surface_realizer", "Step14_guard_strengthening", "Step15_common_core_stabilization"],
    },
    "display_boundary": {
        "label": "表示境界",
        "return_steps": ["Step07_scoped_grounding_frontend_passed_only", "Step14_guard_strengthening"],
    },
    "a_plan_equivalent": {
        "label": "A案相当",
        "return_steps": ["Step19_a_plan_equivalent_composer", "Step20_long_term_quality"],
    },
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


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
    seen: set[str] = set()
    for raw in values:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean(value).lower() in {"1", "true", "yes", "y", "on", "passed", "green", "ok"}


def _counter(value: Any) -> Counter[str]:
    if isinstance(value, Counter):
        return Counter({str(k): int(v) for k, v in value.items() if str(k)})
    if isinstance(value, Mapping):
        return Counter({str(k): int(v) for k, v in dict(value).items() if str(k)})
    return Counter()


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _dedupe(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for raw in values:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _nested(*sources: Mapping[str, Any], key: str) -> Dict[str, Any]:
    for source in sources:
        value = source.get(key) if isinstance(source, Mapping) else None
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _rollout_aggregate(rollout_metrics: Mapping[str, Any], rollout_metrics_aggregate: Mapping[str, Any] | None) -> Dict[str, Any]:
    explicit = _mapping(rollout_metrics_aggregate)
    if explicit:
        return explicit
    for key in ("rollout_metrics_aggregate", "internal_qa_aggregate", "aggregate", "rollout_aggregate"):
        nested = _nested(rollout_metrics, key=key)
        if nested:
            return nested
    return {}


def _aggregate_failure_total(aggregate: Mapping[str, Any], rollout_metrics: Mapping[str, Any]) -> int:
    return (
        _int(aggregate.get("rejected") or aggregate.get("rejected_count"))
        + _int(aggregate.get("unavailable") or aggregate.get("unavailable_count"))
        + _int(aggregate.get("safety_blocked") or aggregate.get("safety_blocked_count"))
        + _int(aggregate.get("blocked_before_attempt_count"))
        + (1 if _bool(rollout_metrics.get("blocked_before_attempt")) else 0)
    )


def _unclassified_reason_count(
    *,
    diagnostic_summary: Mapping[str, Any],
    coverage_matrix: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    aggregate: Mapping[str, Any],
) -> int:
    values = [
        _int(aggregate.get("unclassified_reason_count") or aggregate.get("coverage_unclassified_reason_count")),
        _int(rollout_metrics.get("unclassified_reason_count") or rollout_metrics.get("coverage_unclassified_reason_count")),
        len(_list(diagnostic_summary.get("coverage_unclassified_reasons"))),
        len(_list(diagnostic_summary.get("coverage_unmapped_reasons"))),
        len(_list(coverage_matrix.get("unclassified_reasons"))),
        len(_list(coverage_matrix.get("unmapped_reason_codes"))),
    ]
    return max(values or [0])


def _check(check_key: str, green: bool, *, reason: str, evidence: Mapping[str, Any] | None = None, blocking: bool = True) -> Dict[str, Any]:
    meta = _CHECK_META.get(check_key, {})
    return {
        "check_key": check_key,
        "label": meta.get("label", check_key),
        "phase": STEP18_PHASE,
        "blocking": bool(blocking),
        "green": bool(green),
        "status": "green" if green else "red",
        "primary_reason": "green" if green else (reason or "not_ready"),
        "reason": reason or ("green" if green else "not_ready"),
        "return_steps": [] if green else list(meta.get("return_steps") or []),
        "evidence": dict(evidence or {}),
    }


def _deferred_check(check_key: str, *, reason: str) -> Dict[str, Any]:
    meta = _CHECK_META.get(check_key, {})
    return {
        "check_key": check_key,
        "label": meta.get("label", check_key),
        "phase": "A-1/A-2",
        "blocking": False,
        "green": False,
        "status": "deferred",
        "primary_reason": reason,
        "reason": reason,
        "return_steps": list(meta.get("return_steps") or []),
        "evidence": {"deferred_until": list(meta.get("return_steps") or [])},
    }


def _input_areas(summary: Mapping[str, Any]) -> List[str]:
    return _dedupe([*_list(summary.get("input_areas")), *_list(summary.get("covered_input_areas")), *_list(summary.get("required_input_areas_covered"))])


def _coverage_groups(*sources: Mapping[str, Any]) -> List[str]:
    out: List[str] = []
    for source in sources:
        out.extend(_list(source.get("coverage_groups")))
        out.extend(_list(source.get("required_coverage_groups")))
        out.extend(_list(source.get("active_groups")))
        out.extend(_list(source.get("covered_coverage_groups")))
    return _dedupe(out)


def _broad_fixture_check(broad: Mapping[str, Any]) -> Dict[str, Any]:
    input_areas = _input_areas(broad)
    coverage_groups = _coverage_groups(broad)
    missing_areas = [key for key in STEP18_REQUIRED_INPUT_AREAS if key not in set(input_areas)]
    missing_groups = [key for key in STEP18_REQUIRED_COVERAGE_GROUPS if key not in set(coverage_groups)]
    no_exact_contract = not _bool(broad.get("exact_sentence_contract")) and not _bool(broad.get("expected_comment_text_locked")) and not _bool(broad.get("must_equal_text_contract"))
    structural_fields = bool(
        _bool(broad.get("used_evidence_span_ids_checked"))
        or _bool(broad.get("quality_flags_checked"))
        or _bool(broad.get("forbidden_surface_checked"))
        or _bool(broad.get("structure_level_expectations"))
    )
    fixture_version = _clean(broad.get("version") or broad.get("fixture_version"))
    passed = bool(fixture_version and not missing_areas and not missing_groups and no_exact_contract and structural_fields)
    return _check(
        "step17_broad_fixtures",
        passed,
        reason="missing_step17_fixture_material" if not passed else "green",
        evidence={
            "fixture_version": fixture_version,
            "input_areas": input_areas,
            "coverage_groups": coverage_groups,
            "missing_input_areas": missing_areas,
            "missing_coverage_groups": missing_groups,
            "no_exact_sentence_contract": no_exact_contract,
            "structure_level_expectations": structural_fields,
        },
    )


def _startup_diagnostics_check(
    *,
    diagnostic_summary: Mapping[str, Any],
    coverage_matrix: Mapping[str, Any],
    rollout_metrics: Mapping[str, Any],
    aggregate: Mapping[str, Any],
) -> Dict[str, Any]:
    stage = _clean(diagnostic_summary.get("stage"))
    primary = _clean(diagnostic_summary.get("primary_reason"))
    failure_total = _aggregate_failure_total(aggregate, rollout_metrics)
    unclassified = _unclassified_reason_count(
        diagnostic_summary=diagnostic_summary,
        coverage_matrix=coverage_matrix,
        rollout_metrics=rollout_metrics,
        aggregate=aggregate,
    )
    classified = bool(stage in DIAGNOSTIC_STAGES and primary.lower() not in UNKNOWN_REASON_CODES)
    not_major = bool(unclassified == 0 or unclassified < max(1, failure_total))
    return _check(
        "startup_diagnostics",
        bool(classified and not_major),
        reason="unclassified_reason_still_major" if classified and not not_major else "diagnostic_summary_not_classified",
        evidence={
            "stage": stage,
            "primary_reason": primary,
            "unclassified_reason_count": unclassified,
            "failure_total": failure_total,
            "diagnostic_summary_version": _clean(diagnostic_summary.get("version")),
        },
    )


def _normal_connection_check(*, diagnostic_summary: Mapping[str, Any], rollout_metrics: Mapping[str, Any]) -> Dict[str, Any]:
    rollout_stage = _clean(diagnostic_summary.get("rollout_stage") or rollout_metrics.get("rollout_stage") or rollout_metrics.get("stage"))
    has_attempt_field = "attempted" in rollout_metrics or "rollout_attempted" in diagnostic_summary or "composer_connection_attempted" in diagnostic_summary
    default_resolution = _nested(diagnostic_summary, key="default_composer_resolution") or _nested(diagnostic_summary, key="registry_resolution")
    release_decision = _nested(diagnostic_summary, key="release_decision") or _nested(diagnostic_summary, key="rollout_decision")
    normal_connection = _nested(diagnostic_summary, key="normal_connection") or _nested(diagnostic_summary, key="b_plan_connection")
    composer_model = _clean(diagnostic_summary.get("composer_model") or rollout_metrics.get("composer_model"))
    ready = bool(
        _clean(rollout_metrics.get("version"))
        and rollout_stage in ROLLOUT_STAGES
        and has_attempt_field
        and composer_model
        and (default_resolution or release_decision or normal_connection)
    )
    return _check(
        "normal_connection",
        ready,
        reason="normal_connection_meta_incomplete",
        evidence={
            "rollout_stage": rollout_stage,
            "has_attempt_field": has_attempt_field,
            "composer_model": composer_model,
            "has_default_resolution": bool(default_resolution),
            "has_release_decision": bool(release_decision),
            "has_normal_connection": bool(normal_connection),
            "step16_metrics_version": _clean(rollout_metrics.get("version")),
        },
    )


def _rollout_distribution_check(*, rollout_metrics: Mapping[str, Any], aggregate: Mapping[str, Any]) -> Dict[str, Any]:
    event_count = _int(aggregate.get("event_count") or aggregate.get("record_count") or rollout_metrics.get("record_count") or rollout_metrics.get("event_count"))
    attempted_count = _int(aggregate.get("attempted") or aggregate.get("attempted_count") or rollout_metrics.get("attempted_count"))
    failure_total = _aggregate_failure_total(aggregate, rollout_metrics)
    primary_reason_counts = _counter(aggregate.get("primary_reason_counts") or aggregate.get("by_primary_reason") or rollout_metrics.get("primary_reason_counts"))
    coverage_counts = _counter(aggregate.get("coverage_group_counts") or aggregate.get("by_coverage_group") or rollout_metrics.get("coverage_group_counts"))
    ap0 = _nested(aggregate, key="ap0_judgement") or _nested(rollout_metrics, key="ap0_judgement")
    do_not_promote_from_passed_only = _bool(ap0.get("do_not_promote_from_passed_only")) or failure_total > 0
    ready = bool(
        event_count > 0
        and attempted_count >= 0
        and primary_reason_counts
        and coverage_counts
        and do_not_promote_from_passed_only
    )
    return _check(
        "rollout_distribution",
        ready,
        reason="passed_only_metrics_are_not_enough" if event_count > 0 and not do_not_promote_from_passed_only else "rollout_distribution_incomplete",
        evidence={
            "event_count": event_count,
            "attempted_count": attempted_count,
            "failure_total": failure_total,
            "primary_reason_counts": dict(primary_reason_counts),
            "coverage_group_counts": dict(coverage_counts),
            "do_not_promote_from_passed_only": do_not_promote_from_passed_only,
        },
    )


def _scope_coverage_check(*, broad: Mapping[str, Any], coverage_matrix: Mapping[str, Any], diagnostic_summary: Mapping[str, Any]) -> Dict[str, Any]:
    groups = _coverage_groups(broad, coverage_matrix, diagnostic_summary)
    missing = [key for key in STEP18_REQUIRED_COVERAGE_GROUPS if key not in set(groups)]
    explicit_reasons = bool(
        _bool(broad.get("explicit_out_of_scope_reasons_classified"))
        or _list(coverage_matrix.get("next_steps"))
        or _list(coverage_matrix.get("unclassified_reasons")) == []
    )
    eligible_or_classified = bool(
        _bool(broad.get("scope_coverage_ready"))
        or _clean(diagnostic_summary.get("scope_status")) in {"eligible", "out_of_scope", "safety_blocked"}
        or explicit_reasons
    )
    green = bool(not missing and eligible_or_classified)
    return _check(
        "scope_coverage",
        green,
        reason="required_coverage_groups_not_ready" if missing else "scope_reasons_not_classified",
        evidence={
            "coverage_groups": groups,
            "missing_required_coverage_groups": missing,
            "scope_status": _clean(diagnostic_summary.get("scope_status")),
            "eligible_or_classified": eligible_or_classified,
        },
    )


def _composer_coverage_check(*, broad: Mapping[str, Any]) -> Dict[str, Any]:
    profile = _nested(broad, key="profile_coverage") or _nested(broad, key="composer_coverage") or broad
    known_profiles = _list(profile.get("known_profiles")) or _list(profile.get("covered_profiles"))
    known_ok = _bool(profile.get("known_profile_variants_passed")) or len(known_profiles) >= 4
    unknown_ok = _bool(profile.get("unknown_shallow_path_covered")) or "current_input_core" in known_profiles
    vocab_ok = _bool(profile.get("vocabulary_variants_passed")) or _bool(profile.get("profile_generalization_passed"))
    phrase_ok = _bool(profile.get("phrase_unit_role_coverage_passed")) or _bool(profile.get("phrase_unit_roles_checked"))
    sentence_plan_ok = _bool(profile.get("sentence_plan_coverage_passed")) or _bool(profile.get("sentence_plans_checked"))
    green = bool(known_ok and unknown_ok and vocab_ok and phrase_ok and sentence_plan_ok)
    return _check(
        "composer_coverage",
        green,
        reason="composer_profile_or_shallow_coverage_incomplete",
        evidence={
            "known_profiles": known_profiles,
            "known_profile_variants_passed": known_ok,
            "unknown_shallow_path_covered": unknown_ok,
            "vocabulary_variants_passed": vocab_ok,
            "phrase_unit_role_coverage_passed": phrase_ok,
            "sentence_plan_coverage_passed": sentence_plan_ok,
        },
    )


def _long_input_check(*, broad: Mapping[str, Any]) -> Dict[str, Any]:
    long_summary = _nested(broad, key="long_input") or broad
    grounded = _bool(long_summary.get("long_meaning_arc_grounded")) or _bool(long_summary.get("long_input_grounded"))
    multi = _bool(long_summary.get("multiple_sentences_or_paragraphs_grounded")) or _bool(long_summary.get("paragraph_grounding_checked")) or _int(long_summary.get("min_sentence_plans")) >= 2
    core = _bool(long_summary.get("common_core_guards_passed")) or _bool(long_summary.get("text_generation_core_guarded"))
    green = bool(grounded and multi and core)
    return _check(
        "long_input",
        green,
        reason="long_meaning_arc_not_grounded_enough",
        evidence={
            "long_meaning_arc_grounded": grounded,
            "multiple_sentences_or_paragraphs_grounded": multi,
            "common_core_guards_passed": core,
        },
    )


def _history_cross_core_check(*, broad: Mapping[str, Any]) -> Dict[str, Any]:
    history = _nested(broad, key="history_cross_core") or _nested(broad, key="context_scope") or broad
    history_ok = _bool(history.get("history_scope_grounded")) or _bool(history.get("history_current_input_grounded"))
    cross_ok = _bool(history.get("cross_core_scope_grounded")) or _bool(history.get("cross_core_current_input_grounded"))
    separated = _bool(history.get("history_current_evidence_separated")) or _bool(history.get("current_and_history_evidence_separated"))
    cross_separated = _bool(history.get("cross_core_current_input_only_grounded")) or _bool(history.get("cross_core_evidence_separated"))
    green = bool(history_ok and cross_ok and separated and cross_separated)
    return _check(
        "history_cross_core",
        green,
        reason="history_or_cross_core_scope_not_grounded",
        evidence={
            "history_scope_grounded": history_ok,
            "cross_core_scope_grounded": cross_ok,
            "history_current_evidence_separated": separated,
            "cross_core_current_input_only_grounded": cross_separated,
        },
    )


def _template_avoidance_check(*, broad: Mapping[str, Any], guard: Mapping[str, Any]) -> Dict[str, Any]:
    combined = {**broad, **guard}
    fixed = _bool(combined.get("fixed_sentence_guard_passed")) or _bool(combined.get("surface_variation_without_template"))
    raw_copy = _bool(combined.get("raw_evidence_copy_rejected")) or _bool(combined.get("raw_evidence_sentence_copy_rejected"))
    repeated = _bool(combined.get("repeated_surface_rejected")) or _bool(combined.get("repeated_sentence_tail_rejected"))
    overclaim = _bool(combined.get("overclaim_guard_passed")) or _bool(combined.get("no_general_knowledge_completion")) or _bool(combined.get("general_knowledge_completion_rejected"))
    no_templates_added = not _bool(combined.get("completion_sentence_templates_added")) and not _bool(combined.get("fallback_observation_sentence_added"))
    green = bool(fixed and raw_copy and repeated and overclaim and no_templates_added)
    return _check(
        "template_avoidance",
        green,
        reason="template_or_overclaim_guard_incomplete",
        evidence={
            "fixed_sentence_guard_passed": fixed,
            "raw_evidence_copy_rejected": raw_copy,
            "repeated_surface_rejected": repeated,
            "overclaim_guard_passed": overclaim,
            "no_templates_added": no_templates_added,
        },
    )


def _display_boundary_check(*, diagnostic_summary: Mapping[str, Any], frontend: Mapping[str, Any]) -> Dict[str, Any]:
    status = _clean(diagnostic_summary.get("observation_status"))
    comment_allowed = _bool(diagnostic_summary.get("comment_text_allowed"))
    current_contract_ok = bool(not status or status == "passed" or not comment_allowed)
    frontend_ok = _bool(frontend.get("passed_only_contract_preserved")) or _bool(frontend.get("frontend_modal_only_passed"))
    rejected_empty = _bool(frontend.get("rejected_comment_text_empty")) or _bool(frontend.get("non_passed_comment_text_empty")) or current_contract_ok
    safety_empty = _bool(frontend.get("safety_blocked_comment_text_empty")) or current_contract_ok
    green = bool(current_contract_ok and (frontend_ok or rejected_empty) and rejected_empty and safety_empty)
    return _check(
        "display_boundary",
        green,
        reason="passed_only_display_contract_incomplete",
        evidence={
            "observation_status": status,
            "comment_text_allowed": comment_allowed,
            "current_contract_ok": current_contract_ok,
            "frontend_passed_only_contract": frontend_ok,
            "rejected_comment_text_empty": rejected_empty,
            "safety_blocked_comment_text_empty": safety_empty,
        },
    )


def build_step18_ap0_migration_decision(
    *,
    diagnostic_summary: Mapping[str, Any] | None = None,
    rollout_metrics: Mapping[str, Any] | None = None,
    rollout_metrics_aggregate: Mapping[str, Any] | None = None,
    coverage_matrix: Mapping[str, Any] | None = None,
    broad_input_fixture_summary: Mapping[str, Any] | None = None,
    guard_test_summary: Mapping[str, Any] | None = None,
    frontend_boundary_summary: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the A-P0 checklist decision.

    ``can_proceed_to_a1`` means that the Step01-17 evidence is sufficient to
    start Step19.  It does not certify that the A-1 composer is already
    installed; the A-plan-equivalent check is recorded as a deferred post-A-P0
    check.
    """

    diagnostic = _mapping(diagnostic_summary)
    rollout = _mapping(rollout_metrics)
    aggregate = _rollout_aggregate(rollout, rollout_metrics_aggregate)
    matrix = _mapping(coverage_matrix) or _nested(diagnostic, key="coverage_matrix")
    broad = _mapping(broad_input_fixture_summary)
    guard = _mapping(guard_test_summary)
    frontend = _mapping(frontend_boundary_summary)

    checks = [
        _startup_diagnostics_check(diagnostic_summary=diagnostic, coverage_matrix=matrix, rollout_metrics=rollout, aggregate=aggregate),
        _normal_connection_check(diagnostic_summary=diagnostic, rollout_metrics=rollout),
        _rollout_distribution_check(rollout_metrics=rollout, aggregate=aggregate),
        _broad_fixture_check(broad),
        _scope_coverage_check(broad=broad, coverage_matrix=matrix, diagnostic_summary=diagnostic),
        _composer_coverage_check(broad=broad),
        _long_input_check(broad=broad),
        _history_cross_core_check(broad=broad),
        _template_avoidance_check(broad=broad, guard=guard),
        _display_boundary_check(diagnostic_summary=diagnostic, frontend=frontend),
    ]
    post_ap0_checks = [
        _deferred_check("a_plan_equivalent", reason="checked_after_step19_and_step20"),
    ]

    blocking = [item for item in checks if item.get("blocking")]
    unmet = [item for item in blocking if not item.get("green")]
    return_steps = _dedupe(step for item in unmet for step in list(item.get("return_steps") or []))
    can_proceed = not unmet
    decision = STEP18_DECISION_PROCEED if can_proceed else STEP18_DECISION_RETURN
    next_step = "Step19_a_plan_equivalent_composer" if can_proceed else (return_steps[0] if return_steps else "Step18_ap0_migration_decision")

    check_results = {str(item["check_key"]): item for item in checks}
    green_keys = [item["check_key"] for item in checks if item.get("green")]
    unmet_keys = [item["check_key"] for item in unmet]

    return {
        "version": STEP18_VERSION,
        "phase": STEP18_PHASE,
        "step": STEP18_STEP,
        "purpose": "a_p0_migration_judgement_from_step01_to_step17_materials",
        "ready": True,
        "decision_ready": True,
        "green": bool(can_proceed),
        "can_proceed_to_a1": bool(can_proceed),
        "can_enter_step19": bool(can_proceed),
        "decision": decision,
        "next_step": next_step,
        "return_steps": return_steps,
        "unmet_checks": unmet_keys,
        "unmet_check_count": len(unmet_keys),
        "green_checks": green_keys,
        "green_check_count": len(green_keys),
        "blocking_check_count": len(blocking),
        "check_order": list(STEP18_BLOCKING_CHECKS),
        "check_results": check_results,
        "checks": checks,
        "post_ap0_checks": post_ap0_checks,
        "a_plan_equivalent_check_deferred": True,
        "do_not_promote_from_passed_only": True,
        "passed_only_metrics_accepted": False,
        "external_ai_used": False,
        "fallback_observation_sentence_added": False,
        "fixed_observation_sentence_added": False,
        "comment_text_contract_preserved": bool(check_results.get("display_boundary", {}).get("green")),
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "piece_analysis_text_generation_started": False,
        "evidence_summary": {
            "diagnostic_stage": _clean(diagnostic.get("stage")),
            "primary_reason": _clean(diagnostic.get("primary_reason")),
            "rollout_metrics_version": _clean(rollout.get("version")),
            "rollout_aggregate_version": _clean(aggregate.get("version")),
            "rollout_event_count": _int(aggregate.get("event_count") or aggregate.get("record_count") or rollout.get("record_count")),
            "coverage_groups": _coverage_groups(broad, matrix, diagnostic),
            "fixture_version": _clean(broad.get("version") or broad.get("fixture_version")),
            "guard_summary_version": _clean(guard.get("version")),
            "frontend_summary_version": _clean(frontend.get("version")),
        },
    }


# Backward / ergonomic alias for tests and future callers.
def build_emlis_ap0_migration_decision(**kwargs: Any) -> Dict[str, Any]:
    return build_step18_ap0_migration_decision(**kwargs)


__all__ = [
    "STEP18_BLOCKING_CHECKS",
    "STEP18_DECISION_HOLD",
    "STEP18_DECISION_PROCEED",
    "STEP18_DECISION_RETURN",
    "STEP18_PHASE",
    "STEP18_REQUIRED_COVERAGE_GROUPS",
    "STEP18_REQUIRED_INPUT_AREAS",
    "STEP18_STEP",
    "STEP18_VERSION",
    "build_emlis_ap0_migration_decision",
    "build_step18_ap0_migration_decision",
]
