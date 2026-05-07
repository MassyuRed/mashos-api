# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build generic value-observation signals from current Cocolon input.

This service implements the five observation patterns from the core-strengthening
spec as generic lexical/structural rules.  It deliberately avoids exact sample
matching and returns source-grounded signals that downstream structures can use
in different ways.
"""

import re
from typing import Any, Iterable, List, Mapping, Optional, Sequence

from value_observation_types import ValueObservationPlan, ValueObservationSignal

_TARGET_CORES = ["emlis_ai", "piece", "analysis"]
_SIGNAL_PRIORITY = {
    "ideal_capacity_switch_gap": 90,
    "relationship_cost_asymmetry": 82,
    "outer_inner_role_gap": 76,
    "stagnation_position_gap": 70,
    "inner_activity_fatigue_gap": 64,
}


def _clean(value: Any, *, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()
    if limit > 0 and len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r『』「」（）()\[\]【】]", "", str(value or ""))


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _input_text(current_input: Mapping[str, Any] | None) -> str:
    payload = current_input if isinstance(current_input, Mapping) else {}
    parts: List[str] = []
    for key in ("memo", "memo_action", "text", "free_text"):
        text = _clean(payload.get(key), limit=1000)
        if text:
            parts.append(text)
    for key in ("category", "categories"):
        for item in _as_list(payload.get(key)):
            text = _clean(item, limit=120)
            if text:
                parts.append(text)
    for item in _as_list(payload.get("emotion_details") or payload.get("emotions")):
        if isinstance(item, Mapping):
            label = item.get("type") or item.get("emotion_type") or item.get("emotion") or item.get("label")
        else:
            label = item
        text = _clean(label, limit=80)
        if text:
            parts.append(text)
    return " ".join(parts)


def _input_level(text: Any) -> str:
    count = len(_compact(text))
    if count <= 0:
        return "none"
    if count < 40:
        return "short"
    if count < 120:
        return "medium"
    if count < 260:
        return "long"
    return "very_long"


def _contains_any(compact_text: str, terms: Sequence[str]) -> bool:
    return any(term and term in compact_text for term in terms)


def _evidence_terms(compact_text: str, terms: Sequence[str], *, limit: int = 8) -> List[str]:
    out: List[str] = []
    for term in terms:
        if term and term in compact_text and term not in out:
            out.append(term)
        if len(out) >= limit:
            break
    return out


def _source_fields(current_input: Mapping[str, Any] | None, terms: Sequence[str]) -> List[str]:
    payload = current_input if isinstance(current_input, Mapping) else {}
    fields: List[str] = []
    for key in ("memo", "memo_action", "category", "emotion_details", "emotions"):
        value = payload.get(key)
        joined = " ".join(_clean(v, limit=240) for v in _as_list(value))
        compact = _compact(joined)
        if compact and any(term in compact for term in terms if term):
            fields.append(key)
    return fields or ["memo"]


def _signal(
    *,
    signal_key: str,
    title: str,
    observation_axis: str,
    surface_text: str,
    latent_structure: str,
    value_conversion: str,
    evidence_terms: List[str],
    source_fields: List[str],
    confidence: float,
    emlis_text: str,
    piece_question: str,
    piece_answer: str,
    analysis_hint: str,
    must_keep_terms: Sequence[str],
    softening_required: bool = False,
) -> ValueObservationSignal:
    return ValueObservationSignal(
        signal_key=signal_key,
        title=title,
        observation_axis=observation_axis,
        surface_text=surface_text,
        latent_structure=latent_structure,
        value_conversion=value_conversion,
        evidence_terms=list(evidence_terms),
        source_fields=list(source_fields),
        target_cores=list(_TARGET_CORES),
        confidence=max(0.0, min(1.0, float(confidence or 0.0))),
        public_safe=True,
        softening_required=softening_required,
        no_diagnosis=True,
        no_personality_claim=True,
        emlis_text=emlis_text,
        piece_question=piece_question,
        piece_answer=piece_answer,
        analysis_hint=analysis_hint,
        must_keep_terms=list(must_keep_terms),
        priority=int(_SIGNAL_PRIORITY.get(signal_key, 0)),
    )


def _stagnation_position_gap(current_input: Mapping[str, Any], compact_text: str) -> Optional[ValueObservationSignal]:
    progress_terms = ("進んでない", "進んでいない", "進まない", "進めていない", "進めてない", "前に進", "前進", "進歩")
    sameness_terms = ("同じこと", "繰り返し", "変わり映え", "一日終わ", "このままでいい", "現状", "変わらない", "変化")
    fatigue_terms = ("疲", "嫌", "不満", "不安")
    if not (_contains_any(compact_text, progress_terms) and (_contains_any(compact_text, sameness_terms) or _contains_any(compact_text, fatigue_terms))):
        return None
    terms = _evidence_terms(compact_text, [*progress_terms, *sameness_terms, *fatigue_terms])
    return _signal(
        signal_key="stagnation_position_gap",
        title="停滞・位置変化ギャップ",
        observation_axis="作業量と前進感の不一致",
        surface_text="作業しているのに進んでいない感覚",
        latent_structure="今いる場所から動けていない感覚と、変化したい気持ちの揺れ",
        value_conversion="疲れだけではなく、自分の位置が変わっていないように感じる違和感を言葉にする",
        evidence_terms=terms,
        source_fields=_source_fields(current_input, terms),
        confidence=0.78,
        emlis_text="そこには、作業量の疲れだけでなく、今いる場所から動けていないように感じるしんどさも含まれているように見えます。",
        piece_question="今の自分に足りないと感じている変化は？",
        piece_answer="変わり映えのない日常の中で、このままでいいのかと感じています。進みたい気持ちはあるのに、現実では同じ場所に留まっているように感じ、そのギャップに不満があります。",
        analysis_hint="作業量と前進感が一致しない場面で、停滞感や変化欲求が出やすい流れとして扱う。",
        must_keep_terms=("進", "変わり", "このまま", "ギャップ", "現実"),
    )


def _outer_inner_role_gap(current_input: Mapping[str, Any], compact_text: str) -> Optional[ValueObservationSignal]:
    outer_terms = ("前より", "明るくな", "言われた", "見えて", "褒め", "評価")
    inner_terms = ("怖", "不安", "無理", "本当は", "維持", "そう見え", "保た")
    if not (_contains_any(compact_text, outer_terms) and _contains_any(compact_text, inner_terms)):
        return None
    terms = _evidence_terms(compact_text, [*outer_terms, *inner_terms])
    return _signal(
        signal_key="outer_inner_role_gap",
        title="外側評価・内側実感ギャップ",
        observation_axis="他者評価と自己実感の不一致",
        surface_text="よく見られた嬉しさと、その自分を保つ怖さ",
        latent_structure="周りに見えている自分と、自分の中の実感に差がある状態",
        value_conversion="褒められた嬉しさだけでなく、その見え方を維持しなければならない負担を言葉にする",
        evidence_terms=terms,
        source_fields=_source_fields(current_input, terms),
        confidence=0.80,
        emlis_text="嬉しさの中に、周りに見えている自分と、自分の中の実感が少しずれている怖さも重なっているように見えます。",
        piece_question="最近、無理して保とうとしている自分は？",
        piece_answer="明るく振る舞っている自分です。前より明るくなったと言われるのは嬉しいけれど、その自分を保たないといけないようで怖さもあります。",
        analysis_hint="外側からの評価と内側の実感がずれる場面を、反応傾向として期間内で観測する。",
        must_keep_terms=("明る", "嬉", "怖", "無理", "見え"),
    )


def _relationship_cost_asymmetry(current_input: Mapping[str, Any], compact_text: str) -> Optional[ValueObservationSignal]:
    asymmetry_terms = ("こっちばっかり", "自分だけ", "こっちだけ", "片方", "毎回")
    care_terms = ("気を使", "気遣", "言葉を選", "尊重", "配慮")
    shutdown_terms = ("めんどくさい", "面倒", "どうでもいい", "疲", "しんど")
    if not (_contains_any(compact_text, care_terms) and (_contains_any(compact_text, asymmetry_terms) or _contains_any(compact_text, shutdown_terms))):
        return None
    terms = _evidence_terms(compact_text, [*asymmetry_terms, *care_terms, *shutdown_terms])
    return _signal(
        signal_key="relationship_cost_asymmetry",
        title="関係維持コストの非対称性",
        observation_axis="関係を保つ負担が片側に寄っている感覚",
        surface_text="怒りや投げ出したさとして出ている関係疲れ",
        latent_structure="自分だけが言葉を選び、関係を保つためのエネルギーを使っている感覚",
        value_conversion="怒りの下にある、同じ尊重や配慮を返してほしい気持ちを見つける",
        evidence_terms=terms,
        source_fields=_source_fields(current_input, terms),
        confidence=0.84,
        emlis_text="一番しんどいのは、自分だけが関係を保つために言葉や配慮のエネルギーを使っているように感じるところなのだと思います。",
        piece_question="人間関係で疲れるのはどんな時？",
        piece_answer="自分だけが言葉を選んで、相手を尊重しようとしているように感じる時です。同じように大切に扱ってほしいのに、その負担が自分側に寄っていると疲れてしまいます。",
        analysis_hint="怒りだけではなく、配慮負担の偏りや防衛的な距離取りとして観測する。",
        must_keep_terms=("自分だけ", "言葉", "尊重", "負担", "疲"),
    )


def _inner_activity_fatigue_gap(current_input: Mapping[str, Any], compact_text: str) -> Optional[ValueObservationSignal]:
    low_action_terms = ("何もしてない", "何もしていない", "何もしてなく", "何もし")
    fatigue_terms = ("疲", "しんど", "だる")
    if not (_contains_any(compact_text, low_action_terms) and _contains_any(compact_text, fatigue_terms)):
        return None
    terms = _evidence_terms(compact_text, [*low_action_terms, *fatigue_terms])
    return _signal(
        signal_key="inner_activity_fatigue_gap",
        title="行動量・内的処理量ギャップ",
        observation_axis="外側の行動量と内側の消耗量の不一致",
        surface_text="何もしていないのに疲れている感覚",
        latent_structure="外から見える行動は少なくても、思考・緊張・予測が内側で動いている可能性",
        value_conversion="何かをしたかどうかではなく、内側で動き続けていた負荷を言葉にする",
        evidence_terms=terms,
        source_fields=_source_fields(current_input, terms),
        confidence=0.74,
        emlis_text="何もしていないという行動量だけでは測れない、頭の中の考えや緊張が動き続けていた疲れなのかもしれません。",
        piece_question="何もしていないのに疲れる日は、何が起きている？",
        piece_answer="行動は少なくても、頭の中では考え続けていることがあります。何かをした疲れではなく、内側で動き続けていたことに疲れてしまいます。",
        analysis_hint="行動量ではなく、思考量・緊張・先の予測によって疲れが出る場面として観測する。",
        must_keep_terms=("何もして", "疲", "考え", "内側", "行動"),
    )


def _ideal_capacity_switch_gap(current_input: Mapping[str, Any], compact_text: str) -> Optional[ValueObservationSignal]:
    ideal_terms = ("全部整理", "整理しよう", "計画", "全体", "やること")
    overload_terms = ("量が多", "多すぎ", "嫌にな", "しんど", "扱いきれ")
    switch_terms = ("目についた", "片付け", "手を付け", "手をつけ", "結局")
    after_terms = ("最初の整理", "何だった", "無駄", "終わったあと", "終わった後")
    if not (_contains_any(compact_text, ideal_terms) and (_contains_any(compact_text, switch_terms) or _contains_any(compact_text, overload_terms))):
        return None
    terms = _evidence_terms(compact_text, [*ideal_terms, *overload_terms, *switch_terms, *after_terms])
    return _signal(
        signal_key="ideal_capacity_switch_gap",
        title="理想手順・処理容量ギャップ",
        observation_axis="理想の進め方と実際に処理できる量のズレ",
        surface_text="整理して進めたいのに、途中で目についたものから処理する流れ",
        latent_structure="全体整理を目指すが、扱う量が処理容量を超えると即時処理へ切り替わる反応",
        value_conversion="計画できないのではなく、一度に整理できる量をまだ掴みきれていない状態として見る",
        evidence_terms=terms,
        source_fields=_source_fields(current_input, terms),
        confidence=0.86,
        emlis_text="これは整理する力がないというより、一度に整理できる量を超えた時に、全体管理から目の前の処理へ切り替わりやすい流れとして見えます。",
        piece_question="やることが多い時、どう進めがち？",
        piece_answer="最初は全体を整理して計画的に進めようとします。でも量が多くなると整理しきれなくなって、結局いま目についたものから手をつけることが多いです。終わったあとで、最初の整理がうまく使えなかったことに気づきます。",
        analysis_hint="理想、負荷、即時処理への切替、後評価の流れとして自己構造分析に渡す。",
        must_keep_terms=("整理", "計画", "量", "目についた", "切り替"),
        softening_required=True,
    )


def build_value_observation_signals(
    *,
    current_input: Mapping[str, Any] | None,
    meaning_blocks: Optional[Sequence[Any]] = None,
    shaped_user_phrases: Optional[Sequence[Any]] = None,
) -> List[ValueObservationSignal]:
    payload = current_input if isinstance(current_input, Mapping) else {}
    text = _input_text(payload)
    compact_text = _compact(text)
    if not compact_text:
        return []
    signals: List[ValueObservationSignal] = []
    for builder in (
        _ideal_capacity_switch_gap,
        _relationship_cost_asymmetry,
        _outer_inner_role_gap,
        _stagnation_position_gap,
        _inner_activity_fatigue_gap,
    ):
        signal = builder(payload, compact_text)
        if signal is not None:
            signals.append(signal)
    unique = {signal.signal_key: signal for signal in signals}
    ordered = list(unique.values())
    ordered.sort(key=lambda item: (-int(item.priority), str(item.signal_key)))
    return ordered[:3]


def build_value_observation_plan(
    *,
    current_input: Mapping[str, Any] | None,
    signals: Sequence[ValueObservationSignal] | None,
) -> ValueObservationPlan:
    signal_list = list(signals or [])
    text = _input_text(current_input if isinstance(current_input, Mapping) else {})
    level = _input_level(text)
    terms: List[str] = []
    for signal in signal_list:
        for term in list(signal.evidence_terms or []) + list(signal.must_keep_terms or []):
            if term and term not in terms:
                terms.append(term)
    return ValueObservationPlan(
        input_level=level,
        signal_count=len(signal_list),
        primary_signal_keys=[signal.signal_key for signal in signal_list[:1]],
        must_keep_signal_keys=[signal.signal_key for signal in signal_list if signal.target_cores],
        optional_signal_keys=[signal.signal_key for signal in signal_list if not signal.target_cores],
        overcompression_risk=bool(signal_list and level in {"medium", "long", "very_long"}),
        grounding_terms=terms[:12],
    )


def signal_metas(signals: Iterable[ValueObservationSignal]) -> List[dict[str, Any]]:
    return [signal.as_meta() for signal in list(signals or [])]


def plan_meta(plan: ValueObservationPlan | None) -> dict[str, Any]:
    return plan.as_meta() if plan is not None else ValueObservationPlan(input_level="none", signal_count=0).as_meta()


__all__ = [
    "build_value_observation_plan",
    "build_value_observation_signals",
    "plan_meta",
    "signal_metas",
]
