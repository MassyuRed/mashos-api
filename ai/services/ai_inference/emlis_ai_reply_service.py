# -*- coding: utf-8 -*-
from __future__ import annotations

"""Top-level orchestration for EmlisAI reply rendering."""

from copy import deepcopy
from dataclasses import asdict, is_dataclass
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_context_service import build_emlis_ai_source_bundle
from emlis_ai_quality_gate import attach_emlis_ai_quality_gate_meta, evaluate_emlis_ai_quality_gate
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_user_address_service import build_emlis_observation_greeting, display_name_call
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

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_conversation_composer_service import (
    compose_emlis_conversation_candidate,
    get_default_conversation_composer_client,
    is_default_conversation_composer_configured,
    phase6_composer_contract_ready,
)
from emlis_ai_perspective_observers import phase4_observer_contract_ready, run_perspective_observers
from emlis_ai_perspective_board import build_perspective_board, phase5_board_contract_ready, validate_perspective_board
from emlis_ai_observation_integrator_service import integrate_perspective_board, phase5_observation_graph_ready, validate_observation_graph
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_display_gate import build_emlis_gate_trace, build_phase10_release_readiness, decide_emlis_observation_display, phase7_judge_contract_ready, phase8_display_gate_contract_ready
from emotion_history_search_service import build_open_topic_anchor_candidates, extract_repeated_categories

_NEGATIVE_EMOTIONS = {"不安", "悲しみ", "怒り", "恐れ", "焦り"}


_EMOTION_STRENGTH_DISPLAY_RE = re.compile(r"(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り)（(?:弱|中|強)）")


