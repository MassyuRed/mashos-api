from __future__ import annotations

"""
Self structure engine payload builders.

Intended location:
    analysis_engine/self_structure_engine/builders.py

Role in the pipeline:
    FusionResult
        -> deterministic analysis_results.payload rows

This module is intentionally side-effect free:
- it does not read or write the DB
- it does not create snapshots
- it does not update identity_state incrementally
- it does not perform publish checks
- it does not generate final user-facing prose reports

It only converts fused self-structure analysis results into stable,
storage-oriented payloads that downstream ASTOR / MyProfile report builders can
consume.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # expected package import
    from ..models import (
        BuildContext,
        FusionResult,
        PatternScore,
        RoleGap,
        SignalExtractionResult,
        TargetSignature,
        TargetRoleScore,
        UnknownNeed,
        WorldRoleEvidence,
    )
except Exception:  # local / standalone fallback
    try:
        from models_updated import (  # type: ignore
            BuildContext,
            FusionResult,
            PatternScore,
            RoleGap,
            SignalExtractionResult,
            TargetSignature,
            TargetRoleScore,
            UnknownNeed,
            WorldRoleEvidence,
        )
    except Exception:
        from models import (  # type: ignore
            BuildContext,
            FusionResult,
            PatternScore,
            RoleGap,
            SignalExtractionResult,
            TargetSignature,
            TargetRoleScore,
            UnknownNeed,
            WorldRoleEvidence,
        )

try:  # expected package import
    from .rules import (
        ACTION_DIRECTION_PHRASES,
        ROLE_LABELS_JA,
        ROLE_SUMMARIES_JA,
        THINKING_PURPOSE_PHRASES,
    )
except Exception:  # local / standalone fallback
    from rules import (  # type: ignore
        ACTION_DIRECTION_PHRASES,
        ROLE_LABELS_JA,
        ROLE_SUMMARIES_JA,
        THINKING_PURPOSE_PHRASES,
    )


SUPPORTED_STAGES = {"standard", "deep"}
DEFAULT_ANALYSIS_TYPE = "self_structure"
DEFAULT_SCOPE = "global"


# =============================================================================
# Generic helpers
# =============================================================================


def _ensure_stage(stage: str) -> str:
    value = (stage or "").strip().lower()
    if value not in SUPPORTED_STAGES:
        raise ValueError(f"Unsupported stage: {stage!r}. Expected one of {sorted(SUPPORTED_STAGES)}")
    return value


def _round_float(value: Any, ndigits: int = 4) -> float:
    try:
        return round(float(value), ndigits)
    except Exception:
        return 0.0


def _to_result(item: SignalExtractionResult | Mapping[str, Any]) -> SignalExtractionResult:
    if isinstance(item, SignalExtractionResult):
        return item
    if isinstance(item, Mapping):
        return SignalExtractionResult(**dict(item))  # type: ignore[arg-type]
    if is_dataclass(item):
        return SignalExtractionResult(**asdict(item))  # type: ignore[arg-type]
    raise TypeError(f"Unsupported signal result type: {type(item)!r}")


def _to_ctx(ctx: BuildContext | Mapping[str, Any]) -> BuildContext:
    if isinstance(ctx, BuildContext):
        return ctx
    if isinstance(ctx, Mapping):
        return BuildContext(**dict(ctx))  # type: ignore[arg-type]
    if is_dataclass(ctx):
        return BuildContext(**asdict(ctx))  # type: ignore[arg-type]
    raise TypeError(f"Unsupported build context type: {type(ctx)!r}")


def _target_label_lookup(fusion: FusionResult) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for item in fusion.target_role_scores:
        if item.target_key and item.target_label_ja:
            lookup[item.target_key] = item.target_label_ja
    for item in getattr(fusion, "target_signatures", []) or []:
        if item.target_key and item.target_label_ja:
            lookup[item.target_key] = item.target_label_ja
    return lookup


# =============================================================================
# Coverage and meta
# =============================================================================


def build_meta_block(ctx: BuildContext, stage: str) -> Dict[str, Any]:
    stage = _ensure_stage(stage)
    return {
        "engine": "analysis_engine",
        "analysis_type": ctx.analysis_type or DEFAULT_ANALYSIS_TYPE,
        "analysis_stage": stage,
        "analysis_version": ctx.analysis_version,
        "scope": ctx.scope or DEFAULT_SCOPE,
        "snapshot_id": ctx.snapshot_id,
        "source_hash": ctx.source_hash,
        "generated_at": ctx.generated_at,
    }


def build_coverage_block(results: Sequence[SignalExtractionResult | Mapping[str, Any]]) -> Dict[str, Any]:
    prepared = [_to_result(x) for x in results]

    source_counts: Dict[str, int] = {}
    reliability_counts: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
    reliable_count = 0
    timestamps: List[str] = []
    target_hit_count = 0

    for r in prepared:
        source_counts[r.source_type] = source_counts.get(r.source_type, 0) + 1
        reliability_counts[r.reliability] = reliability_counts.get(r.reliability, 0) + 1
        if r.reliability in ("medium", "high"):
            reliable_count += 1
        if r.timestamp:
            timestamps.append(r.timestamp)
        if r.primary_target is not None:
            target_hit_count += 1

    timestamps.sort()

    return {
        "evidence_count": len(prepared),
        "reliable_evidence_count": reliable_count,
        "target_evidence_count": target_hit_count,
        "source_counts": dict(sorted(source_counts.items(), key=lambda x: x[0])),
        "reliability_counts": {k: reliability_counts.get(k, 0) for k in ("low", "medium", "high")},
        "time_span_start": timestamps[0] if timestamps else None,
        "time_span_end": timestamps[-1] if timestamps else None,
    }


# =============================================================================
# Serialization helpers
# =============================================================================


def serialize_pattern_scores(items: Sequence[PatternScore], top_k: int) -> List[Dict[str, Any]]:
    rows = []
    for x in list(items)[:top_k]:
        rows.append(
            {
                "key": x.key,
                "label_ja": x.label_ja,
                "score": _round_float(x.score),
            }
        )
    return rows


def serialize_target_role_scores(items: Sequence[TargetRoleScore], top_k: int) -> List[Dict[str, Any]]:
    rows = []
    for x in list(items)[:top_k]:
        rows.append(
            {
                "target_key": x.target_key,
                "target_label_ja": x.target_label_ja,
                "target_type": x.target_type,
                "role_key": x.role_key,
                "role_label_ja": x.role_label_ja,
                "score": _round_float(x.score),
                "evidence_count": int(x.evidence_count),
                "last_seen": x.last_seen,
            }
        )
    return rows


def serialize_world_roles(
    items: Sequence[WorldRoleEvidence],
    top_k: int,
    target_labels: Optional[Mapping[str, str]] = None,
) -> List[Dict[str, Any]]:
    lookup = dict(target_labels or {})
    rows = []
    for x in list(items)[:top_k]:
        rows.append(
            {
                "world_kind": x.world_kind,
                "role_key": x.role_key,
                "role_label_ja": x.role_label_ja,
                "score": _round_float(x.score),
                "target_key": x.target_key,
                "target_label_ja": lookup.get(x.target_key or "", None),
                "reason": x.reason,
            }
        )
    return rows


def serialize_role_gaps(
    items: Sequence[RoleGap],
    top_k: int,
    target_labels: Optional[Mapping[str, str]] = None,
) -> List[Dict[str, Any]]:
    lookup = dict(target_labels or {})
    rows = []
    for x in list(items)[:top_k]:
        rows.append(
            {
                "target_key": x.target_key,
                "target_label_ja": lookup.get(x.target_key or "", None),
                "left_kind": x.left_kind,
                "left_role": x.left_role,
                "left_role_label_ja": ROLE_LABELS_JA.get(x.left_role, x.left_role),
                "right_kind": x.right_kind,
                "right_role": x.right_role,
                "right_role_label_ja": ROLE_LABELS_JA.get(x.right_role, x.right_role),
                "gap_score": _round_float(x.gap_score),
                "note": x.note,
            }
        )
    return rows


def serialize_role_history(items: Sequence[Mapping[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for x in list(items)[:top_k]:
        rows.append(
            {
                "target_key": x.get("target_key"),
                "target_label_ja": x.get("target_label_ja"),
                "target_type": x.get("target_type"),
                "role_key": x.get("role_key"),
                "role_label_ja": x.get("role_label_ja"),
                "score": _round_float(x.get("score", 0.0)),
                "evidence_count": int(x.get("evidence_count", 0) or 0),
                "last_seen": x.get("last_seen"),
                "state": x.get("state"),
            }
        )
    return rows


def serialize_target_signatures(items: Sequence[TargetSignature], top_k: int) -> List[Dict[str, Any]]:
    rows = []
    for x in list(items)[:top_k]:
        rows.append(
            {
                "target_key": x.target_key,
                "target_label_ja": x.target_label_ja,
                "target_type": x.target_type,
                "top_role_key": x.top_role_key,
                "top_role_label_ja": ROLE_LABELS_JA.get(x.top_role_key, x.top_role_key),
                "top_role_score": _round_float(x.top_role_score),
                "top_cluster_key": x.top_cluster_key,
                "top_thinking_keys": list(x.top_thinking_keys[:2]),
                "top_action_keys": list(x.top_action_keys[:2]),
                "evidence_count": int(x.evidence_count),
                "last_seen": x.last_seen,
            }
        )
    return rows


# =============================================================================
# Standard helpers
# =============================================================================


def select_top_targets(target_role_scores: Sequence[TargetRoleScore], k: int = 3) -> List[Dict[str, Any]]:
    target_best: Dict[str, TargetRoleScore] = {}
    for tr in target_role_scores:
        prev = target_best.get(tr.target_key)
        if prev is None or tr.score > prev.score or (tr.score == prev.score and tr.role_key < prev.role_key):
            target_best[tr.target_key] = tr

    selected = sorted(target_best.values(), key=lambda x: (-x.score, x.target_key, x.role_key))[:k]
    return serialize_target_role_scores(selected, top_k=len(selected))


def build_standard_summary(fusion: FusionResult) -> Dict[str, Any]:
    top_role = fusion.template_role_scores[0] if fusion.template_role_scores else None
    top_target = select_top_targets(fusion.target_role_scores, k=1)
    top_thinking = fusion.thinking_patterns[0] if fusion.thinking_patterns else None
    top_action = fusion.action_patterns[0] if fusion.action_patterns else None

    return {
        "core_role": {
            "key": top_role.key,
            "label_ja": top_role.label_ja,
            "score": _round_float(top_role.score),
            "summary_ja": ROLE_SUMMARIES_JA.get(top_role.key),
        } if top_role else None,
        "core_target": top_target[0] if top_target else None,
        "core_thinking": {
            "key": top_thinking.key,
            "label_ja": top_thinking.label_ja,
            "score": _round_float(top_thinking.score),
        } if top_thinking else None,
        "core_action": {
            "key": top_action.key,
            "label_ja": top_action.label_ja,
            "score": _round_float(top_action.score),
        } if top_action else None,
    }


def build_standard_block(fusion: FusionResult) -> Dict[str, Any]:
    return {
        "top_roles": serialize_pattern_scores(fusion.template_role_scores, top_k=3),
        "top_targets": select_top_targets(fusion.target_role_scores, k=3),
        "top_thinking_patterns": serialize_pattern_scores(fusion.thinking_patterns, top_k=3),
        "top_action_patterns": serialize_pattern_scores(fusion.action_patterns, top_k=3),
        "summary": build_standard_summary(fusion),
    }


# =============================================================================
# Deep helpers
# =============================================================================


def compose_generated_role_description(sig: TargetSignature) -> str:
    th_key = sig.top_thinking_keys[0] if sig.top_thinking_keys else None
    act_key = sig.top_action_keys[0] if sig.top_action_keys else None

    purpose = THINKING_PURPOSE_PHRASES.get(th_key, "状況に応じて")
    direction = ACTION_DIRECTION_PHRASES.get(act_key, "動き方を選ぶ")
    return f"{purpose}{direction}役割"


def build_generated_roles(fusion: FusionResult, top_k: int = 5) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for sig in list(getattr(fusion, "target_signatures", []) or [])[:top_k]:
        rows.append(
            {
                "target_key": sig.target_key,
                "target_label_ja": sig.target_label_ja,
                "target_type": sig.target_type,
                "template_role": sig.top_role_key,
                "template_role_label_ja": ROLE_LABELS_JA.get(sig.top_role_key, sig.top_role_key),
                "template_role_summary_ja": ROLE_SUMMARIES_JA.get(sig.top_role_key),
                "cluster": sig.top_cluster_key,
                "description": compose_generated_role_description(sig),
                "score": _round_float(sig.top_role_score),
                "evidence_count": int(sig.evidence_count),
                "last_seen": sig.last_seen,
                "top_thinking_keys": list(sig.top_thinking_keys[:2]),
                "top_action_keys": list(sig.top_action_keys[:2]),
            }
        )
    return rows


def build_question_candidates(unknowns: Sequence[UnknownNeed], top_k: int = 5) -> List[Dict[str, Any]]:
    ranked = sorted(unknowns, key=lambda x: (-x.priority, x.target_key or "", x.kind))[:top_k]
    return [
        {
            "kind": x.kind,
            "priority": _round_float(x.priority),
            "target_key": x.target_key,
            "reason": x.reason,
            "hint": x.hint,
        }
        for x in ranked
    ]


def build_deep_summary(fusion: FusionResult) -> Dict[str, Any]:
    target_labels = _target_label_lookup(fusion)
    top_generated = build_generated_roles(fusion, top_k=1)
    top_cluster = serialize_pattern_scores(fusion.cluster_scores, top_k=1)
    top_gap = serialize_role_gaps(fusion.role_gaps, top_k=1, target_labels=target_labels)

    return {
        "core_generated_role": top_generated[0] if top_generated else None,
        "core_cluster": top_cluster[0] if top_cluster else None,
        "core_gap": top_gap[0] if top_gap else None,
        "unknown_count": len(fusion.unknowns),
    }


def build_deep_block(fusion: FusionResult) -> Dict[str, Any]:
    target_labels = _target_label_lookup(fusion)
    return {
        "generated_roles": build_generated_roles(fusion, top_k=5),
        "cluster_distribution": serialize_pattern_scores(fusion.cluster_scores, top_k=5),
        "target_role_map": serialize_target_role_scores(fusion.target_role_scores, top_k=12),
        "target_signatures": serialize_target_signatures(fusion.target_signatures, top_k=10),
        "self_world_roles": serialize_world_roles(fusion.self_world_roles, top_k=5, target_labels=target_labels),
        "real_world_roles": serialize_world_roles(fusion.real_world_roles, top_k=5, target_labels=target_labels),
        "desired_roles": serialize_world_roles(fusion.desired_roles, top_k=5, target_labels=target_labels),
        "role_gaps": serialize_role_gaps(fusion.role_gaps, top_k=5, target_labels=target_labels),
        "question_candidates": build_question_candidates(fusion.unknowns, top_k=5),
        "summary": build_deep_summary(fusion),
    }


# =============================================================================
# Identity-state block
# =============================================================================


def build_identity_state_block(fusion: FusionResult) -> Dict[str, Any]:
    return {
        "template_role_scores": serialize_pattern_scores(fusion.template_role_scores, top_k=10),
        "cluster_scores": serialize_pattern_scores(fusion.cluster_scores, top_k=5),
        "target_role_scores": serialize_target_role_scores(fusion.target_role_scores, top_k=20),
        "thinking_patterns": serialize_pattern_scores(fusion.thinking_patterns, top_k=10),
        "action_patterns": serialize_pattern_scores(fusion.action_patterns, top_k=10),
        "role_history": serialize_role_history(fusion.role_history, top_k=30),
    }


# =============================================================================
# Row builders
# =============================================================================


def build_self_structure_standard_row(
    ctx: BuildContext | Mapping[str, Any],
    fusion: FusionResult,
    results: Sequence[SignalExtractionResult | Mapping[str, Any]],
) -> Dict[str, Any]:
    ctx_obj = _to_ctx(ctx)
    if fusion.stage != "standard":
        raise ValueError(f"Expected standard fusion result, got: {fusion.stage!r}")

    payload = {
        "meta": build_meta_block(ctx_obj, stage="standard"),
        "coverage": build_coverage_block(results),
        "identity_state": build_identity_state_block(fusion),
        "standard": build_standard_block(fusion),
    }

    return {
        "target_user_id": ctx_obj.target_user_id,
        "snapshot_id": ctx_obj.snapshot_id,
        "analysis_type": ctx_obj.analysis_type or DEFAULT_ANALYSIS_TYPE,
        "scope": ctx_obj.scope or DEFAULT_SCOPE,
        "analysis_stage": "standard",
        "analysis_version": ctx_obj.analysis_version,
        "source_hash": ctx_obj.source_hash,
        "payload": payload,
    }


def build_self_structure_deep_row(
    ctx: BuildContext | Mapping[str, Any],
    fusion: FusionResult,
    results: Sequence[SignalExtractionResult | Mapping[str, Any]],
) -> Dict[str, Any]:
    ctx_obj = _to_ctx(ctx)
    if fusion.stage != "deep":
        raise ValueError(f"Expected deep fusion result, got: {fusion.stage!r}")

    payload = {
        "meta": build_meta_block(ctx_obj, stage="deep"),
        "coverage": build_coverage_block(results),
        "identity_state": build_identity_state_block(fusion),
        "deep": build_deep_block(fusion),
    }

    return {
        "target_user_id": ctx_obj.target_user_id,
        "snapshot_id": ctx_obj.snapshot_id,
        "analysis_type": ctx_obj.analysis_type or DEFAULT_ANALYSIS_TYPE,
        "scope": ctx_obj.scope or DEFAULT_SCOPE,
        "analysis_stage": "deep",
        "analysis_version": ctx_obj.analysis_version,
        "source_hash": ctx_obj.source_hash,
        "payload": payload,
    }


def build_self_structure_rows(
    ctx: BuildContext | Mapping[str, Any],
    standard_fusion: FusionResult,
    standard_results: Sequence[SignalExtractionResult | Mapping[str, Any]],
    deep_fusion: FusionResult | None = None,
    deep_results: Sequence[SignalExtractionResult | Mapping[str, Any]] | None = None,
) -> List[Dict[str, Any]]:
    rows = [
        build_self_structure_standard_row(
            ctx=ctx,
            fusion=standard_fusion,
            results=standard_results,
        )
    ]

    if deep_fusion is not None:
        rows.append(
            build_self_structure_deep_row(
                ctx=ctx,
                fusion=deep_fusion,
                results=deep_results if deep_results is not None else standard_results,
            )
        )

    return rows


__all__ = [
    "BuildContext",
    "build_meta_block",
    "build_coverage_block",
    "serialize_pattern_scores",
    "serialize_target_role_scores",
    "serialize_world_roles",
    "serialize_role_gaps",
    "serialize_role_history",
    "serialize_target_signatures",
    "select_top_targets",
    "build_standard_summary",
    "build_standard_block",
    "compose_generated_role_description",
    "build_generated_roles",
    "build_question_candidates",
    "build_deep_summary",
    "build_deep_block",
    "build_identity_state_block",
    "build_self_structure_standard_row",
    "build_self_structure_deep_row",
    "build_self_structure_rows",
]
