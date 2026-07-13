# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free Reception Content Planner v2 contract.

This module decides *what* Emlis may react to before any discourse or surface
wording exists.  It consumes only the canonical ``GroundedObservationPlan``;
case ids, raw input, fixture families, expected text, and surface cues are not
accepted by the public builder.

Step 3 deliberately leaves this planner disconnected from the production
reply path.  Candidate planning, surface realization, selection, and runtime
owner switching belong to later implementation steps.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any, Final, Literal, Mapping, Sequence

from emlis_ai_grounded_observation_plan import (
    GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
    GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION,
    GroundedObservationPlan,
    GroundedReceptionOpportunity,
    GroundedSemanticNucleus,
    GroundedSemanticRelation,
)


RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_content_plan.v2"
)
RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION: Final = (
    f"{GROUND_OBSERVATION_PLAN_SCHEMA_VERSION}+{GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION}"
)

ReceptionContentRole = Literal[
    "attention",
    "significance",
    "connection",
    "felt_response",
    "bounded_counterposition",
]
ReceptionContentDepth = Literal["minimal", "focused", "layered"]
ReceptionQuoteMode = Literal["none", "optional_single_anchor"]

_CODE_RE: Final = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_PLAN_ID_RE: Final = re.compile(r"^rcp2_[0-9a-f]{16}$")
_UNIT_ID_RE: Final = re.compile(r"^cu_[0-9]{2}$")
_FORBIDDEN_FIELD_NAMES: Final = frozenset(
    {
        "case_id",
        "fixture_id",
        "input_family",
        "memo",
        "memo_action",
        "raw_input",
        "raw_text",
        "source_text",
        "surface_text",
        "candidate_text",
        "expected_text",
        "visible_surface",
        "wording_cue",
    }
)
_DEPTH_UNIT_RANGE: Final[Mapping[str, tuple[int, int]]] = {
    "minimal": (1, 1),
    "focused": (2, 2),
    "layered": (3, 4),
}
_SENTENCE_BUDGET: Final[Mapping[str, tuple[int, int, int]]] = {
    "minimal": (1, 1, 2),
    "focused": (2, 2, 3),
    "layered": (3, 3, 4),
}
_RETENTION_RANK: Final = {"required": 2, "should": 1, "optional": 0}
_RELATION_RANK: Final[Mapping[str, int]] = {
    "continuation_or_refusal": 0,
    "shift_from_to": 1,
    "preserves_despite": 2,
    "contrast": 3,
    "coexistence": 4,
    "wish_and_constraint": 5,
    "attempt_and_block": 6,
    "action_supports_change": 7,
    "self_evaluation_about_state": 8,
    "evaluation_about_event": 9,
    "user_stated_result": 10,
    "user_stated_cause": 11,
    "temporal_before_after": 12,
    "uncertain_connection": 13,
}
_RELATION_SIGNATURE: Final[Mapping[str, str]] = {
    "continuation_or_refusal": "continuation_or_refusal_preserved",
    "shift_from_to": "attention_or_evaluation_shift",
    "preserves_despite": "value_or_intention_preserved_despite_burden",
    "contrast": "counterposed_meanings_coexist",
    "coexistence": "distinct_meanings_coexist",
    "wish_and_constraint": "wish_held_with_constraint",
    "attempt_and_block": "attempt_held_with_block",
    "action_supports_change": "action_connected_to_observed_change",
    "self_evaluation_about_state": "self_evaluation_connected_to_state",
    "evaluation_about_event": "evaluation_connected_to_event",
    "user_stated_result": "user_stated_result_relation",
    "user_stated_cause": "user_stated_cause_relation",
    "temporal_before_after": "time_bounded_transition",
    "uncertain_connection": "connection_kept_uncertain",
}
_OPPORTUNITY_SIGNATURE: Final[Mapping[str, str]] = {
    "current_burden": "current_burden_present",
    "concrete_effort": "concrete_action_recorded",
    "retained_intention": "intention_retained",
    "lived_change": "lived_change_observed",
    "help_seeking": "help_seeking_preserved",
    "counterdirection": "self_denial_boundary",
    "words_placed": "expression_or_label_present",
}
_OPPORTUNITY_STANCES: Final[Mapping[str, tuple[str, ...]]] = {
    "current_burden": ("notice", "stay_with"),
    "concrete_effort": ("notice", "honor_effort"),
    "retained_intention": ("notice", "protect_intention"),
    "lived_change": ("notice", "hold_as_meaningful"),
    "help_seeking": ("notice", "protect_help_seeking"),
    "counterdirection": ("bounded_disagreement", "protect_identity_boundary"),
    "words_placed": ("notice", "respect_expression"),
}
_OPPORTUNITY_FORBIDDEN: Final[Mapping[str, tuple[str, ...]]] = {
    "current_burden": (
        "causal_certainty",
        "diagnosis",
        "completed_recovery",
    ),
    "concrete_effort": (
        "success_guarantee",
        "completed_growth",
        "effort_erases_burden",
    ),
    "retained_intention": (
        "future_certainty",
        "success_guarantee",
        "intention_already_completed",
    ),
    "lived_change": (
        "completed_growth",
        "permanent_change",
        "all_difficulty_resolved",
    ),
    "help_seeking": (
        "recovery_guarantee",
        "diagnosis",
        "identity_assertion",
    ),
    "counterdirection": (
        "self_denial_identity_as_fact",
        "unsupported_positive_identity",
        "burden_erasure",
    ),
    "words_placed": (
        "causal_certainty",
        "identity_assertion",
        "input_detail_invention",
    ),
}


