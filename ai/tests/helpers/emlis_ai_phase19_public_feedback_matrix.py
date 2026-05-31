# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase19 test-only public-feedback recovery matrix for EmlisAI.

Phase20-0 keeps this helper quarantined as regression/test material.  The
real-device ABCD fixtures are not implementation targets and their example
wording must not become runtime cues.  This helper only summarizes where a
fixture reaches or misses the public ``input_feedback`` contract without adding
public response keys, carrying raw user input, or exposing candidate/comment
bodies.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final

PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase19.public_feedback_recovery_matrix.v1"
)
PHASE19_PUBLIC_FEEDBACK_MATRIX_SOURCE_PHASE: Final = "Phase19-1_public_feedback_recovery_matrix"
PHASE19_PUBLIC_FEEDBACK_MATRIX_ID: Final = "emlis_phase19_real_device_abcd_public_feedback_recovery"
PHASE19_PUBLIC_FEEDBACK_RN_MODAL_TITLE: Final = "Emlisの観測"

VISIBLE_SURFACE_GATE_PASSED: Final = "passed"
VISIBLE_SURFACE_GATE_FAILED: Final = "failed"
VISIBLE_SURFACE_GATE_NOT_REACHED: Final = "not_reached"
VISIBLE_SURFACE_GATE_UNKNOWN: Final = "unknown"

_ALLOWED_VISIBLE_SURFACE_GATE_STATUSES: Final = frozenset(
    {
        VISIBLE_SURFACE_GATE_PASSED,
        VISIBLE_SURFACE_GATE_FAILED,
        VISIBLE_SURFACE_GATE_NOT_REACHED,
        VISIBLE_SURFACE_GATE_UNKNOWN,
    }
)

_REQUIRED_TOP_LEVEL_KEYS: Final = frozenset(
    {
        "schema_version",
        "source_phase",
        "matrix_id",
        "case_id",
        "expected_public_feedback",
        "current_input",
        "safety",
        "candidate",
        "surface_gate",
        "public_feedback",
        "rn_contract",
    }
)
_REQUIRED_CURRENT_INPUT_KEYS: Final = frozenset(
    {
        "memo_present",
        "memo_action_present",
        "emotions_present",
        "categories_present",
        "memo_text_len",
        "memo_action_text_len",
    }
)
_REQUIRED_SAFETY_KEYS: Final = frozenset({"safety_blocked", "safety_reason"})
_REQUIRED_CANDIDATE_KEYS: Final = frozenset(
    {
        "generation_attempted",
        "generated_before_display_gate",
        "source",
        "first_failure_reason",
    }
)
_REQUIRED_SURFACE_GATE_KEYS: Final = frozenset(
    {
        "visible_surface_acceptance_gate",
        "rejection_reasons",
    }
)
_REQUIRED_PUBLIC_FEEDBACK_KEYS: Final = frozenset(
    {
        "comment_text_present",
        "public_observation_status",
        "input_feedback_included",
        "first_backend_blocker",
    }
)
_REQUIRED_RN_CONTRACT_KEYS: Final = frozenset({"modal_should_open", "modal_title"})

_FORBIDDEN_EXACT_KEYS: Final = frozenset(
    {
        "raw_input",
        "raw_text",
        "input_text",
        "memo",
        "memo_action",
        "comment_text",
        "observation_text",
        "reception_text",
        "generated_text",
        "generated_candidate_text",
        "candidate_text",
        "candidate_comment_text",
        "surface_policy",
        "evidence_spans",
        "current_input_text",
        "body",
        "text",
    }
)


