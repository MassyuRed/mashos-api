# -*- coding: utf-8 -*-
from __future__ import annotations

"""Functional realizer for the distinct Grounded Human Reception layer.

RR5 consumes the body-free Move sequence produced by RR2/RR3 and the ClausePlan
binding produced by RR4. RR7 keeps that same Move ownership through recovery;
only an optional third Move may be removed. It does not use case ids, source
bodies, or a completed observation as selection cues. Surface text is composed
from move-scoped semantic referents and deterministic role/act families.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
import re
from typing import Final, Literal

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import (
    GroundedHumanReceptionPlan,
    GroundedReceptionAct,
    GroundedReceptionMovePlan,
    GroundedSemanticNucleus,
)


ReceptionRecoveryStage = Literal[
    "full",
    "optional_removed",
    "integrated",
    "hedged",
    "minimal_grounded",
]
ReceptionConnectorPolicy = Literal[
    "none",
    "grounded_reason",
    "contrast_safe",
]

_RECOVERY_STAGES: Final = frozenset(
    {
        "full",
        "optional_removed",
        "integrated",
        "hedged",
        "minimal_grounded",
    }
)
_TERMINAL_PREDICATE_BY_ACT: Final[dict[GroundedReceptionAct, str]] = {
    "stay_with_current_burden": "human_response_stay_with_burden",
    "honor_concrete_effort": "human_response_honor_effort",
    "protect_retained_intention": "human_response_protect_intention",
    "recognize_lived_change": "human_response_recognize_change",
    "hold_help_seeking": "human_response_hold_help_seeking",
    "bounded_counter_self_denial": "human_response_bounded_counterposition",
    "respect_words_placed": "human_response_respect_words",
}
_STANCE_BY_ACT: Final[dict[GroundedReceptionAct, str]] = {
    "stay_with_current_burden": "quiet_presence",
    "honor_concrete_effort": "warm_recognition",
    "protect_retained_intention": "gentle_respect",
    "recognize_lived_change": "warm_recognition",
    "hold_help_seeking": "protective_presence",
    "bounded_counter_self_denial": "bounded_disagreement",
    "respect_words_placed": "gentle_respect",
}
_MOVE_ROLE_ORDER: Final = {
    "attention": 0,
    "significance": 1,
    "felt_response": 2,
    "bounded_counterposition": 3,
}
_MOVE_ROLE_BY_SURFACE_STRATEGY: Final = {
    "quiet_referent_first": "felt_response",
    "emlis_attention_first": "attention",
    "referent_significance_first": "significance",
    "felt_response_first": "felt_response",
    "explicit_emlis_counterposition": "bounded_counterposition",
}
_MOVE_PREDICATE_FAMILY_BY_ROLE_ACT: Final[dict[tuple[str, str], str]] = {
    ("attention", "stay_with_current_burden"): "human_response_attention_not_overlooked",
    ("attention", "honor_concrete_effort"): "human_response_attention_stood_out",
    ("attention", "protect_retained_intention"): "human_response_attention_stood_out",
    ("attention", "recognize_lived_change"): "human_response_attention_stood_out",
    ("attention", "hold_help_seeking"): "human_response_attention_not_overlooked",
    ("attention", "respect_words_placed"): "human_response_attention_not_overlooked",
    ("significance", "stay_with_current_burden"): "human_response_significance_not_minimized",
    ("significance", "honor_concrete_effort"): "human_response_significance_effort_made_concrete",
    (
        "significance",
        "protect_retained_intention",
    ): "human_response_significance_intention_preserved",
    ("significance", "recognize_lived_change"): "human_response_significance_change_confirmed",
    ("significance", "hold_help_seeking"): "human_response_significance_help_preserved",
    ("significance", "respect_words_placed"): "human_response_significance_words_placed",
    ("felt_response", "stay_with_current_burden"): "human_response_quiet_presence",
    ("felt_response", "honor_concrete_effort"): "human_response_felt_respect_for_effort",
    ("felt_response", "protect_retained_intention"): "human_response_felt_gentle_respect",
    ("felt_response", "recognize_lived_change"): "human_response_recognize_change",
    ("felt_response", "hold_help_seeking"): "human_response_hold_help_seeking",
    ("felt_response", "respect_words_placed"): "human_response_quiet_presence",
    (
        "bounded_counterposition",
        "bounded_counter_self_denial",
    ): "human_response_bounded_counterposition",
}
_SENTENCE_END_RE: Final = re.compile(r"[。！？!?]+")
_QUESTION_RE: Final = re.compile(r"[?？]")
_QUOTE_RE: Final = re.compile(r"「([^」]*)」")
_POLICY_EXPLANATION_RE: Final = re.compile(
    r"(?:理由|原因).{0,20}(?:決めつけ|断定)|"
    r"入力から言える範囲|診断はしません|ここでは事実として扱いません|"
    r"原因は分かりません"
)
_ADVICE_RE: Final = re.compile(
    r"(?:してください|しましょう|してみて|すべき|した方がいい|"
    r"相談して|連絡して|受診して)"
)
_UNSUPPORTED_CLAIM_RE: Final = re.compile(
    r"(?:必ず|絶対に|確実に|成功|解決|安全です|危険度|診断|"
    r"あなたは(?:強い|優しい|立派|素晴らしい))"
)
_ACT_RESPONSIBILITY_RE: Final[dict[GroundedReceptionAct, re.Pattern[str]]] = {
    "stay_with_current_burden": re.compile(
        r"(?:負荷|しんどさ|苦しさ|つらさ|置かれた言葉).{0,32}"
        r"(?:軽く扱|小さくせず)"
    ),
    "honor_concrete_effort": re.compile(
        r"(?:行動|動いたこと|動かしたこと|記録へ移したこと|働きかけ)"
        r".{0,48}(?:大切|受け止|軽いこととして流さ|軽く扱わ)"
    ),
    "protect_retained_intention": re.compile(
        r"(?:願い|大切にしたいもの).{0,40}(?:大切|なかったこと|消さず)"
    ),
    "recognize_lived_change": re.compile(
        r"変化.{0,40}(?:感じ|受け止|見過ご|軽く扱|軽いこと|流したく)"
    ),
    "hold_help_seeking": re.compile(
        r"(?:助け|踏みとどまり).{0,48}(?:大切|受け止)"
    ),
    "bounded_counter_self_denial": re.compile(
        r"苦しさ.{0,48}否定せず.*Emlis.{0,48}自身.{0,24}思えません"
    ),
    "respect_words_placed": re.compile(r"言葉.{0,40}(?:大切|受け止)"),
}
_ANCHOR_DELETE_TRANSLATION: Final = str.maketrans("", "", "「」『』?？!！")


class GroundedHumanReceptionSurfaceError(ValueError):
    """Raised when a grounded reception cannot satisfy its R4 contract."""


@dataclass(frozen=True)
class GroundedReceptionClausePlan:
    """Body-free RR4 binding of one surface sentence to one or two Moves."""

    sentence_slot: int
    move_ids: tuple[str, ...]
    opening_strategy: str
    connector_policy: ReceptionConnectorPolicy
    terminal_predicate_family: str
    quote_budget: int
    speaker_presence: str


@dataclass(frozen=True)
class GroundedReceptionReferent:
    """Short anaphoric referent selected only from plan semantics."""

    kind: str
    text: str
    nucleus_ids: tuple[str, ...]
    evidence_span_ids: tuple[str, ...]
    source_anchor_used: bool = False


@dataclass(frozen=True)
class GroundedHumanResponsePredicate:
    """Act-specific predicate fragment, not a completed sentence."""

    terminal_predicate_kind: str
    object_particle: str
    predicate_fragment: str


@dataclass(frozen=True)
class GroundedHumanReceptionSurface:
    """Ephemeral validated reception surface and body-free diagnostics."""

    text: str
    terminal_predicate_kinds: tuple[str, ...]
    sentence_count: int
    referent_kind: str
    realized_reception_acts: tuple[GroundedReceptionAct, ...]
    realized_move_ids: tuple[str, ...]
    realized_move_roles: tuple[str, ...]
    move_predicate_families: tuple[str, ...]
    realized_clause_move_ids: tuple[tuple[str, ...], ...]
    grounded_nucleus_ids: tuple[str, ...]
    grounded_evidence_span_ids: tuple[str, ...]
    source_anchor_count: int
    source_anchor_max_visible_chars: int
    recovery_stage: ReceptionRecoveryStage


def reception_terminal_predicate_kind(act: GroundedReceptionAct) -> str:
    """Return the human-response terminal family owned by an act."""

    try:
        return _TERMINAL_PREDICATE_BY_ACT[act]
    except KeyError as exc:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_act:{act}"
        ) from exc


def reception_move_predicate_family(move: GroundedReceptionMovePlan) -> str:
    """Return the deterministic RR5 family for one role/act contribution."""

    try:
        return _MOVE_PREDICATE_FAMILY_BY_ROLE_ACT[
            (move.move_role, move.reception_act)
        ]
    except KeyError as exc:
        raise GroundedHumanReceptionSurfaceError(
            "unsupported_reception_move_role_act:"
            f"{move.move_role}:{move.reception_act}"
        ) from exc


def reception_active_moves(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionMovePlan, ...]:
    """Return the RR7 Move-preserving sequence for one recovery stage."""

    moves = tuple(reception_plan.moves)
    if not moves:
        raise GroundedHumanReceptionSurfaceError("human_reception_move_missing")
    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_recovery_stage:{recovery_stage}"
        )
    if any(move.move_role not in _MOVE_ROLE_ORDER for move in moves):
        raise GroundedHumanReceptionSurfaceError(
            "unsupported_reception_move_role"
        )
    for move in moves:
        reception_move_predicate_family(move)
    original_order = {move.move_id: index for index, move in enumerate(moves)}
    ordered = tuple(
        sorted(
            moves,
            key=lambda move: (
                _MOVE_ROLE_ORDER[move.move_role],
                original_order[move.move_id],
            ),
        )
    )
    if recovery_stage == "full":
        return ordered
    if recovery_stage == "minimal_grounded":
        if (
            reception_plan.depth_policy.level != "minimal"
            or reception_plan.depth_policy.safety_mode != "standard"
            or len(ordered) != 1
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_minimal_grounded_not_allowed"
            )
        return ordered

    retained = ordered
    if (
        recovery_stage == "optional_removed"
        and len(moves) == 3
        and not moves[2].required
    ):
        optional_move_id = moves[2].move_id
        retained = tuple(
            move for move in ordered if move.move_id != optional_move_id
        )
    required_ids = {
        move.move_id for move in reception_plan.moves if move.required
    }
    if not required_ids.issubset(move.move_id for move in retained):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_required_move_missing"
        )
    if len(retained) < reception_plan.depth_policy.min_realized_moves:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_move_budget_below_minimum"
        )
    retained_roles = {move.move_role for move in retained}
    retained_acts = {move.reception_act for move in retained}
    if (
        reception_plan.depth_policy.safety_mode == "self_denial_bounded"
        and (
            "felt_response" not in retained_roles
            or (
                any(
                    move.move_role == "bounded_counterposition"
                    for move in moves
                )
                and "bounded_counterposition" not in retained_roles
            )
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_safety_move_missing"
        )
    if (
        reception_plan.depth_policy.safety_mode == "help_seeking_bounded"
        and (
            "hold_help_seeking" not in retained_acts
            or "bounded_counterposition" not in retained_roles
        )
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_recovery_safety_move_missing"
        )
    return retained


def build_grounded_reception_clause_plans(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionClausePlan, ...]:
    """Bind active Moves to deterministic one- or two-Move sentence slots."""

    moves = reception_active_moves(reception_plan, recovery_stage)
    quote_available = bool(
        recovery_stage in {"full", "optional_removed"}
        and reception_plan.quote_policy.max_anchor_count > 0
    )
    move_groups: tuple[tuple[GroundedReceptionMovePlan, ...], ...] = tuple(
        (move,) for move in moves
    )
    if (
        recovery_stage == "integrated"
        and len(moves) == 3
        and reception_plan.depth_policy.max_moves_per_sentence >= 2
        and reception_plan.depth_policy.min_sentences <= 2
        and not any(
            move.move_role == "bounded_counterposition"
            for move in moves[:2]
        )
    ):
        move_groups = (moves[:2], moves[2:])

    clauses: list[GroundedReceptionClausePlan] = []
    for sentence_slot, group in enumerate(move_groups, start=1):
        opening_move = group[0]
        terminal_move = group[-1]
        quote_budget = int(
            quote_available
            and any(
                move.reference_mode == "short_anchor_if_ambiguous"
                for move in group
            )
        )
        if quote_budget:
            quote_available = False
        clauses.append(
            GroundedReceptionClausePlan(
                sentence_slot=sentence_slot,
                move_ids=tuple(move.move_id for move in group),
                opening_strategy=opening_move.surface_strategy,
                connector_policy=(
                    "contrast_safe"
                    if terminal_move.move_role == "bounded_counterposition"
                    else "none"
                ),
                terminal_predicate_family=reception_move_predicate_family(
                    terminal_move
                ),
                quote_budget=quote_budget,
                speaker_presence=terminal_move.speaker_presence,
            )
        )
    return tuple(clauses)


def reception_effective_sentence_budget(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[int, int]:
    """Return the RR7 sentence budget without weakening original depth."""

    if recovery_stage == "full":
        return (
            reception_plan.depth_policy.min_sentences,
            reception_plan.depth_policy.max_sentences,
        )
    clause_count = len(
        build_grounded_reception_clause_plans(
            reception_plan,
            recovery_stage,
        )
    )
    if reception_plan.depth_policy.level == "layered" and clause_count < 2:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_layered_recovery_collapsed"
        )
    safety_requires_two_sentences = bool(
        reception_plan.depth_policy.safety_mode == "help_seeking_bounded"
        or (
            reception_plan.depth_policy.safety_mode == "self_denial_bounded"
            and any(
                move.move_role == "bounded_counterposition"
                for move in reception_plan.moves
            )
        )
    )
    if safety_requires_two_sentences and clause_count < 2:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_safety_recovery_collapsed"
        )
    return clause_count, clause_count


def reception_active_acts(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionAct, ...]:
    """Return the acts retained by one reception-only recovery stage."""

    return tuple(
        move.reception_act
        for move in reception_active_moves(reception_plan, recovery_stage)
    )


def reception_effective_speaker_presence(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Keep explicit Emlis presence only while a bounded act is active."""

    return (
        "explicit_emlis"
        if "bounded_counter_self_denial"
        in reception_active_acts(reception_plan, recovery_stage)
        else "implicit_emlis"
    )


