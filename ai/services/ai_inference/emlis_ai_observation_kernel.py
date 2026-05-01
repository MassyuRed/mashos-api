# -*- coding: utf-8 -*-
from __future__ import annotations

"""Observation kernel for EmlisAI.

The kernel turns raw world-model hints plus the derived user model into reply
lines with sentence-bound evidence.  The vNext natural-reply policy keeps the
current input central: user words are reflected first, then history / derived
model lines are used only when there is enough evidence.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

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
    UserWordAnchor,
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


def _join_labels(labels: List[str]) -> str:
    cleaned = [str(v or "").strip() for v in labels if str(v or "").strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "、".join(cleaned[:-1]) + "、そして" + cleaned[-1]


def _emotion_label_with_strength(item) -> str:
    label = str(getattr(item, "type", "") or "").strip()
    strength_label = str(getattr(item, "strength_label", "") or "").strip()
    if not label:
        return ""
    if label == "自己理解" or not strength_label:
        return label
    return f"{label}（{strength_label}）"


def _selected_emotion_text(world_model: WorldModel) -> str:
    selected = list(world_model.facts.selected_emotions or [])
    if not selected:
        labels = list(world_model.facts.current_emotion_labels or [])
        return _join_labels(labels)
    return "、".join(v for v in (_emotion_label_with_strength(item) for item in selected) if v)


def _dominant_emotion_text(world_model: WorldModel) -> str:
    selected = list(world_model.facts.selected_emotions or [])
    dominant = next((item for item in selected if getattr(item, "role", "") == "dominant"), None)
    if dominant is not None:
        return _emotion_label_with_strength(dominant)
    dominant_label = str(world_model.facts.dominant_emotion or "").strip()
    if not dominant_label:
        return ""
    strength = {"weak": "弱", "medium": "中", "strong": "強"}.get(str(world_model.facts.dominant_strength or "").strip().lower(), "")
    if dominant_label == "自己理解" or not strength:
        return dominant_label
    return f"{dominant_label}（{strength}）"


def _anchor_by_role(anchors: List[UserWordAnchor], roles: set[str]) -> Optional[UserWordAnchor]:
    return next((item for item in anchors if item.role in roles), None)


def _shorten_anchor_text(text: str, *, max_chars: int = 46) -> str:
    clean = str(text or "").strip(" 、,。.!！?？\t\n\r")
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip("、,") + "…"


def _build_receive_text(bundle: SourceBundle, world_model: WorldModel, style_profile: StyleProfile) -> str:
    current = world_model.facts
    name = _safe_name(bundle.display_name)
    dominant = _dominant_emotion_text(world_model)
    selected_text = _selected_emotion_text(world_model)

    if not current.has_memo_input:
        if dominant:
            base = f"今回は、{dominant}が近くにあった入力として受け取りました。"
        elif selected_text:
            base = f"今回は、{selected_text}が近くにあった入力として受け取りました。"
        else:
            base = "今回は、いまの気持ちをそのまま置いてくれた入力として受け取りました。"
    elif current.memo_richness in {"medium", "long"}:
        if dominant:
            base = f"今回は、{dominant}を中心に、書いてくれた言葉そのものを見ながら受け取ります。"
        else:
            base = "今回は、書いてくれた言葉そのものを見ながら受け取ります。"
    elif dominant:
        if style_profile.family in {"analytical", "structured"}:
            base = f"今回は、{dominant}が前に出ていて、その感じを少し整理したかったのですね。"
        else:
            base = f"今回は、{dominant}が近くにあって、その気持ちを置いておきたかったのですね。"
    else:
        base = "今回は、いまの気持ちをそのまま置いておきたかったのですね。"

    use_name = bool(name) and not (bundle.greeting and bundle.greeting.first_in_slot)
    if not use_name:
        return base
    if "。" in base:
        first, rest = base.split("。", 1)
        return f"{name}、{first}。{rest}".strip()
    return f"{name}、{base}"



def _anchor_reply_text(anchor: UserWordAnchor, *, max_chars: int = 44) -> str:
    text = _shorten_anchor_text(anchor.text, max_chars=max_chars)
    if anchor.role == "mismatch":
        if "連絡" in text and "頻度" in text and "すれ違" in text:
            return "連絡の頻度の違いからすれ違ってしまった"
        for prefix in ("自分は", "私は", "僕は", "俺は", "相手は"):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
    return text


def _event_after_text(event_text: str) -> str:
    if event_text.endswith(("した", "だった", "あった")):
        return f"{event_text}あと"
    return f"{event_text}のあと"


def _compose_anchor_overview(anchors: List[UserWordAnchor]) -> Optional[ObservationCandidate]:
    if not anchors:
        return None
    event = _anchor_by_role(anchors, {"event", "relationship"})
    mismatch = _anchor_by_role(anchors, {"mismatch", "need", "unresolved"})
    explicit = _anchor_by_role(anchors, {"explicit_emotion"})
    evidence: List[EvidenceRef] = []

    if event and mismatch and event.text != mismatch.text:
        event_text = _anchor_reply_text(event, max_chars=32)
        mismatch_text = _anchor_reply_text(mismatch, max_chars=40)
        if mismatch_text.endswith(("した", "った", "しまった", "いた")):
            text = f"{_event_after_text(event_text)}、{mismatch_text}のですね。"
        else:
            text = f"{_event_after_text(event_text)}、{mismatch_text}というところが残っていたのですね。"
        evidence = [*event.evidence, *mismatch.evidence]
    elif event:
        event_text = _anchor_reply_text(event, max_chars=44)
        text = f"{event_text}という出来事を、まずそのまま受け取りました。"
        evidence = list(event.evidence)
    elif mismatch:
        mismatch_text = _anchor_reply_text(mismatch, max_chars=44)
        text = f"{mismatch_text}というところが、今回の中で大事に見えます。"
        evidence = list(mismatch.evidence)
    elif explicit:
        explicit_text = _shorten_anchor_text(explicit.text, max_chars=44)
        text = f"「{explicit_text}」という言葉を、そのまま大事なところとして受け取りました。"
        evidence = list(explicit.evidence)
    else:
        first = anchors[0]
        text = f"「{_shorten_anchor_text(first.text)}」という言葉を、今回の入力の核として受け取りました。"
        evidence = list(first.evidence)

    return ObservationCandidate(
        candidate_key="word_reflection.overview",
        kind="word_reflection",
        text=text,
        evidence=evidence,
        confidence=0.94,
        recency_score=1.0,
        alignment_score=0.95,
        overclaim_risk=0.02,
        source_layers=["canonical_history"],
        notes={"source": "user_word_anchor", "role": "overview"},
    )


def _compose_explicit_emotion_anchor(anchors: List[UserWordAnchor]) -> Optional[ObservationCandidate]:
    explicit = _anchor_by_role(anchors, {"explicit_emotion"})
    if explicit is None:
        return None
    text = f"「{_shorten_anchor_text(explicit.text, max_chars=52)}」というところが、今回いちばん残っていた言葉なのだと思います。"
    return ObservationCandidate(
        candidate_key="word_reflection.explicit_emotion",
        kind="word_reflection",
        text=text,
        evidence=list(explicit.evidence),
        confidence=0.92,
        recency_score=1.0,
        alignment_score=0.94,
        overclaim_risk=0.05,
        source_layers=["canonical_history"],
        notes={"source": "user_word_anchor", "role": explicit.role},
    )


def _compose_secondary_anchor(anchors: List[UserWordAnchor]) -> Optional[ObservationCandidate]:
    # Keep this as an extra nuance line only.  The overview / explicit-emotion
    # lines already use event, mismatch, and explicit emotion anchors, so repeating
    # those makes the reply feel templated rather than attentive.
    priority = ["need", "unresolved", "relationship"]
    overview_roles = {"event", "mismatch", "explicit_emotion"}
    for role in priority:
        for anchor in anchors:
            if anchor.role != role or anchor.role in overview_roles:
                continue
            text = f"{_shorten_anchor_text(anchor.text, max_chars=48)}という部分も、流さずに見ています。"
            return ObservationCandidate(
                candidate_key=f"word_reflection.{role}",
                kind="word_reflection",
                text=text,
                evidence=list(anchor.evidence),
                confidence=0.80,
                recency_score=1.0,
                alignment_score=0.84,
                overclaim_risk=0.06,
                source_layers=["canonical_history"],
                notes={"source": "user_word_anchor", "role": role},
            )
    return None


def _compose_emotion_response(world_model: WorldModel, anchors: List[UserWordAnchor]) -> ObservationCandidate:
    facts = world_model.facts
    labels = set(facts.current_emotion_labels or [])
    response_mode = str(facts.response_mode or "receive")
    selected_text = _selected_emotion_text(world_model)
    dominant_text = _dominant_emotion_text(world_model)
    evidence: List[EvidenceRef] = []
    for anchor in anchors[:2]:
        evidence.extend(anchor.evidence)

    if response_mode == "celebrate":
        text = "その喜びは、小さく流さずに、一緒に大事なものとして受け取りたいです。"
    elif response_mode == "protect_boundary":
        text = "怒りの近くにある、雑に扱われたくなかった部分も、決めつけずに受け取ります。"
    elif response_mode == "quiet_receive":
        text = "この落ち着きは、無理に深く掘らず、そのまま静かに受け取ります。"
    elif response_mode == "comfort":
        if "悲しみ" in labels and "不安" in labels:
            text = "そのしんどさを、急いで答えにせず、まず言葉として受け取りたいです。"
        elif "悲しみ" in labels:
            text = "その悲しさを、ただの出来事として片づけずに受け取りたいです。"
        elif "不安" in labels:
            text = "その不安を、急いで答えにせず、まず言葉として受け取ります。"
        else:
            text = "その気持ちを、軽く扱わずに受け取りたいです。"
    elif response_mode == "organize":
        text = "書いてくれた内容は、今の気持ちを少し見える形にしたかった入力として受け取りました。"
    else:
        if selected_text and selected_text != dominant_text:
            text = f"{selected_text}が重なっていたことも、分けずに受け取ります。"
        else:
            text = "書いてくれた範囲を越えずに、今の入力として受け取ります。"

    return ObservationCandidate(
        candidate_key=f"emotion_response.{response_mode}",
        kind="emotion_response",
        text=text,
        evidence=evidence or [],
        confidence=0.84,
        recency_score=1.0,
        alignment_score=0.84,
        overclaim_risk=0.10,
        source_layers=["canonical_history"],
        notes={"response_mode": response_mode},
    )


def _compose_selected_emotions(world_model: WorldModel, current_ref: EvidenceRef) -> Optional[ObservationCandidate]:
    selected = list(world_model.facts.selected_emotions or [])
    if len(selected) <= 1:
        return None
    dominant = next((item for item in selected if getattr(item, "role", "") == "dominant"), selected[0])
    secondary = [item for item in selected if item is not dominant]
    secondary_text = "、".join(v for v in (_emotion_label_with_strength(item) for item in secondary) if v)
    dominant_text = _emotion_label_with_strength(dominant)
    if not secondary_text or not dominant_text:
        return None
    text = f"中心としては{dominant_text}を見ていますが、{secondary_text}もなかったことにせず一緒に受け取ります。"
    return ObservationCandidate(
        candidate_key="selected_emotions.all",
        kind="selected_emotions",
        text=text,
        evidence=[current_ref],
        confidence=0.90,
        recency_score=1.0,
        alignment_score=0.90,
        overclaim_risk=0.02,
        source_layers=["canonical_history"],
        notes={"selected_emotion_count": len(selected)},
    )


def _compose_receiving_close(bundle: SourceBundle) -> ObservationCandidate:
    return ObservationCandidate(
        candidate_key="receiving_close.default",
        kind="receiving_close",
        text="いつでも、あなたの言葉をEmlisは受け取ります。",
        evidence=[_current_ref(bundle)],
        confidence=0.90,
        recency_score=1.0,
        alignment_score=0.90,
        overclaim_risk=0.0,
        source_layers=["canonical_history"],
        notes={"source": "receiving_close"},
    )


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


def _interpretive_frame_usable(*, capability: EmlisAICapabilityConfig, working_model: Optional[DerivedUserModel], bundle: SourceBundle) -> bool:
    if capability.interpretation_mode != "precision_aligned" or working_model is None:
        return False
    meaning_map = list(working_model.interpretive_frame.meaning_map or [])
    if not meaning_map:
        return False
    history_density = float(bundle.memory_richness.get("history_density_score") or 0.0)
    return history_density >= 0.35 and any(float(getattr(entry, "confidence", 0.0) or 0.0) >= 0.50 for entry in meaning_map)


def generate_observation_candidates(*, kernel_input: ObservationKernelInput) -> List[ObservationCandidate]:
    capability = kernel_input.capability
    bundle = kernel_input.bundle
    world_model = kernel_input.world_model
    style_profile = kernel_input.style_profile
    working_model = kernel_input.working_model
    candidates: List[ObservationCandidate] = []
    current_ref = _current_ref(bundle)
    anchors = list(world_model.facts.user_word_anchors or [])

    candidates.append(
        ObservationCandidate(
            candidate_key="receive.current",
            kind="receive",
            text=_build_receive_text(bundle, world_model, style_profile),
            evidence=[current_ref],
            confidence=0.98,
            recency_score=1.0,
            alignment_score=1.0,
            overclaim_risk=0.0,
            source_layers=["canonical_history"],
            notes={"source": "current_input"},
        )
    )

    for candidate in (
        _compose_anchor_overview(anchors),
        _compose_explicit_emotion_anchor(anchors),
        _compose_secondary_anchor(anchors),
        _compose_selected_emotions(world_model, current_ref),
    ):
        if candidate is not None:
            candidates.append(candidate)

    emotion_response = _compose_emotion_response(world_model, anchors)
    emotion_response.evidence = emotion_response.evidence or [current_ref]
    candidates.append(emotion_response)

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

    allow_precision = _interpretive_frame_usable(capability=capability, working_model=working_model, bundle=bundle)
    if working_model is not None and capability.interpretation_mode != "current_only":
        for entry in working_model.interpretive_frame.meaning_map[: capability.max_anchor_count or 0]:
            if not allow_precision and capability.interpretation_mode == "precision_aligned":
                continue
            if not _trigger_matches_current(bundle, entry.trigger):
                continue
            candidates.append(
                ObservationCandidate(
                    candidate_key=f"interpretation.meaning_map.{entry.trigger}",
                    kind="interpretation",
                    text=f"この {entry.trigger} の流れは、履歴の中では {entry.likely_meaning} と結びつきやすいようです。",
                    evidence=[current_ref, *list(entry.evidence)[:2]],
                    confidence=max(0.45, float(entry.confidence)),
                    recency_score=_recency_score(entry.last_seen_at),
                    alignment_score=0.82,
                    overclaim_risk=0.30 if allow_precision else 0.44,
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
                    text="この話題は、最近の流れの中でもまだ開いたまま残っていそうです。",
                    evidence=[current_ref, *list(anchor.evidence)[:2]],
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
        if capability.partner_mode == "on_advanced" and allow_precision:
            if partner.wants_precise_observation:
                partner_text = "Emlisは、この流れを覚えたまま、今の受け取り方に合う形で返していきます。"
            elif partner.wants_non_judgmental_receive:
                partner_text = "Emlisは、急がず、決めつけずに、この流れを受け取っていきます。"
            elif partner.wants_continuity:
                partner_text = "Emlisは、前からの線も見ながら、今の気持ちに合う返し方をしていきます。"
        elif capability.partner_mode == "on_basic" and (bundle.same_day_recent_inputs or bundle.similar_inputs):
            if pref.prefers_continuity_reference:
                partner_text = "最近の流れも踏まえて、今の入力を受け取ります。"
            else:
                partner_text = "今の気持ちと最近の流れをつないで受け取ります。"
        if partner_text:
            candidates.append(
                ObservationCandidate(
                    candidate_key="partner.memory_aligned",
                    kind="partner_line",
                    text=partner_text,
                    evidence=[current_ref, *list(pref.evidence)[:1], *list(partner.evidence)[:1]],
                    confidence=0.78 if capability.partner_mode == "on_advanced" else 0.70,
                    recency_score=0.65,
                    alignment_score=0.76,
                    overclaim_risk=0.18,
                    source_layers=["canonical_history", "derived_user_model"],
                    notes={"partner_mode": capability.partner_mode},
                )
            )

    candidates.append(_compose_receiving_close(bundle))
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
        if candidate.kind in {"receive", "word_reflection"} and pref.prefers_receive_first:
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
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
    working_model: Optional[DerivedUserModel],
) -> ReplyLengthPlan:
    input_effort_score = float(bundle.input_effort.get("effort_score") or 0.0)
    memory_richness_score = float(bundle.memory_richness.get("history_density_score") or 0.0)
    memo_char_count = int(bundle.input_effort.get("memo_char_count") or 0) + int(bundle.input_effort.get("memo_action_char_count") or 0)
    emotion_count = len(world_model.facts.selected_emotions or world_model.facts.current_emotion_labels or [])
    anchor_count = len(world_model.facts.user_word_anchors or [])
    history_usable = bool(capability.history_mode != "none" and (bundle.same_day_recent_inputs or bundle.similar_inputs or memory_richness_score >= 0.28))
    interpretive_usable = _interpretive_frame_usable(capability=capability, working_model=working_model, bundle=bundle)

    tier_ceiling = max(2, int(capability.max_reply_lines or 3))
    target = 2  # receive + close
    if emotion_count > 1:
        target += 1
    if memo_char_count > 0:
        target += 1
    if memo_char_count >= 40:
        target += 1
    if memo_char_count >= 100:
        target += 1
    if memo_char_count >= 180:
        target += 1
    if anchor_count >= 3:
        target += 1
    if history_usable:
        target += 1
    if interpretive_usable:
        target += 1
        partner = working_model.interpretive_frame.partner_expectation if working_model is not None else None
        if partner is not None and (partner.evidence or partner.wants_precise_observation or partner.wants_continuity or partner.wants_non_judgmental_receive):
            target += 1
    if capability.tier == "premium" and input_effort_score >= 0.75 and memory_richness_score >= 0.70:
        target += 1

    evidence_ceiling = 2  # receive + close
    if anchor_count:
        evidence_ceiling += min(3, anchor_count)
    if emotion_count > 1:
        evidence_ceiling += 1
    if world_model.facts.response_mode:
        evidence_ceiling += 1
    if history_usable:
        evidence_ceiling += 2 if capability.tier == "premium" else 1
    if interpretive_usable:
        evidence_ceiling += 2

    max_lines = min(tier_ceiling, max(2, target), max(2, evidence_ceiling))

    return ReplyLengthPlan(
        mode=capability.reply_length_mode,
        max_lines=max_lines,
        reason="input_amount_user_words_and_available_memory",
        input_effort_score=input_effort_score,
        memory_richness_score=memory_richness_score,
        tier_ceiling=tier_ceiling,
        evidence_ceiling=evidence_ceiling,
        target_lines=target,
        user_word_anchor_count=anchor_count,
        history_usable=history_usable,
        interpretive_frame_usable=interpretive_usable,
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


def _append_unique(target: List[ObservationCandidate], candidate: Optional[ObservationCandidate]) -> None:
    if candidate is None:
        return
    if any(item.candidate_key == candidate.candidate_key for item in target):
        return
    target.append(candidate)


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
    reply_length_plan = decide_reply_length_plan(
        capability=capability,
        bundle=kernel_input.bundle,
        world_model=kernel_input.world_model,
        working_model=kernel_input.working_model,
    )

    accepted: List[ObservationCandidate] = []
    _append_unique(accepted, _pick_best(candidates, kind="receive"))

    word_candidates = [item for item in candidates if item.kind == "word_reflection"]
    word_candidates.sort(key=_candidate_rank, reverse=True)
    for item in word_candidates[:3]:
        if len(accepted) >= reply_length_plan.max_lines - 1:
            break
        _append_unique(accepted, item)

    if len(accepted) < reply_length_plan.max_lines - 1:
        _append_unique(accepted, _pick_best(candidates, kind="selected_emotions"))

    if len(accepted) < reply_length_plan.max_lines - 1:
        _append_unique(accepted, _pick_best(candidates, kind="emotion_response"))

    if reply_length_plan.history_usable and len(accepted) < reply_length_plan.max_lines - 1:
        _append_unique(accepted, _pick_best_among(candidates, kinds=["interpretation", "continuity", "topic_anchor"]))

    if reply_length_plan.interpretive_frame_usable and capability.tier == "premium" and len(accepted) < reply_length_plan.max_lines - 1:
        secondary_middle = _pick_best_among(
            [item for item in candidates if item.candidate_key not in {c.candidate_key for c in accepted}],
            kinds=["interpretation", "continuity", "topic_anchor"],
        )
        _append_unique(accepted, secondary_middle)

    if len(accepted) < reply_length_plan.max_lines - 1:
        _append_unique(accepted, _pick_best_among(candidates, kinds=["change", "recovery"]))

    if len(accepted) < reply_length_plan.max_lines - 1:
        _append_unique(accepted, _pick_best(candidates, kind="partner_line"))

    close = _pick_best(candidates, kind="receiving_close")
    if close is not None:
        if len(accepted) >= reply_length_plan.max_lines:
            accepted = accepted[: max(0, reply_length_plan.max_lines - 1)]
        _append_unique(accepted, close)

    accepted = accepted[: max(0, reply_length_plan.max_lines)]
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
