# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared relation surface contract for EmlisAI generated observations.

This module is intentionally small and dependency-light so Reader, Surface
Realizer and Self-Repair can share the same relation cue vocabulary without
creating import cycles.  It does not read or store raw user input; callers pass
only generated candidate text or relation metadata.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence, Tuple

RELATION_SURFACE_CONTRACT_VERSION = "emlis.relation_surface_contract.v1"
PHRASE_SURFACE_SHAPE_VERSION = "emlis.phrase_surface_shape.v1.20260524"

RAW_INPUT_META_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
}

# Generic relation cues that already represent a relation surface rather than a
# single label.  Do not add broad words such as "関係" here; that would turn the
# Reader Gate into a lexical pass-through and weaken product-quality metrics.
GENERIC_RELATION_SURFACE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("generic_connected", r"つなが(?:って|り|る|っています|れて|った)"),
    ("generic_same_flow", r"同じ(?:時間|場所|流れ|線上|中)"),
    ("generic_both_sides", r"(?:両方|片方|もう一方|一方)"),
    ("generic_overlap", r"(?:重な|並ん|混ざ|同時に|せめぎ合|抱えて)"),
    ("generic_not_one_side", r"(?:片方だけ|一方向|寄らず)"),
)

# Recovery relation cues are stricter.  A mere "回復" or "戻る" is not enough;
# the sentence should surface a bridge between a return/recovery motion and
# prior load, weight, pressure, fatigue, or flow.
RECOVERY_RELATION_SURFACE_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "recovery_load_bridge",
        r"(?:戻ってくる動き|戻る流れ|少し戻(?:って|る)?|形を取り直(?:す|し)|回復)"
        r".{0,32}"
        r"(?:前段|その前|前の|負荷|重さ|圧力|疲れ|流れ)",
    ),
    (
        "recovery_load_bridge_reverse",
        r"(?:前段|その前|前の|負荷|重さ|圧力|疲れ)"
        r".{0,32}"
        r"(?:戻ってくる|戻る|回復|取り直)",
    ),
    (
        "recovery_connected_flow",
        r"(?:戻る流れ|戻ってくる動き|少し戻る動き).{0,32}(?:つなが|同じ流れ|切り離されず)",
    ),
    (
        "recovery_connected_flow_reverse",
        r"(?:つなが|同じ流れ|切り離されず).{0,32}(?:戻る流れ|戻ってくる動き|回復)",
    ),
)

_RELATION_TYPE_ALIASES = {
    "positive_recovery": "recovery",
    "recovering": "recovery",
    "small_recovery": "recovery",
    "repair": "recovery",
}
_CONTEXT_TRUE_VALUES = {"1", "true", "yes", "on", "present", "detected"}


@dataclass(frozen=True)
class RelationSurfaceSignal:
    """Diagnostic-only result of relation surface detection."""

    detected: bool
    count: int = 0
    keys: Tuple[str, ...] = field(default_factory=tuple)
    relation_types: Tuple[str, ...] = field(default_factory=tuple)
    contract_version: str = RELATION_SURFACE_CONTRACT_VERSION
    strict_recovery_bridge_required: bool = True

    def as_meta(self) -> dict[str, Any]:
        return {
            "relation_surface_contract_version": self.contract_version,
            "contract_version": self.contract_version,
            "detected": bool(self.detected),
            "count": int(self.count),
            "keys": list(self.keys),
            "relation_types": list(self.relation_types),
            "reader_relation_signal_detected": bool(self.detected),
            "reader_relation_signal_count": int(self.count),
            "reader_relation_signal_keys": list(self.keys),
            "reader_relation_signal_relation_types": list(self.relation_types),
            "strict_recovery_bridge_required": bool(self.strict_recovery_bridge_required),
            "raw_input_included": False,
        }


