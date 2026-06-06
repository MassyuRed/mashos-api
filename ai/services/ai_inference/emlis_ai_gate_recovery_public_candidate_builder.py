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
from emlis_ai_complete_initial_surface_availability import (
    complete_initial_surface_availability_public_summary,
)
from emlis_ai_complete_initial_surface_recomposition import (
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SOURCE_PHASE,
    build_complete_initial_surface_recomposition_candidate,
    complete_initial_surface_recomposition_public_summary,
    should_attempt_complete_initial_surface_recomposition,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_COMPOSER_MODEL,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_GENERATION_METHOD,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SCHEMA_VERSION,
    LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_SOURCE_PHASE,
    build_labelled_two_stage_surface_recomposition_candidate,
    labelled_two_stage_surface_recomposition_public_summary,
    should_attempt_labelled_two_stage_surface_recomposition,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    public_surface_requirement_public_summary,
    resolve_public_surface_requirement,
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
    BLOCKER_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE_MISSING,
    BLOCKER_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE_MISSING,
    BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED,
    BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING,
    BLOCKER_PUBLIC_CANDIDATE_SOURCE_NOT_OPEN,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LIMITED_COMPOSER,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    CANDIDATE_SOURCE_KIND_NONE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
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
_SELECTION_KIND_NORMAL_OBSERVATION_REBUILD: Final = "normal_observation_rebuild_candidate"
_SELECTION_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION: Final = (
    "complete_initial_surface_recomposition_candidate"
)
_SELECTION_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION: Final = (
    "labelled_two_stage_surface_recomposition_candidate"
)

NORMAL_OBSERVATION_REBUILD_SOURCE_PHASE: Final = (
    "GateRecoveryPublicSurfaceLeakRepair_P8_NormalObservationRebuild"
)
NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL: Final = "normal_observation_rebuild_candidate_v1"
NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD: Final = (
    "normal_observation_rebuild_after_surface_gate_failure"
)
NORMAL_OBSERVATION_REBUILD_META_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase20_8.normal_observation_rebuild.meta.v1"
)
NORMAL_OBSERVATION_REBUILD_RESPONSE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.phase20_8.normal_observation_rebuild.response.v1"
)

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
_NORMAL_REBUILD_REPAIRABLE_REASON_FAMILIES: Final[frozenset[str]] = frozenset(
    {"surface_grammar", "relation_skeleton", "visible_surface", "runtime_surface", "koto_splice"}
)
_NORMAL_REBUILD_NON_REPAIRABLE_REASON_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "safety",
        "source_unavailable",
        "composer_disabled",
        "phase_not_complete",
        "grounding_unsupported",
        "reader_failure",
        "template_echo_major",
        "public_boundary_blocked",
        "infrastructure_error",
    }
)
_NORMAL_REBUILD_REASON_FAMILY_MARKERS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    (
        "surface_grammar",
        (
            "surface_grammar",
            "malformed_phrase",
            "malformed_nominalization",
            "candidate_blocked_surface_grammar",
        ),
    ),
    (
        "relation_skeleton",
        (
            "relation_skeleton",
            "surface_relation_skeleton",
            "candidate_blocked_relation_skeleton",
        ),
    ),
    (
        "visible_surface",
        (
            "visible_surface",
            "visible_surface_acceptance_gate",
            "rerender_surface",
        ),
    ),
    (
        "runtime_surface",
        (
            "runtime_surface",
            "runtime_surface_pre_return_gate",
            "rerender_shallow",
        ),
    ),
    ("koto_splice", ("koto_splice",)),
)
_NORMAL_REBUILD_NON_REPAIRABLE_REASON_MARKERS: Final[tuple[tuple[str, tuple[str, ...]], ...]] = (
    ("safety", ("safety_blocked", "requires_block", "emergency")),
    ("source_unavailable", ("source_unavailable", "composer_source_unavailable")),
    ("composer_disabled", ("composer_disabled", "default_limited_composer_feature_disabled")),
    ("phase_not_complete", ("phase_not_complete",)),
    ("grounding_unsupported", ("grounding_unsupported",)),
    ("reader_failure", ("reader_failure", "reader_unavailable")),
    ("template_echo_major", ("template_echo_major",)),
    ("public_boundary_blocked", ("public_boundary_blocked",)),
    ("infrastructure_error", ("infrastructure_error", "timeout", "exception")),
)

