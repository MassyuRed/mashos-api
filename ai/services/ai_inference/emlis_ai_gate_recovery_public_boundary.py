# -*- coding: utf-8 -*-
from __future__ import annotations

"""P2 public-boundary decision for EmlisAI Gate Recovery surfaces.

This module is meta-only.  It decides whether a Gate Recovery-related candidate
may be promoted to public ``comment_text`` without copying raw input or the
candidate body into the decision material.  Runtime wiring is intentionally left
for P3/P4.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final
import json

from emlis_ai_gate_recovery_public_constants import (
    ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS,
    BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION,
    BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE,
    BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN,
    BLOCKER_RECOVERY_SURFACE_SOURCE_LINEAGE_MISSING,
    CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_NONE,
    FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS,
    GATE_RECOVERY_LOOP_SOURCE_PHASE,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHODS,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    GATE_RECOVERY_MATERIAL_SURFACE_MODELS,
    GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    POST_FINAL_GATE_RECOVERY_SOURCE_PHASE,
    PUBLIC_SURFACE_ROLE_BLOCKED_NO_PUBLIC_CANDIDATE,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    PUBLIC_SURFACE_ROLE_RECOVERY_PLAN_ONLY,
    RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    RECOVERY_CONTEXT_UNKNOWN,
    SURFACE_GENERATION_METHOD_MATERIAL_BOUND_GENERIC_SURFACE,
    gate_recovery_material_surface_blockers_for_model,
)

REJECTION_REASON_DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED: Final = (
    "default_limited_composer_feature_disabled"
)
DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED: Final = REJECTION_REASON_DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED
MATERIAL_BOUND_GENERIC_SURFACE_GENERATION_METHOD: Final = SURFACE_GENERATION_METHOD_MATERIAL_BOUND_GENERIC_SURFACE
GATE_RECOVERY_PUBLIC_BOUNDARY_SOURCE_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P2_PublicBoundaryDecision"
)
GATE_RECOVERY_SURFACE_BINDING_META_KEY: Final = "phase20_15_gate_recovery_surface_binding"

_CONTRACT_FLAG_KEYS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "response_shape_changed",
    "public_response_key_added",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "safety_gate_relaxed",
    "raw_input_included",
    "comment_text_body_included",
)
_ALLOWED_RECOVERY_CONTEXTS: Final[frozenset[str]] = frozenset(
    {
        RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
        RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
        RECOVERY_CONTEXT_UNKNOWN,
    }
)
_FORBIDDEN_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "body",
        "text",
    }
)
_DECISION_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "recovery_context",
        "candidate_source_kind",
        "composer_model",
        "generation_method",
        "public_surface_role",
        "public_display_allowed",
        "decision_reasons",
        "blockers",
        "candidate_lineage",
        "contract_flags",
    }
)


@dataclass(frozen=True)
class GateRecoveryPublicBoundaryDecision:
    source_phase: str = GATE_RECOVERY_PUBLIC_BOUNDARY_SOURCE_PHASE
    recovery_context: str = RECOVERY_CONTEXT_UNKNOWN
    candidate_source_kind: str = CANDIDATE_SOURCE_KIND_NONE
    composer_model: str = ""
    generation_method: str = ""
    public_surface_role: str = PUBLIC_SURFACE_ROLE_BLOCKED_NO_PUBLIC_CANDIDATE
    public_display_allowed: bool = False
    decision_reasons: Sequence[str] = field(default_factory=tuple)
    blockers: Sequence[str] = field(default_factory=tuple)
    candidate_lineage: Mapping[str, Any] = field(default_factory=dict)
    contract_flags: Mapping[str, bool] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION,
            "source_phase": _clean_identifier(self.source_phase, max_length=96),
            "recovery_context": _normalize_recovery_context(self.recovery_context),
            "candidate_source_kind": _clean_identifier(self.candidate_source_kind, max_length=96),
            "composer_model": _clean_identifier(self.composer_model, max_length=128),
            "generation_method": _clean_identifier(self.generation_method, max_length=128),
            "public_surface_role": _clean_identifier(self.public_surface_role, max_length=96),
            "public_display_allowed": bool(self.public_display_allowed),
            "decision_reasons": list(_dedupe(self.decision_reasons)),
            "blockers": list(_dedupe(self.blockers)),
            "candidate_lineage": _candidate_lineage_dict(self.candidate_lineage),
            "contract_flags": _contract_flags(self.contract_flags),
        }


def decide_gate_recovery_public_boundary(
    *,
    candidate: Any,
    composer_meta: Mapping[str, Any] | None = None,
    recovery_context: str = RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    composer_resolution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a body-free public-boundary decision for a recovery candidate."""

    meta = _candidate_meta(candidate, composer_meta)
    resolution = _as_mapping(composer_resolution)
    candidate_map = _as_mapping(candidate)
    binding = _as_mapping(
        _first(
            (
                GATE_RECOVERY_SURFACE_BINDING_META_KEY,
                "gate_recovery_surface_binding",
                "surface_origin",
            ),
            meta,
            candidate_map,
        )
    )

    composer_model = _clean_identifier(
        _candidate_attr(candidate, "composer_model")
        or _first(("composer_model", "surface_origin.composer_model"), meta, binding, candidate_map),
        max_length=128,
    )
    generation_method = _clean_identifier(
        _candidate_attr(candidate, "generation_method")
        or _first(("generation_method", "surface_generation_method", "surface_origin.generation_method"), meta, binding, candidate_map),
        max_length=128,
    )
    source_phase = _clean_identifier(
        _first(("source_phase", "surface_origin.source_phase"), meta, binding, candidate_map),
        max_length=96,
    )
    normalized_context = _normalize_recovery_context(
        recovery_context or _first(("recovery_context", "surface_origin.recovery_context"), meta, binding, candidate_map)
    )
    explicit_source_kind = _clean_identifier(
        _first(("candidate_source_kind", "surface_origin.candidate_source_kind"), meta, binding, candidate_map),
        max_length=96,
    )
    explicit_role = _clean_identifier(
        _first(("public_surface_role", "surface_origin.public_surface_role"), meta, binding, candidate_map),
        max_length=96,
    )
    surface_generation_method = _clean_identifier(
        _first(("surface_generation_method", "surface_origin.surface_generation_method"), meta, binding, candidate_map),
        max_length=128,
    )
    candidate_source_kind = _infer_candidate_source_kind(
        explicit_source_kind=explicit_source_kind,
        composer_model=composer_model,
        generation_method=generation_method,
        source_phase=source_phase,
        public_surface_role=explicit_role,
    )
    public_surface_role = _infer_public_surface_role(
        explicit_role=explicit_role,
        candidate_source_kind=candidate_source_kind,
    )
    public_candidate_rebuilt = bool(
        _first(
            (
                "candidate_lineage.public_candidate_rebuilt_after_recovery",
                "public_candidate_rebuilt_after_recovery",
                "surface_origin.public_candidate_rebuilt_after_recovery",
            ),
            meta,
            binding,
            candidate_map,
        )
        is True
    )

    blockers: list[str] = list(_dedupe(_first(("public_surface_blockers",), meta, binding)))
    reasons: list[str] = []

    def block(blocker: str, reason: str) -> None:
        b = _clean_identifier(blocker, max_length=160)
        r = _clean_identifier(reason, max_length=128)
        if b and b not in blockers:
            blockers.append(b)
        if r and r not in reasons:
            reasons.append(r)

    post_final = _is_post_final(
        composer_model=composer_model,
        generation_method=generation_method,
        source_phase=source_phase,
        recovery_context=normalized_context,
    )
    recovery_material_detected = bool(
        composer_model in GATE_RECOVERY_MATERIAL_SURFACE_MODELS
        or generation_method in GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHODS
        or source_phase in {GATE_RECOVERY_LOOP_SOURCE_PHASE, POST_FINAL_GATE_RECOVERY_SOURCE_PHASE}
        or candidate_source_kind in {
            CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
            CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
        }
    )
    if recovery_material_detected:
        for blocker in gate_recovery_material_surface_blockers_for_model(composer_model):
            block(blocker, "gate_recovery_material_surface_model_blocked")
        block(
            BLOCKER_POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK if post_final else BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
            "gate_recovery_material_surface_lineage_blocked",
        )

    if public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY:
        block(BLOCKER_GATE_RECOVERY_DIAGNOSTIC_SURFACE_PROMOTED_TO_PUBLIC, "diagnostic_recovery_surface_role_blocked")
    elif public_surface_role in {PUBLIC_SURFACE_ROLE_RECOVERY_PLAN_ONLY, PUBLIC_SURFACE_ROLE_BLOCKED_NO_PUBLIC_CANDIDATE}:
        block(BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN, "public_surface_role_not_public_observation")

    if surface_generation_method == SURFACE_GENERATION_METHOD_MATERIAL_BOUND_GENERIC_SURFACE and not public_candidate_rebuilt:
        block(BLOCKER_RECOVERY_SURFACE_SOURCE_LINEAGE_MISSING, "material_bound_generic_surface_without_public_rebuild")

    if candidate_source_kind in FORBIDDEN_PUBLIC_CANDIDATE_SOURCE_KINDS:
        if candidate_source_kind == CANDIDATE_SOURCE_KIND_NONE:
            block(BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN, "public_candidate_source_missing")
        else:
            reasons.append("candidate_source_kind_forbidden_for_public_display")
    elif candidate_source_kind not in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS:
        block(BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN, "public_candidate_source_unknown")

    if _composer_disabled(resolution) and recovery_material_detected:
        block(BLOCKER_COMPOSER_DISABLED_RECOVERY_SURFACE_PUBLIC_SUBSTITUTION, "composer_disabled_recovery_surface_substitution")

    if recovery_material_detected and _template_false_negative_risk(meta, binding):
        block(BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE, "gate_recovery_template_meta_false_negative")

    if _contains_forbidden_text_key(meta) or _contains_forbidden_text_key(resolution):
        block(BLOCKER_GATE_RECOVERY_TEMPLATE_META_FALSE_NEGATIVE, "text_payload_key_detected_in_boundary_material")

    blockers_tuple = _dedupe(blockers)
    public_display_allowed = bool(
        not blockers_tuple
        and candidate_source_kind in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS
        and public_surface_role == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    )
    if public_display_allowed:
        reasons.append("allowed_public_observation_source")
    elif not blockers_tuple:
        block(BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN, "public_candidate_source_not_open")
        blockers_tuple = _dedupe(blockers)

    lineage = {
        "original_candidate_present": bool(_first(("candidate_lineage.original_candidate_present", "original_candidate_present"), meta, binding, candidate_map) is True),
        "original_candidate_source": _clean_identifier(_first(("candidate_lineage.original_candidate_source", "original_candidate_source"), meta, binding, candidate_map), max_length=128),
        "recovery_plan_used": bool(_first(("candidate_lineage.recovery_plan_used", "recovery_plan_used"), meta, binding, candidate_map) is True or recovery_material_detected),
        "diagnostic_surface_used": bool(public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY or recovery_material_detected),
        "public_candidate_rebuilt_after_recovery": bool(public_candidate_rebuilt),
    }
    decision = GateRecoveryPublicBoundaryDecision(
        source_phase=source_phase or GATE_RECOVERY_PUBLIC_BOUNDARY_SOURCE_PHASE,
        recovery_context=normalized_context,
        candidate_source_kind=candidate_source_kind,
        composer_model=composer_model,
        generation_method=generation_method,
        public_surface_role=public_surface_role,
        public_display_allowed=public_display_allowed,
        decision_reasons=_dedupe(reasons),
        blockers=blockers_tuple,
        candidate_lineage=lineage,
        contract_flags=_contract_flags(),
    ).as_dict()
    assert_gate_recovery_public_boundary_decision(decision)
    return decision


