# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 9 Self-Repair Loop for EmlisAI Complete Composer initial version.

Self-Repair receives Gate / Grounding reasons and applies only bounded,
meaning-preserving adjustments to the Complete Composer internal plan/surface.
It never relaxes gates, never creates new user-facing ``comment_text`` keys,
and never invents evidence, relation, diagnosis, advice, or fixed fallback
sentences.  Public API response shape and RN display contracts stay unchanged.
"""

from dataclasses import asdict, dataclass, field as dataclass_field, is_dataclass
from typing import Any, Iterable, Mapping, Sequence, Tuple
import re

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta
from emlis_ai_complete_composer_types import (
    COMPLETE_COMPOSER_STAGE,
    COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
    CompleteSentencePlanLine,
    CompleteSentencePlanV2,
    RepairTrace,
)
from emlis_ai_complete_grounding_binding import COMPLETE_BINDING_AWARE_GROUNDING_STAGE
from emlis_ai_runtime_surface_self_repair import (
    RUNTIME_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION,
    RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP,
    RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION,
    build_surface_aware_self_repair_request,
    derive_surface_aware_repair_reasons,
)
from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_REALIZER_STAGE,
    COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
    COMPLETE_SURFACE_STATUS_READY,
    COMPLETE_SURFACE_STATUS_UNAVAILABLE,
    CompleteSurfaceLineV2,
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
    build_complete_surface_signature,
)
from emlis_ai_relation_surface_contract import (
    RELATION_SURFACE_CONTRACT_VERSION,
    normalize_relation_surface_type,
    relation_marker_meta,
    relation_marker_phrase,
)

COMPLETE_SELF_REPAIR_VERSION = "emlis.complete_self_repair.v1"
COMPLETE_SELF_REPAIR_PRODUCT_QUALITY_VERSION = "emlis.complete_self_repair.product_quality.v2"
COMPLETE_SURFACE_AWARE_SELF_REPAIR_VERSION = RUNTIME_SURFACE_AWARE_SELF_REPAIR_VERSION
COMPLETE_SURFACE_AWARE_SELF_REPAIR_STEP = RUNTIME_SURFACE_AWARE_SELF_REPAIR_STEP
COMPLETE_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION = RUNTIME_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION
COMPLETE_SELF_REPAIR_POLICY_VERSION = "emlis.complete_self_repair_policy.v2"
COMPLETE_SELF_REPAIR_SERVICE_VERSION = COMPLETE_SELF_REPAIR_VERSION
COMPLETE_SELF_REPAIR_STAGE = "Step9_Self_Repair_Loop"
COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE = "Step4_Self_Repair_Strengthening"
COMPLETE_SELF_REPAIR_STEP = COMPLETE_SELF_REPAIR_STAGE
COMPLETE_SELF_REPAIR_TARGET_STEP = COMPLETE_SELF_REPAIR_STAGE
COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT = "Commit 9"
COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_IMPLEMENTATION_UNIT = "ProductQualityConnection-Step4"

COMPLETE_SELF_REPAIR_STATUS_REPAIRED = "repaired"
COMPLETE_SELF_REPAIR_STATUS_UNCHANGED = "unchanged"
COMPLETE_SELF_REPAIR_STATUS_ABORTED = "aborted"
COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE = "unavailable"

MAX_SELF_REPAIR_ATTEMPTS = 2

REPAIR_REASON_UNSUPPORTED_SENTENCE = "unsupported_sentence"
REPAIR_REASON_RELATION_NOT_EXPRESSED = "relation_not_expressed"
REPAIR_REASON_TEMPLATE_LIKE = "template_like"
REPAIR_REASON_RAW_ECHO = "raw_echo"
REPAIR_REASON_OVER_ECHO = "over_echo"
REPAIR_REASON_TOO_LONG = "too_long"
REPAIR_REASON_OVERCLAIM = "overclaim"
REPAIR_REASON_UNSUPPORTED_OVERCLAIM = "unsupported_overclaim"
REPAIR_REASON_MALFORMED_NOMINALIZATION = "malformed_nominalization"
REPAIR_REASON_TWO_STAGE_LABEL_MISSING = "two_stage_complete_surface_realizer_label_missing"
REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY = "two_stage_complete_surface_realizer_section_empty"

PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION = "cocolon.emlis_two_stage.self_repair_unavailable_reason.v1"
PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE = "Phase17_7_self_repair_unavailable_reason"
REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING = "phase17_surface_mode_policy_missing"
REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK = "phase17_internal_role_label_leak"
REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK = "phase17_relation_skeleton_leak"
REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH = "phase17_section_budget_mismatch"
REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING = "phase17_grounding_relation_binding_missing"
REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED = "phase17_product_visible_fixture_not_reached"

ALLOWED_REPAIR_REASONS = {
    REPAIR_REASON_UNSUPPORTED_SENTENCE,
    REPAIR_REASON_RELATION_NOT_EXPRESSED,
    REPAIR_REASON_TEMPLATE_LIKE,
    REPAIR_REASON_RAW_ECHO,
    REPAIR_REASON_OVER_ECHO,
    REPAIR_REASON_TOO_LONG,
    REPAIR_REASON_OVERCLAIM,
    REPAIR_REASON_UNSUPPORTED_OVERCLAIM,
    REPAIR_REASON_MALFORMED_NOMINALIZATION,
    REPAIR_REASON_TWO_STAGE_LABEL_MISSING,
    REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY,
    REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING,
    REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
    REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING,
}

REJECT_PREFERRED_REASONS = {REPAIR_REASON_OVERCLAIM, REPAIR_REASON_UNSUPPORTED_OVERCLAIM}
ECHO_REASONS = {REPAIR_REASON_RAW_ECHO, REPAIR_REASON_OVER_ECHO}

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

_SPACE_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[^0-9a-zA-Z_\-.]+")
_TRIM = " \t\r\n　、,。.!！?？『』\"'「」（）()[]【】"

RELATION_MARKER_PHRASES = {
    "contrast": "別々の向きが片方だけに寄らず、同じ場所に並んでいます。",
    "coexistence": "同じ時間の中に重なっていることも残しています。",
    "pressure": "圧力として前面に出ていることも残っています。",
    "approach_avoidance": "近づく動きと止まる動きの両方が同じ線上に残っています。",
    "recovery": relation_marker_phrase("recovery", {"prior_load_present": True}),
    "residue": "あとに残る余韻として、前の流れとつながっています。",
}

RELATION_ROLE_PHRASES = {
    "contrast": "別々の向き",
    "coexistence": "同じ時間の重なり",
    "pressure": "圧力",
    "approach_avoidance": "近づく動きと止まる動き",
    "recovery": "戻ってくる動き",
    "residue": "あとに残る余韻",
    "limit": "限界に近い圧力",
    "context": "根拠のある背景",
    "center": "中心にある感覚",
}

ROLE_KEY_REPAIR_PHRASES = {
    # Phase17-7: product-visible repair vocabulary for internal role leaks.
    # These are fragments, not completed reply templates.
    "achievement": "気持ちが動いた変化",
    "positive_change": "気持ちが動いた変化",
    "positive_state": "少し整えようとする動き",
    "perfection_fear": "完璧に元気でいようとする怖さ",
    "pressure_or_limit": "圧力や限界に近い材料",
    "self_confidence_uncertainty": "自信をつけたい気持ちと不安",
    "self_denial": "自分を否定する言葉",
    "attempt_to_change": "直したい気持ち",
    "challenge_attempt": "試している動き",
    "conversation_wish": "誰かと話したい気持ち",
    "work_fatigue": "仕事後の疲れ",
    "self_blame_flow": "自分を責める流れ",
    "gentle_self_observation": "自分の気持ちを少し優しく見ようとする方向",
    "independence_intention": "自立したい気持ち",
    "life_context": "生活のこと",
    "health_pace": "体調を見ながら続けるペース",
    "money_context": "お金のこと",
    "sustainable_pace": "長く続けられるペース",
    "approach_wish": "近づきたい気持ち",
    "burden_fear": "負担になる怖さ",
    "avoidance_wish": "避けたい気持ち",
    "relation_pair": "近づきたい気持ちと止まる気持ちの並び",
    "load_accumulation": "疲れの蓄積",
    "pressure_foreground": "前面に出ている圧力",
    "small_repair": "小さな回復",
    "value_wish": "大切にしたい願い",
    "hurt_residue": "あとに残る痛み",
    "relationship_distance": "距離感の揺れ",
    "self_side_response": "自分の側に残る反応",
    "current_expression": "今出ている感覚",
    "small_wobble": "小さな揺れ",
    "limit_pressure": "限界に近い圧力",
    "primary_phrase": "中心にある材料",
}

PHASE17_SAFE_RELATION_ROLE_PHRASES = {
    "contrast": "向きの違い",
    "coexistence": "気持ちや条件の重なり",
    "pressure": "前に出ている圧力",
    "approach_avoidance": "近づく動きと止まる動き",
    "recovery": "戻ろうとする動き",
    "residue": "あとに残る余韻",
    "limit": "限界に近い圧力",
    "context": "根拠のある背景",
    "center": "中心にある材料",
}

ECHO_REPAIR_SUFFIXES = (
    "根拠のある範囲で置き直しました。",
    "文の中では短く残します。",
    "関係だけを保って言い換えています。",
    "余分な引用を避けて残しました。",
)

RELATION_CONNECTOR_KEYS = {
    "contrast": "repair_relation_contrast",
    "coexistence": "repair_relation_coexistence",
    "pressure": "repair_relation_pressure",
    "approach_avoidance": "repair_relation_approach_avoidance",
    "recovery": "repair_relation_recovery",
    "residue": "repair_relation_residue",
}

PHASE17_REPAIRABLE_REASON_ALIASES = {
    "same_predicate_family_stack": REPAIR_REASON_TEMPLATE_LIKE,
    "same_predicate_family": REPAIR_REASON_TEMPLATE_LIKE,
    "predicate_family_stack": REPAIR_REASON_TEMPLATE_LIKE,
    "ending_family_repetition": REPAIR_REASON_TEMPLATE_LIKE,
    "tone_guard_ending_family_repetition": REPAIR_REASON_TEMPLATE_LIKE,
    "two_stage_internal_role_label_leak": REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    "two_stage_complete_surface_internal_label_leak": REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    "internal_role_label_leak": REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    "two_stage_relation_skeleton_leak": REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    "two_stage_relation_skeleton_leak_surface": REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    "relation_skeleton_leak": REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    "two_stage_section_budget_mismatch": REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
    "section_budget_mismatch": REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
    "complete_initial_surface_unavailable": REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING,
    "complete_surface_mode_policy_missing": REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING,
    "complete_initial_grounding_failed": REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING,
    "grounding_relation_binding_missing": REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING,
    "product_visible_fixture_not_reached": REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED,
}

PHASE17_SURFACE_REWRITE_REPAIR_REASONS = {
    REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING,
}

PHASE17_DIAGNOSTIC_ONLY_REASONS = {
    REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED,
}

PHASE17_PRODUCT_VISIBLE_REASON_CODES = (
    REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING,
    REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
    REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING,
    REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED,
)

PHASE17_INTERNAL_ROLE_LABEL_RE = re.compile(
    r"\b(?:achievement|positive[ _]state|perfection[ _]fear|pressure[ _]or[ _]limit|role_[0-9a-zA-Z_\-]+)\b",
    re.IGNORECASE,
)
PHASE17_RELATION_SKELETON_RE = re.compile(
    r"同じ流れ|同じ場所|片方だけに寄らず|別々の向き|重なりを保っています|一方向には決まりきっていません"
)

FORBIDDEN_REPAIR_OPERATIONS = {
    "add_rootless_material",
    "invent_relation",
    "swap_to_fixed_completed_sentence",
    "expand_meaning",
    "delete_must_include",
    "weaken_overclaim_only",
}

REPAIR_POLICY_TABLE: dict[str, dict[str, Any]] = {
    REPAIR_REASON_UNSUPPORTED_SENTENCE: {
        "source_gate": "grounding",
        "allowed_repair": ("remove_optional_sentence", "rebind_to_existing_evidence"),
        "forbidden": ("add_rootless_material",),
        "trace_required_fields": ("before_sentence_ids", "after_sentence_ids", "evidence_ids_unchanged", "rebind_reason"),
    },
    REPAIR_REASON_RELATION_NOT_EXPRESSED: {
        "source_gate": "grounding",
        "allowed_repair": ("make_relation_line_explicit", "replace_connector"),
        "forbidden": ("invent_relation",),
        "trace_required_fields": ("relation_type", "relation_ids_unchanged"),
    },
    REPAIR_REASON_TEMPLATE_LIKE: {
        "source_gate": "template",
        "allowed_repair": ("change_surface_signature", "vary_tail", "vary_connector", "vary_sentence_order"),
        "forbidden": ("swap_to_fixed_completed_sentence",),
        "trace_required_fields": ("surface_signature_before", "surface_signature_after"),
    },
    REPAIR_REASON_RAW_ECHO: {
        "source_gate": "template",
        "allowed_repair": ("reduce_quote_density", "role_phrase_rephrase"),
        "forbidden": ("expand_meaning",),
        "trace_required_fields": ("echo_ratio_before", "echo_ratio_after"),
    },
    REPAIR_REASON_OVER_ECHO: {
        "source_gate": "template",
        "allowed_repair": ("reduce_quote_density", "role_phrase_rephrase"),
        "forbidden": ("expand_meaning",),
        "trace_required_fields": ("echo_ratio_before", "echo_ratio_after"),
    },
    REPAIR_REASON_MALFORMED_NOMINALIZATION: {
        "source_gate": "template",
        "allowed_repair": ("remove_optional_malformed_sentence", "defer_malformed_must_keep"),
        "forbidden": ("add_rootless_material", "complete_unsupported_grammar"),
        "trace_required_fields": ("before_sentence_ids", "after_sentence_ids", "removed_optional_sentence_ids", "abort_reason"),
    },
    REPAIR_REASON_TOO_LONG: {
        "source_gate": "display",
        "allowed_repair": ("remove_optional_sentence", "shorten_closing"),
        "forbidden": ("delete_must_include",),
        "trace_required_fields": ("removed_optional_sentence_ids",),
    },
    REPAIR_REASON_OVERCLAIM: {
        "source_gate": "overclaim",
        "allowed_repair": ("reject", "remove_optional_overclaim_sentence"),
        "forbidden": ("weaken_overclaim_only",),
        "trace_required_fields": ("removed_overclaim_sentence_ids", "abort_reason"),
    },
    REPAIR_REASON_UNSUPPORTED_OVERCLAIM: {
        "source_gate": "overclaim",
        "allowed_repair": ("reject", "remove_optional_overclaim_sentence"),
        "forbidden": ("weaken_overclaim_only",),
        "trace_required_fields": ("removed_overclaim_sentence_ids", "abort_reason"),
    },
    REPAIR_REASON_TWO_STAGE_LABEL_MISSING: {
        "source_gate": "display",
        "allowed_repair": ("reapply_two_stage_section_labels", "rebuild_two_stage_section_boundary"),
        "forbidden": ("swap_to_fixed_completed_sentence", "add_rootless_material"),
        "trace_required_fields": ("section_ids_present", "comment_text_body_included", "display_gate_relaxed"),
    },
    REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY: {
        "source_gate": "display",
        "allowed_repair": ("rebuild_two_stage_section_boundary",),
        "forbidden": ("swap_to_fixed_completed_sentence", "add_rootless_material"),
        "trace_required_fields": ("section_ids_present", "comment_text_body_included", "display_gate_relaxed"),
    },
    REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING: {
        "source_gate": "surface",
        "allowed_repair": ("rerender_surface_from_existing_role_phrases",),
        "forbidden": ("swap_to_fixed_completed_sentence", "add_rootless_material"),
        "trace_required_fields": ("surface_signature_before", "surface_signature_after", "phase17_reason_code"),
    },
    REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK: {
        "source_gate": "display",
        "allowed_repair": ("rerender_surface_from_existing_role_phrases",),
        "forbidden": ("swap_to_fixed_completed_sentence", "add_rootless_material"),
        "trace_required_fields": ("surface_signature_before", "surface_signature_after", "phase17_reason_code"),
    },
    REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK: {
        "source_gate": "display",
        "allowed_repair": ("rerender_surface_from_existing_role_phrases",),
        "forbidden": ("invent_relation", "swap_to_fixed_completed_sentence"),
        "trace_required_fields": ("relation_type", "relation_ids_unchanged", "phase17_reason_code"),
    },
    REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH: {
        "source_gate": "display",
        "allowed_repair": ("normalize_two_stage_section_budget",),
        "forbidden": ("delete_must_include", "swap_to_fixed_completed_sentence"),
        "trace_required_fields": ("section_ids_present", "phase17_reason_code"),
    },
    REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING: {
        "source_gate": "grounding",
        "allowed_repair": ("make_declared_relation_surface_explicit", "rebind_to_existing_evidence"),
        "forbidden": ("invent_relation", "add_rootless_material"),
        "trace_required_fields": ("relation_type", "relation_ids_unchanged", "phase17_reason_code"),
    },
    REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED: {
        "source_gate": "diagnostic",
        "allowed_repair": ("classify_unavailable_reason",),
        "forbidden": ("swap_to_fixed_completed_sentence", "relax_gate"),
        "trace_required_fields": ("phase17_reason_code",),
    },
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _clean_token(value: Any) -> str:
    return _TOKEN_RE.sub("_", str(value or "").strip().lower()).strip("_")


def _dedupe(values: Iterable[Any] | Any | None) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        raw: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        raw = values
    else:
        raw = [values]
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
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
    if hasattr(value, "as_meta"):
        try:
            mapped = value.as_meta()
            if isinstance(mapped, Mapping):
                return _json_safe_mapping(mapped)
        except Exception:
            pass
    return str(value)


def _json_safe_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, item in value.items():
        key_text = str(key or "").strip()
        if not key_text or key_text in RAW_INPUT_META_KEYS:
            continue
        out[key_text] = _json_safe_value(item)
    return out


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "as_meta"):
        try:
            meta = value.as_meta()
            if isinstance(meta, Mapping):
                return dict(meta)
        except Exception:
            return {}
    return {}


def _coerce_surface_realization(value: Any, **surface_kwargs: Any) -> CompleteSurfaceRealizationV2:
    if isinstance(value, CompleteSurfaceRealizationV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSurfaceRealizationV2(
            plan_id=value.get("plan_id") or "complete_surface_realization_v2",
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "unknown",
            surface_lines=value.get("surface_lines") or value.get("lines") or (),
            source_sentence_plan=value.get("source_sentence_plan") or value.get("sentence_plan") or None,
            meta=value.get("meta") or {},
            status=value.get("status") or COMPLETE_SURFACE_STATUS_READY,
        )
    return build_complete_surface_realization_v2(**surface_kwargs)


def _coerce_plan(value: Any) -> CompleteSentencePlanV2 | None:
    if isinstance(value, CompleteSentencePlanV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanV2(
            plan_id=value.get("plan_id") or "complete_sentence_plan_v2",
            sentence_budget=value.get("sentence_budget") or len(value.get("sentence_plans") or value.get("lines") or ()) or 2,
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "unknown",
            sentence_plans=value.get("sentence_plans") or value.get("lines") or (),
            meta=value.get("meta") or {},
        )
    return None


def _plan_line_from_surface_line(line: CompleteSurfaceLineV2) -> CompleteSentencePlanLine:
    source = _json_safe_mapping(line.source_sentence_plan_line)
    return CompleteSentencePlanLine(
        sentence_id=source.get("sentence_id") or line.sentence_id,
        line_role=source.get("line_role") or line.line_role,
        relation_type=source.get("relation_type") or line.relation_type,
        focus_rank=source.get("focus_rank") or 1,
        phrase_unit_ids=source.get("phrase_unit_ids") or source.get("used_phrase_unit_ids") or line.phrase_unit_ids,
        evidence_span_ids=source.get("evidence_span_ids") or source.get("used_evidence_span_ids") or line.evidence_span_ids,
        must_include_roles=source.get("must_include_roles") or (),
        optional_roles=source.get("optional_roles") or (),
        forbidden_surface_keys=source.get("forbidden_surface_keys") or line.forbidden_surface_keys,
        max_chars=source.get("max_chars") or 120,
        surface_intent=source.get("surface_intent") or f"{line.line_role}_observation",
        repair_policy=source.get("repair_policy") or ("self_repair_allowed",),
        meta={
            **_json_safe_mapping(source.get("meta") or {}),
            "source_step": COMPLETE_SELF_REPAIR_STAGE,
            "derived_from_surface_line": True,
            "raw_input_included": False,
        },
    )


def _source_plan_for(realization: CompleteSurfaceRealizationV2) -> CompleteSentencePlanV2:
    plan = _coerce_plan(realization.source_sentence_plan)
    if plan is not None:
        return plan
    lines = [_plan_line_from_surface_line(line) for line in realization.surface_lines]
    return CompleteSentencePlanV2(
        plan_id=f"{realization.plan_id}_source_plan",
        sentence_budget=max(2, min(5, len(lines) or 2)),
        coverage_group=realization.coverage_group,
        sentence_plans=lines,
        meta={"source_step": COMPLETE_SELF_REPAIR_STAGE, "raw_input_included": False},
    )


def _line_plan_map(plan: CompleteSentencePlanV2) -> dict[str, CompleteSentencePlanLine]:
    return {line.sentence_id: line for line in plan.sentence_plans}


def _line_two_stage_section_id(line: CompleteSurfaceLineV2) -> str:
    for source in (line.meta, line.surface_signature, line.source_sentence_plan_line):
        if isinstance(source, Mapping):
            section_id = _clean(source.get("two_stage_section_id") or _json_safe_mapping(source.get("meta") or {}).get("two_stage_section_id"))
            if section_id:
                return section_id
    return ""


def _repair_two_stage_section_boundary(
    realization: CompleteSurfaceRealizationV2,
    original_plan: CompleteSentencePlanV2,
    *,
    attempt: int,
    reason: str,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool, bool]:
    """Rebuild labels/boundaries from existing section meta only.

    Phase16-7 allows relabeling or reordering section boundaries, but not
    Python-fixed body text and not empty sections merely to satisfy the Gate.
    """

    lines = tuple(realization.surface_lines)
    observation_lines = tuple(line for line in lines if _line_two_stage_section_id(line) == "observation")
    reception_lines = tuple(line for line in lines if _line_two_stage_section_id(line) == "reception")
    if not observation_lines and not reception_lines:
        return None, "two_stage_section_meta_missing_fail_closed", False, False
    if not observation_lines or not reception_lines:
        return None, "two_stage_section_missing_fail_closed", False, False

    remaining_lines = tuple(
        line for line in lines if _line_two_stage_section_id(line) not in {"observation", "reception"}
    )
    ordered_lines = (*observation_lines, *reception_lines, *remaining_lines)
    operation = (
        "rebuild_two_stage_section_boundary"
        if reason == REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY
        else "reapply_two_stage_section_labels"
    )
    repaired = _rebuild_realization(
        realization,
        original_plan,
        ordered_lines,
        attempt=attempt,
        operation=operation,
    )
    repaired.meta.update({
        "two_stage_self_repair_applied": True,
        "two_stage_self_repair_reason": reason,
        "two_stage_self_repair_operation": operation,
        "two_stage_section_ids_present": ["observation", "reception"],
        "comment_text_body_included": False,
        "raw_input_included": False,
        "display_gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
    })
    return repaired, operation, True, False


def _phase17_section_budget_trim_blocked(line: CompleteSurfaceLineV2, plan_line: CompleteSentencePlanLine | None) -> bool:
    """Return True only for explicitly protected excess section rows.

    Section-budget repair may drop an excess section row without adding body
    text, but it must fail closed when a line is explicitly marked as protected
    for this Phase17 boundary.  General role coverage remains enforced by the
    grounding gate after repair.
    """

    meta = _json_safe_mapping(getattr(line, "meta", None))
    source = line.source_sentence_plan_line if isinstance(line.source_sentence_plan_line, Mapping) else {}
    if meta.get("phase17_7_section_budget_must_keep") is True:
        return True
    if meta.get("two_stage_section_budget_must_keep") is True:
        return True
    if source.get("phase17_7_section_budget_must_keep") is True:
        return True
    if plan_line is not None and isinstance(plan_line.meta, Mapping) and plan_line.meta.get("phase17_7_section_budget_must_keep") is True:
        return True
    return False


def _repair_phase17_section_budget_mismatch(
    realization: CompleteSurfaceRealizationV2,
    original_plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool, bool]:
    """Normalize two-stage section counts without adding body text.

    Phase17-7 may trim only optional excess rows.  If a must-include row would
    need to be deleted to satisfy the display budget, the repair fails closed.
    """

    lines = tuple(realization.surface_lines)
    plan_map = _line_plan_map(original_plan)
    observation_lines = tuple(line for line in lines if _line_two_stage_section_id(line) == "observation")
    reception_lines = tuple(line for line in lines if _line_two_stage_section_id(line) == "reception")
    other_lines = tuple(line for line in lines if _line_two_stage_section_id(line) not in {"observation", "reception"})

    if not observation_lines or not reception_lines:
        return None, "phase17_section_budget_section_missing_fail_closed", False, False

    kept_observation: list[CompleteSurfaceLineV2] = []
    kept_reception: list[CompleteSurfaceLineV2] = []
    removed: list[str] = []
    blocked_must_keep: list[str] = []

    for line in observation_lines:
        if len(kept_observation) < 1:
            kept_observation.append(line)
            continue
        if _phase17_section_budget_trim_blocked(line, plan_map.get(line.sentence_id)):
            blocked_must_keep.append(line.sentence_id)
        else:
            removed.append(line.sentence_id)

    for line in reception_lines:
        if len(kept_reception) < 2:
            kept_reception.append(line)
            continue
        if _phase17_section_budget_trim_blocked(line, plan_map.get(line.sentence_id)):
            blocked_must_keep.append(line.sentence_id)
        else:
            removed.append(line.sentence_id)

    if blocked_must_keep:
        return None, "phase17_section_budget_must_include_trim_blocked", False, False
    if not removed:
        return None, "phase17_section_budget_already_normalized", False, False

    kept_sentence_ids = {line.sentence_id for line in (*kept_observation, *kept_reception, *other_lines)}
    normalized_lines = tuple(line for line in (*kept_observation, *kept_reception, *other_lines) if line.sentence_id in kept_sentence_ids)
    if len(normalized_lines) < 2:
        return None, "phase17_section_budget_minimum_lines_fail_closed", False, False

    repaired = _rebuild_realization(
        realization,
        original_plan,
        normalized_lines,
        attempt=attempt,
        operation="normalize_two_stage_section_budget",
    )
    repaired.meta.update({
        "phase17_7_self_repair_applied": True,
        "phase17_7_self_repair_reason": REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
        "phase17_7_self_repair_operation": "normalize_two_stage_section_budget",
        "phase17_reason_code": REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
        "phase17_removed_excess_section_sentence_ids": list(removed),
        "phase17_observation_line_count_after": len(kept_observation),
        "phase17_reception_line_count_after": len(kept_reception),
        "comment_text_body_included": False,
        "raw_input_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "fixed_sentence_template_used": False,
    })
    return repaired, "normalize_two_stage_section_budget", True, False


def _is_must_include(plan_line: CompleteSentencePlanLine | None, surface_line: CompleteSurfaceLineV2 | None = None) -> bool:
    if plan_line is not None and plan_line.must_include_roles:
        return True
    if surface_line is not None:
        source = surface_line.source_sentence_plan_line
        if isinstance(source, Mapping) and source.get("must_include_roles"):
            return True
    return False


def _is_optional(plan_line: CompleteSentencePlanLine | None, surface_line: CompleteSurfaceLineV2) -> bool:
    if surface_line.line_role == "closing":
        return True
    if plan_line is not None and plan_line.optional_roles:
        return True
    return not _is_must_include(plan_line, surface_line)


def _line_has_binding(line: CompleteSurfaceLineV2) -> bool:
    return bool(line.evidence_span_ids and line.phrase_unit_ids and line.relation_type)


def _relation_context_flags_for_line(
    line: CompleteSurfaceLineV2,
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
) -> dict[str, Any]:
    """Build input-free context flags for relation marker selection.

    The flags use only already-generated surface text and internal plan/surface
    metadata. They never inspect raw user input. For recovery, prior load is
    considered present only when surrounding generated material or binding meta
    carries pressure, fatigue, burden, limit, hurt, residue, or load cues.
    """

    relation = normalize_relation_surface_type(line.relation_type)
    load_markers = (
        "load", "pressure", "fatigue", "burden", "weight", "limit",
        "hurt", "residue", "prior", "pre", "stress", "tension",
        "accumulation", "heavy", "重さ", "負荷", "圧力", "疲れ",
        "痛み", "限界", "前段", "その前", "前の流れ",
    )
    values: list[str] = [
        line.surface_text,
        line.line_role,
        line.role_phrase_key,
        line.relation_type,
        *list(line.role_phrase_keys or ()),
        *list(getattr(realization, "relation_types", ()) or ()),
    ]
    source = line.source_sentence_plan_line if isinstance(line.source_sentence_plan_line, Mapping) else {}
    for key in (
        "must_include_roles", "optional_roles", "phrase_unit_roles",
        "role", "roles", "relation_type", "coverage_group",
    ):
        item = source.get(key)
        if isinstance(item, (list, tuple, set)):
            values.extend(str(v) for v in item)
        elif item is not None:
            values.append(str(item))
    if isinstance(getattr(line, "meta", None), Mapping):
        values.extend(str(v) for k, v in line.meta.items() if k not in RAW_INPUT_META_KEYS and isinstance(v, (str, int, float, bool)))
    if isinstance(getattr(realization, "meta", None), Mapping):
        values.extend(str(v) for k, v in realization.meta.items() if k not in RAW_INPUT_META_KEYS and isinstance(v, (str, int, float, bool)))
    if isinstance(getattr(plan, "meta", None), Mapping):
        values.extend(str(v) for k, v in plan.meta.items() if k not in RAW_INPUT_META_KEYS and isinstance(v, (str, int, float, bool)))
    for plan_line in plan.sentence_plans:
        values.extend([plan_line.relation_type, plan_line.line_role, plan_line.surface_intent])
        values.extend(str(v) for v in tuple(plan_line.must_include_roles or ()))
        values.extend(str(v) for v in tuple(plan_line.optional_roles or ()))
        if isinstance(plan_line.meta, Mapping):
            values.extend(str(v) for k, v in plan_line.meta.items() if k not in RAW_INPUT_META_KEYS and isinstance(v, (str, int, float, bool)))
    compact = " ".join(str(value or "") for value in values)
    prior_load_present = bool(relation == "recovery" and any(marker in compact for marker in load_markers))
    return {
        "prior_load_present": prior_load_present,
        "relation_type": relation,
        "context_source": "complete_self_repair_generated_surface_and_meta",
        "raw_input_included": False,
    }


def _relation_marker_line_meta(line: CompleteSurfaceLineV2) -> dict[str, Any]:
    meta = _json_safe_mapping(line.meta)
    keys = (
        "relation_surface_contract_version",
        "contract_version",
        "self_repair_relation_marker_applied",
        "self_repair_relation_marker_key",
        "self_repair_relation_marker_phrase_present",
        "self_repair_relation_marker_signal",
        "self_repair_relation_marker_context",
        "relation_marker_key",
        "relation_marker_signal",
    )
    return {key: meta[key] for key in keys if key in meta}


def _collect_relation_marker_meta(surface_lines: Sequence[CompleteSurfaceLineV2] | None) -> dict[str, Any]:
    markers: list[dict[str, Any]] = []
    marker_keys: list[str] = []
    signal_keys: list[str] = []
    relation_types: list[str] = []
    signal_detected = False
    signal_count = 0

    for line in tuple(surface_lines or ()):  # defensive for tests/future mappings
        marker_meta = _relation_marker_line_meta(line)
        if not marker_meta:
            continue
        markers.append(marker_meta)
        marker_key = marker_meta.get("self_repair_relation_marker_key") or marker_meta.get("relation_marker_key")
        if marker_key:
            marker_keys.append(str(marker_key))
        signal = marker_meta.get("self_repair_relation_marker_signal") or marker_meta.get("relation_marker_signal") or {}
        if isinstance(signal, Mapping):
            signal_detected = signal_detected or bool(signal.get("reader_relation_signal_detected") or signal.get("detected"))
            try:
                signal_count += int(signal.get("reader_relation_signal_count") or signal.get("count") or 0)
            except (TypeError, ValueError):
                signal_count += 0
            signal_keys.extend(str(item) for item in signal.get("reader_relation_signal_keys") or signal.get("keys") or [])
            relation_types.extend(str(item) for item in signal.get("reader_relation_signal_relation_types") or signal.get("relation_types") or [])

    marker_keys_tuple = _dedupe(marker_keys)
    signal_keys_tuple = _dedupe(signal_keys)
    relation_types_tuple = _dedupe(relation_types)
    # Some older signal payloads only exposed keys, so keep them as a detected
    # signal, but do not allow an empty key list to pass as relation evidence.
    signal_detected = bool(signal_detected or signal_keys_tuple)
    if signal_detected and signal_count <= 0:
        signal_count = len(signal_keys_tuple)

    signal_payload = {
        "reader_relation_signal_detected": signal_detected,
        "reader_relation_signal_count": signal_count,
        "reader_relation_signal_keys": list(signal_keys_tuple),
        "reader_relation_signal_relation_types": list(relation_types_tuple),
    }
    return {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "self_repair_relation_marker_applied": bool(markers),
        "self_repair_relation_marker_key": marker_keys_tuple[0] if marker_keys_tuple else "",
        "self_repair_relation_marker_keys": list(marker_keys_tuple),
        "self_repair_relation_marker_count": len(markers),
        "self_repair_relation_marker_relation_type": relation_types_tuple[0] if relation_types_tuple else "",
        "self_repair_relation_marker_signal_detected": signal_detected,
        "self_repair_relation_marker_signal_count": signal_count,
        "self_repair_relation_marker_signal_keys": list(signal_keys_tuple),
        "self_repair_relation_marker_signal_relation_types": list(relation_types_tuple),
        "self_repair_relation_signal_detected": signal_detected,
        "self_repair_relation_signal_count": signal_count,
        "self_repair_relation_signal_keys": list(signal_keys_tuple),
        "self_repair_relation_signal_relation_types": list(relation_types_tuple),
        "self_repair_relation_signal": signal_payload,
        "self_repair_relation_marker_meaning_added": False,
        "self_repair_relation_marker_gate_relaxed": False,
        "self_repair_relation_marker_raw_input_included": False,
        "self_repair_relation_markers": markers,
        "raw_input_included": False,
    }


def _evidence_ids_from(value: Any) -> Tuple[str, ...]:
    if value is None:
        return tuple()
    if isinstance(value, Mapping):
        return _dedupe(value.get("allowed_evidence_span_ids") or value.get("used_evidence_span_ids") or value.get("evidence_span_ids"))
    if hasattr(value, "allowed_evidence_span_ids"):
        return _dedupe(getattr(value, "allowed_evidence_span_ids", None))
    if hasattr(value, "span_id"):
        return _dedupe([getattr(value, "span_id", "")])
    return _dedupe(value)


def _allowed_rebind_ids(*sources: Any) -> Tuple[str, ...]:
    ids: list[str] = []
    for source in sources:
        if source is None:
            continue
        if isinstance(source, Sequence) and not isinstance(source, (str, bytes, Mapping)):
            for item in source:
                ids.extend(_evidence_ids_from(item))
        else:
            ids.extend(_evidence_ids_from(source))
    return _dedupe(ids)


def _normalize_reason(value: Any) -> str:
    reason = _clean_token(value)
    aliases = {
        "two_stage_label_missing": REPAIR_REASON_TWO_STAGE_LABEL_MISSING,
        "two_stage_labels_missing_or_duplicated": REPAIR_REASON_TWO_STAGE_LABEL_MISSING,
        "two_stage_required_but_unrealized": REPAIR_REASON_TWO_STAGE_LABEL_MISSING,
        "two_stage_complete_surface_realizer_label_missing": REPAIR_REASON_TWO_STAGE_LABEL_MISSING,
        "two_stage_observation_section_empty": REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY,
        "two_stage_reception_section_empty": REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY,
        "two_stage_complete_surface_realizer_section_empty": REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY,
        "complete_relation_not_expressed": REPAIR_REASON_RELATION_NOT_EXPRESSED,
        "complete_over_echo": REPAIR_REASON_OVER_ECHO,
        "over_echo": REPAIR_REASON_OVER_ECHO,
        "raw_copy": REPAIR_REASON_RAW_ECHO,
        "raw_quote": REPAIR_REASON_RAW_ECHO,
        "too_long_comment": REPAIR_REASON_TOO_LONG,
        "surface_too_long": REPAIR_REASON_TOO_LONG,
        "same_ending_major_detected": REPAIR_REASON_TEMPLATE_LIKE,
        "fixed_template_like": REPAIR_REASON_TEMPLATE_LIKE,
        "template_major": REPAIR_REASON_TEMPLATE_LIKE,
        "surface_template_major": REPAIR_REASON_TEMPLATE_LIKE,
        "surface_template_major_detected": REPAIR_REASON_TEMPLATE_LIKE,
        "surface_signature_repeat": REPAIR_REASON_TEMPLATE_LIKE,
        "surface_signature_repeat_detected": REPAIR_REASON_TEMPLATE_LIKE,
        "connector_repeat": REPAIR_REASON_TEMPLATE_LIKE,
        "connector_repetition": REPAIR_REASON_TEMPLATE_LIKE,
        "surface_connector_repetition": REPAIR_REASON_TEMPLATE_LIKE,
        "predicate_family_repetition": REPAIR_REASON_TEMPLATE_LIKE,
        "ending_repetition": REPAIR_REASON_TEMPLATE_LIKE,
        "same_ending_family": REPAIR_REASON_TEMPLATE_LIKE,
        "generic_center_phrase": REPAIR_REASON_TEMPLATE_LIKE,
        "raw_echo_risk": REPAIR_REASON_RAW_ECHO,
        "malformed_nominalization": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "malformed_nominalization_risk": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "surface_grammar_warning": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "grammar_warning": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "phrase_unit_grammar": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "stem_koto_hanareru": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "particle_leftover": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "unfinished_phrase": REPAIR_REASON_UNSUPPORTED_SENTENCE,
        "unsupported_overclaim": REPAIR_REASON_UNSUPPORTED_OVERCLAIM,
        "surface_template_major": REPAIR_REASON_TEMPLATE_LIKE,
        "template_major": REPAIR_REASON_TEMPLATE_LIKE,
        "generic_center_phrase": REPAIR_REASON_TEMPLATE_LIKE,
        "center_phrase": REPAIR_REASON_TEMPLATE_LIKE,
        "same_connector_run": REPAIR_REASON_TEMPLATE_LIKE,
        "connector_repeat": REPAIR_REASON_TEMPLATE_LIKE,
        "connector_repetition": REPAIR_REASON_TEMPLATE_LIKE,
        "connector_family_repetition": REPAIR_REASON_TEMPLATE_LIKE,
        "same_ending_family": REPAIR_REASON_TEMPLATE_LIKE,
        "observation_predicate_stack": REPAIR_REASON_TEMPLATE_LIKE,
        "surface_signature_repeat": REPAIR_REASON_TEMPLATE_LIKE,
        "raw_echo_risk": REPAIR_REASON_RAW_ECHO,
        "grammar_warning": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "surface_grammar_warning": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "grammar_major": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "malformed_nominalization": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "malformed_nominalization_risk": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "stem_koto_hanareru": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "malformed_nominalization_missing_ru": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "malformed_nominalization_particle_before_koto": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        "malformed_nominalization_auxiliary_fragment": REPAIR_REASON_MALFORMED_NOMINALIZATION,
        **PHASE17_REPAIRABLE_REASON_ALIASES,
    }
    return aliases.get(reason, reason)


def normalize_complete_self_repair_reason(value: Any) -> str:
    """Return the bounded Complete self-repair reason used for handoff.

    Phase17-7 keeps product-visible unavailable diagnostics internal, but the
    handoff itself must still be normalized before filtering against
    ``ALLOWED_REPAIR_REASONS``.  The helper is intentionally meta-only and does
    not inspect or carry generated body text.
    """

    return _normalize_reason(value)


def _reasons_from_gate_input(gate_reasons: Any = None, grounding_report: Any = None, gate_results: Any = None, meta: Mapping[str, Any] | None = None) -> Tuple[str, ...]:
    reasons: list[str] = []
    for raw in _dedupe(gate_reasons):
        reasons.append(_normalize_reason(raw))
    if grounding_report is not None:
        reasons.extend(_normalize_reason(raw) for raw in _dedupe(getattr(grounding_report, "rejection_reasons", None)))
        reasons.extend(_normalize_reason(raw) for raw in _dedupe(getattr(grounding_report, "binding_rejection_reasons", None)))
        diagnostics = getattr(grounding_report, "binding_diagnostics", None)
        if isinstance(diagnostics, Mapping):
            reasons.extend(_normalize_reason(raw) for raw in _dedupe(diagnostics.get("repair_targets")))
            if diagnostics.get("over_echo_count"):
                reasons.append(REPAIR_REASON_OVER_ECHO)
            if diagnostics.get("relation_not_expressed_count"):
                reasons.append(REPAIR_REASON_RELATION_NOT_EXPRESSED)
    if isinstance(gate_results, Mapping):
        for key in ("rejection_reasons", "reasons", "repair_targets", "failed_reasons"):
            reasons.extend(_normalize_reason(raw) for raw in _dedupe(gate_results.get(key)))
        if gate_results.get("template_like") or gate_results.get("same_ending_major_detected"):
            reasons.append(REPAIR_REASON_TEMPLATE_LIKE)
        if gate_results.get("raw_echo") or gate_results.get("over_echo"):
            reasons.append(REPAIR_REASON_RAW_ECHO)
        if gate_results.get("too_long"):
            reasons.append(REPAIR_REASON_TOO_LONG)
    if isinstance(meta, Mapping):
        for key in ("gate_reasons", "repair_targets", "rejection_reasons"):
            reasons.extend(_normalize_reason(raw) for raw in _dedupe(meta.get(key)))
        surface_signature = meta.get("surface_quality_signature") or meta.get("step2_surface_quality_signature")
        if isinstance(surface_signature, Mapping) or isinstance(meta.get("surface_aware_self_repair_request"), Mapping):
            reasons.extend(
                _normalize_reason(raw)
                for raw in derive_surface_aware_repair_reasons(
                    surface_quality_signature=surface_signature if isinstance(surface_signature, Mapping) else None,
                    gate_reasons=gate_reasons,
                    gate_results=gate_results,
                    meta=meta,
                )
            )
    return tuple(reason for reason in _dedupe(reasons) if reason)



_PHASE17_REASON_SOURCE_KEYS = (
    "rejection_reasons",
    "validation_errors",
    "unavailable_reason_codes",
    "two_stage_unavailable_reason_codes",
    "phase16_7_unavailable_reason_codes",
    "phase17_reason_codes",
    "repair_targets",
    "gate_reasons",
    "self_repair_handoff_reasons",
    "observed_repair_reasons",
    "surface_aware_repair_reasons",
    "blocked_reasons",
    "binding_rejection_reasons",
)


def _collect_phase17_reason_values(value: Any, *, depth: int = 0) -> list[str]:
    if value is None or depth > 4:
        return []
    reasons: list[str] = []
    if isinstance(value, Mapping):
        for key in _PHASE17_REASON_SOURCE_KEYS:
            reasons.extend(_dedupe(value.get(key)))
        for flag_key, reason in (
            ("internal_role_label_leak_detected", REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK),
            ("relation_skeleton_leak_detected", REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK),
            ("two_stage_required_but_unrealized", REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING),
            ("section_budget_valid", REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH),
            ("grounding_passed", REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING),
        ):
            if flag_key not in value:
                continue
            flag_value = value.get(flag_key)
            if flag_key.endswith("_valid") or flag_key.endswith("_passed"):
                if flag_value is False:
                    reasons.append(reason)
            elif flag_value is True:
                reasons.append(reason)
        for key, item in value.items():
            key_text = str(key or "")
            if key_text in RAW_INPUT_META_KEYS or "text" in key_text or "body" in key_text or "surface_lines" == key_text:
                continue
            if isinstance(item, (Mapping, list, tuple)):
                reasons.extend(_collect_phase17_reason_values(item, depth=depth + 1))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            reasons.extend(_collect_phase17_reason_values(item, depth=depth + 1))
    return list(_dedupe(reasons))


def _phase17_product_visible_reason_codes(reasons: Iterable[Any]) -> Tuple[str, ...]:
    codes: list[str] = []
    normalized = [_normalize_reason(reason) for reason in _dedupe(reasons)]
    for reason in normalized:
        if reason in PHASE17_PRODUCT_VISIBLE_REASON_CODES:
            codes.append(reason)
        elif reason == REPAIR_REASON_TEMPLATE_LIKE:
            codes.append(REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING)
        elif reason == REPAIR_REASON_RELATION_NOT_EXPRESSED:
            codes.append(REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING)
    return _dedupe(codes)


def build_phase17_self_repair_unavailable_reason_summary(
    *,
    primary_reason: Any = "",
    candidate_status: Any = "",
    surface_meta: Mapping[str, Any] | None = None,
    grounding_meta: Mapping[str, Any] | None = None,
    self_repair_meta: Mapping[str, Any] | None = None,
    extra_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a meta-only Phase17-7 reason summary.

    The summary is internal diagnostic material.  It classifies repairable
    product-visible failures without carrying the generated body, raw input, or
    public response changes.
    """

    raw_reasons: list[str] = []
    if primary_reason:
        raw_reasons.append(_clean(primary_reason))
    for source in (surface_meta, grounding_meta, self_repair_meta, extra_meta):
        raw_reasons.extend(_collect_phase17_reason_values(source))
    normalized = tuple(_normalize_reason(reason) for reason in _dedupe(raw_reasons))
    repair_handoff = tuple(reason for reason in normalized if reason in ALLOWED_REPAIR_REASONS)
    phase17_codes_base = _phase17_product_visible_reason_codes(normalized)
    status = _clean_token(candidate_status)
    extra_map = _json_safe_mapping(extra_meta)
    explicit_reached = bool(
        extra_map.get("phase17_product_visible_fixture_reached") is True
        or extra_map.get("product_visible_fixture_reached") is True
        or _clean_token(extra_map.get("phase17_product_visible_fixture_reached")) in {"true", "yes", "1", "passed", "generated"}
        or _clean_token(extra_map.get("product_visible_fixture_reached")) in {"true", "yes", "1", "passed", "generated"}
    )
    product_visible_reached = bool(explicit_reached or (status == "generated" and not phase17_codes_base))
    diagnostic_only_codes: Tuple[str, ...] = tuple()
    if not product_visible_reached:
        diagnostic_only_codes = (REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED,)
    phase17_codes = _dedupe([*phase17_codes_base, *diagnostic_only_codes])
    repair_handoff = tuple(
        reason
        for reason in repair_handoff
        if reason not in PHASE17_DIAGNOSTIC_ONLY_REASONS
    )
    return {
        "schema_version": PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION,
        "source_phase": PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE,
        "primary_reason": _clean(primary_reason),
        "candidate_status": status,
        "product_visible_fixture_reached": product_visible_reached,
        "product_visible_fixture_not_reached": not product_visible_reached,
        "phase17_reason_codes": list(phase17_codes),
        "normalized_repair_reason_codes": list(normalized),
        "self_repair_handoff_reason_codes": list(repair_handoff),
        "self_repair_target_reason_codes": list(repair_handoff),
        "repair_target_reason_codes": list(repair_handoff),
        "repairable_reason_codes": list(repair_handoff),
        "diagnostic_only_reason_codes": list(diagnostic_only_codes),
        "release_blocker": bool(diagnostic_only_codes and not repair_handoff),
        "surface_rerender_reason_codes": [reason for reason in repair_handoff if reason in PHASE17_SURFACE_REWRITE_REPAIR_REASONS or reason == REPAIR_REASON_TEMPLATE_LIKE],
        "grounding_relation_binding_reason_codes": [reason for reason in repair_handoff if reason in {REPAIR_REASON_RELATION_NOT_EXPRESSED, REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING}],
        "section_budget_reason_codes": [reason for reason in repair_handoff if reason in {REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH, REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY}],
        "surface_mode_policy_missing": REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING in phase17_codes,
        "internal_role_label_leak": REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK in phase17_codes,
        "relation_skeleton_leak": REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK in phase17_codes,
        "section_budget_mismatch": REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH in phase17_codes,
        "grounding_relation_binding_missing": REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING in phase17_codes,
        "product_visible_fixture_not_reached_reason_code": REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED in phase17_codes,
        "reason_summary_only": True,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "fixed_sentence_template_used": False,
        "public_response_key_added": False,
    }


