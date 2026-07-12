# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free semantic and RR6 Depth/Move Gate for the canonical reply path.

The gate consumes the plan, sentence plan, realized surface, and the request-
local Evidence resolver that actually produced the candidate.  It does not
reconstruct meaning from the public body and it never serializes source text.
"""

from dataclasses import dataclass
import re
from typing import Any, Final, Literal, Mapping

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_human_reception import (
    GroundedHumanReceptionSurfaceError,
    realize_grounded_human_reception,
    reception_active_moves,
    reception_effective_sentence_budget,
    reception_move_predicate_family,
    reception_terminal_predicate_kind,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    validate_grounded_human_reception_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    DIRECTIONAL_GROUNDED_RELATION_TYPES,
    GroundedSentencePlan,
    GroundedSurfaceResult,
    expected_human_follow_role,
    split_two_stage_surface,
    validate_grounded_sentence_plan,
    validate_grounded_surface_result,
)


GROUND_OBSERVATION_GATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.grounded_observation_gate.rr6.v2"
)
GROUND_OBSERVATION_REPLY_GENERATION_PATH: Final = "grounded_observation_plan_sentence_surface_canonical_v1"

GateStatus = Literal["passed", "failed", "not_evaluated"]
ProductReadfeelStatus = Literal["not_evaluated", "human_pass", "human_fail"]

RECEPTION_GATE_REPORT_FIELDS: Final = (
    "reception_plan_gate",
    "reception_grounding_gate",
    "reception_role_distinctness_gate",
    "reception_quote_reuse_gate",
    "reception_policy_exposure_gate",
    "reception_human_voice_gate",
    "reception_safety_boundary_gate",
    "reception_depth_plan_gate",
    "reception_move_realization_gate",
    "reception_depth_proportionality_gate",
    "reception_move_distinctness_gate",
    "reception_non_enumeration_gate",
)

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
_LEDGER_NARRATION_RE: Final = re.compile(
    r"(?:記|記録|記載)されています|(?:記録|入力)に(?:あります|置かれています)|"
    r"この記録には|同じ記録には|(?:入力|記録)に書かれています|"
    r"この順に書かれています|入力として受け取ります"
)
_RECEPTION_POLICY_EXPOSURE_RE: Final = re.compile(
    r"理由を(?:こちらで)?決めつけず|入力から言える範囲で|"
    r"診断はしません|ここでは事実として扱いません|原因は分かりませんが"
)
_RECEPTION_UNSUPPORTED_CLAIM_RE: Final = re.compile(
    r"あなたは(?:強い|優しい|立派|素晴らしい)(?:人)?です|"
    r"(?:必ず|絶対に|確実に)(?:成功|解決|良くな)"
)
_RECEPTION_ADVICE_RE: Final = re.compile(
    r"(?:してください|しましょう|してみて|すべき|した方がいい|"
    r"相談して|連絡して|受診して)"
)
_RECEPTION_RELATION_NARRATION_RE: Final = re.compile(
    r"(?:変化|考え|気持ち|意図|願い).{0,24}(?:が|から).{0,24}"
    r"(?:行動|変化|結果).{0,10}(?:生ん|つなが|表れ)|"
    r"(?:という|の)(?:構造|関係|つながり)(?:です|になっています)"
)
_RECEPTION_ANALYSIS_END_RE: Final = re.compile(
    r"(?:という|の)(?:構造|関係|傾向|パターン)(?:です|に見えます)|"
    r"(?:分析|整理|分類)(?:できます|しました|すると)"
)
_RECEPTION_FIELD_ENUMERATION_RE: Final = re.compile(
    r"(?:memo|メモ).{0,80}(?:memo_action|行動).{0,80}"
    r"(?:emotion|感情).{0,80}(?:category|カテゴリ)",
    re.IGNORECASE,
)
_RECEPTION_GENERIC_SUFFIX_RE: Final = re.compile(
    r"^(?:大切に|静かに)?受け止め(?:ます|ています|たいです)[。.!！]*$"
)
_RECEPTION_MEDICAL_DIAGNOSIS_RE: Final = re.compile(
    r"(?:うつ病|鬱病|パニック障害|適応障害|病気です|診断)"
)
_RECEPTION_RISK_JUDGMENT_RE: Final = re.compile(
    r"(?:危険性|危険度|危険では|危険じゃ).{0,8}(?:ありません|ない|低い|高い)"
)
_RECEPTION_RESOLUTION_GUARANTEE_RE: Final = re.compile(
    r"(?:もう大丈夫|安全です|解決しています|解決しました|"
    r"助けはもう必要ありません|問題ありません)"
)
_RECEPTION_FELT_STATE_DENIAL_RE: Final = re.compile(
    r"(?:苦し|つら|しんど|痛|重|胸).{0,18}(?:気のせい|本当ではない|存在しない)"
)
_RECEPTION_IDENTITY_ACCEPTANCE_RE: Final = re.compile(
    r"(?:価値がない|役に立たない|何もできない).{0,12}(?:事実|本当|確か)"
)
_RECEPTION_QUOTE_RE: Final = re.compile(r"「([^」]+)」")
_RECEPTION_SENTENCE_END_RE: Final = re.compile(r"[。！？!?]+")
_GROUNDED_GATE_BODY_FREE_CODE_RE: Final = re.compile(r"^[A-Za-z0-9_.:/-]*$")


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


def _ledger_narration_visible(value: Any) -> bool:
    # Source anchors may legitimately contain the same words.  The defect is
    # the renderer's predicate outside those quoted anchors (for example
    # ``「…」が記されています``), so inspect the generated remainder only.
    residual = _QUOTED_ANCHOR_RE.sub("", str(value or ""))
    return bool(_LEDGER_NARRATION_RE.search(residual))


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
    if plan.coverage_requirements.human_follow_required:
        if len(separate_follow_lines) != 1:
            depth.append("mandatory_two_stage_reception_line_count_invalid")
        if any(
            "human_follow_delivery:integrated" in line.binding.functional_atom_ids
            for line in sentence_plan.lines
        ):
            depth.append("mandatory_two_stage_integrated_follow_forbidden")
    for follow_line in separate_follow_lines:
        follow_role = next(
            (
                atom.split(":", 1)[1]
                for atom in follow_line.binding.functional_atom_ids
                if atom.startswith("human_follow:")
            ),
            "",
        )
        if f"human_follow_contribution:{follow_role}" not in follow_line.binding.functional_atom_ids:
            depth.append("human_follow_distinct_contribution_marker_missing")
        if not follow_role:
            depth.append("human_follow_role_missing")

    surface_line_by_id = {
        line.sentence_id: line
        for line in surface_result.lines
    }
    observation_surface_texts = tuple(
        line.text
        for line in surface_result.lines
        if line.binding.line_role != "human_follow"
    )
    for follow_line in separate_follow_lines:
        realized = surface_line_by_id.get(follow_line.binding.sentence_id)
        if realized is None:
            depth.append("human_follow_surface_missing")
            continue
        normalized_follow = _normalized(realized.text)
        if any(
            normalized_follow
            and normalized_follow == _normalized(observation_text)
            for observation_text in observation_surface_texts
        ):
            depth.append("human_follow_repeats_observation_surface")
        if _ledger_narration_visible(realized.text):
            anti_template.append("human_follow_ledger_narration_visible")
        if not any(
            atom.startswith("reception_move_predicate:")
            for atom in follow_line.binding.functional_atom_ids
        ):
            depth.append("human_follow_reception_owner_missing")

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
    for surface_line in surface_result.lines:
        if surface_line.binding.line_role == "human_follow":
            continue
        if _ledger_narration_visible(surface_line.text):
            anti_template.append("observation_ledger_narration_visible")
        residual = _normalized(_QUOTED_ANCHOR_RE.sub("", surface_line.text))
        if len(residual) < 8:
            depth.append("observation_surface_only_echo")
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
        observation_lines = tuple(
            line
            for line in sentence_plan.lines
            if line.binding.line_role != "human_follow"
        )
        reception_lines = tuple(
            line
            for line in sentence_plan.lines
            if line.binding.line_role == "human_follow"
        )
        if len(observation_lines) != 1 or len(reception_lines) != 1:
            anti_template.append("short_state_two_stage_shape_invalid")

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


def _sentence_count(value: str) -> int:
    return len(
        tuple(
            part.strip()
            for part in _RECEPTION_SENTENCE_END_RE.split(str(value or ""))
            if part.strip()
        )
    )


def _reception_atoms(line: Any, prefix: str) -> tuple[str, ...]:
    return tuple(
        atom.split(":", 1)[1]
        for atom in line.binding.functional_atom_ids
        if atom.startswith(prefix)
    )


def _evaluate_reception_gates(
    *,
    plan: GroundedObservationPlan,
    sentence_plan: GroundedSentencePlan,
    surface_result: GroundedSurfaceResult,
    resolver: EvidenceSpanResolver,
    observation_text: str,
    reception_text: str,
) -> tuple[
    dict[str, GateStatus],
    tuple[str, ...],
    dict[str, Any],
]:
    """Evaluate RR6 Depth/Move contracts without serializing visible bodies."""

    unavailable = surface_result.status in {
        "separate_safety_owner",
        "unavailable",
    }
    reception_required = bool(
        not unavailable and plan.coverage_requirements.human_follow_required
    )
    if not reception_required:
        return (
            {field: "not_evaluated" for field in RECEPTION_GATE_REPORT_FIELDS},
            (),
            {
                "reception_gate_required": False,
                "reception_all_gates_passed": False,
                "reception_act": "",
                "reception_stance": "",
                "reception_reference_mode": "",
                "reception_terminal_predicate_kind": "",
                "reception_depth_level": "",
                "reception_safety_mode": "",
                "reception_opportunity_count": 0,
                "reception_planned_move_count": 0,
                "reception_realized_move_count": 0,
                "reception_move_roles": (),
                "reception_surface_strategies": (),
                "reception_terminal_predicate_families": (),
                "raw_character_count_used": False,
                "reception_sentence_count": 0,
                "repeated_long_anchor_count": 0,
            },
        )

    reasons_by_gate: dict[str, list[str]] = {
        field: [] for field in RECEPTION_GATE_REPORT_FIELDS
    }
    reception_plan = plan.response_plan.human_reception_plan
    human_plan_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    human_surface_lines = tuple(
        line
        for line in surface_result.lines
        if line.binding.line_role == "human_follow"
    )
    human_line = human_plan_lines[0] if len(human_plan_lines) == 1 else None
    human_surface_line = (
        human_surface_lines[0] if len(human_surface_lines) == 1 else None
    )
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}

    reception_act = ""
    reception_stance = ""
    reception_reference_mode = ""
    terminal_predicate_kind = ""
    if human_line is not None:
        reception_acts = _reception_atoms(human_line, "reception_act:")
        reception_stances = _reception_atoms(human_line, "reception_stance:")
        reception_references = _reception_atoms(
            human_line,
            "reception_reference:",
        )
        terminal_predicates = _reception_atoms(
            human_line,
            "reception_terminal_predicate:",
        )
        reception_act = reception_acts[0] if reception_acts else ""
        reception_stance = reception_stances[0] if reception_stances else ""
        reception_reference_mode = (
            reception_references[0] if reception_references else ""
        )
        terminal_predicate_kind = (
            terminal_predicates[0] if terminal_predicates else ""
        )

    active_moves = ()
    realized_reception = None
    recovery_contract_valid = True
    if reception_plan is not None:
        try:
            active_moves = reception_active_moves(
                reception_plan,
                sentence_plan.recovery_stage,
            )
            reception_effective_sentence_budget(
                reception_plan,
                sentence_plan.recovery_stage,
            )
        except (
            GroundedHumanReceptionSurfaceError,
            AttributeError,
            KeyError,
            TypeError,
        ):
            recovery_contract_valid = False
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_recovery_depth_contract_invalid"
            )
            reasons_by_gate["reception_move_realization_gate"].append(
                "reception_recovery_move_contract_invalid"
            )
            reasons_by_gate["reception_depth_proportionality_gate"].append(
                "reception_recovery_proportionality_invalid"
            )
        if human_line is not None and recovery_contract_valid:
            try:
                realized_reception = realize_grounded_human_reception(
                    reception_plan,
                    nucleus_index,
                    resolver,
                    recovery_stage=sentence_plan.recovery_stage,
                    clause_plans=human_line.reception_clause_plans,
                )
            except (
                GroundedHumanReceptionSurfaceError,
                AttributeError,
                KeyError,
                TypeError,
            ):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_canonical_realization_failed"
                )

    if reception_plan is None:
        reasons_by_gate["reception_plan_gate"].append(
            "reception_plan_missing"
        )
    else:
        try:
            reception_plan_issues = validate_grounded_human_reception_plan(
                reception_plan,
                expected_target_ids=plan.response_plan.human_follow_target_ids,
                nucleus_index=nucleus_index,
                resolver=resolver,
                safety_kind=plan.safety_policy.safety_kind,
                material_quality=plan.input_profile.material_quality,
            )
        except (AttributeError, KeyError, TypeError, ValueError):
            reception_plan_issues = (
                "reception_plan_validation_contract_invalid",
            )
        reasons_by_gate["reception_plan_gate"].extend(
            reception_plan_issues
        )
        if human_line is None:
            reasons_by_gate["reception_plan_gate"].append(
                "reception_sentence_plan_line_missing"
            )
        if human_surface_line is None:
            reasons_by_gate["reception_plan_gate"].append(
                "reception_surface_line_missing"
            )
        if not reception_act:
            reasons_by_gate["reception_plan_gate"].append(
                "reception_act_atom_missing"
            )
        if not reception_stance:
            reasons_by_gate["reception_plan_gate"].append(
                "reception_stance_atom_missing"
            )
        if not reception_reference_mode:
            reasons_by_gate["reception_plan_gate"].append(
                "reception_reference_atom_missing"
            )

    depth = (
        getattr(reception_plan, "depth_policy", None)
        if reception_plan is not None
        else None
    )
    if reception_plan is None or depth is None:
        reasons_by_gate["reception_depth_plan_gate"].append(
            "reception_depth_plan_missing"
        )
    else:
        if depth.level not in {"minimal", "focused", "layered"}:
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_depth_level_invalid"
            )
        if depth.safety_mode not in {
            "standard",
            "self_denial_bounded",
            "help_seeking_bounded",
        }:
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_safety_mode_invalid"
            )
        if depth.raw_character_count_used is not False:
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_raw_character_count_used"
            )
        if depth.opportunity_count != len(reception_plan.opportunities):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_opportunity_count_mismatch"
            )
        if (
            depth.selected_move_count != len(reception_plan.moves)
            or not 1 <= len(reception_plan.moves) <= 3
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_selected_move_count_invalid"
            )
        if not 1 <= depth.min_sentences <= depth.max_sentences <= 3:
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_depth_sentence_budget_invalid"
            )
        if not 1 <= depth.min_realized_moves <= max(
            1,
            len(reception_plan.moves),
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_depth_move_budget_invalid"
            )
        expected_level = (
            "focused"
            if depth.safety_mode != "standard"
            else "layered"
            if len(reception_plan.moves) >= 2
            else "minimal"
            if reception_plan.moves
            and reception_plan.moves[0].reception_act
            in {"stay_with_current_burden", "respect_words_placed"}
            else "focused"
        )
        if (
            depth.level != expected_level
            or f"depth:{expected_level}"
            not in depth.selection_reason_codes
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_canonical_depth_classification_mismatch"
            )
        if depth.level == "minimal" and (
            len(reception_plan.moves) != 1
            or depth.min_sentences != 1
            or depth.max_sentences != 1
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_minimal_depth_contract_invalid"
            )
        if depth.level == "focused" and (
            len(reception_plan.moves) not in {1, 2}
            or depth.max_sentences > 2
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_focused_depth_contract_invalid"
            )
        if depth.level == "layered" and (
            len(reception_plan.moves) not in {2, 3}
            or depth.min_sentences < 2
            or depth.min_realized_moves < 2
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_layered_depth_contract_invalid"
            )
        active_roles = {move.move_role for move in active_moves}
        active_acts = {move.reception_act for move in active_moves}
        planned_counterposition = any(
            move.move_role == "bounded_counterposition"
            for move in reception_plan.moves
        )
        if depth.safety_mode == "self_denial_bounded" and (
            "felt_response" not in active_roles
            or (
                planned_counterposition
                and "bounded_counterposition" not in active_roles
            )
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_self_denial_safety_move_missing"
            )
        if depth.safety_mode == "help_seeking_bounded" and (
            "hold_help_seeking" not in active_acts
            or "bounded_counterposition" not in active_roles
        ):
            reasons_by_gate["reception_depth_plan_gate"].append(
                "reception_help_seeking_safety_move_missing"
            )

    if reception_plan is None or human_line is None:
        reasons_by_gate["reception_grounding_gate"].append(
            "reception_grounding_contract_missing"
        )
    else:
        allowed_nuclei = set(
            (
                *reception_plan.target_nucleus_ids,
                *reception_plan.support_nucleus_ids,
            )
        )
        allowed_evidence = set(reception_plan.source_evidence_span_ids)
        if not human_line.binding.nucleus_ids or not set(
            human_line.binding.nucleus_ids
        ).issubset(allowed_nuclei):
            reasons_by_gate["reception_grounding_gate"].append(
                "reception_nucleus_grounding_mismatch"
            )
        if not human_line.binding.evidence_span_ids or not set(
            human_line.binding.evidence_span_ids
        ).issubset(allowed_evidence):
            reasons_by_gate["reception_grounding_gate"].append(
                "reception_evidence_grounding_mismatch"
            )
        if resolver.unresolved_ids(human_line.binding.evidence_span_ids):
            reasons_by_gate["reception_grounding_gate"].append(
                "reception_source_evidence_unresolved"
            )
    if _RECEPTION_UNSUPPORTED_CLAIM_RE.search(reception_text):
        reasons_by_gate["reception_grounding_gate"].append(
            "reception_unsupported_new_claim"
        )
    if _RECEPTION_ADVICE_RE.search(reception_text):
        reasons_by_gate["reception_grounding_gate"].append(
            "reception_advice_added"
        )
    if "?" in reception_text or "？" in reception_text:
        reasons_by_gate["reception_grounding_gate"].append(
            "reception_question_added"
        )

    if reception_plan is None or human_line is None or not active_moves:
        reasons_by_gate["reception_move_realization_gate"].append(
            "reception_move_realization_contract_missing"
        )
    else:
        active_ids = tuple(move.move_id for move in active_moves)
        required_ids = {
            move.move_id for move in reception_plan.moves if move.required
        }
        if not required_ids.issubset(active_ids):
            reasons_by_gate["reception_move_realization_gate"].append(
                "reception_required_move_missing"
            )
        atom_ids = set(human_line.binding.functional_atom_ids)
        expected_move_atoms = {
            item
            for move in active_moves
            for item in (
                f"reception_move:{move.move_id}",
                f"reception_move_role:{move.move_id}:{move.move_role}",
                f"reception_move_act:{move.move_id}:{move.reception_act}",
                (
                    "reception_surface_strategy:"
                    f"{move.move_id}:{move.surface_strategy}"
                ),
                (
                    "reception_move_predicate:"
                    f"{move.move_id}:{reception_move_predicate_family(move)}"
                ),
            )
        }
        if not expected_move_atoms.issubset(atom_ids):
            reasons_by_gate["reception_move_realization_gate"].append(
                "reception_move_contract_atom_missing"
            )
        for move in active_moves:
            if (
                not move.target_nucleus_ids
                or any(
                    nucleus_id not in nucleus_index
                    for nucleus_id in (
                        *move.target_nucleus_ids,
                        *move.support_nucleus_ids,
                    )
                )
            ):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_move_target_unresolved"
                )
            if (
                not move.source_evidence_span_ids
                or resolver.unresolved_ids(move.source_evidence_span_ids)
            ):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_move_evidence_unresolved"
                )
        if realized_reception is None:
            reasons_by_gate["reception_move_realization_gate"].append(
                "reception_realized_move_diagnostics_missing"
            )
        else:
            expected_roles = tuple(move.move_role for move in active_moves)
            expected_families = tuple(
                reception_move_predicate_family(move)
                for move in active_moves
            )
            if realized_reception.realized_move_ids != active_ids:
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_realized_move_id_mismatch"
                )
            if realized_reception.realized_move_roles != expected_roles:
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_realized_move_role_mismatch"
                )
            if realized_reception.move_predicate_families != expected_families:
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_realized_predicate_family_mismatch"
                )
            if realized_reception.text.strip() != reception_text.strip():
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_canonical_surface_mismatch"
                )
            if (
                human_surface_line is None
                or human_surface_line.text.strip()
                != realized_reception.text.strip()
            ):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_surface_line_mismatch"
                )
            allowed_nuclei = {
                nucleus_id
                for move in active_moves
                for nucleus_id in (
                    *move.target_nucleus_ids,
                    *move.support_nucleus_ids,
                )
            }
            allowed_evidence = {
                span_id
                for move in active_moves
                for span_id in move.source_evidence_span_ids
            }
            if (
                not realized_reception.grounded_nucleus_ids
                or set(realized_reception.grounded_nucleus_ids)
                != allowed_nuclei
            ):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_realized_nucleus_grounding_mismatch"
                )
            if (
                not realized_reception.grounded_evidence_span_ids
                or set(realized_reception.grounded_evidence_span_ids)
                != allowed_evidence
            ):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_realized_evidence_grounding_mismatch"
                )

    if human_line is None:
        reasons_by_gate["reception_role_distinctness_gate"].append(
            "reception_line_missing"
        )
    else:
        if human_line.binding.relation_ids:
            reasons_by_gate["reception_role_distinctness_gate"].append(
                "reception_relation_owner_leakage"
            )
        if any(
            atom.startswith(("relation_surface_role:", "observation_surface_role:"))
            for atom in human_line.binding.functional_atom_ids
        ):
            reasons_by_gate["reception_role_distinctness_gate"].append(
                "reception_observation_atom_leakage"
            )
    normalized_reception = _normalized(reception_text)
    observation_surface_texts = tuple(
        line.text
        for line in surface_result.lines
        if line.binding.line_role != "human_follow"
    )
    if normalized_reception and any(
        normalized_reception == _normalized(value)
        for value in observation_surface_texts
    ):
        reasons_by_gate["reception_role_distinctness_gate"].append(
            "reception_observation_summary_repetition"
        )
    if _RECEPTION_RELATION_NARRATION_RE.search(reception_text):
        reasons_by_gate["reception_role_distinctness_gate"].append(
            "reception_observation_narration_visible"
        )

    observation_anchors = {
        value
        for value in _RECEPTION_QUOTE_RE.findall(observation_text)
        if len(value) > 16
    }
    reception_anchors = {
        value
        for value in _RECEPTION_QUOTE_RE.findall(reception_text)
        if len(value) > 16
    }
    repeated_long_anchor_count = len(observation_anchors & reception_anchors)
    if repeated_long_anchor_count:
        reasons_by_gate["reception_quote_reuse_gate"].append(
            "reception_long_source_anchor_replayed"
        )
    if reception_plan is not None:
        visible_quotes = tuple(_RECEPTION_QUOTE_RE.findall(reception_text))
        if len(visible_quotes) > reception_plan.quote_policy.max_anchor_count:
            reasons_by_gate["reception_quote_reuse_gate"].append(
                "reception_quote_anchor_count_exceeded"
            )
        if any(
            len(value) > reception_plan.quote_policy.max_anchor_visible_chars
            for value in visible_quotes
        ):
            reasons_by_gate["reception_quote_reuse_gate"].append(
                "reception_quote_anchor_length_exceeded"
            )

    if _RECEPTION_POLICY_EXPOSURE_RE.search(reception_text):
        reasons_by_gate["reception_policy_exposure_gate"].append(
            "reception_internal_policy_exposure"
        )

    reception_sentence_count = _sentence_count(reception_text)
    realized_move_count = (
        len(realized_reception.realized_move_ids)
        if realized_reception is not None
        else 0
    )
    if reception_plan is None or realized_reception is None:
        reasons_by_gate["reception_depth_proportionality_gate"].append(
            "reception_depth_realization_missing"
        )
    else:
        level = reception_plan.depth_policy.level
        proportional = {
            "minimal": (
                realized_move_count == 1
                and reception_sentence_count == 1
            ),
            "focused": (
                1 <= realized_move_count <= 2
                and 1 <= reception_sentence_count <= 2
            ),
            "layered": (
                2 <= realized_move_count <= 3
                and 2 <= reception_sentence_count <= 3
            ),
        }.get(level, False)
        if not proportional:
            reasons_by_gate["reception_depth_proportionality_gate"].append(
                "reception_depth_proportionality_mismatch"
            )
        try:
            min_sentences, max_sentences = reception_effective_sentence_budget(
                reception_plan,
                sentence_plan.recovery_stage,
            )
        except GroundedHumanReceptionSurfaceError:
            reasons_by_gate["reception_depth_proportionality_gate"].append(
                "reception_effective_sentence_budget_invalid"
            )
        else:
            if not min_sentences <= reception_sentence_count <= max_sentences:
                reasons_by_gate[
                    "reception_depth_proportionality_gate"
                ].append("reception_sentence_depth_budget_mismatch")
        if realized_move_count < reception_plan.depth_policy.min_realized_moves:
            reasons_by_gate["reception_depth_proportionality_gate"].append(
                "reception_realized_move_budget_below_minimum"
            )

    if reception_plan is None or not active_moves:
        reasons_by_gate["reception_move_distinctness_gate"].append(
            "reception_move_distinctness_contract_missing"
        )
    else:
        move_signatures = tuple(
            (
                move.reception_act,
                move.target_nucleus_ids,
                move.move_role,
                reception_move_predicate_family(move),
            )
            for move in active_moves
        )
        predicate_families = tuple(
            reception_move_predicate_family(move) for move in active_moves
        )
        if len(move_signatures) != len(set(move_signatures)):
            reasons_by_gate["reception_move_distinctness_gate"].append(
                "reception_duplicate_move_contribution"
            )
        if len(predicate_families) != len(set(predicate_families)):
            reasons_by_gate["reception_move_distinctness_gate"].append(
                "reception_duplicate_predicate_family"
            )
        visible_units = tuple(
            _normalized(part)
            for part in _RECEPTION_SENTENCE_END_RE.split(reception_text)
            if _normalized(part)
        )
        if len(visible_units) != len(set(visible_units)):
            reasons_by_gate["reception_move_distinctness_gate"].append(
                "reception_duplicate_visible_contribution"
            )
        required_ids = {
            move.move_id for move in reception_plan.moves if move.required
        }
        realized_ids = set(
            realized_reception.realized_move_ids
            if realized_reception is not None
            else ()
        )
        if not required_ids.issubset(realized_ids):
            reasons_by_gate["reception_move_distinctness_gate"].append(
                "reception_required_move_absorbed"
            )

    if reception_plan is None or human_line is None:
        reasons_by_gate["reception_non_enumeration_gate"].append(
            "reception_non_enumeration_contract_missing"
        )
    else:
        if len(active_moves) > 3:
            reasons_by_gate["reception_non_enumeration_gate"].append(
                "reception_selected_move_limit_exceeded"
            )
        if (
            reception_plan.distinctness_policy.all_input_enumeration_allowed
            or "reception_non_enumeration:required"
            not in human_line.binding.functional_atom_ids
        ):
            reasons_by_gate["reception_non_enumeration_gate"].append(
                "reception_non_enumeration_policy_missing"
            )
        if human_line.binding.relation_ids:
            reasons_by_gate["reception_non_enumeration_gate"].append(
                "reception_relation_enumeration_visible"
            )
        if _RECEPTION_FIELD_ENUMERATION_RE.search(reception_text):
            reasons_by_gate["reception_non_enumeration_gate"].append(
                "reception_input_field_enumeration_visible"
            )
        if _RECEPTION_RELATION_NARRATION_RE.search(reception_text):
            reasons_by_gate["reception_non_enumeration_gate"].append(
                "reception_relation_reexplanation_visible"
            )
        observation_units = tuple(
            _normalized(part)
            for part in _RECEPTION_SENTENCE_END_RE.split(observation_text)
            if len(_normalized(part)) >= 8
        )
        replayed_units = sum(
            bool(unit and unit in normalized_reception)
            for unit in observation_units
        )
        if replayed_units >= 2 or (
            observation_units
            and normalized_reception == _normalized(observation_text)
        ):
            reasons_by_gate["reception_non_enumeration_gate"].append(
                "reception_observation_structure_reenumerated"
            )

    if not reception_text.strip():
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_surface_empty"
        )
    terminal_predicates = (
        _reception_atoms(human_line, "reception_terminal_predicate:")
        if human_line is not None
        else ()
    )
    if (
        not terminal_predicates
        or any(
            not value.startswith("human_response_")
            for value in terminal_predicates
        )
    ):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_human_terminal_predicate_missing"
        )
    expected_terminal_predicates = tuple(
        reception_terminal_predicate_kind(move.reception_act)
        for move in active_moves
    )
    if terminal_predicates and terminal_predicates != expected_terminal_predicates:
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_terminal_predicate_act_mismatch"
        )
    expected_predicate_families = tuple(
        reception_move_predicate_family(move) for move in active_moves
    )
    if realized_reception is None or (
        realized_reception.move_predicate_families
        != expected_predicate_families
    ):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_human_move_predicate_family_missing"
        )
    elif any(
        not family.startswith("human_response_")
        for family in realized_reception.move_predicate_families
    ):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_non_human_move_predicate_family"
        )
    if _RECEPTION_ANALYSIS_END_RE.search(reception_text):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_analysis_ending_visible"
        )
    if _RECEPTION_POLICY_EXPOSURE_RE.search(reception_text):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_policy_voice_visible"
        )
    if _RECEPTION_ADVICE_RE.search(reception_text):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_advice_voice_visible"
        )
    if "?" in reception_text or "？" in reception_text:
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_question_voice_visible"
        )
    if _RECEPTION_RELATION_NARRATION_RE.search(reception_text):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_observation_voice_visible"
        )
    if _RECEPTION_GENERIC_SUFFIX_RE.fullmatch(reception_text.strip()):
        reasons_by_gate["reception_human_voice_gate"].append(
            "reception_generic_empathy_suffix_only"
        )

    if _RECEPTION_IDENTITY_ACCEPTANCE_RE.search(reception_text):
        reasons_by_gate["reception_safety_boundary_gate"].append(
            "reception_identity_claim_accepted"
        )
    if _RECEPTION_RESOLUTION_GUARANTEE_RE.search(reception_text):
        reasons_by_gate["reception_safety_boundary_gate"].append(
            "reception_safety_or_resolution_guarantee_added"
        )
    if _RECEPTION_FELT_STATE_DENIAL_RE.search(reception_text):
        reasons_by_gate["reception_safety_boundary_gate"].append(
            "reception_felt_state_denied"
        )
    if _RECEPTION_MEDICAL_DIAGNOSIS_RE.search(reception_text):
        reasons_by_gate["reception_safety_boundary_gate"].append(
            "reception_medical_diagnosis_added"
        )
    if _RECEPTION_RISK_JUDGMENT_RE.search(reception_text):
        reasons_by_gate["reception_safety_boundary_gate"].append(
            "reception_risk_judgment_added"
        )
    counter_moves = tuple(
        move
        for move in active_moves
        if move.move_role == "bounded_counterposition"
    )
    if counter_moves:
        if any(
            not (*move.target_nucleus_ids, *move.support_nucleus_ids)
            or not move.source_evidence_span_ids
            or resolver.unresolved_ids(move.source_evidence_span_ids)
            for move in counter_moves
        ):
            reasons_by_gate["reception_safety_boundary_gate"].append(
                "reception_self_denial_counterposition_ungrounded"
            )
        if "Emlis" not in reception_text:
            reasons_by_gate["reception_safety_boundary_gate"].append(
                "reception_self_denial_explicit_stance_missing"
            )

    gate_statuses = {
        gate_name: (
            "failed" if reasons_by_gate[gate_name] else "passed"
        )
        for gate_name in RECEPTION_GATE_REPORT_FIELDS
    }
    all_reasons = _dedupe(
        reason
        for gate_name in RECEPTION_GATE_REPORT_FIELDS
        for reason in reasons_by_gate[gate_name]
    )
    return (
        gate_statuses,
        all_reasons,
        {
            "reception_gate_required": True,
            "reception_all_gates_passed": all(
                status == "passed" for status in gate_statuses.values()
            ),
            "reception_act": reception_act,
            "reception_stance": reception_stance,
            "reception_reference_mode": reception_reference_mode,
            "reception_terminal_predicate_kind": terminal_predicate_kind,
            "reception_depth_level": getattr(depth, "level", ""),
            "reception_safety_mode": getattr(depth, "safety_mode", ""),
            "reception_opportunity_count": (
                len(reception_plan.opportunities)
                if reception_plan is not None
                else 0
            ),
            "reception_planned_move_count": (
                len(reception_plan.moves)
                if reception_plan is not None
                else 0
            ),
            "reception_realized_move_count": realized_move_count,
            "reception_move_roles": (
                realized_reception.realized_move_roles
                if realized_reception is not None
                else ()
            ),
            "reception_surface_strategies": tuple(
                move.surface_strategy for move in active_moves
            ),
            "reception_terminal_predicate_families": (
                realized_reception.move_predicate_families
                if realized_reception is not None
                else ()
            ),
            "raw_character_count_used": bool(
                getattr(depth, "raw_character_count_used", False)
            ),
            "reception_sentence_count": reception_sentence_count,
            "repeated_long_anchor_count": repeated_long_anchor_count,
        },
    )


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
    mechanical_restatement_gate: GateStatus
    question_dominance_gate: GateStatus
    depth_adequacy_gate: GateStatus
    two_stage_contract_gate: GateStatus
    reception_plan_gate: GateStatus
    reception_grounding_gate: GateStatus
    reception_role_distinctness_gate: GateStatus
    reception_quote_reuse_gate: GateStatus
    reception_policy_exposure_gate: GateStatus
    reception_human_voice_gate: GateStatus
    reception_safety_boundary_gate: GateStatus
    reception_depth_plan_gate: GateStatus
    reception_move_realization_gate: GateStatus
    reception_depth_proportionality_gate: GateStatus
    reception_move_distinctness_gate: GateStatus
    reception_non_enumeration_gate: GateStatus
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
    mechanical_restatement_detected: bool
    two_stage_observation_section_present: bool
    two_stage_reception_section_present: bool
    reception_gate_required: bool
    reception_act: str
    reception_stance: str
    reception_reference_mode: str
    reception_terminal_predicate_kind: str
    reception_depth_level: str
    reception_safety_mode: str
    reception_opportunity_count: int
    reception_planned_move_count: int
    reception_realized_move_count: int
    reception_move_roles: tuple[str, ...]
    reception_surface_strategies: tuple[str, ...]
    reception_terminal_predicate_families: tuple[str, ...]
    raw_character_count_used: bool
    reception_sentence_count: int
    repeated_long_anchor_count: int

    @property
    def passed(self) -> bool:
        return self.semantic_quality_gate == "passed"

    @property
    def all_reception_gates_passed(self) -> bool:
        return bool(
            self.reception_gate_required
            and all(
                getattr(self, field_name) == "passed"
                for field_name in RECEPTION_GATE_REPORT_FIELDS
            )
        )

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
            "mechanical_restatement_gate": self.mechanical_restatement_gate,
            "question_dominance_gate": self.question_dominance_gate,
            "depth_adequacy_gate": self.depth_adequacy_gate,
            "two_stage_contract_gate": self.two_stage_contract_gate,
            "reception_plan_gate": self.reception_plan_gate,
            "reception_grounding_gate": self.reception_grounding_gate,
            "reception_role_distinctness_gate": self.reception_role_distinctness_gate,
            "reception_quote_reuse_gate": self.reception_quote_reuse_gate,
            "reception_policy_exposure_gate": self.reception_policy_exposure_gate,
            "reception_human_voice_gate": self.reception_human_voice_gate,
            "reception_safety_boundary_gate": self.reception_safety_boundary_gate,
            "reception_depth_plan_gate": self.reception_depth_plan_gate,
            "reception_move_realization_gate": self.reception_move_realization_gate,
            "reception_depth_proportionality_gate": self.reception_depth_proportionality_gate,
            "reception_move_distinctness_gate": self.reception_move_distinctness_gate,
            "reception_non_enumeration_gate": self.reception_non_enumeration_gate,
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
            "mechanical_restatement_detected": self.mechanical_restatement_detected,
            "two_stage_required": self.two_stage_contract_gate != "not_evaluated",
            "two_stage_observation_section_present": self.two_stage_observation_section_present,
            "two_stage_reception_section_present": self.two_stage_reception_section_present,
            "reception_gate_required": self.reception_gate_required,
            "reception_all_gates_passed": self.all_reception_gates_passed,
            "reception_act": self.reception_act,
            "reception_stance": self.reception_stance,
            "reception_reference_mode": self.reception_reference_mode,
            "reception_terminal_predicate_kind": self.reception_terminal_predicate_kind,
            "reception_depth_level": self.reception_depth_level,
            "reception_safety_mode": self.reception_safety_mode,
            "reception_opportunity_count": self.reception_opportunity_count,
            "reception_planned_move_count": self.reception_planned_move_count,
            "reception_realized_move_count": self.reception_realized_move_count,
            "reception_move_roles": list(self.reception_move_roles),
            "reception_surface_strategies": list(
                self.reception_surface_strategies
            ),
            "reception_terminal_predicate_families": list(
                self.reception_terminal_predicate_families
            ),
            "raw_character_count_used": self.raw_character_count_used,
            "reception_sentence_count": self.reception_sentence_count,
            "repeated_long_anchor_count": self.repeated_long_anchor_count,
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


_GROUNDED_GATE_BODY_FREE_META_KEYS: Final = frozenset(
    GroundedObservationGateReport.__dataclass_fields__.keys()
) | frozenset(
    {
        "delivery_status",
        "reception_all_gates_passed",
        "two_stage_required",
        "delivery_status_separated_from_product_readfeel",
        "raw_input_included",
        "raw_text_included",
        "source_text_included",
        "comment_text_included",
        "surface_text_included",
        "candidate_body_included",
        "public_contract_changed",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
    }
)


def grounded_gate_meta_is_body_free(meta: Mapping[str, Any]) -> bool:
    """Validate the exact report-meta envelope before it enters reply meta."""

    if not isinstance(meta, Mapping):
        return False
    if set(meta) != _GROUNDED_GATE_BODY_FREE_META_KEYS:
        return False
    for flag_name in (
        "raw_input_included",
        "raw_text_included",
        "source_text_included",
        "comment_text_included",
        "surface_text_included",
        "candidate_body_included",
    ):
        if meta.get(flag_name) is not False:
            return False
    if not isinstance(meta.get("rejection_reasons"), list):
        return False
    for value in meta.values():
        if isinstance(value, str):
            if not _GROUNDED_GATE_BODY_FREE_CODE_RE.fullmatch(value):
                return False
            continue
        if isinstance(value, list):
            if not all(
                isinstance(item, str)
                and _GROUNDED_GATE_BODY_FREE_CODE_RE.fullmatch(item)
                for item in value
            ):
                return False
            continue
        if isinstance(value, (dict, tuple, set, bytes, bytearray)):
            return False
    return True


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

    try:
        plan_issues = validate_grounded_observation_plan(plan, resolver)
    except (AttributeError, KeyError, TypeError, ValueError):
        plan_issues = ("grounded_plan_validation_contract_invalid",)
    try:
        sentence_issues = validate_grounded_sentence_plan(
            sentence_plan,
            plan,
            resolver,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        sentence_issues = ("grounded_sentence_validation_contract_invalid",)
    try:
        surface_issues = validate_grounded_surface_result(
            surface_result,
            sentence_plan,
            plan,
            resolver,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        surface_issues = ("grounded_surface_validation_contract_invalid",)
    semantic_subcheck_reasons, anti_template_reasons, depth_reasons = _semantic_subcheck_reasons(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface_result,
        resolver=resolver,
    )
    two_stage_observation, two_stage_reception, two_stage_reasons = split_two_stage_surface(
        surface_result.text
    )
    (
        reception_gate_statuses,
        reception_gate_reasons,
        reception_gate_diagnostics,
    ) = _evaluate_reception_gates(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface_result,
        resolver=resolver,
        observation_text=two_stage_observation,
        reception_text=two_stage_reception,
    )

    validation_issues = _dedupe((*plan_issues, *sentence_issues, *surface_issues))
    plan_valid = not validation_issues

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
    mechanical_restatement_detected = bool(
        surface_result.status == "generated"
        and _ledger_narration_visible(surface_result.text)
    )
    if surface_result.status == "generated":
        mechanical_restatement_gate: GateStatus = (
            "failed" if mechanical_restatement_detected else "passed"
        )
    else:
        mechanical_restatement_gate = "not_evaluated"
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
    observation_plan_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role != "human_follow"
    )
    reception_plan_lines = tuple(
        line
        for line in sentence_plan.lines
        if line.binding.line_role == "human_follow"
    )
    if separate_safety_owner or surface_result.status == "unavailable":
        two_stage_contract_gate: GateStatus = "not_evaluated"
        two_stage_contract_passed = True
    else:
        two_stage_contract_passed = bool(
            generated
            and plan.response_plan.surface_shape == "two_stage"
            and not two_stage_reasons
            and two_stage_observation
            and two_stage_reception
            and observation_plan_lines
            and len(reception_plan_lines) == 1
            and "human_follow_delivery:separate"
            in reception_plan_lines[0].binding.functional_atom_ids
            and not any(
                "human_follow_delivery:integrated"
                in line.binding.functional_atom_ids
                for line in sentence_plan.lines
            )
        )
        two_stage_contract_gate = "passed" if two_stage_contract_passed else "failed"
    all_semantic_gates_passed = bool(
        plan_valid
        and evidence_resolved
        and required_coverage
        and text_semantic_retained
        and anti_template
        and not mechanical_restatement_detected
        and question_free
        and depth_adequate
        and two_stage_contract_passed
        and (
            not reception_gate_diagnostics["reception_gate_required"]
            or reception_gate_diagnostics["reception_all_gates_passed"]
        )
        and generated
    )

    reasons: list[str] = []
    if not plan_valid:
        reasons.extend(validation_issues or ("grounded_plan_invalid",))
    if not evidence_resolved:
        reasons.extend(unresolved_binding_ids or ("grounded_evidence_resolution_failed",))
    if not required_coverage:
        reasons.append("grounded_required_coverage_failed")
    if not text_semantic_retained:
        reasons.extend(semantic_subcheck_reasons or ("grounded_text_semantic_retention_failed",))
    if not anti_template:
        reasons.extend(anti_template_reasons or ("grounded_anti_template_failed",))
    if mechanical_restatement_detected:
        reasons.append("grounded_mechanical_restatement_surface")
    if not question_free:
        reasons.append("grounded_question_dominance_failed")
    if not depth_adequate:
        reasons.extend(depth_reasons or ("grounded_depth_adequacy_failed",))
    if not two_stage_contract_passed:
        reasons.extend(two_stage_reasons)
        if plan.response_plan.surface_shape != "two_stage":
            reasons.append("mandatory_two_stage_plan_shape_missing")
        if not observation_plan_lines:
            reasons.append("mandatory_two_stage_observation_plan_line_missing")
        if len(reception_plan_lines) != 1:
            reasons.append("mandatory_two_stage_reception_plan_line_count_invalid")
        elif (
            "human_follow_delivery:separate"
            not in reception_plan_lines[0].binding.functional_atom_ids
        ):
            reasons.append("mandatory_two_stage_reception_not_separate")
        if not reasons:
            reasons.append("mandatory_two_stage_contract_failed")
    reasons.extend(reception_gate_reasons)
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
        mechanical_restatement_gate=mechanical_restatement_gate,
        question_dominance_gate="passed" if question_free else "failed",
        depth_adequacy_gate="passed" if depth_adequate else "failed",
        two_stage_contract_gate=two_stage_contract_gate,
        reception_plan_gate=reception_gate_statuses["reception_plan_gate"],
        reception_grounding_gate=reception_gate_statuses[
            "reception_grounding_gate"
        ],
        reception_role_distinctness_gate=reception_gate_statuses[
            "reception_role_distinctness_gate"
        ],
        reception_quote_reuse_gate=reception_gate_statuses[
            "reception_quote_reuse_gate"
        ],
        reception_policy_exposure_gate=reception_gate_statuses[
            "reception_policy_exposure_gate"
        ],
        reception_human_voice_gate=reception_gate_statuses[
            "reception_human_voice_gate"
        ],
        reception_safety_boundary_gate=reception_gate_statuses[
            "reception_safety_boundary_gate"
        ],
        reception_depth_plan_gate=reception_gate_statuses[
            "reception_depth_plan_gate"
        ],
        reception_move_realization_gate=reception_gate_statuses[
            "reception_move_realization_gate"
        ],
        reception_depth_proportionality_gate=reception_gate_statuses[
            "reception_depth_proportionality_gate"
        ],
        reception_move_distinctness_gate=reception_gate_statuses[
            "reception_move_distinctness_gate"
        ],
        reception_non_enumeration_gate=reception_gate_statuses[
            "reception_non_enumeration_gate"
        ],
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
        mechanical_restatement_detected=mechanical_restatement_detected,
        two_stage_observation_section_present=bool(two_stage_observation),
        two_stage_reception_section_present=bool(two_stage_reception),
        reception_gate_required=reception_gate_diagnostics[
            "reception_gate_required"
        ],
        reception_act=reception_gate_diagnostics["reception_act"],
        reception_stance=reception_gate_diagnostics["reception_stance"],
        reception_reference_mode=reception_gate_diagnostics[
            "reception_reference_mode"
        ],
        reception_terminal_predicate_kind=reception_gate_diagnostics[
            "reception_terminal_predicate_kind"
        ],
        reception_depth_level=reception_gate_diagnostics[
            "reception_depth_level"
        ],
        reception_safety_mode=reception_gate_diagnostics[
            "reception_safety_mode"
        ],
        reception_opportunity_count=reception_gate_diagnostics[
            "reception_opportunity_count"
        ],
        reception_planned_move_count=reception_gate_diagnostics[
            "reception_planned_move_count"
        ],
        reception_realized_move_count=reception_gate_diagnostics[
            "reception_realized_move_count"
        ],
        reception_move_roles=reception_gate_diagnostics[
            "reception_move_roles"
        ],
        reception_surface_strategies=reception_gate_diagnostics[
            "reception_surface_strategies"
        ],
        reception_terminal_predicate_families=reception_gate_diagnostics[
            "reception_terminal_predicate_families"
        ],
        raw_character_count_used=reception_gate_diagnostics[
            "raw_character_count_used"
        ],
        reception_sentence_count=reception_gate_diagnostics[
            "reception_sentence_count"
        ],
        repeated_long_anchor_count=reception_gate_diagnostics[
            "repeated_long_anchor_count"
        ],
    )


__all__ = [
    "GROUND_OBSERVATION_GATE_SCHEMA_VERSION",
    "GROUND_OBSERVATION_REPLY_GENERATION_PATH",
    "RECEPTION_GATE_REPORT_FIELDS",
    "GroundedObservationGateReport",
    "grounded_gate_meta_is_body_free",
    "evaluate_grounded_observation_gate",
]