def gate_recovery_public_display_allowed(decision: Mapping[str, Any] | None) -> bool:
    return bool(isinstance(decision, Mapping) and decision.get("public_display_allowed") is True)


def assert_gate_recovery_public_boundary_decision(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("gate recovery public boundary decision must be a mapping")
    if set(value.keys()) != _DECISION_TOP_LEVEL_KEYS:
        raise ValueError("gate recovery public boundary decision key set changed")
    if value.get("schema_version") != GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("unexpected gate recovery public boundary schema_version")
    if value.get("recovery_context") not in _ALLOWED_RECOVERY_CONTEXTS:
        raise ValueError("unsupported gate recovery public boundary recovery_context")
    if not isinstance(value.get("public_display_allowed"), bool):
        raise ValueError("public_display_allowed must be boolean")
    if not isinstance(value.get("decision_reasons"), list):
        raise ValueError("decision_reasons must be list")
    if not isinstance(value.get("blockers"), list):
        raise ValueError("blockers must be list")
    if bool(value.get("public_display_allowed")) and value.get("blockers"):
        raise ValueError("allowed gate recovery public boundary decision cannot have blockers")
    if not bool(value.get("public_display_allowed")) and not value.get("blockers"):
        raise ValueError("blocked gate recovery public boundary decision must have blockers")
    lineage = _as_mapping(value.get("candidate_lineage"))
    for key in (
        "original_candidate_present",
        "original_candidate_source",
        "recovery_plan_used",
        "diagnostic_surface_used",
        "public_candidate_rebuilt_after_recovery",
    ):
        if key not in lineage:
            raise ValueError("gate recovery public boundary candidate_lineage key set changed")
    contract_flags = _as_mapping(value.get("contract_flags"))
    if set(contract_flags.keys()) != set(_CONTRACT_FLAG_KEYS):
        raise ValueError("gate recovery public boundary contract flag key set changed")
    if any(contract_flags.get(key) is not False for key in _CONTRACT_FLAG_KEYS):
        raise ValueError("gate recovery public boundary contract flags must all be false")
    if _contains_forbidden_text_key(value):
        raise ValueError("gate recovery public boundary decision must stay text-free")
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def assert_gate_recovery_public_boundary_decision_meta(value: Mapping[str, Any]) -> None:
    assert_gate_recovery_public_boundary_decision(value)


def validate_gate_recovery_public_boundary_decision(decision: Mapping[str, Any] | None) -> list[str]:
    try:
        if not isinstance(decision, Mapping):
            raise ValueError("gate recovery public boundary decision must be a mapping")
        assert_gate_recovery_public_boundary_decision(decision)
    except ValueError as exc:
        return [str(exc)]
    return []


def dump_gate_recovery_public_boundary_decision(decision: Mapping[str, Any]) -> str:
    assert_gate_recovery_public_boundary_decision(decision)
    return json.dumps(dict(decision), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_identifier(value: Any, *, max_length: int = 160) -> str:
    return _clean(value).replace(" ", "_")[:max_length]


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value.decode("utf-8", errors="ignore") if isinstance(value, (bytes, bytearray)) else value]
    if isinstance(value, Sequence):
        return value
    return [value]


def _dedupe(values: Sequence[Any] | Any | None) -> tuple[str, ...]:
    out: list[str] = []
    for value in _as_sequence(values):
        text = _clean_identifier(value, max_length=160)
        if text and text not in out:
            out.append(text)
    return tuple(out)


def _candidate_attr(candidate: Any, key: str) -> Any:
    if isinstance(candidate, Mapping):
        return candidate.get(key)
    return getattr(candidate, key, None) if candidate is not None else None


def _candidate_meta(candidate: Any, explicit_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta: dict[str, Any] = {}
    meta.update(dict(_as_mapping(_candidate_attr(candidate, "composer_meta"))))
    if isinstance(explicit_meta, Mapping):
        meta.update(dict(explicit_meta))
    return meta


def _candidate_lineage_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    line = _as_mapping(value)
    return {
        "original_candidate_present": bool(line.get("original_candidate_present")),
        "original_candidate_source": _clean_identifier(line.get("original_candidate_source"), max_length=128),
        "recovery_plan_used": bool(line.get("recovery_plan_used")),
        "diagnostic_surface_used": bool(line.get("diagnostic_surface_used")),
        "public_candidate_rebuilt_after_recovery": bool(line.get("public_candidate_rebuilt_after_recovery")),
    }


def _contract_flags(flags: Mapping[str, Any] | None = None) -> dict[str, bool]:
    f = _as_mapping(flags)
    return {key: bool(f.get(key, False)) for key in _CONTRACT_FLAG_KEYS}


def _get_path(source: Mapping[str, Any], path: str) -> Any:
    current: Any = source
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _first(paths: Sequence[str], *sources: Mapping[str, Any]) -> Any:
    for source in sources:
        for path in paths:
            value = _get_path(source, path)
            if value is not None and value != "":
                return value
    return None


def _normalize_recovery_context(value: Any) -> str:
    text = _clean(value) or RECOVERY_CONTEXT_UNKNOWN
    return text if text in _ALLOWED_RECOVERY_CONTEXTS else RECOVERY_CONTEXT_UNKNOWN


def _infer_candidate_source_kind(
    *,
    explicit_source_kind: str,
    composer_model: str,
    generation_method: str,
    source_phase: str,
    public_surface_role: str,
) -> str:
    if explicit_source_kind:
        return explicit_source_kind
    if (
        composer_model in GATE_RECOVERY_MATERIAL_SURFACE_MODELS
        or generation_method in GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHODS
        or source_phase in {GATE_RECOVERY_LOOP_SOURCE_PHASE, POST_FINAL_GATE_RECOVERY_SOURCE_PHASE}
        or public_surface_role == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    ):
        return CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    return CANDIDATE_SOURCE_KIND_NONE


def _infer_public_surface_role(*, explicit_role: str, candidate_source_kind: str) -> str:
    if explicit_role:
        return explicit_role
    if candidate_source_kind in ALLOWED_PUBLIC_CANDIDATE_SOURCE_KINDS:
        return PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    if candidate_source_kind in {
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    }:
        return PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    return PUBLIC_SURFACE_ROLE_BLOCKED_NO_PUBLIC_CANDIDATE


def _is_post_final(*, composer_model: str, generation_method: str, source_phase: str, recovery_context: str) -> bool:
    return bool(
        composer_model == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_MODEL
        or generation_method == POST_FINAL_GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD
        or source_phase == POST_FINAL_GATE_RECOVERY_SOURCE_PHASE
        or recovery_context == RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE
    )


def _composer_disabled(composer_resolution: Mapping[str, Any]) -> bool:
    return REJECTION_REASON_DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED in _dedupe(
        _first(("rejection_reasons", "composer_resolution.rejection_reasons"), composer_resolution)
    )


def _template_false_negative_risk(meta: Mapping[str, Any], binding: Mapping[str, Any]) -> bool:
    signature = _as_mapping(meta.get("surface_quality_signature"))
    return any(
        _first((key,), signature, meta, binding) is False
        for key in ("surface_template_major", "template_major")
    )


def _contains_forbidden_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_key(child) for child in value)
    return False


__all__ = [
    "DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED",
    "GATE_RECOVERY_LOOP_SOURCE_PHASE",
    "GATE_RECOVERY_PUBLIC_BOUNDARY_SOURCE_PHASE",
    "MATERIAL_BOUND_GENERIC_SURFACE_GENERATION_METHOD",
    "POST_FINAL_GATE_RECOVERY_SOURCE_PHASE",
    "RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE",
    "RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE",
    "RECOVERY_CONTEXT_UNKNOWN",
    "REJECTION_REASON_DEFAULT_LIMITED_COMPOSER_FEATURE_DISABLED",
    "SURFACE_GENERATION_METHOD_MATERIAL_BOUND_GENERIC_SURFACE",
    "GateRecoveryPublicBoundaryDecision",
    "assert_gate_recovery_public_boundary_decision",
    "assert_gate_recovery_public_boundary_decision_meta",
    "decide_gate_recovery_public_boundary",
    "dump_gate_recovery_public_boundary_decision",
    "gate_recovery_public_display_allowed",
    "validate_gate_recovery_public_boundary_decision",
]
