# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 3 Material service for EmlisAI Complete Composer initial version.

This additive internal service converts source-grounded EvidenceSpan rows and
existing PhraseUnit-like rows into material units that later Complete Composer
steps can consume. It does not create user-facing ``comment_text`` and does not
change DB physical names, API routes, public response keys, or RN display
contracts.
"""

from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_STAGE
from emlis_ai_limited_composer_client import _compress_text
from emlis_ai_limited_relation_taxonomy import canonical_relation_type, normalize_relation_type, relation_family
from emlis_ai_limited_sentence_quality_guard import (
    judge_phrase_unit_material_quality,
    phase8_primary_role_for_text,
    phase8_role_meta,
    phase8_roles_for_text,
)
from emlis_ai_phrase_unit_grammar_normalizer import (
    DEFER as PHRASE_UNIT_GRAMMAR_DEFER,
    DROP as PHRASE_UNIT_GRAMMAR_DROP,
    KEEP as PHRASE_UNIT_GRAMMAR_KEEP,
    REPHRASE as PHRASE_UNIT_GRAMMAR_REPHRASE,
    PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
    PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
    build_phrase_unit_grammar_normalizer_contract_meta,
    collect_phrase_unit_grammar_warning_codes,
    normalize_phrase_unit_grammar,
    phrase_unit_grammar_normalizer_report_meta,
    summarize_phrase_unit_grammar_normalizer,
)

from emlis_ai_observation_material_connector import (
    build_material_focus_relation_connector,
    observation_material_connector_forward_meta,
)

COMPLETE_MATERIAL_SERVICE_VERSION = "emlis.complete_material_service.v1_step8"
COMPLETE_MATERIAL_SERVICE_BASE_VERSION = "emlis.complete_material_service.v1"
COMPLETE_MATERIAL_UNIT_SCHEMA_VERSION = "emlis.complete_material_unit.v1"
COMPLETE_MATERIAL_REJECTION_SCHEMA_VERSION = "emlis.complete_material_rejection.v1"
COMPLETE_MATERIAL_BUNDLE_SCHEMA_VERSION = "emlis.complete_material_bundle.v1"
COMPLETE_MATERIAL_STAGE = "Step3_Material_service"
COMPLETE_MATERIAL_SERVICE_STEP = COMPLETE_MATERIAL_STAGE
COMPLETE_MATERIAL_TARGET_STEP = COMPLETE_MATERIAL_STAGE
COMPLETE_MATERIAL_SERVICE_TARGET_STEP = COMPLETE_MATERIAL_STAGE
COMPLETE_MATERIAL_IMPLEMENTATION_UNIT = "Commit 3 + RuntimeSurfaceQuality Step8"
COMPLETE_MATERIAL_PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION = PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION
COMPLETE_MATERIAL_PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP = PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP
PHRASE_GRAMMAR_DEFER = PHRASE_UNIT_GRAMMAR_DEFER
PHRASE_GRAMMAR_DROP = PHRASE_UNIT_GRAMMAR_DROP
PHRASE_GRAMMAR_REPHRASE = PHRASE_UNIT_GRAMMAR_REPHRASE

COMPLETE_MATERIAL_STATUS_READY = "ready"
COMPLETE_MATERIAL_STATUS_UNAVAILABLE = "unavailable"

TEXT_SOURCE_FIELDS = {"memo", "memo_action", "text", "free_text", "typed_text", "input_summary"}
NON_TEXT_SOURCE_FIELDS = {"emotion_details", "emotions", "category", "selected_emotions"}
EMOTION_LABELS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "安心", "自己理解", "恐れ", "焦り"}
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

BLOCKING_MATERIAL_FLAGS = {
    "empty_phrase_unit_material",
    "emotion_label_only",
    "connector_only_material",
    "residual_nominal_material",
    "unfinished_phrase",
    "orphan_particle",
    "broken_nominalized_fragment",
    "too_long_quote",
    "too_short_phrase_unit_material",
    "non_text_material_source",
    "phrase_unit_grammar_dropped",
    "phrase_unit_grammar_deferred",
    "must_keep_deferred_not_dropped",
    "malformed_nominalization_missing_ru",
    "stem_koto_hanareru",
    "malformed_nominalization_particle_before_koto",
    "orphan_particle_tail",
    "unfinished_phrase_tail",
    "raw_fragment_centering_risk",
}

_SPACE_RE = re.compile(r"\s+")
_COMPACT_RE = re.compile(r"[\s\n\r\t 　、,。.!！?？『』\"'「」（）()\[\]【】]+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"
_UNFINISHED_TAIL_RE = re.compile(r"(?:けど|だけど|でも|のに|から|なら|すると|したら|普通に|考え始め|現実と|なんであ|を|が|で)$")
_CONNECTOR_ONLY_RE = re.compile(r"^(?:でも|だけど|けど|ただ|とはいえ|その中で|一方|なのに|からこそ|だからこそ)$")
_SAFETY_RE = re.compile(
    r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|ASD|PTSD|うつ|鬱|自律神経|依存症|医療|心理療法|心理学的|"
    r"人格|性格|本質|怠け|甘え|原因は|理由は|必要があります|すべきです|するべきです|しなければなりません|正解です|間違いです|あなたは|あなたの本質|あなたの性格",
    re.IGNORECASE,
)
_SAFETY_RISK_RE = re.compile(r"死にたい|消えたい|自殺|自傷|自分を傷つけたい|殺したい|OD|過量服薬|首を吊|首吊|飛び降り|リスカ|生きていたくない|生きるのをやめたい", re.IGNORECASE)

ROLE_RELATION_HINTS: tuple[tuple[set[str], str], ...] = (
    ({"wish_to_rely", "burden_fear", "rejection_fear"}, "approach_avoidance"),
    ({"fatigue_accumulation", "loss_of_control", "anticipation_loop", "avoidance_wish", "low_energy"}, "pressure"),
    ({"small_repair", "small_action", "achievement", "relieved_weight", "positive_state", "safe_home"}, "recovery"),
    ({"value_wish", "ordinary_life_wish", "known_action"}, "coexistence"),
    ({"anxiety_return", "fall_contrast", "reality_damage", "anger_surface", "unfairness", "hurt_core"}, "contrast"),
    ({"limit", "worsening_risk", "perfection_fear", "withdrawal"}, "residue"),
)

ROLE_KIND_HINTS: dict[str, str] = {
    "fatigue_accumulation": "pressure",
    "loss_of_control": "state",
    "anticipation_loop": "pressure",
    "perfection_fear": "fear",
    "limit": "limit",
    "reality_damage": "pressure",
    "worsening_risk": "pressure",
    "low_energy": "pressure",
    "positive_state": "recovery",
    "small_action": "recovery",
    "relieved_weight": "recovery",
    "achievement": "recovery",
    "small_repair": "recovery",
    "anxiety_return": "fear",
    "fall_contrast": "relation",
    "anger_surface": "state",
    "unfairness": "state",
    "hurt_core": "state",
    "withdrawal": "residue",
    "wish_to_rely": "wish",
    "burden_fear": "fear",
    "rejection_fear": "fear",
    "avoidance_wish": "wish",
    "ordinary_life_wish": "wish",
    "value_wish": "wish",
    "known_action": "state",
    "safe_home": "state",
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _compact(value: Any) -> str:
    return _COMPACT_RE.sub("", str(value or ""))


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    out: dict[str, Any] = {}
    for key in (
        "span_id",
        "evidence_span_id",
        "id",
        "raw_text",
        "text",
        "source_text",
        "source_field",
        "detected_type",
        "type",
        "start_index",
        "end_index",
        "confidence",
        "phrase_unit_id",
        "compressed_text",
        "material_text",
        "phrase",
        "role",
        "polarity",
        "must_keep",
        "relation_type",
        "quality_flags",
        "meta",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


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


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return _json_safe_mapping(value)
    if isinstance(value, (list, tuple, set)):
        return [_json_safe_value(item) for item in value]
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = _clean(key)
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out



def _observation_forward_meta(value: Any) -> dict[str, Any]:
    return observation_material_connector_forward_meta(value)


def _merge_observation_meta(*values: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        merged.update(_observation_forward_meta(value))
    return merged


def _safe_int(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _span_id(span: Mapping[str, Any]) -> str:
    return _clean(span.get("span_id") or span.get("evidence_span_id") or span.get("id"))


def _span_raw_text(span: Mapping[str, Any]) -> str:
    return _clean(span.get("raw_text") or span.get("text") or span.get("source_text"), limit=240)


def _source_field(span: Mapping[str, Any]) -> str:
    return _clean(span.get("source_field") or span.get("field") or "memo")


def _detected_type(span: Mapping[str, Any]) -> str:
    return _clean(span.get("detected_type") or span.get("type") or "event")


def _source_anchor(*, span_id: str, span: Mapping[str, Any] | None = None) -> dict[str, Any]:
    span = span if isinstance(span, Mapping) else {}
    return {
        "evidence_span_id": span_id,
        "source_field": _source_field(span) if span else "",
        "start_index": _safe_int(span.get("start_index"), -1) if span else -1,
        "end_index": _safe_int(span.get("end_index"), -1) if span else -1,
        "source_anchor_present": bool(span_id and span),
    }


def _safety_reasons(text: str) -> tuple[str, ...]:
    reasons: list[str] = []
    if _SAFETY_RISK_RE.search(text):
        reasons.append("safety_risk_material")
    if _SAFETY_RE.search(text):
        reasons.append("unsafe_or_overclaim_material")
        reasons.append("safety_overclaim_or_diagnosis_material")
    return tuple(dict.fromkeys(reasons))


def _skip_evidence(span: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    span_id = _span_id(span)
    raw = _span_raw_text(span)
    compact = _compact(raw)
    source = _source_field(span)
    detected = _detected_type(span)
    if not span_id:
        reasons.append("evidence_span_id_missing")
    if not raw:
        reasons.append("evidence_raw_text_missing")
    if compact in {_compact(label) for label in EMOTION_LABELS}:
        reasons.append("emotion_label_only")
    if source in NON_TEXT_SOURCE_FIELDS or source not in TEXT_SOURCE_FIELDS:
        reasons.append("non_text_material_source")
    if detected in {"emotion", "category"}:
        reasons.append("non_text_material_source")
    if detected == "relation_marker" and (compact in {"でも", "けど", "だけど", "ただ"} or _CONNECTOR_ONLY_RE.search(raw)):
        reasons.append("connector_only_material")
    reasons.extend(_safety_reasons(raw))
    return bool(reasons), tuple(dict.fromkeys(reasons))


def _roles_for_evidence(raw_text: str, detected_type: str) -> tuple[str, ...]:
    roles = tuple(role for role in phase8_roles_for_text(raw_text, detected_type) if role and role != "other")
    if roles:
        return roles
    role, _polarity, _must_keep = phase8_primary_role_for_text(raw_text, detected_type)
    return (role,) if role and role != "other" else tuple()


def _relation_for_material(role: str, explicit_relation: Any = "") -> str:
    explicit = _clean(explicit_relation)
    if explicit:
        return normalize_relation_type(explicit, roles=(role,), line_role=role) or explicit
    for roles, relation in ROLE_RELATION_HINTS:
        if role in roles:
            return relation
    return normalize_relation_type("", roles=(role,), line_role=role) or "coexistence"


def _kind_for_role(role: str, detected_type: str = "") -> str:
    if role in ROLE_KIND_HINTS:
        return ROLE_KIND_HINTS[role]
    if detected_type in {"wish", "value"}:
        return "wish"
    if detected_type in {"fear", "constraint"}:
        return "fear"
    return "state"


def _material_phrase_for_role(raw_text: str, role: str) -> str:
    text = _clean(raw_text, limit=160)
    if not text:
        return ""
    try:
        compressed = _clean(_compress_text(text, role), limit=96)
    except Exception:
        compressed = ""
    if compressed and compressed != "other":
        return compressed
    if role == "fatigue_accumulation" and "疲" in text:
        return "疲れが重なっていること"
    if role == "loss_of_control" and "集中" in text:
        return "集中が切れていること"
    if role in {"small_repair", "positive_state"} and "落ち着" in text:
        return "落ち着いたこと"
    if role in {"avoidance_wish", "value_wish", "wish_to_rely"}:
        if "休みたい" in text:
            return "休みたい気持ち"
        if "大事にしたい" in text:
            return "大事にしたい気持ち"
        if "頼りたい" in text:
            return "頼りたい気持ち"
    cleaned = re.sub(r"^(?:今日は|今日|また|でも|本当は|たぶん|もう|このまま|さっき)\s*", "", text).strip(_TRIM)
    cleaned = re.sub(r"(?:けど|だけど|でも|のに|から|なら|すると|したら|を|が|で)$", "", cleaned).strip(_TRIM)
    if not cleaned:
        return ""
    if cleaned.endswith(("こと", "気持ち", "感覚", "怖さ", "しんどさ", "限界", "不安", "流れ", "つらさ", "状態")):
        return cleaned
    suffix = "気持ち" if role in {"wish_to_rely", "ordinary_life_wish", "avoidance_wish", "value_wish"} else "こと"
    return f"{cleaned}{suffix}"


def _material_quality(phrase: str, *, raw_text: str, role: str, detected_type: str, source_field: str) -> tuple[dict[str, Any], tuple[str, ...]]:
    report = judge_phrase_unit_material_quality(
        phrase,
        raw_text=raw_text,
        role=role,
        detected_type=detected_type,
        source_field=source_field,
    )
    quality_flags = list(_dedupe(report.get("quality_flags") or ()))
    reasons = list(_dedupe(report.get("rejection_reasons") or ()))
    if not reasons:
        reasons = [flag for flag in quality_flags if flag in BLOCKING_MATERIAL_FLAGS]
    compact = _compact(phrase)
    if compact in {_compact(label) for label in EMOTION_LABELS}:
        reasons.append("emotion_label_only")
    if _CONNECTOR_ONLY_RE.search(phrase):
        reasons.append("connector_only_material")
    if _UNFINISHED_TAIL_RE.search(phrase):
        reasons.append("unfinished_phrase")
        if phrase.endswith(("を", "が", "で", "に")):
            reasons.append("orphan_particle")
    reasons.extend(_safety_reasons(phrase))
    return dict(report), tuple(dict.fromkeys(reasons))


def _normalize_material_grammar(
    phrase: str,
    *,
    role: str,
    must_keep: bool,
    source: str,
) -> tuple[str, dict[str, Any], tuple[str, ...]]:
    result = normalize_phrase_unit_grammar(
        phrase,
        role=role,
        must_keep=must_keep,
    )
    grammar_meta = result.as_meta()
    reasons: list[str] = []
    if result.action == PHRASE_UNIT_GRAMMAR_DROP:
        reasons.append("phrase_unit_grammar_dropped")
        reasons.extend(result.warning_codes)
    elif result.action == PHRASE_UNIT_GRAMMAR_DEFER:
        reasons.append("phrase_unit_grammar_deferred")
        reasons.extend(result.warning_codes)
    normalized = result.normalized_text if result.usable else phrase
    return normalized, grammar_meta, tuple(dict.fromkeys(reasons))


def _grammar_codes_from_meta(meta: Mapping[str, Any] | None) -> tuple[str, ...]:
    return collect_phrase_unit_grammar_warning_codes(meta or {})


def _grammar_meta_fields(grammar_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    safe = _json_safe_mapping(grammar_meta)
    codes = list(_grammar_codes_from_meta(safe))
    action = _clean(safe.get("phrase_unit_grammar_action")) or PHRASE_UNIT_GRAMMAR_KEEP
    return {
        "phrase_unit_grammar_normalizer": safe,
        "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "phrase_unit_grammar_normalizer_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "step8_phrase_unit_grammar_normalizer_connected": True,
        "step8_phrase_unit_grammar_normalizer_ready": True,
        "phrase_unit_grammar_action": action,
        "phrase_unit_grammar_rephrased": action == PHRASE_UNIT_GRAMMAR_REPHRASE,
        "phrase_unit_grammar_dropped": action == PHRASE_UNIT_GRAMMAR_DROP,
        "phrase_unit_grammar_deferred": action == PHRASE_UNIT_GRAMMAR_DEFER,
        "grammar_warning_codes": codes,
        "surface_grammar_warning_codes": codes,
        "grammar_warning_count": len(codes),
        "surface_grammar_warning_count": len(codes),
        "malformed_nominalization_risk": any("nominalization" in code or "stem_koto" in code for code in codes),
        "must_keep_dropped": False,
        "must_keep_preserved": True,
        "unsupported_completion_added": False,
        "meaning_added": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


@dataclass(frozen=True)
class CompleteMaterialUnit:
    material_id: str
    phrase_unit_id: str
    evidence_span_id: str
    material_text: str
    role: str
    polarity: str = "neutral"
    must_keep: bool = False
    relation_type: str = ""
    canonical_nucleus_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    canonical_relation_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    source_evidence_span_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    source_anchor: Mapping[str, Any] = dataclass_field(default_factory=dict)
    quality_flags: Iterable[str] = dataclass_field(default_factory=tuple)
    rejection_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_MATERIAL_UNIT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        role = _clean(self.role)
        relation = _relation_for_material(role, self.relation_type)
        object.__setattr__(self, "material_id", _clean(self.material_id))
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "material_text", _clean(self.material_text, limit=96))
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "polarity", _clean(self.polarity) or "neutral")
        object.__setattr__(self, "must_keep", bool(self.must_keep))
        object.__setattr__(self, "relation_type", relation)
        object.__setattr__(self, "canonical_nucleus_ids", tuple(_dedupe(self.canonical_nucleus_ids)))
        object.__setattr__(self, "canonical_relation_ids", tuple(_dedupe(self.canonical_relation_ids)))
        source_evidence_span_ids = tuple(_dedupe(self.source_evidence_span_ids))
        if not source_evidence_span_ids and self.evidence_span_id:
            source_evidence_span_ids = (self.evidence_span_id,)
        object.__setattr__(self, "source_evidence_span_ids", source_evidence_span_ids)
        object.__setattr__(self, "source_anchor", _json_safe_mapping(self.source_anchor))
        object.__setattr__(self, "quality_flags", tuple(_dedupe(self.quality_flags)))
        object.__setattr__(self, "rejection_reasons", tuple(_dedupe(self.rejection_reasons)))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_MATERIAL_UNIT_SCHEMA_VERSION)

    @property
    def text(self) -> str:
        return self.material_text

    @property
    def source_anchor_id(self) -> str:
        return self.evidence_span_id

    @property
    def source_field(self) -> str:
        return _clean(self.source_anchor.get("source_field"))

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return (self.relation_type,) if self.relation_type else tuple()

    @property
    def relation_family(self) -> str:
        return relation_family(self.relation_type)

    @property
    def canonical_relation_type(self) -> str:
        return canonical_relation_type(self.relation_type)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.material_id:
            errors.append("material_id_missing")
        if not self.phrase_unit_id:
            errors.append("phrase_unit_id_missing")
        if not self.evidence_span_id:
            errors.append("evidence_span_id_missing")
        if not self.material_text:
            errors.append("material_text_missing")
        if _compact(self.material_text) in {_compact(label) for label in EMOTION_LABELS}:
            errors.append("emotion_label_only")
        if not self.role:
            errors.append("role_missing")
        if not self.relation_type:
            errors.append("relation_type_missing")
        if not bool(self.source_anchor.get("source_anchor_present")):
            errors.append("source_anchor_missing")
        for reason in self.rejection_reasons:
            if reason not in errors:
                errors.append(reason)
        return tuple(dict.fromkeys(errors))

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_focus_seed(self) -> dict[str, Any]:
        seed = {
            "material_id": self.material_id,
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "material_text": self.material_text,
            "role": self.role,
            "polarity": self.polarity,
            "must_keep": self.must_keep,
            "relation_type": self.relation_type,
            "canonical_relation_type": self.canonical_relation_type,
            "relation_family": self.relation_family,
            "canonical_nucleus_ids": list(self.canonical_nucleus_ids),
            "canonical_relation_ids": list(self.canonical_relation_ids),
            "source_evidence_span_ids": list(self.source_evidence_span_ids),
            "raw_input_included": False,
        }
        seed.update(_observation_forward_meta(self.meta))
        return seed

    def as_sentence_plan_seed(self) -> dict[str, Any]:
        return self.as_focus_seed()

    def as_phrase_unit_like(self) -> dict[str, Any]:
        return {
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "compressed_text": self.material_text,
            "role": self.role,
            "polarity": self.polarity,
            "must_keep": self.must_keep,
            "canonical_nucleus_ids": list(self.canonical_nucleus_ids),
            "canonical_relation_ids": list(self.canonical_relation_ids),
            "source_evidence_span_ids": list(self.source_evidence_span_ids),
            "quality_flags": list(self.quality_flags),
        }

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "material_id": self.material_id,
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "material_text": self.material_text,
            "role": self.role,
            "polarity": self.polarity,
            "must_keep": self.must_keep,
            "relation_type": self.relation_type,
            "canonical_relation_type": self.canonical_relation_type,
            "relation_family": self.relation_family,
            "canonical_nucleus_ids": list(self.canonical_nucleus_ids),
            "canonical_relation_ids": list(self.canonical_relation_ids),
            "source_evidence_span_ids": list(self.source_evidence_span_ids),
            **_observation_forward_meta(self.meta),
            "source_anchor": dict(self.source_anchor),
            "quality_flags": list(self.quality_flags),
            "phrase_unit_grammar_normalizer_version": self.meta.get("phrase_unit_grammar_normalizer_version") or PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
            "phrase_unit_grammar_normalizer_step": self.meta.get("phrase_unit_grammar_normalizer_step") or PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
            "step8_phrase_unit_grammar_normalizer_connected": bool(self.meta.get("step8_phrase_unit_grammar_normalizer_connected", True)),
            "phrase_unit_grammar_action": self.meta.get("phrase_unit_grammar_action") or PHRASE_UNIT_GRAMMAR_KEEP,
            "phrase_unit_grammar_rephrased": bool(self.meta.get("phrase_unit_grammar_rephrased")),
            "phrase_unit_grammar_dropped": False,
            "phrase_unit_grammar_deferred": False,
            "phrase_unit_grammar_normalizer": dict(self.meta.get("phrase_unit_grammar_normalizer") or {}),
            "grammar_warning_codes": list(self.meta.get("grammar_warning_codes") or []),
            "surface_grammar_warning_codes": list(self.meta.get("surface_grammar_warning_codes") or self.meta.get("grammar_warning_codes") or []),
            "grammar_warning_count": int(self.meta.get("grammar_warning_count") or len(self.meta.get("grammar_warning_codes") or [])),
            "surface_grammar_warning_count": int(self.meta.get("surface_grammar_warning_count") or len(self.meta.get("surface_grammar_warning_codes") or self.meta.get("grammar_warning_codes") or [])),
            "must_keep_preserved": bool(self.meta.get("must_keep_preserved", self.must_keep)),
            "unsupported_completion_added": False,
            "meaning_added": False,
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "completion_sentence_template": False,
            "fixed_sentence_template": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


@dataclass(frozen=True)
class CompleteMaterialRejection:
    reason_codes: Iterable[str]
    evidence_span_id: str = ""
    phrase_unit_id: str = ""
    role: str = ""
    relation_type: str = ""
    source_anchor: Mapping[str, Any] = dataclass_field(default_factory=dict)
    quality_flags: Iterable[str] = dataclass_field(default_factory=tuple)
    source: str = "material_service"
    schema_version: str = COMPLETE_MATERIAL_REJECTION_SCHEMA_VERSION
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason_codes", tuple(_dedupe(self.reason_codes)))
        object.__setattr__(self, "evidence_span_id", _clean(self.evidence_span_id))
        object.__setattr__(self, "phrase_unit_id", _clean(self.phrase_unit_id))
        object.__setattr__(self, "role", _clean(self.role))
        object.__setattr__(self, "relation_type", _clean(self.relation_type))
        object.__setattr__(self, "source_anchor", _json_safe_mapping(self.source_anchor))
        object.__setattr__(self, "quality_flags", tuple(_dedupe(self.quality_flags)))
        object.__setattr__(self, "source", _clean(self.source) or "material_service")
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_MATERIAL_REJECTION_SCHEMA_VERSION)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "target_step": COMPLETE_MATERIAL_STAGE,
            "material_id": "",
            "phrase_unit_id": self.phrase_unit_id,
            "evidence_span_id": self.evidence_span_id,
            "role": self.role,
            "relation_type": self.relation_type,
            "source": self.source,
            "source_anchor": dict(self.source_anchor),
            "rejection_reasons": list(self.reason_codes),
            "reason_codes": list(self.reason_codes),
            "quality_flags": list(self.quality_flags),
            "phrase_unit_grammar_normalizer_version": self.meta.get("phrase_unit_grammar_normalizer_version") or PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
            "phrase_unit_grammar_normalizer_step": self.meta.get("phrase_unit_grammar_normalizer_step") or PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
            "step8_phrase_unit_grammar_normalizer_connected": bool(self.meta.get("step8_phrase_unit_grammar_normalizer_connected")),
            "phrase_unit_grammar_action": self.meta.get("phrase_unit_grammar_action") or (PHRASE_UNIT_GRAMMAR_DEFER if self.meta.get("phrase_unit_grammar_deferred") else PHRASE_UNIT_GRAMMAR_DROP),
            "phrase_unit_grammar_dropped": bool(self.meta.get("phrase_unit_grammar_dropped")),
            "phrase_unit_grammar_deferred": bool(self.meta.get("phrase_unit_grammar_deferred")),
            "phrase_unit_grammar_normalizer": dict(self.meta.get("phrase_unit_grammar_normalizer") or {}),
            "grammar_warning_codes": list(self.meta.get("grammar_warning_codes") or []),
            "surface_grammar_warning_codes": list(self.meta.get("surface_grammar_warning_codes") or self.meta.get("grammar_warning_codes") or []),
            "grammar_warning_count": int(self.meta.get("grammar_warning_count") or len(self.meta.get("grammar_warning_codes") or [])),
            "surface_grammar_warning_count": int(self.meta.get("surface_grammar_warning_count") or len(self.meta.get("surface_grammar_warning_codes") or self.meta.get("grammar_warning_codes") or [])),
            "must_keep_preserved": bool(self.meta.get("must_keep_preserved")),
            "must_keep_dropped": False,
            "unsupported_completion_added": False,
            "meaning_added": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }


def _rejection(**kwargs: Any) -> CompleteMaterialRejection:
    return CompleteMaterialRejection(**kwargs)


@dataclass(frozen=True)
class CompleteMaterialBundle:
    materials: Iterable[CompleteMaterialUnit] = dataclass_field(default_factory=tuple)
    rejected_rows: Iterable[CompleteMaterialRejection | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    coverage_group: str = "complete_initial_materials"
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_MATERIAL_BUNDLE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        materials = tuple(item for item in self.materials if isinstance(item, CompleteMaterialUnit))
        rejected: list[CompleteMaterialRejection] = []
        for row in self.rejected_rows:
            if isinstance(row, CompleteMaterialRejection):
                rejected.append(row)
            elif isinstance(row, Mapping):
                rejected.append(CompleteMaterialRejection(reason_codes=row.get("reason_codes") or row.get("rejection_reasons") or (), evidence_span_id=row.get("evidence_span_id") or "", phrase_unit_id=row.get("phrase_unit_id") or "", role=row.get("role") or "", relation_type=row.get("relation_type") or "", source_anchor=row.get("source_anchor") or {}, quality_flags=row.get("quality_flags") or (), source=row.get("source") or "material_service", meta=row.get("meta") or {}))
        object.__setattr__(self, "materials", materials)
        object.__setattr__(self, "rejected_rows", tuple(rejected))
        object.__setattr__(self, "coverage_group", _clean(self.coverage_group) or "complete_initial_materials")
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_MATERIAL_BUNDLE_SCHEMA_VERSION)

    @property
    def usable_materials(self) -> Tuple[CompleteMaterialUnit, ...]:
        return tuple(item for item in self.materials if item.usable)

    @property
    def material_units(self) -> Tuple[CompleteMaterialUnit, ...]:
        return self.usable_materials

    @property
    def material_count(self) -> int:
        return len(self.usable_materials)

    @property
    def phrase_unit_count(self) -> int:
        return len(self.used_phrase_unit_ids)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_rows) + len(tuple(item for item in self.materials if not item.usable))

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.evidence_span_id for item in self.usable_materials))

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.phrase_unit_id or item.material_id for item in self.usable_materials))

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.relation_type for item in self.usable_materials))

    @property
    def role_types(self) -> Tuple[str, ...]:
        return tuple(_dedupe(item.role for item in self.usable_materials))

    @property
    def role_keys(self) -> Tuple[str, ...]:
        return self.role_types

    @property
    def usable(self) -> bool:
        return bool(self.usable_materials)

    @property
    def status(self) -> str:
        return COMPLETE_MATERIAL_STATUS_READY if self.usable else COMPLETE_MATERIAL_STATUS_UNAVAILABLE

    @property
    def ready(self) -> bool:
        return self.status == COMPLETE_MATERIAL_STATUS_READY

    @property
    def rejection_reasons(self) -> Tuple[str, ...]:
        return tuple(self.rejection_reason_counts.keys())

    @property
    def blocked_reason_keys(self) -> Tuple[str, ...]:
        return self.rejection_reasons

    @property
    def skipped_evidence_span_ids(self) -> Tuple[str, ...]:
        return tuple(_dedupe(row.evidence_span_id for row in self.rejected_rows if "evidence_span_not_found" in row.reason_codes or "source_anchor_missing" in row.reason_codes))

    @property
    def rejection_reason_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.rejected_rows:
            for reason in row.reason_codes:
                counts[reason] = counts.get(reason, 0) + 1
        for item in self.materials:
            for reason in item.validation_errors:
                counts[reason] = counts.get(reason, 0) + 1
        if not self.usable_materials and not counts:
            counts["complete_materials_missing"] = 1
        return counts

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors = list(self.rejection_reason_counts.keys())
        if not self.usable_materials:
            errors.append("complete_materials_missing")
        return tuple(dict.fromkeys(errors))

    @property
    def phrase_unit_grammar_reports(self) -> Tuple[dict[str, Any], ...]:
        reports: list[dict[str, Any]] = []
        for item in self.materials:
            meta = item.meta.get("phrase_unit_grammar_normalizer") if isinstance(item.meta, Mapping) else None
            if meta:
                reports.append(dict(meta))
        for row in self.rejected_rows:
            meta = row.meta.get("phrase_unit_grammar_normalizer") if isinstance(row.meta, Mapping) else None
            if meta:
                reports.append(dict(meta))
        return tuple(reports)

    @property
    def grammar_warning_codes(self) -> Tuple[str, ...]:
        return _grammar_codes_from_meta({"rows": list(self.phrase_unit_grammar_reports)})

    @property
    def phrase_unit_grammar_summary(self) -> dict[str, Any]:
        return summarize_phrase_unit_grammar_normalizer(list(self.phrase_unit_grammar_reports))

    def as_focus_selector_input(self) -> dict[str, Any]:
        return {
            "version": COMPLETE_MATERIAL_BUNDLE_SCHEMA_VERSION,
            "source_step": COMPLETE_MATERIAL_STAGE,
            "coverage_group": self.coverage_group,
            "material_count": self.material_count,
            "materials": [item.as_focus_seed() for item in self.usable_materials],
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "role_types": list(self.role_types),
            **_observation_forward_meta(self.meta),
            "grammar_warning_codes": list(self.grammar_warning_codes),
            "surface_grammar_warning_codes": list(self.grammar_warning_codes),
            "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
            "phrase_unit_grammar_normalizer_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
            "raw_input_included": False,
            "response_shape_changed": False,
        }

    def as_sentence_plan_source(self) -> dict[str, Any]:
        return self.as_focus_selector_input()

    def as_sentence_plan_seed(self) -> dict[str, Any]:
        return self.as_focus_selector_input()

    def as_meta(self) -> dict[str, Any]:
        row_metas = [item.as_meta() for item in self.usable_materials]
        rejected_metas = [row.as_meta() for row in self.rejected_rows] + [item.as_meta() for item in self.materials if not item.usable]
        grammar_reports = [
            row.get("phrase_unit_grammar_normalizer")
            for row in [*row_metas, *rejected_metas]
            if isinstance(row, Mapping) and isinstance(row.get("phrase_unit_grammar_normalizer"), Mapping)
        ]
        grammar_summary = summarize_phrase_unit_grammar_normalizer(grammar_reports)
        grammar_codes = collect_phrase_unit_grammar_warning_codes(grammar_summary, self.meta)
        grammar_counts = _step8_counts_from_rows([*row_metas, *rejected_metas])
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "target_step": COMPLETE_MATERIAL_STAGE,
            "step": COMPLETE_MATERIAL_STAGE,
            "implementation_unit": COMPLETE_MATERIAL_IMPLEMENTATION_UNIT,
            "stage": COMPLETE_COMPOSER_STAGE,
            "source": "complete_material_service",
            "status": self.status,
            "ready": self.ready,
            "material_service_added": True,
            "material_stage_filter_enabled": True,
            "material_stage_filtering_enabled": True,
            "sentence_plan_pre_filter_enabled": True,
            "surface_realizer_free_invention_blocked": True,
            "evidence_anchor_required": True,
            "phrase_unit_role_required": True,
            "relation_type_required": True,
            "emotion_label_only_excluded": True,
            "unfinished_fragment_excluded": True,
            "orphan_particle_excluded": True,
            "rootless_material_excluded": True,
            "unsafe_overclaim_material_excluded": True,
            "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
            "phrase_unit_grammar_normalizer_connected": True,
            "step8_phrase_unit_grammar_normalizer_ready": True,
            "step8_phrase_unit_grammar_normalizer_connected": True,
            "phrase_unit_grammar_normalizer": grammar_summary,
            "phrase_unit_grammar_normalizer_report": grammar_summary,
            "grammar_warning_codes": list(grammar_codes),
            "surface_grammar_warning_codes": list(grammar_codes),
            "phrase_unit_grammar_warning_codes": list(grammar_codes),
            "grammar_warning_count": len(grammar_codes),
            "surface_grammar_warning_count": len(grammar_codes),
            "phrase_unit_grammar_warning_count": len(grammar_codes),
            "grammar_warning_major": bool(grammar_codes) and (grammar_counts.get("drop", 0) > 0 or grammar_counts.get("defer", 0) > 0),
            "phrase_unit_grammar_rephrase_count": grammar_counts.get("rephrase", 0),
            "phrase_unit_grammar_drop_count": grammar_counts.get("drop", 0),
            "phrase_unit_grammar_defer_count": grammar_counts.get("defer", 0),
            "must_keep_deferred_count": sum(1 for row in rejected_metas if row.get("phrase_unit_grammar_action") == PHRASE_GRAMMAR_DEFER),
            "must_keep_dropped": False,
            "unsupported_completion_added": False,
            "unsupported_completion_added_by_phrase_unit_grammar": False,
            "meaning_added_by_phrase_unit_grammar": False,
            "meaning_added_by_phrase_unit_grammar_normalizer": False,
            "completion_sentence_templates_added": False,
            "fixed_sentence_template_added": False,
            "fixed_sentence_template_allowed": False,
            "input_specific_template_added": False,
            "external_ai_used": False,
            "external_ai_allowed": False,
            "local_llm_used": False,
            "local_llm_allowed": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "comment_text_generated": False,
            "comment_text_contract": "passed_only",
            "comment_text_included": False,
            "comment_text_body_included": False,
            "coverage_group": self.coverage_group,
            "candidate_material_count": len(self.materials) + len(self.rejected_rows),
            "accepted_material_count": len(self.usable_materials),
            "material_count": len(self.usable_materials),
            "usable_material_count": len(self.usable_materials),
            "rejected_material_count": self.rejected_count,
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "canonical_relation_types": list(_dedupe(canonical_relation_type(item) for item in self.relation_types)),
            "relation_families": list(_dedupe(relation_family(item) for item in self.relation_types)),
            "role_types": list(self.role_types),
            "role_keys": list(self.role_keys),
            **_observation_forward_meta(self.meta),
            "all_materials_usable": bool(self.usable_materials) and self.rejected_count == 0,
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "blocked_reasons": self.rejection_reason_counts,
            "blocked_reason_keys": list(self.rejection_reason_counts.keys()),
            "rows": row_metas,
            "materials": row_metas,
            "rejected_rows": rejected_metas,
            "rejection_reason_counts": self.rejection_reason_counts,
            "focus_selector_input": self.as_focus_selector_input(),
            "material_text_included": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "raw_input_required_for_debug": False,
            "raw_input_required_for_improvement": False,
            "contract_boundary": {
                "comment_text_contract": "passed_only",
                "db_physical_name_changed": False,
                "api_route_changed": False,
                "public_response_key_change": False,
                "rn_visible_title_changed": False,
                "response_shape_changed": False,
            },
            "source_policy": {
                "external_ai_allowed": False,
                "local_llm_allowed": False,
                "fixed_sentence_template_allowed": False,
            },
            "meta": dict(self.meta),
        }


def build_complete_material_service_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta()
    return {
        "version": COMPLETE_MATERIAL_SERVICE_VERSION,
        "target_step": COMPLETE_MATERIAL_STAGE,
        "step": COMPLETE_MATERIAL_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_MATERIAL_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta.get("target_composer_term"),
        "target_composer_family_term": term_meta.get("target_composer_family_term"),
        "complete_composer_initial_term": term_meta.get("complete_composer_initial_term"),
        "material_service_added": True,
        "observation_material_connector_supported": True,
        "observation_reply_kind_preserved_in_material_meta": True,
        "unknown_slots_preserved_in_material_meta": True,
        "user_fact_grounding_mode_preserved_in_material_meta": True,
        "internal_question_ids_preserved_in_material_meta": True,
        "runtime_client_connected": False,
        "base_version": COMPLETE_MATERIAL_SERVICE_BASE_VERSION,
        "phrase_unit_grammar_normalizer_version": COMPLETE_MATERIAL_PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "phrase_unit_grammar_normalizer_step": COMPLETE_MATERIAL_PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "phrase_unit_grammar_normalizer_connected": True,
        "step8_phrase_unit_grammar_normalizer_ready": True,
        "step8_phrase_unit_grammar_normalizer_connected": True,
        "runs_phrase_unit_grammar_before_sentence_plan": True,
        "runs_phrase_unit_grammar_before_surface_realizer": True,
        "grammar_warning_codes_connected": True,
        "phrase_unit_drop_rephrase_defer_supported": True,
        "must_keep_deferred_not_dropped": True,
        "runs_before_sentence_plan": True,
        "runs_before_surface_realizer": True,
        "phrase_unit_grammar_normalizer_contract": build_phrase_unit_grammar_normalizer_contract_meta(),
        "material_stage_filter_enabled": True,
        "material_stage_filtering_enabled": True,
        "sentence_plan_pre_filter_enabled": True,
        "evidence_span_required": True,
        "requires_evidence_span_id": True,
        "source_anchor_required": True,
        "requires_source_anchor": True,
        "phrase_unit_role_required": True,
        "relation_type_required": True,
        "relation_candidate_required": True,
        "filters_emotion_label_only": True,
        "rejects_emotion_label_only": True,
        "filters_unfinished_phrase": True,
        "rejects_unfinished_fragment": True,
        "rejects_unfinished_phrase": True,
        "filters_orphan_particle": True,
        "rejects_orphan_particle": True,
        "filters_rootless_material": True,
        "rejects_ungrounded_material": True,
        "rejects_diagnosis_personality_and_advice": True,
        "step8_phrase_unit_grammar_normalizer_connected": True,
        "step8_phrase_unit_grammar_normalizer_ready": True,
        "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "phrase_unit_grammar_normalizer_step": PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP,
        "rejects_malformed_nominalization": True,
        "rejects_or_defers_unfinished_phrase_unit": True,
        "unsupported_completion_added_by_phrase_unit_grammar": False,
        "meaning_added_by_phrase_unit_grammar": False,
        "comment_text_generated": False,
        "comment_text_contract": "passed_only",
        "comment_text_included": False,
        "comment_text_body_included": False,
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_allowed": False,
        "completion_sentence_templates_added": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
        "unsupported_completion_added": False,
        "meaning_added_by_phrase_unit_grammar_normalizer": False,
        "must_keep_dropped": False,
    }


def _step8_counts_from_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {
        PHRASE_UNIT_GRAMMAR_KEEP: 0,
        PHRASE_UNIT_GRAMMAR_REPHRASE: 0,
        PHRASE_UNIT_GRAMMAR_DROP: 0,
        PHRASE_UNIT_GRAMMAR_DEFER: 0,
    }
    for row in rows:
        meta = row.get("phrase_unit_grammar_normalizer") if isinstance(row, Mapping) else None
        if not isinstance(meta, Mapping):
            meta = row.get("meta") if isinstance(row, Mapping) else {}
        action = _clean((meta or {}).get("phrase_unit_grammar_action") or (row or {}).get("phrase_unit_grammar_action"))
        if action in counts:
            counts[action] += 1
    return counts


def _material_from_phrase_unit(unit: Any, *, index: int, evidence_by_id: Mapping[str, Mapping[str, Any]]) -> tuple[CompleteMaterialUnit | None, CompleteMaterialRejection | None]:
    row = _as_mapping(unit)
    phrase_unit_id = _clean(row.get("phrase_unit_id") or row.get("id") or f"cpu{index}")
    evidence_span_id = _clean(row.get("evidence_span_id") or row.get("span_id"))
    role = _clean(row.get("role"))
    material_text = _clean(row.get("compressed_text") or row.get("material_text") or row.get("phrase") or row.get("text"), limit=96)
    evidence = evidence_by_id.get(evidence_span_id, {}) if evidence_span_id else {}
    source = _source_field(evidence) if evidence else _clean(row.get("source_field")) or "memo"
    detected = _detected_type(evidence) if evidence else _clean(row.get("detected_type")) or "event"
    raw_for_quality = _span_raw_text(evidence) if evidence else ""
    polarity = _clean(row.get("polarity"))
    must_keep = bool(row.get("must_keep"))
    if not polarity or row.get("must_keep") is None:
        polarity_default, must_keep_default = phase8_role_meta(role)
        polarity = polarity or polarity_default
        must_keep = must_keep or must_keep_default
    material_text, grammar_meta, grammar_reasons = _normalize_material_grammar(
        material_text,
        role=role,
        must_keep=must_keep,
        source="phrase_unit",
    )
    quality_report, quality_reasons = _material_quality(material_text, raw_text=raw_for_quality or material_text, role=role, detected_type=detected, source_field=source)
    relation = _relation_for_material(role, row.get("relation_type"))
    anchor = _source_anchor(span_id=evidence_span_id, span=evidence if evidence else None)
    grammar_fields = _grammar_meta_fields(grammar_meta)
    reasons = list(quality_reasons)
    reasons.extend(grammar_reasons)
    if not material_text:
        reasons.append("material_text_missing")
    if not role:
        reasons.append("role_missing")
    if not evidence_span_id:
        reasons.append("evidence_span_id_missing")
    if evidence_span_id and evidence_by_id and evidence_span_id not in evidence_by_id:
        reasons.append("source_anchor_missing")
        reasons.append("evidence_span_not_found")
    if not anchor.get("source_anchor_present"):
        reasons.append("source_anchor_missing")
    reasons.extend(_safety_reasons(raw_for_quality))
    reasons = list(dict.fromkeys(reasons))
    quality_flags = list(_dedupe([*(quality_report.get("quality_flags") or ()), *(row.get("quality_flags") or ()), *grammar_fields.get("grammar_warning_codes", [])]))
    if reasons:
        return None, CompleteMaterialRejection(
            reason_codes=reasons,
            evidence_span_id=evidence_span_id,
            phrase_unit_id=phrase_unit_id,
            role=role,
            relation_type=relation,
            source_anchor=anchor,
            quality_flags=quality_flags,
            source="phrase_unit",
            meta={**grammar_fields, "material_source": "phrase_unit", "must_keep_preserved": bool(must_keep and "phrase_unit_grammar_dropped" not in grammar_reasons), "must_keep_deferred": "phrase_unit_grammar_deferred" in grammar_reasons},
        )
    return CompleteMaterialUnit(
        material_id=f"cm{index}",
        phrase_unit_id=phrase_unit_id,
        evidence_span_id=evidence_span_id,
        material_text=material_text,
        role=role,
        polarity=polarity,
        must_keep=must_keep,
        relation_type=relation,
        canonical_nucleus_ids=row.get("canonical_nucleus_ids") or row.get("nucleus_ids") or (),
        canonical_relation_ids=row.get("canonical_relation_ids") or row.get("relation_ids") or (),
        source_evidence_span_ids=row.get("source_evidence_span_ids") or ((evidence_span_id,) if evidence_span_id else ()),
        source_anchor=anchor,
        quality_flags=quality_flags,
        meta={**grammar_fields, "material_source": "phrase_unit", "must_keep_preserved": True},
    ), None


def _materials_from_evidence_span(span: Any, *, start_index: int) -> tuple[list[CompleteMaterialUnit], list[CompleteMaterialRejection]]:
    row = _as_mapping(span)
    span_id = _span_id(row)
    raw = _span_raw_text(row)
    source = _source_field(row)
    detected = _detected_type(row)
    anchor = _source_anchor(span_id=span_id, span=row)
    should_skip, skip_reasons = _skip_evidence(row)
    if should_skip:
        return [], [CompleteMaterialRejection(reason_codes=skip_reasons, evidence_span_id=span_id, source_anchor=anchor, source="evidence_span")]
    roles = _roles_for_evidence(raw, detected)
    if not roles:
        return [], [CompleteMaterialRejection(reason_codes=("role_missing",), evidence_span_id=span_id, source_anchor=anchor, source="evidence_span")]
    materials: list[CompleteMaterialUnit] = []
    rejected: list[CompleteMaterialRejection] = []
    for offset, role in enumerate(roles, start=0):
        index = start_index + offset
        phrase = _material_phrase_for_role(raw, role)
        polarity, must_keep = phase8_role_meta(role)
        phrase, grammar_meta, grammar_reasons = _normalize_material_grammar(
            phrase,
            role=role,
            must_keep=must_keep,
            source="evidence_span",
        )
        quality_report, quality_reasons = _material_quality(phrase, raw_text=raw, role=role, detected_type=detected, source_field=source)
        relation = _relation_for_material(role)
        grammar_fields = _grammar_meta_fields(grammar_meta)
        reasons = list(quality_reasons)
        reasons.extend(grammar_reasons)
        if not phrase:
            reasons.append("material_text_missing")
        if not relation:
            reasons.append("relation_type_missing")
        quality_flags = list(_dedupe([*(quality_report.get("quality_flags") or ()), *grammar_fields.get("grammar_warning_codes", [])]))
        if reasons:
            rejected.append(CompleteMaterialRejection(reason_codes=list(dict.fromkeys(reasons)), evidence_span_id=span_id, phrase_unit_id=f"cpu{index}", role=role, relation_type=relation, source_anchor=anchor, quality_flags=quality_flags, source="evidence_span", meta={**grammar_fields, "material_source": "evidence_span", "must_keep_preserved": bool(must_keep and "phrase_unit_grammar_dropped" not in grammar_reasons), "must_keep_deferred": "phrase_unit_grammar_deferred" in grammar_reasons}))
            continue
        materials.append(
            CompleteMaterialUnit(
                material_id=f"cm{index}",
                phrase_unit_id=f"cpu{index}",
                evidence_span_id=span_id,
                material_text=phrase,
                role=role,
                polarity=polarity,
                must_keep=must_keep,
                relation_type=relation,
                source_evidence_span_ids=(span_id,) if span_id else (),
                source_anchor=anchor,
                quality_flags=quality_flags,
                meta={**grammar_fields, "material_source": "evidence_span", "must_keep_preserved": True},
            )
        )
    return materials, rejected

def build_complete_material_bundle(
    *,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    coverage_group: str = "complete_initial_materials",
    meta: Mapping[str, Any] | None = None,
    relation_candidates: Sequence[Any] | None = None,
    observation_connector: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    internal_question_set: Any = None,
    current_input: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
) -> CompleteMaterialBundle:
    """Build a sanitized material bundle from EvidenceSpan and PhraseUnit rows."""
    evidence_rows = [_as_mapping(item) for item in list(evidence_spans or ())]
    evidence_by_id = {_span_id(item): item for item in evidence_rows if _span_id(item)}
    connector_source = observation_connector
    if connector_source is None and (
        eligibility_decision is not None
        or user_fact_grounding_decision is not None
        or internal_question_set is not None
        or current_input is not None
        or subscription_tier is not None
        or capability is not None
        or user_facts is not None
    ):
        connector_source = build_material_focus_relation_connector(
            current_input=current_input,
            eligibility_decision=eligibility_decision,
            user_fact_grounding_decision=user_fact_grounding_decision,
            internal_question_set=internal_question_set,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            source_bundle=source_bundle,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
    connector_meta = _observation_forward_meta(connector_source)
    materials: list[CompleteMaterialUnit] = []
    rejected: list[CompleteMaterialRejection] = []
    if phrase_units:
        for index, unit in enumerate(list(phrase_units or ()), start=1):
            material, rejection = _material_from_phrase_unit(unit, index=index, evidence_by_id=evidence_by_id)
            if material is not None:
                materials.append(material)
            if rejection is not None:
                rejected.append(rejection)
    else:
        next_index = 1
        for span in evidence_rows:
            span_materials, span_rejected = _materials_from_evidence_span(span, start_index=next_index)
            materials.extend(span_materials)
            rejected.extend(span_rejected)
            next_index += max(1, len(span_materials) + len(span_rejected))
    if connector_meta:
        materials = [
            CompleteMaterialUnit(
                material_id=item.material_id,
                phrase_unit_id=item.phrase_unit_id,
                evidence_span_id=item.evidence_span_id,
                material_text=item.material_text,
                role=item.role,
                polarity=item.polarity,
                must_keep=item.must_keep,
                relation_type=item.relation_type,
                canonical_nucleus_ids=item.canonical_nucleus_ids,
                canonical_relation_ids=item.canonical_relation_ids,
                source_evidence_span_ids=item.source_evidence_span_ids,
                source_anchor=item.source_anchor,
                quality_flags=item.quality_flags,
                rejection_reasons=item.rejection_reasons,
                meta={**dict(item.meta), **connector_meta},
                schema_version=item.schema_version,
            )
            for item in materials
        ]
    return CompleteMaterialBundle(
        materials=tuple(materials),
        rejected_rows=tuple(rejected),
        coverage_group=coverage_group,
        meta={**build_complete_material_service_contract_meta(), **_json_safe_mapping(meta), **connector_meta},
    )


def build_complete_materials(**kwargs: Any) -> CompleteMaterialBundle:
    return build_complete_material_bundle(**kwargs)


def extract_complete_materials(**kwargs: Any) -> CompleteMaterialBundle:
    return build_complete_material_bundle(**kwargs)


def materialize_complete_materials(**kwargs: Any) -> CompleteMaterialBundle:
    return build_complete_material_bundle(**kwargs)


def build_complete_material_service_meta(**kwargs: Any) -> dict[str, Any]:
    return build_complete_material_bundle(**kwargs).as_meta()


def usable_complete_materials(result_or_units: CompleteMaterialBundle | Iterable[CompleteMaterialUnit] | None) -> Tuple[CompleteMaterialUnit, ...]:
    if isinstance(result_or_units, CompleteMaterialBundle):
        return result_or_units.usable_materials
    return tuple(item for item in (result_or_units or ()) if isinstance(item, CompleteMaterialUnit) and item.usable)


def usable_complete_material_units(result_or_units: CompleteMaterialBundle | Iterable[CompleteMaterialUnit] | None) -> Tuple[CompleteMaterialUnit, ...]:
    return usable_complete_materials(result_or_units)


def complete_materials_by_id(result_or_units: CompleteMaterialBundle | Iterable[CompleteMaterialUnit] | None) -> dict[str, CompleteMaterialUnit]:
    return {item.material_id: item for item in usable_complete_materials(result_or_units)}


def complete_material_units_by_id(result_or_units: CompleteMaterialBundle | Iterable[CompleteMaterialUnit] | None) -> dict[str, CompleteMaterialUnit]:
    return complete_materials_by_id(result_or_units)


CompleteMaterial = CompleteMaterialUnit
CompleteMaterialBuildResult = CompleteMaterialBundle
build_complete_material_bundle = build_complete_material_bundle

__all__ = [
    "BLOCKING_MATERIAL_FLAGS",
    "COMPLETE_MATERIAL_SERVICE_BASE_VERSION",
    "COMPLETE_MATERIAL_BUNDLE_SCHEMA_VERSION",
    "COMPLETE_MATERIAL_IMPLEMENTATION_UNIT",
    "COMPLETE_MATERIAL_PHRASE_UNIT_GRAMMAR_NORMALIZER_STEP",
    "COMPLETE_MATERIAL_PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION",
    "COMPLETE_MATERIAL_REJECTION_SCHEMA_VERSION",
    "COMPLETE_MATERIAL_SERVICE_STEP",
    "COMPLETE_MATERIAL_SERVICE_TARGET_STEP",
    "COMPLETE_MATERIAL_SERVICE_VERSION",
    "COMPLETE_MATERIAL_STAGE",
    "COMPLETE_MATERIAL_STATUS_READY",
    "COMPLETE_MATERIAL_STATUS_UNAVAILABLE",
    "COMPLETE_MATERIAL_TARGET_STEP",
    "COMPLETE_MATERIAL_UNIT_SCHEMA_VERSION",
    "CompleteMaterial",
    "CompleteMaterialBuildResult",
    "CompleteMaterialBundle",
    "CompleteMaterialRejection",
    "CompleteMaterialUnit",
    "build_complete_material_bundle",
    "build_complete_material_service_contract_meta",
    "build_complete_material_service_meta",
    "build_complete_materials",
    "complete_materials_by_id",
    "complete_material_units_by_id",
    "extract_complete_materials",
    "materialize_complete_materials",
    "usable_complete_materials",
    "usable_complete_material_units",
]