class ReceptionContentPlanV2Error(ValueError):
    """Raised when the body-free Step 3 contract cannot be satisfied."""


@dataclass(frozen=True)
class ReceptionSentenceBudgetV2:
    min: int
    target: int
    max: int


@dataclass(frozen=True)
class ReceptionContentUnitV2:
    unit_id: str
    role: ReceptionContentRole
    semantic_signature: str
    target_nucleus_ids: tuple[str, ...]
    support_nucleus_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    evidence_span_ids: tuple[str, ...]
    required: bool
    priority: float
    allowed_stance_codes: tuple[str, ...]
    forbidden_claim_codes: tuple[str, ...]


@dataclass(frozen=True)
class ReceptionDiscourseConstraintsV2:
    allowed_strategy_codes: tuple[str, ...]
    forbidden_strategy_codes: tuple[str, ...]
    must_keep_units_separate: tuple[tuple[str, str], ...]
    must_not_causal_link_unit_pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class ReceptionQuotePolicyV2:
    mode: ReceptionQuoteMode
    max_anchor_count: int
    boundary: Literal["none", "phrase"]


@dataclass(frozen=True)
class ReceptionContentPlanV2:
    schema_version: str
    plan_id: str
    source_observation_plan_version: str
    depth: ReceptionContentDepth
    sentence_budget: ReceptionSentenceBudgetV2
    content_units: tuple[ReceptionContentUnitV2, ...]
    discourse_constraints: ReceptionDiscourseConstraintsV2
    quote_policy: ReceptionQuotePolicyV2
    safety_policy_ref: str
    required_unit_ids: tuple[str, ...]
    body_free: bool = True

    def as_body_free_meta(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "case_id_included": False,
                "fixture_family_included": False,
                "raw_input_included": False,
                "raw_text_included": False,
                "source_text_included": False,
                "surface_text_included": False,
                "candidate_text_included": False,
                "expected_text_included": False,
                "runtime_connected": False,
                "public_contract_changed": False,
            }
        )
        return payload


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    rows: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in seen:
            seen.add(value)
            rows.append(value)
    return tuple(rows)


def _nucleus_index(plan: GroundedObservationPlan) -> dict[str, GroundedSemanticNucleus]:
    return {item.nucleus_id: item for item in plan.nuclei}


def _relation_index(plan: GroundedObservationPlan) -> dict[str, GroundedSemanticRelation]:
    return {item.relation_id: item for item in plan.relations}


def _evidence_for(
    plan: GroundedObservationPlan,
    *,
    target_nucleus_ids: Sequence[str],
    support_nucleus_ids: Sequence[str] = (),
    relation_ids: Sequence[str] = (),
    direct_evidence_span_ids: Sequence[str] = (),
) -> tuple[str, ...]:
    nuclei = _nucleus_index(plan)
    relations = _relation_index(plan)
    rows: list[str] = list(direct_evidence_span_ids)
    for nucleus_id in (*target_nucleus_ids, *support_nucleus_ids):
        nucleus = nuclei.get(nucleus_id)
        if nucleus is not None:
            rows.extend(nucleus.source_span_ids)
    for relation_id in relation_ids:
        relation = relations.get(relation_id)
        if relation is not None:
            rows.extend(relation.source_span_ids)
    available = set(plan.referenced_evidence_span_ids)
    return tuple(item for item in _dedupe(rows) if item in available)