def build_phase19_public_feedback_recovery_matrix(
    *,
    case_id: str,
    expected_public_feedback: bool,
    current_input: Mapping[str, Any] | None,
    public_meta: Mapping[str, Any] | None,
    diagnostic_meta: Mapping[str, Any] | None = None,
    reply_comment_text: Any = None,
    response_body: Mapping[str, Any] | None = None,
    source_phase: str = PHASE19_PUBLIC_FEEDBACK_MATRIX_SOURCE_PHASE,
) -> dict[str, Any]:
    """Build the Phase19 matrix for one real-device public-feedback case.

    The returned payload is a test diagnostic object only. It intentionally
    stores booleans, lengths, statuses, and reason codes, but not raw memo text,
    generated candidate bodies, or public comment bodies.
    """

    safe_current_input = current_input if isinstance(current_input, Mapping) else {}
    safe_public_meta = public_meta if isinstance(public_meta, Mapping) else {}
    safe_diagnostic_meta = diagnostic_meta if isinstance(diagnostic_meta, Mapping) else {}
    safe_response_body = response_body if isinstance(response_body, Mapping) else {}

    feedback = safe_response_body.get("input_feedback")
    public_feedback = feedback if isinstance(feedback, Mapping) else None
    public_status = _optional_str(safe_public_meta.get("observation_status"))
    reason_codes = sorted(_all_reason_codes(safe_public_meta, safe_diagnostic_meta))
    candidate = _build_candidate_block(
        public_meta=safe_public_meta,
        diagnostic_meta=safe_diagnostic_meta,
        reason_codes=reason_codes,
    )
    surface_gate_status = _resolve_visible_surface_gate_status(
        public_meta=safe_public_meta,
        diagnostic_meta=safe_diagnostic_meta,
        reason_codes=reason_codes,
        candidate_generated=bool(candidate["generated_before_display_gate"]),
    )
    comment_text_present = bool(str(reply_comment_text or "").strip())
    input_feedback_included = public_feedback is not None

    matrix = {
        "schema_version": PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION,
        "source_phase": str(source_phase or PHASE19_PUBLIC_FEEDBACK_MATRIX_SOURCE_PHASE),
        "matrix_id": PHASE19_PUBLIC_FEEDBACK_MATRIX_ID,
        "case_id": str(case_id),
        "expected_public_feedback": bool(expected_public_feedback),
        "current_input": {
            "memo_present": bool(str(safe_current_input.get("memo") or "").strip()),
            "memo_action_present": bool(str(safe_current_input.get("memo_action") or "").strip()),
            "emotions_present": bool(safe_current_input.get("emotions")),
            "categories_present": bool(safe_current_input.get("category") or safe_current_input.get("categories")),
            "memo_text_len": len(str(safe_current_input.get("memo") or "")),
            "memo_action_text_len": len(str(safe_current_input.get("memo_action") or "")),
        },
        "safety": {
            "safety_blocked": _is_safety_blocked(safe_public_meta, safe_diagnostic_meta, reason_codes),
            "safety_reason": _resolve_safety_reason(public_status=public_status, reason_codes=reason_codes),
        },
        "candidate": candidate,
        "surface_gate": {
            "visible_surface_acceptance_gate": surface_gate_status,
            "rejection_reasons": reason_codes,
        },
        "public_feedback": {
            "comment_text_present": comment_text_present,
            "public_observation_status": public_status,
            "input_feedback_included": input_feedback_included,
            "first_backend_blocker": _resolve_first_backend_blocker(
                public_status=public_status,
                comment_text_present=comment_text_present,
                input_feedback_included=input_feedback_included,
                safety_blocked=_is_safety_blocked(safe_public_meta, safe_diagnostic_meta, reason_codes),
                candidate=candidate,
                surface_gate_status=surface_gate_status,
                reason_codes=reason_codes,
            ),
        },
        "rn_contract": {
            "modal_should_open": _rn_modal_should_open(public_feedback),
            "modal_title": PHASE19_PUBLIC_FEEDBACK_RN_MODAL_TITLE,
        },
    }
    validate_phase19_public_feedback_recovery_matrix(matrix)
    return matrix


