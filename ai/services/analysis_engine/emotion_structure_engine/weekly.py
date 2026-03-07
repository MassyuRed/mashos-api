from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, Iterable
import math, statistics, collections
from datetime import datetime, timezone, timedelta
from ..models import EmotionEntry, WeeklySnapshot, Narrative, LABELS, BaselineProfile

# Geometry for 2D center (regular pentagon)
DEG = math.pi / 180.0
POS_DEG = {
    "peace": 90,
    "joy": 18,
    "anger": 306,
    "sadness": 234,
    "anxiety": 162,
}
POS = {k: (math.cos(v*DEG), math.sin(v*DEG)) for k, v in POS_DEG.items()}

MOTIF_DICT = {
    ("sadness","peace","joy"): "sadness-peace-joy",
    ("anxiety","peace","joy"): "anxiety-peace-joy",
    ("anger","sadness","peace"): "anger-sadness-peace",
    ("anxiety","peace","peace"): "anxiety-peace-peace",
    ("sadness","sadness","peace"): "sadness-sadness-peace",
    ("joy","peace","joy"): "joy-peace-joy",
    ("peace","joy","peace"): "peace-joy-peace",
    ("peace","anxiety","peace"): "peace-anxiety-peace",
}

STOPWORDS = set(["する","ある","こと","それ","これ","あれ","今日","昨日","です","ます","でした","すること"])

# NOTE:
# time bucket labels are intentionally aligned with the MyWeb API layer.
# The analysis core keeps "peace" internally, but time bucket payloads expose
# "calm" so the downstream API / RN can render Standard without extra mapping.
TIME_BUCKET_ORDER = ("0-6", "6-12", "12-18", "18-24")
TIME_BUCKET_LABELS = ("joy", "sadness", "anxiety", "anger", "calm")

JST = timezone(timedelta(hours=9))


def _attach_time_bucket_aliases(snapshot: WeeklySnapshot, time_buckets: List[Dict[str, Any]]) -> WeeklySnapshot:
    """Keep weekly snapshot serialization compatible even if models.py is not updated yet.

    - Always expose both `time_buckets` and `timeBuckets` in `to_dict()`
    - Attach the attribute on the instance when possible
    """
    try:
        setattr(snapshot, "time_buckets", time_buckets)
    except Exception:
        pass

    def _to_dict_with_aliases() -> Dict[str, Any]:
        base = {}
        try:
            from dataclasses import asdict
            base = asdict(snapshot)
        except Exception:
            try:
                base = dict(vars(snapshot))
            except Exception:
                base = {}
        base["time_buckets"] = time_buckets
        base["timeBuckets"] = time_buckets
        return base

    try:
        setattr(snapshot, "to_dict", _to_dict_with_aliases)
    except Exception:
        pass
    return snapshot


def _make_weekly_snapshot(*, time_buckets: List[Dict[str, Any]], **kwargs: Any) -> WeeklySnapshot:
    """Construct WeeklySnapshot with backward compatibility for older models.py."""
    try:
        snapshot = WeeklySnapshot(time_buckets=time_buckets, **kwargs)
    except TypeError:
        snapshot = WeeklySnapshot(**kwargs)
    return _attach_time_bucket_aliases(snapshot, time_buckets)


def _safe_div(a: float, b: float) -> float:
    if b == 0:
        return 0.0
    return a / b


def _normalize_share(wcounts: Dict[str, int]) -> Dict[str, float]:
    total = sum(wcounts.values())
    if total <= 0:
        return {l: 0.0 for l in LABELS}
    return {l: wcounts.get(l, 0) / total for l in LABELS}


def _entropy(share: Dict[str, float]) -> float:
    H = 0.0
    for p in share.values():
        if p > 0:
            H -= p * math.log(p)
    return _safe_div(H, math.log(len(share))) if len(share) > 0 else 0.0


def _gini_simpson(share: Dict[str, float]) -> float:
    return 1.0 - sum(p * p for p in share.values())


def _center2d(share: Dict[str, float]) -> Dict[str, float]:
    x = sum(share[l] * POS[l][0] for l in LABELS)
    y = sum(share[l] * POS[l][1] for l in LABELS)
    return {"x": x, "y": y}


