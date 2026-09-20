# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free semantic and RR6 Depth/Move Gate for the canonical reply path.

The gate consumes the plan, sentence plan, realized surface, and the request-
local Evidence resolver that actually produced the candidate.  It does not
reconstruct meaning from the public body and it never serializes source text.
"""

from dataclasses import dataclass
from itertools import combinations
import re
from typing import Any, Final, Literal, Mapping

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_human_reception import (
    _SOURCE_GROUNDED_FINITE_END_RE,
    SelectedSubjectiveReceptionInputV1,
    GroundedHumanReceptionSurfaceError,
    replay_source_grounded_human_reception_from_plan,
    reception_action_is_future_intention,
    reception_action_is_performed,
    reception_active_moves,
    reception_effective_move_reference_mode,
    reception_effective_sentence_budget,
    reception_move_predicate_family,
    reception_terminal_predicate_kind,
    realize_grounded_human_reception,
    resolve_grounded_reception_move_referent,
    source_grounded_performed_action_nominal,
    source_grounded_future_action_nominal,
    source_grounded_retained_wish_nominal,
    source_grounded_feeling_target_nominal,
    source_grounded_unfinished_referent,
    source_grounded_current_expression_nominal,
    source_grounded_thread_answer_nominal,
    restore_thread_answer_nominal,
    source_grounded_negative_context_nominal,
    final_reception_source_anchor_text,
)
from emlis_ai_grounded_observation_plan import (
    FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
    GroundedObservationPlan,
    is_grounded_positive_feeling,
    validate_grounded_human_reception_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_sentence_surface import (
    DIRECTIONAL_GROUNDED_RELATION_TYPES,
    OBSERVATION_SECTION_LABEL,
    RECEPTION_SECTION_LABEL,
    GroundedSentencePlan,
    GroundedSurfaceResult,
    expected_human_follow_role,
    parse_grounded_surface_body_bytes,
    realize_grounded_human_follow_text,
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
_BODY_INVERSE_ANCHOR_NORMALIZE_RE: Final = re.compile(
    r"[\s\u3000、。,.!！?？「」『』（）()・:：;；'’\"]"
)
_BODY_INVERSE_LEADING_CONNECTOR_RE: Final = re.compile(
    r"^(?:とそれから|そして|それでも|けれど|だけど|でも|で)"
)
_BODY_INVERSE_RELATION_MARKERS_BY_TYPE: Final[dict[str, frozenset[str]]] = {
    "temporal_before_after": frozenset({"from_to", "change"}),
    "shift_from_to": frozenset({"from_to", "change"}),
    "contrast": frozenset({"coexistence", "counterdirection"}),
    "coexistence": frozenset({"coexistence"}),
    "user_stated_cause": frozenset({"link", "from_to"}),
    "user_stated_result": frozenset({"link", "from_to", "change"}),
    "attempt_and_block": frozenset({"coexistence", "counterdirection"}),
    "wish_and_constraint": frozenset({"coexistence", "counterdirection"}),
    "action_supports_change": frozenset({"link"}),
    "evaluation_about_event": frozenset({"change", "link"}),
    "self_evaluation_about_state": frozenset({"change", "coexistence"}),
    "preserves_despite": frozenset({"coexistence", "counterdirection"}),
    "uncertain_connection": frozenset({"coexistence", "change", "link"}),
    "continuation_or_refusal": frozenset({"counterdirection", "coexistence"}),
}
_BODY_INVERSE_RECEPTION_ACT_TARGET_MARKERS: Final[
    dict[str, frozenset[str]]
] = {
    "stay_with_current_burden": frozenset({"target_burden", "target_words"}),
    "honor_concrete_effort": frozenset({"target_effort", "target_words"}),
    "protect_retained_intention": frozenset({"target_intention", "target_words"}),
    "recognize_lived_change": frozenset({"target_change", "target_words"}),
    "hold_help_seeking": frozenset({"target_help", "target_words"}),
    "bounded_counter_self_denial": frozenset(
        {"target_self_evaluation", "target_words"}
    ),
    "respect_words_placed": frozenset({"target_words"}),
}
_BODY_INVERSE_RECEPTION_RELATION_PREFERENCE: Final[
    dict[str, tuple[str, ...]]
] = {
    "protect_retained_intention": (
        "preserves_despite",
        "wish_and_constraint",
        "coexistence",
        "contrast",
        "continuation_or_refusal",
    ),
    "hold_help_seeking": (
        "wish_and_constraint",
        "preserves_despite",
        "coexistence",
        "contrast",
    ),
    "honor_concrete_effort": (
        "action_supports_change",
        "temporal_before_after",
        "user_stated_result",
    ),
    "recognize_lived_change": (
        "action_supports_change",
        "temporal_before_after",
        "contrast",
    ),
}


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
    if getattr(resolver, "source_contract", None) == "cocolon.cmee.emlis_thread.v1":
        return final_reception_source_anchor_text(nucleus.nucleus_id, {nucleus.nucleus_id: nucleus}, resolver)
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
    # Compare sensation families in the original inflection of an exactly
    # witnessed answer nominal. This local check view never changes body
    # bytes, lexical coverage, or the independent inverse requirement.
    # A second or unrelated sensation expression remains fully checked.
    sensation_body = surface_result.text.encode("utf-8")
    sensation_witness = None
    replacements = set()
    focused_source_nuclei = set()
    reception_plan = plan.response_plan.human_reception_plan
    for move in reception_plan.moves if reception_plan is not None else ():
        if len(move.target_nucleus_ids) > 1 or move.support_nucleus_ids:
            if sensation_witness is None:
                sensation_witness = parse_grounded_surface_body_bytes(sensation_body)
            for sentence in sensation_witness.sentences:
                if sentence.section == "reception":
                    replacements.update(_body_inverse_thread_answer_group(
                        sensation_body, sensation_witness, sentence, move, plan, resolver))
                    replacements.update(_body_inverse_thread_received_group(
                        sensation_body, sensation_witness, sentence, move, plan, resolver) or ())
                    from emlis_ai_grounded_observation_plan import source_owned_relational_focus
                    focus = source_owned_relational_focus(move, plan)
                    if (focus is not None and focus[0] == "received_experience_focus"
                        and _read_relational_focus_discourse(
                            sensation_body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode(),
                            move, plan, resolver, None) is not None):
                        # Exact source roles survive the focus transposition;
                        # a source-string substring is no longer its proof.
                        focused_source_nuclei.add(focus[2].nucleus_id)
            continue
        answer_nominal = source_grounded_thread_answer_nominal(move, plan, nucleus_index, resolver)
        if answer_nominal is None:
            continue
        _, source, grammar, when, nominal = answer_nominal
        nominal_bytes = nominal.encode("utf-8")
        if sensation_body.count(nominal_bytes) != 1:
            continue
        start = sensation_body.index(nominal_bytes)
        end = start + len(nominal_bytes)
        if sensation_witness is None:
            sensation_witness = parse_grounded_surface_body_bytes(sensation_body)
        if (restore_thread_answer_nominal(nominal, grammar, when) == source
            and any(m.section == "reception" and m.marker_code == "thread_answer_nominal"
                    and start <= m.utf8_byte_start and m.utf8_byte_end == end for m in sensation_witness.markers)
            and not any(q.utf8_byte_start < end and start < q.utf8_byte_end for q in sensation_witness.quotes)
            and not any(m.marker_code == "secondary_quote_boundary" and m.utf8_byte_start < end
                        and start < m.utf8_byte_end for m in sensation_witness.markers)):
            replacements.add((start, end, source.encode("utf-8")))
    # Each offset addresses the original body. Dedupe identical witnesses
    # and keep overlapping, disagreeing ranges out of this local view.
    disjoint = tuple(row for row in replacements if not any(
        other != row and row[0] < other[1] and other[0] < row[1] for other in replacements
    ))
    for start, end, source in sorted(disjoint, reverse=True):
        sensation_body = sensation_body[:start] + source + sensation_body[end:]
    sensation_text = sensation_body.decode("utf-8")
    for nucleus in plan.nuclei:
        attributes = set(nucleus.semantic_frame.attribute_codes)
        if "lexical:preserve_source_predicate" in attributes:
            source_anchor = _nucleus_source_text(nucleus, resolver)
            anchors = {_normalized(source_anchor)}
            decision_roles = tuple(role for role in ("choice", "timing")
                if "lexical:source_independent_decision_" + role in attributes)
            if len(decision_roles) == 1:
                from emlis_ai_grounded_observation_plan import _source_independent_decision_clause_parts
                clause = source_anchor.strip(" 　。．.")
                if (_source_independent_decision_clause_parts(clause) or (None,))[0] == decision_roles[0]:
                    # Only these complete, source-proven hosts have a plain
                    # attributive form here; no shortened source stem counts.
                    anchors.add(_normalized(re.sub(r"決められません$", "決められない",
                        re.sub(r"迷っています$", "迷っている", clause))))
            if (any(anchors) and not any(anchor and anchor in surface_normalized for anchor in anchors)
                and nucleus.nucleus_id not in focused_source_nuclei):
                semantic.append("lexical_anchor_missing")
        if "lexical:no_new_sensation_family" in attributes:
            for pattern in _SENSATION_FAMILIES.values():
                if pattern.search(sensation_text) and not pattern.search(source_text):
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
    selected_subjective_input: SelectedSubjectiveReceptionInputV1 | None = None,
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
    canonical_reception_text = ""
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
                canonical_reception_text = realize_grounded_human_follow_text(
                    human_line,
                    plan,
                    resolver,
                    selected_subjective_input=selected_subjective_input,
                )
            except (AttributeError, KeyError, TypeError, ValueError):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_canonical_surface_owner_failed"
                )
            if _body_inverse_is_final_stage1_plan(plan):
                try:
                    realized_reception = replay_source_grounded_human_reception_from_plan(
                        reception_plan, nucleus_index, resolver,
                        plan=plan,
                        recovery_stage=sentence_plan.recovery_stage,
                        clause_plans=human_line.reception_clause_plans,
                        selected_subjective_input=selected_subjective_input,
                    )
                    if not _received_discourse_equivalent(reception_text, realized_reception.text,
                        reception_plan, human_line.reception_clause_plans, plan, resolver,
                        selected_subjective_input):
                        raise GroundedHumanReceptionSurfaceError(
                            "human_reception_surface_replay_mismatch"
                        )
                except (
                    GroundedHumanReceptionSurfaceError,
                    AttributeError,
                    KeyError,
                    TypeError,
                ):
                    reasons_by_gate["reception_move_realization_gate"].append(
                        "reception_actual_surface_contract_failed"
                    )
            else:
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
                final_source_fidelity=FINAL_STAGE1_GROUNDED_PROJECTION_VERSION in plan.source_contracts,
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
            expected_reception_text = (
                canonical_reception_text or realized_reception.text
            )
            if not _received_discourse_equivalent(reception_text.strip(), expected_reception_text.strip(),
                reception_plan, human_line.reception_clause_plans, plan, resolver,
                selected_subjective_input):
                reasons_by_gate["reception_move_realization_gate"].append(
                    "reception_canonical_surface_mismatch"
                )
            if (
                human_surface_line is None
                or human_surface_line.text.strip()
                != reception_text.strip()
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
    # Aggregate contract atoms retain each terminal kind once. The Move
    # predicate-family and visible-duty checks below remain per Move.
    expected_terminal_predicates = _dedupe(
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
    # A source-proven negative degree is not a resolution guarantee. Exempt
    # only the embedded assertion's exact range inside a complete, unchanged
    # nominal object; added assurances elsewhere are still checked normally.
    denied_assertion_ranges = []
    from emlis_ai_grounded_observation_plan import _source_provisional_degree_parts
    for move in active_moves:
        if len(move.target_nucleus_ids) != 1 or move.support_nucleus_ids:
            continue
        n = nucleus_index.get(move.target_nucleus_ids[0])
        if (n is None or "lexical:source_provisional_degree" not in n.semantic_frame.attribute_codes
            or n.source_fields != ("memo",) or len(n.source_span_ids) != 1
            or move.reception_act != "stay_with_current_burden"):
            continue
        source = str(resolver.resolve(n.source_span_ids[0]).raw_text)
        parts = _source_provisional_degree_parts(source)
        if parts is None:
            continue
        for sentence in re.finditer(r"[^。！？!?]+。", reception_text):
            match = re.fullmatch(re.escape(source) + r"という言葉を小さくせずに(?:"
                r"(?:受け止めて|気にかけて)(?:います|いて)|(?:受け止め|気にかけ)たいです)。", sentence.group())
            if match:
                denied_assertion_ranges.extend((sentence.start() + start, sentence.start() + end)
                    for role, start, end, _ in parts if role == "assertion")
    if any(not any(start <= m.start() and m.end() <= end for start, end in denied_assertion_ranges)
           for m in _RECEPTION_RESOLUTION_GUARANTEE_RE.finditer(reception_text)):
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
class GroundedBodyInverseEvaluation:
    """Body-free result of matching a byte-derived witness to required duties."""

    passed: bool
    body_sha256: str
    observation_line_count: int
    reception_line_count: int
    observation_sentence_count: int
    reception_sentence_count: int
    source_anchor_count: int
    relation_marker_count: int
    uncertainty_marker_count: int
    reception_marker_count: int
    failure_codes: tuple[str, ...]

    def as_body_free_meta(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "body_sha256": self.body_sha256,
            "observation_line_count": self.observation_line_count,
            "reception_line_count": self.reception_line_count,
            "observation_sentence_count": self.observation_sentence_count,
            "reception_sentence_count": self.reception_sentence_count,
            "source_anchor_count": self.source_anchor_count,
            "relation_marker_count": self.relation_marker_count,
            "uncertainty_marker_count": self.uncertainty_marker_count,
            "reception_marker_count": self.reception_marker_count,
            "failure_codes": list(self.failure_codes),
            "raw_input_included": False,
            "raw_text_included": False,
            "source_text_included": False,
            "surface_text_included": False,
            "candidate_body_included": False,
        }


def _body_inverse_normalized_anchor(value: Any) -> str:
    compact = _BODY_INVERSE_ANCHOR_NORMALIZE_RE.sub("", str(value or "")).lower()
    while True:
        reduced = _BODY_INVERSE_LEADING_CONNECTOR_RE.sub("", compact, count=1)
        if reduced == compact:
            return compact
        compact = reduced


def _body_inverse_is_final_stage1_plan(plan: GroundedObservationPlan) -> bool:
    return FINAL_STAGE1_GROUNDED_PROJECTION_VERSION in tuple(
        getattr(plan, "source_contracts", ())
    )


def _body_inverse_typed_source_fragment(
    nucleus: Any,
    raw_text: str,
) -> str | None:
    """Independently recover a plan-owned typed source obligation."""

    attributes = tuple(
        getattr(nucleus.semantic_frame, "attribute_codes", ())
    )
    marker_rows = tuple(
        code
        for code in attributes
        if code == "semantic_role:generic_relation_fragment"
    )
    scalar_rows = tuple(
        code
        for code in attributes
        if isinstance(code, str)
        and code.startswith("source_fragment_scalar_range:")
    )
    source_rows = tuple(
        code
        for code in attributes
        if isinstance(code, str)
        and code.startswith("source_fragment_scalar_source:")
    )
    legacy_rows = tuple(
        code
        for code in attributes
        if isinstance(code, str)
        and code.startswith(("surface_scalar_range:", "surface_scalar_source:"))
    )
    if not marker_rows:
        if scalar_rows or source_rows or legacy_rows:
            return ""
        return None
    if (
        len(marker_rows) != 1
        or len(scalar_rows) != 1
        or source_rows
        != ("source_fragment_scalar_source:normalized_raw_text",)
        or legacy_rows
    ):
        return ""
    parts = scalar_rows[0].split(":")
    if len(parts) != 3:
        return ""
    try:
        start, end = int(parts[1]), int(parts[2])
    except ValueError:
        return ""
    normalized_raw = re.sub(
        r"\s+",
        " ",
        str(raw_text or "").replace("\u3000", " "),
    ).strip()
    if not (0 <= start < end <= len(normalized_raw)):
        return ""
    fragment = normalized_raw[start:end]
    if not fragment or fragment != fragment.strip():
        return ""
    return fragment


def _body_inverse_action_is_performed(nucleus: Any) -> bool:
    return reception_action_is_performed(nucleus, final_source_fidelity=True)


def _body_inverse_action_is_future_intention(nucleus: Any) -> bool:
    return reception_action_is_future_intention(nucleus, final_source_fidelity=True)


def _body_inverse_source_values(
    line: Any,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    span_ids: list[str] = []
    for nucleus_id in line.binding.nucleus_ids:
        nucleus = nucleus_index.get(nucleus_id)
        if nucleus is None:
            continue
        for span_id in nucleus.source_span_ids:
            if span_id not in span_ids:
                span_ids.append(span_id)
    for span_id in line.binding.evidence_span_ids:
        if span_id not in span_ids:
            span_ids.append(span_id)
    values: list[str] = []
    for span_id in span_ids:
        try:
            raw_text = str(resolver.resolve(span_id).raw_text or "")
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
        normalized = _body_inverse_normalized_anchor(raw_text)
        if normalized and normalized not in values:
            values.append(normalized)
    return tuple(values)


def _body_inverse_nucleus_source_values(
    nucleus_id: str,
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    nucleus = next(
        (item for item in plan.nuclei if item.nucleus_id == nucleus_id),
        None,
    )
    if nucleus is None:
        return ()
    values: list[str] = []
    for span_id in nucleus.source_span_ids:
        try:
            raw_text = str(resolver.resolve(span_id).raw_text or "")
        except (AttributeError, KeyError, TypeError, ValueError):
            continue
        typed = _body_inverse_typed_source_fragment(nucleus, raw_text)
        if typed == "":
            return ()
        normalized = _body_inverse_normalized_anchor(
            typed if typed is not None else raw_text
        )
        if normalized and normalized not in values:
            values.append(normalized)
    return tuple(values)


def _body_inverse_observation_change_reference(
    body, witness, line, planned_line, plan, resolver,
):
    """Resolve an anaphoric change from adjacent observation bytes alone.

    Neither the author, its eligibility helper, nor forward surface bindings
    are consulted. A named, complete change and feeling must form the first
    contrast; the next sentence owes the original action and that same change.
    """
    visible = _body_inverse_visible_text(body, line)
    exterior = re.sub(r"「[^「」]*」|『[^『』]*』", "", visible)
    if "その変化" not in exterior:
        return frozenset(), ()
    failure = ("body_inverse_observation_change_reference_unbound",)
    binding = planned_line.binding
    relations = {r.relation_id: r for r in plan.relations}
    if len(binding.relation_ids) != 2 or "scope_hedge" in binding.functional_atom_ids:
        return frozenset(), failure
    contrast, support = (relations.get(rid) for rid in binding.relation_ids)
    if (contrast is None or support is None
        or contrast.type != "contrast" or support.type != "action_supports_change"
        or contrast.from_nucleus_id != support.to_nucleus_id
        or len({support.from_nucleus_id, support.to_nucleus_id, contrast.to_nucleus_id}) != 3
        or any(r.grounding_kind != "user_stated_relation" for r in (contrast, support))):
        return frozenset(), failure
    index = {n.nucleus_id: n for n in plan.nuclei}
    nuclei = tuple(index.get(nid) for nid in
        (support.from_nucleus_id, support.to_nucleus_id, contrast.to_nucleus_id))
    if any(n is None for n in nuclei):
        return frozenset(), failure
    action, change, feeling = nuclei
    if (not _body_inverse_action_is_performed(action)
        or action.semantic_frame.time_scope != "past"
        or change.kind != "change" or change.semantic_frame.time_scope != "past"
        or change.semantic_frame.modality not in {"fact", "feeling"}
        or feeling.kind not in {"reaction", "state"}
        or _body_inverse_action_is_performed(feeling) or _body_inverse_action_is_future_intention(feeling)
        or action.source_span_ids != change.source_span_ids
        or any(n.grounding_kind != "explicit" or n.source_fields != ("memo",)
            or len(n.source_span_ids) != 1 or n.semantic_frame.actor != "current_user"
            or any(c.startswith("thread_time:") for c in n.semantic_frame.attribute_codes)
            for n in nuclei)):
        return frozenset(), failure
    sources = tuple(_body_inverse_nucleus_source_values(n.nucleus_id, plan, resolver) for n in nuclei)
    if (any(len(values) != 1 for values in sources)
        or any(re.search(r"[「」『』“”‘’\"?？!！;；…‥\n]",
                         str(resolver.resolve(n.source_span_ids[0]).raw_text or "")) for n in nuclei)):
        return frozenset(), failure
    action_source, change_source, feeling_source = (values[0] for values in sources)
    if any(a in b for i, (a,) in enumerate(sources) for j, (b,) in enumerate(sources) if i != j):
        return frozenset(), failure
    sentences = tuple(row for row in witness.sentences if row.section == "observation"
        and row.section_line_ordinal == line.section_ordinal)
    if len(sentences) < 2:
        return frozenset(), failure
    first, second = (_body_inverse_visible_text(body, row) for row in sentences[:2])
    if planned_line.surface_function == "render_limited_scope":
        before = re.fullmatch(r"今の入力では、「([^「」]+)」という変化と「([^「」]+)」"
                              r"の異なる向きが確認できます。", first)
        after = re.fullmatch(r"また、「([^「」]+)」という行動からその変化へのつながりも確認できます。", second)
    else:
        before = re.fullmatch(r"「([^「」]+)」という変化と「([^「」]+)」"
                              r"が、異なる向きのまま同時にあります。", first)
        after = re.fullmatch(r"「([^「」]+)」という行動からその変化へつながっています。", second)
    if (not before or not after
        or tuple(map(_body_inverse_normalized_anchor, before.groups())) != (change_source, feeling_source)
        or _body_inverse_normalized_anchor(after.group(1)) != action_source
        or exterior.count("その変化") != 1):
        return frozenset(), failure
    return frozenset((support.relation_id,)), ()


def _body_inverse_adjacent_action_context(
    body, parsed_sentence, previous_sentence, clause, previous_clause,
    move, reception_plan, plan, resolver,
) -> bool:
    """Read the two actual sentences without invoking the author/reuse rule.

    A coordination marker cannot replace arbitrary missing context. Its
    immediately preceding sentence must visibly contain the same complete
    action/background and primary source, assigned to the reciprocal Moves.
    """
    if (clause.move_ids != (move.move_id,)
        or move.reference_mode != "anaphoric_first" or not move.required
        or move.move_role != "felt_response" or move.reception_act != "honor_concrete_effort"
        or len(move.target_nucleus_ids) != 1 or len(move.support_nucleus_ids) != 1):
        return False
    index = reception_plan.moves.index(move)
    if index == 0:
        return False
    previous = reception_plan.moves[index - 1]
    if (previous_clause.move_ids != (previous.move_id,) or not previous.required
        or previous.reference_mode != "short_anchor_if_ambiguous"
        or previous.target_nucleus_ids != move.support_nucleus_ids
        or previous.support_nucleus_ids != move.target_nucleus_ids
        or set(move.target_nucleus_ids) & set(move.support_nucleus_ids)):
        return False
    nuclei = {n.nucleus_id: n for n in plan.nuclei}
    action = nuclei[move.target_nucleus_ids[0]]
    context = nuclei[move.support_nucleus_ids[0]]
    pair_ids = {action.nucleus_id, context.nucleus_id}
    if (action.kind != "action" or action.semantic_frame.modality != "fact"
        or not _body_inverse_action_is_performed(action)
        or any(n.semantic_frame.actor != "current_user" or n.retention != "required"
               or n.source_fields not in {("memo",), ("memo_action",)}
               for n in (action, context))
        or set(action.source_span_ids) & set(context.source_span_ids)
        or any(r.relation_id in plan.coverage_requirements.required_relation_ids
               and pair_ids.intersection((r.from_nucleus_id, r.to_nucleus_id))
               for r in plan.relations)
        or any(re.search(r"[「」『』]", span.raw_text)
               for span in resolver.resolve_many(resolver.span_ids)
               if span.source_field in {*action.source_fields, *context.source_fields})):
        return False
    action_text = final_reception_source_anchor_text(action.nucleus_id, nuclei, resolver)
    context_text = final_reception_source_anchor_text(context.nucleus_id, nuclei, resolver)
    if (not action_text or not context_text or not action_text.endswith("た")
        or action_text == context_text):
        return False
    before = body[previous_sentence.utf8_byte_start:previous_sentence.utf8_byte_end].decode("utf-8")
    current = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
    # Bound the affirmative present reception as well as the deictic object.
    # The original action's actor/time/negation are in the exact preceding
    # prefix; dropping or altering either source cannot discharge this duty.
    return bool(before.startswith(action_text + "ことを背景に、")
        and before.count(action_text) == before.count(context_text) == 1
        and current == "また、その行動を大切に思っています。")


def _body_inverse_attributive_support_attention(raw, relation, move, plan, resolver):
    """Read the actual support clause, not the author's candidate or replay.

    Both ordered endpoints are resolved from their own source evidence. The
    support remains progressive, while each source keeps its own time and
    subjectivity. A causal, reversed, quoted or truncated substitute is not
    this object's affirmative attention/reception.
    """
    index = {n.nucleus_id: n for n in plan.nuclei}
    if (relation.type != "action_supports_change"
        or move.reception_act != "honor_concrete_effort"
        or move.target_nucleus_ids != (relation.from_nucleus_id,)
        or move.support_nucleus_ids != (relation.to_nucleus_id,)
        or move.reference_mode == "anaphoric_first"):
        return False
    action, change = index[relation.from_nucleus_id], index[relation.to_nucleus_id]
    if (action.kind != "action" or change.kind != "change"
        or not _body_inverse_action_is_performed(action)
        or action.semantic_frame.modality != "fact"
        or change.semantic_frame.modality not in {"fact", "feeling"}
        or any(n.semantic_frame.actor != "current_user" or n.grounding_kind != "explicit"
               or len(n.source_span_ids) != 1 for n in (action, change))):
        return False
    fragments = []
    for nucleus in (action, change):
        source = str(resolver.resolve(nucleus.source_span_ids[0]).raw_text or "")
        typed = _body_inverse_typed_source_fragment(nucleus, source)
        if typed == "":
            return False
        fragment = (typed if typed is not None else source).strip(" \u3000、,。．.")
        if not fragment or re.search(r'[「」『』“”‘’"?？!！。;；…‥]', fragment):
            return False
        fragments.append(fragment)
    return re.fullmatch(
        re.escape(fragments[0] + "ことが支えている、" + fragments[1] + "という変化")
        + r"(?:を見過ごさず、|に目が留まり、それを)大切に思っています。", raw) is not None


def _body_inverse_preceding_change_context(
    body, previous_sentence, previous_clause, current_sentence,
    move, reception_plan, plan, resolver,
):
    """Prove a discourse antecedent from the preceding actual sentence.

    This parser does not call the author or accept an anchor elsewhere in
    the body. Both complete source objects, their direction and reception
    must occupy the adjacent, single-Move past action/change clause.
    """
    if (previous_sentence is None or previous_clause is None
        or len(previous_clause.move_ids) != 1
        or previous_sentence.utf8_byte_end != current_sentence.utf8_byte_start
        or move.move_role != "attention" or move.reception_act != "stay_with_current_burden"
        or len(move.target_nucleus_ids) != 1 or move.support_nucleus_ids):
        return False
    index = {n.nucleus_id: n for n in plan.nuclei}
    target = index[move.target_nucleus_ids[0]]
    contexts = _body_inverse_reception_context_ids(move, plan)
    prior = next((m for m in reception_plan.moves if m.move_id == previous_clause.move_ids[0]), None)
    if (target.semantic_frame.time_scope != "continuing" or len(contexts) != 1
        or prior is None or prior.move_role != "attention"
        or prior.reception_act != "honor_concrete_effort" or not prior.required
        or len(prior.target_nucleus_ids) != 1 or prior.support_nucleus_ids != contexts):
        return False
    action, change = index[prior.target_nucleus_ids[0]], index[contexts[0]]
    if (action.kind != "action" or change.kind != "change"
        or action.semantic_frame.time_scope != "past"
        or not _body_inverse_action_is_performed(action)
        or len(action.source_span_ids) != 1 or action.source_span_ids != change.source_span_ids
        or any(n.semantic_frame.actor != "current_user" or n.grounding_kind != "explicit"
               or n.source_fields not in {("memo",), ("memo_action",)}
               for n in (action, change, target))):
        return False
    supports = [r for r in plan.relations if r.type == "action_supports_change"
        and (r.from_nucleus_id, r.to_nucleus_id) == (action.nucleus_id, change.nucleus_id)]
    contrasts = [r for r in plan.relations if r.type == "contrast"
        and (r.from_nucleus_id, r.to_nucleus_id) == (change.nucleus_id, target.nucleus_id)]
    if len(supports) != 1 or len(contrasts) != 1:
        return False
    fragments = []
    for nucleus in (action, change):
        source = str(resolver.resolve(nucleus.source_span_ids[0]).raw_text or "")
        typed = _body_inverse_typed_source_fragment(nucleus, source)
        if typed == "":
            return False
        fragment = (typed if typed is not None else source).strip(" \u3000、,。．.")
        if not fragment or re.search(r'[「」『』“”‘’"?？!！。;；…‥]', fragment):
            return False
        fragments.append(fragment)
    expected = (fragments[0] + "ことが支えている、" + fragments[1]
        + "という変化を見過ごさず、大切に思っています。")
    actual = body[previous_sentence.utf8_byte_start:previous_sentence.utf8_byte_end].decode("utf-8")
    return (actual == expected
            or _read_action_change_discourse(actual, prior, plan, resolver, None) is not None)


def _body_inverse_finite_contrast_attention(
    raw, relation, move, plan, resolver, referent, *, preceding_change_proven=False,
):
    """Read the full ordered contrast and its reception without author replay."""
    if move.target_nucleus_ids != (relation.to_nucleus_id,):
        return False
    index = {n.nucleus_id: n for n in plan.nuclei}
    left, right = index[relation.from_nucleus_id], index[relation.to_nucleus_id]
    if len(left.source_span_ids) != 1 or right.semantic_frame.time_scope not in {"current_input", "continuing"}:
        return False
    aspect = tuple(c.split(":", 1)[1] for c in right.semantic_frame.attribute_codes if c.startswith("aspect:"))
    if any(a not in {"unknown", "not_applicable"} for a in aspect):
        return False
    source = str(resolver.resolve(left.source_span_ids[0]).raw_text or "")
    typed = _body_inverse_typed_source_fragment(left, source)
    if typed == "":
        return False
    source = (typed if typed is not None else source).strip(" \u3000、,。．.")
    if (not source or not referent or not referent.endswith("こと")
        or not re.search(r"(?:かった|[てで]いる|[てで]いた|た|ある|ない)$", source)
        or re.search(r"[「」『』“”‘’\"?？!！。;；…‥]", source)):
        return False
    target = referent[:-2]
    prefix = ""
    if right.semantic_frame.time_scope == "continuing":
        final = re.split(r"[、,]", target)[-1]
        ongoing = bool(re.search(r"(?:て|で)(?:い|お)(?:る|ます|た|ました)$", target))
        sustained = bool(final.startswith("ずっと")
            and not re.search(r"[「」『』“”‘’\"()（）\[\]【】?？!！。．.;；…‥]", target)
            and not re.search(r"(?:より|比べ|比較)", target)
            and not re.match(r"ずっと(?:前|後|先|昔|未来|以前|以後|遠|近|多|少|高|低)", final)
            and not re.search(r"(?:と|って)[^、,]*(?:聞|聴|言|話|語|述べ|書|記録|思|考|感じ|判断|伝|教)", final)
            and re.search(r"(?:ない|ある|いる|なる|する|[うくぐすつぬぶむるい])$", final))
        if "今" not in target and not ongoing and not sustained:
            prefix = "今も、"
    connector = ("その一方で、" if preceding_change_proven
                 and right.semantic_frame.time_scope == "continuing" else source + "一方で、")
    expected = connector + prefix + referent + "を見過ごさず、小さくせずに受け止めています。"
    return raw == expected


def _body_inverse_anchor_matches(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return left in right or right in left


def _body_inverse_quote_text(body: bytes, row: Any) -> str:
    return body[row.utf8_byte_start : row.utf8_byte_end].decode(
        "utf-8", errors="strict"
    )


def _body_inverse_visible_text(body: bytes, row: Any) -> str:
    return body[row.utf8_byte_start : row.utf8_byte_end].decode(
        "utf-8", errors="strict"
    )


def _body_inverse_reception_context_ids(
    move: Any,
    plan: GroundedObservationPlan,
) -> tuple[str, ...]:
    if move.support_nucleus_ids:
        return tuple(move.support_nucleus_ids)
    target_set = set(move.target_nucleus_ids)
    preference = {
        relation_type: index
        for index, relation_type in enumerate(
            _BODY_INVERSE_RECEPTION_RELATION_PREFERENCE.get(
                move.reception_act,
                (),
            )
        )
    }
    candidates: list[tuple[int, int, str]] = []
    relation_index = {row.relation_id: row for row in plan.relations}
    for order, relation_id in enumerate(
        plan.coverage_requirements.required_relation_ids
    ):
        relation = relation_index.get(relation_id)
        if relation is None:
            continue
        endpoints = (relation.from_nucleus_id, relation.to_nucleus_id)
        if not target_set.intersection(endpoints):
            continue
        other_ids = tuple(item for item in endpoints if item not in target_set)
        if len(other_ids) != 1:
            continue
        candidates.append(
            (
                preference.get(relation.type, len(preference) + 1),
                order,
                other_ids[0],
            )
        )
    if not candidates:
        return ()
    candidates.sort()
    return (candidates[0][2],)


def _body_inverse_thread_contrast_answers(body, witness, line, plan, resolver):
    """Resolve the sentence's explicit event antecedent before source matching.

    This grammar consumes visible bytes only; it does not replay the renderer.
    An ambiguous source identity or a cross-sentence antecedent cannot bind.
    """
    matched, failures = set(), []
    for sentence in witness.sentences:
        if sentence.section != "observation" or sentence.section_line_ordinal != line.section_ordinal:
            continue
        text = _body_inverse_visible_text(body, sentence)
        connective_text = re.sub(r"「[^「」]*」|『[^『』]*』", "", text)
        if "その出来事に対する" not in connective_text:
            continue
        parsed = re.fullmatch(
            r"「([^「」『』\n]+)」という出来事の一方で「([^「」『』\n]+)」という反応があり、"
            r"その出来事に対する(その時|回答した時点|先の回答時点)の受け止めとして、"
            r"「([^「」『』\n]+)」が見えます。", text)
        if parsed is None:
            failures.append("body_inverse_answer_antecedent_invalid")
            continue
        event_text, reaction_text, when, answer_text = parsed.groups()
        ids = []
        for value in (event_text, reaction_text, answer_text):
            normalized = _body_inverse_normalized_anchor(value)
            candidates = tuple(n.nucleus_id for n in plan.nuclei
                               if normalized in _body_inverse_nucleus_source_values(n.nucleus_id, plan, resolver))
            if len(candidates) != 1:
                break
            ids.append(candidates[0])
        if len(ids) != 3 or len(set(ids)) != 3:
            failures.append("body_inverse_answer_antecedent_ambiguous")
            continue
        index = {n.nucleus_id: n for n in plan.nuclei}
        event, reaction, answer = (index[i] for i in ids)
        contrasts = tuple(r for r in plan.relations if r.type == "contrast"
                          and r.from_nucleus_id == event.nucleus_id)
        about = tuple(r for r in plan.relations if r.type == "evaluation_about_event"
                      and r.from_nucleus_id == event.nucleus_id)
        expected_time = {"その時": "original_occasion", "回答した時点": "answer_time",
                         "先の回答時点": "prior_answer_time"}[when]
        times = {c.split(":", 1)[1] for c in answer.semantic_frame.attribute_codes
                 if c.startswith("thread_time:")}
        if (event.kind == "event" and reaction.kind == "reaction"
                and event.source_fields in {("memo",), ("memo_action",)}
                and reaction.source_fields in {("memo",), ("memo_action",)}
                and answer.source_fields == ("answer_text_private",)
                and times == {expected_time}
                and len(contrasts) == len(about) == 1
                and contrasts[0].to_nucleus_id == reaction.nucleus_id
                and about[0].to_nucleus_id == answer.nucleus_id):
            matched.add(about[0].relation_id)
        else:
            failures.append("body_inverse_answer_antecedent_source_mismatch")
    return frozenset(matched), tuple(failures)



def _read_appraisal_material_discourse(raw, move, plan, resolver, selected_subjective_input=None):
    """Independently read two complete, ordered, non-cancelling source duties.

    No author replay or expected prose is used. A unique original source is
    reconstructed from the actual clause and checked against the source-owned
    appraisal/material inventory. In particular a factual correction, an
    invented goal or an affirmative cancellation cannot discharge either duty.
    """
    from emlis_ai_grounded_observation_plan import _independent_nonaction_pair, _source_self_appraisal
    pair = _independent_nonaction_pair(plan.nuclei, plan.relations,
        safety_kind="safe_observation", material_quality="grounded")
    if (len(pair) != 2 or not _source_self_appraisal(pair[0])
        or move.reception_act != "stay_with_current_burden" or not move.required
        or len(move.target_nucleus_ids) != 1 or move.support_nucleus_ids
        or not raw.endswith("。") or raw.count("。") != 1
        or re.search(r'[「」『』“”‘’"?？!！\r\n]', raw)):
        return None
    active = tuple(m for m in plan.response_plan.human_reception_plan.moves if m.required)
    if (len(active) != 2
        or tuple(m.target_nucleus_ids for m in active) != tuple((n.nucleus_id,) for n in pair)
        or tuple(m.move_role for m in active) != ("attention", "felt_response")):
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions if d.move_id == move.move_id), None)
        appraisal = decision.subjective_proposition.appraisal_content if decision else None
        if appraisal is None or appraisal.operation != "RECEIVE_AS_MATERIAL":
            return None
    index = {n.nucleus_id: n for n in plan.nuclei}
    expected = final_reception_source_anchor_text(move.target_nucleus_ids[0], index, resolver)
    if move.target_nucleus_ids == (pair[0].nucleus_id,) and move.move_role == "attention":
        parsed = re.fullmatch(r"(?P<source>.+)、という言葉(?:が気になりました|に目が留まりました)。", raw)
    elif move.target_nucleus_ids == (pair[1].nucleus_id,) and move.move_role == "felt_response":
        parsed = re.fullmatch(r"(?P<source>.+)、という記録を理由に、先ほどの言葉を"
                              r"(?:打ち消す|否定する)ことはしません。", raw)
    else:
        return None
    if parsed is None or not expected or parsed["source"] != expected:
        return None
    # Preserve source bytes for the existing sensation/qualifier inverse.
    end = len(parsed["source"].encode("utf-8"))
    return ((0, end, expected.encode("utf-8")),)


def _read_relational_focus_discourse(raw, move, plan, resolver, selected_subjective_input):
    """Independently read the asserted focus, then restore only its source spans.

    The plan proves which two source roles may be related; full body parsing
    proves their words, direction, epistemic scope and non-certain stance. No
    author call, author output, fixture text or body binding grants admission.
    """
    from emlis_ai_grounded_observation_plan import source_owned_relational_focus
    focus = source_owned_relational_focus(move, plan)
    if focus is None:
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions
                         if d.move_id == move.move_id), None)
        proposition = decision.subjective_proposition if decision else None
        appraisal = proposition.appraisal_content if proposition else None
        position = proposition.relational_position if proposition else None
        if not (appraisal is not None and appraisal.operation in {
                    "RECEIVE_AS_MATERIAL", "PRESERVE_BOTH_ENDPOINTS"}
                or position is not None and position.stance_operator == "STAY_WITH_SPECIFIC_OBJECT"):
            return None
    kind, left, right = focus
    index = {n.nucleus_id: n for n in plan.nuclei}
    first, second = (final_reception_source_anchor_text(n.nucleus_id, index, resolver)
                     for n in (left, right))
    if (not first or not second or first == second
        or any(mark in first + second for mark in ("。", "？", "?", "「", "」", "\n"))):
        return None
    if kind == "received_experience_focus":
        from emlis_ai_grounded_observation_plan import (
            _source_nominal_past_feeling_parts, _LEADING_CONTRAST_RE,
        )
        source = _source_nominal_past_feeling_parts(second)
        if source is None or source[1] not in {"に", "が"}:
            return None
        experience, particle, degree, feeling = source
        lead = _LEADING_CONTRAST_RE.match(experience)
        prefix = lead.group() if lead else ""
        # Keep a source comma/space with its leading connective. Moving
        # only the word would create a second comma after the focus marker.
        if prefix:
            end = len(prefix)
            while end < len(experience) and experience[end] in "、, ":
                end += 1
            prefix, experience = experience[:end], experience[end:]
        if (re.search(r"(?:私|わたし|自分|僕|ぼく|俺|おれ)(?:は|が)", first + second)
            or "とは思わない" in experience):
            return None
        parsed = re.fullmatch(
            r"(?P<background>.+)けれど、(?P<response>.+)のは、"
            r"(?P<experience>.+)こと(?:なのですね|なのです|なのだと受け取りました)。", raw)
        if (parsed is None or parsed['background'] != first
            or parsed['response'] != prefix + degree + feeling
            or parsed['experience'] != experience
            or prefix + parsed['experience'] + 'こと' + particle + degree + feeling != second):
            return None
        # Restore the complete transposed source only after reading all its
        # roles. These spans serve the existing inverse, never the author.
        return ((0, len(first.encode()), first.encode()),
                (len(raw[:parsed.start('response')].encode()),
                 len(raw[:parsed.end('experience')].encode()), second.encode()))
    if kind == "answer_owned_standard":
        stance_reading = re.fullmatch(
            r"(?P<appraisal>.+)という振り返りを、(?P<wish>.+)という望みを起点に、"
            r"一緒に見ていきたいです。", raw)
        material_reading = re.fullmatch(
            r"(?P<appraisal>.+)という振り返りは、(?P<wish>.+)という望みに"
            r"照らしたものとして(?:読めます|受け取れます)。", raw)
        if selected_subjective_input is not None:
            parsed = stance_reading if position is not None else material_reading
        else:
            parsed = stance_reading or material_reading
        if (parsed is None or parsed["appraisal"] != first or parsed["wish"] != second):
            return None
        spans = (('appraisal', first), ('wish', second))
        return tuple((len(raw[:parsed.start(key)].encode()), len(raw[:parsed.end(key)].encode()),
                      value.encode()) for key, value in spans)
    source = re.fullmatch(r"(?P<matter>.+(?:か|のか))(?P<topic>は|が)?"
                          r"(?P<state>(?:まだ|今は|もう)?(?:分からない|わからない|分からなくなった|"
                          r"わからなくなった|決められない|迷っている))", second)
    parsed = re.fullmatch(r"(?P<affirmed>.+)一方で、(?P<unknown>.+)のは、"
                          r"(?P<matter>.+)という点(?:なのですね|なのだと読めます)。", raw)
    if (source is None or parsed is None or parsed['affirmed'] != first
        or parsed['unknown'] != source['state'] or parsed['matter'] != source['matter']):
        return None
    # The topicalization is one contiguous source-owned span. Restoring it for
    # the existing inverse does not change the emitted body or original data.
    return ((0, len(first.encode()), first.encode()),
            (len(raw[:parsed.start('unknown')].encode()),
             len(raw[:parsed.end('matter')].encode()), second.encode()))


def _read_action_purpose_discourse(raw, move, plan, resolver, selected_subjective_input):
    """Read the purpose and performed action independently from actual prose.

    Source grammar supplies the two permitted roles, never the answer text.
    Restoring that one source span serves the existing evidence inverse only;
    it cannot promote the purpose to an achieved result or a cause.
    """
    from emlis_ai_grounded_observation_plan import source_owned_action_purpose
    from emlis_ai_grounded_human_reception import source_grounded_reception_move_relations
    if (move.reception_act != "honor_concrete_effort" or not move.required
        or len(move.target_nucleus_ids) != 1 or move.support_nucleus_ids
        or source_grounded_reception_move_relations(move, plan)):
        return None
    nucleus = next((n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0]), None)
    parts = source_owned_action_purpose(nucleus, resolver) if nucleus is not None else None
    if parts is None:
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions if d.move_id == move.move_id), None)
        proposition = decision.subjective_proposition if decision else None
        appraisal = proposition.appraisal_content if proposition else None
        if appraisal is None or appraisal.operation != "RECEIVE_AS_MATERIAL":
            return None
    purpose, connector, action = parts
    parsed = re.fullmatch(r"(?P<action>.+)のは、(?P<purpose>.+)ため(?:なのですね|なのです|なのだと受け取りました)。", raw)
    if parsed is None or parsed['action'] != action or parsed['purpose'] != purpose:
        return None
    # The inversion occupies one contiguous body range. Reconstruct the
    # exact source order, including its connective, for downstream scope checks.
    return ((0, len(raw[:parsed.end('purpose')].encode()),
             (purpose + connector + action).encode()),)


def _read_action_change_discourse(raw, move, plan, resolver, selected_subjective_input):
    """Verify the past episode from body bytes without rerunning its author."""
    from emlis_ai_grounded_observation_plan import source_owned_action_change
    parts = source_owned_action_change(move, plan, resolver)
    if parts is None:
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions if d.move_id == move.move_id), None)
        proposition = decision.subjective_proposition if decision else None
        appraisal = proposition.appraisal_content if proposition else None
        if (appraisal is None or appraisal.dimension != "MATERIAL_WEIGHT"
            or appraisal.operation != "RECEIVE_AS_MATERIAL"):
            return None
    left, connector, right = parts
    parsed = re.fullmatch(r"(?P<episode>.+)(?:のですね|のです|のだと受け取りました)。", raw)
    if parsed is None or parsed['episode'] != left + connector + right:
        return None
    start = len((left + connector).encode())
    return ((0, len(left.encode()), left.encode()),
            (start, start + len(right.encode()), right.encode()))


def _answer_feeling_preceding_event(move, plan, resolver, selected_subjective_input,
                                    preceding_context):
    """Resolve a shared event only from its immediately preceding full reading.

    Both selected duties and their order stay intact. An omitted event cannot
    bind through another Move, another event, a partial body or an old answer.
    """
    from emlis_ai_grounded_observation_plan import source_owned_answer_feeling
    roles = source_owned_answer_feeling(move, plan)
    if roles is None or preceding_context is None:
        return False
    previous_move, previous_text = preceding_context
    moves = plan.response_plan.human_reception_plan.moves
    position = next((i for i, candidate in enumerate(moves) if candidate == move), -1)
    event, answer, when = roles
    if (when not in {"answer_time", "prior_answer_time"}
        or position <= 0 or moves[position - 1] != previous_move
        or previous_move.target_nucleus_ids != (event.nucleus_id,)
        or len(previous_move.support_nucleus_ids) != 1
        or not previous_move.required or previous_move.move_role != "felt_response"
        or previous_move.reception_act != "stay_with_current_burden"):
        return False
    index = {n.nucleus_id: n for n in plan.nuclei}
    original = index.get(previous_move.support_nucleus_ids[0])
    if (original is None or original.source_fields != event.source_fields
        or original.source_span_ids != event.source_span_ids
        or original.allowed_claim_scope != "explicit_current_input"
        or original.semantic_frame.actor != "current_user"
        or original.semantic_frame.time_scope != "past"):
        return False
    return read_received_discourse(previous_text, previous_move, plan, resolver,
                                   selected_subjective_input) is not None


def _read_answer_feeling_discourse(raw, move, plan, resolver, selected_subjective_input,
                                   preceding_context=None):
    """Read event ownership, source time and the full answer from body bytes.

    No author replay or expected sentence grants admission. The feeling is
    still the person's explicit answer, not Emlis's state or an inferred change.
    """
    from emlis_ai_grounded_observation_plan import source_owned_answer_feeling
    roles = source_owned_answer_feeling(move, plan)
    if getattr(resolver, "source_contract", None) != "cocolon.cmee.emlis_thread.v1":
        return None
    if roles is None:
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions if d.move_id == move.move_id), None)
        appraisal = decision.subjective_proposition.appraisal_content if decision else None
        if (appraisal is None or appraisal.dimension != "MATERIAL_WEIGHT"
            or appraisal.operation != "RECEIVE_AS_MATERIAL"):
            return None
    event, answer, when = roles
    index = {n.nucleus_id: n for n in plan.nuclei}
    event_text, source = (final_reception_source_anchor_text(n.nucleus_id, index, resolver)
                          for n in (event, answer))
    if (not event_text or not source
        or not _SOURCE_GROUNDED_FINITE_END_RE.search(source)
        or re.search(r"(?:です|ます|でした|ました|だ)$", source)
        or re.search(r"(?:私|わたし|自分|僕|ぼく|俺|おれ)(?:は|も|が)", event_text + source)
        or re.search(r'[「」『』“”‘’"?？!！\r\n。]', event_text + source)):
        return None
    shared_event = _answer_feeling_preceding_event(
        move, plan, resolver, selected_subjective_input, preceding_context)
    parsed = re.fullmatch(r"(?:(?P<event>.+)ことについて、)?"
        r"(?P<time>その時は|回答した時点では|先の回答時点では)"
        r"(?P<feeling>.+)(?:のですね|のです|のだと受け取りました)。", raw)
    expected_time = {"original_occasion": "その時は", "answer_time": "回答した時点では",
                     "prior_answer_time": "先の回答時点では"}[when]
    if (parsed is None or (parsed['event'] != event_text
            and not (parsed['event'] is None and shared_event)) or parsed['time'] != expected_time
        or parsed['feeling'] != source):
        return None
    return tuple((len(raw[:parsed.start(key)].encode()), len(raw[:parsed.end(key)].encode()), value.encode())
                 for key, value in (("event", event_text), ("feeling", source))
                 if parsed[key] is not None)


def _read_independent_decision_discourse(raw, move, plan, resolver, selected_subjective_input):
    """Read both unresolved hosts and their explicit separation from prose.

    Source grammar proves roles; this reader checks actual bytes rather than
    asking the author for its output. Selection and focus remain unchanged.
    """
    from emlis_ai_grounded_observation_plan import (
        _source_independent_decision_group, _source_independent_decision_clause_parts,
        _source_material_allows_reverse,
    )
    group = _source_independent_decision_group(plan.nuclei, plan.relations)
    if (not group or not move.required or move.move_role != "felt_response"
        or move.reception_act != "stay_with_current_burden"
        or re.search(r'[「」『』“”‘’"?？!！\r\n]', raw)):
        return None
    selected = (move.target_nucleus_ids, move.support_nucleus_ids)
    forward = ((group[0].nucleus_id,), (group[1].nucleus_id,))
    reverse = ((group[1].nucleus_id,), (group[0].nucleus_id,))
    if selected == reverse and _source_material_allows_reverse(group):
        group = (group[1], group[0], *group[2:])
    elif selected != forward:
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions
                         if d.move_id == move.move_id), None)
        appraisal = decision.subjective_proposition.appraisal_content if decision else None
        if (appraisal is None or appraisal.dimension != "MATERIAL_WEIGHT"
            or appraisal.operation != "RECEIVE_AS_MATERIAL"):
            return None
    sources = tuple(str(resolver.resolve(n.source_span_ids[0]).raw_text).strip(" 　。．.")
                    for n in group[:2] if len(n.source_span_ids) == 1)
    if len(sources) != 2:
        return None
    for nucleus, source in zip(group, sources):
        proof = _source_independent_decision_clause_parts(source)
        if (proof is None or "lexical:source_independent_decision_" + proof[0]
            not in nucleus.semantic_frame.attribute_codes):
            return None
    parsed = re.fullmatch(r"(?P<left>[^。！？!?]+)こととは別に、(?P<right>[^。！？!?]+)"
                          r"(?:のですね|のです|のだと受け取りました)。", raw)
    if parsed is None:
        return None
    expected = tuple(re.sub(r"^それとは別に[、,]?", "",
                            re.sub(r"決められません$", "決められない",
                                   re.sub(r"迷っています$", "迷っている", source)))
                     for source in sources)
    if (parsed['left'], parsed['right']) != expected:
        return None
    return tuple((len(raw[:parsed.start(key)].encode()), len(raw[:parsed.end(key)].encode()),
                  source.encode()) for key, source in zip(('left', 'right'), sources))


def _read_feeling_reason_discourse(raw, move, plan, resolver, selected_subjective_input):
    """Restore a present experience and its open reason from actual prose.

    The source projection owns their association. The inverse independently
    restores the finite predicate and its SELF topic, never replaying author
    output or accepting a feeling substring inside a different proposition.
    """
    from emlis_ai_grounded_observation_plan import _source_feeling_reason_group
    group = _source_feeling_reason_group(plan.nuclei, plan.relations)
    if (not group or not move.required or move.move_role != "felt_response"
        or move.reception_act != "stay_with_current_burden"
        or (move.target_nucleus_ids, move.support_nucleus_ids)
            != ((group[0].nucleus_id,), (group[1].nucleus_id,))
        or re.search(r'[「」『』“”‘’"?？!！\r\n]', raw)):
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions
                         if d.move_id == move.move_id), None)
        appraisal = decision.subjective_proposition.appraisal_content if decision else None
        if (appraisal is None or appraisal.dimension != "MATERIAL_WEIGHT"
            or appraisal.operation != "RECEIVE_AS_MATERIAL"):
            return None
    sources = tuple(str(resolver.resolve(n.source_span_ids[0]).raw_text).strip(" 　。．.")
                    for n in group[:2] if len(n.source_span_ids) == 1)
    if len(sources) != 2:
        return None
    parsed = re.fullmatch(r"(?P<experience>[^。！？!?]+)、(?P<unknown>"
        r"(?:(?:なぜ|どうして|何故)そう感じるのか|その理由)(?:は|が)?"
        r"(?:まだ)?(?:よく|はっきり)?(?:分からない|わからない))"
        r"(?:のですね|のです|のだと受け取りました)。", raw)
    if parsed is None or parsed['unknown'] != sources[1]:
        return None
    visible = parsed['experience']
    if visible.endswith("感じがして"):
        restored = visible[:-2] + "する"
    elif visible.endswith("感じて"):
        restored = visible[:-1] + "る"
    elif visible.endswith("くて") and sources[0].endswith("い"):
        restored = visible[:-2] + "い"
    else:
        return None
    topic = re.match(r"(?P<owner>わたし|ぼく|おれ|私|僕|俺)は", sources[0])
    if topic:
        if not restored.startswith("あなたは"):
            return None
        restored = topic['owner'] + "は" + restored[len("あなたは"):]
    if restored != sources[0]:
        return None
    return tuple((len(raw[:parsed.start(key)].encode()), len(raw[:parsed.end(key)].encode()),
                  source.encode()) for key, source in zip(('experience', 'unknown'), sources))


def read_source_owned_discourse(raw, move, plan, resolver, selected_subjective_input=None,
                                *, preceding_context=None):
    """Read supported finite source duties without a literal-author oracle."""
    feeling_reason = _read_feeling_reason_discourse(
        raw, move, plan, resolver, selected_subjective_input)
    if feeling_reason is not None:
        return feeling_reason
    independent_decision = _read_independent_decision_discourse(
        raw, move, plan, resolver, selected_subjective_input)
    if independent_decision is not None:
        return independent_decision
    answer = _read_answer_feeling_discourse(raw, move, plan, resolver, selected_subjective_input,
                                           preceding_context)
    if answer is not None:
        return answer
    action_change = _read_action_change_discourse(raw, move, plan, resolver, selected_subjective_input)
    if action_change is not None:
        return action_change
    purpose = _read_action_purpose_discourse(raw, move, plan, resolver, selected_subjective_input)
    if purpose is not None:
        return purpose
    focus = _read_relational_focus_discourse(raw, move, plan, resolver, selected_subjective_input)
    if focus is not None:
        return focus
    appraisal = _read_appraisal_material_discourse(raw, move, plan, resolver, selected_subjective_input)
    return appraisal if appraisal is not None else read_received_discourse(
        raw, move, plan, resolver, selected_subjective_input)


def read_received_discourse(raw, move, plan, resolver, selected_subjective_input=None):
    """Parse either finite or coordinated clauses with a shared past scope.

    Source-owned event boundaries must be unique. Only the actual connective
    inflection is normalized for the independent role reader; the source,
    body, witness and response bindings are never rewritten.
    """
    if len(move.target_nucleus_ids) <= 1 or "、また、" in raw:
        return _read_received_discourse_parts(raw, move, plan, resolver, selected_subjective_input)
    index = {n.nucleus_id: n for n in plan.nuclei}
    cuts = [0]
    for nid in move.target_nucleus_ids[1:]:
        event = final_reception_source_anchor_text(nid, index, resolver)
        starts = [m.start() for m in re.finditer(re.escape("、" + event), raw)] if event else []
        if len(starts) != 1 or starts[0] <= cuts[-1]:
            return None
        cuts.append(starts[0] + 1)
    actual_parts = [raw[start:end - 1] for start, end in zip(cuts, cuts[1:])]
    actual_parts.append(raw[cuts[-1]:])
    normalized_parts = []
    for part in actual_parts[:-1]:
        if part.endswith("つながらず"):
            finite = part[:-5] + "つながらなかった"
        elif part.endswith("感じ"):
            finite = part + "た"
        elif part.endswith("届き"):
            finite = part[:-2] + "届いた"
        elif part.endswith("と思い"):
            finite = part[:-1] + "った"
        elif part.endswith("く"):
            finite = part[:-1] + "かった"
        else:
            return None
        normalized_parts.append(finite + "のですね")
    normalized_parts.append(actual_parts[-1])
    normalized = "、また、".join(normalized_parts)
    proof = _read_received_discourse_parts(normalized, move, plan, resolver, selected_subjective_input)
    if proof is None:
        return None
    intervals, base = [], 0
    for original, adapted, start in zip(actual_parts, normalized_parts, cuts):
        intervals.append((base, base + len(adapted.encode()), len(raw[:start].encode()), len(original.encode())))
        base += len(adapted.encode()) + len("、また、".encode())
    restored = []
    for start, end, source in proof:
        containing = [r for r in intervals if r[0] <= start < end <= r[1]]
        if len(containing) != 1:
            return None
        lo, hi, actual_start, actual_size = containing[0]
        restored.append((actual_start + start - lo,
                         actual_start + min(end - lo, actual_size), source))
    return tuple(restored)


def _read_received_discourse_parts(raw, move, plan, resolver, selected_subjective_input=None):
    """Read finite event/feeling/answer roles from actual text, without replay.

    The response grammar may vary its acknowledgement; acceptance depends on
    the reconstructed propositions, relation ownership, polarity and time.
    No source clause may disappear merely because it is present in Layer 1.
    Returned ranges restore grammatical feeling nouns for sensation checks;
    they are not a replacement body or evidence supplied by the author.
    """
    from emlis_ai_grounded_observation_plan import (
        _thread_retained_reaction_groups, _received_contrast_group_targets,
    )
    original_group = _received_contrast_group_targets(plan.nuclei, plan.relations)
    original = bool(original_group and original_group ==
                    (move.target_nucleus_ids, move.support_nucleus_ids))
    thread_group = (("current_burden", move.target_nucleus_ids, move.support_nucleus_ids)
                    in _thread_retained_reaction_groups(plan.nuclei, plan.relations))
    has_answers = any(n.source_fields == ("answer_text_private",) for n in plan.nuclei)
    if (has_answers and getattr(resolver, "source_contract", None) != "cocolon.cmee.emlis_thread.v1"
        or not move.required or move.move_role != "felt_response"
        or move.reception_act != "stay_with_current_burden"
        or not (original or thread_group)
        or not raw.endswith("。") or raw.count("。") != 1
        or re.search(r'[「」『』“”‘’"?？!！\r\n]', raw)):
        return None
    if selected_subjective_input is not None:
        decision = next((d for d in selected_subjective_input.decisions
                         if d.move_id == move.move_id), None)
        appraisal = decision.subjective_proposition.appraisal_content if decision else None
        if appraisal is None or appraisal.operation not in {"RECEIVE_AS_MATERIAL", "PRESERVE_BOTH_ENDPOINTS"}:
            return None
    parts = raw[:-1].split("、また、")
    if len(parts) != len(move.target_nucleus_ids):
        return None
    nuclei = {n.nucleus_id: n for n in plan.nuclei}
    required = set(plan.coverage_requirements.required_relation_ids)
    consumed, consumed_relations, replacements = set(), set(), []
    offset, saw_answer = 0, False
    for event_id, part in zip(move.target_nucleus_ids, parts):
        event = nuclei[event_id]
        contrasts = tuple(r for r in plan.relations if r.relation_id in required
            and r.type == "contrast" and r.from_nucleus_id == event_id
            and r.to_nucleus_id in move.support_nucleus_ids)
        about = tuple(r for r in plan.relations if r.relation_id in required
            and r.type == "evaluation_about_event" and r.from_nucleus_id == event_id
            and r.to_nucleus_id in move.support_nucleus_ids)
        if (len(contrasts) > 1 or len(about) > 1 or not (contrasts or about)
            or event.semantic_frame.actor != "current_user"
            or event.semantic_frame.time_scope != "past"
            or event.source_fields not in {("memo",), ("memo_action",)}):
            return None
        event_source = final_reception_source_anchor_text(event_id, nuclei, resolver)
        feeling_source = link = None
        if contrasts:
            relation = contrasts[0]
            feeling = nuclei[relation.to_nucleus_id]
            feeling_source = final_reception_source_anchor_text(feeling.nucleus_id, nuclei, resolver)
            if (feeling.source_span_ids != event.source_span_ids or len(event.source_span_ids) != 1
                or feeling.source_fields != event.source_fields
                or feeling.semantic_frame.time_scope != "past"
                or feeling.semantic_frame.actor != "current_user"):
                return None
            source = re.sub(r"\s+", " ", resolver.resolve(event.source_span_ids[0]).raw_text).strip(" 　、,。．.")
            if not (source.startswith(event_source) and source.endswith(feeling_source)):
                return None
            link = source[len(event_source):-len(feeling_source)].rstrip("、,")
            if link not in {"のに", "けど", "けれど", "けれども"}:
                return None
            consumed.add(feeling.nucleus_id)
            consumed_relations.add(relation.relation_id)
        ending = re.search(r"(?:のですね|のです|のだと受け取りました)$", part)
        if ending is None:
            return None
        clause = part[:ending.start()]
        consumed.add(event_id)
        if not about:
            # Reconstruct the complete source feeling from the actual finite
            # reading. Absence is not inability, continuing pain or a cause.
            absent = re.fullmatch(r"(?P<event>.+?)ことは、(?P<feeling>[^、,]+)さにはつながらなかった", clause)
            present = re.fullmatch(r"(?P<event>.+?)(?P<link>けれども|けれど|けど|のに)、(?P<feeling>[^、,]+)さを感じた", clause)
            parsed = absent or present
            if parsed is not None:
                restored = parsed["feeling"] + ("くなかった" if absent else "かった")
                if (parsed["event"] != event_source or restored != feeling_source
                    or present is not None and present["link"] != link):
                    return None
                start = len((raw[:offset] + clause[:parsed.start("feeling")]).encode("utf-8"))
                end = len((raw[:offset] + clause[:parsed.end("feeling")] + "さ").encode("utf-8"))
                replacements.append((start, end, feeling_source.encode("utf-8")))
            else:
                # The earlier grammatical reading remains independently
                # interpretable, but not a reason to require it verbatim.
                candidates = {(clause[:m.start()], m.group(), clause[m.end():])
                              for m in re.finditer(r"けれども|けれど|けど|のに", clause)}
                if (event_source, link, feeling_source) not in candidates:
                    return None
        else:
            relation = about[0]
            answer = nuclei[relation.to_nucleus_id]
            times = {c.split(":", 1)[1] for c in answer.semantic_frame.attribute_codes
                     if c.startswith("thread_time:")}
            if (len(times) != 1 or not times <= {"original_occasion", "answer_time", "prior_answer_time"}
                or answer.source_fields != ("answer_text_private",)
                or answer.allowed_claim_scope != "explicit_supplemental_answer"
                or answer.semantic_frame.actor != "current_user"
                or answer.semantic_frame.polarity != "negative"):
                return None
            answer_source = final_reception_source_anchor_text(answer.nucleus_id, nuclei, resolver)
            if times != {"original_occasion"}:
                # Read source/time roles from the delivered clause, without
                # asking the author for its expected surface. An answer-time
                # statement cannot replace the original past reaction.
                temporal = re.fullmatch(
                    r"(?P<event>.+?)(?:時は(?:(?P<absent>[^、,]+)くなく、|(?P<felt>[^、,]+)く、)|ことについて、)"
                    r"(?P<time>回答した時点では|先の回答時点では)(?P<answer>.+)", clause)
                if temporal is None or len(move.target_nucleus_ids) != 1:
                    return None
                actual_feeling = (temporal["absent"] + "くなかった" if temporal["absent"] is not None
                                  else temporal["felt"] + "かった" if temporal["felt"] is not None else None)
                actual_time = {"回答した時点では": "answer_time",
                               "先の回答時点では": "prior_answer_time"}[temporal["time"]]
                if ((temporal["event"], actual_feeling, temporal["answer"])
                    != (event_source, feeling_source, answer_source)
                    or times != {actual_time}):
                    return None
                consumed.add(answer.nucleus_id)
                consumed_relations.add(relation.relation_id)
                offset += len(part) + len("、また、")
                continue
            # The body, not an author-produced nominal, owns these spans.
            perceived = re.fullmatch(
                r"(?P<event>.+?)ことは(?:(?P<feeling>[^、,]+)さにはつながらず、|、(?P<positive>[^、,]+)さを伴い、|、)"
                r"(?P<perception>.+)ような(?P<burden>[^、,]+)さとして届いた", clause)
            finite = re.fullmatch(
                r"(?P<event>.+?)時は(?:(?P<feeling>[^、,]+)くなく、|(?P<positive>[^、,]+)く、|、)(?P<answer>.+)", clause)
            if perceived is not None:
                actual_event = perceived["event"]
                actual_feeling = (perceived["feeling"] + "くなかった"
                                  if perceived["feeling"] is not None else
                                  perceived["positive"] + "かった" if perceived["positive"] is not None else None)
                restored = {perceived["perception"] + "ようで" + comma
                            + perceived["burden"] + "かった" for comma in ("、", ",")}
                if answer_source not in restored:
                    return None
                begin = len((raw[:offset] + clause[:perceived.start("perception")]).encode("utf-8"))
                finish = len((raw[:offset] + clause[:perceived.end()]).encode("utf-8"))
                replacements.append((begin, finish, answer_source.encode("utf-8")))
            elif finite is not None:
                actual_event = finite["event"]
                actual_feeling = (finite["feeling"] + "くなかった"
                                  if finite["feeling"] is not None else
                                  finite["positive"] + "かった" if finite["positive"] is not None else None)
                if finite["answer"] != answer_source:
                    return None
            else:
                return None
            if (actual_event, actual_feeling) != (event_source, feeling_source):
                return None
            consumed.add(answer.nucleus_id)
            consumed_relations.add(relation.relation_id)
        offset += len(part) + len("、また、")
    expected_relations = {r.relation_id for r in plan.relations if r.relation_id in required
        and r.from_nucleus_id in move.target_nucleus_ids
        and r.to_nucleus_id in move.support_nucleus_ids}
    if (consumed != set((*move.target_nucleus_ids, *move.support_nucleus_ids))
        or consumed_relations != expected_relations):
        return None
    return tuple(replacements)


def _received_discourse_equivalent(actual, canonical, reception_plan, clauses, plan,
                                   resolver, selected_subjective_input):
    """Do not make a grammatical acknowledgement spelling a semantic oracle.

    Unchanged clauses retain the existing contract. A changed finite reading
    must independently express the complete same source-owned duties on both
    sides, so this does not authorize arbitrary rewrites, omissions or labels.
    """
    if actual == canonical:
        return True
    actual_parts = actual.split("。")
    canonical_parts = canonical.split("。")
    if (actual_parts[-1] or canonical_parts[-1]
        or len(actual_parts) != len(canonical_parts)
        or len(actual_parts) != len(clauses) + 1):
        return False
    moves = {m.move_id: m for m in reception_plan.moves}
    for number, (left, right, clause) in enumerate(zip(actual_parts[:-1], canonical_parts[:-1], clauses)):
        if left == right:
            continue
        if len(clause.move_ids) != 1:
            return False
        move = moves.get(clause.move_ids[0])
        previous = (moves.get(clauses[number - 1].move_ids[0])
                    if number and len(clauses[number - 1].move_ids) == 1 else None)
        if move is None or any(read_source_owned_discourse(text + "。", move, plan, resolver,
            selected_subjective_input, preceding_context=(previous, parts[number - 1] + "。")
            if previous is not None else None) is None
            for text, parts in ((left, actual_parts), (right, canonical_parts))):
            return False
    return True


def _body_inverse_thread_received_group(body, witness, sentence, move, plan, resolver):
    """Read original clauses and immediately bound answer anaphora from bytes.

    Source contrasts and ABOUT edges are checked separately; no forward group
    nominal, expression, or grammatical marker payload is the answer oracle.
    """
    finite = read_source_owned_discourse(
        body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8"),
        move, plan, resolver,
    ) if sentence.section == "reception" else None
    if finite is not None:
        return tuple((start + sentence.utf8_byte_start, end + sentence.utf8_byte_start, source)
                     for start, end, source in finite)
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
    if (sentence.section != "reception"
        or ("current_burden", move.target_nucleus_ids, move.support_nucleus_ids)
           not in _thread_retained_reaction_groups(plan.nuclei, plan.relations)):
        return None
    index = {n.nucleus_id: n for n in plan.nuclei}
    expected = []
    for event_id in move.target_nucleus_ids:
        event = index[event_id]
        contrast = tuple(r for r in plan.relations if r.type == "contrast"
            and r.from_nucleus_id == event_id and r.to_nucleus_id in move.support_nucleus_ids
            and r.relation_id in plan.coverage_requirements.required_relation_ids)
        about = tuple(r for r in plan.relations if r.type == "evaluation_about_event"
            and r.from_nucleus_id == event_id and r.to_nucleus_id in move.support_nucleus_ids
            and r.relation_id in plan.coverage_requirements.required_relation_ids)
        if len(contrast) > 1 or len(about) > 1 or not (contrast or about):
            return None
        if contrast:
            feeling = index[contrast[0].to_nucleus_id]
            left, right = (final_reception_source_anchor_text(n.nucleus_id, index, resolver) for n in (event, feeling))
            if (event.source_span_ids != feeling.source_span_ids or len(event.source_span_ids) != 1
                or event.source_fields != feeling.source_fields or event.source_fields not in {("memo",), ("memo_action",)}
                or event.semantic_frame.time_scope != feeling.semantic_frame.time_scope
                or event.semantic_frame.time_scope != "past"):
                return None
            source = re.sub(r"\s+", " ", resolver.resolve(event.source_span_ids[0]).raw_text).strip(" 　、,。．.")
            if not source.startswith(left) or not source.endswith(right):
                return None
            connector = source[len(left):-len(right)].rstrip("、,")
            if connector not in {"のに", "けど", "けれど", "けれども"}:
                return None
            expected.append(("original", event_id, left, connector, right))
        if about:
            answer = index[about[0].to_nucleus_id]
            times = {c.split(":", 1)[1] for c in answer.semantic_frame.attribute_codes if c.startswith("thread_time:")}
            if (len(times) != 1 or answer.source_fields != ("answer_text_private",)
                or answer.allowed_claim_scope != "explicit_supplemental_answer"
                or answer.semantic_frame.polarity != "negative"):
                return None
            expected.append(("answer" if contrast else "direct", event_id,
                final_reception_source_anchor_text(answer.nucleus_id, index, resolver), next(iter(times))))
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    objects, separator, _predicate = raw.rpartition("を")
    if not separator:
        return None
    divisions = tuple(m.start() for m in re.finditer("と、", objects))
    def read_piece(start, end, wanted):
        piece = objects[start:end]
        if wanted[0] == "original":
            if not piece.endswith("こと"):
                return None
            clause = piece[:-2]
            parses = {(clause[:m.start()], m.group(), clause[m.end():])
                      for m in re.finditer(r"けれども|けれど|けど|のに", clause)}
            if wanted[2:] not in parses:
                return None
            nominal_start = start
            markers = {"finite_clause_nominal"}
        else:
            interpretations = set()
            nominal = ""
            event_anchor = "その出来事" if wanted[0] == "answer" else final_reception_source_anchor_text(wanted[1], index, resolver) + "こと"
            for prefix in (event_anchor + "への", event_anchor + "について、"):
                if not piece.startswith(prefix):
                    continue
                nominal = piece[len(prefix):]
                nominal_start = start + len(prefix)
                for when, temporal in (("original_occasion", "その時に"), ("answer_time", "回答した時点で"),
                                       ("prior_answer_time", "先の回答時点で")):
                    if prefix.endswith("への"):
                        for grammar in ("BELIEF", "PAST_FEELING", "PERCEIVED_0", "PERCEIVED_1", "COPULAR_PRESENT_POLITE", "COPULAR_PAST_POLITE", "ADJECTIVE_PRESENT_POLITE"):
                            value = restore_thread_answer_nominal(nominal, grammar, when)
                            if value is not None:
                                interpretations.add((value, when))
                    elif nominal.startswith(temporal) and nominal.endswith("こと"):
                        interpretations.add((nominal[len(temporal):-2], when))
            if wanted[2:] not in interpretations:
                return None
            markers = {"thread_answer_nominal", "finite_clause_nominal"}
        offset = sentence.utf8_byte_start + len(objects[:nominal_start].encode("utf-8"))
        finish = sentence.utf8_byte_start + len(objects[:end].encode("utf-8"))
        if (any(q.utf8_byte_start < finish and offset < q.utf8_byte_end for q in witness.quotes)
            or any(m.marker_code == "secondary_quote_boundary" and m.utf8_byte_start < finish
                   and offset < m.utf8_byte_end for m in witness.markers)
            or not any(m.section == "reception" and m.marker_code in markers
                       and offset <= m.utf8_byte_start and m.utf8_byte_end == finish for m in witness.markers)):
            return None
        return ((offset, finish, wanted[2].encode("utf-8")),) if wanted[0] != "original" else ()

    # Parse successive duties rather than enumerating combinations of every
    # conjunction in a potentially long answer. Cache ambiguous suffixes and
    # retain at most two parses: exactly one complete reading is required.
    from functools import lru_cache
    @lru_cache(None)
    def read_suffix(item, start):
        final = item == len(expected) - 1
        ends = (len(objects),) if final else tuple(end for end in divisions if end >= start)
        successes = []
        for end in ends:
            spans = read_piece(start, end, expected[item])
            if spans is None:
                continue
            tails = ((),) if final else read_suffix(item + 1, end + 2)
            for tail in tails:
                successes.append((*spans, *tail))
                if len(successes) == 2:
                    return tuple(successes)
        return tuple(successes)
    successes = read_suffix(0, 0)
    return successes[0] if len(successes) == 1 else None


def _body_inverse_shared_material_feeling_objects(
    body, sentence, clause, plan, resolver, selected_subjective_input,
) -> bool | None:
    """Read both source-owned objects and their one shared governed predicate.

    This is independent of the author, its replay, and its surface bindings.
    Eligibility comes from the selected duties, never from matching a suffix
    in the supplied body. A changed connective cannot evade the whole proof.
    """
    if len(clause.move_ids) != 2 or selected_subjective_input is None:
        return None
    moves_by_id = {m.move_id: m for m in plan.response_plan.human_reception_plan.moves}
    moves = tuple(moves_by_id[mid] for mid in clause.move_ids if mid in moves_by_id)
    if (len(moves) != 2 or tuple(m.move_role for m in moves) != ("attention", "felt_response")
        or any(m.reception_act != "recognize_lived_change" or not m.required
               or len(m.target_nucleus_ids) != 1 or m.support_nucleus_ids for m in moves)):
        return None
    nuclei = {n.nucleus_id: n for n in plan.nuclei}
    objects = []
    for move in moves:
        nucleus = nuclei.get(move.target_nucleus_ids[0])
        decision = next((d for d in selected_subjective_input.decisions
                         if d.move_id == move.move_id), None)
        appraisal = decision.subjective_proposition.appraisal_content if decision else None
        if (nucleus is None or not is_grounded_positive_feeling(nucleus)
            or nucleus.source_fields != ("memo",)
            or nucleus.semantic_frame.actor != "current_user"
            or _body_inverse_reception_context_ids(move, plan)
            or appraisal is None or appraisal.dimension != "MATERIAL_WEIGHT"
            or appraisal.operation != "RECEIVE_AS_MATERIAL"):
            return None
        source = final_reception_source_anchor_text(nucleus.nucleus_id, nuclei, resolver)
        if not source:
            return False
        objects.append(source + "という気持ち")
    if (len(set(m.target_nucleus_ids[0] for m in moves)) != 2
        or len(set(objects)) != 2
        or set(moves[0].source_evidence_span_ids) & set(moves[1].source_evidence_span_ids)):
        return False
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    expected = objects[0] + "も、" + objects[1] + "も、見過ごさず、受け止めています。"
    return raw == expected


def _body_inverse_nominal_constraint_clause(body, sentence, move, plan, resolver, selected_subjective_input, *, nominal="という言葉", temporal_prefix=""):
    """Restore the entire selected nominal object, including its left edge.

    A matching source substring cannot license an added experiencer, cause,
    or completed thought around it. Parse the body-owned object slot and
    compare its complete contents with the selected source, without replay.
    """
    if (sentence.section != "reception" or move.move_role != "felt_response"
        or move.reception_act != "stay_with_current_burden" or not move.required
        or len(move.target_nucleus_ids) != 1 or move.support_nucleus_ids):
        return False
    nucleus = next((n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0]), None)
    if nucleus is None or len(nucleus.source_span_ids) != 1:
        return False
    decision = next((d for d in selected_subjective_input.decisions if d.move_id == move.move_id), None) if selected_subjective_input else None
    proposition = decision.subjective_proposition if decision else None
    if proposition is None:
        return False
    appraisal = proposition.appraisal_content
    openness = bool(appraisal is not None and appraisal.operation == "LEAVE_UNFINISHED"
        or proposition.relational_position is not None
        and proposition.relational_position.stance_operator == "HOLD_UNFINISHED_OPEN")
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    parsed = re.fullmatch(
        (r"結論を急がずに、" if openness else "")
        + re.escape(temporal_prefix) + r"(?P<source>[^。！？!?]+)" + re.escape(nominal) + r"を小さくせずに(?:"
        r"(?:受け止めて|気にかけて)(?:います|いて)|"
        r"(?:受け止め|気にかけ)たいです)。", raw)
    source = str(resolver.resolve(nucleus.source_span_ids[0]).raw_text).strip(" \u3000、,。．.")
    return parsed is not None and parsed.group("source") == source



def _body_inverse_unfinished_result_clause(body, sentence, move, plan, resolver):
    """Read the complete independent event object from body bytes only."""
    from emlis_ai_grounded_observation_plan import _source_action_change_contrast_unfinished
    unfinished = _source_action_change_contrast_unfinished(plan.nuclei, plan.relations)
    if (not unfinished or move.target_nucleus_ids != unfinished or move.support_nucleus_ids
        or move.move_role != "felt_response" or move.reception_act != "stay_with_current_burden"
        or not move.required or sentence.section != "reception"):
        return False
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == unfinished[0])
    source = str(resolver.resolve(nucleus.source_span_ids[0]).raw_text).strip(" 　、,。．.")
    nominal = "こと" if source.endswith("っていない") else "という言葉"
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    parsed = re.fullmatch(r"(?P<source>[^。！？!?]+)" + nominal
        + r"を小さくせずに(?:(?:受け止めて|気にかけて)(?:います|いて)|(?:受け止め|気にかけ)たいです)。", raw)
    return parsed is not None and parsed.group("source") == source


def _body_inverse_current_material_group(body, witness, sentence, move, plan, resolver, selected_subjective_input):
    """Restore both finite source objects from bytes, without forward replay."""
    from emlis_ai_grounded_observation_plan import _source_current_material_group, _source_material_allows_reverse
    group = _source_current_material_group(plan.nuclei, plan.relations)
    if (not group or sentence.section != "reception" or move.move_role != "felt_response"
        or move.reception_act != "stay_with_current_burden" or not move.required):
        return False
    selected = (move.target_nucleus_ids, move.support_nucleus_ids)
    forward = ((group[0].nucleus_id,), (group[1].nucleus_id,))
    reverse = ((group[1].nucleus_id,), (group[0].nucleus_id,))
    reversed_focus = selected == reverse and _source_material_allows_reverse(group)
    if selected != forward and not reversed_focus:
        return False
    if reversed_focus:
        group = (group[1], group[0], *group[2:])
    decision = next((d for d in selected_subjective_input.decisions if d.move_id == move.move_id), None) if selected_subjective_input else None
    proposition = decision.subjective_proposition if decision else None
    if proposition is None:
        return False
    appraisal = proposition.appraisal_content
    openness = bool(appraisal is not None and appraisal.operation == "LEAVE_UNFINISHED"
        or proposition.relational_position is not None
        and proposition.relational_position.stance_operator == "HOLD_UNFINISHED_OPEN")
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    prefix = "結論を急がずに、" if openness else ""
    expected = tuple(str(resolver.resolve(n.source_span_ids[0]).raw_text).strip(" 　。．.") for n in group[:2])
    expected = tuple(c[:-3] + "いる" if c.endswith("残っています")
                     and "lexical:source_temporal_relief_residue" in n.semantic_frame.attribute_codes
                     else c for n, c in zip(group[:2], expected))
    decision_roles = tuple(next((role for role in ("choice", "timing")
        if "lexical:source_independent_decision_" + role in n.semantic_frame.attribute_codes), None) for n in group[:2])
    if decision_roles in {("choice", "timing"), ("timing", "choice")}:
        expected = tuple(re.sub(r"決められません$", "決められない",
                                re.sub(r"迷っています$", "迷っている", c)) for c in expected)
        if decision_roles == ("timing", "choice"):
            expected = (re.sub(r"^それとは別に[、,]?", "", expected[0]), "それとは別に、" + expected[1])
    self_topic = re.fullmatch(r"(?P<owner>私|わたし|僕|ぼく|俺|おれ)は(?P<feeling>[^、,]+)", expected[0])
    left_suffix = "というあなたの気持ち" if self_topic else "こと"
    parsed = re.fullmatch(re.escape(prefix) + r"(?P<left>[^。！？!?]+)" + re.escape(left_suffix) + r"と、(?P<right>[^。！？!?]+)こと"
        r"を小さくせずに(?:(?:受け止めて|気にかけて)(?:います|いて)|(?:受け止め|気にかけ)たいです)。", raw)
    if parsed is None:
        return False
    restored_left = (self_topic['owner'] + "は" if self_topic else "") + parsed.group("left")
    if (restored_left, parsed.group("right")) != expected:
        return False
    for name in ("left", "right"):
        start = sentence.utf8_byte_start + len(raw[:parsed.start(name)].encode())
        suffix = left_suffix if name == "left" else "こと"
        marker_code = "target_feeling" if name == "left" and self_topic else "finite_clause_nominal"
        end = sentence.utf8_byte_start + len(raw[:parsed.end(name)].encode()) + len(suffix.encode())
        if (any(q.utf8_byte_start < end and start < q.utf8_byte_end for q in witness.quotes)
            or any(m.marker_code == "secondary_quote_boundary" and m.utf8_byte_start < end and start < m.utf8_byte_end for m in witness.markers)
            or not any(m.section == "reception" and m.marker_code == marker_code
                       and start <= m.utf8_byte_start and m.utf8_byte_end == end for m in witness.markers)):
            return False
    return True


def _body_inverse_received_contrast_group(body, witness, sentence, move, plan, resolver):
    """Read each finite event/reaction pair and its actual source connector."""
    count = len(move.target_nucleus_ids)
    if (count not in {2, 3} or len(move.support_nucleus_ids) != count
        or move.reception_act != "stay_with_current_burden" or sentence.section != "reception"):
        return False
    index = {n.nucleus_id: n for n in plan.nuclei}
    expected = []
    for event_id, feeling_id in zip(move.target_nucleus_ids, move.support_nucleus_ids, strict=True):
        event, feeling = index[event_id], index[feeling_id]
        links = tuple(r for r in plan.relations if r.type == "contrast"
            and (r.from_nucleus_id, r.to_nucleus_id) == (event_id, feeling_id)
            and r.relation_id in plan.coverage_requirements.required_relation_ids)
        if (len(links) != 1 or event.kind != "event" or feeling.kind != "reaction"
            or event.semantic_frame.modality != "fact" or feeling.semantic_frame.modality != "feeling"
            or event.semantic_frame.time_scope != feeling.semantic_frame.time_scope
            or event.semantic_frame.time_scope != "past"
            or event.source_span_ids != feeling.source_span_ids or len(event.source_span_ids) != 1
            or event.source_fields != feeling.source_fields or event.source_fields not in {("memo",), ("memo_action",)}):
            return False
        left = final_reception_source_anchor_text(event_id, index, resolver)
        right = final_reception_source_anchor_text(feeling_id, index, resolver)
        raw = re.sub(r"\s+", " ", resolver.resolve(event.source_span_ids[0]).raw_text).strip(" 　、,。．.")
        if not raw.startswith(left) or not raw.endswith(right):
            return False
        connector = raw[len(left):-len(right)].rstrip("、,")
        if connector not in {"のに", "けど", "けれど", "けれども"}:
            return False
        expected.append((left, connector, right))
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    objects, separator, _predicate = raw.rpartition("を")
    pieces = objects.split("と、")
    if not separator or len(pieces) != count:
        return False
    offset = sentence.utf8_byte_start
    for piece, expected_pair in zip(pieces, expected, strict=True):
        if not piece.endswith("こと"):
            return False
        clause = piece[:-2]
        candidates = {(clause[:m.start()], m.group(), clause[m.end():])
                      for m in re.finditer(r"けれども|けれど|けど|のに", clause)}
        if expected_pair not in candidates:
            return False
        end = offset + len(piece.encode("utf-8"))
        if (any(q.utf8_byte_start < end and offset < q.utf8_byte_end for q in witness.quotes)
            or any(m.marker_code == "secondary_quote_boundary" and m.utf8_byte_start < end
                   and offset < m.utf8_byte_end for m in witness.markers)
            or not any(m.section == "reception" and m.marker_code == "finite_clause_nominal"
                       and offset <= m.utf8_byte_start and m.utf8_byte_end == end for m in witness.markers)):
            return False
        offset = end + len("と、".encode("utf-8"))
    return True


def _body_inverse_thread_answer_group(body, witness, sentence, move, plan, resolver):
    """Parse all event/answer/time pairs from one actual reception sentence.

    No forward group or rendered reference is consulted. Every reconstructed
    pair must resolve once to the selected source duties in their own order.
    Returned byte ranges are also safe grammatical views for sensation checks.
    """
    if (getattr(resolver, "source_contract", None) != "cocolon.cmee.emlis_thread.v1"
        or not 2 <= len(move.target_nucleus_ids) <= 3 or move.support_nucleus_ids
        or move.reception_act != "stay_with_current_burden" or sentence.section != "reception"):
        return ()
    index = {n.nucleus_id: n for n in plan.nuclei}
    expected = []
    for nid in move.target_nucleus_ids:
        n = index[nid]
        times = {c.split(":", 1)[1] for c in n.semantic_frame.attribute_codes if c.startswith("thread_time:")}
        about = tuple(r for r in plan.relations if r.type == "evaluation_about_event"
            and r.relation_id in plan.coverage_requirements.required_relation_ids and r.to_nucleus_id == nid)
        if (n.source_fields != ("answer_text_private",) or n.allowed_claim_scope != "explicit_supplemental_answer"
            or n.kind != "reaction" or n.semantic_frame.modality != "feeling"
            or n.semantic_frame.polarity != "negative" or len(times) != 1 or len(about) != 1):
            return ()
        event = index[about[0].from_nucleus_id]
        if event.kind != "event" or event.source_fields not in {("memo",), ("memo_action",)}:
            return ()
        expected.append((final_reception_source_anchor_text(event.nucleus_id, index, resolver),
                         final_reception_source_anchor_text(nid, index, resolver), next(iter(times))))
    if len(set(expected)) != len(expected):
        return ()
    raw = body[sentence.utf8_byte_start:sentence.utf8_byte_end].decode("utf-8")
    objects, separator, _predicate = raw.rpartition("を")
    if not separator:
        return ()
    divisions = tuple(m.start() for m in re.finditer("と、", objects))
    successes = []
    for cuts in combinations(divisions, len(expected) - 1):
        starts = (0, *(i + 2 for i in cuts))
        ends = (*cuts, len(objects))
        restored, spans = [], []
        for start, end in zip(starts, ends, strict=True):
            piece = objects[start:end]
            boundaries = tuple((piece.index(s), s) for s in ("ことへの", "ことについて、") if s in piece)
            if not boundaries:
                break
            boundary, sep = min(boundaries)
            event, nominal = piece[:boundary], piece[boundary + len(sep):]
            interpretations = set()
            for when, prefix in (("original_occasion", "その時に"), ("answer_time", "回答した時点で"),
                                 ("prior_answer_time", "先の回答時点で")):
                for grammar in ("BELIEF", "PAST_FEELING", "PERCEIVED_0", "PERCEIVED_1", "COPULAR_PRESENT_POLITE", "COPULAR_PAST_POLITE", "ADJECTIVE_PRESENT_POLITE"):
                    source = restore_thread_answer_nominal(nominal, grammar, when)
                    if source is not None and sep == "ことへの":
                        interpretations.add((event, source, when))
                if sep == "ことについて、" and nominal.startswith(prefix) and nominal.endswith("こと"):
                    interpretations.add((event, nominal[len(prefix):-2], when))
            matches = interpretations.intersection(expected)
            if len(matches) != 1:
                break
            match = next(iter(matches))
            restored.append(match)
            offset = sentence.utf8_byte_start + len(objects[:start + len(event) + len(sep)].encode("utf-8"))
            finish = offset + len(nominal.encode("utf-8"))
            if (any(q.utf8_byte_start < finish and offset < q.utf8_byte_end for q in witness.quotes)
                or any(m.marker_code == "secondary_quote_boundary" and m.utf8_byte_start < finish
                       and offset < m.utf8_byte_end for m in witness.markers)
                or not any(m.section == "reception" and m.marker_code in {"thread_answer_nominal", "finite_clause_nominal"}
                           and offset <= m.utf8_byte_start and m.utf8_byte_end == finish for m in witness.markers)):
                break
            spans.append((offset, finish, match[1].encode("utf-8")))
        if tuple(restored) == tuple(expected) and len(spans) == len(expected):
            successes.append(tuple(spans))
    return successes[0] if len(successes) == 1 else ()


def _body_inverse_answer_limit(body, parsed_line, planned_line, plan, resolver):
    """Read the completed limit sentence without replaying the renderer.

    Nested source quotes remain source text. Only the outside predicate says
    that part of this answer is unreflected; it makes no claim about the user.
    """
    binding = planned_line.binding
    ids = tuple(atom[len("unknown_boundary:"):] for atom in binding.functional_atom_ids
                if atom.startswith("unknown_boundary:"))
    boundaries = tuple(row for row in plan.unknown_boundaries
        if row.dimension == "answer_interpretation_unresolved" and row.unknown_id in ids)
    if (len(ids) != 1 or len(boundaries) != 1
        or binding.nucleus_ids or binding.relation_ids or not binding.required
        or binding.line_role != "limited_scope" or planned_line.surface_function != "render_limited_scope"
        or boundaries[0].affected_nucleus_ids or boundaries[0].surface_policy != "do_not_claim"
        or binding.evidence_span_ids != boundaries[0].evidence_span_ids
        or not binding.evidence_span_ids
        or getattr(resolver, "source_contract", None) != "cocolon.cmee.emlis_thread.v1"
        or resolver.source_fields_for(binding.evidence_span_ids) != ("answer_text_private",)):
        return False
    text = body[parsed_line.utf8_byte_start:parsed_line.utf8_byte_end].decode("utf-8")
    prefix, suffix = "回答の", "には、今回の観測に反映できていない部分があります。"
    if not text.startswith(prefix) or not text.endswith(suffix):
        return False
    quoted = text[len(prefix):-len(suffix)]
    values, start = [], 0
    while start < len(quoted):
        if quoted[start] != "「":
            return False
        stack, end = ["「"], start + 1
        while end < len(quoted) and stack:
            if quoted[end] in "「『":
                stack.append(quoted[end])
            elif quoted[end] in "」』":
                if stack[-1] != {"」": "「", "』": "『"}[quoted[end]]:
                    return False
                stack.pop()
            end += 1
        if stack or quoted[end-1] != "」":
            return False
        values.append(quoted[start+1:end-1])
        if end == len(quoted):
            break
        if quoted[end:end+2] != "と「":
            return False
        start = end + 1
    # Resolve the source independently of its forward surface. Separators
    # inside a contiguous range are evidence too, not invented conjunctions.
    return tuple(values) == (resolver.source_text_for_contiguous_spans(boundaries[0].evidence_span_ids),)


def evaluate_grounded_surface_body_inverse(
    *,
    body: bytes,
    plan: GroundedObservationPlan,
    sentence_plan: GroundedSentencePlan,
    resolver: EvidenceSpanResolver,
    selected_subjective_input: SelectedSubjectiveReceptionInputV1 | None = None,
) -> GroundedBodyInverseEvaluation:
    """Re-parse final bytes and independently match plan-visible duties.

    The parser is body-only.  This matcher then checks section/line order,
    source-bound quote order, relation and boundary markers, and the distinct
    human-reception duty against the canonical plans.  It never consults a
    forward parser witness or serialized source text.
    """

    witness = parse_grounded_surface_body_bytes(body)
    failures: list[str] = list(witness.structural_issues)
    final_stage1_plan = _body_inverse_is_final_stage1_plan(plan)
    observation_lines = tuple(
        row for row in witness.lines if row.section == "observation"
    )
    reception_lines = tuple(
        row for row in witness.lines if row.section == "reception"
    )
    planned_observation_lines = tuple(
        row
        for row in sentence_plan.lines
        if row.binding.line_role != "human_follow"
    )
    planned_reception_lines = tuple(
        row
        for row in sentence_plan.lines
        if row.binding.line_role == "human_follow"
    )
    nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
    if witness.section_order != ("observation", "reception"):
        failures.append("body_inverse_section_order_mismatch")
    if len(observation_lines) != len(planned_observation_lines):
        failures.append("body_inverse_observation_line_count_mismatch")
    if len(reception_lines) != len(planned_reception_lines):
        failures.append("body_inverse_reception_line_count_mismatch")
    expected_limit_ids = tuple(row.unknown_id for row in plan.unknown_boundaries
                              if row.dimension == "answer_interpretation_unresolved")
    actual_limit_ids = tuple(atom[len("unknown_boundary:"):]
        for line in planned_observation_lines
        if line.binding.claim_scope == "unresolved_answer_interpretation"
        for atom in line.binding.functional_atom_ids if atom.startswith("unknown_boundary:"))
    if actual_limit_ids != expected_limit_ids:
        failures.append("body_inverse_answer_limit_duty_missing")

    sentence_line_index = {
        (row.section, row.section_ordinal): row.section_line_ordinal
        for row in witness.sentences
    }

    def quotes_for_line(section: str, line_ordinal: int) -> tuple[Any, ...]:
        return tuple(
            row
            for row in witness.quotes
            if row.section == section
            and sentence_line_index.get((row.section, row.sentence_ordinal))
            == line_ordinal
        )

    for index, (parsed_line, planned_line) in enumerate(
        zip(observation_lines, planned_observation_lines),
        start=1,
    ):
        if planned_line.binding.claim_scope == "unresolved_answer_interpretation":
            if not _body_inverse_answer_limit(body, parsed_line, planned_line, plan, resolver):
                failures.append(f"body_inverse_answer_limit_mismatch:{index}")
            continue
        quote_rows = quotes_for_line("observation", parsed_line.section_ordinal)
        expected_sources = _body_inverse_source_values(planned_line, plan, resolver)
        # Independently read a complete, source-bound finite cognition clause.
        # This is an exact source obligation, not a quote-free fallback. The
        # writer and this matcher do not share a renderer or its witness.
        direct_cognition = False
        direct_provisional = False
        direct_decision = False
        binding = planned_line.binding
        if (final_stage1_plan
            and (planned_line.surface_function, binding.claim_scope) in {
                ("observe_nuclei", "single_input_bounded_observation"),
                ("render_limited_scope", "limited_grounding_no_event_completion"),
            }
            and len(binding.nucleus_ids) == 1 and not binding.relation_ids):
            cognition = nucleus_index.get(binding.nucleus_ids[0])
            if cognition is not None:
                cf = cognition.semantic_frame
                codes = set(cf.attribute_codes)
                provisional = bool(cognition.kind == cf.predicate_kind == "change"
                    and (cf.actor, cf.modality, cf.polarity, cf.time_scope)
                        == ("current_user", "fact", "mixed", "current_input")
                    and {"lexical:source_provisional_degree", "lexical:preserve_source_predicate"} <= codes)
                decision_roles = tuple(role for role in ("choice", "timing")
                    if "lexical:source_independent_decision_" + role in codes)
                decision = bool(len(decision_roles) == 1 and cognition.kind == cf.predicate_kind == "uncertainty"
                    and cf.actor == "current_user" and cf.modality == "uncertain" and cf.time_scope == "present"
                    and cf.polarity == ("neutral" if decision_roles[0] == "choice" else "negative")
                    and {"operator:uncertainty", "semantic_role:limiting_unknown", "lexical:preserve_source_predicate"} <= codes)
                if ((provisional or decision or (cognition.kind == cf.predicate_kind == "uncertainty"
                    and cf.actor == "current_user" and cf.modality == "uncertain"
                    and cf.polarity == "negative" and cf.time_scope in {"present", "current_input"}
                    and {"operator:negation", "operator:uncertainty", "semantic_role:limiting_unknown",
                         "lexical:preserve_source_predicate"} <= codes))
                    and cognition.grounding_kind == "explicit" and cognition.retention == "required"
                    and cognition.source_fields in {("memo",), ("memo_action",)}
                    and len(cognition.source_span_ids) == 1
                    and binding.evidence_span_ids == cognition.source_span_ids
                    and not any(code.startswith(("thread_time:", "source_fragment_", "surface_scalar_"))
                                or code == "semantic_role:embedded_turn" for code in codes)):
                    source_span = resolver.resolve(cognition.source_span_ids[0])
                    source_clause = str(source_span.raw_text).strip(" \u3000。．.")
                    from emlis_ai_grounded_observation_plan import _source_provisional_degree_parts, _source_independent_decision_clause_parts
                    if (source_span.source_field == cognition.source_fields[0]
                        and 0 <= source_span.start_index < source_span.end_index
                        and (provisional and _source_provisional_degree_parts(source_clause) is not None
                             or decision and (_source_independent_decision_clause_parts(source_clause) or (None,))[0] == decision_roles[0]
                             or re.fullmatch(r"(?:(?:現在|今)(?:も|は))?(?:まだ)?(?:はっきり|よく)?(?:わからない|分からない)", source_clause)
                             or "lexical:source_feeling_reason_unknown" in codes
                             and re.fullmatch(r"(?:(?:何故|どうして|なぜ)そう感じるのか|その理由)(?:が|は)?"
                                              r"(?:まだ)?(?:はっきり|よく)?(?:わからない|分からない)", source_clause)
                             or "lexical:source_temporal_causal_unknown" in codes
                             and re.fullmatch(r".*(?:現在|今|今日)の(?:きっかけ|原因|理由)が同じか(?:も|は)?"
                                              r"(?:まだ)?(?:はっきり|よく)?(?:わからない|分からない)", source_clause))):
                        direct_cognition = True
                        if provisional:
                            source_clause = re.sub(r"(気[がはも])します(?=けれど|けど)", r"\1する", source_clause)
                            source_clause = re.sub(r"ないです$|ありません$", "ない", source_clause)
                            if "lexical:source_denied_resolution" in codes:
                                source_clause = re.sub(r"思いました$", "思った", source_clause)
                                source_clause = re.sub(r"思えました$", "思えた", source_clause)
                        if decision:
                            source_clause = re.sub(r"迷っています$", "迷っている", source_clause)
                            source_clause = re.sub(r"決められません$", "決められない", source_clause)
                        visible = _body_inverse_visible_text(body, parsed_line)
                        if "scope_hedge" in binding.functional_atom_ids:
                            if not visible.startswith("今の入力だけを見ると、"):
                                failures.append(f"body_inverse_cognition_scope_missing:{index}")
                            else:
                                visible = visible[len("今の入力だけを見ると、"):]
                        matched = re.fullmatch(r"(?P<source>.+)のですね。", visible)
                        if (quote_rows or not matched or matched.group("source") != source_clause):
                            failures.append(f"body_inverse_cognition_source_or_predicate_mismatch:{index}")
                        elif provisional:
                            direct_provisional = True
                        elif decision:
                            direct_decision = True
        if expected_sources and not quote_rows and not direct_cognition:
            failures.append(f"body_inverse_observation_source_anchor_missing:{index}")
        normalized_quote_texts: list[str] = []
        for quote_row in quote_rows:
            try:
                quote_text = _body_inverse_normalized_anchor(
                    _body_inverse_quote_text(body, quote_row)
                )
            except (UnicodeDecodeError, ValueError):
                failures.append(f"body_inverse_quote_bytes_invalid:{index}")
                continue
            normalized_quote_texts.append(quote_text)
            matches = tuple(
                source_index
                for source_index, source_text in enumerate(expected_sources)
                if _body_inverse_anchor_matches(quote_text, source_text)
            )
            if not matches:
                failures.append(f"body_inverse_unbound_observation_quote:{index}")
                continue
        if planned_line.binding.relation_ids and not parsed_line.relation_marker_codes:
            failures.append(f"body_inverse_required_relation_marker_missing:{index}")
        relation_index = {item.relation_id: item for item in plan.relations}
        shared_change_relations = frozenset()
        if final_stage1_plan:
            shared_change_relations, reference_failures = _body_inverse_observation_change_reference(
                body, witness, parsed_line, planned_line, plan, resolver,
            )
            failures.extend(reference_failures)
        grouped_answers = frozenset()
        if getattr(resolver, "source_contract", None) == "cocolon.cmee.emlis_thread.v1":
            grouped_answers, group_failures = _body_inverse_thread_contrast_answers(
                body, witness, parsed_line, plan, resolver)
            failures.extend(group_failures)
        for relation_id in planned_line.binding.relation_ids:
            relation = relation_index.get(relation_id)
            if relation is None:
                failures.append(f"body_inverse_required_relation_missing:{index}")
                continue
            allowed_markers = _BODY_INVERSE_RELATION_MARKERS_BY_TYPE.get(
                relation.type,
                frozenset(),
            )
            if allowed_markers and not (
                set(parsed_line.relation_marker_codes) & allowed_markers
            ):
                failures.append(
                    f"body_inverse_relation_type_marker_mismatch:{index}"
                )
            from_values = _body_inverse_nucleus_source_values(
                relation.from_nucleus_id,
                plan,
                resolver,
            )
            to_values = _body_inverse_nucleus_source_values(
                relation.to_nucleus_id,
                plan,
                resolver,
            )
            from_positions = tuple(
                quote_index
                for quote_index, quote_text in enumerate(normalized_quote_texts)
                if any(
                    _body_inverse_anchor_matches(quote_text, source_text)
                    for source_text in from_values
                )
            )
            to_positions = tuple(
                quote_index
                for quote_index, quote_text in enumerate(normalized_quote_texts)
                if any(
                    _body_inverse_anchor_matches(quote_text, source_text)
                    for source_text in to_values
                )
            )
            if final_stage1_plan and (
                not from_positions or not to_positions
            ):
                failures.append(
                    f"body_inverse_relation_endpoint_missing:{index}"
                )
            if (
                relation.type in DIRECTIONAL_GROUNDED_RELATION_TYPES
                and relation_id not in grouped_answers
                and relation_id not in shared_change_relations
                and from_positions
                and to_positions
                and not any(
                    to_position == from_position + 1
                    for from_position in from_positions
                    for to_position in to_positions
                )
            ):
                failures.append(f"body_inverse_relation_direction_reversed:{index}")
            if relation.type == "contrast" and len(planned_line.binding.relation_ids) > 1:
                # Each visible pair must remain adjacent, even when several
                # independent pairs share a single coordinated predicate.
                if not any(b == a + 1 for a in from_positions for b in to_positions):
                    failures.append(f"body_inverse_contrast_pair_crossed:{index}")
            # The typed event/past-feeling sentence owes both complete clauses,
            # their ordered contrast, and a past (not current or causal) reading.
            # Recover these duties from source and body bytes, never author replay.
            if (final_stage1_plan and relation.type == "contrast"
                and len(planned_line.binding.relation_ids) == 1):
                event = nucleus_index[relation.from_nucleus_id]
                feeling = nucleus_index[relation.to_nucleus_id]
                sentence_rows = tuple(row for row in witness.sentences
                    if row.section == "observation"
                    and row.section_line_ordinal == parsed_line.section_ordinal)
                if sentence_rows:
                    first_sentence = _body_inverse_visible_text(body, sentence_rows[0])
                    exterior = re.sub(r"「[^「」]*」|『[^『』]*』", "", first_sentence)
                    if "という経緯" in exterior or "という気持ちも" in exterior:
                        supported = (
                            event.kind == "event" and event.semantic_frame.modality == "fact"
                            and feeling.kind == "reaction"
                            and feeling.semantic_frame.predicate_kind == "feeling"
                            and feeling.semantic_frame.modality == "feeling"
                            and feeling.semantic_frame.polarity == "positive"
                            and feeling.semantic_frame.time_scope == "past"
                            and "lexical:source_nominal_past_feeling" in feeling.semantic_frame.attribute_codes
                            and all(n.semantic_frame.actor == "current_user"
                                and n.grounding_kind == "explicit" and n.source_fields == ("memo",)
                                and len(n.source_span_ids) == 1
                                and not _body_inverse_action_is_performed(n)
                                and not _body_inverse_action_is_future_intention(n)
                                and not any(c.startswith(("source_fragment_scalar_", "surface_scalar_", "thread_time:"))
                                    or c == "semantic_role:generic_relation_fragment"
                                    for c in n.semantic_frame.attribute_codes)
                                for n in (event, feeling)))
                        originals = tuple(str(resolver.resolve(n.source_span_ids[0]).raw_text or "").strip(" \u3000、,。．.")
                                          for n in (event, feeling)) if supported else ()
                        matched = re.fullmatch(r"「([^「」]+)」という経緯があった一方で、"
                            r"「([^「」]+)」という気持ちもあったのですね。", first_sentence)
                        if (not supported or not matched
                            or not re.search(r"(?:かった|[てで]いた|た|だ)$", originals[0])
                            or any(re.search(r"[「」『』“”‘’\"?？!！。;；…‥\n]", text) for text in originals)
                            or tuple(map(_body_inverse_normalized_anchor, matched.groups()))
                               != tuple(map(_body_inverse_normalized_anchor, originals))):
                            failures.append(f"body_inverse_past_feeling_contrast_scope_mismatch:{index}")
            if (relation.type == "evaluation_about_event"
                    and getattr(resolver, "source_contract", None) == "cocolon.cmee.emlis_thread.v1"):
                visible = _body_inverse_normalized_anchor(_body_inverse_visible_text(body, parsed_line))
                left_sources = _body_inverse_nucleus_source_values(relation.from_nucleus_id, plan, resolver)
                right_sources = _body_inverse_nucleus_source_values(relation.to_nucleus_id, plan, resolver)
                target_codes = set(nucleus_index[relation.to_nucleus_id].semantic_frame.attribute_codes)
                when = "先の回答時点" if "thread_time:prior_answer_time" in target_codes else "回答した時点" if "thread_time:answer_time" in target_codes else "その時"
                if relation_id not in grouped_answers and not (any(b == a + 1 for a in from_positions for b in to_positions) and
                        any(re.search(re.escape(left) + r"[^。]*に対する" + when + r"の受け止めとして[^。]*" + re.escape(right), visible)
                            for left in left_sources for right in right_sources)):
                    failures.append(f"body_inverse_answer_target_relation_missing:{index}")
        if (
            planned_line.binding.line_role == "fact_boundary"
            and "fact_boundary" not in parsed_line.uncertainty_marker_codes
        ):
            failures.append(f"body_inverse_fact_boundary_marker_missing:{index}")
        if (
            planned_line.binding.line_role == "limited_opposition"
            and not set(parsed_line.relation_marker_codes)
            & {"counterdirection", "coexistence"}
        ):
            failures.append(f"body_inverse_limited_opposition_marker_missing:{index}")
        required_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in planned_line.binding.nucleus_ids
            if nucleus_id in nucleus_index
            and nucleus_id in set(plan.coverage_requirements.required_nucleus_ids)
        )
        # An undivided current feeling or proven denied report still owes its
        # complete scene/host in Layer 1, independently of its Layer 2 referent.
        # Substring matching must not accept deleting that scene merely because
        # the remaining feeling names the Layer 2 referent. Typed fragments and
        # relation surfaces retain their separate source obligations.
        if (
            final_stage1_plan
            and not plan.relations
            and len(required_nuclei) == 1
            and sum(bool(set(item.source_fields) & {"memo", "memo_action"})
                    for item in plan.nuclei) == 1
        ):
            whole_nucleus = required_nuclei[0]
            frame = whole_nucleus.semantic_frame
            if (
                (
                    whole_nucleus.source_fields == ("memo",)
                    and is_grounded_positive_feeling(whole_nucleus)
                    and frame.time_scope in {"present", "current_input"}
                    or whole_nucleus.source_fields in {("memo",), ("memo_action",)}
                    and whole_nucleus.kind == frame.predicate_kind == "state"
                    and frame.polarity == "negative" and frame.modality == "fact"
                    and frame.time_scope == "past"
                    and "lexical:source_denied_past_thought_report" in frame.attribute_codes
                )
                and len(whole_nucleus.source_span_ids) == 1
                and frame.actor == "current_user"
                and not any(
                    code == "semantic_role:generic_relation_fragment"
                    or code.startswith(("source_fragment_scalar_", "surface_scalar_"))
                    for code in frame.attribute_codes
                )
            ):
                whole_sources = _body_inverse_nucleus_source_values(
                    whole_nucleus.nucleus_id, plan, resolver
                )
                if not whole_sources or any(
                    not any(source_text in quote_text for quote_text in normalized_quote_texts)
                    for source_text in whole_sources
                ):
                    failures.append(f"body_inverse_observation_source_anchor_incomplete:{index}")
        required_kinds = {item.kind for item in required_nuclei}
        # Each finite appraisal retains its complete host independently of
        # the other layer. A surviving adjective must not stand in for a
        # deleted tentative host, nor a verb for its nominalized evaluation.
        for nucleus in required_nuclei:
            if final_stage1_plan and {"lexical:source_appraisal_tentative",
                    "lexical:source_appraisal_alternative"} & set(nucleus.semantic_frame.attribute_codes):
                source_values = _body_inverse_nucleus_source_values(nucleus.nucleus_id, plan, resolver)
                if not source_values or any(not any(value in quote for quote in normalized_quote_texts)
                                            for value in source_values):
                    failures.append(f"body_inverse_appraisal_host_incomplete:{index}")
        if getattr(resolver, "source_contract", None) == "cocolon.cmee.emlis_thread.v1":
            visible_line = _body_inverse_visible_text(body, parsed_line)
            for nucleus in required_nuclei:
                if nucleus.source_fields != ("answer_text_private",):
                    continue
                source_values = _body_inverse_nucleus_source_values(nucleus.nucleus_id, plan, resolver)
                if not source_values or any(not any(value in quote for quote in normalized_quote_texts)
                                            for value in source_values):
                    failures.append(f"body_inverse_answer_source_anchor_incomplete:{index}")
                times = {code.split(":", 1)[1] for code in nucleus.semantic_frame.attribute_codes
                         if code.startswith("thread_time:")}
                expected = "先の回答時点" if times == {"prior_answer_time"} else "回答した時点" if times == {"answer_time"} else "その時" if times == {"original_occasion"} else None
                if expected is None or expected not in visible_line:
                    failures.append(f"body_inverse_answer_target_time_missing:{index}")
        if ("change" in required_kinds and "change" not in parsed_line.semantic_marker_codes
            and not direct_provisional):
            failures.append(f"body_inverse_required_change_missing:{index}")
        if (
            "constraint" in required_kinds
            and "constraint" not in parsed_line.semantic_marker_codes
        ):
            failures.append(f"body_inverse_required_constraint_missing:{index}")
        if (
            (
                "uncertainty" in required_kinds
                or any(
                    "semantic_role:limiting_unknown"
                    in item.semantic_frame.attribute_codes
                    for item in required_nuclei
                )
            )
            and "unknown" not in parsed_line.semantic_marker_codes
            and not parsed_line.uncertainty_marker_codes
            # This exact finite host already states the unresolved object.
            # A changed/deleted host fails the complete source match above.
            and not direct_decision
        ):
            failures.append(f"body_inverse_required_unknown_missing:{index}")
        required_future_intention = any(
            item.kind == "wish"
            and item.semantic_frame.modality in {"wish", "intention"}
            for item in required_nuclei
        ) or (
            final_stage1_plan
            and any(
                _body_inverse_action_is_future_intention(item)
                for item in required_nuclei
            )
        )
        if (
            required_future_intention
            and "intention" not in parsed_line.semantic_marker_codes
        ):
            failures.append(f"body_inverse_required_intention_missing:{index}")
        required_effort = (
            any(
                _body_inverse_action_is_performed(item)
                for item in required_nuclei
            )
            if final_stage1_plan
            else "action" in required_kinds
        )
        if (
            required_effort
            and "effort" not in parsed_line.semantic_marker_codes
        ):
            failures.append(f"body_inverse_required_effort_missing:{index}")

    for index, (parsed_line, planned_line) in enumerate(
        zip(reception_lines, planned_reception_lines),
        start=1,
    ):
        if not parsed_line.reception_marker_codes:
            failures.append(f"body_inverse_reception_response_marker_missing:{index}")
        if (
            "reception_speaker:explicit_emlis"
            in planned_line.binding.functional_atom_ids
            and "emlis_voice" not in parsed_line.reception_marker_codes
        ):
            failures.append(f"body_inverse_explicit_emlis_voice_missing:{index}")
        quote_rows = quotes_for_line("reception", parsed_line.section_ordinal)
        expected_sources = _body_inverse_source_values(planned_line, plan, resolver)
        for quote_row in quote_rows:
            try:
                quote_text = _body_inverse_normalized_anchor(
                    _body_inverse_quote_text(body, quote_row)
                )
            except (UnicodeDecodeError, ValueError):
                failures.append(f"body_inverse_reception_quote_bytes_invalid:{index}")
                continue
            matches = tuple(
                source_index
                for source_index, source_text in enumerate(expected_sources)
                if _body_inverse_anchor_matches(quote_text, source_text)
            )
            if not matches:
                failures.append(f"body_inverse_unbound_reception_quote:{index}")
                continue

        atom_values = set(planned_line.binding.functional_atom_ids)
        min_values = tuple(
            int(atom.rsplit(":", 1)[1])
            for atom in atom_values
            if atom.startswith("reception_sentence_min:")
            and atom.rsplit(":", 1)[1].isdigit()
        )
        max_values = tuple(
            int(atom.rsplit(":", 1)[1])
            for atom in atom_values
            if atom.startswith("reception_sentence_max:")
            and atom.rsplit(":", 1)[1].isdigit()
        )
        if min_values and parsed_line.sentence_count < min_values[0]:
            failures.append(f"body_inverse_reception_sentence_underflow:{index}")
        if max_values and parsed_line.sentence_count > max_values[0]:
            failures.append(f"body_inverse_reception_sentence_overflow:{index}")

        reception_plan = plan.response_plan.human_reception_plan
        if reception_plan is not None:
            if final_stage1_plan:
                try:
                    replay = replay_source_grounded_human_reception_from_plan(
                        reception_plan, nucleus_index, resolver,
                        plan=plan,
                        recovery_stage=sentence_plan.recovery_stage,
                        clause_plans=planned_line.reception_clause_plans,
                        selected_subjective_input=selected_subjective_input,
                    )
                    if not _received_discourse_equivalent(
                        _body_inverse_visible_text(body, parsed_line), replay.text,
                        reception_plan, planned_line.reception_clause_plans, plan, resolver,
                        selected_subjective_input):
                        failures.append(f"body_inverse_reception_replay_mismatch:{index}")
                except (GroundedHumanReceptionSurfaceError, AttributeError, KeyError, TypeError, ValueError):
                    failures.append(f"body_inverse_reception_replay_unavailable:{index}")
            parsed_codes = set(parsed_line.reception_marker_codes)
            if not final_stage1_plan:
                for move in reception_plan.moves:
                    if not move.required:
                        continue
                    target_markers = (
                        _BODY_INVERSE_RECEPTION_ACT_TARGET_MARKERS.get(
                            move.reception_act,
                            frozenset(),
                        )
                    )
                    if target_markers and not parsed_codes.intersection(
                        target_markers
                    ):
                        failures.append(
                            "body_inverse_reception_target_duty_missing:"
                            f"{move.move_id}"
                        )
                    if (
                        move.move_role == "attention"
                        and "attention" not in parsed_codes
                    ):
                        failures.append(
                            "body_inverse_reception_attention_duty_missing:"
                            f"{move.move_id}"
                        )
                    why_markers = {
                        "stay_with_current_burden": {"receive"},
                        "honor_concrete_effort": {
                            "receive",
                            "felt_response",
                        },
                        "protect_retained_intention": {
                            "attention",
                            "protect",
                            "receive",
                        },
                        "recognize_lived_change": {
                            "attention",
                            "felt_response",
                        },
                        "hold_help_seeking": {
                            "attention",
                            "felt_response",
                        },
                        "bounded_counter_self_denial": {"protect"},
                        "respect_words_placed": {
                            "receive",
                            "felt_response",
                        },
                    }.get(move.reception_act, set())
                    if why_markers and not parsed_codes.intersection(
                        why_markers
                    ):
                        failures.append(
                            "body_inverse_reception_why_duty_missing:"
                            f"{move.move_id}"
                        )
            else:
                parsed_sentences = tuple(
                    row
                    for row in witness.sentences
                    if row.section == "reception"
                    and row.section_line_ordinal
                    == parsed_line.section_ordinal
                )
                clause_plans = tuple(planned_line.reception_clause_plans)
                if len(parsed_sentences) != len(clause_plans):
                    failures.append(
                        f"body_inverse_reception_clause_count_mismatch:{index}"
                    )
                move_index = {
                    move.move_id: move for move in reception_plan.moves
                }
                expected_referent_by_move: dict[str, Any] = {}
                anchor_used = False
                for clause in clause_plans:
                    for move_id in clause.move_ids:
                        move = move_index.get(move_id)
                        if move is None:
                            continue
                        try:
                            referent = resolve_grounded_reception_move_referent(
                                reception_plan,
                                move,
                                nucleus_index,
                                resolver,
                                allow_short_anchor=False,
                                recovery_stage=sentence_plan.recovery_stage,
                                allow_anaphoric_topic=True,
                                final_source_fidelity=final_stage1_plan,
                                plan=plan,
                            )
                        except (
                            GroundedHumanReceptionSurfaceError,
                            AttributeError,
                            KeyError,
                            TypeError,
                        ):
                            failures.append(
                                "body_inverse_reception_referent_unavailable:"
                                f"{move_id}"
                            )
                            continue
                        anchor_used = anchor_used or referent.source_anchor_used
                        expected_referent_by_move[move_id] = referent
                for clause_index, (clause, parsed_sentence) in enumerate(zip(
                    clause_plans,
                    parsed_sentences,
                )):
                    try:
                        parsed_sentence_text = (
                            _body_inverse_normalized_anchor(
                                _body_inverse_visible_text(
                                    body,
                                    parsed_sentence,
                                )
                            )
                        )
                    except (UnicodeDecodeError, ValueError):
                        failures.append(
                            f"body_inverse_reception_sentence_bytes_invalid:{index}"
                        )
                        continue
                    sentence_codes = set(
                        parsed_sentence.reception_marker_codes
                    )
                    if final_stage1_plan and sentence_plan.recovery_stage == "full":
                        shared_objects = _body_inverse_shared_material_feeling_objects(
                            body, parsed_sentence, clause, plan, resolver, selected_subjective_input,
                        )
                        if len(clause.move_ids) == 2 and shared_objects is not True:
                            failures.append("body_inverse_shared_feeling_objects_invalid:"
                                            + str(clause.sentence_slot))
                    for move_id in clause.move_ids:
                        move = move_index.get(move_id)
                        if move is None or not move.required:
                            continue
                        finite_proof = read_source_owned_discourse(
                            body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8"),
                            move, plan, resolver, selected_subjective_input,
                            preceding_context=(
                                move_index[clause_plans[clause_index - 1].move_ids[0]],
                                body[parsed_sentences[clause_index - 1].utf8_byte_start:
                                     parsed_sentences[clause_index - 1].utf8_byte_end].decode("utf-8"),
                            ) if clause_index and len(clause_plans[clause_index - 1].move_ids) == 1 else None,
                        ) if (final_stage1_plan and len(clause.move_ids) == 1
                              and sentence_plan.recovery_stage == "full") else None
                        if finite_proof is not None:
                            # Complete body-owned proposition/edge verification
                            # replaces nominal/closing-token requirements only.
                            # Source, plan, clause, trace and safety gates remain.
                            continue
                        target_nuclei = tuple(
                            nucleus_index[nucleus_id]
                            for nucleus_id in move.target_nucleus_ids
                            if nucleus_id in nucleus_index
                        )
                        if any(
                            _body_inverse_action_is_future_intention(nucleus)
                            for nucleus in target_nuclei
                        ):
                            target_markers = frozenset({"target_intention"})
                        elif (
                            final_stage1_plan
                            and move.reception_act == "recognize_lived_change"
                            and target_nuclei
                            and len(target_nuclei) == len(move.target_nucleus_ids)
                            and all(is_grounded_positive_feeling(nucleus)
                                    for nucleus in target_nuclei)
                        ):
                            # The same source-bound feeling used before
                            # selection must be visible in the parsed body.
                            # Change/words markers cannot discharge this duty.
                            target_markers = frozenset({"target_feeling"})
                            if (getattr(resolver, "source_contract", None) == "cocolon.cmee.emlis_thread.v1"
                                and len(target_nuclei) == 1
                                and target_nuclei[0].source_fields == ("answer_text_private",)):
                                answer = target_nuclei[0]
                                times = {code.split(":", 1)[1] for code in answer.semantic_frame.attribute_codes
                                         if code.startswith("thread_time:")}
                                prefixes = {"original_occasion": "その時に", "answer_time": "回答した時点で",
                                            "prior_answer_time": "先の回答時点で"}
                                source = final_reception_source_anchor_text(answer.nucleus_id,nucleus_index,resolver)
                                phrase = (prefixes[next(iter(times))]+source+"という気持ち").encode() if (
                                    len(times) == 1 and times <= prefixes.keys() and source
                                    and answer.allowed_claim_scope == "explicit_supplemental_answer") else b""
                                nominal_answer = source_grounded_thread_answer_nominal(move, plan, nucleus_index, resolver)
                                if nominal_answer is not None:
                                    _, original, grammar, when, nominal = nominal_answer
                                    if original != source or restore_thread_answer_nominal(nominal, grammar, when) != source:
                                        phrase = b""
                                    else:
                                        phrase = (nominal + "という気持ち").encode()
                                # Restore the whole event/time/feeling object from
                                # its required source relation, not an inner phrase
                                # that could sit under a newly inserted experiencer.
                                about = tuple(r for r in plan.relations
                                    if r.type == "evaluation_about_event"
                                    and r.to_nucleus_id == answer.nucleus_id
                                    and r.relation_id in plan.coverage_requirements.required_relation_ids)
                                qualified_object = None
                                if nominal_answer is None and len(clause.move_ids) == 1 and len(about) == 1:
                                    event_source = final_reception_source_anchor_text(
                                        about[0].from_nucleus_id, nucleus_index, resolver)
                                    qualified_object = ((event_source + "ことについて、").encode() + phrase
                                                        if event_source and phrase else b"")
                                raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end]
                                start = parsed_sentence.utf8_byte_start + raw.find(phrase)
                                end = start + len(phrase)
                                if (not phrase or raw.count(phrase) != 1
                                    or nominal_answer is not None and not raw.startswith(phrase)
                                    or qualified_object is not None and (not qualified_object
                                        or not raw.startswith(qualified_object))
                                    or any(q.section == "reception" and q.utf8_byte_start < end
                                           and start < q.utf8_byte_end for q in witness.quotes)
                                    or any(m.section == "reception" and m.marker_code == "secondary_quote_boundary"
                                           and m.utf8_byte_start < end and start < m.utf8_byte_end
                                           for m in witness.markers)):
                                    failures.append(f"body_inverse_positive_answer_source_time_missing:{move_id}")
                        else:
                            target_markers = (
                                _BODY_INVERSE_RECEPTION_ACT_TARGET_MARKERS.get(
                                    move.reception_act,
                                    frozenset(),
                                )
                            )
                        effective_reference_mode = (
                            reception_effective_move_reference_mode(
                                reception_plan,
                                move,
                                sentence_plan.recovery_stage,
                            )
                        )
                        expected_referent = expected_referent_by_move.get(
                            move.move_id
                        )
                        expected_referent_text = (
                            _body_inverse_normalized_anchor(
                                expected_referent.text
                            )
                            if expected_referent is not None
                            else ""
                        )
                        nominal_target_visible = False
                        cognition_nominal_range: tuple[int, int] | None = None
                        future_nominal_required = bool(
                            final_stage1_plan
                            and effective_reference_mode != "anaphoric_first"
                            and expected_referent is not None
                            and expected_referent.kind == "future_action_intention"
                            and expected_referent.text == source_grounded_future_action_nominal(
                                move, nucleus_index, resolver,
                            )
                        )
                        burden_nominal_required = bool(
                            final_stage1_plan
                            and effective_reference_mode == "anaphoric_first"
                            and expected_referent is not None
                            and expected_referent.kind == "current_expression"
                            and expected_referent.text == (source_grounded_feeling_target_nominal(
                                move, plan, nucleus_index, resolver,
                            ) or source_grounded_unfinished_referent(
                                move, plan, nucleus_index, resolver,
                            ))
                        )
                        wish_nominal_required = bool(
                            final_stage1_plan
                            and effective_reference_mode != "anaphoric_first"
                            and expected_referent is not None
                            and expected_referent.kind == "retained_wish"
                            and expected_referent.text == source_grounded_retained_wish_nominal(
                                move, plan, nucleus_index, resolver,
                            )
                        )
                        expression_nominal_required = bool(
                            final_stage1_plan
                            and effective_reference_mode != "anaphoric_first"
                            and expected_referent is not None
                            and expected_referent.kind == "current_expression"
                            and expected_referent.text == source_grounded_current_expression_nominal(
                                move, plan, nucleus_index, resolver,
                            )
                        )
                        expression_words_nominal_required = bool(
                            expression_nominal_required
                            and expected_referent.text.endswith("という言葉")
                        )
                        thread_answer_nominal = (
                            source_grounded_thread_answer_nominal(move, plan, nucleus_index, resolver)
                            if expression_nominal_required else None
                        )
                        nominal_target_required = bool(
                            final_stage1_plan
                            and effective_reference_mode != "anaphoric_first"
                            and expected_referent is not None
                            and expected_referent.kind == "self_started_effort"
                            and expected_referent.text == source_grounded_performed_action_nominal(
                                move, nucleus_index, resolver,
                            )
                        ) or burden_nominal_required or future_nominal_required or wish_nominal_required or expression_nominal_required
                        if nominal_target_required:
                            # Bind a body-only grammatical suffix to the end
                            # of this independently resolved *whole* referent.
                            # Normalized anchor offsets cannot address bytes.
                            nominal_bytes = expected_referent.text.encode("utf-8")
                            raw_sentence = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end]
                            offset = raw_sentence.find(nominal_bytes)
                            if offset >= 0 and raw_sentence.count(nominal_bytes) == 1:
                                start = parsed_sentence.utf8_byte_start + offset
                                end = start + len(nominal_bytes)
                                nominal_target_visible = any(
                                    marker.section == "reception"
                                    and marker.marker_kind == ("reception" if expression_words_nominal_required else "semantic")
                                    and marker.marker_code == (
                                        "target_words" if expression_words_nominal_required else
                                        "thread_answer_nominal" if thread_answer_nominal is not None else
                                        ("negative_carrier_nominal"
                                         if expected_referent.text.endswith("なさ")
                                         else "adnominal_subject") if burden_nominal_required
                                        and expected_referent.text == source_grounded_feeling_target_nominal(
                                            move, plan, nucleus_index, resolver,
                                        )
                                        else "finite_clause_nominal"
                                    )
                                    and start <= marker.utf8_byte_start
                                    and marker.utf8_byte_end == end
                                    for marker in witness.markers
                                )
                                if (burden_nominal_required or future_nominal_required or wish_nominal_required or expression_nominal_required) and (
                                    any(q.section == "reception" and q.utf8_byte_start < end
                                        and start < q.utf8_byte_end for q in witness.quotes)
                                    or any(m.section == "reception" and m.marker_code == "secondary_quote_boundary"
                                           and m.utf8_byte_start < end and start < m.utf8_byte_end
                                           for m in witness.markers)
                                ):
                                    nominal_target_visible = False
                                # A performed action with its coowned change
                                # starts this source-bound relational object.
                                # A matching substring inside a newly prefixed
                                # actor or time does not prove the same object.
                                from emlis_ai_grounded_observation_plan import _source_action_change_contrast
                                action_contrast = _source_action_change_contrast(plan.nuclei, plan.relations)
                                if (action_contrast and move.reception_act == "honor_concrete_effort"
                                    and move.target_nucleus_ids == (action_contrast[0],)
                                    and move.support_nucleus_ids == (action_contrast[1],)
                                    and nucleus_index[action_contrast[0]].semantic_frame.time_scope == "past"):
                                    nominal_target_visible = nominal_target_visible and offset == 0
                                # A separately selected performed action owns the
                                # whole object in attention and felt-response
                                # clauses alike. A new actor/time prefix cannot
                                # borrow the original action as a substring.
                                if (len(clause.move_ids) == 1
                                    and move.reception_act == "honor_concrete_effort"
                                    and len(move.target_nucleus_ids) == 1 and not move.support_nucleus_ids
                                    and expected_referent.kind == "self_started_effort"
                                    and not _body_inverse_reception_context_ids(move, plan)):
                                    # The response act must itself be affirmative.
                                    # A source-internal or earlier positive marker
                                    # cannot discharge a negated final predicate.
                                    response_tail = raw_sentence[len(nominal_bytes):].decode("utf-8")
                                    affirmative_act = re.search(
                                        r"大切に(?:(?:思って|気にかけて|受け止めて)(?:います|いて)|"
                                        r"(?:思い|気にかけ|受け止め)たいです)。\Z", response_tail)
                                    nominal_target_visible = bool(
                                        nominal_target_visible and offset == 0 and affirmative_act)
                                if thread_answer_nominal is not None:
                                    _, source, grammar, when, nominal = thread_answer_nominal
                                    actual_nominal = body[start:end].decode("utf-8")
                                    nominal_target_visible = bool(
                                        nominal_target_visible and actual_nominal == nominal
                                        and restore_thread_answer_nominal(actual_nominal, grammar, when) == source
                                    )
                                # Independently restore a finite cognition from
                                # its body-only こと object. A generic referent,
                                # a quotation, or a source replay elsewhere in
                                # this sentence cannot satisfy this obligation.
                                if ((burden_nominal_required or expression_nominal_required) and nominal_target_visible
                                    and move.move_role == "felt_response"
                                    and len(move.target_nucleus_ids) == 1 and not move.support_nucleus_ids):
                                    cognition = nucleus_index[move.target_nucleus_ids[0]]
                                    cf = cognition.semantic_frame
                                    codes = set(cf.attribute_codes)
                                    independent_cognition = len(reception_plan.moves) == 1 or (
                                        len(reception_plan.moves) == 2
                                        and "lexical:source_bounded_expression" in codes
                                        and cognition.source_fields == ("memo",)
                                        and all(
                                            other.required and other.reception_act == "honor_concrete_effort"
                                            and len(other.target_nucleus_ids) == 1 and not other.support_nucleus_ids
                                            and (action := nucleus_index.get(other.target_nucleus_ids[0])) is not None
                                            and action.nucleus_id != cognition.nucleus_id
                                            and action.source_fields == ("memo_action",) and action.retention == "required"
                                            and not set(action.source_span_ids).intersection(cognition.source_span_ids)
                                            and action.semantic_frame.actor == "current_user"
                                            and action.kind == "action"
                                            and action.semantic_frame.modality == "fact"
                                            and action.semantic_frame.time_scope in {"past", "continuing", "present", "completed"}
                                            and "operator:performed_action" in action.semantic_frame.attribute_codes
                                            for other in reception_plan.moves if other != move
                                        )
                                        and not any(
                                            (r.retention == "required" or r.type != "uncertain_connection")
                                            and cognition.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id)
                                            for r in plan.relations
                                        )
                                    )
                                    if (cognition.kind == cf.predicate_kind == "uncertainty"
                                        and independent_cognition
                                        and cf.actor == "current_user" and cf.modality == "uncertain"
                                        and cf.polarity == "negative" and cf.time_scope in {"present", "current_input"}
                                        and cognition.grounding_kind == "explicit" and cognition.retention == "required"
                                        and cognition.source_fields in {("memo",), ("memo_action",)}
                                        and len(cognition.source_span_ids) == 1
                                        and {"operator:uncertainty", "operator:negation", "semantic_role:limiting_unknown",
                                             "lexical:preserve_source_predicate", "lexical:no_new_sensation_family"} <= codes
                                        and not any(code.startswith(("source_fragment_", "surface_scalar_", "thread_time:"))
                                                    or code == "semantic_role:embedded_turn" for code in codes)):
                                        source_span = resolver.resolve(cognition.source_span_ids[0])
                                        source_clause = str(source_span.raw_text).strip(" \u3000。．.")
                                        if (source_span.source_field == cognition.source_fields[0]
                                            and 0 <= source_span.start_index < source_span.end_index
                                            and re.fullmatch(r"(?:(?:現在|今)(?:も|は))?(?:まだ)?(?:はっきり|よく)?(?:わからない|分からない)", source_clause)):
                                            actual_nominal = body[start:end].decode("utf-8")
                                            # Read the whole object slot, not
                                            # an expected substring inside an
                                            # added まだ/subject/time modifier.
                                            decision = next((d for d in selected_subjective_input.decisions
                                                if d.move_id == move.move_id), None) if selected_subjective_input else None
                                            proposition = decision.subjective_proposition if decision else None
                                            open_required = bool(
                                                proposition is None and len(reception_plan.moves) == 1
                                                or proposition is not None and (
                                                    proposition.appraisal_content is not None
                                                    and proposition.appraisal_content.operation == "LEAVE_UNFINISHED"
                                                    or proposition.relational_position is not None
                                                    and proposition.relational_position.stance_operator == "HOLD_UNFINISHED_OPEN"
                                                )
                                            )
                                            received = re.fullmatch(
                                                (r"結論を急がずに、" if open_required else "")
                                                + r"(?P<source>[^。！？!?]+)こと"
                                                r"を小さくせずに(?:"
                                                r"(?:受け止めて|気にかけて)(?:います|いて)|"
                                                r"(?:受け止め|気にかけ)たいです)。",
                                                raw_sentence.decode("utf-8"),
                                            )
                                            if (received is not None and received.group("source") == source_clause
                                                and actual_nominal.endswith("こと") and actual_nominal[:-2] == source_clause):
                                                cognition_nominal_range = (start, end)
                                            else:
                                                nominal_target_visible = False
                            from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
                            retained_group = bool(move.support_nucleus_ids) and (
                                "current_burden", move.target_nucleus_ids, move.support_nucleus_ids) in (
                                    _thread_retained_reaction_groups(plan.nuclei, plan.relations))
                            from emlis_ai_grounded_observation_plan import _source_action_change_contrast_unfinished
                            if (expression_nominal_required and move.target_nucleus_ids
                                == _source_action_change_contrast_unfinished(plan.nuclei, plan.relations)):
                                nominal_target_visible = nominal_target_visible and _body_inverse_unfinished_result_clause(
                                    body, parsed_sentence, move, plan, resolver)
                            if expression_nominal_required and retained_group:
                                nominal_target_visible = _body_inverse_thread_received_group(
                                    body, witness, parsed_sentence, move, plan, resolver) is not None
                            elif (expression_words_nominal_required and len(clause.move_ids) == 1
                                and move.move_role == "felt_response"
                                and move.reception_act == "stay_with_current_burden"
                                and len(move.target_nucleus_ids) == 1 and not move.support_nucleus_ids
                                and nucleus_index[move.target_nucleus_ids[0]].semantic_frame.time_scope
                                    in {"present", "current_input"}
                                and not _body_inverse_reception_context_ids(move, plan)
                                and len(nucleus_index[move.target_nucleus_ids[0]].source_span_ids) == 1
                                and expected_referent.text == str(resolver.resolve(
                                    nucleus_index[move.target_nucleus_ids[0]].source_span_ids[0]).raw_text)
                                    .strip(" \u3000、,。．.") + "という言葉"):
                                # Read the entire selected object, not a source
                                # substring inside an added actor, time or cause.
                                nominal_target_visible = nominal_target_visible and _body_inverse_nominal_constraint_clause(
                                    body, parsed_sentence, move, plan, resolver, selected_subjective_input)
                            elif expression_nominal_required and any(
                                {"lexical:source_nominal_constraint_clause", "lexical:source_provisional_degree"}
                                & set(nucleus_index[nid].semantic_frame.attribute_codes)
                                for nid in move.target_nucleus_ids):
                                nominal_target_visible = nominal_target_visible and _body_inverse_nominal_constraint_clause(
                                    body, parsed_sentence, move, plan, resolver, selected_subjective_input)
                            elif expression_nominal_required and any(
                                {"lexical:source_feeling_reason_subject", "lexical:source_current_material_primary", "lexical:source_current_material_qualification",
                                 "lexical:source_temporal_relief_residue", "lexical:source_temporal_causal_unknown",
                                 "lexical:source_independent_decision_choice", "lexical:source_independent_decision_timing"}
                                & set(nucleus_index[nid].semantic_frame.attribute_codes)
                                for nid in move.target_nucleus_ids):
                                nominal_target_visible = nominal_target_visible and _body_inverse_current_material_group(
                                    body, witness, parsed_sentence, move, plan, resolver, selected_subjective_input)
                            elif expression_nominal_required and len(move.target_nucleus_ids) > 1:
                                nominal_target_visible = (
                                    _body_inverse_received_contrast_group(body, witness, parsed_sentence, move, plan, resolver)
                                    if move.support_nucleus_ids else bool(_body_inverse_thread_answer_group(
                                        body, witness, parsed_sentence, move, plan, resolver)))
                        # The selected independent two-object path owes the
                        # complete material and action clauses. A familiar
                        # suffix alone cannot authorize another actor or time.
                        from emlis_ai_grounded_observation_plan import _is_independent_source_material
                        independent_pair = bool(
                            final_stage1_plan and len(reception_plan.moves) == 2
                            and effective_reference_mode != "anaphoric_first"
                            and len(clause.move_ids) == 1
                            and {m.reception_act for m in reception_plan.moves}
                                == {"stay_with_current_burden", "honor_concrete_effort"}
                            and all(m.required and m.move_role == "felt_response"
                                    and len(m.target_nucleus_ids) == 1 and not m.support_nucleus_ids
                                    and not _body_inverse_reception_context_ids(m, plan)
                                    for m in reception_plan.moves)
                            and any(_is_independent_source_material(nucleus_index[m.target_nucleus_ids[0]],
                                        safety_kind=plan.input_profile.safety_kind)
                                    for m in reception_plan.moves if m.reception_act == "stay_with_current_burden")
                        )
                        if independent_pair:
                            owner = nucleus_index[move.target_nucleus_ids[0]]
                            source = (str(resolver.resolve(owner.source_span_ids[0]).raw_text)
                                      .strip(" \u3000、,。．.")) if len(owner.source_span_ids) == 1 else ""
                            raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
                            complete_object = False
                            if move.reception_act == "stay_with_current_burden":
                                for nominal in ("こと", "という言葉"):
                                    if expected_referent is not None and expected_referent.text == source + nominal:
                                        # A source-owned time adjunct may be outside
                                        # the complete quoted/nominal object. Preserve
                                        # the existing present/continuing/past forms;
                                        # another actor, time or cause is not licensed.
                                        prefix = {"present": "今、", "continuing": "今も、",
                                                  "past": "これまで、"}.get(owner.semantic_frame.time_scope, "")
                                        prefixes = ("", prefix) if prefix else ("",)
                                        complete_object = any(_body_inverse_nominal_constraint_clause(
                                            body, parsed_sentence, move, plan, resolver, selected_subjective_input,
                                            nominal=nominal, temporal_prefix=prefix) for prefix in prefixes)
                            elif owner.source_fields == ("memo_action",) and owner.semantic_frame.actor == "current_user":
                                nominal = ("というこれからの行動" if _body_inverse_action_is_future_intention(owner)
                                           else "こと" if _body_inverse_action_is_performed(owner) else None)
                                if source and nominal:
                                    parsed = re.fullmatch(r"(?P<source>[^。！？!?]+)" + re.escape(nominal)
                                        + r"を(?:大切に思って(?:います|いて)|大切に思いたいです)。", raw)
                                    complete_object = parsed is not None and parsed.group("source") == source
                            if not complete_object:
                                failures.append(f"body_inverse_independent_material_action_object_missing:{move_id}")
                        adjacent_context_matched = bool(
                            final_stage1_plan and sentence_plan.recovery_stage == "full"
                            and effective_reference_mode == "anaphoric_first" and clause_index > 0
                            and _body_inverse_adjacent_action_context(
                                body, parsed_sentence, parsed_sentences[clause_index - 1],
                                clause, clause_plans[clause_index - 1], move,
                                reception_plan, plan, resolver,
                            )
                        )
                        target_visible = (
                            nominal_target_visible if nominal_target_required
                            else bool(sentence_codes.intersection(target_markers))
                        )
                        if expected_referent_text == "その行動":
                            # This reference is admitted only with its actual
                            # antecedent, never by a generic action marker.
                            target_visible = adjacent_context_matched

                        if (final_stage1_plan and sentence_plan.recovery_stage == "full"
                            and len(clause.move_ids) == 2
                            and move.reception_act == "recognize_lived_change"
                            and target_markers == frozenset({"target_feeling"})):
                            # A shared sentence's other feeling marker cannot
                            # discharge this move's own complete feeling object.
                            # Keep the existing per-duty diagnostic as well as
                            # the independent whole shared-clause proof.
                            owned_source = (final_reception_source_anchor_text(
                                move.target_nucleus_ids[0], nucleus_index, resolver,
                            ) if len(move.target_nucleus_ids) == 1 else "")
                            owned_object = _body_inverse_normalized_anchor(
                                owned_source + "という気持ち"
                            ) if owned_source else ""
                            target_visible = target_visible and bool(
                                owned_object and owned_object in parsed_sentence_text
                            )
                        if target_markers and not target_visible:
                            failures.append(
                                "body_inverse_reception_target_duty_missing:"
                                f"{move.move_id}"
                            )
                        if (
                            not expected_referent_text
                            or expected_referent_text
                            not in parsed_sentence_text
                        ):
                            failures.append(
                                "body_inverse_reception_target_referent_missing:"
                                f"{move.move_id}"
                            )
                        target_values = tuple(
                            source_value
                            for nucleus_id in move.target_nucleus_ids
                            for source_value in (
                                _body_inverse_nucleus_source_values(
                                    nucleus_id,
                                    plan,
                                    resolver,
                                )
                            )
                        )
                        if (final_stage1_plan and sentence_plan.recovery_stage == "full"
                            and len(clause.move_ids) == 1 and len(target_nuclei) == 1
                            and move.reception_act == "recognize_lived_change"
                            and is_grounded_positive_feeling(target_nuclei[0])
                            and {"lexical:source_nominal_cognition_feeling", "lexical:source_received_past_feeling", "lexical:source_nominal_past_feeling"}
                                & set(target_nuclei[0].semantic_frame.attribute_codes)):
                            # The positive main feeling governs this whole
                            # nominal cognition. Its negative background and
                            # potential content cannot be left only in Layer 1
                            # or reassigned to a foreign owner or a change.
                            source = final_reception_source_anchor_text(
                                target_nuclei[0].nucleus_id, nucleus_index, resolver)
                            raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
                            role = {"attention": "を見過ごさず、", "felt_response": "を"}.get(move.move_role)
                            expected = source + "という気持ち" + (role or "") + "受け止めています。"
                            complete_forms = (expected,)
                            contexts = _body_inverse_reception_context_ids(move, plan)
                            contrast = tuple(r for r in plan.relations
                                if r.type == "contrast" and r.retention == "required"
                                and r.to_nucleus_id == target_nuclei[0].nucleus_id
                                and contexts == (r.from_nucleus_id,))
                            context_valid = not contexts and not move.support_nucleus_ids
                            if (len(contrast) == 1 and len(contexts) == 1
                                and nucleus_index[contexts[0]].kind == "event"
                                and "lexical:source_nominal_past_feeling"
                                    in target_nuclei[0].semantic_frame.attribute_codes):
                                before = final_reception_source_anchor_text(contexts[0], nucleus_index, resolver)
                                context_valid = bool(before and (not move.support_nucleus_ids
                                    or move.support_nucleus_ids == contexts))
                                expected = before + "ことと" + source + "という気持ち" + (role or "") + "その違いも含めて受け止めています。"
                                complete_forms = (expected, before + "ことと" + source
                                    + "という気持ちとの違い" + (role or "") + "受け止めています。")
                                # Independently check the finite background,
                                # its contrast connector, the complete past
                                # feeling and the selected reception role.
                                # Do not ask the author to certify its prose.
                                left = nucleus_index[contexts[0]]
                                right = target_nuclei[0]
                                if (right.semantic_frame.time_scope == "past"
                                    and right.semantic_frame.polarity == "positive"
                                    and all(str(n.semantic_frame.actor).lower() in {"current_user", "user", "self"}
                                            and not _body_inverse_action_is_performed(n)
                                            and not _body_inverse_action_is_future_intention(n)
                                            for n in (left, right))
                                    and left.semantic_frame.modality == "fact"
                                    and not any(code.startswith("aspect:") and code.split(":", 1)[1]
                                                not in {"unknown", "not_applicable"}
                                                for code in right.semantic_frame.attribute_codes)
                                    and re.search(r"(?:かった|[てで]いた|た|だ)$", before)
                                    and not re.search(r"[「」『』“”‘’\"?？!！。;；…‥]", before + source)):
                                    complete_forms += (before + "けれど、" + source
                                        + "という気持ち" + (role or "") + "受け止めています。",)
                            if (not source or role is None or not context_valid
                                or effective_reference_mode == "anaphoric_first" or raw not in complete_forms):
                                failures.append(f"body_inverse_nominal_cognition_feeling_object_missing:{move_id}")
                        if (
                            effective_reference_mode == "anaphoric_first"
                            and any(source_value in (
                                _body_inverse_normalized_anchor((
                                    body[parsed_sentence.utf8_byte_start:cognition_nominal_range[0]]
                                    + body[cognition_nominal_range[1]:parsed_sentence.utf8_byte_end]
                                ).decode("utf-8"))
                                if cognition_nominal_range is not None else parsed_sentence_text
                            ) for source_value in target_values)
                        ):
                            failures.append(
                                "body_inverse_reception_anaphoric_target_replayed:"
                                f"{move.move_id}"
                            )
                        relation_attention_valid = True
                        shared_change_context_matched = False
                        if (final_stage1_plan and sentence_plan.recovery_stage == "full"
                            and len(clause.move_ids) == 1 and move.move_role == "attention"
                            and effective_reference_mode != "anaphoric_first"
                            and selected_subjective_input is not None):
                            decision = next((d for d in selected_subjective_input.decisions
                                             if d.move_id == move.move_id), None)
                            appraisal = decision.subjective_proposition.appraisal_content if decision else None
                            object_ids = set(move.target_nucleus_ids) | set(
                                _body_inverse_reception_context_ids(move, plan))
                            object_relations = [r for r in plan.relations
                                if {r.from_nucleus_id, r.to_nucleus_id} == object_ids]
                            if (appraisal is not None and appraisal.dimension == "MATERIAL_WEIGHT"
                                and appraisal.operation == "RECEIVE_AS_MATERIAL"
                                and move.reception_act == "stay_with_current_burden"
                                and len(move.target_nucleus_ids) == 1 and not move.support_nucleus_ids
                                and len(object_ids) == 1
                                and expected_referent is not None
                                and expected_referent.kind == "current_expression"
                                and expected_referent.text.endswith("という言葉")
                                and nucleus_index[move.target_nucleus_ids[0]].semantic_frame.actor == "current_user"):
                                # Read the whole independently resolved source
                                # object and the affirmative attention/reception
                                # clause. Source-internal markers, an inserted
                                # actor/time, or a negated act cannot discharge it.
                                raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
                                # Preserve the existing typed polite-past
                                # adjunct outside the complete source object.
                                # This correction does not change temporal
                                # realization or permit arbitrary added time.
                                frame = nucleus_index[move.target_nucleus_ids[0]].semantic_frame
                                source_text = expected_referent.text[:-len("という言葉")]
                                time_marker = {"past": "これまで", "completed": "すでに"}.get(frame.time_scope)
                                prefix = (time_marker + "、" if time_marker
                                    and source_text.endswith("かったです")
                                    and time_marker not in source_text else "")
                                relation_attention_valid = re.fullmatch(
                                    re.escape(prefix + expected_referent.text)
                                    + r"(?:を見過ごさず、|に目が留まり、それを)"
                                    + r"小さくせずに受け止めています。", raw) is not None
                            change_context_ids = _body_inverse_reception_context_ids(move, plan)
                            change_context_prefix = None
                            # Only required/selected relations belong to this Move.
                            # A retained SHOULD source-order relation is not an
                            # authored causal relation or a second target object.
                            required_object_relations = [r for r in object_relations
                                if r.relation_id in plan.coverage_requirements.required_relation_ids]
                            if (len(change_context_ids) == 1 and len(object_ids) == 2
                                and not required_object_relations):
                                context_nucleus = nucleus_index[change_context_ids[0]]
                                context_frame = context_nucleus.semantic_frame
                                context_source = final_reception_source_anchor_text(
                                    context_nucleus.nucleus_id, nucleus_index, resolver)
                                if (context_nucleus.kind == "action"
                                    and context_frame.actor == "current_user"
                                    and context_frame.predicate_kind == "action"
                                    and context_frame.modality == "fact"
                                    and "operator:performed_action" in context_frame.attribute_codes
                                    and context_source and context_source.endswith("た")):
                                    change_context_prefix = context_source + "ことを背景に、"
                            if (appraisal is not None and appraisal.dimension == "MATERIAL_WEIGHT"
                                and appraisal.operation == "RECEIVE_AS_MATERIAL"
                                and move.reception_act == "recognize_lived_change"
                                and len(move.target_nucleus_ids) == 1
                                and (len(object_ids) == 1 and not move.support_nucleus_ids
                                     or change_context_prefix is not None)
                                and expected_referent is not None and expected_referent.kind == "lived_change"
                                and target_nuclei[0].kind == "reaction"
                                and target_nuclei[0].semantic_frame.actor == "current_user"
                                and target_nuclei[0].semantic_frame.predicate_kind == "feeling"
                                and target_nuclei[0].semantic_frame.modality == "feeling"):
                                # A personally felt change remains subjective.
                                # Resolve the whole original object independently:
                                # mere source words elsewhere, a changed speaker,
                                # time/cause insertion, or negated reception cannot
                                # stand for this affirmative attention clause.
                                source = final_reception_source_anchor_text(
                                    target_nuclei[0].nucleus_id, nucleus_index, resolver)
                                raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
                                relation_attention_valid = bool(source and raw == (
                                    (change_context_prefix or "") + source + "という" + expected_referent.text
                                    + "を見過ごさず、受け止めています。"))
                            if (appraisal is not None and appraisal.dimension == "MATERIAL_WEIGHT"
                                and appraisal.operation == "RECEIVE_AS_MATERIAL"
                                and move.reception_act == "recognize_lived_change"
                                and len(move.target_nucleus_ids) == len(object_ids) == 1
                                and not move.support_nucleus_ids and not change_context_ids
                                and not required_object_relations
                                and effective_reference_mode != "anaphoric_first"
                                and expected_referent is not None and expected_referent.kind == "lived_change"
                                and target_nuclei[0].kind == "change"
                                and target_nuclei[0].semantic_frame.actor == "current_user"
                                and (target_nuclei[0].semantic_frame.predicate_kind,
                                     target_nuclei[0].semantic_frame.modality) in {
                                         ("change", "fact"), ("feeling", "feeling")}):
                                # The sole change object has no admitted background.
                                # Read its complete source and grammatical boundary;
                                # source containment under an invented prefix is not
                                # evidence that this is the same received meaning.
                                source = final_reception_source_anchor_text(
                                    target_nuclei[0].nucleus_id, nucleus_index, resolver)
                                raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
                                relation_attention_valid = bool(source and re.fullmatch(
                                    re.escape(source + "という" + expected_referent.text)
                                    + r"(?:を見過ごさず、|に目が留まり、それを)受け止めています。", raw))
                            if (appraisal is not None and appraisal.dimension == "MATERIAL_WEIGHT"
                                and appraisal.operation == "RECEIVE_AS_MATERIAL"
                                and len(object_ids) == 2 and len(object_relations) == 1):
                                relation_kind = object_relations[0].type
                                boundary = {
                                    ("action_supports_change", "honor_concrete_effort"):
                                        ("支えていること", "大切に思っています"),
                                    ("contrast", "stay_with_current_burden"):
                                        ("との違い", "小さくせずに受け止めています"),
                                }.get((relation_kind, move.reception_act))
                                if boundary is not None:
                                    # Parse the completed object's case and
                                    # affirmative attention/act independently
                                    # of author replay. A source-internal word
                                    # such as 見過ごして cannot stand for this duty.
                                    nominal_end, act = boundary
                                    raw = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end].decode("utf-8")
                                    relation_attention_valid = re.fullmatch(
                                        r"[^。！？!?]+" + re.escape(nominal_end)
                                        + r"(?:を見過ごさず、|に目が留まり、それを)"
                                        + re.escape(act) + "。", raw) is not None
                                    if relation_kind == "action_supports_change":
                                        relation_attention_valid = relation_attention_valid or _body_inverse_attributive_support_attention(
                                            raw, object_relations[0], move, plan, resolver)
                                    if relation_kind == "contrast" and "一方で、" in raw:
                                        prior_proven = bool(raw.startswith("その一方で、") and clause_index > 0
                                            and _body_inverse_preceding_change_context(
                                                body, parsed_sentences[clause_index - 1], clause_plans[clause_index - 1],
                                                parsed_sentence, move, reception_plan, plan, resolver))
                                        relation_attention_valid = _body_inverse_finite_contrast_attention(
                                            raw, object_relations[0], move, plan, resolver,
                                            expected_referent.text if expected_referent is not None else "",
                                            preceding_change_proven=prior_proven)
                                        shared_change_context_matched = prior_proven and relation_attention_valid
                        if (
                            move.move_role == "attention"
                            and ("attention" not in sentence_codes or not relation_attention_valid)
                        ):
                            failures.append(
                                "body_inverse_reception_attention_duty_missing:"
                                f"{move.move_id}"
                            )

                        importance_codes = {
                            "stay_with_current_burden": {"receive"},
                            "honor_concrete_effort": {
                                "receive",
                                "felt_response",
                            },
                            "protect_retained_intention": {
                                "receive",
                                "felt_response",
                            },
                            "recognize_lived_change": {
                                "receive",
                                "felt_response",
                            },
                            "hold_help_seeking": {
                                "receive",
                                "felt_response",
                            },
                            "bounded_counter_self_denial": {"protect"},
                            "respect_words_placed": {
                                "receive",
                                "felt_response",
                            },
                        }.get(move.reception_act, set())
                        importance_missing = bool(
                            importance_codes
                            and not sentence_codes.intersection(
                                importance_codes
                            )
                        )
                        if (
                            move.reception_act
                            == "protect_retained_intention"
                            and "protect" not in sentence_codes
                        ):
                            importance_missing = True

                        context_ids = _body_inverse_reception_context_ids(
                            move,
                            plan,
                        )
                        context_values = tuple(
                            source_value
                            for nucleus_id in context_ids
                            for source_value in (
                                _body_inverse_nucleus_source_values(
                                    nucleus_id,
                                    plan,
                                    resolver,
                                )
                            )
                        )
                        anaphoric_context = bool(
                            context_values
                            and effective_reference_mode
                            == "anaphoric_first"
                        )
                        context_match_text = parsed_sentence_text
                        context_morphology_missing = False
                        decision_context_matched = bool(
                            final_stage1_plan and not anaphoric_context
                            and len(context_ids) == 1
                            and any({"lexical:source_independent_decision_choice",
                                     "lexical:source_independent_decision_timing"}
                                    & set(nucleus_index[nid].semantic_frame.attribute_codes)
                                    for nid in move.target_nucleus_ids)
                            and _body_inverse_current_material_group(
                                body, witness, parsed_sentence, move, plan, resolver, selected_subjective_input)
                        )
                        context_nominal = None
                        if final_stage1_plan and not anaphoric_context:
                            try:
                                context_nominal = source_grounded_negative_context_nominal(
                                    move, plan, nucleus_index, resolver,
                                )
                            except GroundedHumanReceptionSurfaceError:
                                context_morphology_missing = True
                        if context_nominal is not None:
                            context_id, source_fragment, nominal = context_nominal
                            raw_sentence = body[parsed_sentence.utf8_byte_start:parsed_sentence.utf8_byte_end]
                            nominal_bytes = nominal.encode("utf-8")
                            offset = raw_sentence.find(nominal_bytes)
                            start = parsed_sentence.utf8_byte_start + max(offset, 0)
                            end = start + len(nominal_bytes)
                            # This branch requires the independently derived
                            # whole nominal exactly once. It cannot fall back
                            # to the old category phrase or a shortened stem.
                            context_morphology_missing = bool(
                                context_ids != (context_id,)
                                or offset < 0 or raw_sentence.count(nominal_bytes) != 1
                                or any(q.utf8_byte_start < end and start < q.utf8_byte_end
                                       for q in witness.quotes)
                                or any(m.section == "reception" and m.marker_kind == "semantic"
                                       and m.marker_code == "secondary_quote_boundary"
                                       and m.utf8_byte_start < end and start < m.utf8_byte_end
                                       for m in witness.markers)
                                or not nominal.endswith("ないこと")
                                or nominal[:-4] + "なくて" != source_fragment
                                or _body_inverse_normalized_anchor(source_fragment)
                                not in context_values
                            )
                            if not context_morphology_missing:
                                # Restore only this witnessed grammatical
                                # span for the original full-source check.
                                # The actual body/witness and exact replay
                                # comparison remain untouched.
                                restored = (raw_sentence[:offset]
                                            + (nominal[:-4] + "なくて").encode("utf-8")
                                            + raw_sentence[offset + len(nominal_bytes):])
                                context_match_text = _body_inverse_normalized_anchor(
                                    restored.decode("utf-8", errors="strict"))
                        context_missing = bool(
                            context_morphology_missing or context_values
                            and (
                                (
                                    anaphoric_context
                                    and not adjacent_context_matched
                                    and not any(
                                        marker in parsed_sentence_text
                                        for marker in ("中で", "中にも", "背景")
                                    )
                                )
                                or (
                                    not anaphoric_context
                                    and not decision_context_matched
                                    and not shared_change_context_matched
                                    and not any(
                                        source_value in context_match_text
                                        for source_value in context_values
                                    )
                                )
                            )
                        )
                        if anaphoric_context and any(
                            source_value in parsed_sentence_text
                            for source_value in context_values
                        ):
                            failures.append(
                                "body_inverse_reception_anaphoric_context_replayed:"
                                f"{move.move_id}"
                            )
                        if context_missing:
                            failures.append(
                                "body_inverse_reception_context_anchor_missing:"
                                f"{move.move_id}"
                            )
                        if importance_missing or context_missing:
                            failures.append(
                                "body_inverse_reception_why_duty_missing:"
                                f"{move.move_id}"
                            )

    failure_codes = _dedupe(failures)
    return GroundedBodyInverseEvaluation(
        passed=not failure_codes,
        body_sha256=witness.body_sha256,
        observation_line_count=len(observation_lines),
        reception_line_count=len(reception_lines),
        observation_sentence_count=witness.observation_sentence_count,
        reception_sentence_count=witness.reception_sentence_count,
        source_anchor_count=len(witness.quotes),
        relation_marker_count=sum(
            row.marker_kind == "relation" for row in witness.markers
        ),
        uncertainty_marker_count=sum(
            row.marker_kind == "uncertainty" for row in witness.markers
        ),
        reception_marker_count=sum(
            row.marker_kind == "reception" for row in witness.markers
        ),
        failure_codes=failure_codes,
    )


def _grounded_surface_body_projection_matches(
    surface_result: GroundedSurfaceResult,
) -> bool:
    observation = "\n".join(
        line.text
        for line in surface_result.lines
        if line.binding.line_role != "human_follow"
    ).strip()
    reception = "\n".join(
        line.text
        for line in surface_result.lines
        if line.binding.line_role == "human_follow"
    ).strip()
    expected = (
        f"{OBSERVATION_SECTION_LABEL}\n{observation}\n\n"
        f"{RECEPTION_SECTION_LABEL}\n{reception}"
    ).strip()
    return surface_result.text.encode("utf-8") == expected.encode("utf-8")


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
    require_body_inverse: bool = False,
    selected_subjective_input: SelectedSubjectiveReceptionInputV1 | None = None,
) -> GroundedObservationGateReport:
    """Evaluate I5 plan/coverage/evidence/template/depth gates.

    Product Read Feel is an external human result.  A delivery pass therefore
    remains ``not_evaluated`` unless an explicit human result is supplied.
    The stronger body-only inverse is opt-in so the existing production I5
    route remains byte-for-byte and decision-for-decision unchanged; the CMEE
    candidate path enables it explicitly before selection.
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
            selected_subjective_input=selected_subjective_input,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        surface_issues = ("grounded_surface_validation_contract_invalid",)
    body_inverse_reasons: tuple[str, ...] = ()
    if require_body_inverse and surface_result.status == "generated":
        try:
            body_inverse = evaluate_grounded_surface_body_inverse(
                body=surface_result.text.encode("utf-8"),
                plan=plan,
                sentence_plan=sentence_plan,
                resolver=resolver,
                selected_subjective_input=selected_subjective_input,
            )
        except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
            body_inverse_reasons = ("body_inverse_evaluation_contract_invalid",)
        else:
            body_inverse_reasons = body_inverse.failure_codes
        if not _grounded_surface_body_projection_matches(surface_result):
            body_inverse_reasons = _dedupe(
                (*body_inverse_reasons, "body_inverse_surface_projection_mismatch")
            )
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
        selected_subjective_input=selected_subjective_input,
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
    ) and not semantic_subcheck_reasons and not body_inverse_reasons

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
    question_text = surface_result.text
    if require_body_inverse and not body_inverse_reasons:
        for line in surface_result.lines:
            if line.binding.claim_scope == "unresolved_answer_interpretation":
                # Only an independently matched source-limit sentence may
                # contain quoted questions. Its outside predicate is fixed;
                # no source quotation can authorize an Emlis question.
                question_text = question_text.replace(line.text, "", 1)
    question_free = bool(
        not plan.response_plan.question_policy.allowed
        and all(not line.binding.contains_question for line in sentence_plan.lines)
        and "?" not in question_text
        and "？" not in question_text
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
        reasons.extend(
            (*semantic_subcheck_reasons, *body_inverse_reasons)
            or ("grounded_text_semantic_retention_failed",)
        )
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
    "GroundedBodyInverseEvaluation",
    "GroundedObservationGateReport",
    "grounded_gate_meta_is_body_free",
    "evaluate_grounded_surface_body_inverse",
    "evaluate_grounded_observation_gate",
]


