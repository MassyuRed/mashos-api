# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cocolon internal limited Composer client for EmlisAI B-plan.

Phase8 improves the already-connected B-plan Composer by making source-grounded
PhraseUnit / ObservationProfile / SentencePlan decisions before creating text.
It does not call external AI and does not use public knowledge.
"""

from dataclasses import dataclass
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from emlis_ai_limited_sentence_quality_guard import (
    detect_phase8_profile,
    judge_limited_sentence_quality,
    phase8_primary_role_for_text,
    phase8_role_meta,
    phase8_roles_for_text,
)
from cocolon_text_generation_core.adapters.emlis_observation_composer import (
    attach_core_evaluation_meta,
    core_rejection_reason,
    evaluate_emlis_observation_candidate,
)

_RESPONSE_SCHEMA_VERSION = "emlis.composer.response.v1"
_COMPOSER_MODEL = "cocolon_limited_composer.v1"
_GENERATION_METHOD = "scoped_graph_evidence_composer"
_GENERATION_SCOPE = "scoped_graph_only"
_ALLOWED_SOURCE = "ai_generated"
_UNAVAILABLE_SOURCE = "unavailable"
_MIN_BODY_LINES = 2
_MAX_BODY_LINES = 4

_SPACE_RE = re.compile(r"\s+")
_SENTENCE_END_RE = re.compile(r"[。！？!?]+$")
_PUNCT_TRIM = " 　、,。.!！?？『』\"'"
_EMOTION_LABELS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解", "恐れ", "焦り"}
_TEXT_SOURCE_FIELDS = {"memo", "memo_action", "text", "free_text"}
_SKIP_SOURCE_FIELDS = {"emotion_details", "emotions", "category"}
_SKIP_DETECTED_TYPES = {"emotion"}
_GROUP_KEYS = ("pressure_sources", "limit_signals", "self_awareness", "value_or_strength_signals")

_FORBIDDEN_SURFACES = (
    "そこには",
    "もありました",
    "も含まれていました",
    "受け取りました",
    "と思います",
    "として見ています",
    "一緒に見ます",
    "今の私は",
    "あなたは",
    "あなたの",
    "あなたが",
    "あなたに",
    "入力全体では",
    "言葉の流れには",
    "外からは見えにくい緊張",
    "まだ決めきれない揺れ",
    "急いで片づけず",
    "がつながっています",
    "同じ中にあります",
)
_MARKER_NAMES = (
    "_line_primary",
    "_line_pressure",
    "_line_limit",
    "_line_closing",
    "closing_template",
    "role_template",
    "static_observation_text",
    "fallback_observation",
)


@dataclass(frozen=True)
class EmlisPhraseUnit:
    phrase_unit_id: str
    evidence_span_id: str
    raw_text: str
    compressed_text: str
    role: str
    polarity: str = "neutral"
    must_keep: bool = False
    quality_flags: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ObservationProfile:
    profile_key: str
    required_roles: Tuple[str, ...]
    min_lines: int = 2
    max_lines: int = 4
    coverage_scope: str = "partial_observation"


@dataclass(frozen=True)
class SentencePlan:
    line_role: str
    phrase_unit_ids: Tuple[str, ...]
    relation_type: str
    max_chars: int = 110
    must_include: bool = True


@dataclass(frozen=True)
class SentenceSurfaceContext:
    line_role: str
    relation_type: str
    phrase_count: int
    polarity: str
    sequence_order: int


@dataclass(frozen=True)
class SentenceSurfaceParts:
    opener: str = ""
    joiner: str = "や、"
    particle: str = "が"
    predicate: str = "書かれています"
    max_phrases: int = 2


class CocolonLimitedComposerClient:
    """Generate a limited Emlis candidate from a scoped payload."""

    composer_model = _COMPOSER_MODEL

    def generate(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(payload, Mapping):
            return _unavailable_response("limited_composer_invalid_payload")

        scope = _scope_meta(payload)
        coverage_scope = _clean(scope.get("coverage_scope")) or _coverage_scope(_graph(payload))
        if _clean(scope.get("scope_status")) and _clean(scope.get("scope_status")) != "eligible":
            return _unavailable_response("limited_scope_not_eligible", coverage_scope=coverage_scope)

        graph = _graph(payload)
        if not graph:
            return _unavailable_response("limited_composer_missing_graph", coverage_scope=coverage_scope)
        if list(graph.get("safety_boundaries") or []):
            return _unavailable_response("limited_composer_safety_boundary", coverage_scope=coverage_scope)
        if list(graph.get("missing_information") or []):
            return _unavailable_response("limited_composer_missing_information", coverage_scope=coverage_scope)

        evidence_items = [item for item in list(payload.get("evidence_spans") or []) if isinstance(item, Mapping)]
        evidence_by_id = _evidence_by_id(evidence_items)
        if not evidence_by_id:
            return _unavailable_response("limited_composer_missing_evidence", coverage_scope=coverage_scope)

        profile_key = detect_phase8_profile(evidence_items)
        if profile_key == "short_ambiguous_low_evidence":
            return _unavailable_response("limited_composer_short_ambiguous_low_evidence", coverage_scope="current_input_core", profile_key=profile_key)

        allowed_evidence_ids = _allowed_evidence_ids_from_graph(graph)
        if profile_key in {"", "unknown", "current_input_core"}:
            return _generate_current_input_core_candidate(
                payload=payload,
                graph=graph,
                evidence_items=evidence_items,
                evidence_by_id=evidence_by_id,
                allowed_evidence_ids=allowed_evidence_ids,
                source_profile_key=profile_key or "unknown",
            )

        allowed_evidence_ids.update(_phase8_profile_evidence_ids(profile_key, evidence_items))
        generation_evidence_items = [
            item
            for item in evidence_items
            if not allowed_evidence_ids or str(item.get("span_id") or "").strip() in allowed_evidence_ids
        ]
        phrase_units = _build_phrase_units(generation_evidence_items)
        if not phrase_units:
            return _unavailable_response("limited_composer_missing_phrase_units", coverage_scope=coverage_scope, profile_key=profile_key)
        profile = _profile_for_key(profile_key)
        missing_roles = [role for role in profile.required_roles if not _units_for_role(phrase_units, role)]
        if missing_roles:
            return _unavailable_response(
                "limited_composer_required_role_missing",
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={"missing_roles": missing_roles},
            )

        plans = _sentence_plans_for_profile(profile=profile, units=phrase_units)
        lines, used_unit_ids, sentence_tail_keys = _render_sentence_plans(payload=payload, profile=profile, plans=plans, units=phrase_units)
        if not lines:
            return _unavailable_response("limited_composer_empty_candidate", coverage_scope=coverage_scope, profile_key=profile_key)

        min_body, max_body = _body_limits(scope, profile=profile)
        greeting_count = 1 if lines and "Emlis" in lines[0] else 0
        body_lines = lines[greeting_count:][:max_body]
        lines = lines[:greeting_count] + body_lines
        if len(body_lines) < min_body:
            return _unavailable_response("limited_composer_minimum_body_not_met", coverage_scope=coverage_scope, profile_key=profile_key)

        comment_text = "\n".join(line for line in lines if line).strip()
        if not comment_text:
            return _unavailable_response("limited_composer_empty_candidate", coverage_scope=coverage_scope, profile_key=profile_key)

        matched_forbidden = _matched_forbidden_surfaces(payload=payload, text=comment_text)
        if matched_forbidden:
            return _unavailable_response("limited_composer_forbidden_surface", matched_forbidden=matched_forbidden, coverage_scope=coverage_scope, profile_key=profile_key)

        unit_by_id = {unit.phrase_unit_id: unit for unit in phrase_units}
        used_evidence_ids = _dedupe(unit_by_id[unit_id].evidence_span_id for unit_id in used_unit_ids if unit_id in unit_by_id)
        quality_report = judge_limited_sentence_quality(
            comment_text=comment_text,
            evidence_spans=_evidence_objects_for_quality(generation_evidence_items),
            profile_key=profile_key,
            used_evidence_span_ids=used_evidence_ids,
            composer_meta={"profile_key": profile_key},
        )
        if not bool(quality_report.get("passed")):
            return _unavailable_response(
                "limited_composer_sentence_quality_rejected",
                matched_forbidden=list(quality_report.get("matched_fragments") or quality_report.get("matched_surfaces") or []),
                coverage_scope=coverage_scope,
                profile_key=profile_key,
                extra_meta={"phase8_quality": quality_report},
            )

        used_evidence_ids = [span_id for span_id in used_evidence_ids if span_id in evidence_by_id]
        if not used_evidence_ids:
            return _unavailable_response("limited_composer_no_used_evidence", coverage_scope=coverage_scope, profile_key=profile_key)

        response = {
            "schema_version": _RESPONSE_SCHEMA_VERSION,
            "response_schema_version": _RESPONSE_SCHEMA_VERSION,
            "composer_source": _ALLOWED_SOURCE,
            "status": "generated",
            "composer_model": _COMPOSER_MODEL,
            "generation_method": _GENERATION_METHOD,
            "generation_scope": _GENERATION_SCOPE,
            "fixed_string_renderer_used": False,
            "coverage_scope": profile.coverage_scope or coverage_scope,
            "comment_text": comment_text,
            "used_evidence_span_ids": used_evidence_ids,
            "used_claim_ids": _used_claim_ids(graph),
            "used_relation_ids": _used_relation_ids(graph),
            "confidence": _confidence(profile=profile, phrase_units=phrase_units, used_unit_ids=used_unit_ids),
            "composer_meta": {
                "limited_composer": True,
                "generation_scope": _GENERATION_SCOPE,
                "external_ai_used": False,
                "phase8_quality_path": True,
                "profile_key": profile_key,
                "required_roles": list(profile.required_roles),
                "covered_roles": _dedupe(unit.role for unit in phrase_units if unit.phrase_unit_id in set(used_unit_ids)),
                "body_line_count": len(body_lines),
                "phrase_unit_count": len(phrase_units),
                "sentence_plan_count": len(plans),
                "sentence_surface_mode": "componentized",
                "sentence_tail_keys": sentence_tail_keys,
                "allowed_evidence_span_ids": sorted(allowed_evidence_ids),
                "phase8_quality": quality_report,
            },
        }
        return _core_checked_response(
            response=response,
            payload=payload,
            evidence_items=generation_evidence_items,
            phrase_units=phrase_units,
            sentence_plans=plans,
            used_unit_ids=used_unit_ids,
            coverage_scope=profile.coverage_scope or coverage_scope,
            profile_key=profile_key,
        )


def _scope_meta(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("limited_observation_scope", "limited_scope", "scope_meta", "scope"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _graph(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    value = payload.get("observation_graph")
    return value if isinstance(value, Mapping) else {}


def _unavailable_response(
    reason: str,
    *,
    matched_forbidden: Sequence[str] | None = None,
    coverage_scope: str = "",
    profile_key: str = "",
    extra_meta: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    reasons = [str(reason or "limited_composer_unavailable").strip()]
    if matched_forbidden:
        reasons.append("limited_composer_forbidden_or_quality_surface")
    meta: Dict[str, Any] = {
        "limited_composer": True,
        "generation_scope": _GENERATION_SCOPE,
        "external_ai_used": False,
        "phase8_quality_path": True,
    }
    if profile_key:
        meta["profile_key"] = profile_key
    if isinstance(extra_meta, Mapping):
        meta.update(dict(extra_meta))
    return {
        "schema_version": _RESPONSE_SCHEMA_VERSION,
        "response_schema_version": _RESPONSE_SCHEMA_VERSION,
        "composer_source": _UNAVAILABLE_SOURCE,
        "status": "unavailable",
        "composer_model": _COMPOSER_MODEL,
        "generation_method": _GENERATION_METHOD,
        "generation_scope": _GENERATION_SCOPE,
        "fixed_string_renderer_used": False,
        "coverage_scope": coverage_scope or "current_input_core",
        "comment_text": "",
        "used_evidence_span_ids": [],
        "used_claim_ids": [],
        "used_relation_ids": [],
        "confidence": 0.0,
        "rejection_reasons": _dedupe(reasons),
        "matched_forbidden_surfaces": list(matched_forbidden or []),
        "composer_meta": meta,
    }


def _clean(value: Any, *, limit: int = 120) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()
    text = _SENTENCE_END_RE.sub("", text).strip(_PUNCT_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM)
    return text


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r『』「」（）()\[\]【】]", "", str(value or ""))


def _dedupe(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        item = str(value or "").strip()
        if item and item not in out:
            out.append(item)
    return out




def _allowed_evidence_ids_from_graph(graph: Mapping[str, Any]) -> set[str]:
    ids: set[str] = set()

    def add_values(values: Any) -> None:
        if isinstance(values, (list, tuple, set)):
            for value in values:
                item = str(value or "").strip()
                if item:
                    ids.add(item)
        else:
            item = str(values or "").strip()
            if item:
                ids.add(item)

    def add_claim(claim: Any) -> None:
        if isinstance(claim, Mapping):
            add_values(claim.get("evidence_span_ids") or claim.get("evidence_ids") or [])

    add_claim(graph.get("primary_state"))
    for group_key in ("pressure_sources", "limit_signals", "self_awareness", "value_or_strength_signals"):
        for claim in list(graph.get(group_key) or []):
            add_claim(claim)
    for edge in list(graph.get("core_tensions") or []):
        if isinstance(edge, Mapping):
            add_values(edge.get("evidence_span_ids") or edge.get("evidence_ids") or [])
    return ids

def _evidence_by_id(items: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    out: Dict[str, Mapping[str, Any]] = {}
    for item in items:
        span_id = str(item.get("span_id") or "").strip()
        if span_id:
            out[span_id] = item
    return out


def _source_field(item: Mapping[str, Any]) -> str:
    return str(item.get("source_field") or "").strip()


def _detected_type(item: Mapping[str, Any]) -> str:
    return str(item.get("detected_type") or "").strip()


def _raw_text(item: Mapping[str, Any]) -> str:
    return _clean(item.get("raw_text"), limit=240)


def _skip_evidence(item: Mapping[str, Any]) -> bool:
    raw = _raw_text(item)
    source = _source_field(item)
    detected = _detected_type(item)
    if not raw or raw in _EMOTION_LABELS:
        return True
    if source and source not in _TEXT_SOURCE_FIELDS:
        return True
    if detected in _SKIP_DETECTED_TYPES or source in _SKIP_SOURCE_FIELDS:
        return True
    if detected == "relation_marker" and _compact(raw) in {"でも"}:
        return True
    return False


def _role_for_text(text: str, detected_type: str) -> Tuple[str, str, bool]:
    return phase8_primary_role_for_text(text, detected_type)


def _compress_text(raw: str, role: str) -> str:
    """Build a role-scoped PhraseUnit from the evidence span.

    Phase8-R3 keeps PhraseUnit shaping generic: the branch is role + semantic
    cue based, not a fixed ``input sentence -> output phrase`` replacement map.
    """

    text = _clean(raw, limit=200)
    compact = _compact(text)
    if not text:
        return ""

    def has(*terms: str) -> bool:
        return any(term and (term in text or term in compact) for term in terms)

    def has_all(*terms: str) -> bool:
        return all(term and (term in text or term in compact) for term in terms)

    if role == "positive_state":
        if has_all("散歩", "落ち着"):
            return "散歩して落ち着いたこと"
        if has("友達"):
            return "友達と話せた楽しさ"
        if has("元気"):
            return "少し元気になれた感覚" if has("少し") else "元気になれた感覚"
        if has("笑え"):
            return "笑えたこと"
        if has("ほっと"):
            return "ほっとした感覚"
        if has("安心"):
            return "安心したこと"
        if has("楽しか"):
            return "楽しかったこと"

    if role == "anxiety_return":
        if has_all("夜", "失敗", "不安"):
            return "夜に戻った失敗への不安"
        if has_all("一人", "不安"):
            return "一人になった時の不安"
        if has_all("静か", "不安"):
            return "静かになった後の不安"
        if has("不安"):
            return "戻ってきた不安"
        if has("落ちる"):
            return "落ちる感覚"

    if role == "fall_contrast":
        if has("落差"):
            return "ほっとしていた分の落差" if has("ほっと") else "落差の大きさ"
        if has("落ちる"):
            return "楽しかった後に落ちる感覚"

    if role == "anger_surface":
        if has_all("返し方", "雑"):
            return "返し方の雑さにむっとしたこと" if has("むっと", "ムッと") else "返し方の雑さへの怒り"
        if has("言い方"):
            return "きつい言い方への怒り"
        if has("腹が立"):
            return "腹が立ったこと"
        if has("怒"):
            return "怒り"

    if role == "unfairness":
        if has("軽く扱"):
            return "軽く扱われたこと"
        if has("丁寧"):
            return "丁寧に伝えようとしていたこと"
        if has("ちゃんと考", "考えて話"):
            return "ちゃんと考えて話していたこと"
        if has("されなきゃ"):
            return "きつい言い方をされる分からなさ"

    if role == "hurt_core":
        if has("大事に扱"):
            return "大事に扱われなかったしんどさ"
        if has("軽く扱"):
            return "軽く扱われたしんどさ"
        if has("傷つ"):
            return "傷ついたしんどさ"
        if has("しんど"):
            return "しんどさ"

    if role == "withdrawal":
        if has_all("説明", "気力"):
            return "説明する気力がなくなっていること"
        if has("面倒"):
            return "話すのが面倒になっていること"
        if has("距離"):
            return "距離を置きたくなること"

    if role == "known_action":
        if has("見えて"):
            return "やることは見えている流れ"
        if has("分か"):
            return "やることは分かっている流れ"
        if has("そんなの"):
            return "分かっている自覚"

    if role == "anticipation_loop":
        if has_all("考えすぎ", "動け"):
            return "考えすぎて動けなくなる流れ"
        if has("手が止ま"):
            return "考えると手が止まる流れ"
        if has("止まら", "先のこと"):
            return "考え始めると止まらなくなる流れ"
        if has("進めない"):
            return "進めない流れ"

    if role == "perfection_fear":
        if has_all("失敗", "ちゃんとできない"):
            return "失敗やちゃんとできないため進めない怖さ" if has("進めない") else "失敗やちゃんとできないことへの怖さ"
        if has("失敗"):
            return "失敗への怖さ"
        if has("ちゃんとできない"):
            return "ちゃんとできない怖さ"
        if has("完璧"):
            return "完璧にやろうとする怖さ"
        if has("適当"):
            return "適当にやる怖さ"

    if role == "small_action":
        if has("洗い物"):
            return "洗い物を少し終えたこと"
        if has("片付け"):
            return "片付けられたこと"
        if has("台所", "整"):
            return "台所が整ったこと"
        if has("進め"):
            return "少し進められたこと"

    if role == "relieved_weight":
        if has_all("台所", "落ち着"):
            return "台所が整って気持ちが落ち着いた感覚"
        if has("気持ちが軽"):
            return "気持ちが軽くなった感覚"
        if has("気持ちが落ち着", "落ち着"):
            return "気持ちが落ち着いた感覚"
        if has("ほっと"):
            return "ほっとした感覚"
        if has("気にな"):
            return "気になっていた場所に触れられた感覚"

    if role == "achievement":
        if has("ちゃんとでき"):
            return "ちゃんとできた嬉しさ"
        if has_all("進め", "ほっと"):
            return "少し進められてほっとした感覚"
        if has("嬉し"):
            return "嬉しさ"
        if has("ほっと"):
            return "ほっとした感覚"

    if role == "wish_to_rely":
        if has("相談したい"):
            return "相談したい気持ち"
        if has("助けを借りたい"):
            return "助けを借りたい気持ち"
        if has("頼りたい", "頼った"):
            return "頼りたい気持ち"
        if has("話したい"):
            return "話したい気持ち"

    if role == "burden_fear":
        if has_all("時間", "奪"):
            return "相手の時間を奪う怖さ"
        if has("迷惑"):
            return "迷惑だと思われる怖さ"
        if has("困らせ"):
            return "助けを借りたいのに困らせそうで怖いこと" if has("助け") else "困らせそうな怖さ"
        if has("言い出せない"):
            return "言い出せない怖さ"

    if role == "rejection_fear":
        if has("嫌われ", "重い"):
            parts: List[str] = []
            if has("嫌われ"):
                parts.append("嫌われる怖さ")
            if has("重い"):
                parts.append("重いと思われる怖さ")
            return "や".join(parts)
        if has("困らせ"):
            return "困らせそうな怖さ"
        if has("怖"):
            return "怖さ"

    if role == "limit":
        if has_all("考え続け", "つら"):
            return "一人で考え続けるつらさ" if has("一人") else "考え続けるつらさ"
        if has_all("抱え", "限界"):
            return "一人で抱える限界"
        if has("逃げ出"):
            return "逃げ出したくなる感覚"
        if has("投げ出"):
            return "全部投げ出したくなる時" if has("全部") else "投げ出したくなる時"
        if has("限界"):
            return "限界"
        if has("つら"):
            return "つらさ"
        if has("何もしたくない"):
            return "何もしたくない感覚"

    if role == "safe_home":
        if has("リラックス"):
            return "家にいてリラックスできること" if has("家", "お家", "おうち") else "リラックスできること"
        if has("安心", "自分のペース", "ペース"):
            if has("安心") and has("ペース"):
                return "安心して自分のペースで過ごせること"
            return "安心できること"
        if has("優先", "整え"):
            return "自分を優先して整えられること"
        if has("家", "お家", "おうち"):
            return "家で落ち着けること"

    if role == "reality_damage":
        if has("不便"):
            return "生活の不便さが重くなること" if has("重く") else "今の生活の不便さ"
        if has("ダメージ"):
            return "現実と向き合う時の大きなダメージ"
        if has("現実"):
            return "現実へ戻ること"
        if has("移動", "準備"):
            return "移動や準備の負担"

    if role == "ordinary_life_wish":
        if has("いつも通り"):
            return "いつも通りに過ごしたい気持ち"
        if has("生活したい", "普通に"):
            return "普通に生活したい気持ち"

    if role == "worsening_risk":
        if has_all("体調", "崩"):
            return "体調が崩れそうな怖さ"
        if has("悪化"):
            return "悪化するリスク"

    if role == "low_energy":
        if has("だるい"):
            return "だるさ"
        if has("何もしたくない"):
            return "何もしたくない感覚"

    cleaned = re.sub(r"^(?:今日は|今日|また|でも|本当は|たぶん|もう|このまま|さっき)\s*", "", text).strip(_PUNCT_TRIM)
    cleaned = re.sub(r"(?:けど|だけど|でも|のに|から|なら|すると|したら|を|が|で)$", "", cleaned).strip(_PUNCT_TRIM)
    if not cleaned:
        return ""
    if cleaned.endswith(("こと", "気持ち", "感覚", "怖さ", "しんどさ", "限界", "不安", "流れ", "つらさ")):
        return cleaned
    suffix = "気持ち" if role in {"wish_to_rely", "ordinary_life_wish"} else "こと"
    return f"{cleaned}{suffix}"

def _quality_flags(text: str) -> Tuple[str, ...]:
    flags: List[str] = []
    if re.search(r"(なんであ|考え始め|現実と|自分のことを|普通に)$", text):
        flags.append("unfinished_phrase")
    if len(_compact(text)) > 64:
        flags.append("too_long_quote")
    if re.search(r"[をがにはへで]$", text):
        flags.append("orphan_particle")
    return tuple(flags)





def _text_evidence_ids(items: Sequence[Mapping[str, Any]]) -> set[str]:
    ids: set[str] = set()
    for item in items:
        if _skip_evidence(item):
            continue
        span_id = str(item.get("span_id") or "").strip()
        if span_id:
            ids.add(span_id)
    return ids


def _generation_items_for_allowed_ids(items: Sequence[Mapping[str, Any]], allowed_ids: set[str]) -> List[Mapping[str, Any]]:
    if not allowed_ids:
        return [item for item in items if not _skip_evidence(item)]
    return [
        item
        for item in items
        if not _skip_evidence(item) and str(item.get("span_id") or "").strip() in allowed_ids
    ]


def _shallow_polarity(text: str) -> str:
    compact = _compact(text)
    negative = any(term in compact for term in ("疲れ", "不安", "怖", "失敗", "つら", "しんど", "切れて", "詰ま", "重く", "困", "迷惑"))
    positive = any(term in compact for term in ("落ち着", "整え", "終え", "進め", "安心", "ほっと", "嬉し", "楽しか", "できた"))
    if negative and positive:
        return "mixed"
    if negative:
        return "negative"
    if positive:
        return "positive"
    return "neutral"


def _generic_shallow_phrase(raw: str, detected_type: str = "") -> str:
    text = _clean(raw, limit=160)
    compact = _compact(text)
    if not text:
        return ""

    def has(*terms: str) -> bool:
        return any(term and term in compact for term in terms)

    if has("仕事") and has("疲れ"):
        return "仕事で疲れたこと"
    if has("予定") and has("集中"):
        return "予定が詰まって集中が切れていたこと"
    if has("資料") and has("頭がいっぱい"):
        return "資料を直して頭がいっぱいだったこと"
    if has("お茶") and has("落ち着"):
        return "お茶を飲んで落ち着いたこと"
    if has("机") and has("整え"):
        return "少しだけ机を整えたこと" if has("少し") else "机を整えたこと"
    if has("失敗") and has("不安"):
        return "失敗しそうで不安なこと"
    if has("疲れ"):
        return "疲れたこと"
    if has("不安"):
        return "不安"
    if has("つら"):
        return "つらさ"

    parts = [
        _clean(part, limit=70)
        for part in re.split(r"(?:[、,]|けれど|けど|だけど|でも|のに|なら|したら|すると|て、|いて、|と、)", text)
    ]
    parts = [
        re.sub(r"^(?:今日は|今日|朝から|夜になって|昼過ぎには|また|もう|それでも|本当は|このまま|さっき|少しだけ)\s*", "", part).strip(_PUNCT_TRIM)
        for part in parts
        if part.strip(_PUNCT_TRIM)
    ]
    if not parts:
        return ""

    priority_terms = ("疲", "不安", "怖", "失敗", "つら", "しんど", "切れ", "落ち着", "整え", "進め", "終え", "相談", "助け", "困")
    parts.sort(key=lambda part: (0 if any(term in _compact(part) for term in priority_terms) else 1, len(part)))
    chosen = parts[0].strip(_PUNCT_TRIM)
    chosen = re.sub(r"^(?:今日は|今日|朝から|夜になって|昼過ぎには|また|もう|それでも|本当は|このまま|さっき)\s*", "", chosen).strip(_PUNCT_TRIM)
    chosen = re.sub(r"(?:を|が|で|に|へ|は|も|と|から|なら)$", "", chosen).strip(_PUNCT_TRIM)
    if not chosen:
        return ""
    if chosen.endswith(("こと", "気持ち", "感覚", "怖さ", "不安", "つらさ", "しんどさ", "限界")):
        return chosen
    if chosen.endswith(("たい", "したい")):
        return f"{chosen}気持ち"
    return f"{chosen}こと"


def _role_phrase_safe_for_shallow(phrase: str, raw: str) -> bool:
    phrase_compact = _compact(phrase)
    raw_compact = _compact(raw)
    if not phrase_compact or not raw_compact:
        return False
    for term in ("優先", "ペース", "リラックス", "家", "お家", "生活", "悪化", "体調", "相談", "助け", "頼り", "迷惑", "嫌われ", "重い", "限界"):
        if term in phrase_compact and term not in raw_compact:
            return False
    return True


def _add_shallow_unit(
    units: List[EmlisPhraseUnit],
    *,
    span_id: str,
    raw: str,
    phrase: str,
    role: str,
    polarity: str,
) -> None:
    compressed = _clean(phrase, limit=90)
    compact = _compact(compressed)
    if not compressed or compressed in _EMOTION_LABELS or len(compact) < 3:
        return
    for unit in units:
        existing = _compact(unit.compressed_text)
        if compact == existing or (len(compact) >= 6 and compact in existing) or (len(existing) >= 6 and existing in compact):
            return
    flags = _quality_flags(compressed)
    if "unfinished_phrase" in flags or "orphan_particle" in flags or "too_long_quote" in flags:
        return
    units.append(
        EmlisPhraseUnit(
            phrase_unit_id=f"pu{len(units)+1}",
            evidence_span_id=span_id,
            raw_text=raw,
            compressed_text=compressed,
            role=role or "current_input_core",
            polarity=polarity or _shallow_polarity(compressed),
            must_keep=True,
            quality_flags=flags,
        )
    )


def _build_current_input_core_phrase_units(evidence_items: Sequence[Mapping[str, Any]]) -> List[EmlisPhraseUnit]:
    units: List[EmlisPhraseUnit] = []
    role_priority = (
        "positive_state",
        "relieved_weight",
        "achievement",
        "small_action",
        "anxiety_return",
        "perfection_fear",
        "anticipation_loop",
        "burden_fear",
        "rejection_fear",
        "limit",
        "known_action",
        "wish_to_rely",
        "hurt_core",
        "anger_surface",
        "safe_home",
        "reality_damage",
        "ordinary_life_wish",
        "worsening_risk",
    )
    for item in evidence_items:
        if _skip_evidence(item):
            continue
        raw = _raw_text(item)
        span_id = str(item.get("span_id") or f"s{len(units)+1}").strip()
        if not raw or not span_id:
            continue
        generic = _generic_shallow_phrase(raw, _detected_type(item))
        _add_shallow_unit(
            units,
            span_id=span_id,
            raw=raw,
            phrase=generic,
            role="current_input_core",
            polarity=_shallow_polarity(generic or raw),
        )
        roles = set(phase8_roles_for_text(raw, _detected_type(item)))
        for role in role_priority:
            if role not in roles:
                continue
            if role in {"safe_home", "ordinary_life_wish", "reality_damage", "worsening_risk"} and generic:
                # In the shallow path, prefer the direct source phrase over a broad Phase8 profile phrase.
                continue
            compressed = _compress_text(raw, role)
            if not _role_phrase_safe_for_shallow(compressed, raw):
                continue
            polarity, must_keep = phase8_role_meta(role)
            _add_shallow_unit(
                units,
                span_id=span_id,
                raw=raw,
                phrase=compressed,
                role=role,
                polarity=polarity,
            )
    return units


def _select_current_input_core_units(units: Sequence[EmlisPhraseUnit], *, max_units: int = 3) -> List[EmlisPhraseUnit]:
    selected: List[EmlisPhraseUnit] = []
    if not units:
        return selected

    first = units[0]
    selected.append(first)

    for unit in units[1:]:
        if unit.evidence_span_id == first.evidence_span_id and unit.polarity != first.polarity:
            selected.append(unit)
            break
        if len(selected) >= max_units - 1:
            break

    evidence_seen = {unit.evidence_span_id for unit in selected}
    for unit in units[1:]:
        if unit.evidence_span_id not in evidence_seen:
            selected.append(unit)
            evidence_seen.add(unit.evidence_span_id)
        if len(selected) >= max_units:
            return selected

    for unit in units[1:]:
        if unit not in selected:
            selected.append(unit)
        if len(selected) >= max_units:
            return selected
    return selected


def _current_input_core_relation(previous: EmlisPhraseUnit, current: EmlisPhraseUnit) -> str:
    if current.polarity == "positive":
        return "continuation"
    if previous.polarity != current.polarity and {previous.polarity, current.polarity}.issubset({"positive", "negative", "mixed"}):
        return "contrast"
    return "coexistence"


def _choose_tail(parts: Sequence[Tuple[str, str, str]], used_tail_keys: Sequence[str]) -> Tuple[str, str, str]:
    used = set(used_tail_keys or [])
    for particle, tail, key in parts:
        if key not in used:
            return particle, tail, key
    return parts[0] if parts else ("が", "書かれています", "written")


def _shallow_tail_options(relation: str) -> Tuple[Tuple[str, str, str], ...]:
    if relation == "contrast":
        return (("も", "重なっています", "stack"), ("も", "書かれています", "written"))
    if relation == "continuation":
        return (("も", "続いています", "continue"), ("も", "書かれています", "written"))
    return (("も", "書かれています", "written"), ("も", "重なっています", "stack"))


def _render_current_input_core_lines(*, payload: Mapping[str, Any], units: Sequence[EmlisPhraseUnit]) -> Tuple[List[str], List[str]]:
    selected = _select_current_input_core_units(units, max_units=3)
    if len(selected) < 2:
        return [], []

    lines: List[str] = []
    used: List[str] = []
    tail_keys: List[str] = ["center"]
    greeting = _greeting(payload)
    if greeting:
        lines.append(greeting)

    first = selected[0]
    first_line = _finish(f"{first.compressed_text}が中心として書かれています")
    if first_line:
        lines.append(_trim_line(first_line, limit=100))
        used.append(first.phrase_unit_id)

    previous = first
    for unit in selected[1:]:
        relation = _current_input_core_relation(previous, unit)
        prefix = _shallow_opener(relation=relation, body_index=len([line for line in lines if "Emlis" not in line]), total=len(selected))
        particle, tail, tail_key = _choose_tail(_shallow_tail_options(relation), tail_keys)
        raw_line = f"{prefix}{unit.compressed_text}{particle}{tail}"
        line = _trim_line(_finish(raw_line), limit=100)
        if line and line not in lines:
            lines.append(line)
            used.append(unit.phrase_unit_id)
            tail_keys.append(tail_key)
        previous = unit
        if len(lines) >= 4:
            break
    body_count = len([line for line in lines if "Emlis" not in line])
    if body_count < 2:
        return [], []
    return lines, _dedupe(used)


def _shallow_opener(*, relation: str, body_index: int, total: int) -> str:
    if relation == "contrast":
        return "一方で、"
    if relation == "continuation":
        return "一方で、" if total == 2 else "その中でも、"
    return "その中でも、"


def _shallow_confidence(*, used_unit_ids: Sequence[str], units: Sequence[EmlisPhraseUnit]) -> float:
    used_count = len(set(used_unit_ids))
    used_evidence_count = len({unit.evidence_span_id for unit in units if unit.phrase_unit_id in set(used_unit_ids)})
    base = 0.58 + min(0.16, 0.04 * used_count) + min(0.08, 0.04 * used_evidence_count)
    return round(max(0.0, min(0.78, base)), 3)


def _generate_current_input_core_candidate(
    *,
    payload: Mapping[str, Any],
    graph: Mapping[str, Any],
    evidence_items: Sequence[Mapping[str, Any]],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    allowed_evidence_ids: set[str],
    source_profile_key: str,
) -> Mapping[str, Any]:
    profile_key = "current_input_core"
    if not allowed_evidence_ids:
        allowed_evidence_ids = _text_evidence_ids(evidence_items)
    generation_evidence_items = _generation_items_for_allowed_ids(evidence_items, allowed_evidence_ids)
    phrase_units = _build_current_input_core_phrase_units(generation_evidence_items)
    if len(phrase_units) < 2:
        return _unavailable_response(
            "limited_composer_shallow_insufficient_evidence",
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={"source_profile_key": source_profile_key, "shallow_observation_path": True},
        )

    lines, used_unit_ids = _render_current_input_core_lines(payload=payload, units=phrase_units)
    if not lines:
        return _unavailable_response(
            "limited_composer_shallow_empty_candidate",
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={"source_profile_key": source_profile_key, "shallow_observation_path": True},
        )

    comment_text = "\n".join(line for line in lines if line).strip()
    matched_forbidden = _matched_forbidden_surfaces(payload=payload, text=comment_text)
    if matched_forbidden:
        return _unavailable_response(
            "limited_composer_forbidden_surface",
            matched_forbidden=matched_forbidden,
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={"source_profile_key": source_profile_key, "shallow_observation_path": True},
        )

    unit_by_id = {unit.phrase_unit_id: unit for unit in phrase_units}
    used_evidence_ids = _dedupe(unit_by_id[unit_id].evidence_span_id for unit_id in used_unit_ids if unit_id in unit_by_id)
    quality_report = judge_limited_sentence_quality(
        comment_text=comment_text,
        evidence_spans=_evidence_objects_for_quality(generation_evidence_items),
        profile_key=profile_key,
        used_evidence_span_ids=used_evidence_ids,
        composer_meta={"profile_key": profile_key, "source_profile_key": source_profile_key, "shallow_observation_path": True},
    )
    if not bool(quality_report.get("passed")):
        return _unavailable_response(
            "limited_composer_sentence_quality_rejected",
            matched_forbidden=list(quality_report.get("matched_fragments") or quality_report.get("matched_surfaces") or []),
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={"phase8_quality": quality_report, "source_profile_key": source_profile_key, "shallow_observation_path": True},
        )

    used_evidence_ids = [span_id for span_id in used_evidence_ids if span_id in evidence_by_id]
    if not used_evidence_ids:
        return _unavailable_response(
            "limited_composer_no_used_evidence",
            coverage_scope="current_input_core",
            profile_key=profile_key,
            extra_meta={"source_profile_key": source_profile_key, "shallow_observation_path": True},
        )
    greeting_count = 1 if lines and "Emlis" in lines[0] else 0
    body_lines = lines[greeting_count:]
    response = {
        "schema_version": _RESPONSE_SCHEMA_VERSION,
        "response_schema_version": _RESPONSE_SCHEMA_VERSION,
        "composer_source": _ALLOWED_SOURCE,
        "status": "generated",
        "composer_model": _COMPOSER_MODEL,
        "generation_method": _GENERATION_METHOD,
        "generation_scope": _GENERATION_SCOPE,
        "fixed_string_renderer_used": False,
        "coverage_scope": "current_input_core",
        "comment_text": comment_text,
        "used_evidence_span_ids": used_evidence_ids,
        "used_claim_ids": _used_claim_ids(graph),
        "used_relation_ids": _used_relation_ids(graph),
        "confidence": _shallow_confidence(used_unit_ids=used_unit_ids, units=phrase_units),
        "composer_meta": {
            "limited_composer": True,
            "generation_scope": _GENERATION_SCOPE,
            "external_ai_used": False,
            "phase8_quality_path": True,
            "profile_key": profile_key,
            "source_profile_key": source_profile_key,
            "shallow_observation_path": True,
            "required_roles": [],
            "covered_roles": _dedupe(unit.role for unit in phrase_units if unit.phrase_unit_id in set(used_unit_ids)),
            "body_line_count": len(body_lines),
            "phrase_unit_count": len(phrase_units),
            "sentence_plan_count": 0,
            "allowed_evidence_span_ids": sorted(allowed_evidence_ids),
            "phase8_quality": quality_report,
        },
    }
    return _core_checked_response(
        response=response,
        payload=payload,
        evidence_items=generation_evidence_items,
        phrase_units=phrase_units,
        sentence_plans=(),
        used_unit_ids=used_unit_ids,
        coverage_scope="current_input_core",
        profile_key=profile_key,
    )

def _core_checked_response(
    *,
    response: Mapping[str, Any],
    payload: Mapping[str, Any],
    evidence_items: Sequence[Mapping[str, Any]],
    phrase_units: Sequence[EmlisPhraseUnit],
    sentence_plans: Sequence[SentencePlan],
    used_unit_ids: Sequence[str],
    coverage_scope: str,
    profile_key: str,
) -> Mapping[str, Any]:
    evaluation = evaluate_emlis_observation_candidate(
        composer_payload=payload,
        evidence_items=evidence_items,
        phrase_units=phrase_units,
        sentence_plans=sentence_plans,
        comment_text=str(response.get("comment_text") or ""),
        used_evidence_span_ids=list(response.get("used_evidence_span_ids") or []),
        used_phrase_unit_ids=used_unit_ids,
        coverage_scope=coverage_scope,
        composer_model=str(response.get("composer_model") or _COMPOSER_MODEL),
        composer_meta=response.get("composer_meta") if isinstance(response.get("composer_meta"), Mapping) else {},
        response=response,
    )
    if evaluation.passed:
        return attach_core_evaluation_meta(response, evaluation)
    core_meta = evaluation.as_meta()
    return _unavailable_response(
        core_rejection_reason(evaluation),
        coverage_scope=coverage_scope,
        profile_key=profile_key,
        extra_meta={
            "text_generation_core": core_meta,
            "core_text_generation": core_meta,
        },
    )

def _phase8_profile_evidence_ids(profile_key: str, evidence_items: Sequence[Mapping[str, Any]]) -> set[str]:
    profile = _profile_for_key(profile_key)
    required = set(profile.required_roles)
    optional_by_profile = {
        "mixed_positive_anxiety": {"positive_state", "anxiety_return", "fall_contrast"},
        "anger_hurt_boundary": {"anger_surface", "unfairness", "hurt_core", "withdrawal"},
        "self_understanding_loop": {"anticipation_loop", "known_action", "perfection_fear"},
        "positive_progress": {"small_action", "relieved_weight", "achievement"},
        "relationship_approach_avoidance": {"wish_to_rely", "burden_fear", "rejection_fear", "limit"},
        "reality_escape_tension": {"safe_home", "reality_damage", "ordinary_life_wish", "worsening_risk", "known_action", "limit"},
    }.get(profile_key, set())
    target_roles = required | set(optional_by_profile)
    ids: set[str] = set()
    for item in evidence_items:
        if _skip_evidence(item):
            continue
        roles = set(phase8_roles_for_text(_raw_text(item), _detected_type(item)))
        if roles.intersection(target_roles):
            span_id = str(item.get("span_id") or "").strip()
            if span_id:
                ids.add(span_id)
    return ids

def _build_phrase_units(evidence_items: Sequence[Mapping[str, Any]]) -> List[EmlisPhraseUnit]:
    units: List[EmlisPhraseUnit] = []
    for item in evidence_items:
        if _skip_evidence(item):
            continue
        raw = _raw_text(item)
        roles = phase8_roles_for_text(raw, _detected_type(item))
        if not roles:
            role, _polarity, _must_keep = _role_for_text(raw, _detected_type(item))
            roles = (role,) if role != "other" else tuple()
        for role in roles:
            if role == "other":
                continue
            polarity, must_keep = phase8_role_meta(role)
            compressed = _compress_text(raw, role)
            if not compressed or compressed in _EMOTION_LABELS:
                continue
            span_id = str(item.get("span_id") or f"s{len(units)+1}").strip()
            units.append(
                EmlisPhraseUnit(
                    phrase_unit_id=f"pu{len(units)+1}",
                    evidence_span_id=span_id,
                    raw_text=raw,
                    compressed_text=compressed,
                    role=role,
                    polarity=polarity,
                    must_keep=must_keep,
                    quality_flags=_quality_flags(compressed),
                )
            )
    return units


def _profile_for_key(profile_key: str) -> ObservationProfile:
    profiles = {
        "mixed_positive_anxiety": ObservationProfile("mixed_positive_anxiety", ("positive_state", "anxiety_return"), min_lines=2, max_lines=3),
        "anger_hurt_boundary": ObservationProfile("anger_hurt_boundary", ("anger_surface", "hurt_core"), min_lines=2, max_lines=3),
        "self_understanding_loop": ObservationProfile("self_understanding_loop", ("anticipation_loop", "perfection_fear"), min_lines=2, max_lines=3),
        "positive_progress": ObservationProfile("positive_progress", ("small_action", "achievement"), min_lines=2, max_lines=3),
        "relationship_approach_avoidance": ObservationProfile("relationship_approach_avoidance", ("wish_to_rely", "burden_fear", "rejection_fear", "limit"), min_lines=2, max_lines=3),
        "reality_escape_tension": ObservationProfile("reality_escape_tension", ("safe_home", "reality_damage", "ordinary_life_wish", "worsening_risk"), min_lines=3, max_lines=4),
    }
    return profiles.get(profile_key, ObservationProfile("unknown", tuple(), min_lines=0, max_lines=0, coverage_scope="current_input_core"))


def _units_for_role(units: Sequence[EmlisPhraseUnit], role: str) -> List[EmlisPhraseUnit]:
    return [unit for unit in units if unit.role == role]


def _first_unit(units: Sequence[EmlisPhraseUnit], *roles: str) -> Optional[EmlisPhraseUnit]:
    for role in roles:
        found = _units_for_role(units, role)
        if found:
            return found[0]
    return None


def _unit_ids(*units: Optional[EmlisPhraseUnit]) -> Tuple[str, ...]:
    return tuple(unit.phrase_unit_id for unit in units if unit is not None)


def _sentence_plans_for_profile(*, profile: ObservationProfile, units: Sequence[EmlisPhraseUnit]) -> List[SentencePlan]:
    key = profile.profile_key
    if key == "mixed_positive_anxiety":
        return [
            SentencePlan("receive", tuple(unit.phrase_unit_id for unit in units if unit.role == "positive_state")[:2], "sequence"),
            SentencePlan("contrast", _unit_ids(_first_unit(units, "anxiety_return")), "contrast"),
            SentencePlan("contrast_detail", _unit_ids(_first_unit(units, "fall_contrast")), "coexistence", must_include=False),
        ]
    if key == "anger_hurt_boundary":
        hurt_units = tuple(unit.phrase_unit_id for unit in units if unit.role in {"hurt_core", "unfairness"})[:2]
        return [
            SentencePlan("receive", _unit_ids(_first_unit(units, "anger_surface")), "surface"),
            SentencePlan("contrast", hurt_units, "contrast"),
            SentencePlan("distance", _unit_ids(_first_unit(units, "withdrawal")), "distance", must_include=False),
        ]
    if key == "self_understanding_loop":
        return [
            SentencePlan("tension", _unit_ids(_first_unit(units, "anticipation_loop")), "pressure"),
            SentencePlan("context", _unit_ids(_first_unit(units, "known_action")), "context", must_include=False),
            SentencePlan("tension_detail", tuple(unit.phrase_unit_id for unit in units if unit.role == "perfection_fear")[:2], "coexistence"),
        ]
    if key == "positive_progress":
        return [
            SentencePlan("progress", _unit_ids(_first_unit(units, "small_action")), "progress"),
            SentencePlan("progress_detail", _unit_ids(_first_unit(units, "relieved_weight")), "sequence", must_include=False),
            SentencePlan("progress_detail", _unit_ids(_first_unit(units, "achievement")), "progress"),
        ]
    if key == "relationship_approach_avoidance":
        return [
            SentencePlan("approach", _unit_ids(_first_unit(units, "wish_to_rely")), "approach"),
            SentencePlan("tension", tuple(unit.phrase_unit_id for unit in units if unit.role in {"burden_fear", "rejection_fear"})[:2], "approach_avoidance"),
            SentencePlan("limit", _unit_ids(_first_unit(units, "limit")), "limit"),
        ]
    if key == "reality_escape_tension":
        return [
            SentencePlan("receive", tuple(unit.phrase_unit_id for unit in sorted([u for u in units if u.role == "safe_home"], key=lambda u: (0 if any(term in u.compressed_text for term in ("リラックス", "優先", "整え")) else 1, u.phrase_unit_id)))[:1], "sequence"),
            SentencePlan("contrast", tuple(unit.phrase_unit_id for unit in units if unit.role == "reality_damage")[:2], "contrast"),
            SentencePlan("tension", tuple(unit.phrase_unit_id for unit in units if unit.role in {"ordinary_life_wish", "worsening_risk", "known_action"})[:3], "tension"),
            SentencePlan("escape", _unit_ids(_first_unit(units, "limit")), "limit", must_include=False),
        ]
    return []


def _unit_by_id(units: Sequence[EmlisPhraseUnit]) -> Dict[str, EmlisPhraseUnit]:
    return {unit.phrase_unit_id: unit for unit in units}


def _units_for_plan_ids(units: Sequence[EmlisPhraseUnit], plan: SentencePlan) -> List[EmlisPhraseUnit]:
    by_id = _unit_by_id(units)
    return [by_id[unit_id] for unit_id in plan.phrase_unit_ids if unit_id in by_id and by_id[unit_id].compressed_text]


def _texts_for_plan(units: Sequence[EmlisPhraseUnit], plan: SentencePlan) -> List[str]:
    return _dedupe(unit.compressed_text for unit in _units_for_plan_ids(units, plan))


def _finish(value: Any) -> str:
    text = _clean(value, limit=220).strip(_PUNCT_TRIM)
    return f"{text}。" if text else ""


def _plan_polarity(plan_units: Sequence[EmlisPhraseUnit]) -> str:
    polarities = {unit.polarity for unit in plan_units if unit.polarity}
    if not polarities:
        return "neutral"
    if "mixed" in polarities or ("positive" in polarities and "negative" in polarities):
        return "mixed"
    if "negative" in polarities:
        return "negative"
    if "positive" in polarities:
        return "positive"
    return "neutral"


def _sentence_unit_order_key(plan: SentencePlan, unit: EmlisPhraseUnit) -> Tuple[int, str]:
    if plan.relation_type == "tension":
        order = {
            "ordinary_life_wish": 0,
            "wish_to_rely": 0,
            "worsening_risk": 1,
            "perfection_fear": 1,
            "limit": 1,
            "known_action": 2,
        }
        return order.get(unit.role, 9), unit.phrase_unit_id
    if plan.relation_type == "coexistence":
        order = {"known_action": 0, "perfection_fear": 1, "fall_contrast": 1}
        return order.get(unit.role, 5), unit.phrase_unit_id
    return 0, unit.phrase_unit_id


def _select_subject_units(plan: SentencePlan, plan_units: Sequence[EmlisPhraseUnit]) -> List[EmlisPhraseUnit]:
    units = sorted(list(plan_units), key=lambda unit: _sentence_unit_order_key(plan, unit))
    if not units:
        return []
    if plan.relation_type in {"sequence", "contrast", "coexistence", "approach_avoidance", "tension"}:
        return units[:2]
    return units[:1]


def _joiner_for_plan(plan: SentencePlan, selected_units: Sequence[EmlisPhraseUnit]) -> str:
    roles = {unit.role for unit in selected_units}
    if plan.relation_type in {"tension", "coexistence"}:
        return "と、"
    if plan.relation_type == "contrast" and roles.issubset({"reality_damage"}):
        return "と、"
    return "や、"


def _join_subject_texts(*, plan: SentencePlan, selected_units: Sequence[EmlisPhraseUnit]) -> str:
    cleaned = [unit.compressed_text for unit in selected_units if unit.compressed_text]
    cleaned = _dedupe(cleaned)
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    joiner = _joiner_for_plan(plan, selected_units)
    return joiner.join(cleaned[:2])


def _opener_for_plan(*, plan: SentencePlan, sequence_index: int) -> str:
    if sequence_index <= 0:
        return ""
    if plan.relation_type in {"contrast", "approach_avoidance"}:
        return "一方で、"
    if plan.relation_type == "tension":
        return "その中で、"
    if plan.relation_type in {"limit", "distance"}:
        return "さらに、"
    if plan.relation_type in {"sequence", "progress"}:
        return "そこから、"
    if plan.relation_type == "coexistence":
        return "同時に、"
    return "さらに、"


def _surface_parts_for_plan(
    *,
    plan: SentencePlan,
    selected_units: Sequence[EmlisPhraseUnit],
    sequence_index: int,
    used_predicate_keys: Sequence[str],
) -> Tuple[SentenceSurfaceParts, str]:
    ctx = SentenceSurfaceContext(
        line_role=plan.line_role,
        relation_type=plan.relation_type,
        phrase_count=len(selected_units),
        polarity=_plan_polarity(selected_units),
        sequence_order=sequence_index,
    )
    relation = ctx.relation_type
    polarity = ctx.polarity
    opener = _opener_for_plan(plan=plan, sequence_index=ctx.sequence_order)
    joiner = _joiner_for_plan(plan, selected_units)

    candidates: Tuple[Tuple[str, str, str], ...]
    if relation == "surface":
        candidates = (("が", "表に出ています", "surface_visible"), ("が", "前面にあります", "front"))
    elif relation == "pressure":
        candidates = (("が", "続いています", "continue"), ("が", "強く残っています", "strong_remain"))
    elif relation == "context":
        candidates = (("も", "書かれています", "written"), ("も", "重なっています", "stack"))
    elif relation == "progress":
        candidates = (("が", "書かれています", "written"), ("が", "形になっています", "progress_shape"))
    elif relation == "approach":
        candidates = (("が", "言葉になっています", "worded"), ("が", "前面にあります", "front"))
    elif relation == "approach_avoidance":
        candidates = (("も", "書かれています", "written"), ("も", "重なっています", "stack"))
    elif relation == "contrast":
        roles = {unit.role for unit in selected_units}
        if roles.issubset({"reality_damage"}):
            candidates = (("が", "大きく響いています", "impact"), ("も", "残っています", "remain"))
        elif polarity == "negative":
            candidates = (("も", "重なっています", "stack"), ("も", "書かれています", "written"))
        else:
            candidates = (("が", "戻ってきています", "return"), ("も", "残っています", "remain"))
    elif relation == "tension":
        candidates = (("が", "ぶつかっています", "tension"), ("が", "同時に残っています", "co_remain"))
    elif relation == "coexistence":
        candidates = (("が", "混ざっています", "mixed"), ("も", "並んでいます", "parallel"))
    elif relation == "distance":
        candidates = (("も", "書かれています", "written"), ("も", "続いています", "continue"))
    elif relation == "limit":
        subject = selected_units[0].compressed_text if selected_units else ""
        if "限界" in subject:
            candidates = (("まで", "来ています", "limit_arrived"),)
        elif subject.endswith("時"):
            candidates = (("も", "あります", "exists"), ("も", "残っています", "remain"))
        else:
            candidates = (("も", "書かれています", "written"), ("も", "残っています", "remain"))
    elif relation == "sequence":
        if polarity == "positive":
            candidates = (("が", "書かれています", "written"), ("が", "続いています", "continue"), ("が", "残っています", "remain"))
        else:
            candidates = (("が", "続いています", "continue"), ("が", "書かれています", "written"), ("が", "残っています", "remain"))
    else:
        candidates = (("が", "書かれています", "written"), ("が", "残っています", "remain"))

    used = set(used_predicate_keys or [])
    particle, predicate, key = next((candidate for candidate in candidates if candidate[2] not in used), candidates[0])
    return SentenceSurfaceParts(opener=opener, joiner=joiner, particle=particle, predicate=predicate, max_phrases=2), key


def _realize_sentence(
    *,
    plan: SentencePlan,
    plan_units: Sequence[EmlisPhraseUnit],
    sequence_index: int,
    used_predicate_keys: Sequence[str],
) -> Tuple[str, str]:
    selected_units = _select_subject_units(plan, plan_units)
    subject = _join_subject_texts(plan=plan, selected_units=selected_units)
    if not subject:
        return "", ""
    parts, predicate_key = _surface_parts_for_plan(
        plan=plan,
        selected_units=selected_units,
        sequence_index=sequence_index,
        used_predicate_keys=used_predicate_keys,
    )
    return _finish(f"{parts.opener}{subject}{parts.particle}{parts.predicate}"), predicate_key



def _greeting(payload: Mapping[str, Any]) -> str:
    addressee = payload.get("addressee") if isinstance(payload.get("addressee"), Mapping) else {}
    call = _clean(addressee.get("display_name_call"), limit=28)
    greeting = _clean(addressee.get("greeting_text"), limit=32) or "Emlisです"
    if call and call not in greeting:
        return _finish(f"{call}、{greeting}")
    return _finish(greeting)

def _render_sentence_plans(*, payload: Mapping[str, Any], profile: ObservationProfile, plans: Sequence[SentencePlan], units: Sequence[EmlisPhraseUnit]) -> Tuple[List[str], List[str], List[str]]:
    lines: List[str] = []
    used: List[str] = []
    used_predicate_keys: List[str] = []
    greeting = _greeting(payload)
    if greeting:
        lines.append(greeting)
    for plan in plans:
        plan_units = _units_for_plan_ids(units, plan)
        if plan.must_include and not plan_units:
            return [], [], []
        if not plan_units:
            continue
        sequence_index = len([line for line in lines if "Emlis" not in line])
        line, predicate_key = _realize_sentence(
            plan=plan,
            plan_units=plan_units,
            sequence_index=sequence_index,
            used_predicate_keys=used_predicate_keys,
        )
        line = _trim_line(line, limit=plan.max_chars)
        if line and line not in lines:
            lines.append(line)
            used_predicate_keys.append(predicate_key)
            used.extend(unit.phrase_unit_id for unit in _select_subject_units(plan, plan_units))
        if len(lines) >= 1 + _MAX_BODY_LINES:
            break
    return lines, _dedupe(used), _dedupe(used_predicate_keys)


def _trim_line(value: str, *, limit: int) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > limit:
        text = text[:limit].rstrip(_PUNCT_TRIM) + "。"
    return text


def _body_limits(scope: Mapping[str, Any], *, profile: ObservationProfile) -> Tuple[int, int]:
    try:
        min_count = int(scope.get("min_reply_sentence_count") or profile.min_lines or _MIN_BODY_LINES)
    except Exception:
        min_count = profile.min_lines or _MIN_BODY_LINES
    try:
        max_count = int(scope.get("max_reply_sentence_count") or profile.max_lines or _MAX_BODY_LINES)
    except Exception:
        max_count = profile.max_lines or _MAX_BODY_LINES
    min_count = max(min_count, profile.min_lines)
    max_count = max(max_count, profile.max_lines)
    return max(1, min(3, min_count)), max(2, min(4, max_count))


def _matched_forbidden_surfaces(*, payload: Mapping[str, Any], text: str) -> List[str]:
    contract = payload.get("composition_contract") if isinstance(payload.get("composition_contract"), Mapping) else {}
    configured = [str(item or "").strip() for item in list(contract.get("forbidden_output_surfaces") or [])]
    patterns = _dedupe([*_FORBIDDEN_SURFACES, *configured])
    return [surface for surface in patterns if surface and surface in text]


def _coverage_scope(graph: Mapping[str, Any]) -> str:
    if list(graph.get("core_tensions") or []) or any(list(graph.get(key) or []) for key in _GROUP_KEYS):
        return "partial_observation"
    return "current_input_core"


def _used_claim_ids(graph: Mapping[str, Any]) -> List[str]:
    ids: List[str] = []
    primary = graph.get("primary_state") if isinstance(graph.get("primary_state"), Mapping) else {}
    primary_id = str(primary.get("claim_id") or "").strip()
    if primary_id:
        ids.append(primary_id)
    for group_key in _GROUP_KEYS:
        for claim in list(graph.get(group_key) or []):
            if isinstance(claim, Mapping):
                claim_id = str(claim.get("claim_id") or "").strip()
                if claim_id:
                    ids.append(claim_id)
    return _dedupe(ids)


def _used_relation_ids(graph: Mapping[str, Any]) -> List[str]:
    return _dedupe(str(edge.get("edge_id") or "").strip() for edge in list(graph.get("core_tensions") or []) if isinstance(edge, Mapping))


def _evidence_objects_for_quality(items: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    return [dict(item) for item in items if isinstance(item, Mapping)]


def _confidence(*, profile: ObservationProfile, phrase_units: Sequence[EmlisPhraseUnit], used_unit_ids: Sequence[str]) -> float:
    base = 0.74 if profile.profile_key != "unknown" else 0.0
    used_roles = {unit.role for unit in phrase_units if unit.phrase_unit_id in set(used_unit_ids)}
    ratio = len(set(profile.required_roles).intersection(used_roles)) / max(1, len(profile.required_roles))
    return round(max(0.0, min(0.94, base + 0.18 * ratio)), 3)


def audit_limited_composer_contract() -> List[str]:
    issues: List[str] = []
    for marker in _MARKER_NAMES:
        if marker in globals():
            issues.append(marker)
    return issues


__all__ = ["CocolonLimitedComposerClient", "EmlisPhraseUnit", "ObservationProfile", "SentencePlan", "audit_limited_composer_contract"]
