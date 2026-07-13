# -*- coding: utf-8 -*-
from __future__ import annotations

"""Process-local Surface Candidate Generator for grounded reception v2.

Step 5 realizes the bounded, body-free plans produced by the Discourse
Candidate Planner.  It reuses v1's move-scoped referent resolver, predicate
responsibility registry, and phrase-bound anchor shortening, while keeping
all candidate bodies process-local.  It does not score, select, persist, or
connect a candidate to the production reply owner; those are later steps.
"""

from dataclasses import asdict, dataclass, replace
import re
from typing import Any, Final, Literal, Mapping, Sequence

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_human_reception import (
    _compact_bound_anchor as _compact_v1_bound_anchor,
    GroundedReceptionReferent,
    realize_grounded_human_reception,
    reception_move_predicate_family,
    resolve_grounded_reception_move_referent,
)
from emlis_ai_grounded_observation_plan import (
    GroundedHumanReceptionPlan,
    GroundedObservationPlan,
    GroundedReceptionAct,
    GroundedReceptionMovePlan,
    GroundedSemanticNucleus,
)
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION,
    ReceptionCandidatePlanSetV2,
    ReceptionCandidatePlanV2,
    ReceptionVariationSignatureV2,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION,
    ReceptionContentPlanV2,
    ReceptionContentUnitV2,
)


RECEPTION_SURFACE_CANDIDATE_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_surface_candidate.v1"
)
RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_surface_candidate_set.v1"
)

V1ComparisonClassification = Literal[
    "v1_identical_only",
    "v1_identical_present",
    "v1_distinct_only",
]

_QUOTE_RE: Final = re.compile(r"「([^」]*)」")
_QUESTION_RE: Final = re.compile(r"[?？]")
_BROKEN_PUNCTUATION_RE: Final = re.compile(r"(?:、、|。。|、。|。、)")
_CAUSAL_CONNECTOR_RE: Final = re.compile(
    r"(?:だから|そのため|ことで|につながっている|として表れている)"
)
_SAFE_STRUCTURED_LABEL_RE: Final = re.compile(
    r"^[A-Za-z0-9一-龠々ぁ-んァ-ヶー]{1,16}$"
)

_OPPORTUNITY_ACT_BY_SIGNATURE: Final[Mapping[str, GroundedReceptionAct]] = {
    "current_burden_present": "stay_with_current_burden",
    "concrete_action_recorded": "honor_concrete_effort",
    "intention_retained": "protect_retained_intention",
    "lived_change_observed": "recognize_lived_change",
    "help_seeking_preserved": "hold_help_seeking",
    "self_denial_boundary": "bounded_counter_self_denial",
    "expression_or_label_present": "respect_words_placed",
}
_RELATION_ACT_BY_SIGNATURE: Final[Mapping[str, GroundedReceptionAct]] = {
    "action_connected_to_observed_change": "recognize_lived_change",
    "attempt_held_with_block": "stay_with_current_burden",
    "attention_or_evaluation_shift": "recognize_lived_change",
    "counterposed_meanings_coexist": "respect_words_placed",
    "distinct_meanings_coexist": "respect_words_placed",
    "identity_claim_and_grounded_counterdirection": "protect_retained_intention",
    "continuation_or_refusal_preserved": "respect_words_placed",
    "value_or_intention_preserved_despite_burden": "protect_retained_intention",
    "connection_kept_uncertain": "respect_words_placed",
    "wish_held_with_constraint": "protect_retained_intention",
    "grounded_relation_preserved": "respect_words_placed",
    "self_evaluation_connected_to_state": "respect_words_placed",
    "evaluation_connected_to_event": "respect_words_placed",
    "user_stated_result_relation": "respect_words_placed",
    "user_stated_cause_relation": "respect_words_placed",
    "time_bounded_transition": "recognize_lived_change",
}
_NOMINAL_REFERENT_BY_ACT: Final[Mapping[GroundedReceptionAct, str]] = {
    "stay_with_current_burden": "今ここにある負担",
    "honor_concrete_effort": "実際に動いたということ",
    "protect_retained_intention": "そこに残っている願い",
    "recognize_lived_change": "確かめてきた変化",
    "hold_help_seeking": "助けへ向けて残した一歩",
    "bounded_counter_self_denial": "今そこにある苦しさ",
    "respect_words_placed": "ここに言葉を置いたこと",
}
_DEICTIC_REFERENT_BY_ACT: Final[Mapping[GroundedReceptionAct, str]] = {
    "stay_with_current_burden": "その負担",
    "honor_concrete_effort": "その行動",
    "protect_retained_intention": "その願い",
    "recognize_lived_change": "その変化",
    "hold_help_seeking": "その一歩",
    "bounded_counter_self_denial": "その苦しさ",
    "respect_words_placed": "その点",
}
_RELATION_REFERENT_BY_SIGNATURE: Final[Mapping[str, str]] = {
    "action_connected_to_observed_change": "実際に動いたことと、そこで見えた変化",
    "attempt_held_with_block": "動こうとしたことと、その難しさ",
    "attention_or_evaluation_shift": "見方が移ってきたこと",
    "counterposed_meanings_coexist": "並んでいる二つの意味",
    "distinct_meanings_coexist": "それぞれに残っている意味",
    "identity_claim_and_grounded_counterdirection": (
        "その自己評価だけでは終わらない思い"
    ),
    "continuation_or_refusal_preserved": "続けることと、いったん立ち止まること",
    "value_or_intention_preserved_despite_burden": (
        "そこにある負担と、その中にも残っている願い"
    ),
    "connection_kept_uncertain": "その二つのつながり",
    "wish_held_with_constraint": "願いと、そこにある制約",
    "grounded_relation_preserved": "そこに並んでいる二つのこと",
    "self_evaluation_connected_to_state": "自己評価と、今そこにある状態",
    "evaluation_connected_to_event": "受け止め方と、そこで起きたこと",
    "user_stated_result_relation": "本人が結びつけた出来事と結果",
    "user_stated_cause_relation": "本人が結びつけた出来事と理由",
    "time_bounded_transition": "時間を隔てて見えてきた変化",
}