@dataclass(frozen=True)
class PhraseSurfaceShapeSignal:
    """Public-safe diagnostic for relation-line phrase surface shape.

    The signal never stores the phrase body or the raw input.  It only tells the
    shallow realizer whether a candidate phrase can be attached directly, needs
    compression, or must be deferred before relation-line rendering.
    """

    shape: str
    safe_for_direct_koto_attachment: bool
    safe_for_relation_line: bool
    requires_surface_compression: bool = False
    requires_drop_or_defer: bool = False
    warning_codes: Tuple[str, ...] = field(default_factory=tuple)
    contract_version: str = RELATION_SURFACE_CONTRACT_VERSION
    version: str = PHRASE_SURFACE_SHAPE_VERSION

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "phrase_surface_shape_version": self.version,
            "relation_surface_contract_version": self.contract_version,
            "contract_version": self.contract_version,
            "shape": self.shape,
            "safe_for_direct_koto_attachment": bool(self.safe_for_direct_koto_attachment),
            "safe_for_relation_line": bool(self.safe_for_relation_line),
            "requires_surface_compression": bool(self.requires_surface_compression),
            "requires_drop_or_defer": bool(self.requires_drop_or_defer),
            "warning_codes": list(self.warning_codes),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
        }


_KOTO_SPLICE_FRAGMENT_RE = re.compile(
    r"(?:ことこと|(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|行かなければ|出なければ|やらなければ|取らなければ)こと|"
    r"予感こと|気配こと|予定こと|必要こと|つもりこと|はずこと|可能性こと|見込みこと|感じこと)(?:$|[もがはにをでへ、。,.])"
)
_OBLIGATION_OR_SCHEDULE_RE = re.compile(
    r"(?:なければ|なきゃ|しなければ|しないと|しなくては|せねば|いけない|ならない|必要|予定|締切|期日|タスク|出なければ|行かなければ|取らなければ)"
)
_PREDICTION_OR_CAPACITY_RE = re.compile(r"(?:予感|気配|キャパオーバー|限界が近|しそう|なりそう|崩れそう|詰まりそう)")
_RELATIONSHIP_ACTION_RE = re.compile(r"(?:コミュニケーション|関わり|関係|連絡|話さ|顔を出|仲間|相手|人と|人との)")
_ANALYTIC_OR_SYSTEM_REGISTER_RE = re.compile(r"(?:状態が一色|一つの要素|今見えている範囲|重なりとして並ん|片方だけに減らさず|網羅|要素だけ)")
_SAFE_NOMINAL_ENDINGS = ("こと", "気持ち", "感覚", "怖さ", "不安", "つらさ", "しんどさ", "限界", "願い", "予感", "気配")