_NORMAL_REBUILD_FORBIDDEN_SURFACE_FRAGMENTS: Final[tuple[str, ...]] = (
    "同じ流れ",
    "同じ場所",
    "別々の向き",
    "片方だけに減らさず",
    "片方だけに寄らず",
    "重なりを保っています",
    "一方向には決まりきっていません",
    "状態が一色ではありません",
    "今見えている範囲は一つの要素だけではありません",
    "一つの要素だけではありません",
    "重なりとして並んで",
    "網羅",
    "要素",
    "範囲",
    "原因や結論までは決めず",
    "誰かを良い悪いで決めず",
    "Emlisから：",
    "見えたこと：",
)
_NORMAL_REBUILD_GATE_RECOVERY_MATERIAL_FRAGMENTS: Final[tuple[str, ...]] = (
    "今回の入力では",
    "原因や結論までは",
    "誰かを良い悪いで",
    "gate_recovery",
    "Gate Recovery",
)
_NORMAL_REBUILD_ANALYTIC_REGISTER_FRAGMENTS: Final[tuple[str, ...]] = (
    "関係骨格",
    "分類",
    "診断",
    "傾向",
    "人格",
    "処方",
    "原因化",
    "分析",
)
_NORMAL_REBUILD_ALLOWED_SCOPE_MARKERS: Final[tuple[str, ...]] = ("この記録では", "今回の記録では", "この入力では", "今の入力では")
_NORMAL_REBUILD_MAX_SENTENCES: Final = 3
_NORMAL_REBUILD_MIN_SENTENCES: Final = 2
_NORMAL_REBUILD_ATTEMPT_LIMIT: Final = 1

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
    normal_observation_rebuild_candidate: Any | None = None,
    complete_initial_surface_recomposition_candidate: Any | None = None,
    labelled_two_stage_surface_recomposition_candidate: Any | None = None,
    complete_initial_surface_availability_summary: Mapping[str, Any] | None = None,
    composer_resolution: Mapping[str, Any] | None = None,
) -> PublicRecoveryCandidateResult:
    """Select or build a public candidate after Gate Recovery.

    The function accepts already-built candidates from allowed generators and,
    for normal-observation surface failures, can build a body-free-meta rebuild
    candidate.  It never falls back to Gate Recovery material-surface text, and
    no raw input or public body is serialized into the returned meta.
    """

    safety_requires_block = bool(getattr(safety_report, "requires_block", False))

    surface_requirement = _resolve_surface_requirement_for_recovery_plan(
        current_input=current_input,
        material_route=material_route,
        original_composer_candidate=original_composer_candidate,
        original_display_decision=original_display_decision,
        safety_triage_kind=safety_triage_kind,
        recovery_context=recovery_context,
    )
    availability_requirement_family = _clean_identifier(
        _as_mapping(complete_initial_surface_availability_summary).get("surface_requirement_family"),
        max_length=96,
    )
    if (
        availability_requirement_family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
        and not _surface_requirement_requires_labelled_two_stage(surface_requirement)
    ):
        decision_sources = list(_dedupe(_as_mapping(surface_requirement).get("decision_sources") or []))
        decision_sources.append("complete_initial_surface_availability")
        surface_requirement = public_surface_requirement_public_summary(
            {
                **_as_mapping(surface_requirement),
                "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
                "two_stage_required": True,
                "plain_state_answer_allowed": False,
                "low_information_allowed": False,
                "decision_sources": _dedupe(decision_sources),
                "raw_input_included": False,
                "comment_text_body_included": False,
            }
        )
    default_plan = _sanitize_recovery_plan(
        _default_recovery_plan(
            material_route=material_route,
            original_display_decision=original_display_decision,
            safety_triage_kind=safety_triage_kind,
            recovery_context=recovery_context,
            original_candidate_present=original_composer_candidate is not None,
            surface_requirement=surface_requirement,
            complete_initial_surface_availability_summary=complete_initial_surface_availability_summary,
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

    labelled_two_stage_recomposition_build_reasons: list[str] = []
    if labelled_two_stage_surface_recomposition_candidate is None and should_attempt_labelled_two_stage_surface_recomposition(
        current_input=current_input,
        material_route=material_route,
        surface_requirement=plan.get("surface_requirement"),
        original_composer_candidate=original_composer_candidate,
        original_display_decision=original_display_decision,
        safety_requires_block=safety_requires_block,
    ):
        (
            labelled_two_stage_surface_recomposition_candidate,
            labelled_two_stage_recomposition_build_reasons,
        ) = build_labelled_two_stage_surface_recomposition_candidate(
            current_input=current_input,
            material_route=material_route,
            surface_requirement=plan.get("surface_requirement"),
            original_composer_candidate=original_composer_candidate,
            original_display_decision=original_display_decision,
            trace_id=trace_id,
            recovery_context=recovery_context,
            safety_requires_block=safety_requires_block,
        )

    complete_initial_recomposition_build_reasons: list[str] = []
    if complete_initial_surface_recomposition_candidate is None and should_attempt_complete_initial_surface_recomposition(
        availability_summary=complete_initial_surface_availability_summary,
        surface_requirement=plan.get("surface_requirement"),
        material_route=material_route,
        safety_requires_block=safety_requires_block,
    ):
        (
            complete_initial_surface_recomposition_candidate,
            complete_initial_recomposition_build_reasons,
        ) = build_complete_initial_surface_recomposition_candidate(
            current_input=current_input,
            material_route=material_route,
            surface_requirement=plan.get("surface_requirement"),
            availability_summary=complete_initial_surface_availability_summary,
            trace_id=trace_id,
            recovery_context=recovery_context,
            safety_requires_block=safety_requires_block,
        )

    normal_rebuild_build_reasons: list[str] = []
    if normal_observation_rebuild_candidate is None and _should_attempt_normal_observation_rebuild(
        original_composer_candidate=original_composer_candidate,
        original_display_decision=original_display_decision,
        material_route=material_route,
        recovery_plan=plan,
        safety_triage_kind=safety_triage_kind,
        safety_requires_block=safety_requires_block,
    ):
        normal_observation_rebuild_candidate, normal_rebuild_build_reasons = _build_normal_observation_rebuild_candidate(
            current_input=current_input,
            material_route=material_route,
            original_composer_candidate=original_composer_candidate,
            original_display_decision=original_display_decision,
            recovery_plan=plan,
            trace_id=trace_id,
            recovery_context=recovery_context,
        )

    original_source_kind = _candidate_source_kind(original_composer_candidate)
    if "self_denial_safe_state_answer" not in _clean(safety_triage_kind):
        self_denial_safe_state_answer_candidate = None
    candidates = _candidate_options(
        original_composer_candidate=original_composer_candidate,
        bounded_repaired_original_candidate=bounded_repaired_original_candidate,
        low_information_candidate=low_information_candidate,
        self_denial_safe_state_answer_candidate=self_denial_safe_state_answer_candidate,
        normal_observation_rebuild_candidate=normal_observation_rebuild_candidate,
        complete_initial_surface_recomposition_candidate=complete_initial_surface_recomposition_candidate,
        labelled_two_stage_surface_recomposition_candidate=labelled_two_stage_surface_recomposition_candidate,
        original_source_kind=original_source_kind,
        recovery_plan=plan,
    )

    blocked: list[str] = []
    reasons: list[str] = list(
        _dedupe(
            list(bounded_original_build_reasons)
            + list(low_information_build_reasons)
            + list(complete_initial_recomposition_build_reasons)
            + list(labelled_two_stage_recomposition_build_reasons)
            + list(normal_rebuild_build_reasons)
        )
    )
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
            + list(_as_mapping(plan).get("blockers_if_no_public_candidate") or ())
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


def _should_attempt_normal_observation_rebuild(
    *,
    original_composer_candidate: Any | None,
    original_display_decision: Any,
    material_route: Any,
    recovery_plan: Mapping[str, Any],
    safety_triage_kind: str,
    safety_requires_block: bool = False,
) -> bool:
    if safety_requires_block:
        return False
    if original_composer_candidate is None:
        return False
    if _display_decision_passed(original_display_decision):
        return False
    if not _candidate_has_public_text(original_composer_candidate):
        return False
    if _clean_identifier(getattr(original_composer_candidate, "composer_source", ""), max_length=96) != "ai_generated":
        return False
    if bool(getattr(original_composer_candidate, "ai_generated", False)) is not True:
        return False
    if not _safety_triage_allows_normal_observation_rebuild(safety_triage_kind):
        return False
    if _recovery_plan_requires_labelled_two_stage(recovery_plan):
        return False

    source_kind = _candidate_source_kind(original_composer_candidate)
    if source_kind in {
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
        CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
        "diagnostic_recovery_surface",
    }:
        return False
    original_comment = _clean(getattr(original_composer_candidate, "comment_text", ""))
    if _looks_like_gate_recovery_material_surface(original_composer_candidate, original_comment):
        return False

    route_meta = _material_route_meta(material_route)
    input_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    material_quality = _clean_identifier(
        input_summary.get("material_quality")
        or route_meta.get("material_quality")
        or getattr(material_route, "material_quality", ""),
        max_length=96,
    )
    if material_quality in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES:
        return False

    failed_summary = _as_mapping(recovery_plan.get("failed_gate_summary"))
    reason_families = _dedupe(
        failed_summary.get("reason_families")
        or _normal_rebuild_reason_families(original_display_decision)
    )
    non_repairable_families = _dedupe(
        failed_summary.get("non_repairable_reason_families")
        or _normal_rebuild_non_repairable_reason_families(original_display_decision)
    )
    if not set(reason_families).intersection(_NORMAL_REBUILD_REPAIRABLE_REASON_FAMILIES):
        return False
    if set(non_repairable_families).intersection(_NORMAL_REBUILD_NON_REPAIRABLE_REASON_FAMILIES):
        return False

    target = _clean_identifier(recovery_plan.get("target_public_candidate_source"), max_length=96)
    fallback_order = set(_dedupe(recovery_plan.get("fallback_public_candidate_source_order") or []))
    return bool(
        target == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        or CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE in fallback_order
    )


def _build_normal_observation_rebuild_candidate(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    original_composer_candidate: Any | None,
    original_display_decision: Any,
    recovery_plan: Mapping[str, Any],
    trace_id: str,
    recovery_context: str,
) -> tuple[ConversationComposerCandidate | None, list[str]]:
    if original_composer_candidate is None:
        return None, ["normal_observation_rebuild_original_candidate_missing"]
    original_comment = _clean(getattr(original_composer_candidate, "comment_text", ""))
    if not original_comment:
        return None, ["normal_observation_rebuild_original_comment_text_missing"]
    original_source_kind = _candidate_source_kind(original_composer_candidate)
    if original_source_kind in {
        CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
        CANDIDATE_SOURCE_KIND_DIAGNOSTIC_RECOVERY_SURFACE,
        CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
        "diagnostic_recovery_surface",
    }:
        return None, ["normal_observation_rebuild_original_source_not_allowed"]
    if _clean_identifier(getattr(original_composer_candidate, "composer_source", ""), max_length=96) != "ai_generated":
        return None, ["normal_observation_rebuild_original_source_not_ai_generated"]
    if bool(getattr(original_composer_candidate, "ai_generated", False)) is not True:
        return None, ["normal_observation_rebuild_original_ai_generated_flag_missing"]
    if _looks_like_gate_recovery_material_surface(original_composer_candidate, original_comment):
        return None, ["normal_observation_rebuild_original_gate_recovery_material_surface"]

    route_meta = dict(_material_route_meta(material_route))
    input_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    failed_summary = _as_mapping(recovery_plan.get("failed_gate_summary"))
    material_quality = _clean_identifier(
        input_summary.get("material_quality")
        or route_meta.get("material_quality")
        or getattr(material_route, "material_quality", ""),
        max_length=96,
    )
    if material_quality in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES:
        return None, ["normal_observation_rebuild_material_quality_not_normal"]
    if _recovery_plan_requires_labelled_two_stage(recovery_plan):
        return None, [BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED]

    reason_families = _dedupe(
        failed_summary.get("reason_families")
        or _normal_rebuild_reason_families(original_display_decision)
    )
    non_repairable_families = _dedupe(
        failed_summary.get("non_repairable_reason_families")
        or _normal_rebuild_non_repairable_reason_families(original_display_decision)
    )
    if not set(reason_families).intersection(_NORMAL_REBUILD_REPAIRABLE_REASON_FAMILIES):
        return None, ["normal_observation_rebuild_repairable_reason_family_missing"]
    if set(non_repairable_families).intersection(_NORMAL_REBUILD_NON_REPAIRABLE_REASON_FAMILIES):
        return None, ["normal_observation_rebuild_non_repairable_reason_present"]

    surface_plan = _normal_observation_rebuild_surface_plan(
        current_input=current_input,
        material_route=material_route,
        original_composer_candidate=original_composer_candidate,
    )
    comment_text = _normal_observation_rebuild_comment_from_plan(surface_plan)
    precheck_blockers = _normal_rebuild_surface_precheck(comment_text)
    if precheck_blockers:
        return None, [f"normal_observation_rebuild_surface_precheck_failed:{blocker}" for blocker in precheck_blockers]

    original_model = _clean_identifier(getattr(original_composer_candidate, "composer_model", ""), max_length=128)
    original_generation_method = _clean_identifier(getattr(original_composer_candidate, "generation_method", ""), max_length=128)
    original_composer_source = _clean_identifier(getattr(original_composer_candidate, "composer_source", ""), max_length=96)
    original_meta = _body_free_mapping(_candidate_meta(original_composer_candidate))
    original_meta_keys = tuple(sorted(str(key) for key in original_meta.keys()))
    relation_ids = list(
        _dedupe(
            list(getattr(original_composer_candidate, "used_relation_ids", []) or [])
            + list(input_summary.get("relation_material_ids") or [])
            + list(route_meta.get("relation_material_ids") or [])
            + list(route_meta.get("generic_relation_material_ids") or [])
        )
    )
    claim_ids = list(_dedupe(getattr(original_composer_candidate, "used_claim_ids", []) or []))
    visible_slots = list(
        _dedupe(
            input_summary.get("visible_material_slots")
            or route_meta.get("visible_material_slots")
            or getattr(material_route, "visible_material_slots", None)
        )
    )
    lineage = {
        "original_candidate_present": True,
        "original_candidate_source": original_source_kind or original_composer_source or CANDIDATE_SOURCE_KIND_NONE,
        "recovery_plan_used": True,
        "diagnostic_surface_used": False,
        "public_candidate_rebuilt_after_recovery": True,
    }
    meta = {
        "schema_version": NORMAL_OBSERVATION_REBUILD_META_SCHEMA_VERSION,
        "source_phase": NORMAL_OBSERVATION_REBUILD_SOURCE_PHASE,
        "recovery_context": _clean_identifier(recovery_context, max_length=96) or RECOVERY_CONTEXT_UNKNOWN,
        "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_model": NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
        "generation_method": NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
        "normal_observation_rebuild_connected": True,
        "normal_observation_rebuild_ready": True,
        "normal_observation_rebuild_applied": True,
        "normal_observation_rebuild_attempt_count": 1,
        "normal_observation_rebuild_attempt_limit": _NORMAL_REBUILD_ATTEMPT_LIMIT,
        "surface_requirement": _normal_observation_rebuild_plain_surface_requirement(
            material_quality=material_quality,
            recovery_plan=recovery_plan,
        ),
        "surface_requirement_family": SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
        "two_stage_required": False,
        "plain_state_answer_allowed": True,
        "low_information_allowed": False,
        "normal_observation_rebuild_plain_state_answer_surface": True,
        "two_stage_section_surface_plan": {
            "required": False,
            "two_stage_required": False,
            "surface_requirement_family": SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
            "plain_state_answer_allowed": True,
            "source_phase": NORMAL_OBSERVATION_REBUILD_SOURCE_PHASE,
            "normal_observation_rebuild_plain_surface": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "source_gate_failure_families": list(reason_families),
        "non_repairable_reason_families": list(non_repairable_families),
        "surface_repair_operations": list(surface_plan.get("surface_repair_operations") or []),
        "surface_contract_summary": {
            "scope_marker_required": True,
            "scope_marker_family": "environment_state_output",
            "sentence_count_max": _NORMAL_REBUILD_MAX_SENTENCES,
            "forbidden_fragment_screened": True,
            "relation_skeleton_screened": True,
            "diagnostic_claim_screened": True,
        },
        "source_material_summary": {
            "original_candidate_present": True,
            "original_candidate_ai_generated": True,
            "material_quality": material_quality,
            "visible_slot_count": len(visible_slots),
            "relation_id_count": len(relation_ids),
            "claim_id_count": len(claim_ids),
            "user_payload_serialized": False,
            "candidate_payload_serialized": False,
        },
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
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
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
    if _contains_forbidden_text_key(meta):
        return None, ["normal_observation_rebuild_meta_body_free_contract_failed"]

    return (
        ConversationComposerCandidate(
            comment_text=comment_text,
            composer_source="ai_generated",
            status="generated",
            ai_generated=True,
            trace_id=trace_id or _clean_identifier(getattr(original_composer_candidate, "trace_id", ""), max_length=128),
            attempt_count=1,
            used_evidence_span_ids=list(getattr(original_composer_candidate, "used_evidence_span_ids", []) or []),
            confidence=float(getattr(original_composer_candidate, "confidence", 0.0) or 0.0) or 0.76,
            rejection_reasons=[],
            request_schema_version=_clean_identifier(getattr(original_composer_candidate, "request_schema_version", ""), max_length=128) or "emlis.composer.request.v1",
            response_schema_version=NORMAL_OBSERVATION_REBUILD_RESPONSE_SCHEMA_VERSION,
            fixed_string_renderer_used=False,
            composer_model=NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
            generation_method=NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
            coverage_scope="current_input_normal_observation_rebuild",
            generation_scope="current_input_only",
            composer_meta=meta,
            used_claim_ids=claim_ids,
            used_relation_ids=relation_ids,
        ),
        ["normal_observation_rebuild_candidate_built"],
    )


def _normal_observation_rebuild_surface_plan(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    original_composer_candidate: Any,
) -> dict[str, Any]:
    route_meta = _material_route_meta(material_route)
    current = _as_mapping(current_input)
    original_comment = _clean(getattr(original_composer_candidate, "comment_text", ""))
    memo_like = _clean(current.get("memo") or current.get("memo_text") or current.get("comment") or "")
    action_like = _clean(current.get("memo_action") or current.get("action") or current.get("next_action") or "")
    categories = _normal_rebuild_safe_string_items(current.get("category") or current.get("categories"))
    emotions = _normal_rebuild_safe_string_items(current.get("emotions") or current.get("emotion"))
    slots = _dedupe(route_meta.get("visible_material_slots") or getattr(material_route, "visible_material_slots", None) or [])
    relation_ids = _dedupe(
        route_meta.get("relation_material_ids")
        or route_meta.get("generic_relation_material_ids")
        or getattr(material_route, "generic_relation_material_ids", None)
        or []
    )
    return {
        "topic_phrase": _normal_rebuild_topic_phrase(
            memo_like=memo_like,
            original_comment=original_comment,
            categories=categories,
            relation_ids=relation_ids,
        ),
        "feeling_phrase": _normal_rebuild_feeling_phrase(
            memo_like=memo_like,
            original_comment=original_comment,
            emotions=emotions,
        ),
        "follow_phrase": _normal_rebuild_follow_phrase(
            memo_action=action_like,
            memo_like=memo_like,
            slots=slots,
        ),
        "surface_repair_operations": _dedupe(
            [
                "drop_relation_skeleton_markers",
                "replace_analytic_register",
                "normalize_scope_marker",
                "shorten_to_state_answer",
                "remove_gate_recovery_fragments",
                "rebuild_human_follow_sentence",
            ]
        ),
    }


def _normal_observation_rebuild_comment_from_plan(surface_plan: Mapping[str, Any]) -> str:
    topic = _clean(surface_plan.get("topic_phrase")) or "この出来事"
    feeling = _clean(surface_plan.get("feeling_phrase")) or "気持ちの動き"
    follow = _clean(surface_plan.get("follow_phrase")) or "その中で、まだ言葉にしようとしている途中の重さもEmlisは受け取りました。"
    first = f"この記録では、{topic}について、{feeling}がまだ落ち着ききっていない状態として見えます。"
    if not follow.endswith(("。", "！", "？", "!", "?")):
        follow = f"{follow}。"
    return f"{first}{follow}"


def _normal_rebuild_surface_precheck(comment: str) -> list[str]:
    body = _clean(comment)
    blockers: list[str] = []
    if not body:
        blockers.append("empty_comment")
        return blockers
    sentence_count = len([part for part in re.split(r"(?<=[。！？!?])\s*", body) if _clean(part)])
    if sentence_count < _NORMAL_REBUILD_MIN_SENTENCES:
        blockers.append("sentence_count_too_low")
    if sentence_count > _NORMAL_REBUILD_MAX_SENTENCES:
        blockers.append("sentence_count_too_high")
    if not any(marker in body for marker in _NORMAL_REBUILD_ALLOWED_SCOPE_MARKERS):
        blockers.append("scope_marker_missing")
    if _relation_skeleton_forbidden_fragment_present(body):
        blockers.append("relation_skeleton_forbidden_fragment_present")
    if any(fragment in body for fragment in _NORMAL_REBUILD_GATE_RECOVERY_MATERIAL_FRAGMENTS):
        blockers.append("gate_recovery_material_fragment_present")
    if any(fragment in body for fragment in _NORMAL_REBUILD_ANALYTIC_REGISTER_FRAGMENTS):
        blockers.append("analytic_register_fragment_present")
    if re.search(r"(診断|人格|原因|処方|してください|するべき|すべき)", body):
        blockers.append("diagnostic_or_instruction_claim_present")
    return list(_dedupe(blockers))


def _relation_skeleton_forbidden_fragment_present(comment: str) -> bool:
    body = _clean(comment)
    return any(fragment in body for fragment in _NORMAL_REBUILD_FORBIDDEN_SURFACE_FRAGMENTS)


def _safety_triage_allows_normal_observation_rebuild(safety_triage_kind: str) -> bool:
    kind = _clean_identifier(safety_triage_kind, max_length=128).lower()
    if not kind:
        return False
    blocked_markers = ("requires_block", "safety_blocked", "emergency", "self_harm", "medical", "legal")
    if any(marker in kind for marker in blocked_markers):
        return False
    return "safe" in kind or "observation" in kind


def _normal_rebuild_topic_phrase(
    *,
    memo_like: str,
    original_comment: str,
    categories: Sequence[str],
    relation_ids: Sequence[str],
) -> str:
    source = f"{memo_like}\n{original_comment}\n{' '.join(categories)}\n{' '.join(relation_ids)}"
    if any(marker in source for marker in ("仕事", "職場", "会社", "work")) and any(marker in source for marker in ("人間関係", "相手", "関係", "relationship")):
        return "仕事や人とのやり取り"
    if any(marker in source for marker in ("仕事", "職場", "会社", "work")):
        return "仕事の話"
    if any(marker in source for marker in ("家族", "親", "子", "family")):
        return "家族とのやり取り"
    if any(marker in source for marker in ("友", "恋人", "パートナー", "関係", "relationship")):
        return "人とのやり取り"
    if categories:
        return _normal_rebuild_join_terms(categories[:2]) + "のこと"
    return "この出来事"


def _normal_rebuild_feeling_phrase(
    *,
    memo_like: str,
    original_comment: str,
    emotions: Sequence[str],
) -> str:
    source = f"{memo_like}\n{original_comment}\n{' '.join(emotions)}"
    if "納得" in source and any(marker in source for marker in ("引っかかり", "違和感", "ひっかかり")):
        return "納得したい気持ちと引っかかり"
    if "迷" in source and any(marker in source for marker in ("不安", "違和感")):
        return "迷いと不安"
    if len(emotions) >= 2:
        return _normal_rebuild_join_terms(emotions[:2])
    if len(emotions) == 1:
        return f"{emotions[0]}の動き"
    if "不安" in source:
        return "不安の動き"
    if any(marker in source for marker in ("怒", "腹", "嫌")):
        return "強い反応"
    return "気持ちの動き"


def _normal_rebuild_follow_phrase(
    *,
    memo_action: str,
    memo_like: str,
    slots: Sequence[str],
) -> str:
    source = f"{memo_action}\n{memo_like}\n{' '.join(slots)}"
    if "事実" in source and "返事" in source:
        return "返事を急がず、事実を分けて見ようとしているところもEmlisは受け取りました。"
    if any(marker in source for marker in ("書き出", "メモ", "記録")):
        return "一度言葉に分けて見ようとしているところもEmlisは受け取りました。"
    if any(marker in source for marker in ("休", "寝", "落ち着")):
        return "すぐに結論へ寄せず、落ち着きを取り戻そうとしているところもEmlisは受け取りました。"
    if any(marker in source for marker in ("行動", "action", "次")):
        return "次にどう動くかを探しているところもEmlisは受け取りました。"
    return "その中で、まだ言葉にしようとしている途中の重さもEmlisは受け取りました。"


def _normal_rebuild_safe_string_items(value: Any) -> tuple[str, ...]:
    items: list[str] = []
    for item in _as_sequence(value):
        text = re.sub(r"[\r\n\t]+", " ", _clean(item))
        text = re.sub(r"[。！？!?].*$", "", text).strip()
        if not text:
            continue
        if any(fragment in text for fragment in _NORMAL_REBUILD_FORBIDDEN_SURFACE_FRAGMENTS):
            continue
        if text in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
            continue
        items.append(text[:24])
    return _dedupe(items)


def _normal_rebuild_join_terms(values: Sequence[str]) -> str:
    terms = [term for term in values if term]
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    if len(terms) == 2:
        return f"{terms[0]}や{terms[1]}"
    return f"{terms[0]}や{terms[1]}、{terms[2]}"


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
    normal_observation_rebuild_candidate: Any | None,
    complete_initial_surface_recomposition_candidate: Any | None,
    labelled_two_stage_surface_recomposition_candidate: Any | None,
    original_source_kind: str,
    recovery_plan: Mapping[str, Any],
) -> tuple[tuple[str, str, Any | None], ...]:
    repaired_original = bounded_repaired_original_candidate
    if repaired_original is None and original_source_kind in {
        CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
        CANDIDATE_SOURCE_KIND_COMPLETE_SELF_REPAIR_CANDIDATE,
    }:
        repaired_original = original_composer_candidate

    input_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    material_quality = _clean_identifier(input_summary.get("material_quality"), max_length=96)
    if (
        material_quality in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES
        or _recovery_plan_requires_labelled_two_stage(recovery_plan)
    ):
        normal_observation_rebuild_candidate = None

    option_map: dict[str, tuple[str, str, Any | None]] = {
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE: (
            CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
            _SELECTION_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION,
            labelled_two_stage_surface_recomposition_candidate,
        ),
        CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE: (
            CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
            _SELECTION_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION,
            complete_initial_surface_recomposition_candidate,
        ),
        CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE: (
            CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            _SELECTION_KIND_NORMAL_OBSERVATION_REBUILD,
            normal_observation_rebuild_candidate,
        ),
        CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE: (
            CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            _SELECTION_KIND_BOUND_REPAIRED_ORIGINAL,
            repaired_original,
        ),
        CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER: (
            CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            _SELECTION_KIND_LOW_INFORMATION,
            low_information_candidate,
        ),
        CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER: (
            CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
            _SELECTION_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
            self_denial_safe_state_answer_candidate,
        ),
    }
    ordered_sources = _ordered_public_candidate_sources(recovery_plan)
    return tuple(option_map[source] for source in ordered_sources if source in option_map)


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
    if (
        "labelled_two_stage_surface_recomposition" in model
        or "labelled_two_stage_surface_recomposition" in generation_method
        or "labelled_two_stage_surface_recomposition" in composer_source
    ):
        return CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    if (
        "complete_initial_surface_recomposition" in model
        or "complete_initial_surface_recomposition" in generation_method
        or "complete_initial_surface_recomposition" in composer_source
    ):
        return CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
    if "normal_observation_rebuild" in model or "normal_observation_rebuild" in generation_method or "normal_observation_rebuild" in composer_source:
        return CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
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



def _resolve_surface_requirement_for_recovery_plan(
    *,
    current_input: Mapping[str, Any] | None,
    material_route: Any,
    original_composer_candidate: Any | None,
    original_display_decision: Any,
    safety_triage_kind: str,
    recovery_context: str,
) -> dict[str, Any]:
    candidate_meta = _candidate_meta(original_composer_candidate)
    diagnostic_summary = {
        "display_status_before_recovery": _clean_identifier(
            getattr(original_display_decision, "observation_status", ""), max_length=96
        ),
        "rejection_reasons": _dedupe(getattr(original_display_decision, "rejection_reasons", []) or []),
        "reason_families": _normal_rebuild_reason_families(original_display_decision),
        "non_repairable_reason_families": _normal_rebuild_non_repairable_reason_families(original_display_decision),
        "safety_triage_kind": _clean_identifier(safety_triage_kind, max_length=96),
        "composer_source": _clean_identifier(
            getattr(original_composer_candidate, "composer_source", ""), max_length=96
        ),
        "candidate_status": _clean_identifier(
            getattr(original_composer_candidate, "status", ""), max_length=96
        ),
        "candidate_source_kind": _candidate_source_kind(original_composer_candidate),
        "candidate_generated_before_display_gate": bool(original_composer_candidate is not None),
        "recovery_context": _clean_identifier(recovery_context, max_length=96) or RECOVERY_CONTEXT_UNKNOWN,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    return resolve_public_surface_requirement(
        current_input=current_input,
        material_route=material_route,
        composer_meta=candidate_meta,
        diagnostic_summary=diagnostic_summary,
        fixture_family_meta=None,
    )

def _recovery_plan_requires_labelled_two_stage(recovery_plan: Mapping[str, Any] | None) -> bool:
    return _surface_requirement_requires_labelled_two_stage(
        _as_mapping(recovery_plan).get("surface_requirement")
    )


def _surface_requirement_requires_labelled_two_stage(
    surface_requirement: Mapping[str, Any] | None,
) -> bool:
    requirement = _as_mapping(surface_requirement)
    if not requirement:
        return False
    family = _clean_identifier(requirement.get("surface_requirement_family"), max_length=96)
    return bool(
        requirement.get("two_stage_required") is True
        or family == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    )


def _normal_observation_rebuild_plain_surface_requirement(
    *,
    material_quality: str,
    recovery_plan: Mapping[str, Any],
) -> dict[str, Any]:
    plan_requirement = _as_mapping(recovery_plan.get("surface_requirement"))
    plan_classification = _as_mapping(plan_requirement.get("input_material_classification"))
    return public_surface_requirement_public_summary(
        {
            "surface_requirement_family": SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
            "two_stage_required": False,
            "plain_state_answer_allowed": True,
            "low_information_allowed": False,
            "decision_sources": ["normal_observation_rebuild_plain_surface_boundary"],
            "material_quality_family": material_quality,
            "input_material_classification": plan_classification,
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
    )


def _normal_rebuild_candidate_source_order(
    values: Sequence[Any] | Any | None,
    *,
    normal_rebuild_allowed: bool,
) -> tuple[str, ...]:
    ordered = _dedupe(values or [])
    if normal_rebuild_allowed:
        return ordered
    return tuple(
        item
        for item in ordered
        if item != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )


def _default_recovery_plan(
    *,
    material_route: Any,
    original_display_decision: Any,
    safety_triage_kind: str,
    recovery_context: str,
    original_candidate_present: bool,
    surface_requirement: Mapping[str, Any] | None = None,
    complete_initial_surface_availability_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    route_meta = _material_route_meta(material_route)
    material_quality = _clean_identifier(
        _first(("material_quality", "eligibility_status", "status"), route_meta),
        max_length=96,
    )
    surface_requirement_summary = public_surface_requirement_public_summary(surface_requirement)
    repairable_reason_families = _normal_rebuild_reason_families(original_display_decision)
    non_repairable_reason_families = _normal_rebuild_non_repairable_reason_families(original_display_decision)
    normal_rebuild_candidate_possible = bool(
        original_candidate_present
        and repairable_reason_families
        and not non_repairable_reason_families
    )
    normal_rebuild_blocked_by_two_stage = bool(
        normal_rebuild_candidate_possible
        and _surface_requirement_requires_labelled_two_stage(surface_requirement_summary)
    )
    normal_rebuild_allowed = bool(
        normal_rebuild_candidate_possible
        and not normal_rebuild_blocked_by_two_stage
    )
    complete_initial_surface_recomposition_allowed = should_attempt_complete_initial_surface_recomposition(
        availability_summary=complete_initial_surface_availability_summary,
        surface_requirement=surface_requirement_summary,
        material_route=material_route,
    )
    # _default_recovery_plan receives only the candidate-presence boolean.  If a
    # labelled surface is required and an original candidate exists, target P6;
    # the concrete builder will still fail closed if the candidate is missing,
    # unsafe, or already unavailable.
    labelled_two_stage_recomposition_allowed = bool(
        original_candidate_present
        and _surface_requirement_requires_labelled_two_stage(surface_requirement_summary)
        and material_quality not in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES
    )
    target = (
        CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
        if material_quality in _LOW_INFORMATION_RECOVERY_MATERIAL_QUALITIES
        else CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER
        if "self_denial_safe_state_answer" in _clean(safety_triage_kind)
        else CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
        if labelled_two_stage_recomposition_allowed
        else CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
        if complete_initial_surface_recomposition_allowed
        else CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        if normal_rebuild_allowed
        else CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    )
    blockers_if_no_public_candidate = [BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING]
    if labelled_two_stage_recomposition_allowed:
        blockers_if_no_public_candidate.insert(
            0,
            BLOCKER_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE_MISSING,
        )
    if complete_initial_surface_recomposition_allowed:
        blockers_if_no_public_candidate.insert(
            0,
            BLOCKER_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE_MISSING,
        )
    if normal_rebuild_allowed:
        blockers_if_no_public_candidate.insert(0, BLOCKER_NORMAL_OBSERVATION_REBUILD_CANDIDATE_MISSING)
    elif normal_rebuild_blocked_by_two_stage:
        blockers_if_no_public_candidate.insert(
            0,
            BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED,
        )
    normal_rebuild_in_order = not normal_rebuild_blocked_by_two_stage
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
            "reason_families": repairable_reason_families,
            "non_repairable_reason_families": non_repairable_reason_families,
            "safety_triage_kind": _clean_identifier(safety_triage_kind, max_length=96),
        },
        "surface_requirement": surface_requirement_summary,
        "complete_initial_surface_availability_summary": complete_initial_surface_availability_public_summary(
            complete_initial_surface_availability_summary
        ),
        "target_public_candidate_source": target,
        "fallback_public_candidate_source_order": _normal_rebuild_candidate_source_order(
            [
                CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
                CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
                CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
                CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
                CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
            normal_rebuild_allowed=normal_rebuild_in_order,
        ),
        "diagnostic_surface_allowed": True,
        "diagnostic_surface_public_display_allowed": False,
        "public_candidate_required": True,
        "blockers_if_no_public_candidate": blockers_if_no_public_candidate,
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
    if not merged.get("surface_requirement"):
        merged["surface_requirement"] = dict(_as_mapping(defaults.get("surface_requirement")))
    if not merged.get("complete_initial_surface_availability_summary"):
        merged["complete_initial_surface_availability_summary"] = dict(
            _as_mapping(defaults.get("complete_initial_surface_availability_summary"))
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
    for key in (
        "display_status_before_recovery",
        "rejection_reasons",
        "reason_families",
        "non_repairable_reason_families",
        "safety_triage_kind",
    ):
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
    surface_requirement = public_surface_requirement_public_summary(source.get("surface_requirement"))
    normal_rebuild_allowed = not _surface_requirement_requires_labelled_two_stage(surface_requirement)
    fallback_order = _normal_rebuild_candidate_source_order(
        source.get("fallback_public_candidate_source_order") or [],
        normal_rebuild_allowed=normal_rebuild_allowed,
    )
    availability_summary = complete_initial_surface_availability_public_summary(
        source.get("complete_initial_surface_availability_summary")
    )
    blockers = _dedupe(
        source.get("blockers_if_no_public_candidate") or [BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING]
    )
    if availability_summary and availability_summary.get("recovery_lane") == "complete_initial_surface_recomposition":
        blockers = _dedupe(
            [BLOCKER_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE_MISSING, *blockers]
        )
    if not normal_rebuild_allowed:
        blockers = _dedupe(
            [BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED, *blockers]
        )
    target_public_candidate_source = _clean_identifier(source.get("target_public_candidate_source"), max_length=96)
    if not normal_rebuild_allowed and target_public_candidate_source == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE:
        target_public_candidate_source = ""
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
            "reason_families": _dedupe(failed_summary.get("reason_families") or []),
            "non_repairable_reason_families": _dedupe(
                failed_summary.get("non_repairable_reason_families") or []
            ),
            "safety_triage_kind": _clean_identifier(failed_summary.get("safety_triage_kind"), max_length=96),
        },
        "surface_requirement": surface_requirement,
        "complete_initial_surface_availability_summary": availability_summary,
        "target_public_candidate_source": target_public_candidate_source,
        "fallback_public_candidate_source_order": fallback_order,
        "diagnostic_surface_allowed": bool(source.get("diagnostic_surface_allowed", True)),
        "diagnostic_surface_public_display_allowed": False,
        "public_candidate_required": bool(source.get("public_candidate_required", True)),
        "blockers_if_no_public_candidate": blockers,
    }



def _normal_rebuild_failure_family_present(original_display_decision: Any) -> bool:
    return bool(
        _normal_rebuild_reason_families(original_display_decision)
        and not _normal_rebuild_non_repairable_reason_families(original_display_decision)
    )


def _normal_rebuild_reason_families(original_display_decision: Any) -> tuple[str, ...]:
    return _normal_rebuild_reason_families_from_reasons(
        getattr(original_display_decision, "rejection_reasons", []) or []
    )


def _normal_rebuild_non_repairable_reason_families(original_display_decision: Any) -> tuple[str, ...]:
    return _normal_rebuild_reason_families_from_reasons(
        getattr(original_display_decision, "rejection_reasons", []) or [],
        marker_map=_NORMAL_REBUILD_NON_REPAIRABLE_REASON_MARKERS,
        allowed_families=_NORMAL_REBUILD_NON_REPAIRABLE_REASON_FAMILIES,
    )


def _normal_rebuild_reason_families_from_reasons(
    reasons: Sequence[Any] | Any | None,
    *,
    marker_map: Sequence[tuple[str, Sequence[str]]] = _NORMAL_REBUILD_REASON_FAMILY_MARKERS,
    allowed_families: frozenset[str] = _NORMAL_REBUILD_REPAIRABLE_REASON_FAMILIES,
) -> tuple[str, ...]:
    families: list[str] = []
    normalized_reasons = [str(reason or "").strip().lower() for reason in _as_sequence(reasons)]
    for family, markers in marker_map:
        if family not in allowed_families:
            continue
        if any(marker in reason for reason in normalized_reasons for marker in markers):
            families.append(family)
    return _dedupe(families)


def _ordered_public_candidate_sources(recovery_plan: Mapping[str, Any]) -> tuple[str, ...]:
    labelled_two_stage_required = _recovery_plan_requires_labelled_two_stage(recovery_plan)
    normal_rebuild_allowed = not labelled_two_stage_required
    target = _clean_identifier(recovery_plan.get("target_public_candidate_source"), max_length=96)
    if labelled_two_stage_required:
        # P6 owns labelled two-stage repair.  Older gate recovery plans may carry
        # bounded-original first in their fallback order; keeping that ahead of P6
        # re-adopts the already-failed surface.  Promote P6 without changing RN
        # or Gate contracts.
        target = CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    if (
        not normal_rebuild_allowed
        and target == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    ):
        target = ""
    fallback_order = list(
        _normal_rebuild_candidate_source_order(
            recovery_plan.get("fallback_public_candidate_source_order") or [],
            normal_rebuild_allowed=normal_rebuild_allowed,
        )
    )
    if labelled_two_stage_required:
        fallback_order = [
            source
            for source in fallback_order
            if source != CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
        ]
    legacy_order = [
        CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
        CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
        CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
        CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
        CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
    ]
    if target == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE and normal_rebuild_allowed:
        legacy_order.insert(0, CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE)
    return _dedupe([target, *fallback_order, *legacy_order])


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
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_COMPOSER_MODEL",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_GENERATION_METHOD",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_RESPONSE_SCHEMA_VERSION",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SCHEMA_VERSION",
    "COMPLETE_INITIAL_SURFACE_RECOMPOSITION_SOURCE_PHASE",
    "LOW_INFORMATION_RECOVERY_COMPOSER_MODEL",
    "LOW_INFORMATION_RECOVERY_GENERATION_METHOD",
    "LOW_INFORMATION_RECOVERY_SOURCE_PHASE",
    "NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL",
    "NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD",
    "NORMAL_OBSERVATION_REBUILD_META_SCHEMA_VERSION",
    "NORMAL_OBSERVATION_REBUILD_RESPONSE_SCHEMA_VERSION",
    "NORMAL_OBSERVATION_REBUILD_SOURCE_PHASE",
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