class ReceptionSurfaceCandidateV2Error(ValueError):
    """Raised when a Step 5 process-local surface cannot be realized."""


@dataclass(frozen=True)
class ReceptionSurfaceCandidateV2:
    schema_version: str
    candidate_id: str
    content_plan_id: str
    text: str
    sentence_count: int
    realized_unit_ids: tuple[str, ...]
    grounded_nucleus_ids: tuple[str, ...]
    grounded_evidence_span_ids: tuple[str, ...]
    referent_kinds: tuple[str, ...]
    predicate_families: tuple[str, ...]
    source_anchor_count: int
    source_anchor_max_visible_chars: int
    variation_signature: ReceptionVariationSignatureV2
    v1_surface_identical: bool
    process_local: bool = True

    def as_body_free_meta(self) -> dict[str, Any]:
        """Return diagnostics without copying this process-local body."""

        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "content_plan_id": self.content_plan_id,
            "sentence_count": self.sentence_count,
            "realized_unit_ids": list(self.realized_unit_ids),
            "grounded_nucleus_ids": list(self.grounded_nucleus_ids),
            "grounded_evidence_span_ids": list(self.grounded_evidence_span_ids),
            "referent_kinds": list(self.referent_kinds),
            "predicate_families": list(self.predicate_families),
            "source_anchor_count": self.source_anchor_count,
            "source_anchor_max_visible_chars": self.source_anchor_max_visible_chars,
            "variation_signature": asdict(self.variation_signature),
            "v1_surface_identical": self.v1_surface_identical,
            "process_local": self.process_local,
            "candidate_body_included": False,
            "selection_performed": False,
            "hard_gate_performed": False,
        }


@dataclass(frozen=True)
class ReceptionSurfaceCandidateSetV2:
    schema_version: str
    content_plan_id: str
    source_candidate_set_schema_version: str
    candidates: tuple[ReceptionSurfaceCandidateV2, ...]
    v1_comparison_classification: V1ComparisonClassification
    v1_identical_candidate_count: int
    process_local_bodies: bool = True
    selection_performed: bool = False
    hard_gate_performed: bool = False
    runtime_connected: bool = False

    def as_body_free_meta(self) -> dict[str, Any]:
        """Return the comparison receipt without serializing candidate text."""

        return {
            "schema_version": self.schema_version,
            "content_plan_id": self.content_plan_id,
            "source_candidate_set_schema_version": (
                self.source_candidate_set_schema_version
            ),
            "candidate_count": len(self.candidates),
            "candidate_meta": [
                candidate.as_body_free_meta() for candidate in self.candidates
            ],
            "v1_comparison_classification": self.v1_comparison_classification,
            "v1_identical_candidate_count": self.v1_identical_candidate_count,
            "process_local_bodies": self.process_local_bodies,
            "candidate_bodies_included": False,
            "selection_performed": self.selection_performed,
            "hard_gate_performed": self.hard_gate_performed,
            "runtime_connected": self.runtime_connected,
            "public_contract_changed": False,
        }


@dataclass(frozen=True)
class _ResolvedUnit:
    unit: ReceptionContentUnitV2
    move: GroundedReceptionMovePlan
    referent: GroundedReceptionReferent
    predicate_family: str


@dataclass(frozen=True)
class _PredicateForm:
    particle: Literal["が", "を"]
    terminal: str
    connective: str


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    rows: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in seen:
            seen.add(value)
            rows.append(value)
    return tuple(rows)


