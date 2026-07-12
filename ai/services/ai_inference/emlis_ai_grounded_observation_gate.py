# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free semantic gate for the canonical grounded reply path (I5).

The gate consumes the plan, sentence plan, realized surface, and the request-
local Evidence resolver that actually produced the candidate.  It does not
reconstruct meaning from the public body and it never serializes source text.
"""

from dataclasses import dataclass
import re
from typing import Any, Final, Literal

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    DIRECTIONAL_GROUNDED_RELATION_TYPES,
    GroundedSentencePlan,
    GroundedSurfaceResult,
    expected_human_follow_role,
    validate_grounded_sentence_plan,
    validate_grounded_surface_result,
)


GROUND_OBSERVATION_GATE_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_observation_gate.i5.v1"
GROUND_OBSERVATION_REPLY_GENERATION_PATH: Final = "grounded_observation_plan_sentence_surface_canonical_v1"

GateStatus = Literal["passed", "failed", "not_evaluated"]
ProductReadfeelStatus = Literal["not_evaluated", "human_pass", "human_fail"]

_NORMALIZE_RE: Final = re.compile(r"[\s\u3000、。,.!！?？「」『』（）()・:：;；]")
_QUOTED_ANCHOR_RE: Final = re.compile(r"「[^」]*」")
_MAJOR_ROLE_CODES: Final = frozenset(
    {
        "semantic_role:initial_condition",
        "semantic_role:contrast_before",
        "semantic_role:contrast_after",
        "semantic_role:embedded_turn",
        "semantic_role:current_change",
        "semantic_role:explicit_result",
        "semantic_role:explicit_evaluation",
        "semantic_role:retained_intention",
        "semantic_role:protective_or_limiting_refusal",
        "semantic_role:limiting_unknown",
        "semantic_role:provisional_evaluation",
        "semantic_role:counterevidence",
        "semantic_role:concrete_action",
        "semantic_role:concrete_action_evidence",
    }
)
_SENSATION_FAMILIES: Final[dict[str, re.Pattern[str]]] = {
    "burden_weight": re.compile(r"(?:重さ|重い|重たい|鉛|重り)"),
    "pressure": re.compile(r"(?:圧迫|圧力|締め付け|押し潰)"),
    "pain": re.compile(r"(?:痛み|痛い|疼く|刺さる|棘)"),
    "breathing": re.compile(r"(?:息苦し|呼吸が苦し|息が詰ま)"),
}
_CERTAIN_RESULT_RE: Final = re.compile(
    r"(?:結果として|確定した|確実に|必ず|達成した|実現した|解決した|成功した)"
)


def _dedupe(values: Any) -> tuple[str, ...]:
    if values is None:
        source = ()
    elif isinstance(values, (str, bytes, bytearray)):
        source = (values,)
    else:
        try:
            source = tuple(values)
        except TypeError:
            source = (values,)
    output: list[str] = []
    for value in source:
        item = str(value or "").strip()
        if item and item not in output:
            output.append(item)
    return tuple(output)


def _normalized(value: Any) -> str:
    return _NORMALIZE_RE.sub("", str(value or "")).lower()


def _nucleus_source_text(nucleus: Any, resolver: EvidenceSpanResolver) -> str:
    return " ".join(
        str(resolver.resolve(span_id).raw_text or "")
        for span_id in nucleus.source_span_ids
        if not resolver.unresolved_ids((span_id,))
    )


def _terminal_surface_stem(value: str) -> str:
    skeleton = _QUOTED_ANCHOR_RE.sub("<ANCHOR>", str(value or ""))
    return _normalized(skeleton.rsplit("<ANCHOR>", 1)[-1])


def _atom_values(line: Any, prefix: str) -> tuple[str, ...]:
    return _dedupe(
        atom
        for atom in line.binding.functional_atom_ids
        if atom.startswith(prefix)
    )


def _semantic_subcheck_reasons(
    *,
    plan: GroundedObservationPlan,
    sentence_plan: GroundedSentencePlan,
    surface_result: GroundedSurfaceResult,
    resolver: EvidenceSpanResolver,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Return text-retention, anti-template, and depth reason codes."""

    semantic: list[str] = []
    anti_template: list[str] = []
    depth: list[str] = []
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    required_nuclei = set(plan.coverage_requirements.required_nucleus_ids)
    bound_nuclei = {
        nucleus_id
        for line in sentence_plan.lines
        for nucleus_id in line.binding.nucleus_ids
    }
    major_nuclei = {
        item.nucleus_id
        for item in plan.nuclei
        if _MAJOR_ROLE_CODES.intersection(item.semantic_frame.attribute_codes)
    }
    if not major_nuclei <= (required_nuclei & bound_nuclei):
        semantic.append("major_arc_role_missing")

    sentence_by_relation = {
        relation_id: tuple(
            line
            for line in sentence_plan.lines
            if relation_id in line.binding.relation_ids
        )
        for relation_id in plan.coverage_requirements.required_relation_ids
    }
    for relation in plan.relations:
        if relation.relation_id not in plan.coverage_requirements.required_relation_ids:
            continue
        lines = sentence_by_relation.get(relation.relation_id, ())
        endpoints = {relation.from_nucleus_id, relation.to_nucleus_id}
        represented = any(
            endpoints <= set(line.binding.nucleus_ids)
            and (
                relation.type not in DIRECTIONAL_GROUNDED_RELATION_TYPES
                or line.binding.nucleus_ids.index(relation.from_nucleus_id)
                < line.binding.nucleus_ids.index(relation.to_nucleus_id)
            )
            for line in lines
        )
        if relation.type in DIRECTIONAL_GROUNDED_RELATION_TYPES and not represented:
            semantic.append("required_relation_direction_mismatch")
        if relation.type == "preserves_despite" and not represented:
            semantic.append("required_reversal_missing")

    surface_normalized = _normalized(surface_result.text)
    source_text = " ".join(
        _nucleus_source_text(item, resolver)
        for item in plan.nuclei
        if any(code.startswith("lexical:") for code in item.semantic_frame.attribute_codes)
    )
    for nucleus in plan.nuclei:
        attributes = set(nucleus.semantic_frame.attribute_codes)
        if "lexical:preserve_source_predicate" in attributes:
            anchor = _normalized(_nucleus_source_text(nucleus, resolver))
            if anchor and anchor not in surface_normalized:
                semantic.append("lexical_anchor_missing")
        if "lexical:no_new_sensation_family" in attributes:
            for pattern in _SENSATION_FAMILIES.values():
                if pattern.search(surface_result.text) and not pattern.search(source_text):
                    semantic.append("ungrounded_sensation_family_added")
                    break

    for nucleus in plan.nuclei:
        attributes = set(nucleus.semantic_frame.attribute_codes)
        if nucleus.nucleus_id not in required_nuclei or not (
            "semantic_role:limiting_unknown" in attributes or nucleus.kind == "constraint"
        ):
            continue
        bound_surface_lines = tuple(
            line.text
            for line in surface_result.lines
            if nucleus.nucleus_id in line.binding.nucleus_ids
        )
        source_anchor = _normalized(_nucleus_source_text(nucleus, resolver))
        if (
            bound_surface_lines
            and source_anchor
            and not any(source_anchor in _normalized(text) for text in bound_surface_lines)
            and any(_CERTAIN_RESULT_RE.search(text) for text in bound_surface_lines)
        ):
            semantic.append("required_relation_direction_mismatch")

    target_ids = tuple(plan.response_plan.human_follow_target_ids)
    follow_lines = tuple(
        line
        for line in sentence_plan.lines
        if set(target_ids).intersection(line.binding.nucleus_ids)
        and any(atom.startswith("human_follow:") for atom in line.binding.functional_atom_ids)
    )
    expected_role = (
        expected_human_follow_role(plan, target_ids, nucleus_index)
        if target_ids
        else ""
    )
    expected_atom = f"human_follow:{expected_role}" if expected_role else ""
    follow_compatible = bool(
        not plan.coverage_requirements.human_follow_required
        or (follow_lines and any(expected_atom in line.binding.functional_atom_ids for line in follow_lines))
    )
    if not follow_compatible:
        depth.append("human_follow_role_target_mismatch")
    if (
        expected_role == "protective_counterdirection"
        and any(
            "human_follow:burden_expression" in line.binding.functional_atom_ids
            for line in follow_lines
        )
    ):
        depth.append("protective_counterdirection_misclassified_as_burden")

    separate_follow_lines = tuple(
        line
        for line in follow_lines
        if line.binding.line_role == "human_follow"
        and "human_follow_delivery:separate" in line.binding.functional_atom_ids
    )
    relation_target_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.relation_ids
        and set(target_ids).intersection(line.binding.nucleus_ids)
    )
    for follow_line in separate_follow_lines:
        follow_role = next(
            (
                atom.split(":", 1)[1]
                for atom in follow_line.binding.functional_atom_ids
                if atom.startswith("human_follow:")
            ),
            "",
        )
        if not relation_target_lines:
            continue
        if follow_role == "protective_counterdirection":
            depth.extend(
                (
                    "human_follow_no_distinct_contribution",
                    "human_follow_repeats_relation_target",
                    "self_denial_counterdirection_duplicated",
                )
            )
        elif not {
            f"human_follow_contribution:{follow_role}",
            "human_follow_target_already_delivered",
        } <= set(follow_line.binding.functional_atom_ids):
            depth.append("human_follow_repeats_relation_target")

    for follow_line in follow_lines:
        role = next(
            (
                atom.split(":", 1)[1]
                for atom in follow_line.binding.functional_atom_ids
                if atom.startswith("human_follow:")
            ),
            "",
        )
        modality = {
            "retained_intention": "intention",
            "protective_counterdirection": "protective_counterdirection",
            "help_seeking_preserved": "help_seeking",
            "concrete_effort": "action",
            "valued_change": "change",
            "integrated_current_state": "current_state",
            "burden_expression": "burden",
        }.get(role, "bounded_observation")
        if not {
            "closure_role:human_follow",
            f"closure_modality:{modality}",
            "closure_scope:selected_target",
        } <= set(follow_line.binding.functional_atom_ids):
            depth.append("generic_follow_suffix_role_mismatch")

    closure_signatures = tuple(
        _atom_values(line, "closure_")
        for line in follow_lines
        if _atom_values(line, "closure_")
    )
    if len(closure_signatures) != len(set(closure_signatures)):
        anti_template.append("generic_follow_suffix_repeated")

    surface_by_sentence = {
        line.sentence_id: line for line in surface_result.lines
    }
    stem_occurrences: dict[str, list[Any]] = {}
    for line in sentence_plan.lines:
        if line.binding.line_role not in {
            "primary_observation",
            "supporting_observation",
            "relation_observation",
        }:
            continue
        surface_line = surface_by_sentence.get(line.binding.sentence_id)
        if surface_line is None:
            continue
        stem = _terminal_surface_stem(surface_line.text)
        if stem:
            stem_occurrences.setdefault(stem, []).append(line)
    for occurrences in stem_occurrences.values():
        if len(occurrences) < 2:
            continue
        expressed_roles = tuple(
            _dedupe(
                (
                    *_atom_values(line, "relation_surface_role:"),
                    *_atom_values(line, "observation_surface_role:"),
                )
            )
            for line in occurrences
        )
        if any(not roles for roles in expressed_roles) or len(set(expressed_roles)) != len(
            expressed_roles
        ):
            anti_template.append(
                "relation_surface_stem_repetition_without_new_role"
            )

    arc_owners: dict[str, list[Any]] = {}
    for line in sentence_plan.lines:
        for arc in _atom_values(line, "semantic_arc:"):
            if arc in {
                "semantic_arc:coexisting_observation",
                "semantic_arc:state_arc",
            }:
                continue
            arc_owners.setdefault(arc, []).append(line)
    if any(
        len(lines) > 1
        and not all(
            "semantic_arc_fragment:justified" in line.binding.functional_atom_ids
            for line in lines
        )
        for lines in arc_owners.values()
    ):
        depth.append("required_arc_fragmented_without_reason")

    if plan.input_profile.material_quality == "short_state_sufficient" and len(required_nuclei) == 1:
        if (
            len(sentence_plan.lines) != 1
            or any(line.binding.line_role == "human_follow" for line in sentence_plan.lines)
        ):
            anti_template.append("short_state_duplicate_anchor_loop")

    for previous, current in zip(sentence_plan.lines, sentence_plan.lines[1:]):
        previous_set = set(previous.binding.nucleus_ids)
        current_set = set(current.binding.nucleus_ids)
        previous_roles = {
            atom for atom in previous.binding.functional_atom_ids if atom.startswith("human_follow:")
        }
        current_roles = {
            atom for atom in current.binding.functional_atom_ids if atom.startswith("human_follow:")
        }
        if (
            previous_set
            and previous_set == current_set
            and not current.binding.relation_ids
            and not (current_roles - previous_roles)
        ):
            anti_template.append("surface_semantic_repetition_without_new_role")

    for previous, current in zip(surface_result.lines, surface_result.lines[1:]):
        previous_text = _normalized(previous.text)
        current_text = _normalized(current.text)
        current_roles = {
            atom
            for atom in current.binding.functional_atom_ids
            if atom.startswith("human_follow:")
        }
        previous_anchors = {
            _normalized(resolver.resolve(span_id).raw_text)
            for span_id in previous.binding.evidence_span_ids
            if not resolver.unresolved_ids((span_id,))
        }
        current_anchors = {
            _normalized(resolver.resolve(span_id).raw_text)
            for span_id in current.binding.evidence_span_ids
            if not resolver.unresolved_ids((span_id,))
        }
        if (
            previous_text
            and previous_text == current_text
            and not current_roles
        ) or (
            previous_anchors.intersection(current_anchors)
            and not current.binding.relation_ids
            and not current_roles
        ):
            anti_template.append("surface_semantic_repetition_without_new_role")

    return _dedupe(semantic), _dedupe(anti_template), _dedupe(depth)