def _source_forbidden_claims(
    plan: GroundedObservationPlan,
    nucleus_ids: Sequence[str],
) -> tuple[str, ...]:
    nuclei = _nucleus_index(plan)
    return _dedupe(
        [
            code.lower()
            for nucleus_id in nucleus_ids
            for code in getattr(nuclei.get(nucleus_id), "forbidden_inference_codes", ())
            if _CODE_RE.fullmatch(str(code or "").lower())
        ]
    )


def _effective_opportunity_family(
    plan: GroundedObservationPlan,
    opportunity: GroundedReceptionOpportunity,
) -> str:
    """Correct a burden-shaped v1 opportunity using its grounded polarity.

    The canonical v1 reception policy occasionally uses ``current_burden`` as
    its conservative default even when the selected nucleus is positive.  v2
    keeps the source nucleus and evidence unchanged, but must not turn that
    positive material into suffering on the Surface.
    """

    if opportunity.family != "current_burden":
        return opportunity.family
    if plan.safety_policy.identity_claim_must_not_be_accepted_as_fact:
        return opportunity.family
    nuclei = _nucleus_index(plan)
    targets = tuple(
        nuclei[nucleus_id]
        for nucleus_id in opportunity.target_nucleus_ids
        if nucleus_id in nuclei
    )
    target_polarities = {
        nucleus.semantic_frame.polarity for nucleus in targets
    }
    if not target_polarities or not target_polarities <= {"positive", "neutral"}:
        return opportunity.family
    if "positive" not in target_polarities:
        return opportunity.family

    source_polarities = {
        nucleus.semantic_frame.polarity
        for nucleus in plan.nuclei
        if nucleus.semantic_frame.actor == "current_user"
    }
    if "negative" in source_polarities:
        return "words_placed"
    if any(
        "semantic_role:current_change" in nucleus.semantic_frame.attribute_codes
        for nucleus in targets
    ):
        return "lived_change"
    return "words_placed"


def _opportunity_unit(
    plan: GroundedObservationPlan,
    opportunity: GroundedReceptionOpportunity,
    *,
    role: ReceptionContentRole,
    required: bool,
    priority: float,
) -> ReceptionContentUnitV2:
    effective_family = _effective_opportunity_family(plan, opportunity)
    nucleus_ids = _dedupe(
        [*opportunity.target_nucleus_ids, *opportunity.support_nucleus_ids]
    )
    return ReceptionContentUnitV2(
        unit_id="pending",
        role=role,
        semantic_signature=_OPPORTUNITY_SIGNATURE[effective_family],
        target_nucleus_ids=tuple(opportunity.target_nucleus_ids),
        support_nucleus_ids=tuple(opportunity.support_nucleus_ids),
        relation_ids=(),
        evidence_span_ids=_evidence_for(
            plan,
            target_nucleus_ids=opportunity.target_nucleus_ids,
            support_nucleus_ids=opportunity.support_nucleus_ids,
            direct_evidence_span_ids=opportunity.source_evidence_span_ids,
        ),
        required=required,
        priority=round(min(1.0, max(0.0, priority)), 3),
        allowed_stance_codes=_OPPORTUNITY_STANCES[effective_family],
        forbidden_claim_codes=_dedupe(
            [
                *_OPPORTUNITY_FORBIDDEN[effective_family],
                *_source_forbidden_claims(plan, nucleus_ids),
            ]
        ),
    )