def _keywords_from_memo(entries: List[EmotionEntry], top_k: int = 5) -> List[str]:
    # simple fallback tokenizer: split by spaces and punctuation
    # For Japanese, this is a naive approach; acceptable as "任意" keywords
    import re

    bag = collections.Counter()
    for e in entries:
        if not e.memo:
            continue
        tokens = re.split(r"[\s、。．,.!！?？;；:\-\(\)\[\]「」『』\n\t]+", e.memo)
        for t in tokens:
            t = t.strip()
            if not t or t in STOPWORDS or len(t) < 2:
                continue
            bag[t] += 1
    return [w for w, _ in bag.most_common(top_k)]


def _parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    s = str(iso_str or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST)
    except Exception:
        return None


def _time_bucket_key_from_hour(hour: int) -> str:
    if 0 <= hour < 6:
        return "0-6"
    if 6 <= hour < 12:
        return "6-12"
    if 12 <= hour < 18:
        return "12-18"
    return "18-24"


def _bucket_output_label(label: str) -> Optional[str]:
    s = str(label or "").strip()
    if not s:
        return None
    if s == "peace":
        return "calm"
    if s in TIME_BUCKET_LABELS:
        return s
    return None


def _blank_time_bucket_row(bucket: str) -> Dict[str, Any]:
    return {
        "bucket": bucket,
        "label": bucket,
        "inputCount": 0,
        "weightedTotal": 0,
        "counts": {k: 0 for k in TIME_BUCKET_LABELS},
        "weightedCounts": {k: 0 for k in TIME_BUCKET_LABELS},
        "sharePct": {k: 0 for k in TIME_BUCKET_LABELS},
        "dominantKey": None,
        "_input_ids": set(),
    }


