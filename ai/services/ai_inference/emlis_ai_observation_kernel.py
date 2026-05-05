# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic observation kernel for EmlisAI.

This kernel must not contain sample-specific answer templates.  It receives the
current-input world model and composes grounded reply candidates from generic
meaning blocks, shaped phrases, selected emotions, and allowed memory signals.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from emlis_ai_types import (
    DerivedUserModel,
    EmlisAICapabilityConfig,
    EvidenceRef,
    InputMeaningBlock,
    MeaningCoveragePlan,
    ObservationCandidate,
    ObservationDecision,
    ReplyLengthPlan,
    ReplyLine,
    SentenceEvidence,
    ShapedUserPhrase,
    SourceBundle,
    StyleProfile,
    WorldModel,
)
from emlis_ai_input_meaning_block_service import selected_meaning_blocks_for_reply
from emlis_ai_phrase_shaping_service import safe_phrases


@dataclass
class ObservationKernelInput:
    capability: EmlisAICapabilityConfig
    bundle: SourceBundle
    world_model: WorldModel
    style_profile: StyleProfile
    working_model: Optional[DerivedUserModel] = None


def _clean(value) -> str:
    return str(value or "").strip()


def _current_ref(bundle: SourceBundle) -> EvidenceRef:
    return EvidenceRef(kind="emotion", ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"), weight=1.0)


def _selected_emotion_text(world_model: WorldModel) -> str:
    selected = list(world_model.facts.selected_emotions or [])
    labels = [str(getattr(item, "type", "") or "").strip() for item in selected if str(getattr(item, "type", "") or "").strip()]
    if not labels:
        labels = [str(item or "").strip() for item in list(world_model.facts.current_emotion_labels or []) if str(item or "").strip()]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    return "、".join(labels[:-1]) + "、そして" + labels[-1]


def _meaning_blocks(world_model: Optional[WorldModel]) -> List[InputMeaningBlock]:
    if world_model is None:
        return []
    return list(getattr(world_model.facts, "meaning_blocks", []) or [])


def _meaning_plan(world_model: Optional[WorldModel]) -> Optional[MeaningCoveragePlan]:
    if world_model is None:
        return None
    return getattr(world_model.facts, "meaning_coverage_plan", None)


def _clear_long_input(world_model: Optional[WorldModel]) -> bool:
    plan = _meaning_plan(world_model)
    return bool(plan is not None and getattr(plan, "clear_long_input", False))


def _safe_phrases(world_model: Optional[WorldModel]) -> List[ShapedUserPhrase]:
    if world_model is None:
        return []
    return safe_phrases(list(getattr(world_model.facts, "shaped_user_phrases", []) or []))


def _evidence_from_blocks(blocks: List[InputMeaningBlock], fallback: EvidenceRef) -> List[EvidenceRef]:
    refs: List[EvidenceRef] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks:
        for ref in list(getattr(block, "evidence", []) or []):
            key = (str(getattr(ref, "kind", "") or ""), str(getattr(ref, "ref_id", "") or ""))
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)
    return refs or [fallback]



def _as_topic(text: str) -> str:
    clean = _clean(text).rstrip("。")
    if not clean:
        return ""
    if clean.endswith(("こと", "気持ち", "願い", "状態", "感覚", "不安", "怖さ", "思い")):
        return clean
    return f"{clean}こと"

def _opening_text(world_model: WorldModel, blocks: List[InputMeaningBlock], phrases: List[ShapedUserPhrase]) -> str:
    arc = getattr(world_model.facts, "reply_narrative_arc", None)
    opening = _clean(getattr(arc, "opening_thesis", ""))
    if opening:
        return opening
    if blocks:
        first = _clean(blocks[0].summary).rstrip("。")
        if len(blocks) >= 2:
            second = _clean(blocks[1].summary).rstrip("。")
            return f"あなたは、{_as_topic(first)}だけでなく、{_as_topic(second)}も一緒に言葉にしているのですね。"
        return f"あなたは、{_as_topic(first)}を、今ここに置こうとしているのですね。"
    if phrases:
        first = _clean(phrases[0].sentence_fragment or phrases[0].phrase).rstrip("。")
        return f"あなたは、{_as_topic(first)}を言葉にしようとしていたのですね。"
    labels = _selected_emotion_text(world_model)
    if labels:
        return f"今日は、{labels}が近くにあったのですね。"
    return "今日は、言葉にしきれない気持ちを少し置いておきたかったのですね。"


