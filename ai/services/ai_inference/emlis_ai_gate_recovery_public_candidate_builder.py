# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 public candidate builder for EmlisAI Gate Recovery.

The builder is the recovery boundary between a Gate Recovery plan and a public
``comment_text`` candidate.  It does not create a Gate Recovery material
surface, does not inspect/copy raw input into meta, and does not relax any
Reader/Grounding/Template/Display gate.  P6 connects the existing
low-information observation composer as an allowed public candidate source;
when no allowed source can be built, the builder still fails closed with
diagnostic blockers only.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Final
import json
import re

from emlis_ai_low_information_observation_composer import (
    assert_low_information_observation_composer_contract,
    compose_low_information_observation,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_EVENT,
)
from emlis_ai_types import ConversationComposerCandidate
from emlis_ai_gate_recovery_public_boundary import (
    assert_gate_recovery_public_boundary_decision,
    decide_gate_recovery_public_boundary,
    gate_recovery_public_display_allowed,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING,
    BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LIMITED_COMPOSER,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    CANDIDATE_SOURCE_KIND_NONE,
    CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
    PUBLIC_SURFACE_ROLE_BLOCKED_NO_PUBLIC_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
    RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    RECOVERY_CONTEXT_UNKNOWN,
)

PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.gate_recovery_public_candidate_builder.v1"
)
PUBLIC_RECOVERY_CANDIDATE_BUILDER_SOURCE_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P5_PublicCandidateBuilder"
)
GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY: Final = (
    "phase20_5_gate_recovery_public_candidate_builder"
)
RECOVERY_OBSERVATION_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.recovery_observation_plan.v1"

_SELECTION_KIND_NO_PUBLIC_CANDIDATE: Final = "no_public_candidate"
_SELECTION_KIND_BOUND_REPAIRED_ORIGINAL: Final = "bounded_repaired_original_candidate"
_SELECTION_KIND_LOW_INFORMATION: Final = "low_information_observation_composer"
_SELECTION_KIND_SELF_DENIAL_SAFE_STATE_ANSWER: Final = "self_denial_safe_state_answer"

LOW_INFORMATION_RECOVERY_SOURCE_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P6_LowInformationRecovery"
)
LOW_INFORMATION_RECOVERY_COMPOSER_MODEL: Final = "low_information_observation_composer_recovery"
LOW_INFORMATION_RECOVERY_GENERATION_METHOD: Final = (
    "low_information_observation_recovery_after_gate_recovery"
)
BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P7_BoundedOriginalCandidateRepair"
)
BOUNDED_ORIGINAL_REPAIR_COMPOSER_MODEL: Final = "bounded_repaired_original_candidate_v1"
BOUNDED_ORIGINAL_REPAIR_GENERATION_METHOD: Final = "bounded_repair_after_gate_recovery"
BOUNDED_ORIGINAL_REPAIR_RESPONSE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase20_7.bounded_original_repair.response.v1"
)
BOUNDED_ORIGINAL_REPAIR_META_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase20_7.bounded_original_candidate_repair.v1"
)
_LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES: Final[frozenset[str]] = frozenset(
    {"low_information", "limited_grounding"}
)

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
_RESULT_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version",
        "source_phase",
        "recovery_context",
        "candidate_available",
        "display_decision_available",
        "source_kind",
        "selection_kind",
        "decision_reasons",
        "blocked_reasons",
        "recovery_plan",
        "gate_recovery_public_boundary_decision",
        "candidate_lineage",
        "contract_flags",
    }
)


@dataclass(frozen=True)
class PublicRecoveryCandidateResult:
    """Result returned by the P5 public candidate builder.

    ``candidate`` may contain public body text because it is the object that the
    runtime may later send through existing gates.  ``as_meta`` intentionally
    never serializes that body.
    """

    candidate: Any | None = None
    display_decision: Any | None = None
    source_kind: str = CANDIDATE_SOURCE_KIND_NONE
    selection_kind: str = _SELECTION_KIND_NO_PUBLIC_CANDIDATE
    public_boundary: Mapping[str, Any] = field(default_factory=dict)
    blocked_reasons: Sequence[str] = field(default_factory=tuple)
    decision_reasons: Sequence[str] = field(default_factory=tuple)
    recovery_plan: Mapping[str, Any] = field(default_factory=dict)
    candidate_lineage: Mapping[str, Any] = field(default_factory=dict)
    recovery_context: str = RECOVERY_CONTEXT_UNKNOWN

    @property
    def candidate_available(self) -> bool:
        return self.candidate is not None

    @property
    def public_display_allowed(self) -> bool:
        return bool(gate_recovery_public_display_allowed(self.public_boundary))

    def as_meta(self) -> dict[str, Any]:
        boundary = dict(_as_mapping(self.public_boundary))
        if boundary:
            assert_gate_recovery_public_boundary_decision(boundary)
        meta = {
            "schema_version": PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION,
            "source_phase": PUBLIC_RECOVERY_CANDIDATE_BUILDER_SOURCE_PHASE,
            "recovery_context": _clean_identifier(self.recovery_context, max_length=96) or RECOVERY_CONTEXT_UNKNOWN,
            "candidate_available": bool(self.candidate_available),
            "display_decision_available": self.display_decision is not None,
            "source_kind": _clean_identifier(self.source_kind, max_length=96) or CANDIDATE_SOURCE_KIND_NONE,
            "selection_kind": _clean_identifier(self.selection_kind, max_length=96) or _SELECTION_KIND_NO_PUBLIC_CANDIDATE,
            "decision_reasons": list(_dedupe(self.decision_reasons)),
            "blocked_reasons": list(_dedupe(self.blocked_reasons)),
            "recovery_plan": _sanitize_recovery_plan(self.recovery_plan),
            "gate_recovery_public_boundary_decision": boundary,
            "candidate_lineage": _candidate_lineage_dict(self.candidate_lineage),
            "contract_flags": _contract_flags(),
        }
        assert_public_recovery_candidate_result_meta(meta)
        return meta