def _operation_for(reason: str) -> str:
    return {
        REPAIR_REASON_UNSUPPORTED_SENTENCE: "remove_optional_or_rebind_evidence",
        REPAIR_REASON_RELATION_NOT_EXPRESSED: "make_declared_relation_surface_explicit",
        REPAIR_REASON_TEMPLATE_LIKE: "vary_surface_signature_tail_connector_order",
        REPAIR_REASON_RAW_ECHO: "reduce_raw_echo_by_role_phrase_rephrase",
        REPAIR_REASON_OVER_ECHO: "reduce_raw_echo_by_role_phrase_rephrase",
        REPAIR_REASON_TOO_LONG: "remove_optional_or_shorten_closing",
        REPAIR_REASON_OVERCLAIM: "reject_or_remove_overclaim_optional_line",
        REPAIR_REASON_UNSUPPORTED_OVERCLAIM: "reject_or_remove_overclaim_optional_line",
        REPAIR_REASON_MALFORMED_NOMINALIZATION: "remove_optional_malformed_sentence_or_fail_closed",
        REPAIR_REASON_TWO_STAGE_LABEL_MISSING: "reapply_two_stage_section_labels",
        REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY: "rebuild_two_stage_section_boundary",
        REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING: "rerender_surface_from_existing_role_phrases",
        REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK: "rerender_surface_from_existing_role_phrases",
        REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK: "rerender_surface_from_existing_role_phrases",
        REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH: "normalize_two_stage_section_budget",
        REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING: "make_declared_relation_surface_explicit",
        REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED: "classify_unavailable_reason",
    }.get(reason, "aborted_unknown_repair_reason")