def _block_line(block: InputMeaningBlock, *, index: int) -> str:
    summary = _clean(getattr(block, "summary", "")).rstrip("。")
    role = str(getattr(block, "role", "") or "")
    if not summary:
        return ""
    if role in {"self_suppression", "burden_avoidance", "self_view", "relationship_or_others"}:
        return f"その背景には、{summary}流れもありました。"
    if role in {"limit_or_exhaustion", "fear_or_disappointment", "sadness_or_pain", "anger_or_frustration"}:
        return f"そこには、{summary}感覚もありました。"
    if role in {"support_need", "self_protection", "effort_direction", "wish_or_hope", "relief_source"}:
        return f"同時に、{_as_topic(summary)}も大切な場所として見えています。"
    if role == "dual_feeling":
        return f"その中で、{_as_topic(summary)}が重なっていました。"
    return f"そこには、{_as_topic(summary)}も含まれていました。"


def _phrase_line(phrase: ShapedUserPhrase, *, index: int) -> str:
    fragment = _clean(getattr(phrase, "sentence_fragment", "") or getattr(phrase, "phrase", "")).rstrip("。")
    role = str(getattr(phrase, "role", "") or "")
    if not fragment:
        return ""
    if index == 0:
        return f"あなたは、{_as_topic(fragment)}を、少しでも言葉にしたかったのですね。"
    if role in {"fear_or_disappointment", "sadness_or_pain", "anger_or_frustration"}:
        return f"そこには、{fragment}感覚も近くにありました。"
    if role in {"wish", "wish_or_hope", "support_need", "effort_direction"}:
        return f"同時に、{_as_topic(fragment)}も大切な場所としてありました。"
    return f"そこには、{_as_topic(fragment)}も一緒にありました。"


def _presence_text(world_model: WorldModel, blocks: List[InputMeaningBlock], phrases: List[ShapedUserPhrase]) -> str:
    roles = {str(getattr(item, "role", "") or "") for item in list(blocks or []) + list(phrases or [])}
    if {"self_suppression", "self_protection", "support_need", "burden_avoidance"} & roles:
        return "ここでは、抑えてきた気持ちも、自分を守ろうとしている気持ちも、どちらも大切に扱います。"
    if {"wish_or_hope", "fear_or_disappointment", "effort_direction", "wish"} & roles:
        return "ここでは、願いも怖さも、今できることを大切にしたい気持ちも、小さく扱いません。"
    if {"anger_or_frustration", "sadness_or_pain", "relief_source"} & roles:
        return "ここでは、しんどさも、怒りも、少し楽になりたい気持ちも、雑に扱いません。"
    labels = _selected_emotion_text(world_model)
    if "怒り" in labels and "悲しみ" in labels:
        return "ここでは、悲しみも怒りも、無理にきれいにしなくて大丈夫です。"
    return "ここに置いてくれた言葉を、Emlisは軽く扱いません。"


def _candidate(key: str, kind: str, text: str, evidence: List[EvidenceRef], confidence: float = 0.86) -> ObservationCandidate:
    return ObservationCandidate(
        candidate_key=key,
        kind=kind,  # type: ignore[arg-type]
        text=_clean(text),
        evidence=evidence,
        confidence=confidence,
        recency_score=1.0,
        alignment_score=0.88,
        overclaim_risk=0.05,
        source_layers=["canonical_history"],
        notes={"genericized": True},
    )