def _act_for_unit(unit: ReceptionContentUnitV2) -> GroundedReceptionAct:
    signature = unit.semantic_signature
    if signature.startswith("emlis_reception_of_"):
        signature = signature.removeprefix("emlis_reception_of_")
    if unit.role == "bounded_counterposition":
        return "bounded_counter_self_denial"
    act = _OPPORTUNITY_ACT_BY_SIGNATURE.get(signature)
    if act is None:
        act = _RELATION_ACT_BY_SIGNATURE.get(signature)
    if act is None:
        raise ReceptionSurfaceCandidateV2Error(
            f"unsupported_content_unit_signature:{unit.semantic_signature}"
        )
    if act == "bounded_counter_self_denial":
        raise ReceptionSurfaceCandidateV2Error(
            f"bounded_act_requires_bounded_role:{unit.unit_id}"
        )
    return act


def _ephemeral_move(
    unit: ReceptionContentUnitV2,
    candidate: ReceptionCandidatePlanV2,
) -> GroundedReceptionMovePlan:
    act = _act_for_unit(unit)
    move_role = "significance" if unit.role == "connection" else unit.role
    if move_role == "bounded_counterposition":
        surface_strategy = "explicit_emlis_counterposition"
        reference_mode = "explicit_emlis_counterposition"
    elif move_role == "attention":
        surface_strategy = "emlis_attention_first"
        reference_mode = (
            "short_anchor_if_ambiguous"
            if candidate.variation_signature.referent == "short_bound_anchor"
            else "anaphoric_first"
        )
    elif move_role == "significance":
        surface_strategy = "referent_significance_first"
        reference_mode = (
            "short_anchor_if_ambiguous"
            if candidate.variation_signature.referent == "short_bound_anchor"
            else "anaphoric_first"
        )
    else:
        surface_strategy = "felt_response_first"
        reference_mode = (
            "short_anchor_if_ambiguous"
            if candidate.variation_signature.referent == "short_bound_anchor"
            else "anaphoric_first"
        )
    speaker_presence = (
        "implicit_emlis"
        if candidate.variation_signature.speaker_presence == "implicit_emlis"
        else "explicit_emlis"
    )
    move = GroundedReceptionMovePlan(
        move_id=f"v2_{unit.unit_id}",
        move_role=move_role,
        reception_act=act,
        target_nucleus_ids=unit.target_nucleus_ids,
        support_nucleus_ids=unit.support_nucleus_ids,
        source_evidence_span_ids=unit.evidence_span_ids,
        follow_elements=(),
        speaker_presence=speaker_presence,
        reference_mode=reference_mode,
        surface_strategy=surface_strategy,
        required=unit.required,
        distinct_from_move_ids=tuple(
            f"v2_{unit_id}"
            for unit_id in candidate.ordered_unit_ids
            if unit_id != unit.unit_id
        ),
    )
    # The v1 registry remains the owner of valid role/act responsibility.
    reception_move_predicate_family(move)
    return move


def _shared_nucleus(
    left: ReceptionContentUnitV2,
    right: ReceptionContentUnitV2,
) -> bool:
    left_ids = set((*left.target_nucleus_ids, *left.support_nucleus_ids))
    right_ids = set((*right.target_nucleus_ids, *right.support_nucleus_ids))
    return bool(left_ids & right_ids)


