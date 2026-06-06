# -*- coding: utf-8 -*-
from __future__ import annotations

"""P0 diagnostic naming for EmlisAI Public Observation Recovery tests.

This helper is test material only.  It names the current regression shape as
``public_reached`` / ``rn_visible`` / ``product_surface_valid`` without adding
public response keys, serializing raw input, or copying public comment bodies.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
)
from emlis_ai_public_surface_requirement import (
    PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    resolve_public_surface_requirement,
)

PUBLIC_OBSERVATION_RECOVERY_P0_SCHEMA_VERSION: Final = (
    "cocolon.emlis.public_observation_recovery_p0.v1"
)
PUBLIC_OBSERVATION_RECOVERY_P0_SOURCE_PHASE: Final = (
    "PublicObservationRecovery_P0_RedTestNaming"
)

FAILURE_FAMILY_NONE: Final = "none"
FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE: Final = (
    "public_feedback_absent_complete_initial_surface_unavailable"
)
FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_EMPTY_COMMENT_TEXT: Final = (
    "public_feedback_absent_empty_comment_text"
)
FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_NON_PASSED: Final = (
    "public_feedback_absent_non_passed"
)
FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_SURFACE_GATE_FAILED: Final = (
    "public_feedback_absent_surface_gate_failed"
)
FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_UNCLASSIFIED: Final = (
    "public_feedback_absent_unclassified"
)
FAILURE_FAMILY_RN_VISIBLE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE: Final = (
    "rn_visible_product_surface_invalid_two_stage_shape"
)
FAILURE_FAMILY_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE: Final = (
    "product_surface_invalid_low_information_misroute"
)
FAILURE_FAMILY_PUBLIC_BOUNDARY_LEAK: Final = "public_boundary_leak"

_TRUE_VALUES: Final = frozenset({"1", "true", "yes", "on", "passed", "ok", "generated", "green"})
_SOURCE_UNAVAILABLE_VALUES: Final = frozenset({"", "unavailable", "none", "null", "missing", "not_generated"})
_COMPLETE_INITIAL_UNAVAILABLE_REASONS: Final = frozenset(
    {
        "complete_initial_surface_unavailable",
        "composer_source_unavailable",
        "source_unavailable",
        "surface_signature_unavailable",
    }
)
_SURFACE_GATE_FAILURE_REASONS: Final = frozenset(
    {
        "visible_surface_acceptance_gate_failed",
        "runtime_surface_pre_return_gate_failed",
        "runtime_surface_pre_return_gate_action_block",
        "runtime_surface_pre_return_gate_action_fail_closed",
        "surface_relation_skeleton_major",
        "two_stage_relation_skeleton_leak",
    }
)
_FORBIDDEN_EXACT_KEYS: Final = frozenset(
    {
        "raw_input",
        "raw_text",
        "input_text",
        "user_input",
        "current_input",
        "current_input_text",
        "memo",
        "memo_action",
        "comment_text",
        "candidate_comment_text",
        "public_comment_text",
        "generated_text",
        "generated_candidate_text",
        "candidate_text",
        "surface_text",
        "observation_text",
        "reception_text",
        "evidence_text",
        "evidence_spans",
        "body",
        "text",
    }
)
_REQUIRED_TOP_LEVEL_KEYS: Final = frozenset(
    {
        "schema_version",
        "source_phase",
        "public_reached",
        "rn_visible",
        "product_surface_valid",
        "failure_family",
        "failure_code",
        "surface_requirement",
        "comment_text_shape",
        "recovery_lane",
        "boundary",
    }
)


def _clean(value: Any) -> str:
    return str(value or "").replace("\u3000", " ").strip()


def _clean_lower(value: Any) -> str:
    return _clean(value).lower()


def _as_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _recursive_mappings(*sources: Any) -> list[Mapping[str, Any]]:
    """Collect body-free diagnostic mappings without repeatedly walking shared payloads."""

    from collections import deque
    from itertools import islice

    out: list[Mapping[str, Any]] = []
    queue: deque[Mapping[str, Any]] = deque()
    visited: set[int] = set()
    max_mappings = 4096
    max_sequence_items_per_node = 256

    for source in sources:
        mapping = _as_mapping(source)
        if mapping:
            queue.append(mapping)
    while queue and len(out) < max_mappings:
        current = queue.popleft()
        marker = id(current)
        if marker in visited:
            continue
        visited.add(marker)
        out.append(current)
        for child in current.values():
            if isinstance(child, Mapping):
                if id(child) not in visited:
                    queue.append(child)
            elif isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
                for item in islice(child, max_sequence_items_per_node):
                    if isinstance(item, Mapping) and id(item) not in visited:
                        queue.append(item)
    return out


def _first_text_for_keys(sources: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> str:
    key_set = set(keys)
    for source in sources:
        for key, value in source.items():
            if str(key) in key_set:
                text = _clean(value)
                if text:
                    return text
    return ""


def _all_reason_codes(sources: Sequence[Mapping[str, Any]]) -> set[str]:
    reasons: set[str] = set()
    for source in sources:
        for key, value in source.items():
            if key in {"rejection_reasons", "reason_codes", "surface_issue_codes"}:
                for item in _listify(value):
                    text = _clean(item)
                    if text:
                        reasons.add(text)
            elif key in {
                "primary_reason",
                "first_failure_reason",
                "fail_closed_reason_code",
                "candidate_failure_reason",
                "generation_failure_reason",
                "blocker_code",
                "blocker_family",
            }:
                text = _clean(value)
                if text:
                    reasons.add(text)
    return reasons


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return bool(value)
    return _clean_lower(value) in _TRUE_VALUES


def _any_true_for_keys(sources: Sequence[Mapping[str, Any]], keys: Sequence[str]) -> bool:
    key_set = set(keys)
    for source in sources:
        for key, value in source.items():
            if str(key) in key_set and _truthy(value):
                return True
    return False


def _source_kind(sources: Sequence[Mapping[str, Any]]) -> str:
    return _clean_lower(
        _first_text_for_keys(
            sources,
            (
                "candidate_source_kind",
                "public_candidate_source_kind",
                "source_kind",
                "adopted_candidate_source_kind",
                "final_surface_origin_candidate_source_kind",
            ),
        )
    )


def _source_value(sources: Sequence[Mapping[str, Any]]) -> str:
    return _clean_lower(
        _first_text_for_keys(
            sources,
            (
                "candidate_source",
                "candidate_source_before_display_gate",
                "composer_source",
                "comment_source",
                "reply_source",
            ),
        )
    )


def _status_value(sources: Sequence[Mapping[str, Any]]) -> str:
    return _clean_lower(
        _first_text_for_keys(
            sources,
            (
                "candidate_status",
                "candidate_status_before_display_gate",
                "complete_initial_candidate_status",
                "status",
                "composer_status",
                "observation_status",
            ),
        )
    )


def _public_reached(response_body: Mapping[str, Any]) -> bool:
    return isinstance(response_body.get("input_feedback"), Mapping)


def _rn_visible(response_body: Mapping[str, Any]) -> bool:
    feedback = response_body.get("input_feedback")
    if not isinstance(feedback, Mapping):
        return False
    emlis_ai = feedback.get("emlis_ai")
    return bool(
        _clean(feedback.get("comment_text"))
        and isinstance(emlis_ai, Mapping)
        and _clean(emlis_ai.get("observation_status")) == "passed"
    )


def _labelled_two_stage_shape_present(comment_text: Any) -> bool:
    text = str(comment_text or "")
    return text.startswith("見えたこと：\n") and "\n\nEmlisから：\n" in text


def _low_information_candidate_adopted(sources: Sequence[Mapping[str, Any]]) -> bool:
    for source in sources:
        values = {
            _clean_lower(source.get("observation_reply_kind")),
            _clean_lower(source.get("reply_kind")),
            _clean_lower(source.get("eligibility_status")),
            _clean_lower(source.get("material_quality")),
        }
        if "low_information_observation" in values or "low_information" in values:
            return True
        if _truthy(source.get("low_information_repair_branch")) or _truthy(source.get("low_information_repair_applied")):
            return True
    return False


def _resolve_failure_family(
    *,
    public_reached: bool,
    rn_visible: bool,
    product_surface_valid: bool,
    comment_text_present: bool,
    status: str,
    reason_codes: set[str],
    source: str,
    source_kind: str,
    two_stage_required: bool,
    labelled_two_stage_shape_present: bool,
    plain_surface_used: bool,
    low_information_candidate_adopted: bool,
    gate_recovery_material_surface_used: bool,
) -> tuple[str, str | None]:
    if product_surface_valid:
        return FAILURE_FAMILY_NONE, None
    if gate_recovery_material_surface_used:
        return FAILURE_FAMILY_PUBLIC_BOUNDARY_LEAK, "gate_recovery_material_surface_public_leak"
    complete_initial_unavailable = bool(
        source in _SOURCE_UNAVAILABLE_VALUES
        or source_kind in {"unavailable", "none"}
        or reason_codes & _COMPLETE_INITIAL_UNAVAILABLE_REASONS
    )
    if not public_reached or not rn_visible:
        if complete_initial_unavailable:
            return (
                FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE,
                "complete_initial_surface_unavailable",
            )
        if not comment_text_present:
            return FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_EMPTY_COMMENT_TEXT, "comment_text_missing"
        if status and status != "passed":
            return FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_NON_PASSED, f"observation_status_{status}"
        if reason_codes & _SURFACE_GATE_FAILURE_REASONS:
            return FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_SURFACE_GATE_FAILED, sorted(reason_codes & _SURFACE_GATE_FAILURE_REASONS)[0]
        return FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_UNCLASSIFIED, "public_feedback_absent_unclassified"
    if two_stage_required and low_information_candidate_adopted:
        return FAILURE_FAMILY_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE, "low_information_used_for_two_stage_required"
    if two_stage_required and (plain_surface_used or not labelled_two_stage_shape_present):
        return (
            FAILURE_FAMILY_RN_VISIBLE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE,
            "product_surface_invalid_plain_used_for_two_stage_required",
        )
    return FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_UNCLASSIFIED, "product_surface_invalid_unclassified"


def build_public_observation_recovery_p0_summary(
    *,
    current_input: Mapping[str, Any] | None,
    public_meta: Mapping[str, Any] | None,
    diagnostic_meta: Mapping[str, Any] | None = None,
    reply_comment_text: Any = None,
    response_body: Mapping[str, Any] | None = None,
    surface_requirement_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    safe_current = _as_mapping(current_input)
    safe_public_meta = _as_mapping(public_meta)
    safe_diagnostic_meta = _as_mapping(diagnostic_meta)
    safe_response_body = _as_mapping(response_body)
    sources = _recursive_mappings(safe_public_meta, safe_diagnostic_meta)
    reason_codes = _all_reason_codes(sources)
    decision = _as_mapping(surface_requirement_decision) or resolve_public_surface_requirement(
        current_input=safe_current,
        composer_meta=safe_public_meta,
        diagnostic_summary=safe_diagnostic_meta,
        comment_text_present=bool(_clean(reply_comment_text)),
    )
    family = _clean(decision.get("surface_requirement_family"))
    two_stage_required = bool(decision.get("two_stage_required"))
    plain_allowed = bool(decision.get("plain_state_answer_allowed"))
    low_information_allowed = bool(decision.get("low_information_allowed"))
    public_reached_value = _public_reached(safe_response_body)
    rn_visible_value = _rn_visible(safe_response_body)
    comment_present = bool(_clean(reply_comment_text))
    labelled_shape = _labelled_two_stage_shape_present(reply_comment_text)
    plain_surface_used = bool(comment_present and not labelled_shape)
    low_info_used = _low_information_candidate_adopted(sources)
    source_kind = _source_kind(sources)
    source = _source_value(sources)
    status = _status_value(sources)
    normal_rebuild_used = bool(
        source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        or _any_true_for_keys(sources, ("normal_observation_rebuild_applied", "normal_observation_rebuild_used"))
    )
    gate_recovery_material_surface_used = bool(
        source_kind == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
        or _any_true_for_keys(sources, ("gate_recovery_material_surface_used_as_public_body",))
    )

    if two_stage_required:
        product_surface_valid = bool(rn_visible_value and labelled_shape and not low_info_used and not gate_recovery_material_surface_used)
    elif family == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION:
        product_surface_valid = bool(rn_visible_value and low_information_allowed and not gate_recovery_material_surface_used)
    elif family == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER:
        product_surface_valid = bool(rn_visible_value and plain_allowed and not gate_recovery_material_surface_used)
    else:
        product_surface_valid = bool(rn_visible_value and not gate_recovery_material_surface_used)

    failure_family, failure_code = _resolve_failure_family(
        public_reached=public_reached_value,
        rn_visible=rn_visible_value,
        product_surface_valid=product_surface_valid,
        comment_text_present=comment_present,
        status=status,
        reason_codes=reason_codes,
        source=source,
        source_kind=source_kind,
        two_stage_required=two_stage_required,
        labelled_two_stage_shape_present=labelled_shape,
        plain_surface_used=plain_surface_used,
        low_information_candidate_adopted=low_info_used,
        gate_recovery_material_surface_used=gate_recovery_material_surface_used,
    )

    source_unavailable = bool(source in _SOURCE_UNAVAILABLE_VALUES or reason_codes & _COMPLETE_INITIAL_UNAVAILABLE_REASONS)
    summary = {
        "schema_version": PUBLIC_OBSERVATION_RECOVERY_P0_SCHEMA_VERSION,
        "source_phase": PUBLIC_OBSERVATION_RECOVERY_P0_SOURCE_PHASE,
        "public_reached": bool(public_reached_value),
        "rn_visible": bool(rn_visible_value),
        "product_surface_valid": bool(product_surface_valid),
        "failure_family": failure_family,
        "failure_code": failure_code,
        "surface_requirement": {
            "schema_version": PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
            "surface_requirement_family": family,
            "two_stage_required": bool(two_stage_required),
            "plain_state_answer_allowed": bool(plain_allowed),
            "low_information_allowed": bool(low_information_allowed),
            "material_quality_family": _clean(decision.get("material_quality_family")),
            "source_unavailable": bool(source_unavailable or decision.get("source_unavailable")),
        },
        "comment_text_shape": {
            "comment_text_present": bool(comment_present),
            "labelled_two_stage_shape_present": bool(labelled_shape),
            "plain_surface_used": bool(plain_surface_used),
            "low_information_candidate_adopted": bool(low_info_used),
            "comment_text_body_included": False,
        },
        "recovery_lane": {
            "normal_observation_rebuild_allowed": bool(decision.get("normal_observation_rebuild_allowed")),
            "normal_observation_rebuild_used": bool(normal_rebuild_used),
            "source_unavailable_not_normal_rebuildable": bool(source_unavailable),
            "complete_initial_surface_recomposition_expected": bool(
                decision.get("complete_initial_surface_recomposition_lane")
                or (two_stage_required and source_unavailable)
            ),
        },
        "boundary": {
            "gate_recovery_material_surface_used_as_public_body": bool(gate_recovery_material_surface_used),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "public_response_key_added": False,
            "rn_visible_contract_changed": False,
            "display_gate_relaxed": False,
        },
    }
    validate_public_observation_recovery_p0_summary(summary)
    return summary


def validate_public_observation_recovery_p0_summary(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise AssertionError("p0 summary must be a mapping")
    actual = set(value.keys())
    missing = _REQUIRED_TOP_LEVEL_KEYS - actual
    extra = actual - _REQUIRED_TOP_LEVEL_KEYS
    assert actual == _REQUIRED_TOP_LEVEL_KEYS, f"p0_summary: missing={sorted(missing)}, extra={sorted(extra)}"
    assert value["schema_version"] == PUBLIC_OBSERVATION_RECOVERY_P0_SCHEMA_VERSION
    assert value["source_phase"] == PUBLIC_OBSERVATION_RECOVERY_P0_SOURCE_PHASE
    assert isinstance(value["public_reached"], bool)
    assert isinstance(value["rn_visible"], bool)
    assert isinstance(value["product_surface_valid"], bool)
    assert isinstance(value["failure_family"], str) and value["failure_family"].strip()
    assert value["failure_code"] is None or isinstance(value["failure_code"], str)
    assert isinstance(value["surface_requirement"], Mapping)
    assert isinstance(value["comment_text_shape"], Mapping)
    assert isinstance(value["recovery_lane"], Mapping)
    assert isinstance(value["boundary"], Mapping)
    assert_public_observation_recovery_p0_summary_meta_only(value)


def assert_public_observation_recovery_p0_summary_meta_only(value: Any) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = _clean(raw_key)
            assert key not in _FORBIDDEN_EXACT_KEYS, key
            if key in {
                "raw_input_included",
                "raw_text_included",
                "comment_text_body_included",
                "public_response_key_added",
                "rn_visible_contract_changed",
                "display_gate_relaxed",
            }:
                assert child is False, key
            assert_public_observation_recovery_p0_summary_meta_only(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            assert_public_observation_recovery_p0_summary_meta_only(item)


__all__ = [
    "FAILURE_FAMILY_NONE",
    "FAILURE_FAMILY_PRODUCT_SURFACE_INVALID_LOW_INFORMATION_MISROUTE",
    "FAILURE_FAMILY_PUBLIC_BOUNDARY_LEAK",
    "FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_COMPLETE_INITIAL_SURFACE_UNAVAILABLE",
    "FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_EMPTY_COMMENT_TEXT",
    "FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_NON_PASSED",
    "FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_SURFACE_GATE_FAILED",
    "FAILURE_FAMILY_PUBLIC_FEEDBACK_ABSENT_UNCLASSIFIED",
    "FAILURE_FAMILY_RN_VISIBLE_PRODUCT_SURFACE_INVALID_TWO_STAGE_SHAPE",
    "PUBLIC_OBSERVATION_RECOVERY_P0_SCHEMA_VERSION",
    "PUBLIC_OBSERVATION_RECOVERY_P0_SOURCE_PHASE",
    "assert_public_observation_recovery_p0_summary_meta_only",
    "build_public_observation_recovery_p0_summary",
    "validate_public_observation_recovery_p0_summary",
]
