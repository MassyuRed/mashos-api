
from __future__ import annotations

"""
Self structure engine fusion.

Intended location:
    analysis_engine/self_structure_engine/fusion.py

Role in the pipeline:
    SignalExtractionResult[]
        -> aggregate / fuse evidence
        -> derive identity_state-like global structures
        -> produce a FusionResult for builders.py

This module is intentionally deterministic and side-effect free:
- does not read/write the DB
- does not create snapshots
- does not generate final user-facing report text
- does not perform publish or entitlement checks

It is the "analysis integration core" inside the self structure generation
lane and is designed to align with the Cocolon / MashOS national architecture.
"""

from collections import defaultdict
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # expected package import
    from ..models import (
        FusionResult,
        PatternScore,
        RoleGap,
        SignalExtractionResult,
        TargetRoleScore,
        TargetSignature,
        UnknownNeed,
        WorldRoleEvidence,
    )
except Exception:  # local / standalone fallback
    try:
        from models_updated import (  # type: ignore
            FusionResult,
            PatternScore,
            RoleGap,
            SignalExtractionResult,
            TargetRoleScore,
            TargetSignature,
            UnknownNeed,
            WorldRoleEvidence,
        )
    except Exception:
        from models import (  # type: ignore
            FusionResult,
            PatternScore,
            RoleGap,
            SignalExtractionResult,
            TargetRoleScore,
            TargetSignature,
            UnknownNeed,
            WorldRoleEvidence,
        )

try:  # expected package import
    from .rules import (
        ACTION_DIRECTION_PHRASES,
        CLUSTER_RULES,
        RELIABILITY_WEIGHT,
        ROLE_GAP_MIN_SCORE,
        ROLE_LABELS_JA,
        ROLE_TEMPLATES,
        SOURCE_WEIGHT,
        THINKING_PURPOSE_PHRASES,
        WORLD_ROLE_MIN_SCORE,
        compute_recency_weight,
        detect_world_kind,
        normalize_text,
    )
except Exception:  # local / standalone fallback
    from rules import (  # type: ignore
        ACTION_DIRECTION_PHRASES,
        CLUSTER_RULES,
        RELIABILITY_WEIGHT,
        ROLE_GAP_MIN_SCORE,
        ROLE_LABELS_JA,
        ROLE_TEMPLATES,
        SOURCE_WEIGHT,
        THINKING_PURPOSE_PHRASES,
        WORLD_ROLE_MIN_SCORE,
        compute_recency_weight,
        detect_world_kind,
        normalize_text,
    )


SUPPORTED_STAGES = {"standard", "deep"}


# =============================================================================
# Generic helpers
# =============================================================================


def _ensure_stage(stage: str) -> str:
    norm = normalize_text(stage)
    if norm not in SUPPORTED_STAGES:
        raise ValueError(f"Unsupported stage: {stage!r}. Expected one of {sorted(SUPPORTED_STAGES)}")
    return norm


def _to_result(result: SignalExtractionResult | Mapping[str, Any]) -> SignalExtractionResult:
    if isinstance(result, SignalExtractionResult):
        return result
    if isinstance(result, Mapping):
        data = dict(result)
        return SignalExtractionResult(**data)  # type: ignore[arg-type]
    if is_dataclass(result):
        return SignalExtractionResult(**asdict(result))  # type: ignore[arg-type]
    raise TypeError(f"Unsupported signal result type: {type(result)!r}")