def _relation_unit(
    plan: GroundedObservationPlan,
    relation: GroundedSemanticRelation,
) -> ReceptionContentUnitV2:
    nucleus_ids = (relation.from_nucleus_id, relation.to_nucleus_id)
    role: ReceptionContentRole = (
        "connection" if relation.type == "uncertain_connection" else "significance"
    )
    forbidden = [
        "causal_certainty",
        "relation_direction_inversion",
        "topic_reference_merge",
        *_source_forbidden_claims(plan, nucleus_ids),
    ]
    if relation.type in {"user_stated_cause", "user_stated_result"}:
        forbidden = [
            "causal_scope_expansion",
            "relation_direction_inversion",
            "topic_reference_merge",
            *_source_forbidden_claims(plan, nucleus_ids),
        ]
    return ReceptionContentUnitV2(
        unit_id="pending",
        role=role,
        semantic_signature=_RELATION_SIGNATURE.get(
            relation.type,
            "grounded_relation_preserved",
        ),
        target_nucleus_ids=nucleus_ids,
        support_nucleus_ids=(),
        relation_ids=(relation.relation_id,),
        evidence_span_ids=_evidence_for(
            plan,
            target_nucleus_ids=nucleus_ids,
            relation_ids=(relation.relation_id,),
        ),
        required=relation.retention in {"required", "should"},
        priority=round(
            0.82
            + 0.06 * _RETENTION_RANK.get(relation.retention, 0)
            + (0.04 if relation.type != "uncertain_connection" else 0.0),
            3,
        ),
        allowed_stance_codes=("notice", "hold_relation_without_expansion"),
        forbidden_claim_codes=_dedupe(forbidden),
    )


def _felt_response_unit(
    plan: GroundedObservationPlan,
    opportunity: GroundedReceptionOpportunity,
) -> ReceptionContentUnitV2:
    effective_family = _effective_opportunity_family(plan, opportunity)
    base = _opportunity_unit(
        plan,
        opportunity,
        role="felt_response",
        required=True,
        priority=0.86 if not opportunity.safety_required else 0.96,
    )
    return ReceptionContentUnitV2(
        unit_id="pending",
        role="felt_response",
        semantic_signature=(
            f"emlis_reception_of_{_OPPORTUNITY_SIGNATURE[effective_family]}"
        ),
        target_nucleus_ids=base.target_nucleus_ids,
        support_nucleus_ids=base.support_nucleus_ids,
        relation_ids=base.relation_ids,
        evidence_span_ids=base.evidence_span_ids,
        required=True,
        priority=base.priority,
        allowed_stance_codes=base.allowed_stance_codes,
        forbidden_claim_codes=_dedupe(
            [
                *base.forbidden_claim_codes,
                "mind_reading",
                "identity_assertion",
                "emotional_mirroring_without_evidence",
            ]
        ),
    )


def _safety_counterposition_unit(
    plan: GroundedObservationPlan,
) -> ReceptionContentUnitV2:
    """Bind the existing self-denial safety boundary when no opportunity exists.

    Some canonical v1 plans keep the identity boundary in ``safety_policy``
    while their reception Move only stays with the burden.  v2 must not lose
    that already-grounded boundary merely because it is not duplicated as an
    opportunity.
    """

    reception = plan.response_plan.human_reception_plan
    if reception is None or not reception.moves:
        raise ReceptionContentPlanV2Error("safety_counterposition_source_missing")
    source_move = next(
        (
            move
            for move in reception.moves
            if move.reception_act == "bounded_counter_self_denial"
        ),
        reception.moves[0],
    )
    target_ids = tuple(source_move.target_nucleus_ids)
    support_ids = tuple(source_move.support_nucleus_ids)
    nucleus_ids = _dedupe([*target_ids, *support_ids])
    if not target_ids:
        raise ReceptionContentPlanV2Error("safety_counterposition_target_missing")
    return ReceptionContentUnitV2(
        unit_id="pending",
        role="bounded_counterposition",
        semantic_signature="self_denial_boundary",
        target_nucleus_ids=target_ids,
        support_nucleus_ids=support_ids,
        relation_ids=(),
        evidence_span_ids=_evidence_for(
            plan,
            target_nucleus_ids=target_ids,
            support_nucleus_ids=support_ids,
            direct_evidence_span_ids=source_move.source_evidence_span_ids,
        ),
        required=True,
        priority=1.0,
        allowed_stance_codes=_OPPORTUNITY_STANCES["counterdirection"],
        forbidden_claim_codes=_dedupe(
            [
                *_OPPORTUNITY_FORBIDDEN["counterdirection"],
                *_source_forbidden_claims(plan, nucleus_ids),
            ]
        ),
    )


