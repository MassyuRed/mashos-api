# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step8 PhraseUnit Grammar Normalizer for EmlisAI Runtime Surface Quality.

The normalizer runs at material/PhraseUnit level. It only fixes grammar-safe
nominalization fragments (for example ``離れこと`` -> ``離れること``), or
classifies unsafe fragments as drop/defer. It never adds unsupported meaning,
never changes public response keys, and exports meta-only diagnostics without
raw input or public comment_text bodies.
"""

from dataclasses import dataclass, field as dataclass_field
import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Tuple

PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION = "emlis.phrase_unit_grammar_normalizer.v1"
PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION = "emlis.phrase_unit_grammar_normalization.v1"
PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP = "Step8_PhraseUnit_Grammar_Normalizer"
PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE = "phrase_unit_grammar_normalizer"

KEEP = "keep"
REPHRASE = "rephrase"
DROP = "drop"
DEFER = "defer"

_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"
_SPACE_RE = re.compile(r"\s+")
_COMPACT_RE = re.compile(r"[\s\n\r\t 　、,。.!！?？『』\"'「」（）()\[\]【】]+")

_EMOTION_LABELS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "安心", "自己理解", "恐れ", "焦り"}
_CONNECTOR_ONLY = {
    "けど", "けどさ", "けれど", "だけど", "だけどさ", "でも", "でもさ",
    "のに", "から", "ので", "なら", "すると", "したら", "それだと", "だと",
    "ただ", "それで", "普通に",
}
_SAFE_NOMINAL_SUFFIXES = ("こと", "気持ち", "感覚", "怖さ", "しんどさ", "つらさ", "不安", "願い", "限界", "流れ", "状態")
_ORPHAN_PARTICLE_RE = re.compile(r"(?:を|が|は|に|で|へ|まで|より)$")
_UNFINISHED_SUFFIX_RE = re.compile(
    r"(?:なんであ|考え始め|現実と|自分のことを|普通に|それだと|だと|"
    r"けどさ|だけどさ|でもさ|けど|けれど|だけど|でも|のに|から|ので|なら|すると|したら)$"
)
_STEM_KOTO_REPLACEMENTS: tuple[tuple[str, str, str], ...] = (
    ("stem_koto_hanareru", "離れこと", "離れること"),
    ("stem_koto_wakareru", "分かれこと", "分かれること"),
    ("stem_koto_hazureru", "外れこと", "外れること"),
    ("stem_koto_kuzureru", "崩れこと", "崩れること"),
    ("stem_koto_yureru", "揺れこと", "揺れること"),
    ("stem_koto_nagareru", "流れこと", "流れること"),
    ("stem_koto_nigeru", "逃げこと", "逃げること"),
    ("stem_koto_modoreru", "戻れこと", "戻れること"),
    ("stem_koto_mukaeru", "向かえこと", "向かえること"),
    ("stem_koto_kawareru", "変われこと", "変われること"),
    ("stem_koto_tonoeru", "整えこと", "整えること"),
    ("stem_koto_tameru", "貯めこと", "貯めること"),
    ("stem_koto_kimeru", "決めこと", "決めること"),
    ("stem_koto_hajimeru", "始めこと", "始めること"),
    ("stem_koto_tayoru", "頼りこと", "頼ること"),
    ("stem_koto_ganbaru", "頑張りこと", "頑張ること"),
    ("stem_koto_tanoshimu", "楽しみこと", "楽しむこと"),
    ("stem_koto_mamoru", "守りこと", "守ること"),
    ("stem_koto_erabu", "選びこと", "選ぶこと"),
    ("stem_koto_susumu", "進みこと", "進むこと"),
)
_STEM_END_REPLACEMENTS: tuple[tuple[str, str, str], ...] = (
    ("unfinished_stem_hanareru", "離れ", "離れる"),
)
_BROKEN_NOMINALIZATION_RE = re.compile(
    r"(?:離れ|分かれ|外れ|崩れ|揺れ|流れ|逃げ|戻れ|向かえ|変われ|整え|貯め|決め|始め|頼り|頑張り|楽しみ|守り|選び|進み)こと"
)
_PARTICLE_BEFORE_KOTO_RE = re.compile(r"(?:を|が|は|に|で|へ|まで|より)こと")
_AUXILIARY_FRAGMENT_KOTO_RE = re.compile(r"(?:なっ|し|見え|残っ|重なっ)こと(?:も|が|は|に|$)")
_RAW_FRAGMENT_NOMINAL_RE = re.compile(r"(?:自分のことをこと|普通にこと|現実こと|なんであこと|考え始めこと|けどこと|でもこと|のにこと|からこと)$")

# Step3: fatal malformed nominalization fragments observed in the shallow
# current-input path.  These are material/phrase-unit patterns, not screenshot
# special cases and not user-facing replacement templates.
_MALFORMED_NOMINALIZATION_FRAGMENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "malformed_nominalization_temporal_fragment",
        re.compile(r"(?:今まで|これまで|さっき|先ほど|さきほど|このまま|まだ)こと(?:$|[もがはに])"),
    ),
    (
        "malformed_nominalization_adjective_fragment",
        re.compile(r"(?:大丈夫|平気|普通|不安定|曖昧|中途半端|好き|嫌い|上手|下手)こと(?:$|[もがはに])"),
    ),
    (
        "malformed_nominalization_question_fragment",
        re.compile(r"(?:ないか|どれ|どこ|なに|何|なんで|どうして)こと(?:$|[もがはに])"),
    ),
    (
        "malformed_nominalization_auxiliary_fragment",
        re.compile(r"(?:(?<!かも)しれない(?:どれ|どこ|なに|何)?|なっ|し|見え|残っ|重なっ)こと(?:$|[もがはに])"),
    ),
    (
        "malformed_nominalization_te_form_fragment",
        re.compile(r"(?:なくて|ないで|なれなくて|できなくて|ならなくて|なせなくて|しきれなくて)こと(?:$|[もがはに])"),
    ),
    (
        "malformed_nominalization_tari_fragment",
        re.compile(r"たりこと(?:$|[もがはにをでへ])"),
    ),
    (
        "malformed_nominalization_conditional_fragment",
        re.compile(
            r"(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|"
            r"行かなければ|出なければ|やらなければ|取らなければ)こと(?:$|[もがはにをでへ])"
        ),
    ),
    (
        "malformed_nominalization_prediction_noun_fragment",
        re.compile(r"(?:予感|気配|予定|必要|つもり|はず|可能性|見込み|感じ)こと(?:$|[もがはにをでへ])"),
    ),
    (
        "residual_koto_splice_fragment",
        re.compile(r"(?:ことこと|(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|行かなければ|出なければ|やらなければ|取らなければ)こと|予感こと|気配こと|予定こと|必要こと|つもりこと|はずこと|可能性こと|見込みこと|感じこと)(?:$|[もがはにをでへ])"),
    ),
    (
        "long_clause_koto_attachment_risk",
        re.compile(
            r".{18,}(?:(?:なければ|なきゃ|ないと|しないと|しなくては|せねば)こと|"
            r"(?:予感|気配|予定|必要|可能性|見込み)こと)(?:$|[もがはにをでへ])"
        ),
    ),
    (
        "malformed_nominalization_unknown_fragment",
        re.compile(r"しれない(?:どれ|どこ|なに|何)こと(?:$|[もがはに])"),
    ),
)
_FATAL_MALFORMED_NOMINALIZATION_CODES = {code for code, _pattern in _MALFORMED_NOMINALIZATION_FRAGMENT_PATTERNS}
_BROKEN_FEELING_RE = re.compile(r"(?:だ|だから|けど|けれど|から)(?:気持ち|思い|願い|状態)$")
_HALF_WAY_RE = re.compile(r"中途半端(?:だ|だから)(?:気持ち|状態)?$")

_FORBIDDEN_META_TEXT_KEYS = {
    "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
    "input", "input_text", "inputText", "user_input", "userInput", "memo", "memo_text",
    "memoText", "current_input", "currentInput", "comment_text", "commentText",
    "public_comment_text", "candidate_comment_text", "reply_text", "replyText",
    "surface_text", "realized_text", "body", "text", "phrase", "normalized_text",
    "original_text", "raw_quote",
}
_FORBIDDEN_TRUE_FLAGS = (
    "raw_input_included", "raw_text_included", "comment_text_included", "comment_text_body_included",
    "unsupported_completion_added", "unsupported_complement_added", "meaning_added",
    "gate_relaxed", "display_gate_relaxed", "grounding_gate_relaxed", "template_gate_relaxed",
    "reader_gate_relaxed", "public_response_key_change", "api_route_changed", "db_physical_name_changed",
    "rn_visible_contract_changed", "fixed_sentence_template_added", "input_specific_template_used",
    "external_ai_used", "local_llm_used", "product_gate_achieved", "public_release_applied",
)


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _compact(value: Any) -> str:
    return _COMPACT_RE.sub("", str(value or ""))


def _dedupe(values: Iterable[Any] | Any | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        src: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        src = values
    else:
        src = [values]
    out: list[str] = []
    seen: set[str] = set()
    for raw in src:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def _contains_forbidden_meta_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_META_TEXT_KEYS:
                return True
            if _contains_forbidden_meta_text_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_meta_text_key(item) for item in value)
    return False


def assert_phrase_unit_grammar_normalizer_meta_only(
    value: Mapping[str, Any], *, source: str = PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE
) -> None:
    if _contains_forbidden_meta_text_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include raw/material text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")


def _malformed_nominalization_fragment_codes(compact: str) -> tuple[str, ...]:
    codes: list[str] = []
    for code, pattern in _MALFORMED_NOMINALIZATION_FRAGMENT_PATTERNS:
        if pattern.search(compact) and code not in codes:
            codes.append(code)
    return tuple(codes)


def _warning_codes_for(text: Any) -> tuple[str, ...]:
    phrase = _clean(text)
    compact = _compact(phrase)
    codes: list[str] = []
    if not compact:
        return ("empty_phrase_unit_material",)
    if compact in {_compact(label) for label in _EMOTION_LABELS}:
        codes.append("emotion_label_only")
    if compact in _CONNECTOR_ONLY:
        codes.extend(["connector_only_material", "unfinished_phrase"])
    codes.extend(_malformed_nominalization_fragment_codes(compact))
    if _BROKEN_NOMINALIZATION_RE.search(phrase):
        codes.append("malformed_nominalization_missing_ru")
    if _PARTICLE_BEFORE_KOTO_RE.search(phrase):
        codes.append("malformed_nominalization_particle_before_koto")
    if _AUXILIARY_FRAGMENT_KOTO_RE.search(phrase):
        codes.append("malformed_nominalization_auxiliary_fragment")
    if _RAW_FRAGMENT_NOMINAL_RE.search(compact):
        codes.extend(["raw_fragment_centered_as_nominal", "unfinished_phrase"])
    if _BROKEN_FEELING_RE.search(phrase):
        codes.append("broken_nominalized_feeling_phrase")
    safe_suffix = compact.endswith(_SAFE_NOMINAL_SUFFIXES)
    if not safe_suffix and _UNFINISHED_SUFFIX_RE.search(compact):
        codes.append("unfinished_phrase")
    if not safe_suffix and _ORPHAN_PARTICLE_RE.search(compact):
        codes.extend(["orphan_particle", "orphan_particle_tail"])
    if compact.endswith("離れ"):
        codes.extend(["unfinished_stem_fragment", "unfinished_stem_hanareru"])
    return tuple(dict.fromkeys(codes))


def grammar_warning_codes_for_phrase(value: Any) -> tuple[str, ...]:
    """Public helper for signature/surface modules; no text is returned."""
    return _warning_codes_for(value)


def _repair_stem_koto(text: str) -> tuple[str, tuple[str, ...]]:
    out = _clean(text)
    codes: list[str] = []
    for code, before, after in _STEM_KOTO_REPLACEMENTS:
        if before in out:
            out = out.replace(before, after)
            codes.extend(["malformed_nominalization_missing_ru", code])
    return out, tuple(dict.fromkeys(codes))


def _repair_stem_ending(text: str) -> tuple[str, tuple[str, ...]]:
    out = _clean(text)
    codes: list[str] = []
    for code, before, after in _STEM_END_REPLACEMENTS:
        if out.endswith(before) and not out.endswith(after):
            out = out[: -len(before)] + after
            codes.extend(["unfinished_stem_fragment", code])
    return out, tuple(dict.fromkeys(codes))


def _repair_broken_feeling(text: str) -> tuple[str, tuple[str, ...]]:
    out = _clean(text)
    codes: list[str] = []
    if _HALF_WAY_RE.search(out):
        out = _HALF_WAY_RE.sub("中途半端に感じていること", out)
        codes.append("broken_nominalized_feeling_phrase")
    elif _BROKEN_FEELING_RE.search(out):
        out = re.sub(r"(?:だ|だから|けど|けれど|から)(気持ち|思い|願い|状態)$", r"という\1", out)
        codes.append("broken_nominalized_feeling_phrase")
    return out, tuple(codes)


@dataclass(frozen=True)
class PhraseUnitGrammarNormalizationResult:
    original_text: str
    normalized_text: str
    action: str
    warning_codes: Iterable[str] = dataclass_field(default_factory=tuple)
    phrase_unit_id: str = ""
    evidence_span_id: str = ""
    role: str = ""
    must_keep: bool = False
    source_field: str = ""
    schema_version: str = PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        original = _clean(self.original_text, limit=160)
        normalized = _clean(self.normalized_text, limit=160)
        codes = tuple(_dedupe(self.warning_codes))
        action = _clean(self.action) or (KEEP if not codes else DROP)
        if action not in {KEEP, REPHRASE, DROP, DEFER}:
            action = DROP if codes else KEEP
        if action in {KEEP, REPHRASE} and not normalized:
            normalized = original
        if action in {DROP, DEFER}:
            normalized = ""
        object.__setattr__(self, "original_text", original)
        object.__setattr__(self, "normalized_text", normalized)
        object.__setattr__(self, "warning_codes", codes)
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "role", _clean(self.role))
        object.__setattr__(self, "must_keep", bool(self.must_keep))
        object.__setattr__(self, "source_field", _clean(self.source_field))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION)

    @property
    def changed(self) -> bool:
        return self.normalized_text != self.original_text

    @property
    def usable(self) -> bool:
        return self.action in {KEEP, REPHRASE} and bool(self.normalized_text)

    @property
    def blocked(self) -> bool:
        return self.action in {DROP, DEFER}

    @property
    def drop_reasons(self) -> tuple[str, ...]:
        return self.warning_codes if self.action == DROP else tuple()

    @property
    def defer_reasons(self) -> tuple[str, ...]:
        return self.warning_codes if self.action == DEFER else tuple()

    @property
    def grammar_warning_major(self) -> bool:
        return bool(self.warning_codes) and self.blocked

    def as_meta(self, *, include_text: bool = False) -> dict[str, Any]:
        data = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "source": PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE,
            "source_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
            "step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
            "target_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
            "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
            "phrase_unit_grammar_normalizer_ready": True,
            "step8_phrase_unit_grammar_normalizer_ready": True,
            "phrase_unit_grammar_action": self.action,
            "grammar_normalizer_action": self.action,
            "action": self.action,
            "phrase_unit_grammar_rephrased": self.action == REPHRASE,
            "phrase_unit_grammar_deferred": self.action == DEFER,
            "phrase_unit_grammar_dropped": self.action == DROP,
            "grammar_warning_codes": list(self.warning_codes),
            "surface_grammar_warning_codes": list(self.warning_codes),
            "phrase_unit_grammar_warning_codes": list(self.warning_codes),
            "grammar_warning_count": len(tuple(self.warning_codes)),
            "surface_grammar_warning_count": len(tuple(self.warning_codes)),
            "phrase_unit_grammar_warning_count": len(tuple(self.warning_codes)),
            "grammar_warning_major": self.grammar_warning_major,
            "malformed_nominalization_risk": any(
                "nominal" in code or "stem_koto" in code or "koto_splice" in code or "koto_attachment" in code
                for code in self.warning_codes
            ),
            "malformed_nominalization_guard_version": "emlis.phrase_unit_malformed_nominalization_guard.v1",
            "malformed_nominalization_guard_enabled": True,
            "malformed_phrase_unit_guard_enabled": True,
            "malformed_phrase_unit_count": len([
                code for code in self.warning_codes
                if "nominalization" in code or "stem_koto" in code or "malformed" in code or "koto_splice" in code or "koto_attachment" in code
            ]),
            "malformed_nominalization_temporal_fragment_guarded": "malformed_nominalization_temporal_fragment" in self.warning_codes,
            "malformed_nominalization_adjective_fragment_guarded": "malformed_nominalization_adjective_fragment" in self.warning_codes,
            "malformed_nominalization_question_fragment_guarded": "malformed_nominalization_question_fragment" in self.warning_codes,
            "malformed_nominalization_auxiliary_fragment_guarded": "malformed_nominalization_auxiliary_fragment" in self.warning_codes,
            "malformed_nominalization_te_form_fragment_guarded": "malformed_nominalization_te_form_fragment" in self.warning_codes,
            "malformed_nominalization_tari_fragment_guarded": "malformed_nominalization_tari_fragment" in self.warning_codes,
            "malformed_nominalization_conditional_fragment_guarded": "malformed_nominalization_conditional_fragment" in self.warning_codes,
            "malformed_nominalization_prediction_noun_fragment_guarded": "malformed_nominalization_prediction_noun_fragment" in self.warning_codes,
            "residual_koto_splice_fragment_guarded": "residual_koto_splice_fragment" in self.warning_codes,
            "long_clause_koto_attachment_risk_guarded": "long_clause_koto_attachment_risk" in self.warning_codes,
            "malformed_nominalization_unknown_fragment_guarded": "malformed_nominalization_unknown_fragment" in self.warning_codes,
            "orphan_particle_risk": "orphan_particle" in self.warning_codes,
            "unfinished_phrase_risk": "unfinished_phrase" in self.warning_codes or "unfinished_stem_fragment" in self.warning_codes,
            "phrase_unit_id_present": bool(self.phrase_unit_id),
            "evidence_span_id_present": bool(self.evidence_span_id),
            "role_present": bool(self.role),
            "source_field_present": bool(self.source_field),
            "must_keep": bool(self.must_keep),
            "must_keep_deferred": self.action == DEFER and bool(self.must_keep),
            "must_keep_deferred_not_dropped": self.action == DEFER and bool(self.must_keep),
            "must_keep_dropped": False,
            "drop_allowed": self.action == DROP and not self.must_keep,
            "defer_allowed": self.action == DEFER and self.must_keep,
            "repair_allowed": self.action == REPHRASE,
            "unsupported_completion_added": False,
            "unsupported_complement_added": False,
            "meaning_added": False,
            "fixed_sentence_template_added": False,
            "input_specific_template_used": False,
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "comment_text_contract": "passed_only",
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "gate_relaxed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "product_gate_achieved": False,
            "public_release_applied": False,
        }
        if include_text:
            data["original_text"] = self.original_text
            data["normalized_text"] = self.normalized_text
        else:
            data["original_text_included"] = False
            data["normalized_text_included"] = False
            data["original_text_length"] = len(self.original_text)
            data["normalized_text_length"] = len(self.normalized_text)
            assert_phrase_unit_grammar_normalizer_meta_only(data)
        return data


def detect_phrase_unit_grammar_warning_codes_for_text(text: Any) -> tuple[str, ...]:
    """Return grammar warning codes for a text fragment without repairing it."""
    return _warning_codes_for(text)


def normalize_phrase_unit_grammar(
    phrase: Any,
    *,
    raw_text: Any = "",
    role: str = "",
    must_keep: bool = False,
    phrase_unit_id: str = "",
    evidence_span_id: str = "",
    source_field: str = "",
    source: str = "",
) -> PhraseUnitGrammarNormalizationResult:
    """Normalize a PhraseUnit material fragment without adding new meaning."""
    original = _clean(phrase, limit=160)
    warning_codes: list[str] = list(_warning_codes_for(original))
    normalized = original
    normalized, stem_koto_codes = _repair_stem_koto(normalized)
    warning_codes.extend(stem_koto_codes)
    normalized, stem_end_codes = _repair_stem_ending(normalized)
    warning_codes.extend(stem_end_codes)
    normalized, feeling_codes = _repair_broken_feeling(normalized)
    warning_codes.extend(feeling_codes)
    remaining_codes = list(_warning_codes_for(normalized))
    effective_codes = list(dict.fromkeys([*warning_codes, *remaining_codes]))
    blocking_remaining = [
        code for code in remaining_codes
        if code in {
            "empty_phrase_unit_material",
            "emotion_label_only",
            "connector_only_material",
            "unfinished_phrase",
            "orphan_particle",
            "malformed_nominalization_particle_before_koto",
            "malformed_nominalization_auxiliary_fragment",
            "raw_fragment_centered_as_nominal",
            *_FATAL_MALFORMED_NOMINALIZATION_CODES,
        }
    ]
    if not effective_codes:
        action = KEEP
    elif normalized != original and not blocking_remaining:
        action = REPHRASE
    elif must_keep:
        action = DEFER
        if "must_keep_deferred" not in effective_codes:
            effective_codes.append("must_keep_deferred")
        if "must_keep_deferred_not_dropped" not in effective_codes:
            effective_codes.append("must_keep_deferred_not_dropped")
    else:
        action = DROP
    return PhraseUnitGrammarNormalizationResult(
        original_text=original,
        normalized_text=normalized if action in {KEEP, REPHRASE} else "",
        action=action,
        warning_codes=tuple(dict.fromkeys(effective_codes)),
        phrase_unit_id=_clean(phrase_unit_id),
        evidence_span_id=_clean(evidence_span_id),
        role=_clean(role),
        must_keep=must_keep,
        source_field=_clean(source_field or source),
    )


def collect_phrase_unit_grammar_warning_codes(*values: Any) -> tuple[str, ...]:
    codes: list[str] = []

    def visit(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, PhraseUnitGrammarNormalizationResult):
            codes.extend(item.warning_codes)
            return
        if isinstance(item, Mapping):
            for key in ("grammar_warning_codes", "surface_grammar_warning_codes", "phrase_unit_grammar_warning_codes"):
                raw = item.get(key)
                if isinstance(raw, (list, tuple, set)):
                    codes.extend(raw)
                elif isinstance(raw, str):
                    codes.append(raw)
            for key in ("phrase_unit_grammar_normalizer", "phrase_unit_grammar_normalizer_report", "rows", "materials", "rejected_rows", "meta"):
                nested = item.get(key)
                if nested is not item:
                    visit(nested)
            return
        if isinstance(item, (list, tuple, set)):
            for sub in item:
                visit(sub)

    if len(values) == 1:
        visit(values[0])
    else:
        for value in values:
            visit(value)
    return _dedupe(codes)


def summarize_phrase_unit_grammar_normalizer(rows: Sequence[Any] | Mapping[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(rows, Mapping):
        source_rows: Sequence[Any] = [rows]
    else:
        source_rows = list(rows or ())
    action_counts = {KEEP: 0, REPHRASE: 0, DROP: 0, DEFER: 0}
    row_meta: list[dict[str, Any]] = []
    for row in source_rows:
        if isinstance(row, PhraseUnitGrammarNormalizationResult):
            action_counts[row.action] = action_counts.get(row.action, 0) + 1
            row_meta.append(row.as_meta())
        elif isinstance(row, Mapping):
            action = _clean(row.get("phrase_unit_grammar_action") or row.get("action"))
            if action in action_counts:
                action_counts[action] = action_counts.get(action, 0) + 1
            row_meta.append({k: v for k, v in row.items() if k not in _FORBIDDEN_META_TEXT_KEYS})
    codes = collect_phrase_unit_grammar_warning_codes(row_meta)
    report = {
        "version": PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION,
        "schema_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION,
        "source": PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE,
        "source_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "phrase_unit_grammar_normalizer_ready": True,
        "step8_phrase_unit_grammar_normalizer_ready": True,
        "grammar_warning_codes": list(codes),
        "surface_grammar_warning_codes": list(codes),
        "phrase_unit_grammar_warning_codes": list(codes),
        "grammar_warning_count": len(codes),
        "surface_grammar_warning_count": len(codes),
        "phrase_unit_grammar_warning_count": len(codes),
        "grammar_warning_major": any(bool(row.get("grammar_warning_major")) for row in row_meta),
        "action_counts": action_counts,
        "rephrase_count": action_counts.get(REPHRASE, 0),
        "drop_count": action_counts.get(DROP, 0),
        "defer_count": action_counts.get(DEFER, 0),
        "must_keep_deferred_count": sum(1 for row in row_meta if bool(row.get("must_keep_deferred"))),
        "must_keep_dropped": False,
        "rows": row_meta,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "product_gate_achieved": False,
        "public_release_applied": False,
    }
    assert_phrase_unit_grammar_normalizer_meta_only(report)
    return report


def detect_phrase_unit_grammar_warning_codes_for_text(text: Any) -> tuple[str, ...]:
    """Detect Step8 grammar warning codes from one in-memory surface fragment."""
    result = normalize_phrase_unit_grammar(text, source="surface_signature_in_memory")
    return _dedupe(result.warning_codes)


def phrase_unit_grammar_normalizer_report_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, PhraseUnitGrammarNormalizationResult):
        return value.as_meta()
    if isinstance(value, Mapping):
        meta = {k: v for k, v in value.items() if k not in _FORBIDDEN_META_TEXT_KEYS}
        meta.setdefault("version", PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION)
        meta.setdefault("schema_version", PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION)
        meta.setdefault("source", PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE)
        meta.setdefault("source_step", PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP)
        meta.setdefault("step", PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP)
        meta.setdefault("phrase_unit_grammar_normalizer_version", PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION)
        meta.setdefault("raw_input_included", False)
        meta.setdefault("raw_text_included", False)
        meta.setdefault("comment_text_included", False)
        meta.setdefault("comment_text_body_included", False)
        assert_phrase_unit_grammar_normalizer_meta_only(meta)
        return meta
    return summarize_phrase_unit_grammar_normalizer([])


def as_phrase_unit_grammar_scorecard_event(value: Any) -> dict[str, Any]:
    meta = phrase_unit_grammar_normalizer_report_meta(value)
    event = {
        "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "phrase_unit_grammar_normalizer_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "step8_phrase_unit_grammar_normalizer_connected": True,
        "phrase_unit_grammar_action": meta.get("phrase_unit_grammar_action") or meta.get("action") or "unknown",
        "grammar_warning_codes": list(_dedupe(meta.get("grammar_warning_codes") or ())),
        "surface_grammar_warning_codes": list(_dedupe(meta.get("surface_grammar_warning_codes") or meta.get("grammar_warning_codes") or ())),
        "grammar_warning_count": int(meta.get("grammar_warning_count") or len(meta.get("grammar_warning_codes") or ())),
        "surface_grammar_warning_count": int(meta.get("surface_grammar_warning_count") or len(meta.get("surface_grammar_warning_codes") or meta.get("grammar_warning_codes") or ())),
        "grammar_warning_major": bool(meta.get("grammar_warning_major")),
        "malformed_nominalization_risk": bool(meta.get("malformed_nominalization_risk")),
        "must_keep_deferred": bool(meta.get("must_keep_deferred")),
        "must_keep_dropped": False,
        "unsupported_completion_added": False,
        "unsupported_complement_added": False,
        "meaning_added": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
    }
    assert_phrase_unit_grammar_normalizer_meta_only(event)
    return event


def build_phrase_unit_grammar_normalizer_contract_meta() -> dict[str, Any]:
    meta = {
        "version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "schema_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION,
        "source": PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE,
        "source_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "target_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "step8_phrase_unit_grammar_normalizer_added": True,
        "step8_phrase_unit_grammar_normalizer_ready": True,
        "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "runs_before_sentence_plan": True,
        "runs_before_surface_realizer": True,
        "material_stage_normalizer": True,
        "surface_text_repair_by_step8": False,
        "safe_nominalization_guard_enabled": True,
        "malformed_nominalization_guard_version": "emlis.phrase_unit_malformed_nominalization_guard.v1",
        "malformed_nominalization_guard_enabled": True,
        "stem_koto_guard_enabled": True,
        "orphan_particle_guard_enabled": True,
        "unfinished_phrase_guard_enabled": True,
        "raw_fragment_center_guard_enabled": True,
        "malformed_phrase_unit_guard_enabled": True,
        "malformed_nominalization_temporal_fragment_guard_enabled": True,
        "malformed_nominalization_adjective_fragment_guard_enabled": True,
        "malformed_nominalization_question_fragment_guard_enabled": True,
        "malformed_nominalization_auxiliary_fragment_guard_enabled": True,
        "malformed_nominalization_te_form_fragment_guard_enabled": True,
        "malformed_nominalization_tari_fragment_guard_enabled": True,
        "malformed_nominalization_conditional_fragment_guard_enabled": True,
        "malformed_nominalization_prediction_noun_fragment_guard_enabled": True,
        "residual_koto_splice_fragment_guard_enabled": True,
        "long_clause_koto_attachment_risk_guard_enabled": True,
        "malformed_nominalization_unknown_fragment_guard_enabled": True,
        "drop_rephrase_defer_supported": True,
        "must_keep_defer_not_drop": True,
        "grammar_warning_codes_connected": True,
        "grammar_warning_codes_to_signature": True,
        "grammar_warning_codes_to_scorecard": True,
        "unsupported_completion_added": False,
        "unsupported_complement_added": False,
        "meaning_added": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "product_gate_achieved": False,
        "public_release_applied": False,
    }
    assert_phrase_unit_grammar_normalizer_meta_only(meta)
    return meta


def dump_phrase_unit_grammar_normalizer_meta(meta: Mapping[str, Any] | None = None) -> str:
    data = dict(meta or build_phrase_unit_grammar_normalizer_contract_meta())
    data.setdefault("raw_input_included", False)
    data.setdefault("raw_text_included", False)
    data.setdefault("comment_text_included", False)
    data.setdefault("comment_text_body_included", False)
    assert_phrase_unit_grammar_normalizer_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "DEFER",
    "DROP",
    "KEEP",
    "PHRASE_UNIT_GRAMMAR_NORMALIZER_SCHEMA_VERSION",
    "PHRASE_UNIT_GRAMMAR_NORMALIZER_SOURCE",
    "PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP",
    "PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION",
    "REPHRASE",
    "PhraseUnitGrammarNormalizationResult",
    "as_phrase_unit_grammar_scorecard_event",
    "assert_phrase_unit_grammar_normalizer_meta_only",
    "build_phrase_unit_grammar_normalizer_contract_meta",
    "collect_phrase_unit_grammar_warning_codes",
    "detect_phrase_unit_grammar_warning_codes_for_text",
    "dump_phrase_unit_grammar_normalizer_meta",
    "detect_phrase_unit_grammar_warning_codes_for_text",
    "grammar_warning_codes_for_phrase",
    "normalize_phrase_unit_grammar",
    "phrase_unit_grammar_normalizer_report_meta",
    "summarize_phrase_unit_grammar_normalizer",
]
