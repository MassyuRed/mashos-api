"""astor_myweb_insight.py

ASTOR MyWeb Insight v0.3

役割:
- ASTOR が蓄積した構造パターン (astor_structure_patterns.json) をもとに、
  特定ユーザーの「最近の構造傾向」を **構造化されたレポート** として返す。
- MyWeb 週報 / 月報などから呼び出すことを想定した純粋関数群。

背景:
- v0.1 ではテキストのみを返していたが、MyWeb UI 側で安定して表示するために
  "出力するための構文（＝レポートスキーマ）" を追加する。

前提:
- astor_patterns.StructurePatternsStore が JSON を管理している。
- 出力は myweb_report_schema.json（myweb.report.v1）に準拠する。

注意:
- 本モジュールは、統計量そのものの提示（z-score 等）を目的としない。
  内部では相対判定のために数値を扱うが、ユーザー向け出力は「やや」「少し」などの
  比喩語・相対語に変換する（観測主義・非診断）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import datetime as _dt
import json
import os

try:
    # Cocolon 環境でのパス解決前提
    from astor_patterns import StructurePatternsStore
except ImportError:  # 単体テストなどでは直接 JSON を読むフォールバックにできる
    StructurePatternsStore = None  # type: ignore


# ユーザーに見せるエンジン名（リネーム時にここだけ替えられるようにする）
ENGINE_DISPLAY_NAME = os.getenv("COCOLON_ENGINE_DISPLAY_NAME", "ASTOR")

# MyWeb レポート（構文）バージョン
REPORT_VERSION = "myweb.report.v1"


# ---------- 内部データ構造（集計用） ----------


@dataclass
class PeriodStructureStat:
    key: str
    count: int
    avg_score: float
    avg_intensity: float


@dataclass
class StructureTrend:
    """1つの構造語について、現在期間と直前期間の比較をまとめたもの。"""

    key: str
    current: PeriodStructureStat
    previous: PeriodStructureStat
    delta_count: int
    delta_intensity: float
    trend: str  # "new" | "up" | "down" | "stable"

    # 構造辞書があれば補助情報を差し込む（意味づけに使う：UIの詳細にも流用可能）
    term_en: Optional[str] = None
    definition: Optional[str] = None
    observation_viewpoint: Optional[str] = None


# ---------- 基本ユーティリティ ----------


def _load_user_structures(user_id: str) -> Dict[str, Any]:
    """ユーザーごとの構造状態（structure_key -> entry）を取得する。"""

    if StructurePatternsStore is not None:
        # 実行環境によってはパス解決で例外が起きる可能性があるため、
        # ここで握って JSON 直読みフォールバックへ落とす。
        try:
            store = StructurePatternsStore()
            user_entry = store.get_user_patterns(user_id)
            return user_entry.get("structures", {})
        except Exception:
            pass

    # フォールバック: 直接 JSON を読む
    here = Path(__file__).resolve()
    parents = list(here.parents)
    base = parents[3] if len(parents) > 3 else here.parent
    path = base / "ai" / "data" / "state" / "astor_structure_patterns.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    users = raw.get("users") or {}
    entry = users.get(user_id) or {}
    return entry.get("structures", {})


def _parse_ts(ts_str: Any) -> Optional[_dt.datetime]:
    if not isinstance(ts_str, str):
        return None
    try:
        return _dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _filter_by_range(
    struct_entry: Dict[str, Any],
    *,
    start: _dt.datetime,
    end: _dt.datetime,
) -> PeriodStructureStat:
    """単一構造語について、指定期間 [start, end) に絞った統計値を計算する。"""

    key = str(struct_entry.get("structure_key") or "")
    triggers = struct_entry.get("triggers") or []

    cnt = 0
    sum_score = 0.0
    sum_intensity = 0.0

    for t in triggers:
        ts = _parse_ts(t.get("ts"))
        if ts is None:
            continue
        if ts < start or ts >= end:
            continue

        try:
            score = float(t.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        try:
            intensity = float(t.get("intensity") or 0.0) if t.get("intensity") is not None else 0.0
        except (TypeError, ValueError):
            intensity = 0.0

        cnt += 1
        sum_score += score
        sum_intensity += intensity

    if cnt == 0:
        return PeriodStructureStat(key=key, count=0, avg_score=0.0, avg_intensity=0.0)

    return PeriodStructureStat(key=key, count=cnt, avg_score=sum_score / cnt, avg_intensity=sum_intensity / cnt)


def _trend_label(period_days: int, prev_count: int, cur_count: int) -> str:
    """雑に "new/up/down/stable" を決める（内部用）。"""

    if prev_count <= 0 and cur_count > 0:
        return "new"
    delta = cur_count - prev_count
    threshold = 1 if period_days <= 10 else 2
    if delta >= threshold:
        return "up"
    if delta <= -threshold:
        return "down"
    return "stable"


def _lookup_structure_dict(key: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """構造辞書があれば (term_en, definition, observation_viewpoint) を返す。"""

    try:
        from structure_dict import load_structure_dict

        entries = load_structure_dict()
        entry = entries.get(key)
        if not isinstance(entry, dict):
            return (None, None, None)
        term_en = (entry.get("term_en") or "").strip() or None
        sections = entry.get("sections") or {}
        if not isinstance(sections, dict):
            sections = {}
        definition = (sections.get("定義") or "").strip() or None
        observation = (sections.get("観測視点") or "").strip() or None

        # 画面用に長すぎるのは切る（詳細画面でフルを出したくなったら調整）
        if definition and len(definition) > 180:
            definition = definition[:180] + "…"
        if observation and len(observation) > 260:
            observation = observation[:260] + "…"
        return (term_en, definition, observation)
    except Exception:
        return (None, None, None)


def _emotion_label_ja(label: Optional[str]) -> Optional[str]:
    if not label:
        return None
    m = {
        "Joy": "喜び",
        "Sadness": "悲しみ",
        "Anxiety": "不安",
        "Anger": "怒り",
        "Calm": "落ち着き",
    }
    return m.get(label, label)


# ---------- 集計（構造トレンド） ----------


def analyze_myweb_structures(user_id: str, period_days: int = 30) -> List[StructureTrend]:
    """指定ユーザーの構造語について、現在期間と直前期間の比較を返す。"""

    struct_map = _load_user_structures(user_id)
    if not struct_map:
        return []

    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    cur_start = now - _dt.timedelta(days=period_days)
    cur_end = now
    prev_start = now - _dt.timedelta(days=period_days * 2)
    prev_end = cur_start

    trends: List[StructureTrend] = []

    for struct_entry in struct_map.values():
        cur = _filter_by_range(struct_entry, start=cur_start, end=cur_end)
        prev = _filter_by_range(struct_entry, start=prev_start, end=prev_end)
        if cur.count <= 0 and prev.count <= 0:
            continue

        delta_count = int(cur.count - prev.count)
        delta_intensity = float(cur.avg_intensity - prev.avg_intensity)
        trend = _trend_label(period_days, prev.count, cur.count)

        term_en, definition, observation = _lookup_structure_dict(cur.key or prev.key)

        trends.append(
            StructureTrend(
                key=cur.key or prev.key,
                current=cur,
                previous=prev,
                delta_count=delta_count,
                delta_intensity=delta_intensity,
                trend=trend,
                term_en=term_en,
                definition=definition,
                observation_viewpoint=observation,
            )
        )

    return trends


# ---------- 集計（感情の揺らぎ/切り替え：ERST視点の材料） ----------


def _collect_deduped_events(
    struct_map: Dict[str, Any],
    *,
    start: _dt.datetime,
    end: _dt.datetime,
) -> List[Dict[str, Any]]:
    """構造トリガーから、重複をゆるく除いたイベント列を作る。

    注意:
    - 1つの感情ログが複数の構造語にヒットすると、トリガーが重複する。
      ここでは (ts, emotion, intensity, memo_excerpt, is_secret) で重複排除して、
      "だいたいの流れ" を見る。
    """

    seen: set = set()
    events: List[Dict[str, Any]] = []

    for struct_entry in struct_map.values():
        triggers = struct_entry.get("triggers") or []
        for t in triggers:
            ts = _parse_ts(t.get("ts"))
            if ts is None:
                continue
            if ts < start or ts >= end:
                continue

            emotion = t.get("emotion")
            intensity = t.get("intensity")
            memo_excerpt = str(t.get("memo_excerpt") or "")
            is_secret = bool(t.get("is_secret", False))

            # ここでの key は "同一ログの近似"。
            key = (
                ts.isoformat(),
                str(emotion or ""),
                str(intensity if intensity is not None else ""),
                memo_excerpt,
                "1" if is_secret else "0",
            )
            if key in seen:
                continue
            seen.add(key)

            try:
                f_int = float(intensity) if intensity is not None else None
            except (TypeError, ValueError):
                f_int = None

            events.append(
                {
                    "ts": ts,
                    "emotion": str(emotion) if emotion is not None else None,
                    "intensity": f_int,
                }
            )

    events.sort(key=lambda e: e["ts"])
    return events


def _analyze_sway(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """イベント列から、"揺らぎ/切り替え" の粗い特徴を抽出する（内部用）。"""

    n = len(events)
    if n <= 0:
        return {
            "density": "none",
            "switchiness": "unknown",
            "return_to_center": "unknown",
            "negatives": [],
            "positives": [],
            "avg_intensity": None,
        }

    emotions: List[str] = [e.get("emotion") or "" for e in events]
    intensities: List[float] = [float(e["intensity"]) for e in events if e.get("intensity") is not None]

    # 切り替え頻度
    transitions = 0
    for i in range(1, n):
        if emotions[i] and emotions[i - 1] and emotions[i] != emotions[i - 1]:
            transitions += 1
    transition_rate = transitions / max(n - 1, 1)

    if transition_rate >= 0.70:
        switchiness = "fine"  # 細かい
    elif transition_rate <= 0.30:
        switchiness = "slow"  # 続きやすい
    else:
        switchiness = "moderate"

    # ネガ→ポジ（中心へ戻る）っぽい遷移
    NEG = {"Sadness", "Anxiety", "Anger"}
    POS = {"Calm", "Joy"}

    neg_seen = sorted({e for e in emotions if e in NEG})
    pos_seen = sorted({e for e in emotions if e in POS})

    return_hits = 0
    for i in range(n - 1):
        if emotions[i] in NEG and emotions[i + 1] in POS:
            return_hits += 1

    if return_hits >= 4:
        return_to_center = "repeating"
    elif return_hits >= 2:
        return_to_center = "often"
    elif return_hits >= 1:
        return_to_center = "some"
    else:
        return_to_center = "rare"

    # 観測密度（ざっくり）
    if n < 3:
        density = "low"
    elif n < 10:
        density = "mid"
    else:
        density = "high"

    avg_intensity = sum(intensities) / len(intensities) if intensities else None

    return {
        "density": density,
        "switchiness": switchiness,
        "return_to_center": return_to_center,
        "negatives": neg_seen,
        "positives": pos_seen,
        "avg_intensity": avg_intensity,
    }


# ---------- 出力（myweb.report.v1） ----------


def _period_meta(period_days: int) -> Dict[str, Any]:
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    start = (now - _dt.timedelta(days=period_days)).date().isoformat()
    end = now.date().isoformat()

    if period_days <= 8:
        kind = "weekly"
        label = "最近の一週間"
        headline = "最近の一週間の構造観測"
    elif period_days <= 35:
        kind = "monthly"
        label = "最近のひと月"
        headline = "最近のひと月の構造観測"
    else:
        kind = "custom"
        label = "最近の期間"
        headline = "最近の期間の構造観測"

    return {
        "kind": kind,
        "label": label,
        "start_date": start,
        "end_date": end,
        "days": int(max(1, min(period_days, 366))),
        "_headline": headline,  # 内部用（後で取り出して headline に使う）
    }


def _movement_from_trend(tr: StructureTrend) -> str:
    if tr.trend == "new":
        return "emerging"
    if tr.trend == "up" and tr.delta_count > 0:
        return "increasing"
    if tr.trend == "down" and tr.delta_count < 0:
        return "decreasing"
    # intensity の変化が大きいときは揺れ扱い
    if abs(tr.delta_intensity) >= 0.6:
        return "oscillating"
    return "stable"


def _relative_desc(tr: StructureTrend, period_days: int) -> str:
    """数値を出さずに、相対説明へ変換する。"""

    prev = tr.previous.count
    cur = tr.current.count
    delta = tr.delta_count

    # period によってニュアンスの閾値を少し変える
    threshold = 1 if period_days <= 10 else 2

    # 方向性
    if prev <= 0 and cur > 0:
        base = "最近になって、少し顔を出し始めています。"
    elif cur <= 0 and prev > 0:
        base = "この期間は、前より落ち着いて見えます。"
    elif delta >= threshold:
        base = "直前の流れより、やや前に出やすくなっています。"
    elif delta <= -threshold:
        base = "直前の流れより、少し落ち着き気味です。"
    else:
        base = "大きくは変わらず、安定した出方に見えます。"

    # 強さ（強度）
    ai = tr.current.avg_intensity
    if ai >= 2.5:
        strength = "出るときは輪郭がはっきりめになりやすいです。"
    elif ai >= 1.8:
        strength = "出るときはほどよい強さで現れています。"
    else:
        strength = "出方は比較的やわらかい印象です。"

    # 強さの変化
    if tr.delta_intensity >= 0.6:
        change = "最近は、出るときの強さが少し増しているかもしれません。"
    elif tr.delta_intensity <= -0.6:
        change = "最近は、出るときの強さが少し和らいでいるかもしれません。"
    else:
        change = ""

    parts = [base, strength]
    if change:
        parts.append(change)

    return " ".join([p for p in parts if p]).strip()


def _build_observation_summary(
    *,
    top_keys: List[str],
    sway: Dict[str, Any],
    kind_label: str,
) -> str:
    """観測サマリー（段落）。"""

    # 中心テーマ
    if top_keys:
        center = "「" + "」「".join(top_keys[:3]) + "」"
        head = f"{kind_label}は、{center}が中心に観測されました。"
    else:
        head = f"{kind_label}は、いくつかの構造が薄く観測されています。"

    # 揺らぎの説明
    sw = sway.get("switchiness")
    if sw == "fine":
        sway_line = "感情の切り替えが比較的細かく、揺れながら調整している印象があります。"
    elif sw == "slow":
        sway_line = "ひとつの流れが続きやすく、同じテーマを抱え続けるような動きが見えます。"
    else:
        sway_line = "揺れはあるものの、ほどよい間隔で移り変わっている印象です。"

    # 戻り（自己調整）
    rtc = sway.get("return_to_center")
    if rtc in ("repeating", "often"):
        rtc_line = "揺れたあとに落ち着きへ戻ろうとする流れが、繰り返し見えています。"
        meaning = "これは、外から受けた刺激を自分の中で受け止め直すプロセスが働いている可能性があります。"
    elif rtc == "some":
        rtc_line = "揺れたあとに落ち着きへ戻る動きが、一部で見えています。"
        meaning = "乱れそのものよりも、『戻り方』にあなたの調整力が出ているかもしれません。"
    else:
        rtc_line = "揺れがそのまま残りやすく、今は整える前の段階にいる可能性があります。"
        meaning = "焦って結論を出すより、『何が反応しているか』を静かに見ていく時期かもしれません。"

    # 観測密度
    density = sway.get("density")
    if density == "low":
        tail = "観測ログが少なめなので、今回は輪郭を柔らかく捉えています。"
    else:
        tail = ""

    return "\n\n".join([t for t in [head, sway_line, rtc_line, meaning, tail] if t]).strip()


def _build_pattern_bullets(
    *,
    sway: Dict[str, Any],
    top_keys: List[str],
) -> List[Dict[str, Any]]:
    """パターン検出（bullets）。"""

    items: List[Dict[str, Any]] = []

    # 揺れ/切替
    sw = sway.get("switchiness")
    if sw == "fine":
        items.append(
            {
                "text": "短いスパンで切り替えが起きやすく、揺れながらも自分を整え直している印象です。",
                "tags": ["sway", "alternation"],
            }
        )
    elif sw == "slow":
        items.append(
            {
                "text": "同じ流れが続きやすく、ひとつのテーマを抱えながら進んでいる印象です。",
                "tags": ["sway", "continuity"],
            }
        )
    else:
        items.append(
            {
                "text": "揺れはあるものの、急な反転というより、ゆるやかな移り変わりとして見えています。",
                "tags": ["sway"],
            }
        )

    # ネガ→ポジの戻り
    rtc = sway.get("return_to_center")
    negs = [_emotion_label_ja(x) for x in (sway.get("negatives") or [])]
    poss = [_emotion_label_ja(x) for x in (sway.get("positives") or [])]
    neg_phrase = "や".join([n for n in negs if n]) if negs else "揺れ"
    pos_phrase = "や".join([p for p in poss if p]) if poss else "落ち着き"

    if rtc in ("repeating", "often"):
        items.append(
            {
                "text": f"{neg_phrase}が出たあとに、時間をかけて{pos_phrase}へ戻ろうとする流れが繰り返し見えています。",
                "tags": ["regulation", "return"],
            }
        )
    elif rtc == "some":
        items.append(
            {
                "text": f"{neg_phrase}のあとに{pos_phrase}へ戻る動きが一部で見えています。",
                "tags": ["regulation"],
            }
        )

    # 中心テーマ
    if top_keys:
        center = "・".join(top_keys[:3])
        items.append(
            {
                "text": f"この期間の中心テーマは「{center}」まわりに集まりやすいようです。",
                "tags": ["themes"],
            }
        )

    # 観測密度
    if sway.get("density") == "low":
        items.append(
            {
                "text": "観測ログが少なめなので、周期性や揺らぎの判定は控えめにしています。",
                "tags": ["low_data"],
            }
        )

    # 最低1件は保証
    if not items:
        items = [{"text": "今回は大きなパターンの断定はせず、観測された流れだけを短くまとめています。", "tags": []}]

    return items


def _build_structure_items(trends_sorted: List[StructureTrend], period_days: int) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for tr in trends_sorted[:5]:
        movement = _movement_from_trend(tr)
        rel = _relative_desc(tr, period_days)

        ctx_parts: List[str] = []
        if tr.observation_viewpoint:
            ctx_parts.append(tr.observation_viewpoint)
        elif tr.definition:
            ctx_parts.append(tr.definition)
        if tr.term_en:
            ctx_parts.append(f"英語ラベル: {tr.term_en}")

        item: Dict[str, Any] = {
            "structure_key": tr.key,
            "label": tr.key,
            "relative_desc": rel,
            "movement": movement,
        }
        if ctx_parts:
            # context は長文化しやすいので、ここでは短く結合する
            item["context"] = " / ".join(ctx_parts)[:240]

        items.append(item)

    if not items:
        items.append(
            {
                "structure_key": "observing",
                "label": "観測準備中",
                "relative_desc": "もう少し記録が積み重なると、構造の動きが見えてきます。",
                "movement": "stable",
            }
        )

    return items


def generate_myweb_insight_report(user_id: str, period_days: int = 30, lang: str = "ja") -> Dict[str, Any]:
    """MyWeb 用の "構文（=レポートスキーマ）"（myweb.report.v1）を生成して返す。"""

    language = "ja" if lang == "ja" else "ja"
    now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # period meta
    p = _period_meta(period_days)
    headline = p.pop("_headline")

    struct_map = _load_user_structures(user_id)
    trends = analyze_myweb_structures(user_id=user_id, period_days=period_days)

    # trends が空でも schema を満たすため、最低5セクションを必ず出す
    if not struct_map or not trends:
        period_label = p.get("label") or "最近の期間"
        observation = (
            f"{period_label}は、まだ安定して観測できる構造の傾向が十分ではありません。\n\n"
            "記録が少ないときは、無理に結論を出さず、まず『いま何が反応しているか』だけを静かに見ていくのが安全です。"
        )

        report: Dict[str, Any] = {
            "version": REPORT_VERSION,
            "engine_display_name": ENGINE_DISPLAY_NAME,
            "language": language,
            "generated_at": now_iso,
            "frameworks": ["ERST", "ERST-B", "ThreeAxis", "SwayPatterns", "ObservationNotDiagnosis"],
            "period": {k: v for k, v in p.items() if k in ("kind", "label", "start_date", "end_date", "days")},
            "headline": headline,
            "sections": [
                {
                    "id": "observation_summary",
                    "title": "構造観測サマリー",
                    "type": "text",
                    "tone": "gentle",
                    "text": observation,
                },
                {
                    "id": "pattern_detection",
                    "title": "パターン検出",
                    "type": "bullets",
                    "tone": "neutral",
                    "items": [
                        {
                            "text": "観測ログが少なめなので、周期性や揺らぎの判定は控えめにしています。",
                            "tags": ["low_data"],
                        }
                    ],
                },
                {
                    "id": "structure_movements",
                    "title": "構造の動き",
                    "type": "structures",
                    "tone": "neutral",
                    "items": [
                        {
                            "structure_key": "observing",
                            "label": "観測準備中",
                            "relative_desc": "もう少し記録が積み重なると、構造の動きが見えてきます。",
                            "movement": "stable",
                        }
                    ],
                },
                {
                    "id": "self_reflection_hint",
                    "title": "自己観照ヒント",
                    "type": "callout",
                    "tone": "reflective",
                    "style": "reflection",
                    "text": "どんな感情が出たかよりも、『そのあと自分がどう動いたか』に目を向けてみてください。\n揺れたあとの選択に、いまのあなたらしさが出ています。",
                },
                {
                    "id": "notes",
                    "title": "注記",
                    "type": "callout",
                    "tone": "meta",
                    "style": "note",
                    "text": f"これは診断ではなく、『{ENGINE_DISPLAY_NAME}が記録から観測した傾向』のメモです。数値ではなく相対表現でまとめています。",
                },
            ],
        }
        return report

    # 通常ケース
    trends_sorted = sorted(trends, key=lambda t: (t.current.count, t.current.avg_score), reverse=True)
    top_keys = [t.key for t in trends_sorted[:3] if t.key]

    # sway analysis
    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    cur_start = now - _dt.timedelta(days=period_days)
    cur_end = now
    events = _collect_deduped_events(struct_map, start=cur_start, end=cur_end)
    sway = _analyze_sway(events)

    observation_summary = _build_observation_summary(
        top_keys=top_keys,
        sway=sway,
        kind_label=str(p.get("label") or "最近の期間"),
    )

    pattern_items = _build_pattern_bullets(sway=sway, top_keys=top_keys)

    structure_items = _build_structure_items(trends_sorted=trends_sorted, period_days=period_days)

    # self-reflection hint（基本固定。将来、top 構造に応じた個別ヒントも可能）
    reflection_text = (
        "どんな感情が出たかよりも、\n"
        "『そのあと自分がどう動いたか』に目を向けてみてください。\n\n"
        "揺れたあとの選択にこそ、\n"
        "いまのあなたらしさが出ています。"
    )

    # notes
    notes_lines = [
        f"これは診断ではなく、『{ENGINE_DISPLAY_NAME}が記録から観測した傾向』のメモです。",
        "数値ではなく相対表現でまとめています。",
    ]
    if sway.get("density") == "low":
        notes_lines.append("観測ログが少なめのため、断定は控えめにしています。")

    report = {
        "version": REPORT_VERSION,
        "engine_display_name": ENGINE_DISPLAY_NAME,
        "language": language,
        "generated_at": now_iso,
        "frameworks": ["ERST", "ERST-B", "ThreeAxis", "SwayPatterns", "ObservationNotDiagnosis"],
        "period": {k: v for k, v in p.items() if k in ("kind", "label", "start_date", "end_date", "days")},
        "headline": headline,
        "sections": [
            {
                "id": "observation_summary",
                "title": "構造観測サマリー",
                "type": "text",
                "tone": "gentle",
                "text": observation_summary,
            },
            {
                "id": "pattern_detection",
                "title": "パターン検出",
                "type": "bullets",
                "tone": "neutral",
                "items": pattern_items,
            },
            {
                "id": "structure_movements",
                "title": "構造の動き",
                "type": "structures",
                "tone": "neutral",
                "items": structure_items,
            },
            {
                "id": "self_reflection_hint",
                "title": "自己観照ヒント",
                "type": "callout",
                "tone": "reflective",
                "style": "reflection",
                "text": reflection_text,
            },
            {
                "id": "notes",
                "title": "注記",
                "type": "callout",
                "tone": "meta",
                "style": "note",
                "text": "\n".join(notes_lines),
            },
        ],
    }

    # myweb_report_schema.json は additionalProperties=false なので、
    # 余計なキーを足さないこと（ここで固定）。
    return report


def render_myweb_insight_text(report: Dict[str, Any]) -> str:
    """myweb.report.v1 を、人間が読むテキスト（Markdown寄り）に整形する。"""

    headline = str(report.get("headline") or "")
    period = report.get("period") or {}
    period_label = str(period.get("label") or "最近の期間")
    engine_name = str(report.get("engine_display_name") or ENGINE_DISPLAY_NAME)

    lines: List[str] = []
    if headline:
        lines.append(headline)
        lines.append("")

    for sec in report.get("sections") or []:
        title = sec.get("title")
        stype = sec.get("type")
        if title:
            lines.append(f"【{title}】")

        if stype == "text":
            txt = (sec.get("text") or "").strip()
            if txt:
                lines.append(txt)

        elif stype == "bullets":
            for it in sec.get("items") or []:
                t = (it.get("text") or "").strip()
                if t:
                    lines.append(f"- {t}")

        elif stype == "structures":
            for it in sec.get("items") or []:
                label = (it.get("label") or it.get("structure_key") or "").strip()
                rel = (it.get("relative_desc") or "").strip()
                ctx = (it.get("context") or "").strip()
                if label and rel:
                    if ctx:
                        lines.append(f"- {label}: {rel}（{ctx}）")
                    else:
                        lines.append(f"- {label}: {rel}")

        elif stype == "callout":
            txt = (sec.get("text") or "").strip()
            if txt:
                lines.append(txt)

        lines.append("")

    lines.append(f"（{engine_name} / {period_label}）")
    return "\n".join([l for l in lines if l is not None]).strip() + "\n"


def generate_myweb_insight_payload(
    user_id: str,
    period_days: int = 30,
    lang: str = "ja",
) -> Tuple[str, Dict[str, Any]]:
    """(text, report) を同時に返すユーティリティ。"""

    report = generate_myweb_insight_report(user_id=user_id, period_days=period_days, lang=lang)
    text = render_myweb_insight_text(report)
    return text, report


def generate_myweb_insight_text(user_id: str, period_days: int = 30, lang: str = "ja") -> str:
    """互換: 既存の呼び出しは text だけ欲しいので、内部で report を作り文字列化する。"""

    text, _report = generate_myweb_insight_payload(user_id=user_id, period_days=period_days, lang=lang)
    return text