def _best_relation(plan: GroundedObservationPlan) -> GroundedSemanticRelation | None:
    response_relation_ids = set(plan.response_plan.relation_ids)
    rows = tuple(
        item
        for item in plan.relations
        if item.relation_id in response_relation_ids
        or item.retention in {"required", "should"}
    )
    if not rows:
        return None
    return min(
        rows,
        key=lambda item: _relation_sort_key(plan, item),
    )


def _relation_sort_key(
    plan: GroundedObservationPlan,
    relation: GroundedSemanticRelation,
) -> tuple[int, int, int, str]:
    nuclei = _nucleus_index(plan)
    uncertain_relation_count = sum(
        item.type == "uncertain_connection" for item in plan.relations
    )
    source_uncertain_ids = {
        nucleus.nucleus_id
        for nucleus in plan.nuclei
        if nucleus.semantic_frame.modality == "uncertain"
        or "operator:uncertainty" in nucleus.semantic_frame.attribute_codes
    }
    preserves_source_unknown = bool(
        relation.type == "uncertain_connection"
        and (
            source_uncertain_ids
            & {relation.from_nucleus_id, relation.to_nucleus_id}
            or uncertain_relation_count >= 2
            or any(
                nuclei[nucleus_id].kind == "self_evaluation"
                for nucleus_id in (relation.from_nucleus_id, relation.to_nucleus_id)
                if nucleus_id in nuclei
            )
        )
    )
    return (
        0 if preserves_source_unknown else 1,
        _RELATION_RANK.get(relation.type, 99),
        -_RETENTION_RANK.get(relation.retention, 0),
        relation.relation_id,
    )


def _ranked_relations(
    plan: GroundedObservationPlan,
) -> tuple[GroundedSemanticRelation, ...]:
    response_relation_ids = set(plan.response_plan.relation_ids)
    rows = tuple(
        item
        for item in plan.relations
        if item.relation_id in response_relation_ids
        or item.retention in {"required", "should"}
    )
    return tuple(
        sorted(
            rows,
            key=lambda item: _relation_sort_key(plan, item),
        )
    )


def _effective_depth(
    plan: GroundedObservationPlan,
    source_depth: ReceptionContentDepth,
) -> ReceptionContentDepth:
    """Avoid manufacturing a second sentence from one semantic item."""

    reception = plan.response_plan.human_reception_plan
    if reception is None or source_depth != "focused":
        return source_depth
    substantive = tuple(
        item for item in reception.opportunities if item.family != "counterdirection"
    )
    safety_required = bool(
        plan.safety_policy.identity_claim_must_not_be_accepted_as_fact
        or any(item.safety_required for item in reception.opportunities)
    )
    if len(substantive) == 1 and not _ranked_relations(plan) and not safety_required:
        return "minimal"
    return source_depth


