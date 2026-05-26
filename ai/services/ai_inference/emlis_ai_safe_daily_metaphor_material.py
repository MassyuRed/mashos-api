# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal safe daily metaphor material for EmlisAI state answers.

Phase 6 materializes the design rule that metaphors are not freely generated
sentences.  The material exposes only analogy family ids, safe daily analogy ids,
selection/suppression reasons, and gate policies.  It does not create
user-facing ``comment_text``, does not add public response keys, does not alter
API routes, DB physical names, or RN display conditions, and does not store raw
input text or completed metaphor sentences.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import copy
import json
import re
from typing import Any, Final

from cocolon_environment_state_output_frame import (
    ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    build_environment_state_output_frame,
)

EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION: Final = (
    "cocolon.emlis_ai_safe_daily_metaphor_material.v1"
)
EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID: Final = "emlis_ai_safe_daily_metaphor_material"
EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE: Final = "Phase6_safe_daily_metaphor_material"
EMLIS_AI_SAFE_DAILY_METAPHOR_INTERNAL_NAME: Final = "EmlisAI安全日常比喩material"

_SPACE_RE: Final = re.compile(r"\s+")
_STRUCTURE_REQUEST_RE: Final = re.compile(
    r"(なぜ|なんで|何で|どういうこと|どうして|同じことになる|同じ状態|構造|理由|仕組み|しくみ|整理したい|何が起き|どんな状態)"
)
_REPEATED_CONFUSION_RE: Final = re.compile(r"((?:なぜ|何故|なんで|何で|どうして|どういうこと).{0,32}(?:また同じ|何度も|何回も|繰り返|くり返|同じ不安|戻)|(?:また同じ|何度も|何回も|繰り返|くり返|同じ不安|戻).{0,32}(?:なぜ|何故|なんで|何で|どうして|どういうこと|理由))" )
_SELF_DENIAL_RE: Final = re.compile(
    r"(自分(?:なんか|など|は|が|を)?[^。！？!?\n]{0,28}(?:嫌い|きらい|ダメ|だめ|駄目|価値がない|価値ない|いらない|最低|クズ|消えたい|死にたい|生きてる意味|生きる意味)|"
    r"(?:私|わたし|俺|僕)(?:なんか|など|は|が)?[^。！？!?\n]{0,28}(?:嫌い|きらい|ダメ|だめ|駄目|価値がない|価値ない|いらない|最低|クズ|消えたい|死にたい)|"
    r"(?:全部|すべて|みんな)(?:自分|私|わたし|俺|僕)が悪い)"
)
_ANGER_RE: Final = re.compile(r"(怒り|怒っ|腹が立|腹立|ムカつ|むかつ|イライラ|いらいら|許せない|理不尽|不公平|納得できない|軽く扱われ)")
_GRIEF_RE: Final = re.compile(r"(悲し|かなしい|寂し|さみし|孤独|喪失|失った|つらい|辛い|苦しい|消えたい|死にたい)")
_STRONG_WORD_RE: Final = re.compile(r"(強い|かなり|すごく|とても|限界|もう無理|耐えられない|消えたい|死にたい)")
_SPECIALIST_CONTEXT_RE: Final = re.compile(r"(医療|病院|薬|診断|法律|法的|裁判|訴訟|弁護士|宗教|信仰|政治|選挙|政党|政策|税務|投資助言)")

_UNCHECKED_ANSWER_RE: Final = re.compile(r"(確認しない|確認できていない|未確認|聞かない|聞けない|決めている|決めつけ|相手の答え|正解を決め)")
_AHEAD_OF_CONFIRMATION_RE: Final = re.compile(r"(先回り|合わせよう|察し|確認せず|聞かず|相手に合わせ)")
_REPETITION_RE: Final = re.compile(r"(また同じ|何度も|繰り返|くり返|同じ不安|戻ってしま|戻る|同じところ)")
_CARRYING_LOAD_RE: Final = re.compile(r"(全部.*一人|一人で.*全部|抱え|背負|荷物|しんどい|疲れ|消耗|限界)")
_AMBIVALENCE_RE: Final = re.compile(r"(迷|決められ|選べ|どちら|片方|このままでいい|方向|どうしたら)")

