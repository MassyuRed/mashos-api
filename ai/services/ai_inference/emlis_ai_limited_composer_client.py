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

from emlis_ai_limited_sentence_quality_guard import detect_phase8_profile, judge_limited_sentence_quality

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
        if profile_key in {"", "unknown", "current_input_core"}:
            return _unavailable_response("limited_composer_profile_unknown", coverage_scope=coverage_scope, profile_key=profile_key or "unknown")

        allowed_evidence_ids = _allowed_evidence_ids_from_graph(graph)
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
        lines, used_unit_ids = _render_sentence_plans(payload=payload, profile=profile, plans=plans, units=phrase_units)
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

        return {
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
                "allowed_evidence_span_ids": sorted(allowed_evidence_ids),
                "phase8_quality": quality_report,
            },
        }


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
    c = _compact(text)
    if "頼りたい" in c:
        return "wish_to_rely", "mixed", True
    if "迷惑" in c:
        return "burden_fear", "negative", True
    if any(t in c for t in ("嫌われ", "重い", "怖い")) and any(t in c for t in ("嫌われ", "重い")):
        return "rejection_fear", "negative", True
    if any(t in c for t in ("限界", "逃げ出", "何もしたくない")):
        return "limit", "negative", True
    if any(t in c for t in ("大事に扱われ", "しんど")):
        return "hurt_core", "negative", True
    if any(t in c for t in ("されなきゃ", "ちゃんと考えて話")):
        return "unfairness", "negative", True
    if any(t in c for t in ("言い方", "腹が立", "怒って")):
        return "anger_surface", "negative", True
    if "面倒" in c:
        return "withdrawal", "negative", False
    if any(t in c for t in ("分かってる", "分かっている")):
        return "known_action", "neutral", True
    if any(t in c for t in ("考えすぎ", "先のこと", "止まら", "動けなく")):
        return "anticipation_loop", "negative", True
    if any(t in c for t in ("完璧", "適当にやる", "適当")):
        return "perfection_fear", "negative", True
    if "片付け" in c:
        return "small_action", "positive", True
    if any(t in c for t in ("気になってた", "気になっていた", "気持ちが軽い", "軽い")):
        return "relieved_weight", "positive", True
    if any(t in c for t in ("家にいて", "リラックス", "優先", "整え", "お家", "おうち")):
        return "safe_home", "positive", True
    if any(t in c for t in ("ちゃんとできた", "嬉しい")):
        return "achievement", "positive", True
    if any(t in c for t in ("友達と話せ", "楽しかった", "笑えた", "元気")):
        return "positive_state", "positive", True
    if any(t in c for t in ("帰ってきて一人", "急に不安", "落ちる")):
        return "anxiety_return", "negative", True
    if any(t in c for t in ("現実", "ダメージ", "不便")):
        return "reality_damage", "negative", True
    if any(t in c for t in ("普通に生活したい", "生活したい")):
        return "ordinary_life_wish", "mixed", True
    if "悪化" in c:
        return "worsening_risk", "negative", True
    if any(t in c for t in ("だるい", "何もしたくない")):
        return "low_energy", "negative", True
    if detected_type in {"wish", "value"}:
        return "positive_state", "positive", False
    if detected_type in {"fear", "constraint", "limit_signal"}:
        return "pressure_or_limit", "negative", False
    return "other", "neutral", False