def _adapt_referent(
    referent: GroundedReceptionReferent,
    move: GroundedReceptionMovePlan,
    unit: ReceptionContentUnitV2,
    candidate: ReceptionCandidatePlanV2,
    resolver: EvidenceSpanResolver,
    *,
    use_deictic: bool,
    allow_source_anchor: bool,
) -> GroundedReceptionReferent:
    policy = candidate.variation_signature.referent
    relation_text = _RELATION_REFERENT_BY_SIGNATURE.get(unit.semantic_signature)
    if (
        unit.semantic_signature.removeprefix("emlis_reception_of_")
        == "expression_or_label_present"
        and policy != "nominalized_content"
    ):
        spans = resolver.resolve_many(referent.evidence_span_ids)
        structured = tuple(
            span
            for span in resolver.resolve_many(resolver.span_ids)
            if span.source_field in {"emotion_details", "emotions", "category"}
        )
        if spans:
            span = spans[0]
            label = str(span.raw_text or "").strip()
            multiple = len(structured) > 3
            if (
                span.source_field in {"emotion_details", "emotions"}
                and _SAFE_STRUCTURED_LABEL_RE.fullmatch(label)
            ):
                return replace(
                    referent,
                    kind=(
                        "structured_label_emotion_multiple"
                        if multiple
                        else "structured_label_emotion_single"
                    ),
                    text=(
                        f"いくつか並ぶ気持ちの中にある{label}"
                        if multiple
                        else f"{label}としてここに残した気持ち"
                    ),
                    source_anchor_used=False,
                )
            if (
                span.source_field == "category"
                and _SAFE_STRUCTURED_LABEL_RE.fullmatch(label)
            ):
                return replace(
                    referent,
                    kind=(
                        "structured_label_category_multiple"
                        if multiple
                        else "structured_label_category_single"
                    ),
                    text=(
                        f"いくつかの関心の中にある{label}のこと"
                        if multiple
                        else f"{label}についてここに置いたこと"
                    ),
                    source_anchor_used=False,
                )
    if (
        policy == "short_bound_anchor"
        and allow_source_anchor
        and not referent.source_anchor_used
        and not unit.relation_ids
    ):
        spans = resolver.resolve_many(referent.evidence_span_ids)
        for span in spans:
            if span.source_field not in {"memo", "memo_action"}:
                continue
            source = re.sub(r"\s+", " ", str(span.raw_text or "")).strip()
            source = source.strip(" \u3000、,。．.")
            if not source or _QUESTION_RE.search(source):
                continue
            anchor = (
                source
                if len(source) <= 16
                else _compact_v1_bound_anchor(source, 16)
            )
            if 2 <= len(anchor) <= 16:
                return replace(
                    referent,
                    kind=f"anchored_{move.reception_act}",
                    text=f"「{anchor}」とここに残したこと",
                    source_anchor_used=True,
                )
    if policy == "nominalized_content":
        return replace(
            referent,
            kind=(
                f"nominalized_relation_{unit.semantic_signature}"
                if relation_text
                else f"nominalized_{move.reception_act}"
            ),
            text=relation_text or _NOMINAL_REFERENT_BY_ACT[move.reception_act],
            source_anchor_used=False,
        )
    if policy == "deictic_after_unique_antecedent" and use_deictic:
        return replace(
            referent,
            kind=f"deictic_{move.reception_act}",
            text=_DEICTIC_REFERENT_BY_ACT[move.reception_act],
            source_anchor_used=False,
        )
    if relation_text and not referent.source_anchor_used:
        return replace(
            referent,
            kind=f"relation_{unit.semantic_signature}",
            text=relation_text,
            source_anchor_used=False,
        )
    return referent


def _base_predicate(act: GroundedReceptionAct) -> _PredicateForm:
    if act == "stay_with_current_burden":
        return _PredicateForm(
            "を",
            "無理に小さくせず、受け止めています",
            "無理に小さくせず受け止め",
        )
    if act == "honor_concrete_effort":
        return _PredicateForm(
            "を",
            "その手間ごと大切に受け取っています",
            "その手間ごと大切に受け取り",
        )
    if act == "protect_retained_intention":
        return _PredicateForm(
            "を",
            "なかったことにせず、大切にしています",
            "なかったことにせず大切にし",
        )
    if act == "recognize_lived_change":
        return _PredicateForm(
            "を",
            "軽い変化として流さず、受け取っています",
            "軽い変化として流さず受け取り",
        )
    if act == "hold_help_seeking":
        return _PredicateForm(
            "を",
            "大切な一歩として、見過ごさずにいたいです",
            "大切な一歩として見過ごさず",
        )
    if act == "respect_words_placed":
        return _PredicateForm(
            "を",
            "そのまま静かに受け取っています",
            "そのまま静かに受け取り",
        )
    raise ReceptionSurfaceCandidateV2Error(
        f"bounded_predicate_requires_separate_surface:{act}"
    )


def _relation_predicate_form(signature: str) -> _PredicateForm:
    """Realize relation meaning as a relation, not as a generic object."""

    if signature == "connection_kept_uncertain":
        return _PredicateForm("を", "まだ決めつけずにいます", "まだ決めつけず")
    if signature == "continuation_or_refusal_preserved":
        return _PredicateForm(
            "を",
            "まだひとつに決めず、受け取っています",
            "まだひとつに決めず受け取り",
        )
    if signature in {
        "counterposed_meanings_coexist",
        "distinct_meanings_coexist",
        "identity_claim_and_grounded_counterdirection",
    }:
        return _PredicateForm(
            "を",
            "ひとつにまとめず、受け取っています",
            "ひとつにまとめず受け取り",
        )
    if signature in {
        "action_connected_to_observed_change",
        "attempt_held_with_block",
        "wish_held_with_constraint",
        "value_or_intention_preserved_despite_burden",
    }:
        return _PredicateForm(
            "を",
            "ともに見落とさず、受け取っています",
            "ともに見落とさず受け取り",
        )
    if signature in {
        "attention_or_evaluation_shift",
        "time_bounded_transition",
    }:
        return _PredicateForm(
            "を",
            "軽い変化として流さず、受け取っています",
            "軽い変化として流さず受け取り",
        )
    return _PredicateForm(
        "を",
        "広げすぎず、そのまま受け取っています",
        "広げすぎずそのまま受け取り",
    )