def _select_unit_candidates(
    plan: GroundedObservationPlan,
    *,
    depth: ReceptionContentDepth,
) -> tuple[ReceptionContentUnitV2, ...]:
    reception = plan.response_plan.human_reception_plan
    if reception is None or not reception.opportunities:
        raise ReceptionContentPlanV2Error("content_plan_opportunity_missing")

    opportunities = tuple(reception.opportunities)
    counter = next(
        (item for item in opportunities if item.family == "counterdirection"),
        None,
    )
    required_move = next(
        (
            move
            for move in reception.moves
            if move.required and move.move_role != "bounded_counterposition"
        ),
        reception.moves[0] if reception.moves else None,
    )
    primary = next(
        (
            item
            for item in opportunities
            if item.family != "counterdirection"
            and required_move is not None
            and item.reception_act == required_move.reception_act
            and set((*item.target_nucleus_ids, *item.support_nucleus_ids))
            & set(
                (
                    *required_move.target_nucleus_ids,
                    *required_move.support_nucleus_ids,
                )
            )
        ),
        next(
            (item for item in opportunities if item.family != "counterdirection"),
            opportunities[0],
        ),
    )
    best_relation = _best_relation(plan)
    target_count = {
        "minimal": 1,
        "focused": 2,
        "layered": 4 if len(opportunities) >= 3 else 3,
    }[depth]

    selected: list[ReceptionContentUnitV2] = []

    def append_distinct(candidate: ReceptionContentUnitV2) -> None:
        if candidate.relation_ids and any(
            row.relation_ids
            and row.semantic_signature == candidate.semantic_signature
            for row in selected
        ):
            return
        identity = (
            candidate.role,
            candidate.semantic_signature,
            candidate.target_nucleus_ids,
            candidate.support_nucleus_ids,
            candidate.relation_ids,
        )
        if any(
            identity
            == (
                row.role,
                row.semantic_signature,
                row.target_nucleus_ids,
                row.support_nucleus_ids,
                row.relation_ids,
            )
            for row in selected
        ):
            return
        selected.append(candidate)

    if counter is not None:
        append_distinct(
            _opportunity_unit(
                plan,
                counter,
                role="bounded_counterposition",
                required=True,
                priority=1.0,
            )
        )
    elif plan.safety_policy.identity_claim_must_not_be_accepted_as_fact:
        append_distinct(_safety_counterposition_unit(plan))

    append_distinct(
        _opportunity_unit(
            plan,
            primary,
            role="attention",
            required=True,
            priority=0.95 if not primary.safety_required else 0.99,
        )
    )

    if depth != "minimal" and best_relation is not None:
        append_distinct(_relation_unit(plan, best_relation))

    if depth == "layered":
        for opportunity in opportunities:
            if opportunity is primary or opportunity is counter:
                continue
            append_distinct(
                _opportunity_unit(
                    plan,
                    opportunity,
                    role="connection",
                    required=opportunity.retention == "required"
                    or opportunity.safety_required,
                    priority=0.8
                    + (0.08 if opportunity.retention == "required" else 0.0)
                    + (0.1 if opportunity.safety_required else 0.0),
                )
            )

        for relation in _ranked_relations(plan):
            if best_relation is not None and relation.relation_id == best_relation.relation_id:
                continue
            append_distinct(_relation_unit(plan, relation))
            if len(selected) >= target_count:
                break

    append_distinct(_felt_response_unit(plan, primary))

    if len(selected) < target_count:
        for opportunity in opportunities:
            append_distinct(
                _opportunity_unit(
                    plan,
                    opportunity,
                    role="connection",
                    required=opportunity.retention == "required"
                    or opportunity.safety_required,
                    priority=0.78,
                )
            )
            if len(selected) >= target_count:
                break

    selected = selected[:target_count]
    if len(selected) < target_count:
        raise ReceptionContentPlanV2Error(
            f"content_plan_unit_budget_unfilled:{depth}:{len(selected)}:{target_count}"
        )

    return tuple(
        ReceptionContentUnitV2(
            unit_id=f"cu_{index:02d}",
            role=item.role,
            semantic_signature=item.semantic_signature,
            target_nucleus_ids=item.target_nucleus_ids,
            support_nucleus_ids=item.support_nucleus_ids,
            relation_ids=item.relation_ids,
            evidence_span_ids=item.evidence_span_ids,
            required=item.required,
            priority=item.priority,
            allowed_stance_codes=item.allowed_stance_codes,
            forbidden_claim_codes=item.forbidden_claim_codes,
        )
        for index, item in enumerate(selected, start=1)
    )