def reception_effective_reference_mode(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Return a recovery-safe reference mode for the retained acts."""

    if (
        "bounded_counter_self_denial"
        in reception_active_acts(reception_plan, recovery_stage)
    ):
        return "explicit_emlis_counterposition"
    if recovery_stage in {"integrated", "hedged", "minimal_grounded"}:
        return "anaphoric_first"
    if reception_plan.reference_mode == "explicit_emlis_counterposition":
        return "anaphoric_first"
    return reception_plan.reference_mode or "anaphoric_first"


def _dedupe(values) -> tuple[str, ...]:
    result: list[str] = []
    for value in values or ():
        item = str(value or "").strip()
        if item and item not in result:
            result.append(item)
    return tuple(result)


def _selected_nuclei(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedSemanticNucleus, ...]:
    nucleus_ids = _dedupe(
        (
            *reception_plan.target_nucleus_ids,
            *(
                ()
                if recovery_stage == "minimal_grounded"
                else reception_plan.support_nucleus_ids
            ),
        )
    )
    if recovery_stage == "minimal_grounded":
        nucleus_ids = nucleus_ids[:1]
    return tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in nucleus_ids
        if nucleus_id in nucleus_index
    )


def _semantic_attributes(
    nuclei: tuple[GroundedSemanticNucleus, ...],
) -> frozenset[str]:
    return frozenset(
        code
        for nucleus in nuclei
        for code in nucleus.semantic_frame.attribute_codes
    )


def _grounding_evidence_span_ids(
    nuclei: tuple[GroundedSemanticNucleus, ...],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[str, ...]:
    evidence_ids = _dedupe(
        span_id
        for nucleus in nuclei
        for span_id in nucleus.source_span_ids
    )
    return evidence_ids[:1] if recovery_stage == "minimal_grounded" else evidence_ids


def _compact_bound_anchor(candidate: str, max_chars: int) -> str:
    """Return a readable source-bound excerpt without a mid-token cutoff."""

    safe_boundary = re.compile(
        r"[、,.!?！？？をへ]|"
        r"(?<=[㐀-鿿])の(?=[㐀-鿿])|"
        r"(?<=[㐀-鿿])と(?=[㐀-鿿])"
    )
    suffixes = tuple(
        suffix
        for match in safe_boundary.finditer(candidate)
        if (
            2
            <= len(
                suffix := candidate[match.end() :].strip(
                    " 　、,。．."
                )
            )
            <= max_chars
        )
        and not suffix.startswith(("、", ",", "。", "."))
    )
    # Every returned value is one contiguous source substring.  This keeps
    # Japanese quotation marks truthful while still selecting a grammatical
    # suffix instead of cutting a token at the character limit.
    return max(suffixes, key=len, default="")


def _short_bound_anchor(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    allowed_nucleus_ids: tuple[str, ...],
    recovery_stage: ReceptionRecoveryStage,
    *,
    support_action_only: bool = False,
    allow_truncation: bool = True,
    compact_terminal_action: bool = False,
    require_headroom: bool = False,
) -> str:
    quote_policy = reception_plan.quote_policy
    if (
        reception_effective_reference_mode(reception_plan, recovery_stage)
        != "short_anchor_if_ambiguous"
        or quote_policy.max_anchor_count < 1
        or quote_policy.max_anchor_visible_chars < 2
    ):
        return ""
    ordered_ids = _dedupe(
        reception_plan.support_nucleus_ids
        if support_action_only
        else (
            *reception_plan.support_nucleus_ids,
            *reception_plan.target_nucleus_ids,
        )
    )
    allowed = set(allowed_nucleus_ids)
    for nucleus_id in ordered_ids:
        if nucleus_id not in allowed or nucleus_id not in nucleus_index:
            continue
        nucleus = nucleus_index[nucleus_id]
        if support_action_only and not {
            "operator:action",
            "semantic_role:concrete_action_evidence",
        } & frozenset(nucleus.semantic_frame.attribute_codes):
            continue
        for span_id in nucleus.source_span_ids:
            if resolver.unresolved_ids((span_id,)):
                continue
            candidate = re.sub(
                r"\s+",
                " ",
                resolver.resolve(span_id).raw_text,
            ).strip(" \u3000、,。．.")
            candidate = candidate.translate(_ANCHOR_DELETE_TRANSLATION).strip()
            if compact_terminal_action and candidate.endswith("した"):
                candidate = candidate[:-2].rstrip(" \u3000、,")
            if (
                len(candidate) < 2
                or _QUESTION_RE.search(candidate)
                or _POLICY_EXPLANATION_RE.search(candidate)
                or _ADVICE_RE.search(candidate)
                or _UNSUPPORTED_CLAIM_RE.search(candidate)
            ):
                continue
            max_chars = quote_policy.max_anchor_visible_chars
            if require_headroom and len(candidate) >= max_chars:
                continue
            if len(candidate) > max_chars:
                if not allow_truncation:
                    continue
                # A quoted anchor must remain a readable, verbatim source
                # span.  A raw prefix plus an ellipsis can stop mid-word and
                # sound machine-clipped. Prefer the longest source suffix
                # beginning at a punctuation/particle boundary; if none fits,
                # fall back to the semantic anaphor instead of fabricating a
                # clipped quote.
                candidate = _compact_bound_anchor(candidate, max_chars)
                if not candidate:
                    continue
            return candidate
    return ""


def resolve_grounded_reception_referent(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: ReceptionRecoveryStage = "full",
    act: GroundedReceptionAct | None = None,
    allow_short_anchor: bool = True,
) -> GroundedReceptionReferent:
    """Resolve an anaphor or one policy-bounded anchor from bound evidence."""

    reception_act = act or reception_plan.primary_reception_act
    if reception_act is None:
        raise GroundedHumanReceptionSurfaceError("human_reception_act_missing")
    selected = _selected_nuclei(
        reception_plan,
        nucleus_index,
        recovery_stage,
    )
    if not selected:
        raise GroundedHumanReceptionSurfaceError("human_reception_target_missing")
    attributes = _semantic_attributes(selected)
    target_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in reception_plan.target_nucleus_ids
        if nucleus_id in nucleus_index
    )
    target_attributes = _semantic_attributes(target_nuclei)
    support_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in reception_plan.support_nucleus_ids
        if nucleus_id in nucleus_index
    )
    support_attributes = _semantic_attributes(support_nuclei)
    kinds = {nucleus.kind for nucleus in selected}

    if reception_act == "stay_with_current_burden":
        if "lexical:no_new_sensation_family" in attributes:
            if "lexical:source_metaphor_present" in attributes:
                kind, text = "expressed_burden", "その言葉にある負荷"
            elif "detected_type:limit_signal" in attributes:
                kind, text = "current_suffering", "その苦しさ"
            else:
                kind, text = "current_distress", "そのつらさ"
        elif kinds & {"reaction", "state", "constraint"}:
            kind, text = "current_burden", "今のしんどさ"
        else:
            kind, text = "current_expression", "今ここに置かれた言葉"
    elif reception_act == "honor_concrete_effort":
        selected_ids = tuple(nucleus.nucleus_id for nucleus in selected)
        enacted_after_intention = bool(
            recovery_stage in {"full", "optional_removed"}
            and "operator:action" not in target_attributes
            and {
                "operator:action",
                "semantic_role:concrete_action_evidence",
            }
            & support_attributes
        )
        enacted_action_anchor = (
            _short_bound_anchor(
                reception_plan,
                nucleus_index,
                resolver,
                selected_ids,
                recovery_stage,
                support_action_only=True,
                allow_truncation=False,
                compact_terminal_action=True,
                require_headroom=True,
            )
            if enacted_after_intention
            and allow_short_anchor
            and recovery_stage in {"full", "optional_removed"}
            else ""
        )
        anchor = (
            _short_bound_anchor(
                reception_plan,
                nucleus_index,
                resolver,
                selected_ids,
                recovery_stage,
            )
            if allow_short_anchor
            and recovery_stage in {"full", "optional_removed"}
            and not enacted_after_intention
            else ""
        )
        if enacted_action_anchor:
            kind, text = (
                "anchored_enacted_effort",
                f"「{enacted_action_anchor}」という実際の行動",
            )
        elif enacted_after_intention and (
            "operator:positive_change" in target_attributes
        ):
            kind, text = (
                "next_step_effort",
                "次へつなぐために、実際に手を動かしたこと",
            )
        elif enacted_after_intention and (
            "detected_type:wish" in target_attributes
        ):
            kind, text = (
                "recorded_effort_toward_intention",
                "確かめたいことを、実際の記録へ移したこと",
            )
        elif enacted_after_intention:
            kind, text = (
                "enacted_effort_after_intention",
                "言葉だけで終わらせず、実際に動いたこと",
            )
        elif anchor:
            kind, text = (
                "anchored_concrete_effort",
                f"「{anchor}」という実際の行動",
            )
        elif "operator:action" in target_attributes:
            kind, text = "self_started_effort", "自分から実際に動いたこと"
        elif "action" in kinds or {
            "operator:action",
            "semantic_role:concrete_action_evidence",
        } & attributes:
            kind, text = "concrete_effort", "そこまで実際に動いたこと"
        else:
            kind, text = "grounded_effort", "その働きかけ"
    elif reception_act == "protect_retained_intention":
        if "wish" in kinds or "operator:wish" in attributes:
            kind, text = "retained_wish", "その願い"
        else:
            kind, text = "retained_intention", "大切にしたいもの"
    elif reception_act == "recognize_lived_change":
        if "action" in kinds and (
            "change" in kinds or "operator:change" in attributes
        ):
            kind, text = "lived_change", "自分で確かめてきた変化"
        elif "operator:action" in attributes:
            kind, text = "enacted_change", "動きとして確かめてきた変化"
        else:
            kind, text = "lived_change", "その変化"
    elif reception_act == "hold_help_seeking":
        if "operator:action" in target_attributes:
            kind, text = "help_seeking", "助けにつながるものを残したこと"
        elif "operator:help_seeking" in attributes:
            kind, text = "help_seeking_step", "助けへ向かう一歩を残したこと"
        else:
            kind, text = "protective_pause", "その踏みとどまり"
    elif reception_act == "bounded_counter_self_denial":
        if {
            "semantic_role:protective_or_limiting_refusal",
            "semantic_role:retained_intention",
        } & target_attributes:
            kind, text = (
                "felt_suffering_with_counterdirection",
                "今そこにある苦しさ",
            )
        else:
            kind, text = "felt_suffering", "その苦しさ自体"
    elif reception_act == "respect_words_placed":
        kind, text = "words_placed", "ここに言葉を置いたこと"
    else:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_act:{reception_act}"
        )

    evidence_span_ids = _grounding_evidence_span_ids(selected, recovery_stage)
    return GroundedReceptionReferent(
        kind=kind,
        text=text,
        nucleus_ids=tuple(nucleus.nucleus_id for nucleus in selected),
        evidence_span_ids=evidence_span_ids,
        source_anchor_used=bool(_QUOTE_RE.search(text)),
    )


def _scoped_reception_plan_for_move(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
) -> GroundedHumanReceptionPlan:
    """Create an ephemeral compatibility view for one Move's grounding."""

    return replace(
        reception_plan,
        moves=(move,),
        primary_reception_act=move.reception_act,
        secondary_reception_act=None,
        target_nucleus_ids=move.target_nucleus_ids,
        support_nucleus_ids=move.support_nucleus_ids,
        source_evidence_span_ids=move.source_evidence_span_ids,
        stance=_STANCE_BY_ACT[move.reception_act],
        speaker_presence=move.speaker_presence,
        reference_mode=move.reference_mode,
    )


def resolve_grounded_reception_move_referent(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    allow_short_anchor: bool,
) -> GroundedReceptionReferent:
    """Resolve one RR5 referent using only that Move's nucleus/evidence IDs."""

    return resolve_grounded_reception_referent(
        _scoped_reception_plan_for_move(reception_plan, move),
        nucleus_index,
        resolver,
        recovery_stage="full",
        act=move.reception_act,
        allow_short_anchor=allow_short_anchor,
    )


def _predicate_fragment(
    act: GroundedReceptionAct,
    recovery_stage: ReceptionRecoveryStage,
    *,
    referent_kind: str = "",
) -> GroundedHumanResponsePredicate:
    compact = recovery_stage in {"integrated", "minimal_grounded"}
    hedged = recovery_stage == "hedged"

    if act == "stay_with_current_burden":
        fragment = (
            "軽く扱わずに受け止めたいです"
            if hedged
            else "軽く扱わずに受け止めます"
            if compact
            else "軽く扱わず、ここで受け止めています"
            if referent_kind == "current_suffering"
            else "無理に小さくせず、受け止めています"
            if referent_kind == "current_burden"
            else "軽く扱わず、今ここにあるものとして受け止めています"
        )
    elif act == "honor_concrete_effort":
        fragment = (
            "大切なこととして受け止めたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "その手間ごと大切に受け止めています"
            if referent_kind
            in {
                "enacted_effort_after_intention",
                "anchored_enacted_effort",
                "next_step_effort",
                "recorded_effort_toward_intention",
            }
            else "簡単なこととして流さず、大切に受け止めています"
        )
    elif act == "protect_retained_intention":
        fragment = (
            "消さずに大切にしたいです"
            if hedged
            else "大切なものとして、なかったことにしません"
            if compact
            else "なかったことにせず、大切にしています"
        )
    elif act == "recognize_lived_change":
        fragment = (
            "大切な変化として感じたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "うれしく感じています"
        )
    elif act == "hold_help_seeking":
        fragment = (
            "大切な踏みとどまりとして受け止めたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "見過ごさず、大切な踏みとどまりとして受け止めています"
        )
    elif act == "respect_words_placed":
        fragment = (
            "大切に受け止めたいです"
            if hedged
            else "大切に受け止めます"
            if compact
            else "そのまま静かに、大切に受け止めています"
        )
    elif act == "bounded_counter_self_denial":
        fragment = (
            "否定せず、大切に受け止めたいです"
            if hedged
            else "否定せず、大切に受け止めます"
            if compact
            else "否定せず、大切に受け止めています"
        )
    else:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_act:{act}"
        )
    return GroundedHumanResponsePredicate(
        terminal_predicate_kind=reception_terminal_predicate_kind(act),
        object_particle="を",
        predicate_fragment=fragment,
    )