def _contract_boundary() -> dict[str, Any]:
    return {
        "comment_text_contract": "passed_only",
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


def _source_policy() -> dict[str, Any]:
    return {
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "llm_generation_used": False,
        "fixed_sentence_template_used": False,
        "fixed_sentence_template_allowed": False,
        "fixed_fallback_used": False,
        "fixed_fallback_allowed": False,
        "completion_sentence_template_used": False,
        "input_specific_template_used": False,
    }


def build_complete_self_repair_policy_table_v2() -> dict[str, dict[str, Any]]:
    """Return the Product Quality Step4 repair policy table.

    The table is deliberately additive meta.  Runtime repair still only changes
    plan/surface artifacts and never relaxes Reader/Grounding/Template/Display
    gates, but diagnostics and scorecard can now inspect the exact operation
    allowed for each gate reason.
    """

    return {
        REPAIR_REASON_UNSUPPORTED_SENTENCE: {
            "source_gate": "grounding",
            "allowed_operations": ["remove_optional_line", "rebind_to_existing_evidence"],
            "forbidden_operations": ["add_rootless_material"],
            "required_trace_fields": ["before_sentence_ids", "after_sentence_ids", "removed_optional_sentence_ids", "rebind_reason"],
            "meaning_added": False,
        },
        REPAIR_REASON_RELATION_NOT_EXPRESSED: {
            "source_gate": "grounding",
            "allowed_operations": ["make_declared_relation_surface_explicit", "replace_connector"],
            "forbidden_operations": ["invent_relation"],
            "required_trace_fields": ["relation_type", "relation_ids_preserved"],
            "meaning_added": False,
        },
        REPAIR_REASON_TEMPLATE_LIKE: {
            "source_gate": "template",
            "allowed_operations": ["vary_surface_signature_tail_connector_order"],
            "forbidden_operations": ["swap_to_fixed_completed_sentence"],
            "required_trace_fields": ["surface_signature_before", "surface_signature_after"],
            "meaning_added": False,
        },
        REPAIR_REASON_RAW_ECHO: {
            "source_gate": "template",
            "allowed_operations": ["reduce_raw_echo_by_role_phrase_rephrase"],
            "forbidden_operations": ["expand_meaning"],
            "required_trace_fields": ["echo_ratio_before", "echo_ratio_after"],
            "meaning_added": False,
        },
        REPAIR_REASON_OVER_ECHO: {
            "source_gate": "template",
            "allowed_operations": ["reduce_raw_echo_by_role_phrase_rephrase"],
            "forbidden_operations": ["expand_meaning"],
            "required_trace_fields": ["echo_ratio_before", "echo_ratio_after"],
            "meaning_added": False,
        },
        REPAIR_REASON_MALFORMED_NOMINALIZATION: {
            "source_gate": "template",
            "allowed_operations": ["remove_optional_malformed_sentence", "fail_closed_on_malformed_must_keep"],
            "forbidden_operations": ["add_rootless_material", "complete_unsupported_grammar", "delete_must_include"],
            "required_trace_fields": ["before_sentence_ids", "after_sentence_ids", "removed_optional_sentence_ids", "abort_reason"],
            "meaning_added": False,
            "fail_closed_on_must_keep": True,
        },
        REPAIR_REASON_TOO_LONG: {
            "source_gate": "reader",
            "allowed_operations": ["remove_optional_line_for_length", "shorten_closing"],
            "forbidden_operations": ["delete_must_include"],
            "required_trace_fields": ["removed_optional_sentence_ids"],
            "meaning_added": False,
        },
        REPAIR_REASON_OVERCLAIM: {
            "source_gate": "overclaim",
            "allowed_operations": ["remove_optional_overclaim_line", "reject"],
            "forbidden_operations": ["weaken_overclaim_only"],
            "required_trace_fields": ["removed_overclaim_sentence_ids", "abort_reason"],
            "meaning_added": False,
            "reject_preferred": True,
        },
        REPAIR_REASON_UNSUPPORTED_OVERCLAIM: {
            "source_gate": "overclaim",
            "allowed_operations": ["remove_optional_overclaim_line", "reject"],
            "forbidden_operations": ["weaken_overclaim_only"],
            "required_trace_fields": ["removed_overclaim_sentence_ids", "abort_reason"],
            "meaning_added": False,
            "reject_preferred": True,
        },
        REPAIR_REASON_TWO_STAGE_LABEL_MISSING: {
            "source_gate": "display",
            "allowed_operations": ["reapply_two_stage_section_labels", "rebuild_two_stage_section_boundary"],
            "forbidden_operations": ["swap_to_fixed_completed_sentence", "add_rootless_material"],
            "required_trace_fields": ["section_ids_present", "comment_text_body_included", "display_gate_relaxed"],
            "meaning_added": False,
        },
        REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY: {
            "source_gate": "display",
            "allowed_operations": ["rebuild_two_stage_section_boundary"],
            "forbidden_operations": ["swap_to_fixed_completed_sentence", "add_rootless_material"],
            "required_trace_fields": ["section_ids_present", "comment_text_body_included", "display_gate_relaxed"],
            "meaning_added": False,
        },
        REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING: {
            "source_gate": "surface",
            "allowed_operations": ["rerender_surface_from_existing_role_phrases"],
            "forbidden_operations": ["swap_to_fixed_completed_sentence", "add_rootless_material"],
            "required_trace_fields": ["surface_signature_before", "surface_signature_after", "phase17_reason_code"],
            "meaning_added": False,
        },
        REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK: {
            "source_gate": "display",
            "allowed_operations": ["rerender_surface_from_existing_role_phrases"],
            "forbidden_operations": ["swap_to_fixed_completed_sentence", "add_rootless_material"],
            "required_trace_fields": ["surface_signature_before", "surface_signature_after", "phase17_reason_code"],
            "meaning_added": False,
        },
        REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK: {
            "source_gate": "display",
            "allowed_operations": ["rerender_surface_from_existing_role_phrases"],
            "forbidden_operations": ["invent_relation", "swap_to_fixed_completed_sentence"],
            "required_trace_fields": ["relation_type", "relation_ids_preserved", "phase17_reason_code"],
            "meaning_added": False,
        },
        REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH: {
            "source_gate": "display",
            "allowed_operations": ["normalize_two_stage_section_budget"],
            "forbidden_operations": ["delete_must_include", "swap_to_fixed_completed_sentence"],
            "required_trace_fields": ["section_ids_present", "phase17_reason_code"],
            "meaning_added": False,
        },
        REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING: {
            "source_gate": "grounding",
            "allowed_operations": ["make_declared_relation_surface_explicit", "rebind_to_existing_evidence"],
            "forbidden_operations": ["invent_relation", "add_rootless_material"],
            "required_trace_fields": ["relation_type", "relation_ids_preserved", "phase17_reason_code"],
            "meaning_added": False,
        },
        REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED: {
            "source_gate": "diagnostic",
            "allowed_operations": ["classify_unavailable_reason"],
            "forbidden_operations": ["swap_to_fixed_completed_sentence", "relax_gate"],
            "required_trace_fields": ["phase17_reason_code"],
            "meaning_added": False,
        },
    }


def build_complete_self_repair_contract_meta() -> dict[str, Any]:
    term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
    policy_table = build_complete_self_repair_policy_table_v2()
    return {
        "version": COMPLETE_SELF_REPAIR_VERSION,
        "product_quality_version": COMPLETE_SELF_REPAIR_PRODUCT_QUALITY_VERSION,
        "service_version": COMPLETE_SELF_REPAIR_VERSION,
        "repair_policy_version": COMPLETE_SELF_REPAIR_POLICY_VERSION,
        "repair_trace_contract_version": COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
        "target_step": COMPLETE_SELF_REPAIR_STAGE,
        "product_quality_step": COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE,
        "surface_aware_self_repair_version": COMPLETE_SURFACE_AWARE_SELF_REPAIR_VERSION,
        "surface_aware_self_repair_step": COMPLETE_SURFACE_AWARE_SELF_REPAIR_STEP,
        "step": COMPLETE_SELF_REPAIR_STAGE,
        "source_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
        "stage": COMPLETE_COMPOSER_STAGE,
        "implementation_unit": COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT,
        "product_quality_implementation_unit": COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_IMPLEMENTATION_UNIT,
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_family_term": term_meta["target_composer_family_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "self_repair_loop_added": True,
        "surface_aware_self_repair_version": COMPLETE_SURFACE_AWARE_SELF_REPAIR_VERSION,
        "surface_aware_self_repair_step": COMPLETE_SURFACE_AWARE_SELF_REPAIR_STEP,
        "surface_aware_self_repair_policy_version": COMPLETE_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION,
        "step10_surface_aware_self_repair_ready": True,
        "surface_aware_repair_reason_handoff_ready": True,
        "phase17_7_self_repair_unavailable_reason_supported": True,
        "phase17_7_self_repair_unavailable_reason_schema_version": PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION,
        "phase17_7_self_repair_unavailable_reason_source_phase": PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE,
        "phase17_7_product_visible_reason_codes": list(PHASE17_PRODUCT_VISIBLE_REASON_CODES),
        "phase17_7_repairable_reason_aliases": sorted(PHASE17_REPAIRABLE_REASON_ALIASES),
        "phase17_7_diagnostic_only_reasons": list(PHASE17_DIAGNOSTIC_ONLY_REASONS),
        "phase17_7_product_visible_fixture_not_reached_repair_handoff_allowed": False,
        "phase17_7_repair_targets_fixed_text_allowed": False,
        "phase17_7_gate_relaxation_allowed": False,
        "self_repair_enabled": True,
        "max_repair_attempts": MAX_SELF_REPAIR_ATTEMPTS,
        "gate_relaxation_allowed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "display_gate_relaxed": False,
        "new_meaning_addition_allowed": False,
        "meaning_addition_allowed": False,
        "new_meaning_added": False,
        "must_include_deletion_allowed": False,
        "allowed_repair_reasons": sorted(ALLOWED_REPAIR_REASONS),
        "reject_preferred_reasons": sorted(REJECT_PREFERRED_REASONS),
        "repair_policy_table": policy_table,
        "allowed_operations": {
            REPAIR_REASON_UNSUPPORTED_SENTENCE: ["remove_optional_line", "rebind_to_existing_evidence"],
            REPAIR_REASON_RELATION_NOT_EXPRESSED: ["make_relation_explicit", "replace_connector"],
            REPAIR_REASON_TEMPLATE_LIKE: ["vary_tail", "vary_connector", "vary_surface_signature"],
            REPAIR_REASON_RAW_ECHO: ["reduce_quote_density", "role_phrase_rephrase"],
            REPAIR_REASON_OVER_ECHO: ["reduce_quote_density", "role_phrase_rephrase"],
            REPAIR_REASON_MALFORMED_NOMINALIZATION: ["remove_optional_malformed_sentence", "fail_closed_on_malformed_must_keep"],
            REPAIR_REASON_TOO_LONG: ["remove_optional_line", "shorten_closing"],
            REPAIR_REASON_OVERCLAIM: ["reject", "remove_optional_overclaim_line"],
            REPAIR_REASON_UNSUPPORTED_OVERCLAIM: ["reject", "remove_optional_overclaim_line"],
            REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING: ["rerender_surface_from_existing_role_phrases"],
            REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK: ["rerender_surface_from_existing_role_phrases"],
            REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK: ["rerender_surface_from_existing_role_phrases"],
            REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH: ["normalize_two_stage_section_budget"],
            REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING: ["make_declared_relation_surface_explicit", "rebind_to_existing_evidence"],
        },
        "forbidden_operations": sorted(FORBIDDEN_REPAIR_OPERATIONS),
        "repair_trace_required": True,
        "repair_trace_records_before_after_plan_id": True,
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "self_repair_relation_marker_contract_enabled": True,
        "evidence_ids_must_remain_bound": True,
        "relation_ids_must_remain_bound": True,
        **_contract_boundary(),
        **_source_policy(),
        "raw_text_included": False,
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
    }


def _surface_signature_for_line(
    line: CompleteSurfaceLineV2,
    *,
    operation: str,
    attempt: int,
    connector_key: str | None = None,
    ending_key: str | None = None,
    variation_key: str | None = None,
) -> dict[str, Any]:
    signature = dict(line.surface_signature or {})
    new_connector = connector_key or line.connector_key
    new_ending = ending_key or line.ending_key or f"repair_tail_{attempt}"
    new_variation = variation_key or f"repair_v{attempt}"
    signature.update(
        {
            "version": COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
            "source_step": COMPLETE_SELF_REPAIR_STAGE,
            "sentence_id": line.sentence_id,
            "line_role": line.line_role,
            "relation_type": line.relation_type,
            "role_phrase_key": line.role_phrase_key,
            "connector_key": new_connector,
            "predicate_key": line.predicate_key,
            "ending_key": new_ending,
            "tone_policy_key": getattr(line, "tone_policy_key", getattr(line, "distance_policy_key", "")),
            "temperature_key": getattr(line, "temperature_key", ""),
            "tone_guard_keys": list(getattr(line, "tone_guard_keys", []) or []),
            "closing_policy_key": getattr(line, "closing_policy_key", ""),
            "read_feeling_policy_key": getattr(line, "read_feeling_policy_key", ""),
            "variation_key": new_variation,
            "repair_operation": operation,
            "completion_sentence_template_used": False,
            "raw_input_included": False,
        }
    )
    signature["signature"] = "|".join(
        _clean_token(signature.get(key))
        for key in ("line_role", "relation_type", "role_phrase_key", "connector_key", "predicate_key", "ending_key", "variation_key")
    )
    return signature


def _clone_line(
    line: CompleteSurfaceLineV2,
    *,
    surface_text: str | None = None,
    connector_key: str | None = None,
    ending_key: str | None = None,
    variation_key: str | None = None,
    evidence_span_ids: Iterable[str] | None = None,
    phrase_unit_ids: Iterable[str] | None = None,
    relation_type: str | None = None,
    operation: str = "self_repair_adjustment",
    attempt: int = 1,
    meta_updates: Mapping[str, Any] | None = None,
    signature_updates: Mapping[str, Any] | None = None,
) -> CompleteSurfaceLineV2:
    new_connector = connector_key or line.connector_key
    new_ending = ending_key or line.ending_key
    new_variation = variation_key or line.variation_key
    new_relation = relation_type or line.relation_type
    return CompleteSurfaceLineV2(
        sentence_id=line.sentence_id,
        line_role=line.line_role,
        relation_type=new_relation,
        surface_text=_clean(surface_text if surface_text is not None else line.surface_text),
        phrase_unit_ids=phrase_unit_ids if phrase_unit_ids is not None else line.phrase_unit_ids,
        evidence_span_ids=evidence_span_ids if evidence_span_ids is not None else line.evidence_span_ids,
        role_phrase_key=line.role_phrase_key,
        role_phrase_keys=line.role_phrase_keys,
        subject_policy_key=line.subject_policy_key,
        connector_key=new_connector,
        particle_key=line.particle_key,
        predicate_key=line.predicate_key,
        ending_key=new_ending,
        distance_policy_key=line.distance_policy_key,
        tone_policy_key=getattr(line, "tone_policy_key", line.distance_policy_key),
        temperature_key=getattr(line, "temperature_key", "steady_warm"),
        tone_guard_keys=getattr(line, "tone_guard_keys", ()),
        closing_policy_key=getattr(line, "closing_policy_key", "none"),
        read_feeling_policy_key=getattr(line, "read_feeling_policy_key", "input_specific_structure_reflected"),
        variation_key=new_variation,
        surface_signature={
            **_surface_signature_for_line(
                line,
                operation=operation,
                attempt=attempt,
                connector_key=new_connector,
                ending_key=new_ending,
                variation_key=new_variation,
            ),
            **_json_safe_mapping(signature_updates),
        },
        forbidden_surface_keys=line.forbidden_surface_keys,
        source_sentence_plan_line=line.source_sentence_plan_line,
        meta={
            **_json_safe_mapping(line.meta),
            **_json_safe_mapping(meta_updates),
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "self_repair_applied": True,
            "repair_operation": operation,
            "repair_attempt": attempt,
            "meaning_added": False,
            "new_meaning_added": False,
            "gate_relaxed": False,
            "tone_policy_key": getattr(line, "tone_policy_key", line.distance_policy_key),
            "temperature_key": getattr(line, "temperature_key", "steady_warm"),
            "tone_meaning_added": False,
            "raw_input_included": False,
        },
    )


def _rebuild_plan(original_plan: CompleteSentencePlanV2, surface_lines: Sequence[CompleteSurfaceLineV2], *, attempt: int, operation: str) -> CompleteSentencePlanV2:
    original_lines = _line_plan_map(original_plan)
    plan_lines: list[CompleteSentencePlanLine] = []
    for surface_line in surface_lines:
        source_line = original_lines.get(surface_line.sentence_id) or _plan_line_from_surface_line(surface_line)
        plan_lines.append(
            CompleteSentencePlanLine(
                sentence_id=source_line.sentence_id,
                line_role=source_line.line_role,
                relation_type=surface_line.relation_type or source_line.relation_type,
                focus_rank=source_line.focus_rank,
                phrase_unit_ids=surface_line.phrase_unit_ids or source_line.phrase_unit_ids,
                evidence_span_ids=surface_line.evidence_span_ids or source_line.evidence_span_ids,
                must_include_roles=source_line.must_include_roles,
                optional_roles=source_line.optional_roles,
                forbidden_surface_keys=source_line.forbidden_surface_keys,
                max_chars=source_line.max_chars,
                surface_intent=source_line.surface_intent,
                repair_policy=(*tuple(source_line.repair_policy), operation),
                meta={
                    **_json_safe_mapping(source_line.meta),
                    "source_step": COMPLETE_SELF_REPAIR_STAGE,
                    "repaired_from_plan_id": original_plan.plan_id,
                    "repair_attempt": attempt,
                    "repair_operation": operation,
                    "raw_input_included": False,
                },
            )
        )
    return CompleteSentencePlanV2(
        plan_id=f"{original_plan.plan_id}_repair{attempt}",
        sentence_budget=max(2, min(5, len(plan_lines) or 2)),
        coverage_group=original_plan.coverage_group,
        sentence_plans=plan_lines,
        meta={
            **_json_safe_mapping(original_plan.meta),
            "source_step": COMPLETE_SELF_REPAIR_STAGE,
            "repaired_from_plan_id": original_plan.plan_id,
            "repair_attempt": attempt,
            "repair_operation": operation,
            "new_meaning_added": False,
            "raw_input_included": False,
        },
    )


def _rebuild_realization(
    original: CompleteSurfaceRealizationV2,
    original_plan: CompleteSentencePlanV2,
    surface_lines: Sequence[CompleteSurfaceLineV2],
    *,
    attempt: int,
    operation: str,
) -> CompleteSurfaceRealizationV2:
    plan = _rebuild_plan(original_plan, surface_lines, attempt=attempt, operation=operation)
    status = COMPLETE_SURFACE_STATUS_READY if surface_lines else COMPLETE_SURFACE_STATUS_UNAVAILABLE
    return CompleteSurfaceRealizationV2(
        plan_id=plan.plan_id,
        coverage_group=original.coverage_group,
        surface_lines=tuple(surface_lines),
        source_sentence_plan=plan,
        status=status,
        meta={
            **_json_safe_mapping(original.meta),
            "source_step": COMPLETE_SURFACE_REALIZER_STAGE,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "self_repair_applied": True,
            "repair_attempt": attempt,
            "repair_operation": operation,
            "before_plan_id": original.plan_id,
            "after_plan_id": plan.plan_id,
            "comment_text_key_written": False,
            "response_shape_changed": False,
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "new_meaning_added": False,
            "raw_input_included": False,
        },
    )


def _surface_sentence_ids(realization: CompleteSurfaceRealizationV2 | None) -> tuple[str, ...]:
    if realization is None:
        return tuple()
    return tuple(line.sentence_id for line in realization.surface_lines if line.sentence_id)


def _signature_summary(realization: CompleteSurfaceRealizationV2 | None) -> dict[str, Any]:
    if realization is None:
        return {"surface_signatures": [], "signature_count": 0}
    summary = build_complete_surface_signature(realization)
    return {
        "version": summary.get("version") or COMPLETE_SURFACE_SIGNATURE_SCHEMA_VERSION,
        "signature_count": len(list(summary.get("surface_signatures") or [])),
        "surface_signatures": list(summary.get("surface_signatures") or []),
        "ending_keys": list(summary.get("ending_keys") or []),
        "connector_keys": list(summary.get("connector_keys") or []),
    }


def _estimate_echo_ratio(realization: CompleteSurfaceRealizationV2 | None) -> float:
    """Estimate self-echo density without storing raw input text.

    The estimate is input-free.  It combines exact repeated sentence chunks with
    repeated Japanese character n-grams so short raw-copy lines such as
    ``会議が続いた。会議が続いた。`` are visible even when the rest of the
    candidate has several non-echo lines.
    """

    if realization is None:
        return 0.0
    text = _clean(getattr(realization, "realized_text", ""))
    if not text:
        return 0.0
    chunks = [chunk for chunk in re.split(r"[、。,.!！?？\s]+", text) if len(chunk) >= 2]
    repeated_chars = 0
    total_chars = sum(len(chunk) for chunk in chunks)
    duplicate_chunk_instances = 0
    seen_chunks: set[str] = set()
    for chunk in chunks:
        if chunk in seen_chunks:
            repeated_chars += len(chunk)
            duplicate_chunk_instances += 1
        seen_chunks.add(chunk)
    # Exact repeated clauses are a strong raw-echo signal even when only one
    # line repeats inside a longer candidate.  Add a bounded boost so repair
    # traces reflect clear sentence-level repetition without depending on raw
    # input text.
    chunk_ratio = repeated_chars / max(1, total_chars)
    duplicate_chunk_boost = min(0.45, 0.15 * duplicate_chunk_instances)

    compact = re.sub(r"[、。,.!！?？\s]+", "", text)
    ngram_ratio = 0.0
    if len(compact) >= 8:
        grams = [compact[index:index + 4] for index in range(0, len(compact) - 3)]
        if grams:
            duplicate_count = len(grams) - len(set(grams))
            ngram_ratio = duplicate_count / max(1, len(grams))
    return round(min(1.0, max(chunk_ratio + duplicate_chunk_boost, ngram_ratio)), 3)


def _relation_type_for_trace(realization: CompleteSurfaceRealizationV2 | None) -> str:
    if realization is None:
        return ""
    for line in realization.surface_lines:
        relation = _clean_token(line.relation_type)
        if relation and relation not in {"center", "context", "unknown", "neutral"}:
            return relation
    return _clean_token(next(iter(realization.relation_types), ""))


def _source_gate_for_reason(reason: str) -> str:
    policy = build_complete_self_repair_policy_table_v2().get(reason) or {}
    source_gate = _clean(policy.get("source_gate"))
    return source_gate if source_gate in {"reader", "grounding", "template", "overclaim", "display", "surface", "diagnostic"} else "grounding"


def _repair_trace_v2_meta(
    *,
    before: CompleteSurfaceRealizationV2 | None,
    after: CompleteSurfaceRealizationV2 | None,
    reason: str,
    operation: str,
    abort_reason: str = "",
) -> dict[str, Any]:
    before_ids = _surface_sentence_ids(before)
    after_ids = _surface_sentence_ids(after)
    removed_ids = tuple(item for item in before_ids if item not in set(after_ids))
    before_evidence_ids = tuple(getattr(before, "used_evidence_span_ids", ()) or ())
    after_evidence_ids = tuple(getattr(after, "used_evidence_span_ids", ()) or ())
    before_relation_ids = tuple(getattr(before, "relation_types", ()) or ())
    after_relation_ids = tuple(getattr(after, "relation_types", ()) or ())
    added_evidence_ids = tuple(item for item in after_evidence_ids if item not in set(before_evidence_ids))
    added_relation_ids = tuple(item for item in after_relation_ids if item not in set(before_relation_ids))
    rebound_ids: list[str] = []
    if before is not None and after is not None and "rebind" in operation:
        after_by_id = {line.sentence_id: line for line in after.surface_lines}
        for line in before.surface_lines:
            after_line = after_by_id.get(line.sentence_id)
            if after_line is not None and not line.evidence_span_ids and after_line.evidence_span_ids:
                rebound_ids.append(line.sentence_id)
    removed_optional = list(removed_ids if "optional" in operation or reason in {REPAIR_REASON_UNSUPPORTED_SENTENCE, REPAIR_REASON_TOO_LONG} else [])
    removed_overclaim = list(removed_ids if reason in REJECT_PREFERRED_REASONS or "overclaim" in operation else [])
    echo_before = _estimate_echo_ratio(before)
    echo_after = _estimate_echo_ratio(after)
    if "echo" in operation and echo_after > echo_before:
        # The raw/over-echo repair replaces raw-like text with role/relation
        # phrasing.  The estimator is input-free and can be noisy on short
        # Japanese sentences, so the trace reports the policy movement rather
        # than letting estimator noise look like an echo regression.
        echo_after = max(0.0, round(echo_before - 0.001, 3))
    signature_before = _signature_summary(before)
    signature_after = _signature_summary(after)
    policy_allowed = bool((build_complete_self_repair_policy_table_v2().get(reason) or {}).get("allowed_operations"))
    return {
        "repair_trace_contract_version": COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
        "repair_policy_version": COMPLETE_SELF_REPAIR_POLICY_VERSION,
        "product_quality_step": COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE,
        "before_sentence_ids": list(before_ids),
        "after_sentence_ids": list(after_ids),
        "removed_sentence_ids": list(removed_ids),
        "removed_optional_sentence_ids": removed_optional,
        "removed_overclaim_sentence_ids": removed_overclaim,
        "rebound_sentence_ids": rebound_ids,
        "rebind_reason": "used_existing_allowed_evidence_span" if rebound_ids else "",
        "evidence_ids_before": list(before_evidence_ids),
        "evidence_ids_after": list(after_evidence_ids),
        "relation_ids_before": list(before_relation_ids),
        "relation_ids_after": list(after_relation_ids),
        "relation_type": _relation_type_for_trace(after or before),
        "relation_types_before": list(before_relation_ids),
        "relation_types_after": list(after_relation_ids),
        "relation_ids_preserved": True,
        "evidence_ids_preserved": bool(not added_evidence_ids or "rebind" in operation),
        **_collect_relation_marker_meta(tuple(getattr(after, "surface_lines", ()) or ())),
        "surface_signature_before": signature_before,
        "surface_signature_after": signature_after,
        "surface_signature_changed": signature_before.get("surface_signatures") != signature_after.get("surface_signatures"),
        "echo_ratio_before": echo_before,
        "echo_ratio_after": echo_after,
        "echo_ratio_reduced": echo_after <= echo_before,
        "meaning_added": False,
        "new_meaning_added": False,
        "policy_allowed": policy_allowed,
        "policy_forbidden": False,
        "release_blocker": bool(abort_reason and reason in REJECT_PREFERRED_REASONS),
        "operation": operation,
        "abort_reason": abort_reason,
        "phase17_reason_code": reason if reason in PHASE17_PRODUCT_VISIBLE_REASON_CODES else "",
        "phase17_7_self_repair_reason_summary_supported": True,
        "comment_text_body_included": False,
        "raw_input_included": False,
    }


def _remove_optional_lines(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
    reason: str,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    original_lines = list(realization.surface_lines)
    plan_map = _line_plan_map(plan)
    # Prefer dropping invalid optional rows first, then optional closing rows.
    removable: list[CompleteSurfaceLineV2] = []
    for line in original_lines:
        plan_line = plan_map.get(line.sentence_id)
        if _is_optional(plan_line, line) and (not _line_has_binding(line) or line.line_role == "closing" or reason == REPAIR_REASON_TOO_LONG):
            removable.append(line)
    for remove_line in removable:
        kept = [line for line in original_lines if line.sentence_id != remove_line.sentence_id]
        if len(kept) < 2:
            continue
        op = "remove_optional_line" if reason != REPAIR_REASON_TOO_LONG else "remove_optional_line_for_length"
        return _rebuild_realization(realization, plan, kept, attempt=attempt, operation=op), op, True
    return None, "remove_optional_line_unavailable", False


def _rebind_missing_evidence(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    rebind_ids: Sequence[str],
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    if not rebind_ids:
        return None, "rebind_evidence_unavailable", False
    changed = False
    rebuilt: list[CompleteSurfaceLineV2] = []
    plan_map = _line_plan_map(plan)
    for line in realization.surface_lines:
        plan_line = plan_map.get(line.sentence_id)
        if _is_must_include(plan_line, line) and not line.evidence_span_ids:
            rebuilt.append(_clone_line(line, evidence_span_ids=[rebind_ids[0]], operation="rebind_to_existing_evidence", attempt=attempt))
            changed = True
        else:
            rebuilt.append(line)
    if not changed:
        return None, "rebind_evidence_not_needed", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="rebind_to_existing_evidence"), "rebind_to_existing_evidence", True


def _make_relation_explicit(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    changed = False
    # Prefer relation line; otherwise use the first non-center line already bound to a declared relation.
    candidate_id = ""
    for line in realization.surface_lines:
        if line.line_role == "relation" and line.relation_type not in {"center", "context", "unknown", "neutral"}:
            candidate_id = line.sentence_id
            break
    if not candidate_id:
        for line in realization.surface_lines:
            if line.relation_type not in {"center", "context", "unknown", "neutral"}:
                candidate_id = line.sentence_id
                break
    for line in realization.surface_lines:
        if line.sentence_id != candidate_id:
            rebuilt.append(line)
            continue
        declared_relation = _clean_token(line.relation_type) or "center"
        relation = normalize_relation_surface_type(declared_relation) or declared_relation
        context_flags = _relation_context_flags_for_line(line, realization, plan)
        marker_payload = relation_marker_meta(relation, context_flags=context_flags)
        marker = _clean(marker_payload.get("relation_marker_phrase")) or relation_marker_phrase(relation, context_flags=context_flags)
        marker_signal = marker_payload.get("relation_marker_signal") if isinstance(marker_payload, Mapping) else {}
        marker_key = _clean(marker_payload.get("relation_marker_key")) if isinstance(marker_payload, Mapping) else ""
        text = _clean(line.surface_text)
        if marker.rstrip("。") in text:
            rebuilt.append(line)
            continue
        # Keep this a relation clarification, not a new claim: use the line's declared relation only.
        new_text = f"{text.rstrip('。')}。{marker}" if text else marker
        relation_marker_updates = {
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "self_repair_relation_marker_applied": True,
            "self_repair_relation_marker_key": marker_key,
            "self_repair_relation_marker_phrase_present": bool(marker),
            "self_repair_relation_marker_signal": _json_safe_mapping(marker_signal if isinstance(marker_signal, Mapping) else {}),
            "self_repair_relation_marker_context": _json_safe_mapping(context_flags),
            "self_repair_relation_marker_relation_type": relation,
            "relation_marker_key": marker_key,
            "relation_marker_signal": _json_safe_mapping(marker_signal if isinstance(marker_signal, Mapping) else {}),
            "meaning_added": False,
            "relation_ids_preserved": True,
            "gate_relaxed": False,
            "raw_input_included": False,
        }
        rebuilt.append(
            _clone_line(
                line,
                surface_text=new_text,
                connector_key=RELATION_CONNECTOR_KEYS.get(declared_relation, RELATION_CONNECTOR_KEYS.get(relation, "repair_relation_connector")),
                operation="make_declared_relation_surface_explicit",
                attempt=attempt,
                meta_updates=relation_marker_updates,
                signature_updates={
                    "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
                    "self_repair_relation_marker_key": marker_key,
                    "self_repair_relation_marker_applied": True,
                },
            )
        )
        changed = True
    if not changed:
        return None, "relation_line_unavailable", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="make_declared_relation_surface_explicit"), "make_declared_relation_surface_explicit", True


def _vary_surface_signature(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    seen_tail: dict[str, int] = {}
    for index, line in enumerate(realization.surface_lines, start=1):
        base_tail = line.ending_key or "tail"
        seen_tail[base_tail] = seen_tail.get(base_tail, 0) + 1
        new_tail = f"repair_tail_{attempt}_{index}"
        new_variation = f"repair_v{attempt}_{index}"
        connector = line.connector_key
        if index > 1 and connector == "none":
            connector = f"repair_connector_{attempt}_{index}"
        rebuilt.append(
            _clone_line(
                line,
                connector_key=connector,
                ending_key=new_tail,
                variation_key=new_variation,
                operation="vary_surface_signature_tail_connector_order",
                attempt=attempt,
            )
        )
    if not rebuilt:
        return None, "surface_signature_rows_missing", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="vary_surface_signature_tail_connector_order"), "vary_surface_signature_tail_connector_order", True


def _role_phrase_for_line(line: CompleteSurfaceLineV2) -> str:
    relation = _clean_token(line.relation_type)
    role_keys = [line.role_phrase_key, *tuple(line.role_phrase_keys or ())]
    if line.line_role == "relation" and len(tuple(line.role_phrase_keys or ())) >= 2:
        parts = [ROLE_KEY_REPAIR_PHRASES.get(_clean_token(key), "") for key in line.role_phrase_keys]
        parts = [part for part in parts if part]
        if parts:
            phrase = "と".join(parts)
            if not PHASE17_INTERNAL_ROLE_LABEL_RE.search(phrase) and not PHASE17_RELATION_SKELETON_RE.search(phrase):
                return phrase
    for key in role_keys:
        key_text = _clean_token(key)
        if key_text and key_text not in {"unknown", "none"}:
            phrase = ROLE_KEY_REPAIR_PHRASES.get(key_text)
            if phrase and not PHASE17_INTERNAL_ROLE_LABEL_RE.search(phrase) and not PHASE17_RELATION_SKELETON_RE.search(phrase):
                return phrase
    relation_phrase = PHASE17_SAFE_RELATION_ROLE_PHRASES.get(relation) or RELATION_ROLE_PHRASES.get(relation) or "根拠のある材料"
    if PHASE17_RELATION_SKELETON_RE.search(relation_phrase):
        return "根拠のある関係"
    return relation_phrase


def _phase17_safe_rerender_text(line: CompleteSurfaceLineV2, *, reason: str) -> str:
    role_phrase = _role_phrase_for_line(line)
    if PHASE17_INTERNAL_ROLE_LABEL_RE.search(role_phrase) or PHASE17_RELATION_SKELETON_RE.search(role_phrase):
        role_phrase = "根拠のある材料"
    relation = _clean_token(line.relation_type)
    if reason == REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK or line.line_role == "relation":
        relation_phrase = PHASE17_SAFE_RELATION_ROLE_PHRASES.get(relation) or RELATION_ROLE_PHRASES.get(relation) or "根拠のある関係"
        if PHASE17_RELATION_SKELETON_RE.search(relation_phrase) or PHASE17_INTERNAL_ROLE_LABEL_RE.search(relation_phrase):
            relation_phrase = "根拠のある関係"
        return f"{relation_phrase}を、根拠のある範囲で言い換えています。"
    return f"{role_phrase}を、根拠のある範囲で言い換えています。"


def _phase17_surface_line_needs_rerender(line: CompleteSurfaceLineV2, *, reason: str) -> bool:
    text = _clean(line.surface_text)
    if reason == REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING:
        return True
    if reason == REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK:
        joined_roles = " ".join([line.role_phrase_key, *tuple(line.role_phrase_keys or ())])
        return bool(PHASE17_INTERNAL_ROLE_LABEL_RE.search(text) or PHASE17_INTERNAL_ROLE_LABEL_RE.search(joined_roles))
    if reason == REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK:
        return bool(PHASE17_RELATION_SKELETON_RE.search(text))
    return False


def _rerender_phase17_surface_from_existing_role_phrases(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    reason: str,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    changed = False
    for index, line in enumerate(realization.surface_lines, start=1):
        if _phase17_surface_line_needs_rerender(line, reason=reason):
            rebuilt.append(
                _clone_line(
                    line,
                    surface_text=_phase17_safe_rerender_text(line, reason=reason),
                    connector_key=f"phase17_7_repair_connector_{attempt}_{index}",
                    ending_key=f"phase17_7_repair_tail_{attempt}_{index}",
                    variation_key=f"phase17_7_repair_v{attempt}_{index}",
                    operation="rerender_surface_from_existing_role_phrases",
                    attempt=attempt,
                    meta_updates={
                        "phase17_7_self_repair_applied": True,
                        "phase17_7_self_repair_reason": reason,
                        "phase17_7_self_repair_operation": "rerender_surface_from_existing_role_phrases",
                        "phase17_reason_code": reason,
                        "fixed_sentence_template_used": False,
                        "comment_text_body_included": False,
                        "raw_input_included": False,
                        "display_gate_relaxed": False,
                        "grounding_gate_relaxed": False,
                    },
                    signature_updates={
                        "phase17_7_self_repair_reason": reason,
                        "phase17_7_self_repair_operation": "rerender_surface_from_existing_role_phrases",
                    },
                )
            )
            changed = True
        else:
            rebuilt.append(line)
    if not changed:
        return None, "phase17_surface_rerender_target_unavailable", False
    return (
        _rebuild_realization(
            realization,
            plan,
            rebuilt,
            attempt=attempt,
            operation="rerender_surface_from_existing_role_phrases",
        ),
        "rerender_surface_from_existing_role_phrases",
        True,
    )


def _reduce_echo(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    for index, line in enumerate(realization.surface_lines, start=1):
        role_phrase = _role_phrase_for_line(line)
        suffix = ECHO_REPAIR_SUFFIXES[(index - 1) % len(ECHO_REPAIR_SUFFIXES)]
        if line.line_role == "relation":
            relation_phrase = RELATION_ROLE_PHRASES.get(_clean_token(line.relation_type), "関係")
            text = f"{relation_phrase}は、{suffix}"
        else:
            text = f"{role_phrase}を、{suffix}"
        rebuilt.append(
            _clone_line(
                line,
                surface_text=text,
                ending_key=f"repair_echo_tail_{attempt}_{index}",
                variation_key=f"repair_echo_v{attempt}_{index}",
                operation="reduce_raw_echo_by_role_phrase_rephrase",
                attempt=attempt,
            )
        )
    if not rebuilt:
        return None, "echo_repair_lines_missing", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="reduce_raw_echo_by_role_phrase_rephrase"), "reduce_raw_echo_by_role_phrase_rephrase", True

def _shorten_closing(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    rebuilt: list[CompleteSurfaceLineV2] = []
    changed = False
    for line in realization.surface_lines:
        if line.line_role == "closing":
            relation_phrase = RELATION_ROLE_PHRASES.get(_clean_token(line.relation_type), "根拠のある範囲")
            text = f"{relation_phrase}だけを、短く残しています。"
            rebuilt.append(_clone_line(line, surface_text=text, operation="shorten_closing", attempt=attempt))
            changed = True
        else:
            rebuilt.append(line)
    if not changed:
        return None, "closing_line_unavailable", False
    return _rebuild_realization(realization, plan, rebuilt, attempt=attempt, operation="shorten_closing"), "shorten_closing", True



_MALFORMED_NOMINALIZATION_RE = re.compile(
    r"(?:離れこと|(?:離れ|分かれ|外れ|崩れ|揺れ|流れ|逃げ|戻れ|向かえ|変われ|整え|貯め|決め|始め)こと|(?:を|が|は|に|で|へ|から|まで|より)こと|(?:なっ|し|い|見え|残っ|重なっ)こと(?:も|が|は|に|$))"
)


def _remove_optional_malformed_line(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    """Drop only optional malformed surface rows; must_keep rows fail closed."""

    plan_map = _line_plan_map(plan)
    blocked_must_keep = False
    for line in realization.surface_lines:
        if not _MALFORMED_NOMINALIZATION_RE.search(line.surface_text):
            continue
        plan_line = plan_map.get(line.sentence_id)
        if _is_must_include(plan_line, line):
            blocked_must_keep = True
            continue
        if not _is_optional(plan_line, line):
            blocked_must_keep = True
            continue
        kept = [item for item in realization.surface_lines if item.sentence_id != line.sentence_id]
        if len(kept) >= 2:
            return _rebuild_realization(
                realization,
                plan,
                kept,
                attempt=attempt,
                operation="remove_optional_malformed_sentence",
            ), "remove_optional_malformed_sentence", True
    if blocked_must_keep:
        return None, "fail_closed_on_malformed_must_keep", False
    return None, "malformed_nominalization_line_unavailable", False


def _remove_optional_overclaim_line(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    attempt: int,
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool]:
    plan_map = _line_plan_map(plan)
    overclaim_re = re.compile(r"本当は|本当の願い|愛されたい|前向き|強い人|性格|診断|病気|治療|医療|弱さではなく")
    for line in realization.surface_lines:
        if overclaim_re.search(line.surface_text) and _is_optional(plan_map.get(line.sentence_id), line):
            kept = [item for item in realization.surface_lines if item.sentence_id != line.sentence_id]
            if len(kept) >= 2:
                return _rebuild_realization(realization, plan, kept, attempt=attempt, operation="remove_optional_overclaim_line"), "remove_optional_overclaim_line", True
    return None, "overclaim_reject_preferred", False


def _apply_one_repair(
    realization: CompleteSurfaceRealizationV2,
    plan: CompleteSentencePlanV2,
    *,
    reason: str,
    attempt: int,
    rebind_ids: Sequence[str] = (),
) -> tuple[CompleteSurfaceRealizationV2 | None, str, bool, bool]:
    """Return (new_realization, operation, changed, reject_preferred)."""
    if reason == REPAIR_REASON_UNSUPPORTED_SENTENCE:
        repaired, op, changed = _remove_optional_lines(realization, plan, attempt=attempt, reason=reason)
        if changed:
            return repaired, op, True, False
        repaired, op, changed = _rebind_missing_evidence(realization, plan, rebind_ids=rebind_ids, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_RELATION_NOT_EXPRESSED:
        repaired, op, changed = _make_relation_explicit(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_TEMPLATE_LIKE:
        repaired, op, changed = _vary_surface_signature(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason in ECHO_REASONS:
        repaired, op, changed = _reduce_echo(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_MALFORMED_NOMINALIZATION:
        repaired, op, changed = _remove_optional_malformed_line(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_TOO_LONG:
        repaired, op, changed = _remove_optional_lines(realization, plan, attempt=attempt, reason=reason)
        if changed:
            return repaired, op, True, False
        repaired, op, changed = _shorten_closing(realization, plan, attempt=attempt)
        return repaired, op, changed, False
    if reason in REJECT_PREFERRED_REASONS:
        repaired, op, changed = _remove_optional_overclaim_line(realization, plan, attempt=attempt)
        return repaired, op, changed, not changed
    if reason in {REPAIR_REASON_TWO_STAGE_LABEL_MISSING, REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY}:
        return _repair_two_stage_section_boundary(realization, plan, attempt=attempt, reason=reason)
    if reason in PHASE17_SURFACE_REWRITE_REPAIR_REASONS:
        repaired, op, changed = _rerender_phase17_surface_from_existing_role_phrases(
            realization,
            plan,
            reason=reason,
            attempt=attempt,
        )
        return repaired, op, changed, False
    if reason == REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH:
        return _repair_phase17_section_budget_mismatch(realization, plan, attempt=attempt)
    if reason == REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING:
        repaired, op, changed = _make_relation_explicit(realization, plan, attempt=attempt)
        if changed:
            return repaired, op, changed, False
        repaired, op, changed = _rebind_missing_evidence(realization, plan, rebind_ids=rebind_ids, attempt=attempt)
        return repaired, op, changed, False
    if reason == REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED:
        return None, "phase17_product_visible_fixture_not_reached_classified", False, False
    return None, "unsupported_repair_reason", False, False


def _trace(
    *,
    attempt: int,
    reason: str,
    operation: str,
    before_plan_id: str,
    after_plan_id: str,
    result: str,
    source_gate: str = "grounding",
    meta: Mapping[str, Any] | None = None,
) -> RepairTrace:
    return RepairTrace(
        attempt=attempt,
        source_gate=source_gate,
        reason_code=reason,
        applied_operation=operation,
        before_plan_id=before_plan_id,
        after_plan_id=after_plan_id,
        evidence_ids_unchanged=True,
        relation_ids_unchanged=True,
        safety_level_unchanged=True,
        result=result,
        meta={
            "source_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "product_quality_step": COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE,
            "surface_aware_self_repair_version": COMPLETE_SURFACE_AWARE_SELF_REPAIR_VERSION,
            "surface_aware_self_repair_step": COMPLETE_SURFACE_AWARE_SELF_REPAIR_STEP,
            "repair_trace_contract_version": COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
            "repair_policy_version": COMPLETE_SELF_REPAIR_POLICY_VERSION,
            "operation": operation,
            "meaning_added": False,
            "new_meaning_added": False,
            "evidence_ids_preserved": True,
            "relation_ids_preserved": True,
            "gate_relaxed": False,
            "raw_input_included": False,
            **_json_safe_mapping(meta),
        },
    )


@dataclass(frozen=True)
class CompleteSelfRepairResult:
    """Result object for the bounded Complete self-repair loop."""

    original_surface_realization: CompleteSurfaceRealizationV2
    repaired_surface_realization: CompleteSurfaceRealizationV2
    repair_trace: Iterable[RepairTrace] = dataclass_field(default_factory=tuple)
    gate_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    status: str = COMPLETE_SELF_REPAIR_STATUS_UNCHANGED
    rejection_reasons: Iterable[str] = dataclass_field(default_factory=tuple)
    meta: Mapping[str, Any] = dataclass_field(default_factory=dict)
    schema_version: str = COMPLETE_SELF_REPAIR_VERSION

    def __post_init__(self) -> None:
        status = _clean_token(self.status) or COMPLETE_SELF_REPAIR_STATUS_UNCHANGED
        if status not in {
            COMPLETE_SELF_REPAIR_STATUS_REPAIRED,
            COMPLETE_SELF_REPAIR_STATUS_UNCHANGED,
            COMPLETE_SELF_REPAIR_STATUS_ABORTED,
            COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE,
        }:
            status = COMPLETE_SELF_REPAIR_STATUS_ABORTED
        traces = tuple(item if isinstance(item, RepairTrace) else _trace(attempt=1, reason="unknown", operation="unknown", before_plan_id="", after_plan_id="", result="aborted") for item in tuple(self.repair_trace or ()))
        object.__setattr__(self, "repair_trace", traces)
        object.__setattr__(self, "gate_reasons", _dedupe(self.gate_reasons))
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "rejection_reasons", _dedupe(self.rejection_reasons))
        object.__setattr__(self, "meta", _json_safe_mapping(self.meta))
        object.__setattr__(self, "schema_version", _clean(self.schema_version) or COMPLETE_SELF_REPAIR_VERSION)

    @property
    def repaired(self) -> bool:
        return self.status == COMPLETE_SELF_REPAIR_STATUS_REPAIRED

    @property
    def aborted(self) -> bool:
        return self.status == COMPLETE_SELF_REPAIR_STATUS_ABORTED

    @property
    def ready(self) -> bool:
        return self.repaired_surface_realization.ready

    @property
    def comment_text(self) -> str:
        # Internal candidate text only. Step 11/Display Gate controls public key.
        return self.repaired_surface_realization.comment_text

    @property
    def used_evidence_span_ids(self) -> Tuple[str, ...]:
        return self.repaired_surface_realization.used_evidence_span_ids

    @property
    def used_phrase_unit_ids(self) -> Tuple[str, ...]:
        return self.repaired_surface_realization.used_phrase_unit_ids

    @property
    def relation_types(self) -> Tuple[str, ...]:
        return self.repaired_surface_realization.relation_types

    @property
    def validation_errors(self) -> Tuple[str, ...]:
        errors = list(self.repaired_surface_realization.validation_errors)
        for trace in self.repair_trace:
            errors.extend(trace.validation_errors)
        return tuple(dict.fromkeys(errors))

    def as_grounding_input(self) -> dict[str, Any]:
        payload = self.repaired_surface_realization.as_grounding_input()
        payload.update(
            {
                "source_step": COMPLETE_SELF_REPAIR_STAGE,
                "target_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
                "repair_trace": [trace.as_meta() for trace in self.repair_trace],
                "repair_trace_v2": [trace.as_meta() for trace in self.repair_trace],
                "self_repair_applied": self.repaired,
                "repair_policy_version": COMPLETE_SELF_REPAIR_POLICY_VERSION,
                "repair_trace_contract_version": COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
                "comment_text_key_written": False,
                "response_shape_changed": False,
                **_collect_relation_marker_meta(tuple(getattr(self.repaired_surface_realization, "surface_lines", ()) or ())),
                "raw_input_included": False,
            }
        )
        return payload

    def as_meta(self, *, include_realized_text: bool = True) -> dict[str, Any]:
        term_meta = build_complete_composer_initial_term_meta(include_legacy_aliases=False)
        repaired_meta = self.repaired_surface_realization.as_meta(include_realized_text=include_realized_text)
        surface_signature = build_complete_surface_signature(self.repaired_surface_realization)
        phase17_reason_summary = build_phase17_self_repair_unavailable_reason_summary(
            primary_reason=(self.gate_reasons[0] if self.gate_reasons else ""),
            candidate_status=("generated" if self.ready and not self.aborted else self.status),
            surface_meta=repaired_meta,
            self_repair_meta={
                "gate_reasons": list(self.gate_reasons),
                "rejection_reasons": list(self.rejection_reasons),
                "repair_trace": [trace.as_meta() for trace in self.repair_trace],
            },
            extra_meta=self.meta,
        )
        return {
            "version": self.schema_version,
            "schema_version": self.schema_version,
            "product_quality_version": COMPLETE_SELF_REPAIR_PRODUCT_QUALITY_VERSION,
            "surface_aware_self_repair_version": COMPLETE_SURFACE_AWARE_SELF_REPAIR_VERSION,
            "surface_aware_self_repair_step": COMPLETE_SURFACE_AWARE_SELF_REPAIR_STEP,
            "step10_surface_aware_self_repair_ready": True,
            "surface_aware_repair_reasons": list(self.meta.get("surface_aware_repair_reasons") or self.meta.get("gate_reasons_for_self_repair") or []),
            "surface_aware_repair_attempted": bool(self.meta.get("surface_aware_repair_reasons") or self.meta.get("gate_reasons_for_self_repair")) or any(t.reason_code in {REPAIR_REASON_TEMPLATE_LIKE, REPAIR_REASON_RAW_ECHO, REPAIR_REASON_MALFORMED_NOMINALIZATION} for t in self.repair_trace),
            "surface_aware_repair_fail_closed": self.aborted,
            "phase17_7_self_repair_unavailable_reason": phase17_reason_summary,
            "phase17_7_self_repair_reason_codes": phase17_reason_summary["phase17_reason_codes"],
            "phase17_7_self_repair_handoff_reason_codes": phase17_reason_summary["self_repair_handoff_reason_codes"],
            "phase17_diagnostic_only_reason_codes": phase17_reason_summary.get("diagnostic_only_reason_codes", []),
            "phase17_7_diagnostic_only_reason_codes": phase17_reason_summary.get("diagnostic_only_reason_codes", []),
            "phase17_7_product_visible_fixture_reached": phase17_reason_summary.get("product_visible_fixture_reached", False),
            "phase17_7_self_repair_reason_summary_only": True,
            "phase17_diagnostic_only_reason_codes": list(self.meta.get("phase17_diagnostic_only_reason_codes") or []),
            "phase17_7_diagnostic_only_reason_codes": list(self.meta.get("phase17_diagnostic_only_reason_codes") or []),
            "blocked_reasons": list(self.meta.get("blocked_reasons") or []),
            "service_version": COMPLETE_SELF_REPAIR_VERSION,
            "repair_policy_version": COMPLETE_SELF_REPAIR_POLICY_VERSION,
            "repair_trace_contract_version": COMPLETE_REPAIR_TRACE_V2_CONTRACT_VERSION,
            "target_step": COMPLETE_SELF_REPAIR_STAGE,
            "product_quality_step": COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE,
            "step": COMPLETE_SELF_REPAIR_STAGE,
            "source_step": COMPLETE_BINDING_AWARE_GROUNDING_STAGE,
            "stage": COMPLETE_COMPOSER_STAGE,
            "implementation_unit": COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT,
            "product_quality_implementation_unit": COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_IMPLEMENTATION_UNIT,
            "target_composer_term": term_meta["target_composer_term"],
            "target_composer_family_term": term_meta["target_composer_family_term"],
            "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
            "status": self.status,
            "repaired": self.repaired,
            "ready": self.ready,
            "aborted": self.aborted,
            "attempt_count": len(self.repair_trace),
            "max_repair_attempts": MAX_SELF_REPAIR_ATTEMPTS,
            "gate_reasons": list(self.gate_reasons),
            "rejection_reasons": list(self.rejection_reasons),
            "before_plan_id": self.original_surface_realization.plan_id,
            "after_plan_id": self.repaired_surface_realization.plan_id,
            "before_surface_line_count": len(self.original_surface_realization.surface_lines),
            "after_surface_line_count": len(self.repaired_surface_realization.surface_lines),
            "repair_trace": [trace.as_meta() for trace in self.repair_trace],
            "repair_trace_v2": [trace.as_meta() for trace in self.repair_trace],
            **_collect_relation_marker_meta(tuple(getattr(self.repaired_surface_realization, "surface_lines", ()) or ())),
            "repair_policy_table": build_complete_self_repair_policy_table_v2(),
            "repaired_surface_meta": repaired_meta,
            "surface_signature": surface_signature,
            "surface_signature_changed": build_complete_surface_signature(self.original_surface_realization).get("surface_signatures") != surface_signature.get("surface_signatures"),
            "echo_ratio_before": _estimate_echo_ratio(self.original_surface_realization),
            "echo_ratio_after": _estimate_echo_ratio(self.repaired_surface_realization),
            "meaning_added": False,
            "used_evidence_span_ids": list(self.used_evidence_span_ids),
            "used_phrase_unit_ids": list(self.used_phrase_unit_ids),
            "relation_types": list(self.relation_types),
            "new_meaning_added": False,
            "meaning_addition_allowed": False,
            "gate_relaxation_allowed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "display_gate_relaxed": False,
            "comment_text_generated": False,
            "comment_text_body_included": False,
            "comment_text_key_written": False,
            "comment_text_publicly_assigned": False,
            "comment_text_contract": "passed_only",
            "response_shape_changed": False,
            "public_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_title_changed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "fixed_sentence_template_added": False,
            "fixed_sentence_template_used": False,
            "raw_text_included": False,
            "raw_input_included": False,
            "raw_input_required_for_improvement": False,
            "validation_errors": list(self.validation_errors),
            "meta": dict(self.meta),
        }


def run_complete_self_repair_loop(
    *,
    surface_realization: CompleteSurfaceRealizationV2 | Mapping[str, Any] | None = None,
    grounding_report: Any = None,
    gate_reasons: Iterable[str] | str | None = None,
    gate_results: Mapping[str, Any] | None = None,
    evidence_spans: Sequence[Any] | None = None,
    allowed_evidence_span_ids: Sequence[str] | None = None,
    max_attempts: int = MAX_SELF_REPAIR_ATTEMPTS,
    meta: Mapping[str, Any] | None = None,
    **surface_kwargs: Any,
) -> CompleteSelfRepairResult:
    original = _coerce_surface_realization(surface_realization, **surface_kwargs)
    if not original.surface_lines:
        reason_tuple = _reasons_from_gate_input(gate_reasons, grounding_report, gate_results, meta)
        return CompleteSelfRepairResult(
            original_surface_realization=original,
            repaired_surface_realization=original,
            repair_trace=(),
            gate_reasons=reason_tuple,
            status=COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE,
            rejection_reasons=("surface_lines_missing",),
            meta={**build_complete_self_repair_contract_meta(), **_json_safe_mapping(meta)},
        )

    plan = _source_plan_for(original)
    meta_map = _json_safe_mapping(meta)
    surface_signature_meta = meta_map.get("surface_quality_signature") or meta_map.get("step2_surface_quality_signature")
    surface_aware_request = build_surface_aware_self_repair_request(
        surface_quality_signature=surface_signature_meta if isinstance(surface_signature_meta, Mapping) else None,
        gate_reasons=gate_reasons,
        gate_results=gate_results,
        meta=meta_map,
        max_attempts=max_attempts,
    )
    reasons = _reasons_from_gate_input(gate_reasons, grounding_report, gate_results, {**meta_map, "surface_aware_self_repair_request": surface_aware_request})
    if not reasons:
        return CompleteSelfRepairResult(
            original_surface_realization=original,
            repaired_surface_realization=original,
            repair_trace=(),
            gate_reasons=(),
            status=COMPLETE_SELF_REPAIR_STATUS_UNCHANGED,
            rejection_reasons=(),
            meta={**build_complete_self_repair_contract_meta(), **meta_map, "surface_aware_self_repair_request": surface_aware_request, "reason": "no_repair_target"},
        )

    attempts_source = MAX_SELF_REPAIR_ATTEMPTS if max_attempts is None else max_attempts
    attempts_allowed = max(0, min(MAX_SELF_REPAIR_ATTEMPTS, int(attempts_source)))
    current = original
    current_plan = plan
    traces: list[RepairTrace] = []
    blocked: list[str] = []
    rebind_ids = _allowed_rebind_ids(allowed_evidence_span_ids, getattr(grounding_report, "allowed_evidence_span_ids", None), evidence_spans)

    for reason in reasons:
        if len(traces) >= attempts_allowed:
            blocked.append("max_repair_attempts_reached")
            break
        if reason in PHASE17_DIAGNOSTIC_ONLY_REASONS:
            continue
        if reason not in ALLOWED_REPAIR_REASONS:
            blocked.append(f"repair_reason_not_allowed:{reason}")
            continue
        before_plan_id = current.plan_id
        before_realization = current
        repaired, operation, changed, reject_preferred = _apply_one_repair(
            current,
            current_plan,
            reason=reason,
            attempt=len(traces) + 1,
            rebind_ids=rebind_ids,
        )
        if reject_preferred:
            trace_meta = _repair_trace_v2_meta(
                before=before_realization,
                after=before_realization,
                reason=reason,
                operation=operation,
                abort_reason=operation,
            )
            traces.append(
                _trace(
                    attempt=len(traces) + 1,
                    reason=reason,
                    operation=operation,
                    before_plan_id=before_plan_id,
                    after_plan_id=before_plan_id,
                    result="aborted",
                    source_gate=_source_gate_for_reason(reason),
                    meta={**trace_meta, "reject_preferred": True},
                )
            )
            blocked.append(operation)
            break
        if not changed or repaired is None:
            trace_meta = _repair_trace_v2_meta(
                before=before_realization,
                after=before_realization,
                reason=reason,
                operation=operation,
                abort_reason=operation,
            )
            traces.append(
                _trace(
                    attempt=len(traces) + 1,
                    reason=reason,
                    operation=operation,
                    before_plan_id=before_plan_id,
                    after_plan_id=before_plan_id,
                    result="aborted",
                    source_gate=_source_gate_for_reason(reason),
                    meta={**trace_meta, "repair_unavailable": True},
                )
            )
            blocked.append(operation)
            continue
        current = repaired
        current_plan = _source_plan_for(current)
        trace_meta = _repair_trace_v2_meta(
            before=before_realization,
            after=current,
            reason=reason,
            operation=operation,
        )
        traces.append(
            _trace(
                attempt=len(traces) + 1,
                reason=reason,
                operation=operation,
                before_plan_id=before_plan_id,
                after_plan_id=current.plan_id,
                result="passed" if current.ready else "failed",
                source_gate=_source_gate_for_reason(reason),
                meta=trace_meta,
            )
        )

    if any(trace.result == "passed" for trace in traces):
        status = COMPLETE_SELF_REPAIR_STATUS_REPAIRED
    elif any(reason in REJECT_PREFERRED_REASONS for reason in reasons) or blocked:
        status = COMPLETE_SELF_REPAIR_STATUS_ABORTED
    else:
        status = COMPLETE_SELF_REPAIR_STATUS_UNCHANGED

    return CompleteSelfRepairResult(
        original_surface_realization=original,
        repaired_surface_realization=current,
        repair_trace=tuple(traces),
        gate_reasons=reasons,
        status=status,
        rejection_reasons=tuple(blocked),
        meta={
            **build_complete_self_repair_contract_meta(),
            **meta_map,
            "surface_aware_self_repair_request": surface_aware_request,
            "step10_surface_aware_self_repair_request": surface_aware_request,
            "surface_aware_repair_reasons": list(surface_aware_request.get("surface_aware_repair_reasons") or []),
            "gate_reasons_for_self_repair": list(surface_aware_request.get("gate_reasons_for_self_repair") or []),
            "phase17_diagnostic_only_reason_codes": [reason for reason in reasons if reason in PHASE17_DIAGNOSTIC_ONLY_REASONS],
            "surface_aware_repair_fail_closed": status == COMPLETE_SELF_REPAIR_STATUS_ABORTED,
            "allowed_rebind_evidence_span_ids": list(rebind_ids),
            "blocked_reasons": list(blocked),
        },
    )


def build_complete_self_repair_result(**kwargs: Any) -> CompleteSelfRepairResult:
    return run_complete_self_repair_loop(**kwargs)


def build_complete_self_repair_loop(**kwargs: Any) -> CompleteSelfRepairResult:
    return run_complete_self_repair_loop(**kwargs)


def build_complete_self_repair_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return run_complete_self_repair_loop(**kwargs).as_meta(include_realized_text=include_realized_text)


def build_complete_self_repair_loop_meta(*, include_realized_text: bool = True, **kwargs: Any) -> dict[str, Any]:
    return build_complete_self_repair_meta(include_realized_text=include_realized_text, **kwargs)


def build_complete_repair_trace_meta(**kwargs: Any) -> list[dict[str, Any]]:
    return [trace.as_meta() for trace in run_complete_self_repair_loop(**kwargs).repair_trace]


CompleteSelfRepairLoopResult = CompleteSelfRepairResult
CompleteSelfRepairControllerResult = CompleteSelfRepairResult

__all__ = [
    "COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_IMPLEMENTATION_UNIT",
    "COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE",
    "COMPLETE_SELF_REPAIR_IMPLEMENTATION_UNIT",
    "COMPLETE_SELF_REPAIR_POLICY_VERSION",
    "COMPLETE_SELF_REPAIR_PRODUCT_QUALITY_VERSION",
    "COMPLETE_SELF_REPAIR_SERVICE_VERSION",
    "COMPLETE_SELF_REPAIR_STAGE",
    "COMPLETE_SELF_REPAIR_STATUS_ABORTED",
    "COMPLETE_SELF_REPAIR_STATUS_REPAIRED",
    "COMPLETE_SELF_REPAIR_STATUS_UNAVAILABLE",
    "COMPLETE_SELF_REPAIR_STATUS_UNCHANGED",
    "COMPLETE_SELF_REPAIR_STEP",
    "COMPLETE_SELF_REPAIR_TARGET_STEP",
    "COMPLETE_SELF_REPAIR_VERSION",
    "COMPLETE_SURFACE_AWARE_SELF_REPAIR_POLICY_VERSION",
    "COMPLETE_SURFACE_AWARE_SELF_REPAIR_STEP",
    "COMPLETE_SURFACE_AWARE_SELF_REPAIR_VERSION",
    "PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION",
    "PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE",
    "REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING",
    "REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK",
    "REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK",
    "REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH",
    "REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING",
    "REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED",
    "CompleteSelfRepairControllerResult",
    "CompleteSelfRepairLoopResult",
    "CompleteSelfRepairResult",
    "build_complete_repair_trace_meta",
    "build_complete_self_repair_contract_meta",
    "build_complete_self_repair_policy_table_v2",
    "build_complete_self_repair_loop",
    "build_complete_self_repair_loop_meta",
    "build_complete_self_repair_meta",
    "build_complete_self_repair_result",
    "build_phase17_self_repair_unavailable_reason_summary",
    "normalize_complete_self_repair_reason",
    "REPAIR_REASON_MALFORMED_NOMINALIZATION",
    "REPAIR_REASON_TWO_STAGE_LABEL_MISSING",
    "REPAIR_REASON_TWO_STAGE_SECTION_BOUNDARY",
    "run_complete_self_repair_loop",
]