def generate_observation_candidates(*, kernel_input: ObservationKernelInput) -> List[ObservationCandidate]:
    bundle = kernel_input.bundle
    world_model = kernel_input.world_model
    current_ref = _current_ref(bundle)
    all_blocks = _meaning_blocks(world_model)
    plan = _meaning_plan(world_model)
    selected_blocks = selected_meaning_blocks_for_reply(meaning_blocks=all_blocks, coverage_plan=plan)
    phrases = _safe_phrases(world_model)
    candidates: List[ObservationCandidate] = []

    candidates.append(_candidate("receive.current", "receive", _opening_text(world_model, selected_blocks, phrases), [current_ref], confidence=0.98))

    if selected_blocks:
        for idx, block in enumerate(selected_blocks[:8]):
            line = _block_line(block, index=idx)
            if line:
                candidates.append(_candidate(f"word_reflection.meaning.{idx:02d}", "word_reflection", line, _evidence_from_blocks([block], current_ref), confidence=0.90))
    else:
        for idx, phrase in enumerate(phrases[:3]):
            line = _phrase_line(phrase, index=idx)
            if line:
                candidates.append(_candidate(f"word_reflection.phrase.{idx:02d}", "word_reflection", line, list(getattr(phrase, "evidence", []) or [current_ref]), confidence=0.82))

    selected_text = _selected_emotion_text(world_model)
    if selected_text and "、" in selected_text:
        candidates.append(_candidate("selected_emotions.current", "selected_emotions", f"{selected_text}が重なっていたことも、分けずに見ておきたいところです。", [current_ref], confidence=0.82))
    elif selected_text:
        candidates.append(_candidate("emotion_response.current", "emotion_response", f"その{selected_text}は、軽く片づけられない場所にあったのだと思います。", [current_ref], confidence=0.78))

    if kernel_input.capability.history_mode != "none":
        for item in world_model.hypotheses:
            text = _clean(getattr(item, "text", ""))
            if not text:
                continue
            candidates.append(_candidate(f"continuity.{item.key}", "continuity", text, list(getattr(item, "evidence", []) or [current_ref]), confidence=max(0.45, float(getattr(item, "confidence", 0.0) or 0.0))))

    candidates.append(_candidate("receiving_close.default", "receiving_close", _presence_text(world_model, selected_blocks, phrases), [current_ref], confidence=0.92))
    return candidates


def apply_interpretive_alignment(candidates: List[ObservationCandidate], *, kernel_input: ObservationKernelInput) -> List[ObservationCandidate]:
    # Keep the hook for compatibility. Alignment is intentionally conservative;
    # no example-specific boost is applied.
    return candidates


def suppress_overclaiming(candidates: List[ObservationCandidate], *, kernel_input: ObservationKernelInput) -> Tuple[List[ObservationCandidate], List[ObservationCandidate], List[str]]:
    kept: List[ObservationCandidate] = []
    rejected: List[ObservationCandidate] = []
    unknowns: List[str] = []
    for candidate in candidates:
        if not candidate.text or not candidate.evidence:
            rejected.append(candidate)
            continue
        if candidate.overclaim_risk >= 0.80:
            rejected.append(candidate)
            unknowns.append(f"overclaim_suppressed:{candidate.kind}")
            continue
        if kernel_input.capability.interpretation_mode == "current_only" and "derived_user_model" in candidate.source_layers:
            rejected.append(candidate)
            continue
        kept.append(candidate)
    return kept, rejected, unknowns


def decide_reply_length_plan(*, capability: EmlisAICapabilityConfig, bundle: SourceBundle, world_model: WorldModel, working_model: Optional[DerivedUserModel]) -> ReplyLengthPlan:
    memo_char_count = int(bundle.input_effort.get("memo_char_count") or 0) + int(bundle.input_effort.get("memo_action_char_count") or 0)
    input_effort_score = float(bundle.input_effort.get("effort_score") or 0.0)
    memory_richness_score = float(bundle.memory_richness.get("history_density_score") or 0.0)
    blocks = _meaning_blocks(world_model)
    plan = _meaning_plan(world_model)
    clear_long = bool(plan is not None and getattr(plan, "clear_long_input", False))
    selected_count = len(getattr(plan, "selected_block_keys", []) or []) if plan is not None else 0
    tier_ceiling = max(2, int(capability.max_reply_lines or 3))
    if clear_long:
        tier_ceiling = max(tier_ceiling, 10 if capability.tier == "free" else 12 if capability.tier == "plus" else 14)
    target = 2
    if memo_char_count:
        target += 1
    if memo_char_count >= 120:
        target += 1
    if clear_long:
        target = max(target, 2 + min(max(selected_count, len(blocks)), 8))
    history_usable = bool(capability.history_mode != "none" and (bundle.same_day_recent_inputs or bundle.similar_inputs or memory_richness_score >= 0.28))
    if history_usable:
        target += 1
    evidence_ceiling = max(2, 2 + min(max(selected_count, len(blocks)), 8)) if clear_long else max(2, 2 + min(3, len(world_model.facts.user_word_anchors or [])))
    max_lines = min(tier_ceiling, max(2, target), max(2, evidence_ceiling + (1 if history_usable else 0)))
    return ReplyLengthPlan(
        mode=capability.reply_length_mode,
        max_lines=max_lines,
        reason="generic_current_input_coverage",
        input_effort_score=input_effort_score,
        memory_richness_score=memory_richness_score,
        tier_ceiling=tier_ceiling,
        evidence_ceiling=evidence_ceiling,
        target_lines=target,
        user_word_anchor_count=len(world_model.facts.user_word_anchors or []),
        history_usable=history_usable,
        interpretive_frame_usable=False,
        meaning_block_count=len(blocks),
        selected_meaning_block_count=selected_count,
        meaning_coverage_ratio=(selected_count / len(blocks)) if blocks else 0.0,
        clear_long_input=clear_long,
        major_must_keep_count=len(getattr(getattr(world_model.facts, "major_meaning_retention_plan", None), "must_keep_block_keys", []) or []),
        major_must_keep_covered_count=0,
        major_must_keep_coverage_ratio=0.0,
    )


