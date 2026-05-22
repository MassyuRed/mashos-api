# -*- coding: utf-8 -*-
from __future__ import annotations

"""Runtime Surface Quality Step12 Exit Gate for EmlisAI.

Step12 is the handoff boundary for the post ProductGate Measurement Runtime
Surface Quality phase.  It reports the next branch, release blockers,
coverage gaps, and QA gaps, but it does not declare Product Gate achieved and
never applies public release.  The payload is meta-only: raw input bodies and
public ``comment_text`` bodies are not allowed.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

RUNTIME_SURFACE_EXIT_GATE_VERSION = "emlis.runtime_surface_exit_gate.v1"
RUNTIME_SURFACE_EXIT_GATE_STEP = "Step12_Exit_Gate"
RUNTIME_SURFACE_EXIT_GATE_SOURCE = "emlis_runtime_surface_quality_step12_exit_gate"
RUNTIME_SURFACE_EXIT_GATE_REQUIRED_CONNECTIONS: tuple[str, ...] = (
    "scorecard_event_connection_ready",
    "scorecard_surface_metrics_connected",
    "coverage_runtime_baseline_connected",
    "runtime_surface_quality_branch_resolver_connected",
    "complete_runtime_activation_branch_connected",
    "surface_aware_self_repair_connected",
    "blind_qa_long_run_connected",
    "release_ladder_connected",
    "public_contract_unchanged",
    "product_release_closed",
)

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "input_feedback_comment",
    "inputFeedbackComment",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
}
_FORBIDDEN_TRUE_FLAGS = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "public_release_applied",
    "product_gate_public_release_applied",
    "product_quality_released",
    "product_gate_achieved",
    "product_gate_reached",
    "runtime_surface_exit_gate_declares_product_gate",
    "runtime_surface_exit_gate_applies_public_release",
    "runtime_surface_exit_gate_changes_public_contract",
    "step12_runtime_surface_exit_gate_changes_public_contract",
    "step12_runtime_surface_exit_gate_relaxes_gate",
    "step12_runtime_surface_exit_gate_uses_raw_input",
    "step12_runtime_surface_exit_gate_uses_comment_text",
)
_CONTRACT_CHANGE_KEYS = (
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
)
_RELEASE_APPLIED_KEYS = (
    "public_release_applied",
    "product_gate_public_release_applied",
    "product_quality_released",
    "product_gate_achieved",
    "product_gate_reached",
)
_REQUIRED_COVERAGE_GROUPS = (
    "short_daily",
    "long_meaning_arc",
    "conflict",
    "recovery",
    "pressure",
    "desire_fear",
    "relationship",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _as_list(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_exit_gate_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_exit_gate",
) -> None:
    """Reject raw text/comment bodies and Step12 contract/release side effects."""

    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if value.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def _extract_events(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        _safe_mapping(event)
        for event in _as_list(report.get("scorecard_events"))
        if _safe_mapping(event)
    ]


def _first_mapping(report: Mapping[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = _safe_mapping(report.get(key))
        if value:
            return value
    return {}


def _collect_blockers_from_sources(*sources: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for source in sources:
        data = _safe_mapping(source)
        for key in (
            "release_blockers",
            "ladder_blockers",
            "exit_gate_blockers",
            "blocking_reasons",
            "step11_release_blockers",
            "product_gate_candidate_blockers",
        ):
            blockers.extend(_dedupe(data.get(key)))
        stage_evaluations = _safe_mapping(data.get("stage_evaluations"))
        for stage in ("internal", "limited", "broader_beta", "product_gate"):
            stage_data = _safe_mapping(stage_evaluations.get(stage))
            blockers.extend(_dedupe(stage_data.get("blockers")))
    return _dedupe(blockers)


def _coverage_gaps(report: Mapping[str, Any], scorecard: Mapping[str, Any]) -> dict[str, Any]:
    baseline = _first_mapping(
        report,
        "coverage_runtime_baseline",
        "runtime_surface_coverage_baseline",
    ) or _safe_mapping(scorecard.get("coverage_runtime_baseline"))
    missing_groups = _dedupe(
        report.get("missing_coverage_groups")
        or scorecard.get("missing_coverage_groups")
        or baseline.get("missing_coverage_groups")
    )
    observed_groups = _dedupe(
        report.get("observed_coverage_groups")
        or scorecard.get("observed_coverage_groups")
        or baseline.get("observed_coverage_groups")
    )
    required_groups = _dedupe(
        report.get("required_coverage_groups")
        or scorecard.get("required_coverage_groups")
        or baseline.get("required_coverage_groups")
        or list(_REQUIRED_COVERAGE_GROUPS)
    )
    missing_count = _int(
        report.get("coverage_group_missing_count"),
        _int(scorecard.get("coverage_group_missing_count"), _int(baseline.get("coverage_group_missing_count"), 0)),
    )
    group_gap_reasons: list[str] = []
    if missing_groups:
        group_gap_reasons.append("required_coverage_groups_missing")
    if missing_count > 0:
        group_gap_reasons.append("coverage_group_missing")
    if len(observed_groups) < len(required_groups):
        group_gap_reasons.append("coverage_group_count_below_required")
    for blocker in _dedupe(baseline.get("release_blockers")):
        group_gap_reasons.append(blocker)
    return {
        "required_coverage_groups": required_groups,
        "observed_coverage_groups": observed_groups,
        "missing_coverage_groups": missing_groups,
        "coverage_group_missing_count": missing_count,
        "coverage_group_count": _int(report.get("coverage_group_count"), _int(scorecard.get("coverage_group_count"), len(observed_groups))),
        "coverage_runtime_baseline_ready": bool(
            report.get("step4_coverage_runtime_baseline_ready")
            or report.get("coverage_runtime_baseline_ready")
            or baseline.get("coverage_runtime_baseline_ready")
            or baseline.get("step4_coverage_runtime_baseline_ready")
        ),
        "coverage_gaps": _dedupe(group_gap_reasons),
        "coverage_gap_blocker": bool(group_gap_reasons),
    }


def _qa_gaps(report: Mapping[str, Any], scorecard: Mapping[str, Any], step11: Mapping[str, Any]) -> dict[str, Any]:
    qa_gaps: list[str] = []
    qa_gaps.extend(_dedupe(report.get("step11_qa_gaps")))
    qa_gaps.extend(_dedupe(scorecard.get("step11_qa_gaps")))
    qa_gaps.extend(_dedupe(step11.get("qa_gaps")))
    qa_gaps.extend(_dedupe(step11.get("step11_qa_gaps")))
    qa_gaps.extend(_dedupe(step11.get("release_blockers")))
    qa_gaps.extend(_dedupe(step11.get("step11_release_blockers")))

    blind_qa_missing_count = _int(
        report.get("blind_qa_missing_count"),
        _int(scorecard.get("blind_qa_missing_count"), _int(step11.get("blind_qa_missing_count"), 0)),
    )
    unreviewed_count = _int(
        report.get("unreviewed_reviewable_candidate_count"),
        _int(scorecard.get("unreviewed_reviewable_candidate_count"), _int(step11.get("unreviewed_reviewable_candidate_count"), 0)),
    )
    read_feeling = step11.get("read_feeling_score")
    if read_feeling is None:
        read_feeling = scorecard.get("read_feeling_score")
    read_feeling_score = _float(read_feeling, -1.0)
    read_target_met = bool(
        step11.get("read_feeling_product_target_met")
        or (read_feeling_score >= 0.90)
    )
    if blind_qa_missing_count > 0:
        qa_gaps.append("blind_qa_missing")
    if unreviewed_count > 0:
        qa_gaps.append("blind_qa_review_missing")
    if read_feeling_score >= 0 and not read_target_met:
        qa_gaps.append("read_feeling_score_below_product_gate_target")
    if step11.get("long_run_surface_signature_repeat_detected") is True:
        qa_gaps.append("long_run_surface_signature_repeat")
    if not (step11.get("step11_blind_qa_long_run_ready") is True or step11.get("runtime_surface_blind_qa_long_run_ready") is True):
        qa_gaps.append("blind_qa_long_run_not_ready")
    return {
        "blind_qa_candidate_count": _int(report.get("blind_qa_candidate_count"), _int(scorecard.get("blind_qa_candidate_count"), _int(step11.get("blind_qa_candidate_count"), 0))),
        "reviewable_blind_qa_candidate_count": _int(report.get("reviewable_blind_qa_candidate_count"), _int(scorecard.get("reviewable_blind_qa_candidate_count"), _int(step11.get("reviewable_blind_qa_candidate_count"), 0))),
        "blind_qa_review_count": _int(report.get("blind_qa_review_count"), _int(scorecard.get("blind_qa_review_count"), _int(step11.get("blind_qa_review_count"), 0))),
        "blind_qa_missing_count": blind_qa_missing_count,
        "unreviewed_reviewable_candidate_count": unreviewed_count,
        "read_feeling_score": None if read_feeling_score < 0 else read_feeling_score,
        "read_feeling_product_target_met": read_target_met,
        "long_run_surface_signature_diversity_rate": step11.get("long_run_surface_signature_diversity_rate"),
        "long_run_surface_signature_repeat_rate": step11.get("long_run_surface_signature_repeat_rate"),
        "long_run_surface_signature_repeat_detected": bool(step11.get("long_run_surface_signature_repeat_detected")),
        "long_run_groups_needing_attention": _dedupe(step11.get("long_run_groups_needing_attention")),
        "qa_gaps": _dedupe(qa_gaps),
        "qa_gap_blocker": bool(_dedupe(qa_gaps)),
    }


def _next_branch(report: Mapping[str, Any], branch: Mapping[str, Any]) -> dict[str, Any]:
    target_layer = _clean(branch.get("target_layer")) or _clean(report.get("runtime_surface_quality_target_layer"))
    next_work_unit = _clean(branch.get("next_work_unit")) or _clean(report.get("runtime_surface_quality_next_step")) or _clean(report.get("next_step_from_runtime_surface_quality_branch"))
    return {
        "target_layer": target_layer,
        "target_area": _clean(branch.get("target_area")) or _clean(report.get("runtime_surface_quality_target_area")),
        "next_work_unit": next_work_unit,
        "selected_reason": _clean(branch.get("selected_reason")) or _clean(report.get("runtime_surface_quality_selected_reason")),
        "repair_allowed": bool(branch.get("repair_allowed") or report.get("runtime_surface_quality_repair_allowed")),
        "requires_diagnostic_enrichment": bool(branch.get("requires_diagnostic_enrichment")),
        "branch_reasons": _dedupe(branch.get("branch_reasons")),
        "touch_files": _dedupe(branch.get("touch_files") or branch.get("touch_targets")),
        "do_not_touch": _dedupe(branch.get("do_not_touch")),
    }


def _events_step_ready(events: Sequence[Mapping[str, Any]], *keys: str) -> bool:
    return bool(events) and all(any(event.get(key) is True for key in keys) for event in events)


def _public_contract_unchanged(report: Mapping[str, Any], release_ladder: Mapping[str, Any]) -> bool:
    for source in (report, release_ladder):
        for key in _CONTRACT_CHANGE_KEYS:
            if source.get(key) is True:
                return False
    return True


def _product_release_closed(report: Mapping[str, Any], release_ladder: Mapping[str, Any]) -> bool:
    for source in (report, release_ladder):
        for key in _RELEASE_APPLIED_KEYS:
            if source.get(key) is True:
                return False
    return True


def build_runtime_surface_exit_gate(
    report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Build the Step12 handoff summary from a measurement report."""

    data = _safe_mapping(report)
    assert_runtime_surface_exit_gate_meta_only(data, source="runtime_surface_exit_gate_report")
    events = _extract_events(data)
    for index, event in enumerate(events, start=1):
        assert_runtime_surface_exit_gate_meta_only(event, source=f"runtime_surface_exit_gate_event[{index}]")

    scorecard = _first_mapping(data, "scorecard", "product_quality_scorecard")
    release_ladder = _safe_mapping(data.get("release_ladder"))
    branch = _first_mapping(
        data,
        "runtime_surface_quality_branch",
        "runtime_surface_quality_branch_resolver",
        "step5_runtime_surface_quality_branch",
    )
    activation = _first_mapping(
        data,
        "runtime_surface_complete_activation_branch",
        "step6_runtime_surface_complete_activation_branch",
        "complete_runtime_activation_branch",
    )
    step11 = _first_mapping(
        data,
        "runtime_surface_blind_qa_long_run_summary",
        "step11_blind_qa_long_run_summary",
    ) or _safe_mapping(scorecard.get("runtime_surface_blind_qa_long_run_summary"))

    coverage = _coverage_gaps(data, scorecard)
    qa = _qa_gaps(data, scorecard, step11)
    branch_handoff = _next_branch(data, branch)

    scorecard_event_connection_ready = bool(
        data.get("scorecard_event_connection_ready")
        or data.get("scorecard_event_adapter_connected")
        or (events and all(event.get("scorecard_event_adapter_ready") is True for event in events))
    )
    scorecard_surface_metrics_connected = bool(
        data.get("step3_scorecard_surface_metrics_connected")
        or scorecard.get("step3_scorecard_surface_metrics_connected")
        or scorecard.get("surface_metrics_ready")
    )
    coverage_baseline_connected = bool(coverage.get("coverage_runtime_baseline_ready"))
    branch_connected = bool(
        data.get("step5_runtime_surface_quality_branch_resolver_ready")
        and branch.get("runtime_surface_quality_branch_resolver_ready")
        and branch_handoff.get("target_layer")
    )
    activation_connected = bool(
        data.get("step6_runtime_surface_complete_activation_branch_ready")
        and activation.get("runtime_surface_complete_activation_branch_ready")
        and _clean(activation.get("activation_status"))
    )
    self_repair_connected = bool(
        data.get("step10_surface_aware_self_repair_connected")
        or _events_step_ready(events, "step10_surface_aware_self_repair_connected")
    )
    blind_qa_long_run_connected = bool(
        step11
        and (data.get("runtime_surface_blind_qa_long_run_version") or step11.get("version"))
    )
    release_ladder_connected = bool(data.get("release_ladder_connected") and release_ladder.get("release_ladder_connected"))
    public_contract_unchanged = _public_contract_unchanged(data, release_ladder)
    product_release_closed = _product_release_closed(data, release_ladder)

    connection_checks = {
        "scorecard_event_connection_ready": scorecard_event_connection_ready,
        "scorecard_surface_metrics_connected": scorecard_surface_metrics_connected,
        "coverage_runtime_baseline_connected": coverage_baseline_connected,
        "runtime_surface_quality_branch_resolver_connected": branch_connected,
        "complete_runtime_activation_branch_connected": activation_connected,
        "surface_aware_self_repair_connected": self_repair_connected,
        "blind_qa_long_run_connected": blind_qa_long_run_connected,
        "release_ladder_connected": release_ladder_connected,
        "public_contract_unchanged": public_contract_unchanged,
        "product_release_closed": product_release_closed,
    }
    connection_blockers = [key for key, value in connection_checks.items() if value is not True]

    release_blockers = _collect_blockers_from_sources(data, scorecard, release_ladder, step11)
    release_blockers.extend(coverage.get("coverage_gaps", []))
    release_blockers.extend(qa.get("qa_gaps", []))
    release_blockers = _dedupe(release_blockers)
    handoff_ready = not connection_blockers
    product_gate_candidate_ready = bool(
        release_ladder.get("product_gate_candidate_ready")
        or release_ladder.get("product_gate_transition_allowed")
    )

    summary = {
        "version": RUNTIME_SURFACE_EXIT_GATE_VERSION,
        "schema_version": RUNTIME_SURFACE_EXIT_GATE_VERSION,
        "source": RUNTIME_SURFACE_EXIT_GATE_SOURCE,
        "source_step": RUNTIME_SURFACE_EXIT_GATE_STEP,
        "step": RUNTIME_SURFACE_EXIT_GATE_STEP,
        "target_step": RUNTIME_SURFACE_EXIT_GATE_STEP,
        "run_id": _clean(data.get("run_id")),
        "runtime_surface_quality_exit_gate_connected": True,
        "step12_exit_gate_connected": True,
        "runtime_surface_quality_exit_gate_summary_ready": handoff_ready,
        "runtime_surface_quality_exit_gate_ready": handoff_ready,
        "step12_runtime_surface_quality_exit_gate_ready": handoff_ready,
        "step12_exit_gate_ready": handoff_ready,
        "runtime_surface_exit_gate_ready": handoff_ready,
        "runtime_surface_quality_exit_gate_complete": handoff_ready,
        "runtime_surface_quality_exit_gate_completed": handoff_ready,
        "step12_exit_gate_completed": handoff_ready,
        "runtime_surface_quality_handoff_ready": handoff_ready,
        "handoff_only": True,
        "measurement_connection_complete": bool(data.get("measurement_connection_complete") or data.get("measurement_connection_completed")),
        "product_gate_candidate_ready_from_release_ladder": product_gate_candidate_ready,
        "product_gate_candidate_ready_but_public_release_not_applied": product_gate_candidate_ready,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_achieved": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "runtime_surface_exit_gate_declares_product_gate": False,
        "runtime_surface_exit_gate_applies_public_release": False,
        "runtime_surface_exit_gate_changes_public_contract": False,
        "next_branch": branch_handoff,
        "runtime_surface_quality_next_branch": branch_handoff,
        "runtime_surface_quality_next_layer": branch_handoff.get("target_layer"),
        "runtime_surface_quality_next_step": branch_handoff.get("next_work_unit"),
        "runtime_surface_quality_selected_reason": branch_handoff.get("selected_reason"),
        "release_blockers": release_blockers,
        "runtime_surface_quality_release_blockers": release_blockers,
        "remaining_blockers": release_blockers,
        "all_remaining_blockers": release_blockers,
        "coverage_gaps": coverage.get("coverage_gaps"),
        "runtime_surface_quality_coverage_gaps": coverage,
        "qa_gaps": qa.get("qa_gaps"),
        "step11_qa_gaps": qa.get("qa_gaps"),
        "step11_release_blockers": _dedupe(step11.get("step11_release_blockers") or step11.get("release_blockers")),
        "runtime_surface_quality_qa_gaps": qa,
        "coverage_gap_summary": coverage,
        "qa_gap_summary": qa,
        "coverage_gap_blocker": coverage.get("coverage_gap_blocker"),
        "qa_gap_blocker": qa.get("qa_gap_blocker"),
        "connection_checks": connection_checks,
        "exit_gate_checks": connection_checks,
        "connection_blockers": connection_blockers,
        "exit_gate_blockers": connection_blockers,
        "runtime_surface_quality_exit_gate_blockers": connection_blockers,
        "runtime_surface_quality_handoff_blockers": release_blockers,
        "handoff_blockers": connection_blockers,
        "required_connections": list(RUNTIME_SURFACE_EXIT_GATE_REQUIRED_CONNECTIONS),
        "public_contract_unchanged": public_contract_unchanged,
        "product_release_closed": product_release_closed,
        "release_judgment": {
            "release_allowed": False,
            "reason": "step12_runtime_surface_quality_exit_gate_handoff_only_public_release_not_applied",
            "product_gate_candidate_ready_from_release_ladder": product_gate_candidate_ready,
            "runtime_surface_quality_exit_gate_ready": handoff_ready,
        },
        "meta_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "step12_runtime_surface_exit_gate_changes_public_contract": False,
        "step12_runtime_surface_exit_gate_relaxes_gate": False,
        "step12_runtime_surface_exit_gate_uses_raw_input": False,
        "step12_runtime_surface_exit_gate_uses_comment_text": False,
    }
    assert_runtime_surface_exit_gate_meta_only(summary)
    return summary


def dump_runtime_surface_exit_gate(summary: Mapping[str, Any] | None = None) -> str:
    data = dict(summary or {})
    if not data:
        data = build_runtime_surface_exit_gate({})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_runtime_surface_exit_gate_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_runtime_surface_quality_exit_gate = build_runtime_surface_exit_gate
build_runtime_surface_quality_exit_gate_summary = build_runtime_surface_exit_gate
build_runtime_surface_exit_gate_summary = build_runtime_surface_exit_gate


__all__ = [
    "RUNTIME_SURFACE_EXIT_GATE_VERSION",
    "RUNTIME_SURFACE_EXIT_GATE_STEP",
    "RUNTIME_SURFACE_EXIT_GATE_SOURCE",
    "RUNTIME_SURFACE_EXIT_GATE_REQUIRED_CONNECTIONS",
    "assert_runtime_surface_exit_gate_meta_only",
    "build_runtime_surface_exit_gate",
    "build_runtime_surface_quality_exit_gate",
    "build_runtime_surface_quality_exit_gate_summary",
    "build_runtime_surface_exit_gate_summary",
    "dump_runtime_surface_exit_gate",
]