def _stance_adverb(
    stance: str | None,
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    if recovery_stage != "full":
        return ""
    return {
        "quiet_presence": "静かに",
        "warm_recognition": "",
        "gentle_respect": "そっと",
        "protective_presence": "大切に",
        "bounded_disagreement": "",
    }.get(stance or "", "")


def _join_object_predicate(
    referent: GroundedReceptionReferent,
    predicate: GroundedHumanResponsePredicate,
    *,
    stance_adverb: str,
    safety_prefix: str = "",
) -> str:
    predicate_text = predicate.predicate_fragment
    if stance_adverb == "あたたかく" and "うれしく感じ" in predicate_text:
        pass
    elif stance_adverb == "あたたかく" and "大切に受け止め" in predicate_text:
        predicate_text = predicate_text.replace(
            "大切に受け止め",
            "あたたかく、大切に受け止め",
            1,
        )
    elif stance_adverb == "そっと" and "そのまま静かに" in predicate_text:
        pass
    elif stance_adverb == "大切に":
        pass
    elif stance_adverb:
        for terminal in (
            "受け止めています",
            "受け止めたいです",
            "受け止めます",
            "大切にしています",
        ):
            if terminal in predicate_text:
                predicate_text = predicate_text.replace(
                    terminal,
                    f"{stance_adverb}{terminal}",
                    1,
                )
                break
    prefix = f"{safety_prefix}、" if safety_prefix else ""
    return (
        f"{prefix}{referent.text}{predicate.object_particle}、"
        f"{predicate_text}"
    )


def _bounded_counterposition_fragment(
    *,
    preserved_action: bool = False,
    preserved_help_step: bool = False,
    preserved_counterdirection: bool = False,
) -> str:
    if preserved_help_step and preserved_action:
        return (
            "Emlisには、助けへ向けて残したその行動までなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    if preserved_help_step:
        return (
            "Emlisには、助けへ向かうその一歩までなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    if preserved_action:
        return (
            "Emlisには、残したその行動までなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    if preserved_counterdirection:
        return (
            "Emlisには、その自己評価だけでは終わらない別の思いも見失わずに、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    return "Emlisには、その言葉だけであなた自身が決まるとは思えません"


def _move_attributes(
    move: GroundedReceptionMovePlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> frozenset[str]:
    return frozenset(
        code
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
        if nucleus_id in nucleus_index
        for code in nucleus_index[nucleus_id].semantic_frame.attribute_codes
    )


def _realize_full_move_sentence(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    referent: GroundedReceptionReferent,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
) -> str:
    """Realize one deterministic role/act contribution, never a case template."""

    role = move.move_role
    act = move.reception_act
    text = referent.text
    strategy = move.surface_strategy
    if _MOVE_ROLE_BY_SURFACE_STRATEGY.get(strategy) != role:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_move_surface_strategy_mismatch:"
            f"{role}:{strategy}"
        )

    if strategy == "explicit_emlis_counterposition":
        attributes = _move_attributes(move, nucleus_index)
        return _bounded_counterposition_fragment(
            preserved_help_step="operator:help_seeking" in attributes,
            preserved_action="operator:action" in attributes,
            preserved_counterdirection=bool(
                {
                    "operator:continuation",
                    "operator:refusal",
                    "semantic_role:protective_or_limiting_refusal",
                }
                & attributes
            ),
        )

    if strategy == "emlis_attention_first":
        if act == "honor_concrete_effort":
            return (
                f"{text}が特に印象に残り、"
                "その手間を大切に思います"
            )
        if act == "recognize_lived_change":
            return f"{text}が特に印象に残り、見過ごしたくないと感じます"
        if act == "protect_retained_intention":
            attributes = _move_attributes(move, nucleus_index)
            target_rank = next(
                (
                    index
                    for index, nucleus_id in enumerate(
                        reception_plan.observation_owned_nucleus_ids
                    )
                    if nucleus_id in move.target_nucleus_ids
                ),
                0,
            )
            if "operator:positive_change" in attributes:
                return (
                    "変化の中にも残っているその願いが、"
                    "なかったことにしたくないほど印象に残りました"
                )
            if target_rank >= 3:
                return (
                    f"{text}を、なかったことにせず、"
                    "見過ごさずにいたいです"
                )
            return f"{text}が、なかったことにしたくないほど印象に残りました"
        if act == "hold_help_seeking":
            return f"{text}が、見過ごしたくないものとして印象に残りました"
        if act == "stay_with_current_burden":
            return f"{text}を、見過ごしたくありません"
        return f"{text}が、静かに印象に残りました"

    if strategy == "referent_significance_first":
        if act == "honor_concrete_effort":
            return f"{text}を、軽いこととして流さず大切に思います"
        if act == "protect_retained_intention":
            return f"{text}を、消さずにそっと残しておきたいです"
        if act == "recognize_lived_change":
            return f"{text}を、軽い変化として扱いたくありません"
        if act == "hold_help_seeking":
            return f"{text}を、大切な一歩として残しておきたいです"
        return f"{text}を、軽く扱いたくありません"

    if strategy not in {"quiet_referent_first", "felt_response_first"}:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_surface_strategy:{strategy}"
        )

    if act == "stay_with_current_burden":
        if reception_plan.depth_policy.safety_mode == "self_denial_bounded":
            attributes = _move_attributes(move, nucleus_index)
            if "detected_type:value" in attributes:
                return (
                    "その自己評価にある苦しさを、否定せず、"
                    "軽く扱わず受け止めています"
                )
            return (
                "今そこにある苦しさを、否定せず、"
                "無理に小さくせず受け止めています"
            )
        return _join_object_predicate(
            referent,
            _predicate_fragment(
                act,
                "full",
                referent_kind=referent.kind,
            ),
            stance_adverb=_stance_adverb("quiet_presence", "full"),
        )
    if act == "recognize_lived_change":
        attributes = _move_attributes(move, nucleus_index)
        explicitly_valued = bool(
            {
                "semantic_role:explicit_evaluation",
                "semantic_role:positive_evaluation",
                "operator:value",
            }
            & attributes
        )
        if explicitly_valued:
            if "semantic_role:embedded_turn" in attributes:
                return f"{text}を、うれしい変化だと感じます"
            if "operator:contrast" in attributes:
                return f"{text}に、静かなうれしさを感じます"
            return f"{text}を、うれしく感じます"
        if "semantic_role:embedded_turn" in attributes:
            return f"{text}を、軽く扱わずにいたいです"
        if "operator:contrast" in attributes:
            return f"{text}を、見過ごしたくありません"
        if "semantic_role:explicit_result" in attributes:
            if "semantic_role:contrast_before" in attributes:
                return f"{text}を、見過ごさずにいたいです"
            return f"{text}を、軽いこととして流したくありません"
        return f"{text}を、見過ごさずにいたいです"
    if act == "protect_retained_intention":
        return f"{text}を、そっと大切にしたいです"
    if act == "honor_concrete_effort":
        return f"{text}を、その手間ごと大切に思います"
    if act == "hold_help_seeking":
        prefix = (
            "今ある苦しさを否定せず、"
            if reception_plan.depth_policy.safety_mode == "help_seeking_bounded"
            else ""
        )
        return f"{prefix}{text}を、大切な一歩として見過ごしたくありません"
    if act == "respect_words_placed":
        return f"{text}を、そのまま静かに大切に受け止めています"
    raise GroundedHumanReceptionSurfaceError(
        f"unsupported_reception_move_act:{act}"
    )


def _hedge_move_sentence(text: str) -> str:
    """Weaken assertion while retaining the Move's visible responsibility."""

    replacements = (
        ("見過ごしたくありません", "見過ごさずにいたいです"),
        ("見過ごしたくないと感じます", "見過ごさずにいたいと感じています"),
        ("扱いたくありません", "扱わずにいたいです"),
        (
            "その手間ごと大切に思います",
            "その手間ごと軽く扱わずにいたいです",
        ),
        (
            "その手間を大切に思います",
            "その手間を軽いこととして流さずにいたいです",
        ),
        (
            "うれしい変化だと感じます",
            "うれしい変化として受け止めたいです",
        ),
        ("受け止めています", "受け止めたいです"),
        ("受け止めます", "受け止めたいです"),
        ("印象に残りました", "印象に残っています"),
        ("うれしく感じます", "うれしく感じています"),
        ("うれしさを感じます", "うれしさを感じています"),
    )
    for source, replacement in replacements:
        if source in text:
            return text.replace(source, replacement, 1)
    return text


def _realize_move_sentence(
    reception_plan: GroundedHumanReceptionPlan,
    move: GroundedReceptionMovePlan,
    referent: GroundedReceptionReferent,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    recovery_stage: ReceptionRecoveryStage,
) -> str:
    """Realize every recovery stage from the same Move-owned surface path."""

    text = _realize_full_move_sentence(
        reception_plan,
        move,
        referent,
        nucleus_index,
    )
    return (
        _hedge_move_sentence(text)
        if recovery_stage == "hedged"
        and move.move_role != "bounded_counterposition"
        else text
    )


def _integrate_move_sentences(first: str, second: str) -> str:
    """Join two complete Move contributions without deleting either one."""

    lead_endings = (
        ("見過ごしたくないと感じます", "見過ごしたくないと感じ"),
        (
            "なかったことにしたくないほど印象に残りました",
            "なかったことにしたくないほど印象に残り",
        ),
        ("印象に残りました", "印象に残り"),
        ("見過ごしたくありません", "見過ごさず"),
        ("見過ごさずにいたいです", "見過ごさずにいたいと感じ"),
        ("残しておきたいです", "残しておきたく"),
        ("大切にしたいです", "大切にしたく"),
        ("扱いたくありません", "扱わずにいたく"),
        ("大切に思います", "大切に思い"),
        ("受け止めています", "受け止めており"),
        ("受け止めます", "受け止め"),
        ("感じます", "感じ"),
    )
    clean_first = first.rstrip("。")
    clean_second = second.rstrip("。")
    for ending, lead in lead_endings:
        if clean_first.endswith(ending):
            return f"{clean_first[:-len(ending)]}{lead}、{clean_second}"
    raise GroundedHumanReceptionSurfaceError(
        "human_reception_integrated_lead_unsupported"
    )


def _validate_clause_plan_binding(
    reception_plan: GroundedHumanReceptionPlan,
    clauses: Sequence[GroundedReceptionClausePlan],
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionMovePlan, ...]:
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    move_index = {move.move_id: move for move in active_moves}
    canonical_clauses = build_grounded_reception_clause_plans(
        reception_plan,
        recovery_stage,
    )
    if len(clauses) != len(canonical_clauses):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_count_mismatch"
        )
    if tuple(clause.sentence_slot for clause in clauses) != tuple(
        range(1, len(clauses) + 1)
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_slot_invalid"
        )
    flattened_ids = tuple(
        move_id for clause in clauses for move_id in clause.move_ids
    )
    expected_ids = tuple(move.move_id for move in active_moves)
    if len(flattened_ids) != len(set(flattened_ids)):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_move_duplicate"
        )
    if flattened_ids != expected_ids:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_move_binding_mismatch"
        )
    if sum(clause.quote_budget for clause in clauses) > (
        reception_plan.quote_policy.max_anchor_count
    ):
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_clause_quote_budget_exceeded"
        )
    for clause, canonical_clause in zip(clauses, canonical_clauses):
        if not 1 <= len(clause.move_ids) <= min(
            2,
            reception_plan.depth_policy.max_moves_per_sentence,
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_move_limit_invalid"
            )
        moves = tuple(move_index[move_id] for move_id in clause.move_ids)
        if any(
            move.move_role == "bounded_counterposition" for move in moves
        ) and len(moves) != 1:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_counterposition_clause_not_independent"
            )
        if len(moves) == 2 and recovery_stage != "integrated":
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_multi_move_clause_wrong_stage"
            )
        if len(moves) == 2 and len(clauses) < (
            reception_plan.depth_policy.min_sentences
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_integrated_depth_below_minimum"
            )
        opening_move = moves[0]
        terminal_move = moves[-1]
        if clause.terminal_predicate_family != reception_move_predicate_family(
            terminal_move
        ):
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_predicate_family_mismatch"
            )
        if clause.opening_strategy != opening_move.surface_strategy:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_opening_strategy_mismatch"
            )
        if clause.speaker_presence != terminal_move.speaker_presence:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_speaker_mismatch"
            )
        expected_connector = (
            "contrast_safe"
            if terminal_move.move_role == "bounded_counterposition"
            else "none"
        )
        if clause.connector_policy != expected_connector:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_connector_policy_mismatch"
            )
        if clause.quote_budget not in {0, 1}:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_quote_budget_invalid"
            )
        if clause.quote_budget != canonical_clause.quote_budget:
            raise GroundedHumanReceptionSurfaceError(
                "human_reception_clause_quote_budget_mismatch"
            )
    return active_moves


