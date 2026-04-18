# -*- coding: utf-8 -*-
from __future__ import annotations

"""Top-level orchestration for EmlisAI reply rendering."""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_context_service import build_emlis_ai_source_bundle
from emlis_ai_observation_kernel import ObservationKernelInput, run_emlis_ai_observation_kernel
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_types import (
    DerivedModelHypothesis,
    DerivedUserModel,
    EmlisAICapabilityConfig,
    EvidenceRef,
    ReplyEnvelope,
    ReplyLine,
    ReplyPlan,
    SourceBundle,
    StyleProfile,
    TopicAnchor,
    ValueAnchor,
    WorldModel,
)
from emlis_ai_user_model_store import (
    new_empty_derived_user_model,
    save_emlis_ai_user_model_for_user,
)
from emlis_ai_world_model_service import build_emlis_ai_world_model
from emotion_history_search_service import build_open_topic_anchor_candidates, extract_repeated_categories
from input_feedback_text_templates import build_input_feedback_comment as render_fallback_input_feedback

_NEGATIVE_EMOTIONS = {"不安", "悲しみ", "怒り", "恐れ", "焦り"}


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _current_ref(bundle: SourceBundle) -> EvidenceRef:
    return EvidenceRef(
        kind="emotion",
        ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"),
        weight=1.0,
    )


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _collect_used_evidence(reply_lines: List[ReplyLine]) -> List[EvidenceRef]:
    seen: set[tuple[str, str, str]] = set()
    out: List[EvidenceRef] = []
    for line in reply_lines:
        for item in line.sentence_evidence.evidence:
            key = (item.kind, item.ref_id, str(item.note or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def _serialize_evidence_ref(item: EvidenceRef) -> Dict[str, Any]:
    return {
        "kind": item.kind,
        "ref_id": item.ref_id,
        "weight": float(item.weight),
        "note": item.note,
    }


def _clone_or_create_working_model(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
) -> Optional[DerivedUserModel]:
    if not capability.model_write_enabled and bundle.derived_user_model is None:
        return None
    if bundle.derived_user_model is not None:
        working_model = deepcopy(bundle.derived_user_model)
        if not working_model.schema_version:
            working_model.schema_version = "emlis_user_model.v2"
        if not working_model.model_tier:
            working_model.model_tier = capability.tier
        return working_model
    if not capability.model_write_enabled:
        return None
    return new_empty_derived_user_model(tier=capability.tier)


def _merge_counter_items(
    *,
    current_items: List[Dict[str, Any]],
    key_field: str,
    new_values: List[str],
    evidence: List[EvidenceRef],
    seen_at: str,
    limit: int,
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for item in current_items:
        if not isinstance(item, dict):
            continue
        key = _clean(item.get(key_field))
        if not key:
            continue
        merged[key] = dict(item)
    for value in new_values:
        key = _clean(value)
        if not key:
            continue
        entry = merged.get(key) or {key_field: key, "count": 0, "evidence": []}
        entry["count"] = int(entry.get("count") or 0) + 1
        entry["last_seen_at"] = seen_at
        entry["evidence"] = list(entry.get("evidence") or []) + [_serialize_evidence_ref(item) for item in evidence[:2]]
        merged[key] = entry
    items = sorted(
        merged.values(),
        key=lambda item: (-int(item.get("count") or 0), _clean(item.get("last_seen_at")), _clean(item.get(key_field))),
        reverse=False,
    )
    items.sort(key=lambda item: (-int(item.get("count") or 0), _clean(item.get(key_field))))
    return items[: max(0, int(limit))]


def _update_value_anchor(value_anchors: List[ValueAnchor], *, key: str, evidence: List[EvidenceRef], seen_at: str) -> List[ValueAnchor]:
    existing = {item.key: deepcopy(item) for item in value_anchors if _clean(item.key)}
    entry = existing.get(key) or ValueAnchor(key=key, confidence=0.0)
    entry.confidence = min(1.0, max(float(entry.confidence), 0.45) + 0.05)
    entry.last_seen_at = seen_at
    entry.evidence = [*entry.evidence, *evidence[:2]][-4:]
    existing[key] = entry
    out = list(existing.values())
    out.sort(key=lambda item: (-float(item.confidence), _clean(item.key)))
    return out


def _merge_topic_anchor(existing: List[TopicAnchor], incoming: TopicAnchor, *, limit: int) -> List[TopicAnchor]:
    by_key = {item.anchor_key: deepcopy(item) for item in existing if _clean(item.anchor_key)}
    cur = by_key.get(incoming.anchor_key)
    if cur is None:
        by_key[incoming.anchor_key] = incoming
    else:
        cur.confidence = max(float(cur.confidence), float(incoming.confidence))
        cur.last_seen_at = incoming.last_seen_at or cur.last_seen_at
        cur.evidence = [*cur.evidence, *incoming.evidence][-4:]
        cur.label = incoming.label or cur.label
        by_key[incoming.anchor_key] = cur
    out = list(by_key.values())
    out.sort(key=lambda item: (-float(item.confidence), _clean(item.anchor_key)))
    return out[: max(0, int(limit))]


def _project_working_user_model(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
) -> Optional[DerivedUserModel]:
    working_model = _clone_or_create_working_model(capability=capability, bundle=bundle)
    if working_model is None:
        return None

    current_ref = _current_ref(bundle)
    seen_at = _clean(bundle.current_input.get("created_at")) or _now_iso_z()
    current_categories = [str(v).strip() for v in (bundle.current_input.get("category") or []) if str(v).strip()] if isinstance(bundle.current_input.get("category"), list) else []
    current_emotions = list(world_model.facts.current_emotion_labels)
    dominant = _clean(world_model.facts.dominant_emotion)
    effort_score = float(bundle.input_effort.get("effort_score") or 0.0)
    history_density = float(bundle.memory_richness.get("history_density_score") or 0.0)

    working_model.model_tier = capability.tier
    working_model.updated_at = seen_at
    working_model.debug = dict(working_model.debug or {})
    working_model.debug.update(
        {
            "projected_from_current_input": True,
            "input_effort_score": effort_score,
            "history_density_score": history_density,
        }
    )

    facts = dict(working_model.factual_profile or {})
    facts["frequent_categories"] = _merge_counter_items(
        current_items=list(facts.get("frequent_categories") or []),
        key_field="label",
        new_values=current_categories,
        evidence=[current_ref],
        seen_at=seen_at,
        limit=max(4, capability.max_anchor_count),
    )
    facts["recurrent_emotion_labels"] = _merge_counter_items(
        current_items=list(facts.get("recurrent_emotion_labels") or []),
        key_field="label",
        new_values=current_emotions,
        evidence=[current_ref],
        seen_at=seen_at,
        limit=max(4, capability.max_anchor_count),
    )
    working_model.factual_profile = facts

    pref = working_model.interpretive_frame.response_preference_cues
    pref.prefers_receive_first = pref.prefers_receive_first or dominant in _NEGATIVE_EMOTIONS or not world_model.facts.has_memo_input
    pref.prefers_structure_when_long_memo = pref.prefers_structure_when_long_memo or int(bundle.input_effort.get("memo_char_count") or 0) >= 120
    pref.prefers_continuity_reference = pref.prefers_continuity_reference or bool(bundle.same_day_recent_inputs or bundle.similar_inputs)
    pref.evidence = [*pref.evidence, current_ref][-4:]

    partner = working_model.interpretive_frame.partner_expectation
    partner.wants_continuity = partner.wants_continuity or bool(bundle.same_day_recent_inputs or bundle.similar_inputs)
    partner.wants_non_judgmental_receive = partner.wants_non_judgmental_receive or dominant in _NEGATIVE_EMOTIONS or not world_model.facts.has_memo_input
    partner.wants_precise_observation = partner.wants_precise_observation or (capability.interpretation_mode == "precision_aligned" and history_density >= 0.55)
    partner.evidence = [*partner.evidence, current_ref][-4:]

    for category in current_categories:
        working_model.interpretive_frame.value_anchors = _update_value_anchor(
            working_model.interpretive_frame.value_anchors,
            key=f"category:{category}",
            evidence=[current_ref],
            seen_at=seen_at,
        )

    if capability.interpretation_mode != "current_only" and dominant:
        existing_entries = {item.trigger: deepcopy(item) for item in working_model.interpretive_frame.meaning_map if _clean(item.trigger)}
        for trigger in current_categories or current_emotions[:1]:
            key = _clean(trigger)
            if not key:
                continue
            entry = existing_entries.get(key)
            if entry is None:
                from emlis_ai_types import MeaningMapEntry  # local import to keep module import light

                entry = MeaningMapEntry(trigger=key, likely_meaning=dominant, confidence=0.48)
            if entry.likely_meaning == dominant:
                entry.confidence = min(1.0, max(float(entry.confidence), 0.48) + 0.06)
            else:
                entry.confidence = max(float(entry.confidence), 0.44)
            entry.last_seen_at = seen_at
            entry.evidence = [*entry.evidence, current_ref][-4:]
            existing_entries[key] = entry
        meaning_entries = list(existing_entries.values())
        meaning_entries.sort(key=lambda item: (-float(item.confidence), _clean(item.trigger)))
        working_model.interpretive_frame.meaning_map = meaning_entries[: max(0, int(capability.max_anchor_count or 0))]

    all_inputs = [*bundle.same_day_recent_inputs, *bundle.similar_inputs, bundle.current_input]
    for anchor_payload in build_open_topic_anchor_candidates(all_inputs, topn=max(1, int(capability.max_anchor_count or 1))):
        incoming = TopicAnchor(
            anchor_key=_clean(anchor_payload.get("anchor_key")) or "anchor:unknown",
            label=_clean(anchor_payload.get("label")) or "topic",
            confidence=min(1.0, float(anchor_payload.get("count") or 1) / 4.0),
            evidence=[current_ref],
            last_seen_at=_clean(anchor_payload.get("last_seen_at")) or seen_at,
        )
        working_model.open_topic_anchors = _merge_topic_anchor(
            working_model.open_topic_anchors,
            incoming,
            limit=max(0, int(capability.max_anchor_count or 0)),
        )

    if any(item.key == "recovery_signal" for item in world_model.hypotheses):
        incoming = TopicAnchor(
            anchor_key=f"recovery:{dominant or 'emotion'}",
            label=dominant or "回復",
            confidence=0.58,
            evidence=[current_ref],
            last_seen_at=seen_at,
        )
        working_model.recovery_anchors = _merge_topic_anchor(
            working_model.recovery_anchors,
            incoming,
            limit=max(0, int(capability.max_anchor_count or 0)),
        )

    derived_hypotheses: List[DerivedModelHypothesis] = []
    for item in world_model.hypotheses[: max(0, int(capability.max_hypothesis_count or 0))]:
        derived_hypotheses.append(
            DerivedModelHypothesis(
                key=item.key,
                text=item.text,
                confidence=float(item.confidence),
                evidence=list(item.evidence),
                status="active",
                last_seen_at=seen_at,
            )
        )
    working_model.hypotheses = derived_hypotheses

    working_model.source_cursor.last_emotion_id = _clean(bundle.current_input.get("id")) or working_model.source_cursor.last_emotion_id
    working_model.source_cursor.last_emotion_created_at = seen_at or working_model.source_cursor.last_emotion_created_at
    latest_tq_id = _clean(bundle.latest_today_question_answer.get("id"))
    if latest_tq_id:
        working_model.source_cursor.last_today_question_answer_id = latest_tq_id
    return working_model


def _render_comment_text_from_reply_lines(reply_lines: List[ReplyLine], *, greeting_text: str = "") -> str:
    normalized = [str(greeting_text or "").strip()] if str(greeting_text or "").strip() else []
    normalized.extend(str(line.text or "").strip() for line in reply_lines if str(line.text or "").strip())
    return "".join(normalized).strip()


def _build_reply_plan_from_decision(decision) -> ReplyPlan:
    reply_lines = list(decision.reply_lines)
    used_evidence = _collect_used_evidence(reply_lines)
    receive = next((line.text for line in reply_lines if line.key == "receive"), "")
    continuity = next((line.text for line in reply_lines if line.key in {"interpretation", "continuity", "topic_anchor"}), "")
    change = next((line.text for line in reply_lines if line.key in {"change", "recovery"}), "")
    partner_line = next((line.text for line in reply_lines if line.key == "partner_line"), "")
    return ReplyPlan(
        receive=receive,
        continuity=continuity,
        change=change,
        partner_line=partner_line,
        reply_lines=reply_lines,
        used_evidence=used_evidence,
        rejected_candidates=list(decision.rejected_candidates),
        reply_length_plan=decision.reply_length_plan,
        notes={
            "unknowns": list(decision.unknowns),
            "conflicts": list(decision.conflicts),
            **dict(decision.debug or {}),
        },
    )


async def _persist_working_user_model_best_effort(
    *,
    user_id: str,
    capability: EmlisAICapabilityConfig,
    working_model: Optional[DerivedUserModel],
) -> None:
    if not capability.model_write_enabled or working_model is None:
        return None
    try:
        await save_emlis_ai_user_model_for_user(user_id=user_id, model=working_model)
    except Exception:
        return None


def _build_meta(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
    plan: ReplyPlan,
    fallback_used: bool,
    working_model: Optional[DerivedUserModel],
) -> Dict[str, Any]:
    used_sources: List[str] = ["current_input"]
    used_memory_layers: List[str] = ["canonical_history"]
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
    if bundle.derived_user_model is not None or working_model is not None:
        used_sources.append("derived_user_model")
        used_memory_layers.append("derived_user_model")
    if bundle.side_state:
        used_memory_layers.append("side_state")

    evidence_by_line = {
        line.key: [_serialize_evidence_ref(item) for item in line.sentence_evidence.evidence]
        for line in plan.reply_lines
        if line.sentence_evidence.evidence
    }

    return {
        "version": "emlis_ai_v2",
        "kernel_version": "observation_kernel.v2",
        "tier": capability.tier,
        "capability": {
            "history_mode": capability.history_mode,
            "continuity_mode": capability.continuity_mode,
            "style_mode": capability.style_mode,
            "partner_mode": capability.partner_mode,
            "model_mode": capability.model_mode,
            "interpretation_mode": capability.interpretation_mode,
        },
        "used_sources": used_sources,
        "used_memory_layers": used_memory_layers,
        "reply_length_mode": plan.reply_length_plan.mode if plan.reply_length_plan else capability.reply_length_mode,
        "evidence_count": len(plan.used_evidence),
        "evidence_by_line": evidence_by_line,
        "rejected_candidate_count": len(plan.rejected_candidates),
        "fallback_used": fallback_used,
        "model_revision": working_model.updated_at if working_model is not None else None,
        "world_model_debug": {
            **dict(world_model.debug or {}),
            "unknown_count": len(world_model.unknowns),
            "conflict_count": len(world_model.conflicts),
        },
    }


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
    working_model = _project_working_user_model(capability=capability, bundle=bundle, world_model=world_model)
    decision = run_emlis_ai_observation_kernel(
        kernel_input=ObservationKernelInput(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            style_profile=style_profile,
            working_model=working_model,
        )
    )
    plan = _build_reply_plan_from_decision(decision)

    comment_text = _render_comment_text_from_reply_lines(
        plan.reply_lines,
        greeting_text=bundle.greeting.greeting_text if bundle.greeting else "",
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

    await _persist_working_user_model_best_effort(
        user_id=user_id,
        capability=capability,
        working_model=working_model,
    )

    evidence_by_line = {
        line.key: list(line.sentence_evidence.evidence)
        for line in plan.reply_lines
        if line.sentence_evidence.evidence
    }
    used_memory_layers = ["canonical_history"]
    if working_model is not None:
        used_memory_layers.append("derived_user_model")
    if bundle.side_state:
        used_memory_layers.append("side_state")

    return ReplyEnvelope(
        comment_text=comment_text,
        meta=_build_meta(
            capability=capability,
            bundle=bundle,
            world_model=world_model,
            plan=plan,
            fallback_used=fallback_used,
            working_model=working_model,
        ),
        used_evidence=plan.used_evidence,
        evidence_by_line=evidence_by_line,
        used_memory_layers=used_memory_layers,
        fallback_used=fallback_used,
    )
