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
from emlis_ai_complete_tone_policy import (
    COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_STAGE,
    COMPLETE_TONE_ENGINE_VERSION,
    COMPLETE_TONE_ENGINE_2_1_VERSION,
    COMPLETE_TONE_POLICY_VERSION,
    COMPLETE_TONE_POLICY_2_1_VERSION,
    CompleteTonePolicy,
    build_complete_tone_guard_report,
    build_complete_tone_policy,
    build_complete_tone_policy_contract_meta,
    coerce_complete_tone_policy,
)
from emlis_ai_limited_relation_taxonomy import (
    canonical_relation_type,
    normalize_relation_type,
    relation_family,
)
from emlis_ai_relation_surface_contract import (
    RELATION_SURFACE_CONTRACT_VERSION,
    detect_relation_surface,
    relation_marker_key,
    relation_marker_meta,
)
from emlis_ai_complete_surface_realizer_anti_template import (
    COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
    COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
    COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
    build_surface_realizer_anti_template_policy_meta,
    build_surface_realizer_anti_template_report,
    connector_family_key as _anti_template_connector_family_key,
    ending_family_key as _anti_template_ending_family_key,
    opening_family_key as _anti_template_opening_family_key,
    predicate_family_key as _anti_template_predicate_family_key,
)
from emlis_ai_observation_surface_realizer import (
    OBSERVATION_SURFACE_REALIZER_STEP,
    OBSERVATION_SURFACE_REALIZER_VERSION,
    build_observation_surface_realizer_contract_meta,
)

COMPLETE_SURFACE_REALIZER_VERSION = "emlis.complete_surface_realizer.v2_1"
COMPLETE_SURFACE_REALIZER_2_0_VERSION = "emlis.complete_surface_realizer.v2"
COMPLETE_SURFACE_REALIZER_SERVICE_VERSION = COMPLETE_SURFACE_REALIZER_VERSION
COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION = "emlis.complete_surface_realization.v2"
COMPLETE_SURFACE_LINE_SCHEMA_VERSION = "emlis.complete_surface_line.v2"
COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION = "emlis.complete_surface_signature.v2"
COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION = "emlis.complete_product_quality_surface_variation.v2"
COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP = "Step3_Surface_variation_strengthening"
COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION = "emlis.complete_product_quality_surface_variation_report.v2"
COMPLETE_SURFACE_VARIATION_POLICY_VERSION = "emlis.complete_surface_variation_policy.v2"
COMPLETE_SURFACE_VARIATION_PROFILE_VERSION = "emlis.complete_surface_variation_profile.v2"
COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION = COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION
COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP = COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP
COMPLETE_SURFACE_REALIZER_STAGE = "Step7_Surface_Realizer_2_0"
COMPLETE_SURFACE_REALIZER_STEP = COMPLETE_SURFACE_REALIZER_STAGE
COMPLETE_SURFACE_REALIZER_TARGET_STEP = COMPLETE_SURFACE_REALIZER_STAGE
COMPLETE_SURFACE_REALIZER_IMPLEMENTATION_UNIT = "Commit 7"
COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP = "Step4_Surface_recovery_relation_line_alignment"

COMPLETE_SURFACE_STATUS_READY = "ready"
COMPLETE_SURFACE_STATUS_UNAVAILABLE = "unavailable"

ANTI_TEMPLATE_SUPPRESSED_CONNECTOR_KEYS = {"sono_nakademo", "core_center"}
ANTI_TEMPLATE_GENERIC_CENTER_PREDICATE_KEYS = {"center_core"}

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

# Internal structural labels only.  They never come from raw input and are used
# only to decide whether a planned recovery relation line may mention prior load.
RECOVERY_PRIOR_LOAD_ROLE_KEYS = {
    "fatigue_accumulation",
    "load_accumulation",
    "limit_pressure",
    "pressure",
    "burden_fear",
    "hurt_core",
    "hurt_residue",
    "anticipation_loop",
    "small_wobble",
    "residue",
    "pressure_or_load",
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
    "primary_phrase": ("いま扱う核", "primary_phrase"),
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
        ("として", "重なりを保っています", "coexistence_overlap", "tamotsu"),
        ("も", "片方だけに減らずに残っています", "coexistence_not_reduced", "nokoru"),
        ("が", "同じ流れの中で並んでいます", "coexistence_flow_parallel", "narabu"),
        ("として", "同じ場面の中で並んでいます", "coexistence_scene_parallel", "narabu"),
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
        ("が", "いま前に出ています", "center_front", "deru"),
        ("として", "言葉の中に置かれています", "center_placed", "oku"),
        ("も", "軸として残っています", "center_axis", "nokoru"),
        ("が", "根拠のある範囲にあります", "center_grounded_exists", "aru"),
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

# Product-quality Step3: connector candidates are still grammar parts, not
# completed sentences.  They let the realizer avoid repeating the same transition
# shape while staying inside the relation declared by the SentencePlan.
CONNECTOR_VARIATION_BANK: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "opening": {
        "default": (("", "none"),),
        "pressure": (("まず、", "opening_pressure_first"), ("はじめに、", "opening_pressure_begin")),
        "recovery": (("はじめに、", "opening_recovery_first"), ("最初に、", "opening_recovery_begin")),
    },
    "core": {
        "default": (("そこでは、", "core_there"), ("続いて、", "core_continue"), ("その中で、", "core_inside")),
        "pressure": (("その重さの中で、", "core_pressure_weight"), ("圧力のある場面として、", "core_pressure_scene"), ("その中で、", "core_inside_pressure")),
        "recovery": (("戻る流れとして、", "core_recovery_flow"), ("そこに、", "core_recovery_there")),
        "contrast": (("もう一方では、", "core_contrast_other_side"), ("別の向きとして、", "core_contrast_direction"), ("その中で、", "core_inside_contrast")),
        "coexistence": (("重なりとして、", "core_coexistence_overlap"), ("同じ流れの中で、", "core_coexistence_flow"), ("その中で、", "core_inside_coexistence")),
        "approach_avoidance": (("その線上で、", "core_approach_avoidance_line"), ("同じ場所に、", "core_approach_avoidance_place")),
    },
    "relation": {
        "default": (("並んで、", "relation_parallel"), ("同時に、", "relation_same_time")),
        "contrast": (("一方で、", "relation_contrast_other_side"), ("ただ、", "relation_contrast_but")),
        "coexistence": (("重なって、", "relation_coexistence_overlap"), ("同じ流れの中で、", "relation_coexistence_flow"), ("同時に、", "relation_coexistence_same_time")),
        "pressure": (("その重さの中で、", "relation_pressure_weight"), ("その圧力の中で、", "relation_pressure_inside")),
        "recovery": (("戻る流れとして、", "relation_recovery_flow"), ("それでも、", "relation_recovery_after_load")),
        "approach_avoidance": (("向かう動きと止まる動きが、", "relation_approach_avoidance_motion"), ("近づきたい方と止まりたい方が、", "relation_approach_avoidance")),
    },
    "closing": {
        "default": (("最後は、", "closing_default"), ("締めでは、", "closing_soft")),
        "recovery": (("締めでは、", "closing_recovery"), ("最後は、", "closing_recovery_last")),
        "pressure": (("締めでは、", "closing_pressure"), ("最後は、", "closing_pressure_last")),
        "contrast": (("最後は、", "closing_contrast_last"), ("締めでは、", "closing_contrast_soft")),
        "coexistence": (("最後は、", "closing_coexistence_last"), ("締めでは、", "closing_coexistence_soft")),
        "approach_avoidance": (("最後は、", "closing_approach_avoidance_last"), ("締めでは、", "closing_approach_avoidance_soft")),
    },
}

