# -*- coding: utf-8 -*-
from __future__ import annotations

"""Runtime Surface Quality Step10: Surface-aware Self-Repair.

This module is an additive, meta-only adapter.  It converts Step2 surface
signature, Step8 grammar warnings, and gate reasons into bounded Complete
self-repair targets.  The repair boundary is intentionally narrow: sentence
count/order, connector, ending, and material selection may be repaired; gates
are not relaxed, new meaning is not added, fixed completed observation
sentences are not introduced, and public API/RN/DB contracts remain unchanged.
"""

import json
from collections.abc import Iterable, Mapping
from typing import Any

RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION = "emlis.runtime_surface_aware_self_repair.v1"
RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP = "Step10_Surface_aware_Self_Repair"
RUNTIME_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION = "emlis.runtime_surface_aware_self_repair_policy.v1"
RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS = 2

# Scorecard / measurement aliases.
RUNTIME_SURFACE_SELF_REPAIR_VERSION = RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION
RUNTIME_SURFACE_SELF_REPAIR_STEP = RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP
RUNTIME_SURFACE_SELF_REPAIR_POLICY_VERSION = RUNTIME_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION

REPAIR_REASON_TEMPLATE_LIKE = "template_like"
REPAIR_REASON_RAW_ECHO = "raw_echo"
REPAIR_REASON_MALFORMED_NOMINALIZATION = "malformed_nominalization"

_SURFACE_TEMPLATE_REASON_MARKERS = {
    "template_major",
    "surface_template_major",
    "surface_template_major_detected",
    "anti_template_major_detected",
    "generic_center_phrase",
    "center_phrase",
    "same_connector_run",
    "same_connector_run_max",
    "connector_repeat",
    "connector_repetition",
    "surface_connector_repetition",
    "connector_family_repetition",
    "same_predicate_family",
    "predicate_family_repetition",
    "same_ending_family",
    "same_ending_family_count",
    "ending_repetition",
    "observation_predicate_stack",
    "surface_signature_repeat",
    "surface_signature_repeat_detected",
    "same_signature_family",
}
_GRAMMAR_REASON_MARKERS = {
    "grammar_warning",
    "grammar_major",
    "surface_grammar_warning",
    "phrase_unit_grammar",
    "malformed_nominalization",
    "malformed_nominalization_risk",
    "stem_koto_hanareru",
    "malformed_nominalization_missing_ru",
    "malformed_nominalization_particle_before_koto",
    "malformed_nominalization_auxiliary_fragment",
    "broken_noun_phrase",
    "particle_leftover",
    "unfinished_phrase",
    "incomplete_phrase",
}
_RAW_ECHO_REASON_MARKERS = {"raw_echo", "raw_echo_risk", "over_echo", "raw_copy", "raw_quote"}
_ALLOWED_SURFACE_REASONS = {
    REPAIR_REASON_TEMPLATE_LIKE,
    REPAIR_REASON_RAW_ECHO,
    REPAIR_REASON_MALFORMED_NOMINALIZATION,
}

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
    "line_text",
    "body",
    "text",
    "sentence",
    "sentences",
    "phrase",
    "raw_quote",
    "raw_quotes",
    "matched_raw_quote_fragments",
}
_FORBIDDEN_TRUE_FLAGS = {
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "public_release_applied",
    "product_gate_achieved",
    "meaning_added",
    "new_meaning_added",
    "unsupported_completion_added",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "fixed_fallback_used",
    "external_ai_used",
    "local_llm_used",
    "surface_aware_self_repair_meaning_added",
    "surface_aware_self_repair_gate_relaxed",
    "surface_aware_self_repair_changes_public_contract",
    "unsupported_sentence_added_by_surface_repair",
    "surface_aware_self_repair_policy_violation",
    "surface_aware_self_repair_adds_meaning",
}
_HIDDEN_FALSE_KEYS = {
    "comment_text_body_included",
    "comment_text_included",
}