def _predicate_form(
    move: GroundedReceptionMovePlan,
    candidate: ReceptionCandidatePlanV2,
) -> _PredicateForm:
    family = candidate.variation_signature.terminal_family
    if move.move_role == "bounded_counterposition":
        raise ReceptionSurfaceCandidateV2Error(
            "bounded_counterposition_uses_owned_clause"
        )
    if move.move_role == "attention":
        if family == "restraint":
            return _PredicateForm(
                "を",
                "見過ごしたくありません",
                "見過ごさず",
            )
        if family == "meaning_preservation":
            return _PredicateForm(
                "を",
                "軽いこととして流したくありません",
                "軽いこととして流さず",
            )
        return _PredicateForm(
            "が",
            "特に印象に残っています",
            "特に印象に残り",
        )
    if move.move_role == "felt_response" and family == "attention_hold":
        return _PredicateForm(
            "を",
            "心に留めています",
            "心に留め",
        )
    if family == "attention_hold":
        return _PredicateForm("が", "特に印象に残っています", "特に印象に残り")
    if family == "restraint":
        if move.reception_act == "stay_with_current_burden":
            return _base_predicate(move.reception_act)
        return _PredicateForm(
            "を",
            "軽いこととして流したくありません",
            "軽いこととして流さず",
        )
    if family == "meaning_preservation":
        if move.reception_act == "stay_with_current_burden":
            return _PredicateForm(
                "を",
                "軽いこととして片づけず、そこにあるものとして受け止めています",
                "軽いこととして片づけず受け止め",
            )
        if move.reception_act == "honor_concrete_effort":
            return _PredicateForm(
                "を",
                "実際に動いたこととして、大切にしています",
                "実際に動いたこととして大切にし",
            )
        if move.reception_act == "protect_retained_intention":
            return _PredicateForm(
                "を",
                "なかったことにせず、大切にしています",
                "なかったことにせず大切にし",
            )
        if move.reception_act == "recognize_lived_change":
            return _PredicateForm(
                "を",
                "見過ごさずにいたいです",
                "見過ごさず",
            )
        if move.reception_act == "hold_help_seeking":
            return _PredicateForm(
                "を",
                "なかったことにせず、残しておきたいです",
                "なかったことにせず残し",
            )
        if move.reception_act == "respect_words_placed":
            return _PredicateForm(
                "を",
                "なかったことにせず、受け取っています",
                "なかったことにせず受け取り",
            )
    return _base_predicate(move.reception_act)


def _bounded_counterposition_clause() -> str:
    # This is the existing v1 safety responsibility, not a new identity claim.
    return (
        "今そこにある苦しさを否定せず、"
        "Emlisには、その言葉だけであなた自身が決まるとは思えません"
    )


def _render_unit_clause(
    resolved: _ResolvedUnit,
    candidate: ReceptionCandidatePlanV2,
    *,
    explicit_emlis: bool,
    connective: bool,
) -> str:
    if resolved.move.move_role == "bounded_counterposition":
        if connective:
            raise ReceptionSurfaceCandidateV2Error(
                "bounded_counterposition_must_remain_separate"
            )
        return _bounded_counterposition_clause()

    form = (
        _relation_predicate_form(resolved.unit.semantic_signature)
        if resolved.unit.relation_ids
        else _predicate_form(resolved.move, candidate)
    )
    predicate = form.connective if connective else form.terminal
    if explicit_emlis:
        prefix = "Emlisには、" if form.particle == "が" else "Emlisは、"
    else:
        prefix = ""
    separator = "" if connective else "、"
    return (
        f"{prefix}{resolved.referent.text}{form.particle}"
        f"{separator}{predicate}"
    )


def _sentence_prefix(
    candidate: ReceptionCandidatePlanV2,
    sentence_index: int,
) -> str:
    variation = candidate.variation_signature
    if sentence_index == 0:
        if variation.opening == "semantic_shift":
            return "違いをひとつにまとめず、"
        if variation.opening == "uncertainty_boundary":
            return "分からない部分を決めつけず、"
        return ""
    if sentence_index == 1:
        if variation.connection == "contrast_safe":
            return "一方で、"
        if variation.connection == "uncertainty_then_action":
            return "その不明さを残したまま、"
        if variation.connection == "relation_bound":
            return "あわせて、"
        if variation.connection == "separate_responsibilities":
            return "それとは分けて、"
        return "また、"
    if variation.connection in {"parallel", "relation_bound"}:
        return "また、"
    return ""


def _group_connector(candidate: ReceptionCandidatePlanV2) -> str:
    connection = candidate.variation_signature.connection
    if connection == "contrast_safe":
        return "一方で、"
    if connection == "uncertainty_then_action":
        return "その不明さを残したまま、"
    if connection == "relation_bound":
        return "あわせて、"
    if connection == "separate_responsibilities":
        raise ReceptionSurfaceCandidateV2Error(
            "separate_responsibilities_cannot_merge"
        )
    return "あわせて、"