def _afterglow_clause(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> str | None:
    if (
        recovery_stage != "full"
        or reception_plan.afterglow_follow_element != "intent_affirmation"
        or reception_plan.secondary_reception_act is not None
        or reception_plan.sentence_policy.max_sentences < 2
    ):
        return None
    return "そこにある意志も、大切に受け止めています"


def _compose_reception_clauses(
    reception_plan: GroundedHumanReceptionPlan,
    primary_referent: GroundedReceptionReferent,
    secondary_referent: GroundedReceptionReferent | None,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    active_acts = reception_active_acts(reception_plan, recovery_stage)
    primary_act = active_acts[0]
    primary_predicate = _predicate_fragment(
        primary_act,
        recovery_stage,
        referent_kind=primary_referent.kind,
    )
    bounded_primary = primary_act == "bounded_counter_self_denial"
    secondary_act = active_acts[1] if len(active_acts) > 1 else None
    bounded_secondary = secondary_act == "bounded_counter_self_denial"
    stance = _stance_adverb(reception_plan.stance, recovery_stage)

    if bounded_primary:
        felt_clause = _join_object_predicate(
            primary_referent,
            primary_predicate,
            stance_adverb=stance,
        )
        if recovery_stage == "full":
            clauses = (
                felt_clause,
                _bounded_counterposition_fragment(
                    preserved_counterdirection=(
                        primary_referent.kind
                        == "felt_suffering_with_counterdirection"
                    )
                ),
            )
        else:
            clauses = (
                f"{felt_clause}が、{_bounded_counterposition_fragment()}",
            )
        terminal_kinds = (primary_predicate.terminal_predicate_kind,)
    else:
        safety_prefix = (
            "今ある苦しさを否定せず"
            if bounded_secondary
            else ""
        )
        primary_clause = _join_object_predicate(
            primary_referent,
            primary_predicate,
            stance_adverb=stance,
            safety_prefix=safety_prefix,
        )
        if secondary_act is not None:
            if bounded_secondary:
                secondary_clause = _bounded_counterposition_fragment(
                    preserved_action=(
                        primary_act == "hold_help_seeking"
                        and primary_referent.kind == "help_seeking"
                    ),
                    preserved_help_step=(
                        primary_act == "hold_help_seeking"
                        and primary_referent.kind == "help_seeking_step"
                    ),
                )
            else:
                if secondary_referent is None:
                    raise GroundedHumanReceptionSurfaceError(
                        "human_reception_secondary_referent_missing"
                    )
                secondary_predicate = _predicate_fragment(
                    secondary_act,
                    recovery_stage,
                    referent_kind=secondary_referent.kind,
                )
                secondary_clause = _join_object_predicate(
                    secondary_referent,
                    secondary_predicate,
                    stance_adverb=_stance_adverb(
                        _STANCE_BY_ACT[secondary_act],
                        recovery_stage,
                    ),
                )
            clauses = (primary_clause, secondary_clause)
            terminal_kinds = tuple(
                reception_terminal_predicate_kind(act)
                for act in active_acts
            )
        else:
            clauses = (primary_clause,)
            terminal_kinds = (primary_predicate.terminal_predicate_kind,)

    afterglow = _afterglow_clause(reception_plan, recovery_stage)
    if afterglow is not None and len(clauses) < reception_plan.sentence_policy.max_sentences:
        clauses = (*clauses, afterglow)
    return clauses, terminal_kinds


def _sentence_count(text: str) -> int:
    return len(
        tuple(
            part.strip()
            for part in _SENTENCE_END_RE.split(text)
            if part.strip()
        )
    )


def validate_grounded_human_reception_surface(
    surface: GroundedHumanReceptionSurface,
    reception_plan: GroundedHumanReceptionPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Validate the R4 surface without reconstructing observation meaning."""

    issues: list[str] = []
    if not surface.text.strip():
        issues.append("human_reception_surface_empty")
    actual_sentence_count = _sentence_count(surface.text)
    if surface.sentence_count != actual_sentence_count:
        issues.append("human_reception_sentence_diagnostic_mismatch")
    try:
        min_sentences, max_sentences = reception_effective_sentence_budget(
            reception_plan,
            surface.recovery_stage,
        )
    except GroundedHumanReceptionSurfaceError as exc:
        issues.append(str(exc))
        min_sentences, max_sentences = (1, 0)
    if not (
        min_sentences <= actual_sentence_count <= max_sentences
    ):
        issues.append("human_reception_sentence_budget_exceeded")
    if _QUESTION_RE.search(surface.text):
        issues.append("human_reception_question_forbidden")
    if _POLICY_EXPLANATION_RE.search(surface.text):
        issues.append("human_reception_policy_explanation_forbidden")
    if _ADVICE_RE.search(surface.text):
        issues.append("human_reception_advice_forbidden")
    if _UNSUPPORTED_CLAIM_RE.search(surface.text):
        issues.append("human_reception_unsupported_claim_forbidden")

    quote_values = tuple(_QUOTE_RE.findall(surface.text))
    quote_policy = reception_plan.quote_policy
    if len(quote_values) > quote_policy.max_anchor_count:
        issues.append("human_reception_quote_anchor_count_exceeded")
    if any(len(value) > quote_policy.max_anchor_visible_chars for value in quote_values):
        issues.append("human_reception_quote_anchor_length_exceeded")
    if surface.source_anchor_count != len(quote_values):
        issues.append("human_reception_quote_diagnostic_mismatch")
    max_visible = max((len(value) for value in quote_values), default=0)
    if surface.source_anchor_max_visible_chars != max_visible:
        issues.append("human_reception_quote_length_diagnostic_mismatch")

    if surface.recovery_stage not in _RECOVERY_STAGES:
        issues.append("unsupported_reception_recovery_stage")
        active_acts: tuple[GroundedReceptionAct, ...] = ()
        active_moves: tuple[GroundedReceptionMovePlan, ...] = ()
    else:
        active_moves = reception_active_moves(
            reception_plan,
            surface.recovery_stage,
        )
        active_acts = reception_active_acts(
            reception_plan,
            surface.recovery_stage,
        )
    if surface.realized_reception_acts != active_acts:
        issues.append("human_reception_realized_act_mismatch")
    expected_kinds = tuple(
        reception_terminal_predicate_kind(act) for act in active_acts
    )
    if surface.terminal_predicate_kinds != expected_kinds:
        issues.append("human_reception_terminal_predicate_mismatch")
    expected_move_ids = tuple(move.move_id for move in active_moves)
    expected_move_roles = tuple(move.move_role for move in active_moves)
    expected_move_families = tuple(
        reception_move_predicate_family(move) for move in active_moves
    )
    if surface.realized_move_ids != expected_move_ids:
        issues.append("human_reception_realized_move_mismatch")
    if surface.realized_move_roles != expected_move_roles:
        issues.append("human_reception_realized_move_role_mismatch")
    if surface.move_predicate_families != expected_move_families:
        issues.append("human_reception_move_predicate_family_mismatch")
    flattened_clause_moves = tuple(
        move_id
        for move_ids in surface.realized_clause_move_ids
        for move_id in move_ids
    )
    if flattened_clause_moves != expected_move_ids:
        issues.append("human_reception_realized_clause_move_mismatch")
    if any(
        not kind.startswith("human_response_")
        for kind in (
            *surface.terminal_predicate_kinds,
            *surface.move_predicate_families,
        )
    ):
        issues.append("human_reception_non_human_terminal_predicate")
    for act in active_acts:
        responsibility = _ACT_RESPONSIBILITY_RE[act]
        if not responsibility.search(surface.text):
            issues.append(f"human_reception_act_responsibility_missing:{act}")
    if active_acts and all(
        not _ACT_RESPONSIBILITY_RE[act].search(surface.text)
        for act in active_acts
    ):
        issues.append("human_reception_generic_suffix_forbidden")

    bounded_counterposition = "bounded_counter_self_denial" in active_acts
    if bounded_counterposition and "Emlis" not in surface.text:
        issues.append("self_denial_explicit_stance_missing")
    if not bounded_counterposition and "Emlis" in surface.text:
        issues.append("human_reception_implicit_speaker_overstated")
    allowed_nucleus_ids = {
        nucleus_id
        for move in active_moves
        for nucleus_id in (
            *move.target_nucleus_ids,
            *move.support_nucleus_ids,
        )
    }
    allowed_evidence_span_ids = {
        span_id
        for move in active_moves
        for span_id in move.source_evidence_span_ids
    }
    if (
        not surface.grounded_nucleus_ids
        or set(surface.grounded_nucleus_ids) != allowed_nucleus_ids
    ):
        issues.append("human_reception_surface_grounding_mismatch")
    if (
        not surface.grounded_evidence_span_ids
        or set(surface.grounded_evidence_span_ids)
        != allowed_evidence_span_ids
    ):
        issues.append("human_reception_surface_evidence_mismatch")
    if (
        any(move.required for move in reception_plan.moves)
        and not {
            move.move_id for move in reception_plan.moves if move.required
        }.issubset(surface.realized_move_ids)
    ):
        issues.append("human_reception_required_move_missing")
    if surface.recovery_stage == "minimal_grounded":
        if (
            len(surface.realized_reception_acts) != 1
            or len(surface.grounded_nucleus_ids) != 1
            or len(surface.grounded_evidence_span_ids) != 1
        ):
            issues.append("human_reception_minimal_grounding_invalid")
        if reception_plan.target_nucleus_ids and (
            surface.grounded_nucleus_ids[:1]
            != reception_plan.target_nucleus_ids[:1]
        ):
            issues.append("human_reception_minimal_target_mismatch")
    if resolver.unresolved_ids(surface.grounded_evidence_span_ids):
        issues.append("human_reception_source_evidence_unresolved")
    return _dedupe(issues)


def realize_grounded_human_reception(
    reception_plan: GroundedHumanReceptionPlan,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    *,
    recovery_stage: ReceptionRecoveryStage = "full",
    clause_plans: Sequence[GroundedReceptionClausePlan] | None = None,
) -> GroundedHumanReceptionSurface:
    """Realize deterministic Move contributions from one body-free ClausePlan."""

    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_recovery_stage:{recovery_stage}"
        )
    if not reception_plan.required:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_plan_present_but_not_required"
        )
    active_moves = reception_active_moves(reception_plan, recovery_stage)
    active_acts = tuple(move.reception_act for move in active_moves)
    resolved_clause_plans = tuple(
        clause_plans
        if clause_plans is not None
        else build_grounded_reception_clause_plans(
            reception_plan,
            recovery_stage,
        )
    )
    _validate_clause_plan_binding(
        reception_plan,
        resolved_clause_plans,
        recovery_stage,
    )
    move_index = {move.move_id: move for move in active_moves}

    clauses: list[str] = []
    referents: list[GroundedReceptionReferent] = []
    anchor_used = False
    for clause_plan in resolved_clause_plans:
        move_sentences: list[str] = []
        for move_id in clause_plan.move_ids:
            move = move_index[move_id]
            referent = resolve_grounded_reception_move_referent(
                reception_plan,
                move,
                nucleus_index,
                resolver,
                allow_short_anchor=bool(
                    clause_plan.quote_budget and not anchor_used
                ),
            )
            anchor_used = anchor_used or referent.source_anchor_used
            referents.append(referent)
            move_sentences.append(
                _realize_move_sentence(
                    reception_plan,
                    move,
                    referent,
                    nucleus_index,
                    recovery_stage,
                )
            )
        clauses.append(
            move_sentences[0]
            if len(move_sentences) == 1
            else _integrate_move_sentences(
                move_sentences[0],
                move_sentences[1],
            )
        )
    terminal_kinds = tuple(
        reception_terminal_predicate_kind(move.reception_act)
        for move in active_moves
    )

    text = "".join(f"{clause.rstrip('。')}。" for clause in clauses if clause.strip())
    quote_values = tuple(_QUOTE_RE.findall(text))
    surface = GroundedHumanReceptionSurface(
        text=text,
        terminal_predicate_kinds=terminal_kinds,
        sentence_count=_sentence_count(text),
        referent_kind="+".join(referent.kind for referent in referents),
        realized_reception_acts=active_acts,
        realized_move_ids=tuple(move.move_id for move in active_moves),
        realized_move_roles=tuple(move.move_role for move in active_moves),
        move_predicate_families=tuple(
            reception_move_predicate_family(move) for move in active_moves
        ),
        realized_clause_move_ids=tuple(
            clause.move_ids for clause in resolved_clause_plans
        ),
        grounded_nucleus_ids=_dedupe(
            nucleus_id
            for referent in referents
            for nucleus_id in referent.nucleus_ids
        ),
        grounded_evidence_span_ids=_dedupe(
            span_id
            for referent in referents
            for span_id in referent.evidence_span_ids
        ),
        source_anchor_count=len(quote_values),
        source_anchor_max_visible_chars=max(
            (len(value) for value in quote_values),
            default=0,
        ),
        recovery_stage=recovery_stage,
    )
    issues = validate_grounded_human_reception_surface(
        surface,
        reception_plan,
        resolver,
    )
    if issues:
        raise GroundedHumanReceptionSurfaceError(
            "invalid_grounded_human_reception_surface:" + ",".join(issues)
        )
    return surface


__all__ = [
    "ReceptionRecoveryStage",
    "ReceptionConnectorPolicy",
    "GroundedHumanReceptionSurfaceError",
    "GroundedReceptionClausePlan",
    "GroundedReceptionReferent",
    "GroundedHumanResponsePredicate",
    "GroundedHumanReceptionSurface",
    "reception_terminal_predicate_kind",
    "reception_move_predicate_family",
    "reception_active_moves",
    "reception_active_acts",
    "build_grounded_reception_clause_plans",
    "reception_effective_sentence_budget",
    "reception_effective_speaker_presence",
    "reception_effective_reference_mode",
    "resolve_grounded_reception_referent",
    "resolve_grounded_reception_move_referent",
    "validate_grounded_human_reception_surface",
    "realize_grounded_human_reception",
]