CONNECTOR_VARIATION_FALLBACKS: dict[str, tuple[tuple[str, str], ...]] = {
    "opening": (
        ("", "none"),
        ("最初に、", "opening_initial"),
        ("ここでは、", "opening_here"),
    ),
    "core": (
        ("そこでは、", "core_there"),
        ("続いて、", "core_continue"),
        ("もう一つは、", "core_another"),
        ("その中で、", "core_inside"),
    ),
    "relation": (
        ("重なって、", "relation_overlap"),
        ("その一方で、", "relation_other_side"),
        ("並んで、", "relation_parallel"),
        ("同時に、", "relation_same_time"),
        ("ただ、", "relation_contrast_but"),
    ),
    "closing": (
        ("最後は、", "closing_default"),
        ("締めでは、", "closing_wrap"),
        ("残る形として、", "closing_residue"),
    ),
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

def _observation_line_meta(line: CompleteSentencePlanLine | Mapping[str, Any] | None) -> dict[str, Any]:
    if line is None:
        return {}
    if hasattr(line, "as_meta"):
        meta = line.as_meta()
    elif isinstance(line, Mapping):
        meta = dict(line)
    else:
        meta = {}
    nested = meta.get("meta") if isinstance(meta.get("meta"), Mapping) else {}
    out = dict(nested)
    for key in (
        "observation_roles",
        "sentence_plan_observation_roles",
        "observation_reply_kind",
        "question_required",
        "known_scope_only",
        "unknown_slots",
        "inference_depth",
        "user_fact_grounding_mode",
        "surface_role_merge",
    ):
        if key in meta and key not in out:
            out[key] = meta[key]
    return out


def _observation_roles_for_line(line: CompleteSentencePlanLine | Mapping[str, Any] | None) -> Tuple[str, ...]:
    meta = _observation_line_meta(line)
    roles = meta.get("observation_roles") or meta.get("sentence_plan_observation_roles") or ()
    return _dedupe(roles)


def _observation_surface_signature_meta(line: CompleteSentencePlanLine | Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _observation_line_meta(line)
    roles = list(_observation_roles_for_line(line))
    unknown_slots = list(_dedupe(meta.get("unknown_slots")))
    try:
        depth = int(meta.get("inference_depth") or 0)
    except (TypeError, ValueError):
        depth = 0
    if depth < 0:
        depth = 0
    if depth > 3:
        depth = 3
    return {
        "observation_surface_realizer_step": OBSERVATION_SURFACE_REALIZER_STEP,
        "observation_surface_realizer_version": OBSERVATION_SURFACE_REALIZER_VERSION,
        "observation_roles": roles,
        "sentence_plan_observation_roles": roles,
        "observation_reply_kind": _clean_token(meta.get("observation_reply_kind")),
        "question_required": bool(meta.get("question_required")),
        "known_scope_only": bool(meta.get("known_scope_only")),
        "unknown_slots": unknown_slots,
        "inference_depth": depth or None,
        "user_fact_grounding_mode": _clean_token(meta.get("user_fact_grounding_mode")),
        "surface_role_merge": list(_dedupe(meta.get("surface_role_merge"))),
        "comment_text_generated": False,
        "raw_input_included": False,
    }


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
    if line.line_role == "opening" and keys and keys[0] == "primary_phrase":
        # Step7 / Surface Realizer 2.1 Anti-Template: keep the source role
        # binding, but do not surface the opening as the screenshot-like
        # "center phrase + center predicate" skeleton.
        return "今出ている感覚", "opening_current_expression", _dedupe(("opening_current_expression", *keys))
    return phrases[0], keys[0], tuple(keys)


def _connector_candidates(line_role: str, relation_type: str, sequence_index: int) -> tuple[tuple[str, str], ...]:
    if sequence_index <= 0 and line_role == "opening":
        return (("", "none"),)
    role = _clean_token(line_role) or "core"
    relation = _surface_relation(relation_type)
    variation_bank = CONNECTOR_VARIATION_BANK.get(role) or CONNECTOR_VARIATION_BANK["core"]
    legacy_bank = CONNECTOR_BANK.get(role) or CONNECTOR_BANK["core"]
    candidates: list[tuple[str, str]] = []
    variation_pairs = (
        *(variation_bank.get(relation) or ()),
        *(variation_bank.get(canonical_relation_type(relation)) or ()),
        *(variation_bank.get("default") or ()),
    )
    legacy_pairs = (
        legacy_bank.get(relation),
        legacy_bank.get(canonical_relation_type(relation)),
        legacy_bank.get("default"),
        *(CONNECTOR_VARIATION_FALLBACKS.get(role) or ()),
    )
    for pair in (*variation_pairs, *legacy_pairs):
        if not pair:
            continue
        connector, key = pair
        row = (_clean(connector), _clean_token(key) or "none")
        if row[1] in ANTI_TEMPLATE_SUPPRESSED_CONNECTOR_KEYS:
            continue
        if row not in candidates:
            candidates.append(row)
    return tuple(candidates or (("", "none"),))


def _connector_for(
    line_role: str,
    relation_type: str,
    sequence_index: int,
    used_connector_keys: Sequence[str] | None = None,
) -> tuple[str, str]:
    used = {key for key in (used_connector_keys or ()) if key and key != "none"}
    used_families = {_anti_template_connector_family_key(key) for key in used}
    previous_key = (tuple(used_connector_keys or ())[-1] if used_connector_keys else "")
    previous_family = _anti_template_connector_family_key(previous_key)
    candidates = _connector_candidates(line_role, relation_type, sequence_index)
    for connector, key in candidates:
        family = _anti_template_connector_family_key(key, connector)
        if key == "none" or (key not in used and family not in used_families):
            return connector, key
    for connector, key in candidates:
        family = _anti_template_connector_family_key(key, connector)
        if key == "none" or family != previous_family:
            return connector, key
    return candidates[0]


def _predicate_candidates(relation_type: str, line_role: str) -> tuple[tuple[str, str, str, str], ...]:
    relation = _surface_relation(relation_type)
    candidates = list(PREDICATE_BANK.get(relation) or PREDICATE_BANK.get(canonical_relation_type(relation)) or DEFAULT_PREDICATES)
    if line_role == "closing":
        candidates.extend([
            ("として", "静かに残っています", "closing_quiet_remain", "nokoru"),
            ("が", "結論にされずにあります", "closing_no_forced_conclusion", "aru"),
        ])
    if line_role == "opening":
        candidates = [row for row in candidates if row[2] not in ANTI_TEMPLATE_GENERIC_CENTER_PREDICATE_KEYS]
        if relation in {"center", "context"}:
            candidates = [
                ("が", "いま前に出ています", "opening_current_front", "deru"),
                ("として", "言葉の中に置かれています", "opening_word_placed", "oku"),
                *candidates,
            ]
    if line_role == "relation":
        candidates.extend([
            ("として", "分かれずに扱われています", "relation_not_split", "atsukau"),
            ("が", "同じ流れの中で並んでいます", "relation_flow_parallel", "narabu"),
        ])
    return tuple(candidates)


def _choose_predicate(*, relation_type: str, line_role: str, used_predicate_keys: Sequence[str], used_ending_keys: Sequence[str]) -> tuple[str, str, str, str]:
    used_predicates = set(used_predicate_keys or ())
    used_endings = set(used_ending_keys or ())
    used_predicate_families = {_anti_template_predicate_family_key(key) for key in used_predicates}
    used_ending_families = {_anti_template_ending_family_key(key) for key in used_endings}
    candidates = _predicate_candidates(relation_type, line_role)
    for particle, predicate, predicate_key, ending_key in candidates:
        predicate_family = _anti_template_predicate_family_key(predicate_key, ending_key)
        ending_family = _anti_template_ending_family_key(ending_key)
        if (
            predicate_key not in used_predicates
            and ending_key not in used_endings
            and predicate_family not in used_predicate_families
            and ending_family not in used_ending_families
        ):
            return particle, predicate, predicate_key, ending_key
    for particle, predicate, predicate_key, ending_key in candidates:
        predicate_family = _anti_template_predicate_family_key(predicate_key, ending_key)
        if predicate_key not in used_predicates and predicate_family not in used_predicate_families:
            return particle, predicate, predicate_key, ending_key
    for particle, predicate, predicate_key, ending_key in candidates:
        if predicate_key not in used_predicates:
            return particle, predicate, predicate_key, ending_key
    return candidates[0] if candidates else DEFAULT_PREDICATES[0]


def _tone_constraint_for_line(tone_policy: CompleteTonePolicy | Mapping[str, Any] | None, line: CompleteSentencePlanLine, relation: str) -> dict[str, Any]:
    policy = coerce_complete_tone_policy(tone_policy, coverage_group=getattr(line, 'coverage_group', '') if hasattr(line, 'coverage_group') else '')
    constraint = policy.constraint_for(sentence_id=line.sentence_id, line_role=line.line_role, relation_type=relation)
    return constraint.as_meta()


def _tone_guard_keys(constraint: Mapping[str, Any]) -> Tuple[str, ...]:
    return _dedupe(constraint.get('guard_keys'))


def _truncate_sentence(sentence: str, max_chars: int) -> str:
    text = _clean(sentence)
    if not text:
        return ""
    if not text.endswith(("。", "！", "？")):
        text = f"{text}。"
    if max_chars > 0 and len(text) > max_chars:
        text = text[: max(8, max_chars - 1)].rstrip(_TRIM) + "。"
    return text



def _line_meta_flag(line: CompleteSentencePlanLine, key: str) -> bool:
    meta = line.meta if isinstance(line.meta, Mapping) else {}
    value = meta.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "present", "detected"}


def _relation_surface_context_flags(line: CompleteSentencePlanLine, relation: str) -> dict[str, Any]:
    roles = set(_meaning_roles(line))
    meta = line.meta if isinstance(line.meta, Mapping) else {}
    prior_load_present = (
        canonical_relation_type(relation) == "recovery"
        and (
            bool(roles.intersection(RECOVERY_PRIOR_LOAD_ROLE_KEYS))
            or _line_meta_flag(line, "prior_load_present")
            or bool(meta.get("prior_load_hint"))
            or bool(meta.get("prior_load_roles"))
        )
    )
    return {
        "prior_load_present": bool(prior_load_present),
        "role_keys": sorted(roles),
        "raw_input_included": False,
    }


def _relation_surface_alignment_for_line(
    line: CompleteSentencePlanLine,
    *,
    relation: str,
    text: str,
) -> tuple[str, dict[str, Any]]:
    """Align recovery relation lines with the shared surface contract.

    This does not relax Reader.  It only rewrites an already-planned recovery
    relation line to a relation cue that Reader and Self-Repair share.
    """

    base_signal = detect_relation_surface(text, expected_relation_types=(relation,))
    if line.line_role != "relation" or canonical_relation_type(relation) != "recovery":
        return text, {
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "surface_recovery_relation_line_aligned": False,
            "relation_surface_signal": base_signal,
            "reader_relation_signal_detected": bool(base_signal.get("reader_relation_signal_detected")),
            "reader_relation_signal_count": int(base_signal.get("reader_relation_signal_count") or base_signal.get("count") or 0),
            "reader_relation_signal_keys": list(base_signal.get("reader_relation_signal_keys") or base_signal.get("keys") or []),
            "raw_input_included": False,
        }

    context_flags = _relation_surface_context_flags(line, relation)
    marker = relation_marker_meta(relation, context_flags=context_flags)
    # Step4 aligns the Surface relation line itself with the same marker family
    # Self-Repair uses.  This keeps Reader / Surface / Repair on one contract
    # without relaxing the Gate and without creating a fallback observation.
    aligned_text = _truncate_sentence(marker.get("relation_marker_phrase") or text, int(line.max_chars or 120))
    marker_applied = aligned_text != text
    signal = detect_relation_surface(aligned_text, expected_relation_types=(relation,))
    marker_key = str(marker.get("relation_marker_key") or relation_marker_key(relation, context_flags=context_flags))
    return aligned_text, {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": True,
        "surface_recovery_relation_alignment_step": COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
        "surface_recovery_relation_marker_applied": marker_applied,
        "surface_relation_marker_key": marker_key,
        "relation_marker_key": marker_key,
        "relation_surface_signal": signal,
        "reader_relation_signal_detected": bool(signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "reader_relation_signal_count": int(signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "reader_relation_signal_keys": list(signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "reader_relation_signal_relation_types": list(signal.get("reader_relation_signal_relation_types") or signal.get("relation_types") or []),
        "expected_relation_types": list(signal.get("expected_relation_types") or [canonical_relation_type(relation)]),
        "relation_surface_context_flags": context_flags,
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }


def _surface_relation_contract_keys(relation_surface_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _json_safe_mapping(relation_surface_meta)
    signal = meta.get("relation_surface_signal") if isinstance(meta.get("relation_surface_signal"), Mapping) else {}
    marker_key = _clean_token(meta.get("surface_relation_marker_key") or meta.get("relation_marker_key"))
    return {
        "relation_surface_contract_version": meta.get("relation_surface_contract_version") or RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": bool(meta.get("surface_recovery_relation_line_aligned")),
        "surface_recovery_relation_alignment_step": meta.get("surface_recovery_relation_alignment_step") or "",
        "surface_recovery_relation_marker_applied": bool(meta.get("surface_recovery_relation_marker_applied")),
        "surface_relation_marker_key": marker_key,
        "relation_marker_key": marker_key,
        "relation_surface_signal_detected": bool(signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "relation_surface_signal_count": int(signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "relation_surface_signal_keys": list(signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "reader_relation_signal_detected": bool(meta.get("reader_relation_signal_detected") or signal.get("reader_relation_signal_detected") or signal.get("detected")),
        "reader_relation_signal_count": int(meta.get("reader_relation_signal_count") or signal.get("reader_relation_signal_count") or signal.get("count") or 0),
        "reader_relation_signal_keys": list(meta.get("reader_relation_signal_keys") or signal.get("reader_relation_signal_keys") or signal.get("keys") or []),
        "expected_relation_types": list(meta.get("expected_relation_types") or signal.get("expected_relation_types") or []),
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }


def _relation_surface_report_from_lines(lines: Sequence["CompleteSurfaceLineV2"] | None) -> dict[str, Any]:
    marker_keys: list[str] = []
    signal_keys: list[str] = []
    relation_types: list[str] = []
    aligned_sentence_ids: list[str] = []
    signal_count = 0
    signal_detected = False
    for line in tuple(lines or ()):  # defensive for mapping-created test rows
        meta = dict(line.meta) if isinstance(line.meta, Mapping) else {}
        signature = dict(line.surface_signature) if isinstance(line.surface_signature, Mapping) else {}
        if bool(meta.get("surface_recovery_relation_line_aligned") or signature.get("surface_recovery_relation_line_aligned")):
            aligned_sentence_ids.append(line.sentence_id)
        marker_key = _clean(meta.get("surface_relation_marker_key") or meta.get("relation_marker_key") or signature.get("surface_relation_marker_key") or signature.get("relation_marker_key"))
        if marker_key:
            marker_keys.append(marker_key)
        signal = meta.get("relation_surface_signal") or signature.get("relation_surface_signal") or {}
        if isinstance(signal, Mapping):
            signal_detected = signal_detected or bool(signal.get("reader_relation_signal_detected") or signal.get("detected"))
            try:
                signal_count += int(signal.get("reader_relation_signal_count") or signal.get("count") or 0)
            except (TypeError, ValueError):
                signal_count += 0
            signal_keys.extend(str(item) for item in signal.get("reader_relation_signal_keys") or signal.get("keys") or [])
            relation_types.extend(str(item) for item in signal.get("reader_relation_signal_relation_types") or signal.get("relation_types") or [])
        signal_keys.extend(str(item) for item in meta.get("reader_relation_signal_keys") or signature.get("reader_relation_signal_keys") or [])
        relation_types.extend(str(item) for item in meta.get("reader_relation_signal_relation_types") or signature.get("reader_relation_signal_relation_types") or [])
    marker_keys_tuple = _dedupe(marker_keys)
    signal_keys_tuple = _dedupe(signal_keys)
    relation_types_tuple = _dedupe(relation_types)
    signal_detected = bool(signal_detected or signal_keys_tuple)
    if signal_detected and signal_count <= 0:
        signal_count = len(signal_keys_tuple)
    return {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_alignment_step": COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
        "surface_recovery_relation_line_aligned": bool(aligned_sentence_ids),
        "surface_recovery_relation_line_sentence_ids": list(_dedupe(aligned_sentence_ids)),
        "surface_relation_marker_keys": list(marker_keys_tuple),
        "surface_relation_marker_key": marker_keys_tuple[0] if marker_keys_tuple else "",
        "reader_relation_signal_detected": signal_detected,
        "reader_relation_signal_count": signal_count,
        "reader_relation_signal_keys": list(signal_keys_tuple),
        "reader_relation_signal_relation_types": list(relation_types_tuple),
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }

def _surface_signature_row(*, line: CompleteSentencePlanLine, phrase_key: str, role_phrase_keys: Sequence[str], connector_key: str, particle: str, predicate_key: str, ending_key: str, distance_policy_key: str, variation_key: str, tone_policy_key: str = "", temperature_key: str = "", tone_guard_keys: Sequence[str] | None = None, closing_policy_key: str = "", read_feeling_policy_key: str = "", relation_surface_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    relation = _surface_relation(line.relation_type)
    relation_contract = _surface_relation_contract_keys(relation_surface_meta)
    observation_surface_meta = _observation_surface_signature_meta(line)
    marker_key = _clean_token(relation_contract.get("surface_relation_marker_key") or relation_contract.get("relation_marker_key"))
    signature_relation_suffix = f":{marker_key}" if marker_key else ""
    connector_family = _anti_template_connector_family_key(connector_key)
    predicate_family = _anti_template_predicate_family_key(predicate_key, ending_key)
    ending_family = _anti_template_ending_family_key(ending_key)
    opening_family = _anti_template_opening_family_key(line.line_role, predicate_key, phrase_key)
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
        "connector_family_key": connector_family,
        "particle_key": particle,
        "predicate_key": predicate_key,
        "predicate_family_key": predicate_family,
        "ending_key": ending_key,
        "ending_family_key": ending_family,
        "opening_family_key": opening_family,
        "distance_policy_key": distance_policy_key,
        "tone_policy_key": _clean_token(tone_policy_key) or distance_policy_key,
        "temperature_key": _clean_token(temperature_key),
        "tone_guard_keys": list(_dedupe(tone_guard_keys)),
        "closing_policy_key": _clean_token(closing_policy_key),
        "read_feeling_policy_key": _clean_token(read_feeling_policy_key),
        **relation_contract,
        **observation_surface_meta,
        "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
        "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
        "step9_tone_engine_2_1_ready": True,
        "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
        "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "variation_key": variation_key,
        "signature": f"{line.line_role}:{relation}:{phrase_key}:{connector_key}:{particle}:{predicate_key}:{ending_key}:{distance_policy_key}:{_clean_token(tone_policy_key) or distance_policy_key}{signature_relation_suffix}",
        "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template_applied": True,
        "generic_center_opening": opening_family == "generic_center_opening",
        "surface_signature_for_template_guard": True,
        "completion_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "raw_input_included": False,
    }

def _value_counts(values: Iterable[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for raw in values:
        key = _clean(raw)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def _repeated_keys(values: Iterable[Any], *, min_count: int = 2, ignore: Iterable[str] | None = None) -> Tuple[str, ...]:
    ignore_set = set(ignore or ())
    counts = _value_counts(values)
    return tuple(key for key, count in counts.items() if count >= min_count and key not in ignore_set)


def _surface_variation_report_from_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    row_list = [dict(row) for row in rows if isinstance(row, Mapping)]
    connector_keys = [_clean(row.get("connector_key")) for row in row_list if _clean(row.get("connector_key"))]
    predicate_keys = [_clean(row.get("predicate_key")) for row in row_list if _clean(row.get("predicate_key"))]
    ending_keys = [_clean(row.get("ending_key")) for row in row_list if _clean(row.get("ending_key"))]
    signatures = [_clean(row.get("signature")) for row in row_list if _clean(row.get("signature"))]
    repeated_connector_keys = _repeated_keys(connector_keys, min_count=3, ignore={"none"})
    repeated_ending_keys = _repeated_keys(ending_keys, min_count=3)
    repeated_signature_keys = _repeated_keys(signatures, min_count=2)
    anti_template_report = build_surface_realizer_anti_template_report(row_list)

    template_flags = [
        "completion_sentence_template_used",
        "role_completed_sentence_template_used",
        "input_specific_template_used",
        "fixed_sentence_template_used",
    ]
    flagged_template_rows = [
        str(row.get("sentence_id") or index)
        for index, row in enumerate(row_list, start=1)
        if any(bool(row.get(flag)) for flag in template_flags)
    ]
    raw_rows = [
        str(row.get("sentence_id") or index)
        for index, row in enumerate(row_list, start=1)
        if bool(row.get("raw_input_included") or row.get("raw_text_included"))
    ]

    blocker_reasons: list[str] = []
    if repeated_ending_keys:
        blocker_reasons.append("same_ending_major")
    if repeated_signature_keys:
        blocker_reasons.append("surface_signature_repeat")
    if repeated_connector_keys:
        blocker_reasons.append("surface_connector_repetition")
    if flagged_template_rows:
        blocker_reasons.append("surface_signature_template_flag")
    if raw_rows:
        blocker_reasons.append("surface_signature_raw_input_included")
    for reason in list(anti_template_report.get("anti_template_major_reasons") or []):
        marker = str(reason)
        if marker not in blocker_reasons:
            blocker_reasons.append(marker)

    anti_template_major_reasons = list(anti_template_report.get("anti_template_major_reasons") or [])
    return {
        "version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION,
        "surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
        "surface_variation_step": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
        "surface_signature_version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "surface_signature_count": len(signatures),
        "surface_signature_repeat_count": len(repeated_signature_keys),
        "repeated_surface_signature_keys": list(repeated_signature_keys),
        "connector_keys": connector_keys,
        "unique_connector_key_count": len(set(connector_keys)),
        "repeated_connector_keys": list(repeated_connector_keys),
        "connector_repetition_major_count": len(repeated_connector_keys),
        "connector_family_keys": list(anti_template_report.get("connector_family_keys") or []),
        "predicate_keys": predicate_keys,
        "unique_predicate_key_count": len(set(predicate_keys)),
        "predicate_family_keys": list(anti_template_report.get("predicate_family_keys") or []),
        "ending_keys": ending_keys,
        "unique_ending_key_count": len(set(ending_keys)),
        "ending_family_keys": list(anti_template_report.get("ending_family_keys") or []),
        "opening_family_keys": list(anti_template_report.get("opening_family_keys") or []),
        "same_ending_major_count": len(repeated_ending_keys),
        "repeated_ending_keys": list(repeated_ending_keys),
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION,
        "anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_2_1_anti_template_applied": True,
        "surface_anti_template_report": anti_template_report,
        "surface_realizer_anti_template_report": anti_template_report,
        "surface_anti_template_guard_passed": not bool(anti_template_report.get("anti_template_major_detected")),
        "generic_center_opening_count": int(anti_template_report.get("generic_center_opening_count") or 0),
        "same_connector_family_run_max": int(anti_template_report.get("same_connector_family_run_max") or 0),
        "same_connector_key_run_max": int(anti_template_report.get("same_connector_key_run_max") or 0),
        "same_predicate_family_count": int(anti_template_report.get("same_predicate_family_count") or 0),
        "same_ending_family_count": int(anti_template_report.get("same_ending_family_count") or 0),
        "anti_template_major_count": len(anti_template_major_reasons),
        "anti_template_major_reasons": anti_template_major_reasons,
        "completion_sentence_template_used": bool(flagged_template_rows),
        "flagged_template_sentence_ids": flagged_template_rows,
        "raw_input_included": bool(raw_rows),
        "raw_input_sentence_ids": raw_rows,
        "release_blocker": bool(blocker_reasons),
        "blocker_reasons": blocker_reasons,
        "passed": not blocker_reasons,
    }

def _forbidden_surface_hits(text: str) -> Tuple[str, ...]:
    hits: list[str] = []
    for key, pattern in FORBIDDEN_SURFACE_PATTERNS:
        if pattern.search(text or "") and key not in hits:
            hits.append(key)
    return tuple(hits)


def _repeat_instance_count(values: Sequence[str], *, min_count: int = 2, ignore: Sequence[str] = ("", "none")) -> int:
    return sum(max(0, values.count(key) - 1) for key in _repeated_keys(values, min_count=min_count, ignore=ignore))


def _consecutive_repeat_count(values: Sequence[str], *, ignore: Sequence[str] = ("", "none")) -> int:
    ignored = set(ignore)
    count = 0
    previous = ""
    for value in values:
        if value and value not in ignored and value == previous:
            count += 1
        previous = value
    return count


def _realize_line(
    line: CompleteSentencePlanLine,
    *,
    sequence_index: int,
    used_predicate_keys: Sequence[str],
    used_ending_keys: Sequence[str],
    used_connector_keys: Sequence[str] | None = None,
    tone_policy: CompleteTonePolicy | Mapping[str, Any] | None = None,
) -> "CompleteSurfaceLineV2":
    relation = _surface_relation(line.relation_type)
    tone_constraint = _tone_constraint_for_line(tone_policy, line, relation)
    phrase, phrase_key, role_phrase_keys = _phrase_for_line(line)
    connector, connector_key = _connector_for(line.line_role, relation, sequence_index, used_connector_keys=used_connector_keys)
    particle, predicate, predicate_key, ending_key = _choose_predicate(
        relation_type=relation,
        line_role=line.line_role,
        used_predicate_keys=used_predicate_keys,
        used_ending_keys=used_ending_keys,
    )
    if line.line_role == "relation" and connector_key == "relation_approach_avoidance":
        body = f"{connector}{phrase}{particle}{predicate}"
    else:
        body = f"{connector}{phrase}{particle}{predicate}"
    max_chars = int(line.max_chars or 120)
    text = _truncate_sentence(body, max_chars)
    text, relation_surface_meta = _relation_surface_alignment_for_line(line, relation=relation, text=text)
    if relation_surface_meta.get("surface_recovery_relation_line_aligned"):
        marker_key = _clean_token(relation_surface_meta.get("surface_relation_marker_key") or relation_surface_meta.get("relation_marker_key"))
        if marker_key == "recovery_load_bridge_v1":
            connector_key = "relation_recovery_contract_load_bridge"
            predicate_key = "recovery_load_bridge_contract"
            phrase_key = "recovery_load_bridge"
            role_phrase_keys = _dedupe(tuple(role_phrase_keys) + ("recovery_load_bridge",))
        elif marker_key == "recovery_connected_flow_v1":
            connector_key = "relation_recovery_contract_connected_flow"
            predicate_key = "recovery_connected_flow_contract"
            phrase_key = "recovery_connected_flow"
            role_phrase_keys = _dedupe(tuple(role_phrase_keys) + ("recovery_connected_flow",))
        particle = "が"
        ending_key = "tsunagaru"
    distance_policy_key = _clean_token(tone_constraint.get("distance_policy_key")) or DISTANCE_POLICY_KEYS.get(line.line_role, "observe_without_overclaim")
    tone_policy_key = distance_policy_key
    temperature_key = _clean_token(tone_constraint.get("temperature_key"))
    closing_policy_key = _clean_token(tone_constraint.get("closing_policy_key"))
    read_feeling_policy_key = _clean_token(tone_constraint.get("read_feeling_policy_key"))
    tone_guard_keys = _tone_guard_keys(tone_constraint)
    variation_key = f"v{(sequence_index % 3) + 1}"
    observation_surface_meta = _observation_surface_signature_meta(line)
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
        tone_policy_key=tone_policy_key,
        temperature_key=temperature_key,
        tone_guard_keys=tone_guard_keys,
        closing_policy_key=closing_policy_key,
        read_feeling_policy_key=read_feeling_policy_key,
        relation_surface_meta=relation_surface_meta,
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
        tone_policy_key=tone_policy_key,
        temperature_key=temperature_key,
        tone_guard_keys=tone_guard_keys,
        closing_policy_key=closing_policy_key,
        read_feeling_policy_key=read_feeling_policy_key,
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
            **relation_surface_meta,
            **observation_surface_meta,
            "tone_constraint": tone_constraint,
            "tone_policy_key": tone_policy_key,
            "temperature_key": temperature_key,
            "tone_guard_keys": list(tone_guard_keys),
            "tone_meaning_added": False,
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
    tone_policy_key: str = "observe_without_overclaim"
    temperature_key: str = "steady_warm"
    tone_guard_keys: Iterable[str] = dataclass_field(default_factory=tuple)
    closing_policy_key: str = "none"
    read_feeling_policy_key: str = "input_specific_structure_reflected"
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
        object.__setattr__(self, "tone_policy_key", _clean_token(self.tone_policy_key) or _clean_token(self.distance_policy_key) or "observe_without_overclaim")
        object.__setattr__(self, "temperature_key", _clean_token(self.temperature_key) or "steady_warm")
        object.__setattr__(self, "tone_guard_keys", _dedupe(self.tone_guard_keys))
        object.__setattr__(self, "closing_policy_key", _clean_token(self.closing_policy_key) or "none")
        object.__setattr__(self, "read_feeling_policy_key", _clean_token(self.read_feeling_policy_key) or "input_specific_structure_reflected")
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
        source_line = dict(self.source_sentence_plan_line)
        def role_values(value: Any) -> list[Any]:
            if value is None:
                return []
            if isinstance(value, (list, tuple, set)):
                return list(value)
            return [value]
        phrase_roles = _dedupe(
            list(self.role_phrase_keys)
            + ([self.role_phrase_key] if self.role_phrase_key else [])
            + role_values(source_line.get("must_include_roles"))
            + role_values(source_line.get("phrase_unit_roles"))
        )
        relation_contract = _surface_relation_contract_keys(self.meta)
        if self.surface_signature:
            signature_contract = _surface_relation_contract_keys(self.surface_signature)
            if signature_contract.get("surface_recovery_relation_line_aligned"):
                relation_contract = signature_contract
        return {
            "version": self.schema_version,
            "sentence_id": self.sentence_id,
            "surface_text": self.surface_text,
            "line_role": self.line_role,
            "relation_type": self.relation_type,
            "used_evidence_span_ids": list(self.evidence_span_ids),
            "used_phrase_unit_ids": list(self.phrase_unit_ids),
            "role_phrase_key": self.role_phrase_key,
            "role_phrase_keys": list(self.role_phrase_keys),
            **_observation_surface_signature_meta(self.source_sentence_plan_line),
            "phrase_unit_roles": list(phrase_roles),
            "source_sentence_plan_line": source_line,
            "surface_signature": dict(self.surface_signature),
            "relation_surface_contract_version": relation_contract["relation_surface_contract_version"],
            "surface_recovery_relation_line_aligned": relation_contract["surface_recovery_relation_line_aligned"],
            "surface_recovery_relation_alignment_step": relation_contract["surface_recovery_relation_alignment_step"],
            "surface_relation_marker_key": relation_contract["surface_relation_marker_key"],
            "relation_marker_key": relation_contract["relation_marker_key"],
            "reader_relation_signal_detected": relation_contract["reader_relation_signal_detected"],
            "reader_relation_signal_count": relation_contract["reader_relation_signal_count"],
            "reader_relation_signal_keys": relation_contract["reader_relation_signal_keys"],
            "tone_policy_key": self.tone_policy_key,
            "temperature_key": self.temperature_key,
            "tone_guard_keys": list(self.tone_guard_keys),
            "closing_policy_key": self.closing_policy_key,
            "read_feeling_policy_key": self.read_feeling_policy_key,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "step9_tone_engine_2_1_ready": True,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": "Step8_Binding_aware_Grounding",
            "product_quality_grounding_ready": True,
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
            **_observation_surface_signature_meta(self.source_sentence_plan_line),
            "subject_policy_key": self.subject_policy_key,
            "connector_key": self.connector_key,
            "particle_key": self.particle_key,
            "predicate_key": self.predicate_key,
            "ending_key": self.ending_key,
            "distance_policy_key": self.distance_policy_key,
            "tone_policy_key": self.tone_policy_key,
            "temperature_key": self.temperature_key,
            "tone_guard_keys": list(self.tone_guard_keys),
            "closing_policy_key": self.closing_policy_key,
            "read_feeling_policy_key": self.read_feeling_policy_key,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "step9_tone_engine_2_1_ready": True,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "tone_meaning_added": False,
            "variation_key": self.variation_key,
            "surface_signature": dict(self.surface_signature),
            "relation_surface_contract_version": self.surface_signature.get("relation_surface_contract_version") or self.meta.get("relation_surface_contract_version") or RELATION_SURFACE_CONTRACT_VERSION,
            "surface_recovery_relation_line_aligned": bool(self.surface_signature.get("surface_recovery_relation_line_aligned") or self.meta.get("surface_recovery_relation_line_aligned")),
            "surface_recovery_relation_alignment_step": self.surface_signature.get("surface_recovery_relation_alignment_step") or self.meta.get("surface_recovery_relation_alignment_step") or "",
            "surface_relation_marker_key": self.surface_signature.get("surface_relation_marker_key") or self.meta.get("surface_relation_marker_key") or self.meta.get("relation_marker_key") or "",
            "relation_marker_key": self.surface_signature.get("relation_marker_key") or self.meta.get("relation_marker_key") or "",
            "reader_relation_signal_detected": bool(self.surface_signature.get("reader_relation_signal_detected") or self.meta.get("reader_relation_signal_detected")),
            "reader_relation_signal_count": int(self.surface_signature.get("reader_relation_signal_count") or self.meta.get("reader_relation_signal_count") or 0),
            "reader_relation_signal_keys": list(self.surface_signature.get("reader_relation_signal_keys") or self.meta.get("reader_relation_signal_keys") or []),
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
                        tone_policy_key=item.get("tone_policy_key") or item.get("distance_policy_key") or "observe_without_overclaim",
                        temperature_key=item.get("temperature_key") or "steady_warm",
                        tone_guard_keys=item.get("tone_guard_keys") or (),
                        closing_policy_key=item.get("closing_policy_key") or "none",
                        read_feeling_policy_key=item.get("read_feeling_policy_key") or "input_specific_structure_reflected",
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
    def connector_keys(self) -> Tuple[str, ...]:
        return tuple(line.connector_key for line in self.surface_lines if line.connector_key)

    @property
    def predicate_keys(self) -> Tuple[str, ...]:
        return tuple(line.predicate_key for line in self.surface_lines if line.predicate_key)

    @property
    def surface_variation_report(self) -> dict[str, Any]:
        return _surface_variation_report_from_rows([dict(line.surface_signature) for line in self.surface_lines])

    @property
    def surface_anti_template_report(self) -> dict[str, Any]:
        report = self.surface_variation_report.get("surface_anti_template_report")
        if isinstance(report, Mapping):
            return dict(report)
        return build_surface_realizer_anti_template_report([dict(line.surface_signature) for line in self.surface_lines])

    @property
    def surface_anti_template_guard_passed(self) -> bool:
        return not bool(self.surface_anti_template_report.get("anti_template_major_detected"))

    @property
    def same_ending_repeat_count(self) -> int:
        counts = _value_counts(self.ending_keys)
        return sum(max(0, count - 1) for count in counts.values() if count >= 2)

    @property
    def same_ending_consecutive_count(self) -> int:
        endings = list(self.ending_keys)
        return sum(1 for index in range(1, len(endings)) if endings[index] == endings[index - 1])

    @property
    def surface_signature_repeat_count(self) -> int:
        return int(self.surface_variation_report.get("surface_signature_repeat_count") or 0)

    @property
    def surface_variation_profile(self) -> dict[str, Any]:
        report = dict(self.surface_variation_report)
        report.setdefault("version", COMPLETE_SURFACE_VARIATION_PROFILE_VERSION)
        report.setdefault("policy_version", COMPLETE_SURFACE_VARIATION_POLICY_VERSION)
        report.setdefault("source_step", COMPLETE_SURFACE_REALIZER_STAGE)
        report.setdefault("surface_variation_guard_passed", bool(report.get("passed", True)))
        report.setdefault("surface_realizer_anti_template_version", COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION)
        report.setdefault("anti_template_policy_version", COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION)
        report.setdefault("surface_anti_template_guard_passed", bool(report.get("surface_anti_template_guard_passed", True)))
        report.setdefault("same_ending_repeat_count", self.same_ending_repeat_count)
        report.setdefault("same_ending_consecutive_count", self.same_ending_consecutive_count)
        report.setdefault("surface_signature_repeat_count", self.surface_signature_repeat_count)
        report.setdefault("anti_template_policy", build_surface_realizer_anti_template_policy_meta())
        report.setdefault("surface_realizer_anti_template_report", build_surface_realizer_anti_template_report([dict(line.surface_signature) for line in self.surface_lines]))
        report.setdefault("surface_realizer_2_1_anti_template_applied", True)
        report.setdefault("completion_sentence_template_used", False)
        report.setdefault("role_completed_sentence_template_used", False)
        report.setdefault("input_specific_template_used", False)
        report.setdefault("raw_input_included", False)
        return report

    @property
    def tone_policy_meta(self) -> dict[str, Any]:
        item = self.meta.get("tone_policy") if isinstance(self.meta, Mapping) else None
        return dict(item) if isinstance(item, Mapping) else {}

    @property
    def tone_guard_report(self) -> dict[str, Any]:
        return build_complete_tone_guard_report(surface_realization=self, tone_policy=self.tone_policy_meta, comment_text=self.realized_text)

    @property
    def tone_guard_major_count(self) -> int:
        return int(self.tone_guard_report.get("tone_guard_major_count") or 0)

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
        variation_report = self.surface_variation_report
        for reason in list(variation_report.get("blocker_reasons") or []):
            errors.append(str(reason))
        tone_report = self.tone_guard_report
        for reason in list(tone_report.get("blocker_reasons") or []):
            errors.append(f"tone_guard:{reason}")
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
        relation_surface_report = _relation_surface_report_from_lines(self.surface_lines)
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
            "surface_variation_report": self.surface_variation_report,
            "surface_anti_template_report": self.surface_variation_report.get("surface_anti_template_report") or {},
            "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
            "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
            "surface_realizer_2_1_anti_template_applied": True,
            "surface_anti_template_guard_passed": bool(self.surface_variation_report.get("surface_anti_template_guard_passed", True)),
            "anti_template_major_count": int(self.surface_variation_report.get("anti_template_major_count") or 0),
            "anti_template_major_reasons": list(self.surface_variation_report.get("anti_template_major_reasons") or []),
            "connector_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("connector_family_keys") or []),
            "predicate_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("predicate_family_keys") or []),
            "ending_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("ending_family_keys") or []),
            "generic_center_opening_count": int((self.surface_variation_report.get("surface_anti_template_report") or {}).get("generic_center_opening_count") or 0),
            "relation_line_forced_for_all_inputs": False,
            "completed_sentence_templates_added_by_step7": False,
            "input_specific_runtime_branching_added_by_step7": False,
            "relation_surface_contract_version": relation_surface_report["relation_surface_contract_version"],
            "surface_recovery_relation_line_alignment_step": relation_surface_report["surface_recovery_relation_line_alignment_step"],
            "surface_recovery_relation_line_aligned": relation_surface_report["surface_recovery_relation_line_aligned"],
            "surface_recovery_relation_line_sentence_ids": relation_surface_report["surface_recovery_relation_line_sentence_ids"],
            "surface_relation_marker_keys": relation_surface_report["surface_relation_marker_keys"],
            "reader_relation_signal_detected": relation_surface_report["reader_relation_signal_detected"],
            "reader_relation_signal_count": relation_surface_report["reader_relation_signal_count"],
            "reader_relation_signal_keys": relation_surface_report["reader_relation_signal_keys"],
            "reader_relation_signal_relation_types": relation_surface_report["reader_relation_signal_relation_types"],
            "relation_surface_report": relation_surface_report,
            "tone_policy": self.tone_policy_meta,
            "tone_guard_report": self.tone_guard_report,
            "tone_engine_2_1_report": self.tone_guard_report.get("tone_engine_2_1_report") or self.tone_guard_report.get("step9_tone_engine_2_1_report") or {},
            "step9_tone_engine_2_1_report": self.tone_guard_report.get("step9_tone_engine_2_1_report") or self.tone_guard_report.get("tone_engine_2_1_report") or {},
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "step9_tone_engine_2_1_ready": True,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
            "raw_input_included": False,
        }

    def as_meta(self, *, include_realized_text: bool = True) -> dict[str, Any]:
        term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
        source_binding = build_complete_sentence_binding_bundle_meta(self.source_sentence_plan) if isinstance(self.source_sentence_plan, CompleteSentencePlanV2) else {}
        relation_surface_report = _relation_surface_report_from_lines(self.surface_lines)
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
            "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
            "product_quality_surface_variation_step": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
            "product_quality_surface_variation": True,
            "surface_variation_strengthened": True,
            "surface_variation_report": self.surface_variation_report,
            "surface_anti_template_report": self.surface_variation_report.get("surface_anti_template_report") or {},
            "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
            "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
            "surface_realizer_2_1_anti_template_applied": True,
            "surface_anti_template_guard_passed": bool(self.surface_variation_report.get("surface_anti_template_guard_passed", True)),
            "anti_template_major_count": int(self.surface_variation_report.get("anti_template_major_count") or 0),
            "anti_template_major_reasons": list(self.surface_variation_report.get("anti_template_major_reasons") or []),
            "connector_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("connector_family_keys") or []),
            "predicate_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("predicate_family_keys") or []),
            "ending_family_keys": list((self.surface_variation_report.get("surface_anti_template_report") or {}).get("ending_family_keys") or []),
            "generic_center_opening_count": int((self.surface_variation_report.get("surface_anti_template_report") or {}).get("generic_center_opening_count") or 0),
            "relation_line_forced_for_all_inputs": False,
            "completed_sentence_templates_added_by_step7": False,
            "input_specific_runtime_branching_added_by_step7": False,
            "relation_surface_contract_version": relation_surface_report["relation_surface_contract_version"],
            "surface_recovery_relation_line_alignment_step": relation_surface_report["surface_recovery_relation_line_alignment_step"],
            "surface_recovery_relation_line_aligned": relation_surface_report["surface_recovery_relation_line_aligned"],
            "surface_recovery_relation_line_sentence_ids": relation_surface_report["surface_recovery_relation_line_sentence_ids"],
            "surface_relation_marker_keys": relation_surface_report["surface_relation_marker_keys"],
            "reader_relation_signal_detected": relation_surface_report["reader_relation_signal_detected"],
            "reader_relation_signal_count": relation_surface_report["reader_relation_signal_count"],
            "reader_relation_signal_keys": relation_surface_report["reader_relation_signal_keys"],
            "reader_relation_signal_relation_types": relation_surface_report["reader_relation_signal_relation_types"],
            "relation_surface_report": relation_surface_report,
            "connector_keys": list(self.connector_keys),
            "unique_connector_key_count": len(set(self.connector_keys)),
            "repeated_connector_keys": list(self.surface_variation_report.get("repeated_connector_keys") or []),
            "predicate_keys": list(self.predicate_keys),
            "unique_predicate_key_count": len(set(self.predicate_keys)),
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
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
            "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_completion_requires_blind_qa": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "tone_engine_added": True,
            "tone_policy_added": True,
            "tone_policy_applied": True,
            "tone_policy": self.tone_policy_meta,
            "tone_guard_report": self.tone_guard_report,
            "tone_engine_2_1_report": self.tone_guard_report.get("tone_engine_2_1_report") or self.tone_guard_report.get("step9_tone_engine_2_1_report") or {},
            "step9_tone_engine_2_1_report": self.tone_guard_report.get("step9_tone_engine_2_1_report") or self.tone_guard_report.get("tone_engine_2_1_report") or {},
            "tone_engine_2_1_ready": bool(self.tone_guard_report.get("step9_tone_engine_2_1_ready") or self.tone_guard_report.get("tone_engine_2_1_ready")),
            "step9_tone_engine_2_1_ready": True,
            "tone_guard_major_count": self.tone_guard_major_count,
            "tone_guard_passed": self.tone_guard_major_count == 0,
            "over_empathy_guard_passed": bool(self.tone_guard_report.get("over_empathy_guard_passed", True)),
            "diagnostic_tone_guard_passed": bool(self.tone_guard_report.get("diagnostic_tone_guard_passed", True)),
            "advice_like_guard_passed": bool(self.tone_guard_report.get("advice_like_guard_passed", True)),
            "generic_comfort_guard_passed": bool(self.tone_guard_report.get("generic_comfort_guard_passed", True)),
            "temperature_policy_applied": True,
            "closing_policy_applied": True,
            "read_feeling_policy_applied": True,
            "tone_is_surface_constraint_not_post_decoration": True,
            "meaning_added_by_tone_policy": False,
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
            "surface_signature_repeat_detected": self.surface_signature_repeat_count > 0,
            "surface_variation_major_detected": not self.surface_variation_profile["surface_variation_guard_passed"],
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
        "surface_realizer_2_1_anti_template_added": True,
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
        "surface_realizer_added": True,
        "product_quality_surface_variation_added": True,
        "surface_realizer_2_1_anti_template_added": True,
        "surface_realizer_2_1_anti_template_enabled": True,
        "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP,
        "surface_realizer_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
        "surface_realizer_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "generic_center_opening_policy_enabled": True,
        "same_connector_consecutive_guard_enabled": True,
        "predicate_family_stack_guard_enabled": True,
        "ending_family_stack_guard_enabled": True,
        "relation_line_not_forced_for_all_inputs": True,
        "anti_template_completion_sentence_bank_added": False,
        "input_specific_surface_branch_added": False,
        "surface_realizer_2_1_anti_template_relaxes_gate": False,
        "surface_variation_policy_version": COMPLETE_SURFACE_VARIATION_POLICY_VERSION,
        "surface_variation_profile_version": COMPLETE_SURFACE_VARIATION_PROFILE_VERSION,
        "surface_realizer_2_0_version": COMPLETE_SURFACE_REALIZER_2_0_VERSION,
        "surface_realizer_2_1_anti_template_added": True,
        "surface_realizer_2_1_anti_template_enabled": True,
        "surface_realizer_2_1_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_2_1_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
        "generic_center_opening_policy_enabled": True,
        "connector_family_run_suppression_enabled": True,
        "predicate_family_distribution_enabled": True,
        "ending_family_distribution_enabled": True,
        "relation_line_forced_for_all_inputs": False,
        "completion_sentence_templates_added_by_step7": False,
        "input_specific_runtime_branching_added_by_step7": False,
        "accepts_sentence_plan_2_0": True,
        "accepts_complete_sentence_plan_v2": True,
        "sentence_plan_must_be_followed": True,
        "surface_realizer_must_follow_plan": True,
        "observation_surface_realizer_version": OBSERVATION_SURFACE_REALIZER_VERSION,
        "observation_surface_realizer_step": OBSERVATION_SURFACE_REALIZER_STEP,
        "surface_realizer_observation_roles_supported": True,
        "eligible_observation_roles_supported": True,
        "low_information_observation_roles_supported": True,
        "unknown_slot_question_ending_policy_enabled": True,
        "eligible_state_verbalization_relation_required": True,
        "template_skeleton_guard_enabled": True,
        "observation_surface_realizer_contract": build_observation_surface_realizer_contract_meta(include_nested_contract=False),
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
        "tone_engine_added": True,
        "tone_policy_added": True,
        "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
        "tone_engine_2_1_version": COMPLETE_TONE_ENGINE_2_1_VERSION,
        "tone_engine_2_1_policy_version": COMPLETE_TONE_POLICY_2_1_VERSION,
        "step9_tone_engine_2_1_ready": True,
        "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
        "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
        "tone_policy_contract": build_complete_tone_policy_contract_meta(),
        "temperature_policy_added": True,
        "closing_policy_added": True,
        "read_feeling_policy_added": True,
        "over_empathy_guard_added": True,
        "diagnostic_tone_guard_added": True,
        "advice_like_guard_added": True,
        "generic_comfort_guard_added": True,
        "tone_is_surface_constraint_not_post_decoration": True,
        "meaning_added_by_tone_policy": False,
        "variation_policy_added": True,
        "variation_policy_enabled": True,
        "surface_signature_added": True,
        "surface_signature_recorded": True,
        "surface_signature_enabled": True,
        "surface_signature_to_template_guard": True,
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_alignment_step": COMPLETE_SURFACE_RECOVERY_RELATION_LINE_ALIGNMENT_STEP,
        "surface_recovery_relation_line_alignment_added": True,
        "surface_recovery_relation_line_uses_contract": True,
        "surface_recovery_relation_line_fixed_fallback": False,
        "surface_recovery_relation_line_completion_template": False,
        "product_quality_surface_variation_version": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION,
        "product_quality_surface_variation_step": COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP,
        "product_quality_surface_variation": True,
        "surface_variation_strengthened": True,
        "surface_realizer_2_1_anti_template": True,
        "surface_realizer_2_1_anti_template_changes_public_contract": False,
        "surface_realizer_2_1_anti_template_adds_completed_sentence_templates": False,
        "surface_realizer_2_1_anti_template_uses_fixture_strings": False,
        "same_ending_guard_enabled": True,
        "raw_echo_guard_material_exposed": True,
        "surface_signature_repeat_guard_enabled": True,
        "surface_text_internal_only": True,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "comment_text_contract": "passed_only",
        "surface_realizer_anti_template_relaxes_gate": False,
        "surface_realizer_anti_template_changes_public_contract": False,
        "surface_realizer_anti_template_adds_fixed_sentence_templates": False,
        "surface_realizer_anti_template_uses_input_specific_branching": False,
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
    tone_policy: CompleteTonePolicy | Mapping[str, Any] | None = None,
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
    tone_policy_obj = coerce_complete_tone_policy(tone_policy, sentence_plan=source_plan, coverage_group=source_plan.coverage_group)
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
                "tone_policy": tone_policy_obj.as_meta(),
                "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            },
        )
    used_predicate_keys: list[str] = []
    used_ending_keys: list[str] = []
    used_connector_keys: list[str] = []
    surface_lines: list[CompleteSurfaceLineV2] = []
    for index, line in enumerate(source_plan.sentence_plans):
        surface_line = _realize_line(
            line,
            sequence_index=index,
            used_predicate_keys=used_predicate_keys,
            used_ending_keys=used_ending_keys,
            used_connector_keys=used_connector_keys,
            tone_policy=tone_policy_obj,
        )
        surface_lines.append(surface_line)
        used_predicate_keys.append(surface_line.predicate_key)
        used_ending_keys.append(surface_line.ending_key)
        used_connector_keys.append(surface_line.connector_key)
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
            "tone_policy": tone_policy_obj.as_meta(),
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
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
        relation_surface_report = _relation_surface_report_from_lines(realization.surface_lines)
        return {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "signature_count": len(signatures),
            "surface_signatures": signatures,
            "surface_signature_rows": rows,
            "ending_keys": ending_keys,
            "surface_variation_profile": dict(realization.surface_variation_profile),
            "surface_realizer_anti_template_report": dict(realization.surface_variation_profile.get("surface_realizer_anti_template_report") or {}),
            "surface_realizer_anti_template_policy": build_surface_realizer_anti_template_policy_meta(),
            "surface_realizer_2_1_anti_template_applied": True,
            "relation_surface_contract_version": relation_surface_report["relation_surface_contract_version"],
            "surface_recovery_relation_line_aligned": relation_surface_report["surface_recovery_relation_line_aligned"],
            "surface_relation_marker_keys": relation_surface_report["surface_relation_marker_keys"],
            "reader_relation_signal_detected": relation_surface_report["reader_relation_signal_detected"],
            "reader_relation_signal_keys": relation_surface_report["reader_relation_signal_keys"],
            "relation_surface_report": relation_surface_report,
            "tone_engine_version": COMPLETE_TONE_ENGINE_VERSION,
            "tone_policy_version": COMPLETE_TONE_POLICY_VERSION,
            "product_quality_tone_engine_version": COMPLETE_PRODUCT_QUALITY_TONE_ENGINE_VERSION,
            "tone_policy_applied": True,
            "tone_guard_report": realization.tone_guard_report,
            "tone_guard_major_count": realization.tone_guard_major_count,
            "tone_guard_passed": realization.tone_guard_major_count == 0,
            "same_ending_repeat_count": realization.same_ending_repeat_count,
            "same_ending_consecutive_count": realization.same_ending_consecutive_count,
            "same_ending_major_count": realization.same_ending_major_count,
            "surface_signature_repeat_count": realization.surface_signature_repeat_count,
            "same_ending_guard_passed": realization.same_ending_major_count == 0,
            "surface_variation_guard_passed": realization.surface_variation_profile["surface_variation_guard_passed"],
            "surface_anti_template_guard_passed": realization.surface_anti_template_guard_passed,
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
            "surface_variation_profile": _json_safe_value(realization.get("surface_variation_profile") or {}),
            "surface_anti_template_report": _json_safe_value(realization.get("surface_anti_template_report") or {}),
            "surface_anti_template_guard_passed": bool(realization.get("surface_anti_template_guard_passed", True)),
            "relation_surface_contract_version": realization.get("relation_surface_contract_version") or RELATION_SURFACE_CONTRACT_VERSION,
            "surface_recovery_relation_line_aligned": bool(realization.get("surface_recovery_relation_line_aligned")),
            "same_ending_major_count": int(realization.get("same_ending_major_count") or 0),
            "surface_signature_repeat_count": int(realization.get("surface_signature_repeat_count") or 0),
            "surface_variation_guard_passed": bool(realization.get("surface_variation_guard_passed", True)),
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


def build_complete_product_quality_surface_variation_report(
    realization: CompleteSurfaceRealizationV2 | Mapping[str, Any] | None = None,
    *,
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    sentence_plan_seed: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Return the Step3 product-quality surface variation report.

    The report is text-independent where possible. It verifies that Surface
    Realizer produced sentence-plan-bound grammar parts, non-repeated endings,
    connector variation, and surface signatures for Template/Echo Guard.  It
    never writes public ``comment_text`` and never introduces fallback text.
    """

    if isinstance(realization, CompleteSurfaceRealizationV2):
        target = realization
    elif isinstance(realization, Mapping):
        rows = realization.get("surface_signature_rows") or realization.get("surface_lines") or ()
        return _surface_variation_report_from_rows([row for row in rows if isinstance(row, Mapping)])
    else:
        target = build_complete_surface_realization_v2(
            sentence_plan=sentence_plan,
            sentence_plan_seed=sentence_plan_seed,
            **kwargs,
        )
    report = dict(target.surface_variation_report)
    report.update(
        {
            "status": target.status,
            "ready": target.ready,
            "plan_id": target.plan_id,
            "coverage_group": target.coverage_group,
            "surface_line_count": len(target.surface_lines),
            "used_evidence_span_ids": list(target.used_evidence_span_ids),
            "used_phrase_unit_ids": list(target.used_phrase_unit_ids),
            "relation_types": list(target.relation_types),
            "surface_signatures": list(target.surface_signatures),
            "completion_sentence_template_used": bool(report.get("completion_sentence_template_used", False)),
            "fixed_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "raw_input_included": bool(report.get("raw_input_included", False)),
            "comment_text_key_written": False,
            "public_comment_text_assigned": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
        }
    )
    return report


# Compatibility aliases for concise import names in future Step 8/9 work.
CompleteSurfaceLine = CompleteSurfaceLineV2
CompleteSurfaceRealization = CompleteSurfaceRealizationV2
CompleteSurfaceRealizerResult = CompleteSurfaceRealizationV2

__all__ = [
    "build_complete_product_quality_surface_variation_report",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_VERSION",
    "COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_VERSION",
    "COMPLETE_SURFACE_REALIZER_2_1_ANTI_TEMPLATE_STEP",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_STEP",
    "COMPLETE_PRODUCT_QUALITY_SURFACE_VARIATION_SCHEMA_VERSION",
    "COMPLETE_SURFACE_LINE_SCHEMA_VERSION",
    "COMPLETE_SURFACE_REALIZER_SCHEMA_VERSION",
    "COMPLETE_SURFACE_REALIZER_SERVICE_VERSION",
    "COMPLETE_SURFACE_REALIZER_STAGE",
    "COMPLETE_SURFACE_REALIZER_STEP",
    "COMPLETE_SURFACE_REALIZER_TARGET_STEP",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION",
    "COMPLETE_SURFACE_REALIZER_VERSION",
    "COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION",
    "COMPLETE_SURFACE_VARIATION_POLICY_VERSION",
    "COMPLETE_SURFACE_VARIATION_PROFILE_VERSION",
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