def build_public_candidate_after_gate_recovery(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    original_composer_candidate: Any | None,
    original_display_decision: Any,
    safety_triage_kind: str,
    safety_report: Any,
    recovery_plan: Mapping[str, Any] | None,
    trace_id: str,
    recovery_context: str = RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    bounded_repaired_original_candidate: Any | None = None,
    low_information_candidate: Any | None = None,
    self_denial_safe_state_answer_candidate: Any | None = None,
    composer_resolution: Mapping[str, Any] | None = None,
) -> PublicRecoveryCandidateResult:
    """Select a public candidate after Gate Recovery without building text.

    The function accepts already-built candidates from allowed generators.  It
    never falls back to Gate Recovery material-surface text.  ``current_input``
    is accepted to keep the P5/P6/P7 call contract stable, but no raw input or
    public body is serialized into the returned meta.
    """

    del safety_report  # P5/P6 keep safety material out of serialized meta.

    default_plan = _sanitize_recovery_plan(
        _default_recovery_plan(
            material_route=material_route,
            original_display_decision=original_display_decision,
            safety_triage_kind=safety_triage_kind,
            recovery_context=recovery_context,
            original_candidate_present=original_composer_candidate is not None,
        )
    )
    plan = _merge_recovery_plan_defaults(
        _sanitize_recovery_plan(recovery_plan or default_plan),
        default_plan,
    )
    bounded_original_build_reasons: list[str] = []
    if bounded_repaired_original_candidate is None and _should_attempt_bounded_original_repair(
        original_composer_candidate=original_composer_candidate,
        recovery_plan=plan,
    ):
        bounded_repaired_original_candidate, bounded_original_build_reasons = _build_bounded_original_repair_candidate(
            original_composer_candidate=original_composer_candidate,
            original_display_decision=original_display_decision,
            trace_id=trace_id,
            recovery_context=recovery_context,
        )

    low_information_build_reasons: list[str] = []
    if low_information_candidate is None and _should_attempt_low_information_recovery(
        material_route=material_route,
        recovery_plan=plan,
    ):
        low_information_candidate, low_information_build_reasons = _build_low_information_recovery_candidate(
            current_input=current_input,
            material_route=material_route,
            recovery_plan=plan,
            trace_id=trace_id,
        )

    original_source_kind = _candidate_source_kind(original_composer_candidate)
    if "self_denial_safe_state_answer" not in _clean(safety_triage_kind):
        self_denial_safe_state_answer_candidate = None
    candidates = _candidate_options(
        original_composer_candidate=original_composer_candidate,
        bounded_repaired_original_candidate=bounded_repaired_original_candidate,
        low_information_candidate=low_information_candidate,
        self_denial_safe_state_answer_candidate=self_denial_safe_state_answer_candidate,
        original_source_kind=original_source_kind,
    )

    blocked: list[str] = []
    reasons: list[str] = list(_dedupe(list(bounded_original_build_reasons) + list(low_information_build_reasons)))
    last_boundary: dict[str, Any] | None = None
    if (
        original_composer_candidate is not None
        and original_source_kind not in {
            CANDIDATE_SOURCE_KIND_NONE,
            CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
        }
    ):
        original_boundary = decide_gate_recovery_public_boundary(
            candidate=original_composer_candidate,
            composer_meta=_candidate_meta(original_composer_candidate),
            recovery_context=recovery_context,
            composer_resolution=composer_resolution,
        )
        last_boundary = dict(original_boundary)
        if not gate_recovery_public_display_allowed(original_boundary):
            blocked.extend(_dedupe(original_boundary.get("blockers") or ()))
            reasons.extend(_dedupe(original_boundary.get("decision_reasons") or ()))

    for source_kind, selection_kind, candidate in candidates:
        if candidate is None:
            continue
        if not _candidate_has_public_text(candidate):
            if BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN not in blocked:
                blocked.append(BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN)
            if "candidate_comment_text_missing" not in reasons:
                reasons.append("candidate_comment_text_missing")
            continue
        prepared = _candidate_with_public_lineage(
            candidate,
            source_kind=source_kind,
            selection_kind=selection_kind,
            original_candidate_present=original_composer_candidate is not None,
            original_source_kind=original_source_kind,
        )
        boundary = decide_gate_recovery_public_boundary(
            candidate=prepared,
            composer_meta=_candidate_meta(prepared),
            recovery_context=recovery_context,
            composer_resolution=composer_resolution,
        )
        last_boundary = dict(boundary)
        if gate_recovery_public_display_allowed(boundary):
            lineage = dict(_as_mapping(_candidate_meta(prepared).get("candidate_lineage")))
            return PublicRecoveryCandidateResult(
                candidate=prepared,
                display_decision=(
                    original_display_decision
                    if _display_decision_passed(original_display_decision)
                    else None
                ),
                source_kind=source_kind,
                selection_kind=selection_kind,
                public_boundary=boundary,
                blocked_reasons=(),
                decision_reasons=tuple(boundary.get("decision_reasons") or ()),
                recovery_plan=plan,
                candidate_lineage=lineage,
                recovery_context=recovery_context,
            )
        blocked.extend(_dedupe(boundary.get("blockers") or ()))
        reasons.extend(_dedupe(boundary.get("decision_reasons") or ()))

    no_candidate_meta = {
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_NONE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_BLOCKED_NO_PUBLIC_CANDIDATE,
        "public_surface_blockers": _dedupe(
            list(blocked)
            + [
                BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING,
                BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN,
            ]
        ),
        "candidate_lineage": {
            "original_candidate_present": bool(original_composer_candidate is not None),
            "original_candidate_source": original_source_kind,
            "recovery_plan_used": True,
            "diagnostic_surface_used": original_source_kind in {"gate_recovery_material_surface", "diagnostic_recovery_surface"},
            "public_candidate_rebuilt_after_recovery": False,
        },
    }
    boundary = decide_gate_recovery_public_boundary(
        candidate={"composer_meta": no_candidate_meta},
        composer_meta=no_candidate_meta,
        recovery_context=recovery_context,
        composer_resolution=composer_resolution,
    )
    if last_boundary is not None:
        # Preserve the last concrete boundary evidence in the diagnostic reasons
        # while still returning the canonical no-public-candidate boundary.
        reasons.extend(_dedupe(last_boundary.get("decision_reasons") or ()))
    blocked = list(_dedupe(list(blocked) + list(boundary.get("blockers") or ())))
    reasons = list(_dedupe(list(reasons) + list(boundary.get("decision_reasons") or ())))
    return PublicRecoveryCandidateResult(
        candidate=None,
        display_decision=None,
        source_kind=CANDIDATE_SOURCE_KIND_NONE,
        selection_kind=_SELECTION_KIND_NO_PUBLIC_CANDIDATE,
        public_boundary=boundary,
        blocked_reasons=blocked,
        decision_reasons=reasons,
        recovery_plan=plan,
        candidate_lineage=no_candidate_meta["candidate_lineage"],
        recovery_context=recovery_context,
    )


