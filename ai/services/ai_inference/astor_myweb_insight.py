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


# ---------- self insight（自己理解）フィルタ ----------

# 「自己理解」入力は MyWeb の“感情傾向”分析には使わない。
# （履歴には残り得るため、MyWeb で参照する集計ロジック側で除外する。）
SELF_INSIGHT_EMOTION_LABELS = {"SelfInsight", "自己理解"}


def _is_self_insight_emotion_label(label: Any) -> bool:
    """トリガーの emotion ラベルが「自己理解」由来かを判定する。"""
    try:
        s = str(label or "").strip()
    except Exception:
        return False
    return s in SELF_INSIGHT_EMOTION_LABELS


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

        # 「自己理解」入力は MyWeb の感情傾向分析には含めない
        if _is_self_insight_emotion_label(t.get("emotion")):
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
    """指定ユーザーの「感情（emotion label）」について、現在期間と直前期間の比較を返す。

    重要:
    - MyWeb は「感情傾向/推移」からの観測レポートに寄せる。
      （自己構造/思考構造の推定は MyProfile 側に寄せる）
    - そのため、ここでの key は structure_key ではなく「emotion label」を採用する。
      MyWeb の "structure_movements" セクションは互換のためIDを維持しつつ、
      実際の中身は「感情の動き」として表示されることを想定する。
    """

    struct_map = _load_user_structures(user_id)
    if not struct_map:
        return []

    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    cur_start = now - _dt.timedelta(days=period_days)
    cur_end = now
    prev_start = now - _dt.timedelta(days=period_days * 2)
    prev_end = cur_start

    # 重複（同一ログが複数構造語にヒット）をゆるく除いて "感情イベント列" を作る
    cur_events = _collect_deduped_events(struct_map, start=cur_start, end=cur_end)
    prev_events = _collect_deduped_events(struct_map, start=prev_start, end=prev_end)

    def _stats(events: List[Dict[str, Any]]) -> Dict[str, PeriodStructureStat]:
        buckets: Dict[str, Dict[str, Any]] = {}
        for e in events:
            emo = str(e.get("emotion") or "").strip()
            if not emo:
                continue
            # safety: 「自己理解」入力は MyWeb の感情傾向分析には含めない
            if _is_self_insight_emotion_label(emo):
                continue

            b = buckets.setdefault(emo, {"count": 0, "sum_int": 0.0, "cnt_int": 0})
            b["count"] += 1

            if e.get("intensity") is not None:
                try:
                    f = float(e["intensity"])
                except (TypeError, ValueError):
                    f = None
                if f is not None:
                    b["sum_int"] += f
                    b["cnt_int"] += 1

        out: Dict[str, PeriodStructureStat] = {}
        for emo, b in buckets.items():
            cnt = int(b["count"])
            avg_int = float(b["sum_int"] / b["cnt_int"]) if b["cnt_int"] else 0.0
            # avg_score は互換のために残している（ここでは avg_int と同値でよい）
            out[emo] = PeriodStructureStat(key=emo, count=cnt, avg_score=avg_int, avg_intensity=avg_int)
        return out

    cur_stats = _stats(cur_events)
    prev_stats = _stats(prev_events)

    all_keys = sorted(set(cur_stats.keys()) | set(prev_stats.keys()))
    trends: List[StructureTrend] = []

    for emo in all_keys:
        cur = cur_stats.get(emo) or PeriodStructureStat(key=emo, count=0, avg_score=0.0, avg_intensity=0.0)
        prev = prev_stats.get(emo) or PeriodStructureStat(key=emo, count=0, avg_score=0.0, avg_intensity=0.0)
        if cur.count <= 0 and prev.count <= 0:
            continue

        delta_count = int(cur.count - prev.count)
        delta_intensity = float(cur.avg_intensity - prev.avg_intensity)
        trend = _trend_label(period_days, prev.count, cur.count)

        trends.append(
            StructureTrend(
                key=emo,
                current=cur,
                previous=prev,
                delta_count=delta_count,
                delta_intensity=delta_intensity,
                trend=trend,
                term_en=None,
                definition=None,
                observation_viewpoint=None,
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

            # 「自己理解」入力は MyWeb の感情傾向分析には含めない
            if _is_self_insight_emotion_label(t.get("emotion")):
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

    # MyWeb は「感情構造」レポート：
    # 自己（価値観/思考特性/反応モデル）の断定ではなく、
    # 一定期間における感情の傾向・推移・揺らぎを観測できる形にまとめる。
    if period_days <= 8:
        kind = "weekly"
        label = "最近の一週間"
        headline = "最近の一週間の感情構造レポート"
    elif period_days <= 35:
        kind = "monthly"
        label = "最近のひと月"
        headline = "最近のひと月の感情構造レポート"
    else:
        kind = "custom"
        label = "最近の期間"
        headline = "最近の期間の感情構造レポート"

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
    """観測サマリー（段落）。

    MyWeb は「感情の傾向・推移」を扱う。
    そのため、ここでは "中心テーマ" を「中心に出やすかった感情」として言語化する。

    追加方針（商業性とのバランス）:
    - 構造精度（観測主義・非診断）は維持する。
    - ただしユーザーが「答え」を受け取った感覚を持てるよう、
      冒頭に “要点（答え）” を短く明示してから、根拠となる観測文へ繋げる。
    """

    # --------------------------
    # 要点（答え）: まず短く明示
    # --------------------------
    takeaways: List[str] = []

    # 中心（出やすい感情）
    if top_keys:
        labels = [(_emotion_label_ja(k) or str(k)) for k in top_keys[:3]]
        center = "「" + "」「".join(labels) + "」"
        takeaways.append(f"中心は{center}。")
    else:
        takeaways.append("中心となる感情はまだはっきりしません（分散気味）。")

    # 揺れ方（切り替え）
    sw = sway.get("switchiness")
    if sw == "fine":
        takeaways.append("切り替えは細かめ（揺れながら調整している状態）。")
    elif sw == "slow":
        takeaways.append("ひとつの感情が続きやすい（同じ感情が長めに滞在）。")
    else:
        takeaways.append("揺れはあるが、移り変わりはほどよい。")

    # 戻り方（ネガ→ポジ / 落ち着きへ戻る動き）
    rtc = sway.get("return_to_center")
    poss = [_emotion_label_ja(x) for x in (sway.get("positives") or [])]
    pos_phrase = "・".join([p for p in poss if p]) if poss else "落ち着き"

    if rtc in ("repeating", "often"):
        takeaways.append(f"揺れたあとに{pos_phrase}へ戻る動きが複数回。")
    elif rtc == "some":
        takeaways.append(f"{pos_phrase}へ戻る動きは一部で確認。")
    else:
        takeaways.append("揺れが残りやすく、戻りは少なめ。")

    # 観測密度（ログが少ない場合は控えめに）
    density = sway.get("density")
    if density == "low":
        takeaways.append("ログが少なめなので輪郭は控えめに解釈。")

    answer_block = "【要点（答え）】\n" + "\n".join([f"・{t}" for t in takeaways])

    # --------------------------
    # 以降: 観測文（根拠・意味づけ）
    # --------------------------

    # 中心（出やすい感情）: 段落
    if top_keys:
        labels = [(_emotion_label_ja(k) or str(k)) for k in top_keys[:3]]
        center = "「" + "」「".join(labels) + "」"
        head = f"{kind_label}は、{center}が中心に観測されました。"
    else:
        head = f"{kind_label}は、いくつかの感情が薄く観測されています。"

    # 揺らぎの説明
    if sw == "fine":
        sway_line = "感情の切り替えが比較的細かく、揺れながら調整している動きが見えます。"
    elif sw == "slow":
        sway_line = "ひとつの感情の流れが続きやすく、同じ感情が長めに滞在する動きが見えます。"
    else:
        sway_line = "揺れはあるものの、ほどよい間隔で移り変わっている印象です。"

    # 戻り（ネガ→ポジ/落ち着きへ戻る動き）
    if rtc in ("repeating", "often"):
        rtc_line = "揺れたあとに落ち着きへ戻ろうとする動きが、繰り返し見えています。"
        meaning = "刺激を受けたあとに、感情が自然に整っていく流れが起きている可能性があります。"
    elif rtc == "some":
        rtc_line = "揺れたあとに落ち着きへ戻る動きが、一部で見えています。"
        meaning = "乱れそのものよりも、『戻り方』に感情の整え方のパターンが出やすいかもしれません。"
    else:
        rtc_line = "揺れがそのまま残りやすく、今は整える前の段階にいる可能性があります。"
        meaning = "焦って結論を出すより、『何で揺れたか（きっかけ）』を静かに観測していくのが安全です。"

    # 観測密度の補足
    if density == "low":
        tail = "観測ログが少なめなので、今回は輪郭を柔らかく捉えています。"
    else:
        tail = ""

    return "\n\n".join([t for t in [answer_block, head, sway_line, rtc_line, meaning, tail] if t]).strip()




def _build_pattern_bullets(
    *,
    sway: Dict[str, Any],
    top_keys: List[str],
) -> List[Dict[str, Any]]:
    """パターン検出（bullets）。

    MyWeb では「自己の断定」ではなく、
    感情の揺らぎ・切り替え・戻り方など“状態の動き”を中心に提示する。
    """

    items: List[Dict[str, Any]] = []

    # 揺れ/切替
    sw = sway.get("switchiness")
    if sw == "fine":
        items.append(
            {
                "text": "短いスパンで切り替えが起きやすく、揺れながらも感情が調整されている印象です。",
                "tags": ["sway", "alternation"],
            }
        )
    elif sw == "slow":
        items.append(
            {
                "text": "同じ流れが続きやすく、ひとつの感情が長めに滞在しやすい動きがあります。",
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

    # ネガ→ポジの戻り（落ち着きへ戻る）
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

    # 中心（出やすい感情）
    if top_keys:
        center_labels = [(_emotion_label_ja(k) or str(k)) for k in top_keys[:3]]
        center = "・".join(center_labels)
        items.append(
            {
                "text": f"この期間は「{center}」が、比較的出やすい中心の感情でした。",
                "tags": ["emotions", "center"],
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
        items = [{"text": "今回は大きな断定はせず、観測された流れだけを短くまとめています。", "tags": []}]

    return items




def _build_structure_items(trends_sorted: List[StructureTrend], period_days: int) -> List[Dict[str, Any]]:
    """互換セクション: "structure_movements" だが、内容は「感情の動き」を入れる。

    UI/スキーマ互換のためセクションIDは維持しつつ、
    中身を「感情構造（傾向・推移）」として表示する。
    """

    items: List[Dict[str, Any]] = []

    for tr in trends_sorted[:5]:
        movement = _movement_from_trend(tr)
        rel = _relative_desc(tr, period_days)

        label = _emotion_label_ja(tr.key) or tr.key

        item: Dict[str, Any] = {
            "structure_key": tr.key,  # ここでは emotion label を入れる
            "label": label,
            "relative_desc": rel,
            "movement": movement,
        }

        items.append(item)

    if not items:
        items.append(
            {
                "structure_key": "observing",
                "label": "観測準備中",
                "relative_desc": "もう少し記録が積み重なると、感情の動きが見えてきます。",
                "movement": "stable",
            }
        )

    return items




def _build_reflection_text(*, top_keys: List[str]) -> str:
    """MyWeb の「感情観測ヒント」用テキストを作る。

    目的:
    - 構造精度（観測主義・非診断）は守りつつ、
      ユーザーが「次に何をすれば答えに近づくか」を掴みやすくする。
    - MyProfile（自己構造）へ踏み込みすぎず、"感情のきっかけ" の観測に留める。
    """

    hints = {
        "Anxiety": "不安が出た直前の『未確定だった点／不確実だった点』を1つメモ",
        "Anger": "怒りが出た直前の『止まったこと／納得できなかった点』を1つメモ",
        "Sadness": "悲しみが出た直前の『終わったと感じたこと／できなかったこと』を1つメモ",
        "Joy": "喜びが出た直前の『うまくいったこと／満たされたこと』を1つメモ",
        "Calm": "落ち着きが出た直前の『安心材料（環境・人・状況）』を1つメモ",
    }

    lines: List[str] = []
    lines.append("今週の“答え”を見つけるための観測メモ：")
    lines.append("・強く出た感情があった日は、『直前の出来事・環境・体調』を一言メモ")
    lines.append("・感情を良し悪しで判断せず、『いつ・どんな場面で・どれくらい出たか』を観測")

    if top_keys:
        lines.append("")
        lines.append("中心になりやすかった感情（ヒント）:")
        for k in top_keys[:2]:
            label = _emotion_label_ja(k) or str(k)
            hint = hints.get(str(k), "その感情が出た直前の出来事を一言メモ")
            lines.append(f"・{label}: {hint}")

    return "\n".join(lines).strip()


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
            f"{period_label}は、まだ安定して観測できる感情の傾向が十分ではありません。\n\n"
            "記録が少ないときは、無理に結論を出さず、まず『何で揺れたか（きっかけ）』だけを静かに見ていくのが安全です。"
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
                    "title": "感情観測サマリー",
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
                    "title": "感情の動き",
                    "type": "structures",
                    "tone": "neutral",
                    "items": [
                        {
                            "structure_key": "observing",
                            "label": "観測準備中",
                            "relative_desc": "もう少し記録が積み重なると、感情の動きが見えてきます。",
                            "movement": "stable",
                        }
                    ],
                },
                {
                    "id": "self_reflection_hint",
                    "title": "感情観測ヒント",
                    "type": "callout",
                    "tone": "reflective",
                    "style": "reflection",
                    "text": "強く出た感情があった日は、\n『直前の出来事・環境・体調』を一言メモしておくと、次のレポートで“出やすい条件”が見えやすくなります。\n\n感情を良し悪しで判断せず、\n『いつ・どんな場面で・どれくらい出たか』を観測してみてください。",
                },
                {
                    "id": "notes",
                    "title": "注記",
                    "type": "callout",
                    "tone": "meta",
                    "style": "note",
                    "text": f"これは診断ではなく、『{ENGINE_DISPLAY_NAME}が記録から観測した感情の傾向』のメモです。数値ではなく相対表現でまとめています。",
                },
            ],
        }
        return report

    # 通常ケース
    trends_sorted = sorted(trends, key=lambda t: (t.current.count, t.current.avg_intensity), reverse=True)
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
    reflection_text = _build_reflection_text(top_keys=top_keys)

    # notes
    notes_lines = [
        f"これは診断ではなく、『{ENGINE_DISPLAY_NAME}が記録から観測した感情の傾向』のメモです。",
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
                "title": "感情観測サマリー",
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
                "title": "感情の動き",
                "type": "structures",
                "tone": "neutral",
                "items": structure_items,
            },
            {
                "id": "self_reflection_hint",
                "title": "感情観測ヒント",
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