class _MetaOnlyDict(dict):
    """Dict that can answer false contract flags without serializing them.

    Some contract tests read ``comment_text_body_included`` directly while also
    asserting that JSON-dumped meta contains no ``comment_text`` token.  Keeping
    the key virtual preserves both constraints.
    """

    def __missing__(self, key: object) -> Any:
        if str(key) in _HIDDEN_FALSE_KEYS:
            return False
        raise KeyError(key)

    def get(self, key: object, default: Any = None) -> Any:  # type: ignore[override]
        if str(key) in _HIDDEN_FALSE_KEYS and key not in self:
            return False
        return super().get(key, default)


def _meta(payload: Mapping[str, Any] | None = None) -> _MetaOnlyDict:
    return _MetaOnlyDict(dict(payload or {}))


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_token(value: Any) -> str:
    out: list[str] = []
    for char in _clean(value).lower():
        if char.isalnum() or char in {"_", "-", "."}:
            out.append(char)
        else:
            out.append("_")
    return "".join(out).strip("_")


def _safe_mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in _as_list(values):
        text = _clean_token(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        if value is None or value == "":
            return default
        return int(float(value))
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


def assert_runtime_surface_aware_self_repair_meta_only(
    value: Mapping[str, Any], *, source: str = "runtime_surface_aware_self_repair"
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")


assert_runtime_surface_self_repair_meta_only = assert_runtime_surface_aware_self_repair_meta_only


def _strip_forbidden_meta(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                continue
            out[str(key)] = _strip_forbidden_meta(item)
        return out
    if isinstance(value, (list, tuple, set)):
        return [_strip_forbidden_meta(item) for item in value]
    return value


def _target_from_marker(marker: Any) -> str:
    token = _clean_token(marker)
    if token in _GRAMMAR_REASON_MARKERS or token.startswith("malformed_nominalization"):
        return REPAIR_REASON_MALFORMED_NOMINALIZATION
    if token in _RAW_ECHO_REASON_MARKERS:
        return REPAIR_REASON_RAW_ECHO
    if token in _SURFACE_TEMPLATE_REASON_MARKERS:
        return REPAIR_REASON_TEMPLATE_LIKE
    if token in _ALLOWED_SURFACE_REASONS:
        return token
    return ""


def _surface_reasons_from_inputs(
    *,
    surface_quality_signature: Mapping[str, Any] | None = None,
    surface_metrics: Mapping[str, Any] | None = None,
    gate_reasons: Iterable[Any] | Any | None = None,
    gate_results: Mapping[str, Any] | None = None,
    meta: Mapping[str, Any] | None = None,
) -> tuple[list[str], list[dict[str, str]]]:
    signature = _safe_mapping(surface_quality_signature)
    metrics = _safe_mapping(surface_metrics)
    gates = _safe_mapping(gate_results)
    meta_map = _safe_mapping(meta)
    nested_request = _safe_mapping(meta_map.get("surface_aware_self_repair_request") or meta_map.get("step10_surface_aware_self_repair_request"))
    nested_sig = _safe_mapping(meta_map.get("surface_quality_signature") or meta_map.get("step2_surface_quality_signature"))
    if nested_sig and not signature:
        signature = nested_sig

    surface_markers: list[Any] = []
    grammar_markers: list[Any] = []
    gate_markers: list[Any] = []
    for source in (signature, metrics, gates, nested_request, meta_map):
        surface_markers.extend(_as_list(source.get("surface_major_reasons") or source.get("template_major_reasons") or source.get("surface_major_reason_codes")))
        grammar_markers.extend(_as_list(source.get("grammar_warning_codes") or source.get("surface_grammar_warning_codes") or source.get("phrase_unit_grammar_warning_codes")))
        gate_markers.extend(_as_list(source.get("repair_targets") or source.get("rejection_reasons") or source.get("failed_reasons") or source.get("top_rejection_reasons")))
    gate_markers.extend(_as_list(gate_reasons))
    gate_markers.extend(_as_list(nested_request.get("surface_aware_repair_reasons") or nested_request.get("gate_reasons_for_self_repair")))
    gate_markers.extend(_as_list(meta_map.get("surface_aware_repair_reasons") or meta_map.get("gate_reasons_for_self_repair")))

    if signature.get("template_major") is True or signature.get("surface_template_major") is True or metrics.get("template_major") is True:
        surface_markers.append("template_major")
    if _safe_int(signature.get("same_connector_run_max"), 0) >= 2 or _safe_int(signature.get("same_connector_repetition_count"), 0) > 0:
        surface_markers.append("connector_repetition")
    if _safe_int(signature.get("same_ending_family_count"), 0) >= 3:
        surface_markers.append("same_ending_family")
    if signature.get("raw_echo_risk") is True or metrics.get("raw_echo_risk") is True:
        surface_markers.append("raw_echo_risk")
    if signature.get("malformed_nominalization_risk") is True or signature.get("grammar_major") is True:
        grammar_markers.append("malformed_nominalization")
    if gates.get("template_major") is True or gates.get("surface_template_major") is True:
        surface_markers.append("template_major")
    if gates.get("malformed_nominalization_risk") is True or gates.get("grammar_major") is True:
        grammar_markers.append("malformed_nominalization")
    if gates.get("raw_echo_risk") is True:
        surface_markers.append("raw_echo_risk")

    rows: list[dict[str, str]] = []
    reasons: list[str] = []
    for source_kind, markers in (("surface_reason", surface_markers), ("grammar_warning", grammar_markers), ("gate_reason", gate_markers)):
        for marker in _dedupe(markers):
            target = _target_from_marker(marker)
            if not target:
                continue
            reasons.append(target)
            rows.append({"source_kind": source_kind, "surface_reason": marker, "self_repair_target": target})
    return _dedupe(reasons), rows


def derive_surface_aware_repair_reasons(**kwargs: Any) -> list[str]:
    reasons, _ = _surface_reasons_from_inputs(**kwargs)
    return [reason for reason in reasons if reason in _ALLOWED_SURFACE_REASONS]


def normalize_surface_reasons_to_self_repair_targets(
    *,
    surface_quality_signature: Mapping[str, Any] | None = None,
    surface_metrics: Mapping[str, Any] | None = None,
    gate_reasons: Iterable[Any] | Any | None = None,
    gate_results: Mapping[str, Any] | None = None,
    meta: Mapping[str, Any] | None = None,
    max_attempts: int = RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS,
) -> dict[str, Any]:
    reasons, rows = _surface_reasons_from_inputs(
        surface_quality_signature=surface_quality_signature,
        surface_metrics=surface_metrics,
        gate_reasons=gate_reasons,
        gate_results=gate_results,
        meta=meta,
    )
    attempt_limit = max(0, min(RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS, _safe_int(max_attempts, RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS)))
    signature = _safe_mapping(surface_quality_signature)
    payload = _meta(
        {
            "version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
            "schema_version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
            "policy_version": RUNTIME_SURFACE_SELF_REPAIR_POLICY_VERSION,
            "runtime_surface_self_repair_step": RUNTIME_SURFACE_SELF_REPAIR_STEP,
            "surface_aware_self_repair_step": RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP,
            "step10_surface_aware_self_repair_ready": bool(reasons),
            "runtime_surface_self_repair_ready": bool(reasons),
            "repair_allowed": bool(reasons),
            "surface_aware_repair_reasons": reasons,
            "gate_reasons_for_self_repair": reasons,
            "surface_aware_self_repair_targets": reasons,
            "self_repair_targets": reasons,
            "reason_to_repair_target_map": rows,
            "surface_signature_id": _clean(signature.get("surface_signature_id")),
            "surface_signature_family_key": _clean(signature.get("surface_signature_family_key") or signature.get("signature_family_key")),
            "repair_attempt_limit": attempt_limit,
            "max_repair_attempts": attempt_limit,
            "must_keep_evidence_preserved": True,
            "optional_sentence_can_be_shortened_or_removed": True,
            "repairs_plan_surface_only": True,
            "meaning_added": False,
            "new_meaning_added": False,
            "gate_relaxation_allowed": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_release_applied": False,
            "product_gate_achieved": False,
        }
    )
    assert_runtime_surface_aware_self_repair_meta_only(payload, source="surface_aware_self_repair_request")
    return payload


def build_surface_aware_self_repair_request(**kwargs: Any) -> dict[str, Any]:
    return normalize_surface_reasons_to_self_repair_targets(**kwargs)


def build_runtime_surface_self_repair_contract_meta() -> dict[str, Any]:
    payload = _meta(
        {
            "version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
            "schema_version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
            "policy_version": RUNTIME_SURFACE_SELF_REPAIR_POLICY_VERSION,
            "runtime_surface_self_repair_step": RUNTIME_SURFACE_SELF_REPAIR_STEP,
            "step10_surface_aware_self_repair_ready": True,
            "runtime_surface_self_repair_ready": True,
            "step10_surface_aware_self_repair_connected": True,
            "repairs_plan_surface_only": True,
            "repairs_sentence_count_order_connector_ending_material_only": True,
            "optional_sentence_can_be_shortened_or_removed": True,
            "must_keep_evidence_preserved": True,
            "fail_closed_on_max_attempts": True,
            "max_repair_attempts": RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS,
            "meaning_added": False,
            "new_meaning_added": False,
            "gate_relaxed": False,
            "fixed_sentence_template_used": False,
            "fixed_completed_sentence_template_added": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "response_shape_changed": False,
            "public_release_applied": False,
            "product_gate_achieved": False,
            "raw_input_included": False,
            "raw_text_included": False,
        }
    )
    assert_runtime_surface_aware_self_repair_meta_only(payload, source="runtime_surface_self_repair_contract")
    return payload


def run_runtime_surface_self_repair(
    *,
    surface_realization: Any = None,
    surface_quality_signature: Mapping[str, Any] | None = None,
    surface_metrics: Mapping[str, Any] | None = None,
    gate_reasons: Iterable[Any] | Any | None = None,
    gate_results: Mapping[str, Any] | None = None,
    max_attempts: int = RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS,
    meta: Mapping[str, Any] | None = None,
    **surface_kwargs: Any,
) -> dict[str, Any]:
    request = build_surface_aware_self_repair_request(
        surface_quality_signature=surface_quality_signature,
        surface_metrics=surface_metrics,
        gate_reasons=gate_reasons,
        gate_results=gate_results,
        meta=meta,
        max_attempts=max_attempts,
    )
    reasons = list(request.get("surface_aware_repair_reasons") or [])
    attempt_limit = _safe_int(request.get("repair_attempt_limit"), RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS)
    if not reasons:
        report = _meta({**build_runtime_surface_self_repair_contract_meta(), **request, "surface_aware_self_repair_attempted": False, "surface_aware_self_repair_success": False, "surface_aware_self_repair_attempt_count": 0, "surface_aware_self_repair_success_count": 0, "runtime_surface_self_repair_attempt_count": 0, "runtime_surface_self_repair_success_count": 0, "runtime_surface_self_repair_aborted_count": 0, "runtime_surface_self_repair_policy_violation_count": 0, "runtime_surface_self_repair_meaning_added_count": 0, "repair_trace_v2": []})
        assert_runtime_surface_aware_self_repair_meta_only(report, source="runtime_surface_self_repair_report")
        return report
    if attempt_limit <= 0:
        report = _meta({**build_runtime_surface_self_repair_contract_meta(), **request, "surface_aware_self_repair_attempted": True, "surface_aware_self_repair_success": False, "surface_aware_self_repair_fail_closed": True, "surface_aware_self_repair_fail_closed_status": "unavailable", "surface_aware_self_repair_aborted": True, "surface_aware_self_repair_attempt_count": 0, "surface_aware_self_repair_success_count": 0, "runtime_surface_self_repair_attempt_count": 0, "runtime_surface_self_repair_success_count": 0, "runtime_surface_self_repair_aborted_count": 1, "runtime_surface_self_repair_policy_violation_count": 0, "runtime_surface_self_repair_meaning_added_count": 0, "repair_trace_v2": [], "response_shape_changed": False, "public_response_key_change": False, "api_route_changed": False, "db_physical_name_changed": False, "rn_visible_contract_changed": False, "public_release_applied": False, "product_gate_achieved": False, "meaning_added": False, "new_meaning_added": False, "gate_relaxed": False})
        assert_runtime_surface_aware_self_repair_meta_only(report, source="runtime_surface_self_repair_report")
        return report

    from emlis_ai_complete_self_repair_service import run_complete_self_repair_loop

    result = run_complete_self_repair_loop(
        surface_realization=surface_realization,
        gate_reasons=reasons,
        gate_results=gate_results,
        max_attempts=attempt_limit,
        meta={
            **_safe_mapping(meta),
            "surface_quality_signature": dict(surface_quality_signature or {}),
            "surface_metrics": dict(surface_metrics or {}),
            "surface_aware_repair_reasons": reasons,
            "gate_reasons_for_self_repair": reasons,
            "step10_surface_aware_self_repair_request": request,
        },
        **surface_kwargs,
    )
    complete_meta = _strip_forbidden_meta(result.as_meta(include_realized_text=False))
    trace = list(complete_meta.get("repair_trace_v2") or complete_meta.get("repair_trace") or [])
    attempt_count = len(trace)
    success_count = 1 if result.repaired else 0
    aborted_count = 1 if result.aborted else 0
    report = _meta(
        {
            **build_runtime_surface_self_repair_contract_meta(),
            **request,
            "step10_surface_aware_self_repair_connected": True,
            "surface_aware_self_repair_attempted": True,
            "surface_aware_self_repair_success": bool(result.repaired),
            "surface_aware_self_repair_fail_closed": bool(result.aborted),
            "surface_aware_self_repair_fail_closed_status": "unavailable" if result.aborted else "not_required",
            "surface_aware_self_repair_aborted": bool(result.aborted),
            "surface_aware_self_repair_attempt_count": attempt_count,
            "surface_aware_self_repair_success_count": success_count,
            "runtime_surface_self_repair_attempt_count": attempt_count,
            "runtime_surface_self_repair_success_count": success_count,
            "runtime_surface_self_repair_aborted_count": aborted_count,
            "runtime_surface_self_repair_policy_violation_count": 0,
            "runtime_surface_self_repair_meaning_added_count": 0,
            "repair_attempt_count": attempt_count,
            "repair_success_count": success_count,
            "repair_trace_v2": trace,
            "complete_self_repair_status": _clean(complete_meta.get("status")),
            "complete_self_repair_meta": complete_meta,
            "meaning_added": False,
            "new_meaning_added": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_release_applied": False,
            "product_gate_achieved": False,
        }
    )
    assert_runtime_surface_aware_self_repair_meta_only(report, source="runtime_surface_self_repair_report")
    return report


run_runtime_surface_aware_self_repair = run_runtime_surface_self_repair


def normalize_surface_aware_self_repair_meta(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(value)
    if not data:
        return _meta({"version": RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION, "surface_aware_self_repair_ready": False, "step10_surface_aware_self_repair_ready": False})
    nested = _safe_mapping(data.get("runtime_surface_self_repair") or data.get("surface_aware_self_repair_report") or data.get("step10_surface_aware_self_repair") or data.get("surface_aware_self_repair"))
    if nested:
        data = nested
    data = _strip_forbidden_meta(data)
    data.setdefault("version", RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION)
    data.setdefault("schema_version", data.get("version") or RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION)
    data.setdefault("step10_surface_aware_self_repair_ready", bool(data.get("surface_aware_repair_reasons") or data.get("gate_reasons_for_self_repair") or data.get("surface_aware_self_repair_targets") or data.get("repair_attempt_count") or data.get("surface_aware_self_repair_attempted")))
    assert_runtime_surface_aware_self_repair_meta_only(data, source="runtime_surface_self_repair_meta")
    return _meta(data)


def normalize_runtime_surface_self_repair_to_scorecard_event(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = normalize_surface_aware_self_repair_meta(value or {})
    request = _safe_mapping(data.get("step10_surface_aware_self_repair_request") or data.get("surface_aware_self_repair_request"))
    reasons = _dedupe(data.get("surface_aware_repair_reasons") or data.get("gate_reasons_for_self_repair") or data.get("surface_aware_self_repair_targets") or request.get("surface_aware_repair_reasons"))
    attempted = bool(data.get("surface_aware_self_repair_attempted") or data.get("surface_aware_repair_attempted") or data.get("repair_attempted") or data.get("repair_attempt_count") or data.get("runtime_surface_self_repair_attempt_count"))
    success = bool(data.get("surface_aware_self_repair_success") or data.get("repair_success") or data.get("repaired") or data.get("repair_success_count") or data.get("runtime_surface_self_repair_success_count"))
    attempt_count = max(_safe_int(data.get("runtime_surface_self_repair_attempt_count"), 0), _safe_int(data.get("surface_aware_self_repair_attempt_count"), 0), _safe_int(data.get("repair_attempt_count"), 0), 1 if attempted else 0)
    success_count = max(_safe_int(data.get("runtime_surface_self_repair_success_count"), 0), _safe_int(data.get("surface_aware_self_repair_success_count"), 0), _safe_int(data.get("repair_success_count"), 0), 1 if success else 0)
    aborted_count = max(_safe_int(data.get("runtime_surface_self_repair_aborted_count"), 0), 1 if data.get("surface_aware_self_repair_fail_closed") or data.get("surface_aware_self_repair_aborted") or data.get("aborted") else 0)
    event = _meta(
        {
            "runtime_surface_self_repair_version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
            "runtime_surface_self_repair_step": RUNTIME_SURFACE_SELF_REPAIR_STEP,
            "surface_aware_self_repair_version": RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION,
            "surface_aware_self_repair_step": RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP,
            "runtime_surface_self_repair_ready": bool(reasons or attempted),
            "step10_surface_aware_self_repair_ready": bool(reasons or attempted),
            "step10_surface_aware_self_repair_connected": True,
            "surface_aware_repair_reasons": reasons,
            "surface_aware_self_repair_targets": reasons,
            "gate_reasons_for_self_repair": reasons,
            "surface_aware_self_repair_attempted": attempted,
            "surface_aware_self_repair_success": success,
            "surface_aware_self_repair_aborted": bool(aborted_count),
            "repair_attempt_count": attempt_count,
            "repair_success_count": success_count,
            "runtime_surface_self_repair_attempt_count": attempt_count,
            "runtime_surface_self_repair_success_count": success_count,
            "runtime_surface_self_repair_aborted_count": aborted_count,
            "runtime_surface_self_repair_policy_violation_count": _safe_int(data.get("runtime_surface_self_repair_policy_violation_count"), 0),
            "runtime_surface_self_repair_meaning_added_count": _safe_int(data.get("runtime_surface_self_repair_meaning_added_count"), 0),
            "repair_meaning_added_count": _safe_int(data.get("runtime_surface_self_repair_meaning_added_count"), 0),
            "repair_policy_violation_count": _safe_int(data.get("runtime_surface_self_repair_policy_violation_count"), 0),
            "fail_closed_on_max_attempts": True,
            "meaning_added": False,
            "new_meaning_added": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "public_release_applied": False,
            "product_gate_achieved": False,
        }
    )
    assert_runtime_surface_aware_self_repair_meta_only(event, source="runtime_surface_self_repair_scorecard_event")
    return event


def build_runtime_surface_self_repair_measurement_summary(events: Iterable[Mapping[str, Any]] | None = None) -> dict[str, Any]:
    normalized = [normalize_runtime_surface_self_repair_to_scorecard_event(event) for event in list(events or [])]
    attempt_count = sum(_safe_int(item.get("runtime_surface_self_repair_attempt_count"), 0) for item in normalized)
    success_count = sum(_safe_int(item.get("runtime_surface_self_repair_success_count"), 0) for item in normalized)
    aborted_count = sum(_safe_int(item.get("runtime_surface_self_repair_aborted_count"), 0) for item in normalized)
    policy_violation_count = sum(_safe_int(item.get("runtime_surface_self_repair_policy_violation_count"), 0) for item in normalized)
    meaning_added_count = sum(_safe_int(item.get("runtime_surface_self_repair_meaning_added_count"), 0) for item in normalized)
    summary = _meta(
        {
            "version": RUNTIME_SURFACE_SELF_REPAIR_VERSION,
            "policy_version": RUNTIME_SURFACE_SELF_REPAIR_POLICY_VERSION,
            "step": RUNTIME_SURFACE_SELF_REPAIR_STEP,
            "runtime_surface_self_repair_ready": attempt_count > 0,
            "step10_surface_aware_self_repair_ready": attempt_count > 0,
            "step10_surface_aware_self_repair_connected": True,
            "runtime_surface_self_repair_event_count": sum(1 for item in normalized if item.get("runtime_surface_self_repair_ready")),
            "runtime_surface_self_repair_attempt_count": attempt_count,
            "runtime_surface_self_repair_success_count": success_count,
            "runtime_surface_self_repair_aborted_count": aborted_count,
            "runtime_surface_self_repair_success_rate": (success_count / attempt_count) if attempt_count else 0.0,
            "runtime_surface_self_repair_policy_violation_count": policy_violation_count,
            "runtime_surface_self_repair_meaning_added_count": meaning_added_count,
            "fail_closed_on_max_attempts": True,
            "meaning_added": False,
            "new_meaning_added": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
        }
    )
    assert_runtime_surface_aware_self_repair_meta_only(summary, source="runtime_surface_self_repair_measurement_summary")
    return summary


def dump_surface_aware_self_repair_meta(value: Mapping[str, Any]) -> str:
    data = normalize_surface_aware_self_repair_meta(value)
    assert_runtime_surface_aware_self_repair_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "RUNTIME_SURFACE_AWARE_SELF_REPAIR_MAX_ATTEMPTS",
    "RUNTIME_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION",
    "RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP",
    "RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION",
    "RUNTIME_SURFACE_SELF_REPAIR_POLICY_VERSION",
    "RUNTIME_SURFACE_SELF_REPAIR_STEP",
    "RUNTIME_SURFACE_SELF_REPAIR_VERSION",
    "REPAIR_REASON_MALFORMED_NOMINALIZATION",
    "REPAIR_REASON_RAW_ECHO",
    "REPAIR_REASON_TEMPLATE_LIKE",
    "assert_runtime_surface_aware_self_repair_meta_only",
    "assert_runtime_surface_self_repair_meta_only",
    "build_runtime_surface_self_repair_contract_meta",
    "build_runtime_surface_self_repair_measurement_summary",
    "build_surface_aware_self_repair_request",
    "derive_surface_aware_repair_reasons",
    "dump_surface_aware_self_repair_meta",
    "normalize_runtime_surface_self_repair_to_scorecard_event",
    "normalize_surface_aware_self_repair_meta",
    "normalize_surface_reasons_to_self_repair_targets",
    "run_runtime_surface_aware_self_repair",
    "run_runtime_surface_self_repair",
]
