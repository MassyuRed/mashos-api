
# -*- coding: utf-8 -*-
"""piece_generation_engine.py

Premium Reflection generation engine (v1)
========================================

役割
----
`premium_reflection_view`（material snapshot payload）を受け取り、
Premium dynamic Reflections の「生成計画（create / update / deactivate）」を返す。

このファイルは国家機構上の「Reflections生成局」の中核ロジックだけを持つ。
以下は別責務のため、このファイルでは行わない。

- DB 保存 / upsert
- lock / priority / eviction
- inspection enqueue
- publish 判定
- template（MyModelCreate）Reflection の生成

前提
----
- 材料は `premium_reflection_view` のみ
- `premium_reflection_view` は secret-OFF の InputScreen 入力のみ
- MyModelCreate は本エンジンでは使わない
- 生成単位は 1ユーザー
- 生成タイミングは snapshot 作成後
- question は短い題名（短いブログタイトルに近い）
- 既存 topic にマッチした場合は question を固定し、answer だけ更新する
- Topic 数は可変。ただし保存側で上限（例: 50）を持つ前提

設計の流れ
----------
1. normalize
2. (category + text) embedding
3. focus 判定（fun / relief / growth / values / stress / relationship / generic）
4. existing topic attach
5. new topic clustering
6. question / answer generation
7. create / update / deactivate plan を返す

実装メモ
--------
- 高精度型の設計に合わせて意味ベースの clustering を意識する。
- v1 は外部 embedding API を必須にせず、ローカルの deterministic hashing embedding を標準実装として持つ。
- 将来的に外部 embedding / LLM へ差し替えやすいよう、クラス責務は分けている。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import logging
import math
import os
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from piece_generated_identity import compute_generated_question_q_key


logger = logging.getLogger("astor_reflection_engine")

# ---------- thresholds / limits ----------
try:
    EXISTING_TOPIC_MATCH_THRESHOLD = float(
        os.getenv("REFLECTION_EXISTING_TOPIC_MATCH_THRESHOLD", "0.82") or "0.82"
    )
except Exception:
    EXISTING_TOPIC_MATCH_THRESHOLD = 0.82

try:
    EXISTING_TOPIC_RELAXED_THRESHOLD = float(
        os.getenv("REFLECTION_EXISTING_TOPIC_RELAXED_THRESHOLD", "0.45") or "0.45"
    )
except Exception:
    EXISTING_TOPIC_RELAXED_THRESHOLD = 0.45

try:
    NEW_TOPIC_MERGE_THRESHOLD = float(
        os.getenv("REFLECTION_NEW_TOPIC_MERGE_THRESHOLD", "0.78") or "0.78"
    )
except Exception:
    NEW_TOPIC_MERGE_THRESHOLD = 0.78

try:
    GENERIC_TOPIC_MERGE_THRESHOLD = float(
        os.getenv("REFLECTION_GENERIC_TOPIC_MERGE_THRESHOLD", "0.56") or "0.56"
    )
except Exception:
    GENERIC_TOPIC_MERGE_THRESHOLD = 0.56

try:
    LOCAL_EMBED_DIM = int(os.getenv("REFLECTION_LOCAL_EMBED_DIM", "256") or "256")
except Exception:
    LOCAL_EMBED_DIM = 256

try:
    MAX_SIGNALS_PER_TOPIC = int(os.getenv("REFLECTION_MAX_SIGNALS_PER_TOPIC", "12") or "12")
except Exception:
    MAX_SIGNALS_PER_TOPIC = 12

try:
    REFLECTION_LATEST_STATE_WINDOW_HOURS = int(
        os.getenv("REFLECTION_LATEST_STATE_WINDOW_HOURS", "72") or "72"
    )
except Exception:
    REFLECTION_LATEST_STATE_WINDOW_HOURS = 72

try:
    MAX_TEXT_LEN_FOR_EMBEDDING = int(
        os.getenv("REFLECTION_MAX_TEXT_LEN_FOR_EMBEDDING", "500") or "500"
    )
except Exception:
    MAX_TEXT_LEN_FOR_EMBEDDING = 500

DEFAULT_REQUIRED_PLAN_TIER = (os.getenv("REFLECTION_REQUIRED_PLAN_TIER") or "premium").strip() or "premium"
DEFAULT_SCOPE = (os.getenv("REFLECTION_SCOPE_DEFAULT") or "global").strip() or "global"

# ---------- text helpers ----------
_WORD_RE = re.compile(r"[一-龯ぁ-んァ-ンーA-Za-z0-9]+")
_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[「」『』【】\[\]（）()<>＜＞\"'`]+")
_MULTI_SEP_RE = re.compile(r"[、,／/・|｜]+")

_STOPWORDS = {
    "こと", "もの", "感じ", "最近", "自分", "相手", "少し", "かなり", "とても", "すごく", "なんか",
    "なんとなく", "ような", "みたい", "ところ", "ため", "ので", "から", "けど", "けれど",
}

# ---------- dataclasses ----------
@dataclass
class ReflectionSignal:
    source_type: str
    source_id: str
    timestamp: str
    category: str
    text_primary: str
    text_secondary: str
    source_weight: float
    embedding_text: str
    question_text: Optional[str] = None
    emotion_signals: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    focus_key: Optional[str] = None


@dataclass
class ExistingReflectionTopic:
    reflection_id: str
    topic_key: str
    category: str
    question: str
    answer: str
    topic_embedding: Optional[List[float]]
    topic_summary_text: str
    focus_key: Optional[str] = None
    is_active: bool = True


@dataclass
class TopicCluster:
    topic_key: Optional[str]
    category: str
    signals: List[ReflectionSignal]
    centroid: List[float]
    matched_reflection_id: Optional[str]
    topic_summary_text: str
    focus_key: Optional[str] = None


# ---------- small utilities ----------
def _clean_text(x: Any) -> str:
    s = str(x or "")
    s = _PUNCT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _clamp_text(s: str, max_len: int) -> str:
    x = _clean_text(s)
    if len(x) <= max_len:
        return x
    return x[: max(1, max_len)].rstrip()


def _unique_keep_order(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for v in values:
        s = str(v or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _safe_float_list(v: Any) -> Optional[List[float]]:
    if not isinstance(v, list):
        return None
    out: List[float] = []
    for x in v:
        try:
            out.append(float(x))
        except Exception:
            return None
    return out or None


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(n):
        xa = float(a[i]); xb = float(b[i])
        dot += xa * xb
        na += xa * xa
        nb += xb * xb
    if na <= 1e-12 or nb <= 1e-12:
        return 0.0
    return dot / math.sqrt(na * nb)


def _normalize_vector(v: Sequence[float]) -> List[float]:
    n = math.sqrt(sum(float(x) * float(x) for x in v))
    if n <= 1e-12:
        return [0.0 for _ in v]
    return [float(x) / n for x in v]


def _weighted_centroid(vectors: Sequence[Sequence[float]], weights: Sequence[float]) -> List[float]:
    if not vectors:
        return []
    dim = len(vectors[0])
    acc = [0.0] * dim
    total = 0.0
    for idx, vec in enumerate(vectors):
        w = float(weights[idx] if idx < len(weights) else 1.0)
        total += w
        for i in range(min(dim, len(vec))):
            acc[i] += float(vec[i]) * w
    if total <= 1e-12:
        return _normalize_vector(acc)
    return _normalize_vector([x / total for x in acc])


def _parse_signal_timestamp(value: Any) -> Optional[datetime]:
    text = str(value or '').strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace('Z', '+00:00'))
    except Exception:
        return None


def _select_latest_state_signals(signals: Sequence[ReflectionSignal]) -> List[ReflectionSignal]:
    ordered_desc = sorted(
        list(signals or []),
        key=lambda signal: (_parse_signal_timestamp(getattr(signal, 'timestamp', '') or '') or datetime.min, str(getattr(signal, 'timestamp', '') or ''), str(getattr(signal, 'source_type', '') or ''), str(getattr(signal, 'source_id', '') or '')),
        reverse=True,
    )
    if not ordered_desc:
        return []

    parsed_latest = _parse_signal_timestamp(getattr(ordered_desc[0], 'timestamp', '') or '')
    if parsed_latest is None:
        return ordered_desc

    threshold = parsed_latest - timedelta(hours=max(1, int(REFLECTION_LATEST_STATE_WINDOW_HOURS or 72)))
    latest_only = [
        signal
        for signal in ordered_desc
        if (_parse_signal_timestamp(getattr(signal, 'timestamp', '') or '') or parsed_latest) >= threshold
    ]
    return latest_only or ordered_desc


def _tokenize_for_embedding(text: str) -> List[str]:
    s = _clean_text(text).lower()
    words = _WORD_RE.findall(s)
    out: List[str] = []
    for w in words:
        ww = w.strip()
        if not ww:
            continue
        out.append(ww)
        if len(ww) >= 2:
            out.extend(ww[i : i + 2] for i in range(len(ww) - 1))
        if len(ww) >= 3:
            out.extend(ww[i : i + 3] for i in range(len(ww) - 2))
    if not out and s:
        out.append(s)
    return out


def _embed_text_local(text: str, *, dim: int = LOCAL_EMBED_DIM) -> List[float]:
    """Deterministic local hashing embedding.

    外部 embedding API を必須にせず semantic-ish な clustering を回すためのローカル実装。
    将来的には置き換え可能。
    """
    tokens = _tokenize_for_embedding(text)
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim
    for tok in tokens:
        seed = hashlib.sha256(tok.encode("utf-8")).digest()
        idx = int.from_bytes(seed[:4], "big") % dim
        sign = 1.0 if (seed[4] % 2 == 0) else -1.0
        mag = 0.5 + ((seed[5] % 100) / 100.0)
        vec[idx] += sign * mag
    return _normalize_vector(vec)


def _format_embedding_text(
    *,
    category: str,
    text_primary: str,
    text_secondary: str,
    emotion_signals: Optional[List[str]] = None,
    question_text: Optional[str] = None,
) -> str:
    parts: List[str] = []
    cat = _clean_text(category)
    if cat:
        parts.extend([cat, cat])  # category is user-chosen and should have stronger influence

    tp = _clamp_text(text_primary, MAX_TEXT_LEN_FOR_EMBEDDING)
    ts = _clamp_text(text_secondary, MAX_TEXT_LEN_FOR_EMBEDDING // 2)
    if tp:
        parts.append(tp)
    if ts:
        parts.append(ts)

    emos = _unique_keep_order(emotion_signals or [])
    if emos:
        parts.append(" ".join(emos[:8]))

    if question_text:
        parts.append(_clamp_text(question_text, 120))

    return " ".join([p for p in parts if p]).strip()


def _build_source_refs(signals: Sequence[ReflectionSignal]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for s in signals:
        key = (s.source_type, s.source_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "source_type": s.source_type,
                "source_id": s.source_id,
                "timestamp": s.timestamp,
                "category": s.category,
            }
        )
    return out


def _make_topic_key(*, user_id: str, category: str, focus_key: str, topic_summary_text: str) -> str:
    base = f"reflection_topic_v1|{user_id}|{category}|{focus_key}|{_clean_text(topic_summary_text)}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _extract_existing_reflection_id(row: Dict[str, Any]) -> str:
    return (
        str(row.get("id") or "")
        or str(row.get("reflection_id") or "")
        or str(row.get("public_id") or "")
        or str(row.get("q_instance_id") or "")
    ).strip()


def _extract_existing_topic_key(row: Dict[str, Any]) -> str:
    return str(row.get("topic_key") or row.get("q_key") or "").strip()


def _extract_existing_embedding(row: Dict[str, Any]) -> Optional[List[float]]:
    direct = _safe_float_list(row.get("topic_embedding"))
    if direct:
        return direct
    meta = row.get("meta")
    if isinstance(meta, dict):
        for key in ("topic_embedding", "embedding"):
            vv = _safe_float_list(meta.get(key))
            if vv:
                return vv
    return None


def _extract_existing_summary_text(row: Dict[str, Any]) -> str:
    meta = row.get("meta")
    if isinstance(meta, dict):
        s = _clean_text(meta.get("topic_summary_text"))
        if s:
            return s
    return _clean_text(
        " / ".join(
            [
                str(row.get("category") or ""),
                str(row.get("question") or row.get("title") or ""),
                str(row.get("answer") or row.get("body") or ""),
            ]
        )
    )


# ---------- focus / phrase heuristics ----------
def _select_focus_key(category: str, texts: Sequence[str]) -> str:
    text = " ".join([_clean_text(category)] + [_clean_text(t) for t in texts if _clean_text(t)])

    rules = [
        (re.compile(r"頑張|努力|挑戦|成長|学び|勉強|上達|試す|工夫"), "growth"),
        (re.compile(r"落ち着|安心|癒|リラックス|整う|休む|ほっと"), "relief"),
        (re.compile(r"大切|価値|信念|大事|守りたい"), "values"),
        (re.compile(r"不安|迷い|悩み|ストレス|しんど"), "stress"),
        (re.compile(r"人|家族|友人|恋愛|関係|相手|誰か"), "relationship"),
        (re.compile(r"楽しい|楽しく|楽しかった|楽しみ|楽しめ|好き|わくわく|夢中|おもしろ|面白"), "fun"),
    ]
    for pat, key in rules:
        if pat.search(text):
            return key
    return "generic"


def _strip_category_prefix(text: str, category: str) -> str:
    s = _clean_text(text)
    cat = _clean_text(category)
    if not s or not cat:
        return s

    prefixes = [f"{cat}では", f"{cat}には", f"{cat}の", f"{cat}に", f"{cat}で", cat]
    for p in prefixes:
        if s.startswith(p):
            s = s[len(p) :].strip(" 、,")
            break

    for p in ("最近", "この頃", "ここ最近", "今は", "いまは", "は", "が"):
        if s.startswith(p):
            s = s[len(p) :].strip(" 、,")
            break
    return s


def _normalize_phrase_ending(phrase: str) -> str:
    p = _clean_text(phrase)
    if not p:
        return p

    replacements = [
        ("を見に行って", "を見に行く"),
        ("を見にいって", "を見に行く"),
        ("に行って", "に行く"),
        ("にいって", "に行く"),
        ("に行った", "に行く"),
        ("にいった", "に行く"),
        ("見て", "見る"),
        ("みて", "見る"),
        ("していて", "する"),
        ("してる", "する"),
        ("していた", "する"),
        ("してた", "する"),
        ("して", "する"),
        ("読んで", "読む"),
        ("聞いて", "聞く"),
        ("聴いて", "聴く"),
        ("話して", "話す"),
        ("考えて", "考える"),
        ("感じて", "感じる"),
        ("休んで", "休む"),
        ("作って", "作る"),
        ("歩いて", "歩く"),
        ("過ごして", "過ごす"),
        ("整えて", "整える"),
        ("頑張って", "頑張る"),
        ("学んで", "学ぶ"),
    ]
    for old, new in replacements:
        if p.endswith(old):
            p = p[: -len(old)] + new
            return p

    # rough fixes for cut-off stems
    cut_rules = [
        (r"に行っ$", "に行く"),
        (r"を見に行っ$", "を見に行く"),
        (r"見に行っ$", "見に行く"),
        (r"見にいっ$", "見に行く"),
    ]
    for pat, repl in cut_rules:
        if re.search(pat, p):
            p = re.sub(pat, repl, p)
            return p

    return p


def _extract_core_phrase(text: str, *, category: str) -> str:
    s = _strip_category_prefix(text, category)
    if not s:
        return ""

    patterns = [
        r"(.+?)(?:のが|ことが)(?:最近の)?(?:楽しみ|好き|心地いい|心地よい|落ち着く)",
        r"(.+?)(?:とても|すごく|かなり)?楽しかった",
        r"(.+?)(?:とても|すごく|かなり)?嬉しかった",
        r"(.+?)(?:している|してる)$",
        r"(.+?)(?:したい)$",
        r"(.+?)こと$",
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            return _normalize_phrase_ending(m.group(1))

    clause = re.split(r"[。！？!?]", s)[0].strip()
    clause = _MULTI_SEP_RE.split(clause)[0].strip()
    return _normalize_phrase_ending(clause)


def _nominalize_phrase(phrase: str) -> str:
    p = _clean_text(phrase)
    if not p:
        return ""
    if p.endswith("こと"):
        return p
    if re.search(r"(する|行く|見る|作る|読む|聞く|聴く|話す|考える|感じる|休む|過ごす|学ぶ|整える|頑張る)$", p):
        return f"{p}こと"
    return p


def _build_topic_summary_text(category: str, signals: Sequence[ReflectionSignal]) -> str:
    parts: List[str] = []
    for s in signals[:MAX_SIGNALS_PER_TOPIC]:
        for text in (s.text_primary, s.text_secondary):
            phr = _extract_core_phrase(text, category=s.category or category)
            if phr:
                parts.append(phr)

    parts = [p for p in _unique_keep_order(parts) if p and p not in _STOPWORDS]
    joined = " / ".join(parts[:4])
    cat = _clean_text(category)
    if cat and joined:
        return f"{cat} / {joined}"
    return joined or cat or "reflection_topic"


def _fallback_question(category: str, focus_key: str) -> str:
    cat = _clean_text(category)

    if cat:
        if re.search(r"休日|休み|余暇|オフ", cat):
            mapping = {
                "fun": "休日の楽しい過ごし方は？",
                "relief": "休日に心が休まる時間は？",
                "values": "休日に大切にしていることは？",
                "generic": "休日の過ごし方は？",
            }
            return mapping.get(focus_key, "休日の過ごし方は？")

        if re.search(r"趣味|娯楽|遊び", cat):
            mapping = {
                "fun": "最近夢中なことは？",
                "relief": "心がほどける時間は？",
                "generic": "最近気になることは？",
            }
            return mapping.get(focus_key, "最近夢中なことは？")

        if re.search(r"仕事|職場|キャリア", cat):
            mapping = {
                "growth": "仕事で伸ばしたいことは？",
                "values": "仕事で大切にしていることは？",
                "stress": "仕事でしんどい時の整え方は？",
                "generic": "仕事で気にしていることは？",
            }
            return mapping.get(focus_key, "仕事で大切にしていることは？")

        if re.search(r"学習|勉強|学び", cat):
            return "学びを続ける理由は？"

        if re.search(r"健康|体調|生活習慣", cat):
            return "心と体を整える方法は？"

        if re.search(r"家族|友人|恋愛|人間関係|対人", cat):
            return "人との関わりで大切なことは？"

        if re.search(r"感情|気持ち", cat):
            mapping = {
                "stress": "気持ちが揺れる時は？",
                "relief": "気持ちが落ち着く時間は？",
                "fun": "気持ちが明るくなる瞬間は？",
                "generic": "気持ちが動く瞬間は？",
            }
            return mapping.get(focus_key, "気持ちが動く瞬間は？")

        if re.search(r"価値観|人生", cat):
            return "大切にしていることは？"


    generic = {
        "fun": "最近の楽しみは？",
        "relief": "心が休まる時間は？",
        "growth": "伸ばしたいことは？",
        "values": "大切にしていることは？",
        "stress": "気持ちを整える方法は？",
        "relationship": "人との関わりで大切なことは？",
        "generic": "最近気づいたことは？",
    }
    return generic.get(focus_key, "最近気づいたことは？")


def _fallback_answer(category: str, signals: Sequence[ReflectionSignal]) -> str:
    phrases: List[str] = []
    for s in signals[:MAX_SIGNALS_PER_TOPIC]:
        for text in (s.text_primary, s.text_secondary):
            phr = _extract_core_phrase(text, category=s.category or category)
            if phr:
                phrases.append(_nominalize_phrase(phr))

    uniq = _unique_keep_order([p for p in phrases if p])
    if not uniq:
        texts = _unique_keep_order(
            [_clamp_text(s.text_primary or s.text_secondary, 70) for s in signals if (s.text_primary or s.text_secondary)]
        )
        if not texts:
            return "まだ言葉になりきっていないテーマ。"
        if len(texts) == 1:
            return texts[0] + "。"
        return "、".join(texts[:2]) + "。"

    if len(uniq) == 1:
        return uniq[0] + "。"
    if len(uniq) == 2:
        return f"{uniq[0]}や、{uniq[1]}。"
    return "、".join(uniq[:3]) + "。"


# ---------- normalizer ----------
class ReflectionInputNormalizer:
    def normalize(self, premium_reflection_view: Dict[str, Any]) -> List[ReflectionSignal]:
        items = []
        if isinstance(premium_reflection_view, dict):
            items = premium_reflection_view.get("items") or []
        if not isinstance(items, list):
            return []

        out: List[ReflectionSignal] = []
        seen = set()

        for raw in items:
            if not isinstance(raw, dict):
                continue

            source_type = str(raw.get("source_type") or "").strip()
            source_id = str(raw.get("source_id") or "").strip()
            timestamp = str(raw.get("timestamp") or "").strip()
            category = _clean_text(raw.get("category"))
            text_primary = _clean_text(raw.get("text_primary"))
            text_secondary = _clean_text(raw.get("text_secondary"))
            question_text = _clean_text(raw.get("question_text")) or None

            if not source_type or not source_id:
                continue
            if not category:
                continue
            if not text_primary and not text_secondary:
                continue

            key = (source_type, source_id)
            if key in seen:
                continue
            seen.add(key)

            try:
                source_weight = float(raw.get("source_weight") or 1.0)
            except Exception:
                source_weight = 1.0

            emotion_signals = []
            if isinstance(raw.get("emotion_signals"), list):
                emotion_signals = [
                    str(x).strip() for x in raw.get("emotion_signals") or [] if str(x).strip()
                ]

            embedding_text = _format_embedding_text(
                category=category,
                text_primary=text_primary,
                text_secondary=text_secondary,
                emotion_signals=emotion_signals,
                question_text=question_text,
            )
            focus_key = _select_focus_key(category, [text_primary, text_secondary, question_text or ""])

            out.append(
                ReflectionSignal(
                    source_type=source_type,
                    source_id=source_id,
                    timestamp=timestamp,
                    category=category,
                    text_primary=text_primary,
                    text_secondary=text_secondary,
                    source_weight=source_weight,
                    embedding_text=embedding_text,
                    question_text=question_text,
                    emotion_signals=emotion_signals,
                    focus_key=focus_key,
                )
            )

        out.sort(key=lambda s: (s.timestamp, s.source_type, s.source_id))
        return out


# ---------- topic detector ----------
class ReflectionTopicDetector:
    def embed_signals(self, signals: Sequence[ReflectionSignal]) -> None:
        for s in signals:
            if s.embedding is None:
                s.embedding = _embed_text_local(s.embedding_text)

    def _build_existing_topics(self, rows: Sequence[Dict[str, Any]]) -> List[ExistingReflectionTopic]:
        out: List[ExistingReflectionTopic] = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue

            source_type = str(row.get("source_type") or "").strip()
            if source_type and source_type != "generated":
                continue

            reflection_id = _extract_existing_reflection_id(row)
            if not reflection_id:
                continue

            if row.get("is_active") is False:
                continue

            category = _clean_text(row.get("category"))
            question = _clean_text(row.get("question") or row.get("title"))
            answer = _clean_text(row.get("answer") or row.get("body"))
            if not category and not question and not answer:
                continue

            topic_embedding = _extract_existing_embedding(row)
            topic_summary_text = _extract_existing_summary_text(row)
            focus_key = _select_focus_key(category, [question, answer, topic_summary_text])

            if not topic_embedding:
                topic_embedding = _embed_text_local(
                    _format_embedding_text(
                        category=category or "generated",
                        text_primary=topic_summary_text or answer,
                        text_secondary=question,
                    )
                )

            out.append(
                ExistingReflectionTopic(
                    reflection_id=reflection_id,
                    topic_key=_extract_existing_topic_key(row) or reflection_id,
                    category=category,
                    question=question,
                    answer=answer,
                    topic_embedding=topic_embedding,
                    topic_summary_text=topic_summary_text,
                    focus_key=focus_key,
                    is_active=True,
                )
            )
        return out

    def attach_to_existing_topics(
        self,
        signals: Sequence[ReflectionSignal],
        existing_dynamic_reflections: Sequence[Dict[str, Any]],
    ) -> Tuple[List[TopicCluster], List[ReflectionSignal], List[ExistingReflectionTopic]]:
        existing_topics = self._build_existing_topics(existing_dynamic_reflections)
        self.embed_signals(signals)

        by_reflection: Dict[str, List[ReflectionSignal]] = {}
        unmatched: List[ReflectionSignal] = []

        for s in signals:
            best_topic: Optional[ExistingReflectionTopic] = None
            best_score = -1.0
            for topic in existing_topics:
                if topic.category and s.category and topic.category != s.category:
                    continue

                sim = _cosine_similarity(s.embedding or [], topic.topic_embedding or [])
                same_focus = bool(topic.focus_key and s.focus_key and topic.focus_key == s.focus_key)

                # Relaxed rule:
                # same category + same focus is treated as a strong structural match.
                # This intentionally allows:
                #   休日 + fun + カラオケ
                #   休日 + fun + 映画
                # to update the same Reflection.
                if same_focus:
                    score = sim + 0.20
                    if score > best_score:
                        best_score = score
                        best_topic = topic
                    continue

                score = sim
                if score > best_score and sim >= EXISTING_TOPIC_MATCH_THRESHOLD:
                    best_score = score
                    best_topic = topic

            if best_topic is not None:
                by_reflection.setdefault(best_topic.reflection_id, []).append(s)
            else:
                unmatched.append(s)

        clusters: List[TopicCluster] = []
        topic_map = {t.reflection_id: t for t in existing_topics}
        for reflection_id, topic_signals in by_reflection.items():
            topic = topic_map[reflection_id]
            sigs = sorted(topic_signals, key=lambda x: (x.timestamp, x.source_type, x.source_id))
            vectors = [s.embedding or _embed_text_local(s.embedding_text) for s in sigs]
            weights = [max(0.1, float(s.source_weight)) for s in sigs]
            centroid = _weighted_centroid(vectors, weights)
            summary = _build_topic_summary_text(topic.category or (sigs[0].category if sigs else ""), sigs)
            clusters.append(
                TopicCluster(
                    topic_key=topic.topic_key,
                    category=topic.category or (sigs[0].category if sigs else ""),
                    signals=sigs,
                    centroid=centroid,
                    matched_reflection_id=topic.reflection_id,
                    topic_summary_text=summary or topic.topic_summary_text,
                    focus_key=topic.focus_key or (sigs[0].focus_key if sigs else "generic"),
                )
            )

        return clusters, unmatched, existing_topics

    def cluster_new_topics(self, signals: Sequence[ReflectionSignal]) -> List[TopicCluster]:
        if not signals:
            return []

        self.embed_signals(signals)

        # Category is mandatory. For non-generic focus, merge at (category + focus) level.
        buckets: Dict[Tuple[str, str], List[ReflectionSignal]] = {}
        generic_by_category: Dict[str, List[ReflectionSignal]] = {}

        for s in signals:
            focus = s.focus_key or "generic"
            if focus == "generic":
                generic_by_category.setdefault(s.category, []).append(s)
            else:
                buckets.setdefault((s.category, focus), []).append(s)

        clusters: List[TopicCluster] = []

        # Non-generic topics: one cluster per (category, focus)
        for (category, focus), bucket_signals in buckets.items():
            sigs = sorted(bucket_signals, key=lambda x: (x.timestamp, x.source_type, x.source_id))
            vectors = [s.embedding or _embed_text_local(s.embedding_text) for s in sigs]
            weights = [max(0.1, float(s.source_weight)) for s in sigs]
            centroid = _weighted_centroid(vectors, weights)
            summary = _build_topic_summary_text(category, sigs)
            clusters.append(
                TopicCluster(
                    topic_key=None,
                    category=category,
                    signals=sigs,
                    centroid=centroid,
                    matched_reflection_id=None,
                    topic_summary_text=summary,
                    focus_key=focus,
                )
            )

        # Generic topics: similarity-based clustering within category
        for category, bucket_signals in generic_by_category.items():
            sigs = sorted(bucket_signals, key=lambda x: (x.timestamp, x.source_type, x.source_id))
            n = len(sigs)
            if n == 1:
                one = sigs[0]
                clusters.append(
                    TopicCluster(
                        topic_key=None,
                        category=category,
                        signals=[one],
                        centroid=one.embedding or _embed_text_local(one.embedding_text),
                        matched_reflection_id=None,
                        topic_summary_text=_build_topic_summary_text(category, [one]),
                        focus_key="generic",
                    )
                )
                continue

            parent = list(range(n))

            def find(x: int) -> int:
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(a: int, b: int) -> None:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[rb] = ra

            for i in range(n):
                ei = sigs[i].embedding or []
                for j in range(i + 1, n):
                    ej = sigs[j].embedding or []
                    sim = _cosine_similarity(ei, ej)
                    if sim >= GENERIC_TOPIC_MERGE_THRESHOLD:
                        union(i, j)

            grouped: Dict[int, List[ReflectionSignal]] = {}
            for idx, sig in enumerate(sigs):
                grouped.setdefault(find(idx), []).append(sig)

            for members in grouped.values():
                members = sorted(members, key=lambda x: (x.timestamp, x.source_type, x.source_id))
                vectors = [s.embedding or _embed_text_local(s.embedding_text) for s in members]
                weights = [max(0.1, float(s.source_weight)) for s in members]
                centroid = _weighted_centroid(vectors, weights)
                summary = _build_topic_summary_text(category, members)
                clusters.append(
                    TopicCluster(
                        topic_key=None,
                        category=category,
                        signals=members,
                        centroid=centroid,
                        matched_reflection_id=None,
                        topic_summary_text=summary,
                        focus_key="generic",
                    )
                )

        clusters.sort(key=lambda c: (c.category, c.focus_key or "", c.signals[0].timestamp if c.signals else ""))
        return clusters


# ---------- generator ----------
class ReflectionGenerator:
    def generate_question(self, *, category: str, focus_key: str, topic_summary_text: str, signals: Sequence[ReflectionSignal]) -> str:
        # v1: deterministic short title generator
        q = _fallback_question(category, focus_key)
        return q if q.endswith("？") else (q + "？")

    def generate_answer(self, *, category: str, question: str, signals: Sequence[ReflectionSignal]) -> str:
        return _fallback_answer(category, signals)


# ---------- orchestrator ----------
class ReflectionEngine:
    def __init__(self) -> None:
        self._normalizer = ReflectionInputNormalizer()
        self._detector = ReflectionTopicDetector()
        self._generator = ReflectionGenerator()

    def build_generation_plan(
        self,
        *,
        user_id: str,
        snapshot_id: str,
        source_hash: str,
        premium_reflection_view: Dict[str, Any],
        existing_dynamic_reflections: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        sid = str(snapshot_id or "").strip()
        sh = str(source_hash or "").strip()
        if not uid:
            raise ValueError("user_id is required")
        if not sid:
            raise ValueError("snapshot_id is required")
        if not sh:
            raise ValueError("source_hash is required")

        signals = self._normalizer.normalize(premium_reflection_view)

        attached_clusters, unmatched_signals, existing_topics = self._detector.attach_to_existing_topics(
            signals,
            existing_dynamic_reflections,
        )
        new_clusters = self._detector.cluster_new_topics(unmatched_signals)

        existing_map = {t.reflection_id: t for t in existing_topics}
        represented_existing_ids: Set[str] = set()
        kept_existing_ids: Set[str] = set()
        superseded_existing_ids: Set[str] = set()
        grouped_candidates: Dict[str, List[Dict[str, Any]]] = {}

        def _cluster_latest_signal_at(cluster: TopicCluster) -> str:
            timestamps = [str(getattr(signal, "timestamp", "") or "") for signal in (cluster.signals or []) if str(getattr(signal, "timestamp", "") or "")]
            return max(timestamps) if timestamps else ""

        def _merge_signals(entries: Sequence[Dict[str, Any]]) -> List[ReflectionSignal]:
            merged: List[ReflectionSignal] = []
            seen_keys = set()
            raw_signals: List[ReflectionSignal] = []
            for entry in entries or []:
                raw_signals.extend(list(entry.get("signals") or []))
            for signal in sorted(
                raw_signals,
                key=lambda x: (
                    _parse_signal_timestamp(getattr(x, "timestamp", "") or "") or datetime.min,
                    str(getattr(x, "timestamp", "") or ""),
                    str(getattr(x, "source_type", "") or ""),
                    str(getattr(x, "source_id", "") or ""),
                ),
                reverse=True,
            ):
                sig_key = (str(signal.source_type or ""), str(signal.source_id or ""))
                if sig_key in seen_keys:
                    continue
                seen_keys.add(sig_key)
                merged.append(signal)
            return _select_latest_state_signals(merged)

        def _candidate_sort_key(entry: Dict[str, Any]) -> Tuple[int, str, int, str]:
            has_existing = 1 if str(entry.get("reflection_id") or "").strip() else 0
            latest_signal_at = str(entry.get("latest_signal_at") or "")
            signal_count = int(entry.get("signal_count") or 0)
            topic_key = str(entry.get("topic_key") or "")
            return (has_existing, latest_signal_at, signal_count, topic_key)

        def _register_cluster_candidate(cluster: TopicCluster, *, existing_topic: Optional[ExistingReflectionTopic] = None) -> None:
            question = ""
            topic_key = ""
            reflection_id = ""
            if existing_topic is not None:
                reflection_id = str(existing_topic.reflection_id or "").strip()
                topic_key = str(existing_topic.topic_key or "").strip()
                question = str(existing_topic.question or "").strip()
                if reflection_id:
                    represented_existing_ids.add(reflection_id)
            if not question:
                question = self._generator.generate_question(
                    category=cluster.category,
                    focus_key=cluster.focus_key or "generic",
                    topic_summary_text=cluster.topic_summary_text,
                    signals=cluster.signals,
                )
            q_key = compute_generated_question_q_key(question)
            grouped_candidates.setdefault(q_key, []).append(
                {
                    "q_key": q_key,
                    "question": question,
                    "category": cluster.category,
                    "focus_key": cluster.focus_key or "generic",
                    "signals": list(cluster.signals or []),
                    "topic_key": topic_key,
                    "reflection_id": reflection_id,
                    "latest_signal_at": _cluster_latest_signal_at(cluster),
                    "signal_count": len(cluster.signals or []),
                }
            )

        for cluster in attached_clusters:
            rid = str(cluster.matched_reflection_id or "").strip()
            if not rid:
                continue
            topic = existing_map[rid]
            _register_cluster_candidate(cluster, existing_topic=topic)

        for cluster in new_clusters:
            _register_cluster_candidate(cluster, existing_topic=None)

        creates: List[Dict[str, Any]] = []
        updates: List[Dict[str, Any]] = []

        for q_key, entries in grouped_candidates.items():
            if not entries:
                continue
            ordered_entries = sorted(entries, key=_candidate_sort_key, reverse=True)
            canonical = ordered_entries[0]
            for entry in ordered_entries:
                if str(entry.get("reflection_id") or "").strip():
                    canonical = entry
                    break

            question = str(canonical.get("question") or "").strip()
            category = str(canonical.get("category") or "").strip()
            focus_key = str(canonical.get("focus_key") or "").strip() or "generic"
            combined_signals = _merge_signals(ordered_entries)
            vectors = [s.embedding or _embed_text_local(s.embedding_text) for s in combined_signals]
            weights = [max(0.1, float(s.source_weight)) for s in combined_signals]
            centroid = _weighted_centroid(vectors, weights) if vectors else []
            topic_summary_text = _build_topic_summary_text(category, combined_signals)
            answer = self._generator.generate_answer(
                category=category,
                question=question,
                signals=combined_signals,
            )
            payload = {
                "q_key": q_key,
                "source_type": "generated",
                "product_type": "reflection_dynamic",
                "required_plan_tier": DEFAULT_REQUIRED_PLAN_TIER,
                "scope": DEFAULT_SCOPE,
                "status": "draft",
                "category": category,
                "focus_key": focus_key,
                "question": question,
                "answer": answer,
                "source_snapshot_id": sid,
                "source_hash": sh,
                "source_refs": _build_source_refs(combined_signals),
                "topic_summary_text": topic_summary_text,
                "topic_embedding": [round(float(x), 6) for x in centroid],
            }

            canonical_reflection_id = str(canonical.get("reflection_id") or "").strip()
            canonical_topic_key = str(canonical.get("topic_key") or "").strip()
            if canonical_reflection_id:
                kept_existing_ids.add(canonical_reflection_id)
                updates.append(
                    {
                        "reflection_id": canonical_reflection_id,
                        "topic_key": canonical_topic_key,
                        **payload,
                    }
                )
            else:
                topic_key = _make_topic_key(
                    user_id=uid,
                    category=category,
                    focus_key=focus_key,
                    topic_summary_text=topic_summary_text or question,
                )
                creates.append(
                    {
                        "topic_key": topic_key,
                        **payload,
                    }
                )

            for entry in ordered_entries:
                rid = str(entry.get("reflection_id") or "").strip()
                if rid and rid != canonical_reflection_id:
                    superseded_existing_ids.add(rid)

        deactivates: List[Dict[str, Any]] = []
        deactivated_ids: Set[str] = set()

        for rid in sorted(superseded_existing_ids):
            if not rid or rid in deactivated_ids:
                continue
            topic = existing_map.get(rid)
            deactivated_ids.add(rid)
            deactivates.append(
                {
                    "reflection_id": rid,
                    "topic_key": str((topic.topic_key if topic else "") or "").strip(),
                    "reason": "superseded_by_latest_q_key",
                    "source_snapshot_id": sid,
                    "source_hash": sh,
                }
            )

        for topic in existing_topics:
            if topic.reflection_id in kept_existing_ids or topic.reflection_id in deactivated_ids:
                continue
            if topic.reflection_id in represented_existing_ids:
                continue
            deactivated_ids.add(topic.reflection_id)
            deactivates.append(
                {
                    "reflection_id": topic.reflection_id,
                    "topic_key": topic.topic_key,
                    "reason": "topic_missing_from_snapshot",
                    "source_snapshot_id": sid,
                    "source_hash": sh,
                }
            )

        creates.sort(key=lambda x: (str(x.get("q_key") or ""), str(x.get("question") or ""), str(x.get("topic_key") or "")))
        updates.sort(key=lambda x: (str(x.get("q_key") or ""), str(x.get("question") or ""), str(x.get("reflection_id") or "")))
        deactivates.sort(key=lambda x: (str(x.get("reason") or ""), str(x.get("topic_key") or ""), str(x.get("reflection_id") or "")))

        return {
            "user_id": uid,
            "snapshot_id": sid,
            "source_hash": sh,
            "creates": creates,
            "updates": updates,
            "deactivates": deactivates,
            "stats": {
                "input_items": len(signals),
                "attached_topic_count": len(attached_clusters),
                "new_topic_count": len(new_clusters),
                "grouped_question_count": len(grouped_candidates),
                "collapsed_same_question_count": sum(max(0, len(entries) - 1) for entries in grouped_candidates.values()),
                "create_count": len(creates),
                "update_count": len(updates),
                "deactivate_count": len(deactivates),
                "existing_topic_count": len(existing_topics),
            },
        }

def build_generation_plan(
    *,
    user_id: str,
    snapshot_id: str,
    source_hash: str,
    premium_reflection_view: Dict[str, Any],
    existing_dynamic_reflections: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """Top-level convenience wrapper."""
    engine = ReflectionEngine()
    return engine.build_generation_plan(
        user_id=user_id,
        snapshot_id=snapshot_id,
        source_hash=source_hash,
        premium_reflection_view=premium_reflection_view,
        existing_dynamic_reflections=existing_dynamic_reflections,
    )


__all__ = [
    "ReflectionSignal",
    "ExistingReflectionTopic",
    "TopicCluster",
    "ReflectionInputNormalizer",
    "ReflectionTopicDetector",
    "ReflectionGenerator",
    "ReflectionEngine",
    "build_generation_plan",
]