def _explicit_unit_position(
    candidate: ReceptionCandidatePlanV2,
    sentence_index: int,
    sentence_count: int,
    group_size: int,
) -> int | None:
    variation = candidate.variation_signature
    if variation.opening == "emlis_attention" and sentence_index == 0:
        return 0
    if (
        variation.speaker_presence == "explicit_first_sentence"
        and sentence_index == 0
    ):
        return 0
    if (
        variation.speaker_presence == "explicit_terminal_sentence"
        and sentence_index == sentence_count - 1
    ):
        return group_size - 1
    return None


def _resolve_candidate_units(
    reception_plan: GroundedHumanReceptionPlan,
    content_plan: ReceptionContentPlanV2,
    candidate: ReceptionCandidatePlanV2,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
) -> dict[str, _ResolvedUnit]:
    unit_index = {unit.unit_id: unit for unit in content_plan.content_units}
    referent_plan = reception_plan
    if (
        content_plan.quote_policy.max_anchor_count
        > reception_plan.quote_policy.max_anchor_count
    ):
        referent_plan = replace(
            reception_plan,
            quote_policy=replace(
                reception_plan.quote_policy,
                max_anchor_count=content_plan.quote_policy.max_anchor_count,
            ),
        )
    resolved: dict[str, _ResolvedUnit] = {}
    anchor_used = False
    for group in candidate.sentence_groups:
        for group_index, unit_id in enumerate(group):
            unit = unit_index[unit_id]
            move = _ephemeral_move(unit, candidate)
            referent = resolve_grounded_reception_move_referent(
                referent_plan,
                move,
                nucleus_index,
                resolver,
                allow_short_anchor=bool(
                    candidate.variation_signature.referent == "short_bound_anchor"
                    and not anchor_used
                    and content_plan.quote_policy.mode == "optional_single_anchor"
                    and content_plan.quote_policy.max_anchor_count > 0
                ),
            )
            use_deictic = bool(
                group_index == 1
                and len(group) == 2
                and _shared_nucleus(unit_index[group[0]], unit)
            )
            referent = _adapt_referent(
                referent,
                move,
                unit,
                candidate,
                resolver,
                use_deictic=use_deictic,
                allow_source_anchor=bool(
                    candidate.variation_signature.referent
                    == "short_bound_anchor"
                    and not anchor_used
                    and content_plan.quote_policy.max_anchor_count > 0
                ),
            )
            anchor_used = anchor_used or referent.source_anchor_used
            resolved[unit_id] = _ResolvedUnit(
                unit=unit,
                move=move,
                referent=referent,
                predicate_family=reception_move_predicate_family(move),
            )
    return resolved


def _realize_candidate_text(
    candidate: ReceptionCandidatePlanV2,
    resolved: Mapping[str, _ResolvedUnit],
) -> str:
    sentences: list[str] = []
    sentence_count = len(candidate.sentence_groups)
    for sentence_index, group in enumerate(candidate.sentence_groups):
        explicit_position = _explicit_unit_position(
            candidate,
            sentence_index,
            sentence_count,
            len(group),
        )
        clauses = [
            _render_unit_clause(
                resolved[unit_id],
                candidate,
                explicit_emlis=bool(
                    explicit_position == group_index
                    or resolved[unit_id].move.move_role
                    == "bounded_counterposition"
                ),
                connective=group_index < len(group) - 1,
            )
            for group_index, unit_id in enumerate(group)
        ]
        sentence = (
            clauses[0]
            if len(clauses) == 1
            else f"{clauses[0]}、{_group_connector(candidate)}{clauses[1]}"
        )
        sentence = f"{_sentence_prefix(candidate, sentence_index)}{sentence}"
        sentences.append(sentence.rstrip("。") + "。")
    return "".join(sentences)


def _sentences(text: str) -> tuple[str, ...]:
    if not text or not text.endswith("。"):
        return ()
    parts = text.split("。")
    if parts[-1] != "" or any(not part.strip() for part in parts[:-1]):
        return ()
    return tuple(f"{part.strip()}。" for part in parts[:-1])


def _comparison_classification(
    identical_count: int,
    candidate_count: int,
) -> V1ComparisonClassification:
    if identical_count == candidate_count:
        return "v1_identical_only"
    if identical_count:
        return "v1_identical_present"
    return "v1_distinct_only"


