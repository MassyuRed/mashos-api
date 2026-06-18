# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free public source lineage record builder/sanitizer for EmlisAI.

R4/R5 keeps source lineage explainable without copying user input,
``comment_text``, candidate bodies, Gate Recovery material surfaces, traceback,
or reviewer text into public metadata.  The helpers are allow-list based and
return identifiers, booleans, small integer counters, and reason identifiers
only.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import re

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_NONE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    RECOVERY_CONTEXT_UNKNOWN,
)

BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.body_free_public_source_lineage_record.v1"
)
BODY_FREE_PUBLIC_SOURCE_LINEAGE_SOURCE_PHASE: Final = (
    "DisplayContractRedClassification_R4_R5_BodyFreeLineageSanitizer"
)

_IDENTIFIER_RE: Final = re.compile(r"^[A-Za-z0-9_.:/\-]+$")
_BODY_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "memo",
        "memo_action",
        "emotion_details",
        "comment_text",
        "commentText",
        "candidate_comment_text",
        "public_comment_text",
        "surface_text",
        "surface_body",
        "candidate_body",
        "generated_text",
        "realized_text",
        "text",
        "body",
        "source_text",
        "input_text",
        "evidence_text",
        "reviewer_free_text",
        "traceback",
        "terminal_output",
    }
)
_GATE_RELAXATION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "display_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "safety_gate_relaxed",
    }
)
_BODY_FLAG_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "original_comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "body_included",
    }
)
_ALLOWED_REASON_RE: Final = re.compile(r"^[A-Za-z0-9_.:/\-]+$")


def build_body_free_public_source_lineage_record(
    *,
    recovery_context: str = RECOVERY_CONTEXT_UNKNOWN,
    recovery_pass_index: int = 0,
    root_candidate_source_kind: str = CANDIDATE_SOURCE_KIND_NONE,
    recovery_input_candidate_source_kind: str = CANDIDATE_SOURCE_KIND_NONE,
    selected_public_candidate_source_kind: str = CANDIDATE_SOURCE_KIND_NONE,
    pre_public_candidate_source_kind: str = "",
    final_public_candidate_source_kind: str = CANDIDATE_SOURCE_KIND_NONE,
    public_surface_role: str = PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    surface_requirement: Mapping[str, Any] | None = None,
    surface_requirement_family: str = "",
    two_stage_required: bool | None = None,
    plain_surface_allowed: bool | None = None,
    low_information_allowed: bool | None = None,
    source_phase: str = BODY_FREE_PUBLIC_SOURCE_LINEAGE_SOURCE_PHASE,
) -> dict[str, Any]:
    """Build the canonical R4 body-free lineage record."""

    requirement = _mapping_or_empty(surface_requirement)
    family = _clean_identifier(
        surface_requirement_family
        or requirement.get("surface_requirement_family")
        or requirement.get("product_surface_requirement_family"),
        max_length=96,
    )
    final_source = _clean_identifier(final_public_candidate_source_kind, max_length=128) or CANDIDATE_SOURCE_KIND_NONE
    base: dict[str, Any] = {
        "schema_version": BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION,
        "source_phase": source_phase,
        "candidate_source_kind": final_source,
        "recovery_context": recovery_context,
        "recovery_pass_index": recovery_pass_index,
        "root_candidate_source_kind": root_candidate_source_kind,
        "recovery_input_candidate_source_kind": recovery_input_candidate_source_kind,
        "selected_public_candidate_source_kind": selected_public_candidate_source_kind,
        "pre_public_candidate_source_kind": pre_public_candidate_source_kind,
        "final_public_candidate_source_kind": final_source,
        "public_surface_role": public_surface_role,
        "surface_requirement_family": family,
        "two_stage_required": _coerce_bool(
            two_stage_required,
            fallback=bool(
                requirement.get("two_stage_required")
                or requirement.get("product_surface_two_stage_required")
            ),
        ),
        "plain_surface_allowed": _coerce_bool(
            plain_surface_allowed,
            fallback=bool(requirement.get("plain_state_answer_allowed") or requirement.get("plain_surface_allowed")),
        ),
        "low_information_allowed": _coerce_bool(
            low_information_allowed,
            fallback=bool(requirement.get("low_information_allowed")),
        ),
    }
    return sanitize_body_free_public_source_lineage_record(base)