@dataclass(frozen=True)
class GroundedObservationGateReport:
    schema_version: str
    generation_path: str
    recovery_stage: str
    plan_validity_gate: GateStatus
    evidence_resolution_gate: GateStatus
    required_coverage_gate: GateStatus
    text_semantic_retention_gate: GateStatus
    anti_template_gate: GateStatus
    question_dominance_gate: GateStatus
    depth_adequacy_gate: GateStatus
    semantic_quality_gate: GateStatus
    public_observation_status: str
    public_comment_present: bool
    product_readfeel_status: ProductReadfeelStatus
    rejection_reasons: tuple[str, ...]
    material_quality: str
    nucleus_count: int
    required_nucleus_count: int
    covered_required_nucleus_count: int
    relation_count: int
    required_relation_count: int
    covered_required_relation_count: int
    human_follow_required: bool
    human_follow_covered: bool
    fact_boundary_required: bool
    fact_boundary_covered: bool
    fixed_semantic_surface_used: bool
    example_cue_route_used: bool
    label_only_assembly_used: bool
    synthetic_evidence_id_used: bool

    @property
    def passed(self) -> bool:
        return self.semantic_quality_gate == "passed"

    def as_body_free_meta(self) -> dict[str, Any]:
        """Return runtime facts only; body, source text, and raw input stay out."""

        return {
            "schema_version": self.schema_version,
            "generation_path": self.generation_path,
            "recovery_stage": self.recovery_stage,
            "plan_validity_gate": self.plan_validity_gate,
            "evidence_resolution_gate": self.evidence_resolution_gate,
            "required_coverage_gate": self.required_coverage_gate,
            "text_semantic_retention_gate": self.text_semantic_retention_gate,
            "anti_template_gate": self.anti_template_gate,
            "question_dominance_gate": self.question_dominance_gate,
            "depth_adequacy_gate": self.depth_adequacy_gate,
            "semantic_quality_gate": self.semantic_quality_gate,
            "delivery_status": self.public_observation_status,
            "public_observation_status": self.public_observation_status,
            "public_comment_present": self.public_comment_present,
            "product_readfeel_status": self.product_readfeel_status,
            "rejection_reasons": list(self.rejection_reasons),
            "material_quality": self.material_quality,
            "nucleus_count": self.nucleus_count,
            "required_nucleus_count": self.required_nucleus_count,
            "covered_required_nucleus_count": self.covered_required_nucleus_count,
            "relation_count": self.relation_count,
            "required_relation_count": self.required_relation_count,
            "covered_required_relation_count": self.covered_required_relation_count,
            "human_follow_required": self.human_follow_required,
            "human_follow_covered": self.human_follow_covered,
            "fact_boundary_required": self.fact_boundary_required,
            "fact_boundary_covered": self.fact_boundary_covered,
            "fixed_semantic_surface_used": self.fixed_semantic_surface_used,
            "example_cue_route_used": self.example_cue_route_used,
            "label_only_assembly_used": self.label_only_assembly_used,
            "synthetic_evidence_id_used": self.synthetic_evidence_id_used,
            "delivery_status_separated_from_product_readfeel": True,
            "raw_input_included": False,
            "raw_text_included": False,
            "source_text_included": False,
            "comment_text_included": False,
            "surface_text_included": False,
            "candidate_body_included": False,
            "public_contract_changed": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }


def evaluate_grounded_observation_gate(
    *,
    plan: GroundedObservationPlan,
    sentence_plan: GroundedSentencePlan,
    surface_result: GroundedSurfaceResult,
    resolver: EvidenceSpanResolver,
    product_readfeel_status: ProductReadfeelStatus = "not_evaluated",
) -> GroundedObservationGateReport:
    """Evaluate I5 plan/coverage/evidence/template/depth gates.

    Product Read Feel is an external human result.  A delivery pass therefore
    remains ``not_evaluated`` unless an explicit human result is supplied.
    """

    if product_readfeel_status not in {"not_evaluated", "human_pass", "human_fail"}:
        raise ValueError("unsupported_product_readfeel_status")

    plan_issues = validate_grounded_observation_plan(plan, resolver)
    sentence_issues = validate_grounded_sentence_plan(sentence_plan, plan, resolver)
    surface_issues = validate_grounded_surface_result(surface_result, sentence_plan, plan, resolver)
    semantic_subcheck_reasons, anti_template_reasons, depth_reasons = _semantic_subcheck_reasons(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface_result,
        resolver=resolver,
    )

    plan_valid = not plan_issues and not any(
        reason.startswith(("unknown_nucleus:", "unknown_relation:", "source_plan_"))
        for reason in sentence_issues
    )

    binding_ids = tuple(
        span_id
        for line in sentence_plan.lines
        for span_id in line.binding.evidence_span_ids
    )
    unresolved_binding_ids = resolver.unresolved_ids(binding_ids)
    evidence_resolved = bool(
        not unresolved_binding_ids
        and not sentence_plan.unresolved_evidence_span_ids
        and not surface_result.unresolved_evidence_span_ids
        and not surface_result.synthetic_evidence_id_used
        and not any("evidence" in reason for reason in (*plan_issues, *sentence_issues, *surface_issues))
    )

    required_nuclei = set(plan.coverage_requirements.required_nucleus_ids)
    covered_nuclei = set(surface_result.covered_required_nucleus_ids)
    required_relations = set(plan.coverage_requirements.required_relation_ids)
    covered_relations = set(surface_result.covered_required_relation_ids)
    required_coverage = bool(
        surface_result.required_coverage_preserved
        and required_nuclei <= covered_nuclei
        and required_relations <= covered_relations
        and (
            not plan.coverage_requirements.fact_boundary_required
            or surface_result.fact_boundary_covered
        )
        and (
            not plan.coverage_requirements.human_follow_required
            or surface_result.human_follow_covered
        )
    )

    bound_nuclei = {
        nucleus_id
        for line in sentence_plan.lines
        for nucleus_id in line.binding.nucleus_ids
    }
    bound_relations = {
        relation_id
        for line in sentence_plan.lines
        for relation_id in line.binding.relation_ids
    }
    text_semantic_retained = bool(
        plan.input_profile.text_presence != "text_present"
        or (
            required_nuclei
            and required_nuclei <= bound_nuclei
            and required_relations <= bound_relations
        )
    ) and not semantic_subcheck_reasons

    anti_template = bool(
        not plan.surface_policy.completed_semantic_template_allowed
        and not plan.surface_policy.example_cue_route_allowed
        and not surface_result.completed_semantic_template_used
        and not surface_result.fixture_semantic_pattern_used
        and not surface_result.label_assembly_used
    ) and not anti_template_reasons
    question_free = bool(
        not plan.response_plan.question_policy.allowed
        and all(not line.binding.contains_question for line in sentence_plan.lines)
        and "?" not in surface_result.text
        and "？" not in surface_result.text
    )
    depth_adequate = bool(
        required_coverage
        and text_semantic_retained
        and (
            plan.input_profile.material_quality not in {"grounded"}
            or (
                len(bound_nuclei) >= len(required_nuclei)
                and len(bound_relations) >= len(required_relations)
            )
        )
    ) and not depth_reasons

    separate_safety_owner = surface_result.status == "separate_safety_owner"
    generated = surface_result.status == "generated" and bool(surface_result.text.strip())
    all_semantic_gates_passed = bool(
        plan_valid
        and evidence_resolved
        and required_coverage
        and text_semantic_retained
        and anti_template
        and question_free
        and depth_adequate
        and generated
    )

    reasons: list[str] = []
    if not plan_valid:
        reasons.extend(plan_issues or ("grounded_plan_invalid",))
    if not evidence_resolved:
        reasons.extend(unresolved_binding_ids or ("grounded_evidence_resolution_failed",))
    if not required_coverage:
        reasons.append("grounded_required_coverage_failed")
    if not text_semantic_retained:
        reasons.extend(semantic_subcheck_reasons or ("grounded_text_semantic_retention_failed",))
    if not anti_template:
        reasons.extend(anti_template_reasons or ("grounded_anti_template_failed",))
    if not question_free:
        reasons.append("grounded_question_dominance_failed")
    if not depth_adequate:
        reasons.extend(depth_reasons or ("grounded_depth_adequacy_failed",))
    if surface_result.status == "unavailable":
        reasons.append("grounded_surface_unavailable")
    if separate_safety_owner:
        reasons = ["separate_safety_surface_owner_preserved"]

    if separate_safety_owner:
        public_status = "safety_blocked"
        semantic_quality: GateStatus = "not_evaluated"
    elif all_semantic_gates_passed:
        public_status = "passed"
        semantic_quality = "passed"
    elif surface_result.status == "unavailable":
        public_status = "unavailable"
        semantic_quality = "failed"
    else:
        public_status = "rejected"
        semantic_quality = "failed"

    return GroundedObservationGateReport(
        schema_version=GROUND_OBSERVATION_GATE_SCHEMA_VERSION,
        generation_path=GROUND_OBSERVATION_REPLY_GENERATION_PATH,
        recovery_stage=surface_result.recovery_stage,
        plan_validity_gate="passed" if plan_valid else "failed",
        evidence_resolution_gate="passed" if evidence_resolved else "failed",
        required_coverage_gate="passed" if required_coverage else "failed",
        text_semantic_retention_gate="passed" if text_semantic_retained else "failed",
        anti_template_gate="passed" if anti_template else "failed",
        question_dominance_gate="passed" if question_free else "failed",
        depth_adequacy_gate="passed" if depth_adequate else "failed",
        semantic_quality_gate=semantic_quality,
        public_observation_status=public_status,
        public_comment_present=bool(public_status == "passed" and generated),
        product_readfeel_status=product_readfeel_status,
        rejection_reasons=_dedupe(reasons),
        material_quality=plan.input_profile.material_quality,
        nucleus_count=len(plan.nuclei),
        required_nucleus_count=len(required_nuclei),
        covered_required_nucleus_count=len(required_nuclei & covered_nuclei),
        relation_count=len(plan.relations),
        required_relation_count=len(required_relations),
        covered_required_relation_count=len(required_relations & covered_relations),
        human_follow_required=plan.coverage_requirements.human_follow_required,
        human_follow_covered=surface_result.human_follow_covered,
        fact_boundary_required=plan.coverage_requirements.fact_boundary_required,
        fact_boundary_covered=surface_result.fact_boundary_covered,
        fixed_semantic_surface_used=surface_result.completed_semantic_template_used,
        example_cue_route_used=surface_result.fixture_semantic_pattern_used,
        label_only_assembly_used=surface_result.label_assembly_used,
        synthetic_evidence_id_used=surface_result.synthetic_evidence_id_used,
    )


__all__ = [
    "GROUND_OBSERVATION_GATE_SCHEMA_VERSION",
    "GROUND_OBSERVATION_REPLY_GENERATION_PATH",
    "GroundedObservationGateReport",
    "evaluate_grounded_observation_gate",
]