def validate_phase19_public_feedback_recovery_matrix(matrix: Mapping[str, Any]) -> None:
    """Validate the minimal Phase19 matrix schema used by the tests."""

    _assert_exact_keys(matrix, _REQUIRED_TOP_LEVEL_KEYS, "matrix")
    assert matrix["schema_version"] == PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION
    assert matrix["matrix_id"] == PHASE19_PUBLIC_FEEDBACK_MATRIX_ID
    assert isinstance(matrix["case_id"], str) and matrix["case_id"].strip()
    assert isinstance(matrix["expected_public_feedback"], bool)

    _assert_exact_keys(_require_mapping(matrix["current_input"], "current_input"), _REQUIRED_CURRENT_INPUT_KEYS, "current_input")
    _assert_exact_keys(_require_mapping(matrix["safety"], "safety"), _REQUIRED_SAFETY_KEYS, "safety")
    _assert_exact_keys(_require_mapping(matrix["candidate"], "candidate"), _REQUIRED_CANDIDATE_KEYS, "candidate")
    _assert_exact_keys(_require_mapping(matrix["surface_gate"], "surface_gate"), _REQUIRED_SURFACE_GATE_KEYS, "surface_gate")
    _assert_exact_keys(
        _require_mapping(matrix["public_feedback"], "public_feedback"),
        _REQUIRED_PUBLIC_FEEDBACK_KEYS,
        "public_feedback",
    )
    _assert_exact_keys(_require_mapping(matrix["rn_contract"], "rn_contract"), _REQUIRED_RN_CONTRACT_KEYS, "rn_contract")

    current_input = _require_mapping(matrix["current_input"], "current_input")
    for key in _REQUIRED_CURRENT_INPUT_KEYS:
        if key.endswith("_len"):
            assert isinstance(current_input[key], int) and current_input[key] >= 0, key
        else:
            assert isinstance(current_input[key], bool), key

    safety = _require_mapping(matrix["safety"], "safety")
    assert isinstance(safety["safety_blocked"], bool)
    assert safety["safety_reason"] is None or isinstance(safety["safety_reason"], str)

    candidate = _require_mapping(matrix["candidate"], "candidate")
    assert isinstance(candidate["generation_attempted"], bool)
    assert isinstance(candidate["generated_before_display_gate"], bool)
    assert candidate["source"] is None or isinstance(candidate["source"], str)
    assert candidate["first_failure_reason"] is None or isinstance(candidate["first_failure_reason"], str)

    surface_gate = _require_mapping(matrix["surface_gate"], "surface_gate")
    assert surface_gate["visible_surface_acceptance_gate"] in _ALLOWED_VISIBLE_SURFACE_GATE_STATUSES
    assert isinstance(surface_gate["rejection_reasons"], list)
    assert all(isinstance(reason, str) and reason.strip() for reason in surface_gate["rejection_reasons"])

    public_feedback = _require_mapping(matrix["public_feedback"], "public_feedback")
    assert isinstance(public_feedback["comment_text_present"], bool)
    assert public_feedback["public_observation_status"] is None or isinstance(
        public_feedback["public_observation_status"], str
    )
    assert isinstance(public_feedback["input_feedback_included"], bool)
    assert public_feedback["first_backend_blocker"] is None or isinstance(
        public_feedback["first_backend_blocker"], str
    )

    rn_contract = _require_mapping(matrix["rn_contract"], "rn_contract")
    assert isinstance(rn_contract["modal_should_open"], bool)
    assert rn_contract["modal_title"] == PHASE19_PUBLIC_FEEDBACK_RN_MODAL_TITLE
    assert_phase19_public_feedback_matrix_meta_only(matrix)


def assert_phase19_public_feedback_matrix_meta_only(
    payload: Any,
    *,
    forbidden_text_fragments: Sequence[str] | None = None,
) -> None:
    """Assert that a matrix payload contains no raw input or generated bodies."""

    _assert_no_forbidden_exact_keys(payload)
    for fragment in forbidden_text_fragments or ():
        normalized = " ".join(str(fragment or "").split())
        if not normalized:
            continue
        assert not _contains_text_recursive(payload, normalized), normalized


def _build_candidate_block(
    *,
    public_meta: Mapping[str, Any],
    diagnostic_meta: Mapping[str, Any],
    reason_codes: Sequence[str],
) -> dict[str, Any]:
    public_summary = _find_mapping(public_meta, "diagnostic_summary") or public_meta
    diagnostic_summary = _find_mapping(diagnostic_meta, "diagnostic_summary") or diagnostic_meta
    candidate_path = _find_mapping(public_summary, "complete_initial_candidate_generation_path") or _find_mapping(
        diagnostic_summary, "complete_initial_candidate_generation_path"
    )
    candidate_generated = _candidate_generated(public_meta, diagnostic_meta)
    composer_status = _optional_str(public_summary.get("composer_status")) or _optional_str(
        diagnostic_summary.get("composer_status")
    )
    candidate_status = _optional_str(candidate_path.get("candidate_status"))
    candidate_status_before_gate = _optional_str(candidate_path.get("candidate_status_before_display_gate"))
    source = _first_non_empty_recursive(
        (candidate_path, public_summary, diagnostic_summary, public_meta, diagnostic_meta),
        (
            "candidate_source",
            "candidate_source_before_display_gate",
            "composer_source",
            "comment_source",
            "reply_source",
        ),
    )
    first_failure_reason = _first_non_empty_recursive(
        (candidate_path, public_summary, diagnostic_summary, public_meta, diagnostic_meta),
        (
            "first_failure_reason",
            "fail_closed_reason_code",
            "primary_reason",
            "candidate_failure_reason",
            "generation_failure_reason",
        ),
    )
    if first_failure_reason is None and reason_codes:
        first_failure_reason = _first_reason_code_that_is_not_success(reason_codes)
    return {
        "generation_attempted": bool(candidate_path or composer_status or candidate_status or candidate_status_before_gate),
        "generated_before_display_gate": candidate_generated,
        "source": source,
        "first_failure_reason": first_failure_reason,
    }


