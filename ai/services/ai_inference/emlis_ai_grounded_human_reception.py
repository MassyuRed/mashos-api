# -*- coding: utf-8 -*-
from __future__ import annotations

"""Functional realizer for the distinct Grounded Human Reception layer.

The realizer consumes the body-free reception plan produced by I2/R2.  It
does not use case ids, source bodies, relations, or a completed observation as
selection cues.  It may resolve one policy-bounded source anchor only after an
act is selected.  Surface text is composed from a semantic referent, an
act-specific human response predicate, speaker/stance grammar, and at most one
afterglow.
"""

from collections.abc import Mapping
from dataclasses import dataclass
import re
from typing import Final, Literal

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_observation_plan import (
    GroundedHumanReceptionPlan,
    GroundedReceptionAct,
    GroundedSemanticNucleus,
)


ReceptionRecoveryStage = Literal[
    "full",
    "optional_removed",
    "integrated",
    "hedged",
    "minimal_grounded",
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
        r".{0,48}(?:大切|受け止)"
    ),
    "protect_retained_intention": re.compile(
        r"(?:願い|大切にしたいもの).{0,40}(?:大切|なかったこと|消さず)"
    ),
    "recognize_lived_change": re.compile(r"変化.{0,40}(?:感じ|受け止)"),
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


def reception_active_acts(
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: ReceptionRecoveryStage,
) -> tuple[GroundedReceptionAct, ...]:
    """Return the acts retained by one reception-only recovery stage."""

    primary = reception_plan.primary_reception_act
    if primary is None:
        raise GroundedHumanReceptionSurfaceError("human_reception_act_missing")
    return (
        primary,
        *(
            (reception_plan.secondary_reception_act,)
            if recovery_stage == "full"
            and reception_plan.secondary_reception_act is not None
            else ()
        ),
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
                candidate = candidate[: max_chars - 1].rstrip("、,") + "…"
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
            "Emlisには、そこに残した向きまでなかったことにして、"
            "その言葉だけであなた自身が決まるとは思えません"
        )
    return "Emlisには、その言葉だけであなた自身が決まるとは思えません"


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
    sentence_policy = reception_plan.sentence_policy
    actual_sentence_count = _sentence_count(surface.text)
    if surface.sentence_count != actual_sentence_count:
        issues.append("human_reception_sentence_diagnostic_mismatch")
    if not (
        sentence_policy.min_sentences
        <= actual_sentence_count
        <= sentence_policy.max_sentences
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
    else:
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
    if any(
        not kind.startswith("human_response_")
        for kind in surface.terminal_predicate_kinds
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
    allowed_nucleus_ids = set(
        (
            *reception_plan.target_nucleus_ids,
            *reception_plan.support_nucleus_ids,
        )
    )
    if (
        not surface.grounded_nucleus_ids
        or not set(surface.grounded_nucleus_ids).issubset(allowed_nucleus_ids)
    ):
        issues.append("human_reception_surface_grounding_mismatch")
    if (
        not surface.grounded_evidence_span_ids
        or not set(surface.grounded_evidence_span_ids).issubset(
            reception_plan.source_evidence_span_ids
        )
    ):
        issues.append("human_reception_surface_evidence_mismatch")
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
) -> GroundedHumanReceptionSurface:
    """Realize one deterministic, grounded, distinct reception contribution."""

    if recovery_stage not in _RECOVERY_STAGES:
        raise GroundedHumanReceptionSurfaceError(
            f"unsupported_reception_recovery_stage:{recovery_stage}"
        )
    if not reception_plan.required:
        raise GroundedHumanReceptionSurfaceError(
            "human_reception_plan_present_but_not_required"
        )
    active_acts = reception_active_acts(reception_plan, recovery_stage)
    primary_referent = resolve_grounded_reception_referent(
        reception_plan,
        nucleus_index,
        resolver,
        recovery_stage=recovery_stage,
        act=active_acts[0],
    )
    secondary_referent = None
    if len(active_acts) > 1 and active_acts[1] != "bounded_counter_self_denial":
        secondary_referent = resolve_grounded_reception_referent(
            reception_plan,
            nucleus_index,
            resolver,
            recovery_stage=recovery_stage,
            act=active_acts[1],
            allow_short_anchor=not primary_referent.source_anchor_used,
        )
    clauses, terminal_kinds = _compose_reception_clauses(
        reception_plan,
        primary_referent,
        secondary_referent,
        recovery_stage,
    )
    text = "".join(f"{clause.rstrip('。')}。" for clause in clauses if clause.strip())
    quote_values = tuple(_QUOTE_RE.findall(text))
    surface = GroundedHumanReceptionSurface(
        text=text,
        terminal_predicate_kinds=terminal_kinds,
        sentence_count=_sentence_count(text),
        referent_kind=(
            primary_referent.kind
            if secondary_referent is None
            else f"{primary_referent.kind}+{secondary_referent.kind}"
        ),
        realized_reception_acts=active_acts,
        grounded_nucleus_ids=_dedupe(
            (
                *primary_referent.nucleus_ids,
                *(
                    secondary_referent.nucleus_ids
                    if secondary_referent is not None
                    else ()
                ),
            )
        ),
        grounded_evidence_span_ids=_dedupe(
            (
                *primary_referent.evidence_span_ids,
                *(
                    secondary_referent.evidence_span_ids
                    if secondary_referent is not None
                    else ()
                ),
            )
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
    "GroundedHumanReceptionSurfaceError",
    "GroundedReceptionReferent",
    "GroundedHumanResponsePredicate",
    "GroundedHumanReceptionSurface",
    "reception_terminal_predicate_kind",
    "reception_active_acts",
    "reception_effective_speaker_presence",
    "reception_effective_reference_mode",
    "resolve_grounded_reception_referent",
    "validate_grounded_human_reception_surface",
    "realize_grounded_human_reception",
]