_DAILY_ANALOGY_REGISTRY: Final = {
    "unchecked_answer_sheet": {
        "safe_daily_analogy_id": "safe_daily_analogy.unchecked_answer_sheet.v1",
        "analogy_family": "unchecked_answer_sheet",
        "structure_ids": ["unconfirmed_area", "state_text_gap", "thought_action_discrepancy"],
        "domain_kind": "daily_learning_or_checking",
        "qa_target": "unconfirmed_answer_boundary_is_visible",
        "surface_role": "state_explanation_only",
        "must_not_read_as": ["person_as_problem", "action_instruction", "target_judgement"],
    },
    "order_before_cooking": {
        "safe_daily_analogy_id": "safe_daily_analogy.order_before_cooking.v1",
        "analogy_family": "order_before_cooking",
        "structure_ids": ["ahead_of_confirmation", "unexpressed_output_stop"],
        "domain_kind": "daily_household_or_ordering",
        "qa_target": "ahead_of_confirmation_structure_is_visible",
        "surface_role": "state_explanation_only",
        "must_not_read_as": ["action_instruction", "relationship_judgement", "target_judgement"],
    },
    "same_step_on_same_path": {
        "safe_daily_analogy_id": "safe_daily_analogy.same_step_on_same_path.v1",
        "analogy_family": "same_step_on_same_path",
        "structure_ids": ["repetition", "continuation_concern"],
        "domain_kind": "daily_movement_or_path",
        "qa_target": "repeated_return_point_is_visible_without_blame",
        "surface_role": "state_explanation_only",
        "must_not_read_as": ["blame", "period_tendency_from_single_record", "action_instruction"],
    },
    "carrying_all_bags_alone": {
        "safe_daily_analogy_id": "safe_daily_analogy.carrying_all_bags_alone.v1",
        "analogy_family": "carrying_all_bags_alone",
        "structure_ids": ["load_accumulation", "pressure_gap"],
        "domain_kind": "daily_load_or_baggage",
        "qa_target": "load_concentration_is_visible_without_prescription",
        "surface_role": "state_explanation_only",
        "must_not_read_as": ["ask_for_help_instruction", "recovery_prescription", "success_claim"],
    },
    "two_bags_selection_load": {
        "safe_daily_analogy_id": "safe_daily_analogy.two_bags_selection_load.v1",
        "analogy_family": "two_bags_selection_load",
        "structure_ids": ["unformed_self_insight", "direction_concern", "ambivalence"],
        "domain_kind": "daily_choice_or_holding",
        "qa_target": "ambivalence_structure_is_visible_without_choice_instruction",
        "surface_role": "state_explanation_only",
        "must_not_read_as": ["choice_instruction", "action_instruction", "personality_claim"],
    },
    "partial_dark_letters_on_page": {
        "safe_daily_analogy_id": "safe_daily_analogy.partial_dark_letters_on_page.v1",
        "analogy_family": "partial_dark_letters_on_page",
        "structure_ids": ["self_denial", "identity_claim_boundary"],
        "domain_kind": "daily_reading_or_page",
        "qa_target": "part_whole_boundary_is_visible_without_over_praise",
        "surface_role": "state_explanation_only",
        "must_not_read_as": ["personality_praise", "absolute_support", "identity_claim_as_fact"],
    },
}

_FORBIDDEN_ANALOGY_DOMAINS: Final = frozenset(
    {
        "medical",
        "psychological_diagnosis",
        "legal",
        "religious",
        "political",
        "professional_advice",
        "attack_or_weapon",
        "target_attack",
    }
)

