# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 7 Surface Realizer 2.0 for EmlisAI Complete Composer initial version.

Surface Realizer 2.0 turns a binding-first ``CompleteSentencePlanV2`` into
internal surface text using grammar parts: subject policy, role phrase,
particle, connector, predicate, ending, distance, and variation keys.  It does
not choose completed observation sentences by coverage group and it does not
write the public ``input_feedback.comment_text`` key.  Later Grounding /
Template / Display gates decide whether the internal surface can be promoted to
visible Emlis observation text.

The module is additive: DB physical names, API routes, public response keys and
RN display behavior are not changed.
"""

from dataclasses import dataclass, field as dataclass_field, is_dataclass, asdict
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_STAGE,
    CompleteSentencePlanLine,
    CompleteSentencePlanV2,
)
from emlis_ai_complete_sentence_planner import (
    COMPLETE_SENTENCE_PLAN_STAGE,
    build_complete_sentence_plan_v2,
    build_complete_sentence_binding_bundle_meta,
)
from emlis_ai_limited_relation_taxonomy import (
    canonical_relation_type,
    normalize_relation_type,
    relation_family,
)

COMPLETE_SURFACE_REALIZER_VERSION = "emlis.complete_surface_realizer.v2"
COMPLETE_SURFACE_REALIZER_SERVICE_VERSION = COMPLETE_SURFACE_REALIZER_VERSION
COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION = "emlis.complete_surface_realization.v2"
COMPLETE_SURFACE_LINE_SCHEMA_VERSION = "emlis.complete_surface_line.v2"
COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION = "emlis.complete_surface_signature.v2"
COMPLETE_SURFACE_REALIZER_STAGE = "Step7_Surface_Realizer_2_0"
COMPLETE_SURFACE_REALIZER_STEP = COMPLETE_SURFACE_REALIZER_STAGE
COMPLETE_SURFACE_REALIZER_TARGET_STEP = COMPLETE_SURFACE_REALIZER_STAGE
COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT = "Commit 7"

COMPLETE_SURFACE_STATUS_READY = "ready"
COMPLETE_SURFACE_STATUS_UNAVAILABLE = "unavailable"

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

# Roles from Material/Relation/SentencePlan.  Values are noun fragments, not
# completed observations.  They can be combined with particles and predicates.
ROLE_PHRASE_BANK: dict[str, tuple[str, str]] = {
    "fatigue_accumulation": ("疲れの蓄積", "load_accumulation"),
    "small_repair": ("小さな回復", "small_repair"),
    "value_wish": ("大切にしたい願い", "value_wish"),
    "wish_to_rely": ("近づきたい気持ち", "approach_wish"),
    "burden_fear": ("負担になる怖さ", "burden_fear"),
    "avoidance_wish": ("避けたい気持ち", "avoidance_wish"),
    "hurt_core": ("あとに残る痛み", "hurt_residue"),
    "anticipation_loop": ("先を考え続ける流れ", "anticipation_loop"),
    "known_action": ("前から続いている流れ", "known_context"),
    "safe_home": ("安心できる場所", "safe_place"),
    "current_expression": ("今出ている感覚", "current_expression"),
    "small_wobble": ("小さな揺れ", "small_wobble"),
    "limit_pressure": ("限界に近い圧力", "limit_pressure"),
    "relationship_distance": ("距離感の揺れ", "relationship_distance"),
    "self_reference": ("自分の側に残る反応", "self_side_response"),
    "primary_phrase": ("中心にある感覚", "primary_phrase"),
}

TECHNICAL_ROLE_KEYS = {
    "evidence_ids",
    "phrase_unit_ids",
    "relation_ids",
    "relation_type",
    "primary_phrase",
}

# Short grammar components.  These are parts, not complete observation strings.
PREDICATE_BANK: dict[str, tuple[tuple[str, str, str, str], ...]] = {
    "pressure": (
        ("が", "前面にあります", "pressure_foreground", "aru"),
        ("が", "強く残っています", "pressure_remain", "nokoru"),
        ("として", "続いています", "pressure_continue", "tsuzuku"),
    ),
    "recovery": (
        ("が", "少し戻ってきています", "recovery_return", "modoru"),
        ("として", "形を取り直しています", "recovery_reshape", "naosu"),
        ("も", "消えずにあります", "recovery_still_there", "aru"),
    ),
    "contrast": (
        ("が", "別々の向きで並んでいます", "contrast_parallel", "narabu"),
        ("として", "片方だけに寄らずにあります", "contrast_not_one_side", "aru"),
        ("も", "同じ場所に残っています", "contrast_same_place", "nokoru"),
    ),
    "coexistence": (
        ("が", "同じ時間の中にあります", "coexistence_same_time", "aru"),
        ("も", "片方だけに減らずに残っています", "coexistence_not_reduced", "nokoru"),
        ("として", "重なりを保っています", "coexistence_overlap", "tamotsu"),
    ),
    "approach_avoidance": (
        ("が", "近づく動きと止まる動きの両方を持っています", "approach_avoidance_both", "motsu"),
        ("として", "一方向には決まりきっていません", "approach_avoidance_not_one", "kimaranai"),
        ("も", "同じ線上に残っています", "approach_avoidance_line", "nokoru"),
    ),
    "residue": (
        ("が", "あとに残っています", "residue_after", "nokoru"),
        ("として", "終わったあとにも残っています", "residue_after_end", "nokoru"),
        ("も", "まだ薄くあります", "residue_light", "aru"),
    ),
    "limit": (
        ("が", "限界に近い場所まで来ています", "limit_near", "kuru"),
        ("として", "これ以上を急がせない形であります", "limit_no_push", "aru"),
        ("も", "境目として残っています", "limit_boundary", "nokoru"),
    ),
    "context": (
        ("が", "背景として支えています", "context_support", "sasaeru"),
        ("として", "今の流れに接続しています", "context_connect", "tsunagu"),
        ("も", "根拠のある範囲で残っています", "context_bound", "nokoru"),
    ),
    "center": (
        ("が", "中心にあります", "center_core", "aru"),
        ("として", "いま前に出ています", "center_front", "deru"),
        ("も", "軸として残っています", "center_axis", "nokoru"),
    ),
}

DEFAULT_PREDICATES: tuple[tuple[str, str, str, str], ...] = (
    ("が", "根拠のある範囲であります", "grounded_exists", "aru"),
    ("として", "文の中に置かれています", "grounded_placed", "oku"),
    ("も", "消えずに残っています", "grounded_remain", "nokoru"),
)

CONNECTOR_BANK: dict[str, dict[str, tuple[str, str]]] = {
    "opening": {
        "default": ("", "none"),
        "pressure": ("まず、", "opening_pressure_first"),
        "recovery": ("はじめに、", "opening_recovery_first"),
    },
    "core": {
        "default": ("その中で、", "core_inside"),
        "pressure": ("その中で、", "core_inside_pressure"),
        "recovery": ("そこに、", "core_recovery_there"),
    },
    "relation": {
        "default": ("同時に、", "relation_same_time"),
        "contrast": ("ただ、", "relation_contrast_but"),
        "coexistence": ("同時に、", "relation_coexistence_same_time"),
        "pressure": ("その圧力の中で、", "relation_pressure_inside"),
        "recovery": ("それでも、", "relation_recovery_after_load"),
        "approach_avoidance": ("近づきたい方と止まりたい方が、", "relation_approach_avoidance"),
    },
    "closing": {
        "default": ("最後は、", "closing_default"),
        "recovery": ("締めでは、", "closing_recovery"),
        "pressure": ("締めでは、", "closing_pressure"),
    },
}

DISTANCE_POLICY_KEYS = {
    "opening": "receive_without_generalization",
    "core": "observe_without_overclaim",
    "relation": "hold_relation_without_deciding_true_side",
    "closing": "close_without_instruction_or_diagnosis",
}

FORBIDDEN_SURFACE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("second_person_overuse", re.compile(r"あなたは|あなたの|あなたが|あなたに")),
    ("diagnosis_like", re.compile(r"診断|治療|症状|トラウマ|障害|ADHD|うつ|鬱|PTSD")),
    ("action_instruction", re.compile(r"(?:するべき|してください|しなければ|行動しましょう|変えましょう)")),
    ("over_comfort", re.compile(r"もう大丈夫|必ず良く|絶対に")),
    ("generic_fixed_closing", re.compile(r"急いで片づけず|一緒に見ます|小さく扱いません|軽く扱いません")),
    ("might_repetition_phrase", re.compile(r"かもしれません")),
)

_SPACE_RE = re.compile(r"\s+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _clean_token(value: Any) -> str:
    return re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")


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
    if is_dataclass(value):
        return _json_safe_mapping(asdict(value))
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


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    out: dict[str, Any] = {}
    for key in (
        "sentence_id",
        "line_role",
        "relation_type",
        "focus_rank",
        "phrase_unit_ids",
        "evidence_span_ids",
        "used_phrase_unit_ids",
        "used_evidence_span_ids",
        "must_include_roles",
        "optional_roles",
        "forbidden_surface_keys",
        "max_chars",
        "surface_intent",
        "repair_policy",
        "meta",
    ):
        if hasattr(value, key):
            out[key] = getattr(value, key)
    return out


def _coerce_plan_line(value: CompleteSentencePlanLine | Mapping[str, Any]) -> CompleteSentencePlanLine | None:
    if isinstance(value, CompleteSentencePlanLine):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanLine(
            sentence_id=value.get("sentence_id") or value.get("id") or "",
            line_role=value.get("line_role") or value.get("role") or "core",
            relation_type=value.get("relation_type") or value.get("relation") or "center",
            focus_rank=value.get("focus_rank") or value.get("rank") or 1,
            phrase_unit_ids=value.get("phrase_unit_ids") or value.get("used_phrase_unit_ids") or (),
            evidence_span_ids=value.get("evidence_span_ids") or value.get("used_evidence_span_ids") or (),
            must_include_roles=value.get("must_include_roles") or (),
            optional_roles=value.get("optional_roles") or (),
            forbidden_surface_keys=value.get("forbidden_surface_keys") or (),
            max_chars=value.get("max_chars") or 120,
            surface_intent=value.get("surface_intent") or "",
            repair_policy=value.get("repair_policy") or (),
            meta=value.get("meta") or {},
        )
    return None


def _coerce_sentence_plan(value: CompleteSentencePlanV2 | Mapping[str, Any] | None) -> CompleteSentencePlanV2 | None:
    if isinstance(value, CompleteSentencePlanV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanV2(
            plan_id=value.get("plan_id") or "complete_sentence_plan_v2",
            sentence_budget=value.get("sentence_budget") or value.get("planned_sentence_count") or 2,
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "unknown",
            sentence_plans=value.get("sentence_plans") or value.get("lines") or (),
            meta=value.get("meta") or {},
        )
    return None


def _surface_relation(relation_type: Any) -> str:
    relation = normalize_relation_type(relation_type)
    if not relation:
        return "center"
    return relation


def _meaning_roles(line: CompleteSentencePlanLine) -> Tuple[str, ...]:
    roles = []
    for raw in tuple(line.must_include_roles or ()) + tuple(line.optional_roles or ()):  # preserve plan order
        role = _clean_token(raw)
        if role and role not in TECHNICAL_ROLE_KEYS and role not in roles:
            roles.append(role)
    return tuple(roles)


def _role_phrase(role: str) -> tuple[str, str]:
    role_key = _clean_token(role)
    if role_key in ROLE_PHRASE_BANK:
        return ROLE_PHRASE_BANK[role_key]
    if not role_key:
        return "根拠のある材料", "grounded_material"
    # Unknown roles are rendered as sanitized internal structural labels. They
    # are not copied from raw input.
    return role_key.replace("_", " "), f"role_{role_key}"


def _phrase_for_line(line: CompleteSentencePlanLine) -> tuple[str, str, Tuple[str, ...]]:
    roles = _meaning_roles(line)
    if not roles:
        roles = ("primary_phrase",)
    phrases: list[str] = []
    keys: list[str] = []
    for role in roles[:2]:
        phrase, key = _role_phrase(role)
        if phrase not in phrases:
            phrases.append(phrase)
        if key not in keys:
            keys.append(key)
    if line.line_role == "relation" and len(phrases) >= 2:
        return "と".join(phrases[:2]), "relation_pair", tuple(keys)
    return phrases[0], keys[0], tuple(keys)


def _connector_for(line_role: str, relation_type: str, sequence_index: int) -> tuple[str, str]:
    if sequence_index <= 0 and line_role == "opening":
        return "", "none"
    bank = CONNECTOR_BANK.get(line_role) or CONNECTOR_BANK["core"]
    return bank.get(relation_type) or bank.get(canonical_relation_type(relation_type)) or bank.get("default") or ("", "none")


def _predicate_candidates(relation_type: str, line_role: str) -> tuple[tuple[str, str, str, str], ...]:
    relation = _surface_relation(relation_type)
    candidates = list(PREDICATE_BANK.get(relation) or PREDICATE_BANK.get(canonical_relation_type(relation)) or DEFAULT_PREDICATES)
    if line_role == "closing":
        candidates.extend([
            ("として", "静かに残っています", "closing_quiet_remain", "nokoru"),
            ("が", "結論にされずにあります", "closing_no_forced_conclusion", "aru"),
        ])
    if line_role == "relation":
        candidates.extend([
            ("として", "分かれずに扱われています", "relation_not_split", "atsukau"),
            ("が", "同じ流れの中にあります", "relation_same_flow", "aru"),
        ])
    return tuple(candidates)


def _choose_predicate(*, relation_type: str, line_role: str, used_predicate_keys: Sequence[str], used_ending_keys: Sequence[str]) -> tuple[str, str, str, str]:
    used_predicates = set(used_predicate_keys or ())
    used_endings = set(used_ending_keys or ())
    candidates = _predicate_candidates(relation_type, line_role)
    for particle, predicate, predicate_key, ending_key in candidates:
        if predicate_key not in used_predicates and ending_key not in used_endings:
            return particle, predicate, predicate_key, ending_key
    for particle, predicate, predicate_key, ending_key in candidates:
        if predicate_key not in used_predicates:
            return particle, predicate, predicate_key, ending_key
    return candidates[0] if candidates else DEFAULT_PREDICATES[0]


def _truncate_sentence(sentence: str, max_chars: int) -> str:
    text = _clean(sentence)
    if not text:
        return ""
    if not text.endswith(("。", "！", "？")):
        text = f"{text}。"
    if max_chars > 0 and len(text) > max_chars:
        text = text[: max(8, max_chars - 1)].rstrip(_TRIM) + "。"
    return text


def _surface_signature_row(*, line: CompleteSentencePlanLine, phrase_key: str, role_phrase_keys: Sequence[str], connector_key: str, particle: str, predicate_key: str, ending_key: str, distance_policy_key: str, variation_key: str) -> dict[str, Any]:
    relation = _surface_relation(line.relation_type)
    return {
        "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "sentence_id": line.sentence_id,
        "line_role": line.line_role,
        "relation_type": relation,
        "canonical_relation_type": canonical_relation_type(relation),
        "relation_family": relation_family(relation),
        "subject_policy_key": "omit_second_person_subject",
        "role_phrase_key": phrase_key,
        "role_phrase_keys": list(role_phrase_keys),
        "connector_key": connector_key,
        "particle_key": particle,
        "predicate_key": predicate_key,
        "ending_key": ending_key,
        "distance_policy_key": distance_policy_key,
        "variation_key": variation_key,
        "signature": f"{line.line_role}:{relation}:{phrase_key}:{connector_key}:{particle}:{predicate_key}:{ending_key}:{distance_policy_key}",
        "completion_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "raw_input_included": False,
    }


def _forbidden_surface_hits(text: str) -> Tuple[str, ...]:
    hits: list[str] = []
    for key, pattern in FORBIDDEN_SURFACE_PATTERNS:
        if pattern.search(text or "") and key not in hits:
            hits.append(key)
    return tuple(hits)


def _realize_line(line: CompleteSentencePlanLine, *, sequence_index: int, used_predicate_keys: Sequence[str], used_ending_keys: Sequence[str]) -> "CompleteSurfaceLineV2":
    relation = _surface_relation(line.relation_type)
    phrase, phrase_key, role_phrase_keys = _phrase_for_line(line)
    connector, connector_key = _connector_for(line.line_role, relation, sequence_index)
    particle, predicate, predicate_key, ending_key = _choose_predicate(
        relation_type=relation,
        line_role=line.line_role,
        used_predicate_keys=used_predicate_keys,
        used_ending_keys=used_ending_keys,
    )
    # Relation lines get the connector as the relationship carrier; other lines
    # keep it as a sentence-to-sentence transition.  No second-person subject is
    # introduced.
    if line.line_role == "relation" and connector_key == "relation_approach_avoidance":
        body = f"{connector}{phrase}{particle}{predicate}"
    else:
        body = f"{connector}{phrase}{particle}{predicate}"
    max_chars = int(line.max_chars or 120)
    text = _truncate_sentence(body, max_chars)
    distance_policy_key = DISTANCE_POLICY_KEYS.get(line.line_role, "observe_without_overclaim")
    variation_key = f"v{(sequence_index % 3) + 1}"
    signature = _surface_signature_row(
        line=line,
        phrase_key=phrase_key,
        role_phrase_keys=role_phrase_keys,
        connector_key=connector_key,
        particle=particle,
        predicate_key=predicate_key,
        ending_key=ending_key,
        distance_policy_key=distance_policy_key,
        variation_key=variation_key,
    )
    return CompleteSurfaceLineV2(
        sentence_id=line.sentence_id,
        line_role=line.line_role,
        relation_type=relation,
        surface_text=text,
        phrase_unit_ids=line.phrase_unit_ids,
        evidence_span_ids=line.evidence_span_ids,
        role_phrase_key=phrase_key,
        role_phrase_keys=role_phrase_keys,
        subject_policy_key="omit_second_person_subject",
        connector_key=connector_key,
        particle_key=particle,
        predicate_key=predicate_key,
        ending_key=ending_key,
        distance_policy_key=distance_policy_key,
        variation_key=variation_key,
        surface_signature=signature,
        forbidden_surface_keys=line.forbidden_surface_keys,
        source_sentence_plan_line=line.as_meta(),
        meta={
            "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "target_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "surface_intent": line.surface_intent,
            "repair_policy": list(line.repair_policy),
            "surface_realizer_followed_plan": True,
            "raw_input_included": False,
        },
    )


@dataclass(frozen=True)
class CompleteSurfaceLineV2:
    """One internal realized surface line bound to a sentence plan line."""

    sentence_id: str
    line_role: str
    relation_type: str
    surface_text: str
    phrase_unit_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    evidence_span_ids: Iterable[str] = dataclass_field(default_factory=tuple)
    role_phrase_key: str = ""
    role_phrase_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    subject_policy_key: str = "omit_second_person_subject"
    connector_key: str = "none"
    particle_key: str = ""
    predicate_key: str = ""
    ending_key: str = ""
    distance_policy_key: str = "observe_without_overclaim"
    variation_key: str = "v1"
    surface_signature: Mapping[str, Any] = dataclass_field(default_factory=dict)
    forbidden_surface_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    source_sentence_plan_line: Mapping[str, Any] = dataclass_field(default_factory=dict)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_SURFACE_LINE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        relation = _surface_relation(self.relation_type)
        object.__setattr__(self, "sentence_id", _clean_token(self.sentence_id))
        object.__setattr__(self, "line_role", _clean_token(self.line_role) or "core")
        object.__setattr__(self, "relation_type", relation)
        object.__setattr__(self, "surface_text", _truncate_sentence(self.surface_text, 240))
        object.__setattr__(self, "phrase_unit_ids", _dedupe(self.phrase_unit_ids))
        object.__setattr__(self, "evidence_span_ids", _dedupe(self.evidence_span_ids))
        object.__setattr__(self, "role_phrase_key", _clean_token(self.role_phrase_key))
        object.__setattr__(self, "role_phrase_keys", _dedupe(self.role_phrase_keys))
        object.__setattr__(self, "subject_policy_key", _clean_token(self.subject_policy_key) or "omit_second_person_subject")
        object.__setattr__(self, "connector_key", _clean_token(self.connector_key) or "none")
        object.__setattr__(self, "particle_key", _clean(self.particle_key) or "が")
        object.__setattr__(self, "predicate_key", _clean_token(self.predicate_key))
        object.__setattr__(self, "ending_key", _clean_token(self.ending_key))
        object.__setattr__(self, "distance_policy_key", _clean_token(self.distance_policy_key) or "observe_without_overclaim")
        object.__setattr__(self, "variation_key", _clean_token(self.variation_key) or "v1")
        object.__setattr__(self, "surface_signature", _json_safe_mapping(self.surface_signature))
        object.__setattr__(self, "forbidden_surface_keys", _dedupe(self.forbidden_surface_keys))
        object.__setattr__(self, "source_sentence_plan_line", _json_safe_mapping(self.source_sentence_plan_line))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_SURFACE_LINE_SCHEMA_VERSION)

    @property
    def forbidden_surface_hits(self) -> Tuple[str, ...]:
        return _forbidden_surface_hits(self.surface_text)

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.sentence_id:
            errors.append("sentence_id_missing")
        if not self.surface_text:
            errors.append("surface_text_missing")
        if not self.evidence_span_ids:
            errors.append("evidence_span_ids_missing")
        if not self.phrase_unit_ids:
            errors.append("phrase_unit_ids_missing")
        if not self.relation_type:
            errors.append("relation_type_missing")
        if not self.predicate_key:
            errors.append("predicate_key_missing")
        for hit in self.forbidden_surface_hits:
            errors.append(f"forbidden_surface:{hit}")
        return tuple(dict.fromkeys(errors))

    @property
    def usable(self) -> bool:
        return not self.validation_errors

    def as_grounding_row(self) -> dict[str, Any]:
        return {
            "version": self.schema_version,
            "sentence_id": self.sentence_id,
            "surface_text": self.surface_text,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "surface_signature": dict(self.surface_signature),
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": "Step8_Binding_aware_Grounding",
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }

    def as_meta(self, *, include_surface_text: bool = True) -> dict[str, Any]:
        meta = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "sentence_id": self.sentence_id,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "canonical_relation_type": canonical_relation_type(self.relation_type),
            "relation_family": relation_family(self.relation_type),
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "role_phrase_key": self.role_phrase_key,
            "role_phrase_keys": list(self.role_phrase_keys),
            "subject_policy_key": self.subject_policy_key,
            "connector_key": self.connector_key,
            "particle_key": self.particle_key,
            "predicate_key": self.predicate_key,
            "ending_key": self.ending_key,
            "distance_policy_key": self.distance_policy_key,
            "variation_key": self.variation_key,
            "surface_signature": dict(self.surface_signature),
            "surface_text_present": bool(self.surface_text),
            "surface_text_length": len(self.surface_text),
            "forbidden_surface_keys": list(self.forbidden_surface_keys),
            "forbidden_surface_hits": list(self.forbidden_surface_hits),
            "source_sentence_plan_line": dict(self.source_sentence_plan_line),
            "usable": self.usable,
            "validation_errors": list(self.validation_errors),
            "completion_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "fixed_sentence_template_used": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "meta": dict(self.meta),
        }
        if include_surface_text:
            meta["surface_text"] = self.surface_text
        return meta


@dataclass(frozen=True)
class CompleteSurfaceRealizationV2:
    """Internal realized text bundle for Complete Composer initial version."""

    plan_id: str
    coverage_group: str
    surface_lines: Iterable[CompleteSurfaceLineV2 | Mapping[str, Any]] = dataclass_field(default_factory=tuple)
    source_sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    status: str = COMPLETE_SURFACE_STATUS_READY
    schema_version: str = COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION

    def __post_init__(self) -> None:
        lines: list[CompleteSurfaceLineV2] = []
        for item in tuple(self.surface_lines or ()):  # mapping support for tests and future repair
            if isinstance(item, CompleteSurfaceLineV2):
                lines.append(item)
            elif isinstance(item, Mapping):
                lines.append(
                    CompleteSurfaceLineV2(
                        sentence_id=item.get("sentence_id") or "",
                        line_role=item.get("line_role") or "core",
                        relation_type=item.get("relation_type") or "center",
                        surface_text=item.get("surface_text") or "",
                        phrase_unit_ids=item.get("phrase_unit_ids") or item.get("used_phrase_unit_ids") or (),
                        evidence_span_ids=item.get("evidence_span_ids") or item.get("used_evidence_span_ids") or (),
                        role_phrase_key=item.get("role_phrase_key") or "",
                        role_phrase_keys=item.get("role_phrase_keys") or (),
                        subject_policy_key=item.get("subject_policy_key") or "omit_second_person_subject",
                        connector_key=item.get("connector_key") or "none",
                        particle_key=item.get("particle_key") or "",
                        predicate_key=item.get("predicate_key") or "",
                        ending_key=item.get("ending_key") or "",
                        distance_policy_key=item.get("distance_policy_key") or "observe_without_overclaim",
                        variation_key=item.get("variation_key") or "v1",
                        surface_signature=item.get("surface_signature") or {},
                        forbidden_surface_keys=item.get("forbidden_surface_keys") or (),
                        source_sentence_plan_line=item.get("source_sentence_plan_line") or {},
                        meta=item.get("meta") or {},
                    )
                )
        source_plan = _coerce_sentence_plan(self.source_sentence_plan)
        object.__setattr__(self, "plan_id", _clean_token(self.plan_id) or (source_plan.plan_id if source_plan else "complete_surface_realization_v2"))
        object.__setattr__(self, "coverage_group", _clean_token(self.coverage_group) or (source_plan.coverage_group if source_plan else "unknown"))
        object.__setattr__(self, "surface_lines", tuple(lines))
        object.__setattr__(self, "source_sentence_plan", source_plan)
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION)
        status = _clean_token(self.status) or COMPLETE_SURFACE_STATUS_READY
        if status not in {COMPLETE_SURFACE_STATUS_READY, COMPLETE_SURFACE_STATUS_UNAVAILABLE}:
            status = COMPLETE_SURFACE_STATUS_UNAVAILABLE
        if not lines or any(not line.usable for line in lines):
            status = COMPLETE_SURFACE_STATUS_UNAVAILABLE
        object.__setattr__(self, "status", status)

    @property
    def ready(self) -> bool:
        return self.status == COMPLETE_SURFACE_STATUS_READY and not self.validation_errors

    @property
    def realized_text(self) -> str:
        return "".join(line.surface_text for line in self.surface_lines if line.surface_text)

    @property
    def comment_text(self) -> str:
        # Internal candidate text for later gates.  It is not written to the
        # public response key here; ``comment_text_publicly_assigned`` remains
        # false in meta.
        return self.realized_text if self.status == COMPLETE_SURFACE_STATUS_READY else ""

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return _dedupe(item for line in self.surface_lines for item in line.evidence_span_ids)

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return _dedupe(item for line in self.surface_lines for item in line.phrase_unit_ids)

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return _dedupe(line.relation_type for line in self.surface_lines)

    @property
    def ending_keys(self) -> Tuple[str, ...]:
        return tuple(line.ending_key for line in self.surface_lines if line.ending_key)

    @property
    def same_ending_major_count(self) -> int:
        counts: dict[str, int] = {}
        for key in self.ending_keys:
            counts[key] = counts.get(key, 0) + 1
        return sum(1 for count in counts.values() if count >= 3)

    @property
    def surface_signatures(self) -> Tuple[str, ...]:
        return tuple(str(line.surface_signature.get("signature") or "") for line in self.surface_lines if line.surface_signature.get("signature"))

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors: list[str] = []
        if not self.surface_lines:
            errors.append("surface_lines_missing")
        for index, line in enumerate(self.surface_lines):
            for reason in line.validation_errors:
                errors.append(f"line_{index}:{reason}")
        if self.same_ending_major_count > 0:
            errors.append("same_ending_major_detected")
        source_plan = self.source_sentence_plan
        if isinstance(source_plan, CompleteSentencePlanV2):
            plan_sentence_ids = {line.sentence_id for line in source_plan.sentence_plans}
            surface_sentence_ids = {line.sentence_id for line in self.surface_lines}
            if plan_sentence_ids and plan_sentence_ids != surface_sentence_ids:
                errors.append("surface_sentence_ids_do_not_match_plan")
            if len(self.surface_lines) != len(source_plan.sentence_plans):
                errors.append("surface_line_count_does_not_match_plan")
        return tuple(dict.fromkeys(errors))

    def as_grounding_input(self) -> dict[str, Any]:
        return {
            "version": COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": "Step8_Binding_aware_Grounding",
            "plan_id": self.plan_id,
            "coverage_group": self.coverage_group,
            "realized_text": self.realized_text,
            "surface_lines": [line.as_grounding_row() for line in self.surface_lines],
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "surface_signatures": list(self.surface_signatures),
            "raw_input_included": False,
        }

    def as_meta(self, *, include_realized_text: bool = True) -> dict[str, Any]:
        term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
        source_binding = build_complete_sentence_binding_bundle_meta(self.source_sentence_plan) if isinstance(self.source_sentence_plan, CompleteSentencePlanV2) else {}
        meta = {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "service_version": COMPLETE_SURFACE_REALIZER_VERSION,
            "target_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "step": COMPLETE_SURFACE_REALIZER_STAGE,
            "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "stage": COMPLETE_COMPOSER_STAGE,
            "implementation_unit": COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT,
            "target_composer_term": term_meta["target_composer_term"],
            "target_composer_family_term": term_meta["target_composer_family_term"],
            "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
            "status": self.status,
            "ready": self.ready,
            "plan_id": self.plan_id,
            "coverage_group": self.coverage_group,
            "surface_realizer_2_0_added": True,
            "surface_realizer_added": True,
            "surface_text_generated": bool(self.realized_text),
            "internal_realized_text_generated": bool(self.realized_text),
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "comment_text_publicly_assigned": False,
            "public_comment_text_assigned": False,
            "comment_text_contract": "passed_only",
            "source_sentence_plan_step": COMPLETE_SENTENCE_PLAN_STAGE,
            "sentence_plan_followed": not any("plan" in reason for reason in self.validation_errors),
            "surface_realizer_must_follow_plan": True,
            "surface_realizer_free_invention_blocked": True,
            "sentence_plan_line_count": len(tuple(self.source_sentence_plan.sentence_plans)) if isinstance(self.source_sentence_plan, CompleteSentencePlanV2) else None,
            "surface_line_count": len(self.surface_lines),
            "surface_component_row_count": len(self.surface_lines),
            "surface_text_in_meta": False,
            "surface_tail_key_count": len(self.ending_keys),
            "unique_tail_key_count": len(set(self.ending_keys)),
            "repeated_tail_keys": [key for key in dict.fromkeys(self.ending_keys) if self.ending_keys.count(key) > 1],
            "same_ending_detected": len(set(self.ending_keys)) != len(self.ending_keys),
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "surface_signature_version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "surface_signatures": list(self.surface_signatures),
            "surface_signature_rows": [dict(line.surface_signature) for line in self.surface_lines],
            "same_ending_major_count": self.same_ending_major_count,
            "same_ending_guard_passed": self.same_ending_major_count == 0,
            "second_person_subject_omitted": all(line.subject_policy_key == "omit_second_person_subject" for line in self.surface_lines),
            "subject_policy_applied": True,
            "subject_policy_enabled": True,
            "connector_policy_applied": True,
            "connector_policy_enabled": True,
            "predicate_bank_applied": True,
            "predicate_bank_enabled": True,
            "ending_policy_applied": True,
            "ending_policy_enabled": True,
            "distance_policy_applied": True,
            "distance_policy_enabled": True,
            "variation_policy_applied": True,
            "variation_policy_enabled": True,
            "surface_signature_recorded": True,
            "predicate_keys": [line.predicate_key for line in self.surface_lines if line.predicate_key],
            "tail_keys": list(self.ending_keys),
            "used_tail_keys": list(self.ending_keys),
            "surface_tail_key_count": len(self.ending_keys),
            "unique_tail_key_count": len(set(self.ending_keys)),
            "repeated_tail_keys": [key for key in dict.fromkeys(self.ending_keys) if self.ending_keys.count(key) >= 2],
            "same_ending_detected": len(set(self.ending_keys)) != len(self.ending_keys),
            "same_ending_major_detected": self.same_ending_major_count > 0,
            "surface_component_rows": [line.as_meta(include_surface_text=False) for line in self.surface_lines],
            "surface_component_row_count": len(self.surface_lines),
            "surface_lines": [line.as_meta(include_surface_text=include_realized_text) for line in self.surface_lines],
            "surface_component_rows": [_surface_component_row_meta(line) for line in self.surface_lines],
            "grounding_input": self.as_grounding_input(),
            "source_sentence_binding_bundle": source_binding,
            "completion_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "fixed_sentence_template_used": False,
            "fixed_sentence_template_added": False,
            "completion_sentence_templates_added": False,
            "external_ai_used": False,
            "external_ai_allowed": False,
            "local_llm_used": False,
            "local_llm_allowed": False,
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_improvement": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "validation_errors": list(dict.fromkeys(list(self.validation_errors) + list(self.meta.get("validation_errors") or []))),
            "meta": dict(self.meta),
        }
        if include_realized_text:
            meta["realized_text"] = self.realized_text
        return meta




def _surface_component_row_meta(line: "CompleteSurfaceLineV2") -> dict[str, Any]:
    """Return a text-free component row for Template/Echo Guard style checks."""

    if isinstance(line, CompleteSurfaceLineV2):
        row = line.as_meta(include_surface_text=False)
        row.pop("surface_text", None)
        row["surface_text_in_meta"] = False
        row["componentized_surface_realizer"] = True
        row["grammar_parts_only"] = True
        row["raw_input_included"] = False
        return row
    return {}

def build_complete_surface_realizer_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    return {
        "version": COMPLETE_SURFACE_REALIZER_VERSION,
        "service_version": COMPLETE_SURFACE_REALIZER_VERSION,
        "target_step": COMPLETE_SURFACE_REALIZER_STAGE,
        "step": COMPLETE_SURFACE_REALIZER_STAGE,
        "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "surface_realizer_2_0_added": True,
        "surface_realizer_added": True,
        "accepts_sentence_plan_2_0": True,
        "accepts_complete_sentence_plan_v2": True,
        "sentence_plan_must_be_followed": True,
        "surface_realizer_must_follow_plan": True,
        "subject_policy_enabled": True,
        "predicate_bank_enabled": True,
        "connector_policy_enabled": True,
        "ending_policy_enabled": True,
        "distance_policy_enabled": True,
        "variation_policy_enabled": True,
        "surface_signature_recorded": True,
        "subject_policy_added": True,
        "subject_policy_enabled": True,
        "predicate_bank_added": True,
        "predicate_bank_enabled": True,
        "connector_policy_added": True,
        "connector_policy_enabled": True,
        "ending_policy_added": True,
        "ending_policy_enabled": True,
        "distance_policy_added": True,
        "distance_policy_enabled": True,
        "variation_policy_added": True,
        "variation_policy_enabled": True,
        "surface_signature_added": True,
        "surface_signature_recorded": True,
        "surface_signature_enabled": True,
        "surface_signature_to_template_guard": True,
        "surface_text_internal_only": True,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "comment_text_contract": "passed_only",
        "completion_sentence_template_used": False,
        "completed_sentence_template_allowed": False,
        "role_completed_sentence_template_used": False,
        "role_completed_sentence_template_added": False,
        "input_specific_template_used": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_allowed": False,
        "coverage_group_completed_sentence_added": False,
        "completion_sentence_templates_added": False,
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
    }


def build_complete_surface_realization_v2(
    *,
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    sentence_plan_v2: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    observation_graph: Any = None,
    relation_graph: Any = None,
    coverage_plan: Any = None,
    material_bundle: Any = None,
    focus_selector_input: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    phrase_units: Sequence[Any] | None = None,
    sentence_plan_seed: Mapping[str, Any] | None = None,
    coverage_group: str = "",
    meta: Mapping[str, Any] | None = None,
    **planner_kwargs: Any,
) -> CompleteSurfaceRealizationV2:
    source_plan = _coerce_sentence_plan(sentence_plan or sentence_plan_v2 or plan)
    if source_plan is None:
        source_plan = build_complete_sentence_plan_v2(
            observation_graph=observation_graph,
            relation_graph=relation_graph,
            coverage_plan=coverage_plan,
            material_bundle=material_bundle,
            focus_selector_input=focus_selector_input,
            evidence_spans=evidence_spans,
            phrase_units=phrase_units,
            sentence_plan_seed=sentence_plan_seed,
            coverage_group=coverage_group,
            **planner_kwargs,
        )
    if not source_plan.usable:
        return CompleteSurfaceRealizationV2(
            plan_id=source_plan.plan_id,
            coverage_group=source_plan.coverage_group,
            surface_lines=(),
            source_sentence_plan=source_plan,
            status=COMPLETE_SURFACE_STATUS_UNAVAILABLE,
            meta={
                **build_complete_surface_realizer_contract_meta(),
                **_json_safe_mapping(meta),
                "validation_errors": list(source_plan.validation_errors),
                "reason": "sentence_plan_unusable",
                "raw_input_included": False,
            },
        )
    used_predicate_keys: list[str] = []
    used_ending_keys: list[str] = []
    surface_lines: list[CompleteSurfaceLineV2] = []
    for index, line in enumerate(source_plan.sentence_plans):
        surface_line = _realize_line(
            line,
            sequence_index=index,
            used_predicate_keys=used_predicate_keys,
            used_ending_keys=used_ending_keys,
        )
        surface_lines.append(surface_line)
        used_predicate_keys.append(surface_line.predicate_key)
        used_ending_keys.append(surface_line.ending_key)
    realization = CompleteSurfaceRealizationV2(
        plan_id=source_plan.plan_id,
        coverage_group=source_plan.coverage_group,
        surface_lines=surface_lines,
        source_sentence_plan=source_plan,
        status=COMPLETE_SURFACE_STATUS_READY,
        meta={
            **build_complete_surface_realizer_contract_meta(),
            **_json_safe_mapping(meta),
            "source_plan_summary": {
                "version": source_plan.schema_version,
                "source_step": COMPLETE_SENTENCE_PLAN_STAGE,
                "plan_id": source_plan.plan_id,
                "coverage_group": source_plan.coverage_group,
                "sentence_budget": source_plan.sentence_budget,
                "raw_input_included": False,
            },
        },
    )
    return realization


def build_complete_surface_realizer_v2(**kwargs: Any) -> CompleteSurfaceRealizationV2:
    return build_complete_surface_realization_v2(**kwargs)


def build_complete_surface_realizer(**kwargs: Any) -> CompleteSurfaceRealizationV2:
    return build_complete_surface_realization_v2(**kwargs)


def realize_complete_surface(**kwargs: Any) -> CompleteSurfaceRealizationV2:
    return build_complete_surface_realization_v2(**kwargs)


def build_complete_surface_signature(realization: CompleteSurfaceRealizationV2 | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(realization, CompleteSurfaceRealizationV2):
        rows = [dict(line.surface_signature) for line in realization.surface_lines]
        signatures = list(realization.surface_signatures)
        ending_keys = list(realization.ending_keys)
        return {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "signature_count": len(signatures),
            "surface_signatures": signatures,
            "surface_signature_rows": rows,
            "ending_keys": ending_keys,
            "same_ending_major_count": realization.same_ending_major_count,
            "same_ending_guard_passed": realization.same_ending_major_count == 0,
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }
    if isinstance(realization, Mapping):
        rows = list(realization.get("surface_signature_rows") or realization.get("surface_signatures") or ())
        return {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "signature_count": len(rows),
            "surface_signature_rows": _json_safe_value(rows),
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }
    return {
        "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
        "signature_count": 0,
        "surface_signatures": [],
        "completion_sentence_template_used": False,
        "raw_input_included": False,
    }


def build_complete_surface_realizer_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    realization = build_complete_surface_realization_v2(**kwargs)
    meta = realization.as_meta(include_realized_text=include_realized_text)
    meta["surface_signature"] = build_complete_surface_signature(realization)
    meta["surface_signature_meta"] = meta["surface_signature"]
    return meta


def build_complete_surface_realizer_v2_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return build_complete_surface_realizer_meta(include_realized_text=include_realized_text, **kwargs)


def build_complete_surface_realization_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return build_complete_surface_realizer_meta(include_realized_text=include_realized_text, **kwargs)


# Compatibility aliases for concise import names in future Step 8/9 work.
CompleteSurfaceLine = CompleteSurfaceLineV2
CompleteSurfaceRealization = CompleteSurfaceRealizationV2
CompleteSurfaceRealizerResult = CompleteSurfaceRealizationV2

__all__ = [
    "COMPLETE_SURFACE_LINE_SCHEMA_VERSION",
    "COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION",
    "COMPLETE_SURFACE_REALIZER_SERVICE_VERSION",
    "COMPLETE_SURFACE_REALIZER_STAGE",
    "COMPLETE_SURFACE_REALIZER_STEP",
    "COMPLETE_SURFACE_REALIZER_TARGET_STEP",
    "COMPLETE_SURFACE_REALIZER_VERSION",
    "COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION",
    "CompleteSurfaceLine",
    "CompleteSurfaceLineV2",
    "CompleteSurfaceRealization",
    "CompleteSurfaceRealizationV2",
    "CompleteSurfaceRealizerResult",
    "build_complete_surface_realization_meta",
    "build_complete_surface_realization_v2",
    "build_complete_surface_realizer",
    "build_complete_surface_realizer_contract_meta",
    "build_complete_surface_realizer_meta",
    "build_complete_surface_realizer_v2",
    "build_complete_surface_realizer_v2_meta",
    "build_complete_surface_signature",
    "realize_complete_surface",
]
