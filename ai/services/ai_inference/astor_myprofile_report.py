# -*- coding: utf-8 -*-
"""astor_myprofile_report.py

ASTOR MyProfile（月次）自己構造分析レポート生成
-------------------------------------------------

狙い
  - MyProfile の月次レポートを「読める構文」で安定生成する。
  - 現段階では LLM を必須にせず、ASTOR が保持している
    構造パターン（astor_structure_patterns.json）と
    Deep Insight の回答（astor_deep_insight_answers.json）から、
    観測ベースの文章を組み立てる。

注意
  - これは診断ではなく、観測に基づく仮説生成。
  - 外部（target=external）では secret を除外する。
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


# 既存ストア（JSONローカル）
try:
    from astor_patterns import StructurePatternsStore
except Exception:  # pragma: no cover
    StructurePatternsStore = None  # type: ignore

try:
    from astor_deep_insight_store import DeepInsightAnswerStore
except Exception:  # pragma: no cover
    DeepInsightAnswerStore = None  # type: ignore


# 構造辞書（ある場合のみ）
try:
    from structure_dict import load_structure_dict
except Exception:  # pragma: no cover
    load_structure_dict = None  # type: ignore


EMO_JA = {
    "Joy": "喜び",
    "Sadness": "悲しみ",
    "Anxiety": "不安",
    "Anger": "怒り",
    "Calm": "落ち着き",
    "SelfInsight": "自己理解",
    "自己理解": "自己理解",
}


def emo_label_ja(x: Optional[str]) -> str:
    s = str(x or "").strip()
    return EMO_JA.get(s, s or "感情")


def parse_period_days(period: Optional[str]) -> int:
    """"7d","30d","12w","3m" をざっくり日数へ。"""
    if not period:
        return 30
    s = str(period).strip().lower()
    if not s:
        return 30
    try:
        if s.endswith("d"):
            return max(1, int(s[:-1] or "30"))
        if s.endswith("w"):
            return max(1, int(s[:-1] or "1") * 7)
        if s.endswith("m"):
            return max(1, int(s[:-1] or "1") * 30)
        return max(1, int(s))
    except Exception:
        return 30


def is_myprofile_monthly_report_instruction(text: str) -> bool:
    """/mymodel/infer の instruction が「月次自己構造レポ生成」かを判定。"""
    t = str(text or "")
    # なるべく事故らない、広めの判定
    keys = [
        "自己構造分析レポート",
        "自己構造レポート",
        "MyProfile",
        "月次",
        "【自己構造分析レポート",
    ]
    hit = sum(1 for k in keys if k in t)
    return hit >= 2


def _parse_ts(ts: Any) -> Optional[_dt.datetime]:
    if not ts:
        return None
    try:
        return _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None


@dataclass
class StructurePeriodView:
    key: str
    count: int
    avg_intensity: float
    avg_score: float
    top_emotions: List[str]
    sample_memos: List[str]


def _intensity_label(avg_intensity: float) -> str:
    if avg_intensity >= 2.6:
        return "強め"
    if avg_intensity >= 1.9:
        return "中くらい"
    if avg_intensity >= 1.2:
        return "やわらかめ"
    return "かなりやわらかめ"


def _load_structures_map(user_id: str) -> Dict[str, Any]:
    if StructurePatternsStore is None:
        return {}
    try:
        store = StructurePatternsStore()
        user_entry = store.get_user_patterns(user_id)
        return user_entry.get("structures", {}) or {}
    except Exception:
        return {}


def _load_deep_insight_answers(user_id: str, *, include_secret: bool, limit: int = 6) -> List[Dict[str, Any]]:
    if DeepInsightAnswerStore is None:
        return []
    try:
        store = DeepInsightAnswerStore()
        return store.get_user_answers(user_id, limit=limit, include_secret=include_secret)
    except Exception:
        return []


def _collect_period_views(
    structures_map: Dict[str, Any],
    *,
    start: _dt.datetime,
    end: _dt.datetime,
    include_secret: bool,
) -> List[StructurePeriodView]:
    out: List[StructurePeriodView] = []

    for entry in (structures_map or {}).values():
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("structure_key") or "").strip()
        if not key:
            continue
        triggers = entry.get("triggers") or []
        if not isinstance(triggers, list) or not triggers:
            continue

        cnt = 0
        score_sum = 0.0
        inten_sum = 0.0
        inten_n = 0
        emo_counter: Dict[str, int] = {}
        memos: List[str] = []

        for t in triggers:
            if not isinstance(t, dict):
                continue
            if (not include_secret) and bool(t.get("is_secret", False)):
                continue
            ts = _parse_ts(t.get("ts"))
            if ts is None:
                continue
            if ts < start or ts >= end:
                continue

            cnt += 1

            try:
                score_sum += float(t.get("score") or 0.0)
            except Exception:
                pass

            inten = t.get("intensity")
            if inten is not None:
                try:
                    inten_sum += float(inten)
                    inten_n += 1
                except Exception:
                    pass

            emo = str(t.get("emotion") or "").strip()
            if emo:
                emo_counter[emo] = emo_counter.get(emo, 0) + 1

            me = str(t.get("memo_excerpt") or "").strip()
            if me:
                # 同じ行の重複を減らす
                if me not in memos:
                    memos.append(me)

        if cnt <= 0:
            continue

        avg_score = (score_sum / cnt) if cnt else 0.0
        avg_intensity = (inten_sum / inten_n) if inten_n > 0 else 0.0

        top_emotions = [k for k, _ in sorted(emo_counter.items(), key=lambda kv: kv[1], reverse=True)[:2]]

        out.append(
            StructurePeriodView(
                key=key,
                count=cnt,
                avg_intensity=avg_intensity,
                avg_score=avg_score,
                top_emotions=top_emotions,
                sample_memos=memos[:2],
            )
        )

    out.sort(key=lambda v: (v.count, v.avg_intensity, v.avg_score), reverse=True)
    return out


def _short_structure_gloss(struct_key: str) -> str:
    """構造辞書があれば、短い説明（1行）を返す。"""
    if not load_structure_dict:
        return ""
    try:
        d = load_structure_dict() or {}
        entry = d.get(struct_key)
        if not isinstance(entry, dict):
            return ""
        # まずは「定義」を短く
        secs = entry.get("sections") or {}
        defin = str(secs.get("定義") or "").strip()
        if defin:
            # 先頭1文っぽく切る（長すぎないように）
            defin = re.split(r"[。\n]", defin)[0].strip()
            if defin:
                return defin[:64]
    except Exception:
        return ""
    return ""


def _guess_domain_hints(struct_keys: List[str]) -> Dict[str, List[str]]:
    """領域別メモ用の雑な割り当て（断定しない前提の“ヒント”）。"""
    buckets = {
        "仕事": [],
        "対人": [],
        "孤独": [],
        "挑戦": [],
        "評価": [],
    }

    for k in struct_keys:
        if any(w in k for w in ["評価", "承認", "比較"]):
            buckets["評価"].append(k)
        if any(w in k for w in ["罪悪感", "承認", "羞恥", "対人"]):
            buckets["対人"].append(k)
        if any(w in k for w in ["孤独", "寂", "疎外"]):
            buckets["孤独"].append(k)
        if any(w in k for w in ["挑戦", "達成", "無力", "停滞"]):
            buckets["挑戦"].append(k)
        # 仕事は万能すぎるので、挑戦/評価寄りを補助
        if any(w in k for w in ["達成", "評価", "無力", "焦り"]):
            buckets["仕事"].append(k)

    # 重複は除く
    for kk in list(buckets.keys()):
        seen = set()
        uniq = []
        for x in buckets[kk]:
            if x in seen:
                continue
            uniq.append(x)
            seen.add(x)
        buckets[kk] = uniq[:2]
    return buckets


def _extract_quoted_terms(text: str, limit: int = 8) -> List[str]:
    """『...』で囲まれた語を抽出（MyProfileレポ内の構造キー想定）。"""
    if not text:
        return []
    terms: List[str] = []
    for m in re.finditer(r"『([^』]{1,48})』", str(text)):
        t = str(m.group(1) or "").strip()
        if not t:
            continue
        if t in terms:
            continue
        terms.append(t)
        if len(terms) >= limit:
            break
    return terms


def _extract_prev_report_summary(prev_text: str) -> Dict[str, Any]:
    """前回レポ本文から、差分要約に使える“要点”を抜き出す（ルールベース）。

    - 【要点（答え）】ブロックの行（核/崩れ/安定）を優先
    - 見つからない場合は、本文全体から『...』語を拾う
    """
    out: Dict[str, Any] = {
        "core_line": "",
        "shaky_line": "",
        "steady_line": "",
        "keys": [],
    }
    if not prev_text:
        return out

    lines0 = [str(x).strip() for x in str(prev_text).splitlines()]
    lines = [l for l in lines0 if l is not None]

    # 【要点（答え）】セクションの抽出
    try:
        sidx = next(i for i, l in enumerate(lines) if "【要点（答え）】" in l)
    except StopIteration:
        sidx = -1

    bullet_lines: List[str] = []
    if sidx >= 0:
        for j in range(sidx + 1, min(sidx + 12, len(lines))):
            l = lines[j].strip()
            if not l:
                break
            # 次の大見出しに入ったら終わる
            if re.match(r"^\s*\d\s*[\.\)\:：]", l) or l.startswith("【"):
                break
            bullet_lines.append(l)

    # 分類（少し広め）
    for l in bullet_lines:
        if (not out["core_line"]) and any(k in l for k in ["核", "中心"]):
            out["core_line"] = l
        if (not out["shaky_line"]) and any(k in l for k in ["崩れ", "引き金", "揺れ"]):
            out["shaky_line"] = l
        if (not out["steady_line"]) and any(k in l for k in ["安定", "整え", "回復"]):
            out["steady_line"] = l

    keys = _extract_quoted_terms("\n".join(bullet_lines), limit=8)
    if not keys:
        keys = _extract_quoted_terms(prev_text, limit=8)

    out["keys"] = keys
    return out


def _build_prev_diff_summary_lines(
    *,
    prev_text: str,
    current_top_keys: List[str],
    current_core_line: str,
    current_shaky_line: str,
    current_steady_line: str,
    deltas: List[Tuple[str, int, float]],
) -> List[str]:
    """前回本文も参照して、差分を“要約差分”として返す。

    目的:
      - 人が欲しい「更新点」を先に明示する
      - ただし人格の断定はしない（観測→仮説の範囲）
    """
    if not prev_text:
        return []

    prev = _extract_prev_report_summary(prev_text)
    prev_keys: List[str] = list(prev.get("keys") or [])

    def _clean(line: str) -> str:
        return str(line or "").lstrip("・").strip()

    prev_core = _clean(str(prev.get("core_line") or ""))
    prev_shaky = _clean(str(prev.get("shaky_line") or ""))
    prev_steady = _clean(str(prev.get("steady_line") or ""))

    cur_core = _clean(str(current_core_line or ""))
    cur_shaky = _clean(str(current_shaky_line or ""))
    cur_steady = _clean(str(current_steady_line or ""))

    cur_keys = [k for k in (current_top_keys or []) if k][:3]
    prev_main = prev_keys[0] if prev_keys else ""
    cur_main = cur_keys[0] if cur_keys else ""

    lines: List[str] = []
    lines.append("【差分の要約（前回→今回）】")

    # 1) 核（答え）の比較（前回要点が取れていれば優先）
    if prev_core and cur_core:
        lines.append(f"・核の要点: 前回 {prev_core} / 今回 {cur_core}")
    else:
        if prev_main and cur_main:
            if prev_main != cur_main:
                lines.append(f"・中心テーマ: 『{prev_main}』→『{cur_main}』へ移動した可能性")
            else:
                lines.append(f"・中心テーマ: 『{cur_main}』が継続している可能性")
        elif cur_main:
            lines.append(f"・中心テーマ: 今回は『{cur_main}』が核になっている可能性")
        else:
            lines.append("・中心テーマ: （今回は材料が少なめで、核の推定が弱い）")

    # 2) 崩れ/安定の要点比較（取れたときだけ）
    if prev_shaky and cur_shaky:
        lines.append(f"・崩れ条件: 前回 {prev_shaky} / 今回 {cur_shaky}")
    if prev_steady and cur_steady:
        lines.append(f"・安定条件: 前回 {prev_steady} / 今回 {cur_steady}")

    # 3) 新規/減衰（短く）
    if cur_keys and prev_keys:
        new_keys = [k for k in cur_keys if k not in prev_keys]
        faded_keys = [k for k in prev_keys[:3] if k not in cur_keys]
        if new_keys:
            lines.append(f"・新しく目立ち始めた: 『{new_keys[0]}』")
        if faded_keys:
            lines.append(f"・落ち着いた可能性: 『{faded_keys[0]}』")

    # 4) データ差分（1行だけ）
    for k, dc, di in (deltas or [])[:8]:
        if dc == 0 and abs(di) < 0.12:
            continue
        sign = "増えた" if dc > 0 else "減った"
        lines.append(f"・データ差分: 『{k}』が{sign}（回数 {dc:+d} / 強度差 {di:+.1f}）")
        break

    # 余計に長くしない
    return lines[:8]

def build_myprofile_monthly_report(
    *,
    user_id: str,
    period: str = "30d",
    include_secret: bool = True,
    now: Optional[_dt.datetime] = None,
    prev_report_text: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """月次自己構造分析レポート本文と meta を返す。"""
    uid = str(user_id or "").strip()
    if not uid:
        return (
            "【自己構造分析レポート（月次）】\n\n（ユーザーIDが指定されていないため生成できませんでした）",
            {"engine": "astor_myprofile_report", "status": "no_user_id"},
        )

    days = parse_period_days(period)
    now_dt = now or _dt.datetime.utcnow().replace(microsecond=0, tzinfo=_dt.timezone.utc)

    end = now_dt
    start = end - _dt.timedelta(days=max(days, 1))
    prev_end = start
    prev_start = prev_end - _dt.timedelta(days=max(days, 1))

    structures_map = _load_structures_map(uid)
    cur_views = _collect_period_views(structures_map, start=start, end=end, include_secret=include_secret)
    prev_views = _collect_period_views(structures_map, start=prev_start, end=prev_end, include_secret=include_secret)

    prev_map = {v.key: v for v in prev_views}

    # top structures
    top = cur_views[:3]
    top_keys = [v.key for v in top]

    # Deep Insight
    deep_answers = _load_deep_insight_answers(uid, include_secret=include_secret, limit=6)

    # 差分
    deltas: List[Tuple[str, int, float]] = []  # key, delta_count, delta_intensity
    for v in cur_views[:8]:
        pv = prev_map.get(v.key)
        dc = v.count - (pv.count if pv else 0)
        di = v.avg_intensity - (pv.avg_intensity if pv else 0.0)
        deltas.append((v.key, dc, di))
    deltas.sort(key=lambda x: (abs(x[1]), abs(x[2])), reverse=True)

        # 要点（答え）
    if top:
        core = "・核（いちばん出やすい自己テーマ）: " + "、".join([f"『{k}』" for k in top_keys[:2]])
        shaky = "・崩れ条件（揺れを強めやすい引き金）: "
        # top構造に紐づく感情ヒント（ただし MyWeb に踏み込みすぎない）
        ehs: List[str] = []
        for v in top[:2]:
            if v.top_emotions:
                ehs.extend([emo_label_ja(x) for x in v.top_emotions])
        ehs = [x for i, x in enumerate(ehs) if x and x not in ehs[:i]]

        if ehs:
            shaky += f"{ '／'.join(ehs[:2]) }が強い場面で、判断が硬くなりやすい可能性"
        else:
            shaky += "刺激が重なった場面で、意味づけが固定されやすい可能性"

        steady = "・安定に寄せるキー（整える1手）: "
        if deep_answers:
            steady += "判断の前に『基準を1行だけ言語化』すると、構造の暴走が収まりやすい"
            one_liner = f"・ひとこと: いまは『{top[0].key}』が起点になりやすい状態。判断が硬くなる前に“1行メモ”が効きやすい。"
        else:
            steady += "『刺激/解釈/身体』を1行メモすると、揺れがほどけやすい"
            one_liner = f"・ひとこと: いまは『{top[0].key}』が起点になりやすい状態。判断が硬くなる前に“1行メモ”が効きやすい。"
    else:
        core = "・核（いちばん出やすい自己テーマ）: （この期間は材料が少なめ）"
        shaky = "・崩れ条件（揺れを強めやすい引き金）: （未観測）"
        steady = "・安定に寄せるキー（整える1手）: 観測メモを増やすと輪郭が出ます"
        one_liner = "・ひとこと: 入力が少なめ。短文でもいいので観測を増やすと輪郭が出ます。"

# 領域メモの割り当て
    bucket = _guess_domain_hints(top_keys)

    lines: List[str] = []
    lines.append("【自己構造分析レポート（月次）】")
    lines.append("")
    lines.append("【要点（答え）】")
    lines.append(core)
    lines.append(shaky)
    lines.append(steady)
    lines.append(one_liner)
    lines.append("※診断ではなく、観測に基づく仮説です。")
    lines.append("")

    # 1. 輪郭
    lines.append("1. 今月の輪郭（仮説・1〜4行）")
    if not top:
        lines.append("この期間は入力が少なめで、自己モデルの輪郭がまだ薄い状態です。")
        lines.append("感情入力や自己理解/Deep Insight の回答が増えるほど、自己モデルの精度は上がっていきます。")
    else:
        gloss1 = _short_structure_gloss(top[0].key)
        if gloss1:
            lines.append(f"核として『{top[0].key}』が出やすく（意味: {gloss1}）、判断の起点になっている可能性があります。")
        else:
            lines.append(f"核として『{top[0].key}』が出やすく、判断の起点になっている可能性があります。")
        if len(top) >= 2:
            lines.append(f"さらに『{top[1].key}』が重なると、見立てが揺れた瞬間に構造が濃くなりやすい可能性があります。")
        lines.append("※これは診断ではなく、最近の入力から読み取れる“仮の自己モデル”です。")
    lines.append("")

    # 2. 反応パターン
    lines.append("2. 主要な反応パターン（刺激→認知→感情→行動）")
    if not top:
        lines.append("（未観測：まずは“刺激/解釈/感情/行動”を1セットだけでもメモすると、パターンが立ち上がります）")
    else:
        for i, v in enumerate(top[:2], start=1):
            emo_hint = "、".join([emo_label_ja(x) for x in v.top_emotions]) if v.top_emotions else "感情"
            lines.append(f"- パターン{i}: 『{v.key}』")
            lines.append("  流れ: 刺激 → 認知 → 感情 → 行動")
            lines.append(f"  刺激: （例）評価/比較/期待のズレ/未確定など、『{v.key}』を強めやすい出来事")
            lines.append(f"  認知: （仮）『{v.key}』の判断が入り、意味づけが固定されやすい")
            lines.append(f"  感情: {emo_hint} に寄りやすい")
            lines.append("  行動: （仮）確認/修正へ向かう、または一時停止して距離を取る")
            if v.sample_memos:
                lines.append(f"  観測メモ（例）: {v.sample_memos[0]}")
    lines.append("")

    # 3. 条件
    lines.append("3. 安定条件（安心が生まれやすい条件） / 崩れ条件（揺れやすい条件）")
    lines.append("安定条件:")
    lines.append("・判断の前に『刺激/解釈/身体』を1行で切り分けられる")
    if deep_answers:
        lines.append("・Deep Insight の回答で自分の基準を言語化できているとき")
    lines.append("・忙しい日は短文でもいいので“観測”だけは継続できる")
    lines.append("崩れ条件:")
    if top:
        # 最も強い構造
        worst = max(top, key=lambda x: x.avg_intensity)
        lines.append(f"・『{worst.key}』が{_intensity_label(worst.avg_intensity)}で出ている日に、判断が硬直しやすい")
    lines.append("・未確定/比較/評価が重なる場面で、解釈が一気に固定されやすい（視野が狭くなりやすい）")
    lines.append("")

    # 4. 思考のクセ
    lines.append("4. 思考のクセ・判断のクセ（あれば）")
    if not top:
        lines.append("（未観測）")
    else:
        lines.append(f"・『{top[0].key}』が上位に出ているため、判断の起点が“評価/意味づけ”に寄りやすい可能性があります。")
        if len(top) >= 2:
            lines.append(f"・『{top[1].key}』が重なると、白黒を急がず“仮置き”するのが難しくなることがあります。")
        lines.append("・対策としては、結論を急がず『観測→仮説』の順に戻すのが有効です。")
    lines.append("")

    # 5. 領域別
    lines.append("5. 領域別メモ（仕事/対人/孤独/挑戦/評価など、見えている範囲で）")
    for domain in ["仕事", "対人", "孤独", "挑戦", "評価"]:
        hints = bucket.get(domain) or []
        if hints:
            lines.append(f"- {domain}: 『{ '』『'.join(hints) }』が絡む場面で自己モデルが動きやすい可能性")
        else:
            lines.append(f"- {domain}: （この期間の観測からは強い偏りは不明）")
    lines.append("")

    # 6. 観測ポイント
    lines.append("6. 次の観測ポイント（3つ。行動に落ちる形で）")
    lines.append("・揺れた瞬間に『何が刺激だったか』を1語で書く")
    lines.append("・その刺激を『どう解釈したか（1文）』を書いてから、感情ラベルを選ぶ")
    lines.append("・強い日は『身体（睡眠/空腹/疲労）』も一緒にメモして、構造と身体を分けて観測する")
    lines.append("")

    # 7. 差分
    lines.append("7. 前回との差分（変化点 / 更新点 / 揺れ方の違い）")

    used_prev_text = False
    if prev_report_text:
        try:
            diff_lines = _build_prev_diff_summary_lines(
                prev_text=str(prev_report_text),
                current_top_keys=top_keys,
                current_core_line=core,
                current_shaky_line=shaky,
                current_steady_line=steady,
                deltas=deltas,
            )
            if diff_lines:
                lines.extend(diff_lines)
                used_prev_text = True
        except Exception:
            used_prev_text = False

    # 前回本文が無い場合/抽出できない場合は、データ差分で補う
    if not used_prev_text:
        if not prev_views and not cur_views:
            lines.append("前回/今回ともに観測材料が少ないため、差分はまだ評価できません。")
        elif not prev_views and cur_views:
            lines.append("前回期間は観測材料が少なく、今回から自己構造が立ち上がり始めた状態です。")
        else:
            shown = 0
            for k, dc, di in deltas:
                if shown >= 3:
                    break
                if dc == 0 and abs(di) < 0.1:
                    continue
                sign = "増えた" if dc > 0 else "減った"
                lines.append(f"・『{k}』が{sign}（出現回数の差分: {dc:+d} / 強度差: {di:+.1f}）")
                shown += 1
            if shown == 0:
                lines.append("大きな差分は目立たず、構造は安定して推移しています。")

    lines.append("")

    # 8. 感情構造との接続
    lines.append("8. 感情構造との接続（MyWebに譲る前提で、短く）")
    if top:
        lines.append(f"MyWebで感情の揺れ（不安/怒りなど）が目立つとき、背景で『{top[0].key}』が立っている可能性があります。")
        lines.append("感情の“天気”と、自己構造の“地形”を分けて見るほど、回復が速くなります。")
    else:
        lines.append("MyWeb（感情傾向）で揺れが見えたら、MyProfile側で“刺激→解釈”の観測を増やすと接続が強くなります。")

    meta = {
        "engine": "astor_myprofile_report",
        "version": "myprofile.report.v1",
        "period": period,
        "period_days": days,
        "data_scope": "self" if include_secret else "public",
        "diff_reference": "prev_report_text" if (prev_report_text and used_prev_text) else "data_only",
        "top_structures": [
            {
                "key": v.key,
                "count": v.count,
                "avg_intensity": v.avg_intensity,
            }
            for v in top
        ],
        "deep_insight_answers": len(deep_answers),
    }

    return ("\n".join(lines).strip() + "\n", meta)