def _finalize_time_bucket_rows(rows_by_bucket: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for bucket in TIME_BUCKET_ORDER:
        row = rows_by_bucket.get(bucket) or _blank_time_bucket_row(bucket)
        weighted_total = int(sum(int(row["weightedCounts"].get(k, 0) or 0) for k in TIME_BUCKET_LABELS))
        row["weightedTotal"] = weighted_total
        if weighted_total > 0:
            row["sharePct"] = {
                k: int(round((int(row["weightedCounts"].get(k, 0) or 0) / weighted_total) * 100))
                for k in TIME_BUCKET_LABELS
            }
            dominant = max(TIME_BUCKET_LABELS, key=lambda key: int(row["weightedCounts"].get(key, 0) or 0))
            row["dominantKey"] = dominant if int(row["weightedCounts"].get(dominant, 0) or 0) > 0 else None
        else:
            row["sharePct"] = {k: 0 for k in TIME_BUCKET_LABELS}
            row["dominantKey"] = None
        row.pop("_input_ids", None)
        out.append(row)
    return out


def _coerce_bucket_value(raw: Any, *, emotion_key: str) -> int:
    if not isinstance(raw, dict):
        return 0
    if emotion_key == "calm":
        return int(raw.get("calm", 0) or 0) + int(raw.get("peace", 0) or 0)
    return int(raw.get(emotion_key, 0) or 0)


def build_time_bucket_rows(entries: List[EmotionEntry]) -> List[Dict[str, Any]]:
    rows_by_bucket = {bucket: _blank_time_bucket_row(bucket) for bucket in TIME_BUCKET_ORDER}
    for e in entries or []:
        dt = _parse_iso_datetime(getattr(e, "timestamp", ""))
        if dt is None:
            continue
        bucket = _time_bucket_key_from_hour(dt.hour)
        row = rows_by_bucket[bucket]
        input_id = str(getattr(e, "id", "") or "")
        if ":" in input_id:
            input_id = input_id.split(":", 1)[0]
        if input_id and input_id not in row["_input_ids"]:
            row["_input_ids"].add(input_id)
            row["inputCount"] += 1

        out_label = _bucket_output_label(getattr(e, "label", ""))
        if not out_label:
            continue
        row["counts"][out_label] += 1
        intensity = max(1, int(getattr(e, "intensity", 1) or 1))
        row["weightedCounts"][out_label] += intensity
    return _finalize_time_bucket_rows(rows_by_bucket)


def aggregate_time_bucket_rows(bucket_groups: Iterable[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    rows_by_bucket = {bucket: _blank_time_bucket_row(bucket) for bucket in TIME_BUCKET_ORDER}
    for group in bucket_groups or []:
        if not isinstance(group, list):
            continue
        for item in group:
            if not isinstance(item, dict):
                continue
            bucket = str(item.get("bucket") or item.get("label") or "").strip()
            if bucket not in TIME_BUCKET_ORDER:
                continue
            row = rows_by_bucket[bucket]
            row["inputCount"] += int(item.get("inputCount", 0) or 0)
            counts = item.get("counts") if isinstance(item.get("counts"), dict) else {}
            weighted_counts = item.get("weightedCounts") if isinstance(item.get("weightedCounts"), dict) else {}
            for key in TIME_BUCKET_LABELS:
                row["counts"][key] += _coerce_bucket_value(counts, emotion_key=key)
                row["weightedCounts"][key] += _coerce_bucket_value(weighted_counts, emotion_key=key)
    return _finalize_time_bucket_rows(rows_by_bucket)


def build_weekly_features(entries: List[EmotionEntry], period: str) -> WeeklySnapshot:
    # Pre: entries sorted by timestamp asc
    counts = {l: 0 for l in LABELS}
    wcounts = {l: 0 for l in LABELS}
    daily_buckets: Dict[str, Dict[str, int]] = {}
    intensities: List[int] = []
    motifs = []
    motif_counts: Dict[str, int] = {}
    N = len(entries)
    time_buckets = build_time_bucket_rows(entries)
    if N == 0:
        return _make_weekly_snapshot(
            period=period,
            n_events=0,
            counts=counts,
            wcounts=wcounts,
            share=_normalize_share(wcounts),
            daily_share=[],
            alternation_rate=None,
            run_stats={"median": 0, "max": 0, "min": 0},
            intensity={"std": 0.0, "min": 0, "max": 0},
            motifs=[],
            motif_counts={},
            entropy=None,
            gini_simpson=None,
            center2d={"x": 0.0, "y": 0.0},
            keywords=[],
            notes=["no_data"],
            time_buckets=time_buckets,
        )

    # aggregate
    for e in entries:
        counts[e.label] += 1
        wcounts[e.label] += e.intensity
        intensities.append(e.intensity)
        if e.date not in daily_buckets:
            daily_buckets[e.date] = {l: 0 for l in LABELS}
        daily_buckets[e.date][e.label] += e.intensity

    # alternation & run lengths
    changes = 0
    runs = []
    run_len = 1
    for i in range(1, N):
        prev, cur = entries[i - 1], entries[i]
        if (cur.label != prev.label) or (cur.intensity != prev.intensity):
            changes += 1
            runs.append(run_len)
            run_len = 1
        else:
            run_len += 1
    runs.append(run_len)
    alternation_rate = changes / (N - 1) if N > 1 else 0.0
    run_stats = {
        "median": float(statistics.median(runs)) if runs else 0.0,
        "max": max(runs) if runs else 0,
        "min": min(runs) if runs else 0,
    }

    # intensity stats
    intensity_std = float(statistics.pstdev(intensities)) if len(intensities) > 1 else 0.0
    intensity_min = min(intensities) if intensities else 0
    intensity_max = max(intensities) if intensities else 0

    # motifs sliding window length=3
    for t in range(0, N - 2):
        tri = (entries[t].label, entries[t + 1].label, entries[t + 2].label)
        name = MOTIF_DICT.get(tri)
        if name:
            motifs.append({
                "name": name,
                "start_id": entries[t].id,
                "end_id": entries[t + 2].id,
            })
            motif_counts[name] = motif_counts.get(name, 0) + 1

    share = _normalize_share(wcounts)
    entropy = _entropy(share)
    gini = _gini_simpson(share)
    center = _center2d(share)
    daily_share = []
    for d, wc in sorted(daily_buckets.items()):
        total = sum(wc.values())
        ds = {l: (wc[l] / total if total > 0 else 0.0) for l in LABELS}
        daily_share.append({"date": d, "share": ds})

    keywords = _keywords_from_memo(entries, top_k=5)

    return _make_weekly_snapshot(
        period=period,
        n_events=N,
        counts=counts,
        wcounts=wcounts,
        share=share,
        daily_share=daily_share,
        alternation_rate=alternation_rate,
        run_stats=run_stats,
        intensity={"std": intensity_std, "min": intensity_min, "max": intensity_max},
        motifs=motifs,
        motif_counts=motif_counts,
        entropy=entropy,
        gini_simpson=gini,
        center2d=center,
        keywords=keywords,
        notes=[],
        time_buckets=time_buckets,
    )

# --------------- Narrator (weekly) ---------------

def _axis_explicit_text_for_alternation(z: Optional[float]) -> Tuple[str, str]:
    if z is None:
        return ("insufficient", "比較には十分な観測データがありませんでした。")
    if z > 1.0:
        return ("ok", "これまでの傾向と比べて、感情の切り替わりがやや多めでした。")
    if z < -1.0:
        return ("ok", "これまでの傾向と比べて、感情の切り替わりは落ち着いていました。")
    return ("ok", "最近の週と比べて、切り替わりに大きな差は見られませんでした。")


def _axis_explicit_text_for_intensity(z: Optional[float]) -> Tuple[str, str]:
    if z is None:
        return ("insufficient", "比較には十分な観測データがありませんでした。")
    if z > 1.0:
        return ("ok", "最近の週と比べて、感情の強弱の振れ幅がやや大きめでした。")
    if z < -1.0:
        return ("ok", "最近の週と比べて、感情の強弱の振れ幅は小さめでした。")
    return ("ok", "最近の週と比べて、感情の強弱に大きな変化は見られませんでした。")


def _axis_explicit_text_for_diversity(z_entropy: Optional[float], z_gini: Optional[float]) -> Tuple[str, str]:
    # Prefer entropy; fall back to gini
    z = z_entropy if z_entropy is not None else z_gini
    if z is None:
        return ("insufficient", "比較には十分な観測データがありませんでした。")
    if z > 1.0:
        return ("ok", "過去と比べて、感情の種類にやや偏りが見られます。")
    if z < -1.0:
        return ("ok", "過去と比べて、感情の分布はまとまりやすく見えます。")
    return ("ok", "過去と比べて、分布の偏りに大きな変化は見られませんでした。")


def _motif_text(snapshot: WeeklySnapshot) -> Tuple[str, str]:
    # Choose one representative motif to mention, prioritizing sadness->peace->joy
    if not snapshot.motif_counts:
        return ("ok", "この週に特徴的な補正ループの観測はありませんでした。")
    preferred_order = ["sadness-peace-joy", "anxiety-peace-joy", "joy-peace-joy", "peace-joy-peace"]
    name = None
    for p in preferred_order:
        if p in snapshot.motif_counts:
            name = p
            break
    if name is None:
        name = max(snapshot.motif_counts.items(), key=lambda kv: kv[1])[0]
    count = snapshot.motif_counts[name]
    readable = name.replace("-", "→")
    if readable == "sadness→peace→joy":
        term = "補正ループ（悲しみ→平穏→喜び）"
    elif readable == "anxiety→peace→joy":
        term = "補正ループ（不安→平穏→喜び）"
    elif readable == "joy→peace→joy":
        term = "往復の短いリズム（喜び→平穏→喜び）"
    elif readable == "peace→joy→peace":
        term = "往復の短いリズム（平穏→喜び→平穏）"
    else:
        term = f"モチーフ（{readable}）"
    return ("ok", f"{term}が{count}回観測されました。これまでと同様の構造が見られます。")


def _top2_labels_text(share: Dict[str, float]) -> str:
    ordered = sorted(share.items(), key=lambda kv: kv[1], reverse=True)
    top = [k for k, v in ordered if v > 0][:2]
    name_map = {"joy": "喜び", "sadness": "悲しみ", "anxiety": "不安", "anger": "怒り", "peace": "平穏"}
    if len(top) >= 2:
        return f"{name_map[top[0]]}/{name_map[top[1]]} が中心に観測された。"
    if len(top) == 1:
        return f"{name_map[top[0]]} が中心に観測された。"
    return "観測はごく少数だった。"


def _z_value(current: Optional[float], mu: Optional[float], sigma: Optional[float]) -> Optional[float]:
    if current is None or mu is None or sigma is None:
        return None
    if sigma <= 1e-8:
        if abs(mu) <= 1e-8:
            return None
        # use signed pct change scaled to a pseudo-z by threshold 20% ≈ 1.0
        return (current - mu) / (abs(mu) * 0.20)
    return (current - mu) / sigma


def narrate_weekly(snapshot: WeeklySnapshot, baseline: Optional[BaselineProfile]) -> Narrative:
    # structural comment (常体)
    headline = _top2_labels_text(snapshot.share)
    struct_lines = [f"この週は {headline}"]
    z_alt = z_int = z_ent = z_gini = None
    if baseline and baseline.metrics:
        alt_m = baseline.metrics.get("alternation")
        int_m = baseline.metrics.get("intensity_std")
        ent_m = baseline.metrics.get("entropy")
        gin_m = baseline.metrics.get("gini_simpson")
        z_alt = _z_value(snapshot.alternation_rate, alt_m.get("mu") if alt_m else None, alt_m.get("sigma") if alt_m else None) if alt_m else None
        z_int = _z_value(snapshot.intensity.get("std"), int_m.get("mu") if int_m else None, int_m.get("sigma") if int_m else None) if int_m else None
        z_ent = _z_value(snapshot.entropy, ent_m.get("mu") if ent_m else None, ent_m.get("sigma") if ent_m else None) if ent_m else None
        z_gini = _z_value(snapshot.gini_simpson, gin_m.get("mu") if gin_m else None, gin_m.get("sigma") if gin_m else None) if gin_m else None

    items = []
    st, txt = _axis_explicit_text_for_alternation(z_alt)
    items.append({"key": "alternation", "status": st, "text": txt})
    st, txt = _axis_explicit_text_for_intensity(z_int)
    items.append({"key": "intensity_std", "status": st, "text": txt})
    st, txt = _axis_explicit_text_for_diversity(z_ent, z_gini)
    items.append({"key": "diversity", "status": st, "text": txt})
    st, txt = _motif_text(snapshot)
    items.append({"key": "motif", "status": st, "text": txt})

    note = None
    if any(i["status"] == "insufficient" for i in items):
        note = "一部項目は観測数が少なく、比較表現は参考程度となります。"

    tail = None
    if all(i["status"] == "insufficient" for i in items) or snapshot.n_events < 1:
        tail = "今回は比較に必要な観測が揃っていませんでしたが、今後も記録を続けることでより安定した分析が可能になります。"

    structural_comment = " ".join(struct_lines)
    gentle_comment = "1週間、おつかれさまでした。小さな観測が積み上がっています。"

    evidence = {
        "mode": "axis-explicit-text-only",
        "items": items,
    }
    if note:
        evidence["note"] = note
    internal = {
        "alternation": {"current": snapshot.alternation_rate},
        "intensity_std": {"current": snapshot.intensity.get("std")},
        "entropy": {"current": snapshot.entropy},
        "gini_simpson": {"current": snapshot.gini_simpson},
    }
    if baseline and baseline.metrics:
        def _maybe(k: str) -> Dict[str, Any]:
            m = baseline.metrics.get(k)
            if not m:
                return {}
            return {"mu": m.get("mu"), "sigma": m.get("sigma")}

        internal["alternation"].update(_maybe("alternation"))
        internal["intensity_std"].update(_maybe("intensity_std"))
        internal["entropy"].update(_maybe("entropy"))
        internal["gini_simpson"].update(_maybe("gini_simpson"))
        internal["alternation"]["z"] = z_alt
        internal["intensity_std"]["z"] = z_int
        internal["entropy"]["z"] = z_ent
        internal["gini_simpson"]["z"] = z_gini
    evidence["internal"] = internal

    narrative = Narrative(
        type="weekly",
        period=snapshot.period,
        structural_comment=structural_comment,
        gentle_comment=gentle_comment,
        next_points=["来週も同じ観測リズムを続けると、傾向がクリアになります。"],
        evidence=evidence,
    )
    if tail:
        narrative.evidence["tail"] = tail
    return narrative