def assert_public_recovery_candidate_result_meta(value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError("public recovery candidate result meta must be a mapping")
    if set(value.keys()) != _RESULT_TOP_LEVEL_KEYS:
        raise ValueError("public recovery candidate result meta key set changed")
    if value.get("schema_version") != PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION:
        raise ValueError("unexpected public recovery candidate builder schema_version")
    if not isinstance(value.get("candidate_available"), bool):
        raise ValueError("candidate_available must be boolean")
    if not isinstance(value.get("display_decision_available"), bool):
        raise ValueError("display_decision_available must be boolean")
    if value.get("candidate_available") is True and value.get("source_kind") == CANDIDATE_SOURCE_KIND_NONE:
        raise ValueError("available public candidate must have a source_kind")
    if value.get("candidate_available") is False and not value.get("blocked_reasons"):
        raise ValueError("missing public candidate must carry blocked_reasons")
    boundary = _as_mapping(value.get("gate_recovery_public_boundary_decision"))
    if boundary:
        assert_gate_recovery_public_boundary_decision(boundary)
    flags = _as_mapping(value.get("contract_flags"))
    if set(flags.keys()) != set(_CONTRACT_FLAG_KEYS):
        raise ValueError("public recovery candidate builder contract flag key set changed")
    if any(flags.get(key) is not False for key in _CONTRACT_FLAG_KEYS):
        raise ValueError("public recovery candidate builder contract flags must all be false")
    if _contains_forbidden_text_key(value):
        raise ValueError("public recovery candidate builder meta must stay text-free")
    json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


def validate_public_recovery_candidate_result_meta(value: Mapping[str, Any] | None) -> list[str]:
    try:
        if not isinstance(value, Mapping):
            raise ValueError("public recovery candidate result meta must be a mapping")
        assert_public_recovery_candidate_result_meta(value)
    except ValueError as exc:
        return [str(exc)]
    return []


def dump_public_recovery_candidate_result_meta(value: Mapping[str, Any]) -> str:
    assert_public_recovery_candidate_result_meta(value)
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _should_attempt_bounded_original_repair(
    *,
    original_composer_candidate: Any | None,
    recovery_plan: Mapping[str, Any],
) -> bool:
    if original_composer_candidate is None:
        return False
    if not _candidate_has_public_text(original_composer_candidate):
        return False
    source_kind = _candidate_source_kind(original_composer_candidate)
    if source_kind in {
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        "diagnostic_recovery_surface",
    }:
        return False
    target = _clean_identifier(recovery_plan.get("target_public_candidate_source"), max_length=96)
    input_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    material_quality = _clean_identifier(input_summary.get("material_quality"), max_length=96)
    if (
        material_quality in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES
        and target != CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    ):
        return False
    fallback_order = set(_dedupe(recovery_plan.get("fallback_public_candidate_source_order") or []))
    return bool(
        target == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
        or CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE in fallback_order
        or target == ""
    )


def _build_bounded_original_repair_candidate(
    *,
    original_composer_candidate: Any | None,
    original_display_decision: Any,
    trace_id: str,
    recovery_context: str,
) -> tuple[ConversationComposerCandidate | None, list[str]]:
    if original_composer_candidate is None:
        return None, ["bounded_original_candidate_missing"]
    original_comment = _clean(getattr(original_composer_candidate, "comment_text", ""))
    if not original_comment:
        return None, ["bounded_original_candidate_comment_text_missing"]
    if _looks_like_gate_recovery_material_surface(original_composer_candidate, original_comment):
        return None, ["bounded_original_candidate_rejected_gate_recovery_material_surface"]

    original_source_kind = _candidate_source_kind(original_composer_candidate)
    repair_reasons = _bounded_original_repair_reasons(original_display_decision)
    repaired_comment, repair_operations = _bounded_original_repair_text(
        original_comment,
        repair_reasons=repair_reasons,
    )
    if not repaired_comment:
        return None, ["bounded_original_repair_comment_text_empty_after_repair"]

    original_model = _clean_identifier(getattr(original_composer_candidate, "composer_model", ""), max_length=128)
    original_generation_method = _clean_identifier(
        getattr(original_composer_candidate, "generation_method", ""),
        max_length=128,
    )
    original_composer_source = _clean_identifier(
        getattr(original_composer_candidate, "composer_source", ""),
        max_length=96,
    )
    original_meta = _body_free_mapping(_candidate_meta(original_composer_candidate))
    original_meta_keys = tuple(sorted(str(key) for key in original_meta.keys()))
    lineage = {
        "original_candidate_present": True,
        "original_candidate_source": original_source_kind or original_composer_source or CANDIDATE_SOURCE_KIND_NONE,
        "recovery_plan_used": True,
        "diagnostic_surface_used": False,
        "public_candidate_rebuilt_after_recovery": True,
    }
    meta = {
        "schema_version": BOUNDED_ORIGINAL_REPAIR_META_SCHEMA_VERSION,
        "source_phase": BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE,
        "recovery_context": _clean_identifier(recovery_context, max_length=96) or RECOVERY_CONTEXT_UNKNOWN,
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_model": BOUNDED_ORIGINAL_REPAIR_COMPOSER_MODEL,
        "generation_method": BOUNDED_ORIGINAL_REPAIR_GENERATION_METHOD,
        "phase20_7_bounded_original_candidate_repair_connected": True,
        "bounded_original_candidate_repair_ready": True,
        "bounded_original_candidate_repair_applied": True,
        "bounded_original_repair_attempt_count": 1,
        "bounded_original_repair_success_count": 1,
        "bounded_original_rerender_attempted": True,
        "bounded_original_rerender_attempt_limit": 1,
        "bounded_original_rerender_success": True,
        "repair_reasons": list(repair_reasons),
        "repair_operations": list(repair_operations),
        "original_candidate_source_kind": original_source_kind,
        "original_composer_source": original_composer_source,
        "original_composer_model": original_model,
        "original_generation_method": original_generation_method,
        "original_candidate_status": _clean_identifier(getattr(original_composer_candidate, "status", ""), max_length=96),
        "original_candidate_attempt_count": _safe_int(getattr(original_composer_candidate, "attempt_count", 0), 0),
        "original_candidate_meta_keys": list(original_meta_keys),
        "candidate_lineage": lineage,
        "meaning_added": False,
        "new_meaning_added": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "original_comment_text_body_included": False,
        "fixed_fallback_used": False,
        "fixed_sentence_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    return (
        ConversationComposerCandidate(
            comment_text=repaired_comment,
            composer_source="ai_generated",
            status="generated",
            ai_generated=True,
            trace_id=trace_id or _clean_identifier(getattr(original_composer_candidate, "trace_id", ""), max_length=128),
            attempt_count=1,
            used_evidence_span_ids=list(getattr(original_composer_candidate, "used_evidence_span_ids", []) or []),
            confidence=float(getattr(original_composer_candidate, "confidence", 0.0) or 0.0) or 0.76,
            rejection_reasons=[],
            request_schema_version=_clean_identifier(getattr(original_composer_candidate, "request_schema_version", ""), max_length=128) or "emlis.composer.request.v1",
            response_schema_version=BOUNDED_ORIGINAL_REPAIR_RESPONSE_SCHEMA_VERSION,
            fixed_string_renderer_used=False,
            composer_model=BOUNDED_ORIGINAL_REPAIR_COMPOSER_MODEL,
            generation_method=BOUNDED_ORIGINAL_REPAIR_GENERATION_METHOD,
            coverage_scope=_clean_identifier(getattr(original_composer_candidate, "coverage_scope", ""), max_length=128) or "current_input_bounded_original_repair",
            generation_scope=_clean_identifier(getattr(original_composer_candidate, "generation_scope", ""), max_length=128) or "current_input_only",
            composer_meta=meta,
            used_claim_ids=list(getattr(original_composer_candidate, "used_claim_ids", []) or []),
            used_relation_ids=list(getattr(original_composer_candidate, "used_relation_ids", []) or []),
        ),
        ["bounded_original_candidate_repair_built"],
    )


def _should_attempt_low_information_recovery(
    *,
    material_route: Any,
    recovery_plan: Mapping[str, Any],
) -> bool:
    route_meta = _material_route_meta(material_route)
    input_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    material_quality = _clean_identifier(
        input_summary.get("material_quality") or route_meta.get("material_quality") or getattr(material_route, "material_quality", ""),
        max_length=96,
    )
    if material_quality not in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES:
        return False
    target = _clean_identifier(recovery_plan.get("target_public_candidate_source"), max_length=96)
    fallback_order = set(_dedupe(recovery_plan.get("fallback_public_candidate_source_order") or []))
    return bool(
        target == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
        or CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER in fallback_order
        or material_quality in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES
    )


def _build_low_information_recovery_candidate(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    recovery_plan: Mapping[str, Any],
    trace_id: str,
) -> tuple[ConversationComposerCandidate | None, list[str]]:
    route_meta = dict(_material_route_meta(material_route))
    input_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    unknown_slots = list(
        _dedupe(
            input_summary.get("unknown_slots")
            or route_meta.get("unknown_slots")
            or getattr(material_route, "unknown_slots", None)
            or (UNKNOWN_SLOT_EVENT,)
        )
    ) or [UNKNOWN_SLOT_EVENT]
    visible_slots = list(
        _dedupe(
            input_summary.get("visible_material_slots")
            or route_meta.get("visible_material_slots")
            or getattr(material_route, "visible_material_slots", None)
        )
    )
    relation_ids = list(
        _dedupe(
            input_summary.get("relation_material_ids")
            or route_meta.get("relation_material_ids")
            or route_meta.get("generic_relation_material_ids")
            or getattr(material_route, "generic_relation_material_ids", None)
        )
    )
    eligibility_decision = {
        "status": OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        "eligibility_status": OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        "response_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        "material_quality": "low_information",
        "eligible_for_full_observation": False,
        "question_required": True,
        "unknown_slots": unknown_slots,
        "visible_material_slots": visible_slots,
        "generic_relation_material_ids": relation_ids,
        "plan": "free",
        "user_fact_allowed": False,
        "facts_used": [],
        "user_fact_may_promote_to_eligible": False,
        "origin_gate_recovery_plan": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    try:
        draft = compose_low_information_observation(
            current_input=current_input or {},
            eligibility_decision=eligibility_decision,
            input_material_bundle=route_meta or material_route,
            subscription_tier="free",
        )
        assert_low_information_observation_composer_contract(draft, current_input=current_input or {})
    except Exception as exc:  # pragma: no cover - fail-closed diagnostic path
        return None, [f"low_information_recovery_compose_failed:{type(exc).__name__}"]

    draft_meta = _body_free_mapping(draft.as_meta())
    draft_meta.update(
        {
            "source_phase": LOW_INFORMATION_RECOVERY_SOURCE_PHASE,
            "origin_gate_recovery_plan": True,
            "phase20_6_low_information_recovery_connected": True,
            "low_information_observation_composer_recovery_ready": True,
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "composer_model": LOW_INFORMATION_RECOVERY_COMPOSER_MODEL,
            "generation_method": LOW_INFORMATION_RECOVERY_GENERATION_METHOD,
            "recovery_context": _clean_identifier(recovery_plan.get("recovery_context"), max_length=96)
            or RECOVERY_CONTEXT_UNKNOWN,
            "material_quality_before_recovery": _clean_identifier(
                route_meta.get("material_quality") or input_summary.get("material_quality"),
                max_length=96,
            ),
            "visible_material_slots": visible_slots,
            "unknown_slots": unknown_slots,
            "relation_material_ids": relation_ids,
            "low_information_body_promoted_after_gate_recovery": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "safety_gate_relaxed": False,
            "fixed_fallback_used": False,
            "fixed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
    )
    return (
        ConversationComposerCandidate(
            comment_text=draft.body,
            composer_source="ai_generated",
            status="generated",
            ai_generated=True,
            trace_id=trace_id,
            attempt_count=1,
            used_evidence_span_ids=[],
            confidence=0.74,
            rejection_reasons=[],
            response_schema_version="cocolon.emlis.phase20_6.low_information_recovery.response.v1",
            fixed_string_renderer_used=False,
            composer_model=LOW_INFORMATION_RECOVERY_COMPOSER_MODEL,
            generation_method=LOW_INFORMATION_RECOVERY_GENERATION_METHOD,
            coverage_scope="current_input_low_information_recovery",
            generation_scope="current_input_only",
            composer_meta=draft_meta,
            used_claim_ids=[],
            used_relation_ids=relation_ids,
        ),
        ["low_information_observation_composer_recovery_built"],
    )


def _bounded_original_repair_reasons(original_display_decision: Any) -> tuple[str, ...]:
    reasons = list(getattr(original_display_decision, "rejection_reasons", []) or [])
    status = _clean_identifier(getattr(original_display_decision, "observation_status", ""), max_length=96)
    if status and status != "passed":
        reasons.append(f"display_status:{status}")
    return _dedupe(reasons) or ("display_gate_rejected",)


def _bounded_original_repair_text(text: str, *, repair_reasons: Sequence[str]) -> tuple[str, tuple[str, ...]]:
    body = re.sub(r"[ \t\u3000]+", " ", _clean(text))
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    operations: list[str] = ["normalize_spacing"] if body != _clean(text) else []
    sentence_like = [part for part in re.split(r"(?<=[。！？!?])\s*", body) if _clean(part)]
    should_shorten = bool(
        len(sentence_like) > 3
        and any(
            marker in _clean(reason)
            for reason in repair_reasons
            for marker in ("too_long", "surface", "template", "echo", "visible_surface")
        )
    )
    if should_shorten:
        body = "".join(sentence_like[:3]).strip()
        operations.append("bounded_sentence_limit_3")
    return body, tuple(_dedupe(operations or ["bounded_body_preserved"]))


def _looks_like_gate_recovery_material_surface(candidate: Any, comment_text: str) -> bool:
    source_kind = _candidate_source_kind(candidate)
    model = _clean_identifier(getattr(candidate, "composer_model", ""), max_length=128)
    generation_method = _clean_identifier(getattr(candidate, "generation_method", ""), max_length=128)
    if source_kind == CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE:
        return True
    if "gate_recovery" in model or "gate_recovery" in generation_method:
        return True
    body = _clean(comment_text)
    return bool(
        "今回の入力では" in body
        or "原因や結論までは決めず" in body
        or "誰かを良い悪いで決めず" in body
    )


def _candidate_options(
    *,
    original_composer_candidate: Any | None,
    bounded_repaired_original_candidate: Any | None,
    low_information_candidate: Any | None,
    self_denial_safe_state_answer_candidate: Any | None,
    original_source_kind: str,
) -> tuple[tuple[str, str, Any | None], ...]:
    repaired_original = bounded_repaired_original_candidate
    if repaired_original is None and original_source_kind in {
        CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
        CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    }:
        repaired_original = original_composer_candidate
    return (
        (
            CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            _SELECTION_KIND_BOUND_REPAIRED_ORIGINAL,
            repaired_original,
        ),
        (
            CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            _SELECTION_KIND_LOW_INFORMATION,
            low_information_candidate,
        ),
        (
            CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
            _SELECTION_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
            self_denial_safe_state_answer_candidate,
        ),
    )


def _candidate_with_public_lineage(
    candidate: Any,
    *,
    source_kind: str,
    selection_kind: str,
    original_candidate_present: bool,
    original_source_kind: str,
) -> Any:
    meta = _body_free_mapping(_candidate_meta(candidate))
    lineage = dict(_as_mapping(meta.get("candidate_lineage")))
    lineage.update(
        {
            "original_candidate_present": bool(original_candidate_present),
            "original_candidate_source": original_source_kind,
            "recovery_plan_used": True,
            "diagnostic_surface_used": False,
            "public_candidate_rebuilt_after_recovery": True,
        }
    )
    meta.update(
        {
            "candidate_source_kind": source_kind,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "candidate_lineage": lineage,
            "public_candidate_builder": {
                "schema_version": PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION,
                "selection_kind": selection_kind,
                "raw_input_included": False,
                "comment_text_body_included": False,
            },
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "safety_gate_relaxed": False,
        }
    )
    if hasattr(candidate, "composer_meta"):
        try:
            return replace(candidate, composer_meta=meta)
        except Exception:
            pass
    return candidate


def _candidate_source_kind(candidate: Any | None) -> str:
    meta = _candidate_meta(candidate)
    value = _clean_identifier(meta.get("candidate_source_kind"), max_length=96)
    if value:
        return value
    model = _clean_identifier(getattr(candidate, "composer_model", "") if candidate is not None else "", max_length=128)
    generation_method = _clean_identifier(getattr(candidate, "generation_method", "") if candidate is not None else "", max_length=128)
    composer_source = _clean_identifier(getattr(candidate, "composer_source", "") if candidate is not None else "", max_length=96)
    if ("gate_recovery" in model or "gate_recovery" in generation_method) and (
        "material_surface" in model or "material_surface" in generation_method or "material" in generation_method
    ):
        return CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE
    if "low_information" in model or "low_information" in generation_method or "low_information" in composer_source:
        return CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    if "self_denial_safe_state_answer" in model or "self_denial_safe_state_answer" in generation_method or "self_denial_safe_state_answer" in composer_source:
        return CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER
    if "bounded_repaired_original" in model or "bounded_repair" in generation_method:
        return CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    if "complete_self_repair" in model or "complete_self_repair" in generation_method:
        return CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE
    if "complete_initial" in model or "complete_initial" in generation_method or "complete_initial" in composer_source:
        return CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER
    if "limited_composer" in model or "limited_composer" in generation_method or "limited_composer" in composer_source:
        return CANDIDATE_SOURCE_KIND_LIMITED_COMPOSER
    if "self_repair" in model or "self_repair" in generation_method:
        return CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE
    return CANDIDATE_SOURCE_KIND_NONE


def _candidate_has_public_text(candidate: Any) -> bool:
    return bool(_clean(getattr(candidate, "comment_text", "")))


def _display_decision_passed(display_decision: Any) -> bool:
    return _clean(getattr(display_decision, "observation_status", "")) == "passed"


def _candidate_meta(candidate: Any | None) -> dict[str, Any]:
    if candidate is None:
        return {}
    if isinstance(candidate, Mapping):
        return dict(_as_mapping(candidate.get("composer_meta")))
    return dict(_as_mapping(getattr(candidate, "composer_meta", {})))


def _default_recovery_plan(
    *,
    material_route: Any,
    original_display_decision: Any,
    safety_triage_kind: str,
    recovery_context: str,
    original_candidate_present: bool,
) -> dict[str, Any]:
    route_meta = _material_route_meta(material_route)
    material_quality = _clean_identifier(
        _first(("material_quality", "eligibility_status", "status"), route_meta),
        max_length=96,
    )
    target = (
        CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
        if material_quality in {"low_information", "limited_grounding"}
        else CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER
        if "self_denial_safe_state_answer" in _clean(safety_triage_kind)
        else CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
        if original_candidate_present
        else CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    )
    return {
        "schema_version": RECOVERY_OBSERVATION_PLAN_SCHEMA_VERSION,
        "source_phase": PUBLIC_RECOVERY_CANDIDATE_BUILDER_SOURCE_PHASE,
        "recovery_context": recovery_context,
        "input_material_summary": {
            "material_quality": material_quality,
            "visible_material_slots": _dedupe(_first(("visible_material_slots",), route_meta)),
            "unknown_slots": _dedupe(_first(("unknown_slots",), route_meta)),
            "relation_material_ids": _dedupe(_first(("relation_material_ids", "generic_relation_material_ids"), route_meta)),
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "failed_gate_summary": {
            "display_status_before_recovery": _clean_identifier(getattr(original_display_decision, "observation_status", ""), max_length=96),
            "rejection_reasons": _dedupe(getattr(original_display_decision, "rejection_reasons", []) or []),
            "safety_triage_kind": _clean_identifier(safety_triage_kind, max_length=96),
        },
        "target_public_candidate_source": target,
        "fallback_public_candidate_source_order": [
            CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
        ],
        "diagnostic_surface_allowed": True,
        "diagnostic_surface_public_display_allowed": False,
        "public_candidate_required": True,
        "blockers_if_no_public_candidate": [BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING],
    }


def _merge_recovery_plan_defaults(plan: Mapping[str, Any], default_plan: Mapping[str, Any]) -> dict[str, Any]:
    merged = dict(_as_mapping(plan))
    defaults = _as_mapping(default_plan)
    for key in (
        "schema_version",
        "source_phase",
        "recovery_context",
        "target_public_candidate_source",
    ):
        if not merged.get(key):
            merged[key] = defaults.get(key)
    if not merged.get("fallback_public_candidate_source_order"):
        merged["fallback_public_candidate_source_order"] = list(
            defaults.get("fallback_public_candidate_source_order") or []
        )
    if not merged.get("blockers_if_no_public_candidate"):
        merged["blockers_if_no_public_candidate"] = list(
            defaults.get("blockers_if_no_public_candidate") or []
        )

    input_summary = dict(_as_mapping(merged.get("input_material_summary")))
    default_input_summary = _as_mapping(defaults.get("input_material_summary"))
    for key in ("material_quality", "visible_material_slots", "unknown_slots", "relation_material_ids"):
        if not input_summary.get(key):
            value = default_input_summary.get(key)
            input_summary[key] = list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else value
    input_summary["raw_input_included"] = False
    input_summary["comment_text_body_included"] = False
    merged["input_material_summary"] = input_summary

    failed_summary = dict(_as_mapping(merged.get("failed_gate_summary")))
    default_failed_summary = _as_mapping(defaults.get("failed_gate_summary"))
    for key in ("display_status_before_recovery", "rejection_reasons", "safety_triage_kind"):
        if not failed_summary.get(key):
            value = default_failed_summary.get(key)
            failed_summary[key] = list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) else value
    merged["failed_gate_summary"] = failed_summary

    merged["diagnostic_surface_allowed"] = bool(
        merged.get("diagnostic_surface_allowed", defaults.get("diagnostic_surface_allowed", True))
    )
    merged["diagnostic_surface_public_display_allowed"] = False
    merged["public_candidate_required"] = bool(
        merged.get("public_candidate_required", defaults.get("public_candidate_required", True))
    )
    return _sanitize_recovery_plan(merged)


def _sanitize_recovery_plan(plan: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _as_mapping(plan)
    input_summary = _as_mapping(source.get("input_material_summary"))
    failed_summary = _as_mapping(source.get("failed_gate_summary"))
    return {
        "schema_version": _clean_identifier(source.get("schema_version"), max_length=128) or RECOVERY_OBSERVATION_PLAN_SCHEMA_VERSION,
        "source_phase": _clean_identifier(source.get("source_phase"), max_length=128) or PUBLIC_RECOVERY_CANDIDATE_BUILDER_SOURCE_PHASE,
        "recovery_context": _clean_identifier(source.get("recovery_context"), max_length=96) or RECOVERY_CONTEXT_UNKNOWN,
        "input_material_summary": {
            "material_quality": _clean_identifier(input_summary.get("material_quality"), max_length=96),
            "visible_material_slots": _dedupe(input_summary.get("visible_material_slots") or []),
            "unknown_slots": _dedupe(input_summary.get("unknown_slots") or []),
            "relation_material_ids": _dedupe(input_summary.get("relation_material_ids") or []),
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "failed_gate_summary": {
            "display_status_before_recovery": _clean_identifier(failed_summary.get("display_status_before_recovery"), max_length=96),
            "rejection_reasons": _dedupe(failed_summary.get("rejection_reasons") or []),
            "safety_triage_kind": _clean_identifier(failed_summary.get("safety_triage_kind"), max_length=96),
        },
        "target_public_candidate_source": _clean_identifier(source.get("target_public_candidate_source"), max_length=96),
        "fallback_public_candidate_source_order": _dedupe(source.get("fallback_public_candidate_source_order") or []),
        "diagnostic_surface_allowed": bool(source.get("diagnostic_surface_allowed", True)),
        "diagnostic_surface_public_display_allowed": False,
        "public_candidate_required": bool(source.get("public_candidate_required", True)),
        "blockers_if_no_public_candidate": _dedupe(
            source.get("blockers_if_no_public_candidate") or [BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING]
        ),
    }


def _material_route_meta(material_route: Any) -> Mapping[str, Any]:
    if isinstance(material_route, Mapping):
        return material_route
    as_meta = getattr(material_route, "as_meta", None)
    if callable(as_meta):
        try:
            meta = as_meta()
            if isinstance(meta, Mapping):
                return meta
        except Exception:
            return {}
    meta = getattr(material_route, "meta", None)
    if isinstance(meta, Mapping):
        return meta
    return {}


def _candidate_lineage_dict(value: Mapping[str, Any]) -> dict[str, Any]:
    line = _as_mapping(value)
    return {
        "original_candidate_present": bool(line.get("original_candidate_present")),
        "original_candidate_source": _clean_identifier(line.get("original_candidate_source"), max_length=128),
        "recovery_plan_used": bool(line.get("recovery_plan_used")),
        "diagnostic_surface_used": bool(line.get("diagnostic_surface_used")),
        "public_candidate_rebuilt_after_recovery": bool(line.get("public_candidate_rebuilt_after_recovery")),
    }


def _contract_flags() -> dict[str, bool]:
    return {key: False for key in _CONTRACT_FLAG_KEYS}


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Sequence[Any] | Any | None) -> Sequence[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value.decode("utf-8", errors="ignore") if isinstance(value, (bytes, bytearray)) else value]
    if isinstance(value, Sequence):
        return value
    return [value]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_identifier(value: Any, *, max_length: int = 160) -> str:
    return _clean(value).replace(" ", "_")[:max_length]


def _dedupe(values: Sequence[Any] | Any | None) -> tuple[str, ...]:
    out: list[str] = []
    for value in _as_sequence(values):
        text = _clean_identifier(value, max_length=160)
        if text and text not in out:
            out.append(text)
    return tuple(out)


def _get_path(source: Mapping[str, Any], path: str) -> Any:
    current: Any = source
    for part in path.split("."):
        if not isinstance(current, Mapping):
            return None
        current = current.get(part)
    return current


def _first(paths: Sequence[str], source: Mapping[str, Any]) -> Any:
    for path in paths:
        value = _get_path(source, path)
        if value is not None and value != "":
            return value
    return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return int(default)


def _body_free_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, child in _as_mapping(value).items():
        if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
            continue
        if isinstance(child, Mapping):
            out[str(key)] = _body_free_mapping(child)
        elif isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
            out[str(key)] = [
                _body_free_mapping(item) if isinstance(item, Mapping) else item
                for item in child
            ]
        else:
            out[str(key)] = child
    return out


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
    "PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION",
    "PUBLIC_RECOVERY_CANDIDATE_BUILDER_SOURCE_PHASE",
    "GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY",
    "LOW_INFORMATION_RECOVERY_COMPOSER_MODEL",
    "LOW_INFORMATION_RECOVERY_GENERATION_METHOD",
    "LOW_INFORMATION_RECOVERY_SOURCE_PHASE",
    "BOUNDED_ORIGINAL_REPAIR_COMPOSER_MODEL",
    "BOUNDED_ORIGINAL_REPAIR_GENERATION_METHOD",
    "BOUNDED_ORIGINAL_REPAIR_META_SCHEMA_VERSION",
    "BOUNDED_ORIGINAL_REPAIR_RESPONSE_SCHEMA_VERSION",
    "BOUNDED_ORIGINAL_REPAIR_SOURCE_PHASE",
    "RECOVERY_OBSERVATION_PLAN_SCHEMA_VERSION",
    "PublicRecoveryCandidateResult",
    "assert_public_recovery_candidate_result_meta",
    "build_public_candidate_after_gate_recovery",
    "dump_public_recovery_candidate_result_meta",
    "validate_public_recovery_candidate_result_meta",
]