def generate_reception_surface_candidates_v2(
    observation_plan: GroundedObservationPlan,
    content_plan: ReceptionContentPlanV2,
    candidate_plan_set: ReceptionCandidatePlanSetV2,
    resolver: EvidenceSpanResolver,
) -> ReceptionSurfaceCandidateSetV2:
    """Generate all Step 5 bodies without selecting or persisting one."""

    if not isinstance(observation_plan, GroundedObservationPlan):
        raise ReceptionSurfaceCandidateV2Error("grounded_observation_plan_required")
    if content_plan.schema_version != RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION:
        raise ReceptionSurfaceCandidateV2Error("content_plan_schema_mismatch")
    if (
        candidate_plan_set.schema_version
        != RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION
    ):
        raise ReceptionSurfaceCandidateV2Error("candidate_plan_set_schema_mismatch")
    if candidate_plan_set.content_plan_id != content_plan.plan_id:
        raise ReceptionSurfaceCandidateV2Error("candidate_content_plan_mismatch")
    reception_plan = observation_plan.response_plan.human_reception_plan
    if reception_plan is None or not reception_plan.required:
        raise ReceptionSurfaceCandidateV2Error("human_reception_plan_required")
    nucleus_index = {item.nucleus_id: item for item in observation_plan.nuclei}
    v1_text = realize_grounded_human_reception(
        reception_plan,
        nucleus_index,
        resolver,
    ).text

    surfaces: list[ReceptionSurfaceCandidateV2] = []
    for candidate_plan in candidate_plan_set.candidates:
        resolved = _resolve_candidate_units(
            reception_plan,
            content_plan,
            candidate_plan,
            nucleus_index,
            resolver,
        )
        text = _realize_candidate_text(candidate_plan, resolved)
        quote_values = tuple(_QUOTE_RE.findall(text))
        rows = tuple(resolved[unit_id] for unit_id in candidate_plan.ordered_unit_ids)
        surface = ReceptionSurfaceCandidateV2(
            schema_version=RECEPTION_SURFACE_CANDIDATE_V2_SCHEMA_VERSION,
            candidate_id=candidate_plan.candidate_id,
            content_plan_id=content_plan.plan_id,
            text=text,
            sentence_count=len(_sentences(text)),
            realized_unit_ids=candidate_plan.ordered_unit_ids,
            grounded_nucleus_ids=_dedupe(
                [
                    nucleus_id
                    for row in rows
                    for nucleus_id in (
                        *row.unit.target_nucleus_ids,
                        *row.unit.support_nucleus_ids,
                    )
                ]
            ),
            grounded_evidence_span_ids=_dedupe(
                [span_id for row in rows for span_id in row.unit.evidence_span_ids]
            ),
            referent_kinds=tuple(row.referent.kind for row in rows),
            predicate_families=tuple(row.predicate_family for row in rows),
            source_anchor_count=len(quote_values),
            source_anchor_max_visible_chars=max(
                (len(value) for value in quote_values),
                default=0,
            ),
            variation_signature=candidate_plan.variation_signature,
            v1_surface_identical=text == v1_text,
            process_local=True,
        )
        issues = validate_reception_surface_candidate_v2(
            surface,
            candidate_plan,
            content_plan,
            reception_plan,
            resolver,
        )
        if issues:
            raise ReceptionSurfaceCandidateV2Error(
                f"invalid_surface_candidate:{candidate_plan.candidate_id}:"
                + ",".join(issues)
            )
        surfaces.append(surface)

    identical_count = sum(item.v1_surface_identical for item in surfaces)
    candidate_set = ReceptionSurfaceCandidateSetV2(
        schema_version=RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION,
        content_plan_id=content_plan.plan_id,
        source_candidate_set_schema_version=candidate_plan_set.schema_version,
        candidates=tuple(surfaces),
        v1_comparison_classification=_comparison_classification(
            identical_count,
            len(surfaces),
        ),
        v1_identical_candidate_count=identical_count,
        process_local_bodies=True,
        selection_performed=False,
        hard_gate_performed=False,
        runtime_connected=False,
    )
    issues = validate_reception_surface_candidate_set_v2(
        candidate_set,
        candidate_plan_set,
    )
    if issues:
        raise ReceptionSurfaceCandidateV2Error(
            "invalid_surface_candidate_set:" + ",".join(issues)
        )
    return candidate_set