def _candidate_generated(public_meta: Mapping[str, Any], diagnostic_meta: Mapping[str, Any]) -> bool:
    for source in (diagnostic_meta, public_meta):
        if not isinstance(source, Mapping):
            continue
        diagnostic_summary = _find_mapping(source, "diagnostic_summary") or source
        candidate_path = _find_mapping(diagnostic_summary, "complete_initial_candidate_generation_path")
        if candidate_path:
            if candidate_path.get("candidate_generated") is True:
                return True
            if candidate_path.get("candidate_generated_before_display_gate") is True:
                return True
            if str(candidate_path.get("candidate_status") or "") == "generated":
                return True
            if str(candidate_path.get("candidate_status_before_display_gate") or "") == "generated":
                return True
        if str(diagnostic_summary.get("composer_status") or "").strip() == "generated":
            return True
    return False


def _visible_surface_gate_passed(public_meta: Mapping[str, Any], diagnostic_meta: Mapping[str, Any]) -> bool:
    for source in (public_meta, diagnostic_meta):
        gate = _find_mapping(source, "visible_surface_acceptance_gate")
        if gate.get("passed") is True:
            return True
        diagnostic_gate = _find_mapping(source, "diagnostic_summary", "gate_results", "visible_surface_acceptance")
        if diagnostic_gate.get("passed") is True:
            return True
    return False


def _visible_surface_gate_reached(public_meta: Mapping[str, Any], diagnostic_meta: Mapping[str, Any]) -> bool:
    for source in (public_meta, diagnostic_meta):
        if _find_mapping(source, "visible_surface_acceptance_gate"):
            return True
        if _find_mapping(source, "diagnostic_summary", "gate_results", "visible_surface_acceptance"):
            return True
    return False


def _resolve_visible_surface_gate_status(
    *,
    public_meta: Mapping[str, Any],
    diagnostic_meta: Mapping[str, Any],
    reason_codes: Sequence[str],
    candidate_generated: bool,
) -> str:
    if _visible_surface_gate_passed(public_meta, diagnostic_meta):
        return VISIBLE_SURFACE_GATE_PASSED
    if _visible_surface_gate_reached(public_meta, diagnostic_meta):
        return VISIBLE_SURFACE_GATE_FAILED
    if not candidate_generated:
        return VISIBLE_SURFACE_GATE_NOT_REACHED
    if reason_codes:
        return VISIBLE_SURFACE_GATE_FAILED
    return VISIBLE_SURFACE_GATE_UNKNOWN


def _resolve_first_backend_blocker(
    *,
    public_status: str | None,
    comment_text_present: bool,
    input_feedback_included: bool,
    safety_blocked: bool,
    candidate: Mapping[str, Any],
    surface_gate_status: str,
    reason_codes: Sequence[str],
) -> str | None:
    if safety_blocked:
        return "safety_blocked"
    if not bool(candidate.get("generated_before_display_gate")) and bool(candidate.get("generation_attempted")):
        candidate_failure = _optional_str(candidate.get("first_failure_reason"))
        return candidate_failure or "candidate_not_generated"
    if surface_gate_status == VISIBLE_SURFACE_GATE_FAILED:
        visible_failure = _first_surface_failure_reason(reason_codes)
        if visible_failure:
            return visible_failure
    if not comment_text_present:
        return "comment_text_missing"
    if public_status != "passed":
        return f"observation_status_{public_status or 'missing'}"
    if not input_feedback_included:
        return "public_feedback_not_included"
    return None


def _resolve_safety_reason(*, public_status: str | None, reason_codes: Sequence[str]) -> str | None:
    if public_status == "safety_blocked":
        safety_reason = _first_matching_reason(reason_codes, ("safety", "self_harm", "harm"))
        return safety_reason or "safety_blocked"
    return _first_matching_reason(reason_codes, ("safety", "self_harm", "harm"))


def _is_safety_blocked(
    public_meta: Mapping[str, Any],
    diagnostic_meta: Mapping[str, Any],
    reason_codes: Sequence[str],
) -> bool:
    if str(public_meta.get("observation_status") or "") == "safety_blocked":
        return True
    if str(diagnostic_meta.get("observation_status") or "") == "safety_blocked":
        return True
    return any("safety_blocked" == reason or "self_harm" in reason for reason in reason_codes)