def _naturalize_reply_line(line: Any) -> str:
    text = str(line or "").strip()
    if not text:
        return ""
    # 強度は表示文から除外する。内部metaには残して互換性を維持する。
    text = _EMOTION_STRENGTH_DISPLAY_RE.sub(r"\1", text)
    text = re.sub(
        r"中心としては(.+?)を見ていますが、(.+?)もなかったことにせず一緒に受け取ります。?",
        r"\1だけでなく、\2も同じ場所にあったのですね。",
        text,
    )
    text = re.sub(
        r"(.+?かなぁ)のあと、(.+?したい)というところが残っていたのですね。?",
        r"「\1」という不確かさと、「\2」という願いを、同じ流れとして見ています。",
        text,
    )
    replacements = {
        "というところが、今回いちばん残っていた言葉なのだと思います": "と書いてくれたところに、今の気持ちが集まっていたのですね",
        "というところが残っていたのですね": "ことも、今回の流れの中にありました",
        "という部分も、流さずに見ています": "ことも、今回の流れの中にありました",
        "中心としては": "",
        "もなかったことにせず一緒に受け取ります": "も同じ場所にあったのですね",
        "入力として受け取ります": "今の気持ちとして見ます",
        "受け取りました": "見ています",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.replace("ですです", "です")
    text = re.sub(r"になるです([。！？!?]|$)", r"になります\1", text)
    text = re.sub(r"しているです([。！？!?]|$)", r"しています\1", text)
    text = re.sub(r"だったです([。！？!?]|$)", r"でした\1", text)
    text = re.sub(r"したです([。！？!?]|$)", r"しました\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _naturalize_reply_text(text: Any) -> str:
    return "\n".join(
        line for line in (_naturalize_reply_line(part) for part in str(text or "").splitlines()) if line
    ).strip()


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


def _serialize_emotion_display_item(item: Any) -> Dict[str, Any]:
    return {
        "type": _clean(getattr(item, "type", "")),
        "strength": _clean(getattr(item, "strength", "")),
        "strength_label": _clean(getattr(item, "strength_label", "")),
        "role": _clean(getattr(item, "role", "secondary")) or "secondary",
    }


def _serialize_user_word_anchor(item: Any) -> Dict[str, Any]:
    return {
        "anchor_key": _clean(getattr(item, "anchor_key", "")),
        "text": _clean(getattr(item, "text", "")),
        "source_field": _clean(getattr(item, "source_field", "")),
        "role": _clean(getattr(item, "role", "other")) or "other",
        "confidence": float(getattr(item, "confidence", 0.0) or 0.0),
        "evidence": [_serialize_evidence_ref(ev) for ev in list(getattr(item, "evidence", []) or [])],
    }


def _serialize_shaped_user_phrase(item: Any) -> Dict[str, Any]:
    return {
        "anchor_key": _clean(getattr(item, "anchor_key", "")),
        "raw_text": _clean(getattr(item, "raw_text", "")),
        "phrase": _clean(getattr(item, "phrase", "")),
        "sentence_fragment": _clean(getattr(item, "sentence_fragment", "")),
        "nominal": _clean(getattr(item, "nominal", "")),
        "role": _clean(getattr(item, "role", "other")) or "other",
        "source_field": _clean(getattr(item, "source_field", "")),
        "usability": _clean(getattr(item, "usability", "safe")) or "safe",
        "unsafe_reasons": [str(v) for v in list(getattr(item, "unsafe_reasons", []) or []) if str(v)],
    }


def _serialize_cross_core_anchor_packet(item: Any) -> Dict[str, Any]:
    groups = {
        "value_anchors": list(getattr(item, "value_anchors", []) or []),
        "state_anchors": list(getattr(item, "state_anchors", []) or []),
        "individuality_anchors": list(getattr(item, "individuality_anchors", []) or []),
        "boundary_anchors": list(getattr(item, "boundary_anchors", []) or []),
        "concept_anchors": list(getattr(item, "concept_anchors", []) or []),
        "reply_hints": list(getattr(item, "reply_hints", []) or []),
    }
    anchor_count = sum(len(values) for values in groups.values())
    labels: List[str] = []
    hints: List[str] = []
    for key, values in groups.items():
        for anchor in values:
            if not isinstance(anchor, dict):
                continue
            label = _clean(anchor.get("label") or anchor.get("user_definition") or anchor.get("recent_change") or anchor.get("role_pattern"),)
            if label and label not in labels:
                labels.append(label[:96])
            if key == "reply_hints":
                hint = _clean(anchor.get("hint") or anchor.get("receive_hint") or anchor.get("question_hint"),)
                if hint and hint not in hints:
                    hints.append(hint[:120])
            if len(labels) >= 6 and len(hints) >= 4:
                break
        if len(labels) >= 6 and len(hints) >= 4:
            break
    return {
        "schema_version": _clean(getattr(item, "schema_version", "")),
        "source_kind": _clean(getattr(item, "source_kind", "")),
        "source_id": _clean(getattr(item, "source_id", "")),
        "source_updated_at": _clean(getattr(item, "source_updated_at", "")),
        "anchor_count": anchor_count,
        "group_counts": {key: len(values) for key, values in groups.items()},
        "sample_labels": labels[:6],
        "sample_reply_hints": hints[:4],
    }


def _cross_core_source_key(source_kind: Any) -> str:
    kind = _clean(source_kind).lower()
    if kind in {"piece", "emotion_piece", "generated_piece"}:
        return "piece"
    if kind in {"emotion_report", "analysis_report", "emotion_analysis"}:
        return "emotion_report"
    if kind in {"self_structure_report", "self_report", "myprofile_report"}:
        return "self_structure_report"
    return kind or "cross_core_context"


def _cross_core_context_meta(world_model: WorldModel) -> Dict[str, Any]:
    packets = list(getattr(world_model.facts, "cross_core_context", []) or [])
    source_kinds = sorted({
        _cross_core_source_key(getattr(packet, "source_kind", ""))
        for packet in packets
        if _cross_core_source_key(getattr(packet, "source_kind", ""))
    })
    anchor_count = 0
    for packet in packets:
        for key in ("value_anchors", "state_anchors", "individuality_anchors", "boundary_anchors", "concept_anchors", "reply_hints"):
            anchor_count += len(list(getattr(packet, key, []) or []))
    return {
        "enabled": bool(packets),
        "matched_packet_count": len(packets),
        "source_kinds": source_kinds,
        "anchor_count": anchor_count,
        "current_input_filtered": True,
        "current_input_priority": True,
        "sample_packets": [_serialize_cross_core_anchor_packet(packet) for packet in packets[:5]],
    }


def _serialize_meaning_block(item: Any) -> Dict[str, Any]:
    return {
        "block_key": _clean(getattr(item, "block_key", "")),
        "role": _clean(getattr(item, "role", "")),
        "title": _clean(getattr(item, "title", "")),
        "summary": _clean(getattr(item, "summary", "")),
        "priority": float(getattr(item, "priority", 0.0) or 0.0),
        "clarity": float(getattr(item, "clarity", 0.0) or 0.0),
        "include_in_emlis_reply": bool(getattr(item, "include_in_emlis_reply", False)),
        "include_in_piece_core": bool(getattr(item, "include_in_piece_core", False)),
    }


def _serialize_whole_input_arc(item: Any) -> Dict[str, Any]:
    if item is None:
        return {}
    return {
        "arc_key": _clean(getattr(item, "arc_key", "")),
        "title": _clean(getattr(item, "title", "")),
        "summary": _clean(getattr(item, "summary", "")),
        "ordered_block_keys": list(getattr(item, "ordered_block_keys", []) or []),
        "core_wish_keys": list(getattr(item, "core_wish_keys", []) or []),
        "fear_keys": list(getattr(item, "fear_keys", []) or []),
        "present_action_keys": list(getattr(item, "present_action_keys", []) or []),
        "clarity": float(getattr(item, "clarity", 0.0) or 0.0),
    }


def _serialize_major_retention(item: Any) -> Dict[str, Any]:
    if item is None:
        return {}
    return {
        "clear_long_input": bool(getattr(item, "clear_long_input", False)),
        "total_block_count": int(getattr(item, "total_block_count", 0) or 0),
        "must_keep_block_keys": list(getattr(item, "must_keep_block_keys", []) or []),
        "should_keep_block_keys": list(getattr(item, "should_keep_block_keys", []) or []),
        "optional_block_keys": list(getattr(item, "optional_block_keys", []) or []),
        "forbidden_overcompression_targets": list(getattr(item, "forbidden_overcompression_targets", []) or []),
        "min_must_keep_coverage_ratio": float(getattr(item, "min_must_keep_coverage_ratio", 0.0) or 0.0),
        "reason": _clean(getattr(item, "reason", "")),
    }



def _serialize_observation_frame(item: Any) -> Dict[str, Any]:
    if item is None:
        return {"present": False}
    return {
        "present": True,
        "primary_state": _clean(getattr(item, "primary_state", "")),
        "tension_pairs": [
            {
                "left": _clean(getattr(pair, "left", "")),
                "right": _clean(getattr(pair, "right", "")),
                "relation": _clean(getattr(pair, "relation", "")),
            }
            for pair in list(getattr(item, "tension_pairs", []) or [])
        ],
        "pressure_sources": [_clean(v) for v in list(getattr(item, "pressure_sources", []) or []) if _clean(v)],
        "escape_or_limit_signal": _clean(getattr(item, "escape_or_limit_signal", "")),
        "self_awareness_signal": _clean(getattr(item, "self_awareness_signal", "")),
        "strength_signal": _clean(getattr(item, "strength_signal", "")),
        "companion_close": _clean(getattr(item, "companion_close", "")),
        "evidence_terms": [_clean(v) for v in list(getattr(item, "evidence_terms", []) or []) if _clean(v)],
        "required_line_roles": [_clean(v) for v in list(getattr(item, "required_line_roles", []) or []) if _clean(v)],
    }

def _serialize_value_observation_signal(item: Any) -> Dict[str, Any]:
    as_meta = getattr(item, "as_meta", None)
    if callable(as_meta):
        try:
            payload = as_meta()
            if isinstance(payload, dict):
                return dict(payload)
        except Exception:
            pass
    return {
        "signal_key": _clean(getattr(item, "signal_key", "")),
        "title": _clean(getattr(item, "title", "")),
        "observation_axis": _clean(getattr(item, "observation_axis", "")),
        "evidence_terms": list(getattr(item, "evidence_terms", []) or []),
        "target_cores": list(getattr(item, "target_cores", []) or []),
        "confidence": float(getattr(item, "confidence", 0.0) or 0.0),
        "no_diagnosis": bool(getattr(item, "no_diagnosis", True)),
        "no_personality_claim": bool(getattr(item, "no_personality_claim", True)),
    }


def _value_observation_meta(world_model: WorldModel) -> Dict[str, Any]:
    signals = list(getattr(world_model.facts, "value_observation_signals", []) or [])
    plan = getattr(world_model.facts, "value_observation_plan", None)
    as_meta = getattr(plan, "as_meta", None)
    if callable(as_meta):
        plan_payload = as_meta()
    else:
        plan_payload = {
            "input_level": "none",
            "signal_count": len(signals),
            "primary_signal_keys": [str(getattr(item, "signal_key", "") or "") for item in signals[:1]],
            "must_keep_signal_keys": [str(getattr(item, "signal_key", "") or "") for item in signals],
            "optional_signal_keys": [],
            "overcompression_risk": bool(signals),
            "grounding_terms": [],
        }
    return {
        "plan": dict(plan_payload or {}),
        "signals": [_serialize_value_observation_signal(item) for item in signals],
    }


def _composition_meta(world_model: WorldModel) -> Dict[str, Any]:
    plan = getattr(world_model.facts, "response_composition_plan", None)
    arc = getattr(world_model.facts, "reply_narrative_arc", None)
    frame = getattr(world_model.facts, "emlis_observation_frame", None)
    frame_payload = _serialize_observation_frame(frame)
    observation_fields = {
        "observation_frame_present": bool(frame_payload.get("present")),
        "observation_primary_state": _clean(frame_payload.get("primary_state")),
        "observation_required_line_roles": list(frame_payload.get("required_line_roles") or []),
    }
    if plan is None:
        return {
            "composition_key": "observation_frame.v1" if frame_payload.get("present") else "",
            "narrative_pattern": "emlis_observation_frame" if frame_payload.get("present") else "",
            "opening_thesis_present": bool(frame_payload.get("primary_state")),
            "response_composition_ok": True,
            "current_input_grounding_ok": True,
            "stale_meaning_block_leak_blocked": True,
            **observation_fields,
        }
    return {
        "composition_key": _clean(getattr(plan, "composition_key", "")),
        "narrative_pattern": _clean(getattr(plan, "narrative_pattern", "")),
        "ordered_line_roles": list(getattr(plan, "ordered_line_roles", []) or []),
        "required_line_roles": list(getattr(plan, "required_line_roles", []) or []),
        "opening_thesis": _clean(getattr(arc, "opening_thesis", "")) if arc is not None else "",
        "opening_thesis_present": bool(_clean(getattr(arc, "opening_thesis", "")) if arc is not None else "") or bool(frame_payload.get("primary_state")),
        "transition_policy": _clean(getattr(plan, "transition_policy", "")),
        "response_composition_ok": True,
        "current_input_grounding_ok": True,
        "stale_meaning_block_leak_blocked": True,
        **observation_fields,
    }

def _meaning_coverage_meta(world_model: WorldModel, plan: ReplyPlan) -> Dict[str, Any]:
    coverage = getattr(world_model.facts, "meaning_coverage_plan", None)
    frame = getattr(world_model.facts, "emlis_observation_frame", None)
    frame_payload = _serialize_observation_frame(frame)
    observation_meta = {
        "observation_frame_present": bool(frame_payload.get("present")),
        "observation_required_line_roles": list(frame_payload.get("required_line_roles") or []),
        "observation_evidence_terms": list(frame_payload.get("evidence_terms") or []),
    }
    blocks = list(getattr(world_model.facts, "meaning_blocks", []) or [])
    arc = getattr(world_model.facts, "whole_input_meaning_arc", None)
    retention = getattr(world_model.facts, "major_meaning_retention_plan", None)
    length_plan = plan.reply_length_plan
    if coverage is None:
        return {
            "input_level": "none",
            "clear_long_input": False,
            "meaning_block_count": len(blocks),
            "selected_block_count": 0,
            "selected_block_keys": [],
            "required_roles": [],
            "min_blocks_to_cover": 0,
            "coverage_ratio_target": 0.0,
            "sample_blocks": [_serialize_meaning_block(item) for item in blocks[:12]],
            "whole_input_meaning_arc": _serialize_whole_input_arc(arc),
            **observation_meta,
            **_serialize_major_retention(retention),
        }
    selected_keys = list(getattr(coverage, "selected_block_keys", []) or [])
    if length_plan is not None and int(getattr(length_plan, "selected_meaning_block_count", 0) or 0) > 0:
        selected_count = int(getattr(length_plan, "selected_meaning_block_count", 0) or 0)
    else:
        selected_count = len(selected_keys)
    return {
        "input_level": _clean(getattr(coverage, "input_level", "")),
        "clear_long_input": bool(getattr(coverage, "clear_long_input", False)),
        "meaning_block_count": int(getattr(coverage, "meaning_block_count", len(blocks)) or len(blocks)),
        "selected_block_count": selected_count,
        "selected_block_keys": selected_keys,
        "required_roles": list(getattr(coverage, "required_roles", []) or []),
        "min_blocks_to_cover": int(getattr(coverage, "min_blocks_to_cover", 0) or 0),
        "max_blocks_to_cover": int(getattr(coverage, "max_blocks_to_cover", 0) or 0),
        "coverage_ratio_target": float(getattr(coverage, "coverage_ratio_target", 0.0) or 0.0),
        "reason": _clean(getattr(coverage, "reason", "")),
        "sample_blocks": [_serialize_meaning_block(item) for item in blocks[:12]],
        "whole_input_meaning_arc": _serialize_whole_input_arc(arc),
        **observation_meta,
        **_serialize_major_retention(retention),
    }


def _reply_depth_meta(plan: ReplyPlan, capability: EmlisAICapabilityConfig) -> Dict[str, Any]:
    length_plan = plan.reply_length_plan
    if length_plan is None:
        return {
            "target_lines": 0,
            "max_lines": int(capability.max_reply_lines or 0),
            "tier_ceiling": int(capability.max_reply_lines or 0),
            "evidence_ceiling": 0,
            "history_usable": False,
            "interpretive_frame_usable": False,
            "cross_core_usable": False,
            "reason": "missing_reply_length_plan",
        }
    return {
        "target_lines": int(length_plan.target_lines or length_plan.max_lines or 0),
        "max_lines": int(length_plan.max_lines or 0),
        "tier_ceiling": int(length_plan.tier_ceiling or capability.max_reply_lines or 0),
        "evidence_ceiling": int(length_plan.evidence_ceiling or 0),
        "input_effort_score": float(length_plan.input_effort_score or 0.0),
        "memory_richness_score": float(length_plan.memory_richness_score or 0.0),
        "user_word_anchor_count": int(length_plan.user_word_anchor_count or 0),
        "history_usable": bool(length_plan.history_usable),
        "interpretive_frame_usable": bool(length_plan.interpretive_frame_usable),
        "cross_core_usable": bool(getattr(length_plan, "cross_core_usable", False)),
        "meaning_block_count": int(getattr(length_plan, "meaning_block_count", 0) or 0),
        "selected_meaning_block_count": int(getattr(length_plan, "selected_meaning_block_count", 0) or 0),
        "meaning_coverage_ratio": float(getattr(length_plan, "meaning_coverage_ratio", 0.0) or 0.0),
        "clear_long_input": bool(getattr(length_plan, "clear_long_input", False)),
        "major_must_keep_count": int(getattr(length_plan, "major_must_keep_count", 0) or 0),
        "major_must_keep_covered_count": int(getattr(length_plan, "major_must_keep_covered_count", 0) or 0),
        "major_must_keep_coverage_ratio": float(getattr(length_plan, "major_must_keep_coverage_ratio", 0.0) or 0.0),
        "reason": _clean(length_plan.reason),
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
    normalized = [_naturalize_reply_line(greeting_text)] if str(greeting_text or "").strip() else []
    normalized.extend(_naturalize_reply_line(line.text) for line in reply_lines if str(line.text or "").strip())
    return "\n".join(line for line in normalized if line).strip()


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


def _understanding_meta(world_model: WorldModel, plan: ReplyPlan) -> Dict[str, Any]:
    frame = getattr(world_model.facts, "understanding_frame", None)
    patterns = list(getattr(world_model.facts, "understanding_patterns", []) or [])
    role_fields = (
        "event",
        "action",
        "relationship_or_other",
        "boundary_violation",
        "self_awareness",
        "self_fault_awareness",
        "self_avoidance",
        "justification",
        "fear_of_rejection",
        "self_dislike",
        "guilt_or_remorse",
        "explicit_emotion",
        "need_or_wish",
        "unresolved",
        "work_frustration",
        "mentor_attachment",
        "missing_guidance",
        "effort_confusion",
        "anger_surface",
        "sadness_surface",
        "relief_source",
        "chat_relief",
        "fatigue_accumulation",
    )
    roles_used: List[str] = []
    if frame is not None:
        for field_name in role_fields:
            anchor = getattr(frame, field_name, None)
            role = _clean(getattr(anchor, "role", "")) if anchor is not None else ""
            if role and role not in roles_used:
                roles_used.append(role)
    understanding_line_count = sum(
        1
        for line in list(plan.reply_lines or [])
        if line.key == "receive" or str(line.candidate_key or "").startswith("word_reflection.") or line.key == "selected_emotions"
    )
    return {
        "frame_version": "understanding_frame.v1",
        "patterns": patterns,
        "anchor_roles_used": roles_used,
        "understanding_line_count": understanding_line_count,
        "confidence": float(getattr(frame, "confidence", 0.0) or 0.0),
    }


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
    if capability.history_mode != "none" and (bundle.last_input or bundle.same_day_recent_inputs or bundle.similar_inputs):
        used_sources.append("history")
    if capability.include_input_summary:
        used_sources.append("input_summary")
    if capability.include_myweb_summary:
        used_sources.append("myweb_home_summary")
    if capability.include_today_question_history:
        used_sources.append("today_question")
    if bundle.greeting:
        used_sources.append("greeting_state")
    if bundle.derived_user_model is not None:
        used_sources.append("derived_user_model")
        used_memory_layers.append("derived_user_model")
    if bundle.side_state:
        used_memory_layers.append("side_state")
    matched_cross_core_context = list(getattr(world_model.facts, "cross_core_context", []) or [])
    if capability.cross_core_enabled and matched_cross_core_context:
        if "cross_core_context" not in used_memory_layers:
            used_memory_layers.append("cross_core_context")
        for packet in matched_cross_core_context:
            source_key = _cross_core_source_key(getattr(packet, "source_kind", ""))
            if source_key and source_key not in used_sources:
                used_sources.append(source_key)

    evidence_by_line: Dict[str, Any] = {}
    for line in plan.reply_lines:
        if not line.sentence_evidence.evidence:
            continue
        evidence_key = line.key
        if evidence_key in evidence_by_line:
            evidence_key = line.candidate_key or f"{line.key}:{len(evidence_by_line)}"
        evidence_by_line[evidence_key] = [_serialize_evidence_ref(item) for item in line.sentence_evidence.evidence]

    selected_emotions = [_serialize_emotion_display_item(item) for item in list(world_model.facts.selected_emotions or [])]
    dominant_emotion = next((item for item in selected_emotions if item.get("role") == "dominant"), None)
    secondary_emotions = [item for item in selected_emotions if item.get("role") != "dominant"]
    user_word_anchors = list(world_model.facts.user_word_anchors or [])
    shaped_user_phrases = list(getattr(world_model.facts, "shaped_user_phrases", []) or [])
    used_anchor_keys = {
        _clean((line.candidate_key or "").replace("word_reflection.", ""))
        for line in plan.reply_lines
        if line.key == "word_reflection"
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
            "source_scope": capability.source_scope,
            "cross_core_enabled": bool(capability.cross_core_enabled),
            "structure_model_enabled": bool(capability.structure_model_enabled),
        },
        "display": {
            "display_name_call": display_name_call(bundle.display_name),
            "selected_emotions": selected_emotions,
            "dominant_emotion": dominant_emotion,
            "secondary_emotions": secondary_emotions,
        },
        "reply_depth": _reply_depth_meta(plan, capability),
        "anchor_summary": {
            "user_word_anchor_count": len(user_word_anchors),
            "used_user_word_anchor_count": sum(1 for line in plan.reply_lines if line.key == "word_reflection"),
            "sample_user_word_anchors": [_serialize_user_word_anchor(item) for item in user_word_anchors[:8]],
            "used_anchor_keys": sorted(v for v in used_anchor_keys if v),
        },
        "phrase_shaping": {
            "version": "emlis.phrase_shaping.v1",
            "raw_anchor_count": len(user_word_anchors),
            "safe_phrase_count": sum(1 for item in shaped_user_phrases if _clean(getattr(item, "usability", "safe")) in {"safe", "needs_context"}),
            "unsafe_phrase_count": sum(1 for item in shaped_user_phrases if _clean(getattr(item, "usability", "safe")) == "unsafe"),
            "sample_shaped_phrases": [_serialize_shaped_user_phrase(item) for item in shaped_user_phrases[:8]],
            "unsafe_reasons": sorted({reason for item in shaped_user_phrases for reason in list(getattr(item, "unsafe_reasons", []) or []) if str(reason)}),
        },
        "meaning_coverage": _meaning_coverage_meta(world_model, plan),
        "whole_input_meaning_arc": _serialize_whole_input_arc(getattr(world_model.facts, "whole_input_meaning_arc", None)),
        "major_meaning_retention": _serialize_major_retention(getattr(world_model.facts, "major_meaning_retention_plan", None)),
        "value_observation": _value_observation_meta(world_model),
        "emlis_observation_frame": _serialize_observation_frame(getattr(world_model.facts, "emlis_observation_frame", None)),
        "composition": _composition_meta(world_model),
        "understanding": _understanding_meta(world_model, plan),
        "cross_core_context": _cross_core_context_meta(world_model),
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


def _final_review_meta(review: Any, *, repair_applied: bool) -> Dict[str, Any]:
    return {
        "version": _clean(getattr(review, "review_version", "emlis.final_reader.v1")) or "emlis.final_reader.v1",
        "passed": bool(getattr(review, "passed", False)),
        "repair_applied": bool(repair_applied),
        "issues": [
            {
                "code": _clean(getattr(issue, "code", "")),
                "severity": _clean(getattr(issue, "severity", "")),
                "line_index": getattr(issue, "line_index", None),
                "message": _clean(getattr(issue, "message", ""))[:160],
            }
            for issue in list(getattr(review, "issues", []) or [])
        ],
    }


def _issue_codes_from_review(review: Any) -> List[str]:
    return [
        _clean(getattr(issue, "code", ""))
        for issue in list(getattr(review, "issues", []) or [])
        if _clean(getattr(issue, "code", ""))
    ]


def _evaluate_pre_return_gate(
    *,
    comment_text: str,
    capability: EmlisAICapabilityConfig,
    meta: Dict[str, Any],
    fallback_used: bool,
    final_reader_passed: bool,
    repair_attempted: bool = False,
    repair_passed: bool = False,
    safe_fallback_used: bool = False,
    blocked_issue_codes: Optional[List[str]] = None,
):
    reply_depth = meta.get("reply_depth") if isinstance(meta.get("reply_depth"), dict) else {}
    anchor_summary = meta.get("anchor_summary") if isinstance(meta.get("anchor_summary"), dict) else {}
    understanding = meta.get("understanding") if isinstance(meta.get("understanding"), dict) else {}
    meaning_coverage = meta.get("meaning_coverage") if isinstance(meta.get("meaning_coverage"), dict) else {}
    composition = meta.get("composition") if isinstance(meta.get("composition"), dict) else {}
    allowed_line_count = int(reply_depth.get("tier_ceiling") or getattr(capability, "max_reply_lines", 3) or 3) + 1
    return evaluate_emlis_ai_quality_gate(
        comment_text=comment_text,
        capability=capability,
        used_sources=meta.get("used_sources") if isinstance(meta.get("used_sources"), list) else [],
        evidence_by_line=meta.get("evidence_by_line") if isinstance(meta.get("evidence_by_line"), dict) else {},
        fallback_used=fallback_used,
        allowed_line_count=allowed_line_count,
        sample_user_word_anchors=anchor_summary.get("sample_user_word_anchors") if isinstance(anchor_summary.get("sample_user_word_anchors"), list) else [],
        user_word_anchor_count=int(anchor_summary.get("user_word_anchor_count") or 0),
        understanding_patterns=understanding.get("patterns") if isinstance(understanding.get("patterns"), list) else [],
        final_reader_passed=final_reader_passed,
        pre_return_blocking_enabled=True,
        repair_attempted=repair_attempted,
        repair_passed=repair_passed,
        safe_fallback_used=safe_fallback_used,
        blocked_issue_codes=blocked_issue_codes or [],
        meaning_coverage=meaning_coverage,
        composition=composition,
    )



def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


def _multi_perspective_meta(
    *,
    trace_id: str,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    evidence_spans: List[Any],
    reports: List[Any],
    board: Any,
    graph: Any,
    reader_report: Any,
    grounding_report: Any,
    template_echo_report: Any,
    display_decision: Any,
    composer_source: str = "",
    composer_candidate: Any = None,
    composer_backend_ready: bool = True,
) -> Dict[str, Any]:
    used_sources: List[str] = ["current_input"]
    if bundle.greeting:
        used_sources.append("greeting_state")
    if capability.include_input_summary:
        used_sources.append("input_summary")
    if capability.history_mode != "none" and (bundle.last_input or bundle.same_day_recent_inputs or bundle.similar_inputs):
        used_sources.append("history")
    used_memory_layers: List[str] = ["canonical_history"]
    if bundle.derived_user_model is not None:
        used_memory_layers.append("derived_user_model")
    if bundle.side_state:
        used_memory_layers.append("side_state")
    phase4_ready = phase4_observer_contract_ready(reports, evidence_spans)
    phase5_board_ready = phase5_board_contract_ready(board)
    phase5_graph_ready = phase5_observation_graph_ready(board, graph)
    phase5_ready = bool(phase4_ready and phase5_board_ready and phase5_graph_ready)
    phase6_ready = bool(phase5_ready and phase6_composer_contract_ready())
    phase7_ready = bool(
        phase6_ready
        and phase7_judge_contract_ready(
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            composer_source=str(composer_source or ""),
        )
    )
    phase8_ready = bool(phase7_ready and phase8_display_gate_contract_ready(display_decision))
    release_readiness = build_phase10_release_readiness(
        display_decision=display_decision,
        frontend_display_control_ready=phase8_ready,
        composer_backend_ready=composer_backend_ready,
    )
    phase9_ready = bool(phase8_ready and release_readiness.get("phase9_frontend_display_control_ready"))
    phase10_ready = bool(phase9_ready and release_readiness.get("phase10_regression_release_ready"))
    completed_phases = (
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        if phase10_ready
        else (
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            if phase9_ready
            else ([0, 1, 2, 3, 4, 5, 6, 7, 8] if phase8_ready else ([0, 1, 2, 3, 4, 5, 6, 7] if phase7_ready else ([0, 1, 2, 3, 4, 5, 6] if phase6_ready else ([0, 1, 2, 3, 4, 5] if phase5_ready else ([0, 1, 2, 3, 4] if phase4_ready else [0, 1, 2, 3])))))
        )
    )
    gate_trace = getattr(display_decision, "gate_trace", {}) or build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        composer_source=str(composer_source or ""),
        phase_completion_ready=False,
    )
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": capability.tier,
        "observation_status": display_decision.observation_status,
        "observation_trace_id": trace_id,
        "rejection_reasons": list(display_decision.rejection_reasons),
        "display": {
            "display_name_call": display_name_call(bundle.display_name),
            "visible_name": "Emlisの観測",
        },
        "capability": {
            "history_mode": capability.history_mode,
            "continuity_mode": capability.continuity_mode,
            "style_mode": capability.style_mode,
            "partner_mode": capability.partner_mode,
            "model_mode": capability.model_mode,
            "interpretation_mode": capability.interpretation_mode,
            "source_scope": capability.source_scope,
            "cross_core_enabled": bool(capability.cross_core_enabled),
            "structure_model_enabled": bool(capability.structure_model_enabled),
        },
        "multi_perspective": {
            "architecture_version": "emlis.multi_perspective.v1",
            "fail_closed": True,
            "legacy_observation_kernel_used": False,
            "legacy_safe_fallback_used": False,
            "legacy_input_feedback_template_used": False,
            "evidence_span_count": len(evidence_spans),
            "observer_count": len(reports),
            "observer_ids": [str(getattr(report, "observer_id", "")) for report in reports],
            "evidence_spans": _jsonable(evidence_spans[:12]),
            "perspective_reports": _jsonable(reports),
            "perspective_board": _jsonable(board),
            "observation_graph": _jsonable(graph),
            "reader_report": _jsonable(reader_report),
            "grounding_report": _jsonable(grounding_report),
            "template_echo_report": _jsonable(template_echo_report),
            "gate_trace": gate_trace,
            "composer_candidate": _jsonable(composer_candidate) if composer_candidate is not None else {},
            "composer_source": str(composer_source or ""),
            "composer_status": str(getattr(composer_candidate, "status", "") or ""),
            "composer_rejection_reasons": list(getattr(composer_candidate, "rejection_reasons", []) or []),
            "phase_gate": {
                "completed_phases": completed_phases,
                "current_phase": 10 if phase10_ready else (9 if phase9_ready else (8 if phase8_ready else (7 if phase7_ready else (6 if phase6_ready else (5 if phase5_ready else (4 if phase4_ready else 3)))))),
                "next_phase": None if phase10_ready else (10 if phase9_ready else (9 if phase8_ready else (8 if phase7_ready else (7 if phase6_ready else (6 if phase5_ready else (5 if phase4_ready else 4)))))),
                "phase_completion_ready": phase10_ready,
                "release_ready": bool(release_readiness.get("release_ready")),
                "release_blockers": list(release_readiness.get("release_blockers") or []),
                "required_completed_phases": list(release_readiness.get("required_completed_phases") or []),
                "release_checks": dict(release_readiness.get("release_checks") or {}),
                "legacy_text_routes_sealed": True,
                "type_state_contract_ready": True,
                "evidence_ledger_ready": True,
                "specialist_observers_ready": phase4_ready,
                "observer_contract_only_structured": phase4_ready,
                "perspective_board_ready": phase5_board_ready,
                "observation_graph_ready": phase5_graph_ready,
                "composer_contract_ready": phase6_ready,
                "reader_gate_ready": isinstance(gate_trace.get("reader"), dict),
                "grounding_gate_ready": isinstance(gate_trace.get("grounding"), dict),
                "template_echo_gate_ready": isinstance(gate_trace.get("template_echo"), dict),
                "judge_contract_ready": phase7_ready,
                "composer_backend_ready": bool(composer_backend_ready),
                "composer_default_configured": bool(is_default_conversation_composer_configured()),
                "composer_candidate_available": str(getattr(composer_candidate, "composer_source", "") or "") == "ai_generated",
                "composer_status": str(getattr(composer_candidate, "status", "") or ""),
                "board_validation_issues": validate_perspective_board(board),
                "graph_validation_issues": validate_observation_graph(graph, board),
                "gate_trace": gate_trace,
                "display_gate_ready": phase8_ready,
                "display_gate_release_ready": bool(release_readiness.get("display_gate_release_ready")),
                "frontend_display_control_ready": phase9_ready,
                "phase9_frontend_display_control_ready": bool(release_readiness.get("phase9_frontend_display_control_ready")),
                "phase10_regression_release_ready": phase10_ready,
                "regression_release_tests_ready": phase10_ready,
                "comment_text_allowed": bool(phase8_ready and display_decision.observation_status == "passed" and str(display_decision.comment_text or "").strip()),
            },
        },
        "used_sources": used_sources,
        "used_memory_layers": used_memory_layers,
        "reply_length_mode": capability.reply_length_mode,
        "evidence_count": len(evidence_spans),
        "evidence_by_line": {},
        "rejected_candidate_count": 0,
        "fallback_used": False,
        "world_model_debug": {
            "board_report_count": len(getattr(board, "reports", []) or []),
            "missing_information": list(getattr(graph, "missing_information", []) or []),
        },
    }


async def render_emlis_ai_reply(
    *,
    user_id: str,
    subscription_tier: Any,
    current_input: Dict[str, Any],
    display_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
    composer_client: Any = None,
) -> ReplyEnvelope:
    """Render an immediate Emlis observation using the multi-perspective pipeline.

    This path deliberately does not call the legacy observation kernel, legacy
    safe fallback, or input_feedback_text_templates. If the generated text does
    not pass the reader/grounding/template gates, it returns an empty
    ``comment_text`` with ``observation_status`` set to rejected/safety_blocked.
    """

    trace_id = f"emlisobs-{uuid4().hex[:16]}"
    capability = resolve_emlis_ai_capability_for_tier(subscription_tier)
    bundle = await build_emlis_ai_source_bundle(
        user_id=user_id,
        current_input=current_input,
        capability=capability,
        display_name=display_name,
        timezone_name=timezone_name,
    )

    evidence_spans = build_evidence_ledger(current_input)
    reports = run_perspective_observers(evidence_spans)
    board = build_perspective_board(evidence_spans=evidence_spans, reports=reports)
    graph = integrate_perspective_board(board=board, display_name=bundle.display_name or display_name)

    safety_requires_block = bool(getattr(graph, "safety_boundaries", []) or [])
    safety_report = None
    if safety_requires_block:
        from emlis_ai_types import SafetyBoundaryReport

        safety_report = SafetyBoundaryReport(requires_block=True, reasons=["safety_boundary"])

    # Phase 8: run Display Gate as the final fail-closed boundary.  The gate may
    # allow a Composer AI candidate only when every judge passes, the source is
    # ai_generated, and the pipeline phases through Judge are structurally ready.
    # On judge rejection, a single regeneration attempt may be requested with
    # rejection reason codes only.  No sample text or fallback observation is sent.
    phase5_ready = bool(phase4_observer_contract_ready(reports, evidence_spans) and phase5_board_contract_ready(board) and phase5_observation_graph_ready(board, graph))
    phase6_ready = bool(phase5_ready and phase6_composer_contract_ready())
    effective_composer_client = composer_client if composer_client is not None else get_default_conversation_composer_client()
    composer_backend_ready = bool(effective_composer_client is not None)
    composer_candidate = None
    comment_text = ""
    composer_source = ""
    reader_report = judge_listener_readability("")
    grounding_report = judge_grounding(comment_text="", graph=graph, evidence_spans=evidence_spans)
    template_echo_report = guard_template_echo(comment_text="", evidence_spans=evidence_spans, composer_source="unavailable")
    display_decision = decide_emlis_observation_display(
        comment_text="",
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        safety_report=safety_report,
        trace_id=trace_id,
        composer_source="unavailable" if not safety_requires_block else "",
        phase_completion_ready=phase6_ready,
    )

    max_attempts = 2 if effective_composer_client is not None and not safety_requires_block else 1
    regeneration_reasons: List[str] = []
    for attempt in range(1, max_attempts + 1):
        composer_candidate = compose_emlis_conversation_candidate(
            graph=graph,
            evidence_spans=evidence_spans,
            display_name=bundle.display_name or display_name,
            greeting_text=build_emlis_observation_greeting(
                display_name=bundle.display_name or display_name,
                greeting_text=getattr(bundle.greeting, "greeting_text", "") if bundle.greeting else "",
            ),
            composer_client=None if safety_requires_block else effective_composer_client,
            trace_id=trace_id,
            attempt_count=attempt,
            rejection_reasons=regeneration_reasons,
        )
        comment_text = "" if safety_requires_block else str(composer_candidate.comment_text or "").strip()
        composer_source = "" if safety_requires_block else str(composer_candidate.composer_source or "")
        reader_report = judge_listener_readability(comment_text)
        grounding_report = judge_grounding(comment_text=comment_text, graph=graph, evidence_spans=evidence_spans)
        template_echo_report = guard_template_echo(comment_text=comment_text, evidence_spans=evidence_spans, composer_source=composer_source)
        phase7_ready = bool(
            phase6_ready
            and phase7_judge_contract_ready(
                reader_report=reader_report,
                grounding_report=grounding_report,
                template_echo_report=template_echo_report,
                composer_source=composer_source,
            )
        )
        display_decision = decide_emlis_observation_display(
            comment_text=comment_text,
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            safety_report=safety_report,
            trace_id=trace_id,
            composer_source=composer_source,
            phase_completion_ready=phase7_ready,
        )
        if display_decision.observation_status in {"passed", "safety_blocked"}:
            break
        if effective_composer_client is None or attempt >= max_attempts or str(getattr(composer_candidate, "status", "") or "") == "unavailable":
            break
        regeneration_reasons = list(display_decision.rejection_reasons or [])

    # No fixed fallback. The display gate is fail-closed.
    final_text = str(display_decision.comment_text or "").strip()
    meta = _multi_perspective_meta(
        trace_id=trace_id,
        capability=capability,
        bundle=bundle,
        evidence_spans=evidence_spans,
        reports=reports,
        board=board,
        graph=graph,
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        display_decision=display_decision,
        composer_source=composer_source,
        composer_candidate=composer_candidate,
        composer_backend_ready=composer_backend_ready,
    )

    return ReplyEnvelope(
        comment_text=final_text,
        meta=meta,
        used_evidence=[],
        evidence_by_line={},
        used_memory_layers=meta.get("used_memory_layers") if isinstance(meta.get("used_memory_layers"), list) else ["canonical_history"],
        fallback_used=False,
    )
