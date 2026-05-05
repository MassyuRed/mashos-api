# -*- coding: utf-8 -*-
from __future__ import annotations

"""Observation kernel for EmlisAI.

The kernel turns raw world-model hints plus the derived user model into reply
lines with sentence-bound evidence.  The vNext natural-reply policy keeps the
current input central: user words are reflected first, then history / derived
model lines are used only when there is enough evidence.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional, Tuple

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
    ResponseCompositionPlan,
    ReplyNarrativeArc,
    SentenceEvidence,
    ShapedUserPhrase,
    SourceBundle,
    StyleProfile,
    UnderstandingFrame,
    UserWordAnchor,
    WorldModel,
)
from emlis_ai_phrase_shaping_service import safe_phrases, shape_user_phrase
from emlis_ai_input_meaning_block_service import selected_meaning_blocks_for_reply



_ROLE_PRIORITY = {
    role: index
    for index, role in enumerate((
        "state_awareness", "effort_history", "continuation_wish", "not_want_to_quit",
        "fatigue_or_limit", "collapse_anxiety", "dual_holding", "paced_progress",
        "self_permission", "self_understanding", "self_sacrifice_no_worry",
        "self_sacrifice_rounds_off", "old_strategy_ease", "alone_burden",
        "capacity_runs_out", "talk_or_rely_when_hard", "sustainable_by_relying",
        "protective_distance", "no_overdoing_choice", "not_only_patience",
        "state_based_action", "other_contribution", "self_dislike_from_halfway",
        "others_happiness_as_own_happiness", "future_not_giving_up", "resignation_self",
        "betrayal_fear", "own_happiness_wish", "existing_happiness_and_more",
        "concrete_life_wishes", "unreachable_wish", "present_effort_toward_wish",
        "missing_guidance", "anger_or_frustration", "relief_source",
    ))
}

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
    if not raw or raw.lower() == "user" or raw in {"ユーザー", "ゲスト"}:
        return ""
    return f"{raw}さん"


def _join_labels(labels: List[str]) -> str:
    cleaned = [str(v or "").strip() for v in labels if str(v or "").strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return "、".join(cleaned[:-1]) + "、そして" + cleaned[-1]


def _emotion_display_label(item) -> str:
    # 強度は内部判定には使うが、EmlisAIの表示文には出さない。
    return str(getattr(item, "type", "") or "").strip()


def _selected_emotion_text(world_model: WorldModel) -> str:
    selected = list(world_model.facts.selected_emotions or [])
    if not selected:
        labels = list(world_model.facts.current_emotion_labels or [])
        return _join_labels(labels)
    return "、".join(v for v in (_emotion_display_label(item) for item in selected) if v)


def _dominant_emotion_text(world_model: WorldModel) -> str:
    selected = list(world_model.facts.selected_emotions or [])
    dominant = next((item for item in selected if getattr(item, "role", "") == "dominant"), None)
    if dominant is not None:
        return _emotion_display_label(dominant)
    return str(world_model.facts.dominant_emotion or "").strip()


def _anchor_by_role(anchors: List[UserWordAnchor], roles: set[str]) -> Optional[UserWordAnchor]:
    return next((item for item in anchors if item.role in roles), None)


def _phrases(world_model: Optional[WorldModel]) -> List[ShapedUserPhrase]:
    if world_model is None:
        return []
    return safe_phrases(list(getattr(world_model.facts, "shaped_user_phrases", []) or []))


def _phrase_by_role(phrases: List[ShapedUserPhrase], roles: set[str]) -> Optional[ShapedUserPhrase]:
    return next((item for item in phrases if item.role in roles), None)


def _phrase_text(phrase: Optional[ShapedUserPhrase], *, attr: str = "phrase") -> str:
    if phrase is None:
        return ""
    value = getattr(phrase, attr, "") or getattr(phrase, "phrase", "")
    return _shorten_anchor_text(str(value or ""), max_chars=68)


def _has_work_companion_material(world_model: Optional[WorldModel]) -> bool:
    roles = {item.role for item in _phrases(world_model)}
    return bool({"sadness_surface", "work_frustration", "anger_surface", "missing_guidance", "effort_confusion", "chat_relief"} & roles)


def _meaning_plan(world_model: Optional[WorldModel]) -> Optional[MeaningCoveragePlan]:
    if world_model is None:
        return None
    plan = getattr(world_model.facts, "meaning_coverage_plan", None)
    return plan if plan is not None else None


def _meaning_blocks(world_model: Optional[WorldModel]) -> List[InputMeaningBlock]:
    if world_model is None:
        return []
    return list(getattr(world_model.facts, "meaning_blocks", []) or [])


def _whole_input_arc(world_model: Optional[WorldModel]):
    if world_model is None:
        return None
    return getattr(world_model.facts, "whole_input_meaning_arc", None)


def _major_retention_plan(world_model: Optional[WorldModel]):
    if world_model is None:
        return None
    return getattr(world_model.facts, "major_meaning_retention_plan", None)


def _composition_plan(world_model: Optional[WorldModel]) -> Optional[ResponseCompositionPlan]:
    if world_model is None:
        return None
    plan = getattr(world_model.facts, "response_composition_plan", None)
    return plan if plan is not None else None


def _reply_narrative_arc(world_model: Optional[WorldModel]) -> Optional[ReplyNarrativeArc]:
    if world_model is None:
        return None
    arc = getattr(world_model.facts, "reply_narrative_arc", None)
    return arc if arc is not None else None


def _clear_long_input(world_model: Optional[WorldModel]) -> bool:
    plan = _meaning_plan(world_model)
    return bool(plan is not None and plan.clear_long_input)


def _block_by_role(blocks: List[InputMeaningBlock], roles: set[str]) -> Optional[InputMeaningBlock]:
    return next((item for item in blocks if item.role in roles), None)


def _block_evidence(*blocks: Optional[InputMeaningBlock], fallback: Optional[EvidenceRef] = None) -> List[EvidenceRef]:
    evidence: List[EvidenceRef] = []
    for block in blocks:
        if block is not None:
            evidence.extend(list(getattr(block, "evidence", []) or []))
    if not evidence and fallback is not None:
        evidence.append(fallback)
    return evidence


def _shorten_anchor_text(text: str, *, max_chars: int = 46) -> str:
    clean = str(text or "").strip(" 、,。.!！?？\t\n\r")
    if len(clean) <= max_chars:
        return clean
    return clean[:max_chars].rstrip("、,") + "…"


def _frame(world_model: WorldModel) -> Optional[UnderstandingFrame]:
    frame = getattr(world_model.facts, "understanding_frame", None)
    return frame if frame is not None else None


def _anchor_raw(anchor: Optional[UserWordAnchor], *, max_chars: int = 58) -> str:
    if anchor is None:
        return ""
    return _shorten_anchor_text(anchor.text, max_chars=max_chars)


def _normalize_action_text(text: str) -> str:
    return _shorten_anchor_text(text, max_chars=52)


def _normalize_awareness_text(text: str) -> str:
    clean = _shorten_anchor_text(text, max_chars=44)
    for marker in ("知っていながら", "分かっていながら", "わかっていながら"):
        if marker in clean:
            return clean[: clean.index(marker) + len(marker)].lstrip("きっと") or marker
    return clean


def _normalize_justification_text(text: str) -> str:
    clean = _shorten_anchor_text(text, max_chars=56)
    for marker in ("という理由", "理由を掲げ", "理由にして"):
        if marker in clean:
            before = clean.split(marker, 1)[0].strip(" 、,")
            return before or clean
    return clean


def _normalize_avoidance_text(text: str, fault_text: str = "") -> str:
    clean = _shorten_anchor_text(text, max_chars=50)
    if "自分の非" in clean and "見たくない" in clean:
        return "自分の非を見たくない"
    if "見たくない" in clean and fault_text:
        return f"{fault_text}を見たくない"
    if "見たくない" in clean:
        return "見たくない"
    return clean


def _normalize_fear_text(text: str) -> str:
    clean = _shorten_anchor_text(text, max_chars=42)
    if "嫌われてしまいそう" in clean:
        return "嫌われてしまいそう"
    if "嫌われそう" in clean:
        return "嫌われそう"
    return clean


def _emotion_phrase(world_model: WorldModel) -> str:
    labels = list(world_model.facts.current_emotion_labels or [])
    if not labels:
        selected = list(world_model.facts.selected_emotions or [])
        labels = [str(getattr(item, "type", "") or "").strip() for item in selected if str(getattr(item, "type", "") or "").strip()]
    labels = [v for v in labels if v]
    if not labels:
        dominant = _dominant_emotion_text(world_model)
        return dominant
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]}と{labels[1]}"
    return "、".join(labels[:-1]) + "、そして" + labels[-1]


def _build_receive_text(bundle: SourceBundle, world_model: WorldModel, style_profile: StyleProfile) -> str:
    current = world_model.facts
    name = _safe_name(bundle.display_name)
    dominant = _dominant_emotion_text(world_model)
    selected_text = _selected_emotion_text(world_model)

    base = ""
    meaning_plan = _meaning_plan(world_model)
    if meaning_plan is not None and meaning_plan.clear_long_input:
        narrative_arc = _reply_narrative_arc(world_model)
        if narrative_arc is not None and getattr(narrative_arc, "opening_thesis", ""):
            base = str(narrative_arc.opening_thesis).strip()
        if not base:
            blocks = _meaning_blocks(world_model)
            if blocks:
                first_summary = str(getattr(blocks[0], "summary", "") or getattr(blocks[0], "title", "") or "").strip("。")
                if first_summary:
                    base = f"あなたは、{first_summary}ことを、少しでも言葉にしたかったのですね。"

    if not base:
        frame = _frame(world_model)
        if frame is not None and float(getattr(frame, "confidence", 0.0) or 0.0) >= 0.45:
            action_anchor = frame.action or frame.boundary_violation
            awareness_anchor = frame.self_awareness
            action_text = _normalize_action_text(_anchor_raw(action_anchor))
            awareness_text = _normalize_awareness_text(_anchor_raw(awareness_anchor))
            if action_text and awareness_text:
                base = f"あなたは、{action_text}ことだけでなく、{awareness_text}触れてしまった自覚も見ていたのですね。"
            elif action_text:
                base = f"あなたは、{action_text}ことをそのまま流さずに見ていたのですね。"
            elif awareness_text:
                base = f"あなたは、{awareness_text}いたからこそ、余計に心が揺れていたのですね。"

    if not base:
        if not current.has_memo_input:
            if dominant:
                base = f"今日は、{dominant}が近くにあったのですね。"
            elif selected_text:
                base = f"今日は、{selected_text}が近くにあったのですね。"
            else:
                base = "今日は、言葉にしきれない気持ちを少し置いておきたかったのですね。"
        elif current.memo_richness in {"medium", "long"}:
            if dominant:
                base = f"あなたは、{dominant}の近くにあるものを、少しでも言葉にしたかったのですね。"
            else:
                base = "あなたは、今の状態を少しでも言葉にしたかったのですね。"
        elif dominant:
            if style_profile.family in {"analytical", "structured"}:
                base = f"あなたは、{dominant}が前に出ている状態を少し整理したかったのですね。"
            else:
                base = f"あなたは、{dominant}が近くにあることを置いておきたかったのですね。"
        else:
            base = "あなたは、いまの気持ちをそのまま置いておきたかったのですね。"

    use_name = bool(name) and not (bundle.greeting and bundle.greeting.first_in_slot)
    if not use_name:
        return base
    if base.startswith("あなたは、"):
        return f"{name}、{base}"
    if "。" in base:
        first, rest = base.split("。", 1)
        return f"{name}、{first}。{rest}".strip()
    return f"{name}、{base}"

def _anchor_reply_text(anchor: UserWordAnchor, *, max_chars: int = 44) -> str:
    shaped = shape_user_phrase(anchor)
    text = _shorten_anchor_text(shaped.phrase if shaped.usability != "unsafe" and shaped.phrase else anchor.text, max_chars=max_chars)
    if shaped.role == "mismatch" or anchor.role == "mismatch":
        if "連絡" in text and "頻度" in text and "すれ違" in text:
            return "連絡の頻度の違いからすれ違ってしまった"
        for prefix in ("自分は", "私は", "僕は", "俺は", "相手は"):
            if text.startswith(prefix):
                text = text[len(prefix):]
                break
    return text


def _quote_anchor_text(anchor: UserWordAnchor, *, max_chars: int = 44) -> str:
    return f"「{_anchor_reply_text(anchor, max_chars=max_chars)}」"


def _nominalize_anchor_text(anchor_or_text, *, max_chars: int = 44) -> str:
    if isinstance(anchor_or_text, UserWordAnchor):
        shaped = shape_user_phrase(anchor_or_text)
        text = _shorten_anchor_text(shaped.nominal if shaped.usability != "unsafe" and shaped.nominal else shaped.phrase, max_chars=max_chars)
    else:
        text = _shorten_anchor_text(str(anchor_or_text or ""), max_chars=max_chars)
    if not text:
        return ""
    if text.endswith(("こと", "もの", "状態", "気持ち", "しんどさ", "怖さ", "行動", "自覚")):
        return text
    if text.endswith(("けど", "けれど", "でも", "から", "ので", "のに", "だって", "それだと")):
        return re.sub(r"(けど|けれど|でも|から|ので|のに|だって|それだと)$", "", text).strip(" 、,")
    return f"{text}こと"


def _flow_clause(anchor: UserWordAnchor, *, max_chars: int = 44) -> str:
    text = _anchor_reply_text(anchor, max_chars=max_chars)
    if not text:
        return ""
    replacements = (
        ("不安になる", "不安になって"),
        ("不安になった", "不安になって"),
        ("怖くなる", "怖くなって"),
        ("苦しくなる", "苦しくなって"),
        ("悲しくなる", "悲しくなって"),
        ("気になる", "気になって"),
    )
    for src, dst in replacements:
        if text.endswith(src):
            return text[: -len(src)] + dst
    if text.endswith("した"):
        return f"{text}ことで"
    if text.endswith(("だった", "あった", "いた", "いる")):
        return f"{text}ことから"
    return text


def _summary_text(block: Optional[InputMeaningBlock]) -> str:
    if block is None:
        return ""
    return str(getattr(block, "summary", "") or getattr(block, "title", "") or "").strip("。")


def _line_from_summary(summary: str, *, role: str = "") -> str:
    clean = str(summary or "").strip("。")
    if not clean:
        return ""
    if role in {"presence"}:
        return clean if clean.endswith("。") else f"{clean}。"
    if clean.endswith(("いる", "ある", "感じている", "思っている", "見ている", "気づいている", "しようとしている")):
        return f"{clean}のだと思います。"
    if clean.endswith(("たい", "必要", "大切")):
        return f"{clean}気持ちがありました。"
    return f"{clean}。"


def _line_from_blocks(blocks: List[InputMeaningBlock], *, line_role: str) -> str:
    summaries = [_summary_text(block) for block in blocks if _summary_text(block)]
    if not summaries:
        return ""
    if line_role == "presence":
        nouns = []
        for block in blocks[:3]:
            title = str(getattr(block, "title", "") or getattr(block, "summary", "") or "").strip("。")
            if title:
                nouns.append(title)
        if nouns:
            joined = "、".join(nouns[:3])
            return f"ここでは、{joined}を、どれかひとつに削らず大切に扱います。"
        return "ここでは、置いてくれた言葉を急いで小さくまとめず、大切に扱います。"
    if len(summaries) == 1:
        return _line_from_summary(summaries[0], role=line_role)
    if line_role in {"old_strategy", "value_or_wish", "state_and_effort", "meaning_background"}:
        return f"そこには、{summaries[0]}ことと、{summaries[1]}ことがありました。"
    if line_role in {"limit_of_strategy", "fear_or_resignation", "fatigue_or_anxiety", "meaning_conflict_or_need"}:
        return f"ただ、{summaries[0]}こともあり、{summaries[1]}ことも近くにありました。"
    if line_role in {"need_or_realization", "new_direction", "present_effort", "paced_progress", "meaning_direction"}:
        if line_role == "new_direction" and len(summaries) >= 4:
            return f"その中で、{summaries[0]}ことや、{summaries[1]}こと、{summaries[2]}こと、自分の状態を見ながら動くことも大切にしようとしているのだと思います。"
        if line_role == "new_direction" and len(summaries) >= 3:
            return f"その中で、{summaries[0]}ことや、{summaries[1]}こと、{summaries[2]}ことも大切にしようとしているのだと思います。"
        return f"その中で、{summaries[0]}ことや、{summaries[1]}ことも大切にしようとしているのだと思います。"
    return f"{summaries[0]}ことと、{summaries[1]}ことが同じ流れの中にありました。"


def _compose_response_composition_candidates(world_model: WorldModel, current_ref: EvidenceRef) -> List[ObservationCandidate]:
    """Generate ordered reply lines from the generic response-composition layer."""
    composition = _composition_plan(world_model)
    narrative = _reply_narrative_arc(world_model)
    if composition is None or narrative is None:
        return []
    blocks = _meaning_blocks(world_model)
    by_key = {block.block_key: block for block in blocks}
    by_role = {block.role: block for block in blocks}
    candidates: List[ObservationCandidate] = []
    for line_role in list(getattr(narrative, "ordered_roles", []) or []):
        if line_role == "presence":
            continue
        keys = list((getattr(narrative, "role_to_block_keys", {}) or {}).get(line_role, []) or [])
        line_blocks = [by_key[key] for key in keys if key in by_key]
        # Some generic line roles map to role names rather than keys.
        if not line_blocks and line_role in by_role:
            line_blocks = [by_role[line_role]]
        text = _line_from_blocks(line_blocks, line_role=line_role)
        if not text:
            continue
        candidates.append(ObservationCandidate(
            candidate_key=f"word_reflection.meaning.composition.{line_role}",
            kind="word_reflection",
            text=text,
            evidence=_block_evidence(*line_blocks, fallback=current_ref),
            confidence=0.94,
            recency_score=1.0,
            alignment_score=0.94,
            overclaim_risk=0.05,
            source_layers=["canonical_history"],
            notes={"source": "response_composition", "line_role": line_role, "composition_key": composition.composition_key},
        ))
    return candidates

def _compose_long_input_meaning_candidates(world_model: WorldModel, current_ref: EvidenceRef) -> List[ObservationCandidate]:
    plan = _meaning_plan(world_model)
    blocks = _meaning_blocks(world_model)
    if plan is None or not plan.clear_long_input or not blocks:
        return []

    composition_candidates = _compose_response_composition_candidates(world_model, current_ref)
    if composition_candidates:
        return composition_candidates

    selected_blocks = selected_meaning_blocks_for_reply(blocks, plan)
    candidates: List[ObservationCandidate] = []
    for block in selected_blocks:
        text = _line_from_blocks([block], line_role=str(getattr(block, "role", "") or "meaning"))
        if not text:
            continue
        candidates.append(ObservationCandidate(
            candidate_key=f"word_reflection.meaning.{block.block_key}",
            kind="word_reflection",
            text=text,
            evidence=_block_evidence(block, fallback=current_ref),
            confidence=0.92,
            recency_score=1.0,
            alignment_score=0.92,
            overclaim_risk=0.05,
            source_layers=["canonical_history"],
            notes={"source": "generic_meaning_block", "meaning_block_key": block.block_key, "line_role": block.role},
        ))
    return candidates

def _compose_anchor_overview(anchors: List[UserWordAnchor], world_model: Optional[WorldModel] = None) -> Optional[ObservationCandidate]:
    phrases = _phrases(world_model)
    missing = _phrase_by_role(phrases, {"missing_guidance"})
    effort = _phrase_by_role(phrases, {"effort_confusion"})
    anger = _phrase_by_role(phrases, {"anger_surface"})
    if missing is not None or effort is not None:
        if effort is not None and missing is not None:
            text = "むかつく気持ちの奥には、本当は「どう頑張ればいいのか」を教えてほしい気持ちも近くにありました。"
        elif effort is not None:
            text = "むかつく気持ちの奥には、どう頑張ればいいのか分からないしんどさも近くにありました。"
        else:
            text = "むかつく気持ちの奥には、教えてもらえないまま頑張らなきゃいけないしんどさもありました。"
        evidence = []
        for item in (missing, effort, anger):
            if item is not None:
                evidence.extend(item.evidence)
        return ObservationCandidate(
            candidate_key="word_reflection.need_under_anger",
            kind="word_reflection",
            text=text,
            evidence=evidence,
            confidence=0.99,
            recency_score=1.0,
            alignment_score=0.99,
            overclaim_risk=0.04,
            source_layers=["canonical_history"],
            notes={"source": "shaped_user_phrase", "role": "need_under_anger"},
        )

    frame = _frame(world_model) if world_model is not None else None
    if frame is not None:
        justification = _normalize_justification_text(_anchor_raw(frame.justification))
        fault = _anchor_raw(frame.self_fault_awareness, max_chars=24) or "自分の非"
        avoidance = _normalize_avoidance_text(_anchor_raw(frame.self_avoidance), fault_text=fault)
        if justification and avoidance and "justification_vs_fault" in set(frame.relation_patterns or []):
            text = f"「{justification}」と理由を置きたくなる一方で、{avoidance}自分にも気づいていて、そこが苦しかったのだと思います。"
            return ObservationCandidate(
                candidate_key="word_reflection.conflict_language",
                kind="word_reflection",
                text=text,
                evidence=list(frame.evidence),
                confidence=0.98,
                recency_score=1.0,
                alignment_score=0.99,
                overclaim_risk=0.05,
                source_layers=["canonical_history"],
                notes={"source": "understanding_frame", "role": "conflict_language", "patterns": list(frame.relation_patterns or [])},
            )

    if not anchors:
        return None
    anxiety = _anchor_by_role(anchors, {"anxiety_condition"})
    uncertainty = _anchor_by_role(anchors, {"uncertainty"})
    wish = _anchor_by_role(anchors, {"wish", "need"})
    event = _anchor_by_role(anchors, {"event", "relationship"})
    mismatch = _anchor_by_role(anchors, {"mismatch", "unresolved"})
    explicit = _anchor_by_role(anchors, {"explicit_emotion"})
    evidence: List[EvidenceRef] = []

    if anxiety and (uncertainty or wish):
        flow = _flow_clause(anxiety, max_chars=36) or _anchor_reply_text(anxiety, max_chars=36)
        quoted = [
            _quote_anchor_text(item, max_chars=30)
            for item in (uncertainty, wish)
            if item is not None and item.text != anxiety.text
        ]
        joined = "や".join(quoted)
        if joined:
            text = f"{flow}、{joined}ということまで考えが向いていたのですね。"
        else:
            text = f"{flow}いたことが、今の気持ちを強く揺らしていたのですね。"
        evidence = [*anxiety.evidence]
        if uncertainty is not None:
            evidence.extend(uncertainty.evidence)
        if wish is not None:
            evidence.extend(wish.evidence)
    elif event and mismatch and event.text != mismatch.text:
        event_text = _nominalize_anchor_text(event, max_chars=32)
        mismatch_text = _nominalize_anchor_text(mismatch, max_chars=40)
        text = f"{event_text}と、{mismatch_text}が、同じ流れの中にありました。"
        evidence = [*event.evidence, *mismatch.evidence]
    elif anxiety:
        flow = _flow_clause(anxiety, max_chars=44)
        if flow.endswith("て"):
            text = f"{flow}いたことが、今の気持ちを強く揺らしていたのですね。"
        else:
            text = f"{_nominalize_anchor_text(anxiety, max_chars=44)}が、今の気持ちを強く揺らしていたのですね。"
        evidence = list(anxiety.evidence)
    elif event:
        event_text = _nominalize_anchor_text(event, max_chars=44)
        text = f"{event_text}が、今回大きく残っていたのですね。"
        evidence = list(event.evidence)
    elif mismatch:
        mismatch_text = _nominalize_anchor_text(mismatch, max_chars=44)
        text = f"{mismatch_text}が、今回の大事な流れになっていたのですね。"
        evidence = list(mismatch.evidence)
    elif explicit:
        explicit_text = _quote_anchor_text(explicit, max_chars=44)
        text = f"{explicit_text}と書いてくれたところに、今の気持ちが集まっていたのですね。"
        evidence = list(explicit.evidence)
    else:
        first = anchors[0]
        text = f"「{_shorten_anchor_text(first.text)}」という言葉が、今回の気持ちの核に近かったのですね。"
        evidence = list(first.evidence)

    return ObservationCandidate(
        candidate_key="word_reflection.overview",
        kind="word_reflection",
        text=text,
        evidence=evidence,
        confidence=0.90,
        recency_score=1.0,
        alignment_score=0.92,
        overclaim_risk=0.04,
        source_layers=["canonical_history"],
        notes={"source": "user_word_anchor", "role": "overview"},
    )


def _compose_explicit_emotion_anchor(anchors: List[UserWordAnchor], world_model: Optional[WorldModel] = None) -> Optional[ObservationCandidate]:
    phrases = _phrases(world_model)
    mentor = _phrase_by_role(phrases, {"mentor_attachment"})
    fatigue = _phrase_by_role(phrases, {"fatigue_accumulation"})
    anger = _phrase_by_role(phrases, {"anger_surface"})
    if mentor is not None or fatigue is not None or anger is not None:
        parts = []
        evidence = []
        for item in (mentor, fatigue, anger):
            if item is not None:
                parts.append(_phrase_text(item, attr="nominal") or _phrase_text(item))
                evidence.extend(item.evidence)
        joined = "、".join(part for part in parts if part)
        text = f"そこには、{joined}も近くにありました。" if joined else "その気持ちは、軽く片づけられない場所にありました。"
        return ObservationCandidate(
            candidate_key="word_reflection.fatigue_or_pressure",
            kind="word_reflection",
            text=text,
            evidence=evidence,
            confidence=0.88,
            recency_score=1.0,
            alignment_score=0.88,
            overclaim_risk=0.06,
            source_layers=["canonical_history"],
            notes={"source": "shaped_user_phrase", "role": "fatigue_or_pressure"},
        )

    frame = _frame(world_model) if world_model is not None else None
    if frame is not None:
        fear = _normalize_fear_text(_anchor_raw(frame.fear_of_rejection))
        feelings = _emotion_phrase(world_model) if world_model is not None else ""
        explicit_text = _anchor_raw(frame.explicit_emotion)
        if fear and feelings:
            if "嫌われ" in fear and (frame.self_avoidance or frame.self_fault_awareness or frame.self_dislike):
                text = f"その自分ごと{fear}で、{feelings}が重なっていたのですね。"
            else:
                text = f"{fear}感じが、{feelings}につながっていたのですね。"
            return ObservationCandidate(
                candidate_key="word_reflection.feeling_language",
                kind="word_reflection",
                text=text,
                evidence=list(frame.evidence),
                confidence=0.97,
                recency_score=1.0,
                alignment_score=0.98,
                overclaim_risk=0.06,
                source_layers=["canonical_history"],
                notes={"source": "understanding_frame", "role": "feeling_language", "patterns": list(frame.relation_patterns or [])},
            )
        if explicit_text:
            return ObservationCandidate(
                candidate_key="word_reflection.explicit_emotion",
                kind="word_reflection",
                text=f"{explicit_text}ところに、今の気持ちが集まっていたのですね。",
                evidence=list(frame.evidence),
                confidence=0.88,
                recency_score=1.0,
                alignment_score=0.90,
                overclaim_risk=0.06,
                source_layers=["canonical_history"],
                notes={"source": "understanding_frame", "role": "explicit_emotion"},
            )

    uncertainty = _anchor_by_role(anchors, {"uncertainty"})
    wish = _anchor_by_role(anchors, {"wish", "need"})
    if uncertainty is not None and wish is not None and uncertainty.text != wish.text:
        text = f"{_quote_anchor_text(uncertainty, max_chars=34)}という不確かさと、{_quote_anchor_text(wish, max_chars=34)}という願いを、同じ流れとして見ています。"
        return ObservationCandidate(
            candidate_key="word_reflection.uncertainty_wish",
            kind="word_reflection",
            text=text,
            evidence=[*uncertainty.evidence, *wish.evidence],
            confidence=0.91,
            recency_score=1.0,
            alignment_score=0.93,
            overclaim_risk=0.05,
            source_layers=["canonical_history"],
            notes={"source": "user_word_anchor", "role": "uncertainty_wish"},
        )

    explicit = _anchor_by_role(anchors, {"explicit_emotion"})
    if explicit is None:
        return None
    text = f"{_quote_anchor_text(explicit, max_chars=52)}と書いてくれたところに、今の気持ちが集まっていたのですね。"
    return ObservationCandidate(
        candidate_key="word_reflection.explicit_emotion",
        kind="word_reflection",
        text=text,
        evidence=list(explicit.evidence),
        confidence=0.88,
        recency_score=1.0,
        alignment_score=0.90,
        overclaim_risk=0.05,
        source_layers=["canonical_history"],
        notes={"source": "user_word_anchor", "role": explicit.role},
    )


def _compose_secondary_anchor(anchors: List[UserWordAnchor], world_model: Optional[WorldModel] = None) -> Optional[ObservationCandidate]:
    phrases = _phrases(world_model)
    relief = _phrase_by_role(phrases, {"chat_relief", "relief_source"})
    if relief is not None:
        text = "その重さを忘れたい時に、チャットで話す時間が少し癒しになっていたのですね。"
        return ObservationCandidate(
            candidate_key="word_reflection.relief_source",
            kind="word_reflection",
            text=text,
            evidence=list(relief.evidence),
            confidence=0.94,
            recency_score=1.0,
            alignment_score=0.94,
            overclaim_risk=0.05,
            source_layers=["canonical_history"],
            notes={"source": "shaped_user_phrase", "role": "relief_source"},
        )

    frame = _frame(world_model) if world_model is not None else None
    if frame is not None and frame.action is not None:
        action_text = _normalize_action_text(_anchor_raw(frame.action))
        if action_text:
            text = f"{action_text}行動も、今回の気持ちと切り離さずに見ます。"
            return ObservationCandidate(
                candidate_key="word_reflection.action_connection",
                kind="word_reflection",
                text=text,
                evidence=list(frame.action.evidence),
                confidence=0.90,
                recency_score=1.0,
                alignment_score=0.92,
                overclaim_risk=0.05,
                source_layers=["canonical_history"],
                notes={"source": "understanding_frame", "role": "action_connection"},
            )

    action = next((anchor for anchor in anchors if anchor.role == "action" or anchor.source_field == "memo_action"), None)
    if action is not None:
        text = f"{_nominalize_anchor_text(action, max_chars=42)}も、今回の行動として残っていたのですね。"
        return ObservationCandidate(
            candidate_key="word_reflection.action",
            kind="word_reflection",
            text=text,
            evidence=list(action.evidence),
            confidence=0.82,
            recency_score=1.0,
            alignment_score=0.84,
            overclaim_risk=0.05,
            source_layers=["canonical_history"],
            notes={"source": "user_word_anchor", "role": action.role},
        )

    for role in ("wish", "need", "unresolved", "relationship"):
        for anchor in anchors:
            if anchor.role != role:
                continue
            if role in {"wish", "need"}:
                text = f"{_quote_anchor_text(anchor, max_chars=40)}という願いも、今回の言葉の中にありました。"
            else:
                text = f"{_nominalize_anchor_text(anchor, max_chars=42)}も、今回の流れの中にありました。"
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
        text = "その喜びは、小さく流さず、大事にしていいものだったのだと思います。"
    elif response_mode == "protect_boundary":
        text = "怒りの近くには、雑に扱われたくなかった部分もあったのですね。"
    elif response_mode == "quiet_receive":
        text = "この落ち着きは、無理に深く掘らず、静かに置いておけるものだったのですね。"
    elif response_mode == "comfort":
        if "悲しみ" in labels and "不安" in labels:
            text = "そのしんどさは、答えを急ぐよりも、まず分かってほしい場所にあったのだと思います。"
        elif "悲しみ" in labels:
            text = "その悲しさは、ただの出来事として片づけられないものだったのですね。"
        elif "不安" in labels:
            text = "その不安は、急いで答えを出すよりも、まず言葉にしたいものだったのですね。"
        else:
            text = "その気持ちは、軽く片づけられない場所にあったのですね。"
    elif response_mode == "organize":
        text = "書いてくれた内容は、今の気持ちを少し見える形にしたかった言葉なのだと思います。"
    else:
        if selected_text and selected_text != dominant_text:
            text = f"{selected_text}が重なっていたことも、分けずに見ておきたいところです。"
        else:
            text = "書いてくれた範囲を越えずに、今の気持ちを見ます。"

    return ObservationCandidate(
        candidate_key=f"emotion_response.{response_mode}",
        kind="emotion_response",
        text=text,
        evidence=evidence or [],
        confidence=0.80,
        recency_score=1.0,
        alignment_score=0.82,
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
    secondary_text = _join_labels([v for v in (_emotion_display_label(item) for item in secondary) if v])
    dominant_text = _emotion_display_label(dominant)
    if not secondary_text or not dominant_text:
        return None
    text = f"{dominant_text}だけでなく、{secondary_text}も同じ場所にありました。"
    return ObservationCandidate(
        candidate_key="selected_emotions.all",
        kind="selected_emotions",
        text=text,
        evidence=[current_ref],
        confidence=0.86,
        recency_score=1.0,
        alignment_score=0.88,
        overclaim_risk=0.03,
        source_layers=["canonical_history"],
        notes={"selected_emotion_count": len(selected)},
    )


def _compose_receiving_close(bundle: SourceBundle, world_model: Optional[WorldModel] = None) -> ObservationCandidate:
    if _clear_long_input(world_model):
        blocks = _meaning_blocks(world_model)
        if blocks:
            high = sorted(blocks, key=lambda item: (-float(getattr(item, "priority", 0.0) or 0.0), _ROLE_PRIORITY.get(getattr(item, "role", ""), 99)))[:3]
            labels = [str(getattr(item, "title", "") or getattr(item, "summary", "") or "").strip("。") for item in high]
            labels = [label for label in labels if label]
            if labels:
                text = f"ここでは、{ '、'.join(labels) }を、どれかひとつに削らず大切に扱います。"
            else:
                text = "ここでは、置いてくれた言葉を急いで小さくまとめず、大切に扱います。"
        else:
            text = "ここでは、置いてくれた言葉を急いで小さくまとめず、大切に扱います。"
    elif _has_work_companion_material(world_model):
        text = "ここでは、その悔しさも、むかつきも、癒されたい気持ちも、雑に扱いません。"
    else:
        selected_text = _selected_emotion_text(world_model) if world_model is not None else ""
        if "怒り" in selected_text and "悲しみ" in selected_text:
            text = "ここでは、悲しみも怒りも、無理にきれいにしなくて大丈夫です。"
        else:
            text = "ここに置いてくれた言葉を、Emlisは軽く扱いません。"
    return ObservationCandidate(
        candidate_key="receiving_close.default",
        kind="receiving_close",
        text=text,
        evidence=[_current_ref(bundle)],
        confidence=0.90,
        recency_score=1.0,
        alignment_score=0.90,
        overclaim_risk=0.0,
        source_layers=["canonical_history"],
        notes={"source": "receiving_close", "presence_line": True},
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

    candidates.extend(_compose_long_input_meaning_candidates(world_model, current_ref))

    for candidate in (
        _compose_anchor_overview(anchors, world_model),
        _compose_explicit_emotion_anchor(anchors, world_model),
        _compose_secondary_anchor(anchors, world_model),
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
                partner_text = "Emlisは、この流れを覚えたまま、今の気持ちに合う形で返していきます。"
            elif partner.wants_non_judgmental_receive:
                partner_text = "Emlisは、急がず、決めつけずに、この流れを見ていきます。"
            elif partner.wants_continuity:
                partner_text = "Emlisは、前からの線も見ながら、今の気持ちに合う返し方をしていきます。"
        elif capability.partner_mode == "on_basic" and (bundle.same_day_recent_inputs or bundle.similar_inputs):
            if pref.prefers_continuity_reference:
                partner_text = "最近の流れも踏まえて、今の気持ちを見ます。"
            else:
                partner_text = "今の気持ちと最近の流れをつないで見ます。"
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

    candidates.append(_compose_receiving_close(bundle, world_model))
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
        if candidate.kind in {"continuity", "partner_line", "topic_anchor"} and any(
            phrase in candidate.text for phrase in ("近いテーマ", "最近の流れも踏まえて", "今の気持ちを見ます")
        ):
            rejected.append(candidate)
            unknowns.append("abstract_history_reference_suppressed")
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
    meaning_plan = _meaning_plan(world_model)
    meaning_block_count = len(_meaning_blocks(world_model))
    selected_meaning_block_count = len(getattr(meaning_plan, "selected_block_keys", []) or []) if meaning_plan is not None else 0
    clear_long_input = bool(meaning_plan is not None and meaning_plan.clear_long_input)
    retention_plan = _major_retention_plan(world_model)
    major_must_keep_count = len(getattr(retention_plan, "must_keep_block_keys", []) or []) if retention_plan is not None else 0
    history_usable = bool(capability.history_mode != "none" and (bundle.same_day_recent_inputs or bundle.similar_inputs or memory_richness_score >= 0.28))
    interpretive_usable = _interpretive_frame_usable(capability=capability, working_model=working_model, bundle=bundle)

    tier_ceiling = max(2, int(capability.max_reply_lines or 3))
    if clear_long_input:
        if capability.tier == "premium":
            tier_ceiling = max(tier_ceiling, 14)
        elif capability.tier == "plus":
            tier_ceiling = max(tier_ceiling, 12)
        else:
            tier_ceiling = max(tier_ceiling, 10)
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
    if clear_long_input:
        target = max(target, 2 + min(max(selected_meaning_block_count, meaning_block_count, major_must_keep_count), 8))
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
    if clear_long_input:
        evidence_ceiling = max(evidence_ceiling, 2 + min(max(selected_meaning_block_count, meaning_block_count, major_must_keep_count), 8))
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
        meaning_block_count=meaning_block_count,
        selected_meaning_block_count=selected_meaning_block_count,
        meaning_coverage_ratio=(float(selected_meaning_block_count) / float(meaning_block_count)) if meaning_block_count else 0.0,
        clear_long_input=clear_long_input,
        major_must_keep_count=major_must_keep_count,
        major_must_keep_covered_count=0,
        major_must_keep_coverage_ratio=0.0,
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
    if reply_length_plan.clear_long_input:
        meaning_candidates = [item for item in word_candidates if str(item.candidate_key or "").startswith("word_reflection.meaning.")]
        non_meaning_candidates = [item for item in word_candidates if item not in meaning_candidates]
        meaning_order = {
            "word_reflection.meaning.composition.old_strategy": 1,
            "word_reflection.meaning.composition.limit_of_strategy": 2,
            "word_reflection.meaning.composition.need_to_rely": 3,
            "word_reflection.meaning.composition.boundary_and_rest_choice": 4,
            "word_reflection.meaning.composition.new_self_guidance": 5,
            "word_reflection.meaning.self_dislike_from_halfway": 10,
            "word_reflection.meaning.future_resignation_betrayal": 11,
            "word_reflection.meaning.own_happiness_wish": 3,
            "word_reflection.meaning.existing_happiness_and_more": 4,
            "word_reflection.meaning.concrete_life_wishes": 5,
            "word_reflection.meaning.present_effort_toward_wish": 6,
            "word_reflection.meaning.effort_history": 10,
            "word_reflection.meaning.continuation_wish": 11,
            "word_reflection.meaning.fatigue_and_anxiety": 12,
            "word_reflection.meaning.dual_holding": 13,
            "word_reflection.meaning.paced_progress": 14,
            "word_reflection.meaning.self_understanding": 15,
        }
        meaning_candidates.sort(key=lambda item: meaning_order.get(str(item.candidate_key or ""), 99))
        for item in meaning_candidates:
            if len(accepted) >= reply_length_plan.max_lines - 1:
                break
            _append_unique(accepted, item)
        # Do not backfill long, clear inputs with generic anchor overview lines.
        # Those lines can over-compress a detailed input or reintroduce raw-anchor
        # template fragments. The close line is appended below, so leaving one
        # unused line is preferable to showing a thin generic summary.
    else:
        word_candidates.sort(key=_candidate_rank, reverse=True)
        for item in word_candidates[:3]:
            if len(accepted) >= reply_length_plan.max_lines - 1:
                break
            _append_unique(accepted, item)

    if not reply_length_plan.clear_long_input and len(accepted) < reply_length_plan.max_lines - 1:
        _append_unique(accepted, _pick_best(candidates, kind="selected_emotions"))

    if not reply_length_plan.clear_long_input and len(accepted) < reply_length_plan.max_lines - 1:
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
            "clear_long_input": bool(reply_length_plan.clear_long_input),
            "meaning_block_count": int(reply_length_plan.meaning_block_count or 0),
            "selected_meaning_block_count": int(reply_length_plan.selected_meaning_block_count or 0),
            "major_must_keep_count": int(getattr(reply_length_plan, "major_must_keep_count", 0) or 0),
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