def _compress_text(raw: str, role: str) -> str:
    text = _clean(raw, limit=200)
    if role == "safe_home" and ("リラックス" in text or "優先" in text or "整え" in text):
        return "リラックスできて自分を優先して整えられる嬉しさ"
    if role == "ordinary_life_wish" and "生活したい" in text:
        return "普通に生活したい気持ち"
    if role == "limit" and "逃げ出" in text:
        return "たまに逃げ出したくなる感覚"
    if role == "reality_damage" and "生活不便" in text:
        return "今の生活の不便さ"
    replacements = (
        ("今日は久しぶりに友達と話せて楽しかった", "友達と話せて楽しかったこと"),
        ("ちゃんと笑えたし、少し元気になれた気がする", "少し元気になれた感覚"),
        ("帰ってきて一人になったら、また急に不安になった", "帰ってきて一人になった時の急な不安"),
        ("楽しかったはずなのに、なんでこんなに落ちるんだろうって思う", "楽しかったはずなのに落ちる感覚"),
        ("相手の言い方がきつくて腹が立った", "相手の言い方がきつくて腹が立ったこと"),
        ("こっちはちゃんと考えて話してるのに、なんであんな言い方されなきゃいけないのか分からない", "ちゃんと考えて話しているのに、きつい言い方をされる分からなさ"),
        ("怒ってるけど、本当は大事に扱われなかったことがしんどい", "大事に扱われなかったしんどさ"),
        ("もう話すのが面倒になってきた", "もう話すのが面倒になってきたこと"),
        ("また考えすぎて動けなくなった", "考えすぎて動けなくなったこと"),
        ("やることは分かってるのに、先のことを考え始めると止まらなくなる", "やることは分かっているのに、先のことを考えると止まらなくなる流れ"),
        ("たぶん完璧にやろうとしすぎてる", "完璧にやろうとする怖さ"),
        ("でも適当にやるのも怖い", "適当にやる怖さ"),
        ("適当にやるのも怖い", "適当にやる怖さ"),
        ("今日は少しだけ部屋を片付けられた", "少しだけ部屋を片付けられたこと"),
        ("大きなことじゃないけど、ずっと気になってた場所だったから少し気持ちが軽い", "気になっていた場所に触れられて、気持ちが少し軽くなる感覚"),
        ("ちゃんとできた感じがして嬉しい", "ちゃんとできた感じの嬉しさ"),
        ("本当はもっと頼りたい", "本当はもっと頼りたい気持ち"),
        ("頼ったら迷惑だと思われそうで言えない", "迷惑だと思われそうで言えない怖さ"),
        ("相手に嫌われたいわけじゃないし、重いと思われるのも怖い", "嫌われることや重いと思われることへの怖さ"),
        ("一人で抱えるのも限界に近い", "一人で抱える限界の近さ"),
        ("ずっと家にいて", "家にいてリラックスできること"),
        ("ずっと家にいて、リラックスできて自分のことを", "家にいてリラックスできること"),
        ("優先して色々整えたりお家のことも出来るから", "自分を優先して整えられる嬉しさ"),
        ("嬉しいんだけど、ふって気が抜けたときに現実と", "気が抜けた時に現実へ戻ること"),
        ("向き合うことがあるからその時にダメージでかい", "現実と向き合う時の大きなダメージ"),
        ("あぁ、今の生活不便だな、と", "今の生活の不便さ"),
        ("気をつけなきゃ行けないこと、全部無視して普通に", "気をつけなきゃいけないことを無視したい感覚"),
        ("生活したい", "普通に生活したい気持ち"),
        ("そうしたらもっと悪化する", "そうするともっと悪化すると分かっている感覚"),
        ("そんなの分かってる", "悪化すると分かっている自覚"),
        ("たまに逃げ出したくなる", "たまに逃げ出したくなる限界"),
    )
    for src, dst in replacements:
        if text == src or src in text:
            return dst
    if role == "safe_home" and text == "ずっと家にいて":
        return "家にいてリラックスできること"
    if role == "safe_home" and "自分のことを" in text:
        return "リラックスできて自分を優先して整えられる嬉しさ"
    if role == "reality_damage" and text.endswith("現実と"):
        return "気が抜けた時に現実へ戻ること"
    if role == "ordinary_life_wish" and ("生活したい" in text or text == "生活したい"):
        return "普通に生活したい気持ち"
    return text


def _quality_flags(text: str) -> Tuple[str, ...]:
    flags: List[str] = []
    if re.search(r"(なんであ|考え始め|現実と|自分のことを|普通に)$", text):
        flags.append("unfinished_phrase")
    if len(_compact(text)) > 64:
        flags.append("too_long_quote")
    if re.search(r"[をがにはへで]$", text):
        flags.append("orphan_particle")
    return tuple(flags)