_FORBIDDEN_PAYLOAD_KEYS: Final = frozenset(
    {
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "memo",
        "memo_action",
        "memoText",
        "memoAction",
        "comment_text",
        "commentText",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "completed_reply_text",
        "completed_metaphor_text",
        "metaphor_sentence",
        "sentence",
        "sentences",
        "phrase",
        "body",
        "text",
        "example_sentence",
        "runtime_template",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "api_response_key_change",
        "comment_text_body_included",
        "comment_text_generated",
        "comment_text_included",
        "completed_metaphor_sentence_generated",
        "completed_reply_generated",
        "db_physical_name_changed",
        "display_gate_relaxed",
        "external_ai_used",
        "fixed_metaphor_template_used",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "free_metaphor_generation_allowed",
        "free_metaphor_generated",
        "gate_relaxed",
        "input_specific_template_used",
        "local_llm_used",
        "medical_domain_analogy_allowed",
        "legal_domain_analogy_allowed",
        "religious_domain_analogy_allowed",
        "political_domain_analogy_allowed",
        "professional_domain_analogy_allowed",
        "aggressive_surface_allowed",
        "raw_analogy_sentence_included",
        "raw_input_included",
        "raw_text_included",
        "public_payload_changed",
        "public_response_key_added",
        "public_response_key_change",
        "response_key_changed",
        "rn_visible_contract_changed",
        "schema_file_materialized",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "as_meta"):
        try:
            value = value.as_meta()
        except Exception:
            value = {}
    return value if isinstance(value, Mapping) else {}


def _deepcopy_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return copy.deepcopy(dict(value or {}))


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        item = _clean(value)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _source_summary(current_input: Any, frame: Mapping[str, Any]) -> dict[str, Any]:
    frame_source = _as_mapping(frame.get("source"))
    current = _as_mapping(current_input)
    return {
        "source_kind": "current_input",
        "source_record_id": _clean(
            frame_source.get("source_record_id")
            or current.get("id")
            or current.get("record_id")
            or current.get("source_record_id")
        ),
        "selected_at": _clean(frame_source.get("selected_at") or current.get("created_at") or current.get("selected_at")),
        "environment_state_output_frame_id": frame.get("material_id") or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
    }


def _current_source_text(current_input: Any) -> str:
    data = _as_mapping(current_input)
    parts: list[str] = []
    for key in ("memo", "memo_action"):
        value = _clean(data.get(key))
        if value:
            parts.append(value)
    for item in _listify(data.get("emotion_details")):
        if isinstance(item, Mapping):
            parts.append(_clean(item.get("type")))
            parts.append(_clean(item.get("strength")))
        else:
            parts.append(_clean(item))
    for key in ("emotions", "category"):
        for item in _listify(data.get(key)):
            parts.append(_clean(item))
    return " ".join(part for part in parts if part)


def _emotion_labels(current_input: Any, frame: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for label in _as_mapping(frame.get("state_axis")).get("emotion_labels") or []:
        if isinstance(label, Mapping):
            out.append(_clean(label.get("type")))
    current = _as_mapping(current_input)
    for item in _listify(current.get("emotion_details")):
        if isinstance(item, Mapping):
            out.append(_clean(item.get("type")))
        else:
            out.append(_clean(item))
    for item in _listify(current.get("emotions")):
        out.append(_clean(item))
    return _dedupe(out)


def _emotion_strengths(current_input: Any, frame: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    summary = _as_mapping(_as_mapping(frame.get("state_axis")).get("strength_summary"))
    out.extend([summary.get("primary_strength"), summary.get("strongest_strength")])
    for label in _as_mapping(frame.get("state_axis")).get("emotion_labels") or []:
        if isinstance(label, Mapping):
            out.append(label.get("strength"))
    current = _as_mapping(current_input)
    for item in _listify(current.get("emotion_details")):
        if isinstance(item, Mapping):
            out.append(item.get("strength"))
    return _dedupe(out)


def _is_strong_strength(values: Sequence[str], source_text: str) -> bool:
    normalized = {_clean(value).lower() for value in values}
    if normalized & {"strong", "high", "very_strong", "very-high", "強", "強い", "高", "高い"}:
        return True
    return bool(_STRONG_WORD_RE.search(source_text))


def _coerce_frame(current_input: Any, environment_state_output_frame: Any = None) -> dict[str, Any]:
    frame = _as_mapping(environment_state_output_frame)
    if frame:
        return copy.deepcopy(dict(frame))
    # Pass an empty relation list to keep this material independent from the
    # observation-material loader when called standalone.  The surface contract
    # path passes the already-built frame with relation ids.
    built = build_environment_state_output_frame(current_input or {}, observation_structure_relation_ids=[])
    return copy.deepcopy(dict(built))


def _relation_ids(frame: Mapping[str, Any], observation_structure_material: Any = None) -> list[str]:
    material = _as_mapping(observation_structure_material)
    bridge = _as_mapping(frame.get("observation_structure_bridge"))
    return _dedupe(
        material.get("selected_relation_ids")
        or material.get("structure_relation_ids")
        or bridge.get("selected_relation_ids")
        or []
    )


def _structure_question_ids(observation_structure_material: Any = None) -> list[str]:
    material = _as_mapping(observation_structure_material)
    return _dedupe(material.get("structure_question_ids") or [])


def _theme_ids(frame: Mapping[str, Any]) -> list[str]:
    out: list[str] = []
    for item in _as_mapping(frame.get("output_axis")).get("output_theme_candidates") or []:
        if isinstance(item, Mapping):
            out.append(_clean(item.get("theme_id") or item.get("candidate_id")))
    for item in _as_mapping(frame.get("state_axis")).get("state_text_gap_candidates") or []:
        if isinstance(item, Mapping):
            out.append(_clean(item.get("candidate_id")))
    return _dedupe(out)


def _special_case_flags(special_handling: Any) -> dict[str, bool]:
    data = _as_mapping(special_handling)
    self_denial = _as_mapping(data.get("self_denial"))
    anger = _as_mapping(data.get("anger"))
    return {
        "self_denial_enabled": bool(
            data.get("self_denial_special_handling_enabled")
            or self_denial.get("enabled")
            or data.get("identity_claim_is_not_accepted")
            or self_denial.get("identity_claim_is_not_accepted")
        ),
        "anger_enabled": bool(
            data.get("anger_special_handling_enabled")
            or anger.get("enabled")
            or anger.get("inner_value_line_receiving_allowed")
        ),
    }


def _candidate_registry_summary() -> list[dict[str, Any]]:
    def _must_not_read_as(item: Mapping[str, Any]) -> list[str]:
        values = _dedupe(item.get("must_not_read_as") or [])
        if "action_instruction" not in values:
            values.append("action_instruction")
        return values

    return [
        {
            "safe_daily_analogy_id": item["safe_daily_analogy_id"],
            "analogy_family": item["analogy_family"],
            "structure_ids": list(item["structure_ids"]),
            "domain_kind": item["domain_kind"],
            "qa_target": item["qa_target"],
            "surface_role": item["surface_role"],
            "must_not_read_as": _must_not_read_as(item),
            "candidate_is_completed_sentence_template": False,
            "runtime_fixed_sentence_allowed": False,
            "safe_daily_domain_only": True,
        }
        for item in _DAILY_ANALOGY_REGISTRY.values()
    ]


def _family_candidate(
    *,
    source_text: str,
    relation_ids: Sequence[str],
    theme_ids: Sequence[str],
    self_denial_detected: bool,
) -> tuple[str | None, str]:
    relation_set = set(relation_ids)
    theme_set = set(theme_ids)

    if self_denial_detected:
        return "partial_dark_letters_on_page", "self_denial_part_whole_boundary"
    if (
        _UNCHECKED_ANSWER_RE.search(source_text)
        or "state_text_gap" in relation_set
        or "thought_action_discrepancy" in relation_set
    ):
        return "unchecked_answer_sheet", "unconfirmed_area_or_state_text_gap"
    if _AHEAD_OF_CONFIRMATION_RE.search(source_text) or "unexpressed_output_stop" in relation_set:
        return "order_before_cooking", "ahead_of_confirmation_without_action_instruction"
    if _REPETITION_RE.search(source_text) or "repetition" in relation_set or "continuation_concern" in theme_set:
        return "same_step_on_same_path", "repeated_confusion_or_continuation_concern"
    if _CARRYING_LOAD_RE.search(source_text) or {"load_accumulation", "pressure_gap"} & relation_set:
        return "carrying_all_bags_alone", "load_concentration_without_prescription"
    if _AMBIVALENCE_RE.search(source_text) or {"unformed_self_insight", "direction_concern"} & (relation_set | theme_set):
        return "two_bags_selection_load", "ambivalence_or_unformed_self_insight"
    return None, "no_matching_safe_daily_analogy_candidate"


def _trigger_policy(source_text: str, question_ids: Sequence[str]) -> dict[str, Any]:
    # Phase 6 allows metaphor candidates only when the user-facing input itself
    # asks for structure understanding.  Observation-material question ids are
    # retained as supporting context, but they must not turn a standard input
    # into metaphor mode by themselves.
    structure_request = bool(_STRUCTURE_REQUEST_RE.search(source_text))
    repeated_confusion = bool(_REPEATED_CONFUSION_RE.search(source_text))
    return {
        "structure_understanding_request_detected": structure_request,
        "repeated_confusion_detected": repeated_confusion,
        "allowed_trigger_detected": bool(structure_request),
        "allowed_trigger_ids": [
            trigger_id
            for trigger_id, enabled in (
                ("structure_question", structure_request),
                ("repeated_confusion", structure_request and repeated_confusion),
            )
            if enabled
        ],
        "source_fields_used": ["memo", "memo_action", "emotion_details", "category"],
        "raw_text_returned": False,
    }


def _suppression_policy(
    *,
    source_text: str,
    emotion_labels: Sequence[str],
    emotion_strengths: Sequence[str],
    special_handling: Any,
) -> dict[str, Any]:
    labels = set(emotion_labels)
    special = _special_case_flags(special_handling)
    self_denial_detected = special["self_denial_enabled"] or bool(_SELF_DENIAL_RE.search(source_text))
    anger_detected = special["anger_enabled"] or bool(_ANGER_RE.search(source_text)) or "怒り" in labels
    grief_detected = bool(_GRIEF_RE.search(source_text)) or bool(labels & {"悲しみ", "悲しい", "孤独", "寂しさ", "さみしさ"})
    strong = _is_strong_strength(emotion_strengths, source_text)
    strong_self_denial = bool(self_denial_detected and strong)
    strong_grief_or_loneliness = bool(grief_detected and strong)

    panic_like_input = bool(("パニック" in source_text or "息ができない" in source_text) and strong)
    specialist_context_detected = bool(_SPECIALIST_CONTEXT_RE.search(source_text))

    reasons: list[str] = []
    if strong_self_denial:
        reasons.append("strong_self_denial_suppresses_metaphor")
    if strong_grief_or_loneliness:
        reasons.append("strong_grief_or_loneliness_suppresses_metaphor")
    if anger_detected:
        reasons.append("anger_suppresses_metaphor")
    if panic_like_input:
        reasons.append("panic_like_input_suppresses_metaphor")
    if specialist_context_detected:
        reasons.append("specialist_context_suppresses_metaphor")

    return {
        "suppressed": bool(reasons),
        "suppression_reason_ids": reasons,
        "self_denial_detected": self_denial_detected,
        "anger_detected": anger_detected,
        "grief_or_loneliness_detected": grief_detected,
        "strong_intensity_detected": strong,
        "strong_self_denial_suppressed": strong_self_denial,
        "strong_grief_or_loneliness_suppressed": strong_grief_or_loneliness,
        "anger_suppressed": anger_detected,
        "panic_like_input_suppressed": panic_like_input,
        "specialist_context_detected": specialist_context_detected,
        "specialist_context_suppressed": specialist_context_detected,
    }


def _selection(
    *,
    source_text: str,
    frame: Mapping[str, Any],
    observation_structure_material: Any,
    special_handling: Any,
) -> dict[str, Any]:
    relation_ids = _relation_ids(frame, observation_structure_material)
    question_ids = _structure_question_ids(observation_structure_material)
    themes = _theme_ids(frame)
    triggers = _trigger_policy(source_text, question_ids)
    emotion_labels = _emotion_labels({}, frame)
    strengths = _emotion_strengths({}, frame)
    suppression = _suppression_policy(
        source_text=source_text,
        emotion_labels=emotion_labels,
        emotion_strengths=strengths,
        special_handling=special_handling,
    )

    family, reason = _family_candidate(
        source_text=source_text,
        relation_ids=relation_ids,
        theme_ids=themes,
        self_denial_detected=bool(suppression.get("self_denial_detected")),
    )
    selected = _DAILY_ANALOGY_REGISTRY.get(family or "") if family else None
    has_corresponding_structure_id = bool(relation_ids or themes or question_ids or family)
    eligible = bool(
        triggers["allowed_trigger_detected"]
        and has_corresponding_structure_id
        and not suppression["suppressed"]
        and selected
    )
    mode = "safe_daily_analogy" if eligible else "none"
    selected_family = selected["analogy_family"] if eligible and selected else None
    selected_id = selected["safe_daily_analogy_id"] if eligible and selected else None

    if not triggers["allowed_trigger_detected"]:
        selection_reason = "not_structure_understanding_request"
    elif not has_corresponding_structure_id:
        selection_reason = "missing_corresponding_structure_id"
    elif suppression["suppressed"]:
        selection_reason = "metaphor_suppressed_for_input_safety"
    elif not selected:
        selection_reason = "no_matching_safe_daily_analogy_candidate"
    else:
        selection_reason = reason

    return {
        "mode": mode,
        "eligible": eligible,
        "selected_analogy_family": selected_family,
        "selected_analogy_family_id": selected_family,
        "safe_daily_analogy_id": selected_id,
        "selection_reason": selection_reason,
        "candidate_selection_reason": reason,
        "allowed_when": ["structure_question", "repeated_confusion"],
        "corresponding_structure_id_required": True,
        "corresponding_structure_id_detected": has_corresponding_structure_id,
        "trigger_policy": triggers,
        "suppression": suppression,
        "candidate_analogy_families": _candidate_registry_summary(),
        "selected_candidate": copy.deepcopy(selected) if eligible and selected else None,
        "matched_relation_ids": list(relation_ids),
        "matched_theme_ids": list(themes),
        "structure_question_ids": list(question_ids),
        "material_is_completed_sentence_template": False,
        "completed_metaphor_sentence_generated": False,
        "free_metaphor_generation_allowed": False,
    }


def _safe_frame_summary(frame: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": frame.get("schema_version") or "",
        "material_id": frame.get("material_id") or ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
        "axis_presence": _deepcopy_mapping(_as_mapping(frame.get("axis_presence"))),
        "source": _deepcopy_mapping(_as_mapping(frame.get("source"))),
        "observation_structure_bridge": _deepcopy_mapping(_as_mapping(frame.get("observation_structure_bridge"))),
        "output_theme_candidate_ids": _theme_ids(frame),
        "emotion_label_ids": _emotion_labels({}, frame),
        "raw_text_included": False,
    }


def _observation_material_summary(observation_structure_material: Any, frame: Mapping[str, Any]) -> dict[str, Any]:
    material = _as_mapping(observation_structure_material)
    return {
        "schema_version": material.get("schema_version") or "",
        "material_id": material.get("material_id") or "",
        "source_phase": material.get("source_phase") or material.get("phase") or "",
        "selected_relation_ids": _relation_ids(frame, material),
        "structure_question_ids": _structure_question_ids(material),
        "relation_policy_ids": _dedupe(material.get("relation_policy_ids") or material.get("constraint_ids") or []),
        "dictionary_is_observation_material_only": True,
        "dictionary_returns_completed_reply": False,
        "raw_text_included": False,
    }


def _gate_policy() -> dict[str, Any]:
    return {
        "metaphor_must_be_state_explanation_only": True,
        "action_instruction_allowed": False,
        "target_judgement_allowed": False,
        "target_attack_amplification_allowed": False,
        "professional_domain_analogy_allowed": False,
        "medical_domain_analogy_allowed": False,
        "legal_domain_analogy_allowed": False,
        "religious_domain_analogy_allowed": False,
        "political_domain_analogy_allowed": False,
        "aggressive_surface_allowed": False,
        "raw_analogy_sentence_included": False,
        "fixed_metaphor_template_used": False,
    }


def _surface_policy() -> dict[str, Any]:
    return {
        "must_use_safe_daily_analogy": True,
        "free_metaphor_generation_allowed": False,
        "free_metaphor_generated": False,
        "completed_metaphor_sentence_generated": False,
        "material_is_completed_sentence_template": False,
        "fixed_metaphor_template_used": False,
        "examples_are_not_runtime_templates": True,
        "metaphor_is_state_explanation_only": True,
        "must_not_generate_action_instruction": True,
        "must_not_generate_diagnosis": True,
        "must_not_generate_personality_type": True,
        "must_not_generate_professional_advice": True,
        "must_not_generate_target_attack": True,
        "public_payload_changed": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "schema_file_materialized": False,
        "comment_text_generated": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "display_gate_relaxed": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }


@dataclass(frozen=True)
class EmlisAISafeDailyMetaphorMaterial:
    """Text-free Phase 6 safe daily metaphor material."""

    source: Mapping[str, Any]
    selection: Mapping[str, Any]
    analogy_policy: Mapping[str, Any]
    gate_policy: Mapping[str, Any]
    surface_policy: Mapping[str, Any]
    environment_state_output_frame: Mapping[str, Any]
    observation_structure_material: Mapping[str, Any]
    schema_version: str = EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION
    material_id: str = EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID
    internal_name: str = EMLIS_AI_SAFE_DAILY_METAPHOR_INTERNAL_NAME
    phase: str = EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE
    passed: bool = True
    rejection_reasons: tuple[str, ...] = field(default_factory=tuple)

    def as_meta(self) -> dict[str, Any]:
        selection = _deepcopy_mapping(self.selection)
        meta = {
            "schema_version": self.schema_version,
            "version": self.schema_version,
            "material_id": self.material_id,
            "internal_name": self.internal_name,
            "source_phase": self.phase,
            "phase": self.phase,
            "passed": bool(self.passed),
            "evaluated": True,
            "status": "passed" if self.passed else "rejected",
            "rejection_reasons": list(self.rejection_reasons),
            "source": _deepcopy_mapping(self.source),
            "mode": selection.get("mode") or "none",
            "selected_analogy_family": selection.get("selected_analogy_family"),
            "selected_analogy_family_id": selection.get("selected_analogy_family_id"),
            "safe_daily_analogy_id": selection.get("safe_daily_analogy_id"),
            "selected_safe_daily_analogy_id": selection.get("safe_daily_analogy_id"),
            "analogy_candidate_ids": [
                item.get("safe_daily_analogy_id")
                for item in selection.get("candidate_analogy_families") or []
                if isinstance(item, Mapping) and item.get("safe_daily_analogy_id")
            ],
            "selection_basis": ["analogy_family", "safe_daily_analogy_id", "structure_ids", "output_theme_ids"],
            "structure_question_detected": bool(_as_mapping(selection.get("trigger_policy")).get("structure_understanding_request_detected")),
            "repeated_confusion_detected": bool(_as_mapping(selection.get("trigger_policy")).get("repeated_confusion_detected")),
            "suppression_signals": list(_as_mapping(selection.get("suppression")).get("suppression_reason_ids") or []),
            "selection": selection,
            "analogy_policy": _deepcopy_mapping(self.analogy_policy),
            "gate_policy": _deepcopy_mapping(self.gate_policy),
            "surface_policy": _deepcopy_mapping(self.surface_policy),
            "environment_state_output_frame": _deepcopy_mapping(self.environment_state_output_frame),
            "observation_structure_material": _deepcopy_mapping(self.observation_structure_material),
            "safe_daily_metaphor_material_connected": True,
            "safe_daily_metaphor_material_only": True,
            "metaphor_material_connected": True,
            "must_use_safe_daily_analogy": True,
            "free_metaphor_generation_allowed": False,
            "free_metaphor_generated": False,
            "completed_metaphor_sentence_generated": False,
            "material_is_completed_sentence_template": False,
            "fixed_metaphor_template_used": False,
            "comment_text_generated": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "schema_file_materialized": False,
            "public_payload_changed": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "request_key_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "display_gate_relaxed": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_emlis_ai_safe_daily_metaphor_material(meta)
        return meta

    def gate_report(self) -> dict[str, Any]:
        meta = self.as_meta()
        selection = _as_mapping(meta.get("selection"))
        suppression = _as_mapping(selection.get("suppression"))
        report = {
            "schema_version": meta["schema_version"],
            "material_id": meta["material_id"],
            "passed": meta["passed"],
            "evaluated": True,
            "status": meta["status"],
            "rejection_reasons": meta["rejection_reasons"],
            "safe_daily_metaphor_material_connected": True,
            "safe_daily_metaphor_material_only": True,
            "mode": selection.get("mode") or "none",
            "selected_analogy_family": selection.get("selected_analogy_family"),
            "safe_daily_analogy_id": selection.get("safe_daily_analogy_id"),
            "selected_safe_daily_analogy_id": selection.get("safe_daily_analogy_id"),
            "selection_reason": selection.get("selection_reason") or "",
            "allowed_trigger_detected": bool(_as_mapping(selection.get("trigger_policy")).get("allowed_trigger_detected")),
            "metaphor_suppressed": bool(suppression.get("suppressed")),
            "suppression_reason_ids": list(suppression.get("suppression_reason_ids") or []),
            "strong_self_denial_suppressed": bool(suppression.get("strong_self_denial_suppressed")),
            "strong_grief_or_loneliness_suppressed": bool(suppression.get("strong_grief_or_loneliness_suppressed")),
            "anger_suppressed": bool(suppression.get("anger_suppressed")),
            "free_metaphor_generation_allowed": False,
            "completed_metaphor_sentence_generated": False,
            "fixed_metaphor_template_used": False,
            "metaphor_must_be_state_explanation_only": True,
            "action_instruction_allowed": False,
            "professional_domain_analogy_allowed": False,
            "medical_domain_analogy_allowed": False,
            "legal_domain_analogy_allowed": False,
            "religious_domain_analogy_allowed": False,
            "political_domain_analogy_allowed": False,
            "aggressive_surface_allowed": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "public_response_key_added": False,
            "display_gate_relaxed": False,
        }
        assert_emlis_ai_safe_daily_metaphor_material(report)
        return report

    def composer_payload(self) -> dict[str, Any]:
        meta = self.as_meta()
        payload = {
            "schema_version": meta["schema_version"],
            "material_id": meta["material_id"],
            "source_phase": meta["source_phase"],
            "source": _deepcopy_mapping(_as_mapping(meta.get("source"))),
            "selection": _deepcopy_mapping(_as_mapping(meta.get("selection"))),
            "analogy_policy": _deepcopy_mapping(_as_mapping(meta.get("analogy_policy"))),
            "gate_policy": _deepcopy_mapping(_as_mapping(meta.get("gate_policy"))),
            "surface_policy": _deepcopy_mapping(_as_mapping(meta.get("surface_policy"))),
            "safe_daily_metaphor_material_connected": True,
            "safe_daily_metaphor_material_only": True,
            "mode": meta.get("mode") or "none",
            "selected_analogy_family": meta.get("selected_analogy_family"),
            "safe_daily_analogy_id": meta.get("safe_daily_analogy_id"),
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "fixed_metaphor_template_used": False,
            "free_metaphor_generation_allowed": False,
            "completed_metaphor_sentence_generated": False,
            "display_gate_relaxed": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }
        assert_emlis_ai_safe_daily_metaphor_material(payload)
        return payload


def build_emlis_ai_safe_daily_metaphor_material(
    current_input: Any = None,
    *,
    environment_state_output_frame: Any = None,
    observation_structure_material: Any = None,
    special_handling: Any = None,
) -> EmlisAISafeDailyMetaphorMaterial:
    frame = _coerce_frame(current_input, environment_state_output_frame)
    source_text = _current_source_text(current_input)
    # When called from the state-answer contract, current_input is available for
    # guarded detection.  When current_input is absent, the material still works
    # from text-free frame/material ids and simply avoids free inference.
    if not source_text:
        source_text = " ".join(_theme_ids(frame) + _relation_ids(frame, observation_structure_material))
    selection = _selection(
        source_text=source_text,
        frame=frame,
        observation_structure_material=observation_structure_material,
        special_handling=special_handling,
    )
    analogy_policy = {
        "allowed_when": ["structure_question", "repeated_confusion"],
        "candidate_selection_unit": "analogy_family_and_safe_daily_analogy_id",
        "must_use_safe_daily_analogy": True,
        "free_metaphor_generation_allowed": False,
        "candidate_registry": _candidate_registry_summary(),
        "forbidden_analogy_domains": sorted(_FORBIDDEN_ANALOGY_DOMAINS),
        "completed_sentence_template_registry": False,
        "runtime_fixed_sentence_allowed": False,
    }
    material = EmlisAISafeDailyMetaphorMaterial(
        source=_source_summary(current_input, frame),
        selection=selection,
        analogy_policy=analogy_policy,
        gate_policy=_gate_policy(),
        surface_policy=_surface_policy(),
        environment_state_output_frame=_safe_frame_summary(frame),
        observation_structure_material=_observation_material_summary(observation_structure_material, frame),
    )
    assert_emlis_ai_safe_daily_metaphor_material(material)
    return material


def safe_daily_metaphor_material_forward_meta(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisAISafeDailyMetaphorMaterial):
        meta = value.as_meta()
    elif isinstance(value, Mapping):
        meta = dict(value)
    else:
        return {}
    keys = {
        "schema_version",
        "version",
        "material_id",
        "internal_name",
        "source_phase",
        "phase",
        "passed",
        "evaluated",
        "status",
        "rejection_reasons",
        "source",
        "mode",
        "selected_analogy_family",
        "selected_analogy_family_id",
        "safe_daily_analogy_id",
        "selected_safe_daily_analogy_id",
        "analogy_candidate_ids",
        "selection_basis",
        "structure_question_detected",
        "repeated_confusion_detected",
        "suppression_signals",
        "selection",
        "analogy_policy",
        "gate_policy",
        "surface_policy",
        "environment_state_output_frame",
        "observation_structure_material",
        "safe_daily_metaphor_material_connected",
        "safe_daily_metaphor_material_only",
        "metaphor_material_connected",
        "must_use_safe_daily_analogy",
        "free_metaphor_generation_allowed",
        "free_metaphor_generated",
        "completed_metaphor_sentence_generated",
        "material_is_completed_sentence_template",
        "fixed_metaphor_template_used",
        "comment_text_generated",
        "comment_text_included",
        "comment_text_body_included",
        "raw_input_included",
        "raw_text_included",
        "schema_file_materialized",
        "public_payload_changed",
        "public_response_key_added",
        "api_route_changed",
        "request_key_changed",
        "response_key_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "external_ai_used",
        "local_llm_used",
    }
    out = {key: copy.deepcopy(meta.get(key)) for key in keys if key in meta}
    assert_emlis_ai_safe_daily_metaphor_material(out)
    return out


def safe_daily_metaphor_material_gate_report(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisAISafeDailyMetaphorMaterial):
        return value.gate_report()
    meta = safe_daily_metaphor_material_forward_meta(value)
    if not meta:
        return {}
    selection = _as_mapping(meta.get("selection"))
    suppression = _as_mapping(selection.get("suppression"))
    report = {
        "schema_version": meta.get("schema_version") or EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION,
        "material_id": meta.get("material_id") or EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID,
        "passed": bool(meta.get("passed", True)),
        "evaluated": True,
        "status": meta.get("status") or "passed",
        "rejection_reasons": list(meta.get("rejection_reasons") or []),
        "safe_daily_metaphor_material_connected": True,
        "safe_daily_metaphor_material_only": True,
        "mode": selection.get("mode") or meta.get("mode") or "none",
        "selected_analogy_family": selection.get("selected_analogy_family") or meta.get("selected_analogy_family"),
        "safe_daily_analogy_id": selection.get("safe_daily_analogy_id") or meta.get("safe_daily_analogy_id"),
        "selected_safe_daily_analogy_id": selection.get("safe_daily_analogy_id") or meta.get("selected_safe_daily_analogy_id") or meta.get("safe_daily_analogy_id"),
        "selection_reason": selection.get("selection_reason") or "",
        "allowed_trigger_detected": bool(_as_mapping(selection.get("trigger_policy")).get("allowed_trigger_detected")),
        "metaphor_suppressed": bool(suppression.get("suppressed")),
        "suppression_reason_ids": list(suppression.get("suppression_reason_ids") or []),
        "strong_self_denial_suppressed": bool(suppression.get("strong_self_denial_suppressed")),
        "strong_grief_or_loneliness_suppressed": bool(suppression.get("strong_grief_or_loneliness_suppressed")),
        "anger_suppressed": bool(suppression.get("anger_suppressed")),
        "free_metaphor_generation_allowed": False,
        "completed_metaphor_sentence_generated": False,
        "fixed_metaphor_template_used": False,
        "metaphor_must_be_state_explanation_only": True,
        "action_instruction_allowed": False,
        "professional_domain_analogy_allowed": False,
        "medical_domain_analogy_allowed": False,
        "legal_domain_analogy_allowed": False,
        "religious_domain_analogy_allowed": False,
        "political_domain_analogy_allowed": False,
        "aggressive_surface_allowed": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
        "display_gate_relaxed": False,
    }
    assert_emlis_ai_safe_daily_metaphor_material(report)
    return report


def safe_daily_metaphor_material_composer_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, EmlisAISafeDailyMetaphorMaterial):
        return value.composer_payload()
    meta = safe_daily_metaphor_material_forward_meta(value)
    if not meta:
        return {}
    payload = {
        "schema_version": meta.get("schema_version") or EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION,
        "material_id": meta.get("material_id") or EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID,
        "source_phase": meta.get("source_phase") or EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE,
        "source": _deepcopy_mapping(_as_mapping(meta.get("source"))),
        "selection": _deepcopy_mapping(_as_mapping(meta.get("selection"))),
        "analogy_policy": _deepcopy_mapping(_as_mapping(meta.get("analogy_policy"))),
        "gate_policy": _deepcopy_mapping(_as_mapping(meta.get("gate_policy"))),
        "surface_policy": _deepcopy_mapping(_as_mapping(meta.get("surface_policy"))),
        "safe_daily_metaphor_material_connected": True,
        "safe_daily_metaphor_material_only": True,
        "mode": meta.get("mode") or _as_mapping(meta.get("selection")).get("mode") or "none",
        "selected_analogy_family": meta.get("selected_analogy_family") or _as_mapping(meta.get("selection")).get("selected_analogy_family"),
        "safe_daily_analogy_id": meta.get("safe_daily_analogy_id") or _as_mapping(meta.get("selection")).get("safe_daily_analogy_id"),
        "selected_safe_daily_analogy_id": meta.get("selected_safe_daily_analogy_id") or meta.get("safe_daily_analogy_id") or _as_mapping(meta.get("selection")).get("safe_daily_analogy_id"),
        "completed_reply_generated": False,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "fixed_metaphor_template_used": False,
        "free_metaphor_generation_allowed": False,
        "completed_metaphor_sentence_generated": False,
        "display_gate_relaxed": False,
        "api_route_changed": False,
        "response_key_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
    }
    assert_emlis_ai_safe_daily_metaphor_material(payload)
    return payload


def _contains_forbidden_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _FORBIDDEN_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_payload_key(child):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_payload_key(child) for child in value)
    return False


def _candidate_domains_are_safe(value: Any) -> bool:
    candidates: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        selection = _as_mapping(value.get("selection"))
        candidates.extend([item for item in selection.get("candidate_analogy_families") or [] if isinstance(item, Mapping)])
        policy = _as_mapping(value.get("analogy_policy"))
        candidates.extend([item for item in policy.get("candidate_registry") or [] if isinstance(item, Mapping)])
        selected = selection.get("selected_candidate")
        if isinstance(selected, Mapping):
            candidates.append(selected)
    for candidate in candidates:
        domain = _clean(candidate.get("domain_kind"))
        if domain in _FORBIDDEN_ANALOGY_DOMAINS:
            return False
        if _clean(candidate.get("surface_role")) not in {"", "state_explanation_only"}:
            return False
    return True


def assert_emlis_ai_safe_daily_metaphor_material(value: Any, *, source: str = "emlis_ai_safe_daily_metaphor_material") -> None:
    if isinstance(value, EmlisAISafeDailyMetaphorMaterial):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_payload_key(value):
        raise ValueError(f"{source} must not include raw input/comment/metaphor sentence payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    if _clean(value.get("schema_version")) not in {"", EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION}:
        raise ValueError(f"{source} has unexpected schema_version")
    if _clean(value.get("material_id")) not in {"", EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID}:
        raise ValueError(f"{source} has unexpected material_id")
    selection = _as_mapping(value.get("selection"))
    mode = _clean(value.get("mode") or selection.get("mode"))
    selected_family = _clean(value.get("selected_analogy_family") or selection.get("selected_analogy_family"))
    if mode == "safe_daily_analogy" and not selected_family:
        raise ValueError(f"{source} must include selected_analogy_family when mode=safe_daily_analogy")
    if mode == "none" and selected_family:
        raise ValueError(f"{source} must not include selected_analogy_family when mode=none")
    if value.get("material_is_completed_sentence_template") is True:
        raise ValueError(f"{source} must not be a completed sentence template")
    if not _candidate_domains_are_safe(value):
        raise ValueError(f"{source} contains unsafe analogy candidate domain")
    try:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError as exc:
        raise ValueError(f"{source} must be JSON serializable") from exc


# Project-local aliases.
build_safe_daily_metaphor_material = build_emlis_ai_safe_daily_metaphor_material
assert_safe_daily_metaphor_material = assert_emlis_ai_safe_daily_metaphor_material
safe_daily_metaphor_forward_meta = safe_daily_metaphor_material_forward_meta
safe_daily_metaphor_gate_report = safe_daily_metaphor_material_gate_report
safe_daily_metaphor_composer_payload = safe_daily_metaphor_material_composer_payload

__all__ = [
    "EMLIS_AI_SAFE_DAILY_METAPHOR_SCHEMA_VERSION",
    "EMLIS_AI_SAFE_DAILY_METAPHOR_MATERIAL_ID",
    "EMLIS_AI_SAFE_DAILY_METAPHOR_PHASE",
    "EMLIS_AI_SAFE_DAILY_METAPHOR_INTERNAL_NAME",
    "EmlisAISafeDailyMetaphorMaterial",
    "build_emlis_ai_safe_daily_metaphor_material",
    "build_safe_daily_metaphor_material",
    "safe_daily_metaphor_material_forward_meta",
    "safe_daily_metaphor_material_gate_report",
    "safe_daily_metaphor_material_composer_payload",
    "safe_daily_metaphor_forward_meta",
    "safe_daily_metaphor_gate_report",
    "safe_daily_metaphor_composer_payload",
    "assert_emlis_ai_safe_daily_metaphor_material",
    "assert_safe_daily_metaphor_material",
]