def evaluate_emlis_history_line_inverse(text, line_plan, *, prepared):
    """Independent Layer-3 grammar/anchor check; never enter two-layer inverse."""
    from datetime import datetime
    from cocolon_meaning_experience_engine.emlis_thread_history import admitted_history_plans
    from cocolon_meaning_experience_engine.emlis_answer_update import build_updated_grounded_plan
    from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
    current_plan = build_updated_grounded_plan(prepared)
    past = next((row for row in admitted_history_plans(prepared.thread) if row[0].source_guard[0] == line_plan.input_id), None)
    if past is None or past[0].recorded_at != line_plan.recorded_at:
        return False
    for plan, resolver, nid, expected, evidence in (
        (current_plan, prepared.thread.resolver(), line_plan.current_nucleus_id, line_plan.current_text, line_plan.current_evidence_refs),
        (past[2],past[1].thread.resolver(),line_plan.past_nucleus_id,line_plan.past_text,line_plan.past_evidence_refs)):
        index = {n.nucleus_id:n for n in plan.nuclei}
        if nid not in index or final_reception_source_anchor_text(nid,index,resolver) != expected:
            return False
        if tuple(resolver.qualified_ref(s).evidence.evidence_id for s in index[nid].source_span_ids) != evidence:
            return False
    match = re.fullmatch(r'今回の「([^「」\n]+)」という言葉は、(\d{4}-\d{2}-\d{2})の記録の「([^「」\n]+)」にも重なります。同じ言葉でも、今回の受け止めまで同じとは決めずに見ています。', text)
    if not match or line_plan.relation != 'REPEATED_EXPLICIT_WORDING':
        return False
    return (match.group(1) == line_plan.current_text and match.group(3) == line_plan.past_text
            and match.group(2) == datetime.fromisoformat(line_plan.recorded_at.replace('Z','+00:00')).date().isoformat()
            and bool(line_plan.current_evidence_refs and line_plan.past_evidence_refs))