def sanitize_body_free_public_source_lineage_record(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a body-free, allow-listed source lineage record.

    Arbitrary keys are ignored.  Body-bearing keys such as ``comment_text``,
    ``raw_input``, ``body`` and ``traceback`` are never copied into the output.
    """

    source = _mapping_or_empty(value)
    final_source = _clean_identifier(
        _first(source, ("final_public_candidate_source_kind", "candidate_source_kind")),
        max_length=128,
    ) or CANDIDATE_SOURCE_KIND_NONE
    candidate_source = _clean_identifier(source.get("candidate_source_kind"), max_length=128) or final_source
    root_source = _clean_identifier(
        _first(
            source,
            (
                "root_candidate_source_kind",
                "original_candidate_source_kind",
                "original_candidate_source",
            ),
        ),
        max_length=128,
    ) or CANDIDATE_SOURCE_KIND_NONE
    selected_source = _clean_identifier(source.get("selected_public_candidate_source_kind"), max_length=128) or final_source
    recovery_input_source = _clean_identifier(source.get("recovery_input_candidate_source_kind"), max_length=128) or CANDIDATE_SOURCE_KIND_NONE
    pre_public_source = _clean_identifier(source.get("pre_public_candidate_source_kind"), max_length=128) or ""
    public_role = _clean_identifier(source.get("public_surface_role"), max_length=128) or (
        PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
        if final_source in FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS
        else PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    )

    complete_initial_final_used = final_source == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    labelled_two_stage_final_used = final_source == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    normal_rebuild_used = final_source == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    allowed_source = final_source in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
    forbidden_source = final_source in FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS

    record: dict[str, Any] = {
        "schema_version": BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION,
        "source_phase": _clean_identifier(source.get("source_phase"), max_length=160)
        or BODY_FREE_PUBLIC_SOURCE_LINEAGE_SOURCE_PHASE,
        "candidate_source_kind": candidate_source,
        "root_candidate_source_kind": root_source,
        "recovery_input_candidate_source_kind": recovery_input_source,
        "selected_public_candidate_source_kind": selected_source,
        "pre_public_candidate_source_kind": pre_public_source,
        "final_public_candidate_source_kind": final_source,
        "lineage_consistency_passed": bool(candidate_source == final_source and selected_source == final_source),
        "public_candidate_source_allowed": bool(_coerce_bool(source.get("public_candidate_source_allowed"), fallback=allowed_source)),
        "public_candidate_source_forbidden": bool(_coerce_bool(source.get("public_candidate_source_forbidden"), fallback=forbidden_source)),
        "public_surface_role": public_role,
        "public_display_allowed_by_boundary": bool(
            _coerce_bool(source.get("public_display_allowed_by_boundary"), fallback=allowed_source and not forbidden_source)
        ),
        "normal_observation_rebuild_used": bool(
            _coerce_bool(source.get("normal_observation_rebuild_used"), fallback=normal_rebuild_used)
        ),
        "complete_initial_surface_recomposition_attempted": bool(
            _coerce_bool(
                source.get("complete_initial_surface_recomposition_attempted"),
                fallback=pre_public_source == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
            )
        ),
        "complete_initial_surface_recomposition_used": bool(
            _coerce_bool(source.get("complete_initial_surface_recomposition_used"), fallback=complete_initial_final_used)
        ),
        "complete_initial_surface_recomposition_final_used": bool(
            _coerce_bool(source.get("complete_initial_surface_recomposition_final_used"), fallback=complete_initial_final_used)
        ),
        "labelled_two_stage_surface_recomposition_used": bool(
            _coerce_bool(source.get("labelled_two_stage_surface_recomposition_used"), fallback=labelled_two_stage_final_used)
        ),
        "labelled_two_stage_surface_recomposition_final_used": bool(
            _coerce_bool(source.get("labelled_two_stage_surface_recomposition_final_used"), fallback=labelled_two_stage_final_used)
        ),
        "gate_recovery_material_surface_used_as_public_body": bool(
            final_source == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
        ),
        "diagnostic_recovery_surface_used_as_public_body": bool(
            final_source == CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE
        ),
        "surface_requirement_family": _clean_identifier(source.get("surface_requirement_family"), max_length=96) or "",
        "two_stage_required": bool(_coerce_bool(source.get("two_stage_required"), fallback=False)),
        "plain_surface_allowed": bool(_coerce_bool(source.get("plain_surface_allowed"), fallback=False)),
        "low_information_allowed": bool(_coerce_bool(source.get("low_information_allowed"), fallback=False)),
        "body_free": True,
        "body_free_sanitizer_passed": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "original_comment_text_body_included": False,
        "candidate_body_included": False,
        "display_gate_relaxed": False,
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
    }
    recovery_context = _clean_identifier(source.get("recovery_context"), max_length=96)
    if recovery_context:
        record["recovery_context"] = recovery_context
    recovery_pass_index = _safe_int(source.get("recovery_pass_index"), minimum=0, maximum=999)
    if recovery_pass_index is not None:
        record["recovery_pass_index"] = recovery_pass_index
    product_surface_valid = _coerce_bool(source.get("product_surface_valid"), fallback=None)
    if product_surface_valid is not None:
        record["product_surface_valid"] = bool(product_surface_valid)
    blocked_reasons = _safe_reason_list(source.get("blocked_reasons"))
    if blocked_reasons:
        record["blocked_reasons"] = blocked_reasons
    return record


def assert_body_free_public_source_lineage_record(value: Mapping[str, Any]) -> None:
    """Raise ``ValueError`` when a public source lineage record is not safe."""

    if not isinstance(value, Mapping):
        raise ValueError("body-free public source lineage record must be a mapping")
    if value.get("schema_version") != BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION:
        raise ValueError("unexpected body-free public source lineage schema_version")
    for key in _BODY_PAYLOAD_KEYS:
        if key in value:
            raise ValueError(f"body-bearing field must not be present: {key}")
    for key in _BODY_FLAG_KEYS:
        if bool(value.get(key)):
            raise ValueError(f"body flag must be false: {key}")
    for key in _GATE_RELAXATION_KEYS:
        if bool(value.get(key)):
            raise ValueError(f"gate relaxation flag must be false: {key}")
    if value.get("body_free") is not True:
        raise ValueError("body_free must be true")


def _mapping_or_empty(value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first(source: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        value = source.get(key)
        if value is not None and value != "":
            return value
    return ""


def _clean_identifier(value: Any, *, max_length: int) -> str:
    if value is None or isinstance(value, (bool, int, float)):
        return ""
    text = str(value).strip()
    if not text or len(text) > max_length or not _IDENTIFIER_RE.fullmatch(text):
        return ""
    return text


def _coerce_bool(value: Any, *, fallback: bool | None = False) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lower = value.strip().lower()
        if lower in {"true", "1", "yes"}:
            return True
        if lower in {"false", "0", "no"}:
            return False
    return fallback


def _safe_int(value: Any, *, minimum: int, maximum: int) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except Exception:
        return None
    if number < minimum:
        return minimum
    if number > maximum:
        return maximum
    return number


def _safe_reason_list(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        candidates = list(value)
    else:
        return []
    cleaned: list[str] = []
    for item in candidates:
        if item is None or isinstance(item, (bool, int, float)):
            continue
        text = str(item).strip()
        if not text or len(text) > 96 or not _ALLOWED_REASON_RE.fullmatch(text):
            continue
        if text not in cleaned:
            cleaned.append(text)
    return cleaned


__all__ = [
    "BODY_FREE_PUBLIC_SOURCE_LINEAGE_SCHEMA_VERSION",
    "BODY_FREE_PUBLIC_SOURCE_LINEAGE_SOURCE_PHASE",
    "assert_body_free_public_source_lineage_record",
    "build_body_free_public_source_lineage_record",
    "sanitize_body_free_public_source_lineage_record",
]