def validate_reception_surface_candidate_v2(
    surface: ReceptionSurfaceCandidateV2,
    candidate_plan: ReceptionCandidatePlanV2,
    content_plan: ReceptionContentPlanV2,
    reception_plan: GroundedHumanReceptionPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Validate Step 5 surface integrity, not Step 6 eligibility."""

    issues: list[str] = []
    if surface.schema_version != RECEPTION_SURFACE_CANDIDATE_V2_SCHEMA_VERSION:
        issues.append("schema_mismatch")
    if surface.candidate_id != candidate_plan.candidate_id:
        issues.append("candidate_id_mismatch")
    if surface.content_plan_id != content_plan.plan_id:
        issues.append("content_plan_id_mismatch")
    sentences = _sentences(surface.text)
    if not sentences or len(sentences) != len(candidate_plan.sentence_groups):
        issues.append("sentence_group_count_mismatch")
    if surface.sentence_count != len(sentences):
        issues.append("sentence_count_mismatch")
    if _QUESTION_RE.search(surface.text):
        issues.append("question_surface_forbidden")
    if _BROKEN_PUNCTUATION_RE.search(surface.text):
        issues.append("broken_punctuation")
    if _CAUSAL_CONNECTOR_RE.search(surface.text):
        issues.append("causal_connector_not_generated_in_step5")
    if surface.text.count("「") != surface.text.count("」"):
        issues.append("quote_unbalanced")
    quote_values = tuple(_QUOTE_RE.findall(surface.text))
    quote_limit = content_plan.quote_policy.max_anchor_count
    if len(quote_values) > quote_limit:
        issues.append("quote_count_exceeded")
    if any(
        len(value) > reception_plan.quote_policy.max_anchor_visible_chars
        for value in quote_values
    ):
        issues.append("quote_visible_chars_exceeded")
    if surface.source_anchor_count != len(quote_values):
        issues.append("source_anchor_count_mismatch")
    if surface.source_anchor_max_visible_chars != max(
        (len(value) for value in quote_values),
        default=0,
    ):
        issues.append("source_anchor_max_chars_mismatch")
    if surface.realized_unit_ids != candidate_plan.ordered_unit_ids:
        issues.append("realized_unit_order_mismatch")
    unit_index = {unit.unit_id: unit for unit in content_plan.content_units}
    expected_nuclei = _dedupe(
        [
            nucleus_id
            for unit_id in candidate_plan.ordered_unit_ids
            for nucleus_id in (
                *unit_index[unit_id].target_nucleus_ids,
                *unit_index[unit_id].support_nucleus_ids,
            )
        ]
    )
    expected_evidence = _dedupe(
        [
            span_id
            for unit_id in candidate_plan.ordered_unit_ids
            for span_id in unit_index[unit_id].evidence_span_ids
        ]
    )
    if surface.grounded_nucleus_ids != expected_nuclei:
        issues.append("grounded_nucleus_coverage_mismatch")
    if surface.grounded_evidence_span_ids != expected_evidence:
        issues.append("grounded_evidence_coverage_mismatch")
    if resolver.unresolved_ids(surface.grounded_evidence_span_ids):
        issues.append("grounded_evidence_unresolved")
    if len(surface.predicate_families) != len(candidate_plan.ordered_unit_ids):
        issues.append("predicate_responsibility_count_mismatch")
    if len(surface.referent_kinds) != len(candidate_plan.ordered_unit_ids):
        issues.append("referent_count_mismatch")
    if surface.variation_signature != candidate_plan.variation_signature:
        issues.append("variation_signature_mismatch")
    if surface.process_local is not True:
        issues.append("surface_not_process_local")
    return _dedupe(issues)


def validate_reception_surface_candidate_set_v2(
    surface_set: ReceptionSurfaceCandidateSetV2,
    candidate_plan_set: ReceptionCandidatePlanSetV2,
) -> tuple[str, ...]:
    issues: list[str] = []
    if surface_set.schema_version != RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION:
        issues.append("candidate_set_schema_mismatch")
    if surface_set.content_plan_id != candidate_plan_set.content_plan_id:
        issues.append("candidate_set_content_plan_id_mismatch")
    if (
        surface_set.source_candidate_set_schema_version
        != candidate_plan_set.schema_version
    ):
        issues.append("source_candidate_set_schema_mismatch")
    if tuple(item.candidate_id for item in surface_set.candidates) != tuple(
        item.candidate_id for item in candidate_plan_set.candidates
    ):
        issues.append("candidate_order_mismatch")
    if len({item.candidate_id for item in surface_set.candidates}) != len(
        surface_set.candidates
    ):
        issues.append("candidate_id_duplicate")
    identical_count = sum(item.v1_surface_identical for item in surface_set.candidates)
    if surface_set.v1_identical_candidate_count != identical_count:
        issues.append("v1_identical_count_mismatch")
    if surface_set.v1_comparison_classification != _comparison_classification(
        identical_count,
        len(surface_set.candidates),
    ):
        issues.append("v1_comparison_classification_mismatch")
    if surface_set.process_local_bodies is not True:
        issues.append("candidate_bodies_not_process_local")
    if surface_set.selection_performed is not False:
        issues.append("step6_selection_must_not_run")
    if surface_set.hard_gate_performed is not False:
        issues.append("step6_hard_gate_must_not_run")
    if surface_set.runtime_connected is not False:
        issues.append("runtime_connection_forbidden")
    return _dedupe(issues)


__all__ = [
    "RECEPTION_SURFACE_CANDIDATE_V2_SCHEMA_VERSION",
    "RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION",
    "ReceptionSurfaceCandidateV2Error",
    "ReceptionSurfaceCandidateV2",
    "ReceptionSurfaceCandidateSetV2",
    "generate_reception_surface_candidates_v2",
    "validate_reception_surface_candidate_v2",
    "validate_reception_surface_candidate_set_v2",
]
