# -*- coding: utf-8 -*-
from __future__ import annotations

"""Top-level orchestration for EmlisAI reply rendering."""

from typing import Any, Dict, List, Optional

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_context_service import build_emlis_ai_source_bundle
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import (
    EmlisAICapabilityConfig,
    EvidenceRef,
    ReplyEnvelope,
    ReplyPlan,
    SourceBundle,
    StyleProfile,
    WorldModel,
)
from emlis_ai_world_model_service import build_emlis_ai_world_model
from input_feedback_text_templates import build_input_feedback_comment as render_fallback_input_feedback


def _safe_name(display_name: Optional[str]) -> str:
    name = str(display_name or "").strip()
    return f"{name}さん" if name else ""


def _render_receive_line(bundle: SourceBundle, world_model: WorldModel, style_profile: StyleProfile) -> str:
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


def _render_continuity_line(capability: EmlisAICapabilityConfig, world_model: WorldModel) -> str:
    if capability.continuity_mode == "off":
        return ""
    for item in world_model.hypotheses:
        if item.key in {"same_day_change", "repeated_topic"} and item.evidence:
            return item.text
    return ""


def _render_change_line(capability: EmlisAICapabilityConfig, world_model: WorldModel) -> str:
    if capability.continuity_mode == "off":
        return ""
    for item in world_model.hypotheses:
        if item.key == "recovery_signal" and item.evidence:
            return item.text
    return ""


def _render_partner_line(capability: EmlisAICapabilityConfig, style_profile: StyleProfile) -> str:
    if capability.partner_mode == "off":
        return ""
    if capability.partner_mode == "on_advanced":
        if style_profile.family in {"analytical", "structured"}:
            return "ここから先も、いまの流れを急がず一緒に整理していきましょう。"
        return "ここから先も、いまのあなたに合う受け取り方で返していきますね。"
    return "最近の流れも踏まえながら、今の気持ちに合う返し方をしていきますね。"


def _build_meta(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
    used_evidence: List[EvidenceRef],
    fallback_used: bool,
) -> Dict[str, Any]:
    used_sources: List[str] = ["current_input"]
    if capability.history_mode != "none":
        used_sources.append("history")
    if capability.include_input_summary:
        used_sources.append("input_summary")
    if capability.include_myweb_summary:
        used_sources.append("myweb_home_summary")
    if capability.include_today_question_history:
        used_sources.append("today_question")
    if bundle.greeting:
        used_sources.append("greeting_state")

    return {
        "version": "emlis_ai_v1",
        "tier": capability.tier,
        "capability": {
            "history_mode": capability.history_mode,
            "continuity_mode": capability.continuity_mode,
            "style_mode": capability.style_mode,
            "partner_mode": capability.partner_mode,
        },
        "used_sources": used_sources,
        "evidence_count": len(used_evidence),
        "fallback_used": fallback_used,
        "world_model_debug": world_model.debug,
    }


def _merge_comment_lines(*lines: str) -> str:
    normalized = [str(line or "").strip() for line in lines if str(line or "").strip()]
    return "".join(normalized).strip()


def build_emlis_ai_reply_plan(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
    style_profile: StyleProfile,
) -> ReplyPlan:
    used_evidence: List[EvidenceRef] = []
    for hypothesis in world_model.hypotheses:
        used_evidence.extend(hypothesis.evidence)

    return ReplyPlan(
        receive=_render_receive_line(bundle, world_model, style_profile),
        continuity=_render_continuity_line(capability, world_model),
        change=_render_change_line(capability, world_model),
        partner_line=_render_partner_line(capability, style_profile),
        used_evidence=used_evidence,
        notes={"style_family": style_profile.family, "tone_reason": style_profile.tone_reason},
    )


async def render_emlis_ai_reply(
    *,
    user_id: str,
    subscription_tier: Any,
    current_input: Dict[str, Any],
    display_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
) -> ReplyEnvelope:
    capability = resolve_emlis_ai_capability_for_tier(subscription_tier)
    bundle = await build_emlis_ai_source_bundle(
        user_id=user_id,
        current_input=current_input,
        capability=capability,
        display_name=display_name,
        timezone_name=timezone_name,
    )
    world_model = build_emlis_ai_world_model(capability=capability, bundle=bundle)
    style_profile = build_style_profile(capability=capability, bundle=bundle, world_model=world_model)
    plan = build_emlis_ai_reply_plan(
        capability=capability,
        bundle=bundle,
        world_model=world_model,
        style_profile=style_profile,
    )

    comment_text = _merge_comment_lines(
        bundle.greeting.greeting_text if bundle.greeting else "",
        plan.receive,
        plan.continuity,
        plan.change,
        plan.partner_line,
    )
    fallback_used = False

    if not comment_text:
        fallback_used = True
        comment_text = render_fallback_input_feedback(
            emotion_details=current_input.get("emotion_details") if isinstance(current_input.get("emotion_details"), list) else [],
            memo=current_input.get("memo"),
            memo_action=current_input.get("memo_action"),
            category=current_input.get("category") if isinstance(current_input.get("category"), list) else [],
            selection_seed=str(current_input.get("selection_seed") or current_input.get("created_at") or ""),
        )

    return ReplyEnvelope(
        comment_text=comment_text,
        meta=_build_meta(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            used_evidence=plan.used_evidence,
            fallback_used=fallback_used,
        ),
        used_evidence=plan.used_evidence,
        fallback_used=fallback_used,
    )