def _compact_surface(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").replace("　", " "))


def _shape_codes(values: Iterable[Any] | Any = ()) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        values = (values,)
    return _dedupe(str(value or "").strip() for value in values if str(value or "").strip())


def classify_phrase_surface_shape(
    phrase: Any,
    *,
    raw_text: Any = "",
    role: Any = "",
    quality_flags: Iterable[Any] | Any = (),
) -> dict[str, Any]:
    """Classify whether a phrase can safely enter a shallow relation line.

    This classifier is intentionally lexical and public-safe: it only returns
    codes, booleans and counts.  It does not expose phrase text or raw input.
    """

    text = _clean(phrase)
    compact = _compact_surface(text)
    raw_compact = _compact_surface(raw_text)
    joined = compact + raw_compact
    flags = _shape_codes(quality_flags)
    codes: list[str] = []

    if not compact:
        signal = PhraseSurfaceShapeSignal(
            shape="unknown",
            safe_for_direct_koto_attachment=False,
            safe_for_relation_line=False,
            requires_drop_or_defer=True,
            warning_codes=("empty_phrase_surface",),
        )
        return signal.as_meta()

    if _KOTO_SPLICE_FRAGMENT_RE.search(text) or any("malformed_nominalization" in flag for flag in flags):
        codes.extend(flag for flag in flags if "malformed" in flag or "nominalization" in flag)
        codes.append("unsafe_koto_splice")
        signal = PhraseSurfaceShapeSignal(
            shape="unsafe_koto_splice",
            safe_for_direct_koto_attachment=False,
            safe_for_relation_line=False,
            requires_surface_compression=False,
            requires_drop_or_defer=True,
            warning_codes=_dedupe(codes),
        )
        return signal.as_meta()

    if _ANALYTIC_OR_SYSTEM_REGISTER_RE.search(text):
        signal = PhraseSurfaceShapeSignal(
            shape="analytic_or_system_register",
            safe_for_direct_koto_attachment=False,
            safe_for_relation_line=False,
            requires_surface_compression=True,
            requires_drop_or_defer=True,
            warning_codes=("analytic_or_system_register",),
        )
        return signal.as_meta()

    if _OBLIGATION_OR_SCHEDULE_RE.search(joined):
        signal = PhraseSurfaceShapeSignal(
            shape="obligation_or_schedule",
            safe_for_direct_koto_attachment=False,
            safe_for_relation_line=True,
            requires_surface_compression=True,
            warning_codes=("direct_koto_attachment_blocked",),
        )
        return signal.as_meta()

    if _PREDICTION_OR_CAPACITY_RE.search(joined):
        signal = PhraseSurfaceShapeSignal(
            shape="prediction_or_capacity",
            safe_for_direct_koto_attachment=False,
            safe_for_relation_line=True,
            requires_surface_compression=True,
            warning_codes=("prediction_koto_attachment_blocked",),
        )
        return signal.as_meta()

    if _RELATIONSHIP_ACTION_RE.search(joined):
        long_relation = len(compact) >= 18 or len(raw_compact) >= 24
        signal = PhraseSurfaceShapeSignal(
            shape="relationship_action",
            safe_for_direct_koto_attachment=not long_relation,
            safe_for_relation_line=True,
            requires_surface_compression=long_relation,
            warning_codes=("relationship_action_compressed",) if long_relation else tuple(),
        )
        return signal.as_meta()

    if len(compact) >= 34 or len(raw_compact) >= 42:
        signal = PhraseSurfaceShapeSignal(
            shape="long_raw_clause",
            safe_for_direct_koto_attachment=False,
            safe_for_relation_line=True,
            requires_surface_compression=True,
            warning_codes=("long_raw_clause_compressed",),
        )
        return signal.as_meta()

    if compact.endswith(_SAFE_NOMINAL_ENDINGS):
        signal = PhraseSurfaceShapeSignal(
            shape="safe_nominalized_event",
            safe_for_direct_koto_attachment=True,
            safe_for_relation_line=True,
        )
        return signal.as_meta()

    signal = PhraseSurfaceShapeSignal(
        shape="feeling_state",
        safe_for_direct_koto_attachment=False,
        safe_for_relation_line=True,
        requires_surface_compression=False,
    )
    return signal.as_meta()


def compress_phrase_for_relation_surface(
    phrase: Any,
    *,
    raw_text: Any = "",
    role: Any = "",
    quality_flags: Iterable[Any] | Any = (),
    shape_meta: Mapping[str, Any] | None = None,
) -> str:
    """Return a safe relation-line phrase, or an empty string when deferred.

    This is a grammar-surface compression helper, not a fixed observation
    fallback.  It does not add a completed observation sentence and it never
    returns diagnostic text.
    """

    meta = dict(shape_meta or classify_phrase_surface_shape(phrase, raw_text=raw_text, role=role, quality_flags=quality_flags))
    shape = str(meta.get("shape") or "unknown").strip()
    text = _clean(phrase)
    compact = _compact_surface(text)
    raw_compact = _compact_surface(raw_text)
    joined = compact + raw_compact
    if not text or shape in {"unsafe_koto_splice", "analytic_or_system_register", "unknown"} and bool(meta.get("requires_drop_or_defer")):
        return ""

    if shape == "prediction_or_capacity":
        if "キャパオーバー" in joined and "予感" in joined:
            return "キャパオーバーしそうな予感"
        cleaned = re.sub(r"(?:がある)?こと$", "", text).strip(" 　、,。")
        cleaned = cleaned.replace("予感こと", "予感").replace("気配こと", "気配")
        if cleaned.endswith(("予感", "気配")):
            return cleaned
        if "予感" in joined:
            return "予感"
        if "気配" in joined:
            return "気配"
        if "失敗" in joined and "不安" in joined:
            return "失敗しそうで不安な感覚"
        if "失敗" in joined:
            return "失敗しそうな感覚"
        if "不安" in joined:
            return "不安が近づいている感覚"
        return "負荷が近づいている感覚"

    if shape == "obligation_or_schedule":
        if "コミュニケーション" in joined or "関わ" in joined or "連絡" in joined or "仲間" in joined:
            return "人との関わりの負荷"
        if "イベント" in joined and ("予定" in joined or "出" in joined or "顔を出" in joined):
            return "イベント予定の近さ"
        if "予定" in joined and ("集中" in joined or "詰ま" in joined):
            cleaned = re.sub(r"(?:こと|があること)$", "", text).strip(" 　、,。")
            return cleaned or "予定が詰まっていること"
        if "予定" in joined or "締切" in joined or "期日" in joined:
            return "予定の近さ"
        if "必要" in joined or "なければ" in joined or "しないと" in joined:
            return "必要なことの近さ"
        return "やることの近さ"

    if shape == "relationship_action":
        if "コミュニケーション" in joined or "関わ" in joined or "連絡" in joined or "仲間" in joined:
            return "人との関わり"
        return re.sub(r"(?:こと|があること)$", "", text).strip(" 　、,。") or "人との関わり"

    if shape == "long_raw_clause":
        if "キャパオーバー" in joined and "予感" in joined:
            return "キャパオーバーしそうな予感"
        if "コミュニケーション" in joined or "関わ" in joined or "連絡" in joined or "仲間" in joined:
            return "人との関わりの負荷"
        if "予定" in joined or "締切" in joined or "期日" in joined:
            return "予定の近さ"
        cleaned = re.sub(r"(?:こと|があること)$", "", text).strip(" 　、,。")
        if cleaned and len(_compact_surface(cleaned)) <= 24:
            return cleaned
        return ""

    cleaned = text.replace("予感こと", "予感").replace("気配こと", "気配")
    cleaned = re.sub(r"(こと){2,}$", "こと", cleaned).strip(" 　、,。")
    return cleaned


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def normalize_relation_surface_type(value: Any) -> str:
    relation = re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")
    return _RELATION_TYPE_ALIASES.get(relation, relation or "unknown")


def _dedupe(values: Iterable[Any]) -> Tuple[str, ...]:
    out: list[str] = []
    for raw in values or ():
        item = str(raw or "").strip()
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _expected_relation_types(values: Iterable[Any] | Any = ()) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        values = (values,)
    return _dedupe(normalize_relation_surface_type(value) for value in values)


def _pattern_hits(text: str, patterns: Sequence[tuple[str, str]]) -> Tuple[str, ...]:
    return _dedupe(key for key, pattern in patterns if re.search(pattern, text))


def detect_relation_surface(text: Any, expected_relation_types: Iterable[Any] | Any = ()) -> dict[str, Any]:
    """Detect relation surface cues in generated candidate text.

    Recovery is strict: when recovery is expected, generic cues alone are not
    enough.  This preserves Reader Gate safety and avoids passing on a bare word
    such as "関係" or "回復".
    """

    candidate = _clean(text)
    expected = _expected_relation_types(expected_relation_types)
    expects_recovery = "recovery" in expected
    generic_keys = _pattern_hits(candidate, GENERIC_RELATION_SURFACE_PATTERNS)
    recovery_keys = _pattern_hits(candidate, RECOVERY_RELATION_SURFACE_PATTERNS)

    keys: list[str] = []
    relation_types: list[str] = []
    if recovery_keys:
        keys.extend(recovery_keys)
        relation_types.append("recovery")
    if generic_keys and not expects_recovery:
        keys.extend(generic_keys)
        if expected:
            relation_types.extend(rt for rt in expected if rt != "unknown")
        else:
            relation_types.append("generic")

    signal = RelationSurfaceSignal(
        detected=bool(keys),
        count=len(_dedupe(keys)),
        keys=_dedupe(keys),
        relation_types=_dedupe(relation_types),
    )
    meta = signal.as_meta()
    meta.update(
        {
            "expected_relation_types": list(expected),
            "generic_relation_signal_keys": list(generic_keys),
            "recovery_relation_signal_keys": list(recovery_keys),
        }
    )
    return meta


def _context_flag(context_flags: Mapping[str, Any] | None, key: str) -> bool:
    if not isinstance(context_flags, Mapping):
        return False
    value = context_flags.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in _CONTEXT_TRUE_VALUES


def relation_marker_key(relation_type: Any, context_flags: Mapping[str, Any] | None = None) -> str:
    relation = normalize_relation_surface_type(relation_type)
    if relation == "recovery":
        if _context_flag(context_flags, "prior_load_present"):
            return "recovery_load_bridge_v1"
        return "recovery_connected_flow_v1"
    if relation:
        return f"{relation}_relation_marker_v1"
    return "generic_relation_marker_v1"


def relation_marker_phrase(relation_type: Any, context_flags: Mapping[str, Any] | None = None) -> str:
    """Return a short relation marker phrase for Self-Repair.

    This is a relation-surface grammar part, not a fixed fallback observation.
    It only clarifies an already declared relation type.
    """

    relation = normalize_relation_surface_type(relation_type)
    if relation == "recovery":
        if _context_flag(context_flags, "prior_load_present"):
            return "戻ってくる動きとその前の重さが同じ流れの中でつながっています。"
        return "戻る流れが、前の流れと切り離されずにつながっています。"
    if relation == "contrast":
        return "別々の向きが片方だけに寄らず、同じ場所に並んでいます。"
    if relation == "coexistence":
        return "別々の向きが同じ場所に残っています。"
    if relation == "pressure":
        return "圧力として前面に出ていることも残っています。"
    if relation == "approach_avoidance":
        return "近づく動きと止まる動きの両方が同じ線上に残っています。"
    if relation == "residue":
        return "あとに残る余韻として、前の流れとつながっています。"
    return "根拠のある範囲の関係だけを同じ流れの中に置いています。"


def relation_marker_meta(relation_type: Any, context_flags: Mapping[str, Any] | None = None) -> dict[str, Any]:
    relation = normalize_relation_surface_type(relation_type)
    phrase = relation_marker_phrase(relation, context_flags=context_flags)
    return {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "relation_type": relation,
        "relation_marker_key": relation_marker_key(relation, context_flags=context_flags),
        "relation_marker_phrase": phrase,
        "relation_marker_signal": detect_relation_surface(phrase, expected_relation_types=(relation,)),
        "meaning_added": False,
        "raw_input_included": False,
        "gate_relaxed": False,
    }


def build_relation_surface_contract_meta() -> dict[str, Any]:
    return {
        "version": RELATION_SURFACE_CONTRACT_VERSION,
        "contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "generic_relation_cue_keys": [key for key, _ in GENERIC_RELATION_SURFACE_PATTERNS],
        "recovery_relation_cue_keys": [key for key, _ in RECOVERY_RELATION_SURFACE_PATTERNS],
        "recovery_marker_key": relation_marker_key("recovery", {"prior_load_present": True}),
        "strict_matching": True,
        "relation_word_alone_passes": False,
        "phrase_surface_shape_version": PHRASE_SURFACE_SHAPE_VERSION,
        "phrase_surface_shape_classifier_available": True,
        "direct_koto_attachment_safe_by_default": False,
        "raw_input_included": False,
    }


__all__ = [
    "GENERIC_RELATION_SURFACE_PATTERNS",
    "RECOVERY_RELATION_SURFACE_PATTERNS",
    "RELATION_SURFACE_CONTRACT_VERSION",
    "PHRASE_SURFACE_SHAPE_VERSION",
    "RAW_INPUT_META_KEYS",
    "RelationSurfaceSignal",
    "PhraseSurfaceShapeSignal",
    "build_relation_surface_contract_meta",
    "classify_phrase_surface_shape",
    "compress_phrase_for_relation_surface",
    "detect_relation_surface",
    "normalize_relation_surface_type",
    "relation_marker_key",
    "relation_marker_meta",
    "relation_marker_phrase",
]