def _parse_iso_ts(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _max_ts(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if not a:
        return b
    if not b:
        return a
    da = _parse_iso_ts(a)
    db = _parse_iso_ts(b)
    if da is None:
        return b
    if db is None:
        return a
    return a if da >= db else b


def _sorted_pattern_scores(items: Iterable[PatternScore]) -> List[PatternScore]:
    xs = list(items)
    xs.sort(key=lambda x: (-x.score, x.key))
    return xs


def compute_evidence_weight(
    result: SignalExtractionResult,
    now_ts: str | None = None,
) -> float:
    source_weight = SOURCE_WEIGHT.get(result.source_type, 1.0)
    reliability_weight = RELIABILITY_WEIGHT.get(result.reliability, 0.5)
    recency_weight = compute_recency_weight(result.timestamp, now_ts=now_ts)
    return source_weight * reliability_weight * recency_weight


# =============================================================================
# Lane split
# =============================================================================


def split_lanes(results: Sequence[SignalExtractionResult]) -> Dict[str, List[SignalExtractionResult]]:
    lanes: Dict[str, List[SignalExtractionResult]] = {
        "reaction": [],
        "declarative": [],
        "relational": [],
    }

    for r in results:
        if r.source_type == "emotion_input":
            lanes["reaction"].append(r)
        elif r.source_type in ("mymodel_create", "deep_insight", "today_question"):
            lanes["declarative"].append(r)
        elif r.source_type in ("echo", "discovery"):
            lanes["relational"].append(r)

    return lanes


# =============================================================================
# Aggregation primitives
# =============================================================================


def aggregate_template_role_scores(
    results: Sequence[SignalExtractionResult],
    now_ts: str | None = None,
) -> List[PatternScore]:
    score_map: Dict[str, float] = {role: 0.0 for role in ROLE_TEMPLATES}

    for r in results:
        if not r.role_scores:
            continue
        w = compute_evidence_weight(r, now_ts=now_ts)
        for rs in r.role_scores:
            score_map[rs.role_key] += float(rs.score) * w

    items = [
        PatternScore(key=role, label_ja=ROLE_LABELS_JA[role], score=round(score, 4))
        for role, score in score_map.items()
        if score > 0
    ]
    return _sorted_pattern_scores(items)


def aggregate_target_role_scores(
    results: Sequence[SignalExtractionResult],
    now_ts: str | None = None,
) -> List[TargetRoleScore]:
    bucket: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for r in results:
        if not r.primary_target or not r.role_scores:
            continue

        target = r.primary_target
        w = compute_evidence_weight(r, now_ts=now_ts)

        for rs in r.role_scores:
            key = (target.key, rs.role_key)
            row = bucket.setdefault(
                key,
                {
                    "target_key": target.key,
                    "target_label_ja": target.label_ja,
                    "target_type": target.target_type,
                    "role_key": rs.role_key,
                    "role_label_ja": ROLE_LABELS_JA.get(rs.role_key, rs.role_key),
                    "score": 0.0,
                    "evidence_count": 0,
                    "last_seen": None,
                },
            )
            row["score"] += float(rs.score) * w
            row["evidence_count"] += 1
            row["last_seen"] = _max_ts(row["last_seen"], r.timestamp)

    items = [
        TargetRoleScore(
            target_key=v["target_key"],
            target_label_ja=v["target_label_ja"],
            target_type=v["target_type"],
            role_key=v["role_key"],
            role_label_ja=v["role_label_ja"],
            score=round(v["score"], 4),
            evidence_count=v["evidence_count"],
            last_seen=v["last_seen"],
        )
        for v in bucket.values()
        if v["score"] > 0
    ]
    items.sort(key=lambda x: (-x.score, x.target_key, x.role_key))
    return items


def aggregate_cluster_scores(
    results: Sequence[SignalExtractionResult],
    now_ts: str | None = None,
) -> List[PatternScore]:
    score_map: Dict[str, float] = {cluster: 0.0 for cluster in CLUSTER_RULES.keys()}

    for r in results:
        w = compute_evidence_weight(r, now_ts=now_ts)

        for cluster_key, rule in CLUSTER_RULES.items():
            score = 0.0
            for t in r.thinking_tags:
                score += float(rule.get("thinkings", {}).get(t.key, 0.0)) * float(t.score)
            for a in r.action_tags:
                score += float(rule.get("actions", {}).get(a.key, 0.0)) * float(a.score)
            if score > 0:
                score_map[cluster_key] += score * w

    items = [
        PatternScore(key=k, label_ja=k, score=round(v, 4))
        for k, v in score_map.items()
        if v > 0
    ]
    return _sorted_pattern_scores(items)


def aggregate_pattern_scores(
    results: Sequence[SignalExtractionResult],
    attr: str,
    now_ts: str | None = None,
) -> List[PatternScore]:
    bucket: Dict[str, Dict[str, Any]] = {}

    for r in results:
        tags = getattr(r, attr)
        if not tags:
            continue
        w = compute_evidence_weight(r, now_ts=now_ts)

        for t in tags:
            row = bucket.setdefault(
                t.key,
                {"label_ja": getattr(t, "label_ja", t.key), "score": 0.0},
            )
            row["score"] += float(t.score) * w

    items = [
        PatternScore(key=k, label_ja=v["label_ja"], score=round(v["score"], 4))
        for k, v in bucket.items()
        if v["score"] > 0
    ]
    return _sorted_pattern_scores(items)


# =============================================================================
# World-role inference (Deep-oriented)
# =============================================================================


def aggregate_world_roles(
    declarative_results: Sequence[SignalExtractionResult],
    now_ts: str | None = None,
) -> Tuple[List[WorldRoleEvidence], List[WorldRoleEvidence], List[WorldRoleEvidence]]:
    buckets: Dict[str, Dict[Tuple[Optional[str], str], Dict[str, Any]]] = {
        "self": {},
        "real": {},
        "desired": {},
    }

    for r in declarative_results:
        if not r.role_scores:
            continue

        w = compute_evidence_weight(r, now_ts=now_ts)
        text = normalize_text((r.raw_text_primary or "") + "\n" + (r.raw_text_secondary or ""))
        world_kind = detect_world_kind(text)
        if world_kind not in buckets:
            continue

        target_key = r.primary_target.key if r.primary_target else None
        bucket = buckets[world_kind]

        for rs in r.role_scores[:3]:
            key = (target_key, rs.role_key)
            row = bucket.setdefault(
                key,
                {
                    "world_kind": world_kind,
                    "role_key": rs.role_key,
                    "role_label_ja": ROLE_LABELS_JA.get(rs.role_key, rs.role_key),
                    "score": 0.0,
                    "target_key": target_key,
                    "reason": world_kind,
                },
            )
            row["score"] += float(rs.score) * w

    def _to_list(bucket: Dict[Tuple[Optional[str], str], Dict[str, Any]]) -> List[WorldRoleEvidence]:
        xs = [
            WorldRoleEvidence(
                world_kind=v["world_kind"],
                role_key=v["role_key"],
                role_label_ja=v["role_label_ja"],
                score=round(v["score"], 4),
                target_key=v["target_key"],
                reason=v["reason"],
            )
            for v in bucket.values()
            if v["score"] > 0
        ]
        xs.sort(key=lambda x: (-x.score, x.target_key or "", x.role_key))
        return xs

    return _to_list(buckets["self"]), _to_list(buckets["real"]), _to_list(buckets["desired"])


# =============================================================================
# Gap inference and unknowns
# =============================================================================


def _group_world_roles_by_target(
    items: Sequence[WorldRoleEvidence],
    min_score: float,
) -> Dict[Optional[str], List[WorldRoleEvidence]]:
    grouped: Dict[Optional[str], List[WorldRoleEvidence]] = defaultdict(list)
    for item in items:
        if item.score >= min_score:
            grouped[item.target_key].append(item)
    for values in grouped.values():
        values.sort(key=lambda x: (-x.score, x.role_key))
    return grouped


def infer_role_gaps(
    self_roles: Sequence[WorldRoleEvidence],
    real_roles: Sequence[WorldRoleEvidence],
    desired_roles: Sequence[WorldRoleEvidence],
) -> List[RoleGap]:
    gaps: List[RoleGap] = []

    self_by_target = _group_world_roles_by_target(self_roles, WORLD_ROLE_MIN_SCORE)
    real_by_target = _group_world_roles_by_target(real_roles, WORLD_ROLE_MIN_SCORE)
    desired_by_target = _group_world_roles_by_target(desired_roles, WORLD_ROLE_MIN_SCORE)

    # desired vs real
    for target_key, desired_list in desired_by_target.items():
        real_list = real_by_target.get(target_key)
        if not real_list:
            continue
        top_desired = desired_list[0]
        top_real = real_list[0]
        if top_desired.role_key == top_real.role_key:
            continue
        gap_score = abs(top_desired.score - top_real.score) + 1.0
        if gap_score >= ROLE_GAP_MIN_SCORE:
            gaps.append(
                RoleGap(
                    target_key=target_key,
                    left_kind="desired",
                    left_role=top_desired.role_key,
                    right_kind="real",
                    right_role=top_real.role_key,
                    gap_score=round(gap_score, 4),
                    note="望む役割と現実の役割に差がある可能性",
                )
            )

    # self vs real
    for target_key, self_list in self_by_target.items():
        real_list = real_by_target.get(target_key)
        if not real_list:
            continue
        top_self = self_list[0]
        top_real = real_list[0]
        if top_self.role_key == top_real.role_key:
            continue
        gap_score = abs(top_self.score - top_real.score) + 0.5
        if gap_score >= ROLE_GAP_MIN_SCORE:
            gaps.append(
                RoleGap(
                    target_key=target_key,
                    left_kind="self",
                    left_role=top_self.role_key,
                    right_kind="real",
                    right_role=top_real.role_key,
                    gap_score=round(gap_score, 4),
                    note="自己認識と現実の役割に差がある可能性",
                )
            )

    gaps.sort(key=lambda x: (-x.gap_score, x.target_key or "", x.left_kind, x.left_role))
    return gaps


def infer_unknowns(
    target_role_scores: Sequence[TargetRoleScore],
    self_world_roles: Sequence[WorldRoleEvidence],
    real_world_roles: Sequence[WorldRoleEvidence],
    desired_roles: Sequence[WorldRoleEvidence],
) -> List[UnknownNeed]:
    unknowns: List[UnknownNeed] = []

    strong_targets: Dict[str, float] = defaultdict(float)
    for tr in target_role_scores:
        strong_targets[tr.target_key] += float(tr.score)

    for target_key, total in strong_targets.items():
        if total < 4.0:
            continue

        has_real = any(x.target_key == target_key and x.score >= WORLD_ROLE_MIN_SCORE for x in real_world_roles)
        if not has_real:
            unknowns.append(
                UnknownNeed(
                    kind="real_world_role_missing",
                    priority=0.9,
                    target_key=target_key,
                    reason="実際の反応パターンは見えるが、現実でどんな役割を担っているかの証拠が薄い",
                    hint="その対象や場面で、周囲からどんな役割を求められることが多いか",
                )
            )

        has_desired = any(x.target_key == target_key and x.score >= WORLD_ROLE_MIN_SCORE for x in desired_roles)
        if not has_desired:
            unknowns.append(
                UnknownNeed(
                    kind="desired_role_missing",
                    priority=0.7,
                    target_key=target_key,
                    reason="実際の反応パターンは見えるが、どうありたいかの証拠が薄い",
                    hint="その対象や場面で、本当はどんな在り方をしたいか",
                )
            )

    unknowns.sort(key=lambda x: (-x.priority, x.target_key or "", x.kind))
    return unknowns


# =============================================================================
# Target signatures and history
# =============================================================================


def infer_activity_state(last_seen: Optional[str], now_ts: str | None = None) -> str:
    dt = _parse_iso_ts(last_seen)
    now = _parse_iso_ts(now_ts) if now_ts else datetime.now(timezone.utc)
    if dt is None or now is None:
        return "unknown"

    days = max((now - dt).days, 0)
    if days <= 30:
        return "active"
    if days <= 90:
        return "warm"
    return "dormant"


def build_role_history(
    target_role_scores: Sequence[TargetRoleScore],
    now_ts: str | None = None,
) -> List[Dict[str, Any]]:
    history = []
    for tr in target_role_scores:
        history.append(
            {
                "target_key": tr.target_key,
                "target_label_ja": tr.target_label_ja,
                "target_type": tr.target_type,
                "role_key": tr.role_key,
                "role_label_ja": tr.role_label_ja,
                "score": round(float(tr.score), 4),
                "evidence_count": int(tr.evidence_count),
                "last_seen": tr.last_seen,
                "state": infer_activity_state(tr.last_seen, now_ts=now_ts),
            }
        )
    history.sort(key=lambda x: (-x["score"], x["target_key"], x["role_key"]))
    return history


def aggregate_target_signatures(
    results: Sequence[SignalExtractionResult],
    target_role_scores: Sequence[TargetRoleScore],
    now_ts: str | None = None,
) -> List[TargetSignature]:
    role_map: Dict[str, List[TargetRoleScore]] = defaultdict(list)
    target_meta: Dict[str, Dict[str, str]] = {}

    for tr in target_role_scores:
        role_map[tr.target_key].append(tr)
        target_meta[tr.target_key] = {
            "label_ja": tr.target_label_ja,
            "target_type": tr.target_type,
        }

    thinking_map: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    action_map: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    cluster_map: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    evidence_count: Dict[str, int] = defaultdict(int)
    last_seen: Dict[str, Optional[str]] = defaultdict(lambda: None)

    for r in results:
        if not r.primary_target:
            continue
        target_key = r.primary_target.key
        if target_key not in role_map:
            continue

        w = compute_evidence_weight(r, now_ts=now_ts)
        evidence_count[target_key] += 1
        last_seen[target_key] = _max_ts(last_seen[target_key], r.timestamp)

        for t in r.thinking_tags:
            thinking_map[target_key][t.key] += float(t.score) * w
        for a in r.action_tags:
            action_map[target_key][a.key] += float(a.score) * w

        for cluster_key, rule in CLUSTER_RULES.items():
            cluster_score = 0.0
            for t in r.thinking_tags:
                cluster_score += float(rule.get("thinkings", {}).get(t.key, 0.0)) * float(t.score)
            for a in r.action_tags:
                cluster_score += float(rule.get("actions", {}).get(a.key, 0.0)) * float(a.score)
            if cluster_score > 0:
                cluster_map[target_key][cluster_key] += cluster_score * w

    signatures: List[TargetSignature] = []
    for target_key, role_items in role_map.items():
        role_items_sorted = sorted(role_items, key=lambda x: (-x.score, x.role_key))
        top_role = role_items_sorted[0]

        cluster_scores = cluster_map.get(target_key, {})
        top_cluster = None
        if cluster_scores:
            top_cluster = sorted(cluster_scores.items(), key=lambda x: (-x[1], x[0]))[0][0]

        top_thinking_keys = [
            key for key, _ in sorted(thinking_map.get(target_key, {}).items(), key=lambda x: (-x[1], x[0]))[:2]
        ]
        top_action_keys = [
            key for key, _ in sorted(action_map.get(target_key, {}).items(), key=lambda x: (-x[1], x[0]))[:2]
        ]

        meta = target_meta[target_key]
        signatures.append(
            TargetSignature(
                target_key=target_key,
                target_label_ja=meta["label_ja"],
                target_type=meta["target_type"],
                top_role_key=top_role.role_key,
                top_role_score=round(float(top_role.score), 4),
                top_cluster_key=top_cluster,
                top_thinking_keys=top_thinking_keys,
                top_action_keys=top_action_keys,
                evidence_count=evidence_count.get(target_key, int(top_role.evidence_count)),
                last_seen=last_seen.get(target_key) or top_role.last_seen,
            )
        )

    signatures.sort(key=lambda x: (-x.top_role_score, x.target_key))
    return signatures


# =============================================================================
# Views
# =============================================================================


def select_top_targets(target_role_scores: Sequence[TargetRoleScore], k: int = 3) -> List[Dict[str, Any]]:
    target_best: Dict[str, TargetRoleScore] = {}
    for tr in target_role_scores:
        prev = target_best.get(tr.target_key)
        if prev is None or tr.score > prev.score or (tr.score == prev.score and tr.role_key < prev.role_key):
            target_best[tr.target_key] = tr

    selected = sorted(target_best.values(), key=lambda x: (-x.score, x.target_key))[:k]
    return [
        {
            "target_key": x.target_key,
            "target_label_ja": x.target_label_ja,
            "target_type": x.target_type,
            "role_key": x.role_key,
            "role_label_ja": x.role_label_ja,
            "score": round(float(x.score), 4),
            "evidence_count": int(x.evidence_count),
            "last_seen": x.last_seen,
        }
        for x in selected
    ]


def build_standard_view(
    template_role_scores: Sequence[PatternScore],
    target_role_scores: Sequence[TargetRoleScore],
    thinking_patterns: Sequence[PatternScore],
    action_patterns: Sequence[PatternScore],
) -> Dict[str, Any]:
    return {
        "top_roles": [asdict(x) for x in list(template_role_scores)[:3]],
        "top_targets": select_top_targets(target_role_scores, k=3),
        "top_thinking_patterns": [asdict(x) for x in list(thinking_patterns)[:3]],
        "top_action_patterns": [asdict(x) for x in list(action_patterns)[:3]],
    }


def build_deep_view(
    cluster_scores: Sequence[PatternScore],
    target_role_scores: Sequence[TargetRoleScore],
    self_world_roles: Sequence[WorldRoleEvidence],
    real_world_roles: Sequence[WorldRoleEvidence],
    desired_roles: Sequence[WorldRoleEvidence],
    role_gaps: Sequence[RoleGap],
    unknowns: Sequence[UnknownNeed],
    target_signatures: Sequence[TargetSignature],
) -> Dict[str, Any]:
    return {
        "top_target_roles": [asdict(x) for x in list(target_role_scores)[:10]],
        "cluster_distribution": [asdict(x) for x in list(cluster_scores)[:5]],
        "self_world_roles": [asdict(x) for x in list(self_world_roles)[:5]],
        "real_world_roles": [asdict(x) for x in list(real_world_roles)[:5]],
        "desired_roles": [asdict(x) for x in list(desired_roles)[:5]],
        "role_gaps": [asdict(x) for x in list(role_gaps)[:5]],
        "unknowns": [asdict(x) for x in list(unknowns)[:5]],
        "target_signatures": [asdict(x) for x in list(target_signatures)[:10]],
    }


# =============================================================================
# Main orchestration
# =============================================================================


def fuse_signal_results(
    results: Sequence[SignalExtractionResult | Mapping[str, Any]],
    stage: str = "standard",
    now_ts: str | None = None,
) -> FusionResult:
    stage = _ensure_stage(stage)
    prepared = [_to_result(x) for x in results]
    lanes = split_lanes(prepared)

    template_role_scores = aggregate_template_role_scores(prepared, now_ts=now_ts)

    # Prefer actual reaction evidence for target-role mapping.
    target_source = lanes["reaction"] if lanes["reaction"] else prepared
    target_role_scores = aggregate_target_role_scores(target_source, now_ts=now_ts)

    cluster_scores = aggregate_cluster_scores(prepared, now_ts=now_ts)
    thinking_patterns = aggregate_pattern_scores(prepared, "thinking_tags", now_ts=now_ts)
    action_patterns = aggregate_pattern_scores(prepared, "action_tags", now_ts=now_ts)

    self_world_roles, real_world_roles, desired_roles = aggregate_world_roles(
        lanes["declarative"], now_ts=now_ts
    )

    role_gaps: List[RoleGap] = []
    unknowns: List[UnknownNeed] = []
    if stage == "deep":
        role_gaps = infer_role_gaps(
            self_roles=self_world_roles,
            real_roles=real_world_roles,
            desired_roles=desired_roles,
        )
        unknowns = infer_unknowns(
            target_role_scores=target_role_scores,
            self_world_roles=self_world_roles,
            real_world_roles=real_world_roles,
            desired_roles=desired_roles,
        )

    target_signatures = aggregate_target_signatures(
        prepared,
        target_role_scores=target_role_scores,
        now_ts=now_ts,
    )
    role_history = build_role_history(target_role_scores, now_ts=now_ts)

    standard_view = build_standard_view(
        template_role_scores=template_role_scores,
        target_role_scores=target_role_scores,
        thinking_patterns=thinking_patterns,
        action_patterns=action_patterns,
    )

    deep_view: Dict[str, Any] = {}
    if stage == "deep":
        deep_view = build_deep_view(
            cluster_scores=cluster_scores,
            target_role_scores=target_role_scores,
            self_world_roles=self_world_roles,
            real_world_roles=real_world_roles,
            desired_roles=desired_roles,
            role_gaps=role_gaps,
            unknowns=unknowns,
            target_signatures=target_signatures,
        )

    return FusionResult(
        stage=stage,
        template_role_scores=template_role_scores,
        cluster_scores=cluster_scores,
        target_role_scores=target_role_scores,
        thinking_patterns=thinking_patterns,
        action_patterns=action_patterns,
        self_world_roles=self_world_roles,
        real_world_roles=real_world_roles,
        desired_roles=desired_roles,
        role_gaps=role_gaps,
        target_signatures=target_signatures,
        role_history=role_history,
        unknowns=unknowns,
        standard_view=standard_view,
        deep_view=deep_view,
    )


__all__ = [
    "compute_evidence_weight",
    "split_lanes",
    "aggregate_template_role_scores",
    "aggregate_target_role_scores",
    "aggregate_cluster_scores",
    "aggregate_pattern_scores",
    "aggregate_world_roles",
    "infer_role_gaps",
    "infer_unknowns",
    "infer_activity_state",
    "build_role_history",
    "aggregate_target_signatures",
    "select_top_targets",
    "build_standard_view",
    "build_deep_view",
    "fuse_signal_results",
]