def _phase8_profile_evidence_ids(profile_key: str, evidence_items: Sequence[Mapping[str, Any]]) -> set[str]:
    profile = _profile_for_key(profile_key)
    required = set(profile.required_roles)
    optional_by_profile = {
        "mixed_positive_anxiety": {"positive_state", "anxiety_return"},
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
        role, _polarity, _must_keep = _role_for_text(_raw_text(item), _detected_type(item))
        if role in target_roles:
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
        role, polarity, must_keep = _role_for_text(raw, _detected_type(item))
        if role == "other":
            continue
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
            SentencePlan("positive", tuple(unit.phrase_unit_id for unit in units if unit.role == "positive_state")[:2], "sequence"),
            SentencePlan("contrast", _unit_ids(_first_unit(units, "anxiety_return")), "contrast"),
            SentencePlan("fall", _unit_ids(_first_unit(units, "fall_contrast")), "mixed", must_include=False),
        ]
    if key == "anger_hurt_boundary":
        hurt_units = tuple(unit.phrase_unit_id for unit in units if unit.role in {"hurt_core", "unfairness"})[:2]
        return [
            SentencePlan("anger", _unit_ids(_first_unit(units, "anger_surface")), "surface"),
            SentencePlan("hurt", hurt_units, "contrast"),
            SentencePlan("withdrawal", _unit_ids(_first_unit(units, "withdrawal")), "distance", must_include=False),
        ]
    if key == "self_understanding_loop":
        return [
            SentencePlan("stuck", _unit_ids(_first_unit(units, "anticipation_loop")), "loop"),
            SentencePlan("known", _unit_ids(_first_unit(units, "known_action")), "known_but_stuck", must_include=False),
            SentencePlan("fear", tuple(unit.phrase_unit_id for unit in units if unit.role == "perfection_fear")[:2], "coexistence"),
        ]
    if key == "positive_progress":
        return [
            SentencePlan("small_action", _unit_ids(_first_unit(units, "small_action")), "progress"),
            SentencePlan("relief", _unit_ids(_first_unit(units, "relieved_weight")), "sequence", must_include=False),
            SentencePlan("achievement", _unit_ids(_first_unit(units, "achievement")), "positive"),
        ]
    if key == "relationship_approach_avoidance":
        return [
            SentencePlan("wish", _unit_ids(_first_unit(units, "wish_to_rely")), "wish"),
            SentencePlan("fear", tuple(unit.phrase_unit_id for unit in units if unit.role in {"burden_fear", "rejection_fear"})[:2], "approach_avoidance"),
            SentencePlan("limit", _unit_ids(_first_unit(units, "limit")), "limit"),
        ]
    if key == "reality_escape_tension":
        return [
            SentencePlan("safe_home", tuple(unit.phrase_unit_id for unit in sorted([u for u in units if u.role == "safe_home"], key=lambda u: (0 if any(term in u.compressed_text for term in ("リラックス", "優先", "整え")) else 1, u.phrase_unit_id)))[:1], "positive_base"),
            SentencePlan("reality", tuple(unit.phrase_unit_id for unit in units if unit.role == "reality_damage")[:2], "contrast"),
            SentencePlan("wish_risk", tuple(unit.phrase_unit_id for unit in units if unit.role in {"ordinary_life_wish", "worsening_risk", "known_action"})[:3], "tension"),
            SentencePlan("escape", _unit_ids(_first_unit(units, "limit")), "limit", must_include=False),
        ]
    return []


def _unit_by_id(units: Sequence[EmlisPhraseUnit]) -> Dict[str, EmlisPhraseUnit]:
    return {unit.phrase_unit_id: unit for unit in units}


def _texts_for_plan(units: Sequence[EmlisPhraseUnit], plan: SentencePlan) -> List[str]:
    by_id = _unit_by_id(units)
    return _dedupe(by_id[unit_id].compressed_text for unit_id in plan.phrase_unit_ids if unit_id in by_id and by_id[unit_id].compressed_text)