def _plan_fingerprint(
    observation_plan: GroundedObservationPlan,
    units: Sequence[ReceptionContentUnitV2],
    depth: str,
) -> str:
    payload = {
        "source_version": RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION,
        "depth": depth,
        "input_profile": asdict(observation_plan.input_profile),
        "nuclei": [
            {
                "id": item.nucleus_id,
                "kind": item.kind,
                "source_span_ids": item.source_span_ids,
                "source_fields": item.source_fields,
                "semantic_frame": asdict(item.semantic_frame),
                "grounding_kind": item.grounding_kind,
                "retention": item.retention,
                "forbidden_inference_codes": item.forbidden_inference_codes,
            }
            for item in observation_plan.nuclei
        ],
        "relations": [asdict(item) for item in observation_plan.relations],
        "unknown_boundaries": [
            asdict(item) for item in observation_plan.unknown_boundaries
        ],
        "safety_policy": asdict(observation_plan.safety_policy),
        "units": [asdict(item) for item in units],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _discourse_constraints(
    units: Sequence[ReceptionContentUnitV2],
) -> ReceptionDiscourseConstraintsV2:
    roles = {item.role for item in units}
    signatures = {item.semantic_signature for item in units}
    allowed: list[str] = ["attention_then_felt"]
    if "significance" in roles:
        allowed.append("attention_significance_felt")
    if signatures & {
        "attention_or_evaluation_shift",
        "value_or_intention_preserved_despite_burden",
        "counterposed_meanings_coexist",
        "distinct_meanings_coexist",
        "identity_claim_and_grounded_counterdirection",
        "continuation_or_refusal_preserved",
    }:
        allowed.append("contrast_then_felt")
    uncertainty_present = bool(
        signatures
        & {
            "connection_kept_uncertain",
            "continuation_or_refusal_preserved",
            "wish_held_with_constraint",
            "attempt_held_with_block",
        }
    )
    action_or_intention_present = bool(
        signatures
        & {
            "concrete_action_recorded",
            "intention_retained",
            "help_seeking_preserved",
        }
    )
    if uncertainty_present and action_or_intention_present:
        allowed.append("uncertainty_then_action")
    if any(item.semantic_signature == "concrete_action_recorded" for item in units):
        allowed.append("action_then_meaning")
    if "bounded_counterposition" in roles:
        allowed.append("burden_then_counterposition")
    if len(units) >= 3:
        allowed.append("parallel_layered")

    counter_ids = [
        item.unit_id for item in units if item.role == "bounded_counterposition"
    ]
    felt_ids = [item.unit_id for item in units if item.role == "felt_response"]
    uncertain_ids = [
        item.unit_id
        for item in units
        if item.semantic_signature in {
            "connection_kept_uncertain",
            "wish_held_with_constraint",
            "attempt_held_with_block",
        }
    ]
    causal_targets = [
        item.unit_id
        for item in units
        if item.role in {"felt_response", "significance"}
    ]
    return ReceptionDiscourseConstraintsV2(
        allowed_strategy_codes=_dedupe(allowed),
        forbidden_strategy_codes=(
            "flat_input_enumeration",
            "unsupported_causal_chain",
            "surface_cue_routing",
        ),
        must_keep_units_separate=tuple(
            (left, right)
            for left in counter_ids
            for right in felt_ids
            if left != right
        ),
        must_not_causal_link_unit_pairs=tuple(
            (left, right)
            for left in uncertain_ids
            for right in causal_targets
            if left != right
        ),
    )


def build_reception_content_plan_v2(
    observation_plan: GroundedObservationPlan,
) -> ReceptionContentPlanV2:
    """Build a deterministic body-free plan from canonical semantic material."""

    if not isinstance(observation_plan, GroundedObservationPlan):
        raise ReceptionContentPlanV2Error("grounded_observation_plan_required")
    if not observation_plan.evidence_ledger_validation.valid:
        raise ReceptionContentPlanV2Error("source_evidence_ledger_invalid")
    reception = observation_plan.response_plan.human_reception_plan
    if reception is None:
        raise ReceptionContentPlanV2Error("human_reception_plan_missing")
    depth = reception.depth_policy.level
    if depth not in _DEPTH_UNIT_RANGE:
        raise ReceptionContentPlanV2Error(f"unsupported_content_depth:{depth}")

    typed_depth = _effective_depth(observation_plan, depth)
    units = _select_unit_candidates(observation_plan, depth=typed_depth)
    budget_values = _SENTENCE_BUDGET[typed_depth]
    fingerprint = _plan_fingerprint(observation_plan, units, typed_depth)
    has_text = observation_plan.input_profile.text_presence == "text_present"
    max_anchor_count = int(
        has_text
        and not observation_plan.safety_policy.identity_claim_must_not_be_accepted_as_fact
    )
    content_plan = ReceptionContentPlanV2(
        schema_version=RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION,
        plan_id=f"rcp2_{fingerprint[:16]}",
        source_observation_plan_version=RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION,
        depth=typed_depth,
        sentence_budget=ReceptionSentenceBudgetV2(*budget_values),
        content_units=units,
        discourse_constraints=_discourse_constraints(units),
        quote_policy=ReceptionQuotePolicyV2(
            mode="optional_single_anchor" if max_anchor_count else "none",
            max_anchor_count=max_anchor_count,
            boundary="phrase" if max_anchor_count else "none",
        ),
        safety_policy_ref=(
            "existing_grounded_safety_policy:"
            + observation_plan.safety_policy.safety_kind
        ),
        required_unit_ids=tuple(
            item.unit_id for item in units if item.required
        ),
        body_free=True,
    )
    issues = validate_reception_content_plan_v2(content_plan, observation_plan)
    if issues:
        raise ReceptionContentPlanV2Error(
            "invalid_reception_content_plan_v2:" + ",".join(issues)
        )
    return content_plan


def validate_reception_content_plan_v2(
    content_plan: ReceptionContentPlanV2,
    observation_plan: GroundedObservationPlan,
) -> tuple[str, ...]:
    """Validate Step 3 ownership, evidence, budget, and body-free invariants."""

    issues: list[str] = []
    if content_plan.schema_version != RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if not _PLAN_ID_RE.fullmatch(content_plan.plan_id):
        issues.append("plan_id_invalid")
    if content_plan.source_observation_plan_version != RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION:
        issues.append("source_observation_plan_version_mismatch")
    if content_plan.body_free is not True:
        issues.append("body_free_false")

    unit_range = _DEPTH_UNIT_RANGE.get(content_plan.depth)
    if unit_range is None:
        issues.append("depth_invalid")
    elif not unit_range[0] <= len(content_plan.content_units) <= unit_range[1]:
        issues.append("depth_unit_budget_mismatch")
    expected_budget = _SENTENCE_BUDGET.get(content_plan.depth)
    if expected_budget and (
        content_plan.sentence_budget.min,
        content_plan.sentence_budget.target,
        content_plan.sentence_budget.max,
    ) != expected_budget:
        issues.append("sentence_budget_mismatch")

    nucleus_index = _nucleus_index(observation_plan)
    relation_index = _relation_index(observation_plan)
    evidence_ids = set(observation_plan.referenced_evidence_span_ids)
    expected_unit_ids = tuple(
        f"cu_{index:02d}"
        for index in range(1, len(content_plan.content_units) + 1)
    )
    actual_unit_ids = tuple(item.unit_id for item in content_plan.content_units)
    if actual_unit_ids != expected_unit_ids:
        issues.append("unit_id_order_invalid")
    if len(actual_unit_ids) != len(set(actual_unit_ids)):
        issues.append("unit_id_duplicate")

    for item in content_plan.content_units:
        prefix = item.unit_id if _UNIT_ID_RE.fullmatch(item.unit_id) else "unit"
        if not item.target_nucleus_ids:
            issues.append(f"{prefix}:target_nucleus_missing")
        for nucleus_id in (*item.target_nucleus_ids, *item.support_nucleus_ids):
            if nucleus_id not in nucleus_index:
                issues.append(f"{prefix}:unknown_nucleus")
        for relation_id in item.relation_ids:
            if relation_id not in relation_index:
                issues.append(f"{prefix}:unknown_relation")
        if not item.evidence_span_ids:
            issues.append(f"{prefix}:evidence_missing")
        elif any(evidence_id not in evidence_ids for evidence_id in item.evidence_span_ids):
            issues.append(f"{prefix}:evidence_unresolved")
        if not 0.0 <= item.priority <= 1.0:
            issues.append(f"{prefix}:priority_out_of_range")
        if not item.allowed_stance_codes:
            issues.append(f"{prefix}:allowed_stance_missing")
        if not item.forbidden_claim_codes:
            issues.append(f"{prefix}:forbidden_claim_missing")
        for code in (
            item.semantic_signature,
            *item.allowed_stance_codes,
            *item.forbidden_claim_codes,
        ):
            if not _CODE_RE.fullmatch(code):
                issues.append(f"{prefix}:body_free_code_invalid")

    required_ids = tuple(
        item.unit_id for item in content_plan.content_units if item.required
    )
    if content_plan.required_unit_ids != required_ids:
        issues.append("required_unit_ids_mismatch")
    if not required_ids:
        issues.append("required_unit_missing")

    serialized = asdict(content_plan)

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key) in _FORBIDDEN_FIELD_NAMES:
                    issues.append(f"body_field_forbidden:{key}")
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)

    walk(serialized)
    return _dedupe(issues)


__all__ = [
    "RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION",
    "RECEPTION_CONTENT_PLAN_V2_SOURCE_VERSION",
    "ReceptionContentPlanV2Error",
    "ReceptionSentenceBudgetV2",
    "ReceptionContentUnitV2",
    "ReceptionDiscourseConstraintsV2",
    "ReceptionQuotePolicyV2",
    "ReceptionContentPlanV2",
    "build_reception_content_plan_v2",
    "validate_reception_content_plan_v2",
]
