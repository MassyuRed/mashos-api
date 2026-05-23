# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step10 Render-visible exit criteria for EmlisAI runtime surface quality.

This checker consumes meta-only ``emlis_observation_diagnostic_lockdown`` rows
and optional in-memory displayed surfaces.  It never stores raw input or public
comment bodies in returned reports, and it does not change RN/API/DB contracts.
"""

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

RUNTIME_SURFACE_EXIT_CRITERIA_VERSION = "emlis.runtime_surface_exit_criteria.v1"
RUNTIME_SURFACE_EXIT_CRITERIA_STEP = "Step10_Runtime_Surface_Exit_Criteria"
RUNTIME_SURFACE_EXIT_CRITERIA_SOURCE = "emlis_runtime_surface_exit_criteria"

CASE_KIND_NORMAL_INPUT = "normal_input"
CASE_KIND_LOW_INFORMATION = "low_information"
CASE_KIND_BROKEN_SURFACE = "broken_surface"
RUNTIME_SURFACE_EXIT_CRITERIA_CASE_KINDS = (CASE_KIND_NORMAL_INPUT, CASE_KIND_LOW_INFORMATION, CASE_KIND_BROKEN_SURFACE)
OUTCOME_PASSED_DISPLAYED = "passed"
OUTCOME_SURFACE_BLOCKED = "surface_blocked"
OUTCOME_NON_DISPLAY = "non_display"
OUTCOME_FAILED = "blocked"

REQUIRED_EXIT_CRITERIA_CHECKS = (
    "normal_input_display_confirmed",
    "low_information_branch_confirmed",
    "broken_surface_blocked_confirmed",
    "public_contract_unchanged",
)

_FORBIDDEN = (
    ("malformed_nominalization_imamade_koto", re.compile(r"今までこと")),
    ("malformed_nominalization_daijoubu_koto", re.compile(r"大丈夫こと")),
    ("malformed_nominalization_mada_naika_koto", re.compile(r"まだないかこと")),
    ("malformed_nominalization_shirenai_dore_koto", re.compile(r"しれないどれこと")),
    ("malformed_nominalization_umaku_nasenakute_koto", re.compile(r"上手になせなくてこと")),
    ("generic_center_phrase", re.compile(r"[^。\n]{1,80}が中心にあります")),
    ("repeated_sono_nakademo", re.compile(r"その中でも、[\s\S]*その中でも、")),
)
_FORBIDDEN_MARKERS = ("今までこと", "大丈夫こと", "まだないかこと", "しれないどれこと", "上手になせなくてこと", "が中心にあります", "その中でも")
_FORBIDDEN_KEYS = {
    "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
    "input", "input_text", "inputText", "user_input", "userInput", "memo", "memo_text",
    "memoText", "current_input", "currentInput", "comment_text", "commentText",
    "input_feedback_comment", "inputFeedbackComment", "public_comment_text", "candidate_comment_text",
    "reply_text", "replyText", "surface_text", "realized_text", "line_text", "body", "text",
    "sentence", "sentences", "phrase", "raw_quote", "raw_quotes", "matched_raw_quote_fragments",
}
_CONTRACT_FLAGS = (
    "raw_input_included", "raw_text_included", "input_text_included", "comment_text_included",
    "comment_text_body_included", "displayed_comment_text_included", "response_shape_changed",
    "public_response_key_change", "public_response_key_changed", "api_route_changed",
    "db_schema_changed", "db_physical_name_changed", "rn_visible_contract_changed",
    "rn_display_contract_changed", "display_gate_relaxed", "grounding_gate_relaxed",
    "template_gate_relaxed", "reader_gate_relaxed", "gate_relaxed",
)

class RuntimeSurfaceExitCriteriaError(AssertionError):
    pass


def _m(v: Any) -> dict[str, Any]:
    return dict(v) if isinstance(v, Mapping) else {}


def _s(v: Any) -> str:
    if v is None or isinstance(v, (Mapping, list, tuple, set)):
        return ""
    return str(v).strip()


def _b(v: Any) -> bool:
    if isinstance(v, bool): return v
    if isinstance(v, (int, float)): return bool(v)
    if isinstance(v, str): return v.strip().lower() in {"1", "true", "yes", "y", "on", "passed", "ok", "generated"}
    return bool(v)


def _i(v: Any) -> int:
    try:
        if v is None or v == "": return 0
        if isinstance(v, bool): return int(v)
        return int(float(v))
    except Exception:
        return 0


def _list(v: Any) -> list[Any]:
    if v is None:
        return []
    if isinstance(v, list):
        return list(v)
    if isinstance(v, (tuple, set)):
        return list(v)
    if isinstance(v, Iterable) and not isinstance(v, (str, bytes, bytearray, Mapping)):
        return list(v)
    return [v]


def _dedupe(vals: Any) -> list[str]:
    out, seen = [], set()
    for item in _list(vals):
        txt = _s(item)
        if txt and txt not in seen:
            seen.add(txt); out.append(txt)
    return out


def _has_forbidden_key(v: Any) -> bool:
    if isinstance(v, Mapping):
        for k, item in v.items():
            if str(k) in _FORBIDDEN_KEYS: return True
            if _has_forbidden_key(item): return True
    elif isinstance(v, (list, tuple, set)):
        return any(_has_forbidden_key(x) for x in v)
    return False


def _has_marker_value(v: Any) -> bool:
    if isinstance(v, Mapping): return any(_has_marker_value(x) for x in v.values())
    if isinstance(v, (list, tuple, set)): return any(_has_marker_value(x) for x in v)
    txt = _s(v)
    return bool(txt and any(marker in txt for marker in _FORBIDDEN_MARKERS))


def assert_runtime_surface_exit_criteria_meta_only(value: Mapping[str, Any], *, source: str = RUNTIME_SURFACE_EXIT_CRITERIA_SOURCE) -> None:
    data = _m(value)
    if _has_forbidden_key(data):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    if _has_marker_value(data):
        raise ValueError(f"{source} must not include forbidden public surface marker text")
    for flag in _CONTRACT_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def forbidden_runtime_surface_pattern_ids(comment_text: str | None) -> list[str]:
    text = str(comment_text or "")
    return [pid for pid, pat in _FORBIDDEN if pat.search(text)] if text else []


def _rt(record: Mapping[str, Any]) -> dict[str, Any]:
    return _m(record.get("runtime_surface"))


def _gate_eval(record: Mapping[str, Any]) -> bool:
    r = _rt(record)
    return _b(record.get("runtime_surface_pre_return_gate_evaluated")) or _b(r.get("runtime_surface_pre_return_gate_evaluated"))


def _gate_pass(record: Mapping[str, Any]) -> bool:
    r = _rt(record)
    return any(_b(x) for x in (record.get("runtime_surface_pre_return_gate_passed"), record.get("runtime_surface_pre_return_gate_final_passed"), r.get("runtime_surface_pre_return_gate_passed"), r.get("runtime_surface_pre_return_gate_final_passed")))


def _displayed(record: Mapping[str, Any]) -> bool:
    return _s(record.get("observation_status")) == "passed" and (_b(record.get("comment_text_present")) or _i(record.get("comment_text_length")) > 0)


def _low_info(record: Mapping[str, Any]) -> bool:
    r = _rt(record)
    return _s(record.get("coverage_scope")) == "low_information" or _b(record.get("low_information_specificity_used")) or _b(record.get("step6_low_information_specificity_ready")) or _b(r.get("low_information_specificity_used")) or _b(r.get("step6_low_information_specificity_ready"))


def _reasons(record: Mapping[str, Any]) -> list[str]:
    r = _rt(record); vals=[]
    for key in ("runtime_surface_pre_return_gate_rejection_reasons", "display_rejection_reasons", "rejection_reasons"):
        vals += _list(record.get(key)) + _list(r.get(key))
    return _dedupe(vals)


def _surface_major(record: Mapping[str, Any]) -> bool:
    r = _rt(record); reasons = _reasons(record)
    return any(_b(x) for x in (record.get("surface_template_major"), record.get("surface_template_major_blocked"), r.get("surface_template_major"), r.get("surface_template_major_blocked"))) or any(x in {"surface_template_major", "generic_center_phrase", "same_connector_run"} for x in reasons)


def _grammar_count(record: Mapping[str, Any]) -> int:
    r = _rt(record)
    return max(_i(record.get("surface_grammar_warning_count")), _i(record.get("grammar_warning_count")), _i(r.get("surface_grammar_warning_count")), _i(r.get("grammar_warning_count")))


def _malformed_count(record: Mapping[str, Any]) -> int:
    r = _rt(record)
    return max(_i(record.get("malformed_phrase_unit_blocked_count")), _i(record.get("malformed_phrase_unit_count")), _i(r.get("malformed_phrase_unit_blocked_count")), _i(r.get("malformed_phrase_unit_count")))


def _contract_flags(record: Mapping[str, Any]) -> list[str]:
    r = _rt(record)
    return _dedupe([flag for flag in _CONTRACT_FLAGS if _b(record.get(flag)) or _b(r.get(flag))])


def _surface_blocked(record: Mapping[str, Any]) -> bool:
    return _s(record.get("classification")) == "surface_quality_blocked" or (_gate_eval(record) and not _gate_pass(record)) or _surface_major(record) or _malformed_count(record) > 0


def _infer_kind(record: Mapping[str, Any]) -> str:
    if _surface_blocked(record) and not _displayed(record): return CASE_KIND_BROKEN_SURFACE
    if _low_info(record): return CASE_KIND_LOW_INFORMATION
    return CASE_KIND_NORMAL_INPUT


def _case_report(record: Mapping[str, Any], *, displayed_comment_text: str | None = None, case_kind: str | None = None, case_id: str = "") -> dict[str, Any]:
    rec = _m(record); kind = case_kind or _infer_kind(rec)
    if kind not in RUNTIME_SURFACE_EXIT_CRITERIA_CASE_KINDS: raise ValueError(f"unknown case_kind: {kind}")
    displayed = _displayed(rec); forbidden_ids = forbidden_runtime_surface_pattern_ids(displayed_comment_text)
    contract_flags = _contract_flags(rec); blockers: list[str] = []
    status = _s(rec.get("observation_status")); comment_present = _b(rec.get("comment_text_present")) or _i(rec.get("comment_text_length")) > 0
    if not _gate_eval(rec): blockers.append("runtime_surface_pre_return_gate_not_evaluated")
    if status == "passed" and not comment_present: blockers.append("passed_status_without_comment_text")
    if comment_present and status != "passed": blockers.append("comment_text_present_without_passed_status")
    if displayed and not _gate_pass(rec): blockers.append("displayed_without_runtime_surface_gate_pass")
    if displayed and _surface_major(rec): blockers.append("displayed_surface_template_major")
    if displayed and _grammar_count(rec) > 0: blockers.append("displayed_surface_grammar_warning")
    if displayed and _malformed_count(rec) > 0: blockers.append("displayed_malformed_phrase_unit_blocked_count")
    if displayed and forbidden_ids: blockers.append("displayed_forbidden_surface_pattern")
    if kind == CASE_KIND_NORMAL_INPUT and not displayed: blockers.append("normal_input_not_displayed")
    if kind == CASE_KIND_LOW_INFORMATION and displayed and _i(rec.get("safe_anchor_count")) > 0 and not _b(rec.get("uses_safe_anchor")): blockers.append("low_information_safe_anchor_not_used")
    if kind == CASE_KIND_BROKEN_SURFACE:
        if displayed: blockers.append("broken_surface_reached_public_display")
        if not _surface_blocked(rec): blockers.append("broken_surface_not_surface_quality_blocked")
    for flag in contract_flags: blockers.append(f"contract_flag_true:{flag}")
    blockers = _dedupe(blockers)
    report = {
        "version": RUNTIME_SURFACE_EXIT_CRITERIA_VERSION,
        "source": RUNTIME_SURFACE_EXIT_CRITERIA_SOURCE,
        "target_step": RUNTIME_SURFACE_EXIT_CRITERIA_STEP,
        "case_id": _s(case_id) or _s(rec.get("trace_id")) or _s(rec.get("emotion_log_id")),
        "case_kind": kind,
        "runtime_surface_step10_exit_criteria_ready": True,
        "step10_runtime_surface_exit_criteria_ready": True,
        "evaluated": True,
        "passed": not blockers,
        "exit_criteria_case_passed": not blockers,
        "outcome": "passed" if not blockers else "blocked",
        "blockers": blockers,
        "failure_reasons": blockers,
        "observation_status": status or "unavailable",
        "comment_text_present": bool(comment_present),
        "displayed": bool(displayed),
        "forbidden_surface_detected": bool(forbidden_ids),
        "forbidden_surface_pattern_ids": forbidden_ids,
        "runtime_surface_pre_return_gate_evaluated": _gate_eval(rec),
        "runtime_surface_pre_return_gate_passed": _gate_pass(rec),
        "runtime_surface_pre_return_gate_final_passed": _gate_pass(rec),
        "runtime_surface_pre_return_gate_rejection_reasons": _reasons(rec),
        "surface_template_major_for_displayed_text": bool(_surface_major(rec) if displayed else False),
        "surface_grammar_warning_count_for_displayed_text": _grammar_count(rec) if displayed else 0,
        "malformed_phrase_unit_blocked_count_for_displayed_text": _malformed_count(rec) if displayed else 0,
        "surface_quality_blocked": _surface_blocked(rec),
        "low_information_specificity_used": _low_info(rec),
        "safe_anchor_count": _i(rec.get("safe_anchor_count")) or _i(_rt(rec).get("safe_anchor_count")),
        "uses_safe_anchor": _b(rec.get("uses_safe_anchor")) or _b(_rt(rec).get("uses_safe_anchor")),
        "true_contract_flags": contract_flags,
        "rn_display_contract_preserved": not any(reason in blockers for reason in ("comment_text_present_without_passed_status", "passed_status_without_comment_text")),
        "rn_display_contract_unchanged": not contract_flags,
        "api_response_key_unchanged": not contract_flags,
        "db_schema_unchanged": not contract_flags,
        "public_contract_unchanged": not contract_flags,
        "raw_input_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "displayed_comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    assert_runtime_surface_exit_criteria_meta_only(report); return report


def build_runtime_surface_exit_criteria_summary(case_reports: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    reps = [_m(x) for x in case_reports if _m(x)]
    blockers: list[str] = []
    for rep in reps:
        blockers += _list(rep.get("blockers"))
        if not _b(rep.get("passed")): blockers.append("case_failed:" + (_s(rep.get("case_id")) or "unknown_case"))
    normal = any(rep.get("case_kind") == CASE_KIND_NORMAL_INPUT and _b(rep.get("displayed")) and _b(rep.get("passed")) for rep in reps)
    low = any(rep.get("case_kind") == CASE_KIND_LOW_INFORMATION and _b(rep.get("passed")) for rep in reps)
    broken = any(rep.get("case_kind") == CASE_KIND_BROKEN_SURFACE and not _b(rep.get("displayed")) and _b(rep.get("passed")) for rep in reps)
    public_contract = bool(reps) and all(_b(rep.get("public_contract_unchanged")) for rep in reps)
    if not normal: blockers.append("normal_input_display_not_confirmed")
    if not low: blockers.append("low_information_branch_not_confirmed")
    if not broken: blockers.append("broken_surface_block_not_confirmed")
    if not public_contract: blockers.append("public_contract_not_confirmed_unchanged")
    blockers = _dedupe(blockers)
    summary = {
        "version": RUNTIME_SURFACE_EXIT_CRITERIA_VERSION,
        "source": RUNTIME_SURFACE_EXIT_CRITERIA_SOURCE,
        "target_step": RUNTIME_SURFACE_EXIT_CRITERIA_STEP,
        "runtime_surface_step10_exit_criteria_ready": True,
        "step10_runtime_surface_exit_criteria_ready": True,
        "evaluated": True,
        "passed": not blockers,
        "exit_criteria_passed": not blockers,
        "outcome": "passed" if not blockers else "blocked",
        "case_count": len(reps),
        "record_count": len(reps),
        "required_checks": list(REQUIRED_EXIT_CRITERIA_CHECKS),
        "normal_input_display_confirmed": normal,
        "low_information_branch_confirmed": low,
        "broken_surface_blocked_confirmed": broken,
        "public_contract_unchanged": public_contract,
        "rn_display_contract_unchanged": public_contract,
        "api_response_key_unchanged": public_contract,
        "db_schema_unchanged": public_contract,
        "checks": {"normal_input_display_confirmed": normal, "low_information_branch_confirmed": low, "broken_surface_blocked_confirmed": broken, "public_contract_unchanged": public_contract},
        "blockers": blockers,
        "exit_criteria_blockers": blockers,
        "failure_reasons": blockers,
        "raw_input_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "displayed_comment_text_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
        "step10_real_device_check_required": True,
        "step10_real_device_check_executed_by_code": False,
    }
    assert_runtime_surface_exit_criteria_meta_only(summary); return summary


def build_runtime_surface_exit_criteria_report(records: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None, *, diagnostic_record: Mapping[str, Any] | None = None, run_id: str = "", displayed_comment_text: str | None = None, case_kind: str | None = None) -> dict[str, Any]:
    if diagnostic_record is not None:
        return _case_report(diagnostic_record, displayed_comment_text=displayed_comment_text, case_kind=case_kind, case_id=run_id)
    if isinstance(records, Mapping):
        return _case_report(records, displayed_comment_text=displayed_comment_text, case_kind=case_kind, case_id=run_id)
    rows = [_m(x) for x in _list(records) if _m(x)]
    cases = [_case_report(row, displayed_comment_text=displayed_comment_text if _displayed(row) else None, case_kind=case_kind or _infer_kind(row), case_id=_s(row.get("trace_id")) or _s(row.get("emotion_log_id")) or f"{run_id}:{idx}") for idx, row in enumerate(rows)]
    summary = build_runtime_surface_exit_criteria_summary(cases); summary["run_id"] = _s(run_id)
    summary["normal_input_displayed_count"] = sum(1 for c in cases if c.get("case_kind") == CASE_KIND_NORMAL_INPUT and _b(c.get("displayed")))
    summary["low_information_record_count"] = sum(1 for c in cases if c.get("case_kind") == CASE_KIND_LOW_INFORMATION)
    summary["broken_surface_blocked_count"] = sum(1 for c in cases if c.get("case_kind") == CASE_KIND_BROKEN_SURFACE and not _b(c.get("displayed")))
    summary["displayed_surface_clean_count"] = sum(1 for c in cases if _b(c.get("displayed")) and _b(c.get("passed")))
    return summary


def extract_observation_diagnostic_lockdown_records_from_log_lines(log_lines: Sequence[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in log_lines:
        text = str(line or "")
        if "emlis_observation_diagnostic_lockdown" not in text: continue
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start: continue
        try: obj = json.loads(text[start:end+1])
        except json.JSONDecodeError: continue
        if isinstance(obj, Mapping): rows.append(dict(obj))
    return rows


def build_runtime_surface_exit_criteria_report_from_log_lines(*, log_lines: Sequence[str], displayed_comment_text_by_trace_id: Mapping[str, str] | None = None, run_id: str = "") -> dict[str, Any]:
    rows = extract_observation_diagnostic_lockdown_records_from_log_lines(log_lines)
    text_by_trace = _m(displayed_comment_text_by_trace_id)
    cases = []
    for idx, row in enumerate(rows):
        tid = _s(row.get("trace_id")) or _s(row.get("emotion_log_id"))
        cases.append(_case_report(row, displayed_comment_text=_s(text_by_trace.get(tid)) or None, case_kind=_infer_kind(row), case_id=tid or f"{run_id}:{idx}"))
    summary = build_runtime_surface_exit_criteria_summary(cases); summary["run_id"] = _s(run_id); summary["record_count"] = len(rows)
    return summary


def dump_runtime_surface_exit_criteria_report(report: Mapping[str, Any]) -> str:
    data = dict(report or {}); data["raw_input_included"] = False; data["comment_text_included"] = False; data["comment_text_body_included"] = False; data["displayed_comment_text_included"] = False; data["public_release_applied"] = False; data["product_gate_achieved"] = False
    assert_runtime_surface_exit_criteria_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_runtime_surface_exit_criteria_passed(report: Mapping[str, Any]) -> None:
    if not _b(_m(report).get("passed")):
        raise RuntimeSurfaceExitCriteriaError("EmlisAI runtime surface exit criteria failed: " + ", ".join(_dedupe(_m(report).get("blockers") or _m(report).get("failure_reasons"))))

__all__ = [
    "CASE_KIND_BROKEN_SURFACE", "CASE_KIND_LOW_INFORMATION", "CASE_KIND_NORMAL_INPUT",
    "OUTCOME_FAILED", "OUTCOME_NON_DISPLAY", "OUTCOME_PASSED_DISPLAYED", "OUTCOME_SURFACE_BLOCKED",
    "REQUIRED_EXIT_CRITERIA_CHECKS", "RUNTIME_SURFACE_EXIT_CRITERIA_CASE_KINDS",
    "RUNTIME_SURFACE_EXIT_CRITERIA_SOURCE", "RUNTIME_SURFACE_EXIT_CRITERIA_STEP",
    "RUNTIME_SURFACE_EXIT_CRITERIA_VERSION", "RuntimeSurfaceExitCriteriaError",
    "assert_runtime_surface_exit_criteria_meta_only", "assert_runtime_surface_exit_criteria_passed",
    "build_runtime_surface_exit_criteria_report", "build_runtime_surface_exit_criteria_report_from_log_lines",
    "build_runtime_surface_exit_criteria_summary", "dump_runtime_surface_exit_criteria_report",
    "extract_observation_diagnostic_lockdown_records_from_log_lines", "forbidden_runtime_surface_pattern_ids",
]