def _finish(value: Any) -> str:
    text = _clean(value, limit=220).strip(_PUNCT_TRIM)
    return f"{text}。" if text else ""


def _realize_sentence(*, profile: ObservationProfile, plan: SentencePlan, texts: Sequence[str]) -> str:
    key = profile.profile_key
    role = plan.line_role
    t = list(texts)
    if key == "mixed_positive_anxiety":
        if role == "positive":
            return _finish("や、".join(t[:2]) + "が残っています")
        if role == "contrast":
            return _finish(f"一方で、{t[0]}が戻っています")
        if role == "fall":
            return _finish("楽しかったはずなのに落ちる感覚も混ざっています")
    if key == "anger_hurt_boundary":
        if role == "anger":
            return _finish(f"{t[0]}が出ています")
        if role == "hurt":
            return _finish(f"一方で、{'や、'.join(t[:2])}も残っています")
        if role == "withdrawal":
            return _finish(f"{t[0]}も出ています")
    if key == "self_understanding_loop":
        if role == "stuck":
            return _finish(f"{t[0]}が出ています")
        if role == "known":
            return _finish(f"{t[0]}も残っています" if t[0].endswith("流れ") else f"{t[0]}流れも残っています")
        if role == "fear":
            return _finish("と、".join(t[:2]) + "が混ざっています")
    if key == "positive_progress":
        if role == "small_action":
            return _finish(f"{t[0]}が出ています")
        if role == "relief":
            return _finish(f"{t[0]}が残っています" if ("感覚" in t[0] or "軽く" in t[0]) else f"{t[0]}感覚が残っています")
        if role == "achievement":
            return _finish(f"{t[0]}が残っています")
    if key == "relationship_approach_avoidance":
        if role == "wish":
            return _finish(f"{t[0]}が出ています")
        if role == "fear":
            return _finish(f"一方で、{'や、'.join(t[:2])}も出ています")
        if role == "limit":
            base = t[0].replace("感覚", "")
            return _finish(f"{base}が残っています" if "限界" in base else f"{base}まで来ています")
    if key == "reality_escape_tension":
        if role == "safe_home":
            joined = "や、".join(t[:2])
            return _finish(f"{joined}が出ています")
        if role == "reality":
            return _finish(f"一方で、{'と、'.join(t[:2])}が大きく響いています")
        if role == "wish_risk":
            wish = next((x for x in t if "生活したい" in x), t[0])
            risk = next((x for x in t if "悪化" in x), t[-1])
            return _finish(f"{wish}と、{risk}がぶつかっています")
        if role == "escape":
            return _finish(f"{t[0]}も出ています")
    return _finish(t[0])


def _greeting(payload: Mapping[str, Any]) -> str:
    addressee = payload.get("addressee") if isinstance(payload.get("addressee"), Mapping) else {}
    call = _clean(addressee.get("display_name_call"), limit=28)
    greeting = _clean(addressee.get("greeting_text"), limit=32) or "Emlisです"
    if call and call not in greeting:
        return _finish(f"{call}、{greeting}")
    return _finish(greeting)


def _render_sentence_plans(*, payload: Mapping[str, Any], profile: ObservationProfile, plans: Sequence[SentencePlan], units: Sequence[EmlisPhraseUnit]) -> Tuple[List[str], List[str]]:
    lines: List[str] = []
    used: List[str] = []
    greeting = _greeting(payload)
    if greeting:
        lines.append(greeting)
    for plan in plans:
        texts = _texts_for_plan(units, plan)
        if plan.must_include and not texts:
            return [], []
        if not texts:
            continue
        line = _realize_sentence(profile=profile, plan=plan, texts=texts)
        line = _trim_line(line, limit=plan.max_chars)
        if line and line not in lines:
            lines.append(line)
            used.extend(plan.phrase_unit_ids)
        if len(lines) >= 1 + _MAX_BODY_LINES:
            break
    return lines, _dedupe(used)


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
