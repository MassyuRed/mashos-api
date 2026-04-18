# -*- coding: utf-8 -*-
from __future__ import annotations

"""Observation kernel for EmlisAI.

The kernel turns raw world-model hints plus the derived user model into a small
set of accepted reply lines with sentence-bound evidence.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from emlis_ai_types import (
    DerivedUserModel,
    EmlisAICapabilityConfig,
    EvidenceRef,
    ObservationCandidate,
    ObservationDecision,
    ReplyLengthPlan,
    ReplyLine,
    SentenceEvidence,
    SourceBundle,
    StyleProfile,
    WorldModel,
)


@dataclass
class ObservationKernelInput:
    capability: EmlisAICapabilityConfig
    bundle: SourceBundle
    world_model: WorldModel
    style_profile: StyleProfile
    working_model: Optional[DerivedUserModel] = None


def _current_ref(bundle: SourceBundle) -> EvidenceRef:
    return EvidenceRef(
        kind="emotion",
        ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"),
        weight=1.0,
    )


def _safe_name(display_name: Optional[str]) -> str:
    raw = str(display_name or "").strip()
    return f"{raw}さん" if raw else ""


def _build_receive_text(bundle: SourceBundle, world_model: WorldModel, style_profile: StyleProfile) -> str:
    current = world_model.facts
    name = _safe_name(bundle.display_name)
    dominant = str(current.dominant_emotion or "").strip()

    if not current.has_memo_input:
        base = "言葉にならないほどなのですね。よかったら、あなたの言葉も少し聞かせてください。"
    elif dominant:
        if style_profile.family in {"analytical", "structured"}:
            base = f"今回は {dominant} が前に出ていて、その感じを少し整理したかったのですね。"
        else:
            base = f"今回は {dominant} が近くにあって、その気持ちを置いておきたかったのですね。"
    else:
        base = "今回は、いまの気持ちをそのまま置いておきたかったのですね。"

    use_name = bool(name) and not (bundle.greeting and bundle.greeting.first_in_slot)
    if not use_name:
        return base
    if "。" in base:
        first, rest = base.split("。", 1)
        return f"{name}、{first}。{rest}".strip()
    return f"{name}、{base}"


def _trigger_matches_current(bundle: SourceBundle, trigger: str) -> bool:
    raw_trigger = str(trigger or "").strip()
    if not raw_trigger:
        return False
    categories = {str(v).strip() for v in bundle.current_input.get("category") or [] if str(v).strip()} if isinstance(bundle.current_input.get("category"), list) else set()
    emotions = {str(v).strip() for v in bundle.current_input.get("emotions") or [] if str(v).strip()} if isinstance(bundle.current_input.get("emotions"), list) else set()
    memo_text = f"{str(bundle.current_input.get('memo') or '').strip()} {str(bundle.current_input.get('memo_action') or '').strip()}"
    return raw_trigger in categories or raw_trigger in emotions or raw_trigger in memo_text


def _recency_score(last_seen_at: Optional[str]) -> float:
    if not str(last_seen_at or "").strip():
        return 0.45
    return 0.80


def _candidate_rank(candidate: ObservationCandidate) -> float:
    return (
        float(candidate.confidence) * 0.45
        + float(candidate.alignment_score) * 0.30
        + float(candidate.recency_score) * 0.15
        - float(candidate.overclaim_risk) * 0.25
    )


def generate_observation_candidates(*, kernel_input: ObservationKernelInput) -> List[ObservationCandidate]:
    capability = kernel_input.capability
    bundle = kernel_input.bundle
    world_model = kernel_input.world_model
    style_profile = kernel_input.style_profile
    working_model = kernel_input.working_model
    candidates: List[ObservationCandidate] = []

    candidates.append(
        ObservationCandidate(
            candidate_key="receive.current",
            kind="receive",
            text=_build_receive_text(bundle, world_model, style_profile),
            evidence=[_current_ref(bundle)],
            confidence=0.98,
            recency_score=1.0,
            alignment_score=1.0,
            overclaim_risk=0.0,
            source_layers=["canonical_history"],
            notes={"source": "current_input"},
        )
    )

    for item in world_model.hypotheses:
        if item.key in {"same_day_change", "repeated_topic"}:
            candidates.append(
                ObservationCandidate(
                    candidate_key=f"continuity.{item.key}",
                    kind="continuity",
                    text=item.text,
                    evidence=list(item.evidence),
                    confidence=float(item.confidence),
                    recency_score=0.80,
                    alignment_score=0.70,
                    overclaim_risk=0.20,
                    source_layers=["canonical_history"],
                    notes={"hypothesis_key": item.key},
                )
            )
        elif item.key == "recovery_signal":
            candidates.append(
                ObservationCandidate(
                    candidate_key="change.recovery_signal",
                    kind="recovery",
                    text=item.text,
                    evidence=list(item.evidence),
                    confidence=float(item.confidence),
                    recency_score=0.78,
                    alignment_score=0.72,
                    overclaim_risk=0.28,
                    source_layers=["canonical_history"],
                    notes={"hypothesis_key": item.key},
                )
            )

    if working_model is not None and capability.interpretation_mode != "current_only":
        for entry in working_model.interpretive_frame.meaning_map[: capability.max_anchor_count or 0]:
            if not _trigger_matches_current(bundle, entry.trigger):
                continue
            candidates.append(
                ObservationCandidate(
                    candidate_key=f"interpretation.meaning_map.{entry.trigger}",
                    kind="interpretation",
                    text=f"この {entry.trigger} の流れは、最近も {entry.likely_meaning} と結びつきやすいようです。",
                    evidence=[_current_ref(bundle), *list(entry.evidence)[:2]],
                    confidence=max(0.45, float(entry.confidence)),
                    recency_score=_recency_score(entry.last_seen_at),
                    alignment_score=0.82,
                    overclaim_risk=0.34,
                    source_layers=["canonical_history", "derived_user_model"],
                    notes={"trigger": entry.trigger, "meaning": entry.likely_meaning},
                )
            )
        for anchor in working_model.open_topic_anchors[: capability.max_anchor_count or 0]:
            if not _trigger_matches_current(bundle, anchor.label):
                continue
            candidates.append(
                ObservationCandidate(
                    candidate_key=f"topic_anchor.{anchor.anchor_key}",
                    kind="topic_anchor",
                    text=f"この話題は、最近の流れの中でもまだ開いたまま残っていそうです。",
                    evidence=[_current_ref(bundle), *list(anchor.evidence)[:2]],
                    confidence=max(0.40, float(anchor.confidence)),
                    recency_score=_recency_score(anchor.last_seen_at),
                    alignment_score=0.72,
                    overclaim_risk=0.42,
                    source_layers=["canonical_history", "derived_user_model"],
                    notes={"anchor_key": anchor.anchor_key, "label": anchor.label},
                )
            )

        partner = working_model.interpretive_frame.partner_expectation
        pref = working_model.interpretive_frame.response_preference_cues
        partner_text = ""
        if capability.partner_mode == "on_advanced":
            if partner.wants_precise_observation:
                partner_text = "Emlis はこの流れを覚えたまま、今の受け取り方に合う形で返していきます。"
            elif partner.wants_non_judgmental_receive:
                partner_text = "Emlis は急がず、決めつけずに、この流れを受け取っていきます。"
            elif partner.wants_continuity:
                partner_text = "Emlis は前からの線も見ながら、今の気持ちに合う返し方をしていきます。"
        elif capability.partner_mode == "on_basic":
            if pref.prefers_continuity_reference:
                partner_text = "最近の流れも踏まえながら、今の気持ちに合う返し方をしていきますね。"
            else:
                partner_text = "今の気持ちと最近の流れをつないで受け取っていきますね。"
        if partner_text:
            candidates.append(
                ObservationCandidate(
                    candidate_key="partner.memory_aligned",
                    kind="partner_line",
                    text=partner_text,
                    evidence=[_current_ref(bundle), *list(pref.evidence)[:1], *list(partner.evidence)[:1]],
                    confidence=0.78 if capability.partner_mode == "on_advanced" else 0.70,
                    recency_score=0.65,
                    alignment_score=0.76,
                    overclaim_risk=0.18,
                    source_layers=["canonical_history", "derived_user_model"],
                    notes={"partner_mode": capability.partner_mode},
                )
            )
    else:
        if capability.partner_mode != "off":
            candidates.append(
                ObservationCandidate(
                    candidate_key="partner.base",
                    kind="partner_line",
                    text="ここから先も、今の気持ちに合う返し方をしていきますね。",
                    evidence=[_current_ref(bundle)],
                    confidence=0.62,
                    recency_score=0.55,
                    alignment_score=0.55,
                    overclaim_risk=0.10,
                    source_layers=["canonical_history"],
                    notes={"partner_mode": capability.partner_mode},
                )
            )
    return candidates


def apply_interpretive_alignment(
    candidates: List[ObservationCandidate],
    *,
    kernel_input: ObservationKernelInput,
) -> List[ObservationCandidate]:
    capability = kernel_input.capability
    bundle = kernel_input.bundle
    working_model = kernel_input.working_model
    if working_model is None:
        return candidates

    pref = working_model.interpretive_frame.response_preference_cues
    for candidate in candidates:
        if candidate.kind == "receive" and pref.prefers_receive_first:
            candidate.alignment_score = max(candidate.alignment_score, 0.95)
        if candidate.kind in {"continuity", "topic_anchor"} and pref.prefers_continuity_reference:
            candidate.alignment_score = max(candidate.alignment_score, 0.82)
        if candidate.kind == "interpretation" and capability.interpretation_mode == "precision_aligned":
            candidate.alignment_score = min(1.0, max(candidate.alignment_score, 0.88))
            candidate.overclaim_risk = max(0.0, candidate.overclaim_risk - 0.08)
        if candidate.kind == "interpretation" and not _trigger_matches_current(bundle, candidate.notes.get("trigger")):
            candidate.overclaim_risk = min(1.0, candidate.overclaim_risk + 0.25)
    return candidates


def suppress_overclaiming(
    candidates: List[ObservationCandidate],
    *,
    kernel_input: ObservationKernelInput,
) -> Tuple[List[ObservationCandidate], List[ObservationCandidate], List[str]]:
    capability = kernel_input.capability
    kept: List[ObservationCandidate] = []
    rejected: List[ObservationCandidate] = []
    unknowns: List[str] = []

    for candidate in candidates:
        if not candidate.text or not candidate.evidence:
            rejected.append(candidate)
            continue
        if capability.interpretation_mode == "current_only" and "derived_user_model" in candidate.source_layers:
            rejected.append(candidate)
            continue
        if candidate.kind in {"interpretation", "topic_anchor"} and candidate.alignment_score < 0.45:
            rejected.append(candidate)
            unknowns.append("interpretation_alignment_weak")
            continue
        if candidate.kind in {"change", "recovery"} and candidate.confidence < 0.55:
            rejected.append(candidate)
            continue
        if candidate.overclaim_risk >= 0.80:
            rejected.append(candidate)
            unknowns.append(f"overclaim_suppressed:{candidate.kind}")
            continue
        kept.append(candidate)
    return kept, rejected, unknowns


def decide_reply_length_plan(
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
) -> ReplyLengthPlan:
    input_effort_score = float(bundle.input_effort.get("effort_score") or 0.0)
    memory_richness_score = float(bundle.memory_richness.get("history_density_score") or 0.0)

    base_lines = 1 if capability.tier == "free" else 2
    bonus = 0
    if input_effort_score >= 0.45:
        bonus += 1
    if memory_richness_score >= 0.45 and capability.history_mode != "none":
        bonus += 1
    if capability.tier == "premium" and input_effort_score >= 0.75 and memory_richness_score >= 0.70:
        bonus += 1

    max_lines = min(int(capability.max_reply_lines or 3), base_lines + bonus)
    max_lines = max(1, max_lines)

    return ReplyLengthPlan(
        mode=capability.reply_length_mode,
        max_lines=max_lines,
        reason="input_effort_and_memory_richness",
        input_effort_score=input_effort_score,
        memory_richness_score=memory_richness_score,
    )


def _pick_best(candidates: List[ObservationCandidate], *, kind: str) -> Optional[ObservationCandidate]:
    filtered = [item for item in candidates if item.kind == kind]
    if not filtered:
        return None
    return sorted(filtered, key=_candidate_rank, reverse=True)[0]


def _pick_best_among(candidates: List[ObservationCandidate], *, kinds: List[str]) -> Optional[ObservationCandidate]:
    filtered = [item for item in candidates if item.kind in set(kinds)]
    if not filtered:
        return None
    return sorted(filtered, key=_candidate_rank, reverse=True)[0]


def build_reply_lines(
    accepted_candidates: List[ObservationCandidate],
    *,
    reply_length_plan: ReplyLengthPlan,
) -> List[ReplyLine]:
    reply_lines: List[ReplyLine] = []
    for candidate in accepted_candidates[: max(0, int(reply_length_plan.max_lines))]:
        reply_lines.append(
            ReplyLine(
                key=candidate.kind,
                text=str(candidate.text or "").strip(),
                sentence_evidence=SentenceEvidence(line_key=candidate.kind, evidence=list(candidate.evidence)),
                candidate_key=candidate.candidate_key,
            )
        )
    return reply_lines


def arbitrate_candidates(
    candidates: List[ObservationCandidate],
    rejected_candidates: List[ObservationCandidate],
    *,
    kernel_input: ObservationKernelInput,
    unknowns: List[str],
) -> ObservationDecision:
    capability = kernel_input.capability
    reply_length_plan = decide_reply_length_plan(capability, kernel_input.bundle)

    accepted: List[ObservationCandidate] = []
    receive = _pick_best(candidates, kind="receive")
    if receive is not None:
        accepted.append(receive)

    primary_middle = _pick_best_among(candidates, kinds=["interpretation", "continuity", "topic_anchor"])
    if primary_middle is not None:
        accepted.append(primary_middle)

    if capability.tier == "premium" and reply_length_plan.max_lines >= 4:
        secondary_middle = _pick_best_among(
            [item for item in candidates if item is not primary_middle],
            kinds=["interpretation", "continuity", "topic_anchor"],
        )
        if secondary_middle is not None:
            accepted.append(secondary_middle)

    change_or_recovery = _pick_best_among(candidates, kinds=["change", "recovery"])
    if change_or_recovery is not None and len(accepted) < reply_length_plan.max_lines:
        accepted.append(change_or_recovery)

    partner_line = _pick_best(candidates, kind="partner_line")
    if partner_line is not None and len(accepted) < reply_length_plan.max_lines:
        accepted.append(partner_line)

    accepted = [item for idx, item in enumerate(accepted) if item is not None and item not in accepted[:idx]]
    reply_lines = build_reply_lines(accepted, reply_length_plan=reply_length_plan)

    return ObservationDecision(
        accepted_candidates=accepted,
        rejected_candidates=rejected_candidates,
        unknowns=list(unknowns),
        conflicts=list(kernel_input.world_model.conflicts),
        reply_lines=reply_lines,
        reply_length_plan=reply_length_plan,
        debug={
            "candidate_count": len(candidates),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected_candidates),
        },
    )


def run_emlis_ai_observation_kernel(
    *,
    kernel_input: ObservationKernelInput,
) -> ObservationDecision:
    candidates = generate_observation_candidates(kernel_input=kernel_input)
    candidates = apply_interpretive_alignment(candidates, kernel_input=kernel_input)
    kept, rejected, unknowns = suppress_overclaiming(candidates, kernel_input=kernel_input)
    decision = arbitrate_candidates(
        kept,
        rejected,
        kernel_input=kernel_input,
        unknowns=[*kernel_input.world_model.unknowns, *unknowns],
    )
    return decision
