# -*- coding: utf-8 -*-
from __future__ import annotations

"""Canonical Grounded SentencePlan / Surface / Recovery implementation (I3-I5).

I5 connects this module once from ``emlis_ai_reply_service``. It consumes one
canonical :class:`GroundedObservationPlan`, binds every
sentence to real request-local ``sN`` Evidence ids, realizes only generic
functional grammar around source anchors, and keeps Safety ownership intact.

The same plan contract covers normal/long input, short-state sufficient input,
truly-limited input, and the self-denial Safety overlay. Recovery never selects
an older fixed body: it rebuilds the same required meaning with progressively
smaller surface shapes.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
import re
from typing import Any, Final, Literal

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import (
    GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
    GroundedHumanReceptionPlan,
    GroundedObservationPlan,
    GroundedSemanticNucleus,
    GroundedSemanticRelation,
    classify_grounded_human_follow_delivery,
    classify_grounded_human_follow_role,
    validate_grounded_human_reception_plan,
)
from emlis_ai_grounded_human_reception import (
    GroundedHumanReceptionSurface,
    GroundedHumanReceptionSurfaceError,
    realize_grounded_human_reception,
    reception_active_acts,
    reception_effective_reference_mode,
    reception_effective_speaker_presence,
    reception_terminal_predicate_kind,
    resolve_grounded_reception_referent,
    validate_grounded_human_reception_surface,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)

GROUND_SENTENCE_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_sentence_plan.i3.v1"
GROUND_SURFACE_RESULT_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_surface.i4.v1"
GROUND_SURFACE_GENERATION_PATH: Final = "grounded_sentence_surface_canonical_v1"
DIRECTIONAL_GROUNDED_RELATION_TYPES: Final = frozenset(
    {
        "temporal_before_after",
        "shift_from_to",
        "user_stated_cause",
        "user_stated_result",
        "attempt_and_block",
        "action_supports_change",
        "evaluation_about_event",
        "self_evaluation_about_state",
        "preserves_despite",
        "continuation_or_refusal",
    }
)

RecoveryStage = Literal[
    "full",
    "optional_removed",
    "integrated",
    "hedged",
    "minimal_grounded",
]
SurfaceStatus = Literal["generated", "separate_safety_owner", "unavailable"]
LineRole = Literal[
    "primary_observation",
    "supporting_observation",
    "relation_observation",
    "limited_scope",
    "fact_boundary",
    "limited_opposition",
    "human_follow",
]
SurfaceFunction = Literal[
    "observe_nuclei",
    "observe_nuclei_with_relations",
    "observe_relation",
    "render_limited_scope",
    "render_fact_boundary",
    "render_limited_opposition",
    "render_human_follow",
]
SurfaceClauseForm = Literal[
    "nominal_anchor",
    "complete_clause",
    "quotative_clause",
    "dependent_clause_group",
]
SurfaceDependencyRole = Literal[
    "standalone",
    "interrogative_quotative",
    "connector_attached",
    "predicate_continuation",
]
RelationSurfaceRole = Literal[
    "dimension_shift",
    "coexisting_contrast",
    "burden_or_constraint_with_progress",
    "provisional_evaluation_to_counterevidence",
    "comparison_to_counterevidence",
    "coexisting_comparison_and_evidence",
    "intention_evidenced_by_action",
    "change_evidenced_by_action",
    "bounded_relation",
]

GROUND_RECOVERY_STAGES: Final[tuple[RecoveryStage, ...]] = (
    "full",
    "optional_removed",
    "integrated",
    "hedged",
    "minimal_grounded",
)
OBSERVATION_SECTION_LABEL: Final = "見えたこと："
RECEPTION_SECTION_LABEL: Final = "Emlisから："
_EVIDENCE_ID_RE: Final = re.compile(r"^s[1-9][0-9]*$")
_SPACE_RE: Final = re.compile(r"\s+")
_LEADING_CONNECTOR_RE: Final = re.compile(
    r"^(?:でも|だけど|けれど|けど|ただ|一方で?|で|そして|"
    r"と[、,]\s*それから|それでも|とはいえ|"
    r"と考えて(?:いたけど|しまって)|とか|という)[、,\s]*"
)
_QUESTION_RE: Final = re.compile(r"[?？]")
_RECEPTION_SENTENCE_END_RE: Final = re.compile(r"[。！？!?]+")
_RECEPTION_QUOTE_RE: Final = re.compile(r"「([^」]*)」")
_RETENTION_RANK: Final = {"optional": 0, "should": 1, "required": 2}
_FRAGMENT_DELETE_TRANSLATION: Final = str.maketrans("", "", "「」?？")
_SEPARATE_SAFETY_KINDS: Final = frozenset(
    {TRIAGE_SAFETY_SUPPORT_REQUIRED, TRIAGE_SAFETY_BLOCKED_EMERGENCY}
)
_SELF_DENIAL_OPPOSITION_RELATION_PREFERENCE: Final = (
    "continuation_or_refusal",
    "preserves_despite",
    "contrast",
    "shift_from_to",
)
_RELATION_LABELS: Final[dict[str, str]] = {
    "temporal_before_after": "時間の前後",
    "shift_from_to": "前から後への変化",
    "contrast": "異なる向き",
    "coexistence": "同時にある状態",
    "user_stated_cause": "入力内で示された理由のつながり",
    "user_stated_result": "入力内で示された結果のつながり",
    "attempt_and_block": "試みと止まり方",
    "wish_and_constraint": "願いと制約の両方",
    "action_supports_change": "考えと行動のつながり",
    "evaluation_about_event": "出来事への評価",
    "self_evaluation_about_state": "自己評価と状態のつながり",
    "preserves_despite": "苦しさの中にも残る向き",
    "uncertain_connection": "入力に置かれた順序上のつながり",
    "continuation_or_refusal": "続けることへの否定",
}
_RELATION_REALIZING_FUNCTIONS: Final = frozenset(
    {
        "observe_nuclei_with_relations",
        "observe_relation",
        "render_limited_scope",
        "render_limited_opposition",
    }
)


class GroundedSentenceSurfaceError(ValueError):
    """Raised when the isolated I3/I4 contract cannot be satisfied."""


@dataclass(frozen=True)
class SurfaceClauseUnit:
    """Ephemeral source-bound clause shape used only during realization."""

    source_span_ids: tuple[str, ...]
    dependency_role: SurfaceDependencyRole
    surface_text: str
    surface_form: SurfaceClauseForm
    terminal_predicate_kind: str


@dataclass(frozen=True)
class GroundedSentenceBinding:
    sentence_id: str
    line_role: LineRole
    nucleus_ids: tuple[str, ...]
    relation_ids: tuple[str, ...]
    evidence_span_ids: tuple[str, ...]
    claim_scope: str
    functional_atom_ids: tuple[str, ...]
    contains_question: bool
    required: bool


@dataclass(frozen=True)
class GroundedSentencePlanLine:
    binding: GroundedSentenceBinding
    surface_function: SurfaceFunction


@dataclass(frozen=True)
class GroundedSentencePlan:
    schema_version: str
    generation_path: str
    source_plan_schema_version: str
    source_plan_generation_path: str
    recovery_stage: RecoveryStage
    status: SurfaceStatus
    lines: tuple[GroundedSentencePlanLine, ...]
    required_nucleus_ids: tuple[str, ...]
    covered_required_nucleus_ids: tuple[str, ...]
    required_relation_ids: tuple[str, ...]
    covered_required_relation_ids: tuple[str, ...]
    unresolved_evidence_span_ids: tuple[str, ...]
    fact_boundary_covered: bool
    human_follow_covered: bool
    limited_opposition_covered: bool
    coverage_delegated_to_separate_safety_owner: bool

    def as_body_free_meta(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "raw_input_included": False,
                "raw_text_included": False,
                "surface_text_included": False,
                "comment_text_included": False,
                "public_reply_path_connected": True,
                "completed_semantic_template_used": False,
                "label_assembly_used": False,
                "fixture_semantic_pattern_used": False,
                "synthetic_evidence_id_used": False,
            }
        )
        return payload


@dataclass(frozen=True)
class GroundedSurfaceLine:
    sentence_id: str
    text: str
    binding: GroundedSentenceBinding


@dataclass(frozen=True)
class GroundedSurfaceResult:
    schema_version: str
    generation_path: str
    status: SurfaceStatus
    recovery_stage: RecoveryStage
    text: str
    lines: tuple[GroundedSurfaceLine, ...]
    required_nucleus_ids: tuple[str, ...]
    covered_required_nucleus_ids: tuple[str, ...]
    required_relation_ids: tuple[str, ...]
    covered_required_relation_ids: tuple[str, ...]
    unresolved_evidence_span_ids: tuple[str, ...]
    required_coverage_preserved: bool
    fact_boundary_covered: bool
    human_follow_covered: bool
    limited_opposition_covered: bool
    public_reply_path_connected: bool = True
    completed_semantic_template_used: bool = False
    label_assembly_used: bool = False
    fixture_semantic_pattern_used: bool = False
    synthetic_evidence_id_used: bool = False

    def as_body_free_meta(self) -> dict[str, Any]:
        _observation, _reception, two_stage_issues = split_two_stage_surface(self.text)
        return {
            "schema_version": self.schema_version,
            "generation_path": self.generation_path,
            "status": self.status,
            "recovery_stage": self.recovery_stage,
            "sentence_count": len(self.lines),
            "required_nucleus_ids": list(self.required_nucleus_ids),
            "covered_required_nucleus_ids": list(self.covered_required_nucleus_ids),
            "required_relation_ids": list(self.required_relation_ids),
            "covered_required_relation_ids": list(self.covered_required_relation_ids),
            "unresolved_evidence_span_ids": list(self.unresolved_evidence_span_ids),
            "required_coverage_preserved": self.required_coverage_preserved,
            "fact_boundary_covered": self.fact_boundary_covered,
            "human_follow_covered": self.human_follow_covered,
            "limited_opposition_covered": self.limited_opposition_covered,
            "raw_input_included": False,
            "raw_text_included": False,
            "surface_text_included": False,
            "comment_text_included": False,
            "public_reply_path_connected": self.public_reply_path_connected,
            "completed_semantic_template_used": self.completed_semantic_template_used,
            "label_assembly_used": self.label_assembly_used,
            "fixture_semantic_pattern_used": self.fixture_semantic_pattern_used,
            "synthetic_evidence_id_used": self.synthetic_evidence_id_used,
            "two_stage_required": self.status == "generated",
            "two_stage_contract_passed": bool(
                self.status == "generated" and not two_stage_issues
            ),
            "two_stage_rejection_reasons": list(two_stage_issues),
            "two_stage_observation_section_present": bool(_observation),
            "two_stage_reception_section_present": bool(_reception),
        }


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any]) -> tuple[str, ...]:
    out: list[str] = []
    for value in values or ():
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _span_number(span_id: str) -> tuple[int, str]:
    value = _clean(span_id)
    if _EVIDENCE_ID_RE.fullmatch(value):
        return (int(value[1:]), value)
    return (10**9, value)


def _nucleus_order(item: GroundedSemanticNucleus) -> tuple[int, int, float, tuple[int, str]]:
    return (
        -_RETENTION_RANK.get(item.retention, 0),
        0 if any(field in {"memo", "memo_action"} for field in item.source_fields) else 1,
        -float(item.priority),
        _span_number(item.source_span_ids[0] if item.source_span_ids else ""),
    )


def _nucleus_source_order(item: GroundedSemanticNucleus) -> tuple[int, tuple[int, str]]:
    fields = set(item.source_fields)
    if "memo" in fields:
        field_order = 0
    elif "memo_action" in fields:
        field_order = 1
    else:
        field_order = 2
    return (field_order, _span_number(item.source_span_ids[0] if item.source_span_ids else ""))


def _binding_evidence_ids(
    *,
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            _dedupe(
                [
                    *[
                        span_id
                        for nucleus_id in nucleus_ids
                        if nucleus_id in nucleus_index
                        for span_id in nucleus_index[nucleus_id].source_span_ids
                    ],
                    *[
                        span_id
                        for relation_id in relation_ids
                        if relation_id in relation_index
                        for span_id in relation_index[relation_id].source_span_ids
                    ],
                ]
            ),
            key=_span_number,
        )
    )


def _claim_scope(plan: GroundedObservationPlan) -> str:
    if plan.safety_policy.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        return "self_denial_fact_boundary_overlay"
    if plan.input_profile.material_quality == "limited_grounding":
        return "limited_grounding_no_event_completion"
    if plan.input_profile.material_quality == "labels_only_limited":
        return "selected_labels_only"
    return "single_input_bounded_observation"


def expected_human_follow_role(
    plan: GroundedObservationPlan,
    nucleus_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> str:
    """Reconfirm the Plan-owned role and reject incompatible target pairs."""

    nuclei = tuple(nucleus_index[item] for item in nucleus_ids if item in nucleus_index)
    if not nuclei:
        raise GroundedSentenceSurfaceError("human_follow_role_target_mismatch")
    attributes = {
        code
        for nucleus in nuclei
        for code in nucleus.semantic_frame.attribute_codes
    }
    role = classify_grounded_human_follow_role(
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
        required_nucleus_count=len(plan.coverage_requirements.required_nucleus_ids),
        nuclei=nuclei,
    )
    intention_target = any(
        nucleus.kind == "wish"
        or nucleus.semantic_frame.modality in {"wish", "intention"}
        or "semantic_role:retained_intention" in nucleus.semantic_frame.attribute_codes
        for nucleus in nuclei
    )
    if intention_target and role == "valued_change":
        raise GroundedSentenceSurfaceError("intention_misclassified_as_change")
    if "operator:help_seeking" in attributes and role != "help_seeking_preserved":
        raise GroundedSentenceSurfaceError("help_seeking_role_missing")
    protective_target = bool(
        plan.safety_policy.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and (
            "semantic_role:protective_or_limiting_refusal" in attributes
            or any(nucleus.semantic_frame.modality == "refusal" for nucleus in nuclei)
        )
    )
    if protective_target and role not in {
        "protective_counterdirection",
        "help_seeking_preserved",
    }:
        raise GroundedSentenceSurfaceError("protective_counterdirection_misclassified")
    if (
        any(nucleus.kind == "action" for nucleus in nuclei)
        and role == "retained_intention"
        and not intention_target
    ):
        raise GroundedSentenceSurfaceError("human_follow_role_target_mismatch")
    return role


def relation_surface_role(
    relation: GroundedSemanticRelation,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> RelationSurfaceRole:
    """Classify compositional relation grammar from endpoint semantics."""

    left = nucleus_index.get(relation.from_nucleus_id)
    right = nucleus_index.get(relation.to_nucleus_id)
    if left is None or right is None:
        return "bounded_relation"
    left_attributes = set(left.semantic_frame.attribute_codes)
    right_attributes = set(right.semantic_frame.attribute_codes)
    if relation.type == "action_supports_change":
        if (
            left.kind == "wish"
            or left.semantic_frame.modality in {"wish", "intention"}
            or "semantic_role:retained_intention" in left_attributes
        ):
            return "intention_evidenced_by_action"
        return "change_evidenced_by_action"
    if relation.type == "shift_from_to":
        return "dimension_shift"
    if (
        "semantic_role:provisional_evaluation" in left_attributes
        and "semantic_role:counterevidence" in right_attributes
    ):
        return "provisional_evaluation_to_counterevidence"
    if (
        left.kind == "self_evaluation"
        and "semantic_role:current_change" in right_attributes
    ):
        return "comparison_to_counterevidence"
    if relation.type == "preserves_despite" and (
        left.kind in {"reaction", "state", "constraint"}
        or left.semantic_frame.modality in {"feeling", "refusal"}
        or "semantic_role:limiting_unknown" in left_attributes
    ) and (
        right.kind in {"action", "change", "wish"}
        or "semantic_role:current_change" in right_attributes
        or "semantic_role:contrast_after" in right_attributes
    ):
        return "burden_or_constraint_with_progress"
    if relation.type == "contrast" and (
        "semantic_role:contrast_before" in left_attributes
        and "semantic_role:current_change" in right_attributes
        and "semantic_role:limiting_unknown" not in left_attributes
    ):
        return "coexisting_comparison_and_evidence"
    if relation.type in {"contrast", "coexistence", "preserves_despite"}:
        return "coexisting_contrast"
    return "bounded_relation"


def _relation_surface_atoms(
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[str, ...]:
    atoms: list[str] = []
    for relation_id in relation_ids:
        relation = relation_index.get(relation_id)
        if relation is None:
            continue
        role = relation_surface_role(relation, nucleus_index)
        atoms.extend((f"relation_surface:{role}", f"relation_surface_role:{role}"))
        left = nucleus_index.get(relation.from_nucleus_id)
        right = nucleus_index.get(relation.to_nucleus_id)
        if left is not None:
            atoms.append(f"relation_endpoint:left:{_semantic_endpoint_surface_form(left)}")
        if right is not None:
            atoms.append(f"relation_endpoint:right:{_semantic_endpoint_surface_form(right)}")
        if role == "coexisting_comparison_and_evidence":
            atoms.append("relation_surface:coexisting_contrast")
    return _dedupe(atoms)


def _observation_surface_role(
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> str:
    relation_roles = tuple(
        relation_surface_role(relation_index[item], nucleus_index)
        for item in relation_ids
        if item in relation_index
    )
    if relation_roles:
        return relation_roles[0]
    nuclei = tuple(
        nucleus_index[item] for item in nucleus_ids if item in nucleus_index
    )
    attributes = {
        code
        for nucleus in nuclei
        for code in nucleus.semantic_frame.attribute_codes
    }
    if (
        "semantic_role:explicit_evaluation" in attributes
        and "semantic_role:current_change" in attributes
    ):
        return "evaluated_change_arc"
    if (
        "semantic_role:initial_condition" in attributes
        and "semantic_role:current_change" in attributes
    ):
        return "change_direction_arc"
    if (
        "semantic_role:current_change" in attributes
        and any(
            nucleus.kind == "action" or "operator:action" in nucleus.semantic_frame.attribute_codes
            for nucleus in nuclei
        )
    ):
        return "action_change_arc"
    if (
        "semantic_role:retained_intention" in attributes
        and "semantic_role:limiting_unknown" in attributes
    ):
        return "retained_intention_with_unknown_arc"
    if (
        "semantic_role:retained_intention" in attributes
        and any(
            nucleus.kind == "action"
            or "semantic_role:concrete_action" in nucleus.semantic_frame.attribute_codes
            for nucleus in nuclei
        )
    ):
        return "retained_intention_with_preparation_arc"
    if "semantic_role:retained_intention" in attributes:
        return "retained_intention_arc"
    if "semantic_role:current_change" in attributes:
        return "current_change_arc"
    if all(nucleus.kind in {"state", "reaction", "constraint"} for nucleus in nuclei):
        return "state_arc"
    return "coexisting_observation"


def _observation_surface_atoms(
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[str, ...]:
    role = _observation_surface_role(
        nucleus_ids,
        relation_ids,
        nucleus_index,
        relation_index,
    )
    return (
        f"observation_surface_role:{role}",
        f"semantic_arc:{role}",
    )


def _reception_contract_atoms(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: RecoveryStage,
) -> tuple[str, ...]:
    acts = reception_active_acts(reception_plan, recovery_stage)
    secondary_follow_elements = (
        reception_plan.secondary_follow_elements
        if recovery_stage == "full"
        else ()
    )
    afterglow_follow_element = (
        reception_plan.afterglow_follow_element
        if recovery_stage == "full"
        else None
    )
    return _dedupe(
        (
            *[f"reception_act:{act}" for act in acts],
            *(
                (
                    f"reception_follow_primary:"
                    f"{reception_plan.primary_follow_element}",
                )
                if reception_plan.primary_follow_element is not None
                else ()
            ),
            *[
                f"reception_follow_secondary:{element}"
                for element in secondary_follow_elements
            ],
            *(
                (
                    f"reception_follow_afterglow:"
                    f"{afterglow_follow_element}",
                )
                if afterglow_follow_element is not None
                else ()
            ),
            *(
                (f"reception_stance:{reception_plan.stance}",)
                if reception_plan.stance is not None
                else ()
            ),
            *(
                (
                    "reception_speaker:"
                    f"{reception_effective_speaker_presence(reception_plan, recovery_stage)}",
                )
            ),
            (
                "reception_reference:"
                f"{reception_effective_reference_mode(reception_plan, recovery_stage)}"
            ),
            f"reception_quote_policy:{reception_plan.quote_policy.mode}",
            f"reception_quote_anchor_max:{reception_plan.quote_policy.max_anchor_count}",
            (
                "reception_quote_visible_chars_max:"
                f"{reception_plan.quote_policy.max_anchor_visible_chars}"
            ),
            "reception_sentence_budget:one_or_two",
            f"reception_sentence_min:{reception_plan.sentence_policy.min_sentences}",
            f"reception_sentence_max:{reception_plan.sentence_policy.max_sentences}",
            "reception_distinctness:required",
            *[
                "reception_terminal_predicate:"
                f"{reception_terminal_predicate_kind(act)}"
                for act in acts
            ],
        )
    )


def _human_follow_atoms(
    role: str,
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: RecoveryStage,
    *,
    target_already_delivered: bool = False,
) -> tuple[str, ...]:
    modality = {
        "retained_intention": "intention",
        "protective_counterdirection": "protective_counterdirection",
        "help_seeking_preserved": "help_seeking",
        "concrete_effort": "action",
        "valued_change": "change",
        "integrated_current_state": "current_state",
        "burden_expression": "burden",
    }.get(role, "bounded_observation")
    return _dedupe(
        (
            "evidence_bound_human_follow",
            f"human_follow:{role}",
            f"human_follow_contribution:{role}",
            "human_follow_delivery:separate",
            "closure_role:human_follow",
            f"closure_modality:{modality}",
            "closure_scope:selected_target",
            *_reception_contract_atoms(reception_plan, recovery_stage),
            *(
                ("human_follow_target_already_delivered",)
                if target_already_delivered
                else ()
            ),
        )
    )


def _required_reception_plan(
    plan: GroundedObservationPlan,
    follow_ids: Sequence[str],
) -> GroundedHumanReceptionPlan:
    reception_plan = plan.response_plan.human_reception_plan
    if reception_plan is None or not reception_plan.required:
        raise GroundedSentenceSurfaceError("human_reception_plan_missing")
    if tuple(reception_plan.target_nucleus_ids) != tuple(follow_ids):
        raise GroundedSentenceSurfaceError("human_reception_target_mismatch")
    return reception_plan


def _semantic_endpoint_surface_form(
    nucleus: GroundedSemanticNucleus,
) -> SurfaceClauseForm:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if "semantic_role:embedded_turn" in attributes:
        return "dependent_clause_group"
    if nucleus.semantic_frame.modality in {"wish", "intention", "uncertain"}:
        return "quotative_clause"
    if nucleus.semantic_frame.predicate_kind:
        return "complete_clause"
    return "nominal_anchor"


def _make_line(
    *,
    sentence_number: int,
    line_role: LineRole,
    surface_function: SurfaceFunction,
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    claim_scope: str,
    recovery_stage: RecoveryStage,
    required: bool = True,
    extra_atoms: Sequence[str] = (),
) -> GroundedSentencePlanLine:
    atom_ids = _dedupe(
        [
            *(
                ("source_anchor_quote",)
                if surface_function != "render_human_follow"
                else ()
            ),
            f"surface_function:{surface_function}",
            f"line_role:{line_role}",
            f"recovery:{recovery_stage}",
            *[f"relation:{relation_index[item].type}" for item in relation_ids if item in relation_index],
            *_relation_surface_atoms(
                relation_ids,
                nucleus_index,
                relation_index,
            ),
            *(
                _observation_surface_atoms(
                    nucleus_ids,
                    relation_ids,
                    nucleus_index,
                    relation_index,
                )
                if surface_function
                in {
                    "observe_nuclei",
                    "observe_nuclei_with_relations",
                    "observe_relation",
                }
                else ()
            ),
            *extra_atoms,
        ]
    )
    binding = GroundedSentenceBinding(
        sentence_id=f"sentence:{sentence_number}",
        line_role=line_role,
        nucleus_ids=_dedupe(nucleus_ids),
        relation_ids=_dedupe(relation_ids),
        evidence_span_ids=_binding_evidence_ids(
            nucleus_ids=nucleus_ids,
            relation_ids=relation_ids,
            nucleus_index=nucleus_index,
            relation_index=relation_index,
        ),
        claim_scope=claim_scope,
        functional_atom_ids=atom_ids,
        contains_question=False,
        required=required,
    )
    return GroundedSentencePlanLine(binding=binding, surface_function=surface_function)


def _internal_relation_ids(
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[str, ...]:
    included = set(nucleus_ids)
    return tuple(
        relation_id
        for relation_id in relation_ids
        if relation_id in relation_index
        and relation_index[relation_id].from_nucleus_id in included
        and relation_index[relation_id].to_nucleus_id in included
    )


def _directionally_order_group(
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[str, ...]:
    """Keep a relation chain's ``from`` nucleus before its ``to`` nucleus.

    Source position remains the stable tie-breaker for unrelated nuclei.  If a
    malformed relation cycle is ever supplied, retain source order so this
    planner does not invent an arbitrary direction; validation remains owned by
    the canonical gate.
    """

    selected = tuple(
        sorted(
            (item for item in nucleus_ids if item in nucleus_index),
            key=lambda item: _nucleus_source_order(nucleus_index[item]),
        )
    )
    selected_set = set(selected)
    outgoing = {item: set() for item in selected}
    indegree = {item: 0 for item in selected}
    for relation_id in relation_ids:
        relation = relation_index.get(relation_id)
        if (
            relation is None
            or relation.type not in DIRECTIONAL_GROUNDED_RELATION_TYPES
            or relation.from_nucleus_id not in selected_set
            or relation.to_nucleus_id not in selected_set
            or relation.from_nucleus_id == relation.to_nucleus_id
            or relation.to_nucleus_id in outgoing[relation.from_nucleus_id]
        ):
            continue
        outgoing[relation.from_nucleus_id].add(relation.to_nucleus_id)
        indegree[relation.to_nucleus_id] += 1

    ready = [item for item in selected if indegree[item] == 0]
    ordered: list[str] = []
    while ready:
        ready.sort(key=lambda item: _nucleus_source_order(nucleus_index[item]))
        current = ready.pop(0)
        ordered.append(current)
        for target in sorted(
            outgoing[current],
            key=lambda item: _nucleus_source_order(nucleus_index[item]),
        ):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return tuple(ordered) if len(ordered) == len(selected) else selected


def _relation_aware_groups(
    nucleus_ids: Sequence[str],
    relation_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    *,
    max_groups: int,
) -> tuple[tuple[str, ...], ...]:
    """Integrate required relation chains without dropping their endpoints."""

    selected = tuple(item for item in nucleus_ids if item in nucleus_index)
    if not selected:
        return ()
    parent = {item: item for item in selected}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    selected_set = set(selected)
    for relation_id in relation_ids:
        relation = relation_index.get(relation_id)
        if relation is None:
            continue
        if (
            relation.from_nucleus_id in selected_set
            and relation.to_nucleus_id in selected_set
        ):
            union(relation.from_nucleus_id, relation.to_nucleus_id)

    components: dict[str, list[str]] = {}
    for nucleus_id in selected:
        components.setdefault(find(nucleus_id), []).append(nucleus_id)
    groups = [
        sorted(values, key=lambda item: _nucleus_source_order(nucleus_index[item]))
        for values in components.values()
    ]
    groups.sort(key=lambda group: _nucleus_source_order(nucleus_index[group[0]]))

    target = max(1, int(max_groups))
    while len(groups) > target:
        merge_at = min(
            range(len(groups) - 1),
            key=lambda index: (len(groups[index]) + len(groups[index + 1]), index),
        )
        merged = sorted(
            [*groups[merge_at], *groups[merge_at + 1]],
            key=lambda item: _nucleus_source_order(nucleus_index[item]),
        )
        groups[merge_at : merge_at + 2] = [merged]
    return tuple(
        _directionally_order_group(
            group,
            relation_ids,
            nucleus_index,
            relation_index,
        )
        for group in groups
    )


def _merge_homogeneous_state_groups(
    groups: Sequence[Sequence[str]],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> tuple[tuple[str, ...], ...]:
    """Merge adjacent source-local state nuclei without dropping identity."""

    state_kinds = {"state", "reaction", "constraint"}
    merged: list[list[str]] = []
    for group in groups:
        current = list(group)
        if not current:
            continue
        current_nuclei = [nucleus_index[item] for item in current]
        current_fields = {
            field for nucleus in current_nuclei for field in nucleus.source_fields
        }
        current_state_like = all(nucleus.kind in state_kinds for nucleus in current_nuclei)
        if merged:
            previous_nuclei = [nucleus_index[item] for item in merged[-1]]
            previous_fields = {
                field for nucleus in previous_nuclei for field in nucleus.source_fields
            }
            previous_state_like = all(
                nucleus.kind in state_kinds for nucleus in previous_nuclei
            )
            if (
                current_state_like
                and previous_state_like
                and len(current_fields) == 1
                and current_fields == previous_fields
            ):
                merged[-1].extend(current)
                continue
        merged.append(current)
    return tuple(tuple(group) for group in merged)


def _clause_structure_atoms(
    nucleus_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> tuple[str, ...]:
    attributes = {
        code
        for nucleus_id in nucleus_ids
        if nucleus_id in nucleus_index
        for code in nucleus_index[nucleus_id].semantic_frame.attribute_codes
    }
    atoms: list[str] = []
    if {
        "semantic_role:initial_condition",
        "semantic_role:embedded_turn",
    } <= attributes:
        atoms.extend(("surface_unit:complete_clause", "dependency:quotative_continuation"))
    return _dedupe(atoms)


def _self_denial_opposition_relation(
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> GroundedSemanticRelation | None:
    """Return a required, input-grounded relation that limits self-denial.

    A relation counts only when it joins a fact-boundary self-evaluation to a
    distinct required nucleus whose wording supplies refusal, positive/change
    direction, or a contrast.  This keeps the overlay source-bound and avoids
    turning mere adjacency into generic reassurance.
    """

    fact_ids = set(plan.response_plan.fact_boundary_nucleus_ids)
    required_relation_ids = set(plan.coverage_requirements.required_relation_ids)
    preference = {
        relation_type: index
        for index, relation_type in enumerate(_SELF_DENIAL_OPPOSITION_RELATION_PREFERENCE)
    }
    candidates: list[tuple[int, tuple[int, str], GroundedSemanticRelation]] = []
    for relation in relation_index.values():
        if relation.relation_id not in required_relation_ids:
            continue
        endpoints = (relation.from_nucleus_id, relation.to_nucleus_id)
        boundary_endpoints = [item for item in endpoints if item in fact_ids]
        other_endpoints = [item for item in endpoints if item not in fact_ids]
        if len(boundary_endpoints) != 1 or len(other_endpoints) != 1:
            continue
        other = nucleus_index.get(other_endpoints[0])
        if other is None:
            continue
        if relation.type == "continuation_or_refusal":
            qualifies = True
        elif relation.type in {"preserves_despite", "contrast"}:
            # The explicit contrast itself is the bounded evidence that the
            # record contains another direction; no positive personality or
            # outcome needs to be inferred from the second clause.
            qualifies = other.kind != "self_evaluation"
        elif relation.type == "shift_from_to":
            qualifies = bool(
                other.semantic_frame.modality == "refusal"
                or other.semantic_frame.polarity in {"positive", "mixed"}
                or other.kind in {"action", "change", "wish", "value"}
            )
        else:
            qualifies = False
        if not qualifies:
            continue
        candidates.append(
            (
                preference.get(relation.type, len(preference)),
                _span_number(relation.source_span_ids[0] if relation.source_span_ids else ""),
                relation,
            )
        )
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def _build_self_denial_lines(
    *,
    plan: GroundedObservationPlan,
    recovery_stage: RecoveryStage,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[GroundedSentencePlanLine, ...]:
    lines: list[GroundedSentencePlanLine] = []
    sentence_number = 1
    claim_scope = _claim_scope(plan)

    follow_ids = tuple(
        item
        for item in plan.response_plan.human_follow_target_ids
        if item in nucleus_index
    )
    follow_role = (
        expected_human_follow_role(plan, follow_ids, nucleus_index)
        if follow_ids
        else ""
    )
    follow_delivery = classify_grounded_human_follow_delivery(
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
        required_nucleus_count=len(plan.coverage_requirements.required_nucleus_ids),
        target_nuclei=tuple(nucleus_index[item] for item in follow_ids),
        relations=tuple(relation_index.values()),
        required_relation_ids=plan.coverage_requirements.required_relation_ids,
        fact_boundary_nucleus_ids=plan.response_plan.fact_boundary_nucleus_ids,
    )

    fact_ids = tuple(item for item in plan.response_plan.fact_boundary_nucleus_ids if item in nucleus_index)
    if fact_ids:
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="fact_boundary",
                surface_function="render_fact_boundary",
                nucleus_ids=fact_ids,
                relation_ids=(),
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                extra_atoms=("identity_claim_not_fact", "single_input_scope"),
            )
        )
        sentence_number += 1

    opposition = _self_denial_opposition_relation(
        plan,
        nucleus_index,
        relation_index,
    )
    covered_relation_ids: set[str] = set()
    if opposition is not None:
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="limited_opposition",
                surface_function="render_limited_opposition",
                nucleus_ids=(opposition.from_nucleus_id, opposition.to_nucleus_id),
                relation_ids=(opposition.relation_id,),
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                extra_atoms=(
                    "input_grounded_opposition",
                    "no_identity_acceptance",
                ),
            )
        )
        covered_relation_ids.add(opposition.relation_id)
        sentence_number += 1

    covered = {
        nucleus_id
        for line in lines
        for nucleus_id in line.binding.nucleus_ids
    }
    remaining = tuple(
        nucleus_id
        for nucleus_id in plan.coverage_requirements.required_nucleus_ids
        if nucleus_id in nucleus_index and nucleus_id not in covered
    )
    if remaining:
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="supporting_observation",
                surface_function="observe_nuclei",
                nucleus_ids=remaining,
                relation_ids=(),
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                extra_atoms=("soft_observation_ending",),
            )
        )
        sentence_number += 1

    for relation_id in plan.coverage_requirements.required_relation_ids:
        if relation_id in covered_relation_ids or relation_id not in relation_index:
            continue
        relation = relation_index[relation_id]
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="relation_observation",
                surface_function="observe_relation",
                nucleus_ids=(relation.from_nucleus_id, relation.to_nucleus_id),
                relation_ids=(relation_id,),
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                required=True,
                extra_atoms=("soft_relation_ending",),
            )
        )
        covered_relation_ids.add(relation_id)
        sentence_number += 1

    if (
        plan.coverage_requirements.human_follow_required
        and follow_ids
    ):
        reception_plan = _required_reception_plan(plan, follow_ids)
        reception_nucleus_ids = _dedupe(
            (
                *reception_plan.target_nucleus_ids,
                *reception_plan.support_nucleus_ids,
            )
        )
        if follow_delivery != "separate_distinct_contribution":
            raise GroundedSentenceSurfaceError(
                "mandatory_two_stage_follow_delivery_not_separate"
            )
        target_already_delivered = any(
            set(follow_ids).intersection(line.binding.nucleus_ids)
            for line in lines
        )
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="human_follow",
                surface_function="render_human_follow",
                nucleus_ids=reception_nucleus_ids,
                relation_ids=(),
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                extra_atoms=(
                    *_human_follow_atoms(
                        follow_role,
                        reception_plan,
                        recovery_stage,
                        target_already_delivered=target_already_delivered,
                    ),
                    "no_personality_guarantee",
                    "no_action_instruction",
                ),
            )
        )
    return tuple(lines)


def _build_regular_lines(
    *,
    plan: GroundedObservationPlan,
    recovery_stage: RecoveryStage,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
) -> tuple[GroundedSentencePlanLine, ...]:
    required_ids = tuple(
        item.nucleus_id
        for item in sorted(
            (nucleus_index[item] for item in plan.coverage_requirements.required_nucleus_ids if item in nucleus_index),
            key=_nucleus_order,
        )
    )
    should_ids = tuple(
        item.nucleus_id
        for item in sorted(
            (
                nucleus
                for nucleus in nucleus_index.values()
                if nucleus.retention == "should" and nucleus.nucleus_id not in required_ids
            ),
            key=_nucleus_order,
        )
    )
    optional_ids = tuple(
        item.nucleus_id
        for item in sorted(
            (
                nucleus
                for nucleus in nucleus_index.values()
                if nucleus.retention == "optional"
                and nucleus.nucleus_id not in required_ids
                and nucleus.nucleus_id not in should_ids
            ),
            key=_nucleus_order,
        )
    )
    if recovery_stage == "full":
        # The unreduced plan may carry one bounded supporting item, but not at
        # the expense of the public two-stage body's readability.  Once the
        # required semantic set is already large, adding a non-required item
        # recreates the ledger-style enumeration that this repair removes.
        selected_ids = _dedupe(
            [
                *required_ids,
                *(should_ids[:1] if len(required_ids) <= 5 else ()),
            ]
        )
        max_observation_groups = 3
    elif recovery_stage == "optional_removed":
        selected_ids = required_ids
        max_observation_groups = 3
    elif recovery_stage in {"integrated", "hedged"}:
        selected_ids = required_ids
        max_observation_groups = 2
    else:
        selected_ids = required_ids
        max_observation_groups = 1

    claim_scope = _claim_scope(plan)
    required_relation_ids = tuple(
        item for item in plan.coverage_requirements.required_relation_ids if item in relation_index
    )
    relation_candidates = required_relation_ids
    selected_ids = tuple(
        item.nucleus_id
        for item in sorted(
            (nucleus_index[item] for item in selected_ids if item in nucleus_index),
            key=_nucleus_source_order,
        )
    )

    lines: list[GroundedSentencePlanLine] = []
    covered_relations: set[str] = set()
    sentence_number = 1
    hedge_atoms = ("scope_hedge",) if recovery_stage == "hedged" else ()

    material_quality = plan.input_profile.material_quality
    follow_ids = tuple(item for item in plan.response_plan.human_follow_target_ids if item in nucleus_index)
    follow_role = expected_human_follow_role(plan, follow_ids, nucleus_index) if follow_ids else ""
    follow_delivery = classify_grounded_human_follow_delivery(
        safety_kind=plan.safety_policy.safety_kind,
        material_quality=plan.input_profile.material_quality,
        required_nucleus_count=len(plan.coverage_requirements.required_nucleus_ids),
        target_nuclei=tuple(nucleus_index[item] for item in follow_ids),
        relations=tuple(relation_index.values()),
        required_relation_ids=plan.coverage_requirements.required_relation_ids,
        fact_boundary_nucleus_ids=plan.response_plan.fact_boundary_nucleus_ids,
    )
    if (
        plan.coverage_requirements.human_follow_required
        and follow_ids
        and follow_delivery != "separate_distinct_contribution"
    ):
        raise GroundedSentenceSurfaceError(
            "mandatory_two_stage_follow_delivery_not_separate"
        )
    if material_quality in {"limited_grounding", "labels_only_limited"}:
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="limited_scope",
                surface_function="render_limited_scope",
                nucleus_ids=selected_ids,
                relation_ids=required_relation_ids,
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                extra_atoms=(
                    "no_event_completion",
                    "no_reason_completion",
                    "single_input_scope",
                ),
            )
        )
        covered_relations.update(required_relation_ids)
        sentence_number += 1
    else:
        groups = _relation_aware_groups(
            selected_ids,
            relation_candidates,
            nucleus_index,
            relation_index,
            max_groups=max_observation_groups,
        )
        groups = _merge_homogeneous_state_groups(groups, nucleus_index)
        for group_index, group in enumerate(groups):
            internal_relations = _internal_relation_ids(group, relation_candidates, relation_index)
            covered_relations.update(internal_relations)
            lines.append(
                _make_line(
                    sentence_number=sentence_number,
                    line_role="primary_observation" if group_index == 0 else "supporting_observation",
                    surface_function=(
                        "observe_nuclei_with_relations"
                        if internal_relations
                        else "observe_nuclei"
                    ),
                    nucleus_ids=group,
                    relation_ids=internal_relations,
                    nucleus_index=nucleus_index,
                    relation_index=relation_index,
                    claim_scope=claim_scope,
                    recovery_stage=recovery_stage,
                    required=any(item in required_ids for item in group),
                    extra_atoms=(
                        "soft_observation_ending",
                        *_clause_structure_atoms(group, nucleus_index),
                        *hedge_atoms,
                    ),
                )
            )
            sentence_number += 1

        # Recovery may simplify relation wording, but a required relation must
        # still own a rendered line.  Merely attaching its ID to an unrelated
        # nucleus line would satisfy bookkeeping while losing the relation's
        # visible meaning.
        for relation_id in relation_candidates:
            if relation_id in covered_relations:
                continue
            relation = relation_index[relation_id]
            lines.append(
                _make_line(
                    sentence_number=sentence_number,
                    line_role="relation_observation",
                    surface_function="observe_relation",
                    nucleus_ids=(relation.from_nucleus_id, relation.to_nucleus_id),
                    relation_ids=(relation_id,),
                    nucleus_index=nucleus_index,
                    relation_index=relation_index,
                    claim_scope=claim_scope,
                    recovery_stage=recovery_stage,
                    required=relation_id in required_relation_ids,
                    extra_atoms=("soft_relation_ending", *hedge_atoms),
                )
            )
            covered_relations.add(relation_id)
            sentence_number += 1

    if plan.coverage_requirements.human_follow_required and follow_ids:
        reception_plan = _required_reception_plan(plan, follow_ids)
        reception_nucleus_ids = _dedupe(
            (
                *reception_plan.target_nucleus_ids,
                *reception_plan.support_nucleus_ids,
            )
        )
        target_already_delivered = any(
            set(follow_ids).intersection(line.binding.nucleus_ids)
            for line in lines
        )
        lines.append(
            _make_line(
                sentence_number=sentence_number,
                line_role="human_follow",
                surface_function="render_human_follow",
                nucleus_ids=reception_nucleus_ids,
                relation_ids=(),
                nucleus_index=nucleus_index,
                relation_index=relation_index,
                claim_scope=claim_scope,
                recovery_stage=recovery_stage,
                extra_atoms=(
                    *_human_follow_atoms(
                        follow_role,
                        reception_plan,
                        recovery_stage,
                        target_already_delivered=target_already_delivered,
                    ),
                    "no_personality_guarantee",
                    "no_action_instruction",
                ),
            )
        )
    return tuple(lines)


def _coverage_from_lines(
    lines: Sequence[GroundedSentencePlanLine],
    required_nucleus_ids: Sequence[str],
    required_relation_ids: Sequence[str],
    resolver: EvidenceSpanResolver,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    covered_nuclei = _dedupe(
        nucleus_id for line in lines for nucleus_id in line.binding.nucleus_ids
    )
    covered_relations = _dedupe(
        relation_id for line in lines for relation_id in line.binding.relation_ids
    )
    unresolved = _dedupe(
        span_id
        for line in lines
        for span_id in resolver.unresolved_ids(line.binding.evidence_span_ids)
    )
    return (
        tuple(item for item in required_nucleus_ids if item in covered_nuclei),
        tuple(item for item in required_relation_ids if item in covered_relations),
        unresolved,
    )


def build_grounded_sentence_plan(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: RecoveryStage = "full",
) -> GroundedSentencePlan:
    """Build an isolated SentencePlan from the canonical plan only."""

    if recovery_stage not in GROUND_RECOVERY_STAGES:
        raise GroundedSentenceSurfaceError(f"unsupported_recovery_stage:{recovery_stage}")
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    relation_index = {item.relation_id: item for item in plan.relations}
    required_nucleus_ids = tuple(plan.coverage_requirements.required_nucleus_ids)
    required_relation_ids = tuple(plan.coverage_requirements.required_relation_ids)
    safety_kind = plan.safety_policy.safety_kind

    if safety_kind in _SEPARATE_SAFETY_KINDS:
        sentence_plan = GroundedSentencePlan(
            schema_version=GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
            generation_path=GROUND_SURFACE_GENERATION_PATH,
            source_plan_schema_version=plan.schema_version,
            source_plan_generation_path=plan.generation_path,
            recovery_stage=recovery_stage,
            status="separate_safety_owner",
            lines=(),
            required_nucleus_ids=required_nucleus_ids,
            covered_required_nucleus_ids=(),
            required_relation_ids=required_relation_ids,
            covered_required_relation_ids=(),
            unresolved_evidence_span_ids=(),
            fact_boundary_covered=False,
            human_follow_covered=False,
            limited_opposition_covered=False,
            coverage_delegated_to_separate_safety_owner=True,
        )
    elif plan.input_profile.material_quality == "empty":
        sentence_plan = GroundedSentencePlan(
            schema_version=GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
            generation_path=GROUND_SURFACE_GENERATION_PATH,
            source_plan_schema_version=plan.schema_version,
            source_plan_generation_path=plan.generation_path,
            recovery_stage=recovery_stage,
            status="unavailable",
            lines=(),
            required_nucleus_ids=required_nucleus_ids,
            covered_required_nucleus_ids=(),
            required_relation_ids=required_relation_ids,
            covered_required_relation_ids=(),
            unresolved_evidence_span_ids=(),
            fact_boundary_covered=not plan.coverage_requirements.fact_boundary_required,
            human_follow_covered=not plan.coverage_requirements.human_follow_required,
            limited_opposition_covered=False,
            coverage_delegated_to_separate_safety_owner=False,
        )
    else:
        lines = (
            _build_self_denial_lines(
                plan=plan,
                recovery_stage=recovery_stage,
                nucleus_index=nucleus_index,
                relation_index=relation_index,
            )
            if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
            else _build_regular_lines(
                plan=plan,
                recovery_stage=recovery_stage,
                nucleus_index=nucleus_index,
                relation_index=relation_index,
            )
        )
        covered_nuclei, covered_relations, unresolved = _coverage_from_lines(
            lines,
            required_nucleus_ids,
            required_relation_ids,
            resolver,
        )
        roles = {line.binding.line_role for line in lines}
        atoms = {
            atom
            for line in lines
            for atom in line.binding.functional_atom_ids
        }
        sentence_plan = GroundedSentencePlan(
            schema_version=GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
            generation_path=GROUND_SURFACE_GENERATION_PATH,
            source_plan_schema_version=plan.schema_version,
            source_plan_generation_path=plan.generation_path,
            recovery_stage=recovery_stage,
            status="generated",
            lines=lines,
            required_nucleus_ids=required_nucleus_ids,
            covered_required_nucleus_ids=covered_nuclei,
            required_relation_ids=required_relation_ids,
            covered_required_relation_ids=covered_relations,
            unresolved_evidence_span_ids=unresolved,
            fact_boundary_covered=(
                not plan.coverage_requirements.fact_boundary_required
                or "fact_boundary" in roles
            ),
            human_follow_covered=(
                not plan.coverage_requirements.human_follow_required
                or "human_follow" in roles
            ),
            limited_opposition_covered=("limited_opposition" in roles),
            coverage_delegated_to_separate_safety_owner=False,
        )

    issues = validate_grounded_sentence_plan(sentence_plan, plan, resolver)
    if issues:
        raise GroundedSentenceSurfaceError("invalid_grounded_sentence_plan:" + ",".join(issues))
    return sentence_plan


def _clean_fragment(value: Any) -> str:
    text = _clean(value).translate(_FRAGMENT_DELETE_TRANSLATION)
    text = text.strip(" 、,。．.!！\t\n\r")
    text = _LEADING_CONNECTOR_RE.sub("", text)
    return text.strip()


def _quote(value: Any) -> str:
    text = _clean_fragment(value)
    return f"「{text}」" if text else ""


def _texts_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    return _dedupe(
        _clean_fragment(resolver.resolve(span_id).raw_text)
        for span_id in nucleus.source_span_ids
        if _EVIDENCE_ID_RE.fullmatch(span_id)
    )


def _surface_fragment_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    raw_text: Any,
) -> str:
    text = _clean(raw_text)
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if "lexical:preserve_source_predicate" in attributes:
        return text
    if len(text) > 40 and any(code.startswith("semantic_role:") for code in attributes):
        parts = re.split(r"(?:けれども?|だけど|けど|一方で|ただ)[、,\s]*", text)
        candidate = _clean(parts[-1]) if len(parts) > 1 else ""
        if len(candidate) >= 8:
            if "semantic_role:initial_condition" in attributes:
                initial = _clean(parts[0])
                if initial:
                    return f"{initial}一方、{candidate}"
            return candidate
    return text


def _quotes_for_nuclei(
    nucleus_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    fragments: list[tuple[str, GroundedSemanticNucleus, str, str, int, int]] = []
    for nucleus_id in nucleus_ids:
        nucleus = nucleus_index.get(nucleus_id)
        if nucleus is None:
            continue
        for span_id in nucleus.source_span_ids:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                continue
            span = resolver.resolve(span_id)
            fragments.append(
                (
                    span_id,
                    nucleus,
                    _clean(getattr(span, "raw_text", "")),
                    _clean(getattr(span, "source_field", "")),
                    int(getattr(span, "start_index", -1)),
                    int(getattr(span, "end_index", -1)),
                )
            )
    fragments.sort(key=lambda item: (item[3], item[4] if item[4] >= 0 else 10**9))
    units: list[tuple[SurfaceClauseUnit, str, int, int]] = []
    for span_id, nucleus, text, field, start, end in fragments:
        if not text:
            continue
        dependency_role: SurfaceDependencyRole = "standalone"
        if units and units[-1][1] == field:
            previous_unit, _previous_field, previous_start, previous_end = units[-1]
            interrogative = re.search(
                r"(?:何故|なぜ|どうして)$",
                _clean_fragment(previous_unit.surface_text),
            )
            continuation = re.match(
                r"^(?:と考えて(?:いた|しまって)|と思って|とか|という)",
                text,
            )
            source_adjacent = bool(
                previous_end < 0 or start < 0 or max(0, start - previous_end) <= 2
            )
            if source_adjacent and interrogative and continuation:
                dependency_role = "interrogative_quotative"
            elif source_adjacent and continuation:
                dependency_role = "predicate_continuation"
            elif source_adjacent and re.match(
                r"^(?:でも|だけど|けれど|けど|ただ|一方で?)",
                text,
            ):
                dependency_role = "connector_attached"
            if dependency_role != "standalone":
                previous_text = previous_unit.surface_text
                if dependency_role == "interrogative_quotative" and interrogative:
                    tail = interrogative.group(0)
                    previous_text = (
                        previous_text[: interrogative.start()]
                        + f"『{tail}』"
                    )
                combined = _clean_fragment(previous_text + text)
                units[-1] = (
                    SurfaceClauseUnit(
                        source_span_ids=(*previous_unit.source_span_ids, span_id),
                        dependency_role=dependency_role,
                        surface_text=combined,
                        surface_form="dependent_clause_group",
                        terminal_predicate_kind=nucleus.semantic_frame.predicate_kind,
                    ),
                    field,
                    previous_start,
                    end,
                )
                continue

        surface_text = _surface_fragment_for_nucleus(nucleus, text)
        attributes = set(nucleus.semantic_frame.attribute_codes)
        if "semantic_role:embedded_turn" in attributes:
            surface_form: SurfaceClauseForm = "quotative_clause"
        elif nucleus.semantic_frame.predicate_kind or nucleus.semantic_frame.modality != "fact":
            surface_form = "complete_clause"
        else:
            surface_form = "nominal_anchor"
        units.append(
            (
                SurfaceClauseUnit(
                    source_span_ids=(span_id,),
                    dependency_role="standalone",
                    surface_text=surface_text,
                    surface_form=surface_form,
                    terminal_predicate_kind=nucleus.semantic_frame.predicate_kind,
                ),
                field,
                start,
                end,
            )
        )
    return tuple(
        _dedupe(
            _quote(unit.surface_text)
            for unit, _field, _start, _end in units
        )
    )


def _join_quotes(quotes: Sequence[str]) -> str:
    values = [value for value in quotes if value]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]}と{values[1]}"
    return "、".join(values[:-1]) + f"と{values[-1]}"


def _hedge_prefix(binding: GroundedSentenceBinding) -> str:
    return "今の入力だけを見ると、" if "scope_hedge" in binding.functional_atom_ids else ""


def _render_observation(
    binding: GroundedSentenceBinding,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    quotes = _quotes_for_nuclei(binding.nucleus_ids, nucleus_index, resolver)
    joined = _join_quotes(quotes)
    if not joined:
        return ""
    prefix = _hedge_prefix(binding)
    if len(binding.nucleus_ids) > 1:
        atoms = set(binding.functional_atom_ids)
        if "observation_surface_role:evaluated_change_arc" in atoms:
            if len(quotes) >= 3:
                return (
                    f"{prefix}{quotes[0]}から{quotes[1]}へ見方が動き、"
                    f"その変化を{quotes[-1]}と捉えています。"
                )
            return f"{prefix}{joined}が、変化とその受け止め方としてつながっています。"
        if "observation_surface_role:change_direction_arc" in atoms:
            if len(quotes) >= 2:
                return f"{prefix}{quotes[0]}から{quotes[-1]}へ、これから保ちたい向きが動いています。"
            return f"{prefix}{joined}に、これから保ちたい向きが表れています。"
        if "observation_surface_role:action_change_arc" in atoms:
            if len(quotes) >= 2:
                return f"{prefix}{quotes[0]}という変化が、{quotes[-1]}という行動までつながっています。"
            return f"{prefix}{joined}が、考えだけでなく行動にも表れています。"
        if "observation_surface_role:retained_intention_with_unknown_arc" in atoms:
            return f"{prefix}{joined}が並び、保ちたい意図と、まだ分からない範囲の両方があります。"
        if "observation_surface_role:retained_intention_with_preparation_arc" in atoms:
            return f"{prefix}{joined}がつながり、先にした準備が、保ちたい意図を支えています。"
        if "observation_surface_role:retained_intention_arc" in atoms:
            return f"{prefix}{joined}が、これからも保ちたい一つの向きとしてつながっています。"
        if "observation_surface_role:current_change_arc" in atoms:
            return f"{prefix}{joined}が、今感じている変化としてつながっています。"
        if "observation_surface_role:state_arc" in atoms:
            return f"{prefix}{joined}が重なり、今は一つの状態として前に出ています。"
        return f"{prefix}{joined}が、同じ入力の中で一つの流れになっています。"
    nucleus = nucleus_index[binding.nucleus_ids[0]]
    if "lexical:preserve_source_predicate" in nucleus.semantic_frame.attribute_codes:
        return f"{prefix}今は、{joined}という感覚が前に出ています。"
    if all(field in {"emotion_details", "emotions", "category"} for field in nucleus.source_fields):
        return f"{prefix}選択した項目からは、{joined}が今の状態に関わっています。"
    if nucleus.kind == "action":
        return f"{prefix}{joined}という行動に移しています。"
    if nucleus.kind == "wish":
        return f"{prefix}{joined}という方向を望んでいます。"
    if nucleus.kind == "self_evaluation":
        return f"{prefix}今は、{joined}と自分を見ている状態です。"
    if nucleus.kind == "change":
        return f"{prefix}{joined}という変化を、自分でも感じています。"
    if nucleus.kind in {"reaction", "state", "constraint"}:
        return f"{prefix}今は、{joined}という感覚や状態が前に出ています。"
    return f"{prefix}今回の中心には、{joined}があります。"


def _relation_fragment(
    relation: GroundedSemanticRelation,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    left = _join_quotes(_quotes_for_nuclei((relation.from_nucleus_id,), nucleus_index, resolver))
    right = _join_quotes(_quotes_for_nuclei((relation.to_nucleus_id,), nucleus_index, resolver))
    if not left or not right:
        return ""
    label = _RELATION_LABELS.get(relation.type, "入力内のつながり")
    if relation.type == "shift_from_to":
        return f"{left}から{right}への{label}"
    if relation.type == "temporal_before_after":
        return f"{left}と{right}の{label}"
    if relation.type in {"contrast", "preserves_despite", "coexistence", "wish_and_constraint"}:
        return f"{left}と{right}の間にある{label}"
    if relation.type == "action_supports_change":
        return f"{left}と{right}の間にある{label}"
    if relation.type == "continuation_or_refusal":
        return f"{left}に対して置かれた{right}という{label}"
    if relation.type == "uncertain_connection":
        return f"{left}と{right}の順序上のつながり"
    return f"{left}と{right}の{label}"


def _join_relation_fragments(fragments: Sequence[str]) -> str:
    values = [item for item in fragments if item]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]}と{values[1]}"
    return "、".join(values[:-1]) + f"、そして{values[-1]}"


def _render_extra_context(
    extra_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    extras = _join_quotes(_quotes_for_nuclei(extra_ids, nucleus_index, resolver))
    if not extras:
        return ""
    nuclei = tuple(nucleus_index[item] for item in extra_ids if item in nucleus_index)
    kinds = {item.kind for item in nuclei}
    attributes = {
        code
        for item in nuclei
        for code in item.semantic_frame.attribute_codes
    }
    if "action" in kinds or "operator:action" in attributes:
        return f"その流れを支える動きとして、{extras}もあります。"
    if "wish" in kinds or "semantic_role:retained_intention" in attributes:
        return f"その先には、{extras}という保ちたい方向もあります。"
    if "self_evaluation" in kinds:
        return f"一方で、{extras}という自分への見方も重なっています。"
    if kinds.intersection({"state", "reaction", "constraint"}):
        return f"その背景には、{extras}という状態も重なっています。"
    if "change" in kinds or "semantic_role:current_change" in attributes:
        return f"その途中には、{extras}という変化もあります。"
    if "event" in kinds:
        if any(item.semantic_frame.polarity == "negative" for item in nuclei):
            return f"その出発点には、{extras}という止まりや負荷もあります。"
        return f"その出発点には、{extras}という出来事があります。"
    return f"その前提には、{extras}という内容もあります。"


def _render_observation_with_relations(
    binding: GroundedSentenceBinding,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    resolver: EvidenceSpanResolver,
) -> str:
    quotes = _quotes_for_nuclei(binding.nucleus_ids, nucleus_index, resolver)
    joined = _join_quotes(quotes)
    if not joined:
        return ""
    if not binding.relation_ids:
        return _render_observation(binding, nucleus_index, resolver)
    relation_text = _render_relation(binding, nucleus_index, relation_index, resolver)
    endpoint_ids = {
        nucleus_id
        for relation_id in binding.relation_ids
        if relation_id in relation_index
        for nucleus_id in (
            relation_index[relation_id].from_nucleus_id,
            relation_index[relation_id].to_nucleus_id,
        )
    }
    extra_ids = tuple(item for item in binding.nucleus_ids if item not in endpoint_ids)
    extra_context = _render_extra_context(extra_ids, nucleus_index, resolver)
    if extra_context:
        return f"{relation_text}{extra_context}"
    return relation_text


def _render_relation(
    binding: GroundedSentenceBinding,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    resolver: EvidenceSpanResolver,
) -> str:
    if not binding.relation_ids:
        return _render_observation(binding, nucleus_index, resolver)
    sentences: list[str] = []
    for relation_id in binding.relation_ids:
        if relation_id not in relation_index:
            continue
        relation = relation_index[relation_id]
        left = _join_quotes(
            _quotes_for_nuclei((relation.from_nucleus_id,), nucleus_index, resolver)
        )
        right = _join_quotes(
            _quotes_for_nuclei((relation.to_nucleus_id,), nucleus_index, resolver)
        )
        if not left or not right:
            continue
        role = relation_surface_role(relation, nucleus_index)
        left_form = _semantic_endpoint_surface_form(nucleus_index[relation.from_nucleus_id])
        right_form = _semantic_endpoint_surface_form(nucleus_index[relation.to_nucleus_id])
        if role == "provisional_evaluation_to_counterevidence":
            sentences.append(
                f"{left}と見ている一方で、{right}という別の事実もあります。"
            )
        elif role == "burden_or_constraint_with_progress":
            sentences.append(
                f"{left}という負荷がある一方で、{right}という進みも生まれています。"
            )
        elif role == "comparison_to_counterevidence":
            sentences.append(
                f"{left}という比較を含む見方の一方で、{right}という自分の前回を基準にした変化もあります。"
            )
        elif role == "coexisting_comparison_and_evidence":
            sentences.append(
                f"{left}という見方だけでなく、{right}という具体的な変化も同時にあります。"
            )
        elif role == "intention_evidenced_by_action":
            sentences.append(
                f"{left}という意図が、{right}という行動につながっています。"
            )
        elif role == "change_evidenced_by_action":
            sentences.append(
                f"{left}という変化が、{right}という行動にも表れています。"
            )
        elif role == "dimension_shift":
            sentences.append(f"{left}から{right}へ、捉え方や動きが移っています。")
        elif role == "coexisting_contrast":
            sentences.append(f"{left}と{right}が、異なる向きのまま同時にあります。")
        elif relation.type == "temporal_before_after":
            sentences.append(f"{left}のあとに、{right}へ動いています。")
        elif relation.type == "wish_and_constraint":
            sentences.append(f"{left}という願いと、{right}という制約が並んでいます。")
        elif relation.type == "user_stated_cause":
            sentences.append(f"{left}を理由として、{right}へつながっています。")
        elif relation.type == "user_stated_result":
            sentences.append(f"{left}から、結果として{right}へつながっています。")
        elif relation.type == "continuation_or_refusal":
            sentences.append(f"{left}に対して、{right}という、続ける方向には同意していない言葉もあります。")
        elif relation.type == "uncertain_connection":
            sentences.append(f"{left}のあとに{right}が続いていますが、それ以上の因果は確定しません。")
        elif left_form == "nominal_anchor" and right_form == "nominal_anchor":
            sentences.append(f"{left}と{right}が、今の状態の中で並んでいます。")
        else:
            sentences.append(f"{left}と{right}が、この順でつながっています。")
    joined = " ".join(item for item in sentences if item)
    if not joined:
        return _render_observation(binding, nucleus_index, resolver)
    return f"{_hedge_prefix(binding)}{joined}"


def _render_limited_scope(
    binding: GroundedSentenceBinding,
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    resolver: EvidenceSpanResolver,
) -> str:
    joined = _join_quotes(_quotes_for_nuclei(binding.nucleus_ids, nucleus_index, resolver))
    relation_text = _join_relation_fragments(
        tuple(
            _relation_fragment(relation_index[relation_id], nucleus_index, resolver)
            for relation_id in binding.relation_ids
            if relation_id in relation_index
        )
    )
    if plan.input_profile.material_quality == "labels_only_limited":
        base = f"選択した項目からは、{joined}までが見えています。"
    else:
        base = f"今の入力から確かに言えるのは、{joined}までです。"
    if relation_text:
        base += f" 入力内の関係として確認できるのは、{relation_text}までです。"
    return base + " 出来事や理由は、それ以上には広げません。"


def _render_fact_boundary(
    binding: GroundedSentenceBinding,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    joined = _join_quotes(_quotes_for_nuclei(binding.nucleus_ids, nucleus_index, resolver))
    return (
        f"{joined}は、今ここに出ている自己評価です。"
        "あなた自身について確定した事実ではありません。"
    )


def _render_limited_opposition(
    binding: GroundedSentenceBinding,
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    resolver: EvidenceSpanResolver,
) -> str:
    if not binding.relation_ids:
        return _render_observation(binding, nucleus_index, resolver)
    relation = relation_index[binding.relation_ids[0]]
    fact_ids = set(plan.response_plan.fact_boundary_nucleus_ids)
    other_ids = tuple(
        nucleus_id
        for nucleus_id in (relation.from_nucleus_id, relation.to_nucleus_id)
        if nucleus_id not in fact_ids
    )
    other = _join_quotes(_quotes_for_nuclei(other_ids, nucleus_index, resolver))
    if not other:
        return _render_relation(binding, nucleus_index, relation_index, resolver)
    if relation.type == "continuation_or_refusal":
        return f"同時に、{other}という、先の自己評価を続ける方向には同意していない言葉もあります。"
    if relation.type in {"preserves_despite", "contrast"}:
        return f"同時に、{other}という、先の自己評価だけで終わらない言葉もあります。"
    return f"同時に、{other}という、先の自己評価とは別の向きを持つ言葉もあります。"


def _render_human_follow(
    binding: GroundedSentenceBinding,
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> str:
    reception_plan = plan.response_plan.human_reception_plan
    if reception_plan is None or not reception_plan.required:
        raise GroundedSentenceSurfaceError("human_reception_plan_missing")
    expected_nucleus_ids = _dedupe(
        (
            *reception_plan.target_nucleus_ids,
            *reception_plan.support_nucleus_ids,
        )
    )
    if binding.nucleus_ids != expected_nucleus_ids:
        raise GroundedSentenceSurfaceError("human_reception_target_mismatch")
    try:
        reception = realize_grounded_human_reception(
            reception_plan,
            nucleus_index,
            resolver,
            recovery_stage=_plan_recovery_stage(binding),
        )
    except GroundedHumanReceptionSurfaceError as exc:
        raise GroundedSentenceSurfaceError(str(exc)) from exc
    return reception.text


def _plan_recovery_stage(binding: GroundedSentenceBinding) -> RecoveryStage:
    """Read the body-free recovery atom without coupling the R4 realizer."""

    stage = next(
        (
            atom.split(":", 1)[1]
            for atom in binding.functional_atom_ids
            if atom.startswith("recovery:")
        ),
        "",
    )
    if stage not in GROUND_RECOVERY_STAGES:
        raise GroundedSentenceSurfaceError("human_reception_recovery_stage_missing")
    return stage  # type: ignore[return-value]

def _apply_integrated_human_follow(
    text: str,
    binding: GroundedSentenceBinding,
) -> str:
    # Integrated follow is no longer a valid public layout.  Keep this helper
    # side-effect free so stale atoms cannot silently append a pseudo-second
    # layer to an observation sentence; validation and Gate logic reject them.
    _ = binding
    return text


def _realize_line(
    line: GroundedSentencePlanLine,
    *,
    plan: GroundedObservationPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    relation_index: Mapping[str, GroundedSemanticRelation],
    resolver: EvidenceSpanResolver,
) -> str:
    if line.surface_function == "observe_nuclei":
        return _render_observation(line.binding, nucleus_index, resolver)
    if line.surface_function == "observe_nuclei_with_relations":
        return _render_observation_with_relations(
            line.binding,
            nucleus_index,
            relation_index,
            resolver,
        )
    if line.surface_function == "observe_relation":
        return _render_relation(line.binding, nucleus_index, relation_index, resolver)
    if line.surface_function == "render_limited_scope":
        return _render_limited_scope(
            line.binding,
            plan,
            nucleus_index,
            relation_index,
            resolver,
        )
    if line.surface_function == "render_fact_boundary":
        return _render_fact_boundary(line.binding, nucleus_index, resolver)
    if line.surface_function == "render_limited_opposition":
        return _render_limited_opposition(
            line.binding,
            plan,
            nucleus_index,
            relation_index,
            resolver,
        )
    if line.surface_function == "render_human_follow":
        return _render_human_follow(line.binding, plan, nucleus_index, resolver)
    raise GroundedSentenceSurfaceError(f"unsupported_surface_function:{line.surface_function}")


def split_two_stage_surface(text: Any) -> tuple[str, str, tuple[str, ...]]:
    """Return observation/reception sections and structural issue codes."""

    surface = str(text or "")
    issues: list[str] = []
    lines = surface.splitlines()
    observation_positions = tuple(
        index
        for index, line in enumerate(lines)
        if line.strip() == OBSERVATION_SECTION_LABEL
    )
    reception_positions = tuple(
        index
        for index, line in enumerate(lines)
        if line.strip() == RECEPTION_SECTION_LABEL
    )
    if len(observation_positions) != 1 or len(reception_positions) != 1:
        issues.append("two_stage_labels_missing_or_duplicated")
        return "", "", tuple(issues)
    observation_index = observation_positions[0]
    reception_index = reception_positions[0]
    if observation_index != 0 or reception_index <= observation_index:
        issues.append("two_stage_label_order_invalid")
        return "", "", tuple(issues)
    observation = "\n".join(lines[observation_index + 1 : reception_index]).strip()
    reception = "\n".join(lines[reception_index + 1 :]).strip()
    if not observation:
        issues.append("two_stage_observation_section_empty")
    if not reception:
        issues.append("two_stage_reception_section_empty")
    return observation, reception, tuple(issues)


def realize_grounded_sentence_plan(
    sentence_plan: GroundedSentencePlan,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> GroundedSurfaceResult:
    """Realize a SentencePlan with generic functional atoms and source text."""

    if sentence_plan.status != "generated":
        result = GroundedSurfaceResult(
            schema_version=GROUND_SURFACE_RESULT_SCHEMA_VERSION,
            generation_path=GROUND_SURFACE_GENERATION_PATH,
            status=sentence_plan.status,
            recovery_stage=sentence_plan.recovery_stage,
            text="",
            lines=(),
            required_nucleus_ids=sentence_plan.required_nucleus_ids,
            covered_required_nucleus_ids=sentence_plan.covered_required_nucleus_ids,
            required_relation_ids=sentence_plan.required_relation_ids,
            covered_required_relation_ids=sentence_plan.covered_required_relation_ids,
            unresolved_evidence_span_ids=sentence_plan.unresolved_evidence_span_ids,
            required_coverage_preserved=sentence_plan.coverage_delegated_to_separate_safety_owner,
            fact_boundary_covered=sentence_plan.fact_boundary_covered,
            human_follow_covered=sentence_plan.human_follow_covered,
            limited_opposition_covered=sentence_plan.limited_opposition_covered,
        )
    else:
        nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
        relation_index = {item.relation_id: item for item in plan.relations}
        surface_lines: list[GroundedSurfaceLine] = []
        for line in sentence_plan.lines:
            text = _clean(
                _apply_integrated_human_follow(
                    _realize_line(
                        line,
                        plan=plan,
                        nucleus_index=nucleus_index,
                        relation_index=relation_index,
                        resolver=resolver,
                    ),
                    line.binding,
                )
            )
            if not text:
                continue
            binding = GroundedSentenceBinding(
                sentence_id=line.binding.sentence_id,
                line_role=line.binding.line_role,
                nucleus_ids=line.binding.nucleus_ids,
                relation_ids=line.binding.relation_ids,
                evidence_span_ids=line.binding.evidence_span_ids,
                claim_scope=line.binding.claim_scope,
                functional_atom_ids=line.binding.functional_atom_ids,
                contains_question=bool(_QUESTION_RE.search(text)),
                required=line.binding.required,
            )
            surface_lines.append(
                GroundedSurfaceLine(
                    sentence_id=binding.sentence_id,
                    text=text,
                    binding=binding,
                )
            )
        observation_lines = tuple(
            line.text
            for line in surface_lines
            if line.binding.line_role != "human_follow"
        )
        reception_lines = tuple(
            line.text
            for line in surface_lines
            if line.binding.line_role == "human_follow"
        )
        observation_text = "\n".join(observation_lines).strip()
        reception_text = "\n".join(reception_lines).strip()
        text = (
            f"{OBSERVATION_SECTION_LABEL}\n{observation_text}\n\n"
            f"{RECEPTION_SECTION_LABEL}\n{reception_text}"
        ).strip()
        result = GroundedSurfaceResult(
            schema_version=GROUND_SURFACE_RESULT_SCHEMA_VERSION,
            generation_path=GROUND_SURFACE_GENERATION_PATH,
            status="generated",
            recovery_stage=sentence_plan.recovery_stage,
            text=text,
            lines=tuple(surface_lines),
            required_nucleus_ids=sentence_plan.required_nucleus_ids,
            covered_required_nucleus_ids=sentence_plan.covered_required_nucleus_ids,
            required_relation_ids=sentence_plan.required_relation_ids,
            covered_required_relation_ids=sentence_plan.covered_required_relation_ids,
            unresolved_evidence_span_ids=sentence_plan.unresolved_evidence_span_ids,
            required_coverage_preserved=(
                set(sentence_plan.required_nucleus_ids)
                <= set(sentence_plan.covered_required_nucleus_ids)
                and set(sentence_plan.required_relation_ids)
                <= set(sentence_plan.covered_required_relation_ids)
                and not sentence_plan.unresolved_evidence_span_ids
            ),
            fact_boundary_covered=sentence_plan.fact_boundary_covered,
            human_follow_covered=sentence_plan.human_follow_covered,
            limited_opposition_covered=sentence_plan.limited_opposition_covered,
        )

    issues = validate_grounded_surface_result(result, sentence_plan, plan, resolver)
    if issues:
        raise GroundedSentenceSurfaceError("invalid_grounded_surface_result:" + ",".join(issues))
    return result


def build_grounded_surface_result(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: RecoveryStage = "full",
) -> GroundedSurfaceResult:
    sentence_plan = build_grounded_sentence_plan(
        plan,
        resolver,
        recovery_stage=recovery_stage,
    )
    return realize_grounded_sentence_plan(sentence_plan, plan, resolver)


def build_reception_recovery_sentence_plan(
    base_sentence_plan: GroundedSentencePlan,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: RecoveryStage,
) -> GroundedSentencePlan:
    """Change only reception recovery while preserving observation lines."""

    if recovery_stage not in GROUND_RECOVERY_STAGES:
        raise GroundedSentenceSurfaceError(
            f"unsupported_recovery_stage:{recovery_stage}"
        )
    if base_sentence_plan.status != "generated":
        candidate = replace(
            base_sentence_plan,
            recovery_stage=recovery_stage,
        )
    else:
        reception_plan = plan.response_plan.human_reception_plan
        if reception_plan is None or not reception_plan.required:
            raise GroundedSentenceSurfaceError("human_reception_plan_missing")
        contract_atoms = _reception_contract_atoms(
            reception_plan,
            recovery_stage,
        )
        lines: list[GroundedSentencePlanLine] = []
        for line in base_sentence_plan.lines:
            if line.binding.line_role != "human_follow":
                lines.append(line)
                continue
            atom_ids: list[str] = []
            contract_inserted = False
            for atom in line.binding.functional_atom_ids:
                if atom.startswith("recovery:"):
                    atom_ids.append(f"recovery:{recovery_stage}")
                elif atom.startswith("reception_"):
                    if not contract_inserted:
                        atom_ids.extend(contract_atoms)
                        contract_inserted = True
                else:
                    atom_ids.append(atom)
            if not contract_inserted:
                atom_ids.extend(contract_atoms)
            lines.append(
                replace(
                    line,
                    binding=replace(
                        line.binding,
                        functional_atom_ids=_dedupe(atom_ids),
                    ),
                )
            )
        candidate = replace(
            base_sentence_plan,
            recovery_stage=recovery_stage,
            lines=tuple(lines),
        )
    issues = validate_grounded_sentence_plan(candidate, plan, resolver)
    if issues:
        raise GroundedSentenceSurfaceError(
            "invalid_grounded_reception_recovery_plan:" + ",".join(issues)
        )
    return candidate


def build_plan_preserving_recovery_sequence(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[GroundedSurfaceResult, ...]:
    """Render all I4 shrink stages while retaining the required nucleus."""

    base_sentence_plan = build_grounded_sentence_plan(
        plan,
        resolver,
        recovery_stage="full",
    )
    return tuple(
        realize_grounded_sentence_plan(
            (
                base_sentence_plan
                if stage == "full"
                else build_reception_recovery_sentence_plan(
                    base_sentence_plan,
                    plan,
                    resolver,
                    recovery_stage=stage,
                )
            ),
            plan,
            resolver,
        )
        for stage in GROUND_RECOVERY_STAGES
    )


def validate_grounded_sentence_plan(
    sentence_plan: GroundedSentencePlan,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    issues: list[str] = []
    if sentence_plan.schema_version != GROUND_SENTENCE_PLAN_SCHEMA_VERSION:
        issues.append("sentence_plan_schema_version_mismatch")
    if sentence_plan.generation_path != GROUND_SURFACE_GENERATION_PATH:
        issues.append("sentence_plan_generation_path_mismatch")
    if sentence_plan.source_plan_schema_version != GROUND_OBSERVATION_PLAN_SCHEMA_VERSION:
        issues.append("source_plan_schema_version_mismatch")
    if sentence_plan.recovery_stage not in GROUND_RECOVERY_STAGES:
        issues.append("unsupported_recovery_stage")

    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    relation_index = {item.relation_id: item for item in plan.relations}
    nucleus_ids = set(nucleus_index)
    relation_ids = set(relation_index)
    seen_sentence_ids: set[str] = set()
    for line in sentence_plan.lines:
        binding = line.binding
        if binding.sentence_id in seen_sentence_ids:
            issues.append(f"duplicate_sentence_id:{binding.sentence_id}")
        seen_sentence_ids.add(binding.sentence_id)
        if binding.contains_question:
            issues.append(f"question_binding_forbidden:{binding.sentence_id}")
        if not binding.evidence_span_ids:
            issues.append(f"sentence_without_evidence:{binding.sentence_id}")
        for nucleus_id in binding.nucleus_ids:
            if nucleus_id not in nucleus_ids:
                issues.append(f"unknown_nucleus:{binding.sentence_id}:{nucleus_id}")
        for relation_id in binding.relation_ids:
            if relation_id not in relation_ids:
                issues.append(f"unknown_relation:{binding.sentence_id}:{relation_id}")
        if binding.relation_ids and line.surface_function not in _RELATION_REALIZING_FUNCTIONS:
            issues.append(f"relation_binding_not_realized:{binding.sentence_id}")
        for span_id in binding.evidence_span_ids:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(f"synthetic_or_invalid_evidence_id:{binding.sentence_id}:{span_id}")
        for span_id in resolver.unresolved_ids(binding.evidence_span_ids):
            issues.append(f"unresolved_evidence_id:{binding.sentence_id}:{span_id}")

    deliveries: dict[str, list[GroundedSentencePlanLine]] = {}
    for line in sentence_plan.lines:
        for nucleus_id in line.binding.nucleus_ids:
            deliveries.setdefault(nucleus_id, []).append(line)
        if line.binding.relation_ids and not any(
            atom.startswith("relation_surface_role:")
            for atom in line.binding.functional_atom_ids
        ):
            issues.append(f"relation_surface_role_missing:{line.binding.sentence_id}")
        if line.binding.line_role == "human_follow" and (
            "human_follow_delivery:separate"
            not in line.binding.functional_atom_ids
        ):
            issues.append(f"human_follow_delivery_missing:{line.binding.sentence_id}")
        if "human_follow_delivery:integrated" in line.binding.functional_atom_ids:
            issues.append(f"human_follow_integrated_delivery_forbidden:{line.binding.sentence_id}")
    for nucleus_id, lines in deliveries.items():
        if len(lines) < 2:
            continue
        later_has_distinct_responsibility = any(
            line.binding.relation_ids
            or line.binding.line_role in {
                "fact_boundary",
                "limited_opposition",
            }
            or "human_follow_delivery:separate" in line.binding.functional_atom_ids
            for line in lines[1:]
        )
        if not later_has_distinct_responsibility:
            issues.append(f"duplicate_anchor_delivery_without_new_role:{nucleus_id}")

    separate_expected = plan.safety_policy.safety_kind in _SEPARATE_SAFETY_KINDS
    if separate_expected:
        if sentence_plan.status != "separate_safety_owner":
            issues.append("separate_safety_owner_status_missing")
        if sentence_plan.lines:
            issues.append("generic_lines_created_for_separate_safety")
        if not sentence_plan.coverage_delegated_to_separate_safety_owner:
            issues.append("separate_safety_coverage_delegation_missing")
        return _dedupe(issues)

    if plan.input_profile.material_quality == "empty":
        if sentence_plan.status != "unavailable" or sentence_plan.lines:
            issues.append("empty_input_must_be_unavailable")
        return _dedupe(issues)

    if sentence_plan.status != "generated":
        issues.append("generated_sentence_plan_status_missing")
    if plan.response_plan.surface_shape != "two_stage":
        issues.append("mandatory_two_stage_surface_shape_missing")
    missing_nuclei = set(sentence_plan.required_nucleus_ids) - set(sentence_plan.covered_required_nucleus_ids)
    missing_relations = set(sentence_plan.required_relation_ids) - set(sentence_plan.covered_required_relation_ids)
    if missing_nuclei:
        issues.append("missing_required_nucleus_coverage")
    if missing_relations:
        issues.append("missing_required_relation_coverage")
    if sentence_plan.unresolved_evidence_span_ids:
        issues.append("unresolved_sentence_evidence")
    if plan.coverage_requirements.fact_boundary_required and not sentence_plan.fact_boundary_covered:
        issues.append("fact_boundary_not_covered")
    if plan.coverage_requirements.human_follow_required and not sentence_plan.human_follow_covered:
        issues.append("human_follow_not_covered")
    if plan.coverage_requirements.human_follow_required:
        reception_plan = plan.response_plan.human_reception_plan
        reception_lines = tuple(
            line
            for line in sentence_plan.lines
            if line.binding.line_role == "human_follow"
        )
        if reception_plan is None or not reception_plan.required:
            issues.append("human_reception_plan_missing")
        if len(reception_lines) != 1:
            issues.append("two_stage_reception_line_count_invalid")
        else:
            reception_line = reception_lines[0]
            binding = reception_line.binding
            atoms = tuple(binding.functional_atom_ids)
            reception_atoms = tuple(
                atom for atom in atoms if atom.startswith("reception_")
            )
            if "human_follow_delivery:separate" not in atoms:
                issues.append("two_stage_reception_line_missing")
            if reception_line.surface_function != "render_human_follow":
                issues.append("human_reception_surface_owner_invalid")
            if binding.relation_ids or any(
                atom.startswith("relation:")
                or atom.startswith("relation_surface_role:")
                for atom in atoms
            ):
                issues.append("human_reception_relation_owner_forbidden")
            if any(
                atom.startswith("observation_surface_role:")
                or atom.startswith("semantic_arc:")
                for atom in atoms
            ):
                issues.append("human_reception_observation_atom_forbidden")
            if any(
                atom in {"identity_claim_not_fact", "input_grounded_opposition"}
                for atom in atoms
            ):
                issues.append("human_reception_fact_boundary_owner_forbidden")

            if reception_plan is not None:
                issues.extend(
                    validate_grounded_human_reception_plan(
                        reception_plan,
                        expected_target_ids=plan.response_plan.human_follow_target_ids,
                        nucleus_index=nucleus_index,
                        resolver=resolver,
                        safety_kind=plan.safety_policy.safety_kind,
                        material_quality=plan.input_profile.material_quality,
                    )
                )
                expected_nucleus_ids = _dedupe(
                    (
                        *reception_plan.target_nucleus_ids,
                        *reception_plan.support_nucleus_ids,
                    )
                )
                if binding.nucleus_ids != expected_nucleus_ids:
                    issues.append("human_reception_target_mismatch")
                if (
                    binding.evidence_span_ids
                    != tuple(reception_plan.source_evidence_span_ids)
                ):
                    issues.append("human_reception_source_evidence_mismatch")
                if resolver.unresolved_ids(
                    reception_plan.source_evidence_span_ids
                ):
                    issues.append("human_reception_source_evidence_unresolved")

                expected_contract_atoms = _reception_contract_atoms(
                    reception_plan,
                    sentence_plan.recovery_stage,
                )
                expected_acts = tuple(
                    f"reception_act:{act}"
                    for act in reception_active_acts(
                        reception_plan,
                        sentence_plan.recovery_stage,
                    )
                )
                actual_acts = tuple(
                    atom
                    for atom in reception_atoms
                    if atom.startswith("reception_act:")
                )
                if not actual_acts:
                    issues.append("human_reception_act_missing")
                elif actual_acts != expected_acts:
                    issues.append("human_reception_act_mismatch")
                if reception_atoms != expected_contract_atoms:
                    issues.append("human_reception_contract_atom_mismatch")
                if not set(
                    atom
                    for atom in expected_contract_atoms
                    if atom.startswith("reception_follow_")
                ).issubset(reception_atoms):
                    issues.append("human_reception_follow_contract_missing")
                if not {
                    f"reception_stance:{reception_plan.stance}",
                    (
                        "reception_speaker:"
                        f"{reception_effective_speaker_presence(reception_plan, sentence_plan.recovery_stage)}"
                    ),
                }.issubset(reception_atoms):
                    issues.append("human_reception_stance_contract_missing")
                if not {
                    (
                        "reception_reference:"
                        f"{reception_effective_reference_mode(reception_plan, sentence_plan.recovery_stage)}"
                    ),
                    (
                        "reception_quote_policy:"
                        f"{reception_plan.quote_policy.mode}"
                    ),
                }.issubset(reception_atoms):
                    issues.append("human_reception_reference_policy_missing")
                if not {
                    "reception_sentence_budget:one_or_two",
                    (
                        "reception_sentence_min:"
                        f"{reception_plan.sentence_policy.min_sentences}"
                    ),
                    (
                        "reception_sentence_max:"
                        f"{reception_plan.sentence_policy.max_sentences}"
                    ),
                }.issubset(reception_atoms):
                    issues.append("human_reception_sentence_budget_invalid")
                if "reception_distinctness:required" not in reception_atoms:
                    issues.append(
                        "human_reception_distinctness_contract_missing"
                    )
                bounded_counterposition = (
                    "bounded_counter_self_denial"
                    in reception_active_acts(
                        reception_plan,
                        sentence_plan.recovery_stage,
                    )
                )
                if bounded_counterposition and not {
                    "reception_speaker:explicit_emlis",
                    "reception_reference:explicit_emlis_counterposition",
                }.issubset(reception_atoms):
                    issues.append("self_denial_explicit_stance_missing")
        if reception_lines and sentence_plan.lines[-1] is not reception_lines[-1]:
            issues.append("two_stage_reception_line_must_be_last")
        if any(
            line.binding.line_role != "human_follow"
            and any(
                atom.startswith("human_follow:")
                or atom.startswith("human_follow_delivery:")
                or atom.startswith("human_follow_contribution:")
                or atom.startswith("reception_")
                for atom in line.binding.functional_atom_ids
            )
            for line in sentence_plan.lines
        ):
            issues.append("human_follow_atom_leaked_into_observation_section")
            issues.append("human_reception_atom_leaked_into_observation_section")
    if plan.safety_policy.safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        opposition_required = (
            _self_denial_opposition_relation(plan, nucleus_index, relation_index)
            is not None
        )
        if opposition_required and not sentence_plan.limited_opposition_covered:
            issues.append("self_denial_limited_opposition_not_covered")
        required_roles = {"fact_boundary"}
        if opposition_required:
            required_roles.add("limited_opposition")
        roles = {line.binding.line_role for line in sentence_plan.lines}
        if not required_roles <= roles:
            issues.append("self_denial_overlay_roles_missing")
    if plan.input_profile.material_quality == "short_state_sufficient":
        if any(line.binding.contains_question for line in sentence_plan.lines):
            issues.append("short_state_question_escape")
    return _dedupe(issues)


def validate_grounded_surface_result(
    result: GroundedSurfaceResult,
    sentence_plan: GroundedSentencePlan,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    issues: list[str] = []
    if result.schema_version != GROUND_SURFACE_RESULT_SCHEMA_VERSION:
        issues.append("surface_schema_version_mismatch")
    if result.generation_path != GROUND_SURFACE_GENERATION_PATH:
        issues.append("surface_generation_path_mismatch")
    if result.recovery_stage != sentence_plan.recovery_stage:
        issues.append("surface_recovery_stage_mismatch")
    if not result.public_reply_path_connected:
        issues.append("public_reply_path_must_be_connected_at_i5")
    if result.completed_semantic_template_used:
        issues.append("completed_semantic_template_used")
    if result.label_assembly_used:
        issues.append("label_assembly_used")
    if result.fixture_semantic_pattern_used:
        issues.append("fixture_semantic_pattern_used")
    if result.synthetic_evidence_id_used:
        issues.append("synthetic_evidence_id_used")

    if result.status == "generated":
        if not result.text or not result.lines:
            issues.append("generated_surface_empty")
        _observation, _reception, two_stage_issues = split_two_stage_surface(result.text)
        issues.extend(two_stage_issues)
        if not result.required_coverage_preserved:
            issues.append("required_coverage_not_preserved")
        if _QUESTION_RE.search(result.text):
            issues.append("surface_question_forbidden")
        for line in result.lines:
            if line.binding.contains_question:
                issues.append(f"surface_line_contains_question:{line.sentence_id}")
            if not line.text:
                issues.append(f"surface_line_empty:{line.sentence_id}")
            for span_id in resolver.unresolved_ids(line.binding.evidence_span_ids):
                issues.append(f"surface_unresolved_evidence:{line.sentence_id}:{span_id}")

        if plan.coverage_requirements.human_follow_required:
            reception_plan = plan.response_plan.human_reception_plan
            reception_lines = tuple(
                line
                for line in result.lines
                if line.binding.line_role == "human_follow"
            )
            if reception_plan is None or not reception_plan.required:
                issues.append("human_reception_plan_missing")
            elif len(reception_lines) != 1:
                issues.append("human_reception_surface_line_count_invalid")
            else:
                reception_line = reception_lines[0]
                quote_values = tuple(
                    _RECEPTION_QUOTE_RE.findall(reception_line.text)
                )
                terminal_kinds = tuple(
                    atom.split(":", 1)[1]
                    for atom in reception_line.binding.functional_atom_ids
                    if atom.startswith("reception_terminal_predicate:")
                )
                active_acts = reception_active_acts(
                    reception_plan,
                    sentence_plan.recovery_stage,
                )
                grounded_referent = resolve_grounded_reception_referent(
                    reception_plan,
                    {item.nucleus_id: item for item in plan.nuclei},
                    resolver,
                    recovery_stage=sentence_plan.recovery_stage,
                    act=active_acts[0],
                )
                reception_surface = GroundedHumanReceptionSurface(
                    text=reception_line.text,
                    terminal_predicate_kinds=terminal_kinds,
                    sentence_count=len(
                        tuple(
                            part.strip()
                            for part in _RECEPTION_SENTENCE_END_RE.split(
                                reception_line.text
                            )
                            if part.strip()
                        )
                    ),
                    referent_kind="sentence_plan_bound",
                    realized_reception_acts=active_acts,
                    grounded_nucleus_ids=grounded_referent.nucleus_ids,
                    grounded_evidence_span_ids=(
                        grounded_referent.evidence_span_ids
                    ),
                    source_anchor_count=len(quote_values),
                    source_anchor_max_visible_chars=max(
                        (len(value) for value in quote_values),
                        default=0,
                    ),
                    recovery_stage=sentence_plan.recovery_stage,
                )
                issues.extend(
                    validate_grounded_human_reception_surface(
                        reception_surface,
                        reception_plan,
                        resolver,
                    )
                )
    elif result.status == "separate_safety_owner":
        if plan.safety_policy.safety_kind not in _SEPARATE_SAFETY_KINDS:
            issues.append("unexpected_separate_safety_owner")
        if result.text or result.lines:
            issues.append("generic_surface_created_for_separate_safety")
    elif result.status == "unavailable":
        if plan.input_profile.material_quality != "empty":
            issues.append("unexpected_unavailable_surface")
        if result.text or result.lines:
            issues.append("unavailable_surface_must_be_empty")
    else:
        issues.append("unsupported_surface_status")

    if result.fact_boundary_covered != sentence_plan.fact_boundary_covered:
        issues.append("fact_boundary_coverage_mismatch")
    if result.human_follow_covered != sentence_plan.human_follow_covered:
        issues.append("human_follow_coverage_mismatch")
    if result.limited_opposition_covered != sentence_plan.limited_opposition_covered:
        issues.append("limited_opposition_coverage_mismatch")
    return _dedupe(issues)


__all__ = [
    "GROUND_SENTENCE_PLAN_SCHEMA_VERSION",
    "GROUND_SURFACE_RESULT_SCHEMA_VERSION",
    "GROUND_SURFACE_GENERATION_PATH",
    "OBSERVATION_SECTION_LABEL",
    "RECEPTION_SECTION_LABEL",
    "split_two_stage_surface",
    "DIRECTIONAL_GROUNDED_RELATION_TYPES",
    "GROUND_RECOVERY_STAGES",
    "GroundedSentenceSurfaceError",
    "SurfaceClauseUnit",
    "GroundedSentenceBinding",
    "GroundedSentencePlanLine",
    "GroundedSentencePlan",
    "GroundedSurfaceLine",
    "GroundedSurfaceResult",
    "expected_human_follow_role",
    "relation_surface_role",
    "build_grounded_sentence_plan",
    "realize_grounded_sentence_plan",
    "build_grounded_surface_result",
    "build_reception_recovery_sentence_plan",
    "build_plan_preserving_recovery_sequence",
    "validate_grounded_sentence_plan",
    "validate_grounded_surface_result",
]