def _rn_modal_should_open(feedback: Mapping[str, Any] | None) -> bool:
    if not isinstance(feedback, Mapping):
        return False
    emlis_ai = feedback.get("emlis_ai")
    return bool(
        str(feedback.get("comment_text") or "").strip()
        and isinstance(emlis_ai, Mapping)
        and str(emlis_ai.get("observation_status") or "") == "passed"
    )


def _all_reason_codes(*sources: Mapping[str, Any]) -> set[str]:
    reasons: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"rejection_reasons", "reason_codes", "surface_issue_codes"} and isinstance(
                    child, Sequence
                ) and not isinstance(child, (str, bytes, bytearray)):
                    reasons.update(str(item) for item in child if str(item or "").strip())
                elif key in {
                    "primary_reason",
                    "first_failure_reason",
                    "fail_closed_reason_code",
                    "candidate_failure_reason",
                    "generation_failure_reason",
                } and str(child or "").strip():
                    reasons.add(str(child))
                else:
                    collect(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                collect(child)

    for source in sources:
        if isinstance(source, Mapping):
            collect(source)
    return reasons


def _find_mapping(value: Mapping[str, Any] | None, *keys: str) -> Mapping[str, Any]:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key)
    return current if isinstance(current, Mapping) else {}


def _first_non_empty_recursive(values: Sequence[Any], keys: Sequence[str]) -> str | None:
    key_set = set(keys)

    def rec(value: Any) -> str | None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if str(key) in key_set:
                    text = _optional_str(child)
                    if text:
                        return text
                nested = rec(child)
                if nested:
                    return nested
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                nested = rec(child)
                if nested:
                    return nested
        return None

    for value in values:
        found = rec(value)
        if found:
            return found
    return None


def _first_reason_code_that_is_not_success(reason_codes: Sequence[str]) -> str | None:
    for reason in reason_codes:
        normalized = str(reason or "").strip()
        if normalized and normalized not in {"green", "passed"}:
            return normalized
    return None


def _first_surface_failure_reason(reason_codes: Sequence[str]) -> str | None:
    priority = (
        "visible_surface_acceptance_gate_failed",
        "surface_relation_skeleton_major",
        "limited_composer_repeated_surface",
        "phase8_repeated_sentence_tail",
        "repeated_surface",
        "runtime_surface_pre_return_gate_failed",
        "runtime_surface_pre_return_gate_action_fail_closed",
        "empty_comment_text_without_candidate",
        "empty_comment_text",
        "comment_text_missing",
    )
    reason_set = {str(reason) for reason in reason_codes}
    for reason in priority:
        if reason in reason_set:
            return reason
    return _first_reason_code_that_is_not_success(reason_codes)


def _first_matching_reason(reason_codes: Sequence[str], needles: Sequence[str]) -> str | None:
    for reason in reason_codes:
        normalized = str(reason or "").strip()
        if normalized and any(needle in normalized for needle in needles):
            return normalized
    return None


def _optional_str(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    assert isinstance(value, Mapping), name
    return value


def _assert_exact_keys(value: Mapping[str, Any], required: frozenset[str], name: str) -> None:
    actual = set(value.keys())
    assert actual == set(required), f"{name}: missing={sorted(required - actual)}, extra={sorted(actual - required)}"


def _assert_no_forbidden_exact_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            assert str(key) not in _FORBIDDEN_EXACT_KEYS, key
            _assert_no_forbidden_exact_keys(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_exact_keys(item)


def _contains_text_recursive(value: Any, needle: str) -> bool:
    target = " ".join(str(needle or "").split())
    if not target:
        return False
    if isinstance(value, Mapping):
        return any(_contains_text_recursive(child, target) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_recursive(child, target) for child in value)
    if isinstance(value, str):
        return target in " ".join(value.split())
    return False


__all__ = [
    "PHASE19_PUBLIC_FEEDBACK_MATRIX_ID",
    "PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION",
    "PHASE19_PUBLIC_FEEDBACK_MATRIX_SOURCE_PHASE",
    "PHASE19_PUBLIC_FEEDBACK_RN_MODAL_TITLE",
    "VISIBLE_SURFACE_GATE_FAILED",
    "VISIBLE_SURFACE_GATE_NOT_REACHED",
    "VISIBLE_SURFACE_GATE_PASSED",
    "VISIBLE_SURFACE_GATE_UNKNOWN",
    "assert_phase19_public_feedback_matrix_meta_only",
    "build_phase19_public_feedback_recovery_matrix",
    "validate_phase19_public_feedback_recovery_matrix",
]