def _pick(candidates: List[ObservationCandidate], kind: str) -> Optional[ObservationCandidate]:
    return next((candidate for candidate in candidates if candidate.kind == kind), None)


def build_reply_lines(accepted_candidates: List[ObservationCandidate], *, reply_length_plan: ReplyLengthPlan) -> List[ReplyLine]:
    lines: List[ReplyLine] = []
    for candidate in accepted_candidates[: max(0, int(reply_length_plan.max_lines))]:
        lines.append(ReplyLine(key=candidate.kind, text=candidate.text, sentence_evidence=SentenceEvidence(line_key=candidate.kind, evidence=list(candidate.evidence)), candidate_key=candidate.candidate_key))
    return lines


def arbitrate_candidates(candidates: List[ObservationCandidate], rejected_candidates: List[ObservationCandidate], *, kernel_input: ObservationKernelInput, unknowns: List[str]) -> ObservationDecision:
    reply_length_plan = decide_reply_length_plan(capability=kernel_input.capability, bundle=kernel_input.bundle, world_model=kernel_input.world_model, working_model=kernel_input.working_model)
    accepted: List[ObservationCandidate] = []
    receive = _pick(candidates, "receive")
    if receive is not None:
        accepted.append(receive)
    for candidate in [c for c in candidates if c.kind == "word_reflection"]:
        if len(accepted) >= reply_length_plan.max_lines - 1:
            break
        accepted.append(candidate)
    if not reply_length_plan.clear_long_input:
        for kind in ("selected_emotions", "emotion_response"):
            if len(accepted) >= reply_length_plan.max_lines - 1:
                break
            item = _pick(candidates, kind)
            if item is not None:
                accepted.append(item)
    if reply_length_plan.history_usable and len(accepted) < reply_length_plan.max_lines - 1:
        item = _pick(candidates, "continuity")
        if item is not None:
            accepted.append(item)
    close = _pick(candidates, "receiving_close")
    if close is not None:
        if len(accepted) >= reply_length_plan.max_lines:
            accepted = accepted[: max(0, reply_length_plan.max_lines - 1)]
        accepted.append(close)
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
            "reply_length_reason": reply_length_plan.reason,
            "clear_long_input": bool(reply_length_plan.clear_long_input),
            "meaning_block_count": int(reply_length_plan.meaning_block_count or 0),
            "selected_meaning_block_count": int(reply_length_plan.selected_meaning_block_count or 0),
        },
    )


def run_emlis_ai_observation_kernel(*, kernel_input: ObservationKernelInput) -> ObservationDecision:
    candidates = generate_observation_candidates(kernel_input=kernel_input)
    candidates = apply_interpretive_alignment(candidates, kernel_input=kernel_input)
    kept, rejected, unknowns = suppress_overclaiming(candidates, kernel_input=kernel_input)
    return arbitrate_candidates(kept, rejected, kernel_input=kernel_input, unknowns=[*kernel_input.world_model.unknowns, *unknowns])
